# Saved triage runs

[`runs/`](runs/) holds the agent's saved output for each of the ten tickets in [`triage/tickets/`](../../triage/tickets/) — the structured decision, the draft reply, the tool calls it made, and usage — produced on 2026-10-22, America/New_York. [`owner-review.md`](owner-review.md) records the owner's reading of each draft.

The runbooks were edited after these runs; the saved tool logs retain the guidance the agent actually read. The agent has not been rerun with the revised guidance.

Score the outputs against [`triage/expected.yaml`](../../triage/expected.yaml) without an API key:

```sh
uv run python -m api_support_lab evaluate --results evidence/triage/runs
```

Each run records a hash of its ticket, so a saved output cannot quietly describe a ticket that has since been edited.
