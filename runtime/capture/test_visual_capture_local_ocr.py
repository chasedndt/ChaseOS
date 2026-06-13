from __future__ import annotations

import hashlib
import json
import sys
import textwrap
from pathlib import Path
import zipfile

import pytest

from runtime.capture.visual_capture import (
    LocalOpticalCharacterRecognitionError,
    build_visual_capture_markdown,
    capture_from_screenshot_text,
    capture_from_photo_or_document_text,
    extract_text_from_image,
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


def _write_fake_local_text_engine(vault_root: Path, text: str) -> list[str]:
    script = vault_root / "runtime" / "capture" / "fake-local-text-engine.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "from __future__ import annotations\n"
        "import json\n"
        "import sys\n"
        "if len(sys.argv) < 2:\n"
        "    raise SystemExit(2)\n"
        f"print(json.loads({json.dumps(text)!r}))\n",
        encoding="utf-8",
    )
    return [sys.executable, str(script)]


def _write_fake_local_text_engine_script(vault_root: Path, name: str, body: str) -> list[str]:
    script = vault_root / "runtime" / "capture" / name
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    return [sys.executable, str(script)]


def test_local_optical_character_recognition_extracts_text_from_vault_image(tmp_path: Path) -> None:
    _write_png(tmp_path)
    command = _write_fake_local_text_engine(tmp_path, "Visible text extracted from image.")

    packet = capture_from_screenshot_text(
        file_path="07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        vault_root=tmp_path,
        title="Screenshot Text",
        local_ocr_command=command,
    )
    markdown = build_visual_capture_markdown(packet)

    assert packet.capture_method == "screenshot_local_text_extraction"
    assert packet.content.raw_extracted_text == "Visible text extracted from image."
    assert packet.quality.extraction_status == "text_extracted"
    assert packet.quality.confidence == "local_optical_character_recognition"
    assert "local_optical_character_recognition_performed" in packet.quality.extraction_warnings
    assert "cloud_optical_character_recognition_blocked" in packet.quality.extraction_warnings
    assert packet.authority.provider_call_allowed is False
    assert packet.provenance["transformation_chain"][1]["step"] == "screenshot_attachment_validate"
    assert packet.provenance["transformation_chain"][2]["step"] == "local_optical_character_recognition_extract"
    assert packet.provenance["transformation_chain"][2]["engine_id"] == "configured-command"
    assert "optical_character_recognition_status: text_extracted" in markdown
    assert "local_optical_character_recognition" in markdown
    assert "Visible text extracted from image." in markdown
    assert not (tmp_path / "03_INPUTS").exists()


def test_save_local_optical_character_recognition_capture_preserves_review_policy(tmp_path: Path) -> None:
    original = _write_png(tmp_path)
    command = _write_fake_local_text_engine(tmp_path, "Saved image text.")
    packet = capture_from_screenshot_text(
        file_path="07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        vault_root=tmp_path,
        title="Saved Screenshot Text",
        local_ocr_command=command,
    )

    result = save_visual_capture(vault_root=tmp_path, packet=packet)

    assert result["ok"] is True
    assert result["status"] == "raw_ingested"
    assert result["write_performed"] is True
    assert original.exists()
    sidecar = json.loads(Path(result["sidecar_path"]).read_text(encoding="utf-8"))
    packet_json = json.loads(Path(result["visual_capture_packet_path"]).read_text(encoding="utf-8"))
    vc_meta = sidecar["extra_metadata"]["visual_capture"]
    expected_attachment = f"03_INPUTS/00_QUARANTINE/Sources/_attachments/{packet.capture_id}/screenshot.png"
    copied = tmp_path / expected_attachment
    assert copied.exists()
    assert copied.read_bytes() == PNG_BYTES
    assert vc_meta["method"] == "screenshot_local_text_extraction"
    assert vc_meta["extraction_status"] == "text_extracted"
    assert vc_meta["local_optical_character_recognition"]["status"] == "text_extracted"
    assert vc_meta["local_optical_character_recognition"]["engine_id"] == "configured-command"
    assert vc_meta["attachment_review_policy"]["ocr_status"] == "text_extracted"
    assert result["attachment_review_policy"]["ocr_status"] == "text_extracted"
    assert packet_json["attachments"][0]["relative_path"] == expected_attachment
    assert packet_json["provenance"]["transformation_chain"][2]["step"] == "local_optical_character_recognition_extract"

    review_visual_capture_artifact(tmp_path, result["visual_capture_packet_path"], decision="reviewed")
    reviewed_sidecar = json.loads(Path(result["sidecar_path"]).read_text(encoding="utf-8"))
    reviewed_policy = reviewed_sidecar["extra_metadata"]["visual_capture"]["attachment_review_policy"]
    assert reviewed_policy["review_status"] == "reviewed"
    assert reviewed_policy["ocr_status"] == "text_extracted"
    assert reviewed_policy["runtime_delete_allowed"] is False


def test_local_optical_character_recognition_missing_engine_blocks_before_writes(tmp_path: Path) -> None:
    _write_png(tmp_path)

    with pytest.raises(LocalOpticalCharacterRecognitionError, match="not found"):
        extract_text_from_image(
            "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            vault_root=tmp_path,
            command=["missing-local-text-engine"],
        )

    assert not (tmp_path / "03_INPUTS").exists()


def test_local_optical_character_recognition_empty_output_blocks_before_writes(tmp_path: Path) -> None:
    _write_png(tmp_path)
    command = _write_fake_local_text_engine(tmp_path, "")

    with pytest.raises(LocalOpticalCharacterRecognitionError, match="returned no text"):
        extract_text_from_image(
            "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            vault_root=tmp_path,
            command=command,
        )

    assert not (tmp_path / "03_INPUTS").exists()


