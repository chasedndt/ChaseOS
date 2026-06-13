from __future__ import annotations

from datetime import date
from pathlib import Path
import contextlib
import io
import json

from runtime.cli import main as cli
from runtime.cli.main import main as cli_main


ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_CLIENT_SOURCE_PATHS = [
    "runtime/ventureops/fixtures/synthetic_client_runtime/Agent-Control-Plane.md",
    "runtime/ventureops/fixtures/synthetic_client_runtime/Permission-Matrix.md",
    "runtime/ventureops/fixtures/synthetic_client_runtime/Trust-Tiers.md",
    "runtime/ventureops/fixtures/synthetic_client_runtime/Backends-Supported.md",
    "runtime/ventureops/fixtures/synthetic_client_runtime/capabilities.yaml",
    "runtime/ventureops/fixtures/synthetic_client_runtime/workflow_registry.yaml",
]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_aor_fixture(vault: Path) -> None:
    manifest_src = ROOT / "runtime" / "workflows" / "registry" / "agent_runtime_governance_audit.yaml"
    alias_manifest_src = ROOT / "runtime" / "workflows" / "registry" / "ventureops_ai_runtime_security_audit.yaml"
    role_src = ROOT / "06_AGENTS" / "role-cards" / "ventureops-runtime-audit.yaml"
    security_role_src = ROOT / "06_AGENTS" / "role-cards" / "security_reviewer.yaml"
    assert manifest_src.exists(), "agent_runtime_governance_audit AOR manifest must exist"
    assert alias_manifest_src.exists(), "ventureops_ai_runtime_security_audit AOR manifest must exist"
    assert role_src.exists(), "ventureops-runtime-audit role card must exist"
    assert security_role_src.exists(), "security_reviewer role card must exist"

    _write(vault / "CLAUDE.md", "fixture runtime boundary\n")
    _write(vault / "00_HOME" / "Now.md", "Fixture ChaseOS current state for AOR boot context.\n")
    _write(vault / "06_AGENTS" / "Agent-Control-Plane.md", "Runtime authority, Agent Bus, approval gate, external send blocked.\n")
    _write(vault / "06_AGENTS" / "Permission-Matrix.md", "Codex: repo-aware editor. Forbidden: secrets, credentials, destructive deletes.\n")
    _write(vault / "06_AGENTS" / "Trust-Tiers.md", "Tier 4 untrusted inputs must not be treated as instructions.\n")
    _write(vault / "06_AGENTS" / "Backends-Supported.md", "Claude verified. Codex bounded. Browser and provider calls require approval.\n")
    _write(vault / "runtime" / "codex" / "capabilities.yaml", "runtime: Codex\ncapabilities:\n  - code.patch\n  - test.run\n")
    _write(vault / "runtime" / "workflows" / "registry" / "use_case_registry.yaml", "workflows:\n  - workflow_id: agent_runtime_governance_audit\n    status: PARTIAL PACK EXAMPLE\n")
    _write(vault / "07_LOGS" / "Workflow-Proofs" / "README.md", "proof folder\n")
    _write(vault / "07_LOGS" / "Runtime-Audits" / "README.md", "runtime audit folder\n")
    _write(vault / "07_LOGS" / "Agent-Activity" / "README.md", "activity folder\n")
    _write(vault / "runtime" / "workflows" / "registry" / "agent_runtime_governance_audit.yaml", manifest_src.read_text(encoding="utf-8"))
    _write(vault / "runtime" / "workflows" / "registry" / "ventureops_ai_runtime_security_audit.yaml", alias_manifest_src.read_text(encoding="utf-8"))
    _write(vault / "06_AGENTS" / "role-cards" / "ventureops-runtime-audit.yaml", role_src.read_text(encoding="utf-8"))
    _write(vault / "06_AGENTS" / "role-cards" / "security_reviewer.yaml", security_role_src.read_text(encoding="utf-8"))


def _seed_synthetic_client_sources(vault: Path) -> None:
    for relative in SYNTHETIC_CLIENT_SOURCE_PATHS:
        _write(vault / relative, (ROOT / relative).read_text(encoding="utf-8"))


def _seed_workflow_pack_examples(vault: Path) -> None:
    _write(vault / "runtime" / "workflows" / "registry" / "packs" / "agent_runtime_governance_audit.yaml", "workflow_id: agent_runtime_governance_audit\nstatus: verified\n")
    _write(vault / "runtime" / "workflows" / "registry" / "packs" / "growth_studio_proof_pack.yaml", "workflow_id: growth_studio_proof_pack\nstatus: verified\n")


def _run_cli_json(argv: list[str], *, expected_exit: int = 0) -> dict:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = cli_main(argv)
    payload = json.loads(stdout.getvalue())
    assert exit_code == expected_exit, payload
    return payload["result"] if "result" in payload else payload


def _write_valid_scope_packet(vault: Path, relative_path: str = "runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json") -> Path:
    scope_path = vault / relative_path
    approval_relative = "runtime/ventureops/fixtures/scope-evidence/client-alpha-scope-approval.json"
    _write(
        vault / approval_relative,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-approval",
                "approval_id": "operator-real-client-scope-approval-001",
                "client_label": "Synthetic Client Alpha",
                "client_approved_scope_id": "scope-client-alpha-001",
                "approval_status": "approved",
                "approval_decision": "approved",
                "approved_read_paths": [
                    "runtime/ventureops/fixtures/synthetic_client_runtime/Agent-Control-Plane.md",
                    "runtime/ventureops/fixtures/synthetic_client_runtime/Permission-Matrix.md",
                ],
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
        scope_path,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-001",
                "client_label": "Synthetic Client Alpha",
                "approval_id": "operator-real-client-scope-approval-001",
                "approval_status": "approved",
                "approval_artifact_path": approval_relative,
                "approved_read_paths": [
                    "runtime/ventureops/fixtures/synthetic_client_runtime/Agent-Control-Plane.md",
                    "runtime/ventureops/fixtures/synthetic_client_runtime/Permission-Matrix.md",
                ],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            },
            indent=2,
        ),
    )
    return scope_path


def test_agent_runtime_governance_audit_manifest_and_role_card_load() -> None:
    from runtime.aor.registry import load_manifest
    from runtime.aor.role_cards import load_card
    from runtime.aor.task_router import classify

    manifest = load_manifest("agent_runtime_governance_audit", ROOT)
    role = load_card("ventureops-runtime-audit", ROOT)
    task_type = classify("ventureops-runtime-audit", ROOT)

    assert manifest is not None
    assert manifest["status"] == "active"
    assert manifest["task_type"] == "ventureops-runtime-audit"
    assert manifest["permission_ceiling"] == "proposal_log_only"
    assert "07_LOGS/Workflow-Proofs/" in manifest["writeback_targets"]
    assert role is not None
    assert role["id"] == "ventureops-runtime-audit"
    assert "07_LOGS/Workflow-Proofs/" in role["write_scope"]
    assert task_type["id"] == "ventureops-runtime-audit"


