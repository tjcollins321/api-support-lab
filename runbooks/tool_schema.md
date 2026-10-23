# Malformed function-tool schema

A request is rejected while validating a function tool's parameter schema; HTTP 400 alone does not distinguish this from other invalid requests.

Use this runbook when supplied validation details identify a function-tool schema. With an unspecified bad-request error, first request the details needed to locate the failing field.

## The error as the customer sees it

Captured on 2026-10-22 with `openai` 3.36.0 and retries disabled.
Selected fields from [the capture](../evidence/tool_schema/broken-20261022T232240Z.json):

```text
HTTP 400 — openai.BadRequestError
error_type:  invalid_request_error
error_code:  invalid_function_parameters
param:       tools[0].parameters
message:     Invalid schema for function 'support_label': 'not_a_json_schema_type' is not valid under any of the given schemas.
request_id:  req_ed8455b8b9d34759b15ecfaed73816f7
```

`param` identifies the tool index and field; the message names the function and
invalid value. The [request implementation](../src/api_support_lab/cases/tool_schema.py)
sets `tool_choice="none"` in both variants, so this rejection occurred even with
tool selection disabled.

## Evidence and confidence

- Status: `verified` — one reviewed live lab pair supports this guidance; it does not diagnose the customer's request.
- Verified on: `2026-10-22` (America/New_York and UTC).
- Observed evidence: [schema rejection](../evidence/tool_schema/broken-20261022T232240Z.json) and [successful correction](../evidence/tool_schema/fixed-20261022T232318Z.json).
- The lab observed HTTP 400, `BadRequestError`, code `invalid_function_parameters`, and parameter `tools[0].parameters`, followed by HTTP 200 with completed output. This is one schema defect, not a universal mapping for every HTTP 400 or schema failure.

## Evidence to request

- A minimal sanitized validation error with available HTTP status, exception type, code/type/parameter, UTC time, and request ID if received.
- The smallest serialized function-tool definition containing the affected property and its enclosing schema, with sensitive descriptions or examples removed.
- The endpoint, model, SDK version, strict-mode setting, and any transformation between the application's schema and the transmitted request.
- The affected workflow and its reported impact. Do not request credentials, full prompts, or full logs.

## Diagnosis and alternative explanations

Validation evidence identifying a tool schema supports investigating that definition. HTTP 400 can also concern input, model settings, or another unsupported feature. A customer's authentication explanation does not override explicit schema diagnostics.

Distinguish a client-side schema error before transmission from an API rejection. Inspect the actual supplied parameter and schema rather than assuming a particular error code or wording. Connection failures, refusals, and incomplete responses are different outcomes.

## Corrective steps

1. Locate the tool and schema property identified by the customer's validation evidence. Compare the serialized request with the application definition to find transformations or configuration differences.
2. Correct invalid JSON Schema types and object/property definitions. For strict function parameters, include every property in `required` and disable additional properties on object definitions.
3. Check the supported schema subset for the endpoint and model in use, including nested objects. Preserve the intended validation constraints; do not disable strictness blindly to suppress the symptom.
4. Have the application maintainer apply the smallest supported correction and arrange a controlled check of the affected request.

## Confirm recovery

Confirm that the customer's corrected tool definition is accepted and the affected workflow completes as intended. If the model requests a function call, acceptance alone does not verify the application's function execution and result handling; check those parts of the customer's workflow too.

If validation still fails, inspect the new parameter/message and the serialized definition. A different validation failure may identify another property; an unrelated API error needs its own investigation. A verified lab example does not establish the customer's exact cause or recovery.

## Escalation checklist

- Escalate when a schema believed to fit the supported subset still fails, or when the request transformation cannot be explained.
- Supply the smallest sanitized schema/error excerpt, endpoint/model/SDK, strict setting, UTC time, and request ID if available.
- Describe the correction attempted and the customer's resulting acceptance/completion behavior; retain unfamiliar codes and uncertainty.
- Route to the application maintainer or appropriate API support channel without claiming a handoff. Omit credentials and full request/log dumps.

## Illustrative draft reply

“The validation error points to the function tool's parameter schema. Check the property named in the error against the serialized definition your application sends, and replace the invalid type with the supported type for the intended value. If strict mode is enabled, also check the enclosing object's `required` list and `additionalProperties` setting. Could you share the smallest sanitized excerpt containing that property and its enclosing schema? Remove sensitive descriptions and examples. After the correction, confirm that the request is accepted and the affected workflow completes, including function execution if a tool is called.”

This is an illustrative draft for human review, not an executed agent result. Use it with supplied validation evidence; otherwise request distinguishing details.

## Sources

- [Official function-calling guide](https://developers.openai.com/api/docs/guides/function-calling)
- [Official structured-output guide and supported schema subset](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI Python SDK error handling](https://developers.openai.com/api/reference/python)

These references describe expected behavior; they are not observed evidence for this lab's case.
