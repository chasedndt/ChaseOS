from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from runtime.aor import engine
from runtime.osril.approvals import record_approval_response


def _ok(data=None):
    return engine._StageResult(ok=True, data=data)


def _boot() -> SimpleNamespace:
    return SimpleNamespace(
        boot_status="ok",
        runtime_id="hermes",
        current_phase="phase-9",
        sprint_focus="osril",
        trust_ceiling="tier-2",
        sources_read=["Now.md"],
        boot_warnings=[],
    )


def _read_events(vault: Path):
    event_dir = vault / "runtime" / "osril" / "run"
    files = sorted(event_dir.glob("*.events.jsonl"))
    assert files, "expected OSRIL event log file"
    return [line for line in files[0].read_text(encoding="utf-8").splitlines() if line.strip()]


def test_run_workflow_emits_osril_events_on_success(monkeypatch, tmp_path: Path) -> None:
    manifest = {"id": "demo", "status": "active", "permission_ceiling": "tier-2", "task_type": "demo", "role_card": "demo-card"}

    monkeypatch.setattr(engine, "load_boot_context", lambda **_: _boot())
    monkeypatch.setattr(engine, "_write_audit_record", lambda **_: None)
    monkeypatch.setattr(engine, "_stage_workflow_lookup", lambda workflow_id, vault_root: _ok(manifest))
    monkeypatch.setattr(engine, "_stage_task_classification", lambda manifest, vault_root: _ok({"id": "demo", "permission_ceiling": "tier-2"}))
    monkeypatch.setattr(engine, "_stage_role_card_resolution", lambda manifest, vault_root: _ok({"id": "demo-card"}))
    monkeypatch.setattr(engine, "_stage_permission_ceiling", lambda manifest, task_type, role_card, inputs: _ok({}))
    monkeypatch.setattr(engine, "_stage_required_reads", lambda manifest, task_type, role_card, vault_root: _ok({}))
    monkeypatch.setattr(engine, "_stage_run", lambda manifest, inputs, vault_root: _ok({"result": "ok"}))
    monkeypatch.setattr(engine, "_stage_writeback", lambda manifest, role_card, run_data, vault_root, dry_run=False: _ok({"artifact": "07_LOGS/Agent-Activity/demo.md"}))

    result = engine.run_workflow("demo", inputs={"x": 1}, vault_root=tmp_path, runtime_id="hermes")

    assert result.status == "success"
    events = _read_events(tmp_path)
    assert '"event_type": "status"' in events[0]
    assert any('"event_type": "task_started"' in line for line in events)
    assert any('"event_type": "task_complete"' in line for line in events)
    assert any('"terminal_status": "success"' in line for line in events)


def test_run_workflow_emits_osril_events_on_escalation(monkeypatch, tmp_path: Path) -> None:
    manifest = {"id": "demo", "status": "active", "permission_ceiling": "tier-2", "task_type": "demo", "role_card": "demo-card"}

    monkeypatch.setattr(engine, "load_boot_context", lambda **_: _boot())
    monkeypatch.setattr(engine, "_write_audit_record", lambda **_: None)
    monkeypatch.setattr(engine, "_stage_workflow_lookup", lambda workflow_id, vault_root: _ok(manifest))
    monkeypatch.setattr(engine, "_stage_task_classification", lambda manifest, vault_root: _ok({"id": "demo", "permission_ceiling": "tier-2"}))
    monkeypatch.setattr(engine, "_stage_role_card_resolution", lambda manifest, vault_root: _ok({"id": "demo-card"}))
    monkeypatch.setattr(
        engine,
        "_stage_permission_ceiling",
        lambda manifest, task_type, role_card, inputs: engine._StageResult(ok=False, reason="approval missing or invalid"),
    )

    result = engine.run_workflow("demo", inputs={}, vault_root=tmp_path, runtime_id="hermes")

    assert result.status == "escalated"
    events = _read_events(tmp_path)
    assert any('"event_type": "task_failed"' in line for line in events)
    assert any('"terminal_status": "escalated"' in line for line in events)
    assert any('"stage_reached": "permission_ceiling"' in line for line in events)


def test_run_workflow_emits_osril_events_on_failure(monkeypatch, tmp_path: Path) -> None:
    manifest = {"id": "demo", "status": "active", "permission_ceiling": "tier-2", "task_type": "demo", "role_card": "demo-card"}

    monkeypatch.setattr(engine, "load_boot_context", lambda **_: _boot())
    monkeypatch.setattr(engine, "_write_audit_record", lambda **_: None)
    monkeypatch.setattr(engine, "_stage_workflow_lookup", lambda workflow_id, vault_root: _ok(manifest))
    monkeypatch.setattr(engine, "_stage_task_classification", lambda manifest, vault_root: _ok({"id": "demo", "permission_ceiling": "tier-2"}))
    monkeypatch.setattr(engine, "_stage_role_card_resolution", lambda manifest, vault_root: _ok({"id": "demo-card"}))
    monkeypatch.setattr(engine, "_stage_permission_ceiling", lambda manifest, task_type, role_card, inputs: _ok({}))
    monkeypatch.setattr(engine, "_stage_required_reads", lambda manifest, task_type, role_card, vault_root: _ok({}))
    monkeypatch.setattr(
        engine,
        "_stage_run",
        lambda manifest, inputs, vault_root: engine._StageResult(ok=False, reason="boom", terminal_status="failed"),
    )

    result = engine.run_workflow("demo", inputs={}, vault_root=tmp_path, runtime_id="hermes")

    assert result.status == "failed"
    events = _read_events(tmp_path)
    assert any('"event_type": "task_failed"' in line for line in events)
    assert any('"terminal_status": "failed"' in line for line in events)
    assert any('"stage_reached": "run"' in line for line in events)


