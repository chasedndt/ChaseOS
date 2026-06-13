"""Phase 11 ChaseOS credential setup/status UX.

Exposes a ChaseOS-safe credential setup and status surface so future users
can configure provider keys (OpenAI, Anthropic, Discord, etc.) inside
ChaseOS without committing or displaying secrets.

Design principles:
- Never returns, displays, logs, or persists raw secret values.
- Only references credential env var names and metadata.
- Actual secrets stay in the OS/user environment or a local ignored file.
- Provides a CLI path for operators to verify readiness without seeing values.
- Shows a setup guide pointing to .env.example for key placement.
- Status check is read-only; setup write requires explicit operator action.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.phase11_credential_setup_ux.v1"
SURFACE_ID = "phase11_credential_setup_ux"
PASS_ID = "phase11-credential-setup-ux"
STATUS = "COMPLETE / READ-ONLY STATUS / SETUP GUIDE AVAILABLE"
NEXT_RECOMMENDED_PASS = "phase11-p0-manual-ui-verification-with-live-env"

ENV_EXAMPLE_PATH = ".env.example"
SETUP_METADATA_PATH = ".chaseos/credential_setup_metadata.json"

# routing_path values:
#   "runtime_path"        — only needed when Studio calls a runtime directly (not for Chat→Hermes)
#   "direct_provider"     — needed when Studio calls a provider API without a runtime
#   "runtime_owned"       — owned by the runtime in its own environment (e.g. Hermes' WSL env)
#                           Studio does NOT need this; the runtime reads it from its own env
#   "connector"           — needed by a specific connector (capture, Discord posting, etc.)
#
# For the primary Chat path (Chat→Hermes via Agent Bus), only "runtime_owned" credentials are
# needed — and they live in Hermes' WSL environment, not the Studio/Windows environment.
# OPENAI_API_KEY is only needed for the direct-provider fallback path.

_CREDENTIAL_REGISTRY: list[dict[str, Any]] = [
    {
        "key_id": "openai_provider",
        "label": "OpenAI API Key",
        "env_var": "OPENAI_API_KEY",
        "purpose": "Direct provider call from Studio to OpenAI (fallback path only — runtime path does NOT require this key)",
        "required_for": ["direct_provider_call", "studio_openai_fallback"],
        "routing_path": "direct_provider",
        "routing_note": (
            "NOT required for the primary Chat path. Chat→Hermes→Agent Bus works without this key. "
            "Only needed if Studio makes a direct OpenAI call bypassing all runtimes."
        ),
        "setup_guide": "Get your key from https://platform.openai.com/api-keys. Add OPENAI_API_KEY=sk-... to your Windows/process environment or .env file (not committed).",
        "env_example_entry": "OPENAI_API_KEY=test-key-your-key-here",
        "secret_format_hint": "Starts with 'sk-'",
        "value_display_allowed": False,
    },
    {
        "key_id": "openclaw_discord",
        "label": "OpenClaw Discord Bot Token",
        "env_var": "OPENCLAW_DISCORD_BOT_TOKEN",
        "purpose": "OpenClaw Discord runtime lane — posting to audit/alert channels",
        "required_for": ["discord_control_openclaw"],
        "routing_path": "runtime_owned",
        "routing_note": "Owned by OpenClaw runtime (Windows). OpenClaw reads this from its own process environment.",
        "setup_guide": "Get from the Discord Developer Portal → Applications → Your Bot → Token. Add OPENCLAW_DISCORD_BOT_TOKEN=... to OpenClaw's environment. Never share this token.",
        "env_example_entry": "OPENCLAW_DISCORD_BOT_TOKEN=your-bot-token-here",
        "secret_format_hint": "Long alphanumeric string from Discord developer portal",
        "value_display_allowed": False,
    },
    {
        "key_id": "hermes_discord",
        "label": "Hermes Discord Bot Token",
        "env_var": "HERMES_DISCORD_BOT_TOKEN",
        "purpose": "Hermes Discord runtime lane — posting to hermes-chat and alerts",
        "required_for": ["discord_control_hermes"],
        "routing_path": "runtime_owned",
        "routing_note": "Owned by Hermes runtime (WSL). Hermes reads this from its WSL environment.",
        "setup_guide": "Get from Discord Developer Portal for the Hermes bot account. In WSL: export HERMES_DISCORD_BOT_TOKEN=... (add to ~/.bashrc).",
        "env_example_entry": "HERMES_DISCORD_BOT_TOKEN=your-hermes-bot-token-here",
        "secret_format_hint": "Long alphanumeric string from Discord developer portal",
        "value_display_allowed": False,
    },
    {
        "key_id": "perplexity_api",
        "label": "Perplexity API Key",
        "env_var": "PERPLEXITY_API_KEY",
        "purpose": "Capture from Perplexity research queries",
        "required_for": ["capture_perplexity"],
        "setup_guide": "Get from https://www.perplexity.ai/settings/api. Add PERPLEXITY_API_KEY=pplx-... to your local .env.",
        "env_example_entry": "PERPLEXITY_API_KEY=pplx-your-key-here",
        "secret_format_hint": "Starts with 'pplx-'",
        "value_display_allowed": False,
    },
    {
        "key_id": "xai_grok",
        "label": "xAI Grok API Key",
        "env_var": "XAI_API_KEY",
        "purpose": "Capture from Grok/xAI queries",
        "required_for": ["capture_grok"],
        "setup_guide": "Get from https://x.ai/api. Add XAI_API_KEY=xai-... to your local .env.",
        "env_example_entry": "XAI_API_KEY=xai-your-key-here",
        "secret_format_hint": "Starts with 'xai-'",
        "value_display_allowed": False,
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_short(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _check_env_var(env_var: str) -> dict[str, Any]:
    """Check if an env var is set. Never returns the value."""
    raw = os.environ.get(env_var)
    present = bool(raw)
    length = len(raw) if raw else 0
    return {
        "env_var": env_var,
        "present": present,
        "value_length": length if present else 0,
        "value_displayed": False,
        "value_returned": False,
        "non_empty": bool(raw and raw.strip()),
    }


def _load_setup_metadata(vault: Path) -> dict[str, Any]:
    path = vault / SETUP_METADATA_PATH
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_setup_metadata(
    vault: Path,
    *,
    key_id: str,
    env_var: str,
    setup_confirmed_by: str,
    note: str,
) -> str:
    path = vault / SETUP_METADATA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    entries = dict(existing.get("entries") or {})
    entries[key_id] = {
        "key_id": key_id,
        "env_var": env_var,
        "setup_confirmed_by": setup_confirmed_by,
        "note": note,
        "confirmed_at_utc": _now_utc(),
        "value_stored": False,
        "value_displayed": False,
    }
    path.write_text(
        json.dumps(
            {
                "schema_version": "phase11_credential_setup_metadata.v1",
                "updated_at_utc": _now_utc(),
                "secret_values_stored": False,
                "entries": entries,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    try:
        return path.relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def get_credential_status(
    vault_root: str | Path,
    *,
    key_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return a status summary of all credential references.

    Never returns credential values. Shows only presence/length/env_var.
    """

    vault = Path(vault_root).resolve()
    target_registry = _CREDENTIAL_REGISTRY
    if key_ids:
        target_registry = [c for c in _CREDENTIAL_REGISTRY if c["key_id"] in key_ids]

    setup_metadata = _load_setup_metadata(vault)
    env_example_exists = (vault / ENV_EXAMPLE_PATH).exists()

    entries: list[dict[str, Any]] = []
    # For the runtime path (Chat→Hermes), nothing in Studio is "critical" — Hermes owns its keys.
    # For the direct-provider path only, OPENAI_API_KEY is critical.
    _direct_provider_critical = {"openai_provider"}
    runtime_path_missing: list[str] = []   # keys the runtime needs (not Studio's problem)
    direct_provider_missing: list[str] = []  # keys Studio needs for direct-provider fallback

    for cred in target_registry:
        env_var = cred["env_var"]
        routing_path = cred.get("routing_path", "unknown")
        env_status = _check_env_var(env_var)
        meta_entry = (setup_metadata.get("entries") or {}).get(cred["key_id"]) or {}
        # "critical" now means: Studio cannot perform its direct-provider fallback without it.
        # Runtime-owned keys are never critical from Studio's perspective.
        is_direct_provider_critical = (
            cred["key_id"] in _direct_provider_critical and routing_path == "direct_provider"
        )
        if not env_status["present"]:
            if routing_path == "direct_provider":
                direct_provider_missing.append(env_var)
            elif routing_path == "runtime_owned":
                runtime_path_missing.append(env_var)

        entries.append({
            "key_id": cred["key_id"],
            "label": cred["label"],
            "env_var": env_var,
            "purpose": cred["purpose"],
            "required_for": cred["required_for"],
            "routing_path": routing_path,
            "routing_note": cred.get("routing_note", ""),
            "present_in_environment": env_status["present"],
            "value_length": env_status["value_length"],
            "non_empty": env_status["non_empty"],
            "value_displayed": False,
            "value_returned": False,
            "setup_confirmed": bool(meta_entry.get("confirmed_at_utc")),
            "setup_confirmed_at": meta_entry.get("confirmed_at_utc"),
            "is_direct_provider_critical": is_direct_provider_critical,
            "setup_guide_available": True,
        })

    runtime_path_ready = True  # Studio→Hermes via Agent Bus needs no Studio-side key
    direct_provider_ready = not bool(direct_provider_missing)

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "routing_model": {
            "primary_path": "runtime_dispatch",
            "primary_path_description": (
                "Studio Chat → Agent Bus task for Hermes → Hermes processes using its own configured "
                "model/provider → result posted back → Studio shows result card. "
                "OPENAI_API_KEY is NOT required for this path."
            ),
            "primary_path_ready": runtime_path_ready,
            "fallback_path": "direct_provider",
            "fallback_path_description": (
                "Studio Chat → OpenAI API directly (bypasses all runtimes). "
                "Requires OPENAI_API_KEY in Studio/Windows environment. Use only when Hermes is unavailable."
            ),
            "fallback_path_ready": direct_provider_ready,
            "openai_api_key_required_for_primary": False,
            "openai_api_key_required_for_fallback": True,
        },
        "summary": {
            "total_credentials": len(entries),
            "present_count": sum(1 for e in entries if e["present_in_environment"]),
            "missing_count": sum(1 for e in entries if not e["present_in_environment"]),
            "direct_provider_missing": direct_provider_missing,
            "runtime_owned_missing_in_studio_env": runtime_path_missing,
            "runtime_path_ready": runtime_path_ready,
            "direct_provider_ready": direct_provider_ready,
            "env_example_exists": env_example_exists,
            "setup_metadata_path": SETUP_METADATA_PATH,
            "value_display_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "credentials": entries,
        "setup_guide": {
            "runtime_path_setup": (
                "For Chat→Hermes runtime path: ensure Hermes is running in WSL with its own "
                "configured model/provider credentials. Studio does not read or hold any Hermes credentials."
            ),
            "direct_provider_setup": (
                "For direct OpenAI fallback: set OPENAI_API_KEY in Windows/Studio environment. "
                "Already in environment if `present_in_environment=true` above."
            ),
            "step_1": "For runtime path (primary): start Hermes in WSL with its own configured credentials.",
            "step_2": "For direct provider (fallback): set OPENAI_API_KEY in Windows env (may already be set).",
            "step_3": "Verify runtime path: chaseos chat hermes-status",
            "step_4": "Verify direct provider: python -m runtime.studio.phase11_credential_setup_ux status",
            "env_example_path": ENV_EXAMPLE_PATH,
            "secrets_policy": "Never commit real API keys. Never share them in chat or logs.",
        },
        "authority": {
            "read_only": True,
            "credential_value_read_allowed": False,
            "credential_value_display_allowed": False,
            "credential_value_stored": False,
            "env_file_write_allowed": False,
            "setup_metadata_write_allowed": True,
        },
    }


