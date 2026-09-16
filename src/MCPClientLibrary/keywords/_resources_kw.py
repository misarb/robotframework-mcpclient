"""Keywords that list and read the resources a server exposes."""

from robot.api.deco import keyword

from .. import _convert as convert
from .._logging import log_request, log_response


class ResourceKeywords:
    @keyword("List Resources")
    def list_resources(self, timeout=None):
        """Returns every resource the server exposes.

        Each resource has ``uri``, ``name``, ``description`` and ``mime_type``.
        """
        log_request("resources/list")
        result = self._connection.call(lambda s: s.list_resources(), timeout=self._timeout(timeout))
        log_response("resources/list", result)
        return self._maybe_convert(list(result.resources))

    @keyword("Get Resource URIs")
    def get_resource_uris(self, timeout=None):
        """Returns the URIs of the server's resources as a list of strings.

        Example:
        | ${uris}= | Get Resource URIs |
        | Should Contain | ${uris} | docs://weather/usage |
        """
        log_request("resources/list")
        result = self._connection.call(lambda s: s.list_resources(), timeout=self._timeout(timeout))
        uris = [convert.resource_uri(resource) for resource in result.resources]
        log_response("resources/list", uris)
        return uris

    @keyword("Read Resource")
    def read_resource(self, uri, timeout=None):
        """Reads a resource and returns its contents.

        The result has a ``contents`` list. For the text alone, use
        `Get Resource Text`.

        Example:
        | ${resource}= | Read Resource | docs://weather/usage |
        """
        log_request("resources/read", uri=uri)
        result = self._connection.call(
            lambda s: s.read_resource(uri), timeout=self._timeout(timeout)
        )
        log_response("resources/read", result)
        return self._maybe_convert(result)

    @keyword("Get Resource Text")
    def get_resource_text(self, uri, timeout=None):
        """Reads a resource and returns its text content as one string.

        Example:
        | ${text}= | Get Resource Text | docs://weather/usage |
        | Should Not Be Empty | ${text} |
        """
        log_request("resources/read", uri=uri)
        result = self._connection.call(
            lambda s: s.read_resource(uri), timeout=self._timeout(timeout)
        )
        text = convert.all_text(result)
        log_response("resources/read", text)
        return text

    @keyword("List Resource Templates")
    def list_resource_templates(self, timeout=None):
        """Returns the URI templates the server exposes for dynamic resources."""
        log_request("resources/templates/list")
        result = self._connection.call(
            lambda s: s.list_resource_templates(), timeout=self._timeout(timeout)
        )
        log_response("resources/templates/list", result)
        return self._maybe_convert(list(result.resource_templates))
