"""
test_drift_scan.py — Feature 16 (drift_scan) tests

Coverage:
  - _extract_date_from_filename: valid, invalid, no match
  - _match_domain: keyword matches, no match, case insensitive
  - _build_logs: returns files within lookback, excludes old files
  - _extract_signals_from_build_logs: filename match, content fallback, no match
  - _compute_domain_activity: grouping by letter, all present
  - _classify_domains: neglected/active classification
  - _extract_open_loops: extracts unchecked items from close-day sections
  - _render_drift_report: structural sections, neglected listed, no mutation claim
  - run_drift_scan: handler contract, writes report, lookback_days validation
  - AOR task_type_table: drift-scan entry present
  - AOR registry: manifest loads and is active
  - Role card: drift-scan-readonly loads cleanly
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.workflows.drift_scan import (
    _DOMAINS,
    DriftScanResult,
    WorkflowExecutionError,
    _build_logs,
    _classify_domains,
    _compute_domain_activity,
    _extract_date_from_filename,
    _extract_open_loops,
    _extract_signals_from_build_logs,
    _match_domain,
    _render_drift_report,
    run_drift_scan,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_build_log(tmp_path: Path, filename: str, content: str = "") -> Path:
    logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    p = logs_dir / filename
    p.write_text(content or f"# {filename}\n", encoding="utf-8")
    return p


def _make_close_day(tmp_path: Path, filename: str, content: str) -> Path:
    briefs_dir = tmp_path / "07_LOGS" / "Operator-Briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    p = briefs_dir / filename
    p.write_text(content, encoding="utf-8")
    return p


def _empty_result(lookback_days=30) -> DriftScanResult:
    domain_activity = {d.letter: [] for d in _DOMAINS}
    return DriftScanResult(
        scan_date=date.today().isoformat(),
        lookback_days=lookback_days,
        domain_activity=domain_activity,
        neglected_domains=list(_DOMAINS),
        active_domains=[],
        open_loops=[],
        decision_count=0,
        build_log_count=0,
        close_log_count=0,
        gaps=[],
    )


# ── _extract_date_from_filename ────────────────────────────────────────────────


class TestExtractDateFromFilename:
    def test_standard_prefix(self):
        d = _extract_date_from_filename("2026-04-25-ChaseOS-build.md")
        assert d == date(2026, 4, 25)

    def test_no_date_prefix(self):
        assert _extract_date_from_filename("no-date-here.md") is None

    def test_invalid_date(self):
        assert _extract_date_from_filename("2026-13-45-bad-date.md") is None

    def test_date_only(self):
        d = _extract_date_from_filename("2026-04-25.md")
        assert d == date(2026, 4, 25)

    def test_empty_string(self):
        assert _extract_date_from_filename("") is None


# ── _match_domain ─────────────────────────────────────────────────────────────


class TestMatchDomain:
    def test_chaseos_matches_domain_a(self):
        domain = _match_domain("2026-04-25-chaseos-phase9-build.md")
        assert domain is not None
        assert domain.letter == "A"

    def test_tradesync_matches_domain_e(self):
        domain = _match_domain("2026-04-10-tradesync-scoring-engine.md")
        assert domain is not None
        assert domain.letter == "E"

    def test_security_matches_domain_i(self):
        domain = _match_domain("security audit session")
        assert domain is not None
        assert domain.letter == "I"

    def test_case_insensitive(self):
        domain = _match_domain("CHASEOS PASS")
        assert domain is not None
        assert domain.letter == "A"

    def test_no_match_returns_none(self):
        domain = _match_domain("zzzzzz-completely-unrelated.md")
        assert domain is None

    def test_trading_matches_domain_b(self):
        domain = _match_domain("trading-systems-session.md")
        assert domain is not None
        assert domain.letter == "B"

    def test_strikezone_matches_domain_c(self):
        domain = _match_domain("strikezone-discord-update.md")
        assert domain is not None
        assert domain.letter == "C"


# ── _build_logs ───────────────────────────────────────────────────────────────


class TestBuildLogs:
    def test_returns_recent_files(self, tmp_path):
        today = date.today().isoformat()
        _make_build_log(tmp_path, f"{today}-chaseos-build.md")
        result = _build_logs(tmp_path, lookback_days=30)
        assert len(result) == 1

    def test_excludes_old_files(self, tmp_path):
        old = (date.today() - timedelta(days=60)).isoformat()
        _make_build_log(tmp_path, f"{old}-old-session.md")
        result = _build_logs(tmp_path, lookback_days=30)
        assert len(result) == 0

    def test_empty_dir_returns_empty(self, tmp_path):
        result = _build_logs(tmp_path, lookback_days=30)
        assert result == []

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        result = _build_logs(tmp_path / "missing", lookback_days=30)
        assert result == []

    def test_multiple_files_within_window(self, tmp_path):
        for days_ago in [0, 5, 10, 15]:
            d = (date.today() - timedelta(days=days_ago)).isoformat()
            _make_build_log(tmp_path, f"{d}-session-{days_ago}.md")
        result = _build_logs(tmp_path, lookback_days=20)
        assert len(result) == 4

    def test_boundary_day_included(self, tmp_path):
        boundary = (date.today() - timedelta(days=30)).isoformat()
        _make_build_log(tmp_path, f"{boundary}-boundary.md")
        result = _build_logs(tmp_path, lookback_days=30)
        assert len(result) == 1


# ── _extract_signals_from_build_logs ─────────────────────────────────────────


class TestExtractSignals:
    def test_filename_match(self, tmp_path):
        today = date.today().isoformat()
        _make_build_log(tmp_path, f"{today}-chaseos-phase9.md")
        logs = _build_logs(tmp_path, lookback_days=30)
        signals = _extract_signals_from_build_logs(logs, tmp_path)
        assert len(signals) == 1
        assert signals[0].domain_letter == "A"

    def test_content_fallback(self, tmp_path):
        today = date.today().isoformat()
        _make_build_log(tmp_path, f"{today}-generic-session.md",
                        content="---\nproject: TradeSync AI\ndate: 2026-04-25\n---\n# tradesync session\n")
        logs = _build_logs(tmp_path, lookback_days=30)
        signals = _extract_signals_from_build_logs(logs, tmp_path)
        # Should match via content (tradesync keyword)
        letters = [s.domain_letter for s in signals]
        assert "E" in letters

    def test_no_match_produces_no_signal(self, tmp_path):
        today = date.today().isoformat()
        _make_build_log(tmp_path, f"{today}-zzzunknownzzz.md",
                        content="# nothing that matches any domain\n")
        logs = _build_logs(tmp_path, lookback_days=30)
        signals = _extract_signals_from_build_logs(logs, tmp_path)
        assert len(signals) == 0

    def test_multiple_logs_multiple_signals(self, tmp_path):
        today = date.today().isoformat()
        _make_build_log(tmp_path, f"{today}-chaseos-a.md")
        _make_build_log(tmp_path, f"{today}-tradesync-b.md")
        logs = _build_logs(tmp_path, lookback_days=30)
        signals = _extract_signals_from_build_logs(logs, tmp_path)
        letters = {s.domain_letter for s in signals}
        assert "A" in letters
        assert "E" in letters

    def test_empty_log_list(self, tmp_path):
        signals = _extract_signals_from_build_logs([], tmp_path)
        assert signals == []


# ── _compute_domain_activity + _classify_domains ──────────────────────────────


class TestDomainActivity:
    def test_all_domains_present_in_output(self):
        activity = _compute_domain_activity([])
        assert set(activity.keys()) == {d.letter for d in _DOMAINS}

    def test_signal_grouped_correctly(self, tmp_path):
        from runtime.workflows.drift_scan import ActivitySignal
        signals = [
            ActivitySignal("A", "ChaseOS", "07_LOGS/Build-Logs/f.md", "2026-04-25", "chaseos"),
            ActivitySignal("A", "ChaseOS", "07_LOGS/Build-Logs/g.md", "2026-04-25", "vault"),
            ActivitySignal("E", "TradeSync", "07_LOGS/Build-Logs/h.md", "2026-04-25", "tradesync"),
        ]
        activity = _compute_domain_activity(signals)
        assert len(activity["A"]) == 2
        assert len(activity["E"]) == 1
        assert len(activity["B"]) == 0

    def test_classify_neglected_with_no_signals(self):
        activity = _compute_domain_activity([])
        neglected, active = _classify_domains(activity)
        assert len(neglected) == len(_DOMAINS)
        assert len(active) == 0

    def test_classify_with_one_active(self, tmp_path):
        from runtime.workflows.drift_scan import ActivitySignal
        signals = [ActivitySignal("A", "ChaseOS", "f.md", "2026-04-25", "chaseos")]
        activity = _compute_domain_activity(signals)
        neglected, active = _classify_domains(activity)
        assert len(active) == 1
        assert active[0].letter == "A"
        assert len(neglected) == len(_DOMAINS) - 1

    def test_classify_all_active(self):
        from runtime.workflows.drift_scan import ActivitySignal
        signals = [ActivitySignal(d.letter, d.name, "f.md", "2026-04-25", "kw")
                   for d in _DOMAINS]
        activity = _compute_domain_activity(signals)
        neglected, active = _classify_domains(activity)
        assert len(neglected) == 0
        assert len(active) == len(_DOMAINS)


# ── _extract_open_loops ───────────────────────────────────────────────────────


class TestExtractOpenLoops:
    def test_extracts_unchecked_items(self, tmp_path):
        content = """---
