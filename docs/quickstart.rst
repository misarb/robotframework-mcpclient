Quick Start
===========

Your First Test (5 Minutes)
---------------------------

**1. Create a simple MCP server**

Create ``my_server.py``:

.. code-block:: python

    import json
    import sys

    def handle(request):
        method = request.get("method")
        if method == "initialize":
            return {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "my-server", "version": "1.0.0"},
            }
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "greet",
                        "description": "Greet someone",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"],
                        },
                    }
                ]
            }
        if method == "tools/call":
            name = (request.get("params") or {}).get("arguments", {}).get("name", "World")
            return {
                "content": [{"type": "text", "text": f"Hello, {name}!"}],
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

**2. Write a test**

Create ``test_greet.robot``:

.. code-block:: robotframework

    *** Settings ***
    Library           MCPClientLibrary
    Suite Setup       Connect To MCP Server    python    my_server.py
    Suite Teardown    Disconnect All MCP Servers

    *** Test Cases ***
    Server Has Greet Tool
        Tool Should Exist    greet

    Greet Tool Works
        ${result}=    Call Tool    greet    name=Alice
        Tool Result Should Not Be Error    ${result}
        Tool Result Should Contain Text    ${result}    Hello, Alice!

**3. Run the test**

.. code-block:: bash

    robot test_greet.robot

You should see:

.. code-block:: text

    test_greet ::
    Server Has Greet Tool                                  PASS
    Greet Tool Works                                       PASS

    2 tests, 2 passed

Next: Read the :doc:`keywords` reference to explore what the library can do.
