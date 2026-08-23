import os
from types import SimpleNamespace

import pytest

os.environ["MISKEYED_KIT_ADAPTER_ONLY"] = "1"

from miskeyed.kit.xr_agent.adapter import (
    IntegrationContractError,
    KitXRAdapter,
    KitXRBridge,
    KitXRSample,
    discover_kit_xr,
    load_core_contract,
)


def test_discovers_borrowed_kit_interface_without_openxr_construction():
    borrowed = object()
    imported = []

    def importer(name):
        imported.append(name)
        return SimpleNamespace(XRCore=SimpleNamespace(get_singleton=lambda: borrowed))

    bridge = discover_kit_xr(importer)
    assert bridge.interface is borrowed
    assert imported == ["omni.kit.xr.core"]


def test_missing_kit_bridge_fails_instead_of_mocking_tracking():
    def importer(name):
        raise ImportError("not installed")

    with pytest.raises(IntegrationContractError, match="omni.kit.xr.core is unavailable"):
        discover_kit_xr(importer)


def test_core_contract_is_loaded_from_package():
    real_module = SimpleNamespace(SpatialIntentFrame=object, IntentTimeline=object)
    assert load_core_contract(lambda _name: real_module) is real_module


def test_adapter_preserves_host_time_and_reference_space():
    class Value:
        def __init__(self, *values):
            self.values = values

    class Mutable:
        pass

    core = SimpleNamespace(
        SpatialIntentFrame=Mutable,
        ReferenceSpace=Mutable,
        Pose=Mutable,
        Vec3=Value,
        Quaternion=Value,
        PointingIntent=Mutable,
        Ray=Value,
    )
    tracking = object()
    frame = KitXRAdapter(KitXRBridge("kit", object()), core).to_frame(
        KitXRSample(
            timestamp_ns=123456,
            timestamp_domain="kit.xr:106.5",
            reference_space_type="LOCAL",
            reference_space_id="kit-openxr-local",
            reference_space_generation=7,
            head_position=(1.0, 2.0, 3.0),
            head_orientation=(0.0, 0.0, 0.0, 1.0),
            head_tracking=tracking,
        )
    )
    assert frame.timestamp_ns == 123456
    assert frame.timestamp_domain == "kit.xr:106.5"
    assert frame.reference_space.id == "kit-openxr-local"
    assert frame.reference_space.generation == 7
    assert frame.head_tracking is tracking


def test_sample_rejects_partial_aim_and_missing_clock_identity():
    common = dict(
        timestamp_ns=1,
        timestamp_domain="kit.xr:test",
        reference_space_type="LOCAL",
        reference_space_id="local",
        reference_space_generation=0,
        head_position=(0.0, 0.0, 0.0),
        head_orientation=(0.0, 0.0, 0.0, 1.0),
        head_tracking=None,
    )
    with pytest.raises(ValueError, match="appear together"):
        KitXRSample(**common, aim_origin=(0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="timestamp domain"):
        KitXRSample(**(common | {"timestamp_domain": ""}))
