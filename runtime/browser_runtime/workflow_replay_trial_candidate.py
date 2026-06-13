"""Select a reviewed local Browser Workflow trial candidate.

This module bridges the inactive workflow cache and the read-only replay
readiness preflight. It can derive one reviewed-for-trial cache entry from
already-controlled local Browser Run evidence, but it does not execute replay,
launch browsers, connect to CDP, or activate skills.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.models import domain_from_url, slugify
from runtime.browser_runtime.workflows import (
    FORBIDDEN_ACTION_TYPES,
    FORBIDDEN_SECURITY_FLAGS,
    WORKFLOW_CACHE_ENTRY_RECORD_TYPE,
    WORKFLOW_CACHE_METADATA_RECORD_TYPE,
    WORKFLOW_CACHE_SCHEMA_VERSION,
    BrowserWorkflowCacheEntry,
    BrowserWorkflowCacheValidation,
    BrowserWorkflowStep,
    build_empty_workflow_cache_metadata,
    read_workflow_cache_metadata,
    workflow_cache_entries_dir,
    workflow_cache_metadata_path,
)


WORKFLOW_REPLAY_TRIAL_CANDIDATE_VERSION = "browser.workflow_replay_trial_candidate.v1"
WORKFLOW_REPLAY_TRIAL_CANDIDATE_PREVIEW_READY = "workflow_replay_trial_candidate_preview_ready_no_write"
WORKFLOW_REPLAY_TRIAL_CANDIDATE_WRITTEN = "workflow_replay_trial_candidate_written"
WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTED_EXISTING = "workflow_replay_trial_candidate_selected_existing"
WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED = "blocked_workflow_replay_trial_candidate"

DEFAULT_SOURCE_RUN_LOG = "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json"
DEFAULT_WORKFLOW_ID = "wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502"
LOCAL_TRIAL_DOMAINS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_SOURCE_ACTIONS = {"open", "read_state", "harmless_click", "capture_screenshot"}
ALLOWED_SOURCE_RESULTS = {"loaded", "success", "succeeded"}
FORBIDDEN_SOURCE_EFFECT_FLAGS = (
    *FORBIDDEN_SECURITY_FLAGS,
    "cdp_connection_used",
    "real_browser_profile_used",
    "browser_use_cli_live_used",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_path(path: Path, vault: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _is_local_trial_url(url: str) -> bool:
    domain = domain_from_url(url)
    return bool(domain) and domain in LOCAL_TRIAL_DOMAINS


def _false_or_missing(value: Any) -> bool:
    return value is False or value is None


def _source_security_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    governance = record.get("governance")
    if not isinstance(governance, dict):
        errors.append("missing_governance")
        governance = {}
    provider_details = record.get("provider_details")
    if not isinstance(provider_details, dict):
        provider_details = {}
    server = record.get("server")
    if isinstance(server, dict) and server.get("public_tunnel") is True:
        errors.append("public_tunnel_forbidden")

    for flag in FORBIDDEN_SOURCE_EFFECT_FLAGS:
        if governance.get(flag) is True:
            errors.append(f"forbidden_governance_flag:{flag}")
        if provider_details.get(flag) is True:
            errors.append(f"forbidden_provider_detail_flag:{flag}")

    provider_flag_map = {
        "real_browser_profile_used": "real_profile_used",
        "browser_use_cli_used": "browser_use_cli_used",
        "browser_harness_used": "browser_harness_used",
        "cdp_used": "cdp_connection_used",
    }
    for provider_key, governance_key in provider_flag_map.items():
        if provider_details.get(provider_key) is True:
            errors.append(f"forbidden_provider_detail_flag:{provider_key}")
        if governance.get(governance_key) is True:
            errors.append(f"forbidden_governance_flag:{governance_key}")
    return sorted(set(errors))


def validate_source_run_record(record: dict[str, Any] | None) -> BrowserWorkflowCacheValidation:
    """Validate local browser-run evidence before deriving a trial candidate."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(record, dict):
        return BrowserWorkflowCacheValidation(
            ok=False,
            status=WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED,
            errors=["source_run_log_missing_or_invalid_json"],
        )
    if record.get("record_type") != "browser_run_log":
        errors.append("source_record_type_mismatch")
    if record.get("schema_version") != "browser.run.v1":
        errors.append("source_schema_version_mismatch")
    if record.get("status") != "succeeded":
        errors.append("source_run_not_succeeded")
    if record.get("provider") != "codex-in-app-browser":
        errors.append("source_provider_not_codex_iab")
    if record.get("provider_backend") != "iab":
        errors.append("source_backend_not_iab")

    url = str(record.get("url") or "")
    target = record.get("target")
    target_url = str(target.get("url") or "") if isinstance(target, dict) else ""
    target_domain = str(target.get("domain") or "") if isinstance(target, dict) else ""
    if not _is_local_trial_url(url):
        errors.append("source_url_not_local_trial_target")
    if target_url and target_url != url:
        errors.append("target_url_mismatch")
    if target_domain and target_domain not in LOCAL_TRIAL_DOMAINS:
        errors.append("target_domain_not_local_trial_target")
    if isinstance(target, dict) and target.get("safe_mode_asserted") is not True:
        errors.append("safe_mode_not_asserted")
    elif not isinstance(target, dict):
        errors.append("missing_target_contract")

    actions = record.get("actions")
    if not isinstance(actions, list) or not actions:
        errors.append("missing_source_actions")
    else:
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                errors.append(f"source_action_not_object:{index}")
                continue
            action_type = str(action.get("action") or "")
            result = str(action.get("result") or "")
            if action_type not in ALLOWED_SOURCE_ACTIONS:
                errors.append(f"source_action_not_allowed:{action_type}")
            if action_type in FORBIDDEN_ACTION_TYPES:
                errors.append(f"forbidden_source_action_type:{action_type}")
            if result not in ALLOWED_SOURCE_RESULTS:
                errors.append(f"source_action_result_not_success:{index}")
    errors.extend(_source_security_errors(record))
    browser_state = record.get("browser_state")
    if not isinstance(browser_state, dict):
        warnings.append("browser_state_missing")
    elif browser_state.get("post_action_status") != "Panel inspected in safe mode.":
        errors.append("post_action_status_not_verified")

    return BrowserWorkflowCacheValidation(
        ok=not errors,
        status="valid_local_trial_source_run" if not errors else WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED,
        errors=sorted(set(errors)),
        warnings=warnings,
    )


