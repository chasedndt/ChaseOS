from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.capture_markdown_open_safety_proof import (
    run_capture_markdown_open_safety_proof,
)
from runtime.studio.capture_ocr_settings import capture_local_image_text_settings_path


def test_capture_markdown_open_safety_proof_blocks_subprocess_and_restores_settings(
    tmp_path: Path,
) -> None:
    settings_path = capture_local_image_text_settings_path(tmp_path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "schema_version": "studio.capture_local_image_text_settings.v1",
                "updated_at_utc": "2026-05-28T00:00:00Z",
                "local_ocr_command": "",
                "local_ocr_timeout_seconds": 20,
            }
        ),
        encoding="utf-8",
    )
    original_settings = settings_path.read_text(encoding="utf-8")

    proof = run_capture_markdown_open_safety_proof(
        vault_root=tmp_path,
        evidence_slug="unit-capture-open-safety",
        write_evidence=True,
    )

    assert proof["ok"] is True
    assert proof["status"] == "capture_markdown_open_safety_verified"
    assert proof["subprocess_calls"] == []
    assert proof["marker_command"]["marker_exists_after_surface_load"] is False
    assert proof["cleanup"]["settings_restored"] is True
    assert proof["cleanup"]["scratch_removed"] is True
    assert settings_path.read_text(encoding="utf-8") == original_settings

    checks = proof["verification"]["checks"]
    assert checks["shell_launcher_rejected_before_persistence"] is True
    assert checks["marker_command_not_executed_on_load"] is True
    assert checks["subprocess_run_or_popen_not_called"] is True
    assert checks["studio_executables_unchanged"] is True

    evidence = proof["evidence"]
    json_path = tmp_path / evidence["json_path"]
    markdown_path = tmp_path / evidence["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert json.loads(json_path.read_text(encoding="utf-8"))["ok"] is True
    assert "subprocess_run_or_popen_not_called" in markdown_path.read_text(encoding="utf-8")


def test_capture_markdown_open_safety_proof_removes_transient_settings_when_absent(
    tmp_path: Path,
) -> None:
    proof = run_capture_markdown_open_safety_proof(
        vault_root=tmp_path,
        evidence_slug="unit-capture-open-safety-no-settings",
        write_evidence=False,
    )

    assert proof["ok"] is True
    assert proof["cleanup"]["settings_restored"] is True
    assert not capture_local_image_text_settings_path(tmp_path).exists()
