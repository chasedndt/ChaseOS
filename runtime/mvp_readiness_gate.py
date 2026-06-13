"""No-secret MVP readiness gate for ChaseOS.

This module aggregates the current MVP blocker map without calling providers,
reading credential values, consuming approvals, dispatching runtime work, or
mutating repo state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from runtime.mvp_agent_bus_lifecycle import build_mvp_agent_bus_lifecycle
from runtime.mvp_source_context import build_mvp_source_context_bridge
from runtime.mvp_system_control_boundary import build_mvp_system_control_boundary
from runtime.ventureops.evidence_discovery_preflight import build_evidence_discovery_preflight
from runtime.ventureops.real_client_input_manifest import build_real_client_input_manifest


MODEL_VERSION = "chaseos.mvp_readiness_gate.v1"
SURFACE_ID = "chaseos_mvp_readiness_gate"
OPERATOR_INPUT_SCHEMA_VERSION = "chaseos.mvp_operator_input_schema.v1"
OPERATOR_INPUT_TEMPLATE_VERSION = "chaseos.mvp_operator_input_template.v1"
OPERATOR_INPUT_VALIDATION_VERSION = "chaseos.mvp_operator_input_validation.v1"
MVP_CREDENTIAL_HANDOFF_VERSION = "chaseos.mvp_credential_handoff.v1"
PENDING_CHAT_APPROVAL_ID = "5849a53f-10e0-46af-a89a-7de06150f7f8"
PLACEHOLDER_SECRET_REFS = {"", "SET_OPENAI_SECRET_REF", "<env-var>", "<secret-ref>"}
OPENAI_SETUP_METADATA_DRY_RUN_COMMAND = (
    "python -m runtime.cli.main setup set provider openai "
    "secret_reference_kind=env-var-or-local-secret-ref "
    "secret_reference_present=true "
    "secret_reference_target=OPENAI_API_KEY "
    "--dry-run --json"
)
OPENAI_SETUP_METADATA_WRITE_COMMAND = (
    "python -m runtime.cli.main setup set provider openai "
    "secret_reference_kind=env-var-or-local-secret-ref "
    "secret_reference_present=true "
    "secret_reference_target=OPENAI_API_KEY "
    "--json"
)
OPENAI_REFERENCE_PRESENCE_CHECK_USER_COMMAND = (
    '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
)
OPENAI_REFERENCE_PRESENCE_CHECK_PROCESS_COMMAND = (
    '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")'
)
PENDING_CHAT_APPROVAL_READINESS_COMMAND = (
    "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract "
    f"--approval-id {PENDING_CHAT_APPROVAL_ID} --json"
)
PENDING_CHAT_APPROVAL_EXECUTOR_COMMAND_TEMPLATE = (
    "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor "
    f"--approval-id {PENDING_CHAT_APPROVAL_ID} "
    "--expected-consumption-digest <digest_from_readiness> --json"
)
MVP_NEXT_ACTION_CARD_PATH = "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
MVP_OPENAI_SECRET_REFERENCE_HANDOFF_CARD_PATH = (
    "07_LOGS/Operator-Briefs/2026-05-13-mvp-openai-secret-reference-handoff-card.md"
)
MVP_OPENAI_SECRET_REFERENCE_CURRENT_HANDOFF_GUIDE_PATH = (
    "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
)
MVP_OPERATOR_INPUT_TEMPLATE_PATH = "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
MVP_WRITEBACK_INDEX_PATHS = [
    "07_LOGS/Build-Logs/Build-Logs-Index.md",
    "99_ARCHIVE/Documentation-History/Documentation-History-Index.md",
    "07_LOGS/Daily/Daily-Index.md",
    "07_LOGS/Agent-Activity/Agent-Activity-Index.md",
]
MVP_LATEST_WRITEBACK_RECORD_PATHS = [
    "07_LOGS/Build-Logs/2026-05-14-ChaseOS-mvp-current-state-rollover-audit.md",
    "99_ARCHIVE/Documentation-History/2026-05-14_mvp-current-state-rollover-audit.md",
    "07_LOGS/Daily/2026-05-14.md",
    "07_LOGS/Agent-Activity/2026-05-14-codex-mvp-current-state-rollover-audit.md",
]
MVP_OPERATOR_INPUT_TEMPLATE_VALIDATION_COMMAND = (
    f"python -m runtime.cli.main mvp validate-operator-input --input {MVP_OPERATOR_INPUT_TEMPLATE_PATH} --json"
)
MVP_OPERATOR_INPUT_TEMPLATE_WRITE_COMMAND = (
    "python -m runtime.cli.main mvp operator-input-template "
    f"--write-template {MVP_OPERATOR_INPUT_TEMPLATE_PATH} --json"
)
SETUP_WIDE_VALIDATION_COMMAND = "python -m runtime.cli.main setup validate --json"
MVP_REQUIRED_PROVIDER_IDS = ["openai"]
MVP_REQUIRED_SECRET_REFERENCE_IDS = ["openai_secret_reference"]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path, default: Any) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return default
    return payload


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _path_exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _latest_mvp_writeback_record_paths(root: Path, *, per_group_limit: int = 3) -> list[str]:
    groups = [
        ("07_LOGS/Build-Logs", "20*-ChaseOS-mvp-*.md"),
        ("99_ARCHIVE/Documentation-History", "20*_mvp-*.md"),
        ("07_LOGS/Daily", "20??-??-??.md"),
        ("07_LOGS/Agent-Activity", "20*-codex-mvp-*.md"),
    ]
    refs: list[str] = []
    for directory, pattern in groups:
        base = root / directory
        if not base.exists():
            continue
        paths = sorted(
            (path for path in base.glob(pattern) if path.is_file()),
            key=lambda path: (path.stat().st_mtime, path.name),
            reverse=True,
        )
        refs.extend(_rel(root, path) for path in paths[:per_group_limit])
    return _ordered_unique(refs)


def _tracked_chat_approval_resolution(root: Path) -> dict[str, Any]:
    approval_path = root / "runtime" / "studio" / "approvals" / f"{PENDING_CHAT_APPROVAL_ID}.json"
    marker_path = (
        root
        / "runtime"
        / "studio"
        / "approvals"
        / "_chat_consumption_markers"
        / f"{PENDING_CHAT_APPROVAL_ID}.json"
    )
    payload = _approval_payload(approval_path)
    spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
    marker = _approval_payload(marker_path)
    target_path = str(spec.get("target_path") or "")
    target_exists = bool(target_path and (root / target_path).exists())
    marker_state = str(marker.get("state") or marker.get("status") or "")
    consumed = bool(
        payload.get("status") == "executed"
        and payload.get("approval_consumed") is True
        and marker_path.exists()
        and marker_state in {"executed", "completed", "complete", "succeeded"}
        and target_exists
    )
    return {
        "approval_id": PENDING_CHAT_APPROVAL_ID,
        "approval_path": _rel(root, approval_path),
        "approval_exists": approval_path.exists(),
        "status": payload.get("status"),
        "submitted_by": spec.get("submitted_by"),
        "action_type": spec.get("action_type"),
        "target_path": target_path or None,
        "target_exists": target_exists,
        "marker_path": _rel(root, marker_path),
        "marker_exists": marker_path.exists(),
        "marker_state": marker_state or None,
        "consumed": consumed,
        "pending_operator_decision": payload.get("status") == "pending",
    }


def _canonical_operator_handoff(root: Path) -> dict[str, Any]:
    handoff_path = root / MVP_NEXT_ACTION_CARD_PATH
    tracked_chat = _tracked_chat_approval_resolution(root)
    covers = [
        "current_goal",
        "current_sector",
        "ten_pass_scope",
        "openai_secret_reference",
        (
            "pending_chat_approval_decision"
            if tracked_chat.get("pending_operator_decision")
            else "resolved_chat_approval_consumption"
        ),
    ]
    return {
        "id": "mvp_next_action_card",
        "label": "MVP Next Action Card",
        "path": _rel(root, handoff_path),
        "exists": handoff_path.exists(),
        "purpose": "Canonical current MVP handoff for goal, sector, 10-pass scope, P0 OpenAI reference, and tracked Chat approval state.",
        "contains_secret_values": False,
        "execution_authority_granted": False,
        "covers": covers,
    }


def _operator_input_template_artifact(root: Path) -> dict[str, Any]:
    template_path = root / MVP_OPERATOR_INPUT_TEMPLATE_PATH
    return {
        "path": _rel(root, template_path),
        "exists": template_path.exists(),
        "contains_secret_values": False,
        "validation_command": MVP_OPERATOR_INPUT_TEMPLATE_VALIDATION_COMMAND,
        "write_command": MVP_OPERATOR_INPUT_TEMPLATE_WRITE_COMMAND,
    }


def _load_setup_state(root: Path) -> dict[str, Any]:
    path = root / "runtime" / "setup_state.json"
    payload = _read_json(path, {})
    return payload if isinstance(payload, dict) else {}


def _load_setup_registry(root: Path) -> dict[str, Any]:
    path = root / "runtime" / "setup_registry.json"
    payload = _read_json(path, {})
    return payload if isinstance(payload, dict) else {}


def _load_setup_provider_profiles(root: Path) -> dict[str, Any]:
    path = root / "runtime" / "setup_provider_profiles.json"
    payload = _read_json(path, {})
    return payload if isinstance(payload, dict) else {}


def _probe_secret_reference(root: Path, kind: str | None, target: str | None) -> dict[str, Any]:
    if not kind or not target:
        return {"checked": False, "exists": False, "source": kind, "error": "missing_reference_target"}

    if kind == "env-var" or kind == "env-var-or-local-secret-ref":
        if os.environ.get(target):
            return {"checked": True, "exists": True, "source": "env-var", "error": None}
        if kind == "env-var":
            return {"checked": True, "exists": False, "source": "env-var", "error": "env_var_missing"}

    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.exists():
        return {"checked": True, "exists": True, "source": "local-path", "error": None}

    return {"checked": True, "exists": False, "source": kind, "error": "reference_not_found"}


def _provider_secret_reference_handoff_steps(blocked: bool) -> list[dict[str, Any]]:
    """Describe the no-secret operator sequence without embedding or requesting values."""

    reference_status = "blocked_operator_input_required" if blocked else "reference_resolvable"
    return [
        {
            "order": 1,
            "id": "set_outside_repo_secret_reference",
            "actor": "operator",
            "status": reference_status,
            "action": "Create or confirm the OpenAI secret in the gitignored ChaseOS .env file or another approved local secret source, using the reference name OPENAI_API_KEY.",
            "command_template": None,
            "presence_check_commands": [
                OPENAI_REFERENCE_PRESENCE_CHECK_USER_COMMAND,
                OPENAI_REFERENCE_PRESENCE_CHECK_PROCESS_COMMAND,
            ],
            "presence_check_outputs_secret_value": False,
            "manual_only": True,
            "secret_value_allowed_in_repo_or_chat": False,
            "codex_can_execute": False,
            "proof_after_step": "python -m runtime.cli.main setup provider validate openai --json",
        },
        {
            "order": 2,
            "id": "preview_setup_metadata_reference",
            "actor": "operator_or_codex",
            "status": "ready_after_reference_exists" if blocked else "optional_preview_available",
            "action": "Preview the setup metadata change before writing; the preview must report writes_setup_state=false.",
            "command_template": OPENAI_SETUP_METADATA_DRY_RUN_COMMAND,
            "manual_only": False,
            "secret_value_allowed_in_repo_or_chat": False,
            "codex_can_execute": True,
            "proof_after_step": "writes_setup_state=false",
        },
        {
            "order": 3,
            "id": "update_setup_metadata_reference",
            "actor": "operator_or_codex_after_explicit_confirmation",
            "status": "ready_after_reference_exists" if blocked else "optional_metadata_already_aligned_or_ready",
            "action": "Point ChaseOS setup metadata at the reference name only; do not write the API key value.",
            "command_template": OPENAI_SETUP_METADATA_WRITE_COMMAND,
            "manual_only": False,
            "secret_value_allowed_in_repo_or_chat": False,
            "codex_can_execute": False,
            "proof_after_step": "python -m runtime.cli.main setup provider validate openai --json",
        },
        {
            "order": 4,
            "id": "validate_reference_without_secret_read",
            "actor": "operator_or_codex",
            "status": "ready",
            "action": "Validate that the reference resolves without displaying or reading the secret value.",
            "command_template": "python -m runtime.cli.main setup provider validate openai --json",
            "manual_only": False,
            "secret_value_allowed_in_repo_or_chat": False,
            "codex_can_execute": True,
            "proof_after_step": "secret_reference_resolvable=true",
        },
        {
            "order": 5,
            "id": "request_guarded_live_probe_approval",
            "actor": "operator",
            "status": "blocked_until_validation_passes" if blocked else "ready_for_separate_approval_request",
            "action": "Only after validation passes, create or review a separate approval plan for a live provider probe.",
            "command_template": "python -m runtime.cli.main runtime provider live-probe-target-approval-plan primary --json",
            "manual_only": False,
            "secret_value_allowed_in_repo_or_chat": False,
            "codex_can_execute": False,
            "proof_after_step": "approved live probe succeeds through runtime provider live-probe-executor",
        },
    ]


def _provider_credential_check(root: Path) -> dict[str, Any]:
    setup = _load_setup_state(root)
    providers = setup.get("providers") if isinstance(setup.get("providers"), dict) else {}
    openai = providers.get("openai") if isinstance(providers.get("openai"), dict) else {}
    kind = openai.get("secret_reference_kind")
    target = str(openai.get("secret_reference_target") or "").strip()
    target_is_placeholder = target in PLACEHOLDER_SECRET_REFS
    reference_probe = _probe_secret_reference(root, str(kind) if kind else None, target or None)
    secret_reference_resolvable = bool(reference_probe.get("exists")) and not target_is_placeholder
    secret_reference_env_name_present = bool(
        reference_probe.get("source") == "env-var" and reference_probe.get("exists")
    )

    blockers: list[str] = []
    if target_is_placeholder:
        blockers.append("openai_secret_reference_target_placeholder_or_missing")
    elif not secret_reference_resolvable:
        blockers.append("openai_secret_reference_not_resolved")

    status = "ready_for_guarded_live_probe_request" if not blockers else "blocked_operator_input_required"
    operator_handoff_steps = _provider_secret_reference_handoff_steps(bool(blockers))
    return {
        "id": "provider_credential_readiness",
        "status": status,
        "configured_provider": "openai",
        "configured_model": openai.get("default_model"),
        "configured": bool(openai.get("configured")),
        "secret_reference_kind": kind,
        "secret_reference_target": target or None,
        "secret_reference_target_is_placeholder": target_is_placeholder,
        "secret_reference_env_name_present": secret_reference_env_name_present,
        "secret_reference_resolvable": secret_reference_resolvable,
        "secret_reference_probe": reference_probe,
        "secret_reference_probe_source": reference_probe.get("source"),
        "secret_reference_probe_error": reference_probe.get("error"),
        "required_operator_input": None
        if not blockers
        else "Provide a local gitignored ChaseOS .env entry named OPENAI_API_KEY, or an approved alternate local secret reference.",
        "safe_next_command": None
        if not blockers
        else OPENAI_SETUP_METADATA_DRY_RUN_COMMAND,
        "setup_metadata_write_command": OPENAI_SETUP_METADATA_WRITE_COMMAND,
        "reference_presence_check_commands": [
            OPENAI_REFERENCE_PRESENCE_CHECK_USER_COMMAND,
            OPENAI_REFERENCE_PRESENCE_CHECK_PROCESS_COMMAND,
        ],
        "reference_presence_check_outputs_secret_value": False,
        "setup_provider_validation_command": "python -m runtime.cli.main setup provider validate openai --json",
        "operator_handoff_steps": operator_handoff_steps,
        "operator_handoff_step_count": len(operator_handoff_steps),
        "live_probe_approval_plan_command": "python -m runtime.cli.main runtime provider live-probe-target-approval-plan primary --json",
        "blockers": blockers,
        "secret_value_read": False,
        "secret_value_visible": False,
        "live_network_call_attempted": False,
        "provider_state_mutated": False,
        "evidence_refs": ["runtime/setup_state.json", "runtime/setup_cli.py"],
    }


def _setup_scope_boundary(root: Path, provider: dict[str, Any]) -> dict[str, Any]:
    """Explain setup-wide validation scope without probing providers or secrets."""

    registry = _load_setup_registry(root)
    profiles = _load_setup_provider_profiles(root)
    setup = _load_setup_state(root)
    provider_state = setup.get("providers") if isinstance(setup.get("providers"), dict) else {}
    integration_state = (
        setup.get("integrations") if isinstance(setup.get("integrations"), dict) else {}
    )
    registry_providers = (
        registry.get("providers") if isinstance(registry.get("providers"), list) else []
    )
    registry_integrations = (
        registry.get("integrations") if isinstance(registry.get("integrations"), list) else []
    )

    invalid_provider_ids: list[str] = []
    provider_missing: dict[str, list[str]] = {}
    for entry in registry_providers:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip()
        if not provider_id:
            continue
        state = (
            provider_state.get(provider_id)
            if isinstance(provider_state.get(provider_id), dict)
            else {}
        )
        profile = profiles.get(provider_id) if isinstance(profiles.get(provider_id), dict) else {}
        missing = [
            str(check_name)
            for check_name in profile.get("validation_checks", [])
            if not bool(state.get(check_name))
        ]
        if provider_id == "openai" and provider.get("blockers"):
            missing.append("secret_reference_resolvable")
        if not bool(state.get("configured")) or missing:
            invalid_provider_ids.append(provider_id)
            provider_missing[provider_id] = _ordered_unique(missing or ["configured"])

    if not registry_providers and provider.get("blockers"):
        invalid_provider_ids.append("openai")
        provider_missing["openai"] = list(provider.get("blockers") or [])

    invalid_integration_ids: list[str] = []
    integration_missing: dict[str, list[str]] = {}
    for entry in registry_integrations:
        if not isinstance(entry, dict):
            continue
        integration_id = str(entry.get("id") or "").strip()
        if not integration_id:
            continue
        state = (
            integration_state.get(integration_id)
            if isinstance(integration_state.get(integration_id), dict)
            else {}
        )
        validation_checks = entry.get("validation_checks")
        if not isinstance(validation_checks, list):
            validation_checks = ["configured", "binding_present"]
        missing = [
            str(check_name)
            for check_name in validation_checks
            if not bool(state.get(check_name))
        ]
        if missing:
            invalid_integration_ids.append(integration_id)
            integration_missing[integration_id] = _ordered_unique(missing)

    mvp_current_setup_blocker_ids = (
        list(MVP_REQUIRED_SECRET_REFERENCE_IDS) if provider.get("blockers") else []
    )
    non_mvp_setup_gap_ids = [
        f"provider:{provider_id}"
        for provider_id in invalid_provider_ids
        if provider_id not in MVP_REQUIRED_PROVIDER_IDS
    ] + [f"integration:{integration_id}" for integration_id in invalid_integration_ids]

    if mvp_current_setup_blocker_ids and non_mvp_setup_gap_ids:
        status = "setup_wide_validation_expected_to_fail_mvp_blocker_and_non_mvp_gaps"
    elif mvp_current_setup_blocker_ids:
        status = "setup_wide_validation_expected_to_fail_current_mvp_blocker"
    elif non_mvp_setup_gap_ids:
        status = "setup_wide_validation_expected_to_fail_non_mvp_gaps_only"
    else:
        status = "setup_wide_validation_expected_to_pass"

    return {
        "status": status,
        "setup_wide_validation_command": SETUP_WIDE_VALIDATION_COMMAND,
        "setup_wide_validation_expected_to_pass_now": not (
            invalid_provider_ids or invalid_integration_ids
        ),
        "setup_wide_validation_can_fail_on_non_mvp_items": bool(
            non_mvp_setup_gap_ids
        ),
        "mvp_required_provider_ids": list(MVP_REQUIRED_PROVIDER_IDS),
        "mvp_required_secret_reference_ids": list(MVP_REQUIRED_SECRET_REFERENCE_IDS),
        "mvp_current_setup_blocker_ids": mvp_current_setup_blocker_ids,
        "current_mvp_next_operator_action_id": (
            "openai_secret_reference" if provider.get("blockers") else None
        ),
        "setup_wide_invalid_provider_ids": invalid_provider_ids,
        "setup_wide_invalid_provider_missing": provider_missing,
        "setup_wide_invalid_integration_ids": invalid_integration_ids,
        "setup_wide_invalid_integration_missing": integration_missing,
        "non_mvp_setup_gap_ids": non_mvp_setup_gap_ids,
        "non_mvp_setup_gaps_are_current_mvp_blockers": False,
        "secret_values_read": False,
        "provider_calls_performed": False,
        "setup_metadata_write_performed": False,
        "boundary": (
            "Setup-wide validation covers later-scope providers and integrations; "
            "the current MVP completion gate treats only the OpenAI secret reference "
            "as a current setup blocker unless another governed pass promotes a gap."
        ),
        "evidence_refs": [
            "runtime/setup_registry.json",
            "runtime/setup_provider_profiles.json",
            "runtime/setup_state.json",
            "runtime/setup_cli.py",
        ],
    }


def _provider_secret_reference_action_fields(provider: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_secret_reference_kind": provider.get("secret_reference_kind"),
        "current_secret_reference_target": provider.get("secret_reference_target"),
        "current_secret_reference_target_is_placeholder": bool(
            provider.get("secret_reference_target_is_placeholder")
        ),
        "current_secret_reference_resolvable": bool(
            provider.get("secret_reference_resolvable")
        ),
        "secret_reference_probe_source": provider.get("secret_reference_probe_source"),
        "secret_reference_probe_error": provider.get("secret_reference_probe_error"),
        "recommended_reference_name": "OPENAI_API_KEY",
        "setup_provider_validation_command": provider.get(
            "setup_provider_validation_command"
        ),
        "setup_wide_validation_command": SETUP_WIDE_VALIDATION_COMMAND,
        "provider_live_smoke_readiness_command": (
            "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
        ),
        "reference_presence_check_commands": list(
            provider.get("reference_presence_check_commands") or []
        ),
        "reference_presence_check_outputs_secret_value": bool(
            provider.get("reference_presence_check_outputs_secret_value")
        ),
        "secret_value_read": False,
        "secret_value_allowed_in_repo_or_chat": False,
        "live_network_call_attempted": False,
        "files_modified": False,
    }


def _approval_payload(path: Path) -> dict[str, Any]:
    payload = _read_json(path, {})
    return payload if isinstance(payload, dict) else {}


def _pending_chat_approval_handoff_steps(has_pending: bool) -> list[dict[str, Any]]:
    if not has_pending:
        return []
    return [
        {
            "order": 1,
            "id": "inspect_pending_chat_approval",
            "actor": "operator_or_codex",
            "status": "ready_read_only",
            "action": f"Inspect pending Studio approval {PENDING_CHAT_APPROVAL_ID} without consuming it.",
            "command_template": "python -m runtime.cli.main studio approval-center-panel --json",
            "allowed_decisions": [],
            "codex_can_decide": False,
            "approval_consumption_allowed_now": False,
            "execution_allowed_now": False,
        },
        {
            "order": 2,
            "id": "preview_pending_chat_exact_once_consumption_readiness",
            "actor": "operator_or_codex",
            "status": "ready_read_only",
            "action": "Preview exact-once consumption readiness for this approval without approving, consuming, writing the target, or writing a marker.",
            "command_template": PENDING_CHAT_APPROVAL_READINESS_COMMAND,
            "allowed_decisions": [],
            "codex_can_decide": False,
            "approval_consumption_allowed_now": False,
            "execution_allowed_now": False,
        },
        {
            "order": 3,
            "id": "choose_pending_chat_approval_decision",
            "actor": "operator",
            "status": "blocked_operator_decision_required",
            "action": "Choose approve, reject, or leave_pending for the tracked Chat proposal.",
            "command_template": None,
            "allowed_decisions": ["approve", "reject", "leave_pending"],
            "codex_can_decide": False,
            "approval_consumption_allowed_now": False,
            "execution_allowed_now": False,
        },
        {
            "order": 4,
            "id": "validate_pending_chat_approval_decision_packet",
            "actor": "operator_or_codex",
            "status": "ready_after_operator_decision",
            "action": "Validate the decision metadata through the no-execution MVP operator input validator.",
            "command_template": "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
            "allowed_decisions": ["approve", "reject", "leave_pending"],
            "codex_can_decide": False,
            "approval_consumption_allowed_now": False,
            "execution_allowed_now": False,
        },
        {
            "order": 5,
            "id": "run_separate_exact_once_consumption_pass_if_approved",
            "actor": "operator",
            "status": "blocked_until_separate_governed_pass",
            "action": "If approved, run the separate source-specific exact-once executor with the readiness digest; if rejected or left pending, do not write the target.",
            "command_template": PENDING_CHAT_APPROVAL_EXECUTOR_COMMAND_TEMPLATE,
            "allowed_decisions": ["approve"],
            "codex_can_decide": False,
            "approval_consumption_allowed_now": False,
            "execution_allowed_now": False,
        },
    ]


def _studio_approval_check(root: Path) -> dict[str, Any]:
    approvals_root = root / "runtime" / "studio" / "approvals"
    approval_files = sorted(approvals_root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True) if approvals_root.exists() else []
    marker_files: list[Path] = []
    for marker_dir_name in ("_runtime_dispatch_markers", "_chat_consumption_markers"):
        marker_root = approvals_root / marker_dir_name
        if marker_root.exists():
            marker_files.extend(sorted(marker_root.glob("*.json")))
    marker_by_approval_id: dict[str, dict[str, Any]] = {}
    marker_path_by_approval_id: dict[str, str] = {}
    for marker_path in marker_files:
        marker_payload = _approval_payload(marker_path)
        approval_id = str(marker_payload.get("approval_id") or "")
        if approval_id:
            marker_by_approval_id[approval_id] = marker_payload
            marker_path_by_approval_id[approval_id] = _rel(root, marker_path)
    pending: list[dict[str, Any]] = []
    executed: list[dict[str, Any]] = []
    approval_items: list[dict[str, Any]] = []
    for path in approval_files:
        payload = _approval_payload(path)
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        approval_id = str(payload.get("approval_id") or path.stem)
        marker_payload = marker_by_approval_id.get(approval_id, {})
        item = {
            "approval_id": approval_id,
            "status": payload.get("status") or "unknown",
            "action_type": spec.get("action_type"),
            "target_path": spec.get("target_path"),
            "submitted_by": spec.get("submitted_by"),
            "source_ref": _rel(root, path),
            "submitted_at": payload.get("submitted_at"),
            "execution_status": payload.get("execution_status"),
            "result_action_id": payload.get("result_action_id"),
            "exact_once_marker_path": marker_path_by_approval_id.get(approval_id),
            "exact_once_marker_present": bool(marker_payload),
            "agent_bus_task_written": bool(
                metadata.get("agent_bus_task_write_performed")
                or marker_payload.get("agent_bus_task_written")
            ),
            "agent_bus_task_id": marker_payload.get("task_id")
            or metadata.get("phase11_chat_runtime_dispatch_task_id")
            or payload.get("result_action_id"),
            "provider_call_performed": bool(
                metadata.get("provider_call_performed")
                or marker_payload.get("provider_call_performed")
            ),
            "browser_control_performed": bool(
                metadata.get("browser_control_performed")
                or marker_payload.get("browser_control_performed")
            ),
            "target_write_performed": bool(
                metadata.get("target_vault_write_performed")
                or marker_payload.get("target_write_performed")
            ),
            "workflow_dispatched": bool(
                metadata.get("workflow_dispatched")
                or marker_payload.get("workflow_dispatched")
            ),
            "canonical_mutation_performed": bool(
                metadata.get("canonical_mutation_performed")
                or marker_payload.get("canonical_mutation_performed")
            ),
        }
        approval_items.append(item)
        if item["status"] == "pending":
            pending.append(item)
        if item["status"] in {"executed", "approved"} or item.get("execution_status") in {"succeeded", "complete"}:
            executed.append(item)

    explicit_tracked = next(
        (item for item in approval_items if item["approval_id"] == PENDING_CHAT_APPROVAL_ID),
        None,
    )
    explicit_pending = next((item for item in pending if item["approval_id"] == PENDING_CHAT_APPROVAL_ID), None)
    operator_handoff_steps = _pending_chat_approval_handoff_steps(explicit_pending is not None)
    approval_center_visible = approvals_root.exists() and bool(approval_files)
    one_chat_request_created_approval_artifact = bool(
        explicit_tracked
        and explicit_tracked.get("status") in {"pending", "approved", "executed"}
        and explicit_tracked.get("submitted_by") == "studio-chat"
        and explicit_tracked.get("action_type")
        and explicit_tracked.get("target_path")
        and explicit_tracked.get("source_ref")
    )
    executed_agent_bus_task = next(
        (
            item
            for item in executed
            if item.get("agent_bus_task_written")
            and item.get("agent_bus_task_id")
            and item.get("exact_once_marker_present")
        ),
        None,
    )
    approval_to_action_side_effects_blocked = bool(
        executed_agent_bus_task
        and not executed_agent_bus_task.get("provider_call_performed")
        and not executed_agent_bus_task.get("browser_control_performed")
        and not executed_agent_bus_task.get("target_write_performed")
        and not executed_agent_bus_task.get("workflow_dispatched")
        and not executed_agent_bus_task.get("canonical_mutation_performed")
    )
    executed_chat_target_write = next(
        (
            item
            for item in executed
            if item.get("approval_id") == PENDING_CHAT_APPROVAL_ID
            and item.get("exact_once_marker_present")
            and item.get("target_write_performed")
            and not item.get("provider_call_performed")
            and not item.get("browser_control_performed")
            and not item.get("workflow_dispatched")
            and not item.get("canonical_mutation_performed")
        ),
        None,
    )
    executed_approved_action = executed_agent_bus_task or executed_chat_target_write
    approved_action_side_effects_bounded = bool(
        approval_to_action_side_effects_blocked or executed_chat_target_write
    )
    tracked_pending_count = 1 if explicit_pending else 0
    untracked_pending_approval_count = max(0, len(pending) - tracked_pending_count)
    representative_evidence_refs = [_rel(root, approvals_root)] if approvals_root.exists() else []
    representative_items = [
        explicit_tracked,
        explicit_pending,
        executed_agent_bus_task,
        executed_chat_target_write,
    ]
    if not any(representative_items):
        representative_items.append(pending[0] if pending else None)
    for evidence_item in representative_items:
        if not evidence_item:
            continue
        source_ref = evidence_item.get("source_ref")
        marker_ref = evidence_item.get("exact_once_marker_path")
        if source_ref:
            representative_evidence_refs.append(str(source_ref))
        if marker_ref:
            representative_evidence_refs.append(str(marker_ref))
    if not representative_evidence_refs:
        representative_evidence_refs.extend(_rel(root, path) for path in approval_files[:3])
    return {
        "id": "studio_approval_center_readiness",
        "status": "pending_operator_review"
        if explicit_pending
        else "tracked_chat_approval_consumed"
        if executed_chat_target_write
        else "tracked_chat_approval_artifact_available"
        if explicit_tracked
        else "no_pending_chat_approval_found",
        "approval_artifact_count": len(approval_files),
        "pending_count": len(pending),
        "tracked_pending_count": tracked_pending_count,
        "untracked_pending_approval_count": untracked_pending_approval_count,
        "untracked_pending_approvals_are_current_mvp_blockers": False,
        "untracked_pending_approval_boundary": (
            "Visible in Studio approval queues, but excluded from the current MVP P1 blocker set "
            f"unless explicitly selected by a separate governed pass; tracked MVP approval is {PENDING_CHAT_APPROVAL_ID}."
        ),
        "executed_or_approved_count": len(executed),
        "executed_agent_bus_task": executed_agent_bus_task,
        "executed_chat_target_write": executed_chat_target_write,
        "executed_approved_action": executed_approved_action,
        "approved_agent_bus_task_id": executed_agent_bus_task.get("agent_bus_task_id") if executed_agent_bus_task else None,
        "approved_action_id": (
            executed_approved_action.get("agent_bus_task_id")
            if executed_approved_action
            else None
        ),
        "approval_to_action_exact_once_marker_path": executed_approved_action.get("exact_once_marker_path") if executed_approved_action else None,
        "approval_to_action_side_effects_blocked": approved_action_side_effects_bounded,
        "latest_pending": pending[0] if pending else None,
        "tracked_chat_approval": explicit_tracked,
        "tracked_chat_approval_artifact_path": explicit_tracked.get("source_ref") if explicit_tracked else None,
        "tracked_chat_approval_status": explicit_tracked.get("status") if explicit_tracked else None,
        "tracked_chat_action_type": explicit_tracked.get("action_type") if explicit_tracked else None,
        "tracked_chat_target_path": explicit_tracked.get("target_path") if explicit_tracked else None,
        "tracked_chat_submitted_by": explicit_tracked.get("submitted_by") if explicit_tracked else None,
        "tracked_chat_exact_once_marker_path": explicit_tracked.get("exact_once_marker_path") if explicit_tracked else None,
        "tracked_pending_chat_approval": explicit_pending,
        "tracked_pending_chat_approval_artifact_path": explicit_pending.get("source_ref") if explicit_pending else None,
        "tracked_pending_chat_approval_status": explicit_pending.get("status") if explicit_pending else None,
        "tracked_pending_chat_action_type": explicit_pending.get("action_type") if explicit_pending else None,
        "tracked_pending_chat_target_path": explicit_pending.get("target_path") if explicit_pending else None,
        "tracked_pending_chat_submitted_by": explicit_pending.get("submitted_by") if explicit_pending else None,
        "approval_center_visible": approval_center_visible,
        "one_chat_request_created_approval_artifact": one_chat_request_created_approval_artifact,
        "operator_decision_required": explicit_pending is not None,
        "tracked_chat_approval_is_current_mvp_decision": explicit_pending is not None,
        "operator_handoff_steps": operator_handoff_steps,
        "operator_handoff_step_count": len(operator_handoff_steps),
        "required_operator_input": None
        if explicit_pending is None
        else f"Approve, reject, or leave pending Studio approval {PENDING_CHAT_APPROVAL_ID}.",
        "approval_consumption_readiness_command": PENDING_CHAT_APPROVAL_READINESS_COMMAND,
        "approval_consumption_executor_command_template": PENDING_CHAT_APPROVAL_EXECUTOR_COMMAND_TEMPLATE,
        "blockers": ["pending_chat_approval_decision_required"] if explicit_pending is not None else [],
        "approval_execution_performed": False,
        "approval_consumption_performed": bool(executed_chat_target_write),
        "target_write_performed": bool(executed_chat_target_write),
        "canonical_mutation_performed": False,
        "evidence_ref_mode": "representative_mvp_evidence",
        "evidence_refs": _ordered_unique(representative_evidence_refs),
    }


def _ventureops_check(root: Path) -> dict[str, Any]:
    manifest = build_real_client_input_manifest(root)
    discovery = build_evidence_discovery_preflight(
        root,
        scan_roots=["03_INPUTS", "07_LOGS/Workflow-Proofs", "07_LOGS/Revenue-Proofs"],
    )
    selected_scope_packet_path = discovery.get("selected_scope_packet_path")
    selected_live_client_workflow_proof_path = discovery.get("selected_live_client_workflow_proof_path")
    live_client_workflow_proof_artifact_valid = bool(selected_live_client_workflow_proof_path)
    ready_for_live_client_workflow_proof = bool(
        discovery.get("ready_for_live_client_workflow_proof") or manifest.get("ready_for_live_client_workflow_proof")
    )

    if live_client_workflow_proof_artifact_valid:
        status = "complete_for_one_live_client_workflow_proof"
        blockers: list[str] = []
        next_required_action = "VentureOps MVP real-use proof is present; no P0 VentureOps input remains for this objective."
        next_command = None
    elif ready_for_live_client_workflow_proof:
        status = "ready_for_live_client_workflow_proof_execution"
        blockers = ["ventureops_live_client_workflow_proof_not_run"]
        next_required_action = discovery.get("next_required_action")
        next_command = discovery.get("next_command")
    else:
        status = manifest.get("manifest_status")
        blockers = ["ventureops_real_client_inputs_missing"]
        next_required_action = manifest.get("next_required_action")
        next_command = manifest.get("next_command")

    manifest_command = "python -m runtime.cli.main ventureops real-client-input-manifest --json"
    next_safe_command = str(next_command or "").replace(
        "chaseos ventureops",
        "python -m runtime.cli.main ventureops",
        1,
    ) or None
    evidence_refs = [
        "runtime/ventureops/real_client_input_manifest.py",
        "runtime/ventureops/evidence_discovery_preflight.py",
    ]
    scope_payload: dict[str, Any] = {}
    if selected_scope_packet_path:
        scope_payload_raw = _read_json(root / str(selected_scope_packet_path), {})
        if isinstance(scope_payload_raw, dict):
            scope_payload = scope_payload_raw
    approval_artifact_path = scope_payload.get("approval_artifact_path")
    approval_payload: dict[str, Any] = {}
    if isinstance(approval_artifact_path, str) and approval_artifact_path.strip():
        approval_payload_raw = _read_json(root / approval_artifact_path, {})
        if isinstance(approval_payload_raw, dict):
            approval_payload = approval_payload_raw
    live_workflow_payload: dict[str, Any] = {}
    if selected_live_client_workflow_proof_path:
        live_payload_raw = _read_json(root / str(selected_live_client_workflow_proof_path), {})
        if isinstance(live_payload_raw, dict):
            live_workflow_payload = live_payload_raw
    approved_read_paths = scope_payload.get("approved_read_paths")
    if not isinstance(approved_read_paths, list):
        approved_read_paths = []
    typed_scope_approval_artifact_valid = bool(
        approval_payload.get("type") == "ventureops-real-client-scope-approval"
        and approval_payload.get("approval_status") == "approved"
        and approval_payload.get("operator_attested_scope_approved") is True
    )
    scope_evidence_packet_valid = bool(
        scope_payload.get("type") == "ventureops-real-client-scope-evidence"
        and scope_payload.get("approval_status") == "approved"
        and approved_read_paths
    )
    live_client_workflow_proof_valid = bool(
        live_workflow_payload.get("type") == "ventureops-live-client-workflow-proof"
        and live_workflow_payload.get("live_client_workflow_proof_performed") is True
        and live_workflow_payload.get("approval_status") == "approved"
    )
    not_synthetic_demo_evidence = bool(
        typed_scope_approval_artifact_valid
        and scope_evidence_packet_valid
        and live_client_workflow_proof_valid
        and str(scope_payload.get("client_approved_scope_id") or "").strip()
        and str(live_workflow_payload.get("client_approved_scope_id") or "").strip()
    )
    ventureops_side_effects_blocked = bool(
        live_workflow_payload
        and live_workflow_payload.get("broad_client_data_ingested") is False
        and live_workflow_payload.get("live_external_delivery_performed") is False
        and live_workflow_payload.get("external_send_performed") is False
        and live_workflow_payload.get("crm_mutation_performed") is False
        and live_workflow_payload.get("payment_mutation_performed") is False
        and int(live_workflow_payload.get("provider_calls") or 0) == 0
        and int(live_workflow_payload.get("browser_actions") or 0) == 0
        and live_workflow_payload.get("revenue_claim_made") is False
    )
    for ref in (selected_scope_packet_path, selected_live_client_workflow_proof_path):
        if ref:
            evidence_refs.append(str(ref))
    if isinstance(approval_artifact_path, str) and approval_artifact_path.strip():
        evidence_refs.append(approval_artifact_path)
    return {
        "id": "ventureops_real_use_readiness",
        "status": status,
        "provided_inputs": dict(manifest.get("provided_inputs") or {}),
        "ready_to_author_scope_approval": bool(manifest.get("ready_to_author_scope_approval")),
        "ready_to_author_scope_packet": bool(manifest.get("ready_to_author_scope_packet")),
        "ready_for_live_client_workflow_proof": ready_for_live_client_workflow_proof,
        "live_client_workflow_proof_artifact_valid": live_client_workflow_proof_artifact_valid,
        "typed_scope_approval_artifact_valid": typed_scope_approval_artifact_valid,
        "scope_evidence_packet_valid": scope_evidence_packet_valid,
        "live_client_workflow_proof_valid": live_client_workflow_proof_valid,
        "not_synthetic_demo_evidence": not_synthetic_demo_evidence,
        "approved_read_path_count": len(approved_read_paths),
        "ventureops_side_effects_blocked": ventureops_side_effects_blocked,
        "selected_scope_packet_path": selected_scope_packet_path,
        "selected_scope_approval_artifact_path": approval_artifact_path,
        "selected_live_client_workflow_proof_path": selected_live_client_workflow_proof_path,
        "evidence_discovery_status": discovery.get("discovery_status"),
        "evidence_discovery": {
            "scan_roots": list(discovery.get("scan_roots") or []),
            "scope_candidate_count": int(discovery.get("scope_candidate_count") or 0),
            "live_client_workflow_candidate_count": int(
                discovery.get("live_client_workflow_candidate_count") or 0
            ),
            "selected_scope_packet_path": selected_scope_packet_path,
            "selected_live_client_workflow_proof_path": selected_live_client_workflow_proof_path,
            "ready_for_live_client_workflow_proof": bool(discovery.get("ready_for_live_client_workflow_proof")),
            "ready_for_live_revenue_proof": bool(discovery.get("ready_for_live_revenue_proof")),
            "blockers": list(discovery.get("blockers") or []),
        },
        "missing_inputs": list(manifest.get("missing_inputs") or []),
        "next_required_action": next_required_action,
        "next_command": next_command,
        "next_safe_command": next_safe_command,
        "real_client_input_manifest_command": manifest_command,
        "approval_artifact_present": bool(manifest.get("approval_artifact_present")),
        "source_paths_valid": bool(manifest.get("source_paths_valid")),
        "scope_approval_artifact_valid": bool(manifest.get("scope_approval_artifact_valid")),
        "scope_packet_output_path_present": bool(manifest.get("scope_packet_output_path")),
        "manifest_errors": list(manifest.get("errors") or []),
        "blockers": blockers,
        "live_client_data_ingested": False,
        "external_send_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "evidence_refs": evidence_refs,
    }


def _agent_bus_check(root: Path) -> dict[str, Any]:
    lifecycle = build_mvp_agent_bus_lifecycle(root)
    proof_task = (
        lifecycle.get("proof_task") if isinstance(lifecycle.get("proof_task"), dict) else {}
    )
    task_artifact_written = bool(
        proof_task.get("result_artifact_found")
        and (
            proof_task.get("task_artifacts")
            or proof_task.get("adapter_output_artifacts")
        )
    )
    return {
        "id": "agent_bus_lifecycle",
        "status": lifecycle.get("status"),
        "task_id": proof_task.get("task_id"),
        "task_status": proof_task.get("status"),
        "task_created": bool(proof_task.get("task_created")),
        "task_claimed_by_codex": bool(proof_task.get("task_claimed_by_codex")),
        "task_started_by_codex": bool(proof_task.get("task_started_by_codex")),
        "task_completed_or_safely_blocked": bool(
            proof_task.get("task_completed_or_safely_blocked")
        ),
        "task_artifact_written": task_artifact_written,
        "result_logged": bool(proof_task.get("result_logged")),
        "adapter_result_matches_task": bool(proof_task.get("adapter_result_matches_task")),
        "task_created_claimed_executed_artifact_logged": bool(
            lifecycle.get("task_created_claimed_executed_artifact_logged")
        ),
        "lifecycle": lifecycle,
        "evidence_refs": list(lifecycle.get("evidence_refs") or []),
        "writes_agent_bus_tasks": False,
        "claims_tasks": False,
        "dispatches_runtimes": False,
        "blockers": list(lifecycle.get("blockers") or []),
    }


def _graph_source_check(root: Path) -> dict[str, Any]:
    bridge = build_mvp_source_context_bridge(root)
    evidence_refs = [
        "runtime/studio/graph_scanner_parser.py",
        "runtime/studio/graph_visual_overlays.py",
        "06_AGENTS/Source-Intelligence-Core.md",
        "06_AGENTS/ChaseOS-MVP-Consolidation-Map.md",
    ]
    present = [ref for ref in evidence_refs if _path_exists(root, ref)]
    bridge_ready = bool(
        bridge.get("workflow_context", {}).get("workflow_can_reference_context_without_mutation")
    )
    source_context = bridge.get("source_context") if isinstance(bridge.get("source_context"), dict) else {}
    graph_context = bridge.get("graph_context") if isinstance(bridge.get("graph_context"), dict) else {}
    workflow_context = bridge.get("workflow_context") if isinstance(bridge.get("workflow_context"), dict) else {}
    authority = bridge.get("authority") if isinstance(bridge.get("authority"), dict) else {}
    source_refs = [
        ref for ref in source_context.get("references") or [] if isinstance(ref, dict)
    ]
    graph_refs = [
        ref for ref in graph_context.get("references") or [] if isinstance(ref, dict)
    ]
    source_package_paths = [
        str(ref.get("source_package_path"))
        for ref in source_refs
        if ref.get("source_package_path")
    ]
    workflow_read_paths = [
        str(ref.get("required_read_path"))
        for ref in graph_refs
        if ref.get("required_read_path")
    ]
    mutation_authority_false = all(
        authority.get(key) is False
        for key in [
            "source_package_promotion_allowed",
            "canonical_source_write_allowed",
            "graph_mutation_allowed",
            "graph_index_write_allowed",
            "workflow_execution_allowed",
            "provider_calls_allowed",
            "connector_calls_allowed",
            "browser_control_allowed",
            "host_mutation_allowed",
            "canonical_mutation_allowed",
        ]
    )
    context_navigation_only = (
        bool(authority.get("read_only"))
        and bridge_ready
        and mutation_authority_false
    )
    blockers = [] if context_navigation_only else ["workflow_source_graph_context_bridge_unverified"]
    return {
        "id": "graph_source_intelligence",
        "status": "ready_for_read_only_workflow_context_reference" if context_navigation_only else "partial_or_unverified",
        "source_context_available": bool(source_context.get("source_context_available")),
        "source_package_reference_count": len(source_refs),
        "graph_context_available": bool(graph_context.get("graph_context_available")),
        "graph_context_reference_count": len(graph_refs),
        "workflow_context_reference_present": bool(
            workflow_context.get("workflow_can_reference_source_context")
            and workflow_context.get("workflow_can_reference_graph_context")
        ),
        "workflow_can_reference_context_without_mutation": bridge_ready,
        "context_navigation_only": context_navigation_only,
        "mutation_authority_false": mutation_authority_false,
        "autonomous_mutation_allowed": False,
        "context_bridge": bridge,
        "evidence_refs": sorted(
            set(
                present
                + list(bridge.get("evidence_refs") or [])
                + source_package_paths
                + workflow_read_paths
            )
        ),
        "blockers": blockers,
    }


def _studio_cockpit_check(root: Path, approval_check: dict[str, Any]) -> dict[str, Any]:
    evidence_refs = [
        "runtime/studio/approval_center_panel.py",
        "runtime/studio/shell/panel_registry.py",
        "runtime/studio/dashboard.py",
        "runtime/studio/dashboard_app.py",
        "runtime/studio/runtime_startup_controls.py",
        "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
    ]
    present = [ref for ref in evidence_refs if _path_exists(root, ref)]
    return {
        "id": "studio_cockpit",
        "status": "complete_enough_internal_mvp" if present else "partial_or_unverified",
        "approvals_visible": approval_check.get("approval_artifact_count", 0) > 0,
        "pending_approvals_visible": approval_check.get("pending_count", 0) > 0,
        "runtime_health_visible": _path_exists(root, "runtime/studio/runtime_startup_controls.py"),
        "packaged_native_studio_required_for_mvp": False,
        "evidence_refs": present,
        "blockers": [] if present else ["studio_cockpit_evidence_not_found"],
    }


def _scope_lock_check(root: Path) -> dict[str, Any]:
    evidence_refs = [
        "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
        "06_AGENTS/ChaseOS-MVP-Consolidation-Map.md",
        "06_AGENTS/ChaseOS-MVP-Completion-Audit.md",
        "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
    ]
    present = [ref for ref in evidence_refs if _path_exists(root, ref)]
    tracked_chat = _tracked_chat_approval_resolution(root)
    p0_current_blocker_ids = ["openai_secret_reference"]
    p1_pending_decision_ids = (
        ["pending_chat_approval_decision"]
        if tracked_chat.get("pending_operator_decision")
        else []
    )
    p1_next_lane_ids = [
        "provider_backed_chat_studio_after_secret_reference",
        "broader_approval_consumption_coverage",
        "additional_ventureops_client_scopes",
        "revenue_or_external_delivery_after_separate_approval",
    ]
    p2_parked_lane_ids = [
        "packaged_native_studio",
        "broad_browser_system_automation",
        "autonomous_graph_source_mutation",
    ]
    p0_p1_p2_map_present = bool(
        p0_current_blocker_ids and p1_next_lane_ids and p2_parked_lane_ids
    )
    return {
        "id": "mvp_scope_lock",
        "status": "current_scope_locked_for_operator_unblock" if len(present) >= 2 else "partial_or_unverified",
        "p0_current_blocker_ids": p0_current_blocker_ids,
        "p1_pending_decision_ids": p1_pending_decision_ids,
        "p1_next_lane_ids": p1_next_lane_ids,
        "p2_parked_lane_ids": p2_parked_lane_ids,
        "p0_count": len(p0_current_blocker_ids),
        "p1_count": len(p1_pending_decision_ids) + len(p1_next_lane_ids),
        "p2_count": len(p2_parked_lane_ids),
        "p0_p1_p2_map_present": p0_p1_p2_map_present,
        "first_usable_mvp_scope_locked": len(present) >= 2 and p0_p1_p2_map_present,
        "p0": [
            "OpenAI or approved alternate provider secret reference",
        ],
        "p1": [
            *(
                ["Operator decision for pending Chat approval artifact"]
                if p1_pending_decision_ids
                else []
            ),
            "Broader approval consumption coverage",
            "Studio cockpit polish and status aggregation",
            "Provider live probe after approved secret reference",
            "Additional VentureOps client scopes or revenue/external-delivery proof after separate approval",
        ],
        "p2": [
            "Packaged native Studio",
            "Broad browser/system automation",
            "Autonomous graph/source mutation",
        ],
        "evidence_refs": present,
        "blockers": []
        if len(present) >= 2 and p0_p1_p2_map_present
        else ["mvp_scope_lock_evidence_sparse"],
    }


def _repo_truth_check(root: Path) -> dict[str, Any]:
    latest_writeback_records = _latest_mvp_writeback_record_paths(root)
    evidence_refs = [
        "README.md",
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "00_HOME/Now.md",
        "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
        "06_AGENTS/ChaseOS-MVP-Consolidation-Map.md",
        "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
        "runtime/mvp_readiness_gate.py",
        "runtime/studio/dashboard.py",
        *MVP_WRITEBACK_INDEX_PATHS,
        *MVP_LATEST_WRITEBACK_RECORD_PATHS,
        *latest_writeback_records,
    ]
    present = [ref for ref in evidence_refs if _path_exists(root, ref)]
    return {
        "id": "repo_truth_consolidation",
        "status": "current_map_present" if len(present) >= 5 else "partial_or_unverified",
        "evidence_refs": _ordered_unique(
            present
            + MVP_WRITEBACK_INDEX_PATHS
            + MVP_LATEST_WRITEBACK_RECORD_PATHS
            + latest_writeback_records
        ),
        "blockers": [] if len(present) >= 5 else ["repo_truth_current_state_map_evidence_sparse"],
    }


def _full_system_control_check(root: Path) -> dict[str, Any]:
    boundary = build_mvp_system_control_boundary(root)
    authority = boundary.get("authority") if isinstance(boundary.get("authority"), dict) else {}
    cdp = (
        boundary.get("cdp_read_only_boundary")
        if isinstance(boundary.get("cdp_read_only_boundary"), dict)
        else {}
    )
    browser_system_automation_gated = (
        authority.get("browser_system_automation_allowed_now") is False
        and cdp.get("execution_enabled") is False
        and cdp.get("browser_launch_attempted") is False
        and cdp.get("cdp_connection_attempted") is False
    )
    host_mutation_false = authority.get("host_mutation_allowed_now") is False
    workflow_replay_gated = authority.get("workflow_replay_allowed_now") is False
    approval_provider_agent_bus_blocked = all(
        authority.get(key) is False
        for key in [
            "provider_calls_allowed",
            "approval_execution_allowed",
            "approval_consumption_allowed",
            "agent_bus_task_write_allowed",
        ]
    )
    credential_session_profile_access_blocked = all(
        authority.get(key) is False
        for key in [
            "credential_value_read_allowed",
            "cookie_or_session_read_allowed",
            "real_browser_profile_allowed",
        ]
    ) and all(
        cdp.get(key) is False
        for key in ["credential_value_read", "cookie_or_session_read", "real_profile_used"]
    )
    cdp_no_execution_proof = all(
        cdp.get(key) is False
        for key in [
            "execution_enabled",
            "browser_launch_attempted",
            "cdp_connection_attempted",
            "approval_request_written",
            "files_modified",
            "canonical_files_mutated",
        ]
    )
    future_local_proof_requires_separate_approval = (
        bool(boundary.get("future_allowed_scope_after_separate_approval"))
        and cdp.get("approval_artifact_supplied") is False
        and cdp.get("approval_status_approved") is False
    )
    return {
        "id": "full_system_control_boundary",
        "status": boundary.get("status"),
        "browser_system_automation_allowed_now": authority.get("browser_system_automation_allowed_now"),
        "host_mutation_allowed_now": authority.get("host_mutation_allowed_now"),
        "browser_system_automation_gated": browser_system_automation_gated,
        "host_mutation_false": host_mutation_false,
        "workflow_replay_gated": workflow_replay_gated,
        "approval_provider_agent_bus_blocked": approval_provider_agent_bus_blocked,
        "credential_session_profile_access_blocked": credential_session_profile_access_blocked,
        "cdp_no_execution_proof": cdp_no_execution_proof,
        "approval_required_before_any_control": True,
        "future_local_proof_requires_separate_approval": future_local_proof_requires_separate_approval,
        "boundary": boundary,
        "evidence_refs": list(boundary.get("evidence_refs") or []),
        "blockers": list(boundary.get("blockers") or []),
    }


def _pass_row(pass_number: int, name: str, status: str, evidence_refs: list[str], blockers: list[str]) -> dict[str, Any]:
    return {
        "pass": pass_number,
        "name": name,
        "status": status,
        "evidence_refs": evidence_refs,
        "blockers": blockers,
    }


def _build_next_action_queue(
    provider: dict[str, Any],
    ventureops: dict[str, Any],
    approvals: dict[str, Any],
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    if provider.get("blockers"):
        queue.append(
            {
                "order": 1,
                "id": "openai_secret_reference",
                "priority": "P0",
                "sector": "provider_credentials",
                "pass": 3,
                "status": provider.get("status"),
                "action": "Provide a resolvable local OpenAI secret reference and update setup metadata to reference its name only.",
                "why_it_matters": "Unblocks provider-backed Chat/Studio execution after no-secret validation and explicit live-probe approval.",
                "handoff_guide_path": MVP_OPENAI_SECRET_REFERENCE_CURRENT_HANDOFF_GUIDE_PATH,
                "safe_next_command": provider.get("safe_next_command"),
                "validation_command": provider.get("setup_provider_validation_command"),
                **_provider_secret_reference_action_fields(provider),
                "operator_handoff_steps": list(provider.get("operator_handoff_steps") or []),
                "missing_inputs": ["resolvable_openai_secret_reference"],
                "can_codex_execute_now": False,
                "requires_operator_secret_reference": True,
                "requires_operator_client_input": False,
                "requires_operator_approval_decision": False,
                "live_execution_allowed_now": False,
            }
        )
    if ventureops.get("blockers"):
        queue.append(
            {
                "order": len(queue) + 1,
                "id": "ventureops_real_client_scope",
                "priority": "P0",
                "sector": "ventureops_real_use",
                "pass": 7,
                "status": ventureops.get("status"),
                "action": ventureops.get("next_required_action"),
                "why_it_matters": "Unblocks the first real-client VentureOps proof after typed scope approval and evidence packets exist.",
                "safe_next_command": ventureops.get("next_safe_command"),
                "validation_command": ventureops.get("real_client_input_manifest_command"),
                "missing_inputs": list(ventureops.get("missing_inputs") or []),
                "provided_inputs": dict(ventureops.get("provided_inputs") or {}),
                "can_codex_execute_now": False,
                "requires_operator_secret_reference": False,
                "requires_operator_client_input": True,
                "requires_operator_approval_decision": False,
                "live_execution_allowed_now": False,
            }
        )
    if approvals.get("operator_decision_required"):
        queue.append(
            {
                "order": len(queue) + 1,
                "id": "pending_chat_approval_decision",
                "priority": "P1",
                "sector": "studio_approvals",
                "pass": 5,
                "status": approvals.get("status"),
                "action": approvals.get("required_operator_input"),
                "why_it_matters": "Clears or advances the latest pending Chat proposal through the approval lane.",
                "safe_next_command": approvals.get("approval_consumption_readiness_command"),
                "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
                "approval_id": PENDING_CHAT_APPROVAL_ID,
                "approval_consumption_readiness_command": approvals.get("approval_consumption_readiness_command"),
                "approval_consumption_executor_command_template": approvals.get(
                    "approval_consumption_executor_command_template"
                ),
                "operator_handoff_steps": list(approvals.get("operator_handoff_steps") or []),
                "can_codex_execute_now": False,
                "requires_operator_secret_reference": False,
                "requires_operator_client_input": False,
                "requires_operator_approval_decision": True,
                "live_execution_allowed_now": False,
            }
        )
    return queue


def _schema_field(
    *,
    name: str,
    type: str,
    required: bool,
    secret_policy: str,
    current_state: dict[str, Any] | None = None,
    description: str | None = None,
    allowed_values: list[str] | None = None,
    example: str | None = None,
    requirement: str | None = None,
    validation_command: str | None = None,
) -> dict[str, Any]:
    field: dict[str, Any] = {
        "name": name,
        "type": type,
        "required": required,
        "secret_policy": secret_policy,
    }
    if current_state is not None:
        field["current_state"] = current_state
    if description:
        field["description"] = description
    if allowed_values:
        field["allowed_values"] = allowed_values
    if example:
        field["example"] = example
    if requirement:
        field["requirement"] = requirement
    if validation_command:
        field["validation_command"] = validation_command
    return field


def _build_operator_input_schema(gate: dict[str, Any]) -> list[dict[str, Any]]:
    """Build typed operator-input requirements without embedding secret or client values."""

    checks = gate.get("checks") if isinstance(gate.get("checks"), dict) else {}
    provider = checks.get("provider_credentials") if isinstance(checks.get("provider_credentials"), dict) else {}
    ventureops = checks.get("ventureops") if isinstance(checks.get("ventureops"), dict) else {}
    approvals = checks.get("studio_approvals") if isinstance(checks.get("studio_approvals"), dict) else {}
    action_ids = {item.get("id") for item in gate.get("next_action_queue") or []}

    schema: list[dict[str, Any]] = []
    if "openai_secret_reference" in action_ids:
        schema.append(
            {
                "id": "openai_secret_reference",
                "priority": "P0",
                "sector": "provider_credentials",
                "pass": 3,
                "status": provider.get("status"),
                "input_mode": "operator_supplied_secret_reference_metadata",
                "can_codex_collect_value": False,
                "can_codex_validate_reference_without_secret_read": True,
                "safe_command_template": provider.get("safe_next_command"),
                "validation_command": provider.get("setup_provider_validation_command"),
                "operator_handoff_steps": list(provider.get("operator_handoff_steps") or []),
                "fields": [
                    _schema_field(
                        name="secret_reference_target",
                        type="secret-reference-name",
                        required=True,
                        secret_policy="reference_name_only_no_secret_value",
                        description=(
                            "Name of a local OpenAI secret reference, such as OPENAI_API_KEY in the "
                            "gitignored ChaseOS .env file or an approved environment variable; the actual "
                            "API key value must not be pasted into tracked ChaseOS files, chat, or logs."
                        ),
                        example="OPENAI_API_KEY",
                        current_state={
                            "reference_target_configured": bool(
                                provider.get("secret_reference_target")
                                and not provider.get("secret_reference_target_is_placeholder")
                            ),
                            "reference_target_is_placeholder": bool(
                                provider.get("secret_reference_target_is_placeholder")
                            ),
                            "reference_resolvable": bool(provider.get("secret_reference_resolvable")),
                            "probe_source": provider.get("secret_reference_probe_source"),
                            "probe_error": provider.get("secret_reference_probe_error"),
                        },
                        validation_command=provider.get("setup_provider_validation_command"),
                    )
                ],
                "boundary": {
                    "secret_value_required_in_packet": False,
                    "secret_value_visible": False,
                    "provider_call_allowed_by_schema": False,
                    "metadata_write_requires_operator_confirmation": True,
                    "outside_repo_secret_reference_required_first": True,
                },
            }
        )

    if "ventureops_real_client_scope" in action_ids:
        provided_inputs = dict(ventureops.get("provided_inputs") or {})
        missing_inputs = set(str(item) for item in ventureops.get("missing_inputs") or [])
        approval_output_group_missing = "approval_output_path or approval_artifact_path" in missing_inputs

        def venture_state(name: str, *, group_missing: bool = False) -> dict[str, Any]:
            return {
                "provided": bool(provided_inputs.get(name)),
                "missing": bool(group_missing or name in missing_inputs),
            }

        schema.append(
            {
                "id": "ventureops_real_client_scope",
                "priority": "P0",
                "sector": "ventureops_real_use",
                "pass": 7,
                "status": ventureops.get("status"),
                "input_mode": "operator_supplied_client_scope_metadata_and_repo_paths",
                "can_codex_collect_value": False,
                "can_codex_run_live_workflow_without_scope_packet": False,
                "safe_command_template": ventureops.get("next_safe_command"),
                "validation_command": ventureops.get("real_client_input_manifest_command"),
                "fields": [
                    _schema_field(
                        name="client_label",
                        type="string",
                        required=True,
                        secret_policy="approved_label_only_no_private_client_material",
                        description="Operator-approved client label for matching evidence packets.",
                        current_state=venture_state("client_label"),
                    ),
                    _schema_field(
                        name="client_approved_scope_id",
                        type="string",
                        required=True,
                        secret_policy="approval_metadata_only",
                        description="Operator-approved scope identifier that ties the workflow to a bounded client scope.",
                        current_state=venture_state("client_approved_scope_id"),
                    ),
                    _schema_field(
                        name="approval_id",
                        type="string",
                        required=True,
                        secret_policy="approval_metadata_only",
                        description="Approval artifact identifier used to match scope, packet, and later workflow evidence.",
                        current_state=venture_state("approval_id"),
                    ),
                    _schema_field(
                        name="approved_read_paths",
                        type="list[repo-relative-path]",
                        required=True,
                        secret_policy="paths_only_no_client_data_inline",
                        description="Repo-relative paths the operator has approved for this real-client proof.",
                        current_state=venture_state("approved_read_paths"),
                    ),
                    _schema_field(
                        name="approval_output_path",
                        type="repo-relative-path",
                        required=False,
                        secret_policy="path_only_no_client_data_inline",
                        description="Destination for a newly authored scope approval artifact.",
                        requirement="at_least_one_of:approval_output_path,approval_artifact_path",
                        current_state=venture_state("approval_output_path", group_missing=approval_output_group_missing),
                    ),
                    _schema_field(
                        name="approval_artifact_path",
                        type="repo-relative-path",
                        required=False,
                        secret_policy="path_only_no_client_data_inline",
                        description="Existing scope approval artifact to validate and use for packet authoring.",
                        requirement="at_least_one_of:approval_output_path,approval_artifact_path",
                        current_state=venture_state("approval_artifact_path", group_missing=approval_output_group_missing),
                    ),
                    _schema_field(
                        name="scope_packet_output_path",
                        type="repo-relative-path",
                        required=False,
                        secret_policy="path_only_generated_scope_packet_destination",
                        description="Destination for the generated real-client scope evidence packet.",
                        requirement="required_after_valid_approval_artifact_matches_manifest_inputs",
                        current_state=venture_state("scope_packet_output_path"),
                    ),
                ],
                "boundary": {
                    "client_private_material_allowed_inline": False,
                    "client_data_ingestion_allowed_by_schema": False,
                    "external_send_allowed_by_schema": False,
                    "provider_call_allowed_by_schema": False,
                },
            }
        )

    if "pending_chat_approval_decision" in action_ids:
        schema.append(
            {
                "id": "pending_chat_approval_decision",
                "priority": "P1",
                "sector": "studio_approvals",
                "pass": 5,
                "status": approvals.get("status"),
                "input_mode": "operator_approval_decision",
                "can_codex_decide_for_operator": False,
                "safe_command_template": approvals.get("approval_consumption_readiness_command"),
                "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
                "operator_handoff_steps": list(approvals.get("operator_handoff_steps") or []),
                "fields": [
                    _schema_field(
                        name="approval_id",
                        type="string",
                        required=True,
                        secret_policy="approval_metadata_only",
                        description="The pending Chat approval artifact that needs an operator decision.",
                        current_state={
                            "approval_id": PENDING_CHAT_APPROVAL_ID,
                            "pending_artifact_tracked": bool(approvals.get("tracked_pending_chat_approval")),
                        },
                    ),
                    _schema_field(
                        name="decision",
                        type="enum",
                        required=True,
                        secret_policy="decision_only_no_execution",
                        description="Operator decision for the pending approval artifact; this schema does not consume it.",
                        allowed_values=["approve", "reject", "leave_pending"],
                    ),
                ],
                "boundary": {
                    "approval_consumption_allowed_by_schema": False,
                    "approval_consumption_readiness_preview_allowed": True,
                    "canonical_mutation_allowed_by_schema": False,
                    "agent_bus_task_write_allowed_by_schema": False,
                    "studio_decision_controls_present": False,
                    "separate_consumption_pass_required_if_approved": True,
                },
            }
        )

    return schema


def _operator_template_placeholder(group_id: str, field: dict[str, Any]) -> Any:
    name = str(field.get("name") or "")
    field_type = str(field.get("type") or "")
    if name == "secret_reference_target":
        return "OPENAI_API_KEY"
    if name == "client_label":
        return "<operator-approved-client-label>"
    if name == "client_approved_scope_id":
        return "<operator-approved-scope-id>"
    if name == "approval_id":
        return PENDING_CHAT_APPROVAL_ID if group_id == "pending_chat_approval_decision" else "<approval-id>"
    if name == "approved_read_paths":
        return ["03_INPUTS/<approved-client-scope>/redacted-source.md"]
    if name == "approval_output_path":
        return "07_LOGS/Workflow-Proofs/<date>_ventureops-scope-approval.json"
    if name == "approval_artifact_path":
        return "07_LOGS/Workflow-Proofs/<date>_ventureops-scope-approval.json"
    if name == "scope_packet_output_path":
        return "07_LOGS/Workflow-Proofs/<date>_ventureops-scope-evidence.json"
    if name == "decision":
        return "leave_pending"
    if field.get("allowed_values"):
        return list(field.get("allowed_values") or [])[0]
    if field_type.startswith("list["):
        return ["<repo-relative-path>"]
    return f"<{name or 'value'}>"


def _build_operator_input_template(schema: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a fillable operator template from the typed schema."""

    groups: list[dict[str, Any]] = []
    for item in schema:
        group_id = str(item.get("id") or "")
        fields: list[dict[str, Any]] = []
        template_values: dict[str, Any] = {}
        for field in item.get("fields") or []:
            field_name = str(field.get("name") or "")
            placeholder = _operator_template_placeholder(group_id, field)
            template_values[field_name] = placeholder
            fields.append(
                {
                    "name": field_name,
                    "placeholder": placeholder,
                    "type": field.get("type"),
                    "required": bool(field.get("required")),
                    "secret_policy": field.get("secret_policy"),
                    "allowed_values": list(field.get("allowed_values") or []),
                    "requirement": field.get("requirement"),
                    "current_state": dict(field.get("current_state") or {}),
                }
            )
        groups.append(
            {
                "id": group_id,
                "priority": item.get("priority"),
                "sector": item.get("sector"),
                "status": item.get("status"),
                "input_mode": item.get("input_mode"),
                "template_values": template_values,
                "fields": fields,
                "validation_command": item.get("validation_command"),
                "safe_command_template": item.get("safe_command_template"),
                "boundary": dict(item.get("boundary") or {}),
            }
        )

    return {
        "version": OPERATOR_INPUT_TEMPLATE_VERSION,
        "read_only": True,
        "intended_use": "copy_field_names_and_replace_placeholders_with_operator-approved_references_or_paths_only",
        "groups": groups,
        "forbidden_values": [
            "api_key_value",
            "secret_value",
            "wallet_key",
            "seed_phrase",
            "customer_credential",
            "private_client_material_inline",
        ],
        "boundary": {
            "secret_values_allowed": False,
            "private_client_material_inline_allowed": False,
            "provider_calls_allowed": False,
            "approval_consumption_allowed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _extract_operator_input_values(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract operator-provided group values from supported packet shapes."""

    if isinstance(payload.get("operator_input_values"), dict):
        return {
            str(group_id): dict(values)
            for group_id, values in payload["operator_input_values"].items()
            if isinstance(values, dict)
        }
    if isinstance(payload.get("groups"), list):
        values: dict[str, dict[str, Any]] = {}
        for group in payload["groups"]:
            if not isinstance(group, dict) or not group.get("id"):
                continue
            raw_values = group.get("values")
            if raw_values is None:
                raw_values = group.get("template_values")
            if isinstance(raw_values, dict):
                values[str(group["id"])] = dict(raw_values)
        return values
    template = payload.get("operator_input_template")
    if isinstance(template, dict) and isinstance(template.get("groups"), list):
        return _extract_operator_input_values(template)
    return {
        str(group_id): dict(values)
        for group_id, values in payload.items()
        if isinstance(group_id, str) and isinstance(values, dict)
    }


def _looks_unreplaced(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        return not text or text in PLACEHOLDER_SECRET_REFS or ("<" in text and ">" in text)
    if isinstance(value, list):
        return not value or any(_looks_unreplaced(item) for item in value)
    return False


def _looks_like_secret_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    lowered = text.lower()
    secret_prefixes = ("sk-", "sk_", "xoxb-", "xoxp-", "ghp_", "gho_", "ghu_", "github_pat_")
    return bool(
        text.startswith(secret_prefixes)
        or "-----begin " in lowered
        or "api-key:" in lowered
        or "\n" in text
        or "\r" in text
        or len(text) > 120
    )


def _path_validation(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return {"ok": False, "error": "path_missing"}
    text = value.strip().replace("\\", "/")
    if _looks_unreplaced(text):
        return {"ok": False, "error": "placeholder_not_replaced"}
    candidate = Path(text)
    if candidate.is_absolute():
        return {"ok": False, "error": "absolute_path_not_allowed"}
    if ".." in candidate.parts:
        return {"ok": False, "error": "parent_traversal_not_allowed"}
    return {"ok": True, "error": None}


def _validate_operator_field(
    *,
    root: Path,
    group_id: str,
    field: dict[str, Any],
    value: Any,
    value_present: bool,
) -> dict[str, Any]:
    name = str(field.get("name") or "")
    field_type = str(field.get("type") or "")
    required = bool(field.get("required"))
    errors: list[str] = []
    warnings: list[str] = []
    placeholder_unreplaced = value_present and _looks_unreplaced(value)

    if required and not value_present:
        errors.append("required_field_missing")
    if placeholder_unreplaced:
        errors.append("placeholder_not_replaced")

    result: dict[str, Any] = {
        "name": name,
        "type": field_type,
        "required": required,
        "provided": value_present,
        "candidate_value_visible": False,
        "placeholder_unreplaced": placeholder_unreplaced,
        "secret_policy": field.get("secret_policy"),
        "allowed_values": list(field.get("allowed_values") or []),
        "requirement": field.get("requirement"),
        "errors": errors,
        "warnings": warnings,
    }

    if name == "secret_reference_target" and value_present and not placeholder_unreplaced:
        if _looks_like_secret_value(value):
            errors.append("candidate_looks_like_secret_value_not_reference_name")
            result["secret_reference_probe"] = {
                "checked": False,
                "exists": False,
                "source": None,
                "error": "candidate_looks_like_secret_value",
            }
        elif not isinstance(value, str):
            errors.append("secret_reference_target_must_be_string")
        else:
            probe = _probe_secret_reference(root, "env-var-or-local-secret-ref", value.strip())
            result["secret_reference_probe"] = {
                "checked": bool(probe.get("checked")),
                "exists": bool(probe.get("exists")),
                "source": probe.get("source"),
                "error": probe.get("error"),
            }
            if not probe.get("exists"):
                errors.append("secret_reference_not_resolved")

    if name == "decision" and value_present and not placeholder_unreplaced:
        allowed = set(field.get("allowed_values") or [])
        if value not in allowed:
            errors.append("decision_not_allowed")

    if name == "approval_id" and group_id == "pending_chat_approval_decision" and value_present:
        result["approval_id_matches_tracked_pending"] = value == PENDING_CHAT_APPROVAL_ID
        if value != PENDING_CHAT_APPROVAL_ID:
            errors.append("approval_id_does_not_match_tracked_pending")

    if field_type == "repo-relative-path" and value_present:
        path_result = _path_validation(value)
        result["path_policy"] = path_result
        if not path_result.get("ok"):
            errors.append(str(path_result.get("error")))

    if field_type == "list[repo-relative-path]" and value_present:
        if not isinstance(value, list) or not value:
            errors.append("repo_relative_path_list_required")
            result["path_policy"] = {"ok": False, "count": 0, "existing_path_count": 0}
        else:
            path_results = [_path_validation(item) for item in value]
            valid_paths = [item for item in value if isinstance(item, str) and _path_validation(item).get("ok")]
            existing_count = sum(1 for item in valid_paths if (root / item).exists())
            invalid_errors = [item.get("error") for item in path_results if not item.get("ok")]
            result["path_policy"] = {
                "ok": not invalid_errors,
                "count": len(value),
                "existing_path_count": existing_count,
                "invalid_count": len(invalid_errors),
                "errors": sorted(set(str(error) for error in invalid_errors if error)),
            }
            if invalid_errors:
                errors.append("repo_relative_path_list_invalid")

    result["ok"] = not errors
    return result


def _build_safe_followup_plan(groups: list[dict[str, Any]], accepted: bool) -> dict[str, Any]:
    step_specs = {
        "openai_secret_reference": {
            "id": "setup_provider_secret_reference_metadata",
            "label": "Preview then update provider setup metadata to reference the local secret name only.",
            "confirmation_command_template": OPENAI_SETUP_METADATA_WRITE_COMMAND,
            "writes_if_operator_confirms": ["runtime/setup_state.json metadata only"],
            "proof_after_followup": "python -m runtime.cli.main setup provider validate openai --json",
            "preconditions": [
                "operator has already created or confirmed the local gitignored secret reference",
                "dry-run preview reports writes_setup_state=false before live metadata write",
                "no API key value is pasted into repo, chat, logs, or setup metadata",
            ],
        },
        "ventureops_real_client_scope": {
            "id": "author_ventureops_scope_approval_packet",
            "label": "Author the governed VentureOps real-client scope approval packet from approved metadata and paths.",
            "writes_if_operator_confirms": ["operator-selected VentureOps approval artifact path"],
            "proof_after_followup": "python -m runtime.cli.main ventureops real-client-input-manifest --json",
        },
        "pending_chat_approval_decision": {
            "id": "review_pending_chat_approval_decision",
            "label": "Review the pending Chat approval decision and preview exact-once readiness before any executor pass.",
            "confirmation_command_template": PENDING_CHAT_APPROVAL_EXECUTOR_COMMAND_TEMPLATE,
            "writes_if_operator_confirms": ["approval decision artifact only in a separate governed pass"],
            "proof_after_followup": "python -m runtime.cli.main studio approval-center-panel --json",
            "preconditions": [
                "operator has chosen approve, reject, or leave_pending",
                "exact-once consumption readiness preview has been inspected for this approval id",
                "approval consumption remains a separate governed pass",
            ],
        },
    }
    steps: list[dict[str, Any]] = []
    for group in groups:
        group_id = str(group.get("id") or "")
        spec = step_specs.get(group_id)
        if not spec:
            continue
        group_valid = group.get("status") == "valid_for_safe_followup"
        steps.append(
            {
                "order": len(steps) + 1,
                "id": spec["id"],
                "source_group_id": group_id,
                "priority": group.get("priority"),
                "status": "ready_template_only" if group_valid else "blocked_input_validation",
                "label": spec["label"],
                "command_template": group.get("safe_command_template"),
                "confirmation_command_template": spec.get("confirmation_command_template"),
                "validation_command": group.get("validation_command"),
                "proof_after_followup": spec["proof_after_followup"],
                "preconditions": list(spec.get("preconditions") or []),
                "writes_if_operator_confirms": spec["writes_if_operator_confirms"],
                "candidate_values_visible": False,
                "requires_operator_confirmation": True,
                "execution_allowed_now": False,
            }
        )

    return {
        "status": "ready_for_operator_confirmed_followup"
        if accepted
        else "blocked_until_input_validation_passes",
        "read_only": True,
        "candidate_values_visible": False,
        "command_values_filled": False,
        "execution_authority_granted": False,
        "next_steps": steps,
        "blocked_step_ids": [
            step["id"] for step in steps if step.get("status") == "blocked_input_validation"
        ],
        "notes": [
            "Follow-up commands are templates only; replace values locally under operator control.",
            "Validation success does not approve provider calls, approval consumption, Agent Bus writes, external sends, browser/host control, or canonical mutation.",
        ],
    }


def _compare_operator_input_source_context(
    input_payload: dict[str, Any] | None,
    *,
    completion_decision: dict[str, Any],
    barrier: dict[str, Any],
    completion_safety_contract: dict[str, Any],
) -> dict[str, Any]:
    payload = input_payload if isinstance(input_payload, dict) else {}
    source_decision = (
        payload.get("completion_decision")
        if isinstance(payload.get("completion_decision"), dict)
        else {}
    )
    source_barrier = (
        payload.get("autonomous_completion_barrier")
        if isinstance(payload.get("autonomous_completion_barrier"), dict)
        else {}
    )
    source_safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    current_safety = completion_safety_contract
    present = bool(source_decision or source_barrier or source_safety)
    checks = [
        ("completion_decision.objective_achieved", source_decision.get("objective_achieved"), completion_decision.get("objective_achieved")),
        (
            "completion_decision.safe_to_call_update_goal_complete",
            source_decision.get("safe_to_call_update_goal_complete"),
            completion_decision.get("safe_to_call_update_goal_complete"),
        ),
        ("completion_decision.operator_input_ids", list(source_decision.get("operator_input_ids") or []), list(completion_decision.get("operator_input_ids") or [])),
        ("completion_decision.p0_blocker_ids", list(source_decision.get("p0_blocker_ids") or []), list(completion_decision.get("p0_blocker_ids") or [])),
        ("completion_decision.p1_decision_ids", list(source_decision.get("p1_decision_ids") or []), list(completion_decision.get("p1_decision_ids") or [])),
        ("autonomous_completion_barrier.update_goal_allowed", source_barrier.get("update_goal_allowed"), barrier.get("update_goal_allowed")),
        (
            "autonomous_completion_barrier.covered_numbered_mvp_row_count",
            source_barrier.get("covered_numbered_mvp_row_count"),
            barrier.get("covered_numbered_mvp_row_count"),
        ),
        (
            "autonomous_completion_barrier.numbered_mvp_row_count",
            source_barrier.get("numbered_mvp_row_count"),
            barrier.get("numbered_mvp_row_count"),
        ),
        ("autonomous_completion_barrier.p0_blocker_ids", list(source_barrier.get("p0_blocker_ids") or []), list(barrier.get("p0_blocker_ids") or [])),
        ("autonomous_completion_barrier.p1_decision_ids", list(source_barrier.get("p1_decision_ids") or []), list(barrier.get("p1_decision_ids") or [])),
    ]
    if source_safety:
        checks.extend(
            [
                ("completion_safety_contract.status", source_safety.get("status"), current_safety.get("status")),
                ("completion_safety_contract.update_goal_allowed", source_safety.get("update_goal_allowed"), current_safety.get("update_goal_allowed")),
                (
                    "completion_safety_contract.checklist_coverage_is_not_completion",
                    source_safety.get("checklist_coverage_is_not_completion"),
                    current_safety.get("checklist_coverage_is_not_completion"),
                ),
                ("completion_safety_contract.operator_input_ids", list(source_safety.get("operator_input_ids") or []), list(current_safety.get("operator_input_ids") or [])),
                ("completion_safety_contract.p0_blocker_ids", list(source_safety.get("p0_blocker_ids") or []), list(current_safety.get("p0_blocker_ids") or [])),
            ]
        )
    mismatches = [
        {"field": field, "current_value": current, "source_value_present": source is not None}
        for field, source, current in checks
        if present and source != current
    ]
    return {
        "present": present,
        "matches_current": (not mismatches) if present else None,
        "stale_context_detected": bool(mismatches),
        "mismatch_fields": [item["field"] for item in mismatches],
        "candidate_values_visible": False,
        "source_values_echoed": False,
    }


def build_mvp_operator_input_validation(
    vault_root: str | Path = ".",
    input_payload: dict[str, Any] | None = None,
    *,
    source_path: str | None = None,
) -> dict[str, Any]:
    """Validate filled operator-input references/paths without echoing candidate values."""

    root = Path(vault_root).resolve()
    packet = build_mvp_operator_unblock_packet(root)
    schema = list(packet.get("operator_input_schema") or [])
    completion_decision = (
        packet.get("completion_decision")
        if isinstance(packet.get("completion_decision"), dict)
        else {}
    )
    barrier = (
        packet.get("autonomous_completion_barrier")
        if isinstance(packet.get("autonomous_completion_barrier"), dict)
        else {}
    )
    safety = (
        packet.get("completion_safety_contract")
        if isinstance(packet.get("completion_safety_contract"), dict)
        else _completion_safety_contract(
            completion_decision,
            barrier,
            covered_count=int(barrier.get("covered_numbered_mvp_row_count") or 0),
            total_count=int(barrier.get("numbered_mvp_row_count") or 0),
        )
    )
    values_by_id = _extract_operator_input_values(input_payload or {})
    source_completion_context = _compare_operator_input_source_context(
        input_payload,
        completion_decision=completion_decision,
        barrier=barrier,
        completion_safety_contract=safety,
    )
    action_by_id = {
        str(item.get("id")): item
        for item in packet.get("next_action_queue") or []
        if isinstance(item, dict) and item.get("id")
    }
    groups: list[dict[str, Any]] = []
    blocker_ids: list[str] = []

    for item in schema:
        group_id = str(item.get("id") or "")
        group_values = values_by_id.get(group_id, {})
        field_results = [
            _validate_operator_field(
                root=root,
                group_id=group_id,
                field=field,
                value=group_values.get(field.get("name")),
                value_present=field.get("name") in group_values,
            )
            for field in item.get("fields") or []
        ]
        errors = [
            f"{field['name']}:{error}"
            for field in field_results
            for error in field.get("errors", [])
        ]

        if group_id == "ventureops_real_client_scope":
            has_approval_output = bool(
                group_values.get("approval_output_path")
                and not _looks_unreplaced(group_values.get("approval_output_path"))
                and _path_validation(group_values.get("approval_output_path")).get("ok")
            )
            has_approval_artifact = bool(
                group_values.get("approval_artifact_path")
                and not _looks_unreplaced(group_values.get("approval_artifact_path"))
                and _path_validation(group_values.get("approval_artifact_path")).get("ok")
            )
            if not (has_approval_output or has_approval_artifact):
                errors.append("approval_output_path_or_approval_artifact_path:at_least_one_required")

        group_ok = not errors
        if not group_ok:
            blocker_ids.append(group_id)
        group_context: dict[str, Any] = {}
        if group_id == "openai_secret_reference":
            action_context = action_by_id.get(group_id, {})
            for key in (
                "current_secret_reference_kind",
                "current_secret_reference_target",
                "current_secret_reference_target_is_placeholder",
                "current_secret_reference_resolvable",
                "secret_reference_probe_source",
                "secret_reference_probe_error",
                "recommended_reference_name",
                "setup_provider_validation_command",
                "setup_wide_validation_command",
                "provider_live_smoke_readiness_command",
                "secret_value_read",
                "secret_value_allowed_in_repo_or_chat",
                "live_network_call_attempted",
                "files_modified",
            ):
                if key in action_context:
                    group_context[key] = action_context.get(key)
        groups.append(
            {
                "id": group_id,
                "priority": item.get("priority"),
                "sector": item.get("sector"),
                "status": "valid_for_safe_followup" if group_ok else "blocked_input_validation",
                "candidate_values_visible": False,
                "provided_field_count": len(group_values),
                "required_field_count": sum(1 for field in item.get("fields") or [] if field.get("required")),
                "field_results": field_results,
                "errors": errors,
                "validation_command": item.get("validation_command"),
                "safe_command_template": item.get("safe_command_template"),
                **group_context,
            }
        )

    accepted = not blocker_ids and not source_completion_context["stale_context_detected"]
    safe_followup_plan = _build_safe_followup_plan(groups, accepted)

    return {
        "ok": accepted,
        "surface": "chaseos_mvp_operator_input_validation",
        "model_version": OPERATOR_INPUT_VALIDATION_VERSION,
        "generated_at_utc": _now_utc(),
        "read_only": True,
        "source_path": source_path,
        "source_values_echoed": False,
        "candidate_values_visible": False,
        "readiness_status": "operator_inputs_valid_for_safe_followup"
        if accepted
        else "blocked_operator_input_validation",
        "accepted_for_safe_followup": accepted,
        "valid": accepted,
        "objective_achieved": bool(completion_decision.get("objective_achieved")),
        "safe_to_call_update_goal_complete": bool(
            completion_decision.get("safe_to_call_update_goal_complete")
        ),
        "operator_input_ids": list(completion_decision.get("operator_input_ids") or []),
        "p0_blocker_ids": list(completion_decision.get("p0_blocker_ids") or []),
        "p1_decision_ids": list(completion_decision.get("p1_decision_ids") or []),
        "blocked_requirement_ids": list(
            completion_decision.get("blocked_requirement_ids") or []
        ),
        "incomplete_or_operator_blocked_requirements": list(
            completion_decision.get("incomplete_or_operator_blocked_requirements") or []
        ),
        "no_safe_autonomous_completion_pass_available": bool(
            barrier.get("no_safe_autonomous_completion_pass_available")
        ),
        "update_goal_allowed": bool(barrier.get("update_goal_allowed")),
        "next_operator_action_id": barrier.get("next_operator_action_id"),
        "next_recommended_pass": barrier.get("next_recommended_pass"),
        "completion_decision": dict(completion_decision),
        "autonomous_completion_barrier": dict(barrier),
        "completion_safety_contract": dict(safety),
        "source_completion_context": source_completion_context,
        "setup_scope_boundary": dict(packet.get("setup_scope_boundary") or {}),
        "required_operator_inputs": list(packet.get("required_operator_inputs") or []),
        "blocked_group_ids": blocker_ids,
        "groups": groups,
        "safe_followup_commands_are_templates_only": True,
        "safe_followup_plan": safe_followup_plan,
        "boundary": {
            "secret_values_visible": False,
            "provider_calls_performed": False,
            "setup_metadata_mutated": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "client_data_ingested": False,
            "external_send_performed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def format_mvp_operator_input_validation(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS MVP Operator Input Validation",
        f"  readiness_status: {payload.get('readiness_status')}",
        f"  accepted_for_safe_followup: {payload.get('accepted_for_safe_followup')}",
        "  groups:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(3, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            4 if barrier_line else 3,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    source_context = (
        payload.get("source_completion_context")
        if isinstance(payload.get("source_completion_context"), dict)
        else {}
    )
    if source_context:
        source_line = (
            "  source_completion_context: "
            + "present="
            + str(source_context.get("present"))
            + " matches_current="
            + str(source_context.get("matches_current"))
            + " stale_context_detected="
            + str(source_context.get("stale_context_detected"))
        )
        lines.insert(
            5 if safety and barrier_line else 4 if (safety or barrier_line) else 3,
            source_line,
        )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    if setup_scope:
        lines.insert(
            len(lines) - 1,
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}",
        )
    for group in payload.get("groups") or []:
        lines.append(f"    - {group.get('id')} [{group.get('priority')}]: {group.get('status')}")
        if group.get("id") == "openai_secret_reference":
            lines.append(
                "      current_secret_reference: "
                f"target={group.get('current_secret_reference_target')} "
                f"placeholder={group.get('current_secret_reference_target_is_placeholder')} "
                f"resolvable={group.get('current_secret_reference_resolvable')} "
                f"error={group.get('secret_reference_probe_error')}"
            )
            if group.get("provider_live_smoke_readiness_command"):
                lines.append(
                    "      provider_live_smoke_readiness: "
                    + str(group.get("provider_live_smoke_readiness_command"))
                )
        if group.get("errors"):
            lines.append(f"      errors: {', '.join(str(error) for error in group.get('errors') or [])}")
    plan = payload.get("safe_followup_plan") or {}
    steps = plan.get("next_steps") if isinstance(plan, dict) else []
    if steps:
        lines.append("  safe_followup_plan:")
        for step in steps:
            lines.append(f"    - {step.get('order')}. {step.get('id')}: {step.get('status')}")
    lines.append("  boundary: read-only validation; candidate values are not echoed; no secret read display, provider call, setup write, approval consumption, Agent Bus write, client ingestion, browser/host control, or canonical mutation")
    return "\n".join(lines)


def _format_autonomous_completion_barrier(payload: dict[str, Any]) -> str | None:
    barrier = (
        payload.get("autonomous_completion_barrier")
        if isinstance(payload.get("autonomous_completion_barrier"), dict)
        else {}
    )
    if not barrier:
        return None
    return (
        "  autonomous_completion_barrier: "
        + "active="
        + str(barrier.get("active"))
        + " rows="
        + str(barrier.get("covered_numbered_mvp_row_count"))
        + "/"
        + str(barrier.get("numbered_mvp_row_count"))
        + " update_goal_allowed="
        + str(barrier.get("update_goal_allowed"))
    )


def _completion_row(
    *,
    pass_number: int,
    id: str,
    success_criterion: str,
    required_evidence: list[str],
    status: str,
    evidence_refs: list[str],
    blockers: list[str],
    criterion_satisfied: bool,
    coverage_judgment: str,
    remaining_required_evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "pass": pass_number,
        "id": id,
        "success_criterion": success_criterion,
        "required_evidence": required_evidence,
        "status": status,
        "criterion_satisfied": criterion_satisfied,
        "coverage_judgment": coverage_judgment,
        "evidence_refs": evidence_refs,
        "blockers": blockers,
        "remaining_required_evidence": remaining_required_evidence or [],
    }


def _build_completion_matrix(
    *,
    repo_truth: dict[str, Any],
    scope_lock: dict[str, Any],
    provider: dict[str, Any],
    approvals: dict[str, Any],
    ventureops: dict[str, Any],
    agent_bus: dict[str, Any],
    studio: dict[str, Any],
    graph: dict[str, Any],
    system_control: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _completion_row(
            pass_number=1,
            id="repo_truth_consolidation",
            success_criterion="Current truth rechecked across roadmap, Now, Agent Bus, Studio, Chat, VentureOps, provider setup, logs, and latest build records.",
            required_evidence=[
                "current-state map",
                "roadmap and Now truth surfaces",
                "Agent Bus, Studio, Chat, VentureOps, and provider setup checks",
                "writeback logs and latest build records",
                "readiness gate pass 1",
                "operator unblock packet",
            ],
            status=str(repo_truth.get("status")),
            criterion_satisfied=not bool(repo_truth.get("blockers")),
            coverage_judgment="Complete for current snapshot; rerun after operator input.",
            evidence_refs=list(repo_truth.get("evidence_refs") or []),
            blockers=list(repo_truth.get("blockers") or []),
        ),
        _completion_row(
            pass_number=2,
            id="mvp_scope_lock",
            success_criterion="First usable MVP scope locked into P0/P1/P2 lanes.",
            required_evidence=[
                "P0 current blocker ids",
                "P1 pending decision ids",
                "P1 next-after-MVP lanes",
                "P2 parked/gated lanes",
                "operator unblock packet",
                "completion audit",
            ],
            status=str(scope_lock.get("status")),
            criterion_satisfied=bool(scope_lock.get("first_usable_mvp_scope_locked"))
            and not bool(scope_lock.get("blockers")),
            coverage_judgment="Complete for current snapshot; update when operator inputs change.",
            evidence_refs=list(scope_lock.get("evidence_refs") or []),
            blockers=list(scope_lock.get("blockers") or []),
        ),
        _completion_row(
            pass_number=3,
            id="credential_readiness",
            success_criterion="Needed API keys and secret references identified without exposing secrets.",
            required_evidence=[
                "credential checklist",
                "credential-only handoff",
                "setup-wide validation",
                "setup provider validation",
                "provider inventory",
                "provider live-smoke readiness",
                "readiness gate provider check",
                "Studio provider key checks",
            ],
            status=str(provider.get("status")),
            criterion_satisfied=True,
            coverage_judgment="Checklist complete and validation fails closed; provider execution remains blocked until the reference resolves.",
            evidence_refs=list(provider.get("evidence_refs") or [])
            + [
                "06_AGENTS/ChaseOS-MVP-Credential-Readiness-Checklist.md",
                MVP_OPENAI_SECRET_REFERENCE_HANDOFF_CARD_PATH,
                MVP_OPENAI_SECRET_REFERENCE_CURRENT_HANDOFF_GUIDE_PATH,
            ],
            blockers=list(provider.get("blockers") or []),
        ),
        _completion_row(
            pass_number=4,
            id="chat_to_approval",
            success_criterion="Chat works as operator intake by creating one approval artifact.",
            required_evidence=[
                "tracked Chat approval artifact",
                "approval id and lifecycle status",
                "action type and target preview",
                "Studio/Chat submitted-by metadata",
                "Approval Center visibility",
                "governed approval lifecycle state",
            ],
            status="complete_for_one_supported_proposal_lane"
            if approvals.get("one_chat_request_created_approval_artifact")
            else "unverified_in_this_gate",
            criterion_satisfied=bool(
                approvals.get("one_chat_request_created_approval_artifact")
                and approvals.get("approval_center_visible")
            ),
            coverage_judgment="Complete for one supported proposal lane.",
            evidence_refs=list(approvals.get("evidence_refs") or []),
            blockers=[]
            if approvals.get("one_chat_request_created_approval_artifact")
            else ["chat_approval_artifact_not_found"],
        ),
        _completion_row(
            pass_number=5,
            id="approval_to_action",
            success_criterion="One approval can be consumed exactly once into a file write or Agent Bus task.",
            required_evidence=[
                "executed approval artifact",
                "exact-once marker",
                "approved target action id",
                "approved target action performed",
                "provider/browser/workflow/canonical side effects false",
                "operator follow-up separated when a Chat approval remains pending",
            ],
            status="complete_for_one_approved_action"
            if approvals.get("executed_or_approved_count", 0) > 0
            else "partial_or_unverified",
            criterion_satisfied=bool(
                approvals.get("executed_or_approved_count", 0) > 0
                and approvals.get("approved_action_id")
                and approvals.get("approval_to_action_exact_once_marker_path")
                and approvals.get("approval_to_action_side_effects_blocked")
            ),
            coverage_judgment="Complete for one approved exact-once action; broader approval classes remain source-specific.",
            evidence_refs=list(approvals.get("evidence_refs") or []),
            blockers=[]
            if approvals.get("approved_action_id")
            else ["executed_or_approved_artifact_not_found"],
        ),
        _completion_row(
            pass_number=6,
            id="agent_bus_lifecycle",
            success_criterion="One runtime task lifecycle is proven: task created, claimed, executed, artifact written, and result logged.",
            required_evidence=[
                "Agent Bus SQLite events",
                "task created event",
                "task claimed by Codex",
                "task started",
                "task completed or safely blocked",
                "result artifact written",
                "result logged",
                "Codex adapter result artifact",
                "stdout/stderr artifacts",
            ],
            status=str(agent_bus.get("status")),
            criterion_satisfied=bool(
                agent_bus.get("task_created")
                and agent_bus.get("task_claimed_by_codex")
                and agent_bus.get("task_started_by_codex")
                and agent_bus.get("task_completed_or_safely_blocked")
                and agent_bus.get("task_artifact_written")
                and agent_bus.get("result_logged")
                and agent_bus.get("adapter_result_matches_task")
                and agent_bus.get("task_created_claimed_executed_artifact_logged")
            ),
            coverage_judgment="Complete as machine-checked MVP bus lifecycle proof.",
            evidence_refs=list(agent_bus.get("evidence_refs") or []),
            blockers=list(agent_bus.get("blockers") or []),
        ),
        _completion_row(
            pass_number=7,
            id="ventureops_real_use",
            success_criterion="One real client-approved VentureOps scope enters the system and proves a real workflow.",
            required_evidence=[
                "client label",
                "client-approved scope id",
                "approval id",
                "approved read paths",
                "typed scope approval artifact",
                "scope evidence packet",
                "live-client workflow proof",
                "not synthetic/demo evidence",
                "external/provider/browser/revenue side effects false",
            ],
            status=str(ventureops.get("status")),
            criterion_satisfied=bool(
                ventureops.get("live_client_workflow_proof_artifact_valid")
                and ventureops.get("typed_scope_approval_artifact_valid")
                and ventureops.get("scope_evidence_packet_valid")
                and ventureops.get("live_client_workflow_proof_valid")
                and ventureops.get("not_synthetic_demo_evidence")
                and ventureops.get("approved_read_path_count", 0) > 0
                and ventureops.get("ventureops_side_effects_blocked")
            ),
            coverage_judgment=(
                "Complete for one scoped local live-client workflow proof; revenue/external delivery remains outside this MVP criterion."
                if ventureops.get("live_client_workflow_proof_artifact_valid")
                else "Blocked; explicit objective requirement not met."
            ),
            evidence_refs=list(ventureops.get("evidence_refs") or []),
            blockers=list(ventureops.get("blockers") or []),
            remaining_required_evidence=[
                "operator supplies real client scope inputs",
                "guarded scope approval artifact is authored",
                "scope evidence packet is authored",
                "live-client workflow proof runs",
            ]
            if not ventureops.get("live_client_workflow_proof_artifact_valid")
            else [],
        ),
        _completion_row(
            pass_number=8,
            id="studio_cockpit",
            success_criterion="Studio is usable as visibility/control cockpit without blocking on native packaging.",
            required_evidence=[
                "Studio dashboard",
                "MVP readiness panel",
                "status visibility",
                "approval visibility",
                "runtime health visibility",
                "blocker visibility",
            ],
            status=str(studio.get("status")),
            criterion_satisfied=not bool(studio.get("blockers")),
            coverage_judgment="Verified for internal MVP cockpit; execution remains gated.",
            evidence_refs=list(studio.get("evidence_refs") or []),
            blockers=list(studio.get("blockers") or []),
        ),
        _completion_row(
            pass_number=9,
            id="graph_source_intelligence",
            success_criterion="Graph/source intelligence is used as context/navigation, not autonomous mutation.",
            required_evidence=[
                "source package refs",
                "graph context refs",
                "workflow context reference",
                "context/navigation only",
                "mutation authority false",
            ],
            status=str(graph.get("status")),
            criterion_satisfied=bool(
                graph.get("workflow_can_reference_context_without_mutation")
                and graph.get("context_navigation_only")
                and graph.get("mutation_authority_false")
            ),
            coverage_judgment="Verified for read-only workflow context.",
            evidence_refs=list(graph.get("evidence_refs") or []),
            blockers=list(graph.get("blockers") or []),
        ),
        _completion_row(
            pass_number=10,
            id="full_system_control_boundary",
            success_criterion="Broad full system control is parked until the MVP is proven.",
            required_evidence=[
                "machine-readable system control boundary",
                "Permission Matrix",
                "Trust Tiers",
                "browser/system automation gated",
                "host mutation false",
                "workflow replay gated",
                "approval/provider/Agent Bus execution blocked",
                "credential/session/profile access blocked",
                "CDP no-execution proof",
                "future local proof requires separate approval",
            ],
            status=str(system_control.get("status")),
            criterion_satisfied=bool(system_control.get("browser_system_automation_gated"))
            and bool(system_control.get("host_mutation_false"))
            and bool(system_control.get("workflow_replay_gated"))
            and bool(system_control.get("approval_provider_agent_bus_blocked"))
            and bool(system_control.get("credential_session_profile_access_blocked"))
            and bool(system_control.get("cdp_no_execution_proof"))
            and bool(system_control.get("future_local_proof_requires_separate_approval")),
            coverage_judgment="Complete as machine-checked boundary; broad control remains excluded from MVP.",
            evidence_refs=list(system_control.get("evidence_refs") or []),
            blockers=list(system_control.get("blockers") or []),
        ),
    ]


def _snapshot_row(
    *,
    id: str,
    label: str,
    status: str,
    evidence: list[str] | None = None,
    next_action: str | None = None,
    boundary: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": id,
        "label": label,
        "status": status,
    }
    if evidence:
        row["evidence"] = evidence
    if next_action:
        row["next_action"] = next_action
    if boundary:
        row["boundary"] = boundary
    return row


def _build_mvp_usecase_snapshot(
    *,
    readiness_status: str,
    provider: dict[str, Any],
    approvals: dict[str, Any],
    ventureops: dict[str, Any],
    agent_bus: dict[str, Any],
    studio: dict[str, Any],
    graph: dict[str, Any],
    system_control: dict[str, Any],
    operator_inputs_required: list[dict[str, Any]],
    next_action_queue: list[dict[str, Any]],
    blocked_requirement_ids: list[str],
) -> dict[str, Any]:
    """Build the plain-language MVP use case snapshot from existing evidence."""

    next_operator_action = next_action_queue[0] if next_action_queue else None
    p0_blocker_ids = [
        str(item.get("id")) for item in operator_inputs_required if item.get("priority") == "P0"
    ]
    p1_decision_ids = [
        str(item.get("id")) for item in operator_inputs_required if item.get("priority") == "P1"
    ]

    usable_now = [
        _snapshot_row(
            id="read_only_operator_status",
            label="Read-only MVP status consolidation",
            status="usable_now",
            evidence=[
                "python -m runtime.cli.main mvp readiness-gate --json",
                "python -m runtime.cli.main mvp operator-unblock-packet --json",
            ],
            boundary="no secret read, provider call, approval consumption, Agent Bus write, browser/host control, or canonical mutation",
        )
    ]
    if approvals.get("approval_artifact_count", 0) > 0:
        usable_now.append(
            _snapshot_row(
                id="chat_to_approval_artifact",
                label="Chat/Studio intake can produce and display approval artifacts",
                status="usable_now_for_one_supported_lane",
                evidence=list(approvals.get("evidence_refs") or []),
                boundary=(
                    "tracked Chat approval was consumed exactly once; additional approval lanes remain governed"
                    if approvals.get("approval_consumption_performed")
                    else "latest pending approval still needs an operator decision before execution"
                ),
            )
        )
    if approvals.get("executed_or_approved_count", 0) > 0:
        usable_now.append(
            _snapshot_row(
                id="approval_to_action",
                label="One approved exact-once approval-to-action path is proven",
                status="usable_now_for_one_approved_task",
                evidence=list(approvals.get("evidence_refs") or []),
                boundary="broader approval classes remain source-specific",
            )
        )
    if agent_bus.get("task_created_claimed_executed_artifact_logged"):
        usable_now.append(
            _snapshot_row(
                id="agent_bus_codex_lifecycle",
                label="Bounded Codex Agent Bus task lifecycle",
                status=str(agent_bus.get("status")),
                evidence=list(agent_bus.get("evidence_refs") or []),
                boundary="task class and runtime permissions remain bounded by task packet and bus policy",
            )
        )
    if ventureops.get("live_client_workflow_proof_artifact_valid"):
        usable_now.append(
            _snapshot_row(
                id="ventureops_scoped_workflow_proof",
                label="One scoped VentureOps workflow proof is discoverable",
                status=str(ventureops.get("status")),
                evidence=list(ventureops.get("evidence_refs") or []),
                boundary="no revenue claim, external delivery, CRM/payment mutation, provider call, browser action, or canonical promotion is implied",
            )
        )
    if not studio.get("blockers"):
        usable_now.append(
            _snapshot_row(
                id="studio_cockpit_visibility",
                label="Studio dashboard cockpit visibility",
                status=str(studio.get("status")),
                evidence=list(studio.get("evidence_refs") or []),
                boundary="visibility only; execution remains governed by separate approvals",
            )
        )
    if graph.get("workflow_can_reference_context_without_mutation"):
        usable_now.append(
            _snapshot_row(
                id="graph_source_context_reference",
                label="Graph/source intelligence can be used as read-only workflow context",
                status=str(graph.get("status")),
                evidence=list(graph.get("evidence_refs") or []),
                boundary="no graph mutation, source promotion, workflow execution, provider call, browser control, or host mutation",
            )
        )

    blocked_now: list[dict[str, Any]] = []
    if provider.get("blockers"):
        blocked_now.append(
            _snapshot_row(
                id="provider_backed_chat_studio",
                label="Provider-backed Chat/Studio responses",
                status=str(provider.get("status")),
                evidence=[str(provider.get("setup_provider_validation_command"))],
                next_action="Provide a resolvable local OpenAI secret reference, then run no-secret validation.",
                boundary="secret reference name only; no API key value in repo or chat",
            )
        )
    if ventureops.get("blockers"):
        blocked_now.append(
            _snapshot_row(
                id="ventureops_real_client_scope",
                label="VentureOps real-client scope proof",
                status=str(ventureops.get("status")),
                evidence=[str(ventureops.get("real_client_input_manifest_command"))],
                next_action=str(ventureops.get("next_required_action")),
                boundary="approved paths and artifacts only; no private client material inline",
            )
        )
    if approvals.get("operator_decision_required"):
        blocked_now.append(
            _snapshot_row(
                id="pending_chat_approval_decision",
                label="Latest pending Chat approval consumption",
                status=str(approvals.get("status")),
                evidence=list(approvals.get("evidence_refs") or []),
                next_action=str(approvals.get("required_operator_input")),
                boundary="Codex cannot decide or consume the approval in this read-only snapshot",
            )
        )

    parked_or_later = [
        _snapshot_row(
            id="full_system_control",
            label="Broad computer/browser/host control",
            status=str(system_control.get("status")),
            evidence=list(system_control.get("evidence_refs") or []),
            boundary="parked until the MVP loop is proven and a separate approval exists",
        ),
        _snapshot_row(
            id="revenue_external_delivery",
            label="Revenue proof, external delivery, CRM/payment mutation",
            status="parked_until_separate_approval",
            boundary="not part of the first MVP proof",
        ),
        _snapshot_row(
            id="n8n_connector_automation",
            label="n8n and broad connector automation",
            status="later_after_mvp_loop",
            boundary="connector effects require separate setup, credentials, and approvals",
        ),
        _snapshot_row(
            id="wallet_exchange_credentials",
            label="Wallet, exchange, and high-risk financial credentials",
            status="out_of_scope_for_mvp",
            boundary="do not add unless a future governed scope explicitly requires it",
        ),
        _snapshot_row(
            id="canonical_memory_mutation",
            label="Autonomous canonical memory/core-state mutation",
            status="gated",
            boundary="read-only context is allowed; governed core writes need explicit authority",
        ),
    ]

    return {
        "surface": "chaseos_mvp_usecase_snapshot",
        "model_version": "chaseos.mvp_usecase_snapshot.v1",
        "current_sector": "MVP Integration / Operator Workflow Activation",
        "readiness_status": readiness_status,
        "current_mvp_usecase": (
            "Governed local operator workflow: Chat or Studio request, approval visibility, "
            "bounded Agent Bus/runtime proof, evidence/log closeout, and Studio status cockpit."
        ),
        "workflow_shape": [
            "operator_request",
            "approval_artifact",
            "bounded_agent_bus_task",
            "runtime_result_artifact",
            "evidence_and_log_closeout",
            "studio_visibility",
        ],
        "current_outcome": (
            "Useful now as a governed local proof and operator cockpit; provider-backed Chat/Studio "
            "execution remains blocked until the P0 secret reference resolves."
        ),
        "usable_now": usable_now,
        "blocked_now": blocked_now,
        "parked_or_later": parked_or_later,
        "p0_blocker_ids": p0_blocker_ids,
        "p1_decision_ids": p1_decision_ids,
        "blocked_requirement_ids": blocked_requirement_ids,
        "next_operator_action_id": next_operator_action.get("id") if next_operator_action else None,
        "next_operator_action_label": next_operator_action.get("action") if next_operator_action else None,
        "first_live_proof_after_operator_input": (
            "Run no-secret provider validation, request a separate guarded live probe approval, "
            "then prove one provider-backed Chat/Studio response through the governed workflow."
        ),
        "authority": {
            "read_only": True,
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_performed": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def build_mvp_readiness_gate(vault_root: str | Path = ".") -> dict[str, Any]:
    """Build the current ChaseOS MVP readiness gate without side effects."""

    root = Path(vault_root).resolve()
    canonical_handoff = _canonical_operator_handoff(root)
    operator_template_artifact = _operator_input_template_artifact(root)
    repo_truth = _repo_truth_check(root)
    scope_lock = _scope_lock_check(root)
    provider = _provider_credential_check(root)
    setup_scope_boundary = _setup_scope_boundary(root, provider)
    approvals = _studio_approval_check(root)
    ventureops = _ventureops_check(root)
    agent_bus = _agent_bus_check(root)
    studio = _studio_cockpit_check(root, approvals)
    graph = _graph_source_check(root)
    system_control = _full_system_control_check(root)

    chat_to_approval_status = (
        "complete_for_one_supported_proposal_lane"
        if approvals.get("approval_artifact_count", 0) > 0
        else "unverified_in_this_gate"
    )
    approval_to_action_status = (
        "complete_for_one_approved_action"
        if approvals.get("executed_or_approved_count", 0) > 0
        else "partial_or_unverified"
    )

    pass_rows = [
        _pass_row(1, "Repo-Truth Consolidation", repo_truth["status"], repo_truth["evidence_refs"], repo_truth["blockers"]),
        _pass_row(2, "MVP Scope Lock", scope_lock["status"], scope_lock["evidence_refs"], scope_lock["blockers"]),
        _pass_row(3, "Credential Readiness", provider["status"], provider["evidence_refs"], provider["blockers"]),
        _pass_row(4, "Chat-to-Approval", chat_to_approval_status, approvals["evidence_refs"], [] if approvals.get("approval_artifact_count", 0) > 0 else ["chat_approval_artifact_not_found"]),
        _pass_row(5, "Approval-to-Action", approval_to_action_status, approvals["evidence_refs"], [] if approvals.get("executed_or_approved_count", 0) > 0 else ["executed_or_approved_artifact_not_found"]),
        _pass_row(6, "Agent Bus Lifecycle", agent_bus["status"], agent_bus["evidence_refs"], agent_bus["blockers"]),
        _pass_row(7, "VentureOps Real-Use", str(ventureops["status"]), ventureops["evidence_refs"], ventureops["blockers"]),
        _pass_row(8, "Studio Cockpit", studio["status"], studio["evidence_refs"], studio["blockers"]),
        _pass_row(9, "Graph / Source Intelligence", graph["status"], graph["evidence_refs"], graph["blockers"]),
        _pass_row(
            10,
            "Full System Control Boundary",
            system_control["status"],
            system_control["evidence_refs"],
            system_control["blockers"],
        ),
    ]

    operator_inputs_required: list[dict[str, Any]] = []
    if provider["blockers"]:
        operator_inputs_required.append(
            {
                "id": "openai_secret_reference",
                "priority": "P0",
                "description": provider["required_operator_input"],
                "safe_next_command": provider["safe_next_command"],
                "reference_presence_check_commands": list(
                    provider.get("reference_presence_check_commands") or []
                ),
                "reference_presence_check_outputs_secret_value": bool(
                    provider.get("reference_presence_check_outputs_secret_value")
                ),
                "validation_command": "python -m runtime.cli.main setup provider validate openai --json",
            }
        )
    if ventureops["blockers"]:
        operator_inputs_required.append(
            {
                "id": "ventureops_real_client_scope",
                "priority": "P0",
                "description": "Provide client_label, client_approved_scope_id, approval_id, approved_read_paths, and approval output or artifact path.",
                "safe_next_command": ventureops["next_safe_command"],
                "validation_command": ventureops["real_client_input_manifest_command"],
                "missing_inputs": ventureops["missing_inputs"],
                "provided_inputs": ventureops["provided_inputs"],
                "next_required_action": ventureops["next_required_action"],
                "ready_to_author_scope_approval": ventureops["ready_to_author_scope_approval"],
                "ready_to_author_scope_packet": ventureops["ready_to_author_scope_packet"],
                "ready_for_live_client_workflow_proof": ventureops["ready_for_live_client_workflow_proof"],
            }
        )
    if approvals["operator_decision_required"]:
        operator_inputs_required.append(
            {
                "id": "pending_chat_approval_decision",
                "priority": "P1",
                "description": approvals["required_operator_input"],
                "approval_id": PENDING_CHAT_APPROVAL_ID,
                "safe_next_command": approvals.get("approval_consumption_readiness_command"),
                "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
                "approval_consumption_readiness_command": approvals.get(
                    "approval_consumption_readiness_command"
                ),
                "approval_consumption_executor_command_template": approvals.get(
                    "approval_consumption_executor_command_template"
                ),
                "approval_consumption_allowed_now": False,
                "requires_operator_approval_decision": True,
            }
        )

    p0_blockers = [item for item in operator_inputs_required if item.get("priority") == "P0"]
    readiness_status = "ready_for_next_mvp_live_proof" if not p0_blockers else "blocked_operator_input_required"
    next_recommended_pass = (
        "operator-provide-openai-secret-reference"
        if provider["blockers"]
        else "ventureops-real-client-scope-approval-authoring"
        if ventureops["blockers"]
        else "provider-live-probe-after-secret-reference"
    )
    next_action_queue = _build_next_action_queue(provider, ventureops, approvals)
    next_operator_action = next_action_queue[0] if next_action_queue else None
    completion_matrix = _build_completion_matrix(
        repo_truth=repo_truth,
        scope_lock=scope_lock,
        provider=provider,
        approvals=approvals,
        ventureops=ventureops,
        agent_bus=agent_bus,
        studio=studio,
        graph=graph,
        system_control=system_control,
    )
    incomplete_requirements = [
        row
        for row in completion_matrix
        if not row.get("criterion_satisfied") or row.get("remaining_required_evidence")
    ]
    blocked_requirement_ids = [
        row["id"] for row in completion_matrix if not row.get("criterion_satisfied")
    ]
    incomplete_or_operator_blocked_requirements = [
        row["id"] for row in incomplete_requirements
    ]
    operator_input_ids = [str(item.get("id")) for item in operator_inputs_required if item.get("id")]
    p0_blocker_ids = [
        str(item.get("id"))
        for item in operator_inputs_required
        if item.get("priority") == "P0" and item.get("id")
    ]
    p1_decision_ids = [
        str(item.get("id"))
        for item in operator_inputs_required
        if item.get("priority") == "P1" and item.get("id")
    ]
    completion_decision = {
        "objective_achieved": False,
        "safe_to_call_update_goal_complete": False,
        "operator_input_ids": operator_input_ids,
        "p0_blocker_ids": p0_blocker_ids,
        "p1_decision_ids": p1_decision_ids,
        "blocked_requirement_ids": blocked_requirement_ids,
        "incomplete_or_operator_blocked_requirements": incomplete_or_operator_blocked_requirements,
    }
    mvp_usecase_snapshot = _build_mvp_usecase_snapshot(
        readiness_status=readiness_status,
        provider=provider,
        approvals=approvals,
        ventureops=ventureops,
        agent_bus=agent_bus,
        studio=studio,
        graph=graph,
        system_control=system_control,
        operator_inputs_required=operator_inputs_required,
        next_action_queue=next_action_queue,
        blocked_requirement_ids=blocked_requirement_ids,
    )
    covered_completion_row_count = sum(
        1
        for row in completion_matrix
        if row.get("criterion_satisfied") and not row.get("remaining_required_evidence")
    )
    autonomous_completion_barrier = _autonomous_completion_barrier(
        completion_decision,
        covered_count=covered_completion_row_count,
        total_count=len(completion_matrix),
        next_operator_action_id=(
            next_operator_action.get("id") if next_operator_action else None
        ),
        next_recommended_pass=next_recommended_pass,
    )
    completion_safety_contract = _completion_safety_contract(
        completion_decision,
        autonomous_completion_barrier,
        covered_count=covered_completion_row_count,
        total_count=len(completion_matrix),
    )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(root),
        "read_only": True,
        "readiness_status": readiness_status,
        "overall_goal_complete": False,
        "objective_achieved": completion_decision["objective_achieved"],
        "safe_to_call_update_goal_complete": completion_decision[
            "safe_to_call_update_goal_complete"
        ],
        "operator_input_ids": completion_decision["operator_input_ids"],
        "p0_blocker_ids": completion_decision["p0_blocker_ids"],
        "p1_decision_ids": completion_decision["p1_decision_ids"],
        "blocked_requirement_ids": completion_decision["blocked_requirement_ids"],
        "incomplete_or_operator_blocked_requirements": completion_decision[
            "incomplete_or_operator_blocked_requirements"
        ],
        "no_safe_autonomous_completion_pass_available": bool(
            autonomous_completion_barrier.get("no_safe_autonomous_completion_pass_available")
        ),
        "update_goal_allowed": bool(autonomous_completion_barrier.get("update_goal_allowed")),
        "next_operator_action_id": autonomous_completion_barrier.get("next_operator_action_id"),
        "next_recommended_pass": autonomous_completion_barrier.get("next_recommended_pass"),
        "completion_decision": completion_decision,
        "autonomous_completion_barrier": autonomous_completion_barrier,
        "completion_safety_contract": completion_safety_contract,
        "canonical_operator_handoff": canonical_handoff,
        "operator_input_template_artifact": operator_template_artifact,
        "setup_scope_boundary": setup_scope_boundary,
        "usable_now": [
            "Agent Bus task lifecycle for bounded Codex work",
            "Studio approval artifact visibility",
            "Chat-to-approval queue artifact creation",
            "Graph/source context navigation",
            "Read-only operator status consolidation",
        ],
        "not_usable_until_operator_input": [
            item["id"] for item in operator_inputs_required if item.get("priority") == "P0"
        ],
        "summary": {
            "pass_count": len(pass_rows),
            "operator_input_count": len(operator_inputs_required),
            "p0_blocker_count": len(p0_blockers),
            "next_recommended_pass": next_recommended_pass,
            "next_action_count": len(next_action_queue),
            "next_operator_action_id": next_operator_action.get("id") if next_operator_action else None,
            "completion_matrix_count": len(completion_matrix),
            "blocked_requirement_count": len(blocked_requirement_ids),
        },
        "passes": pass_rows,
        "checks": {
            "repo_truth": repo_truth,
            "scope_lock": scope_lock,
            "provider_credentials": provider,
            "studio_approvals": approvals,
            "agent_bus": agent_bus,
            "ventureops": ventureops,
            "studio_cockpit": studio,
            "graph_source_intelligence": graph,
            "full_system_control": system_control,
        },
        "operator_inputs_required": operator_inputs_required,
        "next_action_queue": next_action_queue,
        "next_operator_action": next_operator_action,
        "completion_matrix": completion_matrix,
        "mvp_usecase_snapshot": mvp_usecase_snapshot,
        "authority": {
            "read_only": True,
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_allowed": False,
            "provider_calls_performed": False,
            "approval_execution_allowed": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
            "files_modified": False,
        },
        "completion_audit": {
            "objective_achieved": completion_decision["objective_achieved"],
            "safe_to_call_update_goal_complete": completion_decision[
                "safe_to_call_update_goal_complete"
            ],
            "operator_input_ids": completion_decision["operator_input_ids"],
            "p0_blocker_ids": completion_decision["p0_blocker_ids"],
            "p1_decision_ids": completion_decision["p1_decision_ids"],
            "reason": (
                "Provider-backed usefulness remains blocked on operator-supplied provider secret reference."
                if ventureops.get("live_client_workflow_proof_artifact_valid")
                else "Provider-backed usefulness and VentureOps real-client proof remain blocked on operator-supplied inputs."
            ),
            "proxy_signals_not_accepted_as_completion": True,
            "success_criteria_count": len(completion_matrix),
            "blocked_requirement_ids": completion_decision["blocked_requirement_ids"],
            "incomplete_or_operator_blocked_requirements": completion_decision[
                "incomplete_or_operator_blocked_requirements"
            ],
            "next_action_queue_ids": [row["id"] for row in next_action_queue],
        },
    }


def build_mvp_completion_audit(vault_root: str | Path = ".") -> dict[str, Any]:
    """Build a prompt-to-artifact completion audit from the current readiness gate."""

    root = Path(vault_root).resolve()
    gate = build_mvp_readiness_gate(root)
    completion_matrix = list(gate.get("completion_matrix") or [])
    gate_completion_audit = (
        gate.get("completion_audit")
        if isinstance(gate.get("completion_audit"), dict)
        else {}
    )
    canonical_handoff = _canonical_operator_handoff(root)
    template_artifact = (
        gate.get("operator_input_template_artifact")
        if isinstance(gate.get("operator_input_template_artifact"), dict)
        else _operator_input_template_artifact(root)
    )
    setup_scope_boundary = (
        gate.get("setup_scope_boundary")
        if isinstance(gate.get("setup_scope_boundary"), dict)
        else {}
    )
    checks = gate.get("checks") if isinstance(gate.get("checks"), dict) else {}
    provider = checks.get("provider_credentials") if isinstance(checks.get("provider_credentials"), dict) else {}
    approvals = checks.get("studio_approvals") if isinstance(checks.get("studio_approvals"), dict) else {}
    ventureops = checks.get("ventureops") if isinstance(checks.get("ventureops"), dict) else {}

    command_map = {
        "repo_truth_consolidation": [
            "python -m runtime.cli.main mvp current-state --json",
            "python -m runtime.cli.main mvp readiness-gate --json",
            "python -m runtime.cli.main mvp operator-unblock-packet --json",
        ],
        "mvp_scope_lock": [
            "python -m runtime.cli.main mvp readiness-gate --json",
            "python -m runtime.cli.main mvp completion-audit --json",
        ],
        "credential_readiness": [
            "python -m runtime.cli.main mvp credential-handoff --json",
            "python -m runtime.cli.main setup validate --json",
            "python -m runtime.cli.main setup provider validate openai --json",
            "python -m runtime.cli.main runtime providers --json",
            "python -m runtime.cli.main runtime provider live-smoke-readiness --json",
            "python -m runtime.cli.main mvp readiness-gate --json",
            "python -m runtime.cli.main studio dashboard --json",
        ],
        "chat_to_approval": [
            "python -m runtime.cli.main studio approval-center-panel --json",
        ],
        "approval_to_action": [
            "python -m runtime.cli.main studio approval-center-panel --json",
            "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
        ],
        "agent_bus_lifecycle": [
            "python -m runtime.cli.main mvp readiness-gate --json",
            "python -m runtime.cli.main agent-bus task list --recipient Codex --status done --limit 20 --json",
        ],
        "ventureops_real_use": [
            "python -m runtime.cli.main ventureops evidence-discovery-preflight --json",
            "python -m runtime.cli.main mvp readiness-gate --json",
        ],
        "studio_cockpit": [
            "python -m runtime.cli.main studio dashboard --json",
            "python -m runtime.cli.main mvp current-state --json",
            "python -m runtime.cli.main studio approval-center-panel --json",
        ],
        "graph_source_intelligence": [
            "python -m runtime.cli.main mvp readiness-gate --json",
        ],
        "full_system_control_boundary": [
            "python -m runtime.cli.main mvp readiness-gate --json",
        ],
    }

    prompt_to_artifact_checklist: list[dict[str, Any]] = []
    for row in completion_matrix:
        row_id = str(row.get("id"))
        covered = bool(row.get("criterion_satisfied")) and not bool(row.get("remaining_required_evidence"))
        missing_or_unverified = list(row.get("remaining_required_evidence") or [])
        operator_followups: list[str] = []
        if row_id == "credential_readiness" and provider.get("blockers"):
            operator_followups.extend(
                [
                    "operator supplies resolvable local OpenAI or approved alternate provider reference",
                    "no-secret provider validation passes",
                    "approved live provider probe succeeds",
                ]
            )
        if row_id == "approval_to_action" and approvals.get("operator_decision_required"):
            operator_followups.append(
                f"operator decision on pending Chat approval {PENDING_CHAT_APPROVAL_ID}"
            )
        prompt_to_artifact_checklist.append(
            {
                "pass": row.get("pass"),
                "id": row_id,
                "prompt_requirement": row.get("success_criterion"),
                "required_artifacts_or_evidence": list(row.get("required_evidence") or []),
                "inspection_commands": list(command_map.get(row_id, [])),
                "evidence_refs": list(row.get("evidence_refs") or [])
                + (
                    [template_artifact["path"]]
                    if row_id == "credential_readiness" and template_artifact.get("path")
                    else []
                ),
                "status": row.get("status"),
                "covered_by_current_evidence": covered,
                "criterion_satisfied": bool(row.get("criterion_satisfied")),
                "coverage_judgment": row.get("coverage_judgment"),
                "blockers": list(row.get("blockers") or []),
                "missing_incomplete_or_unverified": sorted(set(missing_or_unverified)),
                "operator_followups": operator_followups,
            }
        )

    missing_incomplete_or_weak = [
        item
        for item in prompt_to_artifact_checklist
        if not item.get("covered_by_current_evidence")
    ]
    operator_input_ids = [item.get("id") for item in gate.get("operator_inputs_required") or []]
    objective_achieved = not missing_incomplete_or_weak and not operator_input_ids
    completion_decision = {
        "objective_achieved": objective_achieved,
        "safe_to_call_update_goal_complete": objective_achieved,
        "reason": (
            "All prompt requirements are covered and no operator inputs remain."
            if objective_achieved
            else "The objective remains incomplete or operator-blocked; do not mark the active goal complete."
        ),
        "operator_input_ids": operator_input_ids,
        "p0_blocker_ids": [
            item.get("id")
            for item in gate.get("operator_inputs_required") or []
            if item.get("priority") == "P0"
        ],
        "p1_decision_ids": [
            item.get("id")
            for item in gate.get("operator_inputs_required") or []
            if item.get("priority") == "P1"
        ],
        "blocked_requirement_ids": list(
            gate_completion_audit.get("blocked_requirement_ids") or []
        ),
        "incomplete_or_operator_blocked_requirements": [
            item.get("id") for item in missing_incomplete_or_weak
        ],
        "proxy_signals_not_accepted_as_completion": True,
    }
    covered_prompt_row_count = sum(
        1
        for row in prompt_to_artifact_checklist
        if row.get("criterion_satisfied") and not row.get("missing_incomplete_or_unverified")
    )
    gate_summary = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}
    autonomous_completion_barrier = _autonomous_completion_barrier(
        completion_decision,
        covered_count=covered_prompt_row_count,
        total_count=len(prompt_to_artifact_checklist),
        next_operator_action_id=gate_summary.get("next_operator_action_id"),
        next_recommended_pass=gate_summary.get("next_recommended_pass"),
    )
    completion_safety_contract = _completion_safety_contract(
        completion_decision,
        autonomous_completion_barrier,
        covered_count=covered_prompt_row_count,
        total_count=len(prompt_to_artifact_checklist),
    )

    return {
        "ok": True,
        "surface": "chaseos_mvp_completion_audit",
        "model_version": "chaseos.mvp_completion_audit.v1",
        "generated_at_utc": gate.get("generated_at_utc"),
        "vault_root": gate.get("vault_root"),
        "read_only": True,
        "source_gate_command": "python -m runtime.cli.main mvp readiness-gate --json",
        "source_usecase_snapshot": dict(gate.get("mvp_usecase_snapshot") or {}),
        "canonical_operator_handoff": canonical_handoff,
        "operator_input_template_artifact": dict(template_artifact),
        "setup_scope_boundary": dict(setup_scope_boundary),
        "objective_achieved": bool(completion_decision["objective_achieved"]),
        "safe_to_call_update_goal_complete": bool(
            completion_decision["safe_to_call_update_goal_complete"]
        ),
        "operator_input_ids": list(completion_decision["operator_input_ids"]),
        "p0_blocker_ids": list(completion_decision["p0_blocker_ids"]),
        "p1_decision_ids": list(completion_decision["p1_decision_ids"]),
        "blocked_requirement_ids": list(completion_decision["blocked_requirement_ids"]),
        "incomplete_or_operator_blocked_requirements": list(
            completion_decision["incomplete_or_operator_blocked_requirements"]
        ),
        "objective_restatement": (
            "Consolidate ChaseOS into a real MVP workflow: repo truth and scope locked, provider references "
            "identified safely, Chat creates approvals, one approval-to-action path and one Agent Bus lifecycle "
            "are proven, VentureOps has one real-use proof, Studio is the cockpit, graph/source context is "
            "read-only, and broad system control stays gated."
        ),
        "deliverable_count": len(prompt_to_artifact_checklist),
        "checklist_count": len(prompt_to_artifact_checklist),
        "covered_checklist_count": covered_prompt_row_count,
        "next_operator_action_id": autonomous_completion_barrier.get("next_operator_action_id"),
        "next_recommended_pass": autonomous_completion_barrier.get("next_recommended_pass"),
        "no_safe_autonomous_completion_pass_available": bool(
            autonomous_completion_barrier.get("no_safe_autonomous_completion_pass_available")
        ),
        "update_goal_allowed": bool(autonomous_completion_barrier.get("update_goal_allowed")),
        "prompt_to_artifact_checklist": prompt_to_artifact_checklist,
        "current_gate_summary": dict(gate_summary),
        "completion_decision": completion_decision,
        "autonomous_completion_barrier": autonomous_completion_barrier,
        "completion_safety_contract": completion_safety_contract,
        "provider_secret_reference_state": {
            "configured_provider": provider.get("configured_provider"),
            "secret_reference_target": provider.get("secret_reference_target"),
            "secret_reference_resolvable": bool(provider.get("secret_reference_resolvable")),
            "secret_reference_probe_error": provider.get("secret_reference_probe_error"),
            "secret_value_read": False,
            "secret_value_visible": False,
        },
        "latest_pending_approval_state": {
            "approval_id": PENDING_CHAT_APPROVAL_ID,
            "operator_decision_required": bool(approvals.get("operator_decision_required")),
            "approval_consumption_performed": bool(approvals.get("approval_consumption_performed")),
            "target_write_performed": bool(approvals.get("target_write_performed")),
            "exact_once_marker_path": approvals.get("tracked_chat_exact_once_marker_path")
            or approvals.get("approval_to_action_exact_once_marker_path"),
        },
        "ventureops_state": {
            "status": ventureops.get("status"),
            "live_client_workflow_proof_artifact_valid": bool(
                ventureops.get("live_client_workflow_proof_artifact_valid")
            ),
            "selected_live_client_workflow_proof_path": ventureops.get(
                "selected_live_client_workflow_proof_path"
            ),
        },
        "authority": {
            "read_only": True,
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_performed": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
            "files_modified": False,
        },
    }


def _current_state_pass_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "pass": row.get("pass"),
        "id": row.get("id"),
        "status": row.get("status"),
        "criterion_satisfied": bool(row.get("criterion_satisfied")),
        "coverage_judgment": row.get("coverage_judgment"),
        "blockers": list(row.get("blockers") or []),
        "remaining_required_evidence": list(row.get("remaining_required_evidence") or []),
        "evidence_refs": list(row.get("evidence_refs") or []),
    }


def _autonomous_completion_barrier(
    completion_decision: dict[str, Any],
    *,
    covered_count: int,
    total_count: int,
    next_operator_action_id: str | None,
    next_recommended_pass: str | None,
) -> dict[str, Any]:
    operator_input_ids = [str(item) for item in completion_decision.get("operator_input_ids") or []]
    p0_blocker_ids = [str(item) for item in completion_decision.get("p0_blocker_ids") or []]
    p1_decision_ids = [str(item) for item in completion_decision.get("p1_decision_ids") or []]
    safe_to_complete = bool(completion_decision.get("safe_to_call_update_goal_complete"))
    all_numbered_rows_covered = total_count > 0 and covered_count == total_count
    barrier_active = not safe_to_complete

    return {
        "active": barrier_active,
        "all_numbered_mvp_rows_covered": all_numbered_rows_covered,
        "covered_numbered_mvp_row_count": covered_count,
        "numbered_mvp_row_count": total_count,
        "no_safe_autonomous_completion_pass_available": barrier_active and bool(operator_input_ids),
        "blocked_by_operator_input": barrier_active and bool(operator_input_ids),
        "update_goal_allowed": safe_to_complete and not operator_input_ids,
        "operator_input_ids": operator_input_ids,
        "p0_blocker_ids": p0_blocker_ids,
        "p1_decision_ids": p1_decision_ids,
        "next_operator_action_id": next_operator_action_id,
        "next_recommended_pass": next_recommended_pass,
        "reason": (
            "All numbered MVP rows are covered, but operator-owned input still blocks safe goal completion."
            if all_numbered_rows_covered and operator_input_ids
            else "The active MVP objective is not safe to mark complete."
        ),
    }


def _completion_safety_contract(
    completion_decision: dict[str, Any],
    autonomous_completion_barrier: dict[str, Any],
    *,
    covered_count: int,
    total_count: int,
) -> dict[str, Any]:
    update_goal_allowed = bool(autonomous_completion_barrier.get("update_goal_allowed"))
    safe_to_complete = bool(completion_decision.get("safe_to_call_update_goal_complete"))
    return {
        "status": (
            "ready_for_update_goal_complete"
            if update_goal_allowed
            else "blocked_do_not_call_update_goal_complete"
        ),
        "update_goal_allowed": update_goal_allowed,
        "safe_to_call_update_goal_complete": safe_to_complete,
        "checklist_coverage_is_not_completion": (
            covered_count == total_count and not safe_to_complete
        ),
        "covered_checklist_count": covered_count,
        "checklist_count": total_count,
        "operator_input_ids": list(completion_decision.get("operator_input_ids") or []),
        "p0_blocker_ids": list(completion_decision.get("p0_blocker_ids") or []),
        "p1_decision_ids": list(completion_decision.get("p1_decision_ids") or []),
        "next_operator_action_id": autonomous_completion_barrier.get(
            "next_operator_action_id"
        ),
        "next_recommended_pass": autonomous_completion_barrier.get("next_recommended_pass"),
        "required_before_update_goal_complete": (
            [
                "resolve_operator_inputs",
                "rerun_completion_audit",
                "require_safe_to_call_update_goal_complete_true",
            ]
            if not update_goal_allowed
            else []
        ),
        "reason": completion_decision.get("reason")
        or autonomous_completion_barrier.get("reason"),
    }


def build_mvp_current_state(vault_root: str | Path = ".") -> dict[str, Any]:
    """Build one clean current-state map from the read-only MVP gate and audit."""

    root = Path(vault_root).resolve()
    gate = build_mvp_readiness_gate(root)
    audit = build_mvp_completion_audit(root)
    snapshot = (
        gate.get("mvp_usecase_snapshot")
        if isinstance(gate.get("mvp_usecase_snapshot"), dict)
        else {}
    )
    summary = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}
    completion_decision = (
        audit.get("completion_decision")
        if isinstance(audit.get("completion_decision"), dict)
        else {}
    )
    pass_statuses = [_current_state_pass_row(row) for row in gate.get("completion_matrix") or []]
    pass_by_id = {str(row.get("id")): row for row in pass_statuses}
    covered_pass_count = sum(1 for row in pass_statuses if row.get("criterion_satisfied"))
    canonical_handoff = _canonical_operator_handoff(root)
    template_artifact = _operator_input_template_artifact(root)
    latest_writeback_records = _latest_mvp_writeback_record_paths(root)
    checks = gate.get("checks") if isinstance(gate.get("checks"), dict) else {}
    approvals = (
        checks.get("studio_approvals")
        if isinstance(checks.get("studio_approvals"), dict)
        else {}
    )
    provider = (
        checks.get("provider_credentials")
        if isinstance(checks.get("provider_credentials"), dict)
        else _provider_credential_check(root)
    )
    setup_scope_boundary = _setup_scope_boundary(root, provider)
    autonomous_completion_barrier = _autonomous_completion_barrier(
        completion_decision,
        covered_count=covered_pass_count,
        total_count=len(pass_statuses),
        next_operator_action_id=summary.get("next_operator_action_id"),
        next_recommended_pass=summary.get("next_recommended_pass"),
    )
    completion_safety_contract = _completion_safety_contract(
        completion_decision,
        autonomous_completion_barrier,
        covered_count=covered_pass_count,
        total_count=len(pass_statuses),
    )
    p0_pass_ids = [
        "repo_truth_consolidation",
        "mvp_scope_lock",
        "credential_readiness",
        "chat_to_approval",
        "approval_to_action",
        "agent_bus_lifecycle",
        "ventureops_real_use",
        "studio_cockpit",
        "graph_source_intelligence",
        "full_system_control_boundary",
    ]

    return {
        "ok": True,
        "surface": "chaseos_mvp_current_state_map",
        "model_version": "chaseos.mvp_current_state_map.v1",
        "generated_at_utc": gate.get("generated_at_utc"),
        "vault_root": gate.get("vault_root"),
        "read_only": True,
        "current_sector": snapshot.get("current_sector") or "MVP Integration / Operator Workflow Activation",
        "current_goal": (
            "Consolidate ChaseOS into one governed local MVP loop instead of expanding more feature families."
        ),
        "current_mvp_usecase": snapshot.get("current_mvp_usecase"),
        "workflow_shape": list(snapshot.get("workflow_shape") or []),
        "current_outcome": snapshot.get("current_outcome"),
        "canonical_operator_handoff": dict(canonical_handoff),
        "operator_input_template_artifact": dict(template_artifact),
        "readiness_status": gate.get("readiness_status"),
        "overall_goal_complete": bool(gate.get("overall_goal_complete")),
        "objective_achieved": bool(completion_decision.get("objective_achieved")),
        "safe_to_call_update_goal_complete": bool(
            completion_decision.get("safe_to_call_update_goal_complete")
        ),
        "operator_input_ids": list(completion_decision.get("operator_input_ids") or []),
        "p0_blocker_ids": list(completion_decision.get("p0_blocker_ids") or []),
        "p1_decision_ids": list(completion_decision.get("p1_decision_ids") or []),
        "blocked_requirement_ids": list(
            completion_decision.get("blocked_requirement_ids") or []
        ),
        "incomplete_or_operator_blocked_requirements": list(
            completion_decision.get("incomplete_or_operator_blocked_requirements") or []
        ),
        "next_operator_action_id": autonomous_completion_barrier.get("next_operator_action_id"),
        "next_recommended_pass": autonomous_completion_barrier.get("next_recommended_pass"),
        "no_safe_autonomous_completion_pass_available": bool(
            autonomous_completion_barrier.get("no_safe_autonomous_completion_pass_available")
        ),
        "update_goal_allowed": bool(autonomous_completion_barrier.get("update_goal_allowed")),
        "completion_decision": dict(completion_decision),
        "autonomous_completion_barrier": autonomous_completion_barrier,
        "completion_safety_contract": completion_safety_contract,
        "pass_status_count": len(pass_statuses),
        "pass_statuses": pass_statuses,
        "pass_status_by_id": pass_by_id,
        "scope_lock": {
            "p0_first_usable_mvp": [
                pass_by_id[pass_id] for pass_id in p0_pass_ids if pass_id in pass_by_id
            ],
            "p0_current_blocker_ids": list(completion_decision.get("p0_blocker_ids") or []),
            "p1_pending_decision_ids": list(completion_decision.get("p1_decision_ids") or []),
            "p1_next_after_mvp_loop": [
                {
                    "id": "chat_live_provider_response",
                    "status": "next_after_p0_secret_reference_and_live_probe_approval",
                },
                {
                    "id": "conversation_persistence_redaction_retention",
                    "status": "planned_after_provider_backed_loop",
                },
                {
                    "id": "studio_release_grade_packaging",
                    "status": "deferred_beyond_internal_cockpit_mvp",
                },
                {
                    "id": "graph_hygiene_review_cleanup",
                    "status": "review_later_no_autonomous_mutation",
                },
                {
                    "id": "selected_live_connector",
                    "status": "later_after_provider_and_scope_inputs",
                },
                {
                    "id": "ventureops_revenue_external_delivery",
                    "status": "separate_approval_required",
                },
            ],
            "p2_parked_or_gated": list(snapshot.get("parked_or_later") or []),
        },
        "usable_now": list(snapshot.get("usable_now") or []),
        "blocked_now": list(snapshot.get("blocked_now") or []),
        "parked_or_later": list(snapshot.get("parked_or_later") or []),
        "approval_queue_boundary": {
            "status": approvals.get("status"),
            "approval_artifact_count": int(approvals.get("approval_artifact_count") or 0),
            "pending_count": int(approvals.get("pending_count") or 0),
            "tracked_pending_count": int(approvals.get("tracked_pending_count") or 0),
            "untracked_pending_approval_count": int(
                approvals.get("untracked_pending_approval_count") or 0
            ),
            "tracked_chat_approval_id": PENDING_CHAT_APPROVAL_ID,
            "tracked_chat_approval_status": approvals.get("tracked_chat_approval_status"),
            "tracked_chat_approval_is_current_mvp_decision": bool(
                approvals.get("tracked_chat_approval_is_current_mvp_decision")
            ),
            "untracked_pending_approvals_are_current_mvp_blockers": bool(
                approvals.get("untracked_pending_approvals_are_current_mvp_blockers")
            ),
            "boundary": approvals.get("untracked_pending_approval_boundary"),
        },
        "setup_scope_boundary": setup_scope_boundary,
        "operator_action_required": {
            "required": bool(gate.get("operator_inputs_required")),
            "no_safe_autonomous_completion_pass_available": bool(
                gate.get("operator_inputs_required")
            )
            and not bool(completion_decision.get("safe_to_call_update_goal_complete")),
            "next_operator_action_id": summary.get("next_operator_action_id"),
            "next_recommended_pass": summary.get("next_recommended_pass"),
            "operator_input_ids": [
                str(item.get("id")) for item in gate.get("operator_inputs_required") or []
            ],
            "p0_blocker_ids": list(completion_decision.get("p0_blocker_ids") or []),
            "p1_decision_ids": list(completion_decision.get("p1_decision_ids") or []),
            "completion_safety_contract": dict(completion_safety_contract),
            "next_action_queue": list(gate.get("next_action_queue") or []),
            "canonical_operator_handoff": dict(canonical_handoff),
            "operator_input_template_artifact": dict(template_artifact),
        },
        "source_commands": {
            "readiness_gate": "python -m runtime.cli.main mvp readiness-gate --json",
            "completion_audit": "python -m runtime.cli.main mvp completion-audit --json",
            "operator_action_required": "python -m runtime.cli.main mvp operator-action-required --json",
            "operator_unblock_packet": "python -m runtime.cli.main mvp operator-unblock-packet --json",
            "credential_handoff": "python -m runtime.cli.main mvp credential-handoff --json",
            "operator_input_template": "python -m runtime.cli.main mvp operator-input-template --json",
            "operator_input_validation": "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
            "studio_dashboard": "python -m runtime.cli.main studio dashboard --json",
            "setup_wide_validation": SETUP_WIDE_VALIDATION_COMMAND,
        },
        "source_docs": [
            "README.md",
            "PROJECT_FOUNDATION.md",
            "ROADMAP.md",
            "00_HOME/Now.md",
            "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
            "06_AGENTS/ChaseOS-MVP-Consolidation-Map.md",
            "06_AGENTS/ChaseOS-MVP-Completion-Audit.md",
            "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
            "06_AGENTS/ChaseOS-MVP-Credential-Readiness-Checklist.md",
            MVP_OPENAI_SECRET_REFERENCE_CURRENT_HANDOFF_GUIDE_PATH,
            *MVP_WRITEBACK_INDEX_PATHS,
            *MVP_LATEST_WRITEBACK_RECORD_PATHS,
            *latest_writeback_records,
        ],
        "authority": {
            "read_only": True,
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_performed": False,
            "setup_metadata_write_performed": False,
            "approval_decision_made": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
            "files_modified": False,
        },
    }


def format_mvp_current_state(payload: dict[str, Any]) -> str:
    decision = (
        payload.get("completion_decision")
        if isinstance(payload.get("completion_decision"), dict)
        else {}
    )
    operator = (
        payload.get("operator_action_required")
        if isinstance(payload.get("operator_action_required"), dict)
        else {}
    )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    handoff = (
        payload.get("canonical_operator_handoff")
        if isinstance(payload.get("canonical_operator_handoff"), dict)
        else {}
    )
    lines = [
        "ChaseOS MVP Current State",
        f"  current_sector: {payload.get('current_sector')}",
        f"  readiness_status: {payload.get('readiness_status')}",
        f"  overall_goal_complete: {payload.get('overall_goal_complete')}",
        f"  objective_achieved: {payload.get('objective_achieved')}",
        f"  safe_to_call_update_goal_complete: {decision.get('safe_to_call_update_goal_complete')}",
        f"  next_recommended_pass: {operator.get('next_recommended_pass')}",
        f"  next_operator_action: {operator.get('next_operator_action_id')}",
        f"  canonical_operator_handoff: {handoff.get('path')} exists={handoff.get('exists')}",
        "  passes:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(5, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            6 if barrier_line else 5,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    for row in payload.get("pass_statuses") or []:
        lines.append(
            f"    {row.get('pass')}. {row.get('id')}: "
            f"{row.get('status')} satisfied={row.get('criterion_satisfied')}"
        )
    lines.append("  usable_now:")
    for item in payload.get("usable_now") or []:
        if isinstance(item, dict):
            lines.append(f"    - {item.get('id')}: {item.get('status')}")
    lines.append("  blocked_now:")
    for item in payload.get("blocked_now") or []:
        if isinstance(item, dict):
            lines.append(f"    - {item.get('id')}: {item.get('status')}")
    lines.append("  parked_or_later:")
    for item in payload.get("parked_or_later") or []:
        if isinstance(item, dict):
            lines.append(f"    - {item.get('id')}: {item.get('status')}")
    lines.append(
        "  operator_inputs: "
        + ", ".join(str(item) for item in operator.get("operator_input_ids") or [])
    )
    if setup_scope:
        lines.append(
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"mvp_blockers={setup_scope.get('mvp_current_setup_blocker_ids')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}"
        )
    next_actions = operator.get("next_action_queue") if isinstance(operator, dict) else []
    for action in next_actions or []:
        if not isinstance(action, dict) or action.get("id") != "openai_secret_reference":
            continue
        presence_checks = action.get("reference_presence_check_commands") or []
        if presence_checks:
            lines.append(
                "  presence_check: "
                + " ; ".join(str(command) for command in presence_checks)
            )
    lines.append("  boundary: read-only current-state map; no secret read, provider call, setup write, approval decision/consumption, Agent Bus write, browser/host control, or canonical mutation")
    return "\n".join(lines)


def build_mvp_credential_handoff(vault_root: str | Path = ".") -> dict[str, Any]:
    """Build a no-secret credential handoff for the first usable MVP loop."""

    root = Path(vault_root).resolve()
    gate = build_mvp_readiness_gate(root)
    checks = gate.get("checks") if isinstance(gate.get("checks"), dict) else {}
    provider = (
        checks.get("provider_credentials")
        if isinstance(checks.get("provider_credentials"), dict)
        else _provider_credential_check(root)
    )
    snapshot = (
        gate.get("mvp_usecase_snapshot")
        if isinstance(gate.get("mvp_usecase_snapshot"), dict)
        else build_mvp_usecase_snapshot(root)
    )
    template_artifact = (
        gate.get("operator_input_template_artifact")
        if isinstance(gate.get("operator_input_template_artifact"), dict)
        else _operator_input_template_artifact(root)
    )
    decision = (
        gate.get("completion_decision")
        if isinstance(gate.get("completion_decision"), dict)
        else {}
    )
    barrier = (
        gate.get("autonomous_completion_barrier")
        if isinstance(gate.get("autonomous_completion_barrier"), dict)
        else {}
    )
    safety = (
        gate.get("completion_safety_contract")
        if isinstance(gate.get("completion_safety_contract"), dict)
        else _completion_safety_contract(
            decision,
            barrier,
            covered_count=int(barrier.get("covered_numbered_mvp_row_count") or 0),
            total_count=int(barrier.get("numbered_mvp_row_count") or 0),
        )
    )
    setup_scope_boundary = _setup_scope_boundary(root, provider)
    blocked = bool(provider.get("blockers"))

    return {
        "ok": True,
        "surface": "chaseos_mvp_credential_handoff",
        "model_version": MVP_CREDENTIAL_HANDOFF_VERSION,
        "generated_at_utc": gate.get("generated_at_utc"),
        "vault_root": str(root),
        "read_only": True,
        "current_sector": snapshot.get("current_sector")
        or "MVP Integration / Operator Workflow Activation",
        "readiness_status": (
            "blocked_operator_input_required"
            if blocked
            else "ready_for_no_secret_validation_and_guarded_live_probe_request"
        ),
        "overall_goal_complete": bool(gate.get("overall_goal_complete")),
        "objective_achieved": bool(decision.get("objective_achieved")),
        "safe_to_call_update_goal_complete": bool(
            decision.get("safe_to_call_update_goal_complete")
        ),
        "operator_input_ids": list(decision.get("operator_input_ids") or []),
        "p0_blocker_ids": list(decision.get("p0_blocker_ids") or []),
        "p1_decision_ids": list(decision.get("p1_decision_ids") or []),
        "current_secret_reference_kind": provider.get("secret_reference_kind"),
        "current_secret_reference_target": provider.get("secret_reference_target"),
        "current_secret_reference_target_is_placeholder": bool(
            provider.get("secret_reference_target_is_placeholder")
        ),
        "current_secret_reference_resolvable": bool(
            provider.get("secret_reference_resolvable")
        ),
        "secret_reference_probe_source": provider.get("secret_reference_probe_source"),
        "secret_reference_probe_error": provider.get("secret_reference_probe_error"),
        "recommended_reference_name": "OPENAI_API_KEY",
        "blocked_requirement_ids": list(decision.get("blocked_requirement_ids") or []),
        "incomplete_or_operator_blocked_requirements": list(
            decision.get("incomplete_or_operator_blocked_requirements") or []
        ),
        "no_safe_autonomous_completion_pass_available": bool(
            barrier.get("no_safe_autonomous_completion_pass_available")
        ),
        "update_goal_allowed": bool(barrier.get("update_goal_allowed")),
        "next_operator_action_id": barrier.get("next_operator_action_id"),
        "next_recommended_pass": barrier.get("next_recommended_pass"),
        "completion_decision": dict(decision),
        "autonomous_completion_barrier": dict(barrier),
        "completion_safety_contract": dict(safety),
        "setup_scope_boundary": setup_scope_boundary,
        "required_operator_inputs": list(gate.get("operator_inputs_required") or []),
        "p0_required_now": [
            {
                "id": "openai_secret_reference",
                "priority": "P0",
                "provider": "openai",
                "required_for": [
                    "provider_backed_chat_studio_response",
                    "guarded_live_provider_probe_after_validation",
                ],
                "status": provider.get("status"),
                "current_secret_reference_kind": provider.get("secret_reference_kind"),
                "current_secret_reference_target": provider.get("secret_reference_target"),
                "current_secret_reference_target_is_placeholder": bool(
                    provider.get("secret_reference_target_is_placeholder")
                ),
                "current_secret_reference_resolvable": bool(
                    provider.get("secret_reference_resolvable")
                ),
                "secret_reference_probe_source": provider.get("secret_reference_probe_source"),
                "secret_reference_probe_error": provider.get("secret_reference_probe_error"),
                "operator_action": (
                    "Create or confirm the OpenAI secret in the gitignored ChaseOS .env file or another approved local secret source, then point setup metadata at the reference name only."
                ),
                "recommended_reference_name": "OPENAI_API_KEY",
                "reference_presence_check_commands": list(
                    provider.get("reference_presence_check_commands") or []
                ),
                "reference_presence_check_outputs_secret_value": bool(
                    provider.get("reference_presence_check_outputs_secret_value")
                ),
                "secret_value_allowed_in_repo_or_chat": False,
                "codex_can_perform_now": False,
                "codex_can_preview_after_reference_exists": True,
                "blocks_goal_completion": blocked,
            }
        ],
        "p1_optional_or_later": [
            {
                "id": "anthropic_or_claude_reference",
                "priority": "P1",
                "status": "only_if_claude_or_hermes_provider_path_is_selected",
                "reason": "Not required for the first OpenAI-backed MVP loop.",
            },
            {
                "id": "discord_output_routing",
                "priority": "P1",
                "status": "useful_but_not_required_for_first_mvp_loop",
                "reason": "Can receive or mirror operator output later; not needed for the local proof loop.",
            },
        ],
        "p2_parked_or_out_of_scope": [
            {
                "id": "n8n_connector_credentials",
                "priority": "P2",
                "status": "later_after_mvp_loop",
            },
            {
                "id": "crm_payment_revenue_credentials",
                "priority": "P2",
                "status": "separate_approval_required",
            },
            {
                "id": "wallet_exchange_or_seed_credentials",
                "priority": "out_of_scope",
                "status": "do_not_add_for_mvp",
            },
            {
                "id": "host_admin_or_full_system_control_credentials",
                "priority": "out_of_scope",
                "status": "parked_until_separate_full_system_control_scope",
            },
        ],
        "safe_operator_sequence": list(provider.get("operator_handoff_steps") or []),
        "operator_input_template_artifact": dict(template_artifact),
        "safe_commands": {
            "check_reference_presence_user": OPENAI_REFERENCE_PRESENCE_CHECK_USER_COMMAND,
            "check_reference_presence_process": OPENAI_REFERENCE_PRESENCE_CHECK_PROCESS_COMMAND,
            "write_template": MVP_OPERATOR_INPUT_TEMPLATE_WRITE_COMMAND,
            "validate_operator_input": MVP_OPERATOR_INPUT_TEMPLATE_VALIDATION_COMMAND,
            "preview_setup_metadata": OPENAI_SETUP_METADATA_DRY_RUN_COMMAND,
            "confirmed_setup_metadata_write": OPENAI_SETUP_METADATA_WRITE_COMMAND,
            "validate_provider_reference": "python -m runtime.cli.main setup provider validate openai --json",
            "provider_live_smoke_readiness": "python -m runtime.cli.main runtime provider live-smoke-readiness --json",
            "guarded_live_probe_approval_plan": "python -m runtime.cli.main runtime provider live-probe-target-approval-plan primary --json",
        },
        "completion_criteria_after_operator_input": [
            "`setup set --dry-run` reports `writes_setup_state=false`.",
            "Operator explicitly confirms the metadata-only setup write.",
            "`setup provider validate openai --json` reports `secret_reference_resolvable=true` without showing a secret value.",
            "A separate live-probe approval plan is reviewed before any provider call.",
        ],
        "source_commands": {
            "credential_handoff": "python -m runtime.cli.main mvp credential-handoff --json",
            "readiness_gate": "python -m runtime.cli.main mvp readiness-gate --json",
            "operator_action_required": "python -m runtime.cli.main mvp operator-action-required --json",
            "completion_audit": "python -m runtime.cli.main mvp completion-audit --json",
            "setup_wide_validation": SETUP_WIDE_VALIDATION_COMMAND,
        },
        "source_docs": [
            "06_AGENTS/ChaseOS-MVP-Credential-Readiness-Checklist.md",
            "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md",
            MVP_OPENAI_SECRET_REFERENCE_CURRENT_HANDOFF_GUIDE_PATH,
        ],
        "boundary": {
            "read_only": True,
            "secret_values_allowed": False,
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_performed": False,
            "setup_metadata_write_performed": False,
            "approval_decision_made": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def format_mvp_credential_handoff(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS MVP Credential Handoff",
        f"  readiness_status: {payload.get('readiness_status')}",
        f"  safe_to_call_update_goal_complete: {payload.get('safe_to_call_update_goal_complete')}",
        "  p0_required_now:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(3, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            4 if barrier_line else 3,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    if setup_scope:
        lines.insert(
            (5 if barrier_line else 4) if safety else (4 if barrier_line else 3),
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}",
        )
    for item in payload.get("p0_required_now") or []:
        lines.append(
            f"    - {item.get('id')}: target={item.get('current_secret_reference_target')} "
            f"placeholder={item.get('current_secret_reference_target_is_placeholder')} "
            f"resolvable={item.get('current_secret_reference_resolvable')} "
            f"error={item.get('secret_reference_probe_error')}"
        )
        live_smoke_command = (
            payload.get("safe_commands", {}).get("provider_live_smoke_readiness")
            if isinstance(payload.get("safe_commands"), dict)
            else None
        )
        if live_smoke_command:
            lines.append(f"      provider_live_smoke_readiness: {live_smoke_command}")
        presence_checks = item.get("reference_presence_check_commands")
        if presence_checks:
            lines.append("      presence_check: " + " ; ".join(str(cmd) for cmd in presence_checks))
    lines.append("  safe_operator_sequence:")
    for step in payload.get("safe_operator_sequence") or []:
        lines.append(f"    {step.get('order')}. {step.get('id')}: {step.get('status')}")
    commands = payload.get("safe_commands") if isinstance(payload.get("safe_commands"), dict) else {}
    lines.append(f"  preview: {commands.get('preview_setup_metadata')}")
    lines.append(f"  validate: {commands.get('validate_provider_reference')}")
    lines.append("  boundary: read-only; no secret values, provider calls, setup writes, approvals, Agent Bus writes, browser/host control, or canonical mutation")
    return "\n".join(lines)


def format_mvp_completion_audit(payload: dict[str, Any]) -> str:
    decision = payload.get("completion_decision") if isinstance(payload.get("completion_decision"), dict) else {}
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    snapshot = (
        payload.get("source_usecase_snapshot")
        if isinstance(payload.get("source_usecase_snapshot"), dict)
        else {}
    )
    lines = [
        "ChaseOS MVP Completion Audit",
        f"  objective_achieved: {decision.get('objective_achieved')}",
        f"  safe_to_call_update_goal_complete: {decision.get('safe_to_call_update_goal_complete')}",
        f"  current_sector: {snapshot.get('current_sector')}",
        f"  readiness_status: {snapshot.get('readiness_status')}",
        "  canonical_operator_handoff: "
        + str(
            (
                payload.get("canonical_operator_handoff")
                if isinstance(payload.get("canonical_operator_handoff"), dict)
                else {}
            ).get("path")
        ),
        "  prompt_to_artifact_checklist:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(5, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            6 if barrier_line else 5,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    if setup_scope:
        lines.insert(
            7 if safety and barrier_line else 6 if (safety or barrier_line) else 5,
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}",
        )
    if safety:
        lines.insert(
            7 if setup_scope and barrier_line else 6 if setup_scope or barrier_line else 5,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    for item in payload.get("prompt_to_artifact_checklist") or []:
        lines.append(
            f"    {item.get('pass')}. {item.get('id')}: "
            f"{item.get('status')} covered={item.get('covered_by_current_evidence')}"
        )
        missing = item.get("missing_incomplete_or_unverified") or []
        if missing:
            lines.append("      missing_or_unverified: " + "; ".join(str(value) for value in missing))
    lines.append(
        "  operator_inputs: "
        + ", ".join(str(item) for item in decision.get("operator_input_ids") or [])
    )
    if "openai_secret_reference" in (decision.get("operator_input_ids") or []):
        lines.append(
            "  presence_check: "
            + " ; ".join(
                [
                    OPENAI_REFERENCE_PRESENCE_CHECK_USER_COMMAND,
                    OPENAI_REFERENCE_PRESENCE_CHECK_PROCESS_COMMAND,
                ]
            )
        )
    lines.append("  reason: " + str(decision.get("reason")))
    lines.append("  boundary: read-only audit; no secret read, provider call, approval consumption, Agent Bus write, browser/host control, or canonical mutation")
    return "\n".join(lines)


def build_mvp_operator_action_required(vault_root: str | Path = ".") -> dict[str, Any]:
    """Build the current operator-action-required gate for the MVP goal."""

    root = Path(vault_root).resolve()
    audit = build_mvp_completion_audit(root)
    decision = (
        audit.get("completion_decision")
        if isinstance(audit.get("completion_decision"), dict)
        else {}
    )
    barrier = (
        audit.get("autonomous_completion_barrier")
        if isinstance(audit.get("autonomous_completion_barrier"), dict)
        else {}
    )
    safety = (
        audit.get("completion_safety_contract")
        if isinstance(audit.get("completion_safety_contract"), dict)
        else {}
    )
    template_artifact = _operator_input_template_artifact(root)
    readiness_gate = build_mvp_readiness_gate(root)
    readiness_checks = (
        readiness_gate.get("checks")
        if isinstance(readiness_gate.get("checks"), dict)
        else {}
    )
    provider = (
        readiness_checks.get("provider_credentials")
        if isinstance(readiness_checks.get("provider_credentials"), dict)
        else {}
    )
    setup_scope_boundary = _setup_scope_boundary(root, provider)

    required_actions: list[dict[str, Any]] = []
    p0_ids = set(decision.get("p0_blocker_ids") or [])
    p1_ids = set(decision.get("p1_decision_ids") or [])
    if "openai_secret_reference" in p0_ids:
        required_actions.append(
            {
                "id": "openai_secret_reference",
                "priority": "P0",
                "owner": "operator",
                "status": "blocked_operator_input_required",
                "action": "Create or confirm an OpenAI secret in the gitignored ChaseOS .env file or another approved local secret source, then provide only the reference name.",
                "handoff_guide_path": MVP_OPENAI_SECRET_REFERENCE_CURRENT_HANDOFF_GUIDE_PATH,
                "template_artifact_path": template_artifact["path"] if template_artifact["exists"] else None,
                "validation_command": MVP_OPERATOR_INPUT_TEMPLATE_VALIDATION_COMMAND,
                "followup_after_valid_template": OPENAI_SETUP_METADATA_DRY_RUN_COMMAND,
                "followup_after_preview_confirmation": OPENAI_SETUP_METADATA_WRITE_COMMAND,
                **_provider_secret_reference_action_fields(provider),
                "codex_can_perform_now": False,
                "blocks_goal_completion": True,
            }
        )
    if "pending_chat_approval_decision" in p1_ids:
        required_actions.append(
            {
                "id": "pending_chat_approval_decision",
                "priority": "P1",
                "owner": "operator",
                "status": "pending_operator_review",
                "action": f"Choose approve, reject, or leave pending for Studio approval {PENDING_CHAT_APPROVAL_ID}.",
                "template_artifact_path": template_artifact["path"] if template_artifact["exists"] else None,
                "validation_command": MVP_OPERATOR_INPUT_TEMPLATE_VALIDATION_COMMAND,
                "approval_id": PENDING_CHAT_APPROVAL_ID,
                "approval_consumption_readiness_command": PENDING_CHAT_APPROVAL_READINESS_COMMAND,
                "approval_consumption_executor_command_template": PENDING_CHAT_APPROVAL_EXECUTOR_COMMAND_TEMPLATE,
                "followup_after_approved_decision": "run a separate source-specific exact-once approval consumption pass",
                "codex_can_decide_now": False,
                "approval_consumption_allowed_now": False,
                "blocks_goal_completion": True,
            }
        )

    no_safe_autonomous_completion_pass_available = bool(required_actions) and not bool(
        decision.get("safe_to_call_update_goal_complete")
    )
    return {
        "ok": True,
        "surface": "chaseos_mvp_operator_action_required",
        "model_version": "chaseos.mvp_operator_action_required.v1",
        "generated_at_utc": audit.get("generated_at_utc"),
        "vault_root": str(root),
        "read_only": True,
        "source_completion_audit_command": "python -m runtime.cli.main mvp completion-audit --json",
        "objective_achieved": bool(decision.get("objective_achieved")),
        "safe_to_call_update_goal_complete": bool(
            decision.get("safe_to_call_update_goal_complete")
        ),
        "operator_input_ids": list(decision.get("operator_input_ids") or []),
        "p0_blocker_ids": list(decision.get("p0_blocker_ids") or []),
        "p1_decision_ids": list(decision.get("p1_decision_ids") or []),
        "blocked_requirement_ids": list(decision.get("blocked_requirement_ids") or []),
        "incomplete_or_operator_blocked_requirements": list(
            decision.get("incomplete_or_operator_blocked_requirements") or []
        ),
        "required": bool(required_actions),
        "operator_action_required": bool(required_actions),
        "no_safe_autonomous_completion_pass_available": no_safe_autonomous_completion_pass_available,
        "next_operator_action_id": barrier.get("next_operator_action_id"),
        "next_recommended_pass": barrier.get("next_recommended_pass"),
        "update_goal_allowed": bool(barrier.get("update_goal_allowed")),
        "reason": (
            "Operator-owned input is required before Codex can truthfully complete the active MVP objective."
            if required_actions
            else "No operator-owned blockers are currently reported by the completion audit."
        ),
        "required_actions": required_actions,
        "required_operator_actions": required_actions,
        "setup_scope_boundary": setup_scope_boundary,
        "canonical_operator_handoff": _canonical_operator_handoff(root),
        "operator_input_template_artifact": dict(template_artifact),
        "completion_decision": dict(decision),
        "autonomous_completion_barrier": dict(barrier),
        "completion_safety_contract": dict(safety),
        "authority": {
            "read_only": True,
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_performed": False,
            "setup_metadata_write_performed": False,
            "approval_decision_made": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def format_mvp_operator_action_required(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS MVP Operator Action Required",
        f"  objective_achieved: {payload.get('objective_achieved')}",
        f"  safe_to_call_update_goal_complete: {payload.get('safe_to_call_update_goal_complete')}",
        f"  operator_action_required: {payload.get('operator_action_required')}",
        "  no_safe_autonomous_completion_pass_available: "
        + str(payload.get("no_safe_autonomous_completion_pass_available")),
        f"  next_recommended_pass: {payload.get('next_recommended_pass')}",
        f"  next_operator_action: {payload.get('next_operator_action_id')}",
        f"  reason: {payload.get('reason')}",
        "  required_operator_actions:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(5, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            6 if barrier_line else 5,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    if setup_scope:
        lines.append(
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}"
        )
    for action in payload.get("required_operator_actions") or []:
        lines.append(f"    - {action.get('priority')} {action.get('id')}: {action.get('action')}")
        if action.get("id") == "openai_secret_reference":
            lines.append(
                "      current_secret_reference: "
                f"target={action.get('current_secret_reference_target')} "
                f"placeholder={action.get('current_secret_reference_target_is_placeholder')} "
                f"resolvable={action.get('current_secret_reference_resolvable')} "
                f"error={action.get('secret_reference_probe_error')}"
            )
            if action.get("provider_live_smoke_readiness_command"):
                lines.append(
                    "      provider_live_smoke_readiness: "
                    + str(action.get("provider_live_smoke_readiness_command"))
                )
            presence_checks = action.get("reference_presence_check_commands")
            if presence_checks:
                lines.append(
                    "      presence_check: "
                    + " ; ".join(str(command) for command in presence_checks)
                )
        if action.get("template_artifact_path"):
            lines.append(f"      template: {action.get('template_artifact_path')}")
        if action.get("validation_command"):
            lines.append(f"      validate: {action.get('validation_command')}")
    handoff = (
        payload.get("canonical_operator_handoff")
        if isinstance(payload.get("canonical_operator_handoff"), dict)
        else {}
    )
    if handoff.get("path"):
        lines.append(
            "  canonical_operator_handoff: "
            + str(handoff.get("path"))
            + f" (exists={handoff.get('exists')})"
        )
    template = (
        payload.get("operator_input_template_artifact")
        if isinstance(payload.get("operator_input_template_artifact"), dict)
        else {}
    )
    lines.append(
        f"  template_artifact: {template.get('path')} exists={template.get('exists')}"
    )
    lines.append("  boundary: read-only; no secret read, provider call, setup write, approval decision/consumption, Agent Bus write, browser/host control, or canonical mutation")
    return "\n".join(lines)


def build_mvp_operator_unblock_packet(vault_root: str | Path = ".") -> dict[str, Any]:
    """Build a compact no-secret operator packet from the readiness gate."""

    root = Path(vault_root).resolve()
    gate = build_mvp_readiness_gate(root)
    summary = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}
    checks = gate.get("checks") if isinstance(gate.get("checks"), dict) else {}
    provider = (
        checks.get("provider_credentials")
        if isinstance(checks.get("provider_credentials"), dict)
        else _provider_credential_check(root)
    )
    setup_scope_boundary = _setup_scope_boundary(root, provider)
    operator_template_artifact = (
        gate.get("operator_input_template_artifact")
        if isinstance(gate.get("operator_input_template_artifact"), dict)
        else {}
    )
    completion_audit = (
        gate.get("completion_audit") if isinstance(gate.get("completion_audit"), dict) else {}
    )
    completion_decision = (
        gate.get("completion_decision")
        if isinstance(gate.get("completion_decision"), dict)
        else {
            "objective_achieved": bool(gate.get("overall_goal_complete")),
            "safe_to_call_update_goal_complete": bool(gate.get("overall_goal_complete")),
            "operator_input_ids": [
                str(item.get("id"))
                for item in gate.get("operator_inputs_required") or []
                if item.get("id")
            ],
            "p0_blocker_ids": [
                str(item.get("id"))
                for item in gate.get("operator_inputs_required") or []
                if item.get("priority") == "P0" and item.get("id")
            ],
            "p1_decision_ids": [
                str(item.get("id"))
                for item in gate.get("operator_inputs_required") or []
                if item.get("priority") == "P1" and item.get("id")
            ],
            "blocked_requirement_ids": list(completion_audit.get("blocked_requirement_ids") or []),
            "incomplete_or_operator_blocked_requirements": list(
                completion_audit.get("incomplete_or_operator_blocked_requirements") or []
            ),
        }
    )
    barrier = (
        gate.get("autonomous_completion_barrier")
        if isinstance(gate.get("autonomous_completion_barrier"), dict)
        else {}
    )
    next_actions = list(gate.get("next_action_queue") or [])
    commands = [
        {
            "id": item.get("id"),
            "priority": item.get("priority"),
            "safe_next_command": item.get("safe_next_command"),
            "validation_command": item.get("validation_command"),
        }
        for item in next_actions
        if item.get("safe_next_command") or item.get("validation_command")
    ]
    operator_input_schema = _build_operator_input_schema(gate)
    operator_input_template = _build_operator_input_template(operator_input_schema)
    safety = _completion_safety_contract(
        completion_decision,
        barrier,
        covered_count=int(summary.get("completion_matrix_count") or 0),
        total_count=int(summary.get("completion_matrix_count") or 0),
    )
    return {
        "ok": True,
        "surface": "chaseos_mvp_operator_unblock_packet",
        "model_version": "chaseos.mvp_operator_unblock_packet.v1",
        "generated_at_utc": gate.get("generated_at_utc"),
        "read_only": True,
        "source_gate_command": "python -m runtime.cli.main mvp readiness-gate --json",
        "readiness_status": gate.get("readiness_status"),
        "overall_goal_complete": bool(gate.get("overall_goal_complete")),
        "objective_achieved": bool(completion_decision.get("objective_achieved")),
        "safe_to_call_update_goal_complete": bool(
            completion_decision.get("safe_to_call_update_goal_complete")
        ),
        "operator_input_ids": list(completion_decision.get("operator_input_ids") or []),
        "p0_blocker_ids": list(completion_decision.get("p0_blocker_ids") or []),
        "p1_decision_ids": list(completion_decision.get("p1_decision_ids") or []),
        "blocked_requirement_ids": list(
            completion_decision.get("blocked_requirement_ids") or []
        ),
        "incomplete_or_operator_blocked_requirements": list(
            completion_decision.get("incomplete_or_operator_blocked_requirements") or []
        ),
        "no_safe_autonomous_completion_pass_available": bool(
            barrier.get("no_safe_autonomous_completion_pass_available")
        ),
        "update_goal_allowed": bool(barrier.get("update_goal_allowed")),
        "completion_decision": dict(completion_decision),
        "autonomous_completion_barrier": dict(barrier),
        "completion_safety_contract": dict(safety),
        "setup_scope_boundary": setup_scope_boundary,
        "current_sector": "MVP Integration / Operator Workflow Activation",
        "next_recommended_pass": summary.get("next_recommended_pass"),
        "next_operator_action_id": summary.get("next_operator_action_id"),
        "next_operator_action": gate.get("next_operator_action"),
        "next_action_queue": next_actions,
        "required_operator_inputs": list(gate.get("operator_inputs_required") or []),
        "operator_inputs_required": list(gate.get("operator_inputs_required") or []),
        "operator_input_schema_version": OPERATOR_INPUT_SCHEMA_VERSION,
        "operator_input_schema": operator_input_schema,
        "operator_input_template_version": OPERATOR_INPUT_TEMPLATE_VERSION,
        "operator_input_template_artifact": dict(operator_template_artifact),
        "operator_input_template": operator_input_template,
        "safe_commands": commands,
        "completion_summary": {
            "completion_matrix_count": summary.get("completion_matrix_count"),
            "blocked_requirement_count": summary.get("blocked_requirement_count"),
            "blocked_requirement_ids": list(completion_audit.get("blocked_requirement_ids") or []),
            "incomplete_or_operator_blocked_requirements": list(
                completion_audit.get("incomplete_or_operator_blocked_requirements") or []
            ),
        },
        "not_usable_until_operator_input": list(gate.get("not_usable_until_operator_input") or []),
        "usable_now": list(gate.get("usable_now") or []),
        "mvp_usecase_snapshot": dict(gate.get("mvp_usecase_snapshot") or {}),
        "authority": dict(gate.get("authority") or {}),
        "boundary": {
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_performed": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def build_mvp_operator_input_template_packet(vault_root: str | Path = ".") -> dict[str, Any]:
    """Build a standalone fillable no-secret operator input template packet."""

    packet = build_mvp_operator_unblock_packet(vault_root)
    template_artifact = (
        packet.get("operator_input_template_artifact")
        if isinstance(packet.get("operator_input_template_artifact"), dict)
        else {}
    )
    template = (
        packet.get("operator_input_template")
        if isinstance(packet.get("operator_input_template"), dict)
        else {}
    )
    groups = template.get("groups") if isinstance(template.get("groups"), list) else []
    operator_input_values = {
        str(group.get("id")): dict(group.get("template_values") or {})
        for group in groups
        if isinstance(group, dict) and group.get("id")
    }
    groups_summary = [
        {
            "id": group.get("id"),
            "priority": group.get("priority"),
            "sector": group.get("sector"),
            "field_names": list((group.get("template_values") or {}).keys()),
            "validation_command": group.get("validation_command"),
            "safe_command_template": group.get("safe_command_template"),
        }
        for group in groups
        if isinstance(group, dict)
    ]
    return {
        "ok": True,
        "surface": "chaseos_mvp_operator_input_template_packet",
        "model_version": "chaseos.mvp_operator_input_template_packet.v1",
        "generated_at_utc": packet.get("generated_at_utc"),
        "read_only": True,
        "source_unblock_packet_command": "python -m runtime.cli.main mvp operator-unblock-packet --json",
        "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
        "readiness_status": packet.get("readiness_status"),
        "overall_goal_complete": bool(packet.get("overall_goal_complete")),
        "objective_achieved": bool(packet.get("objective_achieved")),
        "safe_to_call_update_goal_complete": bool(
            packet.get("safe_to_call_update_goal_complete")
        ),
        "operator_input_ids": list(packet.get("operator_input_ids") or []),
        "p0_blocker_ids": list(packet.get("p0_blocker_ids") or []),
        "p1_decision_ids": list(packet.get("p1_decision_ids") or []),
        "blocked_requirement_ids": list(packet.get("blocked_requirement_ids") or []),
        "incomplete_or_operator_blocked_requirements": list(
            packet.get("incomplete_or_operator_blocked_requirements") or []
        ),
        "no_safe_autonomous_completion_pass_available": bool(
            (packet.get("autonomous_completion_barrier") or {}).get(
                "no_safe_autonomous_completion_pass_available"
            )
        ),
        "update_goal_allowed": bool(
            (packet.get("autonomous_completion_barrier") or {}).get("update_goal_allowed")
        ),
        "completion_decision": dict(packet.get("completion_decision") or {}),
        "autonomous_completion_barrier": dict(
            packet.get("autonomous_completion_barrier") or {}
        ),
        "completion_safety_contract": dict(
            packet.get("completion_safety_contract") or {}
        ),
        "setup_scope_boundary": dict(packet.get("setup_scope_boundary") or {}),
        "required_operator_inputs": list(packet.get("required_operator_inputs") or []),
        "next_operator_action_id": packet.get("next_operator_action_id"),
        "next_recommended_pass": packet.get("next_recommended_pass"),
        "operator_input_template_version": packet.get("operator_input_template_version"),
        "operator_input_template_artifact": dict(template_artifact),
        "operator_input_template": template,
        "operator_input_values": operator_input_values,
        "groups_summary": groups_summary,
        "operator_notes": [
            "Fill only reference names, repo-relative paths, and approval decision metadata.",
            "Do not paste API keys, secret values, wallet keys, seed phrases, customer credentials, or private client material.",
            "Set the actual OpenAI key in the gitignored ChaseOS .env file or another approved local secret source before changing setup metadata to reference its name.",
            "Run the validation command before any separate governed follow-up pass.",
        ],
        "boundary": {
            "secret_values_allowed": False,
            "secret_values_read": False,
            "secret_values_visible": False,
            "provider_calls_allowed": False,
            "provider_calls_performed": False,
            "setup_metadata_write_performed": False,
            "approval_consumption_allowed": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def format_mvp_operator_input_template_packet(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS MVP Operator Input Template",
        f"  readiness_status: {payload.get('readiness_status')}",
        f"  overall_goal_complete: {payload.get('overall_goal_complete')}",
        f"  next_operator_action: {payload.get('next_operator_action_id')}",
        f"  validation_command: {payload.get('validation_command')}",
        "  groups:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(4, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            5 if barrier_line else 4,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    if setup_scope:
        lines.insert(
            6 if safety and barrier_line else 5 if (safety or barrier_line) else 4,
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}",
        )
    for group in payload.get("groups_summary") or []:
        lines.append(
            f"    - {group.get('id')} [{group.get('priority')}]: "
            + ", ".join(str(name) for name in group.get("field_names") or [])
        )
    for item in payload.get("required_operator_inputs") or []:
        if not isinstance(item, dict) or item.get("id") != "openai_secret_reference":
            continue
        presence_checks = item.get("reference_presence_check_commands") or []
        if presence_checks:
            lines.append(
                "  presence_check: "
                + " ; ".join(str(command) for command in presence_checks)
            )
    lines.append("  operator_input_values:")
    for group_id, values in (payload.get("operator_input_values") or {}).items():
        fields = ", ".join(f"{name}={value}" for name, value in dict(values).items())
        lines.append(f"    - {group_id}: {fields}")
    lines.append("  boundary: template only; no secret value, provider call, setup metadata write, approval consumption, Agent Bus write, browser/host control, or canonical mutation")
    return "\n".join(lines)


def format_mvp_operator_unblock_packet(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS MVP Operator Unblock Packet",
        f"  readiness_status: {payload.get('readiness_status')}",
        f"  overall_goal_complete: {payload.get('overall_goal_complete')}",
        f"  next_operator_action: {payload.get('next_operator_action_id')}",
        "  next_action_queue:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(4, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            5 if barrier_line else 4,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    if setup_scope:
        lines.insert(
            (6 if barrier_line else 5) if safety else (5 if barrier_line else 4),
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}",
        )
    for item in payload.get("next_action_queue") or []:
        lines.append(f"    - {item.get('id')} [{item.get('priority')}] {item.get('action')}")
    commands = payload.get("safe_commands") or []
    if commands:
        lines.append("  commands:")
        for item in commands:
            if item.get("safe_next_command"):
                lines.append(f"    - {item.get('id')}: {item.get('safe_next_command')}")
            if item.get("validation_command"):
                prefix = "      validate" if item.get("safe_next_command") else f"    - {item.get('id')} validate"
                lines.append(f"{prefix}: {item.get('validation_command')}")
            presence_checks = item.get("reference_presence_check_commands") or []
            if presence_checks:
                lines.append(
                    "      presence_check: "
                    + " ; ".join(str(command) for command in presence_checks)
                )
    for item in payload.get("required_operator_inputs") or []:
        if not isinstance(item, dict) or item.get("id") != "openai_secret_reference":
            continue
        presence_checks = item.get("reference_presence_check_commands") or []
        if presence_checks:
            lines.append(
                "  presence_check: "
                + " ; ".join(str(command) for command in presence_checks)
            )
            break
    action_handoffs = [
        item
        for item in payload.get("next_action_queue") or []
        if isinstance(item, dict) and item.get("operator_handoff_steps")
    ]
    if action_handoffs:
        lines.append("  action_handoff_steps:")
        for action in action_handoffs:
            lines.append(f"    - {action.get('id')}:")
            for step in action.get("operator_handoff_steps") or []:
                command = step.get("command_template") or "manual/separate governed pass"
                lines.append(f"      {step.get('order')}. {step.get('id')}: {command}")
    snapshot = payload.get("mvp_usecase_snapshot") if isinstance(payload.get("mvp_usecase_snapshot"), dict) else {}
    if snapshot:
        lines.append("  usecase_snapshot:")
        lines.append(f"    current_sector: {snapshot.get('current_sector')}")
        lines.append(f"    current_mvp_usecase: {snapshot.get('current_mvp_usecase')}")
        lines.append("    usable_now:")
        for item in (snapshot.get("usable_now") or [])[:6]:
            if isinstance(item, dict):
                lines.append(f"      - {item.get('id')}: {item.get('status')}")
        lines.append("    blocked_now:")
        for item in (snapshot.get("blocked_now") or [])[:4]:
            if isinstance(item, dict):
                lines.append(f"      - {item.get('id')}: {item.get('status')}")
        lines.append("    parked_or_later:")
        for item in (snapshot.get("parked_or_later") or [])[:5]:
            if isinstance(item, dict):
                lines.append(f"      - {item.get('id')}: {item.get('status')}")
    schema = payload.get("operator_input_schema") or []
    if schema:
        lines.append("  operator_input_schema:")
        for item in schema:
            field_names = ", ".join(str(field.get("name")) for field in item.get("fields") or [])
            lines.append(f"    - {item.get('id')}: {field_names}")
    template = payload.get("operator_input_template") or {}
    template_groups = template.get("groups") if isinstance(template, dict) else []
    if template_groups:
        lines.append("  operator_input_template:")
        for item in template_groups:
            field_names = ", ".join(str(name) for name in (item.get("template_values") or {}).keys())
            lines.append(f"    - {item.get('id')}: {field_names}")
    completion = payload.get("completion_summary") or {}
    lines.append(
        "  blocked_requirements: "
        + ", ".join(str(item) for item in completion.get("blocked_requirement_ids") or [])
    )
    lines.append("  boundary: read-only; no secret read, provider call, approval consumption, Agent Bus write, browser/host control, or canonical mutation")
    return "\n".join(lines)


def format_mvp_readiness_gate(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "ChaseOS MVP Readiness Gate",
        f"  readiness_status: {payload.get('readiness_status')}",
        f"  overall_goal_complete: {payload.get('overall_goal_complete')}",
        f"  objective_achieved: {payload.get('objective_achieved')}",
        f"  safe_to_call_update_goal_complete: {payload.get('safe_to_call_update_goal_complete')}",
        f"  p0_blockers: {summary.get('p0_blocker_count')}",
        f"  operator_inputs_required: {summary.get('operator_input_count')}",
        f"  next_recommended_pass: {summary.get('next_recommended_pass')}",
        f"  next_operator_action: {summary.get('next_operator_action_id')}",
        "  canonical_operator_handoff: "
        + str(
            (
                payload.get("canonical_operator_handoff")
                if isinstance(payload.get("canonical_operator_handoff"), dict)
                else {}
            ).get("path")
        ),
        "  passes:",
    ]
    barrier_line = _format_autonomous_completion_barrier(payload)
    if barrier_line:
        lines.insert(5, barrier_line)
    safety = (
        payload.get("completion_safety_contract")
        if isinstance(payload.get("completion_safety_contract"), dict)
        else {}
    )
    if safety:
        lines.insert(
            6 if barrier_line else 5,
            "  completion_safety_contract: "
            f"status={safety.get('status')} "
            f"checklist_coverage_is_not_completion={safety.get('checklist_coverage_is_not_completion')} "
            f"update_goal_allowed={safety.get('update_goal_allowed')}",
        )
    setup_scope = (
        payload.get("setup_scope_boundary")
        if isinstance(payload.get("setup_scope_boundary"), dict)
        else {}
    )
    if setup_scope:
        lines.insert(
            7 if safety and barrier_line else 6 if (safety or barrier_line) else 5,
            "  setup_scope: "
            f"status={setup_scope.get('status')} "
            f"non_mvp_gaps={setup_scope.get('non_mvp_setup_gap_ids')} "
            "non_mvp_are_mvp_blockers="
            f"{setup_scope.get('non_mvp_setup_gaps_are_current_mvp_blockers')}",
        )
    for row in payload.get("passes") or []:
        lines.append(f"    {row.get('pass')}. {row.get('name')}: {row.get('status')}")
    inputs = payload.get("operator_inputs_required") or []
    if inputs:
        lines.append("  operator_inputs:")
        for item in inputs:
            lines.append(f"    - {item.get('priority')} {item.get('id')}: {item.get('description')}")
            presence_checks = item.get("reference_presence_check_commands") or []
            if presence_checks:
                lines.append(
                    "      presence_check: "
                    + " ; ".join(str(command) for command in presence_checks)
                )
    snapshot = payload.get("mvp_usecase_snapshot") if isinstance(payload.get("mvp_usecase_snapshot"), dict) else {}
    if snapshot:
        lines.append(f"  current_sector: {snapshot.get('current_sector')}")
        lines.append(f"  current_mvp_usecase: {snapshot.get('current_mvp_usecase')}")
        lines.append(
            "  blocked_now: "
            + ", ".join(
                str(item.get("id"))
                for item in snapshot.get("blocked_now") or []
                if isinstance(item, dict)
            )
        )
        lines.append(
            "  parked_or_later: "
            + ", ".join(
                str(item.get("id"))
                for item in snapshot.get("parked_or_later") or []
                if isinstance(item, dict)
            )
        )
    lines.append("  boundary: read-only gate; no secrets read, no provider calls, no approval execution, no Agent Bus write, no host/browser control.")
    return "\n".join(lines)
