# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- **Real-server integration suite**: `atest/real_servers/filesystem_server.robot`
  tests the library against `@modelcontextprotocol/server-filesystem`, the
  official reference MCP server (npx-installable, no API keys), rather than
  this project's own fixtures — 7 tests covering identity, real tool
  schemas, a server that declares no resources capability at all (a
  protocol error, handled cleanly), a real write/read round trip, the
  server's own sandbox security boundary surfacing as a tool error, and a
  real directory listing/search. Robot recurses into subdirectories, so it
  runs as part of `atest/` too, which now also needs Node.js and network
  access. CI runs it in its own job (`real-server`) with
  `continue-on-error: true`.

## [0.2.0] — 2026-09-24

### Added

- **Streamable HTTP transport**: `Connect To MCP Server Over HTTP` connects
  to a remote MCP server by URL instead of launching a subprocess, with an
  optional `headers=` dictionary for authentication (bearer tokens, API keys).
  Every other keyword works unchanged against an HTTP connection — tools,
  resources, prompts, and assertions don't know which transport they're on.
- **Output schema validation**: `Tool Result Should Match Output Schema`
  checks a tool result's structured content against the tool's own declared
  output schema using standard JSON Schema rules. On mcp 2.x, `Call Tool`
  itself already performs this check and now raises `MCPValidationError`
  (instead of a bare `RuntimeError`) when a result doesn't match; the keyword
  remains useful for explicit checks and for SDK versions that don't check
  automatically.
- **Tool call progress capture**: `Get Last Tool Call Progress` returns the
  progress notifications sent during the most recent `Call Tool`, and
  `Tool Call Should Have Reported Progress` asserts at least one arrived.
  Captured automatically — no setup needed.
- **Server log capture**: `Set Logging Level` requests a verbosity from the
  server; `Get Server Log Messages` and `Clear Server Log Messages` read and
  reset what has been collected on the connection; `Server Should Have
  Logged` and `Server Should Not Have Logged` assert on it, with an optional
  `level=` filter.
