*** Settings ***
Documentation       Listing, reading and asserting on the resources a server exposes.

Resource            resources/common.resource

Suite Setup         Connect To The Weather Server
Suite Teardown      Disconnect All MCP Servers


*** Test Cases ***
List Resources Returns Every Resource The Server Exposes
    ${resources}=    List Resources
    Length Should Be    ${resources}    1
    Should Be Equal    ${resources[0].name}    Weather usage

Get Resource URIs Returns Plain Strings
    ${uris}=    Get Resource URIs
    Should Contain    ${uris}    docs://weather/usage

Read Resource Returns The Contents
    ${resource}=    Read Resource    docs://weather/usage
    Length Should Be    ${resource.contents}    1

Get Resource Text Returns The Text Content
    ${text}=    Get Resource Text    docs://weather/usage
    Should Contain    ${text}    get_weather

Resource Should Exist Passes For An Exposed Resource
    Resource Should Exist    docs://weather/usage

Resource Should Exist Fails And Names The Available Resources
    Run Keyword And Expect Error
    ...    *does not expose a resource with the URI 'docs://missing'*
    ...    Resource Should Exist    docs://missing

Resource Should Not Exist Passes For An Unknown Resource
    Resource Should Not Exist    docs://nothing/here

Resource Should Contain Text Checks What A Resource Says
    Resource Should Contain Text    docs://weather/usage    city name

Resource Should Contain Text Fails With The Actual Text
    Run Keyword And Expect Error
    ...    *does not contain 'barometer'*
    ...    Resource Should Contain Text    docs://weather/usage    barometer

Reading An Unknown Resource Fails The Keyword
    Run Keyword And Expect Error    *Unknown resource*    Read Resource    docs://nope
