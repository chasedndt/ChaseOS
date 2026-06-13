from __future__ import annotations

from pathlib import Path

from runtime.browser_runtime.canva_style_autonomy_proof import (
    CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS,
    CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION,
    CANVA_STYLE_AUTONOMY_PROOF_COMPLETE,
    CanvaStyleAutonomyProofRequest,
    run_canva_style_autonomy_proof,
)


class FakeCanvaController:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.state = {
            "templateSelected": False,
            "canvasCleared": False,
            "fakeAssetsLoaded": False,
            "photoLayerAdded": False,
            "photoFrameAdded": False,
            "photoFrameResized": False,
            "circleFeatureAdded": False,
            "penDrawingEnabled": False,
            "manualDrawingAdded": False,
            "manualDrawingPointCount": 0,
            "magicLayersCreated": False,
            "brandApplied": False,
            "resizeApplied": False,
            "photoFrameSize": {"width": 0, "height": 0},
            "featureBadgeText": "",
            "exportBlocked": False,
            "publicShareBlocked": False,
            "accountSettingsBlocked": False,
            "agentControlVisible": True,
            "agentCursorMoved": False,
            "agentClickFeedbackShown": False,
            "agentDragFeedbackShown": False,
            "agentControlLane": "browser",
            "futureControlLanes": ["files", "system", "runtime"],
            "layers": [],
        }

    def ensure_available(self) -> dict[str, object]:
        self.calls.append("ensure_available")
        return {"available": True}

    def open(self, url: str) -> dict[str, object]:
        self.calls.append("open")
        return {"opened_url": url, "profile_policy": "throwaway_only"}

    def read_state(self) -> dict[str, object]:
        self.calls.append("read_state")
        return {"title": "SiteOps Canva Style Shadow Target", "editor_state": dict(self.state)}

    def click_testid(self, testid: str) -> dict[str, object]:
        self.calls.append(f"click:{testid}")
        mapping = {
            "select-poster-template": ("templateSelected", "template"),
            "load-fake-assets": ("fakeAssetsLoaded", "fake-assets"),
            "add-photo-placeholder": ("photoLayerAdded", "photo"),
            "add-photo-frame": ("photoFrameAdded", "photo-frame"),
            "add-feature-circle": ("circleFeatureAdded", "feature-circle"),
            "enable-pen-drawing": ("penDrawingEnabled", None),
            "run-magic-layers": ("magicLayersCreated", "headline"),
            "apply-brand-kit": ("brandApplied", None),
            "resize-social": ("resizeApplied", None),
            "export-file": ("exportBlocked", None),
            "public-share": ("publicShareBlocked", None),
            "account-settings": ("accountSettingsBlocked", None),
        }
        if testid == "clear-canvas":
            self.state.update(
                {
                    "templateSelected": False,
                    "fakeAssetsLoaded": False,
                    "photoLayerAdded": False,
                    "photoFrameAdded": False,
                    "photoFrameResized": False,
                    "circleFeatureAdded": False,
                    "penDrawingEnabled": False,
                    "manualDrawingAdded": False,
                    "manualDrawingPointCount": 0,
                    "magicLayersCreated": False,
                    "brandApplied": False,
                    "resizeApplied": False,
                    "photoFrameSize": {"width": 0, "height": 0},
                    "featureBadgeText": "",
                    "exportBlocked": False,
                    "publicShareBlocked": False,
                    "accountSettingsBlocked": False,
                    "layers": [],
                    "canvasCleared": True,
                }
            )
            self.state["agentCursorMoved"] = True
            self.state["agentClickFeedbackShown"] = True
            return {"ok": True, "testid": testid, "state": dict(self.state)}
        key, layer = mapping[testid]
        self.state["agentCursorMoved"] = True
        self.state["agentClickFeedbackShown"] = True
        self.state[key] = True
        if testid == "add-photo-frame":
            self.state["photoFrameSize"] = {"width": 128, "height": 120}
        if testid == "add-feature-circle":
            self.state["featureBadgeText"] = "NEW FEATURE"
        if layer:
            self.state["layers"].append(layer)
        return {"ok": True, "testid": testid, "state": dict(self.state)}

    def drag_testid(self, testid: str, delta_x: int, delta_y: int) -> dict[str, object]:
        self.calls.append(f"drag:{testid}:{delta_x}:{delta_y}")
        self.state["agentCursorMoved"] = True
        self.state["agentDragFeedbackShown"] = True
        if testid == "poster-drawing-surface":
            self.state["manualDrawingAdded"] = True
            self.state["manualDrawingPointCount"] = 9
            self.state["layers"].append("manual-drawing")
            return {"ok": True, "testid": testid, "deltaX": delta_x, "deltaY": delta_y, "state": dict(self.state)}
        if testid != "photo-frame-resize-handle":
            return {"ok": False, "reason": "unexpected_testid"}
        self.state["photoFrameResized"] = True
        self.state["photoFrameSize"] = {"width": 128 + delta_x, "height": 120 + delta_y}
        return {"ok": True, "testid": testid, "deltaX": delta_x, "deltaY": delta_y, "state": dict(self.state)}

    def capture_screenshot(self) -> bytes:
        self.calls.append("capture_screenshot")
        return b"fake-canva-style-png"

    def close(self) -> None:
        self.calls.append("close")


