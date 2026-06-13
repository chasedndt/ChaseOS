"""
runtime/tests/test_h3_rate_guard.py

Tests for H-3: per-workflow daily execution rate guard.

Coverage:
  TestRateGuardCore         — rate_guard.py unit tests (is_rate_limited, record_execution,
                              get_execution_count, get_rate_guard_state, day reset, fail-open)
  TestScheduleMaxCycles     — loader.py ScheduleIntent.max_cycles_per_day validation + parsing
  TestEngineLookupHelper    — _lookup_schedule_rate_limit helper
  TestEngineRateCheck       — engine.py pre-stage rate_check integration

Running:
  python -m pytest runtime/tests/test_h3_rate_guard.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.rate_guard import (
    is_rate_limited,
    record_execution,
    get_execution_count,
    get_rate_guard_state,
    _state_path,
    _today_utc,
)
from runtime.schedules.loader import load_schedule, ScheduleIntent
from runtime.aor import engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_state(vault: Path, date_utc: str, counts: dict) -> None:
    state_file = vault / ".chaseos" / "rate_guard.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({"date_utc": date_utc, "counts": counts}), encoding="utf-8")


def _ok(data=None):
    return engine._StageResult(ok=True, data=data)


def _boot_ns() -> SimpleNamespace:
    return SimpleNamespace(
        boot_status="ok",
        runtime_id="openclaw",
        current_phase="phase-9",
        sprint_focus="h3",
        trust_ceiling="tier-2",
        sources_read=["Now.md"],
        boot_warnings=[],
    )


def _make_minimal_vault_with_schedule(tmp_path: Path, workflow_id: str, max_cycles: int) -> Path:
    """
    Create a minimal vault with a single schedule intent referencing workflow_id.
    Used for engine integration tests.
    """
    (tmp_path / "CLAUDE.md").write_text("# stub", encoding="utf-8")
    sched_dir = tmp_path / "runtime" / "schedules"
    sched_dir.mkdir(parents=True)
    sched_id = f"sch-{workflow_id}-test"
    (sched_dir / f"{sched_id}.yaml").write_text(
        f"schedule_id: {sched_id}\n"
        f"workflow_id: {workflow_id}\n"
        f"owner: operator\n"
        f"cadence:\n"
        f"  type: cron\n"
        f"  cron_expression: '* * * * *'\n"
        f"  timezone: America/New_York\n"
        f"trigger_source: openclaw\n"
        f"runtime_adapter_target: openclaw\n"
        f"delivery:\n"
        f"  primary_target: vault-local\n"
        f"  vault_writeback_targets:\n"
        f"    - '07_LOGS/Agent-Activity/'\n"
        f"  external_delivery_declared: false\n"
        f"  vault_local_only: true\n"
        f"approval_policy: none\n"
        f"enabled: false\n"
        f"shadow_mode: false\n"
        f"max_cycles_per_day: {max_cycles}\n"
        f"failure_behavior: escalate\n"
        f"audit_requirements: []\n"
        f"allowed_workflow_task_types:\n"
        f"  - coordination\n"
        f"provenance:\n"
        f"  created_by: operator\n"
        f"  created_at: '2026-05-11T00:00:00Z'\n"
        f"  rationale: test schedule\n",
        encoding="utf-8",
    )
    return tmp_path


# ── TestRateGuardCore ─────────────────────────────────────────────────────────

class TestRateGuardCore:
    def test_is_rate_limited_false_when_no_executions(self, tmp_path):
        assert is_rate_limited("archon_watch", 480, tmp_path) is False

    def test_is_rate_limited_false_when_under_limit(self, tmp_path):
        _write_state(tmp_path, _today_utc(), {"archon_watch": 479})
        assert is_rate_limited("archon_watch", 480, tmp_path) is False

    def test_is_rate_limited_true_when_at_limit(self, tmp_path):
        _write_state(tmp_path, _today_utc(), {"archon_watch": 480})
        assert is_rate_limited("archon_watch", 480, tmp_path) is True

    def test_is_rate_limited_true_when_over_limit(self, tmp_path):
        _write_state(tmp_path, _today_utc(), {"archon_watch": 500})
        assert is_rate_limited("archon_watch", 480, tmp_path) is True

    def test_is_rate_limited_false_when_none_limit(self, tmp_path):
        _write_state(tmp_path, _today_utc(), {"archon_watch": 999})
        assert is_rate_limited("archon_watch", None, tmp_path) is False

    def test_is_rate_limited_false_when_zero_limit(self, tmp_path):
        _write_state(tmp_path, _today_utc(), {"archon_watch": 999})
        assert is_rate_limited("archon_watch", 0, tmp_path) is False

    def test_record_execution_increments_count(self, tmp_path):
        record_execution("archon_watch", tmp_path)
        record_execution("archon_watch", tmp_path)
        record_execution("archon_watch", tmp_path)
        assert get_execution_count("archon_watch", tmp_path) == 3

    def test_record_execution_returns_new_count(self, tmp_path):
        c1 = record_execution("hermes_watch", tmp_path)
        c2 = record_execution("hermes_watch", tmp_path)
        c3 = record_execution("hermes_watch", tmp_path)
        assert c1 == 1
        assert c2 == 2
        assert c3 == 3

    def test_get_execution_count_zero_initially(self, tmp_path):
        assert get_execution_count("openclaw_watch", tmp_path) == 0

    def test_get_execution_count_after_recording(self, tmp_path):
        for _ in range(5):
            record_execution("openclaw_watch", tmp_path)
        assert get_execution_count("openclaw_watch", tmp_path) == 5

    def test_day_reset_clears_counts(self, tmp_path):
        _write_state(tmp_path, "2026-05-10", {"archon_watch": 479})
        # Yesterday's counts → reset for today
        assert get_execution_count("archon_watch", tmp_path) == 0
        assert is_rate_limited("archon_watch", 480, tmp_path) is False

    def test_multiple_workflows_tracked_independently(self, tmp_path):
        for _ in range(5):
            record_execution("archon_watch", tmp_path)
        for _ in range(3):
            record_execution("hermes_watch", tmp_path)
        assert get_execution_count("archon_watch", tmp_path) == 5
        assert get_execution_count("hermes_watch", tmp_path) == 3
        assert get_execution_count("openclaw_watch", tmp_path) == 0

    def test_fail_open_corrupt_state_file(self, tmp_path):
        state_file = _state_path(tmp_path)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("NOT_JSON{{{{", encoding="utf-8")
        # Corrupt file → fail-open, not rate-limited
        assert is_rate_limited("archon_watch", 1, tmp_path) is False
        # Count reads 0 after corruption
        assert get_execution_count("archon_watch", tmp_path) == 0

    def test_fail_open_missing_state_dir(self, tmp_path):
        # No .chaseos dir at all
        assert is_rate_limited("archon_watch", 1, tmp_path) is False

    def test_get_rate_guard_state_returns_expected_shape(self, tmp_path):
        record_execution("archon_watch", tmp_path)
        state = get_rate_guard_state(tmp_path)
        assert isinstance(state, dict)
        assert "date_utc" in state
        assert "counts" in state
        assert state["counts"]["archon_watch"] == 1

    def test_state_file_at_expected_path(self, tmp_path):
        record_execution("archon_watch", tmp_path)
        expected = tmp_path / ".chaseos" / "rate_guard.json"
        assert expected.exists()

    def test_record_execution_does_not_bleed_across_workflows(self, tmp_path):
        record_execution("archon_watch", tmp_path)
        # hermes_watch untouched
        assert is_rate_limited("hermes_watch", 1, tmp_path) is False


# ── TestScheduleMaxCycles ─────────────────────────────────────────────────────

class TestScheduleMaxCycles:
    def test_archon_schedule_has_480_limit(self):
        s = load_schedule("sch-archon-watch-every-minute", _VAULT_ROOT, check_registry=False)
        assert s is not None
        assert s.max_cycles_per_day == 480

    def test_hermes_schedule_has_720_limit(self):
        s = load_schedule("sch-hermes-watch-every-minute", _VAULT_ROOT, check_registry=False)
        assert s is not None
        assert s.max_cycles_per_day == 720

    def test_openclaw_schedule_has_720_limit(self):
        s = load_schedule("sch-openclaw-watch-every-minute", _VAULT_ROOT, check_registry=False)
        assert s is not None
        assert s.max_cycles_per_day == 720

    def test_hermes_and_openclaw_limits_are_equal(self):
        hermes = load_schedule("sch-hermes-watch-every-minute", _VAULT_ROOT, check_registry=False)
        openclaw = load_schedule("sch-openclaw-watch-every-minute", _VAULT_ROOT, check_registry=False)
        assert hermes is not None and openclaw is not None
        assert hermes.max_cycles_per_day == openclaw.max_cycles_per_day

    def test_max_cycles_per_day_absent_gives_none(self, tmp_path):
        sched_dir = tmp_path / "runtime" / "schedules"
        sched_dir.mkdir(parents=True)
        # Write schedule without max_cycles_per_day
        (sched_dir / "sch-no-limit.yaml").write_text(
            "schedule_id: sch-no-limit\n"
            "workflow_id: some_workflow\n"
            "owner: operator\n"
            "cadence:\n"
            "  type: cron\n"
            "  cron_expression: '0 7 * * *'\n"
            "  timezone: America/New_York\n"
            "trigger_source: openclaw\n"
            "runtime_adapter_target: openclaw\n"
            "delivery:\n"
            "  primary_target: vault-local\n"
            "  vault_writeback_targets:\n"
            "    - '07_LOGS/Agent-Activity/'\n"
            "  external_delivery_declared: false\n"
            "  vault_local_only: true\n"
            "approval_policy: none\n"
            "enabled: false\n"
            "shadow_mode: false\n"
            "failure_behavior: escalate\n"
            "audit_requirements: []\n"
            "allowed_workflow_task_types:\n"
            "  - coordination\n"
            "provenance:\n"
            "  created_by: operator\n"
            "  created_at: '2026-05-11T00:00:00Z'\n"
            "  rationale: test\n",
            encoding="utf-8",
        )
        s = load_schedule("sch-no-limit", tmp_path, check_registry=False)
        assert s is not None
        assert s.max_cycles_per_day is None

    def test_max_cycles_per_day_zero_is_valid(self, tmp_path):
        sched_dir = tmp_path / "runtime" / "schedules"
        sched_dir.mkdir(parents=True)
        (sched_dir / "sch-zero.yaml").write_text(
            "schedule_id: sch-zero\n"
            "workflow_id: some_workflow\n"
            "owner: operator\n"
            "cadence:\n"
            "  type: cron\n"
            "  cron_expression: '0 7 * * *'\n"
            "  timezone: America/New_York\n"
            "trigger_source: openclaw\n"
            "runtime_adapter_target: openclaw\n"
            "delivery:\n"
            "  primary_target: vault-local\n"
            "  vault_writeback_targets:\n"
            "    - '07_LOGS/Agent-Activity/'\n"
            "  external_delivery_declared: false\n"
            "  vault_local_only: true\n"
            "approval_policy: none\n"
            "enabled: false\n"
            "shadow_mode: false\n"
            "max_cycles_per_day: 0\n"
            "failure_behavior: escalate\n"
            "audit_requirements: []\n"
            "allowed_workflow_task_types:\n"
            "  - coordination\n"
            "provenance:\n"
            "  created_by: operator\n"
            "  created_at: '2026-05-11T00:00:00Z'\n"
            "  rationale: test\n",
            encoding="utf-8",
        )
        s = load_schedule("sch-zero", tmp_path, check_registry=False)
        assert s is not None
        assert s.max_cycles_per_day == 0

    def test_max_cycles_per_day_negative_raises(self, tmp_path):
        sched_dir = tmp_path / "runtime" / "schedules"
        sched_dir.mkdir(parents=True)
        (sched_dir / "sch-neg.yaml").write_text(
            "schedule_id: sch-neg\n"
            "workflow_id: some_workflow\n"
            "owner: operator\n"
            "cadence:\n"
            "  type: cron\n"
            "  cron_expression: '0 7 * * *'\n"
            "  timezone: America/New_York\n"
            "trigger_source: openclaw\n"
            "runtime_adapter_target: openclaw\n"
            "delivery:\n"
            "  primary_target: vault-local\n"
            "  vault_writeback_targets:\n"
            "    - '07_LOGS/Agent-Activity/'\n"
            "  external_delivery_declared: false\n"
            "  vault_local_only: true\n"
            "approval_policy: none\n"
            "enabled: false\n"
            "shadow_mode: false\n"
            "max_cycles_per_day: -1\n"
            "failure_behavior: escalate\n"
            "audit_requirements: []\n"
            "allowed_workflow_task_types:\n"
            "  - coordination\n"
            "provenance:\n"
            "  created_by: operator\n"
            "  created_at: '2026-05-11T00:00:00Z'\n"
            "  rationale: test\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="max_cycles_per_day"):
            load_schedule("sch-neg", tmp_path, check_registry=False)


# ── TestEngineLookupHelper ────────────────────────────────────────────────────

class TestEngineLookupHelper:
    def test_lookup_returns_none_when_no_schedule_dir(self, tmp_path):
        result = engine._lookup_schedule_rate_limit("archon_watch", tmp_path)
        assert result is None

    def test_lookup_returns_none_when_no_matching_schedule(self, tmp_path):
        _make_minimal_vault_with_schedule(tmp_path, "some_other_workflow", 100)
        result = engine._lookup_schedule_rate_limit("archon_watch", tmp_path)
        assert result is None

    def test_lookup_returns_max_cycles_when_present(self, tmp_path):
        _make_minimal_vault_with_schedule(tmp_path, "archon_watch", 480)
        result = engine._lookup_schedule_rate_limit("archon_watch", tmp_path)
        assert result == 480

    def test_lookup_returns_none_when_schedule_has_no_limit(self, tmp_path):
        # Write a schedule without max_cycles_per_day
        (tmp_path / "CLAUDE.md").write_text("# stub", encoding="utf-8")
        sched_dir = tmp_path / "runtime" / "schedules"
        sched_dir.mkdir(parents=True)
        (sched_dir / "sch-some-workflow-test.yaml").write_text(
            "schedule_id: sch-some-workflow-test\n"
            "workflow_id: some_workflow\n"
            "owner: operator\n"
            "cadence:\n"
            "  type: cron\n"
            "  cron_expression: '0 7 * * *'\n"
            "  timezone: America/New_York\n"
            "trigger_source: openclaw\n"
            "runtime_adapter_target: openclaw\n"
            "delivery:\n"
            "  primary_target: vault-local\n"
            "  vault_writeback_targets:\n"
            "    - '07_LOGS/Agent-Activity/'\n"
            "  external_delivery_declared: false\n"
            "  vault_local_only: true\n"
            "approval_policy: none\n"
            "enabled: false\n"
            "shadow_mode: false\n"
            "failure_behavior: escalate\n"
            "audit_requirements: []\n"
            "allowed_workflow_task_types:\n"
            "  - coordination\n"
            "provenance:\n"
            "  created_by: operator\n"
            "  created_at: '2026-05-11T00:00:00Z'\n"
            "  rationale: test\n",
            encoding="utf-8",
        )
        result = engine._lookup_schedule_rate_limit("some_workflow", tmp_path)
        assert result is None

    def test_lookup_real_vault_archon(self):
        result = engine._lookup_schedule_rate_limit("archon_watch", _VAULT_ROOT)
        assert result == 480

    def test_lookup_real_vault_hermes_equals_openclaw(self):
        hermes = engine._lookup_schedule_rate_limit("hermes_watch", _VAULT_ROOT)
        openclaw = engine._lookup_schedule_rate_limit("openclaw_watch", _VAULT_ROOT)
        assert hermes == openclaw == 720


# ── TestEngineRateCheck ───────────────────────────────────────────────────────

class TestEngineRateCheck:
    """Integration tests for the engine's pre-stage rate_check block."""

    def _patch_engine_stages(self, monkeypatch, vault: Path) -> None:
        manifest = {
            "id": "archon_watch",
            "status": "active",
            "permission_ceiling": "tier-2",
            "task_type": "coordination",
            "role_card": "archon-engineering",
        }
        monkeypatch.setattr(engine, "load_boot_context", lambda **_: _boot_ns())
        monkeypatch.setattr(engine, "_write_audit_record", lambda **_: None)
        monkeypatch.setattr(engine, "_stage_workflow_lookup", lambda wid, vr: _ok(manifest))
        monkeypatch.setattr(engine, "_stage_task_classification", lambda m, vr: _ok({"id": "coordination", "permission_ceiling": "tier-2"}))
        monkeypatch.setattr(engine, "_stage_role_card_resolution", lambda m, vr: _ok({"id": "archon-engineering", "write_scope": ["07_LOGS/Agent-Activity/"]}))
        monkeypatch.setattr(engine, "_stage_permission_ceiling", lambda m, tt, rc, inp: _ok({}))
        monkeypatch.setattr(engine, "_stage_required_reads", lambda m, tt, rc, vr: _ok({}))
        monkeypatch.setattr(engine, "_stage_run", lambda m, inp, vr: _ok({"writebacks": [{"path": "07_LOGS/Agent-Activity/test.json", "content": "{}"}]}))
        monkeypatch.setattr(engine, "_stage_writeback", lambda m, rc, rd, vr, dry_run=False: _ok({"artifact": "07_LOGS/Agent-Activity/test.json"}))

    def test_engine_escalates_when_rate_limited(self, monkeypatch, tmp_path):
        vault = _make_minimal_vault_with_schedule(tmp_path, "archon_watch", 480)
        self._patch_engine_stages(monkeypatch, vault)
        # Pre-fill at the limit
        _write_state(vault, _today_utc(), {"archon_watch": 480})

        result = engine.run_workflow("archon_watch", vault_root=vault)

        assert result.status == "escalated"
        assert result.stage_reached == "rate_check"

    def test_engine_escalation_reason_mentions_workflow_and_limit(self, monkeypatch, tmp_path):
        vault = _make_minimal_vault_with_schedule(tmp_path, "archon_watch", 480)
        self._patch_engine_stages(monkeypatch, vault)
        _write_state(vault, _today_utc(), {"archon_watch": 480})

        result = engine.run_workflow("archon_watch", vault_root=vault)

        assert result.escalation_reason is not None
        assert "archon_watch" in result.escalation_reason
        assert "480" in result.escalation_reason

    def test_engine_runs_when_under_rate_limit(self, monkeypatch, tmp_path):
        vault = _make_minimal_vault_with_schedule(tmp_path, "archon_watch", 480)
        self._patch_engine_stages(monkeypatch, vault)
        _write_state(vault, _today_utc(), {"archon_watch": 479})

        result = engine.run_workflow("archon_watch", vault_root=vault)

        assert result.status == "success"

    def test_engine_increments_count_on_success(self, monkeypatch, tmp_path):
        vault = _make_minimal_vault_with_schedule(tmp_path, "archon_watch", 480)
        self._patch_engine_stages(monkeypatch, vault)
        _write_state(vault, _today_utc(), {"archon_watch": 100})

        engine.run_workflow("archon_watch", vault_root=vault)

        assert get_execution_count("archon_watch", vault) == 101

    def test_engine_no_rate_check_without_schedule(self, monkeypatch, tmp_path):
        # Vault with no schedule directory — no rate limit applies
        (tmp_path / "CLAUDE.md").write_text("# stub", encoding="utf-8")
        self._patch_engine_stages(monkeypatch, tmp_path)

        result = engine.run_workflow("archon_watch", vault_root=tmp_path)

        assert result.status == "success"
        assert result.stage_reached != "rate_check"

    def test_engine_rate_check_fail_open_on_guard_error(self, monkeypatch, tmp_path):
        vault = _make_minimal_vault_with_schedule(tmp_path, "archon_watch", 480)
        self._patch_engine_stages(monkeypatch, vault)

        # Corrupt the rate guard state file so is_rate_limited would error
        state_file = vault / ".chaseos" / "rate_guard.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("INVALID{{}", encoding="utf-8")

        result = engine.run_workflow("archon_watch", vault_root=vault)

        # Corruption → fail-open → execution proceeds
        assert result.status == "success"

    def test_engine_rate_limited_at_exactly_720(self, monkeypatch, tmp_path):
        vault = _make_minimal_vault_with_schedule(tmp_path, "openclaw_watch", 720)
        self._patch_engine_stages(monkeypatch, vault)
        _write_state(vault, _today_utc(), {"openclaw_watch": 720})

        result = engine.run_workflow("openclaw_watch", vault_root=vault)

        assert result.status == "escalated"
        assert result.stage_reached == "rate_check"
        assert "720" in (result.escalation_reason or "")
