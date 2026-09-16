"""Writes every request and response into the Robot log.

When a test fails against an MCP server, the useful question is what was sent
and what came back. Both end up in the log at INFO, truncated so a large
payload does not bury the report.
"""

import json

from robot.api import logger

MAX_LOGGED_CHARS = 2000


def _render(value):
    try:
        dump = getattr(value, "model_dump", None)
        data = dump(mode="json") if dump is not None else value
        text = json.dumps(data, indent=2, default=str)
    except (TypeError, ValueError):
        text = repr(value)
    if len(text) > MAX_LOGGED_CHARS:
        text = f"{text[:MAX_LOGGED_CHARS]}\n... (truncated, {len(text)} characters total)"
    return text


def log_request(method, **params):
    given = {key: value for key, value in params.items() if value is not None}
    logger.info(f"MCP request -> {method}\n{_render(given)}")


def log_response(method, result):
    logger.info(f"MCP response <- {method}\n{_render(result)}")


def log_info(message):
    logger.info(message)
