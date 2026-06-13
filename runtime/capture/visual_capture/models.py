"""Core packet models for Visual Capture & Markdown Ingestion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import re
from typing import Any

from runtime.capture.content_packet import VALID_INPUT_CLASSES

from .profiles import ARTIFACT_TYPE, SCHEMA_VERSION, get_capture_profile
from .redaction import SecretRedactionReport, scan_secret_like_text


class VisualCaptureValidationError(ValueError):
    """Raised when a visual capture packet violates the Pass 1 contract."""


def utc_now() -> str:
    """Return a UTC timestamp suitable for packet metadata."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _compact_timestamp(value: str) -> str:
    compact = re.sub(r"[^0-9]", "", value)[:14]
    return compact or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _short_digest(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def new_capture_id(captured_at: str, seed: str) -> str:
    return f"vcmi_{_compact_timestamp(captured_at)}_{_short_digest(seed)}"


def _norm_text(value: str | None) -> str:
    return str(value or "").strip()


def _content_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class DictModel:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VisualCaptureSource(DictModel):
    source_app: str = "manual"
    source_window_title: str = ""
    source_page_title: str = ""
    source_url: str = ""
    source_platform: str = "visual-capture"
    input_class: str = "clipboard"
    declared_source: str = "operator_paste"


@dataclass
class VisualCaptureContent(DictModel):
    raw_extracted_text: str
    raw_content_sha256: str
    raw_content_char_count: int
    raw_content_truncated: bool = False
    generated_summary: str = ""
    generated_interpretation: str = ""
    structured_notes: str = ""
    user_intent: str = ""
    original_content_secret_like: bool = False


@dataclass
class VisualCaptureQuality(DictModel):
    confidence: str = "operator_supplied"
    extraction_status: str = "complete"
    extraction_warnings: list[str] = field(default_factory=list)
    redaction_status: str = "not_needed"
    redaction_count: int = 0
    redaction_categories: list[str] = field(default_factory=list)
    save_blocked_by_redaction: bool = False
    injection_scan: str = "not-scanned"


@dataclass
class VisualCaptureAttachment(DictModel):
    attachment_id: str
    filename: str
    relative_path: str
    mime_type: str = "application/octet-stream"
    sha256: str = ""
    size_bytes: int = 0
    redaction_status: str = "not-scanned"


@dataclass
class VisualCaptureRouting(DictModel):
    raw_ingestion_path: str = ""
    sidecar_path: str = ""
    visual_capture_packet_path: str = ""
    status: str = "preview_only"
    review_status: str = "pending-review"
    canonical_status: str = "not_promoted"
    requires_review: bool = True
    source_package_status: str = "not-ingested"
    aor_queue_status: str = "not_queued"


@dataclass
class VisualCaptureAuthority(DictModel):
    raw_ingestion_write: bool = False
    canonical_mutation_allowed: bool = False
    graph_index_mutation_allowed: bool = False
    provider_call_allowed: bool = False
    external_send_allowed: bool = False
    silent_capture_allowed: bool = False


@dataclass
class VisualCapturePacket(DictModel):
    schema_version: str
    artifact_type: str
    capture_id: str
    title: str
    capture_profile: str
    capture_method: str
    captured_at: str
    captured_by: str
    timezone: str
    source: VisualCaptureSource
    content: VisualCaptureContent
    quality: VisualCaptureQuality
    attachments: list[VisualCaptureAttachment]
    routing: VisualCaptureRouting
    provenance: dict[str, Any]
    authority: VisualCaptureAuthority


def _redact_fields(fields: dict[str, str]) -> tuple[dict[str, str], list[SecretRedactionReport]]:
    reports: list[SecretRedactionReport] = []
    safe_fields: dict[str, str] = {}
    for key, value in fields.items():
        report = scan_secret_like_text(value)
        reports.append(report)
        safe_fields[key] = report.redacted_text
    return safe_fields, reports


def _redaction_summary(
    reports: list[SecretRedactionReport],
    *,
    allow_secret_redaction: bool,
) -> tuple[str, int, list[str], bool]:
    total = sum(report.redaction_count for report in reports)
    categories: list[str] = []
    for report in reports:
        categories.extend(report.indicator_categories)
    unique_categories = list(dict.fromkeys(categories))
    if not total:
        return "not_needed", 0, [], False
    if allow_secret_redaction:
        return "redacted", total, unique_categories, False
    return "blocked_secret_like", total, unique_categories, True


def _coerce_attachments(
    attachments: list[VisualCaptureAttachment | dict[str, Any]] | None,
) -> list[VisualCaptureAttachment]:
    coerced: list[VisualCaptureAttachment] = []
    for index, attachment in enumerate(attachments or [], start=1):
        if isinstance(attachment, VisualCaptureAttachment):
            coerced.append(attachment)
            continue
        payload = dict(attachment)
        payload.setdefault("attachment_id", f"attachment-{index}")
        payload.setdefault("filename", payload.get("relative_path", f"attachment-{index}"))
        payload.setdefault("relative_path", payload["filename"])
        coerced.append(VisualCaptureAttachment(**payload))
    return coerced


def build_visual_capture_packet(
    *,
    title: str,
    raw_extracted_text: str,
    profile: str = "research_note",
    capture_method: str = "manual_paste",
    user_intent: str = "",
    structured_notes: str = "",
    generated_summary: str = "",
    generated_interpretation: str = "",
    source_app: str = "manual",
    source_window_title: str = "",
    source_page_title: str = "",
    source_url: str = "",
    source_platform: str = "visual-capture",
    declared_source: str = "operator_paste",
    input_class: str | None = None,
    captured_by: str = "studio-operator",
    timezone_name: str = "Europe/London",
    confidence: str = "operator_supplied",
    extraction_status: str = "complete",
    extraction_warnings: list[str] | None = None,
    raw_content_truncated: bool = False,
    attachments: list[VisualCaptureAttachment | dict[str, Any]] | None = None,
    allow_secret_redaction: bool = False,
    capture_id: str | None = None,
    captured_at: str | None = None,
) -> VisualCapturePacket:
    """Build a preview-only visual capture packet.

    Secret-like fields are always redacted in the returned packet. If explicit
    redacted-save approval is not supplied, the packet remains save-blocked.
    """

    profile_model = get_capture_profile(profile)
    safe_at = captured_at or utc_now()
    selected_input_class = input_class or profile_model.default_input_class
    if selected_input_class not in VALID_INPUT_CLASSES:
        raise VisualCaptureValidationError(
            f"Unknown input_class '{selected_input_class}'. "
            f"Valid classes: {sorted(VALID_INPUT_CLASSES)}"
        )

    if not _norm_text(raw_extracted_text):
        raise VisualCaptureValidationError("raw_extracted_text is required for Pass 1 preview.")
    if not _norm_text(title):
        raise VisualCaptureValidationError("title is required for visual capture preview.")

    fields = {
        "title": _norm_text(title),
        "raw_extracted_text": str(raw_extracted_text),
        "user_intent": str(user_intent or ""),
        "structured_notes": str(structured_notes or ""),
        "generated_summary": str(generated_summary or ""),
        "generated_interpretation": str(generated_interpretation or ""),
    }
    safe_fields, reports = _redact_fields(fields)
    redaction_status, redaction_count, categories, save_blocked = _redaction_summary(
        reports,
        allow_secret_redaction=allow_secret_redaction,
    )

    safe_raw = safe_fields["raw_extracted_text"]
    safe_capture_id = capture_id or new_capture_id(
        safe_at,
        seed=f"{safe_fields['title']}:{safe_raw}",
    )

    packet = VisualCapturePacket(
        schema_version=SCHEMA_VERSION,
        artifact_type=ARTIFACT_TYPE,
        capture_id=safe_capture_id,
        title=safe_fields["title"],
        capture_profile=profile_model.profile_id,
        capture_method=_norm_text(capture_method) or "manual_paste",
        captured_at=safe_at,
        captured_by=_norm_text(captured_by) or "studio-operator",
        timezone=_norm_text(timezone_name) or "Europe/London",
        source=VisualCaptureSource(
            source_app=_norm_text(source_app) or "manual",
            source_window_title=_norm_text(source_window_title),
            source_page_title=_norm_text(source_page_title),
            source_url=_norm_text(source_url),
            source_platform=_norm_text(source_platform) or "visual-capture",
            input_class=selected_input_class,
            declared_source=_norm_text(declared_source) or "operator_paste",
        ),
        content=VisualCaptureContent(
            raw_extracted_text=safe_raw,
            raw_content_sha256=_content_sha(safe_raw),
            raw_content_char_count=len(safe_raw),
            raw_content_truncated=raw_content_truncated,
            generated_summary=safe_fields["generated_summary"],
            generated_interpretation=safe_fields["generated_interpretation"],
            structured_notes=safe_fields["structured_notes"],
            user_intent=safe_fields["user_intent"],
            original_content_secret_like=bool(redaction_count),
        ),
        quality=VisualCaptureQuality(
            confidence=_norm_text(confidence) or "operator_supplied",
            extraction_status=_norm_text(extraction_status) or "complete",
            extraction_warnings=list(extraction_warnings or []),
            redaction_status=redaction_status,
            redaction_count=redaction_count,
            redaction_categories=categories,
            save_blocked_by_redaction=save_blocked,
            injection_scan="not-scanned",
        ),
        attachments=_coerce_attachments(attachments),
        routing=VisualCaptureRouting(),
        provenance={
            "transformation_chain": [
                {
                    "step": "operator_selected_source",
                    "method": _norm_text(capture_method) or "manual_paste",
                    "at": safe_at,
                },
                {
                    "step": "capture_redaction_scan",
                    "method": "vcmi_secret_like_redaction",
                    "at": safe_at,
                    "status": redaction_status,
                },
                {
                    "step": "visual_capture_packet_build",
                    "method": "vcmi_core_contract",
                    "at": safe_at,
                },
                {
                    "step": "markdown_artifact_preview",
                    "method": "vcmi_markdown_builder",
                    "at": safe_at,
                },
            ]
        },
        authority=VisualCaptureAuthority(),
    )
    validate_visual_capture_packet(packet, require_no_write=True)
    return packet


def validate_visual_capture_packet(
    packet: VisualCapturePacket,
    *,
    require_no_write: bool = True,
) -> None:
    """Validate the VCMI Pass 1 packet invariants."""

    if packet.schema_version != SCHEMA_VERSION:
        raise VisualCaptureValidationError(f"schema_version must be {SCHEMA_VERSION}")
    if packet.artifact_type != ARTIFACT_TYPE:
        raise VisualCaptureValidationError(f"artifact_type must be {ARTIFACT_TYPE}")
    if not _norm_text(packet.capture_id).startswith("vcmi_"):
        raise VisualCaptureValidationError("capture_id must start with 'vcmi_'")
    if packet.capture_profile != get_capture_profile(packet.capture_profile).profile_id:
        raise VisualCaptureValidationError("capture_profile is not normalized")
    if not _norm_text(packet.content.raw_extracted_text):
        raise VisualCaptureValidationError("raw_extracted_text is required")
    if packet.routing.review_status != "pending-review":
        raise VisualCaptureValidationError("review_status must be pending-review")
    if packet.routing.canonical_status != "not_promoted":
        raise VisualCaptureValidationError("canonical_status must be not_promoted")
    if packet.routing.status not in {"preview_only", "raw_ingested"}:
        raise VisualCaptureValidationError("routing.status must be preview_only or raw_ingested")
    if packet.routing.requires_review is not True:
        raise VisualCaptureValidationError("requires_review must be true")
    if packet.routing.status == "raw_ingested" and not _norm_text(packet.routing.raw_ingestion_path):
        raise VisualCaptureValidationError("raw_ingestion_path is required for raw_ingested packets")
    if packet.authority.canonical_mutation_allowed:
        raise VisualCaptureValidationError("canonical mutation is not allowed")
    if packet.authority.graph_index_mutation_allowed:
        raise VisualCaptureValidationError("graph mutation is not allowed")
    if packet.authority.provider_call_allowed:
        raise VisualCaptureValidationError("provider calls are not allowed")
    if packet.authority.external_send_allowed:
        raise VisualCaptureValidationError("external sends are not allowed")
    if packet.authority.silent_capture_allowed:
        raise VisualCaptureValidationError("silent capture is not allowed")
    if require_no_write:
        if packet.routing.status != "preview_only":
            raise VisualCaptureValidationError("Pass 1 routing.status must be preview_only")
        if packet.authority.raw_ingestion_write:
            raise VisualCaptureValidationError("Pass 1 raw_ingestion_write must be false")
