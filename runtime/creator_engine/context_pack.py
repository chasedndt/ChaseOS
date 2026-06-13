"""Context-pack foundation for Creator Engine jobs.

This module builds reviewable, runtime-local context packs from explicit source
references. It does not query providers, build a vector index, generate scripts,
publish content, or promote content into canonical ChaseOS memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .job_store import CreatorJobStore
from .models import BLOCKED_FUTURE_ACTIONS, ContextPack
from .path_policy import artifact_path, ensure_within, relative_to_vault, resolve_vault_root


SUPPORTED_CONTEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml"}
FORBIDDEN_CONTEXT_PATH_PARTS = {"secrets", "credentials"}
MAX_CONTEXT_FILE_BYTES = 512 * 1024
DEFAULT_EXCERPT_CHARS = 1200
INSTRUCTION_LIKE_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer message",
    "delete files",
    "run this command",
    "execute this command",
)


class ContextPackError(ValueError):
    """Raised when a Creator Engine context pack cannot be safely built."""


@dataclass
class ContextPackPreviewResult:
    job_id: str
    source_recording_id: str
    context_pack_artifact_id: str
    job_status: str
    input_digest: str
    context_path: str
    context_markdown_path: str
    files_read: list[str] = field(default_factory=list)
    files_would_write: list[str] = field(default_factory=list)
    transcript: dict[str, Any] = field(default_factory=dict)
    source_recording: dict[str, Any] = field(default_factory=dict)
    context_items: list[dict[str, Any]] = field(default_factory=list)
    project_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    trust_summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "context_pack_artifact_id": self.context_pack_artifact_id,
            "job_status": self.job_status,
            "input_digest": self.input_digest,
            "context_path": self.context_path,
            "context_markdown_path": self.context_markdown_path,
            "files_read": list(self.files_read),
            "files_would_write": list(self.files_would_write),
            "transcript": dict(self.transcript),
            "source_recording": dict(self.source_recording),
            "context_items": [dict(item) for item in self.context_items],
            "project_refs": list(self.project_refs),
            "source_refs": list(self.source_refs),
            "trust_summary": dict(self.trust_summary),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class ContextPackBuildResult:
    job_id: str
    source_recording_id: str
    context_pack_artifact_id: str
    job: dict[str, Any]
    context_pack: dict[str, Any]
    files_read: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "context_pack_artifact_id": self.context_pack_artifact_id,
            "job": self.job,
            "context_pack": self.context_pack,
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class _ContextInputs:
    job: dict[str, Any]
    job_ref: str
    source_recording: dict[str, Any]
    source_recording_ref: str
    transcript_artifact: dict[str, Any]
    transcript_artifact_ref: str
    transcript_text: str
    transcript_ref: str
    context_items: list[dict[str, Any]]
    files_read: list[str]
    warnings: list[str]


def preview_context_pack(
    vault_root: str | Path,
    *,
    job_id: str,
    context_refs: list[str | Path] | None = None,
    context_prompt: str | None = None,
    job_store: CreatorJobStore | None = None,
    max_excerpt_chars: int = DEFAULT_EXCERPT_CHARS,
) -> ContextPackPreviewResult:
    """Validate and assemble context-pack metadata without writing artifacts."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root, create_root=False)
    inputs = _load_context_inputs(
        root,
        store,
        job_id,
        context_refs=context_refs,
        context_prompt=context_prompt,
        max_excerpt_chars=max_excerpt_chars,
    )
    paths = _context_pack_paths(root, store, job_id)
    input_digest = _context_input_digest(inputs)
    pack = _build_context_pack_payload(
        root=root,
        inputs=inputs,
        context_path=paths["json"],
        markdown_path=paths["markdown"],
        input_digest=input_digest,
        max_excerpt_chars=max_excerpt_chars,
    )
    return ContextPackPreviewResult(
        job_id=str(inputs.job.get("job_id", job_id)),
        source_recording_id=str(inputs.job.get("source_recording_id", "")),
        context_pack_artifact_id=str(pack["artifact_id"]),
        job_status=str(inputs.job.get("status", "")),
        input_digest=input_digest,
        context_path=relative_to_vault(root, paths["json"]),
        context_markdown_path=relative_to_vault(root, paths["markdown"]),
        files_read=inputs.files_read,
        files_would_write=[
            relative_to_vault(root, paths["json"]),
            relative_to_vault(root, paths["markdown"]),
            inputs.job_ref,
        ],
        transcript=pack["transcript"],
        source_recording=pack["source_recording"],
        context_items=pack["context_items"],
        project_refs=pack["project_refs"],
        source_refs=pack["source_refs"],
        trust_summary=pack["trust_summary"],
        warnings=pack["warnings"],
    )


