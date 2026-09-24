*** Settings ***
Documentation       What happens when a server crashes mid-call: the failing keyword, the
...                 connection's state afterward, and reconnecting to recover.

Resource            resources/common.resource

Test Teardown       Disconnect All MCP Servers


*** Variables ***
${CRASHING SERVER}      ${SERVER_DIR}/crashing_server.py


*** Test Cases ***
A Healthy Call Works Before Any Crash
    Connect To MCP Server    ${INTERPRETER}    ${CRASHING SERVER}
    ${result}=    Call Tool    healthy_tool
    Tool Result Should Contain Text    ${result}    still here

A Crash Mid Call Fails The Keyword Clearly
    Connect To MCP Server    ${INTERPRETER}    ${CRASHING SERVER}
    Run Keyword And Expect Error
    ...    *connection closed unexpectedly*it may have crashed*
    ...    Call Tool    crash_now    timeout=5

MCP Server Should Be Connected Reflects A Crash
    Connect To MCP Server    ${INTERPRETER}    ${CRASHING SERVER}
    MCP Server Should Be Connected
    Run Keyword And Ignore Error    Call Tool    crash_now    timeout=5
    Run Keyword And Expect Error
    ...    No MCP server is connected.
    ...    MCP Server Should Be Connected

A Second Call After A Crash Fails Without Touching The Dead Process
    Connect To MCP Server    ${INTERPRETER}    ${CRASHING SERVER}
    Run Keyword And Ignore Error    Call Tool    crash_now    timeout=5
    Run Keyword And Expect Error
    ...    The MCP session is not open. Use 'Connect To MCP Server' first.
    ...    Call Tool    healthy_tool

Reconnecting Under The Same Alias Recovers The Suite
    Connect To MCP Server    ${INTERPRETER}    ${CRASHING SERVER}    alias=crashy
    Run Keyword And Ignore Error    Call Tool    crash_now    timeout=5

    Connect To MCP Server    ${INTERPRETER}    ${CRASHING SERVER}    alias=crashy
    Switch MCP Server    crashy
    ${result}=    Call Tool    healthy_tool
    Tool Result Should Contain Text    ${result}    still here

Disconnect All Is Safe With A Dead Connection In The Cache
    Connect To MCP Server    ${INTERPRETER}    ${CRASHING SERVER}    alias=crashy
    Run Keyword And Ignore Error    Call Tool    crash_now    timeout=5
    Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}    alias=weather
    Disconnect All MCP Servers
    Run Keyword And Expect Error    No MCP server is connected.    List Tools
