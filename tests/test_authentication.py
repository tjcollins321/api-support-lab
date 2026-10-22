"""Run the real SDK against an in-memory transport and dummy credentials only."""

import json

import httpx2
import openai
import pytest

from api_support_lab.cases import invalid_credentials
from api_support_lab.cli import main
from api_support_lab.config import ConfigurationError, Settings


@pytest.fixture
def mock_api(monkeypatch):
    original_client = openai.OpenAI

    def install(status, body, headers=None):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx2.Response(status, json=body, headers=headers or {})

        def local_client(**kwargs):
            return original_client(
                **kwargs, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
            )

        monkeypatch.setattr(openai, "OpenAI", local_client)
        return requests

    return install


@pytest.fixture
def completed_response():
    return {
        "id": "resp_synthetic", "object": "response", "created_at": 0,
        "model": "synthetic-model", "status": "completed",
        "output": [{
            "id": "msg_synthetic", "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": "READY", "annotations": []}],
        }],
        "usage": {
            "input_tokens": 8, "output_tokens": 2, "total_tokens": 10,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 0},
        },
    }


def test_broken_auth_uses_only_invalid_key_and_records_expected_error(mock_api, tmp_path, monkeypatch):
    def forbidden():
        pytest.fail("Broken authentication must not look up the environment key")

    monkeypatch.setattr("api_support_lab.sdk.require_api_key", forbidden)
    calls = mock_api(401, {"error": {
        "message": f"Synthetic invalid credential {invalid_credentials.INVALID_API_KEY}",
        "type": "invalid_request_error", "code": "synthetic_invalid_key", "param": None,
    }}, {"x-request-id": "req_synthetic_auth"})
    result = invalid_credentials.broken(Settings(), live=True, output_dir=tmp_path)
    assert len(calls) == 1
    assert calls[0].headers["authorization"] == f"Bearer {invalid_credentials.INVALID_API_KEY}"
    assert invalid_credentials.matches_expected(result)
    assert result.record["error_code"] == "synthetic_invalid_key"
    assert result.record["request_id"] == "req_synthetic_auth"
    assert invalid_credentials.INVALID_API_KEY not in result.path.read_text()


def test_fixed_auth_uses_configured_key_and_bounded_workload(mock_api, completed_response, tmp_path, monkeypatch):
    key = "dummy-configured-test-credential"
    monkeypatch.setenv("OPENAI_API_KEY", key)
    calls = mock_api(200, completed_response, {"x-request-id": "req_synthetic_success"})
    settings = Settings(model="synthetic-model")
    result = invalid_credentials.fixed(settings, live=True, output_dir=tmp_path)
    assert len(calls) == 1
    assert calls[0].method == "POST"
    assert str(calls[0].url) == "https://api.openai.com/v1/responses"
    assert calls[0].headers["authorization"] == f"Bearer {key}"
    assert json.loads(calls[0].content) == {
        "model": "synthetic-model", "input": invalid_credentials.WORKLOAD,
        "reasoning": {"effort": "low"}, "max_output_tokens": 2048, "store": False,
    }
    assert invalid_credentials.matches_expected(result)
    assert result.record["usage"]["total_tokens"] == 10
    assert key not in result.path.read_text()
    assert invalid_credentials.WORKLOAD not in result.path.read_text()


@pytest.mark.parametrize("variant", [invalid_credentials.broken, invalid_credentials.fixed])
def test_case_functions_require_live_before_constructing_clients(variant, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("No client may be constructed before live opt-in")

    monkeypatch.setattr(invalid_credentials, "create_client", forbidden)
    with pytest.raises(ConfigurationError, match="--live"):
        variant(Settings(), live=False, output_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_fixed_auth_missing_key_fails_before_request(mock_api, completed_response, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    calls = mock_api(200, completed_response)
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        invalid_credentials.fixed(Settings(), live=True, output_dir=tmp_path)
    assert calls == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_both_variants_send_the_same_request_body(variant, mock_api, completed_response, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-test-credential")
    calls = mock_api(200, completed_response)
    getattr(invalid_credentials, variant)(Settings(), live=True, output_dir=tmp_path)
    body = json.loads(calls[0].content)
    assert body["input"] == invalid_credentials.WORKLOAD
    assert body["max_output_tokens"] == 2048
    assert body["reasoning"] == {"effort": "low"}
    assert body["store"] is False


@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_unrelated_sdk_errors_are_saved_not_counted_and_not_retried(variant, mock_api, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-test-credential")
    calls = mock_api(500, {"error": {"message": "Synthetic unrelated server failure", "code": "synthetic_server_error"}})
    result = getattr(invalid_credentials, variant)(Settings(), live=True, output_dir=tmp_path)
    assert len(calls) == 1
    assert result.record["http_status"] == 500
    assert not invalid_credentials.matches_expected(result)


@pytest.mark.parametrize("body", [
    {"status": "incomplete", "output": [], "incomplete_details": {"reason": "max_output_tokens"}},
    {"status": "completed", "output": []},
    {"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "Synthetic refusal"}]}]},
])
def test_http_success_alone_does_not_verify_fixed_behavior(body, mock_api, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-test-credential")
    mock_api(200, body)
    result = invalid_credentials.fixed(Settings(), live=True, output_dir=tmp_path)
    assert result.record["http_status"] == 200
    assert not invalid_credentials.matches_expected(result)


@pytest.mark.parametrize("variant", ["broken", "fixed"])
def test_cli_runs_authentication_with_in_memory_transport(variant, mock_api, completed_response, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-cli-credential")
    if variant == "broken":
        mock_api(401, {"error": {"message": "Synthetic invalid credential", "code": "synthetic_auth_code"}})
    else:
        mock_api(200, completed_response)
    assert main(["reproduce", "invalid_credentials", "--variant", variant, "--live", "--output-dir", str(tmp_path)]) == 0
    output = capsys.readouterr()
    assert "Saved evidence:" in output.out
    assert "Pair verification requires both variants and review" in output.out
    assert "dummy-cli-credential" not in output.out + output.err
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_cli_returns_failure_and_retains_unrelated_error(mock_api, tmp_path, capsys):
    calls = mock_api(403, {"error": {"message": "Synthetic permission denial"}})
    assert main(["reproduce", "invalid_credentials", "--variant", "broken", "--live", "--output-dir", str(tmp_path)]) == 1
    assert len(calls) == 1
    assert "did not match" in capsys.readouterr().err
    assert json.loads(next(tmp_path.glob("*.json")).read_text())["http_status"] == 403


def test_cli_missing_key_error_does_not_execute_request(mock_api, completed_response, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    calls = mock_api(200, completed_response)
    with pytest.raises(SystemExit) as error:
        main(["reproduce", "invalid_credentials", "--variant", "fixed", "--live", "--output-dir", str(tmp_path)])
    assert error.value.code == 2
    assert calls == []


def test_cli_write_failure_explains_that_request_may_have_run(mock_api, tmp_path, capsys):
    output = tmp_path / "existing-file"
    output.write_text("existing")
    calls = mock_api(401, {"error": {"message": "Synthetic invalid credential"}})
    assert main(["reproduce", "invalid_credentials", "--variant", "broken", "--live", "--output-dir", str(output)]) == 1
    assert len(calls) == 1
    assert "request may already have run" in capsys.readouterr().err
