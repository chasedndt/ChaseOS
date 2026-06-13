"""Tests for the Phase 10A0 Studio Acquisition Intake Cockpit foothold."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from io import StringIO
import json
import shutil
from unittest.mock import patch

import pytest

from runtime.acquisition.research_imports import (
    STRIKEZONE_LATEST_POINTER_PATH,
    STRIKEZONE_RESEARCH_DROP_FOLDERS,
    STRIKEZONE_RESEARCH_INBOX_FOLDERS,
    STRIKEZONE_RECOMMENDED_RESEARCH_SOURCE_CLASSES,
    initialize_research_repository_template,
)
from runtime.studio.acquisition_cockpit import (
    CockpitActionError,
    _source_pack_review_handoff,
    build_acquisition_cockpit_model,
    import_research_file,
    render_acquisition_cockpit_html,
    run_acquisition_cockpit_action,
)
from runtime.cli.main import main

_TMP_ROOT = Path("runtime/studio/_tmp_acquisition_cockpit")


def _make_empty_vault() -> Path:
    root = _TMP_ROOT / f"vault-{uuid4().hex}"
    for folder in STRIKEZONE_RESEARCH_DROP_FOLDERS.values():
        (root / folder).mkdir(parents=True, exist_ok=True)
    for folder in STRIKEZONE_RESEARCH_INBOX_FOLDERS.values():
        (root / folder).mkdir(parents=True, exist_ok=True)
    _initialize_repository_template(root)
    return root


def _make_research_vault() -> Path:
    root = _make_empty_vault()
    for source_class, folder in STRIKEZONE_RESEARCH_DROP_FOLDERS.items():
        (root / folder / f"{source_class}-sample.md").write_text(
            f"# {source_class} sample\n\nSynthetic operator import for {source_class}.",
            encoding="utf-8",
        )
    return root


def _initialize_repository_template(vault: Path) -> None:
    initialize_research_repository_template(vault, profile="strikezone", confirm_action=True)


def _write_sbp_manifest(vault: Path) -> None:
    source = Path("runtime/workflows/registry/sbp_strikezone_digest.yaml")
    target = vault / "runtime/workflows/registry/sbp_strikezone_digest.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _cleanup(root: Path) -> None:
    base = _TMP_ROOT.resolve()
    target = root.resolve()
    if target == base or base in target.parents:
        shutil.rmtree(target, ignore_errors=True)


def test_cockpit_init_repository_action_bootstraps_fresh_vault_template() -> None:
    vault = _TMP_ROOT / f"vault-{uuid4().hex}"
    try:
        model = build_acquisition_cockpit_model(vault, profile="strikezone")
        controls = {control["id"]: control for control in model["controls"]}
        steps = {step["id"]: step for step in model["rehearsal"]["steps"]}

        assert model["status"]["readiness"]["repository_template_ready"] is False
        assert controls["init_repository"]["enabled"] is True
        assert model["rehearsal"]["current_step_id"] == "init_repository"
        assert steps["init_repository"]["state"] == "current"
        assert steps["stage_research_files"]["state"] == "blocked"

        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="init-repository")

        result = run_acquisition_cockpit_action(vault, action="init-repository", confirm_action=True)
        assert result["action"]["id"] == "init_repository"
        assert result["action"]["write_action"] is True
        assert result["status"]["readiness"]["repository_template_ready"] is True
        assert result["rehearsal"]["current_step_id"] == "stage_research_files"
        assert (vault / "runtime/acquisition/manual/strikezone/repository-template.json").exists()
        assert not (vault / "runtime/acquisition/packs").exists()
        assert not (vault / "02_KNOWLEDGE").exists()
    finally:
        _cleanup(vault)


def test_cockpit_model_shows_empty_research_readiness_without_writes() -> None:
    vault = _make_empty_vault()
    try:
        model = build_acquisition_cockpit_model(vault, profile="strikezone")

        assert model["surface"] == "studio_acquisition_intake_cockpit"
        assert model["profile"] == "strikezone"
        assert model["writes"] == []
        assert model["authority"]["canonical_mutation_allowed"] is False
        assert model["authority"]["browser_scope"] == []
        assert model["authority"]["network_scope"] == []
        assert model["status"]["source_count"] == 0

        cards = {card["source_class"]: card for card in model["source_class_cards"]}
        for source_class in STRIKEZONE_RECOMMENDED_RESEARCH_SOURCE_CLASSES:
            assert cards[source_class]["recommended_for_pilot"] is True
            assert cards[source_class]["required_for_live_proof"] is False
            assert cards[source_class]["missing"] is False
            assert cards[source_class]["coverage_warning"] is True
            assert cards[source_class]["file_count"] == 0

        controls = {control["id"]: control for control in model["controls"]}
        assert controls["clear_active_intake"]["write_action"] is True
        assert controls["clear_active_intake"]["requires_confirmation"] is True
        assert controls["clear_active_intake"]["enabled"] is False
        assert controls["clear_active_intake"]["deletes_files"] is False
        assert controls["preview_read_only"]["write_action"] is False
        assert controls["preview_write"]["write_action"] is True
        assert controls["promote_reviewed_preview"]["requires_confirmation"] is True
        assert controls["verify_research_sbp"]["write_action"] is False
        assert controls["init_repository"]["requires_confirmation"] is True
        assert controls["init_repository"]["enabled"] is False
        assert controls["pulse_schedule_runner_status"]["write_action"] is False
        assert controls["pulse_schedule_runner_status"]["live_runner_built"] is False
        assert controls["pulse_schedule_live_runner_preview"]["write_action"] is False
        assert controls["pulse_schedule_live_runner_execute"]["write_action"] is True
        assert controls["pulse_schedule_live_runner_execute"]["requires_confirmation"] is True
        assert "07_LOGS/Pulse-Decks/native-schedule-run-queue/" in controls[
            "pulse_schedule_live_runner_execute"
        ]["writes_only"]
        assert "07_LOGS/Pulse-Decks/native-schedule-audit/" in controls[
            "pulse_schedule_live_runner_execute"
        ]["writes_only"]
        assert controls["pulse_schedule_runtime_dispatch_proof"]["write_action"] is False
        assert controls["pulse_schedule_runtime_dispatch_proof"]["execute_dispatch_exposed"] is False
        assert controls["pulse_schedule_runtime_dispatch_write_proof"]["write_action"] is True
        assert controls["pulse_schedule_runtime_dispatch_write_proof"]["requires_confirmation"] is True
        assert controls["pulse_schedule_runtime_dispatch_write_proof"]["execute_dispatch_exposed"] is False
        assert "07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/" in controls[
            "pulse_schedule_runtime_dispatch_write_proof"
        ]["writes_only"]
        assert controls["pulse_schedule_activation_gate"]["write_action"] is False
        assert controls["pulse_schedule_activation_request"]["write_action"] is True
        assert controls["pulse_schedule_activation_request"]["requires_confirmation"] is True
        assert "07_LOGS/Pulse-Decks/native-schedule-activation-requests/" in controls[
            "pulse_schedule_activation_request"
        ]["writes_only"]
        assert controls["pulse_schedule_run_queue_audit_proof"]["write_action"] is False
        assert controls["pulse_schedule_run_queue_audit_write_proof"]["write_action"] is True
        assert controls["pulse_schedule_run_queue_audit_write_proof"]["requires_confirmation"] is True
        assert "07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/" in controls[
            "pulse_schedule_run_queue_audit_write_proof"
        ]["writes_only"]
        assert controls["pulse_schedule_supervised_activation_execution_proof"]["write_action"] is False
        assert controls["pulse_schedule_supervised_activation_execution_proof"]["execute_activation_exposed"] is False
        assert controls["pulse_schedule_supervised_activation_execution_write_proof"]["write_action"] is True
        assert controls["pulse_schedule_supervised_activation_execution_write_proof"]["requires_confirmation"] is True
        assert controls["pulse_schedule_supervised_activation_execution_write_proof"]["execute_activation_exposed"] is False
        assert "07_LOGS/Pulse-Decks/native-schedule-activation-executions/" in controls[
            "pulse_schedule_supervised_activation_execution_write_proof"
        ]["writes_only"]
        assert controls["pulse_enqueue_preview"]["write_action"] is False
        assert controls["pulse_enqueue_approved"]["write_action"] is True
        assert controls["pulse_enqueue_approved"]["requires_confirmation"] is True
        assert "--operator-approved" in controls["pulse_enqueue_approved"]["required_evidence_flags"]
        assert "--operator-approval-ref" in controls[
            "pulse_schedule_activation_request"
        ]["required_evidence_ref_flags"]
        assert "--run-queue-scope-ref" in controls[
            "pulse_schedule_run_queue_audit_write_proof"
        ]["required_evidence_ref_flags"]

        pulse = model["pulse_roadmap_controls"]
        assert pulse["surface"] == "studio_pulse_roadmap_controls"
        assert pulse["roadmap_item"] == "10A0 - Studio Acquisition Intake Cockpit"
        assert pulse["authority"]["schedule_activation_allowed"] is False
        assert pulse["authority"]["schedule_manifest_write_allowed"] is False
        assert pulse["authority"]["activation_request_write_allowed_only_for_confirmed_action"] is True
        assert pulse["authority"]["live_schedule_runner_built"] is False
        assert pulse["authority"]["run_queue_write_allowed"] is False
        assert pulse["authority"]["run_queue_write_allowed_only_for_confirmed_live_runner"] is True
        assert pulse["authority"]["real_audit_event_write_allowed"] is False
        assert pulse["authority"]["real_audit_event_write_allowed_only_for_confirmed_live_runner"] is True
        assert pulse["authority"]["runtime_dispatch_proof_built"] is True
        assert pulse["authority"]["runtime_dispatch_proof_ready_count"] == 0
        assert pulse["authority"]["runtime_dispatch_proof_write_allowed_only_for_confirmed_action"] is True
        assert pulse["authority"]["run_queue_audit_proof_write_allowed_only_for_confirmed_action"] is True
        assert pulse["authority"]["schedule_activation_execution_allowed"] is False
        assert pulse["authority"]["supervised_activation_execute_action_exposed"] is False
        assert pulse["authority"]["activation_execution_proof_write_allowed_only_for_confirmed_action"] is True
        assert pulse["authority"]["candidate_apply_allowed"] is False
        assert pulse["schedule_activation_gate"]["request_action_id"] == "pulse-schedule-activation-request"
        assert (
            pulse["schedule_runtime_dispatch_proof"]["write_action_id"]
            == "pulse-schedule-runtime-dispatch-write-proof"
        )
        assert (
            pulse["schedule_run_queue_audit_proof"]["write_action_id"]
            == "pulse-schedule-run-queue-audit-write-proof"
        )
        assert (
            pulse["schedule_supervised_activation_execution"]["write_action_id"]
            == "pulse-schedule-supervised-activation-execution-write-proof"
        )
        assert pulse["agent_bus_enqueue"]["approved_action_id"] == "pulse-enqueue-approved"

        rehearsal = model["rehearsal"]
        steps = {step["id"]: step for step in rehearsal["steps"]}
        assert rehearsal["surface"] == "strikezone_research_rehearsal_ladder"
        assert rehearsal["current_step_id"] == "stage_research_files"
        assert steps["init_repository"]["state"] == "complete"
        assert steps["stage_research_files"]["state"] == "current"
        assert steps["import_inbox"]["state"] == "blocked"
        assert steps["preview_write"]["state"] == "blocked"
        assert steps["verify_sbp_consumption"]["write_action"] is False

        manual = model["manual_test_readiness"]
        assert manual["surface"] == "studio_acquisition_manual_test_readiness"
        assert manual["development_ready_for_manual_real_file_test"] is True
        assert manual["manual_input_ready"] is False
        assert manual["remaining_development_passes"] == []
        assert manual["current_rehearsal_step_id"] == "stage_research_files"
        assert manual["required_source_classes"] == []
        assert manual["source_coverage_model"] == "flexible"
        assert manual["minimum_viable_source_count"] == 1
        assert manual["coverage_warnings"]
        assert [step["id"] for step in manual["manual_test_sequence"]] == [
            "init_repository",
            "stage_research_files",
            "import_inbox",
            "preview_write",
            "reviewed_promotion",
            "verify_sbp_consumption",
        ]
        assert any("No operator-selected research files" in blocker for blocker in manual["manual_blockers"])
    finally:
        _cleanup(vault)


def test_cockpit_import_copies_operator_file_into_declared_source_class_folder() -> None:
    vault = _make_empty_vault()
    source = vault / "operator-downloads" / "perplexity-market-map.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Perplexity Market Map\n\nSynthetic operator import.", encoding="utf-8")
    try:
        result = import_research_file(vault, source_class="perplexity_digest", source_path=source)

        imported = vault / result["destination_path"]
        raw = vault / result["raw_destination_path"]
        dashboard_ledger = vault / result["dashboard_ledger_path"]
        daily_note = vault / result["daily_note_path"]
        daily_index = vault / result["daily_index_path"]
        assert result["ok"] is True
        assert result["source_class"] == "perplexity_digest"
        assert result["dashboard_ready"] is True
        assert result["normalization_method"] == "text_file_read"
        assert result["standardized_artifact_path"] == result["destination_path"]
        assert result["raw_destination_path"] in result["writes"]
        assert result["destination_path"] in result["writes"]
        assert result["dashboard_ledger_path"] in result["writes"]
        assert result["daily_note_path"] in result["writes"]
        assert result["daily_index_path"] in result["writes"]
        assert imported.exists()
        imported_text = imported.read_text(encoding="utf-8")
        assert imported_text.startswith("---")
        assert "type: acquisition-intake-artifact" in imported_text
        assert "dashboard_ready: true" in imported_text
        assert "artifact_role: trading_brief" in imported_text
        assert "## Source Summary" in imported_text
        assert "## Normalized Source Content" not in imported_text
        assert "# Perplexity Market Map" in imported_text
        assert "Synthetic operator import." in imported_text
        assert raw.exists()
        assert raw.read_text(encoding="utf-8").startswith("# Perplexity Market Map")
        assert dashboard_ledger.exists()
        assert '"dashboard_ready": true' in dashboard_ledger.read_text(encoding="utf-8")
        assert daily_note.exists()
        assert "Development / Research Intake" in daily_note.read_text(encoding="utf-8")
        assert daily_index.exists()
        assert "StrikeZone research intake" in daily_index.read_text(encoding="utf-8")
        assert imported.relative_to(vault).as_posix().startswith(
            STRIKEZONE_RESEARCH_DROP_FOLDERS["perplexity_digest"]
        )

        model = build_acquisition_cockpit_model(vault, profile="strikezone")
        cards = {card["source_class"]: card for card in model["source_class_cards"]}
        assert cards["perplexity_digest"]["file_count"] == 1
        assert cards["perplexity_digest"]["missing"] is False
    finally:
        _cleanup(vault)


def test_cockpit_import_rejects_unknown_source_class_and_unsafe_suffix() -> None:
    vault = _make_empty_vault()
    bad = vault / "operator-downloads" / "secret.exe"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("not a research note", encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="unknown source_class"):
            import_research_file(vault, source_class="wallet_export", source_path=bad)

        with pytest.raises(ValueError, match="unsupported research file suffix"):
            import_research_file(vault, source_class="perplexity_digest", source_path=bad)

        assert not any((vault / folder / "secret.exe").exists() for folder in STRIKEZONE_RESEARCH_DROP_FOLDERS.values())
    finally:
        _cleanup(vault)


def test_cockpit_import_inbox_action_imports_trading_brief_and_consumes_staged_file() -> None:
    vault = _make_empty_vault()
    _initialize_repository_template(vault)
    staged = vault / STRIKEZONE_RESEARCH_INBOX_FOLDERS["perplexity_digest"] / "perplexity-digest.md"
    staged.write_text("# Perplexity Digest\n\nOperator-saved digest.", encoding="utf-8")
    try:
        model = build_acquisition_cockpit_model(vault, profile="strikezone")
        controls = {control["id"]: control for control in model["controls"]}
        cards = {card["source_class"]: card for card in model["source_class_cards"]}
        steps = {step["id"]: step for step in model["rehearsal"]["steps"]}
        assert controls["import_inbox"]["enabled"] is True
        assert model["rehearsal"]["current_step_id"] == "import_inbox"
        assert steps["stage_research_files"]["state"] == "complete"
        assert steps["import_inbox"]["state"] == "current"
        assert cards["perplexity_digest"]["inbox_candidate_count"] == 1
        assert cards["perplexity_digest"]["inbox_readiness_label"] == "needs_review"
        assert cards["perplexity_digest"]["inbox_candidates"][0]["display_name"] == "Perplexity Digest"

        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="import-inbox")

        result = run_acquisition_cockpit_action(vault, action="import-inbox", confirm_action=True)
        assert result["action"]["id"] == "import_inbox"
        assert result["action"]["write_action"] is True
        assert any(path.startswith(STRIKEZONE_RESEARCH_DROP_FOLDERS["perplexity_digest"]) for path in result["writes"])
        imported_files = list((vault / STRIKEZONE_RESEARCH_DROP_FOLDERS["perplexity_digest"]).glob("*.md"))
        assert len(imported_files) == 1
        imported_text = imported_files[0].read_text(encoding="utf-8")
        assert "type: acquisition-intake-artifact" in imported_text
        assert "artifact_role: trading_brief" in imported_text
        assert "## Source Summary" in imported_text
        assert "## Normalized Source Content" not in imported_text
        assert not staged.exists()
        consumed = result["action"]["result"]["imported"][0]["consumed_inbox_path"]
        assert consumed.startswith("runtime/acquisition/manual/strikezone/_archive/imported-inbox/")
        assert (vault / consumed).exists()
        assert result["action"]["result"]["imported"][0]["trading_brief_path"] == imported_files[0].relative_to(vault).as_posix()
        assert result["action"]["result"]["imported"][0]["transform_method"] == "local_trading_brief_extraction_v1"
        assert result["action"]["result"]["imported"][0]["source_claims_unverified"] is True
        assert (vault / "runtime/acquisition/manual/strikezone/_raw/perplexity_digest/perplexity-digest.md").exists()
        assert (vault / "runtime/acquisition/state/strikezone-research-dashboard-artifacts.jsonl").exists()
        assert any(path.endswith("07_LOGS/Daily/Daily-Index.md") for path in result["writes"])
    finally:
        _cleanup(vault)


def test_cockpit_import_staged_file_consumes_only_selected_file_and_is_idempotent() -> None:
    vault = _make_empty_vault()
    first = vault / STRIKEZONE_RESEARCH_INBOX_FOLDERS["perplexity_digest"] / "first.md"
    second = vault / STRIKEZONE_RESEARCH_INBOX_FOLDERS["perplexity_digest"] / "second.md"
    first.write_text("# First Digest\n\nHighest probability scenario: long above 5610.", encoding="utf-8")
    second.write_text("# Second Digest\n\nSecond staged file should remain active.", encoding="utf-8")
    try:
        result = run_acquisition_cockpit_action(
            vault,
            action="import-staged-file",
            source_class="perplexity_digest",
            source_path=first.relative_to(vault).as_posix(),
            confirm_action=True,
        )

        assert result["action"]["id"] == "import_staged_file"
        assert result["action"]["result"]["imported_count"] == 1
        assert result["action"]["result"]["skipped_count"] == 0
        assert not first.exists()
        assert second.exists()
        imported_files = list((vault / STRIKEZONE_RESEARCH_DROP_FOLDERS["perplexity_digest"]).glob("*.md"))
        assert len(imported_files) == 1
        consumed = result["action"]["result"]["imported"][0]["consumed_inbox_path"]
        assert (vault / consumed).exists()
        assert "## Actionable Trading Knowledge" in imported_files[0].read_text(encoding="utf-8")

        duplicate = vault / STRIKEZONE_RESEARCH_INBOX_FOLDERS["perplexity_digest"] / "first-again.md"
        duplicate.write_text("# First Digest\n\nHighest probability scenario: long above 5610.", encoding="utf-8")
        second_result = run_acquisition_cockpit_action(
            vault,
            action="import-staged-file",
            source_class="perplexity_digest",
            source_path=duplicate.relative_to(vault).as_posix(),
            confirm_action=True,
        )

        assert second_result["action"]["result"]["imported_count"] == 0
        assert second_result["action"]["result"]["skipped_count"] == 1
        assert second_result["action"]["result"]["skipped"][0]["reason"] == "already_imported"
        assert not duplicate.exists()
        assert second.exists()
        assert len(list((vault / STRIKEZONE_RESEARCH_DROP_FOLDERS["perplexity_digest"]).glob("*.md"))) == 1
    finally:
        _cleanup(vault)


def test_cockpit_open_local_path_allows_generated_artifact_and_rejects_unsafe_path() -> None:
    vault = _make_empty_vault()
    artifact = vault / STRIKEZONE_RESEARCH_DROP_FOLDERS["perplexity_digest"] / "brief.md"
    artifact.write_text("# Brief\n", encoding="utf-8")
    try:
        with patch("runtime.studio.acquisition_cockpit.shutil.which", return_value="antigravity.cmd"), patch(
            "runtime.studio.acquisition_cockpit.subprocess.Popen"
        ) as popen:
            result = run_acquisition_cockpit_action(
                vault,
                action="open-local-path",
                open_target="antigravity",
                open_path=artifact.relative_to(vault).as_posix(),
            )

        assert result["action"]["id"] == "open_local_path"
        assert result["action"]["write_action"] is False
        assert result["action"]["result"]["path"] == artifact.relative_to(vault).as_posix()
        assert popen.call_args.args[0][0] == "antigravity.cmd"
        assert popen.call_args.args[0][1] == str(artifact.resolve())

        with pytest.raises(CockpitActionError, match="outside the allowed"):
            run_acquisition_cockpit_action(
                vault,
                action="open-local-path",
                open_target="folder",
                open_path="README.md",
            )
    finally:
        _cleanup(vault)


def test_cockpit_clear_active_intake_archives_files_without_deleting() -> None:
    vault = _make_empty_vault()
    staged = vault / STRIKEZONE_RESEARCH_INBOX_FOLDERS["perplexity_digest"] / "perplexity-digest.md"
    imported = vault / STRIKEZONE_RESEARCH_DROP_FOLDERS["perplexity_digest"] / "perplexity-digest.md"
    staged.write_text("# Perplexity Digest\n\nOperator-staged copy.", encoding="utf-8")
    imported.write_text("# Perplexity Digest\n\nOperator-imported copy.", encoding="utf-8")
    try:
        model = build_acquisition_cockpit_model(vault, profile="strikezone")
        controls = {control["id"]: control for control in model["controls"]}
        assert controls["clear_active_intake"]["enabled"] is True

        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="clear-active-intake")

        result = run_acquisition_cockpit_action(
            vault,
            action="clear-active-intake",
            confirm_action=True,
        )

        assert result["action"]["id"] == "clear_active_intake"
        assert result["action"]["write_action"] is True
        clear_result = result["action"]["result"]
        assert clear_result["archived_count"] == 2
        assert clear_result["archived_source_count"] == 1
        assert clear_result["archived_staged_count"] == 1
        assert clear_result["deletes_files"] is False
        assert clear_result["clears_preview_packs"] is False
        assert clear_result["clears_latest_pointer"] is False
        assert not staged.exists()
        assert not imported.exists()
        assert all((vault / item["archive_path"]).exists() for item in clear_result["archived"])
        assert (vault / "runtime/acquisition/state/strikezone-active-intake-clears.jsonl").exists()

        refreshed = build_acquisition_cockpit_model(vault, profile="strikezone")
        assert refreshed["status"]["source_count"] == 0
        assert refreshed["status"]["inbox_candidate_count"] == 0
    finally:
        _cleanup(vault)


def test_cockpit_model_reports_metadata_ready_inbox_counts() -> None:
    vault = _make_empty_vault()
    staged = vault / STRIKEZONE_RESEARCH_INBOX_FOLDERS["research_export"] / "notebooklm.md"
    staged.write_text(
        """---
