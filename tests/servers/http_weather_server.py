"""A weather-tool MCP server exposed over streamable HTTP.

Same tools as weather_server.py (stdio), used to test the HTTP transport.
Takes the port as its first argument so tests can pick a free one.
"""

import sys

from mcp.server.mcpserver import MCPServer

KNOWN_CITIES = {"Paris": 18, "Berlin": 15, "Cairo": 33}

server = MCPServer("weather-http-test-server", version="1.0.0")


@server.tool()
def get_weather(city: str, units: str = "celsius") -> str:
    """Return the current weather for a city."""
    if city not in KNOWN_CITIES:
        raise ValueError(f"Unknown city: {city}")
    return f"The temperature in {city} is {KNOWN_CITIES[city]} degrees."


@server.tool()
def echo(message: str) -> str:
    """Echo back the message it is given."""
    return message


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server.run(transport="streamable-http", port=port)
