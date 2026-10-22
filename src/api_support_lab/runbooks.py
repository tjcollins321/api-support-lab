"""Read-only local runbooks and observation-backed diagnostic candidates."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CaseId = Literal["invalid_credentials", "tool_schema", "incomplete_output", "timeout"]
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Runbook:
    path: Path
    observations: tuple[tuple[int, str], ...] = ()


# Only reviewed captures establish mappings. The corrected HTTP 200 is not a
# diagnostic entry. Add other runbooks when milestone 4 supplies their material.
# Source: evidence/invalid_credentials/broken-20261022T032250Z.json
REGISTRY: dict[CaseId, Runbook] = {
    "invalid_credentials": Runbook(
        PROJECT_ROOT / "runbooks" / "invalid_credentials.md",
        ((401, "invalid_api_key"),),
    ),
}


def diagnose(status: int, error_code: str | None = None) -> list[CaseId]:
    """Return candidates, never a confirmed cause. Unknown codes stay unmatched."""
    if type(status) is not int or not 100 <= status <= 599:
        raise ValueError("status must be an HTTP integer from 100 to 599")
    if error_code is not None and not isinstance(error_code, str):
        raise ValueError("error_code must be a string or null")
    return [
        case for case, entry in REGISTRY.items()
        if any(s == status and (error_code is None or c == error_code)
               for s, c in entry.observations)
    ]


def get_runbook(case: CaseId) -> str:
    """Retrieve a registered runbook; IDs are never interpreted as paths."""
    if case not in REGISTRY:
        raise ValueError("Unregistered runbook ID")
    return REGISTRY[case].path.read_text(encoding="utf-8")


def list_runbooks() -> dict[CaseId, str]:
    """List registered IDs with the first prose paragraph after each title."""
    result = {}
    for case in REGISTRY:
        paragraphs = get_runbook(case).split("\n\n")
        result[case] = next(
            " ".join(p.split()) for p in paragraphs[1:]
            if p.strip() and not p.lstrip().startswith("#")
        )
    return result