def test_run_workflow_waits_then_resumes_from_osril_approval(monkeypatch, tmp_path: Path) -> None:
    manifest = {
        "id": "demo",
        "status": "active",
        "permission_ceiling": "tier-2",
        "task_type": "demo",
        "role_card": "demo-card",
        "approval_rule": "operator-explicit",
    }
    run_calls = {"count": 0}

    def _run_stage(manifest, inputs, vault_root):
        run_calls["count"] += 1
        return _ok({"result": "ok"})

    monkeypatch.setattr(engine, "load_boot_context", lambda **_: _boot())
    monkeypatch.setattr(engine, "_write_audit_record", lambda **_: None)
    monkeypatch.setattr(engine, "_stage_workflow_lookup", lambda workflow_id, vault_root: _ok(manifest))
    monkeypatch.setattr(engine, "_stage_task_classification", lambda manifest, vault_root: _ok({"id": "demo", "permission_ceiling": "tier-2"}))
    monkeypatch.setattr(engine, "_stage_role_card_resolution", lambda manifest, vault_root: _ok({"id": "demo-card"}))
    monkeypatch.setattr(engine, "_stage_permission_ceiling", lambda manifest, task_type, role_card, inputs: _ok({}))
    monkeypatch.setattr(engine, "_stage_required_reads", lambda manifest, task_type, role_card, vault_root: _ok({}))
    monkeypatch.setattr(engine, "_stage_run", _run_stage)
    monkeypatch.setattr(engine, "_stage_writeback", lambda manifest, role_card, run_data, vault_root, dry_run=False: _ok({"artifact": "demo"}))

    first = engine.run_workflow("demo", inputs={}, vault_root=tmp_path, runtime_id="hermes")
    assert first.status == "waiting_approval"
    assert run_calls["count"] == 0

    approval_id = first.outputs["approval_gate"]["approval_id"]
    response = record_approval_response(
        tmp_path,
        approval_id=approval_id,
        decision="approve",
        operator_id="chase",
    )
    assert response["applied_to_execution"] is True

    second = engine.run_workflow(
        "demo",
        inputs={"operator_approval_ref": approval_id},
        vault_root=tmp_path,
        runtime_id="hermes",
    )
    assert second.status == "success"
    assert second.outputs["approval_gate"]["resume_executed"] is True
    assert run_calls["count"] == 1

    replay = engine.run_workflow(
        "demo",
        inputs={"operator_approval_ref": approval_id},
        vault_root=tmp_path,
        runtime_id="hermes",
    )
    assert replay.status == "escalated"
    assert "already been consumed" in str(replay.escalation_reason)
    assert run_calls["count"] == 1


def test_run_workflow_denied_osril_approval_does_not_execute(monkeypatch, tmp_path: Path) -> None:
    manifest = {
        "id": "demo",
        "status": "active",
        "permission_ceiling": "tier-2",
        "task_type": "demo",
        "role_card": "demo-card",
        "approval_rule": "operator-explicit",
    }
    run_calls = {"count": 0}

    monkeypatch.setattr(engine, "load_boot_context", lambda **_: _boot())
    monkeypatch.setattr(engine, "_write_audit_record", lambda **_: None)
    monkeypatch.setattr(engine, "_stage_workflow_lookup", lambda workflow_id, vault_root: _ok(manifest))
    monkeypatch.setattr(engine, "_stage_task_classification", lambda manifest, vault_root: _ok({"id": "demo", "permission_ceiling": "tier-2"}))
    monkeypatch.setattr(engine, "_stage_role_card_resolution", lambda manifest, vault_root: _ok({"id": "demo-card"}))
    monkeypatch.setattr(engine, "_stage_permission_ceiling", lambda manifest, task_type, role_card, inputs: _ok({}))
    monkeypatch.setattr(engine, "_stage_required_reads", lambda manifest, task_type, role_card, vault_root: _ok({}))
    monkeypatch.setattr(engine, "_stage_run", lambda manifest, inputs, vault_root: run_calls.update({"count": run_calls["count"] + 1}) or _ok({}))

    first = engine.run_workflow("demo", inputs={}, vault_root=tmp_path, runtime_id="hermes")
    approval_id = first.outputs["approval_gate"]["approval_id"]
    record_approval_response(
        tmp_path,
        approval_id=approval_id,
        decision="deny",
        operator_id="chase",
    )

    denied = engine.run_workflow(
        "demo",
        inputs={"operator_approval_ref": approval_id},
        vault_root=tmp_path,
        runtime_id="hermes",
    )
    assert denied.status == "escalated"
    assert "operator denied" in str(denied.escalation_reason)
    assert run_calls["count"] == 0
