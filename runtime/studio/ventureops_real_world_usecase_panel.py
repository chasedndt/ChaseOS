"""Studio-facing VentureOps real-world use case hardening panel."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.ventureops.autonomous_implementation_completion import (
    build_autonomous_implementation_completion,
)


GUIDE_PATH = (
    "07_LOGS/Operator-Briefs/"
    "2026-05-15-ventureops-studio-real-world-usecase-test-guide.md"
)


def _guide_exists(root: Path) -> bool:
    return (root / GUIDE_PATH).is_file()


def _all_false(flags: dict[str, Any], names: list[str]) -> bool:
    return all(flags.get(name) is False for name in names)


def build_ventureops_real_world_usecase_panel(
    vault_root: str | Path = ".",
) -> dict[str, Any]:
    """Return the read-only Studio panel for testing VentureOps safely.

    The panel intentionally separates local implementation readiness from
    factual external delivery/revenue completion. It is a UI contract over the
    existing VentureOps gates; it does not create evidence packets or run an
    external workflow.
    """

    root = Path(vault_root).resolve()
    try:
        completion = build_autonomous_implementation_completion(root)
        completion_error = None
    except Exception as exc:  # noqa: BLE001
        completion_error = str(exc)
        completion = {
            "ok": False,
            "feature_implementation_complete": False,
            "operator_evidence_required_for_tests": False,
            "real_world_delivery_revenue_complete": False,
            "safe_to_mark_real_world_delivery_revenue_complete": False,
            "real_world_missing_requirements": [
                f"autonomous implementation completion audit unavailable: {completion_error}"
            ],
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
            "local_evidence_chain": {},
        }
    truth_boundary = completion.get("truth_boundary") if isinstance(completion.get("truth_boundary"), dict) else {}
    real_world_missing = list(completion.get("real_world_missing_requirements") or [])
    feature_complete = bool(completion.get("feature_implementation_complete"))
    real_world_complete = bool(completion.get("real_world_delivery_revenue_complete"))
    real_world_safe = bool(completion.get("safe_to_mark_real_world_delivery_revenue_complete"))
    local_chain = completion.get("local_evidence_chain") if isinstance(completion.get("local_evidence_chain"), dict) else {}
    guide_exists = _guide_exists(root)
    external_effects_false = _all_false(
        truth_boundary,
        [
            "external_send_performed",
            "provider_call_performed",
            "browser_action_performed",
            "crm_mutation_performed",
            "payment_mutation_performed",
            "invoice_sent",
            "revenue_claim_made",
            "accounting_claim_made",
            "credential_or_secret_read_performed",
            "canonical_promotion_performed",
        ],
    )
    real_world_gate_preserved = (not real_world_complete) and (not real_world_safe) and bool(real_world_missing)

    hardening_checks = [
        {
            "id": "local_implementation_complete",
            "ok": feature_complete,
            "detail": "VentureOps local implementation audit is complete and testable.",
        },
        {
            "id": "operator_evidence_not_required_for_local_tests",
            "ok": completion.get("operator_evidence_required_for_tests") is False,
            "detail": "Local regression and Studio visibility do not need delivery/payment evidence.",
        },
        {
            "id": "real_world_gate_preserved",
            "ok": real_world_gate_preserved,
            "detail": "The UI still blocks delivery/revenue completion until factual evidence exists.",
        },
        {
            "id": "external_effects_false",
            "ok": external_effects_false,
            "detail": "No external send, provider/browser action, CRM/payment mutation, or revenue claim is reported.",
        },
        {
            "id": "operator_guide_path_declared",
            "ok": bool(GUIDE_PATH),
            "detail": GUIDE_PATH,
        },
    ]

    return {
        "ok": True,
        "surface": "studio_ventureops_real_world_usecase_panel",
        "status": (
            "studio_ready_real_world_evidence_blocked"
            if feature_complete and real_world_gate_preserved
            else "studio_ready_real_world_complete"
            if feature_complete and real_world_complete
            else "implementation_incomplete"
        ),
        "headline": "VentureOps real-use hardening",
        "summary": {
            "feature_implementation_complete": feature_complete,
            "operator_evidence_required_for_tests": bool(
                completion.get("operator_evidence_required_for_tests")
            ),
            "real_world_delivery_revenue_complete": real_world_complete,
            "safe_to_mark_real_world_delivery_revenue_complete": real_world_safe,
            "real_world_missing_requirement_count": len(real_world_missing),
            "hardening_check_count": len(hardening_checks),
            "hardening_checks_passed": sum(1 for item in hardening_checks if item.get("ok")),
            "guide_exists": guide_exists,
        },
        "studio_entrypoints": [
            {
                "id": "native_studio_dashboard",
                "label": "Native Studio Dashboard",
                "command": (
                    "python -m runtime.cli.main studio desktop-shell-app "
                    "--host 127.0.0.1 --port 8772"
                ),
                "dry_run_command": (
                    "python -m runtime.cli.main studio desktop-shell-app "
                    "--host 127.0.0.1 --port 8772 --dry-run --json"
                ),
                "url": "http://127.0.0.1:8772/#/dashboard",
            },
            {
                "id": "localhost_dashboard_app",
                "label": "Localhost Studio Dashboard App",
                "command": (
                    "python -m runtime.cli.main studio dashboard-app "
                    "--host 127.0.0.1 --port 8768"
                ),
                "dry_run_command": (
                    "python -m runtime.cli.main studio dashboard-app "
                    "--host 127.0.0.1 --port 8768 --dry-run --json"
                ),
                "url": "http://127.0.0.1:8768/",
            },
        ],
        "real_world_test_usecase": {
            "id": "ai-runtime-governance-audit-client-service",
            "title": "AI Runtime Governance Audit for a client or Chase-owned venture",
            "safe_rehearsal_scope": "Use repo-local scope/proof artifacts to verify the workflow path and Studio state.",
            "actual_real_world_completion_requires": [
                "explicit real client or venture scope approval",
                "typed approved source paths inside the vault root",
                "factual delivery attestation",
                "client-safe delivery artifact",
                "redacted receipt or payment artifact",
                "payment status, amount, currency, and reference",
                "CRM or customer reference when available",
            ],
        },
        "rehearsal_steps": [
            {
                "id": "open_studio_dashboard",
                "operator_action": "Open either Studio Dashboard entrypoint and find the VentureOps real-use hardening section.",
                "expected_result": "The panel is visible without creating evidence or executing external actions.",
            },
            {
                "id": "verify_local_implementation_complete",
                "operator_action": "Confirm feature implementation is complete and local tests do not require operator evidence.",
                "expected_result": "feature_implementation_complete=true and operator_evidence_required_for_tests=false.",
            },
            {
                "id": "verify_real_world_gate_blocked",
                "operator_action": "Confirm real-world delivery/revenue remains blocked.",
                "expected_result": "safe_to_mark_real_world_delivery_revenue_complete=false with missing evidence listed.",
            },
            {
                "id": "run_safe_cli_cross_check",
                "operator_action": "Run the safe CLI cross-check from the panel or guide.",
                "expected_result": "The CLI returns the same implementation-complete / real-world-blocked posture.",
            },
            {
                "id": "only_then_supply_real_evidence",
                "operator_action": "When a real case exists, supply redacted factual evidence through guarded VentureOps commands.",
                "expected_result": "Proof commands either write bounded artifacts or fail closed; no UI shortcut claims revenue.",
            },
        ],
        "safe_commands": [
            "python -m runtime.cli.main ventureops autonomous-implementation-completion --json",
            "python -m runtime.cli.main ventureops feature-family-completion-audit --json",
            "python -m runtime.cli.main ventureops real-evidence-closeout-readiness --json",
            "python -m runtime.cli.main studio dashboard-app --host 127.0.0.1 --port 8768 --dry-run --json",
            "python -m runtime.cli.main studio desktop-shell-app --host 127.0.0.1 --port 8772 --dry-run --json",
        ],
        "operator_guide": {
            "path": GUIDE_PATH,
            "exists": guide_exists,
            "purpose": "Human test guide for a Studio-visible real-world VentureOps use case rehearsal.",
        },
        "hardening_checks": hardening_checks,
        "local_evidence_chain": {
            "scope_evidence_ok": bool((local_chain.get("scope_evidence") or {}).get("ok")),
            "live_client_workflow_proof_ok": bool(
                (local_chain.get("live_client_workflow_proof") or {}).get("ok")
            ),
            "client_safe_delivery_artifact_ok": bool(
                (local_chain.get("client_safe_delivery_artifact") or {}).get("ok")
            ),
        },
        "real_world_missing_requirements": real_world_missing,
        "completion_report": completion,
        "warnings": [completion_error] if completion_error else [],
        "authority": {
            "read_only": True,
            "writes_vault": False,
            "writes_evidence_packets": False,
            "external_send_allowed": False,
            "provider_calls_allowed": False,
            "browser_control_allowed": False,
            "crm_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "invoice_send_allowed": False,
            "revenue_claim_allowed": False,
            "credential_or_secret_read_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }
