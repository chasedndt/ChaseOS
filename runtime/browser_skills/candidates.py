"""Read-only inspection helpers for Browser Operator Skill candidates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .registry import detect_vault_root, load_yaml_file
from .validator import REQUIRED_FIELDS, validate_skill

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback covers environments without PyYAML
    yaml = None


CANDIDATE_REL = Path("03_INPUTS") / "Browser-Skill-Candidates"
BROWSER_RUN_REL = Path("07_LOGS") / "Browser-Runs"
TRUSTED_SKILL_REL = Path("runtime") / "browser_skills" / "skills"
SITEOPS_SKILL_CARD_REL = Path("runtime") / "siteops" / "registry" / "skill_cards"
SITE_ACTIVITY_LEDGER_REL = Path("07_LOGS") / "Site-Activity" / "site-memory-ledger.json"
SITEOPS_APPROVAL_REL = Path("07_LOGS") / "SiteOps-Approvals"
SITEOPS_RUN_REL = Path("07_LOGS") / "SiteOps-Runs"
SITEOPS_AUDIT_REL = Path("07_LOGS") / "SiteOps-Audits"

DEFAULT_SITEOPS_SCOPE = {
    "tenant_id": "local",
    "workspace_id": "default",
    "user_id": "local-user",
}

SAFE_METADATA_FIELDS = {
    "activation_allowed",
    "allowed_domains",
    "approval_status",
    "canonical_writeback",
    "credentials_required",
    "domain",
    "intent",
    "mode",
    "review_required",
    "risk_level",
    "skill_id",
    "source_run",
    "status",
    "trust_tier",
}


class BrowserSkillCandidateError(ValueError):
    """Raised when read-only candidate inspection cannot satisfy a request."""


@dataclass(frozen=True)
class CandidateValidationSummary:
    checked: bool
    ok: bool | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _vault_root(root: Path | str | None = None) -> Path:
    return Path(root) if root else detect_vault_root()


def candidate_dir(root: Path | str | None = None) -> Path:
    return _vault_root(root) / CANDIDATE_REL


def browser_run_dir(root: Path | str | None = None) -> Path:
    return _vault_root(root) / BROWSER_RUN_REL


def trusted_skill_dir(root: Path | str | None = None) -> Path:
    return _vault_root(root) / TRUSTED_SKILL_REL


def siteops_skill_card_dir(root: Path | str | None = None) -> Path:
    return _vault_root(root) / SITEOPS_SKILL_CARD_REL


def _as_repo_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _parse_mapping_text(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    if yaml is None:
        return {}
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def _parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return _parse_mapping_text("\n".join(lines[1:index]))
    return {}


def _extract_machine_candidate(text: str) -> dict[str, Any]:
    marker_index = text.find("## Machine Candidate")
    search_text = text[marker_index:] if marker_index >= 0 else text
    block_start = search_text.find("```json")
    if block_start < 0:
        return {}
    content_start = search_text.find("\n", block_start)
    if content_start < 0:
        return {}
    content_end = search_text.find("```", content_start + 1)
    if content_end < 0:
        return {}
    try:
        data = json.loads(search_text[content_start:content_end].strip())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_heading_candidate_id(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# Browser Skill Candidate - "):
            return line.replace("# Browser Skill Candidate - ", "", 1).strip() or None
    return None


def _load_candidate(path: Path) -> tuple[str, dict[str, Any], dict[str, Any], str | None]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise BrowserSkillCandidateError(f"candidate JSON is not a mapping: {path}")
        return "json", {}, data, data.get("candidate_id")
    if suffix in {".yaml", ".yml"}:
        data = load_yaml_file(path)
        return "yaml", {}, data, data.get("candidate_id")
    if suffix == ".md":
        text = path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(text)
        machine = _extract_machine_candidate(text)
        return "markdown", frontmatter, machine, _extract_heading_candidate_id(text)
    raise BrowserSkillCandidateError(f"unsupported candidate file type: {path.suffix}")


def iter_candidate_paths(root: Path | str | None = None) -> list[Path]:
    """Return candidate files from the canonical untrusted candidate folder."""
    directory = candidate_dir(root)
    if not directory.exists():
        return []
    suffixes = {".md", ".json", ".yaml", ".yml"}
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in suffixes
        and path.name.lower() != "readme.md"
    )


def _candidate_validation(data: dict[str, Any]) -> CandidateValidationSummary:
    if not data:
        return CandidateValidationSummary(checked=False)
    result = validate_skill(data, candidate=True)
    return CandidateValidationSummary(
        checked=True,
        ok=result.ok,
        errors=result.errors,
        warnings=result.warnings,
    )


def _slug(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in clean.split("-") if part)


def _id_slug(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    return "_".join(part for part in clean.split("_") if part) or "candidate"


def _scope_with_defaults(
    *,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    user_id: str | None = None,
    requested_by: str | None = None,
) -> dict[str, Any]:
    scope = {
        "tenant_id": (tenant_id or DEFAULT_SITEOPS_SCOPE["tenant_id"]).strip(),
        "workspace_id": (workspace_id or DEFAULT_SITEOPS_SCOPE["workspace_id"]).strip(),
        "user_id": (user_id or requested_by or DEFAULT_SITEOPS_SCOPE["user_id"]).strip(),
    }
    defaulted = [
        field
        for field, default in DEFAULT_SITEOPS_SCOPE.items()
        if scope[field] == default
        and {
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "user_id": user_id or requested_by,
        }[field]
        is None
    ]
    scope["defaulted_fields"] = defaulted
    return scope


def _siteops_approval_preview(candidate_id: str, scope: dict[str, Any]) -> dict[str, Any]:
    candidate_slug = _id_slug(candidate_id)
    run_id = f"siteops_candidate_promotion_{candidate_slug}"
    approval_id = f"approval_{run_id}_browser_skill_candidate_promote"
    tenant_path = _slug(str(scope["tenant_id"])) or "local"
    workspace_path = _slug(str(scope["workspace_id"])) or "default"
    approval_rel = SITEOPS_APPROVAL_REL / tenant_path / workspace_path / f"{approval_id}.json"
    run_rel = SITEOPS_RUN_REL / tenant_path / workspace_path / f"{run_id}.json"
    audit_rel = SITEOPS_AUDIT_REL / tenant_path / workspace_path / f"{run_id}.jsonl"
    return {
        "approval_id": approval_id,
        "run_id": run_id,
        "workflow_id": "browser_skill_candidate.promotion",
        "action": "browser_skill_candidate.promote",
        "approval_ref_preview": approval_rel.as_posix(),
        "run_ref_preview": run_rel.as_posix(),
        "audit_ref_preview": audit_rel.as_posix(),
        "approval_request_written": False,
        "run_record_written": False,
        "audit_event_written": False,
        "path_scope_sanitized": {
            "tenant_id": tenant_path,
            "workspace_id": workspace_path,
        },
    }


def _candidate_aliases(path: Path, record: dict[str, Any]) -> set[str]:
    aliases = {
        str(record.get("candidate_id") or ""),
        str(record.get("proposed_skill_id") or ""),
        str(record.get("skill_id") or ""),
        path.stem,
        path.stem.split("__", 1)[-1],
    }
    aliases.update(_slug(alias) for alias in list(aliases) if alias)
    return {alias for alias in aliases if alias}


def _find_candidate(candidate_id: str, root: Path | str | None = None) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Return the scanned candidate path plus redacted/machine records.

    Resolution is intentionally alias-based over the canonical candidate store;
    callers cannot provide arbitrary filesystem paths.
    """
    if not candidate_id or candidate_id.strip() in {".", ".."}:
        raise BrowserSkillCandidateError("candidate_id is required")
    wanted = candidate_id.strip()
    wanted_slug = _slug(wanted)
    for path in iter_candidate_paths(root):
        record_format, frontmatter, machine, heading_candidate_id = _load_candidate(path)
        merged = {**frontmatter, **machine}
        resolved_id = str(
            merged.get("candidate_id") or heading_candidate_id or path.stem.split("__", 1)[-1]
        )
        proposed_skill_id = str(
            merged.get("proposed_skill_id") or merged.get("skill_id") or ""
        )
        alias_record = {
            "candidate_id": resolved_id,
            "proposed_skill_id": proposed_skill_id or None,
            "skill_id": merged.get("skill_id"),
            "format": record_format,
        }
        aliases = _candidate_aliases(path, alias_record)
        if wanted in aliases or wanted_slug in aliases:
            return path, frontmatter, machine, candidate_record(path, root)
    raise BrowserSkillCandidateError(f"browser skill candidate not found: {candidate_id}")


