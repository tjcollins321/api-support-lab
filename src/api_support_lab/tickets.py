"""Safe ticket loading and the explicit model-input allowlist."""

import hashlib
import json
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from api_support_lab.runbooks import PROJECT_ROOT

TICKET_DIR = PROJECT_ROOT / "triage" / "tickets"


class Ticket(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(pattern=r"^T-\d{3}$")
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    pasted_error: str | None
    organization: str | None = None
    channel: str | None = None
    provenance: dict[str, JsonValue] = Field(default_factory=dict)

    def model_input(self) -> str:
        return json.dumps(self.model_dump(include={"subject", "body", "pasted_error"}),
                          ensure_ascii=False)

    def content_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True).encode()).hexdigest()


def load_ticket(path: Path) -> Ticket:
    return Ticket.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_tickets() -> list[Ticket]:
    tickets = [load_ticket(path) for path in sorted(TICKET_DIR.glob("*.yaml"))]
    if not tickets or len({ticket.id for ticket in tickets}) != len(tickets):
        raise ValueError("Ticket set must be nonempty with unique IDs")
    return tickets


def diagnostic_values(ticket: Ticket) -> tuple[set[int], set[str]]:
    """Conservative explicit field extraction, not a diagnosis or text classifier.

    Recognize HTTP NNN, status/http_status: NNN and code/error_code: value,
    including quoted JSON fields. Unrecognized prose requires clarification.
    """
    text = "\n".join((ticket.subject, ticket.body, ticket.pasted_error or ""))
    statuses = {
        int(value) for value in re.findall(
            r'\b(?:HTTP\s+|(?:http_status|status)["\x27]?\s*[:=]\s*)([1-5]\d{2})\b',
            text, flags=re.IGNORECASE,
        )
    }
    codes = set(re.findall(
        r'\b(?:error_code|code)["\x27]?\s*[:=]\s*["\x27]?([A-Za-z][A-Za-z0-9_.-]*)',
        text,
    ))
    return statuses, codes


def diagnosis_is_grounded(arguments: dict, ticket: Ticket) -> bool:
    statuses, codes = diagnostic_values(ticket)
    status, code = arguments.get("status"), arguments.get("error_code")
    return (set(arguments) <= {"status", "error_code"}
            and type(status) is int and status in statuses
            and (code is None or (isinstance(code, str) and code in codes)))