type: close-day
date: 2026-04-25
---

# Close Day Report

## Open Loops

- [ ] Follow up on StrikeZone signals
- [ ] Update Now.md with Phase 9 status
- [x] Already done item

## Next Steps
"""
        _make_close_day(tmp_path, "2026-04-25-close-day.md", content)
        close_logs = [tmp_path / "07_LOGS" / "Operator-Briefs" / "2026-04-25-close-day.md"]
        loops = _extract_open_loops(close_logs, tmp_path)
        texts = [l.text for l in loops]
        assert any("StrikeZone" in t for t in texts)
        assert any("Now.md" in t for t in texts)
        # Checked item should NOT be in loops
        assert not any("Already done" in t for t in texts)

    def test_empty_open_loops_section(self, tmp_path):
        content = "---\ntype: close-day\n---\n\n## Open Loops\n\nNo open loops this session.\n"
        _make_close_day(tmp_path, "2026-04-25-close-day.md", content)
        close_logs = [tmp_path / "07_LOGS" / "Operator-Briefs" / "2026-04-25-close-day.md"]
        loops = _extract_open_loops(close_logs, tmp_path)
        assert loops == []

    def test_no_open_loops_section(self, tmp_path):
        content = "---\ntype: close-day\n---\n\n# Summary\n\n- [ ] This should not be found\n"
        _make_close_day(tmp_path, "2026-04-25-close-day.md", content)
        close_logs = [tmp_path / "07_LOGS" / "Operator-Briefs" / "2026-04-25-close-day.md"]
        loops = _extract_open_loops(close_logs, tmp_path)
        # The item is outside an open_loops section header
        assert loops == []

    def test_multiple_close_day_files(self, tmp_path):
        for day in ["2026-04-24", "2026-04-25"]:
            content = f"---\ndate: {day}\n---\n\n## Open Loops\n\n- [ ] Loop from {day}\n"
            _make_close_day(tmp_path, f"{day}-close-day.md", content)
        close_logs = list((tmp_path / "07_LOGS" / "Operator-Briefs").glob("*.md"))
        loops = _extract_open_loops(close_logs, tmp_path)
        assert len(loops) == 2

    def test_carry_forward_section_detected(self, tmp_path):
        content = "---\n---\n\n## Carry-Forward\n\n- [ ] Carry forward item\n"
        _make_close_day(tmp_path, "2026-04-25-day.md", content)
        close_logs = [tmp_path / "07_LOGS" / "Operator-Briefs" / "2026-04-25-day.md"]
        loops = _extract_open_loops(close_logs, tmp_path)
        assert any("Carry forward" in l.text for l in loops)


# ── _render_drift_report ──────────────────────────────────────────────────────


class TestRenderDriftReport:
    def test_contains_required_sections(self):
        result = _empty_result()
        report = _render_drift_report(result)
        assert "## Summary" in report
        assert "## Potentially Neglected Domains" in report
        assert "## Active Domains" in report
        assert "## Open Loops" in report
        assert "## Recommended Review Items" in report

    def test_no_mutation_disclaimer(self):
        result = _empty_result()
        report = _render_drift_report(result)
        assert "Doctrine files not modified" in report or "never modified" in report or "never mutated" in report or "Read-only" in report

    def test_neglected_domains_listed(self):
        result = _empty_result()
        report = _render_drift_report(result)
        # All 18 domains should be in neglected section
        assert "A · ChaseOS" in report

    def test_active_domain_listed(self):
        from runtime.workflows.drift_scan import ActivitySignal, DomainEntry
        domain_a = next(d for d in _DOMAINS if d.letter == "A")
        domain_activity = {d.letter: [] for d in _DOMAINS}
        domain_activity["A"] = [
            ActivitySignal("A", "ChaseOS", "07_LOGS/Build-Logs/f.md", "2026-04-25", "chaseos")
        ]
        result = DriftScanResult(
            scan_date="2026-04-25",
            lookback_days=30,
            domain_activity=domain_activity,
            neglected_domains=[d for d in _DOMAINS if d.letter != "A"],
            active_domains=[domain_a],
            open_loops=[],
            decision_count=0,
            build_log_count=1,
            close_log_count=0,
            gaps=[],
        )
        report = _render_drift_report(result)
        assert "A · ChaseOS" in report

    def test_has_frontmatter(self):
        result = _empty_result()
        report = _render_drift_report(result)
        assert report.startswith("---")
        assert "type: drift-report" in report

    def test_scan_date_in_report(self):
        result = _empty_result()
        report = _render_drift_report(result)
        assert date.today().isoformat() in report

    def test_gaps_section_present_when_gaps_exist(self):
        result = _empty_result()
        result.gaps = ["Could not read operating-system.md"]
        report = _render_drift_report(result)
        assert "## Scan Gaps" in report
        assert "Could not read" in report


# ── run_drift_scan handler ────────────────────────────────────────────────────


class TestRunDriftScan:
    def test_returns_writeback_dict(self, tmp_path):
        (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
        (tmp_path / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        result = run_drift_scan({"lookback_days": 30}, tmp_path)
        assert result["handler_status"] == "executed"
        assert result["workflow_id"] == "drift_scan"
        assert "writebacks" in result
        assert len(result["writebacks"]) == 1

    def test_writeback_path_has_date(self, tmp_path):
        (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
        (tmp_path / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        result = run_drift_scan({}, tmp_path)
        wb_path = result["writebacks"][0]["path"]
        assert "07_LOGS/Drift-Reports/" in wb_path
        assert date.today().isoformat() in wb_path
        assert wb_path.endswith("drift-scan.md")

    def test_writeback_content_is_markdown(self, tmp_path):
        (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
        (tmp_path / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        result = run_drift_scan({}, tmp_path)
        content = result["writebacks"][0]["content"]
        assert content.startswith("---")
        assert "# Drift Scan Report" in content

    def test_date_override(self, tmp_path):
        (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
        (tmp_path / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        result = run_drift_scan({"date": "2026-01-15"}, tmp_path)
        wb_path = result["writebacks"][0]["path"]
        assert "2026-01-15" in wb_path

    def test_invalid_date_raises(self, tmp_path):
        with pytest.raises(WorkflowExecutionError, match="invalid date"):
            run_drift_scan({"date": "not-a-date"}, tmp_path)

    def test_lookback_days_zero_raises(self, tmp_path):
        with pytest.raises(WorkflowExecutionError, match="lookback_days"):
            run_drift_scan({"lookback_days": 0}, tmp_path)

    def test_lookback_days_too_large_raises(self, tmp_path):
        with pytest.raises(WorkflowExecutionError, match="lookback_days"):
            run_drift_scan({"lookback_days": 999}, tmp_path)

    def test_detects_chaseos_domain_active(self, tmp_path):
        today = date.today().isoformat()
        build_dir = tmp_path / "07_LOGS" / "Build-Logs"
        build_dir.mkdir(parents=True)
        (build_dir / f"{today}-chaseos-phase9-test.md").write_text("# build\n")
        (tmp_path / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        result = run_drift_scan({"lookback_days": 7}, tmp_path)
        assert result["active_domain_count"] >= 1

    def test_all_domains_neglected_with_no_logs(self, tmp_path):
        (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
        (tmp_path / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        result = run_drift_scan({"lookback_days": 7}, tmp_path)
        assert result["neglected_domain_count"] == len(_DOMAINS)
        assert result["active_domain_count"] == 0

    def test_returns_correct_output_keys(self, tmp_path):
        (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
        (tmp_path / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        result = run_drift_scan({}, tmp_path)
        required_keys = {"handler_status", "workflow_id", "date",
                         "neglected_domain_count", "active_domain_count",
                         "open_loop_count", "build_log_count", "writebacks"}
        assert required_keys <= result.keys()


# ── AOR infrastructure integration ───────────────────────────────────────────


class TestDriftScanInfrastructure:
    VAULT = Path(__file__).resolve().parents[2]

    def test_task_type_table_has_drift_scan(self):
        try:
            import yaml
            table_path = self.VAULT / "runtime" / "aor" / "task_type_table.yaml"
            data = yaml.safe_load(table_path.read_text(encoding="utf-8"))
            ids = [t["id"] for t in data["task_types"]]
            assert "drift-scan" in ids
        except ImportError:
            pytest.skip("PyYAML not available")

    def test_registry_manifest_exists(self):
        manifest = self.VAULT / "runtime" / "workflows" / "registry" / "drift_scan.yaml"
        assert manifest.exists()

    def test_registry_manifest_has_required_fields(self):
        try:
            import yaml
            manifest = self.VAULT / "runtime" / "workflows" / "registry" / "drift_scan.yaml"
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            assert data["id"] == "drift_scan"
            assert data["status"] == "active"
            assert data["task_type"] == "drift-scan"
            assert data["role_card"] == "drift-scan-readonly"
        except ImportError:
            pytest.skip("PyYAML not available")

    def test_role_card_exists(self):
        card = self.VAULT / "06_AGENTS" / "role-cards" / "drift-scan-readonly.yaml"
        assert card.exists()

    def test_role_card_has_required_fields(self):
        try:
            import yaml
            card = self.VAULT / "06_AGENTS" / "role-cards" / "drift-scan-readonly.yaml"
            data = yaml.safe_load(card.read_text(encoding="utf-8"))
            assert data["id"] == "drift-scan-readonly"
            assert "07_LOGS/Drift-Reports/" in data.get("write_scope", [])
            forbidden_zones = data.get("forbidden_write_zones", [])
            assert "SOUL.md" in forbidden_zones
            assert "00_HOME/Principles.md" in forbidden_zones
        except ImportError:
            pytest.skip("PyYAML not available")

    def test_engine_imports_drift_scan(self):
        from runtime.aor.engine import run_workflow
        assert callable(run_workflow)

    def test_drift_scan_importable(self):
        from runtime.workflows.drift_scan import run_drift_scan, WorkflowExecutionError
        assert callable(run_drift_scan)

    def test_all_18_domains_defined(self):
        assert len(_DOMAINS) == 18
        letters = {d.letter for d in _DOMAINS}
        expected = set("ABCDEFGHIJKLMNOPQR")
        assert letters == expected

    def test_live_vault_drift_scan_runs(self):
        """Smoke test: run drift_scan against live vault; must not raise."""
        result = run_drift_scan({"lookback_days": 30}, self.VAULT)
        assert result["handler_status"] == "executed"
        assert result["neglected_domain_count"] + result["active_domain_count"] == 18
