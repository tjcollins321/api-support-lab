"""Compare an invalid function parameter schema with its supported correction."""

from pathlib import Path

from api_support_lab.capture import DEFAULT_OUTPUT_DIR, CaptureResult, Variant
from api_support_lab.cases._shared import completed_text, run_request
from api_support_lab.config import Settings

WORKLOAD = "Reply with the single word READY."


def broken(settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR) -> CaptureResult:
    return _run("broken", settings, live=live, output_dir=output_dir)


def fixed(settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR) -> CaptureResult:
    return _run("fixed", settings, live=live, output_dir=output_dir)


def _run(variant: Variant, settings: Settings, *, live: bool, output_dir: Path) -> CaptureResult:
    tool = {
        "type": "function", "name": "support_label", "strict": True,
        "parameters": {
            "type": "object", "additionalProperties": False,
            "properties": {"label": {"type": "not_a_json_schema_type" if variant == "broken" else "string"}},
            "required": ["label"],
        },
    }
    return run_request(
        "tool_schema", variant, settings, live=live, output_dir=output_dir,
        input=WORKLOAD, tools=[tool], tool_choice="none",
    )


def matches_expected(result: CaptureResult) -> bool:
    """Check a tools-related rejection; one reviewed live pair supports this case."""
    record = result.record
    if record["variant"] == "fixed":
        return completed_text(record)
    param = record["error_param"] or ""
    return (
        record["outcome"] == "api_error" and record["http_status"] == 400
        and record["exception_type"] == "BadRequestError"
        and (param == "tools" or param.startswith(("tools[", "tools.")))
    )
