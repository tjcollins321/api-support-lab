import socket
from pathlib import Path

import pytest


def test_offline_guard_blocks_dns():
    with pytest.raises(AssertionError, match="Unexpected network access"):
        socket.getaddrinfo("example.invalid", 443)


@pytest.mark.parametrize("method", ["connect", "connect_ex"])
def test_offline_guard_blocks_connections(method):
    # Invoke the patched methods without creating even a local OS socket.
    with pytest.raises(AssertionError, match="Unexpected network access"):
        getattr(socket.socket, method)(None, ("127.0.0.1", 9))


def test_marker_selection_does_not_authorize_live_tests(pytester):
    # Exercise the real project hooks in an isolated suite with a harmless live probe.
    pytester.makeconftest(Path(__file__).with_name("conftest.py").read_text())
    pytester.makeini("[pytest]\nmarkers = live: explicit live opt-in\n")
    pytester.makepyfile("""
        import pytest

        def test_offline():
            pass

        @pytest.mark.live
        def test_live_probe():
            pass
    """)
    pytester.runpytest_subprocess("-q").assert_outcomes(passed=1, skipped=1)
    pytester.runpytest_subprocess("-q", "-m", "live").assert_outcomes(skipped=1, deselected=1)
    pytester.runpytest_subprocess("-q", "-m", "live", "--run-live").assert_outcomes(
        passed=1, deselected=1,
    )
