# Development notes

These notes explain the decisions behind the lab’s scope, support runbooks, and evaluation process, including the distinction between software tests and live observations and how the agent was tuned.

I designed the specification and scope, selected failure cases and ticket scenarios with Codex, and directed the runbook structure. Codex handled code generation and prose drafting; my review covered the evidence, saved drafts, summaries, tickets, and test fixtures, along with reading the ticket, runbook, agent, and evaluation modules against the saved T-006 run.

The failure cases were kept deliberately limited to leave more time for the triage agent and ticket-based testing.

## Keeping runbooks focused on support

During review, I identified that the runbooks’ purpose and audience were unclear. I worked with Codex to refocus them as support documents and separate the lab reproduction steps into a maintainer guide.

The [support runbooks](../runbooks/) focus on customer evidence, possible causes, corrective steps, recovery checks, and escalation. Experiment commands and evidence-publication procedures live in the separate [maintainer reproduction guide](reproduction-guide.md). The agent retrieves only the support documents. The distinction is also described in the [architecture](architecture.md#runbooks-and-deterministic-tools).

The useful design lesson is to define the reader and the task before adding procedural detail. Establishing a lab example and confirming a customer's recovery require different instructions, even when they concern the same failure.

## Separating software tests from API observations

The resulting distinction matters throughout the project. An in-memory transport exercises SDK serialization, parsing, and exception handling without contacting the service. Hand-authored drafts check the evaluator's behavior. Neither demonstrates how the live API or model will respond. Real observations belong in reviewed [evidence](../evidence/); authored examples remain in [test fixtures](../tests/fixtures/).

Keeping those sources separate makes the results easier to interpret. A passing software test and a successful live experiment answer different questions.

## Tuning the agent

The sample tickets have expected decisions in `triage/expected.yaml` that the agent never sees. `evaluate` scores a run against them — category, basis, action, severity, the fields requested, the runbooks retrieved, the evidence quoted — and checks each saved output's ticket hash, so a result cannot quietly describe a ticket that has since been edited.

The first live pass scored 6/10: T-006 timed out with no draft, T-002 omitted the schema excerpt request, T-007 omitted the SDK version request, and T-010 missed the literal evidence criterion. The T-010 expectation was loosened to accept alternative verbatim extracts for the same supporting facts; this alone made the unchanged first pass score 7/10, a scorer change rather than an agent improvement. Instruction changes required every question in a reply to appear in `missing` under a canonical name, included SDK version among the requests for an unfamiliar code, required a schema excerpt even when the error named the bad value, and treated "not handy" as collectable later. The first follow-up still omitted schema requests for T-002 and T-008; three follow-up cycles reached 10/10 under scorer 2, or 9/10 under the original rubric. T-006 produced drafts in those follow-ups; the instruction changes do not establish why its earlier timeout did not recur.

The original tuning used ten hand-authored tickets. The current demonstration has 13 sample tickets; the outputs in [`evidence/triage/runs/`](../evidence/triage/runs/) and notes in [`owner-review.md`](../evidence/triage/owner-review.md) still describe the earlier run and await replacement. These examples demonstrate the workflow, not reliability. Earlier reports remain in Git history.

The [T-006 reading path](walkthrough.md#follow-t-006-through-the-code) connects a saved reply to the input boundary, tool loop, validation, and scoring. Structured output and successful retrieval still leave the quality of the actual advice for a person to assess.
