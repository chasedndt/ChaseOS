"""
test_studio_memory_inspector.py — Tests for Studio Memory Inspector

Covers:
  TestListRuntimes      (4 tests) — list_registered_runtimes
  TestInspectErrors     (3 tests) — missing runtime, boundary
  TestInspectProfile    (4 tests) — profile section
  TestInspectLedger     (4 tests) — identity ledger section
  TestInspectNavMap     (3 tests) — nav-map section
  TestInspectScorecard  (3 tests) — scorecard section
  TestFilesPresent      (3 tests) — files_present flags
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.memory_inspector import inspect_runtime_memory, list_registered_runtimes


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "runtime" / "memory" / "adapters").mkdir(parents=True)
    (vault / "runtime" / "memory" / "scorecards").mkdir(parents=True)
    (vault / "runtime" / "memory" / "repair").mkdir(parents=True)
    return vault


def _make_runtime(vault: Path, runtime_id: str) -> Path:
    rt_dir = vault / "runtime" / "memory" / "adapters" / runtime_id
    rt_dir.mkdir(parents=True, exist_ok=True)
    return rt_dir


def _write_profile(rt_dir: Path, runtime_id: str = "claude", **overrides) -> Path:
    profile = {
        "schema_version": "1.0",
        "layer": "C",
        "memory_family": "behavioral_profile",
        "runtime_id": runtime_id,
        "runtime_label": "Claude Code",
        "status": "active",
        "updated_at": "2026-04-30T10:00:00Z",
        "behavioral_profile": {
            "primary_goals": ["assist operator", "maintain governance"],
            "domain_focus": ["aor", "studio"],
            "interaction_style": "direct",
        },
        "governance_boundary": {"write_authority": "none"},
    }
    profile.update(overrides)
    path = rt_dir / "profile.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    return path


def _write_ledger(rt_dir: Path, runtime_id: str = "claude") -> Path:
    ledger = {
        "schema_version": "1.0",
        "layer": "C",
        "memory_family": "identity_ledger",
        "runtime_id": runtime_id,
        "runtime_label": "Claude Code",
        "status": "active",
        "updated_at": "2026-04-30T10:00:00Z",
        "identity_summary": "Primary operator-assistant runtime.",
        "behavioral_tendencies": [],
        "doctrine_adherence": {"score": 0.95},
        "correction_history": [{"date": "2026-04-01", "note": "test correction"}],
        "drift_signals": [],
        "authority_boundaries": {"write": "none"},
        "sources": [],
        "workflow_history_posture": {},
        "memory_cluster_influence": {},
        "promotion_rules": [],
        "governance_boundary": {},
    }
    path = rt_dir / "identity-ledger.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")
    return path


def _write_nav_map(rt_dir: Path, runtime_id: str = "claude") -> Path:
    nav = {
        "schema_version": "1.0",
        "runtime_id": runtime_id,
        "updated_at": "2026-04-30T10:00:00Z",
        "successful_route_patterns": [
            "operator_today → write 07_LOGS/Operator-Briefs/",
            "graph_hygiene → write 07_LOGS/Hygiene-Reports/",
        ],
        "common_escalation_triggers": ["missing Now.md"],
    }
    path = rt_dir / "nav-map.json"
    path.write_text(json.dumps(nav), encoding="utf-8")
    return path


def _write_scorecard(vault: Path, runtime_id: str = "claude") -> Path:
    scorecard = {
        "runtime_id": runtime_id,
        "schema_version": "1.0",
        "status": "active",
        "created_at": "2026-04-01T00:00:00Z",
        "last_updated": "2026-04-30T10:00:00Z",
        "executions": [{"workflow": "operator_today", "status": "success"}],
        "aggregate_stats": {
            "total_executions": 10,
            "success_rate": 0.9,
            "avg_duration_seconds": 45.0,
            "escalation_rate": 0.1,
        },
        "notes": "",
    }
    path = vault / "runtime" / "memory" / "scorecards" / f"{runtime_id}.json"
    path.write_text(json.dumps(scorecard), encoding="utf-8")
    return path


# ── TestListRuntimes ──────────────────────────────────────────────────────────

class TestListRuntimes:
    def test_empty_adapters_dir(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = list_registered_runtimes(vault)
        assert result["ok"] is True
        assert result["runtime_count"] == 0

    def test_detects_registered_runtime(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_profile(rt_dir)
        result = list_registered_runtimes(vault)
        assert result["runtime_count"] == 1
        assert result["runtimes"][0]["runtime_id"] == "claude"

    def test_file_presence_flags(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_profile(rt_dir)
        _write_ledger(rt_dir)
        result = list_registered_runtimes(vault)
        entry = result["runtimes"][0]
        assert entry["has_profile"] is True
        assert entry["has_identity_ledger"] is True
        assert entry["has_nav_map"] is False
        assert entry["has_scorecard"] is False

    def test_multiple_runtimes(self, tmp_path):
        vault = _make_vault(tmp_path)
        for name in ("claude", "hermes", "openclaw"):
            _make_runtime(vault, name)
        result = list_registered_runtimes(vault)
        ids = {r["runtime_id"] for r in result["runtimes"]}
        assert ids == {"claude", "hermes", "openclaw"}


# ── TestInspectErrors ─────────────────────────────────────────────────────────

class TestInspectErrors:
    def test_missing_runtime_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_runtime_memory(vault, "ghost")
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_error_has_surface(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_runtime_memory(vault, "ghost")
        assert result["surface"] == "studio_memory_inspector"

    def test_error_has_boundary(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_runtime_memory(vault, "ghost")
        assert result["boundary"]["writes_memory_files"] is False
        assert result["boundary"]["canonical_mutation_allowed"] is False


# ── TestInspectProfile ────────────────────────────────────────────────────────

class TestInspectProfile:
    def test_profile_section_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_profile(rt_dir)
        result = inspect_runtime_memory(vault, "claude")
        assert result["ok"] is True
        assert result["profile"] is not None

    def test_profile_contains_summary_fields(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_profile(rt_dir, runtime_id="claude")
        result = inspect_runtime_memory(vault, "claude")
        p = result["profile"]
        assert p["runtime_id"] == "claude"
        assert "primary_goals" in p
        assert "domain_focus" in p

    def test_profile_none_when_missing(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        assert result["ok"] is True
        assert result["profile"] is None

    def test_files_present_reflects_profile(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_profile(rt_dir)
        result = inspect_runtime_memory(vault, "claude")
        assert result["files_present"]["profile"] is True
        assert result["files_present"]["identity_ledger"] is False


# ── TestInspectLedger ─────────────────────────────────────────────────────────

class TestInspectLedger:
    def test_ledger_section_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_ledger(rt_dir)
        result = inspect_runtime_memory(vault, "claude")
        assert result["identity_ledger"] is not None

    def test_ledger_correction_count(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_ledger(rt_dir)
        result = inspect_runtime_memory(vault, "claude")
        assert result["identity_ledger"]["correction_count"] == 1

    def test_ledger_identity_summary(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_ledger(rt_dir)
        result = inspect_runtime_memory(vault, "claude")
        assert "operator-assistant" in result["identity_ledger"]["identity_summary"]

    def test_ledger_none_when_missing(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        assert result["identity_ledger"] is None


# ── TestInspectNavMap ─────────────────────────────────────────────────────────

class TestInspectNavMap:
    def test_nav_map_section_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_nav_map(rt_dir)
        result = inspect_runtime_memory(vault, "claude")
        assert result["nav_map"] is not None

    def test_nav_map_route_count(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_nav_map(rt_dir)
        result = inspect_runtime_memory(vault, "claude")
        assert result["nav_map"]["route_pattern_count"] == 2

    def test_nav_map_none_when_missing(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        assert result["nav_map"] is None


# ── TestInspectScorecard ──────────────────────────────────────────────────────

class TestInspectScorecard:
    def test_scorecard_section_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        _write_scorecard(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        assert result["scorecard"] is not None

    def test_scorecard_aggregate_stats(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        _write_scorecard(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        sc = result["scorecard"]
        assert sc["total_executions"] == 10
        assert sc["success_rate"] == 0.9

    def test_scorecard_none_when_missing(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        assert result["scorecard"] is None


# ── TestFilesPresent ──────────────────────────────────────────────────────────

class TestFilesPresent:
    def test_all_false_for_empty_runtime(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        fp = result["files_present"]
        assert not any(fp.values())

    def test_all_true_when_all_files_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = _make_runtime(vault, "claude")
        _write_profile(rt_dir)
        _write_ledger(rt_dir)
        _write_nav_map(rt_dir)
        _write_scorecard(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        fp = result["files_present"]
        assert fp["profile"] is True
        assert fp["identity_ledger"] is True
        assert fp["nav_map"] is True
        assert fp["scorecard"] is True

    def test_files_present_has_repair_key(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_runtime(vault, "claude")
        result = inspect_runtime_memory(vault, "claude")
        assert "repair" in result["files_present"]