def test_local_optical_character_recognition_command_failure_blocks_before_writes(tmp_path: Path) -> None:
    _write_png(tmp_path)
    command = _write_fake_local_text_engine_script(
        tmp_path,
        "fake-local-text-engine-failure.py",
        """
        from __future__ import annotations
        import sys
        sys.stderr.write("unit command failure")
        raise SystemExit(7)
        """,
    )

    with pytest.raises(LocalOpticalCharacterRecognitionError, match="command failed: unit command failure"):
        extract_text_from_image(
            "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            vault_root=tmp_path,
            command=command,
        )

    assert not (tmp_path / "03_INPUTS").exists()


def test_local_optical_character_recognition_timeout_blocks_before_writes(tmp_path: Path) -> None:
    _write_png(tmp_path)
    command = _write_fake_local_text_engine_script(
        tmp_path,
        "fake-local-text-engine-timeout.py",
        """
        from __future__ import annotations
        import time
        time.sleep(5)
        print("late text")
        """,
    )

    with pytest.raises(LocalOpticalCharacterRecognitionError, match="timed out"):
        extract_text_from_image(
            "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            vault_root=tmp_path,
            command=command,
            timeout_seconds=1,
        )

    assert not (tmp_path / "03_INPUTS").exists()


def test_secret_like_local_optical_character_recognition_text_blocks_save(tmp_path: Path) -> None:
    _write_png(tmp_path)
    raw_secret = "api_key=test-key-abcdefghijklmnopqrstuvwxyz123456"
    command = _write_fake_local_text_engine(tmp_path, f"Visible config {raw_secret}")
    packet = capture_from_screenshot_text(
        file_path="07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        vault_root=tmp_path,
        title="Secret Image Text",
        local_ocr_command=command,
    )

    result = save_visual_capture(vault_root=tmp_path, packet=packet)

    assert result["ok"] is False
    assert result["status"] == "blocked_secret_like"
    assert result["write_performed"] is False
    assert result["blockers"] == ["secret_or_credential_indicator_present"]
    assert packet.quality.save_blocked_by_redaction is True
    assert raw_secret not in result["markdown"]
    assert not (tmp_path / "03_INPUTS" / "00_QUARANTINE").exists()
    assert packet.content.raw_content_sha256 == hashlib.sha256(
        packet.content.raw_extracted_text.encode("utf-8")
    ).hexdigest()


def test_photo_document_text_extraction_reads_docx_without_cloud_or_writes(tmp_path: Path) -> None:
    docx = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Photo-Documents" / "proof.docx"
    docx.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
                "<w:body><w:p><w:r><w:t>Arbitrary document text proof.</w:t></w:r></w:p></w:body>"
                "</w:document>"
            ),
        )

    packet = capture_from_photo_or_document_text(
        file_path=docx,
        vault_root=tmp_path,
        title="Word Document Text",
    )
    markdown = build_visual_capture_markdown(packet)

    assert packet.capture_method == "photo_document_text_extraction"
    assert packet.content.raw_extracted_text == "Arbitrary document text proof."
    assert packet.quality.extraction_status == "text_extracted"
    assert packet.quality.confidence == "local_document_text_extraction"
    assert "local_document_text_extraction_performed" in packet.quality.extraction_warnings
    assert "cloud_optical_character_recognition_blocked" in packet.quality.extraction_warnings
    assert packet.provenance["transformation_chain"][1]["method"] == "local_docx_xml_parser"
    assert "Arbitrary document text proof." in markdown
    assert not (tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources").exists()


def test_photo_document_text_extraction_accepts_quarantine_photo_image(tmp_path: Path) -> None:
    image = _write_png(
        tmp_path,
        "03_INPUTS/00_QUARANTINE/Photo-Documents/proof.png",
    )
    command = _write_fake_local_text_engine(tmp_path, "Visible text from explicit photo.")

    packet = capture_from_photo_or_document_text(
        file_path=image,
        vault_root=tmp_path,
        title="Photo Image Text",
        local_ocr_command=command,
    )

    assert packet.capture_method == "photo_document_image_text_extraction"
    assert packet.content.raw_extracted_text == "Visible text from explicit photo."
    steps = [step.get("step") for step in packet.provenance["transformation_chain"]]
    assert "photo_document_source_route" in steps
    assert packet.authority.provider_call_allowed is False
    assert not (tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources").exists()


def test_photo_document_text_extraction_reads_pdf_embedded_text_without_cloud_or_writes(tmp_path: Path) -> None:
    pdf = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Photo-Documents" / "proof.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Page /Contents 2 0 R >> endobj\n"
        b"2 0 obj << /Length 68 >> stream\n"
        b"BT /F1 12 Tf 72 720 Td (Embedded PDF text proof.) Tj ET\n"
        b"endstream endobj\n"
        b"%%EOF\n"
    )

    packet = capture_from_photo_or_document_text(
        file_path="03_INPUTS/00_QUARANTINE/Photo-Documents/proof.pdf",
        vault_root=tmp_path,
        title="PDF Document Text",
    )

    assert packet.capture_method == "photo_document_text_extraction"
    assert "Embedded PDF text proof." in packet.content.raw_extracted_text
    assert packet.quality.extraction_status == "text_extracted"
    assert packet.provenance["transformation_chain"][1]["method"] == "local_pdf_embedded_text_parser"
    assert packet.authority.provider_call_allowed is False
    assert not (tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources").exists()
