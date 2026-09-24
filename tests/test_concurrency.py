"""Tests for concurrent access to the library from multiple Python threads.

These matter because the library's async bridge is explicitly designed to be
called from any thread (asyncio.run_coroutine_threadsafe), and because
Switch MCP Server mutates state (ConnectionCache.current) shared across the
whole library instance — a real race if two threads target different
connections. Call Tool On Server exists specifically to avoid that; these
tests pin both the hazard and the fix so a future refactor can't silently
reintroduce it.

Uses the sample servers under tests/servers/ via a real subprocess
connection — these are integration tests dressed as unit tests, but they
need no Robot Framework runtime, so they live here rather than in atest/.
"""

import sys
import threading
import time
from pathlib import Path

import pytest

from MCPClientLibrary import MCPClientLibrary

SERVERS_DIR = Path(__file__).parent / "servers"


@pytest.fixture
def lib():
    library = MCPClientLibrary(default_timeout=10)
    yield library
    library._cache.close_all("close")
    library._bridge.shutdown()


class TestConcurrentCallsOnDifferentConnections:
    def test_call_tool_on_server_is_race_free_under_load(self, lib):
        lib.connect_to_mcp_server(
            sys.executable, str(SERVERS_DIR / "weather_server.py"), alias="weather"
        )
        lib.connect_to_mcp_server(
            sys.executable, str(SERVERS_DIR / "notes_server.py"), alias="notes"
        )

        results = []
        lock = threading.Lock()

        def call_weather(n):
            for _ in range(n):
                result = lib.call_tool_on_server("weather", "get_weather", city="Paris")
                with lock:
                    results.append(("weather", result))

        def call_notes(n):
            for _ in range(n):
                result = lib.call_tool_on_server("notes", "create_note", text="hi")
                with lock:
                    results.append(("notes", result))

        threads = [
            threading.Thread(target=call_weather, args=(30,)),
            threading.Thread(target=call_notes, args=(30,)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 60
        for alias, result in results:
            assert not result.is_error, f"{alias} call unexpectedly errored: {result}"

    def test_switch_mcp_server_races_across_threads(self, lib):
        """Documents the hazard Call Tool On Server exists to avoid.

        Not a test of correct behaviour — it demonstrates the race so this
        file also stands as evidence for the README's warning. If this test
        starts failing (no race detected), the timing assumption below has
        gone stale on whatever's running it; it is not a signal the hazard
        was fixed, since fixing it would require changing what Switch MCP
        Server does.
        """
        lib.connect_to_mcp_server(
            sys.executable, str(SERVERS_DIR / "weather_server.py"), alias="weather"
        )
        lib.connect_to_mcp_server(
            sys.executable, str(SERVERS_DIR / "notes_server.py"), alias="notes"
        )

        wrong_server_errors = []
        lock = threading.Lock()

        def switch_and_call(alias, tool, kwargs, n):
            for _ in range(n):
                lib.switch_mcp_server(alias)
                time.sleep(0.001)  # widen the race window deliberately
                try:
                    lib.call_tool(tool, **kwargs)
                except Exception as err:
                    with lock:
                        wrong_server_errors.append(str(err))

        threads = [
            threading.Thread(
                target=switch_and_call, args=("weather", "get_weather", {"city": "Paris"}, 20)
            ),
            threading.Thread(
                target=switch_and_call, args=("notes", "create_note", {"text": "hi"}, 20)
            ),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The race is real: with a delay between switch and call, at least
        # some calls land on the wrong server. This is expected, not a bug
        # to chase here - see Call Tool On Server for the fix.
        assert len(wrong_server_errors) > 0


class TestConnectionNamedLookup:
    def test_does_not_change_current_connection(self, lib):
        lib.connect_to_mcp_server(
            sys.executable, str(SERVERS_DIR / "weather_server.py"), alias="weather"
        )
        lib.connect_to_mcp_server(
            sys.executable, str(SERVERS_DIR / "notes_server.py"), alias="notes"
        )
        # "weather" is current after the second connect call above? No -
        # "notes" is, since it was connected last.
        current_before = lib._cache.current

        lib._connection_named("weather")

        assert lib._cache.current is current_before

    def test_looks_up_by_alias_and_by_index(self, lib):
        lib.connect_to_mcp_server(
            sys.executable, str(SERVERS_DIR / "weather_server.py"), alias="weather"
        )
        by_alias = lib._connection_named("weather")
        by_index = lib._connection_named(1)
        assert by_alias is by_index
