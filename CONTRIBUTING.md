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

# Acceptance tests (Robot Framework)
python -m robot --variable INTERPRETER:python --outputdir results atest/

# Or run both at once
./run_tests.sh
```

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
