"""Tests for Studio installer governance plan."""

from __future__ import annotations

import json
from pathlib import Path
import hashlib

import pytest

from runtime.studio import installer_plan


FAKE_EXE_SHA256 = hashlib.sha256(b"fake exe").hexdigest()


def _seed_packaging_outputs(vault: Path) -> Path:
    exe = vault / ".pytest_tmp_env" / "studio-packaging-proof" / "dist" / "ChaseOS-Studio" / "ChaseOS-Studio.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"fake exe")
    evidence = vault / "07_LOGS" / "Studio-Graph-Views"
    evidence.mkdir(parents=True)
    (evidence / "2026-05-04-studio-local-packaging-proof.md").write_text("# proof\n", encoding="utf-8")
    (evidence / "2026-05-04-studio-packaged-app-launch-smoke.json").write_text('{"ok": true}', encoding="utf-8")
    (evidence / "2026-05-04-studio-packaged-app-visual-qa.json").write_text('{"ok": true}', encoding="utf-8")
    (evidence / "2026-05-04-studio-packaged-app-visual-qa.png").write_bytes(b"x" * 2048)
    return exe


def _seed_pass10b_completion_audit(
    vault: Path,
    *,
    ok: bool,
    name: str | None = None,
    generated_at: str | None = None,
) -> Path:
    root = vault / "07_LOGS" / "Studio-Graph-Views" / "pass10b-completion-audits"
    root.mkdir(parents=True, exist_ok=True)
    path = root / (name or ("2026-05-11-pass10b-complete.json" if ok else "2026-05-11-pass10b-blocked.json"))
    checklist = [
        {"id": "native_host_policy_allows_launch", "ok": ok, "status": "VERIFIED" if ok else "BLOCKED"},
        {"id": "native_packaged_visual_qa_complete", "ok": ok, "status": "VERIFIED" if ok else "BLOCKED"},
        {"id": "packaged_visual_qa_saved_report_valid", "ok": ok, "status": "VERIFIED" if ok else "PARTIAL"},
    ]
    path.write_text(
        json.dumps(
            {
                "report_type": "pass10b_visual_proof_completion_audit",
                "generated_at": generated_at or ("2026-05-11T12:00:00Z" if ok else "2026-05-11T13:00:00Z"),
                "status": "COMPLETE" if ok else "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA",
                "ok": ok,
                "prompt_to_artifact_checklist": checklist,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_installer_plan_reports_governed_readiness_without_writes(monkeypatch, tmp_path: Path) -> None:
    _seed_packaging_outputs(tmp_path)
    _seed_pass10b_completion_audit(tmp_path, ok=True)
    monkeypatch.setattr(installer_plan, "build_studio_packaging_readiness", lambda _vault: {"ok": True})
    monkeypatch.setattr(
        installer_plan,
        "build_studio_local_packaging_proof",
        lambda _vault: {"ok": True, "outputs": {"executable_sha256": "abc"}},
    )

    report = installer_plan.build_studio_installer_plan(tmp_path)

    assert report["ok"] is True
    assert report["status"] == "ready_for_governed_installer_design"
    assert report["prerequisites"]["visual_qa_evidence_present"] is True
    assert report["prerequisites"]["legacy_visual_qa_ok"] is True
    assert report["prerequisites"]["pass10b_completion_audit_present"] is True
    assert report["prerequisites"]["pass10b_native_visual_qa_complete"] is True
    assert report["prerequisites"]["visual_qa_ok"] is True
    assert report["packaged_app"]["executable"]["exists"] is True
    assert report["packaged_app"]["sha256"] == FAKE_EXE_SHA256
    gate_ids = {item["id"] for item in report["governance_gates"]}
    assert "installer-build-approval" in gate_ids
    assert "signing-approval" in gate_ids
    assert "startup-autostart-approval" in gate_ids
    assert "release-promotion-approval" in gate_ids
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-governed-installer-build-approval"


def test_installer_plan_blocks_stale_visual_qa_when_latest_pass10b_audit_is_blocked(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_packaging_outputs(tmp_path)
    _seed_pass10b_completion_audit(tmp_path, ok=False)
    monkeypatch.setattr(installer_plan, "build_studio_packaging_readiness", lambda _vault: {"ok": True})
    monkeypatch.setattr(
        installer_plan,
        "build_studio_local_packaging_proof",
        lambda _vault: {"ok": True, "outputs": {"executable_sha256": "abc"}},
    )

    report = installer_plan.build_studio_installer_plan(tmp_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_installer_plan"
    assert report["prerequisites"]["visual_qa_evidence_present"] is True
    assert report["prerequisites"]["legacy_visual_qa_ok"] is True
    assert report["prerequisites"]["pass10b_completion_audit_present"] is True
    assert report["prerequisites"]["pass10b_completion_audit_ok"] is False
    assert report["prerequisites"]["pass10b_native_visual_qa_complete"] is False
    assert report["prerequisites"]["visual_qa_ok"] is False
    assert report["evidence"]["pass10b_completion_audit"]["blocks_installer_visual_qa"] is True
    assert "Latest Pass 10B completion audit does not verify native packaged visual QA." in report["blockers"]


def test_installer_plan_prefers_latest_complete_pass10b_audit_over_newer_blocked_diagnostic(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_packaging_outputs(tmp_path)
    newer_blocked = _seed_pass10b_completion_audit(
        tmp_path,
        ok=False,
        name="2026-05-11-pass10b-newer-blocked.json",
        generated_at="2026-05-11T13:00:00Z",
    )
    older_complete = _seed_pass10b_completion_audit(
        tmp_path,
        ok=True,
        name="2026-05-11-pass10b-older-complete-retouched.json",
        generated_at="2026-05-11T12:00:00Z",
    )
    newer_blocked.touch()
    older_complete.touch()
    monkeypatch.setattr(installer_plan, "build_studio_packaging_readiness", lambda _vault: {"ok": True})
    monkeypatch.setattr(
        installer_plan,
        "build_studio_local_packaging_proof",
        lambda _vault: {"ok": True, "outputs": {"executable_sha256": "abc"}},
    )

    report = installer_plan.build_studio_installer_plan(tmp_path)

    assert report["ok"] is True
    assert report["status"].startswith("ready_for_governed_installer_design")
    assert report["prerequisites"]["visual_qa_ok"] is True
    assert report["evidence"]["pass10b_completion_audit"]["path"].endswith(
        "2026-05-11-pass10b-older-complete-retouched.json"
    )
    assert str(report["evidence"]["pass10b_completion_audit"]["status"]).startswith("COMPLETE")


def test_installer_plan_blocks_missing_visual_evidence(monkeypatch, tmp_path: Path) -> None:
    _seed_packaging_outputs(tmp_path)
    (tmp_path / "07_LOGS" / "Studio-Graph-Views" / "2026-05-04-studio-packaged-app-visual-qa.png").unlink()
    monkeypatch.setattr(installer_plan, "build_studio_packaging_readiness", lambda _vault: {"ok": True})
    monkeypatch.setattr(
        installer_plan,
        "build_studio_local_packaging_proof",
        lambda _vault: {"ok": True, "outputs": {"executable_sha256": "abc"}},
    )

    report = installer_plan.build_studio_installer_plan(tmp_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_installer_plan"
    assert "Packaged app visual QA evidence is missing." in report["blockers"]
    assert report["next_recommended_pass"] == "studio-installer-plan-and-governance"


def test_installer_plan_prefers_current_visual_qa_over_legacy_green_report(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_packaging_outputs(tmp_path)
    _seed_pass10b_completion_audit(tmp_path, ok=True)
    current_root = tmp_path / "07_LOGS" / "Visual-QA" / "2026-05-23-studio-ui-packaged-proof-closure-update"
    current_root.mkdir(parents=True)
    current_visual_json = current_root / "2026-05-23-studio-ui-packaged-proof-visual-qa.json"
    current_visual_json.write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_visual_qa",
                "generated_at": "2026-05-23T19:17:26Z",
                "ok": False,
                "status": "blocked_packaged_app_visual_qa",
                "screenshot": {"path": "07_LOGS/Visual-QA/2026-05-23-studio-ui-packaged-proof-closure-update/current.png"},
                "blockers": ["PyWebView backend dependency is missing before native screenshot capture."],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(installer_plan, "build_studio_packaging_readiness", lambda _vault: {"ok": True})
    monkeypatch.setattr(
        installer_plan,
        "build_studio_local_packaging_proof",
        lambda _vault: {"ok": True, "outputs": {"executable_sha256": "abc"}},
    )

    report = installer_plan.build_studio_installer_plan(tmp_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_installer_plan"
    assert report["prerequisites"]["latest_visual_qa_ok"] is False
    assert report["prerequisites"]["visual_qa_ok"] is False
    assert report["evidence"]["visual_qa_json"]["path"].endswith(
        "07_LOGS/Visual-QA/2026-05-23-studio-ui-packaged-proof-closure-update/2026-05-23-studio-ui-packaged-proof-visual-qa.json"
    )
    assert "Latest packaged app visual QA is not green." in report["blockers"]


def test_installer_plan_surfaces_local_packaging_proof_blocker_detail(monkeypatch, tmp_path: Path) -> None:
    _seed_packaging_outputs(tmp_path)
    _seed_pass10b_completion_audit(tmp_path, ok=True)
    monkeypatch.setattr(installer_plan, "build_studio_packaging_readiness", lambda _vault: {"ok": True})
    monkeypatch.setattr(
        installer_plan,
        "build_studio_local_packaging_proof",
        lambda _vault: {
            "ok": False,
            "outputs": {"executable_sha256": "abc"},
            "blockers": ["PyInstaller is not installed in the active Python environment."],
        },
    )

    report = installer_plan.build_studio_installer_plan(tmp_path)

    assert report["ok"] is False
    assert (
        "Local packaging proof is not green: PyInstaller is not installed in the active Python environment."
        in report["blockers"]
    )


def test_installer_plan_rejects_executable_outside_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.exe"
    outside.write_bytes(b"exe")

    with pytest.raises(ValueError):
        installer_plan.build_studio_installer_plan(vault, executable_path=outside)


def test_installer_plan_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": "ready_for_governed_installer_design",
        "generated_at": "2026-05-04T00:00:00Z",
        "prerequisites": {"visual_qa_ok": True},
        "governance_gates": [{"id": "installer-build-approval", "status": "required_before_write", "required_before": ["writes_installer"]}],
        "authority": {"writes_installer": False, "canonical_mutation_allowed": False},
        "unverified": ["No installer was created."],
    }

    evidence = installer_plan.write_installer_plan_evidence(
        tmp_path,
        report,
        evidence_slug="installer-plan-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
