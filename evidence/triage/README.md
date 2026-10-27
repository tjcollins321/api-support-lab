# Earlier saved triage run

[`runs/`](runs/) holds ten saved agent outputs produced on 2026-10-22,
America/New_York. Each file includes the structured decision, draft reply,
tool calls, and available usage. [`owner-review.md`](owner-review.md) records
the owner's review of those drafts.

These outputs predate the current 13 [sample tickets](../../triage/tickets/),
instructions, and runbooks. They remain available as earlier examples until a
new live run and owner review replace them. The saved tool logs preserve the
guidance the agent actually read.

To rescore them against the current [expectations](../../triage/expected.yaml)
without an API key:

```sh
uv run python -m api_support_lab evaluate --results evidence/triage/runs
```

The current result is **0/13** and exit 1: the old records no longer match the
rewritten tickets, and T-011 through T-013 have no saved runs yet. This does not
measure the current agent's reply quality. Each saved ticket hash makes the
version mismatch visible.
