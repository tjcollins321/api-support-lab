"""Authored fixtures through the real SDK; no API observations or real credentials."""

import json

import httpx2
import openai
import pytest

from api_support_lab.cases import incomplete_output, timeout, tool_schema
from api_support_lab.cli import main
from api_support_lab.config import ConfigurationError, Settings

CASES = (tool_schema, incomplete_output, timeout)
KEY = "dummy-slice-four-credential"


def structured_text():
    return json.dumps({"status": "READY", "items": [
        {"index": i, "label": f"item_{i}"} for i in range(1, 33)
    ]})


def response(text="READY", *, status="completed", reason=None):
    return {
        "id": "resp_synthetic", "object": "response", "created_at": 0,
        "model": "synthetic-model", "status": status,
        "incomplete_details": {"reason": reason} if reason else None,
        "output": [] if text is None else [{
            "id": "msg_synthetic", "type": "message", "role": "assistant", "status": status,
            "content": [{"type": "output_text", "text": text, "annotations": []}],
        }],
        "usage": {"input_tokens": 10, "output_tokens": 12, "total_tokens": 22},
    }


def intended(case, variant):
    if variant == "fixed":
        return response(structured_text() if case is incomplete_output else "READY")
    if case is tool_schema:
        return (400, {"error": {
            "message": f"Synthetic invalid schema {KEY}", "type": "invalid_request_error",
            "code": "synthetic_schema_code", "param": "tools[0].parameters",
        }})
    if case is incomplete_output:
        return response(None, status="incomplete", reason="max_output_tokens")
    return httpx2.ReadTimeout(KEY)


@pytest.fixture
def transport(monkeypatch):
    original = openai.OpenAI
    monkeypatch.setenv("OPENAI_API_KEY", KEY)

    def install(value):
        requests, clients = [], []

        def handler(request):
            requests.append(request)
            if isinstance(value, Exception):
                raise value
            status, body = value if isinstance(value, tuple) else (200, value)
            return httpx2.Response(status, json=body, headers={
                "x-request-id": "req_synthetic", "authorization": KEY, "set-cookie": KEY,
            })

        def factory(**kwargs):
            client = original(**kwargs, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))
            clients.append(client)
            return client

        monkeypatch.setattr(openai, "OpenAI", factory)
        return requests, clients

    return install


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_wire_contract_and_single_attempt(case, variant, transport, tmp_path):
    requests, clients = transport(intended(case, variant))
    result = getattr(case, variant)(Settings(model="synthetic-model"), live=True, output_dir=tmp_path)
    assert case.matches_expected(result)
    assert len(requests) == 1
    assert clients[0].max_retries == 0
    assert clients[0].timeout == (0.5 if case is timeout and variant == "broken" else 60)
    assert clients[0].is_closed()
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://api.openai.com/v1/responses"
    assert request.headers["authorization"] == f"Bearer {KEY}"
    body = json.loads(request.content)
    cap = 128 if case is incomplete_output and variant == "broken" else 2048
    assert body["max_output_tokens"] == result.record["settings"]["max_output_tokens"] == cap
    assert result.record["settings"]["timeout_seconds"] == clients[0].timeout
    assert body["reasoning"] == {"effort": "low"}
    assert body["model"] == "synthetic-model"
    assert body["store"] is False
    assert body["input"] == case.WORKLOAD
    assert json.loads(result.path.read_text()) == result.record
    saved = result.path.read_text()
    assert KEY not in saved
    assert case.WORKLOAD not in saved
    assert "authorization" not in saved and "set-cookie" not in saved
    assert len(list(tmp_path.glob("*.json"))) == 1
    if case is tool_schema:
        tool = body["tools"][0]
        assert tool["type"] == "function" and tool["strict"] is True
        assert tool["parameters"]["additionalProperties"] is False
        assert tool["parameters"]["required"] == ["label"]
        assert tool["parameters"]["properties"]["label"]["type"] == (
            "not_a_json_schema_type" if variant == "broken" else "string"
        )
        assert body["tool_choice"] == "none"
    if case is incomplete_output:
        fmt = body["text"]["format"]
        assert fmt["type"] == "json_schema" and fmt["strict"] is True
        assert fmt["schema"]["additionalProperties"] is False
        assert fmt["schema"]["$defs"]["Item"]["additionalProperties"] is False
        assert result.record["output_valid"] is (True if variant == "fixed" else None)
        if variant == "fixed":
            assert len(structured_text()) > 1000
            assert len(result.record["output_excerpt"]) == 1000
    if case is timeout and variant == "broken":
        for field in ("http_status", "request_id", "error_code", "error_type", "error_param", "usage", "response_status"):
            assert result.record[field] is None
        assert result.record["headers"] == {}


