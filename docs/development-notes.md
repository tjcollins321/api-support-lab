# Development notes

These notes explain the decisions behind the lab’s scope, support runbooks, and evaluation process, including the distinction between software tests and live observations and the preservation of earlier evaluation results.

I designed the specification and scope, selected failure cases and ticket scenarios with Codex, and directed the runbook structure. Codex handled code generation and prose drafting; my review covered the evidence, saved drafts, summaries, tickets, and test fixtures, along with reading the ticket, runbook, agent, and evaluation modules against the saved T-006 run.

The failure cases were kept deliberately limited to leave more time for the triage agent and ticket-based testing.

## Keeping runbooks focused on support

During review, I identified that the runbooks’ purpose and audience were unclear. I worked with Codex to refocus them as support documents and separate the lab reproduction steps into a maintainer guide.

The [support runbooks](../runbooks/) focus on customer evidence, possible causes, corrective steps, recovery checks, and escalation. Experiment commands and evidence-publication procedures live in the separate [maintainer reproduction guide](reproduction-guide.md). The agent retrieves only the support documents. The distinction is also described in the [architecture](architecture.md#runbooks-and-deterministic-tools).

The useful design lesson is to define the reader and the task before adding procedural detail. Establishing a lab example and confirming a customer's recovery require different instructions, even when they concern the same failure.

## Separating software tests from API observations

The resulting distinction matters throughout the project. An in-memory transport exercises SDK serialization, parsing, and exception handling without contacting the service. Hand-authored drafts check the evaluator's behavior. Neither demonstrates how the live API or model will respond. Real observations belong in reviewed [evidence](../evidence/); authored examples remain in [test fixtures](../tests/fixtures/).

Keeping those sources separate makes the results easier to interpret. A passing software test and a successful live experiment answer different questions.

## Evaluation review and baseline preservation

After the first evaluation returned 6/10, I requested preserving the baseline and inspected the failed drafts.

My [review notes](../evidence/triage/ten-ticket-follow-up-20261022/owner-review.md) assess the suggested next steps and identify improvements to diagnostic follow-up, information requests, customer communication, and escalation. Recommendations included comparing failed and successful requests, collecting timestamps for log correlation, and checking workload changes against earlier successful runs.

I ran the offline test suite and rescored the saved report myself.

The [evaluation follow-up](evaluation-follow-up.md) preserves the distinction between improving agent output and changing a scorer. Under scorer 2, the unchanged baseline scores 7/10; the selected final run scores 10/10. Under the original rubric, the final outputs score 9/10. Tuning on the same ten tickets limits what either comparison establishes.

The [T-006 reading path](walkthrough.md#follow-t-006-through-the-code) connects a saved reply to the input boundary, tool loop, validation, and scoring. Structured output and successful retrieval still leave the quality of the actual advice for a person to assess.
