"""Real Kit/OpenUSD integration check used by kit-ci."""

from __future__ import annotations

import carb
import omni.kit.app
import omni.usd
import platform
import sys
from pxr import Usd, UsdGeom

import miskeyed.xr.agent as core

from .adapter import KitXRAdapter, KitXRBridge, KitXRSample


def run() -> None:
    """Ground one real core frame against a prim in Kit's active USD context."""

    wheel_details = (
        "CORE_WHEEL "
        f"python={sys.version} executable={sys.executable} "
        f"abi={sys.implementation.cache_tag} os={platform.system()} "
        f"arch={platform.machine()} module={core.__file__}"
    )
    carb.log_info(f"[miskeyed.kit.xr_agent] {wheel_details}")
    print(wheel_details, flush=True)
    context = omni.usd.get_context()
    context.new_stage()
    stage = context.get_stage()
    if stage is None:
        raise RuntimeError("Kit USD context did not create a stage")

    target_path = "/World/Target"
    UsdGeom.Cube.Define(stage, target_path)
    if stage.GetPrimAtPath(target_path).GetPath().pathString != target_path:
        raise RuntimeError("target prim is not available through Kit's USD context")

    frame = KitXRAdapter(KitXRBridge("kit-ci", object()), core).to_frame(
        KitXRSample(
            timestamp_ns=1_000_000,
            timestamp_domain="kit.update:ci",
            reference_space_type="LOCAL",
            reference_space_id="kit-ci-local",
            reference_space_generation=0,
            head_position=(0.0, 0.0, 2.0),
            head_orientation=(0.0, 0.0, 0.0, 1.0),
            head_tracking=core.TrackingConfidence.POSITION_AND_ORIENTATION,
            aim_origin=(0.0, 0.0, 2.0),
            aim_direction=(0.0, 0.0, -1.0),
            pointing_source=core.PointingSource.CONTROLLER,
            pointing_confidence=core.TrackingConfidence.POSITION_AND_ORIENTATION,
        )
    )

    def kit_usd_query(ray):
        prim = stage.GetPrimAtPath(target_path)
        bounds = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]
        ).ComputeWorldBound(prim).ComputeAlignedRange()
        minimum, maximum = bounds.GetMin(), bounds.GetMax()
        origin = (ray.origin.x, ray.origin.y, ray.origin.z)
        direction = (ray.direction.x, ray.direction.y, ray.direction.z)
        near, far = 0.0, float("inf")
        for axis in range(3):
            if abs(direction[axis]) < 1e-12:
                if origin[axis] < minimum[axis] or origin[axis] > maximum[axis]:
                    return None
                continue
            first = (minimum[axis] - origin[axis]) / direction[axis]
            second = (maximum[axis] - origin[axis]) / direction[axis]
            near = max(near, min(first, second))
            far = min(far, max(first, second))
            if near > far:
                return None
        hit = core.SpatialHit()
        hit.position = core.Vec3(
            *(origin[axis] + near * direction[axis] for axis in range(3))
        )
        hit.normal = core.Vec3(0.0, 0.0, 1.0)
        hit.host_id = target_path
        return hit

    grounded = core.resolve_target(frame, kit_usd_query)
    timeline = core.IntentTimeline()
    timeline.push(grounded)
    event = timeline.submit_text("move this there", frame.timestamp_ns)
    result = core.to_dict(event)
    if result["spatial_context"]["target"]["host_id"] != target_path:
        raise RuntimeError("grounded request did not preserve the USD SdfPath")
    success = f"KIT_CI_PASS {result}"
    carb.log_info(f"[miskeyed.kit.xr_agent] {success}")
    print(success, flush=True)
