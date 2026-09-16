"""MCPClientLibrary — a Robot Framework library for testing MCP servers."""

from robot.api.deco import library
from robot.utils import ConnectionCache

from ._bridge import AsyncBridge
from ._convert import to_dict
from .errors import MCPConnectionError, MCPLibraryError, MCPTimeoutError
from .keywords import (
    AssertionKeywords,
    ConnectionKeywords,
    PromptKeywords,
    ResourceKeywords,
    ToolKeywords,
)
from .version import VERSION

__version__ = VERSION
__all__ = ["MCPClientLibrary", "MCPLibraryError", "MCPConnectionError", "MCPTimeoutError"]


@library(scope="GLOBAL", version=VERSION, doc_format="ROBOT")
class MCPClientLibrary(
    ConnectionKeywords,
    ToolKeywords,
    ResourceKeywords,
    PromptKeywords,
    AssertionKeywords,
):
    """A Robot Framework library for testing MCP (Model Context Protocol) servers.

    MCPClientLibrary starts an MCP server, speaks the protocol to it, and gives
    you keywords to check what it exposes and what it returns — so a server can
    be tested the same way as any other interface, without writing async code.

    = Getting started =

    Start the server in a suite setup, close it in a suite teardown, and write
    tests against it in between:

    | *** Settings ***
    | Library           MCPClientLibrary
    | Suite Setup       Connect To MCP Server    python    ${CURDIR}/weather_server.py
    | Suite Teardown    Disconnect All MCP Servers
    |
    | *** Test Cases ***
    | Server Exposes The Weather Tool
    |     Tool Should Exist                   get_weather
    |     Tool Should Have Input Schema       get_weather
    |     Tool Input Schema Should Require    get_weather    city
    |
    | Weather Tool Answers For A Known City
    |     ${result}=    Call Tool    get_weather    city=Paris
    |     Tool Result Should Not Be Error     ${result}
    |     Tool Result Should Contain Text     ${result}    temperature
    |
    | Unknown City Is Reported As A Tool Error
    |     ${result}=    Call Tool    get_weather    city=Nowhereville
    |     Tool Result Should Be Error         ${result}

    = What the keywords cover =

    - *Lifecycle* — `Connect To MCP Server`, `Disconnect From MCP Server`,
      `Disconnect All MCP Servers`, `Switch MCP Server`.
    - *Tools* — `List Tools`, `Get Tool Names`, `Call Tool`, and assertions for
      existence, schemas, descriptions and results.
    - *Resources* — `List Resources`, `Read Resource`, `Get Resource Text`.
    - *Prompts* — `List Prompts`, `Get Prompt`, `Get Prompt Text`.

    = Errors, and why you should not read the error flag yourself =

    An MCP tool reports its own failures by setting an error flag on an
    otherwise normal result — that is not a protocol error. Protocol and
    transport problems are different: they fail the keyword outright.

    Check the flag with `Tool Result Should Be Error` and
    `Tool Result Should Not Be Error` rather than reading the attribute. The
    field has been spelled `isError` and `is_error` in different versions of
    the MCP SDK; these keywords handle both, so your tests survive an upgrade.

    = Testing several servers at once =

    Give each connection an alias and move between them:

    | Connect To MCP Server    python    weather.py    alias=weather
    | Connect To MCP Server    python    notes.py      alias=notes
    | Switch MCP Server        weather
    | Tool Should Exist        get_weather

    = Importing =

    | Argument | Default | Description |
    | ``default_timeout`` | ``30`` | Seconds to wait for a server response. |
    | ``convert_results`` | ``False`` | Return dictionaries instead of MCP objects. |

    Every keyword takes a ``timeout`` that overrides ``default_timeout``.

    With the default, results are MCP objects and you reach into them with
    Robot's extended variable syntax (``${result.content}``). With
    ``convert_results=True`` they are dictionaries (``${result}[content]``),
    which suits data-driven suites and JSON comparison.

    | Library    MCPClientLibrary    default_timeout=60    convert_results=True
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = VERSION

    def __init__(self, default_timeout=30, convert_results=False):
        self._bridge = AsyncBridge()
        self._cache = ConnectionCache(no_current_msg="No MCP server is connected.")
        self._default_timeout = float(default_timeout)
        self._convert_results = bool(convert_results)

    # -- shared plumbing for the keyword mixins ---------------------------

    @property
    def _connection(self):
        """The current connection, or a clear failure if there is none."""
        return self._cache.current

    def _timeout(self, timeout):
        return self._default_timeout if timeout is None else float(timeout)

    def _maybe_convert(self, value):
        return to_dict(value) if self._convert_results else value

    # -- Robot lifecycle hook ---------------------------------------------

    def _close(self):
        """Called by Robot when the library goes out of scope."""
        try:
            self._cache.close_all("close")
        finally:
            self._bridge.shutdown()
