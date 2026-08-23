"""USD world-bound ray query owned by the Kit application."""

from __future__ import annotations

from pxr import Usd, UsdGeom


def raycast_stage(core, stage, ray):
    """Return the nearest imageable prim bound as an opaque core hit."""

    closest = None
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Imageable):
            continue
        bounds = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]
        ).ComputeWorldBound(prim).ComputeAlignedRange()
        distance = _ray_range_distance(ray, bounds)
        if distance is not None and (closest is None or distance < closest[0]):
            closest = (distance, prim.GetPath().pathString)
    if closest is None:
        return None
    distance, path = closest
    hit = core.SpatialHit()
    hit.position = core.Vec3(
        ray.origin.x + distance * ray.direction.x,
        ray.origin.y + distance * ray.direction.y,
        ray.origin.z + distance * ray.direction.z,
    )
    hit.normal = core.Vec3(0.0, 0.0, 1.0)
    hit.host_id = path
    return hit


def _ray_range_distance(ray, bounds):
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
    return near

