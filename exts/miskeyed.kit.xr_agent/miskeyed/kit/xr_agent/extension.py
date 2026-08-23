from __future__ import annotations

import carb
import omni.ext

from .adapter import IntegrationContractError, KitXRAdapter, discover_kit_xr, load_core_contract


class MiskeyedXRExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:
        self._adapter = None
        carb.log_info(f"[miskeyed.xr] starting {ext_id}")
        try:
            bridge = discover_kit_xr()
            core = load_core_contract()
            self._adapter = KitXRAdapter(bridge, core)
            carb.log_info(f"[miskeyed.xr] XR runtime bridge discovered: {bridge.module_name}")
        except IntegrationContractError as exc:
            carb.log_error(f"[miskeyed.xr] integration blocked: {exc}")

    def on_shutdown(self) -> None:
        # Dropping borrowed interfaces is all we own; Kit shuts down OpenXR.
        self._adapter = None

