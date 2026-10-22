# Client timeout

A client raises `APITimeoutError` while awaiting a response; an absent HTTP response leaves status, error code, and request ID unavailable.

Use this runbook to distinguish a client timeout from other connection or API failures, investigate the customer's client settings, and check recovery without assuming earlier processing stopped.

## Evidence and confidence

- Status: `verified` — one reviewed live lab pair supports this guidance; it does not diagnose the customer's request.
- Verified on: `2026-10-22` (America/New_York and UTC).
- Observed evidence: [client timeout](../evidence/timeout/broken-20261022T232402Z.json) and [successful correction](../evidence/timeout/fixed-20261022T232415Z.json).
- The lab observed `APITimeoutError` without an HTTP status, request ID, or usage, followed by HTTP 200 with completed output under a suitable client timeout. This does not show whether the earlier request stopped processing or incurred usage.

## Evidence to request

- The exception type, configured client timeout and retries, elapsed time, and UTC attempt time.
- The model, SDK version, output allowance, and a brief description of workload size and network/proxy conditions.
- Whether any HTTP response or request ID arrived. Keep unavailable fields absent or null; a request ID is optional when no response was received.
- Attempts already made, any application-side retry behavior, and reported workflow impact. Request only minimal sanitized metadata, never credentials, full logs, or sensitive payloads.

## Diagnosis and alternative explanations

An SDK `APITimeoutError` supports a client-timeout diagnosis. A vague “timed out” complaint needs exception and timing details first. DNS/TLS failures, general connection problems, upstream HTTP timeout responses, and slow processing can present similar symptoms.

Preserve any actual response fields. An absent HTTP response does not imply HTTP 408 or 504, and a generic connection error does not establish a client timeout. The SDK timeout setting is not a guarantee of the whole workflow's end-to-end duration.

A client timeout means the client stopped waiting; it does not prove provider-side processing stopped. Usage and cost may be unknown. Consider earlier attempts before arranging another request.

## Corrective steps

1. Compare the configured timeout, observed timing, workload, and retry behavior. Check whether a client/proxy deadline or a general connection failure is actually supported by the evidence.
2. If the client limit is impractically short for the workload, choose a suitable bounded timeout or reduce the workload according to the application's operating requirements. Do not assume one timeout value suits every customer.
3. If the evidence instead points to connectivity or an upstream response, route investigation to the relevant application/network component and preserve the actual diagnostics.
4. Review possible earlier processing and repeated work with the application owner before a controlled recovery check. Avoid blind retries; follow the application's established retry and duplicate-work handling.

## Confirm recovery

For a controlled check of the customer's affected workflow, confirm that the client receives a response within its intended operating bounds and that the requested task completes with a usable result. HTTP success alone is insufficient. Inspect available timing and retry information to understand what actually completed.

If the request times out again, preserve the exception, elapsed time, effective settings, and any actual response metadata. Keep uncertainty about earlier server-side processing and unknown usage explicit; do not describe either as resolved without evidence.

## Escalation checklist

- Escalate persistent timeouts after supported client-setting checks, unexplained timing, or unresolved concern about repeated processing.
- Include minimal sanitized exception/timing details, effective timeout/retries, workload description, model/SDK, and UTC times.
- Include HTTP fields and request ID only if received; state when no response arrived.
- Describe the change and recovery-check outcome, retaining uncertainty about processing/cost. Suggest the application/network maintainer or appropriate API support channel without claiming a handoff.

## Illustrative draft reply

“The supplied client-timeout exception means the client stopped waiting; it does not show whether server-side processing stopped. Could you share the configured timeout and retries, elapsed time, SDK version, and whether any response metadata arrived? A request ID is useful only if available. Review earlier attempts before retrying.”

This is an illustrative draft for human review, not an executed agent result. Ask for the exception type when the complaint is ambiguous.

## Sources

- [OpenAI Python SDK timeouts, retries, and error handling](https://developers.openai.com/api/reference/python)
- [Official API error guidance](https://developers.openai.com/api/docs/guides/error-codes)

These references describe expected behavior; they are not observed evidence for this lab's case.
