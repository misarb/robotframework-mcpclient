*** Settings ***
Documentation       Listing, calling and asserting on the tools a server exposes.

Resource            resources/common.resource

Suite Setup         Connect To The Weather Server
Suite Teardown      Disconnect All MCP Servers


*** Test Cases ***
List Tools Returns Every Tool The Server Exposes
    ${tools}=    List Tools
    Length Should Be    ${tools}    2
    Should Be Equal    ${tools[0].name}    get_weather

Get Tool Names Returns Plain Strings
    ${names}=    Get Tool Names
    Should Be Equal    ${names}    ${{ ['get_weather', 'echo'] }}

Get Tool Returns A Single Tool By Name
    ${tool}=    Get Tool    get_weather
    Should Be Equal    ${tool.name}    get_weather
    Should Contain    ${tool.description}    weather

Get Tool Fails For A Tool The Server Does Not Expose
    Run Keyword And Expect Error
    ...    *does not expose a tool named 'nope'*
    ...    Get Tool    nope

Tool Should Exist Passes For An Exposed Tool
    Tool Should Exist    get_weather
    Tool Should Exist    echo

Tool Should Exist Fails And Names The Available Tools
    Run Keyword And Expect Error
    ...    *does not expose a tool named 'missing'*It exposes: get_weather, echo.
    ...    Tool Should Exist    missing

Tool Should Not Exist Passes For An Unknown Tool
    Tool Should Not Exist    delete_everything

Tool Should Not Exist Fails For An Exposed Tool
    Run Keyword And Expect Error
    ...    The server exposes a tool named 'echo', but should not.
    ...    Tool Should Not Exist    echo

Tool Count Should Be Checks How Many Tools Are Offered
    Tool Count Should Be    2
    Run Keyword And Expect Error    *Expected 5 tools*    Tool Count Should Be    5

Calling A Tool Returns Its Result
    ${result}=    Call Tool    get_weather    city=Paris
    Tool Result Should Not Be Error    ${result}
    Tool Result Should Contain Text    ${result}    18 degrees

Calling A Tool With An Argument Dictionary
    ${arguments}=    Create Dictionary    city=Berlin
    ${result}=    Call Tool With Arguments    get_weather    ${arguments}
    Tool Result Should Contain Text    ${result}    Berlin

Get Tool Result Text Returns The Joined Text Blocks
    ${result}=    Call Tool    echo    message=hello there
    ${text}=    Get Tool Result Text    ${result}
    Should Be Equal    ${text}    hello there

A Tool Reporting Failure Sets The Error Flag
    ${result}=    Call Tool    get_weather    city=Nowhereville
    Tool Result Should Be Error    ${result}
    Tool Result Should Contain Text    ${result}    Unknown city

Tool Result Should Not Be Error Fails And Shows The Tool Message
    ${result}=    Call Tool    get_weather    city=Nowhereville
    Run Keyword And Expect Error
    ...    The tool reported an error: Unknown city: Nowhereville
    ...    Tool Result Should Not Be Error    ${result}

Tool Result Should Be Error Fails For A Successful Call
    ${result}=    Call Tool    get_weather    city=Paris
    Run Keyword And Expect Error
    ...    Expected the tool to report an error, but it succeeded with:*
    ...    Tool Result Should Be Error    ${result}

Tool Result Text Assertions
    ${result}=    Call Tool    get_weather    city=Cairo
    Tool Result Should Contain Text    ${result}    Cairo
    Tool Result Should Contain Text    ${result}    CAIRO    ignore_case=True
    Tool Result Should Not Contain Text    ${result}    Traceback
    Tool Result Should Match    ${result}    \\d+ degrees
    Tool Result Should Not Be Empty    ${result}

Tool Result Should Contain Text Fails With The Actual Text
    ${result}=    Call Tool    get_weather    city=Paris
    Run Keyword And Expect Error
    ...    *does not contain 'snow'*
    ...    Tool Result Should Contain Text    ${result}    snow

A Custom Message Replaces The Default Failure Text
    ${result}=    Call Tool    get_weather    city=Paris
    Run Keyword And Expect Error
    ...    The forecast was missing the snow warning.
    ...    Tool Result Should Contain Text    ${result}    snow
    ...    msg=The forecast was missing the snow warning.

Input Schema Assertions
    Tool Should Have Input Schema    get_weather
    Tool Input Schema Should Require    get_weather    city
    Tool Input Schema Should Have Property    get_weather    city    units

Tool Input Schema Should Require Fails And Names What Is Required
    Run Keyword And Expect Error
    ...    *does not require country*It requires: city.
    ...    Tool Input Schema Should Require    get_weather    country

Tool Should Have Description Passes For A Documented Tool
    Tool Should Have Description    get_weather

Calling An Unknown Tool Fails The Keyword
    Run Keyword And Expect Error    *Unknown tool*    Call Tool    no_such_tool
