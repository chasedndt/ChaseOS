"""
test_hermes_schedule_polling.py — Tests for Hermes Option C: cron schedule polling

Coverage:
  - _cron_field_matches: *, exact, range, list, invalid
  - _cron_matches: 5-field evaluation, day-of-week conversion, wrong field count
  - _load_schedule_state / _save_schedule_state: roundtrip, missing file, corrupt, OS error
  - _check_due_schedules: not_due, fired, already_fired_this_minute, shadow_mode,
                           subprocess_error, hermes_watch skipped, is_fallback skipped,
                           non-cron skipped, loader error fail-open
  - _run_one_cycle: check_schedules=True fires schedules, check_schedules=False skips
  - run_hermes_watch: check_schedules input propagated
"""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from runtime.workflows.hermes_watch import (
    _cron_field_matches,
    _cron_matches,
    _get_schedule_state_path,
    _load_schedule_state,
    _save_schedule_state,
    _check_due_schedules,
    _run_one_cycle,
    run_hermes_watch,
    _SCHEDULE_STATE_FILENAME,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (tmp_path / "00_HOME").mkdir(parents=True)
    (tmp_path / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    (tmp_path / "runtime" / "agent_bus").mkdir(parents=True)
    (tmp_path / ".chaseos").mkdir(parents=True)
    return tmp_path


def _monday_0700_et() -> datetime:
    """Monday 2026-05-11 07:00:00 UTC-4 (ET) = 11:00:00 UTC."""
    from zoneinfo import ZoneInfo
    return datetime(2026, 5, 11, 11, 0, 0, tzinfo=timezone.utc)


def _friday_0550_et() -> datetime:
    """Friday 2026-05-15 05:50:00 ET = 09:50:00 UTC."""
    return datetime(2026, 5, 15, 9, 50, 0, tzinfo=timezone.utc)


def _sunday_0700_et() -> datetime:
    """Sunday 2026-05-17 07:00:00 ET = 11:00:00 UTC."""
    return datetime(2026, 5, 17, 11, 0, 0, tzinfo=timezone.utc)


def _make_schedule_entry(
    *,
    schedule_id: str = "sch-operator-today-0700",
    workflow_id: str = "operator_today",
    cron_expression: str = "0 7 * * 1-5",
    timezone_name: str = "America/New_York",
    shadow_mode: bool = False,
    is_fallback: bool = False,
    enabled: bool = True,
) -> dict:
    return {
        "schedule_id": schedule_id,
        "schedule_kind": "workflow",
        "workflow_id": workflow_id,
        "command_id": None,
        "cadence_type": "cron",
        "cron_expression": cron_expression,
        "timezone": timezone_name,
        "enabled": enabled,
        "shadow_mode": shadow_mode,
        "command": f"chaseos run {workflow_id}",
        "approval_policy": "none",
        "failure_behavior": "escalate",
        "vault_writeback_targets": [],
        "audit_requirements": [],
        "is_fallback": is_fallback,
    }


# ── _cron_field_matches ───────────────────────────────────────────────────────

class TestCronFieldMatches(unittest.TestCase):

    def test_wildcard_matches_any(self):
        for v in [0, 15, 59, 23]:
            with self.subTest(v=v):
                self.assertTrue(_cron_field_matches("*", v))

    def test_exact_match(self):
        self.assertTrue(_cron_field_matches("7", 7))

    def test_exact_no_match(self):
        self.assertFalse(_cron_field_matches("7", 8))

    def test_range_match_lower_bound(self):
        self.assertTrue(_cron_field_matches("1-5", 1))

    def test_range_match_upper_bound(self):
        self.assertTrue(_cron_field_matches("1-5", 5))

    def test_range_match_middle(self):
        self.assertTrue(_cron_field_matches("1-5", 3))

    def test_range_no_match_above(self):
        self.assertFalse(_cron_field_matches("1-5", 6))

    def test_range_no_match_below(self):
        self.assertFalse(_cron_field_matches("1-5", 0))

    def test_list_match(self):
        self.assertTrue(_cron_field_matches("1,3,5", 3))

    def test_list_no_match(self):
        self.assertFalse(_cron_field_matches("1,3,5", 2))

    def test_list_first_element(self):
        self.assertTrue(_cron_field_matches("1,3,5", 1))

    def test_list_last_element(self):
        self.assertTrue(_cron_field_matches("1,3,5", 5))

    def test_invalid_field_returns_false(self):
        self.assertFalse(_cron_field_matches("abc", 5))

    def test_invalid_range_returns_false(self):
        self.assertFalse(_cron_field_matches("a-b", 3))

    def test_zero_minute(self):
        self.assertTrue(_cron_field_matches("0", 0))


# ── _cron_matches ─────────────────────────────────────────────────────────────

class TestCronMatches(unittest.TestCase):

    def test_operator_today_monday_0700(self):
        # "0 7 * * 1-5" should match Monday 07:00 ET
        now = _monday_0700_et()
        from zoneinfo import ZoneInfo
        now_et = now.astimezone(ZoneInfo("America/New_York"))
        self.assertTrue(_cron_matches("0 7 * * 1-5", now_et))

    def test_operator_today_sunday_0700_no_match(self):
        now = _sunday_0700_et()
        from zoneinfo import ZoneInfo
        now_et = now.astimezone(ZoneInfo("America/New_York"))
        self.assertFalse(_cron_matches("0 7 * * 1-5", now_et))

    def test_strikezone_friday_0550(self):
        now = _friday_0550_et()
        from zoneinfo import ZoneInfo
        now_et = now.astimezone(ZoneInfo("America/New_York"))
        self.assertTrue(_cron_matches("50 5 * * 1-5", now_et))

    def test_strikezone_friday_0551_no_match(self):
        dt = datetime(2026, 5, 15, 9, 51, 0, tzinfo=timezone.utc)
        from zoneinfo import ZoneInfo
        now_et = dt.astimezone(ZoneInfo("America/New_York"))
        self.assertFalse(_cron_matches("50 5 * * 1-5", now_et))

    def test_every_minute_always_matches(self):
        now = _monday_0700_et()
        self.assertTrue(_cron_matches("* * * * *", now))

    def test_wrong_field_count_returns_false(self):
        now = _monday_0700_et()
        self.assertFalse(_cron_matches("0 7 * *", now))  # 4 fields
        self.assertFalse(_cron_matches("0 7 * * 1-5 extra", now))  # 6 fields

    def test_daily_hygiene_0300_matches(self):
        dt_0300_utc = datetime(2026, 5, 11, 7, 0, 0, tzinfo=timezone.utc)  # 03:00 ET
        from zoneinfo import ZoneInfo
        now_et = dt_0300_utc.astimezone(ZoneInfo("America/New_York"))
        self.assertTrue(_cron_matches("0 3 * * *", now_et))

    def test_monday_dow_1(self):
        # Monday → cron_dow = (0+1)%7 = 1
        from zoneinfo import ZoneInfo
        dt = datetime(2026, 5, 11, 11, 0, 0, tzinfo=timezone.utc)  # Monday
        et = dt.astimezone(ZoneInfo("America/New_York"))
        self.assertTrue(_cron_matches("0 7 * * 1", et))

    def test_sunday_dow_0(self):
        # Sunday → cron_dow = (6+1)%7 = 0
        from zoneinfo import ZoneInfo
        dt = datetime(2026, 5, 17, 11, 0, 0, tzinfo=timezone.utc)  # Sunday
        et = dt.astimezone(ZoneInfo("America/New_York"))
        self.assertTrue(_cron_matches("0 7 * * 0", et))
        self.assertFalse(_cron_matches("0 7 * * 1", et))


# ── Schedule state ─────────────────────────────────────────────────────────────

class TestScheduleState(unittest.TestCase):

    def test_state_path_correct(self):
        vault = Path("/tmp/vault")
        expected = vault / ".chaseos" / _SCHEDULE_STATE_FILENAME
        self.assertEqual(_get_schedule_state_path(vault), expected)

    def test_load_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            result = _load_schedule_state(vault)
            self.assertEqual(result, {})

    def test_load_corrupt_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            state_path = _get_schedule_state_path(vault)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text("not valid json", encoding="utf-8")
            result = _load_schedule_state(vault)
            self.assertEqual(result, {})

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            state = {"last_fired": {"sch-foo": "2026-05-11T07:00:00+00:00"}}
            _save_schedule_state(vault, state)
            loaded = _load_schedule_state(vault)
            self.assertEqual(loaded, state)

    def test_save_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "nested" / "vault"
            vault.mkdir(parents=True)
            state = {"last_fired": {}}
            _save_schedule_state(vault, state)
            self.assertTrue(_get_schedule_state_path(vault).exists())

    def test_save_os_error_is_suppressed(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            with patch("runtime.workflows.hermes_watch._get_schedule_state_path") as mock_path:
                mock_p = MagicMock()
                mock_p.parent.mkdir.side_effect = OSError("no space")
                mock_path.return_value = mock_p
                # Must not raise
                _save_schedule_state(vault, {"last_fired": {}})


# ── _check_due_schedules ──────────────────────────────────────────────────────

class TestCheckDueSchedules(unittest.TestCase):

    def test_loader_import_error_returns_empty(self):
        """Fail-open: if schedule loader can't be imported, return []."""
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with patch.dict("sys.modules", {"runtime.schedules.loader": None}):
                result = _check_due_schedules(vault, _monday_0700_et())
        self.assertEqual(result, [])

    def test_empty_schedule_list_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with patch("runtime.workflows.hermes_watch.export_schedules_for_adapter", return_value=[], create=True):
                with patch("runtime.schedules.loader.export_schedules_for_adapter", return_value=[]):
                    # Patch at the point of import inside _check_due_schedules
                    pass
            # Direct mock via sys.modules patch
            mock_loader = MagicMock()
            mock_loader.export_schedules_for_adapter.return_value = []
            import sys
            sys.modules["runtime.schedules.loader"] = mock_loader
            try:
                result = _check_due_schedules(vault, _monday_0700_et())
            finally:
                del sys.modules["runtime.schedules.loader"]
            self.assertEqual(result, [])

    def _patch_loader(self, schedules: list[dict]):
        """Context manager that patches export_schedules_for_adapter."""
        import sys
        mock_loader = MagicMock()
        mock_loader.export_schedules_for_adapter.return_value = schedules
        return patch.dict("sys.modules", {"runtime.schedules.loader": mock_loader})

    def test_not_due_schedule_returns_not_due(self):
        entry = _make_schedule_entry(cron_expression="0 7 * * 1-5")
        # Sunday → should not match Mon-Fri expression
        now = _sunday_0700_et()
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                results = _check_due_schedules(vault, now)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["fired"])
        self.assertEqual(results[0]["reason"], "not_due")

    def test_is_fallback_skipped(self):
        entry = _make_schedule_entry(is_fallback=True)
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                results = _check_due_schedules(vault, _monday_0700_et())
        self.assertEqual(results, [])

    def test_hermes_watch_self_skipped(self):
        entry = _make_schedule_entry(workflow_id="hermes_watch", cron_expression="* * * * *")
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                results = _check_due_schedules(vault, _monday_0700_et())
        self.assertEqual(results, [])

    def test_non_cron_cadence_skipped(self):
        entry = _make_schedule_entry()
        entry["cadence_type"] = "event"
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                results = _check_due_schedules(vault, _monday_0700_et())
        self.assertEqual(results, [])

    def test_due_schedule_fires_subprocess(self):
        entry = _make_schedule_entry()  # "0 7 * * 1-5" → due on Monday 07:00 ET
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                with patch("subprocess.run") as mock_run:
                    results = _check_due_schedules(vault, _monday_0700_et())
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn("chaseos", call_args)
            self.assertIn("operator_today", call_args)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["fired"])
        self.assertEqual(results[0]["reason"], "fired")

    def test_state_file_updated_after_fire(self):
        entry = _make_schedule_entry()
        now = _monday_0700_et()
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                with patch("subprocess.run"):
                    _check_due_schedules(vault, now)
            state = _load_schedule_state(vault)
            self.assertIn("sch-operator-today-0700", state.get("last_fired", {}))

    def test_already_fired_this_minute_skipped(self):
        entry = _make_schedule_entry()
        now = _monday_0700_et()
        # Pre-populate state: fired at this exact minute
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            _save_schedule_state(vault, {
                "last_fired": {"sch-operator-today-0700": now.isoformat()}
            })
            with self._patch_loader([entry]):
                with patch("subprocess.run") as mock_run:
                    results = _check_due_schedules(vault, now)
            mock_run.assert_not_called()
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["fired"])
        self.assertEqual(results[0]["reason"], "already_fired_this_minute")

    def test_different_minute_fires_again(self):
        entry = _make_schedule_entry(cron_expression="* * * * *")  # every minute
        now = _monday_0700_et()
        prev_minute = datetime(2026, 5, 11, 10, 59, 0, tzinfo=timezone.utc)  # previous minute
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            _save_schedule_state(vault, {
                "last_fired": {"sch-operator-today-0700": prev_minute.isoformat()}
            })
            with self._patch_loader([entry]):
                with patch("subprocess.run"):
                    results = _check_due_schedules(vault, now)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["fired"])

    def test_shadow_mode_no_subprocess(self):
        entry = _make_schedule_entry(shadow_mode=True)
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                with patch("subprocess.run") as mock_run:
                    results = _check_due_schedules(vault, _monday_0700_et())
            mock_run.assert_not_called()
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["fired"])
        self.assertEqual(results[0]["reason"], "shadow_mode")

    def test_shadow_mode_still_updates_state(self):
        entry = _make_schedule_entry(shadow_mode=True)
        now = _monday_0700_et()
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                with patch("subprocess.run"):
                    _check_due_schedules(vault, now)
            state = _load_schedule_state(vault)
            self.assertIn("sch-operator-today-0700", state.get("last_fired", {}))

    def test_subprocess_error_captured(self):
        entry = _make_schedule_entry()
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader([entry]):
                with patch("subprocess.run", side_effect=OSError("exec failed")):
                    results = _check_due_schedules(vault, _monday_0700_et())
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["fired"])
        self.assertIn("subprocess_error", results[0]["reason"])

    def test_multiple_schedules_mixed(self):
        """One due, one not due, one self."""
        entries = [
            _make_schedule_entry(
                schedule_id="sch-operator-today-0700",
                workflow_id="operator_today",
                cron_expression="0 7 * * 1-5",
            ),
            _make_schedule_entry(
                schedule_id="sch-strikezone-0550",
                workflow_id="strikezone_acquisition",
                cron_expression="50 5 * * 1-5",
            ),
            _make_schedule_entry(
                schedule_id="sch-hermes-watch",
                workflow_id="hermes_watch",
                cron_expression="* * * * *",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self._patch_loader(entries):
                with patch("subprocess.run") as mock_run:
                    results = _check_due_schedules(vault, _monday_0700_et())
            # hermes_watch skipped entirely, strikezone not due (05:50 ≠ 07:00)
            self.assertEqual(mock_run.call_count, 1)
        fired = [r for r in results if r.get("fired")]
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0]["workflow_id"], "operator_today")


