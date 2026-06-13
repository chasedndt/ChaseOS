from __future__ import annotations

from pathlib import Path

from runtime.studio import pulse_schedule_proof_panel as panel
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT = Path(__file__).resolve().parents[3]
FRONTEND = Path(__file__).resolve().parent / "frontend"


def _control(control_id: str, *, write: bool = False, enabled: bool = True) -> dict:
    return {
        "id": control_id,
        "label": control_id.replace("_", " "),
        "command": f"chaseos pulse {control_id} --json",
        "studio_action": control_id.replace("_", "-"),
        "studio_command": f"chaseos studio acquisition-cockpit --action {control_id.replace('_', '-')} --json",
        "write_action": write,
        "requires_confirmation": write,
        "enabled": enabled,
        "writes_only": ["07_LOGS/Pulse-Decks/proof/"] if write else [],
        "required_evidence_ref_flags": ["--operator-approval-ref"] if write else [],
    }


def _fake_cockpit(vault_root: Path, profile: str = "strikezone") -> dict:
    return {
        "pulse_roadmap_controls": {
            "surface": "studio_pulse_roadmap_controls",
            "roadmap_item": "10A0 - Studio Acquisition Intake Cockpit",
            "profile": profile,
            "status": "ready",
            "live_schedule_runner": {
                "surface": "studio_pulse_schedule_runner_status",
                "available": True,
                "status": "BLOCKED",
                "schedule_count": 2,
                "ready_schedule_count": 1,
                "enabled_schedule_count": 1,
                "missing_evidence_count": 0,
                "schedule_activation_allowed": False,
                "schedule_daemon_started": False,
            },
            "schedule_activation_gate": {
                "surface": "studio_pulse_schedule_activation_gate",
                "available": True,
                "status": "blocked",
                "gate_status": "blocked",
                "schedule_count": 2,
                "ready_schedule_count": 1,
                "missing_evidence_count": 2,
                "missing_evidence_slots": ["operator_approval_ref", "permission_envelope_ref"],
                "write_root": "07_LOGS/Pulse-Decks/native-schedule-activation-requests/",
                "request_action_id": "pulse-schedule-activation-request",
                "schedule_activation_allowed": False,
                "schedule_daemon_started": False,
            },
            "schedule_run_queue_audit_proof": {
                "surface": "studio_pulse_schedule_run_queue_audit_proof",
                "available": True,
                "status": "blocked",
                "proof_status": "blocked",
                "schedule_count": 2,
                "missing_evidence_count": 1,
                "missing_evidence_slots": ["audit_identity_ref"],
                "write_root": "07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/",
                "write_action_id": "pulse-schedule-run-queue-audit-write-proof",
                "real_run_queue_written": False,
                "real_audit_event_written": False,
                "workflow_execution_allowed": False,
                "canonical_writeback_allowed": False,
            },
            "schedule_supervised_activation_execution": {
                "surface": "studio_pulse_schedule_supervised_activation_execution",
                "available": True,
                "status": "blocked",
                "execution_status": "blocked",
                "schedule_count": 2,
                "missing_evidence_count": 1,
                "missing_evidence_slots": ["rollback_plan_ref"],
                "write_root": "07_LOGS/Pulse-Decks/native-schedule-activation-executions/",
                "write_action_id": "pulse-schedule-supervised-activation-execution-write-proof",
                "schedule_activation_executed": False,
                "schedule_daemon_started": False,
                "real_run_queue_written": False,
                "real_audit_event_written": False,
                "workflow_execution_allowed": False,
                "canonical_writeback_allowed": False,
            },
            "agent_bus_enqueue": {
                "available": True,
                "approved_action_id": "pulse-enqueue-approved",
            },
            "controls": [
                _control("pulse_schedule_runner_status"),
                _control("pulse_schedule_activation_gate"),
                _control("pulse_schedule_activation_request", write=True),
                _control("pulse_schedule_run_queue_audit_proof"),
                _control("pulse_schedule_run_queue_audit_write_proof", write=True),
                _control("pulse_schedule_supervised_activation_execution_proof"),
                _control("pulse_schedule_supervised_activation_execution_write_proof", write=True),
                _control("pulse_enqueue_preview"),
                _control("pulse_enqueue_approved", write=True),
            ],
            "authority": {
                "schedule_activation_allowed": False,
                "schedule_daemon_start_allowed": False,
                "canonical_writeback_allowed": False,
            },
        }
    }


def test_pulse_schedule_proof_panel_is_read_only(monkeypatch, tmp_path):
    monkeypatch.setattr(panel, "build_acquisition_cockpit_model", _fake_cockpit)

    data = panel.build_pulse_schedule_proof_panel(tmp_path)

    assert data["ok"] is True
    assert data["surface"] == "studio_pulse_schedule_proof_panel"
    assert data["native_panel"]["panel_id"] == "pulse-schedule-proof"
    assert data["summary"]["proof_lane_count"] == 4
    assert data["summary"]["write_control_count"] == 3
    assert data["summary"]["execution_action_exposed"] is False
    assert data["summary"]["activation_allowed"] is False
    assert data["possible_writes"] == []
    assert data["authority"]["read_only"] is True
    assert data["authority"]["writes_proof_artifacts_from_shell"] is False
    assert data["authority"]["activates_schedules"] is False
    assert data["authority"]["exposes_execute_activation"] is False
    assert data["authority"]["writes_agent_bus_tasks"] is False
    assert data["authority"]["executes_workflows"] is False
    assert data["allowed_actions"] == ["inspect-pulse-schedule-proof-panel"]


