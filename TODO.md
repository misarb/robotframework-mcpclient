# MCPClientLibrary TODO

## v0.1.0 — Ready to Ship

### Pre-release (blocking)
- [ ] Verify `robotframework-mcpclient` name available on PyPI
- [ ] Update pyproject.toml URLs (currently placeholders)
  - Homepage: `https://github.com/misarb/robotframework-mcpclient`
  - Documentation: `https://github.com/misarb/robotframework-mcpclient#readme`
  - Issues: `https://github.com/misarb/robotframework-mcpclient/issues`
  - Source: `https://github.com/misarb/robotframework-mcpclient`
- [ ] Generate keyword docs: `robot.libdoc MCPClientLibrary docs/MCPClientLibrary.html`
- [ ] Decide where to host keyword documentation (GitHub Pages, ReadTheDocs, or repo only)
- [ ] Create git tag `v0.1.0`
- [ ] Have PyPI account & API token ready
- [ ] Upload to PyPI: `twine upload dist/*`

### Optional for v0.1.0 (polish, not blocking)
- [ ] Add tested versions to README (mcp 2.2.0, robotframework 7.5, Python 3.10-3.13)
- [ ] Quick test example in README (verify installation works)
- [ ] CONTRIBUTING.md (if accepting PRs early)

---

## v0.2.0 — Next Release

### Documentation
- [ ] Tutorial: "Build Your First MCP Test"
- [ ] Troubleshooting guide
  - Server process won't start
  - Timeout errors
  - Protocol errors
  - Empty tool/resource/prompt lists
- [ ] Architecture deep-dive: async bridge, event loop threading model
- [ ] Example servers beyond weather
  - Real database tool
  - REST API wrapper
  - File system tool

### Testing & CI
- [ ] Test against robotframework 5.0, 6.0, 7.x (not just 7.5)
- [ ] Test against Python 3.10, 3.11, 3.12, 3.13 in CI matrix
- [ ] Edge case tests
  - Empty tool/resource/prompt lists
  - Tools with no input schema
  - Missing required fields in results
  - Large payloads (100KB+ results)
- [ ] Concurrent keyword calls on same server (thread safety)
- [ ] Server crash recovery (reconnect after server dies mid-test)
- [ ] MCP SDK version compatibility (test 1.x if supported)

### Library Features (non-blocking)
- [ ] HTTP/streamable transport (design seam exists, v1 is stdio only)
- [ ] Sampling primitives (design out-of-scope, add if needed)
- [ ] Roots, notifications, progress callbacks
- [ ] Input/elicitation handling (when server needs user input)
- [ ] Streaming responses (currently collects full result)
- [ ] Resource subscription (currently read-once)
- [ ] Schema conformance validation (check results vs output_schema)
- [ ] Set logging level keyword (wraps session.set_logging_level)
- [ ] More granular exceptions (not just MCPLibraryError)
- [ ] Connection pooling / reuse across test suites
- [ ] Better error messages for common failures

### Usability
- [ ] Auto-retry for transient failures (optional)
- [ ] Keep-alive / connection pooling
- [ ] Test fixtures / setup helpers (Robot examples)
- [ ] Performance benchmarks (baseline keyword latency)

### Maintenance
- [ ] Changelog discipline (track breaking changes)
- [ ] Dependabot for SDK updates
- [ ] GitHub issue templates (bug, feature request)
- [ ] Type hints for keywords (IDE autocomplete support)
- [ ] Integration tests against real MCP servers

---

## v1.0.0 — Stable Release

- [ ] All v0.2.0 items complete
- [ ] At least 2 months of v0.2.0 in the wild (gather feedback)
- [ ] Breaking changes fully documented
- [ ] Semantic versioning locked in
- [ ] Consider 1.x API stable (no more major rewrites)
