"""A server exercising edge cases in tool schemas and result payloads:
an empty input schema, a large text result, and unicode/special characters.
"""

import json
import sys

PROTOCOL_VERSION = "2025-06-18"

LARGE_PAYLOAD_SIZE = 200_000  # bytes of text, well past the log's truncation cutoff

TOOLS = [
    {
        "name": "minimal_schema_tool",
        "description": "Declares the minimal input schema: an object with no properties.",
        "inputSchema": {"type": "object"},
    },
    {
        "name": "large_result_tool",
        "description": "Returns a large text payload.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "unicode_tool",
        "description": "Returns text with unicode, emoji, and special characters.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "multi_block_tool",
        "description": "Returns several separate text content blocks.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def text_result(text, is_error=False):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def call_tool(name, arguments):
    if name == "minimal_schema_tool":
        return text_result("ok")
    if name == "large_result_tool":
        return text_result("x" * LARGE_PAYLOAD_SIZE)
    if name == "unicode_tool":
        return text_result('héllo wörld 你好 🎉 "quoted" \\backslash\\ \n newline\t tab')
    if name == "multi_block_tool":
        return {
            "content": [
                {"type": "text", "text": "first block"},
                {"type": "text", "text": "second block"},
                {"type": "text", "text": "third block"},
            ],
            "isError": False,
        }
    raise ValueError(f"Unknown tool: {name}")


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "edge-case-test-server", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        return call_tool(params["name"], params.get("arguments") or {})
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
