"""Tests for the native read-only Studio Approval Center panel."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Event
from time import monotonic

from runtime.forge.registry import (
    LIVE_INSTALL_APPROVAL_RECORD_TYPE,
    LIVE_INSTALL_APPROVAL_RELATIVE_DIR,
    LIVE_INSTALL_APPROVAL_SCOPE,
    ROLLBACK_APPROVAL_RECORD_TYPE,
    ROLLBACK_APPROVAL_RELATIVE_DIR,
    ROLLBACK_APPROVAL_SCOPE,
    SANDBOX_APPROVAL_RECORD_TYPE,
    SANDBOX_APPROVAL_RELATIVE_DIR,
    SANDBOX_APPROVAL_SCOPE,
    build_sandbox_install_approval,
)
from runtime.forge.marketplace import (
    build_forge_marketplace_export_package,
    build_forge_marketplace_import_sandbox_approval,
)
from runtime.forge.panel import load_demo_manifest
from runtime.studio import approval_center_panel
from runtime.studio.approval_center_panel import build_approval_center_panel


def _seed_vault(vault: Path) -> None:
    (vault / "runtime" / "studio" / "approvals").mkdir(parents=True)
    (vault / "runtime" / "studio" / "approvals" / "studio-approval-1.json").write_text(
        json.dumps(
            {
                "approval_id": "studio-approval-1",
                "status": "pending",
                "action_spec": {
                    "action_type": "create_file",
                    "target_path": "02_KNOWLEDGE/example.md",
                    "content": "hidden from panel",
                },
            }
        ),
        encoding="utf-8",
    )
    (vault / "07_LOGS" / "SiteOps-Approvals" / "local" / "default").mkdir(parents=True)
    (vault / "07_LOGS" / "SiteOps-Approvals" / "local" / "default" / "siteops-approval-1.json").write_text(
        json.dumps(
            {
                "approval_id": "siteops-approval-1",
                "status": "pending",
                "workflow_id": "workflow-1",
                "action": "external.publish",
                "approval_ref": "07_LOGS/SiteOps-Approvals/local/default/siteops-approval-1.json",
            }
        ),
        encoding="utf-8",
    )
    (vault / "07_LOGS" / "Operator-Briefs").mkdir(parents=True)
    (vault / "07_LOGS" / "Operator-Briefs" / "2026-05-04-approval-request-proposal.md").write_text(
        "# Runtime MCP Approval Request\n",
        encoding="utf-8",
    )
    (vault / "07_LOGS" / "Pulse-Decks" / "approval-queue").mkdir(parents=True)
    (vault / "07_LOGS" / "Pulse-Decks" / "approval-queue" / "queue.json").write_text(
        "{}",
        encoding="utf-8",
    )


def test_approval_center_panel_aggregates_read_only_sources(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_vault(vault)

    model = build_approval_center_panel(vault)

    assert model["surface"] == "studio_approval_center_panel"
    assert model["model_version"] == "studio.approval_center_panel.v1"
    assert model["native_panel"]["mounted"] is True
    assert model["native_panel"]["panel_id"] == "approval-center"
    source_ids = {item["id"] for item in model["source_groups"]}
    assert {
        "pulse",
        "studio-service",
        "chaser-forge",
        "osril",
        "gate-requests",
        "runtime-resumes",
        "siteops",
        "startup-controls",
    }.issubset(source_ids)
    assert model["summary"]["source_group_count"] >= 8
    assert model["summary"]["operator_decision_controls_present"] is False
    assert model["summary"]["approval_execution_available"] is False
    assert model["queue_handoff"]["viewing_approvals"] is True
    assert model["queue_handoff"]["consuming_or_executing_approvals"] is False
    assert model["queue_handoff"]["handoff_status"] == "phase9_dependency_blocked"
    assert model["queue_handoff"]["required_backend_dependency"] == "phase9_approval_consumption_executor_contract"
    assert model["readiness"]["approval_center_independent_route"] == "#/approval-center"
    assert model["readiness"]["viewing_distinguished_from_consuming"] is True
    assert model["readiness"]["phase9_dependency_blocker_visible"] is True


def test_approval_center_panel_has_no_execution_or_write_authority(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_vault(vault)

    model = build_approval_center_panel(vault)
    authority = model["authority"]

    assert authority["read_only"] is True
    assert authority["possible_writes"] == []
    assert model["possible_writes"] == []
    assert model["allowed_actions"] == ["inspect-approval-center-panel"]
    for key in [
        "writes_approval_artifacts",
        "writes_review_decisions",
        "grants_approvals",
        "executes_approvals",
        "consumes_approval_decisions",
        "applies_candidates",
        "resumes_runtimes",
        "writes_agent_bus_tasks",
        "dispatches_runtimes",
        "executes_workflows",
        "activates_schedules",
        "provider_calls_allowed",
        "connector_calls_allowed",
        "memory_approval_allowed",
        "canonical_mutation_allowed",
        "shows_secrets",
        "shows_raw_credentials",
    ]:
        assert authority[key] is False


def test_approval_center_panel_does_not_expose_studio_action_content(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_vault(vault)

    model = build_approval_center_panel(vault)
    serialized = json.dumps(model)

    assert "hidden from panel" not in serialized
    assert "approval_center_panel_mounted" in serialized
    json.dumps(model)


def test_approval_center_panel_renders_studio_states_duplicates_and_operator_context(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    approvals = vault / "runtime" / "studio" / "approvals"
    approvals.mkdir(parents=True)
    packets = [
        {
            "approval_id": "studio-pending-1",
            "status": "pending",
            "request_digest_sha256": "digest-pending",
            "action_spec": {
                "action_type": "write_draft",
                "target_path": "07_LOGS/Operator-Briefs/draft.md",
                "metadata": {
                    "source_contract": "studio-test-contract",
                    "request_reason": "operator needs to review proposed draft write",
                    "safety_summary": "draft-only write; no canonical mutation",
                },
            },
        },
        {
            "approval_id": "studio-pending-1",
            "status": "pending",
            "request_digest_sha256": "digest-duplicate",
            "action_spec": {"action_type": "write_draft", "target_path": "07_LOGS/Operator-Briefs/duplicate.md"},
        },
        {
            "approval_id": "studio-approved-1",
            "status": "approved",
            "request_digest_sha256": "digest-approved",
            "action_spec": {"action_type": "inspect", "target_path": "runtime/studio/report.json"},
        },
        {
            "approval_id": "studio-rejected-1",
            "status": "rejected",
            "request_digest_sha256": "digest-rejected",
            "action_spec": {"action_type": "publish", "target_path": "02_KNOWLEDGE/rejected.md"},
        },
        {"approval_id": "studio-partial-1", "status": "pending"},
    ]
    for index, packet in enumerate(packets):
        (approvals / f"packet-{index}.json").write_text(json.dumps(packet), encoding="utf-8")
    (approvals / "invalid.json").write_text("{not-json", encoding="utf-8")

    model = build_approval_center_panel(vault)
    studio = next(group for group in model["source_groups"] if group["id"] == "studio-service")
    items_by_title = {item["title"]: item for item in studio["latest_items"]}

    assert studio["status_counts"]["pending"] == 2
    assert studio["status_counts"]["approved"] == 1
    assert studio["status_counts"]["rejected"] == 1
    assert studio["status_counts"]["partial_packet"] == 1
    assert studio["status_counts"]["invalid_packet"] == 1
    assert studio["duplicate_count"] == 1
    assert studio["pending_count"] == 2
    assert studio["ready_count"] == 1
    assert studio["blocked_count"] == 4

    pending = items_by_title["studio-pending-1"]
    assert pending["duplicate"] is True
    assert pending["request_digest_sha256"] in {"digest-pending", "digest-duplicate"}
    assert pending["source_digest"] in {"digest-pending", "digest-duplicate"}
    assert pending["requested_action"] == "write_draft"
    assert pending["requested_touch"] in {
        "07_LOGS/Operator-Briefs/draft.md",
        "07_LOGS/Operator-Briefs/duplicate.md",
    }
    assert pending["affected_files_systems"]
    assert "duplicate" in pending["duplicate_protection_hint"]
    assert pending["request_reason"] in {"operator needs to review proposed draft write", "not_provided"}
    assert pending["safety_summary"] in {"draft-only write; no canonical mutation", "not_provided"}

    assert items_by_title["invalid"]["status"] == "invalid_packet"
    assert items_by_title["studio-partial-1"]["status"] == "partial_packet"


def _forge_packet(
    *,
    record_type: str,
    scope: str,
    packet_id: str,
    status: str,
    decision: str,
    request_digest: str,
    consumed: bool = False,
) -> dict:
    return {
        "record_type": record_type,
        "schema_version": "forge.test",
        "generated_at": "2026-05-20T00:00:00Z",
        "status": status,
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": decision,
        "approval_scope": scope,
        "requested_by": "Codex",
        "extension_id": "ugc-campaign-studio",
        "extension_name": "UGC Campaign Studio",
        "approval_artifact_path": f"artifact/{packet_id}.json",
        "future_registry_path": "runtime/forge/registry/extensions.json",
        "future_extension_target_paths": [
            "extensions/ugc-campaign-studio/manifest.json",
            "extensions/ugc-campaign-studio/ui/sidebar.json",
        ],
        "operator_confirmation_text": "APPROVE FORGE TEST REQUEST ONLY",
        "approved_material": {
            "requested_action": "request_forge_test_action",
            "extension_id": "ugc-campaign-studio",
            "target_paths": [
                "extensions/ugc-campaign-studio/manifest.json",
                "extensions/ugc-campaign-studio/ui/sidebar.json",
            ],
            "approval_effect": "authorizes one future source-specific Forge executor attempt after revalidation",
        },
        "approval_consumed": consumed,
    }


def test_approval_center_panel_routes_chaser_forge_approval_roots(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / SANDBOX_APPROVAL_RELATIVE_DIR).mkdir(parents=True)
    (vault / LIVE_INSTALL_APPROVAL_RELATIVE_DIR).mkdir(parents=True)
    (vault / ROLLBACK_APPROVAL_RELATIVE_DIR).mkdir(parents=True)
    (vault / SANDBOX_APPROVAL_RELATIVE_DIR / "sandbox.json").write_text(
        json.dumps(
            _forge_packet(
                record_type=SANDBOX_APPROVAL_RECORD_TYPE,
                scope=SANDBOX_APPROVAL_SCOPE,
                packet_id="forge-sandbox-appr-demo",
                status="pending_operator_decision",
                decision="pending",
                request_digest="sandbox-digest",
            )
        ),
        encoding="utf-8",
    )
    (vault / LIVE_INSTALL_APPROVAL_RELATIVE_DIR / "live.json").write_text(
        json.dumps(
            _forge_packet(
                record_type=LIVE_INSTALL_APPROVAL_RECORD_TYPE,
                scope=LIVE_INSTALL_APPROVAL_SCOPE,
                packet_id="forge-live-install-appr-demo",
                status="approved",
                decision="approved",
                request_digest="live-digest",
            )
        ),
        encoding="utf-8",
    )
    (vault / ROLLBACK_APPROVAL_RELATIVE_DIR / "rollback.json").write_text(
        json.dumps(
            _forge_packet(
                record_type=ROLLBACK_APPROVAL_RECORD_TYPE,
                scope=ROLLBACK_APPROVAL_SCOPE,
                packet_id="forge-rollback-appr-demo",
                status="consumed",
                decision="approved",
                request_digest="rollback-digest",
                consumed=True,
            )
        ),
        encoding="utf-8",
    )
    (vault / ROLLBACK_APPROVAL_RELATIVE_DIR / "invalid.json").write_text("{not-json", encoding="utf-8")

    model = build_approval_center_panel(vault)
    forge = next(group for group in model["source_groups"] if group["id"] == "chaser-forge")
    items_by_title = {item["title"]: item for item in forge["latest_items"]}

    assert forge["status"] == "pending_operator_review"
    assert forge["status_counts"]["pending_operator_review"] == 1
    assert forge["status_counts"]["approved_pending_execution"] == 1
    assert forge["status_counts"]["consumed"] == 1
    assert forge["status_counts"]["invalid_packet"] == 1
    assert forge["pending_count"] == 1
    assert forge["ready_count"] == 2
    assert forge["blocked_count"] == 1
    assert forge["artifact_count"] == 4
    assert forge["source_specific_decision_handoff_available"] is True
    assert forge["decision_handoff_count"] == 1
    assert forge["decision_handoff_api_method"] == "review_chaser_forge_approval_decision"
    assert forge["operator_decision_form_available"] is True
    assert forge["operator_decision_form_count"] == 1
    assert forge["operator_decision_form_api_method"] == "get_chaser_forge_approval_decision_form"
    assert model["readiness"]["chaser_forge_approvals_visible"] is True
    assert model["readiness"]["chaser_forge_source_specific_decision_handoff_visible"] is True
    assert model["readiness"]["chaser_forge_operator_decision_form_visible"] is True
    assert model["readiness"]["generic_approval_center_decision_controls_present"] is False
    assert model["summary"]["source_specific_decision_handoff_count"] == 1
    assert model["summary"]["operator_decision_form_count"] == 1
    assert model["authority"]["executes_approvals"] is False

    sandbox = items_by_title["forge-sandbox-appr-demo"]
    assert sandbox["source_digest"] == "sandbox-digest"
    assert sandbox["requested_action"] == "request_forge_test_action"
    assert sandbox["requested_touch"] == (
        "extensions/ugc-campaign-studio/manifest.json, "
        "extensions/ugc-campaign-studio/ui/sidebar.json"
    )
    assert sandbox["affected_files_systems"]
    assert "source-specific Forge executor" in sandbox["safety_summary"]
    assert "must match" in sandbox["duplicate_protection_hint"]
    assert sandbox["decision_handoff"]["available"] is True
    assert sandbox["decision_handoff"]["api_method"] == "review_chaser_forge_approval_decision"
    assert sandbox["decision_handoff"]["approval_family"] == "sandbox"
    assert sandbox["decision_handoff"]["expected_request_digest_sha256"] == "sandbox-digest"
    assert sandbox["decision_handoff"]["approval_consumption_allowed"] is False
    assert sandbox["decision_handoff"]["forge_execution_allowed"] is False
    assert sandbox["operator_decision_form"]["available"] is True
    assert sandbox["operator_decision_form"]["api_method"] == "get_chaser_forge_approval_decision_form"
    assert sandbox["operator_decision_form"]["submit_api_method"] == "review_chaser_forge_approval_decision"
    assert sandbox["operator_decision_form"]["approval_family"] == "sandbox"
    assert sandbox["operator_decision_form"]["expected_request_digest_sha256"] == "sandbox-digest"
    assert sandbox["operator_decision_form"]["copyable_statement_required"] is True
    assert sandbox["operator_decision_form"]["prepares_submit_payload"] is True
    assert sandbox["operator_decision_form"]["approval_consumption_allowed"] is False
    assert sandbox["operator_decision_form"]["forge_execution_allowed"] is False


def test_approval_center_panel_routes_real_forge_sandbox_request_artifact(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    preview = build_sandbox_install_approval(vault)
    build_sandbox_install_approval(
        vault,
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    model = build_approval_center_panel(vault)
    forge = next(group for group in model["source_groups"] if group["id"] == "chaser-forge")
    item = forge["latest_items"][0]

    assert forge["pending_count"] == 1
    assert forge["blocked_count"] == 0
    assert item["title"].startswith("forge-sandbox-appr-")
    assert item["status"] == "pending_operator_review"
    assert item["source_digest"] == preview["request_digest_sha256"]
    assert item["requested_action"] == "request_forge_sandbox_install"
    assert "extensions/ugc-campaign-studio" in item["requested_touch"]
    assert item["decision_handoff"]["available"] is True
    assert item["decision_handoff"]["approval_artifact_path"] == item["source_ref"]
    assert item["decision_handoff"]["expected_request_digest_sha256"] == preview["request_digest_sha256"]
    assert item["decision_handoff"]["generic_approval_center_control"] is False
    assert item["operator_decision_form"]["approval_artifact_path"] == item["source_ref"]
    assert item["operator_decision_form"]["api_method"] == "get_chaser_forge_approval_decision_form"
    assert item["operator_decision_form"]["generic_approval_center_control"] is False
    assert model["summary"]["approval_execution_available"] is False


def test_approval_center_panel_routes_real_forge_marketplace_import_request_artifact(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    package_preview = build_forge_marketplace_export_package(vault, manifest=load_demo_manifest())
    approval_preview = build_forge_marketplace_import_sandbox_approval(
        vault,
        package_payload=package_preview["package_payload"],
    )
    build_forge_marketplace_import_sandbox_approval(
        vault,
        package_payload=package_preview["package_payload"],
        request_digest=approval_preview["request_digest_sha256"],
        write_approval_request=True,
    )

    model = build_approval_center_panel(vault)
    forge = next(group for group in model["source_groups"] if group["id"] == "chaser-forge")
    item = forge["latest_items"][0]

    assert forge["pending_count"] == 1
    assert forge["blocked_count"] == 0
    assert "07_LOGS/Agent-Activity/_forge_marketplace_import_approvals" in forge["source_refs"]
    assert item["title"].startswith("forge-marketplace-import-appr-")
    assert item["status"] == "pending_operator_review"
    assert item["source_digest"] == approval_preview["request_digest_sha256"]
    assert item["requested_action"] == "request_forge_marketplace_import_sandbox_review"
    assert "extensions/ugc-campaign-studio" in item["requested_touch"]
    assert item["decision_handoff"]["available"] is True
    assert item["decision_handoff"]["approval_family"] == "marketplace-import"
    assert item["decision_handoff"]["approval_artifact_path"] == item["source_ref"]
    assert item["decision_handoff"]["expected_request_digest_sha256"] == approval_preview["request_digest_sha256"]
    assert item["operator_decision_form"]["approval_family"] == "marketplace-import"
    assert item["operator_decision_form"]["api_method"] == "get_chaser_forge_approval_decision_form"
    assert item["operator_decision_form"]["generic_approval_center_control"] is False
    assert model["summary"]["approval_execution_available"] is False


def test_approval_center_panel_bounds_heavy_source_collection(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    never_finishes = Event()

    def slow_pulse(_vault: Path):
        never_finishes.wait(5)
        return {"id": "pulse"}, []

    monkeypatch.setattr(approval_center_panel, "_pulse_group", slow_pulse)

    started = monotonic()
    model = build_approval_center_panel(vault, source_timeout_seconds=0.01)
    elapsed = monotonic() - started

    assert elapsed < 0.5
    pulse = next(group for group in model["source_groups"] if group["id"] == "pulse")
    assert pulse["status"] == "source_timeout"
    assert "source_timeout:pulse" in model["warnings"]
    assert model["authority"]["executes_approvals"] is False


def test_approval_center_panel_zero_budget_does_not_start_heavy_collectors(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    def forbidden_source(_vault: Path):
        raise AssertionError("zero-budget Studio panel smoke must not start heavy collectors")

    monkeypatch.setattr(approval_center_panel, "_pulse_group", forbidden_source)
    model = build_approval_center_panel(vault, source_timeout_seconds=0.0)

    assert model["surface"] == "studio_approval_center_panel"
    assert "source_timeout:pulse" in model["warnings"]
    assert model["authority"]["canonical_mutation_allowed"] is False
