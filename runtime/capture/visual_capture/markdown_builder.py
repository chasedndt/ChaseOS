"""Markdown artifact builder for Capture to Markdown previews."""

from __future__ import annotations

import json
import re
from typing import Any

from runtime.capture.router import INPUT_CLASS_TO_SUBFOLDER

from .attachment_disposition import build_attachment_disposition_policy
from .attachments import build_screenshot_attachment_review_policy
from .models import VisualCapturePacket, validate_visual_capture_packet
from .profiles import CAPTURE_PROFILES


_SAFE_YAML_PLAIN = re.compile(r"^[A-Za-z0-9_.:/+-]+$")


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text and _SAFE_YAML_PLAIN.match(text) and text.lower() not in {"true", "false", "null"}:
        return text
    return json.dumps(text)


def _yaml_lines(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"{key}: []")
                continue
            lines.append(f"{key}:")
            lines.extend(f"  - {_yaml_scalar(item)}" for item in value)
            continue
        lines.append(f"{key}: {_yaml_scalar(value)}")
    return lines


def _clean_heading(value: str) -> str:
    return " ".join(str(value or "").replace("#", "").split()) or "Untitled Capture"


def _fallback(value: str, fallback: str = "(none provided)") -> str:
    return str(value or "").strip() or fallback


def _fenced_block(value: str, language: str = "text") -> str:
    text = str(value or "")
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{language}\n{text}\n{fence}"


def _frontmatter(packet: VisualCapturePacket) -> str:
    profile = CAPTURE_PROFILES[packet.capture_profile]
    attachments = [item.relative_path or item.filename for item in packet.attachments]
    screenshots = [
        item.relative_path or item.filename
        for item in packet.attachments
        if item.mime_type.lower().startswith("image/")
    ]
    local_ocr = _local_ocr_metadata(packet)
    tags = list(dict.fromkeys(["visual-capture", "raw-ingestion", *profile.suggested_tags]))
    data = {
        "artifact_type": packet.artifact_type,
        "schema_version": packet.schema_version,
        "capture_id": packet.capture_id,
        "profile": packet.capture_profile,
        "method": packet.capture_method,
        "source_app": packet.source.source_app,
        "source_window_title": packet.source.source_window_title,
        "source_page_title": packet.source.source_page_title,
        "source_url": packet.source.source_url,
        "captured_at": packet.captured_at,
        "captured_by": packet.captured_by,
        "timezone": packet.timezone,
        "raw_ingestion_path": packet.routing.raw_ingestion_path,
        "status": packet.routing.status,
        "review_status": packet.routing.review_status,
        "canonical_status": packet.routing.canonical_status,
        "requires_review": packet.routing.requires_review,
        "confidence": packet.quality.confidence,
        "optical_character_recognition_status": local_ocr.get("status") or "not_performed",
        "optical_character_recognition_engine": local_ocr.get("engine_id") or "",
        "redaction_status": packet.quality.redaction_status,
        "redaction_count": packet.quality.redaction_count,
        "injection_scan": packet.quality.injection_scan,
        "screenshots": screenshots,
        "attachments": attachments,
        "tags": tags,
    }
    return "\n".join(["---", *_yaml_lines(data), "---"])


def _metadata_json(packet: VisualCapturePacket) -> str:
    local_ocr = _local_ocr_metadata(packet)
    metadata = {
        "schema_version": packet.schema_version,
        "artifact_type": packet.artifact_type,
        "capture_id": packet.capture_id,
        "capture_profile": packet.capture_profile,
        "capture_method": packet.capture_method,
        "content": {
            "raw_content_sha256": packet.content.raw_content_sha256,
            "raw_content_char_count": packet.content.raw_content_char_count,
            "raw_content_truncated": packet.content.raw_content_truncated,
        },
        "quality": packet.quality.to_dict(),
        "routing": packet.routing.to_dict(),
        "authority": packet.authority.to_dict(),
        "attachment_review_policy": build_screenshot_attachment_review_policy(
            packet.attachments,
            review_status=packet.routing.review_status,
            ocr_status=local_ocr.get("status") or "not_performed",
            cloud_ocr_allowed=False,
        ),
        "attachment_disposition_policy": build_attachment_disposition_policy(
            packet.attachments,
            review_status=packet.routing.review_status,
        ),
        "local_optical_character_recognition": local_ocr,
    }
    return json.dumps(metadata, indent=2, sort_keys=True)


