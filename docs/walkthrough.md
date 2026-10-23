# Walkthrough: four saved support decisions

These examples come from the [final live evaluation](../evidence/triage/ten-ticket-follow-up-20261022/reviewed-evaluation.json) on 2026-10-22, America/New_York. Search its `runs` entries by `ticket_id` for complete records. No installation or API access is needed to follow along.

All tickets and organizations are invented. T-003's pasted diagnostics quote selected fields from a saved live API capture in `evidence/`; T-006 and T-009 are authored scenarios. Quoted drafts preserve recorded wording; Markdown list spacing is adjusted for readability. Commentary appears outside the quotes.

## 1. Supported correction: incomplete output

[T-003](../triage/tickets/T-003.yaml) asks about structured JSON requested with `max_output_tokens` set to 128. Its supplied diagnostics are:

```text
HTTP 200
response_status: incomplete
incomplete_reason: max_output_tokens
```

The fields establish output-budget exhaustion. Two tool calls completed in order:

| Tool | Saved JSON arguments | Status |
| --- | --- | --- |
| `list_runbooks` | `{}` | `completed` |
| `get_runbook` | `{"case": "incomplete_output"}` | `completed` |

The agent retrieved the [incomplete-output runbook](../runbooks/incomplete_output.md) through discovery. HTTP 200 is not a registered failure mapping.

| Saved field | Value |
| --- | --- |
| `category` | `incomplete_output` |
| `basis` | `stated` |
| `severity` | `unknown` |
| `action` | `recommend_fix` |
| `missing` | `["impact"]` |

**Saved customer draft, complete:**

> The returned status and reason establish output-budget exhaustion: HTTP 200 does not mean the structured output completed. Have the application maintainer increase max_output_tokens above 128 to a bounded allowance appropriate to the model and workload, or reduce the requested JSON payload. Account for reasoning tokens as well as visible output; there is no universal correct limit.
>
> During an authorized check of the affected workflow, inspect completion status before consuming the result. Confirm completed status with no incomplete reason, refusal, or response error, then parse the intended output field from the full returned output and validate both the expected schema and required content. Finally, confirm Aspen Demo successfully uses the result; parseable JSON alone is not sufficient, and partial output should not be accepted as a completed task.
>
> What workflow impact is this causing—for example, is the task blocked or is there a workaround?

The [broken capture](../evidence/incomplete_output/broken-20261022T232333Z.json) records HTTP 200, `incomplete`, and `max_output_tokens` at 128 tokens. The [correction](../evidence/incomplete_output/fixed-20261022T232346Z.json) records `completed` and `output_valid: true` at 2,048 tokens, using the same schema and 32-item workload. Validation checked full output before excerpt truncation; the saved excerpt cannot reconstruct the complete JSON.

The budget must suit the actual workload. Severity stays unknown without reported impact. Human review should check applicability and usable output after correction.

## 2. Missing evidence: parser failure with HTTP success

[T-006](../triage/tickets/T-006.yaml) reports:

> The invented Willow Demo team's nightly report is blocked. The API returned HTTP 200, but our JSON parser failed. We have not saved completion details or a failing output excerpt yet. What should we collect to distinguish the cause?

The pasted error is `JSONDecodeError: Expecting ',' delimiter`. Completion details are absent; incomplete generation, field extraction, and parsing remain possible causes.

The saved run again completed `list_runbooks` with `{}`, followed by `get_runbook` with `{"case": "incomplete_output"}`. Retrieving the same guidance does not make the evidence equally conclusive.

| Saved field | Value |
| --- | --- |
| `category` | `incomplete_output` |
| `basis` | `inferred` |
| `severity` | `high` |
| `action` | `request_info` |

**Saved customer draft, complete:**

> HTTP 200 confirms a response arrived, but not that its output was complete. The parser error alone does not establish token-budget exhaustion; extraction or parsing problems are also possible.
>
> During the next authorized check of the affected nightly report, please collect:
>
> - Response completion status, incomplete reason/details, and any response error or refusal (or note their absence); the request ID if received.
> - Configured max_output_tokens, reasoning setting, model, SDK version, and UTC attempt time.
> - Minimal sanitized parser/extraction context: which response field is parsed, the relevant parsing step, and the expected JSON structure/schema. The error line is already supplied.
> - A minimal sanitized failing output excerpt, stating whether it contains all returned text or is truncated.
>
> Please exclude credentials, sensitive records, full prompts, and full logs. Inspect completion details before treating the output as successful; do not increase the output budget solely on the basis of this parser error.

The category remains a hypothesis. High severity follows the blocked report, independently of HTTP status.

The twelve `missing` fields cover completion, configuration, timing, parsing, and output. The complete request is appropriate for distinguishing the cause of this blocked workflow. Recorded review passed the grounded questions and uncertainty; automated agreement alone does not establish usefulness.

