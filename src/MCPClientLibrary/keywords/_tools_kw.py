"""Keywords that list and call the tools a server exposes."""

from robot.api.deco import keyword

from .. import _convert as convert
from .._logging import log_request, log_response
from ..errors import MCPValidationError

# On mcp 2.x, ClientSession.call_tool() validates a successful result's
# structured content against the tool's own output schema and raises a bare
# RuntimeError if it does not match (mcp 1.x has no such check). The three
# phrasings below are the only ones that method raises; matching on them lets
# _call_tool wrap just that failure as MCPValidationError without swallowing
# an unrelated RuntimeError raised elsewhere in the call.
_SCHEMA_VALIDATION_MARKERS = (
    "has an output schema but did not return structured content",
    "Invalid structured content returned by tool",
    "Invalid schema for tool",
)


class ToolKeywords:
    @keyword("List Tools")
    def list_tools(self, timeout=None):
        """Returns every tool the server exposes.

        Each tool has ``name``, ``description`` and ``input_schema``. For just
        the names, use `Get Tool Names`.

        Example:
        | ${tools}= | List Tools |
        | Length Should Be | ${tools} | 2 |
        """
        log_request("tools/list")
        result = self._connection.call(lambda s: s.list_tools(), timeout=self._timeout(timeout))
        log_response("tools/list", result)
        return self._maybe_convert(list(result.tools))

    @keyword("Get Tool Names")
    def get_tool_names(self, timeout=None):
        """Returns the names of the server's tools as a list of strings.

        Example:
        | ${names}= | Get Tool Names |
        | Should Contain | ${names} | get_weather |
        """
        log_request("tools/list")
        result = self._connection.call(lambda s: s.list_tools(), timeout=self._timeout(timeout))
        names = [convert.tool_name(tool) for tool in result.tools]
        log_response("tools/list", names)
        return names

    @keyword("Get Tool")
    def get_tool(self, name, timeout=None):
        """Returns one tool by name, or fails if the server does not expose it."""
        tool = self._find_tool(name, timeout=timeout)
        if tool is None:
            raise AssertionError(
                f"The server does not expose a tool named '{name}'. "
                f"Available tools: {self._tool_names_text(timeout)}."
            )
        return self._maybe_convert(tool)

    @keyword("Call Tool")
    def call_tool(self, name, timeout=None, **arguments):
        """Calls a tool and returns its result.

        Tool arguments are given as named arguments. The result has ``content``
        (a list of content blocks) and an error flag; check the flag with
        `Tool Result Should Not Be Error` rather than reading it directly, so
        the test keeps working across MCP SDK versions.

        A tool that reports a failure still returns a result — only protocol
        and transport problems raise an error from this keyword. On mcp 2.x, a
        tool returning structured content that violates its own declared
        output schema is one such problem: the SDK checks this itself and the
        call raises ``MCPValidationError`` instead of returning a result. See
        `Tool Result Should Match Output Schema` to check this explicitly, and
        for SDK versions that don't check it automatically.

        Example:
        | ${result}= | Call Tool | get_weather | city=Paris |
        | Tool Result Should Not Be Error | ${result} |
        """
        log_request("tools/call", name=name, arguments=arguments)
        result = self._call_tool(name, dict(arguments), timeout)
        log_response("tools/call", result)
        return self._maybe_convert(result)

    @keyword("Call Tool With Arguments")
    def call_tool_with_arguments(self, name, arguments=None, timeout=None):
        """Calls a tool with its arguments given as a dictionary.

        Use this when argument names are not valid Robot named arguments, or
        when the arguments are built at runtime. See `Call Tool` for how a
        schema-violating result is handled.

        Example:
        | ${args}= | Create Dictionary | city=Paris |
        | ${result}= | Call Tool With Arguments | get_weather | ${args} |
        """
        arguments = dict(arguments) if arguments else {}
        log_request("tools/call", name=name, arguments=arguments)
        result = self._call_tool(name, arguments, timeout)
        log_response("tools/call", result)
        return self._maybe_convert(result)

    @keyword("Get Tool Result Text")
    def get_tool_result_text(self, result):
        """Returns the text blocks of a tool result joined into one string.

        Example:
        | ${result}= | Call Tool | get_weather | city=Paris |
        | ${text}= | Get Tool Result Text | ${result} |
        | Should Contain | ${text} | temperature |
        """
        return convert.all_text(result)

    @keyword("Get Tool Result Data")
    def get_tool_result_data(self, result):
        """Returns the structured (JSON) content of a tool result, or None.

        Servers that declare an output schema return data here as well as text.
        """
        return convert.structured_content(result)

    @keyword("Get Last Tool Call Progress")
    def get_last_tool_call_progress(self):
        """Returns the progress notifications sent during the most recent `Call Tool`.

        Each entry is a dictionary with ``progress``, ``total`` (may be
        ``None``), and ``message`` (may be ``None``), in the order the server
        sent them. Empty if the tool sent no progress, or before the first
        call in the suite.

        Cleared at the start of every `Call Tool` / `Call Tool With
        Arguments`, so this always reflects the single most recent call.

        Example:
        | Call Tool | slow_tool | file=big.csv |
        | ${progress}= | Get Last Tool Call Progress |
        | Should Be Equal As Numbers | ${progress}[-1][progress] | 100 |
        """
        return list(self._connection.last_call_progress)

    # -- helpers ---------------------------------------------------------

    def _call_tool(self, name, arguments, timeout):
        connection = self._connection
        connection.last_call_progress = []

        async def on_progress(progress, total, message):
            connection.last_call_progress.append(
                {"progress": progress, "total": total, "message": message}
            )

        try:
            return connection.call(
                lambda s: s.call_tool(name, arguments, progress_callback=on_progress),
                timeout=self._timeout(timeout),
            )
        except RuntimeError as err:
            message = str(err)
            if any(marker in message for marker in _SCHEMA_VALIDATION_MARKERS):
                raise MCPValidationError(
                    f"The result of '{name}' does not match its own declared "
                    f"output schema: {message}"
                ) from err
            raise

    def _find_tool(self, name, timeout=None):
        result = self._connection.call(lambda s: s.list_tools(), timeout=self._timeout(timeout))
        for tool in result.tools:
            if convert.tool_name(tool) == name:
                return tool
        return None

    def _tool_names_text(self, timeout=None):
        result = self._connection.call(lambda s: s.list_tools(), timeout=self._timeout(timeout))
        names = [convert.tool_name(tool) for tool in result.tools]
        return ", ".join(names) if names else "none"
