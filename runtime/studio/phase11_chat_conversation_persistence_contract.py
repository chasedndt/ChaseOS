"""Read-only Phase 11 Chat conversation persistence/session-history contract.

This contract previews the future conversation-log write and approval packet
shape for Chat, but it does not create ``07_LOGS/Conversations``, write a
conversation Markdown file, queue an approval request, or persist hidden model
memory.  Its job is to define the safe boundary for making long-running /goal
conversation history durable operating context: inspectable, retention-governed,
privacy-scoped, audited, and always subordinate to ChaseOS Gate governance.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_router_contract import build_phase11_chat_router_contract


MODEL_VERSION = "studio.phase11_chat_conversation_persistence_contract.v2"
SURFACE_ID = "phase11_chat_conversation_persistence_contract"
PASS_ID = "phase11-chat-conversation-persistence-session-history-contract"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / CONVERSATION WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-approval-queue-write-execution-proof"
CONVERSATION_ROOT = "07_LOGS/Conversations"
AGENT_ACTIVITY_ROOT = "07_LOGS/Agent-Activity"
RETENTION_CLASS = "operator-history-retention-governed"
PRIVACY_SCOPE = "operator-local-vault-scoped"
RECOVERY_MODE = "bounded-rehydration-from-inspectable-log-summary"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _digest(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


SECRET_REDACTION_TOKEN = "[REDACTED_SECRET]"
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "openai_style_api_key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE),
    ),
    (
        "github_style_token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE),
    ),
    (
        "gitlab_style_token",
        re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b", re.IGNORECASE),
    ),
    (
        "slack_style_token",
        re.compile(r"\bxox(?:b|p|a|r|s)-[A-Za-z0-9-]{20,}\b", re.IGNORECASE),
    ),
    (
        "password_assignment",
        re.compile(r"(?i)(\b(?:password|passwd|pwd)\s*[:=]\s*)([^\s,;]{8,})"),
    ),
    (
        "token_assignment",
        re.compile(r"(?i)(\b(?:api[_ -]?key|secret|token|credential)\s*[:=]\s*)([^\s,;]{8,})"),
    ),
    (
        "bearer_token",
        re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{16,})"),
    ),
]


def _redact_secret_bearing_input(message: str) -> dict[str, Any]:
    redacted = message
    categories: list[str] = []
    redaction_count = 0
    for category, pattern in SECRET_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            nonlocal redaction_count
            redaction_count += 1
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}{SECRET_REDACTION_TOKEN}"
            return SECRET_REDACTION_TOKEN

        redacted, count = pattern.subn(repl, redacted)
        if count:
            categories.append(category)
    return {
        "contains_secret": bool(redaction_count),
        "redacted_message": redacted,
        "redaction_count": redaction_count,
        "indicator_categories": list(dict.fromkeys(categories)),
    }


def _slug(value: str, fallback: str = "chat-session") -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (text or fallback)[:72].strip("-") or fallback


def _title(message: str, explicit_title: str | None = None) -> str:
    if explicit_title:
        return " ".join(str(explicit_title).strip().split())[:96] or "Chat Session"
    if not message:
        return "Empty Chat Session"
    words = message.split()[:8]
    candidate = " ".join(words).strip(" .,:;")
    return candidate[:96] or "Chat Session"


def _conversation_target_path(message: str, title: str) -> str:
    # Stable target preview for a given day + input, without touching the target directory.
    day = datetime.now(timezone.utc).date().isoformat()
    stem = f"{day}_{_slug(title)}-{_digest(message or title)}"
    return f"{CONVERSATION_ROOT}/{stem}.md"


def _content_preview(
    *,
    title: str,
    message: str,
    intent: str,
    target_path: str,
) -> str:
    source_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
    return "\n".join(
        [
            "---",
            "type: conversation-log",
            "status: draft-persistence-preview",
            "generated_by: studio-chat-preview",
            "phase: Phase 11",
            f"phase11_intent: {intent}",
            "approval_required: true",
            "canonical_memory: false",
            "hidden_memory: false",
            f"retention_class: {RETENTION_CLASS}",
            f"privacy_scope: {PRIVACY_SCOPE}",
            f"recovery_mode: {RECOVERY_MODE}",
            "chat_persistence_contract_only: true",
            f"source_message_sha256: {source_hash}",
            "---",
            "",
            f"# {title}",
            "",
            "## Persistence Posture",
            "",
            "- Conversation logs are historical records, not canonical memory.",
            "- Promotion to knowledge, project state, or memory requires a later explicit approval.",
            "- Long-history recovery may rehydrate bounded summaries only from inspectable records.",
            "- Raw secrets, credentials, hidden model state, and unreviewed canonical claims are prohibited.",
            f"- Target preview: `{target_path}`",
            "",
            "## User Message Preview",
            "",
            message or "(empty message)",
            "",
        ]
    )


def build_phase11_chat_conversation_persistence_contract(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Build a no-write preview for future Chat conversation persistence."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    normalized_title = _norm(title) if title is not None else ""
    message_secret_report = _redact_secret_bearing_input(normalized_message)
    title_secret_report = _redact_secret_bearing_input(normalized_title)
    safe_message = str(message_secret_report["redacted_message"])
    safe_title = str(title_secret_report["redacted_message"]) if title is not None else None
    secret_bearing_input = bool(
        message_secret_report["contains_secret"] or title_secret_report["contains_secret"]
    )
    secret_indicator_categories = list(
        dict.fromkeys(
            list(message_secret_report["indicator_categories"])
            + list(title_secret_report["indicator_categories"])
        )
    )
    secret_redaction_count = int(message_secret_report["redaction_count"]) + int(
        title_secret_report["redaction_count"]
    )
    router = build_phase11_chat_router_contract(
        vault,
        message=safe_message,
        explicit_intent=explicit_intent,
    )
    intent = str((router.get("intent_result") or {}).get("intent_class") or "chat-answer")
    input_posture = router.get("input_posture") or {}
    conversation_title = _title(safe_message, safe_title)
    target_path = _conversation_target_path(safe_message, conversation_title)
    target_abs = vault / target_path
    preview = _content_preview(
        title=conversation_title,
        message=safe_message,
        intent=intent,
        target_path=target_path,
    )
    content_sha = hashlib.sha256(preview.encode("utf-8")).hexdigest()

    blockers: list[str] = []
    if not normalized_message:
        blockers.append("message_required_for_conversation_persistence_preview")
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    if secret_bearing_input:
        blockers.append("secret_or_credential_indicator_present")
    if target_abs.exists():
        blockers.append("conversation_target_collision")
    blockers.extend(
        [
            "operator_conversation_persistence_approval_missing",
            "conversation_log_writer_not_enabled",
            "approval_queue_writer_not_enabled_for_conversation_persistence",
            "conversation_log_write_denied",
        ]
    )
    preview_ready = bool(normalized_message) and not any(
        blocker in blockers
        for blocker in {
            "prompt_injection_indicator_present",
            "secret_or_credential_indicator_present",
            "conversation_target_collision",
        }
    )
    approval_id_preview = f"chat-conversation-persistence-appr-{_digest(target_path + ':' + content_sha, 16)}"

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "message_present": bool(normalized_message),
            "intent_class": intent,
            "conversation_preview_ready": preview_ready,
            "conversation_write_allowed_now": False,
            "approval_queue_write_allowed_now": False,
            "approval_request_created": False,
            "target_path_preview": target_path,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
            "retention_class": RETENTION_CLASS,
            "privacy_scope": PRIVACY_SCOPE,
            "recovery_mode": RECOVERY_MODE,
            "hidden_memory_allowed": False,
        },
        "conversation_descriptor": {
            "title": conversation_title,
            "participants": ["operator", "studio-chat"],
            "source_message_sha256": hashlib.sha256(normalized_message.encode("utf-8")).hexdigest(),
            "source_message_chars": len(normalized_message),
            "source_message_contains_secret": bool(message_secret_report["contains_secret"]),
            "source_message_redacted": bool(message_secret_report["contains_secret"]),
            "redacted_message_sha256": hashlib.sha256(safe_message.encode("utf-8")).hexdigest(),
            "source_title_chars": len(normalized_title),
            "source_title_contains_secret": bool(title_secret_report["contains_secret"]),
            "source_title_redacted": bool(title_secret_report["contains_secret"]),
            "redacted_title_sha256": hashlib.sha256((safe_title or "").encode("utf-8")).hexdigest(),
            "secret_indicator_categories": secret_indicator_categories,
            "intent_class": intent,
            "target_root": CONVERSATION_ROOT,
            "target_path_preview": target_path,
            "retention_class": RETENTION_CLASS,
            "privacy_scope": PRIVACY_SCOPE,
            "canonical_memory": False,
            "hidden_memory": False,
            "promotion_requires_future_approval": True,
        },
        "persistence_contract": {
            "purpose": "durable operating context for long-running /goal chat sessions",
            "storage_record_preview": CONVERSATION_ROOT,
            "audit_record_preview": AGENT_ACTIVITY_ROOT,
            "record_is_inspectable": True,
            "record_is_user_exportable": True,
            "record_is_retention_governed": True,
            "record_is_privacy_scoped": True,
            "record_is_canonical_memory": False,
            "record_is_hidden_memory": False,
            "approved_lower_phase_contracts_required": [
                "06_AGENTS/Agent-Memory-Architecture.md",
                "06_AGENTS/Hermes-Memory-Boundary.md",
                "06_AGENTS/Agent-Security-Model.md",
                "07_LOGS/Agent-Activity/",
            ],
        },
        "history_classification": {
            "durable_context": {
                "allowed": True,
                "description": "Inspectable conversation/session records and bounded recovery summaries for the active operator goal.",
                "storage": CONVERSATION_ROOT,
                "canonical_memory": False,
            },
            "audit_log": {
                "allowed": True,
                "description": "Agent-Activity writeback records that state what was persisted or previewed and under which approval envelope.",
                "storage": AGENT_ACTIVITY_ROOT,
                "append_only": True,
            },
            "retention_governed_record": {
                "allowed": True,
                "description": "Conversation records with explicit retention class, target path, source hashes, and deletion/export review surface.",
                "retention_class": RETENTION_CLASS,
            },
            "privacy_scoped_data": {
                "allowed": True,
                "description": "Operator-local session content scoped to the declared vault/workspace and never used as cross-user or ambient runtime memory.",
                "privacy_scope": PRIVACY_SCOPE,
            },
            "prohibited_hidden_memory": {
                "allowed": False,
                "description": "Opaque provider state, uninspectable embeddings, unlisted caches, secrets, credentials, or silent canonical promotion.",
                "must_block": True,
            },
        },
        "conversation_log_preview": {
            "visible": True,
            "write_allowed_now": False,
            "writer_called": False,
            "directory_created": False,
            "target_file_written": False,
            "content_preview": preview[:1600],
            "content_sha256": content_sha,
            "source_message_contains_secret": secret_bearing_input,
            "secret_material_redacted": secret_bearing_input,
            "redaction_count": secret_redaction_count,
        },
        "long_history_recovery": {
            "supported_mode": RECOVERY_MODE,
            "restore_source": CONVERSATION_ROOT,
            "restore_manifest_owner_surface": "runtime.memory.long_history_rehydration",
            "phase11_chat_role": "consumer_of_restore_manifest",
            "automatic_restore_enabled_now": False,
            "restore_material": [
                "operator-approved conversation log metadata",
                "bounded summary chunks with source hashes",
                "Agent-Activity audit references",
            ],
            "raw_full_history_auto_injection_allowed": False,
            "canonical_promotion_during_restore_allowed": False,
            "provider_hidden_state_restore_allowed": False,
            "requires_user_visible_manifest": True,
            "conflict_rule": "vault-governed contract and current approval envelope win over restored chat context",
        },
        "retention_privacy_rules": {
            "retention_class": RETENTION_CLASS,
            "privacy_scope": PRIVACY_SCOPE,
            "default_posture": "retain only approved conversation records and bounded summaries needed for goal continuity",
            "secrets_policy": "never persist raw credentials, tokens, API keys, or secret-bearing excerpts",
            "pii_policy": "PII remains operator-local and must not be exported or promoted without explicit approval",
            "deletion_review_surface": "future lower-phase retention manager; Phase 11 only declares the requirement",
            "export_review_surface": "future lower-phase memory/audit inspector; Phase 11 only declares the requirement",
        },
        "future_approval_packet_preview": {
            "visible": True,
            "approval_id_preview": approval_id_preview,
            "approval_artifact_path_preview": f"runtime/studio/approvals/{approval_id_preview}.json",
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "required_approval_class": "studio_chat_conversation_persistence_approval_future",
            "future_status_if_written": "pending",
            "action_spec_preview": {
                "action_type": "create_file",
                "target_path": target_path,
                "submitted_by": "studio-chat",
                "note": "Phase 11 Chat conversation persistence preview",
                "content_sha256": content_sha,
                "metadata": {
                    "pass": PASS_ID,
                    "phase11_intent": intent,
                    "source_surface": "phase11_chat_panel_readonly_contract",
                    "conversation_log": True,
                    "canonical_memory": False,
                    "queue_contract_only": True,
                    "secret_bearing_input_blocked": secret_bearing_input,
                    "secret_material_redacted": secret_bearing_input,
                },
            },
        },
        "preflight_checks": {
            "message_present": bool(normalized_message),
            "prompt_injection_absent": not bool(input_posture.get("prompt_injection_suspected")),
            "secret_bearing_input_absent": not secret_bearing_input,
            "secret_like_input_detected": secret_bearing_input,
            "secret_material_redacted_from_preview": secret_bearing_input,
            "target_under_conversations_root": target_path.startswith(f"{CONVERSATION_ROOT}/"),
            "target_is_markdown": target_path.endswith(".md"),
            "target_collision_absent": not target_abs.exists(),
            "conversation_log_writer_built": False,
            "approval_queue_writer_enabled": False,
            "live_provider_execution_required": False,
            "hidden_memory_absent": True,
            "secret_capture_allowed": False,
            "retention_class_declared": True,
            "privacy_scope_declared": True,
        },
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "authority": {
            "read_only": True,
            "planning_only": True,
            "conversation_persistence_allowed": False,
            "conversation_log_write_allowed": False,
            "conversation_directory_create_allowed": False,
            "approval_queue_write_allowed": False,
            "approval_execution_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "vault_writes_allowed": False,
            "canonical_mutation_allowed": False,
            "hidden_memory_allowed": False,
            "secret_persistence_allowed": False,
            "automatic_long_history_rehydration_allowed": False,
        },
        "denied_by_this_surface": [
            "conversation_directory_create",
            "conversation_log_write",
            "studio_approval_queue_write",
            "approval_artifact_write",
            "approval_grant_or_reject",
            "approval_execution",
            "provider_api_call",
            "runtime_dispatch",
            "browser_control",
            "agent_bus_task_write",
            "vault_write_from_chat",
            "canonical_writeback",
            "hidden_memory_persistence",
            "secret_or_credential_persistence",
            "automatic_canonical_promotion_from_history",
            "opaque_provider_thread_state_restore",
        ],
        "lower_phase_available_contracts": [
            {
                "implemented_contract": "long-history bounded rehydration loader",
                "owner_surface": "runtime.memory.long_history_rehydration",
                "implementation_artifact": "runtime/memory/long_history_rehydration.py",
                "readiness": "available_for_manifest_bounded_restore",
                "phase11_chat_role": "consumer_only",
                "automatic_restore_enabled_now": False,
                "raw_full_history_auto_injection_allowed": False,
                "canonical_promotion_during_restore_allowed": False,
                "provider_hidden_state_restore_allowed": False,
                "agent_bus_write_allowed": False,
                "approval_consumption_allowed": False,
                "readiness_gate": "Phase 11 Chat may consume a user-visible restore manifest only after lower-phase conversation-log writer/retention governance exists and explicit operator approval selects the manifest.",
            },
        ],
        "lower_phase_dependency_report": [
            {
                "missing_contract": "approved conversation log writer plus retention/export/delete manager",
                "affected_phase10_or_phase11_surface": SURFACE_ID,
                "lower_phase_owner_or_surface": "Phase 9 AOR memory/audit owner + Agent-Activity writeback surface",
                "implementation_proposal_artifact": "runtime/aor/conversation_log_writer_contract.py",
                "minimum_proof_needed": "no-secret fixtures, retention/privacy manifest, inspectable conversation-log artifact preview, export/delete review posture, audit-log cross-reference, and collision/idempotency handling",
                "blocked_action_reason": "Phase 11 Chat may preview persistence but cannot create durable conversation state until the lower-phase memory/audit writer is approved/enabled and consumes an exact approved digest",
            },
        ],
        "source_contracts": {
            "router_contract": {
                "surface": router.get("surface"),
                "model_version": router.get("model_version"),
            },
            "post_closeout_planning": "runtime.studio.phase11_post_closeout_planning.build_phase11_post_closeout_planning",
        },
        "closeout_evidence": {
            "conversation_persistence_contract_built": True,
            "conversation_write_performed": False,
            "conversation_directory_created": False,
            "approval_request_created": False,
            "live_execution_performed": False,
            "hidden_memory_persisted": False,
            "secret_material_persisted": False,
            "secret_bearing_input_detected": secret_bearing_input,
            "secret_material_redacted_from_preview": secret_bearing_input,
            "retention_privacy_contract_declared": True,
            "long_history_recovery_contract_declared": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }


def format_phase11_chat_conversation_persistence_contract(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    descriptor = payload.get("conversation_descriptor") or {}
    return "\n".join(
        [
            "Phase 11 Chat Conversation Persistence Session History Contract",
            f"  status: {payload.get('status')}",
            f"  intent: {summary.get('intent_class')}",
            f"  title: {descriptor.get('title')}",
            f"  target: {summary.get('target_path_preview')}",
            f"  preview_ready: {summary.get('conversation_preview_ready')}",
            f"  conversation_write_allowed_now: {summary.get('conversation_write_allowed_now')}",
            f"  approval_queue_write_allowed_now: {summary.get('approval_queue_write_allowed_now')}",
            f"  retention_class: {summary.get('retention_class')}",
            f"  privacy_scope: {summary.get('privacy_scope')}",
            f"  recovery_mode: {summary.get('recovery_mode')}",
            f"  hidden_memory_allowed: {summary.get('hidden_memory_allowed')}",
            f"  next: {summary.get('next_recommended_pass')}",
        ]
    )
