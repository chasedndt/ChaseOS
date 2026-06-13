"""Runtime-local Creator Engine job store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import BLOCKED_FUTURE_ACTIONS, CreatorJob, MVP_SOURCE_ADAPTERS, new_id, utc_now
from .path_policy import (
    artifact_path,
    job_directory,
    relative_to_vault,
    resolve_job_root,
    resolve_vault_root,
    safe_slug,
)


class CreatorJobStoreError(RuntimeError):
    """Fail-closed job store error."""


class CreatorJobStore:
    """Persist Creator Engine jobs under the runtime-local job root."""

    def __init__(
        self,
        vault_root: str | Path,
        job_root: str | Path | None = None,
        *,
        create_root: bool = True,
    ) -> None:
        self.vault_root = resolve_vault_root(vault_root)
        self.job_root = resolve_job_root(self.vault_root, job_root)
        if create_root:
            self.job_root.mkdir(parents=True, exist_ok=True)

    def create_job(
        self,
        *,
        source_adapter: str,
        source_recording_id: str,
        target_platforms: list[str] | None = None,
        inputs: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        blockers: list[str] | None = None,
        job_id: str | None = None,
    ) -> CreatorJob:
        if source_adapter not in MVP_SOURCE_ADAPTERS:
            raise CreatorJobStoreError(f"unsupported Creator Engine source adapter: {source_adapter}")
        resolved_job_id = safe_slug(job_id or new_id("creator-job"))
        directory = job_directory(self.vault_root, resolved_job_id, self.job_root, create=True)
        job = CreatorJob(
            job_id=resolved_job_id,
            source_adapter=source_adapter,
            source_recording_id=source_recording_id,
            artifact_root=relative_to_vault(self.vault_root, directory),
            target_platforms=list(target_platforms or []),
            inputs=dict(inputs or {}),
            warnings=list(warnings or []),
            blockers=list(blockers or []),
        )
        job.artifacts["blocked_future_actions"] = list(BLOCKED_FUTURE_ACTIONS)
        self.save_job(job)
        return job

    def save_job(self, job: CreatorJob | dict[str, Any]) -> Path:
        data = job.to_dict() if isinstance(job, CreatorJob) else dict(job)
        if "job_id" not in data:
            raise CreatorJobStoreError("job record missing job_id")
        data["updated_at"] = utc_now()
        path = artifact_path(self.vault_root, str(data["job_id"]), "job.json", self.job_root, create_parent=True)
        _write_json(path, data)
        return path

    def load_job(self, job_id: str) -> dict[str, Any]:
        path = artifact_path(self.vault_root, job_id, "job.json", self.job_root)
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CreatorJobStoreError(f"Creator Engine job not found: {job_id}") from exc
        if not isinstance(loaded, dict):
            raise CreatorJobStoreError(f"Creator Engine job is not a JSON object: {job_id}")
        return loaded

    def list_jobs(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        if not self.job_root.exists():
            return jobs
        for path in sorted(self.job_root.glob("*/job.json")):
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                jobs.append(loaded)
        return sorted(jobs, key=lambda item: str(item.get("created_at", "")))

    def write_artifact(
        self,
        job_id: str,
        relative_path: str | Path,
        payload: dict[str, Any] | list[Any] | str,
        *,
        artifact_type: str | None = None,
    ) -> Path:
        path = artifact_path(self.vault_root, job_id, relative_path, self.job_root, create_parent=True)
        if isinstance(payload, (dict, list)):
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        else:
            path.write_text(payload, encoding="utf-8")
        if artifact_type:
            self.register_artifact(job_id, artifact_type, relative_to_vault(self.vault_root, path))
        return path

    def register_artifact(self, job_id: str, artifact_type: str, artifact_ref: str) -> Path:
        job = self.load_job(job_id)
        artifacts = job.setdefault("artifacts", {})
        refs = artifacts.setdefault(artifact_type, [])
        if artifact_ref not in refs:
            refs.append(artifact_ref)
        return self.save_job(job)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