def _step_status(action: dict[str, Any]) -> str:
    result = str(action.get("result") or "")
    return "succeeded" if result in ALLOWED_SOURCE_RESULTS else "blocked"


def build_trial_candidate_entry(
    source_record: dict[str, Any],
    *,
    source_log_path: str,
    workflow_id: str = DEFAULT_WORKFLOW_ID,
    created_at: str | None = None,
) -> BrowserWorkflowCacheEntry:
    """Build a reviewed-for-trial workflow cache entry from local run evidence."""
    source_url = str(source_record.get("url") or "")
    domain = domain_from_url(source_url) or "127.0.0.1"
    steps: list[BrowserWorkflowStep] = []
    for index, action in enumerate(source_record.get("actions") or []):
        if not isinstance(action, dict):
            continue
        action_type = str(action.get("action") or "")
        if action_type in FORBIDDEN_ACTION_TYPES:
            continue
        if action_type not in ALLOWED_SOURCE_ACTIONS:
            continue
        steps.append(
            BrowserWorkflowStep(
                step_id=f"step_{index + 1:02d}_{slugify(action_type, 'action')}",
                action_type=action_type,
                target=str(action.get("target") or ""),
                status=_step_status(action),
                source_action_index=index,
                notes=str(action.get("evidence") or ""),
                wait_condition=(
                    "local_target_loaded"
                    if action_type == "open"
                    else "safe_mode_visible_state_verified"
                    if action_type == "read_state"
                    else "post_action_status_verified"
                    if action_type == "harmless_click"
                    else "screenshot_artifact_recorded"
                ),
                metadata={
                    "source_action_index": action.get("index"),
                    "source_result": action.get("result"),
                },
            )
        )

    artifacts = [
        str(artifact.get("path"))
        for artifact in source_record.get("artifacts") or []
        if isinstance(artifact, dict) and artifact.get("path")
    ]
    return BrowserWorkflowCacheEntry(
        workflow_id=workflow_id,
        domain=domain,
        intent="VincisOS local product UI safe-panel inspection trial",
        source_run_id=str(source_record.get("run_id") or ""),
        source_run_log_path=source_log_path,
        created_at=created_at or _now_utc(),
        status="reviewed_for_trial",
        allowed_domains=[domain],
        source_url=source_url,
        steps=steps,
        source_artifacts=artifacts,
        learned_patterns=[
            "Open only the local VincisOS product UI proof target.",
            "Verify safe-mode UI selectors before planning harmless actions.",
            "Use local tab/panel inspection actions only; no account or credential surface is involved.",
            "Verify the final action status equals 'Panel inspected in safe mode.'",
        ],
        rejected_patterns=[
            "No secrets, cookies, saved sessions, browser history, profile paths, or credentials retained.",
            "No raw Browser Harness helper mutation or external workflow-use code copied.",
            "No active SiteOps skill, trusted artifact, Gate mutation, Agent Bus enqueue, or canonical writeback created.",
        ],
        review_required=True,
        activation_allowed=False,
        replay_allowed=True,
        trusted_write_allowed=False,
        external_code_copied=False,
        license_notes=[
            "Native ChaseOS trial candidate shape.",
            "browser-use/workflow-use remains AGPL-3.0 reference only; no code copied.",
        ],
    )


