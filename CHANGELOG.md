# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [semantic versioning](https://semver.org/).

## [0.2.0] — Unreleased

### Added

- **Streamable HTTP transport**: `Connect To MCP Server Over HTTP` connects
  to a remote MCP server by URL instead of launching a subprocess, with an
  optional `headers=` dictionary for authentication (bearer tokens, API keys).
  Every other keyword works unchanged against an HTTP connection — tools,
  resources, prompts, and assertions don't know which transport they're on.

### Fixed

- The async bridge now catches `concurrent.futures.TimeoutError` (not just
  the built-in `TimeoutError`), which `Future.result()` actually raises on
  timeout. Fixes spurious CI failures on some platforms.
- CI: acceptance tests now resolve the Python interpreter with
  `sys.executable` instead of assuming `python` is on PATH, and run under an
  explicit `bash` shell so the fix works on Windows runners too.

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
