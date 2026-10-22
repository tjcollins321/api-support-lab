import os
import subprocess
import sys

import pytest

from api_support_lab import config, sdk
from api_support_lab.cli import main


@pytest.fixture(autouse=True)
def forbid_client_and_credential_access(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("CLI foundation must not load credentials or construct a client")

    monkeypatch.setattr(config, "require_api_key", forbidden)
    monkeypatch.setattr(sdk, "create_client", forbidden)


@pytest.mark.parametrize("key", [None, "dummy-secret-never-display"])
@pytest.mark.parametrize("args", [
    ["reproduce", "invalid_credentials", "--variant", "broken"],
    ["triage", "ticket.yaml"],
    ["evaluate"],
])
def test_live_commands_refuse_without_opt_in(monkeypatch, capsys, key, args):
    if key is None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("OPENAI_API_KEY", key)
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2
    output = capsys.readouterr().err
    assert "--live" in output
    assert "dummy-secret-never-display" not in output


@pytest.mark.parametrize("args", [
    ["reproduce", "tool_schema", "--variant", "fixed", "--live"],
    ["triage", "ticket.yaml", "--live"],
    ["evaluate", "--live"],
    ["evaluate", "--results", "missing-results.json"],
    ["diagnose", "--status", "401", "--error-code", "unfamiliar_code"],
])
def test_unfinished_handlers_fail_explicitly_without_side_effects(capsys, args):
    assert main(args) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "not implemented" in output.err


@pytest.mark.parametrize("args", [
    ["evaluate", "--live", "--results", "results.json"],
    ["diagnose", "--status", "not-a-status"],
    ["diagnose", "--status", "600"],
    ["diagnose", "--status", "99"],
    ["reproduce", "unknown_case", "--variant", "broken"],
    ["reproduce", "timeout", "--variant", "unknown_variant"],
])
def test_invalid_arguments_fail_before_dispatch(args):
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2


def test_imports_and_module_help_from_another_directory(tmp_path):
    environment = os.environ.copy()
    environment.pop("OPENAI_API_KEY", None)
    environment["API_SUPPORT_LAB_MODEL"] = ""  # Help does not require valid live configuration.
    script = """
import sys
import api_support_lab
import api_support_lab.cli
import api_support_lab.config
import api_support_lab.sdk
assert 'openai' not in sys.modules
assert 'agents' not in sys.modules
"""
    imported = subprocess.run(
        [sys.executable, "-c", script], cwd=tmp_path, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert imported.returncode == 0, imported.stderr
    helped = subprocess.run(
        [sys.executable, "-m", "api_support_lab", "--help"], cwd=tmp_path,
        env=environment, capture_output=True, text=True, check=False,
    )
    assert helped.returncode == 0, helped.stderr
    assert "technical learning lab" in helped.stdout
