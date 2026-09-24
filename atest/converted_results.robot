*** Settings ***
Documentation       The convert_results import option returns dictionaries instead of MCP objects.

Library             MCPClientLibrary    convert_results=True
Library             OperatingSystem

Suite Setup         Connect To MCP Server    ${INTERPRETER}    ${WEATHER SERVER}
Suite Teardown      Disconnect All MCP Servers


*** Variables ***
${SERVER_DIR}       ${CURDIR}/../tests/servers
${WEATHER SERVER}   ${SERVER_DIR}/weather_server.py


*** Test Cases ***
Tools Come Back As Dictionaries
    ${tools}=    List Tools
    Should Be Equal    ${tools}[0][name]    get_weather
    Should Be Equal    ${tools}[0][input_schema][required][0]    city

A Tool Result Comes Back As A Dictionary
    ${result}=    Call Tool    get_weather    city=Paris
    Should Be Equal    ${result}[content][0][type]    text
    Should Contain    ${result}[content][0][text]    18 degrees

Assertions Work On Converted Results Too
    ${result}=    Call Tool    get_weather    city=Paris
    Tool Result Should Not Be Error    ${result}
    Tool Result Should Contain Text    ${result}    temperature

The Error Flag Is Read Correctly From A Dictionary
    ${result}=    Call Tool    get_weather    city=Nowhereville
    Tool Result Should Be Error    ${result}
