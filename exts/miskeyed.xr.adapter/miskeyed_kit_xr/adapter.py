"""Boundary between a Kit-owned XR session and miskeyed-xr-agent.

There are deliberately no OpenXR bindings in this module. Kit owns that
lifecycle; this adapter consumes the public state interface Kit provides.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Optional


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
    for module_name in ("omni.kit.xr.system.openxr", "omni.kit.xr.core", "omni.kit.xr.system.core"):
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
    for module_name in ("miskeyed.xr.agent",):
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

    def to_frame(self, sample: "KitXRSample") -> Any:
        """Translate a validated Kit sample without changing its time/space identity."""

        core = self.core
        frame = core.SpatialIntentFrame()
        frame.timestamp_ns = sample.timestamp_ns
        frame.timestamp_domain = sample.timestamp_domain
        frame.reference_space = core.ReferenceSpace()
        frame.reference_space.type = sample.reference_space_type
        frame.reference_space.id = sample.reference_space_id
        frame.reference_space.generation = sample.reference_space_generation
        frame.head_pose = _pose(core, sample.head_position, sample.head_orientation)
        frame.head_tracking = sample.head_tracking
        if sample.aim_origin is not None and sample.aim_direction is not None:
            pointing = core.PointingIntent()
            pointing.ray = core.Ray(
                core.Vec3(*sample.aim_origin), core.Vec3(*sample.aim_direction)
            )
            pointing.source = sample.pointing_source
            pointing.confidence = sample.pointing_confidence
            frame.pointing = pointing
        return frame


@dataclass(frozen=True)
class KitXRSample:
    """Values read from Kit, with host clock and reference-space metadata intact."""

    timestamp_ns: int
    timestamp_domain: str
    reference_space_type: str
    reference_space_id: str
    reference_space_generation: int
    head_position: tuple[float, float, float]
    head_orientation: tuple[float, float, float, float]
    head_tracking: Any
    aim_origin: Optional[tuple[float, float, float]] = None
    aim_direction: Optional[tuple[float, float, float]] = None
    pointing_source: Any = None
    pointing_confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp_domain or not self.reference_space_id:
            raise ValueError("Kit timestamp domain and reference-space identity are required")
        if self.reference_space_generation < 0:
            raise ValueError("reference-space generation cannot be negative")
        if (self.aim_origin is None) != (self.aim_direction is None):
            raise ValueError("aim origin and direction must appear together")


def _pose(core: ModuleType, position: tuple[float, float, float], orientation: tuple[float, float, float, float]) -> Any:
    pose = core.Pose()
    pose.position = core.Vec3(*position)
    pose.orientation = core.Quaternion(*orientation)
    return pose
