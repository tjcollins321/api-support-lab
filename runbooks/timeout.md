# Client timeout

A client raises `APITimeoutError` while awaiting a response; an absent HTTP response leaves status, error code, and request ID unavailable.

## What the customer sees

Illustrative SDK exception:

```text
openai.APITimeoutError: Request timed out.
```

Record the exception, observed elapsed time, and effective timeout and retry
settings. Retain any actual response metadata; do not invent a status or request
ID when no response arrived.

## What it means

The client reached a timeout while making the request. That does not establish
whether server-side processing stopped or whether the request incurred usage;
a later attempt can duplicate work. The SDK timeout is not a whole-workflow
wall-clock deadline.

SDK and application retries can add attempts and lengthen the wait. Inspect
effective settings rather than assuming defaults. Investigate other connection
exceptions using the actual DNS, TLS, proxy, or network diagnostics; an
`APIConnectionError` does not prove that the server never received the request.
An HTTP 408 or 504 is a received response and should be investigated using its
actual status and any available metadata.

## What to ask for

Request only information missing from the ticket:

- The exception type and message, observed elapsed time, and effective client
  timeout and retry settings.
- The model, SDK version, output allowance, approximate workload size, and
  relevant proxy, VPN, or network-path details.
- Earlier attempts, application-side retries, and duplicate-work handling. Ask
  whether a response arrived only if the ticket does not already say; when none
  arrived, do not request unavailable HTTP status, error code/type, request ID,
  or response completion fields. Keep unavailable fields absent or null.
- Context: when it started, request-size changes, whether every request times
  out or only some, a failing attempt's UTC time, and workflow impact.

Do not request credentials, full logs, or request payloads.

## Fix

1. Compare the supplied exception, timing, and settings. If the evidence instead
   shows a different connection failure or an HTTP response, route investigation
   to that network path or status rather than assuming this client-timeout cause.
2. Review earlier attempts and duplicate-work handling with the application
   owner before another attempt. Coordinate SDK and application retry behavior;
   do not enable retries unconditionally or stack repeated attempts blindly.
3. If the client limit is too short for the workload, ask the customer to choose
   a suitable bounded timeout or reduce the workload. Rerun only after the
   earlier-processing and duplicate-work review; keep retry settings consistent
   with the application's handling of repeated requests.

## Confirm it's fixed

Ask the customer to confirm that a response arrives within the intended
operating bounds and that the task completes with usable output. If it times
out again, retain the new exception, elapsed time, settings, and any actual
response metadata; server-side processing and usage for earlier attempts remain
unknown.

## Escalate when

Suggest the application or network owner for unexplained timing, retry behavior,
or duplicate-work concerns, and API support for persistent unexplained timeouts
after those checks. Include effective settings, observed timing, workload,
model and SDK version, UTC times, and whether any response metadata arrived.
Keep unknown processing and usage explicit.

## Reply template

Use only timings and settings the customer supplied. Keep only questions for
missing information.

> Thanks for sending the timeout details. `APITimeoutError` means your client
> stopped waiting; it does not tell us whether the earlier request finished on
> the server, so repeating it could duplicate work.
>
> Before retrying, check earlier attempts and how your application handles
> duplicate work. If the configured timeout is too short for the workload, use
> a suitable bounded timeout or reduce the workload, with retry settings that
> match that duplicate-work handling.
>
> Could you share:
>
> 1. your effective timeout and retry settings, SDK version, and workload size;
> 2. when this started, whether request size changed, whether every request times
>    out or only some, and a failing attempt's UTC time;
> 3. earlier attempts or application-side retries and the workflow impact?
>
> With those details and the outcome of a safe rerun, we can narrow down whether
> the client settings or another part of the request path needs attention.

## Notes

- Status: `verified`. Verified on: `2026-10-22` (America/New_York and UTC), with
  `openai` 3.36.0 and retries disabled. One reproduced broken/corrected pair
  supports the example:
  [client timeout at 0.5 seconds](../evidence/timeout/broken-2026-10-22.json)
  and [completed correction at 60 seconds](../evidence/timeout/fixed-2026-10-22.json).
  Recorded elapsed times were about 620 ms and 1.81 seconds. The timeout capture
  has no HTTP status, request ID, or usage; its earlier server-side processing
  and cost remain unknown.
- Sources: [Python SDK timeouts, retries, and error handling](https://developers.openai.com/api/reference/python),
  [API error guidance](https://developers.openai.com/api/docs/guides/error-codes).
