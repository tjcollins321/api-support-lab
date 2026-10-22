# Malformed function-tool schema

A request is rejected while validating a function tool's parameter schema; HTTP 400 alone does not distinguish this from other invalid requests.

Use this runbook when supplied validation details identify a function-tool schema. With an unspecified bad-request error, first request the details needed to locate the failing field.

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

“The supplied validation details point to the function-tool schema. Please inspect the affected property in the serialized request, including its JSON Schema type and strict object requirements. After correcting it, check that the affected workflow completes. If the error continues, could you share a minimal sanitized schema excerpt, the error parameter/code, and a request ID if received?”

This is an illustrative draft for human review, not an executed agent result. Use it with supplied validation evidence; otherwise request distinguishing details.

## Sources

- [Official function-calling guide](https://developers.openai.com/api/docs/guides/function-calling)
- [Official structured-output guide and supported schema subset](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI Python SDK error handling](https://developers.openai.com/api/reference/python)

These references describe expected behavior; they are not observed evidence for this lab's case.
