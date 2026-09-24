"""A server that calls back into the client: asks for roots, asks the client
to sample a message, asks the client to elicit input from the user, and
sends a resource update notification after a subscribed resource changes.

Hand-rolled JSON-RPC, with its own outgoing request ids kept out of the
client's id space (starting at 9000) so replies are easy to recognise.
"""

import itertools
import json
import sys

PROTOCOL_VERSION = "2025-06-18"
_next_id = itertools.count(9000)

TOOLS = [
    {
        "name": "list_project_roots",
        "description": "Asks the client for its configured roots and reports how many it has.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "ask_llm",
        "description": "Asks the client to sample a message and echoes the answer back.",
        "inputSchema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
    {
        "name": "ask_for_name",
        "description": "Elicits a name from the user and greets them.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "bump_counter",
        "description": "Increments a counter and notifies subscribers of the change.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

RESOURCES = [
    {
        "uri": "data://counter",
        "name": "Counter",
        "description": "A counter that changes when bump_counter is called.",
        "mimeType": "text/plain",
    }
]


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def call_client(method, params):
    """Sends a server->client request and blocks (via the stdin loop) for the reply."""
    request_id = next(_next_id)
    send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if msg.get("id") == request_id and "method" not in msg:
            return msg
        # Anything else arriving while we wait (a notification, e.g.) is
        # simply dropped in this fixture; nothing sends one in that window.


def handle_call_tool(request_id, params):
    name = params.get("name")
    if name == "list_project_roots":
        reply = call_client("roots/list", {})
        if "error" in reply:
            text = f"error asking for roots: {reply['error']['message']}"
        else:
            roots = reply["result"]["roots"]
            text = f"{len(roots)} root(s): " + ", ".join(r["uri"] for r in roots)
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": text}], "isError": False},
            }
        )
    elif name == "ask_llm":
        question = (params.get("arguments") or {}).get("question", "")
        reply = call_client(
            "sampling/createMessage",
            {
                "messages": [{"role": "user", "content": {"type": "text", "text": question}}],
                "maxTokens": 100,
            },
        )
        if "error" in reply:
            error_text = f"sampling failed: {reply['error']['message']}"
            send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": error_text}],
                        "isError": True,
                    },
                }
            )
        else:
            answer = reply["result"]["content"]["text"]
            send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": f"The model said: {answer}"}],
                        "isError": False,
                    },
                }
            )
    elif name == "ask_for_name":
        reply = call_client(
            "elicitation/create",
            {
                "message": "What is your name?",
                "requestedSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
            },
        )
        if "error" in reply:
            text = f"elicitation failed: {reply['error']['message']}"
        else:
            action = reply["result"]["action"]
            if action == "accept":
                who = reply["result"]["content"]["name"]
                text = f"Hello, {who}!"
            else:
                text = f"The user did not answer (action: {action})."
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": text}], "isError": False},
            }
        )
    elif name == "bump_counter":
        send(
            {
                "jsonrpc": "2.0",
                "method": "notifications/resources/updated",
                "params": {"uri": "data://counter"},
            }
        )
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": "bumped"}], "isError": False},
            }
        )
    else:
        raise ValueError(f"Unknown tool: {name}")


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}
    request_id = request.get("id")

    if method == "initialize":
        return request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {"subscribe": True}},
            "serverInfo": {"name": "callback-test-server", "version": "1.0.0"},
        }
    if method == "tools/list":
        return request_id, {"tools": TOOLS}
    if method == "tools/call":
        handle_call_tool(request_id, params)
        return None, None  # response already sent inside handle_call_tool
    if method == "resources/list":
        return request_id, {"resources": RESOURCES}
    if method == "resources/subscribe":
        return request_id, {}
    if method == "resources/unsubscribe":
        return request_id, {}
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
