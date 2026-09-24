Troubleshooting
===============

Each section below quotes the actual error text the library produces, so you
can jump here from a failing test by searching for the message you saw.

Server process won't start
---------------------------

**"Could not connect to the MCP server: ..."**

``Connect To MCP Server`` starts your server as a subprocess and runs the
``initialize`` handshake. This message means that failed, for one of two
reasons the rest of the message tells you apart:

- **The command itself couldn't run** — a typo in the executable name, a
  script that isn't executable, or a missing interpreter:

  .. code-block:: text

      Could not connect to the MCP server: [Errno 2] No such file or directory: 'python3.99'

  Check the ``command`` argument is exactly what you'd type in a terminal to
  run the server, and that it's on the ``PATH`` the test runs with (CI
  environments often differ from your local shell).

- **The process started but exited before completing the handshake** — a
  Python traceback in your server code, a missing dependency, a config file
  it can't find:

  .. code-block:: text

      Could not connect to the MCP server: it closed the connection during the handshake

      The server wrote to stderr:
      Traceback (most recent call last):
        File "server.py", line 12, in <module>
          ...

  The library captures your server's ``stderr`` and includes its tail in the
  failure message — read that traceback first, it names the real problem.
  Run the server directly (``python server.py``) outside Robot to reproduce
  and debug it faster.

**A server that crashes after connecting, mid-call**, is a different failure
— see :ref:`server-crashes` below.

Timeout errors
---------------

**"The MCP server did not respond within N seconds."**

A keyword waited the full timeout and got nothing back. Common causes:

- **The tool is genuinely slow** — raise the timeout for that one call:

  .. code-block:: robotframework

      ${result}=    Call Tool    slow_tool    timeout=120

  Or raise the library's default for the whole suite:

  .. code-block:: robotframework

      Library    MCPClientLibrary    default_timeout=60

- **The server is stuck waiting on something the test never provides** — a
  tool that calls back for sampling or elicitation (see MCP's client
  callbacks) but nothing was queued with ``Set Sampling Response`` or
  ``Set Elicitation Response`` before the call. Check the server's own logic
  first; a callback with nothing queued fails immediately with a clear
  message rather than hanging, so a timeout here usually means the server is
  waiting on something else entirely (a real network call, a lock, an
  infinite loop).

- **The server never sends a JSON-RPC response for a request it handled** —
  a bug in your server's own dispatch code. Test the server directly with a
  raw JSON-RPC message over stdin to confirm it responds at all.

A timeout fails only the one keyword — the suite continues, and the next
keyword on the same connection works normally (unless the timeout was
caused by the process dying, which surfaces differently; see below).

Protocol errors
-----------------

**"The MCP server returned an error: ..."**

The server rejected the request itself at the JSON-RPC level — an unknown
method, invalid parameters, or an internal server error it reported as a
JSON-RPC error response. This is different from a **tool error** (a normal
result with the error flag set, which `Call Tool` returns rather than
raises — check it with ``Tool Result Should Be Error``).

Common causes:

- **Calling a tool, reading a resource, or getting a prompt that doesn't
  exist** — check the exact name/URI with ``List Tools`` /
  ``Get Tool Names`` (or the resource/prompt equivalents) first.
- **A server bug**: an internal exception the server's own framework turned
  into a JSON-RPC error instead of letting your test see a Python
  traceback. Check the server's logs or run it standalone to see the real
  exception.
- **A version mismatch**: the server expects a newer/older protocol version
  than the client negotiated. Check the server's ``initialize`` response
  for the ``protocolVersion`` it declares.

.. _server-crashes:

A server that crashes mid-call
---------------------------------

**"The MCP server's connection closed unexpectedly — it may have crashed.
Reconnect with 'Connect To MCP Server' before the next call."**

The server process died while handling a request — not a clean shutdown, an
abrupt exit. The library detects this specifically (rather than reporting it
as a generic protocol error) and marks the connection closed immediately:

.. code-block:: robotframework

    ${result}=    Call Tool    tool_that_crashes_the_server
    # raises MCPConnectionError with the message above

    MCP Server Should Be Connected
    # now fails too - the crash already updated the connection's state

Every keyword after that on the same connection fails fast with "The MCP
session is not open" — none of them retry against the dead process. To
recover, connect again, reusing the same alias if you had one:

