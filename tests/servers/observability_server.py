"""A server that sends progress notifications from a tool call and log
messages after logging/setLevel, for testing progress and log capture.

Hand-rolled JSON-RPC so both notification kinds are under direct control.
"""

import json
import sys

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "process_file",
        "description": "Processes a file in three steps, reporting progress on each.",
        "inputSchema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
    },
    {
        "name": "quiet_tool",
        "description": "Does its job without reporting any progress.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

PROGRESS_STEPS = (33, 66, 100)


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def handle_call_tool(request_id, params):
    name = params.get("name")
    if name == "process_file":
        token = (params.get("_meta") or {}).get("progressToken")
        if token is not None:
            for pct in PROGRESS_STEPS:
                send(
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/progress",
                        "params": {
                            "progressToken": token,
                            "progress": pct,
                            "total": 100,
                            "message": f"{pct}% done",
                        },
                    }
                )
        filename = (params.get("arguments") or {}).get("filename", "unknown")
        result = {
            "content": [{"type": "text", "text": f"Processed {filename}."}],
            "isError": False,
        }
    elif name == "quiet_tool":
        result = {"content": [{"type": "text", "text": "done"}], "isError": False}
    else:
        raise ValueError(f"Unknown tool: {name}")
    send({"jsonrpc": "2.0", "id": request_id, "result": result})


def handle_set_level(request_id, params):
    level = params.get("level", "info")
    # Acknowledge the request first, then emit a log message at that level so
    # a test that just set the level sees a message caused by its own action.
    send({"jsonrpc": "2.0", "id": request_id, "result": {}})
    send(
        {
            "jsonrpc": "2.0",
            "method": "notifications/message",
            "params": {
                "level": level,
                "logger": "observability-test-server",
                "data": f"log level set to {level}",
            },
        }
    )


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}
    request_id = request.get("id")

    if method == "initialize":
        return (
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}, "logging": {}},
                "serverInfo": {"name": "observability-test-server", "version": "1.0.0"},
            },
        )
    if method == "tools/list":
        return request_id, {"tools": TOOLS}
    if method == "tools/call":
        handle_call_tool(request_id, params)
        return None, None  # response already sent (progress notifications first)
    if method == "logging/setLevel":
        handle_set_level(request_id, params)
        return None, None  # response already sent (log notification after)
    if method == "ping":
        return request_id, {}
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
            request_id, result = handle(request)
            if request_id is not None:
                send({"jsonrpc": "2.0", "id": request_id, "result": result})
        except Exception as err:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "error": {"code": -32603, "message": str(err)},
                }
            )


if __name__ == "__main__":
    main()
