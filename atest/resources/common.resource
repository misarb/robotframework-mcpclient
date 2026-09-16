*** Settings ***
Library     MCPClientLibrary
Library     OperatingSystem


*** Variables ***
${SERVER_DIR}       ${CURDIR}/../../tests/servers
${WEATHER SERVER}   ${SERVER_DIR}/weather_server.py
${BROKEN SERVER}    ${SERVER_DIR}/broken_server.py


*** Keywords ***
Connect To The Weather Server
    [Documentation]    Starts the sample weather server used across the suites.
    ...    Returns the connection index, like `Connect To MCP Server` does.
    ${index}=    Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}
    RETURN    ${index}
