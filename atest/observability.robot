*** Settings ***
Documentation       Capturing progress notifications from a tool call, and log messages the
...                 server sends over the life of a connection.

Resource            resources/common.resource

Suite Setup         Connect To The Observability Server
Suite Teardown      Disconnect All MCP Servers
Test Teardown       Clear Server Log Messages


*** Variables ***
${OBSERVABILITY SERVER}      ${SERVER_DIR}/observability_server.py


*** Test Cases ***
A Tool That Reports Progress Is Captured
    ${result}=    Call Tool    process_file    filename=data.csv
    Tool Result Should Not Be Error    ${result}
    ${progress}=    Get Last Tool Call Progress
    Length Should Be    ${progress}    3
    Should Be Equal As Numbers    ${progress}[0][progress]    33
    Should Be Equal As Numbers    ${progress}[-1][progress]    100
    Should Be Equal    ${progress}[-1][message]    100% done

Tool Call Should Have Reported Progress Passes When Progress Was Sent
    Call Tool    process_file    filename=data.csv
    Tool Call Should Have Reported Progress

Tool Call Should Have Reported Progress Fails For A Quiet Tool
    Call Tool    quiet_tool
    Run Keyword And Expect Error
    ...    The most recent tool call reported no progress notifications.
    ...    Tool Call Should Have Reported Progress

Progress Is Cleared Before Each Call
    Call Tool    process_file    filename=data.csv
    Call Tool    quiet_tool
    ${progress}=    Get Last Tool Call Progress
    Length Should Be    ${progress}    0

Setting The Logging Level Is Accepted
    Set Logging Level    debug

Log Messages Sent After Setting The Level Are Collected
    Set Logging Level    warning
    Sleep    0.3s
    ${logs}=    Get Server Log Messages
    Length Should Be    ${logs}    1
    Should Be Equal    ${logs}[0][level]    warning
    Should Be Equal    ${logs}[0][logger]    observability-test-server

Server Should Have Logged Finds A Matching Message
    Set Logging Level    info
    Sleep    0.3s
    Server Should Have Logged    log level set to info

Server Should Have Logged Can Filter By Level
    Set Logging Level    error
    Sleep    0.3s
    Server Should Have Logged    log level set to error    level=error
    Run Keyword And Expect Error
    ...    No server log message at level 'warning' contains *
    ...    Server Should Have Logged    log level set to error    level=warning

Server Should Not Have Logged Passes When The Text Never Appeared
    Set Logging Level    debug
    Sleep    0.3s
    Server Should Not Have Logged    a string that was never logged

Server Should Not Have Logged Fails When The Text Did Appear
    Set Logging Level    notice
    Sleep    0.3s
    Run Keyword And Expect Error
    ...    A server log message contains 'log level set to notice', but should not.
    ...    Server Should Not Have Logged    log level set to notice

Clear Server Log Messages Empties The Collected List
    Set Logging Level    debug
    Sleep    0.3s
    ${logs}=    Get Server Log Messages
    Should Not Be Empty    ${logs}
    Clear Server Log Messages
    ${logs}=    Get Server Log Messages
    Should Be Empty    ${logs}


*** Keywords ***
Connect To The Observability Server
    Connect To MCP Server    ${INTERPRETER}    ${OBSERVABILITY SERVER}
