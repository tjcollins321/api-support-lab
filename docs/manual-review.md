# How I review support drafts

I assess information requests and evidence quality against the ticket extracts,
structured decision, and actual `customer_reply`. I keep the runbooks written for
support engineers rather than adding an evaluation vocabulary to their prose.

## Automated agreement and manual review

The automated scorer checks result shape and grounding, ticket hashes, category,
basis, action, severity, supporting retrieval, and diagnostic preservation.
Grounding requires every evidence extract to occur verbatim in the ticket.
Diagnostic preservation checks required literal strings; it does not establish
that the chosen evidence is relevant or sufficient.

I manually assess question coverage, unnecessary questions, agreement between
`missing` and the reply, and evidence quality. A full automated score can accompany
a poor reply.

The `information_request_review` and `evidence_review` lists in
[`triage/expected.yaml`](../triage/expected.yaml) describe the ticket-specific
manual review criteria. Reports expose them as `manual_review_criteria` and
`manual_evidence_criteria`. These criteria never enter the triage agent’s prompt.
`required_diagnostic_literals` covers selected error codes, SDK exception names,
schema field paths, or a supplied incomplete reason. It does not prescribe impact
wording, customer intent, or a particular English sentence to quote.

I treat `missing` as a readable summary. Its spelling does not affect automated
agreement. I check its meaning against the reply rather than awarding coverage
from the summary alone.

## How I review each ticket

I read the ticket, retrieved runbook guidance, and complete generated draft.
For each manual review criterion, I record **Satisfied**, **Omitted**, or
**Unclear**, with an exact supporting excerpt and an explanation. I use the
customer’s ticket and selected `observed_evidence` extracts to assess evidence
quality, and the actual reply to assess information requests. I record
**Not applicable** only with a reason, such as information already supplied.
Mentioning a diagnostic concept does not establish that the reply requests it.

I also check that:

- The selected evidence supports the diagnosis, impact, uncertainty, and routing
  without treating a customer hypothesis as an established cause.
- Questions collect enough distinguishing evidence for the next decision.
- The reply does not ask again for supplied information or unretained historical
  output, and requests future collection when needed.
- Lower-priority questions are deferred rather than reproducing a full checklist.
- Requests respect sensitive-data handling and known-unavailable information.
- `missing` represents every request, including conditional follow-ups, without
  omissions or unrelated items.
- The next step, severity, tone, uncertainty, and routing fit the customer’s report.

I choose **Send as-is**, **Send with edits**, or **Would not send** and record my
reasons separately from supporting observations prepared with Codex. These
verdicts live in Markdown; the report’s `pending`/`pass`/`fail` schema is a separate
representation.

My [completed manual review](../evidence/triage/manual-review.md) records
10 Send as-is, 3 Send with edits, and all 51 manual review criteria satisfied.
I approved the whole batch separately after reviewing every ticket. The
[edited replies](../evidence/triage/edited-replies/) preserve the wording I
approved alongside the generated replies in the publication copies. Directory
rescoring creates pending manual-review fields; it does not import my Markdown
judgments or reassess the prose.

For a failed run, I show the failure and available trace; there is no accepted
draft to grade. I keep it in the full denominator. I never rewrite a generated
reply to incorporate my verdict or suggested edits. I retain untouched originals
locally; date-only publication copies and provenance changes are documented in
the [manifest](../evidence/triage/batch.json).

I can use this format:

```markdown
## Ticket ID

My verdict: Pending
My reasoning: Pending
Supporting observations prepared with Codex:

| Information-request criterion | Assessment | Exact reply excerpt and explanation |
| --- | --- | --- |
| Criterion from the report | Pending | |

| Evidence criterion | Assessment | Selected ticket extract and explanation |
| --- | --- | --- |
| Criterion from the report | Pending | |

My suggested edits:
```

## Future enhancement: a separate model grader

I could add a separate model to assess saved drafts against these criteria and
return findings with supporting excerpts. I would compare its decisions with
manually reviewed examples, including omissions, alternate genuine quotations,
irrelevant evidence, unsupported conclusions, questions about supplied
information, and keywords mentioned without a request.

I would keep those findings separate from the triage output and my verdicts.
Such a grader would require separate live authorization and is not implemented.
A small Python evaluation step could handle it; [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)
and [LangSmith](https://docs.langchain.com/langsmith/evaluation-types) are optional
tools if a more complex review workflow becomes useful. I do not need either
for the current manual review process.
