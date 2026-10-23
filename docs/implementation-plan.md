# Implementation plan

This is the historical build sequence and checkpoint record. For current usage, read the [README](../README.md); for the implemented design, read [architecture](architecture.md). The [walkthrough](walkthrough.md) and [development notes](development-notes.md) provide the written examples and learning account. Detailed evaluation results live in the [evaluation record](evaluation-follow-up.md).

The original target was 8–12 build hours with a $15 API allowance. The hour ranges below are cumulative planning estimates, not measured build times. Historical milestone details retain their original context.

## 1. Environment and execution boundaries — hours 0–2

Status: implemented offline. This slice uses no API access or API spending.

- Establish Python 3.14 with `uv`, the `src/api_support_lab` package, dependency manifest, and lockfile. Verify imports for `openai`, `openai-agents`, Pydantic, PyYAML, and pytest.
- Confirm local runner, function-tool export, Pydantic output-type, model-setting, and tracing interfaces against official documentation and installed SDK source. Disable remote tracing in the Agents SDK setup helper; defer actual tool schemas until milestone 3.
- Implement CLI help and parsing for the planned commands, including mutually exclusive live evaluation and offline saved-result scoring. Unfinished handlers return explicit errors and perform no operations, even with `--live`.
- Keep credentials outside settings. Default the model to `gpt-6.1-sol`, allow `API_SUPPORT_LAB_MODEL`, select Responses and low reasoning, and validate request bounds. Read `OPENAI_API_KEY` only when constructing an authorized live client.
- Centralize the live opt-in check and client setup with explicit timeout and zero retries. Do not add budget middleware, per-function decorators, or an authorization framework.
- Register the `live` marker and `--run-live` option. Skip live tests by default; selecting the marker alone cannot enable them. Use a small test-only network tripwire. Verify the opt-in hooks with harmless generated tests, without adding an API test in this slice.
- Add ignore rules for environments, local tooling, credentials, caches, and local artifacts. Check package imports and CLI help outside the checkout without SDK initialization.

**Completion criteria:** the locked environment installs on Python 3.14; offline tests pass without credentials or network access; help works; live forms refuse without opt-in; unfinished handlers cannot make requests; settings omit credentials; tracing is disabled by the SDK helper; and setup instructions distinguish delivered behavior from planned features. This establishes part of R7 and the foundation for R8, not full release acceptance.

**Deliberately deferred:** capture and redaction, reproduction workloads, live access verification, runbooks, deterministic lookup, actual function-tool schemas, the agent, and evaluation. If dependencies cannot install on Python 3.14, report the compatibility blocker without silently changing the target.

## 2. Authentication, capture, and the first runbook — hours 2–3

Status: complete, including separately authorized live verification and artifact review on 2026-10-21 in America/New_York. The offline phase did not read the user's actual key or `.env` contents. Tests use authored SDK fixtures and an in-memory transport with dummy credentials, and write only to temporary directories. Test commands remove the inherited API key and explicitly disable uv environment-file loading. Live preflight, the correction, and exact-match artifact review subsequently loaded the project-root `.env` without displaying the credential.

- Implement one capture wrapper, allowlisted normalization, credential redaction, separate per-attempt artifact writing, and clear unexpected-error handling.
- Add broken and corrected authentication calls using an intentionally invalid credential and the valid environment credential respectively. Keep the workload small and retries disabled.
- With separately authorized live access, use the corrected authentication request as the first bounded smoke call. Capture model/settings and available usage through the shared wrapper; a separate smoke-call implementation is unnecessary. Without access, finish offline handling and label live verification blocked.
- Capture both outcomes, inspect sanitization, and confirm the actual diagnostic fields. Never label this experiment as proof of key revocation.
- Write the authentication runbook using the architecture's template and official sources. Before live verification, explicitly label it `not_reproduced`, leave its verification date null, and state that observed evidence is absent. Add observed evidence links only after review.
- Add offline tests for response/error normalization, credential-bearing messages and headers, missing fields, incomplete/refused output, unexpected programming failures, and artifact serialization/retention. Exercise SDK request serialization, parsing, error classification, disabled retries, and CLI outcomes through an in-memory transport. Keep an explicit live broken/corrected check as the remaining verification work; no live tests are included in this offline slice.

