"""One request through the shared capture boundary; no tool execution or retries."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from api_support_lab.capture import CaptureResult, Variant, capture
from api_support_lab.config import Settings, require_live
from api_support_lab.sdk import create_client


def run_request(
    case: str, variant: Variant, settings: Settings, *, live: bool,
    output_dir: Path, validate_output: Callable[[str], bool] | None = None,
    **request_options: Any,
) -> CaptureResult:
    require_live(live)
    with create_client(settings, live=live) as client:
        return capture(
            case, variant,
            lambda: client.responses.with_raw_response.create(
                model=settings.model,
                reasoning={"effort": settings.reasoning_effort},
                max_output_tokens=settings.max_output_tokens,
                store=False,
                **request_options,
            ),
            settings=settings, secrets=(client.api_key,), output_dir=output_dir,
            validate_output=validate_output,
        )


def completed_text(record: dict[str, Any]) -> bool:
    status = record["http_status"]
    return (
        record["outcome"] == "response"
        and type(status) is int and 200 <= status < 300
        and record["response_status"] == "completed"
        and record["incomplete_reason"] is None
        and record["error_code"] is None
        and bool((record["output_excerpt"] or "").strip())
    )
