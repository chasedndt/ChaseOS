"""Runtime Provider Governance Layer (RPGL).

This module owns shared provider capability decisions for ChaseOS runtime
adapters. It is intentionally local-first and vault-scoped: state, queue, and
audit evidence live under runtime/providers/state beside the existing provider
state ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from runtime.agent_bus.capabilities import CapabilityError, load_all_capabilities
from runtime.chaseos_gate import (
    RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
    RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
    RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_REQUIRED_FIELDS,
    RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID,
    RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
    check_runtime_operation,
    get_runtime_operation_approval_schema,
)
from runtime.execution_adapters.model_config import ModelConfigError, load_runtime_model_config
from runtime.providers.registry import list_provider_status
from runtime.providers.state_ledger import provider_id_from_model_id


SCHEMA_VERSION = 1
FEATURE_NAME = "Runtime Provider Governance Layer"
FEATURE_ABBREVIATION = "RPGL"

STATE_RELATIVE_PATH = Path("runtime/providers/state/provider_state.json")
QUEUE_RELATIVE_PATH = Path("runtime/providers/state/provider_queue.json")
AUDIT_RELATIVE_PATH = Path("runtime/providers/state/provider_audit.jsonl")
APPROVAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_approvals")
LIVE_PROBE_DECISION_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions")
LIVE_PROBE_CONSUMER_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers")
CONFIG_PROPOSAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_config_proposals")
CONFIG_APPLY_APPROVAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_config_apply_approvals")
CONFIG_APPLY_DECISION_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_config_apply_decisions")
CONFIG_APPLY_CONSUMER_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_config_apply_consumers")
TARGET_PROFILE_PROPOSAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_target_profile_proposals")
LIVE_PROBE_MARKER_RELATIVE_DIR = Path("runtime/providers/state/provider_live_probe_markers")
LIVE_PROBE_RESULT_RELATIVE_DIR = Path("runtime/providers/state/provider_live_probe_results")
CONFIG_APPLY_MARKER_RELATIVE_DIR = Path("runtime/providers/state/provider_config_apply_markers")
CONFIG_APPLY_RESULT_RELATIVE_DIR = Path("runtime/providers/state/provider_config_apply_results")
PROVIDER_TARGET_PROFILE_RELATIVE_PATH = Path("runtime/providers/provider_target_profile.json")
SETUP_STATE_RELATIVE_PATH = Path("runtime/setup_state.json")
CHASEOS_CONFIG_RELATIVE_PATH = Path(".chaseos/config.yaml")
LOCAL_FALLBACK_SAFE_NUM_CTX = 16384
LEGACY_DEFAULT_PRIMARY_MODEL = "gpt-5.5"
OPERATOR_REPORTED_EXPECTED_MODEL = LEGACY_DEFAULT_PRIMARY_MODEL
PROVIDER_TARGET_PROFILE_SCHEMA_ID = "rpgl.provider_target_profile.v1"
PROVIDER_TARGET_PROFILE_PROPOSAL_SCHEMA_ID = "rpgl.provider_target_profile_proposal.v1"
PROVIDER_CONFIG_CHANGE_PROPOSAL_SCHEMA_ID = "rpgl.provider_config_change_proposal.v1"

PROVIDER_STRENGTHS = ("weak", "medium", "strong")
PROVIDER_STATES = ("healthy", "rate_limited", "cooling_down", "unhealthy", "disabled", "unknown")
PROBE_MODES = ("config", "network-dry-run", "live-preflight")
LIVE_PROVIDER_PROBE_APPROVAL_STATUSES = ("pending", "approved", "denied", "revoked", "expired")
CONFIG_APPLY_APPROVAL_STATUSES = ("pending", "approved", "denied", "revoked", "expired")
CONFIG_APPLY_APPROVAL_DECISIONS = ("approved", "denied")
LIVE_PROBE_APPROVAL_DECISIONS = ("approved", "denied")
LIVE_PROVIDER_PROBE_GATE_OPERATION = RUNTIME_PROVIDER_LIVE_PROBE_OPERATION
LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID = RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID
_SAFE_GATE_APPROVAL_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
LIVE_PROVIDER_PROBE_REQUIRED_APPROVAL_FIELDS = (
    "operator_request_id",
    "gate_approval_id",
    "provider_id",
    "model",
    "runtime",
    "probe_scope",
    "external_api_id",
    "timeout_policy",
    "secret_reference_metadata_only",
)

HIGH_AUTHORITY_TASK_CLASSES = frozenset(
    {
        "repo_development",
        "architecture_change",
        "yaml_registry_update",
        "multi_file_patch",
        "security_policy_change",
        "runtime_config_change",
        "provider_routing_change",
        "canonical_doc_write",
        "shell_mutation",
        "git_mutation",
        "gateway_restart",
        "deployment_action",
        "trust_tier_change",
        "permission_matrix_change",
    }
)

MEDIUM_TASK_CLASSES = frozenset(
    {
        "read_only_analysis",
        "documentation_draft",
        "test_generation",
        "config_review",
        "queue_review",
        "audit_review",
    }
)

WEAK_SAFE_TASK_CLASSES = frozenset(
    {
        "summarize_failure",
        "prompt_compression",
        "task_classification",
        "queue_item_creation",
        "retry_package_creation",
        "log_summary",
        "provider_status_summary",
        "fallback_diagnostic_summary",
    }
)

ALL_TASK_CLASSES = tuple(sorted(HIGH_AUTHORITY_TASK_CLASSES | MEDIUM_TASK_CLASSES | WEAK_SAFE_TASK_CLASSES))

AUTHORITY_MATRIX: dict[str, dict[str, str]] = {
    "summarize_failure": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "prompt_compression": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "task_classification": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "queue_item_creation": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "retry_package_creation": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "log_summary": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "provider_status_summary": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "fallback_diagnostic_summary": {"weak": "allowed", "medium": "allowed", "strong": "allowed"},
    "read_only_analysis": {"weak": "small-context only", "medium": "allowed", "strong": "allowed"},
    "documentation_draft": {"weak": "scratch only", "medium": "allowed", "strong": "allowed"},
    "test_generation": {"weak": "denied", "medium": "allowed", "strong": "allowed"},
    "config_review": {"weak": "denied", "medium": "allowed", "strong": "allowed"},
    "queue_review": {"weak": "denied", "medium": "allowed", "strong": "allowed"},
    "audit_review": {"weak": "denied", "medium": "allowed", "strong": "allowed"},
    "canonical_doc_write": {"weak": "denied", "medium": "conditional", "strong": "allowed"},
    "repo_development": {"weak": "denied", "medium": "conditional/denied", "strong": "allowed"},
    "architecture_change": {"weak": "denied", "medium": "denied by default", "strong": "allowed"},
    "yaml_registry_update": {"weak": "denied", "medium": "denied by default", "strong": "allowed"},
    "multi_file_patch": {"weak": "denied", "medium": "denied by default", "strong": "allowed"},
    "security_policy_change": {"weak": "denied", "medium": "denied", "strong": "allowed with approval"},
    "runtime_config_change": {"weak": "denied", "medium": "denied by default", "strong": "allowed"},
    "provider_routing_change": {"weak": "denied", "medium": "denied", "strong": "allowed with approval"},
    "trust_tier_change": {"weak": "denied", "medium": "denied", "strong": "allowed with approval"},
    "permission_matrix_change": {"weak": "denied", "medium": "denied", "strong": "allowed with approval"},
    "shell_mutation": {"weak": "denied", "medium": "denied by default", "strong": "allowed with approval"},
    "git_mutation": {"weak": "denied", "medium": "denied by default", "strong": "allowed with approval"},
    "gateway_restart": {"weak": "denied", "medium": "denied by default", "strong": "allowed with approval"},
    "deployment_action": {"weak": "denied", "medium": "denied", "strong": "allowed with approval"},
}

AUDIT_EVENT_TYPES = frozenset(
    {
        "primary_rate_limited",
        "primary_entered_cooldown",
        "primary_probe_started",
        "primary_probe_succeeded",
        "primary_probe_failed",
        "primary_recovered",
        "primary_recovery_failed",
        "fallback_attempt_started",
        "fallback_allowed_by_capability",
        "fallback_denied_by_capability",
        "fallback_timeout_first_token",
        "fallback_timeout_no_chunks",
        "fallback_timeout_wall_time",
        "fallback_timeout_proof_requested",
        "fallback_marked_unhealthy",
        "task_queued_for_primary_retry",
        "queue_item_created",
        "queue_item_retried",
        "queue_item_completed",
        "queue_item_failed",
        "provider_status_requested",
        "provider_state_updated",
        "provider_target_profile_requested",
        "provider_target_profile_plan_requested",
        "provider_target_profile_approval_request_created",
        "provider_live_probe_preflight_started",
        "provider_live_probe_gate_approval_schema_built",
        "provider_live_probe_approval_request_created",
        "provider_live_probe_approval_request_validated",
        "provider_live_probe_approval_request_invalid",
        "provider_live_probe_approval_decision_previewed",
        "provider_live_probe_approval_decision_created",
        "provider_live_probe_decision_record_validated",
        "provider_live_probe_decision_record_invalid",
        "provider_live_probe_decision_preflight_requested",
        "provider_live_probe_marker_contract_requested",
        "provider_live_probe_decision_consumer_record_write_blocked",
        "provider_live_probe_decision_consumer_record_written",
        "provider_live_probe_atomic_marker_write_blocked",
        "provider_live_probe_atomic_marker_written",
        "provider_live_probe_executor_blocked",
        "provider_live_probe_executor_started",
        "provider_live_probe_executor_completed",
        "provider_live_probe_executor_dry_run_requested",
        "provider_live_probe_smoke_readiness_requested",
        "provider_live_smoke_closeout_plan_requested",
        "provider_live_probe_executor_spec_requested",
        "provider_live_probe_preflight_denied",
        "provider_live_probe_result_record_written",
        "provider_live_probe_target_approval_plan_requested",
        "provider_live_probe_target_approval_request_created",
        "provider_completion_status_requested",
        "provider_config_reconciliation_requested",
        "provider_config_change_plan_requested",
        "provider_config_change_approval_request_created",
        "provider_config_apply_preflight_requested",
        "provider_config_apply_design_requested",
        "provider_config_apply_approval_request_created",
        "provider_config_apply_approval_request_validated",
        "provider_config_apply_approval_request_invalid",
        "provider_config_apply_decision_preflight_requested",
        "provider_config_apply_executor_dry_run_requested",
        "provider_config_apply_approval_decision_previewed",
        "provider_config_apply_approval_decision_created",
        "provider_config_apply_decision_record_validated",
        "provider_config_apply_decision_record_invalid",
        "provider_config_apply_decision_consumption_plan_requested",
        "provider_config_apply_decision_consumer_design_requested",
        "provider_config_apply_decision_consumer_preflight_requested",
        "provider_config_apply_decision_consumer_implementation_plan_requested",
        "provider_config_apply_decision_consumer_writer_dry_run_requested",
        "provider_config_apply_decision_consumer_write_guard_contract_requested",
        "provider_config_apply_decision_consumer_record_write_blocked",
        "provider_config_apply_decision_consumer_record_written",
        "provider_config_apply_atomic_marker_write_blocked",
        "provider_config_apply_atomic_marker_written",
        "provider_config_apply_atomic_marker_writer_design_requested",
        "provider_config_apply_live_executor_blocked",
        "provider_config_apply_live_executor_started",
        "provider_config_apply_live_executor_completed",
        "provider_config_apply_live_executor_failed",
        "provider_config_apply_rollback_completed",
        "provider_config_apply_rollback_failed",
        "credential_config_mutation_governance_lane_proof_requested",
        "runtime_status_requested",
        "scheduled_recovery_dry_run_started",
        "scheduled_recovery_dry_run_completed",
    }
)

QUEUE_STATUSES = frozenset(
    {
        "queued",
        "waiting_for_primary",
        "ready_for_retry",
        "retrying",
        "completed",
        "failed",
        "cancelled",
        "needs_operator_approval",
    }
)

QUEUE_RETRY_DRY_RUN_DENIED_ACTIONS = (
    "call_primary_provider",
    "call_fallback_provider",
    "apply_code_patches",
    "edit_provider_config",
    "edit_canonical_docs",
    "drain_high_complexity_queue",
    "restart_gateways",
    "push_git_commits",
    "deploy",
)


class RuntimeProviderGovernanceError(RuntimeError):
    """Raised when RPGL state or routing input is invalid."""


@dataclass(frozen=True)
class FallbackTimeouts:
    first_token_timeout_sec: int = 30
    no_chunk_timeout_sec: int = 60
    total_wall_time_sec: int = 180
    max_fallback_attempts: int = 1

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass
class ProviderStatusRecord:
    provider_key: str
    provider_id: str
    provider_name: str
    model: str | None
    strength: str
    state: str = "unknown"
    last_success_at: str | None = None
    last_failure_at: str | None = None
    last_error_type: str | None = None
    cooldown_until: str | None = None
    last_probe_at: str | None = None
    last_recovered_at: str | None = None
    last_no_chunk_timeout_at: str | None = None
    active_for_task_classes: list[str] = field(default_factory=list)
    denied_task_classes: list[str] = field(default_factory=list)
    runtime: str | None = None
    role: str | None = None
    is_primary: bool = False
    is_fallback: bool = False
    sticky_for_development: bool = False
    source: str = "derived"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["active_for_task_classes"] = sorted(set(self.active_for_task_classes))
        data["denied_task_classes"] = sorted(set(self.denied_task_classes))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderStatusRecord":
        return cls(
            provider_key=str(data.get("provider_key") or data.get("provider_id") or "unknown"),
            provider_id=str(data.get("provider_id") or "unknown"),
            provider_name=str(data.get("provider_name") or data.get("provider_id") or "Unknown"),
            model=data.get("model"),
            strength=normalize_provider_strength(data.get("strength")),
            state=normalize_provider_state(data.get("state")),
            last_success_at=data.get("last_success_at"),
            last_failure_at=data.get("last_failure_at"),
            last_error_type=data.get("last_error_type"),
            cooldown_until=data.get("cooldown_until"),
            last_probe_at=data.get("last_probe_at"),
            last_recovered_at=data.get("last_recovered_at"),
            last_no_chunk_timeout_at=data.get("last_no_chunk_timeout_at"),
            active_for_task_classes=list(data.get("active_for_task_classes") or []),
            denied_task_classes=list(data.get("denied_task_classes") or []),
            runtime=data.get("runtime"),
            role=data.get("role"),
            is_primary=bool(data.get("is_primary", False)),
            is_fallback=bool(data.get("is_fallback", False)),
            sticky_for_development=bool(data.get("sticky_for_development", False)),
            source=str(data.get("source") or "state"),
        )


@dataclass
class ProviderRouteDecision:
    allowed: bool
    task_class: str
    required_provider_strength: str
    decision: str
    reason: str
    route: str
    provider_id: str | None = None
    provider_name: str | None = None
    provider_model: str | None = None
    provider_strength: str | None = None
    provider_state: str | None = None
    fallback_denied_reason: str | None = None
    queue_item_id: str | None = None
    next_action: str | None = None
    files_modified: bool = False
    sticky_for_development: bool = False
    audit_event_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderQueueItem:
    task_id: str
    created_at: str
    updated_at: str
    original_request: str
    task_class: str
    required_provider_strength: str
    primary_provider_id: str | None
    primary_failure_reason: str
    fallback_denied_reason: str
    cooldown_until: str | None
    required_context_files: list[str]
    related_runtime: str
    related_adapter: str
    approval_status: str
    retry_status: str
    retry_attempts: int
    last_retry_at: str | None
    safe_next_step: str
    operator_note: str
    files_modified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderQueueItem":
        retry_status = str(data.get("retry_status") or "queued")
        if retry_status not in QUEUE_STATUSES:
            retry_status = "queued"
        return cls(
            task_id=str(data.get("task_id") or f"rpglq-{uuid.uuid4().hex[:12]}"),
            created_at=str(data.get("created_at") or _utc_now()),
            updated_at=str(data.get("updated_at") or data.get("created_at") or _utc_now()),
            original_request=str(data.get("original_request") or ""),
            task_class=normalize_task_class(data.get("task_class")),
            required_provider_strength=normalize_provider_strength(data.get("required_provider_strength") or "strong"),
            primary_provider_id=data.get("primary_provider_id"),
            primary_failure_reason=str(data.get("primary_failure_reason") or "unknown"),
            fallback_denied_reason=str(data.get("fallback_denied_reason") or "unknown"),
            cooldown_until=data.get("cooldown_until"),
            required_context_files=list(data.get("required_context_files") or []),
            related_runtime=str(data.get("related_runtime") or "unknown"),
            related_adapter=str(data.get("related_adapter") or "unknown"),
            approval_status=str(data.get("approval_status") or "not_required"),
            retry_status=retry_status,
            retry_attempts=int(data.get("retry_attempts") or 0),
            last_retry_at=data.get("last_retry_at"),
            safe_next_step=str(data.get("safe_next_step") or "Wait for primary provider recovery."),
            operator_note=str(data.get("operator_note") or ""),
            files_modified=bool(data.get("files_modified", False)),
        )


@dataclass
class ProviderAuditEvent:
    event_type: str
    runtime: str = "unknown"
    provider_id: str | None = None
    provider_name: str | None = None
    model: str | None = None
    provider_strength: str | None = None
    task_class: str | None = None
    decision: str | None = None
    reason: str | None = None
    timeout_values: dict[str, Any] = field(default_factory=dict)
    queue_item_id: str | None = None
    files_modified: bool = False
    next_action: str | None = None
    source_command: str | None = None
    operator_visible: bool = True
    timestamp: str | None = None
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        event_type = str(self.event_type)
        if event_type not in AUDIT_EVENT_TYPES:
            raise RuntimeProviderGovernanceError(f"Unsupported RPGL audit event_type: {event_type}")
        return {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.event_id or f"rpgl-{uuid.uuid4().hex[:12]}",
            "timestamp": self.timestamp or _utc_now(),
            "event_type": event_type,
            "runtime": str(self.runtime or "unknown"),
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "model": self.model,
            "provider_strength": self.provider_strength,
            "task_class": self.task_class,
            "decision": self.decision,
            "reason": self.reason,
            "timeout_values": dict(self.timeout_values or {}),
            "queue_item_id": self.queue_item_id,
            "files_modified": bool(self.files_modified),
            "next_action": self.next_action,
            "source_command": self.source_command,
            "operator_visible": bool(self.operator_visible),
        }


@dataclass(frozen=True)
class RuntimeAdapterStatus:
    runtime: str
    bus_name: str
    status: str
    last_seen: str | None = None
    source: str = "capabilities"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderProbePlan:
    provider_id: str
    provider_name: str
    model: str | None
    probe_mode: str
    configured: bool | None
    valid_setup_state: bool | None
    secret_reference_present: bool | None
    missing_setup_checks: list[str]
    live_network_call_attempted: bool = False
    secret_value_read: bool = False
    canonical_files_mutated: bool = False
    provider_state_mutated: bool = False
    status: str = "not_attempted"
    reason: str = "metadata_only_probe_plan"
    endpoint_kind: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderLiveProbePreflight:
    provider_id: str
    provider_name: str
    model: str | None
    runtime: str | None
    probe_mode: str = "live-preflight"
    gate_operation: str = LIVE_PROVIDER_PROBE_GATE_OPERATION
    gate_approval_schema_id: str = LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID
    gate_policy_allowed: bool = False
    gate_policy_reason: str = "live_provider_probe_requires_gate_approval"
    external_api_id: str | None = None
    live_probe_allowed: bool = False
    approval_required: bool = True
    approval_status: str = "missing"
    denial_reason: str = "live_provider_probe_requires_gate_approval"
    gate_approval_id: str | None = None
    required_approval_fields: tuple[str, ...] = LIVE_PROVIDER_PROBE_REQUIRED_APPROVAL_FIELDS
    approval_request_template: dict[str, Any] = field(default_factory=dict)
    approval_schema: dict[str, Any] = field(default_factory=dict)
    approval_request_written: bool = False
    approval_request_ref: str | None = None
    approval_validation: dict[str, Any] = field(default_factory=dict)
    probe_scope: str = "provider_health_check_only"
    endpoint_kind: str | None = None
    configured: bool | None = None
    valid_setup_state: bool | None = None
    secret_reference_present: bool | None = None
    missing_setup_checks: list[str] = field(default_factory=list)
    timeout_values: dict[str, Any] = field(default_factory=lambda: FallbackTimeouts().to_dict())
    live_network_call_attempted: bool = False
    secret_value_read: bool = False
    canonical_files_mutated: bool = False
    provider_state_mutated: bool = False
    queue_mutated: bool = False
    gateway_mutated: bool = False
    denied_actions: tuple[str, ...] = (
        "external_provider_call",
        "secret_value_read",
        "provider_state_update",
        "queue_retry_or_drain",
        "gateway_restart",
        "provider_config_edit",
        "canonical_file_write",
    )
    next_action: str = "request_explicit_gate_approval_before_live_probe"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_approval_fields"] = list(self.required_approval_fields)
        data["denied_actions"] = list(self.denied_actions)
        return data


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_expired(value: str | None, now: datetime | None = None) -> bool:
    parsed = _parse_time(value)
    if parsed is None:
        return False
    return parsed <= (now or datetime.now(timezone.utc))


def _provider_display_name(provider_id: str) -> str:
    labels = {
        "anthropic": "Anthropic",
        "claude": "Anthropic Claude",
        "codex": "Codex",
        "local_oss": "Local OSS",
        "ollama": "Ollama",
        "openai": "OpenAI",
        "unknown": "Unknown Provider",
        "xai": "xAI",
    }
    return labels.get(str(provider_id or "unknown"), str(provider_id or "unknown"))


def normalize_provider_strength(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    if text in PROVIDER_STRENGTHS:
        return text
    return "medium" if text == "unknown" else "weak"


def normalize_probe_mode(value: Any) -> str:
    text = str(value or "config").strip().lower()
    if text not in PROBE_MODES:
        raise RuntimeProviderGovernanceError(f"Unsupported provider probe mode {text!r}; expected one of {PROBE_MODES}")
    return text


def normalize_provider_state(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    return text if text in PROVIDER_STATES else "unknown"


def normalize_task_class(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    if text in ALL_TASK_CLASSES:
        return text
    return "needs_operator_approval"


def classify_provider_strength(provider_id: str | None, model: str | None = None) -> str:
    provider = str(provider_id or "").strip().lower()
    model_text = str(model or "").strip().lower()
    if provider in {"local_oss", "ollama", "local"}:
        return "weak"
    if model_text.startswith(("phi", "llama", "mistral", "qwen", "deepseek", "ollama", "local")):
        return "weak"
    if provider in {"openai", "claude", "anthropic", "codex"}:
        return "strong"
    if model_text.startswith(("gpt", "o1", "o3", "o4", "claude", "codex")):
        return "strong"
    return "medium"


def required_strength_for_task_class(task_class: str) -> str:
    normalized = normalize_task_class(task_class)
    if normalized in WEAK_SAFE_TASK_CLASSES:
        return "weak"
    if normalized in MEDIUM_TASK_CLASSES:
        return "medium"
    return "strong"


def task_authority_category(task_class: str) -> str:
    normalized = normalize_task_class(task_class)
    if normalized in WEAK_SAFE_TASK_CLASSES:
        return "weak_safe"
    if normalized in MEDIUM_TASK_CLASSES:
        return "medium_conditional"
    return "high_authority"


def authority_matrix_decision(task_class: str, strength: str) -> str:
    normalized = normalize_task_class(task_class)
    strength = normalize_provider_strength(strength)
    if normalized == "needs_operator_approval":
        return "denied"
    return AUTHORITY_MATRIX.get(normalized, {}).get(strength, "denied")


def is_task_allowed_for_strength(task_class: str, strength: str) -> bool:
    normalized = normalize_task_class(task_class)
    strength = normalize_provider_strength(strength)
    if normalized == "needs_operator_approval":
        return False
    decision = authority_matrix_decision(normalized, strength)
    if strength == "strong":
        return decision.startswith("allowed")
    if strength == "medium":
        return decision == "allowed"
    return decision == "allowed"


def allowed_task_classes_for_strength(strength: str) -> list[str]:
    strength = normalize_provider_strength(strength)
    return [task for task in ALL_TASK_CLASSES if is_task_allowed_for_strength(task, strength)]


def denied_task_classes_for_strength(strength: str) -> list[str]:
    allowed = set(allowed_task_classes_for_strength(strength))
    return [task for task in ALL_TASK_CLASSES if task not in allowed]


def _provider_key(runtime: str | None, role: str, provider_id: str, model: str | None) -> str:
    model_part = str(model or "unknown").replace(" ", "_").replace("/", "_")
    runtime_part = str(runtime or "runtime").lower()
    return f"{runtime_part}:{role}:{provider_id}:{model_part}"


def _state_path(vault_root: str | Path) -> Path:
    return Path(vault_root) / STATE_RELATIVE_PATH


def _queue_path(vault_root: str | Path) -> Path:
    return Path(vault_root) / QUEUE_RELATIVE_PATH


def audit_path(vault_root: str | Path) -> Path:
    return Path(vault_root) / AUDIT_RELATIVE_PATH


def approval_artifacts_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / APPROVAL_RELATIVE_DIR


def config_proposals_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / CONFIG_PROPOSAL_RELATIVE_DIR


def target_profile_proposals_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / TARGET_PROFILE_PROPOSAL_RELATIVE_DIR


def live_probe_decision_records_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / LIVE_PROBE_DECISION_RELATIVE_DIR


def live_probe_consumer_records_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / LIVE_PROBE_CONSUMER_RELATIVE_DIR


def live_probe_marker_records_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / LIVE_PROBE_MARKER_RELATIVE_DIR


def live_probe_result_records_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / LIVE_PROBE_RESULT_RELATIVE_DIR


def config_apply_approval_artifacts_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / CONFIG_APPLY_APPROVAL_RELATIVE_DIR


def config_apply_decision_records_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / CONFIG_APPLY_DECISION_RELATIVE_DIR


def config_apply_consumer_records_dir(vault_root: str | Path) -> Path:
    return Path(vault_root) / CONFIG_APPLY_CONSUMER_RELATIVE_DIR


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeProviderGovernanceError(f"Invalid RPGL JSON at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeProviderGovernanceError(f"RPGL JSON at {path} must be an object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_gate_approval_id(gate_approval_id: str) -> None:
    if not _SAFE_GATE_APPROVAL_ID.match(str(gate_approval_id or "")):
        raise RuntimeProviderGovernanceError(f"unsafe RPGL gate_approval_id: {gate_approval_id!r}")


def _approval_artifact_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = approval_artifacts_dir(vault_root).resolve()
    path = (approval_artifacts_dir(vault_root) / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL approval artifact path escapes approval directory: {path}") from exc
    return path


def _live_probe_decision_record_path(vault_root: str | Path, decision_id: str) -> Path:
    _validate_gate_approval_id(decision_id)
    base = live_probe_decision_records_dir(vault_root).resolve()
    path = (base / f"{decision_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL live probe decision path escapes decision directory: {path}") from exc
    return path


def _live_probe_marker_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = live_probe_marker_records_dir(vault_root).resolve()
    path = (base / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL live probe marker path escapes marker directory: {path}") from exc
    return path


def _live_probe_consumer_record_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = live_probe_consumer_records_dir(vault_root).resolve()
    path = (base / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL live probe consumer path escapes consumer directory: {path}") from exc
    return path


def _live_probe_result_record_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = live_probe_result_records_dir(vault_root).resolve()
    path = (base / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL live probe result path escapes result directory: {path}") from exc
    return path


def _config_apply_approval_artifact_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = config_apply_approval_artifacts_dir(vault_root).resolve()
    path = (config_apply_approval_artifacts_dir(vault_root) / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply approval path escapes approval directory: {path}") from exc
    return path


def _config_apply_decision_record_path(vault_root: str | Path, decision_id: str) -> Path:
    _validate_gate_approval_id(decision_id)
    base = config_apply_decision_records_dir(vault_root).resolve()
    path = (config_apply_decision_records_dir(vault_root) / f"{decision_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply decision path escapes decision directory: {path}") from exc
    return path


def _config_apply_marker_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = (Path(vault_root) / CONFIG_APPLY_MARKER_RELATIVE_DIR).resolve()
    path = (Path(vault_root) / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply marker path escapes marker directory: {path}") from exc
    return path


def _config_apply_result_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    base = (Path(vault_root) / CONFIG_APPLY_RESULT_RELATIVE_DIR).resolve()
    path = (Path(vault_root) / CONFIG_APPLY_RESULT_RELATIVE_DIR / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply result path escapes result directory: {path}") from exc
    return path


def _config_apply_consumer_record_path(
    vault_root: str | Path,
    gate_approval_id: str,
    selected_decision_id: str | None = None,
) -> Path:
    _validate_gate_approval_id(gate_approval_id)
    if selected_decision_id:
        _validate_gate_approval_id(selected_decision_id)
    base = config_apply_consumer_records_dir(vault_root).resolve()
    path = (base / f"{gate_approval_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply consumer path escapes consumer directory: {path}") from exc
    return path


def _approval_digest(record: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in record.items()
        if key not in {"request_digest_sha256", "approval_ref", "proposal_ref", "audit_id"}
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _decision_digest(record: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in record.items()
        if key not in {"decision_digest_sha256", "decision_ref", "audit_id", "write_audit_id"}
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _consumer_record_digest(record: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in record.items()
        if key not in {"consumer_record_digest_sha256", "consumer_record_ref", "audit_id", "write_audit_id"}
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _marker_digest(record: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in record.items()
        if key not in {"marker_digest_sha256", "marker_ref", "audit_id", "write_audit_id"}
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _new_gate_approval_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-live-probe-appr-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_provider_config_apply_gate_approval_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-config-apply-appr-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_operator_request_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-live-probe-req-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_provider_config_apply_operator_request_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-config-apply-req-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_provider_config_apply_decision_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-config-apply-decision-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_live_probe_decision_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-live-probe-decision-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_provider_config_proposal_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-provider-config-proposal-{stamp}-{uuid.uuid4().hex[:8]}"


def _new_provider_target_profile_proposal_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rpgl-target-profile-proposal-{stamp}-{uuid.uuid4().hex[:8]}"


def _provider_config_proposal_path(vault_root: str | Path, proposal_ref: str) -> Path:
    proposal = str(proposal_ref or "").strip()
    if not proposal:
        raise RuntimeProviderGovernanceError("provider config proposal id is required")
    if proposal.endswith(".json"):
        proposal = proposal[:-5]
    if not _SAFE_GATE_APPROVAL_ID.match(proposal):
        raise RuntimeProviderGovernanceError(f"unsafe RPGL provider config proposal id: {proposal_ref!r}")
    base = config_proposals_dir(vault_root).resolve()
    path = (config_proposals_dir(vault_root) / f"{proposal}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise RuntimeProviderGovernanceError(f"RPGL provider config proposal path escapes proposal directory: {path}") from exc
    return path


def build_live_probe_approval_request_record(
    preflight: dict[str, Any],
    *,
    requested_by: str,
    operator_request_id: str | None = None,
    gate_approval_id: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a non-executing RPGL live-probe approval request artifact."""
    gate_approval_id = gate_approval_id or _new_gate_approval_id()
    _validate_gate_approval_id(gate_approval_id)
    operator_request_id = operator_request_id or _new_operator_request_id()
    timeout_policy = dict(preflight.get("timeout_values") or FallbackTimeouts().to_dict())
    record = {
        "record_type": "runtime_provider_live_probe_approval_request",
        "schema_version": SCHEMA_VERSION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "operator_request_id": str(operator_request_id),
        "gate_approval_id": gate_approval_id,
        "provider_id": str(preflight.get("provider_id") or ""),
        "provider_name": str(preflight.get("provider_name") or ""),
        "model": preflight.get("model"),
        "runtime": str(preflight.get("runtime") or "unknown"),
        "probe_scope": str(preflight.get("probe_scope") or "provider_health_check_only"),
        "external_api_id": str(preflight.get("external_api_id") or ""),
        "timeout_policy": timeout_policy,
        "secret_reference_metadata_only": True,
        "credential_values_allowed": False,
        "payload_values_logged": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "canonical_files_mutated": False,
        "gateway_mutated": False,
        "status": "pending",
        "requested_by": str(requested_by or "operator"),
        "requested_at": _utc_now(),
        "approved_by": None,
        "approved_at": None,
        "approval_effect": (
            "Records operator intent to review one future live provider health probe. "
            "This artifact does not execute the probe and this pass has no live probe executor."
        ),
        "denied_actions": list(preflight.get("denied_actions") or ()),
        "source_command": source_command,
    }
    record["request_digest_sha256"] = _approval_digest(record)
    return record


def write_live_probe_approval_request(
    vault_root: str | Path,
    preflight: dict[str, Any],
    *,
    requested_by: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist a pending live-probe approval request without executing anything."""
    record = build_live_probe_approval_request_record(
        preflight,
        requested_by=requested_by,
        source_command=source_command,
    )
    path = _approval_artifact_path(vault_root, str(record["gate_approval_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeProviderGovernanceError(f"RPGL approval request already exists: {record['gate_approval_id']}")
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_approval_request_created",
            runtime=str(record.get("runtime") or "unknown"),
            provider_id=str(record.get("provider_id") or "") or None,
            provider_name=str(record.get("provider_name") or "") or None,
            model=record.get("model"),
            decision="approval_request_created",
            reason="pending_live_provider_probe_approval_request_written",
            files_modified=True,
            next_action="operator_review_required_before_any_live_probe_executor",
            source_command=source_command,
        ),
    )
    return {
        **record,
        "approval_ref": str(path),
        "approval_request_written": True,
        "files_modified": True,
        "audit_id": event["event_id"],
    }


def load_live_probe_approval_request(vault_root: str | Path, gate_approval_id: str) -> dict[str, Any]:
    path = _approval_artifact_path(vault_root, gate_approval_id)
    if not path.exists():
        raise RuntimeProviderGovernanceError(f"RPGL approval request not found: {gate_approval_id}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeProviderGovernanceError(f"Invalid RPGL approval JSON at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeProviderGovernanceError(f"RPGL approval JSON at {path} must be an object")
    data["approval_ref"] = str(path)
    return data


def validate_live_probe_approval_request(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    expected_preflight: dict[str, Any] | None = None,
    source_command: str | None = None,
    write_audit: bool = True,
) -> dict[str, Any]:
    """Validate an RPGL live-probe approval artifact without authorizing execution."""
    record = load_live_probe_approval_request(vault_root, gate_approval_id)
    errors: list[str] = []
    warnings: list[str] = []

    if record.get("record_type") != "runtime_provider_live_probe_approval_request":
        errors.append("record_type must be runtime_provider_live_probe_approval_request")
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if record.get("approval_schema_id") != LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID:
        errors.append(f"approval_schema_id must be {LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID}")
    if record.get("operation") != LIVE_PROVIDER_PROBE_GATE_OPERATION:
        errors.append(f"operation must be {LIVE_PROVIDER_PROBE_GATE_OPERATION}")
    if record.get("gate_approval_id") != gate_approval_id:
        errors.append("gate_approval_id does not match requested artifact id")

    for field_name in LIVE_PROVIDER_PROBE_REQUIRED_APPROVAL_FIELDS:
        value = record.get(field_name)
        if value is None or value == "":
            errors.append(f"required field missing: {field_name}")

    status = str(record.get("status") or "missing")
    if status not in LIVE_PROVIDER_PROBE_APPROVAL_STATUSES:
        errors.append(f"unsupported approval status: {status}")

    if record.get("secret_reference_metadata_only") is not True:
        errors.append("secret_reference_metadata_only must be true")
    for flag_name in [
        "credential_values_allowed",
        "payload_values_logged",
        "live_network_call_attempted",
        "secret_value_read",
        "provider_state_mutated",
        "queue_mutated",
        "canonical_files_mutated",
        "gateway_mutated",
    ]:
        if record.get(flag_name) is not False:
            errors.append(f"{flag_name} must be false")

    if "request_digest_sha256" in record:
        expected_digest = _approval_digest(record)
        if record.get("request_digest_sha256") != expected_digest:
            warnings.append("request_digest_sha256 does not match current artifact content")

    mismatches: list[str] = []
    if expected_preflight:
        comparisons = {
            "provider_id": expected_preflight.get("provider_id"),
            "model": expected_preflight.get("model"),
            "runtime": expected_preflight.get("runtime"),
            "probe_scope": expected_preflight.get("probe_scope"),
            "external_api_id": expected_preflight.get("external_api_id"),
        }
        for field_name, expected_value in comparisons.items():
            if expected_value is not None and record.get(field_name) != expected_value:
                mismatches.append(field_name)
        expected_timeout = dict(expected_preflight.get("timeout_values") or {})
        if expected_timeout and record.get("timeout_policy") != expected_timeout:
            mismatches.append("timeout_policy")
    if mismatches:
        errors.append("approval artifact does not match preflight fields: " + ", ".join(sorted(mismatches)))

    structurally_valid = not errors
    approval_decision_accepted = structurally_valid and status == "approved"
    validation = {
        "gate_approval_id": gate_approval_id,
        "approval_ref": record.get("approval_ref"),
        "approval_schema_id": record.get("approval_schema_id"),
        "operation": record.get("operation"),
        "approval_status": status,
        "structurally_valid": structurally_valid,
        "matches_preflight": not mismatches,
        "approval_decision_accepted": approval_decision_accepted,
        "live_probe_execution_allowed": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "canonical_files_mutated": False,
        "errors": errors,
        "warnings": warnings,
        "reason": (
            "approval_artifact_validation_only_executor_not_built"
            if structurally_valid
            else "approval_artifact_invalid"
        ),
    }
    if write_audit:
        event_type = (
            "provider_live_probe_approval_request_validated"
            if structurally_valid
            else "provider_live_probe_approval_request_invalid"
        )
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type=event_type,
                runtime=str(record.get("runtime") or "unknown"),
                provider_id=str(record.get("provider_id") or "") or None,
                provider_name=str(record.get("provider_name") or "") or None,
                model=record.get("model"),
                decision="approval_artifact_validated" if structurally_valid else "approval_artifact_invalid",
                reason=validation["reason"],
                files_modified=False,
                next_action=(
                    "live_probe_executor_still_not_built"
                    if structurally_valid
                    else "operator_must_recreate_or_fix_approval_artifact"
                ),
                source_command=source_command,
            ),
        )
        validation["audit_id"] = event["event_id"]
    return validation


def load_live_probe_decision_records(vault_root: str | Path, *, gate_approval_id: str) -> list[dict[str, Any]]:
    _validate_gate_approval_id(gate_approval_id)
    directory = live_probe_decision_records_dir(vault_root)
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeProviderGovernanceError(f"Invalid RPGL live probe decision JSON at {path}: {exc}") from exc
        if isinstance(data, dict) and data.get("gate_approval_id") == gate_approval_id:
            data["decision_ref"] = str(path)
            records.append(data)
    return records


def build_live_probe_approval_decision_record(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    decision: str,
    decided_by: str,
    reason: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Preview an immutable live-provider-probe approval decision record without writing it."""
    decision_text = str(decision or "").strip().lower()
    if decision_text not in LIVE_PROBE_APPROVAL_DECISIONS:
        raise RuntimeProviderGovernanceError(
            f"live provider probe approval decision must be one of {', '.join(LIVE_PROBE_APPROVAL_DECISIONS)}"
        )
    approval = load_live_probe_approval_request(vault_root, gate_approval_id)
    validation = validate_live_probe_approval_request(
        vault_root,
        gate_approval_id,
        source_command=source_command,
        write_audit=False,
    )
    existing = load_live_probe_decision_records(vault_root, gate_approval_id=gate_approval_id)
    blocked_reasons: list[str] = []
    if not validation.get("structurally_valid"):
        blocked_reasons.append("approval_artifact_invalid")
    if existing:
        blocked_reasons.append("immutable_decision_already_exists")
    writable = not blocked_reasons
    record = {
        "record_type": "runtime_provider_live_probe_approval_decision",
        "schema_version": SCHEMA_VERSION,
        "decision_schema_id": "rpgl.live_provider_probe_decision.v1",
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "decision_id": _new_live_probe_decision_id(),
        "gate_approval_id": gate_approval_id,
        "provider_id": approval.get("provider_id"),
        "provider_name": approval.get("provider_name"),
        "model": approval.get("model"),
        "runtime": approval.get("runtime"),
        "external_api_id": approval.get("external_api_id"),
        "probe_scope": approval.get("probe_scope"),
        "decision": decision_text,
        "decision_status": "preview",
        "decision_record_writable": writable,
        "decision_record_written": False,
        "decided_by": str(decided_by or "operator"),
        "decided_at": _utc_now(),
        "reason": str(reason or ""),
        "approval_ref": approval.get("approval_ref"),
        "approval_artifact_status_at_decision": validation.get("approval_status"),
        "approval_structurally_valid": bool(validation.get("structurally_valid")),
        "approval_request_digest_sha256": approval.get("request_digest_sha256"),
        "existing_decision_count": len(existing),
        "existing_decision_ids": [item.get("decision_id") for item in existing],
        "blocked_reasons": blocked_reasons,
        "decision_effect": (
            "records_operator_approval_for_one_future_live_probe_attempt_only"
            if decision_text == "approved"
            else "records_operator_denial_and_blocks_future_live_probe_attempt"
        ),
        "immutable": True,
        "append_only": True,
        "execution_enabled": False,
        "live_probe_execution_allowed": False,
        "approval_consumed": False,
        "decision_consumed": False,
        "approval_artifact_mutated": False,
        "idempotency_marker_written": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "files_modified": False,
        "source_command": source_command,
    }
    record["decision_digest_sha256"] = _decision_digest(record)
    append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_approval_decision_previewed",
            runtime=str(record.get("runtime") or "unknown"),
            provider_id=str(record.get("provider_id") or "") or None,
            provider_name=str(record.get("provider_name") or "") or None,
            model=record.get("model"),
            decision=f"approval_decision_previewed_{decision_text}",
            reason="immutable_live_probe_approval_decision_previewed_without_execution",
            files_modified=False,
            next_action="write_decision_record_only_with_explicit_operator_action",
            source_command=source_command,
        ),
    )
    return record


def write_live_probe_approval_decision_record(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    decision: str,
    decided_by: str,
    reason: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist an immutable live-provider-probe approval decision without consuming it."""
    record = build_live_probe_approval_decision_record(
        vault_root,
        gate_approval_id,
        decision=decision,
        decided_by=decided_by,
        reason=reason,
        source_command=source_command,
    )
    if not record.get("decision_record_writable"):
        raise RuntimeProviderGovernanceError(
            "live provider probe approval decision is not writable: "
            + ", ".join(record.get("blocked_reasons") or ["unknown"])
        )
    path = _live_probe_decision_record_path(vault_root, str(record["decision_id"]))
    if path.exists():
        raise RuntimeProviderGovernanceError(f"RPGL live probe decision already exists: {record['decision_id']}")
    written = dict(record)
    written["decision_status"] = "recorded"
    written["decision_record_written"] = True
    written["files_modified"] = True
    written["decision_ref"] = str(path)
    written["decision_digest_sha256"] = _decision_digest(written)
    _write_json(path, written)
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_approval_decision_created",
            runtime=str(written.get("runtime") or "unknown"),
            provider_id=str(written.get("provider_id") or "") or None,
            provider_name=str(written.get("provider_name") or "") or None,
            model=written.get("model"),
            decision=f"approval_decision_recorded_{written.get('decision')}",
            reason="immutable_live_probe_approval_decision_record_written_without_execution",
            files_modified=True,
            next_action="future_executor_must_validate_and_consume_decision_record_before_live_probe",
            source_command=source_command,
        ),
    )
    written["write_audit_id"] = event["event_id"]
    _write_json(path, written)
    return written


def validate_live_probe_decision_records(vault_root: str | Path, *, gate_approval_id: str) -> dict[str, Any]:
    records = load_live_probe_decision_records(vault_root, gate_approval_id=gate_approval_id)
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_schema_id": "rpgl.live_provider_probe_decision.v1",
        "gate_approval_id": gate_approval_id,
        "records_found": len(records),
        "record_refs": [record.get("decision_ref") for record in records],
        "decision_ids": [record.get("decision_id") for record in records],
        "status": "missing",
        "decision": None,
        "selected_decision_id": None,
        "selected_decision_ref": None,
        "structurally_valid": False,
        "decision_digest_valid": False,
        "decision_record_consumable": False,
        "live_probe_execution_allowed": False,
        "decision_consumed": False,
        "approval_artifact_mutated": False,
        "idempotency_marker_written": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "errors": [],
        "warnings": [],
    }
    if not records:
        summary["errors"].append("immutable_decision_record_missing")
    elif len(records) > 1:
        summary["status"] = "multiple"
        summary["errors"].append("multiple_immutable_decision_records_for_gate_approval_id")
    else:
        record = records[0]
        decision = str(record.get("decision") or "")
        recorded_digest = str(record.get("decision_digest_sha256") or "")
        expected_digest = _decision_digest(record)
        checks = {
            "record_type": record.get("record_type") == "runtime_provider_live_probe_approval_decision",
            "schema_version": record.get("schema_version") == SCHEMA_VERSION,
            "decision_schema_id": record.get("decision_schema_id") == "rpgl.live_provider_probe_decision.v1",
            "operation": record.get("operation") == LIVE_PROVIDER_PROBE_GATE_OPERATION,
            "gate_approval_id": record.get("gate_approval_id") == gate_approval_id,
            "decision": decision in LIVE_PROBE_APPROVAL_DECISIONS,
            "decision_status": record.get("decision_status") == "recorded",
            "decision_record_written": record.get("decision_record_written") is True,
            "immutable": record.get("immutable") is True,
            "append_only": record.get("append_only") is True,
            "execution_disabled": record.get("execution_enabled") is False and record.get("live_probe_execution_allowed") is False,
            "no_prior_consumption": record.get("decision_consumed") is False and record.get("approval_consumed") is False,
            "no_mutation_claims": (
                record.get("provider_state_mutated") is False
                and record.get("idempotency_marker_written") is False
                and record.get("queue_mutated") is False
                and record.get("gateway_mutated") is False
                and record.get("canonical_files_mutated") is False
                and record.get("live_network_call_attempted") is False
                and record.get("secret_value_read") is False
            ),
            "decision_digest_sha256": bool(recorded_digest) and recorded_digest == expected_digest,
        }
        for check_id, passed in checks.items():
            if not passed:
                summary["errors"].append(f"decision_record_{check_id}_invalid")
        valid = not summary["errors"]
        summary.update(
            {
                "status": decision if valid else "invalid",
                "decision": decision if valid else None,
                "selected_decision_id": record.get("decision_id") if valid else None,
                "selected_decision_ref": record.get("decision_ref") if valid else None,
                "structurally_valid": valid,
                "decision_digest_valid": bool(checks["decision_digest_sha256"]),
                "decision_record_consumable": valid and decision == "approved",
            }
        )
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_decision_record_validated"
            if summary["structurally_valid"]
            else "provider_live_probe_decision_record_invalid",
            runtime="cli",
            decision=str(summary.get("status") or "missing"),
            reason="immutable_live_probe_decision_validation",
            files_modified=False,
            next_action="live_probe_executor_still_not_built",
        ),
    )
    summary["audit_id"] = event["event_id"]
    return summary


def _load_persisted_provider_records(vault_root: str | Path) -> dict[str, ProviderStatusRecord]:
    data = _read_json(_state_path(vault_root), {"schema_version": SCHEMA_VERSION, "providers": {}})
    providers = data.get("providers") or {}
    if not isinstance(providers, dict):
        raise RuntimeProviderGovernanceError("RPGL provider state 'providers' must be an object")
    return {
        str(key): ProviderStatusRecord.from_dict({"provider_key": key, **value})
        for key, value in providers.items()
        if isinstance(value, dict)
    }


def _save_provider_records(vault_root: str | Path, records: dict[str, ProviderStatusRecord]) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": _utc_now(),
        "providers": {key: record.to_dict() for key, record in sorted(records.items())},
    }
    _write_json(_state_path(vault_root), payload)


def _derive_records_from_model_configs(vault_root: str | Path) -> dict[str, ProviderStatusRecord]:
    root = Path(vault_root)
    records: dict[str, ProviderStatusRecord] = {}
    runtime_root = root / "runtime"
    if not runtime_root.exists():
        return records
    for runtime_dir in sorted(item for item in runtime_root.iterdir() if item.is_dir()):
        runtime_name = runtime_dir.name
        try:
            config = load_runtime_model_config(runtime_name, root)
        except ModelConfigError:
            continue
        for order, spec in enumerate(config.all_models()):
            role = "primary" if order == 0 else "fallback"
            provider_id = provider_id_from_model_id(spec.model_id) or "unknown"
            strength = classify_provider_strength(provider_id, spec.model_id)
            key = _provider_key(runtime_name, role, provider_id, spec.model_id)
            records[key] = ProviderStatusRecord(
                provider_key=key,
                provider_id=provider_id,
                provider_name=_provider_display_name(provider_id),
                model=spec.model_id,
                strength=strength,
                state="unknown",
                active_for_task_classes=allowed_task_classes_for_strength(strength),
                denied_task_classes=denied_task_classes_for_strength(strength),
                runtime=runtime_name,
                role=role,
                is_primary=role == "primary",
                is_fallback=role == "fallback",
                sticky_for_development=False,
                source="model_config",
            )
    return records


def load_provider_records(vault_root: str | Path) -> dict[str, ProviderStatusRecord]:
    """Load provider state merged with current model-config-derived records."""
    derived = _derive_records_from_model_configs(vault_root)
    persisted = _load_persisted_provider_records(vault_root)
    merged = dict(derived)
    for key, persisted_record in persisted.items():
        if key in merged:
            base = merged[key]
            merged[key] = ProviderStatusRecord(
                provider_key=base.provider_key,
                provider_id=base.provider_id,
                provider_name=base.provider_name,
                model=base.model,
                strength=base.strength,
                state=persisted_record.state,
                last_success_at=persisted_record.last_success_at,
                last_failure_at=persisted_record.last_failure_at,
                last_error_type=persisted_record.last_error_type,
                cooldown_until=persisted_record.cooldown_until,
                last_probe_at=persisted_record.last_probe_at,
                last_recovered_at=persisted_record.last_recovered_at,
                last_no_chunk_timeout_at=persisted_record.last_no_chunk_timeout_at,
                active_for_task_classes=base.active_for_task_classes,
                denied_task_classes=base.denied_task_classes,
                runtime=base.runtime,
                role=base.role,
                is_primary=base.is_primary,
                is_fallback=base.is_fallback,
                sticky_for_development=False,
                source=base.source,
            )
        else:
            persisted_record.active_for_task_classes = allowed_task_classes_for_strength(persisted_record.strength)
            persisted_record.denied_task_classes = denied_task_classes_for_strength(persisted_record.strength)
            persisted_record.sticky_for_development = False
            merged[key] = persisted_record
    return merged


def _provider_setup_by_id() -> dict[str, dict[str, Any]]:
    try:
        return {str(item.get("provider_id")): item for item in list_provider_status() if item.get("provider_id")}
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _endpoint_kind_for_provider(provider_id: str | None) -> str:
    return {
        "claude": "anthropic_messages",
        "openai": "openai_responses_or_models",
        "xai": "xai_models",
        "local_oss": "local_ollama_or_oss_endpoint",
        "ollama": "local_ollama_endpoint",
    }.get(str(provider_id or "unknown"), "unknown")


def _external_api_for_provider(provider_id: str | None) -> str:
    normalized = str(provider_id or "unknown").strip().lower()
    return {
        "claude": "provider.anthropic",
        "anthropic": "provider.anthropic",
        "openai": "provider.openai",
        "codex": "provider.openai",
        "local_oss": "provider.local_oss_endpoint",
        "ollama": "provider.local_oss_endpoint",
    }.get(normalized, f"provider.{normalized}")


def _read_optional_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"invalid_json:{exc}"
    if not isinstance(data, dict):
        return {}, "json_root_not_object"
    return data, None


def _secret_reference_target_is_placeholder(target: Any) -> bool:
    value = str(target or "").strip()
    return value in {"<env-var>", "<secret-ref>", "SET_OPENAI_SECRET_REF"} or (
        value.startswith("SET_") and value.endswith("_SECRET_REF")
    )


def _probe_secret_reference_existence(kind: Any, target: Any) -> dict[str, Any]:
    reference_kind = str(kind or "").strip() or None
    reference_target = str(target or "").strip()
    if not reference_kind or not reference_target:
        return {"checked": False, "exists": False, "error": "missing_reference_target"}

    if reference_kind in {"env-var", "env-var-or-local-secret-ref"}:
        if reference_target in os.environ:
            return {"checked": True, "exists": True, "source": "env-var", "error": None}
        if reference_kind == "env-var":
            return {"checked": True, "exists": False, "source": "env-var", "error": "env_var_missing"}

    if Path(reference_target).exists():
        return {"checked": True, "exists": True, "source": "local-path", "error": None}

    return {"checked": True, "exists": False, "source": reference_kind, "error": "reference_not_found"}


def _provider_secret_reference_summary(config_report: dict[str, Any], provider_id: str) -> dict[str, Any]:
    setup = config_report.get("provider_setup_state") if isinstance(config_report.get("provider_setup_state"), dict) else {}
    providers = setup.get("providers") if isinstance(setup.get("providers"), dict) else {}
    provider = providers.get(provider_id) if isinstance(providers.get(provider_id), dict) else {}
    kind = provider.get("secret_reference_kind")
    target = provider.get("secret_reference_target")
    probe = _probe_secret_reference_existence(kind, target)
    target_is_placeholder = _secret_reference_target_is_placeholder(target)
    return {
        "provider_id": provider_id,
        "current_secret_reference_kind": kind,
        "current_secret_reference_target": target,
        "current_secret_reference_target_is_placeholder": target_is_placeholder,
        "current_secret_reference_resolvable": bool(probe.get("exists")) and not target_is_placeholder,
        "secret_reference_probe": probe,
        "secret_reference_probe_source": probe.get("source"),
        "secret_reference_probe_error": probe.get("error"),
    }


def _known_provider_config_files(vault_root: str | Path) -> list[Path]:
    root = Path(vault_root)
    candidates = [
        SETUP_STATE_RELATIVE_PATH,
        CHASEOS_CONFIG_RELATIVE_PATH,
        Path(".codex/config.toml"),
        Path(".codex/config.yaml"),
        Path(".codex/config.json"),
        Path(".claude/settings.json"),
        Path("runtime/policy/adapters/local_oss.yaml"),
        Path("runtime/policy/adapters/openai.yaml"),
        Path("runtime/policy/adapters/openai_config.yaml"),
        Path("runtime/policy/adapters/codex.yaml"),
        Path("runtime/policy/adapters/hermes.yaml"),
        Path("runtime/policy/adapters/hermes_config.yaml"),
        Path("runtime/policy/adapters/openclaw.yaml"),
    ]
    runtime_root = root / "runtime"
    if runtime_root.exists():
        for runtime_dir in sorted(item for item in runtime_root.iterdir() if item.is_dir()):
            model_config = runtime_dir / "model_config.yaml"
            if model_config.exists():
                try:
                    candidates.append(model_config.relative_to(root))
                except ValueError:
                    continue
    seen: set[Path] = set()
    paths: list[Path] = []
    for relative in candidates:
        path = root / relative
        if relative not in seen and path.exists() and path.is_file():
            seen.add(relative)
            paths.append(path)
    return paths


def _scan_provider_config_file(path: Path, vault_root: str | Path, expected_model: str) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "path": str(path),
            "relative_path": str(path),
            "readable": False,
            "error": str(exc),
            "contains_expected_model": False,
            "contains_gpt_5_4": False,
            "contains_phi4": False,
            "contains_ollama": False,
            "context_values": [],
        }
    root = Path(vault_root).resolve()
    try:
        relative_path = path.resolve().relative_to(root).as_posix()
    except ValueError:
        relative_path = str(path)
    context_values: list[dict[str, Any]] = []
    for match in re.finditer(r"\b(num_ctx|context_length|context_window|ollama_context_length)\b\s*[:=]\s*([0-9]+)", text, re.IGNORECASE):
        try:
            value = int(match.group(2))
        except ValueError:
            continue
        context_values.append({"key": match.group(1), "value": value})
    lower = text.lower()
    return {
        "path": str(path),
        "relative_path": relative_path,
        "readable": True,
        "contains_expected_model": expected_model.lower() in lower,
        "contains_gpt_5_4": "gpt-5.4" in lower,
        "contains_phi4": "phi4" in lower,
        "contains_ollama": "ollama" in lower,
        "context_values": context_values,
    }


def _as_model_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def _normalize_runtime_target(
    runtime_name: str,
    raw: Any,
    *,
    default_primary_model: str,
    profile_source: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    desired_primary = (
        raw.get("primary_model")
        or raw.get("primary")
        or raw.get("model")
        or default_primary_model
    )
    desired_fallbacks = _as_model_list(raw.get("fallback_models", raw.get("fallbacks")))
    enforcement = str(raw.get("fallback_enforcement") or "observe_only")
    if enforcement not in {"observe_only", "minimum", "exact"}:
        enforcement = "observe_only"
    return {
        "runtime": runtime_name,
        "desired_primary_model": str(desired_primary),
        "desired_fallback_models": desired_fallbacks,
        "fallback_enforcement": enforcement,
        "profile_source": profile_source,
    }


def build_provider_target_profile(
    vault_root: str | Path,
    *,
    expected_model: str = OPERATOR_REPORTED_EXPECTED_MODEL,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the active provider target profile without mutating config.

    If `runtime/providers/provider_target_profile.json` exists, it is the
    operator-declared target profile. If it does not exist, ChaseOS keeps the
    legacy GPT-5.5 default as a compatibility target, but reports that this is
    a fallback profile rather than permanent source truth.
    """
    root = Path(vault_root)
    profile_path = root / PROVIDER_TARGET_PROFILE_RELATIVE_PATH
    profile_raw, profile_error = _read_optional_json(profile_path)
    profile_exists = profile_path.exists() and isinstance(profile_raw, dict)
    profile_source = str(profile_path) if profile_exists else "legacy_default_expected_primary_model"
    default_primary_model = str(
        (profile_raw.get("default_primary_model") if profile_exists else None)
        or (profile_raw.get("expected_primary_model") if profile_exists else None)
        or expected_model
    )
    raw_runtime_targets = (
        profile_raw.get("runtime_targets", {}) if profile_exists and isinstance(profile_raw.get("runtime_targets", {}), dict) else {}
    )
    runtime_targets: dict[str, dict[str, Any]] = {}
    runtime_root = root / "runtime"
    discovered_runtime_names: set[str] = set()
    if runtime_root.exists():
        for runtime_dir in sorted(item for item in runtime_root.iterdir() if item.is_dir()):
            if (runtime_dir / "model_config.yaml").exists():
                discovered_runtime_names.add(runtime_dir.name)
    for runtime_name in sorted(discovered_runtime_names | {str(name) for name in raw_runtime_targets.keys()}):
        runtime_targets[runtime_name] = _normalize_runtime_target(
            runtime_name,
            raw_runtime_targets.get(runtime_name, {}),
            default_primary_model=default_primary_model,
            profile_source=profile_source,
        )

    raw_setup_targets = (
        profile_raw.get("provider_setup_targets", {})
        if profile_exists and isinstance(profile_raw.get("provider_setup_targets", {}), dict)
        else {}
    )
    provider_setup_targets: dict[str, dict[str, Any]] = {}
    if "openai" not in raw_setup_targets:
        provider_setup_targets["openai"] = {
            "default_model": default_primary_model,
            "profile_source": profile_source,
        }
    for provider_id, target in raw_setup_targets.items():
        if not isinstance(target, dict):
            continue
        provider_setup_targets[str(provider_id)] = {
            "default_model": str(target.get("default_model") or default_primary_model),
            "profile_source": profile_source,
        }

    raw_local = profile_raw.get("local_fallback", {}) if profile_exists and isinstance(profile_raw.get("local_fallback", {}), dict) else {}
    local_fallback_target = {
        "provider_id": str(raw_local.get("provider_id") or "local_oss"),
        "model": str(raw_local.get("model") or "phi4-mini:latest"),
        "strength": str(raw_local.get("strength") or "weak"),
        "enabled": bool(raw_local.get("enabled", False)),
        "num_ctx": int(raw_local.get("num_ctx") or LOCAL_FALLBACK_SAFE_NUM_CTX),
        "max_default_num_ctx": LOCAL_FALLBACK_SAFE_NUM_CTX,
        "authority": str(raw_local.get("authority") or "recovery_assistant_only"),
        "profile_source": profile_source,
    }
    if local_fallback_target["num_ctx"] > LOCAL_FALLBACK_SAFE_NUM_CTX:
        local_fallback_target["safety_status"] = "unsafe_context_above_16384"
    else:
        local_fallback_target["safety_status"] = "safe_context_limit"

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_target_profile_requested",
            runtime="cli",
            provider_id="openai",
            model=default_primary_model,
            provider_strength="strong",
            task_class="config_review",
            decision="provider_target_profile_read",
            reason="operator_requested_provider_target_profile",
            files_modified=False,
            next_action="use_target_profile_for_config_reconciliation",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "profile_schema_id": PROVIDER_TARGET_PROFILE_SCHEMA_ID,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "profile_ref": str(profile_path),
        "profile_exists": profile_exists,
        "profile_source": profile_source,
        "profile_error": profile_error,
        "default_primary_model": default_primary_model,
        "runtime_targets": runtime_targets,
        "provider_setup_targets": provider_setup_targets,
        "local_fallback_target": local_fallback_target,
        "read_only": True,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "setup_state_mutated": False,
        "model_config_mutated": False,
        "files_modified": False,
        "audit_id": event["event_id"],
    }


def _target_profile_digest(profile: dict[str, Any]) -> str:
    canonical = json.dumps(profile, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _candidate_runtime_targets_from_reconciliation(
    reconciliation: dict[str, Any],
    *,
    desired_primary_model: str,
) -> dict[str, dict[str, Any]]:
    targets: dict[str, dict[str, Any]] = {}
    for item in reconciliation.get("runtime_model_configs") or []:
        runtime_name = str(item.get("runtime") or "").strip()
        if not runtime_name:
            continue
        targets[runtime_name] = {
            "primary_model": desired_primary_model,
            "fallback_models": _as_model_list(item.get("fallback_models")),
            "fallback_enforcement": "observe_only",
        }

    active_profile = reconciliation.get("target_profile") if isinstance(reconciliation.get("target_profile"), dict) else {}
    active_targets = active_profile.get("runtime_targets") if isinstance(active_profile.get("runtime_targets"), dict) else {}
    for runtime_name, target in active_targets.items():
        if str(runtime_name) in targets or not isinstance(target, dict):
            continue
        targets[str(runtime_name)] = {
            "primary_model": desired_primary_model,
            "fallback_models": _as_model_list(target.get("desired_fallback_models") or target.get("fallback_models")),
            "fallback_enforcement": str(target.get("fallback_enforcement") or "observe_only"),
        }
    return dict(sorted(targets.items()))


def _build_candidate_provider_target_profile(
    reconciliation: dict[str, Any],
    *,
    desired_primary_model: str,
) -> dict[str, Any]:
    provider_id = provider_id_from_model_id(desired_primary_model) or "primary_provider"
    active_profile = reconciliation.get("target_profile") if isinstance(reconciliation.get("target_profile"), dict) else {}
    active_local = active_profile.get("local_fallback_target") if isinstance(active_profile.get("local_fallback_target"), dict) else {}
    local_num_ctx = int(active_local.get("num_ctx") or LOCAL_FALLBACK_SAFE_NUM_CTX)
    if local_num_ctx > LOCAL_FALLBACK_SAFE_NUM_CTX:
        local_num_ctx = LOCAL_FALLBACK_SAFE_NUM_CTX
    return {
        "schema_version": SCHEMA_VERSION,
        "profile_schema_id": PROVIDER_TARGET_PROFILE_SCHEMA_ID,
        "default_primary_model": desired_primary_model,
        "runtime_targets": _candidate_runtime_targets_from_reconciliation(
            reconciliation,
            desired_primary_model=desired_primary_model,
        ),
        "provider_setup_targets": {
            provider_id: {
                "default_model": desired_primary_model,
            }
        },
        "local_fallback": {
            "provider_id": str(active_local.get("provider_id") or "local_oss"),
            "model": str(active_local.get("model") or "phi4-mini:latest"),
            "strength": str(active_local.get("strength") or "weak"),
            "enabled": bool(active_local.get("enabled", False)),
            "num_ctx": local_num_ctx,
            "authority": str(active_local.get("authority") or "recovery_assistant_only"),
        },
    }


def _find_open_provider_target_profile_queue_item(
    vault_root: str | Path,
    profile_digest: str,
) -> ProviderQueueItem | None:
    marker = f"provider_target_profile_change:{profile_digest}"
    for item in load_queue_items(vault_root):
        if (
            item.task_class == "runtime_config_change"
            and marker in item.original_request
            and item.retry_status in {"queued", "waiting_for_primary", "ready_for_retry", "needs_operator_approval"}
        ):
            return item
    return None


def build_provider_target_profile_plan(
    vault_root: str | Path,
    *,
    target_model: str | None = None,
    expected_model: str = OPERATOR_REPORTED_EXPECTED_MODEL,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a non-mutating candidate provider target profile.

    This is a governance planning surface only. It allows the current ChaseOS
    instance to target GPT-5.5 while keeping the same schema valid for another
    primary model/provider and for per-runtime fallback chains.
    """
    root = Path(vault_root)
    reconciliation = build_provider_config_reconciliation(
        root,
        expected_model=expected_model,
        source_command=source_command,
    )
    active_profile = reconciliation.get("target_profile") if isinstance(reconciliation.get("target_profile"), dict) else {}
    desired_primary_model = str(target_model or active_profile.get("default_primary_model") or expected_model)
    candidate_profile = _build_candidate_provider_target_profile(
        reconciliation,
        desired_primary_model=desired_primary_model,
    )
    candidate_digest = _target_profile_digest(candidate_profile)
    current_profile_exists = bool(active_profile.get("profile_exists"))
    current_profile_digest = _target_profile_digest(
        {
            "schema_version": SCHEMA_VERSION,
            "profile_schema_id": PROVIDER_TARGET_PROFILE_SCHEMA_ID,
            "default_primary_model": active_profile.get("default_primary_model"),
            "runtime_targets": active_profile.get("runtime_targets") or {},
            "provider_setup_targets": active_profile.get("provider_setup_targets") or {},
            "local_fallback": active_profile.get("local_fallback_target") or {},
        }
    )
    profile_change_needed = (not current_profile_exists) or candidate_digest != current_profile_digest
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_target_profile_plan_requested",
            runtime="cli",
            provider_id=provider_id_from_model_id(desired_primary_model) or "primary_provider",
            model=desired_primary_model,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="provider_target_profile_plan_built",
            reason="operator_requested_provider_target_profile_plan",
            files_modified=False,
            next_action="write_approval_request_before_target_profile_file_mutation" if profile_change_needed else "no_target_profile_change_needed",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "proposal_schema_id": PROVIDER_TARGET_PROFILE_PROPOSAL_SCHEMA_ID,
        "generated_at": _utc_now(),
        "plan_status": (
            "profile_missing_candidate_ready"
            if not current_profile_exists
            else ("candidate_differs_from_current_profile" if profile_change_needed else "no_changes_needed")
        ),
        "target_model_source": "cli_target" if target_model else "active_profile_or_legacy_default",
        "target_profile_ref": str(root / PROVIDER_TARGET_PROFILE_RELATIVE_PATH),
        "desired_default_primary_model": desired_primary_model,
        "candidate_profile": candidate_profile,
        "candidate_profile_digest_sha256": candidate_digest,
        "current_profile_digest_sha256": current_profile_digest,
        "profile_change_needed": profile_change_needed,
        "current_profile": active_profile,
        "runtime_model_configs": reconciliation.get("runtime_model_configs") or [],
        "reconciliation": reconciliation,
        "denied_actions": [
            "provider_target_profile_file_write",
            "provider_config_edit",
            "setup_state_edit",
            "provider_state_mutation",
            "secret_value_read",
            "external_provider_call",
            "queue_drain_or_retry",
            "gateway_restart",
            "canonical_doc_write",
        ],
        "read_only": True,
        "profile_file_written": False,
        "approval_request_written": False,
        "queue_item_created": False,
        "queue_item_id": None,
        "files_modified": False,
        "provider_state_mutated": False,
        "model_config_mutated": False,
        "setup_state_mutated": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "audit_id": event["event_id"],
    }


def write_provider_target_profile_approval_request(
    vault_root: str | Path,
    *,
    target_model: str | None = None,
    expected_model: str = OPERATOR_REPORTED_EXPECTED_MODEL,
    requested_by: str = "operator",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist a target-profile proposal and queue item without writing the active profile."""
    root = Path(vault_root)
    plan = build_provider_target_profile_plan(
        root,
        target_model=target_model,
        expected_model=expected_model,
        source_command=source_command,
    )
    proposal_id = _new_provider_target_profile_proposal_id()
    path = target_profile_proposals_dir(root) / f"{proposal_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate_digest = str(plan.get("candidate_profile_digest_sha256") or "")
    queue_item = _find_open_provider_target_profile_queue_item(root, candidate_digest)
    queue_item_created = False
    if plan.get("profile_change_needed") and queue_item is None:
        queue_item = create_queue_item(
            root,
            original_request=f"provider_target_profile_change:{candidate_digest} {json.dumps(plan.get('candidate_profile'), sort_keys=True)}",
            task_class="runtime_config_change",
            required_provider_strength="strong",
            primary_provider_id=provider_id_from_model_id(str(plan.get("desired_default_primary_model") or "")) or "primary_provider",
            primary_failure_reason="provider_target_profile_requires_operator_approval",
            fallback_denied_reason="target_profile_change_denied_to_fallback",
            required_context_files=[str(PROVIDER_TARGET_PROFILE_RELATIVE_PATH)],
            related_runtime="cli",
            related_adapter="cli",
            approval_status="needs_operator_approval",
            retry_status="needs_operator_approval",
            safe_next_step="Operator reviews target-profile proposal before any active target-profile file write.",
            operator_note="Generated by RPGL target-profile plan; active provider_target_profile.json was not written.",
            source_command=source_command,
        )
        queue_item_created = True
    record = {
        "record_type": "runtime_provider_target_profile_approval_request",
        "schema_version": SCHEMA_VERSION,
        "proposal_schema_id": PROVIDER_TARGET_PROFILE_PROPOSAL_SCHEMA_ID,
        "proposal_id": proposal_id,
        "status": "pending_operator_review" if plan.get("profile_change_needed") else "no_changes_needed",
        "requested_by": str(requested_by or "operator"),
        "requested_at": _utc_now(),
        "desired_default_primary_model": plan.get("desired_default_primary_model"),
        "target_profile_ref": plan.get("target_profile_ref"),
        "candidate_profile_digest_sha256": candidate_digest,
        "queue_item_id": queue_item.task_id if queue_item else None,
        "queue_item_created": queue_item_created,
        "profile_file_written": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "approval_effect": (
            "Records operator-visible intent for a future active provider target-profile file write. "
            "This artifact does not edit runtime model config, provider setup, provider state, or execute live probes."
        ),
        "plan": plan,
        "source_command": source_command,
    }
    record["request_digest_sha256"] = _approval_digest(record)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_target_profile_approval_request_created",
            runtime="cli",
            provider_id=provider_id_from_model_id(str(plan.get("desired_default_primary_model") or "")) or "primary_provider",
            model=plan.get("desired_default_primary_model"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="provider_target_profile_approval_request_created",
            reason="pending_target_profile_review_written",
            queue_item_id=queue_item.task_id if queue_item else None,
            files_modified=True,
            next_action="operator_review_required_before_target_profile_file_write",
            source_command=source_command,
        ),
    )
    return {
        **plan,
        "read_only": False,
        "approval_request_written": True,
        "approval_request_ref": str(path),
        "proposal_id": proposal_id,
        "queue_item_created": queue_item_created,
        "queue_item_id": queue_item.task_id if queue_item else None,
        "queue_item": queue_item.to_dict() if queue_item else None,
        "profile_file_written": False,
        "files_modified": True,
        "provider_state_mutated": False,
        "model_config_mutated": False,
        "setup_state_mutated": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "audit_id": event["event_id"],
    }


def _fallbacks_match_target(actual: list[str], desired: list[str], enforcement: str) -> bool | None:
    if not desired or enforcement == "observe_only":
        return None
    if enforcement == "exact":
        return actual == desired
    return all(model in actual for model in desired)


def build_provider_config_reconciliation(
    vault_root: str | Path,
    *,
    expected_model: str = OPERATOR_REPORTED_EXPECTED_MODEL,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a read-only report comparing runtime provider config truth.

    This is intentionally diagnostic only. It reads model/config metadata and
    appends an RPGL audit event, but it does not edit provider config, setup
    state, provider state, approval artifacts, queues, or secrets.
    """
    root = Path(vault_root)
    target_profile = build_provider_target_profile(root, expected_model=expected_model, source_command=source_command)
    expected_model = str(target_profile.get("default_primary_model") or expected_model)
    runtime_targets = target_profile.get("runtime_targets") if isinstance(target_profile.get("runtime_targets"), dict) else {}
    runtime_model_configs: list[dict[str, Any]] = []
    runtime_root = root / "runtime"
    if runtime_root.exists():
        for runtime_dir in sorted(item for item in runtime_root.iterdir() if item.is_dir()):
            model_config_path = runtime_dir / "model_config.yaml"
            if not model_config_path.exists():
                continue
            runtime_name = runtime_dir.name
            target = runtime_targets.get(runtime_name) if isinstance(runtime_targets.get(runtime_name), dict) else {}
            target_primary_model = str(target.get("desired_primary_model") or expected_model)
            target_fallback_models = _as_model_list(target.get("desired_fallback_models"))
            fallback_enforcement = str(target.get("fallback_enforcement") or "observe_only")
            try:
                config = load_runtime_model_config(runtime_name, root)
            except ModelConfigError as exc:
                runtime_model_configs.append(
                    {
                        "runtime": runtime_name,
                        "config_path": str(model_config_path),
                        "readable": False,
                        "error": str(exc),
                        "primary_model": None,
                        "fallback_models": [],
                        "target_primary_model": target_primary_model,
                        "target_fallback_models": target_fallback_models,
                        "fallback_target_enforcement": fallback_enforcement,
                        "primary_matches_target": False,
                        "fallbacks_match_target": None,
                        "primary_matches_expected": False,
                        "any_model_matches_expected": False,
                    }
                )
                continue
            fallback_models = [spec.model_id for spec in config.fallbacks]
            all_models = [config.primary.model_id, *fallback_models]
            fallbacks_match_target = _fallbacks_match_target(
                fallback_models,
                target_fallback_models,
                fallback_enforcement,
            )
            runtime_model_configs.append(
                {
                    "runtime": runtime_name,
                    "config_path": str(model_config_path),
                    "readable": True,
                    "primary_model": config.primary.model_id,
                    "fallback_models": fallback_models,
                    "target_primary_model": target_primary_model,
                    "target_fallback_models": target_fallback_models,
                    "fallback_target_enforcement": fallback_enforcement,
                    "all_models": all_models,
                    "primary_provider_id": provider_id_from_model_id(config.primary.model_id) or "unknown",
                    "primary_strength": classify_provider_strength(
                        provider_id_from_model_id(config.primary.model_id),
                        config.primary.model_id,
                    ),
                    "primary_matches_target": config.primary.model_id == target_primary_model,
                    "fallbacks_match_target": fallbacks_match_target,
                    "primary_matches_expected": config.primary.model_id == target_primary_model,
                    "any_model_matches_expected": target_primary_model in all_models,
                }
            )

    setup_path = root / SETUP_STATE_RELATIVE_PATH
    setup_state, setup_error = _read_optional_json(setup_path)
    setup_providers = setup_state.get("providers", {}) if isinstance(setup_state.get("providers", {}), dict) else {}
    provider_setup_summary: dict[str, Any] = {}
    for provider_id, state in sorted(setup_providers.items()):
        if not isinstance(state, dict):
            continue
        provider_setup_summary[str(provider_id)] = {
            "configured": bool(state.get("configured", False)),
            "auth_present": bool(state.get("auth_present", state.get("api_key_present", False))),
            "secret_reference_present": bool(state.get("secret_reference_present", False)),
            "secret_reference_kind": state.get("secret_reference_kind"),
            "secret_reference_target": state.get("secret_reference_target"),
            "default_model": state.get("default_model"),
            "model_selected": bool(state.get("model_selected", bool(state.get("default_model")))),
            "endpoint_present": bool(state.get("endpoint_present", False)),
            "model_target_present": bool(state.get("model_target_present", False)),
            "launcher_mode": state.get("launcher_mode"),
        }

    scans = [_scan_provider_config_file(path, root, expected_model) for path in _known_provider_config_files(root)]
    expected_model_files = sorted(scan["relative_path"] for scan in scans if scan.get("contains_expected_model"))
    gpt_5_4_files = sorted(scan["relative_path"] for scan in scans if scan.get("contains_gpt_5_4"))
    phi4_files = sorted(scan["relative_path"] for scan in scans if scan.get("contains_phi4"))
    ollama_files = sorted(scan["relative_path"] for scan in scans if scan.get("contains_ollama"))
    context_values = [
        {"relative_path": scan["relative_path"], **value}
        for scan in scans
        for value in scan.get("context_values", [])
    ]
    unsafe_context_values = [item for item in context_values if int(item.get("value", 0)) > LOCAL_FALLBACK_SAFE_NUM_CTX]
    safe_context_values = [item for item in context_values if int(item.get("value", 0)) <= LOCAL_FALLBACK_SAFE_NUM_CTX]

    local_setup = provider_setup_summary.get("local_oss", {})
    local_records = [
        record.to_dict()
        for record in load_provider_records(root).values()
        if record.provider_id in {"local_oss", "ollama"} or "phi4" in str(record.model or "").lower()
    ]
    local_fallback = {
        "setup_configured": bool(local_setup.get("configured", False)),
        "setup_model_target_present": bool(local_setup.get("model_target_present", False)),
        "setup_endpoint_present": bool(local_setup.get("endpoint_present", False)),
        "setup_launcher_mode": local_setup.get("launcher_mode"),
        "model_config_records": local_records,
        "phi4_files": phi4_files,
        "ollama_files": ollama_files,
        "safe_num_ctx_default": LOCAL_FALLBACK_SAFE_NUM_CTX,
        "context_values": context_values,
        "safe_context_values": safe_context_values,
        "unsafe_context_values": unsafe_context_values,
        "num_ctx_status": (
            "unsafe_above_16384"
            if unsafe_context_values
            else ("declared_safe" if safe_context_values else "not_declared")
        ),
    }

    mismatches: list[dict[str, Any]] = []
    for item in runtime_model_configs:
        if item.get("readable") and not item.get("primary_matches_target"):
            mismatches.append(
                {
                    "severity": "warning",
                    "type": "runtime_primary_model_mismatch",
                    "runtime": item.get("runtime"),
                    "expected_model": item.get("target_primary_model"),
                    "actual_model": item.get("primary_model"),
                    "path": item.get("config_path"),
                }
            )
        if item.get("fallbacks_match_target") is False:
            mismatches.append(
                {
                    "severity": "warning",
                    "type": "runtime_fallback_model_mismatch",
                    "runtime": item.get("runtime"),
                    "expected_fallback_models": item.get("target_fallback_models"),
                    "actual_fallback_models": item.get("fallback_models"),
                    "fallback_enforcement": item.get("fallback_target_enforcement"),
                    "path": item.get("config_path"),
                }
            )
    setup_targets = target_profile.get("provider_setup_targets") if isinstance(target_profile.get("provider_setup_targets"), dict) else {}
    for provider_id, setup_target in setup_targets.items():
        if not isinstance(setup_target, dict):
            continue
        setup_state = provider_setup_summary.get(str(provider_id), {})
        desired_default_model = setup_target.get("default_model")
        if setup_state and desired_default_model and setup_state.get("default_model") != desired_default_model:
            mismatches.append(
                {
                    "severity": "warning",
                    "type": f"setup_{provider_id}_default_model_mismatch",
                    "provider_id": str(provider_id),
                    "expected_model": desired_default_model,
                    "actual_model": setup_state.get("default_model"),
                    "path": str(setup_path),
                }
            )
    if not local_fallback["setup_configured"] and not local_records:
        mismatches.append(
            {
                "severity": "info",
                "type": "local_fallback_not_configured",
                "reason": "runtime/setup_state.json local_oss is not configured and no local_oss model_config fallback is active",
            }
        )
    if not context_values:
        mismatches.append(
            {
                "severity": "info",
                "type": "local_fallback_context_not_declared",
                "safe_default_num_ctx": LOCAL_FALLBACK_SAFE_NUM_CTX,
                "reason": "no num_ctx/context_length setting found in targeted provider config files",
            }
        )
    for item in unsafe_context_values:
        mismatches.append(
            {
                "severity": "error",
                "type": "unsafe_local_context_length",
                "safe_default_num_ctx": LOCAL_FALLBACK_SAFE_NUM_CTX,
                **item,
            }
        )

    runtime_expected_primary_matches = [
        item for item in runtime_model_configs if item.get("readable") and item.get("primary_matches_target")
    ]
    hard_mismatches = [m for m in mismatches if str(m.get("type", "")).endswith("_mismatch")]
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_reconciliation_requested",
            runtime="cli",
            decision="provider_config_reconciliation_read",
            reason="operator_requested_provider_config_reconciliation",
            files_modified=False,
            next_action="review_mismatches_before_provider_config_mutation",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "active_target_primary_model": expected_model,
        "expected_primary_model": expected_model,
        "expected_primary_model_compatibility_field": True,
        "target_profile": target_profile,
        "target_profile_source": target_profile.get("profile_source"),
        "target_profile_exists": target_profile.get("profile_exists"),
        "safe_local_num_ctx_default": LOCAL_FALLBACK_SAFE_NUM_CTX,
        "status": "matches_target_profile" if runtime_expected_primary_matches and not mismatches else "mismatch_or_unconfigured",
        "operator_truth_matches_repo": bool(runtime_expected_primary_matches and not hard_mismatches),
        "runtime_model_configs": runtime_model_configs,
        "provider_setup_state": {
            "path": str(setup_path),
            "exists": setup_path.exists(),
            "error": setup_error,
            "providers": provider_setup_summary,
        },
        "local_fallback": local_fallback,
        "config_file_scan": {
            "files_scanned": [scan["relative_path"] for scan in scans],
            "expected_model_files": expected_model_files,
            "gpt_5_4_files": gpt_5_4_files,
            "phi4_files": phi4_files,
            "ollama_files": ollama_files,
            "context_values": context_values,
        },
        "mismatches": mismatches,
        "read_only": True,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "setup_state_mutated": False,
        "model_config_mutated": False,
        "approval_request_written": False,
        "files_modified": False,
        "audit_id": event["event_id"],
    }


def _relative_config_path(path: str | Path | None, vault_root: str | Path) -> str | None:
    if not path:
        return None
    root = Path(vault_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        return candidate.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _provider_config_change_paths(plan: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for change in plan.get("proposed_changes") or []:
        path = change.get("path")
        if path and path not in paths:
            paths.append(str(path))
    return paths


def _find_open_provider_config_queue_item(vault_root: str | Path, expected_model: str) -> ProviderQueueItem | None:
    marker = f"provider_config_change:{expected_model}"
    for item in load_queue_items(vault_root):
        if (
            item.task_class == "runtime_config_change"
            and marker in item.original_request
            and item.retry_status in {"queued", "waiting_for_primary", "ready_for_retry", "needs_operator_approval"}
        ):
            return item
    return None


def build_provider_config_change_plan(
    vault_root: str | Path,
    *,
    expected_model: str = OPERATOR_REPORTED_EXPECTED_MODEL,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a non-mutating provider config change plan from reconciliation truth."""
    root = Path(vault_root)
    reconciliation = build_provider_config_reconciliation(
        root,
        expected_model=expected_model,
        source_command=source_command,
    )
    expected_model = str(
        reconciliation.get("active_target_primary_model")
        or reconciliation.get("expected_primary_model")
        or expected_model
    )
    proposed_changes: list[dict[str, Any]] = []
    for item in reconciliation.get("runtime_model_configs") or []:
        target_primary_model = str(item.get("target_primary_model") or expected_model)
        if item.get("readable") and not item.get("primary_matches_target"):
            proposed_changes.append(
                {
                    "change_id": f"{item.get('runtime')}-primary-model",
                    "change_type": "runtime_primary_model_update",
                    "task_classes": ["runtime_config_change", "provider_routing_change"],
                    "requires_operator_approval": True,
                    "path": _relative_config_path(item.get("config_path"), root),
                    "runtime": item.get("runtime"),
                    "field": "primary.model_id",
                    "current_value": item.get("primary_model"),
                    "proposed_value": target_primary_model,
                    "mutation_status": "not_applied",
                    "reason": "runtime_primary_model_does_not_match_target_profile",
                }
            )

    setup = reconciliation.get("provider_setup_state") or {}
    target_profile = reconciliation.get("target_profile") if isinstance(reconciliation.get("target_profile"), dict) else {}
    setup_targets = target_profile.get("provider_setup_targets") if isinstance(target_profile.get("provider_setup_targets"), dict) else {}
    for provider_id, target in setup_targets.items():
        if not isinstance(target, dict):
            continue
        setup_state = (setup.get("providers") or {}).get(str(provider_id)) or {}
        desired_default_model = target.get("default_model")
        if setup_state and desired_default_model and setup_state.get("default_model") != desired_default_model:
            proposed_changes.append(
                {
                    "change_id": f"setup-{provider_id}-default-model",
                    "change_type": f"setup_{provider_id}_default_model_update",
                    "task_classes": ["runtime_config_change"],
                    "requires_operator_approval": True,
                    "path": _relative_config_path(setup.get("path"), root),
                    "provider_id": str(provider_id),
                    "field": f"providers.{provider_id}.default_model",
                    "current_value": setup_state.get("default_model"),
                    "proposed_value": desired_default_model,
                    "mutation_status": "not_applied",
                    "reason": "setup_state_default_model_does_not_match_target_profile",
                }
            )

    local = reconciliation.get("local_fallback") or {}
    if local.get("num_ctx_status") == "not_declared":
        proposed_changes.append(
            {
                "change_id": "local-fallback-context-policy",
                "change_type": "local_fallback_context_policy_decision",
                "task_classes": ["runtime_config_change", "provider_routing_change"],
                "requires_operator_approval": True,
                "path": "runtime/policy/adapters/local_oss.yaml",
                "provider_id": "local_oss",
                "field": "num_ctx",
                "current_value": "not_declared",
                "proposed_value": LOCAL_FALLBACK_SAFE_NUM_CTX,
                "mutation_status": "not_applied",
                "reason": "safe_local_num_ctx_default_recorded_but_local_oss_is_not_active_config",
                "note": "Do not activate or expand local fallback implicitly; apply only if a future governed local_oss config target exists.",
            }
        )

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_change_plan_requested",
            runtime="cli",
            provider_id="openai",
            model=expected_model,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="config_change_plan_built",
            reason="operator_requested_provider_config_change_plan",
            files_modified=False,
            next_action="write_operator_approval_request_or_apply_in_separate_governed_pass",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "proposal_schema_id": PROVIDER_CONFIG_CHANGE_PROPOSAL_SCHEMA_ID,
        "generated_at": _utc_now(),
        "active_target_primary_model": expected_model,
        "expected_primary_model": expected_model,
        "expected_primary_model_compatibility_field": True,
        "status": "changes_proposed" if proposed_changes else "no_changes_needed",
        "requires_operator_approval": bool(proposed_changes),
        "proposed_changes": proposed_changes,
        "change_count": len(proposed_changes),
        "reconciliation": reconciliation,
        "denied_actions": [
            "provider_config_edit",
            "setup_state_edit",
            "provider_state_mutation",
            "secret_value_read",
            "external_provider_call",
            "queue_drain_or_retry",
            "gateway_restart",
            "canonical_doc_write",
        ],
        "read_only": True,
        "approval_request_written": False,
        "queue_item_created": False,
        "queue_item_id": None,
        "files_modified": False,
        "provider_state_mutated": False,
        "model_config_mutated": False,
        "setup_state_mutated": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "audit_id": event["event_id"],
    }


def write_provider_config_change_approval_request(
    vault_root: str | Path,
    *,
    expected_model: str = OPERATOR_REPORTED_EXPECTED_MODEL,
    requested_by: str = "operator",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist a provider-config proposal and queue item without editing config."""
    root = Path(vault_root)
    plan = build_provider_config_change_plan(
        root,
        expected_model=expected_model,
        source_command=source_command,
    )
    proposal_id = _new_provider_config_proposal_id()
    path = config_proposals_dir(root) / f"{proposal_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    queue_item = _find_open_provider_config_queue_item(root, expected_model)
    queue_item_created = False
    if plan.get("proposed_changes") and queue_item is None:
        queue_item = create_queue_item(
            root,
            original_request=f"provider_config_change:{expected_model} {json.dumps(plan.get('proposed_changes'), sort_keys=True)}",
            task_class="runtime_config_change",
            required_provider_strength="strong",
            primary_provider_id="openai",
            primary_failure_reason="provider_config_mismatch",
            fallback_denied_reason="provider_config_change_requires_operator_approval",
            required_context_files=_provider_config_change_paths(plan),
            related_runtime="cli",
            related_adapter="cli",
            approval_status="needs_operator_approval",
            retry_status="needs_operator_approval",
            safe_next_step="Operator reviews provider config proposal before any config mutation pass.",
            operator_note="Generated by RPGL provider config plan; files_modified=false.",
            source_command=source_command,
        )
        queue_item_created = True
    record = {
        "record_type": "runtime_provider_config_change_approval_request",
        "schema_version": SCHEMA_VERSION,
        "proposal_schema_id": PROVIDER_CONFIG_CHANGE_PROPOSAL_SCHEMA_ID,
        "proposal_id": proposal_id,
        "status": "pending_operator_review" if plan.get("proposed_changes") else "no_changes_needed",
        "requested_by": str(requested_by or "operator"),
        "requested_at": _utc_now(),
        "expected_primary_model": expected_model,
        "queue_item_id": queue_item.task_id if queue_item else None,
        "queue_item_created": queue_item_created,
        "files_modified": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "approval_effect": (
            "Records operator-visible intent for a future provider config mutation pass. "
            "This artifact does not edit provider config or authorize live provider calls."
        ),
        "plan": plan,
        "source_command": source_command,
    }
    record["request_digest_sha256"] = _approval_digest(record)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_change_approval_request_created",
            runtime="cli",
            provider_id="openai",
            model=expected_model,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="provider_config_change_approval_request_created",
            reason="pending_provider_config_change_review_written",
            queue_item_id=queue_item.task_id if queue_item else None,
            files_modified=True,
            next_action="operator_review_required_before_provider_config_mutation",
            source_command=source_command,
        ),
    )
    return {
        **plan,
        "read_only": False,
        "approval_request_written": True,
        "approval_request_ref": str(path),
        "proposal_id": proposal_id,
        "queue_item_created": queue_item_created,
        "queue_item_id": queue_item.task_id if queue_item else None,
        "queue_item": queue_item.to_dict() if queue_item else None,
        "files_modified": True,
        "provider_state_mutated": False,
        "model_config_mutated": False,
        "setup_state_mutated": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "audit_id": event["event_id"],
    }


def load_provider_config_change_proposal(vault_root: str | Path, proposal_ref: str) -> dict[str, Any]:
    path = _provider_config_proposal_path(vault_root, proposal_ref)
    if not path.exists():
        raise RuntimeProviderGovernanceError(f"RPGL provider config proposal not found: {proposal_ref}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeProviderGovernanceError(f"Invalid RPGL provider config proposal JSON at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeProviderGovernanceError(f"RPGL provider config proposal JSON at {path} must be an object")
    data["proposal_ref"] = str(path)
    return data


def _current_value_for_provider_config_change(
    vault_root: str | Path,
    change: dict[str, Any],
    reconciliation: dict[str, Any],
) -> Any:
    change_type = change.get("change_type")
    if change_type == "runtime_primary_model_update":
        runtime = str(change.get("runtime") or "")
        try:
            config = load_runtime_model_config(runtime, vault_root)
        except ModelConfigError:
            return None
        return config.primary.model_id
    if change_type == "setup_openai_default_model_update":
        setup_state, _error = _read_optional_json(Path(vault_root) / SETUP_STATE_RELATIVE_PATH)
        providers = setup_state.get("providers", {}) if isinstance(setup_state.get("providers", {}), dict) else {}
        openai = providers.get("openai", {}) if isinstance(providers.get("openai", {}), dict) else {}
        return openai.get("default_model")
    if change_type == "local_fallback_context_policy_decision":
        local = reconciliation.get("local_fallback") or {}
        return local.get("num_ctx_status")
    return None


def build_provider_config_apply_preflight(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Validate a provider-config proposal before any future apply command.

    This function is intentionally no-apply: it reads the proposal artifact,
    queue item, and current config values, then reports whether a separate
    operator-approved mutation pass could proceed.
    """
    root = Path(vault_root)
    record = load_provider_config_change_proposal(root, proposal_ref)
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    if record.get("record_type") != "runtime_provider_config_change_approval_request":
        errors.append("record_type must be runtime_provider_config_change_approval_request")
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if record.get("proposal_schema_id") != PROVIDER_CONFIG_CHANGE_PROPOSAL_SCHEMA_ID:
        errors.append(f"proposal_schema_id must be {PROVIDER_CONFIG_CHANGE_PROPOSAL_SCHEMA_ID}")
    expected_digest = record.get("request_digest_sha256")
    actual_digest = _approval_digest(record)
    if expected_digest != actual_digest:
        errors.append("request_digest_sha256 mismatch")

    for flag_name in [
        "provider_config_mutated",
        "setup_state_mutated",
        "provider_state_mutated",
        "secret_value_read",
        "live_network_call_attempted",
    ]:
        if record.get(flag_name) is not False:
            errors.append(f"{flag_name} must be false")

    plan = record.get("plan") if isinstance(record.get("plan"), dict) else {}
    proposed_changes = list(plan.get("proposed_changes") or [])
    if not proposed_changes:
        warnings.append("proposal has no proposed_changes")

    queue_item_id = record.get("queue_item_id")
    queue_item = get_queue_item(root, str(queue_item_id)) if queue_item_id else None
    if queue_item_id and queue_item is None:
        errors.append(f"queue item not found: {queue_item_id}")
    elif queue_item is not None:
        if queue_item.task_class != "runtime_config_change":
            errors.append("queue item task_class must be runtime_config_change")
        if queue_item.approval_status != "needs_operator_approval":
            errors.append("queue item approval_status must be needs_operator_approval")
        if queue_item.retry_status != "needs_operator_approval":
            errors.append("queue item retry_status must be needs_operator_approval")
        if queue_item.files_modified is not False:
            errors.append("queue item files_modified must be false")

    expected_model = str(record.get("expected_primary_model") or OPERATOR_REPORTED_EXPECTED_MODEL)
    reconciliation = build_provider_config_reconciliation(
        root,
        expected_model=expected_model,
        source_command=source_command,
    )
    drift_detected = False
    for change in proposed_changes:
        current_value = _current_value_for_provider_config_change(root, change, reconciliation)
        expected_current = change.get("current_value")
        check_status = "ok"
        reason = "current_value_matches_proposal"
        if change.get("change_type") == "local_fallback_context_policy_decision":
            expected_current = "not_declared"
        if current_value != expected_current:
            drift_detected = True
            check_status = "drift_detected"
            reason = "current_value_changed_since_proposal"
        checks.append(
            {
                "change_id": change.get("change_id"),
                "change_type": change.get("change_type"),
                "path": change.get("path"),
                "field": change.get("field"),
                "expected_current_value": expected_current,
                "actual_current_value": current_value,
                "proposed_value": change.get("proposed_value"),
                "status": check_status,
                "reason": reason,
            }
        )

    if drift_detected:
        errors.append("current config drift detected")

    structurally_valid = not errors
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_preflight_requested",
            runtime="cli",
            provider_id="openai",
            model=expected_model,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="apply_preflight_ready" if structurally_valid else "apply_preflight_blocked",
            reason="provider_config_proposal_validated_without_apply" if structurally_valid else "provider_config_proposal_validation_failed",
            queue_item_id=str(queue_item_id) if queue_item_id else None,
            files_modified=False,
            next_action="request_explicit_operator_approval_for_config_mutation" if structurally_valid else "repair_or_regenerate_provider_config_proposal",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "proposal_schema_id": PROVIDER_CONFIG_CHANGE_PROPOSAL_SCHEMA_ID,
        "generated_at": _utc_now(),
        "proposal_id": record.get("proposal_id"),
        "proposal_ref": record.get("proposal_ref"),
        "queue_item_id": queue_item_id,
        "queue_item": queue_item.to_dict() if queue_item else None,
        "preflight_status": "ready_for_operator_approval" if structurally_valid else "blocked",
        "structurally_valid": structurally_valid,
        "drift_detected": drift_detected,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "proposed_changes": proposed_changes,
        "apply_enabled": False,
        "approval_consumed": False,
        "files_modified": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "denied_actions": [
            "provider_config_edit",
            "setup_state_edit",
            "provider_state_mutation",
            "secret_value_read",
            "external_provider_call",
            "queue_drain_or_retry",
            "gateway_restart",
            "canonical_doc_write",
        ],
        "audit_id": event["event_id"],
    }


def _provider_config_changes_digest(proposed_changes: list[dict[str, Any]]) -> str:
    canonical = json.dumps(proposed_changes, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _provider_config_apply_target_writes(proposed_changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for change in proposed_changes:
        change_type = str(change.get("change_type") or "")
        write_enabled = change_type in {"runtime_primary_model_update", "setup_openai_default_model_update"}
        apply_status = "planned_after_approval" if write_enabled else "review_only_no_active_apply_target"
        if change_type == "local_fallback_context_policy_decision":
            apply_status = "blocked_until_active_local_oss_config_target_exists"
        targets.append(
            {
                "change_id": change.get("change_id"),
                "change_type": change_type,
                "path": change.get("path"),
                "runtime": change.get("runtime"),
                "provider_id": change.get("provider_id"),
                "field": change.get("field"),
                "current_value": change.get("current_value"),
                "proposed_value": change.get("proposed_value"),
                "write_enabled_after_approval": write_enabled,
                "apply_status": apply_status,
                "rollback_source": "current_value",
            }
        )
    return targets


def build_provider_config_apply_design(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a non-executing executor design for future provider config apply.

    This deliberately does not consume approval or mutate provider config. It
    composes the existing apply preflight and Gate approval schema into the
    exact preconditions a future executor must satisfy.
    """
    root = Path(vault_root)
    preflight = build_provider_config_apply_preflight(
        root,
        proposal_ref,
        source_command=source_command,
    )
    proposed_changes = list(preflight.get("proposed_changes") or [])
    target_writes = _provider_config_apply_target_writes(proposed_changes)
    enabled_target_paths = sorted(
        {
            str(item.get("path"))
            for item in target_writes
            if item.get("write_enabled_after_approval") and item.get("path")
        }
    )
    proposed_changes_digest = _provider_config_changes_digest(proposed_changes)
    expected_model = str(
        (proposed_changes[0].get("proposed_value") if proposed_changes else None)
        or OPERATOR_REPORTED_EXPECTED_MODEL
    )
    approval_schema = get_runtime_operation_approval_schema(
        RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        provider_id="openai",
        model=expected_model,
        runtime="cli",
        source_command=source_command,
    ) or {}
    approval_template = dict(approval_schema.get("approval_request_template") or {})
    if approval_template:
        approval_template.update(
            {
                "proposal_id": preflight.get("proposal_id"),
                "queue_item_id": preflight.get("queue_item_id"),
                "expected_primary_model": expected_model,
                "proposed_changes_digest_sha256": proposed_changes_digest,
                "target_paths": enabled_target_paths,
            }
        )
    allowed, gate_reason = check_runtime_operation(
        RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        write_targets=enabled_target_paths,
    )
    preflight_valid = bool(preflight.get("structurally_valid"))
    preconditions = [
        {
            "id": "apply_preflight_structurally_valid",
            "passed": preflight_valid,
            "status": "passed" if preflight_valid else "blocked",
            "critical": True,
        },
        {
            "id": "gate_operation_declared",
            "passed": bool(approval_schema),
            "status": "declared" if approval_schema else "missing",
            "critical": True,
        },
        {
            "id": "gate_operation_allows_execution",
            "passed": bool(allowed),
            "status": "blocked_requires_approval" if not allowed else "allowed",
            "reason": gate_reason,
            "critical": True,
        },
        {
            "id": "approval_decision_consumption_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "apply_executor_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "target_paths_limited",
            "passed": all(
                str(path).startswith("runtime/")
                and str(path)
                in {
                    "runtime/hermes/model_config.yaml",
                    "runtime/openclaw/model_config.yaml",
                    "runtime/setup_state.json",
                }
                for path in enabled_target_paths
            ),
            "status": "passed",
            "critical": True,
        },
        {
            "id": "rollback_plan_present",
            "passed": True,
            "status": "planned",
            "critical": True,
        },
        {
            "id": "post_apply_verification_present",
            "passed": True,
            "status": "planned",
            "critical": True,
        },
        {
            "id": "weak_fallback_not_involved",
            "passed": True,
            "status": "passed",
            "critical": True,
        },
    ]
    blocked_reasons = [
        "provider_config_apply_executor_not_implemented",
        "approval_decision_consumption_not_implemented",
    ]
    if not preflight_valid:
        blocked_reasons.append("provider_config_apply_preflight_blocked")
    if not allowed:
        blocked_reasons.append("explicit_gate_approval_required")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_design_requested",
            runtime="cli",
            provider_id="openai",
            model=expected_model,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="apply_design_not_built",
            reason="provider_config_apply_design_is_non_executing",
            queue_item_id=str(preflight.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action="review_apply_executor_design_before_any_config_mutation",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "proposal_id": preflight.get("proposal_id"),
        "proposal_ref": preflight.get("proposal_ref"),
        "queue_item_id": preflight.get("queue_item_id"),
        "design_status": "ready_for_executor_implementation_review" if preflight_valid else "blocked",
        "executor_status": "not_built",
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "preflight": preflight,
        "preflight_status": preflight.get("preflight_status"),
        "preflight_structurally_valid": preflight_valid,
        "drift_detected": bool(preflight.get("drift_detected")),
        "gate_policy_allowed": bool(allowed),
        "gate_policy_reason": gate_reason,
        "approval_required": True,
        "approval_status": "missing",
        "approval_request_written": False,
        "approval_consumed": False,
        "approval_schema": approval_schema,
        "approval_request_template": approval_template,
        "proposed_changes_digest_sha256": proposed_changes_digest,
        "target_writes": target_writes,
        "rollback_plan": {
            "required": True,
            "method": "capture_current_values_before_write_and_restore_on_failed_verification",
            "source_fields": ["path", "field", "current_value"],
        },
        "post_apply_verification": [
            "run chaseos runtime provider config-report --json",
            "run chaseos runtime provider config-apply-preflight <proposal_id> --json",
            "verify runtime/providers/state/provider_state.json was not created or mutated by config apply",
            "verify all enabled target writes match proposed values",
        ],
        "preconditions": preconditions,
        "blocked_reasons": blocked_reasons,
        "files_modified": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "denied_actions": [
            "provider_config_edit",
            "setup_state_edit",
            "provider_state_mutation",
            "secret_value_read",
            "external_provider_call",
            "queue_drain_or_retry",
            "gateway_restart",
            "canonical_doc_write",
        ],
        "audit_id": event["event_id"],
    }


def build_provider_config_apply_approval_request_record(
    design: dict[str, Any],
    *,
    requested_by: str,
    operator_request_id: str | None = None,
    gate_approval_id: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a pending provider-config apply approval artifact without applying it."""
    if not design.get("preflight_structurally_valid"):
        raise RuntimeProviderGovernanceError("provider config apply approval request requires a valid apply preflight")
    gate_approval_id = gate_approval_id or _new_provider_config_apply_gate_approval_id()
    _validate_gate_approval_id(gate_approval_id)
    operator_request_id = operator_request_id or _new_provider_config_apply_operator_request_id()
    approval_template = dict(design.get("approval_request_template") or {})
    target_paths = list(approval_template.get("target_paths") or [])
    record = {
        "record_type": "runtime_provider_config_apply_approval_request",
        "schema_version": SCHEMA_VERSION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "operator_request_id": str(operator_request_id),
        "gate_approval_id": gate_approval_id,
        "proposal_id": str(design.get("proposal_id") or ""),
        "queue_item_id": str(design.get("queue_item_id") or ""),
        "expected_primary_model": str(
            approval_template.get("expected_primary_model")
            or OPERATOR_REPORTED_EXPECTED_MODEL
        ),
        "proposed_changes_digest_sha256": str(design.get("proposed_changes_digest_sha256") or ""),
        "target_paths": target_paths,
        "target_writes": list(design.get("target_writes") or []),
        "rollback_plan": dict(design.get("rollback_plan") or {}),
        "post_apply_verification": list(design.get("post_apply_verification") or []),
        "files_modified_expected": True,
        "status": "pending",
        "requested_by": str(requested_by or "operator"),
        "requested_at": _utc_now(),
        "approved_by": None,
        "approved_at": None,
        "approval_effect": (
            "Records operator intent for one future provider config apply attempt. "
            "This artifact does not apply provider config, consume approval, call providers, "
            "drain queues, restart gateways, or mutate provider state."
        ),
        "preflight_status": design.get("preflight_status"),
        "design_status": design.get("design_status"),
        "executor_status": design.get("executor_status"),
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "approval_consumed": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "denied_actions": list(design.get("denied_actions") or []),
        "source_command": source_command,
    }
    record["request_digest_sha256"] = _approval_digest(record)
    return record


def build_provider_config_apply_approval_request_preview(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    requested_by: str = "operator",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Preview a provider config apply approval request without writing it."""
    design = build_provider_config_apply_design(
        vault_root,
        proposal_ref,
        source_command=source_command,
    )
    record = build_provider_config_apply_approval_request_record(
        design,
        requested_by=requested_by,
        source_command=source_command,
    )
    return {
        **record,
        "approval_ref": None,
        "approval_request_written": False,
        "files_modified": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "approval_design": design,
    }


def write_provider_config_apply_approval_request(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    requested_by: str = "operator",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist a pending provider-config apply approval request without applying it."""
    design = build_provider_config_apply_design(
        vault_root,
        proposal_ref,
        source_command=source_command,
    )
    record = build_provider_config_apply_approval_request_record(
        design,
        requested_by=requested_by,
        source_command=source_command,
    )
    path = _config_apply_approval_artifact_path(vault_root, str(record["gate_approval_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply approval request already exists: {record['gate_approval_id']}")
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_config_apply_approval_request_created",
            runtime="cli",
            provider_id="openai",
            model=record.get("expected_primary_model"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="provider_config_apply_approval_request_created",
            reason="pending_provider_config_apply_approval_request_written",
            queue_item_id=str(record.get("queue_item_id") or "") or None,
            files_modified=True,
            next_action="operator_review_required_before_provider_config_apply_executor",
            source_command=source_command,
        ),
    )
    return {
        **record,
        "approval_ref": str(path),
        "approval_request_written": True,
        "files_modified": True,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "approval_design": design,
        "audit_id": event["event_id"],
    }


def load_provider_config_apply_approval_request(vault_root: str | Path, gate_approval_id: str) -> dict[str, Any]:
    path = _config_apply_approval_artifact_path(vault_root, gate_approval_id)
    if not path.exists():
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply approval request not found: {gate_approval_id}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeProviderGovernanceError(f"Invalid RPGL provider config apply approval JSON at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply approval JSON at {path} must be an object")
    data["approval_ref"] = str(path)
    return data


def validate_provider_config_apply_approval_request(
    vault_root: str | Path,
    gate_approval_id: str,
    *,
    expected_design: dict[str, Any] | None = None,
    source_command: str | None = None,
    write_audit: bool = True,
) -> dict[str, Any]:
    """Validate a provider-config apply approval artifact without authorizing execution."""
    record = load_provider_config_apply_approval_request(vault_root, gate_approval_id)
    errors: list[str] = []
    warnings: list[str] = []

    if record.get("record_type") != "runtime_provider_config_apply_approval_request":
        errors.append("record_type must be runtime_provider_config_apply_approval_request")
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if record.get("approval_schema_id") != RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID:
        errors.append(f"approval_schema_id must be {RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID}")
    if record.get("operation") != RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION:
        errors.append(f"operation must be {RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION}")
    if record.get("gate_approval_id") != gate_approval_id:
        errors.append("gate_approval_id does not match requested artifact id")

    for field_name in RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_REQUIRED_FIELDS:
        value = record.get(field_name)
        if value is None or value == "":
            errors.append(f"required field missing: {field_name}")

    status = str(record.get("status") or "missing")
    if status not in CONFIG_APPLY_APPROVAL_STATUSES:
        errors.append(f"unsupported approval status: {status}")

    for flag_name in [
        "execution_enabled",
        "apply_execution_allowed",
        "approval_consumed",
        "provider_config_mutated",
        "setup_state_mutated",
        "provider_state_mutated",
        "secret_value_read",
        "live_network_call_attempted",
        "queue_drained",
        "gateway_mutated",
        "canonical_files_mutated",
    ]:
        if record.get(flag_name) is not False:
            errors.append(f"{flag_name} must be false")

    if record.get("files_modified_expected") is not True:
        errors.append("files_modified_expected must be true")

    target_paths = record.get("target_paths")
    if not isinstance(target_paths, list) or not target_paths:
        errors.append("target_paths must be a non-empty list")
    else:
        allowed_paths = {
            "runtime/hermes/model_config.yaml",
            "runtime/openclaw/model_config.yaml",
            "runtime/setup_state.json",
        }
        for path in target_paths:
            if path not in allowed_paths:
                errors.append(f"unsupported target path: {path}")

    if not isinstance(record.get("rollback_plan"), dict) or not record.get("rollback_plan", {}).get("required"):
        errors.append("rollback_plan.required must be true")
    if not isinstance(record.get("post_apply_verification"), list) or not record.get("post_apply_verification"):
        errors.append("post_apply_verification must be a non-empty list")

    if "request_digest_sha256" in record:
        expected_digest = _approval_digest(record)
        if record.get("request_digest_sha256") != expected_digest:
            warnings.append("request_digest_sha256 does not match current artifact content")

    mismatches: list[str] = []
    if expected_design:
        comparisons = {
            "proposal_id": expected_design.get("proposal_id"),
            "queue_item_id": expected_design.get("queue_item_id"),
            "proposed_changes_digest_sha256": expected_design.get("proposed_changes_digest_sha256"),
        }
        for field_name, expected_value in comparisons.items():
            if expected_value is not None and record.get(field_name) != expected_value:
                mismatches.append(field_name)
        expected_template = expected_design.get("approval_request_template") or {}
        expected_model = expected_template.get("expected_primary_model")
        if expected_model and record.get("expected_primary_model") != expected_model:
            mismatches.append("expected_primary_model")
        expected_paths = list(expected_template.get("target_paths") or [])
        if expected_paths and record.get("target_paths") != expected_paths:
            mismatches.append("target_paths")
    if mismatches:
        errors.append("approval artifact does not match apply design fields: " + ", ".join(sorted(mismatches)))

    structurally_valid = not errors
    validation = {
        "gate_approval_id": gate_approval_id,
        "approval_ref": record.get("approval_ref"),
        "approval_schema_id": record.get("approval_schema_id"),
        "operation": record.get("operation"),
        "approval_status": status,
        "structurally_valid": structurally_valid,
        "matches_design": not mismatches,
        "approval_decision_accepted": structurally_valid and status == "approved",
        "apply_execution_allowed": False,
        "approval_consumed": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "errors": errors,
        "warnings": warnings,
        "reason": (
            "provider_config_apply_approval_artifact_validation_only_executor_not_built"
            if structurally_valid
            else "provider_config_apply_approval_artifact_invalid"
        ),
    }
    if write_audit:
        event_type = (
            "provider_config_apply_approval_request_validated"
            if structurally_valid
            else "provider_config_apply_approval_request_invalid"
        )
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type=event_type,
                runtime="cli",
                provider_id="openai",
                model=record.get("expected_primary_model"),
                provider_strength="strong",
                task_class="runtime_config_change",
                decision="approval_artifact_validated" if structurally_valid else "approval_artifact_invalid",
                reason=validation["reason"],
                queue_item_id=str(record.get("queue_item_id") or "") or None,
                files_modified=False,
                next_action=(
                    "provider_config_apply_executor_still_not_built"
                    if structurally_valid
                    else "operator_must_recreate_or_fix_provider_config_apply_approval_artifact"
                ),
                source_command=source_command,
            ),
        )
        validation["audit_id"] = event["event_id"]
    return validation


def build_provider_config_apply_decision_preflight(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Inspect approval-decision consumption prerequisites without consuming approval."""
    root = Path(vault_root)
    design = build_provider_config_apply_design(
        root,
        proposal_ref,
        source_command=source_command,
    )
    validation = validate_provider_config_apply_approval_request(
        root,
        gate_approval_id,
        expected_design=design,
        source_command=source_command,
        write_audit=False,
    )
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_exists = marker_path.exists()
    approval_status = str(validation.get("approval_status") or "missing")
    structurally_valid = bool(validation.get("structurally_valid"))
    approval_accepted = bool(validation.get("approval_decision_accepted"))
    decision_record_validation = validate_provider_config_apply_decision_records(
        root,
        gate_approval_id=gate_approval_id,
        expected_design=design,
    )
    immutable_decision_status = str(decision_record_validation.get("status") or "missing")
    immutable_decision = str(decision_record_validation.get("decision") or "")
    immutable_decision_accepted = immutable_decision_status == "approved_decision_record_valid"

    if not structurally_valid:
        decision_status = "blocked_approval_artifact_invalid"
        next_action = "operator_must_recreate_or_fix_provider_config_apply_approval_artifact"
    elif marker_exists:
        decision_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_any_retry"
    elif immutable_decision_status == "missing":
        decision_status = "blocked_missing_immutable_decision_record"
        next_action = "operator_must_record_immutable_approval_decision_before_future_executor"
    elif immutable_decision_status == "multiple":
        decision_status = "blocked_multiple_immutable_decision_records"
        next_action = "operator_must_resolve_duplicate_decision_records_before_future_executor"
    elif immutable_decision_status == "invalid":
        decision_status = "blocked_immutable_decision_record_invalid"
        next_action = "operator_must_recreate_or_review_invalid_decision_record_before_future_executor"
    elif immutable_decision_status == "denied_decision_record_valid":
        decision_status = "blocked_approval_decision_denied"
        next_action = "operator_denied_apply_or_must_create_new_approval_request"
    else:
        decision_status = "approved_decision_record_valid_but_executor_not_built"
        next_action = "implement_operator_approved_apply_executor_before_consumption"

    preconditions = [
        {
            "id": "apply_preflight_structurally_valid",
            "passed": bool(design.get("preflight_structurally_valid")),
            "status": "passed" if design.get("preflight_structurally_valid") else "blocked",
            "critical": True,
        },
        {
            "id": "approval_artifact_structurally_valid",
            "passed": structurally_valid,
            "status": "passed" if structurally_valid else "blocked",
            "critical": True,
        },
        {
            "id": "approval_artifact_status_observed",
            "passed": approval_status in CONFIG_APPLY_APPROVAL_STATUSES,
            "status": approval_status,
            "critical": False,
        },
        {
            "id": "approval_artifact_matches_design",
            "passed": bool(validation.get("matches_design")),
            "status": "passed" if validation.get("matches_design") else "blocked",
            "critical": True,
        },
        {
            "id": "immutable_decision_record_present",
            "passed": int(decision_record_validation.get("records_found") or 0) == 1,
            "status": immutable_decision_status,
            "critical": True,
        },
        {
            "id": "immutable_decision_record_valid",
            "passed": immutable_decision_status in {"approved_decision_record_valid", "denied_decision_record_valid"},
            "status": immutable_decision_status,
            "critical": True,
        },
        {
            "id": "immutable_decision_record_approved",
            "passed": immutable_decision_accepted,
            "status": immutable_decision or immutable_decision_status,
            "critical": True,
        },
        {
            "id": "idempotency_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "marker_path": str(marker_path),
            "critical": True,
        },
        {
            "id": "approval_decision_record_validation_implemented",
            "passed": True,
            "status": "implemented_no_mutation",
            "critical": True,
        },
        {
            "id": "approval_decision_consumption_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "apply_executor_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
    ]
    blocked_reasons = ["approval_decision_consumption_not_implemented", "provider_config_apply_executor_not_implemented"]
    if not structurally_valid:
        blocked_reasons.append("provider_config_apply_approval_artifact_invalid")
    if immutable_decision_status == "missing":
        blocked_reasons.append("provider_config_apply_immutable_decision_missing")
    if immutable_decision_status == "multiple":
        blocked_reasons.append("provider_config_apply_multiple_immutable_decisions")
    if immutable_decision_status == "invalid":
        blocked_reasons.append("provider_config_apply_immutable_decision_invalid")
    if immutable_decision_status == "denied_decision_record_valid":
        blocked_reasons.append("provider_config_apply_approval_decision_denied")
    if marker_exists:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")
    if not design.get("preflight_structurally_valid"):
        blocked_reasons.append("provider_config_apply_preflight_blocked")

    append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type=(
                "provider_config_apply_decision_record_validated"
                if immutable_decision_status in {"approved_decision_record_valid", "denied_decision_record_valid"}
                else "provider_config_apply_decision_record_invalid"
            ),
            runtime="cli",
            provider_id="openai",
            model=design.get("approval_request_template", {}).get("expected_primary_model"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=immutable_decision_status,
            reason="immutable_provider_config_apply_decision_record_validation_only",
            queue_item_id=str(design.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_preflight_requested",
            runtime="cli",
            provider_id="openai",
            model=design.get("approval_request_template", {}).get("expected_primary_model"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=decision_status,
            reason="provider_config_apply_decision_consumption_preflight_is_non_mutating",
            queue_item_id=str(design.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "proposal_id": design.get("proposal_id"),
        "proposal_ref": design.get("proposal_ref"),
        "queue_item_id": design.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "decision_consumption_status": decision_status,
        "executor_status": "not_built",
        "approval_status": approval_status,
        "approval_decision_accepted": approval_accepted,
        "immutable_decision_status": immutable_decision_status,
        "immutable_decision_accepted": immutable_decision_accepted,
        "decision_record_validation": decision_record_validation,
        "approval_validation": validation,
        "apply_design": design,
        "idempotency": {
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "status": "prior_apply_marker_exists_blocked" if marker_exists else "no_prior_apply_marker",
            "future_marker_write_required_before_any_config_mutation": True,
        },
        "preconditions": preconditions,
        "blocked_reasons": blocked_reasons,
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "approval_consumed": False,
        "decision_consumed": False,
        "approval_artifact_mutated": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_decision_preflight(payload: dict[str, Any]) -> str:
    validation = payload.get("approval_validation") if isinstance(payload.get("approval_validation"), dict) else {}
    decision_validation = payload.get("decision_record_validation") if isinstance(payload.get("decision_record_validation"), dict) else {}
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    lines = [
        "RPGL Provider Config Apply Decision Preflight",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- decision_consumption_status: {payload.get('decision_consumption_status')}",
        f"- approval_status: {payload.get('approval_status')}",
        f"- approval_decision_accepted: {payload.get('approval_decision_accepted')}",
        f"- immutable_decision_status: {payload.get('immutable_decision_status')}",
        f"- immutable_decision_accepted: {payload.get('immutable_decision_accepted')}",
        f"- decision_records_found: {decision_validation.get('records_found')}",
        f"- idempotency_marker_exists: {idempotency.get('marker_exists')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- validation_errors: {validation.get('errors')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_decision_consumption_plan(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Describe future single-use decision consumption without consuming it."""
    root = Path(vault_root)
    decision = build_provider_config_apply_decision_preflight(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command,
    )
    validation = (
        decision.get("decision_record_validation")
        if isinstance(decision.get("decision_record_validation"), dict)
        else {}
    )
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_exists = marker_path.exists()
    selected_decision_id = validation.get("selected_decision_id")
    selected_decision_ref = validation.get("selected_decision_ref")
    decision_digest = validation.get("selected_decision_digest_sha256")
    approval_validation = (
        decision.get("approval_validation")
        if isinstance(decision.get("approval_validation"), dict)
        else {}
    )
    approval_record = (
        load_provider_config_apply_approval_request(root, gate_approval_id)
        if approval_validation.get("structurally_valid")
        else {}
    )
    approval_digest = approval_record.get("request_digest_sha256")
    decision_status = str(decision.get("decision_consumption_status") or "unknown")
    approved_decision_ready = decision_status == "approved_decision_record_valid_but_executor_not_built"
    if approved_decision_ready and not marker_exists:
        plan_status = "ready_for_consumption_design_review_executor_not_built"
        next_action = "implement_atomic_decision_consumer_before_any_live_apply_executor"
    elif marker_exists:
        plan_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_any_consumption"
    else:
        plan_status = f"blocked_{decision_status}"
        next_action = str(decision.get("next_action") or "resolve_decision_preflight_before_consumption")

    marker_preview = {
        "record_type": "runtime_provider_config_apply_decision_consumption_marker",
        "schema_version": SCHEMA_VERSION,
        "marker_schema_id": "rpgl.provider_config_apply_consumption_marker.v1",
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "gate_approval_id": gate_approval_id,
        "proposal_id": decision.get("proposal_id"),
        "queue_item_id": decision.get("queue_item_id"),
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": selected_decision_ref,
        "decision_digest_sha256": decision_digest,
        "approval_request_digest_sha256": approval_digest,
        "marker_status": "would_reserve_single_use_apply_attempt",
        "decision_consumption_status": "would_mark_decision_consumed_before_config_mutation",
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "created_at": "<future-executor-timestamp>",
        "source_command": source_command,
    }
    atomic_rules = [
        "rerun_config_apply_decision_preflight_inside_consumer",
        "require_exactly_one_valid_approved_immutable_decision_record",
        "require_decision_digest_match_at_consumption_time",
        "require_approval_request_digest_match_at_consumption_time",
        "require_marker_path_confined_to_provider_config_apply_markers",
        "create_marker_parent_directory_inside_declared_state_path_only",
        "write_marker_with_create_new_exclusive_semantics",
        "fail_closed_if_marker_already_exists_or_write_is_partial",
        "persist_and_flush_consumption_marker_before_any_config_mutation",
        "write_rollback_snapshot_before_any_config_mutation",
        "apply_only_reviewed_target_paths_after_marker_reservation",
        "mark_marker_completed_only_after_post_apply_verification_passes",
        "mark_marker_failed_and_preserve_rollback_snapshot_if_apply_or_verification_fails",
    ]
    preconditions = [
        {
            "id": "decision_preflight_allows_future_consumption",
            "passed": approved_decision_ready,
            "status": decision_status,
            "critical": True,
        },
        {
            "id": "single_use_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "marker_path": str(marker_path),
            "critical": True,
        },
        {
            "id": "atomic_marker_writer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "decision_consumer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "live_apply_executor_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
    ]
    blocked_reasons = list(decision.get("blocked_reasons") or [])
    blocked_reasons.extend(
        [
            "provider_config_apply_atomic_marker_writer_not_implemented",
            "provider_config_apply_decision_consumer_not_implemented",
            "provider_config_apply_live_executor_not_implemented",
        ]
    )
    if marker_exists and "provider_config_apply_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_consumption_plan_requested",
            runtime="cli",
            provider_id="openai",
            model=decision.get("apply_design", {}).get("approval_request_template", {}).get("expected_primary_model")
            if isinstance(decision.get("apply_design"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=plan_status,
            reason="provider_config_apply_decision_consumption_plan_is_non_mutating",
            queue_item_id=str(decision.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "consumption_marker_schema_id": "rpgl.provider_config_apply_consumption_marker.v1",
        "proposal_id": decision.get("proposal_id"),
        "proposal_ref": decision.get("proposal_ref"),
        "queue_item_id": decision.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "decision_consumption_plan_status": plan_status,
        "executor_status": "not_built",
        "decision_preflight": decision,
        "decision_record_validation": validation,
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": selected_decision_ref,
        "future_consumption_marker_plan": {
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "write_enabled": False,
            "write_supported": False,
            "atomic_create_new_required": True,
            "would_write_before_config_mutation": True,
            "payload_preview": marker_preview,
        },
        "atomic_consumption_rules": atomic_rules,
        "preconditions": preconditions,
        "blocked_reasons": blocked_reasons,
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "approval_consumed": False,
        "decision_consumed": False,
        "consumption_marker_written": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "feature_completion_tracker": {
            "rpgl_status": "PARTIAL / IMPLEMENTED FOUNDATION",
            "can_call_feature_complete": False,
            "completed": [
                "provider_strength_classification",
                "task_class_capability_gate",
                "weak_fallback_denial_for_high_authority_work",
                "queue_on_denial",
                "fallback_timeout_decision_records",
                "primary_cooldown_recovery_state",
                "provider_status_cli",
                "provider_config_reconciliation",
                "provider_config_proposal_queue_request",
                "provider_config_apply_preflight",
                "provider_config_apply_design",
                "provider_config_apply_approval_request_artifact",
                "immutable_operator_approval_decision_record",
                "immutable_approval_decision_record_validation",
                "provider_config_apply_decision_preflight",
                "provider_config_apply_decision_consumption_plan",
                "provider_config_apply_decision_consumer_design",
                "provider_config_apply_decision_consumer_preflight",
                "provider_config_apply_decision_consumer_implementation_plan",
                "provider_config_apply_decision_consumer_writer_dry_run",
                "provider_config_apply_executor_dry_run_plan",
            ],
            "remaining_before_complete": [
                "approval_decision_consumer_implementation",
                "atomic_consumption_marker_writer",
                "live_provider_config_apply_executor",
                "rollback_execution_after_failed_apply_verification",
                "live_provider_probe_executor",
                "live_ollama_first_token_no_chunk_timeout_integration",
                "Hermes_OpenClaw_consumption_of_RPGL_route_decisions_where_not_already_integrated",
                "Discord_read_only_or_dry_run_surface_if_operator_keeps_it_in_scope",
            ],
        },
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_decision_consumption_plan(payload: dict[str, Any]) -> str:
    marker = (
        payload.get("future_consumption_marker_plan")
        if isinstance(payload.get("future_consumption_marker_plan"), dict)
        else {}
    )
    tracker = (
        payload.get("feature_completion_tracker")
        if isinstance(payload.get("feature_completion_tracker"), dict)
        else {}
    )
    lines = [
        "RPGL Provider Config Apply Decision Consumption Plan",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- decision_consumption_plan_status: {payload.get('decision_consumption_plan_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- marker_path: {marker.get('marker_path')}",
        f"- marker_exists: {marker.get('marker_exists')}",
        f"- marker_write_enabled: {marker.get('write_enabled')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- consumption_marker_written: {payload.get('consumption_marker_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- rpgl_can_call_complete: {tracker.get('can_call_feature_complete')}",
        f"- remaining_before_complete: {tracker.get('remaining_before_complete')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_decision_consumer_design(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future provider-config approval-decision consumer design without consuming it."""
    root = Path(vault_root)
    consumption_plan = build_provider_config_apply_decision_consumption_plan(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command or "chaseos runtime provider config-apply-decision-consumer-design",
    )
    decision_preflight = (
        consumption_plan.get("decision_preflight")
        if isinstance(consumption_plan.get("decision_preflight"), dict)
        else {}
    )
    validation = (
        consumption_plan.get("decision_record_validation")
        if isinstance(consumption_plan.get("decision_record_validation"), dict)
        else {}
    )
    marker_plan = (
        consumption_plan.get("future_consumption_marker_plan")
        if isinstance(consumption_plan.get("future_consumption_marker_plan"), dict)
        else {}
    )
    marker_payload = (
        marker_plan.get("payload_preview")
        if isinstance(marker_plan.get("payload_preview"), dict)
        else {}
    )
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_exists = bool(marker_plan.get("marker_exists") or marker_path.exists())
    marker_directory = (root / CONFIG_APPLY_MARKER_RELATIVE_DIR).resolve()
    plan_status = str(consumption_plan.get("decision_consumption_plan_status") or "unknown")
    plan_ready = plan_status == "ready_for_consumption_design_review_executor_not_built"
    selected_decision_id = consumption_plan.get("selected_decision_id")

    if marker_exists:
        consumer_design_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_any_decision_consumer"
    elif not plan_ready:
        consumer_design_status = "blocked_decision_consumption_plan_not_ready"
        next_action = str(consumption_plan.get("next_action") or "resolve_decision_consumption_plan_before_consumer")
    else:
        consumer_design_status = "ready_for_future_decision_consumer_but_consumer_not_built"
        next_action = "implement_decision_consumer_before_atomic_marker_writer_or_live_apply"

    consumer_record_template = {
        "record_type": "runtime_provider_config_apply_decision_consumer_record",
        "schema_version": SCHEMA_VERSION,
        "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "proposal_id": consumption_plan.get("proposal_id"),
        "queue_item_id": consumption_plan.get("queue_item_id"),
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": consumption_plan.get("selected_decision_ref"),
        "decision_digest_sha256": validation.get("selected_decision_digest_sha256")
        or marker_payload.get("decision_digest_sha256"),
        "approval_request_digest_sha256": marker_payload.get("approval_request_digest_sha256"),
        "target_marker_path": str(marker_path),
        "decision_consumption_plan_status": plan_status,
        "consumer_status": "future_single_use_decision_consumed_before_marker_write",
        "consumer_digest_sha256": "<future-consumer-record-digest>",
        "created_at": "<future-consumer-timestamp>",
        "source_command": source_command,
        "consumer_side_effects": {
            "approval_artifact_mutated": False,
            "decision_record_mutated": False,
            "decision_consumed_now": False,
            "consumer_record_written_now": False,
            "idempotency_marker_written_now": False,
            "provider_config_mutated_before_consumption": False,
            "setup_state_mutated_before_consumption": False,
        },
    }
    consumer_algorithm = [
        "rerun config apply decision preflight immediately before consumption",
        "require structurally valid approval request artifact matching the current apply design",
        "require exactly one immutable approved decision record for the gate_approval_id",
        "reject denied, revoked, expired, missing, duplicate, or digest-invalid decision records",
        "verify approval request digest and decision digest at consumption time",
        "verify future idempotency marker path is confined and absent",
        "preserve immutable decision records; represent consumption through a separate consumer record and future marker",
        "emit a sanitized consumer record that contains no secret, token, cookie, credential, or env value",
        "hand the consumer record to the atomic marker writer before any provider config or setup mutation",
        "fail closed if any validation, path, digest, or marker-preexistence check changes between plan and consume",
    ]
    preconditions = [
        {
            "id": "decision_consumption_plan_ready",
            "passed": plan_ready,
            "status": plan_status,
            "critical": True,
            "reason": "consumer requires a ready no-mutation consumption plan",
        },
        {
            "id": "single_approved_immutable_decision_selected",
            "passed": bool(selected_decision_id),
            "status": str(selected_decision_id or validation.get("status") or "missing"),
            "critical": True,
            "reason": "consumer must bind one approved immutable decision record",
        },
        {
            "id": "decision_record_consumable",
            "passed": bool(validation.get("decision_record_consumable")),
            "status": str(validation.get("status") or "unknown"),
            "critical": True,
            "reason": "decision validation must mark the record consumable",
        },
        {
            "id": "single_use_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "marker_path": str(marker_path),
            "critical": True,
            "reason": "consumer must fail if a prior apply marker exists",
        },
        {
            "id": "decision_consumer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
            "reason": "approval decision consumer implementation is not built",
        },
        {
            "id": "atomic_marker_writer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
            "reason": "consumer must hand off to an atomic marker writer before live apply",
        },
        {
            "id": "live_apply_executor_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
            "reason": "live provider config apply executor is not built",
        },
    ]
    blocked_reasons = list(consumption_plan.get("blocked_reasons") or [])
    for reason in [
        "provider_config_apply_decision_consumer_not_implemented",
        "provider_config_apply_atomic_marker_writer_not_implemented",
        "provider_config_apply_live_executor_not_implemented",
    ]:
        if reason not in blocked_reasons:
            blocked_reasons.append(reason)
    if marker_exists and "provider_config_apply_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_consumer_design_requested",
            runtime="cli",
            provider_id="openai",
            model=decision_preflight.get("apply_design", {}).get("approval_request_template", {}).get("expected_primary_model")
            if isinstance(decision_preflight.get("apply_design"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=consumer_design_status,
            reason="provider_config_apply_decision_consumer_design_is_non_mutating",
            queue_item_id=str(consumption_plan.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "generated_at": _utc_now(),
        "proposal_id": consumption_plan.get("proposal_id"),
        "proposal_ref": consumption_plan.get("proposal_ref"),
        "queue_item_id": consumption_plan.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "consumer_design_status": consumer_design_status,
        "consumer_status": "not_built",
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "decision_consumption_plan": consumption_plan,
        "decision_record_validation": validation,
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": consumption_plan.get("selected_decision_ref"),
        "idempotency": {
            "marker_directory": str(marker_directory),
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "marker_write_required_after_consumption": True,
            "future_marker_write_mode": "atomic_create_new_only",
        },
        "consumer_record_template": consumer_record_template,
        "consumer_algorithm": consumer_algorithm,
        "path_constraints": {
            "decision_record_directory": str((root / CONFIG_APPLY_DECISION_RELATIVE_DIR).resolve()),
            "approval_request_directory": str((root / CONFIG_APPLY_APPROVAL_RELATIVE_DIR).resolve()),
            "marker_directory": str(marker_directory),
            "marker_path": str(marker_path),
            "path_escape_allowed": False,
            "decision_record_mutation_allowed": False,
            "approval_artifact_mutation_allowed": False,
            "marker_overwrite_allowed": False,
        },
        "future_consumer_preconditions": preconditions,
        "failure_handling_policy": [
            "do not mutate immutable decision records during consumption",
            "do not mark the original approval artifact consumed by editing it",
            "do not proceed to marker writer if approval or decision digest changes",
            "do not proceed to marker writer if a prior apply marker exists",
            "require operator review and a new approval request for any retry after marker creation",
        ],
        "forbidden_consumer_fields": [
            "password",
            "api_key",
            "authorization",
            "secret",
            "token",
            "credential",
            "env_value",
            "cookie",
            "session",
            "private_key",
        ],
        "blocked_reasons": blocked_reasons,
        "approval_consumed": False,
        "decision_consumed": False,
        "decision_consumer_record_written": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "marker_directory_created": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_decision_consumer_design(payload: dict[str, Any]) -> str:
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    lines = [
        "RPGL Provider Config Apply Decision Consumer Design",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_design_status: {payload.get('consumer_design_status')}",
        f"- consumer_status: {payload.get('consumer_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- marker_path: {idempotency.get('marker_path')}",
        f"- marker_exists: {idempotency.get('marker_exists')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- decision_consumer_record_written: {payload.get('decision_consumer_record_written')}",
        f"- consumption_marker_written: {payload.get('consumption_marker_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_decision_consumer_preflight(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Inspect whether a future decision consumer invocation would be allowed."""
    root = Path(vault_root)
    consumer_design = build_provider_config_apply_decision_consumer_design(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command or "chaseos runtime provider config-apply-decision-consumer-preflight",
    )
    consumption_plan = (
        consumer_design.get("decision_consumption_plan")
        if isinstance(consumer_design.get("decision_consumption_plan"), dict)
        else {}
    )
    validation = (
        consumer_design.get("decision_record_validation")
        if isinstance(consumer_design.get("decision_record_validation"), dict)
        else {}
    )
    idempotency = consumer_design.get("idempotency") if isinstance(consumer_design.get("idempotency"), dict) else {}
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_directory = (root / CONFIG_APPLY_MARKER_RELATIVE_DIR).resolve()
    marker_exists = bool(idempotency.get("marker_exists") or marker_path.exists())
    consumer_design_status = str(consumer_design.get("consumer_design_status") or "unknown")
    selected_decision_id = consumer_design.get("selected_decision_id")
    selected_decision_ref = consumer_design.get("selected_decision_ref")
    approval_request_digest = (
        consumer_design.get("consumer_record_template", {}).get("approval_request_digest_sha256")
        if isinstance(consumer_design.get("consumer_record_template"), dict)
        else None
    )
    decision_digest = validation.get("selected_decision_digest_sha256")

    if marker_exists:
        consumer_preflight_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_decision_consumer_invocation"
    elif consumer_design_status != "ready_for_future_decision_consumer_but_consumer_not_built":
        consumer_preflight_status = "blocked_decision_consumer_design_not_ready"
        next_action = str(consumer_design.get("next_action") or "resolve_decision_consumer_design_before_preflight")
    else:
        consumer_preflight_status = "ready_for_future_decision_consumer_invocation_but_consumer_not_built"
        next_action = "implement_decision_consumer_with_explicit_write_flag_after_preflight_tests"

    stop_conditions = [
        "approval_artifact_missing_invalid_or_drifted",
        "immutable_decision_record_missing_duplicate_invalid_denied_revoked_or_expired",
        "approval_request_digest_mismatch",
        "decision_digest_mismatch",
        "idempotency_marker_exists",
        "marker_path_escape_detected",
        "decision_consumer_not_built",
        "atomic_marker_writer_not_built",
        "live_apply_executor_not_built",
        "provider_config_or_setup_target_drifted_since_preflight",
        "any_secret_or_env_value_required_for_preflight",
    ]
    handoff_requirements = [
        "preserve_immutable_decision_record",
        "do_not_edit_original_approval_artifact",
        "write_future_consumer_record_as_separate_sanitized_record_only",
        "require_atomic_marker_writer_before_any_provider_config_mutation",
        "fail_closed_if_any_input_changes_between_preflight_and_consumption",
        "require_explicit_write_flag_for_future_consumer_implementation",
        "emit_audit_event_for_any_future_consumer_attempt",
    ]
    consumer_invocation_contract = {
        "schema_id": "rpgl.provider_config_apply_decision_consumer_preflight.v1",
        "required_proposal_id": consumer_design.get("proposal_id"),
        "required_gate_approval_id": gate_approval_id,
        "required_selected_decision_id": selected_decision_id,
        "required_selected_decision_ref": selected_decision_ref,
        "required_approval_request_digest_sha256": approval_request_digest,
        "required_decision_digest_sha256": decision_digest,
        "required_marker_absent": True,
        "future_consumer_requires_explicit_write_flag": True,
        "future_consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "future_marker_schema_id": "rpgl.provider_config_apply_consumption_marker.v1",
    }
    preconditions = [
        {
            "id": "decision_consumer_design_ready",
            "passed": consumer_design_status == "ready_for_future_decision_consumer_but_consumer_not_built",
            "status": consumer_design_status,
            "critical": True,
        },
        {
            "id": "single_approved_immutable_decision_selected",
            "passed": bool(selected_decision_id),
            "status": str(selected_decision_id or validation.get("status") or "missing"),
            "critical": True,
        },
        {
            "id": "decision_record_consumable",
            "passed": bool(validation.get("decision_record_consumable")),
            "status": str(validation.get("status") or "unknown"),
            "critical": True,
        },
        {
            "id": "approval_request_digest_available",
            "passed": bool(approval_request_digest),
            "status": "present" if approval_request_digest else "missing",
            "critical": True,
        },
        {
            "id": "decision_digest_available",
            "passed": bool(decision_digest),
            "status": "present" if decision_digest else "missing",
            "critical": True,
        },
        {
            "id": "single_use_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "marker_path": str(marker_path),
            "critical": True,
        },
        {
            "id": "decision_consumer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "atomic_marker_writer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "live_apply_executor_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
    ]
    blocked_reasons = list(consumer_design.get("blocked_reasons") or [])
    for reason in [
        "provider_config_apply_decision_consumer_not_implemented",
        "provider_config_apply_atomic_marker_writer_not_implemented",
        "provider_config_apply_live_executor_not_implemented",
    ]:
        if reason not in blocked_reasons:
            blocked_reasons.append(reason)
    if marker_exists and "provider_config_apply_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_consumer_preflight_requested",
            runtime="cli",
            provider_id="openai",
            model=consumer_design.get("decision_consumption_plan", {})
            .get("decision_preflight", {})
            .get("apply_design", {})
            .get("approval_request_template", {})
            .get("expected_primary_model")
            if isinstance(consumer_design.get("decision_consumption_plan"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=consumer_preflight_status,
            reason="provider_config_apply_decision_consumer_preflight_is_non_mutating",
            queue_item_id=str(consumer_design.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "consumer_preflight_schema_id": "rpgl.provider_config_apply_decision_consumer_preflight.v1",
        "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "generated_at": _utc_now(),
        "proposal_id": consumer_design.get("proposal_id"),
        "proposal_ref": consumer_design.get("proposal_ref"),
        "queue_item_id": consumer_design.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "consumer_preflight_status": consumer_preflight_status,
        "consumer_status": "not_built",
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "consumer_design": consumer_design,
        "decision_consumption_plan": consumption_plan,
        "decision_record_validation": validation,
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": selected_decision_ref,
        "selected_decision_digest_sha256": decision_digest,
        "approval_request_digest_sha256": approval_request_digest,
        "idempotency": {
            "marker_directory": str(marker_directory),
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "future_marker_write_mode": "atomic_create_new_only",
            "marker_directory_creation_allowed_in_future_consumer": False,
            "marker_write_supported_now": False,
        },
        "consumer_invocation_contract": consumer_invocation_contract,
        "future_consumer_preconditions": preconditions,
        "stop_conditions": stop_conditions,
        "handoff_requirements": handoff_requirements,
        "blocked_reasons": blocked_reasons,
        "approval_consumed": False,
        "decision_consumed": False,
        "decision_consumer_record_written": False,
        "consumer_preflight_record_written": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "marker_directory_created": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_decision_consumer_preflight(payload: dict[str, Any]) -> str:
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    contract = (
        payload.get("consumer_invocation_contract")
        if isinstance(payload.get("consumer_invocation_contract"), dict)
        else {}
    )
    lines = [
        "RPGL Provider Config Apply Decision Consumer Preflight",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_preflight_status: {payload.get('consumer_preflight_status')}",
        f"- consumer_status: {payload.get('consumer_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- required_decision_digest_sha256: {contract.get('required_decision_digest_sha256')}",
        f"- marker_path: {idempotency.get('marker_path')}",
        f"- marker_exists: {idempotency.get('marker_exists')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- decision_consumer_record_written: {payload.get('decision_consumer_record_written')}",
        f"- consumer_preflight_record_written: {payload.get('consumer_preflight_record_written')}",
        f"- consumption_marker_written: {payload.get('consumption_marker_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_decision_consumer_implementation_plan(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Describe the future decision consumer writer implementation without writing it."""
    root = Path(vault_root)
    consumer_preflight = build_provider_config_apply_decision_consumer_preflight(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command or "chaseos runtime provider config-apply-decision-consumer-implementation-plan",
    )
    validation = (
        consumer_preflight.get("decision_record_validation")
        if isinstance(consumer_preflight.get("decision_record_validation"), dict)
        else {}
    )
    idempotency = (
        consumer_preflight.get("idempotency")
        if isinstance(consumer_preflight.get("idempotency"), dict)
        else {}
    )
    invocation_contract = (
        consumer_preflight.get("consumer_invocation_contract")
        if isinstance(consumer_preflight.get("consumer_invocation_contract"), dict)
        else {}
    )
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_exists = bool(idempotency.get("marker_exists") or marker_path.exists())
    consumer_directory = (root / CONFIG_APPLY_CONSUMER_RELATIVE_DIR).resolve()
    selected_decision_id = consumer_preflight.get("selected_decision_id")
    consumer_record_filename = f"{gate_approval_id}.json" if selected_decision_id else f"{gate_approval_id}.pending-decision.json"
    consumer_record_path = consumer_directory / consumer_record_filename
    preflight_status = str(consumer_preflight.get("consumer_preflight_status") or "unknown")
    preflight_ready = preflight_status == "ready_for_future_decision_consumer_invocation_but_consumer_not_built"

    if marker_exists:
        implementation_plan_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_consumer_implementation"
    elif not preflight_ready:
        implementation_plan_status = "blocked_decision_consumer_preflight_not_ready"
        next_action = str(consumer_preflight.get("next_action") or "resolve_decision_consumer_preflight_before_writer_plan")
    else:
        implementation_plan_status = "ready_for_future_decision_consumer_implementation_but_writer_not_built"
        next_action = "implement_explicit_write_consumer_after_marker_writer_contract_is_ready"

    consumer_record_template = {
        "record_type": "runtime_provider_config_apply_decision_consumer_record",
        "schema_version": SCHEMA_VERSION,
        "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "proposal_id": consumer_preflight.get("proposal_id"),
        "queue_item_id": consumer_preflight.get("queue_item_id"),
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": consumer_preflight.get("selected_decision_ref"),
        "decision_digest_sha256": invocation_contract.get("required_decision_digest_sha256"),
        "approval_request_digest_sha256": invocation_contract.get("required_approval_request_digest_sha256"),
        "target_marker_path": str(marker_path),
        "consumer_record_path": str(consumer_record_path),
        "consumer_status": "future_consumed_before_marker_write",
        "consumer_write_mode": "explicit_write_flag_atomic_create_new_only",
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "created_at": "<future-consumer-writer-timestamp>",
        "source_command": source_command,
    }
    implementation_sequence = [
        "require explicit write flag for future consumer writer invocation",
        "rerun decision consumer preflight immediately before writing any consumer record",
        "require exactly one valid approved immutable decision record and matching digests",
        "require the idempotency marker path to be absent before writing the consumer record",
        "write the sanitized consumer record with create-new semantics under the declared consumer directory",
        "flush the consumer record before handing off to the atomic marker writer",
        "do not edit the original approval artifact or immutable decision record",
        "do not mutate provider config, setup state, provider state, queues, or gateways in the consumer writer",
        "handoff to atomic marker writer before any live apply executor can mutate provider config",
        "fail closed and preserve written consumer evidence if marker writer or live apply later fails",
    ]
    write_contract = {
        "future_command": "chaseos runtime provider config-apply-decision-consumer <proposal_id> --gate-approval-id <id> --write-consumer-record",
        "future_write_flag_required": "--write-consumer-record",
        "write_supported_now": False,
        "write_enabled": False,
        "consumer_record_directory": str(consumer_directory),
        "consumer_record_path": str(consumer_record_path),
        "directory_created_now": False,
        "record_written_now": False,
        "atomic_create_new_required": True,
        "overwrite_allowed": False,
        "delete_on_failure_allowed": False,
    }
    preconditions = [
        {
            "id": "decision_consumer_preflight_ready",
            "passed": preflight_ready,
            "status": preflight_status,
            "critical": True,
        },
        {
            "id": "single_approved_immutable_decision_selected",
            "passed": bool(selected_decision_id),
            "status": str(selected_decision_id or validation.get("status") or "missing"),
            "critical": True,
        },
        {
            "id": "decision_record_consumable",
            "passed": bool(validation.get("decision_record_consumable")),
            "status": str(validation.get("status") or "unknown"),
            "critical": True,
        },
        {
            "id": "idempotency_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "marker_path": str(marker_path),
            "critical": True,
        },
        {
            "id": "decision_consumer_writer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "atomic_marker_writer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
        {
            "id": "live_apply_executor_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
    ]
    blocked_reasons = list(consumer_preflight.get("blocked_reasons") or [])
    for reason in [
        "provider_config_apply_decision_consumer_writer_not_implemented",
        "provider_config_apply_atomic_marker_writer_not_implemented",
        "provider_config_apply_live_executor_not_implemented",
    ]:
        if reason not in blocked_reasons:
            blocked_reasons.append(reason)
    if marker_exists and "provider_config_apply_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_consumer_implementation_plan_requested",
            runtime="cli",
            provider_id="openai",
            model=consumer_preflight.get("consumer_design", {})
            .get("decision_consumption_plan", {})
            .get("decision_preflight", {})
            .get("apply_design", {})
            .get("approval_request_template", {})
            .get("expected_primary_model")
            if isinstance(consumer_preflight.get("consumer_design"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=implementation_plan_status,
            reason="provider_config_apply_decision_consumer_implementation_plan_is_non_mutating",
            queue_item_id=str(consumer_preflight.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "consumer_implementation_plan_schema_id": "rpgl.provider_config_apply_decision_consumer_implementation_plan.v1",
        "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "generated_at": _utc_now(),
        "proposal_id": consumer_preflight.get("proposal_id"),
        "proposal_ref": consumer_preflight.get("proposal_ref"),
        "queue_item_id": consumer_preflight.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "consumer_implementation_plan_status": implementation_plan_status,
        "consumer_writer_status": "not_built",
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "consumer_preflight": consumer_preflight,
        "decision_record_validation": validation,
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": consumer_preflight.get("selected_decision_ref"),
        "consumer_record_template": consumer_record_template,
        "consumer_write_contract": write_contract,
        "implementation_sequence": implementation_sequence,
        "path_constraints": {
            "consumer_record_directory": str(consumer_directory),
            "consumer_record_path": str(consumer_record_path),
            "decision_record_directory": str((root / CONFIG_APPLY_DECISION_RELATIVE_DIR).resolve()),
            "approval_request_directory": str((root / CONFIG_APPLY_APPROVAL_RELATIVE_DIR).resolve()),
            "marker_directory": str((root / CONFIG_APPLY_MARKER_RELATIVE_DIR).resolve()),
            "marker_path": str(marker_path),
            "path_escape_allowed": False,
            "consumer_record_overwrite_allowed": False,
            "decision_record_mutation_allowed": False,
            "approval_artifact_mutation_allowed": False,
        },
        "future_consumer_writer_preconditions": preconditions,
        "failure_handling_policy": [
            "do not delete immutable decision records",
            "do not edit the original approval request artifact",
            "do not proceed if approval or decision digests drift",
            "do not proceed if an idempotency marker already exists",
            "do not mutate provider config before atomic marker writer succeeds",
            "preserve consumer record evidence if downstream marker writer or apply executor fails",
        ],
        "forbidden_consumer_record_fields": [
            "password",
            "api_key",
            "authorization",
            "secret",
            "token",
            "credential",
            "env_value",
            "cookie",
            "session",
            "private_key",
        ],
        "blocked_reasons": blocked_reasons,
        "approval_consumed": False,
        "decision_consumed": False,
        "decision_consumer_record_written": False,
        "consumer_preflight_record_written": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "consumer_directory_created": False,
        "marker_directory_created": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_decision_consumer_implementation_plan(payload: dict[str, Any]) -> str:
    write_contract = (
        payload.get("consumer_write_contract")
        if isinstance(payload.get("consumer_write_contract"), dict)
        else {}
    )
    lines = [
        "RPGL Provider Config Apply Decision Consumer Implementation Plan",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_implementation_plan_status: {payload.get('consumer_implementation_plan_status')}",
        f"- consumer_writer_status: {payload.get('consumer_writer_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- future_write_flag_required: {write_contract.get('future_write_flag_required')}",
        f"- consumer_record_path: {write_contract.get('consumer_record_path')}",
        f"- write_enabled: {write_contract.get('write_enabled')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- decision_consumer_record_written: {payload.get('decision_consumer_record_written')}",
        f"- consumption_marker_written: {payload.get('consumption_marker_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_decision_consumer_writer_dry_run(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Simulate the future decision consumer writer without writing records."""
    root = Path(vault_root)
    implementation_plan = build_provider_config_apply_decision_consumer_implementation_plan(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command or "chaseos runtime provider config-apply-decision-consumer-writer-dry-run",
    )
    validation = (
        implementation_plan.get("decision_record_validation")
        if isinstance(implementation_plan.get("decision_record_validation"), dict)
        else {}
    )
    write_contract = (
        implementation_plan.get("consumer_write_contract")
        if isinstance(implementation_plan.get("consumer_write_contract"), dict)
        else {}
    )
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_exists = marker_path.exists()
    consumer_directory = (root / CONFIG_APPLY_CONSUMER_RELATIVE_DIR).resolve()
    selected_decision_id = implementation_plan.get("selected_decision_id")
    plan_status = str(implementation_plan.get("consumer_implementation_plan_status") or "unknown")
    plan_ready = plan_status == "ready_for_future_decision_consumer_implementation_but_writer_not_built"

    if marker_exists:
        writer_dry_run_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_consumer_writer_dry_run"
    elif not plan_ready:
        writer_dry_run_status = "blocked_decision_consumer_implementation_plan_not_ready"
        next_action = str(implementation_plan.get("next_action") or "resolve_decision_consumer_implementation_plan_before_dry_run")
    else:
        writer_dry_run_status = "ready_for_future_consumer_writer_dry_run_but_write_disabled"
        next_action = "implement_real_consumer_writer_only_after_dry_run_and_marker_writer_are_verified"

    candidate_record = dict(implementation_plan.get("consumer_record_template") or {})
    candidate_record.update(
        {
            "consumer_status": "dry_run_preview_only_not_consumed",
            "consumer_write_mode": "dry_run_no_write",
            "consumer_record_written": False,
            "approval_consumed": False,
            "decision_consumed": False,
            "decision_record_mutated": False,
            "approval_artifact_mutated": False,
            "consumption_marker_written": False,
            "idempotency_marker_written": False,
            "dry_run_generated_at": "<dry-run-timestamp>",
            "source_command": source_command,
        }
    )
    candidate_record_digest = _consumer_record_digest(candidate_record)
    candidate_record["consumer_record_digest_sha256"] = candidate_record_digest
    dry_run_steps = [
        "load implementation plan",
        "rerun decision consumer preflight through implementation plan",
        "require ready implementation-plan status before future writes",
        "verify selected immutable approved decision metadata and digests",
        "verify consumer record path remains under declared consumer directory",
        "verify idempotency marker remains absent",
        "build sanitized consumer record payload",
        "compute consumer record digest",
        "do not create consumer directory",
        "do not write consumer record",
        "do not write idempotency marker",
        "do not consume approval or decision",
    ]
    preconditions = [
        {
            "id": "implementation_plan_ready",
            "passed": plan_ready,
            "status": plan_status,
            "critical": True,
        },
        {
            "id": "single_approved_immutable_decision_selected",
            "passed": bool(selected_decision_id),
            "status": str(selected_decision_id or validation.get("status") or "missing"),
            "critical": True,
        },
        {
            "id": "decision_record_consumable",
            "passed": bool(validation.get("decision_record_consumable")),
            "status": str(validation.get("status") or "unknown"),
            "critical": True,
        },
        {
            "id": "consumer_record_path_confined",
            "passed": str(write_contract.get("consumer_record_path") or "").startswith(str(consumer_directory)),
            "status": str(write_contract.get("consumer_record_path") or "missing"),
            "critical": True,
        },
        {
            "id": "idempotency_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "marker_path": str(marker_path),
            "critical": True,
        },
        {
            "id": "consumer_writer_real_write_enabled",
            "passed": False,
            "status": "disabled_dry_run_only",
            "critical": True,
        },
        {
            "id": "atomic_marker_writer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
        },
    ]
    blocked_reasons = list(implementation_plan.get("blocked_reasons") or [])
    for reason in [
        "provider_config_apply_decision_consumer_writer_real_write_not_enabled",
        "provider_config_apply_atomic_marker_writer_not_implemented",
        "provider_config_apply_live_executor_not_implemented",
    ]:
        if reason not in blocked_reasons:
            blocked_reasons.append(reason)
    if marker_exists and "provider_config_apply_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_consumer_writer_dry_run_requested",
            runtime="cli",
            provider_id="openai",
            model=implementation_plan.get("consumer_preflight", {})
            .get("consumer_design", {})
            .get("decision_consumption_plan", {})
            .get("decision_preflight", {})
            .get("apply_design", {})
            .get("approval_request_template", {})
            .get("expected_primary_model")
            if isinstance(implementation_plan.get("consumer_preflight"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=writer_dry_run_status,
            reason="provider_config_apply_decision_consumer_writer_dry_run_is_non_mutating",
            queue_item_id=str(implementation_plan.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "consumer_writer_dry_run_schema_id": "rpgl.provider_config_apply_decision_consumer_writer_dry_run.v1",
        "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "generated_at": _utc_now(),
        "proposal_id": implementation_plan.get("proposal_id"),
        "proposal_ref": implementation_plan.get("proposal_ref"),
        "queue_item_id": implementation_plan.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "consumer_writer_dry_run_status": writer_dry_run_status,
        "consumer_writer_status": "dry_run_only",
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "implementation_plan": implementation_plan,
        "decision_record_validation": validation,
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": implementation_plan.get("selected_decision_ref"),
        "consumer_record_path": write_contract.get("consumer_record_path"),
        "consumer_record_digest_sha256": candidate_record_digest,
        "candidate_consumer_record": candidate_record,
        "dry_run_steps": dry_run_steps,
        "future_consumer_writer_preconditions": preconditions,
        "path_constraints": {
            "consumer_record_directory": str(consumer_directory),
            "consumer_record_path": write_contract.get("consumer_record_path"),
            "marker_path": str(marker_path),
            "path_escape_allowed": False,
            "consumer_record_overwrite_allowed": False,
            "marker_write_allowed_in_dry_run": False,
        },
        "blocked_reasons": blocked_reasons,
        "write_enabled": False,
        "write_supported_now": False,
        "approval_consumed": False,
        "decision_consumed": False,
        "decision_consumer_record_written": False,
        "consumer_preflight_record_written": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "consumer_directory_created": False,
        "marker_directory_created": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_decision_consumer_writer_dry_run(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Provider Config Apply Decision Consumer Writer Dry Run",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_writer_dry_run_status: {payload.get('consumer_writer_dry_run_status')}",
        f"- consumer_writer_status: {payload.get('consumer_writer_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- consumer_record_path: {payload.get('consumer_record_path')}",
        f"- consumer_record_digest_sha256: {payload.get('consumer_record_digest_sha256')}",
        f"- write_enabled: {payload.get('write_enabled')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- decision_consumer_record_written: {payload.get('decision_consumer_record_written')}",
        f"- consumption_marker_written: {payload.get('consumption_marker_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_decision_consumer_write_guard_contract(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Describe the write guard required before any real consumer writer can be enabled."""
    root = Path(vault_root)
    writer_dry_run = build_provider_config_apply_decision_consumer_writer_dry_run(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command or "chaseos runtime provider config-apply-decision-consumer-write-guard-contract",
    )
    validation = (
        writer_dry_run.get("decision_record_validation")
        if isinstance(writer_dry_run.get("decision_record_validation"), dict)
        else {}
    )
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_exists = marker_path.exists()
    consumer_directory = (root / CONFIG_APPLY_CONSUMER_RELATIVE_DIR).resolve()
    consumer_record_path = Path(str(writer_dry_run.get("consumer_record_path") or consumer_directory / f"{gate_approval_id}.pending-decision.json")).resolve()
    selected_decision_id = writer_dry_run.get("selected_decision_id")
    dry_run_status = str(writer_dry_run.get("consumer_writer_dry_run_status") or "unknown")
    dry_run_ready = dry_run_status == "ready_for_future_consumer_writer_dry_run_but_write_disabled"

    if marker_exists:
        write_guard_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_write_guard"
    elif not dry_run_ready:
        write_guard_status = "blocked_consumer_writer_dry_run_not_ready"
        next_action = str(writer_dry_run.get("next_action") or "resolve_consumer_writer_dry_run_before_write_guard")
    else:
        write_guard_status = "ready_for_future_write_guard_but_real_write_disabled"
        next_action = "implement_real_consumer_writer_only_after_explicit_write_guard_tests"

    explicit_flag_contract = {
        "required_future_flag": "--write-consumer-record",
        "current_cli_accepts_write_flag": False,
        "current_request_contains_write_flag": False,
        "current_write_flag_valid": False,
        "future_writer_must_reject_missing_flag": True,
        "future_writer_must_reject_flag_without_ready_dry_run": True,
        "future_writer_must_reject_flag_if_marker_exists": True,
        "future_writer_must_reject_flag_if_decision_digest_drifted": True,
        "future_writer_must_reject_flag_if_record_path_exists": True,
    }
    create_new_policy = {
        "consumer_record_directory": str(consumer_directory),
        "consumer_record_path": str(consumer_record_path),
        "directory_creation_allowed_only_for_future_writer": True,
        "directory_created_now": False,
        "record_exists_now": consumer_record_path.exists(),
        "record_write_mode_required": "create_new_exclusive",
        "overwrite_allowed": False,
        "delete_on_failure_allowed": False,
        "path_escape_allowed": False,
        "must_flush_before_marker_handoff": True,
    }
    preconditions = [
        {
            "id": "consumer_writer_dry_run_ready",
            "passed": dry_run_ready,
            "status": dry_run_status,
            "critical": True,
        },
        {
            "id": "single_approved_immutable_decision_selected",
            "passed": bool(selected_decision_id),
            "status": str(selected_decision_id or validation.get("status") or "missing"),
            "critical": True,
        },
        {
            "id": "consumer_record_digest_available",
            "passed": bool(writer_dry_run.get("consumer_record_digest_sha256")),
            "status": "present" if writer_dry_run.get("consumer_record_digest_sha256") else "missing",
            "critical": True,
        },
        {
            "id": "consumer_record_path_absent",
            "passed": not consumer_record_path.exists(),
            "status": "absent" if not consumer_record_path.exists() else "present",
            "critical": True,
        },
        {
            "id": "idempotency_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "marker_path": str(marker_path),
            "critical": True,
        },
        {
            "id": "real_write_enabled",
            "passed": False,
            "status": "disabled_contract_only",
            "critical": True,
        },
    ]
    blocked_reasons = list(writer_dry_run.get("blocked_reasons") or [])
    for reason in [
        "provider_config_apply_decision_consumer_real_write_not_enabled",
        "provider_config_apply_atomic_marker_writer_not_implemented",
        "provider_config_apply_live_executor_not_implemented",
    ]:
        if reason not in blocked_reasons:
            blocked_reasons.append(reason)
    if marker_exists and "provider_config_apply_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_consumer_write_guard_contract_requested",
            runtime="cli",
            provider_id="openai",
            model=writer_dry_run.get("implementation_plan", {})
            .get("consumer_preflight", {})
            .get("consumer_design", {})
            .get("decision_consumption_plan", {})
            .get("decision_preflight", {})
            .get("apply_design", {})
            .get("approval_request_template", {})
            .get("expected_primary_model")
            if isinstance(writer_dry_run.get("implementation_plan"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=write_guard_status,
            reason="provider_config_apply_decision_consumer_write_guard_contract_is_non_mutating",
            queue_item_id=str(writer_dry_run.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "consumer_write_guard_contract_schema_id": "rpgl.provider_config_apply_decision_consumer_write_guard_contract.v1",
        "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
        "generated_at": _utc_now(),
        "proposal_id": writer_dry_run.get("proposal_id"),
        "proposal_ref": writer_dry_run.get("proposal_ref"),
        "queue_item_id": writer_dry_run.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "consumer_write_guard_status": write_guard_status,
        "consumer_writer_status": "contract_only",
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "writer_dry_run": writer_dry_run,
        "decision_record_validation": validation,
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": writer_dry_run.get("selected_decision_ref"),
        "consumer_record_path": str(consumer_record_path),
        "consumer_record_digest_sha256": writer_dry_run.get("consumer_record_digest_sha256"),
        "explicit_write_flag_contract": explicit_flag_contract,
        "create_new_record_policy": create_new_policy,
        "future_write_guard_preconditions": preconditions,
        "handoff_requirements": [
            "real writer must rerun writer dry-run immediately before write",
            "real writer must require explicit write flag",
            "real writer must create the consumer record with exclusive create-new semantics",
            "real writer must flush the consumer record before atomic marker writer handoff",
            "real writer must not mutate provider config, setup state, provider state, queues, or gateways",
            "real writer must preserve approval artifact and immutable decision record unchanged",
        ],
        "blocked_reasons": blocked_reasons,
        "write_enabled": False,
        "write_supported_now": False,
        "approval_consumed": False,
        "decision_consumed": False,
        "decision_consumer_record_written": False,
        "consumer_preflight_record_written": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "consumer_directory_created": False,
        "marker_directory_created": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_decision_consumer_write_guard_contract(payload: dict[str, Any]) -> str:
    flag = (
        payload.get("explicit_write_flag_contract")
        if isinstance(payload.get("explicit_write_flag_contract"), dict)
        else {}
    )
    lines = [
        "RPGL Provider Config Apply Decision Consumer Write Guard Contract",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_write_guard_status: {payload.get('consumer_write_guard_status')}",
        f"- consumer_writer_status: {payload.get('consumer_writer_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- required_future_flag: {flag.get('required_future_flag')}",
        f"- current_cli_accepts_write_flag: {flag.get('current_cli_accepts_write_flag')}",
        f"- consumer_record_path: {payload.get('consumer_record_path')}",
        f"- write_enabled: {payload.get('write_enabled')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- decision_consumer_record_written: {payload.get('decision_consumer_record_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def write_provider_config_apply_decision_consumer_record(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist the approval-decision consumer record without applying provider config."""
    root = Path(vault_root)
    source = source_command or "chaseos runtime provider config-apply-decision-consumer"
    guard = build_provider_config_apply_decision_consumer_write_guard_contract(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source,
    )
    selected_decision_id = str(guard.get("selected_decision_id") or "")
    validation = guard.get("decision_record_validation") if isinstance(guard.get("decision_record_validation"), dict) else {}
    ready = (
        guard.get("consumer_write_guard_status") == "ready_for_future_write_guard_but_real_write_disabled"
        and bool(selected_decision_id)
        and bool(validation.get("decision_record_consumable"))
    )
    if not ready:
        event = append_provider_audit_event(
            root,
            ProviderAuditEvent(
                event_type="provider_config_apply_decision_consumer_record_write_blocked",
                runtime="cli",
                provider_id="openai",
                model=guard.get("writer_dry_run", {})
                .get("implementation_plan", {})
                .get("consumer_preflight", {})
                .get("consumer_design", {})
                .get("decision_consumption_plan", {})
                .get("decision_preflight", {})
                .get("apply_design", {})
                .get("approval_request_template", {})
                .get("expected_primary_model")
                if isinstance(guard.get("writer_dry_run"), dict)
                else None,
                provider_strength="strong",
                task_class="runtime_config_change",
                decision=str(guard.get("consumer_write_guard_status") or "blocked"),
                reason="provider_config_apply_decision_consumer_record_write_guard_not_ready",
                queue_item_id=str(guard.get("queue_item_id") or "") or None,
                files_modified=False,
                next_action=str(guard.get("next_action") or "resolve_write_guard_before_consumer_record_write"),
                source_command=source,
            ),
        )
        raise RuntimeProviderGovernanceError(
            "provider config apply decision consumer record write blocked: "
            + ", ".join(guard.get("blocked_reasons") or [str(guard.get("consumer_write_guard_status") or "unknown")])
            + f" (audit_id={event['event_id']})"
        )

    consumer_record_path = _config_apply_consumer_record_path(root, gate_approval_id, selected_decision_id)
    declared_path = str(guard.get("consumer_record_path") or "")
    if declared_path and Path(declared_path).resolve() != consumer_record_path.resolve():
        raise RuntimeProviderGovernanceError("provider config apply decision consumer record path drifted since write guard")
    if consumer_record_path.exists():
        event = append_provider_audit_event(
            root,
            ProviderAuditEvent(
                event_type="provider_config_apply_decision_consumer_record_write_blocked",
                runtime="cli",
                provider_id="openai",
                model="gpt-5.5",
                provider_strength="strong",
                task_class="runtime_config_change",
                decision="blocked_consumer_record_already_exists",
                reason="provider_config_apply_decision_consumer_record_create_new_refused_existing_path",
                queue_item_id=str(guard.get("queue_item_id") or "") or None,
                files_modified=False,
                next_action="operator_must_review_existing_consumer_record_before_retry",
                source_command=source,
            ),
        )
        raise RuntimeProviderGovernanceError(
            f"provider config apply decision consumer record already exists: {consumer_record_path} "
            f"(audit_id={event['event_id']})"
        )

    writer_dry_run = guard.get("writer_dry_run") if isinstance(guard.get("writer_dry_run"), dict) else {}
    candidate_record = writer_dry_run.get("candidate_consumer_record") if isinstance(writer_dry_run.get("candidate_consumer_record"), dict) else {}
    directory_created = not consumer_record_path.parent.exists()
    record = dict(candidate_record)
    record.update(
        {
            "record_type": "runtime_provider_config_apply_decision_consumer_record",
            "schema_version": SCHEMA_VERSION,
            "consumer_record_schema_id": "rpgl.provider_config_apply_decision_consumer.v1",
            "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
            "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
            "gate_approval_id": gate_approval_id,
            "proposal_id": guard.get("proposal_id"),
            "queue_item_id": guard.get("queue_item_id"),
            "selected_decision_id": selected_decision_id,
            "selected_decision_ref": guard.get("selected_decision_ref"),
            "decision_digest_sha256": validation.get("selected_decision_digest_sha256"),
            "consumer_record_ref": str(consumer_record_path),
            "consumer_record_path": str(consumer_record_path),
            "consumer_status": "record_written_marker_handoff_required",
            "consumer_write_mode": "explicit_write_flag_create_new_only",
            "consumer_record_written": True,
            "decision_consumer_record_written": True,
            "consumer_directory_created": directory_created,
            "approval_consumed": False,
            "decision_consumed": True,
            "approval_artifact_mutated": False,
            "decision_record_mutated": False,
            "consumption_marker_written": False,
            "idempotency_marker_written": False,
            "provider_config_mutated": False,
            "setup_state_mutated": False,
            "provider_state_mutated": False,
            "secret_value_read": False,
            "live_network_call_attempted": False,
            "queue_drained": False,
            "gateway_mutated": False,
            "canonical_files_mutated": False,
            "marker_handoff_required": True,
            "apply_execution_allowed": False,
            "execution_enabled": False,
            "created_at": _utc_now(),
            "source_command": source,
        }
    )
    record["consumer_record_digest_sha256"] = _consumer_record_digest(record)
    consumer_record_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with consumer_record_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise RuntimeProviderGovernanceError(f"provider config apply decision consumer record already exists: {consumer_record_path}") from exc

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_decision_consumer_record_written",
            runtime="cli",
            provider_id="openai",
            model=writer_dry_run.get("implementation_plan", {})
            .get("consumer_preflight", {})
            .get("consumer_design", {})
            .get("decision_consumption_plan", {})
            .get("decision_preflight", {})
            .get("apply_design", {})
            .get("approval_request_template", {})
            .get("expected_primary_model")
            if isinstance(writer_dry_run.get("implementation_plan"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="consumer_record_written_marker_handoff_required",
            reason="provider_config_apply_decision_consumer_record_written_without_provider_config_apply",
            queue_item_id=str(guard.get("queue_item_id") or "") or None,
            files_modified=True,
            next_action="run_atomic_marker_writer_before_any_live_provider_config_apply",
            source_command=source,
        ),
    )
    return {
        **guard,
        "consumer_write_status": "consumer_record_written_marker_handoff_required",
        "consumer_writer_status": "record_written",
        "consumer_record": record,
        "consumer_record_ref": str(consumer_record_path),
        "consumer_record_path": str(consumer_record_path),
        "consumer_record_digest_sha256": record["consumer_record_digest_sha256"],
        "write_enabled": True,
        "write_supported_now": True,
        "decision_consumed": True,
        "decision_consumer_record_written": True,
        "consumer_directory_created": directory_created,
        "consumer_preflight_record_written": False,
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": True,
        "write_audit_id": event["event_id"],
        "next_action": "run_atomic_marker_writer_before_any_live_provider_config_apply",
    }


def format_provider_config_apply_decision_consumer_record(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Provider Config Apply Decision Consumer Record",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_write_status: {payload.get('consumer_write_status')}",
        f"- consumer_writer_status: {payload.get('consumer_writer_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- consumer_record_ref: {payload.get('consumer_record_ref')}",
        f"- consumer_record_digest_sha256: {payload.get('consumer_record_digest_sha256')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- decision_consumer_record_written: {payload.get('decision_consumer_record_written')}",
        f"- consumption_marker_written: {payload.get('consumption_marker_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def load_provider_config_apply_consumer_record(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
) -> dict[str, Any] | None:
    path = _config_apply_consumer_record_path(vault_root, gate_approval_id)
    if not path.exists():
        return None
    data = _read_json(path, {})
    data["consumer_record_ref"] = str(path)
    return data


def write_provider_config_apply_atomic_marker(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist the idempotency marker after a valid consumer record, without applying config."""
    root = Path(vault_root)
    source = source_command or "chaseos runtime provider config-apply-atomic-marker-writer"
    decision = build_provider_config_apply_decision_preflight(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source,
    )
    validation = decision.get("decision_record_validation") if isinstance(decision.get("decision_record_validation"), dict) else {}
    selected_decision_id = str(validation.get("selected_decision_id") or "")
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    consumer_record = load_provider_config_apply_consumer_record(root, gate_approval_id=gate_approval_id)
    consumer_digest_valid = False
    consumer_errors: list[str] = []
    if consumer_record:
        expected_consumer_digest = _consumer_record_digest(consumer_record)
        consumer_digest_valid = bool(consumer_record.get("consumer_record_digest_sha256")) and consumer_record.get("consumer_record_digest_sha256") == expected_consumer_digest
        if consumer_record.get("record_type") != "runtime_provider_config_apply_decision_consumer_record":
            consumer_errors.append("consumer_record_type_invalid")
        if consumer_record.get("gate_approval_id") != gate_approval_id:
            consumer_errors.append("consumer_gate_approval_id_mismatch")
        if consumer_record.get("proposal_id") != decision.get("proposal_id"):
            consumer_errors.append("consumer_proposal_id_mismatch")
        if consumer_record.get("queue_item_id") != decision.get("queue_item_id"):
            consumer_errors.append("consumer_queue_item_id_mismatch")
        if consumer_record.get("selected_decision_id") != selected_decision_id:
            consumer_errors.append("consumer_selected_decision_id_mismatch")
        if consumer_record.get("decision_consumed") is not True:
            consumer_errors.append("consumer_decision_consumed_not_true")
        if consumer_record.get("decision_record_mutated") is not False:
            consumer_errors.append("consumer_decision_record_mutated_not_false")
        if consumer_record.get("provider_config_mutated") is not False or consumer_record.get("setup_state_mutated") is not False:
            consumer_errors.append("consumer_mutation_claims_invalid")
        if not consumer_digest_valid:
            consumer_errors.append("consumer_digest_invalid")

    blocked_reasons = list(decision.get("blocked_reasons") or [])
    if validation.get("status") != "approved_decision_record_valid":
        blocked_reasons.append("provider_config_apply_approved_decision_missing_or_invalid")
    if not consumer_record:
        blocked_reasons.append("provider_config_apply_consumer_record_missing")
    blocked_reasons.extend(consumer_errors)
    if marker_path.exists():
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")
    blocked_reasons = list(dict.fromkeys(blocked_reasons))
    ready = (
        validation.get("status") == "approved_decision_record_valid"
        and bool(consumer_record)
        and not consumer_errors
        and not marker_path.exists()
    )
    if not ready:
        event = append_provider_audit_event(
            root,
            ProviderAuditEvent(
                event_type="provider_config_apply_atomic_marker_write_blocked",
                runtime="cli",
                provider_id="openai",
                model=decision.get("apply_design", {}).get("approval_request_template", {}).get("expected_primary_model")
                if isinstance(decision.get("apply_design"), dict)
                else None,
                provider_strength="strong",
                task_class="runtime_config_change",
                decision="blocked_atomic_marker_write_preconditions_not_ready",
                reason="provider_config_apply_atomic_marker_write_preconditions_not_ready",
                queue_item_id=str(decision.get("queue_item_id") or "") or None,
                files_modified=False,
                next_action="write_valid_consumer_record_before_atomic_marker_or_review_existing_marker",
                source_command=source,
            ),
        )
        raise RuntimeProviderGovernanceError(
            "provider config apply atomic marker write blocked: "
            + ", ".join(blocked_reasons or ["unknown"])
            + f" (audit_id={event['event_id']})"
        )

    marker_directory_created = not marker_path.parent.exists()
    marker = {
        "record_type": "runtime_provider_config_apply_consumption_marker",
        "schema_version": SCHEMA_VERSION,
        "marker_schema_id": "rpgl.provider_config_apply_consumption_marker.v1",
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "proposal_id": decision.get("proposal_id"),
        "queue_item_id": decision.get("queue_item_id"),
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": validation.get("selected_decision_ref"),
        "selected_decision_digest_sha256": validation.get("selected_decision_digest_sha256"),
        "consumer_record_ref": consumer_record.get("consumer_record_ref") if consumer_record else None,
        "consumer_record_digest_sha256": consumer_record.get("consumer_record_digest_sha256") if consumer_record else None,
        "marker_status": "written_apply_executor_handoff_required",
        "idempotency_marker_written": True,
        "approval_consumed": False,
        "decision_consumed": True,
        "decision_consumer_record_written": True,
        "consumer_record_mutated": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "apply_execution_allowed": False,
        "execution_enabled": False,
        "created_at": _utc_now(),
        "source_command": source,
    }
    marker["marker_ref"] = str(marker_path)
    marker["marker_digest_sha256"] = _marker_digest(marker)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with marker_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(marker, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise RuntimeProviderGovernanceError(f"provider config apply marker already exists: {marker_path}") from exc

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_atomic_marker_written",
            runtime="cli",
            provider_id="openai",
            model=decision.get("apply_design", {}).get("approval_request_template", {}).get("expected_primary_model")
            if isinstance(decision.get("apply_design"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="atomic_marker_written_apply_executor_handoff_required",
            reason="provider_config_apply_atomic_marker_written_without_provider_config_apply",
            queue_item_id=str(decision.get("queue_item_id") or "") or None,
            files_modified=True,
            next_action="run_live_apply_executor_only_after_gate_and_rollback_preconditions",
            source_command=source,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "marker_schema_id": "rpgl.provider_config_apply_consumption_marker.v1",
        "proposal_id": decision.get("proposal_id"),
        "proposal_ref": decision.get("proposal_ref"),
        "queue_item_id": decision.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "marker_write_status": "atomic_marker_written_apply_executor_handoff_required",
        "marker_ref": str(marker_path),
        "marker_digest_sha256": marker["marker_digest_sha256"],
        "marker": marker,
        "consumer_record": consumer_record,
        "consumer_record_ref": consumer_record.get("consumer_record_ref") if consumer_record else None,
        "consumer_record_digest_valid": consumer_digest_valid,
        "selected_decision_id": selected_decision_id,
        "decision_preflight": decision,
        "idempotency_marker_written": True,
        "marker_directory_created": marker_directory_created,
        "approval_consumed": False,
        "decision_consumed": True,
        "decision_consumer_record_written": True,
        "consumer_record_mutated": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "apply_execution_allowed": False,
        "execution_enabled": False,
        "files_modified": True,
        "write_audit_id": event["event_id"],
        "next_action": "run_live_apply_executor_only_after_gate_and_rollback_preconditions",
    }


def format_provider_config_apply_atomic_marker(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Provider Config Apply Atomic Marker",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- marker_write_status: {payload.get('marker_write_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- consumer_record_ref: {payload.get('consumer_record_ref')}",
        f"- marker_ref: {payload.get('marker_ref')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def load_provider_config_apply_atomic_marker(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
) -> dict[str, Any] | None:
    path = _config_apply_marker_path(vault_root, gate_approval_id)
    if not path.exists():
        return None
    data = _read_json(path, {})
    data["marker_ref"] = str(path)
    return data


def _provider_config_apply_result_record_path(vault_root: str | Path, gate_approval_id: str) -> Path:
    return _config_apply_result_path(vault_root, gate_approval_id)


def _replace_file_text(path: Path, text: str) -> None:
    tmp_path = path.with_name(f"{path.name}.rpgl-{uuid.uuid4().hex}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _provider_config_apply_allowed_target_path(path: str | None) -> bool:
    return str(path or "") in {
        "runtime/hermes/model_config.yaml",
        "runtime/openclaw/model_config.yaml",
        "runtime/setup_state.json",
    }


def _provider_config_apply_current_target_value(vault_root: str | Path, target: dict[str, Any]) -> Any:
    root = Path(vault_root)
    change_type = str(target.get("change_type") or "")
    if change_type == "runtime_primary_model_update":
        runtime = str(target.get("runtime") or "")
        return load_runtime_model_config(runtime, root).primary.model_id
    if change_type == "setup_openai_default_model_update":
        setup_state, _error = _read_optional_json(root / SETUP_STATE_RELATIVE_PATH)
        providers = setup_state.get("providers", {}) if isinstance(setup_state.get("providers"), dict) else {}
        openai = providers.get("openai", {}) if isinstance(providers.get("openai"), dict) else {}
        return openai.get("default_model")
    return None


def _write_runtime_primary_model_id(vault_root: str | Path, target: dict[str, Any], value: Any) -> None:
    root = Path(vault_root)
    relative_path = str(target.get("path") or "")
    path = root / relative_path
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    in_primary = False
    primary_indent: int | None = None
    replaced = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if stripped == "primary:":
            in_primary = True
            primary_indent = indent
            continue
        if in_primary and primary_indent is not None and indent <= primary_indent:
            break
        if in_primary and stripped.startswith("model_id:"):
            newline = "\n" if line.endswith("\n") else ""
            lines[index] = f"{line[:indent]}model_id: {value}{newline}"
            replaced = True
            break
    if not replaced:
        raise RuntimeProviderGovernanceError(f"could not locate primary.model_id in {relative_path}")
    _replace_file_text(path, "".join(lines))


def _write_setup_openai_default_model(vault_root: str | Path, value: Any) -> None:
    path = Path(vault_root) / SETUP_STATE_RELATIVE_PATH
    data = _read_json(path, {})
    providers = data.setdefault("providers", {})
    if not isinstance(providers, dict):
        raise RuntimeProviderGovernanceError("runtime/setup_state.json providers must be an object")
    openai = providers.setdefault("openai", {})
    if not isinstance(openai, dict):
        raise RuntimeProviderGovernanceError("runtime/setup_state.json providers.openai must be an object")
    openai["default_model"] = value
    _replace_file_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def _provider_config_apply_write_target_value(vault_root: str | Path, target: dict[str, Any], value: Any) -> None:
    change_type = str(target.get("change_type") or "")
    if change_type == "runtime_primary_model_update":
        _write_runtime_primary_model_id(vault_root, target, value)
        return
    if change_type == "setup_openai_default_model_update":
        _write_setup_openai_default_model(vault_root, value)
        return
    raise RuntimeProviderGovernanceError(f"unsupported provider config apply target type: {change_type}")


def _provider_config_apply_target_verified(vault_root: str | Path, target: dict[str, Any], expected_value: Any) -> bool:
    return _provider_config_apply_current_target_value(vault_root, target) == expected_value


def _validate_provider_config_apply_marker_chain(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
    proposal_id: str | None,
    queue_item_id: str | None,
    selected_decision_id: str | None,
    selected_decision_ref: str | None,
    selected_decision_digest: str | None,
    consumer_record: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    marker = load_provider_config_apply_atomic_marker(vault_root, gate_approval_id=gate_approval_id)
    errors: list[str] = []
    if marker is None:
        return None, ["provider_config_apply_idempotency_marker_missing"]
    marker_digest_valid = bool(marker.get("marker_digest_sha256")) and marker.get("marker_digest_sha256") == _marker_digest(marker)
    if marker.get("record_type") != "runtime_provider_config_apply_consumption_marker":
        errors.append("marker_record_type_invalid")
    if marker.get("gate_approval_id") != gate_approval_id:
        errors.append("marker_gate_approval_id_mismatch")
    if marker.get("proposal_id") != proposal_id:
        errors.append("marker_proposal_id_mismatch")
    if marker.get("queue_item_id") != queue_item_id:
        errors.append("marker_queue_item_id_mismatch")
    if marker.get("selected_decision_id") != selected_decision_id:
        errors.append("marker_selected_decision_id_mismatch")
    if marker.get("selected_decision_ref") != selected_decision_ref:
        errors.append("marker_selected_decision_ref_mismatch")
    if marker.get("selected_decision_digest_sha256") != selected_decision_digest:
        errors.append("marker_decision_digest_mismatch")
    if consumer_record is None:
        errors.append("marker_consumer_record_missing")
    else:
        if marker.get("consumer_record_ref") != consumer_record.get("consumer_record_ref"):
            errors.append("marker_consumer_record_ref_mismatch")
        if marker.get("consumer_record_digest_sha256") != consumer_record.get("consumer_record_digest_sha256"):
            errors.append("marker_consumer_digest_mismatch")
    if marker.get("provider_config_mutated") is not False or marker.get("setup_state_mutated") is not False:
        errors.append("marker_mutation_claims_invalid")
    if not marker_digest_valid:
        errors.append("marker_digest_invalid")
    return marker, errors


def write_provider_config_apply_live_executor(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Apply reviewed provider config targets after the RPGL decision/marker chain is complete."""
    root = Path(vault_root)
    source = source_command or "chaseos runtime provider config-apply-executor"
    design = build_provider_config_apply_design(root, proposal_ref, source_command=source)
    validation = validate_provider_config_apply_approval_request(
        root,
        gate_approval_id,
        expected_design=design,
        source_command=source,
        write_audit=False,
    )
    decision_validation = validate_provider_config_apply_decision_records(
        root,
        gate_approval_id=gate_approval_id,
        expected_design=design,
    )
    selected_decision_id = decision_validation.get("selected_decision_id")
    selected_decision_ref = decision_validation.get("selected_decision_ref")
    selected_decision_digest = decision_validation.get("selected_decision_digest_sha256")
    consumer_record = load_provider_config_apply_consumer_record(root, gate_approval_id=gate_approval_id)
    marker, marker_errors = _validate_provider_config_apply_marker_chain(
        root,
        gate_approval_id=gate_approval_id,
        proposal_id=str(design.get("proposal_id") or "") or None,
        queue_item_id=str(design.get("queue_item_id") or "") or None,
        selected_decision_id=str(selected_decision_id or "") or None,
        selected_decision_ref=str(selected_decision_ref or "") or None,
        selected_decision_digest=str(selected_decision_digest or "") or None,
        consumer_record=consumer_record,
    )
    result_path = _provider_config_apply_result_record_path(root, gate_approval_id)
    target_writes = [
        item
        for item in list(design.get("target_writes") or [])
        if item.get("write_enabled_after_approval")
    ]
    blocked_reasons: list[str] = []
    if not validation.get("structurally_valid"):
        blocked_reasons.append("provider_config_apply_approval_artifact_invalid")
    if not validation.get("matches_design"):
        blocked_reasons.append("provider_config_apply_approval_artifact_design_mismatch")
    if decision_validation.get("status") != "approved_decision_record_valid":
        blocked_reasons.append("provider_config_apply_approved_decision_missing_or_invalid")
    if consumer_record is None:
        blocked_reasons.append("provider_config_apply_consumer_record_missing")
    blocked_reasons.extend(marker_errors)
    if result_path.exists():
        blocked_reasons.append("provider_config_apply_result_already_exists")
    if not target_writes:
        blocked_reasons.append("provider_config_apply_no_enabled_target_writes")
    for item in target_writes:
        if not _provider_config_apply_allowed_target_path(item.get("path")):
            blocked_reasons.append(f"provider_config_apply_target_not_allowed:{item.get('path')}")
    rollback_snapshot: list[dict[str, Any]] = []
    for item in target_writes:
        try:
            current = _provider_config_apply_current_target_value(root, item)
        except (ModelConfigError, RuntimeProviderGovernanceError, OSError) as exc:
            blocked_reasons.append(f"provider_config_apply_current_value_unreadable:{item.get('change_id')}:{exc}")
            continue
        if current != item.get("current_value"):
            blocked_reasons.append(f"provider_config_apply_current_value_drift:{item.get('change_id')}")
        rollback_snapshot.append(
            {
                "change_id": item.get("change_id"),
                "path": item.get("path"),
                "field": item.get("field"),
                "restore_value": current,
                "proposed_value": item.get("proposed_value"),
                "capture_status": "captured_before_live_apply",
            }
        )
    blocked_reasons = list(dict.fromkeys(blocked_reasons))
    if blocked_reasons:
        event = append_provider_audit_event(
            root,
            ProviderAuditEvent(
                event_type="provider_config_apply_live_executor_blocked",
                runtime="cli",
                provider_id="openai",
                model=design.get("approval_request_template", {}).get("expected_primary_model"),
                provider_strength="strong",
                task_class="runtime_config_change",
                decision="blocked_live_apply_preconditions_not_ready",
                reason="provider_config_apply_live_executor_preconditions_not_ready",
                queue_item_id=str(design.get("queue_item_id") or "") or None,
                files_modified=False,
                next_action="resolve_provider_config_apply_preconditions_before_live_executor",
                source_command=source,
            ),
        )
        raise RuntimeProviderGovernanceError(
            "provider config apply live executor blocked: "
            + ", ".join(blocked_reasons)
            + f" (audit_id={event['event_id']})"
        )

    append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_live_executor_started",
            runtime="cli",
            provider_id="openai",
            model=design.get("approval_request_template", {}).get("expected_primary_model"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="live_apply_started",
            reason="provider_config_apply_live_executor_started_after_marker_chain",
            queue_item_id=str(design.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action="apply_reviewed_provider_config_targets_and_verify",
            source_command=source,
        ),
    )

    applied_writes: list[dict[str, Any]] = []
    try:
        for item in target_writes:
            _provider_config_apply_write_target_value(root, item, item.get("proposed_value"))
            applied_writes.append(
                {
                    "change_id": item.get("change_id"),
                    "path": item.get("path"),
                    "field": item.get("field"),
                    "before": item.get("current_value"),
                    "after": item.get("proposed_value"),
                    "write_status": "written",
                }
            )
        failed_verifications = [
            str(item.get("change_id"))
            for item in target_writes
            if not _provider_config_apply_target_verified(root, item, item.get("proposed_value"))
        ]
        if failed_verifications:
            for snapshot in reversed(rollback_snapshot):
                target = next(item for item in target_writes if item.get("change_id") == snapshot.get("change_id"))
                _provider_config_apply_write_target_value(root, target, snapshot.get("restore_value"))
            rollback_failed = [
                str(snapshot.get("change_id"))
                for snapshot in rollback_snapshot
                if not _provider_config_apply_target_verified(
                    root,
                    next(item for item in target_writes if item.get("change_id") == snapshot.get("change_id")),
                    snapshot.get("restore_value"),
                )
            ]
            append_provider_audit_event(
                root,
                ProviderAuditEvent(
                    event_type=(
                        "provider_config_apply_rollback_failed"
                        if rollback_failed
                        else "provider_config_apply_rollback_completed"
                    ),
                    runtime="cli",
                    provider_id="openai",
                    model=design.get("approval_request_template", {}).get("expected_primary_model"),
                    provider_strength="strong",
                    task_class="runtime_config_change",
                    decision="rollback_failed" if rollback_failed else "rollback_completed",
                    reason="provider_config_apply_verification_failed",
                    queue_item_id=str(design.get("queue_item_id") or "") or None,
                    files_modified=True,
                    next_action="operator_review_required_after_failed_provider_config_apply",
                    source_command=source,
                ),
            )
            append_provider_audit_event(
                root,
                ProviderAuditEvent(
                    event_type="provider_config_apply_live_executor_failed",
                    runtime="cli",
                    provider_id="openai",
                    model=design.get("approval_request_template", {}).get("expected_primary_model"),
                    provider_strength="strong",
                    task_class="runtime_config_change",
                    decision="verification_failed_after_apply",
                    reason="provider_config_apply_post_apply_verification_failed",
                    queue_item_id=str(design.get("queue_item_id") or "") or None,
                    files_modified=True,
                    next_action="operator_review_required_after_rollback",
                    source_command=source,
                ),
            )
            raise RuntimeProviderGovernanceError(
                "provider config apply verification failed; rollback "
                + ("failed" if rollback_failed else "completed")
                + ": "
                + ", ".join(failed_verifications)
            )
    except Exception:
        if not applied_writes:
            raise
        raise

    result = {
        "record_type": "runtime_provider_config_apply_result",
        "schema_version": SCHEMA_VERSION,
        "result_schema_id": "rpgl.provider_config_apply_result.v1",
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "proposal_id": design.get("proposal_id"),
        "queue_item_id": design.get("queue_item_id"),
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": selected_decision_ref,
        "selected_decision_digest_sha256": selected_decision_digest,
        "consumer_record_ref": consumer_record.get("consumer_record_ref") if consumer_record else None,
        "consumer_record_digest_sha256": consumer_record.get("consumer_record_digest_sha256") if consumer_record else None,
        "marker_ref": marker.get("marker_ref") if marker else None,
        "marker_digest_sha256": marker.get("marker_digest_sha256") if marker else None,
        "apply_result_status": "completed",
        "applied_writes": applied_writes,
        "rollback_snapshot": rollback_snapshot,
        "post_apply_verification_status": "passed",
        "provider_config_mutated": any(item.get("path") != SETUP_STATE_RELATIVE_PATH.as_posix() for item in applied_writes),
        "setup_state_mutated": any(item.get("path") == SETUP_STATE_RELATIVE_PATH.as_posix() for item in applied_writes),
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "completed_at": _utc_now(),
        "source_command": source,
    }
    result["result_ref"] = str(result_path)
    result["result_digest_sha256"] = _marker_digest(result)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with result_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise RuntimeProviderGovernanceError(f"provider config apply result already exists: {result_path}") from exc

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_live_executor_completed",
            runtime="cli",
            provider_id="openai",
            model=design.get("approval_request_template", {}).get("expected_primary_model"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="live_apply_completed",
            reason="provider_config_apply_targets_applied_and_verified",
            queue_item_id=str(design.get("queue_item_id") or "") or None,
            files_modified=True,
            next_action="operator_review_result_record_and_run_config_report",
            source_command=source,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "proposal_id": design.get("proposal_id"),
        "proposal_ref": design.get("proposal_ref"),
        "queue_item_id": design.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "executor_status": "live_apply_completed",
        "execution_enabled": True,
        "apply_execution_allowed": True,
        "approval_consumed": False,
        "decision_consumed": True,
        "decision_consumer_record_written": True,
        "idempotency_marker_written": True,
        "result_record_written": True,
        "result_ref": str(result_path),
        "result_digest_sha256": result["result_digest_sha256"],
        "applied_writes": applied_writes,
        "rollback_snapshot": rollback_snapshot,
        "post_apply_verification_status": "passed",
        "provider_config_mutated": result["provider_config_mutated"],
        "setup_state_mutated": result["setup_state_mutated"],
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": True,
        "write_audit_id": event["event_id"],
        "next_action": "operator_review_result_record_and_run_config_report",
    }


def format_provider_config_apply_live_executor(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Provider Config Apply Live Executor",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- applied_writes: {len(payload.get('applied_writes') or [])}",
        f"- post_apply_verification_status: {payload.get('post_apply_verification_status')}",
        f"- result_ref: {payload.get('result_ref')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- queue_drained: {payload.get('queue_drained')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_atomic_marker_writer_design(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the future provider-config apply atomic marker writer design without writing it."""
    root = Path(vault_root)
    consumer_design = build_provider_config_apply_decision_consumer_design(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command or "chaseos runtime provider config-apply-atomic-marker-writer-design",
    )
    consumption_plan = (
        consumer_design.get("decision_consumption_plan")
        if isinstance(consumer_design.get("decision_consumption_plan"), dict)
        else {}
    )
    marker_plan = (
        consumption_plan.get("future_consumption_marker_plan")
        if isinstance(consumption_plan.get("future_consumption_marker_plan"), dict)
        else {}
    )
    decision_preflight = (
        consumption_plan.get("decision_preflight")
        if isinstance(consumption_plan.get("decision_preflight"), dict)
        else {}
    )
    validation = (
        consumption_plan.get("decision_record_validation")
        if isinstance(consumption_plan.get("decision_record_validation"), dict)
        else {}
    )
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    marker_exists = bool(marker_plan.get("marker_exists") or marker_path.exists())
    marker_directory = (root / CONFIG_APPLY_MARKER_RELATIVE_DIR).resolve()
    plan_status = str(consumption_plan.get("decision_consumption_plan_status") or "unknown")
    consumer_status = str(consumer_design.get("consumer_design_status") or "unknown")
    decision_ready = consumer_status == "ready_for_future_decision_consumer_but_consumer_not_built"
    selected_decision_id = consumption_plan.get("selected_decision_id")

    if marker_exists:
        writer_design_status = "blocked_prior_apply_marker_exists"
        next_action = "operator_must_review_existing_apply_marker_before_any_writer_implementation"
    elif not decision_ready:
        writer_design_status = "blocked_decision_consumer_design_not_ready"
        next_action = str(consumer_design.get("next_action") or "resolve_decision_consumer_design_before_marker_writer")
    else:
        writer_design_status = "ready_for_future_atomic_marker_writer_but_writer_not_built"
        next_action = "implement_marker_writer_only_after_decision_consumer_is_built_and_verified"

    marker_payload_preview = dict(marker_plan.get("payload_preview") or {})
    marker_payload_preview.update(
        {
            "writer_record_schema": "rpgl.provider_config_apply_atomic_marker_writer.v1",
            "writer_status": "future_reserved_by_atomic_create_new_only",
            "decision_consumption_plan_status": plan_status,
            "decision_consumer_design_status": consumer_status,
            "marker_payload_digest_sha256": "<future-marker-payload-digest>",
            "writer_side_effects": {
                "decision_consumed_before_write": True,
                "provider_config_mutated_before_write": False,
                "setup_state_mutated_before_write": False,
                "consumption_marker_written_now": False,
            },
        }
    )
    preconditions = [
        {
            "id": "decision_consumption_plan_ready",
            "passed": plan_status == "ready_for_consumption_design_review_executor_not_built",
            "status": plan_status,
            "critical": True,
            "reason": "future marker writer requires a valid approved immutable decision consumption plan",
        },
        {
            "id": "decision_consumer_design_ready",
            "passed": decision_ready,
            "status": consumer_status,
            "critical": True,
            "reason": "future marker writer requires a ready approval-decision consumer design",
        },
        {
            "id": "single_use_marker_absent",
            "passed": not marker_exists,
            "status": "absent" if not marker_exists else "present",
            "critical": True,
            "marker_path": str(marker_path),
            "reason": "future writer must fail if marker exists",
        },
        {
            "id": "approved_immutable_decision_selected",
            "passed": bool(selected_decision_id),
            "status": str(selected_decision_id or "missing"),
            "critical": True,
            "reason": "future writer must bind one immutable approved decision record",
        },
        {
            "id": "decision_consumer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
            "reason": "marker writer depends on immutable decision consumption",
        },
        {
            "id": "atomic_marker_writer_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
            "reason": "atomic marker writer implementation is not built",
        },
        {
            "id": "live_apply_executor_implemented",
            "passed": False,
            "status": "not_built",
            "critical": True,
            "reason": "live provider config apply executor is not built",
        },
    ]
    blocked_reasons = list(consumption_plan.get("blocked_reasons") or [])
    for reason in [
        "provider_config_apply_atomic_marker_writer_not_implemented",
        "provider_config_apply_decision_consumer_not_implemented",
        "provider_config_apply_live_executor_not_implemented",
    ]:
        if reason not in blocked_reasons:
            blocked_reasons.append(reason)
    if marker_exists and "provider_config_apply_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("provider_config_apply_idempotency_marker_exists")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_atomic_marker_writer_design_requested",
            runtime="cli",
            provider_id="openai",
            model=decision_preflight.get("apply_design", {}).get("approval_request_template", {}).get("expected_primary_model")
            if isinstance(decision_preflight.get("apply_design"), dict)
            else None,
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=writer_design_status,
            reason="provider_config_apply_atomic_marker_writer_design_is_non_mutating",
            queue_item_id=str(consumption_plan.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "marker_writer_schema_id": "rpgl.provider_config_apply_atomic_marker_writer.v1",
        "generated_at": _utc_now(),
        "proposal_id": consumption_plan.get("proposal_id"),
        "proposal_ref": consumption_plan.get("proposal_ref"),
        "queue_item_id": consumption_plan.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "writer_design_status": writer_design_status,
        "writer_status": "not_built",
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "decision_consumer_design": consumer_design,
        "decision_consumption_plan": consumption_plan,
        "decision_record_validation": validation,
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": consumption_plan.get("selected_decision_ref"),
        "idempotency": {
            "marker_directory": str(marker_directory),
            "marker_path": str(marker_path),
            "marker_exists": marker_exists,
            "consumption_marker_written": False,
            "future_marker_write_mode": "atomic_create_new_only",
        },
        "marker_record_template": marker_payload_preview,
        "atomic_write_algorithm": [
            "rerun decision consumption plan and decision preflight immediately before marker write",
            "verify exactly one approved immutable decision record is selected",
            "verify approval request digest and decision digest still match the reviewed records",
            "resolve marker path under runtime/providers/state/provider_config_apply_markers and reject path escape",
            "create only the declared marker parent directory if absent",
            "open marker path with create-new/exclusive semantics and fail if it already exists",
            "write only the sanitized marker JSON payload and flush it before any provider config or setup mutation",
            "do not delete the marker after partial or failed apply execution",
            "require a new approval request and decision for any retry after marker creation",
        ],
        "path_constraints": {
            "marker_directory": str(marker_directory),
            "marker_path": str(marker_path),
            "path_escape_allowed": False,
            "overwrite_allowed": False,
            "delete_on_failure_allowed": False,
            "retry_without_new_approval_allowed": False,
        },
        "future_writer_preconditions": preconditions,
        "failure_handling_policy": [
            "do not delete marker after partial or failed provider config apply",
            "do not retry with the same gate_approval_id after marker creation",
            "preserve rollback snapshot and failure evidence for operator review",
            "require operator review and a new approval request before any retry",
        ],
        "forbidden_marker_fields": [
            "password",
            "api_key",
            "authorization",
            "secret",
            "token",
            "credential",
            "env_value",
            "cookie",
            "session",
            "private_key",
        ],
        "blocked_reasons": blocked_reasons,
        "approval_consumed": False,
        "decision_consumed": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "marker_directory_created": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_atomic_marker_writer_design(payload: dict[str, Any]) -> str:
    idempotency = payload.get("idempotency") if isinstance(payload.get("idempotency"), dict) else {}
    lines = [
        "RPGL Provider Config Apply Atomic Marker Writer Design",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- writer_design_status: {payload.get('writer_design_status')}",
        f"- writer_status: {payload.get('writer_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- marker_path: {idempotency.get('marker_path')}",
        f"- marker_exists: {idempotency.get('marker_exists')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- consumption_marker_written: {payload.get('consumption_marker_written')}",
        f"- marker_directory_created: {payload.get('marker_directory_created')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_provider_config_apply_executor_dry_run_plan(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build the future provider-config apply executor plan without applying it."""
    root = Path(vault_root)
    decision = build_provider_config_apply_decision_preflight(
        root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command,
    )
    design = decision.get("apply_design") if isinstance(decision.get("apply_design"), dict) else {}
    target_writes = list(design.get("target_writes") or [])
    enabled_target_writes = [item for item in target_writes if item.get("write_enabled_after_approval")]
    blocked_target_writes = [item for item in target_writes if not item.get("write_enabled_after_approval")]

    dry_run_write_plan = [
        {
            "change_id": item.get("change_id"),
            "path": item.get("path"),
            "field": item.get("field"),
            "before": item.get("current_value"),
            "after": item.get("proposed_value"),
            "operation": "replace_field_value",
            "write_enabled": False,
            "reason": "dry_run_only_provider_config_apply_executor_not_enabled",
        }
        for item in enabled_target_writes
    ]
    rollback_snapshot = [
        {
            "change_id": item.get("change_id"),
            "path": item.get("path"),
            "field": item.get("field"),
            "restore_value": item.get("current_value"),
            "proposed_value": item.get("proposed_value"),
            "capture_status": "dry_run_snapshot_from_current_apply_design",
        }
        for item in enabled_target_writes
    ]
    marker_path = _config_apply_marker_path(root, gate_approval_id)
    decision_status = str(decision.get("decision_consumption_status") or "unknown")
    approval_ready = decision_status == "approved_decision_record_valid_but_executor_not_built"
    if approval_ready:
        dry_run_status = "ready_for_dry_run_review_live_apply_not_enabled"
        next_action = "operator_reviews_dry_run_plan_before_any_live_apply_executor_is_built"
    else:
        dry_run_status = f"blocked_{decision_status}"
        next_action = str(decision.get("next_action") or "resolve_decision_preflight_before_executor_dry_run")

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_config_apply_executor_dry_run_requested",
            runtime="cli",
            provider_id="openai",
            model=design.get("approval_request_template", {}).get("expected_primary_model"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=dry_run_status,
            reason="provider_config_apply_executor_plan_is_dry_run_only",
            queue_item_id=str(design.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action=next_action,
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "approval_schema_id": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
        "proposal_id": decision.get("proposal_id"),
        "proposal_ref": decision.get("proposal_ref"),
        "queue_item_id": decision.get("queue_item_id"),
        "gate_approval_id": gate_approval_id,
        "dry_run": True,
        "dry_run_status": dry_run_status,
        "executor_status": "dry_run_plan_only",
        "executor_implemented": False,
        "live_apply_supported": False,
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "idempotency_marker_written": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "decision_preflight": decision,
        "approval_validation": decision.get("approval_validation"),
        "idempotency_marker_plan": {
            "marker_path": str(marker_path),
            "marker_exists": marker_path.exists(),
            "write_enabled": False,
            "would_write_before_config_mutation": True,
            "payload_preview": {
                "gate_approval_id": gate_approval_id,
                "proposal_id": decision.get("proposal_id"),
                "queue_item_id": decision.get("queue_item_id"),
                "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
                "status": "would_mark_apply_started_before_live_mutation",
            },
        },
        "dry_run_write_plan": dry_run_write_plan,
        "blocked_target_writes": blocked_target_writes,
        "rollback_snapshot": rollback_snapshot,
        "rollback_plan": design.get("rollback_plan"),
        "post_apply_verification_plan": design.get("post_apply_verification"),
        "stop_conditions": [
            "approval artifact is not approved",
            "approval artifact fails structural validation or no longer matches design",
            "idempotency marker already exists",
            "proposal current-value drift is detected",
            "target path is not in the reviewed provider config/setup allowlist",
            "rollback snapshot cannot be captured",
            "post-apply verification plan is missing",
            "operator has not explicitly approved live apply executor implementation",
        ],
        "blocked_reasons": list(decision.get("blocked_reasons") or [])
        + ["provider_config_apply_live_executor_not_implemented"],
        "feature_completion_tracker": {
            "rpgl_status": "PARTIAL / IMPLEMENTED FOUNDATION",
            "can_call_feature_complete": False,
            "completed": [
                "provider_strength_classification",
                "task_class_capability_gate",
                "weak_fallback_denial_for_high_authority_work",
                "queue_on_denial",
                "fallback_timeout_decision_records",
                "primary_cooldown_recovery_state",
                "provider_status_cli",
                "provider_config_reconciliation",
                "provider_config_proposal_queue_request",
                "provider_config_apply_preflight",
                "provider_config_apply_design",
                "provider_config_apply_approval_request_artifact",
                "immutable_operator_approval_decision_record",
                "immutable_approval_decision_record_validation",
                "provider_config_apply_decision_preflight",
                "provider_config_apply_decision_consumption_plan",
                "provider_config_apply_decision_consumer_design",
                "provider_config_apply_decision_consumer_preflight",
                "provider_config_apply_decision_consumer_implementation_plan",
                "provider_config_apply_decision_consumer_writer_dry_run",
                "provider_config_apply_decision_consumer_record_writer",
                "provider_config_apply_atomic_marker_writer_design",
                "provider_config_apply_atomic_marker_writer",
                "provider_config_apply_executor_dry_run_plan",
                "live_provider_config_apply_executor",
                "rollback_execution_after_failed_apply_verification",
            ],
            "remaining_before_complete": [
                "live_provider_probe_executor",
                "live_ollama_first_token_no_chunk_timeout_integration",
                "Hermes_OpenClaw_consumption_of_RPGL_route_decisions_where_not_already_integrated",
                "Discord_read_only_or_dry_run_surface_if_operator_keeps_it_in_scope",
            ],
            "done_when": [
                "approved apply can run through a tested Gate-governed executor",
                "idempotency marker prevents duplicate apply",
                "rollback and post-apply verification are tested",
                "Hermes and OpenClaw consume shared RPGL decisions rather than local fallback policy",
                "live provider and local fallback timeout behavior is verified or explicitly deferred",
            ],
        },
        "next_action": next_action,
        "audit_id": event["event_id"],
    }


def format_provider_config_apply_executor_dry_run_plan(payload: dict[str, Any]) -> str:
    tracker = payload.get("feature_completion_tracker") if isinstance(payload.get("feature_completion_tracker"), dict) else {}
    lines = [
        "RPGL Provider Config Apply Executor Dry-Run Plan",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- dry_run_status: {payload.get('dry_run_status')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- live_apply_supported: {payload.get('live_apply_supported')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- planned_target_writes: {len(payload.get('dry_run_write_plan') or [])}",
        f"- rollback_snapshots: {len(payload.get('rollback_snapshot') or [])}",
        f"- rpgl_can_call_complete: {tracker.get('can_call_feature_complete')}",
        f"- remaining_before_complete: {tracker.get('remaining_before_complete')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def load_provider_config_apply_decision_records(
    vault_root: str | Path,
    *,
    gate_approval_id: str | None = None,
) -> list[dict[str, Any]]:
    base = config_apply_decision_records_dir(vault_root)
    if not base.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(base.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeProviderGovernanceError(f"Invalid RPGL provider config apply decision JSON at {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeProviderGovernanceError(f"RPGL provider config apply decision JSON at {path} must be an object")
        data["decision_ref"] = str(path)
        if gate_approval_id and data.get("gate_approval_id") != gate_approval_id:
            continue
        records.append(data)
    return records


def validate_provider_config_apply_decision_records(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
    expected_design: dict[str, Any],
) -> dict[str, Any]:
    """Validate immutable approval decision records without consuming them."""
    records = load_provider_config_apply_decision_records(vault_root, gate_approval_id=gate_approval_id)
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_schema_id": "rpgl.provider_config_apply_decision.v1",
        "gate_approval_id": gate_approval_id,
        "records_found": len(records),
        "record_refs": [record.get("decision_ref") for record in records],
        "decision_ids": [record.get("decision_id") for record in records],
        "status": "missing",
        "decision": None,
        "selected_decision_id": None,
        "selected_decision_ref": None,
        "structurally_valid": False,
        "decision_digest_valid": False,
        "decision_record_consumable": False,
        "future_consumption_supported": False,
        "decision_consumed": False,
        "approval_artifact_mutated": False,
        "idempotency_marker_written": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "errors": [],
        "warnings": [],
    }
    if not records:
        summary["errors"].append("immutable_decision_record_missing")
        return summary
    if len(records) > 1:
        summary["status"] = "multiple"
        summary["errors"].append("multiple_immutable_decision_records_for_gate_approval_id")
        return summary

    record = records[0]
    errors: list[str] = []
    expected_proposal_id = expected_design.get("proposal_id")
    expected_queue_item_id = expected_design.get("queue_item_id")
    expected_digest = _decision_digest(record)
    recorded_digest = str(record.get("decision_digest_sha256") or "")
    decision = str(record.get("decision") or "")

    checks = {
        "record_type": record.get("record_type") == "runtime_provider_config_apply_approval_decision",
        "schema_version": record.get("schema_version") == SCHEMA_VERSION,
        "decision_schema_id": record.get("decision_schema_id") == "rpgl.provider_config_apply_decision.v1",
        "operation": record.get("operation") == RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "gate_approval_id": record.get("gate_approval_id") == gate_approval_id,
        "proposal_id": record.get("proposal_id") == expected_proposal_id,
        "queue_item_id": record.get("queue_item_id") == expected_queue_item_id,
        "decision": decision in CONFIG_APPLY_APPROVAL_DECISIONS,
        "decision_status": record.get("decision_status") == "recorded",
        "decision_record_written": record.get("decision_record_written") is True,
        "immutable": record.get("immutable") is True,
        "append_only": record.get("append_only") is True,
        "execution_disabled": record.get("execution_enabled") is False and record.get("apply_execution_allowed") is False,
        "no_prior_consumption": record.get("decision_consumed") is False and record.get("approval_consumed") is False,
        "no_mutation_claims": (
            record.get("provider_config_mutated") is False
            and record.get("setup_state_mutated") is False
            and record.get("provider_state_mutated") is False
            and record.get("idempotency_marker_written") is False
            and record.get("queue_drained") is False
            and record.get("gateway_mutated") is False
            and record.get("live_network_call_attempted") is False
        ),
        "decision_digest_sha256": bool(recorded_digest) and recorded_digest == expected_digest,
    }
    for check_id, passed in checks.items():
        if not passed:
            errors.append(f"decision_record_{check_id}_invalid")

    structurally_valid = not errors
    if not structurally_valid:
        status = "invalid"
    elif decision == "approved":
        status = "approved_decision_record_valid"
    else:
        status = "denied_decision_record_valid"

    summary.update(
        {
            "status": status,
            "decision": decision if decision else None,
            "selected_decision_id": record.get("decision_id"),
            "selected_decision_ref": record.get("decision_ref"),
            "selected_decision_digest_sha256": recorded_digest or None,
            "expected_decision_digest_sha256": expected_digest,
            "structurally_valid": structurally_valid,
            "decision_digest_valid": bool(recorded_digest) and recorded_digest == expected_digest,
            "decision_record_consumable": structurally_valid and decision == "approved",
            "future_consumption_supported": False,
            "checks": checks,
            "errors": errors,
            "warnings": [],
        }
    )
    return summary


def build_provider_config_apply_approval_decision_record(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    decision: str,
    decided_by: str,
    reason: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Preview an immutable approval decision record without writing it."""
    decision_text = str(decision or "").strip().lower()
    if decision_text not in CONFIG_APPLY_APPROVAL_DECISIONS:
        raise RuntimeProviderGovernanceError(
            f"provider config apply approval decision must be one of {', '.join(CONFIG_APPLY_APPROVAL_DECISIONS)}"
        )
    dry_run = build_provider_config_apply_executor_dry_run_plan(
        vault_root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        source_command=source_command,
    )
    validation = dry_run.get("approval_validation") if isinstance(dry_run.get("approval_validation"), dict) else {}
    existing_decisions = load_provider_config_apply_decision_records(vault_root, gate_approval_id=gate_approval_id)
    marker_plan = dry_run.get("idempotency_marker_plan") if isinstance(dry_run.get("idempotency_marker_plan"), dict) else {}
    validation_errors = list(validation.get("errors") or [])
    blocked_reasons: list[str] = []
    if validation_errors:
        blocked_reasons.append("approval_artifact_invalid")
    if existing_decisions:
        blocked_reasons.append("immutable_decision_already_exists")
    if marker_plan.get("marker_exists"):
        blocked_reasons.append("idempotency_marker_already_exists")
    writable = not blocked_reasons
    decision_id = _new_provider_config_apply_decision_id()
    record = {
        "record_type": "runtime_provider_config_apply_approval_decision",
        "schema_version": SCHEMA_VERSION,
        "decision_schema_id": "rpgl.provider_config_apply_decision.v1",
        "operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        "decision_id": decision_id,
        "gate_approval_id": gate_approval_id,
        "proposal_id": dry_run.get("proposal_id"),
        "queue_item_id": dry_run.get("queue_item_id"),
        "decision": decision_text,
        "decision_status": "preview",
        "decision_record_writable": writable,
        "decision_record_written": False,
        "decided_by": str(decided_by or "operator"),
        "decided_at": _utc_now(),
        "reason": str(reason or ""),
        "approval_ref": validation.get("approval_ref"),
        "approval_artifact_status_at_decision": validation.get("approval_status"),
        "approval_structurally_valid": bool(validation.get("structurally_valid")),
        "approval_matches_design": bool(validation.get("matches_design")),
        "approval_request_digest_sha256": (
            load_provider_config_apply_approval_request(vault_root, gate_approval_id).get("request_digest_sha256")
        ),
        "dry_run_status_at_decision": dry_run.get("dry_run_status"),
        "dry_run_audit_id": dry_run.get("audit_id"),
        "target_paths": [item.get("path") for item in dry_run.get("dry_run_write_plan", []) if item.get("path")],
        "rollback_snapshot_count": len(dry_run.get("rollback_snapshot") or []),
        "idempotency_marker_path": marker_plan.get("marker_path"),
        "idempotency_marker_exists": bool(marker_plan.get("marker_exists")),
        "existing_decision_count": len(existing_decisions),
        "existing_decision_ids": [item.get("decision_id") for item in existing_decisions],
        "blocked_reasons": blocked_reasons,
        "decision_effect": (
            "records_operator_approval_for_one_future_executor_attempt_only"
            if decision_text == "approved"
            else "records_operator_denial_and_blocks_future_apply_until_new_request"
        ),
        "immutable": True,
        "append_only": True,
        "execution_enabled": False,
        "apply_execution_allowed": False,
        "approval_consumed": False,
        "decision_consumed": False,
        "approval_artifact_mutated": False,
        "idempotency_marker_written": False,
        "provider_config_mutated": False,
        "setup_state_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "source_command": source_command,
    }
    record["decision_digest_sha256"] = _decision_digest(record)
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_config_apply_approval_decision_previewed",
            runtime="cli",
            provider_id="openai",
            model="gpt-5.5",
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=f"approval_decision_preview_{decision_text}",
            reason="provider_config_apply_approval_decision_record_previewed_without_apply",
            queue_item_id=str(record.get("queue_item_id") or "") or None,
            files_modified=False,
            next_action="write_immutable_decision_record_or_stop_before_live_apply",
            source_command=source_command,
        ),
    )
    record["audit_id"] = event["event_id"]
    return record


def write_provider_config_apply_approval_decision_record(
    vault_root: str | Path,
    proposal_ref: str,
    *,
    gate_approval_id: str,
    decision: str,
    decided_by: str,
    reason: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist an immutable approval decision record without consuming it."""
    record = build_provider_config_apply_approval_decision_record(
        vault_root,
        proposal_ref,
        gate_approval_id=gate_approval_id,
        decision=decision,
        decided_by=decided_by,
        reason=reason,
        source_command=source_command,
    )
    if not record.get("decision_record_writable"):
        raise RuntimeProviderGovernanceError(
            "provider config apply approval decision is not writable: "
            + ", ".join(record.get("blocked_reasons") or ["unknown"])
        )
    path = _config_apply_decision_record_path(vault_root, str(record["decision_id"]))
    if path.exists():
        raise RuntimeProviderGovernanceError(f"RPGL provider config apply decision already exists: {record['decision_id']}")
    written = dict(record)
    written["decision_status"] = "recorded"
    written["decision_record_written"] = True
    written["files_modified"] = True
    written["decision_ref"] = str(path)
    written["decision_digest_sha256"] = _decision_digest(written)
    _write_json(path, written)
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_config_apply_approval_decision_created",
            runtime="cli",
            provider_id="openai",
            model="gpt-5.5",
            provider_strength="strong",
            task_class="runtime_config_change",
            decision=f"approval_decision_recorded_{written.get('decision')}",
            reason="immutable_provider_config_apply_approval_decision_record_written_without_apply",
            queue_item_id=str(written.get("queue_item_id") or "") or None,
            files_modified=True,
            next_action="future_executor_must_validate_and_consume_decision_record_before_any_apply",
            source_command=source_command,
        ),
    )
    written["write_audit_id"] = event["event_id"]
    _write_json(path, written)
    return written


def format_provider_config_apply_approval_decision_record(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Provider Config Apply Approval Decision Record",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- decision_id: {payload.get('decision_id')}",
        f"- decision: {payload.get('decision')}",
        f"- decision_status: {payload.get('decision_status')}",
        f"- decision_record_writable: {payload.get('decision_record_writable')}",
        f"- decision_record_written: {payload.get('decision_record_written')}",
        f"- approval_artifact_status_at_decision: {payload.get('approval_artifact_status_at_decision')}",
        f"- existing_decision_count: {payload.get('existing_decision_count')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- approval_consumed: {payload.get('approval_consumed')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
        f"- blocked_reasons: {payload.get('blocked_reasons')}",
    ]
    return "\n".join(lines)


def format_provider_config_apply_approval_request(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Provider Config Apply Approval Request",
        f"- proposal_id: {payload.get('proposal_id')}",
        f"- queue_item_id: {payload.get('queue_item_id')}",
        f"- approval_schema_id: {payload.get('approval_schema_id')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- status: {payload.get('status')}",
        f"- approval_request_written: {payload.get('approval_request_written')}",
        f"- approval_ref: {payload.get('approval_ref')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- apply_execution_allowed: {payload.get('apply_execution_allowed')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- setup_state_mutated: {payload.get('setup_state_mutated')}",
    ]
    validation = payload.get("approval_validation")
    if isinstance(validation, dict):
        lines.extend(
            [
                "",
                "Validation:",
                f"- structurally_valid: {validation.get('structurally_valid')}",
                f"- matches_design: {validation.get('matches_design')}",
                f"- apply_execution_allowed: {validation.get('apply_execution_allowed')}",
                f"- errors: {validation.get('errors')}",
            ]
        )
    return "\n".join(lines)


def build_provider_probe_plan(
    vault_root: str | Path,
    record: ProviderStatusRecord,
    *,
    probe_mode: str = "config",
) -> dict[str, Any]:
    """Build a secret-safe provider probe plan.

    `network-dry-run` performs no network I/O and reads no secret values. It
    only reports setup metadata that is already exposed by the provider setup
    registry.
    """
    del vault_root
    mode = normalize_probe_mode(probe_mode)
    setup = _provider_setup_by_id().get(record.provider_id, {})
    configured = setup.get("configured") if setup else None
    valid = setup.get("valid") if setup else None
    secret_reference_present = setup.get("secret_reference_present") if setup else None
    missing = list(setup.get("missing") or []) if setup else []
    endpoint_kind = _endpoint_kind_for_provider(record.provider_id)

    if mode == "config":
        return ProviderProbePlan(
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            probe_mode=mode,
            configured=configured,
            valid_setup_state=valid,
            secret_reference_present=secret_reference_present,
            missing_setup_checks=missing,
            status="configuration_checked",
            reason="local_model_config_record_present" if record.model else "local_model_config_record_missing_model",
            endpoint_kind=endpoint_kind,
        ).to_dict()

    if mode == "live-preflight":
        return ProviderProbePlan(
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            probe_mode=mode,
            configured=configured,
            valid_setup_state=valid,
            secret_reference_present=secret_reference_present,
            missing_setup_checks=missing,
            live_network_call_attempted=False,
            secret_value_read=False,
            canonical_files_mutated=False,
            provider_state_mutated=False,
            status="preflight_only",
            reason="live_provider_probe_requires_gate_approval",
            endpoint_kind=endpoint_kind,
        ).to_dict()

    reason = "live_network_probe_not_attempted_by_policy"
    if record.provider_id == "local_oss":
        reason = "local_network_probe_requires_explicit_ollama_endpoint_policy"
    elif not record.model:
        reason = "model_missing_for_network_probe"
    elif configured is False or valid is False:
        reason = "provider_setup_not_valid_for_network_probe"
    return ProviderProbePlan(
        provider_id=record.provider_id,
        provider_name=record.provider_name,
        model=record.model,
        probe_mode=mode,
        configured=configured,
        valid_setup_state=valid,
        secret_reference_present=secret_reference_present,
        missing_setup_checks=missing,
        live_network_call_attempted=False,
        secret_value_read=False,
        canonical_files_mutated=False,
        provider_state_mutated=False,
        status="dry_run_only",
        reason=reason,
        endpoint_kind=endpoint_kind,
    ).to_dict()


def build_live_provider_probe_preflight(
    vault_root: str | Path,
    record: ProviderStatusRecord,
    *,
    runtime: str = "unknown",
) -> dict[str, Any]:
    """Build a denied-by-default contract for future live provider probes.

    This function intentionally performs no provider I/O and reads no secret
    values. It only assembles the approval and safety checks required before a
    future live probe implementation may be added.
    """
    setup = _provider_setup_by_id().get(record.provider_id, {})
    configured = setup.get("configured") if setup else None
    valid = setup.get("valid") if setup else None
    secret_reference_present = setup.get("secret_reference_present") if setup else None
    missing = list(setup.get("missing") or []) if setup else []
    external_api_id = _external_api_for_provider(record.provider_id)
    gate_allowed, gate_reason = check_runtime_operation(
        LIVE_PROVIDER_PROBE_GATE_OPERATION,
        external_api=external_api_id,
        write_targets=[
            str(STATE_RELATIVE_PATH).replace("\\", "/"),
            str(AUDIT_RELATIVE_PATH).replace("\\", "/"),
        ],
    )
    approval_schema = get_runtime_operation_approval_schema(
        LIVE_PROVIDER_PROBE_GATE_OPERATION,
        provider_id=record.provider_id,
        model=record.model,
        runtime=record.runtime or runtime,
        external_api=external_api_id,
        source_command="chaseos runtime provider probe --probe-mode live-preflight",
    ) or {}
    denial_reason = "live_provider_probe_requires_gate_approval"
    if not record.model:
        denial_reason = "model_missing_for_live_provider_probe"
    elif configured is False or valid is False:
        denial_reason = "provider_setup_not_valid_for_live_provider_probe"
    return ProviderLiveProbePreflight(
        provider_id=record.provider_id,
        provider_name=record.provider_name,
        model=record.model,
        runtime=record.runtime or runtime,
        gate_policy_allowed=gate_allowed,
        gate_policy_reason=gate_reason,
        external_api_id=external_api_id,
        denial_reason=denial_reason,
        approval_request_template=dict(approval_schema.get("approval_request_template") or {}),
        approval_schema=approval_schema,
        endpoint_kind=_endpoint_kind_for_provider(record.provider_id),
        configured=configured,
        valid_setup_state=valid,
        secret_reference_present=secret_reference_present,
        missing_setup_checks=missing,
    ).to_dict()


def save_provider_record(vault_root: str | Path, record: ProviderStatusRecord) -> None:
    records = load_provider_records(vault_root)
    record.active_for_task_classes = allowed_task_classes_for_strength(record.strength)
    record.denied_task_classes = denied_task_classes_for_strength(record.strength)
    record.sticky_for_development = False
    records[record.provider_key] = record
    _save_provider_records(vault_root, records)


def _redact_config_proof_value(value: Any) -> Any:
    """Return a metadata-safe value for config/proof diffs."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return [_redact_config_proof_value(item) for item in value]
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in ("secret", "token", "password", "credential", "api_key", "apikey")):
                redacted[str(key)] = "[secret-reference-metadata-only]"
            else:
                redacted[str(key)] = _redact_config_proof_value(child)
        return redacted
    text = str(value)
    if re.search(r"(?i)(sk-[a-z0-9][a-z0-9._-]{8,}|secret|token|password|credential|api[_-]?key)", text):
        return "[redacted-sensitive-config-value]"
    return text


def _redacted_change_diff(proposed_changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diff: list[dict[str, Any]] = []
    for change in proposed_changes:
        diff.append(
            {
                "change_id": change.get("change_id"),
                "change_type": change.get("change_type"),
                "target_file": change.get("target_file"),
                "current_value_redacted": _redact_config_proof_value(change.get("current_value")),
                "proposed_value_redacted": _redact_config_proof_value(change.get("proposed_value")),
                "write_enabled_after_approval": bool(change.get("write_enabled_after_approval", True)),
            }
        )
    return diff


def build_credential_config_mutation_governance_lane_proof(
    vault_root: str | Path,
    *,
    target_model: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build a metadata-only proof packet for the credential/config mutation lane.

    This composes existing RPGL, Studio-readiness, and bounded config-store
    evidence. It proves the lane distinction without writing config, reading raw
    secrets, consuming approval, calling providers, or mutating protected files.
    """

    root = Path(vault_root)
    target_profile_plan = build_provider_target_profile_plan(
        root,
        target_model=target_model,
        source_command=source_command or "credential-config-governance-lane-proof",
    )
    config_plan = build_provider_config_change_plan(
        root,
        source_command=source_command or "credential-config-governance-lane-proof",
    )

    from runtime.config.settings_summary import build_settings_summary
    from runtime.config.store import validate_config_payload
    from runtime.studio.provider_readiness import build_studio_provider_readiness

    settings_summary = build_settings_summary(vault_root=root)
    provider_readiness = build_studio_provider_readiness(root)
    denied_payload_validation = validate_config_payload(
        {
            "default_provider": "openai",
            "api_key": "OPENAI_API_KEY_REDACTED_PROOF_PLACEHOLDER",
            "scaffold_defaults": {"workspace_root": "../outside-vault"},
        },
        config_path=root / ".chaseos" / "config.yaml",
    )
    gate_allowed, gate_reason = check_runtime_operation(
        RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        write_targets=[str(CHASEOS_CONFIG_RELATIVE_PATH), str(PROVIDER_TARGET_PROFILE_RELATIVE_PATH)],
    )

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="credential_config_mutation_governance_lane_proof_requested",
            runtime="cli",
            provider_id=str(target_profile_plan.get("candidate_provider_id") or "provider_governance"),
            provider_name="Runtime Provider Governance Layer",
            model=str(target_profile_plan.get("desired_default_primary_model") or target_model or "unspecified"),
            provider_strength="strong",
            task_class="runtime_config_change",
            decision="credential_config_mutation_lane_proof_built",
            reason="studio_chat_settings_provider_config_mutation_contract_requested",
            files_modified=False,
            next_action="operator_review_approval_packet_before_any_config_or_credential_mutation",
            source_command=source_command,
        ),
    )

    redacted_diff = _redacted_change_diff(list(config_plan.get("proposed_changes") or []))
    return {
        "record_type": "credential_config_mutation_governance_lane_proof",
        "schema_id": "rpgl.credential_config_mutation_governance_lane_proof.v1",
        "status": "proof_ready_no_mutation",
        "generated_at": _utc_now(),
        "vault_root": str(root),
        "read_only": True,
        "files_modified": False,
        "raw_secret_values_included": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "approval_consumed": False,
        "provider_config_mutated": False,
        "target_profile_mutated": False,
        "runtime_config_mutated": False,
        "protected_config_mutated": False,
        "canonical_writeback_allowed": False,
        "minimum_proof": {
            "approval_packet": {
                "available": True,
                "target_profile_request_surface": "chaseos runtime provider target-profile-plan <model> --write-approval-request --requested-by <operator> --json",
                "config_change_request_surface": "chaseos runtime provider config-plan --write-approval-request --requested-by <operator> --json",
                "config_apply_operation": RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
                "approval_required": True,
                "gate_allows_without_approval": gate_allowed,
                "gate_reason": gate_reason,
            },
            "redacted_before_after_diff": redacted_diff,
            "secret_reference_only": {
                "secret_reference_metadata_only": bool(
                    provider_readiness.get("credential_posture", {}).get("secret_reference_metadata_only")
                ),
                "raw_credentials_included": bool(provider_readiness.get("credential_posture", {}).get("raw_credentials_included")),
                "raw_credential_values_displayed": bool(
                    provider_readiness.get("credential_posture", {}).get("raw_credential_values_displayed")
                ),
                "settings_secrets_allowed_in_config": bool(
                    settings_summary.get("governance", {}).get("secrets_allowed_in_config")
                ),
            },
            "protected_config_denial": {
                "denied_payload_ok": bool(denied_payload_validation.get("ok")),
                "denied_payload_posture": denied_payload_validation.get("posture"),
                "denied_issue_codes": [issue.get("code") for issue in denied_payload_validation.get("issues") or []],
                "mutates_config": bool(denied_payload_validation.get("mutates_config")),
            },
            "provider_readiness_refresh": {
                "surface": provider_readiness.get("surface"),
                "read_only": bool(provider_readiness.get("read_only")),
                "readiness_status": provider_readiness.get("summary", {}).get("readiness_status"),
                "active_provider_id": provider_readiness.get("summary", {}).get("active_provider_id"),
                "secret_values_visible": bool(provider_readiness.get("authority", {}).get("secret_values_visible")),
                "writes_provider_config": bool(provider_readiness.get("authority", {}).get("writes_provider_config")),
                "writes_target_profile": bool(provider_readiness.get("authority", {}).get("writes_target_profile")),
            },
            "audit_path": {
                "audit_ref": str(audit_path(root)),
                "audit_event_id": event.get("event_id"),
                "audit_event_type": event.get("event_type"),
            },
        },
        "lane_distinctions": {
            "redacted_display": "Studio/Chat may display non-secret posture, provider ids, model ids, readiness labels, and redacted diffs only.",
            "secret_reference_configuration": "Credential material is represented by env/secret-reference metadata; raw secret values are not displayable or storable in .chaseos/config.yaml.",
            "provider_target_profile_changes": "Target-profile changes produce proposal/queue artifacts first and do not write runtime/providers/provider_target_profile.json in this proof lane.",
            "runtime_config_mutation": "Runtime/provider config writes require separate Gate approval, decision, consumption, marker, executor, rollback, and audit evidence.",
        },
        "evidence_refs": {
            "settings_config_path": settings_summary.get("config", {}).get("config_path"),
            "provider_target_profile_ref": str(root / PROVIDER_TARGET_PROFILE_RELATIVE_PATH),
            "provider_config_proposals_dir": str(config_proposals_dir(root)),
            "target_profile_proposals_dir": str(target_profile_proposals_dir(root)),
            "config_apply_approvals_dir": str(config_apply_approval_artifacts_dir(root)),
            "provider_readiness_target_profile_ref": provider_readiness.get("evidence_refs", {}).get("target_profile_ref"),
            "provider_audit_jsonl": str(audit_path(root)),
        },
        "source_summaries": {
            "target_profile_plan_status": target_profile_plan.get("plan_status"),
            "target_profile_change_needed": bool(target_profile_plan.get("profile_change_needed")),
            "config_plan_status": config_plan.get("status"),
            "config_change_count": len(config_plan.get("proposed_changes") or []),
            "settings_posture": settings_summary.get("settings_posture"),
        },
    }


def append_provider_audit_event(
    vault_root: str | Path,
    event: ProviderAuditEvent | dict[str, Any],
) -> dict[str, Any]:
    payload = event.to_dict() if isinstance(event, ProviderAuditEvent) else ProviderAuditEvent(**event).to_dict()
    path = audit_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return payload


def load_provider_audit_events(vault_root: str | Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    path = audit_path(vault_root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise RuntimeProviderGovernanceError(f"Invalid RPGL audit JSONL at {path}:{line_number}: {exc}") from exc
            if isinstance(data, dict):
                events.append(data)
    events.sort(key=lambda item: str(item.get("timestamp") or ""))
    if limit is not None and limit >= 0:
        return events[-int(limit):]
    return events


def _load_queue_payload(vault_root: str | Path) -> dict[str, Any]:
    return _read_json(
        _queue_path(vault_root),
        {"schema_version": SCHEMA_VERSION, "updated_at": None, "items": []},
    )


def load_queue_items(vault_root: str | Path) -> list[ProviderQueueItem]:
    payload = _load_queue_payload(vault_root)
    items = payload.get("items") or []
    if not isinstance(items, list):
        raise RuntimeProviderGovernanceError("RPGL queue 'items' must be an array")
    return [ProviderQueueItem.from_dict(item) for item in items if isinstance(item, dict)]


def _save_queue_items(vault_root: str | Path, items: list[ProviderQueueItem]) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": _utc_now(),
        "items": [item.to_dict() for item in items],
    }
    _write_json(_queue_path(vault_root), payload)


def queue_summary(vault_root: str | Path) -> dict[str, Any]:
    items = load_queue_items(vault_root)
    open_statuses = {"queued", "waiting_for_primary", "ready_for_retry", "needs_operator_approval"}
    high_waiting = [
        item
        for item in items
        if item.task_class in HIGH_AUTHORITY_TASK_CLASSES and item.retry_status in open_statuses
    ]
    safe_fallback = [
        item
        for item in items
        if item.task_class in WEAK_SAFE_TASK_CLASSES and item.retry_status in open_statuses
    ]
    failed = [item for item in items if item.retry_status == "failed"]
    needs_approval = [item for item in items if item.retry_status == "needs_operator_approval"]
    next_retry_candidates = [item.cooldown_until for item in items if item.cooldown_until]
    next_retry_candidates = sorted(value for value in next_retry_candidates if value)
    return {
        "queued_task_count": len([item for item in items if item.retry_status in open_statuses]),
        "high_complexity_waiting_for_primary": len(high_waiting),
        "safe_fallback_tasks": len(safe_fallback),
        "failed_retry_packages": len(failed),
        "needs_operator_approval_count": len(needs_approval),
        "next_eligible_retry": next_retry_candidates[0] if next_retry_candidates else None,
        "items": [item.to_dict() for item in items],
    }


def create_queue_item(
    vault_root: str | Path,
    *,
    original_request: str,
    task_class: str,
    required_provider_strength: str,
    primary_provider_id: str | None,
    primary_failure_reason: str,
    fallback_denied_reason: str,
    cooldown_until: str | None = None,
    required_context_files: list[str] | None = None,
    related_runtime: str = "unknown",
    related_adapter: str = "unknown",
    approval_status: str = "not_required",
    retry_status: str = "waiting_for_primary",
    safe_next_step: str = "Retry with primary provider after cooldown/recovery.",
    operator_note: str = "",
    source_command: str | None = None,
) -> ProviderQueueItem:
    now = _utc_now()
    item = ProviderQueueItem(
        task_id=f"rpglq-{uuid.uuid4().hex[:12]}",
        created_at=now,
        updated_at=now,
        original_request=original_request,
        task_class=normalize_task_class(task_class),
        required_provider_strength=normalize_provider_strength(required_provider_strength),
        primary_provider_id=primary_provider_id,
        primary_failure_reason=primary_failure_reason,
        fallback_denied_reason=fallback_denied_reason,
        cooldown_until=cooldown_until,
        required_context_files=list(required_context_files or []),
        related_runtime=related_runtime,
        related_adapter=related_adapter,
        approval_status=approval_status,
        retry_status=retry_status if retry_status in QUEUE_STATUSES else "waiting_for_primary",
        retry_attempts=0,
        last_retry_at=None,
        safe_next_step=safe_next_step,
        operator_note=operator_note,
        files_modified=False,
    )
    items = load_queue_items(vault_root)
    items.append(item)
    _save_queue_items(vault_root, items)
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="queue_item_created",
            runtime=related_runtime,
            provider_id=primary_provider_id,
            provider_strength=required_provider_strength,
            task_class=item.task_class,
            decision="queue_created",
            reason=primary_failure_reason,
            queue_item_id=item.task_id,
            files_modified=False,
            next_action=safe_next_step,
            source_command=source_command,
        ),
    )
    item.operator_note = (item.operator_note + f" audit_event={event['event_id']}").strip()
    items[-1] = item
    _save_queue_items(vault_root, items)
    return item


def get_queue_item(vault_root: str | Path, task_id: str) -> ProviderQueueItem | None:
    needle = str(task_id)
    for item in load_queue_items(vault_root):
        if item.task_id == needle:
            return item
    return None


def build_queue_retry_package_dry_run(
    vault_root: str | Path,
    item: ProviderQueueItem,
    *,
    records: dict[str, ProviderStatusRecord] | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    provider_records = records if records is not None else load_provider_records(vault_root)
    primary = _select_primary_record(provider_records, provider_id=item.primary_provider_id, runtime=item.related_runtime)
    primary_eligible = primary is not None and _is_primary_eligible(primary)
    approval_clear = item.approval_status not in {"needs_operator_approval", "pending", "denied"}
    retry_status_open = item.retry_status in {"queued", "waiting_for_primary", "ready_for_retry"}
    retry_ready = bool(primary_eligible and approval_clear and retry_status_open)

    blocked_reasons: list[str] = []
    if primary is None:
        blocked_reasons.append("primary_provider_not_found")
    elif not primary_eligible:
        blocked_reasons.append("primary_provider_not_eligible")
    if not approval_clear:
        blocked_reasons.append("operator_approval_required_or_denied")
    if not retry_status_open:
        blocked_reasons.append(f"queue_status_not_retryable:{item.retry_status}")

    package_status = "ready_for_retry" if retry_ready else "waiting_for_primary_or_approval"
    if item.retry_status in {"completed", "failed", "cancelled"}:
        package_status = f"not_retryable_{item.retry_status}"

    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "proof_type": "queue_retry_package_dry_run",
        "generated_at": _utc_now(),
        "source_command": source_command,
        "dry_run": True,
        "task_id": item.task_id,
        "retry_package_id": f"rpgl-retry-{item.task_id}",
        "retry_package_status": package_status,
        "retry_ready": retry_ready,
        "blocked_reasons": blocked_reasons,
        "original_request": item.original_request,
        "task_class": item.task_class,
        "required_provider_strength": item.required_provider_strength,
        "required_context_files": list(item.required_context_files),
        "related_runtime": item.related_runtime,
        "related_adapter": item.related_adapter,
        "approval_status": item.approval_status,
        "retry_status": item.retry_status,
        "retry_attempts": item.retry_attempts,
        "last_retry_at": item.last_retry_at,
        "primary_failure_reason": item.primary_failure_reason,
        "fallback_denied_reason": item.fallback_denied_reason,
        "cooldown_until": item.cooldown_until,
        "primary_provider": primary.to_dict() if primary else None,
        "primary_eligible": primary_eligible,
        "would_route_to": "primary" if retry_ready else None,
        "would_update_queue_status": "ready_for_retry" if retry_ready and item.retry_status != "ready_for_retry" else item.retry_status,
        "would_increment_retry_attempts": False,
        "safe_next_step": (
            "operator_may_retry_with_primary_after_explicit_approval"
            if retry_ready
            else "wait_for_primary_or_operator_approval"
        ),
        "files_modified": False,
        "queue_state_mutated": False,
        "provider_state_mutated": False,
        "canonical_files_mutated": False,
        "queue_drained": False,
        "live_provider_call_attempted": False,
        "secret_value_read": False,
        "fallback_used": False,
        "fallback_sticky_for_development": False,
        "denied_actions": list(QUEUE_RETRY_DRY_RUN_DENIED_ACTIONS),
    }


def retry_queue_item_dry_run(vault_root: str | Path, task_id: str, *, source_command: str | None = None) -> dict[str, Any]:
    item = get_queue_item(vault_root, task_id)
    if item is None:
        return {"ok": False, "task_id": task_id, "reason": "queue_item_not_found", "dry_run": True}
    records = load_provider_records(vault_root)
    package = build_queue_retry_package_dry_run(
        vault_root,
        item,
        records=records,
        source_command=source_command,
    )
    ready = bool(package["retry_ready"])
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="queue_item_retried",
            runtime=item.related_runtime,
            provider_id=item.primary_provider_id,
            provider_strength=item.required_provider_strength,
            task_class=item.task_class,
            decision="dry_run_ready" if ready else "dry_run_wait",
            reason="primary_available" if ready else "primary_unavailable",
            queue_item_id=item.task_id,
            files_modified=False,
            next_action="operator_may_retry_with_primary" if ready else "wait_for_primary",
            source_command=source_command,
        ),
    )
    return {
        "ok": True,
        "dry_run": True,
        "task_id": item.task_id,
        "ready_for_retry": ready,
        "retry_package": package,
        "primary_provider": package.get("primary_provider"),
        "audit_id": event["event_id"],
        "files_modified": False,
        "queue_state_mutated": False,
        "provider_state_mutated": False,
        "canonical_files_mutated": False,
        "queue_drained": False,
        "live_provider_call_attempted": False,
        "secret_value_read": False,
    }


def _select_primary_record(
    records: dict[str, ProviderStatusRecord],
    *,
    provider_id: str | None = None,
    runtime: str | None = None,
) -> ProviderStatusRecord | None:
    candidates = [record for record in records.values() if record.is_primary]
    if runtime and str(runtime).lower() != "unknown":
        runtime_matches = [record for record in candidates if str(record.runtime or "").lower() == str(runtime).lower()]
        if runtime_matches:
            candidates = runtime_matches
    if provider_id:
        provider_matches = [record for record in candidates if record.provider_id == provider_id]
        if not provider_matches:
            return None
        candidates = provider_matches
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item.strength != "strong", item.state in {"disabled", "unhealthy"}, item.provider_key))
    return candidates[0]


def _select_fallback_record(
    records: dict[str, ProviderStatusRecord],
    *,
    provider_id: str | None = None,
    runtime: str | None = None,
) -> ProviderStatusRecord | None:
    candidates = [record for record in records.values() if record.is_fallback]
    if runtime and str(runtime).lower() != "unknown":
        runtime_matches = [record for record in candidates if str(record.runtime or "").lower() == str(runtime).lower()]
        if runtime_matches:
            candidates = runtime_matches
    if provider_id:
        provider_matches = [record for record in candidates if record.provider_id == provider_id]
        if not provider_matches:
            return None
        candidates = provider_matches
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item.strength == "weak", item.state in {"disabled", "unhealthy"}, item.provider_key))
    return candidates[0]


def _is_primary_eligible(record: ProviderStatusRecord) -> bool:
    if record.strength != "strong":
        return False
    if record.state in {"disabled", "unhealthy"}:
        return False
    if record.state in {"rate_limited", "cooling_down"}:
        return _is_expired(record.cooldown_until)
    return True


def _record_to_route_decision(
    record: ProviderStatusRecord,
    *,
    task_class: str,
    required_strength: str,
    decision: str,
    reason: str,
    route: str,
    allowed: bool = True,
    audit_event_ids: list[str] | None = None,
) -> ProviderRouteDecision:
    return ProviderRouteDecision(
        allowed=allowed,
        task_class=task_class,
        required_provider_strength=required_strength,
        decision=decision,
        reason=reason,
        route=route,
        provider_id=record.provider_id,
        provider_name=record.provider_name,
        provider_model=record.model,
        provider_strength=record.strength,
        provider_state=record.state,
        next_action="execute_with_selected_provider" if allowed else "do_not_execute",
        files_modified=False,
        sticky_for_development=False,
        audit_event_ids=list(audit_event_ids or []),
    )


def mark_primary_rate_limited(
    vault_root: str | Path,
    *,
    provider_id: str | None,
    model: str | None,
    runtime: str = "unknown",
    retry_after_seconds: int | None = None,
    cooldown_until: str | None = None,
    reason: str = "rate_limit",
    source_command: str | None = None,
) -> ProviderStatusRecord:
    records = load_provider_records(vault_root)
    target = _select_primary_record(records, provider_id=provider_id, runtime=runtime)
    if target is None:
        target_provider_id = provider_id or provider_id_from_model_id(model) or "unknown"
        strength = classify_provider_strength(target_provider_id, model)
        target = ProviderStatusRecord(
            provider_key=_provider_key(runtime, "primary", target_provider_id, model),
            provider_id=target_provider_id,
            provider_name=_provider_display_name(target_provider_id),
            model=model,
            strength=strength,
            runtime=runtime,
            role="primary",
            is_primary=True,
            is_fallback=False,
            active_for_task_classes=allowed_task_classes_for_strength(strength),
            denied_task_classes=denied_task_classes_for_strength(strength),
            source="rpgl",
        )
    now = _utc_now()
    if cooldown_until is None:
        seconds = retry_after_seconds if retry_after_seconds is not None else 900
        cooldown_until = (datetime.now(timezone.utc) + timedelta(seconds=max(0, int(seconds)))).isoformat().replace("+00:00", "Z")
    target.state = "cooling_down"
    target.last_failure_at = now
    target.last_error_type = reason
    target.cooldown_until = cooldown_until
    target.sticky_for_development = False
    records[target.provider_key] = target
    _save_provider_records(vault_root, records)
    append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="primary_rate_limited",
            runtime=runtime,
            provider_id=target.provider_id,
            provider_name=target.provider_name,
            model=target.model,
            provider_strength=target.strength,
            decision="cooldown",
            reason=reason,
            files_modified=False,
            next_action="queue_strong_tasks_until_primary_recovers",
            source_command=source_command,
        ),
    )
    append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="primary_entered_cooldown",
            runtime=runtime,
            provider_id=target.provider_id,
            provider_name=target.provider_name,
            model=target.model,
            provider_strength=target.strength,
            decision="cooling_down",
            reason=reason,
            files_modified=False,
            next_action=f"retry_after:{cooldown_until}",
            source_command=source_command,
        ),
    )
    return target


def mark_primary_unhealthy(
    vault_root: str | Path,
    *,
    provider_id: str | None,
    model: str | None,
    runtime: str = "unknown",
    reason: str = "provider_error",
    source_command: str | None = None,
) -> ProviderStatusRecord:
    records = load_provider_records(vault_root)
    target = _select_primary_record(records, provider_id=provider_id, runtime=runtime)
    if target is None:
        target_provider_id = provider_id or provider_id_from_model_id(model) or "unknown"
        strength = classify_provider_strength(target_provider_id, model)
        target = ProviderStatusRecord(
            provider_key=_provider_key(runtime, "primary", target_provider_id, model),
            provider_id=target_provider_id,
            provider_name=_provider_display_name(target_provider_id),
            model=model,
            strength=strength,
            runtime=runtime,
            role="primary",
            is_primary=True,
            is_fallback=False,
            active_for_task_classes=allowed_task_classes_for_strength(strength),
            denied_task_classes=denied_task_classes_for_strength(strength),
            source="rpgl",
        )
    now = _utc_now()
    target.state = "unhealthy"
    target.last_failure_at = now
    target.last_error_type = reason
    target.sticky_for_development = False
    records[target.provider_key] = target
    _save_provider_records(vault_root, records)
    append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_state_updated",
            runtime=runtime,
            provider_id=target.provider_id,
            provider_name=target.provider_name,
            model=target.model,
            provider_strength=target.strength,
            decision="primary_marked_unhealthy",
            reason=reason,
            files_modified=False,
            next_action="queue_or_wait_for_primary_recovery",
            source_command=source_command,
        ),
    )
    return target


def probe_provider(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    probe_mode: str = "config",
    write_approval_request: bool = False,
    requested_by: str = "operator",
    gate_approval_id: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    if write_approval_request and gate_approval_id:
        raise RuntimeProviderGovernanceError(
            "runtime provider live-preflight cannot both write a new approval request and validate an existing gate_approval_id"
        )
    mode = normalize_probe_mode(probe_mode)
    records = load_provider_records(vault_root)
    target_text = str(target or "").strip().lower()
    if target_text == "primary":
        record = _select_primary_record(records, runtime=runtime)
    elif target_text == "fallback":
        record = _select_fallback_record(records, runtime=runtime)
    else:
        raise RuntimeProviderGovernanceError("provider probe target must be 'primary' or 'fallback'")
    if record is None:
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="primary_probe_failed" if target_text == "primary" else "provider_state_updated",
                runtime=runtime,
                decision="probe_failed",
                reason=f"{target_text}_provider_not_configured",
                source_command=source_command,
            ),
        )
        return {
            "ok": False,
            "target": target_text,
            "probe_mode": mode,
            "reason": f"{target_text}_provider_not_configured",
            "audit_id": event["event_id"],
            "provider_state_mutated": False,
            "canonical_files_mutated": False,
            "files_modified": False,
        }

    probe_plan = build_provider_probe_plan(vault_root, record, probe_mode=mode)
    if mode == "live-preflight":
        preflight = build_live_provider_probe_preflight(vault_root, record, runtime=runtime)
        approval_artifact: dict[str, Any] | None = None
        approval_validation: dict[str, Any] | None = None
        approval_audit_ids: list[str] = []
        if write_approval_request:
            approval_artifact = write_live_probe_approval_request(
                vault_root,
                preflight,
                requested_by=requested_by,
                source_command=source_command,
            )
            if approval_artifact.get("audit_id"):
                approval_audit_ids.append(str(approval_artifact["audit_id"]))
            preflight = {
                **preflight,
                "gate_approval_id": approval_artifact.get("gate_approval_id"),
                "approval_status": approval_artifact.get("status"),
                "approval_request_written": True,
                "approval_request_ref": approval_artifact.get("approval_ref"),
            }
        elif gate_approval_id:
            approval_validation = validate_live_probe_approval_request(
                vault_root,
                gate_approval_id,
                expected_preflight=preflight,
                source_command=source_command,
            )
            if approval_validation.get("audit_id"):
                approval_audit_ids.append(str(approval_validation["audit_id"]))
            preflight = {
                **preflight,
                "gate_approval_id": gate_approval_id,
                "approval_status": approval_validation.get("approval_status"),
                "approval_validation": approval_validation,
            }
        started = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_preflight_started",
                runtime=record.runtime or runtime,
                provider_id=record.provider_id,
                provider_name=record.provider_name,
                model=record.model,
                provider_strength=record.strength,
                decision="live_probe_preflight_started",
                reason="operator_requested_live_provider_probe_preflight",
                files_modified=False,
                next_action="evaluate_gate_approval_contract",
                source_command=source_command,
            ),
        )
        schema_event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_gate_approval_schema_built",
                runtime=record.runtime or runtime,
                provider_id=record.provider_id,
                provider_name=record.provider_name,
                model=record.model,
                provider_strength=record.strength,
                decision="gate_approval_schema_built",
                reason=str(preflight.get("gate_policy_reason") or "live_provider_probe_requires_gate_approval"),
                files_modified=False,
                next_action="operator_may_review_non_executing_approval_request_template",
                source_command=source_command,
            ),
        )
        denied = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_preflight_denied",
                runtime=record.runtime or runtime,
                provider_id=record.provider_id,
                provider_name=record.provider_name,
                model=record.model,
                provider_strength=record.strength,
                decision="live_probe_denied_by_default",
                reason=str(preflight.get("denial_reason") or "live_provider_probe_requires_gate_approval"),
                files_modified=False,
                next_action="request_explicit_gate_approval_before_live_probe",
                source_command=source_command,
            ),
        )
        return {
            "ok": True,
            "target": target_text,
            "probe_mode": mode,
            "provider": record.to_dict(),
            "probe_plan": probe_plan,
            "live_probe_preflight": preflight,
            "approval_artifact": approval_artifact,
            "approval_validation": approval_validation,
            "live_probe_allowed": False,
            "audit_ids": [started["event_id"], schema_event["event_id"], *approval_audit_ids, denied["event_id"]],
            "provider_state_mutated": False,
            "canonical_files_mutated": False,
            "files_modified": bool(write_approval_request),
        }

    if mode == "network-dry-run":
        started = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="primary_probe_started" if target_text == "primary" else "provider_state_updated",
                runtime=record.runtime or runtime,
                provider_id=record.provider_id,
                provider_name=record.provider_name,
                model=record.model,
                provider_strength=record.strength,
                decision="network_probe_dry_run_started",
                reason="network-dry-run_probe",
                files_modified=False,
                next_action="report_probe_plan_without_external_call",
                source_command=source_command,
            ),
        )
        completed = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_state_updated",
                runtime=record.runtime or runtime,
                provider_id=record.provider_id,
                provider_name=record.provider_name,
                model=record.model,
                provider_strength=record.strength,
                decision="network_probe_dry_run_completed",
                reason=str(probe_plan.get("reason") or "live_network_probe_not_attempted_by_policy"),
                files_modified=False,
                next_action="operator_may_run_approved_live_probe_later",
                source_command=source_command,
            ),
        )
        return {
            "ok": True,
            "target": target_text,
            "probe_mode": mode,
            "provider": record.to_dict(),
            "probe_plan": probe_plan,
            "audit_ids": [started["event_id"], completed["event_id"]],
            "provider_state_mutated": False,
            "canonical_files_mutated": False,
            "files_modified": False,
        }

    started = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="primary_probe_started" if target_text == "primary" else "provider_state_updated",
            runtime=record.runtime or runtime,
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            provider_strength=record.strength,
            decision="probe_started",
            reason="configuration_state_probe",
            files_modified=False,
            next_action="validate_provider_record",
            source_command=source_command,
        ),
    )
    success = bool(record.model) and record.state != "disabled"
    record.last_probe_at = _utc_now()
    if success:
        previous_state = record.state
        record.state = "healthy"
        record.last_success_at = record.last_probe_at
        record.last_error_type = None
        if target_text == "primary":
            record.cooldown_until = None
            record.last_recovered_at = record.last_probe_at
        record.sticky_for_development = False
        records[record.provider_key] = record
        _save_provider_records(vault_root, records)
        event_type = "primary_probe_succeeded" if target_text == "primary" else "provider_state_updated"
        succeeded = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type=event_type,
                runtime=record.runtime or runtime,
                provider_id=record.provider_id,
                provider_name=record.provider_name,
                model=record.model,
                provider_strength=record.strength,
                decision="probe_succeeded",
                reason=f"configuration_record_present; previous_state={previous_state}",
                files_modified=False,
                next_action="primary_available" if target_text == "primary" else "fallback_available",
                source_command=source_command,
            ),
        )
        recovered = None
        if target_text == "primary" and previous_state in {"rate_limited", "cooling_down", "unhealthy", "unknown"}:
            recovered = append_provider_audit_event(
                vault_root,
                ProviderAuditEvent(
                    event_type="primary_recovered",
                    runtime=record.runtime or runtime,
                    provider_id=record.provider_id,
                    provider_name=record.provider_name,
                    model=record.model,
                    provider_strength=record.strength,
                    decision="return_to_primary",
                    reason="probe_succeeded_after_cooldown_or_unknown_state",
                    files_modified=False,
                    next_action="route_high_authority_tasks_to_primary",
                    source_command=source_command,
                ),
            )
        return {
            "ok": True,
            "target": target_text,
            "probe_mode": mode,
            "provider": record.to_dict(),
            "probe_plan": probe_plan,
            "audit_ids": [started["event_id"], succeeded["event_id"]] + ([recovered["event_id"]] if recovered else []),
            "provider_state_mutated": True,
            "canonical_files_mutated": False,
            "files_modified": False,
        }

    record.state = "unhealthy"
    record.last_failure_at = record.last_probe_at
    record.last_error_type = "configuration_record_missing_model"
    records[record.provider_key] = record
    _save_provider_records(vault_root, records)
    failed = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="primary_probe_failed" if target_text == "primary" else "provider_state_updated",
            runtime=record.runtime or runtime,
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            provider_strength=record.strength,
            decision="probe_failed",
            reason="configuration_record_missing_model",
            files_modified=False,
            next_action="keep_queued",
            source_command=source_command,
        ),
    )
    return {
        "ok": False,
        "target": target_text,
        "probe_mode": mode,
        "provider": record.to_dict(),
        "probe_plan": probe_plan,
        "audit_ids": [started["event_id"], failed["event_id"]],
        "provider_state_mutated": True,
        "canonical_files_mutated": False,
        "files_modified": False,
    }


def _executor_precondition(
    precondition_id: str,
    *,
    passed: bool,
    status: str | None = None,
    critical: bool = True,
    reason: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_status = status or ("passed" if passed else "failed")
    return {
        "id": precondition_id,
        "passed": bool(passed),
        "status": resolved_status,
        "critical": bool(critical),
        "reason": reason,
        "evidence": dict(evidence or {}),
    }


def build_live_probe_executor_spec(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the non-executing live-provider-probe executor contract.

    This is an executor specification and precondition report only. It does not
    call provider endpoints, read secret values, mutate provider health state,
    drain queues, restart gateways, or write approval artifacts.
    """
    target_text = str(target or "").strip().lower()
    if target_text not in {"primary", "fallback"}:
        raise RuntimeProviderGovernanceError("provider executor-spec target must be 'primary' or 'fallback'")

    record = _select_live_probe_record(
        vault_root,
        target=target_text,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
    )
    if record is None:
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_executor_spec_requested",
                runtime=runtime,
                decision="executor_spec_failed",
                reason=f"{target_text}_provider_not_configured",
                files_modified=False,
                next_action="configure_provider_before_executor_design",
                source_command=source_command,
            ),
        )
        return {
            "ok": False,
            "target": target_text,
            "executor_status": "not_built",
            "execution_enabled": False,
            "live_probe_execution_allowed": False,
            "reason": f"{target_text}_provider_not_configured",
            "audit_id": event["event_id"],
            "live_network_call_attempted": False,
            "secret_value_read": False,
            "provider_state_mutated": False,
            "queue_mutated": False,
            "gateway_mutated": False,
            "canonical_files_mutated": False,
            "approval_request_written": False,
            "files_modified": False,
        }

    preflight = build_live_provider_probe_preflight(vault_root, record, runtime=runtime)
    probe_plan = build_provider_probe_plan(vault_root, record, probe_mode="live-preflight")
    approval_validation: dict[str, Any] | None = None
    decision_validation: dict[str, Any] | None = None
    if gate_approval_id:
        approval_validation = validate_live_probe_approval_request(
            vault_root,
            gate_approval_id,
            expected_preflight=preflight,
            source_command=source_command,
        )
        decision_validation = validate_live_probe_decision_records(vault_root, gate_approval_id=gate_approval_id)
        preflight = {
            **preflight,
            "gate_approval_id": gate_approval_id,
            "approval_status": approval_validation.get("approval_status"),
            "approval_validation": approval_validation,
            "decision_validation": decision_validation,
        }

    gate_operation_declared = (
        preflight.get("approval_schema", {}).get("operation") == LIVE_PROVIDER_PROBE_GATE_OPERATION
        and preflight.get("approval_schema", {}).get("approval_schema_id") == LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID
    )
    artifact_supplied = bool(gate_approval_id)
    artifact_valid = bool(approval_validation and approval_validation.get("structurally_valid"))
    approval_accepted = bool(approval_validation and approval_validation.get("approval_decision_accepted"))
    approved_decision_record = bool(decision_validation and decision_validation.get("decision_record_consumable"))
    provider_setup_valid = preflight.get("valid_setup_state") is True
    secret_reference_present = preflight.get("secret_reference_present") is True
    timeout_policy_present = dict(preflight.get("timeout_values") or {}) == FallbackTimeouts().to_dict()

    preconditions = [
        _executor_precondition(
            "executor_implemented",
            passed=False,
            status="not_built",
            reason="live_provider_probe_executor_not_implemented",
        ),
        _executor_precondition(
            "gate_operation_declared",
            passed=gate_operation_declared,
            reason="runtime.provider.live_probe approval schema is declared"
            if gate_operation_declared
            else "runtime.provider.live_probe approval schema is missing",
        ),
        _executor_precondition(
            "gate_operation_allows_execution",
            passed=bool(preflight.get("gate_policy_allowed")),
            critical=False,
            reason=str(preflight.get("gate_policy_reason") or "gate_denied_or_not_checked"),
        ),
        _executor_precondition(
            "approval_artifact_supplied",
            passed=artifact_supplied,
            status="passed" if artifact_supplied else "missing",
            reason="gate_approval_id supplied" if artifact_supplied else "no gate_approval_id supplied",
        ),
        _executor_precondition(
            "approval_artifact_structurally_valid",
            passed=artifact_valid,
            status=("passed" if artifact_valid else ("failed" if approval_validation else "not_checked")),
            reason=(
                "approval artifact matches preflight"
                if artifact_valid
                else (
                    str((approval_validation or {}).get("reason") or "approval artifact not checked")
                )
            ),
            evidence={"gate_approval_id": gate_approval_id} if gate_approval_id else {},
        ),
        _executor_precondition(
            "approval_status_approved",
            passed=approval_accepted,
            status=("passed" if approval_accepted else (str((approval_validation or {}).get("approval_status")) if approval_validation else "not_checked")),
            reason="approval artifact is approved" if approval_accepted else "approval artifact is not approved",
        ),
        _executor_precondition(
            "approval_decision_consumption_implemented",
            passed=False,
            status="not_built",
            reason="immutable approval decision consumption is not implemented for RPGL live probes",
        ),
        _executor_precondition(
            "approved_immutable_decision_record_present",
            passed=approved_decision_record,
            status=(
                "passed"
                if approved_decision_record
                else (str((decision_validation or {}).get("status")) if decision_validation else "not_checked")
            ),
            reason=(
                "approved immutable decision record is present"
                if approved_decision_record
                else "approved immutable decision record is missing or not consumable"
            ),
            evidence={
                "selected_decision_id": (decision_validation or {}).get("selected_decision_id"),
                "records_found": (decision_validation or {}).get("records_found"),
            },
        ),
        _executor_precondition(
            "provider_setup_valid",
            passed=provider_setup_valid,
            status="passed" if provider_setup_valid else "failed",
            reason="provider setup is valid" if provider_setup_valid else "provider setup is missing or invalid",
            evidence={"missing_setup_checks": list(preflight.get("missing_setup_checks") or [])},
        ),
        _executor_precondition(
            "secret_reference_present",
            passed=secret_reference_present,
            status="passed" if secret_reference_present else "failed",
            reason="secret reference metadata is present" if secret_reference_present else "secret reference metadata is missing",
        ),
        _executor_precondition(
            "timeout_policy_present",
            passed=timeout_policy_present,
            critical=False,
            reason="fallback/live probe timeout policy is available",
            evidence={"timeout_values": dict(preflight.get("timeout_values") or {})},
        ),
        _executor_precondition(
            "single_attempt_idempotency_marker_absent",
            passed=False,
            status="not_built",
            reason="executor idempotency markers are not implemented",
        ),
        _executor_precondition(
            "write_targets_limited_to_runtime_provider_state",
            passed=True,
            critical=False,
            reason="future executor write targets are limited to provider state and provider audit",
            evidence={
                "allowed_write_targets": [
                    str(STATE_RELATIVE_PATH).replace("\\", "/"),
                    str(AUDIT_RELATIVE_PATH).replace("\\", "/"),
                ]
            },
        ),
        _executor_precondition(
            "blocked_actions_unchanged",
            passed=True,
            critical=False,
            reason="executor spec keeps queue drain, gateway restart, config edits, and canonical writes denied",
            evidence={"denied_actions": list(preflight.get("denied_actions") or [])},
        ),
    ]
    blocked_reasons = [
        str(item["reason"] or item["id"])
        for item in preconditions
        if item.get("critical") and not item.get("passed")
    ]

    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_executor_spec_requested",
            runtime=record.runtime or runtime,
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            provider_strength=record.strength,
            decision="executor_spec_not_built",
            reason="live_provider_probe_executor_spec_requested_without_execution",
            files_modified=False,
            next_action="implement_future_executor_only_after_gate_approval_consumption",
            source_command=source_command,
        ),
    )
    return {
        "ok": True,
        "target": target_text,
        "executor_status": "not_built",
        "execution_enabled": False,
        "live_probe_execution_allowed": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "approval_request_written": False,
        "files_modified": False,
        "provider": record.to_dict(),
        "probe_plan": probe_plan,
        "live_probe_preflight": preflight,
        "approval_validation": approval_validation,
        "decision_validation": decision_validation,
        "preconditions": preconditions,
        "blocked_reasons": blocked_reasons,
        "future_executor_requirements": [
            "validate RPGL approval artifact against the current live-preflight contract",
            "require approved status plus immutable approval decision provenance before any external call",
            "require an approval-aware Gate runtime operation check to pass",
            "load secrets only through an approved credential-reference mechanism without logging values",
            "enforce first-token, no-chunk, wall-time, and max-attempt timeout policy",
            "write only provider state and provider audit records allowed by Gate",
            "persist a single-attempt idempotency marker per gate_approval_id before execution",
            "never drain provider queues, edit provider config, restart gateways, or mutate canonical docs",
        ],
        "audit_id": event["event_id"],
    }


def build_live_probe_decision_preflight(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Validate immutable live-probe decision and marker preconditions without execution."""
    if not gate_approval_id:
        raise RuntimeProviderGovernanceError("live probe decision preflight requires --gate-approval-id")
    target_text = str(target or "").strip().lower()
    if target_text not in {"primary", "fallback"}:
        raise RuntimeProviderGovernanceError("live probe decision preflight target must be 'primary' or 'fallback'")

    executor_spec = build_live_probe_executor_spec(
        vault_root,
        target=target_text,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command=source_command,
    )
    approval_validation = executor_spec.get("approval_validation") or {}
    decision_validation = executor_spec.get("decision_validation") or {}
    marker_path = _live_probe_marker_path(vault_root, gate_approval_id)
    marker_exists = marker_path.exists()
    decision_consumable = bool(decision_validation.get("decision_record_consumable"))

    if marker_exists:
        preflight_status = "blocked_marker_already_exists"
    elif approval_validation.get("errors"):
        preflight_status = "blocked_missing_or_invalid_approval_artifact"
    elif decision_validation.get("errors"):
        preflight_status = "blocked_missing_or_invalid_decision_record"
    elif decision_consumable:
        preflight_status = "approved_decision_record_valid_but_executor_not_built"
    else:
        preflight_status = "blocked_live_probe_executor_not_built"

    blocked_reasons = list(executor_spec.get("blocked_reasons") or [])
    if marker_exists and "live_probe_idempotency_marker_exists" not in blocked_reasons:
        blocked_reasons.append("live_probe_idempotency_marker_exists")

    provider = executor_spec.get("provider") or {}
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_decision_preflight_requested",
            runtime=str(provider.get("runtime") or runtime),
            provider_id=str(provider.get("provider_id") or "") or None,
            provider_name=str(provider.get("provider_name") or "") or None,
            model=provider.get("model"),
            provider_strength=provider.get("strength"),
            decision=preflight_status,
            reason="live_probe_decision_preflight_is_non_executing",
            files_modified=False,
            next_action="build_or_review_marker_contract_before_any_live_probe_executor",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_schema_id": "rpgl.live_provider_probe_decision_preflight.v1",
        "target": target_text,
        "runtime": runtime,
        "gate_approval_id": gate_approval_id,
        "preflight_status": preflight_status,
        "ok": bool(executor_spec.get("ok")),
        "executor_status": executor_spec.get("executor_status"),
        "execution_enabled": False,
        "live_probe_execution_allowed": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "approval_request_written": False,
        "decision_record_written": False,
        "idempotency_marker_written": False,
        "files_modified": False,
        "provider": provider,
        "approval_validation": approval_validation,
        "decision_validation": decision_validation,
        "marker_path": str(marker_path),
        "marker_exists": marker_exists,
        "blocked_reasons": blocked_reasons,
        "executor_spec": executor_spec,
        "audit_id": event["event_id"],
    }


def build_live_probe_marker_contract(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the no-execution marker contract for future live-provider probes."""
    preflight = build_live_probe_decision_preflight(
        vault_root,
        target=target,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command=source_command,
    )
    decision_validation = preflight.get("decision_validation") or {}
    provider = preflight.get("provider") or {}
    marker_path = Path(str(preflight.get("marker_path")))
    marker_exists = bool(preflight.get("marker_exists"))
    marker_payload_preview = {
        "record_type": "runtime_provider_live_probe_consumption_marker",
        "schema_version": SCHEMA_VERSION,
        "marker_schema_id": "rpgl.live_provider_probe_consumption_marker.v1",
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "gate_approval_id": gate_approval_id,
        "target": preflight.get("target"),
        "runtime": runtime,
        "provider_id": provider.get("provider_id"),
        "provider_name": provider.get("provider_name"),
        "model": provider.get("model"),
        "provider_strength": provider.get("strength"),
        "selected_decision_id": decision_validation.get("selected_decision_id"),
        "selected_decision_ref": decision_validation.get("selected_decision_ref"),
        "decision": decision_validation.get("decision"),
        "marker_written": False,
        "live_probe_execution_allowed": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "created_at": "<future-marker-created-at>",
        "source_command": source_command,
    }

    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_marker_contract_requested",
            runtime=str(provider.get("runtime") or runtime),
            provider_id=str(provider.get("provider_id") or "") or None,
            provider_name=str(provider.get("provider_name") or "") or None,
            model=provider.get("model"),
            provider_strength=provider.get("strength"),
            decision="marker_contract_previewed_without_write",
            reason="live_probe_marker_contract_is_non_executing",
            files_modified=False,
            next_action="future_executor_must_write_marker_atomically_before_provider_call",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "marker_contract_schema_id": "rpgl.live_provider_probe_marker_contract.v1",
        "marker_schema_id": "rpgl.live_provider_probe_consumption_marker.v1",
        "target": preflight.get("target"),
        "runtime": runtime,
        "gate_approval_id": gate_approval_id,
        "marker_directory": str(marker_path.parent),
        "marker_path": str(marker_path),
        "marker_exists": marker_exists,
        "writer_status": "not_built",
        "execution_enabled": False,
        "live_probe_execution_allowed": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "approval_request_written": False,
        "decision_record_written": False,
        "idempotency_marker_written": False,
        "files_modified": False,
        "provider": provider,
        "decision_preflight": preflight,
        "marker_payload_preview": marker_payload_preview,
        "atomicity_rules": [
            "validate exactly one approved immutable decision record before marker creation",
            "resolve marker path under runtime/providers/state/provider_live_probe_markers and reject path escape",
            "create marker with create-new/exclusive semantics only",
            "write marker before any provider network call or secret-value read",
            "never overwrite, delete, or reuse an existing marker",
            "do not mutate approval request or decision record artifacts",
        ],
        "forbidden_actions": [
            "provider_network_call",
            "secret_value_read",
            "provider_state_mutation",
            "queue_drain",
            "gateway_restart",
            "provider_config_edit",
            "canonical_doc_write",
            "marker_write_in_this_contract",
        ],
        "blocked_reasons": list(preflight.get("blocked_reasons") or [])
        + ["live_probe_marker_writer_not_implemented", "live_probe_executor_not_implemented"],
        "audit_id": event["event_id"],
    }


def format_live_probe_approval_decision_record(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Approval Decision",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- decision_id: {payload.get('decision_id')}",
        f"- decision: {payload.get('decision')}",
        f"- decision_status: {payload.get('decision_status')}",
        f"- decision_record_writable: {payload.get('decision_record_writable')}",
        f"- decision_record_written: {payload.get('decision_record_written')}",
        f"- decision_ref: {payload.get('decision_ref')}",
        f"- live_probe_execution_allowed: {payload.get('live_probe_execution_allowed')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    blocked = payload.get("blocked_reasons") or []
    if blocked:
        lines.append("- blocked_reasons: " + ", ".join(str(item) for item in blocked))
    return "\n".join(lines)


def format_live_probe_decision_preflight(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Decision Preflight",
        f"- target: {payload.get('target')}",
        f"- runtime: {payload.get('runtime')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- preflight_status: {payload.get('preflight_status')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- marker_path: {payload.get('marker_path')}",
        f"- marker_exists: {payload.get('marker_exists')}",
        f"- live_probe_execution_allowed: {payload.get('live_probe_execution_allowed')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    decision = payload.get("decision_validation") or {}
    if decision:
        lines.append(f"- decision_record_consumable: {decision.get('decision_record_consumable')}")
        lines.append(f"- selected_decision_id: {decision.get('selected_decision_id')}")
    blocked = payload.get("blocked_reasons") or []
    if blocked:
        lines.append("- blocked_reasons:")
        for reason in blocked:
            lines.append(f"  - {reason}")
    return "\n".join(lines)


def format_live_probe_marker_contract(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Marker Contract",
        f"- target: {payload.get('target')}",
        f"- runtime: {payload.get('runtime')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- writer_status: {payload.get('writer_status')}",
        f"- marker_path: {payload.get('marker_path')}",
        f"- marker_exists: {payload.get('marker_exists')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- live_probe_execution_allowed: {payload.get('live_probe_execution_allowed')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    preview = payload.get("marker_payload_preview") or {}
    if preview:
        lines.append(f"- selected_decision_id: {preview.get('selected_decision_id')}")
        lines.append(f"- provider_id: {preview.get('provider_id')}")
        lines.append(f"- model: {preview.get('model')}")
    return "\n".join(lines)


def load_live_probe_decision_consumer_record(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
) -> dict[str, Any] | None:
    path = _live_probe_consumer_record_path(vault_root, gate_approval_id)
    if not path.exists():
        return None
    data = _read_json(path, {})
    data["consumer_record_ref"] = str(path)
    return data


def load_live_probe_atomic_marker(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
) -> dict[str, Any] | None:
    path = _live_probe_marker_path(vault_root, gate_approval_id)
    if not path.exists():
        return None
    data = _read_json(path, {})
    data["marker_ref"] = str(path)
    return data


def write_live_probe_decision_consumer_record(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist a live-probe approval-decision consumer record without executing a probe."""
    target_text = str(target or "").strip().lower()
    if target_text not in {"primary", "fallback"}:
        raise RuntimeProviderGovernanceError("live probe decision consumer target must be 'primary' or 'fallback'")
    source = source_command or f"chaseos runtime provider live-probe-decision-consumer {target_text}"
    preflight = build_live_probe_decision_preflight(
        vault_root,
        target=target_text,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command=source,
    )
    decision_validation = preflight.get("decision_validation") if isinstance(preflight.get("decision_validation"), dict) else {}
    provider = preflight.get("provider") if isinstance(preflight.get("provider"), dict) else {}
    selected_decision_id = str(decision_validation.get("selected_decision_id") or "")
    consumer_record_path = _live_probe_consumer_record_path(vault_root, gate_approval_id)
    marker_path = _live_probe_marker_path(vault_root, gate_approval_id)
    existing_consumer = load_live_probe_decision_consumer_record(vault_root, gate_approval_id=gate_approval_id)

    blocked_reasons: list[str] = []
    if not bool(decision_validation.get("decision_record_consumable")):
        blocked_reasons.append("live_probe_approved_decision_missing_or_invalid")
    if marker_path.exists():
        blocked_reasons.append("live_probe_idempotency_marker_exists")
    if existing_consumer:
        blocked_reasons.append("live_probe_decision_consumer_record_exists")
    if not selected_decision_id:
        blocked_reasons.append("live_probe_selected_decision_missing")
    if not bool(preflight.get("ok")):
        blocked_reasons.append("live_probe_provider_not_configured")

    if blocked_reasons:
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_decision_consumer_record_write_blocked",
                runtime=str(provider.get("runtime") or runtime),
                provider_id=str(provider.get("provider_id") or "") or None,
                provider_name=str(provider.get("provider_name") or "") or None,
                model=provider.get("model"),
                provider_strength=provider.get("strength"),
                decision="blocked_live_probe_decision_consumer_record_write",
                reason="live_probe_decision_consumer_record_preconditions_not_ready",
                files_modified=False,
                next_action="resolve_live_probe_decision_or_existing_marker_before_consumer_record_write",
                source_command=source,
            ),
        )
        raise RuntimeProviderGovernanceError(
            "live probe decision consumer record write blocked: "
            + ", ".join(blocked_reasons)
            + f" (audit_id={event['event_id']})"
        )

    consumer_directory_created = not consumer_record_path.parent.exists()
    record = {
        "record_type": "runtime_provider_live_probe_decision_consumer_record",
        "schema_version": SCHEMA_VERSION,
        "consumer_record_schema_id": "rpgl.live_provider_probe_decision_consumer.v1",
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "target": target_text,
        "runtime": runtime,
        "provider_id": provider.get("provider_id"),
        "provider_name": provider.get("provider_name"),
        "model": provider.get("model"),
        "provider_strength": provider.get("strength"),
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": decision_validation.get("selected_decision_ref"),
        "decision": decision_validation.get("decision"),
        "decision_digest_sha256": decision_validation.get("selected_decision_digest_sha256"),
        "consumer_record_ref": str(consumer_record_path),
        "consumer_record_path": str(consumer_record_path),
        "consumer_status": "record_written_marker_handoff_required",
        "consumer_write_mode": "explicit_write_flag_create_new_only",
        "consumer_record_written": True,
        "decision_consumer_record_written": True,
        "consumer_directory_created": consumer_directory_created,
        "approval_consumed": False,
        "decision_consumed": True,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "marker_handoff_required": True,
        "live_probe_execution_allowed": False,
        "execution_enabled": False,
        "created_at": _utc_now(),
        "source_command": source,
    }
    record["consumer_record_digest_sha256"] = _consumer_record_digest(record)
    consumer_record_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with consumer_record_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise RuntimeProviderGovernanceError(f"live probe decision consumer record already exists: {consumer_record_path}") from exc

    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_decision_consumer_record_written",
            runtime=str(provider.get("runtime") or runtime),
            provider_id=str(provider.get("provider_id") or "") or None,
            provider_name=str(provider.get("provider_name") or "") or None,
            model=provider.get("model"),
            provider_strength=provider.get("strength"),
            decision="consumer_record_written_marker_handoff_required",
            reason="live_probe_decision_consumer_record_written_without_provider_call",
            files_modified=True,
            next_action="run_live_probe_atomic_marker_writer_before_any_live_probe_executor",
            source_command=source,
        ),
    )
    return {
        **preflight,
        "consumer_write_status": "consumer_record_written_marker_handoff_required",
        "consumer_writer_status": "record_written",
        "consumer_record": record,
        "consumer_record_ref": str(consumer_record_path),
        "consumer_record_path": str(consumer_record_path),
        "consumer_record_digest_sha256": record["consumer_record_digest_sha256"],
        "write_enabled": True,
        "write_supported_now": True,
        "decision_consumed": True,
        "decision_consumer_record_written": True,
        "consumer_directory_created": consumer_directory_created,
        "approval_consumed": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "consumption_marker_written": False,
        "idempotency_marker_written": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "live_probe_execution_allowed": False,
        "execution_enabled": False,
        "files_modified": True,
        "write_audit_id": event["event_id"],
        "next_action": "run_live_probe_atomic_marker_writer_before_any_live_probe_executor",
    }


def format_live_probe_decision_consumer_record(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Decision Consumer Record",
        f"- target: {payload.get('target')}",
        f"- runtime: {payload.get('runtime')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- consumer_write_status: {payload.get('consumer_write_status')}",
        f"- consumer_writer_status: {payload.get('consumer_writer_status')}",
        f"- selected_decision_id: {payload.get('decision_validation', {}).get('selected_decision_id') if isinstance(payload.get('decision_validation'), dict) else payload.get('selected_decision_id')}",
        f"- consumer_record_ref: {payload.get('consumer_record_ref')}",
        f"- consumer_record_digest_sha256: {payload.get('consumer_record_digest_sha256')}",
        f"- decision_consumed: {payload.get('decision_consumed')}",
        f"- decision_consumer_record_written: {payload.get('decision_consumer_record_written')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- live_probe_execution_allowed: {payload.get('live_probe_execution_allowed')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def write_live_probe_atomic_marker(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Persist a live-probe idempotency marker without executing a provider call."""
    target_text = str(target or "").strip().lower()
    if target_text not in {"primary", "fallback"}:
        raise RuntimeProviderGovernanceError("live probe atomic marker target must be 'primary' or 'fallback'")
    source = source_command or f"chaseos runtime provider live-probe-atomic-marker-writer {target_text}"
    preflight = build_live_probe_decision_preflight(
        vault_root,
        target=target_text,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command=source,
    )
    decision_validation = preflight.get("decision_validation") if isinstance(preflight.get("decision_validation"), dict) else {}
    provider = preflight.get("provider") if isinstance(preflight.get("provider"), dict) else {}
    selected_decision_id = str(decision_validation.get("selected_decision_id") or "")
    marker_path = _live_probe_marker_path(vault_root, gate_approval_id)
    consumer_record = load_live_probe_decision_consumer_record(vault_root, gate_approval_id=gate_approval_id)
    consumer_digest_valid = False
    consumer_errors: list[str] = []
    if consumer_record:
        expected_consumer_digest = _consumer_record_digest(consumer_record)
        consumer_digest_valid = (
            bool(consumer_record.get("consumer_record_digest_sha256"))
            and consumer_record.get("consumer_record_digest_sha256") == expected_consumer_digest
        )
        if consumer_record.get("record_type") != "runtime_provider_live_probe_decision_consumer_record":
            consumer_errors.append("consumer_record_type_invalid")
        if consumer_record.get("gate_approval_id") != gate_approval_id:
            consumer_errors.append("consumer_gate_approval_id_mismatch")
        if consumer_record.get("target") != target_text:
            consumer_errors.append("consumer_target_mismatch")
        if consumer_record.get("selected_decision_id") != selected_decision_id:
            consumer_errors.append("consumer_selected_decision_id_mismatch")
        if consumer_record.get("decision_consumed") is not True:
            consumer_errors.append("consumer_decision_consumed_not_true")
        if consumer_record.get("decision_record_mutated") is not False:
            consumer_errors.append("consumer_decision_record_mutated_not_false")
        if consumer_record.get("provider_state_mutated") is not False or consumer_record.get("live_network_call_attempted") is not False:
            consumer_errors.append("consumer_mutation_claims_invalid")
        if not consumer_digest_valid:
            consumer_errors.append("consumer_digest_invalid")

    blocked_reasons: list[str] = []
    if not bool(decision_validation.get("decision_record_consumable")):
        blocked_reasons.append("live_probe_approved_decision_missing_or_invalid")
    if not consumer_record:
        blocked_reasons.append("live_probe_decision_consumer_record_missing")
    blocked_reasons.extend(consumer_errors)
    if marker_path.exists():
        blocked_reasons.append("live_probe_idempotency_marker_exists")
    if not bool(preflight.get("ok")):
        blocked_reasons.append("live_probe_provider_not_configured")
    blocked_reasons = list(dict.fromkeys(blocked_reasons))

    if blocked_reasons:
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_atomic_marker_write_blocked",
                runtime=str(provider.get("runtime") or runtime),
                provider_id=str(provider.get("provider_id") or "") or None,
                provider_name=str(provider.get("provider_name") or "") or None,
                model=provider.get("model"),
                provider_strength=provider.get("strength"),
                decision="blocked_live_probe_atomic_marker_write",
                reason="live_probe_atomic_marker_preconditions_not_ready",
                files_modified=False,
                next_action="write_valid_live_probe_consumer_record_before_marker_or_review_existing_marker",
                source_command=source,
            ),
        )
        raise RuntimeProviderGovernanceError(
            "live probe atomic marker write blocked: "
            + ", ".join(blocked_reasons or ["unknown"])
            + f" (audit_id={event['event_id']})"
        )

    marker_directory_created = not marker_path.parent.exists()
    marker = {
        "record_type": "runtime_provider_live_probe_consumption_marker",
        "schema_version": SCHEMA_VERSION,
        "marker_schema_id": "rpgl.live_provider_probe_consumption_marker.v1",
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "target": target_text,
        "runtime": runtime,
        "provider_id": provider.get("provider_id"),
        "provider_name": provider.get("provider_name"),
        "model": provider.get("model"),
        "provider_strength": provider.get("strength"),
        "selected_decision_id": selected_decision_id,
        "selected_decision_ref": decision_validation.get("selected_decision_ref"),
        "selected_decision_digest_sha256": decision_validation.get("selected_decision_digest_sha256"),
        "consumer_record_ref": consumer_record.get("consumer_record_ref") if consumer_record else None,
        "consumer_record_digest_sha256": consumer_record.get("consumer_record_digest_sha256") if consumer_record else None,
        "marker_status": "written_live_probe_executor_handoff_required",
        "idempotency_marker_written": True,
        "approval_consumed": False,
        "decision_consumed": True,
        "decision_consumer_record_written": True,
        "consumer_record_mutated": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "live_probe_execution_allowed": False,
        "execution_enabled": False,
        "created_at": _utc_now(),
        "source_command": source,
    }
    marker["marker_ref"] = str(marker_path)
    marker["marker_digest_sha256"] = _marker_digest(marker)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with marker_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(marker, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise RuntimeProviderGovernanceError(f"live probe marker already exists: {marker_path}") from exc

    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_atomic_marker_written",
            runtime=str(provider.get("runtime") or runtime),
            provider_id=str(provider.get("provider_id") or "") or None,
            provider_name=str(provider.get("provider_name") or "") or None,
            model=provider.get("model"),
            provider_strength=provider.get("strength"),
            decision="atomic_marker_written_live_probe_executor_handoff_required",
            reason="live_probe_atomic_marker_written_without_provider_call",
            files_modified=True,
            next_action="live_probe_executor_still_not_built",
            source_command=source,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "marker_schema_id": "rpgl.live_provider_probe_consumption_marker.v1",
        "target": target_text,
        "runtime": runtime,
        "gate_approval_id": gate_approval_id,
        "marker_write_status": "atomic_marker_written_live_probe_executor_handoff_required",
        "marker_ref": str(marker_path),
        "marker_path": str(marker_path),
        "marker_digest_sha256": marker["marker_digest_sha256"],
        "marker": marker,
        "consumer_record": consumer_record,
        "consumer_record_ref": consumer_record.get("consumer_record_ref") if consumer_record else None,
        "consumer_record_digest_valid": consumer_digest_valid,
        "selected_decision_id": selected_decision_id,
        "decision_preflight": preflight,
        "idempotency_marker_written": True,
        "marker_directory_created": marker_directory_created,
        "approval_consumed": False,
        "decision_consumed": True,
        "decision_consumer_record_written": True,
        "consumer_record_mutated": False,
        "approval_artifact_mutated": False,
        "decision_record_mutated": False,
        "provider_state_mutated": False,
        "secret_value_read": False,
        "live_network_call_attempted": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "live_probe_execution_allowed": False,
        "execution_enabled": False,
        "files_modified": True,
        "write_audit_id": event["event_id"],
        "next_action": "live_probe_executor_still_not_built",
    }


def format_live_probe_atomic_marker(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Atomic Marker",
        f"- target: {payload.get('target')}",
        f"- runtime: {payload.get('runtime')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- marker_write_status: {payload.get('marker_write_status')}",
        f"- selected_decision_id: {payload.get('selected_decision_id')}",
        f"- consumer_record_ref: {payload.get('consumer_record_ref')}",
        f"- marker_ref: {payload.get('marker_ref')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- live_probe_execution_allowed: {payload.get('live_probe_execution_allowed')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def build_live_probe_executor_dry_run_plan(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Return the non-network live-probe executor readiness plan.

    This composes the already-written approval, immutable decision, consumer
    record, and marker chain into one executor handoff report. It intentionally
    does not call providers, read secret values, mutate provider state, drain
    queues, restart gateways, or consume any artifact.
    """
    if not gate_approval_id:
        raise RuntimeProviderGovernanceError("live probe executor dry-run requires --gate-approval-id")
    target_text = str(target or "").strip().lower()
    if target_text not in {"primary", "fallback"}:
        raise RuntimeProviderGovernanceError("live probe executor dry-run target must be 'primary' or 'fallback'")

    record = _select_live_probe_record(
        vault_root,
        target=target_text,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
    )
    if record is None:
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_executor_dry_run_requested",
                runtime=runtime,
                decision="blocked_live_probe_executor_dry_run",
                reason=f"{target_text}_provider_not_configured",
                files_modified=False,
                next_action="configure_provider_before_live_probe_executor_dry_run",
                source_command=source_command,
            ),
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "executor_dry_run_schema_id": "rpgl.live_provider_probe_executor_dry_run.v1",
            "target": target_text,
            "runtime": runtime,
            "gate_approval_id": gate_approval_id,
            "ok": False,
            "readiness_status": "blocked_executor_readiness_preconditions",
            "executor_status": "dry_run_readiness_only",
            "execution_enabled": False,
            "live_probe_execution_allowed": False,
            "live_network_call_attempted": False,
            "secret_value_read": False,
            "provider_state_mutated": False,
            "queue_mutated": False,
            "gateway_mutated": False,
            "canonical_files_mutated": False,
            "files_modified": False,
            "blocked_reasons": [f"{target_text}_provider_not_configured"],
            "audit_id": event["event_id"],
            "next_action": "configure_provider_before_live_probe_executor_dry_run",
        }

    preflight = build_live_provider_probe_preflight(vault_root, record, runtime=runtime)
    probe_plan = build_provider_probe_plan(vault_root, record, probe_mode="live-preflight")
    approval_validation = validate_live_probe_approval_request(
        vault_root,
        gate_approval_id,
        expected_preflight=preflight,
        source_command=source_command,
    )
    decision_validation = validate_live_probe_decision_records(vault_root, gate_approval_id=gate_approval_id)
    consumer_record = load_live_probe_decision_consumer_record(vault_root, gate_approval_id=gate_approval_id)
    marker = load_live_probe_atomic_marker(vault_root, gate_approval_id=gate_approval_id)
    selected_decision_id = str(decision_validation.get("selected_decision_id") or "")
    marker_path = _live_probe_marker_path(vault_root, gate_approval_id)

    consumer_errors: list[str] = []
    consumer_digest_valid = False
    if not consumer_record:
        consumer_errors.append("live_probe_decision_consumer_record_missing")
    else:
        consumer_digest_valid = (
            bool(consumer_record.get("consumer_record_digest_sha256"))
            and consumer_record.get("consumer_record_digest_sha256") == _consumer_record_digest(consumer_record)
        )
        if consumer_record.get("record_type") != "runtime_provider_live_probe_decision_consumer_record":
            consumer_errors.append("consumer_record_type_invalid")
        if consumer_record.get("gate_approval_id") != gate_approval_id:
            consumer_errors.append("consumer_gate_approval_id_mismatch")
        if consumer_record.get("target") != target_text:
            consumer_errors.append("consumer_target_mismatch")
        if consumer_record.get("selected_decision_id") != selected_decision_id:
            consumer_errors.append("consumer_selected_decision_id_mismatch")
        if consumer_record.get("decision_consumed") is not True:
            consumer_errors.append("consumer_decision_consumed_not_true")
        if consumer_record.get("approval_consumed") is not False:
            consumer_errors.append("consumer_approval_consumed_not_false")
        if consumer_record.get("live_network_call_attempted") is not False:
            consumer_errors.append("consumer_live_network_call_attempted_not_false")
        if consumer_record.get("provider_state_mutated") is not False:
            consumer_errors.append("consumer_provider_state_mutated_not_false")
        if not consumer_digest_valid:
            consumer_errors.append("consumer_digest_invalid")

    marker_errors: list[str] = []
    marker_digest_valid = False
    if not marker:
        marker_errors.append("live_probe_idempotency_marker_missing")
    else:
        marker_digest_valid = (
            bool(marker.get("marker_digest_sha256"))
            and marker.get("marker_digest_sha256") == _marker_digest(marker)
        )
        if marker.get("record_type") != "runtime_provider_live_probe_consumption_marker":
            marker_errors.append("marker_record_type_invalid")
        if marker.get("gate_approval_id") != gate_approval_id:
            marker_errors.append("marker_gate_approval_id_mismatch")
        if marker.get("target") != target_text:
            marker_errors.append("marker_target_mismatch")
        if marker.get("selected_decision_id") != selected_decision_id:
            marker_errors.append("marker_selected_decision_id_mismatch")
        if marker.get("decision_consumer_record_written") is not True:
            marker_errors.append("marker_decision_consumer_record_written_not_true")
        if marker.get("idempotency_marker_written") is not True:
            marker_errors.append("marker_idempotency_marker_written_not_true")
        if marker.get("approval_consumed") is not False:
            marker_errors.append("marker_approval_consumed_not_false")
        if marker.get("live_network_call_attempted") is not False:
            marker_errors.append("marker_live_network_call_attempted_not_false")
        if marker.get("provider_state_mutated") is not False:
            marker_errors.append("marker_provider_state_mutated_not_false")
        if not marker_digest_valid:
            marker_errors.append("marker_digest_invalid")

    gate_operation_declared = (
        preflight.get("approval_schema", {}).get("operation") == LIVE_PROVIDER_PROBE_GATE_OPERATION
        and preflight.get("approval_schema", {}).get("approval_schema_id") == LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID
    )
    provider_setup_valid = preflight.get("valid_setup_state") is True
    secret_reference_present = preflight.get("secret_reference_present") is True
    timeout_policy_present = dict(preflight.get("timeout_values") or {}) == FallbackTimeouts().to_dict()
    approval_valid = bool(approval_validation.get("structurally_valid"))
    approval_approved = bool(approval_validation.get("approval_decision_accepted"))
    decision_consumable = bool(decision_validation.get("decision_record_consumable"))
    consumer_ready = not consumer_errors
    marker_ready = not marker_errors

    preconditions = [
        _executor_precondition(
            "executor_implemented",
            passed=False,
            status="dry_run_only",
            critical=False,
            reason="live provider probe executor is intentionally not implemented in this dry-run pass",
        ),
        _executor_precondition(
            "gate_operation_declared",
            passed=gate_operation_declared,
            reason="runtime.provider.live_probe approval schema is declared"
            if gate_operation_declared
            else "runtime.provider.live_probe approval schema is missing",
        ),
        _executor_precondition(
            "gate_operation_allows_execution",
            passed=bool(preflight.get("gate_policy_allowed")),
            critical=False,
            reason=str(preflight.get("gate_policy_reason") or "gate_denied_or_not_checked"),
        ),
        _executor_precondition(
            "approval_artifact_structurally_valid",
            passed=approval_valid,
            status="passed" if approval_valid else "failed",
            reason="approval artifact matches current live-preflight contract"
            if approval_valid
            else str(approval_validation.get("reason") or "approval artifact invalid"),
        ),
        _executor_precondition(
            "approval_status_approved",
            passed=approval_approved or decision_consumable,
            status="passed" if (approval_approved or decision_consumable) else str(approval_validation.get("approval_status") or "failed"),
            reason=(
                "approval artifact is approved"
                if approval_approved
                else (
                    "immutable approved decision record supplies approval without mutating original request artifact"
                    if decision_consumable
                    else "approval artifact is not approved"
                )
            ),
            evidence={"approval_artifact_status": approval_validation.get("approval_status")},
        ),
        _executor_precondition(
            "approved_immutable_decision_record_present",
            passed=decision_consumable,
            status="passed" if decision_consumable else str(decision_validation.get("status") or "failed"),
            reason="approved immutable decision record is consumable"
            if decision_consumable
            else "approved immutable decision record missing, denied, duplicated, or invalid",
            evidence={
                "selected_decision_id": decision_validation.get("selected_decision_id"),
                "records_found": decision_validation.get("records_found"),
            },
        ),
        _executor_precondition(
            "decision_consumer_record_valid",
            passed=consumer_ready,
            status="passed" if consumer_ready else "failed",
            reason="decision consumer record is present and valid"
            if consumer_ready
            else ", ".join(consumer_errors),
            evidence={
                "consumer_record_ref": (consumer_record or {}).get("consumer_record_ref"),
                "consumer_digest_valid": consumer_digest_valid,
            },
        ),
        _executor_precondition(
            "idempotency_marker_valid",
            passed=marker_ready,
            status="passed" if marker_ready else "failed",
            reason="idempotency marker is present and valid"
            if marker_ready
            else ", ".join(marker_errors),
            evidence={
                "marker_ref": (marker or {}).get("marker_ref") or str(marker_path),
                "marker_digest_valid": marker_digest_valid,
            },
        ),
        _executor_precondition(
            "provider_setup_valid",
            passed=provider_setup_valid,
            status="passed" if provider_setup_valid else "failed",
            reason="provider setup is valid" if provider_setup_valid else "provider setup is missing or invalid",
            evidence={"missing_setup_checks": list(preflight.get("missing_setup_checks") or [])},
        ),
        _executor_precondition(
            "secret_reference_present",
            passed=secret_reference_present,
            status="passed" if secret_reference_present else "failed",
            reason="secret reference metadata is present" if secret_reference_present else "secret reference metadata is missing",
        ),
        _executor_precondition(
            "timeout_policy_present",
            passed=timeout_policy_present,
            critical=False,
            reason="first-token, no-chunk, wall-time, and max-attempt timeout values are available",
            evidence={"timeout_values": dict(preflight.get("timeout_values") or {})},
        ),
        _executor_precondition(
            "dry_run_has_no_execution_effects",
            passed=True,
            critical=False,
            reason="dry-run performs no provider call, secret read, provider-state mutation, queue drain, or gateway restart",
        ),
    ]
    blocked_reasons = [
        str(item["reason"] or item["id"])
        for item in preconditions
        if item.get("critical") and not item.get("passed")
    ]
    readiness_status = (
        "ready_for_live_executor_implementation"
        if not blocked_reasons
        else "blocked_executor_readiness_preconditions"
    )
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_smoke_readiness_requested",
            runtime=record.runtime or runtime,
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            provider_strength=record.strength,
            decision=readiness_status,
            reason="live_probe_executor_dry_run_readiness_without_provider_call",
            files_modified=False,
            next_action=(
                "implement_gate_governed_live_probe_executor"
                if readiness_status == "ready_for_live_executor_implementation"
                else "resolve_live_probe_executor_readiness_preconditions"
            ),
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "executor_dry_run_schema_id": "rpgl.live_provider_probe_executor_dry_run.v1",
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "target": target_text,
        "runtime": runtime,
        "gate_approval_id": gate_approval_id,
        "ok": True,
        "readiness_status": readiness_status,
        "executor_status": "dry_run_readiness_only",
        "execution_enabled": False,
        "live_probe_execution_allowed": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "approval_consumed": False,
        "decision_consumed": bool((consumer_record or {}).get("decision_consumed") is True),
        "idempotency_marker_written": bool((marker or {}).get("idempotency_marker_written") is True),
        "files_modified": False,
        "provider": record.to_dict(),
        "probe_plan": probe_plan,
        "live_probe_preflight": {
            **preflight,
            "gate_approval_id": gate_approval_id,
            "approval_status": approval_validation.get("approval_status"),
        },
        "approval_validation": approval_validation,
        "decision_validation": decision_validation,
        "consumer_record": consumer_record,
        "consumer_record_ref": (consumer_record or {}).get("consumer_record_ref"),
        "consumer_record_digest_valid": consumer_digest_valid,
        "marker": marker,
        "marker_ref": (marker or {}).get("marker_ref") or str(marker_path),
        "marker_digest_valid": marker_digest_valid,
        "preconditions": preconditions,
        "blocked_reasons": blocked_reasons,
        "dry_run_steps": [
            "validate provider record and Gate operation metadata",
            "validate approval artifact against current live-preflight contract",
            "validate approved immutable decision record",
            "validate separate decision consumer record",
            "validate create-new idempotency marker",
            "verify timeout policy is present",
            "stop before any provider network call or secret read",
        ],
        "future_live_executor_requirements": [
            "require this readiness report to have no critical blocked_reasons",
            "load provider credential only through approved secret-reference mechanism",
            "write a result record before mutating provider health state",
            "enforce first-token, no-chunk, wall-time, and max-attempt timeout policy",
            "mark provider healthy/unhealthy only from bounded probe outcome",
            "never drain queues, edit config, restart gateways, or mutate canonical docs",
        ],
        "audit_id": event["event_id"],
        "next_action": (
            "implement_gate_governed_live_probe_executor"
            if readiness_status == "ready_for_live_executor_implementation"
            else "resolve_live_probe_executor_readiness_preconditions"
        ),
    }


def format_live_probe_executor_dry_run_plan(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Executor Dry Run",
        f"- target: {payload.get('target')}",
        f"- runtime: {payload.get('runtime')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- readiness_status: {payload.get('readiness_status')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- execution_enabled: {payload.get('execution_enabled')}",
        f"- live_probe_execution_allowed: {payload.get('live_probe_execution_allowed')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- idempotency_marker_written: {payload.get('idempotency_marker_written')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    blocked = payload.get("blocked_reasons") or []
    if blocked:
        lines.append("blocked_reasons:")
        for reason in blocked:
            lines.append(f"- {reason}")
    lines.append(f"- next_action: {payload.get('next_action')}")
    return "\n".join(lines)


def _load_live_probe_approval_requests(vault_root: str | Path) -> list[dict[str, Any]]:
    directory = Path(vault_root) / APPROVAL_RELATIVE_DIR
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        record = _read_json(path, {})
        if isinstance(record, dict) and record.get("record_type") == "runtime_provider_live_probe_approval_request":
            record = dict(record)
            record["approval_ref"] = str(path)
            records.append(record)
    return records


def _find_matching_live_probe_approval(
    approvals: list[dict[str, Any]],
    record: ProviderStatusRecord | None,
) -> dict[str, Any] | None:
    if record is None:
        return None
    for approval in sorted(approvals, key=lambda item: str(item.get("requested_at") or ""), reverse=True):
        if (
            approval.get("provider_id") == record.provider_id
            and approval.get("model") == record.model
            and approval.get("runtime") == record.runtime
            and approval.get("operation") == LIVE_PROVIDER_PROBE_GATE_OPERATION
        ):
            return approval
    return None


def _target_profile_probe_record(
    *,
    runtime: str,
    target: str,
    provider_id: str,
    model: str | None,
    enabled: bool = True,
) -> ProviderStatusRecord:
    strength = classify_provider_strength(provider_id, model)
    return ProviderStatusRecord(
        provider_key=_provider_key(runtime, target, provider_id, model),
        provider_id=provider_id,
        provider_name=_provider_display_name(provider_id),
        model=model,
        strength=strength,
        state="unknown" if enabled else "disabled",
        runtime=runtime,
        role=target,
        is_primary=target == "primary",
        is_fallback=target == "fallback",
        active_for_task_classes=allowed_task_classes_for_strength(strength),
        denied_task_classes=denied_task_classes_for_strength(strength),
        sticky_for_development=False,
        source="target_profile",
    )


def _target_profile_probe_records(target_profile: dict[str, Any], *, runtime: str) -> dict[str, ProviderStatusRecord]:
    primary_model = str(target_profile.get("default_primary_model") or OPERATOR_REPORTED_EXPECTED_MODEL)
    primary_provider_id = provider_id_from_model_id(primary_model) or "primary_provider"
    records = {
        "primary": _target_profile_probe_record(
            runtime=runtime,
            target="primary",
            provider_id=primary_provider_id,
            model=primary_model,
            enabled=True,
        )
    }
    local_target = target_profile.get("local_fallback_target") if isinstance(target_profile.get("local_fallback_target"), dict) else {}
    records["fallback"] = _target_profile_probe_record(
        runtime=runtime,
        target="fallback",
        provider_id=str(local_target.get("provider_id") or "local_oss"),
        model=str(local_target.get("model") or "phi4-mini:latest"),
        enabled=bool(local_target.get("enabled", False)),
    )
    return records


def _approval_matches_probe_record(approval: dict[str, Any], record: ProviderStatusRecord) -> bool:
    return (
        approval.get("provider_id") == record.provider_id
        and approval.get("model") == record.model
        and approval.get("runtime") == record.runtime
        and approval.get("operation") == LIVE_PROVIDER_PROBE_GATE_OPERATION
    )


def _find_matching_target_probe_approval(
    approvals: list[dict[str, Any]],
    record: ProviderStatusRecord,
) -> dict[str, Any] | None:
    for approval in sorted(approvals, key=lambda item: str(item.get("requested_at") or ""), reverse=True):
        if _approval_matches_probe_record(approval, record):
            return approval
    return None


def _live_probe_approval_for_gate_id(
    vault_root: str | Path,
    gate_approval_id: str | None,
) -> dict[str, Any] | None:
    if not gate_approval_id:
        return None
    for approval in _load_live_probe_approval_requests(vault_root):
        if approval.get("gate_approval_id") == gate_approval_id:
            return approval
    return None


def _live_probe_record_from_approval(
    approval: dict[str, Any] | None,
    *,
    target: str,
) -> ProviderStatusRecord | None:
    if not approval or approval.get("operation") != LIVE_PROVIDER_PROBE_GATE_OPERATION:
        return None
    provider_id = str(approval.get("provider_id") or "").strip()
    model = str(approval.get("model") or "").strip()
    runtime = str(approval.get("runtime") or "unknown").strip() or "unknown"
    if not provider_id or not model:
        return None
    target_text = str(target or "").strip().lower()
    if target_text not in {"primary", "fallback"}:
        return None
    return _target_profile_probe_record(
        runtime=runtime,
        target=target_text,
        provider_id=provider_id,
        model=model,
        enabled=approval.get("status") != "disabled",
    )


def _select_live_probe_record(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str | None = None,
) -> ProviderStatusRecord | None:
    """Resolve the provider record for a live-probe chain.

    A live-probe approval can be created from the active target profile before
    provider_state.json has been refreshed. When a gate approval is supplied,
    its provider/model/runtime tuple is the authoritative immutable intent for
    this one probe chain.
    """
    approval_record = _live_probe_record_from_approval(
        _live_probe_approval_for_gate_id(vault_root, gate_approval_id),
        target=target,
    )
    if approval_record is not None:
        return approval_record
    records = load_provider_records(vault_root)
    return (
        _select_primary_record(records, runtime=runtime)
        if str(target or "").strip().lower() == "primary"
        else _select_fallback_record(records, runtime=runtime)
    )


def build_live_probe_target_approval_plan(
    vault_root: str | Path,
    *,
    target: str = "all",
    runtime: str = "unknown",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build target-profile-aware live-probe approval templates.

    This planner is explicitly non-executing. It lets the operator generate
    approval evidence for the currently selected target model, or for another
    future target profile, without hardcoding one model family into RPGL.
    """
    target_text = str(target or "all").strip().lower()
    if target_text not in {"primary", "fallback", "all"}:
        raise RuntimeProviderGovernanceError("live probe target approval plan target must be primary, fallback, or all")
    root = Path(vault_root)
    target_profile = build_provider_target_profile(root, source_command=source_command)
    records_by_target = _target_profile_probe_records(target_profile, runtime=runtime)
    approvals = _load_live_probe_approval_requests(root)
    requested_targets = ["primary", "fallback"] if target_text == "all" else [target_text]
    candidates: list[dict[str, Any]] = []
    approval_requests_needed = 0
    matching_request_count = 0

    for candidate_target in requested_targets:
        record = records_by_target[candidate_target]
        preflight = build_live_provider_probe_preflight(root, record, runtime=runtime)
        matching_approval = _find_matching_target_probe_approval(approvals, record)
        nonmatching_approvals = [
            {
                "gate_approval_id": approval.get("gate_approval_id"),
                "provider_id": approval.get("provider_id"),
                "model": approval.get("model"),
                "runtime": approval.get("runtime"),
                "status": approval.get("status"),
                "approval_ref": approval.get("approval_ref"),
            }
            for approval in approvals
            if approval.get("operation") == LIVE_PROVIDER_PROBE_GATE_OPERATION
            and not _approval_matches_probe_record(approval, record)
        ]
        blocked_reasons: list[str] = []
        ready_for_request = True
        if candidate_target == "fallback":
            local_target = target_profile.get("local_fallback_target") if isinstance(target_profile.get("local_fallback_target"), dict) else {}
            if local_target.get("enabled") is not True:
                ready_for_request = False
                blocked_reasons.append("local_fallback_target_disabled_or_unconfigured")
            if record.strength == "weak":
                blocked_reasons.append("weak_fallback_probe_is_health_check_only_not_development_authority")
        if not record.model:
            ready_for_request = False
            blocked_reasons.append("target_model_missing")
        if matching_approval:
            matching_request_count += 1
        elif ready_for_request:
            approval_requests_needed += 1

        candidate_status = (
            "matching_approval_request_exists"
            if matching_approval
            else ("ready_for_approval_request" if ready_for_request else "blocked")
        )
        candidates.append(
            {
                "target": candidate_target,
                "candidate_status": candidate_status,
                "provider": record.to_dict(),
                "external_api_id": preflight.get("external_api_id"),
                "probe_scope": preflight.get("probe_scope"),
                "approval_request_template": preflight.get("approval_request_template"),
                "approval_schema": preflight.get("approval_schema"),
                "preflight": preflight,
                "matching_approval_request": matching_approval,
                "matching_gate_approval_id": matching_approval.get("gate_approval_id") if matching_approval else None,
                "nonmatching_approval_requests": nonmatching_approvals,
                "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
                "approval_request_written": False,
                "live_probe_execution_allowed": False,
                "live_network_call_attempted": False,
                "secret_value_read": False,
                "provider_state_mutated": False,
            }
        )

    plan_status = "ready_to_write_approval_requests" if approval_requests_needed else "no_new_approval_requests_needed"
    if any(item.get("candidate_status") == "blocked" for item in candidates) and not approval_requests_needed:
        plan_status = "blocked"
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_live_probe_target_approval_plan_requested",
            runtime=runtime,
            provider_id=records_by_target["primary"].provider_id,
            provider_name=records_by_target["primary"].provider_name,
            model=records_by_target["primary"].model,
            provider_strength=records_by_target["primary"].strength,
            task_class="provider_status_summary",
            decision=plan_status,
            reason="target_profile_live_probe_approval_plan_built_without_provider_call",
            files_modified=False,
            next_action="write_pending_target_matching_approval_requests" if approval_requests_needed else "review_existing_or_blocked_approval_posture",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "plan_schema_id": "rpgl.live_probe_target_approval_plan.v1",
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "target": target_text,
        "runtime": runtime,
        "plan_status": plan_status,
        "target_profile": target_profile,
        "target_profile_source": target_profile.get("profile_source"),
        "target_profile_exists": target_profile.get("profile_exists"),
        "active_target_primary_model": target_profile.get("default_primary_model"),
        "requested_targets": requested_targets,
        "approval_request_count": len(approvals),
        "approval_requests_needed": approval_requests_needed,
        "matching_approval_request_count": matching_request_count,
        "candidates": candidates,
        "read_only": True,
        "approval_request_written": False,
        "approval_requests_written": [],
        "write_supported": approval_requests_needed > 0,
        "denied_actions": [
            "external_provider_call",
            "secret_value_read",
            "provider_state_update",
            "queue_retry_or_drain",
            "gateway_restart",
            "provider_config_edit",
            "provider_target_profile_file_write",
            "canonical_file_write",
        ],
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "audit_id": event["event_id"],
        "next_action": "write_approval_request" if approval_requests_needed else "resolve_blockers_or_continue_approval_chain",
    }


def write_live_probe_target_approval_requests(
    vault_root: str | Path,
    *,
    target: str = "all",
    runtime: str = "unknown",
    requested_by: str = "operator",
    source_command: str | None = None,
) -> dict[str, Any]:
    """Write pending target-profile-matching live-probe approval requests only."""
    root = Path(vault_root)
    plan = build_live_probe_target_approval_plan(
        root,
        target=target,
        runtime=runtime,
        source_command=source_command,
    )
    written_requests: list[dict[str, Any]] = []
    skipped_targets: list[dict[str, Any]] = []
    for candidate in plan.get("candidates") or []:
        if candidate.get("candidate_status") != "ready_for_approval_request":
            skipped_targets.append(
                {
                    "target": candidate.get("target"),
                    "reason": candidate.get("candidate_status"),
                    "blocked_reasons": candidate.get("blocked_reasons") or [],
                    "matching_gate_approval_id": candidate.get("matching_gate_approval_id"),
                }
            )
            continue
        artifact = write_live_probe_approval_request(
            root,
            candidate.get("preflight") or {},
            requested_by=requested_by,
            source_command=source_command,
        )
        written_requests.append(artifact)

    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_live_probe_target_approval_request_created",
            runtime=runtime,
            provider_id=str((written_requests[0] if written_requests else {}).get("provider_id") or "") or None,
            provider_name=str((written_requests[0] if written_requests else {}).get("provider_name") or "") or None,
            model=(written_requests[0] if written_requests else {}).get("model"),
            decision="target_matching_approval_requests_written" if written_requests else "no_target_matching_approval_requests_written",
            reason="target_profile_live_probe_approval_request_writer_completed_without_provider_call",
            files_modified=bool(written_requests),
            next_action="operator_reviews_pending_live_probe_approval_requests" if written_requests else "resolve_blocked_or_existing_approval_posture",
            source_command=source_command,
        ),
    )
    return {
        **plan,
        "read_only": False,
        "approval_request_written": bool(written_requests),
        "approval_requests_written": written_requests,
        "approval_requests_written_count": len(written_requests),
        "skipped_targets": skipped_targets,
        "files_modified": bool(written_requests),
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "write_audit_id": event["event_id"],
        "next_action": "operator_review_required_before_live_probe_decision_records" if written_requests else plan.get("next_action"),
    }


def build_live_probe_smoke_readiness(
    vault_root: str | Path,
    *,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Report whether the final RPGL live-provider smoke can safely run now.

    This is a read-only closeout readiness report. It does not create approval
    artifacts, write decision/consumer/marker records, call providers, read
    secret values, mutate provider state, drain queues, restart gateways, or
    apply config.
    """
    root = Path(vault_root)
    config_report = build_provider_config_reconciliation(root, source_command=source_command)
    approvals = _load_live_probe_approval_requests(root)
    target_profile = build_provider_target_profile(root, source_command=source_command)
    target_records = _target_profile_probe_records(target_profile, runtime="unknown")

    readiness_targets: list[dict[str, Any]] = []
    for target in ("primary", "fallback"):
        record = target_records.get(target)
        matching_approval = _find_matching_target_probe_approval(approvals, record) if record is not None else None
        dry_run: dict[str, Any] | None = None
        result_record: dict[str, Any] | None = None
        blocked: list[str] = []
        if record is None:
            blocked.append(f"{target}_provider_not_configured")
        if matching_approval is None:
            blocked.append("matching_live_probe_approval_request_missing")
        else:
            result_record = load_live_probe_result_record(
                root,
                gate_approval_id=str(matching_approval.get("gate_approval_id")),
            )
            if result_record:
                outcome = result_record.get("probe_outcome") if isinstance(result_record.get("probe_outcome"), dict) else {}
                if not bool(outcome.get("ok")):
                    blocked.append(
                        "live_probe_result_failed:"
                        + str(outcome.get("error_type") or result_record.get("result_status") or "unknown")
                    )
            else:
                dry_run = build_live_probe_executor_dry_run_plan(
                    root,
                    target=target,
                    runtime="unknown",
                    gate_approval_id=str(matching_approval.get("gate_approval_id")),
                    source_command=source_command,
                )
                blocked.extend(str(reason) for reason in dry_run.get("blocked_reasons") or [])

        readiness_targets.append(
            {
                "target": target,
                "provider": record.to_dict() if record else None,
                "matching_approval_request": matching_approval,
                "matching_gate_approval_id": matching_approval.get("gate_approval_id") if matching_approval else None,
                "executor_dry_run": dry_run,
                "result_record": result_record,
                "result_status": result_record.get("result_status") if result_record else None,
                "verified_by_result": bool(
                    result_record
                    and isinstance(result_record.get("probe_outcome"), dict)
                    and result_record["probe_outcome"].get("ok")
                ),
                "ready_for_live_probe": bool(
                    (dry_run and not dry_run.get("blocked_reasons"))
                    or (
                        result_record
                        and isinstance(result_record.get("probe_outcome"), dict)
                        and result_record["probe_outcome"].get("ok")
                    )
                ),
                "blocked_reasons": list(dict.fromkeys(blocked)),
            }
        )

    local_fallback = config_report.get("local_fallback") if isinstance(config_report.get("local_fallback"), dict) else {}
    primary_secret_reference = _provider_secret_reference_summary(config_report, "openai")
    model_config_mismatches = [
        item
        for item in config_report.get("mismatches", [])
        if isinstance(item, dict) and item.get("type") in {
            "runtime_primary_model_mismatch",
            "setup_openai_default_model_mismatch",
        }
    ]
    global_blockers: list[str] = []
    if config_report.get("operator_truth_matches_repo") is not True:
        global_blockers.append("active_provider_target_profile_does_not_match_repo_config")
    if model_config_mismatches:
        global_blockers.append("runtime_or_setup_model_config_mismatch")
    if local_fallback.get("setup_configured") is not True and not local_fallback.get("model_config_records"):
        global_blockers.append("local_ollama_fallback_not_configured_for_live_smoke")
    if not approvals:
        global_blockers.append("no_live_probe_approval_requests_present")
    if not (root / LIVE_PROBE_DECISION_RELATIVE_DIR).exists():
        global_blockers.append("live_probe_decision_records_directory_missing")
    if not (root / LIVE_PROBE_CONSUMER_RELATIVE_DIR).exists():
        global_blockers.append("live_probe_consumer_records_directory_missing")
    if not (root / LIVE_PROBE_MARKER_RELATIVE_DIR).exists():
        global_blockers.append("live_probe_marker_directory_missing")
    if not (root / LIVE_PROBE_RESULT_RELATIVE_DIR).exists():
        global_blockers.append("live_probe_result_directory_missing")

    target_blockers = [
        f"{target['target']}:{reason}"
        for target in readiness_targets
        for reason in target.get("blocked_reasons", [])
    ]
    readiness_status = "ready_for_operator_approved_live_smoke" if not global_blockers and not target_blockers else "blocked"
    provider_secret_reference_blocked = bool(
        primary_secret_reference.get("current_secret_reference_target_is_placeholder")
        or not primary_secret_reference.get("current_secret_reference_resolvable")
    )
    next_operator_action_id = (
        "openai_secret_reference"
        if provider_secret_reference_blocked
        else (
            "run_guarded_live_probe_executor"
            if readiness_status == "ready_for_operator_approved_live_smoke"
            else "resolve_live_smoke_readiness_blockers"
        )
    )
    next_recommended_pass = (
        "operator-provide-openai-secret-reference"
        if provider_secret_reference_blocked
        else (
            "provider-live-probe-after-secret-reference"
            if readiness_status == "ready_for_operator_approved_live_smoke"
            else "resolve-live-smoke-readiness-blockers"
        )
    )
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_live_probe_smoke_readiness_requested",
            runtime="cli",
            decision=readiness_status,
            reason="live_probe_smoke_closeout_readiness_without_provider_call",
            files_modified=False,
            next_action=(
                "run_guarded_live_probe_executor"
                if readiness_status == "ready_for_operator_approved_live_smoke"
                else "resolve_live_smoke_readiness_blockers"
            ),
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "readiness_schema_id": "rpgl.live_probe_smoke_readiness.v1",
        "feature": "Runtime Provider Governance Layer",
        "generated_at": _utc_now(),
        "readiness_status": readiness_status,
        "ready_for_live_smoke": readiness_status == "ready_for_operator_approved_live_smoke",
        "safe_to_call_update_goal_complete": False,
        "no_safe_autonomous_completion_pass_available": readiness_status != "ready_for_operator_approved_live_smoke",
        "update_goal_allowed": False,
        "next_operator_action_id": next_operator_action_id,
        "next_recommended_pass": next_recommended_pass,
        "active_target_primary_model": config_report.get("active_target_primary_model")
        or config_report.get("expected_primary_model"),
        "expected_primary_model": config_report.get("expected_primary_model"),
        "target_profile_source": config_report.get("target_profile_source"),
        "target_profile_exists": config_report.get("target_profile_exists"),
        "operator_truth_matches_repo": config_report.get("operator_truth_matches_repo"),
        "provider_secret_reference": primary_secret_reference,
        "current_secret_reference_kind": primary_secret_reference.get("current_secret_reference_kind"),
        "current_secret_reference_target": primary_secret_reference.get("current_secret_reference_target"),
        "current_secret_reference_target_is_placeholder": primary_secret_reference.get(
            "current_secret_reference_target_is_placeholder"
        ),
        "current_secret_reference_resolvable": primary_secret_reference.get("current_secret_reference_resolvable"),
        "secret_reference_probe_source": primary_secret_reference.get("secret_reference_probe_source"),
        "secret_reference_probe_error": primary_secret_reference.get("secret_reference_probe_error"),
        "runtime_model_configs": config_report.get("runtime_model_configs", []),
        "local_fallback": local_fallback,
        "approval_request_count": len(approvals),
        "approval_requests": approvals,
        "targets": readiness_targets,
        "global_blockers": global_blockers,
        "target_blockers": target_blockers,
        "blocked_reasons": list(dict.fromkeys(global_blockers + target_blockers)),
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "audit_id": event["event_id"],
        "next_action": (
            "run_guarded_live_probe_executor"
            if readiness_status == "ready_for_operator_approved_live_smoke"
            else "resolve_live_smoke_readiness_blockers"
        ),
    }


def format_live_probe_smoke_readiness(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Smoke Readiness",
        f"- readiness_status: {payload.get('readiness_status')}",
        f"- ready_for_live_smoke: {payload.get('ready_for_live_smoke')}",
        f"- safe_to_call_update_goal_complete: {payload.get('safe_to_call_update_goal_complete')}",
        f"- no_safe_autonomous_completion_pass_available: {payload.get('no_safe_autonomous_completion_pass_available')}",
        f"- update_goal_allowed: {payload.get('update_goal_allowed')}",
        f"- next_operator_action: {payload.get('next_operator_action_id')}",
        f"- next_recommended_pass: {payload.get('next_recommended_pass')}",
        f"- active_target_primary_model: {payload.get('active_target_primary_model') or payload.get('expected_primary_model')}",
        f"- expected_primary_model: {payload.get('expected_primary_model')} (compatibility field)",
        f"- target_profile_source: {payload.get('target_profile_source')}",
        f"- operator_truth_matches_repo: {payload.get('operator_truth_matches_repo')}",
        (
            "- current_secret_reference: "
            f"target={payload.get('current_secret_reference_target')} "
            f"resolvable={payload.get('current_secret_reference_resolvable')} "
            f"error={payload.get('secret_reference_probe_error')}"
        ),
        f"- approval_request_count: {payload.get('approval_request_count')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    for target in payload.get("targets") or []:
        provider = target.get("provider") or {}
        lines.append(
            f"- {target.get('target')}: provider={provider.get('provider_id')} "
            f"model={provider.get('model')} ready={target.get('ready_for_live_probe')}"
        )
    blocked = payload.get("blocked_reasons") or []
    if blocked:
        lines.append("blocked_reasons:")
        for reason in blocked:
            lines.append(f"- {reason}")
    lines.append(f"- next_action: {payload.get('next_action')}")
    return "\n".join(lines)


def format_live_probe_target_approval_plan(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Target Approval Plan",
        f"- plan_status: {payload.get('plan_status')}",
        f"- target: {payload.get('target')}",
        f"- runtime: {payload.get('runtime')}",
        f"- active_target_primary_model: {payload.get('active_target_primary_model')}",
        f"- target_profile_source: {payload.get('target_profile_source')}",
        f"- approval_requests_needed: {payload.get('approval_requests_needed')}",
        f"- approval_request_written: {payload.get('approval_request_written')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    written = payload.get("approval_requests_written") or []
    if written:
        lines.append("approval_requests_written:")
        for item in written:
            lines.append(
                f"- target_model={item.get('model')} provider={item.get('provider_id')} "
                f"gate_approval_id={item.get('gate_approval_id')}"
            )
    for candidate in payload.get("candidates") or []:
        provider = candidate.get("provider") or {}
        lines.append(
            f"- {candidate.get('target')}: status={candidate.get('candidate_status')} "
            f"provider={provider.get('provider_id')} model={provider.get('model')} "
            f"external_api={candidate.get('external_api_id')}"
        )
        blocked = candidate.get("blocked_reasons") or []
        for reason in blocked:
            lines.append(f"  blocked_reason: {reason}")
    lines.append(f"- next_action: {payload.get('next_action')}")
    return "\n".join(lines)


def build_rpgl_completion_status(
    vault_root: str | Path,
    *,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build the final RPGL completion/deferred-live-proof status.

    This is intentionally read-only apart from the RPGL audit event. It does
    not write approvals, target profiles, decisions, markers, provider config,
    queue retries, or live-provider result records.
    """
    root = Path(vault_root)
    target_profile = build_provider_target_profile(root, source_command=source_command)
    config_report = build_provider_config_reconciliation(root, source_command=source_command)
    target_approval_plan = build_live_probe_target_approval_plan(
        root,
        target="all",
        runtime="unknown",
        source_command=source_command,
    )
    live_smoke = build_live_probe_smoke_readiness(root, source_command=source_command)
    queue = queue_summary(root)
    inventory = build_provider_inventory(root)
    providers = inventory.get("providers") if isinstance(inventory.get("providers"), list) else []
    primary_target = next(
        (
            item
            for item in live_smoke.get("targets", [])
            if isinstance(item, dict) and item.get("target") == "primary"
        ),
        {},
    )
    primary_provider = primary_target.get("provider") if isinstance(primary_target.get("provider"), dict) else None
    if not primary_provider:
        primary_provider = next((item for item in providers if isinstance(item, dict) and item.get("is_primary")), None)
    fallback_count = len([item for item in providers if isinstance(item, dict) and item.get("is_fallback")])
    result_records: list[dict[str, Any]] = []
    result_dir = root / LIVE_PROBE_RESULT_RELATIVE_DIR
    if result_dir.exists():
        for result_path in sorted(result_dir.glob("*.json")):
            record = _read_json(result_path, {})
            if isinstance(record, dict) and record:
                record["result_ref"] = str(result_path)
                result_records.append(record)
    primary_live_probe_verified = any(
        item.get("target") == "primary"
        and isinstance(item.get("probe_outcome"), dict)
        and bool(item["probe_outcome"].get("ok"))
        for item in result_records
    )
    primary_live_probe_attempted = any(item.get("target") == "primary" for item in result_records)
    fallback_live_probe_verified = any(
        item.get("target") == "fallback"
        and isinstance(item.get("probe_outcome"), dict)
        and bool(item["probe_outcome"].get("ok"))
        for item in result_records
    )
    fallback_live_probe_attempted = any(item.get("target") == "fallback" for item in result_records)
    last_primary_live_probe_result = next(
        (item for item in reversed(result_records) if item.get("target") == "primary"),
        None,
    )

    readiness_status = str(live_smoke.get("readiness_status") or "unknown")
    live_provider_proof_status = (
        "verified"
        if primary_live_probe_verified and fallback_live_probe_verified
        else (
            "attempted_blocked_or_failed"
            if primary_live_probe_attempted or fallback_live_probe_attempted
            else "deferred_pending_operator_approval"
        )
    )
    live_provider_proof_deferred = live_provider_proof_status != "verified"
    completion_status = (
        "complete_with_live_provider_proof"
        if live_provider_proof_status == "verified"
        else "implemented_foundation_live_provider_proof_deferred"
    )
    primary_target_model = target_profile.get("default_primary_model") or config_report.get("active_target_primary_model")
    local_fallback = config_report.get("local_fallback") if isinstance(config_report.get("local_fallback"), dict) else {}
    acceptance_criteria = [
        {"id": "canonical_rpgl_doc", "status": "passed", "evidence": "06_AGENTS/Runtime-Provider-Governance-Layer.md"},
        {"id": "provider_strength_classification", "status": "passed", "evidence": "PROVIDER_STRENGTHS"},
        {"id": "task_class_taxonomy", "status": "passed", "evidence": "HIGH_AUTHORITY_TASK_CLASSES/MEDIUM_TASK_CLASSES/WEAK_SAFE_TASK_CLASSES"},
        {"id": "weak_provider_high_authority_denial", "status": "passed", "evidence": "route_task capability gate tests"},
        {"id": "queue_high_authority_when_primary_unavailable", "status": "passed", "evidence": "provider queue and retry package tests"},
        {"id": "provider_state_and_cooldown", "status": "passed", "evidence": "provider_state.json model and cooldown tests"},
        {"id": "automatic_return_to_primary", "status": "passed", "evidence": "primary recovery and route decision tests"},
        {"id": "fallback_timeout_contract", "status": "passed_simulated_and_injected", "evidence": "fallback-timeout-proof and ollama-timeout-contract injected stream tests"},
        {"id": "fallback_not_sticky_for_development", "status": "passed", "evidence": "weak fallback denial and max attempt tests"},
        {"id": "runtime_provider_status_cli", "status": "passed", "evidence": "runtime status/providers/fallback-status/provider-status commands"},
        {"id": "queue_inspection_cli", "status": "passed", "evidence": "runtime queue list/show/retry --dry-run"},
        {"id": "recovery_dry_run_cli", "status": "passed", "evidence": "runtime recover --dry-run"},
        {"id": "hermes_openclaw_adapter_seams", "status": "passed_static", "evidence": "runtime adapter-governance rpgl_consumption checks"},
        {"id": "audit_events", "status": "passed", "evidence": "provider_audit.jsonl event schema"},
        {"id": "scheduled_night_boundaries", "status": "passed", "evidence": "recover --dry-run and denied live/apply defaults"},
        {"id": "live_openai_ollama_provider_smoke", "status": live_provider_proof_status, "evidence": "operator approval chain required before network provider calls"},
    ]
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_completion_status_requested",
            runtime="cli",
            provider_id=str((primary_provider or {}).get("provider_id") or "") or None,
            provider_name=str((primary_provider or {}).get("provider_name") or "") or None,
            model=primary_target_model,
            provider_strength="strong",
            task_class="provider_status_summary",
            decision=completion_status,
            reason="rpgl_final_completion_status_built_without_live_provider_call",
            files_modified=False,
            next_action=(
                "operator_may_accept_deferred_live_provider_proof_or_run_approved_live_smoke_chain"
                if live_provider_proof_deferred
                else "rpgl_live_provider_proof_verified"
            ),
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "completion_schema_id": "rpgl.completion_status.v1",
        "feature": FEATURE_NAME,
        "feature_abbreviation": FEATURE_ABBREVIATION,
        "generated_at": _utc_now(),
        "completion_status": completion_status,
        "feature_development_status": "complete_except_operator_approved_live_provider_proof"
        if live_provider_proof_deferred
        else "complete_verified_with_live_provider_proof",
        "remaining_major_development_passes_after_this": 0,
        "remaining_optional_operator_approval_passes": 1 if live_provider_proof_deferred else 0,
        "live_provider_proof_status": live_provider_proof_status,
        "live_provider_proof_deferred": live_provider_proof_deferred,
        "primary_live_probe_verified": primary_live_probe_verified,
        "fallback_live_probe_verified": fallback_live_probe_verified,
        "primary_live_probe_attempted": primary_live_probe_attempted,
        "fallback_live_probe_attempted": fallback_live_probe_attempted,
        "last_primary_live_probe_result": {
            "result_status": last_primary_live_probe_result.get("result_status"),
            "error_type": (last_primary_live_probe_result.get("probe_outcome") or {}).get("error_type")
            if isinstance(last_primary_live_probe_result.get("probe_outcome"), dict)
            else None,
            "reason": (last_primary_live_probe_result.get("probe_outcome") or {}).get("reason")
            if isinstance(last_primary_live_probe_result.get("probe_outcome"), dict)
            else None,
            "live_network_call_attempted": (last_primary_live_probe_result.get("probe_outcome") or {}).get("live_network_call_attempted")
            if isinstance(last_primary_live_probe_result.get("probe_outcome"), dict)
            else None,
            "secret_value_read": (last_primary_live_probe_result.get("probe_outcome") or {}).get("secret_value_read")
            if isinstance(last_primary_live_probe_result.get("probe_outcome"), dict)
            else None,
            "result_ref": last_primary_live_probe_result.get("result_ref"),
        }
        if last_primary_live_probe_result
        else None,
        "live_probe_result_record_count": len(result_records),
        "live_smoke_readiness_status": readiness_status,
        "ready_for_live_smoke": bool(live_smoke.get("ready_for_live_smoke")),
        "live_smoke_blockers": live_smoke.get("blocked_reasons") or [],
        "target_profile_exists": target_profile.get("profile_exists"),
        "target_profile_source": target_profile.get("profile_source"),
        "primary_target_model": primary_target_model,
        "current_model_target_is_configurable": True,
        "gpt_5_5_is_compatibility_default_not_hardcoded_truth": primary_target_model == LEGACY_DEFAULT_PRIMARY_MODEL
        and target_profile.get("profile_exists") is False,
        "operator_truth_matches_repo": config_report.get("operator_truth_matches_repo"),
        "local_fallback": {
            "provider_id": local_fallback.get("provider_id") or "local_oss",
            "model": local_fallback.get("model") or "phi4-mini:latest",
            "strength": local_fallback.get("strength") or "weak",
            "setup_configured": local_fallback.get("setup_configured"),
            "num_ctx": local_fallback.get("num_ctx") or LOCAL_FALLBACK_SAFE_NUM_CTX,
            "safe_num_ctx": LOCAL_FALLBACK_SAFE_NUM_CTX,
        },
        "queue_summary": queue,
        "provider_inventory_summary": {
            "primary_provider": primary_provider,
            "fallback_count": fallback_count,
            "provider_count": len(providers),
        },
        "target_approval_summary": {
            "plan_status": target_approval_plan.get("plan_status"),
            "approval_requests_needed": target_approval_plan.get("approval_requests_needed"),
            "matching_approval_request_count": target_approval_plan.get("matching_approval_request_count"),
            "candidates": [
                {
                    "target": item.get("target"),
                    "candidate_status": item.get("candidate_status"),
                    "provider_id": (item.get("provider") or {}).get("provider_id"),
                    "model": (item.get("provider") or {}).get("model"),
                    "blocked_reasons": item.get("blocked_reasons") or [],
                }
                for item in target_approval_plan.get("candidates") or []
            ],
        },
        "implemented_cli_surfaces": [
            "chaseos runtime status",
            "chaseos runtime providers",
            "chaseos runtime fallback-status",
            "chaseos runtime queue list",
            "chaseos runtime queue show <id>",
            "chaseos runtime queue retry <id> --dry-run",
            "chaseos runtime provider probe primary|fallback",
            "chaseos runtime provider target-profile",
            "chaseos runtime provider target-profile-plan [MODEL]",
            "chaseos runtime provider config-report",
            "chaseos runtime provider live-probe-target-approval-plan [primary|fallback|all]",
            "chaseos runtime provider live-smoke-readiness",
            "chaseos runtime provider live-smoke-closeout-plan",
            "chaseos runtime provider completion-status",
            "chaseos runtime recover --dry-run",
            "chaseos runtime audit-tail",
        ],
        "acceptance_criteria": acceptance_criteria,
        "denied_by_this_report": [
            "external_provider_call",
            "secret_value_read",
            "provider_state_update",
            "queue_retry_or_drain",
            "gateway_restart",
            "provider_config_edit",
            "provider_target_profile_file_write",
            "approval_decision_write",
            "approval_consumer_or_marker_write",
            "canonical_file_write",
        ],
        "read_only": True,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "audit_id": event["event_id"],
        "next_action": (
            "operator_may_accept_deferred_live_provider_proof_or_run_approved_live_smoke_chain"
            if live_provider_proof_deferred
            else "rpgl_live_provider_proof_verified"
        ),
    }


def format_rpgl_completion_status(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Completion Status",
        f"- completion_status: {payload.get('completion_status')}",
        f"- feature_development_status: {payload.get('feature_development_status')}",
        f"- remaining_major_development_passes_after_this: {payload.get('remaining_major_development_passes_after_this')}",
        f"- remaining_optional_operator_approval_passes: {payload.get('remaining_optional_operator_approval_passes')}",
        f"- live_provider_proof_status: {payload.get('live_provider_proof_status')}",
        f"- primary_live_probe_verified: {payload.get('primary_live_probe_verified')}",
        f"- fallback_live_probe_verified: {payload.get('fallback_live_probe_verified')}",
        f"- live_probe_result_record_count: {payload.get('live_probe_result_record_count')}",
        f"- live_smoke_readiness_status: {payload.get('live_smoke_readiness_status')}",
        f"- primary_target_model: {payload.get('primary_target_model')}",
        f"- target_profile_source: {payload.get('target_profile_source')}",
        f"- current_model_target_is_configurable: {payload.get('current_model_target_is_configurable')}",
        f"- read_only: {payload.get('read_only')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    local_fallback = payload.get("local_fallback") or {}
    lines.append(
        f"- local_fallback: provider={local_fallback.get('provider_id')} "
        f"model={local_fallback.get('model')} strength={local_fallback.get('strength')} "
        f"num_ctx={local_fallback.get('num_ctx')}"
    )
    blockers = payload.get("live_smoke_blockers") or []
    if blockers:
        lines.append("live_smoke_blockers:")
        for reason in blockers:
            lines.append(f"- {reason}")
    target_summary = payload.get("target_approval_summary") or {}
    lines.append(
        f"- target_approval_plan: {target_summary.get('plan_status')} "
        f"needed={target_summary.get('approval_requests_needed')}"
    )
    lines.append("acceptance_criteria:")
    for item in payload.get("acceptance_criteria") or []:
        lines.append(f"- {item.get('id')}: {item.get('status')}")
    lines.append(f"- next_action: {payload.get('next_action')}")
    return "\n".join(lines)


def build_live_smoke_closeout_plan(
    vault_root: str | Path,
    *,
    source_command: str | None = None,
) -> dict[str, Any]:
    """Build the no-mutation closeout sequence for approved RPGL live smoke."""
    root = Path(vault_root)
    readiness = build_live_probe_smoke_readiness(root, source_command=source_command)
    config_plan = build_provider_config_change_plan(root, source_command=source_command)
    blocked_reasons = list(dict.fromkeys(readiness.get("blocked_reasons") or []))
    local_fallback = readiness.get("local_fallback") if isinstance(readiness.get("local_fallback"), dict) else {}
    existing_approval_targets = [
        {
            "gate_approval_id": approval.get("gate_approval_id"),
            "provider_id": approval.get("provider_id"),
            "model": approval.get("model"),
            "runtime": approval.get("runtime"),
            "status": approval.get("status"),
            "source_command": approval.get("source_command"),
        }
        for approval in readiness.get("approval_requests") or []
        if isinstance(approval, dict)
    ]
    closeout_steps = [
        {
            "step_id": "verify_repo_truth",
            "status": "blocked" if readiness.get("operator_truth_matches_repo") is not True else "complete",
            "command": "chaseos runtime provider config-report --json",
            "writes": False,
            "reason": "confirm provider/model/local fallback truth before any approval or live probe",
        },
        {
            "step_id": "prepare_provider_config_change_request",
            "status": "required" if config_plan.get("requires_operator_approval") else "not_required",
            "command": "chaseos runtime provider config-plan --write-approval-request --requested-by operator --json",
            "writes": "approval_request_and_queue_only",
            "reason": "current runtime/setup model config does not match the active provider target profile"
            if config_plan.get("requires_operator_approval")
            else "provider config already matches the active provider target profile",
        },
        {
            "step_id": "operator_approve_provider_config_apply",
            "status": "required" if config_plan.get("requires_operator_approval") else "not_required",
            "command": "chaseos runtime provider config-apply-approval-decision <proposal_id> --gate-approval-id <id> --decision approved --write-decision --requested-by operator --json",
            "writes": "immutable_decision_record_only",
            "reason": "provider config apply requires explicit immutable operator approval before mutation",
        },
        {
            "step_id": "consume_config_apply_decision",
            "status": "required" if config_plan.get("requires_operator_approval") else "not_required",
            "command": "chaseos runtime provider config-apply-decision-consumer <proposal_id> --gate-approval-id <id> --write-consumer-record --json",
            "writes": "decision_consumer_record_only",
            "reason": "single-use apply chain must consume approved decision through a separate consumer record",
        },
        {
            "step_id": "write_config_apply_marker",
            "status": "required" if config_plan.get("requires_operator_approval") else "not_required",
            "command": "chaseos runtime provider config-apply-atomic-marker-writer <proposal_id> --gate-approval-id <id> --write-consumption-marker --json",
            "writes": "idempotency_marker_only",
            "reason": "apply executor requires create-new marker before config mutation",
        },
        {
            "step_id": "apply_provider_config_after_approval",
            "status": "blocked_until_approval_chain_complete" if config_plan.get("requires_operator_approval") else "not_required",
            "command": "chaseos runtime provider config-apply-executor <proposal_id> --gate-approval-id <id> --apply-provider-config --json",
            "writes": "approved_provider_config_targets_only",
            "reason": "do not mutate provider config until approval decision, consumer record, and marker exist",
        },
        {
            "step_id": "configure_local_ollama_fallback_metadata",
            "status": "blocked" if local_fallback.get("setup_configured") is not True else "complete",
            "command": "operator reviews local fallback config target; preserve num_ctx 16384 and do not activate weak fallback for development",
            "writes": "future_approved_config_only",
            "reason": "local Ollama fallback is not configured for live smoke"
            if local_fallback.get("setup_configured") is not True
            else "local fallback setup metadata is present",
        },
        {
            "step_id": "create_target_matching_live_probe_approval_requests",
            "status": "blocked_until_config_truth_resolved" if readiness.get("operator_truth_matches_repo") is not True else "required",
            "command": "chaseos runtime provider probe primary --probe-mode live-preflight --write-approval-request --json",
            "writes": "pending_live_probe_approval_request_only",
            "reason": "current approval requests are stale or pending for current Claude records; create approvals only after final provider targets are correct",
        },
        {
            "step_id": "operator_approve_live_probe_decisions",
            "status": "required_after_matching_approval_requests",
            "command": "chaseos runtime provider live-probe-approval-decision primary|fallback --gate-approval-id <id> --decision approved --write-decision --requested-by operator --json",
            "writes": "immutable_live_probe_decision_record_only",
            "reason": "live provider calls require explicit immutable approval decisions",
        },
        {
            "step_id": "consume_live_probe_decisions_and_markers",
            "status": "required_after_approval_decisions",
            "command": "chaseos runtime provider live-probe-decision-consumer ... --write-consumer-record; chaseos runtime provider live-probe-atomic-marker-writer ... --write-consumption-marker",
            "writes": "consumer_records_and_markers_only",
            "reason": "live probe executor requires single-use consumer records and idempotency markers",
        },
        {
            "step_id": "run_approved_live_smoke",
            "status": "blocked" if readiness.get("ready_for_live_smoke") is not True else "ready",
            "command": "chaseos runtime provider live-probe-executor primary|fallback --gate-approval-id <id> --execute-live-probe --json",
            "writes": "live_probe_result_and_provider_state_only",
            "reason": "run only after readiness has no blockers and operator approval chain is complete",
        },
    ]
    ready_for_closeout = readiness.get("ready_for_live_smoke") is True
    event = append_provider_audit_event(
        root,
        ProviderAuditEvent(
            event_type="provider_live_smoke_closeout_plan_requested",
            runtime="cli",
            decision="ready_for_live_smoke" if ready_for_closeout else "blocked_closeout_plan",
            reason="live_smoke_closeout_plan_without_provider_call_or_config_mutation",
            files_modified=False,
            next_action="run_approved_live_smoke" if ready_for_closeout else "complete_config_and_approval_chain",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "closeout_plan_schema_id": "rpgl.live_smoke_closeout_plan.v1",
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "plan_status": "ready_for_approved_live_smoke" if ready_for_closeout else "blocked_pending_config_and_approval_chain",
        "ready_for_live_smoke": ready_for_closeout,
        "readiness": readiness,
        "provider_config_change_plan": config_plan,
        "existing_live_probe_approval_targets": existing_approval_targets,
        "blocked_reasons": blocked_reasons,
        "closeout_steps": closeout_steps,
        "denied_actions": [
            "external_provider_call",
            "secret_value_read",
            "provider_state_mutation",
            "queue_drain_or_retry",
            "gateway_restart",
            "provider_config_edit",
            "approval_artifact_write",
            "decision_record_write",
            "consumer_record_write",
            "idempotency_marker_write",
            "canonical_doc_write",
        ],
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "provider_config_mutated": False,
        "approval_artifact_written": False,
        "decision_record_written": False,
        "consumer_record_written": False,
        "idempotency_marker_written": False,
        "canonical_files_mutated": False,
        "files_modified": False,
        "audit_id": event["event_id"],
        "next_action": "run_approved_live_smoke" if ready_for_closeout else "complete_config_and_approval_chain",
    }


def format_live_smoke_closeout_plan(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Smoke Closeout Plan",
        f"- plan_status: {payload.get('plan_status')}",
        f"- ready_for_live_smoke: {payload.get('ready_for_live_smoke')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- provider_config_mutated: {payload.get('provider_config_mutated')}",
        f"- approval_artifact_written: {payload.get('approval_artifact_written')}",
        f"- files_modified: {payload.get('files_modified')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("blocked_reasons:")
        for reason in blockers:
            lines.append(f"- {reason}")
    steps = payload.get("closeout_steps") or []
    if steps:
        lines.append("closeout_steps:")
        for step in steps:
            lines.append(f"- {step.get('step_id')}: {step.get('status')} command={step.get('command')}")
    lines.append(f"- next_action: {payload.get('next_action')}")
    return "\n".join(lines)


def load_live_probe_result_record(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
) -> dict[str, Any] | None:
    path = _live_probe_result_record_path(vault_root, gate_approval_id)
    if not path.exists():
        return None
    data = _read_json(path, {})
    data["result_ref"] = str(path)
    return data


def _default_live_probe_runner(
    record: ProviderStatusRecord,
    preflight: dict[str, Any],
    *,
    timeout_values: dict[str, Any],
) -> dict[str, Any]:
    """Run a minimal provider health probe without logging secret values."""
    started = datetime.now(timezone.utc)
    timeout = max(1, int(timeout_values.get("total_wall_time_sec") or FallbackTimeouts().total_wall_time_sec))
    provider_id = str(record.provider_id or "").lower()
    setup = _provider_setup_by_id().get(record.provider_id, {})
    secret_value_read = False
    live_network_call_attempted = False
    try:
        if provider_id in {"openai", "codex"}:
            secret_ref = str(setup.get("secret_reference_target") or "").strip()
            if not secret_ref or secret_ref in {"SET_OPENAI_SECRET_REF", "<env-var>", "<secret-ref>"}:
                return {
                    "ok": False,
                    "error_type": "credential_reference_unavailable",
                    "reason": "openai_secret_reference_target_is_placeholder_or_missing",
                    "live_network_call_attempted": False,
                    "secret_value_read": False,
                }
            token = os.environ.get(secret_ref)
            secret_value_read = bool(token)
            if not token:
                return {
                    "ok": False,
                    "error_type": "credential_value_unavailable",
                    "reason": "openai_secret_reference_env_var_not_set",
                    "live_network_call_attempted": False,
                    "secret_value_read": False,
                }
            request = urllib.request.Request(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {token}"},
                method="GET",
            )
            live_network_call_attempted = True
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status_code = int(getattr(response, "status", 0) or 0)
                response.read(2048)
            return {
                "ok": 200 <= status_code < 300,
                "status_code": status_code,
                "error_type": None if 200 <= status_code < 300 else f"http_{status_code}",
                "reason": "openai_models_endpoint_probe_completed",
                "live_network_call_attempted": True,
                "secret_value_read": secret_value_read,
            }
        if provider_id in {"ollama", "local_oss"}:
            endpoint = str(setup.get("endpoint_url") or setup.get("base_url") or "").strip().rstrip("/")
            if not endpoint:
                return {
                    "ok": False,
                    "error_type": "endpoint_unavailable",
                    "reason": "local_oss_endpoint_url_missing",
                    "live_network_call_attempted": False,
                    "secret_value_read": False,
                }
            url = endpoint if endpoint.endswith("/api/tags") else f"{endpoint}/api/tags"
            request = urllib.request.Request(url, method="GET")
            live_network_call_attempted = True
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status_code = int(getattr(response, "status", 0) or 0)
                response.read(2048)
            return {
                "ok": 200 <= status_code < 300,
                "status_code": status_code,
                "error_type": None if 200 <= status_code < 300 else f"http_{status_code}",
                "reason": "local_oss_tags_endpoint_probe_completed",
                "live_network_call_attempted": True,
                "secret_value_read": False,
            }
        return {
            "ok": False,
            "error_type": "unsupported_provider",
            "reason": f"live_probe_runner_not_supported_for_provider:{provider_id or 'unknown'}",
            "live_network_call_attempted": False,
            "secret_value_read": False,
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status_code": int(getattr(exc, "code", 0) or 0),
            "error_type": "rate_limited" if getattr(exc, "code", None) == 429 else f"http_{getattr(exc, 'code', 'error')}",
            "reason": "provider_http_error",
            "retry_after_seconds": _parse_retry_after_seconds(getattr(exc, "headers", {}).get("Retry-After") if getattr(exc, "headers", None) else None),
            "live_network_call_attempted": live_network_call_attempted,
            "secret_value_read": secret_value_read,
        }
    except TimeoutError:
        return {
            "ok": False,
            "error_type": "timeout",
            "reason": "provider_probe_timeout",
            "live_network_call_attempted": live_network_call_attempted,
            "secret_value_read": secret_value_read,
        }
    except OSError as exc:
        return {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "reason": "provider_probe_os_error",
            "error_message": str(exc),
            "live_network_call_attempted": live_network_call_attempted,
            "secret_value_read": secret_value_read,
        }
    finally:
        elapsed = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        preflight["last_probe_elapsed_ms"] = elapsed


def _parse_retry_after_seconds(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return max(0, int(str(value).strip()))
    except ValueError:
        return None


def _apply_live_probe_outcome_to_provider_state(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str,
    provider: dict[str, Any],
    outcome: dict[str, Any],
) -> ProviderStatusRecord:
    records = load_provider_records(vault_root)
    record = (
        _select_primary_record(records, provider_id=provider.get("provider_id"), runtime=runtime)
        if target == "primary"
        else _select_fallback_record(records, provider_id=provider.get("provider_id"), runtime=runtime)
    )
    if record is None:
        record = ProviderStatusRecord.from_dict(provider)
    now = _utc_now()
    record.last_probe_at = now
    record.sticky_for_development = False
    if bool(outcome.get("ok")):
        record.state = "healthy"
        record.last_success_at = now
        record.last_failure_at = None
        record.last_error_type = None
        record.cooldown_until = None
        if target == "primary":
            record.last_recovered_at = now
    else:
        error_type = str(outcome.get("error_type") or "provider_probe_failed")
        if target == "primary" and error_type == "rate_limited":
            retry_after = outcome.get("retry_after_seconds")
            try:
                seconds = int(retry_after) if retry_after is not None else 900
            except (TypeError, ValueError):
                seconds = 900
            record.state = "cooling_down"
            record.cooldown_until = (
                datetime.now(timezone.utc) + timedelta(seconds=max(0, seconds))
            ).isoformat().replace("+00:00", "Z")
        else:
            record.state = "unhealthy"
            record.cooldown_until = None
        record.last_failure_at = now
        record.last_error_type = error_type
    records[record.provider_key] = record
    _save_provider_records(vault_root, records)
    return record


def write_live_probe_live_executor(
    vault_root: str | Path,
    *,
    target: str,
    runtime: str = "unknown",
    gate_approval_id: str,
    source_command: str | None = None,
    probe_runner: Callable[[ProviderStatusRecord, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute one guarded live provider health probe and write a result record."""
    source = source_command or f"chaseos runtime provider live-probe-executor {target}"
    readiness = build_live_probe_executor_dry_run_plan(
        vault_root,
        target=target,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command=source,
    )
    target_text = str(target or "").strip().lower()
    provider = readiness.get("provider") if isinstance(readiness.get("provider"), dict) else {}
    result_path = _live_probe_result_record_path(vault_root, gate_approval_id)
    blocked_reasons = list(readiness.get("blocked_reasons") or [])
    if readiness.get("readiness_status") != "ready_for_live_executor_implementation":
        blocked_reasons.append("live_probe_executor_readiness_not_ready")
    if result_path.exists():
        blocked_reasons.append("live_probe_result_record_already_exists")
    if target_text not in {"primary", "fallback"}:
        blocked_reasons.append("live_probe_executor_target_invalid")
    blocked_reasons = list(dict.fromkeys(blocked_reasons))
    if blocked_reasons:
        event = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_live_probe_executor_blocked",
                runtime=str(provider.get("runtime") or runtime),
                provider_id=str(provider.get("provider_id") or "") or None,
                provider_name=str(provider.get("provider_name") or "") or None,
                model=provider.get("model"),
                provider_strength=provider.get("strength"),
                decision="blocked_live_probe_executor",
                reason="live_probe_executor_preconditions_not_ready",
                files_modified=False,
                next_action="resolve_live_probe_executor_preconditions_before_retry",
                source_command=source,
            ),
        )
        raise RuntimeProviderGovernanceError(
            "live probe executor blocked: "
            + ", ".join(blocked_reasons or ["unknown"])
            + f" (audit_id={event['event_id']})"
        )

    record = ProviderStatusRecord.from_dict(provider)
    started = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_executor_started",
            runtime=record.runtime or runtime,
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            provider_strength=record.strength,
            decision="live_probe_executor_started",
            reason="approved_live_provider_probe_started",
            files_modified=False,
            next_action="write_live_probe_result_record",
            source_command=source,
        ),
    )
    runner = probe_runner
    timeout_values = dict(readiness.get("live_probe_preflight", {}).get("timeout_values") or FallbackTimeouts().to_dict())
    if runner is None:
        outcome = _default_live_probe_runner(record, readiness.get("live_probe_preflight") or {}, timeout_values=timeout_values)
    else:
        outcome = runner(record, readiness.get("live_probe_preflight") or {})
    if not isinstance(outcome, dict):
        outcome = {"ok": False, "error_type": "invalid_probe_runner_result", "reason": "probe_runner_returned_non_dict"}
    outcome = {
        "ok": bool(outcome.get("ok")),
        "error_type": outcome.get("error_type"),
        "reason": outcome.get("reason"),
        "status_code": outcome.get("status_code"),
        "retry_after_seconds": outcome.get("retry_after_seconds"),
        "live_network_call_attempted": bool(outcome.get("live_network_call_attempted", True)),
        "secret_value_read": bool(outcome.get("secret_value_read", False)),
        "first_token_received": bool(outcome.get("first_token_received", outcome.get("ok", False))),
        "chunks_received": int(outcome.get("chunks_received", 1 if outcome.get("ok") else 0) or 0),
        "raw_error_type": outcome.get("raw_error_type"),
    }
    updated_record = _apply_live_probe_outcome_to_provider_state(
        vault_root,
        target=target_text,
        runtime=record.runtime or runtime,
        provider=provider,
        outcome=outcome,
    )
    result_status = (
        "probe_succeeded"
        if outcome["ok"]
        else "primary_rate_limited"
        if target_text == "primary" and outcome.get("error_type") == "rate_limited"
        else "probe_failed"
    )
    result = {
        "record_type": "runtime_provider_live_probe_result",
        "schema_version": SCHEMA_VERSION,
        "result_schema_id": "rpgl.live_provider_probe_result.v1",
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "gate_approval_id": gate_approval_id,
        "target": target_text,
        "runtime": runtime,
        "provider_id": record.provider_id,
        "provider_name": record.provider_name,
        "model": record.model,
        "provider_strength": record.strength,
        "selected_decision_id": readiness.get("decision_validation", {}).get("selected_decision_id"),
        "consumer_record_ref": readiness.get("consumer_record_ref"),
        "marker_ref": readiness.get("marker_ref"),
        "probe_outcome": outcome,
        "result_status": result_status,
        "provider_state_after": updated_record.to_dict(),
        "approval_consumed": False,
        "decision_consumed": bool(readiness.get("decision_consumed")),
        "decision_consumer_record_written": True,
        "idempotency_marker_written": True,
        "live_network_call_attempted": bool(outcome.get("live_network_call_attempted")),
        "secret_value_read": bool(outcome.get("secret_value_read")),
        "provider_state_mutated": True,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "result_record_written": True,
        "created_at": _utc_now(),
        "source_command": source,
        "start_audit_id": started["event_id"],
    }
    result["result_ref"] = str(result_path)
    result["result_digest_sha256"] = _marker_digest(result)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with result_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise RuntimeProviderGovernanceError(f"live probe result already exists: {result_path}") from exc

    completed = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_executor_completed",
            runtime=updated_record.runtime or runtime,
            provider_id=updated_record.provider_id,
            provider_name=updated_record.provider_name,
            model=updated_record.model,
            provider_strength=updated_record.strength,
            decision=result["result_status"],
            reason=str(outcome.get("reason") or outcome.get("error_type") or result["result_status"]),
            files_modified=True,
            next_action="operator_review_live_probe_result",
            source_command=source,
        ),
    )
    append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_live_probe_result_record_written",
            runtime=updated_record.runtime or runtime,
            provider_id=updated_record.provider_id,
            provider_name=updated_record.provider_name,
            model=updated_record.model,
            provider_strength=updated_record.strength,
            decision="result_record_written",
            reason=result["result_status"],
            files_modified=True,
            next_action="operator_review_live_probe_result",
            source_command=source,
        ),
    )
    if target_text == "primary" and outcome["ok"]:
        append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="primary_probe_succeeded",
                runtime=updated_record.runtime or runtime,
                provider_id=updated_record.provider_id,
                provider_name=updated_record.provider_name,
                model=updated_record.model,
                provider_strength=updated_record.strength,
                decision="probe_succeeded",
                reason="approved_live_probe_succeeded",
                files_modified=True,
                next_action="route_high_authority_work_to_primary",
                source_command=source,
            ),
        )
        append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="primary_recovered",
                runtime=updated_record.runtime or runtime,
                provider_id=updated_record.provider_id,
                provider_name=updated_record.provider_name,
                model=updated_record.model,
                provider_strength=updated_record.strength,
                decision="primary_recovered",
                reason="approved_live_probe_succeeded",
                files_modified=True,
                next_action="route_high_authority_work_to_primary",
                source_command=source,
            ),
        )
    elif target_text == "primary":
        append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="primary_probe_failed",
                runtime=updated_record.runtime or runtime,
                provider_id=updated_record.provider_id,
                provider_name=updated_record.provider_name,
                model=updated_record.model,
                provider_strength=updated_record.strength,
                decision=result_status,
                reason=str(outcome.get("reason") or outcome.get("error_type") or result_status),
                files_modified=True,
                next_action="keep_queued_or_wait_for_primary_recovery",
                source_command=source,
            ),
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": LIVE_PROVIDER_PROBE_GATE_OPERATION,
        "approval_schema_id": LIVE_PROVIDER_PROBE_APPROVAL_SCHEMA_ID,
        "target": target_text,
        "runtime": runtime,
        "gate_approval_id": gate_approval_id,
        "executor_status": "executed",
        "execution_enabled": True,
        "live_probe_execution_allowed": True,
        "result_status": result["result_status"],
        "probe_outcome": outcome,
        "provider_state_after": updated_record.to_dict(),
        "result_record_written": True,
        "result_ref": str(result_path),
        "result_digest_sha256": result["result_digest_sha256"],
        "approval_consumed": False,
        "decision_consumed": bool(readiness.get("decision_consumed")),
        "decision_consumer_record_written": True,
        "idempotency_marker_written": True,
        "live_network_call_attempted": bool(outcome.get("live_network_call_attempted")),
        "secret_value_read": bool(outcome.get("secret_value_read")),
        "provider_state_mutated": True,
        "queue_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": True,
        "start_audit_id": started["event_id"],
        "completion_audit_id": completed["event_id"],
        "next_action": "operator_review_live_probe_result",
    }


def format_live_probe_live_executor(payload: dict[str, Any]) -> str:
    lines = [
        "RPGL Live Provider Probe Executor",
        f"- target: {payload.get('target')}",
        f"- runtime: {payload.get('runtime')}",
        f"- gate_approval_id: {payload.get('gate_approval_id')}",
        f"- executor_status: {payload.get('executor_status')}",
        f"- result_status: {payload.get('result_status')}",
        f"- result_ref: {payload.get('result_ref')}",
        f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
        f"- secret_value_read: {payload.get('secret_value_read')}",
        f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
        f"- queue_drained: {payload.get('queue_drained')}",
        f"- gateway_mutated: {payload.get('gateway_mutated')}",
        f"- files_modified: {payload.get('files_modified')}",
        f"- next_action: {payload.get('next_action')}",
    ]
    return "\n".join(lines)


def route_task(
    vault_root: str | Path,
    *,
    task_class: str,
    original_request: str = "",
    runtime: str = "unknown",
    related_adapter: str = "unknown",
    primary_provider_id: str | None = None,
    fallback_provider_id: str | None = None,
    required_context_files: list[str] | None = None,
    source_command: str | None = None,
) -> ProviderRouteDecision:
    normalized_task = normalize_task_class(task_class)
    required = required_strength_for_task_class(normalized_task)
    records = load_provider_records(vault_root)
    primary = _select_primary_record(records, provider_id=primary_provider_id, runtime=runtime)
    fallback = _select_fallback_record(records, provider_id=fallback_provider_id, runtime=runtime)
    audit_ids: list[str] = []

    if primary is not None and primary.state in {"rate_limited", "cooling_down"} and _is_expired(primary.cooldown_until):
        probe = probe_provider(
            vault_root,
            target="primary",
            runtime=primary.runtime or runtime,
            source_command=source_command or "rpgl.route_task",
        )
        audit_ids.extend(probe.get("audit_ids") or [probe.get("audit_id")] if probe.get("audit_id") else [])
        records = load_provider_records(vault_root)
        primary = _select_primary_record(records, provider_id=primary_provider_id, runtime=runtime)

    if normalized_task == "needs_operator_approval":
        item = create_queue_item(
            vault_root,
            original_request=original_request,
            task_class=normalized_task,
            required_provider_strength="strong",
            primary_provider_id=primary.provider_id if primary else primary_provider_id,
            primary_failure_reason="task_class_unknown",
            fallback_denied_reason="fail_closed_for_unknown_task_class",
            cooldown_until=primary.cooldown_until if primary else None,
            required_context_files=required_context_files,
            related_runtime=runtime,
            related_adapter=related_adapter,
            approval_status="needs_operator_approval",
            retry_status="needs_operator_approval",
            safe_next_step="Classify the task with operator approval before provider execution.",
            source_command=source_command,
        )
        return ProviderRouteDecision(
            allowed=False,
            task_class=normalized_task,
            required_provider_strength="strong",
            decision="queued_needs_operator_approval",
            reason="unknown_task_class_fail_closed",
            route="queue",
            provider_id=primary.provider_id if primary else None,
            provider_name=primary.provider_name if primary else None,
            provider_model=primary.model if primary else None,
            provider_strength=primary.strength if primary else None,
            provider_state=primary.state if primary else None,
            fallback_denied_reason="unknown_task_class",
            queue_item_id=item.task_id,
            next_action=item.safe_next_step,
            files_modified=False,
            sticky_for_development=False,
            audit_event_ids=audit_ids,
        )

    if normalized_task in HIGH_AUTHORITY_TASK_CLASSES:
        if primary is not None and _is_primary_eligible(primary):
            return _record_to_route_decision(
                primary,
                task_class=normalized_task,
                required_strength=required,
                decision="route_primary",
                reason="strong_primary_available",
                route="primary",
                audit_event_ids=audit_ids,
            )

        fallback_reason = "weak_fallback_denied_for_high_authority_task"
        if fallback is not None:
            denied = append_provider_audit_event(
                vault_root,
                ProviderAuditEvent(
                    event_type="fallback_denied_by_capability",
                    runtime=runtime,
                    provider_id=fallback.provider_id,
                    provider_name=fallback.provider_name,
                    model=fallback.model,
                    provider_strength=fallback.strength,
                    task_class=normalized_task,
                    decision="denied",
                    reason=fallback_reason,
                    files_modified=False,
                    next_action="queue_for_primary_retry",
                    source_command=source_command,
                ),
            )
            audit_ids.append(denied["event_id"])
        primary_reason = "primary_unavailable"
        if primary is not None and primary.state in {"rate_limited", "cooling_down"}:
            primary_reason = "primary_cooling_down"
        elif primary is not None and primary.state == "unhealthy":
            primary_reason = "primary_unhealthy"
        item = create_queue_item(
            vault_root,
            original_request=original_request,
            task_class=normalized_task,
            required_provider_strength=required,
            primary_provider_id=primary.provider_id if primary else primary_provider_id,
            primary_failure_reason=primary_reason,
            fallback_denied_reason=fallback_reason,
            cooldown_until=primary.cooldown_until if primary else None,
            required_context_files=required_context_files,
            related_runtime=runtime,
            related_adapter=related_adapter,
            retry_status="waiting_for_primary",
            source_command=source_command,
        )
        queued = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="task_queued_for_primary_retry",
                runtime=runtime,
                provider_id=primary.provider_id if primary else primary_provider_id,
                provider_name=primary.provider_name if primary else None,
                model=primary.model if primary else None,
                provider_strength=required,
                task_class=normalized_task,
                decision="queued",
                reason=primary_reason,
                queue_item_id=item.task_id,
                files_modified=False,
                next_action=item.safe_next_step,
                source_command=source_command,
            ),
        )
        audit_ids.append(queued["event_id"])
        return ProviderRouteDecision(
            allowed=False,
            task_class=normalized_task,
            required_provider_strength=required,
            decision="queued_for_primary_retry",
            reason=primary_reason,
            route="queue",
            provider_id=primary.provider_id if primary else None,
            provider_name=primary.provider_name if primary else None,
            provider_model=primary.model if primary else None,
            provider_strength=primary.strength if primary else None,
            provider_state=primary.state if primary else None,
            fallback_denied_reason=fallback_reason,
            queue_item_id=item.task_id,
            next_action=item.safe_next_step,
            files_modified=False,
            sticky_for_development=False,
            audit_event_ids=audit_ids,
        )

    if fallback is not None and normalized_task in WEAK_SAFE_TASK_CLASSES and is_task_allowed_for_strength(normalized_task, fallback.strength):
        started = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="fallback_attempt_started",
                runtime=runtime,
                provider_id=fallback.provider_id,
                provider_name=fallback.provider_name,
                model=fallback.model,
                provider_strength=fallback.strength,
                task_class=normalized_task,
                decision="fallback_candidate",
                reason="weak_safe_task",
                timeout_values=FallbackTimeouts().to_dict(),
                files_modified=False,
                next_action="execute_bounded_fallback_once",
                source_command=source_command,
            ),
        )
        allowed = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="fallback_allowed_by_capability",
                runtime=runtime,
                provider_id=fallback.provider_id,
                provider_name=fallback.provider_name,
                model=fallback.model,
                provider_strength=fallback.strength,
                task_class=normalized_task,
                decision="allowed",
                reason="task_class_is_weak_safe",
                timeout_values=FallbackTimeouts().to_dict(),
                files_modified=False,
                next_action="execute_bounded_fallback_once",
                source_command=source_command,
            ),
        )
        return _record_to_route_decision(
            fallback,
            task_class=normalized_task,
            required_strength=required,
            decision="route_fallback",
            reason="fallback_allowed_for_weak_safe_task",
            route="fallback",
            allowed=True,
            audit_event_ids=[started["event_id"], allowed["event_id"]],
        )

    if primary is not None and _is_primary_eligible(primary) and is_task_allowed_for_strength(normalized_task, primary.strength):
        return _record_to_route_decision(
            primary,
            task_class=normalized_task,
            required_strength=required,
            decision="route_primary",
            reason="primary_available",
            route="primary",
            audit_event_ids=audit_ids,
        )

    item = create_queue_item(
        vault_root,
        original_request=original_request,
        task_class=normalized_task,
        required_provider_strength=required,
        primary_provider_id=primary.provider_id if primary else primary_provider_id,
        primary_failure_reason="no_authorized_provider_available",
        fallback_denied_reason="provider_strength_or_state_not_authorized",
        cooldown_until=primary.cooldown_until if primary else None,
        required_context_files=required_context_files,
        related_runtime=runtime,
        related_adapter=related_adapter,
        source_command=source_command,
    )
    return ProviderRouteDecision(
        allowed=False,
        task_class=normalized_task,
        required_provider_strength=required,
        decision="queued_no_authorized_provider",
        reason="no_authorized_provider_available",
        route="queue",
        provider_id=primary.provider_id if primary else None,
        provider_name=primary.provider_name if primary else None,
        provider_model=primary.model if primary else None,
        provider_strength=primary.strength if primary else None,
        provider_state=primary.state if primary else None,
        fallback_denied_reason="provider_strength_or_state_not_authorized",
        queue_item_id=item.task_id,
        next_action=item.safe_next_step,
        files_modified=False,
        sticky_for_development=False,
        audit_event_ids=audit_ids,
    )


def evaluate_fallback_timeout(
    *,
    chunks_received: int,
    total_elapsed_sec: float,
    first_token_elapsed_sec: float | None = None,
    last_chunk_elapsed_sec: float | None = None,
    timeouts: FallbackTimeouts | None = None,
) -> str | None:
    policy = timeouts or FallbackTimeouts()
    if total_elapsed_sec >= policy.total_wall_time_sec:
        return "fallback_timeout_wall_time"
    if chunks_received <= 0:
        elapsed = first_token_elapsed_sec if first_token_elapsed_sec is not None else total_elapsed_sec
        if elapsed >= policy.no_chunk_timeout_sec:
            return "fallback_timeout_no_chunks"
        if elapsed >= policy.first_token_timeout_sec:
            return "fallback_timeout_first_token"
        return None
    if last_chunk_elapsed_sec is not None and last_chunk_elapsed_sec >= policy.no_chunk_timeout_sec:
        return "fallback_timeout_no_chunks"
    return None


def record_fallback_timeout(
    vault_root: str | Path,
    *,
    provider_id: str | None,
    model: str | None,
    task_class: str,
    timeout_event_type: str,
    runtime: str = "unknown",
    source_command: str | None = None,
    timeouts: FallbackTimeouts | None = None,
) -> dict[str, Any]:
    if timeout_event_type not in {
        "fallback_timeout_first_token",
        "fallback_timeout_no_chunks",
        "fallback_timeout_wall_time",
    }:
        raise RuntimeProviderGovernanceError(f"Unsupported fallback timeout event: {timeout_event_type}")
    records = load_provider_records(vault_root)
    provider_id = provider_id or provider_id_from_model_id(model) or "local_oss"
    record = _select_fallback_record(records, provider_id=provider_id, runtime=runtime)
    if record is None:
        strength = classify_provider_strength(provider_id, model)
        record = ProviderStatusRecord(
            provider_key=_provider_key(runtime, "fallback", provider_id, model),
            provider_id=provider_id,
            provider_name=_provider_display_name(provider_id),
            model=model,
            strength=strength,
            runtime=runtime,
            role="fallback",
            is_primary=False,
            is_fallback=True,
            active_for_task_classes=allowed_task_classes_for_strength(strength),
            denied_task_classes=denied_task_classes_for_strength(strength),
            source="rpgl",
        )
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type=timeout_event_type,
            runtime=runtime,
            provider_id=record.provider_id,
            provider_name=record.provider_name,
            model=record.model,
            provider_strength=record.strength,
            task_class=normalize_task_class(task_class),
            decision="abort_fallback",
            reason=timeout_event_type,
            timeout_values=(timeouts or FallbackTimeouts()).to_dict(),
            files_modified=False,
            next_action="mark_fallback_unhealthy" if timeout_event_type == "fallback_timeout_no_chunks" else "do_not_retry_fallback",
            source_command=source_command,
        ),
    )
    marked = None
    if timeout_event_type == "fallback_timeout_no_chunks":
        record.state = "unhealthy"
        record.last_failure_at = _utc_now()
        record.last_error_type = "no_chunk_timeout"
        record.last_no_chunk_timeout_at = record.last_failure_at
        record.sticky_for_development = False
        records[record.provider_key] = record
        _save_provider_records(vault_root, records)
        marked = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="fallback_marked_unhealthy",
                runtime=runtime,
                provider_id=record.provider_id,
                provider_name=record.provider_name,
                model=record.model,
                provider_strength=record.strength,
                task_class=normalize_task_class(task_class),
                decision="fallback_unhealthy",
                reason="no_chunk_timeout",
                timeout_values=(timeouts or FallbackTimeouts()).to_dict(),
                files_modified=False,
                next_action="do_not_route_until_recovered",
                source_command=source_command,
            ),
        )
    return {
        "timeout_event": event,
        "fallback_marked_unhealthy_event": marked,
        "provider": record.to_dict(),
    }


FALLBACK_TIMEOUT_PROOF_SCENARIOS = (
    "first-token",
    "no-chunks",
    "wall-time",
    "post-chunk-no-chunks",
)


def _fallback_timeout_proof_observation(
    scenario: str,
    timeouts: FallbackTimeouts,
) -> dict[str, Any]:
    scenario_text = str(scenario or "").strip().lower().replace("_", "-")
    if scenario_text == "first-token":
        return {
            "scenario": scenario_text,
            "chunks_received": 0,
            "total_elapsed_sec": timeouts.first_token_timeout_sec + 1,
            "first_token_elapsed_sec": timeouts.first_token_timeout_sec + 1,
            "last_chunk_elapsed_sec": None,
            "expected_timeout_event_type": "fallback_timeout_first_token",
            "description": "simulated stream emits no visible first token past first-token timeout",
        }
    if scenario_text == "no-chunks":
        return {
            "scenario": scenario_text,
            "chunks_received": 0,
            "total_elapsed_sec": timeouts.no_chunk_timeout_sec + 1,
            "first_token_elapsed_sec": timeouts.no_chunk_timeout_sec + 1,
            "last_chunk_elapsed_sec": None,
            "expected_timeout_event_type": "fallback_timeout_no_chunks",
            "description": "simulated stream emits no chunks past no-chunk timeout",
        }
    if scenario_text == "wall-time":
        return {
            "scenario": scenario_text,
            "chunks_received": 1,
            "total_elapsed_sec": timeouts.total_wall_time_sec + 1,
            "first_token_elapsed_sec": 1,
            "last_chunk_elapsed_sec": 1,
            "expected_timeout_event_type": "fallback_timeout_wall_time",
            "description": "simulated stream exceeds total wall-time budget",
        }
    if scenario_text == "post-chunk-no-chunks":
        return {
            "scenario": scenario_text,
            "chunks_received": 1,
            "total_elapsed_sec": timeouts.no_chunk_timeout_sec + 5,
            "first_token_elapsed_sec": 1,
            "last_chunk_elapsed_sec": timeouts.no_chunk_timeout_sec + 1,
            "expected_timeout_event_type": "fallback_timeout_no_chunks",
            "description": "simulated stream emits one chunk, then stalls past no-chunk timeout",
        }
    raise RuntimeProviderGovernanceError(
        "Unsupported fallback timeout proof scenario: "
        f"{scenario!r}; expected one of {', '.join(FALLBACK_TIMEOUT_PROOF_SCENARIOS)}"
    )


def run_fallback_timeout_proof(
    vault_root: str | Path,
    *,
    scenario: str = "no-chunks",
    runtime: str = "unknown",
    provider_id: str | None = "local_oss",
    model: str | None = "phi4-mini:latest",
    task_class: str = "summarize_failure",
    source_command: str | None = None,
    timeouts: FallbackTimeouts | None = None,
) -> dict[str, Any]:
    """Run a deterministic local fallback timeout proof without provider I/O."""
    policy = timeouts or FallbackTimeouts()
    observation = _fallback_timeout_proof_observation(scenario, policy)
    timeout_event_type = evaluate_fallback_timeout(
        chunks_received=int(observation["chunks_received"]),
        total_elapsed_sec=float(observation["total_elapsed_sec"]),
        first_token_elapsed_sec=observation.get("first_token_elapsed_sec"),
        last_chunk_elapsed_sec=observation.get("last_chunk_elapsed_sec"),
        timeouts=policy,
    )
    source = source_command or f"chaseos runtime provider fallback-timeout-proof {observation['scenario']}"
    requested = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="fallback_timeout_proof_requested",
            runtime=runtime,
            provider_id=provider_id,
            provider_name=_provider_display_name(provider_id or provider_id_from_model_id(model) or "local_oss"),
            model=model,
            provider_strength=classify_provider_strength(provider_id, model),
            task_class=normalize_task_class(task_class),
            decision="simulated_timeout_proof",
            reason=str(observation["description"]),
            timeout_values=policy.to_dict(),
            files_modified=False,
            next_action="record_fallback_timeout_event",
            source_command=source,
        ),
    )
    if timeout_event_type != observation["expected_timeout_event_type"]:
        raise RuntimeProviderGovernanceError(
            "Fallback timeout proof scenario did not resolve to expected event: "
            f"expected={observation['expected_timeout_event_type']} actual={timeout_event_type}"
        )
    recorded = record_fallback_timeout(
        vault_root,
        provider_id=provider_id,
        model=model,
        task_class=task_class,
        timeout_event_type=str(timeout_event_type),
        runtime=runtime,
        source_command=source,
        timeouts=policy,
    )
    provider = recorded["provider"]
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "proof_type": "simulated_local_fallback_timeout",
        "scenario": observation["scenario"],
        "runtime": runtime,
        "provider_id": provider.get("provider_id"),
        "provider_name": provider.get("provider_name"),
        "model": provider.get("model"),
        "provider_strength": provider.get("strength"),
        "task_class": normalize_task_class(task_class),
        "timeout_values": policy.to_dict(),
        "simulated_stream": True,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "wall_clock_wait_performed": False,
        "chunks_received": observation["chunks_received"],
        "total_elapsed_sec": observation["total_elapsed_sec"],
        "first_token_elapsed_sec": observation["first_token_elapsed_sec"],
        "last_chunk_elapsed_sec": observation["last_chunk_elapsed_sec"],
        "timeout_event_type": timeout_event_type,
        "fallback_marked_unhealthy": bool(recorded.get("fallback_marked_unhealthy_event")),
        "provider_state_after": provider,
        "provider_state_mutated": timeout_event_type == "fallback_timeout_no_chunks",
        "queue_drained": False,
        "gateway_mutated": False,
        "canonical_files_mutated": False,
        "files_modified": timeout_event_type == "fallback_timeout_no_chunks",
        "audit_ids": [
            requested["event_id"],
            recorded["timeout_event"]["event_id"],
            *(
                [recorded["fallback_marked_unhealthy_event"]["event_id"]]
                if recorded.get("fallback_marked_unhealthy_event")
                else []
            ),
        ],
        "next_action": (
            "do_not_route_to_fallback_until_recovered"
            if timeout_event_type == "fallback_timeout_no_chunks"
            else "do_not_retry_weak_fallback_for_same_task"
        ),
    }


def format_fallback_timeout_proof(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "RPGL Local Fallback Timeout Proof",
            f"- scenario: {payload.get('scenario')}",
            f"- runtime: {payload.get('runtime')}",
            f"- provider: {payload.get('provider_id')} model={payload.get('model')}",
            f"- timeout_event_type: {payload.get('timeout_event_type')}",
            f"- fallback_marked_unhealthy: {payload.get('fallback_marked_unhealthy')}",
            f"- simulated_stream: {payload.get('simulated_stream')}",
            f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
            f"- secret_value_read: {payload.get('secret_value_read')}",
            f"- wall_clock_wait_performed: {payload.get('wall_clock_wait_performed')}",
            f"- provider_state_mutated: {payload.get('provider_state_mutated')}",
            f"- queue_drained: {payload.get('queue_drained')}",
            f"- gateway_mutated: {payload.get('gateway_mutated')}",
            f"- files_modified: {payload.get('files_modified')}",
            f"- next_action: {payload.get('next_action')}",
        ]
    )


OLLAMA_STREAM_CONTRACT_SCENARIOS = (
    "success",
    "first-token",
    "no-chunks",
    "wall-time",
    "post-chunk-no-chunks",
)


def _ollama_stream_contract_events(scenario: str, timeouts: FallbackTimeouts) -> list[dict[str, Any]]:
    scenario_text = str(scenario or "").strip().lower().replace("_", "-")
    if scenario_text == "success":
        return [
            {"elapsed_sec": 1, "content": "Recovered", "done": False},
            {"elapsed_sec": 2, "content": " summary.", "done": True},
        ]
    if scenario_text == "first-token":
        return [{"elapsed_sec": timeouts.first_token_timeout_sec + 1, "content": "", "done": False}]
    if scenario_text == "no-chunks":
        return [{"elapsed_sec": timeouts.no_chunk_timeout_sec + 1, "content": "", "done": False}]
    if scenario_text == "wall-time":
        return [
            {"elapsed_sec": 1, "content": "Partial", "done": False},
            {"elapsed_sec": timeouts.total_wall_time_sec + 1, "content": "", "done": False},
        ]
    if scenario_text == "post-chunk-no-chunks":
        return [
            {"elapsed_sec": 1, "content": "Partial", "done": False},
            {"elapsed_sec": timeouts.no_chunk_timeout_sec + 2, "content": "", "done": False},
        ]
    raise RuntimeProviderGovernanceError(
        "Unsupported Ollama stream contract scenario: "
        f"{scenario!r}; expected one of {', '.join(OLLAMA_STREAM_CONTRACT_SCENARIOS)}"
    )


def execute_local_ollama_fallback_stream(
    vault_root: str | Path,
    *,
    prompt: str,
    task_class: str = "summarize_failure",
    runtime: str = "unknown",
    provider_id: str = "local_oss",
    model: str = "phi4-mini:latest",
    stream_runner: Callable[[dict[str, Any]], Iterable[dict[str, Any]]] | None = None,
    source_command: str | None = None,
    timeouts: FallbackTimeouts | None = None,
    num_ctx: int = LOCAL_FALLBACK_SAFE_NUM_CTX,
) -> dict[str, Any]:
    policy = timeouts or FallbackTimeouts()
    normalized_task = normalize_task_class(task_class)
    provider_strength = classify_provider_strength(provider_id, model)
    allowed = is_task_allowed_for_strength(normalized_task, provider_strength)
    request_payload = {
        "provider": "ollama",
        "endpoint_policy": "localhost_only_not_called_by_default",
        "model": model,
        "stream": True,
        "prompt": prompt,
        "options": {"num_ctx": min(int(num_ctx), LOCAL_FALLBACK_SAFE_NUM_CTX)},
    }
    source = source_command or "chaseos runtime provider ollama-timeout-contract"
    started = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="fallback_attempt_started",
            runtime=runtime,
            provider_id=provider_id,
            provider_name=_provider_display_name(provider_id),
            model=model,
            provider_strength=provider_strength,
            task_class=normalized_task,
            decision="ollama_stream_contract_started",
            reason="injected_stream_runner" if stream_runner else "live_ollama_runner_not_configured",
            timeout_values=policy.to_dict(),
            files_modified=False,
            next_action="evaluate_stream_timeouts",
            source_command=source,
        ),
    )
    if not allowed:
        denied = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="fallback_denied_by_capability",
                runtime=runtime,
                provider_id=provider_id,
                provider_name=_provider_display_name(provider_id),
                model=model,
                provider_strength=provider_strength,
                task_class=normalized_task,
                decision="fallback_denied",
                reason="task_not_allowed_for_local_ollama_fallback",
                files_modified=False,
                next_action="queue_or_use_primary",
                source_command=source,
            ),
        )
        return {
            "ok": False,
            "reason": "task_not_allowed_for_local_ollama_fallback",
            "audit_ids": [started["event_id"], denied["event_id"]],
            "request_payload": request_payload,
            "dry_run": True,
            "live_network_call_attempted": False,
            "secret_value_read": False,
            "provider_state_mutated": False,
            "canonical_files_mutated": False,
            "files_modified": False,
        }
    if stream_runner is None:
        blocked = append_provider_audit_event(
            vault_root,
            ProviderAuditEvent(
                event_type="provider_state_updated",
                runtime=runtime,
                provider_id=provider_id,
                provider_name=_provider_display_name(provider_id),
                model=model,
                provider_strength=provider_strength,
                task_class=normalized_task,
                decision="ollama_stream_contract_blocked",
                reason="live_ollama_runner_not_configured",
                files_modified=False,
                next_action="inject_runner_or_request_live_ollama_approval",
                source_command=source,
            ),
        )
        return {
            "ok": False,
            "reason": "live_ollama_runner_not_configured",
            "audit_ids": [started["event_id"], blocked["event_id"]],
            "request_payload": request_payload,
            "dry_run": True,
            "live_network_call_attempted": False,
            "secret_value_read": False,
            "provider_state_mutated": False,
            "canonical_files_mutated": False,
            "files_modified": False,
        }

    chunks: list[str] = []
    first_chunk_at: float | None = None
    last_chunk_at: float | None = None
    total_elapsed = 0.0
    audit_ids = [started["event_id"]]
    timeout_event_type: str | None = None
    events_seen = 0
    for event in stream_runner(request_payload):
        events_seen += 1
        total_elapsed = float(event.get("elapsed_sec") or total_elapsed)
        content = str(event.get("content") or "")
        if content:
            chunks.append(content)
            if first_chunk_at is None:
                first_chunk_at = total_elapsed
            last_chunk_at = total_elapsed
        last_chunk_elapsed = None if last_chunk_at is None else max(0.0, total_elapsed - last_chunk_at)
        timeout_event_type = evaluate_fallback_timeout(
            chunks_received=len(chunks),
            total_elapsed_sec=total_elapsed,
            first_token_elapsed_sec=total_elapsed if first_chunk_at is None else first_chunk_at,
            last_chunk_elapsed_sec=last_chunk_elapsed,
            timeouts=policy,
        )
        if timeout_event_type:
            recorded = record_fallback_timeout(
                vault_root,
                provider_id=provider_id,
                model=model,
                task_class=normalized_task,
                timeout_event_type=timeout_event_type,
                runtime=runtime,
                source_command=source,
                timeouts=policy,
            )
            audit_ids.append(recorded["timeout_event"]["event_id"])
            if recorded.get("fallback_marked_unhealthy_event"):
                audit_ids.append(recorded["fallback_marked_unhealthy_event"]["event_id"])
            return {
                "ok": False,
                "reason": timeout_event_type,
                "timeout_event_type": timeout_event_type,
                "request_payload": request_payload,
                "chunks_received": len(chunks),
                "events_seen": events_seen,
                "content": "".join(chunks),
                "total_elapsed_sec": total_elapsed,
                "first_token_elapsed_sec": first_chunk_at,
                "last_chunk_elapsed_sec": last_chunk_elapsed,
                "timeout_values": policy.to_dict(),
                "audit_ids": audit_ids,
                "dry_run": False,
                "injected_stream_runner_used": True,
                "live_network_call_attempted": False,
                "secret_value_read": False,
                "provider_state_mutated": timeout_event_type == "fallback_timeout_no_chunks",
                "canonical_files_mutated": False,
                "queue_drained": False,
                "gateway_mutated": False,
                "files_modified": timeout_event_type == "fallback_timeout_no_chunks",
                "fallback_sticky_for_development": False,
            }
        if bool(event.get("done")):
            break

    completed = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_state_updated",
            runtime=runtime,
            provider_id=provider_id,
            provider_name=_provider_display_name(provider_id),
            model=model,
            provider_strength=provider_strength,
            task_class=normalized_task,
            decision="ollama_stream_contract_completed",
            reason="stream_completed_without_timeout",
            timeout_values=policy.to_dict(),
            files_modified=False,
            next_action="return_recovery_summary_only",
            source_command=source,
        ),
    )
    audit_ids.append(completed["event_id"])
    return {
        "ok": True,
        "reason": "stream_completed_without_timeout",
        "timeout_event_type": None,
        "request_payload": request_payload,
        "chunks_received": len(chunks),
        "events_seen": events_seen,
        "content": "".join(chunks),
        "total_elapsed_sec": total_elapsed,
        "first_token_elapsed_sec": first_chunk_at,
        "last_chunk_elapsed_sec": None if last_chunk_at is None else max(0.0, total_elapsed - last_chunk_at),
        "timeout_values": policy.to_dict(),
        "audit_ids": audit_ids,
        "dry_run": False,
        "injected_stream_runner_used": True,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "canonical_files_mutated": False,
        "queue_drained": False,
        "gateway_mutated": False,
        "files_modified": False,
        "fallback_sticky_for_development": False,
    }


def run_ollama_timeout_contract(
    vault_root: str | Path,
    *,
    scenario: str = "success",
    runtime: str = "unknown",
    prompt: str = "Summarize the fallback failure and prepare a retry note.",
    task_class: str = "summarize_failure",
    provider_id: str = "local_oss",
    model: str = "phi4-mini:latest",
    source_command: str | None = None,
    timeouts: FallbackTimeouts | None = None,
) -> dict[str, Any]:
    policy = timeouts or FallbackTimeouts()
    scenario_text = str(scenario or "").strip().lower().replace("_", "-")
    events = _ollama_stream_contract_events(scenario_text, policy)

    def runner(_: dict[str, Any]) -> Iterable[dict[str, Any]]:
        return iter(events)

    payload = execute_local_ollama_fallback_stream(
        vault_root,
        prompt=prompt,
        task_class=task_class,
        runtime=runtime,
        provider_id=provider_id,
        model=model,
        stream_runner=runner,
        source_command=source_command or f"chaseos runtime provider ollama-timeout-contract {scenario_text}",
        timeouts=policy,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "proof_type": "local_ollama_stream_timeout_contract",
        "scenario": scenario_text,
        "simulated_stream": True,
        "wall_clock_wait_performed": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "request_payload": payload.get("request_payload"),
        "result": payload,
    }


def format_ollama_timeout_contract(payload: dict[str, Any]) -> str:
    result = payload.get("result") or {}
    return "\n".join(
        [
            "RPGL Local Ollama Timeout Contract",
            f"- scenario: {payload.get('scenario')}",
            f"- ok: {result.get('ok')}",
            f"- timeout_event_type: {result.get('timeout_event_type')}",
            f"- chunks_received: {result.get('chunks_received')}",
            f"- simulated_stream: {payload.get('simulated_stream')}",
            f"- live_network_call_attempted: {payload.get('live_network_call_attempted')}",
            f"- secret_value_read: {payload.get('secret_value_read')}",
            f"- wall_clock_wait_performed: {payload.get('wall_clock_wait_performed')}",
            f"- provider_state_mutated: {result.get('provider_state_mutated')}",
            f"- files_modified: {result.get('files_modified')}",
        ]
    )


def build_runtime_adapter_status(vault_root: str | Path) -> list[dict[str, Any]]:
    try:
        capabilities = load_all_capabilities(vault_root)
    except (CapabilityError, OSError):
        return [
            RuntimeAdapterStatus(
                runtime="unknown",
                bus_name="unknown",
                status="unknown",
                source="capabilities_unavailable",
            ).to_dict()
        ]
    return [
        RuntimeAdapterStatus(
            runtime=caps.runtime_name,
            bus_name=caps.bus_name,
            status="configured",
            last_seen=None,
            source="capabilities",
        ).to_dict()
        for caps in sorted(capabilities.values(), key=lambda item: item.bus_name)
    ]


def build_governance_status(vault_root: str | Path, *, audit_limit: int = 10) -> dict[str, Any]:
    records = load_provider_records(vault_root)
    primary = _select_primary_record(records)
    fallback_records = sorted([record for record in records.values() if record.is_fallback], key=lambda item: item.provider_key)
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="runtime_status_requested",
            runtime="cli",
            decision="status_read",
            reason="operator_requested_runtime_provider_status",
            files_modified=False,
            next_action="none",
            source_command="chaseos runtime status",
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "abbreviation": FEATURE_ABBREVIATION,
        "generated_at": _utc_now(),
        "read_only": True,
        "audit_id": event["event_id"],
        "primary_provider": primary.to_dict() if primary else None,
        "fallback_providers": [record.to_dict() for record in fallback_records],
        "providers": [record.to_dict() for record in sorted(records.values(), key=lambda item: item.provider_key)],
        "timeout_defaults": FallbackTimeouts().to_dict(),
        "queue": queue_summary(vault_root),
        "runtime_adapters": build_runtime_adapter_status(vault_root),
        "recent_audit_events": load_provider_audit_events(vault_root, limit=audit_limit),
        "boundaries": {
            "weak_fallback_sticky_for_development": False,
            "scheduled_recovery_mode": "dry_run_only",
            "canonical_doc_write_by_weak_fallback": "denied",
            "queue_drains_automatically": False,
        },
    }


def build_provider_inventory(vault_root: str | Path) -> dict[str, Any]:
    records = load_provider_records(vault_root)
    event = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="provider_status_requested",
            runtime="cli",
            decision="provider_inventory_read",
            reason="operator_requested_provider_inventory",
            files_modified=False,
            next_action="none",
            source_command="chaseos runtime providers",
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "audit_id": event["event_id"],
        "providers": [record.to_dict() for record in sorted(records.values(), key=lambda item: item.provider_key)],
        "authority_matrix": AUTHORITY_MATRIX,
        "task_classes": {
            "high_authority_strong_only": sorted(HIGH_AUTHORITY_TASK_CLASSES),
            "medium_conditional": sorted(MEDIUM_TASK_CLASSES),
            "weak_safe": sorted(WEAK_SAFE_TASK_CLASSES),
        },
    }


def build_fallback_status(vault_root: str | Path) -> dict[str, Any]:
    records = load_provider_records(vault_root)
    fallbacks = sorted([record for record in records.values() if record.is_fallback], key=lambda item: item.provider_key)
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "fallback_providers": [record.to_dict() for record in fallbacks],
        "timeout_defaults": FallbackTimeouts().to_dict(),
        "sticky_for_development": False,
    }


def build_audit_tail(vault_root: str | Path, *, limit: int = 10) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "generated_at": _utc_now(),
        "audit_path": str(audit_path(vault_root)),
        "events": load_provider_audit_events(vault_root, limit=limit),
    }


def run_recovery_dry_run(vault_root: str | Path, *, source_command: str = "chaseos runtime recover --dry-run") -> dict[str, Any]:
    started = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="scheduled_recovery_dry_run_started",
            runtime="cli",
            decision="dry_run_started",
            reason="operator_requested_recovery_dry_run",
            files_modified=False,
            next_action="inspect_provider_state_and_queue",
            source_command=source_command,
        ),
    )
    records = load_provider_records(vault_root)
    primaries = [record for record in records.values() if record.is_primary]
    cooldown_expired = [
        record.to_dict()
        for record in primaries
        if record.state in {"rate_limited", "cooling_down"} and _is_expired(record.cooldown_until)
    ]
    provider_probe_plans = [
        build_provider_probe_plan(vault_root, record, probe_mode="network-dry-run")
        for record in primaries
        if record.state in {"rate_limited", "cooling_down"} and _is_expired(record.cooldown_until)
    ]
    queue = queue_summary(vault_root)
    ready_queue = []
    retry_packages = []
    for item in load_queue_items(vault_root):
        primary = _select_primary_record(records, provider_id=item.primary_provider_id, runtime=item.related_runtime)
        if primary is not None and _is_primary_eligible(primary):
            ready_queue.append(item.to_dict())
        if item.retry_status in {"queued", "waiting_for_primary", "ready_for_retry", "needs_operator_approval"}:
            retry_packages.append(
                build_queue_retry_package_dry_run(
                    vault_root,
                    item,
                    records=records,
                    source_command=source_command,
                )
            )
    completed = append_provider_audit_event(
        vault_root,
        ProviderAuditEvent(
            event_type="scheduled_recovery_dry_run_completed",
            runtime="cli",
            decision="dry_run_completed",
            reason="recovery_dry_run_no_queue_drain",
            files_modified=False,
            next_action="probe_primary_or_operator_retry" if cooldown_expired or ready_queue else "none",
            source_command=source_command,
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "feature": FEATURE_NAME,
        "dry_run": True,
        "started_audit_id": started["event_id"],
        "completed_audit_id": completed["event_id"],
        "provider_state_mutated": False,
        "canonical_files_mutated": False,
        "cooldown_expired_primaries": cooldown_expired,
        "provider_probe_plans": provider_probe_plans,
        "queue_summary": queue,
        "ready_queue_items": ready_queue,
        "retry_packages": retry_packages,
        "queue_state_mutated": False,
        "queue_drained": False,
        "live_provider_call_attempted": False,
        "secret_value_read": False,
        "denied_actions": [
            "apply_code_patches",
            "edit_provider_config",
            "restart_gateways",
            "push_git_commits",
            "drain_high_complexity_queue_without_approval",
        ],
    }


def format_governance_status(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Governance"]
    primary = payload.get("primary_provider") or {}
    if primary:
        lines.extend(
            [
                "Primary provider:",
                f"  provider_id: {primary.get('provider_id')}",
                f"  model: {primary.get('model')}",
                f"  strength: {primary.get('strength')}",
                f"  state: {primary.get('state')}",
                f"  cooldown_until: {primary.get('cooldown_until')}",
                f"  high_complexity_eligible: {_is_primary_eligible(ProviderStatusRecord.from_dict(primary))}",
            ]
        )
    else:
        lines.extend(["Primary provider:", "  status: unknown"])
    lines.append("Fallback providers:")
    fallbacks = payload.get("fallback_providers") or []
    if not fallbacks:
        lines.append("  none configured")
    for record in fallbacks:
        lines.append(f"  - {record.get('provider_id')} model={record.get('model')} strength={record.get('strength')} state={record.get('state')}")
        lines.append(f"    sticky_for_development: {record.get('sticky_for_development')}")
        lines.append(f"    allowed_task_classes: {', '.join(record.get('active_for_task_classes') or [])}")
    queue = payload.get("queue") or {}
    lines.extend(
        [
            "Queue:",
            f"  queued_task_count: {queue.get('queued_task_count', 0)}",
            f"  high_complexity_waiting_for_primary: {queue.get('high_complexity_waiting_for_primary', 0)}",
            f"  next_eligible_retry: {queue.get('next_eligible_retry')}",
        ]
    )
    return "\n".join(lines)


def format_provider_inventory(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Providers"]
    for record in payload.get("providers") or []:
        lines.append(
            f"- {record.get('provider_key')}: model={record.get('model')} "
            f"strength={record.get('strength')} state={record.get('state')} primary={record.get('is_primary')} fallback={record.get('is_fallback')}"
        )
    if not payload.get("providers"):
        lines.append("- none configured")
    return "\n".join(lines)


def format_fallback_status(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Fallback Status"]
    lines.append(f"sticky_for_development: {payload.get('sticky_for_development')}")
    lines.append(f"timeouts: {json.dumps(payload.get('timeout_defaults') or {}, sort_keys=True)}")
    for record in payload.get("fallback_providers") or []:
        lines.append(f"- {record.get('provider_id')} model={record.get('model')} strength={record.get('strength')} state={record.get('state')}")
        lines.append(f"  last_no_chunk_timeout_at: {record.get('last_no_chunk_timeout_at')}")
        lines.append(f"  denied_task_classes: {', '.join(record.get('denied_task_classes') or [])}")
    if not payload.get("fallback_providers"):
        lines.append("- none configured")
    return "\n".join(lines)


def format_provider_config_reconciliation(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Config Reconciliation"]
    lines.append(f"status: {payload.get('status')}")
    lines.append(f"active_target_primary_model: {payload.get('active_target_primary_model') or payload.get('expected_primary_model')}")
    lines.append(f"expected_primary_model: {payload.get('expected_primary_model')} (compatibility field)")
    lines.append(f"target_profile_source: {payload.get('target_profile_source')}")
    lines.append(f"operator_truth_matches_repo: {payload.get('operator_truth_matches_repo')}")
    lines.append(f"read_only: {payload.get('read_only')}")
    lines.append(f"provider_state_mutated: {payload.get('provider_state_mutated')}")
    lines.append(f"model_config_mutated: {payload.get('model_config_mutated')}")
    lines.append("runtime_model_configs:")
    for item in payload.get("runtime_model_configs") or []:
            lines.append(
                f"- {item.get('runtime')}: primary={item.get('primary_model')} "
                f"fallbacks={', '.join(item.get('fallback_models') or [])} "
                f"target_primary={item.get('target_primary_model')} "
                f"target_fallbacks={', '.join(item.get('target_fallback_models') or [])} "
                f"primary_matches_target={item.get('primary_matches_target')}"
            )
    setup = payload.get("provider_setup_state") or {}
    openai = (setup.get("providers") or {}).get("openai") or {}
    local_oss = (setup.get("providers") or {}).get("local_oss") or {}
    lines.append(f"setup_openai_default_model: {openai.get('default_model')}")
    lines.append(f"setup_local_oss_configured: {local_oss.get('configured')}")
    local = payload.get("local_fallback") or {}
    lines.append(f"local_num_ctx_status: {local.get('num_ctx_status')}")
    lines.append(f"safe_local_num_ctx_default: {payload.get('safe_local_num_ctx_default')}")
    mismatches = payload.get("mismatches") or []
    if mismatches:
        lines.append("mismatches:")
        for item in mismatches:
            details: list[str] = []
            if item.get("runtime"):
                details.append(f"runtime={item.get('runtime')}")
            if item.get("expected_model"):
                details.append(f"expected={item.get('expected_model')}")
            if item.get("actual_model"):
                details.append(f"actual={item.get('actual_model')}")
            if item.get("reason"):
                details.append(f"reason={item.get('reason')}")
            lines.append(f"- {item.get('severity')} {item.get('type')} {' '.join(details)}".rstrip())
    else:
        lines.append("mismatches: none")
    return "\n".join(lines)


def format_provider_target_profile(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Target Profile"]
    lines.append(f"profile_exists: {payload.get('profile_exists')}")
    lines.append(f"profile_source: {payload.get('profile_source')}")
    lines.append(f"default_primary_model: {payload.get('default_primary_model')}")
    lines.append(f"read_only: {payload.get('read_only')}")
    runtime_targets = payload.get("runtime_targets") or {}
    if runtime_targets:
        lines.append("runtime_targets:")
        for runtime_name, target in runtime_targets.items():
            lines.append(
                f"- {runtime_name}: primary={target.get('desired_primary_model')} "
                f"fallbacks={', '.join(target.get('desired_fallback_models') or [])} "
                f"fallback_enforcement={target.get('fallback_enforcement')}"
            )
    local = payload.get("local_fallback_target") or {}
    lines.append(
        "local_fallback_target: "
        f"provider={local.get('provider_id')} model={local.get('model')} "
        f"enabled={local.get('enabled')} num_ctx={local.get('num_ctx')} "
        f"safety={local.get('safety_status')}"
    )
    return "\n".join(lines)


def format_provider_target_profile_plan(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Target Profile Plan"]
    lines.append(f"plan_status: {payload.get('plan_status')}")
    lines.append(f"desired_default_primary_model: {payload.get('desired_default_primary_model')}")
    lines.append(f"target_model_source: {payload.get('target_model_source')}")
    lines.append(f"profile_change_needed: {payload.get('profile_change_needed')}")
    lines.append(f"profile_file_written: {payload.get('profile_file_written')}")
    lines.append(f"approval_request_written: {payload.get('approval_request_written')}")
    lines.append(f"queue_item_id: {payload.get('queue_item_id')}")
    lines.append(f"provider_state_mutated: {payload.get('provider_state_mutated')}")
    lines.append(f"model_config_mutated: {payload.get('model_config_mutated')}")
    lines.append(f"setup_state_mutated: {payload.get('setup_state_mutated')}")
    if payload.get("approval_request_ref"):
        lines.append(f"approval_request_ref: {payload.get('approval_request_ref')}")
    candidate = payload.get("candidate_profile") if isinstance(payload.get("candidate_profile"), dict) else {}
    runtime_targets = candidate.get("runtime_targets") if isinstance(candidate.get("runtime_targets"), dict) else {}
    if runtime_targets:
        lines.append("candidate_runtime_targets:")
        for runtime_name, target in runtime_targets.items():
            lines.append(
                f"- {runtime_name}: primary={target.get('primary_model')} "
                f"fallbacks={', '.join(target.get('fallback_models') or [])} "
                f"fallback_enforcement={target.get('fallback_enforcement')}"
            )
    local = candidate.get("local_fallback") if isinstance(candidate.get("local_fallback"), dict) else {}
    if local:
        lines.append(
            "candidate_local_fallback: "
            f"provider={local.get('provider_id')} model={local.get('model')} "
            f"enabled={local.get('enabled')} num_ctx={local.get('num_ctx')} "
            f"authority={local.get('authority')}"
        )
    return "\n".join(lines)


def format_provider_config_change_plan(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Config Change Plan"]
    lines.append(f"status: {payload.get('status')}")
    lines.append(f"active_target_primary_model: {payload.get('active_target_primary_model') or payload.get('expected_primary_model')}")
    lines.append(f"expected_primary_model: {payload.get('expected_primary_model')} (compatibility field)")
    lines.append(f"requires_operator_approval: {payload.get('requires_operator_approval')}")
    lines.append(f"approval_request_written: {payload.get('approval_request_written')}")
    lines.append(f"queue_item_id: {payload.get('queue_item_id')}")
    lines.append(f"provider_state_mutated: {payload.get('provider_state_mutated')}")
    lines.append(f"model_config_mutated: {payload.get('model_config_mutated')}")
    lines.append(f"setup_state_mutated: {payload.get('setup_state_mutated')}")
    if payload.get("approval_request_ref"):
        lines.append(f"approval_request_ref: {payload.get('approval_request_ref')}")
    changes = payload.get("proposed_changes") or []
    if changes:
        lines.append("proposed_changes:")
        for change in changes:
            lines.append(
                f"- {change.get('change_type')} path={change.get('path')} "
                f"field={change.get('field')} current={change.get('current_value')} "
                f"proposed={change.get('proposed_value')} status={change.get('mutation_status')}"
            )
    else:
        lines.append("proposed_changes: none")
    return "\n".join(lines)


def format_provider_config_apply_preflight(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Config Apply Preflight"]
    lines.append(f"preflight_status: {payload.get('preflight_status')}")
    lines.append(f"structurally_valid: {payload.get('structurally_valid')}")
    lines.append(f"drift_detected: {payload.get('drift_detected')}")
    lines.append(f"apply_enabled: {payload.get('apply_enabled')}")
    lines.append(f"proposal_id: {payload.get('proposal_id')}")
    lines.append(f"queue_item_id: {payload.get('queue_item_id')}")
    for error in payload.get("errors") or []:
        lines.append(f"error: {error}")
    checks = payload.get("checks") or []
    if checks:
        lines.append("checks:")
        for check in checks:
            lines.append(
                f"- {check.get('change_id')} field={check.get('field')} "
                f"expected_current={check.get('expected_current_value')} "
                f"actual_current={check.get('actual_current_value')} "
                f"proposed={check.get('proposed_value')} status={check.get('status')}"
            )
    return "\n".join(lines)


def format_provider_config_apply_design(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Config Apply Design"]
    lines.append(f"design_status: {payload.get('design_status')}")
    lines.append(f"executor_status: {payload.get('executor_status')}")
    lines.append(f"execution_enabled: {payload.get('execution_enabled')}")
    lines.append(f"apply_execution_allowed: {payload.get('apply_execution_allowed')}")
    lines.append(f"operation: {payload.get('operation')}")
    lines.append(f"approval_schema_id: {payload.get('approval_schema_id')}")
    lines.append(f"proposal_id: {payload.get('proposal_id')}")
    lines.append(f"queue_item_id: {payload.get('queue_item_id')}")
    lines.append(f"preflight_status: {payload.get('preflight_status')}")
    lines.append(f"gate_policy_allowed: {payload.get('gate_policy_allowed')}")
    blocked = payload.get("blocked_reasons") or []
    if blocked:
        lines.append("blocked_reasons:")
        for reason in blocked:
            lines.append(f"- {reason}")
    target_writes = payload.get("target_writes") or []
    if target_writes:
        lines.append("target_writes:")
        for item in target_writes:
            lines.append(
                f"- {item.get('path')} field={item.get('field')} "
                f"current={item.get('current_value')} proposed={item.get('proposed_value')} "
                f"write_enabled_after_approval={item.get('write_enabled_after_approval')} "
                f"status={item.get('apply_status')}"
            )
    return "\n".join(lines)


def format_queue_list(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Queue"]
    lines.append(f"queued_task_count: {payload.get('queued_task_count', 0)}")
    lines.append(f"needs_operator_approval_count: {payload.get('needs_operator_approval_count', 0)}")
    for item in payload.get("items") or []:
        lines.append(
            f"- {item.get('task_id')} status={item.get('retry_status')} "
            f"task_class={item.get('task_class')} primary={item.get('primary_provider_id')}"
        )
    return "\n".join(lines)


def format_queue_item(item: ProviderQueueItem | None) -> str:
    if item is None:
        return "Queue item not found."
    data = item.to_dict()
    lines = [f"ChaseOS Runtime Provider Queue Item: {item.task_id}"]
    for key in [
        "retry_status",
        "task_class",
        "required_provider_strength",
        "primary_provider_id",
        "primary_failure_reason",
        "fallback_denied_reason",
        "cooldown_until",
        "related_runtime",
        "related_adapter",
        "approval_status",
        "retry_attempts",
        "safe_next_step",
        "files_modified",
    ]:
        lines.append(f"{key}: {data.get(key)}")
    lines.append(f"original_request: {item.original_request[:500]}")
    return "\n".join(lines)


def format_audit_tail(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Provider Audit Tail"]
    events = payload.get("events") or []
    for event in events:
        lines.append(
            f"- {event.get('timestamp')} {event.get('event_type')} "
            f"provider={event.get('provider_id')} task={event.get('task_class')} decision={event.get('decision')}"
        )
    if not events:
        lines.append("- no events")
    return "\n".join(lines)


def format_provider_probe(payload: dict[str, Any]) -> str:
    lines = [f"ChaseOS Runtime Provider Probe: {payload.get('target')}"]
    lines.append(f"ok: {payload.get('ok')}")
    lines.append(f"probe_mode: {payload.get('probe_mode', 'config')}")
    lines.append(f"provider_state_mutated: {payload.get('provider_state_mutated')}")
    lines.append(f"canonical_files_mutated: {payload.get('canonical_files_mutated')}")
    if payload.get("reason"):
        lines.append(f"reason: {payload.get('reason')}")
    provider = payload.get("provider") or {}
    if provider:
        lines.append(f"provider_id: {provider.get('provider_id')}")
        lines.append(f"model: {provider.get('model')}")
        lines.append(f"state: {provider.get('state')}")
        lines.append(f"strength: {provider.get('strength')}")
    plan = payload.get("probe_plan") or {}
    if plan:
        lines.append(f"network_call_attempted: {plan.get('live_network_call_attempted')}")
        lines.append(f"secret_value_read: {plan.get('secret_value_read')}")
        lines.append(f"probe_reason: {plan.get('reason')}")
    preflight = payload.get("live_probe_preflight") or {}
    if preflight:
        lines.append(f"gate_operation: {preflight.get('gate_operation')}")
        lines.append(f"gate_approval_schema_id: {preflight.get('gate_approval_schema_id')}")
        lines.append(f"gate_policy_allowed: {preflight.get('gate_policy_allowed')}")
        lines.append(f"external_api_id: {preflight.get('external_api_id')}")
        lines.append(f"live_probe_allowed: {preflight.get('live_probe_allowed')}")
        lines.append(f"approval_required: {preflight.get('approval_required')}")
        lines.append(f"approval_status: {preflight.get('approval_status')}")
        lines.append(f"gate_approval_id: {preflight.get('gate_approval_id')}")
        lines.append(f"approval_request_ref: {preflight.get('approval_request_ref')}")
        lines.append(f"approval_request_written: {preflight.get('approval_request_written')}")
        validation = preflight.get("approval_validation") or {}
        if validation:
            lines.append(f"approval_structurally_valid: {validation.get('structurally_valid')}")
            lines.append(f"live_probe_execution_allowed: {validation.get('live_probe_execution_allowed')}")
        lines.append(f"denial_reason: {preflight.get('denial_reason')}")
    return "\n".join(lines)


def format_provider_executor_spec(payload: dict[str, Any]) -> str:
    lines = [f"ChaseOS Runtime Provider Executor Spec: {payload.get('target')}"]
    lines.append(f"ok: {payload.get('ok')}")
    lines.append(f"executor_status: {payload.get('executor_status')}")
    lines.append(f"execution_enabled: {payload.get('execution_enabled')}")
    lines.append(f"live_probe_execution_allowed: {payload.get('live_probe_execution_allowed')}")
    lines.append(f"live_network_call_attempted: {payload.get('live_network_call_attempted')}")
    lines.append(f"secret_value_read: {payload.get('secret_value_read')}")
    lines.append(f"provider_state_mutated: {payload.get('provider_state_mutated')}")
    provider = payload.get("provider") or {}
    if provider:
        lines.append(f"provider_id: {provider.get('provider_id')}")
        lines.append(f"model: {provider.get('model')}")
        lines.append(f"strength: {provider.get('strength')}")
    preflight = payload.get("live_probe_preflight") or {}
    if preflight:
        lines.append(f"gate_operation: {preflight.get('gate_operation')}")
        lines.append(f"gate_approval_schema_id: {preflight.get('gate_approval_schema_id')}")
        lines.append(f"gate_policy_allowed: {preflight.get('gate_policy_allowed')}")
        lines.append(f"approval_status: {preflight.get('approval_status')}")
        lines.append(f"gate_approval_id: {preflight.get('gate_approval_id')}")
    blocked = payload.get("blocked_reasons") or []
    if blocked:
        lines.append("blocked_reasons:")
        for reason in blocked:
            lines.append(f"- {reason}")
    preconditions = payload.get("preconditions") or []
    if preconditions:
        lines.append("preconditions:")
        for item in preconditions:
            lines.append(f"- {item.get('id')}: {item.get('status')} critical={item.get('critical')}")
    return "\n".join(lines)


def format_recovery_dry_run(payload: dict[str, Any]) -> str:
    lines = ["ChaseOS Runtime Recovery Dry Run"]
    lines.append(f"provider_state_mutated: {payload.get('provider_state_mutated')}")
    lines.append(f"canonical_files_mutated: {payload.get('canonical_files_mutated')}")
    lines.append(f"cooldown_expired_primaries: {len(payload.get('cooldown_expired_primaries') or [])}")
    lines.append(f"provider_probe_plans: {len(payload.get('provider_probe_plans') or [])}")
    queue = payload.get("queue_summary") or {}
    lines.append(f"queued_task_count: {queue.get('queued_task_count', 0)}")
    lines.append(f"ready_queue_items: {len(payload.get('ready_queue_items') or [])}")
    lines.append(f"retry_packages: {len(payload.get('retry_packages') or [])}")
    return "\n".join(lines)