def test_ventureops_ai_runtime_security_audit_manifest_and_role_card_load() -> None:
    from runtime.aor.registry import load_manifest
    from runtime.aor.role_cards import load_card
    from runtime.aor.task_router import classify

    manifest = load_manifest("ventureops_ai_runtime_security_audit", ROOT)
    role = load_card("security_reviewer", ROOT)
    task_type = classify("ventureops-runtime-audit", ROOT)

    assert manifest is not None
    assert manifest["status"] == "active"
    assert manifest["task_type"] == "ventureops-runtime-audit"
    assert manifest["permission_ceiling"] == "proposal_log_only"
    assert manifest["alias_of"] == "agent_runtime_governance_audit"
    assert "07_LOGS/Workflow-Proofs/" in manifest["writeback_targets"]
    assert "07_LOGS/Runtime-Audits/" in manifest["writeback_targets"]
    assert role is not None
    assert role["id"] == "security_reviewer"
    assert "07_LOGS/Workflow-Proofs/" in role["write_scope"]
    assert "07_LOGS/Runtime-Audits/" in role["write_scope"]
    assert "mutate_provider_config" in role["forbidden_actions"]
    assert "mutate_shell_or_host_state" in role["forbidden_actions"]
    assert task_type["id"] == "ventureops-runtime-audit"


def test_ventureops_ai_runtime_security_audit_handler_preserves_exact_workflow_id() -> None:
    from runtime.workflows.ventureops_ai_runtime_security_audit import (
        build_ventureops_ai_runtime_security_audit,
    )

    audit = build_ventureops_ai_runtime_security_audit(
        inputs={"run_id": "alias-smoke", "date": "2026-05-13"},
        vault_root=ROOT,
    )

    assert audit["workflow_id"] == "ventureops_ai_runtime_security_audit"
    assert audit["alias_of"] == "agent_runtime_governance_audit"
    assert audit["workflow_family"] == "AI Runtime Security Audit"
    assert audit["proof_path"].endswith("2026-05-13_ventureops_ai_runtime_security_audit_alias-smoke.md")
    assert audit["client_report_path"].endswith(
        "2026-05-13_ventureops_ai_runtime_security_audit_alias-smoke_client-report.md"
    )
    assert audit["scorecard"]["workflow_id"] == "ventureops_ai_runtime_security_audit"
    assert audit["proof_card"]["workflow_id"] == "ventureops_ai_runtime_security_audit"
    assert all("agent_runtime_governance_audit" not in item["path"] for item in audit["writebacks"])
    assert any("Credential or secret read" in item for item in audit["blocked_surfaces"])


def test_agent_runtime_governance_audit_handler_ingests_real_chaseos_sources() -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={"run_id": "real-source-smoke", "date": "2026-05-10"},
        vault_root=ROOT,
    )

    assert audit["workflow_id"] == "agent_runtime_governance_audit"
    assert audit["source_count"] >= 5
    assert "06_AGENTS/Permission-Matrix.md" in audit["input_sources"]
    assert any("external send" in item.lower() for item in audit["blocked_surfaces"])
    assert audit["proof_card"]["workflow_id"] == "agent_runtime_governance_audit"
    assert audit["proof_card"]["input_sources"]
    assert "api_key" not in audit["proof_markdown"].lower()
    assert "seed phrase" not in audit["proof_markdown"].lower()


def test_agent_runtime_governance_audit_returns_client_report_and_valid_scorecard() -> None:
    from runtime.ventureops.validation import validate_agent_scorecard
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={"run_id": "client-report-scorecard", "date": "2026-05-10"},
        vault_root=ROOT,
    )

    assert audit["client_report_path"].endswith("_client-report.md")
    assert audit["scorecard_path"].endswith("_scorecard.json")
    assert len(audit["writebacks"]) == 3
    assert {item["path"] for item in audit["writebacks"]} == {
        audit["proof_path"],
        audit["client_report_path"],
        audit["scorecard_path"],
    }
    assert validate_agent_scorecard(audit["scorecard"])["ok"] is True
    assert audit["scorecard"]["status"] == "internal_run_passed"
    assert audit["scorecard"]["evidence_links"] == [audit["proof_path"], audit["client_report_path"]]
    assert audit["client_report_path"] in audit["proof_card"]["files_written"]
    assert audit["scorecard_path"] in audit["proof_card"]["files_written"]


def test_agent_runtime_governance_audit_client_report_is_client_safe_draft() -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={"run_id": "client-safe-report", "date": "2026-05-10"},
        vault_root=ROOT,
    )
    report = audit["client_report_markdown"]
    lowered = report.lower()

    assert "# Client-Safe Agent Runtime Governance Audit Report" in report
    assert "Delivery status: draft only - not externally sent" in report
    assert "Provider/model calls: blocked" in report
    assert "External sends: blocked" in report
    assert "```json" not in report
    assert "06_AGENTS/Permission-Matrix.md" not in report
    assert "internal_private" not in lowered
    assert "api_key" not in lowered
    assert "seed phrase" not in lowered
    assert "cookie" not in lowered