.. code-block:: robotframework

    Connect To MCP Server    python    server.py    alias=myserver
    # ... crash happens here ...
    Connect To MCP Server    python    server.py    alias=myserver    # recovers

``Disconnect All MCP Servers`` is always safe in a teardown, even with a
crashed connection sitting in the cache alongside healthy ones.

If you see this and didn't expect a crash, check your server's own
stderr/logs from that run — a raised exception inside the server's request
handler is the most common cause, especially one raised from a background
thread or an ``os._exit()`` call that skips normal cleanup.

Empty tool/resource/prompt lists
-----------------------------------

``List Tools``, ``List Resources``, and ``List Prompts`` return an empty
list — not an error — when a server genuinely exposes none of that
primitive. This is valid MCP behaviour, not a bug:

.. code-block:: robotframework

    ${tools}=    List Tools
    Should Be Empty    ${tools}          # passes if the server has no tools

If you expected tools/resources/prompts and got an empty list instead:

- Check the server's ``initialize`` response actually declares the
  capability (``Get MCP Server Capabilities``) — a server that never
  declares ``tools`` won't be asked for them by a strict client, though this
  library still calls ``tools/list`` regardless and trusts what comes back.
- Check you're connecting to the right server/script — a common mistake
  when a suite has several similarly-named sample servers.
- If the server builds its tool list lazily (e.g. after some setup step),
  make sure that setup already ran before ``List Tools`` is called.

Schema-related errors
-------------------------

**"The tool '...' does not declare an output schema, so there is nothing to
validate its result against."**

You called ``Tool Result Should Match Output Schema`` on a tool that never
declared an ``output_schema`` in the first place. Check with
``Tool Should Have Input Schema`` for the input side, or read
``${tool.output_schema}`` from ``Get Tool`` directly — ``None`` means no
schema was declared.

**A schema-mismatch failure from ``Call Tool`` itself, not from an
assertion keyword:**

.. code-block:: text

    The result of '...' does not match its own declared output schema: ...

On mcp SDK 2.x, ``Call Tool`` validates a tool's structured content against
its own declared schema automatically and raises ``MCPValidationError``
before a mismatched result is ever returned to your test — you won't see
this from ``Tool Result Should Match Output Schema``, because there's no
result left to check by the time that keyword would run. This is a bug in
the *server* (it advertises a schema its own output doesn't match), not in
your test.

**A minimal schema still counts as "has a schema".**
``Tool Should Have Input Schema`` passes for a tool whose schema is
``{"type": "object"}`` with no properties — a schema exists, it's just
permissive about what it accepts. If you want to check the schema requires
or declares specific fields, use ``Tool Input Schema Should Require`` /
``Tool Input Schema Should Have Property`` instead.

Deprecation warnings from the MCP SDK
-----------------------------------------

Two keywords wrap SDK calls that print a ``MCPDeprecationWarning`` even
though they still work: ``Set Logging Level`` (the MCP logging capability is
deprecated per SEP-2577) and ``Subscribe To Resource`` /
``Unsubscribe From Resource`` (``resources/subscribe`` is deprecated in
favour of the SDK's newer ``Client.listen()``). This library suppresses
those specific warnings so they don't clutter your test output — if you see
one anyway, it's likely from a different SDK call your own server code (or a
custom keyword) makes directly.

Concurrency surprises
------------------------

If you're calling this library from multiple Python threads — a custom
keyword that spawns threads, for example — and see calls landing on the
wrong server (often surfacing as a confusing "Unknown tool" protocol error),
you've hit the ``Switch MCP Server`` race: it changes which connection is
"current" for the *whole library instance*, and two threads racing that
state can interleave badly.

Use ``Call Tool On Server`` instead for concurrent, multi-connection calls —
it names its connection by alias or index directly and never touches the
shared "current connection", so there's no race to land in. See the
`README's concurrency section <https://github.com/misarb/robotframework-mcpclient#calling-several-servers-concurrently>`_
for the full explanation and an example.

Still stuck?
--------------

Run with ``--loglevel DEBUG`` — every request and response the library sends
is logged, truncated only past 2000 characters, so you can see exactly what
went over the wire:

.. code-block:: bash

    robot --loglevel DEBUG my_suite.robot

If the problem looks like a library bug rather than a server or test issue,
open an issue on `GitHub <https://github.com/misarb/robotframework-mcpclient/issues>`_
with the exact error message and, if possible, a minimal server script that
reproduces it.
