"""A server that exposes no tools, resources, or prompts at all.

For testing that the library handles an empty capability correctly — the
common shape of a server that's still under construction, or one that only
exposes a subset of the three primitives.
"""

import json
import sys

PROTOCOL_VERSION = "2025-06-18"


def handle(request):
    method = request.get("method")

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": {"name": "empty-test-server", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {"tools": []}
    if method == "resources/list":
        return {"resources": []}
    if method == "prompts/list":
        return {"prompts": []}
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
