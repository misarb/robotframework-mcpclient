"""A server whose 'hang' tool never answers, for testing keyword timeouts."""

import json
import sys
import time

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "hang",
        "description": "Never returns.",
        "inputSchema": {"type": "object", "properties": {}},
    }
]


def handle(request):
    method = request.get("method")
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "slow-test-server", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        time.sleep(300)  # the keyword timeout must fire long before this
        return {"content": [], "isError": False}
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
