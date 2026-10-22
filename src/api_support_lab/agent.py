"""One bounded, draft-only triage agent with inspectable local tool use."""

import json
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Literal

from agents import Agent, OpenAIResponsesModel, RunConfig, RunHooks, Runner, function_tool
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from api_support_lab import runbooks, sdk
from api_support_lab.artifacts import DEFAULT_TRIAGE_DIR, sanitize, save_record, timestamp
from api_support_lab.capture import _usage_fields
from api_support_lab.config import ConfigurationError, Settings, require_live
from api_support_lab.runbooks import CaseId, PROJECT_ROOT
from api_support_lab.tickets import Ticket, diagnosis_is_grounded

# Decorating the ordinary functions leaves the shared implementations intact.
# Tool errors propagate; an error message must not masquerade as retrieved support.
diagnose_tool = function_tool(runbooks.diagnose, failure_error_function=None)
list_runbooks_tool = function_tool(runbooks.list_runbooks, failure_error_function=None)
get_runbook_tool = function_tool(runbooks.get_runbook, failure_error_function=None)
TOOLS = [diagnose_tool, list_runbooks_tool, get_runbook_tool]


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    category: Literal["invalid_credentials", "tool_schema", "incomplete_output", "timeout",
                      "undetermined", "out_of_scope"]
    candidate_runbooks: list[CaseId]
    observed_evidence: list[str]
    basis: Literal["stated", "inferred", "none"]
    severity: Literal["low", "medium", "high", "unknown"]
    action: Literal["recommend_fix", "request_info", "escalate"]
    missing: list[str]
    customer_reply: str = Field(min_length=1)
    escalation_note: str


class GroundingError(ValueError):
    """A result or tool argument lacks the required supporting evidence."""


class RefusedRun(ValueError):
    """The model refused; no triage result should be accepted."""


class ToolUse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    call_id: str | None = None
    name: Literal["diagnose", "list_runbooks", "get_runbook"]
    arguments: dict[str, JsonValue]
    status: Literal["started", "completed", "failed"]
    result: JsonValue


def validate_grounding(result: TriageResult, tool_use: list[dict], ticket: Ticket) -> set[str]:
    # Validate saved logs too: corrupt artifacts must become explicit failures,
    # rather than crashing the scorer or claiming successful retrieval.
    calls = TypeAdapter(list[ToolUse]).validate_python(tool_use)
    retrieved = set()
    for call in calls:
        if call.status != "completed":
            raise GroundingError("Unsuccessful tool call")
        if call.name == "diagnose" and not diagnosis_is_grounded(call.arguments, ticket):
            raise GroundingError("Diagnosis arguments not supplied by ticket")
        if call.name == "list_runbooks" and call.arguments:
            raise GroundingError("Runbook listing takes no arguments")
        if call.name == "get_runbook":
            case = call.arguments.get("case")
            if (set(call.arguments) != {"case"}
                    or not isinstance(case, str) or case not in runbooks.REGISTRY
                    or not isinstance(call.result, str) or not call.result.strip()):
                raise GroundingError("Invalid supporting runbook retrieval")
            retrieved.add(case)
    cited = set(result.candidate_runbooks)
    if result.category not in ("undetermined", "out_of_scope"):
        cited.add(result.category)
    if not cited <= retrieved:
        raise GroundingError("Case references require successful runbook retrieval")
    if result.action == "recommend_fix" and result.category not in retrieved:
        raise GroundingError("Case-specific fixes require supporting retrieval")
    if result.category in ("undetermined", "out_of_scope") and result.basis != "none":
        raise GroundingError("No supported category requires basis none")
    if result.category == "out_of_scope" and result.action != "escalate":
        raise GroundingError("Out-of-scope requests require escalation")
    if result.action == "escalate" and not result.escalation_note.strip():
        raise GroundingError("Escalation requires a routing note")
    text = "\n".join((ticket.subject, ticket.body, ticket.pasted_error or ""))
    if any(not fact.strip() or fact not in text for fact in result.observed_evidence):
        raise GroundingError("Observed evidence must be short ticket extracts")
    return retrieved


