"""Boundary between a Kit-owned XR session and miskeyed-xr-agent.

There are deliberately no OpenXR bindings in this module. Kit owns that
lifecycle; this adapter consumes the public state interface Kit provides.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable


class IntegrationContractError(RuntimeError):
    """The installed Kit/core versions do not expose the required contract."""


@dataclass(frozen=True)
class KitXRBridge:
    """Discovered Kit module and its existing, Kit-owned XR interface."""

    module_name: str
    interface: Any


def discover_kit_xr(importer: Callable[[str], ModuleType] = import_module) -> KitXRBridge:
    """Find an existing Kit XR interface without initializing OpenXR ourselves."""

    attempts: list[str] = []
    for module_name in ("omni.kit.xr.core", "omni.kit.xr.system.core"):
        try:
            module = importer(module_name)
        except ImportError as exc:
            attempts.append(f"{module_name}: {exc}")
            continue
        for accessor in ("get_xr_interface", "get_interface"):
            factory = getattr(module, accessor, None)
            if callable(factory):
                interface = factory()
                if interface is not None:
                    return KitXRBridge(module_name, interface)
        attempts.append(f"{module_name}: no public interface accessor")
    raise IntegrationContractError("Kit-owned XR bridge unavailable; " + "; ".join(attempts))


def load_core_contract(importer: Callable[[str], ModuleType] = import_module) -> ModuleType:
    """Load the real core public API; never substitute local domain objects."""

    errors: list[str] = []
    for module_name in ("miskeyed_xr_agent", "miskeyed.xr_agent"):
        try:
            module = importer(module_name)
        except ImportError as exc:
            errors.append(f"{module_name}: {exc}")
            continue
        missing = [name for name in ("SpatialIntentFrame", "IntentTimeline") if not hasattr(module, name)]
        if not missing:
            return module
        errors.append(f"{module_name}: missing {', '.join(missing)}")
    raise IntegrationContractError(
        "install the current miskeyed-xr-agent source checkout; " + "; ".join(errors)
    )


class KitXRAdapter:
    """Thin adapter awaiting validation of the concrete Kit/core pose contracts."""

    def __init__(self, bridge: KitXRBridge, core: ModuleType) -> None:
        self.bridge = bridge
        self.core = core

    def sample_head(self) -> Any:
        raise IntegrationContractError(
            "live head-pose accessor is unverified for this Kit release; see F-001"
        )

