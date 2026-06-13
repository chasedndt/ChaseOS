"""Studio panel adapter for Visual Capture to Markdown ingestion.

This module is the Studio-facing wrapper around the Visual Capture Markdown
Ingestion services. It builds previews without writing and saves only through
the Phase 8 quarantine boundary.
"""

from __future__ import annotations

import json
from pathlib import Path, Path as _Path
from typing import Any

from runtime.acquisition.visual_capture_downstream_gate import (
    build_visual_capture_downstream_gate_policy,
)
from runtime.acquisition.visual_capture_source_pack_approval_preview import (
    build_visual_capture_source_pack_approval_preview,
    build_visual_capture_source_pack_approval_preview_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor,
    build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness,
    build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor,
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness,
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_task_writer import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task,
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task_writer_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_consumption_executor import (
    build_visual_capture_source_pack_aor_dispatch_approval_consumption,
    build_visual_capture_source_pack_aor_dispatch_approval_consumption_executor_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_consumption_readiness import (
    build_visual_capture_source_pack_aor_dispatch_approval_consumption_readiness,
    build_visual_capture_source_pack_aor_dispatch_approval_consumption_readiness_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_decision_writer import (
    build_visual_capture_source_pack_aor_dispatch_approval_decision,
    build_visual_capture_source_pack_aor_dispatch_approval_decision_writer_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_design import (
    build_visual_capture_source_pack_aor_dispatch_approval_design,
    build_visual_capture_source_pack_aor_dispatch_approval_design_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_request_writer import (
    build_visual_capture_source_pack_aor_dispatch_approval_request,
    build_visual_capture_source_pack_aor_dispatch_approval_request_writer_policy,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_readiness import (
    build_visual_capture_source_pack_aor_dispatch_readiness,
    build_visual_capture_source_pack_aor_dispatch_readiness_policy,
)
from runtime.acquisition.visual_capture_source_pack_write_executor import (
    build_visual_capture_source_pack_write_executor_policy,
    execute_visual_capture_source_pack_write,
)
from runtime.capture.visual_capture.attachment_disposition import (
    ATTACHMENT_DELETE_CONFIRMATION,
    cleanup_capture_attachments,
    build_attachment_disposition_policy,
    update_capture_attachment_disposition,
)
from runtime.capture.visual_capture.external_surface_policy import (
    build_external_surface_deferral_policy,
)
from runtime.capture.visual_capture.extractors import (
    capture_from_controlled_browser_artifact,
    capture_from_photo_or_document_text,
    capture_from_saved_html,
    capture_from_screenshot_attachment,
    capture_from_screenshot_text,
    capture_from_text,
    capture_from_text_file,
)
from runtime.capture.visual_capture.markdown_builder import build_visual_capture_markdown
from runtime.capture.visual_capture.models import VisualCapturePacket
from runtime.capture.visual_capture.ocr import build_local_ocr_status_model
from runtime.capture.visual_capture.profiles import CAPTURE_PROFILES, PROFILE_RESEARCH_NOTE
from runtime.capture.visual_capture.recent import list_recent_visual_captures
from runtime.capture.visual_capture.review_state import (
    build_operator_review_state_policy,
    review_visual_capture_artifact,
)
from runtime.capture.visual_capture.service import save_visual_capture
from runtime.studio.capture_hotkey_settings import build_capture_hotkey_settings_model
from runtime.studio.capture_collector_settings import (
    build_capture_collector_settings_model,
)
from runtime.studio.capture_ocr_settings import (
    build_capture_local_image_text_settings_model,
    load_capture_local_image_text_settings,
)


MODEL_VERSION = "studio.capture_to_markdown_panel.v1"
SURFACE_ID = "studio_capture_to_markdown_panel"
NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass25-source-pack-aor-dispatch-"
    "agent-bus-claimed-task-aor-dry-run-executor"
)

SOURCE_MODE_MANUAL_TEXT = "manual_text"
SOURCE_MODE_LOCAL_TEXT_FILE = "local_text_file"
SOURCE_MODE_SAVED_HTML_FILE = "saved_html_file"
SOURCE_MODE_CONTROLLED_HTML_ARTIFACT = "controlled_html_artifact"
SOURCE_MODE_SCREENSHOT_ATTACHMENT = "screenshot_attachment"
SOURCE_MODE_SCREENSHOT_TEXT_EXTRACTION = "screenshot_text_extraction"
SOURCE_MODE_PHOTO_DOCUMENT_TEXT_EXTRACTION = "photo_document_text_extraction"

_WINDOW_SIZE_MATRIX_PATTERN = "*capture-markdown-window-size-matrix*.json"
_DOWNSTREAM_FAILURE_MATRIX_PATTERN = "*capture-markdown-downstream-failure-state-matrix*.json"
_SOURCE_SHAPE_MATRIX_PATTERN = "*capture-markdown-source-shape-matrix*.json"
_IMAGE_TO_MARKDOWN_LIVE_PROOF_PATTERN = "*capture-markdown*image-to-markdown-live-proof*.json"

_SOURCE_MODES = [
    {
        "id": SOURCE_MODE_MANUAL_TEXT,
        "label": "Manual Text",
        "description": "Operator-supplied text from a visible capture or paste.",
        "requires_text": True,
        "requires_vault_local_path": False,
        "preview_writes": False,
        "save_writes": True,
    },
    {
        "id": SOURCE_MODE_LOCAL_TEXT_FILE,
        "label": "Vault Text File",
        "description": "Explicit text or Markdown file under the selected vault.",
        "requires_text": False,
        "requires_vault_local_path": True,
        "preview_writes": False,
        "save_writes": True,
    },
    {
        "id": SOURCE_MODE_SAVED_HTML_FILE,
        "label": "Vault Saved HTML",
        "description": "Explicit saved HTML file under the selected vault.",
        "requires_text": False,
        "requires_vault_local_path": True,
        "preview_writes": False,
        "save_writes": True,
    },
    {
        "id": SOURCE_MODE_CONTROLLED_HTML_ARTIFACT,
        "label": "Controlled HTML Artifact",
        "description": "Browser Runtime or Studio webview HTML artifact under allowed evidence dirs with a declared URL.",
        "requires_text": False,
        "requires_vault_local_path": True,
        "requires_declared_url": True,
        "preview_writes": False,
        "save_writes": True,
    },
    {
        "id": SOURCE_MODE_SCREENSHOT_ATTACHMENT,
        "label": "Screenshot Attachment",
        "description": "Explicit vault-local screenshot image under allowed evidence dirs; no text extraction.",
        "requires_text": False,
        "requires_vault_local_path": True,
        "preview_writes": False,
        "save_writes": True,
        "ocr_performed": False,
    },
    {
        "id": SOURCE_MODE_SCREENSHOT_TEXT_EXTRACTION,
        "label": "Screenshot Text Extraction",
        "description": "Explicit vault-local screenshot image; extracts text through a local image text engine.",
        "requires_text": False,
        "requires_vault_local_path": True,
        "requires_local_ocr_engine": True,
        "preview_writes": False,
        "save_writes": True,
        "ocr_performed": True,
    },
    {
        "id": SOURCE_MODE_PHOTO_DOCUMENT_TEXT_EXTRACTION,
        "label": "Photo or Document Text",
        "description": "Explicit vault-local image, PDF, Word document, rich text, text, or Markdown file; extracts text locally.",
        "requires_text": False,
        "requires_vault_local_path": True,
        "requires_local_text_engine_for_images": True,
        "preview_writes": False,
        "save_writes": True,
        "cloud_extraction_allowed": False,
    },
]


def _build_capture_source_options(
    external_surface_policy: dict[str, Any],
    capture_hotkeys: dict[str, Any],
    capture_collectors: dict[str, Any],
    local_ocr_status: dict[str, Any],
) -> list[dict[str, Any]]:
    blocked_reasons = {
        item.get("id"): item.get("reason")
        for item in external_surface_policy.get("blocked_surfaces", [])
        if isinstance(item, dict)
    }
    local_ocr_engine = local_ocr_status.get("engine") if isinstance(local_ocr_status.get("engine"), dict) else {}
    local_ocr_available = bool(local_ocr_engine.get("available"))
    collector_by_id = {
        str(item.get("id")): item
        for item in capture_collectors.get("collectors", [])
        if isinstance(item, dict)
    }
    screen_collector = collector_by_id.get("screen_capture") or {}
    screen_collector_enabled = bool(screen_collector.get("available_in_studio"))
    display_region_collector = collector_by_id.get("display_region_capture") or {}
    display_region_enabled = bool(display_region_collector.get("available_in_studio"))
    active_window_collector = collector_by_id.get("active_window_capture") or {}
    active_window_enabled = bool(active_window_collector.get("available_in_studio"))
    clipboard_collector = collector_by_id.get("clipboard_text_capture") or {}
    clipboard_collector_enabled = bool(clipboard_collector.get("available_in_studio"))
    ambient_clipboard_collector = collector_by_id.get("ambient_clipboard_monitor") or {}
    ambient_clipboard_enabled = bool(
        ambient_clipboard_collector.get("available_in_studio")
    )
    selected_text_collector = collector_by_id.get("selected_text_capture") or {}
    selected_text_enabled = bool(selected_text_collector.get("available_in_studio"))
    accessibility_tree_collector = collector_by_id.get("accessibility_tree_capture") or {}
    accessibility_tree_enabled = bool(
        accessibility_tree_collector.get("available_in_studio")
    )
    browser_artifact_collector = collector_by_id.get("active_browser_artifact_capture") or {}
    browser_artifact_enabled = bool(browser_artifact_collector.get("available_in_studio"))
    browser_extension_collector = collector_by_id.get("browser_extension_capture") or {}
    browser_extension_enabled = bool(browser_extension_collector.get("available_in_studio"))
    active_browser_collector = collector_by_id.get("active_browser_tab_capture") or {}
    active_browser_enabled = bool(active_browser_collector.get("available_in_studio"))
    chaseos_browser_page_collector = collector_by_id.get("chaseos_browser_page_capture") or {}
    chaseos_browser_page_enabled = bool(chaseos_browser_page_collector.get("available_in_studio"))
    discord_collector = collector_by_id.get("discord_capture") or {}
    discord_collector_enabled = bool(discord_collector.get("available_in_studio"))
    live_discord_collector = collector_by_id.get("live_discord_command_capture") or {}
    live_discord_enabled = bool(live_discord_collector.get("available_in_studio"))
    return [
        {
            "id": "manual_text",
            "label": "Paste or type text",
            "status": "available",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT,
            "action": "select_source_mode",
            "description": "Use explicit operator-supplied text.",
        },
        {
            "id": "capture_palette",
            "label": "Capture palette",
            "status": "available",
            "target_panel": "capture-markdown",
            "source_mode": None,
            "action": "open_capture_palette",
            "description": "Open a compact Capture overlay for the available source actions.",
        },
        {
            "id": "local_text_file",
            "label": "Vault text file",
            "status": "available",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_LOCAL_TEXT_FILE,
            "action": "select_source_mode",
            "description": "Read an explicit text or Markdown file under the selected vault.",
        },
        {
            "id": "saved_html_file",
            "label": "Saved web page file",
            "status": "available",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_SAVED_HTML_FILE,
            "action": "select_source_mode",
            "description": "Read an explicit saved HTML file under the selected vault.",
        },
        {
            "id": "controlled_html_artifact",
            "label": "Controlled browser artifact",
            "status": "available",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_CONTROLLED_HTML_ARTIFACT,
            "action": "select_source_mode",
            "description": "Read a declared browser evidence artifact from allowed vault evidence paths.",
        },
        {
            "id": "active_browser_artifact_capture",
            "label": "Browser artifact capture",
            "status": browser_artifact_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": (
                SOURCE_MODE_CONTROLLED_HTML_ARTIFACT
                if browser_artifact_enabled
                else None
            ),
            "action": (
                "run_browser_artifact_collector"
                if browser_artifact_enabled
                else "open_settings_collectors"
            ),
            "description": browser_artifact_collector.get("description")
            or "Validate an operator-selected ChaseOS browser artifact before Preview or Save.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "chaseos_browser_page_capture",
            "label": "ChaseOS browser page",
            "status": chaseos_browser_page_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": (
                SOURCE_MODE_CONTROLLED_HTML_ARTIFACT
                if chaseos_browser_page_enabled
                else None
            ),
            "action": (
                "run_chaseos_browser_page_collector"
                if chaseos_browser_page_enabled
                else "open_settings_collectors"
            ),
            "description": chaseos_browser_page_collector.get("description")
            or "Capture a declared address through a ChaseOS-owned isolated browser before Preview or Save.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "browser_extension_capture",
            "label": "Browser extension capture",
            "status": browser_extension_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT if browser_extension_enabled else None,
            "action": (
                "run_browser_extension_collector"
                if browser_extension_enabled
                else "open_settings_collectors"
            ),
            "description": browser_extension_collector.get("description")
            or "Import a ChaseOS browser extension capture artifact before Preview or Save.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "screenshot_attachment",
            "label": "Screenshot attachment",
            "status": "available_no_text_extraction",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_SCREENSHOT_ATTACHMENT,
            "action": "select_source_mode",
            "description": "Attach an explicit vault-local screenshot without text extraction.",
        },
        {
            "id": "display_region_capture",
            "label": "Display region capture",
            "status": display_region_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": (
                SOURCE_MODE_SCREENSHOT_TEXT_EXTRACTION
                if display_region_enabled
                else None
            ),
            "action": (
                "run_display_region_collector"
                if display_region_enabled
                else "open_settings_collectors"
            ),
            "description": display_region_collector.get("description")
            or "Drag a rectangle over the display and extract its text through the local image text engine before Preview or Save.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "active_window_capture",
            "label": "Active window capture",
            "status": active_window_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": (
                SOURCE_MODE_SCREENSHOT_TEXT_EXTRACTION
                if active_window_enabled
                else None
            ),
            "action": (
                "run_active_window_collector"
                if active_window_enabled
                else "open_settings_collectors"
            ),
            "description": active_window_collector.get("description")
            or "Capture the current foreground window and extract text through the local image text engine before Preview or Save.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "studio_shortcuts",
            "label": "Capture shortcuts",
            "status": "settings_configurable",
            "target_panel": "settings",
            "action": "open_settings_shortcuts",
            "description": "Configure Studio-window shortcuts in Settings. Capture does not need operating-system-wide hooks for the current release path.",
            "settings_path": capture_hotkeys.get("settings_path"),
        },
        {
            "id": "active_browser_tab_capture",
            "label": "Active ChaseOS browser",
            "status": active_browser_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": (
                SOURCE_MODE_CONTROLLED_HTML_ARTIFACT
                if active_browser_enabled
                else None
            ),
            "action": (
                "run_active_browser_collector"
                if active_browser_enabled
                else "open_settings_collectors"
            ),
            "description": active_browser_collector.get("description")
            or (
                "Capture the current ChaseOS-owned active browser artifact before Preview or Save. "
                "Personal browser profiles, sessions, cookies, and history are not read."
            ),
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "clipboard_text_capture",
            "label": "Clipboard text",
            "status": clipboard_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT if clipboard_collector_enabled else None,
            "action": (
                "run_clipboard_text_collector"
                if clipboard_collector_enabled
                else "open_settings_collectors"
            ),
            "description": clipboard_collector.get("description")
            or "Explicit clipboard text capture must be enabled in Settings before use.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "ambient_clipboard_monitor",
            "label": "Ambient clipboard monitor",
            "status": ambient_clipboard_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT if ambient_clipboard_enabled else None,
            "action": (
                "run_ambient_clipboard_monitor"
                if ambient_clipboard_enabled
                else "open_settings_collectors"
            ),
            "description": ambient_clipboard_collector.get("description")
            or "Privacy-gated ambient clipboard monitoring must be enabled in Settings before use.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "selected_text_capture",
            "label": "Selected text",
            "status": selected_text_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT if selected_text_enabled else None,
            "action": (
                "run_selected_text_collector"
                if selected_text_enabled
                else "open_settings_collectors"
            ),
            "description": selected_text_collector.get("description")
            or "Explicit selected-text capture must be enabled in Settings before use.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "accessibility_tree_capture",
            "label": "Accessibility tree",
            "status": accessibility_tree_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT if accessibility_tree_enabled else None,
            "action": (
                "run_accessibility_tree_collector"
                if accessibility_tree_enabled
                else "open_settings_collectors"
            ),
            "description": accessibility_tree_collector.get("description")
            or "Explicit accessibility tree capture must be enabled in Settings before use.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "screen_capture",
            "label": "Screen capture",
            "status": screen_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "action": (
                "run_screen_capture_collector"
                if screen_collector_enabled
                else "open_settings_collectors"
            ),
            "description": screen_collector.get("description")
            or "Explicit screen capture must be enabled in Settings before use.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "optical_character_recognition",
            "label": "Optical character recognition",
            "status": (
                "available_local_engine"
                if local_ocr_available
                else "available_local_engine_required"
            ),
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_SCREENSHOT_TEXT_EXTRACTION,
            "action": "select_source_mode",
            "description": (
                "Extract text from an explicit vault-local image using the configured local engine."
                if local_ocr_available
                else "Configured in the Capture surface, but this host needs a local engine such as Tesseract."
            ),
            "engine": local_ocr_engine,
        },
        {
            "id": "photo_document_text_extraction",
            "label": "Photo or document text",
            "status": "available_local_extraction",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_PHOTO_DOCUMENT_TEXT_EXTRACTION,
            "action": "select_source_mode",
            "description": (
                "Extract text from explicit vault-local image, PDF, Word document, rich text, text, or Markdown files. Images use the local image text engine; supported documents are parsed locally."
            ),
            "engine": local_ocr_engine,
        },
        {
            "id": "discord_capture",
            "label": "Discord capture",
            "status": discord_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT if discord_collector_enabled else None,
            "action": (
                "run_discord_artifact_collector"
                if discord_collector_enabled
                else "open_settings_collectors"
            ),
            "description": discord_collector.get("description")
            or "Explicit Discord artifact capture must be enabled in Settings before use.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "live_discord_command_capture",
            "label": "Live Discord command",
            "status": live_discord_collector.get("status") or "disabled_in_settings",
            "target_panel": "capture-markdown",
            "source_mode": SOURCE_MODE_MANUAL_TEXT if live_discord_enabled else None,
            "action": (
                "run_live_discord_command_collector"
                if live_discord_enabled
                else "open_settings_collectors"
            ),
            "description": live_discord_collector.get("description")
            or "Import a Discord-origin Agent Bus command before Preview or Save.",
            "settings_path": capture_collectors.get("settings_path"),
        },
        {
            "id": "source_intelligence_core_ingestion",
            "label": "Source Intelligence Core ingestion",
            "status": "downstream_approval_gated",
            "target_panel": "capture-markdown",
            "action": "reviewed_capture_downstream",
            "description": "Available only after a reviewed capture, source-pack write, and exact approval chain.",
        },
        {
            "id": "canonical_promotion",
            "label": "Canonical promotion",
            "status": "downstream_approval_gated",
            "target_panel": "capture-markdown",
            "action": "reviewed_capture_downstream",
            "description": "Available only after reviewed capture ingestion, graph indexing, and exact canonical approval.",
        },
        {
            "id": "agent_dispatch",
            "label": "Agent dispatch",
            "status": "downstream_approval_gated",
            "target_panel": "capture-markdown",
            "action": "reviewed_capture_downstream",
            "description": "Available only through source-pack approval and Agent Bus task readiness controls.",
        },
    ]


