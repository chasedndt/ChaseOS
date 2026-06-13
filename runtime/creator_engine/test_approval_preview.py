from __future__ import annotations

import json
from pathlib import Path

import pytest

import runtime.cli.main as cli
from runtime.creator_engine.approvals import (
    CreatorApprovalPreviewError,
    build_creator_approval_consumption_dry_run as dry_run_creator_approval_consumption,
    build_creator_approval_request as write_creator_approval_request,
    preview_creator_approval_packets,
)
from runtime.creator_engine.cli import (
    build_creator_approval_consumption_dry_run,
    build_creator_approval_preview,
    build_creator_approval_request,
    build_creator_ingest,
)
from runtime.creator_engine.context_pack import build_context_pack
from runtime.creator_engine.generator import build_generation_artifact_stubs
from runtime.creator_engine.job_store import CreatorJobStore


def _write_transcript(vault_root: Path, name: str = "transcript.md") -> str:
    rel_path = Path("03_INPUTS") / "Transcript-Raw" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Transcript\n\n"
        "Creator Engine approval previews should bind generated artifacts to explicit "
        "operator review before publishing, timeline execution, or memory promotion.\n",
        encoding="utf-8",
    )
    return rel_path.as_posix()


def _write_media(vault_root: Path, name: str = "recording.mp4") -> str:
    rel_path = Path("03_INPUTS") / "Recordings" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"creator-engine-approval-preview-media-fixture\n")
    return rel_path.as_posix()


def _write_context(vault_root: Path, name: str = "creator-engine-context.md") -> str:
    rel_path = Path("docs") / "context" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Creator Engine Context\n\n"
        "Approval previews are read-only and do not grant authority.\n",
        encoding="utf-8",
    )
    return rel_path.as_posix()


def _create_context_ready_job(tmp_path: Path, job_id: str) -> str:
    media_ref = _write_media(tmp_path, f"{job_id}.mp4")
    transcript_ref = _write_transcript(tmp_path, f"{job_id}.md")
    context_ref = _write_context(tmp_path, f"{job_id}.md")
    media_payload = build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id=job_id,
        target_platforms=["youtube"],
        context_prompt="Keep approval review explicit.",
        manual_source_metadata={"source_title": "Creator approval preview fixture"},
    )
    transcript_payload = build_creator_ingest(
        vault_root=tmp_path,
        source="provided-transcript",
        transcript_path=transcript_ref,
        attach_to_job_id=job_id,
        target_platforms=["linkedin"],
    )
    assert media_payload["ok"] is True
    assert transcript_payload["ok"] is True
    build_context_pack(tmp_path, job_id=job_id, context_refs=[context_ref])
    return job_id


def _create_draft_ready_job(tmp_path: Path, job_id: str = "creator-approval-preview") -> str:
    _create_context_ready_job(tmp_path, job_id)
    build_generation_artifact_stubs(tmp_path, job_id=job_id, target_platforms=["x"])
    return job_id


def test_approval_preview_all_scopes_reads_without_writes(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path)

    result = preview_creator_approval_packets(tmp_path, job_id=job_id)
    repeated = preview_creator_approval_packets(tmp_path, job_id=job_id)
    job = json.loads(
        (tmp_path / "runtime" / "creator_engine" / "jobs" / job_id / "job.json").read_text(encoding="utf-8")
    )

    assert result.approval_scope == "all"
    assert len(result.approval_packet_previews) == 3
    assert [packet["approval_scope"] for packet in result.approval_packet_previews] == [
        "memory-card",
        "publish",
        "timeline",
    ]
    assert [packet["approval_digest"] for packet in result.approval_packet_previews] == [
        packet["approval_digest"] for packet in repeated.approval_packet_previews
    ]
    assert result.files_written == []
    assert "runtime/creator_engine/jobs/creator-approval-preview/job.json" in result.files_read
    assert job["status"] == "draft_ready"
    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals").exists()
    for packet in result.approval_packet_previews:
        assert packet["status"] == "preview_only"
        assert packet["operator_approval_required"] is True
        assert packet["approval_artifact_written"] is False
        assert packet["approval_consumed"] is False
        assert packet["execution_allowed"] is False
        assert packet["writes_performed"] is False
        assert len(packet["approval_digest"]) == 64
        assert packet["future_approval_artifact_path"].startswith(
            "07_LOGS/Agent-Activity/_creator_engine_approvals/"
        )
        assert packet["authority_flags"]["approval_artifact_write_allowed"] is False
        assert packet["authority_flags"]["approval_consumption_allowed"] is False
        assert packet["authority_flags"]["direct_publish_allowed"] is False
        assert packet["authority_flags"]["governed_memory_write_allowed"] is False
        assert packet["target_artifacts"]


