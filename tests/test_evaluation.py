import asyncio
import json
from copy import deepcopy

import pytest

from api_support_lab import evaluation
from api_support_lab.agent import TriageRun
from api_support_lab.cli import main
from api_support_lab.config import ConfigurationError, Settings
from api_support_lab.runbooks import get_runbook
from api_support_lab.tickets import diagnostic_values, load_ticket, load_tickets


@pytest.fixture
def records():
    drafts = {
        "T-001": {
            "category": "invalid_credentials", "candidate_runbooks": ["invalid_credentials"],
            "observed_evidence": ["HTTP 401", "error_code: invalid_api_key"],
            "basis": "stated", "severity": "unknown", "action": "recommend_fix", "missing": [],
            "customer_reply": "Please check that your application loads the intended project credential without sharing it.",
            "escalation_note": "",
        },
        "T-005": {
            "category": "undetermined", "candidate_runbooks": [], "observed_evidence": [],
            "basis": "none", "severity": "unknown", "action": "request_info",
            "missing": ["http_status", "error_code"],
            "customer_reply": "Could you share the HTTP status and error code from a minimal sanitized excerpt?",
            "escalation_note": "",
        },
        "T-009": {
            "category": "out_of_scope", "candidate_runbooks": [], "observed_evidence": ["SSO"],
            "basis": "none", "severity": "unknown", "action": "escalate", "missing": [],
            "customer_reply": "Please route this SSO setup request to your portal administrator or identity team.",
            "escalation_note": "SSO setup is outside the lab's API failure coverage; suggest the identity team.",
        },
    }
    return [{
        "schema_version": 1, "ticket_id": ticket.id, "ticket_hash": ticket.content_hash(),
        "status": "completed", "failure": None, "result": drafts[ticket.id],
        "tool_use": ([{"name": "get_runbook", "arguments": {"case": "invalid_credentials"},
                       "status": "completed", "result": get_runbook("invalid_credentials")}]
                     if ticket.id == "T-001" else []),
        "model": "synthetic-model", "settings": {}, "usage": [],
    } for ticket in load_tickets()]


def score(records):
    return evaluation.score_runs(records, load_tickets(), evaluation.load_expected())


def test_three_final_ids_and_model_input_allowlist():
    tickets = load_tickets()
    assert [ticket.id for ticket in tickets] == ["T-001", "T-005", "T-009"]
    for ticket in tickets:
        assert set(json.loads(ticket.model_input())) == {"subject", "body", "pasted_error"}
        assert ticket.id not in ticket.model_input()
        assert ticket.provenance["source"] not in ticket.model_input()
    assert diagnostic_values(tickets[0]) == ({401}, {"invalid_api_key"})
    assert diagnostic_values(tickets[1]) == (set(), set())


def test_safe_yaml_and_ticket_shape(tmp_path):
    path = tmp_path / "ticket.yaml"
    path.write_text("!!python/object/apply:os.system ['false']")
    with pytest.raises(Exception):
        load_ticket(path)
    path.write_text("id: T-001\nsubject: x\nbody: y\npasted_error: null\nexpected: secret")
    with pytest.raises(ValueError):
        load_ticket(path)


def test_scoring_synthetic_successes_requires_manual_review(records):
    report = score(records)
    assert evaluation.report_passed(report)
    assert report["summary"] == {"total": 3, "automated_pass": 3, "operational_failures": 0,
                                 "semantic_mismatches": 0}
    assert all(review["status"] == "pending" for review in report["manual_reviews"].values())
    assert report["runs"] == records


def test_operational_failure_is_not_dropped(records):
    records[0].update(status="failed", result=None, failure={"type": "APITimeoutError"})
    report = score(records)
    assert report["summary"]["total"] == 3
    assert report["summary"]["automated_pass"] == 2
    assert report["summary"]["operational_failures"] == 1
    assert report["tickets"][0]["operational_failure"] == "APITimeoutError"
    assert not evaluation.report_passed(report)


@pytest.mark.parametrize("field,value", [
    ("category", "undetermined"), ("action", "request_info"), ("severity", "high"),
    ("basis", "inferred"), ("observed_evidence", []),
])
def test_semantic_mismatches_visible(records, field, value):
    if field == "category":
        records[0]["result"]["basis"] = "none"
        records[0]["result"]["action"] = "request_info"
    records[0]["result"][field] = value
    report = score(records)
    assert report["summary"]["automated_pass"] == 2
    assert report["summary"]["semantic_mismatches"] == 1


def test_required_followup_fields_are_checked(records):
    records[1]["result"]["missing"] = []
    report = score(records)
    assert report["tickets"][1]["checks"]["missing"] is False


