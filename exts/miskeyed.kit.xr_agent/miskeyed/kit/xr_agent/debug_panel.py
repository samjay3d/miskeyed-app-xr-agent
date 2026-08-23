"""Small deterministic desktop debug panel for the first XR milestone."""

import omni.ui as ui


class XRDebugPanel:
    def __init__(self, submit_callback) -> None:
        self._models = {
            name: ui.SimpleStringModel("-")
            for name in ("head", "pointing", "ray", "hit", "grounded")
        }
        self.text_model = ui.SimpleStringModel("")
        self.window = ui.Window("Miskeyed XR Intent", width=460, height=260)
        with self.window.frame:
            with ui.VStack(spacing=4):
                for name in ("head", "pointing", "ray", "hit", "grounded"):
                    with ui.HStack(height=24):
                        ui.Label(f"{name.title()}:", width=80)
                        ui.Label(self._models[name])
                with ui.HStack(height=28):
                    ui.StringField(self.text_model)
                    ui.Button("Submit", width=80, clicked_fn=submit_callback)

    def show_frame(self, payload: dict) -> None:
        head = payload.get("head_pose") or {}
        pointing = payload.get("pointing") or {}
        self._models["head"].set_value(str(head.get("position", "unavailable")))
        self._models["pointing"].set_value(str(pointing.get("source", "unavailable")))
        self._models["ray"].set_value(str(pointing.get("ray", "unavailable")))
        target = payload.get("target") or {}
        self._models["hit"].set_value(str(target.get("host_id", "miss")))

    def show_grounded(self, payload: dict) -> None:
        self._models["grounded"].set_value(str(payload))

    def destroy(self) -> None:
        self.window = None