title: NotebookLM Rotation Synthesis
source_url: https://notebooklm.google.com/notebook/rotation
source_event_at: 2026-04-30T08:00:00Z
captured_at: 2026-04-30T08:05:00Z
source_platform: NotebookLM
---
# NotebookLM Rotation Synthesis

Operator-reviewed synthesis.
""",
        encoding="utf-8",
    )
    try:
        model = build_acquisition_cockpit_model(vault, profile="strikezone")
        cards = {card["source_class"]: card for card in model["source_class_cards"]}
        card = cards["research_export"]

        assert model["status"]["inbox_readiness_summary"]["metadata_ready_count"] == 1
        assert card["inbox_candidate_count"] == 1
        assert card["inbox_metadata_ready_count"] == 1
        assert card["inbox_warning_count"] == 0
        assert card["inbox_readiness_label"] == "metadata_ready"
        assert card["inbox_candidates"][0]["readiness_label"] == "metadata_ready"
        planned = card["inbox_candidates"][0]["planned_artifact"]
        assert planned["artifact_date"] == "2026-04-30"
        assert planned["planned_standardized_filename"].startswith(
            "2026-04-30-strikezone-research-export-notebooklm-rotation"
        )
        assert planned["planned_standardized_artifact_path"].startswith(
            "runtime/acquisition/manual/strikezone/research_export/"
        )
    finally:
        _cleanup(vault)


def test_source_pack_review_handoff_explains_preview_review_and_blocked_backend_paths() -> None:
    status = {
        "preview_candidate_count": 1,
        "latest_preview_candidate": {
            "pack_root": "runtime/acquisition/packs/2026-05-11-strikezone-research-import-preview",
            "briefing_ready_input_set_path": "runtime/acquisition/packs/2026-05-11-strikezone-research-import-preview/briefing_ready_input_set.json",
            "normalized_source_pack_path": "runtime/acquisition/packs/2026-05-11-strikezone-research-import-preview/normalized_source_pack.json",
            "source_packet_paths": [
                "runtime/acquisition/packs/2026-05-11-strikezone-research-import-preview/source_packet_001.json"
            ],
            "source_packet_count": 1,
            "source_classes": {"perplexity_digest": 1},
            "valid_for_reviewed_promotion": True,
            "warnings": [],
        },
        "latest_pointer_path": "runtime/acquisition/packs/strikezone-latest.json",
        "latest_pointer": {
            "briefing_ready_input_set_path": "runtime/acquisition/packs/2026-05-11-strikezone-research-import-preview/briefing_ready_input_set.json",
            "reviewed_by": "operator",
            "promoted_at": "2026-05-11T12:00:00Z",
            "canonical_mutation_allowed": False,
        },
        "readiness": {
            "reviewed_preview_promoted": True,
            "current_pointer_consumable_by_sbp": True,
            "default_verify_ready": False,
        },
        "default_verify_error": "latest pointer not verified by default SBP run",
    }
    controls = [
        {
            "id": "promote_reviewed_preview",
            "studio_action": "promote-reviewed-preview",
            "studio_command": "chaseos studio acquisition-cockpit --action promote-reviewed-preview --confirm-action --json",
            "enabled": True,
            "write_action": True,
            "requires_confirmation": True,
            "writes_only": ["runtime/acquisition/packs/strikezone-latest.json"],
        },
        {
            "id": "verify_research_sbp",
            "studio_action": "verify-research-sbp",
            "studio_command": "chaseos studio acquisition-cockpit --action verify-research-sbp --json",
            "enabled": True,
            "write_action": False,
            "requires_confirmation": False,
        },
    ]

    handoff = _source_pack_review_handoff("strikezone", status, controls)

    assert handoff["surface"] == "studio_acquisition_source_pack_review_handoff"
    assert handoff["source_pack_preview"]["candidate_count"] == 1
    assert handoff["source_pack_preview"]["latest_pack_root"].endswith("strikezone-research-import-preview")
    assert handoff["evidence"]["source_packet_paths"] == status["latest_preview_candidate"]["source_packet_paths"]
    assert handoff["review_state"]["reviewed_preview_promoted"] is True
    assert handoff["review_state"]["reviewed_by"] == "operator"
    assert handoff["operator_handoff_paths"]["promoted_latest_pointer"] == "runtime/acquisition/packs/strikezone-latest.json"
    assert handoff["operator_handoff_actions"]["promote_reviewed_preview"]["requires_confirmation"] is True
    assert handoff["authority"]["canonical_mutation_allowed"] is False
    assert handoff["blocked_backend_dependencies"][0] == {
        "missing_contract": "default reviewed-preview SBP verification is not complete",
        "affected_phase10_surface": "Acquisition Cockpit reviewed-promotion visibility and SBP handoff readiness",
        "lower_phase_owner_surface": "Phase 9 acquisition/SBP adapter: runtime/acquisition/research_imports.verify_research_preview_sbp_consumption",
        "minimum_proof_needed": "Run the governed verify-research-sbp action against the promoted reviewed preview pointer and observe default_verify_ready=true.",
        "blocked_action_reason": "latest pointer not verified by default SBP run",
    }


def test_cockpit_html_renders_controls_and_boundaries() -> None:
    vault = _make_empty_vault()
    try:
        model = build_acquisition_cockpit_model(vault, profile="strikezone")
        html = render_acquisition_cockpit_html(model)

        assert "Research Intake Cockpit" in html
        assert "Authority boundary" in html
        assert "Source classes" in html
        assert "Staged inbox" in html
        assert "Governed controls" in html
        assert "Pulse schedule runner status" in html
        assert "Pulse schedule runtime dispatch proof" in html
        assert "pulse-schedule-runtime-dispatch-write-proof" in html
        assert "Pulse schedule activation gate" in html
        assert "pulse-schedule-activation-request" in html
        assert "Pulse schedule run-queue/audit proof" in html
        assert "pulse-schedule-run-queue-audit-write-proof" in html
        assert "Pulse schedule supervised activation execution proof" in html
        assert "pulse-schedule-supervised-activation-execution-write-proof" in html
        assert "Operator-approved Pulse review enqueue" in html
        assert "pulse-enqueue-approved" in html
        assert "Workflow rehearsal" in html
        assert "Manual test readiness" in html
        assert "Source-pack review handoff" in html
        assert "Blocked backend dependencies" in html
        assert "valid runtime-local preview source pack is unavailable" in html
        assert "Development cleanup" in html
        assert "No development blockers remain." in html
        assert "Stage research files" in html
        assert "Current pointer" in html
        assert "Next actions" in html
        assert "perplexity_digest" in html
        assert "studio acquisition-cockpit --profile strikezone --action preview-read-only" in html
        assert "studio acquisition-cockpit --profile strikezone --action promote-reviewed-preview" in html
        assert "Canonical mutation" in html
        assert "blocked" in html
        assert "Browser authority" in html
        assert "none" in html
        assert "Add at least one declared research source file first." in html
        assert "<script" not in html.lower()
    finally:
        _cleanup(vault)


def test_cockpit_html_escapes_dynamic_action_result_content() -> None:
    vault = _make_empty_vault()
    try:
        model = build_acquisition_cockpit_model(vault, profile="strikezone")
        model["action"] = {
            "id": "preview_read_only",
            "status": "complete",
            "write_action": False,
            "requires_confirmation": False,
            "writes": ["runtime/acquisition/packs/<preview>/briefing_ready_input_set.json"],
            "result": {"note": "<script>alert('x')</script>"},
        }
        html = render_acquisition_cockpit_html(model)

        assert "Action result JSON" in html
        assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html
        assert "<script" not in html.lower()
    finally:
        _cleanup(vault)


class _FakePulsePipelineResult:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def to_dict(self) -> dict[str, object]:
        return dict(self.payload)


class _FakeScheduleGateResult:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def to_dict(self) -> dict[str, object]:
        return dict(self.payload)


def _schedule_gate_payload(*, writes: list[str] | None = None) -> dict[str, object]:
    return {
        "generated_at": "2026-05-06T10:00:00Z",
        "gate_status": "blocked_missing_activation_evidence",
        "schedule_ids": ["chaseos_pulse_daily"],
        "schedule_count": 1,
        "ready_schedule_count": 0,
        "enabled_schedule_count": 0,
        "evidence_slots": [],
        "missing_evidence_slots": ["operator_approval_ref"],
        "activation_targets": [],
        "activation_command_preview": [],
        "write_requested": bool(writes),
        "write_executed": bool(writes),
        "writes": writes or [],
        "activation_request": None,
        "read_only": not bool(writes),
        "writes_artifacts": bool(writes),
        "schedule_activation_allowed": False,
        "schedule_manifest_write_allowed": False,
        "schedule_daemon_started": False,
        "canonical_writeback_allowed": False,
        "mutates_canonical_state": False,
        "allowed_write_root": "07_LOGS/Pulse-Decks/native-schedule-activation-requests/",
    }


def _run_queue_audit_payload(*, writes: list[str] | None = None) -> dict[str, object]:
    return {
        "generated_at": "2026-05-06T10:00:00Z",
        "proof_status": "blocked_activation_gate_not_ready",
        "gate_status": "blocked_missing_activation_evidence",
        "schedule_ids": ["chaseos_pulse_daily"],
        "schedule_count": 1,
        "proof_queue_entry_count": 0,
        "proof_audit_event_count": 0,
        "missing_evidence_slots": ["operator_approval_ref"],
        "run_queue_entries": [],
        "audit_events": [],
        "write_requested": bool(writes),
        "write_executed": bool(writes),
        "writes": writes or [],
        "read_only": not bool(writes),
        "writes_artifacts": bool(writes),
        "real_run_queue_written": False,
        "real_audit_event_written": False,
        "schedule_activation_allowed": False,
        "schedule_manifest_write_allowed": False,
        "schedule_daemon_started": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_execution_allowed": False,
        "canonical_writeback_allowed": False,
        "allowed_write_root": "07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/",
    }


def _runtime_dispatch_payload(*, writes: list[str] | None = None) -> dict[str, object]:
    return {
        "generated_at": "2026-05-07T10:00:00Z",
        "dispatch_status": "blocked_no_queued_native_schedule_runs",
        "queue_file_path": "07_LOGS/Pulse-Decks/native-schedule-run-queue/native-schedule-run-queue.jsonl",
        "queue_file_exists": False,
        "queue_entry_count": 0,
        "pending_entry_count": 0,
        "invalid_queue_line_count": 0,
        "invalid_queue_lines": [],
        "dispatch_target_count": 0,
        "ready_dispatch_target_count": 0,
        "blocked_dispatch_target_count": 0,
        "missing_workflow_count": 0,
        "write_requested": bool(writes),
        "write_executed": bool(writes),
        "dispatch_targets": [],
        "proof_events": [],
        "writes": writes or [],
        "read_only": not bool(writes),
        "writes_artifacts": bool(writes),
        "proof_artifact_write_executed": bool(writes),
        "execute_dispatch_action_exposed": False,
        "schedule_daemon_started": False,
        "run_queue_status_write_executed": False,
        "runtime_dispatch_allowed": False,
        "runtime_dispatch_started": False,
        "workflow_execution_allowed": False,
        "workflow_execution_started": False,
        "agent_bus_task_write_allowed": False,
        "provider_or_connector_call_allowed": False,
        "external_scheduler_install_allowed": False,
        "approval_granted": False,
        "canonical_writeback_allowed": False,
        "mutates_canonical_state": False,
        "rd_workbook_update_allowed": False,
        "allowed_write_root": "07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/",
    }


def _supervised_activation_execution_payload(*, writes: list[str] | None = None) -> dict[str, object]:
    return {
        "generated_at": "2026-05-06T10:00:00Z",
        "execution_status": "blocked_activation_gate_not_ready",
        "gate_status": "blocked_missing_activation_evidence",
        "run_queue_proof_status": "blocked_activation_gate_not_ready",
        "schedule_ids": ["chaseos_pulse_daily"],
        "schedule_count": 1,
        "missing_evidence_slots": ["operator_approval_ref"],
        "execute_requested": False,
        "write_proof_requested": bool(writes),
        "write_executed": bool(writes),
        "writes": writes or [],
        "manifest_patch_count": 0,
        "manifest_patches": [],
        "writes_artifacts": bool(writes),
        "schedule_manifest_write_executed": False,
        "schedule_activation_executed": False,
        "schedule_daemon_started": False,
        "real_run_queue_written": False,
        "real_audit_event_written": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_execution_allowed": False,
        "provider_or_connector_call_allowed": False,
        "canonical_writeback_allowed": False,
        "allowed_write_root": "07_LOGS/Pulse-Decks/native-schedule-activation-executions/",
    }


def _live_runner_payload(*, writes: list[str] | None = None) -> dict[str, object]:
    write_executed = bool(writes)
    return {
        "generated_at": "2026-05-07T10:00:00Z",
        "runner_status": "live_run_queue_audit_written" if write_executed else "ready_for_live_run_queue_write",
        "schedule_ids": ["chaseos_pulse_daily"],
        "schedule_count": 1,
        "active_schedule_count": 1,
        "due_schedule_count": 1,
        "duplicate_count": 0,
        "queue_entry_count": 1,
        "audit_event_count": 1,
        "execute_requested": write_executed,
        "force_due": True,
        "write_executed": write_executed,
        "targets": [],
        "run_queue_entries": [],
        "audit_events": [],
        "missing_evidence_slots": [],
        "writes": writes or [],
        "writes_artifacts": write_executed,
        "run_queue_write_executed": write_executed,
        "audit_event_write_executed": write_executed,
        "schedule_daemon_started": False,
        "schedule_manifest_write_executed": False,
        "schedule_activation_executed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_execution_allowed": False,
        "provider_or_connector_call_allowed": False,
        "canonical_writeback_allowed": False,
        "run_queue_root": "07_LOGS/Pulse-Decks/native-schedule-run-queue/",
        "audit_root": "07_LOGS/Pulse-Decks/native-schedule-audit/",
        "run_record_root": "07_LOGS/Pulse-Decks/native-schedule-runs/",
    }


def test_cockpit_pulse_schedule_live_runner_preview_runs_without_writes() -> None:
    vault = _make_empty_vault()
    try:
        with patch(
            "runtime.pulse.native_schedule_live_runner.build_pulse_native_schedule_live_runner",
            return_value=_FakeScheduleGateResult(_live_runner_payload()),
        ) as runner:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-live-runner-preview",
                pulse_schedule_ids=["chaseos_pulse_daily"],
                pulse_force_due=True,
            )

        assert result["action"]["id"] == "pulse_schedule_live_runner_preview"
        assert result["action"]["write_action"] is False
        assert result["writes"] == []
        assert result["action"]["result"]["run_queue_write_executed"] is False
        assert result["action"]["result"]["audit_event_write_executed"] is False
        call = next(call for call in runner.call_args_list if "schedule_ids" in call.kwargs)
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily",)
        assert call.kwargs["force_due"] is True
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_live_runner_execute_requires_confirmation() -> None:
    vault = _make_empty_vault()
    try:
        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="pulse-schedule-live-runner-execute")
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_live_runner_execute_writes_queue_audit_records() -> None:
    vault = _make_empty_vault()
    writes = [
        "07_LOGS/Pulse-Decks/native-schedule-run-queue/native-schedule-run-queue.jsonl",
        "07_LOGS/Pulse-Decks/native-schedule-audit/2026-05-07-native-schedule-audit.jsonl",
        "07_LOGS/Pulse-Decks/native-schedule-runs/2026-05-07-live-runner-test.json",
    ]
    try:
        with patch(
            "runtime.pulse.native_schedule_live_runner.write_pulse_native_schedule_live_runner_records",
            return_value=_FakeScheduleGateResult(_live_runner_payload(writes=writes)),
        ) as runner:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-live-runner-execute",
                confirm_action=True,
                pulse_schedule_ids="chaseos_pulse_daily, hermes_runtime_pulse",
                pulse_force_due=True,
            )

        assert result["action"]["id"] == "pulse_schedule_live_runner_execute"
        assert result["action"]["write_action"] is True
        assert result["writes"] == writes
        assert result["action"]["result"]["run_queue_write_executed"] is True
        assert result["action"]["result"]["audit_event_write_executed"] is True
        assert result["action"]["result"]["runtime_dispatch_allowed"] is False
        assert result["action"]["result"]["workflow_execution_allowed"] is False
        call = runner.call_args_list[-1]
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily", "hermes_runtime_pulse")
        assert call.kwargs["force_due"] is True
        assert call.kwargs["execute"] is True
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_runtime_dispatch_proof_runs_without_writes() -> None:
    vault = _make_empty_vault()
    try:
        with patch(
            "runtime.pulse.native_schedule_runtime_dispatch_proof.build_pulse_native_schedule_runtime_dispatch_proof",
            return_value=_FakeScheduleGateResult(_runtime_dispatch_payload()),
        ) as proof:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-runtime-dispatch-proof",
                pulse_schedule_ids=["chaseos_pulse_daily"],
            )

        assert result["action"]["id"] == "pulse_schedule_runtime_dispatch_proof"
        assert result["action"]["write_action"] is False
        assert result["writes"] == []
        assert result["action"]["result"]["runtime_dispatch_allowed"] is False
        assert result["action"]["result"]["runtime_dispatch_started"] is False
        assert result["action"]["result"]["workflow_execution_allowed"] is False
        assert result["action"]["result"]["workflow_execution_started"] is False
        call = next(call for call in proof.call_args_list if "schedule_ids" in call.kwargs)
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily",)
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_runtime_dispatch_write_proof_requires_confirmation() -> None:
    vault = _make_empty_vault()
    try:
        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="pulse-schedule-runtime-dispatch-write-proof")
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_runtime_dispatch_write_proof_writes_artifact_only() -> None:
    vault = _make_empty_vault()
    write_path = "07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/test.json"
    try:
        with patch(
            "runtime.pulse.native_schedule_runtime_dispatch_proof.write_pulse_native_schedule_runtime_dispatch_proof",
            return_value=_FakeScheduleGateResult(_runtime_dispatch_payload(writes=[write_path])),
        ) as writer:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-runtime-dispatch-write-proof",
                confirm_action=True,
                pulse_schedule_ids="chaseos_pulse_daily, hermes_runtime_pulse",
            )

        assert result["action"]["id"] == "pulse_schedule_runtime_dispatch_write_proof"
        assert result["action"]["write_action"] is True
        assert result["writes"] == [write_path]
        assert result["action"]["result"]["proof_artifact_write_executed"] is True
        assert result["action"]["result"]["run_queue_status_write_executed"] is False
        assert result["action"]["result"]["runtime_dispatch_allowed"] is False
        assert result["action"]["result"]["runtime_dispatch_started"] is False
        assert result["action"]["result"]["workflow_execution_allowed"] is False
        assert result["action"]["result"]["workflow_execution_started"] is False
        call = writer.call_args_list[-1]
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily", "hermes_runtime_pulse")
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_activation_gate_runs_without_writes() -> None:
    vault = _make_empty_vault()
    try:
        with patch(
            "runtime.pulse.native_schedule_activation_gate.build_pulse_native_schedule_activation_gate",
            return_value=_FakeScheduleGateResult(_schedule_gate_payload()),
        ) as gate:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-activation-gate",
                pulse_schedule_ids=["chaseos_pulse_daily"],
                operator_approval_ref="operator-approval-2026-05-06",
            )

        assert result["action"]["id"] == "pulse_schedule_activation_gate"
        assert result["action"]["write_action"] is False
        assert result["writes"] == []
        assert result["action"]["result"]["schedule_activation_allowed"] is False
        call = next(call for call in gate.call_args_list if "schedule_ids" in call.kwargs)
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily",)
        assert call.kwargs["evidence_refs"]["operator_approval_ref"] == "operator-approval-2026-05-06"
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_activation_request_requires_confirmation() -> None:
    vault = _make_empty_vault()
    try:
        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="pulse-schedule-activation-request")
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_activation_request_writes_pending_artifact() -> None:
    vault = _make_empty_vault()
    write_path = "07_LOGS/Pulse-Decks/native-schedule-activation-requests/test.json"
    try:
        with patch(
            "runtime.pulse.native_schedule_activation_gate.write_pulse_native_schedule_activation_request",
            return_value=_FakeScheduleGateResult(_schedule_gate_payload(writes=[write_path])),
        ) as writer:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-activation-request",
                confirm_action=True,
                pulse_schedule_ids="chaseos_pulse_daily, hermes_runtime_pulse",
                operator_approval_ref="operator-approval-2026-05-06",
                permission_envelope_ref="permission-envelope-2026-05-06",
                run_queue_scope_ref="run-queue-scope-2026-05-06",
                audit_identity_ref="audit-identity-2026-05-06",
                runtime_adapter_scope_ref="runtime-adapter-scope-2026-05-06",
                rollback_plan_ref="rollback-plan-2026-05-06",
                external_scheduler_denial_ref="external-scheduler-denial-2026-05-06",
                canonical_writeback_denial_ref="canonical-writeback-denial-2026-05-06",
            )

        assert result["action"]["id"] == "pulse_schedule_activation_request"
        assert result["action"]["write_action"] is True
        assert result["writes"] == [write_path]
        call = writer.call_args_list[-1]
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily", "hermes_runtime_pulse")
        assert call.kwargs["evidence_refs"]["canonical_writeback_denial_ref"] == (
            "canonical-writeback-denial-2026-05-06"
        )
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_run_queue_audit_proof_runs_without_writes() -> None:
    vault = _make_empty_vault()
    try:
        with patch(
            "runtime.pulse.native_schedule_run_queue_audit_proof.build_pulse_native_schedule_run_queue_audit_proof",
            return_value=_FakeScheduleGateResult(_run_queue_audit_payload()),
        ) as proof:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-run-queue-audit-proof",
                pulse_schedule_ids=["chaseos_pulse_daily"],
                operator_approval_ref="operator-approval-2026-05-06",
                run_queue_scope_ref="run-queue-scope-2026-05-06",
            )

        assert result["action"]["id"] == "pulse_schedule_run_queue_audit_proof"
        assert result["action"]["write_action"] is False
        assert result["writes"] == []
        assert result["action"]["result"]["real_run_queue_written"] is False
        assert result["action"]["result"]["real_audit_event_written"] is False
        call = next(call for call in proof.call_args_list if "schedule_ids" in call.kwargs)
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily",)
        assert call.kwargs["evidence_refs"]["run_queue_scope_ref"] == "run-queue-scope-2026-05-06"
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_run_queue_audit_write_proof_requires_confirmation() -> None:
    vault = _make_empty_vault()
    try:
        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="pulse-schedule-run-queue-audit-write-proof")
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_run_queue_audit_write_proof_writes_artifact() -> None:
    vault = _make_empty_vault()
    write_path = "07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/test.json"
    try:
        with patch(
            "runtime.pulse.native_schedule_run_queue_audit_proof.write_pulse_native_schedule_run_queue_audit_proof",
            return_value=_FakeScheduleGateResult(_run_queue_audit_payload(writes=[write_path])),
        ) as writer:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-run-queue-audit-write-proof",
                confirm_action=True,
                pulse_schedule_ids="chaseos_pulse_daily, hermes_runtime_pulse",
                operator_approval_ref="operator-approval-2026-05-06",
                permission_envelope_ref="permission-envelope-2026-05-06",
                run_queue_scope_ref="run-queue-scope-2026-05-06",
                audit_identity_ref="audit-identity-2026-05-06",
                runtime_adapter_scope_ref="runtime-adapter-scope-2026-05-06",
                rollback_plan_ref="rollback-plan-2026-05-06",
                external_scheduler_denial_ref="external-scheduler-denial-2026-05-06",
                canonical_writeback_denial_ref="canonical-writeback-denial-2026-05-06",
            )

        assert result["action"]["id"] == "pulse_schedule_run_queue_audit_write_proof"
        assert result["action"]["write_action"] is True
        assert result["writes"] == [write_path]
        call = writer.call_args_list[-1]
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily", "hermes_runtime_pulse")
        assert call.kwargs["evidence_refs"]["audit_identity_ref"] == "audit-identity-2026-05-06"
        assert result["action"]["result"]["real_run_queue_written"] is False
        assert result["action"]["result"]["real_audit_event_written"] is False
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_supervised_activation_execution_proof_runs_without_writes() -> None:
    vault = _make_empty_vault()
    try:
        with patch(
            (
                "runtime.pulse.native_schedule_supervised_activation_execution."
                "build_pulse_native_schedule_supervised_activation_execution"
            ),
            return_value=_FakeScheduleGateResult(_supervised_activation_execution_payload()),
        ) as proof:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-supervised-activation-execution-proof",
                pulse_schedule_ids=["chaseos_pulse_daily"],
                operator_approval_ref="operator-approval-2026-05-07",
                runtime_adapter_scope_ref="runtime-adapter-scope-2026-05-07",
            )

        assert result["action"]["id"] == "pulse_schedule_supervised_activation_execution_proof"
        assert result["action"]["write_action"] is False
        assert result["writes"] == []
        assert result["action"]["result"]["execute_requested"] is False
        assert result["action"]["result"]["schedule_manifest_write_executed"] is False
        assert result["action"]["result"]["schedule_activation_executed"] is False
        call = next(call for call in proof.call_args_list if "schedule_ids" in call.kwargs)
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily",)
        assert call.kwargs["evidence_refs"]["runtime_adapter_scope_ref"] == (
            "runtime-adapter-scope-2026-05-07"
        )
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_supervised_activation_execution_write_proof_requires_confirmation() -> None:
    vault = _make_empty_vault()
    try:
        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-supervised-activation-execution-write-proof",
            )
    finally:
        _cleanup(vault)


def test_cockpit_pulse_schedule_supervised_activation_execution_write_proof_writes_artifact_only() -> None:
    vault = _make_empty_vault()
    write_path = "07_LOGS/Pulse-Decks/native-schedule-activation-executions/test.json"
    try:
        with patch(
            (
                "runtime.pulse.native_schedule_supervised_activation_execution."
                "write_pulse_native_schedule_supervised_activation_execution_proof"
            ),
            return_value=_FakeScheduleGateResult(_supervised_activation_execution_payload(writes=[write_path])),
        ) as writer:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-schedule-supervised-activation-execution-write-proof",
                confirm_action=True,
                pulse_schedule_ids="chaseos_pulse_daily, hermes_runtime_pulse",
                operator_approval_ref="operator-approval-2026-05-07",
                permission_envelope_ref="permission-envelope-2026-05-07",
                run_queue_scope_ref="run-queue-scope-2026-05-07",
                audit_identity_ref="audit-identity-2026-05-07",
                runtime_adapter_scope_ref="runtime-adapter-scope-2026-05-07",
                rollback_plan_ref="rollback-plan-2026-05-07",
                external_scheduler_denial_ref="external-scheduler-denial-2026-05-07",
                canonical_writeback_denial_ref="canonical-writeback-denial-2026-05-07",
            )

        assert result["action"]["id"] == "pulse_schedule_supervised_activation_execution_write_proof"
        assert result["action"]["write_action"] is True
        assert result["writes"] == [write_path]
        assert result["action"]["result"]["execute_requested"] is False
        assert result["action"]["result"]["schedule_manifest_write_executed"] is False
        assert result["action"]["result"]["schedule_activation_executed"] is False
        call = writer.call_args_list[-1]
        assert call.kwargs["schedule_ids"] == ("chaseos_pulse_daily", "hermes_runtime_pulse")
        assert call.kwargs["execute_activation"] is False
        assert call.kwargs["evidence_refs"]["rollback_plan_ref"] == "rollback-plan-2026-05-07"
    finally:
        _cleanup(vault)


def test_cockpit_pulse_enqueue_preview_runs_pipeline_without_writes() -> None:
    vault = _make_empty_vault()
    payload = {
        "run_at": "2026-05-06T10:00:00Z",
        "pipeline_status": "dry_run",
        "dry_run": True,
        "operator_approved": False,
        "gate_policy_defined": False,
        "external_sender_allowance_present": False,
        "duplicate_work_fingerprint_reviewed": False,
        "plan_preflight_count": 1,
        "enqueued_count": 0,
        "blocked_count": 0,
        "duplicate_count": 0,
        "bus_error_count": 0,
        "enqueue_results": [],
        "dry_run_previews": [{"candidate_id": "candidate-001", "recipient": "OpenClaw"}],
        "candidate_apply_allowed": False,
        "canonical_writeback_allowed": False,
        "mutates_canonical_state": False,
        "second_datastore_write_allowed": False,
        "provider_or_connector_call_allowed": False,
        "schedule_activation_allowed": False,
        "review_response_ingest_allowed": False,
    }
    try:
        with patch(
            "runtime.pulse.pipeline_runner.run_pulse_enqueue_pipeline",
            return_value=_FakePulsePipelineResult(payload),
        ) as pipeline:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-enqueue-preview",
                pulse_recipient="OpenClaw",
                pulse_candidate_kinds=["feedback"],
                pulse_limit=2,
            )

        assert result["action"]["id"] == "pulse_enqueue_preview"
        assert result["action"]["write_action"] is False
        assert result["writes"] == []
        assert result["action"]["result"]["dry_run"] is True
        assert any(call.kwargs["dry_run"] is True for call in pipeline.call_args_list)
        assert any(call.kwargs["default_recipient"] == "OpenClaw" for call in pipeline.call_args_list)
    finally:
        _cleanup(vault)


def test_cockpit_pulse_approved_enqueue_requires_confirmation_and_evidence() -> None:
    vault = _make_empty_vault()
    try:
        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="pulse-enqueue-approved")

        with pytest.raises(CockpitActionError, match="--operator-approved"):
            run_acquisition_cockpit_action(
                vault,
                action="pulse-enqueue-approved",
                confirm_action=True,
            )
    finally:
        _cleanup(vault)


def test_cockpit_pulse_approved_enqueue_runs_live_pipeline_with_evidence() -> None:
    vault = _make_empty_vault()
    live_payload = {
        "run_at": "2026-05-06T10:00:00Z",
        "pipeline_status": "live",
        "dry_run": False,
        "operator_approved": True,
        "gate_policy_defined": True,
        "external_sender_allowance_present": True,
        "duplicate_work_fingerprint_reviewed": True,
        "plan_preflight_count": 1,
        "enqueued_count": 1,
        "blocked_count": 0,
        "duplicate_count": 0,
        "bus_error_count": 0,
        "enqueue_results": [{"candidate_id": "candidate-001", "result_status": "enqueued"}],
        "dry_run_previews": [],
        "candidate_apply_allowed": False,
        "canonical_writeback_allowed": False,
        "mutates_canonical_state": False,
        "second_datastore_write_allowed": False,
        "provider_or_connector_call_allowed": False,
        "schedule_activation_allowed": False,
        "review_response_ingest_allowed": False,
    }
    try:
        with patch(
            "runtime.pulse.pipeline_runner.run_pulse_enqueue_pipeline",
            return_value=_FakePulsePipelineResult(live_payload),
        ) as pipeline:
            result = run_acquisition_cockpit_action(
                vault,
                action="pulse-enqueue-approved",
                confirm_action=True,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                pulse_recipient="Hermes",
                pulse_limit=1,
            )

        assert result["action"]["id"] == "pulse_enqueue_approved"
        assert result["action"]["write_action"] is True
        assert result["action"]["result"]["dry_run"] is False
        assert "07_LOGS/Pulse-Decks/agent-bus-approval-requests/" in result["writes"]
        assert "07_LOGS/Pulse-Decks/agent-bus-enqueue-results/" in result["writes"]
        assert any(call.kwargs["dry_run"] is False for call in pipeline.call_args_list)
        live_call = next(call for call in pipeline.call_args_list if call.kwargs["dry_run"] is False)
        assert live_call.kwargs["operator_approved"] is True
        assert live_call.kwargs["gate_policy_defined"] is True
        assert live_call.kwargs["external_sender_allowance_present"] is True
        assert live_call.kwargs["duplicate_work_fingerprint_reviewed"] is True
    finally:
        _cleanup(vault)


def test_cockpit_action_wrappers_run_preview_promotion_and_sbp_verification() -> None:
    vault = _make_research_vault()
    try:
        _write_sbp_manifest(vault)

        preview = run_acquisition_cockpit_action(vault, action="preview-read-only")
        assert preview["action"]["id"] == "preview_read_only"
        assert preview["action"]["write_action"] is False
        assert preview["writes"] == []

        with pytest.raises(CockpitActionError, match="requires --confirm-action"):
            run_acquisition_cockpit_action(vault, action="preview-write")

        preview_write = run_acquisition_cockpit_action(
            vault,
            action="preview-write",
            confirm_action=True,
        )
        assert preview_write["action"]["id"] == "preview_write"
        assert preview_write["action"]["write_action"] is True
        assert any(path.endswith("briefing_ready_input_set.json") for path in preview_write["writes"])
        briefing_input = preview_write["action"]["result"]["briefing_ready_input_set_path"]

        refreshed = build_acquisition_cockpit_model(vault, profile="strikezone")
        assert refreshed["status"]["preview_candidate_count"] == 1
        assert refreshed["status"]["latest_preview_candidate"]["briefing_ready_input_set_path"] == briefing_input
        controls = {control["id"]: control for control in refreshed["controls"]}
        steps = {step["id"]: step for step in refreshed["rehearsal"]["steps"]}
        assert controls["promote_reviewed_preview"]["enabled"] is True
        assert controls["promote_reviewed_preview"]["briefing_input"] == briefing_input
        assert refreshed["rehearsal"]["current_step_id"] == "reviewed_promotion"
        assert steps["preview_write"]["state"] == "complete"
        assert steps["reviewed_promotion"]["state"] == "current"

        promotion = run_acquisition_cockpit_action(
            vault,
            action="promote-reviewed-preview",
            briefing_input=briefing_input,
            reviewed=True,
            confirm_action=True,
        )
        assert promotion["action"]["id"] == "promote_reviewed_preview"
        assert promotion["writes"] == [STRIKEZONE_LATEST_POINTER_PATH]
        promoted_steps = {step["id"]: step for step in promotion["rehearsal"]["steps"]}
        assert promotion["rehearsal"]["current_step_id"] is None
        assert promotion["rehearsal"]["complete"] is True
        assert promoted_steps["reviewed_promotion"]["state"] == "complete"
        assert promoted_steps["verify_sbp_consumption"]["state"] == "complete"

        verification = run_acquisition_cockpit_action(vault, action="verify-research-sbp")
        assert verification["action"]["id"] == "verify_research_sbp"
        assert verification["action"]["write_action"] is False
        assert verification["action"]["result"]["consumed_by_sbp_adapter"] is True
        assert verification["writes"] == []
    finally:
        _cleanup(vault)


def test_canonical_cli_exposes_studio_acquisition_cockpit_json() -> None:
    vault = _make_empty_vault()
    try:
        out = StringIO()
        with patch("sys.stdout", out):
            rc = main([
                "studio",
                "acquisition-cockpit",
                "--profile",
                "strikezone",
                "--vault-root",
                str(vault),
                "--json",
            ])

        assert rc == 0
        envelope = json.loads(out.getvalue())
        assert envelope["ok"] is True
        assert envelope["action"] == "studio.acquisition-cockpit"
        assert envelope["result"]["surface"] == "studio_acquisition_intake_cockpit"
        assert envelope["result"]["writes"] == []
    finally:
        _cleanup(vault)


def test_canonical_cli_imports_source_file_with_explicit_confirmation() -> None:
    vault = _make_empty_vault()
    source = vault / "operator-downloads" / "youtube-summary.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# YouTube Summary\n\nSynthetic local file.", encoding="utf-8")
    try:
        out = StringIO()
        with patch("sys.stdout", out):
            rc = main([
                "studio",
                "acquisition-cockpit",
                "--action",
                "import-file",
                "--source-class",
                "youtube_summary",
                "--source-file",
                str(source),
                "--confirm-action",
                "--vault-root",
                str(vault),
                "--json",
            ])

        assert rc == 0
        envelope = json.loads(out.getvalue())
        result = envelope["result"]
        assert envelope["ok"] is True
        assert result["action"]["id"] == "import_file"
        assert result["action"]["write_action"] is True
        assert result["writes"] == result["action"]["writes"]
        assert any(path.startswith("runtime/acquisition/manual/strikezone/_raw/youtube_summary/") for path in result["writes"])
        assert any(path.startswith(STRIKEZONE_RESEARCH_DROP_FOLDERS["youtube_summary"]) for path in result["writes"])
        assert any(path == "runtime/acquisition/state/strikezone-research-dashboard-artifacts.jsonl" for path in result["writes"])
        assert "07_LOGS/Daily/Daily-Index.md" in result["writes"]
        assert all((vault / path).exists() for path in result["writes"])
    finally:
        _cleanup(vault)


def test_canonical_cli_rejects_cockpit_write_action_without_confirmation() -> None:
    vault = _make_empty_vault()
    source = vault / "operator-downloads" / "perplexity-note.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Perplexity Note\n\nSynthetic local file.", encoding="utf-8")
    try:
        out = StringIO()
        with patch("sys.stdout", out):
            rc = main([
                "studio",
                "acquisition-cockpit",
                "--action",
                "import-file",
                "--source-class",
                "perplexity_digest",
                "--source-file",
                str(source),
                "--vault-root",
                str(vault),
                "--json",
            ])

        assert rc == 1
        envelope = json.loads(out.getvalue())
        assert envelope["ok"] is False
        assert "requires --confirm-action" in envelope["errors"][0]
        assert not any((vault / folder / source.name).exists() for folder in STRIKEZONE_RESEARCH_DROP_FOLDERS.values())
    finally:
        _cleanup(vault)


def test_canonical_cli_writes_static_cockpit_html_only_when_output_path_is_explicit() -> None:
    vault = _make_empty_vault()
    output = vault / "runtime/studio/out/acquisition-cockpit.html"
    try:
        out = StringIO()
        with patch("sys.stdout", out):
            rc = main([
                "studio",
                "acquisition-cockpit",
                "--profile",
                "strikezone",
                "--vault-root",
                str(vault),
                "--output-html",
                str(output),
                "--json",
            ])

        assert rc == 0
        envelope = json.loads(out.getvalue())
        assert envelope["result"]["html_output_path"] == str(output.resolve())
        assert envelope["result"]["writes"] == [str(output.resolve())]
        assert output.exists()
        assert "Research Intake Cockpit" in output.read_text(encoding="utf-8")
    finally:
        _cleanup(vault)
