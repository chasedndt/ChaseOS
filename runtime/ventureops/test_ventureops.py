from __future__ import annotations

import contextlib
import io
import json
from datetime import date
from pathlib import Path

from runtime.cli.main import main as cli_main
from runtime.ventureops.instance_profile import build_instance_profile
from runtime.ventureops.proof_cards import build_proof_card
from runtime.ventureops.registry import load_use_case_registry, workflow_by_id
from runtime.ventureops.recommendations import build_recommendations
from runtime.ventureops.real_evidence_closeout_readiness import (
    build_real_evidence_closeout_readiness,
)
from runtime.ventureops.feature_family_completion_audit import (
    build_feature_family_completion_audit,
)
from runtime.ventureops.autonomous_implementation_completion import (
    build_autonomous_implementation_completion,
)
from runtime.ventureops.final_external_execution_runbook import (
    build_final_external_execution_runbook,
)
from runtime.ventureops.evidence_discovery_preflight import (
    build_evidence_discovery_preflight,
)
from runtime.ventureops.scope_evidence_packet_builder import (
    build_scope_evidence_packet,
)
from runtime.ventureops.scope_approval_packet_builder import (
    build_scope_approval_packet,
)
from runtime.ventureops.revenue_evidence_packet_builder import (
    build_revenue_evidence_packet,
)
from runtime.ventureops.delivery_proof_packet_builder import (
    build_delivery_proof_packet,
)
from runtime.ventureops.real_client_input_manifest import (
    build_real_client_input_manifest,
)
from runtime.ventureops.validation import (
    LIVE_CLIENT_SCOPE_EXPECTED_SUFFIXES,
    LIVE_CLIENT_SCOPE_PREFIX,
    audit_external_readiness_completion,
    discover_external_completion_artifacts,
    validate_client_safe_delivery_artifact,
    validate_live_delivery_proof_artifact,
    validate_live_client_workflow_proof_artifact,
    validate_live_client_scope_proof_artifact,
    validate_live_revenue_proof_artifact,
    validate_live_revenue_evidence,
    validate_real_client_scope_approval_artifact,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
    validate_proof_card,
    validate_recommendation,
    validate_registry,
    validate_schema_templates,
    validate_workflow_pack,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_registry(root: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    src = source_root / "runtime" / "workflows" / "registry" / "use_case_registry.yaml"
    dst = root / "runtime" / "workflows" / "registry" / "use_case_registry.yaml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _run_cli_json(argv: list[str], *, expected_exit: int = 0) -> dict:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = cli_main(argv)
    payload = json.loads(stdout.getvalue())
    assert exit_code == expected_exit, payload
    if expected_exit == 0:
        assert payload["ok"] is True
    return payload["result"]


def _seed_chaseos_like(root: Path) -> None:
    for folder in ["00_HOME", "01_PROJECTS", "05_TEMPLATES", "06_AGENTS", "07_LOGS", "runtime"]:
        (root / folder).mkdir(parents=True, exist_ok=True)
    _write(root / "README.md", "ChaseOS local-first operating system\n")
    _write(root / "PROJECT_FOUNDATION.md", "AOR Gate runtime agent security audit workflow lab\n")
    _write(root / "ROADMAP.md", "Current P0: content, university, AI engineering, runtime ops\n")
    _write(root / "00_HOME" / "Now.md", "Active domains: creator content, university modules, AI engineering, TradeSync and StrikeZone trading analysis.\n")
    _write(root / "00_HOME" / "Dashboard.md", "Visual product creative studio, job internship search, research to product, content CTA, client service offer.\n")
    _write(root / "06_AGENTS" / "Feature-Register.md", "agent runtime governance audit and workflow packs\n")
    _seed_registry(root)


def test_personal_chaseos_like_fixture_recommends_evidence_backed_optional_crypto(tmp_path: Path) -> None:
    _seed_chaseos_like(tmp_path)

    profile = build_instance_profile(tmp_path)
    result = build_recommendations(tmp_path, profile=profile)
    ids = [item["workflow_id"] for item in result["recommendations"]]

    assert profile["workspace_mode"] == "chaseos_native"
    assert "growth_studio_proof_pack" in ids
    assert "creator_content_to_market_batch" in ids
    assert "job_application_pack" in ids
    assert "research_to_product_intelligence" in ids
    assert "agent_runtime_governance_audit" in ids
    assert "tradesync_strikezone_supply_engine" in ids
    crypto = next(item for item in result["recommendations"] if item["workflow_id"] == "tradesync_strikezone_supply_engine")
    assert crypto["evidence_files"]
    assert any("human approval" in item.lower() for item in crypto["approval_requirements"])
    assert result["crypto_trading_policy"]["live_trading_allowed"] is False


def test_non_crypto_creator_business_does_not_prioritize_trading(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _write(tmp_path / "Dashboard.md", "Local business clients need visual design, creative mockups, content batches, ecommerce listings, and invoices.\n")
    _write(tmp_path / "Projects" / "Client-Ops.md", "Active client service offer with quote, scope, delivery, invoice, and case study.\n")

    result = build_recommendations(tmp_path)
    ids = [item["workflow_id"] for item in result["recommendations"]]

    assert "creator_content_to_market_batch" in ids
    assert "growth_studio_proof_pack" in ids
    assert "client_fulfillment_pipeline" in ids
    assert "founder_automation_audit" in ids or "ecommerce_reselling_ops" in ids
    assert "tradesync_strikezone_supply_engine" not in ids


def test_student_fixture_recommends_career_and_university(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _write(tmp_path / "Study.md", "University module lectures, labs, revision cards, GitHub portfolio, CV and internship search.\n")
    _write(tmp_path / "Career.md", "Job applications, recruiter messages, cover letter, project proof, resume improvements.\n")

    result = build_recommendations(tmp_path)
    ids = [item["workflow_id"] for item in result["recommendations"]]

    assert "job_application_pack" in ids
    assert "university_portfolio_os" in ids


def test_sparse_workspace_gets_questions_not_hallucinated_workflows(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _write(tmp_path / "note.md", "hello\n")

    result = build_recommendations(tmp_path)

    assert result["status"] == "insufficient_evidence"
    assert result["recommendations"] == []
    assert len(result["discovery_questions"]) >= 3


def test_registry_and_schema_templates_validate_current_repo() -> None:
    root = Path(__file__).resolve().parents[2]

    registry = validate_registry(root)
    schemas = validate_schema_templates(root)
    pack_paths = sorted((root / "runtime" / "workflows" / "registry" / "packs").glob("*.yaml"))

    assert registry["ok"], registry["errors"]
    assert registry["workflow_count"] >= 15
    assert schemas["ok"], schemas["errors"]
    assert pack_paths
    import yaml  # type: ignore

    for path in pack_paths:
        pack = yaml.safe_load(path.read_text(encoding="utf-8"))
        validation = validate_workflow_pack(pack)
        assert validation["ok"], (path.name, validation["errors"])


def test_real_client_scope_evidence_schema_template_exists_and_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "runtime" / "workflows" / "registry" / "templates" / "real_client_scope_evidence_schema.yaml"
    template_path = root / "05_TEMPLATES" / "Real-Client-Scope-Evidence-Template.md"

    schemas = validate_schema_templates(root)
    schema = schema_path.read_text(encoding="utf-8")
    template = template_path.read_text(encoding="utf-8")

    assert schemas["ok"], schemas["errors"]
    assert "client_approved_scope_id" in schema
    assert "approval_artifact_path" in schema
    assert "approved_read_paths" in schema
    assert "No live client data should be pasted into this template" in template
    assert "approval_artifact_path" in template
    assert "approved_read_paths" in template


def test_live_revenue_evidence_schema_template_exists_and_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "runtime" / "workflows" / "registry" / "templates" / "live_revenue_evidence_schema.yaml"
    template_path = root / "05_TEMPLATES" / "Live-Revenue-Evidence-Template.md"

    schemas = validate_schema_templates(root)
    schema = schema_path.read_text(encoding="utf-8")
    template = template_path.read_text(encoding="utf-8")

    assert schemas["ok"], schemas["errors"]
    assert "revenue_proof_id" in schema
    assert "receipt_artifact_path" in schema
    assert "No raw payment credentials or customer financial data" in template
    assert "revenue_recognition_boundary" in template


def test_validate_real_client_scope_evidence_accepts_safe_approved_scope() -> None:
    evidence = {
        "type": "ventureops-real-client-scope-evidence",
        "client_approved_scope_id": "scope-client-alpha-001",
        "client_label": "Client Alpha",
        "approval_id": "operator-real-client-scope-approval-001",
        "approval_status": "approved",
        "approval_artifact_path": "client_scopes/client-alpha/scope-approval.json",
        "approved_read_paths": [
            "client_scopes/client-alpha/Agent-Control-Plane.md",
            "client_scopes/client-alpha/Permission-Matrix.md",
        ],
        "redaction_policy": "client_safe_summary_only",
        "delivery_boundary": "no_external_delivery",
    }

    validation = validate_real_client_scope_evidence(evidence)

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["approved_read_path_count"] == 2
    assert validation["safe_read_paths"] == evidence["approved_read_paths"]


def test_validate_real_client_scope_evidence_rejects_missing_approval_artifact_path() -> None:
    evidence = {
        "type": "ventureops-real-client-scope-evidence",
        "client_approved_scope_id": "scope-client-alpha-001",
        "client_label": "Client Alpha",
        "approval_id": "operator-real-client-scope-approval-001",
        "approval_status": "approved",
        "approved_read_paths": ["client_scopes/client-alpha/Agent-Control-Plane.md"],
        "redaction_policy": "client_safe_summary_only",
        "delivery_boundary": "no_external_delivery",
    }

    validation = validate_real_client_scope_evidence(evidence)

    assert validation["ok"] is False
    assert "missing required field: approval_artifact_path" in validation["errors"]


def test_validate_scope_evidence_approval_artifact_accepts_matching_typed_artifact(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")
    approval = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-005",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )
    evidence = {
        "type": "ventureops-real-client-scope-evidence",
        "client_approved_scope_id": "scope-client-alpha-005",
        "client_label": "Client Alpha",
        "approval_id": "operator-approval-client-alpha-005",
        "approval_status": "approved",
        "approval_artifact_path": approval["approval_artifact_path"],
        "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
        "redaction_policy": "client_safe_summary_only",
        "delivery_boundary": "no_external_delivery",
    }

    validation = validate_scope_evidence_approval_artifact(tmp_path, evidence)

    assert validation["ok"] is True
    assert validation["scope_approval_artifact_valid"] is True
    assert validation["approval_artifact_path"] == "03_INPUTS/client-alpha/scope-approval.json"


def test_validate_scope_evidence_approval_artifact_rejects_missing_or_mismatched_artifact(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")
    approval = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-other",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-other",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )
    evidence = {
        "type": "ventureops-real-client-scope-evidence",
        "client_approved_scope_id": "scope-client-alpha-005",
        "client_label": "Client Alpha",
        "approval_id": "operator-approval-client-alpha-005",
        "approval_status": "approved",
        "approval_artifact_path": approval["approval_artifact_path"],
        "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
        "redaction_policy": "client_safe_summary_only",
        "delivery_boundary": "no_external_delivery",
    }

    validation = validate_scope_evidence_approval_artifact(tmp_path, evidence)

    assert validation["ok"] is False
    assert "scope approval artifact approval_id does not match scope evidence approval_id" in validation["errors"]
    assert "scope approval artifact scope id does not match scope evidence scope id" in validation["errors"]


def test_validate_scope_evidence_source_paths_accepts_existing_files(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md"
    _write(source, "redacted client brief\n")

    validation = validate_scope_evidence_source_paths(
        tmp_path,
        ["03_INPUTS/client-alpha/redacted-brief.md"],
    )

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["existing_source_count"] == 1


def test_validate_scope_evidence_source_paths_rejects_missing_or_directory(tmp_path: Path) -> None:
    directory = tmp_path / "03_INPUTS" / "client-alpha" / "folder"
    directory.mkdir(parents=True)

    validation = validate_scope_evidence_source_paths(
        tmp_path,
        [
            "03_INPUTS/client-alpha/missing.md",
            "03_INPUTS/client-alpha/folder",
        ],
    )

    assert validation["ok"] is False
    assert "approved source path missing: 03_INPUTS/client-alpha/missing.md" in validation["errors"]
    assert "approved source path is not a file: 03_INPUTS/client-alpha/folder" in validation["errors"]


def test_validate_real_client_scope_evidence_rejects_template_only_packet() -> None:
    evidence = {
        "type": "ventureops-real-client-scope-evidence",
        "template_only": True,
        "client_approved_scope_id": "scope-client-alpha-001",
        "client_label": "Client Alpha",
        "approval_id": "operator-real-client-scope-approval-001",
        "approval_status": "approved",
        "approved_read_paths": ["client_scopes/client-alpha/Agent-Control-Plane.md"],
        "redaction_policy": "client_safe_summary_only",
        "delivery_boundary": "no_external_delivery",
    }

    validation = validate_real_client_scope_evidence(evidence)

    assert validation["ok"] is False
    assert "template_only scope evidence cannot be used as real client scope proof" in validation["errors"]


def test_validate_real_client_scope_evidence_rejects_secret_like_or_unapproved_scope() -> None:
    unsafe = {
        "type": "ventureops-real-client-scope-evidence",
        "client_approved_scope_id": "scope-client-alpha-unsafe",
        "client_label": "Client Alpha",
        "approval_id": "operator-real-client-scope-approval-unsafe",
        "approval_status": "pending",
        "approved_read_paths": [".env", "../outside.md"],
        "redaction_policy": "raw_dump",
        "delivery_boundary": "external_send_allowed",
    }

    validation = validate_real_client_scope_evidence(unsafe)

    assert validation["ok"] is False
    assert "approval_status must be approved" in validation["errors"]
    assert "approved_read_paths contains unsafe path: .env" in validation["errors"]
    assert "approved_read_paths contains unsafe path: ../outside.md" in validation["errors"]
    assert "redaction_policy must be client_safe_summary_only or stricter" in validation["errors"]
    assert "delivery_boundary must be no_external_delivery for the proof gate" in validation["errors"]


def test_validate_live_revenue_evidence_accepts_safe_received_payment_proof() -> None:
    evidence = {
        "type": "ventureops-live-revenue-evidence",
        "revenue_proof_id": "revenue-proof-client-alpha-001",
        "workflow_id": "agent_runtime_governance_audit",
        "client_label": "Client Alpha",
        "payment_reference_id": "pay_approved_reference_001",
        "payment_status": "received",
        "amount": "250.00",
        "currency": "USD",
        "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
        "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        "crm_reference_id": "crm_client_alpha_001",
        "approval_id": "operator-live-revenue-proof-approval-001",
        "revenue_recognition_boundary": "proof_only_no_accounting_claim",
    }

    validation = validate_live_revenue_evidence(evidence)

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["amount"] == 250.0
    assert validation["receipt_artifact_path"] == "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json"


def test_validate_live_revenue_evidence_rejects_template_only_packet() -> None:
    evidence = {
        "type": "ventureops-live-revenue-evidence",
        "template_only": True,
        "revenue_proof_id": "revenue-proof-client-alpha-001",
        "workflow_id": "agent_runtime_governance_audit",
        "client_label": "Client Alpha",
        "payment_reference_id": "pay_approved_reference_001",
        "payment_status": "received",
        "amount": "250.00",
        "currency": "USD",
        "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
        "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        "crm_reference_id": "crm_client_alpha_001",
        "approval_id": "operator-live-revenue-proof-approval-001",
        "revenue_recognition_boundary": "proof_only_no_accounting_claim",
    }

    validation = validate_live_revenue_evidence(evidence)

    assert validation["ok"] is False
    assert "template_only revenue evidence cannot be used as live revenue proof" in validation["errors"]


def test_validate_live_revenue_evidence_rejects_unpaid_or_secret_like_revenue_proof() -> None:
    unsafe = {
        "type": "ventureops-live-revenue-evidence",
        "revenue_proof_id": "revenue-proof-client-alpha-unsafe",
        "workflow_id": "agent_runtime_governance_audit",
        "client_label": "Client Alpha",
        "payment_reference_id": "pay_pending_reference_001",
        "payment_status": "pending",
        "amount": "0",
        "currency": "US",
        "receipt_artifact_path": ".env",
        "delivery_proof_path": "../outside.json",
        "crm_reference_id": "crm_client_alpha_001",
        "approval_id": "operator-live-revenue-proof-approval-unsafe",
        "revenue_recognition_boundary": "recognized_revenue",
    }

    validation = validate_live_revenue_evidence(unsafe)

    assert validation["ok"] is False
    assert "payment_status must be received or settled" in validation["errors"]
    assert "amount must be greater than zero" in validation["errors"]
    assert "currency must be a 3-letter code" in validation["errors"]
    assert "receipt_artifact_path contains unsafe path: .env" in validation["errors"]
    assert "delivery_proof_path contains unsafe path: ../outside.json" in validation["errors"]
    assert "revenue_recognition_boundary must be proof_only_no_accounting_claim" in validation["errors"]


def _valid_live_client_scope_proof_artifact() -> dict:
    return {
        "type": "ventureops-live-client-scope-proof-gate",
        "workflow_id": "agent_runtime_governance_audit",
        "run_id": "live-client-scope-proof-gate",
        "date": "2026-05-11",
        "status": "real_client_scope_evidence_validated_no_live_client_run",
        "proof_path": "07_LOGS/Workflow-Proofs/client-alpha-proof.md",
        "live_client_scope_contract_path": "07_LOGS/Workflow-Proofs/client-alpha-contract.json",
        "real_client_scope_evidence_path": "runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json",
        "client_approved_scope_id": "scope-client-alpha-001",
        "client_label": "Client Alpha",
        "approval_id": "operator-approval-client-alpha-scope",
        "approval_status": "approved",
        "redaction_policy": "client_safe_summary_only",
        "delivery_boundary": "no_external_delivery",
        "approved_read_path_count": 1,
        "approved_read_paths_validated": True,
        "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
        "real_client_scope_present": True,
        "real_client_scope_approved": True,
        "live_client_scope_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "forbidden_actions": [
            "broad_filesystem_read",
            "external_send",
            "provider_model_execution",
            "browser_action",
            "payment_api_call",
            "crm_record_mutation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-live-client-scope-proof",
    }


def _valid_live_client_workflow_proof_artifact() -> dict:
    return {
        "type": "ventureops-live-client-workflow-proof",
        "status": "live_client_workflow_proof_written",
        "workflow_id": "agent_runtime_governance_audit",
        "run_id": "live-client-workflow-proof-test",
        "date": "2026-05-11",
        "scope_packet_path": "03_INPUTS/client-alpha/scope-evidence.json",
        "client_approved_scope_id": "scope-client-alpha-002",
        "client_label": "Client Alpha",
        "approval_id": "operator-approval-client-alpha-scope-002",
        "approval_status": "approved",
        "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
        "approved_read_path_count": 1,
        "source_digest_count": 1,
        "source_digests": [
            {
                "path": "03_INPUTS/client-alpha/redacted-brief.md",
                "sha256": "a" * 64,
                "byte_count": 128,
            }
        ],
        "scope_proof_gate_path": "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_live-client-scope-proof-gate.json",
        "client_report_path": "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_client-report.md",
        "scorecard_path": "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_scorecard.json",
        "live_client_workflow_proof_performed": True,
        "scoped_client_data_ingested": True,
        "broad_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
    }


def test_validate_live_client_scope_proof_artifact_accepts_guarded_gate() -> None:
    validation = validate_live_client_scope_proof_artifact(_valid_live_client_scope_proof_artifact())

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["client_approved_scope_id"] == "scope-client-alpha-001"
    assert validation["approved_read_path_count"] == 1


def test_validate_live_client_scope_proof_artifact_rejects_wrong_shape_or_side_effects() -> None:
    invalid = {
        **_valid_live_client_scope_proof_artifact(),
        "type": "not-a-live-client-proof",
        "approval_status": "pending",
        "live_client_data_ingested": True,
        "live_external_delivery_performed": True,
        "approved_read_paths": [".env"],
    }

    validation = validate_live_client_scope_proof_artifact(invalid)

    assert validation["ok"] is False
    assert "type must be ventureops-live-client-scope-proof-gate" in validation["errors"]
    assert "approval_status must be approved" in validation["errors"]
    assert "live_client_data_ingested must remain false for proof-only revenue prerequisite" in validation["errors"]
    assert "live_external_delivery_performed must remain false for proof-only revenue prerequisite" in validation["errors"]
    assert "approved_read_paths contains unsafe path: .env" in validation["errors"]


def test_validate_live_client_workflow_proof_artifact_accepts_guarded_local_proof() -> None:
    validation = validate_live_client_workflow_proof_artifact(_valid_live_client_workflow_proof_artifact())

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["client_approved_scope_id"] == "scope-client-alpha-002"
    assert validation["approved_read_path_count"] == 1


def test_validate_live_client_workflow_proof_artifact_rejects_side_effects_or_no_ingestion() -> None:
    invalid = {
        **_valid_live_client_workflow_proof_artifact(),
        "scoped_client_data_ingested": False,
        "external_send_performed": True,
        "payment_mutation_performed": True,
    }

    validation = validate_live_client_workflow_proof_artifact(invalid)

    assert validation["ok"] is False
    assert "scoped_client_data_ingested must be true" in validation["errors"]
    assert "external_send_performed must be false" in validation["errors"]
    assert "payment_mutation_performed must be false" in validation["errors"]


def test_validate_live_client_workflow_proof_artifact_rejects_missing_or_invalid_source_digests() -> None:
    missing_digests = {
        **_valid_live_client_workflow_proof_artifact(),
        "source_digests": [],
    }

    missing_validation = validate_live_client_workflow_proof_artifact(missing_digests)

    assert missing_validation["ok"] is False
    assert "source_digests must be a non-empty list" in missing_validation["errors"]
    assert "source_digests must cover approved_read_paths" in missing_validation["errors"]

    invalid_digest = {
        **_valid_live_client_workflow_proof_artifact(),
        "source_digests": [
            {
                "path": ".env",
                "sha256": "not-a-sha",
                "byte_count": 0,
            }
        ],
    }

    invalid_validation = validate_live_client_workflow_proof_artifact(invalid_digest)

    assert invalid_validation["ok"] is False
    assert "source_digests contains unsafe path: .env" in invalid_validation["errors"]
    assert "source_digests sha256 must be 64 lowercase hex for path: .env" in invalid_validation["errors"]
    assert "source_digests byte_count must be positive for path: .env" in invalid_validation["errors"]


def _valid_live_revenue_proof_artifact() -> dict:
    return {
        "type": "ventureops-live-revenue-proof",
        "status": "proof_only_recorded_no_accounting_claim",
        "date": "2026-05-11",
        "revenue_proof_id": "revenue-client-alpha-007",
        "revenue_packet_path": "runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json",
        "workflow_id": "agent_runtime_governance_audit",
        "client_label": "Client Alpha",
        "payment_reference_id": "pay_ref_redacted_alpha_007",
        "payment_status": "received",
        "amount": 250.0,
        "currency": "USD",
        "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
        "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        "live_client_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        "crm_reference_id": "crm_ref_redacted_alpha_007",
        "approval_id": "operator-approval-client-alpha-revenue-007",
        "revenue_recognition_boundary": "proof_only_no_accounting_claim",
        "receipt_artifact_exists": True,
        "delivery_proof_exists": True,
        "delivery_proof_artifact_valid": True,
        "live_client_proof_exists": True,
        "live_client_proof_artifact_valid": True,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "invoice_sent": False,
        "external_send_performed": False,
        "revenue_claim_made": False,
    }


def _valid_live_delivery_proof_artifact() -> dict:
    return {
        "type": "ventureops-live-delivery-proof",
        "status": "operator_attested_delivery_recorded",
        "delivery_proof_id": "delivery-client-alpha-007",
        "workflow_id": "agent_runtime_governance_audit",
        "client_label": "Client Alpha",
        "delivery_reference_id": "delivery_ref_redacted_alpha_007",
        "delivery_status": "delivered",
        "client_safe_delivery_artifact_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json",
        "live_client_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        "delivery_boundary": "operator_attested_delivery_no_chaseos_external_send",
        "operator_attested_delivery_performed": True,
        "external_send_performed_by_chaseos": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
    }


def _valid_client_safe_delivery_artifact() -> dict:
    return {
        "type": "ventureops-client-safe-delivery-artifact",
        "workflow_id": "agent_runtime_governance_audit",
        "client_label": "Client Alpha",
        "delivery_reference_id": "delivery_ref_redacted_alpha_007",
        "redacted": True,
        "client_safe": True,
        "delivery_summary": "Redacted client-safe delivery summary.",
        "source_live_client_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        "external_send_performed_by_chaseos": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
    }


def _write_valid_revenue_completion_prerequisites(root: Path) -> None:
    _write(root / "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json", json.dumps({"redacted": True}))
    _write(
        root / "07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json",
        json.dumps(_valid_client_safe_delivery_artifact(), indent=2),
    )
    _write(
        root / "runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json",
        json.dumps(
            {
                "type": "ventureops-live-revenue-evidence",
                "revenue_proof_id": "revenue-client-alpha-007",
                "workflow_id": "agent_runtime_governance_audit",
                "client_label": "Client Alpha",
                "payment_reference_id": "pay_ref_redacted_alpha_007",
                "payment_status": "received",
                "amount": "250.00",
                "currency": "USD",
                "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
                "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
                "crm_reference_id": "crm_ref_redacted_alpha_007",
                "approval_id": "operator-approval-client-alpha-revenue-007",
                "revenue_recognition_boundary": "proof_only_no_accounting_claim",
            },
            indent=2,
        ),
    )
    _write(
        root / "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        json.dumps(_valid_live_delivery_proof_artifact(), indent=2),
    )


def _write_valid_live_client_completion_prerequisites(root: Path) -> None:
    _write(root / "03_INPUTS/client-alpha/redacted-brief.md", "redacted client fixture\n")
    _write(
        root / "03_INPUTS/client-alpha/scope-approval.json",
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-approval-client-alpha-scope-002",
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-002",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
                "operator_attested_scope_approved": True,
                "external_send_authorized": False,
                "payment_mutation_authorized": False,
                "crm_mutation_authorized": False,
                "provider_calls_authorized": False,
                "browser_actions_authorized": False,
                "revenue_claim_authorized": False,
            },
            indent=2,
        ),
    )
    _write(
        root / "03_INPUTS/client-alpha/scope-evidence.json",
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-002",
                "client_label": "Client Alpha",
                "approval_id": "operator-approval-client-alpha-scope-002",
                "approval_status": "approved",
                "approval_artifact_path": "03_INPUTS/client-alpha/scope-approval.json",
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            },
            indent=2,
        ),
    )
    scope_gate = {
        **_valid_live_client_scope_proof_artifact(),
        "client_approved_scope_id": "scope-client-alpha-002",
        "approval_id": "operator-approval-client-alpha-scope-002",
    }
    _write(
        root
        / "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_live-client-scope-proof-gate.json",
        json.dumps(scope_gate, indent=2),
    )
    _write(
        root
        / "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_client-report.md",
        "Client-safe live workflow report.\n",
    )
    scorecard = {
        "workflow_id": "agent_runtime_governance_audit",
        "run_id": "live-client-workflow-proof-test",
        "runtime": "Codex",
        "operator": "Chase",
        "timestamp": "2026-05-11T00:00:00Z",
        "status": "client_ready",
        "metrics": {"scoped_client_data_ingested": True},
        "evidence_links": [
            "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_client-report.md"
        ],
        "unresolved_risks": [],
        "recommended_next_action": "author delivery proof packet after operator-attested delivery",
    }
    _write(
        root
        / "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_scorecard.json",
        json.dumps(scorecard, indent=2),
    )


def test_validate_live_delivery_proof_artifact_accepts_redacted_operator_delivery() -> None:
    validation = validate_live_delivery_proof_artifact(_valid_live_delivery_proof_artifact())

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["delivery_proof_id"] == "delivery-client-alpha-007"
    assert validation["delivery_status"] == "delivered"


def test_validate_client_safe_delivery_artifact_accepts_redacted_delivery_summary() -> None:
    validation = validate_client_safe_delivery_artifact(_valid_client_safe_delivery_artifact())

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["client_label"] == "Client Alpha"
    assert validation["delivery_reference_id"] == "delivery_ref_redacted_alpha_007"
    assert (
        validation["source_live_client_proof_path"]
        == "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    )


def test_validate_client_safe_delivery_artifact_rejects_unredacted_or_side_effects() -> None:
    invalid = {
        **_valid_client_safe_delivery_artifact(),
        "redacted": False,
        "client_safe": False,
        "delivery_summary": "",
        "source_live_client_proof_path": ".env",
        "external_send_performed_by_chaseos": True,
        "crm_mutation_performed": True,
        "payment_mutation_performed": True,
        "invoice_sent": True,
        "provider_calls": 1,
        "browser_actions": 1,
        "revenue_claim_made": True,
    }

    validation = validate_client_safe_delivery_artifact(invalid)

    assert validation["ok"] is False
    assert "redacted must be true" in validation["errors"]
    assert "client_safe must be true" in validation["errors"]
    assert "delivery_summary must be non-empty" in validation["errors"]
    assert "source_live_client_proof_path contains unsafe path: .env" in validation["errors"]
    assert "external_send_performed_by_chaseos must be false" in validation["errors"]
    assert "crm_mutation_performed must be false" in validation["errors"]
    assert "payment_mutation_performed must be false" in validation["errors"]
    assert "invoice_sent must be false" in validation["errors"]
    assert "provider_calls must be 0" in validation["errors"]
    assert "browser_actions must be 0" in validation["errors"]
    assert "revenue_claim_made must be false" in validation["errors"]


def test_validate_live_delivery_proof_artifact_rejects_unbounded_delivery_or_mutation() -> None:
    invalid = {
        **_valid_live_delivery_proof_artifact(),
        "delivery_status": "draft",
        "client_safe_delivery_artifact_path": ".env",
        "operator_attested_delivery_performed": False,
        "external_send_performed_by_chaseos": True,
        "crm_mutation_performed": True,
        "payment_mutation_performed": True,
        "invoice_sent": True,
        "revenue_claim_made": True,
    }

    validation = validate_live_delivery_proof_artifact(invalid)

    assert validation["ok"] is False
    assert "delivery_status must be delivered or accepted" in validation["errors"]
    assert "client_safe_delivery_artifact_path contains unsafe path: .env" in validation["errors"]
    assert "operator_attested_delivery_performed must be true" in validation["errors"]
    assert "external_send_performed_by_chaseos must be false" in validation["errors"]
    assert "crm_mutation_performed must be false" in validation["errors"]
    assert "payment_mutation_performed must be false" in validation["errors"]
    assert "invoice_sent must be false" in validation["errors"]
    assert "revenue_claim_made must be false" in validation["errors"]


def test_validate_live_revenue_proof_artifact_accepts_proof_only_record() -> None:
    validation = validate_live_revenue_proof_artifact(_valid_live_revenue_proof_artifact())

    assert validation["ok"] is True
    assert validation["errors"] == []
    assert validation["revenue_proof_id"] == "revenue-client-alpha-007"
    assert validation["amount"] == 250.0
    assert validation["currency"] == "USD"


def test_validate_live_revenue_proof_artifact_rejects_mutation_or_claims() -> None:
    invalid = {
        **_valid_live_revenue_proof_artifact(),
        "delivery_proof_artifact_valid": False,
        "payment_mutation_performed": True,
        "crm_mutation_performed": True,
        "invoice_sent": True,
        "external_send_performed": True,
        "revenue_claim_made": True,
    }

    validation = validate_live_revenue_proof_artifact(invalid)

    assert validation["ok"] is False
    assert "delivery_proof_artifact_valid must be true" in validation["errors"]
    assert "payment_mutation_performed must be false" in validation["errors"]
    assert "crm_mutation_performed must be false" in validation["errors"]
    assert "invoice_sent must be false" in validation["errors"]
    assert "external_send_performed must be false" in validation["errors"]
    assert "revenue_claim_made must be false" in validation["errors"]


def test_external_completion_artifact_discovery_finds_actual_live_proof_files() -> None:
    root = Path(__file__).resolve().parents[2]

    discovery = discover_external_completion_artifacts(root)

    assert discovery["live_client_workflow_proof_present"] is True
    assert discovery["live_revenue_workflow_proof_present"] is False
    assert discovery["valid_live_client_workflow_proof_artifacts"]
    assert discovery["valid_live_revenue_proof_artifacts"] == []


def test_external_completion_artifact_discovery_accepts_valid_live_client_and_revenue_proofs(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    revenue_proof = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)
    _write_valid_revenue_completion_prerequisites(tmp_path)
    _write(revenue_proof, json.dumps(_valid_live_revenue_proof_artifact(), indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is True
    assert discovery["live_revenue_workflow_proof_present"] is True
    assert discovery["valid_live_client_workflow_proof_artifacts"] == [
        "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    ]
    assert discovery["valid_live_revenue_proof_artifacts"] == [
        "07_LOGS/Revenue-Proofs/client-alpha-live-revenue-proof.json"
    ]


def test_external_completion_artifact_discovery_revalidates_revenue_referenced_files(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    revenue_proof = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)
    _write(revenue_proof, json.dumps(_valid_live_revenue_proof_artifact(), indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is True
    assert discovery["live_revenue_workflow_proof_present"] is False
    assert discovery["valid_live_revenue_proof_artifacts"] == []
    invalid = discovery["invalid_live_revenue_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Revenue-Proofs/client-alpha-live-revenue-proof.json"
    assert "receipt artifact missing: 07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json" in invalid[0]["errors"]
    assert "delivery proof artifact missing: 07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json" in invalid[0]["errors"]


def test_external_completion_artifact_discovery_rejects_inconsistent_revenue_references(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    revenue_proof = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json"
    inconsistent_revenue = {**_valid_live_revenue_proof_artifact(), "client_label": "Client Beta"}
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)
    _write_valid_revenue_completion_prerequisites(tmp_path)
    _write(revenue_proof, json.dumps(inconsistent_revenue, indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is True
    assert discovery["live_revenue_workflow_proof_present"] is False
    assert discovery["valid_live_revenue_proof_artifacts"] == []
    invalid = discovery["invalid_live_revenue_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Revenue-Proofs/client-alpha-live-revenue-proof.json"
    assert "delivery proof client_label does not match revenue proof" in invalid[0]["errors"]
    assert "live-client proof client_label does not match revenue proof" in invalid[0]["errors"]


def test_external_completion_artifact_discovery_rejects_invalid_receipt_artifact(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    revenue_proof = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json"
    receipt = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-receipt-redacted.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)
    _write_valid_revenue_completion_prerequisites(tmp_path)
    _write(receipt, json.dumps({"redacted": False}, indent=2))
    _write(revenue_proof, json.dumps(_valid_live_revenue_proof_artifact(), indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is True
    assert discovery["live_revenue_workflow_proof_present"] is False
    assert discovery["valid_live_revenue_proof_artifacts"] == []
    invalid = discovery["invalid_live_revenue_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Revenue-Proofs/client-alpha-live-revenue-proof.json"
    assert "receipt artifact invalid: redacted must be true" in invalid[0]["errors"]


def test_external_completion_artifact_discovery_rejects_invalid_client_safe_delivery_artifact(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    revenue_proof = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json"
    client_safe_delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)
    _write_valid_revenue_completion_prerequisites(tmp_path)
    _write(client_safe_delivery, json.dumps({"redacted": False}, indent=2))
    _write(revenue_proof, json.dumps(_valid_live_revenue_proof_artifact(), indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is True
    assert discovery["live_revenue_workflow_proof_present"] is False
    assert discovery["valid_live_revenue_proof_artifacts"] == []
    invalid = discovery["invalid_live_revenue_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Revenue-Proofs/client-alpha-live-revenue-proof.json"
    assert "client-safe delivery artifact invalid: redacted must be true" in invalid[0]["errors"]


def test_external_completion_artifact_discovery_revalidates_live_revenue_packet(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    revenue_proof = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)
    _write_valid_revenue_completion_prerequisites(tmp_path)
    (tmp_path / "runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json").unlink()
    _write(revenue_proof, json.dumps(_valid_live_revenue_proof_artifact(), indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is True
    assert discovery["live_revenue_workflow_proof_present"] is False
    assert discovery["valid_live_revenue_proof_artifacts"] == []
    invalid = discovery["invalid_live_revenue_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Revenue-Proofs/client-alpha-live-revenue-proof.json"
    assert (
        "revenue packet artifact missing: runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json"
        in invalid[0]["errors"]
    )


def test_external_completion_artifact_discovery_revalidates_live_client_referenced_files(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is False
    assert discovery["valid_live_client_workflow_proof_artifacts"] == []
    invalid = discovery["invalid_live_client_workflow_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    assert (
        "scope proof gate artifact missing: "
        "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_live-client-scope-proof-gate.json"
        in invalid[0]["errors"]
    )
    assert (
        "client report artifact missing: "
        "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_client-report.md"
        in invalid[0]["errors"]
    )
    assert (
        "scorecard artifact missing: "
        "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_scorecard.json"
        in invalid[0]["errors"]
    )


def test_external_completion_artifact_discovery_revalidates_live_client_scope_packet(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)
    (tmp_path / "03_INPUTS/client-alpha/scope-evidence.json").unlink()

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is False
    assert discovery["valid_live_client_workflow_proof_artifacts"] == []
    invalid = discovery["invalid_live_client_workflow_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    assert "scope packet artifact missing: 03_INPUTS/client-alpha/scope-evidence.json" in invalid[0]["errors"]


def test_external_completion_artifact_discovery_rejects_inconsistent_live_client_references(
    tmp_path: Path,
) -> None:
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(tmp_path)

    scope_gate_path = (
        tmp_path
        / "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_live-client-scope-proof-gate.json"
    )
    inconsistent_scope_gate = {
        **_valid_live_client_scope_proof_artifact(),
        "client_approved_scope_id": "scope-client-beta-999",
        "approval_id": "operator-approval-client-beta-scope-999",
        "approved_read_paths": ["03_INPUTS/client-beta/redacted-brief.md"],
    }
    _write(scope_gate_path, json.dumps(inconsistent_scope_gate, indent=2))

    scorecard_path = (
        tmp_path
        / "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof-test_scorecard.json"
    )
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    scorecard["run_id"] = "unrelated-run"
    _write(scorecard_path, json.dumps(scorecard, indent=2))

    discovery = discover_external_completion_artifacts(tmp_path)

    assert discovery["live_client_workflow_proof_present"] is False
    assert discovery["valid_live_client_workflow_proof_artifacts"] == []
    invalid = discovery["invalid_live_client_workflow_proof_artifacts"]
    assert invalid[0]["path"] == "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    assert "scope proof gate client_approved_scope_id does not match live-client workflow proof" in invalid[0]["errors"]
    assert "scope proof gate approval_id does not match live-client workflow proof" in invalid[0]["errors"]
    assert "scope proof gate approved_read_paths do not match live-client workflow proof" in invalid[0]["errors"]
    assert "scorecard run_id does not match live-client workflow proof" in invalid[0]["errors"]


def test_registry_truth_marks_only_verified_agent_runtime_audit_as_client_safe() -> None:
    root = Path(__file__).resolve().parents[2]
    records = workflow_by_id(load_use_case_registry(root))

    audit = records["agent_runtime_governance_audit"]
    job = records["job_application_pack"]

    assert audit["status"] == "LIVE CLIENT SCOPE CONTRACT VERIFIED"
    assert audit["implementation_status"] == "AOR MANIFEST + HANDLER + EXACT VENTUREOPS AI RUNTIME SECURITY AUDIT ALIAS + PROOF + REPORT + SCORECARD + OFFER + CLIENT SCOPE + DELIVERY CONTRACT + DELIVERY PREVIEW + APPROVAL REQUEST + APPROVAL CONSUMPTION + EXACT-ONCE DELIVERY GATE + EXTERNAL-SEND DRY-RUN + APPROVED EXTERNAL-SEND PROOF + CRM DRAFT + PAYMENT INVOICE DRAFT + WORKFLOW EXCHANGE PUBLICATION PREVIEW + LIVE CLIENT SCOPE CONTRACT VERIFIED"
    assert audit["workflow_aliases"] == ["ventureops_ai_runtime_security_audit"]
    assert audit["exact_alias_manifest"] == "runtime/workflows/registry/ventureops_ai_runtime_security_audit.yaml"
    assert audit["exact_alias_role_card"] == "06_AGENTS/role-cards/security_reviewer.yaml"
    assert audit["proof_artifact"].endswith("live-client-scope-contract.md")
    assert audit["client_report_artifact"].endswith("live-client-scope-contract_client-report.md")
    assert audit["scorecard_artifact"].endswith("live-client-scope-contract_scorecard.json")
    assert audit["offer_packet_artifact"].endswith("live-client-scope-contract_offer-packet.md")
    assert audit["client_scope_artifact"].endswith("live-client-scope-contract_client-scope.md")
    assert audit["delivery_approval_contract_artifact"].endswith("live-client-scope-contract_delivery-approval-contract.md")
    assert audit["delivery_packet_preview_artifact"].endswith("live-client-scope-contract_delivery-packet-preview.md")
    assert audit["approval_request_artifact"].endswith("live-client-scope-contract_approval-request.json")
    assert audit["approval_consumption_proof_artifact"].endswith("live-client-scope-contract_approval-consumption.json")
    assert audit["exact_once_delivery_gate_artifact"].endswith("live-client-scope-contract_exact-once-delivery-gate.json")
    assert audit["delivery_gate_marker_artifact"].endswith("live-client-scope-contract_delivery-gate-marker.json")
    assert audit["external_send_dry_run_artifact"].endswith("live-client-scope-contract_external-send-dry-run.json")
    assert audit["approved_external_send_proof_artifact"].endswith("live-client-scope-contract_approved-external-send.json")
    assert audit["crm_draft_artifact"].endswith("live-client-scope-contract_crm-draft.json")
    assert audit["payment_invoice_draft_artifact"].endswith("live-client-scope-contract_payment-invoice-draft.json")
    assert audit["workflow_exchange_publication_preview_artifact"].endswith("live-client-scope-contract_workflow-exchange-publication-preview.json")
    assert audit["live_client_scope_contract_artifact"].endswith("live-client-scope-contract_live-client-scope-contract.json")
    assert job["status"] == "DRAFT PACK CANDIDATE"
    assert job["implementation_status"] == "PARTIAL RUNTIME RECOMMENDATION ONLY"
    assert "client_report_artifact" not in job
    assert "scorecard_artifact" not in job


def test_recommendations_validate_and_keep_evidence(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _write(tmp_path / "Dashboard.md", "Runtime security audit for agents, permission matrix, Gate, MCP and proof artifacts.\n")

    result = build_recommendations(tmp_path)

    assert result["recommendations"]
    for recommendation in result["recommendations"]:
        validation = validate_recommendation(recommendation)
        assert validation["ok"], validation["errors"]


def test_unsafe_workflow_pack_flags_approval_and_live_trading_boundary() -> None:
    pack = {
        "workflow_id": "unsafe_trading_pack",
        "name": "Unsafe Trading Pack",
        "version": "0.1",
        "owner": "operator",
        "customer": "internal",
        "problem": "trade execution",
        "offer": "signals",
        "task_type": "analysis",
        "trigger": "manual",
        "required_inputs": [],
        "required_context": [],
        "role_cards": [],
        "allowed_tools": [],
        "forbidden_tools": [],
        "runtime_split": {},
        "approval_mode": "none",
        "writeback_targets": [],
        "proof_artifact": "07_LOGS/Workflow-Proofs/test.md",
        "audit_target": "07_LOGS/Agent-Activity/test.md",
        "failure_behavior": "abort",
        "monetization_model": "subscription",
        "success_metric": "none",
        "scorecard": {},
        "status": "draft",
        "implementation_status": "DOCS-ONLY",
        "risk_notes": ["live trading execution and external send"],
    }

    validation = validate_workflow_pack(pack)

    assert validation["ok"] is False
    assert any("approval" in error for error in validation["errors"])
    assert any("live_trading_execution" in error for error in validation["errors"])


def test_proof_card_builder_validates_required_fields() -> None:
    card = build_proof_card(
        workflow_id="agent_runtime_governance_audit",
        run_id="run-test",
        before_state="unreviewed runtime permissions",
        after_state="draft audit produced",
        input_sources=["06_AGENTS/Permission-Matrix.md"],
        runtimes_used=["Codex"],
        actions_taken=["read declared files", "built draft audit"],
        outputs_generated=["audit draft"],
        files_written=["07_LOGS/Workflow-Proofs/run-test.md"],
        approvals_used=["operator-draft-approval"],
    )

    assert validate_proof_card(card)["ok"] is True
    assert card["redaction_level"] == "internal_private"


def test_goal_doc_records_foundation_completion_and_tdd_mandate() -> None:
    root = Path(__file__).resolve().parents[2]
    goal = (root / "docs" / "goal.md").read_text(encoding="utf-8")

    assert "FOUNDATION PASS COMPLETE" in goal
    assert "TDD REQUIRED FOR FUTURE VENTUREOPS IMPLEMENTATION" in goal
    assert "red -> green -> refactor -> truth-sync" in goal


def test_external_readiness_passover_lists_remaining_external_features() -> None:
    root = Path(__file__).resolve().parents[2]
    passover_path = root / "06_AGENTS" / "VentureOps-External-Readiness-Passover.md"
    passover = passover_path.read_text(encoding="utf-8")

    assert "PARTIAL / LIVE CLIENT WORKFLOW PROOF VERIFIED / LIVE REVENUE EVIDENCE REQUIRED / NO LIVE EXTERNAL DELIVERY" in passover
    for required in [
        "approval request artifact",
        "approval consumption",
        "exact-once delivery gating",
        "external send connector",
        "CRM integration",
        "payment integration",
        "marketplace publication",
        "live client workflow",
        "live revenue workflow",
    ]:
        assert required in passover
    assert "Do not mark VentureOps COMPLETE" in passover
    assert "No live external delivery has been performed" in passover


def test_external_readiness_handover_alias_points_to_passover() -> None:
    root = Path(__file__).resolve().parents[2]
    handover_path = root / "06_AGENTS" / "VentureOps-External-Readiness-Handover.md"
    handover = handover_path.read_text(encoding="utf-8")

    assert "VentureOps External Readiness Handover" in handover
    assert "VentureOps-External-Readiness-Passover.md" in handover
    assert "approval request artifact" in handover
    assert "PARTIAL / LIVE CLIENT WORKFLOW PROOF VERIFIED / LIVE REVENUE EVIDENCE REQUIRED / NO LIVE EXTERNAL DELIVERY" in handover


def test_external_readiness_requested_typo_handover_alias_is_validated() -> None:
    root = Path(__file__).resolve().parents[2]
    requested_path = root / "06_AGENTS" / "VentureOps-externaal-Readiness-Handover.md"
    requested_handover = requested_path.read_text(encoding="utf-8")

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    assert "VentureOps-External-Readiness-Handover.md" in requested_handover
    assert "VentureOps-External-Readiness-Passover.md" in requested_handover
    assert "Next required real-use pass: `ventureops-live-revenue-proof`" in requested_handover
    assert "live-revenue-proof-readiness --revenue-packet PATH --live-client-proof-path PATH --json" in requested_handover
    assert audit["requested_handover_path"] == "06_AGENTS/VentureOps-externaal-Readiness-Handover.md"
    assert audit["requested_handover_alias_valid"] is True
    assert audit["requested_handover_next_pass_valid"] is True
    assert audit["requested_handover_scope_output_route_valid"] is True
    assert checklist["review requested VentureOps-externaal handover alias"]["status"] == "verified"


def test_external_readiness_completion_audit_validates_passover_handover_and_blocks_complete() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)

    assert audit["ok"] is True
    assert audit["complete"] is False
    assert audit["completion_decision"] == "not_complete"
    assert audit["status"] == "PARTIAL / LIVE CLIENT WORKFLOW PROOF VERIFIED / LIVE REVENUE EVIDENCE REQUIRED / NO LIVE EXTERNAL DELIVERY"
    assert audit["passover_path"] == "06_AGENTS/VentureOps-External-Readiness-Passover.md"
    assert audit["handover_path"] == "06_AGENTS/VentureOps-External-Readiness-Handover.md"
    assert audit["handover_alias_valid"] is True
    assert audit["proof_chain_artifact_count"] == 17
    assert audit["latest_aor_chain_prefix"] == "07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-scope-contract"
    assert audit["live_client_scope_contract"]["status"] == "blocked_real_client_scope_required"
    assert audit["scorecard_metrics"]["live_client_scope_contract_written"] is True
    assert audit["scorecard_metrics"]["live_client_scope_proof_performed"] is False
    assert audit["scorecard_metrics"]["real_client_scope_present"] is False
    assert audit["scorecard_metrics"]["live_client_data_ingested"] is False
    assert audit["scorecard_metrics"]["live_external_delivery_performed"] is False
    assert audit["next_required_real_use_pass"] == "ventureops-live-revenue-proof"
    assert audit["next_guarded_command"] == (
        "chaseos ventureops live-revenue-proof-readiness --revenue-packet PATH --live-client-proof-path PATH --json"
    )
    assert "live client workflow proof missing" not in audit["missing_requirements"]
    assert "live revenue workflow proof missing" in audit["missing_requirements"]


def test_external_readiness_completion_audit_maps_prompt_to_artifacts() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    assert checklist["review VentureOps external readiness handover"]["status"] == "verified"
    assert checklist["validate canonical passover"]["status"] == "verified"
    assert checklist["TDD-backed implementation evidence"]["status"] == "verified"
    assert checklist["full VentureOps feature family complete"]["status"] == "blocked"
    assert checklist["live client workflow"]["status"] == "verified"
    assert checklist["live revenue workflow"]["status"] == "missing"
    assert checklist["live client workflow"]["evidence"]
    assert checklist["live revenue workflow"]["evidence"] == []


def test_ventureops_audits_include_latest_tdd_hardening_evidence() -> None:
    root = Path(__file__).resolve().parents[2]
    latest_tdd_log = (
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-client-safe-delivery-artifact-validation.md"
    )

    external_audit = audit_external_readiness_completion(root)
    external_checklist = {item["requirement"]: item for item in external_audit["prompt_to_artifact_checklist"]}
    feature_audit = build_feature_family_completion_audit(root)
    feature_checklist = {item["requirement"]: item for item in feature_audit["prompt_to_artifact_checklist"]}

    assert latest_tdd_log in external_checklist["TDD-backed implementation evidence"]["evidence"]
    assert latest_tdd_log in feature_checklist["TDD-backed validation tests"]["evidence"]


def test_feature_family_completion_audit_truth_sync_evidence_tracks_current_daily_writeback() -> None:
    root = Path(__file__).resolve().parents[2]

    feature_audit = build_feature_family_completion_audit(root)
    feature_checklist = {item["requirement"]: item for item in feature_audit["prompt_to_artifact_checklist"]}

    truth_sync = feature_checklist["truth-sync docs and indexes"]

    assert truth_sync["status"] == "verified"
    assert "07_LOGS/Daily/2026-05-12.md" in truth_sync["evidence"]
    assert "07_LOGS/Daily/Daily-Index.md" in truth_sync["evidence"]


def test_external_readiness_completion_audit_maps_actual_completion_artifact_discovery() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    discovery = checklist["actual final proof artifact discovery"]

    assert discovery["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in discovery["evidence"]
    assert "runtime.ventureops.validation.validate_live_revenue_proof_artifact" in discovery["evidence"]
    assert "Synthetic scorecard metrics alone cannot clear final completion" in discovery["notes"]
    assert audit["external_completion_artifacts"]["live_client_workflow_proof_present"] is True
    assert audit["external_completion_artifacts"]["live_revenue_workflow_proof_present"] is False


def test_external_readiness_completion_audit_maps_revenue_completion_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["revenue completion reference revalidation"]

    assert audit["revenue_completion_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_live_delivery_proof_artifact" in revalidation["evidence"]
    assert "referenced receipt, delivery proof, and client-safe delivery artifacts" in revalidation["notes"]


def test_external_readiness_completion_audit_maps_client_safe_delivery_artifact_validation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    validation = checklist["client-safe delivery artifact validation"]

    assert audit["client_safe_delivery_artifact_validation_valid"] is True
    assert validation["status"] == "verified"
    assert "runtime.ventureops.validation.validate_client_safe_delivery_artifact" in validation["evidence"]
    assert "runtime/ventureops/delivery_proof_packet_builder.py" in validation["evidence"]
    assert "runtime/ventureops/final_external_evidence_bundle.py" in validation["evidence"]
    assert "redacted JSON" in validation["notes"]


def test_feature_family_completion_audit_maps_client_safe_delivery_artifact_validation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    validation = checklist["client-safe delivery artifact validation"]

    assert audit["client_safe_delivery_artifact_validation_valid"] is True
    assert validation["status"] == "verified"
    assert "runtime.ventureops.validation.validate_client_safe_delivery_artifact" in validation["evidence"]
    assert "runtime/ventureops/final_external_evidence_bundle.py" in validation["evidence"]


def test_external_readiness_completion_audit_maps_live_revenue_packet_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["live-revenue packet reference revalidation"]

    assert audit["live_revenue_packet_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_live_revenue_evidence" in revalidation["evidence"]
    assert "referenced revenue packet" in revalidation["notes"]


def test_external_readiness_completion_audit_maps_live_client_source_digest_validation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    digest_validation = checklist["live-client workflow source digest validation"]

    assert audit["live_client_source_digest_validation_valid"] is True
    assert digest_validation["status"] == "verified"
    assert "runtime.ventureops.validation.validate_live_client_workflow_proof_artifact" in digest_validation["evidence"]
    assert "runtime/ventureops/live_client_workflow_proof.py" in digest_validation["evidence"]
    assert "source_digests must cover approved_read_paths" in digest_validation["notes"]


def test_external_readiness_completion_audit_maps_live_client_completion_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["live-client completion reference revalidation"]

    assert audit["live_client_completion_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_live_client_scope_proof_artifact" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_agent_scorecard" in revalidation["evidence"]
    assert "referenced scope proof gate, client report, and scorecard artifacts" in revalidation["notes"]


def test_external_readiness_completion_audit_maps_live_client_scope_packet_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["live-client scope packet reference revalidation"]

    assert audit["live_client_scope_packet_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_real_client_scope_evidence" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_scope_evidence_approval_artifact" in revalidation["evidence"]
    assert "referenced scope packet, approval artifact, and approved source files" in revalidation["notes"]


def test_external_readiness_completion_audit_maps_live_client_reference_consistency_validation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    consistency = checklist["live-client reference consistency validation"]

    assert audit["live_client_reference_consistency_validation_valid"] is True
    assert consistency["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in consistency["evidence"]
    assert "runtime.ventureops.validation.validate_live_client_scope_proof_artifact" in consistency["evidence"]
    assert "runtime.ventureops.validation.validate_agent_scorecard" in consistency["evidence"]
    assert "scope, approval, read paths, workflow id, and run id" in consistency["notes"]


def test_external_readiness_completion_audit_maps_revenue_reference_consistency_validation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    consistency = checklist["revenue reference consistency validation"]

    assert audit["revenue_reference_consistency_validation_valid"] is True
    assert consistency["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in consistency["evidence"]
    assert "runtime.ventureops.validation.validate_live_delivery_proof_artifact" in consistency["evidence"]
    assert "workflow id and client label" in consistency["notes"]


def test_external_readiness_completion_audit_maps_receipt_artifact_validation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    receipt_validation = checklist["receipt artifact validation"]

    assert audit["receipt_artifact_validation_valid"] is True
    assert receipt_validation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in receipt_validation["evidence"]
    assert "runtime.ventureops.validation._validate_redacted_receipt_artifact" in receipt_validation["evidence"]
    assert "receipt artifacts are JSON objects marked redacted" in receipt_validation["notes"]


def _seed_external_readiness_audit_root(root: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    required_paths = [
        "06_AGENTS/VentureOps-External-Readiness-Passover.md",
        "06_AGENTS/VentureOps-External-Readiness-Handover.md",
        "06_AGENTS/VentureOps-externaal-Readiness-Handover.md",
        "runtime/workflows/registry/templates/real_client_scope_evidence_schema.yaml",
        "runtime/workflows/registry/templates/live_revenue_evidence_schema.yaml",
        "05_TEMPLATES/Real-Client-Scope-Evidence-Template.md",
        "05_TEMPLATES/Live-Revenue-Evidence-Template.md",
        "runtime/ventureops/live_client_readiness.py",
        "runtime/ventureops/live_revenue_readiness.py",
        "runtime/ventureops/evidence_intake.py",
        "runtime/ventureops/evidence_discovery_preflight.py",
        "runtime/ventureops/scope_evidence_packet_builder.py",
        "runtime/ventureops/revenue_evidence_packet_builder.py",
        "runtime/ventureops/real_evidence_closeout_readiness.py",
        "runtime/ventureops/feature_family_completion_audit.py",
        "runtime/ventureops/final_external_execution_runbook.py",
        "runtime/ventureops/live_client_scope_proof.py",
        "runtime/ventureops/live_client_workflow_proof.py",
        "runtime/ventureops/live_revenue_proof.py",
        "runtime/cli/ventureops_commands.py",
        "runtime/cli/command_contract.json",
        "runtime/ventureops/test_ventureops.py",
        "runtime/ventureops/test_agent_runtime_governance_audit_workflow.py",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-live-client-scope-contract.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-scope-evidence-approval-prerequisite.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-scope-evidence-full-validation-cli.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-externaal-handover-next-pass-correction.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-audit-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-closeout-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-invalid-packet-status-hardening.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-live-client-readiness-fields.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-contract-readiness-disclosure.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-proof-cli-dynamic-date-default.md",
        "07_LOGS/Workflow-Proofs/2026-05-12_ventureops-live-client-proof-readiness-report.json",
        "07_LOGS/Workflow-Proofs/2026-05-12_ventureops-live-revenue-proof-readiness-report.json",
        "07_LOGS/Workflow-Proofs/2026-05-11_ventureops-scope-evidence-template.json",
        "07_LOGS/Workflow-Proofs/2026-05-11_ventureops-revenue-evidence-template.json",
    ]
    for rel in required_paths:
        _write(root / rel, (source_root / rel).read_text(encoding="utf-8"))
    for suffix in LIVE_CLIENT_SCOPE_EXPECTED_SUFFIXES:
        rel = f"{LIVE_CLIENT_SCOPE_PREFIX}{suffix}"
        _write(root / rel, (source_root / rel).read_text(encoding="utf-8"))


def test_external_readiness_completion_audit_can_complete_with_valid_final_artifacts(tmp_path: Path) -> None:
    from runtime.ventureops.final_external_evidence_bundle import (
        validate_final_external_evidence_bundle,
        write_final_external_evidence_bundle_report,
    )

    _seed_external_readiness_audit_root(tmp_path)
    bundle = _write_valid_final_evidence_bundle_fixture(tmp_path)
    bundle_report = validate_final_external_evidence_bundle(tmp_path, bundle_path=str(bundle))
    assert bundle_report["ready_for_completion_audit"] is True
    write_final_external_evidence_bundle_report(
        bundle_report,
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-final-evidence-bundle-validation-report.json",
    )

    audit = audit_external_readiness_completion(tmp_path)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    assert audit["external_completion_artifact_discovery_valid"] is True
    assert audit["complete"] is True
    assert audit["completion_decision"] == "complete"
    assert audit["missing_requirements"] == []
    assert audit["external_completion_artifacts"]["live_client_workflow_proof_present"] is True
    assert audit["external_completion_artifacts"]["live_revenue_workflow_proof_present"] is True
    assert audit["final_evidence_bundle_validation_report_present"] is True
    assert audit["final_evidence_bundle_validation_ready"] is True
    assert checklist["live client workflow"]["status"] == "verified"
    assert checklist["live revenue workflow"]["status"] == "verified"
    assert checklist["final evidence bundle validation report"]["status"] == "verified"
    assert checklist["full VentureOps feature family complete"]["status"] == "verified"


def test_external_readiness_completion_audit_requires_ready_final_bundle_validation_report(tmp_path: Path) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    _write_valid_final_evidence_bundle_fixture(tmp_path)

    audit = audit_external_readiness_completion(tmp_path)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    assert audit["external_completion_artifact_discovery_valid"] is True
    assert audit["external_completion_artifacts"]["live_client_workflow_proof_present"] is True
    assert audit["external_completion_artifacts"]["live_revenue_workflow_proof_present"] is True
    assert audit["final_evidence_bundle_validation_report_present"] is False
    assert audit["final_evidence_bundle_validation_ready"] is False
    assert audit["complete"] is False
    assert audit["completion_decision"] == "not_complete"
    assert "final evidence bundle validation missing" in audit["missing_requirements"]
    assert checklist["final evidence bundle validation report"]["status"] == "missing"
    assert checklist["full VentureOps feature family complete"]["status"] == "blocked"


def test_external_readiness_completion_audit_revalidates_final_bundle_report_bundle_path(tmp_path: Path) -> None:
    from runtime.ventureops.final_external_evidence_bundle import (
        validate_final_external_evidence_bundle,
        write_final_external_evidence_bundle_report,
    )

    _seed_external_readiness_audit_root(tmp_path)
    bundle = _write_valid_final_evidence_bundle_fixture(tmp_path)
    bundle_report = validate_final_external_evidence_bundle(tmp_path, bundle_path=str(bundle))
    assert bundle_report["ready_for_completion_audit"] is True
    write_final_external_evidence_bundle_report(
        bundle_report,
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-final-evidence-bundle-validation-report.json",
    )
    bundle.unlink()

    audit = audit_external_readiness_completion(tmp_path)
    invalid_reports = audit["final_evidence_bundle_validation_reports"]["invalid_final_evidence_bundle_validation_reports"]

    assert audit["complete"] is False
    assert audit["final_evidence_bundle_validation_ready"] is False
    assert audit["final_evidence_bundle_validation_report_present"] is False
    assert "final evidence bundle validation missing" in audit["missing_requirements"]
    assert invalid_reports[0]["path"] == "07_LOGS/Workflow-Proofs/client-alpha-final-evidence-bundle-validation-report.json"
    assert "report bundle_path is not currently valid: final evidence bundle missing" in invalid_reports[0]["errors"]


def test_external_readiness_completion_audit_maps_final_bundle_report_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["final evidence bundle report reference revalidation"]

    assert audit["final_evidence_bundle_report_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_final_evidence_bundle_validation_reports" in revalidation["evidence"]
    assert "runtime.ventureops.final_external_evidence_bundle.validate_final_external_evidence_bundle" in revalidation["evidence"]
    assert "report's referenced bundle" in revalidation["notes"]


def test_feature_family_completion_audit_maps_final_bundle_validation_ready_gate() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    gate = checklist["final evidence bundle validation report"]

    assert "ready final evidence bundle validation report exists" in audit["success_criteria"]
    assert audit["final_evidence_bundle_validation_ready"] is False
    assert gate["status"] == "blocked"
    assert "ready final-evidence-bundle validation report" in gate["notes"]
    assert "final evidence bundle validation missing" not in audit["missing_requirements"]


def test_feature_family_completion_audit_maps_final_bundle_report_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["final evidence bundle report reference revalidation"]

    assert audit["final_evidence_bundle_report_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_final_evidence_bundle_validation_reports" in revalidation["evidence"]
    assert "runtime.ventureops.final_external_evidence_bundle.validate_final_external_evidence_bundle" in revalidation["evidence"]
    assert "report's referenced bundle" in revalidation["notes"]


def test_external_readiness_completion_audit_maps_input_contracts_to_artifacts() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    scope_contract = checklist["real client scope evidence contract"]
    revenue_contract = checklist["live revenue evidence contract"]

    assert scope_contract["status"] == "verified"
    assert "runtime/workflows/registry/templates/real_client_scope_evidence_schema.yaml" in scope_contract["evidence"]
    assert "05_TEMPLATES/Real-Client-Scope-Evidence-Template.md" in scope_contract["evidence"]
    assert "runtime.ventureops.validation.validate_real_client_scope_evidence" in scope_contract["evidence"]
    assert "runtime.ventureops.validation.validate_scope_evidence_approval_artifact" in scope_contract["evidence"]
    assert "does not prove a live client workflow" in scope_contract["notes"]

    assert revenue_contract["status"] == "verified"
    assert "runtime/workflows/registry/templates/live_revenue_evidence_schema.yaml" in revenue_contract["evidence"]
    assert "05_TEMPLATES/Live-Revenue-Evidence-Template.md" in revenue_contract["evidence"]
    assert "runtime.ventureops.validation.validate_live_revenue_evidence" in revenue_contract["evidence"]
    assert "does not prove live revenue" in revenue_contract["notes"]

    readiness_contract = checklist["live client proof readiness CLI"]
    assert readiness_contract["status"] == "verified"
    assert "runtime/ventureops/live_client_readiness.py" in readiness_contract["evidence"]
    assert "runtime/cli/ventureops_commands.py" in readiness_contract["evidence"]
    assert "does not prove a live client workflow" in readiness_contract["notes"]

    revenue_readiness_contract = checklist["live revenue proof readiness CLI"]
    assert revenue_readiness_contract["status"] == "verified"
    assert "runtime/ventureops/live_revenue_readiness.py" in revenue_readiness_contract["evidence"]
    assert "runtime/cli/ventureops_commands.py" in revenue_readiness_contract["evidence"]
    assert "does not prove live revenue" in revenue_readiness_contract["notes"]


def test_external_readiness_completion_audit_maps_readiness_reports_to_artifacts() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    report_writeback = checklist["live readiness report writeback"]

    assert audit["readiness_report_writeback_valid"] is True
    assert report_writeback["status"] == "verified"
    assert "07_LOGS/Workflow-Proofs/2026-05-12_ventureops-live-client-proof-readiness-report.json" in report_writeback["evidence"]
    assert "07_LOGS/Workflow-Proofs/2026-05-12_ventureops-live-revenue-proof-readiness-report.json" in report_writeback["evidence"]
    assert "does not prove live client or live revenue completion" in report_writeback["notes"]


def test_external_readiness_completion_audit_maps_live_readiness_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["live readiness report write guard"]

    assert audit["live_readiness_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "existing report paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_live_readiness_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["live readiness report dated default"]

    assert audit["live_readiness_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_live_readiness_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["live readiness report default collision guard"]

    assert audit["live_readiness_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_external_readiness_completion_audit_maps_external_audit_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["external readiness audit report write guard"]

    assert audit["external_readiness_audit_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "escaped report paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_external_audit_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["external readiness audit report dated default"]

    assert audit["external_readiness_audit_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_external_audit_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["external readiness audit report default collision guard"]

    assert audit["external_readiness_audit_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_external_readiness_completion_audit_maps_evidence_templates_to_artifacts() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    template_writeback = checklist["external evidence packet templates"]

    assert audit["evidence_template_writeback_valid"] is True
    assert template_writeback["status"] == "verified"
    assert "07_LOGS/Workflow-Proofs/2026-05-11_ventureops-scope-evidence-template.json" in template_writeback["evidence"]
    assert "07_LOGS/Workflow-Proofs/2026-05-11_ventureops-revenue-evidence-template.json" in template_writeback["evidence"]
    assert "does not prove live client or live revenue completion" in template_writeback["notes"]


def test_external_readiness_completion_audit_maps_template_only_rejection_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    template_guard = checklist["template-only evidence rejection guard"]

    assert audit["template_only_rejection_guard_valid"] is True
    assert template_guard["status"] == "verified"
    assert "runtime.ventureops.validation.validate_real_client_scope_evidence" in template_guard["evidence"]
    assert "runtime.ventureops.validation.validate_live_revenue_evidence" in template_guard["evidence"]
    assert "template-only scaffolds cannot be accepted as proof" in template_guard["notes"]


def test_external_readiness_completion_audit_maps_guarded_live_client_scope_proof_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    proof_cli = checklist["guarded live client scope proof CLI"]

    assert audit["live_client_scope_proof_cli_valid"] is True
    assert proof_cli["status"] == "verified"
    assert "runtime/ventureops/live_client_scope_proof.py" in proof_cli["evidence"]
    assert "runtime/cli/ventureops_commands.py" in proof_cli["evidence"]
    assert "chaseos ventureops live-client-scope-proof" in proof_cli["evidence"]
    assert "does not prove a completed live client workflow until real scope evidence is run" in proof_cli["notes"]


def test_external_readiness_completion_audit_maps_guarded_live_client_workflow_proof_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    proof_cli = checklist["guarded live client workflow proof CLI"]

    assert audit["live_client_workflow_proof_cli_valid"] is True
    assert proof_cli["status"] == "verified"
    assert "runtime/ventureops/live_client_workflow_proof.py" in proof_cli["evidence"]
    assert "runtime/cli/ventureops_commands.py" in proof_cli["evidence"]
    assert "chaseos ventureops live-client-workflow-proof" in proof_cli["evidence"]
    assert "does not prove a completed live client workflow until real scope evidence is run" in proof_cli["notes"]


def test_external_readiness_completion_audit_maps_guarded_live_revenue_proof_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    proof_cli = checklist["guarded live revenue proof CLI"]

    assert audit["live_revenue_proof_cli_valid"] is True
    assert proof_cli["status"] == "verified"
    assert "runtime/ventureops/live_revenue_proof.py" in proof_cli["evidence"]
    assert "runtime/cli/ventureops_commands.py" in proof_cli["evidence"]
    assert "chaseos ventureops live-revenue-proof" in proof_cli["evidence"]
    assert "does not create an accounting claim or complete live revenue" in proof_cli["notes"]


def test_final_external_execution_runbook_maps_remaining_external_features() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    checklist = {item["requirement"]: item for item in runbook["runbook_checklist"]}

    assert runbook["ok"] is True
    assert runbook["complete"] is False
    assert runbook["readiness_status"] == "blocked"
    assert runbook["completion_decision"] == "not_complete"
    assert runbook["passover_valid"] is True
    assert runbook["requested_handover_alias_valid"] is True
    assert "live client workflow proof missing" not in runbook["missing_requirements"]
    assert "live revenue workflow proof missing" in runbook["missing_requirements"]
    assert runbook["next_required_real_use_pass"] == "ventureops-live-revenue-proof"
    assert (
        runbook["next_guarded_command"]
        == "chaseos ventureops live-revenue-proof-readiness --revenue-packet PATH --live-client-proof-path PATH --json"
    )
    assert "redacted live revenue evidence packet" in runbook["next_required_inputs"]
    assert runbook["next_command"].startswith("chaseos ventureops real-client-input-manifest")
    assert "--client-label LABEL" in runbook["next_command"]
    assert runbook["required_operator_inputs"] == [
        "typed real-client scope approval artifact",
        "real client-approved scope evidence packet",
        "approved scope source files inside the vault root",
        "valid live-client workflow proof artifact",
        "client-safe delivery artifact",
        "redacted live revenue evidence packet",
    ]
    assert runbook["runbook_stage_count"] >= 9
    assert runbook["command_sequence"][0]["command"].startswith("chaseos ventureops external-readiness-audit")
    assert any(
        step["command"].startswith("chaseos ventureops evidence-discovery-preflight")
        for step in runbook["command_sequence"]
    )
    assert any(
        step["command"].startswith("chaseos ventureops scope-evidence-packet")
        for step in runbook["command_sequence"]
    )
    assert any(
        step["command"].startswith("chaseos ventureops live-client-workflow-proof")
        for step in runbook["command_sequence"]
    )
    assert any(
        step["command"].startswith("chaseos ventureops live-revenue-proof")
        for step in runbook["command_sequence"]
    )
    assert any(
        step["command"].startswith("chaseos ventureops revenue-evidence-packet")
        for step in runbook["command_sequence"]
    )
    assert checklist["validated final external passover"]["status"] == "verified"
    assert checklist["real client workflow execution input"]["status"] == "blocked"
    assert checklist["live revenue workflow execution input"]["status"] == "blocked"
    assert runbook["live_external_delivery_performed"] is False
    assert runbook["payment_mutation_performed"] is False
    assert runbook["crm_mutation_performed"] is False
    assert runbook["revenue_claim_made"] is False


def test_ventureops_cli_final_external_execution_runbook_can_write_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "final-external-execution-runbook.json"

    result = _run_cli_json([
        "ventureops",
        "final-external-execution-runbook",
        "--vault-root",
        str(root),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))

    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert result["complete"] is False
    assert result["runbook_stage_count"] == len(result["command_sequence"])
    assert written["completion_decision"] == "not_complete"
    assert written["next_required_real_use_pass"] == "ventureops-live-revenue-proof"
    assert written["next_guarded_command"].startswith("chaseos ventureops live-revenue-proof-readiness")
    assert written["boundary"].startswith("operator runbook only")


def test_final_external_execution_runbook_cli_blocks_existing_report_path_without_overwrite(
    tmp_path: Path,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "final-external-execution-runbook.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing final runbook report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "final-external-execution-runbook",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing final runbook report"


def test_final_external_execution_runbook_cli_blocks_escaped_report_path_without_traceback(
    tmp_path: Path,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    escaped_report_path = tmp_path / ".." / "outside-final-external-runbook.json"

    result = _run_cli_json(
        [
            "ventureops",
            "final-external-execution-runbook",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_final_external_execution_runbook_cli_write_report_defaults_to_dated_report_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "final-external-execution-runbook",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-final-external-execution-runbook-report.json"
    )
    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / expected).exists()


def test_final_external_execution_runbook_cli_write_report_uses_collision_safe_default_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    monkeypatch.chdir(tmp_path)
    base = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-final-external-execution-runbook-report.json"
    )
    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-final-external-execution-runbook-report-2.json"
    )
    (tmp_path / base).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / base).write_text("existing final runbook report", encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "final-external-execution-runbook",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / base).read_text(encoding="utf-8") == "existing final runbook report"
    assert (tmp_path / expected).exists()


def test_ventureops_final_external_runbook_contract_discloses_readiness_preview() -> None:
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / "runtime" / "cli" / "command_contract.json").read_text(encoding="utf-8"))
    command = next(
        item
        for item in contract["commands"]
        if item["path"] == ["ventureops", "final-external-execution-runbook"]
    )

    assert "preview:validator-backed-live-client-and-revenue-readiness" in command["side_effects"]


def test_ventureops_real_client_input_manifest_contract_discloses_distinct_report_defaults() -> None:
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / "runtime" / "cli" / "command_contract.json").read_text(encoding="utf-8"))
    command = next(
        item
        for item in contract["commands"]
        if item["path"] == ["ventureops", "real-client-input-manifest"]
    )

    assert "default-write:dated-real-client-input-manifest-report-with---write-report" in command["side_effects"]
    assert "default-write:collision-safe-suffixed-real-client-input-manifest-report" in command["side_effects"]
    assert "default-write:collision-safe-dated-real-client-input-manifest-report" not in command["side_effects"]


def test_final_external_execution_runbook_keeps_invalid_supplied_packets_blocked(tmp_path: Path) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    scope_packet = tmp_path / "07_LOGS" / "Workflow-Proofs" / "invalid-scope-packet.json"
    revenue_packet = tmp_path / "07_LOGS" / "Workflow-Proofs" / "invalid-revenue-packet.json"
    _write(scope_packet, json.dumps({"type": "not-a-scope-packet"}, indent=2))
    _write(revenue_packet, json.dumps({"type": "not-a-revenue-packet"}, indent=2))

    runbook = build_final_external_execution_runbook(
        tmp_path,
        scope_packet_path=str(scope_packet),
        revenue_packet_path=str(revenue_packet),
    )
    stages = {step["stage"]: step for step in runbook["command_sequence"]}

    assert stages["scope evidence validation"]["status"] == "blocked"
    assert stages["live client proof readiness"]["status"] == "blocked"
    assert stages["revenue evidence validation"]["status"] == "blocked"
    assert stages["live revenue readiness"]["status"] == "blocked"


def test_final_external_execution_runbook_exposes_live_client_readiness_with_valid_scope(tmp_path: Path) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    scope_packet = _write_valid_scope_packet(tmp_path)

    runbook = build_final_external_execution_runbook(tmp_path, scope_packet_path=str(scope_packet))
    stages = {step["stage"]: step for step in runbook["command_sequence"]}

    assert runbook["ready_for_live_client_workflow_proof"] is True
    assert runbook["ready_for_live_revenue_proof"] is False
    assert stages["scope evidence validation"]["status"] == "ready"
    assert stages["live client proof readiness"]["status"] == "ready"
    assert stages["live client workflow proof"]["status"] == "ready"
    assert stages["live revenue readiness"]["status"] == "blocked"
    assert "live-client-workflow-proof" in runbook["next_command"]


def test_external_readiness_completion_audit_maps_final_external_runbook_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    runbook_cli = checklist["final external execution runbook CLI"]

    assert audit["final_external_execution_runbook_cli_valid"] is True
    assert runbook_cli["status"] == "verified"
    assert "runtime/ventureops/final_external_execution_runbook.py" in runbook_cli["evidence"]
    assert "runtime/cli/ventureops_commands.py" in runbook_cli["evidence"]
    assert "chaseos ventureops final-external-execution-runbook" in runbook_cli["evidence"]
    assert "does not execute live workflows" in runbook_cli["notes"]
    assert "final evidence bundle" in runbook_cli["notes"]


def test_external_readiness_completion_audit_maps_final_runbook_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["final external runbook report write guard"]

    assert audit["final_external_runbook_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "escaped report paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_final_runbook_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["final external runbook report dated default"]

    assert audit["final_external_runbook_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_final_runbook_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["final external runbook report default collision guard"]

    assert audit["final_external_runbook_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_ventureops_cli_external_readiness_audit_reports_blocked_completion() -> None:
    root = Path(__file__).resolve().parents[2]

    result = _run_cli_json([
        "ventureops",
        "external-readiness-audit",
        "--vault-root",
        str(root),
        "--json",
    ])

    assert result["ok"] is True
    assert result["complete"] is False
    assert result["completion_decision"] == "not_complete"
    assert result["passover_path"] == "06_AGENTS/VentureOps-External-Readiness-Passover.md"
    assert result["handover_alias_valid"] is True
    assert "live client workflow proof missing" not in result["missing_requirements"]
    assert "live revenue workflow proof missing" in result["missing_requirements"]


def test_ventureops_cli_external_readiness_audit_can_write_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "external-readiness-audit.json"

    result = _run_cli_json([
        "ventureops",
        "external-readiness-audit",
        "--vault-root",
        str(root),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))

    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert written["completion_decision"] == "not_complete"
    assert written["complete"] is False
    assert written["report_written"] is True
    assert written["readiness_report_writeback_valid"] is True


def test_external_readiness_audit_cli_blocks_existing_report_path_without_overwrite(tmp_path: Path) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "external-readiness-audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing external readiness report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "external-readiness-audit",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing external readiness report"


def test_external_readiness_audit_cli_blocks_escaped_report_path_without_traceback(tmp_path: Path) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    escaped_report_path = tmp_path / ".." / "outside-external-readiness-audit.json"

    result = _run_cli_json(
        [
            "ventureops",
            "external-readiness-audit",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_external_readiness_audit_cli_write_report_defaults_to_dated_report_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "external-readiness-audit",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-external-readiness-audit-report.json"
    )
    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / expected).exists()


def test_external_readiness_audit_cli_write_report_uses_collision_safe_default_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    monkeypatch.chdir(tmp_path)
    base = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-external-readiness-audit-report.json"
    )
    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-external-readiness-audit-report-2.json"
    )
    (tmp_path / base).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / base).write_text("existing external readiness report", encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "external-readiness-audit",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / base).read_text(encoding="utf-8") == "existing external readiness report"
    assert (tmp_path / expected).exists()


def test_ventureops_cli_validates_scope_and_revenue_evidence_packets(tmp_path: Path) -> None:
    scope_packet = tmp_path / "scope.json"
    scope_packet.write_text(
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-001",
                "client_label": "Client Alpha",
                "approval_id": "operator-approval-client-alpha-scope",
                "approval_status": "approved",
                "approval_artifact_path": "03_INPUTS/client-alpha/scope-approval.json",
                "approved_read_paths": ["README.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            }
        ),
        encoding="utf-8",
    )
    revenue_packet = tmp_path / "revenue.json"
    revenue_packet.write_text(
        json.dumps(
            {
                "type": "ventureops-live-revenue-evidence",
                "revenue_proof_id": "revenue-client-alpha-001",
                "workflow_id": "agent_runtime_governance_audit",
                "client_label": "Client Alpha",
                "payment_reference_id": "pay_ref_redacted_alpha",
                "payment_status": "received",
                "amount": "250.00",
                "currency": "USD",
                "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
                "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json",
                "crm_reference_id": "crm_ref_redacted_alpha",
                "approval_id": "operator-approval-client-alpha-revenue",
                "revenue_recognition_boundary": "proof_only_no_accounting_claim",
            }
        ),
        encoding="utf-8",
    )

    scope_result = _run_cli_json([
        "ventureops",
        "validate-scope-evidence",
        "--packet",
        str(scope_packet),
        "--json",
    ])
    revenue_result = _run_cli_json([
        "ventureops",
        "validate-revenue-evidence",
        "--packet",
        str(revenue_packet),
        "--json",
    ])

    assert scope_result["ok"] is True
    assert scope_result["approved_read_path_count"] == 1
    assert scope_result["scope_evidence_valid"] is True
    assert scope_result["live_client_scope_proof_performed"] is False
    assert revenue_result["ok"] is True
    assert revenue_result["currency"] == "USD"
    assert revenue_result["revenue_evidence_valid"] is True
    assert revenue_result["revenue_claim_made"] is False


def test_ventureops_cli_validate_scope_evidence_can_run_full_root_validation(tmp_path: Path) -> None:
    source_path = tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md"
    _write(source_path, "redacted client scope\n")
    approval = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-full-cli",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-full-cli",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )
    scope_packet = tmp_path / "03_INPUTS" / "client-alpha" / "scope-evidence.json"
    scope_packet.write_text(
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-full-cli",
                "client_label": "Client Alpha",
                "approval_id": "operator-approval-client-alpha-full-cli",
                "approval_status": "approved",
                "approval_artifact_path": approval["approval_artifact_path"],
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli_json([
        "ventureops",
        "validate-scope-evidence",
        "--packet",
        str(scope_packet),
        "--vault-root",
        str(tmp_path),
        "--json",
    ])

    assert result["ok"] is True
    assert result["full_scope_validation_performed"] is True
    assert result["scope_evidence_valid"] is True
    assert result["scope_approval_artifact_valid"] is True
    assert result["scope_sources_valid"] is True
    assert result["scope_approval_validation"]["approval_id"] == "operator-approval-client-alpha-full-cli"
    assert result["scope_source_validation"]["existing_sources"] == ["03_INPUTS/client-alpha/redacted-brief.md"]
    assert result["live_client_data_ingested"] is False


def test_ventureops_cli_writes_scope_evidence_template(tmp_path: Path) -> None:
    output_path = tmp_path / "scope-template.json"

    result = _run_cli_json([
        "ventureops",
        "evidence-template",
        "--kind",
        "scope",
        "--output",
        str(output_path),
        "--json",
    ])
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["template_written"] is True
    assert result["output_path"] == str(output_path)
    assert written["type"] == "ventureops-real-client-scope-evidence"
    assert written["template_only"] is True
    assert written["approved_read_paths"] == []
    assert written["delivery_boundary"] == "no_external_delivery"
    assert result["ready_for_validation"] is False
    assert "validate-scope-evidence" in result["validator_command"]


def test_ventureops_cli_writes_revenue_evidence_template(tmp_path: Path) -> None:
    output_path = tmp_path / "revenue-template.json"

    result = _run_cli_json([
        "ventureops",
        "evidence-template",
        "--kind",
        "revenue",
        "--output",
        str(output_path),
        "--json",
    ])
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["template_written"] is True
    assert result["output_path"] == str(output_path)
    assert written["type"] == "ventureops-live-revenue-evidence"
    assert written["template_only"] is True
    assert written["amount"] == 0
    assert written["revenue_recognition_boundary"] == "proof_only_no_accounting_claim"
    assert result["ready_for_validation"] is False
    assert "validate-revenue-evidence" in result["validator_command"]


def test_ventureops_cli_live_client_proof_readiness_blocks_without_scope_packet() -> None:
    root = Path(__file__).resolve().parents[2]

    result = _run_cli_json([
        "ventureops",
        "live-client-proof-readiness",
        "--vault-root",
        str(root),
        "--json",
    ])

    assert result["ok"] is True
    assert result["ready_for_live_client_scope_proof_gate"] is False
    assert "real client scope evidence packet missing" in result["blockers"]
    assert result["next_required_action"] == "collect real-client scope inputs through real-client-input-manifest"
    assert "--approval-output PATH" in result["next_command"]
    assert "--scope-packet-output PATH" in result["next_command"]
    assert result["live_client_scope_proof_performed"] is False
    assert result["live_client_data_ingested"] is False
    assert result["live_external_delivery_performed"] is False


def test_ventureops_cli_live_client_proof_readiness_accepts_valid_scope_packet(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    approval_path = tmp_path / "scope-approval.json"
    approval_relative = str(approval_path.relative_to(root)).replace("\\", "/")
    _write(
        approval_path,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-approval-client-alpha-scope-002",
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-002",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": ["README.md"],
                "redaction_policy": "redacted_extracts_only",
                "delivery_boundary": "no_external_delivery",
                "operator_attested_scope_approved": True,
                "external_send_authorized": False,
                "payment_mutation_authorized": False,
                "crm_mutation_authorized": False,
                "provider_calls_authorized": False,
                "browser_actions_authorized": False,
                "revenue_claim_authorized": False,
            }
        ),
    )
    scope_packet = tmp_path / "scope.json"
    scope_packet.write_text(
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-002",
                "client_label": "Client Alpha",
                "approval_id": "operator-approval-client-alpha-scope-002",
                "approval_status": "approved",
                "approval_artifact_path": approval_relative,
                "approved_read_paths": ["README.md"],
                "redaction_policy": "redacted_extracts_only",
                "delivery_boundary": "no_external_delivery",
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli_json([
        "ventureops",
        "live-client-proof-readiness",
        "--vault-root",
        str(root),
        "--scope-packet",
        str(scope_packet),
        "--json",
    ])

    assert result["ok"] is True
    assert result["scope_evidence_valid"] is True
    assert result["scope_approval_artifact_valid"] is True
    assert result["ready_for_live_client_scope_proof_gate"] is True
    assert result["ready_for_live_client_workflow"] is True
    assert result["ready_for_live_client_workflow_proof"] is True
    assert result["next_required_action"] == "run live-client-workflow-proof with --execute-proof"
    assert "live-client-workflow-proof" in result["next_command"]
    assert result["recommended_workflow_inputs"]["include_live_client_scope_proof_gate"] is True
    assert result["recommended_workflow_inputs"]["real_client_scope_evidence_path"] == str(scope_packet)
    assert result["live_client_scope_proof_performed"] is False
    assert result["live_client_data_ingested"] is False
    assert "does not run the live client workflow" in result["boundary"]


def test_ventureops_cli_live_client_proof_readiness_blocks_missing_scope_sources(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json",
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-approval-client-alpha-scope-missing",
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-missing",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": ["03_INPUTS/client-alpha/missing-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
                "operator_attested_scope_approved": True,
                "external_send_authorized": False,
                "payment_mutation_authorized": False,
                "crm_mutation_authorized": False,
                "provider_calls_authorized": False,
                "browser_actions_authorized": False,
                "revenue_claim_authorized": False,
            }
        ),
    )
    scope_packet = tmp_path / "scope.json"
    scope_packet.write_text(
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-missing",
                "client_label": "Client Alpha",
                "approval_id": "operator-approval-client-alpha-scope-missing",
                "approval_status": "approved",
                "approval_artifact_path": "03_INPUTS/client-alpha/scope-approval.json",
                "approved_read_paths": ["03_INPUTS/client-alpha/missing-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli_json([
        "ventureops",
        "live-client-proof-readiness",
        "--vault-root",
        str(root),
        "--scope-packet",
        str(scope_packet),
        "--json",
    ])

    assert result["ok"] is True
    assert result["scope_evidence_valid"] is True
    assert result["scope_approval_artifact_valid"] is True
    assert result["scope_sources_valid"] is False
    assert result["ready_for_live_client_scope_proof_gate"] is False
    assert "approved source path missing: 03_INPUTS/client-alpha/missing-brief.md" in result["blockers"]


def test_ventureops_cli_live_revenue_proof_readiness_blocks_without_packet_or_live_client() -> None:
    root = Path(__file__).resolve().parents[2]

    result = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(root),
        "--json",
    ])

    assert result["ok"] is True
    assert result["ready_for_live_revenue_proof"] is False
    assert "live client proof artifact path missing" in result["blockers"]
    assert "live revenue evidence packet missing" in result["blockers"]
    assert result["revenue_evidence_valid"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_ventureops_cli_live_revenue_proof_readiness_keeps_valid_packet_blocked_until_live_client(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    revenue_packet = tmp_path / "revenue.json"
    revenue_packet.write_text(
        json.dumps(
            {
                "type": "ventureops-live-revenue-evidence",
                "revenue_proof_id": "revenue-client-alpha-002",
                "workflow_id": "agent_runtime_governance_audit",
                "client_label": "Client Alpha",
                "payment_reference_id": "pay_ref_redacted_alpha_002",
                "payment_status": "settled",
                "amount": "500.00",
                "currency": "USD",
                "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-002-redacted.json",
                "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-002-redacted.json",
                "crm_reference_id": "crm_ref_redacted_alpha_002",
                "approval_id": "operator-approval-client-alpha-revenue-002",
                "revenue_recognition_boundary": "proof_only_no_accounting_claim",
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(root),
        "--revenue-packet",
        str(revenue_packet),
        "--json",
    ])

    assert result["ok"] is True
    assert result["revenue_evidence_valid"] is True
    assert result["ready_for_live_revenue_proof"] is False
    assert "live client proof artifact path missing" in result["blockers"]
    assert any(blocker.startswith("delivery proof artifact missing") for blocker in result["blockers"])
    assert result["recommended_order"][0] == "complete live client workflow proof"
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False
    assert "does not prove live revenue" in result["boundary"]


def test_ventureops_cli_live_revenue_proof_readiness_validates_live_client_proof_path(
    tmp_path: Path,
) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(tmp_path),
        "--revenue-packet",
        str(revenue_packet),
        "--live-client-proof-path",
        str(live_client_proof),
        "--json",
    ])

    assert result["ok"] is True
    assert result["revenue_evidence_valid"] is True
    assert result["live_client_proof_artifact_present"] is True
    assert result["live_client_proof_artifact_valid"] is True
    assert result["live_client_proof_validation"]["ok"] is True
    assert not any("live client proof artifact invalid" in blocker for blocker in result["blockers"])
    assert result["payment_mutation_performed"] is False


def test_live_readiness_cli_blocks_existing_report_paths_without_overwrite(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client_report = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-readiness.json"
    revenue_report = tmp_path / "07_LOGS" / "Workflow-Proofs" / "revenue-readiness.json"
    _write(client_report, "existing client readiness\n")
    _write(revenue_report, "existing revenue readiness\n")

    client = _run_cli_json(
        [
            "ventureops",
            "live-client-proof-readiness",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(client_report),
            "--json",
        ]
    )
    revenue = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof-readiness",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(revenue_report),
            "--json",
        ]
    )

    assert client["ok"] is False
    assert client["report_write_blocked"] is True
    assert any("report path already exists" in error for error in client["errors"])
    assert client_report.read_text(encoding="utf-8") == "existing client readiness\n"
    assert revenue["ok"] is False
    assert revenue["report_write_blocked"] is True
    assert any("report path already exists" in error for error in revenue["errors"])
    assert revenue_report.read_text(encoding="utf-8") == "existing revenue readiness\n"


def test_live_readiness_cli_blocks_escaped_report_paths_without_traceback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    escaped = tmp_path.parent / f"{tmp_path.name}-escaped-live-readiness.json"

    client = _run_cli_json(
        [
            "ventureops",
            "live-client-proof-readiness",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped),
            "--json",
        ]
    )
    revenue = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof-readiness",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped),
            "--json",
        ]
    )

    assert client["ok"] is False
    assert client["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in client["errors"])
    assert revenue["ok"] is False
    assert revenue["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in revenue["errors"])
    assert not escaped.exists()


def test_live_readiness_cli_write_report_defaults_to_dated_report_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client_expected = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-live-client-proof-readiness-report.json"
    )
    revenue_expected = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-live-revenue-proof-readiness-report.json"
    )

    client = _run_cli_json([
        "ventureops",
        "live-client-proof-readiness",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])
    revenue = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    assert client["report_written"] is True
    assert Path(client["report_path"]) == client_expected.relative_to(tmp_path)
    assert client_expected.exists()
    assert revenue["report_written"] is True
    assert Path(revenue["report_path"]) == revenue_expected.relative_to(tmp_path)
    assert revenue_expected.exists()


def test_live_readiness_cli_write_report_uses_collision_safe_default_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client_base = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-live-client-proof-readiness-report.json"
    )
    revenue_base = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-live-revenue-proof-readiness-report.json"
    )
    _write(client_base, json.dumps({"existing": "client base"}))
    _write(revenue_base, json.dumps({"existing": "revenue base"}))

    client = _run_cli_json([
        "ventureops",
        "live-client-proof-readiness",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])
    revenue = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    client_expected = client_base.with_name(client_base.stem + "-2" + client_base.suffix)
    revenue_expected = revenue_base.with_name(revenue_base.stem + "-2" + revenue_base.suffix)
    assert client["report_written"] is True
    assert Path(client["report_path"]) == client_expected.relative_to(tmp_path)
    assert json.loads(client_base.read_text(encoding="utf-8")) == {"existing": "client base"}
    assert client_expected.exists()
    assert revenue["report_written"] is True
    assert Path(revenue["report_path"]) == revenue_expected.relative_to(tmp_path)
    assert json.loads(revenue_base.read_text(encoding="utf-8")) == {"existing": "revenue base"}
    assert revenue_expected.exists()
    assert revenue["revenue_claim_made"] is False


def test_ventureops_cli_live_revenue_proof_readiness_rejects_scope_gate_prerequisite(
    tmp_path: Path,
) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)
    live_client_proof.write_text(json.dumps(_valid_live_client_scope_proof_artifact(), indent=2), encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(tmp_path),
        "--revenue-packet",
        str(revenue_packet),
        "--live-client-proof-path",
        str(live_client_proof),
        "--json",
    ])

    assert result["ok"] is True
    assert result["ready_for_live_revenue_proof"] is False
    assert result["live_client_proof_artifact_present"] is True
    assert result["live_client_proof_artifact_valid"] is False
    assert "type must be ventureops-live-client-workflow-proof" in result["live_client_proof_validation"]["errors"]
    assert "live client proof artifact invalid" in result["blockers"]
    assert result["revenue_claim_made"] is False


def test_ventureops_cli_live_revenue_proof_readiness_rejects_invalid_delivery_proof(
    tmp_path: Path,
) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)
    delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    delivery.write_text(json.dumps({"redacted": True, "delivery_status": "delivered"}, indent=2), encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(tmp_path),
        "--revenue-packet",
        str(revenue_packet),
        "--live-client-proof-path",
        str(live_client_proof),
        "--json",
    ])

    assert result["ok"] is True
    assert result["ready_for_live_revenue_proof"] is False
    assert result["delivery_proof_artifact_present"] is True
    assert result["delivery_proof_artifact_valid"] is False
    assert "delivery proof artifact invalid" in result["blockers"]
    assert "type must be ventureops-live-delivery-proof" in result["delivery_proof_validation"]["errors"]
    assert result["revenue_claim_made"] is False


def _write_valid_revenue_proof_fixture(root: Path) -> tuple[Path, Path]:
    receipt = root / "07_LOGS" / "Revenue-Proofs" / "client-alpha-receipt-redacted.json"
    client_safe_delivery = root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json"
    delivery = root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    live_client_proof = root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    revenue_packet = root / "runtime" / "ventureops" / "fixtures" / "revenue-evidence" / "client-alpha-revenue.json"
    _write(receipt, json.dumps({"redacted": True, "payment_status": "settled"}))
    _write(client_safe_delivery, json.dumps(_valid_client_safe_delivery_artifact(), indent=2))
    _write(delivery, json.dumps(_valid_live_delivery_proof_artifact(), indent=2))
    _write(
        live_client_proof,
        json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2),
    )
    _write(
        revenue_packet,
        json.dumps(
            {
                "type": "ventureops-live-revenue-evidence",
                "revenue_proof_id": "revenue-client-alpha-003",
                "workflow_id": "agent_runtime_governance_audit",
                "client_label": "Client Alpha",
                "payment_reference_id": "pay_ref_redacted_alpha_003",
                "payment_status": "settled",
                "amount": "500.00",
                "currency": "USD",
                "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
                "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
                "crm_reference_id": "crm_ref_redacted_alpha_003",
                "approval_id": "operator-approval-client-alpha-revenue-003",
                "revenue_recognition_boundary": "proof_only_no_accounting_claim",
            },
            indent=2,
        ),
    )
    return revenue_packet, live_client_proof


def test_ventureops_live_revenue_proof_cli_requires_execute_flag(tmp_path: Path) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof",
            "--vault-root",
            str(tmp_path),
            "--revenue-packet",
            str(revenue_packet),
            "--live-client-proof-path",
            str(live_client_proof),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert "requires --execute-proof" in result["error"]
    assert result["live_revenue_proof_written"] is False
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_ventureops_live_revenue_proof_cli_writes_proof_only_artifact(tmp_path: Path) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof",
            "--vault-root",
            str(tmp_path),
            "--revenue-packet",
            str(revenue_packet),
            "--live-client-proof-path",
            str(live_client_proof),
            "--date",
            "2026-05-11",
            "--execute-proof",
            "--json",
        ],
    )

    assert result["ok"] is True
    assert result["live_revenue_proof_written"] is True
    assert result["proof_path"].endswith("2026-05-11_revenue-client-alpha-003_live-revenue-proof.json")
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["invoice_sent"] is False
    assert result["external_send_performed"] is False
    assert result["revenue_claim_made"] is False

    proof = json.loads((tmp_path / result["proof_path"]).read_text(encoding="utf-8"))
    assert proof["type"] == "ventureops-live-revenue-proof"
    assert proof["status"] == "proof_only_recorded_no_accounting_claim"
    assert proof["amount"] == 500.0
    assert proof["currency"] == "USD"
    assert proof["receipt_artifact_exists"] is True
    assert proof["delivery_proof_exists"] is True
    assert proof["delivery_proof_artifact_valid"] is True
    assert proof["live_client_proof_exists"] is True
    assert proof["payment_mutation_performed"] is False
    assert proof["crm_mutation_performed"] is False
    assert proof["revenue_claim_made"] is False


def test_ventureops_guarded_proof_commands_reject_existing_proof_outputs(tmp_path: Path) -> None:
    scope_packet = _write_valid_scope_packet(tmp_path)
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)
    sentinel = '{"existing": true}\n'
    scope_gate_path = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / "2026-05-11_agent_runtime_governance_audit_live-client-scope-proof_live-client-scope-proof-gate.json"
    )
    workflow_proof_path = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / "2026-05-11_agent_runtime_governance_audit_live-client-workflow-proof_live-client-workflow-proof.json"
    )
    revenue_proof_path = (
        tmp_path / "07_LOGS" / "Revenue-Proofs" / "2026-05-11_revenue-client-alpha-003_live-revenue-proof.json"
    )
    for path in [scope_gate_path, workflow_proof_path, revenue_proof_path]:
        _write(path, sentinel)

    scope_result = _run_cli_json(
        [
            "ventureops",
            "live-client-scope-proof",
            "--vault-root",
            str(tmp_path),
            "--scope-packet",
            str(scope_packet),
            "--date",
            "2026-05-11",
            "--execute-proof",
            "--json",
        ],
        expected_exit=1,
    )
    workflow_result = _run_cli_json(
        [
            "ventureops",
            "live-client-workflow-proof",
            "--vault-root",
            str(tmp_path),
            "--scope-packet",
            str(scope_packet),
            "--date",
            "2026-05-11",
            "--execute-proof",
            "--json",
        ],
        expected_exit=1,
    )
    revenue_result = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof",
            "--vault-root",
            str(tmp_path),
            "--revenue-packet",
            str(revenue_packet),
            "--live-client-proof-path",
            str(live_client_proof),
            "--date",
            "2026-05-11",
            "--execute-proof",
            "--json",
        ],
        expected_exit=1,
    )

    assert scope_result["ok"] is False
    assert scope_result["live_client_scope_proof_gate_written"] is False
    assert workflow_result["ok"] is False
    assert workflow_result["live_client_workflow_proof_written"] is False
    assert revenue_result["ok"] is False
    assert revenue_result["live_revenue_proof_written"] is False
    for result in [scope_result, workflow_result, revenue_result]:
        assert result["error"] == "proof output path already exists"
        assert "proof output path already exists:" in result["errors"][0]
    for path in [scope_gate_path, workflow_proof_path, revenue_proof_path]:
        assert path.read_text(encoding="utf-8") == sentinel


def test_ventureops_live_revenue_proof_cli_rejects_invalid_live_client_proof_artifact(tmp_path: Path) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)
    invalid = {**_valid_live_client_workflow_proof_artifact(), "scoped_client_data_ingested": False}
    live_client_proof.write_text(json.dumps(invalid, indent=2), encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof",
            "--vault-root",
            str(tmp_path),
            "--revenue-packet",
            str(revenue_packet),
            "--live-client-proof-path",
            str(live_client_proof),
            "--execute-proof",
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["live_revenue_proof_written"] is False
    assert result["error"] == "live client proof artifact invalid"
    assert "scoped_client_data_ingested must be true" in result["errors"]
    assert result["revenue_claim_made"] is False


def test_ventureops_live_revenue_proof_cli_rejects_scope_gate_as_live_workflow_proof(tmp_path: Path) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)
    live_client_proof.write_text(json.dumps(_valid_live_client_scope_proof_artifact(), indent=2), encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof",
            "--vault-root",
            str(tmp_path),
            "--revenue-packet",
            str(revenue_packet),
            "--live-client-proof-path",
            str(live_client_proof),
            "--execute-proof",
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["live_revenue_proof_written"] is False
    assert result["error"] == "live client proof artifact invalid"
    assert "type must be ventureops-live-client-workflow-proof" in result["errors"]


def test_ventureops_live_revenue_proof_cli_rejects_invalid_delivery_proof_artifact(tmp_path: Path) -> None:
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)
    delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    delivery.write_text(json.dumps({"redacted": True, "delivery_status": "delivered"}, indent=2), encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "live-revenue-proof",
            "--vault-root",
            str(tmp_path),
            "--revenue-packet",
            str(revenue_packet),
            "--live-client-proof-path",
            str(live_client_proof),
            "--execute-proof",
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["live_revenue_proof_written"] is False
    assert result["error"] == "delivery proof artifact invalid"
    assert "type must be ventureops-live-delivery-proof" in result["errors"]
    assert result["delivery_proof_artifact_valid"] is False
    assert result["revenue_claim_made"] is False


def test_ventureops_cli_live_client_readiness_can_write_audit_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "live-client-readiness.json"

    result = _run_cli_json([
        "ventureops",
        "live-client-proof-readiness",
        "--vault-root",
        str(root),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert written["ready_for_live_client_scope_proof_gate"] is False
    assert written["live_client_data_ingested"] is False
    assert written["live_external_delivery_performed"] is False


def test_ventureops_cli_live_revenue_readiness_can_write_audit_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "live-revenue-readiness.json"

    result = _run_cli_json([
        "ventureops",
        "live-revenue-proof-readiness",
        "--vault-root",
        str(root),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert written["ready_for_live_revenue_proof"] is False
    assert written["payment_mutation_performed"] is False
    assert written["revenue_claim_made"] is False


def _write_valid_scope_packet(root: Path) -> Path:
    scope_packet = root / "runtime" / "ventureops" / "fixtures" / "scope-evidence" / "client-alpha-scope.json"
    _write(root / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client fixture\n")
    approval = build_scope_approval_packet(
        root,
        approval_id="operator-approval-client-alpha-scope-004",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-004",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )
    _write(
        scope_packet,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-004",
                "client_label": "Client Alpha",
                "approval_id": "operator-approval-client-alpha-scope-004",
                "approval_status": "approved",
                "approval_artifact_path": approval["approval_artifact_path"],
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            },
            indent=2,
        ),
    )
    return scope_packet


def test_ventureops_evidence_intake_cli_blocks_without_operator_packets(tmp_path: Path) -> None:
    result = _run_cli_json([
        "ventureops",
        "evidence-intake",
        "--vault-root",
        str(tmp_path),
        "--json",
    ])

    assert result["ok"] is True
    assert result["intake_status"] == "blocked"
    assert result["scope_packet_present"] is False
    assert result["revenue_packet_present"] is False
    assert result["ready_for_live_client_scope_proof_gate"] is False
    assert result["ready_for_live_revenue_proof"] is False
    assert result["next_required_action"] == "collect real-client scope inputs through real-client-input-manifest"
    assert "--approval-output PATH" in result["next_command"]
    assert "--scope-packet-output PATH" in result["next_command"]
    assert result["live_client_scope_proof_performed"] is False
    assert result["live_client_data_ingested"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_ventureops_evidence_intake_cli_routes_valid_scope_to_live_client_workflow_proof(tmp_path: Path) -> None:
    scope_packet = _write_valid_scope_packet(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "evidence-intake",
        "--vault-root",
        str(tmp_path),
        "--scope-packet",
        str(scope_packet),
        "--json",
    ])

    assert result["ok"] is True
    assert result["scope_packet_present"] is True
    assert result["scope_evidence_valid"] is True
    assert result["ready_for_live_client_scope_proof_gate"] is True
    assert result["ready_for_live_client_workflow_proof"] is True
    assert result["ready_for_live_revenue_proof"] is False
    assert result["next_required_action"] == "run live-client-workflow-proof with --execute-proof"
    assert "live-client-workflow-proof" in result["next_command"]
    assert result["live_client_scope_proof_performed"] is False
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_client_data_ingested"] is False


def test_ventureops_evidence_intake_cli_routes_valid_revenue_to_proof_only_command(tmp_path: Path) -> None:
    scope_packet = _write_valid_scope_packet(tmp_path)
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "evidence-intake",
        "--vault-root",
        str(tmp_path),
        "--scope-packet",
        str(scope_packet),
        "--revenue-packet",
        str(revenue_packet),
        "--live-client-proof-path",
        str(live_client_proof),
        "--json",
    ])

    assert result["ok"] is True
    assert result["scope_evidence_valid"] is True
    assert result["revenue_evidence_valid"] is True
    assert result["live_client_proof_artifact_present"] is True
    assert result["receipt_artifact_present"] is True
    assert result["delivery_proof_artifact_present"] is True
    assert result["ready_for_live_revenue_proof"] is True
    assert result["next_required_action"] == "run live-revenue-proof with --execute-proof"
    assert "live-revenue-proof" in result["next_command"]
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_ventureops_evidence_intake_cli_rejects_invalid_delivery_proof(tmp_path: Path) -> None:
    scope_packet = _write_valid_scope_packet(tmp_path)
    revenue_packet, live_client_proof = _write_valid_revenue_proof_fixture(tmp_path)
    delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    delivery.write_text(json.dumps({"redacted": True, "delivery_status": "delivered"}, indent=2), encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "evidence-intake",
        "--vault-root",
        str(tmp_path),
        "--scope-packet",
        str(scope_packet),
        "--revenue-packet",
        str(revenue_packet),
        "--live-client-proof-path",
        str(live_client_proof),
        "--json",
    ])

    assert result["ok"] is True
    assert result["revenue_evidence_valid"] is True
    assert result["delivery_proof_artifact_present"] is True
    assert result["delivery_proof_artifact_valid"] is False
    assert result["ready_for_live_revenue_proof"] is False
    assert "delivery proof artifact invalid" in result["blockers"]
    assert "type must be ventureops-live-delivery-proof" in result["delivery_proof_validation"]["errors"]
    assert result["revenue_claim_made"] is False


def test_ventureops_evidence_intake_cli_blocks_existing_report_path_without_overwrite(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "evidence-intake.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing evidence intake report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "evidence-intake",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing evidence intake report"


def test_ventureops_evidence_intake_cli_blocks_escaped_report_path_without_traceback(
    tmp_path: Path,
) -> None:
    escaped_report_path = tmp_path / ".." / "outside-evidence-intake.json"

    result = _run_cli_json(
        [
            "ventureops",
            "evidence-intake",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_ventureops_evidence_intake_cli_write_report_defaults_to_dated_report_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "evidence-intake",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-evidence-intake-report.json"
    )
    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / expected).exists()


def test_ventureops_evidence_intake_cli_write_report_uses_collision_safe_default_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    base = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-evidence-intake-report.json"
    )
    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-evidence-intake-report-2.json"
    )
    (tmp_path / base).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / base).write_text("existing evidence intake report", encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "evidence-intake",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / base).read_text(encoding="utf-8") == "existing evidence intake report"
    assert (tmp_path / expected).exists()


def test_external_readiness_completion_audit_maps_evidence_intake_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    intake_cli = checklist["operator evidence intake CLI"]

    assert audit["evidence_intake_cli_valid"] is True
    assert intake_cli["status"] == "verified"
    assert "runtime/ventureops/evidence_intake.py" in intake_cli["evidence"]
    assert "chaseos ventureops evidence-intake" in intake_cli["evidence"]
    assert "does not run live client or revenue workflows" in intake_cli["notes"]


def test_external_readiness_completion_audit_maps_evidence_intake_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["evidence intake report write guard"]

    assert audit["evidence_intake_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "escaped report paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_evidence_intake_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["evidence intake report dated default"]

    assert audit["evidence_intake_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_evidence_intake_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["evidence intake report default collision guard"]

    assert audit["evidence_intake_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_external_readiness_completion_audit_maps_live_client_proof_artifact_verifier() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    verifier = checklist["live client proof artifact verifier"]

    assert audit["live_client_proof_artifact_verifier_valid"] is True
    assert verifier["status"] == "verified"
    assert "runtime.ventureops.validation.validate_live_client_scope_proof_artifact" in verifier["evidence"]
    assert "runtime.ventureops.validation.validate_live_client_workflow_proof_artifact" in verifier["evidence"]
    assert "runtime/ventureops/live_revenue_proof.py" in verifier["evidence"]
    assert "prevents arbitrary files from satisfying the revenue prerequisite" in verifier["notes"]


def test_external_readiness_completion_audit_maps_live_delivery_proof_artifact_verifier() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    verifier = checklist["live delivery proof artifact verifier"]

    assert audit["live_delivery_proof_artifact_verifier_valid"] is True
    assert verifier["status"] == "verified"
    assert "runtime.ventureops.validation.validate_live_delivery_proof_artifact" in verifier["evidence"]
    assert "runtime/ventureops/live_revenue_proof.py" in verifier["evidence"]
    assert "prevents arbitrary delivery files from satisfying the revenue prerequisite" in verifier["notes"]


def test_external_readiness_completion_audit_maps_scope_source_path_verifier() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    verifier = checklist["scope evidence source path verifier"]

    assert audit["scope_source_path_verifier_valid"] is True
    assert verifier["status"] == "verified"
    assert "runtime.ventureops.validation.validate_scope_evidence_source_paths" in verifier["evidence"]
    assert "runtime/ventureops/live_client_readiness.py" in verifier["evidence"]
    assert "prevents missing approved read paths from being reported ready" in verifier["notes"]


def test_real_evidence_closeout_readiness_blocks_current_repo_without_real_packets() -> None:
    root = Path(__file__).resolve().parents[2]

    result = build_real_evidence_closeout_readiness(root)

    assert result["ok"] is True
    assert result["readiness_status"] == "blocked"
    assert result["ready_for_completion"] is False
    assert result["completion_decision"] == "not_complete"
    assert result["requested_handover_alias_valid"] is True
    assert result["passover_valid"] is True
    assert "live client workflow proof missing" not in result["missing_requirements"]
    assert "live revenue workflow proof missing" in result["missing_requirements"]
    assert "06_AGENTS/VentureOps-externaal-Readiness-Handover.md" in result["reviewed_surfaces"]
    assert result["live_client_workflow_proof_present"] is True
    assert result["live_revenue_workflow_proof_present"] is False
    assert result["live_external_delivery_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False
    assert result["next_required_real_use_pass"] == "ventureops-live-revenue-proof"
    assert result["next_guarded_command"] == (
        "chaseos ventureops live-revenue-proof-readiness --revenue-packet PATH --live-client-proof-path PATH --json"
    )
    assert "redacted live revenue evidence packet" in result["next_required_inputs"]
    assert result["next_required_action"] == "collect real-client scope inputs through real-client-input-manifest"
    assert "--approval-output PATH" in result["next_command"]
    assert "--scope-packet-output PATH" in result["next_command"]


def test_ventureops_real_evidence_closeout_readiness_cli_can_write_blocked_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "real-evidence-closeout.json"

    result = _run_cli_json([
        "ventureops",
        "real-evidence-closeout-readiness",
        "--vault-root",
        str(root),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert written["ready_for_completion"] is False
    assert written["readiness_status"] == "blocked"
    assert written["requested_handover_alias_valid"] is True
    assert written["next_required_real_use_pass"] == "ventureops-live-revenue-proof"
    assert written["next_guarded_command"].startswith("chaseos ventureops live-revenue-proof-readiness")
    assert "live client workflow proof missing" not in written["missing_requirements"]
    assert "live revenue workflow proof missing" in written["missing_requirements"]
    assert written["payment_mutation_performed"] is False
    assert written["revenue_claim_made"] is False


def test_real_evidence_closeout_readiness_cli_blocks_existing_report_path_without_overwrite(
    tmp_path: Path,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "real-evidence-closeout-readiness.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing real evidence closeout report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "real-evidence-closeout-readiness",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing real evidence closeout report"


def test_real_evidence_closeout_readiness_cli_blocks_escaped_report_path_without_traceback(
    tmp_path: Path,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    escaped_report_path = tmp_path / ".." / "outside-real-evidence-closeout.json"

    result = _run_cli_json(
        [
            "ventureops",
            "real-evidence-closeout-readiness",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_real_evidence_closeout_readiness_cli_write_report_defaults_to_dated_report_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "real-evidence-closeout-readiness",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-real-evidence-closeout-readiness-report.json"
    )
    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / expected).exists()


def test_real_evidence_closeout_readiness_cli_write_report_uses_collision_safe_default_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_external_readiness_audit_root(tmp_path)
    monkeypatch.chdir(tmp_path)
    base = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-real-evidence-closeout-readiness-report.json"
    )
    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-real-evidence-closeout-readiness-report-2.json"
    )
    (tmp_path / base).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / base).write_text("existing real evidence closeout report", encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "real-evidence-closeout-readiness",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--json",
    ])

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / base).read_text(encoding="utf-8") == "existing real evidence closeout report"
    assert (tmp_path / expected).exists()


def test_external_readiness_completion_audit_maps_real_evidence_closeout_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    closeout = checklist["real evidence closeout readiness CLI"]

    assert audit["real_evidence_closeout_readiness_cli_valid"] is True
    assert closeout["status"] == "verified"
    assert "runtime/ventureops/real_evidence_closeout_readiness.py" in closeout["evidence"]
    assert "chaseos ventureops real-evidence-closeout-readiness" in closeout["evidence"]
    assert "does not mark VentureOps complete" in closeout["notes"]


def test_external_readiness_completion_audit_maps_real_evidence_closeout_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["real evidence closeout report write guard"]

    assert audit["real_evidence_closeout_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "escaped report paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_real_evidence_closeout_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["real evidence closeout report dated default"]

    assert audit["real_evidence_closeout_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_real_evidence_closeout_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["real evidence closeout report default collision guard"]

    assert audit["real_evidence_closeout_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_feature_family_completion_audit_maps_goal_to_artifacts_and_blocks_external_gaps() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    assert audit["ok"] is True
    assert audit["complete"] is False
    assert audit["completion_decision"] == "not_complete"
    assert audit["objective"].startswith("Build the ChaseOS VentureOps feature family")
    assert audit["requested_handover_scope_output_route_valid"] is True
    assert "portable instance-aware workflow-pack foundation" in checklist
    assert checklist["portable instance-aware workflow-pack foundation"]["status"] == "verified"
    assert checklist["requested VentureOps-externaal handover reviewed"]["status"] == "verified"
    assert "06_AGENTS/VentureOps-externaal-Readiness-Handover.md" in checklist["requested VentureOps-externaal handover reviewed"]["evidence"]
    assert "scope output route is validated" in checklist["requested VentureOps-externaal handover reviewed"]["notes"]
    assert checklist["external live client and revenue completion"]["status"] == "blocked"
    assert "live client workflow proof missing" not in audit["missing_requirements"]
    assert "live revenue workflow proof missing" in audit["missing_requirements"]
    assert audit["next_required_real_use_pass"] == "ventureops-live-revenue-proof"
    assert audit["next_guarded_command"].startswith("chaseos ventureops live-revenue-proof-readiness")
    assert audit["external_readiness_complete"] is False
    assert audit["ready_for_goal_completion"] is False
    external_audit = audit_external_readiness_completion(root)
    assert external_audit["feature_family_completion_audit_cli_valid"] is True


def test_ventureops_feature_family_completion_audit_cli_can_write_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "feature-family-completion-audit.json"

    result = _run_cli_json([
        "ventureops",
        "feature-family-completion-audit",
        "--vault-root",
        str(root),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert written["complete"] is False
    assert written["ready_for_goal_completion"] is False
    assert "live client workflow proof missing" not in written["missing_requirements"]
    assert "live revenue workflow proof missing" in written["missing_requirements"]
    assert written["external_readiness_complete"] is False
    assert written["revenue_claim_made"] is False


def test_feature_family_completion_audit_cli_blocks_existing_report_path_without_overwrite(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "feature-family-completion-audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing feature audit report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "feature-family-completion-audit",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing feature audit report"


def test_feature_family_completion_audit_cli_blocks_escaped_report_path_without_traceback(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    escaped_report_path = tmp_path / ".." / "outside-feature-family-completion-audit.json"

    result = _run_cli_json(
        [
            "ventureops",
            "feature-family-completion-audit",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_feature_family_completion_audit_cli_write_report_defaults_to_dated_report_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_registry(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "feature-family-completion-audit",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--json",
        ],
        expected_exit=1,
    )

    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-feature-family-completion-audit-report.json"
    )
    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / expected).exists()


def test_feature_family_completion_audit_cli_write_report_uses_collision_safe_default_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_registry(tmp_path)
    monkeypatch.chdir(tmp_path)
    base = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-feature-family-completion-audit-report.json"
    )
    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-feature-family-completion-audit-report-2.json"
    )
    (tmp_path / base).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / base).write_text("existing feature audit report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "feature-family-completion-audit",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--json",
        ],
        expected_exit=1,
    )

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / base).read_text(encoding="utf-8") == "existing feature audit report"
    assert (tmp_path / expected).exists()


def test_autonomous_implementation_completion_marks_feature_implementation_complete_without_operator_evidence() -> None:
    root = Path(__file__).resolve().parents[2]

    result = build_autonomous_implementation_completion(root)

    assert result["ok"] is True
    assert result["feature_implementation_complete"] is True
    assert result["safe_to_mark_feature_implementation_complete"] is True
    assert result["operator_evidence_required_for_tests"] is False
    assert result["operator_evidence_required_for_real_world_delivery_revenue"] is True
    assert result["real_world_delivery_revenue_complete"] is False
    assert result["safe_to_mark_real_world_delivery_revenue_complete"] is False
    assert "live revenue workflow proof missing" in result["real_world_missing_requirements"]
    assert result["truth_boundary"]["external_send_performed"] is False
    assert result["truth_boundary"]["payment_mutation_performed"] is False
    assert result["truth_boundary"]["revenue_claim_made"] is False
    checks = {item["id"]: item for item in result["implementation_checks"]}
    assert checks["real_world_completion_gate_preserved"]["ok"] is True
    assert checks["studio_dashboard_panel_registered"]["ok"] is True
    assert checks["studio_dashboard_app_renders_real_use_panel"]["ok"] is True
    assert checks["native_studio_dashboard_renders_real_use_panel"]["ok"] is True
    assert checks["studio_real_world_usecase_guide_present"]["ok"] is True


def test_ventureops_autonomous_implementation_completion_cli_can_write_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    report_path = tmp_path / "autonomous-implementation-completion.json"

    result = _run_cli_json([
        "ventureops",
        "autonomous-implementation-completion",
        "--vault-root",
        str(root),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert written["feature_implementation_complete"] is True
    assert written["operator_evidence_required_for_tests"] is False
    assert written["safe_to_mark_real_world_delivery_revenue_complete"] is False


def test_autonomous_implementation_completion_cli_blocks_existing_report_path_without_overwrite(
    tmp_path: Path,
) -> None:
    _seed_registry(tmp_path)
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "autonomous-implementation-completion.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing autonomous implementation report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "autonomous-implementation-completion",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing autonomous implementation report"


def test_autonomous_implementation_completion_cli_blocks_escaped_report_path_without_traceback(
    tmp_path: Path,
) -> None:
    _seed_registry(tmp_path)
    escaped_report_path = tmp_path / ".." / "outside-autonomous-implementation-completion.json"

    result = _run_cli_json(
        [
            "ventureops",
            "autonomous-implementation-completion",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_autonomous_implementation_completion_cli_write_report_defaults_to_dated_report_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_registry(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "autonomous-implementation-completion",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--json",
        ]
    )

    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-autonomous-implementation-completion-report.json"
    )
    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / expected).exists()


def test_autonomous_implementation_completion_cli_write_report_uses_collision_safe_default_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _seed_registry(tmp_path)
    monkeypatch.chdir(tmp_path)
    base = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-autonomous-implementation-completion-report.json"
    )
    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-autonomous-implementation-completion-report-2.json"
    )
    (tmp_path / base).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / base).write_text("existing autonomous implementation report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "autonomous-implementation-completion",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--json",
        ]
    )

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / base).read_text(encoding="utf-8") == "existing autonomous implementation report"
    assert (tmp_path / expected).exists()


def test_ventureops_evidence_discovery_preflight_routes_current_repo_to_revenue_handoff() -> None:
    root = Path(__file__).resolve().parents[2]

    result = build_evidence_discovery_preflight(root)

    assert result["ok"] is True
    assert result["discovery_status"] == "internal_workflow_proof_closed_revenue_deferred"
    assert result["selected_revenue_packet_path"] is None
    assert result["selected_live_client_workflow_proof_path"] is not None
    assert result["selected_internal_closeout_path"] is not None
    assert result["template_only_candidate_count"] >= 2
    assert result["next_required_action"] == "no revenue evidence required for internal closeout"
    assert "future real-world VentureOps use case" in result["next_command"]
    assert result["internal_workflow_proof_closed"] is True
    assert result["live_revenue_deferred"] is True
    assert result["revenue_evidence_required_for_closeout"] is False
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_revenue_proof_performed"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_ventureops_evidence_discovery_preflight_selects_valid_scope_packet(tmp_path: Path) -> None:
    scope_packet = _write_valid_scope_packet(tmp_path)

    result = build_evidence_discovery_preflight(tmp_path)

    assert result["ok"] is True
    assert result["discovery_status"] == "ready_for_live_client_workflow_proof"
    assert result["selected_scope_packet_path"] == str(scope_packet.relative_to(tmp_path)).replace("\\", "/")
    assert result["ready_for_live_client_workflow_proof"] is True
    assert result["ready_for_live_revenue_proof"] is False
    assert result["next_required_action"] == "run live-client-workflow-proof with --execute-proof"
    assert "live-client-workflow-proof" in result["next_command"]
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_revenue_proof_performed"] is False


def test_ventureops_evidence_discovery_preflight_routes_live_client_proof_to_revenue_handoff(
    tmp_path: Path,
) -> None:
    scope_packet = _write_valid_scope_packet(tmp_path)
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))

    result = build_evidence_discovery_preflight(tmp_path)

    assert result["ok"] is True
    assert result["selected_scope_packet_path"] == str(scope_packet.relative_to(tmp_path)).replace("\\", "/")
    assert result["selected_live_client_workflow_proof_path"] == str(
        live_client_proof.relative_to(tmp_path)
    ).replace("\\", "/")
    assert result["selected_revenue_packet_path"] is None
    assert result["ready_for_live_client_workflow_proof"] is True
    assert result["ready_for_live_revenue_proof"] is False
    assert result["discovery_status"] == "ready_for_revenue_evidence"
    assert result["next_required_action"] == "provide valid live revenue evidence with redacted receipt and delivery proof"
    assert "evidence-template --kind revenue" in result["next_command"]
    assert "valid live revenue evidence packet with receipt and delivery proof missing" in result["blockers"]
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_revenue_proof_performed"] is False


def test_ventureops_evidence_discovery_preflight_respects_internal_closeout_artifact(
    tmp_path: Path,
) -> None:
    _write_valid_scope_packet(tmp_path)
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    closeout_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-internal-closeout.json"
    _write(
        closeout_path,
        json.dumps(
            {
                "type": "ventureops-internal-workflow-proof-closeout",
                "workflow_id": "agent_runtime_governance_audit",
                "workflow_alias": "ventureops_ai_runtime_security_audit",
                "client_label": "Client Alpha",
                "live_client_workflow_proof_path": str(live_client_proof.relative_to(tmp_path)).replace("\\", "/"),
                "internal_workflow_proof_closed": True,
                "live_revenue_deferred": True,
                "revenue_evidence_required_for_closeout": False,
            },
            indent=2,
        ),
    )

    result = build_evidence_discovery_preflight(tmp_path)

    assert result["ok"] is True
    assert result["discovery_status"] == "internal_workflow_proof_closed_revenue_deferred"
    assert result["selected_internal_closeout_path"] == str(closeout_path.relative_to(tmp_path)).replace("\\", "/")
    assert result["internal_workflow_proof_closed"] is True
    assert result["live_revenue_deferred"] is True
    assert result["revenue_evidence_required_for_closeout"] is False
    assert result["next_required_action"] == "no revenue evidence required for internal closeout"
    assert "valid live revenue evidence packet with receipt and delivery proof missing" not in result["blockers"]


def test_ventureops_evidence_discovery_preflight_classifies_scope_gate_as_insufficient_for_revenue(tmp_path: Path) -> None:
    scope_gate_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-scope-gate.json"
    _write(scope_gate_path, json.dumps(_valid_live_client_scope_proof_artifact(), indent=2))

    result = build_evidence_discovery_preflight(tmp_path)

    assert result["ok"] is True
    assert result["scope_gate_only_candidate_count"] == 1
    assert result["selected_live_client_workflow_proof_path"] is None
    assert result["ready_for_live_revenue_proof"] is False
    assert result["discovery_status"] == "blocked_no_real_evidence_found"
    assert any(
        candidate["classification"] == "scope_gate_only_insufficient_for_revenue"
        for candidate in result["insufficient_live_client_artifacts"]
    )


def test_ventureops_evidence_discovery_preflight_rejects_invalid_delivery_proof_for_revenue(
    tmp_path: Path,
) -> None:
    _write_valid_revenue_proof_fixture(tmp_path)
    delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    delivery.write_text(json.dumps({"redacted": True, "delivery_status": "delivered"}, indent=2), encoding="utf-8")

    result = build_evidence_discovery_preflight(tmp_path)
    revenue_candidate = next(
        candidate for candidate in result["revenue_candidates"] if candidate["classification"] == "live_revenue_evidence"
    )

    assert revenue_candidate["delivery_proof_artifact_present"] is True
    assert revenue_candidate["delivery_proof_artifact_valid"] is False
    assert result["selected_live_client_workflow_proof_path"] is not None
    assert result["selected_revenue_packet_path"] is None
    assert result["ready_for_live_revenue_proof"] is False
    assert result["discovery_status"] == "ready_for_revenue_evidence"
    assert result["next_required_action"] == "provide valid live revenue evidence with redacted receipt and delivery proof"


def test_ventureops_evidence_discovery_preflight_cli_can_write_report(tmp_path: Path) -> None:
    scope_packet = _write_valid_scope_packet(tmp_path)
    report_path = tmp_path / "discovery-preflight.json"

    result = _run_cli_json([
        "ventureops",
        "evidence-discovery-preflight",
        "--vault-root",
        str(tmp_path),
        "--write-report",
        "--report-path",
        str(report_path),
        "--json",
    ])

    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert result["report_written"] is True
    assert result["report_path"] == str(report_path)
    assert written["selected_scope_packet_path"] == str(scope_packet.relative_to(tmp_path)).replace("\\", "/")
    assert written["discovery_status"] == "ready_for_live_client_workflow_proof"
    assert written["payment_mutation_performed"] is False
    assert written["revenue_claim_made"] is False


def test_external_readiness_completion_audit_maps_evidence_discovery_preflight_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    discovery = checklist["evidence discovery preflight CLI"]

    assert audit["evidence_discovery_preflight_cli_valid"] is True
    assert discovery["status"] == "verified"
    assert "runtime/ventureops/evidence_discovery_preflight.py" in discovery["evidence"]
    assert "chaseos ventureops evidence-discovery-preflight" in discovery["evidence"]
    assert "does not execute live workflows" in discovery["notes"]


def test_scope_evidence_packet_builder_requires_operator_approval_and_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md"
    _write(source, "redacted client scope\n")

    result = build_scope_evidence_packet(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approval_id="operator-approval-client-alpha-005",
        approval_artifact_path="03_INPUTS/client-alpha/approval.md",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json",
        operator_approved=False,
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert "operator approval flag required" in result["errors"]
    assert "approval artifact missing: 03_INPUTS/client-alpha/approval.md" in result["errors"]
    assert result["live_client_workflow_proof_performed"] is False
    assert result["external_send_performed"] is False
    assert result["revenue_claim_made"] is False


def test_validate_real_client_scope_approval_artifact_accepts_safe_operator_approval() -> None:
    artifact = {
        "type": "ventureops-real-client-scope-approval",
        "approval_id": "operator-approval-client-alpha-005",
        "client_label": "Client Alpha",
        "client_approved_scope_id": "scope-client-alpha-005",
        "approval_status": "approved",
        "approval_decision": "approved",
        "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
        "redaction_policy": "client_safe_summary_only",
        "delivery_boundary": "no_external_delivery",
        "operator_attested_scope_approved": True,
        "external_send_authorized": False,
        "payment_mutation_authorized": False,
        "crm_mutation_authorized": False,
        "provider_calls_authorized": False,
        "browser_actions_authorized": False,
        "revenue_claim_authorized": False,
    }

    validation = validate_real_client_scope_approval_artifact(artifact)

    assert validation["ok"] is True
    assert validation["approval_id"] == "operator-approval-client-alpha-005"
    assert validation["safe_read_paths"] == ["03_INPUTS/client-alpha/redacted-brief.md"]


def test_validate_real_client_scope_approval_artifact_rejects_template_or_side_effect_authority() -> None:
    artifact = {
        "type": "ventureops-real-client-scope-approval",
        "template_only": True,
        "approval_id": "operator-approval-client-alpha-005",
        "client_label": "Client Alpha",
        "client_approved_scope_id": "scope-client-alpha-005",
        "approval_status": "approved",
        "approval_decision": "approved",
        "approved_read_paths": [".env", "../outside.md"],
        "redaction_policy": "raw_client_data_allowed",
        "delivery_boundary": "external_send_allowed",
        "operator_attested_scope_approved": False,
        "external_send_authorized": True,
        "payment_mutation_authorized": True,
        "crm_mutation_authorized": True,
        "provider_calls_authorized": True,
        "browser_actions_authorized": True,
        "revenue_claim_authorized": True,
    }

    validation = validate_real_client_scope_approval_artifact(artifact)

    assert validation["ok"] is False
    assert "template_only scope approval cannot be used as real client approval" in validation["errors"]
    assert "operator_attested_scope_approved must be true" in validation["errors"]
    assert "approved_read_paths contains unsafe path: .env" in validation["errors"]
    assert "external_send_authorized must be false for scope approval" in validation["errors"]
    assert "revenue_claim_authorized must be false for scope approval" in validation["errors"]


def test_scope_approval_packet_builder_writes_valid_no_side_effect_artifact(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")

    result = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-005",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )

    artifact = json.loads((tmp_path / result["approval_artifact_path"]).read_text(encoding="utf-8"))
    validation = validate_real_client_scope_approval_artifact(artifact)

    assert result["ok"] is True
    assert result["approval_artifact_written"] is True
    assert artifact["type"] == "ventureops-real-client-scope-approval"
    assert artifact["approval_status"] == "approved"
    assert validation["ok"] is True
    assert result["scope_sources_valid"] is True
    assert result["external_send_authorized"] is False
    assert result["payment_mutation_authorized"] is False
    assert result["crm_mutation_authorized"] is False
    assert result["provider_calls_authorized"] is False
    assert result["browser_actions_authorized"] is False
    assert result["revenue_claim_authorized"] is False


def test_scope_evidence_packet_builder_rejects_arbitrary_approval_file(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "approval.md", "approved redacted scope\n")
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")

    result = build_scope_evidence_packet(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approval_id="operator-approval-client-alpha-005",
        approval_artifact_path="03_INPUTS/client-alpha/approval.md",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json",
        operator_approved=True,
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert "scope approval artifact invalid" in result["errors"]
    assert result["scope_approval_artifact_valid"] is False
    assert result["live_client_workflow_proof_performed"] is False


def test_scope_evidence_packet_builder_writes_valid_packet_with_existing_sources(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")
    approval = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-005",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )

    result = build_scope_evidence_packet(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approval_id="operator-approval-client-alpha-005",
        approval_artifact_path=str(approval["approval_artifact_path"]),
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json",
        operator_approved=True,
    )

    packet = json.loads((tmp_path / result["packet_path"]).read_text(encoding="utf-8"))
    validation = validate_real_client_scope_evidence(packet)
    source_validation = validate_scope_evidence_source_paths(tmp_path, validation["safe_read_paths"])

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert packet["type"] == "ventureops-real-client-scope-evidence"
    assert packet["approval_status"] == "approved"
    assert packet["approval_artifact_path"] == "03_INPUTS/client-alpha/scope-approval.json"
    assert "template_only" not in packet
    assert validation["ok"] is True
    assert source_validation["ok"] is True
    assert result["scope_approval_artifact_valid"] is True
    assert result["next_command"].startswith("chaseos ventureops live-client-workflow-proof")
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_external_delivery_performed"] is False


def test_scope_evidence_packet_builder_cli_can_write_packet(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")
    approval = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-005",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )
    output_path = tmp_path / "runtime" / "ventureops" / "fixtures" / "scope-evidence" / "client-alpha-scope.json"

    result = _run_cli_json([
        "ventureops",
        "scope-evidence-packet",
        "--vault-root",
        str(tmp_path),
        "--client-label",
        "Client Alpha",
        "--scope-id",
        "scope-client-alpha-005",
        "--approval-id",
        "operator-approval-client-alpha-005",
        "--approval-artifact-path",
        str(approval["approval_artifact_path"]),
        "--approved-read-path",
        "03_INPUTS/client-alpha/redacted-brief.md",
        "--output",
        str(output_path),
        "--operator-approved",
        "--json",
    ])

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert result["packet_path"] == str(output_path.relative_to(tmp_path)).replace("\\", "/")
    assert result["scope_evidence_valid"] is True
    assert result["scope_sources_valid"] is True
    assert result["scope_approval_artifact_valid"] is True
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_scope_approval_packet_builder_cli_can_write_artifact(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")
    output_path = tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"

    result = _run_cli_json([
        "ventureops",
        "scope-approval-packet",
        "--vault-root",
        str(tmp_path),
        "--approval-id",
        "operator-approval-client-alpha-005",
        "--client-label",
        "Client Alpha",
        "--scope-id",
        "scope-client-alpha-005",
        "--approved-read-path",
        "03_INPUTS/client-alpha/redacted-brief.md",
        "--output",
        str(output_path),
        "--operator-approved",
        "--operator-attested-scope-approved",
        "--json",
    ])

    assert result["ok"] is True
    assert result["approval_artifact_written"] is True
    assert result["approval_artifact_path"] == str(output_path.relative_to(tmp_path)).replace("\\", "/")
    assert result["scope_approval_artifact_valid"] is True
    assert result["external_send_authorized"] is False
    assert result["revenue_claim_authorized"] is False


def test_external_readiness_completion_audit_maps_scope_evidence_packet_builder_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    builder = checklist["scope evidence packet builder CLI"]

    assert audit["scope_evidence_packet_builder_cli_valid"] is True
    assert builder["status"] == "verified"
    assert "runtime/ventureops/scope_evidence_packet_builder.py" in builder["evidence"]
    assert "chaseos ventureops scope-evidence-packet" in builder["evidence"]
    assert "does not run live workflows" in builder["notes"]


def test_external_readiness_completion_audit_maps_scope_approval_packet_builder_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    contract = checklist["real client scope approval artifact contract"]
    builder = checklist["scope approval packet builder CLI"]

    assert audit["scope_approval_contract_verified"] is True
    assert audit["scope_approval_packet_builder_cli_valid"] is True
    assert contract["status"] == "verified"
    assert builder["status"] == "verified"
    assert "runtime/ventureops/scope_approval_packet_builder.py" in builder["evidence"]
    assert "chaseos ventureops scope-approval-packet" in builder["evidence"]
    assert "does not run live workflows" in builder["notes"]


def test_revenue_evidence_packet_builder_requires_operator_approval_receipts_and_live_client_proof(
    tmp_path: Path,
) -> None:
    delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    _write(delivery, json.dumps({"redacted": True, "delivery_status": "delivered"}))

    result = build_revenue_evidence_packet(
        tmp_path,
        revenue_proof_id="revenue-client-alpha-006",
        client_label="Client Alpha",
        payment_reference_id="pay_ref_redacted_alpha_006",
        payment_status="received",
        amount="250.00",
        currency="USD",
        receipt_artifact_path="07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
        delivery_proof_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        crm_reference_id="crm_ref_redacted_alpha_006",
        approval_id="operator-approval-client-alpha-revenue-006",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path="runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json",
        operator_approved=False,
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert "operator approval flag required" in result["errors"]
    assert "receipt artifact missing: 07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json" in result["errors"]
    assert (
        "live client proof artifact missing: 07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
        in result["errors"]
    )
    assert result["revenue_evidence_valid"] is False
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["invoice_sent"] is False
    assert result["revenue_claim_made"] is False


def test_delivery_proof_packet_builder_requires_operator_attestation_and_live_client_proof(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json",
        json.dumps(_valid_client_safe_delivery_artifact(), indent=2),
    )

    result = build_delivery_proof_packet(
        tmp_path,
        delivery_proof_id="delivery-client-alpha-008",
        client_label="Client Alpha",
        delivery_reference_id="delivery_ref_redacted_alpha_007",
        client_safe_delivery_artifact_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        operator_approved=False,
        operator_attested_delivery_performed=False,
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert "operator approval flag required" in result["errors"]
    assert "operator delivery attestation required" in result["errors"]
    assert (
        "live client proof artifact missing: 07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
        in result["errors"]
    )
    assert result["external_send_performed_by_chaseos"] is False
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["invoice_sent"] is False
    assert result["revenue_claim_made"] is False


def test_delivery_proof_packet_builder_writes_valid_operator_attested_artifact(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json",
        json.dumps(_valid_client_safe_delivery_artifact(), indent=2),
    )
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json",
        json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2),
    )

    result = build_delivery_proof_packet(
        tmp_path,
        delivery_proof_id="delivery-client-alpha-008",
        client_label="Client Alpha",
        delivery_reference_id="delivery_ref_redacted_alpha_007",
        client_safe_delivery_artifact_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        operator_approved=True,
        operator_attested_delivery_performed=True,
    )

    packet = json.loads((tmp_path / result["packet_path"]).read_text(encoding="utf-8"))
    validation = validate_live_delivery_proof_artifact(packet)

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert packet["type"] == "ventureops-live-delivery-proof"
    assert packet["status"] == "operator_attested_delivery_recorded"
    assert packet["delivery_status"] == "delivered"
    assert packet["client_safe_delivery_artifact_path"] == "07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json"
    assert packet["live_client_proof_path"] == "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    assert validation["ok"] is True
    assert result["delivery_proof_artifact_valid"] is True
    assert result["live_client_proof_artifact_valid"] is True
    assert result["next_command"].startswith("chaseos ventureops revenue-evidence-packet")
    assert result["external_send_performed_by_chaseos"] is False
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["invoice_sent"] is False
    assert result["revenue_claim_made"] is False


def test_delivery_proof_packet_builder_rejects_invalid_client_safe_delivery_artifact(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json",
        json.dumps({"redacted": False}, indent=2),
    )
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json",
        json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2),
    )

    result = build_delivery_proof_packet(
        tmp_path,
        delivery_proof_id="delivery-client-alpha-008",
        client_label="Client Alpha",
        delivery_reference_id="delivery_ref_redacted_alpha_007",
        client_safe_delivery_artifact_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        operator_approved=True,
        operator_attested_delivery_performed=True,
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert result["delivery_proof_artifact_valid"] is False
    assert "client-safe delivery artifact invalid" in result["errors"]
    assert "redacted must be true" in result["client_safe_delivery_artifact_validation"]["errors"]
    assert result["external_send_performed_by_chaseos"] is False
    assert result["revenue_claim_made"] is False


def test_revenue_evidence_packet_builder_writes_valid_packet_with_existing_artifacts(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-receipt-redacted.json", "{}\n")
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json",
        json.dumps(_valid_live_delivery_proof_artifact(), indent=2),
    )
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json",
        json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2),
    )

    result = build_revenue_evidence_packet(
        tmp_path,
        revenue_proof_id="revenue-client-alpha-006",
        client_label="Client Alpha",
        payment_reference_id="pay_ref_redacted_alpha_006",
        payment_status="received",
        amount="250.00",
        currency="USD",
        receipt_artifact_path="07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
        delivery_proof_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        crm_reference_id="crm_ref_redacted_alpha_006",
        approval_id="operator-approval-client-alpha-revenue-006",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path="runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json",
        operator_approved=True,
    )

    packet = json.loads((tmp_path / result["packet_path"]).read_text(encoding="utf-8"))
    validation = validate_live_revenue_evidence(packet)
    live_client_validation = validate_live_client_workflow_proof_artifact(
        json.loads((tmp_path / result["live_client_proof_path"]).read_text(encoding="utf-8"))
    )

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert packet["type"] == "ventureops-live-revenue-evidence"
    assert packet["payment_status"] == "received"
    assert packet["amount"] == 250.0
    assert packet["receipt_artifact_path"] == "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json"
    assert packet["delivery_proof_path"] == "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json"
    assert "template_only" not in packet
    assert validation["ok"] is True
    assert live_client_validation["ok"] is True
    assert result["revenue_evidence_valid"] is True
    assert result["live_client_proof_artifact_valid"] is True
    assert result["delivery_proof_artifact_valid"] is True
    assert result["next_command"].startswith("chaseos ventureops live-revenue-proof")
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["invoice_sent"] is False
    assert result["revenue_claim_made"] is False


def test_revenue_evidence_packet_builder_rejects_invalid_delivery_proof(tmp_path: Path) -> None:
    _write(tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-receipt-redacted.json", "{}\n")
    _write(tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json", "{}\n")
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json",
        json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2),
    )

    result = build_revenue_evidence_packet(
        tmp_path,
        revenue_proof_id="revenue-client-alpha-006",
        client_label="Client Alpha",
        payment_reference_id="pay_ref_redacted_alpha_006",
        payment_status="received",
        amount="250.00",
        currency="USD",
        receipt_artifact_path="07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
        delivery_proof_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
        crm_reference_id="crm_ref_redacted_alpha_006",
        approval_id="operator-approval-client-alpha-revenue-006",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path="runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json",
        operator_approved=True,
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert result["delivery_proof_artifact_valid"] is False
    assert "delivery proof artifact invalid" in result["errors"]
    assert "type must be ventureops-live-delivery-proof" in result["delivery_proof_validation"]["errors"]
    assert result["revenue_claim_made"] is False


def test_revenue_evidence_packet_builder_cli_can_write_packet(tmp_path: Path) -> None:
    receipt = tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-receipt-redacted.json"
    delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    output_path = tmp_path / "runtime" / "ventureops" / "fixtures" / "revenue-evidence" / "client-alpha-revenue.json"
    _write(receipt, "{}\n")
    _write(delivery, json.dumps(_valid_live_delivery_proof_artifact(), indent=2))
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))

    result = _run_cli_json([
        "ventureops",
        "revenue-evidence-packet",
        "--vault-root",
        str(tmp_path),
        "--revenue-proof-id",
        "revenue-client-alpha-006",
        "--client-label",
        "Client Alpha",
        "--payment-reference-id",
        "pay_ref_redacted_alpha_006",
        "--payment-status",
        "received",
        "--amount",
        "250.00",
        "--currency",
        "USD",
        "--receipt-artifact-path",
        str(receipt),
        "--delivery-proof-path",
        str(delivery),
        "--crm-reference-id",
        "crm_ref_redacted_alpha_006",
        "--approval-id",
        "operator-approval-client-alpha-revenue-006",
        "--live-client-proof-path",
        str(live_client_proof),
        "--output",
        str(output_path),
        "--operator-approved",
        "--json",
    ])

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert result["packet_path"] == str(output_path.relative_to(tmp_path)).replace("\\", "/")
    assert result["revenue_evidence_valid"] is True
    assert result["live_client_proof_artifact_valid"] is True
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_ventureops_external_packet_builders_reject_existing_output_paths(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "redacted-brief.md", "redacted client scope\n")
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json",
        json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2),
    )
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json",
        json.dumps(_valid_client_safe_delivery_artifact(), indent=2),
    )
    _write(tmp_path / "07_LOGS" / "Revenue-Proofs" / "client-alpha-receipt-redacted.json", "{}\n")

    existing_approval = tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"
    existing_scope = tmp_path / "runtime" / "ventureops" / "fixtures" / "scope-evidence" / "client-alpha-scope.json"
    existing_delivery = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    existing_revenue = tmp_path / "runtime" / "ventureops" / "fixtures" / "revenue-evidence" / "client-alpha-revenue.json"
    sentinel = '{"existing": true}\n'
    for path in [existing_approval, existing_scope, existing_delivery, existing_revenue]:
        _write(path, sentinel)

    approval_collision = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-005",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path=str(existing_approval),
        operator_approved=True,
        operator_attested_scope_approved=True,
    )

    approval = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-005",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path="03_INPUTS/client-alpha/scope-approval-new.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )
    scope_collision = build_scope_evidence_packet(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approval_id="operator-approval-client-alpha-005",
        approval_artifact_path=str(approval["approval_artifact_path"]),
        approved_read_paths=["03_INPUTS/client-alpha/redacted-brief.md"],
        output_path=str(existing_scope),
        operator_approved=True,
    )
    delivery_collision = build_delivery_proof_packet(
        tmp_path,
        delivery_proof_id="delivery-client-alpha-008",
        client_label="Client Alpha",
        delivery_reference_id="delivery_ref_redacted_alpha_007",
        client_safe_delivery_artifact_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-redacted.json",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path=str(existing_delivery),
        operator_approved=True,
        operator_attested_delivery_performed=True,
    )
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof-valid.json",
        json.dumps(_valid_live_delivery_proof_artifact(), indent=2),
    )
    revenue_collision = build_revenue_evidence_packet(
        tmp_path,
        revenue_proof_id="revenue-client-alpha-006",
        client_label="Client Alpha",
        payment_reference_id="pay_ref_redacted_alpha_006",
        payment_status="received",
        amount="250.00",
        currency="USD",
        receipt_artifact_path="07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
        delivery_proof_path="07_LOGS/Workflow-Proofs/client-alpha-delivery-proof-valid.json",
        crm_reference_id="crm_ref_redacted_alpha_006",
        approval_id="operator-approval-client-alpha-revenue-006",
        live_client_proof_path="07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
        output_path=str(existing_revenue),
        operator_approved=True,
    )

    assert approval_collision["ok"] is False
    assert approval_collision["approval_artifact_written"] is False
    assert scope_collision["ok"] is False
    assert scope_collision["packet_written"] is False
    assert delivery_collision["ok"] is False
    assert delivery_collision["packet_written"] is False
    assert revenue_collision["ok"] is False
    assert revenue_collision["packet_written"] is False
    for result in [approval_collision, scope_collision, delivery_collision, revenue_collision]:
        assert any("output path already exists:" in error for error in result["errors"])
    for path in [existing_approval, existing_scope, existing_delivery, existing_revenue]:
        assert path.read_text(encoding="utf-8") == sentinel


def test_ventureops_external_packet_builders_block_escaped_paths_without_exception(tmp_path: Path) -> None:
    approval_result = build_scope_approval_packet(
        tmp_path,
        approval_id="operator-approval-client-alpha-005",
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approved_read_paths=["../outside-source.md"],
        output_path="../outside-approval.json",
        operator_approved=True,
        operator_attested_scope_approved=True,
    )

    scope_result = build_scope_evidence_packet(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-005",
        approval_id="operator-approval-client-alpha-005",
        approval_artifact_path="../outside-approval.json",
        approved_read_paths=["../outside-source.md"],
        output_path="../outside-scope.json",
        operator_approved=True,
    )

    delivery_result = build_delivery_proof_packet(
        tmp_path,
        delivery_proof_id="delivery-client-alpha-008",
        client_label="Client Alpha",
        delivery_reference_id="delivery_ref_redacted_alpha_008",
        client_safe_delivery_artifact_path="../outside-delivery.md",
        live_client_proof_path="../outside-live-client.json",
        output_path="../outside-delivery-proof.json",
        operator_approved=True,
        operator_attested_delivery_performed=True,
    )

    revenue_result = build_revenue_evidence_packet(
        tmp_path,
        revenue_proof_id="revenue-client-alpha-006",
        client_label="Client Alpha",
        payment_reference_id="pay_ref_redacted_alpha_006",
        payment_status="received",
        amount="250.00",
        currency="USD",
        receipt_artifact_path="../outside-receipt.json",
        delivery_proof_path="../outside-delivery-proof.json",
        crm_reference_id="crm_ref_redacted_alpha_006",
        approval_id="operator-approval-client-alpha-revenue-006",
        live_client_proof_path="../outside-live-client.json",
        output_path="../outside-revenue.json",
        operator_approved=True,
    )

    assert approval_result["ok"] is False
    assert approval_result["approval_artifact_written"] is False
    assert any("approved_read_paths escapes vault root" in error for error in approval_result["errors"])
    assert any("output_path escapes vault root" in error for error in approval_result["errors"])
    assert approval_result["external_send_authorized"] is False
    assert approval_result["revenue_claim_authorized"] is False

    for result in [scope_result, delivery_result, revenue_result]:
        assert result["ok"] is False
        assert result["packet_written"] is False
        assert any("escapes vault root" in error for error in result["errors"])
        assert result["payment_mutation_performed"] is False
        assert result["revenue_claim_made"] is False


def test_delivery_proof_packet_builder_cli_can_write_artifact(tmp_path: Path) -> None:
    delivery_artifact = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json"
    live_client_proof = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    output_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    _write(delivery_artifact, json.dumps(_valid_client_safe_delivery_artifact(), indent=2))
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))

    result = _run_cli_json([
        "ventureops",
        "delivery-proof-packet",
        "--vault-root",
        str(tmp_path),
        "--delivery-proof-id",
        "delivery-client-alpha-008",
        "--client-label",
        "Client Alpha",
        "--delivery-reference-id",
        "delivery_ref_redacted_alpha_007",
        "--client-safe-delivery-artifact-path",
        str(delivery_artifact),
        "--live-client-proof-path",
        str(live_client_proof),
        "--output",
        str(output_path),
        "--operator-approved",
        "--operator-attested-delivery-performed",
        "--json",
    ])

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert result["packet_path"] == str(output_path.relative_to(tmp_path)).replace("\\", "/")
    assert result["delivery_proof_artifact_valid"] is True
    assert result["live_client_proof_artifact_valid"] is True
    assert result["external_send_performed_by_chaseos"] is False
    assert result["payment_mutation_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_external_readiness_completion_audit_maps_revenue_evidence_packet_builder_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    builder = checklist["revenue evidence packet builder CLI"]

    assert audit["revenue_evidence_packet_builder_cli_valid"] is True
    assert builder["status"] == "verified"
    assert "runtime/ventureops/revenue_evidence_packet_builder.py" in builder["evidence"]
    assert "chaseos ventureops revenue-evidence-packet" in builder["evidence"]
    assert "does not run live workflows" in builder["notes"]


def test_external_readiness_completion_audit_maps_packet_output_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["external packet output collision guard"]

    assert audit["external_packet_output_collision_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/scope_approval_packet_builder.py" in guard["evidence"]
    assert "runtime/ventureops/scope_evidence_packet_builder.py" in guard["evidence"]
    assert "runtime/ventureops/delivery_proof_packet_builder.py" in guard["evidence"]
    assert "runtime/ventureops/revenue_evidence_packet_builder.py" in guard["evidence"]
    assert "existing output paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_external_packet_path_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["external packet path guard"]

    assert audit["external_packet_path_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/scope_approval_packet_builder.py" in guard["evidence"]
    assert "runtime/ventureops/scope_evidence_packet_builder.py" in guard["evidence"]
    assert "runtime/ventureops/delivery_proof_packet_builder.py" in guard["evidence"]
    assert "runtime/ventureops/revenue_evidence_packet_builder.py" in guard["evidence"]
    assert "escaped" in guard["notes"]


def test_external_readiness_completion_audit_maps_proof_output_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["guarded proof output collision guard"]

    assert audit["guarded_proof_output_collision_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/live_client_scope_proof.py" in guard["evidence"]
    assert "runtime/ventureops/live_client_workflow_proof.py" in guard["evidence"]
    assert "runtime/ventureops/live_revenue_proof.py" in guard["evidence"]
    assert "proof output paths" in guard["notes"]


def test_final_external_execution_runbook_includes_delivery_proof_packet_builder() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = {step["stage"]: step for step in runbook["command_sequence"]}

    builder = stages["delivery proof packet authoring"]

    assert "chaseos ventureops delivery-proof-packet" in builder["command"]
    assert "valid live-client workflow proof artifact" in builder["required_before"]
    assert "client-safe delivery artifact" in builder["required_before"]
    assert "operator-selected delivery proof artifact path" in builder["writes"]
    assert "does not perform external delivery" in builder["notes"]


def test_final_external_execution_runbook_includes_scope_approval_packet_builder() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = {step["stage"]: step for step in runbook["command_sequence"]}

    builder = stages["scope approval artifact authoring"]

    assert "typed real-client scope approval artifact" in runbook["required_operator_inputs"]
    assert "chaseos ventureops scope-approval-packet" in builder["command"]
    assert "approved source files inside the vault root" in builder["required_before"]
    assert "operator-selected scope approval artifact path" in builder["writes"]
    assert "does not run live workflows" in builder["notes"]


def test_real_client_input_manifest_blocks_without_required_scope_inputs(tmp_path: Path) -> None:
    manifest = build_real_client_input_manifest(tmp_path)

    assert manifest["ok"] is True
    assert manifest["manifest_status"] == "blocked_missing_real_client_inputs"
    assert manifest["ready_to_author_scope_approval"] is False
    assert manifest["ready_to_author_scope_packet"] is False
    assert manifest["ready_for_live_client_workflow_proof"] is False
    assert "client_label" in manifest["missing_inputs"]
    assert "approved_read_paths" in manifest["missing_inputs"]
    assert manifest["next_command"].startswith("chaseos ventureops scope-approval-packet")
    assert manifest["live_client_workflow_proof_performed"] is False
    assert manifest["live_client_data_ingested"] is False


def test_real_client_input_manifest_recommends_scope_approval_packet_with_existing_sources(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "source.md", "approved source\n")

    manifest = build_real_client_input_manifest(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-001",
        approval_id="operator-real-client-scope-approval-001",
        approved_read_paths=["03_INPUTS/client-alpha/source.md"],
        approval_output_path="03_INPUTS/client-alpha/scope-approval.json",
    )

    assert manifest["manifest_status"] == "ready_to_author_scope_approval"
    assert manifest["ready_to_author_scope_approval"] is True
    assert manifest["ready_to_author_scope_packet"] is False
    assert manifest["source_paths_valid"] is True
    assert manifest["next_command"].startswith("chaseos ventureops scope-approval-packet")
    assert "--approved-read-path 03_INPUTS/client-alpha/source.md" in manifest["next_command"]
    assert "--output 03_INPUTS/client-alpha/scope-approval.json" in manifest["next_command"]


def test_real_client_input_manifest_blocks_scope_approval_without_output_path(tmp_path: Path) -> None:
    _write(tmp_path / "03_INPUTS" / "client-alpha" / "source.md", "approved source\n")

    manifest = build_real_client_input_manifest(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-001",
        approval_id="operator-real-client-scope-approval-001",
        approved_read_paths=["03_INPUTS/client-alpha/source.md"],
    )

    assert manifest["manifest_status"] == "blocked_missing_real_client_inputs"
    assert manifest["ready_to_author_scope_approval"] is False
    assert "approval_output_path or approval_artifact_path" in manifest["missing_inputs"]
    assert "--output PATH" in manifest["next_command"]
    assert manifest["live_client_workflow_proof_performed"] is False


def test_real_client_input_manifest_blocks_escaped_future_output_paths(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    approval_artifact = tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"
    _write(source, "approved source\n")
    _write(
        approval_artifact,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-real-client-scope-approval-001",
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-001",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": ["03_INPUTS/client-alpha/source.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
                "operator_attested_scope_approved": True,
                "external_send_authorized": False,
                "payment_mutation_authorized": False,
                "crm_mutation_authorized": False,
                "provider_calls_authorized": False,
                "browser_actions_authorized": False,
                "revenue_claim_authorized": False,
            },
            indent=2,
        ),
    )

    approval_manifest = build_real_client_input_manifest(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-001",
        approval_id="operator-real-client-scope-approval-001",
        approved_read_paths=["03_INPUTS/client-alpha/source.md"],
        approval_output_path="../outside-approval.json",
    )
    scope_manifest = build_real_client_input_manifest(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-001",
        approval_id="operator-real-client-scope-approval-001",
        approved_read_paths=["03_INPUTS/client-alpha/source.md"],
        approval_artifact_path="03_INPUTS/client-alpha/scope-approval.json",
        scope_packet_output_path="../outside-scope.json",
    )

    assert approval_manifest["ready_to_author_scope_approval"] is False
    assert approval_manifest["approval_output_path"] is None
    assert "approval_output_path or approval_artifact_path" in approval_manifest["missing_inputs"]
    assert any("approval_output_path escapes vault root" in error for error in approval_manifest["errors"])
    assert scope_manifest["ready_to_author_scope_packet"] is False
    assert scope_manifest["scope_packet_output_path"] is None
    assert "scope_packet_output_path" in scope_manifest["missing_inputs"]
    assert any("scope_packet_output_path escapes vault root" in error for error in scope_manifest["errors"])


def test_real_client_input_manifest_recommends_scope_packet_after_valid_approval_artifact(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    approval = tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"
    _write(source, "approved source\n")
    _write(
        approval,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-real-client-scope-approval-001",
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-001",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": ["03_INPUTS/client-alpha/source.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
                "operator_attested_scope_approved": True,
                "external_send_authorized": False,
                "payment_mutation_authorized": False,
                "crm_mutation_authorized": False,
                "provider_calls_authorized": False,
                "browser_actions_authorized": False,
                "revenue_claim_authorized": False,
                "live_client_workflow_proof_performed": False,
                "live_client_data_ingested": False,
                "external_send_performed": False,
                "payment_mutation_performed": False,
                "crm_mutation_performed": False,
                "provider_calls": 0,
                "browser_actions": 0,
                "revenue_claim_made": False,
            },
            indent=2,
        ),
    )

    manifest = build_real_client_input_manifest(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-001",
        approval_id="operator-real-client-scope-approval-001",
        approved_read_paths=["03_INPUTS/client-alpha/source.md"],
        approval_artifact_path="03_INPUTS/client-alpha/scope-approval.json",
        scope_packet_output_path="runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json",
    )

    assert manifest["manifest_status"] == "ready_to_author_scope_packet"
    assert manifest["ready_to_author_scope_approval"] is True
    assert manifest["scope_approval_artifact_valid"] is True
    assert manifest["ready_to_author_scope_packet"] is True
    assert manifest["next_command"].startswith("chaseos ventureops scope-evidence-packet")
    assert "--approval-artifact-path 03_INPUTS/client-alpha/scope-approval.json" in manifest["next_command"]
    assert "--output runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json" in manifest["next_command"]


def test_real_client_input_manifest_blocks_scope_packet_without_output_path(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    approval = tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"
    _write(source, "approved source\n")
    _write(
        approval,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-real-client-scope-approval-001",
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-001",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": ["03_INPUTS/client-alpha/source.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
                "operator_attested_scope_approved": True,
                "external_send_authorized": False,
                "payment_mutation_authorized": False,
                "crm_mutation_authorized": False,
                "provider_calls_authorized": False,
                "browser_actions_authorized": False,
                "revenue_claim_authorized": False,
            },
            indent=2,
        ),
    )

    manifest = build_real_client_input_manifest(
        tmp_path,
        client_label="Client Alpha",
        client_approved_scope_id="scope-client-alpha-001",
        approval_id="operator-real-client-scope-approval-001",
        approved_read_paths=["03_INPUTS/client-alpha/source.md"],
        approval_artifact_path="03_INPUTS/client-alpha/scope-approval.json",
    )

    assert manifest["manifest_status"] == "blocked_missing_real_client_inputs"
    assert manifest["scope_approval_artifact_valid"] is True
    assert manifest["ready_to_author_scope_packet"] is False
    assert "scope_packet_output_path" in manifest["missing_inputs"]
    assert manifest["next_required_action"] == "provide scope packet output path"
    assert manifest["next_command"].startswith("chaseos ventureops real-client-input-manifest")


def test_real_client_input_manifest_cli_reports_next_scope_input_command(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    _write(source, "approved source\n")

    result = _run_cli_json([
        "ventureops",
        "real-client-input-manifest",
        "--vault-root",
        str(tmp_path),
        "--client-label",
        "Client Alpha",
        "--scope-id",
        "scope-client-alpha-001",
        "--approval-id",
        "operator-real-client-scope-approval-001",
        "--approved-read-path",
        str(source),
        "--approval-output",
        str(tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"),
        "--json",
    ])

    assert result["ok"] is True
    assert result["manifest_status"] == "ready_to_author_scope_approval"
    assert result["ready_to_author_scope_approval"] is True
    assert result["next_command"].startswith("chaseos ventureops scope-approval-packet")


def test_real_client_input_manifest_cli_write_report_defaults_to_dated_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    _write(source, "approved source\n")
    monkeypatch.chdir(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "real-client-input-manifest",
        "--vault-root",
        str(tmp_path),
        "--client-label",
        "Client Alpha",
        "--scope-id",
        "scope-client-alpha-001",
        "--approval-id",
        "operator-real-client-scope-approval-001",
        "--approved-read-path",
        str(source),
        "--approval-output",
        str(tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"),
        "--write-report",
        "--json",
    ])

    expected = Path("07_LOGS") / "Workflow-Proofs" / f"{date.today().isoformat()}_ventureops-real-client-input-manifest.json"
    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / expected).exists()


def test_real_client_input_manifest_cli_write_report_uses_collision_safe_default_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    _write(source, "approved source\n")
    monkeypatch.chdir(tmp_path)
    base = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-real-client-input-manifest.json"
    )
    expected = (
        Path("07_LOGS")
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-real-client-input-manifest-2.json"
    )
    (tmp_path / base).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / base).write_text("existing manifest report", encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "real-client-input-manifest",
        "--vault-root",
        str(tmp_path),
        "--client-label",
        "Client Alpha",
        "--scope-id",
        "scope-client-alpha-001",
        "--approval-id",
        "operator-real-client-scope-approval-001",
        "--approved-read-path",
        str(source),
        "--approval-output",
        str(tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"),
        "--write-report",
        "--json",
    ])

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert (tmp_path / base).read_text(encoding="utf-8") == "existing manifest report"
    assert (tmp_path / expected).exists()


def test_real_client_input_manifest_cli_blocks_existing_report_path_without_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    _write(source, "approved source\n")
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "real-client-input-manifest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing manifest report", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "real-client-input-manifest",
            "--vault-root",
            str(tmp_path),
            "--client-label",
            "Client Alpha",
            "--scope-id",
            "scope-client-alpha-001",
            "--approval-id",
            "operator-real-client-scope-approval-001",
            "--approved-read-path",
            str(source),
            "--approval-output",
            str(tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing manifest report"


def test_real_client_input_manifest_cli_blocks_escaped_report_path_without_traceback(tmp_path: Path) -> None:
    source = tmp_path / "03_INPUTS" / "client-alpha" / "source.md"
    _write(source, "approved source\n")
    escaped_report_path = tmp_path / ".." / "outside-real-client-input-manifest.json"

    result = _run_cli_json(
        [
            "ventureops",
            "real-client-input-manifest",
            "--vault-root",
            str(tmp_path),
            "--client-label",
            "Client Alpha",
            "--scope-id",
            "scope-client-alpha-001",
            "--approval-id",
            "operator-real-client-scope-approval-001",
            "--approved-read-path",
            str(source),
            "--approval-output",
            str(tmp_path / "03_INPUTS" / "client-alpha" / "scope-approval.json"),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_final_external_execution_runbook_includes_real_client_input_manifest() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = {step["stage"]: step for step in runbook["command_sequence"]}

    manifest = stages["real-client input manifest"]

    assert "chaseos ventureops real-client-input-manifest" in manifest["command"]
    assert "client label" in manifest["required_before"]
    assert "no-execution real-client input manifest" in manifest["writes"]
    assert "does not run live workflows" in manifest["notes"]


def test_final_external_execution_runbook_manifest_command_requests_scope_packet_output() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = {step["stage"]: step for step in runbook["command_sequence"]}

    manifest_command = stages["real-client input manifest"]["command"]

    assert "--approval-output PATH" in runbook["next_command"]
    assert "--scope-packet-output PATH" in runbook["next_command"]
    assert "--approval-output PATH" in manifest_command
    assert "--scope-packet-output PATH" in manifest_command


def test_final_external_execution_runbook_requires_final_evidence_bundle_before_completion_audit() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = [step["stage"] for step in runbook["command_sequence"]]
    bundle_stage = runbook["command_sequence"][stages.index("final evidence bundle validation")]

    assert stages.index("final evidence bundle validation") < stages.index("final audit rerun")
    assert (
        "chaseos ventureops final-evidence-bundle --bundle PATH --write-report --report-path PATH --json"
        == bundle_stage["command"]
    )
    assert bundle_stage["status"] == "blocked"
    assert "final scope packet" in bundle_stage["required_before"]
    assert "proof-only live revenue artifact" in bundle_stage["required_before"]
    assert "does not execute live workflows" in bundle_stage["notes"]
    assert runbook["final_evidence_bundle_validation_required"] is True
    assert runbook["ready_for_final_audit_rerun"] is False
    assert "final evidence bundle validation" in {
        item["requirement"] for item in runbook["runbook_checklist"]
    }


def test_final_external_execution_runbook_routes_final_bundle_validation_to_report_writeback() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = {step["stage"]: step for step in runbook["command_sequence"]}
    bundle_stage = stages["final evidence bundle validation"]
    checklist = {item["requirement"]: item for item in runbook["runbook_checklist"]}

    assert "--write-report" in bundle_stage["command"]
    assert "--report-path PATH" in bundle_stage["command"]
    assert "operator-selected final evidence bundle validation report path" in bundle_stage["writes"]
    assert "ready validation report" in bundle_stage["notes"]
    assert "final evidence bundle validation report writeback" in checklist
    assert "--write-report" in checklist["final evidence bundle validation report writeback"]["notes"]


def test_final_external_execution_runbook_routes_final_audit_rerun_to_report_writeback() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = {step["stage"]: step for step in runbook["command_sequence"]}
    final_audit = stages["final audit rerun"]
    checklist = {item["requirement"]: item for item in runbook["runbook_checklist"]}

    assert final_audit["command"] == (
        "chaseos ventureops feature-family-completion-audit "
        "--write-report --report-path PATH --json"
    )
    assert "ready final evidence bundle validation report" in final_audit["required_before"]
    assert "operator-selected final feature-family completion audit report path" in final_audit["writes"]
    assert "durable completion audit report" in final_audit["notes"]
    assert "final completion audit report writeback" in checklist
    assert "--write-report --report-path PATH" in checklist["final completion audit report writeback"]["notes"]


def test_final_external_execution_runbook_includes_final_evidence_bundle_packet_authoring() -> None:
    root = Path(__file__).resolve().parents[2]

    runbook = build_final_external_execution_runbook(root)
    stages = [step["stage"] for step in runbook["command_sequence"]]
    packet_stage = runbook["command_sequence"][stages.index("final evidence bundle packet authoring")]

    assert stages.index("proof-only live revenue artifact") < stages.index("final evidence bundle packet authoring")
    assert stages.index("final evidence bundle packet authoring") < stages.index("final evidence bundle validation")
    assert "chaseos ventureops final-evidence-bundle-packet" in packet_stage["command"]
    assert "--scope-packet-path PATH" in packet_stage["command"]
    assert "--live-revenue-proof-path PATH" in packet_stage["command"]
    assert packet_stage["status"] == "blocked"
    assert "operator-selected final evidence bundle path" in packet_stage["writes"]
    assert "does not execute live workflows" in packet_stage["notes"]
    assert "final evidence bundle packet authoring" in {
        item["requirement"] for item in runbook["runbook_checklist"]
    }


def test_external_readiness_completion_audit_maps_real_client_input_manifest_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    manifest = checklist["real-client input manifest CLI"]

    assert audit["real_client_input_manifest_cli_valid"] is True
    assert manifest["status"] == "verified"
    assert "runtime/ventureops/real_client_input_manifest.py" in manifest["evidence"]
    assert "chaseos ventureops real-client-input-manifest" in manifest["evidence"]
    assert "does not run live workflows" in manifest["notes"]


def test_external_readiness_completion_audit_maps_real_client_manifest_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["real-client input manifest report write guard"]

    assert audit["real_client_input_manifest_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/real_client_input_manifest.py" in guard["evidence"]
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "existing report paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_real_client_manifest_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["real-client input manifest report dated default"]

    assert audit["real_client_input_manifest_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_real_client_manifest_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["real-client input manifest report default collision guard"]

    assert audit["real_client_input_manifest_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_feature_family_completion_audit_maps_real_client_manifest_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["real-client input manifest report write guard"]

    assert audit["real_client_input_manifest_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/real_client_input_manifest.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_real_client_manifest_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["real-client input manifest report dated default"]

    assert audit["real_client_input_manifest_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_real_client_manifest_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["real-client input manifest report default collision guard"]

    assert audit["real_client_input_manifest_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_live_readiness_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["live readiness report write guard"]

    assert audit["live_readiness_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_live_readiness_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["live readiness report dated default"]

    assert audit["live_readiness_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_live_readiness_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["live readiness report default collision guard"]

    assert audit["live_readiness_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_external_audit_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["external readiness audit report write guard"]

    assert audit["external_readiness_audit_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_external_audit_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["external readiness audit report dated default"]

    assert audit["external_readiness_audit_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_external_audit_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["external readiness audit report default collision guard"]

    assert audit["external_readiness_audit_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_live_client_scope_packet_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["live-client scope packet reference revalidation"]

    assert audit["live_client_scope_packet_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_real_client_scope_evidence" in revalidation["evidence"]
    assert "referenced scope packet, approval artifact, and approved source files" in revalidation["notes"]


def test_feature_family_completion_audit_maps_live_revenue_packet_reference_revalidation() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    revalidation = checklist["live-revenue packet reference revalidation"]

    assert audit["live_revenue_packet_reference_revalidation_valid"] is True
    assert revalidation["status"] == "verified"
    assert "runtime.ventureops.validation.discover_external_completion_artifacts" in revalidation["evidence"]
    assert "runtime.ventureops.validation.validate_live_revenue_evidence" in revalidation["evidence"]
    assert "referenced revenue packet" in revalidation["notes"]


def test_external_readiness_completion_audit_maps_delivery_proof_packet_builder_cli() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    builder = checklist["delivery proof packet builder CLI"]

    assert audit["delivery_proof_packet_builder_cli_valid"] is True
    assert builder["status"] == "verified"
    assert "runtime/ventureops/delivery_proof_packet_builder.py" in builder["evidence"]
    assert "chaseos ventureops delivery-proof-packet" in builder["evidence"]
    assert "does not perform external delivery" in builder["notes"]


def _write_valid_final_evidence_bundle_fixture(root: Path) -> Path:
    source = root / "03_INPUTS" / "client-alpha" / "redacted-brief.md"
    approval = root / "03_INPUTS" / "client-alpha" / "scope-approval.json"
    scope_packet = root / "03_INPUTS" / "client-alpha" / "scope-evidence.json"
    live_client_proof = root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json"
    delivery_proof = root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json"
    revenue_packet = root / "runtime" / "ventureops" / "fixtures" / "revenue-evidence" / "client-alpha-revenue.json"
    revenue_proof = root / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json"
    bundle = root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-final-evidence-bundle.json"

    _write(source, "approved source\n")
    _write(
        approval,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-approval-client-alpha-scope-002",
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-002",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
                "operator_attested_scope_approved": True,
                "external_send_authorized": False,
                "payment_mutation_authorized": False,
                "crm_mutation_authorized": False,
                "provider_calls_authorized": False,
                "browser_actions_authorized": False,
                "revenue_claim_authorized": False,
            },
            indent=2,
        ),
    )
    _write(
        scope_packet,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-002",
                "client_label": "Client Alpha",
                "approval_id": "operator-approval-client-alpha-scope-002",
                "approval_status": "approved",
                "approval_artifact_path": "03_INPUTS/client-alpha/scope-approval.json",
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-brief.md"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            },
            indent=2,
        ),
    )
    _write(live_client_proof, json.dumps(_valid_live_client_workflow_proof_artifact(), indent=2))
    _write_valid_live_client_completion_prerequisites(root)
    _write_valid_revenue_completion_prerequisites(root)
    _write(
        revenue_packet,
        json.dumps(
            {
                "type": "ventureops-live-revenue-evidence",
                "revenue_proof_id": "revenue-client-alpha-007",
                "workflow_id": "agent_runtime_governance_audit",
                "client_label": "Client Alpha",
                "payment_reference_id": "pay_ref_redacted_alpha_007",
                "payment_status": "received",
                "amount": "250.00",
                "currency": "USD",
                "receipt_artifact_path": "07_LOGS/Revenue-Proofs/client-alpha-receipt-redacted.json",
                "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
                "crm_reference_id": "crm_ref_redacted_alpha_007",
                "approval_id": "operator-approval-client-alpha-revenue-007",
                "revenue_recognition_boundary": "proof_only_no_accounting_claim",
            },
            indent=2,
        ),
    )
    _write(revenue_proof, json.dumps(_valid_live_revenue_proof_artifact(), indent=2))
    _write(
        bundle,
        json.dumps(
            {
                "type": "ventureops-final-external-evidence-bundle",
                "scope_packet_path": "03_INPUTS/client-alpha/scope-evidence.json",
                "live_client_workflow_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json",
                "delivery_proof_path": "07_LOGS/Workflow-Proofs/client-alpha-delivery-proof.json",
                "revenue_packet_path": "runtime/ventureops/fixtures/revenue-evidence/client-alpha-revenue.json",
                "live_revenue_proof_path": "07_LOGS/Revenue-Proofs/client-alpha-live-revenue-proof.json",
            },
            indent=2,
        ),
    )
    return bundle


def test_final_external_evidence_bundle_validation_blocks_missing_bundle(tmp_path: Path) -> None:
    from runtime.ventureops.final_external_evidence_bundle import validate_final_external_evidence_bundle

    result = validate_final_external_evidence_bundle(
        tmp_path,
        bundle_path="07_LOGS/Workflow-Proofs/missing-final-evidence-bundle.json",
    )

    assert result["ok"] is True
    assert result["validation_status"] == "blocked"
    assert result["ready_for_completion_audit"] is False
    assert "final evidence bundle missing" in result["blockers"]
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_external_delivery_performed"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_final_external_evidence_bundle_validation_rejects_scope_packet_path_mismatch(tmp_path: Path) -> None:
    from runtime.ventureops.final_external_evidence_bundle import validate_final_external_evidence_bundle

    bundle = _write_valid_final_evidence_bundle_fixture(tmp_path)
    alternate_scope = tmp_path / "03_INPUTS" / "client-alpha" / "alternate-scope-evidence.json"
    original_scope = tmp_path / "03_INPUTS" / "client-alpha" / "scope-evidence.json"
    _write(alternate_scope, original_scope.read_text(encoding="utf-8"))
    bundle_data = json.loads(bundle.read_text(encoding="utf-8"))
    bundle_data["scope_packet_path"] = "03_INPUTS/client-alpha/alternate-scope-evidence.json"
    _write(bundle, json.dumps(bundle_data, indent=2))

    result = validate_final_external_evidence_bundle(
        tmp_path,
        bundle_path="07_LOGS/Workflow-Proofs/client-alpha-final-evidence-bundle.json",
    )

    assert result["ready_for_completion_audit"] is False
    assert "scope packet path does not match live-client workflow proof scope_packet_path" in result["blockers"]


def test_final_external_evidence_bundle_validation_rejects_revenue_packet_path_mismatch(tmp_path: Path) -> None:
    from runtime.ventureops.final_external_evidence_bundle import validate_final_external_evidence_bundle

    bundle = _write_valid_final_evidence_bundle_fixture(tmp_path)
    alternate_revenue = tmp_path / "runtime" / "ventureops" / "fixtures" / "revenue-evidence" / "alternate-client-alpha-revenue.json"
    original_revenue = tmp_path / "runtime" / "ventureops" / "fixtures" / "revenue-evidence" / "client-alpha-revenue.json"
    _write(alternate_revenue, original_revenue.read_text(encoding="utf-8"))
    bundle_data = json.loads(bundle.read_text(encoding="utf-8"))
    bundle_data["revenue_packet_path"] = "runtime/ventureops/fixtures/revenue-evidence/alternate-client-alpha-revenue.json"
    _write(bundle, json.dumps(bundle_data, indent=2))

    result = validate_final_external_evidence_bundle(
        tmp_path,
        bundle_path="07_LOGS/Workflow-Proofs/client-alpha-final-evidence-bundle.json",
    )

    assert result["ready_for_completion_audit"] is False
    assert "revenue packet path does not match live revenue proof revenue_packet_path" in result["blockers"]


def test_final_external_evidence_bundle_validation_rejects_invalid_client_safe_delivery_artifact(
    tmp_path: Path,
) -> None:
    from runtime.ventureops.final_external_evidence_bundle import validate_final_external_evidence_bundle

    _write_valid_final_evidence_bundle_fixture(tmp_path)
    _write(
        tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-redacted.json",
        json.dumps({"redacted": False}, indent=2),
    )

    result = validate_final_external_evidence_bundle(
        tmp_path,
        bundle_path="07_LOGS/Workflow-Proofs/client-alpha-final-evidence-bundle.json",
    )

    assert result["ready_for_completion_audit"] is False
    assert result["client_safe_delivery_artifact_valid"] is False
    assert "client-safe delivery artifact invalid: redacted must be true" in result["blockers"]


def _write_final_bundle_builder_reference_files(root: Path) -> dict[str, Path]:
    paths = {
        "scope": root / "runtime" / "ventureops" / "fixtures" / "scope-evidence" / "client-alpha-scope.json",
        "live_client": root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json",
        "delivery": root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-delivery-proof.json",
        "revenue": root / "runtime" / "ventureops" / "fixtures" / "revenue-evidence" / "client-alpha-revenue.json",
        "live_revenue": root / "07_LOGS" / "Revenue-Proofs" / "client-alpha-live-revenue-proof.json",
    }
    for path in paths.values():
        _write(path, "{}\n")
    return paths


def test_final_evidence_bundle_packet_builder_writes_guarded_bundle(tmp_path: Path) -> None:
    from runtime.ventureops.final_evidence_bundle_packet_builder import build_final_evidence_bundle_packet

    paths = _write_final_bundle_builder_reference_files(tmp_path)
    output = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-final-evidence-bundle.json"

    result = build_final_evidence_bundle_packet(
        tmp_path,
        scope_packet_path=str(paths["scope"]),
        live_client_workflow_proof_path=str(paths["live_client"]),
        delivery_proof_path=str(paths["delivery"]),
        revenue_packet_path=str(paths["revenue"]),
        live_revenue_proof_path=str(paths["live_revenue"]),
        output_path=str(output),
    )

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert result["packet_path"] == "07_LOGS/Workflow-Proofs/client-alpha-final-evidence-bundle.json"
    assert result["packet"]["type"] == "ventureops-final-external-evidence-bundle"
    assert result["packet"]["scope_packet_path"] == "runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json"
    assert result["packet"]["live_client_workflow_proof_path"] == (
        "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    )
    assert result["next_command"] == (
        "chaseos ventureops final-evidence-bundle "
        "--bundle 07_LOGS/Workflow-Proofs/client-alpha-final-evidence-bundle.json --json"
    )
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_external_delivery_performed"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False
    assert output.exists()


def test_final_evidence_bundle_packet_builder_rejects_existing_output(tmp_path: Path) -> None:
    from runtime.ventureops.final_evidence_bundle_packet_builder import build_final_evidence_bundle_packet

    paths = _write_final_bundle_builder_reference_files(tmp_path)
    output = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-final-evidence-bundle.json"
    _write(output, "{}\n")

    result = build_final_evidence_bundle_packet(
        tmp_path,
        scope_packet_path=str(paths["scope"]),
        live_client_workflow_proof_path=str(paths["live_client"]),
        delivery_proof_path=str(paths["delivery"]),
        revenue_packet_path=str(paths["revenue"]),
        live_revenue_proof_path=str(paths["live_revenue"]),
        output_path=str(output),
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert result["output_path_available"] is False
    assert any("output path already exists:" in error for error in result["errors"])


def test_final_evidence_bundle_packet_builder_blocks_escaped_paths_without_exception(tmp_path: Path) -> None:
    from runtime.ventureops.final_evidence_bundle_packet_builder import build_final_evidence_bundle_packet

    paths = _write_final_bundle_builder_reference_files(tmp_path)

    result = build_final_evidence_bundle_packet(
        tmp_path,
        scope_packet_path="../outside-scope.json",
        live_client_workflow_proof_path=str(paths["live_client"]),
        delivery_proof_path=str(paths["delivery"]),
        revenue_packet_path=str(paths["revenue"]),
        live_revenue_proof_path=str(paths["live_revenue"]),
        output_path="../outside-bundle.json",
    )

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert any("scope_packet_path escapes vault root" in error for error in result["errors"])
    assert any("output_path escapes vault root" in error for error in result["errors"])
    assert result["live_client_workflow_proof_performed"] is False
    assert result["live_external_delivery_performed"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False


def test_final_evidence_bundle_packet_cli_blocks_escaped_output_without_traceback(tmp_path: Path) -> None:
    paths = _write_final_bundle_builder_reference_files(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "final-evidence-bundle-packet",
        "--vault-root",
        str(tmp_path),
        "--scope-packet-path",
        str(paths["scope"]),
        "--live-client-workflow-proof-path",
        str(paths["live_client"]),
        "--delivery-proof-path",
        str(paths["delivery"]),
        "--revenue-packet-path",
        str(paths["revenue"]),
        "--live-revenue-proof-path",
        str(paths["live_revenue"]),
        "--output",
        "../outside-bundle.json",
        "--json",
    ], expected_exit=1)

    assert result["ok"] is False
    assert result["packet_written"] is False
    assert any("output_path escapes vault root" in error for error in result["errors"])
    assert "Traceback" not in json.dumps(result)


def test_final_evidence_bundle_packet_cli_writes_bundle(tmp_path: Path) -> None:
    paths = _write_final_bundle_builder_reference_files(tmp_path)
    output = tmp_path / "07_LOGS" / "Workflow-Proofs" / "client-alpha-final-evidence-bundle.json"

    result = _run_cli_json([
        "ventureops",
        "final-evidence-bundle-packet",
        "--vault-root",
        str(tmp_path),
        "--scope-packet-path",
        str(paths["scope"]),
        "--live-client-workflow-proof-path",
        str(paths["live_client"]),
        "--delivery-proof-path",
        str(paths["delivery"]),
        "--revenue-packet-path",
        str(paths["revenue"]),
        "--live-revenue-proof-path",
        str(paths["live_revenue"]),
        "--output",
        str(output),
        "--json",
    ])

    assert result["ok"] is True
    assert result["packet_written"] is True
    assert result["next_command"].startswith("chaseos ventureops final-evidence-bundle --bundle")
    assert output.exists()


def test_final_external_evidence_bundle_validation_accepts_complete_proof_chain(tmp_path: Path) -> None:
    from runtime.ventureops.final_external_evidence_bundle import validate_final_external_evidence_bundle

    bundle = _write_valid_final_evidence_bundle_fixture(tmp_path)

    result = validate_final_external_evidence_bundle(tmp_path, bundle_path=str(bundle))

    assert result["ok"] is True
    assert result["validation_status"] == "ready_for_completion_audit"
    assert result["ready_for_completion_audit"] is True
    assert result["scope_evidence_valid"] is True
    assert result["scope_approval_artifact_valid"] is True
    assert result["scope_sources_valid"] is True
    assert result["live_client_workflow_proof_valid"] is True
    assert result["delivery_proof_artifact_valid"] is True
    assert result["revenue_evidence_valid"] is True
    assert result["live_revenue_proof_valid"] is True
    assert result["external_completion_artifacts"]["live_client_workflow_proof_present"] is True
    assert result["external_completion_artifacts"]["live_revenue_workflow_proof_present"] is True
    assert result["next_command"] == (
        "chaseos ventureops feature-family-completion-audit "
        "--write-report --report-path PATH --json"
    )


def test_final_external_evidence_bundle_cli_reports_blocked_without_bundle(tmp_path: Path) -> None:
    result = _run_cli_json([
        "ventureops",
        "final-evidence-bundle",
        "--vault-root",
        str(tmp_path),
        "--bundle",
        str(tmp_path / "missing-final-evidence-bundle.json"),
        "--json",
    ])

    assert result["ok"] is True
    assert result["validation_status"] == "blocked"
    assert result["ready_for_completion_audit"] is False
    assert "final evidence bundle missing" in result["blockers"]


def test_final_evidence_bundle_cli_write_report_defaults_to_dated_report_path(tmp_path: Path) -> None:
    bundle = tmp_path / "07_LOGS" / "Workflow-Proofs" / "missing-final-evidence-bundle.json"
    expected = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-final-evidence-bundle-validation-report.json"
    )

    result = _run_cli_json([
        "ventureops",
        "final-evidence-bundle",
        "--vault-root",
        str(tmp_path),
        "--bundle",
        str(bundle),
        "--write-report",
        "--json",
    ])

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert expected.is_file()
    written = json.loads(expected.read_text(encoding="utf-8"))
    assert written["ready_for_completion_audit"] is False
    assert "final evidence bundle missing" in written["blockers"]


def test_final_evidence_bundle_cli_write_report_uses_collision_safe_default_path(tmp_path: Path) -> None:
    bundle = tmp_path / "07_LOGS" / "Workflow-Proofs" / "missing-final-evidence-bundle.json"
    base = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-final-evidence-bundle-validation-report.json"
    )
    expected = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / f"{date.today().isoformat()}_ventureops-final-evidence-bundle-validation-report-2.json"
    )
    base.parent.mkdir(parents=True, exist_ok=True)
    base.write_text("existing validation report", encoding="utf-8")

    result = _run_cli_json([
        "ventureops",
        "final-evidence-bundle",
        "--vault-root",
        str(tmp_path),
        "--bundle",
        str(bundle),
        "--write-report",
        "--json",
    ])

    assert result["report_written"] is True
    assert result["report_path"] == str(expected)
    assert base.read_text(encoding="utf-8") == "existing validation report"
    assert expected.is_file()
    written = json.loads(expected.read_text(encoding="utf-8"))
    assert written["ready_for_completion_audit"] is False
    assert "final evidence bundle missing" in written["blockers"]


def test_final_evidence_bundle_cli_blocks_existing_report_path_without_overwrite(tmp_path: Path) -> None:
    bundle = tmp_path / "07_LOGS" / "Workflow-Proofs" / "missing-final-evidence-bundle.json"
    report_path = tmp_path / "07_LOGS" / "Workflow-Proofs" / "final-bundle-validation-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("existing report bytes", encoding="utf-8")

    result = _run_cli_json(
        [
            "ventureops",
            "final-evidence-bundle",
            "--vault-root",
            str(tmp_path),
            "--bundle",
            str(bundle),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert f"report path already exists: {report_path.relative_to(tmp_path).as_posix()}" in result["errors"]
    assert report_path.read_text(encoding="utf-8") == "existing report bytes"


def test_final_evidence_bundle_cli_blocks_escaped_report_path_without_traceback(tmp_path: Path) -> None:
    bundle = tmp_path / "07_LOGS" / "Workflow-Proofs" / "missing-final-evidence-bundle.json"
    escaped_report_path = tmp_path / ".." / "outside-final-bundle-validation-report.json"

    result = _run_cli_json(
        [
            "ventureops",
            "final-evidence-bundle",
            "--vault-root",
            str(tmp_path),
            "--bundle",
            str(bundle),
            "--write-report",
            "--report-path",
            str(escaped_report_path),
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert result["report_written"] is False
    assert result["report_write_blocked"] is True
    assert any("report_path escapes vault root" in error for error in result["errors"])
    assert not escaped_report_path.exists()


def test_external_readiness_completion_audit_maps_final_evidence_bundle_validator() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    validator = checklist["final external evidence bundle validator"]

    assert audit["final_evidence_bundle_validator_valid"] is True
    assert validator["status"] == "verified"
    assert "runtime/ventureops/final_external_evidence_bundle.py" in validator["evidence"]
    assert "chaseos ventureops final-evidence-bundle" in validator["evidence"]
    assert "whole proof chain" in validator["notes"]


def test_external_readiness_completion_audit_maps_final_bundle_validation_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["final evidence bundle validation report write guard"]

    assert audit["final_evidence_bundle_validation_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/final_external_evidence_bundle.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "overwrite" in guard["notes"]


def test_external_readiness_completion_audit_maps_final_bundle_validation_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["final evidence bundle validation report dated default"]

    assert audit["final_evidence_bundle_validation_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_final_bundle_validation_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["final evidence bundle validation report default collision guard"]

    assert audit["final_evidence_bundle_validation_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_external_readiness_completion_audit_maps_feature_family_audit_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["feature-family completion audit report write guard"]

    assert audit["feature_family_completion_audit_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/feature_family_completion_audit.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "escaped report paths" in guard["notes"]


def test_external_readiness_completion_audit_maps_feature_family_audit_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["feature-family completion audit report dated default"]

    assert audit["feature_family_completion_audit_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]
    assert "date-stamped" in dated_default["notes"]


def test_external_readiness_completion_audit_maps_feature_family_audit_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["feature-family completion audit report default collision guard"]

    assert audit["feature_family_completion_audit_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]
    assert "next available" in collision_guard["notes"]


def test_external_readiness_completion_audit_maps_final_evidence_bundle_packet_builder() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    builder = checklist["final evidence bundle packet builder CLI"]

    assert audit["final_evidence_bundle_packet_builder_cli_valid"] is True
    assert builder["status"] == "verified"
    assert "runtime/ventureops/final_evidence_bundle_packet_builder.py" in builder["evidence"]
    assert "chaseos ventureops final-evidence-bundle-packet" in builder["evidence"]
    assert "does not execute live workflows" in builder["notes"]


def test_external_readiness_completion_audit_maps_final_bundle_packet_path_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = audit_external_readiness_completion(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["final evidence bundle packet path guard"]

    assert audit["final_evidence_bundle_packet_path_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/final_evidence_bundle_packet_builder.py" in guard["evidence"]
    assert "runtime/ventureops/test_ventureops.py" in guard["evidence"]
    assert "escaped final bundle packet paths" in guard["notes"]


def test_feature_family_completion_audit_maps_final_evidence_bundle_validator() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    validator = checklist["final external evidence bundle validator"]

    assert audit["final_evidence_bundle_validator_valid"] is True
    assert validator["status"] == "verified"
    assert "runtime/ventureops/final_external_evidence_bundle.py" in validator["evidence"]
    assert "final completion audit" in validator["notes"]


def test_feature_family_completion_audit_maps_final_bundle_validation_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["final evidence bundle validation report write guard"]

    assert audit["final_evidence_bundle_validation_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/final_external_evidence_bundle.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_final_bundle_validation_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["final evidence bundle validation report dated default"]

    assert audit["final_evidence_bundle_validation_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_final_bundle_validation_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["final evidence bundle validation report default collision guard"]

    assert audit["final_evidence_bundle_validation_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_feature_family_audit_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["feature-family completion audit report write guard"]

    assert audit["feature_family_completion_audit_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/feature_family_completion_audit.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_feature_family_audit_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["feature-family completion audit report dated default"]

    assert audit["feature_family_completion_audit_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_feature_family_audit_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["feature-family completion audit report default collision guard"]

    assert audit["feature_family_completion_audit_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_final_runbook_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["final external runbook report write guard"]

    assert audit["final_external_runbook_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_final_runbook_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["final external runbook report dated default"]

    assert audit["final_external_runbook_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_final_runbook_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["final external runbook report default collision guard"]

    assert audit["final_external_runbook_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_real_evidence_closeout_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["real evidence closeout report write guard"]

    assert audit["real_evidence_closeout_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_real_evidence_closeout_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["real evidence closeout report dated default"]

    assert audit["real_evidence_closeout_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_real_evidence_closeout_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["real evidence closeout report default collision guard"]

    assert audit["real_evidence_closeout_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_evidence_intake_report_write_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["evidence intake report write guard"]

    assert audit["evidence_intake_report_write_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_evidence_intake_report_dated_default() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    dated_default = checklist["evidence intake report dated default"]

    assert audit["evidence_intake_report_dated_default_valid"] is True
    assert dated_default["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in dated_default["evidence"]


def test_feature_family_completion_audit_maps_evidence_intake_report_default_collision_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    collision_guard = checklist["evidence intake report default collision guard"]

    assert audit["evidence_intake_report_default_collision_guard_valid"] is True
    assert collision_guard["status"] == "verified"
    assert "runtime/cli/ventureops_commands.py" in collision_guard["evidence"]


def test_feature_family_completion_audit_maps_final_evidence_bundle_packet_builder() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    builder = checklist["final evidence bundle packet builder CLI"]

    assert audit["final_evidence_bundle_packet_builder_cli_valid"] is True
    assert builder["status"] == "verified"
    assert "runtime/ventureops/final_evidence_bundle_packet_builder.py" in builder["evidence"]
    assert "final evidence bundle" in builder["notes"]


def test_feature_family_completion_audit_maps_final_bundle_packet_path_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["final evidence bundle packet path guard"]

    assert audit["final_evidence_bundle_packet_path_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/final_evidence_bundle_packet_builder.py" in guard["evidence"]


def test_feature_family_completion_audit_maps_external_packet_path_guard() -> None:
    root = Path(__file__).resolve().parents[2]

    audit = build_feature_family_completion_audit(root)
    checklist = {item["requirement"]: item for item in audit["prompt_to_artifact_checklist"]}

    guard = checklist["external packet path guard"]

    assert audit["external_packet_path_guard_valid"] is True
    assert guard["status"] == "verified"
    assert "runtime/ventureops/scope_approval_packet_builder.py" in guard["evidence"]
