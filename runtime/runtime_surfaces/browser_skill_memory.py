"""Read-only ARSL normalization for browser domain skill memory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.browser_skills.candidates import list_candidate_records, storage_reconciliation
from runtime.siteops.registry import load_registry

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


TRUSTED_SKILL_REL = Path("runtime/browser_skills/skills")
BROWSER_WORKFLOW_REL = Path("runtime/browser_workflows/workflows")


@dataclass(frozen=True)
class BrowserSkillMemoryRecord:
    """Sanitized read-only ARSL view of a browser skill memory object."""

    record_id: str
    source_type: str
    source_path: str
    domain: str | None
    status: str | None
    risk_level: str | None
    review_required: bool
    approval_required: bool
    activation_allowed: bool
    browser_execution_allowed: bool
    trusted_write_allowed: bool
    credential_access_allowed: bool
    browser_profile_allowed: bool
    raw_content_visible: bool
    promotion_allowed: bool
    declared_replay_allowed: bool | None = None
    refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "domain": self.domain,
            "status": self.status,
            "risk_level": self.risk_level,
            "review_required": self.review_required,
            "approval_required": self.approval_required,
            "activation_allowed": self.activation_allowed,
            "browser_execution_allowed": self.browser_execution_allowed,
            "trusted_write_allowed": self.trusted_write_allowed,
            "credential_access_allowed": self.credential_access_allowed,
            "browser_profile_allowed": self.browser_profile_allowed,
            "raw_content_visible": self.raw_content_visible,
            "promotion_allowed": self.promotion_allowed,
            "declared_replay_allowed": self.declared_replay_allowed,
            "refs": list(self.refs),
        }


@dataclass(frozen=True)
class BrowserSkillMemoryInventory:
    """Read-only inventory of browser domain skill memory objects."""

    schema_version: int
    records: tuple[BrowserSkillMemoryRecord, ...]
    storage: dict[str, Any]
    writes_performed: bool = False
    browser_execution_performed: bool = False
    promotion_performed: bool = False
    activation_performed: bool = False
    raw_content_visible: bool = False

    def records_by_type(self, source_type: str) -> list[BrowserSkillMemoryRecord]:
        return [record for record in self.records if record.source_type == source_type]

    def summary(self) -> dict[str, object]:
        counts: dict[str, int] = {}
        for record in self.records:
            counts[record.source_type] = counts.get(record.source_type, 0) + 1
        return {
            "schema_version": self.schema_version,
            "record_count": len(self.records),
            "counts_by_type": counts,
            "writes_performed": self.writes_performed,
            "browser_execution_performed": self.browser_execution_performed,
            "promotion_performed": self.promotion_performed,
            "activation_performed": self.activation_performed,
            "raw_content_visible": self.raw_content_visible,
            "storage_decision": self.storage.get("decision"),
            "siteops_boundary": self.storage.get("siteops_boundary"),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            **self.summary(),
            "storage": self.storage,
            "records": [record.to_dict() for record in self.records],
        }


def normalize_browser_skill_memory(root: str | Path | None = None) -> BrowserSkillMemoryInventory:
    """Return a sanitized browser skill memory inventory without promotion or execution."""

    vault_root = Path(root).resolve() if root is not None else _repo_root()
    records: list[BrowserSkillMemoryRecord] = []
    records.extend(_candidate_records(vault_root))
    records.extend(_trusted_skill_records(vault_root))
    records.extend(_siteops_records(vault_root))
    records.extend(_workflow_cache_records(vault_root))
    return BrowserSkillMemoryInventory(
        schema_version=1,
        records=tuple(sorted(records, key=lambda record: (record.source_type, record.record_id, record.source_path))),
        storage=storage_reconciliation(vault_root),
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _as_repo_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _candidate_records(root: Path) -> list[BrowserSkillMemoryRecord]:
    records: list[BrowserSkillMemoryRecord] = []
    for candidate in list_candidate_records(root):
        records.append(
            BrowserSkillMemoryRecord(
                record_id=str(candidate.get("candidate_id") or candidate.get("proposed_skill_id") or "candidate"),
                source_type="browser_skill_candidate",
                source_path=str(candidate.get("path") or ""),
                domain=_optional_text(candidate.get("domain")),
                status=_optional_text(candidate.get("status")),
                risk_level=_optional_text(candidate.get("risk_level")),
                review_required=bool(candidate.get("review_required", True)),
                approval_required=True,
                activation_allowed=False,
                browser_execution_allowed=False,
                trusted_write_allowed=False,
                credential_access_allowed=False,
                browser_profile_allowed=False,
                raw_content_visible=False,
                promotion_allowed=False,
                refs=tuple(str(item) for item in [candidate.get("source_run")] if item),
            )
        )
    return records


def _trusted_skill_records(root: Path) -> list[BrowserSkillMemoryRecord]:
    base = root / TRUSTED_SKILL_REL
    if not base.exists():
        return []
    records: list[BrowserSkillMemoryRecord] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.name.lower() == "readme.md" or path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        data = _load_mapping(path)
        record_id = str(data.get("skill_id") or path.stem)
        records.append(
            BrowserSkillMemoryRecord(
                record_id=record_id,
                source_type="browser_trusted_skill_draft",
                source_path=_as_repo_path(path, root),
                domain=_optional_text(data.get("domain")),
                status=_optional_text(data.get("status")),
                risk_level=_optional_text(data.get("risk_level")),
                review_required=True,
                approval_required=True,
                activation_allowed=False,
                browser_execution_allowed=False,
                trusted_write_allowed=False,
                credential_access_allowed=False,
                browser_profile_allowed=False,
                raw_content_visible=False,
                promotion_allowed=False,
                refs=tuple(str(item) for item in data.get("source_runs") or []),
            )
        )
    return records


def _siteops_records(root: Path) -> list[BrowserSkillMemoryRecord]:
    registry = load_registry(root)
    records: list[BrowserSkillMemoryRecord] = []
    for obj in registry.get("skill", []):
        records.append(
            BrowserSkillMemoryRecord(
                record_id=obj.object_id,
                source_type="siteops_skill_card",
                source_path=_as_repo_path(obj.path, root),
                domain=_optional_text(obj.data.get("site_profile")),
                status=_optional_text(obj.data.get("status")),
                risk_level=_optional_text(obj.data.get("risk_level")),
                review_required=True,
                approval_required=bool(obj.data.get("approval_points")),
                activation_allowed=False,
                browser_execution_allowed=False,
                trusted_write_allowed=False,
                credential_access_allowed=False,
                browser_profile_allowed=False,
                raw_content_visible=False,
                promotion_allowed=False,
                refs=tuple(str(item) for item in [obj.data.get("workflow_id"), obj.data.get("provider_profile")] if item),
            )
        )
    for obj in registry.get("workflow", []):
        records.append(
            BrowserSkillMemoryRecord(
                record_id=obj.object_id,
                source_type="siteops_workflow_manifest",
                source_path=_as_repo_path(obj.path, root),
                domain=_optional_text(obj.data.get("site_profile")),
                status=_optional_text(obj.data.get("live_execution_status") or obj.data.get("status")),
                risk_level=None,
                review_required=True,
                approval_required=bool(obj.data.get("approval_required")),
                activation_allowed=False,
                browser_execution_allowed=False,
                trusted_write_allowed=False,
                credential_access_allowed=False,
                browser_profile_allowed=False,
                raw_content_visible=False,
                promotion_allowed=False,
                refs=tuple(str(item) for item in [obj.data.get("provider_profile")] if item),
            )
        )
    return records


def _workflow_cache_records(root: Path) -> list[BrowserSkillMemoryRecord]:
    base = root / BROWSER_WORKFLOW_REL
    if not base.exists():
        return []
    records: list[BrowserSkillMemoryRecord] = []
    for path in sorted(base.glob("*.json")):
        if path.name.lower() == "readme.md":
            continue
        data = _load_mapping(path)
        records.append(
            BrowserSkillMemoryRecord(
                record_id=str(data.get("workflow_id") or path.stem),
                source_type="browser_workflow_cache",
                source_path=_as_repo_path(path, root),
                domain=_optional_text(data.get("domain")),
                status=_optional_text(data.get("status")),
                risk_level=None,
                review_required=bool(data.get("review_required", True)),
                approval_required=True,
                activation_allowed=False,
                browser_execution_allowed=False,
                trusted_write_allowed=False,
                credential_access_allowed=False,
                browser_profile_allowed=False,
                raw_content_visible=False,
                promotion_allowed=False,
                declared_replay_allowed=bool(data.get("replay_allowed", False)),
                refs=tuple(str(item) for item in [data.get("source_run_log_path")] if item),
            )
        )
    return records


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    elif yaml is not None:
        data = yaml.safe_load(text)
    else:
        data = {}
    return data if isinstance(data, dict) else {}


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
