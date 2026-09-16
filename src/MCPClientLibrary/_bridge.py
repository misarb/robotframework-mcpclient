"""Runs async MCP code from Robot Framework's synchronous keyword thread.

The MCP client is a pair of async context managers that must stay open across
many keywords, and anyio requires that they are entered and exited in the same
task. So the library keeps one event loop running on a background thread for
its whole lifetime, and keywords hop into it with ``run_coroutine_threadsafe``.
"""

import asyncio
import concurrent.futures
import threading

from .errors import MCPLibraryError, MCPTimeoutError


class AsyncBridge:
    """A background thread running one event loop, shared by all connections."""

    def __init__(self):
        self._loop = None
        self._thread = None
        self._lock = threading.Lock()

    @property
    def loop(self):
        self.start()
        return self._loop

    def start(self):
        """Start the loop thread if it is not running yet."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._loop = asyncio.new_event_loop()
            ready = threading.Event()
            self._thread = threading.Thread(
                target=self._run, args=(ready,), name="MCPClientLibrary-loop", daemon=True
            )
            self._thread.start()
            ready.wait(timeout=5)

    def _run(self, ready):
        asyncio.set_event_loop(self._loop)
        self._loop.call_soon(ready.set)
        self._loop.run_forever()

    def run(self, coro, timeout=30):
        """Run ``coro`` on the loop thread and block until it returns.

        The timeout is a hard ceiling: a hung server fails one keyword instead
        of hanging the whole suite.
        """
        self.start()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=timeout)
        except (concurrent.futures.TimeoutError, TimeoutError, asyncio.TimeoutError):
            future.cancel()
            raise MCPTimeoutError(
                f"The MCP server did not respond within {timeout} seconds."
            ) from None
        except asyncio.CancelledError:
            raise MCPLibraryError("The MCP operation was cancelled.") from None

    def shutdown(self, timeout=5):
        """Stop the loop and join the thread. Safe to call more than once."""
        with self._lock:
            if self._thread is None:
                return
            loop, thread = self._loop, self._thread
            self._loop, self._thread = None, None
        if loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=timeout)
        if not loop.is_closed():
            loop.close()
