Keywords
========

MCPClientLibrary exposes 45 keywords across five categories.

Full reference: `MCPClientLibrary.html <_static/MCPClientLibrary.html>`_

Below is a summary with common keywords. For complete details including all parameters and examples, see the full reference above.

Connection Lifecycle
--------------------

**Connect To MCP Server** — Start an MCP server and complete the handshake.

.. code-block:: robotframework

    Connect To MCP Server    python    my_server.py
    Connect To MCP Server    node     server.js    --verbose
    Connect To MCP Server    python    server.py    env=${env}    cwd=${cwd}    alias=myserver

Arguments:
- ``command`` — Executable to run
- ``*args`` — Arguments to pass to the command
- ``env`` — Dictionary of environment variables (optional)
- ``cwd`` — Working directory (optional)
- ``alias`` — Name for this connection (for multi-server suites)
- ``timeout`` — Seconds to wait for the handshake (default: ``default_timeout``)

Returns: Connection index (integer)

**Connect To MCP Server Over HTTP** — Connect to a remote MCP server by URL.

.. code-block:: robotframework

    Connect To MCP Server Over HTTP    https://example.com/mcp

    ${headers}=    Create Dictionary    Authorization=Bearer ${TOKEN}
    Connect To MCP Server Over HTTP    https://example.com/mcp    headers=${headers}    alias=remote

Arguments:
- ``url`` — The server's MCP endpoint
- ``headers`` — Dictionary of extra HTTP headers, e.g. for authentication (optional)
- ``alias`` — Name for this connection (for multi-server suites)
- ``timeout`` — Seconds to wait for the handshake (default: ``default_timeout``)

Returns: Connection index (integer)

Every keyword below works the same regardless of which ``Connect To MCP
Server*`` keyword was used — tools, resources, prompts, and assertions don't
know which transport they're on.

**Disconnect From MCP Server** — Close a connection and stop the server.

.. code-block:: robotframework

    Disconnect From MCP Server
    Disconnect From MCP Server    alias=myserver

**Disconnect All MCP Servers** — Close all connections (use in suite teardown).

.. code-block:: robotframework

    Disconnect All MCP Servers

**Switch MCP Server** — Move between connections (for multi-server tests).

.. code-block:: robotframework

    Switch MCP Server    myserver
    Switch MCP Server    2

Arguments:
- ``alias_or_index`` — Name or index of the connection to switch to

Returns: Index of the previous connection

**Get MCP Server Info** — The name and version the server reported.

.. code-block:: robotframework

    ${info}=    Get MCP Server Info
    Should Be Equal    ${info.name}    my-server

**Get MCP Server Capabilities** — What the server declared it supports.

.. code-block:: robotframework

    ${caps}=    Get MCP Server Capabilities
    Should Not Be Equal    ${caps.tools}    ${None}

Tools
-----

**List Tools** — Every tool the server exposes.

.. code-block:: robotframework

    ${tools}=    List Tools
    Length Should Be    ${tools}    3

**Get Tool Names** — Just the names, as a list of strings.

.. code-block:: robotframework

    ${names}=    Get Tool Names
    Should Contain    ${names}    greet

**Get Tool** — One tool by name.

.. code-block:: robotframework

    ${tool}=    Get Tool    greet
    Should Be Equal    ${tool.description}    Greet someone

**Call Tool** — Execute a tool with named arguments.

.. code-block:: robotframework

    ${result}=    Call Tool    greet    name=Alice
    Tool Result Should Not Be Error    ${result}

**Call Tool With Arguments** — Execute a tool with an argument dictionary.

.. code-block:: robotframework

    ${args}=    Create Dictionary    name=Alice
    ${result}=    Call Tool With Arguments    greet    ${args}

**Get Tool Result Text** — The text blocks of a result, joined.

.. code-block:: robotframework

    ${text}=    Get Tool Result Text    ${result}
    Should Contain    ${text}    Alice

**Get Tool Result Data** — The structured (JSON) content of a result.

.. code-block:: robotframework

    ${data}=    Get Tool Result Data    ${result}

Tool Assertions
---------------

**Tool Should Exist** / **Tool Should Not Exist** — Check if a tool is offered.

