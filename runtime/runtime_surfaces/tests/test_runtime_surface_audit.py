from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from runtime.runtime_surfaces.audit import (
    RuntimeSurfaceAuditError,
    append_route_decision,
    read_route_decision_records,
    route_decision_ledger_path,
)
from runtime.runtime_surfaces.registry import load_runtime_surface_registry
from runtime.runtime_surfaces.router import propose_route


ROOT = Path(__file__).resolve().parents[3]


def test_append_route_decision_writes_jsonl_record(tmp_path):
    registry = load_runtime_surface_registry(ROOT)
    decision = propose_route("code.review", registry=registry)
    ledger = tmp_path / "routing_decisions.jsonl"

    record = append_route_decision(
        decision,
        ledger_path=ledger,
        request_id="req-code-review",
        task_type="code.review",
        decision_id="decision-code-review",
        created_at="2026-05-03T00:00:00Z",
    )
    records = read_route_decision_records(ledger_path=ledger)

    assert record["decision_id"] == "decision-code-review"
    assert record["decision"] == "proposed"
    assert record["selected_surface"] == "agent.codex.bus"
    assert record["execution_performed"] is False
    assert record["ledger_write_performed"] is True
    assert len(records) == 1


def test_append_approval_required_decision_preserves_denial_reason(tmp_path):
    registry = load_runtime_surface_registry(ROOT)
    decision = propose_route("browser.click", registry=registry)
    ledger = tmp_path / "routing_decisions.jsonl"

    record = append_route_decision(decision, ledger_path=ledger)

    assert record["decision"] == "approval_required"
    assert record["selected_surface"] == "browser.operator.playwright"
    assert record["denial_reasons"]
    assert record["gate_required"] is True


def test_append_unknown_decision_records_deny_unknown(tmp_path):
    registry = load_runtime_surface_registry(ROOT)
    decision = propose_route("browser.do_anything", registry=registry)
    ledger = tmp_path / "routing_decisions.jsonl"

    record = append_route_decision(decision, ledger_path=ledger)

    assert record["decision"] == "deny_unknown"
    assert record["selected_surface"] is None
    assert record["candidate_surfaces"] == []


def test_append_refuses_executed_decision(tmp_path):
    registry = load_runtime_surface_registry(ROOT)
    decision = replace(propose_route("code.review", registry=registry), execution_performed=True)

    with pytest.raises(RuntimeSurfaceAuditError, match="execution_performed=true"):
        append_route_decision(decision, ledger_path=tmp_path / "routing_decisions.jsonl")


def test_append_refuses_decision_that_already_reports_ledger_written(tmp_path):
    registry = load_runtime_surface_registry(ROOT)
    decision = replace(propose_route("code.review", registry=registry), ledger_written=True)

    with pytest.raises(RuntimeSurfaceAuditError, match="ledger_written=true"):
        append_route_decision(decision, ledger_path=tmp_path / "routing_decisions.jsonl")


def test_relative_ledger_path_escape_fails_closed(tmp_path):
    registry = load_runtime_surface_registry(ROOT)
    decision = propose_route("code.review", registry=registry)

    with pytest.raises(RuntimeSurfaceAuditError, match="must not escape"):
        append_route_decision(decision, vault_root=tmp_path, ledger_path="../outside.jsonl")


def test_default_ledger_path_is_repo_state_path():
    path = route_decision_ledger_path(ROOT)

    assert path == ROOT / "runtime" / "runtime_surfaces" / "state" / "routing_decisions.jsonl"


def test_initial_repo_ledger_marker_is_not_a_route_decision():
    records = read_route_decision_records(vault_root=ROOT)

    assert records == []


def test_route_decision_record_is_json_serializable(tmp_path):
    registry = load_runtime_surface_registry(ROOT)
    decision = propose_route("provider.fallback_decision", registry=registry)
    record = append_route_decision(decision, ledger_path=tmp_path / "routing_decisions.jsonl")

    encoded = json.dumps(record)

    assert "provider.runtime.rpgl" in encoded
    assert "decision_payload" in encoded