@pytest.mark.parametrize("change", ["schema", "retrieval", "tool_failure", "invented_lookup", "invented_evidence", "malformed_log", "nontext_retrieval"])
def test_invalid_and_ungrounded_results_are_failures(records, change):
    if change == "schema":
        records[0]["result"].pop("action")
    elif change == "retrieval":
        records[0]["tool_use"] = []
    elif change == "tool_failure":
        records[0]["tool_use"][0]["status"] = "failed"
    elif change == "invented_lookup":
        records[0]["tool_use"].append({"name": "diagnose", "arguments": {"status": 400, "error_code": None},
                                      "status": "completed", "result": []})
    elif change == "malformed_log":
        records[0]["tool_use"][0]["arguments"] = []
    elif change == "nontext_retrieval":
        records[0]["tool_use"][0]["result"] = {"error": "not a runbook"}
    else:
        records[0]["result"]["observed_evidence"] = ["A made-up error occurred"]
    report = score(records)
    assert report["tickets"][0]["operational_failure"] == "invalid_or_ungrounded_result"


def test_missing_duplicate_and_unknown_runs_stay_visible(records):
    report = score([records[0], records[0], {"ticket_id": "T-999", "status": "failed"}])
    assert report["summary"]["operational_failures"] == 3
    assert report["tickets"][0]["operational_failure"] == "duplicate_runs"
    assert report["tickets"][1]["operational_failure"] == "missing_run"
    assert len(report["runs"]) == 3
    assert report["input_issues"]


def test_hash_drift_is_visible(records):
    records[0]["ticket_hash"] = "outdated"
    report = score(records)
    assert not report["tickets"][0]["checks"]["ticket_hash"]


def test_saved_scoring_and_cli_use_no_clients(records, tmp_path, monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("offline scoring attempted a model run or key lookup")
    monkeypatch.setattr("api_support_lab.sdk.create_async_client", forbidden)
    monkeypatch.setattr("api_support_lab.sdk.require_api_key", forbidden)
    monkeypatch.setattr(evaluation, "triage_ticket", forbidden)
    source = tmp_path / "saved.json"
    source.write_text(json.dumps({"runs": records, "manual_reviews": {
        "T-001": {"status": "pass", "notes": "Authored fixture review only."},
    }}))
    assert main(["evaluate", "--results", str(source), "--output-dir", str(tmp_path / "reports")]) == 0
    assert "3/3" in capsys.readouterr().out
    saved = json.loads(next((tmp_path / "reports").glob("*.json")).read_text())
    assert saved["manual_reviews"]["T-001"]["status"] == "pass"
    source.write_text(json.dumps(records[0]))
    assert main(["evaluate", "--results", str(source), "--output-dir", str(tmp_path / "reports")]) == 1
    assert "1/3" in capsys.readouterr().out


def test_directory_scoring_includes_corrupt_artifacts(records, tmp_path):
    source = tmp_path / "runs"
    source.mkdir()
    for index, record in enumerate(records):
        (source / f"{index}.json").write_text(json.dumps(record))
    (source / "corrupt.json").write_text("{broken")
    report, path = evaluation.score_saved(source, output_dir=tmp_path / "reports")
    assert report["summary"]["automated_pass"] == 3
    assert report["input_issues"]
    assert not evaluation.report_passed(report)


def test_batch_is_sequential_and_expected_only_loaded_after_execution(records, tmp_path, monkeypatch):
    seen = []
    original_expected = evaluation.load_expected
    async def fake_triage(ticket, settings, *, live, output_dir):
        assert live
        assert len(seen) < 3
        seen.append(ticket.id)
        record = deepcopy(next(r for r in records if r["ticket_id"] == ticket.id))
        if ticket.id == "T-005":
            record.update(status="failed", result=None, failure={"type": "SyntheticFailure"})
        return TriageRun(record, tmp_path / "synthetic.json")
    def expected_after_runs():
        assert seen == ["T-001", "T-005", "T-009"]
        return original_expected()
    monkeypatch.setattr(evaluation, "triage_ticket", fake_triage)
    monkeypatch.setattr(evaluation, "load_expected", expected_after_runs)
    report, path = asyncio.run(evaluation.evaluate_live(Settings(), live=True, output_dir=tmp_path))
    assert report["summary"]["operational_failures"] == 1
    assert report["summary"]["automated_pass"] == 2
    assert path.exists()


def test_evaluation_requires_live_before_loading_tickets(monkeypatch, tmp_path):
    def forbidden():
        pytest.fail("Evaluation began before opt-in")
    monkeypatch.setattr(evaluation, "load_tickets", forbidden)
    with pytest.raises(ConfigurationError):
        asyncio.run(evaluation.evaluate_live(Settings(), live=False, output_dir=tmp_path))
