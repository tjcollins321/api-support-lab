# Requirements

Status: first-release specification; slices 1–3 are implemented and checked offline, including deterministic tools, the asynchronous draft-only agent, and three-ticket evaluation/saved-result scoring. One separately authorized live pilot on 2026-10-22 passed all three automated outcomes, Codex-assisted qualitative reply review, artifact review, and offline rescoring. Human approval is still required before using a draft. Only the authentication reproduction pair is live-verified: 1 of 4 target cases. This document defines full-release acceptance; the current pilot does not meet R6's ten-ticket requirement or R1's four-case requirement.

## Purpose and boundaries

API Support Lab explores a complete support workflow: reproduce a failure, capture evidence, write a runbook, draft a response to a synthetic ticket, and evaluate the draft. It is a local Python learning project with human review of all suggested replies.

The target is 8–12 build hours and an initial $15 API spending allowance. Reassess before increasing either. Protect the complete workflow when reducing scope.

## Functional requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| R1 | Provide broken and corrected real-API calls for invalid credentials, malformed tool schema, incomplete structured output, and client timeout | Each verified case has both variants, sanitized evidence, and an explicit live check; unverified cases carry an explanation |
| R2 | Capture responses and SDK exceptions through one execution wrapper | Offline checks cover normalization, redaction, missing fields, successful responses, incomplete responses, and timeouts |
| R3 | Provide a runbook for each initial case | Every runbook includes symptoms, observed evidence or an unverified label, diagnosis, fix, escalation checklist, draft reply, verification date or null, and source links |
| R4 | Expose deterministic diagnosis and runbook access as three ordinary functions | Offline checks verify candidate lookup, optional and unknown codes, symptom listings, and restricted runbook access |
| R5 | Use one Agents SDK agent with read-only tools to produce structured triage drafts | Three initial tickets demonstrate the complete workflow; final examples include supported guidance, missing evidence, and escalation |
| R6 | Evaluate ten static synthetic tickets against separate expected outcomes | A saved report includes per-ticket results, automated checks, manual reply review, model/settings, and failed runs |
| R7 | Separate offline operation from live and model-backed operation | Default tests need neither a key nor network access; paid commands and live tests require explicit opt-in |
| R8 | Make the project understandable and reproducible | A README, verified setup/usage instructions, worked example, and short walkthrough reflect the delivered capabilities |

## Triage behavior

- Preserve reported evidence separately from a suspected diagnosis. A customer's proposed cause is not diagnostic proof.
- Pass only ticket-supplied status and code values to the lookup. Accept unfamiliar codes without forcing a known category.
- Retrieve supporting runbooks before suggesting a case-specific fix. Candidate matches are possibilities, including when only one is returned.
- Return category, candidate runbooks, observed evidence, stated/inferred/none basis, severity, missing information, draft reply, and escalation note.
- Use `recommend_fix`, `request_info`, or `escalate`. Severity may be `unknown`; determine it from reported impact rather than the error status.
- Treat incomplete output as distinct from transport failure. Missing response fields, including a request ID on a timeout, must not be fabricated.
- The agent drafts only. It cannot execute reproductions, alter accounts, or send messages.

## Evaluation coverage

The ten tickets cover four clear cases and six additional situations: partial evidence, ambiguous symptoms, an unfamiliar error, a misleading diagnosis, an out-of-scope request, and public-sector diagnostic-data handling. The ambiguous ticket also includes a reported business impact so severity can be checked independently of category.

Expected outcomes allow multiple acceptable categories when justified, specify required actions and information requests, and remain outside model input. Exact category labels do not replace checking the evidence and reply. Failures, refusals, and incomplete or invalid agent results remain visible in the report.

## Constraints

- Target Python 3.14, `uv`, locked dependencies, and configurable `gpt-6.1-sol` with low reasoning through Responses. Verify compatibility and access before live experiments.
- Load credentials from the environment. Capture allowlisted fields, redact credentials in text, and inspect artifacts before sharing them.
- Use invented organizations and synthetic workloads only. Public documentation describes learning goals and technical behavior.
- Mark evidence as observed, examples as illustrative, and unavailable reproductions as unverified. Verification dates apply only to actual observations.
- Default to offline checks. Bound live requests, output budgets, and agent turns; review spending between milestones.
- Keep a public repository containing the eventual code and artifacts. Disclose Codex pairing without attributing unverified work or results.

## Deferred features and completion

Defer context overflow, model-access failure cases, rate limits, quota exhaustion, MCP, expanded evaluations, hosting, a UI, databases, embeddings, and external ticketing integrations. Checking access to the configured model remains a prerequisite for live work.

The target first release has all four verified cases and runbooks, the working agent, and ten evaluated tickets. If a trigger exceeds 30 minutes, preserve the workflow and publish its reproduction limitation explicitly. A reduced release must state its verified case count and which R1 criteria remain unmet; it must not claim full coverage. All offline checks must pass, and material grounding failures must be addressed or documented in the evaluation report.

See [architecture](architecture.md) for the design and [implementation plan](implementation-plan.md) for the sequence and requirement mapping.
