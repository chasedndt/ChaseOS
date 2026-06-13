"""Provider credential readiness for Personal Context Import.

Checks whether required provider secret references (OPENAI_API_KEY) are present
in the current environment. Does NOT read, print, log, or expose secret values —
only their presence or absence. Computes a stable credential readiness digest from
presence state only, supporting a digest-gated approval flow.

Does NOT call any provider API, write any files, or perform any live mutation.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.personal_context_import_provider_credential_readiness.v1"
SURFACE_ID = "studio_personal_context_import_provider_credential_readiness"
PASS_ID = "personal-context-import-provider-credential-readiness"
APPROVAL_CLASS = "provider_credential_readiness"
NEXT_RECOMMENDED_PASS = "personal-context-import-provider-execution-proof"
APPROVAL_ROOT = Path(
    "runtime/studio/approvals/personal-context-import/provider-credential"
)

_PROVIDERS: tuple[dict[str, str], ...] = (
    {
        "provider_id": "openai",
        "env_var": "OPENAI_API_KEY",
        "role": "personal_context_synthesis",
        "description": "OpenAI API — personal context synthesis and node proposal generation",
        "required": True,
    },
)

_AUTHORITY = {
    "reads_env_var_presence": True,
    "reads_env_var_values": False,
    "provider_api_call_allowed": False,
    "file_write_allowed": False,
    "canonical_writeback_allowed": False,
    "secret_values_read": False,
    "agent_bus_dispatch_allowed": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check_provider(provider: dict[str, str]) -> dict[str, Any]:
    env_var = provider["env_var"]
    present = env_var in os.environ
    return {
        "provider_id": provider["provider_id"],
        "env_var": env_var,
        "role": provider["role"],
        "description": provider["description"],
        "required": provider.get("required", False),
        "credential_present": present,
        "status": "credential_present" if present else "credential_missing",
    }


def compute_provider_credential_readiness_digest(
    provider_states: list[dict[str, Any]],
) -> str:
    """Stable digest over provider credential presence state (no values)."""
    items = sorted(
        [
            {
                "provider_id": s["provider_id"],
                "env_var": s["env_var"],
                "credential_present": s["credential_present"],
                "required": s["required"],
            }
            for s in provider_states
        ],
        key=lambda x: x["provider_id"],
    )
    return _sha256_text(_canonical_json({"schema": MODEL_VERSION, "provider_states": items}))


def build_personal_context_import_provider_credential_readiness(
    vault_root: str | Path,
) -> dict[str, Any]:
    """Return provider credential readiness (presence check only, no values)."""
    vault = Path(vault_root).resolve()

    provider_states = [_check_provider(p) for p in _PROVIDERS]
    readiness_digest = compute_provider_credential_readiness_digest(provider_states)

    required_present = all(
        s["credential_present"] for s in provider_states if s["required"]
    )
    all_present = all(s["credential_present"] for s in provider_states)
    missing_required = [
        s["provider_id"] for s in provider_states if s["required"] and not s["credential_present"]
    ]
    missing_optional = [
        s["provider_id"] for s in provider_states if not s["required"] and not s["credential_present"]
    ]

    if required_present and all_present:
        status = "all_credentials_present"
    elif required_present:
        status = "required_credentials_present_optional_missing"
    elif not missing_required:
        status = "no_required_credentials_configured"
    else:
        status = f"credential_missing_{','.join(missing_required)}"

    service = StudioService(vault)
    pending_approval_ids: list[str] = []
    try:
        for req in service.list_pending():
            meta = req.action_spec.metadata or {}
            if meta.get("provider_credential_readiness_approval") is True:
                pending_approval_ids.append(req.approval_id)
    except Exception:
        pass

    blockers: list[str] = []
    if missing_required:
        for pid in missing_required:
            env_var = next(
                (p["env_var"] for p in _PROVIDERS if p["provider_id"] == pid), pid
            )
            blockers.append(
                f"required_credential_missing:{pid} (set {env_var} in environment)"
            )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "status": status,
        "readiness_digest": readiness_digest,
        "provider_states": provider_states,
        "required_credentials_present": required_present,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "credential_blockers": blockers,
        "pending_approval_ids": pending_approval_ids,
        "approval_class": APPROVAL_CLASS,
        "can_request_approval": True,
        "unblock_instructions": [
            f"Set {p['env_var']} in your environment to unblock provider {p['provider_id']}"
            for p in _PROVIDERS
            if not _check_provider(p)["credential_present"] and p.get("required")
        ],
        "authority": dict(_AUTHORITY),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def request_personal_context_import_provider_credential_readiness_approval(
    vault_root: str | Path,
    *,
    expected_readiness_digest: str,
    operator_note: str = "",
    operator_id: str = "studio-operator",
) -> dict[str, Any]:
    """Queue a provider credential readiness approval (exact-digest-gated)."""
    vault = Path(vault_root).resolve()
    readiness = build_personal_context_import_provider_credential_readiness(vault)
    actual_digest = str(readiness.get("readiness_digest") or "")
    expected = str(expected_readiness_digest or "").strip()

    blockers: list[str] = []
    if not expected:
        blockers.append("expected_readiness_digest_required")
    elif actual_digest != expected:
        blockers.append("readiness_digest_mismatch")

    if blockers:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "vault_root": str(vault),
            "approval_queued": False,
            "blockers": blockers,
            "actual_readiness_digest": actual_digest,
            "expected_readiness_digest": expected,
        }

    service = StudioService(vault)
    for req in service.list_pending():
        meta = req.action_spec.metadata or {}
        if (
            meta.get("provider_credential_readiness_approval") is True
            and meta.get("provider_credential_readiness_digest") == actual_digest
        ):
            return {
                "ok": True,
                "surface": SURFACE_ID,
                "model_version": MODEL_VERSION,
                "generated_at": _now_utc(),
                "vault_root": str(vault),
                "approval_queued": False,
                "approval_already_exists": True,
                "approval_id": req.approval_id,
                "readiness_digest": actual_digest,
                "blockers": [],
            }

    content_payload = {
        "record_type": "personal_context_import_provider_credential_readiness_approval",
        "schema_version": MODEL_VERSION,
        "readiness_digest": actual_digest,
        "provider_states": readiness.get("provider_states"),
        "required_credentials_present": readiness.get("required_credentials_present"),
        "missing_required": readiness.get("missing_required"),
        "source_text_included": False,
        "secret_values_read": False,
        "canonical_writeback_allowed": False,
        "future_executor_requires_matching_digest": True,
        "operator_note": operator_note,
    }
    target_path = (
        APPROVAL_ROOT / f"credential-readiness-{actual_digest[:16]}.json"
    ).as_posix()
    spec = ActionSpec(
        action_type="create_file",
        target_path=target_path,
        content=json.dumps(content_payload, indent=2, sort_keys=True) + "\n",
        metadata={
            "provider_credential_readiness_approval": True,
            "provider_credential_readiness_digest": actual_digest,
            "source_surface": SURFACE_ID,
            "required_approval_class": APPROVAL_CLASS,
            "provider_api_call_allowed": False,
            "secret_values_read": False,
            "canonical_writeback_allowed": False,
        },
        submitted_by=operator_id,
        note=operator_note or "Provider credential readiness approval (digest-gated).",
    )
    req = service.queue_for_approval(spec)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "approval_queued": True,
        "approval_already_exists": False,
        "approval_id": req.approval_id,
        "readiness_digest": actual_digest,
        "blockers": [],
    }


def format_personal_context_import_provider_credential_readiness(
    payload: dict[str, Any],
) -> str:
    lines = [
        "Personal Context Import Provider Credential Readiness",
        f"Status: {payload.get('status')}",
        f"Readiness digest: {(payload.get('readiness_digest') or 'missing')[:24]}...",
        f"Required credentials present: {payload.get('required_credentials_present')}",
        f"Missing required: {payload.get('missing_required')}",
        f"Can request approval: {payload.get('can_request_approval')}",
        f"Next recommended pass: {payload.get('next_recommended_pass')}",
    ]
    blockers = payload.get("credential_blockers") or []
    if blockers:
        lines.append("Credential blockers:")
        lines.extend(f"- {b}" for b in blockers)
    return "\n".join(lines)
