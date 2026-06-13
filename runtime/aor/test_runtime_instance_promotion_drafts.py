"""
test_runtime_instance_promotion_drafts.py — ChaseOS Phase 9

Focused validation for the draft runtime-instance promotion substrate.

Covers:
  - OpenClaw draft promotion manifest loads and stays draft-only
  - Hermes draft promotion manifest loads and stays draft-only
  - Both draft promotion role cards load and preserve their hard boundaries
  - Shared promotion-review task type resolves from the live task router
  - Manifest writeback targets stay within the matching role-card write scope

Running:
  .venv/Scripts/python.exe -m pytest runtime/aor/test_runtime_instance_promotion_drafts.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.promotion_readiness import (
    assess_hermes_promotion_activation_readiness,
    assess_openclaw_promotion_activation_readiness,
    collect_hermes_preactivation_failure_signals,
    collect_openclaw_preactivation_failure_signals,
)
from runtime.aor.registry import load_manifest
from runtime.aor.role_cards import load_card
from runtime.aor.task_router import classify


def test_openclaw_promotion_manifest_loads_as_draft() -> None:
    manifest = load_manifest("openclaw_promote_note", vault_root=_VAULT_ROOT)

    assert manifest is not None
    assert manifest["id"] == "openclaw_promote_note"
    assert manifest["status"] == "draft"
    assert manifest["task_type"] == "promotion-review"
    assert manifest["role_card"] == "openclaw-promotion-review"
    assert manifest["runtime_adapter"] == "openclaw"
    assert manifest["permission_ceiling"] == "gated_canonical_write"


def test_hermes_promotion_manifest_loads_as_draft() -> None:
    manifest = load_manifest("hermes_promote_note", vault_root=_VAULT_ROOT)

    assert manifest is not None
    assert manifest["id"] == "hermes_promote_note"
    assert manifest["status"] == "draft"
    assert manifest["task_type"] == "promotion-review"
    assert manifest["role_card"] == "hermes-promotion-review"
    assert manifest["runtime_adapter"] == "hermes"
    assert manifest["permission_ceiling"] == "gated_canonical_write"


def test_openclaw_promotion_role_card_preserves_bounded_non_autonomous_posture() -> None:
    card = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)

    assert card is not None
    assert card["id"] == "openclaw-promotion-review"
    assert "write_bounded_canonical_note" in card["allowed_actions"]
    assert "write_promotion_record" in card["allowed_actions"]
    assert "autonomous_promotion" in card["forbidden_actions"]
    assert "ambient_vault_write" in card["forbidden_actions"]
    assert "02_KNOWLEDGE/" in card["write_scope"]
    assert "07_LOGS/Promotion-Records/" in card["write_scope"]


def test_hermes_promotion_role_card_preserves_control_plane_boundary() -> None:
    card = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert card is not None
    assert card["id"] == "hermes-promotion-review"
    assert "read_control_plane_approval_record" in card["allowed_actions"]
    assert "write_promotion_record" in card["allowed_actions"]
    assert "direct_discord_driven_write" in card["forbidden_actions"]
    assert "autonomous_promotion" in card["forbidden_actions"]
    assert "02_KNOWLEDGE/" in card["write_scope"]
    assert "07_LOGS/Promotion-Records/" in card["write_scope"]


def test_promotion_review_task_type_is_live_as_draft_substrate_only() -> None:
    task_type = classify("promotion-review", vault_root=_VAULT_ROOT)

    assert task_type["id"] == "promotion-review"
    assert task_type["runtime_class"] == "gated-write"
    assert task_type["permission_ceiling"] == "gated_canonical_write"
    assert "runtime instance lacks an explicitly activated promotion path" in task_type["escalation_trigger"]


def test_runtime_instance_pair_level_validation_now_asserts_promotion_review_task_type_cross_link_alignment() -> None:
    task_type = classify("promotion-review", vault_root=_VAULT_ROOT)

    assert task_type["id"] == "promotion-review"
    assert task_type["runtime_class"] == "gated-write"
    assert task_type["permission_ceiling"] == "gated_canonical_write"

    required_reads = set(task_type["required_reads"])
    optional_reads = set(task_type["optional_reads"])
    permission_set = set(task_type["permission_set"])
    escalation_trigger = set(task_type["escalation_trigger"])

    for required_read in (
        "02_KNOWLEDGE/",
        "07_LOGS/Agent-Activity/",
        "07_LOGS/Build-Logs/",
    ):
        assert required_read in required_reads

    for optional_read in (
        "runtime/schemas/",
        "runtime/workflows/registry/",
        "06_AGENTS/role-cards/",
    ):
        assert optional_read in optional_reads

    for permission in (
        "read_vault",
        "write_logs",
        "write_bounded_canonical",
        "write_bounded_index_update",
    ):
        assert permission in permission_set

    for escalation in (
        "promotion approval missing or invalid",
        "provenance minimums fail",
        "target outside declared canonical scope",
        "attempted write outside declared writeback_targets",
        "runtime instance lacks an explicitly activated promotion path",
    ):
        assert escalation in escalation_trigger

    assert "explicit approval" in task_type["writeback_expectations"]
    assert "centralized provenance minimum checks" in task_type["writeback_expectations"]


def test_promotion_manifests_writeback_targets_fit_within_role_card_scope() -> None:
    pairs = [
        ("openclaw_promote_note", "openclaw-promotion-review"),
        ("hermes_promote_note", "hermes-promotion-review"),
    ]

    for workflow_id, card_id in pairs:
        manifest = load_manifest(workflow_id, vault_root=_VAULT_ROOT)
        card = load_card(card_id, vault_root=_VAULT_ROOT)

        assert manifest is not None
        assert card is not None
        assert set(manifest["writeback_targets"]).issubset(set(card["write_scope"]))


def test_openclaw_draft_contract_now_declares_promotion_record_scope() -> None:
    manifest = load_manifest("openclaw_promote_note", vault_root=_VAULT_ROOT)
    card = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)

    assert manifest is not None
    assert card is not None
    assert "promotion_record_path" in manifest["outputs"]
    assert "07_LOGS/Promotion-Records/" in manifest["writeback_targets"]
    assert "write_promotion_record" in card["allowed_actions"]
    assert "07_LOGS/Promotion-Records/" in card["write_scope"]


def test_hermes_draft_contract_now_declares_promotion_record_scope() -> None:
    manifest = load_manifest("hermes_promote_note", vault_root=_VAULT_ROOT)
    card = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert manifest is not None
    assert card is not None
    assert "promotion_record_path" in manifest["outputs"]
    assert "07_LOGS/Promotion-Records/" in manifest["writeback_targets"]
    assert "write_promotion_record" in card["allowed_actions"]
    assert "07_LOGS/Promotion-Records/" in card["write_scope"]


def test_runtime_instance_draft_contract_keeps_promotion_records_distinct_from_audit_and_build_logs() -> None:
    pairs = [
        ("openclaw_promote_note", "openclaw-promotion-review"),
        ("hermes_promote_note", "hermes-promotion-review"),
    ]

    for workflow_id, card_id in pairs:
        manifest = load_manifest(workflow_id, vault_root=_VAULT_ROOT)
        card = load_card(card_id, vault_root=_VAULT_ROOT)

        assert manifest is not None
        assert card is not None
        assert "promotion_record_path" in manifest["outputs"]
        assert "audit_record_path" in manifest["outputs"]
        assert "build_log_path" in manifest["outputs"]
        assert "07_LOGS/Promotion-Records/" in manifest["writeback_targets"]
        assert "07_LOGS/Agent-Activity/" in manifest["writeback_targets"]
        assert "07_LOGS/Build-Logs/" in manifest["writeback_targets"]
        assert "write_promotion_record" in card["allowed_actions"]
        assert "write_agent_activity_log" in card["allowed_actions"]
        assert "write_build_log" in card["allowed_actions"]
        assert "07_LOGS/Promotion-Records/" in card["write_scope"]
        assert "07_LOGS/Agent-Activity/" in card["write_scope"]
        assert "07_LOGS/Build-Logs/" in card["write_scope"]
        assert "audit record is written regardless of approval outcome" in card["runtime_expectations"]


def test_hermes_pair_level_validation_now_asserts_control_plane_and_direct_authority_guards() -> None:
    signals = collect_hermes_preactivation_failure_signals(vault_root=_VAULT_ROOT)

    assert signals["approval_linkage_declared"] is True
    assert signals["control_plane_linkage_declared"] is True
    assert signals["direct_authority_guard_declared"] is True
    assert signals["blocking_gaps"] == []


def test_runtime_instance_pair_level_validation_now_asserts_canonical_helper_signal_dimensions() -> None:
    openclaw = collect_openclaw_preactivation_failure_signals(vault_root=_VAULT_ROOT)
    hermes = collect_hermes_preactivation_failure_signals(vault_root=_VAULT_ROOT)

    assert openclaw["operator_approval_ref_required"] is True
    assert openclaw["approval_linkage_declared"] is True
    assert openclaw["target_scope_failure_declared"] is True
    assert openclaw["audit_survival_declared"] is True
    assert openclaw["blocking_gaps"] == []

    assert hermes["operator_approval_ref_required"] is True
    assert hermes["control_plane_request_ref_required"] is True
    assert hermes["approval_linkage_declared"] is True
    assert hermes["control_plane_linkage_declared"] is True
    assert hermes["direct_authority_guard_declared"] is True
    assert hermes["target_scope_failure_declared"] is True
    assert hermes["audit_survival_declared"] is True
    assert hermes["blocking_gaps"] == []


def test_runtime_instance_pair_level_validation_now_asserts_runtime_specific_and_shared_escalation_structure() -> None:
    openclaw = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)
    hermes = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_rules = set(openclaw["escalation_rules"])
    hermes_rules = set(hermes["escalation_rules"])

    assert "approval missing or invalid" in openclaw_rules
    assert "approval envelope missing or invalid" in hermes_rules
    assert "Discord/control-plane input treated as direct authority" in hermes_rules

    for shared_rule in (
        "provenance minimums fail",
        "target outside declared canonical scope",
        "index update target not declared",
        "attempted write outside write_scope",
        "any request exceeds draft substrate posture",
    ):
        assert shared_rule in openclaw_rules
        assert shared_rule in hermes_rules


def test_runtime_instance_pair_level_validation_now_asserts_shared_execution_controls_and_audit_expectations() -> None:
    openclaw = load_manifest("openclaw_promote_note", vault_root=_VAULT_ROOT)
    hermes = load_manifest("hermes_promote_note", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_expectations = set(openclaw["audit_expectations"])
    hermes_expectations = set(hermes["audit_expectations"])

    assert openclaw["failure_behavior"] == "escalate"
    assert hermes["failure_behavior"] == "escalate"
    assert openclaw["approval_rule"] == "operator-explicit"
    assert hermes["approval_rule"] == "operator-explicit"
    assert "rejected before finalization" in openclaw["rollback_path"]
    assert "rejected before finalization" in hermes["rollback_path"]

    assert "operator approval reference recorded" in openclaw_expectations
    assert "operator approval reference recorded" in hermes_expectations
    assert "control-plane request reference recorded" in hermes_expectations

    for shared_expectation in (
        "provenance minimum result recorded",
        "canonical write target recorded",
        "index update targets recorded",
        "draft workflow status recorded",
    ):
        assert shared_expectation in openclaw_expectations
        assert shared_expectation in hermes_expectations


def test_runtime_instance_pair_level_validation_now_asserts_required_and_optional_read_structure() -> None:
    openclaw = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)
    hermes = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_required = set(openclaw["required_reads"])
    hermes_required = set(hermes["required_reads"])
    openclaw_optional = set(openclaw["optional_reads"])
    hermes_optional = set(hermes["optional_reads"])

    assert "candidate_path (declared at runtime)" in openclaw_required
    assert "candidate_path (declared at runtime)" in hermes_required
    assert "source_refs or source_ids (declared at runtime)" in openclaw_required
    assert "source_refs or source_ids (declared at runtime)" in hermes_required
    assert "control_plane_request_ref (declared at runtime)" in hermes_required

    for shared_optional in (
        "index_update_targets (declared at runtime)",
        "07_LOGS/Agent-Activity/",
        "07_LOGS/Build-Logs/",
    ):
        assert shared_optional in openclaw_optional
        assert shared_optional in hermes_optional


def test_runtime_instance_pair_level_validation_now_asserts_shared_forbidden_boundary_structure() -> None:
    openclaw = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)
    hermes = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_forbidden_actions = set(openclaw["forbidden_actions"])
    hermes_forbidden_actions = set(hermes["forbidden_actions"])
    openclaw_forbidden_zones = set(openclaw["forbidden_write_zones"])
    hermes_forbidden_zones = set(hermes["forbidden_write_zones"])

    for shared_forbidden_action in (
        "ambient_vault_write",
        "write_protected_files",
        "write_project_os_files",
        "write_now_md",
        "autonomous_promotion",
        "delete_any_file",
        "rename_any_file",
        "move_any_file",
        "execute_external_commands",
        "access_api_keys_or_credentials",
        "invoke_network_connectors",
        "connector_expansion",
        "multi_repo_access",
        "write_outside_declared_write_scope",
    ):
        assert shared_forbidden_action in openclaw_forbidden_actions
        assert shared_forbidden_action in hermes_forbidden_actions

    assert "direct_discord_driven_write" in hermes_forbidden_actions
    assert "shell_expansion" in hermes_forbidden_actions

    for shared_forbidden_zone in (
        "SOUL.md",
        "CLAUDE.md",
        "README.md",
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "00_HOME/Now.md",
        "01_PROJECTS/",
        "03_INPUTS/",
        "04_SOPS/",
        "05_TEMPLATES/",
        "06_AGENTS/",
        "runtime/",
        ".claude/",
        ".codex/",
        ".obsidian/",
        ".venv/",
    ):
        assert shared_forbidden_zone in openclaw_forbidden_zones
        assert shared_forbidden_zone in hermes_forbidden_zones


def test_runtime_instance_pair_level_validation_now_asserts_shared_input_output_action_alignment() -> None:
    pairs = [
        ("openclaw_promote_note", "openclaw-promotion-review", False),
        ("hermes_promote_note", "hermes-promotion-review", True),
    ]

    for workflow_id, card_id, has_control_plane_linkage in pairs:
        manifest = load_manifest(workflow_id, vault_root=_VAULT_ROOT)
        card = load_card(card_id, vault_root=_VAULT_ROOT)

        assert manifest is not None
        assert card is not None

        inputs = set(manifest["inputs"])
        outputs = set(manifest["outputs"])
        actions = set(card["allowed_actions"])

        assert "candidate_path" in inputs
        assert "target_path" in inputs
        assert "verification_status" in inputs
        assert "source_refs" in inputs
        assert "source_package_id" in inputs
        assert "source_ids" in inputs
        assert "index_update_targets" in inputs
        assert "promotion_reason" in inputs
        assert "operator_approval_ref" in inputs

        assert "promoted_note_path" in outputs
        assert "index_update_paths" in outputs
        assert "provenance_check_result" in outputs
        assert "promotion_record_path" in outputs
        assert "audit_record_path" in outputs
        assert "build_log_path" in outputs

        assert "write_bounded_canonical_note" in actions
        assert "write_bounded_index_update" in actions
        assert "write_promotion_record" in actions
        assert "write_agent_activity_log" in actions
        assert "write_build_log" in actions

        if has_control_plane_linkage:
            assert "control_plane_request_ref" in inputs
            assert "approval_linkage_record" in outputs
            assert "read_control_plane_approval_record" in actions
        else:
            assert "control_plane_request_ref" not in inputs
            assert "approval_linkage_record" not in outputs
            assert "read_control_plane_approval_record" not in actions


def test_runtime_instance_pair_level_validation_now_asserts_manifest_role_card_identity_and_doctrine_alignment() -> None:
    pairs = [
        ("openclaw_promote_note", "openclaw-promotion-review", "openclaw"),
        ("hermes_promote_note", "hermes-promotion-review", "hermes"),
    ]

    for workflow_id, card_id, runtime_id in pairs:
        manifest = load_manifest(workflow_id, vault_root=_VAULT_ROOT)
        card = load_card(card_id, vault_root=_VAULT_ROOT)

        assert manifest is not None
        assert card is not None
        assert manifest["role_card"] == card["id"]
        assert manifest["runtime_adapter"] == runtime_id
        assert manifest["task_type"] == "promotion-review"
        assert manifest["trigger_type"] == "manual"
        assert manifest["owner"] == "operator"
        assert card["owner"] == "operator"
        assert manifest["permission_ceiling"] == "gated_canonical_write"
        assert "draft" in manifest["description"].lower()
        assert "not active authority" in manifest["description"].lower()
        assert "does not activate" in manifest["notes"].lower()
        assert "explicit constitutional approval" in manifest["notes"].lower()
        assert "not active authority" in card["description"].lower()


def test_runtime_instance_pair_level_validation_now_asserts_shared_and_runtime_specific_runtime_expectations() -> None:
    openclaw = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)
    hermes = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_expectations = set(openclaw["runtime_expectations"])
    hermes_expectations = set(hermes["runtime_expectations"])

    for shared_expectation in (
        "AOR stages execute before any writeback",
        "Gate provenance minimums are checked centrally",
        "audit record is written regardless of approval outcome",
        "this role card is draft substrate, not live activation",
    ):
        assert shared_expectation in openclaw_expectations
        assert shared_expectation in hermes_expectations

    assert "OpenClaw remains non-autonomous for promotion" in openclaw_expectations
    assert "Hermes remains non-autonomous for promotion" in hermes_expectations
    assert "Discord/gateway input remains control-plane context, not direct authority" in hermes_expectations


def test_runtime_instance_pair_level_validation_now_asserts_shared_and_runtime_specific_allowed_action_structure() -> None:
    openclaw = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)
    hermes = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_actions = set(openclaw["allowed_actions"])
    hermes_actions = set(hermes["allowed_actions"])

    for shared_action in (
        "read_declared_candidate",
        "read_declared_sources",
        "read_declared_indexes",
        "generate_markdown_output",
        "write_bounded_canonical_note",
        "write_bounded_index_update",
        "write_promotion_record",
        "write_agent_activity_log",
        "write_build_log",
    ):
        assert shared_action in openclaw_actions
        assert shared_action in hermes_actions

    assert "read_control_plane_approval_record" in hermes_actions


def test_runtime_instance_pair_level_validation_now_asserts_shared_write_scope_structure() -> None:
    openclaw = load_card("openclaw-promotion-review", vault_root=_VAULT_ROOT)
    hermes = load_card("hermes-promotion-review", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_scope = set(openclaw["write_scope"])
    hermes_scope = set(hermes["write_scope"])

    for shared_scope in (
        "02_KNOWLEDGE/",
        "07_LOGS/Promotion-Records/",
        "07_LOGS/Agent-Activity/",
        "07_LOGS/Build-Logs/",
    ):
        assert shared_scope in openclaw_scope
        assert shared_scope in hermes_scope

    assert openclaw_scope == hermes_scope


def test_runtime_instance_pair_level_validation_now_asserts_shared_writeback_target_structure() -> None:
    openclaw = load_manifest("openclaw_promote_note", vault_root=_VAULT_ROOT)
    hermes = load_manifest("hermes_promote_note", vault_root=_VAULT_ROOT)

    assert openclaw is not None
    assert hermes is not None

    openclaw_targets = set(openclaw["writeback_targets"])
    hermes_targets = set(hermes["writeback_targets"])

    for shared_target in (
        "02_KNOWLEDGE/",
        "07_LOGS/Promotion-Records/",
        "07_LOGS/Agent-Activity/",
        "07_LOGS/Build-Logs/",
    ):
        assert shared_target in openclaw_targets
        assert shared_target in hermes_targets

    assert openclaw_targets == hermes_targets


def test_runtime_instance_pair_level_validation_now_asserts_canonical_activation_blockers() -> None:
    openclaw = assess_openclaw_promotion_activation_readiness(vault_root=_VAULT_ROOT)
    hermes = assess_hermes_promotion_activation_readiness(vault_root=_VAULT_ROOT)

    assert openclaw["adapter_posture_ok"] is True
    assert openclaw["provenance_gate_seam_present"] is True
    assert openclaw["promotion_record_lane_seeded"] is True
    assert openclaw["ready"] is False
    assert openclaw["promotion_record_lane_declared"] is True
    assert openclaw["workflow_still_draft"] is True
    assert openclaw["adapter_still_fail_closed"] is True
    assert any("draft" in issue.lower() for issue in openclaw["blocking_issues"])
    assert any(
        "fail-closed" in issue.lower() or "may_promote_to_knowledge" in issue
        for issue in openclaw["blocking_issues"]
    )

    assert hermes["adapter_posture_ok"] is True
    assert hermes["provenance_gate_seam_present"] is True
    assert hermes["promotion_record_lane_seeded"] is True
    assert hermes["control_plane_linkage_declared"] is True
    assert hermes["direct_authority_guard_declared"] is True
    assert hermes["ready"] is False
    assert hermes["promotion_record_lane_declared"] is True
    assert hermes["workflow_still_draft"] is True
    assert hermes["adapter_still_fail_closed"] is True
    assert any("draft" in issue.lower() for issue in hermes["blocking_issues"])
    assert any(
        "fail-closed" in issue.lower() or "may_promote_to_knowledge" in issue
        for issue in hermes["blocking_issues"]
    )
