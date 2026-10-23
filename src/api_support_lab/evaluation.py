"""Ten-ticket execution and offline scoring, with failures in denominators."""

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from api_support_lab.agent import TriageResult, triage_ticket, validate_grounding
from api_support_lab.artifacts import DEFAULT_EVALUATION_DIR, sanitize, save_record, timestamp
from api_support_lab.config import Settings, require_live
from api_support_lab.runbooks import PROJECT_ROOT
from api_support_lab.tickets import Ticket, load_tickets

SCORER_VERSION = 2


class Expected(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    categories: list[str]
    basis: list[str]
    action: str
    severity: str
    required_missing: list[str]
    required_runbooks: list[str]
    required_evidence: list[str]
    forbidden_missing: list[str] = Field(default_factory=list)
    required_evidence_any: list[list[str]] = Field(default_factory=list)


def load_expected() -> dict[str, Expected]:
    data = yaml.safe_load((PROJECT_ROOT / "triage" / "expected.yaml").read_text(encoding="utf-8"))
    return {key: Expected.model_validate(value) for key, value in data.items()}


def score_runs(runs: list, tickets: list[Ticket], expectations: dict[str, Expected],
               *, manual_reviews: dict | None = None) -> dict:
    """Score against current tickets. Saved failures, absent runs, and duplicates fail.

    These are deterministic agreement checks, not a grader of reply correctness.
    Retain original records so rescoring cannot hide operational failures.
    """
    by_id: dict[str, list] = {}
    issues = []
    ticket_ids = {ticket.id for ticket in tickets}
    if ticket_ids != set(expectations):
        raise ValueError("Ticket and expectation IDs must agree")
    for run in runs:
        if (not isinstance(run, dict) or not isinstance(run.get("ticket_id"), str)
                or run["ticket_id"] not in ticket_ids):
            issues.append("Unrecognized or malformed saved run")
            continue
        by_id.setdefault(run["ticket_id"], []).append(run)
    rows = []
    reviews = {}
    for ticket in tickets:
        matches = by_id.get(ticket.id, [])
        row = {"ticket_id": ticket.id, "operational_failure": None, "checks": {},
               "automated_pass": False}
        expected = expectations[ticket.id]
        if len(matches) != 1:
            row["operational_failure"] = "missing_run" if not matches else "duplicate_runs"
        else:
            run = matches[0]
            if run.get("status") != "completed":
                failure = run.get("failure") or {}
                failure_type = failure.get("type") if isinstance(failure, dict) else None
                row["operational_failure"] = failure_type if isinstance(failure_type, str) and failure_type else "failed_run"
            else:
                try:
                    if run.get("schema_version") != 1 or run.get("failure") is not None:
                        raise ValueError("Invalid run envelope")
                    result = TriageResult.model_validate(run.get("result"))
                    tool_use = run["tool_use"]
                    if not isinstance(tool_use, list):
                        raise ValueError("Invalid tool-use record")
                    retrieved = validate_grounding(result, tool_use, ticket)
                except (ValueError, TypeError, KeyError):
                    row["operational_failure"] = "invalid_or_ungrounded_result"
                else:
                    evidence = "\n".join(result.observed_evidence)
                    row["checks"] = {
                        "ticket_hash": run.get("ticket_hash") == ticket.content_hash(),
                        "category": result.category in expected.categories,
                        "basis": result.basis in expected.basis,
                        "action": result.action == expected.action,
                        "severity": result.severity == expected.severity,
                        "missing": set(expected.required_missing) <= set(result.missing),
                        "unavailable_information": not set(expected.forbidden_missing) & set(result.missing),
                        "retrieval": set(expected.required_runbooks) <= retrieved,
                        "observed_evidence": (
                            all(fact in evidence for fact in expected.required_evidence)
                            and all(any(fact in evidence for fact in alternatives)
                                    for alternatives in expected.required_evidence_any)
                        ),
                    }
                    row["automated_pass"] = all(row["checks"].values())
        review = (manual_reviews or {}).get(ticket.id, {"status": "pending", "notes": ""})
        if (not isinstance(review, dict) or review.get("status") not in ("pending", "pass", "fail")
                or not isinstance(review.get("notes"), str)):
            issues.append(f"Invalid manual review for {ticket.id}")
        reviews[ticket.id] = review
        rows.append(row)
    return sanitize({
        "schema_version": 1,
        "scorer_version": SCORER_VERSION,
        "expectations_hash": hashlib.sha256(json.dumps(
            {key: value.model_dump() for key, value in expectations.items()},
            sort_keys=True,
        ).encode()).hexdigest(),
        "captured_at": timestamp(),
        "scope": "Ten-ticket technical learning demonstration; no reliability claim.",
        "ticket_hashes": {ticket.id: ticket.content_hash() for ticket in tickets},
        "runs": runs,
        "tickets": rows,
        "input_issues": issues,
        "summary": {
            "total": len(tickets),
            "automated_pass": sum(row["automated_pass"] for row in rows),
            "operational_failures": sum(row["operational_failure"] is not None for row in rows),
            "semantic_mismatches": sum(row["operational_failure"] is None and not row["automated_pass"] for row in rows),
        },
        "manual_reviews": reviews,
        "limitations": [
            "Automated checks do not establish reply usefulness or factual correctness.",
            "Review every reply for supported fixes, meaningful questions, uncertainty, revocation claims, data handling, and routing language.",
            "Usage may be absent or partial after failures; unknown cost is not zero.",
            "Live verification requires actual model runs and manual review; authored fixtures verify offline behavior only and do not establish agent performance.",
        ],
    })


def report_passed(report: dict) -> bool:
    return (not report["input_issues"]
            and report["summary"]["automated_pass"] == report["summary"]["total"])


def score_saved(path: Path, *, output_dir: Path = DEFAULT_EVALUATION_DIR) -> tuple[dict, Path]:
    """Read one run, a report with runs, or a directory of individual run files."""
    reviews = {}
    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            raise ValueError("No saved JSON runs found")
        runs = []
        for file in files:
            try:
                runs.append(json.loads(file.read_text(encoding="utf-8")))
            except (ValueError, OSError):
                runs.append({"status": "failed", "failure": {"type": "unreadable_artifact"}})
    else:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(saved, dict) and "runs" in saved:
            runs = saved["runs"]
            reviews = saved.get("manual_reviews", {})
        else:
            runs = [saved]
    if not isinstance(runs, list) or not isinstance(reviews, dict):
        raise ValueError("Saved results must contain a list of runs and mapping of reviews")
    report = score_runs(runs, load_tickets(), load_expected(), manual_reviews=reviews)
    return report, save_record(report, output_dir, "evaluation")


async def evaluate_live(settings: Settings, *, live: bool,
                        output_dir: Path = DEFAULT_EVALUATION_DIR) -> tuple[dict, Path]:
    require_live(live)
    tickets = load_tickets()
    runs = []
    # Sequential execution attempts each of the ten tickets once.
    # Each failure remains saved; the next ticket is still attempted, without retry.
    for ticket in tickets:
        run = await triage_ticket(ticket, settings, live=live, output_dir=output_dir / "runs")
        runs.append(run.record)
    # Expectations are first loaded AFTER all model execution.
    report = score_runs(runs, tickets, load_expected())
    return report, save_record(report, output_dir, "evaluation")