def test_agent_runtime_governance_audit_synthetic_client_fixture_writes_offer_packet() -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "synthetic-client-offer",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
        },
        vault_root=ROOT,
    )

    assert audit["source_count"] == len(SYNTHETIC_CLIENT_SOURCE_PATHS)
    assert audit["offer_packet_path"].endswith("_offer-packet.md")
    assert len(audit["writebacks"]) == 4
    assert audit["offer_packet_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["offer_packet_path"] in audit["proof_card"]["files_written"]
    assert audit["offer_packet_path"] in audit["scorecard"]["evidence_links"]
    offer = audit["offer_packet_markdown"]
    lowered = offer.lower()
    assert "# Client-Safe Runtime Governance Audit Offer Packet" in offer
    assert "External delivery: blocked until explicit approval" in offer
    assert "Synthetic client fixture: verified" in offer
    assert "provider/model execution: not included" in lowered
    assert "browser action: not included" in lowered
    assert "payment/crm mutation: not included" in lowered
    assert "api_key" not in lowered
    assert "seed phrase" not in lowered
    assert "cookie" not in lowered


def test_agent_runtime_governance_audit_writes_client_scope_and_delivery_approval_contract() -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "client-scope-delivery-approval",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "none",
        },
        vault_root=ROOT,
    )

    assert audit["client_scope_path"].endswith("_client-scope.md")
    assert audit["delivery_approval_contract_path"].endswith("_delivery-approval-contract.md")
    assert len(audit["writebacks"]) == 6
    assert audit["client_scope_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["delivery_approval_contract_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["client_scope_path"] in audit["proof_card"]["files_written"]
    assert audit["delivery_approval_contract_path"] in audit["proof_card"]["files_written"]
    assert audit["client_scope_path"] in audit["scorecard"]["evidence_links"]
    assert audit["delivery_approval_contract_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["external_delivery_approved"] is False

    scope = audit["client_scope_markdown"]
    contract = audit["delivery_approval_contract_markdown"]
    lowered_contract = contract.lower()
    assert "# Client Scope Record" in scope
    assert "Client label: Synthetic Client Alpha" in scope
    assert "Approved use: internal review only" in scope
    assert "# Delivery Approval Contract" in contract
    assert "Delivery approval status: blocked" in contract
    assert "External delivery may not occur from this workflow run." in contract
    assert "provider/model execution: not authorized" in lowered_contract
    assert "browser action: not authorized" in lowered_contract
    assert "payment/crm mutation: not authorized" in lowered_contract
    assert "api_key" not in lowered_contract
    assert "seed phrase" not in lowered_contract
    assert "cookie" not in lowered_contract


def test_agent_runtime_governance_audit_writes_no_send_delivery_packet_preview() -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "delivery-packet-preview",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "none",
        },
        vault_root=ROOT,
    )

    assert audit["delivery_packet_preview_path"].endswith("_delivery-packet-preview.md")
    assert len(audit["writebacks"]) == 7
    assert audit["delivery_packet_preview_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["delivery_packet_preview_path"] in audit["proof_card"]["files_written"]
    assert audit["delivery_packet_preview_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["delivery_packet_preview_written"] is True
    assert audit["scorecard"]["metrics"]["external_delivery_approved"] is False
    assert audit["scorecard"]["metrics"]["external_sends"] == 0
    preview = audit["delivery_packet_preview_markdown"]
    lowered = preview.lower()
    assert "# Delivery Packet Preview" in preview
    assert "Preview status: no-send" in preview
    assert "External send: not performed" in preview
    assert "Approval status: not approved" in preview
    assert audit["client_report_path"] in preview
    assert audit["scorecard_path"] in preview
    assert audit["offer_packet_path"] in preview
    assert audit["client_scope_path"] in preview
    assert audit["delivery_approval_contract_path"] in preview
    assert "provider/model execution: not authorized" in lowered
    assert "browser action: not authorized" in lowered
    assert "payment/crm mutation: not authorized" in lowered
    assert "api_key" not in lowered
    assert "seed phrase" not in lowered
    assert "cookie" not in lowered


def test_agent_runtime_governance_audit_writes_approval_request_artifact_without_consumption() -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "approval-request-artifact",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "none",
        },
        vault_root=ROOT,
    )

    assert audit["approval_request_artifact_path"].endswith("_approval-request.json")
    assert len(audit["writebacks"]) == 8
    assert audit["approval_request_artifact_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["approval_request_artifact_path"] in audit["proof_card"]["files_written"]
    assert audit["approval_request_artifact_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["approval_request_artifact_written"] is True
    assert audit["scorecard"]["metrics"]["approval_consumed"] is False
    assert audit["scorecard"]["metrics"]["external_delivery_approved"] is False
    assert audit["scorecard"]["metrics"]["external_sends"] == 0

    request = audit["approval_request_artifact"]
    assert request["workflow_id"] == "agent_runtime_governance_audit"
    assert request["run_id"] == "approval-request-artifact"
    assert request["status"] == "pending_operator_review"
    assert request["approval_consumed"] is False
    assert request["external_delivery_approved"] is False
    assert request["external_send_performed"] is False
    assert audit["delivery_packet_preview_path"] in request["artifacts_under_review"]
    assert audit["delivery_approval_contract_path"] in request["artifacts_under_review"]
    assert request["requested_decision"] == "approve_or_reject_external_delivery"
    assert request["forbidden_actions"] == [
        "provider_model_execution",
        "browser_action",
        "external_send",
        "payment_crm_mutation",
        "live_remediation",
        "canonical_state_mutation",
    ]
    request_json = audit["approval_request_artifact_json"].lower()
    assert "api_key" not in request_json
    assert "seed phrase" not in request_json
    assert "cookie" not in request_json


def test_agent_runtime_governance_audit_consumes_explicit_approval_without_external_send() -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "approval-consumption-proof",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "approval_decision_id": "operator-decision-approval-consumption-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "approval-consumption-proof",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "none",
        },
        vault_root=ROOT,
    )

    assert audit["approval_consumption_proof_path"].endswith("_approval-consumption.json")
    assert len(audit["writebacks"]) == 9
    assert audit["approval_consumption_proof_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["approval_consumption_proof_path"] in audit["proof_card"]["files_written"]
    assert audit["approval_consumption_proof_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["approval_request_artifact_written"] is True
    assert audit["scorecard"]["metrics"]["approval_consumption_proof_written"] is True
    assert audit["scorecard"]["metrics"]["approval_consumed"] is True
    assert audit["scorecard"]["metrics"]["approval_decision"] == "approved"
    assert audit["scorecard"]["metrics"]["external_delivery_approved"] is True
    assert audit["scorecard"]["metrics"]["external_send_performed"] is False
    assert audit["scorecard"]["metrics"]["external_sends"] == 0

    proof = audit["approval_consumption_proof"]
    assert proof["workflow_id"] == "agent_runtime_governance_audit"
    assert proof["run_id"] == "approval-consumption-proof"
    assert proof["status"] == "approval_consumed_no_send"
    assert proof["approval_decision_id"] == "operator-decision-approval-consumption-001"
    assert proof["approval_decision"] == "approved"
    assert proof["approval_consumed"] is True
    assert proof["approval_request_artifact_path"] == audit["approval_request_artifact_path"]
    assert proof["approval_request_run_id"] == "approval-consumption-proof"
    assert len(proof["approval_request_digest_sha256"]) == 64
    assert proof["external_delivery_approved"] is True
    assert proof["external_send_performed"] is False
    assert proof["send_blocked_until_exact_once_gate"] is True
    assert proof["next_required_pass"] == "ventureops-agent-runtime-governance-audit-exact-once-delivery-gate"
    assert proof["forbidden_actions"] == [
        "provider_model_execution",
        "browser_action",
        "external_send",
        "payment_crm_mutation",
        "live_remediation",
        "canonical_state_mutation",
    ]
    proof_json = audit["approval_consumption_proof_json"].lower()
    assert "api_key" not in proof_json
    assert "seed phrase" not in proof_json
    assert "cookie" not in proof_json


def test_agent_runtime_governance_audit_blocks_mismatched_approval_consumption() -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "approval-consumption-mismatch",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "approval_decision_id": "operator-decision-mismatch-001",
                "approval_decision": "approved",
                "approval_request_run_id": "different-request",
            },
            vault_root=ROOT,
        )
    except WorkflowExecutionError as exc:
        assert "does not match approval request" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("mismatched approval request run id was not blocked")


