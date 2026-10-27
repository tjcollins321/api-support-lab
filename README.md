# API Support Lab

I designed this Python lab to reproduce four OpenAI API failures, document each in a support runbook, and evaluate a triage agent that uses those runbooks to draft replies to synthetic support tickets. I manually review the replies before treating them as examples I would send.

I use the OpenAI Responses API and the Agents SDK (`openai-agents`), with Codex providing code generation and prose drafting under my direction.

The saved reproductions and agent runs used `gpt-6.1-sol` (`openai` 3.36.0; the agent also used `openai-agents` 0.24.0). The reproduction captures are dated 2026-10-22 UTC; the reviewed agent batch is dated 2026-10-27 (UTC and America/New_York).

## A saved example

A synthetic ticket reports: “The API returned HTTP 200 but our JSON parser failed on the response.” The nightly report is blocked, and completion details and failing output were not retained.

The agent retrieved the incomplete-output runbook and returned these fields:

```json
{
  "category": "incomplete_output",
  "basis": "inferred",
  "severity": "high",
  "action": "request_info"
}
```

Its saved reply begins:

> Thanks for sharing the parser error and explaining that your nightly report is blocked. HTTP 200 shows that a response arrived, but the parser error alone cannot distinguish incomplete generation from an extraction or JSON-format issue; it does not establish that the output limit was reached.

The category is a hypothesis; the severity comes from the blocked report; the next step is to collect completion details and a sanitized failing excerpt.

This excerpt comes from the [published T-006 run](evidence/triage/runs/T-006.json) in the batch I reviewed on 2026-10-27. I found its manual review criteria satisfied and selected **Send with edits**, removing one redundant sentence later in the reply. I saved the [edited wording](evidence/triage/edited-replies/T-006.md) separately. The [walkthrough](docs/walkthrough.md) follows this example alongside a supported correction, an escalation, and a misleading customer diagnosis.

## What is implemented

| Case | Synthetic reproduction setup | Observed result (live, 2026-10-22 UTC) | Runbook |
| --- | --- | --- | --- |
| Invalid credentials | Deliberately invalid API key | HTTP 401 `AuthenticationError`, code `invalid_api_key` | [invalid_credentials](runbooks/invalid_credentials.md) |
| Malformed tool schema | `"type": "not_a_json_schema_type"` in a strict function tool | HTTP 400 `BadRequestError`, code `invalid_function_parameters`, param `tools[0].parameters` | [tool_schema](runbooks/tool_schema.md) |
| Incomplete structured output | `max_output_tokens: 128` for a 32-item JSON-schema workload | HTTP 200 with `response_status: incomplete`, `incomplete_reason: max_output_tokens` | [incomplete_output](runbooks/incomplete_output.md) |
| Client timeout | 0.5-second client timeout, zero retries | `APITimeoutError` after about 620 ms; no HTTP status, request ID, or usage | [timeout](runbooks/timeout.md) |

The table combines request setup from the [case implementations](src/api_support_lab/cases/) with observed fields from the captures linked in each runbook.

For ticket triage, I use one agent with three read-only tools. It returns a structured decision and draft reply for each of the [13 sample tickets](triage/tickets/). I published date-only copies of all 13 [records](evidence/triage/runs/), my [manual review](evidence/triage/manual-review.md), and three separately recorded edited replies.

The four cases cover two errors with a diagnostic code to look up (401 and 400), an HTTP-success response whose output is incomplete, and a client timeout without a received response. In two of the four, the status code alone does not tell you what went wrong.

The failure scope was kept deliberately small to leave more time for the triage agent and ticket-based testing. Rate limits, quota, model access, and context overflow are out of scope, as are MCP, hosting, and external ticketing.

The shared tools are ordinary Python functions: `diagnose`, `list_runbooks`, and `get_runbook`. Exact diagnostic matches come from reviewed observations. Unknown codes remain unmatched, and symptom-based retrieval supports cases without a diagnostic status/code mapping.

## Quick start

