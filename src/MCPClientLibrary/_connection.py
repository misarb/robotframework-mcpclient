"""One MCP session, held open across keywords.

The session lives in a single task on the bridge loop: it opens the transport
and the client session, runs the handshake, then waits on a shutdown event so
the context managers stay open. Keywords reach it through :meth:`call`.
"""

import asyncio
import tempfile
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters, stdio_client, types
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from mcp.shared.exceptions import MCPError as SdkMCPError
from mcp.shared.jsonrpc_dispatcher import CONNECTION_CLOSED

from .errors import (
    MCPConnectionError,
    MCPHandshakeError,
    MCPLibraryError,
    MCPProcessError,
    MCPProtocolError,
)

STDERR_TAIL_CHARS = 2000


class MCPConnection:
    """A live connection to one MCP server."""

    def __init__(self, bridge, transport="stdio", **transport_options):
        self._bridge = bridge
        self._transport = transport
        self._transport_options = transport_options
        self._session = None
        self._shutdown = None
        self._ready = None
        self._closed = None
        self._failure = None
        self._errlog = None
        self._stderr_tail = ""
        self.alias = None
        self.server_info = None
        self.capabilities = None
        self.log_messages = []
        self.last_call_progress = []
        self.resource_updates = []
        self.roots = []
        self.pending_sampling_response = None
        self.pending_elicitation_response = None

    # -- transport seam ---------------------------------------------------
    # Every transport returns the same (read, write) stream pair, so adding
    # streamable HTTP later touches this method and nothing else.

    @asynccontextmanager
    async def _open_transport(self):
        if self._transport == "stdio":
            async with self._open_stdio_transport() as streams:
                yield streams
        elif self._transport == "http":
            async with self._open_http_transport() as streams:
                yield streams
        else:
            raise MCPLibraryError(
                f"Unsupported transport '{self._transport}'. "
                f"This version supports 'stdio' and 'http'."
            )

    @asynccontextmanager
    async def _open_stdio_transport(self):
        params = StdioServerParameters(**self._transport_options)
        # The server's stderr goes to a temporary file rather than to
        # sys.stderr: Robot replaces sys.stderr with a stream that has no
        # file descriptor, which the subprocess cannot inherit. Capturing
        # it also means a server that dies during startup can explain why.
        self._errlog = tempfile.TemporaryFile(mode="w+", prefix="mcp-server-stderr-")
        try:
            async with stdio_client(params, errlog=self._errlog) as streams:
                yield streams
        finally:
            errlog, self._errlog = self._errlog, None
            self._stderr_tail = self._read_stderr(errlog)
            errlog.close()

    @asynccontextmanager
    async def _open_http_transport(self):
        url = self._transport_options["url"]
        headers = self._transport_options.get("headers")
        http_client = create_mcp_http_client(headers=headers) if headers else None
        async with streamable_http_client(url, http_client=http_client) as streams:
            yield streams

    @staticmethod
    def _read_stderr(errlog):
        """The tail of whatever the server wrote to stderr, for error messages."""
        try:
            errlog.seek(0)
            text = errlog.read().strip()
        except (OSError, ValueError):
            return ""
        return text[-STDERR_TAIL_CHARS:] if len(text) > STDERR_TAIL_CHARS else text

    async def _on_log_message(self, params):
        """Records a ``notifications/message`` the server sends during the session.

        Called on the bridge's loop thread; every ``_on_*`` callback below
        follows the same rule: the list or attribute it touches is read and
        written on both threads, which is safe under the GIL because there is
        no compound read-modify-write shared across the two sides — a keyword
        either reads a fully-formed value or replaces it outright.
        """
        self.log_messages.append(params)

    async def _on_message(self, message):
        """Routes every other server notification; picks out resource updates.

        ``message_handler`` tees every notification the session surfaces
        (``logging_callback`` also fires for log messages, separately), so
        this is the seam for anything that isn't already handled elsewhere —
        currently just ``notifications/resources/updated``.
        """
        if isinstance(message, types.ResourceUpdatedNotification):
            self.resource_updates.append(str(message.params.uri))

    async def _on_list_roots(self, context):
        """Answers ``roots/list`` with whatever `Set Client Roots` configured."""
        roots = [types.Root(uri=r["uri"], name=r.get("name")) for r in self.roots]
        return types.ListRootsResult(roots=roots)

    async def _on_sampling(self, context, params):
        """Answers ``sampling/createMessage`` with the one pending canned response.

        Consumed once: cleared after answering, so a second sampling request
        in the same call with nothing newly queued gets a clear error instead
        of silently reusing a stale answer.
        """
        response = self.pending_sampling_response
        self.pending_sampling_response = None
        if response is None:
            return types.ErrorData(
                code=-32603,
                message=(
                    "The server asked the client to sample a message, but no "
                    "response was queued. Use 'Set Sampling Response' before "
                    "the call that triggers it."
                ),
            )
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(type="text", text=response["text"]),
            model=response.get("model") or "test-client",
        )

    async def _on_elicitation(self, context, params):
        """Answers ``elicitation/create`` with the one pending canned response.

        Consumed once, same as sampling — see `_on_sampling`.
        """
        response = self.pending_elicitation_response
        self.pending_elicitation_response = None
        if response is None:
            return types.ErrorData(
                code=-32603,
                message=(
                    "The server asked the client to elicit input, but no "
                    "response was queued. Use 'Set Elicitation Response' "
                    "before the call that triggers it."
                ),
            )
        return types.ElicitResult(
            action=response["action"],
            content=response.get("content"),
        )

    def _describe_failure(self, failure):
        """A failure message that includes the server's own stderr, if any."""
        message = f"Could not connect to the MCP server: {failure}"
        if self._stderr_tail:
            message = f"{message}\n\nThe server wrote to stderr:\n{self._stderr_tail}"
        return message

    # -- lifecycle --------------------------------------------------------

    def open(self, timeout=30):
        """Start the server and complete the handshake. Blocks until ready."""
        self._bridge.run(self._start(), timeout=timeout)
        if self._failure is not None:
            failure = self._failure
            self._failure = None
            error_type = (
                type(failure) if isinstance(failure, MCPConnectionError) else MCPProcessError
            )
            raise error_type(self._describe_failure(failure)) from failure
        if self._session is None:
            raise MCPProcessError(
                self._describe_failure("it closed the connection during the handshake")
            )
        return self

    async def _start(self):
        self._shutdown = asyncio.Event()
        self._ready = asyncio.Event()
        self._closed = asyncio.Event()
        # Hold the session in its own task so that open() can return as soon
        # as the handshake is done while the context managers stay entered.
        self._task = asyncio.ensure_future(self._hold())
        await self._ready.wait()

    async def _hold(self):
        try:
            async with self._open_transport() as (read, write):
                try:
                    async with ClientSession(
                        read,
                        write,
                        logging_callback=self._on_log_message,
                        message_handler=self._on_message,
                        list_roots_callback=self._on_list_roots,
                        sampling_callback=self._on_sampling,
                        elicitation_callback=self._on_elicitation,
                    ) as session:
                        result = await session.initialize()
                        self._session = session
                        self.server_info = result.server_info
                        self.capabilities = result.capabilities
                        self._ready.set()
                        await self._shutdown.wait()
                except Exception as err:
                    # The transport came up; the failure is the handshake
                    # itself (bad initialize response, protocol mismatch, or
                    # the session closing before it completed).
                    raise MCPHandshakeError(str(err)) from err
        except MCPHandshakeError as err:
            self._failure = err
        except Exception as err:
            # The transport itself never came up: the process could not be
            # spawned, or (for HTTP) the connection was refused.
            self._failure = MCPProcessError(str(err))
            self._failure.__cause__ = err
        finally:
            self._session = None
            self._ready.set()
            self._closed.set()

    def close(self, timeout=10):
        """Signal shutdown and wait for the transport to tear down."""
        if self._shutdown is None or self._closed is None:
            return
        try:
            self._bridge.run(self._stop(), timeout=timeout)
        except MCPLibraryError:
            # A server that refuses to exit must not fail the teardown; the
            # subprocess is killed by the SDK's transport cleanup regardless.
            pass
        finally:
            self._session = None

    async def _stop(self):
        self._shutdown.set()
        await self._closed.wait()

    @property
    def is_open(self):
        return self._session is not None

    # -- use --------------------------------------------------------------

    def call(self, make_coro, timeout=30):
        """Run ``make_coro(session)`` on the loop thread and return its result.

        A JSON-RPC error from the server (an unknown method, invalid params, an
        internal server error at the protocol level) is not a tool-level
        failure — that comes back as a normal result with the error flag set.
        This is the transport telling us the *request itself* was rejected, so
        it is raised as ``MCPProtocolError`` rather than returned.

        A closed connection (the server crashed, or otherwise tore down its
        end mid-call) is reported by the SDK the same way as a JSON-RPC error,
        under a dedicated error code. That case is treated differently: the
        connection is marked closed right away, so a stale ``is_open`` does
        not outlive the process that backed it, and the failure is raised as
        ``MCPConnectionError`` — a usability problem with the session, not a
        request the server rejected.
        """
        if self._session is None:
            raise MCPConnectionError(
                "The MCP session is not open. Use 'Connect To MCP Server' first."
            )
        try:
            return self._bridge.run(make_coro(self._session), timeout=timeout)
        except SdkMCPError as err:
            if err.code == CONNECTION_CLOSED:
                self._session = None
                raise MCPConnectionError(
                    "The MCP server's connection closed unexpectedly — it may have "
                    "crashed. Reconnect with 'Connect To MCP Server' before the next call."
                ) from err
            raise MCPProtocolError(f"The MCP server returned an error: {err}") from err
