"""Keywords that start, switch, and stop MCP server connections."""

import warnings

from robot.api.deco import keyword

from .._connection import MCPConnection
from .._logging import log_info


class ConnectionKeywords:
    @keyword("Connect To MCP Server")
    def connect_to_mcp_server(self, command, *args, env=None, cwd=None, alias=None, timeout=None):
        """Starts an MCP server as a subprocess and completes the handshake.

        ``command`` is the executable to run and ``args`` are its arguments, so
        a Python server is started as ``python    my_server.py``. ``env`` takes
        a dictionary of extra environment variables, ``cwd`` the working
        directory for the subprocess.

        Give an ``alias`` to keep several servers connected at once and move
        between them with `Switch MCP Server`. Returns the connection index.

        Example:
        | Connect To MCP Server | python | ${CURDIR}/weather_server.py |
        | Connect To MCP Server | node | server.js | alias=notes |
        """
        connection = MCPConnection(
            self._bridge,
            transport="stdio",
            command=command,
            args=list(args),
            env=dict(env) if env else None,
            cwd=cwd,
        )
        connection.open(timeout=self._timeout(timeout))
        connection.alias = alias
        index = self._cache.register(connection, alias)
        name = getattr(connection.server_info, "name", "unknown")
        version = getattr(connection.server_info, "version", "")
        log_info(f"Connected to MCP server '{name}' {version} (index {index}).")
        return index

    @keyword("Connect To MCP Server Over HTTP")
    def connect_to_mcp_server_over_http(self, url, headers=None, alias=None, timeout=None):
        """Connects to a remote MCP server over streamable HTTP.

        ``url`` is the server's MCP endpoint. ``headers`` takes a dictionary of
        extra HTTP headers, for authentication (a bearer token, an API key).

        Give an ``alias`` to keep several servers connected at once and move
        between them with `Switch MCP Server`. Returns the connection index.

        Example:
        | Connect To MCP Server Over HTTP | https://example.com/mcp |
        | ${headers}= | Create Dictionary | Authorization=Bearer secret-token |
        | Connect To MCP Server Over HTTP | https://example.com/mcp | headers=${headers} |
        """
        connection = MCPConnection(
            self._bridge,
            transport="http",
            url=url,
            headers=dict(headers) if headers else None,
        )
        connection.open(timeout=self._timeout(timeout))
        connection.alias = alias
        index = self._cache.register(connection, alias)
        name = getattr(connection.server_info, "name", "unknown")
        version = getattr(connection.server_info, "version", "")
        log_info(f"Connected to MCP server '{name}' {version} over HTTP (index {index}).")
        return index

    @keyword("Disconnect From MCP Server")
    def disconnect_from_mcp_server(self, alias=None):
        """Closes one MCP connection and stops its server process.

        Closes the current connection unless an ``alias`` is given.
        """
        connection = self._cache.switch(alias) if alias else self._cache.current
        connection.close()
        log_info("Disconnected from the MCP server.")

    @keyword("Disconnect All MCP Servers")
    def disconnect_all_mcp_servers(self):
        """Closes every open connection. Use this as a suite teardown.

        Never fails, so a broken connection cannot hide the real failure in a
        test, and no server process is left behind between runs.
        """
        self._cache.close_all("close")
        log_info("Disconnected from all MCP servers.")

    @keyword("Switch MCP Server")
    def switch_mcp_server(self, alias_or_index):
        """Makes another connection the current one.

        Takes the alias given to `Connect To MCP Server` or the index it
        returned. Returns the index of the previous connection, so a test can
        switch back.
        """
        previous = self._cache.current_index
        self._cache.switch(alias_or_index)
        return previous

    @keyword("Get MCP Server Info")
    def get_mcp_server_info(self):
        """Returns the name and version the server reported at connect time.

        Example:
        | ${info}= | Get MCP Server Info |
        | Should Be Equal | ${info.name} | weather-server |
        """
        return self._connection.server_info

    @keyword("Get MCP Server Capabilities")
    def get_mcp_server_capabilities(self):
        """Returns the capabilities the server declared during the handshake.

        Use it to check that a server offers a primitive at all:
        | ${caps}= | Get MCP Server Capabilities |
        | Should Not Be Equal | ${caps.tools} | ${None} |
        """
        return self._connection.capabilities

    @keyword("MCP Server Should Be Connected")
    def mcp_server_should_be_connected(self, msg=None):
        """Fails if there is no open MCP session."""
        connection = self._cache.current if self._cache.current_index else None
        if connection is None or not connection.is_open:
            raise AssertionError(msg or "No MCP server is connected.")

    @keyword("Set Logging Level")
    def set_logging_level(self, level, timeout=None):
        """Asks the server to send log messages at ``level`` or more severe.

        ``level`` is one of ``debug``, ``info``, ``notice``, ``warning``,
        ``error``, ``critical``, ``alert``, ``emergency`` (least to most
        severe), per the MCP logging levels. Messages the server sends
        afterward are collected by `Get Server Log Messages`.

        A server that does not declare the ``logging`` capability will reject
        this with a protocol error — check `Get MCP Server Capabilities`
        first if that's a possibility.

        The MCP logging capability itself is deprecated in the spec (as of
        2026-07-28, SEP-2577) though still widely implemented; the underlying
        SDK call emits a deprecation warning, not an error, and this keyword
        keeps working against any server that still supports it.

        Example:
        | Set Logging Level | debug |
        | Call Tool | get_weather | city=Paris |
        | ${logs}= | Get Server Log Messages |
        """
        log_info(f"Requesting server log level '{level}'.")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._connection.call(
                lambda s: s.set_logging_level(level), timeout=self._timeout(timeout)
            )

    @keyword("Get Server Log Messages")
    def get_server_log_messages(self):
        """Returns every log message the server has sent this connection.

        Each entry is a dictionary with ``level``, ``logger`` (may be
        ``None``), and ``data`` (the message payload — its shape is up to the
        server). Messages accumulate for the life of the connection; use
        `Clear Server Log Messages` to reset between test cases if needed.

        Most servers only send messages at or above the level requested with
        `Set Logging Level`, so call that first if the list stays empty.

        Example:
        | ${logs}= | Get Server Log Messages |
        | Length Should Be | ${logs} | 1 |
        | Should Be Equal | ${logs}[0][level] | warning |
        """
        return [
            {"level": m.level, "logger": m.logger, "data": m.data}
            for m in self._connection.log_messages
        ]

    @keyword("Clear Server Log Messages")
    def clear_server_log_messages(self):
        """Discards every log message collected so far on the current connection.

        Use this between test cases in the same suite so each test only sees
        the log messages its own actions caused.
        """
        self._connection.log_messages.clear()

    @keyword("Set Client Roots")
    def set_client_roots(self, *roots):
        """Sets the directories/URIs the client exposes to the server as its roots.

        Each root is a dictionary with ``uri`` (required) and ``name``
        (optional). Answers the server's ``roots/list`` request from then on,
        for this connection; call again to change them mid-suite.

        MCP roots are typically file:// URIs marking a project's boundaries,
        so a server knows what it's allowed to touch — a test simulates that
        boundary without a real filesystem layout.

        Example:
        | ${root}= | Create Dictionary | uri=file:///workspace | name=Project |
        | Set Client Roots | ${root} |
        | Call Tool | list_project_files |
        """
        self._connection.roots = [dict(root) for root in roots]

    @keyword("Set Sampling Response")
    def set_sampling_response(self, text, model=None):
        """Queues the text the client returns for the server's next sampling request.

        MCP sampling lets a server ask the client's LLM to complete a
        message — the pattern behind an agentic tool. This keyword scripts
        what "the LLM" says back, so that tool can be tested without a real
        model: consumed once, by the next ``sampling/createMessage`` request
        this connection receives, then cleared.

        If the server asks to sample and nothing has been queued, the client
        answers with an error explaining that, rather than silently reusing
        a stale response or hanging.

        Example:
        | Set Sampling Response | 42 |
        | ${result}= | Call Tool | agentic_tool | query=what is 6 times 7 |
        """
        self._connection.pending_sampling_response = {"text": text, "model": model}

    @keyword("Set Elicitation Response")
    def set_elicitation_response(self, action, content=None):
        """Queues the answer the client gives to the server's next elicitation request.

        MCP elicitation lets a server pause mid-call to ask the user for more
        information. ``action`` is ``accept``, ``decline``, or ``cancel``;
        ``content`` is a dictionary of the requested fields, given when
        ``action`` is ``accept``. Consumed once, same as
        `Set Sampling Response`.

        Example:
        | ${answer}= | Create Dictionary | name=Alice |
        | Set Elicitation Response | accept | ${answer} |
        | ${result}= | Call Tool | tool_that_asks_for_a_name |
        """
        self._connection.pending_elicitation_response = {
            "action": action,
            "content": dict(content) if content else None,
        }
