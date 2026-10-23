"""Actual asynchronous SDK execution with authored responses and no network."""

import asyncio
import json

import httpx2
import openai
import pytest
from agents import MaxTurnsExceeded

from api_support_lab import agent, sdk
from api_support_lab.cli import main
from api_support_lab.config import ConfigurationError, Settings
from api_support_lab.runbooks import PROJECT_ROOT
from api_support_lab.tickets import load_ticket


@pytest.fixture
def ticket():
    return load_ticket(PROJECT_ROOT / "triage/tickets/T-001.yaml")


@pytest.fixture
def draft():
    return {
        "category": "invalid_credentials", "candidate_runbooks": ["invalid_credentials"],
        "observed_evidence": ["HTTP 401", "error_code: invalid_api_key"],
        "basis": "stated", "severity": "unknown", "action": "recommend_fix", "missing": [],
        "customer_reply": "Please confirm the application loads the intended project credential without printing or sharing it.",
        "escalation_note": "",
    }


def response(output, *, status="completed", usage=True):
    value = {"id": "resp_synthetic", "object": "response", "created_at": 0,
             "model": "synthetic-model", "status": status, "output": output}
    if status == "incomplete":
        value["incomplete_details"] = {"reason": "max_output_tokens"}
    if usage:
        value["usage"] = {"input_tokens": 15, "output_tokens": 5, "total_tokens": 20}
    return value


def message(draft):
    return {"id": "msg_synthetic", "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": json.dumps(draft), "annotations": []}]}


def tool(name, arguments, call_id="call_synthetic"):
    return {"id": f"fc_{call_id}", "call_id": call_id, "type": "function_call", "name": name,
            "arguments": json.dumps(arguments), "status": "completed"}


@pytest.fixture
def transport(monkeypatch):
    original = openai.AsyncOpenAI
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-triage-test-credential")
    def install(script):
        requests = []
        clients = []
        def handler(request):
            requests.append(request)
            value = script.pop(0)
            if isinstance(value, Exception):
                raise value
            if isinstance(value, tuple):
                return httpx2.Response(value[0], json=value[1])
            return httpx2.Response(200, json=value)
        def factory(**kwargs):
            client = original(**kwargs, http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)))
            clients.append(client)
            return client
        monkeypatch.setattr(openai, "AsyncOpenAI", factory)
        return requests, clients
    return install


def run(ticket, tmp_path, **kwargs):
    async def bounded():
        return await asyncio.wait_for(agent.triage_ticket(ticket, Settings(**kwargs), live=True, output_dir=tmp_path), timeout=5)
    return asyncio.run(bounded())


def test_real_sdk_tool_loop_and_wire_contract(transport, ticket, draft, tmp_path):
    calls, clients = transport([
        response([tool("diagnose", {"status": 401, "error_code": "invalid_api_key"})]),
        response([tool("get_runbook", {"case": "invalid_credentials"}, "retrieve")]),
        response([message(draft)]),
    ])
    outcome = run(ticket, tmp_path)
    assert outcome.record["status"] == "completed", outcome.record
    assert len(calls) == 3
    assert clients[0].max_retries == 0
    assert clients[0].timeout == 60
    assert clients[0].is_closed()
    payload = json.loads(calls[0].content)
    assert payload["model"] == "gpt-6.1-sol"
    assert payload["reasoning"]["effort"] == "low"
    assert payload["max_output_tokens"] == 4096
    assert payload["store"] is False
    assert str(calls[0].url) == "https://api.openai.com/v1/responses"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert len(payload["tools"]) == 3
    serialized_input = json.dumps(payload["input"])
    assert ticket.subject in serialized_input
    for excluded in (ticket.id, "provenance", "broken-20261022", "required_runbooks", "Harbor Demo (invented)"):
        assert excluded not in serialized_input
    assert [call["status"] for call in outcome.record["tool_use"]] == ["completed", "completed"]
    assert outcome.record["usage"] == [{"input_tokens": 15, "output_tokens": 5, "total_tokens": 20}] * 3
    assert "dummy-triage-test-credential" not in outcome.path.read_text()
    assert json.loads(outcome.path.read_text()) == outcome.record


