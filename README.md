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

**Tested with:** Python 3.10–3.13, Robot Framework 5.0.1 / 6.0.2 / 7.5, mcp 2.2.0

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

`Switch MCP Server` changes which connection is current for the whole
library — fine sequentially, but calling it from more than one thread races
(see [Calling several servers concurrently](#calling-several-servers-concurrently)
below).

### Connecting over HTTP

For a remote MCP server, use `Connect To MCP Server Over HTTP` instead — same
keywords work afterward regardless of transport:

```robotframework
Connect To MCP Server Over HTTP    https://example.com/mcp
Tool Should Exist    get_weather
```

Pass extra headers for authentication:

```robotframework
${headers}=    Create Dictionary    Authorization=Bearer ${TOKEN}
Connect To MCP Server Over HTTP    https://example.com/mcp    headers=${headers}
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
| `Call Tool On Server` | Calls a tool on a named connection, without switching (safe for concurrent use) |
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
| `Tool Result Should Match Output Schema` | Structured content matches the tool's declared output schema |

### Tool call progress

A tool that reports progress during a call — a long-running operation, a
multi-step process — has its notifications captured automatically:

```robotframework
${result}=    Call Tool    process_file    filename=data.csv
${progress}=    Get Last Tool Call Progress
Should Be Equal As Numbers    ${progress}[-1][progress]    100
Tool Call Should Have Reported Progress
```

`Get Last Tool Call Progress` returns the events from the most recent
`Call Tool`, cleared before each new call.

### Server-sent log messages

```robotframework
Set Logging Level    debug
Call Tool    get_weather    city=Nowhereville
Server Should Have Logged    unknown city    level=warning
```

`Set Logging Level`, `Get Server Log Messages`, `Clear Server Log Messages`,
`Server Should Have Logged`, `Server Should Not Have Logged`.

Log messages accumulate for the life of the connection; a server must
declare the (now-deprecated but widely implemented) `logging` capability to
accept `Set Logging Level`.

### Resources

```robotframework
Resource Should Exist         docs://weather/usage
${text}=    Get Resource Text    docs://weather/usage
Should Contain                ${text}    get_weather
```

`List Resources`, `Get Resource URIs`, `Read Resource`, `Get Resource Text`,
`List Resource Templates`, `Resource Should Exist`, `Resource Should Not Exist`,
`Resource Should Contain Text`.

### Resource subscriptions

```robotframework
Subscribe To Resource    data://counter
Call Tool    bump_counter
Resource Should Have Been Updated    data://counter
```

`Subscribe To Resource`, `Unsubscribe From Resource`,
`Get Resource Update Notifications`, `Clear Resource Update Notifications`,
`Resource Should Have Been Updated`.

### Prompts

```robotframework
Prompt Should Exist               weather_report
Prompt Should Require Argument    weather_report    city
${text}=    Get Prompt Text       weather_report    city=Berlin
Should Contain                    ${text}    Berlin
```

`List Prompts`, `Get Prompt Names`, `Get Prompt`, `Get Prompt Text`,
`Prompt Should Exist`, `Prompt Should Not Exist`, `Prompt Should Require Argument`.

### Client callbacks: roots, sampling, elicitation

MCP lets a server call back into the client mid-tool-call — to ask what
directories/URIs the client exposes (roots), to have the client's LLM
complete a message (sampling — the pattern behind an agentic tool), or to
ask the user a question (elicitation). These keywords script the client's
side of that conversation, so a tool that depends on it can be tested
without a real LLM or a real user:

```robotframework
${root}=    Create Dictionary    uri=file:///workspace    name=Project
Set Client Roots    ${root}

Set Sampling Response    42
${result}=    Call Tool    agentic_tool    query=what is 6 times 7

${answer}=    Create Dictionary    name=Alice
Set Elicitation Response    accept    ${answer}
${result}=    Call Tool    tool_that_asks_for_a_name
```

`Set Client Roots`, `Set Sampling Response`, `Set Elicitation Response`.

Sampling and elicitation responses are consumed once, by the next matching
request the server sends — set a fresh one before each call that triggers
one. If the server asks and nothing is queued, the client answers with a
clear error naming which keyword to call, rather than hanging or reusing a
stale answer from an earlier test.

## Two kinds of failure, and why it matters

MCP has two failure paths, and a test suite needs to tell them apart:

- A **tool error** is a normal result with an error flag set — the call
  succeeded, and the tool is reporting that it could not do the job. Assert on
  it with `Tool Result Should Be Error`.
- A **protocol error** — an unknown method, a malformed message — fails the
  keyword outright with a readable message.

Check the tool error flag through the assertion keywords rather than reading the
attribute yourself. The field has been spelled `isError` and `is_error` across
MCP SDK versions; the keywords handle both, so your tests survive an SDK
upgrade. This is the main reason to use a library rather than hand-rolling the
checks.

### Exception types

Robot Framework itself only ever matches error messages, but the exceptions
this library raises form a hierarchy, for Python code built on top of it
(custom keywords that want to catch a specific failure):

```
MCPLibraryError
├── MCPTimeoutError        A keyword's timeout expired
├── MCPConnectionError     The connection isn't usable
│   ├── MCPHandshakeError  The server started but initialize() failed
│   └── MCPProcessError    The server process never came up, or crashed mid-call
├── MCPProtocolError       The server returned a JSON-RPC error
└── MCPValidationError     A result didn't match what the server declared
```

### A server that crashes mid-call

If the server process dies while handling a request — not a clean shutdown,
an actual crash — the keyword that was waiting on it fails with
`MCPConnectionError`, and the connection is marked closed immediately:

```robotframework
${result}=    Call Tool    tool_that_crashes_the_server
# raises MCPConnectionError: "...connection closed unexpectedly — it may have crashed..."

MCP Server Should Be Connected
# now fails too: the crash already updated the connection's state
```

Every keyword after that on the same connection fails fast with a clear "not
open" message — none of them re-attempt a call against the dead process.
To recover, connect again (under the same alias, if you had one):

```robotframework
Connect To MCP Server    python    server.py    alias=myserver
Connect To MCP Server    python    server.py    alias=myserver    # after a crash
```

`Disconnect All MCP Servers` is always safe to call in a teardown, even with
a crashed connection sitting in the cache alongside healthy ones.

### Calling several servers concurrently

Every keyword shares one "current connection", tracked by the library — set
by `Connect To MCP Server` and changed by `Switch MCP Server`. That's fine
called sequentially, which covers ordinary test suites, but it becomes a race
if two threads call `Switch MCP Server` and then act on "the current
connection" at the same time: one thread's switch can land between another's
switch and its call, and the call goes to the wrong server.

For calls made concurrently from different threads — a custom keyword that
spawns threads, say — use `Call Tool On Server` instead. It names its
connection by alias or index directly and never reads or writes the shared
"current connection", so there's no shared state for a race to land in:

```robotframework
Connect To MCP Server    python    weather.py    alias=weather
Connect To MCP Server    python    notes.py      alias=notes

${result}=    Call Tool On Server    weather    get_weather    city=Paris
${note}=      Call Tool On Server    notes      create_note     text=remember the milk
```

`Get Last Tool Call Progress` takes the same optional connection argument,
for reading another connection's progress without switching to it.

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

View the full keyword reference: [MCPClientLibrary.html](https://robotframework-mcpclient.readthedocs.io/_static/MCPClientLibrary.html)

Or generate it locally:

```bash
python -m robot.libdoc MCPClientLibrary docs/MCPClientLibrary.html
```

## Transport support

Two transports are supported, and every keyword after `Connect To MCP Server*`
works the same on both:

- **stdio** (`Connect To MCP Server`) — starts the server as a subprocess.
  The usual choice for testing a server you're developing locally.
- **Streamable HTTP** (`Connect To MCP Server Over HTTP`) — connects to a
  running remote server by URL, with optional headers for authentication.

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
