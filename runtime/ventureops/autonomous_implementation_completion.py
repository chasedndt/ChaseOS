"""Autonomous implementation-completion audit for VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from runtime.ventureops.feature_family_completion_audit import build_feature_family_completion_audit
from runtime.ventureops.validation import (
    audit_external_readiness_completion,
    discover_external_completion_artifacts,
    validate_client_safe_delivery_artifact,
    validate_live_client_workflow_proof_artifact,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
)


LOCAL_SCOPE_PACKET = (
    "07_LOGS/Workflow-Proofs/"
    "2026-05-13_chaseos-internal-runtime-security-audit_scope-evidence.json"
)
LOCAL_LIVE_CLIENT_WORKFLOW_PROOF = (
    "07_LOGS/Workflow-Proofs/"
    "2026-05-13_agent_runtime_governance_audit_"
    "2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_"
    "live-client-workflow-proof.json"
)
LOCAL_CLIENT_SAFE_DELIVERY_ARTIFACT = (
    "07_LOGS/Workflow-Proofs/"
    "2026-05-13_chaseos-internal-runtime-security-audit_client-safe-delivery-artifact.json"
)


CORE_IMPLEMENTATION_FILES = [
    "runtime/ventureops/validation.py",
    "runtime/ventureops/evidence_intake.py",
    "runtime/ventureops/evidence_discovery_preflight.py",
    "runtime/ventureops/live_revenue_readiness.py",
    "runtime/ventureops/live_revenue_proof.py",
    "runtime/ventureops/delivery_proof_packet_builder.py",
    "runtime/ventureops/revenue_evidence_packet_builder.py",
    "runtime/ventureops/final_evidence_bundle_packet_builder.py",
    "runtime/ventureops/final_external_evidence_bundle.py",
    "runtime/ventureops/feature_family_completion_audit.py",
    "runtime/ventureops/mission_runtime_claim_result_gate.py",
    "runtime/ventureops/mission_activation_gate.py",
    "runtime/ventureops/mission_external_client_evidence_gate.py",
    "runtime/studio/ventureops_real_world_usecase_panel.py",
    "runtime/studio/dashboard.py",
    "runtime/studio/desktop_shell_app.py",
    "runtime/studio/shell/frontend/app.js",
    "runtime/cli/ventureops_commands.py",
    "runtime/cli/main.py",
]

CORE_TEST_FILES = [
    "runtime/ventureops/test_ventureops.py",
    "runtime/ventureops/test_mission_runtime_claim_result_and_activation_gates.py",
    "runtime/ventureops/test_mission_external_client_evidence_gate.py",
    "runtime/studio/test_ventureops_real_world_usecase_panel.py",
    "runtime/studio/test_desktop_shell_app.py",
    "runtime/tests/test_studio_dashboard.py",
]

CORE_DOC_FILES = [
    "README.md",
    "ROADMAP.md",
    "00_HOME/Now.md",
    "06_AGENTS/VentureOps-Mission-Mode.md",
    "07_LOGS/Operator-Briefs/2026-05-15-ventureops-studio-real-world-usecase-test-guide.md",
    "07_LOGS/Build-Logs/Build-Logs-Index.md",
    "99_ARCHIVE/Documentation-History/Documentation-History-Index.md",
    "07_LOGS/Daily/Daily-Index.md",
]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json_object(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.is_file():
        return None, [f"missing artifact: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive path for bad local artifacts.
        return None, [f"artifact is not readable JSON: {path}: {exc}"]
    if not isinstance(data, dict):
        return None, [f"artifact is not a JSON object: {path}"]
    return data, []


def _path_status(root: Path, paths: list[str]) -> dict[str, Any]:
    present = [path for path in paths if (root / path).is_file()]
    missing = [path for path in paths if not (root / path).is_file()]
    return {
        "ok": not missing,
        "present_count": len(present),
        "expected_count": len(paths),
        "present": present,
        "missing": missing,
    }


def _contains_all(root: Path, path: str, needles: list[str]) -> dict[str, Any]:
    text = _read_text(root / path)
    missing = [needle for needle in needles if needle not in text]
    return {
        "ok": not missing,
        "path": path,
        "missing_needles": missing,
    }


def _artifact_validation(
    root: Path,
    relative: str,
    validator: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    artifact, load_errors = _load_json_object(root / relative)
    if load_errors:
        return {
            "ok": False,
            "path": relative,
            "errors": load_errors,
        }
    assert artifact is not None
    validation = validator(artifact)
    return {
        "ok": bool(validation.get("ok")),
        "path": relative,
        "errors": list(validation.get("errors") or []),
        "summary": {
            key: value
            for key, value in validation.items()
            if key not in {"ok", "errors", "safe_read_paths"}
        },
    }


def _scope_chain_validation(root: Path) -> dict[str, Any]:
    artifact, load_errors = _load_json_object(root / LOCAL_SCOPE_PACKET)
    if load_errors:
        return {
            "ok": False,
            "path": LOCAL_SCOPE_PACKET,
            "errors": load_errors,
            "approval_artifact_ok": False,
            "source_paths_ok": False,
        }
    assert artifact is not None
    scope = validate_real_client_scope_evidence(artifact)
    approval = validate_scope_evidence_approval_artifact(root, artifact) if scope["ok"] else {
        "ok": False,
        "errors": ["scope evidence invalid; approval reference not trusted"],
    }
    sources = validate_scope_evidence_source_paths(root, scope.get("safe_read_paths") or []) if scope["ok"] else {
        "ok": False,
        "errors": ["scope evidence invalid; source paths not trusted"],
    }
    errors = [
        *[f"scope: {error}" for error in scope.get("errors") or []],
        *[f"approval: {error}" for error in approval.get("errors") or []],
        *[f"source: {error}" for error in sources.get("errors") or []],
    ]
    return {
        "ok": bool(scope.get("ok")) and bool(approval.get("ok")) and bool(sources.get("ok")),
        "path": LOCAL_SCOPE_PACKET,
        "errors": errors,
        "approval_artifact_ok": bool(approval.get("ok")),
        "source_paths_ok": bool(sources.get("ok")),
        "approved_read_path_count": int(scope.get("approved_read_path_count") or 0),
    }


def _real_world_missing_requirements(completion_audit: dict[str, Any]) -> list[str]:
    missing = list(completion_audit.get("missing_requirements") or [])
    if not missing:
        return []
    return [str(item) for item in missing]


def build_autonomous_implementation_completion(vault_root: str | Path = ".") -> dict[str, Any]:
    """Audit whether the VentureOps implementation can complete without operator evidence."""
    root = Path(vault_root).resolve()

    implementation_files = _path_status(root, CORE_IMPLEMENTATION_FILES)
    test_files = _path_status(root, CORE_TEST_FILES)
    doc_files = _path_status(root, CORE_DOC_FILES)
    cli_registration = _contains_all(
        root,
        "runtime/cli/main.py",
        ["autonomous-implementation-completion", "cmd_ventureops_autonomous_implementation_completion"],
    )
    command_contract = _contains_all(
        root,
        "runtime/cli/command_contract.json",
        [
            "\"autonomous-implementation-completion\"",
            "cmd_ventureops_autonomous_implementation_completion",
        ],
    )
    generated_docs = _contains_all(
        root,
        "06_AGENTS/ChaseOS-CLI-Command-Reference.md",
        ["chaseos ventureops autonomous-implementation-completion"],
    )
    focused_tests = _contains_all(
        root,
        "runtime/ventureops/test_ventureops.py",
        [
            "test_autonomous_implementation_completion_marks_feature_implementation_complete_without_operator_evidence",
            "test_autonomous_implementation_completion_cli_blocks_existing_report_path_without_overwrite",
        ],
    )
    studio_dashboard_panel = _contains_all(
        root,
        "runtime/studio/dashboard.py",
        [
            "ventureops_real_world_usecase_panel",
            "_gather_ventureops_real_world_usecase_panel",
        ],
    )
    studio_dashboard_app = _contains_all(
        root,
        "runtime/studio/desktop_shell_app.py",
        [
            "VentureOps real-use test",
            "safe_to_mark_real_world_delivery_revenue_complete",
        ],
    )
    studio_native_shell = _contains_all(
        root,
        "runtime/studio/shell/frontend/app.js",
        [
            "ventureopsHomePanel",
            "VentureOps real-use hardening",
        ],
    )
    studio_operator_guide = _contains_all(
        root,
        "07_LOGS/Operator-Briefs/2026-05-15-ventureops-studio-real-world-usecase-test-guide.md",
        [
            "VentureOps Studio Real-World Use Case Test Guide",
            "safe_to_mark_real_world_delivery_revenue_complete=false",
        ],
    )

    scope_chain = _scope_chain_validation(root)
    live_client = _artifact_validation(
        root,
        LOCAL_LIVE_CLIENT_WORKFLOW_PROOF,
        validate_live_client_workflow_proof_artifact,
    )
    client_safe_delivery = _artifact_validation(
        root,
        LOCAL_CLIENT_SAFE_DELIVERY_ARTIFACT,
        validate_client_safe_delivery_artifact,
    )
    discovery = discover_external_completion_artifacts(root)
    live_client_reference_ok = LOCAL_LIVE_CLIENT_WORKFLOW_PROOF in set(
        discovery.get("valid_live_client_workflow_proof_artifacts") or []
    )

    completion_audit = build_feature_family_completion_audit(root)
    external_readiness = audit_external_readiness_completion(root)
    real_world_complete = bool(completion_audit.get("complete"))
    real_world_missing = _real_world_missing_requirements(completion_audit)
    real_world_gate_preserved = real_world_complete or bool(real_world_missing)

    checks = [
        {
            "id": "core_implementation_files_present",
            "ok": implementation_files["ok"],
            "evidence": implementation_files["present"],
            "missing": implementation_files["missing"],
        },
        {
            "id": "focused_test_files_present",
            "ok": test_files["ok"],
            "evidence": test_files["present"],
            "missing": test_files["missing"],
        },
        {
            "id": "truth_docs_present",
            "ok": doc_files["ok"],
            "evidence": doc_files["present"],
            "missing": doc_files["missing"],
        },
        {
            "id": "cli_command_registered",
            "ok": cli_registration["ok"],
            "evidence": [cli_registration["path"]],
            "missing": cli_registration["missing_needles"],
        },
        {
            "id": "command_contract_registered",
            "ok": command_contract["ok"],
            "evidence": [command_contract["path"]],
            "missing": command_contract["missing_needles"],
        },
        {
            "id": "generated_cli_docs_registered",
            "ok": generated_docs["ok"],
            "evidence": [generated_docs["path"]],
            "missing": generated_docs["missing_needles"],
        },
        {
            "id": "focused_completion_tests_present",
            "ok": focused_tests["ok"],
            "evidence": [focused_tests["path"]],
            "missing": focused_tests["missing_needles"],
        },
        {
            "id": "studio_dashboard_panel_registered",
            "ok": studio_dashboard_panel["ok"],
            "evidence": [studio_dashboard_panel["path"]],
            "missing": studio_dashboard_panel["missing_needles"],
        },
        {
            "id": "studio_dashboard_app_renders_real_use_panel",
            "ok": studio_dashboard_app["ok"],
            "evidence": [studio_dashboard_app["path"]],
            "missing": studio_dashboard_app["missing_needles"],
        },
        {
            "id": "native_studio_dashboard_renders_real_use_panel",
            "ok": studio_native_shell["ok"],
            "evidence": [studio_native_shell["path"]],
            "missing": studio_native_shell["missing_needles"],
        },
        {
            "id": "studio_real_world_usecase_guide_present",
            "ok": studio_operator_guide["ok"],
            "evidence": [studio_operator_guide["path"]],
            "missing": studio_operator_guide["missing_needles"],
        },
        {
            "id": "local_scope_evidence_chain_valid",
            "ok": scope_chain["ok"],
            "evidence": [LOCAL_SCOPE_PACKET],
            "missing": scope_chain["errors"],
        },
        {
            "id": "local_live_client_workflow_proof_valid",
            "ok": live_client["ok"] and live_client_reference_ok,
            "evidence": [LOCAL_LIVE_CLIENT_WORKFLOW_PROOF],
            "missing": [] if live_client["ok"] and live_client_reference_ok else live_client["errors"],
        },
        {
            "id": "client_safe_delivery_artifact_valid",
            "ok": client_safe_delivery["ok"],
            "evidence": [LOCAL_CLIENT_SAFE_DELIVERY_ARTIFACT],
            "missing": client_safe_delivery["errors"],
        },
        {
            "id": "real_world_completion_gate_preserved",
            "ok": real_world_gate_preserved,
            "evidence": ["chaseos ventureops feature-family-completion-audit --json"],
            "missing": [] if real_world_gate_preserved else ["real-world completion state is neither complete nor blocked"],
        },
    ]
    feature_implementation_complete = all(bool(item["ok"]) for item in checks)

    return {
        "ok": True,
        "status": (
            "COMPLETE / AUTONOMOUS IMPLEMENTATION VERIFIED / REAL_WORLD_EVIDENCE_BLOCKED"
            if feature_implementation_complete
            else "PARTIAL / AUTONOMOUS IMPLEMENTATION EVIDENCE INCOMPLETE"
        ),
        "completion_decision": (
            "implementation_complete_real_world_evidence_blocked"
            if feature_implementation_complete and not real_world_complete
            else "implementation_complete_real_world_complete"
            if feature_implementation_complete
            else "implementation_incomplete"
        ),
        "feature_implementation_complete": feature_implementation_complete,
        "safe_to_mark_feature_implementation_complete": feature_implementation_complete,
        "operator_evidence_required_for_tests": False,
        "operator_evidence_required_for_real_world_delivery_revenue": not real_world_complete,
        "real_world_delivery_revenue_complete": real_world_complete,
        "safe_to_mark_real_world_delivery_revenue_complete": real_world_complete,
        "real_world_missing_requirements": real_world_missing,
        "implementation_checks": checks,
        "local_evidence_chain": {
            "scope_evidence": scope_chain,
            "live_client_workflow_proof": {
                **live_client,
                "reference_artifacts_valid": live_client_reference_ok,
            },
            "client_safe_delivery_artifact": client_safe_delivery,
        },
        "external_readiness_summary": {
            "complete": bool(external_readiness.get("complete")),
            "completion_decision": external_readiness.get("completion_decision"),
            "next_required_real_use_pass": external_readiness.get("next_required_real_use_pass"),
            "next_guarded_command": external_readiness.get("next_guarded_command"),
        },
        "feature_family_completion_summary": {
            "complete": real_world_complete,
            "completion_decision": completion_audit.get("completion_decision"),
            "next_required_real_use_pass": completion_audit.get("next_required_real_use_pass"),
            "next_guarded_command": completion_audit.get("next_guarded_command"),
        },
        "truth_boundary": {
            "external_send_performed": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "invoice_sent": False,
            "revenue_claim_made": False,
            "accounting_claim_made": False,
            "credential_or_secret_read_performed": False,
            "canonical_promotion_performed": False,
        },
        "next_recommended_pass": (
            "final-hardening-pass"
            if feature_implementation_complete
            else "repair-autonomous-implementation-completion-evidence"
        ),
        "notes": [
            "Operator evidence is not required to run local tests or complete the implementation lane.",
            "Factual operator delivery and payment evidence are still required before real-world delivery/revenue completion can be marked complete.",
            "This audit intentionally does not weaken the existing final external completion audit.",
        ],
    }
