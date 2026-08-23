"""Shared Miskeyed namespace across Kit extensions and released packages."""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