def _request(**overrides: object) -> CanvaStyleAutonomyProofRequest:
    payload = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "requested_by": "Codex",
        "operator_id": "local-user",
        "execute_browser": True,
        "run_slug": "canva-style-proof-test",
    }
    payload.update(overrides)
    return CanvaStyleAutonomyProofRequest(**payload)


def test_no_execute_blocks_without_writes(tmp_path: Path) -> None:
    result = run_canva_style_autonomy_proof(
        tmp_path,
        _request(execute_browser=False),
        generated_at="2026-05-04T15:30:00Z",
        controller=FakeCanvaController(),
    )

    assert result.status == CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION
    assert result.browser_launch_attempted is False
    assert not list(tmp_path.rglob("*"))


def test_injected_canva_style_proof_writes_scoped_artifacts(tmp_path: Path) -> None:
    result = run_canva_style_autonomy_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-04T15:35:00Z",
        controller=FakeCanvaController(),
    )

    assert result.status == CANVA_STYLE_AUTONOMY_PROOF_COMPLETE
    assert result.final_design_state["canvasCleared"] is True
    assert result.final_design_state["templateSelected"] is True
    assert result.final_design_state["fakeAssetsLoaded"] is True
    assert result.final_design_state["photoLayerAdded"] is True
    assert result.final_design_state["photoFrameAdded"] is True
    assert result.final_design_state["photoFrameResized"] is True
    assert result.final_design_state["circleFeatureAdded"] is True
    assert result.final_design_state["penDrawingEnabled"] is True
    assert result.final_design_state["manualDrawingAdded"] is True
    assert result.final_design_state["manualDrawingPointCount"] == 9
    assert result.final_design_state["featureBadgeText"] == "NEW FEATURE"
    assert result.final_design_state["photoFrameSize"]["width"] == 216
    assert result.final_design_state["photoFrameSize"]["height"] == 172
    assert result.final_design_state["magicLayersCreated"] is True
    assert result.final_design_state["brandApplied"] is True
    assert result.final_design_state["resizeApplied"] is True
    assert result.final_design_state["exportBlocked"] is True
    assert result.final_design_state["publicShareBlocked"] is True
    assert result.final_design_state["accountSettingsBlocked"] is True
    assert result.final_design_state["agentControlVisible"] is True
    assert result.final_design_state["agentCursorMoved"] is True
    assert result.final_design_state["agentClickFeedbackShown"] is True
    assert result.final_design_state["agentDragFeedbackShown"] is True
    assert result.final_design_state["agentControlLane"] == "browser"
    assert Path(result.browser_run_log_path).exists()
    assert Path(result.screenshot_path).read_bytes() == b"fake-canva-style-png"
    assert Path(result.siteops_run_path).exists()
    assert Path(result.siteops_audit_path).exists()
    assert all(value is False for value in result.denied_effects.values())


def test_duplicate_marker_blocks_before_browser(tmp_path: Path) -> None:
    run_canva_style_autonomy_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-04T15:35:00Z",
        controller=FakeCanvaController(),
    )
    controller = FakeCanvaController()
    result = run_canva_style_autonomy_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-04T15:35:00Z",
        controller=controller,
    )

    assert result.status == CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS
    assert result.browser_launch_attempted is False
    assert controller.calls == []