def _local_ocr_metadata(packet: VisualCapturePacket) -> dict[str, Any]:
    chain = packet.provenance.get("transformation_chain", [])
    for step in reversed(chain if isinstance(chain, list) else []):
        if not isinstance(step, dict):
            continue
        if step.get("step") == "local_optical_character_recognition_extract":
            return {
                "status": step.get("status") or "text_extracted",
                "engine_id": step.get("engine_id") or "unknown",
                "engine_protocol": step.get("engine_protocol") or "unknown",
                "extracted_text_sha256": step.get("extracted_text_sha256") or "",
                "extracted_text_char_count": step.get("extracted_text_char_count") or 0,
                "cloud_optical_character_recognition_allowed": bool(
                    step.get("cloud_optical_character_recognition_allowed")
                ),
                "provider_call_allowed": bool(step.get("provider_call_allowed")),
                "secret_scan_required_after_extraction": bool(
                    step.get("secret_scan_required_after_extraction")
                ),
            }
    return {
        "status": "not_performed",
        "engine_id": "",
        "engine_protocol": "",
        "extracted_text_sha256": "",
        "extracted_text_char_count": 0,
        "cloud_optical_character_recognition_allowed": False,
        "provider_call_allowed": False,
        "secret_scan_required_after_extraction": False,
    }


def _provenance_lines(packet: VisualCapturePacket) -> list[str]:
    chain = packet.provenance.get("transformation_chain", [])
    lines = [
        f"- Source app: `{_fallback(packet.source.source_app, 'unknown')}`",
        f"- Declared source: `{_fallback(packet.source.declared_source, 'unknown')}`",
        f"- Source platform: `{_fallback(packet.source.source_platform, 'visual-capture')}`",
        f"- Input class: `{packet.source.input_class}`",
        f"- Source URL: {_fallback(packet.source.source_url)}",
        f"- Window title: {_fallback(packet.source.source_window_title)}",
        f"- Page title: {_fallback(packet.source.source_page_title)}",
        "- Transformation chain:",
    ]
    if not chain:
        lines.append("  - (none recorded)")
        return lines
    for step in chain:
        name = step.get("step", "unknown_step")
        method = step.get("method", "unknown_method")
        at = step.get("at", "")
        status = step.get("status")
        suffix = f" ({status})" if status else ""
        lines.append(f"  - `{name}` via `{method}` at `{at}`{suffix}")
    return lines


def build_visual_capture_markdown(packet: VisualCapturePacket) -> str:
    """Build the preview Markdown artifact for a visual capture packet."""

    validate_visual_capture_packet(packet, require_no_write=False)
    profile = CAPTURE_PROFILES[packet.capture_profile]
    quarantine_folder = INPUT_CLASS_TO_SUBFOLDER.get(packet.source.input_class, "unknown")

    sections = [
        _frontmatter(packet),
        "",
        f"# Capture to Markdown - {_clean_heading(packet.title)}",
        "",
        "## Capture Summary",
        "",
        f"- Profile: `{profile.label}`",
        f"- Method: `{packet.capture_method}`",
        f"- Confidence: `{packet.quality.confidence}`",
        f"- Extraction status: `{packet.quality.extraction_status}`",
        f"- Redaction status: `{packet.quality.redaction_status}`",
        f"- Review required: `{str(packet.routing.requires_review).lower()}`",
        f"- Canonical status: `{packet.routing.canonical_status}`",
        "",
        "## Source & Provenance",
        "",
        "\n".join(_provenance_lines(packet)),
        "",
        "## User Intent",
        "",
        _fallback(packet.content.user_intent),
        "",
        "## Raw Extracted Content",
        "",
        _fenced_block(packet.content.raw_extracted_text, "text"),
        "",
        "## Structured Notes",
        "",
        _fallback(packet.content.structured_notes),
        "",
        "## Generated Interpretation",
        "",
        "Generated interpretation is analysis only, not source truth.",
        "",
        _fallback(packet.content.generated_interpretation),
        "",
        "## Suggested Routing",
        "",
        f"- Suggested raw intake class: `{packet.source.input_class}`",
        f"- Suggested quarantine folder: `03_INPUTS/00_QUARANTINE/{quarantine_folder}/`",
        f"- Routing status: `{packet.routing.status}`",
        f"- Source package status: `{packet.routing.source_package_status}`",
        f"- Agent Orchestration Runtime queue status: `{packet.routing.aor_queue_status}`",
        "- Suggested routing is a hint only; canonical promotion still requires later Gate review.",
        "",
        "## Review Checklist",
        "",
        "- [ ] Prompt-injection indicators reviewed.",
        "- [ ] Source identity and provenance verified.",
        "- [ ] Secret/redaction status reviewed.",
        "- [ ] Raw content compared against source before promotion.",
        "- [ ] Canonical promotion denied unless a later Gate-reviewed pass approves it.",
        "",
        "## Attachments",
        "",
    ]

    if packet.attachments:
        sections.extend(f"- `{item.relative_path or item.filename}` ({item.mime_type})" for item in packet.attachments)
    else:
        sections.append("(none)")

    sections.extend(
        [
            "",
            "## Ingestion Metadata",
            "",
            _fenced_block(_metadata_json(packet), "json"),
            "",
        ]
    )
    return "\n".join(sections)