**Offline completion:** the shared capture wrapper and both authentication command variants work against synthetic inputs; allowed fields are selected before serialization, credentials are redacted before truncation/writing, attempts are not overwritten, and unrelated or unsuccessful outcomes do not pass the per-attempt check. The broken variant does not load a genuine key; corrected requests require it only after live opt-in. Programming errors propagate and filesystem failures do not retry requests. The offline phase delivered an unverified runbook; test artifacts remain separate from live evidence.

**Checkpoint:** one case has inspectable broken and corrected evidence and a useful runbook. Default tests remain offline. Review account spending before further live work.

**Live verification result:** exactly one broken request returned HTTP 401, `AuthenticationError`, and `invalid_api_key`; one corrected request returned HTTP 200, completed status, and `READY`. Retries were disabled. Both commands exited 0. Artifact inspection confirmed expected fields and absence of the real credential, authorization/cookie headers, and full prompt/client/environment dumps. Reviewed copies are linked from the [verified runbook](../runbooks/invalid_credentials.md). No other API requests were made in this verification session.

The corrected response reported 13 input and 5 output tokens (18 total), estimating to $0.000076 at published standard rates. This is not a billed-charge confirmation: the service tier is not recorded, broken-request usage is unavailable, and the billing dashboard/remaining credit balance were not inspected. Review account spending before the next live milestone. The existing $15 total experiment allowance is unchanged. This completed slice-2 checkpoint was followed by the offline milestone-3 implementation below.

## 3. Shared tools and an initial agent workflow — hours 3–5

Status: implemented and verified offline on 2026-10-22, followed by one separately authorized live pilot that day. The implementation phase made no API/model calls and read neither the real credential nor `.env` contents. The subsequent authorization explicitly covered one three-ticket evaluation using the project-root `.env`, artifact/reply review, and offline scoring, with no rerun, commit, or push.

- Implement the static runbook registry and `diagnose`, `list_runbooks`, and `get_runbook` as ordinary functions. Add thin SDK wrappers with matching signatures.
- Test schema generation for these actual tools on Python 3.14; verify the asynchronous agent client uses explicit timeout and zero retries. Do not rely on the SDK's default client settings.
- Test optional and unfamiliar error codes, unknown status combinations, deterministic candidate order, deduplication, invalid runbook IDs, and missing files. Populate lookup entries from observations only.
- Define the structured result and instructions: preserve evidence, infer after retrieval, acknowledge incomplete information, apply the impact rubric, and draft without performing external actions.
- Bound agent turns and output, disable automatic retries initially, and record sanitized tool use and explicit run failures. Validate supporting retrieval before accepting a case-specific fix.
- Write three tickets and separate expected outcomes: clear authentication evidence, an incomplete authentication complaint, and an out-of-scope request. Implement single-ticket CLI execution and the first evaluation path.

**Checkpoint:** one command can produce a structured draft and saved tool-use record for each ticket. Demonstrate `recommend_fix`, `request_info`, and `escalate` appropriately; inspect the actual reply, not just its label. Confirm expected outcomes and answer-revealing provenance never reach the model.

**Offline result:** the static registry exposes only the available authentication runbook and its observed 401/`invalid_api_key` mapping. Plain functions, actual strict SDK tool schemas, restricted IDs, working-directory-independent resources, exact/unknown/status-only lookup behavior, and deterministic candidate ordering have tests. The asynchronous SDK loop runs against an in-memory transport with dummy credentials, exercising retrieval, all three pilot actions, request serialization, failed tools/API calls/timeouts/refusals/incomplete outputs, invalid/ungrounded results, and turn exhaustion. Client and runner retries are zero; client timeout, low reasoning, Responses, output/turn limits, storage, and disabled tracing are explicit. Test artifacts stay in temporary directories, with the pytest DNS/socket tripwire active during offline execution.

