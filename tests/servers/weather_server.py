"""A tiny MCP server used by the library's own acceptance tests.

Implements the JSON-RPC handshake and the three primitives directly over
stdio so the test fixtures do not depend on a server framework.
"""

import json
import sys

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "get_weather",
        "description": "Return the current weather for a city.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city"],
        },
    },
    {
        "name": "echo",
        "description": "Echo back the message it is given.",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
]

RESOURCES = [
    {
        "uri": "docs://weather/usage",
        "name": "Weather usage",
        "description": "How to use the weather tool.",
        "mimeType": "text/plain",
    }
]

PROMPTS = [
    {
        "name": "weather_report",
        "description": "Draft a weather report for a city.",
        "arguments": [{"name": "city", "description": "City name", "required": True}],
    }
]

KNOWN_CITIES = {"Paris": 18, "Berlin": 15, "Cairo": 33}


def text_result(text, is_error=False):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def call_tool(name, arguments):
    if name == "get_weather":
        city = arguments.get("city")
        if city not in KNOWN_CITIES:
            return text_result(f"Unknown city: {city}", is_error=True)
        return text_result(f"The temperature in {city} is {KNOWN_CITIES[city]} degrees.")
    if name == "echo":
        return text_result(arguments.get("message", ""))
    raise ValueError(f"Unknown tool: {name}")


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": {"name": "weather-test-server", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        return call_tool(params["name"], params.get("arguments") or {})
    if method == "resources/list":
        return {"resources": RESOURCES}
    if method == "resources/read":
        uri = params["uri"]
        if uri != "docs://weather/usage":
            raise ValueError(f"Unknown resource: {uri}")
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": "Call get_weather with a city name to get the temperature.",
                }
            ]
        }
    if method == "prompts/list":
        return {"prompts": PROMPTS}
    if method == "prompts/get":
        city = (params.get("arguments") or {}).get("city", "somewhere")
        return {
            "description": f"Weather report for {city}",
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": f"Write a weather report for {city}."},
                }
            ],
        }
    if method == "ping":
        return {}
    raise ValueError(f"Unknown method: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        request = json.loads(line)
        if "id" not in request:  # a notification; nothing to answer
            continue
        try:
            response = {"jsonrpc": "2.0", "id": request["id"], "result": handle(request)}
        except Exception as err:  # report as a JSON-RPC error
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "error": {"code": -32603, "message": str(err)},
            }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
