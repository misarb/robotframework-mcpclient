"""Exceptions raised by the library.

Robot shows the message of a failing keyword to the user, so every error the
library raises carries a message that explains the problem without a traceback.
``ROBOT_SUPPRESS_NAME`` keeps the class name out of that message.

Robot Framework itself only matches on message text (``Run Keyword And Expect
Error`` takes a glob pattern, not a type), so the hierarchy below is aimed at
Python code that builds on this library — a custom keyword module can catch
``MCPHandshakeError`` specifically instead of the generic base. Existing tests
that match text, or catch the base ``MCPLibraryError``, keep working: every
subclass here is still an ``MCPLibraryError``.
"""


class MCPLibraryError(RuntimeError):
    """A problem talking to the MCP server, or using the library wrongly."""

    ROBOT_SUPPRESS_NAME = True


class MCPTimeoutError(MCPLibraryError):
    """The server did not answer within the timeout."""


class MCPConnectionError(MCPLibraryError):
    """The server could not be started, or the session is not usable."""


class MCPHandshakeError(MCPConnectionError):
    """The server started but the ``initialize`` handshake failed or never completed."""


class MCPProcessError(MCPConnectionError):
    """The server subprocess could not be started, or exited before the handshake."""


class MCPProtocolError(MCPLibraryError):
    """The server returned a JSON-RPC error, or violated the protocol."""


class MCPValidationError(MCPLibraryError):
    """A result did not match what the server itself declared (e.g. its schema)."""
