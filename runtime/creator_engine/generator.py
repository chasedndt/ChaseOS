"""Deterministic draft artifact stubs for Creator Engine jobs.

This pass packages existing context-ready jobs into reviewable runtime-local
drafts. It deliberately does not call a provider, query Source Intelligence,
publish/upload, or promote anything into governed ChaseOS memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .job_store import CreatorJobStore
from .models import (
    BLOCKED_FUTURE_ACTIONS,
    CaptionArtifact,
    ContentMemoryCard,
    EditPlan,
    SocialPack,
    utc_now,
)
from .path_policy import artifact_path, relative_to_vault, resolve_vault_root


DEFAULT_TARGET_PLATFORMS = ("youtube", "linkedin", "x")
DEFAULT_EXCERPT_CHARS = 900


class GenerationArtifactError(ValueError):
    """Raised when Creator Engine draft stubs cannot be safely produced."""


@dataclass
class GenerationArtifactPreviewResult:
    job_id: str
    source_recording_id: str
    generation_artifact_id: str
    job_status: str
    input_digest: str
    target_platforms: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    files_would_write: list[str] = field(default_factory=list)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "generation_artifact_id": self.generation_artifact_id,
            "job_status": self.job_status,
            "input_digest": self.input_digest,
            "target_platforms": list(self.target_platforms),
            "files_read": list(self.files_read),
            "files_would_write": list(self.files_would_write),
            "artifact_paths": dict(self.artifact_paths),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class GenerationArtifactBuildResult:
    job_id: str
    source_recording_id: str
    generation_artifact_id: str
    job: dict[str, Any]
    manifest: dict[str, Any]
    files_read: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "generation_artifact_id": self.generation_artifact_id,
            "job": self.job,
            "manifest": self.manifest,
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class _GenerationInputs:
    job: dict[str, Any]
    job_ref: str
    source_recording: dict[str, Any]
    source_recording_ref: str
    context_pack: dict[str, Any]
    context_pack_ref: str
    transcript_text: str
    transcript_ref: str
    target_platforms: list[str]
    files_read: list[str]
    warnings: list[str]


def preview_generation_artifact_stubs(
    vault_root: str | Path,
    *,
    job_id: str,
    target_platforms: list[str] | None = None,
    job_store: CreatorJobStore | None = None,
) -> GenerationArtifactPreviewResult:
    """Validate a context-ready job and return write-free artifact paths."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root, create_root=False)
    inputs = _load_generation_inputs(root, store, job_id, target_platforms=target_platforms)
    payloads = _build_generation_payloads(root=root, store=store, inputs=inputs)
    return GenerationArtifactPreviewResult(
        job_id=str(inputs.job.get("job_id", job_id)),
        source_recording_id=str(inputs.job.get("source_recording_id", "")),
        generation_artifact_id=str(payloads["manifest"]["artifact_id"]),
        job_status=str(inputs.job.get("status", "")),
        input_digest=str(payloads["manifest"]["input_digest"]),
        target_platforms=list(inputs.target_platforms),
        files_read=list(inputs.files_read),
        files_would_write=[*payloads["relative_paths"].values(), inputs.job_ref],
        artifact_paths=dict(payloads["relative_paths"]),
        warnings=list(payloads["warnings"]),
    )


