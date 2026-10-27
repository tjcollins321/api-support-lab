# Development notes

I designed the project specification and scope, selected failure cases and
synthetic ticket scenarios with Codex, and directed the support workflow and
runbook structure. Codex handled code generation and prose drafting. My
contribution centered on technical direction and review: examining captured
evidence and earlier drafts, reading the ticket, runbook, agent, and evaluation
code, and deciding what the guidance and evaluation should require.

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

During review, I identified that the runbooks mixed support guidance with lab
reproduction procedures. I directed the separation: the
[support runbooks](../runbooks/) explain what customers report, what the evidence
supports, what to ask for, possible corrections, recovery checks, and routing.
Experiment commands and evidence-publication procedures belong in the
[maintainer guide](reproduction-guide.md). Provenance and reproduction links
remain in each runbook's Notes section.

I also chose to keep the runbooks readable for a support engineer when
we reconsidered automated evaluation. Adding machine-oriented keywords to the
questions would have changed their audience to accommodate the tests. The
agent should use the same readable guidance as an engineer.

## Tuning the agent

I asked for the instructions to define the output fields and their values in
separate sections, so a policy can be reviewed and refined in one place.
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
