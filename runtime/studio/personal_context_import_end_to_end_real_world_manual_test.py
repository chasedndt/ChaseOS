"""End-to-end real-world manual-test orchestrator for Personal Context Import.

Runs every Personal Context Import surface in read-only mode and produces a
comprehensive status report the operator can inspect to verify the full import
pipeline is wired correctly before executing any live mutations.

This orchestrator does NOT:
- Execute any approved write (execute=False on all executors)
- Call any provider API
- Write canonical files, Personal Map apply, or runtime memory mutations
- Read or print secret values

The operator can use this output to confirm each lane is functional and identify
exactly which blockers require operator input before live execution.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.personal_context_import_end_to_end_real_world_manual_test.v1"
SURFACE_ID = "studio_personal_context_import_end_to_end_real_world_manual_test"
PASS_ID = "personal-context-import-end-to-end-real-world-manual-test"
NEXT_RECOMMENDED_PASS = "personal-context-import-100-percent-closeout"

_LANES = (
    "personal_context_import",
    "personal_map_apply_readiness",
    "personal_map_approved_apply_executor",
    "runtime_memory_mutation_readiness",
    "runtime_memory_approved_mutation_executor",
    "agent_bus_dispatch_packet",
    "provider_credential_readiness",
    "provider_execution_proof",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _lane_result(
    lane_id: str,
    ok: bool,
    status: str,
    surface: str,
    blockers: list[str],
    next_pass: str | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "lane_id": lane_id,
        "ok": ok,
        "status": status,
        "surface": surface,
        "blockers": blockers,
        "next_recommended_pass": next_pass,
        **(extra or {}),
    }


def run_personal_context_import_end_to_end_manual_test(
    vault_root: str | Path,
) -> dict[str, Any]:
    """Run all Personal Context Import surfaces read-only and return a status report."""
    vault = Path(vault_root).resolve()
    started_at = _now_utc()
    lane_results: list[dict[str, Any]] = []
    total_blockers: list[str] = []
    operator_owned_blockers: list[str] = []

    # Lane 1: Top-level planner surface
    try:
        from runtime.studio.personal_context_import import (
            build_personal_context_import_panel,
        )
        result = build_personal_context_import_panel(vault)
        lane_results.append(_lane_result(
            "personal_context_import",
            ok=result.get("ok", False),
            status=str(result.get("status", "unknown")),
            surface=str(result.get("surface", "")),
            blockers=list(result.get("blockers") or []),
            next_pass=result.get("next_recommended_pass"),
        ))
        if result.get("blockers"):
            total_blockers.extend(result["blockers"])
    except Exception as exc:
        lane_results.append(_lane_result(
            "personal_context_import", False, f"import_error:{exc}",
            "personal_context_import", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"personal_context_import_import_error:{exc}")

    # Lane 2: Personal Map apply readiness
    try:
        from runtime.studio.personal_context_import_personal_map_apply_readiness import (
            build_personal_context_import_personal_map_apply_readiness,
        )
        result = build_personal_context_import_personal_map_apply_readiness(vault)
        lane_results.append(_lane_result(
            "personal_map_apply_readiness",
            ok=result.get("ok", False),
            status=str(result.get("status", "unknown")),
            surface=str(result.get("surface", "")),
            blockers=[result["load_error"]] if result.get("load_error") else [],
            next_pass=result.get("next_recommended_pass"),
            extra={
                "total_candidates": (result.get("candidate_summary") or {}).get("total_candidate_count", 0),
                "approved_candidates": (result.get("candidate_summary") or {}).get("approved_count", 0),
                "readiness_digest_prefix": (result.get("readiness_digest") or "")[:16],
            },
        ))
        if result.get("load_error"):
            total_blockers.append(f"personal_map_load_error:{result['load_error']}")
    except Exception as exc:
        lane_results.append(_lane_result(
            "personal_map_apply_readiness", False, f"import_error:{exc}",
            "personal_map_apply_readiness", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"personal_map_apply_readiness_import_error:{exc}")

    # Lane 3: Personal Map approved apply executor (preview only)
    try:
        from runtime.studio.personal_context_import_personal_map_approved_apply_executor import (
            SURFACE_ID as PMA_SURFACE,
            NEXT_RECOMMENDED_PASS as PMA_NEXT,
            STATUS_BLOCKED,
        )
        lane_results.append(_lane_result(
            "personal_map_approved_apply_executor",
            ok=True,
            status="executor_module_importable",
            surface=PMA_SURFACE,
            blockers=[],
            next_pass=PMA_NEXT,
            extra={"note": "Executor requires approval_id + digest + statement + execute=True for live run"},
        ))
    except Exception as exc:
        lane_results.append(_lane_result(
            "personal_map_approved_apply_executor", False, f"import_error:{exc}",
            "personal_map_approved_apply_executor", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"personal_map_executor_import_error:{exc}")

    # Lane 4: Runtime memory mutation readiness
    try:
        from runtime.studio.personal_context_import_runtime_memory_mutation_readiness import (
            build_personal_context_import_runtime_memory_mutation_readiness,
        )
        result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
        lane_results.append(_lane_result(
            "runtime_memory_mutation_readiness",
            ok=result.get("ok", False),
            status=str(result.get("status", "unknown")),
            surface=str(result.get("surface", "")),
            blockers=[],
            next_pass=result.get("next_recommended_pass"),
            extra={
                "runtimes_needing_mutation": result.get("runtimes_needing_mutation"),
                "mutation_digest_prefix": (result.get("mutation_digest") or "")[:16],
            },
        ))
    except Exception as exc:
        lane_results.append(_lane_result(
            "runtime_memory_mutation_readiness", False, f"import_error:{exc}",
            "runtime_memory_mutation_readiness", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"runtime_memory_mutation_readiness_import_error:{exc}")

    # Lane 5: Runtime memory approved mutation executor (preview only)
    try:
        from runtime.studio.personal_context_import_runtime_memory_approved_mutation_executor import (
            SURFACE_ID as RMM_SURFACE,
            NEXT_RECOMMENDED_PASS as RMM_NEXT,
        )
        lane_results.append(_lane_result(
            "runtime_memory_approved_mutation_executor",
            ok=True,
            status="executor_module_importable",
            surface=RMM_SURFACE,
            blockers=[],
            next_pass=RMM_NEXT,
            extra={"note": "Executor requires approval_id + digest + statement + execute=True for live run"},
        ))
    except Exception as exc:
        lane_results.append(_lane_result(
            "runtime_memory_approved_mutation_executor", False, f"import_error:{exc}",
            "runtime_memory_approved_mutation_executor", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"runtime_memory_executor_import_error:{exc}")

    # Lane 6: Agent Bus dispatch packet
    try:
        from runtime.studio.personal_context_import_agent_bus_dispatch_packet import (
            build_personal_context_import_agent_bus_dispatch_packet,
        )
        result = build_personal_context_import_agent_bus_dispatch_packet(vault)
        bus_state = result.get("bus_state") or {}
        lane_results.append(_lane_result(
            "agent_bus_dispatch_packet",
            ok=result.get("ok", False),
            status=str(result.get("status", "unknown")),
            surface=str(result.get("surface", "")),
            blockers=[],
            next_pass=result.get("next_recommended_pass"),
            extra={
                "target_recipient": result.get("target_recipient"),
                "packet_digest_prefix": (result.get("packet_digest") or "")[:16],
                "bus_db_present": bus_state.get("bus_db_present"),
                "agent_bus_task_written": result.get("agent_bus_task_written"),
            },
        ))
    except Exception as exc:
        lane_results.append(_lane_result(
            "agent_bus_dispatch_packet", False, f"import_error:{exc}",
            "agent_bus_dispatch_packet", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"agent_bus_dispatch_packet_import_error:{exc}")

    # Lane 7: Provider credential readiness
    try:
        from runtime.studio.personal_context_import_provider_credential_readiness import (
            build_personal_context_import_provider_credential_readiness,
        )
        result = build_personal_context_import_provider_credential_readiness(vault)
        cred_blockers = list(result.get("credential_blockers") or [])
        lane_results.append(_lane_result(
            "provider_credential_readiness",
            ok=result.get("ok", False),
            status=str(result.get("status", "unknown")),
            surface=str(result.get("surface", "")),
            blockers=cred_blockers,
            next_pass=result.get("next_recommended_pass"),
            extra={
                "required_credentials_present": result.get("required_credentials_present"),
                "missing_required": result.get("missing_required"),
                "readiness_digest_prefix": (result.get("readiness_digest") or "")[:16],
            },
        ))
        if cred_blockers:
            operator_owned_blockers.extend(cred_blockers)
            total_blockers.extend(cred_blockers)
    except Exception as exc:
        lane_results.append(_lane_result(
            "provider_credential_readiness", False, f"import_error:{exc}",
            "provider_credential_readiness", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"provider_credential_readiness_import_error:{exc}")

    # Lane 8: Provider execution proof (preview only)
    try:
        from runtime.studio.personal_context_import_provider_execution_proof import (
            build_personal_context_import_provider_execution_proof,
        )
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
        proof_blockers: list[str] = []
        if not result.get("credential_present"):
            proof_blockers.append("operator_credential_required:OPENAI_API_KEY")
            operator_owned_blockers.append("provider_execution_proof:OPENAI_API_KEY_NOT_PRESENT")
        lane_results.append(_lane_result(
            "provider_execution_proof",
            ok=result.get("ok", False) or not result.get("credential_present", True),
            status=str(result.get("status", "unknown")),
            surface=str(result.get("surface", "")),
            blockers=proof_blockers,
            next_pass=result.get("next_recommended_pass"),
            extra={
                "credential_present": result.get("credential_present"),
                "provider_call_executed": result.get("provider_call_executed"),
                "has_unblock_packet": result.get("unblock_packet") is not None,
            },
        ))
        if proof_blockers:
            total_blockers.extend(proof_blockers)
    except Exception as exc:
        lane_results.append(_lane_result(
            "provider_execution_proof", False, f"import_error:{exc}",
            "provider_execution_proof", [f"import_error:{exc}"], None,
        ))
        total_blockers.append(f"provider_execution_proof_import_error:{exc}")

    finished_at = _now_utc()
    lanes_ok = sum(1 for r in lane_results if r.get("ok"))
    lanes_total = len(lane_results)
    code_blockers = [b for b in total_blockers if b not in operator_owned_blockers]

    if operator_owned_blockers and code_blockers:
        overall_status = "PARTIAL / CODE_BLOCKERS_AND_OPERATOR_BLOCKERS"
    elif operator_owned_blockers:
        overall_status = "READY_FOR_OPERATOR_INPUT / ALL_CODE_LANES_GREEN"
    elif code_blockers:
        overall_status = "BLOCKED / CODE_ERRORS_REQUIRE_FIX"
    else:
        overall_status = "ALL_LANES_GREEN / MANUAL_TEST_READY"

    return {
        "ok": len(code_blockers) == 0,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "started_at": started_at,
        "finished_at": finished_at,
        "vault_root": str(vault),
        "overall_status": overall_status,
        "lanes_ok": lanes_ok,
        "lanes_total": lanes_total,
        "lane_results": lane_results,
        "total_blockers": total_blockers,
        "operator_owned_blockers": operator_owned_blockers,
        "code_blockers": code_blockers,
        "manual_test_instructions": {
            "step_1_planner": "chaseos studio or python -c 'from runtime.studio.personal_context_import import build_personal_context_import_readiness; ...'",
            "step_2_personal_map": "Review candidates in 07_LOGS/Pulse-Decks/memory-candidates/personal-map/",
            "step_3_apply_readiness": "Call build_personal_context_import_personal_map_apply_readiness(vault_root) to see digest",
            "step_4_apply_executor": "Provide approval_id + exact digest + statement + execute=True to run apply",
            "step_5_runtime_memory": "Call build_personal_context_import_runtime_memory_mutation_readiness(vault_root)",
            "step_6_runtime_executor": "Provide approval_id + exact digest + statement + execute=True to mutate nav maps",
            "step_7_agent_bus": "Call build_personal_context_import_agent_bus_dispatch_packet(vault_root) to preview packet",
            "step_8_provider": "Set OPENAI_API_KEY and call build_personal_context_import_provider_execution_proof(vault_root, execute=True, ...)",
        },
        "authority": {
            "provider_call_executed": False,
            "file_write_executed": False,
            "canonical_writeback_executed": False,
            "personal_map_apply_executed": False,
            "agent_bus_task_written": False,
            "secret_values_read": False,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_personal_context_import_end_to_end_manual_test(
    payload: dict[str, Any],
) -> str:
    lines = [
        "Personal Context Import End-to-End Manual Test",
        f"Overall status: {payload.get('overall_status')}",
        f"Lanes OK: {payload.get('lanes_ok')}/{payload.get('lanes_total')}",
    ]
    for lane in payload.get("lane_results") or []:
        icon = "OK" if lane.get("ok") else "BLOCKED"
        lines.append(f"  [{icon}] {lane['lane_id']}: {lane['status']}")
        for b in lane.get("blockers") or []:
            lines.append(f"         ^ {b}")
    op_blockers = payload.get("operator_owned_blockers") or []
    if op_blockers:
        lines.append("Operator-owned blockers (require operator action):")
        for b in op_blockers:
            lines.append(f"  - {b}")
    code_blockers = payload.get("code_blockers") or []
    if code_blockers:
        lines.append("Code blockers (require implementation fix):")
        for b in code_blockers:
            lines.append(f"  - {b}")
    lines.append(f"Next recommended pass: {payload.get('next_recommended_pass')}")
    return "\n".join(lines)
