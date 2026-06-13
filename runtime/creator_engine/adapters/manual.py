"""Manual file adapter for Creator Engine media references."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .base import AdapterValidationResult, RecordingCandidate
from ..media_reference import MediaReferenceError, read_declared_media_reference


class ManualFileRecordingAdapter:
    """Validate one operator-declared media file without copying or probing it."""

    adapter_id = "manual_file"

    def __init__(self, vault_root: str | Path) -> None:
        self.vault_root = Path(vault_root)

    def discover(self, source: str | Path) -> Iterable[RecordingCandidate]:
        try:
            media = read_declared_media_reference(self.vault_root, source)
        except MediaReferenceError:
            return []
        return [
            RecordingCandidate(
                source_ref=media.source_ref,
                adapter_id=self.adapter_id,
                media_kind=media.media_kind,
                metadata={
                    "file_size_bytes": media.file_size_bytes,
                    "sha256": media.file_digest,
                    "copied_media": False,
                    "probe_status": "not_probed",
                },
            )
        ]

    def validate(self, candidate: RecordingCandidate) -> AdapterValidationResult:
        blockers: list[str] = []
        if candidate.adapter_id != self.adapter_id:
            blockers.append("candidate adapter_id is not manual_file")
        if candidate.media_kind not in {"audio", "video"}:
            blockers.append("manual_file candidate must be audio or video")
        if not candidate.metadata.get("sha256"):
            blockers.append("manual_file candidate is missing sha256 metadata")
        if candidate.metadata.get("copied_media") is not False:
            blockers.append("manual_file candidate must not copy media")
        if candidate.metadata.get("probe_status") != "not_probed":
            blockers.append("manual_file candidate must remain not_probed in Pass 5")
        return AdapterValidationResult(
            ok=not blockers,
            normalized_source=None if blockers else candidate,
            blockers=blockers,
        )
