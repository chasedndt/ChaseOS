"""Tests for the native Studio Settings + Runtime Controls panel."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from runtime.studio.settings_runtime_controls_panel import build_settings_runtime_controls_panel


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_settings_runtime_controls_panel_exposes_runtime_gateway_actions() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    assert panel["ok"] is True
    assert panel["surface"] == "studio_settings_runtime_controls_panel"
    assert panel["read_only"] is False
    assert panel["native_panel"]["mounted"] is True
    assert panel["native_panel"]["panel_id"] == "settings"
    assert panel["authority"]["read_only"] is False
    assert panel["authority"]["possible_writes"] == [
        "runtime_gateway_control_preferences",
        "runtime_lifecycle_run",
        "capture_shortcut_preferences",
        "capture_collector_preferences",
        "capture_local_image_text_preferences",
    ]
    assert panel["authority"]["writes_config"] is False
    assert panel["authority"]["writes_provider_target_profile"] is False
    assert panel["authority"]["provider_switch_allowed"] is False
    assert panel["authority"]["executes_live_provider_probe"] is False
    assert panel["authority"]["writes_host_startup"] is True
    assert panel["authority"]["startup_mutation_allowed"] is True
    assert panel["authority"]["executes_runtime_actions"] is True
    assert panel["authority"]["writes_capture_shortcut_preferences"] is True
    assert panel["authority"]["writes_capture_collector_preferences"] is True
    assert panel["authority"]["registers_global_hotkeys"] is False
    assert panel["authority"]["runs_capture_collectors_from_global_hotkeys"] is False
    assert panel["authority"]["starts_subprocesses_on_settings_load"] is False
    assert panel["authority"]["runs_shell_commands_on_settings_load"] is False
    assert panel["authority"]["runs_capture_collectors_from_studio_shortcuts"] is True
    assert panel["authority"]["captures_screen_pixels"] is False
    assert panel["authority"]["captures_screen_pixels_on_settings_load"] is False
    assert panel["authority"]["reads_clipboard_on_settings_load"] is False
    assert panel["authority"]["reads_clipboard_on_capture_panel_load"] is False
    assert panel["authority"]["reads_active_browser_tab"] is False
    assert panel["authority"]["reads_personal_active_browser_tab"] is False
    assert panel["authority"]["reads_controlled_browser_artifact_on_settings_load"] is False
    assert panel["authority"]["reads_controlled_browser_artifact_on_capture_panel_load"] is False
    assert panel["authority"]["reads_chaseos_owned_browser_page_only_after_settings_url_and_click"] is True
    assert panel["authority"]["reads_chaseos_owned_browser_page_on_settings_load"] is False
    assert panel["authority"]["reads_chaseos_owned_browser_page_on_capture_panel_load"] is False
    assert panel["authority"]["reads_chaseos_discord_artifact_on_settings_load"] is False
    assert panel["authority"]["reads_chaseos_discord_artifact_on_capture_panel_load"] is False
    assert panel["authority"]["calls_discord_api"] is False
    assert panel["authority"]["reads_discord_token"] is False
    assert panel["authority"]["canonical_mutation_allowed"] is False
    assert panel["runtime_status"]["gateway_controls"]["authority"]["starts_gateways"] is True
    assert panel["readiness"]["runtime_gateway_controls_visible"] is True
    assert panel["launcher_update"]["authority"]["read_only"] is True
    assert panel["launcher_update"]["authority"]["binary_download_allowed_in_this_pass"] is False
    assert panel["launcher_update"]["authority"]["executable_replacement_allowed_in_this_pass"] is False


def test_settings_runtime_controls_panel_load_does_not_start_subprocesses(monkeypatch) -> None:
    def fail_run(*args, **kwargs):
        raise AssertionError(f"Settings page load must not call subprocess.run: {args!r}")

    def fail_popen(*args, **kwargs):
        raise AssertionError(f"Settings page load must not call subprocess.Popen: {args!r}")

    monkeypatch.setattr(subprocess, "run", fail_run)
    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    assert panel["ok"] is True
    assert panel["runtime_status"]["startup_process_probe_enabled"] is False
    assert panel["runtime_status"]["gateway_controls"]["runtimes"]


def test_settings_runtime_controls_panel_exposes_capture_shortcut_settings() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    shortcuts = panel["capture_hotkeys"]
    assert shortcuts["surface"] == "studio_capture_hotkey_settings"
    assert shortcuts["readiness"]["settings_page_visible"] is True
    assert shortcuts["readiness"]["studio_window_shortcuts_configurable"] is True
    assert shortcuts["readiness"]["studio_window_collector_shortcuts_configurable"] is True
    assert shortcuts["readiness"]["global_hotkey_registration_available"] is True
    assert shortcuts["readiness"]["global_hotkey_registration_enabled"] is False
    assert shortcuts["readiness"]["global_hotkey_registration_blocked"] is False
    assert shortcuts["authority"]["registers_global_hotkeys"] is False
    assert shortcuts["authority"]["runs_explicit_collectors_from_studio_shortcuts"] is True
    assert shortcuts["authority"]["reads_ambient_clipboard"] is False
    assert shortcuts["authority"]["captures_screen_pixels"] is False
    assert shortcuts["authority"]["reads_controlled_browser_artifact_from_shortcut_without_settings"] is False
    assert shortcuts["authority"]["launches_chaseos_owned_browser_page_from_shortcut_without_settings"] is False
    assert shortcuts["authority"]["reads_discord_artifact_from_shortcut_without_settings"] is False
    assert shortcuts["authority"]["calls_discord_from_shortcut"] is False
    assert shortcuts["authority"]["reads_personal_active_browser_tab"] is False
    assert shortcuts["bindings"]["open_capture_markdown"] == "Ctrl+Shift+C"
    assert shortcuts["bindings"]["run_screen_capture_collector"] == ""
    assert shortcuts["bindings"]["run_display_region_collector"] == ""
    assert shortcuts["bindings"]["run_clipboard_text_collector"] == ""
    assert shortcuts["bindings"]["run_ambient_clipboard_monitor"] == ""
    assert shortcuts["bindings"]["run_selected_text_collector"] == ""
    assert shortcuts["bindings"]["run_browser_artifact_collector"] == ""
    assert shortcuts["bindings"]["run_chaseos_browser_page_collector"] == ""
    assert shortcuts["bindings"]["run_discord_artifact_collector"] == ""
    assert shortcuts["readiness"]["studio_window_browser_artifact_collector_shortcut_available"] is True
    assert shortcuts["readiness"]["studio_window_display_region_collector_shortcut_available"] is True
    assert shortcuts["readiness"]["studio_window_ambient_clipboard_monitor_shortcut_available"] is True
    assert shortcuts["readiness"]["studio_window_selected_text_collector_shortcut_available"] is True
    assert shortcuts["readiness"]["studio_window_chaseos_browser_page_collector_shortcut_available"] is True
    assert shortcuts["readiness"]["studio_window_discord_artifact_collector_shortcut_available"] is True
    assert panel["readiness"]["capture_shortcut_settings_visible"] is True
    assert panel["readiness"]["capture_studio_window_shortcuts_configurable"] is True
    assert panel["readiness"]["capture_studio_window_collector_shortcuts_configurable"] is True


def test_settings_runtime_controls_panel_exposes_capture_local_image_text_settings() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    image_text = panel["capture_local_image_text"]
    assert image_text["surface"] == "studio_capture_local_image_text_settings"
    assert image_text["quality_fixture_proof"]["surface"] == "studio_capture_local_image_text_quality_fixtures"
    assert image_text["readiness"]["settings_page_visible"] is True
    assert image_text["readiness"]["local_command_configurable"] is True
    assert image_text["readiness"]["quality_fixture_runner_available"] is True
    assert image_text["readiness"]["cloud_optical_character_recognition_blocked"] is True
    assert image_text["authority"]["provider_calls_allowed"] is False
    assert image_text["authority"]["captures_screen_pixels"] is False
    assert panel["summary"]["capture_local_image_text_settings_visible"] is True
    assert panel["summary"]["capture_local_image_text_quality_fixture_status"]
    assert panel["readiness"]["capture_local_image_text_settings_visible"] is True
    assert panel["readiness"]["capture_local_image_text_command_configurable"] is True
    assert panel["readiness"]["capture_local_image_text_quality_fixture_runner_available"] is True


def test_settings_runtime_controls_panel_exposes_capture_collector_settings() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    collectors = panel["capture_collectors"]
    assert collectors["surface"] == "studio_capture_collectors"
    assert collectors["readiness"]["settings_page_visible"] is True
    assert collectors["readiness"]["screen_capture_collector_built"] is True
    assert collectors["readiness"]["screen_capture_requires_operator_click"] is True
    assert collectors["readiness"]["display_region_capture_collector_built"] is True
    assert collectors["readiness"]["display_region_capture_requires_operator_drag"] is True
    assert collectors["readiness"]["clipboard_capture_collector_built"] is True
    assert collectors["readiness"]["clipboard_capture_requires_operator_click"] is True
    assert collectors["readiness"]["ambient_clipboard_monitor_built"] is True
    assert collectors["readiness"]["ambient_clipboard_monitor_requires_privacy_opt_in"] is True
    assert collectors["readiness"]["ambient_clipboard_monitor_writes_no_markdown_on_poll"] is True
    assert collectors["readiness"]["selected_text_capture_collector_built"] is True
    assert collectors["readiness"]["selected_text_capture_requires_operator_click"] is True
    assert collectors["readiness"]["selected_text_capture_uses_temporary_clipboard_copy"] is True
    assert collectors["readiness"]["selected_text_capture_restores_text_clipboard_when_possible"] is True
    assert collectors["readiness"]["browser_artifact_capture_collector_built"] is True
    assert collectors["readiness"]["browser_artifact_capture_requires_operator_click"] is True
    assert collectors["readiness"]["browser_artifact_capture_requires_operator_selected_file"] is True
    assert collectors["readiness"]["browser_artifact_capture_requires_declared_url"] is True
    assert collectors["readiness"]["browser_artifact_capture_reads_live_browser"] is False
    assert collectors["readiness"]["active_chaseos_browser_capture_collector_built"] is True
    assert collectors["readiness"]["active_chaseos_browser_capture_requires_operator_click"] is True
    assert collectors["readiness"]["active_chaseos_browser_capture_reads_chaseos_state"] is True
    assert collectors["readiness"]["active_chaseos_browser_capture_reads_personal_browser"] is False
    assert collectors["readiness"]["chaseos_browser_page_capture_collector_built"] is True
    assert collectors["readiness"]["chaseos_browser_page_capture_requires_operator_click"] is True
    assert collectors["readiness"]["chaseos_browser_page_capture_requires_declared_url"] is True
    assert collectors["readiness"]["chaseos_browser_page_capture_reads_personal_browser"] is False
    assert collectors["readiness"]["discord_artifact_capture_collector_built"] is True
    assert collectors["readiness"]["discord_artifact_capture_requires_operator_click"] is True
    assert collectors["readiness"]["discord_artifact_capture_requires_operator_selected_file"] is True
    assert collectors["readiness"]["discord_artifact_capture_requires_declared_source"] is True
    assert collectors["readiness"]["discord_artifact_capture_calls_discord_api"] is False
    assert collectors["authority"]["captures_screen_pixels_on_settings_load"] is False
    assert collectors["authority"]["reads_clipboard_on_settings_load"] is False
    assert collectors["authority"]["reads_clipboard_on_capture_panel_load"] is False
    assert collectors["authority"]["reads_ambient_clipboard_on_settings_load"] is False
    assert collectors["authority"]["reads_ambient_clipboard_on_capture_panel_load"] is False
    assert collectors["authority"]["reads_selected_text"] is False
    assert collectors["authority"]["reads_active_browser_tab"] is False
    assert collectors["authority"]["reads_chaseos_active_browser_state_only_after_settings_and_click"] is True
    assert collectors["authority"]["reads_chaseos_active_browser_state_on_settings_load"] is False
    assert collectors["authority"]["reads_chaseos_active_browser_state_on_capture_panel_load"] is False
    assert collectors["authority"]["reads_personal_active_browser_tab"] is False
    assert collectors["authority"]["reads_browser_profile"] is False
    assert collectors["authority"]["calls_discord_api"] is False
    assert collectors["authority"]["reads_discord_token"] is False
    assert collectors["authority"]["reads_discord_webhook"] is False
    assert collectors["authority"]["writes_raw_quarantine_markdown_on_click"] is False
    assert panel["summary"]["capture_screen_collector_built"] is True
    assert panel["summary"]["capture_display_region_collector_built"] is True
    assert panel["summary"]["capture_clipboard_collector_built"] is True
    assert panel["summary"]["capture_ambient_clipboard_monitor_built"] is True
    assert panel["summary"]["capture_selected_text_collector_built"] is True
    assert panel["summary"]["capture_accessibility_tree_collector_built"] is True
    assert panel["summary"]["capture_browser_artifact_collector_built"] is True
    assert panel["summary"]["capture_browser_extension_collector_built"] is True
    assert panel["summary"]["capture_active_chaseos_browser_collector_built"] is True
    assert panel["summary"]["capture_chaseos_browser_page_collector_built"] is True
    assert panel["summary"]["capture_discord_artifact_collector_built"] is True
    assert panel["readiness"]["capture_collector_settings_visible"] is True
    assert panel["readiness"]["capture_screen_collector_writes_evidence_only"] is True
    assert panel["readiness"]["capture_display_region_collector_writes_evidence_only"] is True
    assert panel["readiness"]["capture_clipboard_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_ambient_clipboard_monitor_writes_no_markdown_on_poll"] is True
    assert panel["readiness"]["capture_ambient_clipboard_monitor_requires_privacy_opt_in"] is True
    assert panel["readiness"]["capture_selected_text_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_selected_text_collector_requires_operator_click"] is True
    assert panel["readiness"]["capture_selected_text_collector_uses_temporary_clipboard_copy"] is True
    assert panel["readiness"]["capture_accessibility_tree_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_accessibility_tree_collector_requires_operator_click"] is True
    assert panel["readiness"]["capture_browser_artifact_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_browser_extension_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_active_chaseos_browser_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_active_chaseos_browser_collector_reads_chaseos_state"] is True
    assert panel["readiness"]["capture_active_chaseos_browser_collector_reads_personal_browser"] is False
    assert panel["readiness"]["capture_chaseos_browser_page_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_discord_artifact_collector_writes_no_markdown_on_click"] is True
    assert panel["readiness"]["capture_discord_artifact_collector_calls_discord_api"] is False


def test_settings_runtime_controls_panel_exposes_status_without_secrets() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    assert panel["config_status"]["validation_posture"]
    assert panel["provider_status"]["providers"]
    assert panel["provider_readiness"]["summary"]["readiness_status"]
    assert panel["provider_readiness"]["active_profile"]["model"]
    assert panel["provider_readiness"]["fallback_profile"]["model"]
    assert panel["provider_readiness"]["credential_posture"]["raw_credential_values_displayed"] is False
    assert panel["provider_readiness"]["live_probe_readiness"]["approval_gated"] is True
    assert panel["provider_readiness"]["live_probe_readiness"]["studio_executes_live_probe"] is False
    assert panel["runtime_status"]["startup_surfaces"]
    assert panel["launcher_update"]["current_version"]
    assert panel["launcher_update"]["latest_version_label"] == "Not checked"
    assert panel["launcher_update"]["readiness"]["settings_update_check_visible"] is True
    assert panel["launcher_update"]["readiness"]["network_manifest_fetch_built"] is True
    assert panel["launcher_update"]["readiness"]["network_manifest_default_enabled"] is False
    assert panel["launcher_update"]["readiness"]["network_manifest_fetch_requires_operator_approval"] is True
    assert panel["launcher_update"]["readiness"]["download_staging_readiness_built"] is True
    assert panel["launcher_update"]["readiness"]["download_staging_default_enabled"] is False
    assert panel["launcher_update"]["readiness"]["download_staging_writes_enabled"] is False
    assert panel["launcher_update"]["readiness"]["download_staging_executor_proof_built"] is True
    assert panel["launcher_update"]["readiness"]["download_staging_executor_default_enabled"] is False
    assert panel["launcher_update"]["readiness"]["download_staging_executor_writes_enabled_in_settings"] is False
    assert panel["launcher_update"]["readiness"]["signature_verification_proof_built"] is True
    assert panel["launcher_update"]["readiness"]["signature_verification_default_enabled"] is False
    assert panel["launcher_update"]["readiness"]["signature_verification_requires_staged_artifact"] is True
    assert panel["launcher_update"]["readiness"]["signature_verification_requires_verifier"] is True
    assert panel["launcher_update"]["readiness"]["signature_verification_writes_enabled_in_settings"] is False
    assert panel["launcher_update"]["readiness"]["signature_verification_install_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_readiness_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_requires_signature_verified_staged_artifact"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_requires_current_executable_path"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_write_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_execution_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_replacement_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_from_verified_staged_signature_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_from_verified_staged_signature_requires_verified_signature"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_from_verified_staged_signature_requires_current_executable"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_from_verified_staged_signature_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_from_verified_staged_signature_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_from_verified_staged_signature_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_temp_fixture_proof_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_temp_fixture_writes_enabled_in_settings"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_temp_fixture_real_exe_replacement_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_design_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_build_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_execution_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_writes_enabled_in_settings"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_real_replacement_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_build_strategy_proof_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_build_strategy_build_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_build_strategy_execution_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_binary_build_strategy_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_binary_build_strategy_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_spec_scaffold_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_spec_scaffold_build_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_spec_scaffold_execution_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_binary_spec_scaffold_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_binary_spec_scaffold_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_static_verification_proof_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_static_verification_build_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_binary_static_verification_execution_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_binary_static_verification_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_binary_static_verification_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_file_proof_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_file_writes_enabled_in_settings"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_file_real_helper_execution_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_file_real_exe_replacement_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_file_from_signed_manifest_plan_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_file_from_signed_manifest_plan_requires_verified_staged_signature_plan"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_file_from_signed_manifest_plan_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_file_from_signed_manifest_plan_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_file_from_signed_manifest_plan_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_executable_scaffold_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_executable_scaffold_execution_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"]["updater_helper_executable_scaffold_writes_enabled_in_settings"]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"]["updater_helper_executable_scaffold_real_exe_replacement_enabled"]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_executable_scaffold_from_signed_manifest_plan_file_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_executable_scaffold_from_signed_manifest_plan_file_requires_signed_manifest_plan_file"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_executable_scaffold_from_signed_manifest_plan_file_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_executable_scaffold_from_signed_manifest_plan_file_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_executable_scaffold_from_signed_manifest_plan_file_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_consumption_from_signed_manifest_scaffold_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_consumption_from_signed_manifest_scaffold_requires_signed_manifest_scaffold"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_consumption_from_signed_manifest_scaffold_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_consumption_from_signed_manifest_scaffold_audit_write_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_plan_consumption_from_signed_manifest_scaffold_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_from_signed_manifest_consumption_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_from_signed_manifest_consumption_requires_signed_manifest_consumption"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_from_signed_manifest_consumption_audit_write_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_from_signed_manifest_consumption_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_from_signed_manifest_consumption_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_from_signed_manifest_envelope_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_from_signed_manifest_envelope_requires_signed_manifest_audit_envelope"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_from_signed_manifest_envelope_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_from_signed_manifest_envelope_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_from_signed_manifest_envelope_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_execution_dry_run_from_signed_manifest_audit_write_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_execution_dry_run_from_signed_manifest_audit_write_requires_signed_manifest_audit_write"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_execution_dry_run_from_signed_manifest_audit_write_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_execution_dry_run_from_signed_manifest_audit_write_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_execution_dry_run_from_signed_manifest_audit_write_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_requires_execution_dry_run"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_prompted_only"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_startup_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_startup_background_prompt_from_signed_manifest_execution_dry_run_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_end_to_end_dry_run_closeout_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_end_to_end_dry_run_closeout_requires_startup_background_prompt"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"]["updater_end_to_end_dry_run_closeout_safe_dry_run_lane"]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_end_to_end_dry_run_closeout_production_auto_update_complete"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_end_to_end_dry_run_closeout_real_exe_replacement_complete"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_host_mutation_approval_gate_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_host_mutation_approval_gate_requires_closeout"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_host_mutation_approval_gate_requires_disposable_target"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_host_mutation_approval_gate_host_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_host_mutation_approval_gate_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_execution_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_execution_boundary_requires_approval_gate"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_execution_boundary_disposable_target_scope_only"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_execution_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_execution_boundary_external_helper_launch_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_helper_launch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_helper_launch_receipt_boundary_requires_execution_boundary"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_helper_launch_receipt_boundary_requires_injected_launcher"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_helper_launch_receipt_boundary_uses_chaseos_installer"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_helper_launch_receipt_boundary_os_process_spawn_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_helper_launch_receipt_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_relaunch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_relaunch_receipt_boundary_requires_helper_launch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_relaunch_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_relaunch_receipt_boundary_chaseos_relaunch_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_disposable_target_relaunch_receipt_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_install_mutation_gate_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_install_mutation_gate_requires_relaunch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_install_mutation_gate_requires_primary_executable_descriptor"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_install_mutation_gate_future_mutation_only"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_install_mutation_gate_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_install_mutation_gate_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_rollback_audit_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_rollback_audit_boundary_requires_primary_install_mutation_gate"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_rollback_audit_boundary_writes_rollback_copy"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_rollback_audit_boundary_writes_audit_receipt"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_rollback_audit_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_rollback_audit_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_replacement_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_replacement_receipt_boundary_requires_primary_rollback_audit_boundary"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_replacement_receipt_boundary_requires_replacement_artifact_descriptor"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_replacement_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_replacement_receipt_boundary_chaseos_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_replacement_receipt_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_source_recovery_cleanup_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_source_recovery_cleanup_recovery_bytecode_hash_pinning_enabled"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_source_recovery_cleanup_normal_source_restoration_required"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_source_recovery_cleanup_final_auto_update_closeout_blocked_until_source_restored"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_normal_source_restoration_readiness_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_normal_source_restoration_requires_wrapper_removal"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_normal_source_restoration_requires_authoritative_candidate"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_normal_source_restoration_final_auto_update_closeout_blocked_until_source_restored"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_relaunch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_relaunch_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_consumption_dry_run_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_consumption_execution_enabled"] is False
    assert panel["launcher_update"]["readiness"]["updater_helper_plan_consumption_audit_write_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"]["updater_helper_plan_consumption_real_exe_replacement_enabled"]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_audit_envelope_proof_built"] is True
    assert panel["launcher_update"]["readiness"]["updater_helper_audit_envelope_write_enabled"] is False
    assert (
        panel["launcher_update"]["readiness"]["updater_helper_audit_envelope_writes_enabled_in_settings"]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"]["updater_helper_audit_envelope_real_exe_replacement_enabled"]
        is False
    )
    assert panel["launcher_update"]["readiness"]["updater_helper_audit_envelope_write_proof_built"] is True
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_proof_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_proof_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "updater_helper_audit_envelope_write_proof_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["github_release_publication_approval_proof_built"] is True
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_approval_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_approval_github_api_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_approval_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["github_release_publication_execution_proof_built"] is True
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_execution_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_execution_github_api_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_execution_asset_upload_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_execution_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_approval_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_approval_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_approval_requires_credential_boundary"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_approval_github_api_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_approval_asset_upload_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_approval_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_execution_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_execution_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_execution_no_network_harness_only"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_execution_github_api_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_execution_asset_upload_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "github_release_publication_live_runner_execution_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloader_dry_run_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloader_dry_run_requires_signed_manifest_live_readback"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloader_dry_run_download_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloader_dry_run_staging_writes_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloader_dry_run_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_approved_live_download_staging_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_approved_live_download_staging_requires_signed_manifest_downloader_dry_run"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_approved_live_download_staging_requires_injected_downloader"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_approved_live_download_staging_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_approved_live_download_staging_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloaded_staged_signature_verification_proof_built"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloaded_staged_signature_verification_requires_approved_live_download_staging"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloaded_staged_signature_verification_requires_injected_verifier"
        ]
        is True
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloaded_staged_signature_verification_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["launcher_update"]["readiness"][
            "signed_manifest_downloaded_staged_signature_verification_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["launcher_update"]["readiness"]["download_or_install_controls_exposed"] is False
    assert panel["summary"]["launcher_network_manifest_fetch_built"] is True
    assert panel["summary"]["launcher_network_manifest_default_enabled"] is False
    assert panel["summary"]["launcher_network_manifest_requires_operator_approval"] is True
    assert panel["summary"]["launcher_download_staging_readiness_built"] is True
    assert panel["summary"]["launcher_download_staging_default_enabled"] is False
    assert panel["summary"]["launcher_download_staging_writes_enabled"] is False
    assert panel["summary"]["launcher_download_staging_executor_proof_built"] is True
    assert panel["summary"]["launcher_download_staging_executor_default_enabled"] is False
    assert panel["summary"]["launcher_download_staging_executor_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_signature_verification_proof_built"] is True
    assert panel["summary"]["launcher_signature_verification_default_enabled"] is False
    assert panel["summary"]["launcher_signature_verification_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_signature_verification_install_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_readiness_built"] is True
    assert panel["summary"]["launcher_updater_helper_plan_write_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_execution_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_replacement_enabled"] is False
    assert (
        panel["summary"]["launcher_updater_helper_plan_from_verified_staged_signature_proof_built"]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_verified_signature"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_current_executable"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_from_verified_staged_signature_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_from_verified_staged_signature_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_from_verified_staged_signature_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["summary"]["launcher_updater_helper_temp_fixture_proof_built"] is True
    assert panel["summary"]["launcher_updater_helper_temp_fixture_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_updater_helper_temp_fixture_real_exe_replacement_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_design_built"] is True
    assert panel["summary"]["launcher_updater_helper_binary_build_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_execution_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_updater_helper_binary_real_replacement_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_build_strategy_proof_built"] is True
    assert panel["summary"]["launcher_updater_helper_binary_build_strategy_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_updater_helper_binary_build_strategy_execution_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_build_strategy_real_exe_replacement_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_spec_scaffold_built"] is True
    assert panel["summary"]["launcher_updater_helper_binary_spec_scaffold_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_updater_helper_binary_spec_scaffold_execution_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_spec_scaffold_real_exe_replacement_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_binary_static_verification_proof_built"] is True
    assert (
        panel["summary"]["launcher_updater_helper_binary_static_verification_writes_enabled_in_settings"] is False
    )
    assert panel["summary"]["launcher_updater_helper_binary_static_verification_execution_enabled"] is False
    assert (
        panel["summary"]["launcher_updater_helper_binary_static_verification_real_exe_replacement_enabled"]
        is False
    )
    assert panel["summary"]["launcher_updater_helper_plan_file_proof_built"] is True
    assert panel["summary"]["launcher_updater_helper_plan_file_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_updater_helper_plan_file_real_helper_execution_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_plan_file_real_exe_replacement_enabled"] is False
    assert (
        panel["summary"]["launcher_updater_helper_plan_file_from_signed_manifest_plan_proof_built"]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_requires_verified_staged_signature_plan"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["summary"]["launcher_updater_helper_executable_scaffold_built"] is True
    assert panel["summary"]["launcher_updater_helper_executable_scaffold_execution_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_executable_scaffold_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_updater_helper_executable_scaffold_real_exe_replacement_enabled"] is False
    assert (
        panel["summary"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_requires_signed_manifest_plan_file"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_requires_signed_manifest_scaffold"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_audit_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_requires_signed_manifest_consumption"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_audit_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_requires_signed_manifest_audit_envelope"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_requires_signed_manifest_audit_write"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_requires_execution_dry_run"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_prompted_only"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_startup_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["summary"]["launcher_updater_end_to_end_dry_run_closeout_proof_built"] is True
    assert (
        panel["summary"][
            "launcher_updater_end_to_end_dry_run_closeout_requires_startup_background_prompt"
        ]
        is True
    )
    assert panel["summary"]["launcher_updater_end_to_end_dry_run_closeout_safe_dry_run_lane"] is True
    assert (
        panel["summary"][
            "launcher_updater_end_to_end_dry_run_closeout_production_auto_update_complete"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_end_to_end_dry_run_closeout_real_exe_replacement_complete"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_host_mutation_approval_gate_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_host_mutation_approval_gate_requires_closeout"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_host_mutation_approval_gate_requires_disposable_target"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_host_mutation_approval_gate_host_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_host_mutation_approval_gate_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_execution_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_execution_boundary_requires_approval_gate"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_execution_boundary_disposable_target_scope_only"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_execution_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_execution_boundary_external_helper_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_execution_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_injected_launcher"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_uses_chaseos_installer"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_os_process_spawn_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_helper_launch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_chaseos_relaunch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_install_mutation_gate_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_install_mutation_gate_requires_relaunch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_install_mutation_gate_requires_primary_executable_descriptor"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_install_mutation_gate_future_mutation_only"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_install_mutation_gate_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_install_mutation_gate_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_rollback_audit_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_rollback_audit_boundary_requires_primary_install_mutation_gate"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_rollback_audit_boundary_writes_rollback_copy"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_rollback_audit_boundary_writes_audit_receipt"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_rollback_audit_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_rollback_audit_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_replacement_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_primary_rollback_audit_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_replacement_artifact_descriptor"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_replacement_receipt_boundary_chaseos_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_replacement_receipt_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"]["launcher_updater_source_recovery_cleanup_proof_built"]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_source_recovery_cleanup_hash_pinning_enabled"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_source_recovery_cleanup_normal_source_restoration_required"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_source_recovery_cleanup_final_closeout_blocked"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_normal_source_restoration_readiness_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_normal_source_restoration_requires_wrapper_removal"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_normal_source_restoration_requires_authoritative_candidate"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_normal_source_restoration_final_closeout_blocked"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_source_restoration_execution_regression_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_source_restoration_execution_requires_explicit_restore_root"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_source_restoration_execution_requires_regression_evidence"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_source_restoration_execution_runs_regression_commands"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_source_restoration_execution_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_source_restoration_execution_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_restoration_closeout_readiness_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_restoration_closeout_requires_source_cleanup_ready"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_restoration_closeout_requires_regression_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_restoration_closeout_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_restoration_closeout_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_wrapper_removal_preflight_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_scans_current_vault_sources"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_scans_build_lib_candidates"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_requires_authoritative_candidates"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_decompiler_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_wrapper_removal_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_source_candidate_inventory_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_packet_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_requires_candidate_files_inside_vault"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_requires_required_symbols"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_rejects_recovery_wrappers"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_wrapper_removal_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_normal_source_candidate_supply_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_requires_import_candidate_paths"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_requires_required_symbols"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_rejects_recovery_wrappers"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_requires_explicit_candidate_write_flag"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_candidate_write_enabled"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_source_candidate_import_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_readiness_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_scans_configured_roots"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_requires_wrapper_free_candidates"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_rejects_current_live_sources"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_prepares_import_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_candidate_import_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_requires_source_materializer"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_requires_explicit_candidate_write_flag"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_candidate_write_enabled"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_candidate_import_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_materialization_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_requires_materialization_proof"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_rechecks_materialization_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_requires_explicit_candidate_import_write_flag"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_candidate_import_write_enabled"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_import_from_materialization_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_import_from_materialization_proof"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_rechecks_import_from_materialization_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_reuses_after_import_verifier"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_supply_verification_from_materialization_import_proof"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_rechecks_supply_verification_from_materialization_import_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_reuses_after_import_wrapper_removal_executor"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_explicit_source_write_flag"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_from_materialization_import_execution_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_from_materialization_import_execution_proof"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_rechecks_wrapper_removal_from_materialization_import_execution_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_performed"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_supplied_regression_evidence"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_does_not_execute_regression_commands"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_post_wrapper_removal_regression_from_materialization_import_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_requires_post_wrapper_removal_regression_from_materialization_import_proof"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_rechecks_post_wrapper_removal_regression_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_requires_source_cleanup_ready"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_requires_wrapper_free_current_vault_sources"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_read_only"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_source_closeout_from_materialization_import_regression_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_current_vault_source_closeout"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_source_closeout_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_primary_relaunch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_primary_relaunch_receipt_boundary_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_external_chaseos_installer_primary_relaunch_receipt"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_helper_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_closeout_after_source_recovery_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_production_primary_closeout_after_source_recovery"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_primary_closeout_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_live_completion_evidence"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_live_evidence_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_primary_replacement_verified_live"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_startup_background_prompt_verified"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_read_only"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_helper_launch_enabled_by_this_proof"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_primary_real_exe_replacement_enabled_by_this_proof"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_final_production_auto_update_closeout_audit_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_requires_live_claims"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_rechecks_live_evidence_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_feeds_final_closeout_audit"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_read_only"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_helper_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_governed_live_completion_evidence_packet_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_live_download_approval"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_primary_replacement_approval"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_builds_governed_evidence_packet"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_default_live_download_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_default_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_default_primary_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_controlled_live_installer_evidence_runner_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_requires_signed_manifest_live_readback"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_requires_live_download_staging"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_requires_primary_relaunch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_adapts_to_controlled_live_installer_evidence_runner"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_builds_governed_evidence_packet"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_download_performed_by_adapter"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_installer_launch_performed_by_adapter"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_primary_real_exe_replacement_performed_by_adapter"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_adapter_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_collects_current_vault_source_proofs"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_requires_source_proof_readiness"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_adapts_to_approved_live_evidence_runner_adapter"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_can_preview_final_audit"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_download_performed_by_dry_run"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_installer_launch_performed_by_dry_run"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_primary_real_exe_replacement_performed_by_dry_run"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_collects_current_vault_source_proofs"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_normalizes_blocked_receipt_digests_only"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_download_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_installer_launch_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_primary_real_exe_replacement_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_requires_external_receipt_bundle"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_requires_all_six_source_receipts"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_rechecks_bundle_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_feeds_approved_real_dry_run"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_download_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_installer_launch_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_primary_real_exe_replacement_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_capture_boundary_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_live_action_approvals"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_produces_external_receipt_bundle"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_feeds_real_live_receipt_capture_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_requires_ready_production_runner_proof"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_requires_primary_closeout_after_source_recovery"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_runner_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_governed_packet_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_feeds_final_closeout_audit"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_runner_final_closeout_bridge_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_in_vault_evidence_root"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_explicit_file_read_flag"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_runner_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_primary_closeout_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_feeds_final_closeout_bridge"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_requires_exact_installer_name"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_requires_build_script_studio_hash_guard"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_signature_probe_required_for_signed_output"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_installer_real_artifact_build_output_capture_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_both_artifacts"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_studio_dist"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_installer_dist"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_cross_artifact_hash_guards"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_requires_import_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_rechecks_import_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_revalidates_imported_candidate_hashes"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_requires_supply_approval"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_requires_candidate_verification_approval"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_authoritative_candidate_supply_verification_after_import_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_requires_after_import_proof"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_rechecks_after_import_digest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_reuses_wrapper_removal_executor"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_requires_explicit_source_write_flag"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_after_import_execution_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_requires_supply_packet"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_requires_candidate_verification"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_requires_explicit_source_write_flag"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_decompiler_execution_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_settings_write_control_exposed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_current_vault_wrapper_removal_executor_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["summary"]["launcher_updater_helper_plan_consumption_dry_run_built"] is True
    assert panel["summary"]["launcher_updater_helper_plan_consumption_execution_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_plan_consumption_audit_write_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_plan_consumption_real_exe_replacement_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_audit_envelope_proof_built"] is True
    assert panel["summary"]["launcher_updater_helper_audit_envelope_write_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_audit_envelope_writes_enabled_in_settings"] is False
    assert panel["summary"]["launcher_updater_helper_audit_envelope_real_exe_replacement_enabled"] is False
    assert panel["summary"]["launcher_updater_helper_audit_envelope_write_proof_built"] is True
    assert (
        panel["summary"]["launcher_updater_helper_audit_envelope_write_proof_writes_enabled_in_settings"]
        is False
    )
    assert (
        panel["summary"]["launcher_updater_helper_audit_envelope_write_proof_helper_execution_enabled"]
        is False
    )
    assert (
        panel["summary"]["launcher_updater_helper_audit_envelope_write_proof_real_exe_replacement_enabled"]
        is False
    )
    assert panel["summary"]["launcher_github_release_publication_live_runner_approval_proof_built"] is True
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_runner_approval_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_runner_approval_requires_credential_boundary"
        ]
        is True
    )
    assert (
        panel["summary"]["launcher_github_release_publication_live_runner_approval_github_api_enabled"]
        is False
    )
    assert (
        panel["summary"]["launcher_github_release_publication_live_runner_approval_asset_upload_enabled"]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_runner_approval_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["summary"]["launcher_github_release_publication_live_runner_execution_proof_built"] is True
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_runner_execution_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_runner_execution_no_network_harness_only"
        ]
        is True
    )
    assert (
        panel["summary"]["launcher_github_release_publication_live_runner_execution_github_api_enabled"]
        is False
    )
    assert (
        panel["summary"]["launcher_github_release_publication_live_runner_execution_asset_upload_enabled"]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_runner_execution_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_activation_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_activation_requires_credential_reference"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_activation_reads_secret_values_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_activation_github_api_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_activation_asset_upload_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_activation_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_execution_contract_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_execution_contract_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_execution_contract_reads_secret_values_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_execution_contract_github_api_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_execution_contract_asset_upload_performed"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_execution_contract_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_reads_secret_values_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_invokes_network_from_chaseos"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_github_api_performed_by_chaseos"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"]["launcher_signed_release_manifest_live_readback_proof_built"]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_release_manifest_live_readback_requires_published_manifest"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_release_manifest_live_readback_performs_network_from_chaseos"
        ]
        is False
    )
    assert (
        panel["summary"]["launcher_signed_release_manifest_live_readback_download_enabled"]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_release_manifest_live_readback_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_release_manifest_live_readback_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["summary"]["launcher_signed_manifest_downloader_dry_run_proof_built"] is True
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloader_dry_run_requires_signed_manifest_live_readback"
        ]
        is True
    )
    assert (
        panel["summary"]["launcher_signed_manifest_downloader_dry_run_network_performed"]
        is False
    )
    assert (
        panel["summary"]["launcher_signed_manifest_downloader_dry_run_download_enabled"]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloader_dry_run_staging_writes_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloader_dry_run_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_approved_live_download_staging_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_approved_live_download_staging_requires_signed_manifest_downloader_dry_run"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_approved_live_download_staging_requires_injected_downloader"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_approved_live_download_staging_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_approved_live_download_staging_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_approved_live_download_staging_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_proof_built"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_approved_live_download_staging"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_injected_verifier"
        ]
        is True
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["summary"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["preference_posture"]["raw_credential_values_displayed"] is False
    assert panel["security"]["secret_values_included"] is False
    assert panel["security"]["raw_credentials_included"] is False
    assert panel["security"]["sensitive_key_scan_passed"] is True
    assert "expected_contents" not in json.dumps(panel)


def test_settings_runtime_controls_panel_distinguishes_gated_actions() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)
    action_posture = panel["action_posture"]

    assert action_posture["read_only_status_visible"] is True
    assert action_posture["native_ui_action_buttons_enabled"] is True
    assert action_posture["dry_run_command_visible"] is True
    assert action_posture["confirmed_toggle_command_visible"] is True
    assert action_posture["confirm_action_required"] is True
    assert action_posture["gate_approval_required"] is True
    assert action_posture["host_mutation_blocked"] is True
    assert "runtime-startup-controls" in action_posture["route_for_current_preview"]
    assert "--confirm-action" in action_posture["route_for_future_mutation"]


def test_settings_runtime_controls_panel_exposes_provider_readiness_summary() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    readiness = panel["provider_readiness"]
    assert readiness["read_only"] is True
    assert readiness["summary"]["active_provider_id"]
    assert readiness["summary"]["active_binding_label"]
    assert panel["summary"]["active_provider_binding"] == readiness["summary"]["active_binding_label"]
    assert panel["summary"]["fallback_provider_binding"] == readiness["summary"]["fallback_binding_label"]
    assert "degraded_reason" in readiness["summary"]
    assert "last_probe_marker_present" in readiness["summary"]
    assert isinstance(readiness["summary"]["queued_retry_count"], int)
    assert readiness["authority"]["provider_calls_allowed"] is False
    assert readiness["authority"]["provider_switch_allowed"] is False
    assert readiness["authority"]["executes_live_probe"] is False
    assert panel["readiness"]["provider_readiness_visible"] is True
    assert panel["readiness"]["provider_live_probe_status_visible"] is True
    assert panel["readiness"]["launcher_update_check_visible"] is True
    assert panel["readiness"]["launcher_current_version_visible"] is True
    assert panel["readiness"]["launcher_latest_available_version_visible"] is True
    assert panel["readiness"]["launcher_network_manifest_fetch_built"] is True
    assert panel["readiness"]["launcher_network_manifest_default_enabled"] is False
    assert panel["readiness"]["launcher_network_manifest_requires_operator_approval"] is True
    assert panel["readiness"]["launcher_download_staging_readiness_built"] is True
    assert panel["readiness"]["launcher_download_staging_default_enabled"] is False
    assert panel["readiness"]["launcher_download_staging_writes_enabled"] is False
    assert panel["readiness"]["launcher_download_staging_executor_proof_built"] is True
    assert panel["readiness"]["launcher_download_staging_executor_default_enabled"] is False
    assert panel["readiness"]["launcher_download_staging_executor_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_signature_verification_proof_built"] is True
    assert panel["readiness"]["launcher_signature_verification_default_enabled"] is False
    assert panel["readiness"]["launcher_signature_verification_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_signature_verification_install_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_readiness_built"] is True
    assert panel["readiness"]["launcher_updater_helper_plan_write_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_execution_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_replacement_enabled"] is False
    assert (
        panel["readiness"]["launcher_updater_helper_plan_from_verified_staged_signature_proof_built"]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_verified_signature"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_from_verified_staged_signature_requires_current_executable"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_from_verified_staged_signature_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_from_verified_staged_signature_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_from_verified_staged_signature_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_updater_helper_temp_fixture_proof_built"] is True
    assert panel["readiness"]["launcher_updater_helper_temp_fixture_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_updater_helper_temp_fixture_real_exe_replacement_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_design_built"] is True
    assert panel["readiness"]["launcher_updater_helper_binary_build_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_execution_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_real_replacement_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_build_strategy_proof_built"] is True
    assert panel["readiness"]["launcher_updater_helper_binary_build_strategy_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_build_strategy_execution_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_build_strategy_real_exe_replacement_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_spec_scaffold_built"] is True
    assert panel["readiness"]["launcher_updater_helper_binary_spec_scaffold_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_spec_scaffold_execution_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_spec_scaffold_real_exe_replacement_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_binary_static_verification_proof_built"] is True
    assert (
        panel["readiness"]["launcher_updater_helper_binary_static_verification_writes_enabled_in_settings"]
        is False
    )
    assert panel["readiness"]["launcher_updater_helper_binary_static_verification_execution_enabled"] is False
    assert (
        panel["readiness"]["launcher_updater_helper_binary_static_verification_real_exe_replacement_enabled"]
        is False
    )
    assert panel["readiness"]["launcher_updater_helper_plan_file_proof_built"] is True
    assert panel["readiness"]["launcher_updater_helper_plan_file_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_updater_helper_plan_file_real_helper_execution_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_plan_file_real_exe_replacement_enabled"] is False
    assert (
        panel["readiness"]["launcher_updater_helper_plan_file_from_signed_manifest_plan_proof_built"]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_requires_verified_staged_signature_plan"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_file_from_signed_manifest_plan_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_updater_helper_executable_scaffold_built"] is True
    assert panel["readiness"]["launcher_updater_helper_executable_scaffold_execution_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_executable_scaffold_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_updater_helper_executable_scaffold_real_exe_replacement_enabled"] is False
    assert (
        panel["readiness"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_requires_signed_manifest_plan_file"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_executable_scaffold_from_signed_manifest_plan_file_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_requires_signed_manifest_scaffold"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_execution_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_audit_write_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_plan_consumption_from_signed_manifest_scaffold_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_requires_signed_manifest_consumption"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_audit_write_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_from_signed_manifest_consumption_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_requires_signed_manifest_audit_envelope"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_audit_envelope_write_from_signed_manifest_envelope_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_requires_signed_manifest_audit_write"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_helper_execution_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_helper_execution_dry_run_from_signed_manifest_audit_write_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_requires_execution_dry_run"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_prompted_only"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_startup_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_startup_background_prompt_from_signed_manifest_execution_dry_run_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_updater_end_to_end_dry_run_closeout_proof_built"] is True
    assert (
        panel["readiness"][
            "launcher_updater_end_to_end_dry_run_closeout_requires_startup_background_prompt"
        ]
        is True
    )
    assert panel["readiness"]["launcher_updater_end_to_end_dry_run_closeout_safe_dry_run_lane"] is True
    assert (
        panel["readiness"][
            "launcher_updater_end_to_end_dry_run_closeout_production_auto_update_complete"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_end_to_end_dry_run_closeout_real_exe_replacement_complete"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_host_mutation_approval_gate_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_host_mutation_approval_gate_requires_closeout"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_host_mutation_approval_gate_requires_disposable_target"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_host_mutation_approval_gate_host_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_host_mutation_approval_gate_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_execution_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_execution_boundary_requires_approval_gate"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_execution_boundary_disposable_target_scope_only"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_execution_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_execution_boundary_external_helper_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_execution_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_requires_injected_launcher"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_uses_chaseos_installer"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_os_process_spawn_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_helper_launch_receipt_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_helper_launch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_chaseos_relaunch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_disposable_target_relaunch_receipt_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_install_mutation_gate_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_install_mutation_gate_requires_relaunch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_install_mutation_gate_requires_primary_executable_descriptor"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_install_mutation_gate_future_mutation_only"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_install_mutation_gate_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_install_mutation_gate_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_rollback_audit_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_rollback_audit_boundary_requires_primary_install_mutation_gate"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_rollback_audit_boundary_writes_rollback_copy"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_rollback_audit_boundary_writes_audit_receipt"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_rollback_audit_boundary_primary_install_mutation_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_rollback_audit_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_replacement_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_primary_rollback_audit_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_replacement_artifact_descriptor"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_replacement_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_replacement_receipt_boundary_chaseos_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_replacement_receipt_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"]["launcher_updater_source_recovery_cleanup_proof_built"]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_source_recovery_cleanup_hash_pinning_enabled"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_source_recovery_cleanup_normal_source_restoration_required"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_source_recovery_cleanup_final_closeout_blocked"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_normal_source_restoration_readiness_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_normal_source_restoration_requires_wrapper_removal"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_normal_source_restoration_requires_authoritative_candidate"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_normal_source_restoration_final_closeout_blocked"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_current_vault_source_closeout"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_source_closeout_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_primary_relaunch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_rechecks_primary_relaunch_receipt_boundary_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_requires_external_chaseos_installer_primary_relaunch_receipt"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_source_write_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_helper_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_closeout_after_source_recovery_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_production_primary_closeout_after_source_recovery"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_primary_closeout_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_live_completion_evidence"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_rechecks_live_evidence_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_primary_replacement_verified_live"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_requires_startup_background_prompt_verified"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_read_only"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_helper_launch_enabled_by_this_proof"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_primary_real_exe_replacement_enabled_by_this_proof"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_final_production_auto_update_closeout_audit_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_requires_live_claims"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_rechecks_live_evidence_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_feeds_final_closeout_audit"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_read_only"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_helper_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_governed_live_completion_evidence_packet_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_live_download_approval"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_requires_primary_replacement_approval"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_builds_governed_evidence_packet"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_default_live_download_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_default_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_default_primary_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_controlled_live_installer_evidence_runner_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_requires_signed_manifest_live_readback"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_requires_live_download_staging"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_requires_primary_relaunch_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_adapts_to_controlled_live_installer_evidence_runner"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_builds_governed_evidence_packet"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_download_performed_by_adapter"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_installer_launch_performed_by_adapter"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_primary_real_exe_replacement_performed_by_adapter"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_adapter_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_collects_current_vault_source_proofs"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_requires_source_proof_readiness"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_adapts_to_approved_live_evidence_runner_adapter"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_can_preview_final_audit"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_download_performed_by_dry_run"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_installer_launch_performed_by_dry_run"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_primary_real_exe_replacement_performed_by_dry_run"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_collects_current_vault_source_proofs"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_normalizes_blocked_receipt_digests_only"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_download_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_installer_launch_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_primary_real_exe_replacement_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_requires_external_receipt_bundle"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_requires_all_six_source_receipts"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_rechecks_bundle_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_feeds_approved_real_dry_run"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_download_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_installer_launch_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_primary_real_exe_replacement_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_capture_boundary_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_requires_live_action_approvals"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_produces_external_receipt_bundle"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_feeds_real_live_receipt_capture_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_requires_ready_production_runner_proof"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_requires_primary_closeout_after_source_recovery"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_runner_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_rechecks_governed_packet_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_feeds_final_closeout_audit"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_runner_final_closeout_bridge_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_in_vault_evidence_root"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_requires_explicit_file_read_flag"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_runner_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_rechecks_primary_closeout_digest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_feeds_final_closeout_bridge"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_requires_exact_installer_name"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_requires_build_script_studio_hash_guard"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_signature_probe_required_for_signed_output"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_installer_real_artifact_build_output_capture_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_both_artifacts"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_studio_dist"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_isolated_installer_dist"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_requires_cross_artifact_hash_guards"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_download_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_installer_launch_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_primary_replacement_enabled_by_default"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_updater_helper_plan_consumption_dry_run_built"] is True
    assert panel["readiness"]["launcher_updater_helper_plan_consumption_execution_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_plan_consumption_audit_write_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_plan_consumption_real_exe_replacement_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_audit_envelope_proof_built"] is True
    assert panel["readiness"]["launcher_updater_helper_audit_envelope_write_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_audit_envelope_writes_enabled_in_settings"] is False
    assert panel["readiness"]["launcher_updater_helper_audit_envelope_real_exe_replacement_enabled"] is False
    assert panel["readiness"]["launcher_updater_helper_audit_envelope_write_proof_built"] is True
    assert (
        panel["readiness"]["launcher_updater_helper_audit_envelope_write_proof_writes_enabled_in_settings"]
        is False
    )
    assert (
        panel["readiness"]["launcher_updater_helper_audit_envelope_write_proof_helper_execution_enabled"]
        is False
    )
    assert (
        panel["readiness"]["launcher_updater_helper_audit_envelope_write_proof_real_exe_replacement_enabled"]
        is False
    )
    assert panel["readiness"]["launcher_github_release_publication_approval_proof_built"] is True
    assert (
        panel["readiness"][
            "launcher_github_release_publication_approval_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["readiness"]["launcher_github_release_publication_approval_github_api_enabled"]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_approval_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_github_release_publication_execution_proof_built"] is True
    assert (
        panel["readiness"][
            "launcher_github_release_publication_execution_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["readiness"]["launcher_github_release_publication_execution_github_api_enabled"]
        is False
    )
    assert (
        panel["readiness"]["launcher_github_release_publication_execution_asset_upload_enabled"]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_execution_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_github_release_publication_live_runner_approval_proof_built"] is True
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_runner_approval_requires_exact_operator_statement"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_runner_approval_requires_credential_boundary"
        ]
        is True
    )
    assert (
        panel["readiness"]["launcher_github_release_publication_live_runner_approval_github_api_enabled"]
        is False
    )
    assert (
        panel["readiness"]["launcher_github_release_publication_live_runner_approval_asset_upload_enabled"]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_runner_approval_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_github_release_publication_live_runner_execution_proof_built"] is True
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_runner_execution_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_runner_execution_no_network_harness_only"
        ]
        is True
    )
    assert (
        panel["readiness"]["launcher_github_release_publication_live_runner_execution_github_api_enabled"]
        is False
    )
    assert (
        panel["readiness"]["launcher_github_release_publication_live_runner_execution_asset_upload_enabled"]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_runner_execution_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_activation_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_activation_requires_credential_reference"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_activation_reads_secret_values_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_activation_github_api_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_activation_asset_upload_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_activation_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_execution_contract_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_execution_contract_requires_injected_runner"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_execution_contract_reads_secret_values_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_execution_contract_github_api_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_execution_contract_asset_upload_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_execution_contract_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_requires_external_receipt"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_reads_secret_values_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_invokes_network_from_chaseos"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_github_api_performed_by_chaseos"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_github_release_publication_live_github_runner_real_execution_boundary_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"]["launcher_signed_release_manifest_live_readback_proof_built"]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_release_manifest_live_readback_requires_published_manifest"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_release_manifest_live_readback_performs_network_from_chaseos"
        ]
        is False
    )
    assert (
        panel["readiness"]["launcher_signed_release_manifest_live_readback_download_enabled"]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_release_manifest_live_readback_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_release_manifest_live_readback_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_signed_manifest_downloader_dry_run_proof_built"] is True
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloader_dry_run_requires_signed_manifest_live_readback"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloader_dry_run_network_performed"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloader_dry_run_download_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloader_dry_run_staging_writes_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloader_dry_run_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_approved_live_download_staging_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_approved_live_download_staging_requires_signed_manifest_downloader_dry_run"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_approved_live_download_staging_requires_injected_downloader"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_approved_live_download_staging_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_approved_live_download_staging_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_approved_live_download_staging_real_exe_replacement_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_proof_built"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_approved_live_download_staging"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_requires_injected_verifier"
        ]
        is True
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_writes_enabled_in_settings"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_installer_launch_enabled"
        ]
        is False
    )
    assert (
        panel["readiness"][
            "launcher_signed_manifest_downloaded_staged_signature_verification_real_exe_replacement_enabled"
        ]
        is False
    )
    assert panel["readiness"]["launcher_download_or_install_controls_exposed"] is False


def test_settings_runtime_controls_panel_exposes_personal_context_import_posture() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)
    context_import = panel["personal_context_import"]

    assert context_import["surface"] == "studio_personal_context_import_panel"
    assert "READY_FOR_MANUAL_TESTING" in context_import["implementation_status"] or "PARTIAL" in context_import["implementation_status"]
    assert context_import["preview_writer"]["surface"] == "studio_personal_context_import_preview_writer"
    assert context_import["readiness"]["approved_preview_writer_built"] is True
    assert context_import["readiness"]["approved_preview_execution_proof_built"] is True
    assert context_import["readiness"]["approved_preview_execution_proof_source_digest_gated"] is True
    assert context_import["readiness"]["multi_instance_test_harness_built"] is True
    assert context_import["readiness"]["runtime_consumption_readiness_built"] is True
    assert context_import["readiness"]["raw_full_memory_injection_blocked"] is True
    assert context_import["readiness"]["canonical_promotion_approval_preview_built"] is True
    assert context_import["readiness"]["canonical_promotion_executor_built"] is True
    assert context_import["readiness"]["canonical_promotion_executor_approval_gated"] is True
    assert context_import["summary"]["multi_instance_fixture_harness_ready"] is True
    assert context_import["summary"]["runtime_consumption_readiness_ready"] is True
    assert context_import["summary"]["canonical_promotion_approval_preview_ready"] is True
    assert context_import["summary"]["canonical_promotion_approved_executor_ready"] is True
    assert context_import["authority"]["read_only"] is True
    assert context_import["authority"]["writes_vault"] is False
    assert context_import["authority"]["writes_raw_intake"] is False
    assert context_import["authority"]["writes_personal_map"] is False
    assert context_import["authority"]["canonical_mutation_allowed"] is False
    assert context_import["readiness"]["live_import_writes_enabled"] is False
    assert panel["summary"]["personal_context_import_pipeline_stage_count"] >= 6
    assert panel["preference_posture"]["personal_context_import_surface"]
    assert panel["readiness"]["personal_context_import_visible"] is True
    assert panel["readiness"]["personal_context_import_settings_entrypoint_ready"] is True
    assert panel["readiness"]["personal_context_import_writes_blocked"] is True


def test_settings_runtime_controls_panel_exposes_signed_artifact_verification_closeout_readiness() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    launcher_readiness = panel["launcher_update"]["readiness"]
    settings_readiness = panel["readiness"]

    for readiness, prefix in (
        (launcher_readiness, "updater"),
        (settings_readiness, "launcher_updater"),
    ):
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_proof_built"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_requires_dist_artifact_isolation_cohabitation"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_requires_signature_probe"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_requires_studio_signed_output"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_requires_installer_signed_output"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_download_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_installer_launch_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_primary_replacement_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_signed_artifact_verification_closeout_settings_install_control_exposed"
            ]
            is False
        )


def test_settings_runtime_controls_panel_exposes_local_installer_disposable_dry_run_readiness() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    launcher_readiness = panel["launcher_update"]["readiness"]
    settings_readiness = panel["readiness"]

    for readiness, prefix in (
        (launcher_readiness, "updater"),
        (settings_readiness, "launcher_updater"),
    ):
        assert (
            readiness[f"{prefix}_local_installer_disposable_dry_run_proof_built"]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_requires_plan_file"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_requires_disposable_target_root"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_requires_explicit_execution_flag"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_uses_chaseos_installer"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_blocks_primary_dist_target"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_live_install_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_primary_replacement_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_installer_disposable_dry_run_settings_install_control_exposed"
            ]
            is False
        )


def test_settings_runtime_controls_panel_exposes_local_manifest_prompt_readiness() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    launcher_update = panel["launcher_update"]
    local_prompt = launcher_update["local_manifest_prompt"]
    launcher_readiness = launcher_update["readiness"]
    settings_readiness = panel["readiness"]

    assert local_prompt["surface"] == (
        "studio_launcher_update_local_manifest_background_prompt_settings_action"
    )
    assert local_prompt["status"] == (
        "launcher_update_local_manifest_background_prompt_no_manifest_configured"
    )
    assert local_prompt["settings_prompt_visible"] is False
    assert local_prompt["settings_install_control_exposed"] is False
    assert local_prompt["settings_download_control_exposed"] is False
    assert panel["summary"]["launcher_local_manifest_prompt_status"] == local_prompt["status"]
    assert panel["summary"]["launcher_local_manifest_prompt_visible"] is False

    for readiness, prefix in (
        (launcher_readiness, "updater"),
        (settings_readiness, "launcher_updater"),
    ):
        assert (
            readiness[f"{prefix}_local_manifest_background_prompt_proof_built"]
            is True
        )
        assert (
            readiness[f"{prefix}_local_manifest_background_prompt_requires_manifest_file"]
            is True
        )
        assert (
            readiness[f"{prefix}_local_manifest_background_prompt_validates_manifest_schema"]
            is True
        )
        assert (
            readiness[f"{prefix}_local_manifest_background_prompt_compares_current_latest"]
            is True
        )
        assert (
            readiness[f"{prefix}_local_manifest_background_prompt_prompted_only"]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_manifest_background_prompt_background_poll_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_manifest_background_prompt_download_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_manifest_background_prompt_installer_launch_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_manifest_background_prompt_primary_replacement_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_manifest_background_prompt_settings_install_control_exposed"
            ]
            is False
        )


def test_settings_runtime_controls_panel_exposes_local_release_channel_closeout_readiness() -> None:
    panel = build_settings_runtime_controls_panel(VAULT_ROOT)

    launcher_update = panel["launcher_update"]
    closeout = launcher_update["local_release_channel_closeout"]
    launcher_readiness = launcher_update["readiness"]
    settings_readiness = panel["readiness"]

    assert closeout["surface"] == (
        "studio_launcher_update_local_release_channel_blocker_closeout"
    )
    assert closeout["ok"] is True
    assert closeout["only_external_blockers_remain"] is True
    assert closeout["non_external_blockers"] == []
    assert "release_channel_hosting_not_connected" in closeout["external_blocker_ids"]
    assert closeout["settings_install_control_exposed"] is False
    assert closeout["production_auto_update_complete"] is False
    assert panel["summary"]["launcher_local_release_channel_closeout_status"] == closeout[
        "status"
    ]
    assert (
        panel["summary"][
            "launcher_local_release_channel_only_external_blockers_remain"
        ]
        is True
    )
    assert panel["summary"]["launcher_local_release_channel_local_passes_remaining"] == 0

    for readiness, prefix in (
        (launcher_readiness, "updater"),
        (settings_readiness, "launcher_updater"),
    ):
        assert (
            readiness[f"{prefix}_local_release_channel_blocker_closeout_proof_built"]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_release_channel_blocker_closeout_classifies_external_blockers"
            ]
            is True
        )
        assert (
            readiness[
                f"{prefix}_local_release_channel_blocker_closeout_download_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_release_channel_blocker_closeout_installer_launch_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_release_channel_blocker_closeout_primary_replacement_enabled_by_default"
            ]
            is False
        )
        assert (
            readiness[
                f"{prefix}_local_release_channel_blocker_closeout_settings_install_control_exposed"
            ]
            is False
        )


def test_settings_runtime_controls_panel_json_serializable() -> None:
    json.dumps(build_settings_runtime_controls_panel(VAULT_ROOT))
