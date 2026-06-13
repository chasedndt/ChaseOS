"""Tests for the read-only Studio personal context import planner."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.personal_context_import import (
    CANONICAL_KNOWLEDGE_INDEX_PATH,
    RAW_INTAKE_DIR,
    ROOT_KNOWLEDGE_SHIM_PATH,
    SURFACE_ID,
    build_personal_context_import_panel,
)


def _write(vault: Path, relative_path: str, text: str) -> None:
    path = vault / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_import_ready_vault(vault: Path) -> None:
    from runtime.studio.test_personal_operator_context_index import _seed_personal_context

    _seed_personal_context(vault)
    _write(vault, "01_PROJECTS/Projects-Hub.md", "# Projects Hub\n")
    _write(vault, "00_HOME/Personal-Domains/Personal-Domains-Index.md", "# Personal Domains Index\n")
    _write(vault, "06_AGENTS/Use-Case-Mode-Architecture.md", "# Workspace Mode Layer\n")


def test_personal_context_import_panel_declares_read_only_import_contract(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)

    panel = build_personal_context_import_panel(vault)

    assert panel["ok"] is True
    assert panel["surface"] == SURFACE_ID
    assert panel["implementation_status"] == "READY_FOR_MANUAL_TESTING / 100_PERCENT_IMPLEMENTED_FOR_LOCAL_MANUAL_TEST"
    assert panel["status"] == "ready_for_review_preview"
    assert panel["knowledge_index_resolution"]["canonical_index_path"] == CANONICAL_KNOWLEDGE_INDEX_PATH
    assert panel["knowledge_index_resolution"]["root_shim_path"] == ROOT_KNOWLEDGE_SHIM_PATH
    assert panel["knowledge_index_resolution"]["root_file_role"] == "routing_shim_not_canonical"
    assert panel["storage_policy"]["raw_context_dir"] == RAW_INTAKE_DIR
    assert panel["storage_policy"]["canonical_targets_require_review"] is True
    assert panel["runtime_context_contract"]["workspace_mode"] == "personal_os"
    assert panel["summary"]["approved_preview_writer_ready"] is True
    assert panel["summary"]["approved_preview_execution_proof_ready"] is True
    assert panel["summary"]["multi_instance_fixture_harness_ready"] is True
    assert panel["summary"]["runtime_consumption_readiness_ready"] is True
    assert panel["summary"]["canonical_promotion_approval_preview_ready"] is True
    assert panel["summary"]["canonical_promotion_approved_executor_ready"] is True
    assert panel["preview_writer"]["surface"] == "studio_personal_context_import_preview_writer"
    assert panel["preview_writer"]["queue_write_allowed_after_exact_digest"] is True
    assert panel["preview_writer"]["source_text_stored_in_approval_packet"] is False
    assert panel["preview_writer"]["raw_intake_writes_enabled"] is False
    assert panel["readiness"]["writer_built"] is False
    assert panel["readiness"]["approved_preview_writer_built"] is True
    assert panel["readiness"]["approved_preview_writer_stores_source_text"] is False
    assert panel["readiness"]["approved_preview_execution_proof_built"] is True
    assert panel["readiness"]["approved_preview_execution_proof_source_digest_gated"] is True
    assert panel["readiness"]["approved_preview_artifact_writes_enabled"] is True
    assert panel["readiness"]["multi_instance_test_harness_built"] is True
    assert panel["readiness"]["multi_instance_fixture_harness_temp_only"] is True
    assert panel["readiness"]["multi_instance_fixture_harness_source_text_returned"] is False
    assert panel["readiness"]["runtime_consumption_readiness_built"] is True
    assert panel["readiness"]["runtime_reference_packet_source_text_returned"] is False
    assert panel["readiness"]["raw_full_memory_injection_blocked"] is True
    assert panel["readiness"]["canonical_promotion_approval_preview_built"] is True
    assert panel["readiness"]["canonical_promotion_approval_queue_write_gated"] is True
    assert panel["readiness"]["canonical_promotion_executor_built"] is True
    assert panel["readiness"]["canonical_promotion_executor_approval_gated"] is True
    assert panel["readiness"]["canonical_promotion_writes_enabled_after_approval"] is True
    assert panel["readiness"]["approved_writer_built"] is False
    assert panel["readiness"]["live_import_writes_enabled"] is False
    assert panel["readiness"]["secret_storage_blocked"] is True
    assert panel["authority"]["read_only"] is True
    assert panel["authority"]["writes_vault"] is False
    assert panel["authority"]["writes_raw_intake"] is False
    assert panel["authority"]["writes_personal_map"] is False
    assert panel["authority"]["agent_bus_dispatch_allowed"] is False
    assert panel["authority"]["canonical_mutation_allowed"] is False
    assert panel["multi_instance_fixture_harness"]["surface"] == "studio_personal_context_import_multi_instance_fixture_harness"
    assert panel["multi_instance_fixture_harness"]["writes_live_vault"] is False
    assert panel["runtime_consumption_readiness"]["surface"] == "studio_personal_context_import_runtime_consumption_readiness"
    assert panel["runtime_consumption_readiness"]["context_refs_only"] is True
    assert panel["runtime_consumption_readiness"]["source_text_returned_in_payload"] is False
    assert panel["runtime_consumption_readiness"]["raw_full_memory_injection_allowed"] is False
    assert panel["runtime_consumption_readiness"]["agent_bus_dispatch_allowed"] is False
    assert panel["runtime_consumption_readiness"]["canonical_writes_enabled"] is False
    assert panel["canonical_promotion_approval_preview"]["surface"] == (
        "studio_personal_context_import_canonical_promotion_approval_preview"
    )
    assert panel["canonical_promotion_approval_preview"]["requires_exact_canonical_promotion_digest"] is True
    assert panel["canonical_promotion_approval_preview"]["canonical_executor_built"] is True
    assert panel["canonical_promotion_approval_preview"]["credential_reads_allowed"] is False
    assert panel["canonical_promotion_approved_executor"]["surface"] == (
        "studio_personal_context_import_canonical_promotion_approved_executor"
    )
    assert panel["canonical_promotion_approved_executor"]["requires_execute_flag"] is True
    assert panel["canonical_promotion_approved_executor"]["canonical_writes_enabled_after_approval"] is True
    assert panel["canonical_promotion_approved_executor"]["personal_map_apply_allowed"] is False


def test_personal_context_import_panel_exposes_entrypoints_pipeline_and_parent_child_plan(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)

    panel = build_personal_context_import_panel(vault)
    entrypoints = {item["id"]: item for item in panel["entrypoints"]}
    stages = {item["id"]: item for item in panel["pipeline_stages"]}
    families = {item["id"]: item for item in panel["node_families"]}

    assert {"settings", "context_import_panel", "dashboard", "approval_center"} <= set(entrypoints)
    assert stages["capture_raw_context"]["trust_posture"] == "TIER 4 RAW INPUT"
    assert stages["extract_nodes_and_edges"]["requires_operator_review"] is True
    assert stages["stage_personal_map_candidates"]["trust_posture"] == "CANDIDATE / NOT APPLIED"
    assert "fitness" in families["personal_domains"]["children"]
    assert "languages" in families["personal_domains"]["children"]
    assert "active projects" in families["project_operating_files"]["children"]
    assert "technical disciplines" in families["knowledge_domains"]["children"]
    assert "candidate review deck" in families["personal_map_candidates"]["children"]


def test_personal_context_import_panel_blocks_when_required_hubs_are_missing(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _write(vault, "SOUL.md", "# SOUL\n")

    panel = build_personal_context_import_panel(vault)

    assert panel["status"] == "blocked_missing_required_hubs"
    assert panel["summary"]["missing_required_hub_count"] > 0
    assert panel["missing_required_hubs"]
    assert panel["readiness"]["live_import_writes_enabled"] is False
    assert panel["authority"]["canonical_mutation_allowed"] is False
