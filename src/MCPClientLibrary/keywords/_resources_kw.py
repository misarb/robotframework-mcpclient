"""Keywords that list and read the resources a server exposes."""

import warnings

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

    @keyword("Subscribe To Resource")
    def subscribe_to_resource(self, uri, timeout=None):
        """Asks the server to notify the client when this resource changes.

        Updates arrive as ``notifications/resources/updated`` and are
        collected by `Get Resource Update Notifications`. A server that does
        not declare the ``resources.subscribe`` capability will reject this
        with a protocol error.

        The underlying ``resources/subscribe`` request is deprecated in the
        MCP spec (removed as of 2026-07-28, in favour of the SDK's higher-level
        ``Client.listen()``) but still accepted by ``ClientSession`` in this
        SDK version, and still widely implemented by servers. This keyword
        suppresses the resulting deprecation warning and keeps working
        against any server that still supports it.

        Example:
        | Subscribe To Resource | data://counter |
        | Call Tool | increment_counter |
        | Resource Should Have Been Updated | data://counter |
        """
        log_request("resources/subscribe", uri=uri)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._connection.call(
                lambda s: s.subscribe_resource(uri), timeout=self._timeout(timeout)
            )

    @keyword("Unsubscribe From Resource")
    def unsubscribe_from_resource(self, uri, timeout=None):
        """Cancels a subscription made with `Subscribe To Resource`.

        See `Subscribe To Resource` for a note on this method's deprecation.
        """
        log_request("resources/unsubscribe", uri=uri)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._connection.call(
                lambda s: s.unsubscribe_resource(uri), timeout=self._timeout(timeout)
            )

    @keyword("Get Resource Update Notifications")
    def get_resource_update_notifications(self):
        """Returns the URIs of every resource update notification received so far.

        A URI appears once per notification, so a resource updated three
        times appears three times. Accumulates for the life of the
        connection — see `Clear Resource Update Notifications` to reset.

        Example:
        | ${updates}= | Get Resource Update Notifications |
        | Should Contain | ${updates} | data://counter |
        """
        return list(self._connection.resource_updates)

    @keyword("Clear Resource Update Notifications")
    def clear_resource_update_notifications(self):
        """Discards every resource update notification collected so far."""
        self._connection.resource_updates.clear()
