"""One bounded Responses request with either invalid or environment credentials."""

from pathlib import Path

from api_support_lab.capture import DEFAULT_OUTPUT_DIR, CaptureResult, Variant, capture
from api_support_lab.config import Settings, require_live
from api_support_lab.sdk import create_client

INVALID_API_KEY = "sk-obviously-invalid-api-support-lab"
WORKLOAD = "Reply with the single word READY."


def broken(
    settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> CaptureResult:
    """Use an intentionally invalid credential without loading the environment key."""
    return _run("broken", settings, live=live, output_dir=output_dir)


def fixed(
    settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> CaptureResult:
    """Use OPENAI_API_KEY; completion remains subject to live verification."""
    return _run("fixed", settings, live=live, output_dir=output_dir)


def _run(variant: Variant, settings: Settings, *, live: bool, output_dir: Path) -> CaptureResult:
    require_live(live)
    key = INVALID_API_KEY if variant == "broken" else None
    with create_client(settings, live=live, api_key=key) as client:
        return capture(
            "invalid_credentials", variant,
            lambda: client.responses.with_raw_response.create(
                model=settings.model,
                input=WORKLOAD,
                reasoning={"effort": settings.reasoning_effort},
                max_output_tokens=settings.max_output_tokens,
                store=False,
            ),
            settings=settings,
            secrets=(client.api_key,),
            output_dir=output_dir,
        )


def matches_expected(result: CaptureResult) -> bool:
    """Check this attempt's behavior; this does not verify a broken/fixed pair."""
    record = result.record
    if record["variant"] == "broken":
        return (
            record["outcome"] == "api_error"
            and record["exception_type"] == "AuthenticationError"
            and record["http_status"] == 401
        )
    status = record["http_status"]
    return (
        record["outcome"] == "response"
        and isinstance(status, int) and 200 <= status < 300
        and record["response_status"] == "completed"
        and bool((record["output_excerpt"] or "").strip())
    )
