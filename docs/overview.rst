Overview
========

What is MCPClientLibrary?
-------------------------

MCPClientLibrary is a `Robot Framework <https://robotframework.org/>`_ library for testing MCP servers.

The `Model Context Protocol (MCP) <https://modelcontextprotocol.io/>`_ is a standard for giving LLMs access to tools, data, and prompts. Like any interface, MCP servers need tests.

This library makes testing them straightforward: write Robot Framework test cases, start the server, call its tools, read its resources, render its prompts, and assert on the results.

No async code. No protocol plumbing. Just keywords.

Key Features
------------

- **62 keywords** spanning connection lifecycle, tools, resources, and prompts
- **Two transports** — stdio (local subprocess) and streamable HTTP (remote server)
- **Assertion keywords** for both pass and fail paths
- **Output schema validation** — check a tool result's structured content
  against its own declared schema
- **Progress capture** — inspect the progress notifications a tool sent
  during a call
- **Server log capture** — collect and assert on log messages a server sends
  over the connection
- **Resource subscriptions** — subscribe to a resource and assert it was
  updated after an action that should change it
- **Client-side callbacks** — script canned answers for a server's
  sampling and elicitation requests, and declare the client's roots
- **Granular exceptions** — connection, handshake, protocol, and validation
  failures are distinct types, not one generic error
- **Multi-server support** with connection aliases, and a thread-safe way
  to call tools on several connections concurrently
- **Crash detection** — a server dying mid-call is reported clearly and
  the connection marked closed immediately, rather than a stale "connected"
  state or a repeated failure against a dead process
- **Comprehensive logging** of every request and response
- **Timeout protection** so hung servers don't hang test suites
- **Optional plain-dict returns** for data-driven tests
- **Sample servers** included for reference and testing

Why Use It?
-----------

**Before:** Hand-code async Python using the MCP SDK, manage event loops, debug context manager lifetimes.

**After:** Write readable Robot Framework keywords.

Example
-------

.. code-block:: robotframework

    *** Settings ***
    Library           MCPClientLibrary
    Suite Setup       Connect To MCP Server    python    ${CURDIR}/weather_server.py
    Suite Teardown    Disconnect All MCP Servers

    *** Test Cases ***
    Server Exposes The Weather Tool
        Tool Should Exist                   get_weather
        Tool Should Have Input Schema       get_weather
        Tool Input Schema Should Require    get_weather    city

    Weather Tool Answers For A Known City
        ${result}=    Call Tool    get_weather    city=Paris
        Tool Result Should Not Be Error     ${result}
        Tool Result Should Contain Text     ${result}    temperature

Supported Platforms
-------------------

- **Python:** 3.10, 3.11, 3.12, 3.13
- **Robot Framework:** 5.0+
- **MCP SDK:** 1.0+ (tested with 2.2.0)
- **OS:** Linux, macOS, Windows (any OS that runs Python)

Next Steps
----------

- :doc:`installation` — Install the library
- :doc:`quickstart` — Your first test in 5 minutes
- :doc:`keywords` — Full keyword reference
- :doc:`examples` — Real-world test examples
