"""Small SDK setup helpers. Importing this module creates no clients."""

import os
from typing import TYPE_CHECKING

from api_support_lab.config import Settings, require_api_key, require_live

if TYPE_CHECKING:
    from agents import ModelSettings
    from openai import OpenAI


def create_client(settings: Settings, *, live: bool, api_key: str | None = None) -> OpenAI:
    """Construct the reproduction client only after explicit live authorization."""
    require_live(live)
    key = require_api_key() if api_key is None else api_key
    from openai import OpenAI

    return OpenAI(
        api_key=key,
        base_url="https://api.openai.com/v1",
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
    )


def configure_agents(settings: Settings) -> ModelSettings:
    """Select Responses, disable remote tracing, and prepare local model settings.

    This does not construct a client, create an agent, or run the model.
    """
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    from agents import ModelSettings, set_default_openai_api, set_tracing_disabled
    from openai.types.shared import Reasoning

    set_tracing_disabled(True)
    set_default_openai_api("responses")
    return ModelSettings(
        max_tokens=settings.agent_max_output_tokens,
        reasoning=Reasoning(effort=settings.reasoning_effort),
    )
