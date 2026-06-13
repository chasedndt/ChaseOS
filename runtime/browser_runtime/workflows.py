"""ChaseOS-native browser workflow cache foundation.

This module records review-only workflow cache entries derived from browser run
evidence. It does not execute workflows, launch browsers, connect to CDP, call
external providers, activate skills, mutate Gate policy, or write canonical
ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.models import (
    BrowserRunResult,
    domain_from_url,
    slugify,
)


WORKFLOW_CACHE_SCHEMA_VERSION = "browser.workflow_cache.v1"
WORKFLOW_CACHE_METADATA_RECORD_TYPE = "browser_workflow_cache_metadata"
WORKFLOW_CACHE_ENTRY_RECORD_TYPE = "browser_workflow_cache_entry"

FORBIDDEN_SECURITY_FLAGS = (
    "real_profile_used",
    "real_profile_allowed",
    "credentials_used",
    "credentials_allowed",
    "cookies_exported",
    "browser_history_imported",
    "trusted_skill_write",
    "siteops_skill_card_write",
    "skill_activation",
    "browser_harness_used",
    "browser_use_cli_used",
    "public_tunnel_used",
    "agent_bus_enqueue",
    "provider_call",
    "gate_policy_mutation",
    "canonical_writeback",
)

FORBIDDEN_ACTION_TYPES = {
    "credential_field_fill",
    "cookie_export",
    "form_submit",
    "payment_submit",
    "account_mutation",
    "download_private_file",
    "upload_file",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def workflow_cache_root(root: Path | str | None = None) -> Path:
    base = Path(root) if root else _default_root()
    return base / "runtime" / "browser_workflows"


def workflow_cache_metadata_path(root: Path | str | None = None) -> Path:
    return workflow_cache_root(root) / "metadata.json"


def workflow_cache_entries_dir(root: Path | str | None = None) -> Path:
    return workflow_cache_root(root) / "workflows"


@dataclass(frozen=True)
class BrowserWorkflowStep:
    """One review-only step in a cached browser workflow."""

    step_id: str
    action_type: str
    target: str
    status: str
    source_action_index: int
    notes: str = ""
    wait_condition: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrowserWorkflowCacheEntry:
    """Inactive workflow cache entry derived from browser run evidence."""

    workflow_id: str
    domain: str
    intent: str
    source_run_id: str
    source_run_log_path: str
    created_at: str = field(default_factory=_now_utc)
    schema_version: str = WORKFLOW_CACHE_SCHEMA_VERSION
    record_type: str = WORKFLOW_CACHE_ENTRY_RECORD_TYPE
    status: str = "draft_review_only"
    allowed_domains: list[str] = field(default_factory=list)
    source_url: str = ""
    steps: list[BrowserWorkflowStep] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    learned_patterns: list[str] = field(default_factory=list)
    rejected_patterns: list[str] = field(default_factory=list)
    review_required: bool = True
    activation_allowed: bool = False
    replay_allowed: bool = False
    trusted_write_allowed: bool = False
    external_code_copied: bool = False
    license_notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = [step.as_dict() for step in self.steps]
        return payload


@dataclass(frozen=True)
class BrowserWorkflowCacheValidation:
    """Validation result for a workflow cache entry."""

    ok: bool
    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_empty_workflow_cache_metadata(*, generated_at: str | None = None) -> dict[str, Any]:
    """Return the empty inactive registry metadata shape."""
    return {
        "record_type": WORKFLOW_CACHE_METADATA_RECORD_TYPE,
        "schema_version": WORKFLOW_CACHE_SCHEMA_VERSION,
        "status": "empty_initialized",
        "generated_at": generated_at or _now_utc(),
        "activation_allowed": False,
        "replay_allowed": False,
        "trusted_write_allowed": False,
        "external_code_copied": False,
        "license_notes": [
            "ChaseOS workflow cache is native code.",
            "browser-use/workflow-use is AGPL-3.0 reference only; no code copied.",
        ],
        "workflows": [],
    }


def read_workflow_cache_metadata(root: Path | str | None = None) -> dict[str, Any]:
    """Read metadata if present, otherwise return an in-memory empty shape."""
    path = workflow_cache_metadata_path(root)
    if not path.exists():
        return build_empty_workflow_cache_metadata()
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_workflow_cache(root: Path | str | None = None) -> dict[str, Any]:
    """Return read-only workflow cache status."""
    cache_root = workflow_cache_root(root)
    metadata_path = workflow_cache_metadata_path(root)
    entries_dir = workflow_cache_entries_dir(root)
    entries = sorted(entries_dir.glob("*.workflow.json")) if entries_dir.exists() else []
    metadata = read_workflow_cache_metadata(root)
    return {
        "record_type": "browser_workflow_cache_status",
        "schema_version": WORKFLOW_CACHE_SCHEMA_VERSION,
        "status": "cache_foundation_ready" if metadata_path.exists() else "cache_metadata_missing",
        "cache_root": cache_root.as_posix(),
        "metadata_path": metadata_path.as_posix(),
        "entries_dir": entries_dir.as_posix(),
        "metadata_exists": metadata_path.exists(),
        "workflow_count": len(entries),
        "activation_allowed": False,
        "replay_allowed": False,
        "trusted_write_allowed": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
        "metadata": metadata,
    }


def workflow_entry_from_run(
    result: BrowserRunResult,
    *,
    source_log_path: str | None = None,
    learned_patterns: list[str] | None = None,
) -> BrowserWorkflowCacheEntry:
    """Build an inactive workflow cache entry from browser run evidence."""
    domain = domain_from_url(result.url) or "local"
    workflow_id = f"wf_{slugify(domain, 'local')}_{slugify(result.task, 'browser-task')}_{slugify(result.run_id, 'run')}"
    steps: list[BrowserWorkflowStep] = []
    for index, action in enumerate(result.actions):
        if action.action_type in FORBIDDEN_ACTION_TYPES:
            continue
        steps.append(
            BrowserWorkflowStep(
                step_id=f"step_{index + 1:02d}_{slugify(action.action_type, 'action')}",
                action_type=action.action_type,
                target=action.target,
                status=action.status,
                source_action_index=index,
                notes=action.notes,
                metadata={
                    "source_timestamp": action.timestamp,
                    "blocked_reason": action.blocked_reason,
                },
            )
        )
    artifacts = [artifact.path for artifact in result.artifacts]
    return BrowserWorkflowCacheEntry(
        workflow_id=workflow_id,
        domain=domain,
        intent=result.task,
        source_run_id=result.run_id,
        source_run_log_path=source_log_path or result.browser_run_log_path or "",
        allowed_domains=[domain],
        source_url=result.url,
        steps=steps,
        source_artifacts=artifacts,
        learned_patterns=learned_patterns
        or [
            "Workflow cache entry derived from ChaseOS-controlled browser run evidence.",
            "Entry remains review-only until a separate approval and executor pass.",
        ],
        rejected_patterns=[
            "No secrets, cookies, credentials, profile state, or user-specific session data retained.",
            "No external workflow-use code copied.",
        ],
        license_notes=[
            "Native ChaseOS cache shape.",
            "browser-use/workflow-use remains AGPL-3.0 reference only.",
        ],
    )


def validate_workflow_cache_entry(
    entry: BrowserWorkflowCacheEntry,
    *,
    source_security_flags: dict[str, Any] | None = None,
) -> BrowserWorkflowCacheValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if entry.schema_version != WORKFLOW_CACHE_SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if entry.record_type != WORKFLOW_CACHE_ENTRY_RECORD_TYPE:
        errors.append("record_type_mismatch")
    if not entry.workflow_id:
        errors.append("missing_workflow_id")
    if not entry.domain:
        errors.append("missing_domain")
    if not entry.source_run_id:
        errors.append("missing_source_run_id")
    if not entry.source_run_log_path:
        errors.append("missing_source_run_log_path")
    if not entry.steps:
        warnings.append("no_cacheable_steps")
    if entry.activation_allowed:
        errors.append("activation_must_remain_disabled")
    if entry.replay_allowed:
        errors.append("replay_must_remain_disabled")
    if entry.trusted_write_allowed:
        errors.append("trusted_write_must_remain_disabled")
    if entry.external_code_copied:
        errors.append("external_code_copy_forbidden")
    for step in entry.steps:
        if step.action_type in FORBIDDEN_ACTION_TYPES:
            errors.append(f"forbidden_action_type:{step.action_type}")
    flags = source_security_flags or {}
    for flag in FORBIDDEN_SECURITY_FLAGS:
        if flags.get(flag) is True:
            errors.append(f"forbidden_source_security_flag:{flag}")
    return BrowserWorkflowCacheValidation(
        ok=not errors,
        status="valid_inactive_workflow_cache_entry" if not errors else "blocked_workflow_cache_entry",
        errors=errors,
        warnings=warnings,
    )


def write_workflow_cache_entry(
    entry: BrowserWorkflowCacheEntry,
    *,
    root: Path | str | None = None,
    source_security_flags: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Write an inactive workflow cache entry and update cache metadata."""
    validation = validate_workflow_cache_entry(entry, source_security_flags=source_security_flags)
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    directory = workflow_cache_entries_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    entry_path = directory / f"{slugify(entry.workflow_id, 'browser-workflow')}.workflow.json"
    entry_path.write_text(json.dumps(entry.as_dict(), indent=2) + "\n", encoding="utf-8")

    metadata_path = workflow_cache_metadata_path(root)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = read_workflow_cache_metadata(root)
    workflow_record = {
        "workflow_id": entry.workflow_id,
        "domain": entry.domain,
        "status": entry.status,
        "path": entry_path.as_posix(),
        "source_run_id": entry.source_run_id,
        "activation_allowed": False,
        "replay_allowed": False,
    }
    workflows = [item for item in metadata.get("workflows", []) if item.get("workflow_id") != entry.workflow_id]
    workflows.append(workflow_record)
    metadata.update(
        {
            "record_type": WORKFLOW_CACHE_METADATA_RECORD_TYPE,
            "schema_version": WORKFLOW_CACHE_SCHEMA_VERSION,
            "status": "inactive_review_cache",
            "updated_at": _now_utc(),
            "activation_allowed": False,
            "replay_allowed": False,
            "trusted_write_allowed": False,
            "external_code_copied": False,
            "workflows": sorted(workflows, key=lambda item: item["workflow_id"]),
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return entry_path.as_posix(), metadata_path.as_posix()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report read-only Browser Workflow Cache status.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    payload = summarize_workflow_cache(args.vault_root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"workflow_count: {payload['workflow_count']}")
        print(f"metadata_path: {payload['metadata_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
