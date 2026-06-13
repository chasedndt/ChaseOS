from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

from runtime.aiso.closeout_readiness import build_aiso_real_test_closeout_readiness
from runtime.aiso.dry_run_contract import run_aiso_submission_dry_run
from runtime.studio.aiso_rename_review_panel import apply_aiso_package_approval, apply_aiso_rename_approval


def _touch(path: Path, *, mtime: int, content: bytes = b"video") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    os.utime(path, (mtime, mtime))


def test_aiso_real_test_closeout_readiness_blocks_until_dry_run_and_package_proofs_exist(tmp_path: Path) -> None:
    readiness = build_aiso_real_test_closeout_readiness(tmp_path)

    assert readiness["ok"] is False
    assert readiness["ready_for_real_test_closeout"] is False
    assert readiness["remaining_development_passes"] == [
        "visual dry-run proof packet with email/portal screenshot artifacts",
        "approval-consumed rename plus package/zip proof",
    ]
    assert readiness["authority"]["read_only_status"] is True
    assert readiness["authority"]["package_write_performed"] is False


def test_aiso_real_test_closeout_readiness_passes_after_visual_dry_run_and_safe_zip_smoke(tmp_path: Path) -> None:
    vault = tmp_path
    source = vault / "03_INPUTS" / "00_QUARANTINE" / "raw class video.mp4"
    _touch(source, mtime=1_800_000_000, content=b"real-test-closeout-fixture")

    dry_run = run_aiso_submission_dry_run(
        vault_root=vault,
        request_text="Find the university video I recorded last night, rename it properly, zip it, and prepare the Outlook email for submission.",
        declared_roots=["03_INPUTS/00_QUARANTINE"],
        proof_root="07_LOGS/Workflow-Proofs/aiso-visual-proof",
        now="2026-06-13T12:00:00Z",
    )
    assert dry_run["ok"] is True

    manifest_path = vault / dry_run["proof_packet"]["manifest_path"]
    proof_dir = vault / "07_LOGS" / "Workflow-Proofs" / "aiso-rename-package-proof"
    proof_dir.mkdir(parents=True)
    package_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package_manifest["rename_package_proposal"]["approval_message"]["old_path"] = "03_INPUTS/00_QUARANTINE/raw class video.mp4"
    package_manifest["rename_package_proposal"]["approval_message"]["new_path"] = "03_INPUTS/00_QUARANTINE/university-submission-2026-06-13.mp4"
    package_manifest["rename_package_proposal"]["approval_message"]["old_filename"] = "raw class video.mp4"
    package_manifest["rename_package_proposal"]["approval_message"]["new_filename"] = "university-submission-2026-06-13.mp4"
    package_manifest["rename_package_proposal"]["staged_filename"] = "university-submission-2026-06-13.mp4"
    (proof_dir / "aiso-proof-manifest.json").write_text(json.dumps(package_manifest), encoding="utf-8")

    rename = apply_aiso_rename_approval(
        vault,
        proposal_id="aiso-rename-package-proof",
        approval_confirmed=True,
        expected_old_filename="raw class video.mp4",
        expected_new_filename="university-submission-2026-06-13.mp4",
        operator_id="test-operator",
    )
    assert rename["ok"] is True
    package = apply_aiso_package_approval(
        vault,
        proposal_id="aiso-rename-package-proof",
        approval_confirmed=True,
        expected_media_filename="university-submission-2026-06-13.mp4",
        operator_id="test-operator",
    )
    assert package["ok"] is True
    with zipfile.ZipFile(vault / package["package_path"]) as archive:
        assert archive.namelist() == ["university-submission-2026-06-13.mp4"]

    readiness = build_aiso_real_test_closeout_readiness(vault)

    assert readiness["ok"] is True
    assert readiness["ready_for_real_test_closeout"] is True
    assert readiness["remaining_development_passes"] == []
    assert readiness["remaining_closeout_only"] == [
        "Run one operator-declared safe-root real media test: candidate selection, explicit rename approval, explicit package approval, zip verification, and proof record review."
    ]
    assert readiness["evidence"]["dry_run_visual_proof"]["visual_artifacts"]["email_preview_png"].endswith("aiso-email-draft-preview.png")
    assert readiness["evidence"]["dry_run_visual_proof"]["visual_artifacts"]["portal_preview_png"].endswith("aiso-portal-draft-preview.png")
    assert readiness["evidence"]["rename_package_proof"]["package_path"].endswith(".zip")
    assert readiness["authority"]["original_mutation_performed"] is False
    assert readiness["authority"]["email_send_performed"] is False
    assert readiness["authority"]["browser_submit_performed"] is False
