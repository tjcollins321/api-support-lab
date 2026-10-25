# Invalid credentials

A request is rejected during authentication, potentially reported as HTTP 401 or an SDK `AuthenticationError`; the exact diagnostic fields must be checked before choosing a cause.

## What the customer sees

Illustrative SDK-shaped example, formatted for readability:

```text
openai.AuthenticationError: Error code: 401 - {
  'error': {
    'message': 'Incorrect API key provided: [REDACTED]************************-lab. You can find your API key at https://platform.openai.com/account/api-keys.',
    'type': 'invalid_request_error',
    'param': None,
    'code': 'invalid_api_key'
  }
}
```

For an SDK status error, `e.status_code`, `e.code`, and `e.type` expose the
available diagnostics; `e.request_id` is available when returned by the service.

## What it means

The request's credential was rejected. The rejection supports checking loading
and validity, but does not establish that the key was revoked. Investigate in
this order:

- A missing or stale deployment secret reference, unintended whitespace, or a
  difference between the developer's shell and the process making the request.
- A deleted or rotated key that the running process still references.
- The intended project and credential configuration, checked through project
  settings or secret-management records rather than a masked key fragment.

A partial complaint such as "our key stopped working" needs diagnostic details
first. Preserve unfamiliar codes and distinguish permission, model-access,
billing, and connection errors from the supplied authentication rejection.

## What to ask for

Request only information missing from the ticket:

- A minimal sanitized error excerpt: HTTP status, exception type, error code,
  type, message, and request ID if received.
- How the running process loads the key, its execution environment, and the
  intended project. Ask for configuration descriptions, never secret values.
- The model and SDK version used by the failing process.
- Context: when it started, recent deploys or key rotations, whether every
  request fails or only some, a failing attempt's UTC time, and workflow impact.

Do not request keys, credential-bearing headers, full logs, or environment dumps.

## Fix

1. Ask the customer to check the credential source in the process making the
   request. If the application reads `OPENAI_API_KEY`, verify it there rather
   than only in a shell; check secret references and whitespace locally.
2. Have the project's credential owner verify that the configured key still
   exists in the intended project. A masked prefix or suffix does not prove
   project ownership or validity.
3. Ask the customer to correct the identified loading or configuration problem
   through their secret-management process. Do not prescribe rotation solely
   because of a 401; involve the credential owner if validity remains uncertain.

## Confirm it's fixed

Ask the customer to rerun the affected request from the corrected environment
and confirm successful authentication and usable output. For Responses, check
completed status and handle incomplete output or refusal before calling the
workflow recovered. If another error appears, inspect its actual diagnostics;
a changed error alone does not establish recovery.

## Escalate when

Involve the project or credential owner when loading or validity cannot be
confirmed. Suggest the appropriate API support channel if rejection persists
after those checks. Include sanitized diagnostics, request ID if received, UTC
time, model and SDK version, environment, checks made, and the rerun's outcome.

## Reply template

Use this after a supplied 401 with `invalid_api_key`; for an unconfirmed key
complaint, request the error details first. Keep only questions for missing
information.

> Thanks for sending the error details. The 401 with `invalid_api_key` means the
> API rejected the key this request sent; it does not tell us whether it was revoked.
>
> Could you check locally, without printing or sharing the key:
>
> 1. that the process making the request loads the intended credential, including
>    deployment secret references and unintended whitespace;
> 2. that the key still exists in the intended project's settings;
> 3. when this started and whether it followed a deploy or key rotation?
>
> After correcting any loading issue, rerun the request and confirm you receive
> usable output. If it still fails, send a sanitized error excerpt, the request
> ID if received, and the attempt's UTC time so we can narrow down the next step.

## Notes

- Status: `verified`. Verified on: `2026-10-21` (America/New_York; captures are
  dated `2026-10-22` UTC), with `openai` 3.36.0 and retries disabled. One
  reproduced broken/corrected pair supports the example:
  [authentication rejection](../evidence/invalid_credentials/broken-20261022T032250Z.json)
  and [completed correction](../evidence/invalid_credentials/fixed-20261022T032341Z.json).
  The SDK-shaped layout is reconstructed from selected recorded diagnostics;
  the credential text retains the capture's `[REDACTED]` marker. Rejected-request
  usage was not reported.
- Sources: [Python SDK error handling](https://developers.openai.com/api/reference/python),
  [API error guidance](https://developers.openai.com/api/docs/guides/error-codes),
  [Authentication](https://developers.openai.com/api/reference/overview).
