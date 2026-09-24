"""A server that connects and answers normally, then dies mid-call when asked to.

For testing what happens to the library and the test suite when a server
crashes after the handshake — not a clean shutdown, an abrupt process exit
partway through handling a request.
"""

import json
import os
import sys

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "healthy_tool",
        "description": "Answers normally.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "crash_now",
        "description": "Kills the server process immediately, before answering.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "crashing-test-server", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        if name == "crash_now":
            sys.stdout.flush()
            os._exit(1)  # abrupt: no cleanup, no final message, unlike sys.exit()
        if name == "healthy_tool":
            return {"content": [{"type": "text", "text": "still here"}], "isError": False}
        raise ValueError(f"Unknown tool: {name}")
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
