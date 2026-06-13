"""Tests for packaged Studio host-policy unblock readiness."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.studio import packaged_app_host_policy_unblock as unblock


def test_host_policy_unblock_readiness_requires_probe(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    monkeypatch.setattr(
        unblock,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )

    report = unblock.build_packaged_app_host_policy_unblock_readiness(
        tmp_path,
        executable_path=exe,
    )

    assert report["ok"] is False
    assert report["status"] == "host_policy_probe_required"
    assert report["readiness"]["host_policy_probe_performed"] is False
    assert report["authority"]["mutates_host_policy"] is False
    assert report["next_recommended_pass"] == "pass10b-native-host-policy-unblock"


def test_host_policy_unblock_readiness_reports_application_control_block(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    monkeypatch.setattr(
        unblock,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )

    def fake_visual_qa(*_args, **_kwargs):
        return {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "host_policy": {
                "status": "blocked_by_windows_application_control",
                "blocked_by_windows_application_control": True,
            },
            "checks": [
                {"name": "host_policy_allows_launch", "ok": False, "detail": "blocked_by_windows_application_control"},
                {"name": "no_markdown_writes", "ok": True, "detail": "markdown unchanged"},
                {"name": "no_approval_artifact_writes", "ok": True, "detail": "approvals unchanged"},
            ],
        }

    monkeypatch.setattr(unblock, "build_packaged_app_visual_qa", fake_visual_qa)

    report = unblock.build_packaged_app_host_policy_unblock_readiness(
        tmp_path,
        executable_path=exe,
        probe_launch=True,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert report["status"] == "blocked_by_windows_application_control"
    assert report["readiness"]["host_policy_probe_performed"] is True
    assert report["readiness"]["host_policy_allows_launch"] is False
    assert checks["codex_did_not_mutate_host_policy"]["ok"] is True
    assert "Windows Application Control" in report["blockers"][0]


def test_host_policy_unblock_readiness_routes_to_visual_qa_rerun_when_launch_allowed(
    monkeypatch, tmp_path: Path
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    monkeypatch.setattr(
        unblock,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )

    def fake_visual_qa(*_args, **_kwargs):
        return {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "host_policy": {
                "status": "not_applicable",
                "blocked_by_windows_application_control": False,
            },
            "checks": [
                {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                {"name": "no_markdown_writes", "ok": True, "detail": "markdown unchanged"},
                {"name": "no_approval_artifact_writes", "ok": True, "detail": "approvals unchanged"},
            ],
        }

    monkeypatch.setattr(unblock, "build_packaged_app_visual_qa", fake_visual_qa)

    report = unblock.build_packaged_app_host_policy_unblock_readiness(
        tmp_path,
        executable_path=exe,
        probe_launch=True,
    )

    assert report["status"] == "host_policy_unblocked_visual_qa_retry_needed"
    assert report["readiness"]["native_visual_qa_can_retry"] is True
    assert report["next_recommended_pass"] == "pass10b-native-visual-qa-rerun"


def test_host_policy_unblock_readiness_probes_explicit_executable_without_default_packaging_proof(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "custom-proof" / "dist" / "ChaseOS-Studio" / "ChaseOS-Studio.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"fake exe")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        unblock,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": False, "executable_sha256": None}},
    )

    def fake_visual_qa(*_args, **kwargs):
        captured.update(kwargs)
        return {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "host_policy": {
                "status": "not_applicable",
                "blocked_by_windows_application_control": False,
            },
            "checks": [
                {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                {"name": "no_markdown_writes", "ok": True, "detail": "markdown unchanged"},
                {"name": "no_approval_artifact_writes", "ok": True, "detail": "approvals unchanged"},
            ],
        }

    monkeypatch.setattr(unblock, "build_packaged_app_visual_qa", fake_visual_qa)

    report = unblock.build_packaged_app_host_policy_unblock_readiness(
        tmp_path,
        executable_path=exe,
        probe_launch=True,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert captured["executable_path"] == exe
    assert report["executable"]["source"] == "explicit_executable_path"
    assert report["readiness"]["packaged_executable_ready_for_probe"] is True
    assert checks["packaging_proof_executable_seen"]["ok"] is True
    assert "Local packaging proof does not currently see a generated executable." not in report["blockers"]


def test_host_policy_unblock_parser_exposes_probe_launch() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "packaged-app-host-policy-unblock-readiness",
            "--probe-launch",
            "--settle-seconds",
            "2",
            "--window-timeout-seconds",
            "3",
            "--terminate-timeout-seconds",
            "4",
            "--write-handoff",
            "--handoff-slug",
            "handoff-test",
        ]
    )

    assert args.probe_launch is True
    assert args.settle_seconds == 2
    assert args.window_timeout_seconds == 3
    assert args.terminate_timeout_seconds == 4
    assert args.write_handoff is True
    assert args.handoff_slug == "handoff-test"


def test_host_policy_unblock_handoff_writer_stays_in_vault(tmp_path: Path) -> None:
    report = {
        "status": "blocked_by_windows_application_control",
        "ok": False,
        "executable": {"path": "dist/ChaseOS-Studio.exe", "exists": True, "sha256": "abc"},
        "host_policy": {
            "status": "blocked_by_windows_application_control",
            "blocked_by_windows_application_control": True,
        },
        "readiness": {"host_policy_allows_launch": False},
        "operator_handoff": {
            "required_external_actions": ["Resolve host policy."],
            "acceptance_criteria": ["`host_policy_allows_launch=true`"],
            "probe_command": "python -m chaseos studio packaged-app-host-policy-unblock-readiness --probe-launch --json",
            "visual_qa_command": "python -m chaseos studio packaged-app-visual-qa --json",
        },
        "authority": {"mutates_host_policy": False},
        "checks": [],
        "blockers": ["Windows Application Control blocks the packaged Studio executable."],
    }

    evidence = unblock.write_packaged_app_host_policy_unblock_handoff(
        tmp_path,
        report,
        handoff_slug="handoff-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    markdown = tmp_path / evidence["markdown_path"]
    assert markdown.is_file()
    assert "review-only" in markdown.read_text(encoding="utf-8")


def test_host_policy_unblock_handoff_writer_rejects_slug_escape_from_handoff_root(tmp_path: Path) -> None:
    report = {
        "status": "blocked_by_windows_application_control",
        "ok": False,
        "executable": {"path": "dist/ChaseOS-Studio.exe", "exists": True, "sha256": "abc"},
        "host_policy": {
            "status": "blocked_by_windows_application_control",
            "blocked_by_windows_application_control": True,
        },
        "readiness": {"host_policy_allows_launch": False},
        "operator_handoff": {
            "required_external_actions": ["Resolve host policy."],
            "acceptance_criteria": ["`host_policy_allows_launch=true`"],
            "probe_command": "python -m chaseos studio packaged-app-host-policy-unblock-readiness --probe-launch --json",
            "visual_qa_command": "python -m chaseos studio packaged-app-visual-qa --json",
        },
        "authority": {"mutates_host_policy": False},
        "checks": [],
        "blockers": ["Windows Application Control blocks the packaged Studio executable."],
    }

    with pytest.raises(ValueError, match="handoff output must stay inside the handoff root"):
        unblock.write_packaged_app_host_policy_unblock_handoff(
            tmp_path,
            report,
            handoff_root="handoffs",
            handoff_slug="../vault-local-but-outside-handoff-root",
        )
    assert (tmp_path / "handoffs").exists() is False
    assert (tmp_path / "vault-local-but-outside-handoff-root.json").exists() is False
    assert (tmp_path / "vault-local-but-outside-handoff-root.md").exists() is False
