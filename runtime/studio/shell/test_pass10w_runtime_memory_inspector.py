"""Pass 10W - Runtime Memory/RNM Detail Inspector tests."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

VAULT = Path(__file__).resolve().parents[3]
SHELL = Path(__file__).resolve().parent
sys.path.insert(0, str(VAULT))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_runtime_memory(vault: Path) -> None:
    _write_json(
        vault / "runtime/memory/adapters/codex/profile.json",
        {
            "runtime_id": "codex",
            "runtime_label": "Codex",
            "status": "active",
            "updated_at": "2026-05-07T00:00:00Z",
            "behavioral_profile": {
                "primary_goals": ["repo-grounded implementation"],
                "domain_focus": ["runtime/studio"],
                "interaction_style": "bounded coding agent",
            },
            "governance_boundary": {"canonical_mutation_allowed": False},
        },
    )
    _write_json(
        vault / "runtime/memory/adapters/codex/identity-ledger.json",
        {
            "runtime_id": "codex",
            "status": "seeded",
            "updated_at": "2026-05-07T00:00:00Z",
            "identity_summary": {"posture": "bounded developer"},
            "correction_history": [{"id": "repo_truth"}],
            "drift_signals": [{"id": "overclaim"}],
            "doctrine_adherence": {"gate_bypass": False},
            "authority_boundaries": {"writes_gate": False},
        },
    )
    _write_json(
        vault / "runtime/memory/nav/codex/nav-map.json",
        {
            "runtime_id": "codex",
            "updated_at": "2026-05-07T00:00:00Z",
            "successful_route_patterns": [{"task_class": "code.patch", "route": ["README.md", "runtime"]}],
            "common_escalation_triggers": [{"id": "protected_truth"}],
        },
    )
    _write_json(
        vault / "runtime/memory/scorecards/codex.json",
        {
            "runtime_id": "codex",
            "status": "seeded",
            "last_updated": "2026-05-07T00:00:00Z",
            "aggregate_stats": {
                "total_executions": 4,
                "success_rate": 0.75,
                "avg_duration_seconds": 10,
                "escalation_rate": 0.25,
            },
            "executions": [{"id": "run-1"}],
        },
    )
    _write_json(
        vault / "runtime/memory/repair/codex.json",
        {
            "runtime_id": "codex",
            "incident_candidates": [{"id": "candidate-1"}],
            "repair_patterns": [{"id": "pattern-1"}],
        },
    )
    _write_json(
        vault / "runtime/memory/adapters/hermes/profile.json",
        {
            "runtime_id": "hermes",
            "runtime_label": "Hermes",
            "status": "partial",
            "behavioral_profile": {},
        },
    )
    malformed = vault / "runtime/memory/repair/hermes.json"
    malformed.parent.mkdir(parents=True, exist_ok=True)
    malformed.write_text("{not-json", encoding="utf-8")


@pytest.fixture()
def api(tmp_path):
    from runtime.studio.shell.api import StudioAPI

    _seed_runtime_memory(tmp_path)
    return StudioAPI(str(tmp_path))


@pytest.fixture()
def registry(tmp_path):
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    return build_native_shell_panel_registry(str(tmp_path))


@pytest.fixture()
def html_text():
    return (SHELL / "frontend" / "index.html").read_text(encoding="utf-8")


@pytest.fixture()
def css_text():
    return (SHELL / "frontend" / "styles.css").read_text(encoding="utf-8")


@pytest.fixture()
def js_text():
    return (SHELL / "frontend" / "app.js").read_text(encoding="utf-8")


class TestRuntimeMemoryAPI:
    def test_runtime_list_returns_registered_runtimes(self, api):
        r = api.get_runtime_memory_runtimes()
        ids = {item["runtime_id"] for item in r["data"]["runtimes"]}
        assert r["ok"] is True
        assert {"codex", "hermes"} <= ids

    def test_runtime_list_presence_flags(self, api):
        r = api.get_runtime_memory_runtimes()
        codex = next(item for item in r["data"]["runtimes"] if item["runtime_id"] == "codex")
        assert codex["has_profile"] is True
        assert codex["has_identity_ledger"] is True
        assert codex["has_nav_map"] is True
        assert codex["has_scorecard"] is True
        assert codex["has_repair"] is True

    def test_nav_map_under_runtime_memory_nav_is_detected(self, api):
        r = api.get_runtime_memory_detail("codex")
        assert r["ok"] is True
        assert r["data"]["nav_map"]["route_pattern_count"] == 1
        assert r["data"]["files_present"]["nav_map"] is True

    def test_detail_returns_all_sections_where_present(self, api):
        r = api.get_runtime_memory_detail("codex")
        data = r["data"]
        assert data["profile"]["runtime_id"] == "codex"
        assert data["identity_ledger"]["correction_count"] == 1
        assert data["nav_map"]["escalation_trigger_count"] == 1
        assert data["scorecard"]["total_executions"] == 4
        assert data["repair"]["candidate_count"] == 1
        assert data["repair"]["pattern_count"] == 1

    def test_missing_optional_files_are_tolerated(self, api):
        r = api.get_runtime_memory_detail("hermes")
        assert r["ok"] is True
        assert r["data"]["profile"]["runtime_id"] == "hermes"
        assert r["data"]["identity_ledger"] is None
        assert r["data"]["nav_map"] is None
        assert r["data"]["scorecard"] is None
        assert r["data"]["repair"] is None

    def test_malformed_optional_json_does_not_crash_panel(self, api):
        r = api.get_runtime_memory_detail("hermes")
        assert r["ok"] is True
        assert r["data"]["files_present"]["repair"] is False

    def test_missing_runtime_fails_cleanly(self, api):
        r = api.get_runtime_memory_detail("missing-runtime")
        assert r["ok"] is False
        assert r["error"]["code"] == "runtime_not_found"

    def test_invalid_runtime_id_is_blocked(self, api):
        r = api.get_runtime_memory_detail("../codex")
        assert r["ok"] is False
        assert r["error"]["code"] == "invalid_runtime_id"


class TestPanelRegistry:
    def test_runtime_memory_panel_present(self, registry):
        ids = [panel["id"] for panel in registry["panels"]]
        assert "runtime-memory-inspector" in ids

    def test_runtime_memory_panel_contract(self, registry):
        panel = next(panel for panel in registry["panels"] if panel["id"] == "runtime-memory-inspector")
        assert panel["status"] == "mounted"
        assert panel["frontend_target"] == "panel-runtime-memory-inspector"
        assert panel["route_hint"] == "#runtime-memory-inspector"
        assert "get_runtime_memory_runtimes" in panel["api_methods"]
        assert "get_runtime_memory_detail" in panel["api_methods"]
        assert panel["read_only"] is True
        assert panel["blocked_authority"]["canonical_mutation"] is False

    def test_readiness_marker_advanced(self, registry):
        assert registry["readiness"]["runtime_memory_inspector_panel_mounted"] is True
        assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
        assert registry["readiness"]["declared_panel_count"] >= 29
        assert registry["readiness"]["mounted_panel_count"] >= 29

    def test_possible_writes_empty(self, registry):
        assert registry["authority"]["possible_writes"] == []


class TestHTML:
    def test_sidebar_button_present(self, html_text):
        assert 'data-panel="runtime-memory-inspector"' in html_text
        assert 'title="Memory Manager"' in html_text

    def test_panel_present(self, html_text):
        assert 'id="panel-runtime-memory-inspector"' in html_text
        assert 'data-read-only="true"' in html_text

    def test_panel_targets_present(self, html_text):
        assert 'id="runtime-memory-search"' in html_text
        assert 'id="runtime-memory-list"' in html_text
        assert 'id="runtime-memory-viewer"' in html_text
        assert 'id="runtime-memory-inspector-status"' in html_text


class TestCSS:
    def test_runtime_memory_panel_classes_present(self, css_text):
        assert ".runtime-memory-inspector-panel" in css_text
        assert ".runtime-memory-list" in css_text
        assert ".runtime-memory-item" in css_text
        assert ".runtime-memory-item--active" in css_text
        assert ".runtime-memory-viewer" in css_text
        assert ".runtime-memory-section" in css_text
        assert ".runtime-memory-badge--present" in css_text
        assert ".runtime-memory-badge--missing" in css_text


class TestJS:
    def test_runtime_memory_functions_present(self, js_text):
        assert "async function loadRuntimeMemoryInspector" in js_text
        assert "function renderRuntimeMemoryList" in js_text
        assert "async function loadRuntimeMemoryDetail" in js_text
        assert "function renderRuntimeMemoryDetail" in js_text
        assert "function runtimeMemorySection" in js_text
        assert "function _initRuntimeMemoryInspectorPanel" in js_text

    def test_runtime_memory_state_present(self, js_text):
        assert "runtimeMemoryInspectorLoaded" in js_text
        assert "runtimeMemorySelectedId" in js_text
        assert "_runtimeMemoryRuntimesAll" in js_text

    def test_panel_switch_wired(self, js_text):
        assert "if (id === 'runtime-memory-inspector') loadRuntimeMemoryInspector()" in js_text

    def test_init_called_in_on_shell_ready(self, js_text):
        assert "_initRuntimeMemoryInspectorPanel()" in js_text

    def test_api_calls_present(self, js_text):
        assert "get_runtime_memory_runtimes" in js_text
        assert "get_runtime_memory_detail" in js_text





