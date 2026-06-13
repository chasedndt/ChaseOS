from __future__ import annotations

from pathlib import Path

from runtime.studio.capture_markdown_source_shape_matrix_proof import (
    build_capture_markdown_source_shape_matrix_proof,
)
from runtime.studio.capture_to_markdown_panel import build_capture_to_markdown_panel


def test_source_shape_matrix_proof_runs_in_disposable_scratch_vault(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch-source-shape"

    report = build_capture_markdown_source_shape_matrix_proof(
        tmp_path,
        scratch_root=scratch,
        write_evidence=False,
    )

    assert report["ok"] is True
    assert report["status"] == "capture_markdown_source_shape_matrix_verified"
    assert report["writes_performed"] is False
    assert report["summary"]["case_count"] == 10
    assert report["summary"]["passed_case_count"] == 10
    assert report["summary"]["long_source_text_verified"] is True
    assert report["summary"]["table_code_text_verified"] is True
    assert report["summary"]["local_markdown_file_verified"] is True
    assert report["summary"]["saved_html_file_verified"] is True
    assert report["summary"]["controlled_browser_artifact_verified"] is True
    assert report["summary"]["secret_like_save_block_verified"] is True
    assert report["summary"]["needs_redaction_downstream_block_verified"] is True
    assert report["summary"]["duplicate_save_block_verified"] is True
    assert report["summary"]["scratch_workspace_removed"] is True
    assert scratch.exists() is False
    assert report["forbidden_downstream_writes"] == []
    assert report["authority"]["reads_personal_browser_state"] is False
    assert report["authority"]["reads_clipboard"] is False
    assert report["authority"]["captures_screen_pixels"] is False
    assert report["authority"]["writes_selected_vault"] is False


def test_source_shape_matrix_evidence_marks_capture_release_readiness(tmp_path: Path) -> None:
    report = build_capture_markdown_source_shape_matrix_proof(
        tmp_path,
        evidence_slug="2026-05-28-capture-markdown-source-shape-matrix-test",
        write_evidence=True,
    )

    assert report["ok"] is True
    assert report["writes_performed"] is True
    assert (tmp_path / report["evidence"]["json_path"]).is_file()
    assert (tmp_path / report["evidence"]["markdown_path"]).is_file()

    panel = build_capture_to_markdown_panel(tmp_path)
    release_readiness = panel["release_readiness"]
    assert release_readiness["summary"]["capture_source_shape_matrix_verified"] is True
    assert release_readiness["summary"]["capture_source_shape_matrix_report"] == report["evidence"]["json_path"]
    release_group = next(
        group for group in release_readiness["groups"] if group["id"] == "release_proof_open"
    )
    source_shape = next(
        item for item in release_group["items"] if item["id"] == "broader_real_source_matrix"
    )
    assert source_shape["label"] == "Broader source-shape matrix"
    assert source_shape["status"] == "verified"
    assert source_shape["latest_report"] == report["evidence"]["json_path"]


def test_source_shape_matrix_cases_prove_review_and_duplicate_blocking(tmp_path: Path) -> None:
    report = build_capture_markdown_source_shape_matrix_proof(tmp_path)
    cases = {case["id"]: case for case in report["cases"]}

    needs_redaction = cases["needs_redaction_review_blocks_downstream"]
    assert needs_redaction["checks"]["review_marks_needs_redaction"] is True
    assert needs_redaction["checks"]["source_pack_preview_blocked"] is True
    assert needs_redaction["checks"]["source_pack_write_not_performed"] is True
    assert needs_redaction["source_pack_approval_preview"]["ok"] is False

    duplicate = cases["duplicate_save_blocks_second_write"]
    assert duplicate["checks"]["second_is_duplicate"] is True
    assert duplicate["checks"]["second_write_blocked"] is True
    assert duplicate["checks"]["no_second_quarantine_file"] is True
