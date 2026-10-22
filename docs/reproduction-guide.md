# Reproduction guide for lab maintainers

Use this guide to operate API Support Lab's synthetic experiments, inspect captures, and establish the evidence supporting its runbooks. It is maintainer documentation. The [support runbooks](../runbooks/) help support staff and the triage agent investigate a customer's symptoms and confirm that customer's recovery. Customers do not need to run these experiments to troubleshoot their applications.

The runbook registry exposes only the four support documents. This guide is not registered or retrieved by the agent's tools, and the agent cannot execute reproductions. A customer ticket never grants authorization to run an experiment. Runbook recovery checks concern the customer's affected workflow; lab verification requires reviewed broken/corrected observations.

## Current verification status

| Case | Lab status | Verified on | Evidence |
| --- | --- | --- | --- |
| `invalid_credentials` | `verified` | `2026-10-21` America/New_York | [Rejection](../evidence/invalid_credentials/broken-20261022T032250Z.json), [correction](../evidence/invalid_credentials/fixed-20261022T032341Z.json) |
| `tool_schema` | `verified` | `2026-10-22` America/New_York | [Rejection](../evidence/tool_schema/broken-20261022T232240Z.json), [correction](../evidence/tool_schema/fixed-20261022T232318Z.json) |
| `incomplete_output` | `verified` | `2026-10-22` America/New_York | [Incomplete](../evidence/incomplete_output/broken-20261022T232333Z.json), [correction](../evidence/incomplete_output/fixed-20261022T232346Z.json) |
| `timeout` | `verified` | `2026-10-22` America/New_York | [Timeout](../evidence/timeout/broken-20261022T232402Z.json), [correction](../evidence/timeout/fixed-20261022T232415Z.json) |

Verified live reproduction cases are **4 of 4**. The authentication captures are dated `2026-10-22` UTC; the other pairs were observed on `2026-10-22` in both time zones. Each case has one reviewed pair, not a reliability benchmark. Offline fixtures remain distinct from these observations. A customer's successful recovery does not automatically verify a new lab experiment.

## Execution boundaries and preparation

