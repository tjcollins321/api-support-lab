"""Authored SDK fixtures exercise local handling, never observed API behavior."""

import json
from datetime import datetime
from types import SimpleNamespace

import httpx2
import pytest
from openai import (
    APIConnectionError, APIError, APIResponseValidationError, APITimeoutError,
    AuthenticationError, OpenAIError,
)

from api_support_lab.capture import OUTPUT_EXCERPT_LIMIT, capture, redact
from api_support_lab.config import Settings


def raw_response(body, *, status=200, headers=None):
    return SimpleNamespace(status_code=status, headers=headers or {}, parse=lambda: body)


def text_response(text="READY", **fields):
    return {
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
        **fields,
    }


def test_success_allowlists_fields_and_writes_roundtrippable_json(tmp_path, monkeypatch):
    times = iter([10.0, 10.125])
    monkeypatch.setattr("api_support_lab.capture.perf_counter", lambda: next(times))
    response = raw_response(
        text_response(
            "Synthetic output café",
            instructions="DO NOT SAVE THE PROMPT",
            metadata={"secret": "DO NOT SAVE METADATA"},
            usage={
                "input_tokens": 11, "output_tokens": 3, "total_tokens": 14,
                "input_tokens_details": {"cached_tokens": 0, "private": "DO NOT SAVE"},
                "output_tokens_details": {"reasoning_tokens": 1},
                "arbitrary": "DO NOT SAVE",
            },
        ),
        headers={
            "X-Request-Id": "req_synthetic", "Retry-After": "2",
            "X-RateLimit-Remaining-Requests": "8", "Authorization": "DO NOT SAVE AUTH",
            "Set-Cookie": "DO NOT SAVE COOKIE", "x-arbitrary": "DO NOT SAVE HEADER",
        },
    )
    result = capture("invalid_credentials", "fixed", lambda: response, settings=Settings(), output_dir=tmp_path)
    record = result.record
    assert json.loads(result.path.read_text()) == record
    assert datetime.fromisoformat(record["captured_at"]).utcoffset().total_seconds() == 0
    assert record["sdk_version"]
    assert record["elapsed_ms"] == 125.0
    assert record["outcome"] == "response"
    assert record["response_status"] == "completed"
    assert record["output_excerpt"] == "Synthetic output café"
    assert record["http_status"] == 200
    assert record["request_id"] == "req_synthetic"
    assert record["headers"] == {
        "x-request-id": "req_synthetic", "retry-after": "2", "x-ratelimit-remaining-requests": "8",
    }
    assert record["usage"] == {
        "input_tokens": 11, "output_tokens": 3, "total_tokens": 14,
        "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 1},
    }
    assert record["settings"] == {
        "max_output_tokens": 2048, "reasoning_effort": "low", "timeout_seconds": 60.0, "max_retries": 0,
    }
    assert "DO NOT SAVE" not in result.path.read_text()


@pytest.mark.parametrize("body", [{}, {"output": None, "usage": {}, "incomplete_details": None}])
def test_missing_response_fields_stay_null(tmp_path, body):
    result = capture("timeout", "fixed", lambda: raw_response(body, status=None), settings=Settings(), output_dir=tmp_path)
    for name in (
        "http_status", "request_id", "exception_type", "error_type", "error_code",
        "error_param", "message", "response_status", "incomplete_reason", "output_excerpt", "usage",
    ):
        assert result.record[name] is None
    assert result.record["headers"] == {}


def test_incomplete_response_is_not_a_transport_failure(tmp_path):
    response = raw_response({
        "status": "incomplete", "output": [], "incomplete_details": {"reason": "max_output_tokens"},
    })
    result = capture("incomplete_output", "broken", lambda: response, settings=Settings(max_output_tokens=128), output_dir=tmp_path)
    assert result.record["outcome"] == "response"
    assert result.record["http_status"] == 200
    assert result.record["response_status"] == "incomplete"
    assert result.record["incomplete_reason"] == "max_output_tokens"
    assert result.record["output_excerpt"] is None


