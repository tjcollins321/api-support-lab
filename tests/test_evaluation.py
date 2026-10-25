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
def records(authored_drafts):
    return [{
        "schema_version": 1, "ticket_id": ticket.id, "ticket_hash": ticket.content_hash(),
        "status": "completed", "failure": None, "result": authored_drafts[ticket.id],
        "tool_use": [{"name": "get_runbook", "arguments": {"case": case},
                      "status": "completed", "result": get_runbook(case)}
                     for case in authored_drafts[ticket.id]["candidate_runbooks"]],
        "model": "synthetic-model", "settings": {"max_turns": 8},
        "sdk_versions": {"openai": "authored", "openai-agents": "authored"},
        "usage": [None],
    } for ticket in load_tickets()]


def score(records):
    return evaluation.score_runs(records, load_tickets(), evaluation.load_expected())


def test_ten_final_ids_and_model_input_allowlist():
    tickets = load_tickets()
    assert [ticket.id for ticket in tickets] == [f"T-{i:03}" for i in range(1, 11)]
    for ticket in tickets:
        assert set(json.loads(ticket.model_input())) == {"subject", "body", "pasted_error"}
        assert ticket.id not in ticket.model_input()
        assert ticket.provenance["source"] not in ticket.model_input()
    assert diagnostic_values(tickets[0]) == ({401}, {"invalid_api_key"})
    assert diagnostic_values(tickets[4]) == (set(), set())


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
    assert report["summary"] == {"total": 10, "automated_pass": 10, "operational_failures": 0,
                                 "semantic_mismatches": 0}
    assert all(review["status"] == "pending" for review in report["manual_reviews"].values())
    assert report["runs"] == records


def test_operational_failure_is_not_dropped(records):
    records[0].update(status="failed", result=None, failure={"type": "APITimeoutError"})
    report = score(records)
    assert report["summary"]["total"] == 10
    assert report["summary"]["automated_pass"] == 9
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
    assert report["summary"]["automated_pass"] == 9
    assert report["summary"]["semantic_mismatches"] == 1


def test_required_followup_fields_are_checked(records):
    records[4]["result"]["missing"] = []
    report = score(records)
    assert report["tickets"][4]["checks"]["missing"] is False


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
    assert report["summary"]["operational_failures"] == 10
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
    assert "10/10" in capsys.readouterr().out
    saved = json.loads(next((tmp_path / "reports").glob("*.json")).read_text())
    assert saved["manual_reviews"]["T-001"]["status"] == "pass"
    source.write_text(json.dumps(records[0]))
    assert main(["evaluate", "--results", str(source), "--output-dir", str(tmp_path / "reports")]) == 1
    assert "1/10" in capsys.readouterr().out


def test_directory_scoring_includes_corrupt_artifacts(records, tmp_path):
    source = tmp_path / "runs"
    source.mkdir()
    for index, record in enumerate(records):
        (source / f"{index}.json").write_text(json.dumps(record))
    (source / "corrupt.json").write_text("{broken")
    report, path = evaluation.score_saved(source, output_dir=tmp_path / "reports")
    assert report["summary"]["automated_pass"] == 10
    assert report["input_issues"]
    assert not evaluation.report_passed(report)


def test_batch_is_sequential_and_expected_only_loaded_after_execution(records, tmp_path, monkeypatch):
    seen = []
    original_expected = evaluation.load_expected
    async def fake_triage(ticket, settings, *, live, output_dir):
        assert live
        assert len(seen) < 10
        seen.append(ticket.id)
        record = deepcopy(next(r for r in records if r["ticket_id"] == ticket.id))
        if ticket.id == "T-005":
            record.update(status="failed", result=None, failure={"type": "SyntheticFailure"})
        return TriageRun(record, tmp_path / "synthetic.json")
    def expected_after_runs():
        assert seen == [f"T-{i:03}" for i in range(1, 11)]
        return original_expected()
    monkeypatch.setattr(evaluation, "triage_ticket", fake_triage)
    monkeypatch.setattr(evaluation, "load_expected", expected_after_runs)
    report, path = asyncio.run(evaluation.evaluate_live(Settings(), live=True, output_dir=tmp_path))
    assert report["summary"]["operational_failures"] == 1
    assert report["summary"]["automated_pass"] == 9
    assert path.exists()