In my [review](../evidence/triage/ten-ticket-follow-up-20261022/owner-review.md#t-006), I recommend comparing the failed report with an earlier successful run, checking dataset-size changes and existing completion logs, and considering a smaller-payload diagnostic trial without assuming token-budget exhaustion.

## 3. Escalation: an unsupported setup request

[T-009](../triage/tickets/T-009.yaml) asks:

> Can you enable SSO and configure identity-provider groups for the invented Cedar Demo employee portal? We need someone to route this setup request.

Only `list_runbooks` with `{}` appears in the log. No case runbook was retrieved or cited; this setup request falls outside the registry's API-failure coverage.

| Saved field | Value |
| --- | --- |
| `category` | `out_of_scope` |
| `basis` | `none` |
| `severity` | `unknown` |
| `action` | `escalate` |
| `candidate_runbooks` / `missing` | `[]` / `[]` |

**Saved customer draft, complete:**

> SSO enablement and identity-provider group configuration are outside API Support Lab’s troubleshooting scope. Please route this setup request to the Cedar Demo portal administrator or your organization’s identity and access management team. They can coordinate the configuration with the identity-provider administrator. No configuration changes or handoff have been performed here.

The escalation note suggests the portal administrator or identity team and records no supplied error or impact. A person must identify the owner and perform the handoff.

In my [review](../evidence/triage/ten-ticket-follow-up-20261022/owner-review.md#t-009), I recommend making the routing actionable with official setup documentation or an appropriate assistance link once the platform or identity provider is known.

## 4. Misleading diagnosis: a key-replacement request with schema evidence

[T-008](../triage/tickets/T-008.yaml) says the team "believes authentication is the cause and asks whether to replace the key", but pastes HTTP 400 `invalid_function_parameters` for `tools[0].parameters`.

Two tool calls completed in order:

| Tool | Saved JSON arguments | Status |
| --- | --- | --- |
| `diagnose` | `{"status": 400, "error_code": "invalid_function_parameters"}` | `completed` |
| `get_runbook` | `{"case": "tool_schema"}` | `completed` |

| Saved field | Value |
| --- | --- |
| `category` | `tool_schema` |
| `basis` | `stated` |
| `severity` | `unknown` |
| `action` | `recommend_fix` |
| `missing` | `["tool_schema", "impact"]` |

**Saved customer draft, complete:**

> The evidence supports checking the function-tool schema first, not replacing the API key. The error explicitly identifies `tools[0].parameters` for `support_label` and rejects `not_a_json_schema_type` as invalid schema content; it does not establish an authentication problem.
>
> Have the application maintainer inspect the serialized tool definition, locate that invalid type value, and replace it with the intended supported JSON Schema type while preserving the intended constraints. Compare the transmitted schema with the application definition for any transformations. After the correction, an authorized maintainer should confirm that the request is accepted and the affected workflow completes, including function execution and result handling if applicable.
>
> Please share the smallest sanitized serialized schema excerpt containing the affected property and its enclosing schema, with sensitive descriptions/examples removed, so the precise correction can be confirmed. Also, is the affected workflow blocked, degraded with a workaround, or unaffected?

The customer's assertion appears in `observed_evidence` as a quoted extract, but it does not become the category. The reply identifies the invalid type from the error, requests the smallest schema excerpt containing it, and does not suggest replacing the key.

## Follow T-006 through the code

Read the saved run alongside these entry points:

| Stage | Code and responsibility |
| --- | --- |
| Ticket input | [`Ticket.model_input()`](../src/api_support_lab/tickets.py) serializes only subject, body, and pasted error. Organization metadata, provenance, and expected outcomes do not enter that input. |
| Model and tools | [`build_agent()` and `triage_ticket()`](../src/api_support_lab/agent.py) configure the three tools and structured output, then execute `Runner.run`. The model chooses tool calls; the SDK runs the loop. |
| Validation and capture | In the same module, `validate_grounding()` checks retrieval and verbatim ticket evidence; `ToolRecorder` logs tools and usage. A validated result is sanitized and saved through [`save_record()`](../src/api_support_lab/artifacts.py). |
| Evaluation | [`score_runs()`](../src/api_support_lab/evaluation.py) checks the saved result against [`expected.yaml`](../triage/expected.yaml). Live batch execution loads those expectations after model runs. Offline rescoring reads saved runs. |

Inspect T-006's `result`, `tool_use`, and evaluation row. The model chose the action, category, and severity. Validation checks structure and grounding; evaluation checks expected decisions. Neither independently proves the reply correct or useful.

## What the results establish

All four examples passed automated checks in the saved final report. I reviewed all ten saved final drafts and found their general suggested next steps accurate. My [review notes](../evidence/triage/ten-ticket-follow-up-20261022/owner-review.md) record recommendations for diagnostic follow-up, customer communication, and escalation. The saved evaluation report reached 10/10 after tuning on the same ten tickets. The preserved baseline includes an operational timeout on T-006; the [evaluation record](evaluation-follow-up.md) explains subsequent changes and the separate scorer revision. These are documented support cases with saved outputs and manual review; they do not establish general reliability or approval for customer use.

The runbooks have since received documentation edits without a new live evaluation. The saved tool logs retain the guidance used for these replies; offline agreement does not validate the revised runbooks.

Use the [offline rescoring command](../README.md#quick-start) to create a new local score without generating another reply or changing public evidence.
