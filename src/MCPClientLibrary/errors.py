"""Exceptions raised by the library.

Robot shows the message of a failing keyword to the user, so every error the
library raises carries a message that explains the problem without a traceback.
``ROBOT_SUPPRESS_NAME`` keeps the class name out of that message.
"""


class MCPLibraryError(RuntimeError):
    """A problem talking to the MCP server, or using the library wrongly."""

    ROBOT_SUPPRESS_NAME = True


class MCPTimeoutError(MCPLibraryError):
    """The server did not answer within the timeout."""


class MCPConnectionError(MCPLibraryError):
    """The server could not be started, or the session is not usable."""
