#!/usr/bin/env bash
# Runs the library's unit tests and its Robot Framework acceptance tests.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if [ -x .venv/bin/python ]; then
    PYTHON="$(pwd)/.venv/bin/python"
fi

echo "== Unit tests =="
# Third-party pytest plugins installed system-wide (ROS ships one) can fail to
# import and take the run down with them; this suite needs none of them.
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest tests/ -q

echo
echo "== Acceptance tests =="
# The sample servers are started with the same interpreter that runs the tests,
# so they can import the dependencies from this environment.
"$PYTHON" -m robot --variable "INTERPRETER:$PYTHON" --outputdir results atest/

echo
echo "== Keyword documentation =="
"$PYTHON" -m robot.libdoc MCPClientLibrary docs/MCPClientLibrary.html
