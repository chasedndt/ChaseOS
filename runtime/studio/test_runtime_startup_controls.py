"""Tests for Studio runtime startup controls."""

from __future__ import annotations

from pathlib import Path
import inspect

import pytest

from runtime.studio import runtime_startup_controls as controls


def _test_vault(name: str) -> Path:
    path = Path(__file__).resolve().parents[2] / ".pytest-tmp" / "studio-runtime-startup-controls" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _fake_settings_report() -> dict:
    return {
        "action": "startup-surface-settings",
        "schema_version": 1,
        "read_only": True,
        "settings_write_enabled": True,
        "mutation_enabled": True,
        "runtime_count": 1,
        "surface_count": 1,
        "runtimes": [
            {
                "runtime_id": "hermes",
                "runtime_name": "Hermes",
                "settings": [
                    {
                        "surface_id": "gateway",
                        "ui_label": "Hermes Gateway",
                        "current_state": "registered",
                        "user_manageable": True,
                        "cli_mutation_enabled": True,
                        "startup_registration_kind": "windows-startup-folder",
                        "launch_profile": {"launch_kind": "wsl", "wsl_distro": "Ubuntu"},
                    }
                ],
            }
        ],
        "errors": [],
    }


def test_runtime_startup_controls_model_exposes_studio_commands(monkeypatch):
    monkeypatch.setattr(
        controls,
        "build_startup_surface_settings_report",
        lambda runtime_id, **kwargs: _fake_settings_report(),
    )

    model = controls.build_runtime_startup_controls_model(_test_vault("model"), "hermes")

    assert model["surface"] == "studio_runtime_startup_controls"
    assert model["mutation_actions_enabled"] is True
    assert model["studio_visual_toggle_built"] is True
    card = model["surface_cards"][0]
    assert card["runtime_id"] == "hermes"
    assert card["surface_id"] == "gateway"
    assert card["studio_control_enabled"] is True
    assert "studio runtime-startup-controls" in card["commands"]["disable"]["studio_toggle"]
    assert "--confirm-action" in card["commands"]["disable"]["studio_toggle"]


