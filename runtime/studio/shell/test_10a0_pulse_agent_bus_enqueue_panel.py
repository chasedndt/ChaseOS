from __future__ import annotations

import inspect
from pathlib import Path

from runtime.studio import pulse_agent_bus_enqueue_panel as panel
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT = Path(__file__).resolve().parents[3]
FRONTEND = Path(__file__).resolve().parent / "frontend"


def test_pulse_agent_bus_enqueue_panel_is_read_only(tmp_path):
    data = panel.build_pulse_agent_bus_enqueue_panel(tmp_path)

    assert data["surface"] == "studio_pulse_agent_bus_enqueue_panel"
    assert data["native_panel"]["panel_id"] == "pulse-enqueue"
    assert data["native_panel"]["read_only"] is True
    assert data["native_panel"]["frontend_target"] == "panel-pulse-enqueue"
    assert data["roadmap_item"] == "10A0 - Studio Acquisition Intake Cockpit"
    assert data["possible_writes"] == []
    assert data["allowed_actions"] == ["inspect-pulse-agent-bus-enqueue-panel"]
    assert data["summary"]["displayed_request_count"] == 0

    authority = data["authority"]
    assert authority["read_only"] is True
    for key in (
        "shell_action_available",
        "approval_grant_from_shell",
        "approval_request_write_from_shell",
        "evidence_write_from_shell",
        "live_enqueue_from_shell",
        "agent_bus_task_write_from_shell",
        "runtime_dispatch_from_shell",
        "candidate_apply_allowed",
        "review_response_ingest_allowed",
        "schedule_activation_allowed",
        "provider_or_connector_call_allowed",
        "canonical_writeback_allowed",
    ):
        assert authority[key] is False


def test_pulse_agent_bus_enqueue_panel_source_avoids_live_writers():
    source = inspect.getsource(panel)
    forbidden_tokens = (
        "from runtime.pulse.bus_enqueue import",
        "import runtime.pulse.bus_enqueue",
        "enqueue_pulse_review_task",
        "run_pulse_enqueue_pipeline",
        "persist_agent_bus_enqueue_approval_request",
        "persist_agent_bus_enqueue_evidence",
        "create_task",
        "update_task_status",
        "claim_task",
        "write_text",
        "open(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_studio_api_exposes_pulse_agent_bus_enqueue_panel(tmp_path):
    resp = StudioAPI(tmp_path).get_pulse_agent_bus_enqueue_panel()

    assert resp["ok"] is True
    assert resp["surface"] == "pulse_agent_bus_enqueue_panel"
    assert resp["data"]["native_panel"]["frontend_target"] == "panel-pulse-enqueue"
    assert resp["data"]["possible_writes"] == []
    assert resp["data"]["authority"]["live_enqueue_from_shell"] is False


def test_native_shell_registry_mounts_pulse_agent_bus_enqueue_panel():
    registry = build_native_shell_panel_registry(VAULT)
    panels = {item["id"]: item for item in registry["panels"]}

    mounted = panels["pulse-enqueue"]
    assert mounted["status"] == "mounted"
    assert mounted["read_only"] is True
    assert mounted["frontend_target"] == "panel-pulse-enqueue"
    assert mounted["route_hint"] == "#pulse-enqueue"
    assert mounted["api_methods"] == ["get_pulse_agent_bus_enqueue_panel"]
    assert mounted["blocked_authority"]["canonical_mutation"] is False
    assert mounted["blocked_authority"]["workflow_execution"] is False
    assert "approval grants" in mounted["blocked_reason"]
    assert "not mounted" in mounted["blocked_reason"]
    assert registry["readiness"]["pulse_agent_bus_enqueue_panel_mounted"] is True
    assert registry["readiness"]["mounted_panel_count"] >= 25


def test_pulse_agent_bus_enqueue_frontend_mount_contracts():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")
    css = (FRONTEND / "styles.css").read_text(encoding="utf-8")

    assert 'data-panel="pulse-enqueue"' in html
    assert 'aria-label="Review Queue"' in html
    assert 'id="panel-pulse-enqueue"' in html
    assert 'data-read-only="true"' in html
    assert 'id="pulse-enqueue-summary"' in html
    assert 'id="pulse-enqueue-preflight-list"' in html
    assert 'id="pulse-enqueue-request-list"' in html
    assert 'id="pulse-enqueue-command-list"' in html
    assert 'id="pulse-enqueue-refresh-btn"' in html

    assert "let pulseEnqueueLoaded = false;" in js
    assert "_initPulseEnqueuePanel();" in js
    assert "if (id === 'pulse-enqueue') loadPulseEnqueue();" in js
    assert "async function loadPulseEnqueue()" in js
    assert "function renderPulseEnqueuePanel(data)" in js
    assert "function _initPulseEnqueuePanel()" in js
    assert "get_pulse_agent_bus_enqueue_panel()" in js
    assert "escHtml" in js[js.index("async function loadPulseEnqueue()") : js.index("let siteopsPanelTab")]

    enqueue_js = js[js.index("// -- 10A0: Pulse Agent Bus Enqueue") : js.index("let siteopsPanelTab")]
    for forbidden in (
        "run_acquisition_dry_run",
        "run_pulse_enqueue_pipeline",
        "enqueue_pulse_review_task",
        "create_task",
        "toggle_schedule",
        "execute_activation",
        "run_pulse(",
    ):
        assert forbidden not in enqueue_js

    assert ".pulse-enqueue-panel" in css
    assert ".pulse-enqueue-summary" in css
    assert ".pulse-enqueue-tab" in css
    assert ".pulse-enqueue-card" in css
    assert ".pulse-enqueue-command" in css
    assert ".pulse-enqueue-slot" in css

    enqueue_css = css[css.index("/* -- 10A0: Pulse Agent Bus Enqueue") : css.index("Pass 10L")]
    for forbidden_var in (
        "--bg-panel",
        "--bg-secondary",
        "--bg-tertiary",
        "--border-color",
        "--accent-color",
    ):
        assert forbidden_var not in enqueue_css


def test_pulse_agent_bus_enqueue_panel_degrades_read_only_when_plan_unavailable(monkeypatch, tmp_path):
    def _raise(*_args, **_kwargs):
        raise RuntimeError("plan unavailable")

    monkeypatch.setattr(panel, "build_agent_bus_enqueue_plan", _raise)

    data = panel.build_pulse_agent_bus_enqueue_panel(tmp_path)

    assert data["ok"] is False
    assert data["readiness"]["pulse_enqueue_panel_ready"] is False
    assert data["readiness"]["warnings"] == ["pulse_enqueue_plan_unavailable"]
    assert data["possible_writes"] == []
    assert data["authority"]["live_enqueue_from_shell"] is False
    assert data["native_panel"]["mounted"] is True