def build_context_pack(
    vault_root: str | Path,
    *,
    job_id: str,
    context_refs: list[str | Path] | None = None,
    context_prompt: str | None = None,
    job_store: CreatorJobStore | None = None,
    max_excerpt_chars: int = DEFAULT_EXCERPT_CHARS,
) -> ContextPackBuildResult:
    """Write a runtime-local context pack for an existing transcript-ready job."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root)
    inputs = _load_context_inputs(
        root,
        store,
        job_id,
        context_refs=context_refs,
        context_prompt=context_prompt,
        max_excerpt_chars=max_excerpt_chars,
    )
    paths = _context_pack_paths(root, store, job_id)
    input_digest = _context_input_digest(inputs)
    pack = _build_context_pack_payload(
        root=root,
        inputs=inputs,
        context_path=paths["json"],
        markdown_path=paths["markdown"],
        input_digest=input_digest,
        max_excerpt_chars=max_excerpt_chars,
    )
    markdown = _render_context_pack_markdown(pack)

    json_path = store.write_artifact(
        job_id,
        "context/context_pack.json",
        pack,
        artifact_type="context_pack",
    )
    markdown_path = store.write_artifact(
        job_id,
        "context/context_pack.md",
        markdown,
        artifact_type="context_pack_markdown",
    )

    updated_job = store.load_job(job_id)
    updated_inputs = dict(updated_job.get("inputs", {}))
    updated_inputs.update(
        {
            "context_pack_input_digest": input_digest,
            "context_pack_built_from_transcript": True,
            "context_pack_excerpts_only": True,
            "context_refs": pack["declared_context_refs"],
            "context_prompt_included": bool(pack["operator_context_prompt"]),
            "source_intelligence_query_performed": False,
            "provider_call_performed": False,
            "canonical_writeback_performed": False,
        }
    )
    updated_job["status"] = "context_ready"
    updated_job["inputs"] = updated_inputs
    updated_job["warnings"] = list(dict.fromkeys([*updated_job.get("warnings", []), *pack["warnings"]]))
    job_path = store.save_job(updated_job)
    final_job = store.load_job(job_id)

    return ContextPackBuildResult(
        job_id=str(final_job.get("job_id", job_id)),
        source_recording_id=str(final_job.get("source_recording_id", "")),
        context_pack_artifact_id=str(pack["artifact_id"]),
        job=final_job,
        context_pack=pack,
        files_read=inputs.files_read,
        files_written=[
            relative_to_vault(root, json_path),
            relative_to_vault(root, markdown_path),
            relative_to_vault(root, job_path),
        ],
        warnings=pack["warnings"],
    )


def _load_context_inputs(
    root: Path,
    store: CreatorJobStore,
    job_id: str,
    *,
    context_refs: list[str | Path] | None,
    context_prompt: str | None,
    max_excerpt_chars: int,
) -> _ContextInputs:
    try:
        job = store.load_job(job_id)
    except Exception as exc:
        raise ContextPackError(f"Creator Engine job not found: {job_id}") from exc

    _ensure_no_existing_context_pack(root, store, job_id, job)
    if job.get("status") != "transcript_ready":
        raise ContextPackError("context pack can only be built for a transcript_ready Creator Engine job")
    if not job.get("source_recording_id"):
        raise ContextPackError("Creator Engine job is missing source_recording_id")

    source_recording_ref, source_recording = _read_job_json_artifact(
        root,
        store,
        job_id,
        "source_recording.json",
        missing_message="Creator Engine job is missing source_recording.json",
    )
    if source_recording.get("recording_id") != job.get("source_recording_id"):
        raise ContextPackError("source_recording.json id does not match the Creator Engine job")

    transcript_artifact_ref, transcript_artifact = _read_job_json_artifact(
        root,
        store,
        job_id,
        "transcripts/transcript_artifact.json",
        missing_message="Creator Engine job is missing transcript_artifact.json",
    )
    if transcript_artifact.get("job_id") != job.get("job_id"):
        raise ContextPackError("transcript_artifact.json job_id does not match the Creator Engine job")
    if transcript_artifact.get("source_recording_id") != job.get("source_recording_id"):
        raise ContextPackError("transcript_artifact.json source_recording_id does not match the job")

    transcript_path = artifact_path(root, job_id, "transcripts/transcript.raw.md", store.job_root)
    if not transcript_path.exists():
        raise ContextPackError("Creator Engine job is missing transcripts/transcript.raw.md")
    try:
        transcript_text = _normalize_text(transcript_path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise ContextPackError("Creator Engine transcript artifact must be UTF-8 text") from exc
    if not transcript_text:
        raise ContextPackError("Creator Engine transcript artifact is empty")
    transcript_ref = relative_to_vault(root, transcript_path)

    declared_context_refs = list(context_refs or [])
    context_items = [
        _read_declared_context_ref(root, ref, max_excerpt_chars=max_excerpt_chars)
        for ref in declared_context_refs
    ]

    resolved_context_prompt = _resolve_context_prompt(job, context_prompt)
    if resolved_context_prompt:
        context_items.append(_operator_context_prompt_item(resolved_context_prompt, max_excerpt_chars))

    files_read = [
        relative_to_vault(root, artifact_path(root, job_id, "job.json", store.job_root)),
        source_recording_ref,
        transcript_artifact_ref,
        transcript_ref,
        *[
            str(item["source_ref"])
            for item in context_items
            if item.get("source_kind") == "declared_context_file"
        ],
    ]
    warnings = list(
        dict.fromkeys(
            [
                *_content_warnings(transcript_text, "transcript"),
                *[
                    warning
                    for item in context_items
                    for warning in item.get("warnings", [])
                    if isinstance(warning, str)
                ],
            ]
        )
    )

    return _ContextInputs(
        job=job,
        job_ref=files_read[0],
        source_recording=source_recording,
        source_recording_ref=source_recording_ref,
        transcript_artifact=transcript_artifact,
        transcript_artifact_ref=transcript_artifact_ref,
        transcript_text=transcript_text,
        transcript_ref=transcript_ref,
        context_items=context_items,
        files_read=files_read,
        warnings=warnings,
    )


def _build_context_pack_payload(
    *,
    root: Path,
    inputs: _ContextInputs,
    context_path: Path,
    markdown_path: Path,
    input_digest: str,
    max_excerpt_chars: int,
) -> dict[str, Any]:
    transcript_digest = hashlib.sha256(inputs.transcript_text.encode("utf-8")).hexdigest()
    transcript_summary = {
        "source_ref": inputs.transcript_ref,
        "artifact_ref": inputs.transcript_artifact_ref,
        "artifact_id": inputs.transcript_artifact.get("artifact_id"),
        "status": inputs.transcript_artifact.get("status"),
        "word_count": _word_count(inputs.transcript_text),
        "content_sha256": transcript_digest,
        "excerpt": _excerpt(inputs.transcript_text, max_excerpt_chars),
        "excerpt_truncated": len(inputs.transcript_text) > max_excerpt_chars,
        "trust_tier": "tier-4",
    }
    source_recording_summary = {
        "source_ref": inputs.source_recording_ref,
        "recording_id": inputs.source_recording.get("recording_id"),
        "adapter": inputs.source_recording.get("adapter"),
        "media_kind": inputs.source_recording.get("media_kind"),
        "sha256": inputs.source_recording.get("sha256"),
        "path": inputs.source_recording.get("path"),
        "probe_status": inputs.source_recording.get("probe_status"),
        "trust_tier": inputs.source_recording.get("trust_tier", "tier-4"),
    }
    declared_context_refs = [
        str(item["source_ref"])
        for item in inputs.context_items
        if item.get("source_kind") == "declared_context_file"
    ]
    operator_context_prompt = next(
        (item for item in inputs.context_items if item.get("source_kind") == "operator_context_prompt"),
        None,
    )
    source_refs = list(
        dict.fromkeys(
            [
                inputs.source_recording_ref,
                inputs.transcript_artifact_ref,
                inputs.transcript_ref,
                *declared_context_refs,
                *(["operator_context_prompt"] if operator_context_prompt else []),
            ]
        )
    )
    trust_summary = {
        "source_recording_trust_tier": source_recording_summary["trust_tier"],
        "transcript_trust_tier": transcript_summary["trust_tier"],
        "declared_context_ref_count": len(declared_context_refs),
        "operator_context_prompt_present": operator_context_prompt is not None,
        "all_sources_operator_declared": True,
        "content_treated_as_untrusted": True,
        "provider_call_performed": False,
        "source_intelligence_query_performed": False,
        "rag_index_write_performed": False,
        "canonical_writeback_performed": False,
        "governed_memory_write_performed": False,
    }
    pack_model = ContextPack(
        artifact_id=f"context-pack-{input_digest[:12]}",
        job_id=str(inputs.job.get("job_id", "")),
        context_path=relative_to_vault(root, context_path),
        project_refs=_project_refs(inputs.context_items),
        source_refs=source_refs,
        trust_summary=trust_summary,
        status="draft",
    )
    payload = pack_model.to_dict()
    payload.update(
        {
            "context_markdown_path": relative_to_vault(root, markdown_path),
            "input_digest": input_digest,
            "source_recording": source_recording_summary,
            "transcript": transcript_summary,
            "context_items": inputs.context_items,
            "declared_context_refs": declared_context_refs,
            "operator_context_prompt": operator_context_prompt,
            "authority_flags": _context_authority_flags(),
            "blocked_future_actions": list(BLOCKED_FUTURE_ACTIONS),
            "transformation_chain": [
                {
                    "step": "load_transcript_ready_creator_job",
                    "job_ref": inputs.job_ref,
                    "external_call": False,
                },
                {
                    "step": "read_runtime_local_transcript_artifacts",
                    "transcript_ref": inputs.transcript_ref,
                    "external_call": False,
                },
                {
                    "step": "read_declared_context_refs",
                    "declared_context_ref_count": len(declared_context_refs),
                    "external_call": False,
                },
                {
                    "step": "write_runtime_local_context_pack",
                    "context_path": relative_to_vault(root, context_path),
                    "canonical_promotion": False,
                },
            ],
            "warnings": list(inputs.warnings),
            "blockers": [],
        }
    )
    return payload


def _render_context_pack_markdown(pack: dict[str, Any]) -> str:
    lines = [
        "# Creator Engine Context Pack",
        "",
        f"- Job: `{pack.get('job_id')}`",
        f"- Artifact: `{pack.get('artifact_id')}`",
        f"- Status: `{pack.get('status')}`",
        f"- Input digest: `{pack.get('input_digest')}`",
        "- Boundary: runtime-local review artifact only; no provider call, generation, publish, or canonical writeback.",
        "",
        "## Source Recording",
        "",
    ]
    source = pack.get("source_recording") or {}
    for key in ("recording_id", "adapter", "media_kind", "path", "sha256", "probe_status"):
        lines.append(f"- {key}: `{source.get(key)}`")
    transcript = pack.get("transcript") or {}
    lines.extend(
        [
            "",
            "## Transcript Excerpt",
            "",
            f"- Source: `{transcript.get('source_ref')}`",
            f"- Word count: `{transcript.get('word_count')}`",
            "",
            "```text",
            str(transcript.get("excerpt", "")).strip(),
            "```",
            "",
            "## Declared Context",
            "",
        ]
    )
    context_items = pack.get("context_items") or []
    if not context_items:
        lines.append("_No additional declared context files or prompt supplied._")
    for item in context_items:
        lines.extend(
            [
                f"### {item.get('source_ref')}",
                "",
                f"- Kind: `{item.get('source_kind')}`",
                f"- Trust tier: `{item.get('trust_tier')}`",
                f"- Word count: `{item.get('word_count')}`",
                f"- Content SHA-256: `{item.get('content_sha256')}`",
                "",
                "```text",
                str(item.get("excerpt", "")).strip(),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Authority Flags",
            "",
        ]
    )
    for key, value in (pack.get("authority_flags") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Source Refs", ""])
    for ref in pack.get("source_refs") or []:
        lines.append(f"- `{ref}`")
    return "\n".join(lines).rstrip() + "\n"


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
        raise ContextPackError(missing_message)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContextPackError(f"{relative_path} is not valid JSON") from exc
    if not isinstance(loaded, dict):
        raise ContextPackError(f"{relative_path} is not a JSON object")
    return relative_to_vault(root, path), loaded


def _read_declared_context_ref(
    root: Path,
    context_ref: str | Path,
    *,
    max_excerpt_chars: int,
) -> dict[str, Any]:
    path = _resolve_declared_context_ref(root, context_ref)
    _validate_context_ref(root, path)
    raw_bytes = path.read_bytes()
    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ContextPackError("declared context reference must be UTF-8 text") from exc

    normalized_text = _normalize_structured_context_text(path, raw_text)
    source_ref = relative_to_vault(root, path)
    return {
        "source_kind": "declared_context_file",
        "source_ref": source_ref,
        "suffix": path.suffix.lower(),
        "file_size_bytes": len(raw_bytes),
        "file_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "content_sha256": hashlib.sha256(normalized_text.encode("utf-8")).hexdigest(),
        "word_count": _word_count(normalized_text),
        "excerpt": _excerpt(normalized_text, max_excerpt_chars),
        "excerpt_truncated": len(normalized_text) > max_excerpt_chars,
        "trust_tier": "tier-4",
        "warnings": _content_warnings(normalized_text, source_ref),
    }


def _resolve_declared_context_ref(root: Path, context_ref: str | Path) -> Path:
    declared = Path(context_ref)
    candidate = declared.resolve() if declared.is_absolute() else (root / declared).resolve()
    try:
        return ensure_within(root, candidate)
    except ValueError as exc:
        raise ContextPackError(f"declared context reference is outside the vault: {context_ref}") from exc


def _validate_context_ref(root: Path, path: Path) -> None:
    if not path.exists():
        raise ContextPackError(f"declared context reference does not exist: {path}")
    if not path.is_file():
        raise ContextPackError(f"declared context reference is not a file: {path}")
    if path.suffix.lower() not in SUPPORTED_CONTEXT_SUFFIXES:
        raise ContextPackError(
            "declared context reference extension must be one of: "
            + ", ".join(sorted(SUPPORTED_CONTEXT_SUFFIXES))
        )
    if path.stat().st_size <= 0:
        raise ContextPackError("declared context reference is empty")
    if path.stat().st_size > MAX_CONTEXT_FILE_BYTES:
        raise ContextPackError("declared context reference exceeds the context-pack byte limit")

    relative_parts = [part.lower() for part in Path(relative_to_vault(root, path)).parts]
    if any(part in FORBIDDEN_CONTEXT_PATH_PARTS for part in relative_parts):
        raise ContextPackError("declared context reference crosses a forbidden secrets boundary")
    if any(part == ".env" or part.startswith(".env.") for part in relative_parts):
        raise ContextPackError("declared context reference crosses a forbidden environment boundary")


def _normalize_structured_context_text(path: Path, text: str) -> str:
    normalized = _normalize_text(text)
    if path.suffix.lower() != ".json":
        return normalized
    try:
        loaded = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ContextPackError("declared JSON context reference is not valid JSON") from exc
    return json.dumps(loaded, indent=2, sort_keys=True)


def _operator_context_prompt_item(prompt: str, max_excerpt_chars: int) -> dict[str, Any]:
    normalized = _normalize_text(prompt)
    if not normalized:
        raise ContextPackError("operator context prompt is empty")
    return {
        "source_kind": "operator_context_prompt",
        "source_ref": "operator_context_prompt",
        "file_size_bytes": len(normalized.encode("utf-8")),
        "file_sha256": None,
        "content_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "word_count": _word_count(normalized),
        "excerpt": _excerpt(normalized, max_excerpt_chars),
        "excerpt_truncated": len(normalized) > max_excerpt_chars,
        "trust_tier": "tier-4",
        "warnings": _content_warnings(normalized, "operator_context_prompt"),
    }


def _resolve_context_prompt(job: dict[str, Any], context_prompt: str | None) -> str | None:
    if context_prompt is not None:
        return context_prompt
    inputs = job.get("inputs", {})
    if isinstance(inputs, dict):
        existing = inputs.get("context_prompt")
        if isinstance(existing, str):
            return existing
    return None


def _ensure_no_existing_context_pack(
    root: Path,
    store: CreatorJobStore,
    job_id: str,
    job: dict[str, Any],
) -> None:
    artifacts = job.get("artifacts", {}) if isinstance(job.get("artifacts"), dict) else {}
    if artifacts.get("context_pack") or artifacts.get("context_pack_markdown"):
        raise ContextPackError("Creator Engine job already has context pack artifacts")
    context_paths = [
        artifact_path(root, job_id, "context/context_pack.json", store.job_root),
        artifact_path(root, job_id, "context/context_pack.md", store.job_root),
    ]
    if any(path.exists() for path in context_paths):
        raise ContextPackError("Creator Engine job already has context pack files")


def _context_pack_paths(root: Path, store: CreatorJobStore, job_id: str) -> dict[str, Path]:
    return {
        "json": artifact_path(root, job_id, "context/context_pack.json", store.job_root),
        "markdown": artifact_path(root, job_id, "context/context_pack.md", store.job_root),
    }


def _context_input_digest(inputs: _ContextInputs) -> str:
    digest_payload = {
        "job_id": inputs.job.get("job_id"),
        "source_recording_sha256": inputs.source_recording.get("sha256"),
        "transcript_sha256": hashlib.sha256(inputs.transcript_text.encode("utf-8")).hexdigest(),
        "context_items": [
            {
                "source_kind": item.get("source_kind"),
                "source_ref": item.get("source_ref"),
                "content_sha256": item.get("content_sha256"),
            }
            for item in inputs.context_items
        ],
    }
    serialized = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _context_authority_flags() -> dict[str, bool]:
    return {
        "runtime_local_write_allowed": True,
        "context_reference_read_allowed": True,
        "context_pack_write_allowed": True,
        "source_intelligence_query_allowed": False,
        "rag_index_write_allowed": False,
        "generation_allowed": False,
        "provider_call_allowed": False,
        "direct_publish_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
    }


def _project_refs(context_items: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for item in context_items:
        if item.get("source_kind") != "declared_context_file":
            continue
        source_ref = str(item.get("source_ref", ""))
        if source_ref.startswith(("01_PROJECTS/", "02_KNOWLEDGE/", "docs/")):
            refs.append(source_ref)
    return list(dict.fromkeys(refs))


def _normalize_text(text: str) -> str:
    body = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return f"{body}\n" if body else ""


def _excerpt(text: str, limit: int) -> str:
    normalized = _normalize_text(text)
    if len(normalized) <= limit:
        return normalized.rstrip()
    return normalized[:limit].rstrip()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _content_warnings(text: str, source_label: str) -> list[str]:
    lowered = text.lower()
    if any(pattern in lowered for pattern in INSTRUCTION_LIKE_PATTERNS):
        return [f"instruction_like_context_text_treated_as_untrusted_content:{source_label}"]
    return []