- Use Python 3.14 and `uv` installed on PATH with the locked dependencies; follow the [README setup](../README.md#setup-and-current-usage).
- Live requests require separate authorization and explicit `--live` opt-in. Check configured-model access and review account spending before a live milestone. The initial $15 experiment allowance is a planning limit, not an enforced billing ceiling.
- Settings default to `gpt-6.1-sol`, low reasoning, 2,048 output tokens, a 60-second client timeout, zero retries, and `store=False`. The two broken-limit exceptions are listed below.
- Only broken authentication uses the deliberately invalid credential without loading `OPENAI_API_KEY`. Its fixed variant and both variants of the other cases require a process-provided `OPENAI_API_KEY`, loaded only after live opt-in. Never print or share it.
- The application does not automatically load `.env`. If a future authorization permits that source, an operator can explicitly use `uv run --locked --env-file .env ...`. Command examples below use `--no-env-file`; they assume any required credential is already supplied through the authorized process environment.
- Run one variant at a time and inspect its outcome before proceeding. Do not automatically run the correction, repeat a failed call, or search for a trigger in a loop. Timebox investigation of a difficult trigger to 30 minutes and retain an honest limitation if it remains unverified.

This guide's initial creation and support-document refactor made no API calls or real-credential/`.env` reads. A later authorized checkpoint loaded the project-root `.env` without displaying credentials and ran the six new-case commands once each, with review between attempts. The observed pairs are documented below. Future reruns require their own authorization; these command forms do not grant it. Documentation references and fixtures do not substitute for observations.

## Experiments and commands

Every invocation makes one bounded request through the shared capture wrapper, with no automatic retries. Both variants use the same workload except for the intended defect or limit. These commands are for future authorized work, not steps to ask a customer to perform.

### Invalid credentials

Both variants request the single word `READY`. Broken authentication uses an obviously invalid credential against the normal API endpoint; the fixed variant uses the authorized environment credential. The request body and default limits are identical. This experiment cannot establish that a real key was revoked.

```sh
uv run --locked --no-env-file python -m api_support_lab reproduce invalid_credentials --variant broken --live
uv run --locked --no-env-file python -m api_support_lab reproduce invalid_credentials --variant fixed --live
```

### Malformed function-tool schema

Both variants request `READY` and register a strict `support_label` function with a required `label` property. The broken property type is deliberately invalid: `not_a_json_schema_type`. The correction uses `string`. The root is an object with `additionalProperties: false`; the required property list is unchanged. Both requests set `tool_choice="none"`, so no local tool execution is needed.

```sh
uv run --locked --no-env-file python -m api_support_lab reproduce tool_schema --variant broken --live
uv run --locked --no-env-file python -m api_support_lab reproduce tool_schema --variant fixed --live
```

The live broken request returned HTTP 400, `BadRequestError`, `invalid_request_error`, code `invalid_function_parameters`, and parameter `tools[0].parameters`; the API validated the schema even with tool selection disabled. The correction completed with `READY`. The predicate below remains conservative and does not require an exact code/message; the registry's exact mapping comes from the reviewed capture, not a fixture. Other schema defects can have different diagnostics.

### Incomplete structured output

Both variants request strict JSON with `status: READY` and exactly 32 ordered items. Each item has an integer index from 1 through 32 and its matching `item_N` label. The schema and prompt are identical. The broken variant starts at 128 output tokens; the correction starts at 2,048. Both otherwise use the normal 60-second timeout and low reasoning.

```sh
uv run --locked --no-env-file python -m api_support_lab reproduce incomplete_output --variant broken --live
uv run --locked --no-env-file python -m api_support_lab reproduce incomplete_output --variant fixed --live
```

`--max-output-tokens N` overrides the effective output cap for either variant. This live workload accepted 128 tokens and returned explicit `max_output_tokens` exhaustion with partial JSON; 2,048 completed and validated all 32 items. This does not establish a universal minimum or suitable budget for other workloads. For future investigations, respect actual minimums and adjust only within the timebox and allowance. Exhaustion before visible JSON also qualifies because reasoning can consume the budget. Parser failure, a minimum-budget rejection, and content-filter termination do not establish budget exhaustion.

Corrected output must validate against the strict Pydantic schema and contain the expected 32 items in order. The capture wrapper checks full output before redaction/excerpt truncation and saves only the boolean `output_valid`. Incomplete, refused, and failed responses skip this validation; `output_valid` stays null. A completed invalid or wrong-content result is retained and fails the correction. A saved excerpt may be too short to contain complete JSON even when the full-output check passed.

### Client timeout

Both variants request `READY` with the same request body and 2,048-token cap. The broken client starts with a 0.5-second timeout; the corrected client starts at 60 seconds. Only the client timeout changes.

```sh
uv run --locked --no-env-file python -m api_support_lab reproduce timeout --variant broken --live
uv run --locked --no-env-file python -m api_support_lab reproduce timeout --variant fixed --live
```

`--timeout-seconds N` overrides the effective client timeout for either variant. A short request that completes is saved but does not reproduce the intended timeout. An SDK timeout does not establish that provider-side processing stopped; repeating the request may cause additional work or charges. Missing usage means unknown cost. The SDK timeout is not a whole-operation wall-clock guarantee. Offline transport exceptions do not measure real latency or prove enforcement of a real deadline.

The live 0.5-second client raised `APITimeoutError` after approximately 620 ms with no transport fields or usage. The 60-second correction completed with `READY` after approximately 1.81 seconds. The earlier request's server-side processing and cost remain unknown.

Both limit flags are available on all reproduction commands, are validated before client construction, and are recorded as effective settings. The starting limits above are lab experiment choices, not universal customer recommendations.

## Per-attempt checks and exit codes

| Case | Broken attempt passes when | Corrected attempt passes when |
| --- | --- | --- |
| `invalid_credentials` | Outcome `api_error`, HTTP 401, SDK `AuthenticationError`; no exact message or code required | HTTP success, outcome `response`, completed status, nonempty text |
| `tool_schema` | Outcome `api_error`, HTTP 400, SDK `BadRequestError`, and error parameter equal to `tools` or starting with `tools[` or `tools.` | HTTP success, completed text response, no incomplete reason or response error |
| `incomplete_output` | HTTP success, outcome `response`, status `incomplete`, reason `max_output_tokens`, no response error | HTTP success, completed text response, no incomplete reason or response error, and full schema/content check `output_valid: true` |
| `timeout` | Outcome `client_timeout` and SDK `APITimeoutError` | HTTP success, completed text response, no incomplete reason or response error |

For the new cases, a response error means a captured non-null response `error_code`. Refusal is a distinct outcome. An unrelated rejection, permission/model-access failure, generic connection failure, HTTP timeout response, empty completion, refusal, or unsuccessful correction must remain visible and cannot count as the intended pair. A client-side programming error propagates rather than being relabeled as a reproduced API failure.

Exit 0 means that one attempt matched its predicate, including a deliberate failure for a broken variant. Other captured outcomes return 1. Argument/configuration errors, missing credentials where required, and missing live opt-in return 2. Filesystem errors return 1 without repeating a possibly processed request. Neither exit 0 nor HTTP success alone verifies a pair or updates a runbook.

## Reviewed slice 4 observations

Six explicitly authorized requests ran sequentially from 19:22–19:24 America/New_York on 2026-10-22 (23:22–23:24 UTC): one broken and one fixed attempt for each new case. All six commands exited 0. No rerun, automatic retry, trigger adjustment, extra authentication/model-access request, or live agent evaluation occurred. The corrected schema request confirmed configured-model access as part of the pair, rather than using a separate smoke request.

| Case/variant | UTC time | Observed result | Reported input/output/total tokens |
| --- | --- | --- | --- |
| Schema / broken | `23:22:40.318052` | HTTP 400, `BadRequestError`, `invalid_function_parameters`, `tools[0].parameters` | Unknown |
| Schema / fixed | `23:23:18.195182` | HTTP 200, completed, `READY` | 42 / 5 / 47 |
| Incomplete / broken | `23:23:33.193696` | HTTP 200, `incomplete`, `max_output_tokens`, partial JSON | 138 / 128 / 266 |
| Incomplete / fixed | `23:23:46.160497` | HTTP 200, completed, full-output schema/content validation passed | 138 / 337 / 475 |
| Timeout / broken | `23:24:02.582143` | `APITimeoutError`; null HTTP status, request ID, server fields, and usage | Unknown |
| Timeout / fixed | `23:24:15.273520` | HTTP 200, completed, `READY` | 13 / 5 / 18 |

All requested `gpt-6.1-sol` with SDK 3.36.0, low reasoning, zero retries, and `store=False`. Settings matched the planned limits: 2,048 output tokens and 60 seconds except for the broken incomplete request's 128 tokens and broken timeout's 0.5 seconds. No local tools executed. The corrected structured output was validated in full before the saved excerpt was shortened to 1,000 characters; its `output_valid: true` is the recorded check, and the excerpt alone cannot reconstruct the full response.

Exact-match checks against the active credential, recognizable key/bearer checks, capture-field/header allowlist inspection, and qualitative review found no exposed credential, unexpected sensitive data, or full prompt/client/environment dumps. Reviewed public copies linked above are byte-for-byte copies of the original captures. Originals and the local audit remain under ignored `artifacts/evidence/slice4-live-20261022/`. No original authentication evidence or pilot artifacts changed, and no commit/push occurred in this checkpoint.

Available usage sums to **331 input, 475 output, 806 total tokens**, with zero cached-input and reasoning-output tokens reported. At the standard $2/million input and $10/million output rates checked in the [official model reference](https://developers.openai.com/api/docs/models/gpt-6.1-sol), this is **$0.005412 for known usage only**. It is not a billed-charge confirmation or a total for all six attempts. The service tier is not captured; rejection and timeout usage/cost remain unknown, and account billing/remaining balance were not inspected. The owner supplied the spending checkpoint before authorizing these requests. Review actual account spending before the next live milestone.

The reviewed schema capture adds 400/`invalid_function_parameters` to deterministic diagnosis. Incomplete output remains symptom-based, and a client timeout gains no fabricated HTTP mapping. The updated registry/runbook text/instructions have offline checks only; these reproduction pairs do not replace the planned ten-ticket agent evaluation.

## Capture and evidence review

Each attempt gets a separate timestamped, uniquely named JSON file under the checkout's ignored `artifacts/evidence/`. `--output-dir PATH` overrides that directory; relative overrides resolve from the caller's working directory. Failed expectations retain their artifacts. A write failure never triggers another request.

Capture selects allowlisted error/transport/completion fields, effective limits, bounded output, and available usage. It excludes full prompts, client/environment objects, authorization/cookie headers, and arbitrary response-body dumps. Active credentials and recognizable key/bearer strings are redacted before output is truncated to 1,000 characters and before serialization. Redaction still requires review before sharing.

Missing fields remain null and unavailable diagnostic headers remain an empty object. In particular, a timeout without a response has no invented HTTP 408, request ID, server error code, or usage. Older reviewed captures predate `output_valid`; preserve them as observed rather than rewriting them to match the current schema.

For a future authorized pair review:

1. Inspect each attempt's actual outcome, diagnostics, settings, available usage, and intended correction. Investigate unrelated failures rather than treating them as reproduction success.
2. Review sanitization and the field allowlist, including any credential-bearing error text or headers. Use real-credential comparisons only if explicitly authorized; never print a credential or dump full artifacts indiscriminately.
3. Confirm that both observations support the intended case. Review cumulative spending; unknown usage, especially after timeout or rejection, is not zero cost.
4. Deliberately select reviewed sanitized observations for the public `evidence/` tree and link them from the runbook's brief evidence note. Keep test fixtures in temporary directories and never publish them as live observations.
5. Update status/date/count only after pair review. Use `partially_verified` or `not_reproduced` when appropriate and leave the verification date null until verification succeeds. Retain unsuccessful observations and limitations. Customer recovery checks and passing tests do not automatically change this status.
6. Add diagnostic registry mappings only from reviewed error observations. Do not register HTTP success as a diagnosis, invent a timeout status, or add a schema mapping from an authored fixture.

## Reviewed authentication observation

The existing pair made exactly one request per variant with zero retries. Both commands exited 0. Sanitization review found no real credential, authorization/cookie headers, full prompts, client objects, or environment dumps. The masked fragment in the rejection belongs to the deliberately invalid credential. The real credential was used only for the authorized local preflight, corrected request, and exact-match artifact review; it was not displayed.

| Variant | UTC capture time | Observation | Available usage |
| --- | --- | --- | --- |
| Broken | `2026-10-22T03:22:50.374958+00:00` | HTTP 401, `AuthenticationError`, `invalid_request_error`, `invalid_api_key`, null parameter, request ID received | Null; unavailable |
| Fixed | `2026-10-22T03:23:41.220586+00:00` | HTTP 200, status `completed`, output `READY`, request ID received | 13 input, 5 output, 18 total tokens; zero cached-input and reasoning-output tokens reported |

Both requested `gpt-6.1-sol` using SDK 3.36.0, low reasoning, a 2,048-token cap, 60-second client timeout, zero retries, and `store=False`. Recorded elapsed times were approximately 395 ms and 2,962 ms. Access was established only at that observation time; these results are not a reliability benchmark or a guarantee of future access. The observed `invalid_api_key` field supports the existing 401/code mapping, not a universal taxonomy of authentication failures or proof of revocation.

The previously recorded standard-rate estimate for the corrected request was $0.000076, using $2 per million input tokens and $10 per million output tokens. This is a historical token estimate, not a current pricing assertion or inspected billing charge. The effective service tier was not captured, rejected-request usage is unknown, and account spending/remaining credit were not inspected. Verify current pricing and account spending before future live work.

## Offline checks and references

```sh
env -u OPENAI_API_KEY uv run --offline --locked --no-env-file pytest
```

`uv --offline` prevents dependency downloads; it does not block an application's own network requests. The pytest DNS/socket tripwire supplies the offline test boundary. Do not add `--run-live` to ordinary offline validation; the suite currently contains no live API tests.

- `tests/test_authentication.py` exercises the authentication pair with dummy credentials and an in-memory transport.
- `tests/test_remaining_cases.py` covers the new variants, serialized requests, effective limits, exhaustion without visible JSON, validation, refusals, timeout null fields, unrelated failures, redaction, and CLI outcomes.
- `tests/test_capture.py` covers normalization, allowlisting/redaction, missing fields, programming failures, and artifact retention.
- [Architecture](architecture.md#failure-lab-and-evidence-contract) defines the capture contract; the [implementation plan](implementation-plan.md) records milestones and limitations.
- [Official Python SDK reference](https://developers.openai.com/api/reference/python), [function-calling guide](https://developers.openai.com/api/docs/guides/function-calling), and [structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs) describe expected API interfaces.
- [Model reference and pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol) is the documentation reference for the earlier estimate; check current rates before making a new estimate.

Slice 4's initial implementation checked locked SDK interfaces and authored fixtures locally. Before the later live checkpoint, official model and structured-output documentation were checked again; the six captures establish the actual observations above. Broader behavior remains unverified.
