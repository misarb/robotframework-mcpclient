*** Settings ***
Documentation       Empty capability lists, minimal schemas, large payloads, and unicode text.

Resource            resources/common.resource


*** Variables ***
${EMPTY SERVER}         ${SERVER_DIR}/empty_server.py
${EDGE CASE SERVER}     ${SERVER_DIR}/edge_case_server.py


*** Test Cases ***
An Empty Server Exposes No Tools
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EMPTY SERVER}
    ${tools}=    List Tools
    Should Be Empty    ${tools}
    ${names}=    Get Tool Names
    Should Be Empty    ${names}
    Tool Count Should Be    0
    [Teardown]    Disconnect All MCP Servers

An Empty Server Exposes No Resources
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EMPTY SERVER}
    ${resources}=    List Resources
    Should Be Empty    ${resources}
    ${uris}=    Get Resource URIs
    Should Be Empty    ${uris}
    [Teardown]    Disconnect All MCP Servers

An Empty Server Exposes No Prompts
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EMPTY SERVER}
    ${prompts}=    List Prompts
    Should Be Empty    ${prompts}
    ${names}=    Get Prompt Names
    Should Be Empty    ${names}
    [Teardown]    Disconnect All MCP Servers

Tool Should Exist Fails Cleanly Against An Empty Server
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EMPTY SERVER}
    Run Keyword And Expect Error
    ...    *does not expose a tool named 'anything'*It exposes: no tools.
    ...    Tool Should Exist    anything
    [Teardown]    Disconnect All MCP Servers

Tool Should Not Exist Passes Trivially Against An Empty Server
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EMPTY SERVER}
    Tool Should Not Exist    anything
    [Teardown]    Disconnect All MCP Servers

A Minimal Input Schema Is Still A Schema
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EDGE CASE SERVER}
    Tool Should Have Input Schema    minimal_schema_tool
    ${tool}=    Get Tool    minimal_schema_tool
    Should Be Equal    ${tool.input_schema}[type]    object
    [Teardown]    Disconnect All MCP Servers

A Minimal Schema Requires Nothing And Declares No Properties
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EDGE CASE SERVER}
    ${result}=    Call Tool    minimal_schema_tool
    Tool Result Should Not Be Error    ${result}
    Run Keyword And Expect Error
    ...    *does not require anything*It requires: nothing.
    ...    Tool Input Schema Should Require    minimal_schema_tool    anything
    Run Keyword And Expect Error
    ...    *does not declare anything*It declares: nothing.
    ...    Tool Input Schema Should Have Property    minimal_schema_tool    anything
    [Teardown]    Disconnect All MCP Servers

A Large Text Result Round Trips Intact
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EDGE CASE SERVER}
    ${result}=    Call Tool    large_result_tool    timeout=15
    ${text}=    Get Tool Result Text    ${result}
    Length Should Be    ${text}    200000
    Tool Result Should Contain Text    ${result}    xxxxx
    [Teardown]    Disconnect All MCP Servers

Unicode And Special Characters Round Trip Intact
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EDGE CASE SERVER}
    ${result}=    Call Tool    unicode_tool
    ${text}=    Get Tool Result Text    ${result}
    Should Contain    ${text}    héllo wörld
    Should Contain    ${text}    你好
    Should Contain    ${text}    🎉
    Should Contain    ${text}    "quoted"
    Should Contain    ${text}    \\backslash\\
    [Teardown]    Disconnect All MCP Servers

Several Content Blocks Are Joined With Newlines
    [Setup]    Connect To MCP Server    ${INTERPRETER}    ${EDGE CASE SERVER}
    ${result}=    Call Tool    multi_block_tool
    ${text}=    Get Tool Result Text    ${result}
    Should Be Equal    ${text}    first block\nsecond block\nthird block
    [Teardown]    Disconnect All MCP Servers
