# Reviewed ten-ticket follow-up

[reviewed-evaluation.json](reviewed-evaluation.json) is the unchanged final report
from cycle 3.

I manually reviewed all ten saved cycle-3 drafts for accuracy of their suggested
next steps and recorded **10 passes**. My review documented recommendations for
diagnostic follow-up, troubleshooting clarity, customer communication, and
escalation. The per-ticket findings are recorded in
[owner-review.md](owner-review.md); the original model responses remain unchanged.

[review-summary.json](review-summary.json) records the comparison, usage, and
selected report hash. Original runs, snapshots, reviews, audits, and offline
scores remain unchanged under ignored
`artifacts/evaluation/slice5-follow-up-20261023T002058Z/`.

Three follow-up cycles ran on **2026-10-22, 20:20:58–20:28:13 America/New_York**
(2026-10-23, 00:20:58–00:28:13 UTC). Every cycle attempted all ten tickets once,
with zero client/runner retries. The loop stopped after cycle 3.

| Cycle | Scorer 2 | Original rubric | Operational failures |
| --- | --- | --- | --- |
| 1 | 7/10 | 6/10 | 0 |
| 2 | 9/10 | 8/10 | 0 |
| 3 | **10/10** | **9/10** | 0 |

The [frozen 6/10 baseline](../ten-ticket-baseline-20261022/README.md) remains
unchanged in commit `2fbf2e2`. Its unchanged outputs score 7/10 under scorer 2;
that extra point is a scoring change, not improved model output. Scorer 2 requires
evidence of the sensitivity risk, handling question, and absent payload for
T-010, using alternative verbatim extracts rather than the original exact strings.
All three follow-up cycles used one unchanged expectations hash. The final
original-rubric mismatch is T-010 alone.

Cycle 1 retained schema-follow-up omissions and a timeout action mismatch.
Cycle 2 resolved those but omitted concrete status/code requests in the partial
complaint. Cycle 3 resolved that omission. The complete findings and scorer
rationale are in the [follow-up record](../../../docs/evaluation-follow-up.md).
Earlier failed results remain preserved; only the final cycle's report is selected
here.

Cycle 3 used `gpt-6.1-sol`, low reasoning, eight turns per ticket, a 4,096-token
cap per response, a 60-second client timeout, `store=False`, and disabled tracing.
It recorded 27 model responses with 60,681 input and 3,371 output tokens (64,052
total), including 33,413 cached input and 51 reasoning output tokens. Its known
usage standard-rate estimate was about $0.09. All three follow-ups recorded 78
responses and 170,321 tokens, estimating to about $0.25 additional known usage.
These estimates use the [rates checked at execution](https://developers.openai.com/api/docs/models/gpt-6.1-sol);
actual service tier, billed charges, and account balance were not inspected.

The recorded implementation checkpoint had 281 passing offline tests. This is a
historical live result: the runbooks have since received documentation edits, and
the revised text has not been evaluated live. The saved tool logs retain the
guidance retrieved during cycle 3. Offline rescoring checks these saved outputs
against the current tickets and expectations; it does not rerun the agent with
the revised runbooks.

These are synthetic tickets and an evaluation tuned on the same ten examples.
The results do not establish general reliability. Automated agreement and the
historical qualitative findings in the saved report remain separate; human
approval is required before using any draft. No customer reply was sent or account
settings changed.
