from __future__ import annotations

import json
from pathlib import Path

from runtime.capture.visual_capture import (
    SECRET_REDACTION_TOKEN,
    capture_from_saved_html,
    capture_from_text,
    capture_from_text_file,
    save_visual_capture,
)


def _make_vault(tmp_path: Path) -> Path:
    (tmp_path / "03_INPUTS").mkdir()
    return tmp_path


def test_save_visual_capture_writes_quarantine_markdown_sidecar_and_packet_json(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    result = save_visual_capture(
        vault_root=vault,
        title="Dashboard Research Capture",
        profile="research_note",
        capture_method="manual_paste",
        raw_extracted_text="Visible source text for later review.",
        user_intent="Keep this as raw intake.",
        captured_at="2026-05-20T12:34:56Z",
        capture_id="vcmi_20260520123456_save0001",
    )

    content_path = Path(result["content_path"])
    sidecar_path = Path(result["sidecar_path"])
    packet_path = Path(result["visual_capture_packet_path"])
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    markdown = content_path.read_text(encoding="utf-8")

    assert result["ok"] is True
    assert result["status"] == "raw_ingested"
    assert result["write_performed"] is True
    assert result["is_duplicate"] is False
    assert content_path.exists()
    assert sidecar_path.exists()
    assert packet_path.exists()
    assert "03_INPUTS" in result["content_path"]
    assert "00_QUARANTINE" in result["content_path"]
    assert "Sources" in result["content_path"]
    assert "status: raw_ingested" in markdown
    assert "raw_ingestion_path:" in markdown
    assert "canonical_status: not_promoted" in markdown
    assert sidecar["promotion_status"] == "quarantine"
    assert sidecar["quarantine_status"] == "pending-review"
    assert sidecar["source_package_status"] == "not-ingested"
    assert sidecar["extra_metadata"]["visual_capture"]["schema_version"] == "vcmi.v0.1"
    assert sidecar["extra_metadata"]["visual_capture"]["capture_id"] == "vcmi_20260520123456_save0001"
    assert sidecar["extra_metadata"]["visual_capture"]["canonical_status"] == "not_promoted"
    assert sidecar["extra_metadata"]["visual_capture"]["requires_review"] is True
    assert packet["routing"]["status"] == "raw_ingested"
    assert packet["routing"]["canonical_status"] == "not_promoted"
    assert packet["authority"]["raw_ingestion_write"] is True
    assert packet["authority"]["canonical_mutation_allowed"] is False
    assert packet["authority"]["provider_call_allowed"] is False
    assert packet["authority"]["external_send_allowed"] is False


def test_save_visual_capture_preserves_no_downstream_canonical_writes(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    save_visual_capture(
        vault_root=vault,
        title="No Canonical Writes",
        profile="raw_archive",
        capture_method="manual_paste",
        raw_extracted_text="This should land only in raw quarantine.",
        captured_at="2026-05-20T12:34:56Z",
        capture_id="vcmi_20260520123456_nocanon",
    )

    assert (vault / "03_INPUTS" / "00_QUARANTINE").exists()
    assert not (vault / "02_KNOWLEDGE").exists()
    assert not (vault / "runtime" / "source_intelligence").exists()
    assert not (vault / "07_LOGS" / "Workflow-Proofs").exists()


def test_save_visual_capture_blocks_secret_like_text_without_writes(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    raw_secret = "api_key=test-key-abcdefghijklmnopqrstuvwxyz123456"
    result = save_visual_capture(
        vault_root=vault,
        title="Secret Bearing Capture",
        profile="research_note",
        capture_method="manual_paste",
        raw_extracted_text=f"Visible config {raw_secret}",
        captured_at="2026-05-20T12:34:56Z",
        capture_id="vcmi_20260520123456_secret1",
    )

    assert result["ok"] is False
    assert result["status"] == "blocked_secret_like"
    assert result["write_performed"] is False
    assert result["blockers"] == ["secret_or_credential_indicator_present"]
    assert raw_secret not in result["markdown"]
    assert SECRET_REDACTION_TOKEN in result["markdown"]
    assert not (vault / "03_INPUTS" / "00_QUARANTINE").exists()
    assert not (vault / ".chaseos").exists()


def test_save_visual_capture_allows_explicit_redacted_save(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    raw_secret = "Bearer abcdefghijklmnopqrstuvwxyz123456"
    result = save_visual_capture(
        vault_root=vault,
        title="Redacted Save",
        profile="research_note",
        capture_method="manual_paste",
        raw_extracted_text=f"Header: {raw_secret}",
        allow_secret_redaction=True,
        captured_at="2026-05-20T12:34:56Z",
        capture_id="vcmi_20260520123456_redact1",
    )

    content = Path(result["content_path"]).read_text(encoding="utf-8")
    sidecar = json.loads(Path(result["sidecar_path"]).read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["write_performed"] is True
    assert raw_secret not in content
    assert SECRET_REDACTION_TOKEN in content
    assert sidecar["extra_metadata"]["visual_capture"]["redaction_status"] == "redacted"
    assert sidecar["extra_metadata"]["visual_capture"]["redaction_count"] == 1


def test_save_visual_capture_dedup_returns_no_second_packet_json(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    kwargs = {
        "vault_root": vault,
        "title": "Duplicate Capture",
        "profile": "research_note",
        "capture_method": "manual_paste",
        "raw_extracted_text": "Same visual capture body.",
        "captured_at": "2026-05-20T12:34:56Z",
        "capture_id": "vcmi_20260520123456_dupe001",
    }
    first = save_visual_capture(**kwargs)
    second = save_visual_capture(**kwargs)

    assert first["write_performed"] is True
    assert second["status"] == "duplicate"
    assert second["write_performed"] is False
    assert second["is_duplicate"] is True
    assert second["capture_result"]["duplicate_of"] == first["phase8_capture_id"]
    assert len(list((vault / "03_INPUTS" / "00_QUARANTINE").rglob("*.md"))) == 1
    assert len(list((vault / "03_INPUTS" / "00_QUARANTINE").rglob("*.visual_capture.json"))) == 1


def test_text_and_file_extractors_build_packets_without_writes(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    source = vault / "source.md"
    source.write_text("# Local Source\n\nBody text.", encoding="utf-8")

    text_packet = capture_from_text(text="Pasted source text", title="Pasted Capture")
    file_packet = capture_from_text_file(file_path=source)

    assert text_packet.routing.status == "preview_only"
    assert text_packet.content.raw_extracted_text == "Pasted source text"
    assert file_packet.source.source_app == "local-file"
    assert "Body text." in file_packet.content.raw_extracted_text
    assert not (vault / "03_INPUTS" / "00_QUARANTINE").exists()


def test_saved_html_extractor_uses_browser_connector_without_writing(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    html = vault / "article.html"
    html.write_text(
        "<html><head><title>Example Article</title></head>"
        "<body><nav>Skip</nav><h1>Article Heading</h1><p>Useful paragraph.</p></body></html>",
        encoding="utf-8",
    )

    packet = capture_from_saved_html(
        file_path=html,
        source_url="https://example.com/article",
        captured_at="2026-05-20T12:34:56Z",
        capture_id="vcmi_20260520123456_html001",
    )

    assert packet.routing.status == "preview_only"
    assert packet.source.source_app == "browser-saved-html"
    assert packet.source.source_url == "https://example.com/article"
    assert "Useful paragraph." in packet.content.raw_extracted_text
    assert "Skip" not in packet.content.raw_extracted_text
    assert not (vault / "03_INPUTS" / "00_QUARANTINE").exists()
