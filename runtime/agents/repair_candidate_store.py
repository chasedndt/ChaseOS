"""Pending-review candidate store for execution repair memory.

This store records proposed runtime repair memories as append-only Pulse log
artifacts. It does not apply repair memory, update runtime navigation maps,
write Agent Identity Ledgers, create SOPs, expand permissions, or mutate
canonical state.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.pulse.card_schema import now_utc


REPAIR_CANDIDATE_ROOT = (
    Path("07_LOGS") / "Pulse-Decks" / "memory-candidates" / "runtime-repair"
)
PENDING_REVIEW = "pending_review"
REPAIR_CANDIDATE_STATUSES = {PENDING_REVIEW}
REPAIR_BLOCKED_EFFECTS = (
    "runtime_memory_mutation",
    "runtime_navigation_map_update",
    "agent_identity_ledger_update",
    "sop_creation",
    "tool_or_connector_grant",
    "permission_expansion",
    "knowledge_promotion",
    "canonical_writeback",
    "second_datastore_write",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _assert_inside(child: Path, parent: Path, message: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(message) from exc


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    if not slug or slug in {".", ".."} or ".." in slug:
        raise ValueError("repair candidate slug is invalid")
    return slug


def _date_slug(created_at: str) -> str:
    candidate = (created_at or now_utc())[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return now_utc()[:10]
    return candidate


def _candidate_id(entry: ExecutionRepairMemoryEntry, created_at: str, reason: str) -> str:
    seed = f"{entry.repair_id}|{entry.runtime_id}|{created_at}|{reason}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"repair-memory-candidate-{_safe_slug(entry.runtime_id)}-{digest}"


def _entry_from_dict(data: dict[str, Any] | ExecutionRepairMemoryEntry) -> ExecutionRepairMemoryEntry:
    if isinstance(data, ExecutionRepairMemoryEntry):
        return data
    payload = dict(data)
    pattern = payload.get("repair_pattern")
    if isinstance(pattern, dict):
        payload["repair_pattern"] = RepairPattern(**pattern)
    return ExecutionRepairMemoryEntry(**payload)


@dataclass
class ExecutionRepairMemoryCandidate:
    candidate_id: str
    runtime_id: str
    entry: ExecutionRepairMemoryEntry
    reason: str
    source_card_id: str | None = None
    source_feedback_candidate_id: str | None = None
    source_deck_path: str | None = None
    created_at: str = field(default_factory=now_utc)
    status: str = PENDING_REVIEW
    review_required: bool = True
    candidate_only: bool = True
    canonical_writeback_allowed: bool = False
    applied_to_runtime_memory: bool = False
    updates_runtime_navigation_map: bool = False
    updates_agent_identity_ledger: bool = False
    creates_sop: bool = False
    grants_tool_or_connector: bool = False
    expands_permissions: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False

    def validate(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.runtime_id:
            raise ValueError("runtime_id is required")
        if not self.reason:
            raise ValueError("candidate reason is required")
        if self.status not in REPAIR_CANDIDATE_STATUSES:
            raise ValueError(f"status must be one of {sorted(REPAIR_CANDIDATE_STATUSES)}")
        self.entry.validate()
        if self.entry.runtime_id != self.runtime_id:
            raise ValueError("candidate runtime_id must match repair entry runtime_id")
        if not self.review_required:
            raise ValueError("repair memory candidates require review")
        if not self.candidate_only:
            raise ValueError("repair memory candidates must remain candidate-only")
        if self.canonical_writeback_allowed:
            raise ValueError("repair memory candidates cannot allow canonical writeback")
        if self.applied_to_runtime_memory:
            raise ValueError("repair memory candidates cannot be applied by this store")
        if self.updates_runtime_navigation_map:
            raise ValueError("repair memory candidates cannot update runtime navigation maps")
        if self.updates_agent_identity_ledger:
            raise ValueError("repair memory candidates cannot update identity ledgers")
        if self.creates_sop:
            raise ValueError("repair memory candidates cannot create SOPs")
        if self.grants_tool_or_connector:
            raise ValueError("repair memory candidates cannot grant tools or connectors")
        if self.expands_permissions:
            raise ValueError("repair memory candidates cannot expand permissions")
        if self.mutates_canonical_state:
            raise ValueError("repair memory candidates cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("repair memory candidates cannot write a second datastore")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionRepairMemoryCandidate":
        candidate = cls(
            candidate_id=str(data.get("candidate_id") or ""),
            runtime_id=str(data.get("runtime_id") or ""),
            entry=_entry_from_dict(data.get("entry") or {}),
            reason=str(data.get("reason") or ""),
            source_card_id=data.get("source_card_id"),
            source_feedback_candidate_id=data.get("source_feedback_candidate_id"),
            source_deck_path=data.get("source_deck_path"),
            created_at=str(data.get("created_at") or now_utc()),
            status=str(data.get("status") or PENDING_REVIEW),
            review_required=bool(data.get("review_required", True)),
            candidate_only=bool(data.get("candidate_only", True)),
            canonical_writeback_allowed=bool(data.get("canonical_writeback_allowed", False)),
            applied_to_runtime_memory=bool(data.get("applied_to_runtime_memory", False)),
            updates_runtime_navigation_map=bool(
                data.get("updates_runtime_navigation_map", False)
            ),
            updates_agent_identity_ledger=bool(data.get("updates_agent_identity_ledger", False)),
            creates_sop=bool(data.get("creates_sop", False)),
            grants_tool_or_connector=bool(data.get("grants_tool_or_connector", False)),
            expands_permissions=bool(data.get("expands_permissions", False)),
            mutates_canonical_state=bool(data.get("mutates_canonical_state", False)),
            second_datastore_write_allowed=bool(
                data.get("second_datastore_write_allowed", False)
            ),
        )
        candidate.validate()
        return candidate


@dataclass
class ExecutionRepairMemoryCandidateArtifact:
    path: str
    candidate_id: str
    runtime_id: str
    status: str = PENDING_REVIEW
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False

    def validate(self) -> None:
        if not self.path:
            raise ValueError("repair candidate artifact path is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.runtime_id:
            raise ValueError("runtime_id is required")
        if self.status != PENDING_REVIEW:
            raise ValueError("repair candidate artifacts are pending review only")
        if self.canonical_writeback_allowed:
            raise ValueError("repair candidate artifacts cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("repair candidate artifacts cannot write a second datastore")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class ExecutionRepairMemoryCandidateQueue:
    generated_at: str = field(default_factory=now_utc)
    items: list[ExecutionRepairMemoryCandidate] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    queue_status: str = "read_only"
    writes: list[str] = field(default_factory=list)
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False
    blocked_effects: tuple[str, ...] = REPAIR_BLOCKED_EFFECTS

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def pending_count(self) -> int:
        return sum(1 for item in self.items if item.status == PENDING_REVIEW)

    def validate(self) -> None:
        if self.queue_status != "read_only":
            raise ValueError("repair memory candidate queue is read-only")
        if self.writes:
            raise ValueError("repair memory candidate queue cannot declare writes")
        if self.canonical_writeback_allowed:
            raise ValueError("repair memory candidate queue cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("repair memory candidate queue cannot write a second datastore")
        if set(self.blocked_effects) != set(REPAIR_BLOCKED_EFFECTS):
            raise ValueError("repair memory candidate queue must declare blocked effects")
        for item in self.items:
            item.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "queue_status": self.queue_status,
            "item_count": self.item_count,
            "pending_count": self.pending_count,
            "source_log_paths": list(self.source_log_paths),
            "writes": list(self.writes),
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "blocked_effects": list(self.blocked_effects),
            "items": [item.to_dict() for item in self.items],
        }


def build_execution_repair_memory_candidate(
    entry: ExecutionRepairMemoryEntry,
    *,
    reason: str,
    source_card_id: str | None = None,
    source_feedback_candidate_id: str | None = None,
    source_deck_path: str | None = None,
    created_at: str | None = None,
) -> ExecutionRepairMemoryCandidate:
    entry.validate()
    timestamp = created_at or now_utc()
    candidate = ExecutionRepairMemoryCandidate(
        candidate_id=_candidate_id(entry, timestamp, reason),
        runtime_id=entry.runtime_id,
        entry=entry,
        reason=reason,
        source_card_id=source_card_id,
        source_feedback_candidate_id=source_feedback_candidate_id,
        source_deck_path=source_deck_path,
        created_at=timestamp,
    )
    candidate.validate()
    return candidate


def repair_candidate_log_path(
    vault_root: str | Path,
    runtime_id: str,
    *,
    created_at: str | None = None,
) -> Path:
    vault = _vault_path(vault_root)
    root = (vault / REPAIR_CANDIDATE_ROOT / _safe_slug(runtime_id)).resolve()
    path = root / f"{_date_slug(created_at or now_utc())}-repair-candidates.jsonl"
    _assert_inside(path, root, "repair candidate logs must stay inside runtime-repair/")
    return path


def persist_execution_repair_memory_candidate(
    vault_root: str | Path,
    candidate: ExecutionRepairMemoryCandidate,
) -> ExecutionRepairMemoryCandidateArtifact:
    candidate.validate()
    vault = _vault_path(vault_root)
    path = repair_candidate_log_path(
        vault,
        candidate.runtime_id,
        created_at=candidate.created_at,
    )
    root = (vault / REPAIR_CANDIDATE_ROOT / _safe_slug(candidate.runtime_id)).resolve()
    _assert_inside(path, root, "repair candidate logs must stay inside runtime-repair/")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(candidate.to_dict(), sort_keys=True))
        handle.write("\n")

    artifact = ExecutionRepairMemoryCandidateArtifact(
        path=_relative_to_vault(vault, path),
        candidate_id=candidate.candidate_id,
        runtime_id=candidate.runtime_id,
        status=candidate.status,
        canonical_writeback_allowed=False,
        second_datastore_write_allowed=False,
    )
    artifact.validate()
    return artifact


def load_execution_repair_memory_candidates(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    log_path: str | Path | None = None,
) -> list[ExecutionRepairMemoryCandidate]:
    vault = _vault_path(vault_root)
    root = (vault / REPAIR_CANDIDATE_ROOT).resolve()
    if log_path is not None:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        _assert_inside(target, root, "repair candidate logs must stay inside runtime-repair/")
        paths = [target]
    elif runtime_id is not None:
        runtime_root = (root / _safe_slug(runtime_id)).resolve()
        paths = sorted(runtime_root.glob("*-repair-candidates.jsonl")) if runtime_root.exists() else []
    else:
        paths = sorted(root.glob("*/*-repair-candidates.jsonl")) if root.exists() else []

    candidates: list[ExecutionRepairMemoryCandidate] = []
    for path in paths:
        if not path.exists():
            continue
        _assert_inside(path, root, "repair candidate logs must stay inside runtime-repair/")
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                candidates.append(ExecutionRepairMemoryCandidate.from_dict(json.loads(line)))
    return candidates


def _source_log_paths(vault: Path, runtime_id: str | None, log_path: str | Path | None) -> list[str]:
    root = (vault / REPAIR_CANDIDATE_ROOT).resolve()
    if log_path is not None:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        return [_relative_to_vault(vault, target)]
    if not root.exists():
        return []
    if runtime_id is not None:
        runtime_root = (root / _safe_slug(runtime_id)).resolve()
        paths = (
            sorted(runtime_root.glob("*-repair-candidates.jsonl"))
            if runtime_root.exists()
            else []
        )
    else:
        paths = sorted(root.glob("*/*-repair-candidates.jsonl"))
    return [_relative_to_vault(vault, path) for path in paths]


def build_execution_repair_memory_candidate_queue(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    log_path: str | Path | None = None,
) -> ExecutionRepairMemoryCandidateQueue:
    vault = _vault_path(vault_root)
    items = [
        item
        for item in load_execution_repair_memory_candidates(
            vault,
            runtime_id=runtime_id,
            log_path=log_path,
        )
        if item.status == PENDING_REVIEW
    ]
    queue = ExecutionRepairMemoryCandidateQueue(
        items=items,
        source_log_paths=_source_log_paths(vault, runtime_id, log_path),
    )
    queue.validate()
    return queue
