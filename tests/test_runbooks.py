import asyncio
import json

import pytest
from agents import ModelBehaviorError
from agents.tool_context import ToolContext

from api_support_lab import runbooks
from api_support_lab.agent import TOOLS, diagnose_tool, get_runbook_tool, list_runbooks_tool


@pytest.mark.parametrize("status,code,expected", [
    (401, None, ["invalid_credentials"]),
    (401, "invalid_api_key", ["invalid_credentials"]),
    (401, "unknown_code", []), (401, "", []),
    (403, "invalid_api_key", []), (200, None, []),
    (400, None, ["tool_schema"]),
    (400, "invalid_function_parameters", ["tool_schema"]),
    (400, "unknown_schema_code", []), (408, None, []),
])
def test_observation_backed_diagnosis(status, code, expected):
    assert runbooks.diagnose(status, code) == expected


@pytest.mark.parametrize("status", [True, "401", 401.0, None, 99, 600])
def test_status_validation(status):
    with pytest.raises(ValueError, match="HTTP integer"):
        runbooks.diagnose(status)


def test_code_type():
    with pytest.raises(ValueError, match="string or null"):
        runbooks.diagnose(401, 3)


def test_order_deduplication_and_status_ambiguity(monkeypatch, tmp_path):
    # Synthetic registry, not additions to the observed production mappings.
    monkeypatch.setattr(runbooks, "REGISTRY", {
        "timeout": runbooks.Runbook(tmp_path / "a", ((400, "a"), (400, "a"))),
        "tool_schema": runbooks.Runbook(tmp_path / "b", ((400, "b"),)),
    })
    assert runbooks.diagnose(400) == ["timeout", "tool_schema"]
    assert runbooks.diagnose(400, "b") == ["tool_schema"]


def test_resources_ignore_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert "Status: `verified`" in runbooks.get_runbook("invalid_credentials")
    assert list(runbooks.list_runbooks()) == ["invalid_credentials", "tool_schema", "incomplete_output", "timeout"]
    for case, symptoms in runbooks.list_runbooks().items():
        assert symptoms == runbooks.get_runbook(case).split("\n\n")[1]


@pytest.mark.parametrize("case", ["../.env", "/etc/passwd", "unknown"])
def test_only_registered_ids(case):
    with pytest.raises(ValueError, match="Unregistered"):
        runbooks.get_runbook(case)


def test_missing_runbook_is_explicit(monkeypatch, tmp_path):
    monkeypatch.setattr(runbooks, "REGISTRY", {
        "invalid_credentials": runbooks.Runbook(tmp_path / "absent.md"),
    })
    with pytest.raises(FileNotFoundError):
        runbooks.get_runbook("invalid_credentials")
    with pytest.raises(FileNotFoundError):
        runbooks.list_runbooks()


def test_actual_strict_tool_schemas_and_invocation():
    assert [tool.name for tool in TOOLS] == ["diagnose", "list_runbooks", "get_runbook"]
    for tool in TOOLS:
        assert tool.strict_json_schema
        assert tool.params_json_schema["additionalProperties"] is False
    schema = diagnose_tool.params_json_schema
    assert schema["required"] == ["status", "error_code"]
    assert schema["properties"]["status"]["type"] == "integer"
    assert schema["properties"]["error_code"]["anyOf"] == [{"type": "string"}, {"type": "null"}]
    assert list_runbooks_tool.params_json_schema["properties"] == {}
    assert get_runbook_tool.params_json_schema["required"] == ["case"]
    assert get_runbook_tool.params_json_schema["properties"]["case"]["enum"] == [
        "invalid_credentials", "tool_schema", "incomplete_output", "timeout",
    ]
    async def invoke():
        async def call(tool, args):
            arguments = json.dumps(args)
            context = ToolContext(context=None, tool_name=tool.name, tool_call_id="synthetic", tool_arguments=arguments)
            return await tool.on_invoke_tool(context, arguments)
        assert await call(diagnose_tool, {"status": 401, "error_code": None}) == ["invalid_credentials"]
        assert await call(list_runbooks_tool, {}) == runbooks.list_runbooks()
        assert await call(get_runbook_tool, {"case": "invalid_credentials"}) == runbooks.get_runbook("invalid_credentials")
        for case in ("tool_schema", "incomplete_output", "timeout"):
            contents = await call(get_runbook_tool, {"case": case})
            assert "Status: `verified`" in contents
            assert "Verified on: `2026-10-22`" in contents
        assert runbooks.REGISTRY["incomplete_output"].observations == ()
        assert runbooks.REGISTRY["timeout"].observations == ()
        with pytest.raises(ModelBehaviorError, match="Invalid JSON input"):
            await call(get_runbook_tool, {"case": "unknown"})
    asyncio.run(asyncio.wait_for(invoke(), timeout=5))
