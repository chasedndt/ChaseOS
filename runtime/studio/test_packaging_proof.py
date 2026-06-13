"""Tests for the bounded native Studio local packaging proof."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from runtime.studio import packaging_proof
from runtime.studio.packaging_proof import build_studio_local_packaging_proof, write_packaging_proof_evidence
from runtime.studio.packaging_readiness import build_studio_packaging_readiness


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_local_packaging_proof_blocks_without_local_dependencies(monkeypatch) -> None:
    def fake_module_available(module_name: str) -> bool:
        return False

    monkeypatch.setattr(packaging_proof, "_module_available", fake_module_available)

    report = build_studio_local_packaging_proof(VAULT_ROOT, execute_build=True)

    assert report["ok"] is False
    assert report["status"] == "blocked_local_packaging_proof"
    assert report["command"]["started"] is False
    assert report["dependencies"]["pyinstaller_available"] is False
    assert report["dependencies"]["pywebview_available"] is False
    assert "PyInstaller is not installed in the active Python environment." in report["blockers"]
    assert "pywebview is not installed in the active Python environment." in report["blockers"]
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["launches_executable"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False


def test_local_packaging_proof_preflight_passes_when_dependencies_available(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(packaging_proof, "_module_available", lambda _name: True)

    report = build_studio_local_packaging_proof(
        VAULT_ROOT,
        execute_build=False,
        output_root=tmp_path,
    )

    assert report["ok"] is True
    assert report["status"] == "ready_to_execute_local_packaging_proof"
    assert report["command"]["started"] is False
    assert report["outputs"]["executable_exists"] is False
    assert report["authority"]["builds_executable"] is False
    assert report["next_recommended_pass"] == "studio-local-packaging-proof"


def test_expected_executable_uses_windows_desktop_exe_contract(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(packaging_proof.sys, "platform", "linux")
    assert packaging_proof._expected_executable(tmp_path) == tmp_path / "dist" / packaging_proof.APP_NAME / f"{packaging_proof.APP_NAME}.exe"

    monkeypatch.setattr(packaging_proof.sys, "platform", "win32")
    assert packaging_proof._expected_executable(tmp_path) == tmp_path / "dist" / packaging_proof.APP_NAME / f"{packaging_proof.APP_NAME}.exe"


def test_packaging_proof_expected_executable_matches_readiness_dist_contract(tmp_path: Path) -> None:
    readiness = build_studio_packaging_readiness(VAULT_ROOT)

    assert readiness["packaging_target"]["dist_exe"] == "dist/ChaseOS-Studio/ChaseOS-Studio.exe"
    assert packaging_proof._expected_executable(tmp_path).relative_to(tmp_path).as_posix() == readiness["packaging_target"]["dist_exe"]


def test_packaging_spec_includes_recovered_studio_api_bytecode() -> None:
    spec = (VAULT_ROOT / packaging_proof.SPEC_PATH).read_text(encoding="utf-8")

    assert 'RECOVERY = ROOT / "runtime" / "studio" / "recovery"' in spec
    assert '(str(RECOVERY), "runtime/studio/recovery")' in spec


def test_local_packaging_proof_execute_records_output_hash(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(packaging_proof, "_module_available", lambda _name: True)

    def fake_run_command(args, *, cwd, timeout_seconds):
        distpath = Path(args[args.index("--distpath") + 1])
        exe = packaging_proof._expected_executable(distpath.parent)
        exe.parent.mkdir(parents=True, exist_ok=True)
        exe.write_bytes(b"fake studio executable")
        return {
            "ok": True,
            "returncode": 0,
            "stdout_tail": "fake build complete",
            "stderr_tail": "",
            "timed_out": False,
        }

    monkeypatch.setattr(packaging_proof, "_run_command", fake_run_command)

    report = build_studio_local_packaging_proof(
        VAULT_ROOT,
        execute_build=True,
        output_root=tmp_path,
        timeout_seconds=1,
    )

    assert report["ok"] is True
    assert report["status"] == "local_packaging_proof_complete"
    assert report["command"]["started"] is True
    assert report["outputs"]["executable_exists"] is True
    assert report["outputs"]["executable_sha256"]
    assert report["authority"]["builds_executable"] is True
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["launches_executable"] is False
    assert report["next_recommended_pass"] == "studio-packaged-app-launch-smoke"


def test_local_packaging_proof_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": False,
        "status": "blocked_local_packaging_proof",
        "generated_at": "2026-05-04T00:00:00Z",
        "execute_build_requested": True,
        "dependencies": {"pyinstaller_available": False, "pywebview_available": False},
        "outputs": {
            "output_root": ".pytest_tmp_env/studio-packaging-proof",
            "expected_executable": ".pytest_tmp_env/studio-packaging-proof/dist/ChaseOS-Studio/ChaseOS-Studio.exe",
            "executable_exists": False,
            "executable_sha256": None,
        },
        "blockers": ["PyInstaller is not installed in the active Python environment."],
        "authority": {"canonical_mutation_allowed": False},
    }

    evidence = write_packaging_proof_evidence(
        tmp_path,
        report,
        evidence_slug="packaging-proof-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()


def test_local_packaging_proof_evidence_writer_rejects_slug_escape_from_evidence_root(tmp_path: Path) -> None:
    report = {"ok": False, "status": "fixture"}

    with pytest.raises(ValueError, match="evidence output must stay inside the evidence root"):
        write_packaging_proof_evidence(
            tmp_path,
            report,
            evidence_root="evidence",
            evidence_slug="../vault-local-but-outside-evidence-root",
        )

    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.json").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.md").exists()


def test_local_packaging_proof_cli_returns_json_error_for_slug_escape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from runtime.cli.main import cmd_studio_local_packaging_proof

    monkeypatch.setattr(packaging_proof, "_module_available", lambda _name: True)

    code = cmd_studio_local_packaging_proof(
        argparse.Namespace(
            vault_root=str(tmp_path),
            execute_build=False,
            output_root=None,
            timeout_seconds=1.0,
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
