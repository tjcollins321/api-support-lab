"""Live opt-in and a test-only tripwire for unexpected network access."""

import json
import socket
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def authored_drafts():
    """Hand-written offline examples, never observations of model performance."""
    return json.loads((Path(__file__).parent / "fixtures/triage_drafts.json").read_text())


def pytest_addoption(parser):
    parser.addoption("--run-live", action="store_true", help="Permit tests marked live to run.")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-live"):
        skip = pytest.mark.skip(reason="Live tests require explicit --run-live opt-in.")
        for item in items:
            if item.get_closest_marker("live"):
                item.add_marker(skip)


@pytest.fixture(autouse=True)
def offline_network_guard(request, monkeypatch):
    if request.node.get_closest_marker("live") and request.config.getoption("--run-live"):
        return

    def blocked(*args, **kwargs):
        raise AssertionError("Unexpected network access in an offline test.")

    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
