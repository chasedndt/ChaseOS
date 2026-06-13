"""Attachment validators for Capture to Markdown fallback sources."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

from runtime.browser_runtime.artifacts import validate_browser_artifact_path

from .models import VisualCaptureAttachment
from .redaction import scan_secret_like_text


SCREENSHOT_ATTACHMENT_REVIEW_POLICY_ID = "vcmi.screenshot_attachment.retention.v1"

SCREENSHOT_ATTACHMENT_ALLOWED_DIRS = (
    "03_INPUTS/00_QUARANTINE/Photo-Documents",
    "07_LOGS/Operator-Screenshots",
    "07_LOGS/Browser-Runs",
    "runtime/browser_runtime/artifacts",
    "runtime/studio/webview_artifacts",
)

SCREENSHOT_ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024
SCREENSHOT_ATTACHMENT_MIN_BYTES = 32

_IMAGE_EXTENSION_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

_FORBIDDEN_SCREENSHOT_PATH_MARKERS = (
    "/.env",
    "/secrets/",
    "/secret/",
    "/credentials/",
    "/credential/",
    "/wallet",
    "/seed",
    "/password",
    "/keychain",
    "/cookies/",
    "/sessions/",
    "/sessionstore/",
    "/browser-history/",
    "/chrome-history/",
    "/edge-history/",
    "/localstorage/",
    "/indexeddb/",
)


def build_screenshot_attachment_review_policy(
    attachments: list[VisualCaptureAttachment],
    *,
    review_status: str = "pending-review",
    ocr_status: str = "not_performed",
    cloud_ocr_allowed: bool = False,
) -> dict[str, Any]:
    """Return the no-delete review policy for screenshot attachment evidence."""

    image_attachments = [
        attachment
        for attachment in attachments
        if attachment.mime_type.lower().startswith("image/")
    ]
    if not image_attachments:
        return {
            "policy_id": SCREENSHOT_ATTACHMENT_REVIEW_POLICY_ID,
            "applicable": False,
            "attachment_count": 0,
            "storage_status": "not_applicable",
            "retention_status": "not_applicable",
            "review_status": "not_applicable",
            "operator_review_required": False,
            "cleanup_requires_operator_decision": False,
            "runtime_delete_allowed": False,
            "delete_allowed_by_runtime": False,
            "ocr_status": "not_applicable",
            "cloud_ocr_allowed": bool(cloud_ocr_allowed),
        }

    storage_statuses = {
        _screenshot_attachment_storage_status(attachment)
        for attachment in image_attachments
    }
    storage_status = (
        next(iter(storage_statuses))
        if len(storage_statuses) == 1
        else "mixed"
    )
    return {
        "policy_id": SCREENSHOT_ATTACHMENT_REVIEW_POLICY_ID,
        "applicable": True,
        "attachment_count": len(image_attachments),
        "attachment_ids": [attachment.attachment_id for attachment in image_attachments],
        "attachment_paths": [
            attachment.relative_path or attachment.filename
            for attachment in image_attachments
        ],
        "storage_status": storage_status,
        "retention_status": "retain_until_operator_review",
        "review_status": review_status or "pending-review",
        "operator_review_required": True,
        "cleanup_requires_operator_decision": True,
        "runtime_delete_allowed": False,
        "delete_allowed_by_runtime": False,
        "retention_scope": "raw_quarantine_attachment",
        "ocr_status": str(ocr_status or "not_performed"),
        "cloud_ocr_allowed": bool(cloud_ocr_allowed),
        "screenshot_content_redaction_status": "not_performed",
        "content_privacy_status": "not_inferred",
        "governance_note": (
            "Screenshot attachments are raw quarantine evidence retained until "
            "operator review; Capture to Markdown does not delete copied "
            "attachments, infer private image contents, or run cloud optical "
            "character recognition."
        ),
    }


def _screenshot_attachment_storage_status(attachment: VisualCaptureAttachment) -> str:
    normalized = (attachment.relative_path or attachment.filename).replace("\\", "/")
    if (
        normalized.startswith("03_INPUTS/00_QUARANTINE/")
        and "/_attachments/" in normalized
    ):
        return "copied_to_quarantine"
    return "validated_source_reference"


@dataclass(frozen=True)
class ScreenshotAttachmentInfo:
    """Validated local screenshot attachment plus text-extraction posture metadata."""

    attachment: VisualCaptureAttachment
    absolute_path: str
    warnings: tuple[str, ...]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachment": self.attachment.to_dict(),
            "absolute_path": self.absolute_path,
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }


def build_screenshot_attachment(
    file_path: str | Path,
    *,
    vault_root: str | Path,
    attachment_id: str = "screenshot-1",
    min_bytes: int = SCREENSHOT_ATTACHMENT_MIN_BYTES,
    max_bytes: int = SCREENSHOT_ATTACHMENT_MAX_BYTES,
    optical_character_recognition_requested: bool = False,
) -> ScreenshotAttachmentInfo:
    """Validate an explicit vault-local screenshot file and return attachment metadata.

    This validates only the local file, path boundary, image signature, size,
    hash, and byte-level nonblank posture. It does not inspect pixels,
    or infer whether private/authenticated content is visible inside the image.
    """

    validation = validate_browser_artifact_path(
        file_path,
        root=vault_root,
        artifact_type="screenshot_attachment",
        require_exists=True,
        min_bytes=min_bytes,
        allowed_dirs=SCREENSHOT_ATTACHMENT_ALLOWED_DIRS,
    )
    if not validation.ok:
        raise ValueError(validation.error or validation.status)

    path = Path(validation.path)
    relative_path = validation.relative_path or str(path)
    _validate_screenshot_path_text(relative_path)

    data = path.read_bytes()
    if len(data) > max_bytes:
        raise ValueError(
            f"Screenshot attachment is too large: {len(data):,} bytes exceeds "
            f"maximum {max_bytes:,} bytes."
        )
    _validate_nonblank_bytes(data)
    mime = _detect_image_mime(path, data)
    digest = hashlib.sha256(data).hexdigest()

    attachment = VisualCaptureAttachment(
        attachment_id=str(attachment_id or "screenshot-1"),
        filename=path.name,
        relative_path=relative_path,
        mime_type=mime,
        sha256=digest,
        size_bytes=len(data),
        redaction_status="operator-review-required",
    )
    warnings = [
        "screenshot_attachment_imported",
        "nonblank_byte_check_only",
        "private_or_authenticated_content_not_detectable_by_byte_check",
        "no_cloud_ocr",
        "cloud_optical_character_recognition_blocked",
    ]
    if optical_character_recognition_requested:
        warnings.extend(
            [
                "local_optical_character_recognition_requested",
                "local_only_optical_character_recognition",
            ]
        )
    else:
        warnings.extend(
            [
                "ocr_not_performed",
                "local_only_ocr_deferred",
            ]
        )
    metadata = {
        "validation_status": "screenshot_attachment_validated",
        "allowed_dirs": list(SCREENSHOT_ATTACHMENT_ALLOWED_DIRS),
        "nonblank_check": "byte-level-only",
        "retention_status": "retain_until_operator_review",
        "review_status": "pending-review",
        "operator_review_required": True,
        "cleanup_requires_operator_decision": True,
        "runtime_delete_allowed": False,
        "ocr_status": (
            "requested"
            if optical_character_recognition_requested
            else "not_performed"
        ),
        "cloud_ocr_allowed": False,
        "cloud_optical_character_recognition_allowed": False,
    }
    return ScreenshotAttachmentInfo(
        attachment=attachment,
        absolute_path=str(path),
        warnings=tuple(warnings),
        metadata=metadata,
    )


def _validate_screenshot_path_text(relative_path: str) -> None:
    normalized = "/" + str(relative_path).replace("\\", "/").lower().strip("/")
    if scan_secret_like_text(normalized).redaction_count:
        raise ValueError("Screenshot attachment path contains secret-like material.")
    if any(marker in normalized for marker in _FORBIDDEN_SCREENSHOT_PATH_MARKERS):
        raise ValueError(
            "Screenshot attachment path appears to reference secrets, credentials, "
            "browser history, cookies, sessions, passwords, wallet data, or storage."
        )


def _detect_image_mime(path: Path, data: bytes) -> str:
    expected = _IMAGE_EXTENSION_MIME.get(path.suffix.lower())
    if expected is None:
        raise ValueError(
            "Unsupported screenshot attachment extension. "
            "Allowed extensions: .png, .jpg, .jpeg, .webp."
        )
    detected = ""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        detected = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        detected = "image/jpeg"
    elif len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        detected = "image/webp"
    if not detected:
        raise ValueError("Screenshot attachment does not match a supported image signature.")
    if detected != expected:
        raise ValueError(
            f"Screenshot attachment extension does not match image signature: "
            f"{path.suffix.lower()} vs {detected}."
        )
    return detected


def _validate_nonblank_bytes(data: bytes) -> None:
    sample = data[:4096]
    if len(set(sample)) <= 1:
        raise ValueError("Screenshot attachment failed byte-level nonblank validation.")
