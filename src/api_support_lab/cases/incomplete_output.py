"""Exercise output-budget exhaustion separately from JSON parsing failure."""

from dataclasses import replace
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from api_support_lab.capture import DEFAULT_OUTPUT_DIR, CaptureResult, Variant
from api_support_lab.cases._shared import completed_text, run_request
from api_support_lab.config import Settings

BROKEN_OUTPUT_TOKENS = 128
WORKLOAD = (
    "Return status READY and exactly 32 items, in index order from 1 through 32. "
    "Each item has its integer index and label item_N, where N is that index."
)


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    index: int
    label: str


class StructuredResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal["READY"]
    items: list[Item]


def validate_output(text: str) -> bool:
    """Check schema and requested content on full output, before excerpt truncation."""
    try:
        parsed = StructuredResult.model_validate_json(text)
    except ValidationError:
        return False
    return parsed.items == [Item(index=i, label=f"item_{i}") for i in range(1, 33)]


def broken(
    settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_output_tokens: int = BROKEN_OUTPUT_TOKENS,
) -> CaptureResult:
    effective = replace(settings, max_output_tokens=max_output_tokens)
    return _run("broken", effective, live=live, output_dir=output_dir)


def fixed(settings: Settings, *, live: bool, output_dir: Path = DEFAULT_OUTPUT_DIR) -> CaptureResult:
    return _run("fixed", settings, live=live, output_dir=output_dir)


def _run(variant: Variant, settings: Settings, *, live: bool, output_dir: Path) -> CaptureResult:
    return run_request(
        "incomplete_output", variant, settings, live=live, output_dir=output_dir,
        input=WORKLOAD, text={"format": {
            "type": "json_schema", "name": "support_sequence", "strict": True,
            "schema": StructuredResult.model_json_schema(),
        }}, validate_output=validate_output,
    )


def matches_expected(result: CaptureResult) -> bool:
    record = result.record
    if record["variant"] == "fixed":
        return completed_text(record) and record["output_valid"] is True
    status = record["http_status"]
    return (
        record["outcome"] == "response" and type(status) is int and 200 <= status < 300
        and record["response_status"] == "incomplete"
        and record["incomplete_reason"] == "max_output_tokens"
        and record["error_code"] is None
    )
