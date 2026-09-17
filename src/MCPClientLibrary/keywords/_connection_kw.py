"""Keywords that start, switch, and stop MCP server connections."""

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