.. code-block:: robotframework

    Tool Should Exist        greet
    Tool Should Not Exist    delete_all

**Tool Count Should Be** — How many tools the server offers.

.. code-block:: robotframework

    Tool Count Should Be    3

**Tool Should Have Input Schema** — Tool declares an input schema.

.. code-block:: robotframework

    Tool Should Have Input Schema    greet

**Tool Input Schema Should Require** — Schema marks fields required.

.. code-block:: robotframework

    Tool Input Schema Should Require    greet    name

**Tool Input Schema Should Have Property** — Schema declares properties.

.. code-block:: robotframework

    Tool Input Schema Should Have Property    greet    name    greeting_style

**Tool Should Have Description** — Tool has a non-empty description.

.. code-block:: robotframework

    Tool Should Have Description    greet

Tool Result Assertions
----------------------

**Tool Result Should Not Be Error** / **Tool Result Should Be Error** — Check error flag.

.. code-block:: robotframework

    Tool Result Should Not Be Error    ${result}
    Tool Result Should Be Error        ${error_result}

**Tool Result Should Contain Text** / **Should Not Contain Text** — Substring match.

.. code-block:: robotframework

    Tool Result Should Contain Text        ${result}    Alice
    Tool Result Should Not Contain Text    ${result}    error

**Tool Result Should Match** — Regular expression match.

.. code-block:: robotframework

    Tool Result Should Match    ${result}    .*Alice.*

**Tool Result Should Be Empty** / **Should Not Be Empty** — Content presence.

.. code-block:: robotframework

    Tool Result Should Not Be Empty    ${result}

**Tool Result Should Have Data** — Structured content present.

.. code-block:: robotframework

    Tool Result Should Have Data    ${result}

Resources
---------

**List Resources** — Every resource the server offers.

.. code-block:: robotframework

    ${resources}=    List Resources

**Get Resource URIs** — Just the URIs, as strings.

.. code-block:: robotframework

    ${uris}=    Get Resource URIs
    Should Contain    ${uris}    docs://greet/usage

**Read Resource** — Get a resource by URI.

.. code-block:: robotframework

    ${resource}=    Read Resource    docs://greet/usage

**Get Resource Text** — Resource text as a string.

.. code-block:: robotframework

    ${text}=    Get Resource Text    docs://greet/usage
    Should Contain    ${text}    greet

Resource Assertions
-------------------

**Resource Should Exist** / **Resource Should Not Exist** — Check if a URI is offered.

.. code-block:: robotframework

    Resource Should Exist        docs://greet/usage
    Resource Should Not Exist    docs://missing

**Resource Should Contain Text** — Check resource content.

.. code-block:: robotframework

    Resource Should Contain Text    docs://greet/usage    how to use

Prompts
-------

**List Prompts** — Every prompt the server offers.

.. code-block:: robotframework

    ${prompts}=    List Prompts

**Get Prompt Names** — Just the names, as strings.

.. code-block:: robotframework

    ${names}=    Get Prompt Names
    Should Contain    ${names}    greet_prompt

**Get Prompt** — Render a prompt with arguments.

.. code-block:: robotframework

    ${prompt}=    Get Prompt    greet_prompt    language=French

**Get Prompt Text** — Prompt messages as a string.

.. code-block:: robotframework

    ${text}=    Get Prompt Text    greet_prompt    language=French
    Should Contain    ${text}    Bonjour

Prompt Assertions
-----------------

**Prompt Should Exist** / **Prompt Should Not Exist** — Check if a prompt is offered.

.. code-block:: robotframework

    Prompt Should Exist        greet_prompt
    Prompt Should Not Exist    missing_prompt

**Prompt Should Require Argument** — Check required arguments.

.. code-block:: robotframework

    Prompt Should Require Argument    greet_prompt    language

Common Options
--------------

All keywords accept:

- ``timeout`` — Override the library's ``default_timeout`` for this keyword
- ``msg`` — Custom failure message (assertions only)

Example:

.. code-block:: robotframework

    Tool Should Exist    greet    msg=Expected greet tool but server does not offer it
    ${result}=    Call Tool    slow_tool    timeout=120
