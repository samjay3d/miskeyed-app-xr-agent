"""Kit XR adapter package and standard Kit extension entry point."""

from importlib.util import find_spec

if find_spec("omni") is not None and find_spec("omni.ext") is not None:
    from .extension import MiskeyedXRExtension

    __all__ = ["MiskeyedXRExtension"]
else:
    __all__ = []
