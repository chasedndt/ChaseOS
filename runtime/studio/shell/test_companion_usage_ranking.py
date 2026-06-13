"""Tests for runtime usage-backed home companion ranking.

Covers:
  - get_runtime_usage_ranking() API method (backend)
  - AOR audit record parsing (manifest_snapshot.runtime_adapter)
  - Bus heartbeat recency integration
  - Score computation (AOR weight=3, bus_heartbeat weight=1)
  - resolveHomeCompanionCandidate() step 2 contract (via companion.js source scan)
  - Fallback chain when ranking is empty
  - Public API surface (getUsageRanking exposed on CompanionSystem)
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    """Minimal vault structure for usage ranking tests."""
    activity = tmp_path / "07_LOGS" / "Agent-Activity"
    activity.mkdir(parents=True)
    return tmp_path


def _write_audit(activity_dir: Path, name: str, runtime_adapter: str, status: str = "success") -> Path:
    """Write a minimal AOR audit record."""
    record = {
        "audit_id": f"test-{name}",
        "workflow_id": f"wf_{name}",
        "timestamp_utc": "2026-05-30T10:00:00+00:00",
        "status": status,
        "manifest_snapshot": {
            "id": f"wf_{name}",
            "runtime_adapter": runtime_adapter,
        },
    }
    path = activity_dir / f"{name}.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def _make_api(vault_root: str):
    from runtime.studio.shell.api import StudioAPI
    api = StudioAPI.__new__(StudioAPI)
    api._vault_root = vault_root
    return api


# ---------------------------------------------------------------------------
# Backend: get_runtime_usage_ranking
# ---------------------------------------------------------------------------

class TestGetRuntimeUsageRanking:
    def test_empty_activity_dir_returns_ok_empty(self, vault: Path):
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        assert result["ok"] is True
        assert result["data"]["ranked"] == []
        assert result["data"]["top_runtime"] is None
        assert result["data"]["total_aor_records_scanned"] == 0

    def test_single_runtime_returns_it_as_top(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "run1", "hermes")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        assert result["ok"] is True
        assert result["data"]["top_runtime"] == "hermes"
        ranked = result["data"]["ranked"]
        assert len(ranked) == 1
        assert ranked[0]["runtime_id"] == "hermes"
        assert ranked[0]["aor_execution_count"] == 1
        assert ranked[0]["score"] == 3  # 1 AOR × 3

    def test_multiple_runtimes_ranked_by_aor_count(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "h1", "hermes")
        _write_audit(activity, "h2", "hermes")
        _write_audit(activity, "h3", "hermes")
        _write_audit(activity, "o1", "openclaw")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        ranked = result["data"]["ranked"]
        assert ranked[0]["runtime_id"] == "hermes"
        assert ranked[0]["aor_execution_count"] == 3
        assert ranked[0]["score"] == 9  # 3 × 3
        assert ranked[1]["runtime_id"] == "openclaw"
        assert ranked[1]["aor_execution_count"] == 1
        assert ranked[1]["score"] == 3  # 1 × 3

    def test_aor_score_weight_is_3_per_record(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "h1", "hermes")
        _write_audit(activity, "h2", "hermes")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        assert result["data"]["ranked"][0]["score"] == 6  # 2 × 3

    def test_bus_heartbeat_adds_1_point(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "h1", "hermes")
        mock_hb = [{
            "runtime": "Hermes",
            "last_seen": "2026-05-30T10:00:00+00:00",
        }]
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=mock_hb):
            result = api.get_runtime_usage_ranking()
        ranked = result["data"]["ranked"]
        assert ranked[0]["has_bus_heartbeat"] is True
        assert ranked[0]["score"] == 4  # 1 AOR × 3 + 1 bus heartbeat

    def test_bus_heartbeat_uses_last_seen_field(self, vault: Path):
        """Confirms 'last_seen' is the correct field (not 'last_heartbeat_at')."""
        mock_hb = [
            {"runtime": "Hermes", "last_seen": "2026-05-30T10:00:00+00:00"},
            {"runtime": "OpenClaw", "last_heartbeat_at": "2026-05-30T09:00:00+00:00"},  # old field name
        ]
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=mock_hb):
            result = api.get_runtime_usage_ranking()
        runtimes = {r["runtime_id"]: r for r in result["data"]["ranked"]}
        assert runtimes["hermes"]["has_bus_heartbeat"] is True    # last_seen present
        assert runtimes["openclaw"]["has_bus_heartbeat"] is True  # last_heartbeat_at fallback

    def test_runtime_with_only_bus_heartbeat_included(self, vault: Path):
        """Runtime that never ran an AOR job still appears if it has a heartbeat."""
        mock_hb = [{"runtime": "Archon", "last_seen": "2026-05-30T10:00:00+00:00"}]
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=mock_hb):
            result = api.get_runtime_usage_ranking()
        runtimes = {r["runtime_id"]: r for r in result["data"]["ranked"]}
        assert "archon" in runtimes
        assert runtimes["archon"]["aor_execution_count"] == 0
        assert runtimes["archon"]["score"] == 1

    def test_evidence_sources_populated_correctly(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "h1", "hermes")
        mock_hb = [{"runtime": "Hermes", "last_seen": "2026-05-30T10:00:00+00:00"}]
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=mock_hb):
            result = api.get_runtime_usage_ranking()
        ranked = result["data"]["ranked"]
        hermes = next(r for r in ranked if r["runtime_id"] == "hermes")
        assert "aor_audit_records" in hermes["evidence_sources"]
        assert "bus_heartbeat" in hermes["evidence_sources"]

    def test_runtime_adapter_case_normalised(self, vault: Path):
        """Handles mixed-case runtime_adapter values."""
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "h1", "Hermes")   # capitalised
        _write_audit(activity, "h2", "HERMES")   # upper
        _write_audit(activity, "h3", "hermes")   # lower
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        ranked = result["data"]["ranked"]
        assert len(ranked) == 1
        assert ranked[0]["runtime_id"] == "hermes"
        assert ranked[0]["aor_execution_count"] == 3

    def test_malformed_json_files_skipped_gracefully(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        (activity / "bad.json").write_text("not json!", encoding="utf-8")
        _write_audit(activity, "h1", "hermes")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        assert result["ok"] is True
        assert result["data"]["ranked"][0]["runtime_id"] == "hermes"
        assert result["data"]["ranked"][0]["aor_execution_count"] == 1

    def test_missing_runtime_adapter_field_skipped(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        # Record without manifest_snapshot.runtime_adapter
        (activity / "no_ra.json").write_text(
            json.dumps({"audit_id": "x", "manifest_snapshot": {}}),
            encoding="utf-8",
        )
        _write_audit(activity, "h1", "hermes")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        runtimes = {r["runtime_id"] for r in result["data"]["ranked"]}
        assert "hermes" in runtimes
        # No phantom empty-string runtime
        assert "" not in runtimes

    def test_bus_error_falls_back_gracefully(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "h1", "hermes")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", side_effect=RuntimeError("db error")):
            result = api.get_runtime_usage_ranking()
        # AOR data still returned; bus heartbeat just absent
        assert result["ok"] is True
        ranked = result["data"]["ranked"]
        assert ranked[0]["runtime_id"] == "hermes"
        assert ranked[0]["has_bus_heartbeat"] is False
        assert ranked[0]["score"] == 3

    def test_ties_broken_alphabetically(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "a1", "zclaw")
        _write_audit(activity, "b1", "archon")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        ids = [r["runtime_id"] for r in result["data"]["ranked"]]
        assert ids == ["archon", "zclaw"]  # same score, alphabetical

    def test_total_records_scanned_count(self, vault: Path):
        activity = vault / "07_LOGS" / "Agent-Activity"
        _write_audit(activity, "h1", "hermes")
        _write_audit(activity, "h2", "hermes")
        _write_audit(activity, "o1", "openclaw")
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        assert result["data"]["total_aor_records_scanned"] == 3

    def test_runtimes_with_bus_heartbeat_count(self, vault: Path):
        mock_hb = [
            {"runtime": "Hermes", "last_seen": "2026-05-30T10:00:00+00:00"},
            {"runtime": "OpenClaw", "last_seen": "2026-05-29T10:00:00+00:00"},
        ]
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=mock_hb):
            result = api.get_runtime_usage_ranking()
        assert result["data"]["runtimes_with_bus_heartbeat"] == 2

    def test_result_envelope_is_ok(self, vault: Path):
        api = _make_api(str(vault))
        with patch("runtime.agent_bus.bus.list_heartbeats", return_value=[]):
            result = api.get_runtime_usage_ranking()
        assert result["ok"] is True
        assert result["status"] == "ok"
        assert result["surface"] == "get_runtime_usage_ranking"
        assert "ranked" in result["data"]
        assert "top_runtime" in result["data"]


# ---------------------------------------------------------------------------
# Frontend: companion.js source contract
# ---------------------------------------------------------------------------

COMPANION_JS = Path(__file__).parent / "frontend" / "companion.js"


class TestCompanionJsUsageRankingContract:
    def test_usage_ranking_variable_declared(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "_usageRanking" in src

    def test_init_backend_sync_calls_get_runtime_usage_ranking(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "get_runtime_usage_ranking" in src

    def test_resolve_home_companion_candidate_step2_uses_usage_ranking(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        # The function must reference _usageRanking in its resolution logic
        assert "most_used_runtime" in src
        assert "_usageRanking" in src

    def test_resolve_fallback_chain_preserved(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "explicit_selection" in src
        assert "persistence_priority" in src
        assert "first_hatched" in src

    def test_get_usage_ranking_exposed_in_public_api(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "getUsageRanking" in src

    def test_evidence_source_field_present(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "evidenceSources" in src or "evidence_sources" in src

    def test_aor_execution_count_field_present(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "aorExecutionCount" in src

    def test_version_is_v2_2_or_later(self):
        """Version should be v2.2 or higher (v3.0 after identity upgrade pass)."""
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "v2.2" in src or "v2.3" in src or "v2.4" in src or "v3.0" in src

    def test_header_documents_usage_backed_selection(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "Usage-backed" in src or "usage-backed" in src

    def test_init_backend_sync_has_two_steps(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        # Step A = companion sync, Step B = usage ranking
        assert "Step A" in src
        assert "Step B" in src

    def test_hermes_fallback_still_present_for_first_render(self):
        """Step 3 hermes fallback must remain for pre-async first render."""
        src = COMPANION_JS.read_text(encoding="utf-8")
        assert "hermes_24_7_runtime" in src

    def test_refresh_home_companion_column_called_after_ranking(self):
        src = COMPANION_JS.read_text(encoding="utf-8")
        # After loading ranking, should trigger a re-render
        assert "_refreshHomeCompanionColumn" in src


# ---------------------------------------------------------------------------
# Live vault smoke test (real data, read-only)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).parents[3]


class TestLiveVaultUsageRanking:
    def test_live_ranking_returns_ok(self):
        api = _make_api(str(VAULT_ROOT))
        result = api.get_runtime_usage_ranking()
        assert result["ok"] is True

    def test_live_hermes_is_top_runtime(self):
        """Hermes has the most AOR executions on this vault instance."""
        api = _make_api(str(VAULT_ROOT))
        result = api.get_runtime_usage_ranking()
        assert result["data"]["top_runtime"] == "hermes"

    def test_live_hermes_has_more_aor_records_than_openclaw(self):
        api = _make_api(str(VAULT_ROOT))
        result = api.get_runtime_usage_ranking()
        ranked = {r["runtime_id"]: r for r in result["data"]["ranked"]}
        assert "hermes" in ranked
        assert "openclaw" in ranked
        assert ranked["hermes"]["aor_execution_count"] > ranked["openclaw"]["aor_execution_count"]

    def test_live_bus_heartbeats_detected(self):
        """Bus has heartbeat entries from multiple runtimes on this vault."""
        api = _make_api(str(VAULT_ROOT))
        result = api.get_runtime_usage_ranking()
        assert result["data"]["runtimes_with_bus_heartbeat"] >= 1

    def test_live_hermes_has_both_evidence_sources(self):
        api = _make_api(str(VAULT_ROOT))
        result = api.get_runtime_usage_ranking()
        ranked = {r["runtime_id"]: r for r in result["data"]["ranked"]}
        hermes = ranked["hermes"]
        assert "aor_audit_records" in hermes["evidence_sources"]
        assert "bus_heartbeat" in hermes["evidence_sources"]

    def test_live_ranking_json_serialisable(self):
        api = _make_api(str(VAULT_ROOT))
        result = api.get_runtime_usage_ranking()
        # Must not raise
        json.dumps(result)
