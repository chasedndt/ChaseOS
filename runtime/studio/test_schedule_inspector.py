"""Tests for Studio Schedule Inspector."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.studio import schedule_inspector as si


# ── Helpers ───────────────────────────────────────────────────────────────────

def _test_vault(name: str) -> Path:
    path = Path(__file__).resolve().parents[2] / ".pytest-tmp" / "studio-schedule-inspector" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _make_state_log(vault: Path, entries: list[dict]) -> None:
    log_dir = vault / "07_LOGS" / "Schedule-State"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "schedule_state_log.jsonl"
    log_path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n",
        encoding="utf-8",
    )


def _fake_intent(
    schedule_id: str = "sch-test-0700",
    enabled: bool = True,
    runtime_adapter_target: str = "openclaw",
    cadence_type: str = "cron",
    cron_expr: str = "0 7 * * 1-5",
    workflow_id: str = "operator_today",
    schedule_kind: str = "workflow",
) -> MagicMock:
    intent = MagicMock()
    intent.schedule_id = schedule_id
    intent.schedule_kind = schedule_kind
    intent.workflow_id = workflow_id
    intent.command_id = None
    intent.enabled = enabled
    intent.shadow_mode = False
    intent.owner = "operator"
    intent.runtime_adapter_target = runtime_adapter_target
    intent.trigger_source = "openclaw"
    intent.approval_policy = "none"
    intent.failure_behavior = "escalate"
    intent.allowed_workflow_task_types = ["operator-briefing"]
    intent.notes = "A test schedule."

    cadence = MagicMock()
    cadence.type = cadence_type
    cadence.cron_expression = cron_expr
    cadence.timezone = "America/New_York"
    intent.cadence = cadence

    delivery = MagicMock()
    delivery.primary_target = "vault-local"
    delivery.vault_local_only = True
    delivery.vault_writeback_targets = ["07_LOGS/Agent-Activity/"]
    intent.delivery = delivery

    provenance = MagicMock()
    provenance.created_at = "2026-04-15T00:00:00Z"
    provenance.created_by = "operator"
    provenance.rationale = "Test schedule rationale."
    intent.provenance = provenance

    return intent


# ── _BOUNDARY sentinel ────────────────────────────────────────────────────────

class TestBoundarySentinel:
    def test_no_write_flags(self):
        b = si._BOUNDARY
        assert b["writes_schedule_files"] is False
        assert b["enables_or_disables_schedules"] is False
        assert b["triggers_execution"] is False
        assert b["cron_mutation_allowed"] is False
        assert b["external_scheduler_mutation_allowed"] is False
        assert b["agent_bus_task_write_allowed"] is False
        assert b["runtime_dispatch_allowed"] is False
        assert b["workflow_execution"] is False
        assert b["approval_consumption_allowed"] is False
        assert b["provider_calls_allowed"] is False
        assert b["canonical_mutation_allowed"] is False

    def test_read_flags(self):
        b = si._BOUNDARY
        assert b["read_only"] is True
        assert b["reads_schedule_files"] is True
        assert b["reads_state_log"] is True


# ── State log loading ─────────────────────────────────────────────────────────

class TestLoadScheduleStateLog:
    def test_empty_when_no_log(self, tmp_path):
        result = si._load_schedule_state_log(tmp_path)
        assert result == []

    def test_loads_all_entries(self, tmp_path):
        entries = [
            {"timestamp_utc": "2026-04-15T10:00:00Z", "schedule_id": "sch-a", "action": "enable"},
            {"timestamp_utc": "2026-04-15T11:00:00Z", "schedule_id": "sch-b", "action": "disable"},
        ]
        _make_state_log(tmp_path, entries)
        result = si._load_schedule_state_log(tmp_path)
        assert len(result) == 2

    def test_filters_by_schedule_id(self, tmp_path):
        entries = [
            {"schedule_id": "sch-a", "action": "enable"},
            {"schedule_id": "sch-b", "action": "disable"},
            {"schedule_id": "sch-a", "action": "disable"},
        ]
        _make_state_log(tmp_path, entries)
        result = si._load_schedule_state_log(tmp_path, schedule_id="sch-a")
        assert len(result) == 2
        assert all(e["schedule_id"] == "sch-a" for e in result)

    def test_skips_malformed_lines(self, tmp_path):
        log_dir = tmp_path / "07_LOGS" / "Schedule-State"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "schedule_state_log.jsonl"
        log_path.write_text(
            '{"schedule_id": "sch-a"}\nNOT_JSON\n{"schedule_id": "sch-b"}\n',
            encoding="utf-8",
        )
        result = si._load_schedule_state_log(tmp_path)
        assert len(result) == 2

    def test_empty_lines_skipped(self, tmp_path):
        log_dir = tmp_path / "07_LOGS" / "Schedule-State"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "schedule_state_log.jsonl").write_text(
            "\n\n\n",
            encoding="utf-8",
        )
        result = si._load_schedule_state_log(tmp_path)
        assert result == []


# ── Intent summarization ──────────────────────────────────────────────────────

class TestScheduleIntentToSummary:
    def test_all_fields_present(self):
        intent = _fake_intent()
        summary = si._schedule_intent_to_summary(intent)
        assert summary["schedule_id"] == "sch-test-0700"
        assert summary["enabled"] is True
        assert summary["runtime_adapter_target"] == "openclaw"
        assert summary["cadence_type"] == "cron"
        assert summary["cron_expression"] == "0 7 * * 1-5"
        assert summary["workflow_id"] == "operator_today"
        assert summary["delivery_primary_target"] == "vault-local"
        assert summary["vault_local_only"] is True
        assert summary["created_at"] == "2026-04-15T00:00:00Z"
        assert summary["status_label"] == "enabled intent"
        assert "Agent Bus writes" in summary["schedule_boundary"]

    def test_detail_includes_rationale_and_notes(self):
        intent = _fake_intent()
        detail = si._schedule_intent_to_detail(intent)
        assert detail["rationale"] == "Test schedule rationale."
        assert detail["notes"] == "A test schedule."

    def test_disabled_intent(self):
        intent = _fake_intent(enabled=False)
        summary = si._schedule_intent_to_summary(intent)
        assert summary["enabled"] is False

    def test_command_kind_intent(self):
        intent = _fake_intent(schedule_kind="command", workflow_id=None)
        intent.workflow_id = None
        intent.command_id = "events.watch"
        summary = si._schedule_intent_to_summary(intent)
        assert summary["schedule_kind"] == "command"
        assert summary["command_id"] == "events.watch"
        assert summary["workflow_id"] is None


# ── list_schedules ────────────────────────────────────────────────────────────

class TestListSchedules:
    def test_returns_ok_structure(self, tmp_path):
        intents = [_fake_intent("sch-a"), _fake_intent("sch-b", enabled=False)]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.list_schedules(tmp_path)
        assert result["ok"] is True
        assert result["surface"] == "studio_schedule_inspector"
        assert result["schedule_count"] == 2
        assert "boundary" in result

    def test_enabled_only_filter(self, tmp_path):
        intents = [_fake_intent("sch-a", enabled=True), _fake_intent("sch-b", enabled=False)]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.list_schedules(tmp_path, enabled_only=True)
        assert result["schedule_count"] == 1
        assert result["schedules"][0]["schedule_id"] == "sch-a"

    def test_runtime_filter(self, tmp_path):
        intents = [
            _fake_intent("sch-a", runtime_adapter_target="openclaw"),
            _fake_intent("sch-b", runtime_adapter_target="archon"),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.list_schedules(tmp_path, runtime_filter="archon")
        assert result["schedule_count"] == 1
        assert result["schedules"][0]["schedule_id"] == "sch-b"

    def test_cadence_filter(self, tmp_path):
        intents = [
            _fake_intent("sch-a", cadence_type="cron"),
            _fake_intent("sch-b", cadence_type="manual"),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.list_schedules(tmp_path, cadence_filter="manual")
        assert result["schedule_count"] == 1
        assert result["schedules"][0]["schedule_id"] == "sch-b"

    def test_enabled_sorted_first(self, tmp_path):
        intents = [
            _fake_intent("sch-b", enabled=False),
            _fake_intent("sch-a", enabled=True),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.list_schedules(tmp_path)
        assert result["schedules"][0]["enabled"] is True
        assert result["schedules"][0]["schedule_id"] == "sch-a"

    def test_loader_error_returns_ok_false(self, tmp_path):
        with patch("runtime.schedules.loader.list_schedules", side_effect=RuntimeError("boom")):
            result = si.list_schedules(tmp_path)
        assert result["ok"] is False
        assert "boom" in result["error"]
        assert result["schedules"] == []

    def test_empty_schedules(self, tmp_path):
        with patch("runtime.schedules.loader.list_schedules", return_value=[]):
            result = si.list_schedules(tmp_path)
        assert result["ok"] is True
        assert result["schedule_count"] == 0
        assert result["schedules"] == []


# ── inspect_schedule ──────────────────────────────────────────────────────────

class TestInspectSchedule:
    def test_found_returns_detail(self, tmp_path):
        intent = _fake_intent("sch-test-0700")
        with patch("runtime.schedules.loader.load_schedule", return_value=intent):
            result = si.inspect_schedule(tmp_path, "sch-test-0700")
        assert result["ok"] is True
        assert result["schedule"]["schedule_id"] == "sch-test-0700"
        assert result["schedule"]["rationale"] == "Test schedule rationale."
        assert "recent_state_changes" in result
        assert "boundary" in result

    def test_not_found_returns_ok_false(self, tmp_path):
        with patch("runtime.schedules.loader.load_schedule", return_value=None):
            result = si.inspect_schedule(tmp_path, "sch-nonexistent")
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_loader_error_returns_ok_false(self, tmp_path):
        with patch("runtime.schedules.loader.load_schedule", side_effect=RuntimeError("bad yaml")):
            result = si.inspect_schedule(tmp_path, "sch-broken")
        assert result["ok"] is False
        assert "bad yaml" in result["error"]

    def test_state_changes_attached(self, tmp_path):
        vault = _test_vault("inspect-state")
        entries = [
            {"schedule_id": "sch-op-0700", "action": "enable", "timestamp_utc": "2026-04-15T10:00:00Z"},
            {"schedule_id": "sch-op-0700", "action": "disable", "timestamp_utc": "2026-04-15T11:00:00Z"},
            {"schedule_id": "sch-other", "action": "enable", "timestamp_utc": "2026-04-15T12:00:00Z"},
        ]
        _make_state_log(vault, entries)
        intent = _fake_intent("sch-op-0700")
        with patch("runtime.schedules.loader.load_schedule", return_value=intent):
            result = si.inspect_schedule(vault, "sch-op-0700")
        # Only sch-op-0700 entries
        assert result["state_changes_shown"] == 2
        for change in result["recent_state_changes"]:
            assert change["schedule_id"] == "sch-op-0700"

    def test_state_changes_newest_first(self, tmp_path):
        vault = _test_vault("inspect-newest-first")
        entries = [
            {"schedule_id": "sch-x", "action": "enable", "timestamp_utc": "2026-04-10T00:00:00Z"},
            {"schedule_id": "sch-x", "action": "disable", "timestamp_utc": "2026-04-20T00:00:00Z"},
        ]
        _make_state_log(vault, entries)
        intent = _fake_intent("sch-x")
        with patch("runtime.schedules.loader.load_schedule", return_value=intent):
            result = si.inspect_schedule(vault, "sch-x")
        changes = result["recent_state_changes"]
        assert changes[0]["timestamp_utc"] == "2026-04-20T00:00:00Z"

    def test_state_log_limit_respected(self, tmp_path):
        vault = _test_vault("inspect-limit")
        entries = [{"schedule_id": "sch-y", "action": "enable", "n": i} for i in range(20)]
        _make_state_log(vault, entries)
        intent = _fake_intent("sch-y")
        with patch("runtime.schedules.loader.load_schedule", return_value=intent):
            result = si.inspect_schedule(vault, "sch-y", state_log_limit=5)
        assert result["state_changes_shown"] <= 5

    def test_no_state_log_still_ok(self, tmp_path):
        intent = _fake_intent("sch-z")
        with patch("runtime.schedules.loader.load_schedule", return_value=intent):
            result = si.inspect_schedule(tmp_path, "sch-z")
        assert result["ok"] is True
        assert result["recent_state_changes"] == []
        assert result["state_changes_shown"] == 0


# ── get_schedule_summary ──────────────────────────────────────────────────────

class TestGetScheduleSummary:
    def test_returns_correct_counts(self, tmp_path):
        intents = [
            _fake_intent("sch-a", enabled=True, runtime_adapter_target="openclaw", cadence_type="cron"),
            _fake_intent("sch-b", enabled=True, runtime_adapter_target="openclaw", cadence_type="cron"),
            _fake_intent("sch-c", enabled=False, runtime_adapter_target="archon", cadence_type="cron"),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.get_schedule_summary(tmp_path)
        assert result["ok"] is True
        assert result["total"] == 3
        assert result["enabled"] == 2
        assert result["disabled"] == 1
        assert result["authority"]["runtime_dispatch_allowed"] is False
        assert result["operating_context"]["title"] == "Schedule Operating Context"
        assert result["readiness"]["rows"]
        assert result["feature_family_coverage"]

    def test_by_runtime_counts(self, tmp_path):
        intents = [
            _fake_intent("sch-a", runtime_adapter_target="openclaw"),
            _fake_intent("sch-b", runtime_adapter_target="openclaw"),
            _fake_intent("sch-c", runtime_adapter_target="archon"),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.get_schedule_summary(tmp_path)
        assert result["by_runtime_adapter_target"]["openclaw"] == 2
        assert result["by_runtime_adapter_target"]["archon"] == 1

    def test_by_cadence_counts(self, tmp_path):
        intents = [
            _fake_intent("sch-a", cadence_type="cron"),
            _fake_intent("sch-b", cadence_type="cron"),
            _fake_intent("sch-c", cadence_type="manual"),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.get_schedule_summary(tmp_path)
        assert result["by_cadence_type"]["cron"] == 2
        assert result["by_cadence_type"]["manual"] == 1

    def test_by_schedule_kind(self, tmp_path):
        intents = [
            _fake_intent("sch-a", schedule_kind="workflow"),
            _fake_intent("sch-b", schedule_kind="command"),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.get_schedule_summary(tmp_path)
        assert result["by_schedule_kind"]["workflow"] == 1
        assert result["by_schedule_kind"]["command"] == 1

    def test_last_state_change_attached(self, tmp_path):
        vault = _test_vault("summary-state")
        entries = [
            {"schedule_id": "sch-a", "action": "enable", "timestamp_utc": "2026-04-10T00:00:00Z"},
            {"schedule_id": "sch-b", "action": "disable", "timestamp_utc": "2026-04-20T00:00:00Z"},
        ]
        _make_state_log(vault, entries)
        with patch("runtime.schedules.loader.list_schedules", return_value=[]):
            result = si.get_schedule_summary(vault)
        assert result["last_state_change_utc"] == "2026-04-20T00:00:00Z"

    def test_empty_schedules(self, tmp_path):
        with patch("runtime.schedules.loader.list_schedules", return_value=[]):
            result = si.get_schedule_summary(tmp_path)
        assert result["ok"] is True
        assert result["total"] == 0
        assert result["enabled"] == 0
        assert result["disabled"] == 0

    def test_loader_error(self, tmp_path):
        with patch("runtime.schedules.loader.list_schedules", side_effect=RuntimeError("fail")):
            result = si.get_schedule_summary(tmp_path)
        assert result["ok"] is False
        assert "fail" in result["error"]

    def test_surface_field(self, tmp_path):
        with patch("runtime.schedules.loader.list_schedules", return_value=[]):
            result = si.get_schedule_summary(tmp_path)
        assert result["surface"] == "studio_schedule_inspector"

    def test_product_context_cards_are_conservative(self, tmp_path):
        intents = [
            _fake_intent("sch-a", enabled=True, runtime_adapter_target="openclaw"),
            _fake_intent("sch-b", enabled=False, runtime_adapter_target="hermes"),
        ]
        with patch("runtime.schedules.loader.list_schedules", return_value=intents):
            result = si.get_schedule_summary(tmp_path)
        cards = result["operating_context"]["cards"]
        assert cards[0]["label"] == "Schedule intents"
        assert cards[0]["value"] == 2
        readiness = {row["label"]: row for row in result["readiness"]["rows"]}
        assert readiness["Cron / runtime dispatch"]["status"] == "blocked"
        assert "No Agent Bus task write" in readiness["Agent Bus / provider / delivery writes"]["note"]

    def test_feature_family_coverage_names_expected_capabilities(self, tmp_path):
        with patch("runtime.schedules.loader.list_schedules", return_value=[]):
            result = si.get_schedule_summary(tmp_path)
        rows = result["feature_family_coverage"]
        capabilities = {row["capability"] for row in rows}
        assert "Trigger schedule intent readback" in capabilities
        assert "Native schedule intent store" in capabilities
        assert "Schedule state audit readback" in capabilities
        assert all("boundary" in row for row in rows)


# ── Live vault smoke (read-only, uses real schedule files) ────────────────────

class TestLiveVaultSmoke:
    def test_list_schedules_real_vault(self):
        vault = Path(__file__).resolve().parents[2]
        if not (vault / "runtime" / "schedules").exists():
            pytest.skip("Not in ChaseOS vault")
        result = si.list_schedules(vault)
        assert result["ok"] is True
        assert result["schedule_count"] >= 1

    def test_inspect_real_schedule(self):
        vault = Path(__file__).resolve().parents[2]
        if not (vault / "runtime" / "schedules" / "sch-operator-today-0700.yaml").exists():
            pytest.skip("Not in ChaseOS vault")
        result = si.inspect_schedule(vault, "sch-operator-today-0700")
        assert result["ok"] is True
        assert result["schedule"]["workflow_id"] == "operator_today"

    def test_inspect_archon_schedule(self):
        vault = Path(__file__).resolve().parents[2]
        if not (vault / "runtime" / "schedules" / "sch-archon-watch-every-minute.yaml").exists():
            pytest.skip("Not in ChaseOS vault")
        result = si.inspect_schedule(vault, "sch-archon-watch-every-minute")
        assert result["ok"] is True
        assert result["schedule"]["workflow_id"] == "archon_watch"
        assert result["schedule"]["runtime_adapter_target"] == "hermes"

    def test_get_summary_real_vault(self):
        vault = Path(__file__).resolve().parents[2]
        if not (vault / "runtime" / "schedules").exists():
            pytest.skip("Not in ChaseOS vault")
        result = si.get_schedule_summary(vault)
        assert result["ok"] is True
        assert result["total"] >= 1

    def test_inspect_nonexistent_schedule(self):
        vault = Path(__file__).resolve().parents[2]
        if not (vault / "runtime" / "schedules").exists():
            pytest.skip("Not in ChaseOS vault")
        result = si.inspect_schedule(vault, "sch-does-not-exist-xyz")
        assert result["ok"] is False
