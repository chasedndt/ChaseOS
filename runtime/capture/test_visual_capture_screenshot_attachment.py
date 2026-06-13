from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runtime.capture.visual_capture import (
    build_screenshot_attachment,
    build_visual_capture_markdown,
    capture_from_screenshot_attachment,
    review_visual_capture_artifact,
    save_visual_capture,
)


PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15"
    "c4890000000d49444154789c6360000002000100ffff03000006000557bfab"
    "d40000000049454e44ae426082"
)


def _write_png(vault_root: Path, relative_path: str = "07_LOGS/Operator-Screenshots/local/default/screenshot.png") -> Path:
    target = vault_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PNG_BYTES)
    return target


def test_build_screenshot_attachment_validates_vault_local_image(tmp_path: Path) -> None:
    image = _write_png(tmp_path)

    result = build_screenshot_attachment("07_LOGS/Operator-Screenshots/local/default/screenshot.png", vault_root=tmp_path)

    assert Path(result.absolute_path) == image.resolve()
    assert result.attachment.filename == "screenshot.png"
    assert result.attachment.relative_path == "07_LOGS/Operator-Screenshots/local/default/screenshot.png"
    assert result.attachment.mime_type == "image/png"
    assert result.attachment.size_bytes == len(PNG_BYTES)
    assert result.attachment.sha256 == hashlib.sha256(PNG_BYTES).hexdigest()
    assert result.attachment.redaction_status == "operator-review-required"
    assert "ocr_not_performed" in result.warnings
    assert "no_cloud_ocr" in result.warnings
    assert result.metadata["ocr_status"] == "not_performed"
    assert result.metadata["cloud_ocr_allowed"] is False
    assert result.metadata["retention_status"] == "retain_until_operator_review"
    assert result.metadata["review_status"] == "pending-review"
    assert result.metadata["operator_review_required"] is True
    assert result.metadata["runtime_delete_allowed"] is False


def test_capture_from_screenshot_attachment_builds_attachment_only_packet(tmp_path: Path) -> None:
    _write_png(tmp_path)

    packet = capture_from_screenshot_attachment(
        file_path="07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        vault_root=tmp_path,
        title="Screenshot Evidence",
        source_url="https://example.test/evidence",
    )
    markdown = build_visual_capture_markdown(packet)

    assert packet.capture_method == "screenshot_attachment_import"
    assert packet.routing.status == "preview_only"
    assert packet.authority.raw_ingestion_write is False
    assert packet.authority.provider_call_allowed is False
    assert packet.quality.extraction_status == "attachment_only"
    assert packet.quality.confidence == "screenshot_attachment_no_ocr"
    assert "ocr_not_performed" in packet.quality.extraction_warnings
    assert "no_cloud_ocr" in packet.quality.extraction_warnings
    assert packet.attachments[0].mime_type == "image/png"
    assert packet.attachments[0].relative_path == "07_LOGS/Operator-Screenshots/local/default/screenshot.png"
    assert packet.provenance["transformation_chain"][1]["step"] == "screenshot_attachment_validate"
    assert packet.provenance["transformation_chain"][1]["ocr_status"] == "not_performed"
    assert "screenshots:" in markdown
    assert "- 07_LOGS/Operator-Screenshots/local/default/screenshot.png" in markdown
    assert "Optical character recognition text is not available in this pass." in markdown
    assert not (tmp_path / "03_INPUTS").exists()


