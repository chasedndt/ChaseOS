from __future__ import annotations

from pathlib import Path

from runtime.studio.capture_collector_settings import load_capture_collector_settings
from runtime.studio.capture_markdown_image_to_markdown_live_proof import (
    PROOF_LINES,
    decode_proof_image_text,
    render_proof_image,
    run_capture_markdown_image_to_markdown_live_proof,
)
from runtime.studio.capture_to_markdown_panel import build_capture_to_markdown_panel


def test_proof_pixel_engine_reads_generated_image_text(tmp_path: Path) -> None:
    image_bytes, _width, _height = render_proof_image(PROOF_LINES)
    image_path = tmp_path / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown" / "proof.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(image_bytes)

    assert decode_proof_image_text(image_path) == "\n".join(PROOF_LINES)


def test_image_to_markdown_live_proof_captures_extracts_and_saves_markdown(tmp_path: Path) -> None:
    proof = run_capture_markdown_image_to_markdown_live_proof(
        vault_root=tmp_path,
        evidence_slug="2026-05-28-capture-markdown-image-to-markdown-live-proof-test",
        write_evidence=True,
    )

    assert proof["ok"] is True
    assert proof["status"] == "capture_markdown_image_to_markdown_live_proof_verified"
    assert proof["authority"]["uses_screen_capture_collector"] is True
    assert proof["authority"]["captures_personal_ambient_screen"] is False
    assert proof["authority"]["calls_cloud_optical_character_recognition"] is False
    assert proof["capture"]["status"] == "screen_capture_ready_for_markdown"
    assert proof["capture"]["source_mode"] == "screenshot_attachment"
    assert proof["preview"]["capture_method"] == "screenshot_local_text_extraction"
    assert proof["preview"]["contains_extracted_text"] is True
    assert proof["save"]["write_performed"] is True

    checks = proof["verification"]["checks"]
    assert checks["captured_image_sha256_matches_rendered_fixture"] is True
    assert checks["preview_contains_extracted_image_text"] is True
    assert checks["saved_markdown_contains_extracted_image_text"] is True
    assert checks["settings_restored_after_run"] is True

    artifacts = proof["verification"]["artifact_paths"]
    saved_markdown = tmp_path / artifacts["saved_markdown"]
    captured_image = tmp_path / artifacts["captured_image"]
    assert saved_markdown.is_file()
    assert captured_image.is_file()
    markdown_text = saved_markdown.read_text(encoding="utf-8")
    assert "\n".join(PROOF_LINES) in markdown_text
    assert "Extraction status: `text_extracted`" in markdown_text

    assert (tmp_path / proof["evidence"]["json_path"]).is_file()
    assert (tmp_path / proof["evidence"]["markdown_path"]).is_file()
    assert not (tmp_path / "runtime" / "studio" / "state" / "capture-collectors.json").exists()
    settings = load_capture_collector_settings(tmp_path)
    assert settings["screen_capture_enabled"] is False


def test_image_to_markdown_live_proof_marks_release_readiness(tmp_path: Path) -> None:
    proof = run_capture_markdown_image_to_markdown_live_proof(
        vault_root=tmp_path,
        evidence_slug="2026-05-28-capture-markdown-image-to-markdown-live-proof-test",
        write_evidence=True,
    )

    panel = build_capture_to_markdown_panel(tmp_path)
    release_readiness = panel["release_readiness"]
    assert release_readiness["summary"]["image_to_markdown_live_proof_verified"] is True
    assert release_readiness["summary"]["image_to_markdown_live_proof_report"] == proof["evidence"]["json_path"]
    assert release_readiness["summary"]["image_to_markdown_live_proof_saved_markdown"] == (
        proof["verification"]["artifact_paths"]["saved_markdown"]
    )

    release_group = next(
        group for group in release_readiness["groups"] if group["id"] == "release_proof_open"
    )
    image_to_markdown = next(
        item for item in release_group["items"] if item["id"] == "live_image_to_markdown_save"
    )
    assert image_to_markdown["status"] == "verified"
    assert image_to_markdown["latest_report"] == proof["evidence"]["json_path"]
    assert image_to_markdown["saved_markdown"] == proof["verification"]["artifact_paths"]["saved_markdown"]