class ToolRecorder(RunHooks):
    def __init__(self, ticket: Ticket, secrets: tuple[str, ...]):
        self.ticket = ticket
        self.secrets = secrets
        self.tool_use: list[dict] = []
        self.usage: list[dict | None] = []
        self.pending: dict[str, dict] = {}

    async def on_tool_start(self, context, agent, tool):
        arguments = json.loads(context.tool_arguments)
        call = sanitize({
            "call_id": context.tool_call_id,
            "name": tool.name,
            "arguments": arguments,
            "status": "started",
            "result": None,
        }, self.secrets)
        self.tool_use.append(call)
        self.pending[context.tool_call_id] = call
        if tool.name == "diagnose" and not diagnosis_is_grounded(arguments, self.ticket):
            call["status"] = "failed"
            raise GroundingError("Diagnosis arguments not supplied by ticket")

    async def on_tool_end(self, context, agent, tool, result):
        call = self.pending.pop(context.tool_call_id)
        cleaned = sanitize(result, self.secrets)
        call.update(status="completed", result=cleaned)

    async def on_llm_end(self, context, agent, response):
        # raw_usage preserves missing fields; normalized SDK usage may default them
        # to zero. No usage received is unknown, including on a failed request.
        self.usage.append(_usage_fields(response.raw_usage))
        for item in response.output:
            for content in getattr(item, "content", ()):
                if getattr(content, "type", None) == "refusal":
                    raise RefusedRun("Model refusal")


def build_agent(settings: Settings, client) -> Agent:
    return Agent(
        name="API Support Lab triage",
        instructions=(PROJECT_ROOT / "triage" / "instructions.md").read_text(encoding="utf-8"),
        model=OpenAIResponsesModel(settings.model, client),
        model_settings=sdk.configure_agents(settings),
        tools=list(TOOLS),
        output_type=TriageResult,
    )


@dataclass(frozen=True)
class TriageRun:
    record: dict
    path: Path


async def triage_ticket(
    ticket: Ticket, settings: Settings, *, live: bool,
    output_dir: Path = DEFAULT_TRIAGE_DIR,
) -> TriageRun:
    require_live(live)
    started = perf_counter()
    record = {
        "schema_version": 1,
        "ticket_id": ticket.id,
        "ticket_hash": ticket.content_hash(),
        "captured_at": timestamp(),
        "model": settings.model,
        "settings": {**asdict(settings), "api": "responses", "store": False,
                     "tracing_disabled": True},
        "sdk_versions": {name: version(name) for name in ("openai", "openai-agents")},
        "status": "failed",
        "failure": None,
        "result": None,
        "tool_use": [],
        "usage": [],
    }
    secrets = ()
    recorder = ToolRecorder(ticket, secrets)
    try:
        async with sdk.create_async_client(settings, live=live) as client:
            secrets = (client.api_key,)
            recorder.secrets = secrets
            outcome = await Runner.run(
                build_agent(settings, client),
                input=ticket.model_input(),
                max_turns=settings.max_turns,
                hooks=recorder,
                run_config=RunConfig(tracing_disabled=True, trace_include_sensitive_data=False),
            )
            result = TriageResult.model_validate(outcome.final_output)
            validate_grounding(result, recorder.tool_use, ticket)
            record.update(status="completed", result=result.model_dump())
    except ConfigurationError:
        raise
    except Exception as error:
        # Deliberately omit exception strings, raw responses, and prompts. SDK
        # errors can embed arbitrary request/response data or credentials.
        record.update(status="failed", result=None, failure={
            "type": type(error).__name__,
            "cause_type": type(error.__cause__).__name__ if error.__cause__ else None,
            "message": "Triage failed; no draft accepted.",
        })
    for call in recorder.tool_use:
        if call["status"] == "started":
            call["status"] = "failed"
    record.update(tool_use=recorder.tool_use, usage=recorder.usage,
                  elapsed_ms=round((perf_counter() - started) * 1000, 3))
    record = sanitize(record, secrets)
    # Saving is outside execution error handling: disk failure must not retry a run.
    path = save_record(record, output_dir, "triage", secrets=secrets)
    return TriageRun(record, path)
