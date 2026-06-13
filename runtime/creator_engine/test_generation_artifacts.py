from __future__ import annotations

import json
from pathlib import Path

import pytest

import runtime.cli.main as cli
from runtime.creator_engine.cli import build_creator_generation_stubs, build_creator_ingest
from runtime.creator_engine.context_pack import build_context_pack
from runtime.creator_engine.generator import (
    GenerationArtifactError,
    build_generation_artifact_stubs,
    preview_generation_artifact_stubs,
)


def _write_transcript(vault_root: Path, name: str = "transcript.md") -> str:
    rel_path = Path("03_INPUTS") / "Transcript-Raw" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Transcript\n\n"
        "Creator Engine now has context and should produce reviewable draft stubs. "
        "The package needs captions, social copy, an edit plan, and a memory card stub.\n",
        encoding="utf-8",
    )
    return rel_path.as_posix()


def _write_media(vault_root: Path, name: str = "recording.mp4") -> str:
    rel_path = Path("03_INPUTS") / "Recordings" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"creator-engine-generation-artifact-media-fixture\n")
    return rel_path.as_posix()


def _write_context(vault_root: Path, name: str = "creator-engine-context.md") -> str:
    rel_path = Path("docs") / "context" / name
    path = vault_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Creator Engine Context\n\n"
        "Keep artifacts runtime-local, review-first, and blocked from publishing until approval.\n",
        encoding="utf-8",
    )
    return rel_path.as_posix()


def _create_context_ready_job(tmp_path: Path, job_id: str = "creator-generation-test") -> str:
    media_ref = _write_media(tmp_path)
    transcript_ref = _write_transcript(tmp_path)
    context_ref = _write_context(tmp_path)
    media_payload = build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id=job_id,
        target_platforms=["youtube"],
        context_prompt="Use ChaseInTech review-first framing.",
        manual_source_metadata={"source_title": "Creator generation fixture"},
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


def test_build_generation_artifact_stubs_writes_runtime_local_drafts(tmp_path: Path) -> None:
    job_id = _create_context_ready_job(tmp_path)

    result = build_generation_artifact_stubs(tmp_path, job_id=job_id, target_platforms=["x"])

    job_root = tmp_path / "runtime" / "creator_engine" / "jobs" / job_id
    manifest = json.loads((job_root / "generation" / "generation_manifest.json").read_text(encoding="utf-8"))
    edit_plan = json.loads((job_root / "edit" / "edit_plan.json").read_text(encoding="utf-8"))
    social_pack = json.loads((job_root / "social" / "social_pack.json").read_text(encoding="utf-8"))
    memory_card = json.loads((job_root / "memory" / "content_memory_card.json").read_text(encoding="utf-8"))

    assert result.job["status"] == "draft_ready"
    assert result.generation_artifact_id == manifest["artifact_id"]
    assert manifest["status"] == "draft_stub_ready"
    assert manifest["generation_mode"] == "deterministic_stub"
    assert manifest["authority_flags"]["provider_call_allowed"] is False
    assert manifest["authority_flags"]["upload_allowed"] is False
    assert manifest["authority_flags"]["canonical_writeback_allowed"] is False
    assert result.job["inputs"]["provider_call_performed"] is False
    assert result.job["inputs"]["ai_generation_performed"] is False
    assert result.job["inputs"]["publish_performed"] is False
    assert result.job["approval_state"]["approval_artifact_written"] is False
    assert "content_memory_card_canonical_promotion" in result.job["approval_state"]["future_approval_required_for"]
    assert result.job["target_platforms"] == ["youtube", "linkedin"]
    assert manifest["target_platforms"] == ["youtube", "linkedin", "x"]
    assert edit_plan["status"] == "draft_stub"
    assert edit_plan["approval_required"] is True
    assert social_pack["target_platforms"] == ["youtube", "linkedin", "x"]
    assert all(post["publish_allowed"] is False for post in social_pack["posts"])
    assert memory_card["canonical_promotion_allowed"] is False
    assert memory_card["approval_required"] is True
    assert (job_root / "transcripts" / "transcript.clean.md").exists()
    assert (job_root / "drafts" / "script.cleaned.md").exists()
    assert (job_root / "drafts" / "voiceover.script.md").exists()
    assert (job_root / "captions" / "captions.srt").exists()
    assert (job_root / "captions" / "captions.vtt").exists()
    assert (job_root / "metadata" / "upload_metadata.json").exists()
    assert all(path.startswith("runtime/creator_engine/jobs/") for path in result.files_written)
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()


