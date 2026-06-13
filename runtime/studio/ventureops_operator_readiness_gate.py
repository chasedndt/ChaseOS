"""VentureOps Operator Readiness Gate — terminal pass in the Phase 11 activation chain.

Checks:
  1. Local implementation complete — all 10 MVP items covered, Studio surface wired
  2. Studio surface accessible — panel builds without errors
  3. Real-world gate preserved — safe_to_mark_real_world_delivery_revenue_complete=False
  4. External effects absent — no false revenue/delivery claims in the truth boundary

`operator_ready` = checks 1–4 all pass (local chain complete, gate preserved).
`real_world_complete` = check from autonomous_implementation_completion (requires real evidence).

This pass loops to itself as NEXT_RECOMMENDED_PASS until the operator supplies real-world
client + revenue evidence. It does not gate or block normal system operation.

Read-only: no builds, no external calls, no vault mutations, no evidence packets.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.ventureops_operator_readiness_gate.v1"
SURFACE_ID = "ventureops_operator_readiness_gate"
PASS_ID = "ventureops-operator-readiness-gate"
NEXT_RECOMMENDED_PASS = "ventureops-operator-readiness-gate"  # terminal — loops to self


def _now_utc_str() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _all_false(flags: dict[str, Any], names: list[str]) -> bool:
    return all(flags.get(name) is False for name in names)


def build_ventureops_operator_readiness_gate(
    vault_root: str | Path = ".",
) -> dict[str, Any]:
    """Aggregate the VentureOps readiness state into an operator gate report.

    Read-only: no builds, no external calls, no vault mutations, no evidence packets.
    """
    vault = Path(vault_root).resolve()

    # ── Pull VentureOps completion state ─────────────────────────────────────
    try:
        from runtime.ventureops.autonomous_implementation_completion import (
            build_autonomous_implementation_completion,
        )
        completion = build_autonomous_implementation_completion(vault)
        completion_error: str | None = None
    except Exception as exc:
        completion_error = str(exc)[:200]
        completion = {
            "ok": False,
            "feature_implementation_complete": False,
            "real_world_delivery_revenue_complete": False,
            "safe_to_mark_real_world_delivery_revenue_complete": False,
            "real_world_missing_requirements": [f"completion audit unavailable: {completion_error}"],
            "truth_boundary": {},
        }

    # ── Pull Studio panel state ───────────────────────────────────────────────
    try:
        from runtime.studio.ventureops_real_world_usecase_panel import (
            build_ventureops_real_world_usecase_panel,
        )
        panel = build_ventureops_real_world_usecase_panel(vault)
        panel_error: str | None = None
    except Exception as exc:
        panel_error = str(exc)[:200]
        panel = {"ok": False, "hardening_checks": []}

    # ── Extract gate fields ───────────────────────────────────────────────────
    feature_complete = bool(completion.get("feature_implementation_complete"))
    real_world_complete = bool(completion.get("real_world_delivery_revenue_complete"))
    real_world_safe = bool(completion.get("safe_to_mark_real_world_delivery_revenue_complete"))
    real_world_missing: list[str] = list(completion.get("real_world_missing_requirements") or [])
    truth_boundary: dict[str, Any] = (
        completion.get("truth_boundary")
        if isinstance(completion.get("truth_boundary"), dict)
        else {}
    )

    panel_ok = bool(panel.get("ok"))
    hardening_checks: list[dict[str, Any]] = list(panel.get("hardening_checks") or [])
    hardening_passed = sum(1 for c in hardening_checks if c.get("ok"))
    hardening_total = len(hardening_checks)

    real_world_gate_preserved = (
        not real_world_complete
        and not real_world_safe
        and bool(real_world_missing)
    )
    external_effects_clear = _all_false(
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

    # ── Gate checks ───────────────────────────────────────────────────────────
    checks: dict[str, dict[str, Any]] = {
        "local_implementation_complete": {
            "ok": feature_complete,
            "detail": "All 10 MVP implementation items covered and testable locally.",
        },
        "studio_surface_accessible": {
            "ok": panel_ok,
            "detail": "VentureOps Studio panel builds and returns ok=True.",
        },
        "real_world_gate_preserved": {
            "ok": real_world_gate_preserved,
            "detail": (
                "real_world_delivery_revenue_complete=False and "
                "safe_to_mark=False — gate correctly closed until evidence supplied."
            ),
        },
        "external_effects_clear": {
            "ok": external_effects_clear,
            "detail": "No external send, provider call, CRM/payment mutation, or revenue claim reported.",
        },
    }

    check_results = {name: c["ok"] for name, c in checks.items()}
    failing_checks = [name for name, ok in check_results.items() if not ok]
    operator_ready = all(check_results.values())

    # ── Status string ─────────────────────────────────────────────────────────
    if real_world_complete:
        status = "REAL_WORLD_COMPLETE — full VentureOps activation achieved"
    elif operator_ready:
        status = (
            "OPERATOR_READY — local implementation complete, gate preserved; "
            "supply real-world client + revenue evidence to complete"
        )
    else:
        status = f"GATE_INCOMPLETE — {len(failing_checks)} check(s) failing: {', '.join(failing_checks[:2])}"

    # ── Operator notes ────────────────────────────────────────────────────────
    operator_notes: list[str] = []
    if not feature_complete:
        operator_notes.append(
            "VentureOps local implementation is not complete. "
            "Run: python -m runtime.cli.main ventureops autonomous-implementation-completion --json"
        )
    if not panel_ok:
        operator_notes.append(
            "VentureOps Studio panel failed to build. "
            f"Error: {panel_error or 'unknown'}"
        )
    if not real_world_gate_preserved:
        if real_world_complete:
            operator_notes.append(
                "Real-world gate is OPEN — real_world_delivery_revenue_complete=True. "
                "Verify this reflects factual evidence, not a placeholder."
            )
        else:
            operator_notes.append(
                "Real-world gate state is unexpected — "
                "safe_to_mark=True or no missing requirements listed. Inspect the completion audit."
            )
    if real_world_missing:
        operator_notes.append(
            f"To complete VentureOps: supply {len(real_world_missing)} evidence item(s): "
            + "; ".join(real_world_missing[:2])
            + ("..." if len(real_world_missing) > 2 else "")
        )

    return {
        "ok": True,  # probe itself always succeeds
        "operator_ready": operator_ready,
        "real_world_complete": real_world_complete,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc_str(),
        "vault_root": str(vault),
        "status": status,
        "check_results": check_results,
        "failing_checks": failing_checks,
        "checks": checks,
        "summary": {
            "feature_implementation_complete": feature_complete,
            "studio_surface_ok": panel_ok,
            "real_world_gate_preserved": real_world_gate_preserved,
            "external_effects_clear": external_effects_clear,
            "hardening_checks_passed": hardening_passed,
            "hardening_checks_total": hardening_total,
            "real_world_missing_requirement_count": len(real_world_missing),
        },
        "real_world_missing_requirements": real_world_missing,
        "operator_notes": operator_notes,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "authority": {
            "read_only": True,
            "builds_triggered": False,
            "external_calls_made": False,
            "vault_mutations": False,
            "evidence_packets_created": False,
            "revenue_claim_made": False,
        },
        "warnings": (
            [f"completion_error: {completion_error}"] if completion_error else []
        ) + (
            [f"panel_error: {panel_error}"] if panel_error else []
        ),
    }
