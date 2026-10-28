# Walkthrough: four saved support decisions

I evaluated and reviewed 13 synthetic tickets on **2026-10-27**, using `gpt-6.1-sol`, `openai` 3.36.0, and `openai-agents` 0.24.0. These four examples show the resulting decisions. Each [published record](../evidence/triage/runs/) contains the generated result, draft, tools, and available usage. I retained full timestamps locally and published date-only copies. No installation or API access is needed to follow along.

All tickets and organizations are invented. T-003 and T-008 paste diagnostics from the live reproduction captures; T-006 and T-009 are scenarios without one. The quotes below preserve the complete original drafts; Markdown list spacing is adjusted for readability. Approved edits are linked separately.

## 1. Supported correction: incomplete output

[T-003](../triage/tickets/T-003.yaml) reports invalid or cut-off structured JSON with a configured output allowance of 128 tokens. The supplied diagnostics are:

```text
HTTP 200
response_status: incomplete
incomplete_reason: max_output_tokens
```

The incomplete status and explicit reason support output-budget exhaustion. Two tool calls completed in order:

| Tool | Saved JSON arguments | Status |
| --- | --- | --- |
| `diagnose` | `{"status": 200, "error_code": null}` | `completed` |
| `get_runbook` | `{"case": "incomplete_output"}` | `completed` |

The `diagnose` lookup returned `[]`; HTTP 200 is not a registered mapping. The case IDs are visible in the `get_runbook` and result schemas, and `incomplete_output` matches the ticket's `response_status: incomplete`, so the model went straight to that [runbook](../runbooks/incomplete_output.md); it still had to retrieve it before citing it. Tickets with no matching name (T-006, below) list the runbooks first.

| Saved field | Value |
| --- | --- |
| `category` | `incomplete_output` |
| `basis` | `stated` |
| `severity` | `unknown` |
| `action` | `recommend_fix` |
| `missing` | 2 readable information-request summaries; see the published record |

**Original customer draft, complete:**

> Thanks for sharing the completion details and your 128-token limit; they explain why your structured JSON is being cut off. HTTP 200 means a response arrived, but `response_status: incomplete` with `incomplete_reason: max_output_tokens` shows that generation exhausted its output allowance.
>
> Increase `max_output_tokens` above 128 to fit the expected JSON, or request less output. There is no universal suitable limit; on reasoning models, the allowance also covers reasoning tokens, not just visible JSON.
>
> Before parsing, check completion status, incomplete details, and any refusal or response error. Do not treat partial output as a completed result.
>
> Please retry and confirm that the response completes without an incomplete reason, refusal, or response error, that the full JSON validates against your expected schema, and that your application can use it successfully. If it still fails, share your model, reasoning setting, and SDK version.
>
> The retry result will help determine whether the budget adjustment resolves the issue or further investigation is needed.

The [broken capture](../evidence/incomplete_output/broken-2026-10-22.json) records HTTP 200, `incomplete`, and `max_output_tokens` at 128 tokens. The [correction](../evidence/incomplete_output/fixed-2026-10-22.json) records `completed` and `output_valid: true` at 2,048 tokens, using the same schema and 32-item workload. Validation checked full output before excerpt truncation; the saved excerpt cannot reconstruct the complete JSON.

The budget must suit the actual workload. Severity stays unknown without reported impact. I selected **Send as-is** and found all four manual review criteria were met, including usable-output validation after correction.

## 2. Missing evidence: parser failure with HTTP success

[T-006](../triage/tickets/T-006.yaml) reports:

> Our nightly report is blocked. The API returned HTTP 200 but our JSON parser failed on the response. We don't log the completion details or keep the failing output, so I don't have those yet. What should we collect to figure out what's going on?

The pasted error is `JSONDecodeError: Expecting ',' delimiter`. Completion details and failing output were not retained. Incomplete generation, field extraction, and parsing remain possible causes.

| Tool | Saved JSON arguments | Status |
| --- | --- | --- |
| `list_runbooks` | `{}` | `completed` |
| `get_runbook` | `{"case": "incomplete_output"}` | `completed` |

| Saved field | Value |
| --- | --- |
| `category` | `incomplete_output` |
| `basis` | `inferred` |
| `severity` | `high` |
| `action` | `request_info` |
| `missing` | 4 readable information-request summaries; see the published record |

**Original customer draft, complete:**

> Thanks for sharing the parser error and explaining that your nightly report is blocked. HTTP 200 shows that a response arrived, but the parser error alone cannot distinguish incomplete generation from an extraction or JSON-format issue; it does not establish that the output limit was reached.
>
> Please collect and share:
>
> 1. On the next failing run, before parsing: the response's status, incomplete_details, any refusal or response error, and request ID if received. You do not need to recover output that was not saved.
> 2. Your model, SDK version, configured max_output_tokens, and reasoning setting.
> 3. The expected JSON schema and a minimal sanitized code snippet showing which response field you select and how you extract and parse it. On the next failure, also capture a short sanitized output excerpt and indicate whether it includes all returned text or was shortened for logging or sharing. Please omit sensitive records and credentials, and do not send full logs or request bodies.
> 4. When this started, whether every request fails or only some, any input-size or dataset changes, and the UTC times of the next failing run and last successful run if available.
>
> These details will help distinguish incomplete generation from an extraction or parser issue and guide the appropriate correction.

The category remains a hypothesis. High severity follows the blocked report. The reply asks the customer to **collect and share** completion fields and a sanitized failing excerpt from a future failure, including whether the excerpt was shortened. It also requests the extraction/parsing path and expected structure.

I selected **Send with edits** and found all five manual review criteria were met. The approved edit removes “You do not need to recover output that was not saved.” because the next-failing-run request is sufficient. The [edited reply](../evidence/triage/edited-replies/T-006.md) is separate from the [published JSON](../evidence/triage/runs/T-006.json).

