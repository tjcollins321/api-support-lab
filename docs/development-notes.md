# Development notes

API Support Lab is a personal learning project built with Codex as a pair-programming assistant. I used it to implement the Python CLI, API experiments, agent tools, and tests, and to explain unfamiliar parts of the workflow. My role included setting scope, asking for explanations, reviewing saved replies, and questioning whether the implementation served the intended support use case. Codex proposed and implemented much of the code; the decisions below describe specific parts of that collaboration.

## Keeping runbooks focused on support

One correction came from reviewing the runbooks' audience. Their fix-and-verification sections originally mixed customer troubleshooting with instructions for running this lab's broken and corrected requests. I questioned why a support person investigating a customer's credentials would need to run our synthetic experiment.

That prompted a refactor: [support runbooks](../runbooks/) now focus on customer evidence, possible causes, corrective steps, recovery checks, and escalation. Experiment commands and evidence-publication procedures live in the separate [maintainer reproduction guide](reproduction-guide.md). The agent retrieves only the support documents. The distinction is also described in the [architecture](architecture.md#runbooks-and-deterministic-tools).

The useful design lesson is to define the reader and the task before adding procedural detail. Establishing a lab example and confirming a customer's recovery require different instructions, even when they concern the same failure.

## Separating software tests from API observations

I asked about the approach for testing without network access, including in-memory SDK responses and authored triage drafts. The discussion focused on which behaviors those tests can verify and which require live observations.

The resulting distinction matters throughout the project. An in-memory transport exercises SDK serialization, parsing, and exception handling without contacting the service. Hand-authored drafts check the evaluator's behavior. Neither demonstrates how the live API or model will respond. Real observations belong in reviewed [evidence](../evidence/); authored examples remain in [test fixtures](../tests/fixtures/).

Keeping those sources separate makes the results easier to interpret. A passing software test and a successful live experiment answer different questions.

## Learning from the evaluation

After the first ten-ticket run returned 6/10, I requested preserving that baseline before tuning. Codex then adjusted instructions and tests, ran the follow-up evaluations, and produced review summaries. I reviewed the selected replies and summaries before their inclusion as public evidence.

The [evaluation follow-up](evaluation-follow-up.md) preserves the distinction between improving agent output and changing a scorer. Under scorer 2, the unchanged baseline scores 7/10; the selected final run scores 10/10. Under the original rubric, the final outputs score 9/10. Tuning on the same ten tickets limits what either comparison establishes.

These results provide concrete behavior to inspect and discuss. Code-level understanding remains an ongoing part of the learning project: the [T-006 reading path](walkthrough.md#follow-t-006-through-the-code) connects a saved reply to the input boundary, tool loop, validation, and scoring. Structured output and successful retrieval still leave the quality of the actual advice for a person to assess.