def validate_trial_candidate_entry(
    entry: BrowserWorkflowCacheEntry,
    *,
    source_record: dict[str, Any] | None,
) -> BrowserWorkflowCacheValidation:
    """Validate a replay-enabled trial candidate without enabling execution."""
    source_validation = validate_source_run_record(source_record)
    errors: list[str] = list(source_validation.errors)
    warnings: list[str] = list(source_validation.warnings)
    if entry.record_type != WORKFLOW_CACHE_ENTRY_RECORD_TYPE:
        errors.append("entry_record_type_mismatch")
    if entry.schema_version != WORKFLOW_CACHE_SCHEMA_VERSION:
        errors.append("entry_schema_version_mismatch")
    if entry.status != "reviewed_for_trial":
        errors.append("entry_status_must_be_reviewed_for_trial")
    if not entry.review_required:
        errors.append("review_required_must_remain_true")
    if entry.activation_allowed:
        errors.append("activation_must_remain_disabled")
    if entry.trusted_write_allowed:
        errors.append("trusted_write_must_remain_disabled")
    if entry.external_code_copied:
        errors.append("external_code_copy_forbidden")
    if not entry.replay_allowed:
        errors.append("trial_candidate_must_be_replay_allowed_for_readiness_only")
    if not entry.workflow_id:
        errors.append("missing_workflow_id")
    if not entry.source_run_id:
        errors.append("missing_source_run_id")
    if not entry.source_run_log_path:
        errors.append("missing_source_run_log_path")
    if not entry.source_url or not _is_local_trial_url(entry.source_url):
        errors.append("entry_source_url_not_local_trial_target")
    if not entry.allowed_domains:
        errors.append("missing_allowed_domains")
    for domain in entry.allowed_domains:
        if domain not in LOCAL_TRIAL_DOMAINS:
            errors.append(f"entry_allowed_domain_not_local:{domain}")
    if not entry.steps:
        errors.append("missing_trial_steps")
    for step in entry.steps:
        if step.action_type not in ALLOWED_SOURCE_ACTIONS:
            errors.append(f"entry_action_not_allowed:{step.action_type}")
        if step.action_type in FORBIDDEN_ACTION_TYPES:
            errors.append(f"forbidden_entry_action_type:{step.action_type}")
        if step.status != "succeeded":
            errors.append(f"entry_step_not_succeeded:{step.step_id}")
    if isinstance(source_record, dict) and entry.source_run_id != str(source_record.get("run_id") or ""):
        errors.append("source_run_id_mismatch")

    return BrowserWorkflowCacheValidation(
        ok=not errors,
        status="valid_reviewed_local_trial_candidate" if not errors else WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED,
        errors=sorted(set(errors)),
        warnings=warnings,
    )


