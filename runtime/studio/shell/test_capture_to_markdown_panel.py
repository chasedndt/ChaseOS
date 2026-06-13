"""VCMI Pass 3 Studio Capture to Markdown panel tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import zipfile

VAULT = Path(__file__).resolve().parents[3]
FRONTEND = Path(__file__).resolve().parent / "frontend"
sys.path.insert(0, str(VAULT))


PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15"
    "c4890000000d49444154789c6360000002000100ffff03000006000557bfab"
    "d40000000049454e44ae426082"
)


def _make_api(vault_root: Path):
    from runtime.studio.shell.api import StudioAPI

    return StudioAPI(str(vault_root))


def _payload(*, title: str = "Studio VCMI Capture", text: str = "Visible capture text for review.") -> dict:
    return {
        "source_mode": "manual_text",
        "profile": "research_note",
        "title": title,
        "raw_text": text,
        "source_url": "https://example.test/source",
        "user_intent": "capture for later review",
        "structured_notes": "- keep raw and generated fields separate",
        "generated_summary": "Short operator summary.",
        "generated_interpretation": "Operator interpretation.",
    }


def _write_png(vault_root: Path, relative_path: str = "07_LOGS/Operator-Screenshots/local/default/screenshot.png") -> Path:
    target = vault_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PNG_BYTES)
    return target


def _write_fake_local_text_engine(vault_root: Path, text: str) -> str:
    script = vault_root / "runtime" / "capture" / "fake-local-text-engine.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "from __future__ import annotations\n"
        "import json\n"
        "import sys\n"
        "if len(sys.argv) < 2:\n"
        "    raise SystemExit(2)\n"
        f"print(json.loads({json.dumps(text)!r}))\n",
        encoding="utf-8",
    )
    return json.dumps([sys.executable, str(script)])


def _write_marker_local_text_engine(vault_root: Path, text: str, marker: Path) -> str:
    script = vault_root / "runtime" / "capture" / "fake-marker-local-text-engine.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    marker.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "from __future__ import annotations\n"
        "import json\n"
        "from pathlib import Path\n"
        "import sys\n"
        "if len(sys.argv) < 2:\n"
        "    raise SystemExit(2)\n"
        f"Path(json.loads({json.dumps(str(marker))!r})).write_text('ran', encoding='utf-8')\n"
        f"print(json.loads({json.dumps(text)!r}))\n",
        encoding="utf-8",
    )
    return json.dumps([sys.executable, str(script)])


def _seed_downstream_contracts(vault_root: Path) -> None:
    now = vault_root / "00_HOME" / "Now.md"
    now.parent.mkdir(parents=True, exist_ok=True)
    now.write_text(
        "# Now\n\n## Current Phase\nPhase 9 test fixture\n\n## Active Now\n- VCMI Studio AOR dry-run fixture\n",
        encoding="utf-8",
    )

    workflow = vault_root / "runtime" / "workflows" / "registry" / "source_pack_builder.yaml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "\n".join(
            [
                "id: source_pack_builder",
                "workflow_id: source_pack_builder",
                "name: Source Pack Builder",
                "version: '1.0'",
                "description: Source pack builder test fixture",
                "status: active",
                "task_type: source-pack-builder",
                "role_card: source-pack-builder",
                "trigger_type: manual",
                "owner: operator",
                "permission_ceiling: acquisition_pack_only",
                "connector_policy:",
                "  browser_automation: disabled",
                "writeback_targets:",
                "  - runtime/acquisition/packs/",
                "  - 07_LOGS/Acquisition-Packs/",
                "non_goals:",
                "  - no canonical state mutation",
                "failure_behavior: escalate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    task_table = vault_root / "runtime" / "aor" / "task_type_table.yaml"
    task_table.parent.mkdir(parents=True, exist_ok=True)
    task_table.write_text(
        "\n".join(
            [
                "task_types:",
                "  - id: source-pack-builder",
                "    permission_ceiling: acquisition_pack_only",
                "    notes: no canonical mutations; canonical mutation requested must escalate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    role_card = vault_root / "06_AGENTS" / "role-cards" / "source-pack-builder.yaml"
    role_card.parent.mkdir(parents=True, exist_ok=True)
    role_card.write_text(
        "\n".join(
            [
                "id: source-pack-builder",
                "name: Source Pack Builder",
                "version: '1.0'",
                "description: Source pack builder test role card",
                "owner: operator",
                "allowed_actions:",
                "  - read_declared_source_files",
                "  - write_runtime_acquisition_pack",
                "forbidden_actions:",
                "  - access_credentials",
                "  - browse_live_web",
                "  - mutate_canonical_state",
                "write_scope:",
                "  - runtime/acquisition/packs/",
                "  - 07_LOGS/Acquisition-Packs/",
                "forbidden_write_zones:",
                "  - 00_HOME/",
                "  - 02_KNOWLEDGE/",
                "escalation_rules:",
                "  - unsupported source scope",
                "runtime_expectations:",
                "  - dry run skips writeback",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    schema = vault_root / "runtime" / "source_intelligence" / "schemas" / "source_package_schema.md"
    schema.parent.mkdir(parents=True, exist_ok=True)
    schema.write_text(
        "# Source Package Schema\n\n"
        "Required normalized source-package fields include `normalized_text`, "
        "`origin_path`, and `user_trust_level`.\n",
        encoding="utf-8",
    )
    (vault_root / "runtime" / "source_intelligence" / "workspaces").mkdir(parents=True, exist_ok=True)
    openclaw_caps = vault_root / "runtime" / "openclaw" / "capabilities.yaml"
    openclaw_caps.parent.mkdir(parents=True, exist_ok=True)
    openclaw_caps.write_text(
        "\n".join(
            [
                "runtime: openclaw",
                "bus_name: OpenClaw",
                "handles:",
                "  - task_type: source-pack-builder",
                "    priority: primary",
                "max_concurrent_tasks: 3",
                "heartbeat_stale_seconds: 900",
                "priority_ceiling: normal",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _list_files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


class TestCaptureToMarkdownAPI:
    def test_panel_model_exposes_profiles_sources_and_boundaries(self, tmp_path):
        api = _make_api(tmp_path)
        result = api.get_capture_to_markdown_panel()

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_panel"
        data = result["data"]
        assert data["surface"] == "studio_capture_to_markdown_panel"
        assert data["readiness"]["capture_to_markdown_panel_mounted"] is True
        assert data["readiness"]["preview_api_ready"] is True
        assert data["readiness"]["save_api_ready"] is True
        assert data["authority"]["raw_quarantine_write_on_save"] is True
        assert data["authority"]["canonical_mutation_allowed"] is False
        assert data["authority"]["provider_call_allowed"] is False
        assert {profile["profile_id"] for profile in data["profiles"]} >= {"research_note", "raw_archive"}
        assert {mode["id"] for mode in data["source_modes"]} >= {
            "manual_text",
            "local_text_file",
            "saved_html_file",
            "controlled_html_artifact",
            "screenshot_attachment",
            "screenshot_text_extraction",
            "photo_document_text_extraction",
        }
        source_options = {option["id"]: option for option in data["capture_source_options"]}
        assert source_options["manual_text"]["source_mode"] == "manual_text"
        assert source_options["capture_palette"]["status"] == "available"
        assert source_options["capture_palette"]["action"] == "open_capture_palette"
        assert source_options["screenshot_attachment"]["status"] == "available_no_text_extraction"
        assert source_options["studio_shortcuts"]["target_panel"] == "settings"
        assert source_options["active_browser_artifact_capture"]["status"] in {
            "disabled_in_settings",
            "available_select_artifact",
        }
        assert source_options["active_browser_artifact_capture"]["action"] in {
            "open_settings_collectors",
            "run_browser_artifact_collector",
        }
        assert source_options["browser_extension_capture"]["status"] in {
            "disabled_in_settings",
            "available_select_extension_artifact",
        }
        assert source_options["browser_extension_capture"]["action"] in {
            "open_settings_collectors",
            "run_browser_extension_collector",
        }
        assert source_options["browser_extension_capture"]["source_mode"] in {
            None,
            "manual_text",
        }
        assert source_options["active_browser_tab_capture"]["status"] in {
            "disabled_in_settings",
            "available_click_to_capture",
        }
        assert source_options["active_browser_tab_capture"]["action"] in {
            "open_settings_collectors",
            "run_active_browser_collector",
        }
        assert source_options["active_browser_tab_capture"]["source_mode"] in {
            None,
            "controlled_html_artifact",
        }
        assert source_options["chaseos_browser_page_capture"]["status"] in {
            "disabled_in_settings",
            "available_click_to_capture",
        }
        assert source_options["chaseos_browser_page_capture"]["action"] in {
            "open_settings_collectors",
            "run_chaseos_browser_page_collector",
        }
        assert source_options["discord_capture"]["status"] in {
            "disabled_in_settings",
            "available_select_artifact",
        }
        assert source_options["discord_capture"]["action"] in {
            "open_settings_collectors",
            "run_discord_artifact_collector",
        }
        assert source_options["screen_capture"]["status"] in {
            "disabled_in_settings",
            "available_click_to_capture",
        }
        assert source_options["screen_capture"]["action"] in {
            "open_settings_collectors",
            "run_screen_capture_collector",
        }
        assert source_options["display_region_capture"]["status"] in {
            "disabled_in_settings",
            "available_drag_select_to_capture",
        }
        assert source_options["display_region_capture"]["action"] in {
            "open_settings_collectors",
            "run_display_region_collector",
        }
        assert source_options["display_region_capture"]["source_mode"] in {
            None,
            "screenshot_text_extraction",
        }
        assert source_options["active_window_capture"]["status"] in {
            "disabled_in_settings",
            "available_active_window_capture",
        }
        assert source_options["active_window_capture"]["action"] in {
            "open_settings_collectors",
            "run_active_window_collector",
        }
        assert source_options["active_window_capture"]["source_mode"] in {
            None,
            "screenshot_text_extraction",
        }
        assert source_options["clipboard_text_capture"]["status"] in {
            "disabled_in_settings",
            "available_click_to_capture",
        }
        assert source_options["clipboard_text_capture"]["action"] in {
            "open_settings_collectors",
            "run_clipboard_text_collector",
        }
        assert source_options["ambient_clipboard_monitor"]["status"] in {
            "disabled_in_settings",
            "available_privacy_gated_monitor",
        }
        assert source_options["ambient_clipboard_monitor"]["action"] in {
            "open_settings_collectors",
            "run_ambient_clipboard_monitor",
        }
        assert source_options["ambient_clipboard_monitor"]["source_mode"] in {
            None,
            "manual_text",
        }
        assert source_options["selected_text_capture"]["status"] in {
            "disabled_in_settings",
            "available_click_to_capture",
        }
        assert source_options["selected_text_capture"]["action"] in {
            "open_settings_collectors",
            "run_selected_text_collector",
        }
        assert source_options["selected_text_capture"]["source_mode"] in {
            None,
            "manual_text",
        }
        assert source_options["accessibility_tree_capture"]["status"] in {
            "disabled_in_settings",
            "available_accessibility_tree_capture",
        }
        assert source_options["accessibility_tree_capture"]["action"] in {
            "open_settings_collectors",
            "run_accessibility_tree_collector",
        }
        assert source_options["accessibility_tree_capture"]["source_mode"] in {
            None,
            "manual_text",
        }
        assert source_options["optical_character_recognition"]["status"] in {
            "available_local_engine",
            "available_local_engine_required",
        }
        assert source_options["optical_character_recognition"]["source_mode"] == "screenshot_text_extraction"
        assert source_options["photo_document_text_extraction"]["status"] == "available_local_extraction"
        assert source_options["photo_document_text_extraction"]["source_mode"] == "photo_document_text_extraction"
        assert source_options["source_intelligence_core_ingestion"]["status"] == "downstream_approval_gated"
        assert source_options["canonical_promotion"]["status"] == "downstream_approval_gated"
        assert source_options["agent_dispatch"]["status"] == "downstream_approval_gated"
        release_readiness = data["release_readiness"]
        assert release_readiness["status"] == "release_ready_explicit_capture_paths_verified"
        assert release_readiness["summary"]["core_capture_verified"] is True
        assert release_readiness["summary"]["settings_shortcuts_visible"] is True
        assert release_readiness["summary"]["settings_collector_shortcuts_visible"] is True
        assert release_readiness["summary"]["local_image_text_adapter_ready"] is True
        assert release_readiness["summary"]["local_image_text_real_engine_quality_verified"] is False
        assert release_readiness["summary"]["screen_capture_collector_built"] is True
        assert release_readiness["summary"]["screen_capture_collector_enabled"] is False
        assert release_readiness["summary"]["display_region_capture_collector_built"] is True
        assert release_readiness["summary"]["display_region_capture_collector_enabled"] is False
        assert release_readiness["summary"]["active_window_capture_collector_built"] is True
        assert release_readiness["summary"]["active_window_capture_collector_enabled"] is False
        assert release_readiness["summary"]["clipboard_capture_collector_built"] is True
        assert release_readiness["summary"]["clipboard_capture_collector_enabled"] is False
        assert release_readiness["summary"]["selected_text_capture_collector_built"] is True
        assert release_readiness["summary"]["selected_text_capture_collector_enabled"] is False
        assert release_readiness["summary"]["accessibility_tree_capture_collector_built"] is True
        assert release_readiness["summary"]["accessibility_tree_capture_collector_enabled"] is False
        assert release_readiness["summary"]["browser_artifact_capture_collector_built"] is True
        assert release_readiness["summary"]["browser_artifact_capture_collector_enabled"] is False
        assert release_readiness["summary"]["browser_extension_capture_collector_built"] is True
        assert release_readiness["summary"]["browser_extension_capture_collector_enabled"] is False
        assert release_readiness["summary"]["active_chaseos_browser_capture_collector_built"] is True
        assert release_readiness["summary"]["active_chaseos_browser_capture_collector_enabled"] is False
        assert release_readiness["summary"]["chaseos_browser_page_capture_collector_built"] is True
        assert release_readiness["summary"]["chaseos_browser_page_capture_collector_enabled"] is False
        assert release_readiness["summary"]["discord_artifact_capture_collector_built"] is True
        assert release_readiness["summary"]["discord_artifact_capture_collector_enabled"] is False
        assert release_readiness["summary"]["blocked_collector_count"] == 0
        assert release_readiness["summary"]["manual_or_covered_collector_count"] == 2
        assert release_readiness["summary"]["approval_gated_downstream_count"] == 3
        assert release_readiness["summary"]["release_proof_open_count"] >= 3
        assert "public_signing_handoff_status" in release_readiness["summary"]
        assert "public_signing_ready_to_attempt" in release_readiness["summary"]
        assert "public_signing_certificate_candidate_count" in release_readiness["summary"]
        assert "public_signing_handoff_report" in release_readiness["summary"]
        assert "packaged_window_size_matrix_verified" in release_readiness["summary"]
        assert "packaged_downstream_failure_state_matrix_verified" in release_readiness["summary"]
        release_groups = {group["id"]: group for group in release_readiness["groups"]}
        assert {
            "ready_now",
            "approval_gated_downstream",
            "release_distribution",
            "manual_or_covered_collectors",
            "release_proof_open",
        } <= set(release_groups)
        assert any(
            item["id"] == "public_certificate_authority_signing"
            for item in release_groups["release_distribution"]["items"]
        )
        assert any(
            item["label"] == "Source Intelligence Core ingestion"
            for item in release_groups["approval_gated_downstream"]["items"]
        )
        assert any(
            item["id"] == "active_chaseos_browser_collector"
            for item in release_groups["ready_now"]["items"]
        )
        assert any(
            item["id"] == "ambient_clipboard_monitor"
            for item in release_groups["ready_now"]["items"]
        )
        assert any(
            item["label"] == "Real image text engine quality"
            and item["status"] in {"fixture_proof_required", "unverified_on_this_host"}
            for item in release_groups["release_proof_open"]["items"]
        )
        assert any(
            item["id"] == "packaged_window_size_matrix"
            and item["status"] in {"open", "verified"}
            for item in release_groups["release_proof_open"]["items"]
        )
        assert any(
            item["id"] == "packaged_downstream_action_matrix"
            and item["status"] in {"open", "verified"}
            for item in release_groups["release_proof_open"]["items"]
        )
        assert release_readiness["authority"]["read_only_status_surface"] is True
        assert release_readiness["authority"]["starts_collectors"] is False
        assert data["capture_hotkeys"]["readiness"]["settings_page_visible"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_collector_shortcuts_configurable"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_display_region_collector_shortcut_available"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_active_window_collector_shortcut_available"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_ambient_clipboard_monitor_shortcut_available"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_selected_text_collector_shortcut_available"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_accessibility_tree_collector_shortcut_available"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_browser_artifact_collector_shortcut_available"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_browser_extension_collector_shortcut_available"] is True
        assert (
            data["capture_hotkeys"]["readiness"][
                "studio_window_active_chaseos_browser_collector_shortcut_available"
            ]
            is True
        )
        assert data["capture_hotkeys"]["readiness"]["studio_window_chaseos_browser_page_collector_shortcut_available"] is True
        assert data["capture_hotkeys"]["readiness"]["studio_window_discord_artifact_collector_shortcut_available"] is True
        assert data["capture_hotkeys"]["authority"]["registers_global_hotkeys"] is False
        assert data["capture_hotkeys"]["authority"]["runs_explicit_collectors_from_studio_shortcuts"] is True
        assert data["capture_hotkeys"]["authority"]["reads_controlled_browser_artifact_from_shortcut_without_settings"] is False
        assert data["capture_hotkeys"]["authority"]["launches_chaseos_owned_browser_page_from_shortcut_without_settings"] is False
        assert data["capture_hotkeys"]["authority"]["reads_discord_artifact_from_shortcut_without_settings"] is False
        assert data["capture_hotkeys"]["authority"]["calls_discord_from_shortcut"] is False
        assert data["capture_collectors"]["surface"] == "studio_capture_collectors"
        assert data["capture_collectors"]["readiness"]["screen_capture_collector_built"] is True
        assert data["capture_collectors"]["readiness"]["screen_capture_enabled"] is False
        assert data["capture_collectors"]["readiness"]["display_region_capture_collector_built"] is True
        assert data["capture_collectors"]["readiness"]["display_region_capture_enabled"] is False
        assert data["capture_collectors"]["readiness"]["active_window_capture_collector_built"] is True
        assert data["capture_collectors"]["readiness"]["active_window_capture_enabled"] is False
        assert data["capture_collectors"]["readiness"]["clipboard_capture_collector_built"] is True
        assert data["capture_collectors"]["readiness"]["clipboard_capture_enabled"] is False
        assert data["capture_collectors"]["readiness"]["ambient_clipboard_monitor_built"] is True
        assert data["capture_collectors"]["readiness"]["ambient_clipboard_monitoring_enabled"] is False
        assert data["capture_collectors"]["readiness"]["selected_text_capture_collector_built"] is True
        assert data["capture_collectors"]["readiness"]["selected_text_capture_enabled"] is False
        assert data["capture_collectors"]["readiness"]["accessibility_tree_capture_collector_built"] is True
        assert data["capture_collectors"]["readiness"]["accessibility_tree_capture_enabled"] is False
        assert data["readiness"]["studio_capture_shortcuts_settings_visible"] is True
        assert data["readiness"]["studio_capture_collector_shortcuts_configurable"] is True
        assert data["readiness"]["capture_palette_overlay_ready"] is True
        assert data["readiness"]["explicit_screen_capture_settings_visible"] is True
        assert data["readiness"]["explicit_screen_capture_collector_ready"] is True
        assert data["readiness"]["explicit_screen_capture_enabled"] is False
        assert data["readiness"]["explicit_clipboard_capture_settings_visible"] is True
        assert data["readiness"]["explicit_clipboard_capture_collector_ready"] is True
        assert data["readiness"]["explicit_clipboard_capture_enabled"] is False
        assert data["readiness"]["ambient_clipboard_monitor_ready"] is True
        assert data["readiness"]["ambient_clipboard_monitor_enabled"] is False
        assert data["readiness"]["ambient_clipboard_monitor_requires_privacy_opt_in"] is True
        assert data["readiness"]["ambient_clipboard_monitor_reads_on_settings_load"] is False
        assert data["readiness"]["explicit_selected_text_capture_settings_visible"] is True
        assert data["readiness"]["explicit_selected_text_capture_collector_ready"] is True
        assert data["readiness"]["explicit_selected_text_capture_enabled"] is False
        assert data["readiness"]["explicit_accessibility_tree_capture_settings_visible"] is True
        assert data["readiness"]["explicit_accessibility_tree_capture_collector_ready"] is True
        assert data["readiness"]["explicit_accessibility_tree_capture_enabled"] is False

        assert data["readiness"]["clipboard_capture_reads_on_settings_load"] is False
        assert data["readiness"]["clipboard_capture_reads_on_capture_panel_load"] is False
        assert data["readiness"]["selected_text_capture_uses_temporary_clipboard_copy"] is True
        assert data["readiness"]["selected_text_capture_restores_text_clipboard_when_possible"] is True
        assert data["readiness"]["selected_text_capture_reads_on_settings_load"] is False
        assert data["readiness"]["selected_text_capture_reads_on_capture_panel_load"] is False
        assert data["readiness"]["accessibility_tree_capture_reads_on_settings_load"] is False
        assert data["readiness"]["accessibility_tree_capture_reads_on_capture_panel_load"] is False
        assert data["readiness"]["global_hotkey_registration_available"] is True
        assert data["readiness"]["global_hotkey_registration_enabled"] is False
        assert data["readiness"]["global_hotkey_registration_blocked"] is False
        assert data["readiness"]["capture_release_readiness_surface_ready"] is True
        assert data["readiness"]["capture_release_readiness_read_only"] is True
        assert data["readiness"]["controlled_browser_artifact_extractor_ready"] is True
        assert data["readiness"]["controlled_browser_artifact_collector_ready"] is True
        assert data["readiness"]["controlled_browser_artifact_collector_enabled"] is False
        assert data["readiness"]["controlled_browser_artifact_collector_requires_operator_click"] is True
        assert data["readiness"]["controlled_browser_artifact_collector_requires_operator_selected_file"] is True
        assert data["readiness"]["controlled_browser_artifact_collector_requires_declared_url"] is True
        assert data["readiness"]["browser_extension_capture_collector_ready"] is True
        assert data["readiness"]["browser_extension_capture_collector_enabled"] is False
        assert data["readiness"]["browser_extension_capture_requires_operator_selected_file"] is True
        assert data["readiness"]["chaseos_browser_page_collector_ready"] is True
        assert data["readiness"]["chaseos_browser_page_collector_enabled"] is False
        assert data["readiness"]["chaseos_browser_page_collector_requires_operator_click"] is True
        assert data["readiness"]["chaseos_browser_page_collector_requires_declared_url"] is True
        assert data["readiness"]["chaseos_browser_page_collector_reads_personal_browser"] is False
        assert data["readiness"]["controlled_discord_artifact_collector_ready"] is True
        assert data["readiness"]["controlled_discord_artifact_collector_enabled"] is False
        assert data["readiness"]["controlled_discord_artifact_collector_requires_operator_click"] is True
        assert data["readiness"]["controlled_discord_artifact_collector_requires_operator_selected_file"] is True
        assert data["readiness"]["controlled_discord_artifact_collector_requires_declared_source"] is True
        assert data["readiness"]["controlled_discord_artifact_collector_calls_discord_api"] is False
        assert data["readiness"]["screenshot_attachment_import_ready"] is True
        assert data["readiness"]["screenshot_attachment_quarantine_copy_ready"] is True
        assert data["readiness"]["screenshot_attachment_retention_policy_ready"] is True
        assert data["readiness"]["screenshot_attachment_cleanup_requires_operator_decision"] is True
        assert data["readiness"]["screenshot_attachment_runtime_delete_blocked"] is True
        assert data["readiness"]["screenshot_attachment_ocr_disabled"] is True
        assert data["readiness"]["screenshot_text_extraction_ready"] is True
        assert data["readiness"]["photo_document_text_extraction_ready"] is True
        assert data["readiness"]["photo_document_text_extraction_cloud_blocked"] is True
        assert data["readiness"]["local_optical_character_recognition_adapter_ready"] is True
        assert data["readiness"]["local_optical_character_recognition_real_engine_quality_verified"] is False
        assert data["capture_local_image_text"]["quality_fixture_proof"]["surface"] == "studio_capture_local_image_text_quality_fixtures"
        assert data["readiness"]["cloud_ocr_blocked"] is True
        assert data["readiness"]["cloud_optical_character_recognition_blocked"] is True
        assert data["readiness"]["external_surface_deferral_policy_ready"] is True
        assert data["readiness"]["operator_review_state_machine_ready"] is True
        assert data["readiness"]["operator_review_cli_ready"] is True
        assert data["readiness"]["operator_review_api_ready"] is True
        assert data["readiness"]["operator_review_studio_clickthrough_ready"] is True
        assert data["readiness"]["attachment_disposition_policy_ready"] is True
        assert data["readiness"]["attachment_disposition_metadata_only"] is False
        assert data["readiness"]["attachment_disposition_runtime_delete_blocked"] is True
        assert data["readiness"]["attachment_disposition_studio_delete_controls_ready"] is True
        assert data["readiness"]["attachment_cleanup_requires_exact_operator_confirmation"] is True
        assert data["readiness"]["reviewed_capture_downstream_gate_ready"] is True
        assert data["readiness"]["reviewed_capture_acquisition_preview_gate_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_approval_preview_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_approval_preview_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_approval_preview_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_approval_artifact_write_blocked"] is True
        assert data["readiness"]["reviewed_capture_source_pack_write_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_write_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_write_requires_exact_approval"] is True
        assert data["readiness"]["reviewed_capture_source_pack_write_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_write_blocked_without_exact_approval"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_packet_preview_ready_after_write"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_design_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_design_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_design_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_request_writer_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_request_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_request_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_request_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_request_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_artifact_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_request_overwrite_blocked"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_blocked"] is False
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_marker_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_blocked"] is False
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_blocked"] is False
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_execute_blocked"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_marker_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_blocked_without_exact_approval"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_future_packet_preview_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_marker_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_blocked"] is False
        assert data["readiness"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_source_pack_writeback_allowed"] is True
        assert data["readiness"]["reviewed_capture_aor_dispatch_executor_blocked"] is False
        assert data["readiness"]["reviewed_capture_aor_dispatch_blocked"] is False
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_readiness_requires_full_dispatch_artifact"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_readiness_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_future_packet_preview_ready_after_full_dispatch"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_design_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_design_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_design_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_design_requires_readiness_packet_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_request_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_request_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_request_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_marker_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_overwrite_blocked"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_marker_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_ingestion_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_candidate_preview_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_indexing_requires_operator_statement"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_snapshot_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_sic_graph_store_manifest_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_requires_exact_graph_artifact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_candidate_preview_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_design_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_design_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_design_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_request_writer_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_request_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_request_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_request_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_request_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_read_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_pending_request"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_canonical_promotion_approval_decision_writer_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ui_ready"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_marker_create_only"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_requires_exact_digest"] is True
        assert data["readiness"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_write_allowed"] is True
        assert data["readiness"]["reviewed_capture_canonical_promotion_approval_consumption_ready"] is True
        assert data["readiness"]["reviewed_capture_sic_ingestion_blocked"] is False
        assert data["readiness"]["reviewed_capture_graph_or_canonical_promotion_blocked"] is True
        assert data["readiness"]["external_capture_surfaces_deferred"] is True
        assert data["readiness"]["hotkey_capture_blocked"] is True
        assert data["readiness"]["overlay_capture_blocked"] is False
        assert data["readiness"]["display_region_drag_select_overlay_ready"] is True
        assert data["readiness"]["capture_palette_overlay_blocked"] is False
        assert data["readiness"]["ambient_clipboard_capture_blocked"] is False
        assert data["readiness"]["discord_capture_commands_blocked"] is False
        assert data["readiness"]["external_control_plane_capture_blocked"] is True
        assert data["readiness"]["external_browser_tab_capture_blocked"] is True
        assert data["readiness"]["accessibility_tree_capture_blocked"] is False
        assert data["authority"]["browser_history_allowed"] is False
        assert data["authority"]["screenshot_attachment_runtime_delete_allowed"] is False
        assert data["authority"]["attachment_disposition_policy_ready"] is True
        assert data["authority"]["attachment_disposition_runtime_delete_allowed"] is False
        assert data["authority"]["attachment_disposition_studio_delete_controls_allowed"] is True
        assert data["authority"]["attachment_cleanup_requires_exact_operator_confirmation"] is True
        assert data["authority"]["reviewed_capture_downstream_gate_ready"] is True
        assert data["authority"]["reviewed_capture_downstream_gate_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_approval_preview_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_approval_preview_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_approval_preview_write_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_approval_artifact_write_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_write_executor_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_write_requires_exact_approval"] is True
        assert data["authority"]["reviewed_capture_source_pack_write_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_rewrite_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_design_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_design_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_design_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_request_writer_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_request_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_request_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_request_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_request_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_artifact_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_marker_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_write_allowed"] is True
        assert data["authority"]["reviewed_capture_aor_dispatch_approval_consumption_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_task_execute_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_marker_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_blocked_without_exact_approval"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_future_packet_preview_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_source_pack_writeback_allowed"] is True
        assert data["authority"]["reviewed_capture_aor_dispatch_executor_ready"] is True
        assert data["authority"]["reviewed_capture_aor_dispatch_allowed"] is True
        assert data["authority"]["reviewed_capture_aor_dispatch_source_pack_writeback_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_future_packet_preview_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_design_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_design_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_design_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_design_requires_readiness_packet_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_packet_preview_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_request_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_request_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_request_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_artifact_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_request_overwrite_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_decision_overwrite_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_marker_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_overwrite_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_approval_consumption_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_executor_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_executor_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_ingestion_write_allowed"] is True
        assert data["authority"]["reviewed_capture_sic_ingestion_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_graph_indexing_readiness_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_graph_candidate_preview_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_graph_indexing_executor_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_sic_graph_indexing_executor_ui_ready"] is True
        assert data["authority"]["reviewed_capture_graph_index_mutation_allowed"] is True
        assert data["authority"]["reviewed_capture_graph_snapshot_write_allowed"] is True
        assert data["authority"]["reviewed_capture_graph_store_manifest_write_allowed"] is True
        assert data["authority"]["reviewed_capture_graph_current_pointer_update_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_requires_exact_graph_artifact_digest"] is True
        assert data["authority"]["reviewed_capture_canonical_promotion_candidate_preview_allowed"] is True
        assert data["authority"]["reviewed_capture_canonical_promotion_approval_required"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_design_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_design_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_design_read_only"] is True
        assert data["authority"]["reviewed_capture_canonical_promotion_approval_packet_preview_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_request_writer_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_request_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_request_create_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_request_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_request_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_artifact_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_request_overwrite_allowed"] is False
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_read_only"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_pending_request"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_exact_digest"] is True
        assert data["authority"]["reviewed_capture_canonical_promotion_approval_decision_writer_ready"] is True
        assert data["authority"]["reviewed_capture_canonical_promotion_approval_decision_write_allowed"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ui_ready"] is True
        assert data["authority"]["reviewed_capture_source_pack_canonical_promotion_approval_consumption_write_allowed"] is True
        assert data["authority"]["reviewed_capture_canonical_promotion_approval_consumption_allowed"] is True
        assert data["authority"]["reviewed_capture_canonical_promotion_approval_exact_once_marker_write_allowed"] is True
        assert data["authority"]["reviewed_capture_canonical_mutation_allowed"] is False
        assert data["authority"]["reviewed_capture_sic_workspace_write_allowed"] is True
        assert data["authority"]["reviewed_capture_sic_source_package_write_allowed"] is True
        assert data["authority"]["reviewed_capture_sic_workspace_membership_write_allowed"] is True
        assert data["authority"]["reviewed_capture_graph_or_canonical_promotion_allowed"] is False
        assert data["authority"]["screen_pixel_capture_allowed"] is False
        assert data["authority"]["global_hotkey_capture_allowed"] is True
        assert data["authority"]["overlay_capture_allowed"] is True
        assert data["authority"]["capture_palette_allowed"] is True
        assert data["authority"]["ambient_clipboard_capture_allowed"] is True
        assert data["authority"]["discord_command_capture_allowed"] is True
        assert data["authority"]["external_control_plane_capture_allowed"] is False
        assert data["authority"]["active_browser_tab_capture_allowed"] is False
        assert data["authority"]["accessibility_tree_capture_allowed"] is True
        assert data["authority"]["ocr_allowed"] is True
        assert data["authority"]["local_optical_character_recognition_allowed_with_explicit_image"] is True
        assert data["authority"]["cloud_ocr_allowed"] is False
        assert data["authority"]["cloud_optical_character_recognition_allowed"] is False
        assert data["authority"]["studio_window_capture_collector_shortcuts_allowed"] is True
        assert data["storage_policy"]["attachment_retention"] == "retain_until_operator_review"
        assert data["storage_policy"]["attachment_review_status"] == "pending-review"
        assert (
            data["storage_policy"]["attachment_cleanup"]
            == "quarantine_local_only_after_exact_operator_confirmation"
        )
        assert (
            data["storage_policy"]["attachment_disposition"]
            == "operator_controlled_metadata_and_guarded_cleanup"
        )
        assert data["storage_policy"]["operator_review_state_machine"] == "sidecar_packet_only"
        assert data["storage_policy"]["operator_review_studio_clickthrough"] == "mounted_sidecar_packet_only"
        assert data["storage_policy"]["reviewed_capture_downstream_gate"] == "read_only_gate_readiness"
        assert data["storage_policy"]["reviewed_capture_source_pack_approval_preview"] == "read_only_operator_preview"
        assert data["storage_policy"]["source_pack_write"] == "exact_approval_guarded_create_only_pack_artifacts"
        assert data["storage_policy"]["source_pack_aor_dispatch_readiness"] == "read_only_after_source_pack_write"
        assert data["storage_policy"]["source_pack_aor_dispatch_approval_design"] == "read_only_after_aor_dispatch_readiness"
        assert data["storage_policy"]["source_pack_aor_dispatch_approval_request"] == "exact_digest_statement_guarded_create_only_pending_approval_request"
        assert data["storage_policy"]["source_pack_aor_dispatch_approval_consumption_readiness"] == "read_only_pending_approval_request_validation"
        assert data["storage_policy"]["source_pack_aor_dispatch_approval_decision"] == "exact_digest_statement_guarded_create_only_decision_artifact"
        assert data["storage_policy"]["source_pack_aor_dispatch_approval_consumption"] == "exact_digest_statement_guarded_create_only_marker_and_consumption_artifact"
        assert data["storage_policy"]["source_pack_aor_dispatch_agent_bus_task"] == "exact_digest_statement_guarded_create_only_marker_open_task_and_task_artifact"
        assert data["storage_policy"]["source_pack_aor_dispatch_agent_bus_task_claim_readiness"] == "read_only_open_unclaimed_task_claimability_and_route_liveness"
        assert data["storage_policy"]["source_pack_aor_dispatch_agent_bus_task_claim"] == "exact_digest_statement_guarded_marker_claim_and_claim_artifact"
        assert data["storage_policy"]["source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle"] == "exact_digest_statement_guarded_marker_review_status_update_and_artifact"
        assert data["storage_policy"]["source_pack_aor_dispatch_agent_bus_full_dispatch_readiness"] == "read_only_reviewed_task_status_artifact_and_future_full_dispatch_packet_preview"
        assert data["storage_policy"]["source_pack_aor_dispatch_agent_bus_full_dispatch_executor"] == "exact_digest_statement_guarded_marker_non_dry_run_aor_source_pack_writeback_and_artifact"
        assert data["storage_policy"]["source_pack_sic_ingestion_readiness"] == "read_only_pass28_source_pack_writeback_and_future_sic_ingestion_packet_preview"
        assert data["storage_policy"]["source_pack_sic_ingestion_approval_design"] == "read_only_future_source_intelligence_core_ingestion_approval_packet_preview"
        assert data["storage_policy"]["source_pack_sic_ingestion_approval_request"] == "exact_digest_statement_guarded_create_only_pending_source_intelligence_core_ingestion_approval_request"
        assert data["storage_policy"]["source_pack_sic_ingestion_approval_decision_consumption_readiness"] == "read_only_pending_source_intelligence_core_ingestion_approval_request_validation"
        assert data["storage_policy"]["source_pack_sic_ingestion_approval_decision"] == "exact_digest_statement_guarded_create_only_source_intelligence_core_ingestion_approval_decision"
        assert data["storage_policy"]["source_pack_sic_ingestion_approval_consumption"] == "exact_digest_statement_guarded_marker_then_create_only_source_intelligence_core_ingestion_approval_consumption"
        assert data["storage_policy"]["source_pack_sic_ingestion"] == "exact_digest_statement_guarded_marker_then_source_intelligence_core_workspace_source_package_membership_and_artifact"
        assert data["storage_policy"]["source_pack_sic_graph_indexing_readiness"] == "read_only_source_intelligence_core_ingestion_artifact_to_graph_candidate_preview"
        assert data["storage_policy"]["source_pack_sic_graph_indexing_executor"] == "exact_digest_statement_gated_graph_snapshot_manifest_current_pointer_write"
        assert data["storage_policy"]["source_pack_canonical_promotion_readiness"] == "read_only_graph_indexing_artifact_to_canonical_promotion_candidate_preview"
        assert data["storage_policy"]["source_pack_canonical_promotion_approval_design"] == "read_only_canonical_promotion_candidate_to_future_approval_packet_preview"
        assert data["storage_policy"]["source_pack_canonical_promotion_approval_request"] == "exact_digest_statement_guarded_create_only_pending_canonical_promotion_approval_request"
        assert data["storage_policy"]["source_pack_canonical_promotion_approval_decision_consumption_readiness"] == "read_only_pending_canonical_promotion_approval_request_to_future_decision_consumption_contract_preview"
        assert data["storage_policy"]["source_pack_canonical_promotion_approval_decision"] == "exact_digest_statement_guarded_create_only_canonical_promotion_approval_decision"
        assert data["storage_policy"]["source_pack_canonical_promotion_approval_consumption"] == "exact_digest_statement_guarded_create_only_marker_then_consumption"
        assert data["storage_policy"]["graph_canonical_promotion"] == "canonical_promotion_candidate_preview_available_but_canonical_writes_blocked"
        assert data["storage_policy"]["sic_ingestion"] == "implemented_for_reviewed_capture_markdown_source_package_only_graph_and_canonical_blocked"
        assert data["storage_policy"]["source_pack_rewrite"] == "blocked"
        assert data["storage_policy"]["aor_dispatch"] == "blocked"
        assert data["storage_policy"]["runtime_deletion"] == "blocked"
        assert data["storage_policy"]["external_capture_surfaces"] == "deferred_blocked"
        policy = data["external_surface_policy"]
        assert policy["policy_id"] == "vcmi.external_capture_surfaces.deferred.v1"
        assert policy["all_external_capture_surfaces_blocked"] is False
        assert "global_hotkey_capture" in policy["implemented_surface_ids"]
        assert "active_window_capture" in policy["implemented_surface_ids"]
        assert "global_hotkey_capture" not in policy["blocked_surface_ids"]
        assert "discord_command_capture" in policy["implemented_surface_ids"]
        assert "discord_command_capture" not in policy["blocked_surface_ids"]
        assert "manual_text" in policy["safe_current_inputs"]
        review_policy = data["operator_review_state_policy"]
        assert review_policy["policy_id"] == "vcmi.operator_review_state.v1"
        assert review_policy["authority"]["content_write_allowed"] is False
        assert "reviewed" in review_policy["statuses"]
        disposition_policy = data["attachment_disposition_policy"]
        assert disposition_policy["policy_id"] == "vcmi.attachment_disposition.v1"
        assert disposition_policy["status"] == "metadata_policy_only"
        assert disposition_policy["runtime_delete_allowed"] is False
        assert disposition_policy["studio_delete_controls_allowed"] is True
        assert disposition_policy["cleanup_executor_available"] is True
        assert "delete-requested" in disposition_policy["supported_dispositions"]
        downstream_policy = data["downstream_gate_policy"]
        assert downstream_policy["policy_id"] == "vcmi.reviewed_capture_downstream_gate.v1"
        assert downstream_policy["authority"]["source_pack_write_allowed"] is False
        assert downstream_policy["future_source_pack_task_type"] == "source-pack-builder"
        approval_policy = data["source_pack_approval_preview_policy"]
        assert approval_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_write_approval_preview.v1"
        assert approval_policy["authority"]["approval_artifact_write_allowed"] is False
        assert approval_policy["authority"]["source_pack_write_allowed"] is False
        assert approval_policy["required_operator_statement"]
        executor_policy = data["source_pack_write_executor_policy"]
        assert executor_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_write_executor.v1"
        assert executor_policy["authority"]["source_pack_write_allowed"] is True
        assert executor_policy["authority"]["source_pack_overwrite_allowed"] is False
        assert executor_policy["authority"]["aor_dispatch_allowed"] is False
        aor_policy = data["source_pack_aor_dispatch_readiness_policy"]
        assert aor_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_readiness.v1"
        assert aor_policy["aor_engine_invocation_allowed"] is False
        assert aor_policy["authority"]["aor_dispatch_allowed"] is False
        assert aor_policy["authority"]["agent_bus_task_write_allowed"] is False
        aor_approval_policy = data["source_pack_aor_dispatch_approval_design_policy"]
        assert aor_approval_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_approval_design.v1"
        assert aor_approval_policy["approval_request_write_allowed"] is False
        assert aor_approval_policy["approval_artifact_write_allowed"] is False
        assert aor_approval_policy["approval_consumption_allowed"] is False
        assert aor_approval_policy["authority"]["aor_dispatch_allowed"] is False
        aor_approval_request_policy = data["source_pack_aor_dispatch_approval_request_writer_policy"]
        assert aor_approval_request_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_approval_request_writer.v1"
        assert aor_approval_request_policy["approval_request_write_allowed"] is True
        assert aor_approval_request_policy["approval_artifact_write_allowed"] is True
        assert aor_approval_request_policy["approval_consumption_allowed"] is False
        assert aor_approval_request_policy["authority"]["aor_dispatch_allowed"] is False
        aor_approval_consumption_policy = data["source_pack_aor_dispatch_approval_consumption_readiness_policy"]
        assert aor_approval_consumption_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness.v1"
        aor_approval_decision_policy = data["source_pack_aor_dispatch_approval_decision_writer_policy"]
        assert aor_approval_decision_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_approval_decision_writer.v1"
        assert aor_approval_decision_policy["approval_decision_write_allowed"] is True
        assert aor_approval_decision_policy["approval_consumption_allowed"] is False
        assert aor_approval_consumption_policy["approval_decision_write_allowed"] is False
        assert aor_approval_consumption_policy["approval_consumption_allowed"] is False
        assert aor_approval_consumption_policy["approval_exact_once_marker_write_allowed"] is False
        assert aor_approval_consumption_policy["authority"]["aor_dispatch_allowed"] is False
        aor_approval_consumption_executor_policy = data["source_pack_aor_dispatch_approval_consumption_executor_policy"]
        assert aor_approval_consumption_executor_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor.v1"
        assert aor_approval_consumption_executor_policy["approval_consumption_allowed"] is True
        assert aor_approval_consumption_executor_policy["approval_exact_once_marker_write_allowed"] is True
        assert aor_approval_consumption_executor_policy["agent_bus_task_write_allowed"] is False
        assert aor_approval_consumption_executor_policy["aor_engine_invocation_allowed"] is False
        aor_agent_bus_task_policy = data["source_pack_aor_dispatch_agent_bus_task_writer_policy"]
        assert aor_agent_bus_task_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer.v1"
        assert aor_agent_bus_task_policy["agent_bus_task_write_allowed"] is True
        assert aor_agent_bus_task_policy["agent_bus_task_claim_allowed"] is False
        assert aor_agent_bus_task_policy["aor_engine_invocation_allowed"] is False
        aor_agent_bus_task_claim_policy = data["source_pack_aor_dispatch_agent_bus_task_claim_readiness_policy"]
        assert aor_agent_bus_task_claim_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness.v1"
        assert aor_agent_bus_task_claim_policy["agent_bus_task_claim_readiness_allowed"] is True
        assert aor_agent_bus_task_claim_policy["agent_bus_task_claim_allowed"] is False
        assert aor_agent_bus_task_claim_policy["writes_allowed"] is False
        aor_agent_bus_task_claim_executor_policy = data["source_pack_aor_dispatch_agent_bus_task_claim_executor_policy"]
        assert aor_agent_bus_task_claim_executor_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor.v1"
        assert aor_agent_bus_task_claim_executor_policy["agent_bus_task_claim_executor_allowed"] is True
        assert aor_agent_bus_task_claim_executor_policy["agent_bus_task_claim_allowed"] is True
        assert aor_agent_bus_task_claim_executor_policy["agent_bus_task_execute_allowed"] is False
        status_lifecycle_policy = data["source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_policy"]
        assert status_lifecycle_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle.v1"
        assert status_lifecycle_policy["agent_bus_task_status_update_allowed"] is True
        assert status_lifecycle_policy["agent_bus_task_target_status"] == "review"
        assert status_lifecycle_policy["agent_bus_task_execute_allowed"] is False
        full_dispatch_readiness_policy = data["source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_policy"]
        assert full_dispatch_readiness_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness.v1"
        assert full_dispatch_readiness_policy["writes_allowed"] is False
        assert full_dispatch_readiness_policy["requires_agent_bus_task_status"] == "review"
        assert full_dispatch_readiness_policy["agent_bus_task_execute_allowed"] is False
        assert full_dispatch_readiness_policy["aor_full_run_allowed"] is False
        full_dispatch_executor_policy = data["source_pack_aor_dispatch_agent_bus_full_dispatch_executor_policy"]
        assert full_dispatch_executor_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor.v1"
        assert full_dispatch_executor_policy["writes_allowed"] is True
        assert full_dispatch_executor_policy["aor_full_run_allowed"] is True
        assert full_dispatch_executor_policy["source_pack_writeback_allowed"] is True
        assert full_dispatch_executor_policy["agent_bus_task_execute_allowed"] is False
        assert full_dispatch_executor_policy["sic_ingestion_allowed"] is False
        sic_readiness_policy = data["source_pack_sic_ingestion_readiness_policy"]
        assert sic_readiness_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_sic_ingestion_readiness.v1"
        assert sic_readiness_policy["read_only"] is True
        assert sic_readiness_policy["writes_allowed"] is False
        assert sic_readiness_policy["requires_full_dispatch_artifact"] is True
        assert sic_readiness_policy["requires_source_pack_writeback"] is True
        assert sic_readiness_policy["sic_ingestion_allowed"] is False
        assert sic_readiness_policy["sic_source_package_write_allowed"] is False
        assert sic_readiness_policy["graph_index_mutation_allowed"] is False
        sic_approval_request_policy = data["source_pack_sic_ingestion_approval_request_writer_policy"]
        assert sic_approval_request_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_sic_ingestion_approval_request_writer.v1"
        assert sic_approval_request_policy["approval_request_write_allowed"] is True
        assert sic_approval_request_policy["approval_request_overwrite_allowed"] is False
        assert sic_approval_request_policy["approval_decision_write_allowed"] is False
        assert sic_approval_request_policy["approval_consumption_allowed"] is False
        assert sic_approval_request_policy["source_intelligence_core_ingestion_allowed"] is False
        assert sic_approval_request_policy["graph_index_mutation_allowed"] is False
        assert sic_approval_request_policy["canonical_mutation_allowed"] is False
        sic_approval_readiness_policy = data["source_pack_sic_ingestion_approval_consumption_readiness_policy"]
        assert sic_approval_readiness_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_sic_ingestion_approval_consumption_readiness.v1"
        assert sic_approval_readiness_policy["approval_decision_write_allowed"] is False
        assert sic_approval_readiness_policy["approval_consumption_allowed"] is False
        assert sic_approval_readiness_policy["source_intelligence_core_ingestion_allowed"] is False
        assert sic_approval_readiness_policy["graph_index_mutation_allowed"] is False
        assert sic_approval_readiness_policy["canonical_mutation_allowed"] is False
        sic_approval_decision_policy = data["source_pack_sic_ingestion_approval_decision_writer_policy"]
        assert sic_approval_decision_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_sic_ingestion_approval_decision_writer.v1"
        assert sic_approval_decision_policy["approval_decision_write_allowed"] is True
        assert sic_approval_decision_policy["approval_decision_overwrite_allowed"] is False
        assert sic_approval_decision_policy["approval_consumption_allowed"] is False
        assert sic_approval_decision_policy["source_intelligence_core_ingestion_allowed"] is False
        assert sic_approval_decision_policy["graph_index_mutation_allowed"] is False
        assert sic_approval_decision_policy["canonical_mutation_allowed"] is False
        sic_approval_consumption_policy = data["source_pack_sic_ingestion_approval_consumption_executor_policy"]
        assert sic_approval_consumption_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor.v1"
        assert sic_approval_consumption_policy["approval_consumption_allowed"] is True
        assert sic_approval_consumption_policy["approval_exact_once_marker_write_allowed"] is True
        assert sic_approval_consumption_policy["source_intelligence_core_ingestion_allowed"] is False
        assert sic_approval_consumption_policy["graph_index_mutation_allowed"] is False
        assert sic_approval_consumption_policy["canonical_mutation_allowed"] is False
        canonical_approval_request_policy = data["source_pack_canonical_promotion_approval_request_writer_policy"]
        assert canonical_approval_request_policy["policy_id"] == "vcmi.reviewed_capture_source_pack_canonical_promotion_approval_request_writer.v1"
        assert canonical_approval_request_policy["approval_request_write_allowed"] is True
        assert canonical_approval_request_policy["approval_request_overwrite_allowed"] is False
        assert canonical_approval_request_policy["approval_decision_write_allowed"] is False
        assert canonical_approval_request_policy["approval_consumption_allowed"] is False
        assert canonical_approval_request_policy["canonical_promotion_executor_allowed"] is False
        assert canonical_approval_request_policy["canonical_knowledge_note_write_allowed"] is False
        assert canonical_approval_request_policy["canonical_knowledge_index_write_allowed"] is False
        assert canonical_approval_request_policy["provider_call_allowed"] is False
        assert canonical_approval_request_policy["external_send_allowed"] is False
        canonical_approval_readiness_policy = data[
            "source_pack_canonical_promotion_approval_consumption_readiness_policy"
        ]
        assert (
            canonical_approval_readiness_policy["policy_id"]
            == "vcmi.reviewed_capture_source_pack_canonical_promotion_approval_consumption_readiness.v1"
        )
        assert canonical_approval_readiness_policy["approval_decision_write_allowed"] is False
        assert canonical_approval_readiness_policy["approval_consumption_allowed"] is False
        assert canonical_approval_readiness_policy["canonical_promotion_executor_allowed"] is False
        assert canonical_approval_readiness_policy["canonical_knowledge_note_write_allowed"] is False
        assert canonical_approval_readiness_policy["canonical_knowledge_index_write_allowed"] is False
        assert canonical_approval_readiness_policy["provider_call_allowed"] is False
        assert canonical_approval_readiness_policy["external_send_allowed"] is False
        canonical_approval_decision_policy = data[
            "source_pack_canonical_promotion_approval_decision_writer_policy"
        ]
        assert (
            canonical_approval_decision_policy["policy_id"]
            == "vcmi.reviewed_capture_source_pack_canonical_promotion_approval_decision_writer.v1"
        )
        assert canonical_approval_decision_policy["approval_decision_write_allowed"] is True
        assert canonical_approval_decision_policy["approval_decision_overwrite_allowed"] is False
        assert canonical_approval_decision_policy["approval_consumption_allowed"] is False
        assert canonical_approval_decision_policy["canonical_promotion_executor_allowed"] is False
        assert canonical_approval_decision_policy["canonical_knowledge_note_write_allowed"] is False
        assert canonical_approval_decision_policy["canonical_knowledge_index_write_allowed"] is False
        assert canonical_approval_decision_policy["provider_call_allowed"] is False
        assert canonical_approval_decision_policy["external_send_allowed"] is False
        canonical_approval_consumption_policy = data[
            "source_pack_canonical_promotion_approval_consumption_executor_policy"
        ]
        assert (
            canonical_approval_consumption_policy["policy_id"]
            == "vcmi.reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor.v1"
        )
        assert canonical_approval_consumption_policy["approval_consumption_allowed"] is True
        assert canonical_approval_consumption_policy["approval_exact_once_marker_write_allowed"] is True
        assert canonical_approval_consumption_policy["approval_consumption_overwrite_allowed"] is False
        assert canonical_approval_consumption_policy["canonical_promotion_executor_allowed"] is False
        assert canonical_approval_consumption_policy["canonical_knowledge_note_write_allowed"] is False
        assert canonical_approval_consumption_policy["canonical_knowledge_index_write_allowed"] is False
        assert canonical_approval_consumption_policy["provider_call_allowed"] is False
        assert canonical_approval_consumption_policy["external_send_allowed"] is False
        canonical_promotion_policy = data["source_pack_canonical_promotion_executor_policy"]
        assert (
            canonical_promotion_policy["policy_id"]
            == "vcmi.reviewed_capture_source_pack_canonical_promotion_executor.v1"
        )
        assert canonical_promotion_policy["canonical_promotion_executor_allowed"] is True
        assert canonical_promotion_policy["canonical_promotion_marker_write_allowed"] is True
        assert canonical_promotion_policy["canonical_knowledge_note_write_allowed"] is True
        assert canonical_promotion_policy["canonical_knowledge_index_write_allowed"] is True
        assert canonical_promotion_policy["canonical_graph_mutation_allowed"] is False
        assert canonical_promotion_policy["source_intelligence_core_rewrite_allowed"] is False
        assert canonical_promotion_policy["provider_call_allowed"] is False
        assert canonical_promotion_policy["external_send_allowed"] is False

    def test_release_readiness_reads_packaged_downstream_failure_matrix(self, tmp_path):
        evidence_root = tmp_path / "07_LOGS" / "Studio-Graph-Views"
        evidence_root.mkdir(parents=True, exist_ok=True)
        report_path = evidence_root / "2026-05-28-capture-markdown-downstream-failure-state-matrix-test.json"
        report_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "status": "packaged_capture_markdown_downstream_failure_state_matrix_complete",
                    "case_count": 3,
                    "cases": [
                        {
                            "id": "aor_approval_request_bad_statement",
                            "label": "Agent Orchestration Runtime approval request",
                            "ok": True,
                            "guard_card_visible": True,
                            "forbidden_artifacts_not_written": True,
                        },
                        {
                            "id": "source_intelligence_core_approval_request_bad_statement",
                            "label": "Source Intelligence Core approval request",
                            "ok": True,
                            "guard_card_visible": True,
                            "forbidden_artifacts_not_written": True,
                        },
                        {
                            "id": "canonical_promotion_approval_request_bad_statement",
                            "label": "Canonical promotion approval request",
                            "ok": True,
                            "guard_card_visible": True,
                            "forbidden_artifacts_not_written": True,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        api = _make_api(tmp_path)
        result = api.get_capture_to_markdown_panel()

        assert result["ok"] is True
        release_readiness = result["data"]["release_readiness"]
        assert release_readiness["summary"]["packaged_downstream_failure_state_matrix_verified"] is True
        assert (
            release_readiness["summary"]["packaged_downstream_failure_state_matrix_report"]
            == "07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-downstream-failure-state-matrix-test.json"
        )
        release_groups = {group["id"]: group for group in release_readiness["groups"]}
        downstream_item = next(
            item
            for item in release_groups["release_proof_open"]["items"]
            if item["id"] == "packaged_downstream_action_matrix"
        )
        assert downstream_item["status"] == "verified"
        assert downstream_item["latest_report"] == release_readiness["summary"][
            "packaged_downstream_failure_state_matrix_report"
        ]

    def test_panel_open_model_does_not_start_subprocesses(self, tmp_path, monkeypatch):
        calls = []

        def fake_run(*args, **kwargs):
            calls.append(("run", args, kwargs))
            raise AssertionError("Capture panel open must not run subprocesses")

        def fake_popen(*args, **kwargs):
            calls.append(("Popen", args, kwargs))
            raise AssertionError("Capture panel open must not launch subprocesses")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(subprocess, "Popen", fake_popen)

        api = _make_api(tmp_path)
        result = api.get_capture_to_markdown_panel(10)

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_panel"
        assert calls == []

    def test_preview_is_no_write(self, tmp_path):
        api = _make_api(tmp_path)
        result = api.preview_capture_to_markdown(_payload())

        assert result["ok"] is True
        data = result["data"]
        assert data["status"] == "preview_only"
        assert data["write_performed"] is False
        assert data["save_allowed"] is True
        assert data["authority"]["raw_ingestion_write"] is False
        assert not (tmp_path / "03_INPUTS").exists()
        assert "Studio VCMI Capture" in data["markdown"]

    def test_save_writes_only_raw_quarantine_artifacts(self, tmp_path):
        api = _make_api(tmp_path)
        result = api.save_capture_to_markdown(_payload(text="Unique save text for pass three."))

        assert result["ok"] is True
        data = result["data"]
        assert data["status"] == "raw_ingested"
        assert data["write_performed"] is True
        assert data["panel_authority"]["canonical_mutation_allowed"] is False
        assert data["panel_authority"]["graph_index_mutation_allowed"] is False
        assert data["panel_authority"]["sic_ingestion_allowed"] is False
        assert data["panel_authority"]["aor_queue_allowed"] is False

        content_path = Path(data["content_path"])
        sidecar_path = Path(data["sidecar_path"])
        packet_path = Path(data["visual_capture_packet_path"])
        assert content_path.exists()
        assert sidecar_path.exists()
        assert packet_path.exists()
        assert content_path.resolve().is_relative_to((tmp_path / "03_INPUTS" / "00_QUARANTINE").resolve())

        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        vc_meta = sidecar["extra_metadata"]["visual_capture"]
        assert sidecar["source_platform"] == "visual-capture"
        assert sidecar["capture_method"] == "capture-to-markdown"
        assert sidecar["source_package_status"] == "not-ingested"
        assert sidecar["promotion_status"] == "quarantine"
        assert vc_meta["canonical_status"] == "not_promoted"
        assert vc_meta["aor_queue_status"] == "not_queued"
        assert vc_meta["authority"]["canonical_mutation_allowed"] is False
        assert vc_meta["authority"]["provider_call_allowed"] is False

    def test_secret_like_save_is_blocked_unless_redacted_save_allowed(self, tmp_path):
        api = _make_api(tmp_path)
        result = api.save_capture_to_markdown(
            _payload(text="api_key=test-key-abcdefghijklmnop1234")
        )

        assert result["ok"] is False
        assert result["surface"] == "capture_to_markdown_save"
        assert result["data"]["status"] == "blocked_secret_like"
        assert result["data"]["write_performed"] is False
        assert not (tmp_path / "03_INPUTS").exists()

    def test_recent_capture_listing_after_save(self, tmp_path):
        api = _make_api(tmp_path)
        api.save_capture_to_markdown(_payload(title="Recent Visual Capture", text="recent unique body"))
        result = api.get_capture_to_markdown_panel()

        assert result["ok"] is True
        recent = result["data"]["recent_captures"]
        assert len(recent) == 1
        assert recent[0]["title"] == "Recent Visual Capture"
        assert recent[0]["profile"] == "research_note"
        assert recent[0]["visual_capture_packet_path"].endswith(".visual_capture.json")

    def test_review_clickthrough_updates_sidecar_and_packet_only(self, tmp_path):
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Reviewable Capture", text="Unique review text remains unchanged.")
        )
        save_data = save_result["data"]
        content_path = Path(save_data["content_path"])
        sidecar_path = Path(save_data["sidecar_path"])
        packet_path = Path(save_data["visual_capture_packet_path"])
        original_content = content_path.read_text(encoding="utf-8")

        review_result = api.review_capture_to_markdown({
            "sidecar_path": str(sidecar_path),
            "decision": "reviewed",
            "review_note": "operator confirmed raw quarantine capture",
        })

        assert review_result["ok"] is True
        data = review_result["data"]
        assert data["status"] == "review_state_updated"
        assert data["old_status"] == "pending-review"
        assert data["new_status"] == "reviewed"
        assert data["content_write_performed"] is False
        assert data["sidecar_write_performed"] is True
        assert data["visual_capture_packet_json_write_performed"] is True
        assert data["panel_authority"]["canonical_mutation_allowed"] is False
        assert data["panel_authority"]["sic_ingestion_allowed"] is False
        assert data["panel_authority"]["aor_queue_allowed"] is False
        assert "canonical_knowledge_promotion" in data["blocked_downstream_actions"]
        assert content_path.read_text(encoding="utf-8") == original_content

        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        assert sidecar["quarantine_status"] == "reviewed"
        assert sidecar["extra_metadata"]["visual_capture"]["review_status"] == "reviewed"
        assert packet["routing"]["review_status"] == "reviewed"
        assert review_result["data"]["recent_captures"][0]["review_status"] == "reviewed"

    def test_source_pack_approval_preview_clickthrough_is_read_only(self, tmp_path):
        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Approval Preview Capture", text="Unique approval preview text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack approval preview",
        })

        before_files = _list_files(tmp_path)
        result = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })
        after_files = _list_files(tmp_path)

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_approval_preview"
        data = result["data"]
        assert data["action"] == "source_pack_approval_preview"
        assert data["status"] == "ready_for_operator_source_pack_write_approval_preview"
        assert data["write_performed"] is False
        assert data["approval_artifact_written"] is False
        assert data["source_pack_write_performed"] is False
        assert data["request_digest"]
        assert data["approval_preview"]["request_digest"] == data["request_digest"]
        assert data["approval_preview"]["write_scope_count"] > 0
        assert data["panel_authority"]["reviewed_capture_source_pack_approval_preview_ready"] is True
        assert data["panel_authority"]["reviewed_capture_source_pack_approval_artifact_write_allowed"] is False
        assert data["panel_authority"]["reviewed_capture_source_pack_write_allowed"] is True
        assert data["panel_authority"]["reviewed_capture_source_pack_write_requires_exact_approval"] is True
        assert data["authority"]["approval_artifact_write_allowed"] is False
        assert data["authority"]["source_pack_write_allowed"] is False
        assert before_files == after_files

    def test_source_pack_write_clickthrough_writes_only_approved_pack_artifacts(self, tmp_path):
        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack Write Capture", text="Unique approved source-pack text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack write",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]

        result = api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_write"
        data = result["data"]
        assert data["action"] == "source_pack_write"
        assert data["status"] == "source_pack_write_completed"
        assert data["source_pack_write_performed"] is True
        assert data["exact_once_marker_written"] is True
        assert data["approval_artifact_written"] is False
        assert data["panel_authority"]["reviewed_capture_source_pack_write_allowed"] is True
        assert data["authority"]["aor_dispatch_allowed"] is False
        assert data["authority"]["sic_ingestion_allowed"] is False
        assert data["authority"]["canonical_mutation_allowed"] is False
        assert data["authority"]["source_pack_overwrite_allowed"] is False
        for rel_path in data["written_paths"]:
            assert (tmp_path / rel_path).is_file()
            assert rel_path.startswith("runtime/acquisition/packs/")

    def test_source_pack_aor_dispatch_readiness_clickthrough_is_read_only_after_write(self, tmp_path):
        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack AOR Readiness Capture", text="Unique AOR readiness source-pack text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack AOR readiness",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        write_result = api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })["data"]
        before_files = _list_files(tmp_path)

        result = api.preview_capture_to_markdown_source_pack_aor_dispatch_readiness({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "reviewed_by": "studio-operator",
        })
        after_files = _list_files(tmp_path)

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_aor_dispatch_readiness"
        data = result["data"]
        assert data["action"] == "source_pack_aor_dispatch_readiness"
        assert data["status"] == "ready_for_source_pack_aor_dispatch_readiness_preview"
        assert data["read_only"] is True
        assert data["write_performed"] is False
        assert data["source_pack_exact_once_marker_verified"] is True
        assert data["source_pack_artifacts_verified"] is True
        assert data["source_pack_artifact_paths"] == write_result["written_paths"][1:]
        assert data["future_aor_dispatch_packet_preview_ready"] is True
        assert data["future_aor_dispatch_packet_preview"]["workflow_id"] == "source_pack_builder"
        assert data["future_aor_dispatch_packet_preview"]["dispatch_allowed_now"] is False
        assert data["panel_authority"]["reviewed_capture_source_pack_aor_dispatch_readiness_ready"] is True
        assert data["authority"]["aor_dispatch_allowed"] is False
        assert data["authority"]["agent_bus_task_write_allowed"] is False
        assert data["authority"]["aor_dry_run_allowed"] is False
        assert data["aor_audit_written"] is False
        assert data["osril_event_written"] is False
        assert before_files == after_files

    def test_source_pack_aor_dispatch_approval_design_clickthrough_is_read_only_after_readiness(self, tmp_path):
        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack AOR Approval Design Capture", text="Unique AOR approval design text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack AOR approval design",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })
        before_files = _list_files(tmp_path)

        result = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_design({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "reviewed_by": "studio-operator",
        })
        after_files = _list_files(tmp_path)

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_aor_dispatch_approval_design"
        data = result["data"]
        assert data["action"] == "source_pack_aor_dispatch_approval_design"
        assert data["status"] == "ready_for_source_pack_aor_dispatch_approval_design"
        assert data["read_only"] is True
        assert data["write_performed"] is False
        assert data["source_readiness_verified"] is True
        assert data["aor_dispatch_approval_design_ready"] is True
        assert data["future_aor_dispatch_approval_packet_preview_ready"] is True
        assert data["future_aor_dispatch_approval_packet_preview"]["approval_packet_id"].startswith(
            "vcmi-aor-dispatch-appr-"
        )
        assert data["future_aor_dispatch_approval_packet_preview"]["approval_request_written"] is False
        assert data["approval_artifact_written"] is False
        assert data["approval_request_written"] is False
        assert data["approval_consumed"] is False
        assert data["approval_decision_written"] is False
        assert data["panel_authority"]["reviewed_capture_source_pack_aor_dispatch_approval_design_ready"] is True
        assert data["authority"]["approval_artifact_write_allowed"] is False
        assert data["authority"]["approval_request_write_allowed"] is False
        assert data["authority"]["approval_consumption_allowed"] is False
        assert data["authority"]["aor_dispatch_allowed"] is False
        assert data["authority"]["agent_bus_task_write_allowed"] is False
        assert before_files == after_files

    def test_source_pack_aor_dispatch_approval_request_clickthrough_writes_pending_request_only(self, tmp_path):
        from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_design import (
            FUTURE_OPERATOR_APPROVAL_STATEMENT,
        )

        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack AOR Approval Request Capture", text="Unique AOR approval request text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack AOR approval request",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })
        design = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_design({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "reviewed_by": "studio-operator",
        })["data"]
        expected = design["future_aor_dispatch_approval_packet_preview"]["approval_request_digest"]
        before_files = set(_list_files(tmp_path))

        result = api.request_capture_to_markdown_source_pack_aor_dispatch_approval({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "operator_statement": FUTURE_OPERATOR_APPROVAL_STATEMENT,
            "write_approval_request": True,
            "reviewed_by": "studio-operator",
            "requested_by": "studio-operator",
        })
        after_files = set(_list_files(tmp_path))

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_aor_dispatch_approval_request"
        data = result["data"]
        assert data["action"] == "source_pack_aor_dispatch_approval_request"
        assert data["status"] == "source_pack_aor_dispatch_approval_request_written"
        assert data["write_performed"] is True
        assert data["approval_request_written"] is True
        assert data["approval_artifact_written"] is True
        assert data["approval_decision_written"] is False
        assert data["approval_consumed"] is False
        assert data["approval_exact_once_marker_written"] is False
        assert data["agent_bus_task_written"] is False
        assert data["aor_dispatch_allowed_now"] is False
        assert data["ready_for_aor_dispatch_approval_decision"] is True
        assert data["ready_for_aor_dispatch"] is False
        assert data["panel_authority"]["reviewed_capture_source_pack_aor_dispatch_approval_request_writer_ready"] is True
        assert data["authority"]["approval_request_written"] is True
        assert data["authority"]["approval_decision_write_allowed"] is False
        assert data["authority"]["approval_consumption_allowed"] is False
        assert data["authority"]["agent_bus_task_write_allowed"] is False
        assert data["authority"]["aor_dispatch_allowed"] is False
        assert after_files - before_files == {data["approval_artifact_path"]}
        artifact = json.loads((tmp_path / data["approval_artifact_path"]).read_text(encoding="utf-8"))
        assert artifact["status"] == "pending-operator-decision"
        assert artifact["approval_request_digest"] == expected

    def test_source_pack_aor_dispatch_approval_consumption_readiness_clickthrough_is_read_only(
        self,
        tmp_path,
    ):
        from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_design import (
            FUTURE_OPERATOR_APPROVAL_STATEMENT,
        )

        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack AOR Approval Decision Readiness", text="Unique decision readiness text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack AOR approval decision readiness",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })
        design = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_design({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "reviewed_by": "studio-operator",
        })["data"]
        expected = design["future_aor_dispatch_approval_packet_preview"]["approval_request_digest"]
        request = api.request_capture_to_markdown_source_pack_aor_dispatch_approval({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "operator_statement": FUTURE_OPERATOR_APPROVAL_STATEMENT,
            "write_approval_request": True,
            "reviewed_by": "studio-operator",
            "requested_by": "studio-operator",
        })["data"]
        before_files = _list_files(tmp_path)

        result = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "reviewed_by": "studio-operator",
        })
        after_files = _list_files(tmp_path)

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness"
        data = result["data"]
        assert data["action"] == "source_pack_aor_dispatch_approval_consumption_readiness"
        assert (
            data["status"]
            == "source_pack_aor_dispatch_approval_decision_consumption_readiness_ready_no_write"
        )
        assert data["read_only"] is True
        assert data["write_performed"] is False
        assert data["writes_performed"] is False
        assert data["approval_request_artifact_verified"] is True
        assert data["ready_for_aor_dispatch_approval_decision_writer"] is True
        assert data["ready_for_aor_dispatch_approval_consumption"] is False
        assert data["approval_decision_written"] is False
        assert data["approval_consumed"] is False
        assert data["approval_exact_once_marker_written"] is False
        assert data["agent_bus_task_written"] is False
        assert data["aor_dispatch_allowed_now"] is False
        assert data["panel_authority"]["reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ready"] is True
        assert data["authority"]["approval_decision_write_allowed"] is False
        assert data["authority"]["approval_consumption_allowed"] is False
        assert data["authority"]["approval_exact_once_marker_write_allowed"] is False
        assert data["authority"]["agent_bus_task_write_allowed"] is False
        assert data["authority"]["aor_dispatch_allowed"] is False
        assert len(data["future_approval_decision_options"]) == 2
        assert data["future_approval_consumption_contract"]["effect_now"] == "read_only_contract_preview"
        assert before_files == after_files

    def test_source_pack_aor_dispatch_approval_decision_clickthrough_writes_decision_only(
        self,
        tmp_path,
    ):
        from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_design import (
            FUTURE_OPERATOR_APPROVAL_STATEMENT,
        )

        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack AOR Approval Decision Writer", text="Unique approval decision text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack AOR approval decision writer",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })
        design = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_design({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "reviewed_by": "studio-operator",
        })["data"]
        expected = design["future_aor_dispatch_approval_packet_preview"]["approval_request_digest"]
        request = api.request_capture_to_markdown_source_pack_aor_dispatch_approval({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "operator_statement": FUTURE_OPERATOR_APPROVAL_STATEMENT,
            "write_approval_request": True,
            "reviewed_by": "studio-operator",
            "requested_by": "studio-operator",
        })["data"]
        readiness = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        decision_option = next(
            option for option in readiness["future_approval_decision_options"] if option["decision"] == "approved"
        )
        before_files = set(_list_files(tmp_path))

        result = api.write_capture_to_markdown_source_pack_aor_dispatch_approval_decision({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "decision": "approved",
            "expected_approval_decision_digest": decision_option["decision_preview_digest"],
            "operator_statement": decision_option["required_operator_statement"],
            "write_approval_decision": True,
            "reviewed_by": "studio-operator",
            "decided_by": "studio-operator",
        })
        after_files = set(_list_files(tmp_path))

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_aor_dispatch_approval_decision"
        data = result["data"]
        assert data["action"] == "source_pack_aor_dispatch_approval_decision"
        assert data["status"] == "source_pack_aor_dispatch_approval_decision_written"
        assert data["write_performed"] is True
        assert data["approval_decision_written"] is True
        assert data["approval_decision_artifact_written"] is True
        assert data["approval_consumed"] is False
        assert data["approval_exact_once_marker_written"] is False
        assert data["agent_bus_task_written"] is False
        assert data["aor_dispatch_allowed_now"] is False
        assert data["ready_for_aor_dispatch_approval_consumption"] is True
        assert data["ready_for_aor_dispatch"] is False
        assert data["panel_authority"]["reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ready"] is True
        assert data["authority"]["approval_decision_write_allowed"] is True
        assert data["authority"]["approval_consumption_allowed"] is False
        assert data["authority"]["approval_exact_once_marker_write_allowed"] is False
        assert data["authority"]["agent_bus_task_write_allowed"] is False
        assert data["authority"]["aor_dispatch_allowed"] is False
        assert after_files - before_files == {data["approval_decision_artifact_path"]}
        artifact = json.loads((tmp_path / data["approval_decision_artifact_path"]).read_text(encoding="utf-8"))
        assert artifact["artifact_type"] == "vcmi_source_pack_aor_dispatch_approval_decision"
        assert artifact["decision"] == "approved"
        assert artifact["approval_request_digest"] == expected
        assert artifact["source_approval_artifact_path"] == request["approval_artifact_path"]
        assert artifact["approval_consumed"] is False
        assert artifact["agent_bus_task_written"] is False
        assert artifact["dispatch_allowed_now"] is False

    def test_source_pack_aor_dispatch_approval_consumption_clickthrough_writes_marker_and_consumption_only(
        self,
        tmp_path,
    ):
        from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_design import (
            FUTURE_OPERATOR_APPROVAL_STATEMENT,
        )

        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack AOR Approval Consumption", text="Unique approval consumption text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack AOR approval consumption executor",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })
        design = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_design({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "reviewed_by": "studio-operator",
        })["data"]
        expected = design["future_aor_dispatch_approval_packet_preview"]["approval_request_digest"]
        request = api.request_capture_to_markdown_source_pack_aor_dispatch_approval({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "operator_statement": FUTURE_OPERATOR_APPROVAL_STATEMENT,
            "write_approval_request": True,
            "reviewed_by": "studio-operator",
            "requested_by": "studio-operator",
        })["data"]
        readiness = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        decision_option = next(
            option for option in readiness["future_approval_decision_options"] if option["decision"] == "approved"
        )
        decision = api.write_capture_to_markdown_source_pack_aor_dispatch_approval_decision({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "decision": "approved",
            "expected_approval_decision_digest": decision_option["decision_preview_digest"],
            "operator_statement": decision_option["required_operator_statement"],
            "write_approval_decision": True,
            "reviewed_by": "studio-operator",
            "decided_by": "studio-operator",
        })["data"]
        before_preview_files = set(_list_files(tmp_path))

        preview_consumption = api.consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "decision": "approved",
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "reviewed_by": "studio-operator",
            "consumed_by": "studio-operator",
        })["data"]
        assert set(_list_files(tmp_path)) == before_preview_files
        assert preview_consumption["status"] == "ready_for_source_pack_aor_dispatch_approval_consumption_preview"
        assert preview_consumption["write_performed"] is False
        assert preview_consumption["approval_consumption_digest"]
        assert preview_consumption["required_operator_statement"]

        result = api.consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "decision": "approved",
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "expected_approval_consumption_digest": preview_consumption["approval_consumption_digest"],
            "operator_statement": preview_consumption["required_operator_statement"],
            "write_consumption_marker": True,
            "write_approval_consumption": True,
            "reviewed_by": "studio-operator",
            "consumed_by": "studio-operator",
        })
        after_files = set(_list_files(tmp_path))

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_aor_dispatch_approval_consumption"
        data = result["data"]
        assert data["action"] == "source_pack_aor_dispatch_approval_consumption"
        assert data["status"] == "source_pack_aor_dispatch_approval_decision_consumed_agent_bus_ready"
        assert data["write_performed"] is True
        assert data["approval_consumed"] is True
        assert data["approval_decision_consumed"] is True
        assert data["approval_exact_once_marker_written"] is True
        assert data["approval_consumption_artifact_written"] is True
        assert data["ready_for_agent_bus_task_writer"] is True
        assert data["agent_bus_task_written"] is False
        assert data["aor_dispatch_allowed_now"] is False
        assert data["authority"]["approval_consumption_write_allowed"] is True
        assert data["authority"]["approval_exact_once_marker_written"] is True
        assert data["authority"]["agent_bus_task_write_allowed"] is False
        assert data["authority"]["aor_dispatch_allowed"] is False
        assert after_files - before_preview_files == {
            data["approval_consumption_marker_path"],
            data["approval_consumption_artifact_path"],
        }
        marker = json.loads((tmp_path / data["approval_consumption_marker_path"]).read_text(encoding="utf-8"))
        artifact = json.loads((tmp_path / data["approval_consumption_artifact_path"]).read_text(encoding="utf-8"))
        assert marker["record_type"] == "vcmi_source_pack_aor_dispatch_approval_consumption_marker"
        assert marker["approval_consumed"] is False
        assert marker["approval_consumption_artifact_written"] is False
        assert marker["agent_bus_task_written"] is False
        assert marker["aor_dispatch_performed"] is False
        assert artifact["record_type"] == "vcmi_source_pack_aor_dispatch_approval_consumption"
        assert artifact["approval_consumed"] is True
        assert artifact["approval_decision_consumed"] is True
        assert artifact["ready_for_agent_bus_task_writer"] is True
        assert artifact["agent_bus_task_written"] is False
        assert artifact["dispatch_allowed_now"] is False

    def test_source_pack_aor_dispatch_agent_bus_task_clickthrough_writes_open_task_only(
        self,
        tmp_path,
    ):
        from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_design import (
            FUTURE_OPERATOR_APPROVAL_STATEMENT,
        )
        from runtime.agent_bus.bus import list_events, list_tasks

        _seed_downstream_contracts(tmp_path)
        api = _make_api(tmp_path)
        save_result = api.save_capture_to_markdown(
            _payload(title="Source Pack AOR Agent Bus Task", text="Unique agent bus task text.")
        )
        save_data = save_result["data"]
        api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "operator confirmed for source-pack AOR agent bus task writer",
        })
        preview = api.preview_capture_to_markdown_source_pack_approval({
            "sidecar_path": save_data["sidecar_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        api.execute_capture_to_markdown_source_pack_write({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "operator_statement": preview["required_operator_statement"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })
        design = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_design({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "reviewed_by": "studio-operator",
        })["data"]
        expected = design["future_aor_dispatch_approval_packet_preview"]["approval_request_digest"]
        request = api.request_capture_to_markdown_source_pack_aor_dispatch_approval({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "operator_statement": FUTURE_OPERATOR_APPROVAL_STATEMENT,
            "write_approval_request": True,
            "reviewed_by": "studio-operator",
            "requested_by": "studio-operator",
        })["data"]
        readiness = api.preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "reviewed_by": "studio-operator",
        })["data"]
        decision_option = next(
            option for option in readiness["future_approval_decision_options"] if option["decision"] == "approved"
        )
        decision = api.write_capture_to_markdown_source_pack_aor_dispatch_approval_decision({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "decision": "approved",
            "expected_approval_decision_digest": decision_option["decision_preview_digest"],
            "operator_statement": decision_option["required_operator_statement"],
            "write_approval_decision": True,
            "reviewed_by": "studio-operator",
            "decided_by": "studio-operator",
        })["data"]
        consumption_preview = api.consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "decision": "approved",
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "reviewed_by": "studio-operator",
            "consumed_by": "studio-operator",
        })["data"]
        consumption = api.consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "decision": "approved",
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "expected_approval_consumption_digest": consumption_preview["approval_consumption_digest"],
            "operator_statement": consumption_preview["required_operator_statement"],
            "write_consumption_marker": True,
            "write_approval_consumption": True,
            "reviewed_by": "studio-operator",
            "consumed_by": "studio-operator",
        })["data"]
        before_preview_files = set(_list_files(tmp_path))

        task_preview = api.write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
            "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })["data"]
        assert set(_list_files(tmp_path)) == before_preview_files
        assert task_preview["status"] == "ready_for_source_pack_aor_dispatch_agent_bus_task_preview"
        assert task_preview["agent_bus_task_digest"]
        assert task_preview["required_operator_statement"]
        assert task_preview["agent_bus_task_written"] is False
        assert task_preview["agent_bus_task_claimed"] is False
        assert task_preview["aor_dispatch_allowed_now"] is False

        result = api.write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
            "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
            "expected_agent_bus_task_digest": task_preview["agent_bus_task_digest"],
            "operator_statement": task_preview["required_operator_statement"],
            "write_task_marker": True,
            "write_agent_bus_task": True,
            "reviewed_by": "studio-operator",
            "written_by": "studio-operator",
        })

        assert result["ok"] is True
        assert result["surface"] == "capture_to_markdown_source_pack_aor_dispatch_agent_bus_task"
        data = result["data"]
        assert data["action"] == "source_pack_aor_dispatch_agent_bus_task"
        assert data["status"] == "source_pack_aor_dispatch_agent_bus_task_written_unclaimed_aor_blocked"
        assert data["agent_bus_exact_once_marker_written"] is True
        assert data["agent_bus_task_written"] is True
        assert data["agent_bus_task_artifact_written"] is True
        assert data["agent_bus_task_claimed"] is False
        assert data["runtime_process_started"] is False
        assert data["aor_dispatch_allowed_now"] is False
        assert data["authority"]["agent_bus_task_write_allowed"] is True
        assert data["authority"]["agent_bus_task_claim_allowed"] is False
        assert data["authority"]["aor_dispatch_allowed"] is False
        after_files = set(_list_files(tmp_path))
        new_files = after_files - before_preview_files
        assert data["agent_bus_task_marker_path"] in new_files
        assert data["agent_bus_task_artifact_path"] in new_files
        assert "runtime/agent_bus/agent_bus.sqlite" in new_files
        tasks = [task for task in list_tasks(tmp_path, recipient="OpenClaw") if task["task_id"] == data["agent_bus_task_id"]]
        assert len(tasks) == 1
        assert tasks[0]["status"] == "open"
        marker = json.loads((tmp_path / data["agent_bus_task_marker_path"]).read_text(encoding="utf-8"))
        artifact = json.loads((tmp_path / data["agent_bus_task_artifact_path"]).read_text(encoding="utf-8"))
        assert marker["record_type"] == "vcmi_source_pack_aor_dispatch_agent_bus_task_marker"
        assert marker["agent_bus_task_written"] is False
        assert marker["agent_bus_task_claimed"] is False
        assert artifact["record_type"] == "vcmi_source_pack_aor_dispatch_agent_bus_task"
        assert artifact["agent_bus_task_written"] is True
        assert artifact["agent_bus_task_claimed"] is False
        assert artifact["aor_dispatch_performed"] is False

        claim_readiness = api.preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
            "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
            "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
            "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
            "agent_bus_task_id": data["agent_bus_task_id"],
            "runtime": "OpenClaw",
            "reviewed_by": "studio-operator",
        })

        assert claim_readiness["ok"] is True
        assert claim_readiness["surface"] == "capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness"
        claim_data = claim_readiness["data"]
        assert claim_data["action"] == "source_pack_aor_dispatch_agent_bus_task_claim_readiness"
        assert claim_data["agent_bus_task_artifact_verified"] is True
        assert claim_data["agent_bus_task_claimable"] is True
        assert claim_data["agent_bus_task_claim_preflight_ready"] is True
        assert claim_data["agent_bus_task_claim_allowed_now"] is False
        assert claim_data["agent_bus_task_claimed"] is False
        assert claim_data["agent_bus_route_configured_for_runtime"] is True
        assert claim_data["runtime_liveness_ready"] is False
        assert claim_data["runtime_process_started"] is False
        assert claim_data["aor_dispatch_allowed_now"] is False
        tasks_after_claim_readiness = [
            task for task in list_tasks(tmp_path, recipient="OpenClaw") if task["task_id"] == data["agent_bus_task_id"]
        ]
        assert len(tasks_after_claim_readiness) == 1
        assert tasks_after_claim_readiness[0]["status"] == "open"
        assert tasks_after_claim_readiness[0]["owner"] is None

        claim_preview = api.claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
            "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
            "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
            "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
            "agent_bus_task_id": data["agent_bus_task_id"],
            "runtime": "OpenClaw",
            "reviewed_by": "studio-operator",
        })
        assert claim_preview["ok"] is True
        assert claim_preview["surface"] == "capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim"
        claim_preview_data = claim_preview["data"]
        assert claim_preview_data["action"] == "source_pack_aor_dispatch_agent_bus_task_claim"
        assert claim_preview_data["agent_bus_task_claim_preview_ready"] is True
        assert claim_preview_data["agent_bus_task_claim_digest"]
        assert claim_preview_data["agent_bus_task_claimed"] is False

        claim = api.claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
            "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
            "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
            "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
            "agent_bus_task_id": data["agent_bus_task_id"],
            "expected_agent_bus_task_claim_digest": claim_preview_data["agent_bus_task_claim_digest"],
            "operator_statement": claim_preview_data["required_operator_statement"],
            "runtime": "OpenClaw",
            "reviewed_by": "studio-operator",
            "claimed_by": "studio-operator",
            "write_claim_marker": True,
            "claim_agent_bus_task": True,
            "write_claim_artifact": True,
        })
        assert claim["ok"] is True
        assert claim["surface"] == "capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim"
        claim_result = claim["data"]
        assert claim_result["status"] == "source_pack_aor_dispatch_agent_bus_task_claimed_execution_blocked"
        assert claim_result["agent_bus_task_claim_marker_written"] is True
        assert claim_result["agent_bus_task_claimed"] is True
        assert claim_result["agent_bus_task_claim_artifact_written"] is True
        assert claim_result["agent_bus_task_executed"] is False
        assert claim_result["runtime_process_started"] is False
        assert claim_result["aor_dispatch_allowed_now"] is False
        tasks_after_claim = [
            task for task in list_tasks(tmp_path, recipient="OpenClaw") if task["task_id"] == data["agent_bus_task_id"]
        ]
        assert len(tasks_after_claim) == 1
        assert tasks_after_claim[0]["status"] == "claimed"
        assert tasks_after_claim[0]["owner"] == "OpenClaw"

        dry_run_readiness = (
            api.preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness(
                {
                    "sidecar_path": save_data["sidecar_path"],
                    "request_digest": preview["request_digest"],
                    "expected_approval_request_digest": expected,
                    "approval_artifact_path": request["approval_artifact_path"],
                    "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
                    "expected_approval_decision_digest": decision["approval_decision_digest"],
                    "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
                    "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
                    "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
                    "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
                    "agent_bus_task_id": data["agent_bus_task_id"],
                    "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
                    "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
                    "runtime": "OpenClaw",
                    "reviewed_by": "studio-operator",
                }
            )
        )
        assert dry_run_readiness["ok"] is True
        assert (
            dry_run_readiness["surface"]
            == "capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness"
        )
        dry_run_data = dry_run_readiness["data"]
        assert dry_run_data["action"] == "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness"
        assert dry_run_data["agent_bus_task_claimed"] is True
        assert dry_run_data["aor_contracts_verified"] is True
        assert dry_run_data["future_aor_dry_run_packet_ready"] is True
        assert dry_run_data["aor_dry_run_allowed_now"] is False
        assert dry_run_data["aor_dry_run_performed"] is False

        dry_run_preview = api.execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
            "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
            "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
            "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
            "agent_bus_task_id": data["agent_bus_task_id"],
            "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
            "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
            "runtime": "OpenClaw",
            "reviewed_by": "studio-operator",
            "executed_by": "studio-operator",
        })["data"]
        assert dry_run_preview["aor_dry_run_executor_preview_ready"] is True
        assert dry_run_preview["aor_dry_run_packet_digest"]

        dry_run = api.execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run({
            "sidecar_path": save_data["sidecar_path"],
            "request_digest": preview["request_digest"],
            "expected_approval_request_digest": expected,
            "approval_artifact_path": request["approval_artifact_path"],
            "approval_decision_artifact_path": decision["approval_decision_artifact_path"],
            "expected_approval_decision_digest": decision["approval_decision_digest"],
            "approval_consumption_artifact_path": consumption["approval_consumption_artifact_path"],
            "expected_approval_consumption_digest": consumption["approval_consumption_digest"],
            "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
            "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
            "agent_bus_task_id": data["agent_bus_task_id"],
            "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
            "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
            "expected_aor_dry_run_packet_digest": dry_run_preview["aor_dry_run_packet_digest"],
            "operator_statement": dry_run_preview["required_operator_statement"],
            "runtime": "OpenClaw",
            "reviewed_by": "studio-operator",
            "executed_by": "studio-operator",
            "write_aor_dry_run_marker": True,
            "run_aor_dry_run": True,
            "write_aor_dry_run_artifact": True,
        })["data"]
        assert dry_run["ok"] is True, dry_run["blockers"]
        assert dry_run["status"] == "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executed"
        assert dry_run["aor_dry_run_marker_written"] is True
        assert dry_run["aor_dry_run_artifact_written"] is True
        assert dry_run["agent_bus_task_executed"] is False
        assert dry_run["agent_bus_task_status_updated"] is False

        status_preview = (
            api.execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle(
                {
                    "sidecar_path": save_data["sidecar_path"],
                    "request_digest": preview["request_digest"],
                    "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
                    "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
                    "agent_bus_task_id": data["agent_bus_task_id"],
                    "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
                    "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
                    "aor_dry_run_artifact_path": dry_run["aor_dry_run_artifact_path"],
                    "expected_aor_dry_run_artifact_digest": dry_run["aor_dry_run_artifact"]["artifact_digest"],
                    "runtime": "OpenClaw",
                    "reviewed_by": "studio-operator",
                    "executed_by": "studio-operator",
                }
            )["data"]
        )
        assert status_preview["status_lifecycle_preview_ready"] is True
        assert status_preview["agent_bus_task_status_before"] == "claimed"
        assert status_preview["required_operator_statement"].startswith("I update VCMI Agent Bus task")

        before_status_events = list_events(tmp_path, data["agent_bus_task_id"])
        status_result = (
            api.execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle(
                {
                    "sidecar_path": save_data["sidecar_path"],
                    "request_digest": preview["request_digest"],
                    "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
                    "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
                    "agent_bus_task_id": data["agent_bus_task_id"],
                    "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
                    "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
                    "aor_dry_run_artifact_path": dry_run["aor_dry_run_artifact_path"],
                    "expected_aor_dry_run_artifact_digest": dry_run["aor_dry_run_artifact"]["artifact_digest"],
                    "operator_statement": status_preview["required_operator_statement"],
                    "runtime": "OpenClaw",
                    "reviewed_by": "studio-operator",
                    "executed_by": "studio-operator",
                    "write_status_lifecycle_marker": True,
                    "update_agent_bus_task_status": True,
                    "write_status_lifecycle_artifact": True,
                }
            )["data"]
        )
        assert status_result["status"] == "source_pack_aor_dispatch_agent_bus_claimed_task_status_lifecycle_review_requested"
        assert status_result["status_lifecycle_marker_written"] is True
        assert status_result["agent_bus_task_status_updated"] is True
        assert status_result["agent_bus_task_status_after"] == "review"
        assert status_result["agent_bus_task_review_requested"] is True
        assert status_result["status_lifecycle_artifact_written"] is True
        assert status_result["agent_bus_task_executed"] is False
        assert status_result["runtime_process_started"] is False
        assert status_result["aor_dispatch_performed"] is False
        for rel_path in status_result["written_paths"]:
            assert (tmp_path / rel_path).is_file()
        tasks_after_status_lifecycle = [
            task for task in list_tasks(tmp_path, recipient="OpenClaw") if task["task_id"] == data["agent_bus_task_id"]
        ]
        assert len(tasks_after_status_lifecycle) == 1
        assert tasks_after_status_lifecycle[0]["status"] == "review"
        assert tasks_after_status_lifecycle[0]["owner"] == "OpenClaw"
        after_status_events = list_events(tmp_path, data["agent_bus_task_id"])
        assert len(after_status_events) == len(before_status_events) + 1
        assert after_status_events[-1]["event_type"] == "review_requested"

        full_dispatch_readiness = (
            api.preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness(
                {
                    "sidecar_path": save_data["sidecar_path"],
                    "request_digest": preview["request_digest"],
                    "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
                    "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
                    "agent_bus_task_id": data["agent_bus_task_id"],
                    "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
                    "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
                    "aor_dry_run_artifact_path": dry_run["aor_dry_run_artifact_path"],
                    "expected_aor_dry_run_artifact_digest": dry_run["aor_dry_run_artifact"]["artifact_digest"],
                    "status_lifecycle_artifact_path": status_result["status_lifecycle_artifact_path"],
                    "expected_status_lifecycle_artifact_digest": status_result["status_lifecycle_artifact"]["artifact_digest"],
                    "runtime": "OpenClaw",
                    "reviewed_by": "studio-operator",
                }
            )
        )
        assert full_dispatch_readiness["ok"] is True
        assert (
            full_dispatch_readiness["surface"]
            == "capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness"
        )
        full_dispatch_data = full_dispatch_readiness["data"]
        assert full_dispatch_data["action"] == "source_pack_aor_dispatch_agent_bus_full_dispatch_readiness"
        assert full_dispatch_data["status"] == "source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ready"
        assert full_dispatch_data["agent_bus_task_status"] == "review"
        assert full_dispatch_data["review_requested_event_verified"] is True
        assert full_dispatch_data["ready_for_full_dispatch_executor"] is True
        assert full_dispatch_data["future_full_dispatch_packet_ready"] is True
        assert full_dispatch_data["future_full_dispatch_packet_digest"]
        assert full_dispatch_data["aor_full_dispatch_allowed_now"] is False
        assert full_dispatch_data["aor_full_dispatch_performed"] is False
        assert full_dispatch_data["agent_bus_task_body_executed"] is False
        assert full_dispatch_data["runtime_process_started"] is False
        assert full_dispatch_data["sic_ingestion_performed"] is False
        assert full_dispatch_data["canonical_mutation_performed"] is False
        assert full_dispatch_data["graph_index_mutation_performed"] is False

        full_dispatch_preview = (
            api.execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch(
                {
                    "sidecar_path": save_data["sidecar_path"],
                    "request_digest": preview["request_digest"],
                    "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
                    "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
                    "agent_bus_task_id": data["agent_bus_task_id"],
                    "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
                    "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
                    "aor_dry_run_artifact_path": dry_run["aor_dry_run_artifact_path"],
                    "expected_aor_dry_run_artifact_digest": dry_run["aor_dry_run_artifact"]["artifact_digest"],
                    "status_lifecycle_artifact_path": status_result["status_lifecycle_artifact_path"],
                    "expected_status_lifecycle_artifact_digest": status_result["status_lifecycle_artifact"]["artifact_digest"],
                    "runtime": "OpenClaw",
                    "reviewed_by": "studio-operator",
                    "executed_by": "studio-operator",
                }
            )
        )
        assert full_dispatch_preview["ok"] is True
        assert (
            full_dispatch_preview["surface"]
            == "capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch"
        )
        full_dispatch_preview_data = full_dispatch_preview["data"]
        assert full_dispatch_preview_data["action"] == "source_pack_aor_dispatch_agent_bus_full_dispatch"
        assert full_dispatch_preview_data["status"] == "source_pack_aor_dispatch_agent_bus_full_dispatch_executor_preview_ready"
        assert full_dispatch_preview_data["full_dispatch_executor_preview_ready"] is True
        assert full_dispatch_preview_data["full_dispatch_packet_digest"] == full_dispatch_data["future_full_dispatch_packet_digest"]
        assert full_dispatch_preview_data["required_operator_statement"].startswith("I execute VCMI AOR full-dispatch")
        assert full_dispatch_preview_data["aor_full_dispatch_performed"] is False
        assert full_dispatch_preview_data["source_pack_writeback_created"] is False

        before_full_dispatch_task = [
            task for task in list_tasks(tmp_path, recipient="OpenClaw") if task["task_id"] == data["agent_bus_task_id"]
        ][0]
        full_dispatch_execution = (
            api.execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch(
                {
                    "sidecar_path": save_data["sidecar_path"],
                    "request_digest": preview["request_digest"],
                    "agent_bus_task_artifact_path": data["agent_bus_task_artifact_path"],
                    "expected_agent_bus_task_digest": data["agent_bus_task_digest"],
                    "agent_bus_task_id": data["agent_bus_task_id"],
                    "agent_bus_task_claim_artifact_path": claim_result["agent_bus_task_claim_artifact_path"],
                    "expected_agent_bus_task_claim_digest": claim_result["agent_bus_task_claim_digest"],
                    "aor_dry_run_artifact_path": dry_run["aor_dry_run_artifact_path"],
                    "expected_aor_dry_run_artifact_digest": dry_run["aor_dry_run_artifact"]["artifact_digest"],
                    "status_lifecycle_artifact_path": status_result["status_lifecycle_artifact_path"],
                    "expected_status_lifecycle_artifact_digest": status_result["status_lifecycle_artifact"]["artifact_digest"],
                    "expected_full_dispatch_packet_digest": full_dispatch_preview_data["full_dispatch_packet_digest"],
                    "operator_statement": full_dispatch_preview_data["required_operator_statement"],
                    "runtime": "OpenClaw",
                    "reviewed_by": "studio-operator",
                    "executed_by": "studio-operator",
                    "write_full_dispatch_marker": True,
                    "run_full_dispatch": True,
                    "write_full_dispatch_artifact": True,
                }
            )
        )
        assert full_dispatch_execution["ok"] is True
        full_dispatch_execution_data = full_dispatch_execution["data"]
        assert full_dispatch_execution_data["status"] == "source_pack_aor_dispatch_agent_bus_full_dispatch_executed"
        assert full_dispatch_execution_data["aor_result_status"] == "success"
        assert full_dispatch_execution_data["aor_full_dispatch_marker_written"] is True
        assert full_dispatch_execution_data["aor_full_dispatch_performed"] is True
        assert full_dispatch_execution_data["aor_full_dispatch_artifact_written"] is True
        assert full_dispatch_execution_data["source_pack_writeback_created"] is True
        assert full_dispatch_execution_data["sic_ingestion_performed"] is False
        assert full_dispatch_execution_data["canonical_mutation_performed"] is False
        assert full_dispatch_execution_data["graph_index_mutation_performed"] is False
        assert full_dispatch_execution_data["provider_call_performed"] is False
        assert full_dispatch_execution_data["external_send_performed"] is False
        assert full_dispatch_execution_data["attachment_delete_performed"] is False
        after_full_dispatch_task = [
            task for task in list_tasks(tmp_path, recipient="OpenClaw") if task["task_id"] == data["agent_bus_task_id"]
        ][0]
        assert after_full_dispatch_task == before_full_dispatch_task

        sic_readiness = api.preview_capture_to_markdown_source_pack_sic_ingestion_readiness(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
            }
        )
        assert sic_readiness["ok"] is True
        assert sic_readiness["surface"] == "capture_to_markdown_source_pack_sic_ingestion_readiness"
        sic_data = sic_readiness["data"]
        assert sic_data["action"] == "source_pack_sic_ingestion_readiness"
        assert sic_data["status"] == "source_pack_sic_ingestion_readiness_ready"
        assert sic_data["full_dispatch_artifact_verified"] is True
        assert sic_data["source_pack_writeback_verified"] is True
        assert sic_data["sic_contracts_verified"] is True
        assert sic_data["future_sic_ingestion_packet_preview_ready"] is True
        assert sic_data["ready_for_sic_ingestion_approval_design"] is True
        assert sic_data["ready_for_sic_ingestion_executor"] is False
        assert sic_data["sic_ingestion_allowed_now"] is False
        assert sic_data["sic_ingestion_performed"] is False
        assert sic_data["sic_source_package_written"] is False
        assert sic_data["graph_index_mutation_performed"] is False
        assert sic_data["canonical_mutation_performed"] is False

        sic_approval_design = api.preview_capture_to_markdown_source_pack_sic_ingestion_approval_design(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
            }
        )
        assert sic_approval_design["ok"] is True
        sic_approval_design_data = sic_approval_design["data"]
        assert sic_approval_design_data["action"] == "source_pack_sic_ingestion_approval_design"
        assert sic_approval_design_data["source_intelligence_core_ingestion_approval_design_ready"] is True
        assert sic_approval_design_data["approval_request_written"] is False
        assert sic_approval_design_data["source_intelligence_core_ingestion_performed"] is False
        approval_packet = sic_approval_design_data[
            "future_source_intelligence_core_ingestion_approval_packet_preview"
        ]
        approval_request = api.preview_capture_to_markdown_source_pack_sic_ingestion_approval_request(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "expected_sic_ingestion_approval_request_digest": approval_packet["approval_request_digest"],
                "operator_statement": sic_approval_design_data["approval_design"]["future_operator_statement_required"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
                "requested_by": "studio-operator",
                "write_approval_request": True,
            }
        )
        assert approval_request["ok"] is True
        approval_request_data = approval_request["data"]
        assert approval_request_data["action"] == "source_pack_sic_ingestion_approval_request"
        assert approval_request_data["approval_request_written"] is True
        assert approval_request_data["approval_artifact_written"] is True
        assert approval_request_data["approval_decision_written"] is False
        assert approval_request_data["approval_consumed"] is False
        assert approval_request_data["source_intelligence_core_ingestion_performed"] is False
        assert approval_request_data["source_intelligence_core_source_package_written"] is False
        assert approval_request_data["graph_index_mutation_performed"] is False
        assert approval_request_data["canonical_mutation_performed"] is False
        assert (tmp_path / approval_request_data["approval_artifact_path"]).is_file()
        decision_readiness = api.preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision_consumption_readiness(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "expected_sic_ingestion_approval_request_digest": approval_request_data["approval_request_digest"],
                "approval_artifact_path": approval_request_data["approval_artifact_path"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
            }
        )
        assert decision_readiness["ok"] is True
        decision_readiness_data = decision_readiness["data"]
        assert (
            decision_readiness_data["action"]
            == "source_pack_sic_ingestion_approval_decision_consumption_readiness"
        )
        assert decision_readiness_data["approval_request_artifact_verified"] is True
        assert decision_readiness_data["ready_for_source_intelligence_core_approval_decision_writer"] is True
        assert decision_readiness_data["approval_decision_written"] is False
        assert decision_readiness_data["approval_consumed"] is False
        assert decision_readiness_data["source_intelligence_core_ingestion_allowed_now"] is False
        assert decision_readiness_data["source_intelligence_core_ingestion_performed"] is False
        assert decision_readiness_data["source_intelligence_core_source_package_written"] is False
        assert decision_readiness_data["graph_index_mutation_performed"] is False
        assert decision_readiness_data["canonical_mutation_performed"] is False
        approval_decision_option = decision_readiness_data["future_approval_decision_options"][0]
        approval_decision = api.preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "expected_sic_ingestion_approval_request_digest": approval_request_data["approval_request_digest"],
                "approval_artifact_path": approval_request_data["approval_artifact_path"],
                "decision": approval_decision_option["decision"],
                "expected_sic_ingestion_approval_decision_digest": approval_decision_option["decision_preview_digest"],
                "operator_statement": approval_decision_option["required_operator_statement"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
                "decided_by": "studio-operator",
                "write_approval_decision": True,
            }
        )
        assert approval_decision["ok"] is True
        approval_decision_data = approval_decision["data"]
        assert approval_decision_data["action"] == "source_pack_sic_ingestion_approval_decision"
        assert approval_decision_data["approval_decision_written"] is True
        assert approval_decision_data["approval_consumed"] is False
        assert approval_decision_data["ready_for_source_intelligence_core_approval_consumption"] is True
        assert approval_decision_data["ready_for_source_intelligence_core_ingestion_executor"] is False
        assert approval_decision_data["source_intelligence_core_ingestion_performed"] is False
        assert approval_decision_data["source_intelligence_core_source_package_written"] is False
        assert approval_decision_data["graph_index_mutation_performed"] is False
        assert approval_decision_data["canonical_mutation_performed"] is False
        assert (tmp_path / approval_decision_data["approval_decision_artifact_path"]).is_file()
        approval_consumption_preview = api.consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "expected_sic_ingestion_approval_request_digest": approval_request_data["approval_request_digest"],
                "approval_artifact_path": approval_request_data["approval_artifact_path"],
                "decision": approval_decision_data["decision"],
                "approval_decision_artifact_path": approval_decision_data["approval_decision_artifact_path"],
                "expected_sic_ingestion_approval_decision_digest": approval_decision_data["approval_decision_digest"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
                "consumed_by": "studio-operator",
            }
        )
        assert approval_consumption_preview["ok"] is True
        approval_consumption_preview_data = approval_consumption_preview["data"]
        assert approval_consumption_preview_data["action"] == "source_pack_sic_ingestion_approval_consumption"
        assert approval_consumption_preview_data["approval_consumption_preview_ready"] is True
        assert approval_consumption_preview_data["approval_consumed"] is False
        assert approval_consumption_preview_data["approval_exact_once_marker_written"] is False
        assert approval_consumption_preview_data["source_intelligence_core_ingestion_performed"] is False
        approval_consumption = api.consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "expected_sic_ingestion_approval_request_digest": approval_request_data["approval_request_digest"],
                "approval_artifact_path": approval_request_data["approval_artifact_path"],
                "decision": approval_decision_data["decision"],
                "approval_decision_artifact_path": approval_decision_data["approval_decision_artifact_path"],
                "expected_sic_ingestion_approval_decision_digest": approval_decision_data["approval_decision_digest"],
                "expected_sic_ingestion_approval_consumption_digest": approval_consumption_preview_data["approval_consumption_digest"],
                "operator_statement": approval_consumption_preview_data["required_operator_statement"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
                "consumed_by": "studio-operator",
                "write_consumption_marker": True,
                "write_approval_consumption": True,
            }
        )
        assert approval_consumption["ok"] is True
        approval_consumption_data = approval_consumption["data"]
        assert approval_consumption_data["approval_consumed"] is True
        assert approval_consumption_data["approval_decision_consumed"] is True
        assert approval_consumption_data["approval_exact_once_marker_written"] is True
        assert approval_consumption_data["approval_consumption_artifact_written"] is True
        assert approval_consumption_data["ready_for_source_intelligence_core_ingestion_executor"] is True
        assert approval_consumption_data["source_intelligence_core_ingestion_allowed_now"] is False
        assert approval_consumption_data["source_intelligence_core_ingestion_performed"] is False
        assert approval_consumption_data["source_intelligence_core_source_package_written"] is False
        assert approval_consumption_data["graph_index_mutation_performed"] is False
        assert approval_consumption_data["canonical_mutation_performed"] is False
        for path in approval_consumption_data["written_paths"]:
            assert (tmp_path / path).is_file()
        ingestion_preview = api.ingest_capture_to_markdown_source_pack_sic_ingestion(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "expected_sic_ingestion_approval_request_digest": approval_request_data["approval_request_digest"],
                "approval_artifact_path": approval_request_data["approval_artifact_path"],
                "decision": approval_decision_data["decision"],
                "approval_decision_artifact_path": approval_decision_data["approval_decision_artifact_path"],
                "expected_sic_ingestion_approval_decision_digest": approval_decision_data["approval_decision_digest"],
                "approval_consumption_artifact_path": approval_consumption_data["approval_consumption_artifact_path"],
                "expected_sic_ingestion_approval_consumption_digest": approval_consumption_data["approval_consumption_digest"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
                "ingested_by": "studio-operator",
            }
        )
        assert ingestion_preview["ok"] is True
        ingestion_preview_data = ingestion_preview["data"]
        assert ingestion_preview_data["action"] == "source_pack_sic_ingestion"
        assert ingestion_preview_data["source_intelligence_core_ingestion_preview_ready"] is True
        assert ingestion_preview_data["source_intelligence_core_ingestion_performed"] is False
        assert ingestion_preview_data["source_intelligence_core_source_package_written"] is False
        assert ingestion_preview_data["graph_index_mutation_performed"] is False
        assert ingestion_preview_data["canonical_mutation_performed"] is False
        ingestion = api.ingest_capture_to_markdown_source_pack_sic_ingestion(
            {
                "sidecar_path": save_data["sidecar_path"],
                "request_digest": preview["request_digest"],
                "full_dispatch_artifact_path": full_dispatch_execution_data["full_dispatch_artifact_path"],
                "expected_full_dispatch_artifact_digest": full_dispatch_execution_data["aor_full_dispatch_artifact"]["artifact_digest"],
                "expected_full_dispatch_packet_digest": full_dispatch_execution_data["full_dispatch_packet_digest"],
                "expected_sic_ingestion_readiness_packet_digest": sic_data["future_sic_ingestion_packet_digest"],
                "expected_sic_ingestion_approval_request_digest": approval_request_data["approval_request_digest"],
                "approval_artifact_path": approval_request_data["approval_artifact_path"],
                "decision": approval_decision_data["decision"],
                "approval_decision_artifact_path": approval_decision_data["approval_decision_artifact_path"],
                "expected_sic_ingestion_approval_decision_digest": approval_decision_data["approval_decision_digest"],
                "approval_consumption_artifact_path": approval_consumption_data["approval_consumption_artifact_path"],
                "expected_sic_ingestion_approval_consumption_digest": approval_consumption_data["approval_consumption_digest"],
                "expected_sic_ingestion_digest": ingestion_preview_data["source_intelligence_core_ingestion_digest"],
                "operator_statement": ingestion_preview_data["required_operator_statement"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "reviewed_by": "studio-operator",
                "ingested_by": "studio-operator",
                "write_ingestion_marker": True,
                "run_source_intelligence_core_ingestion": True,
                "write_ingestion_artifact": True,
            }
        )
        assert ingestion["ok"] is True
        ingestion_data = ingestion["data"]
        assert ingestion_data["source_intelligence_core_ingestion_performed"] is True
        assert ingestion_data["source_intelligence_core_workspace_written"] is True
        assert ingestion_data["source_intelligence_core_source_package_written"] is True
        assert ingestion_data["source_intelligence_core_workspace_membership_written"] is True
        assert ingestion_data["graph_index_mutation_performed"] is False
        assert ingestion_data["canonical_mutation_performed"] is False
        for path in ingestion_data["written_paths"]:
            assert (tmp_path / path).is_file()

        graph_readiness = api.preview_capture_to_markdown_source_pack_sic_graph_indexing_readiness(
            {
                "source_intelligence_core_ingestion_artifact_path": ingestion_data[
                    "source_intelligence_core_ingestion_artifact_path"
                ],
                "expected_sic_ingestion_artifact_digest": ingestion_data[
                    "source_intelligence_core_ingestion_artifact"
                ]["artifact_digest"],
                "expected_sic_ingestion_digest": ingestion_data[
                    "source_intelligence_core_ingestion_digest"
                ],
                "target_workspace_id": "vcmi-reviewed-captures",
            }
        )
        assert graph_readiness["ok"] is True
        assert (
            graph_readiness["surface"]
            == "capture_to_markdown_source_pack_sic_graph_indexing_readiness"
        )
        graph_readiness_data = graph_readiness["data"]
        assert graph_readiness_data["action"] == "source_pack_sic_graph_indexing_readiness"
        assert graph_readiness_data["graph_indexing_readiness_preview_ready"] is True
        assert graph_readiness_data["source_intelligence_core_ingestion_artifact_digest_matched"] is True
        assert graph_readiness_data["source_intelligence_core_ingestion_digest_matched"] is True
        assert graph_readiness_data["graph_index_candidate_preview"]["candidate_node_count"] >= 4
        assert graph_readiness_data["graph_index_candidate_preview"]["candidate_edge_count"] >= 3
        assert graph_readiness_data["graph_index_mutation_performed"] is False
        assert graph_readiness_data["graph_snapshot_written"] is False
        assert graph_readiness_data["canonical_mutation_performed"] is False

        graph_indexing_preview = api.index_capture_to_markdown_source_pack_sic_graph_indexing(
            {
                "source_intelligence_core_ingestion_artifact_path": ingestion_data[
                    "source_intelligence_core_ingestion_artifact_path"
                ],
                "expected_sic_ingestion_artifact_digest": ingestion_data[
                    "source_intelligence_core_ingestion_artifact"
                ]["artifact_digest"],
                "expected_sic_ingestion_digest": ingestion_data[
                    "source_intelligence_core_ingestion_digest"
                ],
                "expected_graph_index_preview_packet_digest": graph_readiness_data[
                    "graph_index_preview_packet_digest"
                ],
                "target_workspace_id": "vcmi-reviewed-captures",
            }
        )
        assert graph_indexing_preview["ok"] is True
        assert (
            graph_indexing_preview["surface"]
            == "capture_to_markdown_source_pack_sic_graph_indexing"
        )
        graph_indexing_preview_data = graph_indexing_preview["data"]
        assert graph_indexing_preview_data["action"] == "source_pack_sic_graph_indexing"
        assert graph_indexing_preview_data["graph_indexing_executor_preview_ready"] is True
        assert graph_indexing_preview_data["graph_indexing_write_allowed_now"] is False
        assert graph_indexing_preview_data["graph_snapshot_written"] is False
        assert graph_indexing_preview_data["canonical_mutation_performed"] is False

        graph_indexing = api.index_capture_to_markdown_source_pack_sic_graph_indexing(
            {
                "source_intelligence_core_ingestion_artifact_path": ingestion_data[
                    "source_intelligence_core_ingestion_artifact_path"
                ],
                "expected_sic_ingestion_artifact_digest": ingestion_data[
                    "source_intelligence_core_ingestion_artifact"
                ]["artifact_digest"],
                "expected_sic_ingestion_digest": ingestion_data[
                    "source_intelligence_core_ingestion_digest"
                ],
                "expected_graph_index_preview_packet_digest": graph_readiness_data[
                    "graph_index_preview_packet_digest"
                ],
                "operator_statement": graph_indexing_preview_data["required_operator_statement"],
                "target_workspace_id": "vcmi-reviewed-captures",
                "write_graph_indexing_marker": True,
                "write_graph_snapshot": True,
                "write_graph_indexing_artifact": True,
            }
        )
        assert graph_indexing["ok"] is True
        graph_indexing_data = graph_indexing["data"]
        assert graph_indexing_data["graph_indexing_marker_written"] is True
        assert graph_indexing_data["graph_snapshot_written"] is True
        assert graph_indexing_data["graph_store_manifest_written"] is True
        assert graph_indexing_data["graph_current_pointer_written"] is True
        assert graph_indexing_data["graph_indexing_artifact_written"] is True
        assert graph_indexing_data["graph_index_mutation_performed"] is True
        assert graph_indexing_data["canonical_mutation_performed"] is False
        for path in graph_indexing_data["written_paths"]:
            assert (tmp_path / path).is_file()

        canonical_readiness = api.preview_capture_to_markdown_source_pack_canonical_promotion_readiness(
            {
                "graph_indexing_artifact_path": graph_indexing_data["graph_indexing_artifact_path"],
                "expected_graph_indexing_artifact_digest": graph_indexing_data[
                    "graph_indexing_artifact"
                ]["artifact_digest"],
            }
        )
        assert canonical_readiness["ok"] is True
        assert (
            canonical_readiness["surface"]
            == "capture_to_markdown_source_pack_canonical_promotion_readiness"
        )
        canonical_data = canonical_readiness["data"]
        assert canonical_data["action"] == "source_pack_canonical_promotion_readiness"
        assert canonical_data["canonical_promotion_readiness_preview_ready"] is True
        assert canonical_data["ready_for_canonical_promotion_approval_design"] is True
        assert canonical_data["graph_indexing_artifact_digest_matched"] is True
        assert canonical_data["graph_store_current_pointer_verified"] is True
        assert canonical_data["future_canonical_promotion_candidate_digest"]
        assert canonical_data["canonical_target_count"] >= 2
        assert canonical_data["canonical_mutation_allowed_now"] is False
        assert canonical_data["canonical_mutation_performed"] is False
        assert canonical_data["canonical_knowledge_promotion_performed"] is False
        assert canonical_data["provider_call_performed"] is False
        assert canonical_data["external_send_performed"] is False
        assert canonical_data["attachment_delete_performed"] is False

        canonical_approval_design = (
            api.preview_capture_to_markdown_source_pack_canonical_promotion_approval_design(
                {
                    "graph_indexing_artifact_path": graph_indexing_data[
                        "graph_indexing_artifact_path"
                    ],
                    "expected_graph_indexing_artifact_digest": graph_indexing_data[
                        "graph_indexing_artifact"
                    ]["artifact_digest"],
                    "expected_canonical_promotion_candidate_digest": canonical_data[
                        "future_canonical_promotion_candidate_digest"
                    ],
                }
            )
        )
        assert canonical_approval_design["ok"] is True
        assert (
            canonical_approval_design["surface"]
            == "capture_to_markdown_source_pack_canonical_promotion_approval_design"
        )
        canonical_approval_data = canonical_approval_design["data"]
        assert canonical_approval_data["action"] == "source_pack_canonical_promotion_approval_design"
        assert canonical_approval_data["canonical_promotion_approval_design_ready"] is True
        assert (
            canonical_approval_data[
                "future_canonical_promotion_approval_packet_preview_ready"
            ]
            is True
        )
        assert canonical_approval_data["ready_for_canonical_promotion_approval_request_writer"] is True
        assert canonical_approval_data["ready_for_canonical_promotion_executor"] is False
        assert canonical_approval_data["canonical_promotion_allowed_now"] is False
        assert canonical_approval_data["canonical_promotion_performed"] is False
        assert canonical_approval_data["canonical_knowledge_note_written"] is False
        assert canonical_approval_data["canonical_knowledge_index_written"] is False
        assert canonical_approval_data["provider_call_performed"] is False
        assert canonical_approval_data["external_send_performed"] is False
        assert canonical_approval_data["attachment_delete_performed"] is False
        assert canonical_approval_data["future_canonical_promotion_approval_packet_preview"][
            "approval_request_digest"
        ]

        canonical_packet = canonical_approval_data[
            "future_canonical_promotion_approval_packet_preview"
        ]
        canonical_request = (
            api.preview_capture_to_markdown_source_pack_canonical_promotion_approval_request(
                {
                    "graph_indexing_artifact_path": graph_indexing_data[
                        "graph_indexing_artifact_path"
                    ],
                    "expected_graph_indexing_artifact_digest": graph_indexing_data[
                        "graph_indexing_artifact"
                    ]["artifact_digest"],
                    "expected_canonical_promotion_candidate_digest": canonical_data[
                        "future_canonical_promotion_candidate_digest"
                    ],
                    "expected_canonical_promotion_approval_request_digest": canonical_packet[
                        "approval_request_digest"
                    ],
                    "operator_statement": canonical_approval_data["approval_design"][
                        "future_operator_statement_required"
                    ],
                    "write_approval_request": True,
                }
            )
        )
        assert canonical_request["ok"] is True
        assert (
            canonical_request["surface"]
            == "capture_to_markdown_source_pack_canonical_promotion_approval_request"
        )
        canonical_request_data = canonical_request["data"]
        assert canonical_request_data["action"] == "source_pack_canonical_promotion_approval_request"
        assert canonical_request_data["approval_request_written"] is True
        assert canonical_request_data["approval_artifact_written"] is True
        assert canonical_request_data["approval_decision_written"] is False
        assert canonical_request_data["approval_consumed"] is False
        assert canonical_request_data["approval_exact_once_marker_written"] is False
        assert canonical_request_data["ready_for_canonical_promotion_approval_decision"] is True
        assert canonical_request_data["ready_for_canonical_promotion_executor"] is False
        assert canonical_request_data["canonical_promotion_allowed_now"] is False
        assert canonical_request_data["canonical_promotion_performed"] is False
        assert canonical_request_data["canonical_knowledge_note_written"] is False
        assert canonical_request_data["canonical_knowledge_index_written"] is False
        assert canonical_request_data["canonical_graph_mutation_performed"] is False
        assert canonical_request_data["provider_call_performed"] is False
        assert canonical_request_data["external_send_performed"] is False
        assert canonical_request_data["attachment_delete_performed"] is False
        assert (tmp_path / canonical_request_data["approval_artifact_path"]).is_file()

        canonical_decision_readiness = (
            api.preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness(
                {
                    "graph_indexing_artifact_path": graph_indexing_data[
                        "graph_indexing_artifact_path"
                    ],
                    "expected_graph_indexing_artifact_digest": graph_indexing_data[
                        "graph_indexing_artifact"
                    ]["artifact_digest"],
                    "expected_canonical_promotion_candidate_digest": canonical_data[
                        "future_canonical_promotion_candidate_digest"
                    ],
                    "expected_canonical_promotion_approval_request_digest": canonical_packet[
                        "approval_request_digest"
                    ],
                    "approval_artifact_path": canonical_request_data["approval_artifact_path"],
                }
            )
        )
        assert canonical_decision_readiness["ok"] is True
        assert (
            canonical_decision_readiness["surface"]
            == "capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness"
        )
        canonical_decision_data = canonical_decision_readiness["data"]
        assert (
            canonical_decision_data["action"]
            == "source_pack_canonical_promotion_approval_decision_consumption_readiness"
        )
        assert canonical_decision_data["approval_request_artifact_verified"] is True
        assert canonical_decision_data["approval_request_pending"] is True
        assert canonical_decision_data["ready_for_canonical_promotion_approval_decision_writer"] is True
        assert canonical_decision_data["ready_for_canonical_promotion_approval_decision"] is True
        assert canonical_decision_data["ready_for_canonical_promotion_approval_consumption"] is False
        assert canonical_decision_data["ready_for_canonical_promotion_executor"] is False
        assert canonical_decision_data["approval_decision_written"] is False
        assert canonical_decision_data["approval_consumed"] is False
        assert canonical_decision_data["approval_exact_once_marker_written"] is False
        assert canonical_decision_data["canonical_promotion_allowed_now"] is False
        assert canonical_decision_data["canonical_promotion_performed"] is False
        assert canonical_decision_data["canonical_knowledge_note_written"] is False
        assert canonical_decision_data["canonical_knowledge_index_written"] is False
        assert canonical_decision_data["canonical_graph_mutation_performed"] is False
        assert canonical_decision_data["provider_call_performed"] is False
        assert canonical_decision_data["external_send_performed"] is False
        assert canonical_decision_data["attachment_delete_performed"] is False
        assert len(canonical_decision_data["future_approval_decision_options"]) == 2
        assert canonical_decision_data["future_approval_consumption_contract"][
            "effect_now"
        ] == "read_only_contract_preview"
        assert not (tmp_path / canonical_decision_data["future_approval_consumption_marker_path"]).exists()

        approved_option = next(
            option
            for option in canonical_decision_data["future_approval_decision_options"]
            if option["decision"] == "approved"
        )
        canonical_decision_write = (
            api.preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision(
                {
                    "graph_indexing_artifact_path": graph_indexing_data[
                        "graph_indexing_artifact_path"
                    ],
                    "expected_graph_indexing_artifact_digest": graph_indexing_data[
                        "graph_indexing_artifact"
                    ]["artifact_digest"],
                    "expected_canonical_promotion_candidate_digest": canonical_data[
                        "future_canonical_promotion_candidate_digest"
                    ],
                    "expected_canonical_promotion_approval_request_digest": canonical_packet[
                        "approval_request_digest"
                    ],
                    "approval_artifact_path": canonical_request_data["approval_artifact_path"],
                    "decision": "approved",
                    "expected_canonical_promotion_approval_decision_digest": approved_option[
                        "decision_preview_digest"
                    ],
                    "operator_statement": approved_option["required_operator_statement"],
                    "write_approval_decision": True,
                }
            )
        )
        assert canonical_decision_write["ok"] is True
        assert (
            canonical_decision_write["surface"]
            == "capture_to_markdown_source_pack_canonical_promotion_approval_decision"
        )
        canonical_decision_write_data = canonical_decision_write["data"]
        assert (
            canonical_decision_write_data["action"]
            == "source_pack_canonical_promotion_approval_decision"
        )
        assert canonical_decision_write_data["approval_decision_written"] is True
        assert canonical_decision_write_data["approval_decision_artifact_written"] is True
        assert canonical_decision_write_data["approval_consumed"] is False
        assert canonical_decision_write_data["approval_exact_once_marker_written"] is False
        assert canonical_decision_write_data["ready_for_canonical_promotion_approval_consumption"] is True
        assert canonical_decision_write_data["ready_for_canonical_promotion_executor"] is False
        assert canonical_decision_write_data["canonical_promotion_allowed_now"] is False
        assert canonical_decision_write_data["canonical_promotion_performed"] is False
        assert canonical_decision_write_data["canonical_knowledge_note_written"] is False
        assert canonical_decision_write_data["canonical_knowledge_index_written"] is False
        assert canonical_decision_write_data["canonical_graph_mutation_performed"] is False
        assert canonical_decision_write_data["provider_call_performed"] is False
        assert canonical_decision_write_data["external_send_performed"] is False
        assert canonical_decision_write_data["attachment_delete_performed"] is False
        assert (
            tmp_path / canonical_decision_write_data["approval_decision_artifact_path"]
        ).is_file()

        canonical_consumption_preview = (
            api.preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption(
                {
                    "graph_indexing_artifact_path": graph_indexing_data[
                        "graph_indexing_artifact_path"
                    ],
                    "expected_graph_indexing_artifact_digest": graph_indexing_data[
                        "graph_indexing_artifact"
                    ]["artifact_digest"],
                    "expected_canonical_promotion_candidate_digest": canonical_data[
                        "future_canonical_promotion_candidate_digest"
                    ],
                    "expected_canonical_promotion_approval_request_digest": canonical_packet[
                        "approval_request_digest"
                    ],
                    "approval_artifact_path": canonical_request_data["approval_artifact_path"],
                    "decision": "approved",
                    "approval_decision_artifact_path": canonical_decision_write_data[
                        "approval_decision_artifact_path"
                    ],
                    "expected_canonical_promotion_approval_decision_digest": canonical_decision_write_data[
                        "approval_decision_digest"
                    ],
                }
            )
        )
        assert canonical_consumption_preview["ok"] is True
        canonical_consumption_preview_data = canonical_consumption_preview["data"]
        assert (
            canonical_consumption_preview_data["action"]
            == "source_pack_canonical_promotion_approval_consumption"
        )
        assert canonical_consumption_preview_data["approval_consumption_preview_ready"] is True
        assert canonical_consumption_preview_data["approval_consumed"] is False
        assert canonical_consumption_preview_data["ready_for_canonical_promotion_executor"] is False
        assert canonical_consumption_preview_data["canonical_promotion_performed"] is False

        canonical_consumption_write = (
            api.preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption(
                {
                    "graph_indexing_artifact_path": graph_indexing_data[
                        "graph_indexing_artifact_path"
                    ],
                    "expected_graph_indexing_artifact_digest": graph_indexing_data[
                        "graph_indexing_artifact"
                    ]["artifact_digest"],
                    "expected_canonical_promotion_candidate_digest": canonical_data[
                        "future_canonical_promotion_candidate_digest"
                    ],
                    "expected_canonical_promotion_approval_request_digest": canonical_packet[
                        "approval_request_digest"
                    ],
                    "approval_artifact_path": canonical_request_data["approval_artifact_path"],
                    "decision": "approved",
                    "approval_decision_artifact_path": canonical_decision_write_data[
                        "approval_decision_artifact_path"
                    ],
                    "expected_canonical_promotion_approval_decision_digest": canonical_decision_write_data[
                        "approval_decision_digest"
                    ],
                    "expected_canonical_promotion_approval_consumption_digest": canonical_consumption_preview_data[
                        "approval_consumption_digest"
                    ],
                    "operator_statement": canonical_consumption_preview_data[
                        "required_operator_statement"
                    ],
                    "write_consumption_marker": True,
                    "write_approval_consumption": True,
                }
            )
        )
        assert canonical_consumption_write["ok"] is True
        assert (
            canonical_consumption_write["surface"]
            == "capture_to_markdown_source_pack_canonical_promotion_approval_consumption"
        )
        canonical_consumption_write_data = canonical_consumption_write["data"]
        assert canonical_consumption_write_data["approval_consumed"] is True
        assert canonical_consumption_write_data["approval_decision_consumed"] is True
        assert canonical_consumption_write_data["approval_exact_once_marker_written"] is True
        assert canonical_consumption_write_data["approval_consumption_artifact_written"] is True
        assert canonical_consumption_write_data["ready_for_canonical_promotion_executor"] is True
        assert canonical_consumption_write_data["canonical_promotion_allowed_now"] is False
        assert canonical_consumption_write_data["canonical_promotion_performed"] is False
        assert canonical_consumption_write_data["canonical_knowledge_note_written"] is False
        assert canonical_consumption_write_data["canonical_knowledge_index_written"] is False
        assert canonical_consumption_write_data["canonical_graph_mutation_performed"] is False
        assert canonical_consumption_write_data["provider_call_performed"] is False
        assert canonical_consumption_write_data["external_send_performed"] is False
        assert canonical_consumption_write_data["attachment_delete_performed"] is False
        assert all(
            (tmp_path / path).is_file()
            for path in canonical_consumption_write_data["written_paths"]
        )

    def test_review_clickthrough_blocks_secret_like_note(self, tmp_path):
        api = _make_api(tmp_path)
        save_data = api.save_capture_to_markdown(_payload(title="Secret Note Block", text="safe body"))["data"]

        result = api.review_capture_to_markdown({
            "sidecar_path": save_data["sidecar_path"],
            "decision": "reviewed",
            "review_note": "api_key=test-key-abcdefghijklmnop1234",
        })

        assert result["ok"] is False
        assert result["surface"] == "capture_to_markdown_review"
        assert "review_note contains secret-like material" in result["error"]["message"]

    def test_local_text_file_mode_is_vault_limited_and_previewable(self, tmp_path):
        source_file = tmp_path / "captures" / "source-note.md"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("Local vault file content.", encoding="utf-8")
        api = _make_api(tmp_path)

        result = api.preview_capture_to_markdown({
            "source_mode": "local_text_file",
            "profile": "research_note",
            "title": "Local File Capture",
            "file_path": "captures/source-note.md",
        })

        assert result["ok"] is True
        assert result["data"]["write_performed"] is False
        assert "Local vault file content." in result["data"]["markdown"]

    def test_capture_shortcut_settings_api_is_settings_scoped(self, tmp_path):
        api = _make_api(tmp_path)

        defaults = api.get_capture_hotkey_settings()
        assert defaults["ok"] is True
        assert defaults["data"]["bindings"]["open_capture_markdown"] == "Ctrl+Shift+C"
        assert defaults["data"]["bindings"]["run_display_region_collector"] == ""
        assert defaults["data"]["bindings"]["run_active_window_collector"] == ""
        assert defaults["data"]["bindings"]["run_browser_artifact_collector"] == ""
        assert defaults["data"]["bindings"]["run_active_browser_collector"] == ""
        assert defaults["data"]["bindings"]["run_chaseos_browser_page_collector"] == ""
        assert defaults["data"]["bindings"]["run_discord_artifact_collector"] == ""
        assert defaults["data"]["global_hotkeys_enabled"] is False
        assert defaults["data"]["authority"]["registers_global_hotkeys"] is False

        saved = api.save_capture_hotkey_settings(
            {
                "global_hotkeys_enabled": True,
                "bindings": {
                    "open_capture_markdown": "Ctrl+Alt+M",
                    "run_display_region_collector": "Ctrl+Alt+R",
                    "run_active_window_collector": "Ctrl+Alt+W",
                    "run_browser_artifact_collector": "Ctrl+Alt+A",
                    "run_active_browser_collector": "Ctrl+Alt+Q",
                    "run_chaseos_browser_page_collector": "Ctrl+Alt+B",
                    "run_discord_artifact_collector": "Ctrl+Alt+D",
                }
            }
        )
        assert saved["ok"] is True
        assert saved["data"]["bindings"]["open_capture_markdown"] == "Ctrl+Alt+M"
        assert saved["data"]["bindings"]["run_display_region_collector"] == "Ctrl+Alt+R"
        assert saved["data"]["bindings"]["run_active_window_collector"] == "Ctrl+Alt+W"
        assert saved["data"]["bindings"]["run_browser_artifact_collector"] == "Ctrl+Alt+A"
        assert saved["data"]["bindings"]["run_active_browser_collector"] == "Ctrl+Alt+Q"
        assert saved["data"]["bindings"]["run_chaseos_browser_page_collector"] == "Ctrl+Alt+B"
        assert saved["data"]["bindings"]["run_discord_artifact_collector"] == "Ctrl+Alt+D"
        assert saved["data"]["global_hotkeys_enabled"] is True
        assert saved["data"]["authority"]["registers_global_hotkeys"] is True
        assert saved["data"]["readiness"]["global_hotkey_registration_enabled"] is True
        assert (tmp_path / "runtime" / "studio" / "state" / "capture-hotkeys.json").is_file()

    def test_capture_local_image_text_settings_api_is_settings_scoped(self, tmp_path):
        command = _write_fake_local_text_engine(tmp_path, "configured image text")
        api = _make_api(tmp_path)

        defaults = api.get_capture_local_image_text_settings()
        assert defaults["ok"] is True
        assert defaults["data"]["readiness"]["settings_page_visible"] is True
        assert defaults["data"]["authority"]["provider_calls_allowed"] is False

        saved = api.save_capture_local_image_text_settings(
            {
                "local_ocr_command": command,
                "local_ocr_timeout_seconds": 30,
            }
        )
        assert saved["ok"] is True
        assert saved["data"]["local_ocr_command"] == command
        assert saved["data"]["local_ocr_timeout_seconds"] == 30
        assert saved["data"]["quality_fixture_proof"]["summary"]["fixture_runner_ready"] is True
        assert saved["data"]["quality_fixture_proof"]["summary"]["real_engine_quality_verified"] is False
        assert (tmp_path / "runtime" / "studio" / "state" / "capture-local-image-text.json").is_file()

    def test_capture_collector_settings_api_is_settings_scoped(self, tmp_path):
        api = _make_api(tmp_path)

        defaults = api.get_capture_collector_settings()
        assert defaults["ok"] is True
        assert defaults["data"]["surface"] == "studio_capture_collectors"
        assert defaults["data"]["screen_capture_enabled"] is False
        assert defaults["data"]["display_region_capture_enabled"] is False
        assert defaults["data"]["active_window_capture_enabled"] is False
        assert defaults["data"]["clipboard_capture_enabled"] is False
        assert defaults["data"]["ambient_clipboard_monitoring_enabled"] is False
        assert defaults["data"]["selected_text_capture_enabled"] is False
        assert defaults["data"]["accessibility_tree_capture_enabled"] is False
        assert defaults["data"]["browser_artifact_capture_enabled"] is False
        assert defaults["data"]["browser_extension_capture_enabled"] is False
        assert defaults["data"]["active_chaseos_browser_capture_enabled"] is False
        assert defaults["data"]["chaseos_browser_page_capture_enabled"] is False
        assert defaults["data"]["discord_artifact_capture_enabled"] is False
        assert defaults["data"]["readiness"]["screen_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["display_region_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["active_window_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["clipboard_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["ambient_clipboard_monitor_built"] is True
        assert defaults["data"]["readiness"]["selected_text_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["accessibility_tree_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["browser_artifact_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["browser_extension_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["active_chaseos_browser_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["chaseos_browser_page_capture_collector_built"] is True
        assert defaults["data"]["readiness"]["discord_artifact_capture_collector_built"] is True
        assert defaults["data"]["authority"]["captures_screen_pixels_on_settings_load"] is False
        assert defaults["data"]["authority"]["reads_clipboard_on_settings_load"] is False

        blocked = api.capture_current_screen_for_markdown({"operator_confirmed": True})
        assert blocked["ok"] is True
        assert blocked["data"]["ok"] is False
        assert blocked["data"]["blockers"] == ["screen_capture_disabled_in_settings"]

        region_blocked = api.capture_display_region_for_markdown({"operator_confirmed": True})
        assert region_blocked["ok"] is True
        assert region_blocked["data"]["ok"] is False
        assert region_blocked["data"]["blockers"] == ["display_region_capture_disabled_in_settings"]

        active_window_blocked = api.capture_active_window_for_markdown({"operator_confirmed": True})
        assert active_window_blocked["ok"] is True
        assert active_window_blocked["data"]["ok"] is False
        assert active_window_blocked["data"]["blockers"] == ["active_window_capture_disabled_in_settings"]

        clipboard_blocked = api.capture_clipboard_text_for_markdown({"operator_confirmed": True})
        assert clipboard_blocked["ok"] is True
        assert clipboard_blocked["data"]["ok"] is False
        assert clipboard_blocked["data"]["blockers"] == ["clipboard_capture_disabled_in_settings"]

        ambient_blocked = api.poll_ambient_clipboard_for_markdown(
            {"monitoring_session_confirmed": True}
        )
        assert ambient_blocked["ok"] is True
        assert ambient_blocked["data"]["ok"] is False
        assert ambient_blocked["data"]["blockers"] == [
            "ambient_clipboard_monitoring_disabled_in_settings"
        ]

        selected_text_blocked = api.capture_selected_text_for_markdown({"operator_confirmed": True})
        assert selected_text_blocked["ok"] is True
        assert selected_text_blocked["data"]["ok"] is False
        assert selected_text_blocked["data"]["blockers"] == ["selected_text_capture_disabled_in_settings"]

        accessibility_tree_blocked = api.capture_accessibility_tree_for_markdown({"operator_confirmed": True})
        assert accessibility_tree_blocked["ok"] is True
        assert accessibility_tree_blocked["data"]["ok"] is False
        assert accessibility_tree_blocked["data"]["blockers"] == [
            "accessibility_tree_capture_disabled_in_settings"
        ]

        browser_blocked = api.capture_browser_artifact_for_markdown({"operator_confirmed": True})
        assert browser_blocked["ok"] is True
        assert browser_blocked["data"]["ok"] is False
        assert browser_blocked["data"]["blockers"] == ["browser_artifact_capture_disabled_in_settings"]

        extension_blocked = api.capture_browser_extension_artifact_for_markdown({"operator_confirmed": True})
        assert extension_blocked["ok"] is True
        assert extension_blocked["data"]["ok"] is False
        assert extension_blocked["data"]["blockers"] == ["browser_extension_capture_disabled_in_settings"]

        active_browser_blocked = api.capture_active_chaseos_browser_for_markdown(
            {"operator_confirmed": True}
        )
        assert active_browser_blocked["ok"] is True
        assert active_browser_blocked["data"]["ok"] is False
        assert active_browser_blocked["data"]["blockers"] == [
            "active_chaseos_browser_capture_disabled_in_settings"
        ]

        chaseos_browser_blocked = api.capture_chaseos_browser_page_for_markdown({"operator_confirmed": True})
        assert chaseos_browser_blocked["ok"] is True
        assert chaseos_browser_blocked["data"]["ok"] is False
        assert chaseos_browser_blocked["data"]["blockers"] == ["chaseos_browser_page_capture_disabled_in_settings"]

        discord_blocked = api.capture_discord_artifact_for_markdown({"operator_confirmed": True})
        assert discord_blocked["ok"] is True
        assert discord_blocked["data"]["ok"] is False
        assert discord_blocked["data"]["blockers"] == ["discord_artifact_capture_disabled_in_settings"]

        saved = api.save_capture_collector_settings(
            {
                "screen_capture_enabled": True,
                "display_region_capture_enabled": True,
                "active_window_capture_enabled": True,
                "clipboard_capture_enabled": True,
                "ambient_clipboard_monitoring_enabled": True,
                "selected_text_capture_enabled": True,
                "accessibility_tree_capture_enabled": True,
                "browser_artifact_capture_enabled": True,
                "browser_extension_capture_enabled": True,
                "active_chaseos_browser_capture_enabled": True,
                "chaseos_browser_page_capture_enabled": True,
                "discord_artifact_capture_enabled": True,
            }
        )
        assert saved["ok"] is True
        assert saved["data"]["screen_capture_enabled"] is True
        assert saved["data"]["display_region_capture_enabled"] is True
        assert saved["data"]["active_window_capture_enabled"] is True
        assert saved["data"]["clipboard_capture_enabled"] is True
        assert saved["data"]["ambient_clipboard_monitoring_enabled"] is True
        assert saved["data"]["selected_text_capture_enabled"] is True
        assert saved["data"]["accessibility_tree_capture_enabled"] is True
        assert saved["data"]["browser_artifact_capture_enabled"] is True
        assert saved["data"]["browser_extension_capture_enabled"] is True
        assert saved["data"]["active_chaseos_browser_capture_enabled"] is True
        assert saved["data"]["chaseos_browser_page_capture_enabled"] is True
        assert saved["data"]["discord_artifact_capture_enabled"] is True
        collectors = {item["id"]: item for item in saved["data"]["collectors"]}
        assert collectors["screen_capture"]["action"] == "run_screen_capture_collector"
        assert collectors["display_region_capture"]["action"] == "run_display_region_collector"
        assert collectors["active_window_capture"]["action"] == "run_active_window_collector"
        assert collectors["clipboard_text_capture"]["action"] == "run_clipboard_text_collector"
        assert collectors["ambient_clipboard_monitor"]["action"] == "run_ambient_clipboard_monitor"
        assert collectors["selected_text_capture"]["action"] == "run_selected_text_collector"
        assert collectors["accessibility_tree_capture"]["action"] == "run_accessibility_tree_collector"
        assert collectors["active_browser_artifact_capture"]["action"] == "run_browser_artifact_collector"
        assert collectors["browser_extension_capture"]["action"] == "run_browser_extension_collector"
        assert collectors["active_browser_tab_capture"]["action"] == "run_active_browser_collector"
        assert collectors["chaseos_browser_page_capture"]["action"] == "run_chaseos_browser_page_collector"
        assert collectors["discord_capture"]["action"] == "run_discord_artifact_collector"
        assert (tmp_path / "runtime" / "studio" / "state" / "capture-collectors.json").is_file()

    def test_capture_page_and_settings_load_do_not_run_saved_local_image_text_command(self, tmp_path):
        _write_png(tmp_path)
        marker = tmp_path / "runtime" / "capture" / "command-ran.txt"
        command = _write_marker_local_text_engine(tmp_path, "Explicit run text.", marker)
        api = _make_api(tmp_path)

        saved = api.save_capture_local_image_text_settings(
            {
                "local_ocr_command": command,
                "local_ocr_timeout_seconds": 30,
            }
        )
        assert saved["ok"] is True
        assert not marker.exists()

        settings = api.get_capture_local_image_text_settings()
        assert settings["ok"] is True
        assert not marker.exists()

        panel = api.get_capture_to_markdown_panel(10)
        assert panel["ok"] is True
        assert panel["data"]["capture_local_image_text"]["local_ocr_command"] == command
        assert not marker.exists()

        preview = api.preview_capture_to_markdown({
            "source_mode": "screenshot_text_extraction",
            "profile": "research_note",
            "title": "Explicit Image Text Run",
            "file_path": "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        })
        assert preview["ok"] is True
        assert marker.read_text(encoding="utf-8") == "ran"
        assert "Explicit run text." in preview["data"]["markdown"]

    def test_screenshot_text_extraction_uses_settings_command_when_payload_command_is_blank(self, tmp_path):
        _write_png(tmp_path)
        command = _write_fake_local_text_engine(tmp_path, "Studio settings image text.")
        api = _make_api(tmp_path)
        api.save_capture_local_image_text_settings(
            {
                "local_ocr_command": command,
                "local_ocr_timeout_seconds": 30,
            }
        )

        result = api.preview_capture_to_markdown({
            "source_mode": "screenshot_text_extraction",
            "profile": "research_note",
            "title": "Studio Settings Screenshot Text",
            "file_path": "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        })

        assert result["ok"] is True
        assert result["data"]["packet"]["capture_method"] == "screenshot_local_text_extraction"
        assert "Studio settings image text." in result["data"]["markdown"]

    def test_controlled_html_artifact_mode_requires_confined_artifact_and_url(self, tmp_path):
        source_file = tmp_path / "07_LOGS" / "Browser-Runs" / "local" / "default" / "controlled.html"
        source_file.parent.mkdir(parents=True)
        source_file.write_text(
            "<html><head><title>Studio Controlled</title></head><body><p>Studio controlled DOM text.</p></body></html>",
            encoding="utf-8",
        )
        api = _make_api(tmp_path)

        result = api.preview_capture_to_markdown({
            "source_mode": "controlled_html_artifact",
            "profile": "research_note",
            "title": "Studio Controlled",
            "file_path": "07_LOGS/Browser-Runs/local/default/controlled.html",
            "source_url": "https://example.test/controlled",
        })

        assert result["ok"] is True
        assert result["data"]["write_performed"] is False
        assert result["data"]["packet"]["capture_method"] == "controlled_browser_dom"
        assert "Studio controlled DOM text." in result["data"]["markdown"]
        assert not (tmp_path / "03_INPUTS").exists()

    def test_screenshot_attachment_mode_imports_vault_local_image_without_ocr(self, tmp_path):
        _write_png(tmp_path)
        api = _make_api(tmp_path)

        result = api.preview_capture_to_markdown({
            "source_mode": "screenshot_attachment",
            "profile": "research_note",
            "title": "Studio Screenshot",
            "file_path": "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
        })

        assert result["ok"] is True
        data = result["data"]
        assert data["write_performed"] is False
        assert data["packet"]["capture_method"] == "screenshot_attachment_import"
        assert data["packet"]["quality"]["extraction_status"] == "attachment_only"
        assert data["packet"]["quality"]["confidence"] == "screenshot_attachment_no_ocr"
        assert "ocr_not_performed" in data["packet"]["quality"]["extraction_warnings"]
        assert data["packet"]["attachments"][0]["mime_type"] == "image/png"
        assert data["authority"]["provider_call_allowed"] is False
        assert "screenshots:" in data["markdown"]
        assert not (tmp_path / "03_INPUTS").exists()

    def test_screenshot_text_extraction_mode_uses_local_command_without_writes(self, tmp_path):
        _write_png(tmp_path)
        command = _write_fake_local_text_engine(tmp_path, "Studio extracted image text.")
        api = _make_api(tmp_path)

        result = api.preview_capture_to_markdown({
            "source_mode": "screenshot_text_extraction",
            "profile": "research_note",
            "title": "Studio Screenshot Text",
            "file_path": "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            "local_ocr_command": command,
        })

        assert result["ok"] is True
        data = result["data"]
        assert data["write_performed"] is False
        assert data["packet"]["capture_method"] == "screenshot_local_text_extraction"
        assert data["packet"]["quality"]["extraction_status"] == "text_extracted"
        assert data["packet"]["quality"]["confidence"] == "local_optical_character_recognition"
        assert "local_optical_character_recognition_performed" in data["packet"]["quality"]["extraction_warnings"]
        assert data["packet"]["provenance"]["transformation_chain"][2]["step"] == "local_optical_character_recognition_extract"
        assert "Studio extracted image text." in data["markdown"]
        assert "optical_character_recognition_status: text_extracted" in data["markdown"]
        assert data["authority"]["provider_call_allowed"] is False
        assert not (tmp_path / "03_INPUTS").exists()

    def test_photo_document_text_extraction_mode_reads_docx_without_writes(self, tmp_path):
        source_file = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Photo-Documents" / "studio-proof.docx"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source_file, "w") as archive:
            archive.writestr(
                "word/document.xml",
                (
                    "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
                    "<w:body><w:p><w:r><w:t>Studio document extraction proof.</w:t></w:r></w:p></w:body>"
                    "</w:document>"
                ),
            )
        api = _make_api(tmp_path)

        result = api.preview_capture_to_markdown({
            "source_mode": "photo_document_text_extraction",
            "profile": "research_note",
            "title": "Studio Document Text",
            "file_path": "03_INPUTS/00_QUARANTINE/Photo-Documents/studio-proof.docx",
        })

        assert result["ok"] is True
        data = result["data"]
        assert data["write_performed"] is False
        assert data["packet"]["capture_method"] == "photo_document_text_extraction"
        assert data["packet"]["quality"]["confidence"] == "local_document_text_extraction"
        assert "local_document_text_extraction_performed" in data["packet"]["quality"]["extraction_warnings"]
        assert "Studio document extraction proof." in data["markdown"]
        assert data["authority"]["provider_call_allowed"] is False
        assert not (tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources").exists()

    def test_intake_listing_compatible_after_save(self, tmp_path):
        api = _make_api(tmp_path)
        api.save_capture_to_markdown(_payload(title="Intake Compatible Capture", text="intake compatible body"))

        result = api.get_intake_panel(input_class="source")
        items = result["data"]["items"]
        assert any(item["title"] == "Intake Compatible Capture" for item in items)
        assert any(item["source_platform"] == "visual-capture" for item in items)


class TestCaptureToMarkdownRegistry:
    def test_registry_mounts_capture_markdown_panel(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        panel = panels["capture-markdown"]
        assert panel["status"] == "mounted"
        assert panel["frontend_target"] == "panel-capture-markdown"
        assert panel["route_hint"] == "#/capture-markdown"
        assert panel["read_only"] is False
        assert panel["write_mode"] == "approval_gated"
        assert "save_capture_to_markdown" in panel["api_methods"]
        assert "review_capture_to_markdown" in panel["api_methods"]
        assert "update_capture_to_markdown_attachment_disposition" in panel["api_methods"]
        assert "cleanup_capture_to_markdown_attachments" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_approval" in panel["api_methods"]
        assert "execute_capture_to_markdown_source_pack_write" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_readiness" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_approval_design" in panel["api_methods"]
        assert "request_capture_to_markdown_source_pack_aor_dispatch_approval" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness" in panel["api_methods"]
        assert "write_capture_to_markdown_source_pack_aor_dispatch_approval_decision" in panel["api_methods"]
        assert "consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision" in panel["api_methods"]
        assert "write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness" in panel["api_methods"]
        assert "claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task" in panel["api_methods"]
        assert (
            "preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness"
            in panel["api_methods"]
        )
        assert (
            "execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run"
            in panel["api_methods"]
        )
        assert (
            "execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle"
            in panel["api_methods"]
        )
        assert (
            "preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness"
            in panel["api_methods"]
        )
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_readiness" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_design" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_request" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision_consumption_readiness" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision" in panel["api_methods"]
        assert "consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision" in panel["api_methods"]
        assert "ingest_capture_to_markdown_source_pack_sic_ingestion" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_sic_graph_indexing_readiness" in panel["api_methods"]
        assert "index_capture_to_markdown_source_pack_sic_graph_indexing" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_readiness" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_design" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_request" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption" in panel["api_methods"]
        assert "preview_capture_to_markdown_source_pack_canonical_promotion" in panel["api_methods"]
        assert "03_INPUTS/00_QUARANTINE raw Markdown artifact" in panel["possible_writes"]
        assert "Phase 8 sidecar review-state update" in panel["possible_writes"]
        assert "adjacent .visual_capture.json review-state update" in panel["possible_writes"]
        assert "attachment retention metadata and exact-confirmation quarantine cleanup controls" in panel["possible_writes"]
        assert "quarantine-local screenshot attachment copy when screenshot source mode is saved" in panel["possible_writes"]
        assert "approved runtime/acquisition/packs/ source-pack JSON artifacts" in panel["possible_writes"]
        assert "approved source-pack exact-once marker under runtime/acquisition/packs/" in panel["possible_writes"]
        assert "pending AOR dispatch approval request under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/" in panel["possible_writes"]
        assert "approved/rejected AOR dispatch approval decision under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_decisions/" in panel["possible_writes"]
        assert "AOR dispatch approval exact-once marker under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_consumption_markers/" in panel["possible_writes"]
        assert "AOR dispatch approval consumption artifact under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_consumptions/" in panel["possible_writes"]
        assert "AOR dispatch Agent Bus task exact-once marker under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_agent_bus_task_markers/" in panel["possible_writes"]
        assert "AOR dispatch Agent Bus task artifact under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_agent_bus_tasks/" in panel["possible_writes"]
        assert "local open Agent Bus task row in runtime/agent_bus/agent_bus.sqlite" in panel["possible_writes"]
        assert "AOR dispatch Agent Bus task claim marker under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_agent_bus_task_claim_markers/" in panel["possible_writes"]
        assert "AOR dispatch Agent Bus task claim artifact under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_agent_bus_task_claims/" in panel["possible_writes"]
        assert "local Agent Bus task row status/owner claim update in runtime/agent_bus/agent_bus.sqlite" in panel["possible_writes"]
        assert "AOR dry-run exact-once marker under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_aor_dry_run_markers/" in panel["possible_writes"]
        assert "AOR dry-run OSRIL session/events under runtime/osril/run/" in panel["possible_writes"]
        assert "AOR dry-run audit record under 07_LOGS/Agent-Activity/" in panel["possible_writes"]
        assert "AOR dry-run artifact under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_aor_dry_runs/" in panel["possible_writes"]
        assert "AOR dispatch Agent Bus task status lifecycle marker under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_agent_bus_task_status_lifecycle_markers/" in panel["possible_writes"]
        assert "local Agent Bus task row status update to review in runtime/agent_bus/agent_bus.sqlite" in panel["possible_writes"]
        assert "AOR dispatch Agent Bus task status lifecycle artifact under 07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/_agent_bus_task_status_lifecycle/" in panel["possible_writes"]
        assert "pending Source Intelligence Core ingestion approval request under 07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/" in panel["possible_writes"]
        assert "approved/rejected Source Intelligence Core ingestion approval decision under 07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_decisions/" in panel["possible_writes"]
        assert "Source Intelligence Core ingestion approval consumption marker under 07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_consumption_markers/" in panel["possible_writes"]
        assert "Source Intelligence Core ingestion approval consumption artifact under 07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_consumptions/" in panel["possible_writes"]
        assert "Source Intelligence Core ingestion exact-once marker under 07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_ingestion_markers/" in panel["possible_writes"]
        assert "Source Intelligence Core reviewed source package under runtime/source_intelligence/workspaces/" in panel["possible_writes"]
        assert "Source Intelligence Core workspace membership update under runtime/source_intelligence/workspaces/" in panel["possible_writes"]
        assert "Source Intelligence Core ingestion artifact under 07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_ingestions/" in panel["possible_writes"]
        assert "Source Intelligence Core graph indexing exact-once marker under 07_LOGS/Agent-Activity/_vcmi_sic_graph_indexing/_markers/" in panel["possible_writes"]
        assert "graph snapshot and manifest/current pointer under runtime/graph/store/" in panel["possible_writes"]
        assert "Source Intelligence Core graph indexing execution artifact under 07_LOGS/Agent-Activity/_vcmi_sic_graph_indexing/_executions/" in panel["possible_writes"]
        assert "pending canonical-promotion approval request under 07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/" in panel["possible_writes"]
        assert "approved/rejected canonical-promotion approval decision under 07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/_decisions/" in panel["possible_writes"]
        assert "canonical-promotion approval consumption marker under 07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/_consumption_markers/" in panel["possible_writes"]
        assert "canonical-promotion approval consumption artifact under 07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/_consumptions/" in panel["possible_writes"]
        assert "canonical-promotion exact-once marker under 07_LOGS/Agent-Activity/_vcmi_canonical_promotion/_markers/" in panel["possible_writes"]
        assert "canonical reviewed capture note under 02_KNOWLEDGE/Source-Intelligence/Reviewed-Captures/" in panel["possible_writes"]
        assert "managed Knowledge Index route block under 02_KNOWLEDGE/Knowledge-Index.md" in panel["possible_writes"]
        assert "canonical-promotion execution artifact under 07_LOGS/Agent-Activity/_vcmi_canonical_promotion/_executions/" in panel["possible_writes"]
        assert "canonical-promotion approval design" in panel["blocked_reason"]
        assert "governed attachment disposition policy" in panel["blocked_reason"]
        assert "Attachment cleanup is exact-confirmation gated" in panel["blocked_reason"]
        assert "downstream gate readiness, source-pack write approval preview" in panel["blocked_reason"]
        assert "post-write AOR dispatch readiness preview" in panel["blocked_reason"]
        assert "AOR dispatch approval design preview" in panel["blocked_reason"]
        assert "pending approval decision/consumption readiness" in panel["blocked_reason"]
        assert "Approved source-pack write execution and downstream executors remain exact digest/statement gated" in panel["blocked_reason"]
        assert "Source Intelligence Core ingestion readiness" in panel["blocked_reason"]
        assert "Source Intelligence Core ingestion approval design" in panel["blocked_reason"]
        assert "canonical-promotion approval design" in panel["blocked_reason"]
        assert "rewrite source packs" in panel["blocked_reason"]
        assert "register hotkeys" in panel["blocked_reason"]
        assert "accept external capture commands" in panel["blocked_reason"]
        assert panel["blocked_authority"]["canonical_mutation"] is False
        assert registry["readiness"]["capture_to_markdown_panel_mounted"] is True
        assert registry["readiness"]["capture_to_markdown_raw_quarantine_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_external_surface_deferral_policy_ready"] is True
        assert registry["readiness"]["capture_to_markdown_operator_review_state_machine_ready"] is True
        assert registry["readiness"]["capture_to_markdown_operator_review_studio_clickthrough_ready"] is True
        assert registry["readiness"]["capture_to_markdown_operator_review_studio_clickthrough_deferred"] is False
        assert registry["readiness"]["capture_to_markdown_attachment_disposition_policy_ready"] is True
        assert registry["readiness"]["capture_to_markdown_attachment_disposition_metadata_only"] is False
        assert registry["readiness"]["capture_to_markdown_attachment_disposition_runtime_delete_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_attachment_delete_controls_ready"] is True
        assert registry["readiness"]["capture_to_markdown_attachment_cleanup_requires_exact_operator_confirmation"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_downstream_gate_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_approval_preview_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_approval_preview_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_approval_preview_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_approval_artifact_write_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_write_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_write_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_write_requires_exact_approval"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_write_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_write_blocked_without_exact_approval"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_rewrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_packet_preview_ready_after_write"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_design_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_design_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_design_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_request_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_request_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_request_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_request_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_request_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_artifact_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_request_overwrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_decision_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_decision_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_decision_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_decision_writer_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_marker_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_approval_consumption_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_writer_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_write_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_claim_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_task_execute_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_marker_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_call_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_call_blocked_without_exact_executor_approval"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle_marker_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_claimed_task_review_status_update_blocked_without_exact_approval"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_future_packet_preview_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_future_packet_preview_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_marker_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_overwrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_readiness_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_candidate_preview_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_executor_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_indexing_executor_requires_operator_statement"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_snapshot_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_graph_store_manifest_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_requires_exact_graph_artifact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_candidate_preview_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_design_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_design_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_design_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_packet_preview_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_request_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_request_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_request_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_request_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_request_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_request_overwrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_pending_request"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_consumption_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_writer_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_decision_overwrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_marker_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_approval_consumption_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_promotion_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_knowledge_note_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_canonical_knowledge_index_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_design_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_design_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_design_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_packet_preview_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_request_writer_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_request_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_request_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_request_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_request_overwrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_consumption_readiness_read_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_writer_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_decision_overwrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_executor_ui_ready"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_marker_create_only"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_requires_exact_digest"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_write_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_overwrite_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_source_pack_sic_ingestion_approval_consumption_allowed"] is True
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_aor_dispatch_executor_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_aor_dispatch_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_sic_ingestion_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_reviewed_capture_graph_canonical_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_hotkey_overlay_external_surfaces_blocked"] is True
        assert registry["readiness"]["capture_to_markdown_discord_commands_blocked"] is False
        assert registry["readiness"]["capture_to_markdown_active_chaseos_browser_collector_built"] is True
        assert registry["readiness"]["capture_to_markdown_active_chaseos_browser_collector_settings_gated"] is True
        assert registry["readiness"]["capture_to_markdown_personal_active_browser_tab_blocked"] is True


class TestCaptureToMarkdownFrontend:
    def _html(self) -> str:
        return (FRONTEND / "index.html").read_text(encoding="utf-8")

    def _css(self) -> str:
        return (FRONTEND / "styles.css").read_text(encoding="utf-8")

    def _js(self) -> str:
        return (FRONTEND / "app.js").read_text(encoding="utf-8")

    def test_sidebar_and_panel_markup_present(self):
        html = self._html()
        assert 'data-panel="capture-markdown"' in html
        assert 'id="panel-capture-markdown"' in html
        assert 'id="capture-markdown-profile-select"' in html
        assert 'id="capture-markdown-source-select"' in html
        assert 'id="capture-markdown-source-options"' in html
        assert 'id="capture-markdown-raw-text"' in html
        assert 'id="capture-markdown-preview-btn"' in html
        assert 'id="capture-markdown-save-btn"' in html
        assert 'id="capture-markdown-policy-body"' in html
        assert 'id="capture-markdown-source-pack-preview-body"' in html
        assert 'id="capture-markdown-recent-body"' in html

    def test_css_classes_present(self):
        css = self._css()
        assert ".capture-markdown-panel" in css
        assert ".capture-markdown-grid" in css
        assert ".capture-markdown-markdown" in css
        assert ".capture-markdown-recent-item" in css
        assert ".capture-markdown-review-row" in css
        assert ".capture-markdown-review-decision" in css
        assert ".capture-markdown-policy-strip" in css
        assert ".capture-markdown-source-card" in css
        assert ".capture-markdown-palette" in css
        assert ".capture-markdown-palette-action" in css
        assert ".capture-hotkey-row" in css
        assert ".capture-markdown-approval-preview-btn" in css
        assert ".capture-markdown-source-pack-write-btn" in css
        assert ".capture-markdown-source-pack-aor-readiness-btn" in css
        assert ".capture-markdown-source-pack-aor-approval-design-btn" in css
        assert ".capture-markdown-source-pack-aor-approval-request-btn" in css
        assert ".capture-markdown-source-pack-aor-approval-consumption-readiness-btn" in css
        assert ".capture-markdown-source-pack-aor-approval-decision-btn" in css
        assert ".capture-markdown-source-pack-aor-approval-consume-preview-btn" in css
        assert ".capture-markdown-source-pack-aor-approval-consume-btn" in css
        assert ".capture-markdown-source-pack-write-statement" in css
        assert ".capture-markdown-source-pack-aor-approval-request-statement" in css
        assert ".capture-markdown-source-pack-aor-approval-decision-statement" in css
        assert ".capture-markdown-source-pack-aor-approval-consume-statement" in css
        assert ".capture-markdown-source-pack-written-paths" in css
        assert ".capture-markdown-source-pack-boundary" in css
        assert ".capture-markdown-source-pack-aor-readiness-result" in css
        assert ".capture-markdown-source-pack-aor-approval-design-result" in css
        assert ".capture-markdown-source-pack-aor-approval-request-result" in css
        assert ".capture-markdown-source-pack-aor-approval-consumption-readiness-result" in css
        assert ".capture-markdown-source-pack-aor-approval-decision-result" in css
        assert ".capture-markdown-source-pack-aor-approval-consume-preview-result" in css
        assert ".capture-markdown-source-pack-aor-approval-consume-result" in css
        assert ".capture-markdown-source-pack-agent-bus-task-preview-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-task-write-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-task-claim-readiness-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-aor-dry-run-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-status-lifecycle-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-full-dispatch-readiness-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-full-dispatch-btn" in css
        assert ".capture-markdown-source-pack-sic-readiness-btn" in css
        assert ".capture-markdown-source-pack-agent-bus-task-statement" in css
        assert ".capture-markdown-source-pack-agent-bus-aor-dry-run-statement" in css
        assert ".capture-markdown-source-pack-agent-bus-status-lifecycle-statement" in css
        assert ".capture-markdown-source-pack-agent-bus-full-dispatch-statement" in css
        assert ".capture-markdown-source-pack-agent-bus-task-preview-result" in css
        assert ".capture-markdown-source-pack-agent-bus-task-result" in css
        assert ".capture-markdown-source-pack-agent-bus-task-claim-readiness-result" in css
        assert ".capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-result" in css
        assert ".capture-markdown-source-pack-agent-bus-aor-dry-run-result" in css
        assert ".capture-markdown-source-pack-agent-bus-status-lifecycle-result" in css
        assert ".capture-markdown-source-pack-agent-bus-full-dispatch-readiness-result" in css
        assert ".capture-markdown-source-pack-agent-bus-full-dispatch-result" in css
        assert ".capture-markdown-source-pack-sic-readiness-result" in css
        assert ".capture-markdown-source-pack-aor-approval-decision-card" in css
        assert ".capture-markdown-source-pack-preview" in css
        assert ".capture-markdown-source-pack-preview-body { min-height: 0; position: relative; z-index: 2; }" in css
        assert ".capture-markdown-preview-body:empty { pointer-events: none; }" in css
        assert ".capture-markdown-guard-failure" in css
        assert ".capture-markdown-guard-failure-message" in css

    def test_js_routes_and_api_calls_present(self):
        js = self._js()
        assert "'capture-markdown': '#/capture-markdown'" in js
        assert "async function loadCaptureMarkdownPanel(" in js
        assert "function renderCaptureMarkdownPanel(" in js
        assert "async function previewCaptureMarkdown(" in js
        assert "async function saveCaptureMarkdown(" in js
        assert "function escHtmlRaw(" in js
        assert "escHtmlRaw(data.markdown || '')" in js
        assert "function renderCaptureMarkdownGuardFailure(" in js
        assert "data-capture-guard-failure=\"true\"" in js
        assert "Source-pack write blocked" in js
        assert "Agent Orchestration Runtime approval request blocked" in js
        assert "Source Intelligence Core approval request blocked" in js
        assert "Canonical promotion request blocked" in js
        assert "async function reviewCaptureMarkdown(" in js
        assert "async function previewCaptureMarkdownSourcePackApproval(" in js
        assert "async function executeCaptureMarkdownSourcePackWrite(" in js
        assert "async function previewCaptureMarkdownSourcePackAorDispatchReadiness(" in js
        assert "async function previewCaptureMarkdownSourcePackAorDispatchApprovalDesign(" in js
        assert "async function requestCaptureMarkdownSourcePackAorDispatchApproval(" in js
        assert "async function previewCaptureMarkdownSourcePackAorDispatchApprovalConsumptionReadiness(" in js
        assert "async function writeCaptureMarkdownSourcePackAorDispatchApprovalDecision(" in js
        assert "async function previewCaptureMarkdownSourcePackAorDispatchApprovalConsumption(" in js
        assert "async function consumeCaptureMarkdownSourcePackAorDispatchApprovalDecision(" in js
        assert "async function previewCaptureMarkdownSourcePackAorDispatchAgentBusTask(" in js
        assert "async function writeCaptureMarkdownSourcePackAorDispatchAgentBusTask(" in js
        assert "async function previewCaptureMarkdownSourcePackAorDispatchAgentBusTaskClaimReadiness(" in js
        assert "async function claimCaptureMarkdownSourcePackAorDispatchAgentBusTask(" in js
        assert (
            "async function previewCaptureMarkdownSourcePackAorDispatchAgentBusClaimedTaskDryRunReadiness("
            in js
        )
        assert (
            "async function runCaptureMarkdownSourcePackAorDispatchAgentBusClaimedTaskDryRun("
            in js
        )
        assert (
            "async function runCaptureMarkdownSourcePackAorDispatchAgentBusClaimedTaskStatusLifecycle("
            in js
        )
        assert "function renderCaptureMarkdownSourcePackApprovalPreview(" in js
        assert "capture-markdown-source-pack-boundary" in js
        assert "Source Intelligence Core ingestion" in js
        assert "Canonical promotion" in js
        assert "function captureMarkdownReviewOptions(" in js
        assert "function renderCaptureMarkdownAttachmentPolicy(" in js
        assert "function captureMarkdownAttachmentDispositionOptions(" in js
        assert "async function updateCaptureMarkdownAttachmentDisposition(" in js
        assert "async function cleanupCaptureMarkdownAttachments(" in js
        assert "update_capture_to_markdown_attachment_disposition" in js
        assert "cleanup_capture_to_markdown_attachments" in js
        assert "capture-markdown-attachment-disposition-btn" in js
        assert "DELETE CAPTURE ATTACHMENTS" in js
        assert "function renderCaptureMarkdownSourceOptions(" in js
        assert "function openCapturePalette(" in js
        assert "function closeCapturePalette(" in js
        assert "function runCaptureMarkdownSourceAction(" in js
        assert "function openCaptureShortcutSettings(" in js
        assert "function setCaptureMarkdownFormValues(" in js
        assert "function installCaptureMarkdownProofBridge(" in js
        assert "window.__CHASEOS_CAPTURE_MARKDOWN_PROOF__" in js
        assert "window.__CHASEOS_CAPTURE_MARKDOWN_HANDLERS__" in js
        assert "function loadCaptureHotkeySettings(" in js
        assert "function loadCaptureLocalImageTextSettings(" in js
        assert "function _renderCaptureLocalImageTextSettingsSection(" in js
        assert "function _renderCaptureCollectorSettingsSection(" in js
        assert "function openCaptureCollectorSettings(" in js
        assert "async function captureCurrentScreenForMarkdown(" in js
        assert "async function captureDisplayRegionForMarkdown(" in js
        assert "async function captureActiveWindowForMarkdown(" in js
        assert "async function captureClipboardTextForMarkdown(" in js
        assert "async function pollAmbientClipboardForMarkdownOnce(" in js
        assert "async function toggleAmbientClipboardMonitorForMarkdown(" in js
        assert "async function captureSelectedTextForMarkdown(" in js
        assert "async function captureAccessibilityTreeForMarkdown(" in js
        assert "async function captureBrowserExtensionArtifactForMarkdown(" in js
        assert "input.addEventListener('keydown', event => {" in js
        assert "const chord = captureHotkeyEventChord(event);" in js
        assert "save_capture_hotkey_settings" in js
        assert "get_capture_hotkey_settings" in js
        assert "capture-global-hotkeys-enabled-input" in js
        assert "global_hotkeys_enabled" in js
        assert "save_capture_collector_settings" in js
        assert "get_capture_collector_settings" in js
        assert "capture_current_screen_for_markdown" in js
        assert "capture_display_region_for_markdown" in js
        assert "capture_active_window_for_markdown" in js
        assert "capture_clipboard_text_for_markdown" in js
        assert "poll_ambient_clipboard_for_markdown" in js
        assert "capture_selected_text_for_markdown" in js
        assert "capture_accessibility_tree_for_markdown" in js
        assert "capture_browser_extension_artifact_for_markdown" in js
        assert "capture-display-region-collector-enabled-input" in js
        assert "capture-active-window-collector-enabled-input" in js
        assert "capture-clipboard-collector-enabled-input" in js
        assert "capture-ambient-clipboard-monitor-enabled-input" in js
        assert "capture-selected-text-collector-enabled-input" in js
        assert "capture-accessibility-tree-collector-enabled-input" in js
        assert "capture-browser-artifact-collector-enabled-input" in js
        assert "capture-active-chaseos-browser-collector-enabled-input" in js
        assert "capture-chaseos-browser-page-collector-enabled-input" in js
        assert "capture-discord-artifact-collector-enabled-input" in js
        assert "capture-live-discord-command-collector-enabled-input" in js
        assert "run_clipboard_text_collector" in js
        assert "run_ambient_clipboard_monitor" in js
        assert "open_capture_palette" in js
        assert "run_selected_text_collector" in js
        assert "run_accessibility_tree_collector" in js
        assert "run_browser_extension_collector" in js
        assert "run_display_region_collector" in js
        assert "run_active_window_collector" in js
        assert "run_browser_artifact_collector" in js
        assert "run_active_browser_collector" in js
        assert "run_chaseos_browser_page_collector" in js
        assert "run_discord_artifact_collector" in js
        assert "run_live_discord_command_collector" in js
        assert "capture_browser_artifact_for_markdown" in js
        assert "capture-browser-extension-collector-enabled-input" in js
        assert "capture_active_chaseos_browser_for_markdown" in js
        assert "capture_chaseos_browser_page_for_markdown" in js
        assert "capture_discord_artifact_for_markdown" in js
        assert "capture_live_discord_command_for_markdown" in js
        assert "action.id === 'run_screen_capture_collector'" in js
        assert "action.id === 'run_display_region_collector'" in js
        assert "action.id === 'run_active_window_collector'" in js
        assert "action.id === 'run_clipboard_text_collector'" in js
        assert "action.id === 'run_ambient_clipboard_monitor'" in js
        assert "action.id === 'run_selected_text_collector'" in js
        assert "action.id === 'run_accessibility_tree_collector'" in js
        assert "action.id === 'run_browser_artifact_collector'" in js
        assert "action.id === 'run_browser_extension_collector'" in js
        assert "action.id === 'run_active_browser_collector'" in js
        assert "action.id === 'run_chaseos_browser_page_collector'" in js
        assert "action.id === 'run_discord_artifact_collector'" in js
        assert "action.id === 'run_live_discord_command_collector'" in js
        assert "captureCurrentScreenForMarkdown();" in js
        assert "captureDisplayRegionForMarkdown();" in js
        assert "captureActiveWindowForMarkdown();" in js
        assert "captureClipboardTextForMarkdown();" in js
        assert "toggleAmbientClipboardMonitorForMarkdown();" in js
        assert "capture-markdown-palette-action" in js
        assert "captureSelectedTextForMarkdown();" in js
        assert "captureAmbientClipboard: toggleAmbientClipboardMonitorForMarkdown" in js
        assert "captureSelectedText: captureSelectedTextForMarkdown" in js
        assert "captureAccessibilityTreeForMarkdown();" in js
        assert "captureAccessibilityTree: captureAccessibilityTreeForMarkdown" in js
        assert "captureBrowserArtifactForMarkdown();" in js
        assert "captureBrowserExtensionArtifactForMarkdown();" in js
        assert "captureActiveChaseosBrowserForMarkdown();" in js
        assert "captureChaseosBrowserPageForMarkdown();" in js
        assert "captureDiscordArtifactForMarkdown();" in js
        assert "save_capture_local_image_text_settings" in js
        assert "get_capture_local_image_text_settings" in js
        assert "function _initCaptureMarkdownPanel(" in js
        assert "if (id === 'capture-markdown') runPanelLoader(loadCaptureMarkdownPanel);" in js
        assert "_initCaptureMarkdownPanel();" in js
        assert "get_capture_to_markdown_panel" in js
        assert "preview_capture_to_markdown" in js
        assert "save_capture_to_markdown" in js
        assert "review_capture_to_markdown" in js
        assert "preview_capture_to_markdown_source_pack_approval" in js
        assert "execute_capture_to_markdown_source_pack_write" in js
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_readiness" in js
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_approval_design" in js
        assert "request_capture_to_markdown_source_pack_aor_dispatch_approval" in js
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness" in js
        assert "write_capture_to_markdown_source_pack_aor_dispatch_approval_decision" in js
        assert "consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision" in js
        assert "write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task" in js
        assert "preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness" in js
        assert "claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task" in js
        assert (
            "preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness"
            in js
        )
        assert (
            "execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run"
            in js
        )
        assert (
            "execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle"
            in js
        )
        assert (
            "preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness"
            in js
        )
        assert (
            "execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch"
            in js
        )
        assert "async function previewCaptureMarkdownSourcePackSicIngestionReadiness(" in js
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_readiness" in js
        assert "async function previewCaptureMarkdownSourcePackSicIngestionApprovalDesign(" in js
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_design" in js
        assert "async function previewCaptureMarkdownSourcePackSicIngestionApprovalRequest(" in js
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_request" in js
        assert "async function writeCaptureMarkdownSourcePackSicIngestionApprovalDecision(" in js
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision" in js
        assert "async function previewCaptureMarkdownSourcePackSicIngestionApprovalConsumption(" in js
        assert "async function consumeCaptureMarkdownSourcePackSicIngestionApprovalDecision(" in js
        assert "consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision" in js
        assert "async function previewCaptureMarkdownSourcePackSicIngestion(" in js
        assert "async function executeCaptureMarkdownSourcePackSicIngestion(" in js
        assert "ingest_capture_to_markdown_source_pack_sic_ingestion" in js
        assert "Ingest into Source Intelligence Core" in js
        assert "async function previewCaptureMarkdownSourcePackSicGraphIndexingReadiness(" in js
        assert "preview_capture_to_markdown_source_pack_sic_graph_indexing_readiness" in js
        assert "Graph Indexing Readiness Preview" in js
        assert "async function executeCaptureMarkdownSourcePackSicGraphIndexing(" in js
        assert "index_capture_to_markdown_source_pack_sic_graph_indexing" in js
        assert "Graph indexing executor preview ready" in js
        assert "Write Graph Snapshot" in js
        assert "Graph snapshot written" in js
        assert "async function previewCaptureMarkdownSourcePackCanonicalPromotionReadiness(" in js
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_readiness" in js
        assert "Canonical Promotion Readiness" in js
        assert "Canonical promotion readiness ready" in js
        assert "async function previewCaptureMarkdownSourcePackCanonicalPromotionApprovalDesign(" in js
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_design" in js
        assert "Canonical Approval Design" in js
        assert "Canonical approval design ready" in js
        assert "capture-markdown-source-pack-canonical-promotion-approval-design-btn" in js
        assert "async function previewCaptureMarkdownSourcePackCanonicalPromotionApprovalRequest(" in js
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_request" in js
        assert "Write Canonical Request" in js
        assert "Canonical request written" in js
        assert "capture-markdown-source-pack-canonical-promotion-approval-request-btn" in js
        assert "async function previewCaptureMarkdownSourcePackCanonicalPromotionDecisionReadiness(" in js
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness" in js
        assert "Canonical Decision Readiness" in js
        assert "Canonical decision readiness verified" in js
        assert "capture-markdown-source-pack-canonical-promotion-decision-readiness-btn" in js
        assert "async function writeCaptureMarkdownSourcePackCanonicalPromotionApprovalDecision(" in js
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision" in js
        assert "Approve Canonical Promotion" in js
        assert "Canonical approval decision written" in js
        assert "capture-markdown-source-pack-canonical-promotion-approval-decision-btn" in js
        assert "async function consumeCaptureMarkdownSourcePackCanonicalPromotionApprovalDecision(" in js
        assert "preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption" in js
        assert "Consume Canonical Decision" in js
        assert "Canonical approval decision consumed" in js
        assert "capture-markdown-source-pack-canonical-promotion-approval-consumption-btn" in js
        assert "async function promoteCaptureMarkdownSourcePackCanonicalPromotion(" in js
        assert "preview_capture_to_markdown_source_pack_canonical_promotion" in js
        assert "Promote Canonical Knowledge" in js
        assert "Canonical knowledge promoted" in js
        assert "capture-markdown-source-pack-canonical-promotion-btn" in js
        assert "write_canonical_knowledge_note" in js
        assert "write_canonical_knowledge_index" in js
        assert "approval_consumption_digest" in js
        assert "source_intelligence_core_ingestion_digest" in js
        assert "data-source-intelligence-core-ingestion-digest" in js
        assert "capture-markdown-source-pack-sic-ingestion-blocked" in js
        assert "Missing Source Intelligence Core ingestion data." in js
        assert "expected_agent_bus_task_digest" in js
        assert "write_consumption_marker" in js
        assert "write_approval_consumption" in js
        assert "write_task_marker" in js
        assert "write_agent_bus_task" in js
        assert "write_status_lifecycle_marker" in js
        assert "update_agent_bus_task_status" in js
        assert "write_status_lifecycle_artifact" in js
        assert "Consumption Preview" in js
        assert "Consume Decision" in js
        assert "Agent Bus Task Preview" in js
        assert "Write Agent Bus Task" in js
        assert "Task Claim Readiness" in js
        assert "Claim Task" in js
        assert "Claim executor" in js
        assert "Agent Orchestration Runtime Dry-Run Readiness" in js
        assert "Run Agent Orchestration Runtime Dry-Run" in js
        assert "Agent Orchestration Runtime dry-run OK" in js
        assert "Request Task Review" in js
        assert "Task Status Lifecycle" in js
        assert "Review requested" in js
        assert "Full Dispatch Readiness" in js
        assert "Run Full Dispatch" in js
        assert "Full dispatch complete" in js
        assert "Source Intelligence Core Readiness" in js
        assert "Source Intelligence Core readiness verified" in js
        assert "Source Intelligence Core Approval Design" in js
        assert "Source Intelligence Core approval design ready" in js
        assert "Write Source Intelligence Core Approval Request" in js
        assert "Source Intelligence Core Approval Request" in js
        assert "Source Intelligence Core approval request written" in js
        assert "Source Intelligence Core Decision Readiness" in js
        assert "Source Intelligence Core decision readiness verified" in js
        assert "preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision_consumption_readiness" in js
        assert "Approve Source Intelligence Core" in js
        assert "Reject Source Intelligence Core" in js
        assert "Source Intelligence Core Approval Decision" in js
        assert "Source Intelligence Core approval decision written" in js
        assert "Ready for approval consumption" in js
        assert "Source Intelligence Core Approval Consumption Preview" in js
        assert "Consume Source Intelligence Core Decision" in js
        assert "Source Intelligence Core approval decision consumed" in js
        assert "Ready for executor" in js
        assert "Future packet" in js
        assert "capture-markdown-source-pack-write-btn" in js
        assert "capture-markdown-source-pack-aor-readiness-btn" in js
        assert "capture-markdown-source-pack-aor-approval-design-btn" in js
        assert "capture-markdown-source-pack-aor-approval-request-btn" in js
        assert "capture-markdown-source-pack-aor-approval-consumption-readiness-btn" in js
        assert "capture-markdown-source-pack-aor-approval-decision-btn" in js
        assert "capture-markdown-source-pack-aor-approval-consume-preview-btn" in js
        assert "capture-markdown-source-pack-aor-approval-consume-btn" in js
        assert "capture-markdown-source-pack-agent-bus-task-preview-btn" in js
        assert "capture-markdown-source-pack-agent-bus-task-write-btn" in js
        assert "capture-markdown-source-pack-agent-bus-task-claim-readiness-btn" in js
        assert "capture-markdown-source-pack-agent-bus-task-claim-btn" in js
        assert "capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-btn" in js
        assert "capture-markdown-source-pack-agent-bus-aor-dry-run-btn" in js
        assert "capture-markdown-source-pack-agent-bus-status-lifecycle-btn" in js
        assert "capture-markdown-source-pack-agent-bus-status-lifecycle-statement" in js
        assert "capture-markdown-source-pack-agent-bus-full-dispatch-readiness-btn" in js
        assert "capture-markdown-source-pack-agent-bus-full-dispatch-btn" in js
        assert "capture-markdown-source-pack-agent-bus-full-dispatch-statement" in js
        assert "capture-markdown-source-pack-sic-readiness-btn" in js
        assert "capture-markdown-source-pack-sic-approval-design-btn" in js
        assert "capture-markdown-source-pack-sic-approval-request-btn" in js
        assert "capture-markdown-source-pack-sic-approval-decision-btn" in js
        assert "capture-markdown-source-pack-sic-approval-consumption-preview-btn" in js
        assert "capture-markdown-source-pack-sic-approval-consumption-btn" in js
        assert "capture-markdown-source-pack-sic-approval-consumption-statement" in js
        assert "capture-markdown-source-pack-canonical-promotion-approval-design-btn" in js

    def test_capture_markdown_product_language_hardens_status_rendering(self):
        js = self._js()
        expected_labels = {
            "'disabled_in_settings': 'Disabled in Settings'": "disabled collector status",
            "'available_click_to_capture': 'Available after click'": "click-only collector status",
            "'available_select_artifact': 'Available after selecting artifact'": "artifact collector status",
            "'fixture_proof_required': 'Fixture verification required'": "fixture proof status",
            "'blocked_secret_like': 'Blocked: secret-like text'": "secret-like block status",
            "'raw_ingested': 'Saved to raw quarantine'": "raw capture status",
            "'not_queued': 'Not queued'": "queue status",
            "'not_ingested': 'Not ingested'": "ingestion status",
        }
        for token, label in expected_labels.items():
            assert token in js, label

        assert "function captureMarkdownResponseError(" in js
        assert "function captureMarkdownBlockerText(" in js
        assert "msg.textContent = captureMarkdownBlockerText(data.blockers);" in js
        assert "<span>${escHtml(reviewStatusLabel)}</span>" in js
        assert "productLabel(item.review_status || 'pending-review', 'Pending review')" in js
        assert "const blockerLabels = captureMarkdownBlockerList(blockers);" in js
        assert "captureMarkdownResponseError(resp, data, 'Source-pack write blocked.')" in js
        assert "captureMarkdownOperatorText(item.detail || '')" in js
