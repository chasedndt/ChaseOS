from __future__ import annotations

import json
from pathlib import Path

import pytest

import runtime.cli.main as cli
from runtime.creator_engine.cli import build_creator_context_pack, build_creator_ingest
from runtime.creator_engine.context_pack import ContextPackError, build_context_pack, preview_context_pack


def _write_transcript(vault_root: Path, name: str = "transcript.md") -> str:
    rel_path = Path("03_INPUTS") / "Transcript-Raw" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Transcript\n\nWe shipped the Creator Engine media and transcript link. "
        "Now build a context pack for a ChaseInTech walkthrough.\n",
        encoding="utf-8",
    )
    return rel_path.as_posix()


def _write_media(vault_root: Path, name: str = "recording.mp4") -> str:
    rel_path = Path("03_INPUTS") / "Recordings" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True)
    path.write_bytes(b"creator-engine-context-pack-media-fixture\n")
    return rel_path.as_posix()


def _write_context(vault_root: Path, name: str = "creator-engine-note.md") -> str:
    rel_path = Path("docs") / "context" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Creator Engine Note\n\n"
        "The next package should be review-first, runtime-local, and blocked from publishing.\n",
        encoding="utf-8",
    )
    return rel_path.as_posix()


def _create_transcript_ready_media_job(tmp_path: Path, job_id: str = "creator-context-pack-test") -> tuple[str, str, str]:
    media_ref = _write_media(tmp_path)
    transcript_ref = _write_transcript(tmp_path)
    media_payload = build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id=job_id,
        target_platforms=["youtube"],
        context_prompt="Use the builder persona and keep the output review-first.",
    )
    transcript_payload = build_creator_ingest(
        vault_root=tmp_path,
        source="provided-transcript",
        transcript_path=transcript_ref,
        attach_to_job_id=job_id,
    )
    assert media_payload["ok"] is True
    assert transcript_payload["ok"] is True
    return job_id, media_ref, transcript_ref


def test_build_context_pack_writes_runtime_local_json_and_markdown(tmp_path: Path) -> None:
    job_id, media_ref, _ = _create_transcript_ready_media_job(tmp_path)
    context_ref = _write_context(tmp_path)

    result = build_context_pack(tmp_path, job_id=job_id, context_refs=[context_ref])

    job_root = tmp_path / "runtime" / "creator_engine" / "jobs" / job_id
    context_pack_path = job_root / "context" / "context_pack.json"
    context_markdown_path = job_root / "context" / "context_pack.md"
    pack = json.loads(context_pack_path.read_text(encoding="utf-8"))

    assert result.job["status"] == "context_ready"
    assert result.context_pack["artifact_type"] == "context_pack"
    assert result.context_pack["status"] == "draft"
    assert result.context_pack["source_recording"]["path"] == media_ref
    assert result.context_pack["transcript"]["source_ref"].endswith("transcripts/transcript.raw.md")
    assert result.context_pack["declared_context_refs"] == [context_ref]
    assert result.context_pack["operator_context_prompt"]["source_ref"] == "operator_context_prompt"
    assert result.context_pack["authority_flags"]["provider_call_allowed"] is False
    assert result.context_pack["authority_flags"]["canonical_writeback_allowed"] is False
    assert result.context_pack["trust_summary"]["source_intelligence_query_performed"] is False
    assert result.context_pack["trust_summary"]["canonical_writeback_performed"] is False
    assert context_pack_path.exists()
    assert context_markdown_path.exists()
    assert pack["input_digest"] == result.context_pack["input_digest"]
    assert any(path.endswith("transcripts/transcript.raw.md") for path in result.files_read)
    assert all(path.startswith("runtime/creator_engine/jobs/") for path in result.files_written)
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_preview_context_pack_reads_without_writes(tmp_path: Path) -> None:
    job_id, _, _ = _create_transcript_ready_media_job(tmp_path, "creator-context-pack-preview")
    context_ref = _write_context(tmp_path, "preview.md")

    preview = preview_context_pack(tmp_path, job_id=job_id, context_refs=[context_ref])

    job_root = tmp_path / "runtime" / "creator_engine" / "jobs" / job_id
    loaded_job = json.loads((job_root / "job.json").read_text(encoding="utf-8"))

    assert preview.job_status == "transcript_ready"
    assert preview.files_would_write
    assert preview.files_read[-1] == context_ref
    assert preview.context_items[0]["source_ref"] == context_ref
    assert loaded_job["status"] == "transcript_ready"
    assert not (job_root / "context").exists()


