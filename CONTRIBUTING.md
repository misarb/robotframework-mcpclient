# Contributing to MCPClientLibrary

Thanks for interest in improving the library! This document explains how to set up a development environment and what to focus on.

## Development setup

```bash
git clone https://github.com/misarb/robotframework-mcpclient.git
cd robotframework-mcpclient

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
# Unit tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v

# Acceptance tests (Robot Framework) — Robot recurses into subdirectories,
# so this also runs atest/real_servers/ (see below) and needs Node.js too
python -m robot --variable INTERPRETER:python --outputdir results atest/

# Skip atest/real_servers/ (tagged 'real-server') if you don't have Node.js set up
python -m robot --variable INTERPRETER:python --outputdir results --exclude real-server atest/

# Or run both at once
./run_tests.sh
```

### Real-server integration tests

`atest/real_servers/` runs against a real MCP server
(`@modelcontextprotocol/server-filesystem`) instead of this project's own
fixtures under `tests/servers/` — it needs Node.js and network access to
fetch the package. It's tagged `real-server`, which is how the commands
above include or exclude it. To run just this suite:

```bash
python -m robot --variable INTERPRETER:python --outputdir results atest/real_servers/
```

CI's `test` and `robotframework-versions` jobs run with
`--exclude real-server` (no Node.js set up there); a separate `real-server`
job runs it with `continue-on-error: true` — a failure there is worth
investigating (the package changed behaviour, or the npm registry was
unreachable) but doesn't block a PR the way the other jobs do.

## Code style

```bash
# Check
ruff check src/ tests/

# Format
ruff format src/ tests/
```

All code must pass ruff checks before being merged.

## What to work on

**Good first issues:**
- Add more sample servers (e.g., a file tool, a database tool)
- Improve error messages for common failures
- Add edge-case tests (empty lists, missing fields, large payloads)
- Documentation improvements (tutorials, troubleshooting)

**Bigger features (discuss first):**
- HTTP transport (design seam exists in `_connection.py`)
- New MCP primitives (sampling, roots, notifications)
- Performance optimizations

## PR process

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Make changes + run tests
4. Commit with clear messages
5. Push and open a PR

PRs must:
- Pass all tests (unit + acceptance)
- Pass ruff lint/format
- Include tests for new code
- Update README or docs if user-facing

## Testing philosophy

- Test both pass *and* fail paths — for each assertion, include a case where it fails with a readable error
- Use the sample servers in `tests/servers/` as reference
- Keep tests independent (no shared state between test cases)

## Questions?

Open an issue or discussion on GitHub. The library is still early (v0.1.0), so design feedback is welcome.
