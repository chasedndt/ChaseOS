from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.capture_markdown_proof_accounting import (
    PROOF_LANES,
    build_proof_accounting,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_proofs(root: Path, *, palette_ok: bool = True) -> None:
    for lane in PROOF_LANES:
        payload = {"ok": True, "status": "ok"}
        if lane["id"] == "capture_overlay_palette":
            payload = {
                "ok": palette_ok,
                "proof_type": "capture_palette_model_and_frontend_wiring",
                "palette_option_available": True,
                "palette_action": "open_capture_palette",
                "readiness": {
                    "capture_palette_overlay_ready": True,
                    "capture_palette_overlay_blocked": False,
                },
                "authority": {
                    "adds_new_capture_authority": False,
                    "writes_markdown_on_palette_open": False,
                },
                "frontend_wiring": {
                    "open_capture_palette_function": True,
                    "close_capture_palette_function": True,
                    "source_action_dispatch_function": True,
                    "palette_button": True,
                    "palette_action_buttons": True,
                    "palette_css": True,
                    "palette_action_css": True,
                    "required_actions_present": {"run_display_region_collector": True},
                },
            }
        _write_json(root / lane["path"], payload)


def test_proof_accounting_writes_complete_bundle(tmp_path: Path) -> None:
    _seed_proofs(tmp_path)

    result = build_proof_accounting(
        tmp_path,
        generated_at="2026-05-31T00:00:00Z",
        write=True,
    )

    assert result["ok"] is True
    assert result["status"] == "complete"
    assert result["palette_accounted_alongside_other_lanes"] is True
    assert (tmp_path / result["summary_path"]).exists()
    assert (tmp_path / result["markdown_path"]).exists()
    palette = next(lane for lane in result["lanes"] if lane["id"] == "capture_overlay_palette")
    assert palette["palette_details"]["capture_palette_overlay_ready"] is True
    assert palette["palette_details"]["writes_markdown_on_palette_open"] is False


def test_proof_accounting_fails_when_palette_is_not_ok(tmp_path: Path) -> None:
    _seed_proofs(tmp_path, palette_ok=False)

    result = build_proof_accounting(tmp_path, generated_at="2026-05-31T00:00:00Z")

    assert result["ok"] is False
    assert result["status"] == "incomplete"
    assert "capture_overlay_palette" in result["not_ok_lanes"]
