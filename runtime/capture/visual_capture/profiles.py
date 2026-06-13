"""Capture profile definitions for Capture to Markdown."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from runtime.capture.content_packet import INPUT_CLASS_CLIPBOARD, INPUT_CLASS_SOURCE


SCHEMA_VERSION = "vcmi.v0.1"
ARTIFACT_TYPE = "visual_capture"

PROFILE_RAW_ARCHIVE = "raw_archive"
PROFILE_RESEARCH_NOTE = "research_note"
PROFILE_FEATURE_PRODUCT_SPEC = "feature_product_spec"
PROFILE_DEBUG_ERROR_CAPTURE = "debug_error_capture"
PROFILE_UI_UX_TEARDOWN = "ui_ux_teardown"
PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE = "prompt_chatbot_output_capture"

REQUIRED_PROFILE_IDS: tuple[str, ...] = (
    PROFILE_RAW_ARCHIVE,
    PROFILE_RESEARCH_NOTE,
    PROFILE_FEATURE_PRODUCT_SPEC,
    PROFILE_DEBUG_ERROR_CAPTURE,
    PROFILE_UI_UX_TEARDOWN,
    PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE,
)


@dataclass(frozen=True)
class VisualCaptureProfile:
    """Operator-selected intent profile for one visual capture."""

    profile_id: str
    label: str
    default_input_class: str
    desired_output_kind: str
    description: str
    suggested_tags: tuple[str, ...]
    generated_interpretation_allowed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CAPTURE_PROFILES: dict[str, VisualCaptureProfile] = {
    PROFILE_RAW_ARCHIVE: VisualCaptureProfile(
        profile_id=PROFILE_RAW_ARCHIVE,
        label="Raw Archive",
        default_input_class=INPUT_CLASS_CLIPBOARD,
        desired_output_kind="reference",
        description="Preserve the extracted source text with minimal operator notes.",
        suggested_tags=("visual-capture", "raw-archive"),
        generated_interpretation_allowed=False,
    ),
    PROFILE_RESEARCH_NOTE: VisualCaptureProfile(
        profile_id=PROFILE_RESEARCH_NOTE,
        label="Research Note",
        default_input_class=INPUT_CLASS_SOURCE,
        desired_output_kind="source-note",
        description="Capture source material for later reviewed research ingestion.",
        suggested_tags=("visual-capture", "research-note"),
    ),
    PROFILE_FEATURE_PRODUCT_SPEC: VisualCaptureProfile(
        profile_id=PROFILE_FEATURE_PRODUCT_SPEC,
        label="Feature/Product Spec",
        default_input_class=INPUT_CLASS_CLIPBOARD,
        desired_output_kind="feature-spec",
        description="Convert visible product or chatbot output into a reviewed feature-spec draft.",
        suggested_tags=("visual-capture", "feature-spec"),
    ),
    PROFILE_DEBUG_ERROR_CAPTURE: VisualCaptureProfile(
        profile_id=PROFILE_DEBUG_ERROR_CAPTURE,
        label="Debug/Error Capture",
        default_input_class=INPUT_CLASS_SOURCE,
        desired_output_kind="debug-note",
        description="Capture error text, logs, stack traces, or debugging context.",
        suggested_tags=("visual-capture", "debug-error"),
    ),
    PROFILE_UI_UX_TEARDOWN: VisualCaptureProfile(
        profile_id=PROFILE_UI_UX_TEARDOWN,
        label="User Interface and User Experience Teardown",
        default_input_class=INPUT_CLASS_SOURCE,
        desired_output_kind="ui-ux-teardown",
        description="Capture a product surface for later reviewed user interface or user experience analysis.",
        suggested_tags=("visual-capture", "ui-ux"),
    ),
    PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE: VisualCaptureProfile(
        profile_id=PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE,
        label="Prompt/Chatbot Output Capture",
        default_input_class=INPUT_CLASS_CLIPBOARD,
        desired_output_kind="generated-idea",
        description="Capture prompt output or chatbot content while keeping generated text untrusted.",
        suggested_tags=("visual-capture", "prompt-output"),
    ),
}


def normalize_profile_id(value: str) -> str:
    """Normalize common UI spellings to the internal profile id."""

    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    aliases = {
        "raw": PROFILE_RAW_ARCHIVE,
        "raw_archive": PROFILE_RAW_ARCHIVE,
        "research": PROFILE_RESEARCH_NOTE,
        "research_note": PROFILE_RESEARCH_NOTE,
        "feature": PROFILE_FEATURE_PRODUCT_SPEC,
        "product_spec": PROFILE_FEATURE_PRODUCT_SPEC,
        "feature_product_spec": PROFILE_FEATURE_PRODUCT_SPEC,
        "debug": PROFILE_DEBUG_ERROR_CAPTURE,
        "error": PROFILE_DEBUG_ERROR_CAPTURE,
        "debug_error": PROFILE_DEBUG_ERROR_CAPTURE,
        "debug_error_capture": PROFILE_DEBUG_ERROR_CAPTURE,
        "ui": PROFILE_UI_UX_TEARDOWN,
        "ux": PROFILE_UI_UX_TEARDOWN,
        "ui_ux": PROFILE_UI_UX_TEARDOWN,
        "ui_ux_teardown": PROFILE_UI_UX_TEARDOWN,
        "prompt": PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE,
        "chatbot": PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE,
        "prompt_output": PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE,
        "prompt_chatbot_output": PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE,
        "prompt_chatbot_output_capture": PROFILE_PROMPT_CHATBOT_OUTPUT_CAPTURE,
    }
    return aliases.get(normalized, normalized)


def get_capture_profile(value: str) -> VisualCaptureProfile:
    """Return a capture profile or raise ValueError for unknown ids."""

    profile_id = normalize_profile_id(value)
    try:
        return CAPTURE_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(
            f"Unknown visual capture profile '{value}'. "
            f"Valid profiles: {sorted(CAPTURE_PROFILES)}"
        ) from exc