@dataclass(frozen=True)
class WorkflowReplayTrialCandidateResult:
    """Result for trial-candidate selection or writing."""

    record_type: str
    version: str
    generated_at: str
    status: str
    workflow_id: str
    source_run_id: str
    source_run_log_path: str
    workflow_entry_path: str = ""
    metadata_path: str = ""
    write_requested: bool = False
    wrote_workflow_entry: bool = False
    wrote_metadata: bool = False
    selected_existing: bool = False
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    next_step: str = "operator_review"
    activation_allowed: bool = False
    replay_allowed_for_readiness_only: bool = True
    execution_allowed: bool = False
    workflow_replay_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    external_code_copied: bool = False
    workflow_use_reference_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.activation_allowed:
            raise ValueError("activation_allowed must remain false")
        if self.execution_allowed:
            raise ValueError("execution_allowed must remain false")
        if self.workflow_replay_attempted:
            raise ValueError("workflow_replay_attempted must remain false")
        if self.browser_launch_attempted:
            raise ValueError("browser_launch_attempted must remain false")
        if self.cdp_connection_attempted:
            raise ValueError("cdp_connection_attempted must remain false")
        if self.browser_harness_used:
            raise ValueError("browser_harness_used must remain false")
        if self.browser_use_cli_live_used:
            raise ValueError("browser_use_cli_live_used must remain false")
        if self.real_profile_access_attempted:
            raise ValueError("real_profile_access_attempted must remain false")
        if self.credential_or_cookie_read_attempted:
            raise ValueError("credential_or_cookie_read_attempted must remain false")
        if self.agent_bus_enqueue_attempted:
            raise ValueError("agent_bus_enqueue_attempted must remain false")
        if self.provider_call_attempted:
            raise ValueError("provider_call_attempted must remain false")
        if self.gate_mutation_attempted:
            raise ValueError("gate_mutation_attempted must remain false")
        if self.trusted_skill_write_attempted:
            raise ValueError("trusted_skill_write_attempted must remain false")
        if self.skill_activation_attempted:
            raise ValueError("skill_activation_attempted must remain false")
        if self.canonical_writeback_attempted:
            raise ValueError("canonical_writeback_attempted must remain false")
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow_use_reference_only must remain true")
        if self.status != WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED and self.validation_errors:
            raise ValueError("non-blocked trial candidate cannot have validation errors")


def _entry_path_for(vault: Path, workflow_id: str) -> Path:
    return workflow_cache_entries_dir(vault) / f"{slugify(workflow_id, 'browser-workflow')}.workflow.json"


def _existing_entry_ok(path: Path, source_record: dict[str, Any] | None) -> bool:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return False
    steps = [
        BrowserWorkflowStep(
            step_id=str(step.get("step_id") or ""),
            action_type=str(step.get("action_type") or ""),
            target=str(step.get("target") or ""),
            status=str(step.get("status") or ""),
            source_action_index=int(step.get("source_action_index") or 0),
            notes=str(step.get("notes") or ""),
            wait_condition=step.get("wait_condition") if isinstance(step.get("wait_condition"), str) else None,
            metadata=step.get("metadata") if isinstance(step.get("metadata"), dict) else {},
        )
        for step in payload.get("steps", [])
        if isinstance(step, dict)
    ]
    entry = BrowserWorkflowCacheEntry(
        workflow_id=str(payload.get("workflow_id") or ""),
        domain=str(payload.get("domain") or ""),
        intent=str(payload.get("intent") or ""),
        source_run_id=str(payload.get("source_run_id") or ""),
        source_run_log_path=str(payload.get("source_run_log_path") or ""),
        created_at=str(payload.get("created_at") or _now_utc()),
        status=str(payload.get("status") or ""),
        allowed_domains=list(payload.get("allowed_domains") or []),
        source_url=str(payload.get("source_url") or ""),
        steps=steps,
        source_artifacts=list(payload.get("source_artifacts") or []),
        learned_patterns=list(payload.get("learned_patterns") or []),
        rejected_patterns=list(payload.get("rejected_patterns") or []),
        review_required=payload.get("review_required") is True,
        activation_allowed=payload.get("activation_allowed") is True,
        replay_allowed=payload.get("replay_allowed") is True,
        trusted_write_allowed=payload.get("trusted_write_allowed") is True,
        external_code_copied=payload.get("external_code_copied") is True,
        license_notes=list(payload.get("license_notes") or []),
    )
    return validate_trial_candidate_entry(entry, source_record=source_record).ok


