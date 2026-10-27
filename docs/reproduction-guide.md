# Reproduction guide for lab maintainers

I use this guide to operate API Support Lab’s synthetic experiments, inspect captures, and establish the evidence supporting its runbooks. It is maintainer documentation. The [support runbooks](../runbooks/) help support staff and the triage agent investigate customer symptoms and confirm recovery. Customers troubleshoot their applications; they do not need to run these lab experiments.

The runbook registry exposes only the four support documents. This guide is not registered or retrieved by the agent's tools, and the agent cannot execute reproductions. Live experiments require explicit `--live` opt-in. Runbook recovery checks concern the customer's affected workflow; lab verification requires reviewed broken/corrected observations.

## Execution boundaries and preparation

- Use Python 3.14 and `uv` installed on PATH with the locked dependencies; follow the [README setup](../README.md#quick-start).
- Live requests require explicit `--live` opt-in. Confirm the effective model and credential source locally and review account spending before a live milestone. An authorization for one evaluation batch does not authorize an extra authentication or model-access smoke request.
- Settings default to `gpt-6.1-sol`, low reasoning, 2,048 output tokens, a 60-second client timeout, zero retries, and `store=False`. The two broken-limit exceptions are listed below.
- Only broken authentication uses the deliberately invalid credential without loading `OPENAI_API_KEY`. Its fixed variant and both variants of the other cases require a process-provided `OPENAI_API_KEY`, loaded only after live opt-in. Never print or share it.
- The application does not automatically load `.env`. An operator can explicitly use `uv run --locked --env-file .env ...`. Command examples below use `--no-env-file`; they assume any required credential is already supplied through the process environment.
- Run one variant at a time and inspect its outcome before proceeding. Do not automatically run the correction, repeat a failed call, or search for a trigger in a loop. Timebox investigation of a difficult trigger to 30 minutes and retain an honest limitation if it remains unverified.

## Experiments and commands

Every invocation makes one bounded request through the shared capture wrapper, with no automatic retries. Both variants use the same workload except for the intended defect or limit. These commands are for lab maintainers; customers troubleshoot their own applications using the support runbooks.

### Invalid credentials

Both variants request the single word `READY`. Broken authentication uses an obviously invalid credential against the normal API endpoint; the fixed variant uses the environment credential. The request body and default limits are identical. This experiment cannot establish that a real key was revoked.

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

## Capture and evidence review

Each attempt gets a separate timestamped, uniquely named JSON file under the checkout's ignored `artifacts/evidence/`. `--output-dir PATH` overrides that directory; relative overrides resolve from the caller's working directory. Failed expectations retain their artifacts. A write failure never triggers another request.

Capture selects allowlisted error/transport/completion fields, effective limits, bounded output, and available usage. It excludes full prompts, client/environment objects, authorization/cookie headers, and arbitrary response-body dumps. Active credentials and recognizable key/bearer strings are redacted before output is truncated to 1,000 characters and before serialization. Redaction still requires review before sharing.

Missing fields remain null and unavailable diagnostic headers remain an empty object. In particular, a timeout without a response has no invented HTTP 408, request ID, server error code, or usage. Older reviewed captures predate `output_valid`; preserve them as observed rather than rewriting them to match the current schema.

To review a new pair:

1. Inspect each attempt's actual outcome, diagnostics, settings, available usage, and intended correction. Investigate unrelated failures rather than treating them as reproduction success.
2. Review sanitization and the field allowlist, including any credential-bearing error text or headers. Compare against the active credential locally without printing it; never dump full artifacts indiscriminately.
3. Confirm that both observations support the intended case. Review cumulative spending; unknown usage, especially after timeout or rejection, is not zero cost.
4. Deliberately select reviewed sanitized observations for the public `evidence/` tree and link them from the runbook's brief evidence note. Keep test fixtures in temporary directories and never publish them as live observations.
5. Update status/date/count only after pair review. Use `partially_verified` or `not_reproduced` when appropriate and leave the verification date null until verification succeeds. Retain unsuccessful observations and limitations. Customer recovery checks and passing tests do not automatically change this status.
6. Add diagnostic registry mappings only from reviewed error observations. Do not register HTTP success as a diagnosis, invent a timeout status, or add a schema mapping from an authored fixture.

## Publishing a reviewed triage batch

I evaluated and reviewed the [published batch](../evidence/triage/) on 2026-10-27. The automated scorer reported 13/13 agreement, zero operational failures, and zero semantic mismatches. I separately recorded 10 Send as-is and 3 Send with edits, finding all 51 manual review criteria satisfied. I used these development samples without a separate holdout; they do not establish general reliability.

For a new evaluation, I use the following workflow:

1. I record the exact source state, including uncommitted and untracked inputs,
   source/input hashes, effective non-secret settings, and offline preflight.
   Keep credentials and ignored secret files out of the snapshot. The current
   triage bounds are eight turns per ticket, 4,096 tokens per model response,
   low reasoning, a 60-second client timeout, zero client/runner retries,
   `store=False`, and disabled tracing. They do not enforce a whole-batch
   deadline or spending ceiling.
2. I run the authorized batch once, retaining every ticket record and any failures.
   Preserve the original report and individual records. Scan artifacts for
   credentials locally without displaying matches, hash the originals, and
   rescore the saved results offline. Do not automatically retry, tune, or begin
   another live cycle.
3. I review every original draft using both sets of criteria in
   the [manual review guide](manual-review.md). Record three-way send verdicts,
   criterion assessments, reasons, supporting excerpts, and assistant observations
   separately. Obtain explicit overall approval of the exact batch and revised
   wording before replacing the published examples.
4. I keep untouched originals in ignored artifacts and publish date-only copies
   in `evidence/triage/runs/`, including failures. Shorten capture dates and
   evidence filenames, and update references in saved runbook text and ticket
   provenance. Refresh full-ticket hashes when provenance paths change;
   preserve the customer-visible input and all generated reply wording.
   Keep approved wording revisions in separate Markdown files; do not change
   generated replies in the JSON to implement them. Refresh the triage README,
   manual review, batch provenance, project README, walkthrough, and affected
   guidance from those exact records. Apply the same date-only policy to the
   eight reproduction publication copies while preserving their diagnostic
   fields and measured durations.
5. I run the offline tests and rescore the published run directory. I compare the
   summaries, per-ticket checks, and result content with the original report.
   Account explicitly for date redactions and refreshed provenance hashes;
   publication copies are not byte-identical originals.
   Directory rescoring initializes pending manual-review fields; consult the
   Markdown for my actual judgments. Check local links, quotations, artifact
   hashes, sanitization, and whitespace. Report automated findings honestly even
   after I approve the batch.

The [batch manifest](../evidence/triage/batch.json) makes the published records
traceable without depending on ignored local artifacts. It distinguishes
original and publication hashes and identifies the source commit and
execution-input hashes because a commit alone does not capture uncommitted
preparation. I retain full capture timestamps locally and publish UTC dates;
measured elapsed durations remain intact. This publication step does not rewrite
Git history or dependency upload metadata in `uv.lock`. I keep historical
artifacts locally and select the exact reviewed batch rather than combining
outputs from different attempts.

## Offline checks and references

```sh
env -u OPENAI_API_KEY uv run --offline --locked --no-env-file pytest
env -u OPENAI_API_KEY uv run --offline --locked --no-env-file python -m api_support_lab evaluate --results evidence/triage/runs
```

`uv --offline` prevents dependency downloads; it does not block an application's own network requests. The pytest DNS/socket tripwire supplies the offline test boundary. Do not add `--run-live` to ordinary offline validation; the suite currently contains no live API tests.

- `tests/test_authentication.py` exercises the authentication pair with dummy credentials and an in-memory transport.
- `tests/test_remaining_cases.py` covers the new variants, serialized requests, effective limits, exhaustion without visible JSON, validation, refusals, timeout null fields, unrelated failures, redaction, and CLI outcomes.
- `tests/test_capture.py` covers normalization, allowlisting/redaction, missing fields, programming failures, and artifact retention.
- [Architecture](architecture.md#failure-lab-and-evidence-contract) defines the capture contract.
- [Official Python SDK reference](https://developers.openai.com/api/reference/python), [function-calling guide](https://developers.openai.com/api/docs/guides/function-calling), and [structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs) describe expected API interfaces.
- [Model reference and pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol): check current rates before estimating costs.