def _latest_window_size_matrix_proof(vault: Path) -> dict[str, Any]:
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    if not evidence_root.is_dir():
        return {"verified": False, "relative_path": "", "case_count": 0, "cases": []}
    candidates = sorted(
        evidence_root.glob(_WINDOW_SIZE_MATRIX_PATTERN),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in candidates:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(report, dict):
            continue
        cases = report.get("cases") if isinstance(report.get("cases"), list) else []
        return {
            "verified": bool(report.get("ok")),
            "status": str(report.get("status") or ""),
            "relative_path": str(path.relative_to(vault)).replace("\\", "/"),
            "case_count": len(cases),
            "cases": [
                {
                    "id": str(case.get("id") or ""),
                    "requested": case.get("requested") if isinstance(case.get("requested"), dict) else {},
                    "captured": case.get("captured") if isinstance(case.get("captured"), dict) else {},
                    "ok": bool(case.get("ok")),
                }
                for case in cases
                if isinstance(case, dict)
            ],
        }
    return {"verified": False, "relative_path": "", "case_count": 0, "cases": []}


def _latest_downstream_failure_matrix_proof(vault: Path) -> dict[str, Any]:
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    if not evidence_root.is_dir():
        return {"verified": False, "relative_path": "", "case_count": 0, "cases": []}
    candidates = sorted(
        evidence_root.glob(_DOWNSTREAM_FAILURE_MATRIX_PATTERN),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in candidates:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(report, dict):
            continue
        cases = report.get("cases") if isinstance(report.get("cases"), list) else []
        return {
            "verified": bool(report.get("ok")),
            "status": str(report.get("status") or ""),
            "relative_path": str(path.relative_to(vault)).replace("\\", "/"),
            "case_count": len(cases),
            "cases": [
                {
                    "id": str(case.get("id") or ""),
                    "label": str(case.get("label") or ""),
                    "ok": bool(case.get("ok")),
                    "guard_card_visible": bool(case.get("guard_card_visible")),
                    "forbidden_artifacts_not_written": bool(case.get("forbidden_artifacts_not_written")),
                }
                for case in cases
                if isinstance(case, dict)
            ],
        }
    return {"verified": False, "relative_path": "", "case_count": 0, "cases": []}


def _latest_source_shape_matrix_proof(vault: Path) -> dict[str, Any]:
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    if not evidence_root.is_dir():
        return {"verified": False, "relative_path": "", "case_count": 0, "cases": []}
    candidates = sorted(
        evidence_root.glob(_SOURCE_SHAPE_MATRIX_PATTERN),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in candidates:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(report, dict):
            continue
        cases = report.get("cases") if isinstance(report.get("cases"), list) else []
        summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        return {
            "verified": bool(report.get("ok")),
            "status": str(report.get("status") or ""),
            "relative_path": str(path.relative_to(vault)).replace("\\", "/"),
            "case_count": len(cases),
            "summary": {
                "source_modes_covered": list(summary.get("source_modes_covered") or []),
                "duplicate_save_block_verified": bool(
                    summary.get("duplicate_save_block_verified")
                ),
                "needs_redaction_downstream_block_verified": bool(
                    summary.get("needs_redaction_downstream_block_verified")
                ),
                "secret_like_save_block_verified": bool(
                    summary.get("secret_like_save_block_verified")
                ),
                "scratch_workspace_removed": bool(summary.get("scratch_workspace_removed")),
            },
            "cases": [
                {
                    "id": str(case.get("id") or ""),
                    "label": str(case.get("label") or ""),
                    "source_mode": str(case.get("source_mode") or ""),
                    "ok": bool(case.get("ok")),
                }
                for case in cases
                if isinstance(case, dict)
            ],
        }
    return {"verified": False, "relative_path": "", "case_count": 0, "cases": []}


def _latest_image_to_markdown_live_proof(vault: Path) -> dict[str, Any]:
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    if not evidence_root.is_dir():
        return {"verified": False, "relative_path": "", "saved_markdown": ""}
    candidates = sorted(
        evidence_root.glob(_IMAGE_TO_MARKDOWN_LIVE_PROOF_PATTERN),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in candidates:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(report, dict):
            continue
        verification = report.get("verification") if isinstance(report.get("verification"), dict) else {}
        artifacts = (
            verification.get("artifact_paths")
            if isinstance(verification.get("artifact_paths"), dict)
            else {}
        )
        checks = verification.get("checks") if isinstance(verification.get("checks"), dict) else {}
        return {
            "verified": bool(report.get("ok")),
            "status": str(report.get("status") or ""),
            "relative_path": str(path.relative_to(vault)).replace("\\", "/"),
            "captured_image": str(artifacts.get("captured_image") or ""),
            "saved_markdown": str(artifacts.get("saved_markdown") or ""),
            "preview_contains_text": bool(checks.get("preview_contains_extracted_image_text")),
            "save_contains_text": bool(checks.get("saved_markdown_contains_extracted_image_text")),
        }
    return {"verified": False, "relative_path": "", "saved_markdown": ""}


def _latest_public_signing_handoff(vault: Path) -> dict[str, Any]:
    operator_briefs = vault / "07_LOGS" / "Operator-Briefs"
    paths = sorted(
        operator_briefs.glob("*-capture-markdown-public-signing-handoff.json"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0,
        reverse=True,
    )
    for path in paths:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(report, dict):
            continue
        report = dict(report)
        report.setdefault(
            "markdown_report_path",
            str(
                path.with_suffix(".md")
                .relative_to(vault)
            ).replace("\\", "/"),
        )
        report.setdefault(
            "report_path",
            str(path.relative_to(vault)).replace("\\", "/"),
        )
        report.setdefault("public_certificate_candidates", [])
        report.setdefault("ready_to_attempt_public_signing", False)
        report.setdefault("local_release_ready", False)
        report.setdefault("status", "public_signing_handoff_report_read")
        return report
    return {
        "status": "public_signing_handoff_report_missing",
        "ready_to_attempt_public_signing": False,
        "local_release_ready": False,
        "public_certificate_candidates": [],
        "errors": ["public_signing_handoff_report_missing"],
        "warnings": [],
        "markdown_report_path": "",
        "report_path": "",
    }


def _build_release_readiness_summary(
    *,
    vault: Path,
    capture_source_options: list[dict[str, Any]],
    capture_hotkeys: dict[str, Any],
    capture_collectors: dict[str, Any],
    local_ocr_status: dict[str, Any],
    local_ocr_quality: dict[str, Any],
    external_surface_policy: dict[str, Any],
) -> dict[str, Any]:
    local_ocr_engine = local_ocr_status.get("engine") if isinstance(local_ocr_status.get("engine"), dict) else {}
    local_ocr_available = bool(local_ocr_engine.get("available"))
    shortcut_readiness = capture_hotkeys.get("readiness") if isinstance(capture_hotkeys.get("readiness"), dict) else {}
    global_hotkey_enabled = bool(shortcut_readiness.get("global_hotkey_registration_enabled"))
    global_hotkey_count = int(shortcut_readiness.get("global_hotkey_registered_binding_count") or 0)
    quality_summary = (
        local_ocr_quality.get("summary")
        if isinstance(local_ocr_quality.get("summary"), dict)
        else {}
    )
    collector_summary = (
        capture_collectors.get("summary")
        if isinstance(capture_collectors.get("summary"), dict)
        else {}
    )
    screen_capture_enabled = bool(collector_summary.get("screen_capture_enabled"))
    display_region_capture_enabled = bool(
        collector_summary.get("display_region_capture_enabled")
    )
    active_window_capture_enabled = bool(
        collector_summary.get("active_window_capture_enabled")
    )
    clipboard_capture_enabled = bool(collector_summary.get("clipboard_capture_enabled"))
    ambient_clipboard_enabled = bool(
        collector_summary.get("ambient_clipboard_monitoring_enabled")
    )
    selected_text_capture_enabled = bool(
        collector_summary.get("selected_text_capture_enabled")
    )
    accessibility_tree_capture_enabled = bool(
        collector_summary.get("accessibility_tree_capture_enabled")
    )
    browser_artifact_capture_enabled = bool(
        collector_summary.get("browser_artifact_capture_enabled")
    )
    browser_extension_capture_enabled = bool(
        collector_summary.get("browser_extension_capture_enabled")
    )
    active_chaseos_browser_capture_enabled = bool(
        collector_summary.get("active_chaseos_browser_capture_enabled")
    )
    chaseos_browser_page_capture_enabled = bool(
        collector_summary.get("chaseos_browser_page_capture_enabled")
    )
    discord_artifact_capture_enabled = bool(
        collector_summary.get("discord_artifact_capture_enabled")
    )
    live_discord_enabled = bool(
        collector_summary.get("live_discord_command_capture_enabled")
    )
    quality_verified = bool(quality_summary.get("real_engine_quality_verified"))
    quality_latest = (
        local_ocr_quality.get("latest_report")
        if isinstance(local_ocr_quality.get("latest_report"), dict)
        else {}
    )
    window_size_proof = _latest_window_size_matrix_proof(vault)
    window_size_verified = bool(window_size_proof.get("verified"))
    downstream_failure_proof = _latest_downstream_failure_matrix_proof(vault)
    downstream_failure_verified = bool(downstream_failure_proof.get("verified"))
    source_shape_proof = _latest_source_shape_matrix_proof(vault)
    source_shape_verified = bool(source_shape_proof.get("verified"))
    image_to_markdown_proof = _latest_image_to_markdown_live_proof(vault)
    image_to_markdown_verified = bool(image_to_markdown_proof.get("verified"))
    public_signing_handoff = _latest_public_signing_handoff(vault)
    public_candidate_count = len(public_signing_handoff.get("public_certificate_candidates") or [])
    blocked_source_ids = [
        str(option.get("id"))
        for option in capture_source_options
        if "blocked" in str(option.get("status") or "")
    ]
    approval_gated_source_ids = [
        str(option.get("id"))
        for option in capture_source_options
        if "approval_gated" in str(option.get("status") or "")
    ]
    blocked_reasons = {
        str(item.get("id")): str(item.get("reason") or "")
        for item in external_surface_policy.get("blocked_surfaces", [])
        if isinstance(item, dict)
    }
    groups = [
        {
            "id": "ready_now",
            "label": "Ready now",
            "items": [
                {
                    "id": "core_capture",
                    "label": "Text and vault-file capture",
                    "status": "verified",
                    "detail": (
                        "Preview, raw quarantine save, recent listing, and review-state updates are available "
                        "for pasted text, vault text files, saved web page files, controlled browser artifacts, "
                        "and explicit screenshot attachments."
                    ),
                },
                {
                    "id": "studio_window_shortcuts",
                    "label": "Studio-window shortcuts",
                    "status": "settings_configurable"
                    if shortcut_readiness.get("studio_window_shortcuts_configurable")
                    else "not_configured",
                    "detail": (
                        "Open Capture, focus raw text, Preview, Save, and explicit collector shortcuts are visible "
                        "in Settings. Operating-system-wide hooks are not required for this release path."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_screen_capture_collector",
                    "label": "Explicit screen capture collector",
                    "status": (
                        "available_click_to_capture"
                        if screen_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can collect the current screen after Settings enablement and a direct click. It writes screenshot evidence only; Markdown still requires Preview or Save."
                        if screen_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want a direct screen snapshot source."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_display_region_capture_collector",
                    "label": "Explicit display region capture collector",
                    "status": (
                        "available_drag_select_to_capture"
                        if display_region_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can open a drag-select overlay after Settings enablement and a Capture page click or Studio shortcut. It writes selected-region image evidence only; local image text extraction and Markdown still require Preview or Save."
                        if display_region_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want to drag a rectangle over the display and convert that selected image to Markdown."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_active_window_capture_collector",
                    "label": "Explicit active window capture collector",
                    "status": (
                        "available_active_window_capture"
                        if active_window_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can capture the foreground window rectangle after Settings enablement and a Capture page click or Studio shortcut. It writes active-window image evidence only; local image text extraction and Markdown still require Preview or Save."
                        if active_window_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want Capture to use the current foreground window as an image source."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_clipboard_text_collector",
                    "label": "Explicit clipboard text collector",
                    "status": (
                        "available_click_to_capture"
                        if clipboard_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can read current clipboard text after Settings enablement and a direct click. It fills the raw text field only; Markdown still requires Preview or Save."
                        if clipboard_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want a direct clipboard text source."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "ambient_clipboard_monitor",
                    "label": "Ambient clipboard monitor",
                    "status": (
                        "available_privacy_gated_monitor"
                        if ambient_clipboard_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can poll clipboard text during an explicit monitoring session after Settings opt-in. It keeps a small local buffer only; Markdown still requires Preview or Save."
                        if ambient_clipboard_enabled
                        else "Built but disabled by default. Enable it in Settings only if you accept the privacy risk of clipboard monitoring."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_selected_text_collector",
                    "label": "Explicit selected-text collector",
                    "status": (
                        "available_selected_text_capture"
                        if selected_text_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can copy selected text from the foreground application after Settings enablement and a direct click or configured shortcut. It fills the raw text field only; Markdown still requires Preview or Save."
                        if selected_text_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want Capture to copy currently selected text from another application."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_accessibility_tree_collector",
                    "label": "Explicit accessibility tree collector",
                    "status": (
                        "available_accessibility_tree_capture"
                        if accessibility_tree_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can read the foreground application's accessibility tree text after Settings enablement and a direct click or configured shortcut. It fills the raw text field only; Markdown still requires Preview or Save."
                        if accessibility_tree_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want Capture to read accessible labels and text from the foreground application."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_browser_artifact_collector",
                    "label": "Explicit browser artifact collector",
                    "status": (
                        "available_select_artifact"
                        if browser_artifact_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can validate a ChaseOS-controlled browser artifact after Settings enablement and a direct click. It does not inspect personal tabs, profiles, cookies, sessions, or history."
                        if browser_artifact_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want to import a ChaseOS-owned browser evidence artifact."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "browser_extension_collector",
                    "label": "Browser extension capture collector",
                    "status": (
                        "available_select_extension_artifact"
                        if browser_extension_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can import a ChaseOS browser extension artifact after Settings enablement and a direct click. The extension exports page text into an operator-selected local artifact; Markdown still requires Preview or Save."
                        if browser_extension_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want to import captures exported from the ChaseOS browser extension."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "active_chaseos_browser_collector",
                    "label": "Active ChaseOS browser collector",
                    "status": (
                        "available_click_to_capture"
                        if active_chaseos_browser_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can read the current ChaseOS-owned active browser state or controlled artifact after Settings enablement and a direct click. It does not inspect personal browser profiles, cookies, sessions, or history."
                        if active_chaseos_browser_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want Capture to use the current ChaseOS-owned active browser artifact."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_chaseos_browser_page_collector",
                    "label": "ChaseOS-owned browser page collector",
                    "status": (
                        "available_click_to_capture"
                        if chaseos_browser_page_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can launch an isolated ChaseOS-owned browser for a declared address after Settings enablement and a direct click. It does not inspect personal tabs, profiles, cookies, sessions, or history."
                        if chaseos_browser_page_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want Capture to create a controlled browser artifact from a declared address."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "explicit_discord_artifact_collector",
                    "label": "Explicit Discord artifact collector",
                    "status": (
                        "available_select_artifact"
                        if discord_artifact_capture_enabled
                        else "disabled_in_settings"
                    ),
                    "detail": (
                        "The Capture page can import a ChaseOS-owned Discord artifact after Settings enablement and a direct click. Visible Discord content can also flow through screen capture and image text extraction."
                        if discord_artifact_capture_enabled
                        else "Built but disabled by default. Enable it in Settings when you want to import a ChaseOS-owned Discord records artifact."
                    ),
                    "target_panel": "settings",
                },
                {
                    "id": "local_image_text_adapter",
                    "label": "Local image text extraction adapter",
                    "status": "engine_available" if local_ocr_available else "engine_required",
                    "detail": (
                        "Explicit vault-local images can be converted to Markdown through the configured local "
                        "engine."
                        if local_ocr_available
                        else "The local adapter is built, but this host still needs a local engine such as Tesseract before real image text quality can be verified."
                    ),
                },
            ],
        },
        {
            "id": "release_distribution",
            "label": "Release distribution",
            "items": [
                {
                    "id": "local_release_manifest",
                    "label": "Local release manifest",
                    "status": (
                        "ready"
                        if public_signing_handoff.get("local_release_ready")
                        else "not_ready"
                    ),
                    "detail": (
                        "The local Capture to Markdown package is ready for this machine."
                        if public_signing_handoff.get("local_release_ready")
                        else "The local Capture to Markdown release manifest is not ready."
                    ),
                },
                {
                    "id": "public_certificate_authority_signing",
                    "label": "Public certificate-authority signing",
                    "status": (
                        "ready_to_sign"
                        if public_signing_handoff.get("ready_to_attempt_public_signing")
                        else "certificate_required"
                    ),
                    "detail": (
                        "A public code-signing certificate candidate is available for the public release signing pass."
                        if public_signing_handoff.get("ready_to_attempt_public_signing")
                        else "No public code-signing certificate candidate is installed. Current signing remains local to this Windows user."
                    ),
                },
                {
                    "id": "public_signing_handoff_report",
                    "label": "Public signing handoff",
                    "status": (
                        "written"
                        if (
                            vault
                            / str(public_signing_handoff.get("markdown_report_path") or "")
                        ).is_file()
                        else "available_to_generate"
                    ),
                    "detail": str(public_signing_handoff.get("markdown_report_path") or ""),
                },
            ],
        },
        {
            "id": "approval_gated_downstream",
            "label": "Approval-gated downstream",
            "items": [
                {
                    "id": "source_package_write",
                    "label": "Source package writing",
                    "status": "exact_approval_required",
                    "detail": "Reviewed captures can move into source packages only after exact digest and operator-statement checks.",
                },
                {
                    "id": "source_intelligence_core_ingestion",
                    "label": "Source Intelligence Core ingestion",
                    "status": "approval_gated",
                    "detail": "Research workspace ingestion remains behind the reviewed-capture and source-package approval chain.",
                },
                {
                    "id": "canonical_promotion_and_agent_dispatch",
                    "label": "Canonical promotion and Agent Orchestration Runtime dispatch",
                    "status": "approval_gated",
                    "detail": "Knowledge promotion and Agent Orchestration Runtime dispatch remain governed downstream actions, not automatic Capture actions.",
                },
            ],
        },
        {
            "id": "manual_or_covered_collectors",
            "label": "Manual or covered capture paths",
            "items": [
                {
                    "id": "global_hotkey_capture",
                    "label": "Global shortcut capture",
                    "status": (
                        "operating_system_hotkeys_configured"
                        if global_hotkey_enabled and global_hotkey_count > 0
                        else "settings_toggle_available"
                    ),
                    "detail": (
                        "Settings can register operating-system-wide Windows hotkeys for explicit Capture collectors. Collector Settings toggles are still required before a hotkey can capture anything."
                    ),
                },
                {
                    "id": "live_discord_command_capture",
                    "label": "Live Discord command capture",
                    "status": (
                        "agent_bus_ingress_ready"
                        if live_discord_enabled
                        else "settings_toggle_available"
                    ),
                    "detail": "Import a Discord-origin Agent Bus command into the Capture preview and save path. Studio still does not read Discord tokens, webhooks, raw bindings, or direct Discord events.",
                },
            ],
        },
        {
            "id": "release_proof_open",
            "label": "Release proof still open",
            "items": [
                {
                    "id": "real_image_text_quality",
                    "label": "Real image text engine quality",
                    "status": (
                        "verified"
                        if quality_verified
                        else "fixture_proof_required"
                        if local_ocr_available
                        else "unverified_on_this_host"
                    ),
                    "detail": (
                        "The latest local fixture report verifies no-text, dense-text, low-contrast, table, mixed-language, and common Studio-font screenshot image text extraction."
                        if quality_verified
                        else "A local engine is available, but the no-text, dense-text, low-contrast, table, mixed-language, and common Studio-font screenshot fixture run has not passed yet."
                        if local_ocr_available
                        else "Packaged success and failure paths are verified with fake local commands; real local engine output is still unverified."
                    ),
                    "latest_report": quality_latest.get("relative_path") or "",
                },
                {
                    "id": "live_image_to_markdown_save",
                    "label": "Live image to Markdown save",
                    "status": "verified" if image_to_markdown_verified else "open",
                    "detail": (
                        "Latest controlled proof captured a high-contrast image, extracted its pixel text through the local command path, and saved the resulting Markdown."
                        if image_to_markdown_verified
                        else "A controlled proof still needs to capture an image, extract local image text, and save the resulting Markdown through the quarantine writer."
                    ),
                    "latest_report": image_to_markdown_proof.get("relative_path") or "",
                    "saved_markdown": image_to_markdown_proof.get("saved_markdown") or "",
                },
                {
                    "id": "broader_real_source_matrix",
                    "label": "Broader source-shape matrix",
                    "status": "verified" if source_shape_verified else "open",
                    "detail": (
                        f"Latest controlled source-shape proof passed {source_shape_proof.get('case_count')} cases covering long text, sparse text, tables, code blocks, file-based capture, saved page capture, controlled browser artifacts, rejection paths, and duplicate save blocking."
                        if source_shape_verified
                        else "Long pages, sparse pages, tables, code blocks, file-based capture, saved page capture, controlled browser artifacts, rejection paths, and duplicate save paths still need controlled product-surface proof."
                    ),
                    "latest_report": source_shape_proof.get("relative_path") or "",
                },
                {
                    "id": "packaged_downstream_action_matrix",
                    "label": "Packaged downstream action matrix",
                    "status": "verified" if downstream_failure_verified else "open",
                    "detail": (
                        f"Latest packaged Capture proof rejected {downstream_failure_proof.get('case_count')} governed downstream request paths after source-package write."
                        if downstream_failure_verified
                        else "Source package result cards and downstream governed failure states still need proof."
                    ),
                    "latest_report": downstream_failure_proof.get("relative_path") or "",
                },
                {
                    "id": "packaged_window_size_matrix",
                    "label": "Packaged window-size matrix",
                    "status": "verified" if window_size_verified else "open",
                    "detail": (
                        f"Latest packaged Capture proof passed across {window_size_proof.get('case_count')} controlled window sizes."
                        if window_size_verified
                        else "Compact and wide packaged Capture window sizes still need proof."
                    ),
                    "latest_report": window_size_proof.get("relative_path") or "",
                },
            ],
        },
    ]
    release_proof_open_count = len(
        [
            item
            for group in groups
            if group["id"] == "release_proof_open"
            for item in group["items"]
            if item.get("status") != "verified"
        ]
    )
    return {
        "status": "release_ready_explicit_capture_paths_verified",
        "label": "Capture release readiness",
        "summary": {
            "core_capture_verified": True,
            "settings_shortcuts_visible": bool(shortcut_readiness.get("settings_page_visible")),
            "settings_collector_shortcuts_visible": bool(
                shortcut_readiness.get("studio_window_collector_shortcuts_configurable")
            ),
            "local_image_text_adapter_ready": True,
            "local_image_text_engine_available": local_ocr_available,
            "local_image_text_real_engine_quality_verified": quality_verified,
            "photo_document_text_extraction_ready": True,
            "photo_document_text_supported_extensions": [
                ".docx",
                ".jpg",
                ".jpeg",
                ".markdown",
                ".md",
                ".pdf",
                ".png",
                ".rtf",
                ".txt",
                ".webp",
            ],
            "packaged_window_size_matrix_verified": window_size_verified,
            "packaged_window_size_matrix_report": window_size_proof.get("relative_path") or "",
            "packaged_downstream_failure_state_matrix_verified": downstream_failure_verified,
            "packaged_downstream_failure_state_matrix_report": downstream_failure_proof.get("relative_path") or "",
            "image_to_markdown_live_proof_verified": image_to_markdown_verified,
            "image_to_markdown_live_proof_report": image_to_markdown_proof.get("relative_path") or "",
            "image_to_markdown_live_proof_saved_markdown": image_to_markdown_proof.get("saved_markdown") or "",
            "capture_source_shape_matrix_verified": source_shape_verified,
            "capture_source_shape_matrix_report": source_shape_proof.get("relative_path") or "",
            "public_signing_handoff_status": public_signing_handoff.get("status", ""),
            "public_signing_ready_to_attempt": bool(
                public_signing_handoff.get("ready_to_attempt_public_signing")
            ),
            "public_signing_certificate_candidate_count": public_candidate_count,
            "public_signing_handoff_report": public_signing_handoff.get(
                "markdown_report_path", ""
            ),
            "screen_capture_collector_built": True,
            "screen_capture_collector_enabled": screen_capture_enabled,
            "display_region_capture_collector_built": True,
            "display_region_capture_collector_enabled": display_region_capture_enabled,
            "active_window_capture_collector_built": True,
            "active_window_capture_collector_enabled": active_window_capture_enabled,
            "clipboard_capture_collector_built": True,
            "clipboard_capture_collector_enabled": clipboard_capture_enabled,
            "selected_text_capture_collector_built": True,
            "selected_text_capture_collector_enabled": selected_text_capture_enabled,
            "accessibility_tree_capture_collector_built": True,
            "accessibility_tree_capture_collector_enabled": accessibility_tree_capture_enabled,
            "browser_artifact_capture_collector_built": True,
            "browser_artifact_capture_collector_enabled": browser_artifact_capture_enabled,
            "browser_extension_capture_collector_built": True,
            "browser_extension_capture_collector_enabled": browser_extension_capture_enabled,
            "active_chaseos_browser_capture_collector_built": True,
            "active_chaseos_browser_capture_collector_enabled": active_chaseos_browser_capture_enabled,
            "chaseos_browser_page_capture_collector_built": True,
            "chaseos_browser_page_capture_collector_enabled": chaseos_browser_page_capture_enabled,
            "discord_artifact_capture_collector_built": True,
            "discord_artifact_capture_collector_enabled": discord_artifact_capture_enabled,
            "global_hotkey_registration_enabled": global_hotkey_enabled,
            "global_hotkey_registered_binding_count": global_hotkey_count,
            "blocked_collector_count": 0,
            "manual_or_covered_collector_count": 2,
            "approval_gated_downstream_count": len(approval_gated_source_ids),
            "release_proof_open_count": release_proof_open_count,
        },
        "groups": groups,
        "authority": {
            "read_only_status_surface": True,
            "writes_files": False,
            "starts_collectors": False,
            "registers_global_hotkeys": bool(
                (capture_hotkeys.get("authority") or {}).get("registers_global_hotkeys")
            ),
            "calls_providers": False,
        },
        "next_recommended_pass": "capture-markdown-operator-facing-final-proof",
    }


_AUTHORITY = {
    "read_vault_quarantine": True,
    "raw_quarantine_write_on_save": True,
    "phase8_sidecar_write_on_save": True,
    "visual_capture_packet_json_write_on_save": True,
    "operator_review_sidecar_write_allowed": True,
    "operator_review_packet_write_allowed": True,
    "operator_review_content_write_allowed": False,
    "canonical_mutation_allowed": False,
    "graph_index_mutation_allowed": False,
    "provider_call_allowed": False,
    "external_send_allowed": False,
    "aor_queue_allowed": False,
    "sic_ingestion_allowed": False,
    "ambient_filesystem_browse_allowed": False,
    "source_file_reads_limited_to_vault": True,
    "controlled_browser_artifact_reads_confined": True,
    "controlled_browser_artifact_collector_allowed_with_settings_file_and_click": True,
    "controlled_browser_artifact_collector_writes_no_markdown_on_click": True,
    "controlled_browser_artifact_markdown_save_uses_existing_quarantine_flow": True,
    "browser_extension_capture_collector_allowed_with_settings_file_and_click": True,
    "browser_extension_capture_writes_no_markdown_on_click": True,
    "browser_extension_capture_markdown_save_uses_existing_quarantine_flow": True,
    "active_chaseos_browser_collector_allowed_with_settings_and_click": True,
    "active_chaseos_browser_collector_reads_chaseos_state_only": True,
    "active_chaseos_browser_collector_writes_no_markdown_on_click": True,
    "active_chaseos_browser_markdown_save_uses_existing_quarantine_flow": True,
    "chaseos_owned_browser_page_collector_allowed_with_settings_url_and_click": True,
    "chaseos_owned_browser_page_collector_writes_no_markdown_on_click": True,
    "chaseos_owned_browser_page_markdown_save_uses_existing_quarantine_flow": True,
    "personal_active_browser_tab_capture_allowed": False,
    "controlled_discord_artifact_collector_allowed_with_settings_file_and_click": True,
    "controlled_discord_artifact_collector_writes_no_markdown_on_click": True,
    "controlled_discord_artifact_markdown_save_uses_existing_quarantine_flow": True,
    "live_discord_command_collector_allowed_with_settings_and_click": True,
    "live_discord_command_collector_reads_agent_bus_only": True,
    "live_discord_command_collector_writes_no_markdown_on_click": True,
    "live_discord_command_markdown_save_uses_existing_quarantine_flow": True,
    "discord_api_call_allowed": False,
    "discord_event_listener_allowed": False,
    "discord_token_read_allowed": False,
    "discord_webhook_read_allowed": False,
    "browser_profile_access_allowed": False,
    "browser_history_allowed": False,
    "browser_forms_or_downloads_allowed": False,
    "explicit_screen_capture_collector_allowed_with_settings_and_click": True,
    "explicit_screen_capture_writes_evidence_only": True,
    "explicit_screen_capture_markdown_save_uses_existing_quarantine_flow": True,
    "explicit_clipboard_text_collector_allowed_with_settings_and_click": True,
    "explicit_clipboard_text_writes_no_markdown_on_click": True,
    "explicit_clipboard_text_markdown_save_uses_existing_quarantine_flow": True,
    "ambient_clipboard_monitor_allowed_with_settings_and_operator_start": True,
    "ambient_clipboard_monitor_writes_state_ring_buffer_only": True,
    "ambient_clipboard_monitor_writes_no_markdown_on_poll": True,
    "ambient_clipboard_monitor_clear_requires_exact_confirmation": True,
    "explicit_selected_text_collector_allowed_with_settings_and_click": True,
    "explicit_selected_text_uses_temporary_clipboard_copy": True,
    "explicit_selected_text_writes_no_markdown_on_click": True,
    "explicit_selected_text_markdown_save_uses_existing_quarantine_flow": True,
    "explicit_accessibility_tree_collector_allowed_with_settings_and_click": True,
    "explicit_accessibility_tree_writes_no_markdown_on_click": True,
    "explicit_accessibility_tree_markdown_save_uses_existing_quarantine_flow": True,
    "screenshot_attachment_import_allowed": True,
    "screenshot_attachment_retention_policy_ready": True,
    "screenshot_attachment_cleanup_requires_operator_decision": True,
    "screenshot_attachment_runtime_delete_allowed": False,
    "attachment_disposition_policy_ready": True,
    "attachment_disposition_metadata_write_allowed": True,
    "attachment_disposition_delete_request_metadata_allowed": True,
    "attachment_disposition_runtime_delete_allowed": False,
    "attachment_disposition_studio_delete_controls_allowed": True,
    "attachment_cleanup_executor_available": True,
    "attachment_cleanup_requires_exact_operator_confirmation": True,
    "reviewed_capture_downstream_gate_ready": True,
    "reviewed_capture_downstream_gate_read_only": True,
    "reviewed_capture_source_pack_approval_preview_ready": True,
    "reviewed_capture_source_pack_approval_preview_read_only": True,
    "reviewed_capture_source_pack_approval_preview_write_allowed": False,
    "reviewed_capture_source_pack_approval_artifact_write_allowed": False,
    "reviewed_capture_source_pack_write_executor_ready": True,
    "reviewed_capture_source_pack_write_requires_exact_approval": True,
    "reviewed_capture_source_pack_write_create_only": True,
    "reviewed_capture_source_pack_write_allowed": True,
    "reviewed_capture_source_pack_rewrite_allowed": False,
    "reviewed_capture_source_pack_aor_dispatch_readiness_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_readiness_read_only": True,
    "reviewed_capture_source_pack_aor_dispatch_readiness_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_packet_preview_ready_after_write": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_design_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_design_read_only": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_design_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_request_writer_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_request_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_request_create_only": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_request_requires_exact_digest": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_request_write_allowed": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_artifact_write_allowed": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_read_only": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_decision_create_only": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_decision_requires_exact_digest": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_decision_write_allowed": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_create_only": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_requires_exact_digest": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_marker_create_only": True,
    "reviewed_capture_source_pack_aor_dispatch_approval_consumption_write_allowed": True,
    "reviewed_capture_aor_dispatch_approval_consumption_allowed": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_create_only": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_requires_exact_digest": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_allowed": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_read_only": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_requires_exact_digest": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_allowed": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_read_only": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_ui_ready": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_requires_exact_digest": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_marker_create_only": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_call_allowed": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_call_blocked_without_exact_executor_approval": True,
    "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_execute_allowed": False,
    "reviewed_capture_aor_dispatch_executor_ready": False,
    "reviewed_capture_aor_dispatch_allowed": False,
    "reviewed_capture_sic_ingestion_allowed": False,
    "reviewed_capture_graph_or_canonical_promotion_allowed": False,
    "screen_pixel_capture_allowed": False,
    "active_window_capture_allowed": False,
    "live_screenshot_capture_allowed": False,
    "ocr_allowed": True,
    "local_optical_character_recognition_allowed_with_explicit_image": True,
    "cloud_ocr_allowed": False,
    "cloud_optical_character_recognition_allowed": False,
    "studio_window_capture_collector_shortcuts_allowed": True,
    "global_hotkey_capture_allowed": True,
    "overlay_capture_allowed": True,
    "capture_palette_allowed": True,
    "ambient_clipboard_capture_allowed": True,
    "discord_command_capture_allowed": True,
    "external_control_plane_capture_allowed": False,
    "active_browser_tab_capture_allowed": False,
    "accessibility_tree_capture_allowed": True,
}


def build_capture_to_markdown_panel(
    vault_root: str | Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model for Capture to Markdown."""

    vault = Path(vault_root).resolve()
    recent_captures = list_recent_visual_captures(vault, limit=recent_limit)
    profiles = [profile.to_dict() for profile in CAPTURE_PROFILES.values()]

    external_surface_policy = build_external_surface_deferral_policy()
    capture_hotkeys = build_capture_hotkey_settings_model(vault)
    capture_collectors = build_capture_collector_settings_model(vault)
    capture_image_text_settings = build_capture_local_image_text_settings_model(vault)
    local_ocr_status = (
        capture_image_text_settings.get("local_optical_character_recognition")
        if isinstance(capture_image_text_settings.get("local_optical_character_recognition"), dict)
        else build_local_ocr_status_model()
    )
    capture_source_options = _build_capture_source_options(
        external_surface_policy,
        capture_hotkeys,
        capture_collectors,
        local_ocr_status,
    )
    release_readiness = _build_release_readiness_summary(
        vault=vault,
        capture_source_options=capture_source_options,
        capture_hotkeys=capture_hotkeys,
        capture_collectors=capture_collectors,
        local_ocr_status=local_ocr_status,
        local_ocr_quality=(
            capture_image_text_settings.get("quality_fixture_proof")
            if isinstance(capture_image_text_settings.get("quality_fixture_proof"), dict)
            else {}
        ),
        external_surface_policy=external_surface_policy,
    )
    review_state_policy = build_operator_review_state_policy()
    attachment_disposition_policy = build_attachment_disposition_policy(None)
    downstream_gate_policy = build_visual_capture_downstream_gate_policy()
    source_pack_approval_preview_policy = build_visual_capture_source_pack_approval_preview_policy()
    source_pack_write_executor_policy = build_visual_capture_source_pack_write_executor_policy()
    source_pack_aor_dispatch_readiness_policy = (
        build_visual_capture_source_pack_aor_dispatch_readiness_policy()
    )
    source_pack_aor_dispatch_approval_design_policy = (
        build_visual_capture_source_pack_aor_dispatch_approval_design_policy()
    )
    source_pack_aor_dispatch_approval_request_writer_policy = (
        build_visual_capture_source_pack_aor_dispatch_approval_request_writer_policy()
    )
    source_pack_aor_dispatch_approval_consumption_readiness_policy = (
        build_visual_capture_source_pack_aor_dispatch_approval_consumption_readiness_policy()
    )
    source_pack_aor_dispatch_approval_decision_writer_policy = (
        build_visual_capture_source_pack_aor_dispatch_approval_decision_writer_policy()
    )
    source_pack_aor_dispatch_approval_consumption_executor_policy = (
        build_visual_capture_source_pack_aor_dispatch_approval_consumption_executor_policy()
    )
    source_pack_aor_dispatch_agent_bus_task_writer_policy = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_task_writer_policy()
    )
    source_pack_aor_dispatch_agent_bus_task_claim_readiness_policy = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_policy()
    )
    source_pack_aor_dispatch_agent_bus_task_claim_executor_policy = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_policy()
    )
    source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_policy = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_policy()
    )
    source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_policy = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_policy()
    )

    summary = {
        "profile_count": len(profiles),
        "source_mode_count": len(_SOURCE_MODES),
        "capture_source_option_count": len(capture_source_options),
        "capture_source_available_count": len(
            [item for item in capture_source_options if str(item.get("status")).startswith("available")]
        ),
        "capture_source_blocked_count": len(
            [item for item in capture_source_options if "blocked" in str(item.get("status"))]
        ),
        "capture_shortcut_settings_visible": bool(
            (capture_hotkeys.get("readiness") or {}).get("settings_page_visible")
        ),
        "capture_screen_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get("screen_capture_collector_built")
        ),
        "capture_screen_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("screen_capture_enabled")
        ),
        "capture_display_region_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get(
                "display_region_capture_collector_built"
            )
        ),
        "capture_display_region_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("display_region_capture_enabled")
        ),
        "capture_active_window_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get(
                "active_window_capture_collector_built"
            )
        ),
        "capture_active_window_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("active_window_capture_enabled")
        ),
        "capture_clipboard_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get("clipboard_capture_collector_built")
        ),
        "capture_clipboard_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("clipboard_capture_enabled")
        ),
        "capture_ambient_clipboard_monitor_built": bool(
            (capture_collectors.get("readiness") or {}).get("ambient_clipboard_monitor_built")
        ),
        "capture_ambient_clipboard_monitor_enabled": bool(
            (capture_collectors.get("readiness") or {}).get(
                "ambient_clipboard_monitoring_enabled"
            )
        ),
        "capture_accessibility_tree_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get(
                "accessibility_tree_capture_collector_built"
            )
        ),
        "capture_accessibility_tree_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get(
                "accessibility_tree_capture_enabled"
            )
        ),
        "capture_browser_artifact_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get("browser_artifact_capture_collector_built")
        ),
        "capture_browser_artifact_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("browser_artifact_capture_enabled")
        ),
        "capture_browser_extension_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get(
                "browser_extension_capture_collector_built"
            )
        ),
        "capture_browser_extension_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get(
                "browser_extension_capture_enabled"
            )
        ),
        "capture_chaseos_browser_page_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get("chaseos_browser_page_capture_collector_built")
        ),
        "capture_chaseos_browser_page_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("chaseos_browser_page_capture_enabled")
        ),
        "capture_discord_artifact_collector_built": bool(
            (capture_collectors.get("readiness") or {}).get("discord_artifact_capture_collector_built")
        ),
        "capture_discord_artifact_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("discord_artifact_capture_enabled")
        ),
        "recent_capture_count": len(recent_captures),
        "preview_write_free": True,
        "save_routes_through_phase8_quarantine": True,
        "operator_review_state_machine_ready": True,
        "operator_review_studio_clickthrough_ready": True,
        "attachment_disposition_policy_ready": True,
        "local_optical_character_recognition_adapter_ready": True,
        "local_optical_character_recognition_engine_available": bool(
            (local_ocr_status.get("engine") or {}).get("available")
            if isinstance(local_ocr_status.get("engine"), dict)
            else False
        ),
        "blocked_external_surface_count": int(
            external_surface_policy.get("blocked_surface_count") or 0
        ),
        "reviewed_capture_downstream_gate_ready": True,
        "reviewed_capture_source_pack_approval_preview_ready": True,
        "reviewed_capture_source_pack_write_executor_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_design_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_request_writer_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_ready": True,
        "capture_release_readiness_surface_visible": True,
        "capture_release_readiness_open_count": release_readiness["summary"]["release_proof_open_count"],
        "local_optical_character_recognition_real_engine_quality_verified": bool(
            release_readiness["summary"].get("local_image_text_real_engine_quality_verified")
        ),
    }

    readiness = {
        "capture_to_markdown_panel_mounted": True,
        "profile_selector_ready": True,
        "source_selector_ready": True,
        "preview_api_ready": True,
        "save_api_ready": True,
        "phase8_writer_integration_ready": True,
        "recent_capture_listing_ready": True,
        "source_file_reads_limited_to_vault": True,
        "controlled_browser_artifact_extractor_ready": True,
        "controlled_browser_artifact_collector_settings_visible": True,
        "controlled_browser_artifact_collector_ready": True,
        "controlled_browser_artifact_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("browser_artifact_capture_enabled")
        ),
        "controlled_browser_artifact_collector_requires_operator_click": True,
        "controlled_browser_artifact_collector_requires_operator_selected_file": True,
        "controlled_browser_artifact_collector_requires_declared_url": True,
        "controlled_browser_artifact_collector_writes_no_markdown_on_click": True,
        "controlled_browser_declared_url_required": True,
        "browser_extension_capture_collector_settings_visible": True,
        "browser_extension_capture_collector_ready": True,
        "browser_extension_capture_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get(
                "browser_extension_capture_enabled"
            )
        ),
        "browser_extension_capture_requires_operator_click": True,
        "browser_extension_capture_requires_operator_selected_file": True,
        "browser_extension_capture_writes_no_markdown_on_click": True,
        "browser_extension_capture_reads_personal_browser_profile": False,
        "chaseos_browser_page_collector_settings_visible": True,
        "chaseos_browser_page_collector_ready": True,
        "chaseos_browser_page_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("chaseos_browser_page_capture_enabled")
        ),
        "chaseos_browser_page_collector_requires_operator_click": True,
        "chaseos_browser_page_collector_requires_declared_url": True,
        "chaseos_browser_page_collector_writes_no_markdown_on_click": True,
        "chaseos_browser_page_collector_reads_personal_browser": False,
        "controlled_discord_artifact_collector_settings_visible": True,
        "controlled_discord_artifact_collector_ready": True,
        "controlled_discord_artifact_collector_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("discord_artifact_capture_enabled")
        ),
        "controlled_discord_artifact_collector_requires_operator_click": True,
        "controlled_discord_artifact_collector_requires_operator_selected_file": True,
        "controlled_discord_artifact_collector_requires_declared_source": True,
        "controlled_discord_artifact_collector_writes_no_markdown_on_click": True,
        "controlled_discord_artifact_collector_calls_discord_api": False,
        "screenshot_attachment_import_ready": True,
        "screenshot_attachment_quarantine_copy_ready": True,
        "screenshot_attachment_retention_policy_ready": True,
        "screenshot_attachment_cleanup_requires_operator_decision": True,
        "screenshot_attachment_runtime_delete_blocked": True,
        "screenshot_attachment_ocr_disabled": True,
        "screenshot_text_extraction_ready": True,
        "photo_document_text_extraction_ready": True,
        "photo_document_text_extraction_cloud_blocked": True,
        "local_optical_character_recognition_adapter_ready": True,
        "local_optical_character_recognition_engine_available": bool(
            (local_ocr_status.get("engine") or {}).get("available")
            if isinstance(local_ocr_status.get("engine"), dict)
            else False
        ),
        "cloud_ocr_blocked": True,
        "cloud_optical_character_recognition_blocked": True,
        "external_surface_deferral_policy_ready": True,
        "external_capture_surfaces_deferred": True,
        "hotkey_capture_blocked": True,
        "studio_capture_shortcuts_settings_visible": True,
        "studio_capture_shortcuts_configurable": True,
        "studio_capture_collector_shortcuts_configurable": bool(
            (capture_hotkeys.get("readiness") or {}).get(
                "studio_window_collector_shortcuts_configurable"
            )
        ),
        "capture_palette_overlay_ready": True,
        "explicit_screen_capture_settings_visible": True,
        "explicit_screen_capture_collector_ready": True,
        "explicit_screen_capture_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("screen_capture_enabled")
        ),
        "explicit_screen_capture_requires_operator_click": True,
        "screen_capture_markdown_save_uses_existing_quarantine_flow": True,
        "explicit_display_region_capture_settings_visible": True,
        "explicit_display_region_capture_collector_ready": True,
        "explicit_display_region_capture_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("display_region_capture_enabled")
        ),
        "explicit_display_region_capture_requires_operator_drag": True,
        "display_region_capture_markdown_save_uses_existing_quarantine_flow": True,
        "explicit_active_window_capture_settings_visible": True,
        "explicit_active_window_capture_collector_ready": True,
        "explicit_active_window_capture_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("active_window_capture_enabled")
        ),
        "explicit_active_window_capture_requires_operator_click": True,
        "active_window_capture_markdown_save_uses_existing_quarantine_flow": True,
        "explicit_clipboard_capture_settings_visible": True,
        "explicit_clipboard_capture_collector_ready": True,
        "explicit_clipboard_capture_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("clipboard_capture_enabled")
        ),
        "explicit_clipboard_capture_requires_operator_click": True,
        "explicit_clipboard_capture_writes_no_markdown_on_click": True,
        "clipboard_capture_markdown_save_uses_existing_quarantine_flow": True,
        "clipboard_capture_reads_only_after_settings_and_click": True,
        "clipboard_capture_reads_on_settings_load": False,
        "clipboard_capture_reads_on_capture_panel_load": False,
        "ambient_clipboard_monitor_settings_visible": True,
        "ambient_clipboard_monitor_ready": True,
        "ambient_clipboard_monitor_enabled": bool(
            (capture_collectors.get("readiness") or {}).get(
                "ambient_clipboard_monitoring_enabled"
            )
        ),
        "ambient_clipboard_monitor_requires_privacy_opt_in": True,
        "ambient_clipboard_monitor_requires_operator_start": True,
        "ambient_clipboard_monitor_reads_on_settings_load": False,
        "ambient_clipboard_monitor_reads_on_capture_panel_load": False,
        "ambient_clipboard_monitor_writes_no_markdown_on_poll": True,
        "ambient_clipboard_monitor_clear_requires_exact_confirmation": True,
        "explicit_selected_text_capture_settings_visible": True,
        "explicit_selected_text_capture_collector_ready": True,
        "explicit_selected_text_capture_enabled": bool(
            (capture_collectors.get("readiness") or {}).get("selected_text_capture_enabled")
        ),
        "explicit_selected_text_capture_requires_operator_click": True,
        "selected_text_capture_uses_temporary_clipboard_copy": True,
        "selected_text_capture_restores_text_clipboard_when_possible": True,
        "selected_text_capture_reads_on_settings_load": False,
        "selected_text_capture_reads_on_capture_panel_load": False,
        "explicit_accessibility_tree_capture_settings_visible": True,
        "explicit_accessibility_tree_capture_collector_ready": True,
        "explicit_accessibility_tree_capture_enabled": bool(
            (capture_collectors.get("readiness") or {}).get(
                "accessibility_tree_capture_enabled"
            )
        ),
        "explicit_accessibility_tree_capture_requires_operator_click": True,
        "accessibility_tree_capture_reads_on_settings_load": False,
        "accessibility_tree_capture_reads_on_capture_panel_load": False,
        "accessibility_tree_capture_writes_no_markdown_on_click": True,
        "accessibility_tree_capture_markdown_save_uses_existing_quarantine_flow": True,
        "global_hotkey_registration_available": True,
        "global_hotkey_registration_enabled": bool(
            (capture_hotkeys.get("readiness") or {}).get("global_hotkey_registration_enabled")
        ),
        "global_hotkey_registration_blocked": False,
        "overlay_capture_blocked": False,
        "display_region_drag_select_overlay_ready": True,
        "capture_palette_overlay_blocked": False,
        "ambient_clipboard_capture_blocked": False,
        "active_window_screenshot_capture_blocked": False,
        "active_window_capture_blocked": False,
        "screen_pixel_capture_blocked": True,
        "live_screenshot_capture_blocked": True,
        "discord_capture_commands_blocked": False,
        "external_control_plane_capture_blocked": True,
        "external_browser_tab_capture_blocked": True,
        "accessibility_tree_capture_blocked": False,
        "browser_history_session_profile_access_blocked": True,
        "browser_forms_downloads_blocked": True,
        "operator_review_state_machine_ready": True,
        "operator_review_cli_ready": True,
        "operator_review_api_ready": True,
        "operator_review_studio_clickthrough_ready": True,
        "attachment_disposition_policy_ready": True,
        "attachment_disposition_metadata_only": False,
        "attachment_disposition_runtime_delete_blocked": True,
        "attachment_disposition_studio_delete_controls_ready": True,
        "attachment_cleanup_executor_available": True,
        "attachment_cleanup_requires_exact_operator_confirmation": True,
        "reviewed_capture_downstream_gate_ready": True,
        "reviewed_capture_acquisition_preview_gate_ready": True,
        "reviewed_capture_source_pack_approval_preview_ready": True,
        "reviewed_capture_source_pack_approval_preview_ui_ready": True,
        "reviewed_capture_source_pack_approval_preview_read_only": True,
        "reviewed_capture_source_pack_approval_artifact_write_blocked": True,
        "reviewed_capture_source_pack_write_executor_ready": True,
        "reviewed_capture_source_pack_write_executor_ui_ready": True,
        "reviewed_capture_source_pack_write_requires_exact_approval": True,
        "reviewed_capture_source_pack_write_create_only": True,
        "reviewed_capture_source_pack_write_blocked_without_exact_approval": True,
        "reviewed_capture_source_pack_aor_dispatch_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_readiness_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_readiness_read_only": True,
        "reviewed_capture_source_pack_aor_dispatch_packet_preview_ready_after_write": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_design_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_design_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_design_read_only": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_request_writer_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_request_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_request_create_only": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_request_requires_exact_digest": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_request_write_allowed": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_artifact_write_allowed": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_request_overwrite_blocked": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_read_only": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_decision_create_only": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_decision_requires_exact_digest": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_decision_write_allowed": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_blocked": False,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_create_only": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_requires_exact_digest": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_marker_create_only": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_write_allowed": True,
        "reviewed_capture_source_pack_aor_dispatch_approval_consumption_blocked": False,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_create_only": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_requires_exact_digest": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_allowed": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_blocked": False,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_read_only": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_requires_exact_digest": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_allowed": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_execute_blocked": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_read_only": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_ui_ready": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_requires_exact_digest": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_marker_create_only": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_call_allowed": True,
        "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_call_blocked_without_exact_executor_approval": True,
        "capture_release_readiness_surface_ready": True,
        "capture_release_readiness_read_only": True,
        "local_optical_character_recognition_real_engine_quality_verified": bool(
            release_readiness["summary"].get("local_image_text_real_engine_quality_verified")
        ),
        "reviewed_capture_aor_dispatch_executor_blocked": True,
        "reviewed_capture_aor_dispatch_blocked": True,
        "reviewed_capture_sic_ingestion_blocked": True,
        "reviewed_capture_graph_or_canonical_promotion_blocked": True,
        "canonical_writeback_blocked": True,
        "graph_index_write_blocked": True,
        "provider_calls_blocked": True,
        "external_sends_blocked": True,
        "sic_ingestion_blocked": True,
        "aor_queue_blocked": True,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    return {
        "surface": SURFACE_ID,
        "status": "mounted",
        "implementation_status": "COMPLETE / STANDALONE APP MVP",
        "model_version": MODEL_VERSION,
        "vault_root": str(vault),
        "default_profile": PROFILE_RESEARCH_NOTE,
        "profiles": profiles,
        "source_modes": list(_SOURCE_MODES),
        "capture_source_options": capture_source_options,
        "release_readiness": release_readiness,
        "capture_hotkeys": capture_hotkeys,
        "capture_collectors": capture_collectors,
        "local_optical_character_recognition": local_ocr_status,
        "capture_local_image_text": capture_image_text_settings,
        "recent_captures": recent_captures,
        "summary": summary,
        "readiness": readiness,
        "authority": dict(_AUTHORITY)
        | {
            "global_hotkey_capture_allowed": bool(
                (capture_hotkeys.get("readiness") or {}).get("global_hotkey_registration_available")
            )
        },
        "external_surface_policy": external_surface_policy,
        "operator_review_state_policy": review_state_policy,
        "attachment_disposition_policy": attachment_disposition_policy,
        "downstream_gate_policy": downstream_gate_policy,
        "source_pack_approval_preview_policy": source_pack_approval_preview_policy,
        "source_pack_write_executor_policy": source_pack_write_executor_policy,
        "source_pack_aor_dispatch_readiness_policy": source_pack_aor_dispatch_readiness_policy,
        "source_pack_aor_dispatch_approval_design_policy": source_pack_aor_dispatch_approval_design_policy,
        "source_pack_aor_dispatch_approval_request_writer_policy": source_pack_aor_dispatch_approval_request_writer_policy,
        "source_pack_aor_dispatch_approval_consumption_readiness_policy": source_pack_aor_dispatch_approval_consumption_readiness_policy,
        "source_pack_aor_dispatch_approval_decision_writer_policy": source_pack_aor_dispatch_approval_decision_writer_policy,
        "source_pack_aor_dispatch_approval_consumption_executor_policy": source_pack_aor_dispatch_approval_consumption_executor_policy,
        "source_pack_aor_dispatch_agent_bus_task_writer_policy": source_pack_aor_dispatch_agent_bus_task_writer_policy,
        "source_pack_aor_dispatch_agent_bus_task_claim_readiness_policy": source_pack_aor_dispatch_agent_bus_task_claim_readiness_policy,
        "source_pack_aor_dispatch_agent_bus_task_claim_executor_policy": source_pack_aor_dispatch_agent_bus_task_claim_executor_policy,
        "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_policy": source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_policy,
        "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_policy": source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_policy,
        "storage_policy": {
            "preview": "no_write",
            "save": "phase8_quarantine_raw_ingestion",
            "content_root": "03_INPUTS/00_QUARANTINE",
            "sidecar": "*.meta.json",
            "visual_capture_packet": "*.visual_capture.json",
            "attachment_copy_root": "03_INPUTS/00_QUARANTINE/<Class>/_attachments/<capture_id>/",
            "attachment_retention": "retain_until_operator_review",
            "attachment_review_status": "pending-review",
            "attachment_cleanup": "quarantine_local_only_after_exact_operator_confirmation",
            "attachment_disposition": "operator_controlled_metadata_and_guarded_cleanup",
            "attachment_delete_confirmation_phrase": ATTACHMENT_DELETE_CONFIRMATION,
            "operator_review_state_machine": "sidecar_packet_only",
            "operator_review_studio_clickthrough": "mounted_sidecar_packet_only",
            "reviewed_capture_downstream_gate": "read_only_gate_readiness",
            "reviewed_capture_source_pack_approval_preview": "read_only_operator_preview",
            "source_pack_write": "exact_approval_guarded_create_only_pack_artifacts",
            "source_pack_aor_dispatch_readiness": "read_only_after_source_pack_write",
            "source_pack_aor_dispatch_approval_design": "read_only_after_aor_dispatch_readiness",
            "source_pack_aor_dispatch_approval_request": "exact_digest_statement_guarded_create_only_pending_approval_request",
            "source_pack_aor_dispatch_approval_consumption_readiness": "read_only_pending_approval_request_validation",
            "source_pack_aor_dispatch_approval_decision": "exact_digest_statement_guarded_create_only_decision_artifact",
            "source_pack_aor_dispatch_approval_consumption": "exact_digest_statement_guarded_create_only_marker_and_consumption_artifact",
            "source_pack_aor_dispatch_agent_bus_task": "exact_digest_statement_guarded_create_only_marker_open_task_and_task_artifact",
            "source_pack_aor_dispatch_agent_bus_task_claim_readiness": "read_only_open_unclaimed_task_claimability_and_route_liveness",
            "source_pack_aor_dispatch_agent_bus_task_claim": "exact_digest_statement_guarded_marker_claim_and_claim_artifact",
            "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness": "read_only_claim_artifact_claimed_task_row_and_aor_dry_run_packet_preview",
            "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run": "exact_digest_statement_guarded_marker_aor_dry_run_and_artifact",
            "source_pack_rewrite": "blocked",
            "aor_dispatch": "blocked",
            "sic_ingestion": "blocked",
            "graph_canonical_promotion": "blocked",
            "runtime_deletion": "blocked",
            "external_capture_surfaces": "deferred_blocked",
            "downstream_promotion": "not_mounted",
        },
    }


def preview_capture_to_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a write-free Capture to Markdown preview."""

    vault = Path(vault_root).resolve()
    packet = _packet_from_payload(vault, payload or {})
    markdown = build_visual_capture_markdown(packet)
    blockers: list[str] = []
    if packet.quality.save_blocked_by_redaction:
        blockers.append("secret_or_credential_indicator_present")
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "preview",
        "status": "preview_only",
        "preview_ready": True,
        "save_allowed": not bool(blockers),
        "write_performed": False,
        "blockers": blockers,
        "packet": packet.to_dict(),
        "markdown": markdown,
        "authority": dict(_AUTHORITY) | packet.authority.to_dict(),
        "recent_captures": list_recent_visual_captures(vault, limit=10),
    }


def save_capture_to_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Save a Capture to Markdown packet through the quarantine writer."""

    vault = Path(vault_root).resolve()
    packet = _packet_from_payload(vault, payload or {})
    result = save_visual_capture(vault_root=vault, packet=packet, write_visual_capture_packet=True)
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "save",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_AUTHORITY),
    }


def review_capture_to_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply a sidecar/packet-only operator review decision."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    decision = _text(request.get("decision"))
    if not decision:
        raise ValueError("decision is required for Capture Markdown review.")
    result = review_visual_capture_artifact(
        vault,
        _capture_review_path(request),
        decision=decision,
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        review_note=_text(request.get("review_note")),
        allow_secret_redaction=bool(request.get("allow_secret_redaction")),
        dry_run=bool(request.get("dry_run")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "review",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_AUTHORITY),
    }


def update_capture_to_markdown_attachment_disposition(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update attachment retention/disposition metadata for one recent capture."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = update_capture_attachment_disposition(
        vault,
        _capture_review_path(request),
        requested_disposition=_text(request.get("requested_disposition")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        review_note=_text(request.get("review_note")),
        dry_run=bool(request.get("dry_run")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "attachment_disposition",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_AUTHORITY),
    }


def cleanup_capture_to_markdown_attachments(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Delete copied quarantine attachments after exact operator confirmation."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = cleanup_capture_attachments(
        vault,
        _capture_review_path(request),
        operator_confirmed=bool(request.get("operator_confirmed")),
        confirmation_phrase=_text(request.get("confirmation_phrase")),
        dry_run=bool(request.get("dry_run")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "attachment_cleanup",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_AUTHORITY),
    }


def preview_capture_to_markdown_source_pack_approval(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview a reviewed-capture source-pack write approval request."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_approval_preview(
        vault,
        _capture_review_path(request),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return _panel_result(vault, result, "source_pack_approval_preview")


def execute_capture_to_markdown_source_pack_write(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write approved source-pack artifacts for a reviewed capture."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = execute_visual_capture_source_pack_write(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        operator_statement=_text(request.get("operator_statement")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        written_by=_text(request.get("written_by") or "studio-operator"),
    )
    return _panel_result(vault, result, "source_pack_write")


def preview_capture_to_markdown_source_pack_aor_dispatch_readiness(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview Agent Orchestration Runtime dispatch readiness for a written source pack."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_readiness(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_readiness")


def preview_capture_to_markdown_source_pack_aor_dispatch_approval_design(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview the future Agent Orchestration Runtime dispatch approval design."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_approval_design(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_approval_design")


def request_capture_to_markdown_source_pack_aor_dispatch_approval(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write or preview a pending Agent Orchestration Runtime dispatch approval request."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_approval_request(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        operator_statement=_text(request.get("operator_statement")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        requested_by=_text(request.get("requested_by") or "studio-operator"),
        write_approval_request=bool(request.get("write_approval_request")),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_approval_request")


def preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate pending Agent Orchestration Runtime approval consumption readiness."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_approval_consumption_readiness(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_approval_consumption_readiness")


def write_capture_to_markdown_source_pack_aor_dispatch_approval_decision(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write or preview a guarded Agent Orchestration Runtime dispatch approval decision."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_approval_decision(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        decision=_text(request.get("decision")),
        expected_approval_decision_digest=_text(request.get("expected_approval_decision_digest")),
        operator_statement=_text(request.get("operator_statement")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        decided_by=_text(request.get("decided_by") or "studio-operator"),
        write_approval_decision=bool(request.get("write_approval_decision")),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_approval_decision")


def consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Consume or preview a guarded Agent Orchestration Runtime dispatch approval decision."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_approval_consumption(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        decision=_text(request.get("decision")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_approval_decision_digest=_text(request.get("expected_approval_decision_digest")),
        expected_approval_consumption_digest=_text(request.get("expected_approval_consumption_digest")),
        operator_statement=_text(request.get("operator_statement")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        consumed_by=_text(request.get("consumed_by") or "studio-operator"),
        write_consumption_marker=bool(request.get("write_consumption_marker")),
        write_approval_consumption=bool(request.get("write_approval_consumption")),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_approval_consumption")


def write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write or preview a guarded local Agent Bus task for source-pack dispatch."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_task(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_approval_decision_digest=_text(request.get("expected_approval_decision_digest")),
        approval_consumption_artifact_path=_text(request.get("approval_consumption_artifact_path")),
        expected_approval_consumption_digest=_text(request.get("expected_approval_consumption_digest")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        operator_statement=_text(request.get("operator_statement")),
        recipient=_text(request.get("recipient") or "OpenClaw"),
        priority=_text(request.get("priority") or "normal"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        written_by=_text(request.get("written_by") or "studio-operator"),
        write_task_marker=bool(request.get("write_task_marker")),
        write_agent_bus_task=bool(request.get("write_agent_bus_task")),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_agent_bus_task")


def preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return read-only claim readiness for a guarded local Agent Bus task."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_approval_decision_digest=_text(request.get("expected_approval_decision_digest")),
        approval_consumption_artifact_path=_text(request.get("approval_consumption_artifact_path")),
        expected_approval_consumption_digest=_text(request.get("expected_approval_consumption_digest")),
        agent_bus_task_artifact_path=_text(request.get("agent_bus_task_artifact_path")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        agent_bus_task_id=_text(request.get("agent_bus_task_id")),
        runtime=_text(request.get("runtime") or "OpenClaw"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_agent_bus_task_claim_readiness")


def claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Claim or preview claiming a guarded local Agent Bus task."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_approval_decision_digest=_text(request.get("expected_approval_decision_digest")),
        approval_consumption_artifact_path=_text(request.get("approval_consumption_artifact_path")),
        expected_approval_consumption_digest=_text(request.get("expected_approval_consumption_digest")),
        agent_bus_task_artifact_path=_text(request.get("agent_bus_task_artifact_path")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        agent_bus_task_id=_text(request.get("agent_bus_task_id")),
        expected_agent_bus_task_claim_digest=_text(request.get("expected_agent_bus_task_claim_digest")),
        operator_statement=_text(request.get("operator_statement")),
        runtime=_text(request.get("runtime") or "OpenClaw"),
        runtime_instance_id=_text(request.get("runtime_instance_id")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        claimed_by=_text(request.get("claimed_by") or "studio-operator"),
        write_claim_marker=bool(request.get("write_claim_marker")),
        claim_agent_bus_task=bool(request.get("claim_agent_bus_task")),
        write_claim_artifact=bool(request.get("write_claim_artifact")),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_agent_bus_task_claim")


def preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return read-only Agent Orchestration Runtime dry-run readiness for a claimed task."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_approval_decision_digest=_text(request.get("expected_approval_decision_digest")),
        approval_consumption_artifact_path=_text(request.get("approval_consumption_artifact_path")),
        expected_approval_consumption_digest=_text(request.get("expected_approval_consumption_digest")),
        agent_bus_task_artifact_path=_text(request.get("agent_bus_task_artifact_path")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        agent_bus_task_id=_text(request.get("agent_bus_task_id")),
        agent_bus_task_claim_artifact_path=_text(request.get("agent_bus_task_claim_artifact_path")),
        expected_agent_bus_task_claim_digest=_text(request.get("expected_agent_bus_task_claim_digest")),
        runtime=_text(request.get("runtime") or "OpenClaw"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness")


def execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run or preview a guarded Agent Orchestration Runtime dry run for a claimed task."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor(
        vault,
        _capture_review_path(request),
        request_digest=_text(request.get("request_digest")),
        expected_approval_request_digest=_text(request.get("expected_approval_request_digest")),
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_approval_decision_digest=_text(request.get("expected_approval_decision_digest")),
        approval_consumption_artifact_path=_text(request.get("approval_consumption_artifact_path")),
        expected_approval_consumption_digest=_text(request.get("expected_approval_consumption_digest")),
        agent_bus_task_artifact_path=_text(request.get("agent_bus_task_artifact_path")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        agent_bus_task_id=_text(request.get("agent_bus_task_id")),
        agent_bus_task_claim_artifact_path=_text(request.get("agent_bus_task_claim_artifact_path")),
        expected_agent_bus_task_claim_digest=_text(request.get("expected_agent_bus_task_claim_digest")),
        expected_aor_dry_run_packet_digest=_text(request.get("expected_aor_dry_run_packet_digest")),
        operator_statement=_text(request.get("operator_statement")),
        runtime=_text(request.get("runtime") or "OpenClaw"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        executed_by=_text(request.get("executed_by") or "studio-operator"),
        write_aor_dry_run_marker=bool(request.get("write_aor_dry_run_marker")),
        run_aor_dry_run=bool(request.get("run_aor_dry_run")),
        write_aor_dry_run_artifact=bool(request.get("write_aor_dry_run_artifact")),
    )
    return _panel_result(vault, result, "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run")


def _panel_result(vault: Path, result: dict[str, Any], action: str) -> dict[str, Any]:
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": action,
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_AUTHORITY),
    }


def _packet_from_payload(vault: Path, payload: dict[str, Any]) -> VisualCapturePacket:
    mode = _text(payload.get("source_mode") or SOURCE_MODE_MANUAL_TEXT)
    profile = _text(payload.get("profile") or PROFILE_RESEARCH_NOTE)
    title = _text(payload.get("title") or "Visual Capture")
    allow_secret_redaction = bool(payload.get("allow_secret_redaction"))
    common = {
        "profile": profile,
        "user_intent": _text(payload.get("user_intent")),
        "structured_notes": _text(payload.get("structured_notes")),
        "generated_summary": _text(payload.get("generated_summary")),
        "generated_interpretation": _text(payload.get("generated_interpretation")),
        "source_url": _text(payload.get("source_url")),
        "source_window_title": _text(payload.get("source_window_title")),
        "source_page_title": _text(payload.get("source_page_title")),
        "input_class": _text(payload.get("input_class")) or None,
        "captured_by": _text(payload.get("captured_by") or "studio-operator"),
        "timezone_name": _text(payload.get("timezone_name") or "Europe/London"),
        "confidence": _text(payload.get("confidence") or "operator_supplied"),
        "allow_secret_redaction": allow_secret_redaction,
    }

    if mode == SOURCE_MODE_MANUAL_TEXT:
        return capture_from_text(
            text=_text(payload.get("raw_text")),
            title=title,
            capture_method="studio_manual_text",
            declared_source=_text(payload.get("declared_source") or "studio_capture_to_markdown_panel"),
            source_app="studio",
            source_platform="visual-capture",
            **common,
        )

    if mode == SOURCE_MODE_LOCAL_TEXT_FILE:
        file_path = _require_vault_local_file(vault, payload.get("file_path"))
        return capture_from_text_file(
            file_path=file_path,
            title=title or None,
            **_without_source_overrides(common),
        )

    if mode == SOURCE_MODE_SAVED_HTML_FILE:
        file_path = _require_vault_local_file(vault, payload.get("file_path"))
        return capture_from_saved_html(
            file_path=file_path,
            title=title or None,
            source_url=_text(payload.get("source_url")) or None,
            **_without_source_overrides(common, "source_url"),
        )

    if mode == SOURCE_MODE_CONTROLLED_HTML_ARTIFACT:
        file_path = _require_vault_local_file(vault, payload.get("file_path"))
        declared_url = _text(payload.get("source_url"))
        if not declared_url:
            raise ValueError("source_url is required for controlled HTML artifact capture.")
        return capture_from_controlled_browser_artifact(
            file_path=file_path,
            vault_root=vault,
            declared_url=declared_url,
            allowed_origin=_text(payload.get("allowed_origin")) or None,
            source_selector=_text(payload.get("controlled_source") or "browser_runtime_artifact"),
            title=title or None,
            **_without_source_overrides(common, "source_url"),
        )

    if mode == SOURCE_MODE_SCREENSHOT_ATTACHMENT:
        file_path = _require_vault_local_file(vault, payload.get("file_path"))
        return capture_from_screenshot_attachment(
            file_path=file_path,
            vault_root=vault,
            title=title or None,
            source_url=_text(payload.get("source_url")) or None,
            **_without_source_overrides(common, "source_url"),
        )

    if mode == SOURCE_MODE_SCREENSHOT_TEXT_EXTRACTION:
        file_path = _require_vault_local_file(vault, payload.get("file_path"))
        image_text_settings = load_capture_local_image_text_settings(vault)
        return capture_from_screenshot_text(
            file_path=file_path,
            vault_root=vault,
            title=title or None,
            source_url=_text(payload.get("source_url")) or None,
            local_ocr_command=(
                _text(payload.get("local_ocr_command"))
                or _text(image_text_settings.get("local_ocr_command"))
                or None
            ),
            local_ocr_timeout_seconds=_positive_int(
                payload.get("local_ocr_timeout_seconds")
                or image_text_settings.get("local_ocr_timeout_seconds"),
                default=20,
            ),
            **_without_source_overrides(common, "source_url"),
        )

    if mode == SOURCE_MODE_PHOTO_DOCUMENT_TEXT_EXTRACTION:
        file_path = _require_vault_local_file(vault, payload.get("file_path"))
        image_text_settings = load_capture_local_image_text_settings(vault)
        return capture_from_photo_or_document_text(
            file_path=file_path,
            vault_root=vault,
            title=title or None,
            source_url=_text(payload.get("source_url")) or None,
            local_ocr_command=(
                _text(payload.get("local_ocr_command"))
                or _text(image_text_settings.get("local_ocr_command"))
                or None
            ),
            local_ocr_timeout_seconds=_positive_int(
                payload.get("local_ocr_timeout_seconds")
                or image_text_settings.get("local_ocr_timeout_seconds"),
                default=20,
            ),
            **_without_source_overrides(common, "source_url"),
        )

    raise ValueError(f"Unsupported capture source_mode '{mode}'.")


def _require_vault_local_file(vault: Path, file_path: Any) -> Path:
    raw_path = _text(file_path)
    if not raw_path:
        raise ValueError("file_path is required for this capture source mode.")
    path = Path(raw_path)
    resolved = path if path.is_absolute() else vault / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError(
            "Studio Capture to Markdown may only read explicit files under the selected vault."
        ) from exc
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"Capture source file not found: {raw_path}")
    return resolved


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _capture_review_path(payload: dict[str, Any]) -> str:
    capture_path = _text(
        payload.get("sidecar_path")
        or payload.get("capture_path")
        or payload.get("content_path")
        or payload.get("visual_capture_packet_path")
    )
    if not capture_path:
        raise ValueError("capture_path, sidecar_path, or visual_capture_packet_path is required.")
    return capture_path


def _without_source_overrides(payload: dict[str, Any], *extra_keys: str) -> dict[str, Any]:
    blocked = {
        "declared_source",
        "input_class",
        "source_app",
        "source_page_title",
        "source_platform",
        *extra_keys,
    }
    return {key: value for key, value in payload.items() if key not in blocked}


def _vault_relative(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _text(value: Any) -> str:
    return str(value or "").strip()


NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass26-source-pack-aor-dispatch-"
    "agent-bus-claimed-task-execution-status-lifecycle"
)

_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 26 status lifecycle wiring."""

    panel = _BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass26_panel_model(panel)


def execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview or run the Pass 26 Agent Bus review-status lifecycle update."""

    from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle import (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        agent_bus_task_artifact_path=_text(request.get("agent_bus_task_artifact_path")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        agent_bus_task_id=_text(request.get("agent_bus_task_id")),
        agent_bus_task_claim_artifact_path=_text(request.get("agent_bus_task_claim_artifact_path")),
        expected_agent_bus_task_claim_digest=_text(request.get("expected_agent_bus_task_claim_digest")),
        aor_dry_run_artifact_path=_text(request.get("aor_dry_run_artifact_path")),
        expected_aor_dry_run_artifact_digest=_text(request.get("expected_aor_dry_run_artifact_digest")),
        operator_statement=_text(request.get("operator_statement")),
        runtime=_text(request.get("runtime") or "OpenClaw"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        executed_by=_text(request.get("executed_by") or "studio-operator"),
        write_status_lifecycle_marker=bool(request.get("write_status_lifecycle_marker")),
        update_agent_bus_task_status=bool(request.get("update_agent_bus_task_status")),
        write_status_lifecycle_artifact=bool(request.get("write_status_lifecycle_artifact")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass26_authority(dict(_AUTHORITY))),
    }


def _augment_pass26_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle import (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_policy,
    )

    panel["next_recommended_pass"] = NEXT_RECOMMENDED_PASS
    panel["source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_policy"] = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ui_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_requires_exact_digest": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_marker_create_only": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_allowed": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_blocked_without_exact_approval": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass26_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle"
    ] = "exact_digest_statement_guarded_marker_review_status_update_and_artifact"

    return panel


def _augment_pass26_authority(authority: dict[str, Any]) -> dict[str, Any]:
    authority.update(
        {
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ui_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_requires_exact_digest": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_marker_create_only": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_allowed": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_blocked_without_exact_approval": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_execute_allowed": False,
            "reviewed_capture_aor_dispatch_executor_ready": False,
            "reviewed_capture_aor_dispatch_allowed": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS27_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass28-source-pack-aor-dispatch-"
    "agent-bus-full-dispatch-executor"
)

_PASS27_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 27 readiness wiring."""

    panel = _PASS27_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass27_panel_model(panel)


def preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the read-only Pass 27 full-dispatch readiness preview."""

    from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness import (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        agent_bus_task_artifact_path=_text(request.get("agent_bus_task_artifact_path")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        agent_bus_task_id=_text(request.get("agent_bus_task_id")),
        agent_bus_task_claim_artifact_path=_text(request.get("agent_bus_task_claim_artifact_path")),
        expected_agent_bus_task_claim_digest=_text(request.get("expected_agent_bus_task_claim_digest")),
        aor_dry_run_artifact_path=_text(request.get("aor_dry_run_artifact_path")),
        expected_aor_dry_run_artifact_digest=_text(request.get("expected_aor_dry_run_artifact_digest")),
        status_lifecycle_artifact_path=_text(request.get("status_lifecycle_artifact_path")),
        expected_status_lifecycle_artifact_digest=_text(request.get("expected_status_lifecycle_artifact_digest")),
        runtime=_text(request.get("runtime") or "OpenClaw"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_aor_dispatch_agent_bus_full_dispatch_readiness",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass27_authority(dict(_AUTHORITY))),
    }


def _augment_pass27_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness import (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_policy,
    )

    panel["next_recommended_pass"] = PASS27_NEXT_RECOMMENDED_PASS
    panel["source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_policy"] = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ui_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_read_only": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_requires_exact_digest": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_future_packet_preview_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ready": False,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_blocked": True,
            "next_recommended_pass": PASS27_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass27_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_aor_dispatch_agent_bus_full_dispatch_readiness"
    ] = "read_only_reviewed_task_status_artifact_and_future_full_dispatch_packet_preview"

    return panel


def _augment_pass27_authority(authority: dict[str, Any]) -> dict[str, Any]:
    authority.update(
        {
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ui_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_read_only": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_requires_exact_digest": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_future_packet_preview_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ready": False,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_allowed": False,
            "reviewed_capture_aor_dispatch_executor_ready": False,
            "reviewed_capture_aor_dispatch_allowed": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS28_NEXT_RECOMMENDED_PASS = "visual-capture-markdown-ingestion-pass29-source-pack-sic-ingestion-readiness"

_PASS28_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 28 full-dispatch executor wiring."""

    panel = _PASS28_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass28_panel_model(panel)


def execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview or run the Pass 28 guarded full-dispatch executor."""

    from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor import (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    result = build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        agent_bus_task_artifact_path=_text(request.get("agent_bus_task_artifact_path")),
        expected_agent_bus_task_digest=_text(request.get("expected_agent_bus_task_digest")),
        agent_bus_task_id=_text(request.get("agent_bus_task_id")),
        agent_bus_task_claim_artifact_path=_text(request.get("agent_bus_task_claim_artifact_path")),
        expected_agent_bus_task_claim_digest=_text(request.get("expected_agent_bus_task_claim_digest")),
        aor_dry_run_artifact_path=_text(request.get("aor_dry_run_artifact_path")),
        expected_aor_dry_run_artifact_digest=_text(request.get("expected_aor_dry_run_artifact_digest")),
        status_lifecycle_artifact_path=_text(request.get("status_lifecycle_artifact_path")),
        expected_status_lifecycle_artifact_digest=_text(request.get("expected_status_lifecycle_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        operator_statement=_text(request.get("operator_statement")),
        runtime=_text(request.get("runtime") or "OpenClaw"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        executed_by=_text(request.get("executed_by") or "studio-operator"),
        write_full_dispatch_marker=bool(request.get("write_full_dispatch_marker")),
        run_full_dispatch=bool(request.get("run_full_dispatch")),
        write_full_dispatch_artifact=bool(request.get("write_full_dispatch_artifact")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_aor_dispatch_agent_bus_full_dispatch",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass28_authority(dict(_AUTHORITY))),
    }


def _augment_pass28_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor import (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_policy,
    )

    panel["next_recommended_pass"] = PASS28_NEXT_RECOMMENDED_PASS
    panel["source_pack_aor_dispatch_agent_bus_full_dispatch_executor_policy"] = (
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ui_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_requires_exact_digest": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_marker_create_only": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_blocked": False,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_source_pack_writeback_allowed": True,
            "reviewed_capture_aor_dispatch_executor_blocked": False,
            "reviewed_capture_aor_dispatch_blocked": False,
            "next_recommended_pass": PASS28_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass28_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_aor_dispatch_agent_bus_full_dispatch_executor"
    ] = "exact_digest_statement_guarded_marker_non_dry_run_aor_source_pack_writeback_and_artifact"

    return panel


def _augment_pass28_authority(authority: dict[str, Any]) -> dict[str, Any]:
    authority.update(
        {
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ui_ready": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_requires_exact_digest": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_marker_create_only": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_allowed": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_source_pack_writeback_allowed": True,
            "reviewed_capture_aor_dispatch_executor_ready": True,
            "reviewed_capture_aor_dispatch_allowed": True,
            "reviewed_capture_aor_dispatch_source_pack_writeback_allowed": True,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_task_execute_allowed": False,
            "reviewed_capture_source_pack_aor_dispatch_agent_bus_status_update_allowed": False,
            "reviewed_capture_runtime_process_start_allowed": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS29_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass30-source-pack-sic-ingestion-approval-design"
)

_PASS29_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 29 Source Intelligence Core readiness wiring."""

    panel = _PASS29_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass29_panel_model(panel)


def preview_capture_to_markdown_source_pack_sic_ingestion_readiness(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the read-only Pass 29 Source Intelligence Core ingestion readiness preview."""

    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_readiness import (
        build_visual_capture_source_pack_sic_ingestion_readiness,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    result = build_visual_capture_source_pack_sic_ingestion_readiness(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        full_dispatch_artifact_path=_text(request.get("full_dispatch_artifact_path")),
        expected_full_dispatch_artifact_digest=_text(request.get("expected_full_dispatch_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_ingestion_readiness",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass29_authority(dict(_AUTHORITY))),
    }


def _augment_pass29_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_readiness import (
        build_visual_capture_source_pack_sic_ingestion_readiness_policy,
    )

    panel["next_recommended_pass"] = PASS29_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_ingestion_readiness_policy"] = (
        build_visual_capture_source_pack_sic_ingestion_readiness_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_ingestion_readiness_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_readiness_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_read_only": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_requires_full_dispatch_artifact": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_future_packet_preview_ready_after_full_dispatch": True,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_blocked": True,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS29_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass29_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_ingestion_readiness"
    ] = "read_only_pass28_source_pack_writeback_and_future_sic_ingestion_packet_preview"
    storage_policy["sic_ingestion"] = "blocked_until_separate_approval_and_executor"

    return panel


def _augment_pass29_authority(authority: dict[str, Any]) -> dict[str, Any]:
    authority.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_readiness_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_read_only": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_requires_full_dispatch_artifact": True,
            "reviewed_capture_source_pack_sic_ingestion_readiness_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_future_packet_preview_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_sic_workspace_write_allowed": False,
            "reviewed_capture_sic_source_package_write_allowed": False,
            "reviewed_capture_sic_workspace_membership_write_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS30_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass31-source-pack-sic-ingestion-approval-request-writer"
)

_PASS30_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 30 approval-design wiring."""

    panel = _PASS30_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass30_panel_model(panel)


def preview_capture_to_markdown_source_pack_sic_ingestion_approval_design(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the read-only Pass 30 Source Intelligence Core approval-design preview."""

    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_design import (
        build_visual_capture_source_pack_sic_ingestion_approval_design,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    result = build_visual_capture_source_pack_sic_ingestion_approval_design(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        full_dispatch_artifact_path=_text(request.get("full_dispatch_artifact_path")),
        expected_full_dispatch_artifact_digest=_text(request.get("expected_full_dispatch_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        expected_sic_ingestion_readiness_packet_digest=_text(
            request.get("expected_sic_ingestion_readiness_packet_digest")
        ),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_ingestion_approval_design",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass30_authority(dict(_AUTHORITY))),
    }


def _augment_pass30_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_design import (
        build_visual_capture_source_pack_sic_ingestion_approval_design_policy,
    )

    panel["next_recommended_pass"] = PASS30_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_ingestion_approval_design_policy"] = (
        build_visual_capture_source_pack_sic_ingestion_approval_design_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_ingestion_approval_design_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_design_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_design_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_design_read_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_design_requires_readiness_packet_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_blocked": True,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS30_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass30_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_ingestion_approval_design"
    ] = "read_only_future_source_intelligence_core_ingestion_approval_packet_preview"
    storage_policy["sic_ingestion"] = "blocked_until_separate_approval_request_decision_consumption_and_executor"

    return panel


def _augment_pass30_authority(authority: dict[str, Any]) -> dict[str, Any]:
    authority.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_design_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_design_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_design_read_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_design_requires_readiness_packet_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_packet_preview_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_sic_workspace_write_allowed": False,
            "reviewed_capture_sic_source_package_write_allowed": False,
            "reviewed_capture_sic_workspace_membership_write_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS31_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass32-source-pack-sic-ingestion-approval-decision-consumption-readiness"
)

_PASS31_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 31 approval-request wiring."""

    panel = _PASS31_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass31_panel_model(panel)


def preview_capture_to_markdown_source_pack_sic_ingestion_approval_request(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return or write the Pass 31 Source Intelligence Core approval request."""

    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_request_writer import (
        build_visual_capture_source_pack_sic_ingestion_approval_request,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    expected_approval_request_digest = _text(
        request.get("expected_sic_ingestion_approval_request_digest")
        or request.get("expected_approval_request_digest")
    )
    result = build_visual_capture_source_pack_sic_ingestion_approval_request(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        full_dispatch_artifact_path=_text(request.get("full_dispatch_artifact_path")),
        expected_full_dispatch_artifact_digest=_text(request.get("expected_full_dispatch_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        expected_sic_ingestion_readiness_packet_digest=_text(
            request.get("expected_sic_ingestion_readiness_packet_digest")
        ),
        expected_sic_ingestion_approval_request_digest=expected_approval_request_digest,
        operator_statement=_text(request.get("operator_statement")),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        requested_by=_text(request.get("requested_by") or "studio-operator"),
        write_approval_request=bool(request.get("write_approval_request")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_ingestion_approval_request",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass31_authority(dict(_AUTHORITY))),
    }


def _augment_pass31_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_request_writer import (
        build_visual_capture_source_pack_sic_ingestion_approval_request_writer_policy,
    )

    panel["next_recommended_pass"] = PASS31_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_ingestion_approval_request_writer_policy"] = (
        build_visual_capture_source_pack_sic_ingestion_approval_request_writer_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_overwrite_blocked": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_blocked": True,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS31_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass31_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_ingestion_approval_request"
    ] = "exact_digest_statement_guarded_create_only_pending_source_intelligence_core_ingestion_approval_request"
    storage_policy[
        "sic_ingestion"
    ] = "blocked_until_separate_approval_decision_consumption_and_executor"

    return panel


def _augment_pass31_authority(authority: dict[str, Any]) -> dict[str, Any]:
    authority.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_artifact_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_request_overwrite_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_sic_workspace_write_allowed": False,
            "reviewed_capture_sic_source_package_write_allowed": False,
            "reviewed_capture_sic_workspace_membership_write_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS32_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass33-source-pack-sic-ingestion-approval-decision-writer"
)

_PASS32_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 32 approval-readiness wiring."""

    panel = _PASS32_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass32_panel_model(panel)


def preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision_consumption_readiness(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the Pass 32 Source Intelligence Core approval decision readiness."""

    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_consumption_readiness import (
        build_visual_capture_source_pack_sic_ingestion_approval_consumption_readiness,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    expected_approval_request_digest = _text(
        request.get("expected_sic_ingestion_approval_request_digest")
        or request.get("expected_approval_request_digest")
    )
    result = build_visual_capture_source_pack_sic_ingestion_approval_consumption_readiness(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        full_dispatch_artifact_path=_text(request.get("full_dispatch_artifact_path")),
        expected_full_dispatch_artifact_digest=_text(request.get("expected_full_dispatch_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        expected_sic_ingestion_readiness_packet_digest=_text(
            request.get("expected_sic_ingestion_readiness_packet_digest")
        ),
        expected_sic_ingestion_approval_request_digest=expected_approval_request_digest,
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_ingestion_approval_decision_consumption_readiness",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass32_authority(dict(_AUTHORITY))),
    }


def _augment_pass32_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_consumption_readiness import (
        build_visual_capture_source_pack_sic_ingestion_approval_consumption_readiness_policy,
    )

    panel["next_recommended_pass"] = PASS32_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_ingestion_approval_consumption_readiness_policy"] = (
        build_visual_capture_source_pack_sic_ingestion_approval_consumption_readiness_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_read_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_blocked": True,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS32_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass32_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_ingestion_approval_decision_consumption_readiness"
    ] = "read_only_pending_source_intelligence_core_ingestion_approval_request_validation"
    storage_policy[
        "sic_ingestion"
    ] = "blocked_until_separate_approval_decision_consumption_and_executor"

    return panel


def _augment_pass32_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass31_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_read_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_write_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_exact_once_marker_write_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_sic_workspace_write_allowed": False,
            "reviewed_capture_sic_source_package_write_allowed": False,
            "reviewed_capture_sic_workspace_membership_write_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS33_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass34-source-pack-sic-ingestion-approval-consumption-executor"
)

_PASS33_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 33 approval-decision wiring."""

    panel = _PASS33_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass33_panel_model(panel)


def preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return or write the Pass 33 Source Intelligence Core approval decision."""

    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_decision_writer import (
        build_visual_capture_source_pack_sic_ingestion_approval_decision,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    expected_approval_request_digest = _text(
        request.get("expected_sic_ingestion_approval_request_digest")
        or request.get("expected_approval_request_digest")
    )
    expected_approval_decision_digest = _text(
        request.get("expected_sic_ingestion_approval_decision_digest")
        or request.get("expected_approval_decision_digest")
    )
    result = build_visual_capture_source_pack_sic_ingestion_approval_decision(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        full_dispatch_artifact_path=_text(request.get("full_dispatch_artifact_path")),
        expected_full_dispatch_artifact_digest=_text(request.get("expected_full_dispatch_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        expected_sic_ingestion_readiness_packet_digest=_text(
            request.get("expected_sic_ingestion_readiness_packet_digest")
        ),
        expected_sic_ingestion_approval_request_digest=expected_approval_request_digest,
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        decision=_text(request.get("decision")),
        expected_sic_ingestion_approval_decision_digest=expected_approval_decision_digest,
        operator_statement=_text(request.get("operator_statement")),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        decided_by=_text(request.get("decided_by") or "studio-operator"),
        write_approval_decision=bool(request.get("write_approval_decision")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_ingestion_approval_decision",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass33_authority(dict(_AUTHORITY))),
    }


def _augment_pass33_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_decision_writer import (
        build_visual_capture_source_pack_sic_ingestion_approval_decision_writer_policy,
    )

    panel["next_recommended_pass"] = PASS33_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_ingestion_approval_decision_writer_policy"] = (
        build_visual_capture_source_pack_sic_ingestion_approval_decision_writer_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_overwrite_blocked": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_ready": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_blocked": True,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS33_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass33_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_ingestion_approval_decision"
    ] = "exact_digest_statement_guarded_create_only_source_intelligence_core_ingestion_approval_decision"
    storage_policy[
        "sic_ingestion"
    ] = "blocked_until_separate_approval_consumption_and_executor"

    return panel


def _augment_pass33_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass32_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_artifact_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_decision_overwrite_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_exact_once_marker_write_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_sic_workspace_write_allowed": False,
            "reviewed_capture_sic_source_package_write_allowed": False,
            "reviewed_capture_sic_workspace_membership_write_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS34_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass35-source-pack-sic-ingestion-executor"
)

_PASS34_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 34 approval-consumption wiring."""

    panel = _PASS34_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass34_panel_model(panel)


def consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview or consume the Pass 34 Source Intelligence Core approval decision."""

    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_consumption_executor import (
        build_visual_capture_source_pack_sic_ingestion_approval_consumption,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    expected_approval_request_digest = _text(
        request.get("expected_sic_ingestion_approval_request_digest")
        or request.get("expected_approval_request_digest")
    )
    expected_approval_decision_digest = _text(
        request.get("expected_sic_ingestion_approval_decision_digest")
        or request.get("expected_approval_decision_digest")
    )
    expected_approval_consumption_digest = _text(
        request.get("expected_sic_ingestion_approval_consumption_digest")
        or request.get("expected_approval_consumption_digest")
    )
    result = build_visual_capture_source_pack_sic_ingestion_approval_consumption(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        full_dispatch_artifact_path=_text(request.get("full_dispatch_artifact_path")),
        expected_full_dispatch_artifact_digest=_text(request.get("expected_full_dispatch_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        expected_sic_ingestion_readiness_packet_digest=_text(
            request.get("expected_sic_ingestion_readiness_packet_digest")
        ),
        expected_sic_ingestion_approval_request_digest=expected_approval_request_digest,
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        decision=_text(request.get("decision")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_sic_ingestion_approval_decision_digest=expected_approval_decision_digest,
        expected_sic_ingestion_approval_consumption_digest=expected_approval_consumption_digest,
        operator_statement=_text(request.get("operator_statement")),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        consumed_by=_text(request.get("consumed_by") or "studio-operator"),
        write_consumption_marker=bool(request.get("write_consumption_marker")),
        write_approval_consumption=bool(request.get("write_approval_consumption")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_ingestion_approval_consumption",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass34_authority(dict(_AUTHORITY))),
    }


def _augment_pass34_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_consumption_executor import (
        build_visual_capture_source_pack_sic_ingestion_approval_consumption_executor_policy,
    )

    panel["next_recommended_pass"] = PASS34_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_ingestion_approval_consumption_executor_policy"] = (
        build_visual_capture_source_pack_sic_ingestion_approval_consumption_executor_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_marker_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_overwrite_blocked": True,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_blocked": True,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS34_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass34_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_ingestion_approval_consumption"
    ] = "exact_digest_statement_guarded_marker_then_create_only_source_intelligence_core_ingestion_approval_consumption"
    storage_policy[
        "sic_ingestion"
    ] = "blocked_until_separate_source_intelligence_core_ingestion_executor"

    return panel


def _augment_pass34_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass33_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_marker_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_approval_consumption_overwrite_allowed": False,
            "reviewed_capture_source_pack_sic_ingestion_approval_exact_once_marker_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": False,
            "reviewed_capture_sic_ingestion_allowed": False,
            "reviewed_capture_sic_workspace_write_allowed": False,
            "reviewed_capture_sic_source_package_write_allowed": False,
            "reviewed_capture_sic_workspace_membership_write_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
        }
    )
    return authority


PASS35_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass36-source-pack-sic-graph-indexing-readiness"
)

_PASS35_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 35 ingestion wiring."""

    panel = _PASS35_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass35_panel_model(panel)


def ingest_capture_to_markdown_source_pack_sic_ingestion(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview or run the Pass 35 guarded Source Intelligence Core ingestion."""

    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_executor import (
        build_visual_capture_source_pack_sic_ingestion,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    capture_path = _capture_review_path(request) if "_capture_review_path" in globals() else _text(
        request.get("sidecar_path")
        or request.get("capture_path")
        or request.get("content_path")
        or request.get("visual_capture_packet_path")
    )
    expected_approval_request_digest = _text(
        request.get("expected_sic_ingestion_approval_request_digest")
        or request.get("expected_approval_request_digest")
    )
    expected_approval_decision_digest = _text(
        request.get("expected_sic_ingestion_approval_decision_digest")
        or request.get("expected_approval_decision_digest")
    )
    expected_approval_consumption_digest = _text(
        request.get("expected_sic_ingestion_approval_consumption_digest")
        or request.get("expected_approval_consumption_digest")
    )
    expected_ingestion_digest = _text(
        request.get("expected_sic_ingestion_digest")
        or request.get("expected_source_intelligence_core_ingestion_digest")
    )
    result = build_visual_capture_source_pack_sic_ingestion(
        vault,
        capture_path,
        request_digest=_text(request.get("request_digest")),
        full_dispatch_artifact_path=_text(request.get("full_dispatch_artifact_path")),
        expected_full_dispatch_artifact_digest=_text(request.get("expected_full_dispatch_artifact_digest")),
        expected_full_dispatch_packet_digest=_text(request.get("expected_full_dispatch_packet_digest")),
        expected_sic_ingestion_readiness_packet_digest=_text(
            request.get("expected_sic_ingestion_readiness_packet_digest")
        ),
        expected_sic_ingestion_approval_request_digest=expected_approval_request_digest,
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        decision=_text(request.get("decision") or "approved"),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_sic_ingestion_approval_decision_digest=expected_approval_decision_digest,
        approval_consumption_artifact_path=_text(request.get("approval_consumption_artifact_path")),
        expected_sic_ingestion_approval_consumption_digest=expected_approval_consumption_digest,
        expected_sic_ingestion_digest=expected_ingestion_digest,
        operator_statement=_text(request.get("operator_statement")),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        ingested_by=_text(request.get("ingested_by") or "studio-operator"),
        source_type=_text(request.get("source_type") or "markdown"),
        user_trust_level=_text(request.get("user_trust_level") or "reviewed"),
        domain=_text(request.get("domain")),
        write_ingestion_marker=bool(request.get("write_ingestion_marker")),
        run_source_intelligence_core_ingestion=bool(
            request.get("run_source_intelligence_core_ingestion")
            or request.get("run_sic_ingestion")
        ),
        write_ingestion_artifact=bool(request.get("write_ingestion_artifact")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_ingestion",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass35_authority(dict(_AUTHORITY))),
    }


def _augment_pass35_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_ingestion_executor import (
        build_visual_capture_source_pack_sic_ingestion_executor_policy,
    )

    panel["next_recommended_pass"] = PASS35_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_ingestion_executor_policy"] = (
        build_visual_capture_source_pack_sic_ingestion_executor_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_ingestion_executor_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_executor_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_marker_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_overwrite_blocked": True,
            "reviewed_capture_sic_ingestion_blocked": False,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS35_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass35_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_ingestion"
    ] = "exact_digest_statement_guarded_marker_then_source_intelligence_core_workspace_source_package_membership_and_artifact"
    storage_policy[
        "sic_ingestion"
    ] = "implemented_for_reviewed_capture_markdown_source_package_only_graph_and_canonical_blocked"

    return panel


def _augment_pass35_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass34_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_sic_ingestion_executor_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_executor_ui_ready": True,
            "reviewed_capture_source_pack_sic_ingestion_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_marker_create_only": True,
            "reviewed_capture_source_pack_sic_ingestion_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_ingestion_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_ingestion_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_write_allowed": True,
            "reviewed_capture_source_pack_sic_ingestion_overwrite_allowed": False,
            "reviewed_capture_sic_ingestion_allowed": True,
            "reviewed_capture_sic_workspace_write_allowed": True,
            "reviewed_capture_sic_source_package_write_allowed": True,
            "reviewed_capture_sic_workspace_membership_write_allowed": True,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
            "reviewed_capture_embedding_or_retrieval_index_write_allowed": False,
        }
    )
    return authority


PASS36_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass37-source-pack-graph-indexing-executor"
)

_PASS36_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 36 graph readiness wiring."""

    panel = _PASS36_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass36_panel_model(panel)


def preview_capture_to_markdown_source_pack_sic_graph_indexing_readiness(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview the Pass 36 Source Intelligence Core graph-indexing readiness packet."""

    from runtime.acquisition.visual_capture_source_pack_sic_graph_indexing_readiness import (
        build_visual_capture_source_pack_sic_graph_indexing_readiness,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_sic_graph_indexing_readiness(
        vault,
        _text(
            request.get("source_intelligence_core_ingestion_artifact_path")
            or request.get("ingestion_artifact_path")
        ),
        expected_sic_ingestion_artifact_digest=_text(
            request.get("expected_sic_ingestion_artifact_digest")
            or request.get("expected_source_intelligence_core_ingestion_artifact_digest")
        ),
        expected_sic_ingestion_digest=_text(
            request.get("expected_sic_ingestion_digest")
            or request.get("expected_source_intelligence_core_ingestion_digest")
        ),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        max_chunk_nodes=int(request.get("max_chunk_nodes") or 5),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_graph_indexing_readiness",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass36_authority(dict(_AUTHORITY))),
    }


def _augment_pass36_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_graph_indexing_readiness import (
        build_visual_capture_source_pack_sic_graph_indexing_readiness_policy,
    )

    panel["next_recommended_pass"] = PASS36_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_graph_indexing_readiness_policy"] = (
        build_visual_capture_source_pack_sic_graph_indexing_readiness_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_graph_indexing_readiness_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_ui_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_read_only": True,
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_graph_indexing_candidate_preview_ready": True,
            "reviewed_capture_graph_or_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS36_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass36_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_graph_indexing_readiness"
    ] = "read_only_source_intelligence_core_ingestion_artifact_to_graph_candidate_preview"
    storage_policy[
        "graph_canonical_promotion"
    ] = "graph_candidate_preview_available_but_graph_mutation_and_canonical_promotion_blocked"

    return panel


def _augment_pass36_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass35_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_ui_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_read_only": True,
            "reviewed_capture_source_pack_sic_graph_indexing_readiness_requires_exact_digest": True,
            "reviewed_capture_graph_candidate_preview_allowed": True,
            "reviewed_capture_graph_index_mutation_allowed": False,
            "reviewed_capture_graph_snapshot_write_allowed": False,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
            "reviewed_capture_canonical_mutation_allowed": False,
        }
    )
    return authority


PASS37_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass38-source-pack-canonical-promotion-readiness"
)

_PASS37_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 37 graph indexing wiring."""

    panel = _PASS37_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass37_panel_model(panel)


def index_capture_to_markdown_source_pack_sic_graph_indexing(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview or run the Pass 37 guarded Source Intelligence Core graph indexing."""

    from runtime.acquisition.visual_capture_source_pack_sic_graph_indexing_executor import (
        build_visual_capture_source_pack_sic_graph_indexing_executor,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_sic_graph_indexing_executor(
        vault,
        _text(
            request.get("source_intelligence_core_ingestion_artifact_path")
            or request.get("ingestion_artifact_path")
        ),
        expected_sic_ingestion_artifact_digest=_text(
            request.get("expected_sic_ingestion_artifact_digest")
            or request.get("expected_source_intelligence_core_ingestion_artifact_digest")
        ),
        expected_sic_ingestion_digest=_text(
            request.get("expected_sic_ingestion_digest")
            or request.get("expected_source_intelligence_core_ingestion_digest")
        ),
        expected_graph_index_preview_packet_digest=_text(
            request.get("expected_graph_index_preview_packet_digest")
            or request.get("expected_sic_graph_index_preview_packet_digest")
        ),
        operator_statement=_text(request.get("operator_statement")),
        target_workspace_id=_text(request.get("target_workspace_id") or "vcmi-reviewed-captures"),
        max_chunk_nodes=int(request.get("max_chunk_nodes") or 5),
        indexed_by=_text(request.get("indexed_by") or "studio-operator"),
        write_graph_indexing_marker=bool(request.get("write_graph_indexing_marker")),
        write_graph_snapshot=bool(request.get("write_graph_snapshot")),
        write_graph_indexing_artifact=bool(request.get("write_graph_indexing_artifact")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_sic_graph_indexing",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass37_authority(dict(_AUTHORITY))),
    }


def _augment_pass37_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_sic_graph_indexing_executor import (
        build_visual_capture_source_pack_sic_graph_indexing_executor_policy,
    )

    panel["next_recommended_pass"] = PASS37_NEXT_RECOMMENDED_PASS
    panel["source_pack_sic_graph_indexing_executor_policy"] = (
        build_visual_capture_source_pack_sic_graph_indexing_executor_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_sic_graph_indexing_executor_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_sic_graph_indexing_executor_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_executor_ui_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_graph_indexing_requires_operator_statement": True,
            "reviewed_capture_source_pack_sic_graph_indexing_marker_create_only": True,
            "reviewed_capture_source_pack_sic_graph_snapshot_write_allowed": True,
            "reviewed_capture_source_pack_sic_graph_store_manifest_write_allowed": True,
            "reviewed_capture_source_pack_sic_graph_current_pointer_update_allowed": True,
            "reviewed_capture_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS37_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass37_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_sic_graph_indexing_executor"
    ] = "exact_digest_statement_gated_graph_snapshot_manifest_current_pointer_write"
    storage_policy[
        "graph_canonical_promotion"
    ] = "graph_snapshot_store_write_available_but_canonical_promotion_still_blocked"

    return panel


def _augment_pass37_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass36_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_sic_graph_indexing_executor_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_executor_ui_ready": True,
            "reviewed_capture_source_pack_sic_graph_indexing_requires_exact_digest": True,
            "reviewed_capture_source_pack_sic_graph_indexing_requires_operator_statement": True,
            "reviewed_capture_graph_indexing_marker_create_only": True,
            "reviewed_capture_graph_index_mutation_allowed": True,
            "reviewed_capture_graph_snapshot_write_allowed": True,
            "reviewed_capture_graph_store_manifest_write_allowed": True,
            "reviewed_capture_graph_current_pointer_update_allowed": True,
            "reviewed_capture_graph_or_canonical_promotion_allowed": False,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_source_intelligence_core_rewrite_allowed": False,
        }
    )
    return authority


PASS38_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass39-source-pack-canonical-promotion-approval-design"
)

_PASS38_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 38 canonical readiness wiring."""

    panel = _PASS38_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass38_panel_model(panel)


def preview_capture_to_markdown_source_pack_canonical_promotion_readiness(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview the Pass 38 canonical-promotion readiness packet."""

    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_readiness import (
        build_visual_capture_source_pack_canonical_promotion_readiness,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_canonical_promotion_readiness(
        vault,
        _text(
            request.get("graph_indexing_artifact_path")
            or request.get("source_graph_indexing_artifact_path")
        ),
        expected_graph_indexing_artifact_digest=_text(
            request.get("expected_graph_indexing_artifact_digest")
        ),
        expected_graph_snapshot_digest=_text(request.get("expected_graph_snapshot_digest")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_canonical_promotion_readiness",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass38_authority(dict(_AUTHORITY))),
    }


def _augment_pass38_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_readiness import (
        build_visual_capture_source_pack_canonical_promotion_readiness_policy,
    )

    panel["next_recommended_pass"] = PASS38_NEXT_RECOMMENDED_PASS
    panel["source_pack_canonical_promotion_readiness_policy"] = (
        build_visual_capture_source_pack_canonical_promotion_readiness_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_canonical_promotion_readiness_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_readiness_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_readiness_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_readiness_read_only": True,
            "reviewed_capture_source_pack_canonical_promotion_requires_exact_graph_artifact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_candidate_preview_ready": True,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS38_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass38_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_canonical_promotion_readiness"
    ] = "read_only_graph_indexing_artifact_to_canonical_promotion_candidate_preview"
    storage_policy[
        "graph_canonical_promotion"
    ] = "canonical_promotion_candidate_preview_available_but_canonical_writes_blocked"

    return panel


def _augment_pass38_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass37_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_readiness_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_readiness_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_readiness_read_only": True,
            "reviewed_capture_source_pack_canonical_promotion_requires_exact_graph_artifact_digest": True,
            "reviewed_capture_canonical_promotion_candidate_preview_allowed": True,
            "reviewed_capture_canonical_promotion_approval_required": True,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_knowledge_promotion_allowed": False,
            "reviewed_capture_canonical_target_file_write_allowed": False,
            "reviewed_capture_source_intelligence_core_rewrite_allowed": False,
            "reviewed_capture_graph_snapshot_write_allowed_after_canonical_readiness": False,
            "reviewed_capture_graph_current_pointer_update_allowed_after_canonical_readiness": False,
        }
    )
    return authority


PASS39_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass40-source-pack-canonical-promotion-approval-request-writer"
)

_PASS39_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 39 canonical approval design wiring."""

    panel = _PASS39_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass39_panel_model(panel)


def preview_capture_to_markdown_source_pack_canonical_promotion_approval_design(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preview the Pass 39 canonical-promotion approval design packet."""

    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_design import (
        build_visual_capture_source_pack_canonical_promotion_approval_design,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    result = build_visual_capture_source_pack_canonical_promotion_approval_design(
        vault,
        _text(
            request.get("graph_indexing_artifact_path")
            or request.get("source_graph_indexing_artifact_path")
        ),
        expected_graph_indexing_artifact_digest=_text(
            request.get("expected_graph_indexing_artifact_digest")
        ),
        expected_graph_snapshot_digest=_text(request.get("expected_graph_snapshot_digest")),
        expected_canonical_promotion_candidate_digest=_text(
            request.get("expected_canonical_promotion_candidate_digest")
            or request.get("future_canonical_promotion_candidate_digest")
        ),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_canonical_promotion_approval_design",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass39_authority(dict(_AUTHORITY))),
    }


def _augment_pass39_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_design import (
        build_visual_capture_source_pack_canonical_promotion_approval_design_policy,
    )

    panel["next_recommended_pass"] = PASS39_NEXT_RECOMMENDED_PASS
    panel["source_pack_canonical_promotion_approval_design_policy"] = (
        build_visual_capture_source_pack_canonical_promotion_approval_design_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_canonical_promotion_approval_design_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_design_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_design_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_design_read_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_design_requires_candidate_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_packet_preview_ready": True,
            "reviewed_capture_canonical_promotion_approval_request_writer_ready": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS39_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass39_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_canonical_promotion_approval_design"
    ] = "read_only_canonical_promotion_candidate_to_future_approval_packet_preview"

    return panel


def _augment_pass39_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass38_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_design_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_design_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_design_read_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_design_requires_candidate_digest": True,
            "reviewed_capture_canonical_promotion_approval_packet_preview_allowed": True,
            "reviewed_capture_canonical_promotion_approval_request_writer_ready": False,
            "reviewed_capture_canonical_promotion_approval_request_write_allowed": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_promotion_executor_allowed": False,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_knowledge_promotion_allowed": False,
            "reviewed_capture_canonical_target_file_write_allowed": False,
            "reviewed_capture_canonical_knowledge_index_write_allowed": False,
            "reviewed_capture_canonical_graph_mutation_allowed": False,
            "reviewed_capture_provider_call_allowed": False,
            "reviewed_capture_external_send_allowed": False,
            "reviewed_capture_attachment_delete_allowed": False,
        }
    )
    return authority


PASS40_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass41-source-pack-canonical-promotion-approval-decision-consumption-readiness"
)

_PASS40_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 40 canonical approval request wiring."""

    panel = _PASS40_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass40_panel_model(panel)


def preview_capture_to_markdown_source_pack_canonical_promotion_approval_request(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return or write the Pass 40 canonical-promotion approval request."""

    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_request_writer import (
        build_visual_capture_source_pack_canonical_promotion_approval_request,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    expected_approval_request_digest = _text(
        request.get("expected_canonical_promotion_approval_request_digest")
        or request.get("expected_approval_request_digest")
    )
    result = build_visual_capture_source_pack_canonical_promotion_approval_request(
        vault,
        _text(
            request.get("graph_indexing_artifact_path")
            or request.get("source_graph_indexing_artifact_path")
        ),
        expected_graph_indexing_artifact_digest=_text(
            request.get("expected_graph_indexing_artifact_digest")
        ),
        expected_graph_snapshot_digest=_text(request.get("expected_graph_snapshot_digest")),
        expected_canonical_promotion_candidate_digest=_text(
            request.get("expected_canonical_promotion_candidate_digest")
            or request.get("future_canonical_promotion_candidate_digest")
        ),
        expected_canonical_promotion_approval_request_digest=expected_approval_request_digest,
        operator_statement=_text(request.get("operator_statement")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        requested_by=_text(request.get("requested_by") or "studio-operator"),
        write_approval_request=bool(request.get("write_approval_request")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_canonical_promotion_approval_request",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass40_authority(dict(_AUTHORITY))),
    }


def _augment_pass40_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_request_writer import (
        build_visual_capture_source_pack_canonical_promotion_approval_request_writer_policy,
    )

    panel["next_recommended_pass"] = PASS40_NEXT_RECOMMENDED_PASS
    panel["source_pack_canonical_promotion_approval_request_writer_policy"] = (
        build_visual_capture_source_pack_canonical_promotion_approval_request_writer_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_canonical_promotion_approval_request_writer_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_request_writer_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_requires_operator_statement": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_overwrite_blocked": True,
            "reviewed_capture_canonical_promotion_approval_decision_writer_ready": False,
            "reviewed_capture_canonical_promotion_approval_consumption_ready": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS40_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass40_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_canonical_promotion_approval_request"
    ] = "exact_digest_statement_guarded_create_only_pending_canonical_promotion_approval_request"

    return panel


def _augment_pass40_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass39_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_request_writer_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_requires_operator_statement": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_artifact_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_request_overwrite_allowed": False,
            "reviewed_capture_canonical_promotion_approval_decision_writer_ready": False,
            "reviewed_capture_canonical_promotion_approval_consumption_ready": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_promotion_executor_allowed": False,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_knowledge_promotion_allowed": False,
            "reviewed_capture_canonical_target_file_write_allowed": False,
            "reviewed_capture_canonical_knowledge_index_write_allowed": False,
            "reviewed_capture_canonical_graph_mutation_allowed": False,
            "reviewed_capture_provider_call_allowed": False,
            "reviewed_capture_external_send_allowed": False,
            "reviewed_capture_attachment_delete_allowed": False,
        }
    )
    return authority


PASS41_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass42-source-pack-canonical-promotion-approval-decision-writer"
)

_PASS41_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 41 canonical approval readiness wiring."""

    panel = _PASS41_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass41_panel_model(panel)


def preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the Pass 41 canonical-promotion approval decision readiness preview."""

    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_consumption_readiness import (
        build_visual_capture_source_pack_canonical_promotion_approval_consumption_readiness,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    expected_approval_request_digest = _text(
        request.get("expected_canonical_promotion_approval_request_digest")
        or request.get("expected_approval_request_digest")
        or request.get("approval_request_digest")
    )
    result = build_visual_capture_source_pack_canonical_promotion_approval_consumption_readiness(
        vault,
        _text(
            request.get("graph_indexing_artifact_path")
            or request.get("source_graph_indexing_artifact_path")
        ),
        expected_graph_indexing_artifact_digest=_text(
            request.get("expected_graph_indexing_artifact_digest")
            or request.get("graph_indexing_artifact_digest")
        ),
        expected_graph_snapshot_digest=_text(request.get("expected_graph_snapshot_digest")),
        expected_canonical_promotion_candidate_digest=_text(
            request.get("expected_canonical_promotion_candidate_digest")
            or request.get("future_canonical_promotion_candidate_digest")
        ),
        expected_canonical_promotion_approval_request_digest=expected_approval_request_digest,
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_canonical_promotion_approval_decision_consumption_readiness",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass41_authority(dict(_AUTHORITY))),
    }


def _augment_pass41_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_consumption_readiness import (
        build_visual_capture_source_pack_canonical_promotion_approval_consumption_readiness_policy,
    )

    panel["next_recommended_pass"] = PASS41_NEXT_RECOMMENDED_PASS
    panel["source_pack_canonical_promotion_approval_consumption_readiness_policy"] = (
        build_visual_capture_source_pack_canonical_promotion_approval_consumption_readiness_policy()
    )

    summary = panel.setdefault("summary", {})
    summary[
        "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ready"
    ] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_read_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_pending_request": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_exact_digest": True,
            "reviewed_capture_canonical_promotion_approval_decision_writer_ready": True,
            "reviewed_capture_canonical_promotion_approval_consumption_ready": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS41_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass41_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_canonical_promotion_approval_decision_consumption_readiness"
    ] = "read_only_pending_canonical_promotion_approval_request_to_future_decision_consumption_contract_preview"

    return panel


def _augment_pass41_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass40_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_read_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_pending_request": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_exact_digest": True,
            "reviewed_capture_canonical_promotion_approval_decision_writer_ready": True,
            "reviewed_capture_canonical_promotion_approval_decision_write_allowed": False,
            "reviewed_capture_canonical_promotion_approval_consumption_ready": False,
            "reviewed_capture_canonical_promotion_approval_consumption_allowed": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_promotion_executor_allowed": False,
            "reviewed_capture_canonical_mutation_allowed": False,
            "reviewed_capture_canonical_knowledge_promotion_allowed": False,
            "reviewed_capture_canonical_target_file_write_allowed": False,
            "reviewed_capture_canonical_knowledge_index_write_allowed": False,
            "reviewed_capture_canonical_graph_mutation_allowed": False,
            "reviewed_capture_provider_call_allowed": False,
            "reviewed_capture_external_send_allowed": False,
            "reviewed_capture_attachment_delete_allowed": False,
        }
    )
    return authority


PASS43_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass43-source-pack-canonical-promotion-approval-consumption-executor"
)

_PASS42_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 42 canonical decision wiring."""

    panel = _PASS42_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass42_panel_model(panel)


def preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return or write the Pass 42 canonical-promotion approval decision."""

    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_decision_writer import (
        build_visual_capture_source_pack_canonical_promotion_approval_decision,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    expected_approval_request_digest = _text(
        request.get("expected_canonical_promotion_approval_request_digest")
        or request.get("expected_approval_request_digest")
        or request.get("approval_request_digest")
    )
    expected_approval_decision_digest = _text(
        request.get("expected_canonical_promotion_approval_decision_digest")
        or request.get("expected_approval_decision_digest")
        or request.get("approval_decision_digest")
    )
    result = build_visual_capture_source_pack_canonical_promotion_approval_decision(
        vault,
        _text(
            request.get("graph_indexing_artifact_path")
            or request.get("source_graph_indexing_artifact_path")
        ),
        expected_graph_indexing_artifact_digest=_text(
            request.get("expected_graph_indexing_artifact_digest")
            or request.get("graph_indexing_artifact_digest")
        ),
        expected_graph_snapshot_digest=_text(request.get("expected_graph_snapshot_digest")),
        expected_canonical_promotion_candidate_digest=_text(
            request.get("expected_canonical_promotion_candidate_digest")
            or request.get("future_canonical_promotion_candidate_digest")
        ),
        expected_canonical_promotion_approval_request_digest=expected_approval_request_digest,
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        decision=_text(request.get("decision")),
        expected_canonical_promotion_approval_decision_digest=expected_approval_decision_digest,
        operator_statement=_text(request.get("operator_statement")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        decided_by=_text(request.get("decided_by") or "studio-operator"),
        write_approval_decision=bool(request.get("write_approval_decision")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_canonical_promotion_approval_decision",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass42_authority(dict(_AUTHORITY))),
    }


def _augment_pass42_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_decision_writer import (
        build_visual_capture_source_pack_canonical_promotion_approval_decision_writer_policy,
    )

    panel["next_recommended_pass"] = PASS43_NEXT_RECOMMENDED_PASS
    panel["source_pack_canonical_promotion_approval_decision_writer_policy"] = (
        build_visual_capture_source_pack_canonical_promotion_approval_decision_writer_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_requires_operator_statement": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_overwrite_blocked": True,
            "reviewed_capture_canonical_promotion_approval_decision_write_allowed": True,
            "reviewed_capture_canonical_promotion_approval_consumption_ready": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS43_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass42_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_canonical_promotion_approval_decision"
    ] = "exact_digest_statement_guarded_create_only_canonical_promotion_approval_decision"
    storage_policy[
        "canonical_promotion"
    ] = "blocked_until_separate_approval_consumption_and_executor"

    return panel


def _augment_pass42_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass41_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_requires_operator_statement": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_artifact_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_decision_overwrite_allowed": False,
            "reviewed_capture_canonical_promotion_approval_decision_write_allowed": True,
            "reviewed_capture_canonical_promotion_approval_consumption_allowed": False,
            "reviewed_capture_canonical_promotion_approval_exact_once_marker_write_allowed": False,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_promotion_allowed": False,
            "reviewed_capture_canonical_target_file_write_allowed": False,
            "reviewed_capture_canonical_knowledge_index_write_allowed": False,
            "reviewed_capture_canonical_graph_mutation_allowed": False,
        }
    )
    return authority


PASS44_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass44-source-pack-canonical-promotion-executor"
)

_PASS43_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 43 canonical consumption wiring."""

    panel = _PASS43_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass43_panel_model(panel)


def preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return or write the Pass 43 canonical-promotion approval consumption."""

    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_consumption_executor import (
        build_visual_capture_source_pack_canonical_promotion_approval_consumption,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    expected_approval_request_digest = _text(
        request.get("expected_canonical_promotion_approval_request_digest")
        or request.get("expected_approval_request_digest")
        or request.get("approval_request_digest")
    )
    expected_approval_decision_digest = _text(
        request.get("expected_canonical_promotion_approval_decision_digest")
        or request.get("expected_approval_decision_digest")
        or request.get("approval_decision_digest")
    )
    expected_approval_consumption_digest = _text(
        request.get("expected_canonical_promotion_approval_consumption_digest")
        or request.get("expected_approval_consumption_digest")
        or request.get("approval_consumption_digest")
    )
    result = build_visual_capture_source_pack_canonical_promotion_approval_consumption(
        vault,
        _text(
            request.get("graph_indexing_artifact_path")
            or request.get("source_graph_indexing_artifact_path")
        ),
        expected_graph_indexing_artifact_digest=_text(
            request.get("expected_graph_indexing_artifact_digest")
            or request.get("graph_indexing_artifact_digest")
        ),
        expected_graph_snapshot_digest=_text(request.get("expected_graph_snapshot_digest")),
        expected_canonical_promotion_candidate_digest=_text(
            request.get("expected_canonical_promotion_candidate_digest")
            or request.get("future_canonical_promotion_candidate_digest")
        ),
        expected_canonical_promotion_approval_request_digest=expected_approval_request_digest,
        approval_artifact_path=_text(request.get("approval_artifact_path")),
        decision=_text(request.get("decision")),
        approval_decision_artifact_path=_text(request.get("approval_decision_artifact_path")),
        expected_canonical_promotion_approval_decision_digest=expected_approval_decision_digest,
        expected_canonical_promotion_approval_consumption_digest=expected_approval_consumption_digest,
        operator_statement=_text(request.get("operator_statement")),
        reviewed_by=_text(request.get("reviewed_by") or "studio-operator"),
        consumed_by=_text(request.get("consumed_by") or "studio-operator"),
        write_consumption_marker=bool(request.get("write_consumption_marker")),
        write_approval_consumption=bool(request.get("write_approval_consumption")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_canonical_promotion_approval_consumption",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass43_authority(dict(_AUTHORITY))),
    }


def _augment_pass43_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_consumption_executor import (
        build_visual_capture_source_pack_canonical_promotion_approval_consumption_executor_policy,
    )

    panel["next_recommended_pass"] = PASS44_NEXT_RECOMMENDED_PASS
    panel["source_pack_canonical_promotion_approval_consumption_executor_policy"] = (
        build_visual_capture_source_pack_canonical_promotion_approval_consumption_executor_policy()
    )

    summary = panel.setdefault("summary", {})
    summary[
        "reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ready"
    ] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_marker_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_requires_operator_statement": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_overwrite_blocked": True,
            "reviewed_capture_canonical_promotion_approval_consumption_ready": True,
            "reviewed_capture_canonical_promotion_approval_consumption_allowed": True,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_promotion_blocked": True,
            "next_recommended_pass": PASS44_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass43_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_canonical_promotion_approval_consumption"
    ] = "exact_digest_statement_guarded_create_only_marker_then_consumption"
    storage_policy[
        "canonical_promotion"
    ] = "blocked_until_separate_canonical_promotion_executor"

    return panel


def _augment_pass43_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass42_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_marker_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_requires_operator_statement": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_write_allowed": True,
            "reviewed_capture_source_pack_canonical_promotion_approval_consumption_overwrite_allowed": False,
            "reviewed_capture_canonical_promotion_approval_consumption_allowed": True,
            "reviewed_capture_canonical_promotion_approval_exact_once_marker_write_allowed": True,
            "reviewed_capture_canonical_promotion_executor_ready": False,
            "reviewed_capture_canonical_promotion_executor_allowed": False,
            "reviewed_capture_canonical_promotion_allowed": False,
            "reviewed_capture_canonical_target_file_write_allowed": False,
            "reviewed_capture_canonical_knowledge_index_write_allowed": False,
            "reviewed_capture_canonical_graph_mutation_allowed": False,
            "reviewed_capture_provider_call_allowed": False,
            "reviewed_capture_external_send_allowed": False,
            "reviewed_capture_attachment_delete_allowed": False,
        }
    )
    return authority


PASS45_NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass45-live-capture-ocr-and-packaged-desktop-proof"
)

_PASS44_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL = build_capture_to_markdown_panel


def build_capture_to_markdown_panel(
    vault_root: str | _Path,
    *,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Return the mounted Studio panel model with Pass 44 canonical promotion wiring."""

    panel = _PASS44_BASE_BUILD_CAPTURE_TO_MARKDOWN_PANEL(vault_root, recent_limit=recent_limit)
    return _augment_pass44_panel_model(panel)


def preview_capture_to_markdown_source_pack_canonical_promotion(
    vault_root: str | _Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return or write the Pass 44 canonical-promotion executor result."""

    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_executor import (
        build_visual_capture_source_pack_canonical_promotion,
    )

    vault = _Path(vault_root).resolve()
    request = payload or {}
    expected_approval_request_digest = _text(
        request.get("expected_canonical_promotion_approval_request_digest")
        or request.get("expected_approval_request_digest")
        or request.get("approval_request_digest")
    )
    expected_approval_decision_digest = _text(
        request.get("expected_canonical_promotion_approval_decision_digest")
        or request.get("expected_approval_decision_digest")
        or request.get("approval_decision_digest")
    )
    expected_approval_consumption_digest = _text(
        request.get("expected_canonical_promotion_approval_consumption_digest")
        or request.get("expected_approval_consumption_digest")
        or request.get("approval_consumption_digest")
    )
    result = build_visual_capture_source_pack_canonical_promotion(
        vault,
        _text(
            request.get("graph_indexing_artifact_path")
            or request.get("source_graph_indexing_artifact_path")
        ),
        expected_graph_indexing_artifact_digest=_text(
            request.get("expected_graph_indexing_artifact_digest")
            or request.get("graph_indexing_artifact_digest")
        ),
        expected_graph_snapshot_digest=_text(request.get("expected_graph_snapshot_digest")),
        expected_canonical_promotion_candidate_digest=_text(
            request.get("expected_canonical_promotion_candidate_digest")
            or request.get("future_canonical_promotion_candidate_digest")
        ),
        expected_canonical_promotion_approval_request_digest=expected_approval_request_digest,
        expected_canonical_promotion_approval_decision_digest=expected_approval_decision_digest,
        approval_consumption_artifact_path=_text(
            request.get("approval_consumption_artifact_path")
        ),
        expected_canonical_promotion_approval_consumption_digest=expected_approval_consumption_digest,
        expected_canonical_promotion_digest=_text(
            request.get("expected_canonical_promotion_digest")
            or request.get("canonical_promotion_digest")
        ),
        operator_statement=_text(request.get("operator_statement")),
        promoted_by=_text(request.get("promoted_by") or "studio-operator"),
        write_canonical_promotion_marker=bool(request.get("write_canonical_promotion_marker")),
        write_canonical_knowledge_note=bool(request.get("write_canonical_knowledge_note")),
        write_canonical_knowledge_index=bool(request.get("write_canonical_knowledge_index")),
        write_canonical_promotion_artifact=bool(request.get("write_canonical_promotion_artifact")),
    )
    return dict(result) | {
        "panel_surface": SURFACE_ID,
        "action": "source_pack_canonical_promotion",
        "recent_captures": list_recent_visual_captures(vault, limit=10),
        "panel_authority": dict(_augment_pass44_authority(dict(_AUTHORITY))),
    }


def _augment_pass44_panel_model(panel: dict[str, Any]) -> dict[str, Any]:
    from runtime.acquisition.visual_capture_source_pack_canonical_promotion_executor import (
        build_visual_capture_source_pack_canonical_promotion_executor_policy,
    )

    panel["next_recommended_pass"] = PASS45_NEXT_RECOMMENDED_PASS
    panel["source_pack_canonical_promotion_executor_policy"] = (
        build_visual_capture_source_pack_canonical_promotion_executor_policy()
    )

    summary = panel.setdefault("summary", {})
    summary["reviewed_capture_source_pack_canonical_promotion_executor_ready"] = True

    readiness = panel.setdefault("readiness", {})
    readiness.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_executor_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_executor_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_requires_operator_statement": True,
            "reviewed_capture_source_pack_canonical_promotion_marker_create_only": True,
            "reviewed_capture_source_pack_canonical_promotion_artifact_create_only": True,
            "reviewed_capture_source_pack_canonical_knowledge_note_create_only": True,
            "reviewed_capture_canonical_promotion_executor_allowed": True,
            "reviewed_capture_canonical_promotion_allowed": True,
            "reviewed_capture_canonical_knowledge_note_write_allowed": True,
            "reviewed_capture_canonical_knowledge_index_write_allowed": True,
            "reviewed_capture_canonical_graph_mutation_allowed": False,
            "reviewed_capture_source_intelligence_core_rewrite_allowed": False,
            "reviewed_capture_provider_call_allowed": False,
            "reviewed_capture_external_send_allowed": False,
            "next_recommended_pass": PASS45_NEXT_RECOMMENDED_PASS,
        }
    )

    authority = panel.setdefault("authority", {})
    _augment_pass44_authority(authority)

    storage_policy = panel.setdefault("storage_policy", {})
    storage_policy[
        "source_pack_canonical_promotion"
    ] = "exact_digest_statement_guarded_marker_note_index_and_artifact"
    storage_policy[
        "canonical_promotion"
    ] = "canonical_note_and_index_route_write_available_after_exact_approval_consumption"

    return panel


def _augment_pass44_authority(authority: dict[str, Any]) -> dict[str, Any]:
    _augment_pass43_authority(authority)
    authority.update(
        {
            "reviewed_capture_source_pack_canonical_promotion_executor_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_executor_ui_ready": True,
            "reviewed_capture_source_pack_canonical_promotion_requires_exact_digest": True,
            "reviewed_capture_source_pack_canonical_promotion_requires_operator_statement": True,
            "reviewed_capture_canonical_promotion_executor_allowed": True,
            "reviewed_capture_canonical_promotion_allowed": True,
            "reviewed_capture_canonical_promotion_marker_write_allowed": True,
            "reviewed_capture_canonical_promotion_artifact_write_allowed": True,
            "reviewed_capture_canonical_target_file_write_allowed": True,
            "reviewed_capture_canonical_knowledge_note_write_allowed": True,
            "reviewed_capture_canonical_knowledge_index_write_allowed": True,
            "reviewed_capture_canonical_graph_mutation_allowed": False,
            "reviewed_capture_source_intelligence_core_rewrite_allowed": False,
            "reviewed_capture_provider_call_allowed": False,
            "reviewed_capture_external_send_allowed": False,
            "reviewed_capture_attachment_delete_allowed": False,
        }
    )
    return authority
