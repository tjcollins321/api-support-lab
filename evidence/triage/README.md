# Reviewed triage batch

I evaluated and reviewed all **13 tickets**, T-001 through T-013, on
**2026-10-27**. I published [date-only copies of the records](runs/), my
[manual review](manual-review.md), and the three [edited replies](edited-replies/)
I approved. I kept the untouched originals in ignored local artifacts.

The agent used **gpt-6.1-sol**, Python **3.14.4**, `openai` **3.36.0**, and
`openai-agents` **0.24.0**. Responses used low reasoning effort, a 4,096-token cap
per model response, at most eight turns per ticket, a 60-second client timeout,
zero client/runner retries, `store=False`, and disabled tracing. I ran the tickets
sequentially, once each. These limits are not a whole-batch deadline or spending cap.

## Automated agreement and manual review

The automated scorer reported **13/13 agreement**, **0 operational failures**,
and **0 semantic mismatches**. Offline rescoring of the publication copies
preserves those outcomes. The checks cover shape/grounding, ticket identity,
category, basis, action, severity, retrieval, and selected diagnostic literals.
They do not grade the quality of questions or selected evidence.

I separately recorded **10 Send as-is**, **3 Send with edits**, and **0 Would not
send**. I found all **51 manual review criteria Satisfied**: 26 information-request
criteria and 25 evidence criteria. I approved the whole batch and the revised
wording after reviewing every ticket.

My three edits are separate from the generated replies in the JSON:

- [T-006](edited-replies/T-006.md): remove a redundant sentence about unsaved output.
- [T-010](edited-replies/T-010.md): trim repeated explanation and approval language.
- [T-013](edited-replies/T-013.md): remove the conditional environment-variable example.

I recorded my verdicts and criterion assessments in Markdown. I did not infer
them from automated agreement or force them into the generated report’s
`pending`/`pass`/`fail` review schema. Rescoring a directory creates pending review
fields; my actual judgments are in the manual review.

## Publication copies and provenance

I removed times of day from the publication copies while keeping UTC dates:

- `captured_at` contains `YYYY-MM-DD`; measured elapsed durations remain intact.
- Evidence filenames and embedded references use dates without times. The saved
  runbook guidance is unchanged apart from those evidence links.
- Renamed provenance links change full-ticket hashes. I refreshed those hashes;
  the subject, body, and pasted error sent to the model are unchanged.

The generated decisions, replies, escalation notes, tool arguments/statuses,
usage, settings, and SDK versions are unchanged. The publication copies are
**not byte-identical originals**. The [manifest](batch.json) distinguishes original
and published record, reproduction, ticket, and source hashes. It also records
the effective settings and original report hash without exposing time-bearing
filenames. Reviewing or rescoring these examples does not require local artifacts.

## Reproduce the score offline

From the repository root, with dependencies installed:

```sh
env -u OPENAI_API_KEY uv run --offline --locked --no-env-file python -m api_support_lab evaluate --results evidence/triage/runs
```

The publication copies and current expectations produce **13/13**, exit **0**,
without model calls. Generated reports go under ignored `artifacts/`. I retain
input hashes when comparing scores because changing tickets or expectations can
change the result.

## Limits

I used these 13 synthetic samples during development, without a separate holdout
group. All organizations are invented. Selected diagnostics come from the eight
reviewed reproduction captures; authored scenarios do not establish observed API
behavior. These results demonstrate the workflow on these inputs and do not
establish unseen-ticket performance or general reliability. Missing or partial
usage remains unknown, not zero. I would still review every future customer reply.

This publication step masks times in the working tree. It does not rewrite
previous Git history. Dependency upload times in `uv.lock` describe package
releases, not my testing, and remain unchanged.