def test_preview_generation_artifact_stubs_reads_without_writes(tmp_path: Path) -> None:
    job_id = _create_context_ready_job(tmp_path, "creator-generation-preview")

    preview = preview_generation_artifact_stubs(tmp_path, job_id=job_id, target_platforms=["x"])

    job_root = tmp_path / "runtime" / "creator_engine" / "jobs" / job_id
    loaded_job = json.loads((job_root / "job.json").read_text(encoding="utf-8"))

    assert preview.job_status == "context_ready"
    assert preview.target_platforms == ["youtube", "linkedin", "x"]
    assert preview.files_would_write
    assert preview.artifact_paths["generation_manifest"].endswith("generation/generation_manifest.json")
    assert loaded_job["status"] == "context_ready"
    assert not (job_root / "generation").exists()
    assert not (job_root / "drafts").exists()


def test_generation_artifacts_block_non_context_ready_jobs(tmp_path: Path) -> None:
    media_ref = _write_media(tmp_path, "no-context.mp4")
    transcript_ref = _write_transcript(tmp_path, "no-context.md")
    build_creator_ingest(
        vault_root=tmp_path,
        source="manual-file",
        media_path=media_ref,
        job_id="creator-generation-no-context",
    )
    build_creator_ingest(
        vault_root=tmp_path,
        source="provided-transcript",
        transcript_path=transcript_ref,
        attach_to_job_id="creator-generation-no-context",
    )

    with pytest.raises(GenerationArtifactError, match="context_ready"):
        build_generation_artifact_stubs(tmp_path, job_id="creator-generation-no-context")

    assert not (
        tmp_path
        / "runtime"
        / "creator_engine"
        / "jobs"
        / "creator-generation-no-context"
        / "generation"
    ).exists()


def test_generation_artifacts_block_duplicate_drafts(tmp_path: Path) -> None:
    job_id = _create_context_ready_job(tmp_path, "creator-generation-duplicate")
    build_generation_artifact_stubs(tmp_path, job_id=job_id)

    with pytest.raises(GenerationArtifactError, match="already has generation draft"):
        build_generation_artifact_stubs(tmp_path, job_id=job_id)


def test_creator_generate_stubs_cli_json_envelope(tmp_path: Path, capsys) -> None:
    job_id = _create_context_ready_job(tmp_path, "creator-generation-cli")

    exit_code = cli.main(
        [
            "creator",
            "generate-stubs",
            "--job-id",
            job_id,
            "--target",
            "x",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    envelope = json.loads(capsys.readouterr().out)
    result = envelope["result"]

    assert exit_code == 0
    assert envelope["ok"] is True
    assert envelope["action"] == "creator.generate-stubs"
    assert result["status"] == "draft_ready"
    assert result["writes_performed"] is True
    assert result["job"]["status"] == "draft_ready"
    assert result["manifest"]["authority_flags"]["provider_call_allowed"] is False
    assert result["manifest"]["authority_flags"]["direct_publish_allowed"] is False
    assert result["target_platforms"] == ["youtube", "linkedin", "x"]


def test_creator_generate_stubs_dry_run_cli_reads_without_writes(tmp_path: Path, capsys) -> None:
    job_id = _create_context_ready_job(tmp_path, "creator-generation-cli-dry-run")

    exit_code = cli.main(
        [
            "creator",
            "generate-stubs",
            "--job-id",
            job_id,
            "--target",
            "x",
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
    assert envelope["action"] == "creator.generate-stubs"
    assert result["status"] == "dry_run_ready"
    assert result["writes_performed"] is False
    assert result["files_written"] == []
    assert result["files_would_write"]
    assert result["authority_flags"]["runtime_local_write_allowed"] is False
    assert result["target_platforms"] == ["youtube", "linkedin", "x"]
    assert not (job_root / "generation").exists()
    assert not (job_root / "drafts").exists()


def test_build_creator_generation_stubs_error_payload_for_missing_job_id(tmp_path: Path) -> None:
    payload = build_creator_generation_stubs(vault_root=tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "missing_job_id"
    assert payload["writes_performed"] is False
    assert "--job-id is required" in payload["errors"][0]