Needs Python 3.14 and [uv](https://docs.astral.sh/uv/getting-started/installation/) on your `PATH`; uv can fetch Python if needed. Run these commands from a checkout:

```sh
uv sync --locked
uv run python -m api_support_lab diagnose --status 401 --error-code invalid_api_key
uv run pytest -q
uv run python -m api_support_lab evaluate --results evidence/triage/runs
```

None of these commands need an API key. `diagnose` prints `["invalid_credentials"]`, a candidate for investigation. Tests use dummy credentials and an in-memory transport; a pytest DNS/socket guard blocks unexpected network access during offline execution. `evaluate --results` scores the saved outputs against `triage/expected.yaml` without calling the model. For the approved batch and current expectations, this command reports **13/13** under the scorer and exits **0**. Manual review verdicts remain separate from that score. It does not rerun the agent. Generated files go under ignored `artifacts/`. The fully locked-down command forms are in the [reproduction guide](docs/reproduction-guide.md#offline-checks-and-references).

For a live draft, copy `.env.example` to `.env`, configure your own project key, and explicitly load it:

```sh
uv run --locked --env-file .env python -m api_support_lab triage triage/tickets/T-006.yaml --live
```

The application does not automatically load `.env`; it is ignored by Git. Live commands require `--live` and may incur charges. The agent reads runbooks and drafts replies; it cannot send messages, run reproductions, or change accounts. Review every draft before use.

## How it works

```mermaid
flowchart TD
    A[Broken or corrected client call] --> B[OpenAI Responses API]
    B --> C[Capture response or SDK exception]
    C --> D[Sanitized evidence]
    D -->|Write and review guidance| E[Support runbooks]
    T[Synthetic ticket] --> F[Triage agent]
    F <--> G[Diagnosis lookup and runbook tools]
    E --> G
    F --> H[Structured decision and draft reply]
    H --> I[Manual review]
    H --> J[Evaluation against separate expectations]
```

Capture keeps the diagnostic fields, effective settings, a bounded output excerpt, and available usage. Code checks the shape of the result, that any runbook the agent cites was actually retrieved, and that lookup arguments came from the ticket. Whether the prose is right is still a person's call. Evidence relevance and sufficiency, information-request coverage, and agreement with the readable `missing` summary are assessed through [manual review](docs/manual-review.md). Automated diagnostic-preservation checks cover selected literal diagnostics; they do not establish evidence quality.

Three rules shape the agent:

- It passes only ticket-stated status/code values to `diagnose`. For [T-005](triage/tickets/T-005.yaml), the customer's authentication suspicion supplies neither; the saved agent run lists runbooks, retrieves credential guidance, and asks for diagnostics instead of guessing a lookup code.
- It must retrieve supporting guidance before recommending a case-specific fix. A result referencing a runbook it never retrieved is rejected.
- `basis` records whether supplied diagnostics directly support the category (`stated`), symptoms support a hypothesis (`inferred`), or no supported category is determined (`none`). For [T-008](triage/tickets/T-008.yaml), pasted schema diagnostics take precedence over the customer's authentication claim.

## Results and limits

Each case has one reviewed live broken/corrected pair — a reproduction, not a benchmark.

I evaluated all 13 synthetic sample tickets sequentially on 2026-10-27, once each, with no client or runner retries. The agent used low reasoning, a 4,096-token cap per model response, at most eight turns per ticket, a 60-second client timeout, `store=False`, and disabled tracing. These bounds are not a whole-batch deadline or spending cap.

| Assessment | Recorded result |
| --- | --- |
| Automated agreement | **13/13**; 0 operational failures, 0 semantic mismatches; offline rescore matched |
| My send verdicts | **10 Send as-is**, **3 Send with edits**, **0 Would not send** |
| Manual review criteria | **51 Satisfied**: 26 information-request and 25 evidence criteria |

I kept the untouched originals in ignored local artifacts and published [date-only copies](evidence/triage/runs/). The generated replies, decisions, usage, and elapsed durations are unchanged; capture dates and evidence references were simplified for publication. My [manual review](evidence/triage/manual-review.md) records the judgments and supporting excerpts, and [edited replies](evidence/triage/edited-replies/) contain the wording I approved for T-006, T-010, and T-013. The [batch manifest](evidence/triage/batch.json) distinguishes original and published hashes. My approval does not change automated findings.

I used these samples during development, with no separate holdout group. The results demonstrate this workflow on those inputs and do not establish unseen-ticket performance or general reliability. Available usage is recorded; missing usage remains unknown. The [development notes](docs/development-notes.md) explain my contributions and design decisions.

The offline tests (279, mostly parametrised) cover capture, redaction, tool schemas, the agent loop against an in-memory transport, and scoring. They test the software, not the quality of a live reply. All organizations and tickets are invented.

## Explore further

- [Walkthrough](docs/walkthrough.md): four saved decisions, actual replies, and a code-reading path.
- [Manual review](docs/manual-review.md): assessing actual questions, with a model grader left as future work.
- [Development notes](docs/development-notes.md): project attribution, the design calls, and how the agent was tuned.
- [Architecture](docs/architecture.md): components, interfaces, and design tradeoffs.
- [Reproduction guide](docs/reproduction-guide.md): running the cases and publishing evidence.
