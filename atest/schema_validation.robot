*** Settings ***
Documentation       Validating a tool result's structured content against its declared output schema.
...
...                 On mcp 2.x, ClientSession.call_tool() already checks this itself and raises
...                 before a mismatched result is ever returned — see the mismatch tests below,
...                 which assert on Call Tool failing rather than on the assertion keyword. The
...                 assertion keyword (Tool Result Should Match Output Schema) exists for explicit,
...                 self-documenting checks in a test, and for SDK versions (mcp 1.x) that never
...                 check this on their own.

Library             Process
Library             MCPClientLibrary

Suite Setup         Start The Servers
Suite Teardown      Stop The Servers And Disconnect


*** Variables ***
${SERVER_DIR}           ${CURDIR}/../tests/servers
${HTTP SERVER}          ${SERVER_DIR}/http_weather_server.py
${STDIO SERVER}         ${SERVER_DIR}/weather_server.py
${MISMATCH SERVER}      ${SERVER_DIR}/schema_mismatch_server.py
${SERVER URL}           ${EMPTY}


*** Test Cases ***
A Tool With An Output Schema Declares It
    Switch MCP Server    http
    Tool Should Have Input Schema    get_weather_structured
    ${tool}=    Get Tool    get_weather_structured
    Should Not Be Equal    ${tool.output_schema}    ${None}

Matching Structured Content Passes Validation
    Switch MCP Server    http
    ${result}=    Call Tool    get_weather_structured    city=Paris
    Tool Result Should Have Data    ${result}
    Tool Result Should Match Output Schema    get_weather_structured    ${result}

Structured Content Includes The Expected Fields
    Switch MCP Server    http
    ${result}=    Call Tool    get_weather_structured    city=Berlin    units=celsius
    ${data}=    Get Tool Result Data    ${result}
    Should Be Equal    ${data}[city]    Berlin
    Should Be Equal As Integers    ${data}[temperature]    15

Validating Against A Tool With No Output Schema Fails Clearly
    # weather_server.py is hand-rolled JSON-RPC and genuinely declares no
    # outputSchema, unlike the HTTP server's tools (the SDK's tool decorator
    # auto-generates one even for a plain string return).
    Switch MCP Server    stdio
    ${result}=    Call Tool    get_weather    city=Paris
    Run Keyword And Expect Error
    ...    *does not declare an output schema*
    ...    Tool Result Should Match Output Schema    get_weather    ${result}

A Custom Message Replaces The Default Schema Failure Text
    Switch MCP Server    stdio
    ${result}=    Call Tool    get_weather    city=Paris
    Run Keyword And Expect Error
    ...    get_weather has no schema to check.
    ...    Tool Result Should Match Output Schema    get_weather    ${result}
    ...    msg=get_weather has no schema to check.

Calling A Tool Whose Result Violates Its Own Schema Fails The Call
    # On mcp 2.x, ClientSession.call_tool() validates structured content
    # against the tool's declared schema itself — this is Call Tool raising,
    # not Tool Result Should Match Output Schema, because a mismatched result
    # never comes back to check.
    Switch MCP Server    mismatch
    Run Keyword And Expect Error
    ...    *does not match its own declared output schema*
    ...    Call Tool    get_weather_structured    city=Paris


*** Keywords ***
Start The Servers
    ${port}=    Get Free Port
    Set Suite Variable    ${SERVER URL}    http://127.0.0.1:${port}/mcp

    ${handle}=    Start Process
    ...    ${INTERPRETER}    ${HTTP SERVER}    ${port}
    ...    stdout=${OUTPUT DIR}/schema_http_server_stdout.log
    ...    stderr=${OUTPUT DIR}/schema_http_server_stderr.log
    Set Suite Variable    ${SERVER HANDLE}    ${handle}

    Wait Until Keyword Succeeds    10x    0.5s
    ...    Connect To MCP Server Over HTTP    ${SERVER URL}    alias=http

    Connect To MCP Server    ${INTERPRETER}    ${STDIO SERVER}    alias=stdio
    Connect To MCP Server    ${INTERPRETER}    ${MISMATCH SERVER}    alias=mismatch

Stop The Servers And Disconnect
    Disconnect All MCP Servers
    Terminate Process    ${SERVER HANDLE}

Get Free Port
    ${result}=    Run Process    ${INTERPRETER}    ${SERVER_DIR}/find_free_port.py
    Should Be Equal As Integers    ${result.rc}    0
    RETURN    ${result.stdout.strip()}