def test_evaluation_requires_live_before_loading_tickets(monkeypatch, tmp_path):
    def forbidden():
        pytest.fail("Evaluation began before opt-in")
    monkeypatch.setattr(evaluation, "load_tickets", forbidden)
    with pytest.raises(ConfigurationError):
        asyncio.run(evaluation.evaluate_live(Settings(), live=False, output_dir=tmp_path))


@pytest.mark.parametrize("ticket_id", ["T-002", "T-003", "T-004", "T-006", "T-007", "T-008", "T-010"])
@pytest.mark.parametrize("field", ["action", "severity", "observed_evidence"])
def test_new_scenarios_reject_wrong_action_severity_and_evidence(records, ticket_id, field):
    index = next(i for i, record in enumerate(records) if record["ticket_id"] == ticket_id)
    result = records[index]["result"]
    if field == "action":
        result["action"] = "request_info" if result["action"] != "request_info" else "escalate"
        result["escalation_note"] = "Suggest application support; no handoff occurred."
    elif field == "severity":
        result["severity"] = "low"  # No new ticket reports a limited nonblocking issue.
    else:
        result["observed_evidence"] = []
    report = score(records)
    row = report["tickets"][index]
    if ticket_id == "T-010" and field == "action":
        assert row["operational_failure"] == "invalid_or_ungrounded_result"
    else:
        assert row["operational_failure"] is None
        assert not row["checks"][field]
    assert report["summary"]["automated_pass"] == 9


@pytest.mark.parametrize("field", ["http_status", "error_code", "error_type", "request_id", "response_status", "incomplete_reason"])
def test_timeout_does_not_require_known_unavailable_response_fields(records, field):
    records[3]["result"]["missing"].append(field)
    report = score(records)
    assert not report["tickets"][3]["checks"]["unavailable_information"]
    assert not evaluation.report_passed(report)


def test_ambiguous_parser_failure_allows_no_diagnosis_with_supporting_retrieval(records):
    records[5]["result"].update(category="undetermined", basis="none")
    assert evaluation.report_passed(score(records))
    records[5]["result"].update(basis="stated", category="incomplete_output")
    assert not score(records)["tickets"][5]["checks"]["basis"]


@pytest.mark.parametrize("index", [6, 7])
def test_unknown_code_or_customer_assertion_cannot_force_a_known_category(records, index):
    records[index]["result"].update(category="invalid_credentials", basis="stated")
    records[index]["tool_use"].append({
        "name": "get_runbook", "arguments": {"case": "invalid_credentials"},
        "status": "completed", "result": get_runbook("invalid_credentials"),
    })
    report = score(records)
    assert not report["tickets"][index]["checks"]["category"]


def test_unknown_code_replacement_is_ungrounded_even_with_matching_status(records):
    records[6]["tool_use"].append({
        "name": "diagnose", "arguments": {"status": 400, "error_code": "invalid_function_parameters"},
        "status": "completed", "result": ["tool_schema"],
    })
    assert score(records)["tickets"][6]["operational_failure"] == "invalid_or_ungrounded_result"


def test_required_retrieval_is_checked_even_for_undetermined_category(records):
    records[5]["result"].update(category="undetermined", basis="none", candidate_runbooks=[])
    records[5]["tool_use"] = []
    assert not score(records)["tickets"][5]["checks"]["retrieval"]


def test_review_failure_does_not_change_automated_agreement(records, tmp_path):
    reviews = {r["ticket_id"]: {"status": "pass", "notes": "Authored example only."} for r in records}
    reviews["T-010"] = {"status": "fail", "notes": "Example manual finding retained separately."}
    source = tmp_path / "reviewed.json"
    source.write_text(json.dumps({"runs": records, "manual_reviews": reviews}))
    report, _ = evaluation.score_saved(source, output_dir=tmp_path / "scores")
    assert evaluation.report_passed(report)  # Automated agreement only.
    assert report["manual_reviews"] == reviews
    assert report["runs"] == records  # Includes model/settings/versions and unknown usage.


@pytest.mark.parametrize("review", [None, "pass", {"status": "approved", "notes": "x"}, {"status": "pass"}])
def test_corrupt_review_is_preserved_and_flagged(records, review):
    report = evaluation.score_runs(records, load_tickets(), evaluation.load_expected(),
                                   manual_reviews={"T-010": review})
    assert report["manual_reviews"]["T-010"] == review
    assert report["input_issues"] == ["Invalid manual review for T-010"]
    assert not evaluation.report_passed(report)


