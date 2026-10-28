# Architecture

The lab uses a local CLI, a capture pipeline, runbook tools, one triage agent, and an automated scorer. The failure lab and triage agent share deterministic lookup and runbook functions. A ticket never grants the agent access to reproduction code or credentials. The [README](../README.md) and [walkthrough](walkthrough.md) show the reviewed examples.

## Overview

```mermaid
flowchart LR
    subgraph Lab[Explicit live reproduction]
        C[Case: broken or fixed] --> API[Responses API]
        API --> H[Capture wrapper]
        H --> E[Sanitized JSON evidence]
    end
    E --> W[Runbooks written from observations]
    W --> R[Lookup and runbook functions]
    T[Synthetic ticket] --> A[One triage agent]
    A <--> R
    A --> D[Structured draft and tool-use log]
    D --> P[Manual review]
    D --> V[Evaluation]
    X[Separate expected outcomes] --> V
```

Captures become guidance through separate authoring and review. Evaluation expectations are loaded after model execution and never supplied to the agent or its tools.

## Components and storage

| Component | Responsibility |
| --- | --- |
| `cli.py`, `config.py`, `sdk.py` | Command dispatch, non-secret settings, live opt-in, lazy client construction |
| `cases/`, `capture.py` | Four broken/corrected reproductions; response and exception capture |
| `runbooks.py`, `runbooks/` | Static registry, diagnostic lookup, discovery, and support guidance |
| `agent.py`, `tickets.py`, `artifacts.py` | Agent loop, safe ticket input, grounding, sanitized run records |
| `evaluation.py`, `triage/` | Synthetic tickets, agent instructions, separate expectations, and scoring |
| `evidence/`, `tests/`, `docs/` | Reviewed observations, offline software checks, and explanatory guides |

The checkout holds eight reviewed reproduction captures, 13 saved triage runs, my [manual review](../evidence/triage/manual-review.md), and three separate approved edits. New artifacts go under ignored `artifacts/`. The [batch manifest](../evidence/triage/batch.json) distinguishes execution and publication hashes. Runbook and ticket resources resolve from the checkout; standalone wheel resource distribution is deferred.

## Environment and model

The package targets Python 3.14, with dependencies locked through `uv`: `openai`, `openai-agents`, Pydantic, PyYAML, and pytest for development. The CLI uses standard-library argument parsing.

`API_SUPPORT_LAB_MODEL` overrides the default `gpt-6.1-sol`; reasoning effort is explicitly `low`. Settings contain no credential. Client construction checks live opt-in before reading `OPENAI_API_KEY`; the invalid-credential reproduction supplies an explicit override. The application does not load `.env` automatically. Both clients use the normal OpenAI API endpoint.

The agent uses the SDK's `Agent`, asynchronous `Runner.run`, and `function_tool`, with a Pydantic `output_type`. `configure_agents()` selects Responses, prepares model settings, and disables tracing without constructing a client or running a model. [Agents SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart), [structured agent output](https://developers.openai.com/api/docs/guides/agents/define-agents)

## Failure lab and evidence contract

Each case exposes `broken()` and `fixed()` on the same synthetic workload. The shared `capture()` wrapper receives the case, variant, callable, settings, explicit redaction credentials, and an optional output directory. It retains raw transport fields before parsing, normalizes responses or SDK exceptions, sanitizes, and writes JSON. It never loads credentials or constructs clients. Unexpected programming errors fail the command.

| Evidence fields | Meaning |
| --- | --- |
| `case`, `variant`, `captured_at` | Registry ID, broken/fixed variant, UTC timestamp locally or date in publication copies |
| `model`, `sdk_version`, `elapsed_ms` | Requested model, installed SDK version, monotonic duration |
| `outcome`, `exception_type` | Response, refusal, API error, client timeout, connection error, or SDK error |
| `http_status`, `error_type`, `error_code`, `error_param`, `message` | Available transport/error details or refusal message |
| `request_id`, `headers` | Available request ID and allowlisted diagnostic headers |
| `response_status`, `incomplete_reason` | Parsed completion fields |
| `output_excerpt`, `usage` | Sanitized excerpt, at most 1,000 characters, and available usage |
| `output_valid` | Full schema/content validation result, or null when inapplicable; absent in older evidence |
| `settings` | Effective token limit, reasoning effort, timeout, and retry settings |