def _safe_draft_preview(data: dict[str, Any], target_path: str) -> dict[str, Any]:
    source_runs = data.get("source_runs")
    steps = data.get("steps")
    selectors = data.get("selectors")
    preconditions = data.get("preconditions")
    return {
        "target_path": target_path,
        "schema_version": data.get("schema_version"),
        "skill_id": data.get("skill_id"),
        "domain": data.get("domain"),
        "intent": data.get("intent"),
        "allowed_domains": data.get("allowed_domains") if isinstance(data.get("allowed_domains"), list) else [],
        "approval_status": data.get("approval_status"),
        "risk_level": data.get("risk_level"),
        "credentials_required": bool(data.get("credentials_required", False)),
        "canonical_writeback": bool(data.get("canonical_writeback", False)),
        "step_count": len(steps) if isinstance(steps, list) else 0,
        "selector_count": len(selectors) if isinstance(selectors, dict) else 0,
        "precondition_count": len(preconditions) if isinstance(preconditions, list) else 0,
        "source_run_count": len(source_runs) if isinstance(source_runs, list) else 0,
        "included_fields": sorted(field for field in REQUIRED_FIELDS if field in data),
        "redacted_fields": ["steps", "selectors", "source_runs"],
    }


def preflight_candidate_promotion(candidate_id: str, root: Path | str | None = None) -> dict[str, Any]:
    """Compute a non-mutating promotion preflight for one untrusted candidate.

    The preflight validates the machine candidate and returns a sanitized target
    preview. It does not create, modify, activate, or promote trusted skill files.
    """
    root_path = _vault_root(root)
    path, _frontmatter, machine, record = _find_candidate(candidate_id, root_path)
    validation = _candidate_validation(machine).as_dict()
    skill_id = str(machine.get("skill_id") or record.get("proposed_skill_id") or "").strip()
    if not skill_id:
        target_rel = TRUSTED_SKILL_REL / "unresolved-candidate.yaml"
    else:
        target_rel = TRUSTED_SKILL_REL / f"{skill_id}.yaml"
    target_path = root_path / target_rel
    ready = bool(validation.get("ok")) and bool(skill_id) and not target_path.exists()
    blockers: list[str] = []
    if not validation.get("ok"):
        blockers.append("candidate validation failed")
    if not skill_id:
        blockers.append("candidate has no skill_id")
    if target_path.exists():
        blockers.append("target trusted skill path already exists")

    target_repo_path = target_rel.as_posix()
    return {
        "ok": True,
        "candidate_id": record.get("candidate_id"),
        "proposed_skill_id": skill_id or None,
        "preflight_status": "ready_for_operator_review" if ready else "blocked",
        "blockers": blockers,
        "validation": validation,
        "candidate": record,
        "target": {
            "type": "browser_skill_yaml",
            "path": target_repo_path,
            "exists": target_path.exists(),
        },
        "draft_preview": _safe_draft_preview(machine, target_repo_path),
        "source_path": _as_repo_path(path, root_path),
        "writes_performed": False,
        "activation_allowed": False,
        "promotion_allowed": False,
        "raw_content_visible": False,
        "approval_required": True,
        "boundary": (
            "preflight only; no trusted skill, SiteOps skill card, browser execution, "
            "activation, or canonical writeback is performed"
        ),
    }


