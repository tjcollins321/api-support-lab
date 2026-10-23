# Evaluation guide for lab maintainers

Use this guide to execute the ten-ticket evaluation, score saved results offline, and review drafts. The [evaluation record](evaluation-follow-up.md) explains the baseline, follow-up results, scorer change, and limitations. The [walkthrough](walkthrough.md) illustrates four saved decisions. Authored drafts under `tests/fixtures/` exercise software behavior and do not establish live agent performance.

## Tickets and expectations

The fixed scenarios are in [the implementation plan](implementation-plan.md#5-ten-ticket-evaluation--hours-810).
[Expected outcomes](../triage/expected.yaml) were defined before updating the
agent instructions and writing the new authored results. They specify category
sets, basis, action, impact severity, required information, evidence extracts,
and supporting retrieval. T-006 permits either an inferred incomplete-output
hypothesis or an undetermined category with basis `none`; both require the
incomplete-output runbook. HTTP success and a parser error do not establish exhaustion.

T-001, T-002, T-003, T-004, and T-008 paste selected fields from reviewed
observations; their surrounding customer stories are synthetic. T-008 deliberately
adds an unsupported customer authentication claim. The other tickets are authored
synthetic situations; T-007's `lunar_teapot_alignment_77` is invented, with no known
mapping. T-010 uses an invented public-sector organization and contains no actual
sensitive content. Provenance and evidence paths live in ticket metadata.
Only `subject`, `body`, and `pasted_error` reach the agent's ticket input.
Expectations are loaded after execution and are never tool or prompt inputs.

Information names in `missing` identify requested data, not transport fields that
must exist. `tool_schema` means a minimal sanitized serialized definition;
`parser_error` includes the parser/extraction context needed beyond a generic
exception. `workload` means approximate size and nature, without payloads.
`diagnostic_summary` means minimal sanitized metadata, subject to the organization's
handling process. T-004 already states no response arrived: it must not request an
HTTP status, server error fields, completion fields, or request ID. It can request
SDK version and workload context. Missing usage remains unknown cost.

## Offline verification and scoring

```sh
env -u OPENAI_API_KEY uv run --offline --locked --no-env-file pytest -q
env -u OPENAI_API_KEY uv run --offline --locked --no-env-file python -m api_support_lab evaluate --results PATH --output-dir artifacts/evaluation/offline-scores
```

If uv's default cache is not writable, add
`UV_CACHE_DIR=/tmp/api-support-lab-uv-cache` after `env -u OPENAI_API_KEY`.
The pytest DNS/socket guard remains active. The SDK tests use an in-memory
transport and dummy credentials; `--live` inside those tests exercises the CLI
boundary without making model calls. uv's `--offline` alone does not block
application networking.

Saved scoring accepts a run, a report containing `runs`, or a directory of run
JSON files. It uses all ten current tickets. A single passing result scores 1/10;
the unchanged earlier pilot scores 3/10 with seven missing runs. This reflects
expanded coverage, not a new finding about the earlier pilot. Do not replace
the reviewed pilot report with a current score.

Missing, duplicate, corrupt, failed, invalid, or ungrounded runs remain visible.
Checks include ticket hashes, categories, basis, action, severity, information
requests, evidence extracts, supporting retrieval, and ticket-grounded lookup
arguments. Scorer 2 saves its version/expectations hash and supports groups of
alternative grounded excerpts for T-010. Each required handling fact must still
be present; field and prose approval remain separate. The frozen 6/10 report
rescored under version 2 gives 7/10 without improved model output. T-004 also rejects requests for known-unavailable response fields.
Reports retain original runs, settings, versions, available usage, and manual
reviews. Invalid manual-review records are retained and flagged as input issues.
Exit 0 means full automated agreement with no input issues. It never approves a
reply, even if all checks pass or a manual review records `fail`.

## Future authorized live checkpoints

This guide prepares the workflow and grants no live authorization. Before that
checkpoint, review actual account spending and remaining allowance, confirm the
configured model/settings and the permitted credential source, and agree on the
ten-ticket pass and any correction/rerun scope. The first slice 5 pass used an owner
confirmation of budget readiness; numeric account spending and billing were not
inspected. Official model settings/pricing were checked, and the successful calls
established access for that pass only. Do not add an unsolicited smoke request.

After separate authorization, the implemented command form is:

```sh
uv run --locked --no-env-file python -m api_support_lab evaluate --live --output-dir artifacts/evaluation/ten-ticket-live-CHECKPOINT
```

This assumes an authorized process-provided credential; a different credential
source needs authorization at that checkpoint. Choose a fresh output directory.
Evaluation attempts tickets sequentially once each, continuing after saved
operational failures, with zero retries. Current bounds are low reasoning,
eight turns per ticket, 4,096 output tokens per response, 60-second client timeout,
Responses, `store=False`, and disabled tracing. These bounds do not guarantee a
whole-run deadline or spending ceiling.

Preserve the original report and individual runs. Review sanitization before any
sharing, including allowlisted fields, recognizable credential patterns, and
unexpected sensitive content; exact real-credential checks require authorization.
Save review notes in a separate copy of the report's `manual_reviews`, keyed by all
ten IDs, with `status: pass|fail` and substantive `notes`. Failed runs remain failed
and need notes explaining that no reply was available to approve. Keep pending
reviews explicit. Rescore the reviewed copy offline into another directory and
verify reviews, hashes, failures, settings/versions, and usage are retained.

## Manual reply review

Review actual prose as well as structured labels. Every required information field
must be asked for meaningfully; JSON field presence alone is insufficient. Record
supported fixes, uncertainty, useful questions, severity reasoning, data requests,
and routing. A passing automated report may contain an unsafe or unhelpful draft.

| Ticket | Specific manual checks |
| --- | --- |
| T-001 | Supported credential/environment checks; no assertion of revocation or request to share a key |
| T-002 | Validation evidence identifies tool parameters; minimal sanitized schema request and supported correction/recovery checks |
| T-003 | Explicit completion reason supports a larger bounded budget or smaller payload; validate full completion/schema/content |
| T-004 | Client stopped waiting; no invented HTTP fields, request ID, stopped server work, or zero cost; avoid blind retries |
| T-005 | Authentication remains a customer suspicion; ask for distinguishing status/code and impact as appropriate |
| T-006 | Blocked report supports high severity; exhaustion remains tentative; ask for completion details, output limit, parser context, and sanitized excerpt |
| T-007 | Preserve the unfamiliar code; do not replace it with a familiar mapping or infer schema trouble from HTTP 400 |
| T-008 | Prefer pasted schema diagnostics over the authentication assertion; do not prescribe credential replacement from that assertion |
| T-009 | Suggest identity/portal routing without claiming SSO setup or a handoff occurred |
| T-010 | Escalate handling through the organization's established process; initially ask only for minimal sanitized summary and impact; no sensitive records, full logs, or claim of a compliant channel |

Report all ten outcomes with automated numerators/denominators, operational
failures, semantic mismatches, and separate manual findings. Address material
grounding failures or record their specific effect before accepting the checkpoint.
Do not silently retry, tune expectations to a model answer, send a reply, change an
account, or publish artifacts. Any later rerun or publication follows its own
authorized scope. This small demonstration cannot establish general reliability.

## Recorded slice 5 live pass

One pass ran on **2026-10-22 at 19:58:56–20:01:23 America/New_York**
(2026-10-22 23:58:56–2026-10-23 00:01:23 UTC), loading the project-root `.env`
without displaying credentials. The planning allowance was $15; no numeric
current spend was supplied. All ten tickets were attempted sequentially once,
with the documented model/settings, zero retries, and no reruns or extra smoke
requests. Expectations, tickets, instructions, and runtime code were unchanged.

Automated agreement was **6/10**, with **one operational failure** and **three
semantic expectation mismatches**; there were no report input issues. Nine drafts
were available. Codex-assisted qualitative records were **8 pass, 2 fail** over ten
ticket slots: eight drafts passed, T-007 lacked a required question, and T-006 had
no draft to approve. Human approval is still required before customer use.

| Ticket | Automated outcome | Qualitative finding |
| --- | --- | --- |
| T-001 | Pass | Supported credential checks; no revocation/secret-sharing claim; could be shorter |
| T-002 | Missing-information mismatch | Reply conditionally asks for a sanitized schema, but `tool_schema` is absent from structured `missing`; prose review passed |
| T-003 | Pass | Explicit budget-exhaustion diagnosis and bounded correction with full completion/schema/content checks |
| T-004 | Pass | Preserves absent response fields and uncertainty about earlier processing/cost; no blind retry |
| T-005 | Pass | Keeps authentication tentative and requests distinguishing evidence and impact |
| T-006 | `APITimeoutError` / `ReadTimeout` | No draft; ambiguous parser failure, high impact, runbook retrieval, and required questions remain unassessed |
| T-007 | Missing-information mismatch | Unknown code preserved without a forced match, but SDK version is absent from both the structured request and reply; qualitative review failed |
| T-008 | Pass | Schema evidence takes precedence over the customer's authentication claim |
| T-009 | Pass | Suggests portal/IAM routing without claiming a handoff |
| T-010 | Evidence-excerpt mismatch | Substantively appropriate excerpts omit the exact expected strings `potentially sensitive` and `public-sector`; safe handling/routing prose passed review |

T-006 received one model response and completed a ticket-grounded
`diagnose(status=200, error_code=null)` call returning no candidates before the
next model attempt timed out. No customer diagnosis or draft was fabricated, and
no retry occurred. The timeout means that model attempt's server processing,
usage, and cost are unknown. It does not establish the cause of the ticket's
parser failure or demonstrate the agent's impact classification.

The pass recorded **23 successful model responses plus one timed-out model
attempt**. Available usage was **34,989 input, 3,239 output, 38,228 total tokens**,
including 16,359 cached input tokens and 77 reasoning output tokens. At the checked
[official standard rates](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
($2/million uncached input, $0.10/million cached input, $10/million output), known
usage estimates to **$0.0712859**. This excludes the timed-out attempt and is not a
billed total. Service tier, account billing, and numeric remaining allowance were
not inspected.

Exact active-credential/pattern, field-allowlist, settings, and qualitative artifact
checks found no exposed credential, unexpected sensitive content, or prompt or
environment dump. Source/protected-artifact hashes stayed unchanged. Original
runs and the original report are preserved under ignored
`artifacts/evaluation/ten-ticket-live-20261022T235856Z/`. The original report keeps
its pending reviews; `reviewed-evaluation.json`, `checkpoint-review.json`, and
`review.md` hold separate findings. An offline score under `offline-score/`
retained 6/10, all runs/settings/versions/usage, ticket hashes, and manual notes;
its exit code 1 is expected. No new evaluation artifacts were selected into the
public evidence tree, no replies were sent, and no account changes, commits, or
pushes occurred.

This pass does not meet full evaluation acceptance. Preserve the score and
findings. Later work should distinguish T-002's structured/prose inconsistency,
T-007's follow-up omission, T-010's literal evidence-check limitation, and T-006's
unassessed behavior. Do not tune expectations merely to make this report pass.
Any correction verification or later live run requires a separately agreed scope.

The original baseline was preserved before three follow-up tuning cycles. TJ
requested baseline preservation and inspected the failed drafts. The tuning
checkpoint reported $0.11 spent from the $15 allowance, without an inspection of
account billing. Baseline commit `2fbf2e2` preserves the unchanged reviewed report.
The three cycles reached a clean reviewed pass, with 281 offline tests passing.
Source snapshots, per-cycle failures, scores under both rubrics, manual findings,
usage, and offline rescores are preserved locally. The
[follow-up record](evaluation-follow-up.md) documents the comparison and scorer
changes; [TJ's later manual review](../evidence/triage/ten-ticket-follow-up-20261022/owner-review.md)
records feedback on all ten final drafts. No further cycle was started after
success, and the original pass above remains unchanged.
