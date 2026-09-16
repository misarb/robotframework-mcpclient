*** Settings ***
Documentation       Starting, switching and closing MCP server connections.

Resource            resources/common.resource

Test Teardown       Disconnect All MCP Servers


*** Variables ***
${NOTES SERVER}     ${SERVER_DIR}/notes_server.py


*** Test Cases ***
Connecting Runs The Handshake And Reports The Server
    Connect To The Weather Server
    ${info}=    Get MCP Server Info
    Should Be Equal    ${info.name}    weather-test-server
    Should Be Equal    ${info.version}    1.0.0

The Server Reports Its Capabilities
    Connect To The Weather Server
    ${capabilities}=    Get MCP Server Capabilities
    Should Not Be Equal    ${capabilities.tools}    ${None}
    Should Not Be Equal    ${capabilities.resources}    ${None}

Connecting Returns A Connection Index
    ${index}=    Connect To The Weather Server
    Should Be Equal As Integers    ${index}    1

MCP Server Should Be Connected Passes While A Session Is Open
    Connect To The Weather Server
    MCP Server Should Be Connected

Keywords Fail Clearly When Nothing Is Connected
    Run Keyword And Expect Error    No MCP server is connected.    List Tools

MCP Server Should Be Connected Fails When Nothing Is Connected
    Run Keyword And Expect Error    No MCP server is connected.    MCP Server Should Be Connected

Disconnecting Closes The Session
    Connect To The Weather Server
    Disconnect From MCP Server
    Run Keyword And Expect Error    *not open*    List Tools

Two Servers Can Be Connected At Once Under Aliases
    Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}    alias=weather
    Connect To MCP Server    ${INTERPRETER}    ${NOTES SERVER}    alias=notes

    Tool Should Exist    create_note
    Tool Should Not Exist    get_weather

    Switch MCP Server    weather
    Tool Should Exist    get_weather
    Tool Should Not Exist    create_note

Switch MCP Server Returns The Previous Connection Index
    Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}    alias=weather
    Connect To MCP Server    ${INTERPRETER}    ${NOTES SERVER}    alias=notes
    ${previous}=    Switch MCP Server    weather
    Should Be Equal As Integers    ${previous}    2

Both Servers Stay Usable After Switching
    Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}    alias=weather
    Connect To MCP Server    ${INTERPRETER}    ${NOTES SERVER}    alias=notes

    ${note}=    Call Tool    create_note    text=remember the milk
    Tool Result Should Contain Text    ${note}    Stored note 1

    Switch MCP Server    weather
    ${weather}=    Call Tool    get_weather    city=Paris
    Tool Result Should Contain Text    ${weather}    Paris

    Switch MCP Server    notes
    ${second}=    Call Tool    create_note    text=and the eggs
    Tool Result Should Contain Text    ${second}    Stored note 2

Disconnect All Closes Every Connection
    Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}    alias=weather
    Connect To MCP Server    ${INTERPRETER}    ${NOTES SERVER}    alias=notes
    Disconnect All MCP Servers
    Run Keyword And Expect Error    No MCP server is connected.    List Tools

Disconnect All Is Safe When Nothing Is Connected
    Disconnect All MCP Servers
    Disconnect All MCP Servers

A Server That Dies On Startup Reports Its Own Error
    ${error}=    Run Keyword And Expect Error    *
    ...    Connect To MCP Server    ${INTERPRETER}    ${BROKEN SERVER}
    Should Contain    ${error}    Could not connect to the MCP server
    Should Contain    ${error}    the configuration file could not be read

Connecting To A Command That Does Not Exist Fails Clearly
    Run Keyword And Expect Error
    ...    *Could not connect to the MCP server*
    ...    Connect To MCP Server    definitely-not-a-real-command-xyz
