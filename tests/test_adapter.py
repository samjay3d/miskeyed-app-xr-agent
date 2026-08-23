from types import SimpleNamespace

import pytest

from miskeyed_kit_xr.adapter import IntegrationContractError, discover_kit_xr, load_core_contract


def test_discovers_borrowed_kit_interface_without_openxr_construction():
    borrowed = object()
    imported = []

    def importer(name):
        imported.append(name)
        return SimpleNamespace(get_xr_interface=lambda: borrowed)

    bridge = discover_kit_xr(importer)
    assert bridge.interface is borrowed
    assert imported == ["omni.kit.xr.core"]


def test_missing_kit_bridge_fails_instead_of_mocking_tracking():
    def importer(name):
        raise ImportError("not installed")

    with pytest.raises(IntegrationContractError, match="Kit-owned XR bridge unavailable"):
        discover_kit_xr(importer)


def test_core_contract_is_loaded_from_package():
    real_module = SimpleNamespace(SpatialIntentFrame=object, IntentTimeline=object)
    assert load_core_contract(lambda _name: real_module) is real_module