The tickets use final IDs **T-001, T-005, T-009**; expected outcomes live separately in `triage/expected.yaml`. Only subject/body/pasted error enter the model input. Single-ticket `triage ... --live`, sequential `evaluate --live`, and offline `evaluate --results PATH` are implemented. Saved reports retain all three ticket slots, failures, tool use, per-response available usage, hashes, model/settings/SDK versions, and pending manual reviews. Missing/duplicate/corrupt or semantically mismatched results cannot silently pass. Offline checks with authored drafts do not establish actual model performance or complete R5/R6.

**Live checkpoint result:** one authorized evaluation pass completed at approximately 18:15 America/New_York on 2026-10-22 (22:15 UTC), using `gpt-6.1-sol`, low reasoning, eight turns per ticket, 4,096 output tokens per response, a 60-second client timeout, zero client/runner retries, disabled remote tracing, and `store=False`. T-001 recommended supported credential/environment checks after exact diagnosis and verified runbook retrieval; T-005 requested distinguishing status/code/type and impact data without asserting authentication; T-009 escalated SSO setup through a routing recommendation without inventing a diagnosis or claiming a handoff. All three passed automated checks and Codex-assisted qualitative reply review; human approval remains necessary before using any draft. The T-001 draft could be shortened, but no material grounding failure was found.

The six recorded model responses (3/2/1 per ticket) reported 7,863 input tokens, 814 output tokens, and 8,677 total tokens, including 1,064 cached input tokens and 59 reasoning output tokens. There were no recorded operational failures or semantic mismatches. Exact-match credential checks, recognizable-key/bearer checks, structural-field inspection, and qualitative review found no exposed credential or prompt/environment dumps. Original run records/report were preserved, review notes were saved separately, and offline rescoring of the reviewed report returned 3/3 with all review notes retained. Original artifacts remain unchanged under ignored `artifacts/evaluation/live-pilot-20261022/`. Following project-owner review and separate authorization, an unchanged copy of the reviewed report and an adapted summary were selected for [public learning-lab evidence](../evidence/triage/README.md). During live verification, no rerun, additional authentication request, reply send, account change, commit, or push occurred. Account spending and billed charges were not inspected; reported usage is not a billing confirmation. The bounded live checkpoint for the initial three tickets is complete; the remaining reproductions and seven-ticket expansion require later work and separate live authorization.

Reassess remaining time and spending here before expanding reproduction coverage. Use pilot usage and verified pricing to estimate the ten-ticket pass and reserve allowance for corrections. Turns and token caps bound operations but do not establish that they fit $15; repeated input, tool results, reruns, and timeouts also matter. Keep spending review manual.

## 4. Remaining cases and runbooks — hours 5–8

Status: complete. The initial phase was implemented and checked offline on 2026-10-22 with three honestly unverified runbooks. A subsequent separately authorized live checkpoint that day completed all three pairs and their sanitization review. Each new runbook now has status `verified`, date `2026-10-22`, and reviewed evidence links. Verified count is **4 of 4**.

- Implement malformed tool schema, incomplete structured output, and client timeout, in that order, with broken and corrected variants using bounded workloads.
- Follow the architecture's starting limits, timebox each difficult trigger to 30 minutes, and save effective settings. Adjust within the timebox rather than making an unbounded series of calls.
- Treat budget-driven incomplete output as distinct from parser failure; inspect completion status and reason. Allow the output budget to be exhausted before visible JSON. Verify corrected structured output completes and validates.
- Preserve null HTTP fields and request ID when a timeout has no response. Record the SDK exception without asserting that server-side processing stopped.
- Write each runbook from observed evidence, or label it as partially verified/not reproduced. Extend the registry and offline/live checks without changing the three tool interfaces.

**Initial offline result:** broken/fixed CLI handlers covered tool schema, incomplete structured output, and client timeout through the shared capture wrapper. They use bounded synthetic workloads, low reasoning, zero retries, and `store=False`; no local tools execute. Starting limits are 128 tokens for broken incomplete output and 0.5 seconds for broken timeout, with corrected defaults of 2,048 tokens/60 seconds. CLI overrides are validated and captured. The schema predicate conservatively requires a tools-related HTTP 400 rejection, without registering unobserved mappings. Incomplete output requires explicit budget-exhaustion status/reason, even without visible JSON; corrected output must validate its full strict schema and expected 32-item content before excerpt truncation. Client timeouts preserve null transport fields when no response exists and leave server processing/cost unknown. At that offline checkpoint all four runbooks were retrievable, with only authentication mapped from observations. Agent instructions required disclosure of the then-unverified guidance.

