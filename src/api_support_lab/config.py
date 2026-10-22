"""Non-secret settings; credentials are read only at the live boundary."""

import math
import os
from dataclasses import dataclass, field
from typing import Literal


class ConfigurationError(ValueError):
    """An actionable configuration error whose message contains no secrets."""


@dataclass(frozen=True)
class Settings:
    model: str = "gpt-6.1-sol"
    timeout_seconds: float = 60.0
    max_output_tokens: int = 2_048
    agent_max_output_tokens: int = 4_096
    max_turns: int = 8
    max_retries: int = field(default=0, init=False)
    reasoning_effort: Literal["low"] = field(default="low", init=False)

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ConfigurationError("API_SUPPORT_LAB_MODEL must not be blank.")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ConfigurationError("timeout_seconds must be positive and finite.")
        for name in ("max_output_tokens", "agent_max_output_tokens", "max_turns"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ConfigurationError(f"{name} must be a positive integer.")


def load_settings() -> Settings:
    """Read the model override without looking up or retaining credentials."""
    return Settings(model=os.environ.get("API_SUPPORT_LAB_MODEL", Settings.model).strip())


def require_live(live: bool) -> None:
    if not live:
        raise ConfigurationError("This operation requires explicit --live opt-in.")


def require_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ConfigurationError("Set OPENAI_API_KEY in the environment for live operations.")
    return key