def test_agent_runtime_governance_audit_writes_exact_once_delivery_gate_without_external_send(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "exact-once-delivery-gate",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "approval_decision_id": "operator-decision-exact-once-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "exact-once-delivery-gate",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "none",
        },
        vault_root=tmp_path,
    )

    assert audit["exact_once_delivery_gate_path"].endswith("_exact-once-delivery-gate.json")
    assert audit["delivery_gate_marker_path"].endswith("_delivery-gate-marker.json")
    assert len(audit["writebacks"]) == 11
    writeback_paths = {item["path"] for item in audit["writebacks"]}
    assert audit["exact_once_delivery_gate_path"] in writeback_paths
    assert audit["delivery_gate_marker_path"] in writeback_paths
    assert audit["exact_once_delivery_gate_path"] in audit["scorecard"]["evidence_links"]
    assert audit["delivery_gate_marker_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["exact_once_delivery_gate_written"] is True
    assert audit["scorecard"]["metrics"]["delivery_gate_marker_written"] is True
    assert audit["scorecard"]["metrics"]["approval_consumed"] is True
    assert audit["scorecard"]["metrics"]["external_send_performed"] is False
    assert audit["scorecard"]["metrics"]["external_sends"] == 0

    gate = audit["exact_once_delivery_gate"]
    marker = audit["delivery_gate_marker"]
    assert gate["status"] == "exact_once_gate_reserved_no_send"
    assert gate["approval_consumption_proof_path"] == audit["approval_consumption_proof_path"]
    assert gate["delivery_gate_marker_path"] == audit["delivery_gate_marker_path"]
    assert gate["duplicate_delivery_attempt_blocked"] is True
    assert gate["external_send_performed"] is False
    assert gate["next_required_pass"] == "ventureops-agent-runtime-governance-audit-external-send-dry-run"
    assert marker["status"] == "reserved"
    assert marker["marker_key"] == gate["marker_key"]
    assert marker["approval_decision_id"] == "operator-decision-exact-once-001"
    assert marker["external_send_performed"] is False
    gate_json = audit["exact_once_delivery_gate_json"].lower()
    marker_json = audit["delivery_gate_marker_json"].lower()
    assert "api_key" not in gate_json
    assert "seed phrase" not in gate_json
    assert "cookie" not in gate_json
    assert "api_key" not in marker_json
    assert "seed phrase" not in marker_json
    assert "cookie" not in marker_json


def test_agent_runtime_governance_audit_blocks_duplicate_exact_once_delivery_gate(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    marker_path = (
        tmp_path
        / "07_LOGS"
        / "Workflow-Proofs"
        / "2026-05-11_agent_runtime_governance_audit_exact-once-delivery-gate_delivery-gate-marker.json"
    )
    _write(marker_path, '{"status":"reserved"}\n')

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "exact-once-delivery-gate",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "approval_decision_id": "operator-decision-exact-once-001",
                "approval_decision": "approved",
                "approval_request_run_id": "exact-once-delivery-gate",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "duplicate delivery gate marker already exists" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("duplicate delivery gate marker was not blocked")


def test_agent_runtime_governance_audit_writes_external_send_dry_run_without_external_send(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "external-send-dry-run",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "include_external_send_dry_run": "true",
            "approval_decision_id": "operator-decision-external-dry-run-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "external-send-dry-run",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "email",
            "external_delivery_channel": "email",
            "external_recipient_label": "Synthetic Client Alpha",
            "external_recipient_route": "client-alpha@example.invalid",
        },
        vault_root=tmp_path,
    )

    assert audit["external_send_dry_run_path"].endswith("_external-send-dry-run.json")
    assert len(audit["writebacks"]) == 12
    assert audit["external_send_dry_run_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["external_send_dry_run_path"] in audit["proof_card"]["files_written"]
    assert audit["external_send_dry_run_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["external_send_dry_run_written"] is True
    assert audit["scorecard"]["metrics"]["external_send_dry_run_passed"] is True
    assert audit["scorecard"]["metrics"]["external_send_performed"] is False
    assert audit["scorecard"]["metrics"]["external_sends"] == 0
    assert audit["scorecard"]["metrics"]["connector_dispatch_performed"] is False

    dry_run = audit["external_send_dry_run"]
    assert dry_run["status"] == "external_send_dry_run_verified_no_send"
    assert dry_run["dry_run"] is True
    assert dry_run["external_send_performed"] is False
    assert dry_run["external_sends"] == 0
    assert dry_run["connector_dispatch_performed"] is False
    assert dry_run["delivery_gate_marker_path"] == audit["delivery_gate_marker_path"]
    assert dry_run["exact_once_delivery_gate_path"] == audit["exact_once_delivery_gate_path"]
    assert dry_run["approval_consumption_proof_path"] == audit["approval_consumption_proof_path"]
    assert dry_run["external_delivery_channel"] == "email"
    assert dry_run["external_recipient_label"] == "Synthetic Client Alpha"
    assert dry_run["recipient_route_digest_sha256"]
    assert "client-alpha@example.invalid" not in audit["external_send_dry_run_json"]
    assert dry_run["next_required_pass"] == "ventureops-agent-runtime-governance-audit-approved-external-send"
    dry_run_json = audit["external_send_dry_run_json"].lower()
    assert "api_key" not in dry_run_json
    assert "seed phrase" not in dry_run_json
    assert "cookie" not in dry_run_json


def test_agent_runtime_governance_audit_blocks_external_send_dry_run_without_exact_once_gate(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "external-send-dry-run-no-gate",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_external_send_dry_run": "true",
                "approval_decision_id": "operator-decision-external-dry-run-001",
                "approval_decision": "approved",
                "approval_request_run_id": "external-send-dry-run-no-gate",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "external send dry-run requires include_exact_once_delivery_gate=true" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("external-send dry-run without exact-once gate was not blocked")


def test_agent_runtime_governance_audit_writes_approved_external_send_proof_without_live_delivery(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "approved-external-send",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "include_external_send_dry_run": "true",
            "include_approved_external_send_proof": "true",
            "approval_decision_id": "operator-decision-approved-send-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "approved-external-send",
            "external_send_approval_id": "operator-approved-send-proof-001",
            "external_send_approval_decision": "approved",
            "external_send_approval_actor": "operator",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "email",
            "external_delivery_channel": "email",
            "external_recipient_label": "Synthetic Client Alpha",
            "external_recipient_route": "client-alpha@example.invalid",
        },
        vault_root=tmp_path,
    )

    assert audit["approved_external_send_proof_path"].endswith("_approved-external-send.json")
    assert len(audit["writebacks"]) == 13
    assert audit["approved_external_send_proof_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["approved_external_send_proof_path"] in audit["proof_card"]["files_written"]
    assert audit["approved_external_send_proof_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["approved_external_send_proof_written"] is True
    assert audit["scorecard"]["metrics"]["external_send_approval_decision"] == "approved"
    assert audit["scorecard"]["metrics"]["local_proof_sink_dispatches"] == 1
    assert audit["scorecard"]["metrics"]["connector_dispatch_performed"] is True
    assert audit["scorecard"]["metrics"]["live_external_send_performed"] is False
    assert audit["scorecard"]["metrics"]["external_send_performed"] is False
    assert audit["scorecard"]["metrics"]["external_sends"] == 0

    proof = audit["approved_external_send_proof"]
    assert proof["status"] == "approved_external_send_proof_recorded_no_live_external_delivery"
    assert proof["external_send_approval_id"] == "operator-approved-send-proof-001"
    assert proof["external_send_approval_decision"] == "approved"
    assert proof["external_send_dry_run_path"] == audit["external_send_dry_run_path"]
    assert proof["delivery_gate_marker_path"] == audit["delivery_gate_marker_path"]
    assert proof["connector_type"] == "local_proof_sink"
    assert proof["connector_dispatch_performed"] is True
    assert proof["local_proof_sink_dispatches"] == 1
    assert proof["live_external_delivery_performed"] is False
    assert proof["external_send_performed"] is False
    assert proof["external_sends"] == 0
    assert proof["raw_recipient_route_persisted"] is False
    assert proof["recipient_route_digest_sha256"] == audit["external_send_dry_run"]["recipient_route_digest_sha256"]
    assert proof["next_required_pass"] == "ventureops-crm-draft-integration"
    proof_json = audit["approved_external_send_proof_json"].lower()
    assert "client-alpha@example.invalid" not in proof_json
    assert "api_key" not in proof_json
    assert "seed phrase" not in proof_json
    assert "cookie" not in proof_json


def test_agent_runtime_governance_audit_blocks_approved_external_send_without_dry_run(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "approved-external-send-no-dry-run",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "include_approved_external_send_proof": "true",
                "approval_decision_id": "operator-decision-approved-send-001",
                "approval_decision": "approved",
                "approval_request_run_id": "approved-external-send-no-dry-run",
                "external_send_approval_id": "operator-approved-send-proof-001",
                "external_send_approval_decision": "approved",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "approved external-send proof requires include_external_send_dry_run=true" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("approved external-send proof without dry-run was not blocked")


def test_agent_runtime_governance_audit_writes_crm_draft_without_crm_mutation(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "crm-draft-integration",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "include_external_send_dry_run": "true",
            "include_approved_external_send_proof": "true",
            "include_crm_draft": "true",
            "approval_decision_id": "operator-decision-crm-draft-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "crm-draft-integration",
            "external_send_approval_id": "operator-approved-send-proof-001",
            "external_send_approval_decision": "approved",
            "external_send_approval_actor": "operator",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "email",
            "external_delivery_channel": "email",
            "external_recipient_label": "Synthetic Client Alpha",
            "external_recipient_route": "client-alpha@example.invalid",
            "crm_system": "local-draft-crm",
            "crm_record_type": "deal",
        },
        vault_root=tmp_path,
    )

    assert audit["crm_draft_path"].endswith("_crm-draft.json")
    assert len(audit["writebacks"]) == 14
    assert audit["crm_draft_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["crm_draft_path"] in audit["proof_card"]["files_written"]
    assert audit["crm_draft_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["crm_draft_written"] is True
    assert audit["scorecard"]["metrics"]["crm_mutation_performed"] is False
    assert audit["scorecard"]["metrics"]["crm_records_mutated"] == 0

    crm = audit["crm_draft"]
    assert crm["status"] == "crm_draft_prepared_no_mutation"
    assert crm["crm_system"] == "local-draft-crm"
    assert crm["crm_record_type"] == "deal"
    assert crm["workflow_id"] == "agent_runtime_governance_audit"
    assert crm["client_scope_path"] == audit["client_scope_path"]
    assert crm["delivery_packet_preview_path"] == audit["delivery_packet_preview_path"]
    assert crm["proof_path"] == audit["proof_path"]
    assert crm["approved_external_send_proof_path"] == audit["approved_external_send_proof_path"]
    assert crm["crm_mutation_performed"] is False
    assert crm["crm_records_mutated"] == 0
    assert crm["approval_required_before_crm_mutation"] is True
    assert crm["next_required_pass"] == "ventureops-payment-invoice-draft-integration"
    crm_json = audit["crm_draft_json"].lower()
    assert "client-alpha@example.invalid" not in crm_json
    assert "api_key" not in crm_json
    assert "seed phrase" not in crm_json
    assert "cookie" not in crm_json


def test_agent_runtime_governance_audit_blocks_crm_draft_without_approved_external_send(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "crm-draft-no-approved-send",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "include_external_send_dry_run": "true",
                "include_crm_draft": "true",
                "approval_decision_id": "operator-decision-crm-draft-001",
                "approval_decision": "approved",
                "approval_request_run_id": "crm-draft-no-approved-send",
                "external_delivery_channel": "email",
                "external_recipient_route": "client-alpha@example.invalid",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "CRM draft requires include_approved_external_send_proof=true" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("CRM draft without approved-send proof was not blocked")


def test_agent_runtime_governance_audit_writes_payment_invoice_draft_without_payment_mutation(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "payment-invoice-draft-integration",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "include_external_send_dry_run": "true",
            "include_approved_external_send_proof": "true",
            "include_crm_draft": "true",
            "include_payment_invoice_draft": "true",
            "approval_decision_id": "operator-decision-payment-draft-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "payment-invoice-draft-integration",
            "external_send_approval_id": "operator-approved-send-proof-001",
            "external_send_approval_decision": "approved",
            "external_send_approval_actor": "operator",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "email",
            "external_delivery_channel": "email",
            "external_recipient_label": "Synthetic Client Alpha",
            "external_recipient_route": "client-alpha@example.invalid",
            "crm_system": "local-draft-crm",
            "crm_record_type": "deal",
            "payment_system": "local-draft-invoice",
            "invoice_record_type": "invoice",
            "invoice_currency": "USD",
            "invoice_amount": "0.00",
        },
        vault_root=tmp_path,
    )

    assert audit["payment_invoice_draft_path"].endswith("_payment-invoice-draft.json")
    assert len(audit["writebacks"]) == 15
    assert audit["payment_invoice_draft_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["payment_invoice_draft_path"] in audit["proof_card"]["files_written"]
    assert audit["payment_invoice_draft_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["payment_invoice_draft_written"] is True
    assert audit["scorecard"]["metrics"]["payment_mutation_performed"] is False
    assert audit["scorecard"]["metrics"]["payment_records_mutated"] == 0
    assert audit["scorecard"]["metrics"]["invoices_sent"] == 0

    payment = audit["payment_invoice_draft"]
    assert payment["status"] == "payment_invoice_draft_prepared_no_mutation"
    assert payment["payment_system"] == "local-draft-invoice"
    assert payment["invoice_record_type"] == "invoice"
    assert payment["invoice_currency"] == "USD"
    assert payment["invoice_amount"] == "0.00"
    assert payment["workflow_id"] == "agent_runtime_governance_audit"
    assert payment["client_scope_path"] == audit["client_scope_path"]
    assert payment["delivery_packet_preview_path"] == audit["delivery_packet_preview_path"]
    assert payment["proof_path"] == audit["proof_path"]
    assert payment["crm_draft_path"] == audit["crm_draft_path"]
    assert payment["approved_external_send_proof_path"] == audit["approved_external_send_proof_path"]
    assert payment["payment_mutation_performed"] is False
    assert payment["payment_records_mutated"] == 0
    assert payment["invoices_sent"] == 0
    assert payment["approval_required_before_payment_mutation"] is True
    assert payment["approval_required_before_invoice_send"] is True
    assert payment["next_required_pass"] == "ventureops-workflow-exchange-publication-preview"
    payment_json = audit["payment_invoice_draft_json"].lower()
    assert "client-alpha@example.invalid" not in payment_json
    assert "api_key" not in payment_json
    assert "seed phrase" not in payment_json
    assert "cookie" not in payment_json


def test_agent_runtime_governance_audit_blocks_payment_invoice_draft_without_crm_draft(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "payment-draft-no-crm",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "include_external_send_dry_run": "true",
                "include_approved_external_send_proof": "true",
                "include_payment_invoice_draft": "true",
                "approval_decision_id": "operator-decision-payment-draft-001",
                "approval_decision": "approved",
                "approval_request_run_id": "payment-draft-no-crm",
                "external_send_approval_id": "operator-approved-send-proof-001",
                "external_send_approval_decision": "approved",
                "external_delivery_channel": "email",
                "external_recipient_route": "client-alpha@example.invalid",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "payment/invoice draft requires include_crm_draft=true" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("payment/invoice draft without CRM draft was not blocked")


def test_agent_runtime_governance_audit_writes_workflow_exchange_publication_preview_without_publication(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "workflow-exchange-publication-preview",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "include_external_send_dry_run": "true",
            "include_approved_external_send_proof": "true",
            "include_crm_draft": "true",
            "include_payment_invoice_draft": "true",
            "include_workflow_exchange_publication_preview": "true",
            "approval_decision_id": "operator-decision-publication-preview-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "workflow-exchange-publication-preview",
            "external_send_approval_id": "operator-approved-send-proof-001",
            "external_send_approval_decision": "approved",
            "external_send_approval_actor": "operator",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "email",
            "external_delivery_channel": "email",
            "external_recipient_label": "Synthetic Client Alpha",
            "external_recipient_route": "client-alpha@example.invalid",
            "crm_system": "local-draft-crm",
            "crm_record_type": "deal",
            "payment_system": "local-draft-invoice",
            "invoice_record_type": "invoice",
            "invoice_currency": "USD",
            "invoice_amount": "0.00",
            "publication_surface": "workflow-exchange-preview",
            "listing_visibility": "draft-private",
        },
        vault_root=tmp_path,
    )

    assert audit["workflow_exchange_publication_preview_path"].endswith("_workflow-exchange-publication-preview.json")
    assert len(audit["writebacks"]) == 16
    assert audit["workflow_exchange_publication_preview_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["workflow_exchange_publication_preview_path"] in audit["proof_card"]["files_written"]
    assert audit["workflow_exchange_publication_preview_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["workflow_exchange_publication_preview_written"] is True
    assert audit["scorecard"]["metrics"]["marketplace_publication_performed"] is False
    assert audit["scorecard"]["metrics"]["public_listing_created"] is False
    assert audit["scorecard"]["metrics"]["workflow_pack_examples_detected"] >= 2
    assert audit["scorecard"]["metrics"]["revenue_claim_made"] is False

    preview = audit["workflow_exchange_publication_preview"]
    assert preview["status"] == "publication_preview_prepared_no_publication"
    assert preview["publication_surface"] == "workflow-exchange-preview"
    assert preview["listing_visibility"] == "draft-private"
    assert preview["workflow_pack_examples_detected"] >= 2
    assert preview["workflow_pack_supply_verified"] is True
    assert preview["payment_invoice_draft_path"] == audit["payment_invoice_draft_path"]
    assert preview["crm_draft_path"] == audit["crm_draft_path"]
    assert preview["proof_path"] == audit["proof_path"]
    assert preview["marketplace_publication_performed"] is False
    assert preview["public_listing_created"] is False
    assert preview["revenue_claim_made"] is False
    assert preview["approval_required_before_publication"] is True
    assert preview["next_required_pass"] == "ventureops-live-client-scope-proof"
    preview_json = audit["workflow_exchange_publication_preview_json"].lower()
    assert "client-alpha@example.invalid" not in preview_json
    assert "api_key" not in preview_json
    assert "seed phrase" not in preview_json
    assert "cookie" not in preview_json


def test_agent_runtime_governance_audit_blocks_workflow_exchange_preview_without_payment_invoice_draft(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "publication-preview-no-payment",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "include_external_send_dry_run": "true",
                "include_approved_external_send_proof": "true",
                "include_crm_draft": "true",
                "include_workflow_exchange_publication_preview": "true",
                "approval_decision_id": "operator-decision-publication-preview-001",
                "approval_decision": "approved",
                "approval_request_run_id": "publication-preview-no-payment",
                "external_send_approval_id": "operator-approved-send-proof-001",
                "external_send_approval_decision": "approved",
                "external_delivery_channel": "email",
                "external_recipient_route": "client-alpha@example.invalid",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "Workflow Exchange publication preview requires include_payment_invoice_draft=true" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("Workflow Exchange preview without payment/invoice draft was not blocked")


def test_agent_runtime_governance_audit_writes_live_client_scope_contract_without_live_client_run(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "live-client-scope-contract",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "include_external_send_dry_run": "true",
            "include_approved_external_send_proof": "true",
            "include_crm_draft": "true",
            "include_payment_invoice_draft": "true",
            "include_workflow_exchange_publication_preview": "true",
            "include_live_client_scope_contract": "true",
            "approval_decision_id": "operator-decision-live-client-contract-001",
            "approval_decision": "approved",
            "approval_decision_actor": "operator",
            "approval_request_run_id": "live-client-scope-contract",
            "external_send_approval_id": "operator-approved-send-proof-001",
            "external_send_approval_decision": "approved",
            "external_send_approval_actor": "operator",
            "client_label": "Synthetic Client Alpha",
            "engagement_type": "runtime governance audit",
            "approved_use": "internal review only",
            "delivery_channels": "email",
            "external_delivery_channel": "email",
            "external_recipient_label": "Synthetic Client Alpha",
            "external_recipient_route": "client-alpha@example.invalid",
            "crm_system": "local-draft-crm",
            "crm_record_type": "deal",
            "payment_system": "local-draft-invoice",
            "invoice_record_type": "invoice",
            "invoice_currency": "USD",
            "invoice_amount": "0.00",
            "publication_surface": "workflow-exchange-preview",
            "listing_visibility": "draft-private",
        },
        vault_root=tmp_path,
    )

    assert audit["live_client_scope_contract_path"].endswith("_live-client-scope-contract.json")
    assert len(audit["writebacks"]) == 17
    assert audit["live_client_scope_contract_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["live_client_scope_contract_path"] in audit["proof_card"]["files_written"]
    assert audit["live_client_scope_contract_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["live_client_scope_contract_written"] is True
    assert audit["scorecard"]["metrics"]["live_client_scope_proof_performed"] is False
    assert audit["scorecard"]["metrics"]["real_client_scope_present"] is False
    assert audit["scorecard"]["metrics"]["live_client_data_ingested"] is False

    contract = audit["live_client_scope_contract"]
    assert contract["status"] == "blocked_real_client_scope_required"
    assert contract["workflow_exchange_publication_preview_path"] == audit["workflow_exchange_publication_preview_path"]
    assert contract["real_client_scope_present"] is False
    assert contract["live_client_scope_proof_performed"] is False
    assert contract["live_client_data_ingested"] is False
    assert contract["real_client_scope_required"] is True
    assert contract["approval_required_before_live_client_run"] is True
    assert contract["next_required_pass"] == "ventureops-live-client-scope-proof"
    contract_json = audit["live_client_scope_contract_json"].lower()
    assert "client-alpha@example.invalid" not in contract_json
    assert "api_key" not in contract_json
    assert "seed phrase" not in contract_json
    assert "cookie" not in contract_json


def test_agent_runtime_governance_audit_blocks_live_client_scope_contract_without_publication_preview(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "live-contract-no-preview",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "include_external_send_dry_run": "true",
                "include_approved_external_send_proof": "true",
                "include_crm_draft": "true",
                "include_payment_invoice_draft": "true",
                "include_live_client_scope_contract": "true",
                "approval_decision_id": "operator-decision-live-client-contract-001",
                "approval_decision": "approved",
                "approval_request_run_id": "live-contract-no-preview",
                "external_send_approval_id": "operator-approved-send-proof-001",
                "external_send_approval_decision": "approved",
                "external_delivery_channel": "email",
                "external_recipient_route": "client-alpha@example.invalid",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "live client scope contract requires include_workflow_exchange_publication_preview=true" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("live client scope contract without publication preview was not blocked")


def test_agent_runtime_governance_audit_writes_live_client_scope_proof_gate_from_scope_evidence(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)
    _write_valid_scope_packet(tmp_path)

    audit = build_agent_runtime_governance_audit(
        inputs={
            "run_id": "live-client-scope-proof-gate",
            "date": "2026-05-11",
            "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
            "include_offer_packet": "true",
            "include_delivery_approval_contract": "true",
            "include_delivery_packet_preview": "true",
            "include_approval_request_artifact": "true",
            "include_approval_consumption_proof": "true",
            "include_exact_once_delivery_gate": "true",
            "include_external_send_dry_run": "true",
            "include_approved_external_send_proof": "true",
            "include_crm_draft": "true",
            "include_payment_invoice_draft": "true",
            "include_workflow_exchange_publication_preview": "true",
            "include_live_client_scope_contract": "true",
            "include_live_client_scope_proof_gate": "true",
            "real_client_scope_evidence_path": "runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json",
            "approval_decision_id": "operator-decision-live-client-gate-001",
            "approval_decision": "approved",
            "approval_request_run_id": "live-client-scope-proof-gate",
            "external_send_approval_id": "operator-approved-send-proof-001",
            "external_send_approval_decision": "approved",
            "external_delivery_channel": "email",
            "external_recipient_route": "client-alpha@example.invalid",
        },
        vault_root=tmp_path,
    )

    assert audit["live_client_scope_proof_gate_path"].endswith("_live-client-scope-proof-gate.json")
    assert len(audit["writebacks"]) == 18
    assert audit["live_client_scope_proof_gate_path"] in {item["path"] for item in audit["writebacks"]}
    assert audit["live_client_scope_proof_gate_path"] in audit["proof_card"]["files_written"]
    assert audit["live_client_scope_proof_gate_path"] in audit["scorecard"]["evidence_links"]
    assert audit["scorecard"]["metrics"]["live_client_scope_proof_gate_written"] is True
    assert audit["scorecard"]["metrics"]["real_client_scope_present"] is True
    assert audit["scorecard"]["metrics"]["real_client_scope_approved"] is True
    assert audit["scorecard"]["metrics"]["live_client_scope_proof_performed"] is False
    assert audit["scorecard"]["metrics"]["live_client_data_ingested"] is False
    assert audit["scorecard"]["metrics"]["live_external_delivery_performed"] is False

    gate = audit["live_client_scope_proof_gate"]
    assert gate["status"] == "real_client_scope_evidence_validated_no_live_client_run"
    assert gate["real_client_scope_evidence_path"] == "runtime/ventureops/fixtures/scope-evidence/client-alpha-scope.json"
    assert gate["client_approved_scope_id"] == "scope-client-alpha-001"
    assert gate["approved_read_path_count"] == 2
    assert gate["approved_read_paths_validated"] is True
    assert gate["live_client_scope_proof_performed"] is False
    assert gate["live_client_data_ingested"] is False
    assert gate["next_required_pass"] == "ventureops-live-client-scope-proof"
    gate_json = audit["live_client_scope_proof_gate_json"].lower()
    assert "client-alpha@example.invalid" not in gate_json
    assert "api_key" not in gate_json
    assert "seed phrase" not in gate_json
    assert "cookie" not in gate_json


def test_agent_runtime_governance_audit_blocks_live_client_scope_proof_gate_without_scope_evidence(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "live-client-gate-no-scope",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "include_external_send_dry_run": "true",
                "include_approved_external_send_proof": "true",
                "include_crm_draft": "true",
                "include_payment_invoice_draft": "true",
                "include_workflow_exchange_publication_preview": "true",
                "include_live_client_scope_contract": "true",
                "include_live_client_scope_proof_gate": "true",
                "approval_decision_id": "operator-decision-live-client-gate-001",
                "approval_decision": "approved",
                "approval_request_run_id": "live-client-gate-no-scope",
                "external_send_approval_id": "operator-approved-send-proof-001",
                "external_send_approval_decision": "approved",
                "external_delivery_channel": "email",
                "external_recipient_route": "client-alpha@example.invalid",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "real_client_scope_evidence_path is required" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("live client scope proof gate without scope evidence was not blocked")


def test_agent_runtime_governance_audit_blocks_live_client_scope_proof_gate_with_secret_like_scope_paths(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)
    scope_path = tmp_path / "runtime" / "ventureops" / "fixtures" / "scope-evidence" / "unsafe-scope.json"
    _write(
        scope_path,
        json.dumps(
            {
                "type": "ventureops-real-client-scope-evidence",
                "client_approved_scope_id": "scope-client-alpha-unsafe",
                "client_label": "Synthetic Client Alpha",
                "approval_id": "operator-real-client-scope-approval-unsafe",
                "approval_status": "approved",
                "approved_read_paths": [".env"],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
            },
            indent=2,
        ),
    )

    try:
        build_agent_runtime_governance_audit(
            inputs={
                "run_id": "live-client-gate-unsafe-scope",
                "date": "2026-05-11",
                "source_paths": SYNTHETIC_CLIENT_SOURCE_PATHS,
                "include_offer_packet": "true",
                "include_delivery_approval_contract": "true",
                "include_delivery_packet_preview": "true",
                "include_approval_request_artifact": "true",
                "include_approval_consumption_proof": "true",
                "include_exact_once_delivery_gate": "true",
                "include_external_send_dry_run": "true",
                "include_approved_external_send_proof": "true",
                "include_crm_draft": "true",
                "include_payment_invoice_draft": "true",
                "include_workflow_exchange_publication_preview": "true",
                "include_live_client_scope_contract": "true",
                "include_live_client_scope_proof_gate": "true",
                "real_client_scope_evidence_path": "runtime/ventureops/fixtures/scope-evidence/unsafe-scope.json",
                "approval_decision_id": "operator-decision-live-client-gate-001",
                "approval_decision": "approved",
                "approval_request_run_id": "live-client-gate-unsafe-scope",
                "external_send_approval_id": "operator-approved-send-proof-001",
                "external_send_approval_decision": "approved",
                "external_delivery_channel": "email",
                "external_recipient_route": "client-alpha@example.invalid",
            },
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "scope evidence contains unsafe approved_read_paths" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("unsafe live client scope proof gate was not blocked")


def test_agent_runtime_governance_audit_blocks_secret_like_source_paths(tmp_path: Path) -> None:
    from runtime.workflows.agent_runtime_governance_audit import WorkflowExecutionError, build_agent_runtime_governance_audit

    _write(tmp_path / "CLAUDE.md", "fixture\n")
    try:
        build_agent_runtime_governance_audit(
            inputs={"source_paths": [".env"]},
            vault_root=tmp_path,
        )
    except WorkflowExecutionError as exc:
        assert "refuses secret-like source path" in str(exc)
    else:  # pragma: no cover - the assertion above is the behavior under test
        raise AssertionError("secret-like source path was not blocked")


def test_agent_runtime_governance_audit_executes_through_aor_and_writes_proof(tmp_path: Path) -> None:
    from runtime.aor.engine import run_workflow

    _seed_aor_fixture(tmp_path)

    result = run_workflow(
        "agent_runtime_governance_audit",
        inputs={"run_id": "fixture-real-workflow", "date": "2026-05-10"},
        vault_root=tmp_path,
        dry_run=False,
        runtime_id="codex",
    )

    assert result.status == "success", result
    files_written = result.outputs["writeback"]["files_written"]
    proof_paths = [path for path in files_written if path.startswith("07_LOGS/Workflow-Proofs/")]
    assert len(proof_paths) == 3
    proof_path = next(path for path in proof_paths if path.endswith("fixture-real-workflow.md"))
    report_path = next(path for path in proof_paths if path.endswith("fixture-real-workflow_client-report.md"))
    scorecard_path = next(path for path in proof_paths if path.endswith("fixture-real-workflow_scorecard.json"))
    proof = (tmp_path / proof_path).read_text(encoding="utf-8")
    report = (tmp_path / report_path).read_text(encoding="utf-8")
    scorecard = json.loads((tmp_path / scorecard_path).read_text(encoding="utf-8"))
    assert "Agent Runtime Governance Audit" in proof
    assert "Real Source Ingestion" in proof
    assert "06_AGENTS/Permission-Matrix.md" in proof
    assert "Live trading execution: blocked" in proof
    assert "Client-Safe Agent Runtime Governance Audit Report" in report
    assert scorecard["status"] == "internal_run_passed"
    assert scorecard["evidence_links"] == [proof_path, report_path]


def test_ventureops_ai_runtime_security_audit_executes_through_aor_and_writes_proof(tmp_path: Path) -> None:
    from runtime.aor.engine import run_workflow

    _seed_aor_fixture(tmp_path)

    result = run_workflow(
        "ventureops_ai_runtime_security_audit",
        inputs={"run_id": "fixture-security-audit", "date": "2026-05-13"},
        vault_root=tmp_path,
        dry_run=False,
        runtime_id="codex",
    )

    assert result.status == "success", result
    assert result.outputs["role_card"] == "security_reviewer"
    files_written = result.outputs["writeback"]["files_written"]
    proof_paths = [path for path in files_written if path.startswith("07_LOGS/Workflow-Proofs/")]
    assert len(proof_paths) == 3
    proof_path = next(path for path in proof_paths if path.endswith("fixture-security-audit.md"))
    report_path = next(path for path in proof_paths if path.endswith("fixture-security-audit_client-report.md"))
    scorecard_path = next(path for path in proof_paths if path.endswith("fixture-security-audit_scorecard.json"))
    assert "ventureops_ai_runtime_security_audit" in proof_path
    proof = (tmp_path / proof_path).read_text(encoding="utf-8")
    report = (tmp_path / report_path).read_text(encoding="utf-8")
    scorecard = json.loads((tmp_path / scorecard_path).read_text(encoding="utf-8"))
    assert "workflow_id: ventureops_ai_runtime_security_audit" in proof
    assert "Agent Runtime Governance Audit" in proof
    assert "Client-Safe Agent Runtime Governance Audit Report" in report
    assert scorecard["workflow_id"] == "ventureops_ai_runtime_security_audit"
    assert scorecard["status"] == "internal_run_passed"
    assert scorecard["metrics"]["provider_calls"] == 0
    assert scorecard["metrics"]["external_sends"] == 0


def test_ventureops_live_client_scope_proof_cli_requires_execute_flag(tmp_path: Path) -> None:
    _seed_aor_fixture(tmp_path)
    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)
    scope_path = _write_valid_scope_packet(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "live-client-scope-proof",
            "--vault-root",
            str(tmp_path),
            "--scope-packet",
            str(scope_path),
            "--run-id",
            "live-client-scope-proof-cli-no-execute",
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert "requires --execute-proof" in result["error"]
    assert result["live_client_scope_proof_gate_written"] is False
    assert result["external_send_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["payment_mutation_performed"] is False


def test_ventureops_live_client_scope_proof_cli_writes_guarded_scope_gate(tmp_path: Path) -> None:
    _seed_aor_fixture(tmp_path)
    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)
    scope_path = _write_valid_scope_packet(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "live-client-scope-proof",
            "--vault-root",
            str(tmp_path),
            "--scope-packet",
            str(scope_path),
            "--run-id",
            "live-client-scope-proof-cli",
            "--date",
            "2026-05-11",
            "--execute-proof",
            "--json",
        ],
    )

    assert result["ok"] is True
    assert result["workflow_status"] == "success"
    assert result["writes_performed"] is True
    assert result["live_client_scope_proof_gate_written"] is True
    assert result["live_client_scope_proof_performed"] is False
    assert result["live_client_data_ingested"] is False
    assert result["live_external_delivery_performed"] is False
    assert result["external_send_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False
    assert result["proof_gate_path"].endswith("_live-client-scope-proof-gate.json")
    assert result["proof_gate_path"] in result["files_written"]

    gate = json.loads((tmp_path / result["proof_gate_path"]).read_text(encoding="utf-8"))
    assert gate["status"] == "real_client_scope_evidence_validated_no_live_client_run"
    assert gate["client_approved_scope_id"] == "scope-client-alpha-001"
    assert gate["approved_read_path_count"] == 2
    assert gate["live_client_scope_proof_performed"] is False
    assert gate["live_client_data_ingested"] is False


def test_ventureops_live_client_workflow_proof_cli_requires_execute_flag(tmp_path: Path) -> None:
    _seed_aor_fixture(tmp_path)
    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)
    scope_path = _write_valid_scope_packet(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "live-client-workflow-proof",
            "--vault-root",
            str(tmp_path),
            "--scope-packet",
            str(scope_path),
            "--run-id",
            "live-client-workflow-proof-no-execute",
            "--json",
        ],
        expected_exit=1,
    )

    assert result["ok"] is False
    assert "requires --execute-proof" in result["error"]
    assert result["live_client_workflow_proof_written"] is False
    assert result["external_send_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["payment_mutation_performed"] is False


def test_ventureops_proof_cli_date_defaults_are_dynamic() -> None:
    parser = cli.build_parser()

    scope_args = parser.parse_args([
        "ventureops",
        "live-client-scope-proof",
        "--scope-packet",
        "scope.json",
    ])
    workflow_args = parser.parse_args([
        "ventureops",
        "live-client-workflow-proof",
        "--scope-packet",
        "scope.json",
    ])
    revenue_args = parser.parse_args([
        "ventureops",
        "live-revenue-proof",
        "--revenue-packet",
        "revenue.json",
        "--live-client-proof-path",
        "proof.json",
    ])

    assert scope_args.date is None
    assert workflow_args.date is None
    assert revenue_args.date is None


def test_ventureops_live_client_workflow_proof_cli_uses_current_date_by_default(tmp_path: Path) -> None:
    _seed_aor_fixture(tmp_path)
    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)
    scope_path = _write_valid_scope_packet(tmp_path)

    result = _run_cli_json([
        "ventureops",
        "live-client-workflow-proof",
        "--vault-root",
        str(tmp_path),
        "--scope-packet",
        str(scope_path),
        "--run-id",
        "current-date",
        "--execute-proof",
        "--json",
    ])

    today = date.today().isoformat()
    proof = json.loads((tmp_path / result["workflow_proof_path"]).read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["workflow_proof_path"].startswith(f"07_LOGS/Workflow-Proofs/{today}_")
    assert proof["date"] == today
    assert proof["live_client_workflow_proof_performed"] is True


def test_ventureops_live_client_workflow_proof_cli_writes_guarded_local_proof(tmp_path: Path) -> None:
    _seed_aor_fixture(tmp_path)
    _seed_synthetic_client_sources(tmp_path)
    _seed_workflow_pack_examples(tmp_path)
    scope_path = _write_valid_scope_packet(tmp_path)

    result = _run_cli_json(
        [
            "ventureops",
            "live-client-workflow-proof",
            "--vault-root",
            str(tmp_path),
            "--scope-packet",
            str(scope_path),
            "--run-id",
            "live-client-workflow-proof-cli",
            "--date",
            "2026-05-11",
            "--execute-proof",
            "--json",
        ],
    )

    assert result["ok"] is True
    assert result["workflow_status"] == "success"
    assert result["live_client_workflow_proof_written"] is True
    assert result["live_client_workflow_proof_performed"] is True
    assert result["scoped_client_data_ingested"] is True
    assert result["broad_client_data_ingested"] is False
    assert result["live_external_delivery_performed"] is False
    assert result["external_send_performed"] is False
    assert result["crm_mutation_performed"] is False
    assert result["payment_mutation_performed"] is False
    assert result["revenue_claim_made"] is False
    assert result["workflow_proof_path"].endswith("_live-client-workflow-proof.json")
    assert result["workflow_proof_path"] in result["files_written"]

    proof = json.loads((tmp_path / result["workflow_proof_path"]).read_text(encoding="utf-8"))
    assert proof["type"] == "ventureops-live-client-workflow-proof"
    assert proof["status"] == "live_client_workflow_proof_written"
    assert proof["client_approved_scope_id"] == "scope-client-alpha-001"
    assert proof["approved_read_path_count"] == 2
    assert proof["source_digest_count"] == 2
    assert proof["scoped_client_data_ingested"] is True
    assert proof["external_send_performed"] is False
