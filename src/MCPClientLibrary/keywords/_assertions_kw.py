"""Assertion keywords: the checks a test writer would otherwise hand-roll.

Every keyword takes an optional ``msg`` that replaces the default failure
message, following Robot convention. Default messages name what was expected
and what the server actually offered, so a failing test explains itself.
"""

import re

from robot.api.deco import keyword

from .. import _convert as convert


class AssertionKeywords:
    # -- tools ------------------------------------------------------------

    @keyword("Tool Should Exist")
    def tool_should_exist(self, name, msg=None):
        """Fails unless the server exposes a tool with this name.

        Example:
        | Tool Should Exist | get_weather |
        """
        names = self.get_tool_names()
        if name not in names:
            raise AssertionError(
                msg
                or f"The server does not expose a tool named '{name}'. "
                f"It exposes: {', '.join(names) or 'no tools'}."
            )

    @keyword("Tool Should Not Exist")
    def tool_should_not_exist(self, name, msg=None):
        """Fails if the server exposes a tool with this name.

        Useful for checking that a tool is gated off in a given configuration.
        """
        if name in self.get_tool_names():
            raise AssertionError(
                msg or f"The server exposes a tool named '{name}', but should not."
            )

    @keyword("Tool Count Should Be")
    def tool_count_should_be(self, count, msg=None):
        """Fails unless the server exposes exactly this many tools."""
        names = self.get_tool_names()
        if len(names) != int(count):
            raise AssertionError(
                msg
                or f"Expected {count} tools but the server exposes {len(names)}: "
                f"{', '.join(names) or 'none'}."
            )

    @keyword("Tool Should Have Input Schema")
    def tool_should_have_input_schema(self, name, msg=None):
        """Fails unless the named tool declares an input schema.

        A tool without a schema gives the model nothing to validate arguments
        against, so this is worth asserting even when the tool works.
        """
        tool = self._require_tool(name)
        if not convert.input_schema(tool):
            raise AssertionError(msg or f"The tool '{name}' does not declare an input schema.")

    @keyword("Tool Input Schema Should Require")
    def tool_input_schema_should_require(self, name, *fields, msg=None):
        """Fails unless the tool's input schema marks every given field required.

        Example:
        | Tool Input Schema Should Require | get_weather | city |
        """
        tool = self._require_tool(name)
        required = convert.schema_required(tool)
        missing = [field for field in fields if field not in required]
        if missing:
            raise AssertionError(
                msg
                or f"The input schema of '{name}' does not require "
                f"{', '.join(missing)}. It requires: {', '.join(required) or 'nothing'}."
            )

    @keyword("Tool Input Schema Should Have Property")
    def tool_input_schema_should_have_property(self, name, *properties, msg=None):
        """Fails unless the tool's input schema declares every given property."""
        tool = self._require_tool(name)
        declared = convert.schema_properties(tool)
        missing = [prop for prop in properties if prop not in declared]
        if missing:
            raise AssertionError(
                msg
                or f"The input schema of '{name}' does not declare "
                f"{', '.join(missing)}. It declares: {', '.join(declared) or 'nothing'}."
            )

    @keyword("Tool Should Have Description")
    def tool_should_have_description(self, name, msg=None):
        """Fails unless the named tool carries a non-empty description.

        A model picks tools by their descriptions, so an empty one is a bug
        even though the tool still runs.
        """
        tool = self._require_tool(name)
        description = (getattr(tool, "description", None) or "").strip()
        if not description:
            raise AssertionError(msg or f"The tool '{name}' has no description.")

    # -- tool results -----------------------------------------------------

    @keyword("Tool Result Should Not Be Error")
    def tool_result_should_not_be_error(self, result, msg=None):
        """Fails if the tool result carries the error flag.

        Example:
        | ${result}= | Call Tool | get_weather | city=Paris |
        | Tool Result Should Not Be Error | ${result} |
        """
        if convert.is_error(result):
            raise AssertionError(
                msg or f"The tool reported an error: {convert.all_text(result) or '(no message)'}"
            )

    @keyword("Tool Result Should Be Error")
    def tool_result_should_be_error(self, result, msg=None):
        """Fails unless the tool result carries the error flag.

        Use it to check that a server reports bad input as a tool error
        instead of crashing or quietly returning something wrong.
        """
        if not convert.is_error(result):
            raise AssertionError(
                msg
                or f"Expected the tool to report an error, but it succeeded with: "
                f"{convert.all_text(result) or '(no text)'}"
            )

    @keyword("Tool Result Should Contain Text")
    def tool_result_should_contain_text(self, result, expected, ignore_case=False, msg=None):
        """Fails unless some text block of the result contains ``expected``.

        All text blocks are searched, so a server that splits its answer over
        several blocks passes the same as one returning a single block.

        Example:
        | Tool Result Should Contain Text | ${result} | temperature |
        """
        actual = convert.all_text(result)
        haystack, needle = (actual.lower(), expected.lower()) if ignore_case else (actual, expected)
        if needle not in haystack:
            raise AssertionError(
                msg
                or f"The tool result does not contain '{expected}'. "
                f"It contains: {actual or '(no text)'}"
            )

    @keyword("Tool Result Should Not Contain Text")
    def tool_result_should_not_contain_text(self, result, unexpected, ignore_case=False, msg=None):
        """Fails if any text block of the result contains ``unexpected``.

        Handy for checking that an error path does not leak a stack trace or a
        secret into the text a model would see.
        """
        actual = convert.all_text(result)
        haystack, needle = (
            (actual.lower(), unexpected.lower()) if ignore_case else (actual, unexpected)
        )
        if needle in haystack:
            raise AssertionError(msg or f"The tool result contains '{unexpected}', but should not.")

    @keyword("Tool Result Should Match")
    def tool_result_should_match(self, result, pattern, msg=None):
        """Fails unless the result text matches a regular expression.

        Example:
        | Tool Result Should Match | ${result} | \\\\d+ degrees |
        """
        actual = convert.all_text(result)
        if not re.search(pattern, actual):
            raise AssertionError(
                msg
                or f"The tool result does not match '{pattern}'. "
                f"It contains: {actual or '(no text)'}"
            )

    @keyword("Tool Result Should Be Empty")
    def tool_result_should_be_empty(self, result, msg=None):
        """Fails unless the result carries no content blocks."""
        blocks = convert.content_blocks(result)
        if blocks:
            raise AssertionError(
                msg or f"Expected an empty tool result but it has {len(blocks)} content block(s)."
            )

    @keyword("Tool Result Should Not Be Empty")
    def tool_result_should_not_be_empty(self, result, msg=None):
        """Fails if the result carries no content blocks."""
        if not convert.content_blocks(result):
            raise AssertionError(msg or "The tool result is empty.")

    @keyword("Tool Result Should Have Data")
    def tool_result_should_have_data(self, result, msg=None):
        """Fails unless the result carries structured (JSON) content."""
        if convert.structured_content(result) is None:
            raise AssertionError(msg or "The tool result carries no structured content.")

    # -- resources --------------------------------------------------------

    @keyword("Resource Should Exist")
    def resource_should_exist(self, uri, msg=None):
        """Fails unless the server lists a resource with this URI.

        Example:
        | Resource Should Exist | docs://weather/usage |
        """
        uris = self.get_resource_uris()
        if uri not in uris:
            raise AssertionError(
                msg
                or f"The server does not expose a resource with the URI '{uri}'. "
                f"It exposes: {', '.join(uris) or 'no resources'}."
            )

    @keyword("Resource Should Not Exist")
    def resource_should_not_exist(self, uri, msg=None):
        """Fails if the server lists a resource with this URI."""
        if uri in self.get_resource_uris():
            raise AssertionError(
                msg or f"The server exposes a resource with the URI '{uri}', but should not."
            )

    @keyword("Resource Should Contain Text")
    def resource_should_contain_text(self, uri, expected, msg=None):
        """Reads a resource and fails unless its text contains ``expected``.

        Example:
        | Resource Should Contain Text | docs://weather/usage | get_weather |
        """
        actual = self.get_resource_text(uri)
        if expected not in actual:
            raise AssertionError(
                msg
                or f"The resource '{uri}' does not contain '{expected}'. "
                f"It contains: {actual or '(no text)'}"
            )

    # -- prompts ----------------------------------------------------------

    @keyword("Prompt Should Exist")
    def prompt_should_exist(self, name, msg=None):
        """Fails unless the server exposes a prompt with this name."""
        names = self.get_prompt_names()
        if name not in names:
            raise AssertionError(
                msg
                or f"The server does not expose a prompt named '{name}'. "
                f"It exposes: {', '.join(names) or 'no prompts'}."
            )

    @keyword("Prompt Should Not Exist")
    def prompt_should_not_exist(self, name, msg=None):
        """Fails if the server exposes a prompt with this name."""
        if name in self.get_prompt_names():
            raise AssertionError(
                msg or f"The server exposes a prompt named '{name}', but should not."
            )

    @keyword("Prompt Should Require Argument")
    def prompt_should_require_argument(self, name, *arguments, msg=None):
        """Fails unless the named prompt marks every given argument required."""
        prompt = self._require_prompt(name)
        required = [
            argument.name
            for argument in (getattr(prompt, "arguments", None) or [])
            if getattr(argument, "required", False)
        ]
        missing = [argument for argument in arguments if argument not in required]
        if missing:
            raise AssertionError(
                msg
                or f"The prompt '{name}' does not require {', '.join(missing)}. "
                f"It requires: {', '.join(required) or 'nothing'}."
            )

    # -- helpers ----------------------------------------------------------

    def _require_tool(self, name):
        tool = self._find_tool(name)
        if tool is None:
            raise AssertionError(
                f"The server does not expose a tool named '{name}'. "
                f"It exposes: {self._tool_names_text()}."
            )
        return tool

    def _require_prompt(self, name):
        result = self._connection.call(lambda s: s.list_prompts(), timeout=self._timeout(None))
        for prompt in result.prompts:
            if prompt.name == name:
                return prompt
        names = [p.name for p in result.prompts]
        raise AssertionError(
            f"The server does not expose a prompt named '{name}'. "
            f"It exposes: {', '.join(names) or 'no prompts'}."
        )
