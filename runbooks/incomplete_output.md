# Incomplete structured output

An HTTP-success response is incomplete or a JSON parser fails; check response completion status and incomplete reason before treating output-budget exhaustion as the cause.

Use this runbook to distinguish incomplete generation from parsing or application-validation problems, and confirm that the customer's output is complete and usable after a correction.

## Evidence and confidence

- Status: `verified` — one reviewed live lab pair supports this guidance; it does not diagnose the customer's request.
- Verified on: `2026-10-22` (America/New_York and UTC).
- Observed evidence: [budget-exhausted response](../evidence/incomplete_output/broken-20261022T232333Z.json) and [successful correction](../evidence/incomplete_output/fixed-20261022T232346Z.json).
- The lab observed HTTP 200 with status `incomplete` and reason `max_output_tokens`, followed by a completed response whose full output passed schema/content validation. This does not establish that an arbitrary parser failure has the same cause.

## Evidence to request

- Response completion status, incomplete reason/details, any refusal or response error, and request ID if received.
- The configured output-token limit, reasoning setting, model, SDK version, and UTC attempt time.
- The parser/validation error, expected schema, and a minimal sanitized failing output excerpt. An excerpt may itself be truncated; ask whether it represents all returned text.
- The affected workflow and its impact, including whether a report or other task is blocked. Request no sensitive records, full prompts, credentials, or full logs.

## Diagnosis and alternative explanations

An explicit `incomplete` status with reason `max_output_tokens` supports output-budget exhaustion. Reasoning may consume the budget before visible JSON appears. HTTP success plus a parser failure alone does not establish that cause.

Other explanations include content-filter termination, refusal, extraction of the wrong response field, a schema mismatch, or an application parser bug. A completed response that fails schema/content validation needs investigation even if it parses as JSON. Treat transport failure separately from a response that arrived incomplete.

## Corrective steps

1. Inspect completion status, incomplete details, refusal, and errors before parsing or consuming the output as a successful result.
2. When the supplied reason establishes output-budget exhaustion, choose a larger bounded output allowance appropriate to the model and workload, or reduce the requested payload. Account for reasoning as well as visible output; there is no universal token limit that fixes every workload.
3. If output is completed but parsing or validation fails, investigate response extraction, parser behavior, and the expected schema/content instead of assuming that increasing the budget will fix it.
4. Have the application maintainer apply the supported change and arrange a controlled check of the affected workflow.

## Confirm recovery

Inspect the customer's full returned output, not just a shortened log excerpt. Confirm completed status without an incomplete reason, refusal, or response error. Parse the intended output field and validate both its schema and the task's required content.

Confirm that the previously affected workflow now uses the result successfully. HTTP 200 or parseable JSON alone is insufficient, and a partially emitted payload must not be accepted as a completed task. If the correction fails, retain the actual completion and validation details.

## Escalation checklist

- Escalate persistent incomplete output within appropriate workload limits, or completed output that still fails the expected schema/content checks.
- Include status, incomplete reason, output/reasoning settings, model/SDK, UTC time, and request ID if available.
- Supply minimal sanitized schema/output and parser-error excerpts, stating any excerpt truncation.
- Describe the change attempted and its effect on the customer's task. Route to the application maintainer or appropriate API support channel without claiming a handoff.

## Illustrative draft reply

“Could you share the response status, incomplete reason, output-token limit, and a small sanitized excerpt that fails parsing? If the response confirms output-budget exhaustion, a larger bounded allowance or smaller payload may help. Then check completion, schema, and required content before using the result.”

This is an illustrative draft for human review, not an executed agent result. A blocked workflow establishes impact without establishing the cause.

## Sources

- [Official structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Official reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
- [OpenAI Python SDK and Responses interfaces](https://developers.openai.com/api/reference/python)

These references describe expected behavior; they are not observed evidence for this lab's case.
