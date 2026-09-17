"""A server whose tool declares an output schema its own result doesn't
match, for testing that Tool Result Should Match Output Schema catches it.

Hand-rolled JSON-RPC (like weather_server.py) so the schema and the returned
data are both under direct control, with nothing from the SDK's own tool
decorator in between.
"""

import json
import sys

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "get_weather_structured",
        "description": "Claims to return {city, temperature, units} but doesn't.",
        "inputSchema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "temperature": {"type": "integer"},
                "units": {"type": "string"},
            },
            "required": ["city", "temperature", "units"],
        },
    }
]


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "schema-mismatch-test-server", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        if params["name"] != "get_weather_structured":
            raise ValueError(f"Unknown tool: {params['name']}")
        # Missing "temperature" and wrong type for "units": violates the
        # declared output schema on purpose.
        bad_data = {"city": params.get("arguments", {}).get("city", "Nowhere"), "units": 42}
        return {
            "content": [{"type": "text", "text": json.dumps(bad_data)}],
            "structuredContent": bad_data,
            "isError": False,
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
        if "id" not in request:
            continue
        try:
            response = {"jsonrpc": "2.0", "id": request["id"], "result": handle(request)}
        except Exception as err:
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "error": {"code": -32603, "message": str(err)},
            }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
