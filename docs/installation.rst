Installation
============

Requirements
------------

- Python 3.10 or newer
- Robot Framework 5.0 or newer
- mcp 1.0 or newer (tested with 2.2.0)

Install from PyPI
-----------------

.. code-block:: bash

    pip install robotframework-mcpclient

This brings in the library plus its dependencies (Robot Framework and the MCP SDK).

Verify Installation
-------------------

.. code-block:: bash

    # Check Robot Framework
    robot --version
    # Robot Framework 7.5 (Python 3.12.3 on linux)

    # Check the library loads
    python -c "from MCPClientLibrary import MCPClientLibrary; print('✓ Installed')"

Develop from Source
--------------------

.. code-block:: bash

    git clone https://github.com/misarb/robotframework-mcpclient.git
    cd robotframework-mcpclient

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"

    # Run tests
    ./run_tests.sh