def test_refusal_is_distinct_from_completion_and_incomplete_output(tmp_path):
    response = raw_response({
        "status": "completed", "output": [{"type": "message", "content": [
            {"type": "refusal", "refusal": "Synthetic refusal."},
        ]}],
    })
    result = capture("invalid_credentials", "fixed", lambda: response, settings=Settings(), output_dir=tmp_path)
    assert result.record["outcome"] == "refusal"
    assert result.record["message"] == "Synthetic refusal."
    assert result.record["output_excerpt"] is None


def test_response_level_error_is_preserved_without_dumping_response(tmp_path):
    response = raw_response({"status": "failed", "error": {"code": "synthetic_error", "message": "Synthetic failure"}})
    result = capture("invalid_credentials", "fixed", lambda: response, settings=Settings(), output_dir=tmp_path)
    assert result.record["response_status"] == "failed"
    assert result.record["error_code"] == "synthetic_error"
    assert result.record["message"] == "Synthetic failure"


def test_authentication_error_is_sanitized_and_body_is_allowlisted(tmp_path):
    secret = "dummy-credential-that-does-not-start-with-sk"
    body = {"message": f"Synthetic invalid key: {secret}", "code": "synthetic_auth_code", "type": "invalid_request_error", "param": "api_key"}
    request = httpx2.Request("POST", "https://example.invalid/v1/responses", headers={"Authorization": f"Bearer {secret}"})
    response = httpx2.Response(401, request=request, headers={"x-request-id": "req_auth_synthetic", "set-cookie": "DO NOT SAVE"})
    error = AuthenticationError("SDK string including DO NOT SAVE FULL BODY", response=response, body={**body, "private": "DO NOT SAVE"})

    def failing_call():
        raise error

    result = capture("invalid_credentials", "broken", failing_call, settings=Settings(), secrets=(secret,), output_dir=tmp_path)
    record = result.record
    assert record["outcome"] == "api_error"
    assert record["exception_type"] == "AuthenticationError"
    assert record["http_status"] == 401
    assert record["request_id"] == "req_auth_synthetic"
    assert record["error_code"] == "synthetic_auth_code"
    assert record["error_param"] == "api_key"
    assert record["error_type"] == "invalid_request_error"
    assert record["message"] == "Synthetic invalid key: [REDACTED]"
    assert secret not in result.path.read_text()
    assert "DO NOT SAVE" not in result.path.read_text()


def test_missing_error_message_does_not_fall_back_to_a_dump_of_the_body(tmp_path):
    response = httpx2.Response(401, request=httpx2.Request("POST", "https://example.invalid"))
    body = {"error": {"code": "synthetic_code", "private": "DO NOT SAVE BODY"}}
    error = AuthenticationError(f"Error code: 401 - {body}", response=response, body=body)

    def failing_call():
        raise error

    result = capture("invalid_credentials", "broken", failing_call, settings=Settings(), output_dir=tmp_path)
    assert result.record["message"] is None
    assert result.record["error_code"] == "synthetic_code"
    assert "DO NOT SAVE" not in result.path.read_text()


@pytest.mark.parametrize("error_factory,outcome", [
    (lambda req: APITimeoutError(request=req), "client_timeout"),
    (lambda req: APIConnectionError(request=req), "connection_error"),
    (lambda req: APIError("Synthetic SDK error", req, body=None), "sdk_error"),
    (lambda req: OpenAIError("Synthetic root SDK error"), "sdk_error"),
])
def test_sdk_errors_without_a_response_do_not_invent_transport_fields(tmp_path, error_factory, outcome):
    error = error_factory(httpx2.Request("POST", "https://example.invalid"))

    def failing_call():
        raise error

    result = capture("timeout", "broken", failing_call, settings=Settings(), output_dir=tmp_path)
    assert result.record["outcome"] == outcome
    assert result.record["exception_type"] == type(error).__name__
    assert result.record["message"]
    assert result.record["http_status"] is None
    assert result.record["request_id"] is None
    assert result.record["headers"] == {}
    assert result.record["usage"] is None