def test_runtime_startup_controls_model_exposes_approval_idempotency_readiness(monkeypatch):
    monkeypatch.setattr(
        controls,
        "build_startup_surface_settings_report",
        lambda runtime_id, **kwargs: _fake_settings_report(),
    )

    def fake_contract(runtime_id, surface_id, intent):
        return {
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "current_state": "registered",
            "target_state": "off" if intent == "disable" else "registered",
            "required_gate_operation": f"lifecycle.startup_surface.{surface_id}.{intent}",
            "required_write_target_categories": ["runtime_lifecycle_state"],
            "external_api": "host.startup_folder",
            "execution_steps": [],
            "verification_commands": ["chaseos runtime startup-surfaces --runtime hermes --json"],
            "rollback_plan": {"inverse_intent": "enable" if intent == "disable" else "disable"},
            "source_plan": {"runtime_id": runtime_id, "surface_id": surface_id, "intent": intent},
        }

    monkeypatch.setattr(controls, "build_startup_surface_mutation_contract", fake_contract)
    monkeypatch.setattr(controls, "_json_digest", lambda payload: "a" * 64)
    controls._approval_readiness_material.cache_clear()

    model = controls.build_runtime_startup_controls_model(_test_vault("approval-readiness"), "hermes")

    assert model["approval_boundary"]["approval_artifact_consumption_built"] is False
    assert model["approval_boundary"]["idempotency_marker_write_built"] is False
    card = model["surface_cards"][0]
    disable = card["approval_readiness"]["disable"]
    assert disable["approval_required"] is True
    assert disable["approval_artifact"]["status"] == "missing"
    assert disable["approval_artifact"]["consumption_enabled"] is False
    assert disable["idempotency"]["marker_written"] is False
    assert disable["idempotency"]["marker_write_enabled"] is False
    assert disable["live_toggle_blocked_until_approval_consumption"] is True
    assert disable["preflight_command"].startswith("chaseos runtime startup-surface-executor-preflight")
    assert disable["executor_readiness"]["read_only"] is True
    assert disable["executor_readiness"]["executor_enabled_now"] is False
    assert disable["executor_readiness"]["startup_folder_mutation_enabled"] is False
    assert disable["executor_readiness"]["task_scheduler_mutation_enabled"] is False
    assert "startup-surface-executor-readiness" in disable["executor_readiness"]["readiness_command"]
    assert disable["host_boundary_policy"]["read_only"] is True
    assert disable["host_boundary_policy"]["policy_status"] == "blocked"
    assert "startup-surface-host-boundary-policy" in disable["host_boundary_policy"]["policy_command"]
    assert "wsl-windows-host-boundary-policy-not-approved" in disable["host_boundary_policy"]["blocked_reasons"]
    assert disable["host_mutation_audit_template"]["read_only"] is True
    assert disable["host_mutation_audit_template"]["audit_template_status"] == "blocked"
    assert "startup-surface-host-mutation-audit-template" in disable["host_mutation_audit_template"]["audit_template_command"]
    assert "audit-template-not-approved" in disable["host_mutation_audit_template"]["blocked_reasons"]
    assert disable["success_marker_evidence_verifier"]["read_only"] is True
    assert disable["success_marker_evidence_verifier"]["verifier_status"] == "blocked"
    assert "startup-surface-success-marker-evidence-verifier" in disable["success_marker_evidence_verifier"]["verifier_command"]
    assert disable["success_marker_evidence_verifier"]["success_marker_allowed_now"] is False
    assert "success-marker-acceptance-policy-not-approved" in disable["success_marker_evidence_verifier"]["blocked_reasons"]
    assert disable["success_marker_acceptance_policy"]["read_only"] is True
    assert disable["success_marker_acceptance_policy"]["acceptance_policy_status"] == "blocked"
    assert disable["success_marker_acceptance_policy"]["success_marker_allowed_now"] is False
    assert disable["success_marker_acceptance_policy"]["success_marker_write_allowed"] is False
    assert "startup-surface-success-marker-acceptance-policy" in disable["success_marker_acceptance_policy"]["policy_command"]
    assert "success-marker-write-gate-not-approved" in disable["success_marker_acceptance_policy"]["blocked_reasons"]


def test_runtime_startup_controls_dry_run_routes_to_lifecycle_executor(monkeypatch):
    captured: dict[str, object] = {}

    def fake_execute(runtime_id, surface_id, intent, *, confirm, dry_run, requested_by):
        captured.update(
            {
                "runtime_id": runtime_id,
                "surface_id": surface_id,
                "intent": intent,
                "confirm": confirm,
                "dry_run": dry_run,
                "requested_by": requested_by,
            }
        )
        return {
            "action": "startup-surface-toggle",
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "dry_run": dry_run,
            "before_state": "registered",
            "after_state": "registered",
        }

    monkeypatch.setattr(controls, "execute_startup_surface_toggle", fake_execute)

    result = controls.run_runtime_startup_control_action(
        _test_vault("dry-run"),
        runtime_id="hermes",
        surface_id="gateway",
        intent="disable",
        action="dry-run",
        requested_by="operator",
    )

    assert result["ok"] is True
    assert result["action"]["status"] == "dry_run_complete"
    assert result["action"]["writes_host_startup"] is False
    assert captured == {
        "runtime_id": "hermes",
        "surface_id": "gateway",
        "intent": "disable",
        "confirm": False,
        "dry_run": True,
        "requested_by": "operator",
    }


def test_runtime_startup_controls_toggle_requires_confirm_action():
    with pytest.raises(controls.RuntimeStartupControlError, match="confirm-action"):
        controls.run_runtime_startup_control_action(
            _test_vault("requires-confirm"),
            runtime_id="hermes",
            surface_id="gateway",
            intent="disable",
            action="toggle",
        )


def test_runtime_startup_controls_confirmed_toggle_requires_approval_gate_material():
    with pytest.raises(controls.RuntimeStartupControlError, match="gate approval"):
        controls.run_runtime_startup_control_action(
            _test_vault("confirmed-missing-gate"),
            runtime_id="hermes",
            surface_id="gateway",
            intent="disable",
            action="toggle",
            confirm_action=True,
        )