# ── _run_one_cycle integration ────────────────────────────────────────────────

class TestRunOneCycleScheduleIntegration(unittest.TestCase):

    def _mock_bus(self):
        return {
            "runtime.agent_bus.bus": MagicMock(
                upsert_heartbeat=MagicMock(),
                list_tasks=MagicMock(return_value=[]),
            )
        }

    def test_check_schedules_true_calls_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with patch.dict("sys.modules", self._mock_bus()):
                with patch(
                    "runtime.workflows.hermes_watch._check_due_schedules",
                    return_value=[],
                ) as mock_check:
                    _run_one_cycle(
                        vault,
                        max_tasks_per_cycle=2,
                        synthesize=False,
                        now_iso="2026-05-11T07:00:00Z",
                        check_schedules=True,
                    )
            mock_check.assert_called_once()

    def test_check_schedules_false_skips_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with patch.dict("sys.modules", self._mock_bus()):
                with patch(
                    "runtime.workflows.hermes_watch._check_due_schedules",
                    return_value=[],
                ) as mock_check:
                    _run_one_cycle(
                        vault,
                        max_tasks_per_cycle=2,
                        synthesize=False,
                        now_iso="2026-05-11T07:00:00Z",
                        check_schedules=False,
                    )
            mock_check.assert_not_called()

    def test_schedules_fired_in_cycle_result(self):
        fired_entry = {"schedule_id": "sch-foo", "fired": True, "reason": "fired"}
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with patch.dict("sys.modules", self._mock_bus()):
                with patch(
                    "runtime.workflows.hermes_watch._check_due_schedules",
                    return_value=[fired_entry],
                ):
                    result = _run_one_cycle(
                        vault,
                        max_tasks_per_cycle=2,
                        synthesize=False,
                        now_iso="2026-05-11T07:00:00Z",
                        check_schedules=True,
                    )
        self.assertEqual(len(result["schedules_fired"]), 1)
        self.assertEqual(result["schedules_fired"][0]["schedule_id"], "sch-foo")

    def test_non_fired_entries_excluded_from_schedules_fired(self):
        not_due = {"schedule_id": "sch-bar", "fired": False, "reason": "not_due"}
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with patch.dict("sys.modules", self._mock_bus()):
                with patch(
                    "runtime.workflows.hermes_watch._check_due_schedules",
                    return_value=[not_due],
                ):
                    result = _run_one_cycle(
                        vault,
                        max_tasks_per_cycle=2,
                        synthesize=False,
                        now_iso="2026-05-11T07:00:00Z",
                        check_schedules=True,
                    )
        self.assertEqual(result["schedules_fired"], [])


