from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import runtime.cli.main as cli
import runtime.siteops.candidate_promotions as candidate_promotions_module
from runtime.chaseos_gate import check_runtime_operation
from runtime.siteops.approvals import decide_approval_request
from runtime.siteops.candidate_promotions import (
    PROMOTION_GATE_APPLY_OPERATION,
    apply_trusted_candidate_artifacts,
    candidate_promotion_activation_approval_decision_consumer_design,
    candidate_promotion_activation_approval_decision_consumer_write_guard_contract,
    candidate_promotion_activation_approval_decision_consumer_writer_design,
    candidate_promotion_activation_approval_decision_consumer_writer_implementation,
    candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval,
    candidate_promotion_activation_approval_decision_consumer_writer_implementation_request,
    candidate_promotion_activation_consumption_live_readiness,
    candidate_promotion_activation_executor_design,
    candidate_promotion_activation_executor_implementation,
    candidate_promotion_activation_executor_implementation_approval,
    candidate_promotion_activation_executor_implementation_request,
    candidate_promotion_activation_gate_policy_patch_writer_implementation,
    candidate_promotion_activation_gate_live_readiness,
    candidate_promotion_activation_executor_live_readiness,
    candidate_promotion_activation_executor_preflight,
    candidate_promotion_activation_approval_decision_preflight,
    candidate_promotion_activation_approval_request,
    candidate_promotion_activation_boundary_readiness,
    candidate_promotion_apply_contract,
    candidate_promotion_approval_rebind_spec,
    candidate_promotion_bound_approval_request_spec,
    candidate_promotion_bound_approval_writer_design,
    candidate_promotion_bound_approval_writer_implementation,
    candidate_promotion_bound_approval_writer_implementation_approval,
    candidate_promotion_bound_approval_writer_implementation_request,
    candidate_promotion_bound_approval_writer_preflight,
    candidate_promotion_browser_skill_shadow_replay_design,
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout,
    candidate_promotion_browser_skill_shadow_execution_approval_packet,
    candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight,
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request,
    candidate_promotion_browser_skill_shadow_execution_approval_live_decision_readiness,
    candidate_promotion_browser_skill_shadow_execution_proof,
    candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard,
    candidate_promotion_browser_skill_shadow_execution_proof_review_closeout,
    candidate_promotion_browser_skill_shadow_execution_proof_readiness,
    candidate_promotion_browser_skill_shadow_replay_implementation_approval,
    candidate_promotion_browser_skill_shadow_replay_implementation_request,
    candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run,
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass,
    candidate_promotion_browser_skill_shadow_replay_runner_write_guard,
    candidate_promotion_live_activation_evidence_closeout,
    candidate_promotion_source_approval_rebind_live_readiness,
    candidate_promotion_replacement_approval_decision_consumption,
    candidate_promotion_collision_policy_spec,
    candidate_promotion_executor_implementation_design_review,
    candidate_promotion_executor_prewrite_audit_spec,
    candidate_promotion_executor_review_checklist,
    candidate_promotion_gate_apply_design,
    candidate_promotion_gate_allowlist_review,
    candidate_promotion_gate_executor_spec,
    candidate_promotion_inactive_artifact_validator,
    candidate_promotion_trusted_inactive_artifact_writer_implementation,
    candidate_promotion_trusted_inactive_artifact_writer_implementation_approval,
    candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request,
    candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_design,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_design,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_live_application_readiness,
    candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_plan,
    candidate_promotion_trusted_inactive_artifact_writer_live_gate_readiness,
    candidate_promotion_trusted_inactive_artifact_writer_implementation_request,
    candidate_promotion_trusted_inactive_artifact_writer_preflight,
    candidate_promotion_preimplementation_verifier,
    candidate_promotion_trusted_executor_design,
    list_candidate_promotion_approvals,
    request_scoped_candidate_promotion,
)
from runtime.siteops.errors import SiteOpsValidationError


ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_FIXTURE = (
    ROOT
    / "runtime"
    / "tests"
    / "fixtures"
    / "browser_skill_candidates_vault"
    / "03_INPUTS"
    / "Browser-Skill-Candidates"
    / "example-com"
    / "20260430__candidate-run-123.md"
)


def _copy_candidate(vault: Path) -> None:
    target = vault / "03_INPUTS" / "Browser-Skill-Candidates" / "example-com" / CANDIDATE_FIXTURE.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CANDIDATE_FIXTURE, target)


