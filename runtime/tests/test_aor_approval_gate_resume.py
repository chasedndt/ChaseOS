from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from runtime.aor import engine
from runtime.osril.approvals import (
    find_pending_approvals,
    read_approval_response,
    record_approval_response,
)


def _ok(data=None):
    return engine._StageResult(ok=True, data=data)


def _boot() -> SimpleNamespace:
    return SimpleNamespace(
        boot_status="ok",
        runtime_id="hermes",
        current_phase="phase-9",
        sprint_focus="approval-gate",
        trust_ceiling="tier-2",
        sources_read=["Now.md"],
        boot_warnings=[],
    )


def _manifest() -> dict:
    return {
        "id": "approval_demo",
        "status": "active",
        "permission_ceiling": "tier-2",
        "task_type": "demo",
        "role_card": "demo-card",
        "approval_rule": "operator-explicit",
    }


def _patch_engine(monkeypatch, manifest: dict, run_calls: dict[str, int]) -> None:
    monkeypatch.setattr(engine, "_SCORECARDS_AVAILABLE", False)
    monkeypatch.setattr(engine, "load_boot_context", lambda **_: _boot())
    monkeypatch.setattr(engine, "_stage_workflow_lookup", lambda workflow_id, vault_root: _ok(manifest))
    monkeypatch.setattr(
        engine,
        "_stage_task_classification",
        lambda manifest, vault_root: _ok({"id": "demo", "permission_ceiling": "tier-2"}),
    )
    monkeypatch.setattr(
        engine,
        "_stage_role_card_resolution",
        lambda manifest, vault_root: _ok({"id": "demo-card"}),
    )
    monkeypatch.setattr(
        engine,
        "_stage_permission_ceiling",
        lambda manifest, task_type, role_card, inputs: _ok({}),
    )
    monkeypatch.setattr(
        engine,
        "_stage_required_reads",
        lambda manifest, task_type, role_card, vault_root: _ok({}),
    )

    def _run_stage(manifest, inputs, vault_root):
        run_calls["run"] += 1
        return _ok({"handler_status": "executed"})

    monkeypatch.setattr(engine, "_stage_run", _run_stage)
    monkeypatch.setattr(
        engine,
        "_stage_writeback",
        lambda manifest, role_card, run_data, vault_root, dry_run=False: _ok(
            {"files_written": ["07_LOGS/Agent-Activity/demo.md"]}
        ),
    )


def _event_lines(vault_root: Path) -> list[str]:
    event_dir = vault_root / "runtime" / "osril" / "run"
    lines: list[str] = []
    for path in sorted(event_dir.glob("*.events.jsonl")):
        lines.extend(line for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return lines


def test_operator_explicit_workflow_waits_before_run(monkeypatch, tmp_path: Path) -> None:
    run_calls = {"run": 0}
    _patch_engine(monkeypatch, _manifest(), run_calls)

    result = engine.run_workflow("approval_demo", vault_root=tmp_path, runtime_id="hermes")

    assert result.status == "waiting_approval"
    assert result.stage_reached == "approval_gate"
    assert run_calls["run"] == 0
    approval_id = result.outputs["approval_gate"]["approval_id"]
    assert approval_id.startswith("aor-approval_demo-")
    assert find_pending_approvals(tmp_path)[0]["approval_id"] == approval_id
    assert any('"event_type": "approval_required"' in line for line in _event_lines(tmp_path))

    audit_files = list((tmp_path / "07_LOGS" / "Agent-Activity").glob("*.json"))
    assert len(audit_files) == 1
    assert '"status": "waiting_approval"' in audit_files[0].read_text(encoding="utf-8")


def test_approved_response_resumes_once_and_marks_resume(monkeypatch, tmp_path: Path) -> None:
    run_calls = {"run": 0}
    _patch_engine(monkeypatch, _manifest(), run_calls)

    waiting = engine.run_workflow("approval_demo", vault_root=tmp_path, runtime_id="hermes")
    approval_id = waiting.outputs["approval_gate"]["approval_id"]
    response = record_approval_response(
        tmp_path,
        approval_id=approval_id,
        decision="approve",
        operator_id="chase",
    )

    assert response["applied_to_execution"] is True
    assert response["resume_executed"] is False

    resumed = engine.run_workflow(
        "approval_demo",
        inputs={"operator_approval_ref": approval_id},
        vault_root=tmp_path,
        runtime_id="hermes",
    )

    assert resumed.status == "success"
    assert run_calls["run"] == 1
    assert resumed.outputs["approval_gate"]["approval_id"] == approval_id
    assert resumed.outputs["approval_gate"]["resume_executed"] is True
    stored_response = read_approval_response(tmp_path, approval_id)
    assert stored_response is not None
    assert stored_response["resume_executed"] is True
    assert stored_response["resumed_run_id"] == resumed.audit_id

    replay = engine.run_workflow(
        "approval_demo",
        inputs={"operator_approval_ref": approval_id},
        vault_root=tmp_path,
        runtime_id="hermes",
    )

    assert replay.status == "escalated"
    assert replay.stage_reached == "approval_gate"
    assert "already been consumed" in (replay.escalation_reason or "")
    assert run_calls["run"] == 1


def test_denied_response_halts_resume(monkeypatch, tmp_path: Path) -> None:
    run_calls = {"run": 0}
    _patch_engine(monkeypatch, _manifest(), run_calls)

    waiting = engine.run_workflow("approval_demo", vault_root=tmp_path, runtime_id="hermes")
    approval_id = waiting.outputs["approval_gate"]["approval_id"]
    record_approval_response(
        tmp_path,
        approval_id=approval_id,
        decision="deny",
        operator_id="chase",
    )

    denied = engine.run_workflow(
        "approval_demo",
        inputs={"operator_approval_ref": approval_id},
        vault_root=tmp_path,
        runtime_id="hermes",
    )

    assert denied.status == "escalated"
    assert denied.stage_reached == "approval_gate"
    assert "operator denied approval" in (denied.escalation_reason or "")
    assert run_calls["run"] == 0