def test_sdk_parse_error_retains_the_http_response(tmp_path):
    response = httpx2.Response(200, request=httpx2.Request("POST", "https://example.invalid"), headers={"x-request-id": "req_parse_synthetic"})

    def parse():
        raise APIResponseValidationError(response, body={"private": "DO NOT SAVE"})

    raw = SimpleNamespace(status_code=200, headers=response.headers, parse=parse)
    result = capture("invalid_credentials", "fixed", lambda: raw, settings=Settings(), output_dir=tmp_path)
    assert result.record["outcome"] == "sdk_error"
    assert result.record["http_status"] == 200
    assert result.record["request_id"] == "req_parse_synthetic"
    assert "DO NOT SAVE" not in result.path.read_text()


def test_redaction_precedes_truncation_and_covers_all_saved_text(tmp_path):
    secret = "dummy-credential-long-enough-to-cross-the-excerpt-boundary"
    response = raw_response(text_response("x" * 995 + secret + " sk-proj-another-credential"), headers={
        "x-request-id": secret, "x-ratelimit-test": f"Bearer {secret}", "Authorization": secret,
    })
    result = capture("invalid_credentials", "fixed", lambda: response, settings=Settings(model=secret), secrets=(secret,), output_dir=tmp_path)
    assert len(result.record["output_excerpt"]) == OUTPUT_EXCERPT_LIMIT
    assert "dummy" not in result.record["output_excerpt"]
    assert result.record["request_id"] == "[REDACTED]"
    assert result.record["model"] == "[REDACTED]"
    assert result.record["headers"]["x-ratelimit-test"] == "Bearer [REDACTED]"
    assert secret not in result.path.read_text()


def test_recognizable_credentials_and_bearer_tokens_are_redacted():
    assert redact("key sk-proj-EXAMPLE_123, Bearer opaque.credential==") == "key [REDACTED], Bearer [REDACTED]"
    assert redact("long-token and long", ("long", "long-token")) == "[REDACTED] and [REDACTED]"


def test_each_attempt_is_retained_without_overwriting(tmp_path):
    first = capture("invalid_credentials", "fixed", lambda: raw_response(text_response("first")), settings=Settings(), output_dir=tmp_path)
    second = capture("invalid_credentials", "fixed", lambda: raw_response(text_response("second")), settings=Settings(), output_dir=tmp_path)
    assert first.path != second.path
    assert len(list(tmp_path.glob("invalid_credentials-fixed-*.json"))) == 2
    assert json.loads(first.path.read_text())["output_excerpt"] == "first"
    assert json.loads(second.path.read_text())["output_excerpt"] == "second"


def test_programming_errors_propagate_without_evidence(tmp_path):
    def failing_call():
        raise ValueError("Synthetic programming mistake")

    with pytest.raises(ValueError, match="programming mistake"):
        capture("invalid_credentials", "fixed", failing_call, settings=Settings(), output_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("case,variant", [("../escape", "fixed"), ("invalid_credentials", "other")])
def test_invalid_capture_identifiers_fail_before_execution(tmp_path, case, variant):
    def forbidden():
        pytest.fail("An invalid capture must not run the callable")

    with pytest.raises(ValueError, match="Invalid capture"):
        capture(case, variant, forbidden, settings=Settings(), output_dir=tmp_path)


def test_filesystem_failure_is_not_relabelled_as_an_api_error(tmp_path):
    output = tmp_path / "not-a-directory"
    output.write_text("existing content")
    with pytest.raises(FileExistsError):
        capture("invalid_credentials", "fixed", lambda: raw_response(text_response()), settings=Settings(), output_dir=output)
    assert output.read_text() == "existing content"
