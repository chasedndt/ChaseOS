"""Lower-phase governed conversation log writer contract proposal.

This module defines the Phase 9/AOR side of the Phase 11 Chat conversation
persistence dependency.  It intentionally does not write conversation logs yet;
instead it produces the exact approval, retention/privacy, audit, collision, and
export/delete posture that a future approved writer must satisfy before creating
inspectable records under approved log/audit paths.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
from typing import Any

MODEL_VERSION = "aor.conversation_log_writer_contract.v1"
SURFACE_ID = "aor_conversation_log_writer_contract"
STATUS = "PROPOSED / READ-ONLY / APPROVAL-GATED / WRITES DISABLED"
CONVERSATION_ROOT = "07_LOGS/Conversations"
AGENT_ACTIVITY_ROOT = "07_LOGS/Agent-Activity"
RETENTION_CLASS = "operator-history-retention-governed"
PRIVACY_SCOPE = "operator-local-vault-scoped"
WRITE_MODE = "create_new_only"

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key\s*=\s*)([^\s,;]+)"),
    re.compile(r"(?i)(token\s*=\s*)([^\s,;]+)"),
    re.compile(r"(?i)(password\s*=\s*)([^\s,;]+)"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _slug(value: str, fallback: str = "conversation-log") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (slug or fallback)[:72].strip("-") or fallback


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _redact_secret_match(match: re.Match[str]) -> str:
    if match.lastindex and match.lastindex >= 2:
        return f"{match.group(1)}[REDACTED-SECRET]"
    return "[REDACTED-SECRET]"


def _redact_secrets(value: str) -> tuple[str, bool, list[str]]:
    redacted = value
    labels: list[str] = []
    for pattern in _SECRET_PATTERNS:
        if pattern.search(redacted):
            labels.append(pattern.pattern)
            redacted = pattern.sub(_redact_secret_match, redacted)
    return redacted, bool(labels), labels


def _target_path(title: str, safe_text: str) -> str:
    day = datetime.now(timezone.utc).date().isoformat()
    digest = _sha256_text(f"{title}\n{safe_text}")[:16]
    return f"{CONVERSATION_ROOT}/{day}_{_slug(title)}-{digest}.md"


def _conversation_artifact_preview(
    *,
    title: str,
    safe_text: str,
    target_path: str,
    operator_id: str,
    approval_id: str | None,
) -> str:
    source_hash = _sha256_text(safe_text)
    lines = [
        "---",
        "type: conversation-log",
        "status: proposed-approved-writer-artifact",
        "runtime_surface: aor-conversation-log-writer",
        "phase: Phase 9 AOR / Phase 11 Chat dependency",
        f"operator_id: {operator_id}",
        f"approval_id: {approval_id or 'required-before-write'}",
        "approval_required: true",
        "writer_enabled_now: false",
        "canonical_memory: false",
        "hidden_memory: false",
        f"retention_class: {RETENTION_CLASS}",
        f"privacy_scope: {PRIVACY_SCOPE}",
        f"write_mode: {WRITE_MODE}",
        f"source_message_sha256: {source_hash}",
        "---",
        "",
        f"# {title}",
        "",
        "## Conversation Record Posture",
        "",
        "- This artifact is inspectable operator-history context, not canonical memory.",
        "- Raw credentials, API keys, tokens, passwords, and secret-bearing excerpts are rejected/redacted.",
        "- Export and deletion require an operator-reviewed retention manager request.",
        "- Promotion to knowledge or durable memory requires a separate Gate-approved action.",
        f"- Target path: `{target_path}`",
        "",
        "## Conversation Text",
        "",
        safe_text or "(empty conversation text)",
        "",
    ]
    return "\n".join(lines)


def build_conversation_log_writer_contract(
    vault_root: str | Path,
    *,
    title: str | None = None,
    conversation_text: str | None = None,
    operator_id: str = "operator",
    requested_write: bool = False,
    approval_id: str | None = None,
    approval_status: str | None = None,
    expected_content_sha256: str | None = None,
) -> dict[str, Any]:
    """Return a no-write contract/proposal for the governed log writer.

    The returned payload deliberately avoids directory creation, approval
    consumption, conversation log writes, export/delete execution, hidden memory,
    provider replay, and canonical writeback.  It is safe to use as a lower-phase
    proof packet for the Phase 11 preview surface.
    """

    vault = Path(vault_root).resolve()
    clean_title = _norm(title) or "Conversation Log"
    clean_operator = _norm(operator_id) or "operator"
    normalized_text = _norm(conversation_text)
    safe_text, secret_detected, secret_pattern_refs = _redact_secrets(normalized_text)
    target_path = _target_path(clean_title, safe_text)
    target_abs = vault / target_path
    content_preview = _conversation_artifact_preview(
        title=clean_title,
        safe_text=safe_text,
        target_path=target_path,
        operator_id=clean_operator,
        approval_id=approval_id,
    )
    content_sha = _sha256_text(content_preview)

    blockers: list[str] = []
    if not normalized_text:
        blockers.append("conversation_text_required")
    if secret_detected:
        blockers.append("secret_material_detected")
    target_collision_absent = not target_abs.exists()
    if not target_collision_absent:
        blockers.append("conversation_target_collision")
    if requested_write:
        if not approval_id:
            blockers.append("approved_gate_packet_required")
        if approval_id and str(approval_status or "").lower() != "approved":
            blockers.append("approval_status_not_approved")
        if expected_content_sha256 != content_sha:
            blockers.append("expected_content_sha256_mismatch")

    unique_blockers = list(dict.fromkeys(blockers))
    approved_digest_ready = (
        bool(approval_id)
        and str(approval_status or "").lower() == "approved"
        and expected_content_sha256 == content_sha
        and target_collision_absent
        and normalized_text != ""
        and not secret_detected
    )

    return {
        "ok": not unique_blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "writer_enabled_now": False,
            "requested_write": bool(requested_write),
            "conversation_log_write_allowed": False,
            "approval_ready_if_writer_enabled": approved_digest_ready,
            "secret_material_detected": secret_detected,
            "target_collision_absent": target_collision_absent,
            "retention_governed": True,
            "export_delete_manager_declared": True,
            "canonical_memory": False,
            "hidden_memory": False,
            "blocker_count": len(unique_blockers),
        },
        "conversation_log_artifact": {
            "target_root": CONVERSATION_ROOT,
            "target_path": target_path,
            "approved_path_root_only": True,
            "content_preview": content_preview[:2400],
            "content_sha256": content_sha,
            "content_uses_redacted_text": secret_detected,
            "directory_created": False,
            "target_file_written": False,
            "write_mode": WRITE_MODE,
            "inspectable_markdown_record": True,
            "canonical_memory": False,
            "hidden_memory": False,
        },
        "approval_gate": {
            "approval_required": True,
            "approval_id": approval_id,
            "approval_status": approval_status,
            "expected_content_sha256": expected_content_sha256,
            "actual_content_sha256": content_sha,
            "expected_digest_matches": expected_content_sha256 == content_sha,
            "approved_digest_ready": approved_digest_ready,
            "approval_consumed": False,
            "approval_consumption_allowed_now": False,
            "write_requires_approved_gate_packet": True,
        },
        "retention_privacy_manifest": {
            "retention_class": RETENTION_CLASS,
            "privacy_scope": PRIVACY_SCOPE,
            "default_retention_posture": "retain only approved operator-history records needed for goal continuity",
            "secrets_policy": "reject or redact raw credentials, tokens, API keys, passwords, and secret-bearing excerpts before write",
            "pii_policy": "operator-local-vault-scoped; export and promotion require separate approval",
            "canonical_memory": False,
            "hidden_memory": False,
            "provider_hidden_state_restore_allowed": False,
        },
        "retention_export_delete_manager": {
            "manager_declared": True,
            "export_requires_operator_review": True,
            "delete_requires_operator_review": True,
            "export_performed": False,
            "delete_performed": False,
            "delete_mode": "tombstone_or_remove_after_review_only",
            "export_scope": "selected inspectable conversation records only",
            "raw_secret_export_allowed": False,
            "canonical_promotion_during_export_allowed": False,
            "delete_audit_required": True,
        },
        "audit_cross_reference": {
            "agent_activity_root": AGENT_ACTIVITY_ROOT,
            "audit_record_required_for_write": True,
            "audit_record_written": False,
            "future_audit_fields": [
                "approval_id",
                "conversation_log_path",
                "conversation_content_sha256",
                "retention_class",
                "operator_id",
                "secret_redaction_status",
                "export_delete_review_status",
            ],
        },
        "idempotency_and_collision": {
            "write_mode": WRITE_MODE,
            "target_collision_absent": target_collision_absent,
            "overwrite_allowed": False,
            "duplicate_digest_replay_allowed": False,
            "idempotency_key": _sha256_text(f"{target_path}:{content_sha}")[:24],
        },
        "secret_handling": {
            "raw_secret_rejected": secret_detected,
            "redaction_applied_to_preview": secret_detected,
            "secret_pattern_refs_detected": secret_pattern_refs,
            "secret_material_persisted": False,
            "raw_conversation_text_returned": False,
        },
        "authority_boundaries": {
            "phase11_chat_is_preview_request_surface_only": True,
            "lower_phase_writer_required": True,
            "writer_enabled_now": False,
            "approval_queue_mutation_allowed": False,
            "conversation_log_write_allowed": False,
            "export_allowed_without_review": False,
            "delete_allowed_without_review": False,
            "canonical_promotion_allowed": False,
            "canonical_writeback_allowed": False,
            "hidden_memory_persistence_allowed": False,
            "provider_replay_allowed": False,
            "agent_bus_task_write_allowed": False,
        },
        "blocked_reasons": unique_blockers,
        "closeout_evidence": {
            "conversation_log_written": False,
            "audit_log_written": False,
            "approval_consumed": False,
            "export_performed": False,
            "delete_performed": False,
            "secret_material_persisted": False,
            "hidden_memory_persisted": False,
            "canonical_writeback_performed": False,
            "provider_call_performed": False,
        },
    }
