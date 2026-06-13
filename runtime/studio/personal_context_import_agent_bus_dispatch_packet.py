"""Agent Bus dispatch packet surface for Personal Context Import.

Builds the governed dispatch packet shape for delivering a scoped personal
context reference to a target runtime via the Agent Bus. Shows what would be
dispatched — does NOT write any Agent Bus tasks.

The dispatch packet carries bounded references only: no raw source text, no
full-memory dumps, no Personal Map apply records, no provider calls.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.memory.personal_map import APPLIED_PERSONAL_MAP_GRAPH


MODEL_VERSION = "studio.personal_context_import_agent_bus_dispatch_packet.v1"
SURFACE_ID = "studio_personal_context_import_agent_bus_dispatch_packet"
PASS_ID = "personal-context-import-agent-bus-dispatch-packet"
NEXT_RECOMMENDED_PASS = "personal-context-import-provider-credential-readiness"

_DISPATCH_SENDER = "OpenClaw"
_DISPATCH_RECIPIENTS = ("Hermes", "Archon")
_TASK_TYPE = "personal-context-reference-delivery"
_TASK_PRIORITY = "normal"

_REFERENCE_FIELDS = (
    "personal_operator_index_path",
    "personal_domains_index_path",
    "personal_map_candidate_queue_dir",
    "personal_context_intake_dir",
    "applied_personal_map_graph_path",
    "personal_map_graph_present",
)

_EXCLUDED_FIELDS = (
    "raw_source_text",
    "full_memory_dump",
    "personal_map_apply_records",
    "credential_values",
    "provider_response_bodies",
)

_AUTHORITY = {
    "builds_dispatch_packet_preview": True,
    "agent_bus_task_write_allowed": False,
    "runtime_dispatch_allowed": False,
    "personal_map_apply_allowed": False,
    "canonical_writeback_allowed": False,
    "provider_calls_allowed": False,
    "secret_values_read": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_reference_packet(vault: Path) -> dict[str, Any]:
    graph_path = vault / APPLIED_PERSONAL_MAP_GRAPH
    return {
        "packet_type": "personal_context_reference_packet.v1",
        "generated_at": _now_utc(),
        "source_text_included": False,
        "full_memory_dump_included": False,
        "personal_operator_index_path": "00_HOME/Personal-Operator-Index.md",
        "personal_domains_index_path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "personal_map_candidate_queue_dir": "07_LOGS/Pulse-Decks/memory-candidates/personal-map",
        "personal_context_intake_dir": "03_INPUTS/Personal-Context-Intake",
        "applied_personal_map_graph_path": APPLIED_PERSONAL_MAP_GRAPH.as_posix(),
        "personal_map_graph_present": graph_path.exists(),
        "workspace_mode": "personal_os",
        "runtime_delivery_rules": [
            "Runtimes may read approved context routes.",
            "Runtimes must not infer permission from context availability.",
            "WML supplies mode-aware routing context but does not grant execution authority.",
            "Personal Map candidates must be reviewed/applied before runtime memory use.",
            "Raw context exports must not be injected wholesale into tasks.",
        ],
    }


def _build_task_preview(
    *,
    recipient: str,
    reference_packet: dict[str, Any],
    packet_digest: str,
) -> dict[str, Any]:
    return {
        "task_type": _TASK_TYPE,
        "sender": _DISPATCH_SENDER,
        "recipient": recipient,
        "priority": _TASK_PRIORITY,
        "intent": (
            f"Deliver scoped personal context reference packet to {recipient} for "
            "personal-os workspace task routing."
        ),
        "payload": {
            "personal_context_reference_packet": reference_packet,
            "packet_digest": packet_digest,
            "source_text_included": False,
            "full_memory_dump_included": False,
        },
        "boundary": {
            "raw_source_text_excluded": True,
            "full_memory_dump_excluded": True,
            "personal_map_apply_excluded": True,
            "provider_call_excluded": True,
            "credential_read_excluded": True,
        },
        "agent_bus_task_written": False,
        "dispatch_note": (
            "This is a preview packet only. Actual Agent Bus task write requires a "
            "separate approved dispatch executor (not yet implemented in this pass)."
        ),
    }


def build_personal_context_import_agent_bus_dispatch_packet(
    vault_root: str | Path,
    *,
    target_recipient: str = "Hermes",
) -> dict[str, Any]:
    """Return the Agent Bus dispatch packet preview (read-only, no task written)."""
    vault = Path(vault_root).resolve()
    recipient = str(target_recipient or "Hermes")
    if recipient not in _DISPATCH_RECIPIENTS:
        recipient = "Hermes"

    reference_packet = _build_reference_packet(vault)
    # Digest over stable fields only (exclude generated_at timestamp)
    _stable = {k: v for k, v in reference_packet.items() if k != "generated_at"}
    packet_digest = _sha256_text(_canonical_json(_stable))
    task_preview = _build_task_preview(
        recipient=recipient,
        reference_packet=reference_packet,
        packet_digest=packet_digest,
    )

    # Check for agent bus availability
    bus_config_path = vault / "runtime/agent_bus/bus_config.yaml"
    bus_db_path = vault / "runtime/agent_bus/bus.sqlite"
    bus_available = bus_db_path.exists()

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "status": "dispatch_packet_preview_ready" if bus_available else "dispatch_packet_preview_ready_bus_not_verified",
        "packet_digest": packet_digest,
        "reference_packet": reference_packet,
        "task_preview": task_preview,
        "dispatch_sender": _DISPATCH_SENDER,
        "dispatch_recipients": list(_DISPATCH_RECIPIENTS),
        "target_recipient": recipient,
        "bus_state": {
            "bus_config_present": bus_config_path.exists(),
            "bus_db_present": bus_available,
        },
        "excluded_fields": list(_EXCLUDED_FIELDS),
        "reference_fields": list(_REFERENCE_FIELDS),
        "dispatch_gate_requirements": [
            "approved dispatch executor (not yet built in this pass)",
            "approval_id required",
            "exact dispatch_packet_digest required",
            "operator_approval_statement required",
            "execute=True required",
            "Agent Bus task write allowed only after approval",
        ],
        "authority": dict(_AUTHORITY),
        "agent_bus_task_written": False,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_personal_context_import_agent_bus_dispatch_packet(
    payload: dict[str, Any],
) -> str:
    lines = [
        "Personal Context Import Agent Bus Dispatch Packet",
        f"Status: {payload.get('status')}",
        f"Packet digest: {(payload.get('packet_digest') or 'missing')[:24]}...",
        f"Target recipient: {payload.get('target_recipient')}",
        f"Agent Bus task written: {payload.get('agent_bus_task_written')}",
        f"Bus DB present: {(payload.get('bus_state') or {}).get('bus_db_present')}",
        f"Next recommended pass: {payload.get('next_recommended_pass')}",
    ]
    return "\n".join(lines)
