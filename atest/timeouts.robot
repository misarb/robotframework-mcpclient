*** Settings ***
Documentation       A server that stops answering must fail one keyword, not hang the suite.

Resource            resources/common.resource

Suite Teardown      Disconnect All MCP Servers


*** Variables ***
${SLOW SERVER}      ${SERVER_DIR}/slow_server.py


*** Test Cases ***
A Tool That Never Answers Times Out
    Connect To MCP Server    ${INTERPRETER}    ${SLOW SERVER}
    ${error}=    Run Keyword And Expect Error    *    Call Tool    hang    timeout=2
    Should Contain    ${error}    did not respond within 2.0 seconds

The Suite Keeps Working After A Timeout
    Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}    alias=weather
    ${result}=    Call Tool    get_weather    city=Paris
    Tool Result Should Not Be Error    ${result}
