"""Keywords that list and call the tools a server exposes."""

from robot.api.deco import keyword

from .. import _convert as convert
from .._logging import log_request, log_response


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
        and transport problems raise an error from this keyword.

        Example:
        | ${result}= | Call Tool | get_weather | city=Paris |
        | Tool Result Should Not Be Error | ${result} |
        """
        log_request("tools/call", name=name, arguments=arguments)
        result = self._connection.call(
            lambda s: s.call_tool(name, dict(arguments)), timeout=self._timeout(timeout)
        )
        log_response("tools/call", result)
        return self._maybe_convert(result)

    @keyword("Call Tool With Arguments")
    def call_tool_with_arguments(self, name, arguments=None, timeout=None):
        """Calls a tool with its arguments given as a dictionary.

        Use this when argument names are not valid Robot named arguments, or
        when the arguments are built at runtime.

        Example:
        | ${args}= | Create Dictionary | city=Paris |
        | ${result}= | Call Tool With Arguments | get_weather | ${args} |
        """
        arguments = dict(arguments) if arguments else {}
        log_request("tools/call", name=name, arguments=arguments)
        result = self._connection.call(
            lambda s: s.call_tool(name, arguments), timeout=self._timeout(timeout)
        )
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

    # -- helpers ---------------------------------------------------------

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
