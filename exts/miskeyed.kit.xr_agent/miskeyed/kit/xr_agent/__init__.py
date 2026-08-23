"""Kit XR adapter package and standard Kit extension entry point."""

import os

if os.environ.get("MISKEYED_KIT_ADAPTER_ONLY") != "1":
    from .extension import MiskeyedXRExtension

    __all__ = ["MiskeyedXRExtension"]
else:
    __all__ = []
