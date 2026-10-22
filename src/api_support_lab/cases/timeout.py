"""Compare an impractically short client timeout with a bounded correction."""

from dataclasses import replace
from pathlib import Path

from api_support_lab.capture import DEFAULT_OUTPUT_DIR, CaptureResult, Variant
from api_support_lab.cases._shared import completed_text, run_request
from api_support_lab.config import Settings

BROKEN_TIMEOUT_SECONDS = 0.5
WORKLOAD = "Reply with the single word READY."


def broken(
    settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR,
    timeout_seconds: float = BROKEN_TIMEOUT_SECONDS,
) -> CaptureResult:
    effective = replace(settings, timeout_seconds=timeout_seconds)
    return _run("broken", effective, live=live, output_dir=output_dir)


def fixed(settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR) -> CaptureResult:
    return _run("fixed", settings, live=live, output_dir=output_dir)


def _run(variant: Variant, settings: Settings, *, live: bool, output_dir: Path) -> CaptureResult:
    return run_request("timeout", variant, settings, live=live, output_dir=output_dir, input=WORKLOAD)


def matches_expected(result: CaptureResult) -> bool:
    record = result.record
    if record["variant"] == "fixed":
        return completed_text(record)
    return record["outcome"] == "client_timeout" and record["exception_type"] == "APITimeoutError"