def test_pulse_schedule_proof_panel_filters_enqueue_controls(monkeypatch, tmp_path):
    monkeypatch.setattr(panel, "build_acquisition_cockpit_model", _fake_cockpit)

    data = panel.build_pulse_schedule_proof_panel(tmp_path)

    control_ids = {control["id"] for control in data["display_controls"]}
    assert "pulse_enqueue_preview" not in control_ids
    assert "pulse_enqueue_approved" not in control_ids
    assert "pulse_schedule_activation_request" in control_ids
    assert all(control["shell_action_available"] is False for control in data["display_controls"])
    assert all(lane["write_shell_action_available"] is False for lane in data["proof_lanes"])
    assert all(lane["live_execution_allowed"] is False for lane in data["proof_lanes"])


def test_pulse_schedule_proof_panel_degrades_without_writes(monkeypatch, tmp_path):
    def _raise(_vault: Path, profile: str = "strikezone") -> dict:
        raise RuntimeError("source unavailable")

    monkeypatch.setattr(panel, "build_acquisition_cockpit_model", _raise)

    data = panel.build_pulse_schedule_proof_panel(tmp_path)

    assert data["ok"] is False
    assert data["possible_writes"] == []
    assert data["native_panel"]["mounted"] is True
    assert data["readiness"]["pulse_schedule_proof_panel_ready"] is False
    assert data["readiness"]["warnings"] == ["pulse_schedule_proof_panel_source_unavailable"]
    assert data["authority"]["read_only"] is True


def test_studio_api_exposes_pulse_schedule_proof_panel(monkeypatch, tmp_path):
    monkeypatch.setattr(panel, "build_acquisition_cockpit_model", _fake_cockpit)

    resp = StudioAPI(tmp_path).get_pulse_schedule_proof_panel()

    assert resp["ok"] is True
    assert resp["surface"] == "pulse_schedule_proof_panel"
    assert resp["data"]["native_panel"]["frontend_target"] == "panel-pulse-schedule-proof"
    assert resp["data"]["possible_writes"] == []


def test_native_shell_registry_mounts_pulse_schedule_proof_panel():
    registry = build_native_shell_panel_registry(VAULT)
    panels = {item["id"]: item for item in registry["panels"]}

    mounted = panels["pulse-schedule-proof"]
    assert mounted["status"] == "mounted"
    assert mounted["read_only"] is True
    assert mounted["frontend_target"] == "panel-pulse-schedule-proof"
    assert mounted["route_hint"] == "#pulse-schedule-proof"
    assert mounted["api_methods"] == ["get_pulse_schedule_proof_panel"]
    assert mounted["blocked_authority"]["canonical_mutation"] is False
    assert mounted["blocked_authority"]["workflow_execution"] is False
    assert registry["readiness"]["pulse_schedule_proof_panel_mounted"] is True
    assert registry["readiness"]["mounted_panel_count"] >= 23


def test_pulse_schedule_proof_frontend_mount_contracts():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")
    css = (FRONTEND / "styles.css").read_text(encoding="utf-8")

    assert 'data-panel="pulse-schedule-proof"' in html
    assert 'title="Proactive Briefings"' in html
    assert 'id="panel-pulse-schedule-proof"' in html
    assert 'id="pulse-schedule-proof-body"' in html
    assert 'id="pulse-schedule-proof-summary"' in html
    assert 'id="pulse-schedule-proof-refresh-btn"' in html

    assert "let pulseScheduleProofLoaded = false;" in js
    assert "_initPulseScheduleProofPanel();" in js
    assert "if (id === 'pulse-schedule-proof') loadPulseScheduleProof();" in js
    assert "function loadPulseScheduleProof()" in js
    assert "get_pulse_schedule_proof_panel()" in js

    section_start = js.index("// -- 10A0: Pulse Schedule Proofs")
    section_end = js.index("Pass 10L", section_start)
    pulse_js = js[section_start:section_end]
    assert "run_acquisition_dry_run" not in pulse_js
    assert "toggle_schedule" not in pulse_js
    assert "run_pulse" not in pulse_js
    assert "execute_activation" not in pulse_js

    assert ".pulse-schedule-proof-panel" in css
    assert ".pulse-schedule-proof-card" in css
    assert ".pulse-schedule-proof-command" in css
    css_start = css.index("/* -- 10A0: Pulse Schedule Proofs")
    css_end = css.index("Pass 10L", css_start)
    pulse_css = css[css_start:css_end]
    for forbidden_var in (
        "--bg-panel",
        "--bg-secondary",
        "--bg-tertiary",
        "--border-color",
        "--accent-color",
    ):
        assert forbidden_var not in pulse_css