@pytest.mark.parametrize("code", [None, "unfamiliar_synthetic_code"])
def test_lookup_arguments_come_from_ticket(transport, ticket, tmp_path, code):
    if code is not None:
        ticket = ticket.model_copy(update={"pasted_error": f"HTTP 401\nerror_code: {code}"})
    calls, _ = transport([response([tool("diagnose", {"status": 401, "error_code": code})])])
    # Stop after one turn; the allowed tool call must still have been recorded.
    outcome = run(ticket, tmp_path, max_turns=1)
    assert len(calls) == 1
    assert outcome.record["tool_use"][0]["status"] == "completed"
    assert outcome.record["failure"]["type"] == "MaxTurnsExceeded"


@pytest.mark.parametrize("args", [
    {"status": 400, "error_code": None},
    {"status": 401, "error_code": "invented_code"},
])
def test_invented_lookup_arguments_fail_without_second_call(transport, ticket, tmp_path, args):
    calls, _ = transport([response([tool("diagnose", args)])])
    outcome = run(ticket, tmp_path)
    assert len(calls) == 1
    assert outcome.record["status"] == "failed"
    assert outcome.record["result"] is None
    assert outcome.record["failure"]["type"] == "UserError"
    assert outcome.record["failure"]["cause_type"] == "GroundingError"
    assert outcome.record["tool_use"][0]["status"] == "failed"


def test_missing_supporting_retrieval_fails(transport, ticket, draft, tmp_path):
    transport([response([message(draft)])])
    outcome = run(ticket, tmp_path)
    assert outcome.record["failure"]["type"] == "GroundingError"
    assert outcome.record["result"] is None


def test_listing_is_not_supporting_retrieval(transport, ticket, draft, tmp_path):
    transport([response([tool("list_runbooks", {})]), response([message(draft)])])
    assert run(ticket, tmp_path).record["failure"]["type"] == "GroundingError"


def test_tool_error_is_failed_run(transport, ticket, tmp_path, monkeypatch):
    monkeypatch.setattr(agent.runbooks, "REGISTRY", {
        "timeout": agent.runbooks.Runbook(tmp_path / "missing-runbook.md"),
    })
    transport([response([tool("get_runbook", {"case": "timeout"})])])
    outcome = run(ticket, tmp_path)
    assert outcome.record["failure"]["type"] == "UserError"
    assert outcome.record["failure"]["cause_type"] == "FileNotFoundError"
    assert outcome.record["tool_use"][0]["status"] == "failed"
    assert outcome.record["result"] is None


@pytest.mark.parametrize("kind", ["api", "timeout", "incomplete", "refusal", "invalid"])
def test_execution_failures_are_saved_without_retries(transport, ticket, tmp_path, kind):
    values = {
        "api": (429, {"error": {"message": "dummy-triage-test-credential", "type": "rate_limit_error"}}),
        "timeout": httpx2.ReadTimeout("dummy-triage-test-credential"),
        "incomplete": response([], status="incomplete"),
        "refusal": response([{"id": "msg_refusal", "type": "message", "role": "assistant", "status": "completed",
                              "content": [{"type": "refusal", "refusal": "synthetic refusal"}]}]),
        "invalid": response([message({"wrong": "shape"})]),
    }
    calls, _ = transport([values[kind]])
    outcome = run(ticket, tmp_path)
    assert len(calls) == 1
    assert outcome.record["status"] == "failed"
    assert outcome.record["result"] is None
    assert outcome.record["failure"] is not None
    assert "dummy-triage-test-credential" not in outcome.path.read_text()
    if kind in ("api", "timeout", "incomplete"):
        assert outcome.record["usage"] == []  # No fabricated zero usage.


def test_logs_and_result_redact_before_saving(transport, ticket, draft, tmp_path, monkeypatch):
    from api_support_lab import runbooks

    draft["customer_reply"] = "dummy-triage-test-credential sk-test-secret Bearer arbitrary-token"
    # Deliberately inject sensitive-looking strings into a synthetic local resource
    # and generated reply; test artifacts remain in this temporary directory.
    path = tmp_path / "synthetic.md"
    path.write_text("# Synthetic runbook\n\ndummy-triage-test-credential sk-test-secret Bearer arbitrary-token")
    monkeypatch.setattr(runbooks, "REGISTRY", {"invalid_credentials": runbooks.Runbook(path)})
    transport([response([tool("get_runbook", {"case": "invalid_credentials"})]),
               response([message(draft)])])
    outcome = run(ticket, tmp_path)
    assert outcome.record["status"] == "completed"
    text = outcome.path.read_text()
    assert "dummy-triage-test-credential" not in text
    assert "sk-test-secret" not in text
    assert "arbitrary-token" not in text
    assert "[REDACTED]" in text