def test_approval_preview_memory_scope_blocks_canonical_promotion(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-memory")

    result = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="memory-card")
    packet = result.approval_packet_previews[0]

    assert result.approval_scope == "memory-card"
    assert len(result.approval_packet_previews) == 1
    assert packet["target_action"] == "content_memory_card_canonical_promotion"
    assert "canonical_memory_promotion" in packet["blocked_until_approved"]
    assert packet["authority_flags"]["content_memory_card_canonical_promotion_allowed"] is False
    assert any(ref["path"].endswith("memory/content_memory_card.json") for ref in packet["target_artifacts"])
    assert any(path.endswith("memory/content_memory_card.md") for path in result.files_read)


def test_approval_preview_blocks_non_draft_ready_jobs(tmp_path: Path) -> None:
    job_id = _create_context_ready_job(tmp_path, "creator-approval-not-draft")

    with pytest.raises(CreatorApprovalPreviewError, match="draft_ready"):
        preview_creator_approval_packets(tmp_path, job_id=job_id)

    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals").exists()


def test_approval_preview_blocks_missing_generation_manifest(tmp_path: Path) -> None:
    job_id = _create_context_ready_job(tmp_path, "creator-approval-missing-manifest")
    store = CreatorJobStore(tmp_path)
    job = store.load_job(job_id)
    job["status"] = "draft_ready"
    store.save_job(job)

    with pytest.raises(CreatorApprovalPreviewError, match="generation/generation_manifest.json"):
        preview_creator_approval_packets(tmp_path, job_id=job_id)

    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals").exists()