Offline SDK transport tests cover both variants, serialized requests and pair equivalence, effective overrides, redaction, retry suppression, null timeout fields, unrelated errors, refusals, parser failures, wrong content, CLI outcomes, and status-preserving runbook retrieval. Fixtures stay in temporary directories and are not public evidence; no live tests were added. During the initial offline phase, installed SDK sources were checked without fetching current documentation or verifying service behavior. That phase made no usage/cost observation. The 30-minute trigger timebox and $15 planning allowance remain in force for later authorized work. The subsequent live phase below checked documentation, access, actual diagnostics/corrections, and sanitization before updating status/counts.

**Initial offline validation:** 219 tests passed with pytest's DNS/socket tripwire active; tests used no real credentials or network transport. The portable command is `env -u OPENAI_API_KEY uv run --offline --locked --no-env-file pytest -q`.

**Runbook audience refinement:** all four runbooks use the support-facing structure, including evidence requests, corrective steps, and customer recovery checks. Synthetic workloads, reproduction commands, attempt predicates, detailed observations, and artifact/spending/pair-review procedures moved to the maintainer reproduction guide. Status/date/evidence links remain in the runbooks. At this documentation-only checkpoint the mappings were unchanged and the count remained 1 of 4; the subsequent live checkpoint below supplied the remaining evidence. The earlier pilot retains its original retrieved text, and the revised agent workflow has no new live evaluation.

**Live checkpoint result:** the owner supplied a spending checkpoint and authorized live verification. Exactly six requests ran sequentially at 19:22–19:24 America/New_York on 2026-10-22 (23:22–23:24 UTC), using the project-root `.env` without displaying credentials. The schema pair returned HTTP 400, `BadRequestError`, `invalid_function_parameters`, and `tools[0].parameters`, then HTTP 200/completed/`READY`. The incomplete pair returned HTTP 200/incomplete/`max_output_tokens` at 128 tokens, then HTTP 200/completed with full schema and expected-content validation at a 2,048-token cap. The timeout pair raised `APITimeoutError` at a 0.5-second client limit with null HTTP fields/request ID/usage, then completed with HTTP 200/`READY` at 60 seconds. All attempts used `gpt-6.1-sol`, low reasoning, SDK 3.36.0, zero retries, and `store=False`. There were no reruns, trigger adjustments, extra smoke requests, or agent evaluations.

