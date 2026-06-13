"""coordination-watch bootstrap registration tests for ChaseOS.

Verifies:
- lifecycle records expose coordination_watch bootstrap registration defaults
- plan generation resolves host-level registration artifacts and commands
- install/status/remove use bounded artifact files rather than claiming ambient host registration

Run when pytest is available:
    .venv/Scripts/python.exe -m pytest runtime/lifecycle/test_coordination_watch_bootstrap.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.lifecycle.coordination_watch_bootstrap import (  # type: ignore
    build_coordination_watch_activation_checklist,
    apply_coordination_watch_bootstrap,
    build_coordination_watch_activation_report,
    build_coordination_watch_bootstrap_plan,
    capture_coordination_watch_bootstrap_success_state,
    get_coordination_watch_bootstrap_status,
    install_coordination_watch_bootstrap,
    load_coordination_watch_bootstrap_config,
    reconcile_coordination_watch_bootstrap_reboot_result,
    remove_coordination_watch_bootstrap,
    unregister_coordination_watch_bootstrap,
    verify_coordination_watch_bootstrap,
    write_coordination_watch_bootstrap_handoff_bundle,
    write_coordination_watch_bootstrap_reboot_verification_bundle,
)


def test_hermes_lifecycle_record_declares_coordination_watch_bootstrap_defaults():
    config = load_coordination_watch_bootstrap_config("hermes")

    assert config["bootstrap_enabled"] is True
    assert config["registration_kind"] == "windows-task-scheduler"
    assert config["task_name"] == "ChaseOS-Hermes-Coordination-Watch"
    assert config["launcher_path"].endswith("hermes-coordination-watch-start.cmd")


def test_build_coordination_watch_bootstrap_plan_for_hermes_uses_windows_supervisor_launcher():
    plan = build_coordination_watch_bootstrap_plan("hermes")

    assert plan["runtime_id"] == "hermes"
    assert plan["registration_kind"] == "windows-task-scheduler"
    assert plan["wsl_distro"] == "Ubuntu"
    assert plan["supervisor_host"] == "windows"
    assert "wsl.exe" not in plan["launcher_contents"]
    assert "%VAULT%\\.venv\\Scripts\\python.exe" in plan["launcher_contents"]
    assert ".venv/Scripts/python.exe" not in plan["launcher_contents"]
    assert "coordination-watch-supervisor --runtime hermes --action start" in plan["launcher_contents"]
    assert "set \"BOOTSTRAP_DIR=%~dp0\"" in plan["launcher_contents"]
    assert "C:\\Users\\chaseos\\Documents\\chaseos_obsidian" not in plan["launcher_contents"]
    assert plan["register_command"][0].lower().endswith("schtasks")


def test_install_coordination_watch_bootstrap_writes_artifacts(monkeypatch, tmp_path):
    launcher_path = tmp_path / "openclaw-start.cmd"
    artifact_path = tmp_path / "openclaw-registration.json"

    plan = {
        "runtime_id": "openclaw",
        "runtime_name": "OpenClaw",
        "bootstrap_enabled": True,
        "registration_kind": "windows-task-scheduler",
        "trigger": "on-logon",
        "task_name": "ChaseOS-OpenClaw-Coordination-Watch",
        "launcher_path": str(launcher_path),
        "registration_artifact": str(artifact_path),
        "launcher_contents": "@echo off\r\nREM start openclaw\r\n",
        "register_command": ["schtasks", "/Create"],
        "unregister_command": ["schtasks", "/Delete"],
        "event_log_path": str(tmp_path / "openclaw-events.jsonl"),
        "notes": "test-plan",
    }

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: dict(plan),
    )

    result = install_coordination_watch_bootstrap("openclaw")

    assert result["installed"] is True
    assert launcher_path.exists()
    assert artifact_path.exists()
    assert "@echo off" in launcher_path.read_text(encoding="utf-8")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["task_name"] == "ChaseOS-OpenClaw-Coordination-Watch"
    assert artifact["register_command"] == ["schtasks", "/Create"]

    event_log = tmp_path / "openclaw-events.jsonl"
    assert event_log.exists()
    lines = [line for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["action"] == "install"
    assert event["runtime_id"] == "openclaw"


def test_coordination_watch_bootstrap_status_reports_installed(monkeypatch, tmp_path):
    launcher_path = tmp_path / "hermes-start.cmd"
    artifact_path = tmp_path / "hermes-registration.json"
    event_log_path = tmp_path / "hermes-events.jsonl"
    launcher_path.write_text("@echo off\r\n", encoding="utf-8")
    artifact_path.write_text(json.dumps({"task_name": "ChaseOS-Hermes-Coordination-Watch"}), encoding="utf-8")
    event_log_path.write_text(json.dumps({"action": "handoff", "runtime_id": "hermes"}) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "registration_kind": "windows-task-scheduler",
            "trigger": "on-logon",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "launcher_path": str(launcher_path),
            "registration_artifact": str(artifact_path),
            "event_log_path": str(event_log_path),
            "launcher_contents": "@echo off\r\n",
            "register_command": ["schtasks", "/Create"],
            "unregister_command": ["schtasks", "/Delete"],
            "notes": "test",
        },
    )

    result = get_coordination_watch_bootstrap_status("hermes")

    assert result["installed"] is True
    assert result["artifact_present"] is True
    assert result["launcher_present"] is True
    assert result["event_log_present"] is True
    assert result["latest_event"]["action"] == "handoff"


def test_remove_coordination_watch_bootstrap_deletes_artifacts(monkeypatch, tmp_path):
    launcher_path = tmp_path / "hermes-start.cmd"
    artifact_path = tmp_path / "hermes-registration.json"
    launcher_path.write_text("@echo off\r\n", encoding="utf-8")
    artifact_path.write_text(json.dumps({"task_name": "ChaseOS-Hermes-Coordination-Watch"}), encoding="utf-8")

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "registration_kind": "windows-task-scheduler",
            "trigger": "on-logon",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "launcher_path": str(launcher_path),
            "registration_artifact": str(artifact_path),
            "launcher_contents": "@echo off\r\n",
            "register_command": ["schtasks", "/Create"],
            "unregister_command": ["schtasks", "/Delete"],
            "event_log_path": str(tmp_path / "hermes-events.jsonl"),
            "notes": "test",
        },
    )

    result = remove_coordination_watch_bootstrap("hermes")

    assert result["removed"] is True
    assert not launcher_path.exists()
    assert not artifact_path.exists()


def test_apply_coordination_watch_bootstrap_runs_register_command(monkeypatch, tmp_path):
    launcher_path = tmp_path / "openclaw-start.cmd"
    artifact_path = tmp_path / "openclaw-registration.json"

    plan = {
        "runtime_id": "openclaw",
        "runtime_name": "OpenClaw",
        "bootstrap_enabled": True,
        "registration_kind": "windows-task-scheduler",
        "trigger": "on-logon",
        "task_name": "ChaseOS-OpenClaw-Coordination-Watch",
        "launcher_path": str(launcher_path),
        "registration_artifact": str(artifact_path),
        "launcher_contents": "@echo off\r\nREM start openclaw\r\n",
        "register_command": ["schtasks", "/Create", "/TN", "ChaseOS-OpenClaw-Coordination-Watch"],
        "unregister_command": ["schtasks", "/Delete"],
        "event_log_path": str(tmp_path / "openclaw-events.jsonl"),
        "notes": "test-plan",
    }
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: dict(plan),
    )

    def fake_run(command, capture_output=True, text=True, check=False):
        calls["command"] = command
        class Result:
            returncode = 0
            stdout = "SUCCESS"
            stderr = ""
        return Result()

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.subprocess.run", fake_run)

    result = apply_coordination_watch_bootstrap("openclaw")

    assert result["applied"] is True
    assert calls["command"] == ["schtasks", "/Create", "/TN", "ChaseOS-OpenClaw-Coordination-Watch"]
    assert launcher_path.exists()
    assert artifact_path.exists()


def test_verify_coordination_watch_bootstrap_reports_registered(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "registration_kind": "windows-task-scheduler",
            "trigger": "on-logon",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "launcher_path": "launcher.cmd",
            "registration_artifact": "artifact.json",
            "register_command": ["schtasks", "/Create"],
            "unregister_command": ["schtasks", "/Delete"],
            "event_log_path": str(tmp_path / "hermes-events.jsonl"),
            "wsl_distro": "Ubuntu",
        },
    )

    def fake_run(command, capture_output=True, text=True, check=False):
        class Result:
            returncode = 0
            stdout = "TaskName: ChaseOS-Hermes-Coordination-Watch"
            stderr = ""
        return Result()

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.subprocess.run", fake_run)

    result = verify_coordination_watch_bootstrap("hermes")

    assert result["registered"] is True
    assert result["task_name"] == "ChaseOS-Hermes-Coordination-Watch"


def test_unregister_coordination_watch_bootstrap_runs_unregister_command(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "registration_kind": "windows-task-scheduler",
            "trigger": "on-logon",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "launcher_path": "launcher.cmd",
            "registration_artifact": "artifact.json",
            "register_command": ["schtasks", "/Create"],
            "unregister_command": ["schtasks", "/Delete", "/TN", "ChaseOS-Hermes-Coordination-Watch", "/F"],
            "event_log_path": str(tmp_path / "hermes-events.jsonl"),
        },
    )
    calls: dict[str, object] = {}

    def fake_run(command, capture_output=True, text=True, check=False):
        calls["command"] = command
        class Result:
            returncode = 0
            stdout = "SUCCESS"
            stderr = ""
        return Result()

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.subprocess.run", fake_run)

    result = unregister_coordination_watch_bootstrap("hermes")

    assert result["unregistered"] is True
    assert calls["command"] == ["schtasks", "/Delete", "/TN", "ChaseOS-Hermes-Coordination-Watch", "/F"]


def test_write_coordination_watch_bootstrap_handoff_bundle_writes_elevated_artifacts(monkeypatch, tmp_path):
    launcher_path = tmp_path / "hermes-start.cmd"
    artifact_path = tmp_path / "hermes-registration.json"
    handoff_script_path = tmp_path / "hermes-handoff.ps1"
    handoff_artifact_path = tmp_path / "hermes-handoff.json"

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "registration_kind": "windows-task-scheduler",
            "trigger": "on-logon",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "launcher_path": str(launcher_path),
            "registration_artifact": str(artifact_path),
            "register_command": ["schtasks", "/Create", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
            "unregister_command": ["schtasks", "/Delete", "/TN", "ChaseOS-Hermes-Coordination-Watch", "/F"],
            "handoff_script_path": str(handoff_script_path),
            "handoff_artifact_path": str(handoff_artifact_path),
            "event_log_path": str(tmp_path / "hermes-events.jsonl"),
            "wsl_distro": "Ubuntu",
            "notes": "test-handoff",
        },
    )

    result = write_coordination_watch_bootstrap_handoff_bundle("hermes")

    assert result["handoff_ready"] is True
    assert handoff_script_path.exists()
    assert handoff_artifact_path.exists()
    script = handoff_script_path.read_text(encoding="utf-8")
    assert "Start-Process" in script
    assert "-Verb RunAs" in script
    assert "ChaseOS-Hermes-Coordination-Watch" in script
    artifact = json.loads(handoff_artifact_path.read_text(encoding="utf-8"))
    assert artifact["register_command"] == ["schtasks", "/Create", "/TN", "ChaseOS-Hermes-Coordination-Watch"]
    assert artifact["verify_command"] == ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"]


def test_write_coordination_watch_bootstrap_reboot_verification_bundle_writes_post_boot_artifacts(monkeypatch, tmp_path):
    reboot_verify_script_path = tmp_path / "hermes-reboot-verify.ps1"
    reboot_verify_artifact_path = tmp_path / "hermes-reboot-verify.json"
    reboot_verify_result_path = tmp_path / "hermes-reboot-verify-result.json"

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "registration_kind": "windows-task-scheduler",
            "trigger": "on-logon",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "launcher_path": str(tmp_path / "hermes-start.cmd"),
            "registration_artifact": str(tmp_path / "hermes-registration.json"),
            "register_command": ["schtasks", "/Create", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
            "unregister_command": ["schtasks", "/Delete", "/TN", "ChaseOS-Hermes-Coordination-Watch", "/F"],
            "reboot_verify_script_path": str(reboot_verify_script_path),
            "reboot_verify_artifact_path": str(reboot_verify_artifact_path),
            "reboot_verify_result_path": str(reboot_verify_result_path),
            "state_file": str(tmp_path / "hermes-supervisor-state.json"),
            "log_file": str(tmp_path / "hermes-supervisor.log"),
            "event_log_path": str(tmp_path / "hermes-events.jsonl"),
            "wsl_distro": "Ubuntu",
            "notes": "test-reboot-verify",
        },
    )

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap._utc_now_iso", lambda: "2026-04-26T04:00:00Z")

    result = write_coordination_watch_bootstrap_reboot_verification_bundle("hermes")

    assert result["reboot_verification_ready"] is True
    assert result["prepared_at_utc"] == "2026-04-26T04:00:00Z"
    assert reboot_verify_script_path.exists()
    assert reboot_verify_artifact_path.exists()
    script = reboot_verify_script_path.read_text(encoding="utf-8")
    assert "schtasks.exe" in script
    assert "$preparedAtUtc" in script
    assert "Get-CimInstance Win32_OperatingSystem" in script
    assert "Get-ScheduledTaskInfo" in script
    assert "scheduled_task_ran_after_boot" in script
    assert "reboot_observed" in script
    assert "ChaseOS-Hermes-Coordination-Watch" in script
    assert "supervisor" in script.lower()
    assert "ConvertTo-Json" in script
    assert "$LASTEXITCODE" in script
    assert "returncode-zero-task-name-present" in script
    assert "task-name-missing-from-output" in script
    assert "$schedulerRegistered = ($verificationReturnCode -eq 0" in script
    assert "$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path" in script
    assert "$vaultRoot = Resolve-Path (Join-Path $scriptRoot" in script
    assert "$resultOutputPath = Join-Path $vaultRoot 'runtime/lifecycle/run/hermes-coordination-watch-reboot-verify-result.json'" in script
    assert str(reboot_verify_result_path) not in script
    artifact = json.loads(reboot_verify_artifact_path.read_text(encoding="utf-8"))
    assert artifact["prepared_at_utc"] == "2026-04-26T04:00:00Z"
    assert artifact["verification_command"] == ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"]
    assert artifact["expected_supervisor_state_file"].endswith("hermes-supervisor-state.json")
    assert artifact["result_output_path"] == str(reboot_verify_result_path)
    assert result["reboot_verify_result_path"] == str(reboot_verify_result_path)


def test_capture_coordination_watch_bootstrap_success_state_imports_reboot_verify_result_when_present(monkeypatch, tmp_path):
    success_record_path = tmp_path / "hermes-bootstrap-success.json"
    reboot_verify_result_path = tmp_path / "hermes-reboot-verify-result.json"
    reboot_verify_result_path.write_text(
        json.dumps(
            {
                "timestamp_utc": "2026-04-26T05:00:00Z",
                "runtime_id": "hermes",
                "runtime_name": "Hermes",
                "task_name": "ChaseOS-Hermes-Coordination-Watch",
                "registration_kind": "windows-task-scheduler",
                "scheduler_registered": True,
                "verification_returncode": 0,
                "verification_stdout": "TaskName: ChaseOS-Hermes-Coordination-Watch",
                "verification_stderr": "",
                "verification_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
                "scheduler_registration_evidence": "returncode-zero-task-name-present",
                "prepared_at_utc": "2026-04-26T04:00:00Z",
                "current_boot_time_utc": "2026-04-26T04:55:00Z",
                "reboot_observed": True,
                "task_last_run_time_utc": "2026-04-26T04:56:00Z",
                "task_last_result": 0,
                "scheduled_task_ran_after_boot": True,
                "scheduled_task_last_result_ok": True,
                "supervisor_state_file": str(tmp_path / "postboot-state.json"),
                "supervisor_state_present": True,
                "supervisor_log_file": str(tmp_path / "postboot.log"),
                "supervisor_log_present": True,
                "success_observed": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.ROOT", tmp_path)
    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap._utc_now_iso", lambda: "2026-04-26T05:10:00Z")

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "success_record_path": str(success_record_path),
            "reboot_verify_result_path": str(reboot_verify_result_path),
            "state_file": str(tmp_path / "live-state.json"),
            "log_file": str(tmp_path / "live.log"),
            "event_log_path": str(tmp_path / "events.jsonl"),
            "wsl_distro": "Ubuntu",
        },
    )

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.verify_coordination_watch_bootstrap",
        lambda runtime_id: {
            "action": "verify",
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "registered": False,
            "query_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
            "returncode": 1,
            "stdout": "",
            "stderr": "ERROR: The system cannot find the file specified.",
        },
    )

    result = capture_coordination_watch_bootstrap_success_state("hermes")

    assert result["success_record_written"] is True
    assert result["success_observed"] is True
    assert result["scheduler_registered"] is True
    assert result["supervisor_state_present"] is True
    assert result["supervisor_log_present"] is True
    assert result["evidence_source"] == "reboot_verify_result"
    assert result["reboot_verify_result_imported"] is True
    assert result["reboot_verify_result_rejected_reason"] is None
    assert result["agent_activity_record_written"] is True
    record = json.loads(success_record_path.read_text(encoding="utf-8"))
    assert record["evidence_source"] == "reboot_verify_result"
    assert record["reboot_verify_result_path"] == str(reboot_verify_result_path)
    assert record["verification_returncode"] == 0
    assert record["scheduler_registration_evidence"] == "returncode-zero-task-name-present"
    assert record["reboot_observed"] is True
    assert record["scheduled_task_ran_after_boot"] is True
    assert record["supervisor_state_file"].endswith("postboot-state.json")


def test_capture_coordination_watch_bootstrap_success_state_reads_utf8_bom_reboot_result(monkeypatch, tmp_path):
    success_record_path = tmp_path / "hermes-bootstrap-success.json"
    reboot_verify_result_path = tmp_path / "hermes-reboot-verify-result.json"
    reboot_verify_result_path.write_text(
        json.dumps(
            {
                "timestamp_utc": "2026-04-26T05:00:00Z",
                "runtime_id": "hermes",
                "runtime_name": "Hermes",
                "task_name": "ChaseOS-Hermes-Coordination-Watch",
                "registration_kind": "windows-task-scheduler",
                "scheduler_registered": True,
                "verification_returncode": 0,
                "verification_stdout": "TaskName: ChaseOS-Hermes-Coordination-Watch",
                "verification_stderr": "",
                "verification_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
                "scheduler_registration_evidence": "returncode-zero-task-name-present",
                "prepared_at_utc": "2026-04-26T04:00:00Z",
                "current_boot_time_utc": "2026-04-26T04:55:00Z",
                "reboot_observed": True,
                "task_last_run_time_utc": "2026-04-26T04:56:00Z",
                "task_last_result": 0,
                "scheduled_task_ran_after_boot": True,
                "scheduled_task_last_result_ok": True,
                "supervisor_state_file": str(tmp_path / "postboot-state.json"),
                "supervisor_state_present": True,
                "supervisor_log_file": str(tmp_path / "postboot.log"),
                "supervisor_log_present": True,
                "success_observed": True,
            },
            indent=2,
        ),
        encoding="utf-8-sig",
    )

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.ROOT", tmp_path)
    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap._utc_now_iso", lambda: "2026-04-26T05:10:00Z")
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "success_record_path": str(success_record_path),
            "reboot_verify_result_path": str(reboot_verify_result_path),
            "state_file": str(tmp_path / "live-state.json"),
            "log_file": str(tmp_path / "live.log"),
            "event_log_path": str(tmp_path / "events.jsonl"),
            "wsl_distro": "Ubuntu",
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.verify_coordination_watch_bootstrap",
        lambda runtime_id: {
            "action": "verify",
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "registered": False,
            "query_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
            "returncode": 1,
            "stdout": "",
            "stderr": "ERROR: The system cannot find the file specified.",
        },
    )

    result = capture_coordination_watch_bootstrap_success_state("hermes")

    assert result["reboot_verify_result_imported"] is True
    assert result["reboot_verify_result_rejected_reason"] is None
    assert result["success_observed"] is True


def test_capture_coordination_watch_bootstrap_success_state_rejects_same_boot_reboot_result(monkeypatch, tmp_path):
    success_record_path = tmp_path / "hermes-bootstrap-success.json"
    reboot_verify_result_path = tmp_path / "hermes-reboot-verify-result.json"
    reboot_verify_result_path.write_text(
        json.dumps(
            {
                "timestamp_utc": "2026-04-26T05:00:00Z",
                "runtime_id": "hermes",
                "runtime_name": "Hermes",
                "task_name": "ChaseOS-Hermes-Coordination-Watch",
                "registration_kind": "windows-task-scheduler",
                "scheduler_registered": True,
                "verification_returncode": 0,
                "verification_stdout": "TaskName: ChaseOS-Hermes-Coordination-Watch",
                "verification_stderr": "",
                "verification_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
                "scheduler_registration_evidence": "returncode-zero-task-name-present",
                "prepared_at_utc": "2026-04-26T04:00:00Z",
                "current_boot_time_utc": "2026-04-26T03:50:00Z",
                "reboot_observed": False,
                "task_last_run_time_utc": "2026-04-26T03:55:00Z",
                "task_last_result": 0,
                "scheduled_task_ran_after_boot": True,
                "scheduled_task_last_result_ok": True,
                "supervisor_state_file": str(tmp_path / "postboot-state.json"),
                "supervisor_state_present": True,
                "supervisor_log_file": str(tmp_path / "postboot.log"),
                "supervisor_log_present": True,
                "success_observed": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.ROOT", tmp_path)
    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap._utc_now_iso", lambda: "2026-04-26T05:15:00Z")

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "success_record_path": str(success_record_path),
            "reboot_verify_result_path": str(reboot_verify_result_path),
            "state_file": str(tmp_path / "missing-live-state.json"),
            "log_file": str(tmp_path / "missing-live.log"),
            "event_log_path": str(tmp_path / "events.jsonl"),
            "wsl_distro": "Ubuntu",
        },
    )

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.verify_coordination_watch_bootstrap",
        lambda runtime_id: {
            "action": "verify",
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "registered": False,
            "query_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
            "returncode": 1,
            "stdout": "",
            "stderr": "ERROR: The system cannot find the file specified.",
        },
    )

    result = capture_coordination_watch_bootstrap_success_state("hermes")

    assert result["evidence_source"] == "live_verify"
    assert result["reboot_verify_result_imported"] is False
    assert result["reboot_verify_result_rejected_reason"] == "reboot_not_observed_after_bundle_preparation"
    assert result["success_observed"] is False
    assert result["agent_activity_record_written"] is False


def test_capture_coordination_watch_bootstrap_success_state_rejects_mismatched_reboot_result(monkeypatch, tmp_path):
    success_record_path = tmp_path / "hermes-bootstrap-success.json"
    reboot_verify_result_path = tmp_path / "hermes-reboot-verify-result.json"
    reboot_verify_result_path.write_text(
        json.dumps(
            {
                "timestamp_utc": "2026-04-26T05:00:00Z",
                "runtime_id": "hermes",
                "runtime_name": "Hermes",
                "task_name": "Other-Task",
                "registration_kind": "windows-task-scheduler",
                "scheduler_registered": True,
                "verification_returncode": 0,
                "verification_stdout": "TaskName: Other-Task",
                "verification_stderr": "",
                "verification_command": ["schtasks", "/Query", "/TN", "Other-Task"],
                "supervisor_state_file": str(tmp_path / "postboot-state.json"),
                "supervisor_state_present": True,
                "supervisor_log_file": str(tmp_path / "postboot.log"),
                "supervisor_log_present": True,
                "success_observed": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.ROOT", tmp_path)
    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap._utc_now_iso", lambda: "2026-04-26T05:15:00Z")

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "success_record_path": str(success_record_path),
            "reboot_verify_result_path": str(reboot_verify_result_path),
            "state_file": str(tmp_path / "missing-live-state.json"),
            "log_file": str(tmp_path / "missing-live.log"),
            "event_log_path": str(tmp_path / "events.jsonl"),
            "wsl_distro": "Ubuntu",
        },
    )

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.verify_coordination_watch_bootstrap",
        lambda runtime_id: {
            "action": "verify",
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "registered": False,
            "query_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
            "returncode": 1,
            "stdout": "",
            "stderr": "ERROR: The system cannot find the file specified.",
        },
    )

    result = capture_coordination_watch_bootstrap_success_state("hermes")

    assert result["evidence_source"] == "live_verify"
    assert result["reboot_verify_result_imported"] is False
    assert result["reboot_verify_result_rejected_reason"] == "task_name_mismatch"
    assert result["success_observed"] is False
    assert result["agent_activity_record_written"] is False
    record = json.loads(success_record_path.read_text(encoding="utf-8"))
    assert record["reboot_verify_result_rejected_reason"] == "task_name_mismatch"


def test_reconcile_coordination_watch_bootstrap_reboot_result_reports_explicit_action(monkeypatch):
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.capture_coordination_watch_bootstrap_success_state",
        lambda runtime_id: {
            "action": "capture-success",
            "runtime_id": runtime_id,
            "evidence_source": "reboot_verify_result",
            "success_record_written": True,
            "success_observed": True,
        },
    )

    result = reconcile_coordination_watch_bootstrap_reboot_result("hermes")

    assert result["action"] == "reconcile-reboot-result"
    assert result["runtime_id"] == "hermes"
    assert result["reconciled"] is True
    assert result["evidence_source"] == "reboot_verify_result"
    assert result["success_observed"] is True


def test_build_coordination_watch_activation_report_proves_live_runtime(monkeypatch):
    from runtime.agent_bus import bus

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "interval_seconds": 30,
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_coordination_watch_bootstrap_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "installed": True,
            "handoff_ready": True,
            "reboot_verification_ready": True,
            "latest_success_record": {
                "timestamp_utc": "2026-04-27T10:00:00Z",
                "runtime_id": "hermes",
                "task_name": "ChaseOS-Hermes-Coordination-Watch",
                "registration_kind": "windows-task-scheduler",
                "scheduler_registered": True,
                "verification_returncode": 0,
                "verification_stdout": "TaskName: ChaseOS-Hermes-Coordination-Watch",
                "supervisor_state_present": True,
                "supervisor_log_present": True,
                "success_observed": True,
            },
            "latest_reboot_verify_result": {
                "timestamp_utc": "2026-04-27T10:05:00Z",
                "runtime_id": "hermes",
                "task_name": "ChaseOS-Hermes-Coordination-Watch",
                "registration_kind": "windows-task-scheduler",
                "scheduler_registered": True,
                "verification_returncode": 0,
                "verification_stdout": "TaskName: ChaseOS-Hermes-Coordination-Watch",
                "prepared_at_utc": "2026-04-27T09:50:00Z",
                "current_boot_time_utc": "2026-04-27T09:55:00Z",
                "reboot_observed": True,
                "task_last_run_time_utc": "2026-04-27T09:56:00Z",
                "task_last_result": 0,
                "scheduled_task_ran_after_boot": True,
                "scheduled_task_last_result_ok": True,
                "supervisor_state_present": True,
                "supervisor_log_present": True,
                "success_observed": True,
            },
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "running": True,
            "state_present": True,
            "interval_seconds": 30,
            "stale_after_seconds": 900,
        },
    )

    class Result:
        returncode = 0
        stdout = "TaskName: ChaseOS-Hermes-Coordination-Watch"
        stderr = ""

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.subprocess.run",
        lambda command, capture_output=True, text=True, check=False: Result(),
    )
    monkeypatch.setattr(
        bus,
        "list_heartbeats",
        lambda vault_root, runtime=None: [
            {
                "runtime": "Hermes",
                "heartbeat_scope": "runtime",
                "status": "idle",
                "health": "ok",
                "last_seen": "2026-04-27T10:09:30Z",
            }
        ],
    )

    result = build_coordination_watch_activation_report("hermes", now_iso="2026-04-27T10:10:00Z")

    assert result["action"] == "activation-report"
    assert result["activation_state"] == "proven"
    assert result["proof_ready"] is True
    assert result["proof_complete"] is True
    assert result["checks"]["scheduler_registered"] is True
    assert result["checks"]["supervisor_running"] is True
    assert result["checks"]["heartbeat_fresh"] is True
    assert result["checks"]["proof_complete"] is True
    assert result["activation_proof"]["missing_evidence"] == []
    assert result["heartbeat"]["age_seconds"] == 30
    assert result["next_actions"] == []


def test_build_coordination_watch_activation_report_requires_reboot_evidence_for_proven(monkeypatch):
    from runtime.agent_bus import bus

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "interval_seconds": 30,
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_coordination_watch_bootstrap_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "installed": True,
            "handoff_ready": True,
            "reboot_verification_ready": True,
            "success_record_path": "runtime/lifecycle/run/hermes-coordination-watch-bootstrap-success.json",
            "reboot_verify_result_path": "runtime/lifecycle/run/hermes-coordination-watch-reboot-verify-result.json",
            "event_log_path": "runtime/lifecycle/run/hermes-coordination-watch-bootstrap-events.jsonl",
            "latest_success_record": {
                "timestamp_utc": "2026-04-27T10:00:00Z",
                "runtime_id": "hermes",
                "task_name": "ChaseOS-Hermes-Coordination-Watch",
                "registration_kind": "windows-task-scheduler",
                "scheduler_registered": True,
                "verification_returncode": 0,
                "verification_stdout": "TaskName: ChaseOS-Hermes-Coordination-Watch",
                "supervisor_state_present": True,
                "supervisor_log_present": True,
                "success_observed": True,
            },
            "latest_reboot_verify_result": None,
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "running": True,
            "state_present": True,
            "state_file": "runtime/lifecycle/run/hermes-coordination-watch.json",
            "log_file": "runtime/lifecycle/run/hermes-coordination-watch.log",
            "interval_seconds": 30,
            "stale_after_seconds": 900,
        },
    )

    class Result:
        returncode = 0
        stdout = "TaskName: ChaseOS-Hermes-Coordination-Watch"
        stderr = ""

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.subprocess.run",
        lambda command, capture_output=True, text=True, check=False: Result(),
    )
    monkeypatch.setattr(
        bus,
        "list_heartbeats",
        lambda vault_root, runtime=None: [
            {
                "runtime": "Hermes",
                "heartbeat_scope": "runtime",
                "status": "idle",
                "health": "ok",
                "last_seen": "2026-04-27T10:09:30Z",
            }
        ],
    )

    result = build_coordination_watch_activation_report("hermes", now_iso="2026-04-27T10:10:00Z")

    assert result["activation_state"] == "live-awaiting-reboot-proof"
    assert result["proof_ready"] is True
    assert result["proof_complete"] is False
    assert result["checks"]["success_observed"] is True
    assert result["checks"]["reboot_success_observed"] is False
    assert result["activation_proof"]["missing_evidence"] == ["reboot_verification_observed"]
    assert result["next_actions"] == ["run-reboot-verify-after-next-logon"]


def test_build_coordination_watch_activation_report_reports_partial_next_actions(monkeypatch):
    from runtime.agent_bus import bus

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "OpenClaw",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-OpenClaw-Coordination-Watch",
            "interval_seconds": 30,
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_coordination_watch_bootstrap_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "OpenClaw",
            "bootstrap_enabled": True,
            "installed": True,
            "handoff_ready": False,
            "reboot_verification_ready": False,
            "latest_success_record": None,
            "latest_reboot_verify_result": None,
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "OpenClaw",
            "running": False,
            "state_present": False,
            "interval_seconds": 30,
            "stale_after_seconds": 900,
        },
    )

    class Result:
        returncode = 1
        stdout = ""
        stderr = "ERROR: The system cannot find the file specified."

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.subprocess.run",
        lambda command, capture_output=True, text=True, check=False: Result(),
    )
    monkeypatch.setattr(bus, "list_heartbeats", lambda vault_root, runtime=None: [])

    result = build_coordination_watch_activation_report("openclaw", now_iso="2026-04-27T10:10:00Z")

    assert result["activation_state"] == "partial"
    assert result["proof_ready"] is False
    assert result["checks"]["installed"] is True
    assert result["checks"]["scheduler_registered"] is False
    assert result["next_actions"] == ["apply-or-handoff"]


def test_build_coordination_watch_activation_report_degrades_when_schtasks_unavailable(monkeypatch):
    from runtime.agent_bus import bus

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "interval_seconds": 30,
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_coordination_watch_bootstrap_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "bootstrap_enabled": True,
            "installed": True,
            "handoff_ready": True,
            "reboot_verification_ready": True,
            "latest_success_record": None,
            "latest_reboot_verify_result": None,
        },
    )
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "running": False,
            "state_present": False,
            "interval_seconds": 30,
            "stale_after_seconds": 900,
        },
    )

    def missing_schtasks(command, capture_output=True, text=True, check=False):
        raise FileNotFoundError(2, "No such file or directory", "schtasks")

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.subprocess.run", missing_schtasks)
    monkeypatch.setattr(bus, "list_heartbeats", lambda vault_root, runtime=None: [])

    result = build_coordination_watch_activation_report("hermes", now_iso="2026-04-27T10:10:00Z")

    assert result["activation_state"] == "degraded"
    assert result["checks"]["scheduler_available"] is False
    assert result["checks"]["scheduler_registered"] is False
    assert result["scheduler"]["available"] is False
    assert result["scheduler"]["unavailable_reason"] == "executable-not-found: schtasks"
    assert result["scheduler"]["returncode"] is None
    assert result["next_actions"] == ["run-on-windows-host-or-handoff"]


def test_build_coordination_watch_activation_checklist_guides_inactive_runtime(monkeypatch):
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_activation_report",
        lambda runtime_id, now_iso=None: {
            "runtime_id": runtime_id,
            "runtime_name": "OpenClaw",
            "task_name": "ChaseOS-OpenClaw-Coordination-Watch",
            "registration_kind": "windows-task-scheduler",
            "activation_state": "inactive",
            "proof_ready": False,
            "proof_complete": False,
            "checks": {
                "installed": False,
                "handoff_ready": False,
                "reboot_verification_ready": False,
                "scheduler_registered": False,
                "supervisor_running": False,
                "heartbeat_fresh": False,
                "success_observed": False,
                "reboot_success_observed": False,
            },
            "activation_proof": {
                "missing_evidence": [
                    "host_startup_registered",
                    "supervisor_running",
                    "heartbeat_fresh",
                    "success_record_observed",
                    "reboot_verification_observed",
                ],
                "evidence_paths": {
                    "success_record_path": "runtime/lifecycle/run/openclaw-success.json",
                    "reboot_verify_result_path": "runtime/lifecycle/run/openclaw-reboot-result.json",
                },
            },
            "bootstrap_status": {
                "handoff_script_path": "runtime/lifecycle/bootstrap/openclaw-handoff.ps1",
                "reboot_verify_script_path": "runtime/lifecycle/bootstrap/openclaw-reboot-verify.ps1",
            },
        },
    )

    result = build_coordination_watch_activation_checklist("openclaw")

    assert result["action"] == "activation-checklist"
    assert result["activation_state"] == "inactive"
    assert result["proof_complete"] is False
    assert result["current_step"]["step_id"] == "install-artifacts"
    assert result["current_step"]["status"] == "ready"
    assert result["ready_commands"][0] == [
        "chaseos",
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "openclaw",
        "--action",
        "install",
        "--json",
    ]
    assert "host_startup_registered" in result["missing_evidence"]


def test_build_coordination_watch_activation_checklist_marks_reboot_host_action(monkeypatch):
    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_activation_report",
        lambda runtime_id, now_iso=None: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "registration_kind": "windows-task-scheduler",
            "activation_state": "live-awaiting-reboot-proof",
            "proof_ready": True,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "handoff_ready": True,
                "reboot_verification_ready": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
                "success_observed": True,
                "reboot_success_observed": False,
            },
            "activation_proof": {
                "missing_evidence": ["reboot_verification_observed"],
                "evidence_paths": {
                    "success_record_path": "runtime/lifecycle/run/hermes-success.json",
                    "reboot_verify_result_path": "runtime/lifecycle/run/hermes-reboot-result.json",
                },
            },
            "bootstrap_status": {
                "handoff_script_path": "runtime/lifecycle/bootstrap/hermes-handoff.ps1",
                "reboot_verify_script_path": "runtime/lifecycle/bootstrap/hermes-reboot-verify.ps1",
            },
        },
    )

    result = build_coordination_watch_activation_checklist("hermes")

    assert result["current_step"]["step_id"] == "run-post-reboot-verification"
    assert result["current_step"]["status"] == "host-action-required"
    assert result["host_required_steps"][0]["step_id"] == "run-post-reboot-verification"
    assert result["host_required_steps"][0]["host_command"] == (
        "PowerShell -ExecutionPolicy Bypass -File runtime/lifecycle/bootstrap/hermes-reboot-verify.ps1"
    )
    assert result["missing_evidence"] == ["reboot_verification_observed"]


def test_capture_coordination_watch_bootstrap_success_state_writes_success_record(monkeypatch, tmp_path):
    success_record_path = tmp_path / "hermes-bootstrap-success.json"
    supervisor_state_file = tmp_path / "hermes-supervisor-state.json"
    supervisor_log_file = tmp_path / "hermes-supervisor.log"
    supervisor_state_file.write_text(json.dumps({"pid": 1234}), encoding="utf-8")
    supervisor_log_file.write_text("running\n", encoding="utf-8")

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.ROOT", tmp_path)
    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap._utc_now_iso", lambda: "2026-04-26T04:30:00Z")

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "success_record_path": str(success_record_path),
            "state_file": str(supervisor_state_file),
            "log_file": str(supervisor_log_file),
            "event_log_path": str(tmp_path / "events.jsonl"),
            "wsl_distro": "Ubuntu",
        },
    )

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.verify_coordination_watch_bootstrap",
        lambda runtime_id: {
            "action": "verify",
            "runtime_id": runtime_id,
            "runtime_name": "Hermes",
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "registered": True,
            "query_command": ["schtasks", "/Query", "/TN", "ChaseOS-Hermes-Coordination-Watch"],
            "returncode": 0,
            "stdout": "TaskName: ChaseOS-Hermes-Coordination-Watch",
            "stderr": "",
        },
    )

    result = capture_coordination_watch_bootstrap_success_state("hermes")

    assert result["success_record_written"] is True
    assert result["scheduler_registered"] is True
    assert result["supervisor_state_present"] is True
    assert result["supervisor_log_present"] is True
    assert result["success_observed"] is True
    assert result["agent_activity_record_written"] is True
    assert success_record_path.exists()
    record = json.loads(success_record_path.read_text(encoding="utf-8"))
    assert record["success_observed"] is True
    assert record["scheduler_registered"] is True
    assert record["agent_activity_record_path"].endswith("2026-04-26-hermes-coordination-watch-bootstrap-success-043000z.md")
    activity_record_path = Path(record["agent_activity_record_path"])
    assert activity_record_path.exists()
    activity_text = activity_record_path.read_text(encoding="utf-8")
    assert "confirmed startup success" in activity_text.lower()
    assert "ChaseOS-Hermes-Coordination-Watch" in activity_text


def test_capture_coordination_watch_bootstrap_success_state_skips_agent_activity_until_success_observed(monkeypatch, tmp_path):
    success_record_path = tmp_path / "openclaw-bootstrap-success.json"

    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap.ROOT", tmp_path)
    monkeypatch.setattr("runtime.lifecycle.coordination_watch_bootstrap._utc_now_iso", lambda: "2026-04-26T04:31:00Z")

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.build_coordination_watch_bootstrap_plan",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "runtime_name": "OpenClaw",
            "registration_kind": "windows-task-scheduler",
            "task_name": "ChaseOS-OpenClaw-Coordination-Watch",
            "success_record_path": str(success_record_path),
            "state_file": str(tmp_path / "missing-state.json"),
            "log_file": str(tmp_path / "missing.log"),
            "event_log_path": str(tmp_path / "events.jsonl"),
            "wsl_distro": "Ubuntu",
        },
    )

    monkeypatch.setattr(
        "runtime.lifecycle.coordination_watch_bootstrap.verify_coordination_watch_bootstrap",
        lambda runtime_id: {
            "action": "verify",
            "runtime_id": runtime_id,
            "runtime_name": "OpenClaw",
            "task_name": "ChaseOS-OpenClaw-Coordination-Watch",
            "registered": False,
            "query_command": ["schtasks", "/Query", "/TN", "ChaseOS-OpenClaw-Coordination-Watch"],
            "returncode": 1,
            "stdout": "",
            "stderr": "ERROR: The system cannot find the file specified.",
        },
    )

    result = capture_coordination_watch_bootstrap_success_state("openclaw")

    assert result["success_record_written"] is True
    assert result["success_observed"] is False
    assert result["agent_activity_record_written"] is False
    assert result["agent_activity_record_path"] is None
    record = json.loads(success_record_path.read_text(encoding="utf-8"))
    assert record["agent_activity_record_path"] is None
    assert not (tmp_path / "07_LOGS" / "Agent-Activity").exists()
