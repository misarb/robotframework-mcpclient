*** Settings ***
Documentation       Integration test against a real, independently-built MCP server:
...                 @modelcontextprotocol/server-filesystem, the official reference
...                 filesystem server (npx-installable, no API keys required).
...
...                 Robot recurses into subdirectories, so this suite runs as part of
...                 a plain ``robot atest/`` too — that needs Node.js and network
...                 access to fetch the package on top of the usual Python
...                 requirements. To run only this suite:
...
...                 | robot --variable INTERPRETER:python atest/real_servers/
...
...                 It exists to check the library against a server this project did
...                 not write and cannot make convenient assumptions about — every
...                 other suite under atest/ runs against fixtures in tests/servers/
...                 built specifically to exercise this library's own keywords.

Library             Process
Library             MCPClientLibrary    default_timeout=20
Library             OperatingSystem

Force Tags          real-server

Suite Setup         Start The Filesystem Server
Suite Teardown      Disconnect All MCP Servers


*** Variables ***
${SERVER_VERSION}      2026.8.31
${SANDBOX}              ${OUTPUT DIR}/fs_sandbox


*** Test Cases ***
The Server Reports Its Identity
    ${info}=    Get MCP Server Info
    Should Be Equal    ${info.name}    secure-filesystem-server

The Server Exposes Its Real Tool Set
    ${names}=    Get Tool Names
    Should Contain    ${names}    read_text_file
    Should Contain    ${names}    write_file
    Should Contain    ${names}    list_directory
    Should Contain    ${names}    search_files
    Tool Should Have Input Schema    read_text_file
    Tool Input Schema Should Require    read_text_file    path

The Server Declares No Resources Capability
    # Real-world servers don't all implement every MCP primitive - this one
    # only declares tools. Calling a primitive it never declared fails as a
    # protocol error, not a hang or a crash.
    ${caps}=    Get MCP Server Capabilities
    Should Be Equal    ${caps.resources}    ${None}
    Run Keyword And Expect Error    *Method not found*    List Resources

Writing And Reading A File Round Trips Through The Real Server
    ${result}=    Call Tool    write_file
    ...    path=${SANDBOX}/written.txt    content=written by MCPClientLibrary
    Tool Result Should Not Be Error    ${result}

    ${read}=    Call Tool    read_text_file    path=${SANDBOX}/written.txt
    Tool Result Should Not Be Error    ${read}
    Tool Result Should Contain Text    ${read}    written by MCPClientLibrary

The Server Enforces Its Own Sandbox As A Tool Error
    # Not a protocol error and not a crash: the server's own security
    # boundary reports itself the same way any other tool failure does.
    ${result}=    Call Tool    read_text_file    path=/etc/passwd
    Tool Result Should Be Error    ${result}
    Tool Result Should Contain Text    ${result}    outside allowed directories

Listing A Directory Reflects Real Filesystem State
    Create File    ${SANDBOX}/listed.txt    content=irrelevant
    ${result}=    Call Tool    list_directory    path=${SANDBOX}
    Tool Result Should Contain Text    ${result}    listed.txt

Searching Files Finds A Real Match
    # search_files takes a glob pattern, not a substring - "*.md" matches,
    # a bare "needle" does not.
    Create File    ${SANDBOX}/needle.md    content=irrelevant
    ${result}=    Call Tool    search_files    path=${SANDBOX}    pattern=*.md
    Tool Result Should Contain Text    ${result}    needle.md


*** Keywords ***
Start The Filesystem Server
    Create Directory    ${SANDBOX}
    Create File    ${SANDBOX}/greeting.txt    content=hello from a real MCP server
    Connect To MCP Server
    ...    npx    -y    @modelcontextprotocol/server-filesystem@${SERVER_VERSION}    ${SANDBOX}
    ...    timeout=60
