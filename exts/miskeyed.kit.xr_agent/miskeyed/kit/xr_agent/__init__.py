"""Kit XR adapter package and standard Kit extension entry point."""

import sys

if "omni.ext" in sys.modules:
    from .extension import MiskeyedXRExtension

    __all__ = ["MiskeyedXRExtension"]
else:
    __all__ = []
