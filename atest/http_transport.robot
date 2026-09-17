*** Settings ***
Documentation       Connecting to an MCP server over streamable HTTP.

Library             Process
Library             MCPClientLibrary
Library             OperatingSystem

Suite Setup         Start The HTTP Weather Server
Suite Teardown      Stop The HTTP Weather Server And Disconnect


*** Variables ***
${SERVER_DIR}       ${CURDIR}/../tests/servers
${HTTP SERVER}      ${SERVER_DIR}/http_weather_server.py
${SERVER PORT}      ${EMPTY}
${SERVER URL}       ${EMPTY}


*** Test Cases ***
Connecting Over HTTP Runs The Handshake
    ${info}=    Get MCP Server Info
    Should Be Equal    ${info.name}    weather-http-test-server

Listing Tools Over HTTP
    ${names}=    Get Tool Names
    Should Contain    ${names}    get_weather
    Should Contain    ${names}    echo

Calling A Tool Over HTTP
    ${result}=    Call Tool    get_weather    city=Paris
    Tool Result Should Not Be Error    ${result}
    Tool Result Should Contain Text    ${result}    18 degrees

A Tool Error Over HTTP Sets The Error Flag
    ${result}=    Call Tool    get_weather    city=Nowhereville
    Tool Result Should Be Error    ${result}

Connecting To A URL With No Server Fails Clearly
    Run Keyword And Expect Error
    ...    *Could not connect to the MCP server*
    ...    Connect To MCP Server Over HTTP    http://127.0.0.1:1/mcp    timeout=5

Connecting With Custom Headers Does Not Fail The Handshake
    ${headers}=    Create Dictionary    X-Test-Header=hello
    ${index}=    Connect To MCP Server Over HTTP    ${SERVER URL}    headers=${headers}    alias=with_headers
    Switch MCP Server    with_headers
    Tool Should Exist    get_weather
    Disconnect From MCP Server    alias=with_headers


*** Keywords ***
Start The HTTP Weather Server
    ${port}=    Get Free Port
    Set Suite Variable    ${SERVER PORT}    ${port}
    Set Suite Variable    ${SERVER URL}    http://127.0.0.1:${port}/mcp

    ${handle}=    Start Process
    ...    ${INTERPRETER}    ${HTTP SERVER}    ${port}
    ...    stdout=${OUTPUT DIR}/http_server_stdout.log
    ...    stderr=${OUTPUT DIR}/http_server_stderr.log
    Set Suite Variable    ${SERVER HANDLE}    ${handle}

    Wait Until Keyword Succeeds    10x    0.5s    Connect To MCP Server Over HTTP    ${SERVER URL}

Stop The HTTP Weather Server And Disconnect
    Disconnect All MCP Servers
    Terminate Process    ${SERVER HANDLE}

Get Free Port
    ${result}=    Run Process    ${INTERPRETER}    ${SERVER_DIR}/find_free_port.py
    Should Be Equal As Integers    ${result.rc}    0
    RETURN    ${result.stdout.strip()}
