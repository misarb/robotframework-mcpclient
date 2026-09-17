"""Reads MCP result objects without tying tests to SDK attribute names.

The protocol uses camelCase on the wire (``isError``, ``inputSchema``) and the
Python SDK has spelled those fields both ways across versions. Every access
goes through here so a rename in the SDK is a change in one file rather than in
everybody's test suites.
"""

from .errors import MCPLibraryError


def _attr(obj, *names, default=None):
    """Return the first of ``names`` present on ``obj`` (or in it, if a dict)."""
    for name in names:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
        elif hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def is_error(result):
    """True if a tool result carries the tool-level error flag.

    This is not a protocol error: the call succeeded and the tool reported a
    failure in its own result. Genuine protocol errors arrive as exceptions.
    """
    return bool(_attr(result, "is_error", "isError", default=False))


def tool_name(tool):
    name = _attr(tool, "name")
    if name is None:
        raise MCPLibraryError(f"A tool in the server's list has no name: {tool!r}")
    return name


def input_schema(tool):
    """The tool's JSON input schema, or None if it declares none."""
    return _attr(tool, "input_schema", "inputSchema")


def output_schema(tool):
    """The tool's JSON output schema, or None if it declares none."""
    return _attr(tool, "output_schema", "outputSchema")


def schema_required(tool):
    """The list of required field names in the tool's input schema."""
    schema = input_schema(tool) or {}
    required = _attr(schema, "required", default=[])
    return list(required or [])


def schema_properties(tool):
    """The properties mapping of the tool's input schema."""
    schema = input_schema(tool) or {}
    return dict(_attr(schema, "properties", default={}) or {})


def resource_uri(resource):
    return str(_attr(resource, "uri", default=""))


def content_blocks(result):
    """The content blocks of a tool result, prompt message, or resource read."""
    return list(_attr(result, "content", "contents", default=[]) or [])


def text_of(block):
    """The text of a content block, or None for a non-text block."""
    return _attr(block, "text")


def all_text(result):
    """Every text block of a result joined with newlines.

    Assertions match against this so a server that splits its answer over
    several blocks behaves the same as one that returns a single block.
    """
    texts = [text_of(b) for b in content_blocks(result)]
    return "\n".join(t for t in texts if t is not None)


def structured_content(result):
    """The structured (JSON) payload of a tool result, if it returned one."""
    return _attr(result, "structured_content", "structuredContent")


def prompt_messages(result):
    return list(_attr(result, "messages", default=[]) or [])


def message_text(message):
    """The text of one prompt message, whose content may be a block or a list."""
    content = _attr(message, "content")
    if content is None:
        return ""
    if isinstance(content, list):
        return "\n".join(t for t in (text_of(b) for b in content) if t is not None)
    return text_of(content) or ""


def to_dict(obj):
    """A plain-dict view of an SDK object, for ``convert_results=True``."""
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {key: to_dict(value) for key, value in obj.items()}
    dump = getattr(obj, "model_dump", None)
    if dump is not None:
        return dump(mode="json", by_alias=False)
    return obj