def test_observed_ticket_fields_match_reviewed_captures():
    from api_support_lab.runbooks import PROJECT_ROOT

    tickets = {ticket.id: ticket for ticket in load_tickets()}
    for ticket_id in ("T-001", "T-002", "T-003", "T-004", "T-008"):
        ticket = tickets[ticket_id]
        observation = json.loads((PROJECT_ROOT / ticket.provenance["evidence"]).read_text())
        for line in ticket.pasted_error.splitlines():
            if line.startswith("HTTP "):
                assert int(line.removeprefix("HTTP ")) == observation["http_status"]
            else:
                field, value = line.split(": ", 1)
                assert value == str(observation[field])
        assert ticket.provenance["evidence"] not in ticket.model_input()
    timeout = tickets["T-004"]
    assert diagnostic_values(timeout) == (set(), set())
    assert "0.5-second" in timeout.body


@pytest.mark.parametrize("ticket_id", ["T-002", "T-004", "T-006", "T-007", "T-008", "T-010"])
def test_new_required_information_fields_are_enforced(records, ticket_id):
    index = next(i for i, record in enumerate(records) if record["ticket_id"] == ticket_id)
    records[index]["result"]["missing"] = []
    assert not score(records)["tickets"][index]["checks"]["missing"]


@pytest.mark.parametrize("evidence", [
    ["potentially sensitive", "how should we route"],
    ["potentially sensitive", "what minimal/sanitized metadata"],
    ["potentially sensitive", "Before sharing anything"],
])
def test_handling_evidence_accepts_grounded_alternatives(records, evidence):
    records[9]["result"]["observed_evidence"] = evidence
    assert evaluation.report_passed(score(records))


@pytest.mark.parametrize("evidence", [
    ["potentially sensitive"],
    ["how should we route"],
    [],
])
def test_handling_evidence_requires_each_supporting_fact(records, evidence):
    records[9]["result"]["observed_evidence"] = evidence
    report = score(records)
    assert report["tickets"][9]["operational_failure"] is None
    assert not report["tickets"][9]["checks"]["observed_evidence"]


def test_sector_label_alone_does_not_support_handling_escalation(records):
    tickets = load_tickets()
    tickets[9] = tickets[9].model_copy(update={"body": "We are a public-sector organization."})
    records[9]["ticket_hash"] = tickets[9].content_hash()
    records[9]["result"]["observed_evidence"] = ["public-sector"]
    row = evaluation.score_runs(records, tickets, evaluation.load_expected())["tickets"][9]
    assert row["operational_failure"] is None
    assert not row["checks"]["observed_evidence"]


def test_matching_evidence_substrings_still_require_verbatim_ticket_support(records):
    records[9]["result"]["observed_evidence"] = [
        "An actual agency sent potentially sensitive records; how should we route?",
    ]
    assert score(records)["tickets"][9]["operational_failure"] == "invalid_or_ungrounded_result"


def test_report_identifies_scorer_and_expectations_without_changing_runs(records):
    expectations = evaluation.load_expected()
    first = evaluation.score_runs(records, load_tickets(), expectations)
    reordered = evaluation.score_runs(records, load_tickets(), dict(reversed(list(expectations.items()))))
    assert first["scorer_version"] == 2
    assert first["expectations_hash"] == reordered["expectations_hash"]
    assert first["runs"] == records
    expectations["T-007"].required_missing.append("attempt_time_utc")
    changed = evaluation.score_runs(records, load_tickets(), expectations)
    assert changed["expectations_hash"] != first["expectations_hash"]
    assert changed["summary"]["automated_pass"] == 9


def test_generic_summary_does_not_replace_distinguishing_diagnostic_fields(records):
    records[4]["result"].update(
        missing=["diagnostic_summary", "impact"],
        customer_reply="Please share a sanitized symptom summary and impact, including any exception or code you can access.",
    )
    row = score(records)["tickets"][4]
    assert row["operational_failure"] is None
    assert row["checks"]["category"] and row["checks"]["basis"]
    assert not row["checks"]["missing"]


@pytest.mark.parametrize("index,field", [(4, "http_status"), (4, "error_code"), (6, "sdk_version")])
def test_each_distinguishing_field_is_independently_required(records, index, field):
    records[index]["result"]["missing"].remove(field)
    assert not score(records)["tickets"][index]["checks"]["missing"]
