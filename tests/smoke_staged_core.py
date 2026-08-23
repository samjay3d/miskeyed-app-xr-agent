"""Exercise the staged native core through the adapter, as Kit will import it."""

from miskeyed.xr import agent as core
from miskeyed_kit_xr.adapter import KitXRAdapter, KitXRBridge, KitXRSample


adapter = KitXRAdapter(KitXRBridge("ci.kit-owned-placeholder", object()), core)
frame = adapter.to_frame(
    KitXRSample(
        timestamp_ns=42,
        timestamp_domain="kit.xr:ci",
        reference_space_type="LOCAL",
        reference_space_id="ci-local-space",
        reference_space_generation=2,
        head_position=(1.0, 2.0, 3.0),
        head_orientation=(0.0, 0.0, 0.0, 1.0),
        head_tracking=core.TrackingConfidence.POSITION_AND_ORIENTATION,
        aim_origin=(1.0, 2.0, 3.0),
        aim_direction=(0.0, 0.0, -1.0),
        pointing_source=core.PointingSource.CONTROLLER,
        pointing_confidence=core.TrackingConfidence.POSITION_AND_ORIENTATION,
    )
)

assert frame.timestamp_ns == 42
assert frame.timestamp_domain == "kit.xr:ci"
assert frame.reference_space.id == "ci-local-space"
assert frame.reference_space.generation == 2
assert frame.pointing is not None
assert core.to_dict(frame)["reference_space"]["id"] == "ci-local-space"
