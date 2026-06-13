"""Tests for Phase 10 companion-surface read-only status aggregator."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase10_companion_surface_status import (
    REQUIRED_BLOCKERS,
    SURFACE_ID,
    build_phase10_companion_surface_status,
)


def _snapshot_files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _seed_operator_brief(root: Path) -> Path:
    path = root / "07_LOGS" / "Operator-Briefs" / "2026-05-12-test-brief.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Test Brief\n\nRead-only fixture.", encoding="utf-8")
    return path


def _seed_workflow_output(root: Path) -> Path:
    path = root / "07_LOGS" / "Workflow-Outputs" / "2026-05-12-test-output.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Test Workflow Output\n\nRead-only fixture.", encoding="utf-8")
    return path


def test_companion_surface_status_aggregates_read_only_status_and_blockers(tmp_path: Path) -> None:
    brief = _seed_operator_brief(tmp_path)
    output = _seed_workflow_output(tmp_path)
    before = _snapshot_files(tmp_path)

    payload = build_phase10_companion_surface_status(tmp_path, requested_runtime="hermes")

    after = _snapshot_files(tmp_path)

    assert payload["ok"] is True
    assert payload["surface"] == SURFACE_ID
    assert payload["read_only"] is True
    assert payload["companion_status"]["summary"]["selected_runtime_id"] == "hermes"
    assert payload["summary"]["companion_personality_grants_authority"] is False
    assert payload["summary"]["mobile_tablet_actions_route_through"] == ["Gate", "AOR", "StudioService"]
    assert payload["briefs"]["operator_briefs"]["exists"] is True
    assert payload["briefs"]["operator_briefs"]["file_count"] == 1
    assert payload["briefs"]["operator_briefs"]["latest_files"][0]["path"] == brief.relative_to(tmp_path).as_posix()
    assert payload["briefs"]["workflow_outputs"]["exists"] is True
    assert payload["briefs"]["workflow_outputs"]["file_count"] == 1
    assert payload["briefs"]["workflow_outputs"]["latest_files"][0]["path"] == output.relative_to(tmp_path).as_posix()
    assert REQUIRED_BLOCKERS.issubset(set(payload["blocked_live_authority"]))
    assert payload["authority"]["approval_artifact_write_allowed"] is False
    assert payload["authority"]["approval_consumption_allowed"] is False
    assert payload["authority"]["runtime_dispatch_allowed"] is False
    assert payload["authority"]["provider_or_gateway_call_allowed"] is False
    assert payload["authority"]["credential_or_config_mutation_allowed"] is False
    assert payload["authority"]["agent_bus_write_allowed"] is False
    assert payload["authority"]["canonical_writeback_allowed"] is False
    assert before == after


def test_companion_surface_status_degrades_when_optional_read_apis_are_absent(tmp_path: Path, monkeypatch) -> None:
    import runtime.studio.phase10_companion_surface_status as status

    def _raise(*args, **kwargs):  # noqa: ANN002, ANN003
        raise RuntimeError("fixture unavailable")

    monkeypatch.setattr(status, "_read_osril_summary", _raise)
    monkeypatch.setattr(status, "_read_approval_summary", _raise)

    payload = build_phase10_companion_surface_status(tmp_path)

    assert payload["ok"] is True
    assert payload["osril"]["available"] is False
    assert payload["approvals"]["available"] is False
    assert "osril_read_api_unavailable:fixture unavailable" in payload["warnings"]
    assert "approval_read_api_unavailable:fixture unavailable" in payload["warnings"]
    assert REQUIRED_BLOCKERS.issubset(set(payload["blocked_live_authority"]))


def test_companion_surface_status_api_and_registry_surface_are_read_only(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase10_companion_surface_status("hermes")
    registry = build_native_shell_panel_registry(tmp_path)
    companion_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "companion-surface"), {})
    readiness = registry.get("readiness") or {}

    assert api_status["ok"] is True
    assert api_status["surface"] == SURFACE_ID
    assert api_status["data"]["read_only"] is True
    assert "get_phase10_companion_surface_status" in (companion_panel.get("api_methods") or [])
    assert companion_panel.get("status") == "readiness_only"
    assert companion_panel.get("frontend_target") is None
    assert companion_panel.get("route_hint") is None
    assert companion_panel.get("read_only") is True
    assert companion_panel.get("possible_writes") == []
    assert readiness["phase10_companion_surface_status_ready"] is True
    assert readiness["phase10_companion_surface_live_authority_blocked"] is True


def test_companion_surface_registry_does_not_claim_missing_frontend_mount(tmp_path: Path) -> None:
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    registry = build_native_shell_panel_registry(tmp_path)
    companion_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "companion-surface"), {})
    frontend_html = (Path(__file__).parent / "shell" / "frontend" / "index.html").read_text(encoding="utf-8")

    assert 'data-panel="companion-surface"' not in frontend_html
    assert 'id="panel-companion-surface"' not in frontend_html
    assert companion_panel.get("status") != "mounted"
    assert companion_panel.get("frontend_target") is None


def test_companion_surface_status_is_json_safe_and_secret_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")

    payload = build_phase10_companion_surface_status(tmp_path)
    encoded = json.dumps(payload, sort_keys=True)

    assert "fixture-secret-not-returned" not in encoded
    assert "API_KEY" not in encoded.upper()
