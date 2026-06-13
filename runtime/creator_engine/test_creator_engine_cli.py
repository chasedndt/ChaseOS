from __future__ import annotations

import json
from pathlib import Path

import runtime.cli.main as cli
from runtime.creator_engine.cli import build_creator_ingest


def _write_transcript(vault_root: Path, name: str = "example.md") -> str:
    rel_path = Path("03_INPUTS") / "Transcript-Raw" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Raw Transcript\n\nCreator Engine CLI should import this provided transcript.\n",
        encoding="utf-8",
    )
    return rel_path.as_posix()


def _write_media(vault_root: Path, name: str = "example.mp4") -> str:
    rel_path = Path("03_INPUTS") / "Recordings" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True)
    path.write_bytes(b"creator-engine-media-reference-fixture\n")
    return rel_path.as_posix()


def test_build_creator_ingest_imports_provided_transcript_only(tmp_path: Path) -> None:
    transcript_ref = _write_transcript(tmp_path)

    payload = build_creator_ingest(
        vault_root=tmp_path,
        transcript_path=transcript_ref,
        job_id="creator-cli-test",
        target_platforms=["youtube"],
        context_prompt="make a short-form edit plan later",
    )

    assert payload["ok"] is True
    assert payload["status"] == "transcript_ready"
    assert payload["command"] == "creator.ingest"
    assert payload["source"] == "provided_transcript"
    assert payload["job_id"] == "creator-cli-test"
    assert payload["job"]["inputs"]["transcription_backend"] == "not_used_provided_transcript"
    assert payload["job"]["inputs"]["copied_media"] is False
    assert payload["job"]["target_platforms"] == ["youtube"]
    assert payload["authority_flags"]["runtime_local_write_allowed"] is True
    assert payload["authority_flags"]["transcription_backend_allowed"] is False
    assert payload["authority_flags"]["canonical_writeback_allowed"] is False
    assert payload["files_read"] == [transcript_ref]
    assert all(path.startswith("runtime/creator_engine/jobs/") for path in payload["files_written"])
    assert (tmp_path / "runtime" / "creator_engine" / "jobs" / "creator-cli-test" / "job.json").exists()
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()
    assert not (tmp_path / "00_HOME").exists()


