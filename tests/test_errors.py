"""Unit tests for the exception hierarchy.

Robot Framework itself only ever matches on message text, so these types
matter for Python code built on top of the library (custom keywords that want
to catch a specific failure kind). The tests below pin the hierarchy so a
future change doesn't silently flatten it back to one generic error.
"""

from MCPClientLibrary.errors import (
    MCPConnectionError,
    MCPHandshakeError,
    MCPLibraryError,
    MCPProcessError,
    MCPProtocolError,
    MCPTimeoutError,
    MCPValidationError,
)


class TestHierarchy:
    def test_every_error_is_an_mcp_library_error(self):
        for cls in (
            MCPTimeoutError,
            MCPConnectionError,
            MCPHandshakeError,
            MCPProcessError,
            MCPProtocolError,
            MCPValidationError,
        ):
            assert issubclass(cls, MCPLibraryError)

    def test_handshake_and_process_errors_are_connection_errors(self):
        # A test written against the old, flatter hierarchy that catches
        # MCPConnectionError must still catch both of these.
        assert issubclass(MCPHandshakeError, MCPConnectionError)
        assert issubclass(MCPProcessError, MCPConnectionError)

    def test_protocol_and_validation_errors_are_not_connection_errors(self):
        # These happen on an already-open connection, so catching
        # MCPConnectionError should not swallow them.
        assert not issubclass(MCPProtocolError, MCPConnectionError)
        assert not issubclass(MCPValidationError, MCPConnectionError)

    def test_all_errors_suppress_their_class_name_in_robot_output(self):
        for cls in (
            MCPLibraryError,
            MCPTimeoutError,
            MCPConnectionError,
            MCPHandshakeError,
            MCPProcessError,
            MCPProtocolError,
            MCPValidationError,
        ):
            assert cls.ROBOT_SUPPRESS_NAME is True

    def test_errors_carry_the_message_given_to_them(self):
        err = MCPProcessError("the executable was not found")
        assert str(err) == "the executable was not found"
