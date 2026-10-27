# Incomplete structured output

An HTTP-success response is incomplete or a JSON parser fails; check response completion status and incomplete reason before treating output-budget exhaustion as the cause.

## What the customer sees

An HTTP-success response can still have incomplete output. Illustrative SDK
fields, with the output excerpt abbreviated for readability:

```text
HTTP 200
response.status                     "incomplete"
response.incomplete_details.reason  "max_output_tokens"
response.usage.output_tokens        128
response.output_text                {"status":"READY","items":[{"index":1,"label":"item_1"}, … {"index":12
```

A customer who parses the output without checking completion details may report
only a `JSONDecodeError`.

## What it means

An explicit `incomplete` status with `incomplete_details.reason: max_output_tokens`
supports output-budget exhaustion. On reasoning models, the output allowance
also covers reasoning tokens, so visible output can be shorter than expected.

A parser error by itself does not establish exhaustion. With completed output,
check field extraction, the expected schema, and parser behavior; also inspect
any refusal or response error. A content-filter termination needs its own
investigation. If no response arrived, investigate the SDK or transport failure
first, using the timeout runbook when the exception or symptoms support it.

## What to ask for

Request only information missing from the ticket:

- The response's `status`, `incomplete_details`, any refusal or response error,
  and request ID if received.
- The configured `max_output_tokens`, reasoning setting, model, and SDK version.
- The parser/validation error, expected schema, and a minimal sanitized snippet
  showing which response field is selected and how it is extracted and parsed.
  Include a short failing output excerpt and whether it contains all returned
  text or was cut by logging; the error line alone does not show the parsing path.
- Context: when it started, UTC times for a failing and last successful run,
  input-size or dataset changes, whether every request fails or only some, and
  workflow impact.

If completion details or failing output were not retained, ask the customer to
capture the completion fields above before parsing on the next failing run.
Ask them to share those fields and a short sanitized failing output excerpt,
alongside the extraction/parsing context, when available. Do not ask them to
recover historical output they did not save.

Do not request sensitive records, credentials, full prompts, full request bodies,
or full logs.

## Fix

1. Ask the customer to check completion status, incomplete details, refusal, and
   response errors before parsing or using the result. If those details are
   missing, collect them before choosing a correction; do not treat partial
   output as a completed task.
2. When the reason establishes output-budget exhaustion, have the customer
   increase the bounded allowance to suit the workload or request less output.
   Account for reasoning tokens; there is no universal suitable limit.
3. When completed output fails parsing or validation, investigate the selected
   response field, extraction/parsing steps, and expected schema and content.
   Do not assume a larger output allowance will fix that failure.

## Confirm it's fixed

Ask the customer to confirm completed status without an incomplete reason,
refusal, or response error, then parse and validate the full output against the
expected schema and required content. Confirm the affected application uses the
result successfully; HTTP 200 or parseable JSON alone does not establish that.

## Escalate when

Suggest the application owner for unresolved extraction, parsing, or schema
mismatches, or API support for repeated incomplete output within suitable
workload limits. Include status and reason, output/reasoning settings, model and
SDK version, request ID if received, UTC time, and minimal sanitized schema,
parsing, and output excerpts with any truncation noted.

## Reply template

Keep only questions for missing information, and condition the correction on
the completion details the customer actually supplied. When details or output
were not retained, adapt the requests to capture and share evidence from the
next failing run.

> Thanks for the details. HTTP 200 confirms that a response arrived, but a parser
> error alone does not show whether generation finished or what caused the failure.
>
> Could you share:
>
> 1. the completion status and `incomplete_details`, including any refusal or
>    response error;
> 2. the configured `max_output_tokens`;
> 3. a minimal sanitized failing output excerpt and the parsing/extraction step,
>    including the response field selected and expected JSON structure;
> 4. UTC times for a failing and last successful run, and any input-size changes?
>
> Please say whether the excerpt contains all returned text or was shortened by
> logging. If the response reports `incomplete` because of `max_output_tokens`,
> raise the allowance to fit the workload or request less output, then check
> completion before parsing. These details will help distinguish incomplete
> generation from an extraction or parser issue.

## Notes

- Status: `verified`. Verified on: `2026-10-22` (America/New_York and UTC), with
  `openai` 3.36.0, `gpt-6.1-sol`, and retries disabled. One reproduced
  broken/corrected pair supports the example:
  [incomplete at 128 tokens](../evidence/incomplete_output/broken-2026-10-22.json)
  and [completed at 2,048](../evidence/incomplete_output/fixed-2026-10-22.json).
  The SDK-shaped display maps the selected capture fields to their API names;
  `…` marks omitted excerpt text. Saved excerpts are limited to 1,000 characters,
  so the corrected capture also ends mid-array; its `output_valid: true` was
  computed on the full text before truncation.
- Sources: [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
  [Reasoning](https://developers.openai.com/api/docs/guides/reasoning),
  [Python SDK and Responses interfaces](https://developers.openai.com/api/reference/python).
