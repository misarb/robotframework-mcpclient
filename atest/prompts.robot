*** Settings ***
Documentation       Listing, rendering and asserting on the prompts a server exposes.

Resource            resources/common.resource

Suite Setup         Connect To The Weather Server
Suite Teardown      Disconnect All MCP Servers


*** Test Cases ***
List Prompts Returns Every Prompt The Server Exposes
    ${prompts}=    List Prompts
    Length Should Be    ${prompts}    1
    Should Be Equal    ${prompts[0].name}    weather_report

Get Prompt Names Returns Plain Strings
    ${names}=    Get Prompt Names
    Should Contain    ${names}    weather_report

Get Prompt Renders The Messages
    ${prompt}=    Get Prompt    weather_report    city=Berlin
    Length Should Be    ${prompt.messages}    1
    Should Contain    ${prompt.description}    Berlin

Get Prompt Text Returns The Rendered Text
    ${text}=    Get Prompt Text    weather_report    city=Berlin
    Should Be Equal    ${text}    Write a weather report for Berlin.

Prompt Should Exist Passes For An Exposed Prompt
    Prompt Should Exist    weather_report

Prompt Should Exist Fails And Names The Available Prompts
    Run Keyword And Expect Error
    ...    *does not expose a prompt named 'missing'*It exposes: weather_report.
    ...    Prompt Should Exist    missing

Prompt Should Not Exist Passes For An Unknown Prompt
    Prompt Should Not Exist    no_such_prompt

Prompt Should Require Argument Checks The Declared Arguments
    Prompt Should Require Argument    weather_report    city

Prompt Should Require Argument Fails And Names What Is Required
    Run Keyword And Expect Error
    ...    *does not require country*It requires: city.
    ...    Prompt Should Require Argument    weather_report    country