Capture allows `x-request-id`, `retry-after`, and `x-ratelimit-*` headers. It redacts configured credentials and recognizable credential strings before truncation, including header values. Artifacts omit full prompts, response objects, clients, and environment dumps. Server error bodies contribute only their structured message; a missing message stays null. Usage normalization retains available token counts and cached-input/reasoning-output details.

Unavailable fields are null and unavailable headers are empty. `APITimeoutError` is caught before broader connection errors; without a received response, transport fields stay null. A timeout establishes neither stopped server processing nor zero usage. Offline doubles remain test fixtures.

Reproductions make one request with zero retries and `store=False`. Unique filenames and exclusive creation prevent overwriting; filesystem errors fail without another request. The default directory is checkout-relative `artifacts/evidence/`; explicit relative overrides follow the caller's working directory. Published copies use UTC dates and updated evidence links while preserving diagnostics and durations. Refreshed ticket hashes account for changed provenance links; customer-visible model input is unchanged.

### Case behavior

| Case ID | Broken variant | Corrected variant and verification |
| --- | --- | --- |
| `invalid_credentials` | Deliberately invalid credential | Environment credential on the same bounded request; completed response |
| `tool_schema` | Invalid function-tool property type | Valid schema; API acceptance and completion; tool execution disabled in both variants |
| `incomplete_output` | 128-token cap for a strict 32-item JSON workload | Larger allowance; completed status and full schema/content validation before excerpt truncation |
| `timeout` | 0.5-second client timeout | Suitable timeout on the same request; completed response with retries still disabled |

Corrected requests default to 2,048 output tokens and 60 seconds. CLI overrides are validated before client construction and recorded. The broken-schema predicate checks HTTP 400, `BadRequestError`, and a tools-related parameter without requiring exact error wording. The incomplete correction records `output_valid`; invalid JSON/schema/content fails verification, while incomplete/refused/error responses skip validation. Reasoning can consume the allowance before visible JSON appears. Each [runbook](../runbooks/) links its reviewed pair; an attempt check alone does not verify a pair or establish customer recovery.

## Runbooks and deterministic tools

Each support runbook presents symptoms, meaning, evidence requests, a correction, recovery checks, escalation, a customer reply template, and Notes with verification status and capture links. The four published runbooks are verified against one broken/corrected lab pair each. Those labels describe lab evidence. Customer recovery still requires usable output in the affected workflow. Experiment commands and publication procedures live in the [maintainer guide](reproduction-guide.md), outside the agent's tools.

```python
CaseId = Literal["invalid_credentials", "tool_schema", "incomplete_output", "timeout"]

def diagnose(status: int, error_code: str | None = None) -> list[CaseId]: ...
def list_runbooks() -> dict[CaseId, str]: ...
def get_runbook(case: CaseId) -> str: ...
```

The registry maps IDs to checkout-relative paths. `diagnose` validates HTTP status integers and returns registered status candidates or exact status/code matches in registry order; unknown combinations return `[]`. Captures support only 401/`invalid_api_key` and 400/`invalid_function_parameters` mappings. Status-only candidates remain hypotheses; HTTP 200 and absent transport fields have no diagnostic mapping.

`list_runbooks` returns IDs and the first prose paragraph as each symptoms description. `get_runbook` rejects unknown IDs and arbitrary paths; missing files fail explicitly. Incomplete output and timeout use symptom-based retrieval. SDK wrappers expose the same plain functions; the `get_runbook` parameter schema enumerates case IDs. These functions read local material without network requests or state changes.

## Agent input, output, and behavior

Safe YAML loading validates ticket ID, subject, body, nullable pasted error, and optional context/provenance metadata. Only subject, body, and pasted error reach the model; evaluation labels and provenance filenames do not.

| Result field | Contract |
| --- | --- |
| `category`, `candidate_runbooks` | A case ID, `undetermined`, or `out_of_scope`; candidate list contains known case IDs |
| `observed_evidence` | Verbatim ticket extracts supporting the decision |
| `basis` | `stated`, `inferred`, or `none` |
| `severity` | `low`, `medium`, `high`, or `unknown`, based on reported impact |
| `action` | `recommend_fix`, `request_info`, or `escalate` |
| `missing` | Readable summaries of actual information requests |
| `customer_reply`, `escalation_note` | Nonempty draft reply; routing summary when escalating |