def _write_metadata(vault: Path, entry: BrowserWorkflowCacheEntry, entry_path: Path, timestamp: str) -> Path:
    metadata_path = workflow_cache_metadata_path(vault)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = read_workflow_cache_metadata(vault)
    if not isinstance(metadata, dict):
        metadata = build_empty_workflow_cache_metadata(generated_at=timestamp)
    workflow_record = {
        "workflow_id": entry.workflow_id,
        "domain": entry.domain,
        "status": entry.status,
        "path": _relative_path(entry_path, vault),
        "source_run_id": entry.source_run_id,
        "activation_allowed": False,
        "replay_allowed": True,
        "trusted_write_allowed": False,
        "external_code_copied": False,
        "trial_candidate": True,
    }
    workflows = [
        item
        for item in metadata.get("workflows", [])
        if isinstance(item, dict) and item.get("workflow_id") != entry.workflow_id
    ]
    workflows.append(workflow_record)
    metadata.update(
        {
            "record_type": WORKFLOW_CACHE_METADATA_RECORD_TYPE,
            "schema_version": WORKFLOW_CACHE_SCHEMA_VERSION,
            "status": "inactive_review_cache",
            "updated_at": timestamp,
            "activation_allowed": False,
            "replay_allowed": False,
            "trusted_write_allowed": False,
            "external_code_copied": False,
            "license_notes": [
                "ChaseOS workflow cache is native code.",
                "browser-use/workflow-use is AGPL-3.0 reference only; no code copied.",
            ],
            "workflows": sorted(workflows, key=lambda item: str(item["workflow_id"])),
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata_path


def select_or_write_trial_candidate(
    vault_root: str | Path,
    *,
    source_run_log_path: str = DEFAULT_SOURCE_RUN_LOG,
    workflow_id: str = DEFAULT_WORKFLOW_ID,
    write_trial_candidate: bool = False,
    generated_at: str | None = None,
) -> WorkflowReplayTrialCandidateResult:
    """Preview or write the reviewed local trial candidate."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    source_path = Path(source_run_log_path)
    source_abs = source_path if source_path.is_absolute() else vault / source_path
    source_record = _load_json(source_abs)
    source_validation = validate_source_run_record(source_record)
    source_run_id = str(source_record.get("run_id") or "") if isinstance(source_record, dict) else ""
    entry_path = _entry_path_for(vault, workflow_id)
    metadata_path = workflow_cache_metadata_path(vault)

    if not source_validation.ok or not isinstance(source_record, dict):
        result = WorkflowReplayTrialCandidateResult(
            record_type="browser_workflow_replay_trial_candidate_result",
            version=WORKFLOW_REPLAY_TRIAL_CANDIDATE_VERSION,
            generated_at=timestamp,
            status=WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED,
            workflow_id=workflow_id,
            source_run_id=source_run_id,
            source_run_log_path=_relative_path(source_abs, vault),
            workflow_entry_path=_relative_path(entry_path, vault),
            metadata_path=_relative_path(metadata_path, vault),
            write_requested=write_trial_candidate,
            validation_errors=source_validation.errors,
            validation_warnings=source_validation.warnings,
            next_step="repair_source_browser_run_evidence",
        )
        result.validate()
        return result

    entry = build_trial_candidate_entry(
        source_record,
        source_log_path=_relative_path(source_abs, vault),
        workflow_id=workflow_id,
        created_at=timestamp,
    )
    entry_validation = validate_trial_candidate_entry(entry, source_record=source_record)
    if not entry_validation.ok:
        result = WorkflowReplayTrialCandidateResult(
            record_type="browser_workflow_replay_trial_candidate_result",
            version=WORKFLOW_REPLAY_TRIAL_CANDIDATE_VERSION,
            generated_at=timestamp,
            status=WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED,
            workflow_id=workflow_id,
            source_run_id=entry.source_run_id,
            source_run_log_path=entry.source_run_log_path,
            workflow_entry_path=_relative_path(entry_path, vault),
            metadata_path=_relative_path(metadata_path, vault),
            write_requested=write_trial_candidate,
            validation_errors=entry_validation.errors,
            validation_warnings=entry_validation.warnings,
            next_step="repair_trial_candidate_validation",
        )
        result.validate()
        return result

    if not write_trial_candidate:
        result = WorkflowReplayTrialCandidateResult(
            record_type="browser_workflow_replay_trial_candidate_result",
            version=WORKFLOW_REPLAY_TRIAL_CANDIDATE_VERSION,
            generated_at=timestamp,
            status=WORKFLOW_REPLAY_TRIAL_CANDIDATE_PREVIEW_READY,
            workflow_id=workflow_id,
            source_run_id=entry.source_run_id,
            source_run_log_path=entry.source_run_log_path,
            workflow_entry_path=_relative_path(entry_path, vault),
            metadata_path=_relative_path(metadata_path, vault),
            write_requested=False,
            validation_warnings=entry_validation.warnings,
            next_step="rerun_with_write_trial_candidate_to_select_for_readiness",
        )
        result.validate()
        return result

    if entry_path.exists():
        if not _existing_entry_ok(entry_path, source_record):
            result = WorkflowReplayTrialCandidateResult(
                record_type="browser_workflow_replay_trial_candidate_result",
                version=WORKFLOW_REPLAY_TRIAL_CANDIDATE_VERSION,
                generated_at=timestamp,
                status=WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED,
                workflow_id=workflow_id,
                source_run_id=entry.source_run_id,
                source_run_log_path=entry.source_run_log_path,
                workflow_entry_path=_relative_path(entry_path, vault),
                metadata_path=_relative_path(metadata_path, vault),
                write_requested=True,
                validation_errors=["existing_trial_candidate_invalid_or_conflicting"],
                next_step="operator_review_existing_trial_candidate",
            )
            result.validate()
            return result
        metadata_path = _write_metadata(vault, entry, entry_path, timestamp)
        result = WorkflowReplayTrialCandidateResult(
            record_type="browser_workflow_replay_trial_candidate_result",
            version=WORKFLOW_REPLAY_TRIAL_CANDIDATE_VERSION,
            generated_at=timestamp,
            status=WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTED_EXISTING,
            workflow_id=workflow_id,
            source_run_id=entry.source_run_id,
            source_run_log_path=entry.source_run_log_path,
            workflow_entry_path=_relative_path(entry_path, vault),
            metadata_path=_relative_path(metadata_path, vault),
            write_requested=True,
            wrote_metadata=True,
            selected_existing=True,
            validation_warnings=entry_validation.warnings,
            next_step="run_readiness_preflight_with_selected_workflow",
        )
        result.validate()
        return result

    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry_path.write_text(json.dumps(entry.as_dict(), indent=2) + "\n", encoding="utf-8")
    metadata_path = _write_metadata(vault, entry, entry_path, timestamp)
    result = WorkflowReplayTrialCandidateResult(
        record_type="browser_workflow_replay_trial_candidate_result",
        version=WORKFLOW_REPLAY_TRIAL_CANDIDATE_VERSION,
        generated_at=timestamp,
        status=WORKFLOW_REPLAY_TRIAL_CANDIDATE_WRITTEN,
        workflow_id=workflow_id,
        source_run_id=entry.source_run_id,
        source_run_log_path=entry.source_run_log_path,
        workflow_entry_path=_relative_path(entry_path, vault),
        metadata_path=_relative_path(metadata_path, vault),
        write_requested=True,
        wrote_workflow_entry=True,
        wrote_metadata=True,
        validation_warnings=entry_validation.warnings,
        next_step="run_readiness_preflight_with_selected_workflow",
    )
    result.validate()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or write a local workflow replay trial candidate.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--source-run-log", default=DEFAULT_SOURCE_RUN_LOG, help="Safe source Browser Run log.")
    parser.add_argument("--workflow-id", default=DEFAULT_WORKFLOW_ID, help="Workflow id for the trial candidate.")
    parser.add_argument("--write-trial-candidate", action="store_true", help="Write the reviewed-for-trial entry.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = select_or_write_trial_candidate(
        args.vault_root,
        source_run_log_path=args.source_run_log,
        workflow_id=args.workflow_id,
        write_trial_candidate=args.write_trial_candidate,
    )
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {result.status}")
        print(f"workflow_id: {result.workflow_id}")
        print(f"workflow_entry_path: {result.workflow_entry_path}")
        print(f"next_step: {result.next_step}")
    return 0 if result.status != WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED else 1


if __name__ == "__main__":
    raise SystemExit(main())
