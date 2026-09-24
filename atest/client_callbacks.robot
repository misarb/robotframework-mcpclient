*** Settings ***
Documentation       Answering a server's requests back to the client: roots, sampling,
...                 elicitation, and resource-change subscriptions.

Resource            resources/common.resource

Suite Setup         Connect To The Callback Server
Suite Teardown      Disconnect All MCP Servers
Test Teardown       Reset Callback State


*** Variables ***
${CALLBACK SERVER}      ${SERVER_DIR}/callback_server.py


*** Test Cases ***
Client Roots Default To Empty
    ${result}=    Call Tool    list_project_roots
    Tool Result Should Contain Text    ${result}    0 root(s)

Set Client Roots Answers The Servers Roots List Request
    ${root}=    Create Dictionary    uri=file:///workspace    name=Project
    Set Client Roots    ${root}
    ${result}=    Call Tool    list_project_roots
    Tool Result Should Contain Text    ${result}    1 root(s): file:///workspace

Set Client Roots Accepts Several Roots
    ${a}=    Create Dictionary    uri=file:///a
    ${b}=    Create Dictionary    uri=file:///b
    Set Client Roots    ${a}    ${b}
    ${result}=    Call Tool    list_project_roots
    Tool Result Should Contain Text    ${result}    2 root(s)

Roots Can Be Changed Mid Suite
    ${first}=    Create Dictionary    uri=file:///first
    Set Client Roots    ${first}
    ${result1}=    Call Tool    list_project_roots
    Tool Result Should Contain Text    ${result1}    file:///first

    ${second}=    Create Dictionary    uri=file:///second
    Set Client Roots    ${second}
    ${result2}=    Call Tool    list_project_roots
    Tool Result Should Contain Text    ${result2}    file:///second
    Tool Result Should Not Contain Text    ${result2}    file:///first

Set Sampling Response Answers The Servers Sampling Request
    Set Sampling Response    42
    ${result}=    Call Tool    ask_llm    question=what is 6 times 7
    Tool Result Should Not Be Error    ${result}
    Tool Result Should Contain Text    ${result}    The model said: 42

Set Sampling Response Accepts A Custom Model Name
    Set Sampling Response    hello    model=fake-llm-v1
    ${result}=    Call Tool    ask_llm    question=hi
    Tool Result Should Contain Text    ${result}    The model said: hello

Sampling Response Is Consumed Once
    Set Sampling Response    first answer
    Call Tool    ask_llm    question=one
    ${result}=    Call Tool    ask_llm    question=two
    Tool Result Should Be Error    ${result}
    Tool Result Should Contain Text    ${result}    no response was queued

A Sampling Request With Nothing Queued Fails Clearly
    ${result}=    Call Tool    ask_llm    question=anything
    Tool Result Should Be Error    ${result}
    Tool Result Should Contain Text    ${result}    Set Sampling Response

Set Elicitation Response Accepts And Provides Content
    ${answer}=    Create Dictionary    name=Alice
    Set Elicitation Response    accept    ${answer}
    ${result}=    Call Tool    ask_for_name
    Tool Result Should Contain Text    ${result}    Hello, Alice!

Set Elicitation Response Can Decline
    Set Elicitation Response    decline
    ${result}=    Call Tool    ask_for_name
    Tool Result Should Contain Text    ${result}    action: decline

Set Elicitation Response Can Cancel
    Set Elicitation Response    cancel
    ${result}=    Call Tool    ask_for_name
    Tool Result Should Contain Text    ${result}    action: cancel

Elicitation Response Is Consumed Once
    ${answer}=    Create Dictionary    name=Bob
    Set Elicitation Response    accept    ${answer}
    Call Tool    ask_for_name
    ${result}=    Call Tool    ask_for_name
    Tool Result Should Contain Text    ${result}    elicitation failed

Subscribing To A Resource Captures Its Update Notifications
    Subscribe To Resource    data://counter
    Call Tool    bump_counter
    Resource Should Have Been Updated    data://counter

Unsubscribing Is Accepted
    Subscribe To Resource    data://counter
    Unsubscribe From Resource    data://counter

Resource Should Have Been Updated Fails Without A Matching Notification
    Run Keyword And Expect Error
    ...    *No update notification was received for 'data://never-touched'*
    ...    Resource Should Have Been Updated    data://never-touched

Get And Clear Resource Update Notifications
    Subscribe To Resource    data://counter
    Call Tool    bump_counter
    ${updates}=    Get Resource Update Notifications
    Should Contain    ${updates}    data://counter
    Clear Resource Update Notifications
    ${after}=    Get Resource Update Notifications
    Should Be Empty    ${after}


*** Keywords ***
Connect To The Callback Server
    Connect To MCP Server    ${INTERPRETER}    ${CALLBACK SERVER}

Reset Callback State
    Set Client Roots
    Clear Resource Update Notifications
