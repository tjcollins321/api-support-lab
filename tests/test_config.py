import math

import pytest

from api_support_lab.config import ConfigurationError, Settings, load_settings, require_api_key


def test_default_settings_need_no_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("API_SUPPORT_LAB_MODEL", raising=False)
    settings = load_settings()
    assert settings.model == "gpt-6.1-sol"
    assert settings.reasoning_effort == "low"
    assert settings.max_retries == 0


def test_model_override_and_secret_free_settings(monkeypatch):
    monkeypatch.setenv("API_SUPPORT_LAB_MODEL", " custom-model ")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-secret-never-display")
    settings = load_settings()
    assert settings.model == "custom-model"
    assert "dummy-secret-never-display" not in repr(settings)


def test_blank_model_override_is_rejected(monkeypatch):
    monkeypatch.setenv("API_SUPPORT_LAB_MODEL", "   ")
    with pytest.raises(ConfigurationError, match="API_SUPPORT_LAB_MODEL must not be blank"):
        load_settings()


@pytest.mark.parametrize("timeout", [0, -1, math.inf, math.nan])
def test_timeout_must_be_positive_and_finite(timeout):
    with pytest.raises(ConfigurationError, match="timeout_seconds"):
        Settings(timeout_seconds=timeout)


@pytest.mark.parametrize("name", ["max_output_tokens", "agent_max_output_tokens", "max_turns"])
@pytest.mark.parametrize("value", [0, -1, 1.5])
def test_request_bounds_must_be_positive_integers(name, value):
    with pytest.raises(ConfigurationError, match=name):
        Settings(**{name: value})


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_credentials_have_an_actionable_error(monkeypatch, key):
    if key is None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("OPENAI_API_KEY", key)
    with pytest.raises(ConfigurationError, match="Set OPENAI_API_KEY"):
        require_api_key()
