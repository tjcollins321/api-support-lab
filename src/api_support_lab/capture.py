"""Execute one request and save only allowlisted, sanitized diagnostic fields."""

import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAIError

from api_support_lab.config import Settings

Variant = Literal["broken", "fixed"]
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "evidence"
OUTPUT_EXCERPT_LIMIT = 1_000
_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)


@dataclass(frozen=True)
class CaptureResult:
    record: dict[str, Any]
    path: Path


def redact(text: str, secrets: Sequence[str] = ()) -> str:
    """Remove explicit credentials and recognizable key/bearer strings."""
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = _BEARER_PATTERN.sub("Bearer [REDACTED]", text)
    return _KEY_PATTERN.sub("[REDACTED]", text)


def _sanitize(value: Any, secrets: Sequence[str]) -> Any:
    if isinstance(value, str):
        return redact(value, secrets)
    if isinstance(value, dict):
        return {redact(key, secrets): _sanitize(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item, secrets) for item in value]
    return value


def _field(value: Any, name: str) -> Any:
    return value.get(name) if isinstance(value, Mapping) else getattr(value, name, None)


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _transport_fields(response: Any) -> dict[str, Any]:
    headers = {}
    for name, value in (_field(response, "headers") or {}).items():
        name = name.lower()
        if isinstance(value, str) and (
            name in ("x-request-id", "retry-after") or name.startswith("x-ratelimit-")
        ):
            headers[name] = value
    status = _field(response, "status_code")
    return {
        "http_status": status if type(status) is int else None,
        "request_id": headers.get("x-request-id"),
        "headers": headers,
    }


def _usage_fields(usage: Any) -> dict[str, Any] | None:
    if usage is None:
        return None
    result = {}
    for name in ("input_tokens", "output_tokens", "total_tokens"):
        value = _field(usage, name)
        if type(value) is int and value >= 0:
            result[name] = value
    for name, detail in (
        ("input_tokens_details", "cached_tokens"),
        ("output_tokens_details", "reasoning_tokens"),
    ):
        value = _field(_field(usage, name), detail)
        if type(value) is int and value >= 0:
            result[name] = {detail: value}
    return result or None


def _response_fields(response: Any) -> dict[str, Any]:
    # Walk only text output items; do not dump prompts, tools, or response objects.
    parts = []
    refusals = []
    refused = False
    for item in _field(response, "output") or []:
        if _field(item, "type") == "message":
            for content in _field(item, "content") or []:
                text = _text(_field(content, "text"))
                if _field(content, "type") == "output_text" and text is not None:
                    parts.append(text)
                elif _field(content, "type") == "refusal":
                    refused = True
                    refusal = _text(_field(content, "refusal"))
                    if refusal is not None:
                        refusals.append(refusal)
    error = _field(response, "error")
    return {
        "outcome": "refusal" if refused else "response",
        "response_status": _text(_field(response, "status")),
        "incomplete_reason": _text(_field(_field(response, "incomplete_details"), "reason")),
        "output_excerpt": "".join(parts) if parts else None,
        "usage": _usage_fields(_field(response, "usage")),
        "error_code": _text(_field(error, "code")),
        "message": _text(_field(error, "message")) or ("".join(refusals) if refusals else None),
    }


def _error_fields(error: OpenAIError, outcome: str) -> dict[str, Any]:
    body = _field(error, "body")
    if isinstance(body, Mapping) and isinstance(body.get("error"), Mapping):
        body = body["error"]
    # SDK strings may embed the entire server body. If a body exists, select its
    # message only; a missing message must not expose unrelated body fields.
    if body is not None:
        message = _text(_field(body, "message"))
    else:
        message = _text(_field(error, "message")) or (_text(error.args[0]) if error.args else None)
    fields = {
        "outcome": outcome,
        "exception_type": type(error).__name__,
        "error_type": _text(_field(error, "type")) or _text(_field(body, "type")),
        "error_code": _text(_field(error, "code")) or _text(_field(body, "code")),
        "error_param": _text(_field(error, "param")) or _text(_field(body, "param")),
        "message": message,
    }
    response = _field(error, "response")
    if response is not None:
        fields.update(_transport_fields(response))
    return fields


def capture(
    case: str,
    variant: Variant,
    call: Callable[[], Any],
    *,
    settings: Settings,
    secrets: Sequence[str] = (),
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    validate_output: Callable[[str], bool] | None = None,
) -> CaptureResult:
    """Capture a raw SDK response or SDK exception; let programming errors propagate.

    The callable returns the result of a ``with_raw_response`` request. This
    function never reads credentials or constructs a client. Test callers must
    use temporary output directories and must not label fixtures as live evidence.
    """
    if not re.fullmatch(r"[a-z][a-z0-9_]*", case) or variant not in ("broken", "fixed"):
        raise ValueError("Invalid capture case or variant.")
    captured_at = datetime.now(UTC)
    record = {
        "case": case,
        "variant": variant,
        "captured_at": captured_at.isoformat(),
        "model": settings.model,
        "sdk_version": version("openai"),
        "elapsed_ms": None,
        "outcome": "response",
        "exception_type": None,
        "http_status": None,
        "error_type": None,
        "error_code": None,
        "error_param": None,
        "message": None,
        "request_id": None,
        "headers": {},
        "response_status": None,
        "incomplete_reason": None,
        "output_excerpt": None,
        "output_valid": None,
        "usage": None,
        "settings": {
            "max_output_tokens": settings.max_output_tokens,
            "reasoning_effort": settings.reasoning_effort,
            "timeout_seconds": settings.timeout_seconds,
            "max_retries": settings.max_retries,
        },
    }
    started = perf_counter()
    try:
        raw = call()
        record.update(_transport_fields(raw))
        record.update(_response_fields(raw.parse()))
    except APITimeoutError as error:
        record.update(_error_fields(error, "client_timeout"))
    except APIConnectionError as error:
        record.update(_error_fields(error, "connection_error"))
    except APIStatusError as error:
        record.update(_error_fields(error, "api_error"))
    except OpenAIError as error:
        record.update(_error_fields(error, "sdk_error"))
    # Validate the complete text, never a saved/truncated excerpt. Incomplete,
    # refused, or failed responses do not enter a JSON parser. Validators return
    # a boolean only; unexpected programming errors still propagate.
    if (
        validate_output is not None and record["outcome"] == "response"
        and record["response_status"] == "completed"
        and record["incomplete_reason"] is None and record["error_code"] is None
        and type(record["http_status"]) is int and 200 <= record["http_status"] < 300
    ):
        record["output_valid"] = validate_output(record["output_excerpt"] or "")
    record["elapsed_ms"] = round((perf_counter() - started) * 1_000, 3)
    record = _sanitize(record, secrets)
    # Redact before truncation, so a credential cannot survive as a cut-off prefix.
    if record["output_excerpt"] is not None:
        record["output_excerpt"] = record["output_excerpt"][:OUTPUT_EXCERPT_LIMIT]

    serialized = json.dumps(record, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{case}-{variant}-{captured_at:%Y%m%dT%H%M%S%fZ}-{uuid4().hex}.json"
    path = output_dir / filename
    with path.open("x", encoding="utf-8") as artifact:
        artifact.write(serialized)
    return CaptureResult(record=record, path=path)
