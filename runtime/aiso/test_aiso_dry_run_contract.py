from __future__ import annotations

import json
import os
from pathlib import Path

from runtime.aiso.dry_run_contract import run_aiso_submission_dry_run


def _touch(path: Path, *, mtime: int, content: bytes = b"video") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    os.utime(path, (mtime, mtime))


def test_university_submission_dry_run_builds_local_proof_without_live_authority(tmp_path: Path) -> None:
    vault = tmp_path
    candidate = vault / "03_INPUTS" / "00_QUARANTINE" / "captures" / "raw class video.mp4"
    _touch(candidate, mtime=1_800_000_000, content=b"not real media but fixture bytes")
    before = candidate.read_bytes()

    result = run_aiso_submission_dry_run(
        vault_root=vault,
        request_text="Find the university video I recorded last night, rename it properly, zip it, and prepare the Outlook email for submission.",
        declared_roots=["03_INPUTS/00_QUARANTINE"],
        proof_root="07_LOGS/Workflow-Proofs/aiso-test-proof",
        now="2026-06-12T16:00:00Z",
    )

    assert result["ok"] is True
    assert result["workflow"]["workflow_id"] == "university_submission_operator"
    assert result["workflow"]["task_type"] == "university_submission_prepare"
    assert result["workflow"]["mode"] == "prepare_and_stage"
    assert result["workflow"]["media_derived_text_is_instruction"] is False
    assert result["selected_candidate"]["relative_path"] == "03_INPUTS/00_QUARANTINE/captures/raw class video.mp4"
    assert result["metadata_stub"]["provider_call_performed"] is False
    assert result["metadata_stub"]["transcript"]["status"] == "unavailable_without_provider_or_local_transcriber"
    assert result["rename_package_proposal"]["original_mutation_performed"] is False
    assert result["rename_package_proposal"]["staged_filename"].endswith("university-submission-2026-06-12.mp4")
    rename_approval = result["rename_package_proposal"]["approval_message"]
    assert rename_approval["action"] == "rename_original_file"
    assert rename_approval["requires_operator_approval"] is True
    assert rename_approval["old_filename"] == "raw class video.mp4"
    assert rename_approval["new_filename"] == "university-submission-2026-06-12.mp4"
    assert "raw class video.mp4" in rename_approval["message"]
    assert "university-submission-2026-06-12.mp4" in rename_approval["message"]
    assert result["approval_blocking"]["rename_original_file"]["old_filename"] == "raw class video.mp4"
    assert result["approval_blocking"]["rename_original_file"]["new_filename"] == "university-submission-2026-06-12.mp4"
    assert result["approval_blocking"]["rename_original_file"]["blocked_before_original_side_effects"] is True
    assert result["authority"]["write_performed"] is True
    assert result["authority"]["original_mutation_performed"] is False
    assert result["authority"]["provider_call_performed"] is False
    assert result["authority"]["browser_submit_performed"] is False
    assert result["authority"]["email_send_performed"] is False
    assert result["authority"]["credential_access_performed"] is False
    assert result["authority"]["canonical_promotion_performed"] is False
    assert result["approval_blocking"]["send_or_submit"]["status"] == "approval_required"
    assert result["proof_packet"]["status"] == "created"
    assert result["proof_packet"]["visual_preview_path"].endswith("aiso-proof-preview.html")
    assert result["proof_packet"]["visual_image_path"].endswith("aiso-proof-preview.svg")
    assert result["proof_packet"]["visual_screenshot_path"].endswith("aiso-proof-preview.png")
    assert (vault / result["proof_packet"]["manifest_path"]).is_file()
    assert (vault / result["proof_packet"]["audit_envelope_path"]).is_file()
    assert (vault / result["proof_packet"]["visual_preview_path"]).is_file()
    assert (vault / result["proof_packet"]["visual_image_path"]).is_file()
    assert (vault / result["proof_packet"]["visual_screenshot_path"]).is_file()
    assert candidate.read_bytes() == before

    audit = json.loads((vault / result["proof_packet"]["audit_envelope_path"]).read_text(encoding="utf-8"))
    assert audit["selected_fallback_path"] == "local_proof_packet"
    assert "email_send" in audit["blocked_live_paths"]
    assert "browser_portal_submit" in audit["blocked_live_paths"]


def test_dry_run_blocks_when_no_declared_candidate_is_available(tmp_path: Path) -> None:
    result = run_aiso_submission_dry_run(
        vault_root=tmp_path,
        request_text="Submit my class video",
        declared_roots=["missing", ".env", str(tmp_path.parent / "outside")],
        proof_root="07_LOGS/Workflow-Proofs/aiso-empty-proof",
        now="2026-06-12T16:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == "blocked_no_candidate"
    assert result["authority"]["write_performed"] is False
    assert {item["reason"] for item in result["locator"]["blocked_roots"]} >= {
        "root_missing",
        "credential_or_browser_profile_root_blocked",
        "root_outside_vault",
    }
