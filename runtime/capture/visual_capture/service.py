"""Preview and save services for Capture to Markdown."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.capture.capture import capture_content
from runtime.capture.content_packet import ContentPacket
from runtime.capture.dedup_registry import (
    build_registry_entry,
    get_entry,
    is_duplicate,
    load_registry,
    register_capture,
    save_registry,
)
from runtime.capture.router import make_filename, resolve_unique_path, route_input_class

from .attachment_disposition import build_attachment_disposition_policy
from .attachments import build_screenshot_attachment_review_policy
from .markdown_builder import build_visual_capture_markdown
from .models import (
    VisualCaptureAttachment,
    VisualCaptureAuthority,
    VisualCapturePacket,
    VisualCaptureRouting,
    build_visual_capture_packet,
    utc_now,
)
from .profiles import CAPTURE_PROFILES


def preview_visual_capture(
    *,
    vault_root: str | Path | None = None,
    packet: VisualCapturePacket | None = None,
    **packet_kwargs: Any,
) -> dict[str, Any]:
    """Build a no-write visual capture preview.

    ``vault_root`` is accepted for future API symmetry but is not read from or
    written to in Pass 1.
    """

    preview_packet = packet or build_visual_capture_packet(**packet_kwargs)
    markdown = build_visual_capture_markdown(preview_packet)
    blockers: list[str] = []
    if preview_packet.quality.save_blocked_by_redaction:
        blockers.append("secret_or_credential_indicator_present")

    return {
        "ok": True,
        "surface": "capture-to-markdown",
        "status": "preview_only",
        "preview_ready": True,
        "save_allowed": not blockers,
        "write_performed": False,
        "vault_root": str(Path(vault_root)) if vault_root is not None else "",
        "blockers": blockers,
        "packet": preview_packet.to_dict(),
        "markdown": markdown,
        "authority": preview_packet.authority.to_dict(),
    }


def _vault_relative(path: Path, vault_root: Path) -> str:
    try:
        return path.resolve().relative_to(vault_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _predicted_paths(packet: VisualCapturePacket, vault_root: Path) -> tuple[Path, Path, Path]:
    target_dir = route_input_class(packet.source.input_class, vault_root)
    filename = make_filename(
        input_class=packet.source.input_class,
        source_platform="visual-capture",
        title=packet.title,
        captured_at=packet.captured_at,
    )
    content_path = resolve_unique_path(target_dir, filename)
    return (
        content_path,
        content_path.with_suffix(".meta.json"),
        content_path.with_suffix(".visual_capture.json"),
    )


def _saved_packet(
    packet: VisualCapturePacket,
    *,
    vault_root: Path,
    content_path: Path,
    sidecar_path: Path,
    packet_path: Path,
) -> VisualCapturePacket:
    save_at = utc_now()
    chain = list(packet.provenance.get("transformation_chain", []))
    chain.append(
        {
            "step": "quarantine_write",
            "method": "phase8_capture_content",
            "at": save_at,
        }
    )
    chain.append(
        {
            "step": "visual_capture_packet_json_write",
            "method": "vcmi_adjacent_packet_json",
            "at": save_at,
        }
    )
    return replace(
        packet,
        routing=VisualCaptureRouting(
            raw_ingestion_path=_vault_relative(content_path, vault_root),
            sidecar_path=_vault_relative(sidecar_path, vault_root),
            visual_capture_packet_path=_vault_relative(packet_path, vault_root),
            status="raw_ingested",
            review_status="pending-review",
            canonical_status="not_promoted",
            requires_review=True,
            source_package_status="not-ingested",
            aor_queue_status="not_queued",
        ),
        provenance={"transformation_chain": chain},
        authority=VisualCaptureAuthority(raw_ingestion_write=True),
    )


def _safe_attachment_filename(attachment: VisualCaptureAttachment) -> str:
    filename = Path(attachment.filename or attachment.relative_path or "attachment").name
    return filename or "attachment"


def _copy_quarantine_attachments(
    packet: VisualCapturePacket,
    *,
    vault_root: Path,
    content_path: Path,
) -> VisualCapturePacket:
    """Copy local image attachments into quarantine-local attachment storage."""

    if not packet.attachments:
        return packet

    vault = vault_root.resolve()
    copy_specs: list[tuple[VisualCaptureAttachment, Path, Path]] = []
    copied_attachments: list[VisualCaptureAttachment] = []
    changed = False
    for index, attachment in enumerate(packet.attachments, start=1):
        if not attachment.mime_type.lower().startswith("image/"):
            copied_attachments.append(attachment)
            continue

        raw_source = Path(attachment.relative_path or attachment.filename)
        source_path = raw_source if raw_source.is_absolute() else vault / raw_source
        source_path = source_path.resolve()
        if not _is_relative_to(source_path, vault):
            raise ValueError("Visual capture attachment copy requires a vault-local source file.")
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Visual capture attachment source not found: {attachment.relative_path}")
        data = source_path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if attachment.sha256 and digest != attachment.sha256:
            raise ValueError("Visual capture attachment hash changed before quarantine copy.")
        if attachment.size_bytes and len(data) != attachment.size_bytes:
            raise ValueError("Visual capture attachment size changed before quarantine copy.")

        target_dir = content_path.parent / "_attachments" / packet.capture_id
        target_name = _safe_attachment_filename(attachment)
        target_path = target_dir / target_name
        if target_path.exists() and target_path.resolve() != source_path:
            target_path = target_dir / f"{index}-{target_name}"
        copy_specs.append((attachment, source_path, target_path))
        copied_attachments.append(
            replace(
                attachment,
                relative_path=_vault_relative(target_path, vault_root),
                sha256=digest,
                size_bytes=len(data),
                redaction_status=attachment.redaction_status or "operator-review-required",
            )
        )
        changed = True

    if not changed:
        return packet

    for _attachment, source_path, target_path in copy_specs:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.resolve() != source_path:
            target_path.write_bytes(source_path.read_bytes())

    warnings = list(packet.quality.extraction_warnings)
    for warning in (
        "screenshot_attachment_copied_to_quarantine",
        "screenshot_attachment_retention_review_required",
    ):
        if warning not in warnings:
            warnings.append(warning)
    chain = list(packet.provenance.get("transformation_chain", []))
    review_policy = build_screenshot_attachment_review_policy(
        copied_attachments,
        review_status=packet.routing.review_status,
        ocr_status=_local_ocr_metadata(packet).get("status") or "not_performed",
        cloud_ocr_allowed=False,
    )
    chain.append(
        {
            "step": "screenshot_attachment_quarantine_copy",
            "method": "vcmi_attachment_copy_policy",
            "at": utc_now(),
            "status": "copied",
            "attachments": [
                {
                    "attachment_id": attachment.attachment_id,
                    "relative_path": attachment.relative_path,
                    "sha256": attachment.sha256,
                    "size_bytes": attachment.size_bytes,
                }
                for attachment in copied_attachments
                if attachment.mime_type.lower().startswith("image/")
            ],
        }
    )
    chain.append(
        {
            "step": "screenshot_attachment_retention_review_policy",
            "method": "vcmi_attachment_review_policy",
            "at": utc_now(),
            "status": review_policy["review_status"],
            "policy_id": review_policy["policy_id"],
            "retention_status": review_policy["retention_status"],
            "runtime_delete_allowed": review_policy["runtime_delete_allowed"],
            "operator_review_required": review_policy["operator_review_required"],
            "attachment_ids": review_policy.get("attachment_ids", []),
        }
    )
    return replace(
        packet,
        attachments=copied_attachments,
        quality=replace(
            packet.quality,
            extraction_warnings=warnings,
        ),
        provenance={"transformation_chain": chain},
    )


def _visual_capture_sidecar_metadata(packet: VisualCapturePacket) -> dict[str, Any]:
    profile = CAPTURE_PROFILES[packet.capture_profile]
    local_ocr = _local_ocr_metadata(packet)
    return {
        "schema_version": packet.schema_version,
        "artifact_type": packet.artifact_type,
        "capture_id": packet.capture_id,
        "profile": packet.capture_profile,
        "method": packet.capture_method,
        "confidence": packet.quality.confidence,
        "extraction_status": packet.quality.extraction_status,
        "extraction_warnings": list(packet.quality.extraction_warnings),
        "review_status": packet.routing.review_status,
        "canonical_status": packet.routing.canonical_status,
        "requires_review": packet.routing.requires_review,
        "source_package_status": packet.routing.source_package_status,
        "aor_queue_status": packet.routing.aor_queue_status,
        "desired_output_kind": profile.desired_output_kind,
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
        "raw_ingestion_path": packet.routing.raw_ingestion_path,
        "sidecar_path": packet.routing.sidecar_path,
        "visual_capture_packet_path": packet.routing.visual_capture_packet_path,
        "attachments": [attachment.to_dict() for attachment in packet.attachments],
        "redaction_status": packet.quality.redaction_status,
        "redaction_count": packet.quality.redaction_count,
        "redaction_categories": list(packet.quality.redaction_categories),
        "raw_content_sha256": packet.content.raw_content_sha256,
        "raw_content_char_count": packet.content.raw_content_char_count,
        "raw_content_truncated": packet.content.raw_content_truncated,
        "raw_generated_separation": True,
        "local_optical_character_recognition": local_ocr,
        "source": packet.source.to_dict(),
        "authority": packet.authority.to_dict(),
    }


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


def _visual_capture_dedup_sha(packet: VisualCapturePacket) -> str:
    """Build a stable dedup key that ignores destination paths and capture time."""

    payload = {
        "schema_version": packet.schema_version,
        "artifact_type": packet.artifact_type,
        "capture_profile": packet.capture_profile,
        "title": packet.title,
        "capture_method": packet.capture_method,
        "source": packet.source.to_dict(),
        "content": {
            "raw_content_sha256": packet.content.raw_content_sha256,
            "generated_summary": packet.content.generated_summary,
            "generated_interpretation": packet.content.generated_interpretation,
            "structured_notes": packet.content.structured_notes,
            "user_intent": packet.content.user_intent,
            "raw_content_truncated": packet.content.raw_content_truncated,
        },
        "quality": {
            "confidence": packet.quality.confidence,
            "extraction_status": packet.quality.extraction_status,
            "redaction_status": packet.quality.redaction_status,
            "redaction_count": packet.quality.redaction_count,
            "redaction_categories": list(packet.quality.redaction_categories),
        },
        "attachments": [attachment.to_dict() for attachment in packet.attachments],
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _content_packet_for_save(packet: VisualCapturePacket, markdown: str) -> ContentPacket:
    profile = CAPTURE_PROFILES[packet.capture_profile]
    origin_kind = (
        "ai-generated"
        if packet.capture_profile == "prompt_chatbot_output_capture"
        else None
    )
    return ContentPacket(
        content=markdown,
        input_class=packet.source.input_class,
        source_platform="visual-capture",
        title=packet.title,
        source_url=packet.source.source_url or None,
        author=None,
        captured_at=packet.captured_at,
        original_name=packet.source.source_page_title or packet.title,
        original_path_or_uri=packet.source.declared_source,
        detected_mime="text/markdown; charset=utf-8",
        workspace_hint=None,
        origin_kind=origin_kind,
        desired_output_kind=profile.desired_output_kind,
        extra_metadata={"visual_capture": _visual_capture_sidecar_metadata(packet)},
        capture_method="capture-to-markdown",
        injection_scan=packet.quality.injection_scan,
    )


def save_visual_capture(
    *,
    vault_root: str | Path,
    packet: VisualCapturePacket | None = None,
    write_visual_capture_packet: bool = True,
    **packet_kwargs: Any,
) -> dict[str, Any]:
    """Write a visual capture Markdown artifact to Phase 8 quarantine.

    This is raw ingestion only. It does not promote content, trigger SIC, enqueue
    AOR work, call providers, or mutate graph/canonical knowledge surfaces.
    """

    vault = Path(vault_root)
    base_packet = packet or build_visual_capture_packet(**packet_kwargs)
    preview_markdown = build_visual_capture_markdown(base_packet)
    if base_packet.quality.save_blocked_by_redaction:
        return {
            "ok": False,
            "surface": "capture-to-markdown",
            "status": "blocked_secret_like",
            "save_allowed": False,
            "write_performed": False,
            "is_duplicate": False,
            "blockers": ["secret_or_credential_indicator_present"],
            "packet": base_packet.to_dict(),
            "markdown": preview_markdown,
            "authority": base_packet.authority.to_dict(),
            "capture_result": {},
        }

    stable_dedup_sha = _visual_capture_dedup_sha(base_packet)
    registry = load_registry(vault)
    if is_duplicate(stable_dedup_sha, registry):
        existing = get_entry(stable_dedup_sha, registry) or {}
        duplicate_result = {
            "is_duplicate": True,
            "content_sha256": stable_dedup_sha,
            "duplicate_of": existing.get("capture_id"),
            "original_captured_at": existing.get("first_captured_at"),
            "title": base_packet.title,
            "source_platform": "visual-capture",
            "input_class": base_packet.source.input_class,
            "dedup_key": "visual_capture_stable",
        }
        return {
            "ok": True,
            "surface": "capture-to-markdown",
            "status": "duplicate",
            "save_allowed": True,
            "write_performed": False,
            "is_duplicate": True,
            "blockers": [],
            "packet": base_packet.to_dict(),
            "markdown": preview_markdown,
            "authority": base_packet.authority.to_dict(),
            "capture_result": duplicate_result,
        }

    predicted_content, predicted_sidecar, predicted_packet = _predicted_paths(base_packet, vault)
    saved_packet = _saved_packet(
        base_packet,
        vault_root=vault,
        content_path=predicted_content,
        sidecar_path=predicted_sidecar,
        packet_path=predicted_packet,
    )
    saved_packet = _copy_quarantine_attachments(
        saved_packet,
        vault_root=vault,
        content_path=predicted_content,
    )
    markdown = build_visual_capture_markdown(saved_packet)
    content_packet = _content_packet_for_save(saved_packet, markdown)
    capture_result = capture_content(content_packet, vault_root=vault)

    if capture_result.get("is_duplicate"):
        return {
            "ok": True,
            "surface": "capture-to-markdown",
            "status": "duplicate",
            "save_allowed": True,
            "write_performed": False,
            "is_duplicate": True,
            "blockers": [],
            "packet": saved_packet.to_dict(),
            "markdown": markdown,
            "authority": saved_packet.authority.to_dict(),
            "capture_result": capture_result,
        }

    content_path = Path(capture_result["content_path"])
    sidecar_path = Path(capture_result["sidecar_path"])
    packet_path = content_path.with_suffix(".visual_capture.json")
    actual_packet = saved_packet
    if content_path != predicted_content or sidecar_path != predicted_sidecar or packet_path != predicted_packet:
        actual_packet = _saved_packet(
            base_packet,
            vault_root=vault,
            content_path=content_path,
            sidecar_path=sidecar_path,
            packet_path=packet_path,
        )
        actual_packet = _copy_quarantine_attachments(
            actual_packet,
            vault_root=vault,
            content_path=content_path,
        )

    if write_visual_capture_packet:
        packet_path.write_text(
            json.dumps(actual_packet.to_dict(), indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

    registry = load_registry(vault)
    register_capture(
        stable_dedup_sha,
        build_registry_entry(
            content_sha256=stable_dedup_sha,
            capture_id=str(capture_result.get("capture_id") or ""),
            first_captured_at=actual_packet.captured_at,
            title=actual_packet.title,
            source_platform="visual-capture",
            source_url=actual_packet.source.source_url or None,
            input_class=actual_packet.source.input_class,
            capture_method="capture-to-markdown",
        ),
        registry,
    )
    save_registry(vault, registry)

    return {
        "ok": True,
        "surface": "capture-to-markdown",
        "status": "raw_ingested",
        "save_allowed": True,
        "write_performed": True,
        "is_duplicate": False,
        "blockers": [],
        "packet": actual_packet.to_dict(),
        "markdown": markdown,
        "authority": actual_packet.authority.to_dict(),
        "capture_result": capture_result,
        "content_path": str(content_path),
        "sidecar_path": str(sidecar_path),
        "visual_capture_packet_path": str(packet_path) if write_visual_capture_packet else "",
        "phase8_capture_id": capture_result.get("capture_id"),
        "visual_capture_id": actual_packet.capture_id,
        "attachment_review_policy": build_screenshot_attachment_review_policy(
            actual_packet.attachments,
            review_status=actual_packet.routing.review_status,
            ocr_status=_local_ocr_metadata(actual_packet).get("status") or "not_performed",
            cloud_ocr_allowed=False,
        ),
        "attachment_disposition_policy": build_attachment_disposition_policy(
            actual_packet.attachments,
            review_status=actual_packet.routing.review_status,
        ),
    }
