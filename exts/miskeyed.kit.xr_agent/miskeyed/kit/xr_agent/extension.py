from __future__ import annotations

import carb
import omni.ext
import omni.kit.app
import omni.usd

from .adapter import (
    IntegrationContractError,
    KitXRAdapter,
    KitXRBridge,
    discover_kit_xr,
    load_core_contract,
)


class MiskeyedXRExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:
        self._ext_id = ext_id
        self._ci_completed = False
        self._adapter = None
        self._update_subscription = None
        self._debug_panel = None
        self._timeline = None
        self._latest_timestamp_ns = 0
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
        elif self._adapter is not None:
            from .debug_panel import XRDebugPanel

            self._timeline = core.IntentTimeline()
            self._debug_panel = XRDebugPanel(self._submit_text)
            self._update_subscription = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
                self._on_xr_update, name="miskeyed.kit.xr_agent.live_update"
            )

    def _on_xr_update(self, _event) -> None:
        settings = carb.settings.get_settings()
        app = omni.kit.app.get_app()
        timestamp_ns = int(app.get_time_since_start_s() * 1_000_000_000)
        try:
            frame = self._adapter.sample_head(
                timestamp_ns,
                "kit.app.time_since_start",
                settings.get_as_string("/persistent/xr/anchorMode"),
                settings.get_as_string("/xrstage/customAnchor"),
            )
        except IntegrationContractError:
            return
        stage = omni.usd.get_context().get_stage()
        if stage is not None and frame.pointing is not None:
            from .scene_query import raycast_stage

            frame = self._adapter.core.resolve_target(
                frame, lambda ray: raycast_stage(self._adapter.core, stage, ray)
            )
        self._timeline.push(frame)
        self._latest_timestamp_ns = timestamp_ns
        self._debug_panel.show_frame(self._adapter.core.to_dict(frame))

    def _submit_text(self) -> None:
        text = self._debug_panel.text_model.get_value_as_string().strip()
        if not text or not self._latest_timestamp_ns:
            return
        event = self._timeline.submit_text(text, self._latest_timestamp_ns)
        if event is not None:
            self._debug_panel.show_grounded(self._adapter.core.to_dict(event))

    def _run_ci_smoke(self, _event) -> None:
        if self._ci_completed:
            return
        self._ci_completed = True
        self._update_subscription = None
        if self._debug_panel is not None:
            self._debug_panel.destroy()
            self._debug_panel = None
        self._timeline = None
        from .ci_smoke import run

        try:
            run()
        except Exception as exc:
            carb.log_error(f"[miskeyed.kit.xr_agent] KIT_CI_FAIL: {exc}")
            omni.kit.app.get_app().post_quit(1)
            raise
        omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate(
            self._ext_id, False
        )

    def on_shutdown(self) -> None:
        # Dropping borrowed interfaces is all we own; Kit shuts down OpenXR.
        self._adapter = None
        self._update_subscription = None
        if carb.settings.get_settings().get_as_bool("/miskeyed/kit/xr_agent/ciSmoke"):
            carb.log_info("[miskeyed.kit.xr_agent] KIT_CI_UNLOAD")
            print("KIT_CI_UNLOAD", flush=True)
            omni.kit.app.get_app().post_quit(0)
