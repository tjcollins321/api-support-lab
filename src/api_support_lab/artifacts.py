"""Sanitize local run/report records and write unique artifacts."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from api_support_lab.capture import redact
from api_support_lab.runbooks import PROJECT_ROOT

DEFAULT_TRIAGE_DIR = PROJECT_ROOT / "artifacts" / "triage"
DEFAULT_EVALUATION_DIR = PROJECT_ROOT / "artifacts" / "evaluation"


def sanitize(value, secrets=()):
    if isinstance(value, str):
        return redact(value, secrets)
    if isinstance(value, dict):
        return {redact(str(k), secrets): sanitize(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v, secrets) for v in value]
    return value


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def save_record(record: dict, output_dir: Path, prefix: str, *, secrets=()) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{prefix}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex}.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(sanitize(record, secrets), stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    return path
