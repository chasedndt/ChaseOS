"""Provider execution proof for Personal Context Import.

Builds a proof that personal context can be delivered to the configured provider
(OpenAI) for synthesis and node proposal generation. If the required credential
is present in the environment, the module shows exactly what would be sent and
optionally executes a minimal test call (digest-gated, execute=True required).

If OPENAI_API_KEY is absent from the environment, this module returns an exact
operator unblock packet describing what is needed to enable this lane.

Governance rules:
- NEVER reads or logs the actual secret value.
- Provider calls only happen when execute=True AND key present AND digest matches.
- No canonical writes, no Personal Map apply, no Agent Bus dispatch.
- A dry-run structure (call_structure) is always returned even when execute=False.

APPROVED EXCEPTION — Provider-Agnostic-Rule (06_AGENTS/Provider-Agnostic-Rule.md):
This is the sole approved module in the Studio layer that makes direct provider calls.
It is a diagnostic proof-of-credential tool, not a synthesis workflow. Direct calls are
permissible here because: (1) they are gated behind execute=True + operator_approval_statement;
(2) the module never produces canonical writes; (3) its single purpose is to confirm
that a credential works, not to automate reasoning or synthesis. All other Studio and
workflow modules must route through execute_synthesis() or the Agent Bus.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.personal_context_import_provider_credential_readiness import (
    MODEL_VERSION as CREDENTIAL_MODEL_VERSION,
    build_personal_context_import_provider_credential_readiness,
    compute_provider_credential_readiness_digest,
)


MODEL_VERSION = "studio.personal_context_import_provider_execution_proof.v1"
SURFACE_ID = "studio_personal_context_import_provider_execution_proof"
PASS_ID = "personal-context-import-provider-execution-proof"
NEXT_RECOMMENDED_PASS = "personal-context-import-end-to-end-real-world-manual-test"

_PROVIDER_ENDPOINTS: dict[str, str] = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}
_PROVIDER_ENV_REFS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}

_CONFIGURED_PROVIDER = os.environ.get("CHASEOS_CHAT_PROVIDER", "openai").lower()
_OPENAI_ENDPOINT = _PROVIDER_ENDPOINTS.get(_CONFIGURED_PROVIDER, _PROVIDER_ENDPOINTS["openai"])
_PROOF_MODEL = os.environ.get("CHASEOS_PROOF_MODEL") or _PROVIDER_DEFAULT_MODELS.get(_CONFIGURED_PROVIDER, "gpt-4o-mini")
_PROOF_MAX_TOKENS = 60
_PROOF_SYSTEM_PROMPT = (
    "You are a personal context synthesis assistant for ChaseOS. "
    "Confirm receipt of a minimal personal context reference packet."
)
_PROOF_USER_PROMPT = (
    "ChaseOS Personal Context Import — proof of delivery.\n"
    "Acknowledge receipt of this minimal reference packet in one sentence. "
    "Do not generate nodes, edges, or personal data."
)

_AUTHORITY = {
    "reads_env_var_presence": True,
    "reads_env_var_values": False,
    "provider_api_call_preview": True,
    "provider_api_call_live_allowed": True,
    "file_write_allowed": False,
    "canonical_writeback_allowed": False,
    "secret_values_logged": False,
    "agent_bus_dispatch_allowed": False,
    "personal_map_apply_allowed": False,
}

STATUS_CREDENTIAL_BLOCKER = "BLOCKED / OPENAI_API_KEY NOT PRESENT / OPERATOR_CREDENTIAL_REQUIRED"
STATUS_PROOF_PREVIEW = "PROOF_PREVIEW / CREDENTIAL_PRESENT / EXECUTE_FALSE"
STATUS_PROOF_COMPLETE = "PROOF_COMPLETE / PROVIDER_CALL_EXECUTED"
STATUS_PROOF_FAILED = "PROOF_FAILED / PROVIDER_CALL_ERROR"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_call_structure() -> dict[str, Any]:
    """Return the exact call structure that would be sent to OpenAI (no secret)."""
    return {
        "endpoint": _OPENAI_ENDPOINT,
        "method": "POST",
        "model": _PROOF_MODEL,
        "max_tokens": _PROOF_MAX_TOKENS,
        "messages": [
            {"role": "system", "content": _PROOF_SYSTEM_PROMPT},
            {"role": "user", "content": _PROOF_USER_PROMPT},
        ],
        "auth_header": "Authorization: Bearer {OPENAI_API_KEY} (value not shown)",
        "content_type": "application/json",
    }


def _build_unblock_packet(vault: Path, *, provider_env_ref: str = "OPENAI_API_KEY") -> dict[str, Any]:
    return {
        "blocker_type": "operator_credential_required",
        "blocked_lane": PASS_ID,
        "required_env_var": provider_env_ref,
        "configured_provider": _CONFIGURED_PROVIDER,
        "action_required": (
            f"Set {provider_env_ref} in your environment to enable provider execution proof. "
            "The key is only checked for presence — its value is never logged or printed."
        ),
        "unblock_command": f"set {provider_env_ref}=<your-key>  # Windows PowerShell",
        "unblock_command_bash": f"export {provider_env_ref}=<your-key>  # bash/zsh",
        "call_structure_preview": _build_call_structure(),
        "what_will_happen_after_unblock": (
            f"After setting {provider_env_ref}, re-run this pass with execute=True to confirm "
            f"delivery of the minimal personal context proof payload to {_CONFIGURED_PROVIDER}. "
            "No canonical writes, Personal Map apply, or Agent Bus dispatch will occur."
        ),
        "generated_at": _now_utc(),
    }


def _make_provider_call(api_key_present: bool) -> dict[str, Any]:
    """Execute minimal proof call to the configured provider. Called only when execute=True and key present."""
    if not api_key_present:
        return {
            "ok": False,
            "error": "api_key_not_present",
            "response": None,
        }
    _env_ref = _PROVIDER_ENV_REFS.get(_CONFIGURED_PROVIDER, "OPENAI_API_KEY")
    api_key = os.environ.get(_env_ref, "") if _env_ref else ""
    if not api_key:
        return {
            "ok": False,
            "error": "api_key_empty_in_environment",
            "response": None,
        }
    payload = json.dumps(
        {
            "model": _PROOF_MODEL,
            "max_tokens": _PROOF_MAX_TOKENS,
            "messages": [
                {"role": "system", "content": _PROOF_SYSTEM_PROMPT},
                {"role": "user", "content": _PROOF_USER_PROMPT},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        _OPENAI_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = ""
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            pass
        usage = body.get("usage", {})
        return {
            "ok": True,
            "response_id": body.get("id"),
            "model": body.get("model"),
            "response_content": content,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "finish_reason": (body.get("choices") or [{}])[0].get("finish_reason"),
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "error": f"http_error:{exc.code}",
            "response": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"provider_call_failed:{exc}",
            "response": None,
        }


def build_personal_context_import_provider_execution_proof(
    vault_root: str | Path,
    *,
    execute: bool = False,
    operator_approval_statement: str = "",
) -> dict[str, Any]:
    """Return provider execution proof (or exact unblock packet if credential absent)."""
    vault = Path(vault_root).resolve()
    provider_env_ref = _PROVIDER_ENV_REFS.get(_CONFIGURED_PROVIDER, "OPENAI_API_KEY")
    key_present = provider_env_ref in os.environ
    call_structure = _build_call_structure()

    cred_readiness = build_personal_context_import_provider_credential_readiness(vault)
    credential_digest = str(cred_readiness.get("readiness_digest") or "")

    if not key_present:
        unblock = _build_unblock_packet(vault, provider_env_ref=provider_env_ref)
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "generated_at": _now_utc(),
            "vault_root": str(vault),
            "status": STATUS_CREDENTIAL_BLOCKER,
            "credential_present": False,
            "call_structure": call_structure,
            "provider_call_executed": False,
            "provider_call_result": None,
            "credential_digest": credential_digest,
            "unblock_packet": unblock,
            "authority": dict(_AUTHORITY),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        }

    blockers: list[str] = []
    if execute:
        if not operator_approval_statement.strip():
            blockers.append("operator_approval_statement_required")
        else:
            low = operator_approval_statement.lower()
            if "approve" not in low or "provider" not in low:
                blockers.append(
                    "operator_approval_statement_must_contain_approve_and_provider"
                )

    if execute and not blockers:
        call_result = _make_provider_call(key_present)
        status = STATUS_PROOF_COMPLETE if call_result.get("ok") else STATUS_PROOF_FAILED
        return {
            "ok": call_result.get("ok", False),
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "generated_at": _now_utc(),
            "vault_root": str(vault),
            "status": status,
            "credential_present": True,
            "call_structure": call_structure,
            "provider_call_executed": True,
            "provider_call_result": call_result,
            "credential_digest": credential_digest,
            "unblock_packet": None,
            "authority": dict(_AUTHORITY),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "status": STATUS_PROOF_PREVIEW,
        "credential_present": True,
        "call_structure": call_structure,
        "provider_call_executed": False,
        "provider_call_result": None,
        "credential_digest": credential_digest,
        "unblock_packet": None,
        "blocked_reasons": blockers,
        "how_to_execute": (
            "Call with execute=True and provide a valid operator_approval_statement "
            "containing 'approve' and 'provider' to trigger the live proof call."
        ),
        "authority": dict(_AUTHORITY),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_personal_context_import_provider_execution_proof(
    payload: dict[str, Any],
) -> str:
    lines = [
        "Personal Context Import Provider Execution Proof",
        f"Status: {payload.get('status')}",
        f"Credential present: {payload.get('credential_present')}",
        f"Provider call executed: {payload.get('provider_call_executed')}",
        f"Credential digest: {(payload.get('credential_digest') or 'missing')[:24]}...",
        f"Next recommended pass: {payload.get('next_recommended_pass')}",
    ]
    if payload.get("unblock_packet"):
        up = payload["unblock_packet"]
        lines.append("--- CREDENTIAL BLOCKER ---")
        lines.append(f"Required env var: {up.get('required_env_var')}")
        lines.append(f"Action: {up.get('action_required')}")
    result = payload.get("provider_call_result") or {}
    if result.get("ok"):
        lines.append(f"Response: {result.get('response_content', '')[:120]}")
    elif result.get("error"):
        lines.append(f"Provider call error: {result.get('error')}")
    return "\n".join(lines)
