"""Append-only audit helpers for ARSL route decisions."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from runtime.runtime_surfaces.router import RuntimeSurfaceRouteDecision


ROUTING_LEDGER_RELATIVE_PATH = Path("runtime/runtime_surfaces/state/routing_decisions.jsonl")


class RuntimeSurfaceAuditError(ValueError):
    """Raised when an ARSL routing ledger operation is invalid or unsafe."""


def route_decision_ledger_path(vault_root: str | Path | None = None) -> Path:
    root = Path(vault_root).resolve() if vault_root is not None else _repo_root()
    return root / ROUTING_LEDGER_RELATIVE_PATH


def append_route_decision(
    decision: RuntimeSurfaceRouteDecision,
    *,
    vault_root: str | Path | None = None,
    ledger_path: str | Path | None = None,
    request_id: str | None = None,
    task_type: str | None = None,
    decision_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Append a route decision record to JSONL without executing the route."""

    if decision.execution_performed:
        raise RuntimeSurfaceAuditError("Refusing to audit a decision that reports execution_performed=true")

    path = _resolve_ledger_path(vault_root=vault_root, ledger_path=ledger_path)
    record = _route_decision_record(
        decision,
        request_id=request_id,
        task_type=task_type,
        decision_id=decision_id,
        created_at=created_at,
    )
    _validate_route_decision_record(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def read_route_decision_records(
    *,
    vault_root: str | Path | None = None,
    ledger_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Read route-decision records from the JSONL ledger.

    Non-decision metadata records are ignored so the ledger can carry a single
    initialization marker while remaining append-only.
    """

    path = _resolve_ledger_path(vault_root=vault_root, ledger_path=ledger_path)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeSurfaceAuditError(f"{path}: invalid JSONL on line {line_number}: {exc}") from exc
        if not isinstance(payload, dict):
            raise RuntimeSurfaceAuditError(f"{path}: line {line_number} must be a JSON object")
        if payload.get("record_type") != "arsl_route_decision":
            continue
        _validate_route_decision_record(payload)
        records.append(payload)
    return records


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _resolve_ledger_path(
    *,
    vault_root: str | Path | None,
    ledger_path: str | Path | None,
) -> Path:
    root = Path(vault_root).resolve() if vault_root is not None else _repo_root()
    if ledger_path is None:
        return route_decision_ledger_path(root)
    candidate = Path(ledger_path)
    if not candidate.is_absolute():
        if ".." in candidate.parts:
            raise RuntimeSurfaceAuditError(f"Ledger path must not escape the repo root: {ledger_path}")
        candidate = root / candidate
    candidate = candidate.resolve()
    if vault_root is not None and not _is_within(candidate, root):
        raise RuntimeSurfaceAuditError(f"Ledger path must stay inside the vault root: {candidate}")
    return candidate


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _route_decision_record(
    decision: RuntimeSurfaceRouteDecision,
    *,
    request_id: str | None,
    task_type: str | None,
    decision_id: str | None,
    created_at: str | None,
) -> dict[str, Any]:
    decision_payload = decision.to_dict()
    return {
        "schema_version": 1,
        "record_type": "arsl_route_decision",
        "decision_id": decision_id or f"arsl-route-{uuid4().hex}",
        "created_at": created_at or _now_utc_iso(),
        "request_id": request_id,
        "task_type": task_type,
        "requested_capability": decision.requested_capability,
        "requested_surface_id": decision.requested_surface_id,
        "candidate_surfaces": list(decision.candidate_surfaces),
        "selected_surface": decision.selected_surface,
        "decision": decision.decision,
        "authority_layer": decision.authority_layer,
        "policy_refs": list(decision.policy_refs),
        "risk_class": decision.risk_class,
        "risk_severity": decision.risk_severity,
        "trust_ceiling": decision.trust_ceiling,
        "approval_required": decision.approval_required,
        "audit_required": decision.audit_required,
        "gate_required": decision.gate_required,
        "denial_reasons": list(decision.denial_reasons),
        "execution_performed": False,
        "ledger_write_performed": True,
        "source_decision_ledger_written": decision.ledger_written,
        "decision_payload": decision_payload,
    }


def _validate_route_decision_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "record_type",
        "decision_id",
        "created_at",
        "requested_capability",
        "candidate_surfaces",
        "decision",
        "policy_refs",
        "denial_reasons",
        "execution_performed",
        "ledger_write_performed",
        "source_decision_ledger_written",
    }
    missing = sorted(required.difference(record))
    if missing:
        raise RuntimeSurfaceAuditError(f"Route decision record missing fields: {missing}")
    if record["schema_version"] != 1:
        raise RuntimeSurfaceAuditError("Route decision record schema_version must be 1")
    if record["record_type"] != "arsl_route_decision":
        raise RuntimeSurfaceAuditError("Route decision record_type must be arsl_route_decision")
    if record["execution_performed"] is not False:
        raise RuntimeSurfaceAuditError("Route decision record must report execution_performed=false")
    if record["source_decision_ledger_written"] is not False:
        raise RuntimeSurfaceAuditError("Route decision source must not already report ledger_written=true")
    if record["ledger_write_performed"] is not True:
        raise RuntimeSurfaceAuditError("Route decision record must report ledger_write_performed=true")
    for field_name in ("candidate_surfaces", "policy_refs", "denial_reasons"):
        if not isinstance(record[field_name], list):
            raise RuntimeSurfaceAuditError(f"Route decision record {field_name} must be a list")
