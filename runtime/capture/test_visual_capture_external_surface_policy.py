from __future__ import annotations

from runtime.capture.visual_capture.external_surface_policy import (
    EXTERNAL_SURFACE_DEFERRAL_POLICY_ID,
    SAFE_CURRENT_INPUTS,
    build_external_surface_deferral_policy,
    is_external_surface_blocked,
)


def test_external_surface_deferral_policy_blocks_unbuilt_capture_surfaces() -> None:
    policy = build_external_surface_deferral_policy()

    assert policy["policy_id"] == EXTERNAL_SURFACE_DEFERRAL_POLICY_ID
    assert policy["status"] == "partial"
    assert policy["implementation_status"] == "partially_built"
    assert policy["all_external_capture_surfaces_blocked"] is False
    assert set(SAFE_CURRENT_INPUTS) <= set(policy["safe_current_inputs"])
    assert "global_hotkey_capture" in policy["implemented_surface_ids"]
    assert "active_window_capture" in policy["implemented_surface_ids"]
    assert "screen_pixel_capture" in policy["implemented_surface_ids"]
    assert "accessibility_tree_capture" in policy["implemented_surface_ids"]
    assert "browser_extension_capture" in policy["implemented_surface_ids"]
    assert "ambient_clipboard_capture" in policy["implemented_surface_ids"]
    assert "discord_command_capture" in policy["implemented_surface_ids"]

    required_blocked = {
        "overlay_capture_ui",
        "external_control_plane_capture",
        "external_browser_tab_capture",
    }
    assert required_blocked <= set(policy["blocked_surface_ids"])
    assert "read_ambient_clipboard_without_privacy_opt_in" in policy["forbidden_effects"]
    assert "accept_discord_capture_command_outside_agent_bus" in policy["forbidden_effects"]

    for surface in policy["blocked_surfaces"]:
        assert surface["status"] == "deferred"
        assert surface["implementation_status"] == "not_built"
        assert surface["authority_allowed"] is False
        assert surface["requires_operator_approval"] is True
        assert surface["runtime_action"] == "blocked"


def test_external_surface_block_lookup_is_explicit() -> None:
    assert is_external_surface_blocked("global_hotkey_capture") is False
    assert is_external_surface_blocked("discord_command_capture") is False
    assert is_external_surface_blocked("active_window_capture") is False
    assert is_external_surface_blocked("accessibility_tree_capture") is False
    assert is_external_surface_blocked("ambient_clipboard_capture") is False
    assert is_external_surface_blocked("manual_text") is False
    assert is_external_surface_blocked("") is False
