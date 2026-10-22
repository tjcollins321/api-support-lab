# Invalid credentials

A request is rejected during authentication, potentially reported as HTTP 401 or an SDK `AuthenticationError`; the exact diagnostic fields must be checked before choosing a cause.

## Reproduction status and evidence

- Status: `verified` — one broken/corrected pair was observed against the real OpenAI Responses API and its sanitized artifacts were reviewed.
- Verified on: `2026-10-21` (America/New_York; the captures are dated `2026-10-22` in UTC).
- Observed evidence: [broken request](../evidence/invalid_credentials/broken-20261022T032250Z.json) and [corrected request](../evidence/invalid_credentials/fixed-20261022T032341Z.json).
- Offline coverage: authored responses and SDK errors in `tests/test_capture.py` and `tests/test_authentication.py`. These are synthetic fixtures, not observations of API behavior.

Both command variants are implemented. The broken variant uses an obviously invalid credential without loading `OPENAI_API_KEY`. The fixed variant loads the environment credential. Both send the same small synthetic Responses workload with low reasoning, a 2,048-token output cap, a 60-second timeout, zero retries, and `store=False` by default. A timeout or unrelated failure does not verify authentication behavior.

## Observed behavior and verification boundaries

Exactly one request was made per variant, with zero retries. Both commands exited 0 and the artifacts were inspected before selecting the linked public copies. The real credential was loaded for local preflight, the corrected request, and exact-match artifact review; it was not displayed or used by the broken request. Authorization, cookies, full prompts, client objects, and environment dumps are absent from the artifacts. The remaining masked fragment in the broken error message belongs to the deliberately invalid credential, not the real key.

| Variant | UTC time | Observation | Available usage |
| --- | --- | --- | --- |
| Broken | `2026-10-22T03:22:50.374958+00:00` | HTTP 401, `AuthenticationError`, `invalid_request_error`, code `invalid_api_key`, null parameter, diagnostic request ID received | Unavailable; recorded as null |
| Corrected | `2026-10-22T03:23:41.220586+00:00` | HTTP 200, response status `completed`, output `READY`, diagnostic request ID received | 13 input tokens, 5 output tokens, 18 total; zero cached input and reasoning output tokens reported |

Both used the requested model alias `gpt-6.1-sol`, SDK 3.36.0, low reasoning, a 2,048-token cap, a 60-second timeout, zero retries, and `store=False`. Recorded elapsed times were approximately 395 ms and 2,962 ms. This establishes access for this configured credential/model at this observation time; it is not a reliability benchmark or a guarantee of future access.

The documented expectation for an invalid credential is an authentication rejection. This project's broken-attempt check requires HTTP 401 and `AuthenticationError`; it does not require a particular error code or exact message. `invalid_api_key` is now an observation of this attempt, not a universal mapping for every authentication failure.

The fixed-attempt check requires an HTTP success response, completed response status, and nonempty text output. HTTP 200 alone is insufficient. Incomplete output, refusal, permission failures, and unavailable models must remain visible as unsuccessful corrections.

A successful single-attempt check does not automatically verify a pair or update this runbook. This pair's status was updated only after both observations and sanitization were reviewed. Other cases remain unverified; the project has 1 of 4 target cases verified.

At the published standard token rates of $2 per million input tokens and $10 per million output tokens, the corrected request's reported usage estimates to **$0.000076**. This is a token-based estimate, not an inspected billing charge; the effective service tier is not captured in this evidence schema. Broken-request usage is unavailable and is not treated as zero. The billing dashboard and remaining credit balance were not inspected; review account spending before further live work.

## Diagnosis and alternative explanations

Authentication rejection can be consistent with a missing, malformed, outdated, or incorrectly loaded credential. Check which environment and project the application actually uses. A customer assertion that a key was revoked is not evidence of revocation, and this lab's intentionally invalid key cannot establish that a real key was revoked.

Project permissions, model availability, billing issues, and connection failures may prevent a corrected request from succeeding for different reasons. Preserve their actual diagnostics instead of counting them as an authentication reproduction. Unknown error codes remain unknown until supported by evidence.

## Fix and verification procedure

Confirm that the intended project key is present in the process environment, without printing it. The application does not automatically read `.env`; when using that file, explicitly pass `uv run --env-file .env`. The broken variant does not need a genuine credential.

These command forms were used for the observed live pair, with the workspace-local `.tools/uv`, a local uv cache, and package downloads disabled. Future reruns require their own explicit live opt-in and spending review:

```sh
uv run --locked python -m api_support_lab reproduce invalid_credentials --variant broken --live
uv run --locked --env-file .env python -m api_support_lab reproduce invalid_credentials --variant fixed --live
```

Run each variant once. If an attempt exits nonzero, inspect its evidence and stop before another request. Exit code 0 means that attempt matched its intended behavior, including the deliberate rejection for `broken`; it does not mean every request succeeded.

Artifacts are written separately under the checkout's ignored `artifacts/evidence/`, with a UTC timestamp and unique suffix. An explicit `--output-dir PATH` overrides the directory; relative overrides use the caller's working directory. Filesystem failure is reported without automatically repeating the request, which may already have incurred usage.

For future verification, inspect both artifacts for credentials, unintended data, correct settings, the actual rejection, and successful completion of the correction. Unavailable fields remain null. Check account spending; unavailable usage means unknown cost. Select sanitized observations for the public `evidence/` directory only after review, then link them here and update the verification date/status and case count. An unsuccessful future pair must retain its limitation rather than silently replacing these observations.

## Escalation checklist

- Include a minimal sanitized error message, available status/code/type/parameter, UTC attempt time, configured model, and relevant client settings.
- Include the request ID only if one was received; a timeout may have none.
- Describe the environment/key-loading checks already performed, without sharing any credential or full environment dump.
- State whether the broken and corrected attempts behaved as intended, and preserve unrelated failures.
- If the environment credential still fails after local configuration checks, suggest investigation by the project's owner or the appropriate support channel. This lab does not perform an account change or an engineering handoff.

## Illustrative draft reply

“The supplied authentication error indicates that the request's credential was rejected; it does not establish that a key was revoked. Please confirm that the application loads the intended project's API credential into its execution environment without printing or sharing it. If the error continues, could you provide the error code/type and request ID if available from a minimal sanitized excerpt?”

This draft is illustrative, not an executed agent result. Use it only when the ticket supplies authentication evidence; otherwise ask for distinguishing details first.

## Sources

- [OpenAI Python SDK: error handling, raw responses, retries, and timeouts](https://developers.openai.com/api/reference/python)
- [API error guidance](https://developers.openai.com/api/docs/guides/error-codes)
- [Authentication and credential handling](https://developers.openai.com/api/reference/overview)
- [GPT-6.1 Sol standard token pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol)

These sources explain expected behavior and pricing. The linked live artifacts establish what was observed in this lab.
