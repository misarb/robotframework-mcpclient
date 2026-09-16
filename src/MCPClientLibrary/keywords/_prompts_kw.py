"""Keywords that list and render the prompts a server exposes."""

from robot.api.deco import keyword

from .. import _convert as convert
from .._logging import log_request, log_response


class PromptKeywords:
    @keyword("List Prompts")
    def list_prompts(self, timeout=None):
        """Returns every prompt the server exposes.

        Each prompt has ``name``, ``description`` and ``arguments``.
        """
        log_request("prompts/list")
        result = self._connection.call(lambda s: s.list_prompts(), timeout=self._timeout(timeout))
        log_response("prompts/list", result)
        return self._maybe_convert(list(result.prompts))

    @keyword("Get Prompt Names")
    def get_prompt_names(self, timeout=None):
        """Returns the names of the server's prompts as a list of strings."""
        log_request("prompts/list")
        result = self._connection.call(lambda s: s.list_prompts(), timeout=self._timeout(timeout))
        names = [prompt.name for prompt in result.prompts]
        log_response("prompts/list", names)
        return names

    @keyword("Get Prompt")
    def get_prompt(self, name, timeout=None, **arguments):
        """Renders a prompt with the given arguments and returns the result.

        The result has a ``messages`` list. For the text alone, use
        `Get Prompt Text`.

        Example:
        | ${prompt}= | Get Prompt | weather_report | city=Berlin |
        """
        arguments = {key: str(value) for key, value in arguments.items()}
        log_request("prompts/get", name=name, arguments=arguments)
        result = self._connection.call(
            lambda s: s.get_prompt(name, arguments), timeout=self._timeout(timeout)
        )
        log_response("prompts/get", result)
        return self._maybe_convert(result)

    @keyword("Get Prompt Text")
    def get_prompt_text(self, name, timeout=None, **arguments):
        """Renders a prompt and returns its messages joined into one string.

        Example:
        | ${text}= | Get Prompt Text | weather_report | city=Berlin |
        | Should Contain | ${text} | Berlin |
        """
        arguments = {key: str(value) for key, value in arguments.items()}
        log_request("prompts/get", name=name, arguments=arguments)
        result = self._connection.call(
            lambda s: s.get_prompt(name, arguments), timeout=self._timeout(timeout)
        )
        text = "\n".join(convert.message_text(m) for m in convert.prompt_messages(result))
        log_response("prompts/get", text)
        return text
