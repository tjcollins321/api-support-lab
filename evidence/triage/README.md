# API Support Lab: initial live triage pilot

Historical. This three-ticket pilot preceded the
[ten-ticket evaluation](ten-ticket-follow-up-20261022/README.md) and is kept as the
first recorded run. Rescoring it with the current evaluator reports 3/10 with
seven missing runs, because the evaluator now expects all ten tickets; the three
saved results themselves are unchanged.

The [selected reviewed report](pilot-20261022.json) records one explicitly
authorized evaluation pass on 2026-10-22 at approximately 18:15 America/New_York
(22:15 UTC). All tickets and organizations are synthetic; T-001 includes selected
sanitized fields from the lab's observed authentication rejection. No live rerun
occurred.

| Ticket | Observed action | Automated agreement | Review note |
| --- | --- | --- | --- |
| [T-001](../../triage/tickets/T-001.yaml) | `recommend_fix` | Pass | Supported credential/environment checks after exact diagnosis and verified runbook retrieval; no revocation claim |
| [T-005](../../triage/tickets/T-005.yaml) | `request_info` | Pass | Requests HTTP status, error code/type, and impact without asserting authentication |
| [T-009](../../triage/tickets/T-009.yaml) | `escalate` | Pass | Suggests the portal administrator or identity team; no invented diagnosis or claimed handoff |

The historical report retains its qualitative review notes. Human approval is
required before using any reply. T-001's draft is somewhat long and can be
shortened before customer use. No reply was sent and no account settings changed.

The model was `gpt-6.1-sol` with low reasoning, an eight-turn limit per ticket,
4,096 output tokens per response, a 60-second client timeout, zero client/runner
retries, disabled remote tracing, and `store=False`. Six model responses were
recorded: three for T-001, two for T-005, and one for T-009.

Reported usage totaled 7,863 input tokens and 814 output tokens (8,677 total),
including 1,064 cached input tokens and 59 reasoning output tokens. Billed cost
and account spending were not inspected. Token usage is not a billing statement.

Credential exact-match checks, recognizable credential checks, structural-field
inspection, and qualitative review found no exposed credential or prompt/client/
environment dumps. All retrieved runbook text matched the registered resource.
These checks do not guarantee recognition of every possible sensitive string.

The JSON is an unchanged copy of the reviewed report. It includes all three run
records, drafts, tool use, effective settings, SDK versions, ticket hashes,
available usage, automated outcomes, review notes, and audit/usage summaries.
Original local artifacts remain unchanged under the ignored `artifacts/` tree.
Authorization bookkeeping, individual run files, and duplicate local reports are
not part of this selected evidence directory.

To score the selected report offline from a configured checkout:

```sh
env -u OPENAI_API_KEY uv run --offline --locked --no-env-file python -m api_support_lab evaluate --results evidence/triage/pilot-20261022.json
```

The command reads the current [tickets](../../triage/tickets/) and separate
[expectations](../../triage/expected.yaml), preserves the review notes, and writes
a new report under ignored `artifacts/evaluation/`. It makes no model calls and
needs no credential. At the time, all three tickets passed (3/3). Today the same
command prints **3/10** with **seven missing runs** and exits 1, as explained above.
Automated agreement does not replace qualitative reply review.

This is a three-ticket technical learning demonstration, not a reliability
benchmark or the full ten-ticket release evaluation. At the time of this pilot,
only the authentication case had been reproduced; all four cases now have
reviewed live broken/corrected pairs.
