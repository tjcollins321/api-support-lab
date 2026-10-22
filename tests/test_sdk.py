import inspect
from unittest.mock import Mock

import pytest

from api_support_lab import config
from api_support_lab.config import ConfigurationError, Settings
from api_support_lab.sdk import configure_agents, create_client


def test_client_refuses_before_reading_credentials(monkeypatch):
    def forbidden():
        pytest.fail("Credentials were read before live opt-in")

    monkeypatch.setattr("api_support_lab.sdk.require_api_key", forbidden)
    with pytest.raises(ConfigurationError, match="--live"):
        create_client(Settings(), live=False)


def test_client_requires_key_after_opt_in(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="Set OPENAI_API_KEY"):
        create_client(Settings(), live=True)


def test_local_client_configuration_without_a_request(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key-not-a-real-credential")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid")
    settings = Settings(timeout_seconds=12.0)
    # Client construction is local; no method that sends requests is invoked.
    with create_client(settings, live=True) as client:
        assert client.max_retries == 0
        assert client.timeout == 12.0
        assert str(client.base_url) == "https://api.openai.com/v1/"
        assert callable(client.responses.with_raw_response.create)


def test_agents_interfaces_and_structured_output_without_running(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = config.load_settings()
    model_settings = configure_agents(settings)
    from agents import Agent, Runner, function_tool
    from pydantic import BaseModel
    import yaml

    class ExampleResult(BaseModel):
        summary: str

    agent = Agent(
        name="Offline compatibility check",
        model=settings.model,
        model_settings=model_settings,
        output_type=ExampleResult,
    )
    assert agent.output_type is ExampleResult
    assert ExampleResult.model_json_schema()["required"] == ["summary"]
    assert inspect.iscoroutinefunction(Runner.run)
    assert callable(function_tool)
    assert model_settings.reasoning.effort == "low"
    assert model_settings.max_tokens == 4_096
    assert yaml.safe_load("id: synthetic-example") == {"id": "synthetic-example"}


def test_tracing_is_disabled_even_when_environment_enables_it(monkeypatch):
    monkeypatch.setenv("OPENAI_AGENTS_DISABLE_TRACING", "0")
    configure_agents(Settings())
    from agents import TracingProcessor, set_trace_processors, trace

    recorder = Mock(spec=TracingProcessor)
    set_trace_processors([recorder])
    try:
        with trace("offline tracing check"):
            pass
        recorder.on_trace_start.assert_not_called()
        recorder.on_trace_end.assert_not_called()
    finally:
        set_trace_processors([])
