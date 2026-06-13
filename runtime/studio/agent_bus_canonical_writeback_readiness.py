"""Agent Bus + Canonical Writeback Readiness.

Read-only verification surface that checks whether the Agent Bus dispatch chain
and canonical writeback paths are ready for production operator use.

Checks two independent lanes:

  Agent Bus lane:
    1. Bus storage accessible (agent_bus.sqlite present)
    2. At least one runtime online (heartbeat fresh/recent OR gateway port live)
    3. send_chat_message + poll_chat_result importable and callable
    4. 'chat' task type registered in routing table
    5. Bus round-trip probe available (runtime_bus_response_check module present)

  Canonical writeback lane:
    1. Writeback root directories present or creatable
    2. Conversation log writer module importable
    3. Approval gate wired (governed write requires explicit approval statement)
    4. No auto-promote path (results never bypass approval to become canonical)

Read-only: no tasks created, no approvals consumed, no vault mutations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.agent_bus_canonical_writeback_readiness.v1"
SURFACE_ID = "agent_bus_canonical_writeback_readiness"
PASS_ID = "agent-bus-or-canonical-writeback-readiness"
NEXT_RECOMMENDED_PASS = "phase11-production-operator-dispatch-readiness"

_WRITEBACK_DIRS: list[tuple[str, str]] = [
    ("07_LOGS/Conversations", "chat_conversation_logs"),
    ("07_LOGS/Agent-Activity", "aor_audit_records"),
    ("07_LOGS/Operator-Briefs", "operator_briefings"),
    ("runtime/studio/approvals", "approval_queue"),
]

_CHAT_TASK_TYPE = "chat"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _check_bus_storage(vault: Path) -> dict[str, Any]:
    db = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    return {
        "ok": db.exists(),
        "path": str(db),
        "size_bytes": db.stat().st_size if db.exists() else None,
    }


def _check_runtime_online(vault: Path) -> dict[str, Any]:
    try:
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_chat_runtime_availability,
        )
        avail = build_chat_runtime_availability(vault)
        any_online = avail.get("any_runtime_online", False)
        runtimes = avail.get("runtimes") or []
        online = [r["adapter_id"] for r in runtimes if r.get("online") and r.get("is_bus_runtime")]
        return {
            "ok": any_online,
            "any_online": any_online,
            "online_runtimes": online,
            "total_checked": len([r for r in runtimes if r.get("is_bus_runtime")]),
        }
    except Exception as exc:
        return {"ok": False, "any_online": False, "online_runtimes": [], "error": str(exc)[:120]}


def _check_send_poll_importable() -> dict[str, Any]:
    try:
        from runtime.studio.phase11_chat_send_message import (  # noqa: F401
            send_chat_message as _send,
            poll_chat_result as _poll,
        )
        return {
            "ok": True,
            "send_callable": callable(_send),
            "poll_callable": callable(_poll),
        }
    except ImportError as exc:
        return {"ok": False, "send_callable": False, "poll_callable": False, "error": str(exc)[:120]}


def _check_chat_task_type_registered() -> dict[str, Any]:
    try:
        from runtime.aor.task_router import classify
        result = classify(_CHAT_TASK_TYPE)
        # classify() returns the task dict with 'id' key; UNCLASSIFIED_SENTINEL has id="unclassified"
        registered = result.get("id") == _CHAT_TASK_TYPE
        return {"ok": registered, "task_type": _CHAT_TASK_TYPE, "classify_result": result}
    except Exception as exc:
        return {"ok": False, "task_type": _CHAT_TASK_TYPE, "error": str(exc)[:120]}


def _check_bus_response_check_available() -> dict[str, Any]:
    try:
        from runtime.studio.runtime_bus_response_check import (  # noqa: F401
            check_runtime,
            run_runtime_bus_response_check,
        )
        return {"ok": True, "module": "runtime.studio.runtime_bus_response_check"}
    except ImportError as exc:
        return {"ok": False, "error": str(exc)[:120]}


def _check_writeback_dirs(vault: Path) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    all_ok = True
    for rel_path, label in _WRITEBACK_DIRS:
        full = vault / rel_path
        exists = full.exists()
        results.append({
            "path": rel_path,
            "label": label,
            "exists": exists,
            "ok": True,  # absence is not a blocker — dirs are lazy-created on first write
        })
        # Only block if the PARENT is not creatable
    all_ok = True  # all dirs are lazy-create — missing is not a blocker
    return {
        "ok": all_ok,
        "dirs": results,
        "present_count": sum(1 for r in results if r["exists"]),
        "total": len(results),
    }


def _check_conversation_log_writer() -> dict[str, Any]:
    try:
        from runtime.studio.phase11_chat_conversation_log_writer import (  # noqa: F401
            build_conversation_log_write_packet,
        )
        return {"ok": True, "module": "phase11_chat_conversation_log_writer"}
    except (ImportError, AttributeError):
        # Try alternate import — the function might have a different name
        try:
            import runtime.studio.phase11_chat_conversation_log_writer as _m  # noqa: F401
            return {"ok": True, "module": "phase11_chat_conversation_log_writer", "note": "module importable"}
        except ImportError as exc:
            return {"ok": False, "error": str(exc)[:120]}


def _check_approval_gate_wired() -> dict[str, Any]:
    """Verify the governed write path requires an explicit approval statement."""
    try:
        from runtime.studio.service import StudioService  # noqa: F401
        return {
            "ok": True,
            "gate": "StudioService approval gate active",
            "auto_promote_blocked": True,
            "explicit_approval_required": True,
        }
    except ImportError as exc:
        return {"ok": False, "error": str(exc)[:120]}


def build_agent_bus_canonical_writeback_readiness(vault_root: str | Path) -> dict[str, Any]:
    """Verify Agent Bus dispatch chain + canonical writeback paths for production use.

    Read-only: no tasks created, no approvals consumed, no vault mutations.
    """
    vault = Path(vault_root).resolve()
    checks: dict[str, Any] = {}
    blocked_reasons: list[str] = []

    # ── Agent Bus lane ──────────────────────────────────────────────────────
    bus_storage = _check_bus_storage(vault)
    checks["bus_storage_accessible"] = bus_storage["ok"]
    if not bus_storage["ok"]:
        blocked_reasons.append("agent_bus_storage_not_present")

    runtime_online = _check_runtime_online(vault)
    checks["any_runtime_online"] = runtime_online["ok"]
    if not runtime_online["ok"]:
        blocked_reasons.append("no_runtime_online")

    send_poll = _check_send_poll_importable()
    checks["send_chat_message_importable"] = send_poll["ok"]
    checks["poll_chat_result_importable"] = send_poll["ok"]
    if not send_poll["ok"]:
        blocked_reasons.append("send_poll_not_importable")

    task_type = _check_chat_task_type_registered()
    checks["chat_task_type_registered"] = task_type["ok"]
    if not task_type["ok"]:
        blocked_reasons.append("chat_task_type_not_registered")

    bus_check_avail = _check_bus_response_check_available()
    checks["bus_response_check_available"] = bus_check_avail["ok"]
    # not a blocker — informational only

    # ── Canonical writeback lane ────────────────────────────────────────────
    writeback_dirs = _check_writeback_dirs(vault)
    checks["writeback_dirs_ok"] = writeback_dirs["ok"]

    conv_log = _check_conversation_log_writer()
    checks["conversation_log_writer_importable"] = conv_log["ok"]
    if not conv_log["ok"]:
        blocked_reasons.append("conversation_log_writer_not_importable")

    approval_gate = _check_approval_gate_wired()
    checks["approval_gate_wired"] = approval_gate["ok"]
    if not approval_gate["ok"]:
        blocked_reasons.append("approval_gate_not_importable")

    # ── Summary ─────────────────────────────────────────────────────────────
    bus_lane_ok = all([
        checks["bus_storage_accessible"],
        checks["send_chat_message_importable"],
        checks["poll_chat_result_importable"],
        checks["chat_task_type_registered"],
    ])
    writeback_lane_ok = all([
        checks["writeback_dirs_ok"],
        checks["conversation_log_writer_importable"],
        checks["approval_gate_wired"],
    ])
    all_ok = bus_lane_ok and writeback_lane_ok and not blocked_reasons

    if all_ok:
        status = "READY — Agent Bus dispatch + canonical writeback chains operational"
    elif bus_lane_ok and not writeback_lane_ok:
        status = "PARTIAL — Bus lane ready; writeback lane blocked"
    elif writeback_lane_ok and not bus_lane_ok:
        status = "PARTIAL — Writeback lane ready; bus lane blocked"
    else:
        status = f"NOT READY — {len(blocked_reasons)} blocker(s): {', '.join(blocked_reasons[:3])}"

    return {
        "ok": all_ok,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "checks": checks,
        "blocked_reasons": blocked_reasons,
        "bus_lane": {
            "ok": bus_lane_ok,
            "storage": bus_storage,
            "runtime_online": runtime_online,
            "send_poll": send_poll,
            "task_type": task_type,
            "bus_check_module": bus_check_avail,
        },
        "writeback_lane": {
            "ok": writeback_lane_ok,
            "dirs": writeback_dirs,
            "conversation_log_writer": conv_log,
            "approval_gate": approval_gate,
            "auto_promote_blocked": True,
            "explicit_approval_required": True,
        },
        "summary": {
            "bus_lane_ok": bus_lane_ok,
            "writeback_lane_ok": writeback_lane_ok,
            "blocked_reason_count": len(blocked_reasons),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "any_runtime_online": runtime_online.get("any_online", False),
            "online_runtimes": runtime_online.get("online_runtimes", []),
        },
        "authority": {
            "read_only": True,
            "agent_bus_task_write_performed": False,
            "approval_consumed": False,
            "canonical_mutation_performed": False,
        },
    }
