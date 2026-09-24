Architecture
============

This page explains how MCPClientLibrary bridges Robot Framework's synchronous
keyword calls to the MCP Python SDK's async client — the one hard problem
the whole library is built around — and how a request actually travels from
a test case to a server and back.

The core problem
-----------------

Robot Framework keywords are ordinary synchronous Python calls. The MCP
Python SDK is built on ``asyncio``/``anyio``: ``ClientSession`` is an async
context manager, every request is an ``await``, and the transport
(``stdio_client``, ``streamable_http_client``) is itself an async context
manager that has to stay *open* for as long as the session is used.

The tempting shortcut — call ``asyncio.run(...)`` inside each keyword — does
not work here, for a reason specific to this SDK: ``anyio`` requires that a
task group's cancel scope is entered and exited by the *same task*. A
session opened inside one ``asyncio.run()`` call and used from another hits
"different task" errors and flaky teardown, because each call to
``asyncio.run()`` spins up and tears down its own event loop.

The fix is a **single event loop that outlives every keyword call**, running
on its own background thread for the life of the library:

.. graphviz::

   digraph components {
       rankdir=TB;
       node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, margin="0.15,0.08"];
       edge [fontname="Helvetica", fontsize=9];

       robot [label="Robot Framework test\n(sync keyword thread)", fillcolor="#e8eef7"];
       library [label="MCPClientLibrary\n(facade + keyword mixins)", fillcolor="#e8eef7"];
       bridge [label="AsyncBridge\n(background thread,\none persistent event loop)", fillcolor="#fdf0d5"];
       connection [label="MCPConnection\n(one per Connect To MCP Server*)", fillcolor="#fdf0d5"];
       session [label="ClientSession\n(MCP SDK)", fillcolor="#d9ead3"];
       transport [label="Transport\nstdio_client / streamable_http_client", fillcolor="#d9ead3"];
       server [label="MCP server\n(subprocess or remote HTTP)", shape=box3d, fillcolor="#f4cccc"];

       robot -> library [label="  Call Tool, List Tools, ..."];
       library -> bridge [label="  run_coroutine_threadsafe()"];
       bridge -> connection [label="  awaits inside\n  the loop thread"];
       connection -> session [label="  session.call_tool(...)"];
       session -> transport [label="  JSON-RPC message"];
       transport -> server [label="  stdio pipe / HTTP request"];

       { rank=same; robot; }
   }

Three layers do the work:

- **The library facade** (``MCPClientLibrary`` and its keyword mixins) is
  what a test talks to. Every keyword method is synchronous, thin, and does
  the same three things: log the request, delegate to a connection, convert
  and return the result.
- **AsyncBridge** owns the one event loop, on one background thread, for as
  long as the library is imported. Keywords hop into it with
  ``asyncio.run_coroutine_threadsafe()``, which is explicitly designed to be
  called safely from another thread — this is the seam that makes the
  sync/async crossing work.
- **MCPConnection** wraps one MCP session. It runs entirely as coroutines on
  the bridge's loop, so it can hold the transport and ``ClientSession``
  context managers open across many separate keyword calls, all from the
  same task, satisfying ``anyio``'s requirement.

The session as a long-lived task
-----------------------------------

``ClientSession`` and its transport are async context managers, but a
Robot Framework suite calls ``Connect To MCP Server``, then many other
keywords, then ``Disconnect From MCP Server`` — as separate calls, with
arbitrary code running between them. The context managers have to stay
*entered* across all of that.

``MCPConnection`` solves this by giving the session its own dedicated
coroutine (``_hold``) that never returns until told to shut down:

.. graphviz::

   digraph lifecycle {
       rankdir=LR;
       node [shape=box, style="rounded,filled", fillcolor="#fdf0d5", fontname="Helvetica", fontsize=10, margin="0.15,0.08"];
       edge [fontname="Helvetica", fontsize=9];

       enter [label="enter transport +\nClientSession\ncontext managers"];
       init [label="await\nsession.initialize()"];
       ready [label="signal ready\n(connect() can return)"];
       wait [label="await shutdown event\n(idle — session usable\nby other coroutines)"];
       exit [label="exit context managers\n(transport torn down,\nprocess/connection closed)"];

       enter -> init -> ready -> wait -> exit;
   }

``Connect To MCP Server`` schedules ``_hold`` as its own task on the bridge
loop and then waits only for the "ready" signal — so the keyword returns as
soon as the handshake completes, while ``_hold`` keeps running underneath,
holding the transport open. Every later keyword (``Call Tool``,
``List Resources``, ...) reaches the *same* session object by calling
methods on it from the bridge loop — never by re-entering the context
managers. ``Disconnect From MCP Server`` sets the shutdown event; ``_hold``
wakes up, falls out of the ``async with`` blocks in order, and the
transport's own cleanup (closing the subprocess, or the HTTP client) runs
exactly once, in the task that opened it.

One request, end to end
--------------------------

Putting both pieces together, here is what happens for a single
``Call Tool`` keyword call, from the moment a test case reaches it to the
moment it gets a result back:

