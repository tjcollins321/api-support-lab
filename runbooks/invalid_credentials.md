# Invalid credentials

A request is rejected during authentication, potentially reported as HTTP 401 or an SDK `AuthenticationError`; the exact diagnostic fields must be checked before choosing a cause.

Use this runbook to investigate a customer's authentication symptoms, identify a supported correction, and confirm recovery of the affected workflow.

## The error as the customer sees it

Captured on 2026-10-21 in America/New_York (2026-10-22 UTC), with
`openai` 3.36.0 and retries disabled. These are selected normalized fields from
[the sanitized capture](../evidence/invalid_credentials/broken-20261022T032250Z.json):

```text
HTTP 401 — openai.AuthenticationError
error_type:  invalid_request_error
error_code:  invalid_api_key
message:     Incorrect API key provided: [REDACTED]************************-lab. You can find your API key at https://platform.openai.com/account/api-keys.
request_id:  req_c610e4e44403409bbe5eecc22366c2d8
```

The capture's `[REDACTED]` marker replaced a recognizable key prefix in the
server-masked message. This is the saved sanitized text, not a reconstruction of
the original credential fragment. Do not paste a key into a support reply.

## Evidence and confidence

- Status: `verified` — one reviewed live lab pair supports this guidance; it does not diagnose the customer's request.
- Verified on: `2026-10-21` (America/New_York; captures are dated `2026-10-22` UTC).
- Observed evidence: [authentication rejection](../evidence/invalid_credentials/broken-20261022T032250Z.json) and [successful correction](../evidence/invalid_credentials/fixed-20261022T032341Z.json).
- The lab observed HTTP 401, `AuthenticationError`, and `invalid_api_key`, followed by HTTP 200 with completed output. This does not establish key revocation or guarantee every authentication failure has these fields.

## Evidence to request

- A minimal sanitized error excerpt with available HTTP status, SDK exception type, error code/type/parameter, UTC attempt time, and request ID if received.
- The model, SDK version, and execution environment in which the failure occurs.
- How the application loads its credential and which project it is intended to use. Request configuration descriptions, never the credential or an environment dump.
- Whether the workflow is blocked, degraded with a workaround, or nonblocking; impact determines severity independently of the error.

- When the failure started and whether anything changed around then (a deploy, a key rotation, a new environment); whether every request fails or only some; a timestamp from a failing attempt.

## Diagnosis and alternative explanations

An explicit authentication rejection supports investigating credential loading and validity. HTTP status alone or a customer's assertion that a key was revoked does not identify the exact cause. A partial complaint such as “my key stopped working” needs distinguishing status/code/type evidence before a case-specific correction.

A missing, malformed, outdated, or incorrectly loaded credential can be consistent with these symptoms. Check the application process and deployment actually making the request. Permission, model-access, billing, and connection failures may require different investigations; preserve their actual diagnostics and unfamiliar codes.

## Corrective steps

1. Confirm that the affected application loads the intended API credential through its configured credential mechanism. Check the running process or deployment, rather than assuming its configuration matches a developer's shell.
2. Confirm that `OPENAI_API_KEY` is set in the process making the request, if that is the application's credential source. Check deployment secret references and unintended whitespace locally, without printing the value. Use the intended project's API-key settings or secret-management records to check whether the configured key still exists and belongs to that project; a key prefix alone does not prove project identity or validity.
3. Correct the identified loading or configuration problem using the application's established secret-management process. If credential validity remains uncertain, involve the project's credential owner through that process; do not claim revocation from the rejection alone.
4. After the change, have the customer rerun the failing request and confirm it completes with usable output, not just a 200.

## Confirm recovery

Check the customer's affected request in the corrected execution environment. Confirm that authentication succeeds and the requested task completes with the expected usable result; HTTP success alone is insufficient. For Responses, inspect completion status and handle incomplete output or refusal separately.

If the request still fails, retain the new sanitized diagnostics and compare them with the original failure. A different error can mean authentication progressed while another issue remains. Describe recovery only to the extent actually observed.

## Escalation checklist

- Escalate persistent authentication rejection after loading/configuration checks to the project owner or appropriate API support channel.
- Include minimal sanitized diagnostics, available request ID, UTC time, model/SDK, and affected environment.
- Describe the loading checks, configuration change, and result of the customer's recovery check; identify uncertainties and unrelated errors.
- Omit credentials, credential-bearing headers, full logs, and environment dumps. Name the team the ticket should go to.

## Illustrative draft reply

Thanks for sending the error details. The 401 with `invalid_api_key` means the API rejected the key this request actually sent — on its own it doesn't mean the key was revoked. Check whether the running process is loading a different key than you expect: an old value in the deployment's environment, a key from another project, or unintended whitespace.

Could you check, in the environment where it fails and without pasting the key:

1. that `OPENAI_API_KEY` is set in the process making the request, not just in your shell;
2. that the key still exists in the intended project's settings, without printing or sharing its value;
3. when this started and whether anything changed around then, such as a deploy or a key rotation.

If it still fails after that, send the `error_code`, `error_type`, `request_id` if received, and a timestamp, and we'll take it from there.

This is an illustrative draft for human review, not an executed agent result. Use it with supplied authentication evidence; otherwise ask for distinguishing details first.

## Sources

- [OpenAI Python SDK error handling](https://developers.openai.com/api/reference/python)
- [API error guidance](https://developers.openai.com/api/docs/guides/error-codes)
- [Authentication and credential handling](https://developers.openai.com/api/reference/overview)

Documentation supports the troubleshooting approach; the linked observations establish only what this lab verified.
