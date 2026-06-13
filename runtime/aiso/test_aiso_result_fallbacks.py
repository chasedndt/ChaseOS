from __future__ import annotations

import os
from pathlib import Path

from runtime.aiso.dry_run_contract import run_aiso_submission_dry_run


def _touch(path: Path, *, mtime: int, content: bytes = b"video") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    os.utime(path, (mtime, mtime))


def test_dry_run_result_fallbacks_include_local_email_and_portal_previews(tmp_path: Path) -> None:
    vault = tmp_path
    _touch(vault / "03_INPUTS" / "00_QUARANTINE" / "assignment.mov", mtime=1_800_000_000)

    result = run_aiso_submission_dry_run(
        vault_root=vault,
        request_text="Prepare the video submission email and portal upload draft, but do not send it.",
        declared_roots=["03_INPUTS/00_QUARANTINE"],
        proof_root="07_LOGS/Workflow-Proofs/aiso-fallbacks",
        now="2026-06-12T17:00:00Z",
    )

    fallbacks = result["result_fallbacks"]
    assert [item["id"] for item in fallbacks] == [
        "local_proof_packet",
        "email_draft_preview",
        "browser_portal_draft_preview",
    ]
    assert fallbacks[0]["status"] == "available"
    assert fallbacks[0]["selected"] is True
    assert fallbacks[1]["status"] == "preview_created_no_send"
    assert fallbacks[1]["email_send_performed"] is False
    assert fallbacks[1]["credential_access_performed"] is False
    assert fallbacks[1]["blocked_reason"] == "email_adapter_and_credentials_not_authorized"
    assert fallbacks[1]["attachment_plan"]["staged_package_path"].endswith(".zip")
    assert (vault / fallbacks[1]["preview_path"]).is_file()
    assert fallbacks[1]["visual_screenshot_path"].endswith("aiso-email-draft-preview.png")
    assert (vault / fallbacks[1]["visual_screenshot_path"]).is_file()
    assert (vault / fallbacks[1]["visual_screenshot_path"]).read_bytes().startswith(b"\x89PNG")
    assert fallbacks[2]["status"] == "preview_created_no_submit"
    assert fallbacks[2]["browser_opened"] is False
    assert fallbacks[2]["browser_submit_performed"] is False
    assert fallbacks[2]["blocked_reason"] == "browser_session_and_portal_submission_not_authorized"
    assert (vault / fallbacks[2]["preview_path"]).is_file()
    assert fallbacks[2]["visual_screenshot_path"].endswith("aiso-portal-draft-preview.png")
    assert (vault / fallbacks[2]["visual_screenshot_path"]).is_file()
    assert (vault / fallbacks[2]["visual_screenshot_path"]).read_bytes().startswith(b"\x89PNG")
    assert result["proof_packet"]["visual_preview_path"] == fallbacks[0]["preview_path"]
    assert result["proof_packet"]["visual_image_path"] == fallbacks[0]["visual_image_path"]


def test_dry_run_audit_envelope_records_visual_proof_and_test_commands(tmp_path: Path) -> None:
    vault = tmp_path
    _touch(vault / "03_INPUTS" / "00_QUARANTINE" / "lecture.webm", mtime=1_800_000_000)

    result = run_aiso_submission_dry_run(
        vault_root=vault,
        request_text="Make a submission package for my lecture recording.",
        declared_roots=["03_INPUTS/00_QUARANTINE"],
        proof_root="07_LOGS/Workflow-Proofs/aiso-audit",
        now="2026-06-12T18:00:00Z",
    )

    audit = result["audit_envelope"]
    assert audit["authority"]["original_mutation_performed"] is False
    assert audit["authority"]["provider_call_performed"] is False
    assert audit["authority"]["browser_submit_performed"] is False
    assert audit["authority"]["email_send_performed"] is False
    assert audit["authority"]["credential_access_performed"] is False
    assert audit["authority"]["canonical_promotion_performed"] is False
    assert audit["test_commands"] == [
        "PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_recent_artifact_locator.py -q",
        "PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_aiso_dry_run_contract.py -q",
        "PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_aiso_result_fallbacks.py -q",
    ]
    assert audit["visual_proof_artifacts"]["proof_packet_html"].endswith("aiso-proof-preview.html")
    assert audit["visual_proof_artifacts"]["proof_packet_svg"].endswith("aiso-proof-preview.svg")
    assert audit["visual_proof_artifacts"]["proof_packet_png"].endswith("aiso-proof-preview.png")
    assert audit["visual_proof_artifacts"]["email_preview_png"].endswith("aiso-email-draft-preview.png")
    assert audit["visual_proof_artifacts"]["portal_preview_png"].endswith("aiso-portal-draft-preview.png")
    assert (vault / audit["visual_proof_artifacts"]["email_preview_png"]).is_file()
    assert (vault / audit["visual_proof_artifacts"]["portal_preview_png"]).is_file()
    assert audit["source_fixture_ids"] == ["runtime/aiso/test_aiso_result_fallbacks.py"]
