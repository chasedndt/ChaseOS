"""Local-only Pulse source candidate preview.

The preview scans bounded, declared ChaseOS source artifact folders by path and
file metadata only. It does not read source content, call connectors/providers,
browse, ingest browser history, activate schedules, promote sources, or write
canonical state.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.connector_source_scanner_readiness import (
    BLOCKED_EFFECTS,
    build_pulse_connector_source_scanner_readiness,
)


PREVIEW_ROOT = Path("07_LOGS") / "Pulse-Decks" / "source-scanner-preview"
DEFAULT_LIMIT = 40
MAX_LIMIT = 100

ALLOWED_EXTENSIONS = {
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".html",
    ".htm",
    ".pdf",
    ".yaml",
    ".yml",
    ".csv",
}

SKIP_DIRS = {
    "__pycache__",
    ".pytest_cache",
    "_tmp_pytest",
    "_tmp_cli_test",
    "_tmp_signal_driven_decks",
    "_tmp_feedback_candidates",
    "_tmp_feedback_review_queue",
    "_tmp_local_surface",
    "_tmp_memory_runtime_readiness",
    "_tmp_multi_audience_decks",
    "_tmp_native_schedule_activation_proof",
}

PREVIEW_SURFACES = (
    (
        "pulse_decks",
        "07_LOGS/Pulse-Decks",
        "pulse_deck_or_review_artifact",
        ("Pulse Card", "Review Queue"),
    ),
    (
        "source_intelligence",
        "runtime/source_intelligence",
        "source_intelligence_artifact",
        ("Research Watch", "Source Conflict"),
    ),
    (
        "capture_inputs",
        "03_INPUTS",
        "captured_input_artifact",
        ("Research Watch", "Manual Input Needed"),
    ),
    (
        "build_logs",
        "07_LOGS/Build-Logs",
        "build_log_artifact",
        ("Project Momentum", "Truth-State Warning"),
    ),
    (
        "agent_activity",
        "07_LOGS/Agent-Activity",
        "agent_activity_artifact",
        ("Runtime Reflection", "Error Cluster"),
    ),
    (
        "acquisition_runtime",
        "runtime/acquisition",
        "acquisition_artifact",
        ("Research Watch", "Source Conflict"),
    ),
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _assert_inside(child: Path, parent: Path, message: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(message) from exc


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _candidate_id(rel_path: str, *, size_bytes: int, modified_at: str) -> str:
    digest = hashlib.sha256(f"{rel_path}|{size_bytes}|{modified_at}".encode("utf-8")).hexdigest()
    return f"source-candidate-{digest[:16]}"


def _source_class_for(surface_id: str, suffix: str) -> str:
    if surface_id == "pulse_decks":
        return "pulse_artifact"
    if surface_id == "source_intelligence":
        return "source_intelligence_local"
    if surface_id == "capture_inputs":
        if suffix == ".html" or suffix == ".htm":
            return "operator_supplied_html_file"
        if suffix == ".pdf":
            return "local_document"
        return "local_captured_input"
    if surface_id == "build_logs":
        return "build_log"
    if surface_id == "agent_activity":
        return "agent_activity_log"
    if surface_id == "acquisition_runtime":
        return "acquisition_local_artifact"
    return "local_file"


def _iter_surface_files(vault: Path, rel_root: str, *, limit: int) -> list[Path]:
    root = (vault / rel_root).resolve()
    if not root.exists():
        return []
    _assert_inside(root, vault, "source preview root must stay inside vault")
    candidates: list[Path] = []
    for current, dirs, files in os.walk(root, onerror=lambda _error: None):
        dirs[:] = [
            name
            for name in dirs
            if name not in SKIP_DIRS and not name.startswith("tmp") and name != "__pycache__"
        ]
        for name in files:
            path = Path(current) / name
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            candidates.append(path)
            if len(candidates) >= limit * 3:
                break
        if len(candidates) >= limit * 3:
            break
    candidates.sort(key=lambda path: (path.stat().st_mtime, path.as_posix()), reverse=True)
    return candidates[:limit]


@dataclass(frozen=True)
class PulseSourcePreviewCandidate:
    candidate_id: str
    source_surface_id: str
    source_path: str
    source_class: str
    artifact_kind: str
    file_name: str
    extension: str
    size_bytes: int
    modified_at: str
    recommended_card_classes: tuple[str, ...]
    approval_required_for_use: bool = False
    live_connector_required: bool = False
    source_content_read: bool = False
    preview_status: str = "candidate_previewed"

    def validate(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.source_surface_id:
            raise ValueError("source_surface_id is required")
        if not self.source_path:
            raise ValueError("source_path is required")
        if not self.source_class:
            raise ValueError("source_class is required")
        if self.source_content_read:
            raise ValueError("local preview cannot read source content")
        if self.live_connector_required:
            raise ValueError("local preview cannot require live connector execution")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["recommended_card_classes"] = list(self.recommended_card_classes)
        return data


@dataclass(frozen=True)
class PulseConnectorSourceScannerLocalPreview:
    generated_at: str
    preview_status: str
    candidates: tuple[PulseSourcePreviewCandidate, ...]
    source_surface_count: int
    scanned_surface_count: int
    readiness_status: str
    limit: int
    next_recommended_pass: str = "chaseos-pulse-connector-source-scanner-candidate-cards"
    read_only: bool = True
    local_only: bool = True
    source_content_read: bool = False
    writes_artifacts: bool = False
    live_connector_execution_enabled: bool = False
    provider_or_connector_call_allowed: bool = False
    unrestricted_web_scan_allowed: bool = False
    browser_history_ingest_allowed: bool = False
    credential_or_secret_read_allowed: bool = False
    schedule_activation_allowed: bool = False
    approval_execution_allowed: bool = False
    memory_approval_allowed: bool = False
    autonomous_promotion_allowed: bool = False
    canonical_writeback_allowed: bool = False
    rd_workbook_update_allowed: bool = False
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    writes: tuple[str, ...] = ()

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    def validate(self) -> None:
        if self.preview_status not in {"ready", "empty", "partial"}:
            raise ValueError("invalid source scanner preview_status")
        for candidate in self.candidates:
            candidate.validate()
        if not self.read_only and not self.writes_artifacts:
            raise ValueError("non-read-only preview must only be artifact-writing mode")
        if self.source_content_read:
            raise ValueError("local preview cannot read source content")
        if self.live_connector_execution_enabled:
            raise ValueError("local preview cannot enable live connector execution")
        if self.provider_or_connector_call_allowed:
            raise ValueError("local preview cannot call providers/connectors")
        if self.unrestricted_web_scan_allowed:
            raise ValueError("local preview cannot allow unrestricted web scan")
        if self.browser_history_ingest_allowed:
            raise ValueError("local preview cannot ingest browser history")
        if self.credential_or_secret_read_allowed:
            raise ValueError("local preview cannot read credentials or secrets")
        if self.schedule_activation_allowed:
            raise ValueError("local preview cannot activate schedules")
        if self.approval_execution_allowed:
            raise ValueError("local preview cannot execute approvals")
        if self.memory_approval_allowed:
            raise ValueError("local preview cannot approve memory")
        if self.autonomous_promotion_allowed:
            raise ValueError("local preview cannot autonomously promote sources")
        if self.canonical_writeback_allowed:
            raise ValueError("local preview cannot write canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("local preview cannot update the R&D workbook")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("local preview must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "preview_status": self.preview_status,
            "candidate_count": self.candidate_count,
            "source_surface_count": self.source_surface_count,
            "scanned_surface_count": self.scanned_surface_count,
            "readiness_status": self.readiness_status,
            "limit": self.limit,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "next_recommended_pass": self.next_recommended_pass,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "source_content_read": self.source_content_read,
            "writes_artifacts": self.writes_artifacts,
            "live_connector_execution_enabled": self.live_connector_execution_enabled,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "unrestricted_web_scan_allowed": self.unrestricted_web_scan_allowed,
            "browser_history_ingest_allowed": self.browser_history_ingest_allowed,
            "credential_or_secret_read_allowed": self.credential_or_secret_read_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "approval_execution_allowed": self.approval_execution_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "autonomous_promotion_allowed": self.autonomous_promotion_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "blocked_effects": list(self.blocked_effects),
            "writes": list(self.writes),
        }


def build_pulse_connector_source_scanner_local_preview(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> PulseConnectorSourceScannerLocalPreview:
    """Build local source candidates from metadata only, without writes."""

    if limit < 1:
        raise ValueError("limit must be at least 1")
    bounded_limit = min(limit, MAX_LIMIT)
    vault = _vault_path(vault_root)
    readiness = build_pulse_connector_source_scanner_readiness(vault)

    candidates: list[PulseSourcePreviewCandidate] = []
    scanned_surfaces = 0
    per_surface_limit = max(1, bounded_limit // max(1, len(PREVIEW_SURFACES)))
    for surface_id, rel_root, artifact_kind, card_classes in PREVIEW_SURFACES:
        files = _iter_surface_files(vault, rel_root, limit=per_surface_limit)
        if files:
            scanned_surfaces += 1
        for path in files:
            stat = path.stat()
            rel_path = _relative_to_vault(vault, path)
            modified_at = _mtime_iso(path)
            suffix = path.suffix.lower()
            candidates.append(
                PulseSourcePreviewCandidate(
                    candidate_id=_candidate_id(
                        rel_path,
                        size_bytes=stat.st_size,
                        modified_at=modified_at,
                    ),
                    source_surface_id=surface_id,
                    source_path=rel_path,
                    source_class=_source_class_for(surface_id, suffix),
                    artifact_kind=artifact_kind,
                    file_name=path.name,
                    extension=suffix,
                    size_bytes=stat.st_size,
                    modified_at=modified_at,
                    recommended_card_classes=tuple(card_classes),
                )
            )

    candidates.sort(key=lambda item: (item.modified_at, item.source_path), reverse=True)
    candidates = candidates[:bounded_limit]
    status = "ready" if candidates else "empty"
    preview = PulseConnectorSourceScannerLocalPreview(
        generated_at=generated_at or now_utc(),
        preview_status=status,
        candidates=tuple(candidates),
        source_surface_count=readiness.source_surface_count,
        scanned_surface_count=scanned_surfaces,
        readiness_status=readiness.readiness_status,
        limit=bounded_limit,
    )
    preview.validate()
    return preview


def write_pulse_connector_source_scanner_local_preview(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    limit: int = DEFAULT_LIMIT,
    output_path: str | Path | None = None,
) -> PulseConnectorSourceScannerLocalPreview:
    """Write local preview JSON under Pulse logs only when explicitly requested."""

    vault = _vault_path(vault_root)
    preview = build_pulse_connector_source_scanner_local_preview(
        vault,
        generated_at=generated_at,
        limit=limit,
    )
    date_slug = (preview.generated_at or now_utc())[:10]
    preview_root = (vault / PREVIEW_ROOT).resolve()
    target = (
        (vault / output_path).resolve()
        if output_path is not None
        else preview_root / f"{date_slug}-source-scanner-local-preview.json"
    )
    _assert_inside(target, preview_root, "source scanner preview output must stay under Pulse preview logs")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = preview.to_dict()
    payload["read_only"] = False
    payload["writes_artifacts"] = True
    payload["writes"] = [_relative_to_vault(vault, target)]
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    written = PulseConnectorSourceScannerLocalPreview(
        generated_at=preview.generated_at,
        preview_status=preview.preview_status,
        candidates=preview.candidates,
        source_surface_count=preview.source_surface_count,
        scanned_surface_count=preview.scanned_surface_count,
        readiness_status=preview.readiness_status,
        limit=preview.limit,
        read_only=False,
        writes_artifacts=True,
        writes=(_relative_to_vault(vault, target),),
    )
    written.validate()
    return written
