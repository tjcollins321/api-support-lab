# Malformed function-tool schema

A request is rejected while validating a function tool's parameter schema; HTTP 400 alone does not distinguish this from other invalid requests.

## What the customer sees

Illustrative SDK-shaped example, formatted for readability:

```text
openai.BadRequestError: Error code: 400 - {
  'error': {
    'message': "Invalid schema for function 'support_label': 'not_a_json_schema_type' is not valid under any of the given schemas.",
    'type': 'invalid_request_error',
    'param': 'tools[0].parameters',
    'code': 'invalid_function_parameters'
  }
}
```

`param` locates the tool and schema field. This message names the function and
invalid value; the serialized definition is needed to locate the affected
property precisely.

## What it means

The supplied validation details identify a function-tool parameter schema that
is invalid or outside the API's supported subset. Investigate that evidence
before acting on a customer's authentication or quota hypothesis; HTTP 400 alone
does not identify a tool-schema problem.

Check for an invalid `type`, strict-mode object requirements, unsupported nested
definitions, and transformations between source definitions and the serialized
request. Distinguish a local validation exception from an API rejection using
the actual exception and available response diagnostics. Preserve unfamiliar
codes and parameters rather than forcing them into this example.

## What to ask for

Request only information missing from the ticket:

- A minimal sanitized validation error: HTTP status, exception type, code, type,
  parameter, message, and request ID if received.
- The smallest serialized tool-definition excerpt containing the affected
  property and its enclosing schema, with sensitive descriptions and examples
  removed. Request it even when the error already names the invalid value.
- The endpoint, model, SDK version, strict-mode setting, and any transformations
  between the application's definition and the transmitted request.
- Context: whether the schema ever worked, what changed, whether all requests
  using it fail or only some, a failing attempt's UTC time, and workflow impact.
  For intermittent failures, compare minimal failing and passing schema excerpts.

Do not request credentials, full request bodies, full prompts, or full logs.

## Fix

1. Use the supplied `param` and message to locate the invalid value in the
   serialized definition. Ask the customer to compare it with the application
   definition if a transformation or serialization step is involved.
2. Have the customer replace an invalid JSON Schema type with the supported type
   for the intended value, preserving the intended constraint.
3. If strict mode is enabled, check that every property appears in `required`
   and every object, including nested ones, has `additionalProperties: false`.
   Do not recommend disabling strictness just to suppress the error.
4. Check the supported schema subset for the endpoint and model, then ask the
   customer to apply the smallest supported correction and rerun the request.

## Confirm it's fixed

Confirm the corrected definition is accepted and the affected workflow completes
with the expected result. If a function call occurs, ask the customer to verify
function execution and result handling too. If validation still fails, inspect
the new diagnostics and serialized definition before choosing another change.

## Escalate when

Suggest the application owner when a transformation or transmitted definition
cannot be explained, or API support when a schema believed to fit the supported
subset still fails. Include the minimal sanitized schema and error, endpoint,
model and SDK version, strict setting, request ID if received, UTC time, and the
attempted correction and outcome.

## Reply template

Adapt the named field and invalid value to the supplied error. Keep only
questions for missing information.

> Thanks for sending the validation error. It points to your function tool's
> parameter schema; the next step is to check the serialized definition around
> the field and invalid value named in the error.
>
> Could you:
>
> 1. send the smallest sanitized excerpt containing the affected property and
>    its enclosing schema, even if the error already names the invalid value;
> 2. confirm the endpoint, model, SDK version, and whether strict mode is enabled;
> 3. say whether this schema worked before and what changed?
>
> If the error identifies an invalid type, replace it with the supported type
> you intend. If strict mode is enabled, check `required` and
> `additionalProperties: false` on each object too. Rerun after the correction
> and share the outcome so we can confirm acceptance and completion of the
> affected workflow.

## Notes

- Status: `verified`. Verified on: `2026-10-22` (America/New_York and UTC), with
  `openai` 3.36.0 and retries disabled. One reproduced broken/corrected pair
  supports the example:
  [schema rejection](../evidence/tool_schema/broken-20261022T232240Z.json)
  and [completed correction](../evidence/tool_schema/fixed-20261022T232318Z.json).
  The SDK-shaped layout is reconstructed from selected recorded diagnostics;
  rejected-request usage was not reported. The
  [case implementation](../src/api_support_lab/cases/tool_schema.py) sets
  `tool_choice="none"` in both variants; the broken schema was still rejected.
- Sources: [Function calling](https://developers.openai.com/api/docs/guides/function-calling),
  [Structured outputs and supported subset](https://developers.openai.com/api/docs/guides/structured-outputs),
  [Python SDK error handling](https://developers.openai.com/api/reference/python).