def candidate_promotion_preflight(candidate_id: str, root: Path | str | None = None) -> dict[str, Any]:
    """Compatibility wrapper for the candidate promotion preflight helper."""
    return preflight_candidate_promotion(candidate_id, root)


def candidate_promotion_request_contract(
    candidate_id: str,
    root: Path | str | None = None,
    *,
    requested_by: str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Return a non-mutating approval-request contract for candidate promotion.

    This is intentionally one step short of promotion. It converts the preflight
    result into an operator-reviewable approval request shape while denying all
    trusted skill writes, SiteOps skill-card writes, activation, and browser
    execution until a separate Gate/permission policy exists.
    """
    preflight = preflight_candidate_promotion(candidate_id, root)
    target = preflight.get("target") or {}
    candidate = preflight.get("candidate") or {}
    blockers = list(preflight.get("blockers") or [])
    ready = preflight.get("preflight_status") == "ready_for_operator_review" and not blockers
    scope = _scope_with_defaults(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        requested_by=requested_by,
    )
    approval_preview = _siteops_approval_preview(str(preflight.get("candidate_id") or candidate_id), scope)
    request = {
        "action": "browser_skill_candidate.promote",
        "requested_by": requested_by or scope["user_id"],
        "status": "draft_pending_operator_review",
        "required_approver_role": "owner",
        "siteops_required_approver_role": "tenant_admin",
        "approval_id": approval_preview["approval_id"],
        "run_id": approval_preview["run_id"],
        "workflow_id": approval_preview["workflow_id"],
        "tenant_id": scope["tenant_id"],
        "workspace_id": scope["workspace_id"],
        "user_id": scope["user_id"],
        "scope": scope,
        "risk_level": candidate.get("risk_level") or "high",
        "reason": "Promote an untrusted Browser Operator Skill candidate into a trusted draft skill only after explicit Gate/owner approval.",
        "target": {
            "candidate_id": preflight.get("candidate_id"),
            "proposed_skill_id": preflight.get("proposed_skill_id"),
            "trusted_skill_path": target.get("path"),
            "source_path": preflight.get("source_path"),
        },
        "siteops_approval_preview": approval_preview,
        "blocked_effects": [
            "trusted_skill_write",
            "siteops_skill_card_write",
            "browser_execution",
            "skill_activation",
            "canonical_writeback",
        ],
    }
    return {
        "ok": True,
        "candidate_id": preflight.get("candidate_id"),
        "proposed_skill_id": preflight.get("proposed_skill_id"),
        "contract_status": "approval_request_ready" if ready else "blocked",
        "blockers": blockers,
        "preflight": preflight,
        "scope": scope,
        "siteops_approval_preview": approval_preview,
        "approval_required": True,
        "approval_request": request,
        "approval_request_written": False,
        "run_record_written": False,
        "audit_event_written": False,
        "writes_performed": False,
        "trusted_skill_write_allowed": False,
        "siteops_skill_card_write_allowed": False,
        "browser_execution_allowed": False,
        "activation_allowed": False,
        "promotion_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "approval-request contract only; no approval is persisted and no trusted skill, "
            "SiteOps skill card, browser execution, activation, or canonical writeback is performed"
        ),
    }


def _safe_metadata(frontmatter: dict[str, Any], machine: dict[str, Any]) -> dict[str, Any]:
    merged = {**frontmatter, **machine}
    return {key: merged.get(key) for key in sorted(SAFE_METADATA_FIELDS) if key in merged}


def candidate_record(path: Path, root: Path | str | None = None) -> dict[str, Any]:
    root_path = _vault_root(root)
    record_format, frontmatter, machine, heading_candidate_id = _load_candidate(path)
    merged = {**frontmatter, **machine}
    candidate_id = (
        str(merged.get("candidate_id") or heading_candidate_id or path.stem.split("__", 1)[-1])
    )
    validation = _candidate_validation(machine).as_dict()
    stat = path.stat()
    source_runs = machine.get("source_runs")
    source_run_count = len(source_runs) if isinstance(source_runs, list) else 0
    proposed_skill_id = str(
        merged.get("proposed_skill_id") or merged.get("skill_id") or ""
    )
    record = {
        "candidate_id": candidate_id,
        "proposed_skill_id": proposed_skill_id or None,
        "domain": merged.get("domain"),
        "intent": merged.get("intent"),
        "status": merged.get("status") or frontmatter.get("status") or "candidate_untrusted",
        "trust_tier": frontmatter.get("trust_tier") or "Tier 4",
        "approval_status": merged.get("approval_status"),
        "risk_level": merged.get("risk_level"),
        "activation_allowed": bool(merged.get("activation_allowed", False)),
        "review_required": bool(merged.get("review_required", True)),
        "source_run": frontmatter.get("source_run"),
        "source_run_count": source_run_count,
        "path": _as_repo_path(path, root_path),
        "format": record_format,
        "bytes": stat.st_size,
        "modified_at": stat.st_mtime,
        "validation": validation,
        "raw_content_visible": False,
        "source_run_paths_visible": False,
        "safe_metadata": _safe_metadata(frontmatter, machine),
    }
    record["aliases"] = sorted(_candidate_aliases(path, record))
    return record


def list_candidate_records(root: Path | str | None = None) -> list[dict[str, Any]]:
    """List redacted summaries for untrusted browser skill candidates."""
    return [candidate_record(path, root) for path in iter_candidate_paths(root)]


def show_candidate_record(candidate_id: str, root: Path | str | None = None) -> dict[str, Any]:
    """Find one candidate by ID, skill ID, slug, or filename stem.

    This function only searches the canonical candidate folder. It never opens a
    caller-supplied path, so path traversal strings cannot escape the candidate
    store.
    """
    if not candidate_id or candidate_id.strip() in {".", ".."}:
        raise BrowserSkillCandidateError("candidate_id is required")
    wanted = candidate_id.strip()
    wanted_slug = _slug(wanted)
    for record in list_candidate_records(root):
        aliases = set(record.get("aliases") or [])
        if wanted in aliases or wanted_slug in aliases:
            return record
    raise BrowserSkillCandidateError(f"browser skill candidate not found: {candidate_id}")


def storage_reconciliation(root: Path | str | None = None) -> dict[str, Any]:
    """Return the current storage decision across BOSL, Browser Runtime, and SiteOps."""
    root_path = _vault_root(root)
    return {
        "candidate_home": CANDIDATE_REL.as_posix(),
        "candidate_home_exists": (root_path / CANDIDATE_REL).exists(),
        "browser_run_home": BROWSER_RUN_REL.as_posix(),
        "browser_run_home_exists": (root_path / BROWSER_RUN_REL).exists(),
        "trusted_skill_home": TRUSTED_SKILL_REL.as_posix(),
        "trusted_skill_home_exists": (root_path / TRUSTED_SKILL_REL).exists(),
        "siteops_skill_card_home": SITEOPS_SKILL_CARD_REL.as_posix(),
        "siteops_skill_card_home_exists": (root_path / SITEOPS_SKILL_CARD_REL).exists(),
        "site_activity_ledger": SITE_ACTIVITY_LEDGER_REL.as_posix(),
        "site_activity_ledger_exists": (root_path / SITE_ACTIVITY_LEDGER_REL).exists(),
        "decision": (
            "BOSL candidate home is the canonical pending-review browser-skill "
            "candidate store; SiteOps exposes read-only inspection and must not "
            "create a duplicate candidate store."
        ),
        "siteops_boundary": "read-only inspection only; no promotion, activation, browser execution, or canonical writeback",
    }
