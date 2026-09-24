Keywords
========

MCPClientLibrary exposes 61 keywords across five categories.

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

Output Schema Validation
-------------------------

**Tool Result Should Match Output Schema** — Check a result's structured
content against the tool's own declared output schema.

.. code-block:: robotframework

    ${result}=    Call Tool    get_weather_structured    city=Paris
    Tool Result Should Match Output Schema    get_weather_structured    ${result}

On mcp 2.x, ``Call Tool`` already checks this itself and raises
``MCPValidationError`` if a result doesn't match — this keyword exists for
explicit checks in a test, and for SDK versions that don't check it on their
own.

Progress Capture
-----------------

**Get Last Tool Call Progress** — The progress notifications sent during the
most recent ``Call Tool``.

.. code-block:: robotframework

    Call Tool    process_file    filename=data.csv
    ${progress}=    Get Last Tool Call Progress
    Should Be Equal As Numbers    ${progress}[-1][progress]    100

**Tool Call Should Have Reported Progress** — Fails unless the most recent
call sent at least one progress notification.

.. code-block:: robotframework

    Call Tool    process_file    filename=data.csv
    Tool Call Should Have Reported Progress

Server Log Capture
--------------------

**Set Logging Level** — Ask the server to send log messages at a level or
more severe (``debug``, ``info``, ``notice``, ``warning``, ``error``,
``critical``, ``alert``, ``emergency``).

.. code-block:: robotframework

    Set Logging Level    debug

**Get Server Log Messages** / **Clear Server Log Messages** — Read or discard
the messages collected on the current connection.

.. code-block:: robotframework

    ${logs}=    Get Server Log Messages
    Length Should Be    ${logs}    1
    Clear Server Log Messages

**Server Should Have Logged** / **Server Should Not Have Logged** — Check a
collected message contains (or doesn't contain) given text, optionally
filtered to one level.

.. code-block:: robotframework

    Server Should Have Logged        unknown city    level=warning
    Server Should Not Have Logged    Traceback

Resource Subscriptions
------------------------

**Subscribe To Resource** / **Unsubscribe From Resource** — Ask the server to
notify the client when a resource changes.

.. code-block:: robotframework

    Subscribe To Resource    data://counter
    Call Tool    bump_counter
    Resource Should Have Been Updated    data://counter

**Get Resource Update Notifications** / **Clear Resource Update
Notifications** — Read or discard the URIs of every update notification
received.

.. code-block:: robotframework

    ${updates}=    Get Resource Update Notifications
    Should Contain    ${updates}    data://counter

**Resource Should Have Been Updated** — Fails unless an update notification
for the given URI was received.

Client Callbacks
------------------

MCP lets a server call back into the client mid-tool-call: to ask what
directories/URIs it exposes (roots), to have the client's LLM complete a
message (sampling — the pattern behind an agentic tool), or to ask the user
a question (elicitation). These keywords script the client's side of that
conversation so the server-side tool can be tested without a real LLM or a
real user watching.

**Set Client Roots** — Declares the roots the client answers ``roots/list``
with, from then on for the connection.

.. code-block:: robotframework

    ${root}=    Create Dictionary    uri=file:///workspace    name=Project
    Set Client Roots    ${root}
    ${result}=    Call Tool    list_project_files

Call with no arguments to reset to an empty list.

**Set Sampling Response** — Queues the text the client returns for the
server's *next* sampling request. Consumed once.

.. code-block:: robotframework

    Set Sampling Response    42
    ${result}=    Call Tool    agentic_tool    query=what is 6 times 7

**Set Elicitation Response** — Queues the answer the client gives to the
server's *next* elicitation request: ``accept``, ``decline``, or ``cancel``,
with a ``content`` dictionary for ``accept``. Consumed once.

.. code-block:: robotframework

    ${answer}=    Create Dictionary    name=Alice
    Set Elicitation Response    accept    ${answer}
    ${result}=    Call Tool    tool_that_asks_for_a_name

A server that asks and finds nothing queued gets a clear error back
explaining what to call first — not a hang, and not a stale answer from an
earlier test.

Common Options
--------------

All keywords accept:

- ``timeout`` — Override the library's ``default_timeout`` for this keyword
- ``msg`` — Custom failure message (assertions only)

Example:

.. code-block:: robotframework

    Tool Should Exist    greet    msg=Expected greet tool but server does not offer it
    ${result}=    Call Tool    slow_tool    timeout=120
