# Implementation plan

## Current state and objective

The foundation and slice 2 are complete; slice 3 is implemented, checked offline, and verified with one separately authorized three-ticket live pilot on 2026-10-22. It provides deterministic tools, one asynchronous triage agent, and the initial evaluation/offline scorer. The authentication runbook is verified from one reviewed live pair on 2026-10-21 in America/New_York (2026-10-22 UTC); 1 of 4 target reproduction cases is live-verified. The pilot also established configured-model access at its observation time. The other cases/runbooks, full ten-ticket evaluation, and walkthrough remain pending.

Build a small complete workflow before expanding coverage: real API reproduction, sanitized evidence, runbook, agent draft, and evaluation. Target 8–12 build hours and an initial $15 API allowance. Milestones are sequential; the hour ranges below are cumulative planning estimates rather than deadlines.

The full scope is an optimistic 12-hour target with little contingency; eight hours may require the documented reduced release. Reassess effort and spending after the first complete three-ticket workflow. Preserve honest limitations when cutting reproduction breadth.

The [requirements](requirements.md) define success and scope. The [architecture](architecture.md) supplies the component, interface, execution, and data contracts. Update those documents when an implementation finding changes the design; keep this plan synchronized.

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

**Offline result:** the static registry exposes only the available authentication runbook and its observed 401/`invalid_api_key` mapping. Plain functions, actual strict SDK tool schemas, restricted IDs, working-directory-independent resources, exact/unknown/status-only lookup behavior, and deterministic candidate ordering have tests. The asynchronous SDK loop runs against an in-memory transport with dummy credentials, exercising retrieval, all three pilot actions, request serialization, failed tools/API calls/timeouts/refusals/incomplete outputs, invalid/ungrounded results, and turn exhaustion. Client and runner retries are zero; client timeout, low reasoning, Responses, output/turn limits, storage, and disabled tracing are explicit. Test artifacts stay in temporary directories. Local asyncio wakeups stalled inside the execution sandbox; offline verification ran outside that restriction with the pytest DNS/socket tripwire still active.

The tickets use final IDs **T-001, T-005, T-009**; expected outcomes live separately in `triage/expected.yaml`. Only subject/body/pasted error enter the model input. Single-ticket `triage ... --live`, sequential `evaluate --live`, and offline `evaluate --results PATH` are implemented. Saved reports retain all three ticket slots, failures, tool use, per-response available usage, hashes, model/settings/SDK versions, and pending manual reviews. Missing/duplicate/corrupt or semantically mismatched results cannot silently pass. Offline checks with authored drafts do not establish actual model performance or complete R5/R6.

**Live checkpoint result:** one authorized evaluation pass completed at approximately 18:15 America/New_York on 2026-10-22 (22:15 UTC), using `gpt-6.1-sol`, low reasoning, eight turns per ticket, 4,096 output tokens per response, a 60-second client timeout, zero client/runner retries, disabled remote tracing, and `store=False`. T-001 recommended supported credential/environment checks after exact diagnosis and verified runbook retrieval; T-005 requested distinguishing status/code/type and impact data without asserting authentication; T-009 escalated SSO setup through a routing recommendation without inventing a diagnosis or claiming a handoff. All three passed automated checks and Codex-assisted qualitative reply review; human approval remains necessary before using any draft. The T-001 draft could be shortened, but no material grounding failure was found.

The six recorded model responses (3/2/1 per ticket) reported 7,863 input tokens, 814 output tokens, and 8,677 total tokens, including 1,064 cached input tokens and 59 reasoning output tokens. There were no recorded operational failures or semantic mismatches. Exact-match credential checks, recognizable-key/bearer checks, structural-field inspection, and qualitative review found no exposed credential or prompt/environment dumps. Original run records/report were preserved, review notes were saved separately, and offline rescoring of the reviewed report returned 3/3 with all review notes retained. Original artifacts remain unchanged under ignored `artifacts/evaluation/live-pilot-20261022/`. Following project-owner review and separate authorization, an unchanged copy of the reviewed report and an adapted summary were selected for [public learning-lab evidence](../evidence/triage/README.md). During live verification, no rerun, additional authentication request, reply send, account change, commit, or push occurred. Account spending and billed charges were not inspected; reported usage is not a billing confirmation. The bounded live checkpoint for the initial three tickets is complete; the remaining reproductions and seven-ticket expansion require later work and separate live authorization.

Reassess remaining time and spending here before expanding reproduction coverage. Use pilot usage and verified pricing to estimate the ten-ticket pass and reserve allowance for corrections. Turns and token caps bound operations but do not establish that they fit $15; repeated input, tool results, reruns, and timeouts also matter. Keep spending review manual.

## 4. Remaining cases and runbooks — hours 5–8

- Implement malformed tool schema, incomplete structured output, and client timeout, in that order, with broken and corrected variants using bounded workloads.
- Follow the architecture's starting limits, timebox each difficult trigger to 30 minutes, and save effective settings. Adjust within the timebox rather than making an unbounded series of calls.
- Treat budget-driven incomplete output as distinct from parser failure; inspect completion status and reason. Allow the output budget to be exhausted before visible JSON. Verify corrected structured output completes and validates.
- Preserve null HTTP fields and request ID when a timeout has no response. Record the SDK exception without asserting that server-side processing stopped.
- Write each runbook from observed evidence, or label it as partially verified/not reproduced. Extend the registry and offline/live checks without changing the three tool interfaces.

**Checkpoint:** the target is four verified cases and four complete runbooks. Count verified cases explicitly. Identify unrelated errors and unsuccessful corrections rather than counting them as successful reproduction. Review cumulative spending.

## 5. Ten-ticket evaluation — hours 8–10

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

**Checkpoint:** all ten tickets are accounted for, failed runs remain visible, and the report distinguishes automated agreement from manual findings. Scoring saved results works offline.

## 6. Documentation, example, and walkthrough — hours 10–12

- Replace intended command examples with commands checked against the implementation and locked environment. Keep planned and delivered features clearly distinguished.
- Provide the real code, CLI, runbooks, selected sanitized evidence, ticket fixtures, evaluation artifacts, and tests alongside the documentation. Do not publish local credentials or arbitrary run logs.
- Develop the README example from an actual saved run and label its provenance. Retain the Codex pairing disclosure and synthetic-data labels.
- Record a short walkthrough showing one supported recommendation, one focused request for information, and one escalation. Explain evidence and limitations in learning-lab terms.
- Inspect public files for credentials, real customer data, unsupported claims, and material outside the project's technical learning purpose. Review Git history if available before publication.

**Checkpoint:** a fresh environment can follow the setup instructions, run the default offline checks without credentials, and understand the saved example and report without a live model call. List delivered cases and known limitations accurately.

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

The foundation consists of the README, requirements, architecture, and this plan. Check their links, terminology, scope, requirement mapping, implementation-status labels, and learning-lab framing before treating them as ready for implementation.

Git was initialized on `main` on 2026-10-21 after slice 2's live verification. The initial snapshot includes the specification, offline implementation and tests, and reviewed authentication evidence. Earlier revisions were not tracked in this repository, so no pre-initialization history audit is available.