def test_context_pack_blocks_jobs_without_transcript(tmp_path: Path) -> None:
    media_ref = _write_media(tmp_path, "no-transcript.mp4")
    build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id="creator-context-pack-no-transcript",
    )

    with pytest.raises(ContextPackError, match="transcript_ready"):
        build_context_pack(tmp_path, job_id="creator-context-pack-no-transcript")

    assert not (
        tmp_path
        / "runtime"
        / "creator_engine"
        / "jobs"
        / "creator-context-pack-no-transcript"
        / "context"
    ).exists()


def test_context_pack_blocks_secret_context_refs(tmp_path: Path) -> None:
    job_id, _, _ = _create_transcript_ready_media_job(tmp_path, "creator-context-pack-secret")
    secret_ref = Path("secrets") / "context.md"
    secret_path = tmp_path / secret_ref
    secret_path.parent.mkdir(parents=True)
    secret_path.write_text("do not read me\n", encoding="utf-8")

    with pytest.raises(ContextPackError, match="forbidden secrets boundary"):
        build_context_pack(tmp_path, job_id=job_id, context_refs=[secret_ref.as_posix()])

    assert not (tmp_path / "runtime" / "creator_engine" / "jobs" / job_id / "context").exists()


def test_context_pack_blocks_duplicate_context_artifacts(tmp_path: Path) -> None:
    job_id, _, _ = _create_transcript_ready_media_job(tmp_path, "creator-context-pack-duplicate")
    build_context_pack(tmp_path, job_id=job_id)

    with pytest.raises(ContextPackError, match="already has context pack"):
        build_context_pack(tmp_path, job_id=job_id)


def test_creator_context_pack_cli_json_envelope(tmp_path: Path, capsys) -> None:
    job_id, _, _ = _create_transcript_ready_media_job(tmp_path, "creator-context-pack-cli")
    context_ref = _write_context(tmp_path, "cli.md")

    exit_code = cli.main(
        [
            "creator",
            "context-pack",
            "--job-id",
            job_id,
            "--context-ref",
            context_ref,
            "--context",
            "Frame this as a ChaseInTech build-log walkthrough.",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]

    assert exit_code == 0
    assert envelope["ok"] is True
    assert envelope["action"] == "creator.context-pack"
    assert result["status"] == "context_ready"
    assert result["writes_performed"] is True
    assert result["job"]["status"] == "context_ready"
    assert result["context_pack"]["declared_context_refs"] == [context_ref]
    assert result["context_pack"]["authority_flags"]["generation_allowed"] is False
    assert result["context_pack"]["authority_flags"]["provider_call_allowed"] is False


def test_creator_context_pack_dry_run_cli_reads_without_writes(tmp_path: Path, capsys) -> None:
    job_id, _, _ = _create_transcript_ready_media_job(tmp_path, "creator-context-pack-cli-dry-run")
    context_ref = _write_context(tmp_path, "cli-dry-run.md")

    exit_code = cli.main(
        [
            "creator",
            "context-pack",
            "--job-id",
            job_id,
            "--context-ref",
            context_ref,
            "--vault-root",
            str(tmp_path),
            "--dry-run",
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]
    job_root = tmp_path / "runtime" / "creator_engine" / "jobs" / job_id

    assert exit_code == 0
    assert envelope["action"] == "creator.context-pack"
    assert result["status"] == "dry_run_ready"
    assert result["writes_performed"] is False
    assert result["files_written"] == []
    assert result["files_would_write"]
    assert result["preview"]["context_items"][0]["source_ref"] == context_ref
    assert not (job_root / "context").exists()


def test_build_creator_context_pack_error_payload_for_missing_job_id(tmp_path: Path) -> None:
    payload = build_creator_context_pack(vault_root=tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "missing_job_id"
    assert payload["writes_performed"] is False
    assert "--job-id is required" in payload["errors"][0]
