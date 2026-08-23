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
    """Acquire Kit 110.2's supported XRCore singleton."""

    try:
        module = importer("omni.kit.xr.core")
    except ImportError as exc:
        raise IntegrationContractError("omni.kit.xr.core is unavailable") from exc
    xr_core_type = getattr(module, "XRCore", None)
    if xr_core_type is None:
        raise IntegrationContractError("omni.kit.xr.core does not export XRCore")
    interface = xr_core_type.get_singleton()
    if interface is None:
        raise IntegrationContractError("XRCore.get_singleton() returned no Kit XR interface")
    return KitXRBridge("omni.kit.xr.core.XRCore", interface)


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
        "Kit dependency bundle must provide miskeyed-xr-agent==0.1.0; " + "; ".join(errors)
    )


class KitXRAdapter:
    """Thin adapter awaiting validation of the concrete Kit/core pose contracts."""

    def __init__(self, bridge: KitXRBridge, core: ModuleType) -> None:
        self.bridge = bridge
        self.core = core
        self._space_key: Optional[tuple[str, str]] = None
        self._space_generation = 0

    def sample_head(
        self,
        timestamp_ns: int,
        timestamp_domain: str,
        anchor_mode: str,
        anchor_path: str,
    ) -> Any:
        """Read Kit's head and right-controller virtual-world poses into a frame."""

        head = self.bridge.interface.get_input_device("/user/head")
        if head is None:
            raise IntegrationContractError("Kit XR head input device is unavailable")
        head_pose = _matrix_pose(head.get_virtual_world_pose(""))
        controller = self.bridge.interface.get_input_device("/user/hand/right")
        aim_origin = None
        aim_direction = None
        if controller is not None:
            controller_matrix = controller.get_virtual_world_pose()
            aim_pose = _matrix_pose(controller_matrix)
            direction = controller_matrix.TransformDir((0.0, 0.0, -1.0)).GetNormalized()
            aim_origin = aim_pose[0]
            aim_direction = tuple(float(direction[index]) for index in range(3))

        space_key = (anchor_mode or "kit-virtual-world", anchor_path or "/")
        if self._space_key is not None and space_key != self._space_key:
            self._space_generation += 1
        self._space_key = space_key
        sample = KitXRSample(
            timestamp_ns=timestamp_ns,
            timestamp_domain=timestamp_domain,
            reference_space_type="KIT_VIRTUAL_WORLD",
            reference_space_id=f"{space_key[0]}:{space_key[1]}",
            reference_space_generation=self._space_generation,
            head_position=head_pose[0],
            head_orientation=head_pose[1],
            head_tracking=self.core.TrackingConfidence.POSITION_AND_ORIENTATION,
            aim_origin=aim_origin,
            aim_direction=aim_direction,
            pointing_source=self.core.PointingSource.CONTROLLER if controller else None,
            pointing_confidence=(
                self.core.TrackingConfidence.POSITION_AND_ORIENTATION if controller else None
            ),
        )
        return self.to_frame(sample)

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
    pointing_confidence: Any = None

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


def _matrix_pose(matrix: Any) -> tuple[tuple[float, float, float], tuple[float, float, float, float]]:
    translation = matrix.ExtractTranslation()
    quaternion = matrix.ExtractRotationQuat()
    imaginary = quaternion.GetImaginary()
    return (
        tuple(float(translation[index]) for index in range(3)),
        (
            float(imaginary[0]),
            float(imaginary[1]),
            float(imaginary[2]),
            float(quaternion.GetReal()),
        ),
    )
