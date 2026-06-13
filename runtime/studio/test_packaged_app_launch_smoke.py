"""Tests for packaged Studio app launch smoke."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pytest

from runtime.studio import packaged_app_launch_smoke as launch_smoke
from runtime.studio.packaging_readiness import build_studio_packaging_readiness


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_packaged_launch_smoke_default_executable_matches_packaging_contract() -> None:
    readiness = build_studio_packaging_readiness(VAULT_ROOT)

    assert launch_smoke.DEFAULT_EXE.as_posix() == f".pytest_tmp_env/studio-packaging-proof/{readiness['packaging_target']['dist_exe']}"


def test_packaged_launch_smoke_converts_wsl_mnt_vault_arg_for_windows_packaged_exe(monkeypatch) -> None:
    calls = {}

    class FakeCompleted:
        stdout = "C:\\Users\\chaseos\\Documents\\chaseos_obsidian\n"

    def fake_run(args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs
        return FakeCompleted()

    monkeypatch.setattr(launch_smoke.subprocess, "run", fake_run)

    converted = launch_smoke._vault_arg_for_packaged_exe(Path("<VAULT_ROOT>"))

    assert converted == "C:\\Users\\chaseos\\Documents\\chaseos_obsidian"
    assert calls["args"] == ["wslpath", "-w", "<VAULT_ROOT>"]


class FakeProcess:
    def __init__(self, *, alive: bool = True) -> None:
        self.pid = 12345
        self.returncode = None
        self._alive = alive
        self.terminated = False
        self.killed = False

    def poll(self):
        return None if self._alive else self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self._alive = False
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self._alive = False
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode

    def communicate(self, timeout=None):
        return "", ""


def test_packaged_launch_smoke_rejects_executable_outside_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.exe"
    outside.write_bytes(b"exe")

    with pytest.raises(ValueError):
        launch_smoke.build_packaged_app_launch_smoke(vault, executable_path=outside)


def test_packaged_launch_smoke_blocks_when_executable_missing(tmp_path: Path) -> None:
    report = launch_smoke.build_packaged_app_launch_smoke(
        VAULT_ROOT,
        executable_path=Path(".pytest_tmp_env") / "missing-packaged-app.exe",
        settle_seconds=0.1,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_packaged_app_launch_smoke"
    assert "Packaged Studio executable is missing." in report["blockers"]
    assert report["authority"]["launches_packaged_executable"] is False


def test_packaged_launch_smoke_missing_executable_uses_fast_preflight(monkeypatch, tmp_path: Path) -> None:
    def fail_packaging_proof(_vault: Path):
        raise AssertionError("missing executable preflight must not inspect packaging proof")

    def fail_snapshot(_vault: Path):
        raise AssertionError("missing executable preflight must not scan the vault")

    monkeypatch.setattr(launch_smoke, "build_studio_local_packaging_proof", fail_packaging_proof)
    monkeypatch.setattr(launch_smoke, "_markdown_snapshot", fail_snapshot)
    monkeypatch.setattr(launch_smoke, "_approval_artifact_snapshot", fail_snapshot)

    report = launch_smoke.build_packaged_app_launch_smoke(
        tmp_path,
        executable_path="missing-packaged-app.exe",
        settle_seconds=0.1,
    )

    assert report["ok"] is False
    assert report["launch"]["started"] is False
    assert "Packaged Studio executable is missing." in report["blockers"]
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_packaged_launch_smoke_launches_and_terminates_owned_process(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    popen_args = {}

    monkeypatch.setattr(
        launch_smoke,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(launch_smoke.time, "sleep", lambda _seconds: None)

    def fake_popen(args, **kwargs):
        popen_args["args"] = args
        popen_args["kwargs"] = kwargs
        return fake_process

    monkeypatch.setattr(launch_smoke.subprocess, "Popen", fake_popen)

    report = launch_smoke.build_packaged_app_launch_smoke(
        tmp_path,
        executable_path=exe,
        settle_seconds=0.1,
        terminate=True,
    )

    assert report["ok"] is True
    assert report["status"] == "packaged_app_launch_smoke_complete"
    assert popen_args["args"][2] == str(tmp_path.resolve())
    assert report["launch"]["started"] is True
    assert report["launch"]["process_alive_after_settle"] is True
    assert report["termination"]["terminated"] is True
    assert fake_process.terminated is True
    assert report["authority"]["launches_packaged_executable"] is True
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["owned_process_terminated"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_packaged_launch_smoke_blocks_on_markdown_write_sentinel(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    markdown_snapshots = iter([{}, {"06_AGENTS/Feature-Fit-Register.md": 1.0}])

    monkeypatch.setattr(
        launch_smoke,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(launch_smoke.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(launch_smoke.subprocess, "Popen", lambda *args, **kwargs: fake_process)
    monkeypatch.setattr(launch_smoke, "_markdown_snapshot", lambda _vault: next(markdown_snapshots))
    monkeypatch.setattr(launch_smoke, "_approval_artifact_snapshot", lambda _vault: {})

    report = launch_smoke.build_packaged_app_launch_smoke(
        tmp_path,
        executable_path=exe,
        settle_seconds=0.1,
        terminate=True,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert "Markdown write sentinel changed during packaged launch smoke." in report["blockers"]
    assert checks["no_markdown_writes"]["ok"] is False
    assert "added: 06_AGENTS/Feature-Fit-Register.md" in checks["no_markdown_writes"]["detail"]
    assert report["write_sentinel"]["markdown"]["added"] == ["06_AGENTS/Feature-Fit-Register.md"]


def test_markdown_snapshot_ignores_timestamp_only_touches(tmp_path: Path) -> None:
    doc = tmp_path / "06_AGENTS" / "Feature-Fit-Register.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("same content\n", encoding="utf-8")

    before = launch_smoke._markdown_snapshot(tmp_path)
    os.utime(doc, (doc.stat().st_atime + 60, doc.stat().st_mtime + 60))
    after = launch_smoke._markdown_snapshot(tmp_path)

    assert before == after
    assert launch_smoke._snapshot_delta(before, after) == {"added": [], "removed": [], "modified": []}


def test_approval_snapshot_includes_capture_downstream_approval_roots(tmp_path: Path) -> None:
    artifact = (
        tmp_path
        / "07_LOGS"
        / "Agent-Activity"
        / "_vcmi_aor_dispatch_approvals"
        / "approval-request.json"
    )
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"status":"pending"}\n', encoding="utf-8")

    snapshot = launch_smoke._approval_artifact_snapshot(tmp_path)

    assert "07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/approval-request.json" in snapshot


def test_packaged_launch_smoke_accepts_explicit_executable_when_default_proof_root_is_empty(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        launch_smoke,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": False, "executable_sha256": None}},
    )
    monkeypatch.setattr(launch_smoke.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(launch_smoke.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    report = launch_smoke.build_packaged_app_launch_smoke(
        tmp_path,
        executable_path=exe,
        settle_seconds=0.1,
        terminate=True,
    )

    assert report["ok"] is True
    assert report["executable"]["sha256"]
    assert "Local packaging proof does not currently see a generated executable." not in report["blockers"]


def test_packaged_launch_smoke_hashes_explicit_executable_instead_of_default_packaging_proof(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "explicit" / "ChaseOS-Studio.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"explicit executable bytes")
    fake_process = FakeProcess(alive=True)
    proof_sha = "0" * 64

    monkeypatch.setattr(
        launch_smoke,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": proof_sha}},
    )
    monkeypatch.setattr(launch_smoke.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(launch_smoke.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    report = launch_smoke.build_packaged_app_launch_smoke(
        tmp_path,
        executable_path=exe,
        settle_seconds=0.1,
        terminate=True,
    )

    assert report["ok"] is True
    assert report["executable"]["path"] == "explicit/ChaseOS-Studio.exe"
    assert report["executable"]["sha256"] == launch_smoke._sha256(exe)
    assert report["executable"]["sha256"] != proof_sha


def test_packaged_launch_smoke_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": "packaged_app_launch_smoke_complete",
        "generated_at": "2026-05-04T00:00:00Z",
        "executable": {"path": "app.exe", "exists": True, "sha256": "abc"},
        "launch": {"started": True, "process_id": 1, "process_alive_after_settle": True},
        "termination": {"terminated": True},
        "checks": [{"name": "process_alive_after_settle", "ok": True, "detail": "ok"}],
        "authority": {"canonical_mutation_allowed": False},
    }

    evidence = launch_smoke.write_launch_smoke_evidence(
        tmp_path,
        report,
        evidence_slug="launch-smoke-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()


def test_packaged_launch_smoke_evidence_writer_rejects_slug_escape_from_evidence_root(tmp_path: Path) -> None:
    report = {"ok": False, "status": "fixture"}

    with pytest.raises(ValueError, match="evidence output must stay inside the evidence root"):
        launch_smoke.write_launch_smoke_evidence(
            tmp_path,
            report,
            evidence_root="evidence",
            evidence_slug="../vault-local-but-outside-evidence-root",
        )

    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.json").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.md").exists()


def test_packaged_launch_smoke_cli_returns_json_error_for_slug_escape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from runtime.cli.main import cmd_studio_packaged_app_launch_smoke

    code = cmd_studio_packaged_app_launch_smoke(
        argparse.Namespace(
            vault_root=str(tmp_path),
            executable_path=".pytest_tmp_env/missing-packaged-app.exe",
            settle_seconds=0.1,
            keep_running=False,
            terminate_timeout_seconds=0.1,
            write_evidence=True,
            evidence_slug="../vault-local-but-outside-evidence-root",
            evidence_root="evidence",
            output_json=True,
        )
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == 1
    assert payload["ok"] is False
    assert "evidence output must stay inside the evidence root" in payload["error"]
    assert captured.err == ""
    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.json").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.md").exists()