All six commands exited 0; exact-credential/pattern, field/header, and qualitative reviews passed before unchanged reviewed copies were selected into `evidence/`. The [maintainer guide](reproduction-guide.md#reviewed-slice-4-observations) links the pairs and records their limits; original captures and a local audit remain unchanged under ignored `artifacts/evidence/slice4-live-20261022/`. The new observed mapping is 400/`invalid_function_parameters`; incomplete output/timeout have no invented HTTP mappings. Available usage totals 331 input, 475 output, and 806 tokens, with zero cached/reasoning tokens reported. The standard-rate estimate for known usage is $0.005412, not an account charge or six-attempt total; rejection and timeout usage/cost, service tier, billed charges, and remaining balance remain unknown. Earlier public evidence/pilot artifacts were preserved. No account change, commit, or push occurred. Review actual spending before another live milestone; the ten-ticket expansion is next.

**Post-verification offline validation:** 222 tests passed after updating the schema mapping and verified-runbook checks, including exact/unknown schema codes, a status-only hypothesis, and no fabricated timeout mapping. The command above again removed the API key and disabled env-file loading/downloads, with the pytest network tripwire active. No further API requests were made.

**Checkpoint:** the target is four verified cases and four complete runbooks. Count verified cases explicitly. Identify unrelated errors and unsuccessful corrections rather than counting them as successful reproduction. Review cumulative spending.

## 5. Ten-ticket evaluation — hours 8–10

Status: offline implementation complete; the initial live baseline is preserved, and three authorized follow-ups reached a clean reviewed demonstration pass under scorer 2. The offline phase made no API/model calls or real-credential/`.env` reads.

Grow the initial three tickets into this fixed set, keeping expected outcomes separate:

| Ticket | Scenario | Expected behavior to check |
| --- | --- | --- |
| T-001 | Clear invalid-credential evidence | Retrieve the runbook and recommend supported corrective steps; do not assert revocation |
| T-002 | Clear malformed-tool-schema evidence | Identify the supplied validation evidence and retrieve schema guidance |
| T-003 | Explicit incomplete-output evidence | Check completion details and recommend the supported bounded correction |
| T-004 | Explicit client-timeout evidence | Distinguish client settings from an API error response; avoid invented transport fields |
| T-005 | Partial authentication complaint | Request distinguishing evidence rather than treating the complaint as proof |
| T-006 | HTTP success plus parser failure and a blocked report | Treat incomplete output as a hypothesis, request completion/parser details, and reflect stated impact |
| T-007 | Synthetic unfamiliar error code | Preserve the unfamiliar code and request relevant evidence without manufacturing a known match |
| T-008 | Customer claims an authentication cause but pastes schema evidence | Prefer the supplied diagnostic evidence over the asserted cause |
| T-009 | SSO request outside the lab's coverage | Escalate with a routing note and no forced runbook match |
| T-010 | Invented public-sector organization asks how to share potentially sensitive diagnostics | Escalate the handling question, request minimal sanitized metadata, and defer to its established process |

- Use sanitized observed excerpts for verified cases. Mark hand-authored unknown-error data as synthetic in evaluator-only provenance. If a case remains unverified, disclose the fixture source and exclude claims of observed live behavior.
- Define acceptable category sets, expected action/basis/severity, required evidence fields, and required runbook IDs before tuning. Do not require an unavailable request ID for a timeout known to lack a response.
- Complete automated checks for result shape, categories, actions, severity, information requests, supported retrieval, and diagnosis arguments grounded in ticket values. Add offline tests of the scorer using authored results, including failed runs.
- Manually review all ten replies for useful follow-up questions, factual support, uncertainty, data-handling boundaries, and clear escalation language. Check that requested fields appear meaningfully in the draft.
- Record all ten outcomes, including operational failures, with aggregate numerators and denominators. Save model/settings, SDK versions, ticket hashes or version, timestamp, tool use, available usage, and limitations.
- Rerun after relevant changes or failures, within the remaining budget. Address material grounding failures or document their specific impact; do not imply that a small ticket set establishes general reliability.

**Offline result:** T-001/T-005/T-009 remain unchanged. Seven new tickets complete the fixed set; T-002/T-003/T-004/T-008 use selected reviewed observations, with paths/provenance outside the three allowed model-input fields. T-007's unfamiliar code is explicitly synthetic in evaluator-only metadata. T-010 contains no sensitive content and requests handling guidance for an invented organization. Separate category/basis/action/severity/information/retrieval expectations were defined before the instruction update and authored-result fixtures. Timeout expectations request SDK/workload context and forbid demanding known-unavailable response fields.

The existing scorer and live batch now account for all ten slots. Offline tests cover authored drafts for every scenario, actual SDK serialization/tool loops through in-memory transport, required follow-ups, impact, ambiguity, unknown/misleading evidence, grounding failures, hashes, operational failures, missing/duplicate/corrupt inputs, and review preservation. Model/settings/versions/available usage remain in saved runs. A failed manual review can coexist with automated agreement; neither is implicit approval to send a reply. The original public pilot is preserved and scores as a partial 3/10 set under current expectations, with seven missing runs. These checks establish software behavior only, not agent performance.

The [maintainer evaluation guide](evaluation-guide.md) prepares a later separately authorized ten-ticket pass, artifact review, per-ticket qualitative findings, and offline rescoring. At offline completion, all ten live outcomes and manual reviews remained unobserved; the subsequent authorized pass below supplies the observations. No live rerun occurred.

**Offline validation:** 267 tests passed using `env -u OPENAI_API_KEY UV_CACHE_DIR=/tmp/api-support-lab-uv-cache uv run --offline --locked --no-env-file pytest -q`. The pytest DNS/socket guard stayed active. The restricted sandbox stalled even a minimal asyncio worker-thread shutdown; the full suite passed outside that sandbox with the same guard and credential/env-file restrictions. Reviewed evidence, earlier pilot artifacts, the three original tickets, and locked dependencies remain unchanged. No commit/push occurred.

**First live checkpoint:** one owner-authorized pass ran on 2026-10-22 at 19:58:56–20:01:23 America/New_York, loading the project-root `.env` without displaying credentials. Owner confirmation covered budget readiness and exact-credential review; numeric account spending was not supplied or inspected. The documented model/limits, zero retries, `store=False`, and disabled tracing were retained. No expectations, tickets, instructions, or runtime code were tuned to this pass.

All ten tickets were attempted once. Automated agreement was **6/10**, with **one operational failure** (T-006: `APITimeoutError` / `ReadTimeout`, no draft) and **three semantic expectation mismatches** (T-002: structured schema request missing; T-007: SDK-version request missing; T-010: exact expected evidence strings omitted). Nine drafts were available: **eight passed Codex-assisted qualitative review**, T-007 failed follow-up completeness, and T-006's record failed because no reply existed. T-002 and T-010 passed prose review despite their automated mismatches. T-006's ambiguity/high-impact behavior remains unassessed. No draft is approved for customer use by these checks.

The pass recorded 23 successful model responses and one timed-out model attempt. Available usage totals 34,989 input, 3,239 output, and 38,228 tokens, including 16,359 cached input and 77 reasoning output tokens. Checked standard rates estimate known usage at $0.0712859, excluding the timed-out attempt; service tier, billed charges, and numeric remaining allowance are unknown. Exact-credential/pattern, structural/settings, and qualitative artifact checks passed, and source/protected-artifact hashes were unchanged. Original runs/report remain under ignored `artifacts/evaluation/ten-ticket-live-20261022T235856Z/`; separate reviewed records and offline rescoring preserve every failure, mismatch, review, setting/version/usage record, and hash. Rescoring returned the expected exit 1 and 6/10. Earlier evidence/pilot artifacts were preserved; no rerun, extra smoke request, reply send, account change, publication, commit, or push occurred.

Full acceptance remains unmet. The [recorded findings](evaluation-guide.md#recorded-slice-5-live-pass) separate operational failure, structured/prose disagreement, missing follow-up, and literal evidence-check limitations. A later agreed correction/rerun scope is needed; do not retroactively relax expectations or claim reliability from this small pass.

**Authorized follow-up result:** the owner requested committing/pushing the current 6/10 baseline, then authorized offline tuning and up to ten live/tune cycles with a reported $0.11 spent of $15. Commit `2fbf2e2` and an unchanged reviewed baseline copy were pushed to `origin/main` over SSH before tuning. Source changes subsequently clarified structured/prose information requests, SDK context, supported primary actions with supplementary questions, and not-handy versus known-unavailable data. Scorer 2 adds an expectations hash and alternative verbatim evidence groups for T-010, with negative tests. The frozen baseline remains 6/10; rescoring unchanged outputs gives 7/10 solely from the criterion change.

Three cycles returned **7/10, 9/10, 10/10 under scorer 2**, **6/10, 8/10, 9/10 under the original rubric**, and **8/10, 9/10, 10/10 Codex-assisted qualitative passes**. No new operational failure occurred. The loop stopped after cycle 3, with seven cycles unused. All original results, failures, source snapshots, protected earlier artifacts, settings/versions/usage, hashes, manual notes, and offline scores were preserved. The criterion hash stayed unchanged across the three cycles. **281 offline tests passed** with the network guard active, key removed, and env-file loading/downloads disabled.

The follow-ups recorded 78 responses, 160,667 input and 9,654 output tokens (170,321 total), with 86,205 cached input and 183 reasoning output tokens. Additional known-usage standard-rate estimate: $0.2540845; billing/service tier and current balance were not inspected. Full details and per-cycle findings are in the [follow-up record](evaluation-follow-up.md). The same ten tickets were used for tuning/evaluation; this is not a held-out reliability result. After reviewing cycle 3 and its summary, the owner authorized committing/pushing the follow-up implementation and docs. An unchanged copy of the final reviewed report and comparison summary are selected in [public evidence](../evidence/triage/ten-ticket-follow-up-20261022/README.md); original runs, snapshots, and earlier outcomes remain preserved locally and the 6/10 baseline remains unchanged. Human approval remains necessary before using any reply.

**Checkpoint:** all ten tickets are accounted for, failed runs remain visible, and the report distinguishes automated agreement from manual findings. Scoring saved results works offline.

## 6. Documentation, example, and walkthrough — hours 10–12

The documentation now includes:

- A concise [README](../README.md) with an actual saved example, setup, offline commands, capability table, workflow diagram, and limitations.
- A [written walkthrough](walkthrough.md) covering a supported correction, missing-information request, escalation, and a code-reading path.
- [Development notes](development-notes.md) describing Codex collaboration, the runbook-audience correction, and evaluation lessons.
- Current architecture and maintainer guides, with historical experiment records linked separately.

The written walkthrough presents existing saved drafts and evidence.

**Checkpoint:** documented offline commands work without credentials after setup, and a reader can understand the saved examples and report without a live model call. Personal-learning claims must accurately reflect the author's contribution.

## Requirement mapping

| Requirement | Architecture section | Milestones | Acceptance check |
| --- | --- | --- | --- |
| R1: reproductions | [Failure lab](architecture.md#failure-lab-and-evidence-contract) | 2, 4 | Broken/corrected captures, explicit live checks, verified case count |
| R2: capture | [Evidence contract](architecture.md#failure-lab-and-evidence-contract) | 2, 4 | Offline normalization, redaction, missing-field and timeout checks |
| R3: runbooks | [Runbooks and tools](architecture.md#runbooks-and-deterministic-tools) | 2, 4 | Template coverage, evidence links, source links and honest status |
| R4: tools | [Runbooks and tools](architecture.md#runbooks-and-deterministic-tools) | 3 | Offline known/unknown lookup and restricted access checks |
| R5: agent | [Agent behavior](architecture.md#agent-input-output-and-behavior) | 3, 5 | Structured drafts, supporting retrieval, appropriate actions |
| R6: evaluation | [Evaluation design](architecture.md#evaluation-design) | 3, 5 | Ten accounted-for results, offline scorer checks, manual findings |
| R7: execution boundaries | [CLI and budget](architecture.md#cli-execution-boundaries-and-budget) | 1, 5 | No-key offline checks; opt-in required for API calls |
| R8: reproducibility | [Components and storage](architecture.md#components-and-storage) | 6 | Checked instructions, complete example, short walkthrough |

## Cut lines and decision checkpoints

- Preserve the agent and evaluation when reducing reproduction breadth. A reduced release states which target requirements remain unmet.
- Stop investigating a difficult trigger after 30 minutes; retain its runbook with a clear verification limitation.
- Reassess before exceeding the initial $15 allowance or 12-hour target. Local request bounds and recorded usage do not guarantee total account spending, especially for timed-out calls.
- If live access is unavailable, finish offline components and explicitly mark live verification as blocked. Do not describe test doubles as API evidence.
- Defer context overflow, model-access failure cases, rate limits, quota exhaustion, MCP, larger evaluations, hosting, a UI, databases, embeddings, and external ticketing integrations until the complete workflow works. Access verification for the configured model is still required before live work.

## Documentation foundation validation

The original foundation consisted of the README, requirements, architecture, and this plan. Current documentation checks cover links, command behavior, evidence fidelity, capability boundaries, and learning-lab framing.

Git was initialized on `main` on 2026-10-21 after slice 2's live verification. The initial snapshot includes the specification, offline implementation and tests, and reviewed authentication evidence. Earlier revisions were not tracked in this repository, so no pre-initialization history audit is available.