def build_generation_artifact_stubs(
    vault_root: str | Path,
    *,
    job_id: str,
    target_platforms: list[str] | None = None,
    job_store: CreatorJobStore | None = None,
) -> GenerationArtifactBuildResult:
    """Write deterministic runtime-local draft artifacts for a context-ready job."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root)
    inputs = _load_generation_inputs(root, store, job_id, target_platforms=target_platforms)
    payloads = _build_generation_payloads(root=root, store=store, inputs=inputs)

    written_paths = [
        store.write_artifact(job_id, "transcripts/transcript.clean.md", payloads["clean_transcript"], artifact_type="transcript_clean"),
        store.write_artifact(job_id, "drafts/script.cleaned.md", payloads["script_stub"], artifact_type="script_stub"),
        store.write_artifact(job_id, "drafts/voiceover.script.md", payloads["voiceover_stub"], artifact_type="voiceover_script_stub"),
        store.write_artifact(job_id, "captions/captions.srt", payloads["captions_srt"], artifact_type="caption_file"),
        store.write_artifact(job_id, "captions/captions.vtt", payloads["captions_vtt"], artifact_type="caption_file"),
        store.write_artifact(job_id, "captions/captions.srt.json", payloads["caption_srt_artifact"], artifact_type="caption_artifact"),
        store.write_artifact(job_id, "captions/captions.vtt.json", payloads["caption_vtt_artifact"], artifact_type="caption_artifact"),
        store.write_artifact(job_id, "edit/edit_plan.json", payloads["edit_plan"], artifact_type="edit_plan"),
        store.write_artifact(job_id, "social/social_pack.json", payloads["social_pack"], artifact_type="social_pack"),
        store.write_artifact(job_id, "social/social_pack.md", payloads["social_pack_markdown"], artifact_type="social_pack_markdown"),
        store.write_artifact(job_id, "metadata/upload_metadata.json", payloads["upload_metadata"], artifact_type="upload_metadata"),
        store.write_artifact(job_id, "memory/content_memory_card.json", payloads["content_memory_card"], artifact_type="content_memory_card"),
        store.write_artifact(job_id, "memory/content_memory_card.md", payloads["content_memory_card_markdown"], artifact_type="content_memory_card_markdown"),
        store.write_artifact(job_id, "generation/generation_manifest.json", payloads["manifest"], artifact_type="generation_manifest"),
    ]

    updated_job = store.load_job(job_id)
    updated_inputs = dict(updated_job.get("inputs", {}))
    updated_inputs.update(
        {
            "generation_stub_input_digest": payloads["manifest"]["input_digest"],
            "generation_mode": "deterministic_stub",
            "generation_artifact_stub_write_performed": True,
            "provider_call_performed": False,
            "ai_generation_performed": False,
            "source_intelligence_query_performed": False,
            "rag_index_write_performed": False,
            "publish_performed": False,
            "canonical_writeback_performed": False,
            "governed_memory_write_performed": False,
            "target_platforms_for_generation": list(inputs.target_platforms),
        }
    )
    updated_job["status"] = "draft_ready"
    updated_job["inputs"] = updated_inputs
    updated_job["approval_state"] = _draft_approval_state(updated_job.get("approval_state"))
    updated_job["warnings"] = list(
        dict.fromkeys([*updated_job.get("warnings", []), *payloads["warnings"]])
    )
    job_path = store.save_job(updated_job)
    final_job = store.load_job(job_id)

    return GenerationArtifactBuildResult(
        job_id=str(final_job.get("job_id", job_id)),
        source_recording_id=str(final_job.get("source_recording_id", "")),
        generation_artifact_id=str(payloads["manifest"]["artifact_id"]),
        job=final_job,
        manifest=payloads["manifest"],
        files_read=list(inputs.files_read),
        files_written=[*[relative_to_vault(root, path) for path in written_paths], relative_to_vault(root, job_path)],
        warnings=list(payloads["warnings"]),
    )


def _load_generation_inputs(
    root: Path,
    store: CreatorJobStore,
    job_id: str,
    *,
    target_platforms: list[str] | None,
) -> _GenerationInputs:
    try:
        job = store.load_job(job_id)
    except Exception as exc:
        raise GenerationArtifactError(f"Creator Engine job not found: {job_id}") from exc

    _ensure_no_existing_generation_artifacts(root, store, job_id, job)
    if job.get("status") != "context_ready":
        raise GenerationArtifactError("generation stubs can only be built for a context_ready Creator Engine job")
    if not job.get("source_recording_id"):
        raise GenerationArtifactError("Creator Engine job is missing source_recording_id")

    source_ref, source_recording = _read_job_json_artifact(
        root,
        store,
        job_id,
        "source_recording.json",
        missing_message="Creator Engine job is missing source_recording.json",
    )
    if source_recording.get("recording_id") != job.get("source_recording_id"):
        raise GenerationArtifactError("source_recording.json id does not match the Creator Engine job")

    context_ref, context_pack = _read_job_json_artifact(
        root,
        store,
        job_id,
        "context/context_pack.json",
        missing_message="Creator Engine job is missing context/context_pack.json",
    )
    if context_pack.get("job_id") != job.get("job_id"):
        raise GenerationArtifactError("context_pack.json job_id does not match the Creator Engine job")

    transcript_path = artifact_path(root, job_id, "transcripts/transcript.raw.md", store.job_root)
    if not transcript_path.exists():
        raise GenerationArtifactError("Creator Engine job is missing transcripts/transcript.raw.md")
    try:
        transcript_text = _normalize_text(transcript_path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise GenerationArtifactError("Creator Engine transcript artifact must be UTF-8 text") from exc
    if not transcript_text:
        raise GenerationArtifactError("Creator Engine transcript artifact is empty")
    transcript_ref = relative_to_vault(root, transcript_path)

    resolved_targets = _resolve_target_platforms(job, target_platforms)
    job_ref = relative_to_vault(root, artifact_path(root, job_id, "job.json", store.job_root))
    warnings = [
        "deterministic_stub_only_no_provider_call",
        "caption_timing_unverified_untimed_stub",
        "review_required_before_publish_upload_or_memory_promotion",
    ]
    return _GenerationInputs(
        job=job,
        job_ref=job_ref,
        source_recording=source_recording,
        source_recording_ref=source_ref,
        context_pack=context_pack,
        context_pack_ref=context_ref,
        transcript_text=transcript_text,
        transcript_ref=transcript_ref,
        target_platforms=resolved_targets,
        files_read=[job_ref, source_ref, context_ref, transcript_ref],
        warnings=warnings,
    )


def _build_generation_payloads(
    *,
    root: Path,
    store: CreatorJobStore,
    inputs: _GenerationInputs,
) -> dict[str, Any]:
    paths = _generation_artifact_paths(root, store, str(inputs.job["job_id"]))
    relative_paths = {name: relative_to_vault(root, path) for name, path in paths.items()}
    input_digest = _generation_input_digest(inputs)
    artifact_id = f"generation-stubs-{input_digest[:12]}"
    now = utc_now()
    source_title = _source_title(inputs)
    transcript_excerpt = _excerpt(inputs.transcript_text, DEFAULT_EXCERPT_CHARS)
    source_refs = list(
        dict.fromkeys(
            [
                inputs.source_recording_ref,
                inputs.context_pack_ref,
                inputs.transcript_ref,
                *list(inputs.context_pack.get("source_refs") or []),
            ]
        )
    )
    source_summary = {
        "title": source_title,
        "source_recording_id": inputs.source_recording.get("recording_id"),
        "source_adapter": inputs.source_recording.get("adapter"),
        "media_kind": inputs.source_recording.get("media_kind"),
        "transcript_word_count": _word_count(inputs.transcript_text),
        "context_pack_id": inputs.context_pack.get("artifact_id"),
        "context_item_count": len(inputs.context_pack.get("context_items") or []),
    }
    clean_transcript = _render_clean_transcript(inputs, source_title)
    script_stub = _render_script_stub(inputs, source_title, transcript_excerpt)
    voiceover_stub = _render_voiceover_stub(inputs, source_title, transcript_excerpt)
    captions_srt = _render_srt_stub(transcript_excerpt)
    captions_vtt = _render_vtt_stub(transcript_excerpt)
    caption_warning = ["untimed_caption_stub_review_required"]
    caption_srt_artifact = CaptionArtifact(
        artifact_id=f"caption-srt-{input_digest[:12]}",
        job_id=str(inputs.job["job_id"]),
        caption_path=relative_paths["captions_srt"],
        format="srt",
        status="untimed_stub",
        line_count=len([line for line in captions_srt.splitlines() if line.strip()]),
        warnings=caption_warning,
    ).to_dict()
    caption_vtt_artifact = CaptionArtifact(
        artifact_id=f"caption-vtt-{input_digest[:12]}",
        job_id=str(inputs.job["job_id"]),
        caption_path=relative_paths["captions_vtt"],
        format="vtt",
        status="untimed_stub",
        line_count=len([line for line in captions_vtt.splitlines() if line.strip()]),
        warnings=caption_warning,
    ).to_dict()
    edit_plan = EditPlan(
        artifact_id=f"edit-plan-{input_digest[:12]}",
        job_id=str(inputs.job["job_id"]),
        plan_path=relative_paths["edit_plan"],
        target_formats=list(inputs.target_platforms),
        status="draft_stub",
    ).to_dict()
    edit_plan.update(
        {
            "generation_mode": "deterministic_stub",
            "provider_call_performed": False,
            "source_summary": source_summary,
            "timeline": [
                {
                    "segment": "hook",
                    "time_range": "00:00-00:05",
                    "instruction": "Review and replace with the strongest operator-approved opening moment.",
                    "source_refs": [inputs.transcript_ref],
                },
                {
                    "segment": "walkthrough",
                    "time_range": "review_required",
                    "instruction": "Use the transcript/context pack to choose the real demo beats before editing.",
                    "source_refs": [inputs.context_pack_ref],
                },
                {
                    "segment": "close",
                    "time_range": "review_required",
                    "instruction": "Add a platform-specific call to action only after operator review.",
                    "source_refs": [inputs.context_pack_ref],
                },
            ],
            "b_roll_suggestions": [
                "Use real product or repo footage from the declared recording only.",
                "Do not add unverifiable product claims without repo evidence.",
            ],
            "approval_required_for": ["timeline_edit_execution", "external_delivery", "publish_upload"],
            "authority_flags": _generation_authority_flags(),
        }
    )
    social_pack = SocialPack(
        artifact_id=f"social-pack-{input_digest[:12]}",
        job_id=str(inputs.job["job_id"]),
        pack_path=relative_paths["social_pack"],
        target_platforms=list(inputs.target_platforms),
        posts=_social_posts(inputs, source_title, transcript_excerpt),
        status="draft_stub",
    ).to_dict()
    social_pack.update(
        {
            "generation_mode": "deterministic_stub",
            "provider_call_performed": False,
            "approval_required_for": ["publish_upload", "external_delivery"],
            "source_refs": source_refs,
            "authority_flags": _generation_authority_flags(),
        }
    )
    upload_metadata = {
        "schema_version": "creator_engine.v1",
        "artifact_id": f"upload-metadata-{input_digest[:12]}",
        "artifact_type": "upload_metadata",
        "job_id": inputs.job["job_id"],
        "created_at": now,
        "status": "manual_upload_metadata_stub",
        "metadata_path": relative_paths["upload_metadata"],
        "target_platforms": list(inputs.target_platforms),
        "title_stub": source_title,
        "description_stub": "Review required. This metadata was assembled deterministically from a context-ready job.",
        "manual_upload_only": True,
        "upload_allowed": False,
        "publish_allowed": False,
        "provider_call_performed": False,
        "source_refs": source_refs,
        "authority_flags": _generation_authority_flags(),
        "blocked_actions": list(BLOCKED_FUTURE_ACTIONS),
    }
    memory_card = ContentMemoryCard(
        artifact_id=f"content-memory-card-{input_digest[:12]}",
        job_id=str(inputs.job["job_id"]),
        card_path=relative_paths["content_memory_card"],
        summary=f"Draft content memory card stub for {source_title}. Review is required before any canonical promotion.",
        source_refs=source_refs,
        canonical_promotion_allowed=False,
        approval_required=True,
        status="draft_stub",
    ).to_dict()
    memory_card.update(
        {
            "generation_mode": "deterministic_stub",
            "provider_call_performed": False,
            "promotion_target": None,
            "authority_flags": _generation_authority_flags(),
            "blocked_actions": list(BLOCKED_FUTURE_ACTIONS),
        }
    )
    manifest = {
        "schema_version": "creator_engine.v1",
        "artifact_id": artifact_id,
        "artifact_type": "generation_artifact_manifest",
        "job_id": inputs.job["job_id"],
        "source_recording_id": inputs.job.get("source_recording_id"),
        "created_at": now,
        "status": "draft_stub_ready",
        "generation_mode": "deterministic_stub",
        "input_digest": input_digest,
        "target_platforms": list(inputs.target_platforms),
        "artifact_paths": dict(relative_paths),
        "source_summary": source_summary,
        "source_refs": source_refs,
        "authority_flags": _generation_authority_flags(),
        "approval_required_for": [
            "content_memory_card_canonical_promotion",
            "publish_upload",
            "external_delivery",
            "timeline_edit_execution",
        ],
        "blocked_future_actions": list(BLOCKED_FUTURE_ACTIONS),
        "transformation_chain": [
            {"step": "load_context_ready_creator_job", "job_ref": inputs.job_ref, "external_call": False},
            {"step": "read_runtime_local_context_pack", "context_pack_ref": inputs.context_pack_ref, "external_call": False},
            {"step": "read_runtime_local_transcript", "transcript_ref": inputs.transcript_ref, "external_call": False},
            {"step": "write_runtime_local_draft_stubs", "artifact_root": inputs.job.get("artifact_root"), "external_call": False},
        ],
        "warnings": list(inputs.warnings),
        "blockers": [],
    }
    return {
        "relative_paths": relative_paths,
        "clean_transcript": clean_transcript,
        "script_stub": script_stub,
        "voiceover_stub": voiceover_stub,
        "captions_srt": captions_srt,
        "captions_vtt": captions_vtt,
        "caption_srt_artifact": caption_srt_artifact,
        "caption_vtt_artifact": caption_vtt_artifact,
        "edit_plan": edit_plan,
        "social_pack": social_pack,
        "social_pack_markdown": _render_social_pack_markdown(social_pack),
        "upload_metadata": upload_metadata,
        "content_memory_card": memory_card,
        "content_memory_card_markdown": _render_content_memory_card_markdown(memory_card, transcript_excerpt),
        "manifest": manifest,
        "warnings": list(inputs.warnings),
    }


def _read_job_json_artifact(
    root: Path,
    store: CreatorJobStore,
    job_id: str,
    relative_path: str,
    *,
    missing_message: str,
) -> tuple[str, dict[str, Any]]:
    path = artifact_path(root, job_id, relative_path, store.job_root)
    if not path.exists():
        raise GenerationArtifactError(missing_message)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GenerationArtifactError(f"{relative_path} is not valid JSON") from exc
    if not isinstance(loaded, dict):
        raise GenerationArtifactError(f"{relative_path} is not a JSON object")
    return relative_to_vault(root, path), loaded


def _ensure_no_existing_generation_artifacts(
    root: Path,
    store: CreatorJobStore,
    job_id: str,
    job: dict[str, Any],
) -> None:
    artifacts = job.get("artifacts", {}) if isinstance(job.get("artifacts"), dict) else {}
    existing_types = {
        "generation_manifest",
        "transcript_clean",
        "script_stub",
        "voiceover_script_stub",
        "caption_artifact",
        "caption_file",
        "edit_plan",
        "social_pack",
        "upload_metadata",
        "content_memory_card",
    }
    if any(artifacts.get(key) for key in existing_types):
        raise GenerationArtifactError("Creator Engine job already has generation draft artifacts")
    if any(path.exists() for path in _generation_artifact_paths(root, store, job_id).values()):
        raise GenerationArtifactError("Creator Engine job already has generation draft files")


def _generation_artifact_paths(root: Path, store: CreatorJobStore, job_id: str) -> dict[str, Path]:
    return {
        "clean_transcript": artifact_path(root, job_id, "transcripts/transcript.clean.md", store.job_root),
        "script_stub": artifact_path(root, job_id, "drafts/script.cleaned.md", store.job_root),
        "voiceover_stub": artifact_path(root, job_id, "drafts/voiceover.script.md", store.job_root),
        "captions_srt": artifact_path(root, job_id, "captions/captions.srt", store.job_root),
        "captions_vtt": artifact_path(root, job_id, "captions/captions.vtt", store.job_root),
        "caption_srt_artifact": artifact_path(root, job_id, "captions/captions.srt.json", store.job_root),
        "caption_vtt_artifact": artifact_path(root, job_id, "captions/captions.vtt.json", store.job_root),
        "edit_plan": artifact_path(root, job_id, "edit/edit_plan.json", store.job_root),
        "social_pack": artifact_path(root, job_id, "social/social_pack.json", store.job_root),
        "social_pack_markdown": artifact_path(root, job_id, "social/social_pack.md", store.job_root),
        "upload_metadata": artifact_path(root, job_id, "metadata/upload_metadata.json", store.job_root),
        "content_memory_card": artifact_path(root, job_id, "memory/content_memory_card.json", store.job_root),
        "content_memory_card_markdown": artifact_path(root, job_id, "memory/content_memory_card.md", store.job_root),
        "generation_manifest": artifact_path(root, job_id, "generation/generation_manifest.json", store.job_root),
    }


def _generation_input_digest(inputs: _GenerationInputs) -> str:
    digest_payload = {
        "job_id": inputs.job.get("job_id"),
        "source_recording_sha256": inputs.source_recording.get("sha256"),
        "context_pack_input_digest": inputs.context_pack.get("input_digest"),
        "context_pack_artifact_id": inputs.context_pack.get("artifact_id"),
        "transcript_sha256": hashlib.sha256(inputs.transcript_text.encode("utf-8")).hexdigest(),
        "target_platforms": list(inputs.target_platforms),
    }
    serialized = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _resolve_target_platforms(job: dict[str, Any], requested: list[str] | None) -> list[str]:
    values: list[str] = []
    for value in [*(job.get("target_platforms") or []), *(requested or [])]:
        cleaned = str(value).strip().lower()
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return values or list(DEFAULT_TARGET_PLATFORMS)


def _source_title(inputs: _GenerationInputs) -> str:
    candidates: list[str] = []
    for key in ("manual_source_metadata", "provided_transcript_source_metadata"):
        metadata = inputs.job.get("inputs", {}).get(key)
        if isinstance(metadata, dict) and metadata.get("source_title"):
            candidates.append(str(metadata["source_title"]))
    source_path = inputs.source_recording.get("path")
    if source_path:
        candidates.append(Path(str(source_path)).stem.replace("-", " ").replace("_", " "))
    for candidate in candidates:
        normalized = " ".join(candidate.split())
        if normalized:
            return normalized[:120]
    return f"Creator Engine draft {inputs.job.get('job_id')}"


def _render_clean_transcript(inputs: _GenerationInputs, source_title: str) -> str:
    return "\n".join(
        [
            f"# Clean Transcript Stub - {source_title}",
            "",
            "Status: deterministic normalization only. No AI cleanup or provider generation was performed.",
            "",
            "## Source",
            "",
            f"- Job: `{inputs.job.get('job_id')}`",
            f"- Raw transcript: `{inputs.transcript_ref}`",
            f"- Context pack: `{inputs.context_pack_ref}`",
            "",
            "## Transcript",
            "",
            inputs.transcript_text.rstrip(),
            "",
        ]
    )


def _render_script_stub(inputs: _GenerationInputs, source_title: str, transcript_excerpt: str) -> str:
    return "\n".join(
        [
            f"# Script Draft Stub - {source_title}",
            "",
            "Status: deterministic review scaffold. No model/provider generation was performed.",
            "",
            "## Hook",
            "",
            "[Review required] Select the strongest real moment from the recording/transcript.",
            "",
            "## Core Beats",
            "",
            "1. Establish what the demo or build pass is about.",
            "2. Show the concrete repo/product evidence from the recording.",
            "3. Explain the operator-visible result without overstating completion.",
            "",
            "## Transcript Excerpt",
            "",
            "```text",
            transcript_excerpt,
            "```",
            "",
            "## Required Review",
            "",
            "- Verify every claim against the source recording, transcript, and context pack.",
            "- Approve separately before timeline execution, upload, publishing, or memory promotion.",
            f"- Context pack: `{inputs.context_pack_ref}`",
            "",
        ]
    )


def _render_voiceover_stub(inputs: _GenerationInputs, source_title: str, transcript_excerpt: str) -> str:
    first_sentence = _first_sentence(transcript_excerpt)
    return "\n".join(
        [
            f"# Voiceover Script Stub - {source_title}",
            "",
            "Status: deterministic placeholder. No TTS or model/provider generation was performed.",
            "",
            "## Opening",
            "",
            first_sentence or "[Review required] Draft the opening from the verified transcript.",
            "",
            "## Notes",
            "",
            "- Keep this as a human-reviewed script before recording or TTS.",
            "- Do not add unsupported implementation claims.",
            f"- Source transcript: `{inputs.transcript_ref}`",
            "",
        ]
    )


def _render_srt_stub(transcript_excerpt: str) -> str:
    caption = _caption_text(transcript_excerpt)
    return f"1\n00:00:00,000 --> 00:00:05,000\n[Untimed stub] {caption}\n"


def _render_vtt_stub(transcript_excerpt: str) -> str:
    caption = _caption_text(transcript_excerpt)
    return f"WEBVTT\n\n00:00:00.000 --> 00:00:05.000\n[Untimed stub] {caption}\n"


def _social_posts(inputs: _GenerationInputs, source_title: str, transcript_excerpt: str) -> list[dict[str, Any]]:
    excerpt = _caption_text(transcript_excerpt, limit=180)
    posts: list[dict[str, Any]] = []
    for platform in inputs.target_platforms:
        posts.append(
            {
                "platform": platform,
                "status": "draft_stub",
                "title_stub": source_title,
                "body_stub": f"Review required: {excerpt}",
                "cta_stub": "Operator approval required before posting.",
                "source_refs": [inputs.transcript_ref, inputs.context_pack_ref],
                "publish_allowed": False,
            }
        )
    return posts


def _render_social_pack_markdown(social_pack: dict[str, Any]) -> str:
    lines = [
        "# Creator Engine Social Pack Stub",
        "",
        f"- Job: `{social_pack.get('job_id')}`",
        f"- Artifact: `{social_pack.get('artifact_id')}`",
        "- Boundary: review artifact only; no upload or publish authority.",
        "",
    ]
    for post in social_pack.get("posts") or []:
        lines.extend(
            [
                f"## {post.get('platform')}",
                "",
                f"- Title: {post.get('title_stub')}",
                f"- Body: {post.get('body_stub')}",
                f"- CTA: {post.get('cta_stub')}",
                f"- Publish allowed: `{post.get('publish_allowed')}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_content_memory_card_markdown(memory_card: dict[str, Any], transcript_excerpt: str) -> str:
    lines = [
        "# Creator Engine Content Memory Card Stub",
        "",
        f"- Job: `{memory_card.get('job_id')}`",
        f"- Artifact: `{memory_card.get('artifact_id')}`",
        f"- Status: `{memory_card.get('status')}`",
        f"- Approval required: `{memory_card.get('approval_required')}`",
        f"- Canonical promotion allowed: `{memory_card.get('canonical_promotion_allowed')}`",
        "",
        "## Summary",
        "",
        str(memory_card.get("summary", "")),
        "",
        "## Source Refs",
        "",
    ]
    for ref in memory_card.get("source_refs") or []:
        lines.append(f"- `{ref}`")
    lines.extend(
        [
            "",
            "## Transcript Excerpt",
            "",
            "```text",
            transcript_excerpt,
            "```",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _draft_approval_state(existing: Any) -> dict[str, Any]:
    base = dict(existing) if isinstance(existing, dict) else {}
    base["requires_approval"] = False
    base.setdefault("approval_ids", [])
    base["future_approval_required_for"] = [
        "content_memory_card_canonical_promotion",
        "publish_upload",
        "external_delivery",
        "timeline_edit_execution",
    ]
    base["approval_artifact_written"] = False
    return base


def _generation_authority_flags() -> dict[str, bool]:
    return {
        "runtime_local_write_allowed": True,
        "generation_artifact_stub_write_allowed": True,
        "deterministic_template_only": True,
        "ai_generation_performed": False,
        "source_intelligence_query_allowed": False,
        "rag_index_write_allowed": False,
        "provider_call_allowed": False,
        "tts_generation_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
    }


def _normalize_text(text: str) -> str:
    body = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return f"{body}\n" if body else ""


def _excerpt(text: str, limit: int) -> str:
    normalized = _normalize_text(text)
    if len(normalized) <= limit:
        return normalized.rstrip()
    return normalized[:limit].rstrip()


def _caption_text(text: str, *, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", _normalize_text(text)).strip()
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _first_sentence(text: str) -> str:
    compact = _caption_text(text, limit=220)
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    return match.group(1).strip() if match else compact


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))