def test_opt_in_precedes_client_and_artifact(monkeypatch, ticket, tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail("client constructed without opt-in")
    monkeypatch.setattr(sdk, "create_async_client", forbidden)
    with pytest.raises(ConfigurationError, match="--live"):
        asyncio.run(agent.triage_ticket(ticket, Settings(), live=False, output_dir=tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_disk_failure_does_not_rerun_model(transport, ticket, draft, tmp_path):
    draft.update(category="undetermined", candidate_runbooks=[], basis="none", action="request_info")
    calls, _ = transport([response([message(draft)])])
    blocked_dir = tmp_path / "file"
    blocked_dir.write_text("blocking directory creation")
    with pytest.raises(OSError):
        run(ticket, blocked_dir)
    assert len(calls) == 1


def test_run_configuration_and_turn_cap(monkeypatch, transport, ticket, draft, tmp_path):
    transport([])
    async def fake_run(starting_agent, **kwargs):
        assert kwargs["max_turns"] == 2
        assert kwargs["run_config"].tracing_disabled
        assert not kwargs["run_config"].trace_include_sensitive_data
        assert starting_agent.model_settings.retry.max_retries == 0
        assert starting_agent.model_settings.preserve_raw_usage
        assert starting_agent.output_type is agent.TriageResult
        raise MaxTurnsExceeded("synthetic turn exhaustion")
    monkeypatch.setattr(agent.Runner, "run", fake_run)
    assert run(ticket, tmp_path, max_turns=2).record["failure"]["type"] == "MaxTurnsExceeded"


def test_ten_ticket_evaluation_through_sdk_and_cli(transport, authored_drafts, tmp_path, capsys):
    script = []
    for ticket_id, result in authored_drafts.items():
        # Unknown code is passed unchanged; it must not find a schema mapping.
        if ticket_id == "T-007":
            script.append(response([tool("diagnose", {
                "status": 400, "error_code": "lunar_teapot_alignment_77",
            }, "unknown_code")]))
        for case in result["candidate_runbooks"]:
            script.append(response([tool("get_runbook", {"case": case}, ticket_id)]))
        script.append(response([message(result)]))
    calls, _ = transport(script)
    assert main(["evaluate", "--live", "--output-dir", str(tmp_path)]) == 0
    assert "10/10" in capsys.readouterr().out
    report = json.loads(next(tmp_path.glob("evaluation-*.json")).read_text())
    assert len(report["runs"]) == 10
    assert len(list((tmp_path / "runs").glob("triage-*.json"))) == 10
    assert len(calls) == 17
    unknown = report["runs"][6]
    assert unknown["tool_use"][0]["arguments"]["error_code"] == "lunar_teapot_alignment_77"
    assert unknown["tool_use"][0]["result"] == []
    assert all(review["status"] == "pending" for review in report["manual_reviews"].values())
    for request in calls:
        payload = json.loads(request.content)
        user_inputs = [item for item in payload["input"] if item.get("role") == "user"]
        assert len(user_inputs) == 1
        value = json.loads(user_inputs[0]["content"])
        assert set(value) == {"subject", "body", "pasted_error"}


@pytest.mark.parametrize("success", [True, False])
def test_single_ticket_cli_draft_or_visible_failure(transport, draft, tmp_path, capsys, success):
    script = [response([tool("get_runbook", {"case": "invalid_credentials"})]), response([message(draft)])]
    if not success:
        script = [(500, {"error": {"message": "synthetic failure"}})]
    calls, _ = transport(script)
    status = main(["triage", str(PROJECT_ROOT / "triage/tickets/T-001.yaml"),
                   "--live", "--output-dir", str(tmp_path)])
    assert status == (0 if success else 1)
    output = capsys.readouterr()
    assert "Saved triage run" in output.out
    if success:
        assert "Draft for human review" in output.out
    else:
        assert "no draft accepted" in output.err
        assert len(calls) == 1


def test_missing_usage_stays_unknown(transport, ticket, draft, tmp_path):
    draft.update(category="undetermined", candidate_runbooks=[], basis="none", action="request_info")
    transport([response([message(draft)], usage=False)])
    outcome = run(ticket, tmp_path)
    assert outcome.record["status"] == "completed"
    assert outcome.record["usage"] == [None]
