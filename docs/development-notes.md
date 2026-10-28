# Development notes

I set the scope, chose the failure cases and ticket scenarios, and decided what
the runbooks, the agent, and the evaluation should require. Codex wrote the Python
and first drafts of the prose; the tickets, agent instructions, runbooks, reply
templates, and expectations then went through several rounds of my restructuring
and rewriting, by hand and by direction. I read the ticket, runbook, agent, and
evaluation modules against the saved T-006 run, ran the offline tests and
rescoring myself, and reviewed all 13 generated replies.

## Keeping the scope focused

I kept the reproduced failures limited to authentication rejection, malformed
function-tool schemas, incomplete structured output, and client timeouts. This
left time to develop the triage workflow and evaluate how an agent uses support
guidance. The sample tickets include partial evidence, misleading customer
hypotheses, reported business impact, and requests outside the runbooks.

The agent drafts replies and uses read-only tools. It cannot send messages,
change accounts, or transfer tickets. A person remains responsible for deciding
whether a draft is appropriate to send.

## Writing runbooks for support engineers

The [support runbooks](../runbooks/) are written for the engineer handling the
ticket, not for someone operating the lab: what the customer reports, what the
evidence does and does not establish, what to ask for, the fix, how to confirm it,
and when to escalate. I set that order and rewrote each runbook to it. The reproduction
commands are in the [architecture](architecture.md#cli-execution-boundaries-and-budget)
and the publication steps in the [triage evidence README](../evidence/triage/README.md#publishing-a-new-batch);
provenance and reproduction links stay in each runbook's Notes section.

I also chose to keep the runbooks readable for a support engineer when
we reconsidered automated evaluation. Adding machine-oriented keywords to the
questions would have changed their audience to accommodate the tests. The
agent should use the same readable guidance as an engineer.

## Tuning the agent

I directed a full rewrite of the agent instructions so that each output field
and its allowed values is defined in its own section, and a policy can be
reviewed and changed in one place.
Supported case IDs come from the response schema, case-specific diagnostic
guidance comes from runbooks, and general intake guidance covers requests that
do not yet match a case.

Two distinctions matter: basis describes the evidence supporting a category,
while severity describes the customer's reported workflow impact. Knowing that
a client timed out does not establish the underlying cause, and a failed
request alone does not establish the severity of the disruption. Uncertainty
should remain visible in the decision and reply.

I used draft review to identify gaps in the investigation the reply proposed.
For example, when a customer has not retained a failing response, useful
guidance must explain what to collect on a future failing run, including a
sanitized output excerpt. Asking only for instrumentation would leave that
investigation incomplete. The resulting clarification belongs in the runbook.

The synthetic collection has been used during development. Its results
illustrate this workflow; they do not establish performance on unseen support
requests or general reliability.

## Evaluating the task rather than the wording

I questioned checks that rejected a meaningful question because its summary
used a different label, or rejected relevant evidence because the selected
quotation omitted a particular phrase. These checks could also pass when the
expected labels were present but the customer reply was inadequate.

I chose to keep deterministic checks for result shape, grounded tool use,
ticket identity, agreed decision values, genuine quotations, and selected
diagnostic literals. Information-request coverage and evidence relevance and
sufficiency are assessed by a person against the actual ticket, selected
extracts, and reply. The missing field remains a readable summary. The
[manual review guide](manual-review.md) explains how to record criteria,
supporting excerpts, my verdicts, and reasons.

This distinction matters when interpreting a score: changing a rubric can
change automated agreement without changing any reply. The latest reviewed
examples and results belong in the [README](../README.md#results-and-limits)
and [saved triage evidence](../evidence/triage/); these notes describe the design
decisions rather than a history of individual runs.

## Separating software checks from live observations

The in-memory SDK transport exercises serialization, parsing, and exception
handling without contacting the API. Authored fixtures exercise the evaluator.
The reviewed reproduction captures establish what happened in those API
attempts. Saved agent drafts and manual reviews establish what was produced and
judged for those particular inputs. Each source answers a different question.

A separate model grader is potential future work. It could apply the manual review
criteria to saved drafts and return findings with supporting excerpts. Its
judgments would need comparison with manual reviews before being relied upon.
I currently assess those criteria manually, without adding an evaluation
framework dependency.