def _approved_legacy_unbound_candidate_request(vault: Path) -> dict[str, object]:
    _copy_candidate(vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")
    return request


def _approved_gate_policy_patch_inputs(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str]:
    request = _approved_legacy_unbound_candidate_request(vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    return replacement_approval_id, gate_approval_id


def _write_gate_policy_application_preflight_files(vault: Path) -> tuple[Path, Path]:
    runtime_policy = vault / "runtime" / "chaseos_gate.py"
    gateway_allowlists = vault / "runtime" / "policy" / "gateway_allowlists.json"
    runtime_policy.parent.mkdir(parents=True, exist_ok=True)
    gateway_allowlists.parent.mkdir(parents=True, exist_ok=True)
    runtime_policy.write_text(
        "RUNTIME_OPERATION_POLICIES = {}\n",
        encoding="utf-8",
    )
    gateway_allowlists.write_text(
        json.dumps({"write_targets": {"existing_review": ["runtime/existing/*.json"]}}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return runtime_policy, gateway_allowlists


def test_secret_session_exclusion_recheck_redacts_matched_validation_errors() -> None:
    recheck = candidate_promotions_module._secret_session_exclusion_recheck(
        {
            "validation": {
                "checked": True,
                "errors": [
                    "forbidden secret-like value at steps.0.note: bearer sk_live_123",
                    "forbidden cookie field at selectors.login.cookie: sessionid=abc123",
                    "ordinary validation error",
                ],
            }
        }
    )

    assert recheck["checked"] is True
    assert recheck["passed"] is False
    assert recheck["matched_error_count"] == 2
    assert recheck["raw_content_visible"] is False
    assert recheck["writes_performed"] is False
    assert len(recheck["matched_errors"]) == 2
    serialized = json.dumps(recheck["matched_errors"])
    assert "bearer" not in serialized
    assert "sk_live" not in serialized
    assert "cookie" not in serialized
    assert "sessionid" not in serialized
    assert "abc123" not in serialized
    assert "forbidden secret-like value" not in serialized
    assert "forbidden cookie field" not in serialized


def _copy_candidate_variant(vault: Path, *, candidate_id: str, skill_id: str) -> None:
    target = vault / "03_INPUTS" / "Browser-Skill-Candidates" / "example-com" / f"20260430__{candidate_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    text = CANDIDATE_FIXTURE.read_text(encoding="utf-8")
    text = text.replace("candidate_run_123", candidate_id)
    text = text.replace("example.safe_candidate", skill_id)
    target.write_text(text, encoding="utf-8")


def _write_test_tenant(vault: Path, *, tenant_id: str, workspace_id: str, user_id: str) -> None:
    target = vault / "runtime" / "siteops" / "tenants" / f"{tenant_id}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tenant": {
            "tenant_id": tenant_id,
            "display_name": "Candidate Promotion Test Tenant",
            "default_workspace_id": workspace_id,
            "default_user_id": user_id,
            "mode": "test",
            "owner_type": "tenant",
            "visibility": "private",
            "created_by": user_id,
            "updated_by": user_id,
            "version": "0.1.0",
            "status": "VERIFIED",
        },
        "roles": [
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "roles": ["tenant_admin", "workspace_admin", "workflow_author", "approver", "auditor"],
                "status": "VERIFIED",
            }
        ],
        "site_skill_installations": [],
        "workflow_installations": [],
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _payload(text: str) -> dict:
    data = json.loads(text)
    return data.get("result", data)


def _assert_guarded_executor_entrypoint() -> None:
    assert hasattr(candidate_promotions_module, "apply_trusted_candidate_artifacts")
    assert callable(apply_trusted_candidate_artifacts)
    assert getattr(candidate_promotions_module.apply_trusted_candidate_artifacts, "siteops_guarded_executor") is True


def test_scoped_candidate_promotion_contract_requires_scope_and_writes_nothing(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)

    result = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=False,
    )

    assert result["scope"] == {"tenant_id": "local", "workspace_id": "default", "user_id": "local-user"}
    assert result["contract_status"] == "approval_request_ready"
    assert result["approval_request"]["tenant_id"] == "local"
    assert result["approval_request"]["workspace_id"] == "default"
    assert result["approval_request"]["user_id"] == "local-user"
    assert result["approval_request_written"] is False
    assert result["siteops_run_written"] is False
    assert result["audit_written"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_scoped_candidate_promotion_can_persist_approval_run_and_audit_only(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)

    result = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    assert result["approval_request_written"] is True
    assert result["siteops_run_written"] is True
    assert result["audit_written"] is True
    assert Path(result["run_ref"]).exists()
    assert Path(result["audit_ref"]).exists()
    assert Path(result["approval"]["approval_ref"]).exists()
    assert result["approval"]["tenant_id"] == "local"
    assert result["approval"]["workspace_id"] == "default"
    assert result["approval"]["user_id"] == "local-user"
    assert result["approval"]["action"] == "browser_skill_candidate.promote"
    assert result["approval"]["metadata"]["candidate_id"] == "candidate_run_123"
    assert result["approval"]["metadata"]["proposed_skill_id"] == "example.safe_candidate"
    assert result["apply_contract"]["apply_contract_status"] == "blocked_pending_approval"
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()

    audit_events = [json.loads(line) for line in Path(result["audit_ref"]).read_text(encoding="utf-8").splitlines()]
    assert any(event["event_type"] == "policy_decision" for event in audit_events)
    assert any(event["event_type"] == "approval_request_created" for event in audit_events)


def test_scoped_candidate_promotion_request_denies_viewer_role(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)

    with pytest.raises(SiteOpsValidationError, match="lacks role"):
        request_scoped_candidate_promotion(
            "candidate_run_123",
            siteops_vault,
            tenant_id="local",
            workspace_id="default",
            user_id="viewer-user",
            requested_by="viewer-user",
            write_approval=True,
        )


def test_candidate_apply_contract_stays_non_mutating_after_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    pending = candidate_promotion_apply_contract(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )
    assert pending["apply_contract"]["apply_contract_status"] == "blocked_pending_approval"

    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approved = candidate_promotion_apply_contract(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert approved["apply_contract"]["apply_contract_status"] == "gate_apply_review_ready"
    assert approved["approval_provenance"]["provenance_status"] == "bound_match"
    assert approved["approval_provenance"]["candidate_id_matches"] is True
    assert approved["approval_provenance"]["proposed_skill_id_matches"] is True
    assert approved["approval_provenance"]["bound_candidate_id"] == "candidate_run_123"
    assert approved["approval_provenance"]["bound_proposed_skill_id"] == "example.safe_candidate"
    assert approved["approval_provenance"]["checked"] is True
    assert approved["writes_performed"] is False
    assert approved["trusted_skill_write_allowed"] is False
    assert approved["siteops_skill_card_write_allowed"] is False


def test_candidate_apply_contract_reports_legacy_unbound_provenance(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_apply_contract(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["approval_provenance"]["provenance_status"] == "legacy_unbound"
    assert result["approval_provenance"]["checked"] is True
    assert result["approval_provenance"]["candidate_id_matches"] is None
    assert result["approval_provenance"]["proposed_skill_id_matches"] is None
    assert result["writes_performed"] is False


def test_candidate_approval_rebind_spec_requires_new_bound_approval_for_legacy(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_approval_rebind_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["approval_rebind_spec_status"] == "approval_rebind_spec_required_no_write_authority"
    assert result["review_decision"] == "create_new_bound_approval_request_in_separate_pass_do_not_mutate_legacy_approval"
    assert result["approval_provenance"]["provenance_status"] == "legacy_unbound"
    assert result["rebind_policy"]["legacy_unbound_approval"] == "do_not_mutate_in_place"
    assert result["replacement_request_preview"]["expected_new_approval_metadata"]["candidate_id"] == "candidate_run_123"
    assert result["replacement_request_preview"]["expected_new_approval_metadata"]["proposed_skill_id"] == "example.safe_candidate"
    assert result["legacy_approval_mutation_allowed"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["approval_decision_written"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_approval_rebind_spec_not_required_for_bound_match(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_approval_rebind_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["approval_rebind_spec_status"] == "approval_rebind_not_required_bound_match"
    assert result["review_decision"] == "no_rebind_needed_existing_approval_is_bound"
    assert result["approval_provenance"]["provenance_status"] == "bound_match"
    assert result["legacy_approval_mutation_allowed"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["writes_performed"] is False


def test_candidate_apply_contract_rejects_approval_for_different_candidate(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    _copy_candidate_variant(siteops_vault, candidate_id="candidate_run_456", skill_id="example.other_candidate")
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    with pytest.raises(SiteOpsValidationError, match="approval candidate does not match"):
        candidate_promotion_apply_contract(
            "candidate_run_456",
            siteops_vault,
            tenant_id="local",
            workspace_id="default",
            user_id="local-user",
            approval_id=request["approval"]["approval_id"],
        )


def test_candidate_approval_provenance_list_is_read_only(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = list_candidate_promotion_approvals(
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
    )

    assert result["ok"] is True
    assert result["writes_performed"] is False
    assert result["candidate_approval_count"] == 1
    item = result["approvals"][0]
    assert item["candidate_id"] == "candidate_run_123"
    assert item["proposed_skill_id"] == "example.safe_candidate"
    assert item["approval_id"] == request["approval"]["approval_id"]
    assert item["approval_status"] == "pending"
    assert item["approval_provenance"]["provenance_status"] == "bound_match"
    assert item["approval_provenance"]["candidate_id_matches"] is True
    assert item["approval_provenance"]["proposed_skill_id_matches"] is True
    assert item["apply_contract_status"] == "blocked_pending_approval"
    assert "executor_preflight_status" not in item
    assert item["writes_performed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_candidate_approval_list_can_include_read_only_executor_preflight(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = list_candidate_promotion_approvals(
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        include_executor_preflight=True,
    )

    item = result["approvals"][0]
    assert item["approval_status"] == "approved"
    assert item["approval_provenance"]["provenance_status"] == "bound_match"
    assert item["apply_contract_status"] == "gate_apply_review_ready"
    assert item["executor_preflight_status"] == "executor_spec_ready_gate_allowlisted_no_write"
    assert item["executor_preflight"]["executor_implemented"] is True
    assert item["executor_preflight"]["executor_enabled"] is True
    assert item["executor_preflight"]["gate_operation_allowed"] is True
    assert item["executor_preflight"]["writes_performed"] is False
    assert item["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_candidate_approval_list_can_include_activation_boundary_readiness(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = list_candidate_promotion_approvals(
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        include_activation_boundary=True,
    )

    item = result["approvals"][0]
    assert result["include_activation_boundary"] is True
    assert item["activation_boundary_status"] == "activation_boundary_ready_no_authority"
    assert item["activation_boundary"]["review_decision"] == "activation_contract_only_do_not_activate_in_this_pass"
    assert item["activation_boundary"]["activation_allowed"] is False
    assert item["activation_boundary"]["activation_performed"] is False
    assert item["activation_boundary"]["writes_performed"] is False
    assert item["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()



def test_candidate_approval_list_can_include_bound_approval_request_spec(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = list_candidate_promotion_approvals(
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        include_bound_approval_request_spec=True,
    )

    item = result["approvals"][0]
    assert result["include_bound_approval_request_spec"] is True
    assert item["approval_provenance"]["provenance_status"] == "legacy_unbound"
    assert item["bound_approval_request_spec_status"] == "bound_approval_request_spec_ready_no_write"
    assert item["bound_approval_request_spec"]["approval_request_artifact_written"] is False
    assert item["bound_approval_request_spec"]["legacy_approval_mutation_allowed"] is False
    assert item["bound_approval_request_spec"]["writes_performed"] is False
    assert item["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_candidate_approval_list_can_include_readiness_summary(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = list_candidate_promotion_approvals(
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        include_executor_preflight=True,
        include_activation_boundary=True,
        include_readiness_summary=True,
    )

    summary = result["readiness_summary"]
    assert result["include_readiness_summary"] is True
    assert summary["approval_status_counts"] == {"approved": 1}
    assert summary["approval_provenance_status_counts"] == {"bound_match": 1}
    assert summary["apply_contract_status_counts"] == {"gate_apply_review_ready": 1}
    assert summary["executor_preflight_status_counts"] == {"executor_spec_ready_gate_allowlisted_no_write": 1}
    assert summary["activation_boundary_status_counts"] == {"activation_boundary_ready_no_authority": 1}
    assert summary["authority"]["writes_performed"] is False
    assert summary["authority"]["activation_allowed"] is False
    assert summary["authority"]["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()



def test_candidate_approval_list_flags_legacy_unbound_executor_preflight_unavailable(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = list_candidate_promotion_approvals(
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        include_executor_preflight=True,
    )

    item = result["approvals"][0]
    assert item["approval_provenance"]["provenance_status"] == "legacy_unbound"
    assert item["executor_preflight_status"] == "blocked_executor_preflight_unavailable"
    assert item["executor_preflight"]["executor_implemented"] is False
    assert item["executor_preflight"]["executor_enabled"] is False
    assert item["executor_preflight"]["writes_performed"] is False
    assert item["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_siteops_candidate_approval_provenance_cli_lists_without_mutation(
    siteops_vault: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_candidate(siteops_vault)
    _write_test_tenant(siteops_vault, tenant_id="tenant-a", workspace_id="workspace-a", user_id="user-a")
    request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "approvals",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["candidate_approval_count"] == 1
    assert result["writes_performed"] is False
    assert result["approvals"][0]["candidate_id"] == "candidate_run_123"
    assert result["approvals"][0]["approval_provenance"]["provenance_status"] == "bound_match"
    assert "executor_preflight_status" not in result["approvals"][0]
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_siteops_candidate_approvals_cli_can_include_executor_preflight(
    siteops_vault: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "approvals",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--include-executor-preflight",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    item = result["approvals"][0]
    assert item["executor_preflight_status"] == "executor_spec_ready_gate_allowlisted_no_write"
    assert item["executor_preflight"]["executor_enabled"] is True
    assert item["executor_preflight"]["writes_performed"] is False
    assert item["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()



def test_siteops_candidate_approvals_cli_can_include_activation_boundary(
    siteops_vault: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "approvals",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--include-activation-boundary",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    item = result["approvals"][0]
    assert result["include_activation_boundary"] is True
    assert item["activation_boundary_status"] == "activation_boundary_ready_no_authority"
    assert item["activation_boundary"]["activation_allowed"] is False
    assert item["activation_boundary"]["activation_performed"] is False
    assert item["activation_boundary"]["writes_performed"] is False
    assert item["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()



def test_siteops_candidate_approvals_cli_can_include_bound_approval_request_spec(
    siteops_vault: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "approvals",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--include-bound-approval-request-spec",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    item = result["approvals"][0]
    assert result["include_bound_approval_request_spec"] is True
    assert item["bound_approval_request_spec_status"] == "bound_approval_request_spec_ready_no_write"
    assert item["bound_approval_request_spec"]["approval_request_artifact_written"] is False
    assert item["bound_approval_request_spec"]["legacy_approval_mutation_allowed"] is False
    assert item["bound_approval_request_spec"]["writes_performed"] is False
    assert item["trusted_skill_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_siteops_candidate_approvals_cli_can_include_readiness_summary(
    siteops_vault: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "approvals",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--include-executor-preflight",
            "--include-activation-boundary",
            "--include-readiness-summary",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    summary = result["readiness_summary"]
    assert result["include_readiness_summary"] is True
    assert summary["approval_status_counts"] == {"approved": 1}
    assert summary["executor_preflight_status_counts"] == {"executor_spec_ready_gate_allowlisted_no_write": 1}
    assert summary["activation_boundary_status_counts"] == {"activation_boundary_ready_no_authority": 1}
    assert summary["authority"]["writes_performed"] is False
    assert summary["authority"]["activation_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()



def test_siteops_candidate_approvals_text_summary_includes_bound_approval_request_counts(
    siteops_vault: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "approvals",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--include-bound-approval-request-spec",
            "--include-readiness-summary",
            "--vault-root",
            str(siteops_vault),
        ]
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "bound_approval_request_spec_status_counts" in output
    assert "bound_approval_request_spec_ready_no_write" in output
    assert "writes_performed: false" in output
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()



def test_candidate_gate_apply_design_stays_denied_by_default_after_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    design = candidate_promotion_gate_apply_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert design["apply_contract"]["apply_contract_status"] == "gate_apply_review_ready"
    assert design["approval_provenance"]["provenance_status"] == "bound_match"
    assert design["approval_provenance"]["candidate_id_matches"] is True
    assert design["approval_provenance"]["proposed_skill_id_matches"] is True
    assert design["gate_apply_design_status"] == "gate_apply_design_ready_but_execution_disabled"
    assert design["gate_operation_allowed"] is True
    assert "allowed" in design["gate_reason"]
    assert design["writes_performed"] is False
    assert design["apply_execution_allowed"] is False
    assert design["trusted_skill_write_allowed"] is False
    assert design["siteops_skill_card_write_allowed"] is False
    assert design["browser_execution_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_gate_executor_spec_is_fail_closed_and_non_mutating(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    spec = candidate_promotion_gate_executor_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in spec["executor_preflight_checks"]}
    assert spec["executor_spec_status"] == "executor_spec_ready_gate_allowlisted_no_write"
    assert spec["executor_preflight_status"] == "executor_spec_ready_gate_allowlisted_no_write"
    assert spec["candidate_preflight_status"] == "approval_request_ready"
    assert spec["approval_provenance"]["provenance_status"] == "bound_match"
    assert checks["candidate_preflight_ready"]["passed"] is True
    assert checks["apply_contract_ready"]["passed"] is True
    assert checks["approval_provenance_bound_match"]["passed"] is True
    assert checks["target_paths_confined"]["passed"] is True
    assert checks["secret_session_exclusion_rechecked"]["passed"] is True
    assert checks["secret_session_exclusion_rechecked"]["detail"] == "no secret/cookie/token/session material detected in candidate validation"
    assert spec["secret_session_exclusion_recheck"] == {
        "checked": True,
        "passed": True,
        "source": "candidate_preflight.validation",
        "matched_error_count": 0,
        "matched_errors": [],
        "raw_content_visible": False,
        "writes_performed": False,
    }
    assert checks["gate_operation_allowlisted"]["passed"] is True
    assert checks["executor_implemented"]["passed"] is True
    assert checks["writes_disabled"]["passed"] is True
    assert spec["gate_operation_allowed"] is True
    assert spec["future_executor"]["implementation_status"] == "BUILT_GUARDED"
    assert spec["future_executor"]["enabled"] is True
    assert spec["executor_implemented"] is True
    assert spec["executor_enabled"] is True
    assert spec["writes_performed"] is False
    assert spec["trusted_skill_write_allowed"] is False
    assert spec["siteops_skill_card_write_allowed"] is False
    assert spec["agent_bus_enqueue_allowed"] is False
    assert spec["provider_api_call_allowed"] is False
    assert all(item.get("write_allowed") is False for item in spec["future_write_plan"] if "write_allowed" in item)
    assert any(item["step"] == "write_trusted_browser_skill" for item in spec["future_write_plan"])
    assert any(item["step"] == "write_siteops_skill_card" for item in spec["future_write_plan"])
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_gate_executor_spec_blocks_legacy_unbound_approval_before_gate_status(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    spec = candidate_promotion_gate_executor_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in spec["executor_preflight_checks"]}
    assert spec["executor_spec_status"] == "blocked_approval_provenance_not_bound"
    assert spec["executor_preflight_status"] == "blocked_approval_provenance_not_bound"
    assert spec["approval_provenance"]["provenance_status"] == "legacy_unbound"
    assert checks["approval_provenance_bound_match"]["passed"] is False
    assert spec["writes_performed"] is False
    assert spec["trusted_skill_write_allowed"] is False


def test_candidate_gate_allowlist_review_is_review_only_and_non_mutating(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    review = candidate_promotion_gate_allowlist_review(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in review["allowlist_review_checks"]}
    assert review["allowlist_review_status"] == "blocked_operation_already_allowlisted"
    assert review["executor_spec_status"] == "executor_spec_ready_gate_allowlisted_no_write"
    assert review["operation_currently_allowlisted"] is True
    assert checks["candidate_preflight_ready"]["passed"] is True
    assert checks["apply_contract_ready"]["passed"] is True
    assert checks["approval_provenance_bound_match"]["passed"] is True
    assert checks["target_paths_confined"]["passed"] is True
    assert checks["secret_session_exclusion_rechecked"]["passed"] is True
    assert review["secret_session_exclusion_recheck"]["passed"] is True
    assert checks["executor_implemented"]["passed"] is True
    assert checks["allowlist_policy_write_disabled"]["passed"] is True
    assert review["allowlist_entry_preview"]["policy_file"] == "runtime/policy/gateway_allowlists.json"
    assert review["allowlist_entry_preview"]["policy_file_write_performed"] is False
    assert review["review_decision"] == "do_not_allowlist_in_this_pass"
    assert review["allowlist_change_allowed"] is False
    assert review["allowlist_change_performed"] is False
    assert review["policy_file_write_allowed"] is False
    assert review["executor_enabled"] is True
    assert review["writes_performed"] is False
    assert review["trusted_skill_write_allowed"] is False
    assert review["siteops_skill_card_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_trusted_executor_design_is_design_only_and_non_mutating(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    design = candidate_promotion_trusted_executor_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in design["trusted_executor_design_checks"]}
    assert design["trusted_executor_design_status"] == "trusted_executor_design_ready_gate_allowlisted"
    assert design["allowlist_review_status"] == "blocked_operation_already_allowlisted"
    assert design["operation_currently_allowlisted"] is True
    assert checks["approval_bound_for_design"]["passed"] is True
    assert checks["target_paths_confined_for_design"]["passed"] is True
    assert checks["audit_sequence_defined"]["passed"] is True
    assert checks["rollback_plan_defined"]["passed"] is True
    assert checks["executor_implementation_disabled"]["passed"] is False
    assert design["executor_entrypoint_preview"]["status"] == "BUILT_GUARDED"
    assert design["executor_entrypoint_preview"]["callable"] is True
    assert any(item["component"] == "artifact_writer" for item in design["executor_components"])
    assert any(event["event_type"] == "trusted_executor_prewrite_validated" for event in design["audit_sequence"])
    assert any(item["case"] == "failure_after_partial_artifact_write" for item in design["rollback_plan"])
    assert "Gate operation not allowlisted blocks executor" in design["acceptance_tests_required"]
    assert design["executor_implemented"] is True
    assert design["executor_enabled"] is True
    assert design["executor_build_allowed"] is False
    assert design["executor_implementation_performed"] is True
    assert design["allowlist_change_performed"] is False
    assert design["policy_file_write_allowed"] is False
    assert design["writes_performed"] is False
    assert design["trusted_skill_write_allowed"] is False
    assert design["siteops_skill_card_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_trusted_executor_design_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    design = candidate_promotion_trusted_executor_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in design["trusted_executor_design_checks"]}
    assert design["trusted_executor_design_status"] == "blocked_pending_approval"
    assert design["allowlist_review_status"] == "blocked_pending_approval"
    assert checks["approval_bound_for_design"]["passed"] is True
    assert design["approval"]["status"] == "pending"
    assert design["executor_implemented"] is True
    assert design["executor_enabled"] is False
    assert design["executor_implementation_performed"] is True
    assert design["writes_performed"] is False
    assert design["trusted_skill_write_allowed"] is False
    assert design["siteops_skill_card_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_trusted_executor_design_blocks_legacy_unbound_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    design = candidate_promotion_trusted_executor_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in design["trusted_executor_design_checks"]}
    assert design["trusted_executor_design_status"] == "blocked_approval_provenance_not_bound"
    assert design["allowlist_review_status"] == "blocked_approval_provenance_not_bound"
    assert design["approval_provenance"]["provenance_status"] == "legacy_unbound"
    assert checks["approval_bound_for_design"]["passed"] is False
    assert design["executor_implemented"] is True
    assert design["executor_enabled"] is False
    assert design["executor_implementation_performed"] is True
    assert design["writes_performed"] is False
    assert design["trusted_skill_write_allowed"] is False
    assert design["siteops_skill_card_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_executor_review_checklist_is_no_write_and_gate_blocked(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    checklist = candidate_promotion_executor_review_checklist(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    gates = {item["gate_id"]: item for item in checklist["required_review_gates"]}
    steps = {item["step_id"]: item for item in checklist["implementation_review_steps"]}
    assert checklist["executor_review_status"] == "executor_review_checklist_ready_no_write_authority"
    assert checklist["trusted_executor_design_status"] == "trusted_executor_design_ready_gate_allowlisted"
    assert checklist["allowlist_review_status"] == "blocked_operation_already_allowlisted"
    assert checklist["review_decision"] == "do_not_implement_in_this_pass"
    assert checklist["operation_currently_allowlisted"] is True
    assert gates["approval_provenance_bound_match"]["status"] == "ready_for_review"
    assert gates["candidate_revalidation_before_write"]["blocks_execution"] is True
    assert gates["secret_session_exclusion_before_write"]["blocks_execution"] is True
    assert gates["gate_operation_allowlist"]["status"] == "ready_for_review"
    assert gates["inactive_activation_boundary"]["required"] is True
    assert steps["executor_entrypoint_review"]["implemented"] is True
    assert steps["gate_policy_review"]["decision"] == "do_not_allowlist_in_this_pass"
    assert "Gate operation remains denied until an approved policy change lands" in checklist["replacement_test_requirements"]
    assert "edit runtime/policy/gateway_allowlists.json" in checklist["blocked_actions"]
    assert checklist["executor_entrypoint_preview"]["function"] == "apply_trusted_candidate_artifacts"
    assert checklist["executor_entrypoint_preview"]["callable"] is True
    assert checklist["executor_implemented"] is True
    assert checklist["executor_enabled"] is True
    assert checklist["executor_build_allowed"] is False
    assert checklist["executor_implementation_allowed"] is False
    assert checklist["executor_implementation_performed"] is True
    assert checklist["allowlist_change_allowed"] is False
    assert checklist["allowlist_change_performed"] is False
    assert checklist["policy_file_write_allowed"] is False
    assert checklist["writes_performed"] is False
    assert checklist["trusted_skill_write_allowed"] is False
    assert checklist["siteops_skill_card_write_allowed"] is False
    assert checklist["browser_execution_allowed"] is False
    assert checklist["agent_bus_enqueue_allowed"] is False
    assert checklist["provider_api_call_allowed"] is False
    assert checklist["activation_allowed"] is False
    assert checklist["canonical_writeback_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_executor_review_checklist_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    checklist = candidate_promotion_executor_review_checklist(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert checklist["executor_review_status"] == "blocked_pending_approval"
    assert checklist["trusted_executor_design_status"] == "blocked_pending_approval"
    assert checklist["approval_status"] == "pending"
    assert checklist["review_decision"] == "do_not_implement_in_this_pass"
    assert checklist["executor_implemented"] is True
    assert checklist["executor_enabled"] is False
    assert checklist["writes_performed"] is False
    assert checklist["trusted_skill_write_allowed"] is False
    assert checklist["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_writes_scoped_approval_only_when_requested(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_candidate(siteops_vault)

    code = cli.main(
        [
            "siteops",
            "candidates",
            "request-promotion",
            "candidate_run_123",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--write-approval",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["approval_request_written"] is True
    assert result["scope"] == {"tenant_id": "local", "workspace_id": "default", "user_id": "local-user"}
    assert result["trusted_skill_write_allowed"] is False
    assert result["browser_execution_allowed"] is False

    apply_code = cli.main(
        [
            "siteops",
            "candidates",
            "apply-contract",
            "candidate_run_123",
            "--approval-id",
            result["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    apply_result = _payload(capsys.readouterr().out)
    assert apply_code == 0
    assert apply_result["apply_contract"]["apply_contract_status"] == "blocked_pending_approval"
    assert apply_result["writes_performed"] is False

    list_code = cli.main(
        [
            "siteops",
            "candidates",
            "approvals",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    list_result = _payload(capsys.readouterr().out)
    assert list_code == 0
    assert list_result["candidate_approval_count"] == 1
    listed = list_result["approvals"][0]
    assert listed["approval_id"] == result["approval"]["approval_id"]
    assert listed["approval_provenance"]["provenance_status"] == "bound_match"
    assert listed["writes_performed"] is False


def test_siteops_candidate_cli_gate_apply_design_is_non_mutating(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "gate-apply-design",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_apply_design_status"] == "gate_apply_design_ready_but_execution_disabled"
    assert result["gate_operation_allowed"] is True
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_gate_executor_spec_is_non_mutating(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "gate-executor-spec",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["executor_spec_status"] == "executor_spec_ready_gate_allowlisted_no_write"
    checks = {item["check_id"]: item for item in result["executor_preflight_checks"]}
    assert checks["approval_provenance_bound_match"]["passed"] is True
    assert checks["gate_operation_allowlisted"]["passed"] is True
    assert checks["executor_implemented"]["passed"] is True
    assert result["future_executor"]["implementation_status"] == "BUILT_GUARDED"
    assert result["executor_enabled"] is True
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_gate_allowlist_review_is_non_mutating(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "gate-allowlist-review",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["allowlist_review_status"] == "blocked_operation_already_allowlisted"
    assert result["operation_currently_allowlisted"] is True
    assert result["allowlist_change_performed"] is False
    assert result["policy_file_write_allowed"] is False
    assert result["executor_enabled"] is True
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_trusted_executor_design_is_non_mutating(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-executor-design",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["trusted_executor_design_status"] == "trusted_executor_design_ready_gate_allowlisted"
    assert result["allowlist_review_status"] == "blocked_operation_already_allowlisted"
    assert result["operation_currently_allowlisted"] is True
    assert result["executor_implemented"] is True
    assert result["executor_enabled"] is True
    assert result["executor_implementation_performed"] is True
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_executor_review_checklist_is_non_mutating(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "executor-review-checklist",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["executor_review_status"] == "executor_review_checklist_ready_no_write_authority"
    assert result["trusted_executor_design_status"] == "trusted_executor_design_ready_gate_allowlisted"
    assert result["review_decision"] == "do_not_implement_in_this_pass"
    assert result["operation_currently_allowlisted"] is True
    assert result["executor_implemented"] is True
    assert result["executor_enabled"] is True
    assert result["executor_implementation_allowed"] is False
    assert result["executor_implementation_performed"] is True
    assert result["allowlist_change_performed"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_executor_guard_entrypoint_is_guarded() -> None:
    _assert_guarded_executor_entrypoint()


def test_candidate_executor_guard_gate_operation_is_allowlisted_after_approval_patch() -> None:
    allowed, reason = check_runtime_operation(
        PROMOTION_GATE_APPLY_OPERATION,
        write_targets=[
            "runtime/browser_skills/skills/example.safe_candidate.yaml",
            "runtime/siteops/registry/skill_cards/example.safe_candidate.json",
        ],
    )

    assert allowed is True
    assert "allowed" in reason


def test_candidate_executor_guard_design_marks_entrypoint_built_but_gate_blocked(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    spec = candidate_promotion_gate_executor_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )
    review = candidate_promotion_gate_allowlist_review(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )
    design = candidate_promotion_trusted_executor_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert spec["future_executor"]["implementation_status"] == "BUILT_GUARDED"
    assert spec["executor_implemented"] is True
    assert spec["executor_enabled"] is True
    assert all(item["implemented"] is False for item in spec["future_write_plan"])
    assert all(
        item.get("write_allowed") is False
        for item in spec["future_write_plan"]
        if "write_allowed" in item
    )
    assert review["allowlist_change_performed"] is False
    assert review["policy_file_write_allowed"] is False
    assert design["executor_entrypoint_preview"]["function"] == "apply_trusted_candidate_artifacts"
    assert design["executor_entrypoint_preview"]["status"] == "BUILT_GUARDED"
    assert design["executor_entrypoint_preview"]["callable"] is True
    assert any(item["implemented"] is True for item in design["executor_components"])
    assert any(item["implemented"] is True for item in design["audit_sequence"])
    assert all(item["implemented"] is False for item in design["rollback_plan"])
    assert design["writes_performed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


# ── Pre-implementation verifier tests ──────────────────────────────────────────


def test_candidate_preimplementation_verifier_ready_for_patch_proposal(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With an approved, provenance-bound approval the verifier should return ready_for_patch_proposal."""
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    result = candidate_promotion_preimplementation_verifier(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in result["verifier_checks"]}
    assert result["ok"] is True
    assert result["verifier_verdict"] == "ready_for_patch_proposal"
    assert result["verifier_pass"] is True
    assert result["checklist_layer_pass"] is True
    assert result["checklist_status"] == "executor_review_checklist_ready_no_write_authority"
    # All five live guards must pass
    assert checks["gate_operation_currently_denied"]["passed"] is True
    assert checks["gate_operation_policy_state_acceptable"]["passed"] is True
    assert checks["executor_entrypoint_absent_or_guarded"]["passed"] is True
    assert checks["trusted_artifact_targets_absent"]["passed"] is True
    assert checks["guard_tests_present"]["passed"] is True
    assert checks["cli_contract_present"]["passed"] is True
    # Authority surface must be fully blocked
    assert result["writes_performed"] is False
    assert result["executor_implemented"] is True
    assert result["executor_enabled"] is False
    assert result["executor_build_allowed"] is False
    assert result["executor_implementation_allowed"] is False
    assert result["allowlist_change_allowed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False


def test_candidate_preimplementation_verifier_accepts_reviewed_gate_allowance(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After an approved Gate patch, the verifier should not block the inactive writer chain."""
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_gate_allowed_after_review"),
    )

    result = candidate_promotion_preimplementation_verifier(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in result["verifier_checks"]}
    assert result["verifier_verdict"] == "ready_for_patch_proposal"
    assert result["verifier_pass"] is True
    assert checks["gate_operation_currently_denied"]["passed"] is False
    assert checks["gate_operation_currently_denied"]["required"] is False
    assert checks["gate_operation_policy_state_acceptable"]["passed"] is True
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["activation_allowed"] is False
    assert result["browser_execution_allowed"] is False


def test_candidate_activation_approval_decision_consumer_design_ready_no_mutation(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    assert result["activation_approval_decision_consumer_design_status"] == (
        "activation_approval_decision_consumer_design_ready_no_mutation"
    )
    assert result["ready_for_activation_consumer_write_guard_next_pass"] is True
    assert result["activation_consumer_implemented"] is False
    assert result["activation_consumer_write_allowed_in_this_pass"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    marker = result["consumer_marker_preview"]
    assert marker["create_new_only"] is True
    assert marker["exact_once"] is True
    assert marker["written_in_this_pass"] is False
    assert not Path(marker["path"]).exists()
    schema = result["consumer_record_schema"]
    assert schema["activation_approval_id"] == activation_request["approval_id"]
    assert schema["source_approval_id"] == request["approval"]["approval_id"]
    assert schema["secret_values_visible"] is False
    assert schema["activation_performed"] is False
    assert any(item["step_id"] == "stop_before_activation_executor" for item in result["future_consumer_sequence"])
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_decision_consumer_design_blocks_pending(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )

    result = candidate_promotion_activation_approval_decision_consumer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    assert result["activation_approval_decision_consumer_design_status"].startswith(
        "blocked_activation_approval_decision_consumer_design_preflight"
    )
    assert result["ready_for_activation_consumer_write_guard_next_pass"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False
    assert not Path(result["consumer_marker_preview"]["path"]).exists()


def test_siteops_candidate_cli_activation_approval_decision_consumer_design_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-design",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_decision_consumer_design_status"] == (
        "activation_approval_decision_consumer_design_ready_no_mutation"
    )
    assert result["ready_for_activation_consumer_write_guard_next_pass"] is True
    assert result["activation_consumer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert not Path(result["consumer_marker_preview"]["path"]).exists()
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    # Trusted artifact targets remain absent
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_decision_consumer_write_guard_ready_no_write(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_write_guard_contract(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    contract = result["activation_consumer_write_guard_contract"]
    checks = {check["check_id"]: check for check in result["activation_consumer_write_guard_checks"]}
    assert result["activation_approval_decision_consumer_write_guard_status"] == (
        "activation_approval_decision_consumer_write_guard_ready_no_write"
    )
    assert result["ready_for_activation_consumer_writer_design_next_pass"] is True
    assert contract["explicit_write_flag"] == "--consume-activation-approval"
    assert contract["explicit_write_flag_supported_in_this_pass"] is False
    assert contract["requires_trusted_artifact_provenance_check"] is True
    assert contract["activation_executor_may_not_run_in_consumer"] is True
    assert checks["explicit_consume_flag_unsupported_this_pass"]["passed"] is True
    assert checks["consumer_marker_absent_before_future_write"]["passed"] is True
    assert checks["trusted_artifact_writes_forbidden_by_consumer"]["passed"] is True
    assert result["consume_activation_approval_flag_supported"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumer_audit_written"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False
    assert not Path(result["consumer_marker_preview"]["path"]).exists()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_decision_consumer_write_guard_blocks_pending(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )

    result = candidate_promotion_activation_approval_decision_consumer_write_guard_contract(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumer_write_guard_checks"]}
    assert result["activation_approval_decision_consumer_write_guard_status"] == (
        "blocked_activation_approval_decision_consumer_write_guard_preconditions"
    )
    assert result["ready_for_activation_consumer_writer_design_next_pass"] is False
    assert checks["consumer_design_ready"]["passed"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_approval_decision_consumer_write_guard_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-write-guard",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_decision_consumer_write_guard_status"] == (
        "activation_approval_decision_consumer_write_guard_ready_no_write"
    )
    assert result["ready_for_activation_consumer_writer_design_next_pass"] is True
    assert result["consume_activation_approval_flag_supported"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not Path(result["consumer_marker_preview"]["path"]).exists()


def test_siteops_candidate_cli_activation_approval_decision_consumer_write_guard_rejects_consume_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-write-guard",
            "candidate_run_123",
            "--source-approval-id",
            "approval_source",
            "--activation-approval-id",
            "approval_activation",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--consume-activation-approval",
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 1
    assert result["ok"] is False
    assert "--consume-activation-approval" in result["reason"]


def test_candidate_activation_approval_decision_consumer_writer_design_ready_no_mutation(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumer_writer_design_checks"]}
    write_set = result["activation_consumer_writer_write_set_preview"]
    rollback = result["activation_consumer_writer_rollback_contract"]
    assert result["activation_approval_decision_consumer_writer_design_status"] == (
        "activation_approval_decision_consumer_writer_design_ready_no_mutation"
    )
    assert result["ready_for_activation_consumer_writer_implementation_request_next_pass"] is True
    assert write_set["explicit_write_flag"] == "--consume-activation-approval"
    assert write_set["explicit_write_flag_supported_in_this_pass"] is False
    assert write_set["create_new_only"] is True
    assert write_set["append_only_audit"] is True
    assert rollback["rollback_required_before_future_write"] is True
    assert rollback["written_in_this_pass"] is False
    assert checks["future_writer_requires_explicit_consume_flag"]["passed"] is True
    assert checks["future_writer_marker_create_new_only"]["passed"] is True
    assert checks["future_writer_stops_before_activation_executor"]["passed"] is True
    assert result["future_writer_consume_activation_approval_flag_required"] is True
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False
    assert not Path(write_set["marker_path"]).exists()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_decision_consumer_writer_design_blocks_pending(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumer_writer_design_checks"]}
    assert result["activation_approval_decision_consumer_writer_design_status"] == (
        "blocked_activation_approval_decision_consumer_writer_design_preconditions"
    )
    assert result["ready_for_activation_consumer_writer_implementation_request_next_pass"] is False
    assert checks["write_guard_ready"]["passed"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_approval_decision_consumer_writer_design_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-writer-design",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_decision_consumer_writer_design_status"] == (
        "activation_approval_decision_consumer_writer_design_ready_no_mutation"
    )
    assert result["ready_for_activation_consumer_writer_implementation_request_next_pass"] is True
    assert result["future_writer_consume_activation_approval_flag_required"] is True
    assert result["consume_activation_approval_flag_supported"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not Path(result["activation_consumer_writer_write_set_preview"]["marker_path"]).exists()


def test_candidate_activation_approval_decision_consumer_writer_implementation_request_ready_no_write(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    request_packet = result["activation_consumer_writer_implementation_request"]
    checks = {check["check_id"]: check for check in result["activation_consumer_writer_implementation_request_checks"]}
    assert result["activation_approval_decision_consumer_writer_implementation_request_status"] == (
        "activation_approval_decision_consumer_writer_implementation_request_ready_no_write"
    )
    assert result["ready_for_activation_consumer_writer_implementation_approval_next_pass"] is True
    assert request_packet["request_type"] == "siteops_activation_consumer_writer_implementation_request"
    assert request_packet["future_explicit_write_flag"] == "--consume-activation-approval"
    assert request_packet["status"] == "review_packet_only"
    assert request_packet["writes_allowed_in_this_pass"] is False
    assert request_packet["approval_consumption_allowed_in_this_pass"] is False
    assert checks["writer_implementation_request_design_ready"]["passed"] is True
    assert checks["writer_implementation_request_future_consume_flag_required"]["passed"] is True
    assert checks["writer_implementation_request_write_set_preview_ready"]["passed"] is True
    assert checks["writer_implementation_request_no_writes_this_pass"]["passed"] is True
    assert result["implementation_request_artifact_written"] is False
    assert result["consume_activation_approval_flag_supported"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_consumer_audit_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False
    assert not Path(request_packet["future_write_set"]["marker_path"]).exists()


def test_candidate_activation_approval_decision_consumer_writer_implementation_request_blocks_pending(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumer_writer_implementation_request_checks"]}
    assert result["activation_approval_decision_consumer_writer_implementation_request_status"] == (
        "blocked_activation_approval_decision_consumer_writer_implementation_request_preconditions"
    )
    assert result["ready_for_activation_consumer_writer_implementation_approval_next_pass"] is False
    assert checks["writer_implementation_request_design_ready"]["passed"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_approval_decision_consumer_writer_implementation_request_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-writer-implementation-request",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_decision_consumer_writer_implementation_request_status"] == (
        "activation_approval_decision_consumer_writer_implementation_request_ready_no_write"
    )
    assert result["ready_for_activation_consumer_writer_implementation_approval_next_pass"] is True
    assert result["implementation_request_artifact_written"] is False
    assert result["consume_activation_approval_flag_supported"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_consumer_audit_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not Path(
        result["activation_consumer_writer_implementation_request"]["future_write_set"]["marker_path"]
    ).exists()


def test_siteops_candidate_cli_activation_approval_decision_consumer_writer_implementation_request_rejects_consume_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-writer-implementation-request",
            "candidate_run_123",
            "--source-approval-id",
            "approval_source",
            "--activation-approval-id",
            "approval_activation",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--consume-activation-approval",
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 1
    assert result["ok"] is False
    assert "--consume-activation-approval" in result["reason"]


def test_candidate_activation_approval_decision_consumer_writer_implementation_approval_approve_no_write(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        decision="approve",
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumer_writer_implementation_approval_checks"]}
    approval = result["activation_consumer_writer_implementation_approval"]
    assert result["activation_approval_decision_consumer_writer_implementation_approval_status"] == (
        "activation_approval_decision_consumer_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["implementation_approved_no_write"] is True
    assert result["ready_for_activation_consumer_writer_implementation_next_pass"] is True
    assert approval["decision"] == "approve"
    assert approval["durable_record_written"] is False
    assert approval["future_explicit_write_flag"] == "--consume-activation-approval"
    assert checks["writer_implementation_request_ready"]["passed"] is True
    assert checks["writer_implementation_approval_record_still_no_write"]["passed"] is True
    assert checks["writer_implementation_consume_flag_still_unsupported"]["passed"] is True
    assert result["implementation_approval_artifact_written"] is False
    assert result["consume_activation_approval_flag_supported"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_consumer_audit_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_approval_decision_consumer_writer_implementation_approval_reject_no_write(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        decision="reject",
        actor="local-user",
    )

    assert result["activation_approval_decision_consumer_writer_implementation_approval_status"] == (
        "activation_approval_decision_consumer_writer_implementation_rejected_no_write"
    )
    assert result["implementation_approved_no_write"] is False
    assert result["implementation_rejected_no_write"] is True
    assert result["ready_for_activation_consumer_writer_implementation_next_pass"] is False
    assert result["implementation_approval_artifact_written"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["approval_consumed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_approval_decision_consumer_writer_implementation_approval_blocks_pending(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        decision="approve",
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumer_writer_implementation_approval_checks"]}
    assert result["activation_approval_decision_consumer_writer_implementation_approval_status"].startswith(
        "blocked_activation_consumer_writer_implementation_request"
    )
    assert result["implementation_approved_no_write"] is False
    assert result["ready_for_activation_consumer_writer_implementation_next_pass"] is False
    assert checks["writer_implementation_request_ready"]["passed"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_approval_decision_consumer_writer_implementation_approval_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-writer-implementation-approval",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--decision",
            "approve",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_decision_consumer_writer_implementation_approval_status"] == (
        "activation_approval_decision_consumer_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["ready_for_activation_consumer_writer_implementation_next_pass"] is True
    assert result["implementation_approval_artifact_written"] is False
    assert result["consume_activation_approval_flag_supported"] is False
    assert result["activation_consumer_writer_implemented"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_consumer_audit_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_siteops_candidate_cli_activation_approval_decision_consumer_writer_implementation_approval_rejects_consume_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-writer-implementation-approval",
            "candidate_run_123",
            "--source-approval-id",
            "approval_source",
            "--activation-approval-id",
            "approval_activation",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--decision",
            "approve",
            "--consume-activation-approval",
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 1
    assert result["ok"] is False
    assert "--consume-activation-approval" in result["reason"]


def test_candidate_activation_approval_decision_consumer_writer_implementation_dry_run_ready(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumer_writer_checks"]}
    marker_path = Path(result["activation_consumer_marker_path"])
    assert result["activation_approval_decision_consumer_writer_implementation_status"] == (
        "activation_consumer_writer_ready_dry_run_no_write"
    )
    assert result["consume_activation_approval_flag_supported"] is True
    assert result["activation_consumer_writer_implemented"] is True
    assert result["activation_consumer_writer_ready_to_consume"] is True
    assert checks["activation_consumer_marker_absent_before_write"]["passed"] is True
    assert marker_path.exists() is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_consumer_audit_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_approval_decision_consumer_writer_implementation_consumes_once(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )

    marker_path = Path(result["activation_consumer_marker_ref"])
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    audit_path = Path(result["audit_ref"])
    run_path = Path(result["run_ref"])
    approval_payload = json.loads(Path(activation_request["approval_ref"]).read_text(encoding="utf-8"))
    assert result["activation_approval_decision_consumer_writer_implementation_status"] == (
        "activation_approval_consumed_marker_and_audit_written"
    )
    assert marker_path.exists() is True
    assert audit_path.exists() is True
    assert run_path.exists() is True
    assert len(audit_path.read_text(encoding="utf-8").splitlines()) == 2
    assert marker_payload["activation_approval_id"] == activation_request["approval_id"]
    assert marker_payload["trusted_artifacts_written"] is False
    assert marker_payload["activation_performed"] is False
    assert approval_payload["status"] == "approved"
    assert result["activation_consumption_marker_written"] is True
    assert result["activation_consumer_audit_written"] is True
    assert result["approval_consumed"] is True
    assert result["approval_decision_written"] is False
    assert result["approval_request_status_mutated"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_written"] is False
    assert result["browser_execution_allowed"] is False

    repeat = candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )

    assert repeat["activation_approval_decision_consumer_writer_implementation_status"].startswith(
        "blocked_activation_consumer_writer_implementation_approval"
    )
    assert repeat["activation_consumption_marker_written"] is False
    assert repeat["approval_consumed"] is False


def test_siteops_candidate_cli_activation_approval_decision_consumer_writer_implementation_consumes_marker_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-consumer-writer-implementation",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--consume-activation-approval",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_decision_consumer_writer_implementation_status"] == (
        "activation_approval_consumed_marker_and_audit_written"
    )
    assert result["activation_consumption_marker_written"] is True
    assert result["activation_consumer_audit_written"] is True
    assert result["approval_consumed"] is True
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_written"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_activation_consumption_live_readiness_blocks_missing_ids(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)

    result = candidate_promotion_activation_consumption_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_consumption_live_readiness_checks"]}
    assert result["activation_consumption_live_readiness_status"] == (
        "blocked_missing_source_promotion_approval_id"
    )
    assert checks["source_promotion_approval_id_present"]["passed"] is False
    assert result["writer_dry_run_ready"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_consumption_live_readiness_auto_discovers_ready_pair(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_consumption_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    assert result["activation_consumption_live_readiness_status"] == (
        "activation_consumption_live_readiness_ready_no_write"
    )
    assert result["source_approval_id"] == request["approval"]["approval_id"]
    assert result["activation_approval_id"] == activation_request["approval_id"]
    assert result["writer_dry_run_ready"] is True
    assert "--consume-activation-approval" in result["consume_command_preview"]
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_consumer_audit_written"] is False
    assert result["approval_consumed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_consumption_live_readiness_blocks_unknown_supplied_ids(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)

    result = candidate_promotion_activation_consumption_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
        source_approval_id="approval_missing_source",
        activation_approval_id="approval_missing_activation",
    )

    assert result["activation_consumption_live_readiness_status"] == (
        "blocked_unknown_source_promotion_approval_id"
    )
    assert result["writer_dry_run_error"] is not None
    assert result["writer_dry_run_ready"] is False
    assert result["approval_consumed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_consumption_live_readiness_ready_no_write(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-consumption-live-readiness",
            "candidate_run_123",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_consumption_live_readiness_status"] == (
        "activation_consumption_live_readiness_ready_no_write"
    )
    assert result["writer_dry_run_ready"] is True
    assert result["activation_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_performed"] is False


def _approved_activation_pair(siteops_vault: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    return request, activation_request


def _write_inactive_trusted_artifacts(siteops_vault: Path) -> None:
    payload = {
        "skill_id": "example.safe_candidate",
        "tenant_id": "local",
        "workspace_id": "default",
        "created_by": "local-user",
        "status": "inactive_review",
        "activation_allowed": False,
        "provenance": {
            "source": "test-fixture",
            "candidate_id": "candidate_run_123",
        },
    }
    browser_skill = siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml"
    skill_card = siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json"
    browser_skill.parent.mkdir(parents=True, exist_ok=True)
    skill_card.parent.mkdir(parents=True, exist_ok=True)
    browser_skill.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    skill_card.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _prepared_activation_executor_inputs(siteops_vault: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)
    return request, activation_request


def test_candidate_activation_executor_design_blocks_missing_marker(siteops_vault: Path) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)

    result = candidate_promotion_activation_executor_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_design_checks"]}
    assert result["activation_executor_design_status"] == "blocked_activation_consumption_marker_missing"
    assert checks["activation_consumption_marker_present"]["passed"] is False
    assert result["ready_for_activation_executor_preflight_next_pass"] is False
    assert result["activation_executor_implemented"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_activation_executor_design_ready_after_marker_and_inactive_artifacts(
    siteops_vault: Path,
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    consumed = candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    result = candidate_promotion_activation_executor_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_design_checks"]}
    assert consumed["activation_consumption_marker_written"] is True
    assert result["activation_executor_design_status"] == "activation_executor_design_ready_no_write"
    assert result["ready_for_activation_executor_preflight_next_pass"] is True
    assert checks["activation_consumption_marker_present"]["passed"] is True
    assert checks["inactive_trusted_artifacts_ready"]["passed"] is True
    assert result["future_activation_state_transition"]["explicit_future_flag"] == "--activate-trusted-artifact"
    assert result["future_activation_state_transition"]["browser_skill"]["to_status"] == "active_approved"
    assert all(item["ready_for_activation_design"] for item in result["trusted_artifact_posture"])
    assert result["activation_executor_implemented"] is False
    assert result["future_activate_trusted_artifact_flag_supported"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_siteops_candidate_cli_activation_executor_design_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-executor-design",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_executor_design_status"] == "activation_executor_design_ready_no_write"
    assert result["ready_for_activation_executor_preflight_next_pass"] is True
    assert result["activation_executor_implemented"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_activation_executor_preflight_blocks_until_design_ready(siteops_vault: Path) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)

    result = candidate_promotion_activation_executor_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_preflight_checks"]}
    assert result["activation_executor_preflight_status"] == "blocked_activation_executor_design_not_ready"
    assert result["activation_executor_design_status"] == "blocked_activation_consumption_marker_missing"
    assert checks["activation_executor_design_ready"]["passed"] is False
    assert result["ready_for_activation_executor_implementation_request_next_pass"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_executor_preflight_ready_no_write(
    siteops_vault: Path,
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    result = candidate_promotion_activation_executor_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_preflight_checks"]}
    activation_record = Path(result["future_activation_record"]["path"])
    assert result["activation_executor_preflight_status"] == "activation_executor_preflight_ready_no_write"
    assert result["ready_for_activation_executor_implementation_request_next_pass"] is True
    assert checks["activation_consumption_marker_valid"]["passed"] is True
    assert checks["inactive_trusted_artifacts_ready"]["passed"] is True
    assert checks["future_activation_record_absent_before_write"]["passed"] is True
    assert activation_record.exists() is False
    assert result["activate_trusted_artifact_flag_supported_in_this_pass"] is False
    assert result["activation_record_written"] is False
    assert result["activation_audit_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_executor_preflight_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-executor-preflight",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_executor_preflight_status"] == "activation_executor_preflight_ready_no_write"
    assert result["ready_for_activation_executor_implementation_request_next_pass"] is True
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_activation_executor_implementation_request_blocks_until_preflight_ready(
    siteops_vault: Path,
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)

    result = candidate_promotion_activation_executor_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_implementation_request_checks"]}
    assert result["activation_executor_implementation_request_status"] == (
        "blocked_activation_executor_implementation_request_preconditions"
    )
    assert result["activation_executor_preflight_status"] == "blocked_activation_executor_design_not_ready"
    assert checks["activation_executor_implementation_request_preflight_ready"]["passed"] is False
    assert result["ready_for_activation_executor_implementation_approval_next_pass"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_executor_implementation_request_ready_no_write(
    siteops_vault: Path,
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    result = candidate_promotion_activation_executor_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    request_packet = result["activation_executor_implementation_request"]
    assert result["activation_executor_implementation_request_status"] == (
        "activation_executor_implementation_request_ready_no_write"
    )
    assert result["ready_for_activation_executor_implementation_approval_next_pass"] is True
    assert request_packet["future_explicit_write_flag"] == "--activate-trusted-artifact"
    assert request_packet["future_write_set"]["activation_record_create_new_only"] is True
    assert request_packet["future_write_set"]["stop_before_browser_runtime"] is True
    assert request_packet["implementation_allowed_in_this_pass"] is False
    assert result["future_activate_trusted_artifact_flag_required"] is True
    assert result["activate_trusted_artifact_flag_supported_in_this_pass"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["activation_record_written"] is False
    assert result["activation_audit_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_executor_implementation_request_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-executor-implementation-request",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_executor_implementation_request_status"] == (
        "activation_executor_implementation_request_ready_no_write"
    )
    assert result["ready_for_activation_executor_implementation_approval_next_pass"] is True
    assert result["implementation_request_artifact_written"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_activation_executor_implementation_approval_blocks_until_request_ready(
    siteops_vault: Path,
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)

    result = candidate_promotion_activation_executor_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        decision="approve",
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_implementation_approval_checks"]}
    assert result["activation_executor_implementation_approval_status"].startswith(
        "blocked_activation_executor_implementation_request"
    )
    assert result["activation_executor_implementation_request_status"] == (
        "blocked_activation_executor_implementation_request_preconditions"
    )
    assert checks["activation_executor_implementation_request_ready"]["passed"] is False
    assert result["ready_for_activation_executor_implementation_next_pass"] is False
    assert result["implementation_approval_artifact_written"] is False
    assert result["approval_decision_written"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_executor_implementation_approval_approve_ready_no_write(
    siteops_vault: Path,
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    result = candidate_promotion_activation_executor_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        decision="approve",
        actor="local-user",
    )

    approval = result["activation_executor_implementation_approval"]
    assert result["activation_executor_implementation_approval_status"] == (
        "activation_executor_implementation_approved_for_next_pass_no_write"
    )
    assert result["activation_executor_implementation_approved_for_next_pass"] is True
    assert result["ready_for_activation_executor_implementation_next_pass"] is True
    assert approval["decision"] == "approve"
    assert approval["future_explicit_write_flag"] == "--activate-trusted-artifact"
    assert approval["durable_record_written"] is False
    assert result["implementation_approval_artifact_written"] is False
    assert result["approval_decision_written"] is False
    assert result["activation_record_written"] is False
    assert result["activation_audit_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_executor_implementation_approval_reject_ready_no_write(
    siteops_vault: Path,
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    result = candidate_promotion_activation_executor_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        decision="reject",
        actor="local-user",
    )

    assert result["activation_executor_implementation_approval_status"] == (
        "activation_executor_implementation_rejected_no_write"
    )
    assert result["activation_executor_implementation_rejected"] is True
    assert result["ready_for_activation_executor_implementation_next_pass"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_executor_implementation_approval_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    _write_inactive_trusted_artifacts(siteops_vault)

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-executor-implementation-approval",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--decision",
            "approve",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_executor_implementation_approval_status"] == (
        "activation_executor_implementation_approved_for_next_pass_no_write"
    )
    assert result["ready_for_activation_executor_implementation_next_pass"] is True
    assert result["implementation_approval_artifact_written"] is False
    assert result["approval_decision_written"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_activation_executor_implementation_ready_dry_run_requires_explicit_flag(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_activation_executor_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        activate_trusted_artifact=False,
    )

    checks = {check["check_id"]: check for check in result["activation_executor_checks"]}
    assert result["activation_executor_implementation_status"] == "activation_executor_ready_dry_run_no_write"
    assert result["activate_trusted_artifact_flag_supported"] is True
    assert result["activation_executor_ready_to_activate"] is True
    assert checks["activation_executor_requires_explicit_activate_flag"]["passed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["writes_performed"] is False
    assert not Path(result["activation_record_path"]).exists()


def test_candidate_activation_executor_implementation_blocks_gate_denied_with_explicit_flag(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_activation_executor_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        activate_trusted_artifact=True,
    )

    assert result["activation_executor_implementation_status"] == "blocked_activation_gate_operation_not_allowlisted"
    assert result["gate_operation_allowed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_executor_implementation_activates_local_artifacts_and_stops_before_runtime(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_activation_executor_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        reason="activate reviewed local artifacts",
        activate_trusted_artifact=True,
    )

    browser_skill = siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml"
    skill_card = siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json"
    browser_payload, browser_error = candidate_promotions_module._load_activation_artifact(browser_skill)
    card_payload, card_error = candidate_promotions_module._load_activation_artifact(skill_card)
    activation_record = json.loads(Path(result["activation_record_ref"]).read_text(encoding="utf-8"))
    audit_events = [
        json.loads(line)
        for line in Path(result["audit_ref"]).read_text(encoding="utf-8").splitlines()
    ]

    assert result["activation_executor_implementation_status"] == "trusted_artifacts_activated_stop_before_runtime"
    assert result["activation_record_written"] is True
    assert result["activation_audit_written"] is True
    assert result["activation_performed"] is True
    assert result["trusted_artifacts_mutated"] is True
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert browser_error is None
    assert card_error is None
    assert browser_payload["status"] == "active_approved"
    assert card_payload["status"] == "active_approved"
    assert browser_payload["activation_allowed"] is True
    assert card_payload["activation_allowed"] is True
    assert activation_record["browser_execution_performed"] is False
    assert activation_record["canonical_writeback_performed"] is False
    assert any(event["event_type"] == "activation_executor_prewrite" for event in audit_events)
    assert any(event["event_type"] == "activation_executor_postwrite" for event in audit_events)


def test_siteops_candidate_cli_activation_executor_implementation_can_activate_with_explicit_flag(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-executor-implementation",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--activate-trusted-artifact",
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_executor_implementation_status"] == "trusted_artifacts_activated_stop_before_runtime"
    assert result["activation_record_written"] is True
    assert result["activation_performed"] is True
    assert result["trusted_artifacts_mutated"] is True
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert Path(result["activation_record_ref"]).exists()


def test_candidate_activation_executor_live_readiness_blocks_without_approval_ids(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)

    result = candidate_promotion_activation_executor_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_live_readiness_checks"]}
    assert result["activation_executor_live_readiness_status"].startswith(
        "blocked_activation_consumption_live_readiness"
    )
    assert checks["activation_consumption_live_readiness_ready"]["passed"] is False
    assert result["activation_executor_dry_run_ready"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_executor_live_readiness_reports_gate_denied_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_activation_executor_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    assert result["activation_executor_live_readiness_status"] == (
        "blocked_activation_gate_operation_not_allowlisted"
    )
    assert result["activation_executor_dry_run_status"] == "blocked_activation_gate_operation_not_allowlisted"
    assert result["gate_operation_allowed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["writes_performed"] is False


def test_candidate_activation_executor_live_readiness_ready_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_activation_executor_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_executor_live_readiness_checks"]}
    assert result["activation_executor_live_readiness_status"] == (
        "activation_executor_live_readiness_ready_no_write"
    )
    assert result["activation_executor_dry_run_status"] == "activation_executor_ready_dry_run_no_write"
    assert result["activation_executor_dry_run_ready"] is True
    assert result["gate_operation_allowed"] is True
    assert "--activate-trusted-artifact" in result["activate_command_preview"]
    assert checks["readiness_pass_is_no_write"]["passed"] is True
    assert result["activation_record_path"]
    assert Path(result["activation_record_path"]).exists() is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False


def test_candidate_activation_gate_live_readiness_reports_exact_policy_delta_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    _write_gate_policy_application_preflight_files(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_activation_gate_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["activation_gate_live_readiness_checks"]}
    preview = result["policy_patch_preview"]
    runtime_entry = preview["runtime_operation_entry"][
        "siteops.browser_skill_candidate.activate_trusted_artifact"
    ]

    assert result["activation_gate_live_readiness_status"] == (
        "activation_gate_live_readiness_ready_for_policy_patch_no_write"
    )
    assert result["ready_for_activation_gate_policy_patch_plan"] is True
    assert result["gate_operation_allowed"] is False
    assert result["activation_gate_policy_patch_required"] is True
    assert preview["target_files"] == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    assert preview["exact_two_file_patch_required"] is True
    assert runtime_entry["allow_cli_operator"] is True
    assert "siteops_activation_records" in runtime_entry["write_target_categories"]
    assert result["required_write_categories"]["siteops_activation_records"] == [
        "07_LOGS/SiteOps-Activations/**"
    ]
    assert set(result["missing_or_different_write_categories"]) == {
        "browser_skills_inactive_review",
        "siteops_skill_cards_inactive_review",
        "siteops_activation_records",
    }
    assert checks["activation_evidence_ready_except_gate"]["passed"] is True
    assert checks["activation_executor_blocked_only_by_gate"]["passed"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_activation_gate_live_readiness_reports_already_allowlisted_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    _write_gate_policy_application_preflight_files(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_activation_gate_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    assert result["activation_gate_live_readiness_status"] == (
        "activation_gate_live_readiness_already_allowlisted_no_write"
    )
    assert result["ready_for_activation_executor_readiness_retry"] is True
    assert result["ready_for_activation_gate_policy_patch_plan"] is False
    assert result["gate_operation_allowed"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False


def _write_activation_gate_policy_patch_writer_preflight_files(
    vault: Path,
) -> tuple[Path, Path]:
    runtime_policy = vault / "runtime" / "chaseos_gate.py"
    gateway_allowlists = vault / "runtime" / "policy" / "gateway_allowlists.json"
    runtime_policy.parent.mkdir(parents=True, exist_ok=True)
    gateway_allowlists.parent.mkdir(parents=True, exist_ok=True)
    runtime_policy.write_text(
        'RUNTIME_OPERATION_POLICIES = {\n'
        '    "siteops.browser_skill_candidate.apply_trusted_artifacts": {\n'
        '        "allow_cli_operator": True,\n'
        '        "gateway_write_categories": [\n'
        '            "browser_skills_inactive_review",\n'
        '            "siteops_skill_cards_inactive_review",\n'
        "        ],\n"
        '        "write_target_categories": [\n'
        '            "browser_skills_inactive_review",\n'
        '            "siteops_skill_cards_inactive_review",\n'
        "        ],\n"
        "    },\n"
        "}\n",
        encoding="utf-8",
    )
    gateway_allowlists.write_text(
        json.dumps(
            {
                "write_targets": {
                    "browser_skills_inactive_review": [
                        "runtime/browser_skills/skills/*.yaml",
                    ],
                    "siteops_skill_cards_inactive_review": [
                        "runtime/siteops/registry/skill_cards/*.json",
                    ],
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_policy, gateway_allowlists


def test_candidate_activation_gate_policy_patch_writer_dry_run_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    runtime_policy, gateway_allowlists = _write_activation_gate_policy_patch_writer_preflight_files(
        siteops_vault
    )
    before_runtime = runtime_policy.read_text(encoding="utf-8")
    before_allowlists = gateway_allowlists.read_text(encoding="utf-8")
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_activation_gate_policy_patch_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = result["activation_gate_policy_patch_writer_checks"]
    assert result["activation_gate_policy_patch_writer_implementation_status"] == (
        "activation_gate_policy_patch_writer_ready_dry_run"
    )
    assert result["write_preconditions_ready"] is True
    assert checks["activation_gate_live_readiness_ready"]["passed"] is True
    assert checks["activation_approval_targets_candidate_and_source"]["passed"] is True
    assert checks["apply_activation_gate_policy_patch_flag_present"]["passed"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["backup_artifact_written"] is False
    assert result["writes_performed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == before_runtime
    assert gateway_allowlists.read_text(encoding="utf-8") == before_allowlists


def test_candidate_activation_gate_policy_patch_writer_applies_minimal_gate_patch(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    runtime_policy, gateway_allowlists = _write_activation_gate_policy_patch_writer_preflight_files(
        siteops_vault
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_activation_gate_policy_patch_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        apply_activation_gate_policy_patch=True,
    )

    patched_runtime = runtime_policy.read_text(encoding="utf-8")
    patched_allowlists = json.loads(gateway_allowlists.read_text(encoding="utf-8"))
    rollback_ref = siteops_vault / result["backup_artifact_paths"]["rollback_audit"]

    assert result["activation_gate_policy_patch_writer_implementation_status"] == (
        "activation_gate_policy_patch_writer_implementation_applied"
    )
    assert result["write_preconditions_ready"] is True
    assert result["gate_policy_change_performed"] is True
    assert result["allowlist_change_performed"] is True
    assert result["backup_artifact_written"] is True
    assert result["rollback_audit_artifact_written"] is True
    assert result["writes_performed"] is True
    assert result["files_modified"] is True
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert '"siteops.browser_skill_candidate.activate_trusted_artifact"' in patched_runtime
    assert patched_runtime.count('"siteops.browser_skill_candidate.activate_trusted_artifact"') == 1
    assert patched_allowlists["write_targets"]["siteops_activation_records"] == [
        "07_LOGS/SiteOps-Activations/**"
    ]
    assert result["post_apply_verification"]["runtime_policy_compiles"] is True
    assert result["post_apply_verification"]["gateway_allowlists_parses"] is True
    assert rollback_ref.exists() is True
    assert json.loads(rollback_ref.read_text(encoding="utf-8"))["rollback_performed"] is False


def test_siteops_candidate_cli_activation_gate_policy_patch_writer_dry_run_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    _write_activation_gate_policy_patch_writer_preflight_files(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-gate-policy-patch-writer-implementation",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_gate_policy_patch_writer_implementation_status"] == (
        "activation_gate_policy_patch_writer_ready_dry_run"
    )
    assert result["write_preconditions_ready"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_gate_live_readiness_is_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    _write_gate_policy_application_preflight_files(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-gate-live-readiness",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_gate_live_readiness_status"] == (
        "activation_gate_live_readiness_ready_for_policy_patch_no_write"
    )
    assert result["ready_for_activation_gate_policy_patch_plan"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_activation_executor_live_readiness_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-executor-live-readiness",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_executor_live_readiness_status"] == (
        "activation_executor_live_readiness_ready_no_write"
    )
    assert result["activation_executor_dry_run_ready"] is True
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_live_activation_evidence_closeout_blocks_missing_approval_ids(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)

    result = candidate_promotion_live_activation_evidence_closeout(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    evidence = {item["evidence_key"]: item for item in result["evidence_items"]}
    assert result["live_activation_evidence_closeout_status"] == "blocked_live_activation_evidence_chain"
    assert result["backend_activation_ready"] is False
    assert result["feature_done"] is False
    assert evidence["source_promotion_approval_id"]["status"] == "missing"
    assert "source_promotion_approval_id" in result["remaining_backend_activation_blockers"]
    assert "browser_replay_shadow_mode" in result["remaining_feature_blockers"]
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_live_activation_evidence_closeout_reports_gate_denied(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_live_activation_evidence_closeout(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    evidence = {item["evidence_key"]: item for item in result["evidence_items"]}
    assert result["live_activation_evidence_closeout_status"] == "blocked_live_activation_evidence_chain"
    assert result["backend_activation_ready"] is False
    assert result["gate_operation_allowed"] is False
    assert evidence["activation_gate_allowance"]["status"] == "missing_or_denied"
    assert "activation_gate_allowance" in result["remaining_backend_activation_blockers"]
    assert result["writes_performed"] is False
    assert result["activation_performed"] is False


def test_candidate_live_activation_evidence_closeout_reports_missing_inactive_artifacts(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _approved_activation_pair(siteops_vault)
    candidate_promotion_activation_approval_decision_consumer_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        consume_activation_approval=True,
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_live_activation_evidence_closeout(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    evidence = {item["evidence_key"]: item for item in result["evidence_items"]}
    summary = result["readiness_check_summary"]
    assert evidence["activation_consumption_marker"]["status"] == "satisfied"
    assert evidence["inactive_trusted_browser_skill"]["status"] == "missing_or_invalid"
    assert evidence["inactive_siteops_skill_card"]["status"] == "missing_or_invalid"
    assert "inactive_trusted_browser_skill" in result["remaining_backend_activation_blockers"]
    assert "inactive_siteops_skill_card" in result["remaining_backend_activation_blockers"]
    assert summary["activation_executor_artifacts_still_inactive_and_secret_free"]["passed"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["writes_performed"] is False


def test_candidate_live_activation_evidence_closeout_ready_backend_but_feature_not_done(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_live_activation_evidence_closeout(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    evidence = {item["evidence_key"]: item for item in result["evidence_items"]}
    assert result["live_activation_evidence_closeout_status"] == (
        "live_activation_evidence_ready_for_operator_activation_no_write"
    )
    assert result["backend_activation_ready"] is True
    assert result["feature_done"] is False
    assert result["browser_replay_built"] is False
    assert result["remaining_backend_activation_blockers"] == []
    assert result["remaining_feature_blockers"] == ["browser_replay_shadow_mode"]
    assert evidence["activation_executor_dry_run"]["status"] == "satisfied"
    assert evidence["browser_replay_shadow_mode"]["status"] == "not_built"
    assert "--activate-trusted-artifact" in result["activate_command_preview"]
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_live_activation_evidence_closeout_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "live-activation-evidence-closeout",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["backend_activation_ready"] is True
    assert result["feature_done"] is False
    assert result["browser_replay_built"] is False
    assert result["activation_record_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_browser_skill_shadow_replay_design_blocks_before_backend_ready(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)

    result = candidate_promotion_browser_skill_shadow_replay_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["browser_skill_shadow_replay_design_checks"]}
    assert result["browser_skill_shadow_replay_design_status"] == (
        "blocked_browser_skill_shadow_replay_design_activation_evidence"
    )
    assert result["backend_activation_ready"] is False
    assert result["ready_for_shadow_replay_implementation_request_next_pass"] is False
    assert checks["activation_backend_ready"]["passed"] is False
    assert "source_promotion_approval_id" in result["remaining_backend_activation_blockers"]
    assert result["shadow_mode_required"] is True
    assert result["shadow_mode_built"] is False
    assert result["browser_replay_built"] is False
    assert result["browser_execution_allowed"] is False
    assert result["browser_launch_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_design_ready_no_execution(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["browser_skill_shadow_replay_design_checks"]}
    assert result["browser_skill_shadow_replay_design_status"] == (
        "browser_skill_shadow_replay_design_ready_no_execution"
    )
    assert result["review_decision"] == "ready_for_shadow_replay_implementation_request_next_pass"
    assert result["backend_activation_ready"] is True
    assert result["ready_for_shadow_replay_implementation_request_next_pass"] is True
    assert result["remaining_backend_activation_blockers"] == []
    assert result["remaining_feature_blockers"] == ["browser_replay_shadow_mode"]
    assert checks["only_browser_replay_shadow_mode_remaining"]["passed"] is True
    assert "browser-skill-shadow-replay-implementation-request" in result[
        "future_shadow_replay_implementation_request_command_preview"
    ]
    assert result["shadow_mode_required"] is True
    assert result["shadow_mode_built"] is False
    assert result["browser_replay_built"] is False
    assert result["activation_write_required_in_this_pass"] is False
    assert result["future_replay_may_require_active_trusted_artifact_or_activation_ready_evidence"] is True
    assert result["browser_execution_allowed"] is False
    assert result["browser_launch_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["cookie_or_token_access_allowed"] is False
    assert result["dom_mutation_allowed"] is False
    assert result["external_submit_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_replay_design_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-replay-design",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_replay_design_status"] == (
        "browser_skill_shadow_replay_design_ready_no_execution"
    )
    assert result["backend_activation_ready"] is True
    assert result["ready_for_shadow_replay_implementation_request_next_pass"] is True
    assert result["shadow_mode_required"] is True
    assert result["browser_replay_built"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_browser_skill_shadow_replay_implementation_request_blocks_before_design_ready(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_implementation_request_checks"]}
    assert result["browser_skill_shadow_replay_implementation_request_status"] == (
        "blocked_browser_skill_shadow_replay_implementation_request"
    )
    assert result["ready_for_shadow_replay_implementation_approval_next_pass"] is False
    assert result["backend_activation_ready"] is False
    assert checks["shadow_replay_design_ready"]["passed"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["browser_run_log_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_implementation_request_ready_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_implementation_request_checks"]}
    request_packet = result["shadow_replay_implementation_request"]
    future_write_set = result["future_write_set"]
    assert result["browser_skill_shadow_replay_implementation_request_status"] == (
        "browser_skill_shadow_replay_implementation_request_ready_no_write"
    )
    assert result["ready_for_shadow_replay_implementation_approval_next_pass"] is True
    assert result["backend_activation_ready"] is True
    assert checks["shadow_replay_design_ready"]["passed"] is True
    assert checks["future_write_set_declared"]["passed"] is True
    assert checks["request_pass_is_no_write_no_browser"]["passed"] is True
    assert request_packet["request_type"] == "siteops_browser_skill_shadow_replay_implementation_request"
    assert request_packet["future_required_mode"] == "shadow"
    assert "--shadow-mode" in request_packet["future_required_flags"]
    assert future_write_set["browser_run_log_path"].startswith("07_LOGS/Browser-Runs/")
    assert future_write_set["browser_skill_ref"] == "runtime/browser_skills/skills/example.safe_candidate.yaml"
    assert "cookie" in request_packet["record_schema"]["forbidden_fields"]
    assert result["implementation_request_artifact_written"] is False
    assert result["browser_run_log_written"] is False
    assert result["agent_activity_log_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["browser_launch_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["cookie_or_token_access_allowed"] is False
    assert result["dom_mutation_allowed"] is False
    assert result["external_submit_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["gate_policy_mutation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_replay_implementation_request_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-replay-implementation-request",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_replay_implementation_request_status"] == (
        "browser_skill_shadow_replay_implementation_request_ready_no_write"
    )
    assert result["ready_for_shadow_replay_implementation_approval_next_pass"] is True
    assert result["backend_activation_ready"] is True
    assert result["implementation_request_artifact_written"] is False
    assert result["browser_run_log_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_implementation_approval_blocks_before_request_ready(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        decision="approve",
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_implementation_approval_checks"]}
    assert result["browser_skill_shadow_replay_implementation_approval_status"].startswith(
        "blocked_shadow_replay_implementation_request"
    )
    assert result["ready_for_shadow_replay_implementation_next_pass"] is False
    assert checks["shadow_replay_implementation_request_ready"]["passed"] is False
    assert result["implementation_approval_artifact_written"] is False
    assert result["browser_run_log_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_implementation_approval_approve_ready_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        decision="approve",
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_implementation_approval_checks"]}
    approval = result["shadow_replay_implementation_approval"]
    assert result["browser_skill_shadow_replay_implementation_approval_status"] == (
        "shadow_replay_implementation_approved_for_next_pass_no_write"
    )
    assert result["shadow_replay_implementation_approved_for_next_pass"] is True
    assert result["ready_for_shadow_replay_implementation_next_pass"] is True
    assert checks["shadow_replay_implementation_request_ready"]["passed"] is True
    assert checks["shadow_replay_implementation_approval_record_still_no_write"]["passed"] is True
    assert approval["record_type"] == "siteops_browser_skill_shadow_replay_implementation_approval"
    assert approval["approval_id"] != approval["implementation_request_id"]
    assert approval["future_required_mode"] == "shadow"
    assert approval["future_write_set"]["browser_run_log_path"].startswith("07_LOGS/Browser-Runs/")
    assert approval["durable_record_written"] is False
    assert result["implementation_approval_artifact_written"] is False
    assert result["browser_run_log_written"] is False
    assert result["agent_activity_log_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["browser_launch_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["cookie_or_token_access_allowed"] is False
    assert result["dom_mutation_allowed"] is False
    assert result["external_submit_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["gate_policy_mutation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_implementation_approval_reject_ready_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        decision="reject",
    )

    assert result["browser_skill_shadow_replay_implementation_approval_status"] == (
        "shadow_replay_implementation_rejected_no_write"
    )
    assert result["shadow_replay_implementation_rejected"] is True
    assert result["ready_for_shadow_replay_implementation_next_pass"] is False
    assert result["implementation_approval_artifact_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_replay_implementation_approval_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-replay-implementation-approval",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--decision",
            "approve",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_replay_implementation_approval_status"] == (
        "shadow_replay_implementation_approved_for_next_pass_no_write"
    )
    assert result["ready_for_shadow_replay_implementation_next_pass"] is True
    assert result["implementation_approval_artifact_written"] is False
    assert result["browser_run_log_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_runner_write_guard_blocks_before_approval(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_activation_gate_denied"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_runner_write_guard(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_runner_write_guard_checks"]}
    assert result["browser_skill_shadow_replay_runner_write_guard_status"] == (
        "blocked_shadow_replay_runner_write_guard"
    )
    assert result["ready_for_shadow_replay_runner_implementation_next_pass"] is False
    assert checks["shadow_replay_implementation_approved_no_write"]["passed"] is False
    assert result["shadow_replay_runner_write_guard_artifact_written"] is False
    assert result["shadow_replay_runner_implemented"] is False
    assert result["browser_run_log_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_runner_write_guard_ready_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_runner_write_guard(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_runner_write_guard_checks"]}
    guard = result["shadow_replay_runner_write_guard"]
    assert result["browser_skill_shadow_replay_runner_write_guard_status"] == (
        "shadow_replay_runner_write_guard_ready_no_write"
    )
    assert result["review_decision"] == "ready_for_shadow_replay_runner_implementation_next_pass"
    assert result["ready_for_shadow_replay_runner_implementation_next_pass"] is True
    assert checks["shadow_replay_implementation_approved_no_write"]["passed"] is True
    assert checks["future_write_targets_scoped_to_logs_and_candidate_evidence"]["passed"] is True
    assert guard["contract_type"] == "siteops_browser_skill_shadow_replay_runner_write_guard"
    assert guard["durable_contract_written"] is False
    assert "07_LOGS/Browser-Runs/" in guard["allowed_future_write_targets"][0]
    assert "runtime/chaseos_gate.py" in guard["forbidden_future_write_targets"]
    assert "--shadow-mode" in guard["future_required_flags"]
    assert result["shadow_replay_runner_write_guard_artifact_written"] is False
    assert result["shadow_replay_runner_implemented"] is False
    assert result["browser_replay_built"] is False
    assert result["browser_run_log_written"] is False
    assert result["agent_activity_log_written"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_mutated"] is False
    assert result["browser_execution_allowed"] is False
    assert result["browser_launch_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["cookie_or_token_access_allowed"] is False
    assert result["dom_mutation_allowed"] is False
    assert result["external_submit_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["gate_policy_mutation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_replay_runner_write_guard_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-replay-runner-write-guard",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_replay_runner_write_guard_status"] == (
        "shadow_replay_runner_write_guard_ready_no_write"
    )
    assert result["ready_for_shadow_replay_runner_implementation_next_pass"] is True
    assert result["shadow_replay_runner_write_guard_artifact_written"] is False
    assert result["shadow_replay_runner_implemented"] is False
    assert result["browser_run_log_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_runner_implementation_dry_run_ready_no_browser(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="http://localhost:8765/shadow",
        shadow_mode=True,
        local_target_only=True,
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_runner_dry_run_checks"]}
    assert result["browser_skill_shadow_replay_runner_dry_run_status"] == (
        "shadow_replay_runner_dry_run_ready_no_browser"
    )
    assert result["review_decision"] == "ready_for_shadow_replay_runner_write_pass_next"
    assert result["ready_for_shadow_replay_runner_write_pass_next"] is True
    assert result["runner_dry_run_shell_built"] is True
    assert result["shadow_replay_runner_implemented"] is False
    assert result["browser_replay_built"] is False
    assert checks["shadow_replay_runner_write_guard_ready"]["passed"] is True
    assert checks["shadow_mode_flag_present"]["passed"] is True
    assert checks["target_url_local_or_allowlisted"]["passed"] is True
    assert result["browser_run_preview"]["artifact_written"] is False
    assert result["browser_run_log_written"] is False
    assert result["runner_dry_run_artifact_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["browser_launch_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["cookie_or_token_access_allowed"] is False
    assert result["dom_mutation_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_runner_implementation_dry_run_rejects_write_flag(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="http://localhost:8765/shadow",
        shadow_mode=True,
        write_browser_run_log=True,
        local_target_only=True,
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_runner_dry_run_checks"]}
    assert result["browser_skill_shadow_replay_runner_dry_run_status"] == (
        "blocked_write_browser_run_log_not_supported_in_dry_run"
    )
    assert checks["write_browser_run_log_flag_not_used"]["passed"] is False
    assert result["write_browser_run_log_requested"] is True
    assert result["ready_for_shadow_replay_runner_write_pass_next"] is False
    assert result["browser_run_log_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_runner_implementation_dry_run_blocks_non_allowlisted_target(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="https://example.com/shadow",
        shadow_mode=True,
        local_target_only=True,
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_runner_dry_run_checks"]}
    assert result["browser_skill_shadow_replay_runner_dry_run_status"] == (
        "blocked_shadow_replay_runner_dry_run"
    )
    assert checks["target_url_local_or_allowlisted"]["passed"] is False
    assert result["target_policy_reason"] == "non_local_target_blocked_by_local_target_only"
    assert result["browser_execution_allowed"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_replay_runner_implementation_dry_run_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-replay-runner-implementation-dry-run",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_replay_runner_dry_run_status"] == (
        "shadow_replay_runner_dry_run_ready_no_browser"
    )
    assert result["ready_for_shadow_replay_runner_write_pass_next"] is True
    assert result["runner_dry_run_shell_built"] is True
    assert result["browser_run_log_written"] is False
    assert result["runner_dry_run_artifact_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_runner_write_pass_ready_no_write_without_flag(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="http://localhost:8765/shadow",
        shadow_mode=True,
        local_target_only=True,
    )

    checks = {check["check_id"]: check for check in result["shadow_replay_runner_write_pass_checks"]}
    assert result["browser_skill_shadow_replay_runner_write_pass_status"] == (
        "shadow_replay_runner_write_pass_ready_no_write"
    )
    assert checks["explicit_write_browser_run_log_flag_present"]["passed"] is False
    assert result["write_browser_run_log_requested"] is False
    assert result["browser_run_log_written"] is False
    assert result["agent_activity_log_written"] is False
    assert result["candidate_evidence_written"] is False
    assert result["ready_for_replay_evidence_review_next"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_runner_write_pass_writes_scoped_untrusted_evidence(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    result = candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="http://localhost:8765/shadow",
        shadow_mode=True,
        write_browser_run_log=True,
        local_target_only=True,
    )

    assert result["browser_skill_shadow_replay_runner_write_pass_status"] == (
        "shadow_replay_runner_write_pass_evidence_written_no_browser"
    )
    assert result["browser_run_log_written"] is True
    assert result["agent_activity_log_written"] is True
    assert result["candidate_evidence_written"] is True
    assert result["ready_for_replay_evidence_review_next"] is True
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is True

    browser_run_path = Path(result["browser_run_ref"])
    agent_activity_path = Path(result["agent_activity_ref"])
    candidate_evidence_path = Path(result["candidate_evidence_ref"])
    assert browser_run_path.is_file()
    assert agent_activity_path.is_file()
    assert candidate_evidence_path.is_file()
    assert siteops_vault in browser_run_path.parents
    assert siteops_vault in agent_activity_path.parents
    assert siteops_vault in candidate_evidence_path.parents

    browser_run = json.loads(browser_run_path.read_text(encoding="utf-8"))
    assert browser_run["browser_execution_performed"] is False
    assert browser_run["cdp_connection_performed"] is False
    assert browser_run["trusted_evidence"] is False
    assert browser_run["untrusted_until_review"] is True
    assert "Browser-Skill-Candidates/" in browser_run["artifacts_ref"]
    assert "untrusted" in candidate_evidence_path.read_text(encoding="utf-8").lower()


def test_candidate_browser_skill_shadow_replay_runner_write_pass_blocks_existing_evidence(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "write_browser_run_log": True,
        "local_target_only": True,
    }

    first = candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123", siteops_vault, **kwargs
    )
    second = candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123", siteops_vault, **kwargs
    )

    assert first["browser_run_log_written"] is True
    assert second["browser_skill_shadow_replay_runner_write_pass_status"] == (
        "blocked_shadow_replay_runner_write_pass_existing_evidence"
    )
    assert second["browser_run_log_written"] is False
    assert second["agent_activity_log_written"] is False
    assert second["candidate_evidence_written"] is False
    assert second["writes_performed"] is False
    assert second["browser_execution_allowed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_replay_runner_write_pass_read_only_without_flag(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-replay-runner-write-pass",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_replay_runner_write_pass_status"] == (
        "shadow_replay_runner_write_pass_ready_no_write"
    )
    assert result["browser_run_log_written"] is False
    assert result["agent_activity_log_written"] is False
    assert result["candidate_evidence_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_evidence_review_closeout_ready_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )

    result = candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        **kwargs,
    )

    checks = {
        check["check_id"]: check
        for check in result["shadow_replay_evidence_review_closeout_checks"]
    }
    assert result["browser_skill_shadow_replay_evidence_review_closeout_status"] == (
        "shadow_replay_evidence_review_closeout_ready_no_write"
    )
    assert checks["browser_run_digest_matches_markdown_refs"]["passed"] is True
    assert checks["evidence_confirms_no_browser_or_session_effects"]["passed"] is True
    assert checks["evidence_remains_untrusted_until_review"]["passed"] is True
    assert result["ready_for_local_shadow_execution_approval_next"] is True
    assert result["review_closeout_written"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_replay_evidence_review_closeout_writes_scoped_record(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )

    result = candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )

    assert result["browser_skill_shadow_replay_evidence_review_closeout_status"] == (
        "shadow_replay_evidence_review_closeout_written"
    )
    assert result["review_closeout_written"] is True
    assert result["ready_for_local_shadow_execution_approval_next"] is True
    assert result["trusted_promotion_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["writes_performed"] is True
    review_path = Path(result["review_closeout_ref"])
    assert review_path.is_file()
    assert siteops_vault in review_path.parents
    review_record = json.loads(review_path.read_text(encoding="utf-8"))
    assert review_record["record_type"] == (
        "siteops_browser_skill_shadow_replay_evidence_review_closeout"
    )
    assert review_record["trusted_promotion_allowed"] is False
    assert review_record["browser_execution_allowed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_replay_evidence_review_closeout_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="http://localhost:8765/shadow",
        shadow_mode=True,
        write_browser_run_log=True,
        local_target_only=True,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-replay-evidence-review-closeout",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_replay_evidence_review_closeout_status"] == (
        "shadow_replay_evidence_review_closeout_ready_no_write"
    )
    assert result["ready_for_local_shadow_execution_approval_next"] is True
    assert result["review_closeout_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_execution_approval_packet_ready_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )

    result = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        **kwargs,
    )

    checks = {
        check["check_id"]: check
        for check in result["shadow_execution_approval_packet_checks"]
    }
    assert result["browser_skill_shadow_execution_approval_packet_status"] == (
        "shadow_execution_approval_packet_ready_no_write"
    )
    assert checks["shadow_replay_evidence_review_closeout_status_valid"]["passed"] is True
    assert checks["shadow_replay_evidence_review_digest_matches"]["passed"] is True
    assert checks["shadow_execution_future_targets_create_new"]["passed"] is True
    assert result["approval_request_ready"] is True
    assert result["approval_request_written"] is False
    assert result["ready_for_guarded_local_shadow_execution_proof_next"] is True
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_execution_approval_packet_writes_approval_request(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )

    result = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )

    assert result["browser_skill_shadow_execution_approval_packet_status"] == (
        "shadow_execution_approval_request_written"
    )
    assert result["approval_request_written"] is True
    assert result["run_record_written"] is True
    assert result["audit_written"] is True
    assert result["writes_performed"] is True
    approval = result["approval"]
    assert approval["action"] == "browser_skill_candidate.browser_skill_shadow_execution_proof"
    assert approval["metadata"]["candidate_id"] == "candidate_run_123"
    assert approval["metadata"]["browser_run_sha256"]
    assert Path(result["approval_ref"]).is_file()
    assert Path(result["run_ref"]).is_file()
    assert Path(result["audit_ref"]).is_file()
    assert result["browser_execution_allowed"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_execution_approval_packet_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="http://localhost:8765/shadow",
        shadow_mode=True,
        write_browser_run_log=True,
        local_target_only=True,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_request["approval_id"],
        actor="local-user",
        target_url="http://localhost:8765/shadow",
        shadow_mode=True,
        write_review_closeout=True,
        local_target_only=True,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-approval-packet",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["browser_skill_shadow_execution_approval_packet_status"] == (
        "shadow_execution_approval_packet_ready_no_write"
    )
    assert result["approval_request_ready"] is True
    assert result["approval_request_written"] is False
    assert result["ready_for_guarded_local_shadow_execution_proof_next"] is True
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_execution_approval_decision_preflight_pending_then_approved(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    approval_id = approval_packet["approval_id"]
    before = json.loads(Path(approval_packet["approval_ref"]).read_text(encoding="utf-8"))

    pending = candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_id,
        **kwargs,
    )
    decide_approval_request(
        siteops_vault,
        approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approved = candidate_promotion_browser_skill_shadow_execution_approval_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_id,
        **kwargs,
    )

    assert pending["shadow_execution_approval_decision_preflight_status"] == (
        "blocked_pending_shadow_execution_approval"
    )
    assert pending["ready_for_shadow_execution_proof_review_next_pass"] is False
    assert pending["browser_run_digest_matches"] is True
    assert pending["review_closeout_digest_matches"] is True
    assert pending["future_write_set_matches"] is True
    assert pending["approval_decision_written"] is False
    assert pending["approval_consumed"] is False
    assert pending["shadow_execution_proof_written"] is False
    assert pending["browser_execution_allowed"] is False
    assert pending["canonical_writeback_allowed"] is False
    assert pending["writes_performed"] is False
    assert approved["shadow_execution_approval_decision_preflight_status"] == (
        "shadow_execution_approval_decision_preflight_ready_no_mutation"
    )
    assert approved["approval_status"] == "approved"
    assert approved["ready_for_shadow_execution_proof_review_next_pass"] is True
    assert approved["approved_for_future_shadow_execution_proof_review"] is True
    assert approved["approval_decision_written"] is False
    assert approved["approval_consumed"] is False
    assert approved["shadow_execution_proof_written"] is False
    assert approved["browser_execution_allowed"] is False
    assert approved["canonical_writeback_allowed"] is False
    after = json.loads(Path(approval_packet["approval_ref"]).read_text(encoding="utf-8"))
    assert after["metadata"] == before["metadata"]


def test_siteops_candidate_cli_browser_skill_shadow_execution_approval_decision_preflight_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-approval-decision-preflight",
            "candidate_run_123",
            "--shadow-execution-approval-id",
            approval_packet["approval_id"],
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["shadow_execution_approval_decision_preflight_status"] == (
        "blocked_pending_shadow_execution_approval"
    )
    assert result["approval_status"] == "pending"
    assert result["browser_run_digest_matches"] is True
    assert result["review_closeout_digest_matches"] is True
    assert result["approval_decision_written"] is False
    assert result["approval_consumed"] is False
    assert result["shadow_execution_proof_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["cdp_connection_allowed"] is False
    assert result["authenticated_session_allowed"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_execution_approval_decision_request_preview_and_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    approval_id = approval_packet["approval_id"]

    preview = candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_id,
        decision="approve",
        write_approval_decision=False,
        **kwargs,
    )
    written = candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_id,
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )

    assert preview["shadow_execution_approval_decision_request_status"] == (
        "shadow_execution_approval_decision_ready_no_write"
    )
    assert preview["approval_decision_write_requested"] is False
    assert preview["approval_decision_written"] is False
    assert preview["approval_consumed"] is False
    assert preview["browser_execution_allowed"] is False
    assert preview["writes_performed"] is False
    assert written["shadow_execution_approval_decision_request_status"] == (
        "shadow_execution_approval_decision_written"
    )
    assert written["approval_status_after_decision"] == "approved"
    assert written["approval_decision_write_requested"] is True
    assert written["approval_decision_written"] is True
    assert written["approval_consumed"] is False
    assert written["shadow_execution_proof_written"] is False
    assert written["ready_for_shadow_execution_proof_next_pass"] is True
    assert written["browser_execution_allowed"] is False
    assert written["canonical_writeback_allowed"] is False
    assert written["writes_performed"] is True
    decided = json.loads(Path(written["approval_ref"]).read_text(encoding="utf-8"))
    assert decided["status"] == "approved"
    assert decided["metadata"]["browser_run_sha256"]


def test_siteops_candidate_cli_browser_skill_shadow_execution_approval_decision_request_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-approval-decision-request",
            "candidate_run_123",
            "--shadow-execution-approval-id",
            approval_packet["approval_id"],
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--decision",
            "approve",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["shadow_execution_approval_decision_request_status"] == (
        "shadow_execution_approval_decision_ready_no_write"
    )
    assert result["approval_decision_written"] is False
    assert result["approval_consumed"] is False
    assert result["shadow_execution_proof_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_execution_approval_live_decision_readiness_requires_explicit_decision(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )

    missing_decision = (
        candidate_promotion_browser_skill_shadow_execution_approval_live_decision_readiness(
            "candidate_run_123",
            siteops_vault,
            shadow_execution_approval_id=approval_packet["approval_id"],
            **kwargs,
        )
    )
    approve_ready = (
        candidate_promotion_browser_skill_shadow_execution_approval_live_decision_readiness(
            "candidate_run_123",
            siteops_vault,
            shadow_execution_approval_id=approval_packet["approval_id"],
            intended_decision="approve",
            **kwargs,
        )
    )

    assert missing_decision["shadow_execution_approval_live_decision_readiness_status"] == (
        "blocked_missing_explicit_operator_decision"
    )
    assert missing_decision["ready_for_live_decision_write_next_pass"] is False
    assert missing_decision["live_decision_written"] is False
    assert approve_ready["shadow_execution_approval_live_decision_readiness_status"] == (
        "live_decision_ready_waiting_explicit_write_authorization"
    )
    assert approve_ready["ready_for_live_decision_write_next_pass"] is True
    assert approve_ready["explicit_operator_authorization_present"] is False
    assert approve_ready["approval_command_preview"]
    assert approve_ready["approval_decision_written"] is False
    assert approve_ready["approval_consumed"] is False
    assert approve_ready["browser_execution_allowed"] is False
    assert approve_ready["canonical_writeback_allowed"] is False
    assert approve_ready["writes_performed"] is False
    approval_file = Path(approval_packet["approval_ref"])
    assert json.loads(approval_file.read_text(encoding="utf-8"))["status"] == "pending"


def test_siteops_candidate_cli_browser_skill_shadow_execution_approval_live_decision_readiness_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-approval-live-decision-readiness",
            "candidate_run_123",
            "--shadow-execution-approval-id",
            approval_packet["approval_id"],
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--intended-decision",
            "approve",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["shadow_execution_approval_live_decision_readiness_status"] == (
        "live_decision_ready_waiting_explicit_write_authorization"
    )
    assert result["ready_for_live_decision_write_next_pass"] is True
    assert result["explicit_operator_authorization_present"] is False
    assert result["live_decision_written"] is False
    assert result["approval_decision_written"] is False
    assert result["approval_consumed"] is False
    assert result["shadow_execution_proof_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_execution_proof_readiness_blocks_pending_and_allows_approved(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )

    pending = candidate_promotion_browser_skill_shadow_execution_proof_readiness(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )
    approved = candidate_promotion_browser_skill_shadow_execution_proof_readiness(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        **kwargs,
    )

    assert pending["shadow_execution_proof_readiness_status"] == (
        "blocked_shadow_execution_proof_pending_approval_decision"
    )
    assert pending["ready_for_shadow_execution_proof"] is False
    assert pending["approval_consumed"] is False
    assert pending["browser_execution_allowed"] is False
    assert pending["writes_performed"] is False
    assert approved["shadow_execution_proof_readiness_status"] == "shadow_execution_proof_ready_no_execution"
    assert approved["ready_for_shadow_execution_proof"] is True
    assert approved["proof_command_preview"]
    assert approved["approval_consumed"] is False
    assert approved["shadow_execution_proof_written"] is False
    assert approved["browser_execution_allowed"] is False
    assert approved["canonical_writeback_allowed"] is False
    assert approved["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_execution_proof_readiness_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-proof-readiness",
            "candidate_run_123",
            "--shadow-execution-approval-id",
            approval_packet["approval_id"],
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["shadow_execution_proof_readiness_status"] == (
        "blocked_shadow_execution_proof_pending_approval_decision"
    )
    assert result["ready_for_shadow_execution_proof"] is False
    assert result["approval_consumed"] is False
    assert result["shadow_execution_proof_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False


def test_candidate_browser_skill_shadow_execution_proof_consumption_guard_dry_run_and_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )

    dry_run = candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        **kwargs,
    )
    marker_path = Path(dry_run["shadow_execution_consumer_marker_path"])

    assert dry_run["shadow_execution_proof_consumption_guard_status"] == (
        "shadow_execution_proof_consumption_guard_ready_dry_run_no_write"
    )
    assert dry_run["shadow_execution_consumer_ready_to_consume"] is True
    assert dry_run["approval_consumed"] is False
    assert dry_run["shadow_execution_consumption_marker_written"] is False
    assert dry_run["browser_execution_allowed"] is False
    assert dry_run["canonical_writeback_allowed"] is False
    assert not marker_path.exists()

    written = candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        consume_shadow_execution_approval=True,
        **kwargs,
    )

    assert written["shadow_execution_proof_consumption_guard_status"] == (
        "shadow_execution_approval_consumed_marker_and_audit_written"
    )
    assert written["approval_consumed"] is True
    assert written["shadow_execution_consumption_marker_written"] is True
    assert written["shadow_execution_consumer_audit_written"] is True
    assert written["run_record_written"] is True
    assert written["shadow_execution_proof_written"] is False
    assert written["browser_execution_allowed"] is False
    assert written["trusted_promotion_allowed"] is False
    assert written["canonical_writeback_allowed"] is False
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["shadow_execution_approval_id"] == approval_packet["approval_id"]
    assert marker["shadow_execution_proof_written"] is False
    assert marker["browser_execution_performed"] is False
    assert Path(written["run_ref"]).exists()
    assert Path(written["audit_ref"]).exists()
    approval_after = json.loads(Path(approval_packet["approval_ref"]).read_text(encoding="utf-8"))
    assert approval_after["status"] == "approved"

    duplicate = candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        consume_shadow_execution_approval=True,
        **kwargs,
    )
    assert duplicate["shadow_execution_proof_consumption_guard_status"] == (
        "blocked_shadow_execution_consumption_marker_already_exists"
    )
    assert duplicate["approval_consumed"] is False
    assert duplicate["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_execution_proof_consumption_guard_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-proof-consumption-guard",
            "candidate_run_123",
            "--shadow-execution-approval-id",
            approval_packet["approval_id"],
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["shadow_execution_proof_consumption_guard_status"] == (
        "shadow_execution_proof_consumption_guard_ready_dry_run_no_write"
    )
    assert result["shadow_execution_consumer_ready_to_consume"] is True
    assert result["consume_shadow_execution_approval_requested"] is False
    assert result["approval_consumed"] is False
    assert result["shadow_execution_consumption_marker_written"] is False
    assert result["shadow_execution_proof_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not Path(result["shadow_execution_consumer_marker_path"]).exists()


def test_candidate_browser_skill_shadow_execution_proof_artifact_writer(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )

    blocked = candidate_promotion_browser_skill_shadow_execution_proof(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        **kwargs,
    )
    assert blocked["shadow_execution_proof_status"] == (
        "blocked_shadow_execution_proof_consumption_marker_missing"
    )
    assert blocked["shadow_execution_proof_written"] is False

    candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        consume_shadow_execution_approval=True,
        **kwargs,
    )
    dry_run = candidate_promotion_browser_skill_shadow_execution_proof(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        **kwargs,
    )
    browser_run_path = Path(dry_run["browser_run_path"])
    agent_activity_path = Path(dry_run["agent_activity_path"])

    assert dry_run["shadow_execution_proof_status"] == (
        "shadow_execution_proof_artifact_writer_ready_no_write"
    )
    assert dry_run["shadow_execution_proof_ready_to_write"] is True
    assert dry_run["approval_consumed"] is True
    assert dry_run["shadow_execution_proof_written"] is False
    assert dry_run["writes_performed"] is False
    assert not browser_run_path.exists()
    assert not agent_activity_path.exists()

    written = candidate_promotion_browser_skill_shadow_execution_proof(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        write_shadow_execution_proof=True,
        **kwargs,
    )

    assert written["shadow_execution_proof_status"] == (
        "shadow_execution_proof_artifact_written_no_browser"
    )
    assert written["shadow_execution_proof_written"] is True
    assert written["browser_run_log_written"] is True
    assert written["agent_activity_log_written"] is True
    assert written["run_record_written"] is True
    assert written["browser_execution_allowed"] is False
    assert written["cdp_connection_allowed"] is False
    assert written["authenticated_session_allowed"] is False
    assert written["trusted_promotion_allowed"] is False
    assert written["canonical_writeback_allowed"] is False
    proof = json.loads(browser_run_path.read_text(encoding="utf-8"))
    assert proof["record_type"] == "siteops_browser_skill_shadow_execution_proof"
    assert proof["browser_execution_performed"] is False
    assert proof["cdp_connection_performed"] is False
    assert proof["authenticated_session_used"] is False
    assert proof["canonical_writeback_performed"] is False
    assert agent_activity_path.exists()

    duplicate = candidate_promotion_browser_skill_shadow_execution_proof(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        write_shadow_execution_proof=True,
        **kwargs,
    )
    assert duplicate["shadow_execution_proof_status"] == (
        "blocked_shadow_execution_proof_artifact_already_exists"
    )
    assert duplicate["shadow_execution_proof_written"] is False
    assert duplicate["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_execution_proof_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        consume_shadow_execution_approval=True,
        **kwargs,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-proof",
            "candidate_run_123",
            "--shadow-execution-approval-id",
            approval_packet["approval_id"],
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["shadow_execution_proof_status"] == (
        "shadow_execution_proof_artifact_writer_ready_no_write"
    )
    assert result["shadow_execution_proof_ready_to_write"] is True
    assert result["approval_consumed"] is True
    assert result["write_shadow_execution_proof_requested"] is False
    assert result["shadow_execution_proof_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not Path(result["browser_run_path"]).exists()


def test_candidate_browser_skill_shadow_execution_proof_review_closeout(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        consume_shadow_execution_approval=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_proof(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        write_shadow_execution_proof=True,
        **kwargs,
    )

    dry_run = candidate_promotion_browser_skill_shadow_execution_proof_review_closeout(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        **kwargs,
    )
    review_path = Path(dry_run["review_closeout_path"])

    assert dry_run["shadow_execution_proof_review_closeout_status"] == (
        "shadow_execution_proof_artifact_review_closeout_ready_no_write"
    )
    assert dry_run["ready_for_trusted_promotion_review_next"] is True
    assert dry_run["trusted_promotion_allowed"] is False
    assert dry_run["browser_execution_allowed"] is False
    assert dry_run["canonical_writeback_allowed"] is False
    assert dry_run["review_closeout_written"] is False
    assert dry_run["writes_performed"] is False
    assert not review_path.exists()

    written = candidate_promotion_browser_skill_shadow_execution_proof_review_closeout(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        write_review_closeout=True,
        **kwargs,
    )

    assert written["shadow_execution_proof_review_closeout_status"] == (
        "shadow_execution_proof_artifact_review_closeout_written"
    )
    assert written["review_closeout_written"] is True
    assert written["writes_performed"] is True
    assert written["trusted_promotion_allowed"] is False
    assert written["browser_execution_allowed"] is False
    assert review_path.exists()
    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert review["record_type"] == "siteops_browser_skill_shadow_execution_proof_review_closeout"
    assert review["review_status"] == "closed_untrusted_no_browser_proof"
    assert review["evidence_trust"] == "untrusted_shadow_execution_proof"
    assert review["trusted_promotion_allowed"] is False
    assert review["browser_execution_allowed"] is False
    assert review["canonical_writeback_allowed"] is False

    duplicate = candidate_promotion_browser_skill_shadow_execution_proof_review_closeout(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        write_review_closeout=True,
        **kwargs,
    )
    assert duplicate["shadow_execution_proof_review_closeout_status"] == (
        "blocked_shadow_execution_proof_review_closeout_already_exists"
    )
    assert duplicate["review_closeout_written"] is False
    assert duplicate["writes_performed"] is False


def test_siteops_candidate_cli_browser_skill_shadow_execution_proof_review_closeout_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request, activation_request = _prepared_activation_executor_inputs(siteops_vault)
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_activation_gate_allowed"),
    )
    kwargs = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "source_approval_id": request["approval"]["approval_id"],
        "activation_approval_id": activation_request["approval_id"],
        "actor": "local-user",
        "target_url": "http://localhost:8765/shadow",
        "shadow_mode": True,
        "local_target_only": True,
    }
    candidate_promotion_browser_skill_shadow_replay_runner_write_pass(
        "candidate_run_123",
        siteops_vault,
        write_browser_run_log=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_replay_evidence_review_closeout(
        "candidate_run_123",
        siteops_vault,
        write_review_closeout=True,
        **kwargs,
    )
    approval_packet = candidate_promotion_browser_skill_shadow_execution_approval_packet(
        "candidate_run_123",
        siteops_vault,
        write_approval_request=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_approval_decision_request(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        decision="approve",
        write_approval_decision=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_proof_consumption_guard(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        consume_shadow_execution_approval=True,
        **kwargs,
    )
    candidate_promotion_browser_skill_shadow_execution_proof(
        "candidate_run_123",
        siteops_vault,
        shadow_execution_approval_id=approval_packet["approval_id"],
        write_shadow_execution_proof=True,
        **kwargs,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "browser-skill-shadow-execution-proof-review-closeout",
            "candidate_run_123",
            "--shadow-execution-approval-id",
            approval_packet["approval_id"],
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--target-url",
            "http://localhost:8765/shadow",
            "--shadow-mode",
            "--local-target-only",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["shadow_execution_proof_review_closeout_status"] == (
        "shadow_execution_proof_artifact_review_closeout_ready_no_write"
    )
    assert result["ready_for_trusted_promotion_review_next"] is True
    assert result["write_review_closeout_requested"] is False
    assert result["review_closeout_written"] is False
    assert result["trusted_promotion_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not Path(result["review_closeout_path"]).exists()


def test_candidate_preimplementation_verifier_blocked_pending_approval(siteops_vault: Path) -> None:
    """With a pending (not-yet-approved) approval the verifier must be blocked."""
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_preimplementation_verifier(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["ok"] is True
    assert result["verifier_pass"] is False
    assert result["checklist_layer_pass"] is False
    assert "blocked" in result["verifier_verdict"]
    assert result["writes_performed"] is False
    assert result["executor_implemented"] is True
    assert result["trusted_skill_write_allowed"] is False


def test_candidate_preimplementation_verifier_blocks_preexisting_target_artifact(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    target = siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("id: example.safe_candidate\nstatus: unexpected_preexisting\n", encoding="utf-8")

    result = candidate_promotion_preimplementation_verifier(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in result["verifier_checks"]}
    target_items = {item["path"]: item for item in result["absent_target_paths"]}
    assert result["verifier_pass"] is False
    assert result["verifier_verdict"].startswith("blocked_")
    assert (
        result["checklist_layer_pass"] is False
        or checks["trusted_artifact_targets_absent"]["passed"] is False
    )
    if "runtime/browser_skills/skills/example.safe_candidate.yaml" in target_items:
        assert target_items["runtime/browser_skills/skills/example.safe_candidate.yaml"]["exists_on_disk"] is True
    assert result["writes_performed"] is False
    assert result["executor_implemented"] is True
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_preimplementation_verifier_blocks_unexpected_executor_entrypoint(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "apply_trusted_candidate_artifacts",
        lambda *args, **kwargs: None,
        raising=False,
    )

    result = candidate_promotion_preimplementation_verifier(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in result["verifier_checks"]}
    assert result["checklist_layer_pass"] is True
    assert result["verifier_pass"] is False
    assert result["verifier_verdict"] == "blocked_live_guard_failure: executor_entrypoint_absent_or_guarded"
    assert checks["executor_entrypoint_absent_or_guarded"]["passed"] is False
    assert "exists" in str(checks["executor_entrypoint_absent_or_guarded"]["detail"])
    assert result["writes_performed"] is False
    assert result["executor_implemented"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_preimplementation_verifier_blocks_missing_cli_contract_marker(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    fake_repo = siteops_vault / "fake_repo"
    fake_module_path = fake_repo / "runtime" / "siteops" / "candidate_promotions.py"
    fake_module_path.parent.mkdir(parents=True, exist_ok=True)
    fake_module_path.write_text("# fake module path for verifier repo-root resolution\n", encoding="utf-8")
    fake_tests = fake_repo / "runtime" / "siteops" / "tests" / "test_candidate_promotions.py"
    fake_tests.parent.mkdir(parents=True, exist_ok=True)
    fake_tests.write_text(
        "\n".join(
            [
                "def test_candidate_executor_guard_entrypoint_is_guarded(): pass",
                "def test_candidate_executor_guard_gate_operation_is_allowlisted_after_approval_patch(): pass",
                "def test_candidate_executor_guard_design_marks_entrypoint_built_but_gate_blocked(): pass",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    fake_cli = fake_repo / "runtime" / "cli" / "main.py"
    fake_cli.parent.mkdir(parents=True, exist_ok=True)
    fake_cli.write_text("# intentionally missing executor review checklist marker\n", encoding="utf-8")
    monkeypatch.setattr(candidate_promotions_module, "__file__", str(fake_module_path))

    result = candidate_promotion_preimplementation_verifier(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in result["verifier_checks"]}
    assert result["checklist_layer_pass"] is True
    assert result["verifier_pass"] is False
    assert result["verifier_verdict"] == "blocked_live_guard_failure: cli_contract_present"
    assert checks["guard_tests_present"]["passed"] is True
    assert checks["cli_contract_present"]["passed"] is False
    assert "not found" in str(checks["cli_contract_present"]["detail"])
    assert result["writes_performed"] is False
    assert result["executor_implemented"] is True
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_preimplementation_verifier_cli_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI smoke: preimplementation-verifier returns 0 exit code, verifier_pass in JSON."""
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "preimplementation-verifier",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["verifier_verdict"] == "ready_for_patch_proposal"
    assert result["verifier_pass"] is True
    assert result["executor_implemented"] is True
    assert result["executor_enabled"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


# -- Executor implementation design-review tests ---------------------------


def test_candidate_executor_implementation_design_review_ready_no_authority(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_executor_implementation_design_review(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["ok"] is True
    assert result["verifier_pass"] is True
    assert result["implementation_design_status"] == "implementation_design_review_ready_no_authority"
    assert result["review_decision"] == "patch_plan_only_do_not_implement_in_this_pass"
    assert result["gate_operation"] == PROMOTION_GATE_APPLY_OPERATION
    assert result["executor_implemented"] is True
    assert result["executor_enabled"] is False
    assert result["executor_build_allowed"] is False
    assert result["executor_implementation_allowed"] is False
    assert result["allowlist_change_allowed"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert any(item["step_id"] == "add_executor_entrypoint" for item in result["patch_plan"])
    assert all(item["allowed_in_this_pass"] is False for item in result["patch_plan"])
    _assert_guarded_executor_entrypoint()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_executor_implementation_design_review_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_executor_implementation_design_review(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["verifier_pass"] is False
    assert result["implementation_design_status"].startswith("blocked_preimplementation_verifier")
    assert result["review_decision"] == "blocked_before_patch_plan"
    assert result["executor_implemented"] is True
    assert result["executor_enabled"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_executor_implementation_design_review_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "executor-implementation-design-review",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["implementation_design_status"] == "implementation_design_review_ready_no_authority"
    assert result["verifier_pass"] is True
    assert result["executor_implemented"] is True
    assert result["executor_enabled"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    _assert_guarded_executor_entrypoint()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


# -- Executor prewrite audit spec tests -------------------------------------


def test_candidate_executor_prewrite_audit_spec_ready_no_authority(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_executor_prewrite_audit_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    event_types = [item["event_type"] for item in result["audit_event_sequence"]]
    contracts = {item["artifact_kind"]: item for item in result["inactive_artifact_contracts"]}
    assert result["ok"] is True
    assert result["prewrite_audit_spec_status"] == "prewrite_audit_spec_ready_no_authority"
    assert result["review_decision"] == "audit_contract_only_do_not_write_in_this_pass"
    assert "trusted_executor_preflight_started" in event_types
    assert "trusted_executor_prewrite_validated" in event_types
    assert "trusted_executor_blocked" in event_types
    assert "trusted_executor_rollback_required" in event_types
    assert contracts["browser_skill"]["required_status"] == "inactive_review"
    assert contracts["browser_skill"]["activation_allowed"] is False
    assert contracts["siteops_skill_card"]["required_status"] == "inactive_review"
    assert result["validation_contract"]["all_checks_implemented"] is False
    assert "cookie" in result["forbidden_metadata_fields"]
    assert "raw_candidate_content" in result["forbidden_metadata_fields"]
    assert result["audit_events_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    _assert_guarded_executor_entrypoint()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_executor_prewrite_audit_spec_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_executor_prewrite_audit_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["prewrite_audit_spec_status"].startswith("blocked_implementation_design_review")
    assert result["review_decision"] == "blocked_before_audit_contract"
    assert result["audit_events_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_executor_prewrite_audit_spec_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "executor-prewrite-audit-spec",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["prewrite_audit_spec_status"] == "prewrite_audit_spec_ready_no_authority"
    assert result["audit_events_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    _assert_guarded_executor_entrypoint()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


# -- Inactive artifact validator tests --------------------------------------


def test_candidate_inactive_artifact_validator_ready_no_authority(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_inactive_artifact_validator(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    validations = {item["artifact_kind"]: item for item in result["artifact_validations"]}
    payloads = result["proposed_artifact_payloads"]
    assert result["inactive_artifact_validator_status"] == "inactive_artifact_validator_ready_no_authority"
    assert result["review_decision"] == "validator_contract_only_do_not_write_in_this_pass"
    assert result["validation_pass"] is True
    assert validations["browser_skill"]["ok"] is True
    assert validations["siteops_skill_card"]["ok"] is True
    assert payloads["browser_skill"]["status"] == "inactive_review"
    assert payloads["browser_skill"]["activation_allowed"] is False
    assert payloads["siteops_skill_card"]["status"] == "inactive_review"
    assert payloads["siteops_skill_card"]["activation_allowed"] is False
    assert result["validator_wrote_artifacts"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    _assert_guarded_executor_entrypoint()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_inactive_artifact_validator_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_inactive_artifact_validator(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["inactive_artifact_validator_status"].startswith("blocked_prewrite_audit_spec")
    assert result["review_decision"] == "blocked_before_inactive_artifact_validation"
    assert result["validation_pass"] is False
    assert result["validator_wrote_artifacts"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_inactive_artifact_validator_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "inactive-artifact-validator",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["inactive_artifact_validator_status"] == "inactive_artifact_validator_ready_no_authority"
    assert result["validation_pass"] is True
    assert result["validator_wrote_artifacts"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    _assert_guarded_executor_entrypoint()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


# -- Collision policy spec tests -------------------------------------------


def test_candidate_collision_policy_spec_ready_no_authority(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_collision_policy_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    target_checks = {item["artifact_kind"]: item for item in result["target_path_checks"]}
    assert result["collision_policy_status"] == "collision_policy_spec_ready_no_authority"
    assert result["review_decision"] == "collision_contract_only_do_not_write_in_this_pass"
    assert result["collision_policy_pass"] is True
    assert result["collision_policy"]["pre_existing_target"] == "block"
    assert result["collision_policy"]["overwrite"].startswith("forbidden")
    assert target_checks["browser_skill"]["path_confined"] is True
    assert target_checks["browser_skill"]["exists_on_disk"] is False
    assert target_checks["browser_skill"]["collision_detected"] is False
    assert target_checks["siteops_skill_card"]["exists_on_disk"] is False
    assert target_checks["browser_skill"]["overwrite_allowed"] is False
    assert target_checks["browser_skill"]["write_allowed_in_this_pass"] is False
    assert result["overwrite_allowed"] is False
    assert result["collision_resolution_allowed"] is False
    assert result["idempotent_apply_allowed"] is False
    assert result["rollback_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["collision_policy_wrote_artifacts"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_collision_policy_spec_blocks_preexisting_target(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    target = siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("id: example.safe_candidate\nstatus: preexisting\n", encoding="utf-8")

    result = candidate_promotion_collision_policy_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    target_checks = {item["artifact_kind"]: item for item in result["target_path_checks"]}
    assert result["collision_policy_status"] == "blocked_target_collision"
    assert result["review_decision"] == "blocked_existing_target_requires_manual_collision_review"
    assert result["collision_policy_pass"] is False
    assert target_checks["browser_skill"]["exists_on_disk"] is True
    assert target_checks["browser_skill"]["collision_detected"] is True
    assert target_checks["browser_skill"]["overwrite_allowed"] is False
    assert target_checks["browser_skill"]["write_allowed_in_this_pass"] is False
    assert result["overwrite_allowed"] is False
    assert result["collision_resolution_allowed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False


def test_candidate_collision_policy_spec_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_collision_policy_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["collision_policy_status"].startswith("blocked_inactive_artifact_validator")
    assert result["review_decision"] == "blocked_before_collision_policy"
    assert result["collision_policy_pass"] is False
    assert result["overwrite_allowed"] is False
    assert result["collision_resolution_allowed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_collision_policy_spec_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "collision-policy-spec",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["collision_policy_status"] == "collision_policy_spec_ready_no_authority"
    assert result["collision_policy_pass"] is True
    assert result["overwrite_allowed"] is False
    assert result["collision_resolution_allowed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["executor_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    _assert_guarded_executor_entrypoint()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_siteops_candidate_cli_approval_rebind_spec_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "approval-rebind-spec",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["approval_rebind_spec_status"] == "approval_rebind_spec_required_no_write_authority"
    assert result["approval_provenance"]["provenance_status"] == "legacy_unbound"
    assert result["legacy_approval_mutation_allowed"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["approval_decision_written"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_bound_approval_request_spec_defines_no_write_replacement_artifact(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_bound_approval_request_spec(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    artifact = result["approval_request_artifact"]
    metadata = artifact["metadata"]
    validation = result["approval_request_validation"]
    assert result["ok"] is True
    assert result["bound_approval_request_spec_status"] == "bound_approval_request_spec_ready_no_write"
    assert result["approval_rebind_spec_status"] == "approval_rebind_spec_required_no_write_authority"
    assert artifact["action"] == "browser_skill_candidate.promote"
    assert artifact["status"] == "pending"
    assert artifact["supersedes_approval_id"] == request["approval"]["approval_id"]
    assert metadata["candidate_id"] == "candidate_run_123"
    assert metadata["proposed_skill_id"] == "example.safe_candidate"
    assert metadata["approval_binding_version"] == "browser_skill_candidate.v1"
    assert validation["passed"] is True
    assert validation["checks"]["candidate_metadata_bound"]["passed"] is True
    assert validation["checks"]["legacy_approval_immutable"]["passed"] is True
    assert result["approval_request_artifact_written"] is False
    assert result["legacy_approval_mutation_allowed"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["activation_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_siteops_candidate_cli_bound_approval_request_spec_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "bound-approval-request-spec",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["bound_approval_request_spec_status"] == "bound_approval_request_spec_ready_no_write"
    assert result["approval_request_validation"]["passed"] is True
    assert result["approval_request_artifact_written"] is False
    assert result["approval_decision_written"] is False
    assert result["writes_performed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()


def test_candidate_bound_approval_writer_design_ready_no_write(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_bound_approval_writer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    target = Path(result["target_path_preview"]["path"])
    assert result["bound_approval_writer_design_status"] == "bound_approval_writer_design_ready_no_write"
    assert result["writer_ready_no_write"] is True
    assert result["bound_approval_request_spec_status"] == "bound_approval_request_spec_ready_no_write"
    assert result["target_path_preview"]["target_confined"] is True
    assert result["target_path_preview"]["target_exists"] is False
    assert result["audit_event_contract"]["event_type"] == "bound_approval_request_created"
    assert result["idempotency_policy"]["existing_target"] == "block_for_manual_review"
    assert result["rollback_policy"]["atomic_write_required"] is True
    assert result["approval_request_artifact_written"] is False
    assert result["bound_approval_writer_implemented"] is False
    assert result["bound_approval_audit_event_written"] is False
    assert result["writes_performed"] is False
    assert not target.exists()


def test_candidate_bound_approval_writer_design_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_bound_approval_writer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["bound_approval_writer_design_status"].startswith("blocked_bound_approval_request_spec")
    assert result["review_decision"] == "blocked_before_bound_approval_writer"
    assert result["writer_ready_no_write"] is False
    assert result["approval_request_artifact_written"] is False
    assert result["bound_approval_writer_implemented"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_bound_approval_writer_design_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "bound-approval-writer-design",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["bound_approval_writer_design_status"] == "bound_approval_writer_design_ready_no_write"
    assert result["writer_ready_no_write"] is True
    assert result["approval_request_artifact_written"] is False
    assert result["bound_approval_audit_event_written"] is False
    assert result["bound_approval_idempotency_marker_written"] is False
    assert result["approval_decision_written"] is False
    assert result["writes_performed"] is False
    assert not Path(result["target_path_preview"]["path"]).exists()


def test_candidate_bound_approval_writer_preflight_ready_no_write(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_bound_approval_writer_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["bound_approval_writer_preflight_status"] == "bound_approval_writer_preflight_ready_no_write"
    assert result["preflight_ready_no_write"] is True
    assert result["preflight_checks"]["writer_design_ready"]["passed"] is True
    assert result["preflight_checks"]["idempotency_marker_absent_and_scoped"]["passed"] is True
    assert result["preflight_checks"]["recovery_marker_absent_and_scoped"]["passed"] is True
    assert result["preflight_checks"]["trusted_apply_gate_posture_recorded"]["passed"] is True
    assert result["trusted_apply_gate_posture"]["allowed"] is False
    assert result["approval_request_artifact_written"] is False
    assert result["bound_approval_preflight_marker_written"] is False
    assert result["bound_approval_recovery_marker_written"] is False
    assert result["writes_performed"] is False
    assert not Path(result["target_path_preview"]["path"]).exists()
    assert not Path(result["idempotency_marker_preview"]["path"]).exists()
    assert not Path(result["recovery_marker_preview"]["path"]).exists()


def test_candidate_bound_approval_writer_preflight_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_bound_approval_writer_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["bound_approval_writer_preflight_status"].startswith("blocked_bound_approval_writer_design")
    assert result["review_decision"] == "blocked_before_bound_approval_writer_preflight"
    assert result["preflight_ready_no_write"] is False
    assert result["approval_request_artifact_written"] is False
    assert result["writes_performed"] is False


def test_candidate_bound_approval_writer_preflight_blocks_existing_marker(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")
    initial = candidate_promotion_bound_approval_writer_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )
    marker_path = Path(initial["idempotency_marker_preview"]["path"])
    marker_path.parent.mkdir(parents=True)
    marker_path.write_text("{}\n", encoding="utf-8")

    result = candidate_promotion_bound_approval_writer_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["bound_approval_writer_preflight_status"] == "blocked_existing_bound_approval_idempotency_marker"
    assert result["preflight_ready_no_write"] is False
    assert result["idempotency_marker_preview"]["marker_exists"] is True
    assert result["bound_approval_idempotency_marker_written"] is False


def test_siteops_candidate_cli_bound_approval_writer_preflight_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "bound-approval-writer-preflight",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["bound_approval_writer_preflight_status"] == "bound_approval_writer_preflight_ready_no_write"
    assert result["preflight_ready_no_write"] is True
    assert result["approval_request_artifact_written"] is False
    assert result["bound_approval_preflight_marker_written"] is False
    assert result["bound_approval_recovery_marker_written"] is False
    assert result["writes_performed"] is False
    assert not Path(result["target_path_preview"]["path"]).exists()


def test_candidate_bound_approval_writer_implementation_request_ready_no_write(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_bound_approval_writer_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert (
        result["bound_approval_writer_implementation_request_status"]
        == "bound_approval_writer_implementation_request_ready_no_write"
    )
    assert result["request_ready_no_write"] is True
    assert result["implementation_request_checks"]["preflight_ready"]["passed"] is True
    assert result["implementation_request_checks"]["implementation_still_disabled"]["passed"] is True
    assert result["implementation_request_artifact"]["implementation_allowed_in_this_pass"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["approval_request_artifact_written"] is False
    assert result["bound_approval_writer_implemented"] is False
    assert result["writes_performed"] is False


def test_candidate_bound_approval_writer_implementation_request_blocks_pending_approval(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_bound_approval_writer_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["bound_approval_writer_implementation_request_status"].startswith(
        "blocked_bound_approval_writer_preflight"
    )
    assert result["review_decision"] == "blocked_before_implementation_request"
    assert result["request_ready_no_write"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_bound_approval_writer_implementation_request_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "bound-approval-writer-implementation-request",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert (
        result["bound_approval_writer_implementation_request_status"]
        == "bound_approval_writer_implementation_request_ready_no_write"
    )
    assert result["request_ready_no_write"] is True
    assert result["implementation_request_artifact_written"] is False
    assert result["approval_request_artifact_written"] is False
    assert result["bound_approval_writer_implemented"] is False
    assert result["writes_performed"] is False


def test_candidate_bound_approval_writer_implementation_approval_approve_no_write(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_bound_approval_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        decision="approve",
        actor="local-user",
        reason="approve writer implementation scaffold",
    )

    assert (
        result["bound_approval_writer_implementation_approval_status"]
        == "bound_approval_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["implementation_patch_allowed_next_pass"] is True
    assert (
        result["implementation_approval_record"]["decision_id"]
        != result["implementation_approval_record"]["implementation_request_id"]
    )
    assert result["implementation_approval_record"]["durable_record_written"] is False
    assert result["implementation_approval_record_written"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["bound_approval_writer_implemented"] is False
    assert result["writes_performed"] is False


def test_candidate_bound_approval_writer_implementation_approval_reject_no_write(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_bound_approval_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        decision="reject",
        actor="local-user",
    )

    assert (
        result["bound_approval_writer_implementation_approval_status"]
        == "bound_approval_writer_implementation_rejected_no_write"
    )
    assert result["implementation_patch_allowed_next_pass"] is False
    assert result["implementation_rejected_no_write"] is True
    assert result["implementation_approval_record_written"] is False
    assert result["writes_performed"] is False


def test_candidate_bound_approval_writer_implementation_approval_blocks_pending_approval(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_bound_approval_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        decision="approve",
        actor="local-user",
    )

    assert result["bound_approval_writer_implementation_approval_status"].startswith(
        "blocked_bound_approval_writer_implementation_request"
    )
    assert result["review_decision"] == "blocked_before_implementation_approval"
    assert result["implementation_patch_allowed_next_pass"] is False
    assert result["implementation_approval_record_written"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_bound_approval_writer_implementation_approval_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "bound-approval-writer-implementation-approval",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--decision",
            "approve",
            "--reason",
            "approve writer implementation scaffold",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert (
        result["bound_approval_writer_implementation_approval_status"]
        == "bound_approval_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["implementation_patch_allowed_next_pass"] is True
    assert result["implementation_approval_record_written"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["bound_approval_writer_implemented"] is False
    assert result["writes_performed"] is False


def test_candidate_bound_approval_writer_implementation_dry_run_ready_no_write(siteops_vault: Path) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)

    result = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        reason="bounded writer implementation",
        write_replacement_approval=False,
    )

    assert result["bound_approval_writer_implementation_status"] == "bound_approval_writer_ready_dry_run_no_write"
    assert result["writer_ready_to_write"] is True
    assert result["write_replacement_approval_requested"] is False
    assert result["bound_approval_writer_implemented"] is True
    assert result["replacement_approval_request_written"] is False
    assert result["bound_approval_audit_event_written"] is False
    assert result["bound_approval_idempotency_marker_written"] is False
    assert result["bound_approval_recovery_marker_written"] is False
    assert result["writes_performed"] is False
    assert not Path(result["target_path_preview"]["path"]).exists()
    assert not Path(result["idempotency_marker_preview"]["path"]).exists()
    assert not Path(result["recovery_marker_preview"]["path"]).exists()


def test_candidate_bound_approval_writer_implementation_writes_only_replacement_approval_evidence(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    legacy_approval_path = Path(request["approval"]["approval_ref"])
    legacy_before = json.loads(legacy_approval_path.read_text(encoding="utf-8"))

    result = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        reason="bounded writer implementation",
        write_replacement_approval=True,
    )

    approval_path = Path(result["approval_ref"])
    marker_path = Path(result["idempotency_marker_ref"])
    recovery_path = Path(result["recovery_marker_ref"])
    audit_path = Path(result["audit_ref"])
    run_path = Path(result["run_ref"])
    replacement = json.loads(approval_path.read_text(encoding="utf-8"))
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
    audit_lines = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]

    assert result["bound_approval_writer_implementation_status"] == "bound_approval_writer_replacement_approval_written"
    assert result["replacement_approval_request_written"] is True
    assert result["bound_approval_run_record_written"] is True
    assert result["bound_approval_audit_event_written"] is True
    assert result["bound_approval_idempotency_marker_written"] is True
    assert result["bound_approval_recovery_marker_written"] is True
    assert result["approval_decision_written"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert approval_path.exists()
    assert marker_path.exists()
    assert recovery_path.exists()
    assert audit_path.exists()
    assert run_path.exists()
    assert replacement["status"] == "pending"
    assert replacement["metadata"]["candidate_id"] == "candidate_run_123"
    assert replacement["metadata"]["proposed_skill_id"] == "example.safe_candidate"
    assert replacement["metadata"]["supersedes_approval_id"] == request["approval"]["approval_id"]
    assert replacement["required_approver_role"] == "tenant_admin"
    assert marker["approval_payload_sha256"] == result["approval_payload_sha256"]
    assert recovery["status"] == "completed"
    assert audit_lines[-1]["event_type"] == "bound_approval_request_created"
    assert audit_lines[-1]["metadata"]["approval_id"] == replacement["approval_id"]
    assert "api_key" not in json.dumps(audit_lines).lower()
    assert "cookie" not in json.dumps(audit_lines).lower()
    assert json.loads(legacy_approval_path.read_text(encoding="utf-8")) == legacy_before
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_bound_approval_writer_implementation_blocks_pending_source_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    assert result["bound_approval_writer_implementation_status"].startswith(
        "blocked_bound_approval_writer_implementation_approval"
    )
    assert result["writer_ready_to_write"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["bound_approval_audit_event_written"] is False
    assert result["writes_performed"] is False
    assert not Path(result["target_path_preview"]["path"]).exists()


def test_candidate_bound_approval_writer_implementation_blocks_duplicate_target(siteops_vault: Path) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    first = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    second = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    assert first["replacement_approval_request_written"] is True
    assert second["bound_approval_writer_implementation_status"].startswith(
        "blocked_bound_approval_writer_implementation_approval"
    )
    assert second["replacement_approval_request_written"] is False
    assert second["writes_performed"] is False


def test_siteops_candidate_cli_bound_approval_writer_implementation_writes_when_explicit(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)

    code = cli.main(
        [
            "siteops",
            "candidates",
            "bound-approval-writer-implementation",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--write-replacement-approval",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["replacement_approval_request_written"] is True
    assert result["bound_approval_writer_implemented"] is True
    assert result["bound_approval_audit_event_written"] is True
    assert result["bound_approval_idempotency_marker_written"] is True
    assert result["bound_approval_recovery_marker_written"] is True
    assert result["approval_decision_written"] is False
    assert Path(result["approval_ref"]).exists()


def test_candidate_replacement_approval_decision_consumption_approves_without_trusted_writes(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    legacy_before = json.loads(Path(request["approval"]["approval_ref"]).read_text(encoding="utf-8"))

    result = candidate_promotion_replacement_approval_decision_consumption(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        decision="approve",
        reason="reviewed replacement approval binding",
        write_approval_decision=True,
    )

    replacement = json.loads(Path(writer["approval_ref"]).read_text(encoding="utf-8"))
    legacy_after = json.loads(Path(request["approval"]["approval_ref"]).read_text(encoding="utf-8"))
    assert result["replacement_approval_decision_status"] == "replacement_approval_decision_written"
    assert result["replacement_approval_consumption_status"] == "replacement_approval_consumption_ready_no_trusted_write"
    assert result["approval_decision_written"] is True
    assert result["replacement_approval_consumption_ready"] is True
    assert result["replacement_approval_consumption_marker_written"] is False
    assert result["approval_consumed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert replacement["status"] == "approved"
    assert replacement["decided_by"] == "local-user"
    assert replacement["decision_reason"] == "reviewed replacement approval binding"
    assert legacy_after == legacy_before
    audit_events = [json.loads(line) for line in Path(result["audit_ref"]).read_text(encoding="utf-8").splitlines()]
    decision_events = [event for event in audit_events if event["event_type"] == "approval_decision"]
    assert decision_events[-1]["metadata"]["decision_reason"] == "reviewed replacement approval binding"
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_siteops_candidate_cli_replacement_approval_decision_consumption_writes_decision_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "replacement-approval-decision-consumption",
            "candidate_run_123",
            "--replacement-approval-id",
            writer["approval_request_artifact"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--decision",
            "approve",
            "--write-approval-decision",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["replacement_approval_decision_status"] == "replacement_approval_decision_written"
    assert result["approval_decision_written"] is True
    assert result["approval_consumed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_replacement_approval_decision_consumption_dry_run_is_non_mutating(siteops_vault: Path) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_before = json.loads(Path(writer["approval_ref"]).read_text(encoding="utf-8"))

    result = candidate_promotion_replacement_approval_decision_consumption(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        decision="approve",
        write_approval_decision=False,
    )

    replacement_after = json.loads(Path(writer["approval_ref"]).read_text(encoding="utf-8"))
    assert result["replacement_approval_decision_status"] == "replacement_approval_decision_ready_no_write"
    assert result["replacement_approval_consumption_status"] == "replacement_approval_pending_not_consumed"
    assert result["replacement_approval_consumption_ready"] is False
    assert result["approval_decision_written"] is False
    assert result["writes_performed"] is False
    assert replacement_after == replacement_before


def test_candidate_replacement_approval_decision_consumption_ready_after_existing_approval(siteops_vault: Path) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_replacement_approval_decision_consumption(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        decision="approve",
        write_approval_decision=False,
    )

    assert result["replacement_approval_decision_status"] == "replacement_approval_already_approved"
    assert result["replacement_approval_consumption_status"] == "replacement_approval_consumption_ready_no_trusted_write"
    assert result["replacement_approval_consumption_ready"] is True
    assert result["approval_decision_written"] is False
    assert result["approval_consumed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_replacement_approval_decision_consumption_rejects_without_trusted_writes(siteops_vault: Path) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    result = candidate_promotion_replacement_approval_decision_consumption(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        decision="reject",
        write_approval_decision=True,
    )

    replacement = json.loads(Path(writer["approval_ref"]).read_text(encoding="utf-8"))
    assert result["replacement_approval_decision_status"] == "replacement_approval_decision_written"
    assert result["replacement_approval_consumption_status"] == "replacement_approval_rejected_not_consumed"
    assert result["replacement_approval_consumption_ready"] is False
    assert result["approval_decision_written"] is True
    assert result["approval_consumed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert replacement["status"] == "rejected"


def test_candidate_trusted_inactive_artifact_writer_preflight_ready_after_bound_replacement_approval(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
        reason="approved for inactive artifact preflight",
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
    )

    checks = {item["check_id"]: item for item in result["preflight_checks"]}
    target_paths = result["target_paths"]
    assert result["trusted_inactive_artifact_writer_preflight_status"] == "trusted_inactive_artifact_writer_preflight_ready_no_write"
    assert result["replacement_approval_consumption_ready"] is True
    assert result["write_preflight_pass"] is True
    assert checks["replacement_approval_bound_and_approved"]["passed"] is True
    assert checks["inactive_artifact_payloads_valid"]["passed"] is True
    assert checks["target_paths_confined_and_clear"]["passed"] is True
    assert checks["activation_disabled"]["passed"] is True
    assert target_paths["browser_skill"].endswith("runtime/browser_skills/skills/example.safe_candidate.yaml")
    assert target_paths["siteops_skill_card"].endswith("runtime/siteops/registry/skill_cards/example.safe_candidate.json")
    assert result["writes_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["activation_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_preflight_is_no_write(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-preflight",
            "candidate_run_123",
            "--replacement-approval-id",
            writer["approval_request_artifact"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["trusted_inactive_artifact_writer_preflight_status"] == "trusted_inactive_artifact_writer_preflight_ready_no_write"
    assert result["write_preflight_pass"] is True
    assert result["writes_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_implementation_request_ready_no_write(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
    )

    checks = result["implementation_request_checks"]
    target_paths = result["implementation_request_artifact"]["target_paths"]
    assert (
        result["trusted_inactive_artifact_writer_implementation_request_status"]
        == "trusted_inactive_artifact_writer_implementation_request_ready_no_write"
    )
    assert result["request_ready_no_write"] is True
    assert checks["trusted_inactive_artifact_writer_preflight_ready"]["passed"] is True
    assert checks["replacement_approval_bound_and_approved"]["passed"] is True
    assert target_paths["browser_skill"].endswith("runtime/browser_skills/skills/example.safe_candidate.yaml")
    assert target_paths["siteops_skill_card"].endswith("runtime/siteops/registry/skill_cards/example.safe_candidate.json")
    assert result["implementation_request_artifact_written"] is False
    assert result["writes_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["trusted_inactive_artifact_writer_implemented"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["activation_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_candidate_trusted_inactive_artifact_writer_implementation_request_blocks_pending_replacement(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
    )

    assert result["trusted_inactive_artifact_writer_implementation_request_status"].startswith(
        "blocked_trusted_inactive_artifact_writer_preflight"
    )
    assert result["request_ready_no_write"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["writes_performed"] is False
    assert result["inactive_artifacts_written"] is False


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_implementation_request_is_no_write(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-implementation-request",
            "candidate_run_123",
            "--replacement-approval-id",
            writer["approval_request_artifact"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert (
        result["trusted_inactive_artifact_writer_implementation_request_status"]
        == "trusted_inactive_artifact_writer_implementation_request_ready_no_write"
    )
    assert result["request_ready_no_write"] is True
    assert result["implementation_request_artifact_written"] is False
    assert result["writes_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_implementation_approval_approve_no_write(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        decision="approve",
        actor="local-user",
        reason="approve future inactive writer implementation",
    )

    assert (
        result["trusted_inactive_artifact_writer_implementation_approval_status"]
        == "trusted_inactive_artifact_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["implementation_patch_allowed_next_pass"] is True
    assert result["implementation_rejected_no_write"] is False
    assert result["implementation_approval_record"]["durable_record_written"] is False
    assert result["implementation_approval_record_written"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["approval_decision_written"] is False
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["trusted_inactive_artifact_writer_implemented"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["activation_allowed"] is False
    assert result["browser_execution_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_implementation_approval_reject_no_write(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        decision="reject",
        actor="local-user",
    )

    assert (
        result["trusted_inactive_artifact_writer_implementation_approval_status"]
        == "trusted_inactive_artifact_writer_implementation_rejected_no_write"
    )
    assert result["implementation_patch_allowed_next_pass"] is False
    assert result["implementation_rejected_no_write"] is True
    assert result["implementation_approval_record_written"] is False
    assert result["writes_performed"] is False


def test_candidate_trusted_inactive_artifact_writer_implementation_approval_blocks_pending_replacement(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_implementation_approval(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        decision="approve",
        actor="local-user",
    )

    assert result["trusted_inactive_artifact_writer_implementation_approval_status"].startswith(
        "blocked_trusted_inactive_artifact_writer_implementation_request"
    )
    assert result["implementation_patch_allowed_next_pass"] is False
    assert result["implementation_approval_record_written"] is False
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["writes_performed"] is False


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_implementation_approval_is_no_write(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-implementation-approval",
            "candidate_run_123",
            "--replacement-approval-id",
            writer["approval_request_artifact"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--decision",
            "approve",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert (
        result["trusted_inactive_artifact_writer_implementation_approval_status"]
        == "trusted_inactive_artifact_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["implementation_patch_allowed_next_pass"] is True
    assert result["implementation_approval_record_written"] is False
    assert result["implementation_request_artifact_written"] is False
    assert result["writes_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_implementation_blocks_without_gate_allowance(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
        actor="local-user",
        reason="test denied gate",
        write_inactive_artifacts=True,
    )

    target_paths = result["target_paths"]
    assert result["trusted_inactive_artifact_writer_implementation_status"] == "blocked_gate_operation_not_allowlisted"
    assert result["writer_ready_to_write"] is False
    assert result["gate_operation_allowed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["writes_performed"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_candidate_trusted_inactive_artifact_writer_implementation_writes_inactive_artifacts_when_gate_allows(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replacement_approval_id = "approval_test_bound_replacement"
    scope = {"tenant_id": "local", "workspace_id": "default", "user_id": "local-user"}
    target_paths = {
        "browser_skill": "runtime/browser_skills/skills/example.safe_candidate.yaml",
        "siteops_skill_card": "runtime/siteops/registry/skill_cards/example.safe_candidate.json",
    }
    payloads = {
        "browser_skill": {
            "skill_id": "example.safe_candidate",
            "source_candidate_id": "candidate_run_123",
            "tenant_id": "local",
            "workspace_id": "default",
            "created_by": "local-user",
            "status": "inactive_review",
            "activation_allowed": False,
            "provenance": {"approval_id": replacement_approval_id},
        },
        "siteops_skill_card": {
            "skill_id": "example.safe_candidate",
            "source_candidate_id": "candidate_run_123",
            "tenant_id": "local",
            "workspace_id": "default",
            "created_by": "local-user",
            "status": "inactive_review",
            "activation_allowed": False,
            "provenance": {"approval_id": replacement_approval_id},
        },
    }
    monkeypatch.setattr(
        candidate_promotions_module,
        "candidate_promotion_trusted_inactive_artifact_writer_implementation_approval",
        lambda *args, **kwargs: {
            "candidate_id": "candidate_run_123",
            "proposed_skill_id": "example.safe_candidate",
            "scope": scope,
            "actor": "local-user",
            "implementation_patch_allowed_next_pass": True,
            "trusted_inactive_artifact_writer_implementation_approval_status": (
                "trusted_inactive_artifact_writer_implementation_approved_for_next_pass_no_write"
            ),
            "denied_effects": [],
        },
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "candidate_promotion_trusted_inactive_artifact_writer_preflight",
        lambda *args, **kwargs: {
            "candidate_id": "candidate_run_123",
            "proposed_skill_id": "example.safe_candidate",
            "scope": scope,
            "replacement_approval_id": replacement_approval_id,
            "write_preflight_pass": True,
            "trusted_inactive_artifact_writer_preflight_status": (
                "trusted_inactive_artifact_writer_preflight_ready_no_write"
            ),
            "target_paths": target_paths,
            "target_path_checks": [
                {
                    "artifact_kind": "browser_skill",
                    "target_path": target_paths["browser_skill"],
                    "path_confined": True,
                    "collision_detected": False,
                },
                {
                    "artifact_kind": "siteops_skill_card",
                    "target_path": target_paths["siteops_skill_card"],
                    "path_confined": True,
                    "collision_detected": False,
                },
            ],
            "proposed_artifact_payloads": payloads,
        },
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (True, "mock_gate_allowed"),
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        reason="test gate-allowed inactive write",
        write_inactive_artifacts=True,
    )

    target_paths = result["target_paths"]
    assert result["trusted_inactive_artifact_writer_implementation_status"] == "trusted_inactive_artifacts_written_inactive_review"
    assert result["writer_ready_to_write"] is True
    assert result["gate_operation_allowed"] is True
    assert result["inactive_artifacts_written"] is True
    browser_skill_path = siteops_vault / target_paths["browser_skill"]
    siteops_card_path = siteops_vault / target_paths["siteops_skill_card"]
    siteops_payload = json.loads(siteops_card_path.read_text(encoding="utf-8"))
    browser_skill_text = browser_skill_path.read_text(encoding="utf-8")

    assert result["browser_skill_artifact_written"] is True
    assert result["siteops_skill_card_artifact_written"] is True
    assert result["run_record_written"] is True
    assert result["audit_events_written"] is True
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert browser_skill_path.exists()
    assert siteops_card_path.exists()
    assert "status: inactive_review" in browser_skill_text
    assert "activation_allowed: false" in browser_skill_text
    assert siteops_payload["status"] == "inactive_review"
    assert siteops_payload["activation_allowed"] is False
    assert siteops_payload["provenance"]["approval_id"] == replacement_approval_id


def test_apply_trusted_candidate_artifacts_blocks_without_gate_allowance(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    result = apply_trusted_candidate_artifacts(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        reason="test canonical executor gate denial",
        write_inactive_artifacts=True,
    )

    target_paths = result["target_paths"]
    assert result["action"] == "browser_skill_candidate.apply_trusted_candidate_artifacts"
    assert result["executor_entrypoint"] == "apply_trusted_candidate_artifacts"
    assert result["siteops_guarded_executor"] is True
    assert result["trusted_inactive_artifact_writer_implementation_status"] == "blocked_gate_operation_not_allowlisted"
    assert result["gate_operation_allowed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["writes_performed"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_apply_trusted_candidate_artifacts_is_gate_blocked(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "apply-trusted-candidate-artifacts",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--write-inactive-artifacts",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["action"] == "browser_skill_candidate.apply_trusted_candidate_artifacts"
    assert result["executor_entrypoint"] == "apply_trusted_candidate_artifacts"
    assert result["trusted_inactive_artifact_writer_implementation_status"] == "blocked_gate_operation_not_allowlisted"
    assert result["gate_operation_allowed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["writes_performed"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_live_gate_readiness_is_no_write_packet(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_live_gate_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        reason="test live gate readiness",
    )

    target_paths = result["target_paths"]
    assert result["trusted_inactive_artifact_writer_live_gate_readiness_status"] == (
        "trusted_inactive_artifact_writer_live_gate_readiness_ready_no_write"
    )
    assert result["gate_patch_ready_for_operator_review"] is True
    assert result["gate_operation_allowed"] is False
    assert result["proposed_gate_patch"]["patch_performed"] is False
    assert result["proposed_gate_patch"]["runtime_operation_policy_file"] == "runtime/chaseos_gate.py"
    assert result["proposed_gate_patch"]["gateway_allowlists_file"] == "runtime/policy/gateway_allowlists.json"
    assert result["fail_closed_live_smoke"]["required_before_any_live_write"] is True
    assert result["writes_performed"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_live_gate_readiness_non_mutating(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-live-gate-readiness",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_patch_ready_for_operator_review"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["writes_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_allowlist_approval_request_writes_pending_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    preview = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=False,
    )
    result = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )

    approval_path = Path(result["approval_ref"])
    target_paths = result["target_paths"]
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    assert preview["gate_allowlist_approval_request_status"] == "gate_allowlist_approval_request_ready_preview_only"
    assert preview["approval_request_written"] is False
    assert result["gate_allowlist_approval_request_status"] == (
        "gate_allowlist_approval_request_written_pending_operator_decision"
    )
    assert result["approval_request_written"] is True
    assert result["approval_request_pending"] is True
    assert approval_path.exists()
    assert approval_payload["status"] == "pending"
    assert approval_payload["action"] == "browser_skill_candidate.gate_allowlist_approval_request"
    assert approval_payload["metadata"]["gate_operation"] == PROMOTION_GATE_APPLY_OPERATION
    assert approval_payload["metadata"]["secrets_or_session_state_included"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_allowlist_approval_request_write_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-allowlist-approval-request",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--requested-by",
            "local-user",
            "--write-approval-request",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["approval_request_written"] is True
    assert Path(result["approval_ref"]).exists()
    assert result["gate_policy_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight_blocks_pending_and_accepts_approved(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]

    pending = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approved = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    target_paths = approved["target_paths"]
    assert pending["gate_allowlist_decision_preflight_status"] == "blocked_pending_gate_allowlist_approval"
    assert pending["ready_for_gate_policy_patch_next_pass"] is False
    assert approved["gate_allowlist_decision_preflight_status"] == (
        "gate_allowlist_decision_preflight_ready_no_mutation"
    )
    assert approved["approval_status"] == "approved"
    assert approved["digest_matches"] is True
    assert approved["ready_for_gate_policy_patch_next_pass"] is True
    assert approved["approval_consumed"] is False
    assert approved["gate_policy_change_performed"] is False
    assert approved["allowlist_change_performed"] is False
    assert approved["inactive_artifacts_written"] is False
    assert approved["browser_execution_allowed"] is False
    assert approved["agent_bus_enqueue_allowed"] is False
    assert approved["canonical_writeback_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight_read_only(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        approval_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-allowlist-decision-preflight",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            approval_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_allowlist_decision_preflight_status"] == (
        "gate_allowlist_decision_preflight_ready_no_mutation"
    )
    assert result["ready_for_gate_policy_patch_next_pass"] is True
    assert result["approval_consumed"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight_reports_pending_and_approved(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]

    pending = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approved = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    assert pending["gate_allowlist_decision_preflight_status"] == "blocked_pending_gate_allowlist_approval"
    assert pending["ready_for_gate_policy_patch_next_pass"] is False
    assert pending["digest_matches"] is True
    assert approved["gate_allowlist_decision_preflight_status"] == (
        "gate_allowlist_decision_preflight_ready_no_mutation"
    )
    assert approved["approval_status"] == "approved"
    assert approved["ready_for_gate_policy_patch_next_pass"] is True
    assert approved["approved_for_future_gate_policy_patch_review"] is True
    assert approved["gate_policy_change_performed"] is False
    assert approved["allowlist_change_performed"] is False
    assert approved["inactive_artifacts_written"] is False
    assert approved["approval_consumed"] is False
    assert approved["browser_execution_allowed"] is False
    assert approved["agent_bus_enqueue_allowed"] is False
    assert approved["canonical_writeback_allowed"] is False


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_allowlist_decision_preflight_non_mutating(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-allowlist-decision-preflight",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["ready_for_gate_policy_patch_next_pass"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_plan_is_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    plan = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_plan(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    assert plan["gate_policy_patch_plan_status"] == "gate_policy_patch_plan_ready_no_write"
    assert plan["ready_for_gate_policy_write_next_pass"] is True
    assert plan["policy_patch_plan"]["runtime_operation_policy_change"]["file"] == "runtime/chaseos_gate.py"
    assert plan["policy_patch_plan"]["gateway_allowlists_change"]["file"] == "runtime/policy/gateway_allowlists.json"
    assert plan["policy_patch_plan"]["patch_performed"] is False
    assert plan["gate_policy_change_performed"] is False
    assert plan["allowlist_change_performed"] is False
    assert plan["policy_file_write_allowed"] is False
    assert plan["approval_consumed"] is False
    assert plan["inactive_artifacts_written"] is False
    assert plan["browser_execution_allowed"] is False
    assert plan["agent_bus_enqueue_allowed"] is False
    assert plan["canonical_writeback_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_plan_non_mutating(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-plan",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_plan_status"] == "gate_policy_patch_plan_ready_no_write"
    assert result["ready_for_gate_policy_write_next_pass"] is True
    assert result["policy_patch_plan"]["patch_performed"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_plan_is_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    plan = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_plan(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    target_paths = plan["target_paths"]
    desired_entry = plan["policy_patch_plan"]["runtime_operation_policy_change"]["desired_entry"]
    assert plan["gate_policy_patch_plan_status"] == "gate_policy_patch_plan_ready_no_write"
    assert plan["ready_for_gate_policy_write_next_pass"] is True
    assert desired_entry["gateway_write_categories"] == [
        "browser_skills_inactive_review",
        "siteops_skill_cards_inactive_review",
    ]
    assert plan["policy_patch_plan"]["gateway_allowlists_change"]["desired_entries"] == {
        "browser_skills_inactive_review": ["runtime/browser_skills/skills/*.yaml"],
        "siteops_skill_cards_inactive_review": [
            "runtime/siteops/registry/skill_cards/*.json"
        ],
    }
    assert plan["gate_policy_change_performed"] is False
    assert plan["allowlist_change_performed"] is False
    assert plan["inactive_artifacts_written"] is False
    assert plan["approval_consumed"] is False
    assert plan["browser_execution_allowed"] is False
    assert plan["agent_bus_enqueue_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_plan_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-plan",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_plan_status"] == "gate_policy_patch_plan_ready_no_write"
    assert result["ready_for_gate_policy_write_next_pass"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_application_design_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    design = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    assert design["gate_policy_patch_application_design_status"] == (
        "gate_policy_patch_application_design_ready_no_write"
    )
    assert design["ready_for_gate_policy_application_next_pass"] is True
    transaction = design["policy_patch_application_design"]
    assert transaction["status"] == "design_only"
    assert transaction["write_performed"] is False
    assert transaction["requires_explicit_write_flag"] == "--apply-gate-policy-patch"
    assert "runtime/chaseos_gate.py" in transaction["target_files"]
    assert "runtime/policy/gateway_allowlists.json" in transaction["target_files"]
    assert design["gate_policy_change_performed"] is False
    assert design["allowlist_change_performed"] is False
    assert design["approval_consumed"] is False
    assert design["inactive_artifacts_written"] is False
    assert design["browser_execution_allowed"] is False
    assert design["agent_bus_enqueue_allowed"] is False
    assert design["canonical_writeback_allowed"] is False


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_application_design_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )
    replacement_approval_id = writer["approval_request_artifact"]["approval_id"]
    decide_approval_request(
        siteops_vault,
        replacement_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    monkeypatch.setattr(
        candidate_promotions_module,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "mock_gate_denied"),
    )
    approval_request = candidate_promotion_trusted_inactive_artifact_writer_gate_allowlist_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    gate_approval_id = approval_request["approval_id"]
    decide_approval_request(
        siteops_vault,
        gate_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-application-design",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_application_design_status"] == (
        "gate_policy_patch_application_design_ready_no_write"
    )
    assert result["ready_for_gate_policy_application_next_pass"] is True
    assert result["policy_patch_application_design"]["write_performed"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_application_design_is_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    design = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    target_paths = design["target_paths"]
    application_design = design["policy_patch_application_design"]
    checks = {check["check_id"]: check for check in design["policy_patch_application_checks"]}
    assert design["gate_policy_patch_application_design_status"] == (
        "gate_policy_patch_application_design_ready_no_write"
    )
    assert design["ready_for_gate_policy_application_next_pass"] is True
    assert application_design["status"] == "design_only"
    assert application_design["write_performed"] is False
    assert application_design["requires_explicit_write_flag"] == "--apply-gate-policy-patch"
    assert application_design["target_files"] == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    assert checks["policy_application_disabled_this_pass"]["passed"] is True
    assert design["gate_policy_application_allowed_in_this_pass"] is False
    assert design["gate_policy_change_performed"] is False
    assert design["allowlist_change_performed"] is False
    assert design["policy_file_write_allowed"] is False
    assert design["approval_consumed"] is False
    assert design["inactive_artifacts_written"] is False
    assert design["browser_execution_allowed"] is False
    assert design["agent_bus_enqueue_allowed"] is False
    assert design["canonical_writeback_allowed"] is False
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_application_design_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-application-design",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_application_design_status"] == (
        "gate_policy_patch_application_design_ready_no_write"
    )
    assert result["ready_for_gate_policy_application_next_pass"] is True
    assert result["gate_policy_patch_plan_status"] == "gate_policy_patch_plan_ready_no_write"
    assert result["policy_patch_application_design"]["write_performed"] is False
    assert result["gate_policy_application_allowed_in_this_pass"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    preflight = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    checks = {
        check["check_id"]: check
        for check in preflight["policy_patch_application_preflight_checks"]
    }
    current_files = preflight["current_file_preflight"]
    target_paths = preflight["target_paths"]
    assert preflight["gate_policy_patch_application_preflight_status"] == (
        "gate_policy_patch_application_preflight_ready_no_write"
    )
    assert preflight["ready_for_gate_policy_application_write_next_pass"] is True
    assert current_files["runtime_policy"]["parse_ok"] is True
    assert current_files["gateway_allowlists"]["parse_ok"] is True
    assert current_files["runtime_policy"]["operation_already_present"] is False
    assert current_files["desired_category_absence"] == {
        "browser_skills_inactive_review": True,
        "siteops_skill_cards_inactive_review": True,
    }
    assert checks["gate_operation_absent_before_patch"]["passed"] is True
    assert checks["inactive_review_categories_absent_before_patch"]["passed"] is True
    assert checks["rollback_audit_artifact_shape_ready"]["passed"] is True
    assert preflight["rollback_audit_artifact_preview"]["write_allowed_in_this_pass"] is False
    assert preflight["gate_policy_application_allowed_in_this_pass"] is False
    assert preflight["gate_policy_change_performed"] is False
    assert preflight["allowlist_change_performed"] is False
    assert preflight["policy_file_write_allowed"] is False
    assert preflight["rollback_audit_artifact_written"] is False
    assert preflight["approval_consumed"] is False
    assert preflight["inactive_artifacts_written"] is False
    assert preflight["browser_execution_allowed"] is False
    assert preflight["agent_bus_enqueue_allowed"] is False
    assert preflight["canonical_writeback_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_application_preflight_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-application-preflight",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_application_preflight_status"] == (
        "gate_policy_patch_application_preflight_ready_no_write"
    )
    assert result["ready_for_gate_policy_application_write_next_pass"] is True
    assert result["current_file_preflight"]["runtime_policy"]["parse_ok"] is True
    assert result["current_file_preflight"]["gateway_allowlists"]["parse_ok"] is True
    assert result["gate_policy_application_allowed_in_this_pass"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    guard = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    checks = {
        check["check_id"]: check
        for check in guard["policy_patch_application_write_guard_checks"]
    }
    contract = guard["write_guard_contract"]
    target_paths = guard["target_paths"]
    assert guard["gate_policy_patch_application_write_guard_status"] == (
        "gate_policy_patch_application_write_guard_ready_no_write"
    )
    assert guard["ready_for_gate_policy_patch_writer_next_pass"] is True
    assert contract["status"] == "write_guard_contract_only"
    assert contract["explicit_write_flag"] == "--apply-gate-policy-patch"
    assert contract["explicit_write_flag_supported_in_this_pass"] is False
    assert contract["allowed_target_files"] == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    assert contract["atomic_write_policy"]["allowed_in_future_write_pass_only"] is True
    assert checks["explicit_apply_flag_unsupported_this_pass"]["passed"] is True
    assert checks["guard_current_file_digests_present"]["passed"] is True
    assert checks["guard_target_files_minimal"]["passed"] is True
    assert checks["guard_writes_disabled_this_pass"]["passed"] is True
    assert guard["apply_gate_policy_patch_flag_supported"] is False
    assert guard["gate_policy_patch_writer_implemented"] is False
    assert guard["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert guard["gate_policy_change_performed"] is False
    assert guard["allowlist_change_performed"] is False
    assert guard["policy_file_write_allowed"] is False
    assert guard["rollback_audit_artifact_written"] is False
    assert guard["approval_consumed"] is False
    assert guard["inactive_artifacts_written"] is False
    assert guard["browser_execution_allowed"] is False
    assert guard["agent_bus_enqueue_allowed"] is False
    assert guard["provider_api_call_allowed"] is False
    assert guard["activation_allowed"] is False
    assert guard["canonical_writeback_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before
    assert not (siteops_vault / target_paths["browser_skill"]).exists()
    assert not (siteops_vault / target_paths["siteops_skill_card"]).exists()


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_contract_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-application-write-guard",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_application_write_guard_status"] == (
        "gate_policy_patch_application_write_guard_ready_no_write"
    )
    assert result["ready_for_gate_policy_patch_writer_next_pass"] is True
    assert result["write_guard_contract"]["explicit_write_flag_supported_in_this_pass"] is False
    assert result["apply_gate_policy_patch_flag_supported"] is False
    assert result["gate_policy_patch_writer_implemented"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_application_write_guard_rejects_apply_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    try:
        cli.main(
            [
                "siteops",
                "candidates",
                "trusted-inactive-artifact-writer-gate-policy-patch-application-write-guard",
                "candidate_run_123",
                "--replacement-approval-id",
                "approval_x",
                "--gate-approval-id",
                "approval_gate_x",
                "--tenant",
                "local",
                "--user",
                "local-user",
                "--actor",
                "local-user",
                "--apply-gate-policy-patch",
            ]
        )
    except SystemExit as exc:
        exit_code = exc.code
    else:
        exit_code = 0
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "unrecognized arguments: --apply-gate-policy-patch" in captured.err


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_writer_design_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    design = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in design["gate_policy_patch_writer_design_checks"]}
    writer_design = design["gate_policy_patch_writer_design"]
    assert design["gate_policy_patch_writer_design_status"] == "gate_policy_patch_writer_design_ready_no_write"
    assert design["ready_for_gate_policy_patch_writer_implementation_next_pass"] is True
    assert writer_design["status"] in {"design_only", "writer_design_only"}
    assert writer_design["explicit_write_flag"] == "--apply-gate-policy-patch"
    assert writer_design["explicit_write_flag_supported_in_this_pass"] is False
    assert writer_design["future_writer_requires_explicit_write_flag"] is True
    assert writer_design["allowed_target_files"] == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    assert writer_design["requires_approved_patch_plan_evidence"] is True
    assert writer_design["requires_write_guard_evidence"] is True
    assert writer_design["requires_fail_closed_live_smoke_evidence"] is True
    assert writer_design["requires_operator_approval"] is True
    assert writer_design["atomicity_contract"]["backup_before_write"] is True
    assert writer_design["atomicity_contract"]["rollback_on_verification_failure"] is True
    assert checks["writer_design_target_files_minimal"]["passed"] is True
    assert checks["writer_design_writes_disabled_this_pass"]["passed"] is True
    assert design["gate_policy_patch_writer_implemented"] is False
    assert design["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert design["gate_policy_change_performed"] is False
    assert design["allowlist_change_performed"] is False
    assert design["approval_consumed"] is False
    assert design["rollback_audit_artifact_written"] is False
    assert design["inactive_artifacts_written"] is False
    assert design["activation_allowed"] is False
    assert design["browser_execution_allowed"] is False
    assert design["agent_bus_enqueue_allowed"] is False
    assert design["provider_api_call_allowed"] is False
    assert design["canonical_writeback_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_design_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-writer-design",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_writer_design_status"] == "gate_policy_patch_writer_design_ready_no_write"
    assert result["ready_for_gate_policy_patch_writer_implementation_next_pass"] is True
    assert result["gate_policy_patch_writer_implemented"] is False
    assert result["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_design_rejects_apply_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    try:
        cli.main(
            [
                "siteops",
                "candidates",
                "trusted-inactive-artifact-writer-gate-policy-patch-writer-design",
                "candidate_run_123",
                "--replacement-approval-id",
                "approval_x",
                "--gate-approval-id",
                "approval_gate_x",
                "--tenant",
                "local",
                "--user",
                "local-user",
                "--actor",
                "local-user",
                "--apply-gate-policy-patch",
            ]
        )
    except SystemExit as exc:
        exit_code = exc.code
    else:
        exit_code = 0
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "unrecognized arguments: --apply-gate-policy-patch" in captured.err


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_writer_design_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    design = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_design(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    checks = {check["check_id"]: check for check in design["policy_patch_writer_design_checks"]}
    writer_design = design["policy_patch_writer_design"]
    assert design["gate_policy_patch_writer_design_status"] == (
        "gate_policy_patch_writer_design_ready_no_write"
    )
    assert design["ready_for_gate_policy_patch_writer_implementation_request_next_pass"] is True
    assert writer_design["status"] == "writer_design_only"
    assert writer_design["future_writer_implemented"] is False
    assert writer_design["future_explicit_write_flag"] == "--apply-gate-policy-patch"
    assert writer_design["future_explicit_write_flag_supported_here"] is False
    assert writer_design["target_files"] == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    assert checks["writer_design_guard_ready"]["passed"] is True
    assert checks["writer_design_target_files_minimal"]["passed"] is True
    assert checks["writer_design_current_digests_present"]["passed"] is True
    assert checks["writer_design_explicit_apply_flag_still_unsupported_here"]["passed"] is True
    assert checks["writer_design_writes_disabled_this_pass"]["passed"] is True
    assert design["apply_gate_policy_patch_flag_supported"] is False
    assert design["gate_policy_patch_writer_implemented"] is False
    assert design["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert design["gate_policy_change_performed"] is False
    assert design["allowlist_change_performed"] is False
    assert design["backup_artifact_written"] is False
    assert design["rollback_audit_artifact_written"] is False
    assert design["approval_consumed"] is False
    assert design["inactive_artifacts_written"] is False
    assert design["browser_execution_allowed"] is False
    assert design["agent_bus_enqueue_allowed"] is False
    assert design["provider_api_call_allowed"] is False
    assert design["activation_allowed"] is False
    assert design["canonical_writeback_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_design_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-writer-design",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_writer_design_status"] == (
        "gate_policy_patch_writer_design_ready_no_write"
    )
    assert result["ready_for_gate_policy_patch_writer_implementation_request_next_pass"] is True
    assert result["policy_patch_writer_design"]["future_writer_implemented"] is False
    assert result["gate_policy_patch_writer_implemented"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["backup_artifact_written"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_design_rejects_apply_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    try:
        cli.main(
            [
                "siteops",
                "candidates",
                "trusted-inactive-artifact-writer-gate-policy-patch-writer-design",
                "candidate_run_123",
                "--replacement-approval-id",
                "approval_x",
                "--gate-approval-id",
                "approval_gate_x",
                "--tenant",
                "local",
                "--user",
                "local-user",
                "--actor",
                "local-user",
                "--apply-gate-policy-patch",
            ]
        )
    except SystemExit as exc:
        exit_code = exc.code
    else:
        exit_code = 0
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "unrecognized arguments: --apply-gate-policy-patch" in captured.err


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    request = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    checks = {
        check["check_id"]: check
        for check in request["gate_policy_patch_writer_implementation_request_checks"]
    }
    artifact = request["gate_policy_patch_writer_implementation_request"]
    assert request["gate_policy_patch_writer_implementation_request_status"] == (
        "gate_policy_patch_writer_implementation_request_ready_no_write"
    )
    assert request["ready_for_gate_policy_patch_writer_implementation_approval_next_pass"] is True
    assert artifact["status"] == "review_packet_only"
    assert artifact["request_type"] == "siteops_gate_policy_patch_writer_implementation_request"
    assert artifact["future_explicit_write_flag"] == "--apply-gate-policy-patch"
    assert artifact["target_files"] == [
        "runtime/chaseos_gate.py",
        "runtime/policy/gateway_allowlists.json",
    ]
    assert checks["writer_implementation_request_design_ready"]["passed"] is True
    assert checks["writer_implementation_request_exact_target_files"]["passed"] is True
    assert checks["writer_implementation_request_current_digests_present"]["passed"] is True
    assert checks["writer_implementation_request_future_apply_flag_required"]["passed"] is True
    assert checks["writer_implementation_request_backup_rollback_required"]["passed"] is True
    assert checks["writer_implementation_request_no_writes_this_pass"]["passed"] is True
    assert request["implementation_request_artifact_written"] is False
    assert request["apply_gate_policy_patch_flag_supported"] is False
    assert request["gate_policy_patch_writer_implemented"] is False
    assert request["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert request["gate_policy_change_performed"] is False
    assert request["allowlist_change_performed"] is False
    assert request["backup_artifact_written"] is False
    assert request["rollback_audit_artifact_written"] is False
    assert request["approval_consumed"] is False
    assert request["inactive_artifacts_written"] is False
    assert request["browser_execution_allowed"] is False
    assert request["agent_bus_enqueue_allowed"] is False
    assert request["provider_api_call_allowed"] is False
    assert request["activation_allowed"] is False
    assert request["canonical_writeback_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-request",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_writer_implementation_request_status"] == (
        "gate_policy_patch_writer_implementation_request_ready_no_write"
    )
    assert result["ready_for_gate_policy_patch_writer_implementation_approval_next_pass"] is True
    assert result["implementation_request_artifact_written"] is False
    assert result["gate_policy_patch_writer_implemented"] is False
    assert result["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["backup_artifact_written"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_request_rejects_apply_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    try:
        cli.main(
            [
                "siteops",
                "candidates",
                "trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-request",
                "candidate_run_123",
                "--replacement-approval-id",
                "approval_x",
                "--gate-approval-id",
                "approval_gate_x",
                "--tenant",
                "local",
                "--user",
                "local-user",
                "--actor",
                "local-user",
                "--apply-gate-policy-patch",
            ]
        )
    except SystemExit as exc:
        exit_code = exc.code
    else:
        exit_code = 0
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "unrecognized arguments: --apply-gate-policy-patch" in captured.err


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval_approve_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    result = (
        candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval(
            "candidate_run_123",
            siteops_vault,
            tenant_id="local",
            workspace_id="default",
            user_id="local-user",
            replacement_approval_id=replacement_approval_id,
            gate_approval_id=gate_approval_id,
            decision="approve",
            actor="local-user",
            reason="approve future Gate policy patch writer implementation",
        )
    )

    checks = result["gate_policy_patch_writer_implementation_approval_checks"]
    approval = result["gate_policy_patch_writer_implementation_approval"]
    assert result["gate_policy_patch_writer_implementation_approval_status"] == (
        "gate_policy_patch_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["gate_policy_patch_writer_implementation_allowed_next_pass"] is True
    assert result["ready_for_gate_policy_patch_writer_implementation_next_pass"] is True
    assert approval["record_type"] == "siteops_gate_policy_patch_writer_implementation_approval"
    assert approval["durable_record_written"] is False
    assert approval["future_explicit_write_flag"] == "--apply-gate-policy-patch"
    assert checks["implementation_request_ready"]["passed"] is True
    assert checks["target_files_bound"]["passed"] is True
    assert checks["current_digests_bound"]["passed"] is True
    assert checks["future_apply_flag_bound_but_unsupported_here"]["passed"] is True
    assert result["implementation_approval_record_written"] is False
    assert result["apply_gate_policy_patch_flag_supported"] is False
    assert result["gate_policy_patch_writer_implemented"] is False
    assert result["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["backup_artifact_written"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["provider_api_call_allowed"] is False
    assert result["activation_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval_reject_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    result = (
        candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval(
            "candidate_run_123",
            siteops_vault,
            tenant_id="local",
            workspace_id="default",
            user_id="local-user",
            replacement_approval_id=replacement_approval_id,
            gate_approval_id=gate_approval_id,
            decision="reject",
            actor="local-user",
        )
    )

    assert result["gate_policy_patch_writer_implementation_approval_status"] == (
        "gate_policy_patch_writer_implementation_rejected_no_write"
    )
    assert result["gate_policy_patch_writer_implementation_allowed_next_pass"] is False
    assert result["gate_policy_patch_writer_implementation_rejected_no_write"] is True
    assert result["implementation_approval_record_written"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["writes_performed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-approval",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--decision",
            "approve",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_writer_implementation_approval_status"] == (
        "gate_policy_patch_writer_implementation_approved_for_next_pass_no_write"
    )
    assert result["gate_policy_patch_writer_implementation_allowed_next_pass"] is True
    assert result["implementation_approval_record_written"] is False
    assert result["apply_gate_policy_patch_flag_supported"] is False
    assert result["gate_policy_patch_writer_implemented"] is False
    assert result["gate_policy_patch_writer_allowed_in_this_pass"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["backup_artifact_written"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_approval_rejects_apply_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    try:
        cli.main(
            [
                "siteops",
                "candidates",
                "trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-approval",
                "candidate_run_123",
                "--replacement-approval-id",
                "approval_x",
                "--gate-approval-id",
                "approval_gate_x",
                "--tenant",
                "local",
                "--user",
                "local-user",
                "--actor",
                "local-user",
                "--decision",
                "approve",
                "--apply-gate-policy-patch",
            ]
        )
    except SystemExit as exc:
        exit_code = exc.code
    else:
        exit_code = 0
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "unrecognized arguments: --apply-gate-policy-patch" in captured.err


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_dry_run_no_write(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
    )

    assert result["gate_policy_patch_writer_implementation_status"] == (
        "gate_policy_patch_writer_implementation_ready_dry_run"
    )
    assert result["apply_gate_policy_patch_flag_supported"] is True
    assert result["apply_gate_policy_patch_requested"] is False
    assert result["write_preconditions_ready"] is True
    assert result["gate_policy_patch_writer_implemented"] is True
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["backup_artifact_written"] is False
    assert result["rollback_audit_artifact_written"] is False
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_candidate_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_apply_writes_only_gate_policy(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
        actor="local-user",
        apply_gate_policy_patch=True,
    )

    runtime_text = runtime_policy.read_text(encoding="utf-8")
    allowlists = json.loads(gateway_allowlists.read_text(encoding="utf-8"))
    backup_paths = result["backup_artifact_paths"]

    assert result["gate_policy_patch_writer_implementation_status"] == (
        "gate_policy_patch_writer_implementation_applied"
    )
    assert result["apply_gate_policy_patch_requested"] is True
    assert result["gate_policy_change_performed"] is True
    assert result["allowlist_change_performed"] is True
    assert result["backup_artifact_written"] is True
    assert result["rollback_audit_artifact_written"] is True
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert runtime_text.count(f'"{PROMOTION_GATE_APPLY_OPERATION}"') == 1
    assert allowlists["write_targets"]["browser_skills_inactive_review"] == [
        "runtime/browser_skills/skills/*.yaml"
    ]
    assert allowlists["write_targets"]["siteops_skill_cards_inactive_review"] == [
        "runtime/siteops/registry/skill_cards/*.json"
    ]
    assert (siteops_vault / backup_paths["runtime_policy"]).exists()
    assert (siteops_vault / backup_paths["gateway_allowlists"]).exists()
    rollback_audit = json.loads((siteops_vault / backup_paths["rollback_audit"]).read_text(encoding="utf-8"))
    assert rollback_audit["contains_secrets_or_session_state"] is False
    assert rollback_audit["rollback_performed"] is False


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_patch_writer_implementation_apply_writes_only_gate_policy(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation",
            "candidate_run_123",
            "--replacement-approval-id",
            replacement_approval_id,
            "--gate-approval-id",
            gate_approval_id,
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--apply-gate-policy-patch",
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_patch_writer_implementation_status"] == (
        "gate_policy_patch_writer_implementation_applied"
    )
    assert result["gate_policy_change_performed"] is True
    assert result["allowlist_change_performed"] is True
    assert result["backup_artifact_written"] is True
    assert result["rollback_audit_artifact_written"] is True
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False
    assert runtime_policy.read_text(encoding="utf-8").count(f'"{PROMOTION_GATE_APPLY_OPERATION}"') == 1
    assert json.loads(gateway_allowlists.read_text(encoding="utf-8"))["write_targets"][
        "browser_skills_inactive_review"
    ] == ["runtime/browser_skills/skills/*.yaml"]


def test_candidate_trusted_inactive_artifact_writer_gate_policy_live_application_readiness_blocks_without_approval_ids(
    siteops_vault: Path,
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")

    result = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_live_application_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    assert result["gate_policy_live_application_readiness_status"] == (
        "blocked_missing_gate_policy_live_application_approval_ids"
    )
    assert result["ready_for_live_gate_policy_application"] is False
    assert result["gate_policy_already_applied"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_candidate_trusted_inactive_artifact_writer_gate_policy_live_application_readiness_ready_with_approved_ids(
    siteops_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_gate_policy_application_preflight_files(siteops_vault)
    replacement_approval_id, gate_approval_id = _approved_gate_policy_patch_inputs(
        siteops_vault, monkeypatch
    )

    result = candidate_promotion_trusted_inactive_artifact_writer_gate_policy_live_application_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
        replacement_approval_id=replacement_approval_id,
        gate_approval_id=gate_approval_id,
    )

    assert result["gate_policy_live_application_readiness_status"] == (
        "gate_policy_live_application_ready_no_write"
    )
    assert result["ready_for_live_gate_policy_application"] is True
    assert result["writer_dry_run_status"] == "gate_policy_patch_writer_implementation_ready_dry_run"
    assert "--apply-gate-policy-patch" in result["live_apply_command_preview"]
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["backup_artifact_written"] is False
    assert result["approval_consumed"] is False
    assert result["inactive_artifacts_written"] is False


def test_siteops_candidate_cli_trusted_inactive_artifact_writer_gate_policy_live_application_readiness_no_write(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_policy, gateway_allowlists = _write_gate_policy_application_preflight_files(
        siteops_vault
    )
    runtime_before = runtime_policy.read_text(encoding="utf-8")
    allowlists_before = gateway_allowlists.read_text(encoding="utf-8")

    code = cli.main(
        [
            "siteops",
            "candidates",
            "trusted-inactive-artifact-writer-gate-policy-live-application-readiness",
            "candidate_run_123",
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["gate_policy_live_application_readiness_status"] == (
        "blocked_missing_gate_policy_live_application_approval_ids"
    )
    assert result["ready_for_live_gate_policy_application"] is False
    assert result["gate_policy_change_performed"] is False
    assert result["allowlist_change_performed"] is False
    assert result["inactive_artifacts_written"] is False
    assert runtime_policy.read_text(encoding="utf-8") == runtime_before
    assert gateway_allowlists.read_text(encoding="utf-8") == allowlists_before


def test_candidate_replacement_approval_decision_consumption_requires_full_scope(siteops_vault: Path) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    writer = candidate_promotion_bound_approval_writer_implementation(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_replacement_approval=True,
    )

    with pytest.raises(SiteOpsValidationError):
        candidate_promotion_replacement_approval_decision_consumption(
            "candidate_run_123",
            siteops_vault,
            tenant_id="local",
            workspace_id="default",
            user_id=None,
            replacement_approval_id=writer["approval_request_artifact"]["approval_id"],
            actor="local-user",
            decision="approve",
            write_approval_decision=False,
        )


# -- Activation boundary readiness tests ------------------------------------


def test_candidate_activation_boundary_readiness_ready_no_authority(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_boundary_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["ok"] is True
    assert result["activation_boundary_status"] == "activation_boundary_ready_no_authority"
    assert result["review_decision"] == "activation_contract_only_do_not_activate_in_this_pass"
    assert result["inactive_artifact_validator_status"] == "inactive_artifact_validator_ready_no_authority"
    assert result["collision_policy_status"] == "collision_policy_spec_ready_no_authority"
    assert result["activation_path_separated"] is True
    assert result["activation_requires_separate_workflow"] is True
    assert result["activation_requirements"]["separate_gate_operation"] == "siteops.browser_skill_candidate.activate_trusted_artifact"
    assert result["activation_requirements"]["requires_operator_approval"] is True
    assert result["activation_requirements"]["requires_inactive_artifact_present"] is True
    assert result["activation_requirements"]["requires_runtime_ownership_review"] is True
    assert result["activation_requirements"]["requires_post_activation_audit"] is True
    assert all(item["implemented"] is False for item in result["future_activation_steps"])
    assert all(item["allowed_in_this_pass"] is False for item in result["future_activation_steps"])
    assert "activate promoted skills" in result["blocked_actions"]
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    assert result["writes_performed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_boundary_readiness_blocks_pending_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_activation_boundary_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["activation_boundary_status"].startswith("blocked_collision_policy")
    assert result["review_decision"] == "blocked_before_activation_boundary"
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False


def test_siteops_candidate_cli_activation_boundary_readiness_is_non_mutating(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-boundary-readiness",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_boundary_status"] == "activation_boundary_ready_no_authority"
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_request_preview_is_non_mutating(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_approval_request=False,
    )

    assert result["activation_approval_request_status"] == "activation_approval_request_ready_preview_only"
    assert result["approval_request_written"] is False
    assert result["run_record_written"] is False
    assert result["audit_event_written"] is False
    assert result["writes_performed"] is False
    assert result["activation_ready_for_operator_review"] is True
    assert result["approval_request_artifact"]["activation_gate_operation"] == "siteops.browser_skill_candidate.activate_trusted_artifact"
    assert result["approval_request_artifact"]["activation_allowed_in_this_pass"] is False
    assert result["approval_request_artifact"]["trusted_artifact_write_allowed_in_this_pass"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["agent_bus_enqueue_allowed"] is False
    assert result["canonical_writeback_allowed"] is False
    run_dir = siteops_vault / "07_LOGS" / "SiteOps-Runs" / "local" / "default"
    assert not list(run_dir.glob("siteops_activation_approval_*.json"))
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_request_writes_pending_only(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )

    assert result["activation_approval_request_status"] == "activation_approval_request_written_pending_operator_decision"
    assert result["review_decision"] == "pending_operator_review_for_future_activation"
    assert result["approval_request_written"] is True
    assert result["approval_request_pending"] is True
    assert result["run_record_written"] is True
    assert result["audit_event_written"] is True
    assert result["writes_performed"] is True
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["trusted_artifacts_written"] is False
    approval = json.loads(Path(result["approval_ref"]).read_text(encoding="utf-8"))
    assert approval["status"] == "pending"
    assert approval["tenant_id"] == "local"
    assert approval["workspace_id"] == "default"
    assert approval["user_id"] == "local-user"
    assert approval["action"] == "siteops.browser_skill_candidate.activate_trusted_artifact"
    assert approval["required_approver_role"] == "tenant_admin"
    assert approval["metadata"]["candidate_id"] == "candidate_run_123"
    assert approval["metadata"]["proposed_skill_id"] == "example.safe_candidate"
    assert approval["metadata"]["source_approval_id"] == request["approval"]["approval_id"]
    assert approval["metadata"]["activation_performed"] is False
    assert approval["metadata"]["secrets_or_session_state_included"] is False
    run = json.loads(Path(result["run_ref"]).read_text(encoding="utf-8"))
    assert run["status"] == "approval_needed"
    assert run["outputs_ref"] == result["approval_ref"]
    audit_events = [
        json.loads(line)
        for line in Path(result["audit_ref"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(event["event_type"] == "activation_approval_request_created" for event in audit_events)
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_request_blocks_pending_source_approval(siteops_vault: Path) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )

    result = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        write_approval_request=True,
    )

    assert result["activation_approval_request_status"].startswith("blocked_activation_boundary_readiness")
    assert result["review_decision"] == "blocked_before_activation_approval_request"
    assert result["approval_request_written"] is False
    assert result["run_record_written"] is False
    assert result["audit_event_written"] is False
    assert result["writes_performed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    run_dir = siteops_vault / "07_LOGS" / "SiteOps-Runs" / "local" / "default"
    assert not list(run_dir.glob("siteops_activation_approval_*.json"))


def test_siteops_candidate_cli_activation_approval_request_writes_pending_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-request",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--write-approval-request",
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_request_status"] == "activation_approval_request_written_pending_operator_decision"
    assert result["approval_request_written"] is True
    assert result["run_record_written"] is True
    assert result["audit_event_written"] is True
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False
    assert Path(result["approval_ref"]).exists()
    assert Path(result["run_ref"]).exists()
    assert Path(result["audit_ref"]).exists()
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_candidate_activation_approval_decision_preflight_blocks_pending_and_accepts_approved(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    activation_approval_id = activation_request["approval_id"]
    before = json.loads(Path(activation_request["approval_ref"]).read_text(encoding="utf-8"))

    pending = candidate_promotion_activation_approval_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_approval_id,
        actor="local-user",
    )
    decide_approval_request(
        siteops_vault,
        activation_approval_id,
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    approved = candidate_promotion_activation_approval_decision_preflight(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        source_approval_id=request["approval"]["approval_id"],
        activation_approval_id=activation_approval_id,
        actor="local-user",
    )

    assert pending["activation_approval_decision_preflight_status"] == "blocked_pending_activation_approval"
    assert pending["ready_for_activation_consumer_next_pass"] is False
    assert pending["digest_matches"] is True
    assert pending["approval_decision_written"] is False
    assert pending["approval_consumed"] is False
    assert pending["activation_performed"] is False
    assert pending["writes_performed"] is False
    assert approved["activation_approval_decision_preflight_status"] == (
        "activation_approval_decision_preflight_ready_no_mutation"
    )
    assert approved["approval_status"] == "approved"
    assert approved["ready_for_activation_consumer_next_pass"] is True
    assert approved["approved_for_future_activation_consumer_review"] is True
    assert approved["digest_matches"] is True
    assert approved["approval_decision_written"] is False
    assert approved["approval_consumed"] is False
    assert approved["activation_allowed"] is False
    assert approved["activation_performed"] is False
    assert approved["browser_execution_allowed"] is False
    assert approved["canonical_writeback_allowed"] is False
    after = json.loads(Path(activation_request["approval_ref"]).read_text(encoding="utf-8"))
    assert after["metadata"] == before["metadata"]
    assert not (siteops_vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    assert not (siteops_vault / "runtime" / "siteops" / "registry" / "skill_cards" / "example.safe_candidate.json").exists()


def test_siteops_candidate_cli_activation_approval_decision_preflight_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )
    activation_request = candidate_promotion_activation_approval_request(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        approval_id=request["approval"]["approval_id"],
        actor="local-user",
        requested_by="local-user",
        write_approval_request=True,
    )
    decide_approval_request(
        siteops_vault,
        activation_request["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    code = cli.main(
        [
            "siteops",
            "candidates",
            "activation-approval-decision-preflight",
            "candidate_run_123",
            "--source-approval-id",
            request["approval"]["approval_id"],
            "--activation-approval-id",
            activation_request["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["activation_approval_decision_preflight_status"] == (
        "activation_approval_decision_preflight_ready_no_mutation"
    )
    assert result["ready_for_activation_consumer_next_pass"] is True
    assert result["approval_decision_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["siteops_skill_card_write_allowed"] is False
    assert result["browser_execution_allowed"] is False


def test_candidate_source_approval_rebind_live_readiness_reports_ready_no_write_for_legacy(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)

    result = candidate_promotion_source_approval_rebind_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
        approval_id=request["approval"]["approval_id"],
    )

    assert result["source_approval_rebind_live_readiness_status"] == (
        "source_approval_rebind_live_readiness_ready_no_write"
    )
    assert result["selected_legacy_approval_id"] == request["approval"]["approval_id"]
    assert result["rebind_spec_status"] == "approval_rebind_spec_required_no_write_authority"
    assert result["replacement_approval_needed"] is True
    assert result["replacement_source_approval_ready_to_write"] is True
    assert result["replacement_approval_request_written"] is False
    assert result["approval_request_artifact_written"] is False
    assert result["approval_consumed"] is False
    assert result["trusted_artifacts_written"] is False
    assert result["activation_performed"] is False
    assert result["browser_execution_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_candidate_source_approval_rebind_live_readiness_blocks_pending_legacy_source(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    approval_path = Path(request["approval"]["approval_ref"])
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload.pop("metadata", None)
    approval_path.write_text(json.dumps(approval_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_source_approval_rebind_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    assert result["selected_legacy_approval_id"] == request["approval"]["approval_id"]
    assert result["source_approval_rebind_live_readiness_status"] == "blocked_legacy_source_approval_not_approved"
    assert result["pending_legacy_unbound_approval_ids"] == [request["approval"]["approval_id"]]
    assert result["replacement_source_approval_ready_to_write"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["approval_consumed"] is False
    assert result["browser_execution_allowed"] is False


def test_candidate_source_approval_rebind_live_readiness_auto_prefers_approved_legacy(
    siteops_vault: Path,
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)
    approved_path = Path(request["approval"]["approval_ref"])
    pending_payload = json.loads(approved_path.read_text(encoding="utf-8"))
    pending_payload["approval_id"] = "approval_zzzz_pending_legacy_candidate_run_123_browser_skill_candidate_promote"
    pending_payload["run_id"] = "siteops_candidate_zzzz_pending_legacy_candidate_run_123"
    pending_payload["status"] = "pending"
    pending_payload.pop("decided_by", None)
    pending_payload.pop("decided_at", None)
    pending_path = approved_path.with_name(f"{pending_payload['approval_id']}.json")
    pending_path.write_text(json.dumps(pending_payload, indent=2) + "\n", encoding="utf-8")

    result = candidate_promotion_source_approval_rebind_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    assert result["selected_legacy_approval_id"] == request["approval"]["approval_id"]
    assert result["source_approval_status"] == "approved"
    assert result["replacement_source_approval_ready_to_write"] is True
    assert result["pending_legacy_unbound_approval_ids"] == [pending_payload["approval_id"]]


def test_candidate_source_approval_rebind_live_readiness_reports_bound_ready(
    siteops_vault: Path,
) -> None:
    _copy_candidate(siteops_vault)
    request = request_scoped_candidate_promotion(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        requested_by="local-user",
        write_approval=True,
    )
    decide_approval_request(
        siteops_vault,
        request["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    result = candidate_promotion_source_approval_rebind_live_readiness(
        "candidate_run_123",
        siteops_vault,
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        actor="local-user",
    )

    assert result["source_approval_rebind_live_readiness_status"] == (
        "source_approval_rebind_not_required_bound_source_ready"
    )
    assert result["bound_source_approval_ids"] == [request["approval"]["approval_id"]]
    assert result["replacement_source_approval_ready_to_write"] is False
    assert result["replacement_approval_request_written"] is False
    assert result["approval_consumed"] is False
    assert result["activation_allowed"] is False


def test_siteops_candidate_cli_source_approval_rebind_live_readiness_read_only(
    siteops_vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = _approved_legacy_unbound_candidate_request(siteops_vault)

    code = cli.main(
        [
            "siteops",
            "candidates",
            "source-approval-rebind-live-readiness",
            "candidate_run_123",
            "--approval-id",
            request["approval"]["approval_id"],
            "--tenant",
            "local",
            "--workspace",
            "default",
            "--user",
            "local-user",
            "--actor",
            "local-user",
            "--vault-root",
            str(siteops_vault),
            "--json",
        ]
    )
    result = _payload(capsys.readouterr().out)

    assert code == 0
    assert result["source_approval_rebind_live_readiness_status"] == (
        "source_approval_rebind_live_readiness_ready_no_write"
    )
    assert result["replacement_source_approval_ready_to_write"] is True
    assert result["replacement_approval_request_written"] is False
    assert result["approval_consumed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["activation_allowed"] is False
    assert result["browser_execution_allowed"] is False