def test_runtime_startup_controls_confirmed_toggle_checks_gate_and_keeps_host_mutation_blocked(monkeypatch):
    captured: dict[str, object] = {}

    def fake_execute(*args, **kwargs):
        raise AssertionError("confirmed Studio gate check must not call host startup toggle executor")

    def fake_consumption(runtime_id, surface_id, intent, *, gate_approval_id, plan_digest, consumed_by, write):
        captured.update(
            {
                "runtime_id": runtime_id,
                "surface_id": surface_id,
                "intent": intent,
                "gate_approval_id": gate_approval_id,
                "plan_digest": plan_digest,
                "consumed_by": consumed_by,
                "write": write,
            }
        )
        return {
            "action": "startup-surface-approval-consumption",
            "ready": True,
            "write_enabled": False,
            "approval_consumed": False,
            "idempotency_marker_written": False,
            "host_mutation_attempted": False,
            "startup_surface_mutation_executed": False,
            "approval_consumption_path": "approval-consumption.json",
            "idempotency_marker_path": "marker.json",
            "blocked_reasons": [],
        }

    monkeypatch.setattr(controls, "execute_startup_surface_toggle", fake_execute)
    monkeypatch.setattr(controls, "build_startup_surface_approval_consumption", fake_consumption)
    monkeypatch.setattr(controls, "_approval_readiness", lambda runtime_id, surface_id, intent: {"approval_required": True})

    result = controls.run_runtime_startup_control_action(
        _test_vault("confirmed-gated"),
        runtime_id="hermes",
        surface_id="gateway",
        intent="disable",
        action="toggle",
        confirm_action=True,
        gate_approval_id="approval-123",
        plan_digest="a" * 64,
        requested_by="operator",
    )

    assert result["ok"] is True
    assert result["action"]["status"] == "approval_gate_ready_host_mutation_blocked"
    assert result["action"]["writes_host_startup"] is False
    assert result["action"]["host_mutation_attempted"] is False
    assert result["action"]["lifecycle_toggle_invoked"] is False
    assert result["action"]["approval_gate"]["ready"] is True
    assert captured == {
        "runtime_id": "hermes",
        "surface_id": "gateway",
        "intent": "disable",
        "gate_approval_id": "approval-123",
        "plan_digest": "a" * 64,
        "consumed_by": "operator",
        "write": False,
    }


def test_runtime_startup_controls_studio_action_has_no_approval_consumption_parameter():
    signature = inspect.signature(controls.run_runtime_startup_control_action)

    assert "consume_approval" not in signature.parameters


def test_runtime_startup_controls_confirmed_toggle_never_consumes_gate_from_studio(monkeypatch):
    captured: dict[str, object] = {}

    def fake_consumption(runtime_id, surface_id, intent, *, gate_approval_id, plan_digest, consumed_by, write):
        captured["write"] = write
        return {
            "action": "startup-surface-approval-consumption",
            "ready": True,
            "write_enabled": write,
            "approval_consumed": write,
            "idempotency_marker_written": write,
            "host_mutation_attempted": False,
            "startup_surface_mutation_executed": False,
            "blocked_reasons": [],
        }

    monkeypatch.setattr(controls, "build_startup_surface_approval_consumption", fake_consumption)
    monkeypatch.setattr(controls, "_approval_readiness", lambda runtime_id, surface_id, intent: {"approval_required": True})

    result = controls.run_runtime_startup_control_action(
        _test_vault("confirmed-no-consume-gate"),
        runtime_id="hermes",
        surface_id="gateway",
        intent="disable",
        action="toggle",
        confirm_action=True,
        gate_approval_id="approval-123",
        plan_digest="a" * 64,
        requested_by="operator",
    )

    assert captured["write"] is False
    assert result["action"]["status"] == "approval_gate_ready_host_mutation_blocked"
    assert result["action"]["writes_host_startup"] is False
    assert result["action"]["approval_gate"]["approval_consumed"] is False
    assert result["action"]["approval_gate"]["idempotency_marker_written"] is False
    assert result["action"]["host_mutation_attempted"] is False
