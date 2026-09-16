"""Unit tests for the async-to-sync bridge."""

import asyncio

import pytest

from MCPClientLibrary._bridge import AsyncBridge
from MCPClientLibrary.errors import MCPTimeoutError


@pytest.fixture
def bridge():
    bridge = AsyncBridge()
    yield bridge
    bridge.shutdown()


def test_runs_a_coroutine_and_returns_its_value(bridge):
    async def answer():
        return 42

    assert bridge.run(answer()) == 42


def test_exceptions_from_the_coroutine_reach_the_caller(bridge):
    async def fail():
        raise ValueError("server said no")

    with pytest.raises(ValueError, match="server said no"):
        bridge.run(fail())


def test_a_slow_coroutine_times_out_with_a_readable_message(bridge):
    async def slow():
        await asyncio.sleep(5)

    with pytest.raises(MCPTimeoutError, match="did not respond within 0.1 seconds"):
        bridge.run(slow(), timeout=0.1)


def test_the_loop_survives_a_timeout(bridge):
    async def slow():
        await asyncio.sleep(5)

    async def answer():
        return "still working"

    with pytest.raises(MCPTimeoutError):
        bridge.run(slow(), timeout=0.1)
    assert bridge.run(answer()) == "still working"


def test_state_persists_across_calls_on_the_same_loop(bridge):
    # The point of the bridge: one loop, so asyncio primitives created in one
    # call are still usable in the next.
    event = bridge.run(make_event())

    async def set_it():
        event.set()

    async def read_it():
        return event.is_set()

    bridge.run(set_it())
    assert bridge.run(read_it()) is True


async def make_event():
    return asyncio.Event()


def test_starting_twice_is_harmless(bridge):
    bridge.start()
    bridge.start()

    async def answer():
        return "ok"

    assert bridge.run(answer()) == "ok"


def test_shutdown_is_idempotent():
    bridge = AsyncBridge()

    async def answer():
        return "ok"

    bridge.run(answer())
    bridge.shutdown()
    bridge.shutdown()


def test_the_bridge_restarts_after_shutdown():
    bridge = AsyncBridge()

    async def answer():
        return "ok"

    assert bridge.run(answer()) == "ok"
    bridge.shutdown()
    assert bridge.run(answer()) == "ok"
    bridge.shutdown()
