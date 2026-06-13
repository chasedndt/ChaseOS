"""Visual Capture & Markdown Ingestion core contract.

Pass 1 is preview-only: it builds packets and Markdown artifacts but does not
write quarantine files, call providers, enqueue AOR work, or mutate canonical
knowledge surfaces.
"""

from .markdown_builder import build_visual_capture_markdown
from .models import (
    VisualCaptureAttachment,
    VisualCaptureAuthority,
    VisualCaptureContent,
    VisualCapturePacket,
    VisualCaptureQuality,
    VisualCaptureRouting,
    VisualCaptureSource,
    VisualCaptureValidationError,
    build_visual_capture_packet,
    validate_visual_capture_packet,
)
from .profiles import CAPTURE_PROFILES, REQUIRED_PROFILE_IDS, VisualCaptureProfile
from .redaction import (
    SECRET_REDACTION_TOKEN,
    SecretRedactionReport,
    redact_secret_like_text,
    scan_secret_like_text,
)
from .service import preview_visual_capture, save_visual_capture
from .attachment_disposition import (
    ATTACHMENT_CLEANUP_POLICY_ID,
    ATTACHMENT_DELETE_CONFIRMATION,
    ATTACHMENT_DISPOSITION_DECISIONS,
    ATTACHMENT_DISPOSITION_POLICY_ID,
    build_attachment_disposition_policy,
    cleanup_capture_attachments,
    update_capture_attachment_disposition,
)
from .attachments import (
    SCREENSHOT_ATTACHMENT_ALLOWED_DIRS,
    ScreenshotAttachmentInfo,
    build_screenshot_attachment,
)
from .extractors import (
    CONTROLLED_BROWSER_ARTIFACT_DIRS,
    CONTROLLED_BROWSER_ARTIFACT_SOURCE_SELECTORS,
    PHOTO_DOCUMENT_TEXT_EXTENSIONS,
    capture_from_controlled_browser_artifact,
    capture_from_photo_or_document_text,
    capture_from_saved_html,
    capture_from_screenshot_attachment,
    capture_from_screenshot_text,
    capture_from_text,
    capture_from_text_file,
)
from .ocr import (
    LOCAL_OCR_POLICY_ID,
    LocalOpticalCharacterRecognitionError,
    build_local_ocr_status_model,
    extract_text_from_image,
    local_ocr_policy,
    resolve_local_ocr_engine,
)
from .external_surface_policy import (
    EXTERNAL_SURFACE_DEFERRAL_POLICY_ID,
    SAFE_CURRENT_INPUTS,
    build_external_surface_deferral_policy,
    is_external_surface_blocked,
)
from .recent import list_recent_visual_captures
from .review_state import (
    OPERATOR_REVIEW_STATE_POLICY_ID,
    REVIEW_STATUSES,
    VisualCaptureReviewStateError,
    build_operator_review_state_policy,
    review_visual_capture_artifact,
)

__all__ = [
    "CAPTURE_PROFILES",
    "OPERATOR_REVIEW_STATE_POLICY_ID",
    "REQUIRED_PROFILE_IDS",
    "REVIEW_STATUSES",
    "SECRET_REDACTION_TOKEN",
    "SecretRedactionReport",
    "VisualCaptureAttachment",
    "VisualCaptureAuthority",
    "VisualCaptureContent",
    "VisualCapturePacket",
    "VisualCaptureProfile",
    "VisualCaptureQuality",
    "VisualCaptureReviewStateError",
    "VisualCaptureRouting",
    "VisualCaptureSource",
    "VisualCaptureValidationError",
    "SCREENSHOT_ATTACHMENT_ALLOWED_DIRS",
    "ATTACHMENT_DISPOSITION_DECISIONS",
    "ATTACHMENT_DISPOSITION_POLICY_ID",
    "ATTACHMENT_CLEANUP_POLICY_ID",
    "ATTACHMENT_DELETE_CONFIRMATION",
    "LOCAL_OCR_POLICY_ID",
    "LocalOpticalCharacterRecognitionError",
    "ScreenshotAttachmentInfo",
    "build_attachment_disposition_policy",
    "cleanup_capture_attachments",
    "build_local_ocr_status_model",
    "build_screenshot_attachment",
    "build_operator_review_state_policy",
    "build_visual_capture_markdown",
    "build_visual_capture_packet",
    "CONTROLLED_BROWSER_ARTIFACT_DIRS",
    "CONTROLLED_BROWSER_ARTIFACT_SOURCE_SELECTORS",
    "PHOTO_DOCUMENT_TEXT_EXTENSIONS",
    "capture_from_controlled_browser_artifact",
    "capture_from_photo_or_document_text",
    "capture_from_saved_html",
    "capture_from_screenshot_attachment",
    "capture_from_screenshot_text",
    "capture_from_text",
    "capture_from_text_file",
    "extract_text_from_image",
    "EXTERNAL_SURFACE_DEFERRAL_POLICY_ID",
    "SAFE_CURRENT_INPUTS",
    "build_external_surface_deferral_policy",
    "is_external_surface_blocked",
    "list_recent_visual_captures",
    "preview_visual_capture",
    "redact_secret_like_text",
    "review_visual_capture_artifact",
    "update_capture_attachment_disposition",
    "local_ocr_policy",
    "resolve_local_ocr_engine",
    "save_visual_capture",
    "scan_secret_like_text",
    "validate_visual_capture_packet",
]