def confirm_credential_setup(
    vault_root: str | Path,
    *,
    key_id: str,
    setup_confirmed_by: str = "operator",
    note: str = "",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Mark a credential as setup-confirmed in local metadata (no value stored).

    This only records that the operator has confirmed the key is configured.
    It does NOT store, verify, or touch the actual credential value.
    """

    vault = Path(vault_root).resolve()
    cred = next((c for c in _CREDENTIAL_REGISTRY if c["key_id"] == key_id), None)
    if cred is None:
        return {
            "ok": False,
            "blocked_reasons": [f"key_id_not_found:{key_id}"],
            "value_stored": False,
        }

    env_status = _check_env_var(cred["env_var"])
    if not env_status["present"]:
        return {
            "ok": False,
            "blocked_reasons": [f"env_var_not_present_cannot_confirm:{cred['env_var']}"],
            "value_stored": False,
            "hint": f"Set {cred['env_var']} in your environment first, then re-run confirm.",
        }

    metadata_path: str | None = None
    if not dry_run:
        metadata_path = _write_setup_metadata(
            vault,
            key_id=key_id,
            env_var=cred["env_var"],
            setup_confirmed_by=setup_confirmed_by,
            note=note,
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "key_id": key_id,
        "env_var": cred["env_var"],
        "env_var_present": True,
        "setup_confirmed": not dry_run,
        "dry_run": dry_run,
        "metadata_path": metadata_path,
        "value_stored": False,
        "value_displayed": False,
        "generated_at_utc": _now_utc(),
    }


def get_setup_guide(key_id: str | None = None) -> dict[str, Any]:
    """Return setup instructions for one or all credentials."""
    if key_id:
        cred = next((c for c in _CREDENTIAL_REGISTRY if c["key_id"] == key_id), None)
        if cred is None:
            return {"ok": False, "error": f"key_id_not_found:{key_id}"}
        return {
            "ok": True,
            "key_id": cred["key_id"],
            "label": cred["label"],
            "env_var": cred["env_var"],
            "purpose": cred["purpose"],
            "setup_guide": cred["setup_guide"],
            "env_example_entry": cred["env_example_entry"],
            "secret_format_hint": cred["secret_format_hint"],
            "value_display_allowed": False,
        }
    return {
        "ok": True,
        "credentials": [
            {
                "key_id": c["key_id"],
                "label": c["label"],
                "env_var": c["env_var"],
                "setup_guide": c["setup_guide"],
                "env_example_entry": c["env_example_entry"],
            }
            for c in _CREDENTIAL_REGISTRY
        ],
    }


def ensure_env_example(vault_root: str | Path) -> dict[str, Any]:
    """Ensure .env.example exists with all credential template entries (no values)."""
    vault = Path(vault_root).resolve()
    path = vault / ENV_EXAMPLE_PATH

    lines = [
        "# ChaseOS credential template — copy to .env and fill in real values.",
        "# NEVER commit .env to version control.",
        "# Each line below is a reference only; add your actual key after the =",
        "",
    ]
    for cred in _CREDENTIAL_REGISTRY:
        lines.append(f"# {cred['label']} — {cred['purpose']}")
        lines.append(cred["env_example_entry"])
        lines.append("")

    content = "\n".join(lines)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing.strip() == content.strip():
            return {"ok": True, "action": "already_current", "path": ENV_EXAMPLE_PATH}
        backup = path.with_suffix(".example.bak")
        backup.write_text(existing, encoding="utf-8")

    path.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "action": "written",
        "path": ENV_EXAMPLE_PATH,
        "secret_values_stored": False,
        "entries_count": len(_CREDENTIAL_REGISTRY),
    }


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="ChaseOS credential setup/status UX")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("status", help="Show credential status (no values displayed)")
    confirm_p = sub.add_parser("confirm", help="Mark a credential as configured")
    confirm_p.add_argument("--key-id", required=True)
    confirm_p.add_argument("--confirmed-by", default="operator")
    confirm_p.add_argument("--note", default="")
    confirm_p.add_argument("--live", action="store_true", help="Write confirmation (default is dry-run)")
    sub.add_parser("guide", help="Show setup guide for all credentials")
    guide_p = sub.add_parser("guide-key", help="Show setup guide for one credential")
    guide_p.add_argument("--key-id", required=True)
    sub.add_parser("ensure-env-example", help="Ensure .env.example exists")

    args = parser.parse_args()
    vault = Path.cwd()

    if args.cmd == "status":
        result = get_credential_status(vault)
        print(json.dumps(result, indent=2))
    elif args.cmd == "confirm":
        result = confirm_credential_setup(
            vault,
            key_id=args.key_id,
            setup_confirmed_by=args.confirmed_by,
            note=args.note,
            dry_run=not args.live,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "guide":
        print(json.dumps(get_setup_guide(), indent=2))
    elif args.cmd == "guide-key":
        print(json.dumps(get_setup_guide(args.key_id), indent=2))
    elif args.cmd == "ensure-env-example":
        print(json.dumps(ensure_env_example(vault), indent=2))
    else:
        parser.print_help()
        sys.exit(1)