def test_save_screenshot_attachment_copies_attachment_into_raw_quarantine(tmp_path: Path) -> None:
    original = _write_png(tmp_path)
    packet = capture_from_screenshot_attachment(
        file_path="07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        vault_root=tmp_path,
        title="Screenshot Save",
    )

    result = save_visual_capture(vault_root=tmp_path, packet=packet)

    assert result["ok"] is True
    assert result["status"] == "raw_ingested"
    assert result["write_performed"] is True
    assert Path(result["content_path"]).resolve().is_relative_to(
        (tmp_path / "03_INPUTS" / "00_QUARANTINE").resolve()
    )
    assert not Path(result["content_path"]).resolve().is_relative_to((tmp_path / "02_KNOWLEDGE").resolve())
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    markdown = Path(result["content_path"]).read_text(encoding="utf-8")
    sidecar = json.loads(Path(result["sidecar_path"]).read_text(encoding="utf-8"))
    packet_json = json.loads(Path(result["visual_capture_packet_path"]).read_text(encoding="utf-8"))
    vc_meta = sidecar["extra_metadata"]["visual_capture"]
    expected_attachment = f"03_INPUTS/00_QUARANTINE/Sources/_attachments/{packet.capture_id}/screenshot.png"
    copied = tmp_path / expected_attachment
    assert original.exists()
    assert copied.exists()
    assert copied.read_bytes() == PNG_BYTES
    assert vc_meta["method"] == "screenshot_attachment_import"
    assert vc_meta["extraction_status"] == "attachment_only"
    assert "no_cloud_ocr" in vc_meta["extraction_warnings"]
    assert "screenshot_attachment_copied_to_quarantine" in vc_meta["extraction_warnings"]
    assert "screenshot_attachment_retention_review_required" in vc_meta["extraction_warnings"]
    assert vc_meta["attachments"][0]["relative_path"] == expected_attachment
    assert vc_meta["attachments"][0]["sha256"] == hashlib.sha256(PNG_BYTES).hexdigest()
    policy = vc_meta["attachment_review_policy"]
    assert policy["policy_id"] == "vcmi.screenshot_attachment.retention.v1"
    assert policy["storage_status"] == "copied_to_quarantine"
    assert policy["retention_status"] == "retain_until_operator_review"
    assert policy["review_status"] == "pending-review"
    assert policy["operator_review_required"] is True
    assert policy["cleanup_requires_operator_decision"] is True
    assert policy["runtime_delete_allowed"] is False
    assert policy["delete_allowed_by_runtime"] is False
    assert policy["ocr_status"] == "not_performed"
    assert policy["cloud_ocr_allowed"] is False
    assert result["attachment_review_policy"] == policy
    disposition = vc_meta["attachment_disposition_policy"]
    assert disposition["policy_id"] == "vcmi.attachment_disposition.v1"
    assert disposition["status"] == "metadata_policy_only"
    assert disposition["default_disposition"] == "retain-until-downstream-review"
    assert disposition["runtime_delete_allowed"] is False
    assert disposition["studio_delete_controls_allowed"] is True
    assert disposition["cleanup_executor_available"] is True
    assert disposition["attachments"][0]["relative_path"] == expected_attachment
    assert result["attachment_disposition_policy"] == disposition
    assert packet_json["attachments"][0]["relative_path"] == expected_attachment
    assert packet_json["provenance"]["transformation_chain"][-2]["step"] == "screenshot_attachment_quarantine_copy"
    assert packet_json["provenance"]["transformation_chain"][-1]["step"] == "screenshot_attachment_retention_review_policy"
    assert packet_json["provenance"]["transformation_chain"][-1]["runtime_delete_allowed"] is False
    assert expected_attachment in markdown
    assert "retain_until_operator_review" in markdown
    assert "Declared source: `07_LOGS/Operator-Screenshots/local/default/screenshot.png`" in markdown
    assert vc_meta["authority"]["canonical_mutation_allowed"] is False
    assert vc_meta["authority"]["provider_call_allowed"] is False

    review_visual_capture_artifact(tmp_path, result["visual_capture_packet_path"], decision="reviewed")
    reviewed_sidecar = json.loads(Path(result["sidecar_path"]).read_text(encoding="utf-8"))
    reviewed_disposition = reviewed_sidecar["extra_metadata"]["visual_capture"]["attachment_disposition_policy"]
    assert reviewed_disposition["default_disposition"] == "retain"
    assert reviewed_disposition["review_status"] == "reviewed"
    assert reviewed_disposition["runtime_delete_allowed"] is False


def test_save_screenshot_attachment_missing_source_blocks_before_writes(tmp_path: Path) -> None:
    image = _write_png(tmp_path)
    packet = capture_from_screenshot_attachment(
        file_path="07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        vault_root=tmp_path,
        title="Screenshot Missing Source",
    )
    image.unlink()

    with pytest.raises(FileNotFoundError):
        save_visual_capture(vault_root=tmp_path, packet=packet)

    assert not (tmp_path / "03_INPUTS" / "00_QUARANTINE").exists()


def test_duplicate_screenshot_attachment_save_does_not_copy_second_attachment(tmp_path: Path) -> None:
    _write_png(tmp_path)
    packet = capture_from_screenshot_attachment(
        file_path="07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        vault_root=tmp_path,
        title="Screenshot Duplicate",
    )

    first = save_visual_capture(vault_root=tmp_path, packet=packet)
    second = save_visual_capture(vault_root=tmp_path, packet=packet)

    assert first["write_performed"] is True
    assert second["status"] == "duplicate"
    assert second["write_performed"] is False
    copied = list((tmp_path / "03_INPUTS" / "00_QUARANTINE").rglob("screenshot.png"))
    assert len(copied) == 1


def test_screenshot_attachment_rejects_path_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.png"
    outside.write_bytes(PNG_BYTES)

    with pytest.raises(ValueError):
        build_screenshot_attachment(outside, vault_root=tmp_path)


def test_screenshot_attachment_rejects_unallowed_vault_directory(tmp_path: Path) -> None:
    image = tmp_path / "captures" / "screenshot.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(PNG_BYTES)

    with pytest.raises(ValueError):
        build_screenshot_attachment("captures/screenshot.png", vault_root=tmp_path)


def test_screenshot_attachment_rejects_unsupported_extension_or_signature(tmp_path: Path) -> None:
    image = tmp_path / "07_LOGS" / "Operator-Screenshots" / "local" / "default" / "not-image.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"not an image file but long enough for minimum bytes")

    with pytest.raises(ValueError, match="signature"):
        build_screenshot_attachment(image, vault_root=tmp_path)


def test_screenshot_attachment_rejects_blank_or_tiny_file(tmp_path: Path) -> None:
    blank = tmp_path / "07_LOGS" / "Operator-Screenshots" / "local" / "default" / "blank.png"
    blank.parent.mkdir(parents=True)
    blank.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError):
        build_screenshot_attachment(blank, vault_root=tmp_path)

    tiny = tmp_path / "07_LOGS" / "Operator-Screenshots" / "local" / "default" / "tiny.png"
    tiny.write_bytes(PNG_BYTES[:16])

    with pytest.raises(ValueError):
        build_screenshot_attachment(tiny, vault_root=tmp_path)


def test_screenshot_attachment_rejects_secret_or_browser_storage_path_marker(tmp_path: Path) -> None:
    image = tmp_path / "07_LOGS" / "Operator-Screenshots" / "secrets" / "screenshot.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(PNG_BYTES)

    with pytest.raises(ValueError, match="secrets|credentials|browser history"):
        build_screenshot_attachment(image, vault_root=tmp_path)
