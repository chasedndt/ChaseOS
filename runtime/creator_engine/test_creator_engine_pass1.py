from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.creator_engine.adapters import (
    AdapterValidationResult,
    ManualFileRecordingAdapter,
    RecordingCandidate,
)
from runtime.creator_engine.job_store import CreatorJobStore, CreatorJobStoreError
from runtime.creator_engine.models import (
    BLOCKED_FUTURE_ACTIONS,
    ContentMemoryCard,
    EditPlan,
    SourceRecording,
)
from runtime.creator_engine.path_policy import CreatorEnginePathError, artifact_path


SCHEMA_DIR = Path(__file__).parent / "schemas"
EXPECTED_SCHEMAS = {
    "creator_job.schema.json": {"job_id", "status", "artifact_root", "approval_state"},
    "source_recording.schema.json": {"recording_id", "adapter", "path", "sha256"},
    "transcript_artifact.schema.json": {"artifact_id", "job_id", "transcript_path"},
    "context_pack.schema.json": {"artifact_id", "job_id", "context_path"},
    "edit_plan.schema.json": {"artifact_id", "job_id", "plan_path", "blocked_actions"},
    "caption_artifact.schema.json": {"artifact_id", "job_id", "caption_path"},
    "social_pack.schema.json": {"artifact_id", "job_id", "pack_path", "approval_required"},
    "content_memory_card.schema.json": {
        "artifact_id",
        "job_id",
        "card_path",
        "canonical_promotion_allowed",
    },
}


def test_schema_files_are_valid_json_with_required_fields() -> None:
    for filename, required_fields in EXPECTED_SCHEMAS.items():
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        assert schema["$schema"].endswith("2020-12/schema")
        assert schema["type"] == "object"
        assert required_fields.issubset(set(schema["required"]))


def test_job_store_creates_runtime_local_job(tmp_path: Path) -> None:
    store = CreatorJobStore(tmp_path)
    job = store.create_job(
        source_adapter="manual_file",
        source_recording_id="recording-001",
        target_platforms=["youtube", "tiktok"],
        inputs={"source_path": "03_INPUTS/Transcript-Raw/example.md"},
    )

    loaded = store.load_job(job.job_id)
    job_path = tmp_path / loaded["artifact_root"] / "job.json"

    assert loaded["status"] == "created"
    assert loaded["source_adapter"] == "manual_file"
    assert loaded["target_platforms"] == ["youtube", "tiktok"]
    assert job_path.exists()
    assert loaded["artifact_root"].startswith("runtime/creator_engine/jobs/")
    assert loaded["artifacts"]["blocked_future_actions"] == list(BLOCKED_FUTURE_ACTIONS)
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "01_PROJECTS").exists()
    assert not (tmp_path / "00_HOME").exists()


def test_job_store_blocks_unknown_source_adapter(tmp_path: Path) -> None:
    store = CreatorJobStore(tmp_path)

    with pytest.raises(CreatorJobStoreError):
        store.create_job(source_adapter="openscreen_mcp", source_recording_id="recording-001")


def test_job_store_blocks_job_root_escape(tmp_path: Path) -> None:
    outside_root = tmp_path.parent / f"{tmp_path.name}-outside"

    with pytest.raises(CreatorEnginePathError):
        CreatorJobStore(tmp_path, job_root=outside_root)


def test_artifact_paths_cannot_escape_job_directory(tmp_path: Path) -> None:
    store = CreatorJobStore(tmp_path)
    job = store.create_job(source_adapter="provided_transcript", source_recording_id="transcript-001")

    with pytest.raises(CreatorEnginePathError):
        store.write_artifact(job.job_id, "../outside.json", {})

    with pytest.raises(CreatorEnginePathError):
        artifact_path(tmp_path, job.job_id, "../../outside.json")


def test_job_store_writes_and_registers_artifact_inside_job(tmp_path: Path) -> None:
    store = CreatorJobStore(tmp_path)
    job = store.create_job(source_adapter="obs_folder", source_recording_id="obs-001")

    path = store.write_artifact(
        job.job_id,
        "transcripts/transcript.json",
        {"artifact_type": "transcript_artifact", "job_id": job.job_id},
        artifact_type="transcript_artifact",
    )
    loaded = store.load_job(job.job_id)

    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("{")
    assert loaded["artifacts"]["transcript_artifact"][0].endswith("transcripts/transcript.json")
    assert str(path).startswith(str(tmp_path))


def test_models_preserve_publish_and_promotion_blocks() -> None:
    recording = SourceRecording(
        recording_id="recording-001",
        adapter="recordly_folder",
        path="runtime/creator_engine/fixtures/example.wav",
        media_kind="audio",
        file_size_bytes=10,
        sha256="abc",
        created_at="2026-05-20T00:00:00Z",
        modified_at="2026-05-20T00:00:00Z",
    )
    edit_plan = EditPlan(artifact_id="edit-001", job_id="job-001", plan_path="edit_plan.json")
    memory_card = ContentMemoryCard(
        artifact_id="card-001",
        job_id="job-001",
        card_path="content_memory_card.json",
    )

    assert recording.probe_status == "not_probed"
    assert "direct_publish" in edit_plan.blocked_actions
    assert "auto_upload" in edit_plan.blocked_actions
    assert memory_card.canonical_promotion_allowed is False
    assert memory_card.approval_required is True


def test_adapter_contract_shape() -> None:
    candidate = RecordingCandidate(
        source_ref="recordings/example.wav",
        adapter_id="manual_file",
        media_kind="audio",
        metadata={"declared": True},
    )
    result = AdapterValidationResult(ok=True, normalized_source=candidate)

    assert result.ok is True
    assert result.normalized_source == candidate
    assert result.warnings == []
    assert result.blockers == []


def test_manual_file_adapter_discovers_and_validates_media_reference(tmp_path: Path) -> None:
    media_path = tmp_path / "03_INPUTS" / "Recordings" / "fixture.webm"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"creator-engine-manual-adapter-fixture")

    adapter = ManualFileRecordingAdapter(tmp_path)
    candidates = list(adapter.discover("03_INPUTS/Recordings/fixture.webm"))
    result = adapter.validate(candidates[0])

    assert len(candidates) == 1
    assert candidates[0].adapter_id == "manual_file"
    assert candidates[0].media_kind == "video"
    assert candidates[0].metadata["copied_media"] is False
    assert candidates[0].metadata["probe_status"] == "not_probed"
    assert len(candidates[0].metadata["sha256"]) == 64
    assert result.ok is True
    assert result.normalized_source == candidates[0]