@pytest.mark.parametrize("case", CASES)
def test_pair_changes_only_intended_setting(case, transport, tmp_path):
    bodies, clients = [], []
    for variant in ("broken", "fixed"):
        requests, made = transport(response())
        getattr(case, variant)(Settings(), live=True, output_dir=tmp_path)
        bodies.append(json.loads(requests[0].content))
        clients.extend(made)
    if case is tool_schema:
        bodies[0]["tools"][0]["parameters"]["properties"]["label"]["type"] = "string"
    elif case is incomplete_output:
        bodies[0]["max_output_tokens"] = 2048
    else:
        assert [client.timeout for client in clients] == [0.5, 60]
    assert bodies[0] == bodies[1]


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_case_requires_live_and_key_before_requests(case, variant, transport, tmp_path, monkeypatch):
    requests, clients = transport(response())
    with pytest.raises(ConfigurationError, match="--live"):
        getattr(case, variant)(Settings(), live=False, output_dir=tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        getattr(case, variant)(Settings(), live=True, output_dir=tmp_path)
    assert requests == clients == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_unrelated_errors_retained_without_retry_or_success(case, variant, transport, tmp_path):
    requests, _ = transport((500, {"error": {"message": KEY, "code": "synthetic_failure"}}))
    result = getattr(case, variant)(Settings(), live=True, output_dir=tmp_path)
    assert not case.matches_expected(result)
    assert len(requests) == 1
    assert result.path.exists()
    assert result.record["http_status"] == 500
    assert KEY not in result.path.read_text()


@pytest.mark.parametrize("param", [None, "input", "tools_unrelated"])
def test_other_bad_requests_do_not_verify_schema_case(param, transport, tmp_path):
    transport((400, {"error": {"message": "Synthetic unrelated validation", "param": param}}))
    result = tool_schema.broken(Settings(), live=True, output_dir=tmp_path)
    assert not tool_schema.matches_expected(result)


@pytest.mark.parametrize("body", [
    response(None), response('{"status":', status="incomplete", reason="content_filter"),
    response('{"status":'), response(None, status="incomplete"),
])
def test_parser_failure_or_other_completion_does_not_prove_exhaustion(body, transport, tmp_path):
    transport(body)
    result = incomplete_output.broken(Settings(), live=True, output_dir=tmp_path)
    assert not incomplete_output.matches_expected(result)


@pytest.mark.parametrize("text", [
    "not JSON", '{"status":"READY","items":[]}',
    structured_text().replace('"index": 1,', '"index": "1",', 1),
    structured_text().replace('"item_32"', '"wrong"'),
    structured_text().replace('"status": "READY"', '"status": "WRONG"'),
    structured_text().replace('"status": "READY"', '"extra": 1, "status": "READY"'),
])
def test_corrected_output_must_validate_schema_and_expected_content(text, transport, tmp_path):
    transport(response(text))
    result = incomplete_output.fixed(Settings(), live=True, output_dir=tmp_path)
    assert result.record["output_valid"] is False
    assert not incomplete_output.matches_expected(result)
    assert result.path.exists()


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("kind", ["incomplete", "empty", "refusal"])
def test_http_success_alone_does_not_verify_corrections(case, kind, transport, tmp_path):
    body = response(None, status="incomplete", reason="max_output_tokens") if kind == "incomplete" else response(None)
    if kind == "refusal":
        body["output"] = [{"type": "message", "content": [{"type": "refusal", "refusal": "Synthetic refusal"}]}]
    transport(body)
    result = case.fixed(Settings(), live=True, output_dir=tmp_path)
    assert not case.matches_expected(result)
    if kind != "empty":
        assert result.record["output_valid"] is None


@pytest.mark.parametrize("value", [
    httpx2.ConnectError("Synthetic connection failure"),
    (408, {"error": {"message": "Synthetic HTTP timeout response"}}),
    response(),
])
def test_only_sdk_client_timeout_verifies_timeout_trigger(value, transport, tmp_path):
    requests, _ = transport(value)
    result = timeout.broken(Settings(), live=True, output_dir=tmp_path)
    assert not timeout.matches_expected(result)
    assert len(requests) == 1


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_cli_dispatch_and_artifacts(case, variant, transport, tmp_path, capsys):
    requests, _ = transport(intended(case, variant))
    case_id = case.__name__.rsplit(".", 1)[1]
    assert main(["reproduce", case_id, "--variant", variant, "--live", "--output-dir", str(tmp_path)]) == 0
    assert len(requests) == 1
    assert "Pair verification requires both variants and review" in capsys.readouterr().out


@pytest.mark.parametrize("case_id,flag,value,field", [
    ("incomplete_output", "--max-output-tokens", "256", "max_output_tokens"),
    ("timeout", "--timeout-seconds", "0.25", "timeout_seconds"),
])
@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_cli_records_effective_overrides(case_id, flag, value, field, variant, transport, tmp_path):
    requests, clients = transport(response())
    main(["reproduce", case_id, "--variant", variant, "--live", flag, value, "--output-dir", str(tmp_path)])
    record = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert record["settings"][field] == float(value)
    if field == "timeout_seconds":
        assert clients[0].timeout == float(value)
    else:
        assert json.loads(requests[0].content)[field] == int(value)


@pytest.mark.parametrize("flag,value", [("--max-output-tokens", "0"), ("--timeout-seconds", "nan")])
def test_cli_invalid_limits_fail_before_clients(flag, value, transport, tmp_path):
    requests, clients = transport(response())
    with pytest.raises(SystemExit) as error:
        main(["reproduce", "timeout", "--variant", "broken", "--live", flag, value, "--output-dir", str(tmp_path)])
    assert error.value.code == 2
    assert requests == clients == []


@pytest.mark.parametrize("case", CASES)
def test_cli_failed_expectation_keeps_evidence(case, transport, tmp_path, capsys):
    requests, _ = transport((403, {"error": {"message": "Synthetic permission failure"}}))
    case_id = case.__name__.rsplit(".", 1)[1]
    assert main(["reproduce", case_id, "--variant", "broken", "--live", "--output-dir", str(tmp_path)]) == 1
    assert len(requests) == 1
    assert "did not match" in capsys.readouterr().err
    assert next(tmp_path.glob("*.json")).exists()
