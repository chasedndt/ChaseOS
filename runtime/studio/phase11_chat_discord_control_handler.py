"""Phase 11 Chat runtime-side Discord control handler.

Processes Chat-originated Discord-control handoff payloads delivered via the
Agent Bus. Uses ``.chaseos/discord_instance_bindings.yaml`` for local channel
IDs and references credentials only by their env var names — never prints or
persists token/webhook values.

Hard boundaries:
- Reads discord_instance_bindings.yaml for IDs only.
- Never prints, returns, or logs Discord token/webhook values.
- Dry-run by default: no Discord API call unless ``dry_run=False`` AND
  ``operator_approved=True``.
- Any action that sends a message, creates a thread, or changes channels
  requires approval evidence before execution.
- Evidence record written regardless of dry-run status.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request
import yaml


MODEL_VERSION = "studio.phase11_chat_discord_control_handler.v1"
SURFACE_ID = "phase11_chat_discord_control_handler"
PASS_ID = "phase11-chat-discord-control-handler"
STATUS_DRY = "COMPLETE / DRY RUN / NO DISCORD API CALL"
STATUS_EXECUTED = "COMPLETE / DISCORD API CALL ATTEMPTED"
STATUS_BLOCKED = "BLOCKED / DISCORD CONTROL NOT EXECUTED"
NEXT_RECOMMENDED_PASS = "phase11-chat-schedule-apply-handler"

BINDINGS_PATH = ".chaseos/discord_instance_bindings.yaml"
EVIDENCE_DIR = Path("07_LOGS") / "Agent-Activity"
DISCORD_API_BASE = "https://discord.com/api/v10"

_ALLOWED_ACTIONS = {"post_message", "post_audit", "dry_run_ping"}
_CREDENTIAL_ENV_REFS: dict[str, str] = {
    "openclaw": "OPENCLAW_DISCORD_BOT_TOKEN",
    "hermes": "HERMES_DISCORD_BOT_TOKEN",
    "default": "CHASEOS_DISCORD_BOT_TOKEN",
}
_SAFE_CHANNEL_CLASSES = {
    "audit-writeback", "alerts", "debug", "docs-archive", "runtime-chat",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_bindings(vault: Path) -> dict[str, Any]:
    path = vault / BINDINGS_PATH
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        return yaml.safe_load(text) or {}
    except Exception:
        return {}


def _channel_info(bindings: dict[str, Any], channel_name: str) -> dict[str, Any] | None:
    """Look up a channel by name across primary and supplemental channels."""
    for section_key in ("primary_channels", "supplemental_channels"):
        section = bindings.get(section_key) or {}
        for _key, entry in section.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("name") == channel_name or _key == channel_name:
                return entry
    return None


def _redact_token(value: str) -> str:
    if len(value) <= 8:
        return "[REDACTED]"
    return value[:4] + "…" + value[-4:]


def _post_discord_message(
    *,
    channel_id: str,
    content: str,
    bot_token: str,
    timeout: int = 15,
) -> dict[str, Any]:
    """Send one message to a Discord channel. Returns ok/status/error dict."""
    body = json.dumps({"content": content[:2000]}).encode("utf-8")
    req = request.Request(
        f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json",
            "User-Agent": "ChaseOS/1.0",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw else {}
            return {
                "ok": True,
                "status_code": getattr(resp, "status", 200),
                "message_id": payload.get("id"),
                "channel_id": channel_id,
                "token_displayed": False,
            }
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        return {
            "ok": False,
            "status_code": exc.code,
            "error_type": "http_error",
            "reason": detail,
            "channel_id": channel_id,
            "token_displayed": False,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "error_type": exc.__class__.__name__,
            "reason": str(exc)[:300],
            "channel_id": channel_id,
            "token_displayed": False,
        }


def _write_evidence(
    vault: Path,
    *,
    session_id: str,
    action: str,
    channel_name: str | None,
    channel_class: str | None,
    dry_run: bool,
    operator_approved: bool,
    call_result: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> str:
    root = vault / EVIDENCE_DIR
    root.mkdir(parents=True, exist_ok=True)
    filename = f"{PASS_ID}-{session_id[:20]}.md"
    path = root / filename
    status = STATUS_DRY if dry_run else (STATUS_EXECUTED if operator_approved else STATUS_BLOCKED)
    lines = [
        "---",
        "type: agent-activity",
        "runtime: Codex",
        f"pass_id: {PASS_ID}",
        f"session_id: {session_id}",
        f"status: {status}",
        "---",
        "",
        "# Phase 11 Chat Discord Control Handler",
        "",
        f"action: {action}",
        f"channel_name: {channel_name or '—'}",
        f"channel_class: {channel_class or '—'}",
        f"dry_run: {dry_run}",
        f"operator_approved: {operator_approved}",
        f"discord_api_called: {bool(call_result and not dry_run and operator_approved)}",
        "token_displayed: false",
        f"blocked_reasons: {blocked_reasons or []}",
        f"written_at_utc: {_now_utc()}",
        "",
    ]
    if call_result:
        lines.append(f"call_ok: {call_result.get('ok')}")
        lines.append(f"call_status_code: {call_result.get('status_code')}")
    path.write_text("\n".join(lines), encoding="utf-8")
    try:
        return path.relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def handle_discord_control(
    vault_root: str | Path,
    *,
    action: str = "post_audit",
    channel_name: str | None = None,
    message_content: str | None = None,
    runtime_id: str = "openclaw",
    operator_approved: bool = False,
    operator_approval_statement: str | None = None,
    expected_action_digest: str | None = None,
    dry_run: bool = True,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    """Process a Chat-originated Discord-control request.

    Args:
        vault_root: Vault root directory.
        action: Permitted action — ``post_message``, ``post_audit``, ``dry_run_ping``.
        channel_name: Target channel name from discord_instance_bindings.yaml.
        message_content: Text content to post (max 2000 chars; must not contain credentials).
        runtime_id: Which runtime bot identity to use (``openclaw`` / ``hermes``).
        operator_approved: Must be True for live execution (dry_run=False).
        operator_approval_statement: Required for live execution.
        expected_action_digest: Deterministic digest of (action+channel+content); must match.
        dry_run: Default True. Set False only for live execution with approval.
        timeout_seconds: Discord API request timeout.
    """

    vault = Path(vault_root).resolve()
    normalized_action = str(action or "").strip().lower()
    normalized_content = _norm(message_content)
    session_id = _sha256(f"{normalized_action}:{channel_name}:{normalized_content}")[:20]
    bindings = _load_bindings(vault)
    blockers: list[str] = []

    if normalized_action not in _ALLOWED_ACTIONS:
        blockers.append(f"action_not_permitted:{normalized_action}")

    content_digest = _sha256(
        f"{normalized_action}:{channel_name or ''}:{normalized_content}"
    )[:32]
    if expected_action_digest and expected_action_digest != content_digest:
        blockers.append("action_digest_mismatch")

    channel_entry: dict[str, Any] | None = None
    channel_class: str | None = None
    channel_id: str | None = None

    if channel_name:
        channel_entry = _channel_info(bindings, channel_name)
        if channel_entry is None:
            blockers.append(f"channel_not_found_in_bindings:{channel_name}")
        else:
            channel_class = str(channel_entry.get("channel_class") or "")
            channel_id = str(channel_entry.get("id") or "")
            if not channel_entry.get("bound"):
                blockers.append(f"channel_not_bound:{channel_name}")
            if channel_class not in _SAFE_CHANNEL_CLASSES:
                blockers.append(f"channel_class_not_permitted:{channel_class}")
            runtime_lower = runtime_id.lower()
            posting_eligible = [
                str(r).lower() for r in (channel_entry.get("posting_eligible_runtimes") or [])
            ]
            if posting_eligible and runtime_lower not in posting_eligible:
                blockers.append(f"runtime_not_eligible_to_post:{runtime_id}:{channel_name}")
    else:
        blockers.append("channel_name_required")

    if not dry_run and not operator_approved:
        blockers.append("operator_approved_required_for_live_discord_call")
    if not dry_run and not _norm(operator_approval_statement):
        blockers.append("operator_approval_statement_required_for_live_execution")
    if not normalized_content and normalized_action == "post_message":
        blockers.append("message_content_required_for_post_message")

    env_ref = _CREDENTIAL_ENV_REFS.get(runtime_id.lower(), _CREDENTIAL_ENV_REFS["default"])
    token_present = bool(os.environ.get(env_ref))
    if not dry_run and not token_present:
        blockers.append(f"discord_bot_token_missing:{env_ref}")

    evidence_path = _write_evidence(
        vault,
        session_id=session_id,
        action=normalized_action,
        channel_name=channel_name,
        channel_class=channel_class,
        dry_run=dry_run,
        operator_approved=operator_approved,
        call_result=None,
        blocked_reasons=blockers,
    )

    if blockers:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "status": STATUS_BLOCKED,
            "generated_at_utc": _now_utc(),
            "vault_root": str(vault),
            "dry_run": dry_run,
            "session_id": session_id,
            "action": normalized_action,
            "channel_name": channel_name,
            "channel_class": channel_class,
            "channel_id_present": bool(channel_id),
            "runtime_id": runtime_id,
            "credential_env_ref": env_ref,
            "credential_value_displayed": False,
            "discord_api_called": False,
            "operator_approved": operator_approved,
            "action_digest": content_digest,
            "evidence_path": evidence_path,
            "blocked_reasons": list(dict.fromkeys(blockers)),
        }

    call_result: dict[str, Any] | None = None
    discord_api_called = False

    if not dry_run and operator_approved and normalized_action in {"post_message", "post_audit"}:
        bot_token = os.environ[env_ref]
        post_content = normalized_content or f"[ChaseOS Studio Chat Discord control — {normalized_action}]"
        call_result = _post_discord_message(
            channel_id=str(channel_id),
            content=post_content,
            bot_token=bot_token,
            timeout=timeout_seconds,
        )
        discord_api_called = True
        _write_evidence(
            vault,
            session_id=session_id,
            action=normalized_action,
            channel_name=channel_name,
            channel_class=channel_class,
            dry_run=dry_run,
            operator_approved=operator_approved,
            call_result=call_result,
            blocked_reasons=[],
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS_DRY if dry_run else STATUS_EXECUTED,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "dry_run": dry_run,
        "session_id": session_id,
        "action": normalized_action,
        "channel_name": channel_name,
        "channel_class": channel_class,
        "channel_id_present": bool(channel_id),
        "runtime_id": runtime_id,
        "credential_env_ref": env_ref,
        "credential_value_displayed": False,
        "discord_api_called": discord_api_called,
        "operator_approved": operator_approved,
        "action_digest": content_digest,
        "call_result": call_result or {"performed": False, "dry_run": dry_run},
        "evidence_path": evidence_path,
        "blocked_reasons": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "authority": {
            "discord_api_call_allowed_with_approval": True,
            "credential_value_display_allowed": False,
            "token_value_returned": False,
            "direct_call_from_studio_allowed": False,
            "canonical_mutation_allowed": False,
            "runtime_task_claim_allowed": False,
        },
        "warnings": [
            "Discord token is read from env reference only; value is never returned or logged.",
            "Only audit/alert/debug/docs/runtime-chat channel classes are permitted.",
            "Dry-run default: set dry_run=False and operator_approved=True for live execution.",
        ],
    }


def get_discord_bindings_status(vault_root: str | Path) -> dict[str, Any]:
    """Return a status summary of the discord_instance_bindings.yaml without exposing IDs unnecessarily."""
    vault = Path(vault_root).resolve()
    bindings = _load_bindings(vault)
    if not bindings:
        return {
            "ok": False,
            "bindings_found": False,
            "path": BINDINGS_PATH,
            "message": "discord_instance_bindings.yaml not found or empty",
        }
    server = bindings.get("server") or {}
    runtimes = bindings.get("runtimes") or {}
    primary = bindings.get("primary_channels") or {}
    supplemental = bindings.get("supplemental_channels") or {}
    bound_primary = [k for k, v in primary.items() if isinstance(v, dict) and v.get("bound")]
    bound_supplemental = [k for k, v in supplemental.items() if isinstance(v, dict) and v.get("bound")]
    return {
        "ok": True,
        "bindings_found": True,
        "schema_version": bindings.get("schema_version"),
        "server_name": server.get("name"),
        "runtimes": list(runtimes.keys()),
        "primary_channels_count": len(primary),
        "supplemental_channels_count": len(supplemental),
        "bound_primary_channels": bound_primary,
        "bound_supplemental_channels": bound_supplemental,
        "hermes_lane_present": bindings.get("hermes_discord_lane_present", False),
        "hermes_execution_enabled": bindings.get("hermes_execution_via_discord_enabled", False),
        "default_unmapped_policy": bindings.get("default_unmapped_policy", "deny"),
        "credential_values_displayed": False,
    }
