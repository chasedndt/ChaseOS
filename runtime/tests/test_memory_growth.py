"""
test_memory_growth.py — Tests for runtime/memory/growth.py

Covers:
  TestNavMapWarm             (9 tests) — warm_nav_map_from_execution
  TestRepairPatterns         (7 tests) — record_repair_pattern + record_incident_candidate
  TestExportMemorySnapshot   (4 tests) — export_memory_snapshot
  TestApplyExecutionToMemory (5 tests) — apply_execution_to_memory orchestrator
  TestEngineWiring           (3 tests) — _GROWTH_AVAILABLE + wiring sanity
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.memory.growth import (
    apply_execution_to_memory,
    export_memory_snapshot,
    record_incident_candidate,
    record_repair_pattern,
    warm_nav_map_from_execution,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


def _success_record(workflow_id: str = "operator_today", reads: list | None = None) -> dict:
    reads = reads or ["00_HOME/Now.md", "01_PROJECTS/ChaseOS/ChaseOS-OS.md"]
    return {
        "audit_id": "audit-001",
        "workflow_id": workflow_id,
        "status": "success",
        "stage_reached": "audit_record",
        "escalation_reason": None,
        "manifest_snapshot": {
            "id": workflow_id,
            "required_reads": reads,
        },
    }


def _escalation_record(workflow_id: str = "operator_today", stage: str = "permission_ceiling") -> dict:
    return {
        "audit_id": "audit-esc",
        "workflow_id": workflow_id,
        "status": "escalated",
        "stage_reached": stage,
        "escalation_reason": "write to protected file attempted",
        "manifest_snapshot": {"id": workflow_id, "required_reads": []},
    }


def _nav_path(vault: Path, runtime_id: str = "test-rt") -> Path:
    return vault / "runtime" / "memory" / "nav" / runtime_id / "nav-map.json"


def _repair_path(vault: Path, runtime_id: str = "test-rt") -> Path:
    return vault / "runtime" / "memory" / "repair" / f"{runtime_id}.json"


# ── TestNavMapWarm ────────────────────────────────────────────────────────────

class TestNavMapWarm:
    def test_creates_nav_map_if_missing(self, tmp_path):
        vault = _make_vault(tmp_path)
        warm_nav_map_from_execution("rt1", vault, _success_record())
        assert _nav_path(vault, "rt1").exists()

    def test_appends_successful_route(self, tmp_path):
        vault = _make_vault(tmp_path)
        warm_nav_map_from_execution("rt1", vault, _success_record())
        data = json.loads(_nav_path(vault, "rt1").read_text())
        patterns = data["successful_route_patterns"]
        assert len(patterns) == 1
        assert patterns[0]["workflow_id"] == "operator_today"
        assert "00_HOME/Now.md" in patterns[0]["reads"]

    def test_appends_escalation_trigger(self, tmp_path):
        vault = _make_vault(tmp_path)
        warm_nav_map_from_execution("rt1", vault, _escalation_record())
        data = json.loads(_nav_path(vault, "rt1").read_text())
        triggers = data["common_escalation_triggers"]
        assert len(triggers) == 1
        assert "protected file" in triggers[0]["reason"]

    def test_no_trigger_for_non_ceiling_escalation(self, tmp_path):
        vault = _make_vault(tmp_path)
        rec = _escalation_record(stage="task_classification")
        warm_nav_map_from_execution("rt1", vault, rec)
        data = json.loads(_nav_path(vault, "rt1").read_text())
        # stage_reached != permission_ceiling, so no trigger appended
        assert data.get("common_escalation_triggers", []) == []

    def test_status_set_to_active(self, tmp_path):
        vault = _make_vault(tmp_path)
        warm_nav_map_from_execution("rt1", vault, _success_record())
        data = json.loads(_nav_path(vault, "rt1").read_text())
        assert data["status"] == "active"

    def test_accumulates_multiple_routes(self, tmp_path):
        vault = _make_vault(tmp_path)
        warm_nav_map_from_execution("rt1", vault, _success_record("wf-a", ["file1.md"]))
        warm_nav_map_from_execution("rt1", vault, _success_record("wf-b", ["file2.md"]))
        data = json.loads(_nav_path(vault, "rt1").read_text())
        assert len(data["successful_route_patterns"]) == 2

    def test_route_cap_enforced(self, tmp_path):
        from runtime.memory.growth import _ROUTE_CAP
        vault = _make_vault(tmp_path)
        for i in range(_ROUTE_CAP + 5):
            warm_nav_map_from_execution("rt1", vault, _success_record(f"wf-{i}", [f"file{i}.md"]))
        data = json.loads(_nav_path(vault, "rt1").read_text())
        assert len(data["successful_route_patterns"]) == _ROUTE_CAP

    def test_preserves_existing_nav_map_fields(self, tmp_path):
        vault = _make_vault(tmp_path)
        path = _nav_path(vault, "rt1")
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "runtime_id": "rt1",
            "version": "0.1",
            "status": "seeded",
            "preferred_read_routes": [{"task_class": "existing", "route": ["x.md"]}],
            "trusted_zones": ["runtime/aor/"],
            "risk_zones": [],
            "successful_route_patterns": [],
        }), encoding="utf-8")
        warm_nav_map_from_execution("rt1", vault, _success_record())
        data = json.loads(path.read_text())
        assert len(data["preferred_read_routes"]) == 1
        assert data["preferred_read_routes"][0]["task_class"] == "existing"

    def test_fail_open_on_corrupt_file(self, tmp_path):
        vault = _make_vault(tmp_path)
        path = _nav_path(vault, "rt1")
        path.parent.mkdir(parents=True)
        path.write_text("CORRUPT JSON!!!", encoding="utf-8")
        # Must not raise
        warm_nav_map_from_execution("rt1", vault, _success_record())


# ── TestRepairPatterns ────────────────────────────────────────────────────────

class TestRepairPatterns:
    def test_creates_repair_file(self, tmp_path):
        vault = _make_vault(tmp_path)
        record_repair_pattern(
            "rt1", vault,
            workflow_id="wf-x",
            failure_context="context_boot failed",
            repair_action="re-seeded Now.md",
            resolved=True,
        )
        assert _repair_path(vault, "rt1").exists()

    def test_appends_pattern(self, tmp_path):
        vault = _make_vault(tmp_path)
        record_repair_pattern(
            "rt1", vault,
            workflow_id="wf-x",
            failure_context="boot failed",
            repair_action="fix",
            resolved=True,
        )
        data = json.loads(_repair_path(vault, "rt1").read_text())
        patterns = data["repair_patterns"]
        assert len(patterns) == 1
        assert patterns[0]["workflow_id"] == "wf-x"
        assert patterns[0]["resolved"] is True

    def test_repair_cap_enforced(self, tmp_path):
        from runtime.memory.growth import _REPAIR_CAP
        vault = _make_vault(tmp_path)
        for i in range(_REPAIR_CAP + 3):
            record_repair_pattern(
                "rt1", vault,
                workflow_id=f"wf-{i}",
                failure_context=f"failure {i}",
                repair_action=f"fix {i}",
                resolved=True,
            )
        data = json.loads(_repair_path(vault, "rt1").read_text())
        assert len(data["repair_patterns"]) == _REPAIR_CAP

    def test_incident_candidate_created(self, tmp_path):
        vault = _make_vault(tmp_path)
        record_incident_candidate(
            "rt1", vault,
            workflow_id="wf-esc",
            outcome="escalated",
            escalation_reason="protected file write",
        )
        data = json.loads(_repair_path(vault, "rt1").read_text())
        candidates = data["incident_candidates"]
        assert len(candidates) == 1
        assert candidates[0]["outcome"] == "escalated"
        assert candidates[0]["operator_reviewed"] is False

    def test_fail_open_on_exception(self, tmp_path):
        vault = _make_vault(tmp_path)
        # Inject a bad path by passing a string as vault_root
        record_repair_pattern(
            "rt1", "not_a_path",  # type: ignore[arg-type]
            workflow_id="wf",
            failure_context="test",
            repair_action="none",
            resolved=False,
        )

    def test_status_set_to_active(self, tmp_path):
        vault = _make_vault(tmp_path)
        record_repair_pattern(
            "rt1", vault,
            workflow_id="wf",
            failure_context="test",
            repair_action="fix",
            resolved=True,
        )
        data = json.loads(_repair_path(vault, "rt1").read_text())
        assert data["status"] == "active"

    def test_preserves_existing_patterns(self, tmp_path):
        vault = _make_vault(tmp_path)
        # Seed with one existing pattern
        path = _repair_path(vault, "rt1")
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "schema_version": "1.0",
            "runtime_id": "rt1",
            "status": "seeded-empty",
            "repair_patterns": [{"workflow_id": "wf-old", "resolved": True}],
            "incident_candidates": [],
        }), encoding="utf-8")
        record_repair_pattern(
            "rt1", vault,
            workflow_id="wf-new",
            failure_context="something",
            repair_action="something else",
            resolved=False,
        )
        data = json.loads(path.read_text())
        assert len(data["repair_patterns"]) == 2
        assert data["repair_patterns"][0]["workflow_id"] == "wf-old"
        assert data["repair_patterns"][1]["workflow_id"] == "wf-new"


# ── TestExportMemorySnapshot ──────────────────────────────────────────────────

class TestExportMemorySnapshot:
    def test_returns_dict(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = export_memory_snapshot("rt1", vault)
        assert isinstance(result, dict)

    def test_contains_runtime_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = export_memory_snapshot("rt1", vault)
        assert result["runtime_id"] == "rt1"

    def test_contains_all_surface_keys(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = export_memory_snapshot("rt1", vault)
        assert "profile" in result
        assert "nav_map" in result
        assert "repair_memory" in result
        assert "scorecard" in result

    def test_exported_at_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = export_memory_snapshot("rt1", vault)
        assert "exported_at" in result
        assert result["exported_at"].startswith("20")


# ── TestApplyExecutionToMemory ────────────────────────────────────────────────

class TestApplyExecutionToMemory:
    def test_success_warms_nav_map(self, tmp_path):
        vault = _make_vault(tmp_path)
        apply_execution_to_memory("rt1", vault, _success_record())
        data = json.loads(_nav_path(vault, "rt1").read_text())
        assert len(data["successful_route_patterns"]) == 1

    def test_escalation_warms_nav_map_and_creates_incident(self, tmp_path):
        vault = _make_vault(tmp_path)
        apply_execution_to_memory("rt1", vault, _escalation_record())
        # Nav-map should have a trigger
        nav = json.loads(_nav_path(vault, "rt1").read_text())
        assert len(nav["common_escalation_triggers"]) == 1
        # Repair memory should have an incident candidate
        repair = json.loads(_repair_path(vault, "rt1").read_text())
        assert len(repair["incident_candidates"]) == 1

    def test_failed_creates_incident(self, tmp_path):
        vault = _make_vault(tmp_path)
        failed_record = {
            "audit_id": "audit-fail",
            "workflow_id": "wf-failed",
            "status": "failed",
            "stage_reached": "run",
            "escalation_reason": None,
            "manifest_snapshot": {"id": "wf-failed", "required_reads": []},
        }
        apply_execution_to_memory("rt1", vault, failed_record)
        repair = json.loads(_repair_path(vault, "rt1").read_text())
        assert len(repair["incident_candidates"]) == 1
        assert repair["incident_candidates"][0]["outcome"] == "failed"

    def test_fail_open_with_bad_vault(self):
        # Must not raise even with invalid vault_root type
        apply_execution_to_memory("rt1", "not_a_path", _success_record())  # type: ignore

    def test_dry_run_no_incident(self, tmp_path):
        vault = _make_vault(tmp_path)
        dry_record = {
            "audit_id": "audit-dry",
            "workflow_id": "wf-dry",
            "status": "dry_run_ok",
            "stage_reached": "dry_run_exit",
            "escalation_reason": None,
            "manifest_snapshot": {"id": "wf-dry", "required_reads": ["00_HOME/Now.md"]},
        }
        apply_execution_to_memory("rt1", vault, dry_record)
        # dry_run_ok should not create an incident candidate
        if _repair_path(vault, "rt1").exists():
            data = json.loads(_repair_path(vault, "rt1").read_text())
            assert data.get("incident_candidates", []) == []


# ── TestEngineWiring ──────────────────────────────────────────────────────────

class TestEngineWiring:
    def test_growth_module_importable(self):
        import runtime.memory.growth  # noqa: F401

    def test_growth_available_flag_in_engine(self):
        import runtime.aor.engine as eng
        assert hasattr(eng, "_GROWTH_AVAILABLE")

    def test_growth_available_true(self):
        import runtime.aor.engine as eng
        assert eng._GROWTH_AVAILABLE is True
