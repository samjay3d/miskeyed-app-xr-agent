from __future__ import annotations

import carb
import omni.ext
import omni.kit.app

from .adapter import (
    IntegrationContractError,
    KitXRAdapter,
    KitXRBridge,
    discover_kit_xr,
    load_core_contract,
)


class MiskeyedXRExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:
        self._adapter = None
        self._update_subscription = None
        carb.log_info(f"[miskeyed.xr] starting {ext_id}")
        ci_smoke = carb.settings.get_settings().get_as_bool("/miskeyed/kit/xr_agent/ciSmoke")
        try:
            core = load_core_contract()
            bridge = KitXRBridge("kit-ci", object()) if ci_smoke else discover_kit_xr()
            self._adapter = KitXRAdapter(bridge, core)
            carb.log_info(f"[miskeyed.xr] XR runtime bridge discovered: {bridge.module_name}")
        except IntegrationContractError as exc:
            carb.log_error(f"[miskeyed.xr] integration blocked: {exc}")

        if ci_smoke:
            self._update_subscription = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
                self._run_ci_smoke, name="miskeyed.kit.xr_agent.ci_smoke"
            )

    def _run_ci_smoke(self, _event) -> None:
        self._update_subscription = None
        from .ci_smoke import run

        try:
            run()
        except Exception as exc:
            carb.log_error(f"[miskeyed.kit.xr_agent] KIT_CI_FAIL: {exc}")
            omni.kit.app.get_app().post_quit(1)
            raise
        omni.kit.app.get_app().post_quit(0)

    def on_shutdown(self) -> None:
        # Dropping borrowed interfaces is all we own; Kit shuts down OpenXR.
        self._adapter = None
        self._update_subscription = None
        if carb.settings.get_settings().get_as_bool("/miskeyed/kit/xr_agent/ciSmoke"):
            carb.log_info("[miskeyed.kit.xr_agent] KIT_CI_UNLOAD")