# ── run_hermes_watch inputs ────────────────────────────────────────────────────

class TestRunHermesWatchCheckSchedulesInput(unittest.TestCase):

    def test_check_schedules_default_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            mock_bus = MagicMock(
                upsert_heartbeat=MagicMock(),
                list_tasks=MagicMock(return_value=[]),
            )
            with patch.dict("sys.modules", {"runtime.agent_bus.bus": mock_bus}):
                with patch(
                    "runtime.workflows.hermes_watch._check_due_schedules",
                    return_value=[],
                ) as mock_check:
                    run_hermes_watch({"interval_seconds": None}, vault)
            mock_check.assert_called_once()

    def test_check_schedules_false_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            mock_bus = MagicMock(
                upsert_heartbeat=MagicMock(),
                list_tasks=MagicMock(return_value=[]),
            )
            with patch.dict("sys.modules", {"runtime.agent_bus.bus": mock_bus}):
                with patch(
                    "runtime.workflows.hermes_watch._check_due_schedules",
                    return_value=[],
                ) as mock_check:
                    run_hermes_watch({"interval_seconds": None, "check_schedules": False}, vault)
            mock_check.assert_not_called()

    def test_cycle_summary_includes_schedules_fired_count(self):
        fired = {"schedule_id": "sch-x", "fired": True, "reason": "fired"}
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            mock_bus = MagicMock(
                upsert_heartbeat=MagicMock(),
                list_tasks=MagicMock(return_value=[]),
            )
            with patch.dict("sys.modules", {"runtime.agent_bus.bus": mock_bus}):
                with patch(
                    "runtime.workflows.hermes_watch._check_due_schedules",
                    return_value=[fired],
                ):
                    result = run_hermes_watch({"interval_seconds": None}, vault)
        self.assertEqual(result["cycle_summaries"][0]["schedules_fired"], 1)


if __name__ == "__main__":
    unittest.main()