def test_creator_ingest_cli_json_envelope(tmp_path: Path, capsys) -> None:
    transcript_ref = _write_transcript(tmp_path, "cli.md")

    exit_code = cli.main(
        [
            "creator",
            "ingest",
            "--source",
            "provided-transcript",
            "--transcript",
            transcript_ref,
            "--job-id",
            "creator-cli-json-test",
            "--target",
            "tiktok",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]

    assert exit_code == 0
    assert envelope["ok"] is True
    assert envelope["action"] == "creator.ingest"
    assert envelope["errors"] == []
    assert result["status"] == "transcript_ready"
    assert result["job_id"] == "creator-cli-json-test"
    assert result["files_read"] == [transcript_ref]
    assert result["job"]["target_platforms"] == ["tiktok"]
    assert result["authority_flags"]["direct_publish_allowed"] is False
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_creator_ingest_dry_run_reads_fixture_without_writes(tmp_path: Path, capsys) -> None:
    transcript_ref = _write_transcript(tmp_path, "dry-run.md")

    exit_code = cli.main(
        [
            "creator",
            "ingest",
            "--source",
            "provided-transcript",
            "--transcript",
            transcript_ref,
            "--target",
            "linkedin",
            "--source-title",
            "Fixture walkthrough",
            "--source-origin",
            "operator-declared",
            "--source-kind",
            "screen-demo",
            "--recorded-at",
            "2026-05-20",
            "--source-note",
            "No media file was copied.",
            "--vault-root",
            str(tmp_path),
            "--dry-run",
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]
    preview = result["preview"]

    assert exit_code == 0
    assert envelope["action"] == "creator.ingest"
    assert result["status"] == "dry_run_ready"
    assert result["dry_run"] is True
    assert result["writes_performed"] is False
    assert result["files_written"] == []
    assert result["authority_flags"]["runtime_local_write_allowed"] is False
    assert result["files_read"] == [transcript_ref]
    assert preview["word_count"] > 0
    assert preview["target_platforms"] == ["linkedin"]
    assert preview["manual_source_metadata"]["source_title"] == "Fixture walkthrough"
    assert preview["manual_source_metadata"]["source_notes"] == ["No media file was copied."]
    assert not (tmp_path / "runtime" / "creator_engine" / "jobs").exists()
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_creator_ingest_records_manual_source_metadata_in_runtime_job(tmp_path: Path) -> None:
    transcript_ref = _write_transcript(tmp_path, "metadata.md")

    payload = build_creator_ingest(
        vault_root=tmp_path,
        transcript_path=transcript_ref,
        job_id="creator-cli-metadata-test",
        manual_source_metadata={
            "source_title": "Metadata fixture",
            "source_origin": "operator note",
            "source_kind": "screen-demo",
            "recorded_at": "2026-05-20",
            "source_notes": ["trim silence later"],
        },
    )

    source_recording_path = (
        tmp_path
        / "runtime"
        / "creator_engine"
        / "jobs"
        / "creator-cli-metadata-test"
        / "source_recording.json"
    )
    source_recording = json.loads(source_recording_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["manual_source_metadata"]["source_title"] == "Metadata fixture"
    assert payload["job"]["inputs"]["manual_source_metadata"]["source_notes"] == ["trim silence later"]
    assert source_recording["adapter_metadata"]["manual_source_metadata"]["source_origin"] == "operator note"
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_creator_ingest_manual_file_dry_run_reads_media_without_writes(tmp_path: Path, capsys) -> None:
    media_ref = _write_media(tmp_path, "dry-run.mp4")

    exit_code = cli.main(
        [
            "creator",
            "ingest",
            "--source",
            "manual-file",
            "--media",
            media_ref,
            "--target",
            "youtube",
            "--source-title",
            "Manual media fixture",
            "--source-origin",
            "operator-declared",
            "--source-kind",
            "screen-demo",
            "--vault-root",
            str(tmp_path),
            "--dry-run",
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]
    preview = result["preview"]

    assert exit_code == 0
    assert envelope["action"] == "creator.ingest"
    assert result["status"] == "dry_run_ready"
    assert result["source"] == "manual_file"
    assert result["dry_run"] is True
    assert result["writes_performed"] is False
    assert result["files_written"] == []
    assert result["files_read"] == [media_ref]
    assert result["authority_flags"]["runtime_local_write_allowed"] is False
    assert result["authority_flags"]["media_copy_allowed"] is False
    assert result["authority_flags"]["ffmpeg_probe_allowed"] is False
    assert preview["media_kind"] == "video"
    assert preview["probe_status"] == "not_probed"
    assert preview["copied_media"] is False
    assert len(preview["file_sha256"]) == 64
    assert preview["manual_source_metadata"]["source_title"] == "Manual media fixture"
    assert not (tmp_path / "runtime" / "creator_engine" / "jobs").exists()
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_creator_ingest_manual_file_records_runtime_source_reference_only(tmp_path: Path) -> None:
    media_ref = _write_media(tmp_path, "source.mov")

    payload = build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id="creator-manual-media-test",
        manual_source_metadata={
            "source_title": "Manual media source",
            "source_origin": "operator-selected-file",
            "source_kind": "recording",
        },
    )

    source_recording_path = (
        tmp_path
        / "runtime"
        / "creator_engine"
        / "jobs"
        / "creator-manual-media-test"
        / "source_recording.json"
    )
    source_recording = json.loads(source_recording_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["status"] == "intake_ready"
    assert payload["source"] == "manual_file"
    assert payload["job"]["source_adapter"] == "manual_file"
    assert payload["job"]["inputs"]["manual_media_path"] == media_ref
    assert payload["job"]["inputs"]["media_reference_only"] is True
    assert payload["job"]["inputs"]["copied_media"] is False
    assert payload["job"]["inputs"]["ffmpeg_probe_performed"] is False
    assert payload["job"]["inputs"]["transcription_backend"] == "not_used_media_reference_only"
    assert source_recording["adapter"] == "manual_file"
    assert source_recording["media_kind"] == "video"
    assert source_recording["path"] == media_ref
    assert source_recording["probe_status"] == "not_probed"
    assert source_recording["adapter_metadata"]["copied_media"] is False
    assert source_recording["adapter_metadata"]["ffmpeg_probe_performed"] is False
    assert source_recording["adapter_metadata"]["manual_source_metadata"]["source_origin"] == "operator-selected-file"
    assert all(path.startswith("runtime/creator_engine/jobs/") for path in payload["files_written"])
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_creator_ingest_attach_transcript_to_manual_media_job(tmp_path: Path) -> None:
    media_ref = _write_media(tmp_path, "linked.mp4")
    transcript_ref = _write_transcript(tmp_path, "linked.md")

    media_payload = build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id="creator-linked-job",
        target_platforms=["youtube"],
    )
    source_recording_path = (
        tmp_path
        / "runtime"
        / "creator_engine"
        / "jobs"
        / "creator-linked-job"
        / "source_recording.json"
    )
    source_recording_before = json.loads(source_recording_path.read_text(encoding="utf-8"))

    payload = build_creator_ingest(
        vault_root=tmp_path,
        source="provided-transcript",
        transcript_path=transcript_ref,
        attach_to_job_id="creator-linked-job",
        target_platforms=["linkedin"],
        manual_source_metadata={"source_title": "Linked transcript"},
    )

    source_recording_after = json.loads(source_recording_path.read_text(encoding="utf-8"))

    assert media_payload["ok"] is True
    assert payload["ok"] is True
    assert payload["status"] == "transcript_ready"
    assert payload["attach_to_job_id"] == "creator-linked-job"
    assert payload["job_id"] == "creator-linked-job"
    assert payload["job"]["source_adapter"] == "manual_file"
    assert payload["job"]["target_platforms"] == ["youtube", "linkedin"]
    assert payload["job"]["inputs"]["manual_media_path"] == media_ref
    assert payload["job"]["inputs"]["provided_transcript_path"] == transcript_ref
    assert payload["job"]["inputs"]["transcript_attached_to_media_job"] is True
    assert payload["job"]["inputs"]["provided_transcript_source_metadata"]["source_title"] == "Linked transcript"
    assert source_recording_after == source_recording_before
    assert "source_recording.json" not in "\n".join(payload["files_written"])
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_creator_ingest_attach_transcript_dry_run_reads_without_writes(tmp_path: Path, capsys) -> None:
    media_ref = _write_media(tmp_path, "linked-dry-run.mov")
    transcript_ref = _write_transcript(tmp_path, "linked-dry-run.md")
    build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id="creator-linked-dry-run",
    )

    exit_code = cli.main(
        [
            "creator",
            "ingest",
            "--source",
            "provided-transcript",
            "--transcript",
            transcript_ref,
            "--attach-to-job",
            "creator-linked-dry-run",
            "--target",
            "youtube",
            "--vault-root",
            str(tmp_path),
            "--dry-run",
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]
    job_root = tmp_path / "runtime" / "creator_engine" / "jobs" / "creator-linked-dry-run"

    assert exit_code == 0
    assert result["ok"] is True
    assert result["status"] == "dry_run_ready"
    assert result["writes_performed"] is False
    assert result["attach_to_job_id"] == "creator-linked-dry-run"
    assert result["files_written"] == []
    assert result["files_would_write"]
    assert result["preview"]["existing_source_adapter"] == "manual_file"
    assert result["preview"]["target_platforms"] == ["youtube"]
    assert not (job_root / "transcripts").exists()


def test_creator_ingest_manual_file_blocks_missing_media_without_writes(tmp_path: Path) -> None:
    payload = build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=None,
        job_id="should-not-write",
    )

    assert payload["ok"] is False
    assert payload["status"] == "missing_media"
    assert payload["writes_performed"] is False
    assert "--media is required" in payload["errors"][0]
    assert not (tmp_path / "runtime" / "creator_engine" / "jobs" / "should-not-write").exists()


def test_creator_ingest_unsupported_source_is_blocked_without_writes(tmp_path: Path) -> None:
    transcript_ref = _write_transcript(tmp_path, "recordly.md")

    payload = build_creator_ingest(
        vault_root=tmp_path,
        source="recordly",
        transcript_path=transcript_ref,
        job_id="should-not-write",
    )

    assert payload["ok"] is False
    assert payload["status"] == "unsupported_source"
    assert payload["writes_performed"] is False
    assert "provided-transcript or manual-file only" in payload["errors"][0]
    assert not (tmp_path / "runtime" / "creator_engine" / "jobs" / "should-not-write").exists()