.. graphviz::

   digraph sequence {
       rankdir=TB;
       node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, margin="0.12,0.08"];
       edge [fontname="Helvetica", fontsize=9];

       kw [label="Call Tool keyword\n(Robot's thread)", fillcolor="#e8eef7"];
       submit [label="bridge.run(coro)\nrun_coroutine_threadsafe\n+ future.result(timeout=)", fillcolor="#e8eef7"];
       loopstart [label="loop thread wakes,\nruns the coroutine", fillcolor="#fdf0d5"];
       callsdk [label="session.call_tool(name, args,\nprogress_callback=...)", fillcolor="#d9ead3"];
       wire [label="JSON-RPC request over\nthe transport", fillcolor="#f4cccc"];
       serverwork [label="server handles the\ntools/call request", fillcolor="#f4cccc"];
       reply [label="JSON-RPC response\n(+ any progress\nnotifications first)", fillcolor="#f4cccc"];
       sdkcheck [label="SDK validates the result\nagainst the tool's\noutput_schema (mcp 2.x)", fillcolor="#d9ead3"];
       future [label="coroutine result set\non the Future", fillcolor="#fdf0d5"];
       resume [label="Robot's thread resumes,\nresult (or exception)\nreturned from the keyword", fillcolor="#e8eef7"];

       kw -> submit -> loopstart -> callsdk -> wire -> serverwork -> reply -> sdkcheck -> future -> resume;
   }

A few things worth noting on that path:

- **The timeout lives on the Robot side of the crossing** —
  ``future.result(timeout=...)`` — not inside the coroutine itself. A hung
  server fails the one keyword when the timeout elapses; the underlying
  coroutine is cancelled, but the loop thread and every *other* connection's
  session keep running normally.
- **Progress notifications arrive on the same connection, interleaved with
  the final response.** The ``progress_callback`` passed to
  ``call_tool()`` fires for each one, appending to that connection's
  ``last_call_progress`` list, before the call's own result comes back.
- **A schema mismatch can fail the call itself, not just an assertion.** On
  mcp SDK 2.x, ``session.call_tool()`` validates the result's structured
  content against the tool's declared ``output_schema`` before returning —
  a violation raises there, and this library re-raises it as
  ``MCPValidationError``.
- **A closed connection is detected at this exact boundary.** If the
  server's process died mid-call, the SDK reports it as an ``MCPError``
  under a dedicated ``CONNECTION_CLOSED`` code; ``MCPConnection.call()``
  checks for that code specifically, marks the connection closed
  immediately, and raises ``MCPConnectionError`` instead of a generic
  protocol error.

Why this makes concurrent calls to different servers work
-------------------------------------------------------------

Because the bridge is one ``asyncio`` event loop, and ``asyncio`` is a
*cooperative* scheduler, a coroutine that's ``await``-ing a slow server's
response yields control back to the loop rather than blocking it. A second
thread calling a *different* connection's tool submits its own coroutine to
the same loop, which the loop runs while the first one is still waiting —
the two calls proceed independently, and a 3-second hang on one connection
does not delay a 2-millisecond call on another.

What the loop does *not* protect against is two threads mutating the same
Python object. ``Switch MCP Server`` changes which connection is "current"
for the whole library instance (``ConnectionCache.current``) — a plain
attribute write, not routed through the bridge at all — so two threads
racing ``Switch MCP Server`` and then ``Call Tool`` can interleave badly:
one thread's switch can land between another thread's switch and its call.
``Call Tool On Server`` exists specifically to sidestep this: it resolves
its connection with a read-only cache lookup and never touches "current",
so there is no shared mutable state left for a race to land in. See
:doc:`troubleshooting`'s "Concurrency surprises" section for the
failure mode this avoids.

Where each transport fits in
--------------------------------

``MCPConnection._open_transport()`` is the one method every transport goes
through; everything above it — the session, the callbacks, the keyword
layer — is identical regardless of which transport is in play:

.. graphviz::

   digraph transports {
       rankdir=LR;
       node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, margin="0.12,0.08"];
       edge [fontname="Helvetica", fontsize=9];

       seam [label="_open_transport()", fillcolor="#e8eef7"];
       stdio [label="stdio_client()\nsubprocess + pipes", fillcolor="#d9ead3"];
       http [label="streamable_http_client()\nhttpx-based HTTP client", fillcolor="#d9ead3"];
       proc [label="local subprocess\n(python, node, ...)", shape=box3d, fillcolor="#f4cccc"];
       remote [label="remote HTTP server", shape=box3d, fillcolor="#f4cccc"];

       seam -> stdio [label="  transport='stdio'"];
       seam -> http [label="  transport='http'"];
       stdio -> proc;
       http -> remote;
   }

Both branches yield the same ``(read, write)`` stream pair the SDK's
``ClientSession`` expects, which is what makes ``Connect To MCP Server`` and
``Connect To MCP Server Over HTTP`` interchangeable from every other
keyword's point of view — a test that switches from a local server to a
remote one doesn't change anything past this one seam.

Cross-thread state and why it's safe
------------------------------------------

Several pieces of per-connection state are written from callbacks running
on the bridge's loop thread and read from keyword methods on Robot's
thread: ``log_messages``, ``last_call_progress``, ``resource_updates``.
None of these need a lock. Each one is either:

- a plain Python list, appended to on one side and read (or ``.clear()``-ed)
  on the other — under the GIL, ``list.append`` and iteration are
  individually atomic, and nothing here does a read-modify-write that spans
  both sides, or
- a plain attribute replaced outright (``self._session = None``,
  ``self.pending_sampling_response = None``) rather than mutated in place.

This is why the library needs no explicit locking despite genuinely running
code on two threads at once — the shared state is deliberately kept to
shapes the GIL already makes safe, and the one place that *isn't* safe
(``ConnectionCache.current``, a single mutable pointer two threads can both
want to change) is called out explicitly above and in the README.