def test_creator_approval_preview_cli_json_envelope(tmp_path: Path, capsys) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-cli")

    exit_code = cli.main(
        [
            "creator",
            "approval-preview",
            "--job-id",
            job_id,
            "--approval-scope",
            "publish",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]
    packet = result["approval_packet_previews"][0]

    assert exit_code == 0
    assert envelope["ok"] is True
    assert envelope["action"] == "creator.approval-preview"
    assert result["status"] == "approval_preview_ready"
    assert result["writes_performed"] is False
    assert result["files_written"] == []
    assert result["approval_scope"] == "publish"
    assert result["approval_packet_count"] == 1
    assert packet["target_action"] == "publish_upload_or_external_delivery"
    assert packet["authority_flags"]["upload_allowed"] is False
    assert packet["approval_artifact_written"] is False
    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals").exists()


def test_build_creator_approval_preview_error_payload_for_missing_job_id(tmp_path: Path) -> None:
    payload = build_creator_approval_preview(vault_root=tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "missing_job_id"
    assert payload["writes_performed"] is False
    assert "--job-id is required" in payload["errors"][0]


def test_approval_request_preview_requires_no_write(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-request-preview")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="publish")
    digest = preview.approval_packet_previews[0]["approval_digest"]

    payload = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="publish",
        expected_approval_digest=digest,
        requested_by="codex-test",
    )

    assert payload["ok"] is True
    assert payload["status"] == "ready_to_write_approval_request"
    assert payload["approval_request_written"] is False
    assert payload["approval_artifact_written"] is False
    assert payload["writes_performed"] is False
    assert payload["files_written"] == []
    assert payload["approval_digest_matched"] is True
    assert payload["approval_artifact_path"].endswith(".json")
    assert payload["approval_artifact_preview"]["approval_request_only"] is True
    assert payload["approval_artifact_preview"]["approval_granted"] is False
    assert payload["approval_artifact_preview"]["approval_consumed"] is False
    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals").exists()


def test_approval_request_writer_persists_pending_artifact_with_exact_digest(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-request-write")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="memory-card")
    digest = preview.approval_packet_previews[0]["approval_digest"]

    payload = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="memory-card",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )
    artifact_path = tmp_path / payload["approval_artifact_path"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    job = json.loads(
        (tmp_path / "runtime" / "creator_engine" / "jobs" / job_id / "job.json").read_text(encoding="utf-8")
    )

    assert payload["ok"] is True
    assert payload["status"] == "approval_request_written"
    assert payload["approval_request_written"] is True
    assert payload["approval_artifact_written"] is True
    assert payload["writes_performed"] is True
    assert payload["files_written"] == [payload["approval_artifact_path"]]
    assert payload["authority_flags"]["approval_artifact_write_allowed"] is True
    assert payload["authority_flags"]["approval_consumption_allowed"] is False
    assert artifact["packet_type"] == "creator_approval_request"
    assert artifact["status"] == "pending_operator_approval"
    assert artifact["approval_request_only"] is True
    assert artifact["approval_granted"] is False
    assert artifact["approval_consumed"] is False
    assert artifact["approval_digest"] == digest
    assert artifact["approval_scope"] == "memory-card"
    assert artifact["requested_action"] == "content_memory_card_canonical_promotion"
    assert artifact["source_approval_preview"]["approval_packet_count"] == 1
    assert job["status"] == "draft_ready"
    assert not (tmp_path / "02_KNOWLEDGE").exists()


def test_approval_request_writer_requires_expected_digest_for_write(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-request-no-digest")

    payload = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="timeline",
        requested_by="codex-test",
        write_approval_request=True,
    )

    assert payload["ok"] is False
    assert payload["approval_request_written"] is False
    assert "expected_approval_digest_required_for_write" in payload["blockers"]
    assert payload["files_written"] == []
    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals").exists()


def test_approval_request_writer_blocks_digest_mismatch_without_write(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-request-mismatch")

    payload = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="publish",
        expected_approval_digest="not-the-current-digest",
        requested_by="codex-test",
        write_approval_request=True,
    )

    assert payload["ok"] is False
    assert payload["approval_request_written"] is False
    assert "expected_approval_digest_mismatch" in payload["blockers"]
    assert payload["files_written"] == []
    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals").exists()


def test_approval_request_writer_blocks_duplicate_without_overwrite(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-request-duplicate")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="publish")
    digest = preview.approval_packet_previews[0]["approval_digest"]

    first = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="publish",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )
    duplicate = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="publish",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )

    assert first["approval_request_written"] is True
    assert duplicate["ok"] is False
    assert duplicate["approval_request_written"] is False
    assert "approval_artifact_already_exists_no_overwrite" in duplicate["blockers"]


def test_creator_write_approval_request_cli_json_envelope(tmp_path: Path, capsys) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-request-cli")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="timeline")
    digest = preview.approval_packet_previews[0]["approval_digest"]

    exit_code = cli.main(
        [
            "creator",
            "write-approval-request",
            "--job-id",
            job_id,
            "--approval-scope",
            "timeline",
            "--expected-approval-digest",
            digest,
            "--requested-by",
            "codex-test",
            "--write-approval-request",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]
    artifact = json.loads((tmp_path / result["approval_artifact_path"]).read_text(encoding="utf-8"))

    assert exit_code == 0
    assert envelope["ok"] is True
    assert envelope["action"] == "creator.write-approval-request"
    assert result["status"] == "approval_request_written"
    assert result["approval_request_written"] is True
    assert result["approval_scope"] == "timeline"
    assert result["approval_digest"] == digest
    assert result["authority_flags"]["approval_consumption_allowed"] is False
    assert artifact["requested_action"] == "timeline_edit_execution"
    assert artifact["approval_consumed"] is False


def test_build_creator_approval_request_error_payload_for_missing_job_id(tmp_path: Path) -> None:
    payload = build_creator_approval_request(vault_root=tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "missing_job_id"
    assert payload["writes_performed"] is False
    assert "--job-id is required" in payload["errors"][0]


def test_approval_consumption_dry_run_validates_pending_request_without_writes(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-consumption-dry-run")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="publish")
    digest = preview.approval_packet_previews[0]["approval_digest"]
    request = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="publish",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )

    payload = dry_run_creator_approval_consumption(
        request["approval_artifact_path"],
        expected_approval_digest=digest,
        vault_root=tmp_path,
    )

    assert payload["ok"] is True
    assert payload["status"] == "blocked_pending_operator_decision"
    assert payload["approval_request_valid_for_decision_boundary"] is True
    assert payload["approval_digest_matched"] is True
    assert payload["current_approval_digest"] == digest
    assert payload["checks"]["current_approval_digest_matches_artifact"] is True
    assert payload["checks"]["future_consumption_marker_absent"] is True
    assert payload["approval_consumption_ready"] is False
    assert payload["approval_consumed"] is False
    assert payload["approval_decision_written"] is False
    assert payload["approval_consumption_marker_written"] is False
    assert payload["timeline_edit_executed"] is False
    assert payload["direct_publish_performed"] is False
    assert payload["files_written"] == []
    assert "operator_approval_decision_required" in payload["blockers"]
    assert payload["authority_flags"]["approval_consumption_allowed"] is False
    assert not (tmp_path / "07_LOGS" / "Agent-Activity" / "_creator_engine_approvals" / "_consumption_markers").exists()


def test_approval_consumption_dry_run_blocks_expected_digest_mismatch(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-consumption-mismatch")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="timeline")
    digest = preview.approval_packet_previews[0]["approval_digest"]
    request = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="timeline",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )

    payload = dry_run_creator_approval_consumption(
        request["approval_artifact_path"],
        expected_approval_digest="not-the-current-digest",
        vault_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["approval_consumption_ready"] is False
    assert payload["files_written"] == []
    assert "expected_approval_digest_mismatch" in payload["blockers"]


def test_approval_consumption_dry_run_blocks_stale_request_digest(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-consumption-stale")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="memory-card")
    digest = preview.approval_packet_previews[0]["approval_digest"]
    request = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="memory-card",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )
    memory_card = (
        tmp_path
        / "runtime"
        / "creator_engine"
        / "jobs"
        / job_id
        / "memory"
        / "content_memory_card.md"
    )
    memory_card.write_text(memory_card.read_text(encoding="utf-8") + "\nStale mutation.\n", encoding="utf-8")

    payload = dry_run_creator_approval_consumption(
        request["approval_artifact_path"],
        expected_approval_digest=digest,
        vault_root=tmp_path,
    )

    assert payload["ok"] is False
    assert payload["approval_digest_matched"] is True
    assert payload["current_approval_digest"] != digest
    assert "current_approval_digest_mismatch" in payload["blockers"]
    assert payload["files_written"] == []


def test_approval_consumption_dry_run_blocks_consumed_artifact(tmp_path: Path) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-consumption-consumed")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="publish")
    digest = preview.approval_packet_previews[0]["approval_digest"]
    request = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="publish",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )
    artifact_path = tmp_path / request["approval_artifact_path"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["approval_consumed"] = True
    artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = dry_run_creator_approval_consumption(
        request["approval_artifact_path"],
        expected_approval_digest=digest,
        vault_root=tmp_path,
    )

    assert payload["ok"] is False
    assert "approval_artifact_already_consumed_or_ambiguous" in payload["blockers"]
    assert payload["approval_consumed"] is False
    assert payload["files_written"] == []


def test_creator_approval_consumption_dry_run_cli_json_envelope(tmp_path: Path, capsys) -> None:
    job_id = _create_draft_ready_job(tmp_path, "creator-approval-consumption-cli")
    preview = preview_creator_approval_packets(tmp_path, job_id=job_id, approval_scope="timeline")
    digest = preview.approval_packet_previews[0]["approval_digest"]
    request = write_creator_approval_request(
        tmp_path,
        job_id=job_id,
        approval_scope="timeline",
        expected_approval_digest=digest,
        requested_by="codex-test",
        write_approval_request=True,
    )

    exit_code = cli.main(
        [
            "creator",
            "approval-consumption-dry-run",
            "--approval-artifact-path",
            request["approval_artifact_path"],
            "--expected-approval-digest",
            digest,
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]

    assert exit_code == 0
    assert envelope["ok"] is True
    assert envelope["action"] == "creator.approval-consumption-dry-run"
    assert result["status"] == "blocked_pending_operator_decision"
    assert result["approval_scope"] == "timeline"
    assert result["approval_digest"] == digest
    assert result["approval_consumption_ready"] is False
    assert result["files_written"] == []


def test_build_creator_approval_consumption_dry_run_error_payload_for_missing_artifact_path(
    tmp_path: Path,
) -> None:
    payload = build_creator_approval_consumption_dry_run(vault_root=tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "missing_approval_artifact_path"
    assert payload["writes_performed"] is False
    assert "--approval-artifact-path is required" in payload["errors"][0]
