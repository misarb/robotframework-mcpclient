# robotframework-mcpclient — Design & Architecture (v1)

A Robot Framework library for testing **MCP (Model Context Protocol)** servers.
The goal: let people write readable, keyword-driven tests that spin up an MCP
server, talk to it over the protocol, and assert on what it exposes and returns.

---

## 1. Scope of v1

Keep v1 small, correct, and runnable. Do **stdio transport only**, cover the
three MCP primitives (tools, resources, prompts), and invest in good assertion
keywords — because that's where a *test* library earns its keep.

**In scope for v1**

- Connect / disconnect to a local MCP server launched as a subprocess (stdio)
- The initialization handshake (`initialize`) done automatically on connect
- Tools: list, call, and assert
- Resources: list, read
- Prompts: list, get
- Rich assertion keywords (error flags, schema presence, content matching)
- Structured logging of every request/response into the Robot log

**Deliberately out of scope for v1** (design for it, don't build it yet)

- Streamable HTTP / remote servers → v3
- Multiple simultaneous connections / connection switching → design the seam now
- Sampling, roots, notifications, progress callbacks → later
- Schema *conformance* validation against the full MCP spec → v2

---

## 2. High-level architecture

The single hardest design problem is that the **MCP Python SDK is async**
(built on `anyio`/`asyncio`) while **Robot Framework keywords are synchronous**.
Everything else follows from how you solve that.

```
+---------------------------------------------------------------+
|                     Robot Framework test                      |
|   Connect To MCP Server / Call Tool / Tool Result Should ...  |
+------------------------------+--------------------------------+
                               | (sync calls)
                               v
+---------------------------------------------------------------+
|                        MCPClientLibrary  (facade)                   |
|   - the class Robot imports; exposes keywords                 |
|   - holds a ConnectionCache (multi-server ready)             |
|   - thin keyword methods -> delegate to the client wrapper    |
+------------------------------+--------------------------------+
                               | (submit coroutine)
                               v
+---------------------------------------------------------------+
|                   AsyncBridge  (the crux)                    |
|   - background thread running a dedicated asyncio loop        |
|   - run_coroutine_threadsafe() to call async code from sync   |
+------------------------------+--------------------------------+
                               | (awaits)
                               v
+---------------------------------------------------------------+
|              MCPConnection  (one per server)                 |
|   - owns the long-lived session task                         |
|   - enters stdio_client + ClientSession context managers     |
|   - keeps them open until disconnect                          |
+------------------------------+--------------------------------+
                               | (JSON-RPC over stdio)
                               v
+---------------------------------------------------------------+
|                     MCP server under test                    |
+---------------------------------------------------------------+
```

---

## 3. The async-to-sync bridge (read this part twice)

### Why the naive approach fails

The tempting version is: each keyword calls `asyncio.run(...)` or
`loop.run_until_complete(...)`.

That does **not** work for MCP, because the client is a set of **async context
managers that must stay open across many keyword calls**:

```python
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # session is only usable INSIDE this block
```

`Connect To MCP Server` and `Call Tool` are separate keywords, so the session
has to live *between* them. On top of that, `anyio` task groups and cancel
scopes must be entered and exited **in the same task**. If you open the session
in one `run_until_complete` call and try to use it in another, you'll hit
cancel-scope / "different task" errors and flaky teardown.

### The correct pattern: a long-lived session task + a persistent loop

1. On connect, start **one background thread** with **one asyncio event loop**
   that lives for the whole session (or the whole suite).
2. Inside that loop, launch a single **session coroutine** that opens the
   context managers, runs `initialize()`, then **waits on an asyncio.Event**
   (the shutdown signal). The context managers stay open the entire time.
3. Keywords call session methods with
   `asyncio.run_coroutine_threadsafe(coro, loop).result(timeout=...)` — this
   safely hops from Robot's sync thread into the loop thread and blocks for the
   answer.
4. On disconnect, set the shutdown event. The session coroutine falls out of
   the `async with` blocks, the SDK tears down cleanly, then you stop the loop
   and join the thread.

Sketch:

```python
import asyncio, threading

class AsyncBridge:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro, timeout=30):
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=timeout)

    def shutdown(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
```

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPConnection:
    def __init__(self, bridge):
        self._bridge = bridge
        self._session = None
        self._shutdown = None       # asyncio.Event, created in the loop
        self._ready = None          # asyncio.Event, signals init done

    def open(self, command, args, env=None, timeout=30):
        # schedule the long-lived session task on the bridge loop
        self._bridge.run(self._start(command, args, env), timeout=timeout)

    async def _start(self, command, args, env):
        self._shutdown = asyncio.Event()
        self._ready = asyncio.Event()
        # run the holder as its own task so open() can return once ready
        asyncio.ensure_future(self._hold(command, args, env))
        await self._ready.wait()

    async def _hold(self, command, args, env):
        params = StdioServerParameters(command=command, args=args, env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                self._ready.set()
                await self._shutdown.wait()   # keep everything open
        self._session = None

    def call(self, method_coro_factory, timeout=30):
        return self._bridge.run(method_coro_factory(self._session), timeout)

    def close(self, timeout=5):
        if self._shutdown:
            self._bridge.run(self._signal_shutdown(), timeout)

    async def _signal_shutdown(self):
        self._shutdown.set()
```

> **Verify against the SDK**: import paths (`mcp.client.stdio.stdio_client`),
> `StdioServerParameters` fields, and the `ClientSession` method names/return
> types. My research task will confirm the current API; the bridge design above
> is independent of those specifics.

---

## 4. Library object model

### Library type and scope

- **Hybrid library** (a Python class named `MCPClientLibrary`) — standard for a
  stateful library with a connection.
- `ROBOT_LIBRARY_SCOPE = 'GLOBAL'` with **explicit** connect/disconnect, plus a
  connection cache. Global scope + explicit lifecycle is the most predictable;
  it also lets a suite setup connect once and share across tests.
- Expose `ROBOT_LIBRARY_VERSION`.

### Multi-server readiness via ConnectionCache

Even though v1 targets one server at a time, use Robot's built-in
`robot.utils.ConnectionCache` from day one. It gives you connection **aliases**
and switching for free, mirrors how SeleniumLibrary/DatabaseLibrary work, and
costs almost nothing now while saving a refactor later.

```python
from robot.utils import ConnectionCache

class MCPClientLibrary:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = '0.1.0'

    def __init__(self, default_timeout=30):
        self._bridge = AsyncBridge()
        self._cache = ConnectionCache(no_current_msg='No MCP server connected')
        self._default_timeout = float(default_timeout)

    @property
    def _conn(self) -> 'MCPConnection':
        return self._cache.current
```

### Keyword modules (composition, not one giant file)

Split keywords by concern and compose them onto the main class. Keep keyword
methods **thin** — they log, delegate to `MCPConnection`, convert the result,
and return. Put logic in the wrapper, not the keywords.

```
src/MCPClientLibrary/
    __init__.py          # MCPClientLibrary facade, imports keyword mixins
    _bridge.py           # AsyncBridge
    _connection.py       # MCPConnection (session lifecycle)
    _logging.py          # request/response logging helpers
    _convert.py          # SDK objects -> Robot-friendly returns
    keywords/
        _connection_kw.py
        _tools_kw.py
        _resources_kw.py
        _prompts_kw.py
        _assertions_kw.py
    version.py
```

---

## 5. Keyword set for v1

Group as: **lifecycle**, **actions** (return data), **assertions** (fail on
mismatch). Assertions are separate keywords, not flags on actions — it reads
better and keeps actions reusable.

### Lifecycle
| Keyword | Args | Notes |
|---|---|---|
| `Connect To MCP Server` | `command`, `*args`, `env=`, `alias=`, `timeout=` | Launches subprocess, runs `initialize`, registers in cache. Returns index. |
| `Disconnect From MCP Server` | `alias=` | Signals shutdown, closes session. |
| `Disconnect All MCP Servers` | – | Suite teardown safety net. |
| `Switch MCP Server` | `alias_or_index` | Multi-server (works now via cache). |

### Tools
| Keyword | Returns |
|---|---|
| `List Tools` | list of tool objects (name, description, input schema) |
| `Get Tool Names` | list of strings (convenience for quick asserts) |
| `Call Tool` | `name`, `**arguments` → `CallToolResult` |

### Resources
| Keyword | Returns |
|---|---|
| `List Resources` | list of resource descriptors |
| `Read Resource` | `uri` → resource contents |

### Prompts
| Keyword | Returns |
|---|---|
| `List Prompts` | list of prompt descriptors |
| `Get Prompt` | `name`, `**arguments` → prompt messages |

### Assertions (the testing value)
| Keyword | Checks |
|---|---|
| `Tool Should Exist` / `Tool Should Not Exist` | tool name present in list |
| `Tool Result Should Not Be Error` / `...Should Be Error` | the error flag on the result |
| `Tool Result Should Contain Text` | substring across text content blocks |
| `Tool Should Have Input Schema` | tool declares an input schema |
| `Tool Input Schema Should Require` | schema `required` includes given field(s) |
| `Resource Should Exist` | uri present in resource list |
| `Prompt Should Exist` | name present in prompt list |

Give each a `msg=` override for custom failure text, following Robot convention.

---

## 6. Return values & the error-flag question

MCP results come back as **Pydantic model objects** from the SDK. You have two
choices:

1. **Return the SDK objects as-is.** Robot supports attribute access with
   extended variable syntax (`${result.content}`), so this feels natural and
   avoids lossy conversion. *Recommended default.*
2. Convert to plain dicts/lists in `_convert.py` for users who prefer
   `${result}[content]`. Offer this as an option, not the default.

**Important nuance — don't make users depend on the raw error field.** In the
protocol the tool-error flag is `isError` (JSON); the Python attribute may be
`isError` or an aliased `is_error` depending on SDK version. If tests assert on
the raw attribute name, they break when the SDK changes. This is the strongest
argument for `Tool Result Should Not Be Error` as a keyword: **normalize the
check in one place** so tests stay stable. (v1 should look up the attribute
defensively, e.g. try both names.)

Also remember: an MCP tool reporting a *tool-level* failure sets the error flag
on a normal result — it is **not** a JSON-RPC/transport error. Your assertion
keyword must inspect the result object, while genuine protocol errors surface as
exceptions from the SDK. Handle both paths distinctly.

---

## 7. Cross-cutting concerns

**Logging.** Use `robot.api.logger`. Log every outgoing call (keyword, args) and
the raw response at `INFO`/`DEBUG`. For a test tool this is the difference
between "test failed" and "here's exactly the request and the server's reply."
Redact/limit large payloads.

**Timeouts.** One `default_timeout` at import, overridable per keyword. The
bridge's `future.result(timeout=...)` gives you a hard ceiling so a hung server
fails the keyword instead of hanging the whole suite.

**Errors → clean failures.** Wrap bridge calls; translate SDK exceptions and
timeouts into `AssertionError`/library errors with a readable message. Never let
a raw `anyio`/asyncio traceback be the whole failure a user sees.

**Subprocess hygiene.** On disconnect, ensure the child process is actually
gone (the SDK's stdio client should handle it via context-manager exit; verify,
and add a `Disconnect All MCP Servers` for suite teardown so nothing leaks
between runs).

**Transport seam.** Put transport creation behind one method
(`_open_transport()` returning the `(read, write)` streams). v1 implements the
stdio branch; v3 adds `streamablehttp_client` there without touching a single
keyword.

---

## 8. Example test (target UX)

```robotframework
*** Settings ***
Library           MCPClientLibrary
Suite Setup       Connect To MCP Server    python    ${CURDIR}/weather_server.py
Suite Teardown    Disconnect All MCP Servers

*** Test Cases ***
Server Exposes The Weather Tool
    Tool Should Exist            get_weather
    Tool Should Have Input Schema    get_weather
    Tool Input Schema Should Require    get_weather    city

Weather Tool Returns A Result
    ${result}=    Call Tool    get_weather    city=Paris
    Tool Result Should Not Be Error    ${result}
    Tool Result Should Contain Text    ${result}    temperature

Unknown City Is Reported As A Tool Error
    ${result}=    Call Tool    get_weather    city=Nowhereville
    Tool Result Should Be Error    ${result}

Server Exposes Documentation Resource
    Resource Should Exist    docs://weather/usage
    ${doc}=    Read Resource    docs://weather/usage
    Should Not Be Empty    ${doc}
```

---

## 9. Project layout & packaging

- **Distribution name:** `robotframework-mcpclient` (PyPI). **Import name:**
  `MCPClientLibrary` (Robot users write `Library    MCPClientLibrary`). This split matches
  Robot ecosystem convention.
- `pyproject.toml`, `src/` layout, dependencies: `robotframework`, `mcp`.
- Include **sample MCP servers** under `tests/servers/` and write the library's
  own acceptance tests **in Robot** against them — dogfooding, and they double
  as documentation.
- Ship keyword docs generated with **Libdoc**.

```
robotframework-mcpclient/
    pyproject.toml
    README.md
    src/MCPClientLibrary/...          # section 4
    tests/
        servers/weather_server.py
        tools.robot
        resources.robot
        prompts.robot
    docs/MCPClientLibrary.html        # libdoc output
```

---

## 10. Suggested build order

1. `AsyncBridge` + a throwaway script that connects to a sample server and
   lists tools. **Prove the bridge before anything else** — it's the risk.
2. `MCPConnection` with the long-lived session task; get connect/list/disconnect
   solid, including clean teardown with no leftover processes.
3. `MCPClientLibrary` facade + `ConnectionCache`; wire lifecycle + `List Tools` /
   `Call Tool`.
4. Assertion keywords for tools (error flag, exists, contains, schema).
5. Resources + prompts (list/read/get) and their assertions.
6. Logging, timeouts, error translation, `Disconnect All`.
7. Sample servers + Robot acceptance suite + Libdoc + README.

Nail step 1 and the rest is straightforward plumbing.

---

## 11. Open decisions to make early

- **Library scope:** `GLOBAL` (recommended) vs `SUITE`. Affects where the loop
  thread lives and whether tests share a connection.
- **Return raw SDK objects vs dicts** (section 6) — pick the default, document it.
- **Auto-connect handshake options:** do you expose client `capabilities` /
  client info at connect time, or keep connect zero-config in v1? (Recommend
  zero-config now, add an optional `capabilities=` arg later.)
- **One loop thread total vs one per connection.** One shared loop is simpler and
  fine for v1; revisit only if you support many concurrent servers.

---

## 12. Implementation notes (what the build changed)

The design above was written before the code. This section records where
reality differed, so the document matches what ships.

### The MCP SDK renamed its fields

The design assumed the protocol's camelCase names (`isError`, `inputSchema`)
might appear as Python attributes. Built against **mcp 2.2.0**, they are
snake_case: `is_error`, `input_schema`, `mime_type`, `structured_content`.
Older 1.x releases used the camelCase spellings.

This is exactly the breakage section 6 predicted, and it arrived immediately.
`_convert.py` reads every field through a helper that tries both spellings, and
`tests/test_convert.py` covers both shapes. Tests written against
`Tool Result Should Not Be Error` survive the rename; tests that read the
attribute directly would not.

### Robot's stderr has no file descriptor

`stdio_client` passes its `errlog` straight to the subprocess as `stderr`, so it
must be a real file. Robot Framework replaces `sys.stderr` — the SDK default —
with a wrapper that has no `fileno()`, and every connection failed with a bare
`fileno` error. The spike passed because it ran outside Robot; the first
acceptance run caught it.

The connection now gives the server a temporary file instead, and reads it back
when the session ends. That turned a workaround into a feature: a server that
dies during startup has its own stderr quoted in the failure message, so
`Connect To MCP Server` reports *"the configuration file could not be read"*
rather than just failing.

### Decisions from section 11, as resolved

- **Library scope:** `GLOBAL`, with explicit connect/disconnect.
- **Return values:** MCP objects by default; `convert_results=True` returns
  dictionaries. Both are covered by acceptance tests.
- **Connect options:** zero-config, plus `env`, `cwd`, `alias` and `timeout`.
  Client capabilities stay out of v1 as planned.
- **Loop threads:** one shared loop for all connections. Two servers connected
  at once and used alternately are covered in `atest/connection.robot`.

### Test suite

- 38 unit tests (`tests/`) — the bridge and field normalisation.
- 61 acceptance tests (`atest/`) — written in Robot against four sample servers
  in `tests/servers/`: a weather server, a second server for aliases, one that
  dies on startup, and one that never answers.

Both the assertion keywords' pass *and* fail paths are tested: for each
assertion there is a case checking that it fails with a message naming what the
server actually offered.
