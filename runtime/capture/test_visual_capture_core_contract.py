from __future__ import annotations

from pathlib import Path

import pytest

from runtime.capture.visual_capture import (
    CAPTURE_PROFILES,
    REQUIRED_PROFILE_IDS,
    SECRET_REDACTION_TOKEN,
    VisualCaptureValidationError,
    build_visual_capture_markdown,
    build_visual_capture_packet,
    preview_visual_capture,
)


def _sample_packet(**overrides):
    payload = {
        "title": "Acme Dashboard Notes",
        "profile": "research-note",
        "capture_method": "manual_paste",
        "raw_extracted_text": "Visible source text from a dashboard or page.",
        "user_intent": "Capture this for later reviewed research.",
        "structured_notes": "- Keep raw and notes separate.",
        "generated_interpretation": "This may be useful later, but it is not source truth.",
        "captured_at": "2026-05-20T12:34:56Z",
        "capture_id": "vcmi_20260520123456_test1234",
    }
    payload.update(overrides)
    return build_visual_capture_packet(**payload)


def test_required_mvp_profiles_are_registered() -> None:
    assert set(REQUIRED_PROFILE_IDS).issubset(set(CAPTURE_PROFILES))
    assert CAPTURE_PROFILES["raw_archive"].generated_interpretation_allowed is False
    assert CAPTURE_PROFILES["debug_error_capture"].default_input_class == "source"


def test_packet_defaults_to_preview_only_and_not_promoted() -> None:
    packet = _sample_packet()

    assert packet.schema_version == "vcmi.v0.1"
    assert packet.artifact_type == "visual_capture"
    assert packet.capture_profile == "research_note"
    assert packet.routing.status == "preview_only"
    assert packet.routing.review_status == "pending-review"
    assert packet.routing.canonical_status == "not_promoted"
    assert packet.routing.requires_review is True
    assert packet.authority.raw_ingestion_write is False
    assert packet.authority.canonical_mutation_allowed is False
    assert packet.authority.graph_index_mutation_allowed is False
    assert packet.authority.provider_call_allowed is False
    assert packet.authority.external_send_allowed is False
    assert packet.authority.silent_capture_allowed is False


def test_markdown_builder_has_required_frontmatter_and_sections() -> None:
    markdown = build_visual_capture_markdown(_sample_packet())

    assert markdown.startswith("---\n")
    assert "artifact_type: visual_capture" in markdown
    assert "schema_version: vcmi.v0.1" in markdown
    assert "canonical_status: not_promoted" in markdown
    assert "requires_review: true" in markdown
    for section in (
        "## Capture Summary",
        "## Source & Provenance",
        "## User Intent",
        "## Raw Extracted Content",
        "## Structured Notes",
        "## Generated Interpretation",
        "## Suggested Routing",
        "## Review Checklist",
        "## Attachments",
        "## Ingestion Metadata",
    ):
        assert section in markdown


def test_generated_interpretation_is_separate_from_raw_content() -> None:
    markdown = build_visual_capture_markdown(
        _sample_packet(
            raw_extracted_text="RAW SOURCE LINE",
            generated_interpretation="GENERATED ANALYSIS LINE",
        )
    )

    raw_index = markdown.index("## Raw Extracted Content")
    generated_index = markdown.index("## Generated Interpretation")

    assert raw_index < generated_index
    raw_section = markdown[raw_index:generated_index]
    generated_section = markdown[generated_index:]
    assert "RAW SOURCE LINE" in raw_section
    assert "GENERATED ANALYSIS LINE" not in raw_section
    assert "GENERATED ANALYSIS LINE" in generated_section
    assert "not source truth" in generated_section


def test_secret_like_text_is_redacted_and_blocks_save_by_default() -> None:
    raw_secret = "api_key=test-key-abcdefghijklmnopqrstuvwxyz123456"
    packet = _sample_packet(raw_extracted_text=f"Visible config {raw_secret}")
    markdown = build_visual_capture_markdown(packet)

    assert packet.quality.redaction_status == "blocked_secret_like"
    assert packet.quality.save_blocked_by_redaction is True
    assert packet.quality.redaction_count == 1
    assert SECRET_REDACTION_TOKEN in packet.content.raw_extracted_text
    assert raw_secret not in packet.content.raw_extracted_text
    assert raw_secret not in markdown
    assert SECRET_REDACTION_TOKEN in markdown


def test_explicit_redaction_mode_reports_redacted_and_allows_save_preview() -> None:
    packet = _sample_packet(
        raw_extracted_text="Bearer abcdefghijklmnopqrstuvwxyz123456",
        allow_secret_redaction=True,
    )

    assert packet.quality.redaction_status == "redacted"
    assert packet.quality.save_blocked_by_redaction is False
    assert SECRET_REDACTION_TOKEN in packet.content.raw_extracted_text


def test_preview_service_performs_no_writes(tmp_path: Path) -> None:
    result = preview_visual_capture(
        vault_root=tmp_path,
        title="Preview Only",
        profile="raw_archive",
        capture_method="manual_paste",
        raw_extracted_text="No files should be written by preview.",
        captured_at="2026-05-20T12:34:56Z",
        capture_id="vcmi_20260520123456_nowrite1",
    )

    assert result["ok"] is True
    assert result["status"] == "preview_only"
    assert result["write_performed"] is False
    assert result["authority"]["raw_ingestion_write"] is False
    assert list(tmp_path.iterdir()) == []


def test_invalid_profile_is_rejected() -> None:
    with pytest.raises(ValueError):
        _sample_packet(profile="write-directly-to-knowledge")


def test_empty_raw_content_is_rejected() -> None:
    with pytest.raises(VisualCaptureValidationError):
        _sample_packet(raw_extracted_text="  ")
