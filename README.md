# robotframework-mcpclient

A [Robot Framework](https://robotframework.org/) library for testing **MCP
(Model Context Protocol)** servers.

MCP servers are becoming the standard way to give an LLM access to tools, data
and prompts — and like any other interface, they need tests. This library lets
you write those tests as ordinary Robot Framework test cases: start the server,
call its tools, and assert on what it exposes and returns. No async code, no
protocol plumbing.

```robotframework
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

Unknown City Is Reported As A Tool Error
    ${result}=    Call Tool    get_weather    city=Nowhereville
    Tool Result Should Be Error         ${result}
```

## Installation

```bash
pip install robotframework-mcpclient
```

**Requirements:** Python 3.10+, Robot Framework 5.0+, mcp 1.0+

**Tested with:** Python 3.10–3.13, Robot Framework 7.5, mcp 2.2.0

## Quick test

After installing, verify it works:

```bash
python -m robot --version
# Robot Framework 7.5 (Python 3.12.3 on linux)

python -c "from MCPClientLibrary import MCPClientLibrary; print('✓ Library imported')"
# ✓ Library imported
```

## Connecting to a server

`Connect To MCP Server` starts the server as a subprocess and completes the
MCP handshake. The first argument is the executable, the rest are its arguments:

```robotframework
Connect To MCP Server    python    ${CURDIR}/my_server.py
Connect To MCP Server    node     server.js    --verbose
Connect To MCP Server    uv       run    my-server
```

Extra environment variables and a working directory are optional:

```robotframework
${env}=    Create Dictionary    API_KEY=test-key
Connect To MCP Server    python    server.py    env=${env}    cwd=${CURDIR}
```

Always close connections in a suite teardown so no server process is left
behind between runs:

```robotframework
Suite Teardown    Disconnect All MCP Servers
```

### Several servers at once

Give each connection an alias and switch between them:

```robotframework
Connect To MCP Server    python    weather.py    alias=weather
Connect To MCP Server    python    notes.py      alias=notes

Switch MCP Server        weather
Tool Should Exist        get_weather

Switch MCP Server        notes
Tool Should Exist        create_note
```

## What you can test

### Tools

| Keyword | What it does |
|---|---|
| `List Tools` | Every tool the server exposes |
| `Get Tool Names` | Just the names, as a list of strings |
| `Get Tool` | One tool by name |
| `Call Tool` | Calls a tool with named arguments |
| `Call Tool With Arguments` | Calls a tool with an argument dictionary |
| `Get Tool Result Text` | The text blocks of a result, joined |
| `Get Tool Result Data` | The structured (JSON) content of a result |

Assertions:

| Keyword | Checks |
|---|---|
| `Tool Should Exist` / `Tool Should Not Exist` | The tool is (not) offered |
| `Tool Count Should Be` | How many tools the server offers |
| `Tool Should Have Input Schema` | The tool declares a schema at all |
| `Tool Input Schema Should Require` | The schema marks fields required |
| `Tool Input Schema Should Have Property` | The schema declares properties |
| `Tool Should Have Description` | The tool has a non-empty description |
| `Tool Result Should Be Error` / `Should Not Be Error` | The tool-level error flag |
| `Tool Result Should Contain Text` / `Should Not Contain Text` | Substring in the result text |
| `Tool Result Should Match` | Regular expression against the result text |
| `Tool Result Should Be Empty` / `Should Not Be Empty` | Whether there is content |
| `Tool Result Should Have Data` | The result carries structured content |

### Resources

```robotframework
Resource Should Exist         docs://weather/usage
${text}=    Get Resource Text    docs://weather/usage
Should Contain                ${text}    get_weather
```

`List Resources`, `Get Resource URIs`, `Read Resource`, `Get Resource Text`,
`List Resource Templates`, `Resource Should Exist`, `Resource Should Not Exist`,
`Resource Should Contain Text`.

### Prompts

```robotframework
Prompt Should Exist               weather_report
Prompt Should Require Argument    weather_report    city
${text}=    Get Prompt Text       weather_report    city=Berlin
Should Contain                    ${text}    Berlin
```

`List Prompts`, `Get Prompt Names`, `Get Prompt`, `Get Prompt Text`,
`Prompt Should Exist`, `Prompt Should Not Exist`, `Prompt Should Require Argument`.

## Two kinds of failure, and why it matters

MCP has two failure paths, and a test suite needs to tell them apart:

- A **tool error** is a normal result with an error flag set — the call
  succeeded, and the tool is reporting that it could not do the job. Assert on
  it with `Tool Result Should Be Error`.
- A **protocol error** — an unknown method, a malformed message, a server that
  died — fails the keyword outright with a readable message.

Check the tool error flag through the assertion keywords rather than reading the
attribute yourself. The field has been spelled `isError` and `is_error` across
MCP SDK versions; the keywords handle both, so your tests survive an SDK
upgrade. This is the main reason to use a library rather than hand-rolling the
checks.

## Return values

By default keywords return MCP objects, which you reach into with Robot's
extended variable syntax:

```robotframework
${result}=    Call Tool    get_weather    city=Paris
Length Should Be    ${result.content}    1
```

Import the library with `convert_results=True` to get plain dictionaries and
lists instead, which suits data-driven suites and JSON comparison:

```robotframework
Library    MCPClientLibrary    convert_results=True
```

```robotframework
${result}=    Call Tool    get_weather    city=Paris
Should Be Equal    ${result}[content][0][type]    text
```

## Timeouts

Every keyword waits `default_timeout` seconds (30 by default) for the server to
answer, and each one accepts a `timeout` that overrides it:

```robotframework
Library    MCPClientLibrary    default_timeout=60
```

```robotframework
${result}=    Call Tool    slow_tool    timeout=120
```

A server that stops responding fails one keyword rather than hanging the suite.

## Reading the log

Every request and response is written to the Robot log at INFO level, so a
failing test shows exactly what was sent and what came back. Large payloads are
truncated. Run with `--loglevel DEBUG` for the full detail.

## Keyword documentation

View the full keyword reference: [MCPClientLibrary.html](docs/MCPClientLibrary.html)

Or generate it locally:

```bash
python -m robot.libdoc MCPClientLibrary docs/MCPClientLibrary.html
```

## Transport support

This version speaks **stdio**, which covers local servers — the case that
matters for testing a server you are developing. Streamable HTTP for remote
servers is planned; the transport sits behind a single seam in the code, so
adding it will not change any keyword.

## Contributing

The library's own acceptance tests are written in Robot Framework against the
sample servers in `tests/servers/`, so they double as worked examples:

```bash
pip install -e ".[dev]"
python -m pytest tests/              # unit tests
python -m robot --outputdir results atest/   # acceptance tests
```

## License

Apache 2.0. See [LICENSE](LICENSE).
