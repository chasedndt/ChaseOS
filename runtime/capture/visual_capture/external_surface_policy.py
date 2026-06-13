"""External capture surface policy for Capture to Markdown.

This file separates implemented opt-in Capture surfaces from remaining surfaces
that still require their own privacy and permission adapters.
"""

from __future__ import annotations

from typing import Any


EXTERNAL_SURFACE_DEFERRAL_POLICY_ID = "vcmi.external_capture_surfaces.deferred.v1"

SAFE_CURRENT_INPUTS = (
    "manual_text",
    "local_text_file",
    "saved_html_file",
    "controlled_html_artifact",
    "browser_extension_capture",
    "screenshot_attachment",
    "screen_capture",
    "display_region_capture",
    "active_window_capture",
    "accessibility_tree_capture",
    "ambient_clipboard_capture",
    "global_hotkey_capture",
)

_IMPLEMENTED_SURFACES = (
    {
        "id": "global_hotkey_capture",
        "label": "Global hotkey capture",
        "reason": "Windows hotkey registration is opt-in from Settings and runs only explicit Capture collectors.",
    },
    {
        "id": "active_window_capture",
        "label": "Active-window capture",
        "reason": "Active-window capture is opt-in from Settings and captures only after a Capture page click or configured shortcut.",
    },
    {
        "id": "screen_pixel_capture",
        "label": "Screen-pixel capture",
        "reason": "Screen and display-region capture are opt-in from Settings and write screenshot evidence only after operator action.",
    },
    {
        "id": "accessibility_tree_capture",
        "label": "Accessibility tree capture",
        "reason": "Accessibility tree capture is opt-in from Settings and reads foreground application accessible text only after operator action.",
    },
    {
        "id": "browser_extension_capture",
        "label": "Browser extension capture",
        "reason": "The ChaseOS browser extension exports operator-triggered page text artifacts that Studio imports only after Settings enablement and operator selection.",
    },
    {
        "id": "ambient_clipboard_capture",
        "label": "Ambient clipboard capture",
        "reason": "Ambient clipboard monitoring is opt-in from Settings, runs only during an explicit monitoring session, and writes a small local state buffer only.",
    },
    {
        "id": "discord_command_capture",
        "label": "Discord command capture",
        "reason": "Discord-origin commands are captured only after they have entered ChaseOS-owned Agent Bus structured state and after Settings enablement plus operator action.",
    },
)

_BLOCKED_SURFACES = (
    {
        "id": "overlay_capture_ui",
        "label": "Overlay capture UI",
        "reason": "The drag-select display-region overlay is implemented; a broader floating capture palette still needs a separate design.",
    },
    {
        "id": "external_control_plane_capture",
        "label": "External control-plane capture",
        "reason": "External commands are ingress data, not direct capture instructions.",
    },
    {
        "id": "external_browser_tab_capture",
        "label": "External browser tab capture",
        "reason": "Active tabs, profiles, sessions, cookies, and history remain out of scope.",
    },
)

FORBIDDEN_EXTERNAL_SURFACE_EFFECTS = (
    "read_ambient_clipboard_without_privacy_opt_in",
    "show_broad_capture_palette",
    "read_active_browser_tab",
    "read_browser_profile",
    "read_browser_history",
    "read_browser_cookies",
    "read_browser_sessions",
    "accept_discord_capture_command_outside_agent_bus",
    "accept_external_control_plane_command",
    "send_capture_externally",
)


def build_external_surface_deferral_policy() -> dict[str, Any]:
    """Return the deterministic policy for implemented and remaining external surfaces."""

    implemented_surfaces = [
        {
            "id": surface["id"],
            "label": surface["label"],
            "status": "implemented",
            "implementation_status": "built",
            "authority_allowed": True,
            "requires_operator_approval": True,
            "approval_scope": "settings_toggle_and_operator_action_required",
            "runtime_action": "allowed_after_settings_and_click_or_shortcut",
            "reason": surface["reason"],
        }
        for surface in _IMPLEMENTED_SURFACES
    ]

    blocked_surfaces = [
        {
            "id": surface["id"],
            "label": surface["label"],
            "status": "deferred",
            "implementation_status": "not_built",
            "authority_allowed": False,
            "requires_operator_approval": True,
            "approval_scope": "separate_design_and_operator_approval_required",
            "runtime_action": "blocked",
            "reason": surface["reason"],
        }
        for surface in _BLOCKED_SURFACES
    ]
    return {
        "policy_id": EXTERNAL_SURFACE_DEFERRAL_POLICY_ID,
        "status": "partial",
        "implementation_status": "partially_built",
        "all_external_capture_surfaces_blocked": False,
        "safe_current_inputs": list(SAFE_CURRENT_INPUTS),
        "implemented_surface_count": len(implemented_surfaces),
        "implemented_surfaces": implemented_surfaces,
        "implemented_surface_ids": [surface["id"] for surface in implemented_surfaces],
        "blocked_surface_count": len(blocked_surfaces),
        "blocked_surfaces": blocked_surfaces,
        "blocked_surface_ids": [surface["id"] for surface in blocked_surfaces],
        "forbidden_effects": list(FORBIDDEN_EXTERNAL_SURFACE_EFFECTS),
        "external_ingress_rule": (
            "Discord, chat, browser, OS, and other external ingress must become "
            "explicit operator-selected source material or ChaseOS-owned "
            "structured state before Capture to Markdown processing."
        ),
        "governance_note": (
            "This policy is a deferral and authority block only. It does not "
            "implement broad capture palettes, Discord "
            "commands, external control-plane capture, or active browser-tab capture."
        ),
    }


def is_external_surface_blocked(surface_id: str) -> bool:
    """Return true when a surface is blocked by the Pass 8 deferral policy."""

    return str(surface_id or "") in {
        surface["id"]
        for surface in _BLOCKED_SURFACES
    }