Instructions distinguish diagnostic evidence from hypotheses, impact from error type, and suggested routing from a completed handoff. They call for sanitized requests, uncertainty where evidence is incomplete, and treating ticket content as data. These judgments remain subject to manual review.

Runtime validation enforces result shape, verbatim extracts, and successful retrieval of every cited case, including candidates. Lookup arguments must match explicit ticket fields recognized as HTTP status/code syntax, including quoted JSON. The recognizer does not classify arbitrary prose. Categories `undetermined` and `out_of_scope` require basis `none`; out-of-scope requests require escalation, and escalation requires a note.

By default, the runner uses `AsyncOpenAI` and `OpenAIResponsesModel` with a 60-second timeout, zero client/runner retries, `store=False`, eight turns, and a 4,096-token cap per model response. Global setup and `RunConfig` disable tracing. Hooks retain sanitized tool arguments/results and raw available usage. Tool errors propagate. API/model failure, refusal, turn exhaustion, or invalid/ungrounded output produces a failed record with no accepted draft; only exception/cause types and a fixed failure message are saved. These limits impose neither a whole-run deadline nor an account spending cap.

## CLI, execution boundaries, and budget

```text
uv run python -m api_support_lab reproduce CASE --variant broken|fixed --live
uv run python -m api_support_lab diagnose --status STATUS [--error-code CODE]
uv run python -m api_support_lab triage TICKET.yaml --live
uv run python -m api_support_lab evaluate --live
uv run --offline --locked --no-env-file python -m api_support_lab evaluate --results PATH
uv run pytest
```

API commands require `--live` before client construction. Live evaluation and saved-result scoring are mutually exclusive. Offline scoring needs no credential or client. Pytest skips live-marked tests without `--run-live` and blocks DNS/socket connections inside its process for offline tests. The current suite contains no live API tests; its opt-in policy probe is harmless. `--no-env-file` prevents uv from loading an environment file.

Triage and evaluation accept `--output-dir`, defaulting to checkout-relative `artifacts/triage/` and `artifacts/evaluation/`. Evaluation also saves individual runs. Accepted triage drafts and fully passing evaluations exit 0; failed attempts, input/data issues, or mismatches exit 1; configuration/argument errors exit 2. Reproduction exit 0 means its per-attempt predicate matched, as detailed in the maintainer guide.

## Evaluation design

The 13 synthetic tickets cover supported cases, partial/misleading evidence, intermittent parsing failures, unfamiliar errors, unsupported requests, sensitive-data routing, and an authentication outage. Five paste live-capture diagnostics; authored scenarios do not establish observed API behavior.

The scorer checks shape/grounding, ticket identity, category, basis, action, severity, retrieval, and selected diagnostic literals. Expectations separately hold information-request and evidence-review criteria, exposed as `manual_review_criteria` and `manual_evidence_criteria`. Those criteria and the wording of `missing` do not affect automated agreement; question usefulness, evidence relevance/sufficiency, and reply correctness require [manual review](manual-review.md).

Live evaluation runs tickets once, sequentially, with no retries; ticket failures remain in the denominator. Reports separate operational failures from semantic mismatches and record settings, SDK versions, timestamps, ticket hashes, and the expectations hash. Offline scoring accepts a run, a report containing runs, or a directory; missing/duplicate/corrupt records and hash drift stay visible. Directory rescoring initializes pending review fields rather than importing Markdown verdicts.

The published batch scored 13/13 with no operational failures or semantic mismatches. My separate review recorded 9 Send as-is, 3 Send with edits, 1 Would not send, and 51 satisfied criteria. Generated replies remain unchanged; approved edits are separate. All 13 samples were used during development, with no holdout set, so the batch does not establish unseen-ticket performance.

## Tradeoffs and remaining verification

| Choice | Benefit and cost |
| --- | --- |
| One agent with three function tools | Makes retrieval inspectable; adds orchestration compared with one prompt containing every runbook |
| Plain functions and files | Easy to read and test; deliberately limited search and persistence capabilities |
| Explicit capture wrapper | Handles success and exceptions in one place without decorator indirection |
| Four cases before expanding coverage | Leaves time for evaluation; many real errors remain outside the registry |
| Python 3.14 and one model default | A single documented environment; dependency and account compatibility must be checked |