- **Granular exceptions**: the exception hierarchy now distinguishes
  `MCPHandshakeError` (server started, `initialize()` failed) from
  `MCPProcessError` (the process/connection never came up), and adds
  `MCPProtocolError` (a JSON-RPC error from the server) and
  `MCPValidationError` (a result didn't match what the server declared).
  All remain `MCPLibraryError` subclasses, so existing code that catches the
  base class, or matches on message text, is unaffected.
- **Resource subscriptions**: `Subscribe To Resource` and
  `Unsubscribe From Resource` ask the server for change notifications;
  `Get Resource Update Notifications`, `Clear Resource Update
  Notifications`, and `Resource Should Have Been Updated` read and assert
  on what arrived.
- **Client callbacks**: `Set Client Roots` declares the roots the client
  answers `roots/list` with. `Set Sampling Response` and
  `Set Elicitation Response` script the client's side of a server's
  sampling (agentic tool completion) or elicitation (asking the user a
  question) request — each consumed once, by the next matching request; a
  request with nothing queued gets a clear error rather than hanging or
  reusing a stale answer.
- **Concurrent calls across connections**: `Call Tool On Server` calls a
  tool on a named connection (by alias or index) without reading or
  changing which connection is "current" — the safe way to call several
  connections from different threads. `Get Last Tool Call Progress` takes
  the same optional connection argument.
- **Architecture documentation**: `docs/architecture.rst` explains the
  sync/async bridge (why a naive `asyncio.run()` per keyword fails, and how
  a single long-lived event loop thread avoids it), the session's
  long-lived task lifecycle, a full request sequence from keyword call to
  server and back, the transport seam, and why concurrent calls to
  different connections are safe while `Switch MCP Server` isn't — with 4
  Graphviz diagrams rendered to SVG at build time.

### Fixed

- The async bridge now catches `concurrent.futures.TimeoutError` (not just
  the built-in `TimeoutError`), which `Future.result()` actually raises on
  timeout. Fixes spurious CI failures on some platforms.
- CI: acceptance tests now resolve the Python interpreter with
  `sys.executable` instead of assuming `python` is on PATH, and run under an
  explicit `bash` shell so the fix works on Windows runners too.
- **A server crashing mid-call left the connection reporting itself open.**
  `Call Tool` (and every other keyword) would keep hitting the dead
  transport and re-raising a raw "Connection closed" `MCPProtocolError`
  instead of a clean "not connected" message, and `MCP Server Should Be
  Connected` would pass on a connection that no longer had a server behind
  it. The SDK's `CONNECTION_CLOSED` error code is now detected specifically:
  the connection is marked closed immediately and the failure is raised as
  `MCPConnectionError`, so the next keyword on that connection fails fast
  with a clear message instead of repeating the dead call.
- **`atest/converted_results.robot` failed outright on Robot Framework
  5.x.** It used `Library ... AS MCPDicts` import aliasing to run two named
  instances of the library side by side, which doesn't exist before RF 6.0.
  The suite only ever needed one instance, so the alias was dropped rather
  than working around it. CI now verifies robotframework 5.0.1, 6.0.2, and
  7.5 on every push (`robotframework-versions` job), so a future break like
  this is caught immediately rather than discovered by a user on an older
  Robot Framework.
- **The Sphinx documentation build was broken locally** (and only worked on
  ReadTheDocs, apparently via build-environment differences RTD applies that
  a bare `sphinx-build` invocation doesn't): `index.rst` used
  `.. include:: ../README.md :parser: myst_parser`, but `myst_parser` was
  neither a registered Sphinx extension nor a valid docutils parser path,
  and `docs/requirements.txt` never declared it as a dependency at all.
  Replaced the raw README include (which also produced RST parsing errors
  on Markdown syntax like `---` once the parser issue was worked around)
  with a plain summary and a link to the README on GitHub — `overview.rst`
  already covers the same ground natively in RST. Also fixed a stale
  `release = "0.1.0"` in `conf.py` and a `display_version` theme option
  `sphinx-rtd-theme` no longer supports. CI now builds the docs with
  warnings promoted to errors (`docs` job) on every push, so a break like
  this is caught before it reaches ReadTheDocs.

### Notes

- `resources/subscribe`/`resources/unsubscribe` are deprecated in the MCP
  spec (removed as of 2026-07-28, in favour of the SDK's higher-level
  `Client.listen()`) but still accepted by `ClientSession` in the mcp SDK
  version this library targets, and still widely implemented by servers.
  `Subscribe To Resource`/`Unsubscribe From Resource` suppress the resulting
  deprecation warning and keep working; a future major version may migrate
  the connection layer to `Client` if `ClientSession` drops the methods
  entirely.
- `Set Logging Level`'s underlying `session.set_logging_level` is
  similarly deprecated (SEP-2577) but functional; same treatment.

## [0.1.0] — 2026-09-16

First release.

### Added

- **Connection lifecycle** over the stdio transport: `Connect To MCP Server`,
  `Disconnect From MCP Server`, `Disconnect All MCP Servers`,
  `Switch MCP Server`, `Get MCP Server Info`, `Get MCP Server Capabilities`,
  `MCP Server Should Be Connected`. Several servers can be connected at once
  under aliases.
- **Tools**: `List Tools`, `Get Tool Names`, `Get Tool`, `Call Tool`,
  `Call Tool With Arguments`, `Get Tool Result Text`, `Get Tool Result Data`.
- **Resources**: `List Resources`, `Get Resource URIs`, `Read Resource`,
  `Get Resource Text`, `List Resource Templates`.
- **Prompts**: `List Prompts`, `Get Prompt Names`, `Get Prompt`,
  `Get Prompt Text`.
- **Assertions** for tool existence, count, descriptions, input schemas,
  result error flags, result text (substring, regular expression, emptiness,
  structured content), resources and prompts. Each takes a `msg=` override.
- Per-keyword `timeout=`, with a `default_timeout` set at import. A server that
  stops answering fails one keyword instead of hanging the suite.
- `convert_results=True` import option to return plain dictionaries and lists
  instead of MCP objects.
- Every request and response is logged to the Robot log, truncated so a large
  payload does not bury the report. A server that dies during startup has its
  stderr included in the failure message.

[0.2.0]: https://github.com/misarb/robotframework-mcpclient/releases/tag/v0.2.0
[0.1.0]: https://github.com/misarb/robotframework-mcpclient/releases/tag/v0.1.0