## 3. Escalation: an unsupported setup request

[T-009](../triage/tickets/T-009.yaml) asks:

> Can you enable SSO and set up identity-provider groups for our employee portal? I'm not sure if this is the right queue, please point us to whoever can help with this.

| Tool | Saved JSON arguments | Status |
| --- | --- | --- |
| `list_runbooks` | `{}` | `completed` |

Only `list_runbooks` appears in the log. No case runbook was retrieved or cited; the SSO and identity-provider setup request is outside the registry’s API-failure guidance.

| Saved field | Value |
| --- | --- |
| `category` | `out_of_scope` |
| `basis` | `none` |
| `severity` | `unknown` |
| `action` | `escalate` |
| `missing` | 0 readable information-request summaries; see the published record |

**Original customer draft, complete:**

> Thank you for explaining that you need SSO and identity-provider groups configured for your employee portal. This is an identity and access administration request rather than an API troubleshooting issue, so it falls outside the available troubleshooting guidance. Please route it to your organization's IT or identity and access management team, working with the employee portal administrator. They can determine the required SSO configuration and group mappings.

The escalation note suggests the customer’s IT/identity team and portal administrator, accurately describes a configuration request without API diagnostics, and records that no change or transfer occurred. I would still need to perform any routing. I selected **Send as-is** and found both manual review criteria were met.

## 4. Misleading diagnosis: a key-replacement request with schema evidence

[T-008](../triage/tickets/T-008.yaml) says:

> Juniper Demo here. Our app is throwing an error. We think our API key is the problem and want to rotate it. Can you confirm that's the fix? Here's the error we're getting.

The supplied error identifies `invalid_function_parameters` at `tools[0].parameters` and names the invalid value `not_a_json_schema_type`.

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
| `missing` | 4 readable information-request summaries; see the published record |

**Original customer draft, complete:**

> Thanks for sharing the error you're seeing in your app; it identifies a function-tool schema problem rather than evidence that your API key needs replacing. Rotating the key is not the indicated fix for this error.
>
> In the serialized definition for `support_label`, inspect `tools[0].parameters` and replace `not_a_json_schema_type` with the supported JSON Schema type intended for that value. The error does not identify the precise property, so check the transmitted definition rather than only your source definition. If strict mode is enabled, ensure every object's properties are included in `required` and each object has `additionalProperties: false`.
>
> Could you:
> 1. Share the smallest sanitized serialized tool-definition excerpt containing the affected property and its enclosing schema, removing sensitive descriptions and examples—not the full request or credentials?
> 2. Confirm the endpoint, model, SDK version, strict-mode setting, and any transformations between your application definition and the transmitted schema?
> 3. Say whether this schema previously worked, what changed, whether every request using it fails or only some, and whether your workflow is blocked or has a usable workaround?
> 4. Rerun after the correction and report whether validation succeeds and your workflow completes, including function execution and result handling if a function call occurs. If validation still fails, share the sanitized new error details, request ID if received, and the attempt's UTC time.
>
> The excerpt and rerun result will help confirm the correction or identify the next schema check.

The selected evidence contains the supplied schema diagnostics. The customer’s key hypothesis does not establish the cause. The reply recommends a schema correction and requests the smallest serialized excerpt without prescribing key rotation. I selected **Send as-is** and found all four manual review criteria were met.

## Follow T-006 through the code

| Stage | Code and responsibility |
| --- | --- |
| Ticket input | [`Ticket.model_input()`](../src/api_support_lab/tickets.py) sends only subject, body, and pasted error. Organization metadata, provenance, and expected outcomes do not enter that input. |
| Model and tools | [`build_agent()` and `triage_ticket()`](../src/api_support_lab/agent.py) configure the tools and structured output, then execute `Runner.run`. The model chooses calls; the SDK runs the loop. |
| Validation and capture | `validate_grounding()` checks retrieval and verbatim ticket evidence; `ToolRecorder` logs tools and available usage. The result is sanitized and saved through [`save_record()`](../src/api_support_lab/artifacts.py). |
| Evaluation | [`score_runs()`](../src/api_support_lab/evaluation.py) checks saved results against [`expected.yaml`](../triage/expected.yaml). Live execution loads expectations after model runs. Offline rescoring reads saved runs. |

Inspect T-006’s `result` and `tool_use`, then rescore the saved runs to inspect its evaluation row. The model chose the action, category, and severity. Validation checks structure and grounding; evaluation checks expected decisions. Question coverage, agreement with `missing`, and evidence quality require [manual review](manual-review.md).

## What the results establish

The complete batch has **13/13 automated agreement** under the automated scorer, with **0 operational failures** and **0 semantic mismatches**. My separate [manual review](../evidence/triage/manual-review.md) records **9 Send as-is**, **3 Send with edits**, **1 Would not send**, and all **51 manual review criteria satisfied**. Edited wording for T-006, T-010, and T-013 is labeled separately; the generated replies remain unchanged in the date-only JSON copies.

The additional [T-012 review](../evidence/triage/manual-review.md#t-012) checks completion-versus-parsing uncertainty and medium severity for a retry workaround. The [T-013 review](../evidence/triage/manual-review.md#t-013) checks a deployed credential source after two rotations during a customer-facing outage. The [T-011 review](../evidence/triage/manual-review.md#t-011) is the case where every criterion holds and the reply is still not one I would send.

I used these 13 synthetic samples during development, without a separate holdout. They illustrate this workflow on these inputs and do not establish general reliability. Future replies still need review. The [offline command](../evidence/triage/README.md#reproduce-the-score-offline) rescores the published records without an API key or new model calls.
