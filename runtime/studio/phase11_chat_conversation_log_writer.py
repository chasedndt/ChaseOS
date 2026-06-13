"""Phase 11 Chat conversation log writer.

Governed executor that persists one Chat session as a conversation-log Markdown
record under ``07_LOGS/Conversations/``. The record stores:
- session/conversation id
- user prompt (redacted of secret-bearing text)
- provider response (output text, not raw API payload)
- runtime task ids and result summaries (Hermes / OpenClaw)
- approval ids, digests, operator statements, and evidence paths
- lane status for provider, Hermes, OpenClaw Discord-control, OpenClaw cron-control
- Agent Bus readback snapshot at write time

Hard boundaries:
- Never stores secret values, raw API keys, tokens, or credential values.
- Redacts secret-like patterns from user input before writing.
- Does not promote to canonical memory automatically.
- Does not write if a record for the same session already exists (idempotent).
- Requires explicit operator approval statement before writing.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_conversation_persistence_contract import (
    _redact_secret_bearing_input,
    _slug,
    _title,
    CONVERSATION_ROOT,
)


MODEL_VERSION = "studio.phase11_chat_conversation_log_writer.v1"
SURFACE_ID = "phase11_chat_conversation_log_writer"
PASS_ID = "phase11-chat-conversation-log-writer"
STATUS = "COMPLETE / CONVERSATION LOG WRITTEN"
STATUS_DRY = "COMPLETE / DRY RUN / NO FILE WRITTEN"
STATUS_BLOCKED = "BLOCKED / CONVERSATION LOG NOT WRITTEN"
NEXT_RECOMMENDED_PASS = "phase11-chat-runtime-result-display"

AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"
MARKER_DIR = Path("runtime/studio/approvals/_conversation_log_markers")

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_style", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE)),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE)),
    ("bearer", re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{16,})")),
    ("token_assign", re.compile(r"(?i)(\b(?:api[_ -]?key|secret|token|credential)\s*[:=]\s*)([^\s,;]{8,})")),
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_short(value: str, length: int = 16) -> str:
    return _sha256(value)[:length]


def _redact(text: str) -> str:
    result = _redact_secret_bearing_input(text)
    return str(result["redacted_message"])


def _session_id(user_prompt: str, session_hint: str | None) -> str:
    base = session_hint or user_prompt or _now_utc()
    return f"chat-session-{_sha256_short(base, 20)}"


def _conversation_path(session_id: str, title: str) -> str:
    day = datetime.now(timezone.utc).date().isoformat()
    stem = f"{day}_{_slug(title)}-{_sha256_short(session_id, 12)}"
    return f"{CONVERSATION_ROOT}/{stem}.md"


def _lane_md_row(name: str, status: str | None, task_id: str | None, summary: str | None) -> str:
    status_label = str(status or "not_run").upper()
    task_label = f"`{task_id}`" if task_id else "—"
    summary_text = (_norm(summary) or "")[:200]
    return f"| {name} | {status_label} | {task_label} | {summary_text} |"


def _build_markdown(
    *,
    session_id: str,
    title: str,
    operator_id: str,
    operator_statement: str,
    user_prompt_safe: str,
    provider_output: str | None,
    provider_id: str | None,
    provider_model: str | None,
    provider_approval_id: str | None,
    provider_digest: str | None,
    provider_evidence_path: str | None,
    hermes_task_id: str | None,
    hermes_status: str | None,
    hermes_result_summary: str | None,
    hermes_approval_id: str | None,
    openclaw_discord_task_id: str | None,
    openclaw_discord_status: str | None,
    openclaw_discord_result_summary: str | None,
    openclaw_cron_task_id: str | None,
    openclaw_cron_status: str | None,
    openclaw_cron_result_summary: str | None,
    bus_readback_snapshot: list[dict[str, Any]] | None,
    additional_evidence: list[str] | None,
    generated_at: str,
) -> str:
    lines = [
        "---",
        "type: conversation-log",
        f"session_id: {session_id}",
        f"title: {title}",
        f"operator_id: {operator_id}",
        f"generated_at_utc: {generated_at}",
        "phase: Phase 11",
        "canonical_memory: false",
        "hidden_memory: false",
        "retention_class: operator-history-retention-governed",
        "privacy_scope: operator-local-vault-scoped",
        "secret_values_stored: false",
        "promotion_requires_approval: true",
        "---",
        "",
        f"# {title}",
        "",
        f"**Session:** `{session_id}`  ",
        f"**Generated:** {generated_at}  ",
        f"**Operator:** {operator_id}  ",
        "",
        "---",
        "",
        "## Operator Statement",
        "",
        operator_statement or "(no operator statement provided)",
        "",
        "---",
        "",
        "## User Prompt",
        "",
        "> *Secret-bearing text is redacted before storage.*",
        "",
        user_prompt_safe or "(empty prompt)",
        "",
        "---",
        "",
        "## Provider Response",
        "",
    ]

    if provider_output:
        lines += [
            f"**Provider:** {provider_id or 'unknown'}  ",
            f"**Model:** {provider_model or 'unknown'}  ",
            f"**Approval:** `{provider_approval_id or '—'}`  ",
            f"**Digest:** `{provider_digest or '—'}`  ",
            f"**Evidence:** `{provider_evidence_path or '—'}`  ",
            "",
            provider_output,
        ]
    else:
        lines.append("*(provider call not performed or not available)*")

    lines += [
        "",
        "---",
        "",
        "## Runtime Lane Status",
        "",
        "| Lane | Status | Task ID | Summary |",
        "|------|--------|---------|---------|",
        _lane_md_row("Provider", "executed" if provider_output else "not_run", provider_approval_id, provider_output[:120] if provider_output else None),
        _lane_md_row("Hermes / Main Runtime", hermes_status, hermes_task_id, hermes_result_summary),
        _lane_md_row("OpenClaw Discord Control", openclaw_discord_status, openclaw_discord_task_id, openclaw_discord_result_summary),
        _lane_md_row("OpenClaw Cron Control", openclaw_cron_status, openclaw_cron_task_id, openclaw_cron_result_summary),
        "",
    ]

    if bus_readback_snapshot:
        lines += [
            "---",
            "",
            "## Agent Bus Readback (at write time)",
            "",
            "```json",
            json.dumps(bus_readback_snapshot[:10], indent=2, default=str),
            "```",
            "",
        ]

    if additional_evidence:
        lines += [
            "---",
            "",
            "## Evidence Paths",
            "",
        ]
        for path in additional_evidence:
            lines.append(f"- `{path}`")
        lines.append("")

    lines += [
        "---",
        "",
        "## Persistence Posture",
        "",
        "- This record is a historical session log, not canonical memory.",
        "- Promotion to knowledge, project state, or memory requires a later explicit approval.",
        "- Secret values, credentials, and raw API keys are never stored here.",
        "- Retention and deletion are governed by operator review.",
    ]

    return "\n".join(lines) + "\n"


def write_conversation_log(
    vault_root: str | Path,
    *,
    session_hint: str | None = None,
    operator_id: str = "studio-operator",
    operator_approval_statement: str,
    user_prompt: str,
    provider_output: str | None = None,
    provider_id: str | None = None,
    provider_model: str | None = None,
    provider_approval_id: str | None = None,
    provider_digest: str | None = None,
    provider_evidence_path: str | None = None,
    hermes_task_id: str | None = None,
    hermes_status: str | None = None,
    hermes_result_summary: str | None = None,
    hermes_approval_id: str | None = None,
    openclaw_discord_task_id: str | None = None,
    openclaw_discord_status: str | None = None,
    openclaw_discord_result_summary: str | None = None,
    openclaw_cron_task_id: str | None = None,
    openclaw_cron_status: str | None = None,
    openclaw_cron_result_summary: str | None = None,
    bus_readback_snapshot: list[dict[str, Any]] | None = None,
    additional_evidence: list[str] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Write one governed conversation log record.

    ``dry_run=True`` (default) previews the output without writing.
    ``dry_run=False`` requires ``operator_approval_statement`` to be non-empty.
    """

    vault = Path(vault_root).resolve()
    generated_at = _now_utc()
    prompt_safe = _redact(user_prompt)
    provider_out_safe = _redact(provider_output or "")

    blockers: list[str] = []
    if not user_prompt:
        blockers.append("user_prompt_required")
    if not dry_run and not _norm(operator_approval_statement):
        blockers.append("operator_approval_statement_required_for_live_write")

    session_id = _session_id(prompt_safe, session_hint)
    conv_title = _title(prompt_safe)
    target_rel = _conversation_path(session_id, conv_title)
    target_abs = vault / target_rel

    if not dry_run and target_abs.exists():
        blockers.append("conversation_log_collision_target_exists")

    marker_path = vault / MARKER_DIR / f"{session_id}.json"
    if not dry_run and marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    content = _build_markdown(
        session_id=session_id,
        title=conv_title,
        operator_id=_norm(operator_id) or "studio-operator",
        operator_statement=_norm(operator_approval_statement),
        user_prompt_safe=prompt_safe,
        provider_output=provider_out_safe or None,
        provider_id=provider_id,
        provider_model=provider_model,
        provider_approval_id=provider_approval_id,
        provider_digest=provider_digest,
        provider_evidence_path=provider_evidence_path,
        hermes_task_id=hermes_task_id,
        hermes_status=hermes_status,
        hermes_result_summary=hermes_result_summary,
        hermes_approval_id=hermes_approval_id,
        openclaw_discord_task_id=openclaw_discord_task_id,
        openclaw_discord_status=openclaw_discord_status,
        openclaw_discord_result_summary=openclaw_discord_result_summary,
        openclaw_cron_task_id=openclaw_cron_task_id,
        openclaw_cron_status=openclaw_cron_status,
        openclaw_cron_result_summary=openclaw_cron_result_summary,
        bus_readback_snapshot=bus_readback_snapshot,
        additional_evidence=additional_evidence,
        generated_at=generated_at,
    )
    content_sha = _sha256(content)

    if blockers:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "status": STATUS_BLOCKED,
            "generated_at_utc": generated_at,
            "vault_root": str(vault),
            "dry_run": dry_run,
            "session_id": session_id,
            "target_path": target_rel,
            "file_written": False,
            "secret_values_stored": False,
            "blocked_reasons": list(dict.fromkeys(blockers)),
            "content_preview": content[:800],
        }

    file_written = False
    audit_path: str | None = None

    if not dry_run:
        target_abs.parent.mkdir(parents=True, exist_ok=True)
        marker_path.parent.mkdir(parents=True, exist_ok=True)

        marker_path.write_text(
            json.dumps({
                "schema_version": "phase11_conversation_log_marker.v1",
                "session_id": session_id,
                "target_path": target_rel,
                "status": "writing",
                "operator_id": _norm(operator_id),
                "created_at_utc": generated_at,
                "secret_values_stored": False,
            }, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        target_abs.write_text(content, encoding="utf-8")
        file_written = True

        marker_path.write_text(
            json.dumps({
                "schema_version": "phase11_conversation_log_marker.v1",
                "session_id": session_id,
                "target_path": target_rel,
                "status": "written",
                "content_sha256": content_sha,
                "operator_id": _norm(operator_id),
                "written_at_utc": _now_utc(),
                "secret_values_stored": False,
            }, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        audit_root = vault / AUDIT_DIR
        audit_root.mkdir(parents=True, exist_ok=True)
        audit_file = audit_root / f"{PASS_ID}-{session_id[:20]}.md"
        audit_file.write_text(
            "\n".join([
                "---",
                "type: agent-activity",
                "runtime: Codex",
                f"pass_id: {PASS_ID}",
                f"session_id: {session_id}",
                f"status: {STATUS}",
                "---",
                "",
                "# Phase 11 Chat Conversation Log Written",
                "",
                f"session_id: {session_id}",
                f"target_path: {target_rel}",
                f"operator_id: {_norm(operator_id)}",
                f"written_at_utc: {_now_utc()}",
                "secret_values_stored: false",
                "canonical_mutation_performed: false",
                "",
            ]),
            encoding="utf-8",
        )
        audit_path = str(audit_file.relative_to(vault))

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if file_written else STATUS_DRY,
        "generated_at_utc": generated_at,
        "vault_root": str(vault),
        "dry_run": dry_run,
        "session_id": session_id,
        "target_path": target_rel,
        "file_written": file_written,
        "content_sha256": content_sha,
        "content_preview": content[:800],
        "secret_values_stored": False,
        "canonical_mutation_performed": False,
        "audit_path": audit_path,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocked_reasons": [],
        "authority": {
            "conversation_log_write_allowed": True,
            "canonical_memory_write_allowed": False,
            "provider_call_allowed": False,
            "agent_bus_task_write_allowed": False,
            "secret_value_storage_allowed": False,
            "credential_display_allowed": False,
        },
    }
