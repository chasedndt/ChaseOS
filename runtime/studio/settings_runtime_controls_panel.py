"""Read-only Studio Settings + Runtime Controls panel model."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.config.settings_summary import build_settings_summary
from runtime.config.store import validate_config_store
from runtime.studio.launcher_update_check import (
    build_launcher_update_local_manifest_background_prompt_settings_action,
    build_launcher_update_local_release_channel_blocker_closeout,
    build_launcher_update_status,
)
from runtime.studio.capture_collector_settings import build_capture_collector_settings_model
from runtime.studio.capture_hotkey_settings import build_capture_hotkey_settings_model
from runtime.studio.capture_ocr_settings import build_capture_local_image_text_settings_model
from runtime.studio.provider_readiness import build_studio_provider_readiness
from runtime.studio.personal_context_import import build_personal_context_import_panel
from runtime.studio.runtime_gateway_controls import build_runtime_gateway_controls_model
from runtime.studio.runtime_startup_controls import build_runtime_startup_controls_model


MODEL_VERSION = "studio.settings_runtime_controls_panel.v1"
SURFACE_ID = "studio_settings_runtime_controls_panel"


SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "credential",
    "cookie",
    "connection_string",
    "expected_contents",
)

SAFE_SECRET_STATUS_KEYS = {
    "secret_reference_present",
    "secret_values_included",
    "secrets_allowed_in_config",
    "secrets_displayed",
    "shows_secret_values",
    "shows_raw_credentials",
    "raw_credentials_included",
    "raw_credential_values_displayed",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in SAFE_SECRET_STATUS_KEYS and isinstance(item, (bool, type(None))):
                continue
            if any(fragment in lowered for fragment in SENSITIVE_KEY_FRAGMENTS):
                return True
            if _contains_sensitive_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _provider_rows(settings_summary: dict[str, Any]) -> list[dict[str, Any]]:
    provider_summary = settings_summary.get("provider_summary") or {}
    providers = provider_summary.get("providers") or []
    rows: list[dict[str, Any]] = []
    for provider in providers:
        rows.append(
            {
                "provider_id": provider.get("provider_id"),
                "label": provider.get("label"),
                "configured": bool(provider.get("configured")),
                "valid": bool(provider.get("valid")),
                "default_model": provider.get("default_model"),
                "binding_label": f"{provider.get('provider_id') or 'unknown_provider'} / {provider.get('default_model') or 'unknown_model'}",
                "reasoning_policy": provider.get("reasoning_policy"),
                "secret_reference_present": bool(provider.get("secret_reference_present")),
                "missing": list(provider.get("missing") or []),
                "notes": provider.get("notes"),
            }
        )
    return rows


def _startup_surface_rows(startup_model: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for card in startup_model.get("surface_cards") or []:
        commands = card.get("commands") if isinstance(card.get("commands"), dict) else {}
        rows.append(
            {
                "runtime_id": card.get("runtime_id"),
                "runtime_name": card.get("runtime_name"),
                "surface_id": card.get("surface_id"),
                "ui_label": card.get("ui_label"),
                "current_state": card.get("current_state"),
                "user_manageable": bool(card.get("user_manageable")),
                "studio_control_enabled": bool(card.get("studio_control_enabled")),
                "studio_visual_toggle_built": bool(card.get("studio_visual_toggle_built")),
                "requires_confirm_action": bool(card.get("requires_confirm_action")),
                "live_toggle_blocked_until_approval_consumption": bool(
                    card.get("live_toggle_blocked_until_approval_consumption")
                ),
                "dry_run_enable_command": commands.get("dry_run_enable")
                or ((commands.get("enable") or {}).get("studio_preview") if isinstance(commands.get("enable"), dict) else None),
                "dry_run_disable_command": commands.get("dry_run_disable")
                or ((commands.get("disable") or {}).get("studio_preview") if isinstance(commands.get("disable"), dict) else None),
                "executor_preflight_command": commands.get("executor_preflight"),
            }
        )
    return rows


def build_settings_runtime_controls_panel(vault_root: str | Path) -> dict[str, Any]:
    """Build the native Settings panel contract without executing mutations."""

    vault = Path(vault_root).resolve()
    startup_model = build_runtime_startup_controls_model(vault, probe_processes=False)
    settings_summary = build_settings_summary(vault_root=vault)
    validation = validate_config_store(vault_root=vault)
    provider_readiness = build_studio_provider_readiness(vault)
    personal_context_import = build_personal_context_import_panel(vault)
    launcher_update = dict(build_launcher_update_status(vault))
    local_manifest_prompt = build_launcher_update_local_manifest_background_prompt_settings_action(
        vault
    )
    local_release_channel_closeout = (
        build_launcher_update_local_release_channel_blocker_closeout(vault)
    )
    launcher_update["local_manifest_prompt"] = local_manifest_prompt
    launcher_update["local_release_channel_closeout"] = local_release_channel_closeout
    capture_hotkeys = build_capture_hotkey_settings_model(vault)
    capture_collectors = build_capture_collector_settings_model(vault)
    capture_image_text_settings = build_capture_local_image_text_settings_model(vault)
    capture_image_text_quality = (
        capture_image_text_settings.get("quality_fixture_proof")
        if isinstance(capture_image_text_settings.get("quality_fixture_proof"), dict)
        else {}
    )
    runtime_gateway_controls = build_runtime_gateway_controls_model(vault, probe_processes=False)
    provider_rows = _provider_rows(settings_summary)
    startup_rows = _startup_surface_rows(startup_model)
    provider_summary = settings_summary.get("provider_summary") or {}
    runtime_summary = settings_summary.get("runtime_summary") or {}
    governance = settings_summary.get("governance") or {}
    approval_boundary = startup_model.get("approval_boundary") or {}
    config = settings_summary.get("config") or {}

    authority = {
        "read_only": False,
        "possible_writes": [
            "runtime_gateway_control_preferences",
            "runtime_lifecycle_run",
            "capture_shortcut_preferences",
            "capture_collector_preferences",
            "capture_local_image_text_preferences",
        ],
        "writes_vault": False,
        "writes_config": False,
        "writes_host_startup": True,
        "writes_runtime_lifecycle": True,
        "writes_capture_shortcut_preferences": True,
        "writes_capture_collector_preferences": True,
        "writes_capture_local_image_text_preferences": True,
        "registers_global_hotkeys": bool(
            (capture_hotkeys.get("authority") or {}).get("registers_global_hotkeys")
        ),
        "runs_capture_collectors_from_studio_shortcuts": bool(
            (capture_hotkeys.get("authority") or {}).get(
                "runs_explicit_collectors_from_studio_shortcuts"
            )
        ),
        "runs_capture_collectors_from_global_hotkeys": bool(
            (capture_hotkeys.get("authority") or {}).get(
                "runs_explicit_collectors_from_global_hotkeys"
            )
        ),
        "reads_selected_text": bool(
            (capture_collectors.get("readiness") or {}).get("selected_text_capture_enabled")
        ),
        "reads_accessibility_tree": bool(
            (capture_collectors.get("readiness") or {}).get(
                "accessibility_tree_capture_enabled"
            )
        ),
        "reads_accessibility_tree_on_settings_load": False,
        "starts_subprocesses_on_settings_load": False,
        "runs_shell_commands_on_settings_load": False,
        "reads_ambient_clipboard": bool(
            (capture_collectors.get("readiness") or {}).get(
                "ambient_clipboard_monitoring_enabled"
            )
        ),
        "reads_ambient_clipboard_only_after_privacy_opt_in_and_monitor_start": True,
        "reads_ambient_clipboard_on_settings_load": False,
        "reads_clipboard_text_only_after_settings_and_click": True,
        "reads_clipboard_on_settings_load": False,
        "reads_clipboard_on_capture_panel_load": False,
        "captures_screen_pixels": bool(
            (capture_collectors.get("readiness") or {}).get("screen_capture_enabled")
            or (capture_collectors.get("readiness") or {}).get("display_region_capture_enabled")
            or (capture_collectors.get("readiness") or {}).get("active_window_capture_enabled")
        ),
        "captures_screen_pixels_on_settings_load": False,
        "reads_active_browser_tab": False,
        "reads_controlled_browser_artifact_only_after_settings_file_and_click": True,
        "reads_browser_extension_artifact_only_after_settings_file_and_click": True,
        "reads_controlled_browser_artifact_on_settings_load": False,
        "reads_controlled_browser_artifact_on_capture_panel_load": False,
        "reads_chaseos_active_browser_state_only_after_settings_and_click": True,
        "reads_chaseos_active_browser_state_on_settings_load": False,
        "reads_chaseos_active_browser_state_on_capture_panel_load": False,
        "launches_chaseos_owned_browser_page_only_after_settings_url_and_click": True,
        "reads_chaseos_owned_browser_page_only_after_settings_url_and_click": True,
        "reads_chaseos_owned_browser_page_on_settings_load": False,
        "reads_chaseos_owned_browser_page_on_capture_panel_load": False,
        "reads_personal_active_browser_tab": False,
        "reads_chaseos_discord_artifact_only_after_settings_file_and_click": True,
        "reads_chaseos_agent_bus_discord_ingress_only_after_settings_and_click": True,
        "reads_chaseos_discord_artifact_on_settings_load": False,
        "reads_chaseos_discord_artifact_on_capture_panel_load": False,
        "reads_chaseos_agent_bus_discord_ingress_on_settings_load": False,
        "reads_chaseos_agent_bus_discord_ingress_on_capture_panel_load": False,
        "calls_discord_api": False,
        "reads_discord_token": False,
        "reads_discord_webhook": False,
        "reads_discord_bindings": False,
        "listens_to_discord_events": False,
        "writes_provider_config": False,
        "writes_provider_target_profile": False,
        "provider_switch_allowed": False,
        "executes_runtime_actions": True,
        "executes_live_provider_probe": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "workflow_execution_allowed": False,
        "approval_execution_allowed": False,
        "startup_mutation_allowed": True,
        "canonical_mutation_allowed": False,
        "shows_raw_credentials": False,
        "shows_secret_values": False,
    }

    action_posture = {
        "read_only_status_visible": True,
        "native_ui_action_buttons_enabled": True,
        "dry_run_command_visible": True,
        "confirmed_toggle_command_visible": True,
        "confirm_action_required": bool(
            (startup_model.get("boundary") or {}).get("live_toggle_requires_confirm_action")
        ),
        "gate_approval_required": bool(
            approval_boundary.get("approval_required_before_confirmed_mutation")
        ),
        "executor_enabled_now": bool(approval_boundary.get("executor_enabled_now")),
        "host_mutation_blocked": bool(
            approval_boundary.get("confirmed_host_mutation_blocked_until_boundary_settled")
        ),
        "route_for_future_mutation": "chaseos studio runtime-startup-controls --action toggle --confirm-action --gate-approval-id <approval-id> --plan-digest <sha256>",
        "route_for_current_preview": "chaseos studio runtime-startup-controls --action dry-run --json",
    }

    model = {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "title": "Settings + Runtime Controls",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "summary": {
            "settings_posture": settings_summary.get("settings_posture"),
            "config_posture": validation.get("posture"),
            "known_provider_count": int(provider_summary.get("known_count") or 0),
            "configured_provider_count": int(provider_summary.get("configured_count") or 0),
            "valid_provider_count": int(provider_summary.get("valid_count") or 0),
            "provider_readiness_status": (provider_readiness.get("summary") or {}).get("readiness_status"),
            "active_provider_binding": (provider_readiness.get("summary") or {}).get("active_binding_label"),
            "fallback_provider_binding": (provider_readiness.get("summary") or {}).get("fallback_binding_label"),
            "provider_degraded_reason": (provider_readiness.get("summary") or {}).get("degraded_reason"),
            "queued_provider_retry_count": int((provider_readiness.get("summary") or {}).get("queued_retry_count") or 0),
            "known_runtime_count": int(runtime_summary.get("known_count") or 0),
            "startup_runtime_count": int(startup_model.get("runtime_count") or 0),
            "startup_surface_count": int(startup_model.get("surface_count") or 0),
            "runtime_gateway_component_count": int(runtime_gateway_controls.get("component_count") or 0),
            "capture_shortcut_action_count": len(capture_hotkeys.get("actions") or []),
            "capture_collector_shortcut_action_count": len(
                [
                    action
                    for action in capture_hotkeys.get("actions") or []
                    if isinstance(action, dict) and action.get("collector_action")
                ]
            ),
            "capture_screen_collector_built": bool(
                (capture_collectors.get("summary") or {}).get("screen_capture_collector_built")
            ),
            "capture_screen_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get("screen_capture_enabled")
            ),
            "capture_screen_collector_status": (
                (capture_collectors.get("summary") or {}).get("screen_capture_status")
                or "unknown"
            ),
            "capture_display_region_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "display_region_capture_collector_built"
                )
            ),
            "capture_display_region_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "display_region_capture_enabled"
                )
            ),
            "capture_display_region_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "display_region_capture_status"
                )
                or "unknown"
            ),
            "capture_active_window_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "active_window_capture_collector_built"
                )
            ),
            "capture_active_window_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "active_window_capture_enabled"
                )
            ),
            "capture_active_window_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "active_window_capture_status"
                )
                or "unknown"
            ),
            "capture_clipboard_collector_built": bool(
                (capture_collectors.get("summary") or {}).get("clipboard_capture_collector_built")
            ),
            "capture_clipboard_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get("clipboard_capture_enabled")
            ),
            "capture_clipboard_collector_status": (
                (capture_collectors.get("summary") or {}).get("clipboard_capture_status")
                or "unknown"
            ),
            "capture_ambient_clipboard_monitor_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "ambient_clipboard_monitor_built"
                )
            ),
            "capture_ambient_clipboard_monitor_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "ambient_clipboard_monitoring_enabled"
                )
            ),
            "capture_ambient_clipboard_monitor_status": (
                (capture_collectors.get("summary") or {}).get("ambient_clipboard_status")
                or "unknown"
            ),
            "capture_selected_text_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "selected_text_capture_collector_built"
                )
            ),
            "capture_selected_text_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "selected_text_capture_enabled"
                )
            ),
            "capture_selected_text_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "selected_text_capture_status"
                )
                or "unknown"
            ),
            "capture_accessibility_tree_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "accessibility_tree_capture_collector_built"
                )
            ),
            "capture_accessibility_tree_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "accessibility_tree_capture_enabled"
                )
            ),
            "capture_accessibility_tree_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "accessibility_tree_capture_status"
                )
                or "unknown"
            ),
            "capture_browser_artifact_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "browser_artifact_capture_collector_built"
                )
            ),
            "capture_browser_artifact_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "browser_artifact_capture_enabled"
                )
            ),
            "capture_browser_artifact_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "browser_artifact_capture_status"
                )
                or "unknown"
            ),
            "capture_browser_extension_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "browser_extension_capture_collector_built"
                )
            ),
            "capture_browser_extension_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "browser_extension_capture_enabled"
                )
            ),
            "capture_browser_extension_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "browser_extension_capture_status"
                )
                or "unknown"
            ),
            "capture_active_chaseos_browser_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "active_chaseos_browser_capture_collector_built"
                )
            ),
            "capture_active_chaseos_browser_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "active_chaseos_browser_capture_enabled"
                )
            ),
            "capture_active_chaseos_browser_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "active_chaseos_browser_capture_status"
                )
                or "unknown"
            ),
            "capture_chaseos_browser_page_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "chaseos_browser_page_capture_collector_built"
                )
            ),
            "capture_chaseos_browser_page_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "chaseos_browser_page_capture_enabled"
                )
            ),
            "capture_chaseos_browser_page_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "chaseos_browser_page_capture_status"
                )
                or "unknown"
            ),
            "capture_discord_artifact_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "discord_artifact_capture_collector_built"
                )
            ),
            "capture_discord_artifact_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "discord_artifact_capture_enabled"
                )
            ),
            "capture_discord_artifact_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "discord_artifact_capture_status"
                )
                or "unknown"
            ),
            "capture_live_discord_command_collector_built": bool(
                (capture_collectors.get("summary") or {}).get(
                    "live_discord_command_capture_collector_built"
                )
            ),
            "capture_live_discord_command_collector_enabled": bool(
                (capture_collectors.get("summary") or {}).get(
                    "live_discord_command_capture_enabled"
                )
            ),
            "capture_live_discord_command_collector_status": (
                (capture_collectors.get("summary") or {}).get(
                    "live_discord_command_capture_status"
                )
                or "unknown"
            ),
            "capture_local_image_text_settings_visible": bool(
                (capture_image_text_settings.get("readiness") or {}).get("settings_page_visible")
            ),
            "capture_local_image_text_engine_available": bool(
                (capture_image_text_settings.get("readiness") or {}).get("local_engine_available")
            ),
            "capture_local_image_text_quality_fixture_status": (
                capture_image_text_quality.get("status") or "unknown"
            ),
            "capture_local_image_text_real_engine_quality_verified": bool(
                (capture_image_text_quality.get("summary") or {}).get("real_engine_quality_verified")
            ),
            "capture_shortcut_settings_visible": bool(
                (capture_hotkeys.get("readiness") or {}).get("settings_page_visible")
            ),
            "capture_global_hotkey_registration_enabled": bool(
                (capture_hotkeys.get("readiness") or {}).get(
                    "global_hotkey_registration_enabled"
                )
            ),
            "capture_global_hotkey_registered_binding_count": int(
                (capture_hotkeys.get("readiness") or {}).get(
                    "global_hotkey_registered_binding_count"
                )
                or 0
            ),
            "capture_global_hotkey_registration_blocked": bool(
                (capture_hotkeys.get("readiness") or {}).get("global_hotkey_registration_blocked")
            ),
            "personal_context_import_status": personal_context_import.get("status"),
            "launcher_update_status": launcher_update.get("status"),
            "launcher_current_version": launcher_update.get("current_version"),
            "launcher_latest_available_version": launcher_update.get("latest_version_label"),
            "launcher_local_manifest_prompt_status": local_manifest_prompt.get("status"),
            "launcher_local_manifest_prompt_visible": bool(
                local_manifest_prompt.get("settings_prompt_visible")
            ),
            "launcher_local_manifest_latest_available_version": local_manifest_prompt.get(
                "latest_version_label"
            ),
            "launcher_local_release_channel_closeout_status": local_release_channel_closeout.get(
                "status"
            ),
            "launcher_local_release_channel_only_external_blockers_remain": bool(
                local_release_channel_closeout.get("only_external_blockers_remain")
            ),
            "launcher_local_release_channel_local_passes_remaining": int(
                (
                    local_release_channel_closeout.get("closeout_summary") or {}
                ).get("local_passes_remaining_before_external_blocker")
                or 0
            ),
            "launcher_network_manifest_fetch_built": bool(
                (launcher_update.get("readiness") or {}).get("network_manifest_fetch_built")
            ),
            "launcher_network_manifest_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("network_manifest_default_enabled")
            ),
            "launcher_network_manifest_requires_operator_approval": bool(
                (launcher_update.get("readiness") or {}).get("network_manifest_fetch_requires_operator_approval")
            ),
            "launcher_download_staging_readiness_built": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_readiness_built")
            ),
            "launcher_download_staging_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_default_enabled")
            ),
            "launcher_download_staging_writes_enabled": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_writes_enabled")
            ),
            "launcher_download_staging_executor_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_executor_proof_built")
            ),
            "launcher_download_staging_executor_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_executor_default_enabled")
            ),
            "launcher_download_staging_executor_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_executor_writes_enabled_in_settings")
            ),
            "launcher_signature_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_proof_built")
            ),
            "launcher_signature_verification_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_default_enabled")
            ),
            "launcher_signature_verification_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_writes_enabled_in_settings")
            ),
            "launcher_signature_verification_install_enabled": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_install_enabled")
            ),
            "launcher_updater_helper_readiness_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_readiness_built")
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_proof_built"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_verified_signature": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_requires_verified_signature"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_current_executable": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_requires_current_executable"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_plan_write_enabled")
            ),
            "launcher_updater_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_execution_enabled")
            ),
            "launcher_updater_helper_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_replacement_enabled")
            ),
            "launcher_updater_helper_temp_fixture_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_temp_fixture_proof_built")
            ),
            "launcher_updater_helper_temp_fixture_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_temp_fixture_writes_enabled_in_settings")
            ),
            "launcher_updater_helper_temp_fixture_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_temp_fixture_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_binary_design_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_design_built")
            ),
            "launcher_updater_helper_binary_build_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_build_enabled")
            ),
            "launcher_updater_helper_binary_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_execution_enabled")
            ),
            "launcher_updater_helper_binary_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_writes_enabled_in_settings")
            ),
            "launcher_updater_helper_binary_real_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_real_replacement_enabled")
            ),
            "launcher_updater_helper_binary_build_strategy_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_proof_built"
                )
            ),
            "launcher_updater_helper_binary_build_strategy_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_binary_build_strategy_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_execution_enabled"
                )
            ),
            "launcher_updater_helper_binary_build_strategy_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_binary_spec_scaffold_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_spec_scaffold_built")
            ),
            "launcher_updater_helper_binary_spec_scaffold_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_spec_scaffold_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_binary_spec_scaffold_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_spec_scaffold_execution_enabled"
                )
            ),
            "launcher_updater_helper_binary_spec_scaffold_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_spec_scaffold_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_binary_static_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_proof_built"
                )
            ),
            "launcher_updater_helper_binary_static_verification_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_binary_static_verification_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_execution_enabled"
                )
            ),
            "launcher_updater_helper_binary_static_verification_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_plan_file_proof_built")
            ),
            "launcher_updater_helper_plan_file_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_plan_file_real_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_real_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_proof_built"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_requires_verified_staged_signature_plan": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_requires_verified_staged_signature_plan"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_executable_scaffold_built")
            ),
            "launcher_updater_helper_executable_scaffold_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_execution_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_executable_scaffold_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_proof_built"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_requires_signed_manifest_plan_file": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_requires_signed_manifest_plan_file"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_proof_built"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_requires_signed_manifest_scaffold": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_requires_signed_manifest_scaffold"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_audit_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_audit_write_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_proof_built"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_requires_signed_manifest_consumption": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_requires_signed_manifest_consumption"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_audit_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_audit_write_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_proof_built"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_requires_signed_manifest_audit_envelope": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_requires_signed_manifest_audit_envelope"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_proof_built"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_requires_signed_manifest_audit_write": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_requires_signed_manifest_audit_write"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_installer_launch_enabled"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_proof_built"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_requires_execution_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_requires_execution_dry_run"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_prompted_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_prompted_only"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_startup_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_startup_mutation_enabled"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_proof_built"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_requires_startup_background_prompt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_requires_startup_background_prompt"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_safe_dry_run_lane": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_safe_dry_run_lane"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_production_auto_update_complete": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_production_auto_update_complete"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_real_exe_replacement_complete": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_real_exe_replacement_complete"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_proof_built"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_requires_closeout": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_requires_closeout"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_requires_disposable_target": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_requires_disposable_target"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_host_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_host_mutation_enabled"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_proof_built"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_requires_approval_gate": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_requires_approval_gate"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_disposable_target_scope_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_disposable_target_scope_only"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_external_helper_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_external_helper_launch_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_settings_install_control_exposed"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_execution_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_requires_execution_boundary"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_injected_launcher": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_requires_injected_launcher"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_uses_chaseos_installer": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_uses_chaseos_installer"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_os_process_spawn_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_os_process_spawn_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_helper_launch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_requires_helper_launch_receipt_boundary"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_requires_external_receipt"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_chaseos_relaunch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_chaseos_relaunch_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_proof_built"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_requires_relaunch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_requires_relaunch_receipt_boundary"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_requires_primary_executable_descriptor": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_requires_primary_executable_descriptor"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_future_mutation_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_future_mutation_only"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_proof_built"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_requires_primary_install_mutation_gate": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_requires_primary_install_mutation_gate"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_writes_rollback_copy": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_writes_rollback_copy"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_writes_audit_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_writes_audit_receipt"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_primary_rollback_audit_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_requires_primary_rollback_audit_boundary"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_replacement_artifact_descriptor": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_requires_replacement_artifact_descriptor"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_requires_external_receipt"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_chaseos_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_chaseos_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_source_recovery_cleanup_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_proof_built"
                )
            ),
            "launcher_updater_source_recovery_cleanup_hash_pinning_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_recovery_bytecode_hash_pinning_enabled"
                )
            ),
            "launcher_updater_source_recovery_cleanup_normal_source_restoration_required": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_normal_source_restoration_required"
                )
            ),
            "launcher_updater_source_recovery_cleanup_final_closeout_blocked": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_final_auto_update_closeout_blocked_until_source_restored"
                )
            ),
            "launcher_updater_normal_source_restoration_readiness_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_readiness_proof_built"
                )
            ),
            "launcher_updater_normal_source_restoration_requires_wrapper_removal": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_requires_wrapper_removal"
                )
            ),
            "launcher_updater_normal_source_restoration_requires_authoritative_candidate": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_requires_authoritative_candidate"
                )
            ),
            "launcher_updater_normal_source_restoration_final_closeout_blocked": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_final_auto_update_closeout_blocked_until_source_restored"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_proof_built"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_source_write_enabled"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_source_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_source_replacement_enabled"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_proof_built"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_source_write_enabled_with_explicit_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_source_write_enabled_with_explicit_approval"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_settings_write_control_exposed"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_decompiler_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_decompiler_enabled"
                )
            ),
            "launcher_updater_source_regeneration_readiness_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_readiness_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_requires_local_decompiler_or_operator_source": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_requires_local_decompiler_or_operator_source"
                )
            ),
            "launcher_updater_source_regeneration_decompiler_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_decompiler_execution_enabled"
                )
            ),
            "launcher_updater_source_regeneration_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_source_write_enabled"
                )
            ),
            "launcher_updater_source_regeneration_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_runner_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_boundary_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_runner_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_requires_injected_runner"
                )
            ),
            "launcher_updater_source_regeneration_runner_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_source_regeneration_runner_candidate_writes_enabled_with_explicit_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_candidate_writes_enabled_with_explicit_approval"
                )
            ),
            "launcher_updater_source_regeneration_runner_live_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_live_source_write_enabled"
                )
            ),
            "launcher_updater_source_regeneration_runner_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_runner_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_runner_boundary"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_candidate_verification_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_candidate_verification_statement"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_restore_root": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_restore_root"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_restore_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_restore_statement"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_requires_live_restore_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_requires_live_restore_proof"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_scans_wrapper_tokens": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_scans_wrapper_tokens"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_real_source_restoration_execution_regression_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_source_restoration_execution_regression_boundary_proof_built"
                )
            ),
            "launcher_updater_real_source_restoration_execution_requires_explicit_restore_root": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_source_restoration_execution_requires_explicit_restore_root"
                )
            ),
            "launcher_updater_real_source_restoration_execution_requires_regression_evidence": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_source_restoration_execution_requires_regression_evidence"
                )
            ),
            "launcher_updater_real_source_restoration_execution_runs_regression_commands": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_source_restoration_execution_runs_regression_commands"
                )
            ),
            "launcher_updater_real_source_restoration_execution_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_source_restoration_execution_settings_write_control_exposed"
                )
            ),
            "launcher_updater_real_source_restoration_execution_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_source_restoration_execution_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_current_vault_source_restoration_closeout_readiness_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_restoration_closeout_readiness_proof_built"
                )
            ),
            "launcher_updater_current_vault_source_restoration_closeout_requires_source_cleanup_ready": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_restoration_closeout_requires_source_cleanup_ready"
                )
            ),
            "launcher_updater_current_vault_source_restoration_closeout_requires_regression_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_restoration_closeout_requires_regression_boundary"
                )
            ),
            "launcher_updater_current_vault_source_restoration_closeout_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_restoration_closeout_settings_write_control_exposed"
                )
            ),
            "launcher_updater_current_vault_source_restoration_closeout_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_restoration_closeout_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_source_candidate_inventory_wrapper_removal_preflight_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_wrapper_removal_preflight_proof_built"
                )
            ),
            "launcher_updater_source_candidate_inventory_scans_current_vault_sources": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_scans_current_vault_sources"
                )
            ),
            "launcher_updater_source_candidate_inventory_scans_build_lib_candidates": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_scans_build_lib_candidates"
                )
            ),
            "launcher_updater_source_candidate_inventory_requires_authoritative_candidates": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_requires_authoritative_candidates"
                )
            ),
            "launcher_updater_source_candidate_inventory_decompiler_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_decompiler_execution_enabled"
                )
            ),
            "launcher_updater_source_candidate_inventory_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_source_write_enabled"
                )
            ),
            "launcher_updater_source_candidate_inventory_wrapper_removal_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_wrapper_removal_enabled"
                )
            ),
            "launcher_updater_source_candidate_inventory_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_candidate_inventory_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_candidate_inventory_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_packet_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_packet_built"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_requires_candidate_files_inside_vault": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_requires_candidate_files_inside_vault"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_requires_required_symbols": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_requires_required_symbols"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_rejects_recovery_wrappers": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_rejects_recovery_wrappers"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_source_write_enabled"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_wrapper_removal_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_wrapper_removal_enabled"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_settings_write_control_exposed"
                )
            ),
            "launcher_updater_authoritative_normal_source_candidate_supply_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_normal_source_candidate_supply_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_boundary_proof_built"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_requires_import_candidate_paths": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_requires_import_candidate_paths"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_requires_required_symbols": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_requires_required_symbols"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_rejects_recovery_wrappers": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_rejects_recovery_wrappers"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_requires_explicit_candidate_write_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_requires_explicit_candidate_write_flag"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_candidate_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_candidate_write_enabled_with_explicit_approval"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_source_write_enabled"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_settings_write_control_exposed"
                )
            ),
            "launcher_updater_authoritative_source_candidate_import_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_source_candidate_import_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_readiness_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_readiness_proof_built"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_scans_configured_roots": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_scans_configured_roots"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_requires_wrapper_free_candidates": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_requires_wrapper_free_candidates"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_rejects_current_live_sources": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_rejects_current_live_sources"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_prepares_import_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_prepares_import_boundary"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_candidate_import_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_candidate_import_write_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_source_write_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_settings_write_control_exposed"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_proof_built"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_requires_source_materializer": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_requires_injected_source_materializer"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_requires_explicit_candidate_write_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_requires_explicit_candidate_write_flag"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_candidate_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_candidate_writes_enabled_with_explicit_approval"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_candidate_import_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_candidate_import_write_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_source_write_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_settings_write_control_exposed"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_materialization_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_materialization_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_proof_built"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_requires_materialization_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_requires_materialization_proof"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_rechecks_materialization_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_rechecks_materialization_digest"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_requires_explicit_candidate_import_write_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_requires_explicit_candidate_import_write_flag"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_candidate_import_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_candidate_import_write_enabled_with_explicit_approval"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_source_write_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_settings_write_control_exposed"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_import_from_materialization_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof_built"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_import_from_materialization_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_import_from_materialization_proof"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_rechecks_import_from_materialization_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_rechecks_import_from_materialization_digest"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_reuses_after_import_verifier": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_reuses_after_import_verifier"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_source_write_enabled"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_settings_write_control_exposed"
                )
            ),
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_proof_built"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_supply_verification_from_materialization_import_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_supply_verification_from_materialization_import_proof"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_rechecks_supply_verification_from_materialization_import_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_rechecks_supply_verification_from_materialization_import_digest"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_reuses_after_import_wrapper_removal_executor": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_reuses_after_import_wrapper_removal_executor"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_explicit_source_write_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_explicit_source_write_flag"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_source_write_enabled"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_settings_write_control_exposed"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_from_materialization_import_execution_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_proof_built"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_from_materialization_import_execution_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_from_materialization_import_execution_proof"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_rechecks_wrapper_removal_from_materialization_import_execution_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_rechecks_wrapper_removal_from_materialization_import_execution_digest"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_performed"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_supplied_regression_evidence": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_requires_supplied_regression_evidence"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_does_not_execute_regression_commands": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_does_not_execute_regression_commands"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_source_write_enabled"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_settings_write_control_exposed"
                )
            ),
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_post_wrapper_removal_regression_from_materialization_import_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_proof_built"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_requires_post_wrapper_removal_regression_from_materialization_import_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_requires_post_wrapper_removal_regression_from_materialization_import_proof"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_rechecks_post_wrapper_removal_regression_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_rechecks_post_wrapper_removal_regression_digest"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_requires_source_cleanup_ready": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_requires_source_cleanup_ready"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_requires_wrapper_free_current_vault_sources": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_requires_wrapper_free_current_vault_sources"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_read_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_read_only"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_settings_write_control_exposed"
                )
            ),
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_source_closeout_from_materialization_import_regression_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_proof_built"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_current_vault_source_closeout": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_requires_current_vault_source_closeout"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_source_closeout_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_rechecks_source_closeout_digest"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_primary_relaunch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_requires_primary_relaunch_receipt_boundary"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_primary_relaunch_receipt_boundary_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_rechecks_primary_relaunch_receipt_boundary_digest"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_external_chaseos_installer_primary_relaunch_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_requires_external_chaseos_installer_primary_relaunch_receipt"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_source_write_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_helper_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_helper_launch_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_settings_install_control_exposed"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_proof_built"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_production_primary_closeout_after_source_recovery": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_production_primary_closeout_after_source_recovery"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_primary_closeout_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_rechecks_primary_closeout_digest"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_live_completion_evidence": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_live_completion_evidence"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_live_evidence_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_rechecks_live_evidence_digest"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_primary_replacement_verified_live": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_primary_replacement_verified_live"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_startup_background_prompt_verified": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_startup_background_prompt_verified"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_read_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_read_only"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_helper_launch_enabled_by_this_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_helper_launch_enabled_by_this_proof"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_primary_real_exe_replacement_enabled_by_this_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_primary_real_exe_replacement_enabled_by_this_proof"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_settings_install_control_exposed"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_proof_built"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_requires_live_claims": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_requires_live_claims"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_rechecks_live_evidence_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_rechecks_live_evidence_digest"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_feeds_final_closeout_audit": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_feeds_final_closeout_audit"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_read_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_read_only"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_helper_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_helper_launch_enabled"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_settings_install_control_exposed"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_proof_built"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_injected_runner"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_live_download_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_live_download_approval"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_primary_replacement_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_primary_replacement_approval"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_builds_governed_evidence_packet": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_builds_governed_evidence_packet"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_default_live_download_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_default_live_download_enabled"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_default_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_default_installer_launch_enabled"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_default_primary_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_default_primary_replacement_enabled"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_settings_install_control_exposed"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_proof_built"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_signed_manifest_live_readback": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_signed_manifest_live_readback"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_live_download_staging": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_live_download_staging"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_downloaded_staged_signature_verification": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_downloaded_staged_signature_verification"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_installer_signed_output_verification": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_installer_signed_output_verification"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_primary_relaunch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_primary_relaunch_receipt_boundary"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_startup_background_prompt_verification": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_startup_background_prompt_verification"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_adapts_to_controlled_live_installer_evidence_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_adapts_to_controlled_live_installer_evidence_runner"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_builds_governed_evidence_packet": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_builds_governed_evidence_packet"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_download_performed_by_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_download_performed_by_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_installer_launch_performed_by_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_installer_launch_performed_by_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_primary_real_exe_replacement_performed_by_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_primary_real_exe_replacement_performed_by_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_settings_install_control_exposed"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_proof_built"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_collects_current_vault_source_proofs": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_collects_current_vault_source_proofs"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_requires_source_proof_readiness": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_requires_source_proof_readiness"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_adapts_to_approved_live_evidence_runner_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_adapts_to_approved_live_evidence_runner_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_can_preview_final_audit": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_can_preview_final_audit"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_download_performed_by_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_download_performed_by_dry_run"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_installer_launch_performed_by_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_installer_launch_performed_by_dry_run"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_primary_real_exe_replacement_performed_by_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_primary_real_exe_replacement_performed_by_dry_run"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_proof_built"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_collects_current_vault_source_proofs": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_collects_current_vault_source_proofs"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_normalizes_blocked_receipt_digests_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_normalizes_blocked_receipt_digests_only"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_download_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_download_performed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_installer_launch_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_installer_launch_performed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_primary_real_exe_replacement_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_primary_real_exe_replacement_performed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_proof_built"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_requires_external_receipt_bundle": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_requires_external_receipt_bundle"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_requires_all_six_source_receipts": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_requires_all_six_source_receipts"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_rechecks_bundle_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_rechecks_bundle_digest"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_feeds_approved_real_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_feeds_approved_real_dry_run"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_download_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_download_performed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_installer_launch_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_installer_launch_performed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_primary_real_exe_replacement_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_primary_real_exe_replacement_performed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_settings_install_control_exposed"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_proof_built"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_requires_injected_runner"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_live_action_approvals": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_requires_live_action_approvals"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_produces_external_receipt_bundle": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_produces_external_receipt_bundle"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_feeds_real_live_receipt_capture_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_feeds_real_live_receipt_capture_boundary"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_download_enabled_by_default"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_proof_built"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_requires_ready_production_runner_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_requires_ready_production_runner_proof"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_requires_primary_closeout_after_source_recovery": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_requires_primary_closeout_after_source_recovery"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_runner_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_rechecks_runner_digest"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_governed_packet_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_rechecks_governed_packet_digest"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_feeds_final_closeout_audit": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_feeds_final_closeout_audit"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_download_enabled_by_default"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_settings_install_control_exposed"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_proof_built"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_in_vault_evidence_root": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_requires_in_vault_evidence_root"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_explicit_file_read_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_requires_explicit_file_read_flag"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_runner_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_rechecks_runner_digest"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_primary_closeout_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_rechecks_primary_closeout_digest"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_feeds_final_closeout_bridge": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_feeds_final_closeout_bridge"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_download_enabled_by_default"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_built"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_requires_exact_installer_name": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_requires_exact_installer_name"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_requires_build_script_studio_hash_guard": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_requires_build_script_studio_hash_guard"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_signature_probe_required_for_signed_output": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_signature_probe_required_for_signed_output"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_download_enabled_by_default"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_settings_install_control_exposed"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_proof_built"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_both_artifacts": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_both_artifacts"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_studio_dist": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_isolated_studio_dist"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_installer_dist": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_isolated_installer_dist"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_cross_artifact_hash_guards": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_cross_artifact_hash_guards"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_download_enabled_by_default"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_proof_built"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_dist_artifact_isolation_cohabitation": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_dist_artifact_isolation_cohabitation"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_signature_probe": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_signature_probe"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_studio_signed_output": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_studio_signed_output"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_installer_signed_output": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_installer_signed_output"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_rechecks_artifact_hashes": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_rechecks_artifact_hashes"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_rejects_secret_like_signature_probe": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_rejects_secret_like_signature_probe"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_download_enabled_by_default"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_settings_install_control_exposed"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_proof_built"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_requires_import_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_requires_import_boundary"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_rechecks_import_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_rechecks_import_digest"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_revalidates_imported_candidate_hashes": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_revalidates_imported_candidate_hashes"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_requires_supply_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_requires_supply_approval"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_requires_candidate_verification_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_requires_candidate_verification_approval"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_source_write_enabled"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_settings_write_control_exposed"
                )
            ),
            "launcher_updater_authoritative_candidate_supply_verification_after_import_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_authoritative_candidate_supply_verification_after_import_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_proof_built"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_requires_after_import_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_requires_after_import_proof"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_rechecks_after_import_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_rechecks_after_import_digest"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_reuses_wrapper_removal_executor": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_reuses_wrapper_removal_executor"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_requires_explicit_source_write_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_requires_explicit_source_write_flag"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_settings_write_control_exposed"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_after_import_execution_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_boundary_proof_built"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_requires_supply_packet": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_requires_supply_packet"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_requires_candidate_verification": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_requires_candidate_verification"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_requires_explicit_source_write_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_requires_explicit_source_write_flag"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_decompiler_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_decompiler_execution_enabled"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_settings_write_control_exposed"
                )
            ),
            "launcher_updater_current_vault_wrapper_removal_executor_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_current_vault_wrapper_removal_executor_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_requires_external_receipt"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_dry_run_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_plan_consumption_dry_run_built")
            ),
            "launcher_updater_helper_plan_consumption_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_audit_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_audit_write_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_audit_envelope_proof_built")
            ),
            "launcher_updater_helper_audit_envelope_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_audit_envelope_write_enabled")
            ),
            "launcher_updater_helper_audit_envelope_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_audit_envelope_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_built"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_approval_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_proof_built"
                )
            ),
            "launcher_github_release_publication_approval_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_requires_exact_operator_statement"
                )
            ),
            "launcher_github_release_publication_approval_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_approval_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_execution_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_proof_built"
                )
            ),
            "launcher_github_release_publication_execution_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_requires_injected_runner"
                )
            ),
            "launcher_github_release_publication_execution_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_execution_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_execution_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_proof_built"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_requires_exact_operator_statement"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_requires_credential_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_requires_credential_boundary"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_proof_built"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_requires_injected_runner"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_no_network_harness_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_no_network_harness_only"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_proof_built"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_requires_credential_reference": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_requires_credential_reference"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_reads_secret_values_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_reads_secret_values_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_proof_built"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_requires_injected_runner"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_reads_secret_values_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_reads_secret_values_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_github_api_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_github_api_performed"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_asset_upload_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_asset_upload_performed"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_proof_built"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_requires_external_receipt"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_reads_secret_values_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_reads_secret_values_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_invokes_network_from_chaseos": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_invokes_network_from_chaseos"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_github_api_performed_by_chaseos": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_github_api_performed_by_chaseos"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_release_manifest_live_readback_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_proof_built"
                )
            ),
            "launcher_signed_release_manifest_live_readback_requires_published_manifest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_requires_published_manifest"
                )
            ),
            "launcher_signed_release_manifest_live_readback_performs_network_from_chaseos": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_performs_network_from_chaseos"
                )
            ),
            "launcher_signed_release_manifest_live_readback_download_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_download_enabled"
                )
            ),
            "launcher_signed_release_manifest_live_readback_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_installer_launch_enabled"
                )
            ),
            "launcher_signed_release_manifest_live_readback_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_proof_built"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_requires_signed_manifest_live_readback": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_requires_signed_manifest_live_readback"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_network_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_network_performed"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_download_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_download_enabled"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_staging_writes_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_staging_writes_enabled"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_proof_built"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_requires_signed_manifest_downloader_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_requires_signed_manifest_downloader_dry_run"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_requires_injected_downloader": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_requires_injected_downloader"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_writes_enabled_in_settings"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_installer_launch_enabled"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_proof_built"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_approved_live_download_staging": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_requires_approved_live_download_staging"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_injected_verifier": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_requires_injected_verifier"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_writes_enabled_in_settings"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_installer_launch_enabled"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_real_exe_replacement_enabled"
                )
            ),
            "personal_context_import_missing_hub_count": int(
                (personal_context_import.get("summary") or {}).get("missing_required_hub_count") or 0
            ),
            "personal_context_import_pipeline_stage_count": int(
                (personal_context_import.get("summary") or {}).get("pipeline_stage_count") or 0
            ),
            "attention_count": len(settings_summary.get("attention_items") or []),
        },
        "config_status": {
            "config_path": config.get("config_path") or validation.get("config_path"),
            "config_present": bool(config.get("config_present", True)),
            "validation_ok": bool(validation.get("ok")),
            "validation_posture": validation.get("posture"),
            "issue_count": len(validation.get("issues") or []),
            "issues": list(validation.get("issues") or []),
            "non_secret_config_only": bool(governance.get("non_secret_config_only")),
            "secrets_allowed_in_config": bool(governance.get("secrets_allowed_in_config")),
            "config_grants_authority": bool(governance.get("config_grants_authority")),
            "gate_overrides_config": bool(governance.get("gate_overrides_config")),
        },
        "provider_status": {
            "default_provider": provider_summary.get("default_provider") or {},
            "providers": provider_rows,
        },
        "provider_readiness": provider_readiness,
        "runtime_status": {
            "default_runtime": runtime_summary.get("default_runtime") or {},
            "known_runtimes": list(runtime_summary.get("known_runtimes") or []),
            "startup_surfaces": startup_rows,
            "gateway_controls": runtime_gateway_controls,
            "startup_read_only_model": bool(startup_model.get("read_only")),
            "startup_process_probe_enabled": bool(startup_model.get("process_probe_enabled")),
            "settings_write_enabled_in_backend": bool(startup_model.get("settings_write_enabled")),
            "mutation_actions_available_in_cli": bool(startup_model.get("mutation_actions_enabled")),
        },
        "capture_hotkeys": capture_hotkeys,
        "capture_collectors": capture_collectors,
        "capture_local_image_text": capture_image_text_settings,
        "launcher_update": launcher_update,
        "personal_context_import": personal_context_import,
        "preference_posture": {
            "operator_config_surface": "bounded .chaseos/config.yaml status only",
            "graph_preferences_surface": "local Studio graph settings modal state",
            "runtime_gateway_controls_surface": "local Studio runtime gateway preference state",
            "capture_shortcut_surface": "local Studio Capture shortcut preference state",
            "capture_collector_surface": "local Studio Capture collector preference state",
            "capture_local_image_text_surface": "local Studio image text extraction preference state",
            "personal_context_import_surface": "read-only import planner and storage/security route",
            "graph_preferences_are_canonical_vault_state": False,
            "native_settings_panel_writes_preferences": True,
            "secrets_displayed": False,
            "raw_credential_values_displayed": False,
        },
        "action_posture": action_posture,
        "authority": authority,
        "approval_boundary": approval_boundary,
        "security": {
            "secret_values_included": False,
            "raw_credentials_included": False,
            "sensitive_key_scan_passed": not _contains_sensitive_key(
                {
                    "summary": provider_rows,
                    "startup_surfaces": startup_rows,
                    "runtime_gateway_controls": runtime_gateway_controls.get("runtimes") or [],
                    "config_status": {
                        "validation_posture": validation.get("posture"),
                        "issue_count": len(validation.get("issues") or []),
                    },
                }
            ),
        },
        "native_panel": {
            "mounted": True,
            "panel_id": "settings",
            "frontend_target": "panel-settings",
            "route_hint": "#settings",
            "read_only": False,
            "status": "mounted-runtime-controls-active",
        },
        "readiness": {
            "settings_runtime_controls_panel_mounted": True,
            "runtime_startup_status_visible": True,
            "runtime_gateway_controls_visible": True,
            "runtime_gateway_controls_write_preferences_enabled": bool(
                (runtime_gateway_controls.get("authority") or {}).get("writes_studio_preferences")
            ),
            "runtime_gateway_controls_start_stop_enabled": bool(
                (runtime_gateway_controls.get("authority") or {}).get("starts_gateways")
            ),
            "capture_shortcut_settings_visible": bool(
                (capture_hotkeys.get("readiness") or {}).get("settings_page_visible")
            ),
            "capture_local_image_text_settings_visible": bool(
                (capture_image_text_settings.get("readiness") or {}).get("settings_page_visible")
            ),
            "capture_collector_settings_visible": bool(
                (capture_collectors.get("readiness") or {}).get("settings_page_visible")
            ),
            "capture_screen_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get("screen_capture_collector_built")
            ),
            "capture_screen_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get("screen_capture_enabled")
            ),
            "capture_screen_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get("screen_capture_requires_operator_click")
            ),
            "capture_screen_collector_writes_evidence_only": bool(
                (capture_collectors.get("readiness") or {}).get("screen_capture_writes_evidence_only")
            ),
            "capture_display_region_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "display_region_capture_collector_built"
                )
            ),
            "capture_display_region_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "display_region_capture_enabled"
                )
            ),
            "capture_display_region_collector_requires_operator_drag": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "display_region_capture_requires_operator_drag"
                )
            ),
            "capture_display_region_collector_writes_evidence_only": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "display_region_capture_writes_evidence_only"
                )
            ),
            "capture_active_window_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_window_capture_collector_built"
                )
            ),
            "capture_active_window_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_window_capture_enabled"
                )
            ),
            "capture_active_window_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_window_capture_requires_operator_click"
                )
            ),
            "capture_active_window_collector_writes_evidence_only": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_window_capture_writes_evidence_only"
                )
            ),
            "capture_clipboard_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get("clipboard_capture_collector_built")
            ),
            "capture_clipboard_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get("clipboard_capture_enabled")
            ),
            "capture_clipboard_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get("clipboard_capture_requires_operator_click")
            ),
            "capture_clipboard_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get("clipboard_capture_writes_no_markdown_on_click")
            ),
            "capture_ambient_clipboard_monitor_built": bool(
                (capture_collectors.get("readiness") or {}).get("ambient_clipboard_monitor_built")
            ),
            "capture_ambient_clipboard_monitor_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "ambient_clipboard_monitoring_enabled"
                )
            ),
            "capture_ambient_clipboard_monitor_requires_privacy_opt_in": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "ambient_clipboard_monitor_requires_privacy_opt_in"
                )
            ),
            "capture_ambient_clipboard_monitor_writes_no_markdown_on_poll": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "ambient_clipboard_monitor_writes_no_markdown_on_poll"
                )
            ),
            "capture_selected_text_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "selected_text_capture_collector_built"
                )
            ),
            "capture_selected_text_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "selected_text_capture_enabled"
                )
            ),
            "capture_selected_text_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "selected_text_capture_requires_operator_click"
                )
            ),
            "capture_selected_text_collector_uses_temporary_clipboard_copy": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "selected_text_capture_uses_temporary_clipboard_copy"
                )
            ),
            "capture_selected_text_collector_restores_text_clipboard_when_possible": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "selected_text_capture_restores_text_clipboard_when_possible"
                )
            ),
            "capture_selected_text_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "selected_text_capture_writes_no_markdown_on_click"
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
            "capture_accessibility_tree_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "accessibility_tree_capture_requires_operator_click"
                )
            ),
            "capture_accessibility_tree_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "accessibility_tree_capture_writes_no_markdown_on_click"
                )
            ),
            "capture_browser_artifact_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_artifact_capture_collector_built"
                )
            ),
            "capture_browser_artifact_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_artifact_capture_enabled"
                )
            ),
            "capture_browser_artifact_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_artifact_capture_requires_operator_click"
                )
            ),
            "capture_browser_artifact_collector_requires_operator_selected_file": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_artifact_capture_requires_operator_selected_file"
                )
            ),
            "capture_browser_artifact_collector_requires_declared_url": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_artifact_capture_requires_declared_url"
                )
            ),
            "capture_browser_artifact_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_artifact_capture_writes_no_markdown_on_click"
                )
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
            "capture_browser_extension_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_extension_capture_requires_operator_click"
                )
            ),
            "capture_browser_extension_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "browser_extension_capture_writes_no_markdown_on_click"
                )
            ),
            "capture_active_chaseos_browser_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_chaseos_browser_capture_collector_built"
                )
            ),
            "capture_active_chaseos_browser_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_chaseos_browser_capture_enabled"
                )
            ),
            "capture_active_chaseos_browser_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_chaseos_browser_capture_requires_operator_click"
                )
            ),
            "capture_active_chaseos_browser_collector_reads_chaseos_state": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_chaseos_browser_capture_reads_chaseos_state"
                )
            ),
            "capture_active_chaseos_browser_collector_reads_personal_browser": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_chaseos_browser_capture_reads_personal_browser"
                )
            ),
            "capture_active_chaseos_browser_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "active_chaseos_browser_capture_writes_no_markdown_on_click"
                )
            ),
            "capture_chaseos_browser_page_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "chaseos_browser_page_capture_collector_built"
                )
            ),
            "capture_chaseos_browser_page_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "chaseos_browser_page_capture_enabled"
                )
            ),
            "capture_chaseos_browser_page_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "chaseos_browser_page_capture_requires_operator_click"
                )
            ),
            "capture_chaseos_browser_page_collector_requires_declared_url": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "chaseos_browser_page_capture_requires_declared_url"
                )
            ),
            "capture_chaseos_browser_page_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "chaseos_browser_page_capture_writes_no_markdown_on_click"
                )
            ),
            "capture_discord_artifact_collector_built": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "discord_artifact_capture_collector_built"
                )
            ),
            "capture_discord_artifact_collector_enabled": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "discord_artifact_capture_enabled"
                )
            ),
            "capture_discord_artifact_collector_requires_operator_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "discord_artifact_capture_requires_operator_click"
                )
            ),
            "capture_discord_artifact_collector_requires_operator_selected_file": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "discord_artifact_capture_requires_operator_selected_file"
                )
            ),
            "capture_discord_artifact_collector_requires_declared_source": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "discord_artifact_capture_requires_declared_source"
                )
            ),
            "capture_discord_artifact_collector_writes_no_markdown_on_click": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "discord_artifact_capture_writes_no_markdown_on_click"
                )
            ),
            "capture_discord_artifact_collector_calls_discord_api": bool(
                (capture_collectors.get("readiness") or {}).get(
                    "discord_artifact_capture_calls_discord_api"
                )
            ),
            "capture_local_image_text_preferences_write_enabled": bool(
                (capture_image_text_settings.get("authority") or {}).get("writes_studio_preferences")
            ),
            "capture_local_image_text_command_configurable": bool(
                (capture_image_text_settings.get("readiness") or {}).get("local_command_configurable")
            ),
            "capture_local_image_text_quality_fixture_runner_available": bool(
                (capture_image_text_settings.get("readiness") or {}).get("quality_fixture_runner_available")
            ),
            "capture_local_image_text_real_engine_quality_verified": bool(
                (capture_image_text_settings.get("readiness") or {}).get("real_engine_quality_verified")
            ),
            "capture_local_image_text_cloud_blocked": bool(
                (capture_image_text_settings.get("readiness") or {}).get("cloud_optical_character_recognition_blocked")
            ),
            "capture_shortcut_preferences_write_enabled": bool(
                (capture_hotkeys.get("authority") or {}).get("writes_studio_preferences")
            ),
            "capture_studio_window_shortcuts_configurable": bool(
                (capture_hotkeys.get("readiness") or {}).get("studio_window_shortcuts_configurable")
            ),
            "capture_studio_window_collector_shortcuts_configurable": bool(
                (capture_hotkeys.get("readiness") or {}).get(
                    "studio_window_collector_shortcuts_configurable"
                )
            ),
            "capture_global_hotkey_registration_blocked": bool(
                (capture_hotkeys.get("readiness") or {}).get("global_hotkey_registration_blocked")
            ),
            "capture_selected_text_shortcut_blocked": bool(
                (capture_hotkeys.get("readiness") or {}).get("selected_text_capture_blocked")
            ),
            "capture_screen_shortcut_blocked": bool(
                (capture_hotkeys.get("readiness") or {}).get("screen_capture_blocked")
            ),
            "provider_config_status_visible": True,
            "provider_readiness_visible": True,
            "provider_live_probe_status_visible": True,
            "personal_context_import_visible": True,
            "personal_context_import_settings_entrypoint_ready": True,
            "personal_context_import_writes_blocked": bool(
                not (personal_context_import.get("readiness") or {}).get("live_import_writes_enabled")
            ),
            "preference_posture_visible": True,
            "confirmation_gated_actions_described": True,
            "launcher_update_check_visible": bool(
                (launcher_update.get("readiness") or {}).get("settings_update_check_visible")
            ),
            "launcher_current_version_visible": bool(
                (launcher_update.get("readiness") or {}).get("current_version_visible")
            ),
            "launcher_latest_available_version_visible": bool(
                (launcher_update.get("readiness") or {}).get("latest_available_version_visible")
            ),
            "launcher_download_or_install_controls_exposed": bool(
                (launcher_update.get("readiness") or {}).get("download_or_install_controls_exposed")
            ),
            "launcher_network_manifest_fetch_built": bool(
                (launcher_update.get("readiness") or {}).get("network_manifest_fetch_built")
            ),
            "launcher_network_manifest_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("network_manifest_default_enabled")
            ),
            "launcher_network_manifest_requires_operator_approval": bool(
                (launcher_update.get("readiness") or {}).get("network_manifest_fetch_requires_operator_approval")
            ),
            "launcher_download_staging_readiness_built": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_readiness_built")
            ),
            "launcher_download_staging_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_default_enabled")
            ),
            "launcher_download_staging_writes_enabled": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_writes_enabled")
            ),
            "launcher_download_staging_executor_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_executor_proof_built")
            ),
            "launcher_download_staging_executor_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_executor_default_enabled")
            ),
            "launcher_download_staging_executor_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("download_staging_executor_writes_enabled_in_settings")
            ),
            "launcher_signature_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_proof_built")
            ),
            "launcher_signature_verification_default_enabled": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_default_enabled")
            ),
            "launcher_signature_verification_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_writes_enabled_in_settings")
            ),
            "launcher_signature_verification_install_enabled": bool(
                (launcher_update.get("readiness") or {}).get("signature_verification_install_enabled")
            ),
            "launcher_updater_helper_readiness_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_readiness_built")
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_proof_built"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_verified_signature": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_requires_verified_signature"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_current_executable": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_requires_current_executable"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_from_verified_staged_signature_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_from_verified_staged_signature_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_plan_write_enabled")
            ),
            "launcher_updater_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_execution_enabled")
            ),
            "launcher_updater_helper_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_replacement_enabled")
            ),
            "launcher_updater_helper_temp_fixture_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_temp_fixture_proof_built")
            ),
            "launcher_updater_helper_temp_fixture_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_temp_fixture_writes_enabled_in_settings")
            ),
            "launcher_updater_helper_temp_fixture_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_temp_fixture_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_binary_design_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_design_built")
            ),
            "launcher_updater_helper_binary_build_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_build_enabled")
            ),
            "launcher_updater_helper_binary_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_execution_enabled")
            ),
            "launcher_updater_helper_binary_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_writes_enabled_in_settings")
            ),
            "launcher_updater_helper_binary_real_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_real_replacement_enabled")
            ),
            "launcher_updater_helper_binary_build_strategy_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_proof_built"
                )
            ),
            "launcher_updater_helper_binary_build_strategy_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_binary_build_strategy_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_execution_enabled"
                )
            ),
            "launcher_updater_helper_binary_build_strategy_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_build_strategy_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_binary_spec_scaffold_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_binary_spec_scaffold_built")
            ),
            "launcher_updater_helper_binary_spec_scaffold_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_spec_scaffold_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_binary_spec_scaffold_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_spec_scaffold_execution_enabled"
                )
            ),
            "launcher_updater_helper_binary_spec_scaffold_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_spec_scaffold_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_binary_static_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_proof_built"
                )
            ),
            "launcher_updater_helper_binary_static_verification_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_binary_static_verification_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_execution_enabled"
                )
            ),
            "launcher_updater_helper_binary_static_verification_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_binary_static_verification_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_plan_file_proof_built")
            ),
            "launcher_updater_helper_plan_file_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_plan_file_real_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_real_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_proof_built"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_requires_verified_staged_signature_plan": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_requires_verified_staged_signature_plan"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_file_from_signed_manifest_plan_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_executable_scaffold_built")
            ),
            "launcher_updater_helper_executable_scaffold_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_execution_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_executable_scaffold_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_proof_built"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_requires_signed_manifest_plan_file": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_requires_signed_manifest_plan_file"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_executable_scaffold_from_signed_manifest_plan_file_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_proof_built"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_requires_signed_manifest_scaffold": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_requires_signed_manifest_scaffold"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_audit_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_audit_write_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_from_signed_manifest_scaffold_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_proof_built"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_requires_signed_manifest_consumption": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_requires_signed_manifest_consumption"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_audit_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_audit_write_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_from_signed_manifest_consumption_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_proof_built"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_requires_signed_manifest_audit_envelope": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_requires_signed_manifest_audit_envelope"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_from_signed_manifest_envelope_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_proof_built"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_requires_signed_manifest_audit_write": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_requires_signed_manifest_audit_write"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_installer_launch_enabled"
                )
            ),
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_execution_dry_run_from_signed_manifest_audit_write_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_proof_built"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_requires_execution_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_requires_execution_dry_run"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_prompted_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_prompted_only"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_startup_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_startup_mutation_enabled"
                )
            ),
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_proof_built"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_requires_startup_background_prompt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_requires_startup_background_prompt"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_safe_dry_run_lane": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_safe_dry_run_lane"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_production_auto_update_complete": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_production_auto_update_complete"
                )
            ),
            "launcher_updater_end_to_end_dry_run_closeout_real_exe_replacement_complete": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_end_to_end_dry_run_closeout_real_exe_replacement_complete"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_proof_built"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_requires_closeout": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_requires_closeout"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_requires_disposable_target": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_requires_disposable_target"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_host_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_host_mutation_enabled"
                )
            ),
            "launcher_updater_production_host_mutation_approval_gate_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_host_mutation_approval_gate_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_proof_built"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_requires_approval_gate": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_requires_approval_gate"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_disposable_target_scope_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_disposable_target_scope_only"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_external_helper_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_external_helper_launch_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_execution_boundary_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_execution_boundary_settings_install_control_exposed"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_execution_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_requires_execution_boundary"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_injected_launcher": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_requires_injected_launcher"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_uses_chaseos_installer": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_uses_chaseos_installer"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_os_process_spawn_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_os_process_spawn_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_helper_launch_receipt_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_helper_launch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_requires_helper_launch_receipt_boundary"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_requires_external_receipt"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_chaseos_relaunch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_chaseos_relaunch_enabled"
                )
            ),
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_disposable_target_relaunch_receipt_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_proof_built"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_requires_relaunch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_requires_relaunch_receipt_boundary"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_requires_primary_executable_descriptor": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_requires_primary_executable_descriptor"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_future_mutation_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_future_mutation_only"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_primary_install_mutation_gate_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_install_mutation_gate_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_proof_built"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_requires_primary_install_mutation_gate": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_requires_primary_install_mutation_gate"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_writes_rollback_copy": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_writes_rollback_copy"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_writes_audit_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_writes_audit_receipt"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_primary_install_mutation_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_primary_install_mutation_enabled"
                )
            ),
            "launcher_updater_production_primary_rollback_audit_boundary_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_rollback_audit_boundary_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_primary_rollback_audit_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_requires_primary_rollback_audit_boundary"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_replacement_artifact_descriptor": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_requires_replacement_artifact_descriptor"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_requires_external_receipt"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_chaseos_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_chaseos_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_replacement_receipt_boundary_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_replacement_receipt_boundary_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_source_recovery_cleanup_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_proof_built"
                )
            ),
            "launcher_updater_source_recovery_cleanup_hash_pinning_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_recovery_bytecode_hash_pinning_enabled"
                )
            ),
            "launcher_updater_source_recovery_cleanup_normal_source_restoration_required": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_normal_source_restoration_required"
                )
            ),
            "launcher_updater_source_recovery_cleanup_final_closeout_blocked": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_recovery_cleanup_final_auto_update_closeout_blocked_until_source_restored"
                )
            ),
            "launcher_updater_normal_source_restoration_readiness_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_readiness_proof_built"
                )
            ),
            "launcher_updater_normal_source_restoration_requires_wrapper_removal": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_requires_wrapper_removal"
                )
            ),
            "launcher_updater_normal_source_restoration_requires_authoritative_candidate": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_requires_authoritative_candidate"
                )
            ),
            "launcher_updater_normal_source_restoration_final_closeout_blocked": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_restoration_final_auto_update_closeout_blocked_until_source_restored"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_proof_built"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_source_write_enabled"
                )
            ),
            "launcher_updater_normal_source_candidate_verification_source_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_verification_source_replacement_enabled"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_proof_built"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_source_write_enabled_with_explicit_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_source_write_enabled_with_explicit_approval"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_settings_write_control_exposed"
                )
            ),
            "launcher_updater_normal_source_candidate_restore_executor_decompiler_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_normal_source_candidate_restore_executor_decompiler_enabled"
                )
            ),
            "launcher_updater_source_regeneration_readiness_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_readiness_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_requires_local_decompiler_or_operator_source": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_requires_local_decompiler_or_operator_source"
                )
            ),
            "launcher_updater_source_regeneration_decompiler_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_decompiler_execution_enabled"
                )
            ),
            "launcher_updater_source_regeneration_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_source_write_enabled"
                )
            ),
            "launcher_updater_source_regeneration_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_runner_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_boundary_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_runner_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_requires_injected_runner"
                )
            ),
            "launcher_updater_source_regeneration_runner_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_source_regeneration_runner_candidate_writes_enabled_with_explicit_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_candidate_writes_enabled_with_explicit_approval"
                )
            ),
            "launcher_updater_source_regeneration_runner_live_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_live_source_write_enabled"
                )
            ),
            "launcher_updater_source_regeneration_runner_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_runner_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_runner_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_runner_boundary"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_candidate_verification_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_candidate_verification_statement"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_restore_root": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_restore_root"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_requires_restore_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_requires_restore_statement"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_candidate_restore_chain_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_candidate_restore_chain_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_proof_built"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_requires_live_restore_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_requires_live_restore_proof"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_scans_wrapper_tokens": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_scans_wrapper_tokens"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_settings_write_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_settings_write_control_exposed"
                )
            ),
            "launcher_updater_source_regeneration_live_source_restoration_closeout_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_source_regeneration_live_source_restoration_closeout_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_proof_built"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_current_vault_source_closeout": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_requires_current_vault_source_closeout"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_source_closeout_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_rechecks_source_closeout_digest"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_primary_relaunch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_requires_primary_relaunch_receipt_boundary"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_primary_relaunch_receipt_boundary_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_rechecks_primary_relaunch_receipt_boundary_digest"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_external_chaseos_installer_primary_relaunch_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_requires_external_chaseos_installer_primary_relaunch_receipt"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_source_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_source_write_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_helper_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_helper_launch_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_production_primary_closeout_after_source_recovery_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_closeout_after_source_recovery_settings_install_control_exposed"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_proof_built"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_production_primary_closeout_after_source_recovery": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_production_primary_closeout_after_source_recovery"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_primary_closeout_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_rechecks_primary_closeout_digest"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_live_completion_evidence": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_live_completion_evidence"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_live_evidence_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_rechecks_live_evidence_digest"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_primary_replacement_verified_live": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_primary_replacement_verified_live"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_requires_startup_background_prompt_verified": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_requires_startup_background_prompt_verified"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_read_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_read_only"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_helper_launch_enabled_by_this_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_helper_launch_enabled_by_this_proof"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_primary_real_exe_replacement_enabled_by_this_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_primary_real_exe_replacement_enabled_by_this_proof"
                )
            ),
            "launcher_updater_final_production_auto_update_closeout_audit_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_final_production_auto_update_closeout_audit_settings_install_control_exposed"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_proof_built"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_requires_live_claims": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_requires_live_claims"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_rechecks_live_evidence_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_rechecks_live_evidence_digest"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_feeds_final_closeout_audit": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_feeds_final_closeout_audit"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_read_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_read_only"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_helper_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_helper_launch_enabled"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_governed_live_completion_evidence_packet_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_governed_live_completion_evidence_packet_settings_install_control_exposed"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_proof_built"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_injected_runner"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_live_download_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_live_download_approval"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_requires_primary_replacement_approval": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_requires_primary_replacement_approval"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_builds_governed_evidence_packet": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_builds_governed_evidence_packet"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_default_live_download_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_default_live_download_enabled"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_default_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_default_installer_launch_enabled"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_default_primary_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_default_primary_replacement_enabled"
                )
            ),
            "launcher_updater_controlled_live_installer_evidence_runner_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_controlled_live_installer_evidence_runner_settings_install_control_exposed"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_proof_built"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_signed_manifest_live_readback": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_signed_manifest_live_readback"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_live_download_staging": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_live_download_staging"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_downloaded_staged_signature_verification": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_downloaded_staged_signature_verification"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_installer_signed_output_verification": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_installer_signed_output_verification"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_primary_relaunch_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_primary_relaunch_receipt_boundary"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_requires_startup_background_prompt_verification": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_requires_startup_background_prompt_verification"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_adapts_to_controlled_live_installer_evidence_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_adapts_to_controlled_live_installer_evidence_runner"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_builds_governed_evidence_packet": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_builds_governed_evidence_packet"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_download_performed_by_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_download_performed_by_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_installer_launch_performed_by_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_installer_launch_performed_by_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_primary_real_exe_replacement_performed_by_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_primary_real_exe_replacement_performed_by_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_adapter_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_adapter_settings_install_control_exposed"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_proof_built"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_collects_current_vault_source_proofs": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_collects_current_vault_source_proofs"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_requires_source_proof_readiness": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_requires_source_proof_readiness"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_requires_exact_operator_statement"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_adapts_to_approved_live_evidence_runner_adapter": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_adapts_to_approved_live_evidence_runner_adapter"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_can_preview_final_audit": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_can_preview_final_audit"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_download_performed_by_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_download_performed_by_dry_run"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_installer_launch_performed_by_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_installer_launch_performed_by_dry_run"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_primary_real_exe_replacement_performed_by_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_primary_real_exe_replacement_performed_by_dry_run"
                )
            ),
            "launcher_updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_proof_built"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_collects_current_vault_source_proofs": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_collects_current_vault_source_proofs"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_normalizes_blocked_receipt_digests_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_normalizes_blocked_receipt_digests_only"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_download_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_download_performed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_installer_launch_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_installer_launch_performed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_primary_real_exe_replacement_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_primary_real_exe_replacement_performed"
                )
            ),
            "launcher_updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_proof_built"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_requires_external_receipt_bundle": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_requires_external_receipt_bundle"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_requires_all_six_source_receipts": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_requires_all_six_source_receipts"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_rechecks_bundle_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_rechecks_bundle_digest"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_feeds_approved_real_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_feeds_approved_real_dry_run"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_download_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_download_performed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_installer_launch_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_installer_launch_performed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_primary_real_exe_replacement_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_primary_real_exe_replacement_performed"
                )
            ),
            "launcher_updater_real_live_receipt_capture_boundary_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_capture_boundary_settings_install_control_exposed"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_proof_built"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_requires_injected_runner"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_live_action_approvals": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_requires_live_action_approvals"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_produces_external_receipt_bundle": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_produces_external_receipt_bundle"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_feeds_real_live_receipt_capture_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_feeds_real_live_receipt_capture_boundary"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_download_enabled_by_default"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_proof_built"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_requires_ready_production_runner_proof": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_requires_ready_production_runner_proof"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_requires_primary_closeout_after_source_recovery": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_requires_primary_closeout_after_source_recovery"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_runner_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_rechecks_runner_digest"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_governed_packet_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_rechecks_governed_packet_digest"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_feeds_final_closeout_audit": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_feeds_final_closeout_audit"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_download_enabled_by_default"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_production_runner_final_closeout_bridge_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_runner_final_closeout_bridge_settings_install_control_exposed"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_proof_built"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_in_vault_evidence_root": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_requires_in_vault_evidence_root"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_explicit_file_read_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_requires_explicit_file_read_flag"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_runner_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_rechecks_runner_digest"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_primary_closeout_digest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_rechecks_primary_closeout_digest"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_feeds_final_closeout_bridge": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_feeds_final_closeout_bridge"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_download_enabled_by_default"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_built"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_requires_exact_installer_name": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_requires_exact_installer_name"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_requires_build_script_studio_hash_guard": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_requires_build_script_studio_hash_guard"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_signature_probe_required_for_signed_output": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_signature_probe_required_for_signed_output"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_download_enabled_by_default"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_installer_real_artifact_build_output_capture_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_installer_real_artifact_build_output_capture_settings_install_control_exposed"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_proof_built"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_both_artifacts": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_both_artifacts"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_studio_dist": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_isolated_studio_dist"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_installer_dist": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_isolated_installer_dist"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_cross_artifact_hash_guards": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_requires_cross_artifact_hash_guards"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_download_enabled_by_default"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_proof_built"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_dist_artifact_isolation_cohabitation": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_dist_artifact_isolation_cohabitation"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_signature_probe": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_signature_probe"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_studio_signed_output": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_studio_signed_output"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_requires_installer_signed_output": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_requires_installer_signed_output"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_rechecks_artifact_hashes": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_rechecks_artifact_hashes"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_rejects_secret_like_signature_probe": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_rejects_secret_like_signature_probe"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_download_enabled_by_default"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_signed_artifact_verification_closeout_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_signed_artifact_verification_closeout_settings_install_control_exposed"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_proof_built"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_requires_plan_file": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_requires_plan_file"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_requires_disposable_target_root": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_requires_disposable_target_root"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_requires_explicit_execution_flag": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_requires_explicit_execution_flag"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_uses_chaseos_installer": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_uses_chaseos_installer"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_creates_backup": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_creates_backup"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_writes_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_writes_receipt"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_blocks_primary_dist_target": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_blocks_primary_dist_target"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_live_install_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_live_install_enabled_by_default"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_local_installer_disposable_dry_run_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_installer_disposable_dry_run_settings_install_control_exposed"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_proof_built"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_requires_manifest_file": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_requires_manifest_file"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_validates_manifest_schema": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_validates_manifest_schema"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_compares_current_latest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_compares_current_latest"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_prompted_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_prompted_only"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_background_poll_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_background_poll_enabled_by_default"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_download_enabled_by_default"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_local_manifest_background_prompt_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_manifest_background_prompt_settings_install_control_exposed"
                )
            ),
            "launcher_updater_local_release_channel_blocker_closeout_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_release_channel_blocker_closeout_proof_built"
                )
            ),
            "launcher_updater_local_release_channel_blocker_closeout_classifies_external_blockers": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_release_channel_blocker_closeout_classifies_external_blockers"
                )
            ),
            "launcher_updater_local_release_channel_blocker_closeout_download_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_release_channel_blocker_closeout_download_enabled_by_default"
                )
            ),
            "launcher_updater_local_release_channel_blocker_closeout_installer_launch_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_release_channel_blocker_closeout_installer_launch_enabled_by_default"
                )
            ),
            "launcher_updater_local_release_channel_blocker_closeout_primary_replacement_enabled_by_default": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_release_channel_blocker_closeout_primary_replacement_enabled_by_default"
                )
            ),
            "launcher_updater_local_release_channel_blocker_closeout_settings_install_control_exposed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_local_release_channel_blocker_closeout_settings_install_control_exposed"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_proof_built"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_requires_external_receipt"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled"
                )
            ),
            "launcher_updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_dry_run_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_plan_consumption_dry_run_built")
            ),
            "launcher_updater_helper_plan_consumption_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_execution_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_audit_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_audit_write_enabled"
                )
            ),
            "launcher_updater_helper_plan_consumption_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_plan_consumption_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_proof_built": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_audit_envelope_proof_built")
            ),
            "launcher_updater_helper_audit_envelope_write_enabled": bool(
                (launcher_update.get("readiness") or {}).get("updater_helper_audit_envelope_write_enabled")
            ),
            "launcher_updater_helper_audit_envelope_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_audit_envelope_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_real_exe_replacement_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_built"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_writes_enabled_in_settings"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_helper_execution_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_helper_execution_enabled"
                )
            ),
            "launcher_updater_helper_audit_envelope_write_proof_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "updater_helper_audit_envelope_write_proof_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_approval_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_proof_built"
                )
            ),
            "launcher_github_release_publication_approval_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_requires_exact_operator_statement"
                )
            ),
            "launcher_github_release_publication_approval_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_approval_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_approval_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_execution_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_proof_built"
                )
            ),
            "launcher_github_release_publication_execution_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_requires_injected_runner"
                )
            ),
            "launcher_github_release_publication_execution_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_execution_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_execution_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_execution_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_proof_built"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_requires_exact_operator_statement": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_requires_exact_operator_statement"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_requires_credential_boundary": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_requires_credential_boundary"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_approval_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_approval_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_proof_built"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_requires_injected_runner"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_no_network_harness_only": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_no_network_harness_only"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_live_runner_execution_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_runner_execution_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_proof_built"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_requires_credential_reference": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_requires_credential_reference"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_reads_secret_values_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_reads_secret_values_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_github_api_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_github_api_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_asset_upload_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_asset_upload_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_activation_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_activation_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_proof_built"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_requires_injected_runner": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_requires_injected_runner"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_reads_secret_values_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_reads_secret_values_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_github_api_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_github_api_performed"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_asset_upload_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_asset_upload_performed"
                )
            ),
            "launcher_github_release_publication_live_github_runner_execution_contract_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_execution_contract_real_exe_replacement_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_proof_built"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_requires_external_receipt": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_requires_external_receipt"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_reads_secret_values_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_reads_secret_values_enabled"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_invokes_network_from_chaseos": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_invokes_network_from_chaseos"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_github_api_performed_by_chaseos": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_github_api_performed_by_chaseos"
                )
            ),
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "github_release_publication_live_github_runner_real_execution_boundary_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_release_manifest_live_readback_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_proof_built"
                )
            ),
            "launcher_signed_release_manifest_live_readback_requires_published_manifest": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_requires_published_manifest"
                )
            ),
            "launcher_signed_release_manifest_live_readback_performs_network_from_chaseos": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_performs_network_from_chaseos"
                )
            ),
            "launcher_signed_release_manifest_live_readback_download_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_download_enabled"
                )
            ),
            "launcher_signed_release_manifest_live_readback_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_installer_launch_enabled"
                )
            ),
            "launcher_signed_release_manifest_live_readback_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_release_manifest_live_readback_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_proof_built"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_requires_signed_manifest_live_readback": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_requires_signed_manifest_live_readback"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_network_performed": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_network_performed"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_download_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_download_enabled"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_staging_writes_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_staging_writes_enabled"
                )
            ),
            "launcher_signed_manifest_downloader_dry_run_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloader_dry_run_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_proof_built"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_requires_signed_manifest_downloader_dry_run": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_requires_signed_manifest_downloader_dry_run"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_requires_injected_downloader": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_requires_injected_downloader"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_writes_enabled_in_settings"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_installer_launch_enabled"
                )
            ),
            "launcher_signed_manifest_approved_live_download_staging_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_approved_live_download_staging_real_exe_replacement_enabled"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_proof_built": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_proof_built"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_approved_live_download_staging": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_requires_approved_live_download_staging"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_injected_verifier": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_requires_injected_verifier"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_writes_enabled_in_settings": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_writes_enabled_in_settings"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_installer_launch_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_installer_launch_enabled"
                )
            ),
            "launcher_signed_manifest_downloaded_staged_signature_verification_real_exe_replacement_enabled": bool(
                (launcher_update.get("readiness") or {}).get(
                    "signed_manifest_downloaded_staged_signature_verification_real_exe_replacement_enabled"
                )
            ),
            "native_ui_mutation_controls_built": False,
            "secrets_hidden": True,
            "no_authority_expansion": True,
            "next_recommended_pass": "phase11-provider-routing-foundation",
        },
        "allowed_actions": ["inspect-settings-runtime-controls-panel"],
        "possible_writes": [],
        "errors": list(startup_model.get("errors") or []),
    }
    return model
