"""ChaseOS setup CLI foothold.

Phase 9/10 operator setup surface seed.
This begins the provider/integration/menu family without yet handling secrets writes.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import shutil

try:
    from runtime.local_env import load_chaseos_env
except ModuleNotFoundError:  # pragma: no cover - direct script compatibility
    from local_env import load_chaseos_env  # type: ignore

try:
    from runtime.setup_state import (
        ensure_setup_state,
        load_setup_state,
        update_integration_state,
        update_provider_state,
        validate_setup_state_credential_boundary,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script compatibility
    from setup_state import ensure_setup_state, load_setup_state, update_integration_state, update_provider_state, validate_setup_state_credential_boundary  # type: ignore

try:
    from runtime.chaseos_gate import check_gateway_write_target, check_runtime_operation
except ModuleNotFoundError:  # pragma: no cover - direct script compatibility
    from chaseos_gate import check_gateway_write_target, check_runtime_operation  # type: ignore


RUNTIME_DIR = Path(__file__).resolve().parent
SETUP_REGISTRY = RUNTIME_DIR / "setup_registry.json"
SETUP_PROVIDER_PROFILES = RUNTIME_DIR / "setup_provider_profiles.json"
SETUP_STATE_EXAMPLE = RUNTIME_DIR / "setup_state.example.json"
SETUP_INIT_MANIFEST = RUNTIME_DIR / "setup_init_manifest.json"


SETUP_INIT_TEMPLATES = {
    "soul": "# SOUL.md\n\n> Define the identity, tone, and operating posture of this ChaseOS instance.\n\n## Identity\n- Name:\n- Role:\n- Voice:\n\n## Boundaries\n-\n\n## Notes\n-\n",
    "now": "# Now\n\n## Current Sprint Focus\n-\n\n## Active Priorities\n-\n\n## Open Loops\n-\n",
    "dashboard": "# Dashboard\n\n## System Status\n- Setup state: seeded\n- Runtime lanes: openclaw, hermes\n\n## Quick Links\n- [[Now]]\n- [[Operating-System]]\n- [[Vault-Map]]\n",
    "operating_system": "# Operating System\n\n## Domains\n- Define the major domains this ChaseOS instance will operate across.\n\n## Rules\n-\n",
    "principles": "# Principles\n\n## Core Principles\n-\n\n## Decision Rules\n-\n",
    "agent_registry": "# Agent Registry\n\n| Agent | Surface | Role | Trust Tier | Status |\n|---|---|---|---|---|\n| OpenClaw | runtime | bounded execution | active-lane | seeded |\n| Hermes | runtime | bounded coordination | shadow-lane | seeded |\n",
    "tool_map": "# Tool Map\n\n## Providers\n- Claude\n- OpenAI\n- Local OSS\n- n8n\n\n## Integrations\n- Discord\n- Telegram\n- Slack\n",
    "knowledge_index": "# Knowledge Index\n\n## Domains\n- Add domain knowledge roots here.\n\n## Notes\n- This is the top-level operator-facing index for knowledge surfaces.\n",
    "build_logs_index": "# Build Logs Index\n\n## Recent Sessions\n- Add links to important build logs here.\n\n## Notes\n- Build logs remain the canonical record of implementation passes.\n",
    "documentation_history_index": "# Documentation History Index\n\n## Major Passes\n- Add links to major architecture/docs passes here.\n\n## Notes\n- Use this to track meaningful structural/documentation evolution.\n",
    "operator_brief_index": "# Operator Brief Index\n\n## Briefings\n- Add operator briefing links here.\n\n## Notes\n- This is the operator-facing index for structured briefing outputs.\n",
    "system_status": "# System Status\n\n## Current Setup Posture\n- Setup init: seeded\n- Runtime lanes: openclaw, hermes\n- Providers: claude, openai, local_oss, n8n\n- Integrations: discord, telegram, slack\n\n## Notes\n- Expand this into a richer operator summary surface over time.\n",
    "setup_instructions": "# Setup Instructions\n\n## Recommended First Actions\n1. Review `SOUL.md`\n2. Review `00_HOME/Operating-System.md`\n3. Fill in `00_HOME/Now.md`\n4. Confirm runtime/provider/integration setup\n\n## Notes\n- This file backs setup/init onboarding instructions for CLI and future interface surfaces.\n",
    "runtime_registry": "# Runtime Registry\n\n| Runtime | Role | Status | Notes |\n|---|---|---|---|\n| openclaw | active bounded execution | seeded | Primary active runtime lane |\n| hermes | bounded coordination/shadow | seeded | Secondary runtime lane |\n",
    "operating_system_map": "# Operating System Map\n\n## Core OS Surfaces\n- Link the primary operating-system-level notes and control surfaces here.\n\n## Notes\n- This is an OS-level map surface for top-level system navigation.\n",
    "runtime_surfaces": "# Runtime Surfaces\n\n## Runtime Control Surfaces\n- Link runtime-facing operational notes and registry surfaces here.\n\n## Notes\n- This is an OS-level runtime navigation surface.\n",
    "setup_surfaces": "# Setup Surfaces\n\n## Setup and Onboarding Surfaces\n- Link setup-facing notes, instructions, and validation surfaces here.\n\n## Notes\n- This is an OS-level setup navigation surface.\n",
    "folder_build_logs_index": "# Build Logs Index\n\n## Build Logs\n- Add links to major build logs in this folder.\n\n## Notes\n- This is the folder-local canonical index for build-log navigation.\n",
    "folder_agent_activity_index": "# Agent Activity Index\n\n## Agent Activity\n- Add links to important runtime/agent activity records in this folder.\n\n## Notes\n- This is the folder-local canonical index for agent activity navigation.\n",
    "folder_operator_briefs_index": "# Operator Briefs Index\n\n## Operator Briefs\n- Add links to structured operator brief outputs here.\n\n## Notes\n- This is the folder-local canonical index for operator briefing outputs.\n",
    "folder_daily_index": "# Daily Index\n\n## Daily Notes\n- Add links to daily notes here.\n\n## Notes\n- This is the folder-local canonical index for daily-note navigation.\n",
    "folder_knowledge_index": "# Knowledge Index\n\n## Domain Roots\n- Add links to the major knowledge domain indexes here.\n\n## Notes\n- This is the folder-local canonical knowledge index surface.\n",
}


def load_setup_registry() -> dict:
    return json.loads(SETUP_REGISTRY.read_text(encoding="utf-8"))


def load_provider_profiles() -> dict:
    return json.loads(SETUP_PROVIDER_PROFILES.read_text(encoding="utf-8"))


def load_setup_state_example() -> dict:
    return json.loads(SETUP_STATE_EXAMPLE.read_text(encoding="utf-8"))


def load_setup_init_manifest() -> dict:
    return json.loads(SETUP_INIT_MANIFEST.read_text(encoding="utf-8"))


def _parse_patch_items(items: list[str]) -> dict:
    patch: dict = {}
    for item in items:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        value = value.strip()
        if value.lower() == "true":
            patch[key.strip()] = True
        elif value.lower() == "false":
            patch[key.strip()] = False
        else:
            patch[key.strip()] = value
    return patch


def _print_entries(title: str, entries: list[dict], as_json: bool) -> int:
    if as_json:
        print(json.dumps(entries, indent=2))
        return 0

    print(title)
    for entry in entries:
        print()
        print(f"- id: {entry.get('id')}")
        print(f"  label: {entry.get('label')}")
        print(f"  setup_kind: {entry.get('setup_kind')}")
        print(f"  status: {entry.get('status')}")
        if entry.get('notes'):
            print(f"  notes: {entry.get('notes')}")
    return 0


def _print_setup_error(message: str, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": message}, indent=2))
    else:
        print(f"ERROR: {message}")
    return 1


def _check_setup_operation(operation: str, as_json: bool) -> bool:
    allowed, reason = check_runtime_operation(operation)
    if allowed:
        return True
    _print_setup_error(reason, as_json)
    return False


def _print_provider_detail(entry: dict, profile: dict | None, as_json: bool) -> int:
    payload = dict(entry)
    if profile:
        payload["required_inputs"] = profile.get("required_inputs", [])
        payload["validation_checks"] = profile.get("validation_checks", [])
        payload["secret_reference_kind"] = profile.get("secret_reference_kind")
        payload["profile_notes"] = profile.get("notes")

    if as_json:
        print(json.dumps(payload, indent=2))
        return 0

    print("ChaseOS Setup Provider")
    print(f"  id: {payload.get('id')}")
    print(f"  label: {payload.get('label')}")
    print(f"  setup_kind: {payload.get('setup_kind')}")
    print(f"  status: {payload.get('status')}")
    if payload.get('notes'):
        print(f"  notes: {payload.get('notes')}")
    if payload.get('required_inputs'):
        print(f"  required_inputs: {', '.join(payload['required_inputs'])}")
    if payload.get('validation_checks'):
        print(f"  validation_checks: {', '.join(payload['validation_checks'])}")
    if payload.get('secret_reference_kind'):
        print(f"  secret_reference_kind: {payload.get('secret_reference_kind')}")
    if payload.get('profile_notes'):
        print(f"  profile_notes: {payload.get('profile_notes')}")
    return 0


def _wizard_provider_patch(target_id: str, profile: dict | None) -> dict:
    patch = {"configured": True}
    for item in (profile.get("required_inputs", []) if profile else []):
        if item == "default_model":
            patch["default_model"] = f"set-by-wizard:{target_id}"
            patch["model_selected"] = True
        elif item == "reasoning_policy":
            patch["reasoning_policy"] = "set-by-wizard"
        elif item == "api_key" or item == "api_key_or_supported_auth":
            patch["secret_reference_present"] = True
            patch["secret_reference_kind"] = "env-var-or-local-secret-ref"
            patch["secret_reference_target"] = f"SET_{target_id.upper()}_SECRET_REF"
            patch["auth_present"] = True
            patch["api_key_present"] = True
        elif item == "endpoint_url":
            patch["endpoint_present"] = True
            patch["endpoint_url"] = "http://localhost:11434/v1"
        elif item == "model_id_or_registry":
            patch["model_target_present"] = True
        elif item == "launcher_mode":
            patch["launcher_mode"] = "set-by-wizard"
        elif item == "base_url":
            patch["base_url_present"] = True
        elif item == "auth_secret_or_token":
            patch["secret_reference_present"] = True
            patch["secret_reference_kind"] = "env-var-or-local-secret-ref"
            patch["secret_reference_target"] = f"SET_{target_id.upper()}_SECRET_REF"
            patch["auth_present"] = True
        elif item == "workflow_scope":
            patch["workflow_scope"] = "set-by-wizard"
    return patch


def _print_provider_wizard(target_id: str, profile: dict | None, as_json: bool) -> int:
    wizard = {
        "provider_id": target_id,
        "steps": [
            "Collect required provider inputs",
            "Validate local config presence",
            "Confirm default model/runtime posture",
            "Write safe non-secret setup state"
        ],
        "required_inputs": profile.get("required_inputs", []) if profile else [],
        "validation_checks": profile.get("validation_checks", []) if profile else [],
        "proposed_patch": _wizard_provider_patch(target_id, profile),
    }
    if as_json:
        print(json.dumps(wizard, indent=2))
        return 0

    print(f"ChaseOS Setup Provider Wizard: {target_id}")
    for index, step in enumerate(wizard["steps"], start=1):
        print(f"{index}. {step}")
    if wizard["required_inputs"]:
        print(f"required_inputs: {', '.join(wizard['required_inputs'])}")
    if wizard["validation_checks"]:
        print(f"validation_checks: {', '.join(wizard['validation_checks'])}")
    print(f"proposed_patch: {wizard['proposed_patch']}")
    return 0


def _probe_http_endpoint(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return {
                "reachable": True,
                "status_code": response.getcode(),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "reachable": True,
            "status_code": exc.code,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "reachable": False,
            "status_code": None,
            "error": str(exc),
        }


def _probe_secret_reference(kind: str | None, target: str | None) -> dict:
    if not kind or not target:
        return {"checked": False, "exists": False, "error": "missing_reference_target"}

    if kind == "env-var" or kind == "env-var-or-local-secret-ref":
        value = os.environ.get(target)
        if value:
            return {"checked": True, "exists": True, "source": "env-var", "error": None}
        if kind == "env-var":
            return {"checked": True, "exists": False, "source": "env-var", "error": "env_var_missing"}

    candidate = Path(target)
    if candidate.exists():
        return {"checked": True, "exists": True, "source": "local-path", "error": None}

    return {"checked": True, "exists": False, "source": kind, "error": "reference_not_found"}


def _secret_reference_target_is_placeholder(target: str | None) -> bool:
    value = str(target or "").strip()
    return bool(value) and value.startswith("SET_") and value.endswith("_SECRET_REF")


def _provider_stop_aliases(payload: dict) -> dict:
    secret_reference_blocked = bool(
        payload.get("secret_reference_target_is_placeholder")
        or (
            payload.get("secret_reference_target")
            and not payload.get("secret_reference_resolvable")
        )
    )
    return {
        "safe_to_call_update_goal_complete": False,
        "no_safe_autonomous_completion_pass_available": secret_reference_blocked,
        "update_goal_allowed": False,
        "next_operator_action_id": (
            "openai_secret_reference"
            if payload.get("provider_id") == "openai" and secret_reference_blocked
            else "provider-live-probe-after-secret-reference"
            if payload.get("valid")
            else "resolve_setup_validation_blockers"
        ),
        "next_recommended_pass": (
            "operator-provide-openai-secret-reference"
            if payload.get("provider_id") == "openai" and secret_reference_blocked
            else "provider-live-probe-after-secret-reference"
            if payload.get("valid")
            else "resolve-setup-validation-blockers"
        ),
    }


def _setup_validation_stop_aliases(providers: list[dict], integrations: list[dict]) -> dict:
    openai = next((item for item in providers if item.get("provider_id") == "openai"), None)
    if openai:
        next_operator_action_id = openai.get("next_operator_action_id")
        next_recommended_pass = openai.get("next_recommended_pass")
        no_safe = bool(openai.get("no_safe_autonomous_completion_pass_available"))
    else:
        invalid = [
            item
            for item in providers + integrations
            if not item.get("valid")
        ]
        next_operator_action_id = "resolve_setup_validation_blockers" if invalid else "provider-live-probe-after-secret-reference"
        next_recommended_pass = "resolve-setup-validation-blockers" if invalid else "provider-live-probe-after-secret-reference"
        no_safe = bool(invalid)
    return {
        "safe_to_call_update_goal_complete": False,
        "no_safe_autonomous_completion_pass_available": no_safe,
        "update_goal_allowed": False,
        "next_operator_action_id": next_operator_action_id,
        "next_recommended_pass": next_recommended_pass,
    }


def _validate_provider(provider_id: str, profile: dict | None, state: dict | None) -> dict:
    state = state or {}
    checks = []
    missing = []
    for check_name in (profile.get("validation_checks", []) if profile else []):
        passed = bool(state.get(check_name, False))
        checks.append({"check": check_name, "passed": passed})
        if not passed:
            missing.append(check_name)
    configured = bool(state.get("configured", False))
    secret_reference_kind = state.get("secret_reference_kind") or (
        profile.get("secret_reference_kind") if profile else None
    )
    secret_reference_probe = None
    if state.get("secret_reference_present"):
        secret_reference_probe = _probe_secret_reference(
            str(secret_reference_kind) if secret_reference_kind else None,
            state.get("secret_reference_target"),
        )
        secret_reference_resolved = bool(secret_reference_probe.get("exists"))
        checks.append({"check": "secret_reference_resolvable", "passed": secret_reference_resolved})
        if not secret_reference_resolved:
            missing.append("secret_reference_resolvable")
    payload = {
        "provider_id": provider_id,
        "configured": configured,
        "checks": checks,
        "missing": missing,
        "secret_reference_kind": secret_reference_kind,
        "secret_reference_target": state.get("secret_reference_target"),
        "secret_reference_target_is_placeholder": _secret_reference_target_is_placeholder(
            state.get("secret_reference_target")
        ),
        "secret_reference_resolvable": bool(secret_reference_probe and secret_reference_probe.get("exists")),
        "secret_reference_probe_source": (
            secret_reference_probe.get("source") if secret_reference_probe is not None else None
        ),
        "secret_reference_probe_error": (
            secret_reference_probe.get("error") if secret_reference_probe is not None else None
        ),
        "valid": configured and not missing,
    }

    if secret_reference_probe is not None:
        payload["secret_reference_probe"] = secret_reference_probe

    if profile and profile.get("probe_kind") == "http-endpoint" and state.get("endpoint_url"):
        payload["endpoint_probe"] = _probe_http_endpoint(str(state.get("endpoint_url")))

    payload.update(_provider_stop_aliases(payload))

    return payload


def _validate_integration(entry: dict, state: dict | None) -> dict:
    state = state or {}
    integration_id = entry.get("id")
    checks = []
    missing = []
    for check_name in entry.get("validation_checks", ["configured", "binding_present"]):
        passed = bool(state.get(check_name, False))
        checks.append({"check": check_name, "passed": passed})
        if not passed:
            missing.append(check_name)

    payload = {
        "integration_id": integration_id,
        "configured": bool(state.get("configured", False)),
        "binding_present": bool(state.get("binding_present", False)),
        "checks": checks,
        "missing": missing,
        "secret_reference_kind": entry.get("secret_reference_kind"),
        "secret_reference_target": state.get("secret_reference_target"),
        "valid": not missing,
    }

    if state.get("secret_reference_present"):
        secret_reference_probe = _probe_secret_reference(
            str(state.get("secret_reference_kind") or entry.get("secret_reference_kind")),
            state.get("secret_reference_target"),
        )
        secret_reference_resolved = bool(secret_reference_probe.get("exists"))
        payload["secret_reference_probe"] = secret_reference_probe
        payload["checks"].append({"check": "secret_reference_resolvable", "passed": secret_reference_resolved})
        if not secret_reference_resolved:
            payload["missing"].append("secret_reference_resolvable")
            payload["valid"] = False

    return payload


def _print_validation_result(title: str, payload: dict | list[dict], as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, indent=2))
        if isinstance(payload, list):
            return 0 if all(item.get("valid") for item in payload) else 1
        return 0 if payload.get("valid") else 1

    print(title)
    if isinstance(payload, list):
        for item in payload:
            print()
            identifier = item.get("provider_id") or item.get("integration_id") or item.get("id")
            print(f"- target: {identifier}")
            print(f"  valid: {item.get('valid')}")
            if item.get("missing"):
                print(f"  missing: {', '.join(item['missing'])}")
            if item.get("endpoint_probe"):
                print(f"  endpoint_probe: {item['endpoint_probe']}")
            if item.get("secret_reference_probe"):
                print(f"  secret_reference_probe: {item['secret_reference_probe']}")
        return 0 if all(item.get("valid") for item in payload) else 1

    identifier = payload.get("provider_id") or payload.get("integration_id") or payload.get("id")
    print(f"{title}: {identifier}")
    print(f"  valid: {payload.get('valid')}")
    if payload.get("missing"):
        print(f"  missing: {', '.join(payload['missing'])}")
    if payload.get("endpoint_probe"):
        print(f"  endpoint_probe: {payload['endpoint_probe']}")
    if payload.get("secret_reference_probe"):
        print(f"  secret_reference_probe: {payload['secret_reference_probe']}")
    return 0 if payload.get("valid") else 1


def cmd_provider(args: argparse.Namespace) -> int:
    registry = load_setup_registry()
    providers = registry.get("providers", [])
    profiles = load_provider_profiles()
    state = load_setup_state().get("providers", {})
    if args.setup_command == "list":
        return _print_entries("ChaseOS Setup Providers", providers, as_json=args.json)
    if args.setup_command == "show":
        for entry in providers:
            if entry.get("id") == args.target_id:
                return _print_provider_detail(entry, profiles.get(args.target_id), as_json=args.json)
        print(f"No provider found for id: {args.target_id}")
        return 1
    if args.setup_command == "wizard":
        if not args.target_id:
            print("Provider wizard requires a provider id")
            return 1
        if getattr(args, "apply", False):
            if not _check_setup_operation("setup.provider.apply", args.json):
                return 1
            ensure_setup_state()
            patch = _wizard_provider_patch(args.target_id, profiles.get(args.target_id))
            try:
                path = update_provider_state(args.target_id, patch)
            except ValueError as exc:
                return _print_setup_error(str(exc), args.json)
            if args.json:
                print(json.dumps({"applied": True, "path": str(path), "provider_id": args.target_id, "patch": patch}, indent=2))
                return 0
            print(f"Applied provider wizard -> {path}")
            print(f"provider_id: {args.target_id}")
            print(f"patch: {patch}")
            return 0
        return _print_provider_wizard(args.target_id, profiles.get(args.target_id), as_json=args.json)
    if args.setup_command == "validate":
        if not args.target_id:
            payload = [_validate_provider(entry.get("id"), profiles.get(entry.get("id")), state.get(entry.get("id"))) for entry in providers]
            return _print_validation_result("ChaseOS Setup Provider Validation", payload, as_json=args.json)
        return _print_validation_result(
            "ChaseOS Setup Provider Validation",
            _validate_provider(args.target_id, profiles.get(args.target_id), state.get(args.target_id)),
            as_json=args.json,
        )
    print("Provider command not implemented")
    return 0


def _wizard_integration_patch(target_id: str, entry: dict) -> dict:
    patch = {"configured": True, "binding_present": True}
    if entry.get("secret_reference_kind"):
        patch["secret_reference_present"] = True
        patch["secret_reference_kind"] = entry.get("secret_reference_kind")
        patch["secret_reference_target"] = f"SET_{target_id.upper()}_SECRET_REF"
    return patch


def cmd_integration(args: argparse.Namespace) -> int:
    registry = load_setup_registry()
    integrations = registry.get("integrations", [])
    state = load_setup_state().get("integrations", {})
    if args.setup_command == "list":
        return _print_entries("ChaseOS Setup Integrations", integrations, as_json=args.json)
    if args.setup_command == "show":
        for entry in integrations:
            if entry.get("id") == args.target_id:
                return _print_entries("ChaseOS Setup Integration", [entry], as_json=args.json)
        print(f"No integration found for id: {args.target_id}")
        return 1
    if args.setup_command == "wizard":
        if not args.target_id:
            print("Integration wizard requires an integration id")
            return 1
        for entry in integrations:
            if entry.get("id") == args.target_id:
                patch = _wizard_integration_patch(args.target_id, entry)
                if getattr(args, "apply", False):
                    if not _check_setup_operation("setup.integration.apply", args.json):
                        return 1
                    ensure_setup_state()
                    try:
                        path = update_integration_state(args.target_id, patch)
                    except ValueError as exc:
                        return _print_setup_error(str(exc), args.json)
                    if args.json:
                        print(json.dumps({"applied": True, "path": str(path), "integration_id": args.target_id, "patch": patch}, indent=2))
                        return 0
                    print(f"Applied integration wizard -> {path}")
                    print(f"integration_id: {args.target_id}")
                    print(f"patch: {patch}")
                    return 0
                if args.json:
                    print(json.dumps({"integration_id": args.target_id, "proposed_patch": patch}, indent=2))
                    return 0
                print(f"ChaseOS Setup Integration Wizard: {args.target_id}")
                print(f"proposed_patch: {patch}")
                return 0
        print(f"No integration found for id: {args.target_id}")
        return 1
    if args.setup_command == "validate":
        if not args.target_id:
            payload = [_validate_integration(entry, state.get(entry.get("id"))) for entry in integrations]
            return _print_validation_result("ChaseOS Setup Integration Validation", payload, as_json=args.json)
        for entry in integrations:
            if entry.get("id") == args.target_id:
                return _print_validation_result(
                    "ChaseOS Setup Integration Validation",
                    _validate_integration(entry, state.get(args.target_id)),
                    as_json=args.json,
                )
        print(f"No integration found for id: {args.target_id}")
        return 1
    print("Integration wizard not yet implemented")
    return 0


def _seed_missing_file(relative_path: str, template_key: str | None = None) -> dict:
    allowed, reason = check_gateway_write_target("setup_init_seed_files", relative_path)
    if not allowed:
        raise ValueError(f"setup init write target blocked: {reason}")

    target = Path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        return {"path": relative_path, "action": "kept", "reason": "already_exists"}

    example_candidate = target.with_suffix(target.suffix + ".example") if target.suffix else None
    if example_candidate and example_candidate.exists():
        shutil.copyfile(example_candidate, target)
        return {"path": relative_path, "action": "seeded", "source": str(example_candidate)}

    if template_key and template_key in SETUP_INIT_TEMPLATES:
        target.write_text(SETUP_INIT_TEMPLATES[template_key], encoding="utf-8")
        return {"path": relative_path, "action": "seeded", "source": f"template:{template_key}"}

    if target.suffix == ".json":
        target.write_text("{}\n", encoding="utf-8")
    else:
        target.write_text(f"# {target.name}\n\nSeeded by chaseos setup init.\n", encoding="utf-8")
    return {"path": relative_path, "action": "seeded", "source": "placeholder"}


def _selected_families(manifest: dict, args: argparse.Namespace) -> set[str]:
    families = manifest.get("families", {})
    selected = {family_id for family_id, meta in families.items() if meta.get("default_enabled", False)}
    if getattr(args, "include_family", None):
        selected.update(args.include_family)
    if getattr(args, "exclude_family", None):
        selected.difference_update(args.exclude_family)
    return selected


def cmd_init(args: argparse.Namespace) -> int:
    manifest = load_setup_init_manifest()
    profile_id = args.profile or "personal"
    profile = manifest.get("profiles", {}).get(profile_id)
    if not profile:
        print(f"Unknown setup init profile: {profile_id}")
        return 1
    if getattr(args, "write", False) and not _check_setup_operation("setup.init.write", args.json):
        return 1

    selected_families = _selected_families(manifest, args)

    folder_results = []
    for folder in profile.get("required_folders", []):
        allowed, reason = check_gateway_write_target("setup_init_scaffold", folder)
        if not allowed:
            return _print_setup_error(f"setup init folder blocked: {reason}", args.json)
        folder_path = Path(folder)
        exists_before = folder_path.exists()
        if getattr(args, "write", False):
            folder_path.mkdir(parents=True, exist_ok=True)
        folder_results.append({
            "path": folder,
            "exists": folder_path.exists(),
            "action": "kept" if exists_before else ("created" if getattr(args, "write", False) else "planned"),
        })

    file_results = []
    for entry in profile.get("required_files", []):
        file_path = entry.get("path") if isinstance(entry, dict) else str(entry)
        metadata = entry if isinstance(entry, dict) else {"path": file_path}
        family = metadata.get("index_scope")
        if family and family not in selected_families:
            continue
        target = Path(file_path)
        allowed, reason = check_gateway_write_target("setup_init_seed_files", file_path)
        if not allowed:
            return _print_setup_error(f"setup init file blocked: {reason}", args.json)
        exists_before = target.exists()
        result = {
            "path": file_path,
            "classification": metadata.get("classification"),
            "owner": metadata.get("owner"),
            "mode": metadata.get("mode"),
            "index_scope": metadata.get("index_scope"),
            "exists": exists_before,
            "action": "kept" if exists_before else "planned",
        }
        if getattr(args, "write", False):
            try:
                seeded = _seed_missing_file(file_path, metadata.get("template_key"))
            except ValueError as exc:
                return _print_setup_error(str(exc), args.json)
            result.update(seeded)
            result["exists"] = Path(file_path).exists()
        file_results.append(result)

    setup_instructions = [
        "Review SOUL.md",
        "Review 00_HOME/Operating-System.md",
        "Fill in 00_HOME/Now.md",
        "Confirm runtime/provider/integration setup",
    ]

    created_folders = [item["path"] for item in folder_results if item.get("action") == "created"]
    planned_folders = [item["path"] for item in folder_results if item.get("action") == "planned"]
    seeded_files = [item["path"] for item in file_results if item.get("action") == "seeded"]
    planned_files = [item["path"] for item in file_results if item.get("action") == "planned"]
    canonical_folder_local_indexes = [item["path"] for item in file_results if item.get("index_scope") == "canonical-folder-local"]
    convenience_indexes = [item["path"] for item in file_results if item.get("index_scope") == "convenience"]
    orientation_surfaces = [item["path"] for item in file_results if item.get("index_scope") == "orientation"]
    os_core_surfaces = [item["path"] for item in file_results if item.get("index_scope") == "os-core"]

    payload = {
        "profile": profile_id,
        "write": bool(getattr(args, "write", False)),
        "folders": folder_results,
        "files": file_results,
        "runtime_seeds": profile.get("runtime_seeds", []),
        "provider_targets": profile.get("provider_targets", []),
        "integration_targets": profile.get("integration_targets", []),
        "selected_families": sorted(selected_families),
        "setup_instructions": setup_instructions,
        "summary": {
            "created_folders": created_folders,
            "planned_folders": planned_folders,
            "seeded_files": seeded_files,
            "planned_files": planned_files,
            "canonical_folder_local_indexes": canonical_folder_local_indexes,
            "convenience_indexes": convenience_indexes,
            "orientation_surfaces": orientation_surfaces,
            "os_core_surfaces": os_core_surfaces,
            "follow_up_actions": setup_instructions,
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print("ChaseOS Setup Init")
    print(f"  profile: {profile_id}")
    print(f"  write: {payload['write']}")
    print(f"  folders: {len(payload['folders'])}")
    print(f"  files: {len(payload['files'])}")
    if payload.get("selected_families"):
        print(f"  selected_families: {', '.join(payload['selected_families'])}")
    if payload["runtime_seeds"]:
        print(f"  runtime_seeds: {', '.join(payload['runtime_seeds'])}")
    if payload["provider_targets"]:
        print(f"  provider_targets: {', '.join(payload['provider_targets'])}")
    if payload["integration_targets"]:
        print(f"  integration_targets: {', '.join(payload['integration_targets'])}")
    if payload["summary"].get("created_folders"):
        print("  created_folders:")
        for item in payload["summary"]["created_folders"]:
            print(f"    - {item}")
    if payload["summary"].get("seeded_files"):
        print("  seeded_files:")
        for item in payload["summary"]["seeded_files"]:
            print(f"    - {item}")
    if payload["summary"].get("planned_files"):
        print("  planned_files:")
        for item in payload["summary"]["planned_files"]:
            print(f"    - {item}")
    if payload["summary"].get("canonical_folder_local_indexes"):
        print("  canonical_folder_local_indexes:")
        for item in payload["summary"]["canonical_folder_local_indexes"]:
            print(f"    - {item}")
    if payload["summary"].get("convenience_indexes"):
        print("  convenience_indexes:")
        for item in payload["summary"]["convenience_indexes"]:
            print(f"    - {item}")
    if payload["summary"].get("orientation_surfaces"):
        print("  orientation_surfaces:")
        for item in payload["summary"]["orientation_surfaces"]:
            print(f"    - {item}")
    if payload["summary"].get("os_core_surfaces"):
        print("  os_core_surfaces:")
        for item in payload["summary"]["os_core_surfaces"]:
            print(f"    - {item}")
    if payload["setup_instructions"]:
        print("  setup_instructions:")
        for item in payload["setup_instructions"]:
            print(f"    - {item}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ensure_setup_state()
    state = load_setup_state()
    if args.json:
        print(json.dumps(state, indent=2))
        return 0

    print("ChaseOS Setup Status")
    print("Providers:")
    for provider_id, provider_state in state.get("providers", {}).items():
        print(f"- {provider_id}: configured={provider_state.get('configured')}")
    print("Integrations:")
    for integration_id, integration_state in state.get("integrations", {}).items():
        print(f"- {integration_id}: configured={integration_state.get('configured')}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    ensure_setup_state()
    registry = load_setup_registry()
    provider_profiles = load_provider_profiles()
    state = load_setup_state()
    providers = [
        _validate_provider(entry.get("id"), provider_profiles.get(entry.get("id")), state.get("providers", {}).get(entry.get("id")))
        for entry in registry.get("providers", [])
    ]
    integrations = [
        _validate_integration(entry, state.get("integrations", {}).get(entry.get("id")))
        for entry in registry.get("integrations", [])
    ]
    payload = {
        "providers": providers,
        "integrations": integrations,
        **_setup_validation_stop_aliases(providers, integrations),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0 if all(item.get("valid") for item in payload["providers"] + payload["integrations"]) else 1

    print("ChaseOS Setup Validation")
    print("Providers:")
    for item in payload["providers"]:
        print(f"- {item.get('provider_id')}: valid={item.get('valid')}")
        if item.get("missing"):
            print(f"  missing: {', '.join(item['missing'])}")
    print("Integrations:")
    for item in payload["integrations"]:
        print(f"- {item.get('integration_id')}: valid={item.get('valid')}")
        if item.get("missing"):
            print(f"  missing: {', '.join(item['missing'])}")
    return 0 if all(item.get("valid") for item in payload["providers"] + payload["integrations"]) else 1


def cmd_discord(args: argparse.Namespace) -> int:
    if args.setup_command != "validate":
        return _print_setup_error(f"Unsupported Discord setup command: {args.setup_command}", args.json)
    try:
        from runtime.discord_bindings import (
            build_discord_binding_validation,
            format_discord_binding_validation,
        )
    except ModuleNotFoundError:  # pragma: no cover - direct script compatibility
        from discord_bindings import build_discord_binding_validation, format_discord_binding_validation  # type: ignore

    vault_root = Path(args.vault_root).resolve() if getattr(args, "vault_root", None) else Path.cwd().resolve()
    payload = build_discord_binding_validation(vault_root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_discord_binding_validation(payload))
    return 0 if payload.get("valid") else 1


def _build_setup_set_dry_run(target_kind: str, target_id: str, patch: dict) -> dict:
    state = json.loads(json.dumps(load_setup_state()))
    collection_name = "providers" if target_kind == "provider" else "integrations"
    collection = state.setdefault(collection_name, {})
    before = dict(collection.get(target_id) or {})
    after = dict(before)
    after.update(patch)
    collection[target_id] = after
    validate_setup_state_credential_boundary(state)
    return {
        "ok": True,
        "surface": "chaseos_setup_state_set_dry_run",
        "dry_run": True,
        "read_only": True,
        "target_kind": target_kind,
        "target_id": target_id,
        "patch": patch,
        "patch_keys": sorted(patch),
        "target_preexisting": bool(before),
        "would_update_path": "runtime/setup_state.json",
        "writes_setup_state": False,
        "provider_calls_performed": False,
        "secret_values_read": False,
        "secret_values_visible": False,
        "candidate_values_are_reference_names_only": True,
        "authority": {
            "read_only": True,
            "writes_setup_state": False,
            "writes_vault": False,
            "provider_calls_performed": False,
            "approval_consumption_performed": False,
            "agent_bus_task_write_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def cmd_set(args: argparse.Namespace) -> int:
    patch = _parse_patch_items(args.items)
    if getattr(args, "dry_run", False):
        try:
            payload = _build_setup_set_dry_run(args.target_kind, args.target_id, patch)
        except ValueError as exc:
            return _print_setup_error(str(exc), args.json)
        if args.json:
            print(json.dumps(payload, indent=2))
            return 0
        print("ChaseOS Setup State Set Dry Run")
        print(f"target_kind: {payload['target_kind']}")
        print(f"target_id: {payload['target_id']}")
        print(f"patch_keys: {', '.join(payload['patch_keys'])}")
        print(f"would_update_path: {payload['would_update_path']}")
        print("writes_setup_state: False")
        return 0

    if not _check_setup_operation("setup.state.set", args.json):
        return 1
    ensure_setup_state()
    try:
        if args.target_kind == "provider":
            path = update_provider_state(args.target_id, patch)
        else:
            path = update_integration_state(args.target_id, patch)
    except ValueError as exc:
        return _print_setup_error(str(exc), args.json)

    if args.json:
        print(json.dumps({"updated": True, "path": str(path), "patch": patch}, indent=2))
        return 0

    print(f"Updated setup state -> {path}")
    print(f"target_kind: {args.target_kind}")
    print(f"target_id: {args.target_id}")
    print(f"patch: {patch}")
    return 0


def cmd_menu(args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps({
            "menu": [
                "Configure model/provider",
                "Configure runtime lane",
                "Configure messaging integration",
                "Validate current setup",
                "Show configured providers and integrations"
            ]
        }, indent=2))
        return 0

    print("ChaseOS Setup Menu")
    print("1. Configure model/provider")
    print("2. Configure runtime lane")
    print("3. Configure messaging integration")
    print("4. Validate current setup")
    print("5. Show configured providers and integrations")
    return 0


def cmd_path(args: argparse.Namespace) -> int:
    """Add vault .venv/Scripts to the Windows user PATH permanently."""
    import subprocess
    import sys

    vault_root = Path(getattr(args, "vault_root", None) or os.getcwd()).resolve()
    venv_scripts = (vault_root / ".venv" / "Scripts").resolve()

    if not venv_scripts.is_dir():
        msg = (
            f"No .venv/Scripts found at {venv_scripts}. "
            "Run: python -m venv .venv && pip install -e ."
        )
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": msg}))
        else:
            print(f"ERROR: {msg}")
        return 1

    venv_str = str(venv_scripts)

    # Check whether already present in the *current process* PATH
    current_entries = [
        p.strip() for p in os.environ.get("PATH", "").split(os.pathsep) if p.strip()
    ]
    try:
        already_active = any(
            Path(p).resolve() == venv_scripts for p in current_entries
        )
    except Exception:
        already_active = venv_str in current_entries

    if getattr(args, "dry_run", False):
        result = {
            "ok": True,
            "status": "dry_run",
            "already_on_process_path": already_active,
            "would_add": venv_str,
        }
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            print(f"[dry-run] Would add to Windows user PATH: {venv_str}")
            if already_active:
                print("  (already active in this terminal session)")
        return 0

    if sys.platform != "win32":
        result = {
            "ok": True,
            "status": "manual_required",
            "instruction": f'Add to your shell profile: export PATH="{venv_str}:$PATH"',
        }
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            print("Non-Windows detected. Add this to your shell profile (~/.bashrc or ~/.zshrc):")
            print(f'  export PATH="{venv_str}:$PATH"')
        return 0

    ps_script = (
        "$current = [Environment]::GetEnvironmentVariable('PATH', 'User') -split ';'"
        " | Where-Object { $_ -ne '' };"
        f" $target = '{venv_str}';"
        " if ($current -notcontains $target) {"
        "   $new = ($current + $target) -join ';';"
        "   [Environment]::SetEnvironmentVariable('PATH', $new, 'User');"
        "   Write-Output 'added'"
        " } else { Write-Output 'already_present' }"
    )

    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"exit code {proc.returncode}")
        ps_out = proc.stdout.strip()
        status = ps_out if ps_out in ("added", "already_present") else "added"
        output = {
            "ok": True,
            "status": status,
            "path": venv_str,
            "note": "Open a new terminal for the PATH change to take effect.",
        }
        if getattr(args, "json", False):
            print(json.dumps(output, indent=2))
        else:
            if status == "already_present":
                print(f"Already on user PATH: {venv_str}")
            else:
                print(f"Added to user PATH: {venv_str}")
                print("Open a new terminal window for the change to take effect.")
                print("Verify with:  where chaseos")
        return 0
    except Exception as exc:
        err = {"ok": False, "error": str(exc), "path": venv_str}
        if getattr(args, "json", False):
            print(json.dumps(err, indent=2))
        else:
            print(f"ERROR setting PATH: {exc}")
            print(f"Manual fix: add '{venv_str}' to your Windows user PATH")
            print("  Settings → System → Advanced system settings → Environment Variables → User PATH")
        return 1


def add_setup_subcommands(
    subparsers: argparse._SubParsersAction,
    *,
    root_name: str | None = "setup",
) -> argparse.ArgumentParser | None:
    if root_name is None:
        setup_parser = None
        setup_sub = subparsers
    else:
        setup_parser = subparsers.add_parser(root_name, help="Provider, integration, and onboarding setup commands")
        setup_sub = setup_parser.add_subparsers(dest="setup_mode", metavar="MODE")
        setup_sub.required = True

    init_parser = setup_sub.add_parser("init", help="Show or apply setup init scaffold plan")
    init_parser.add_argument("--profile", default="personal", help="Setup init profile")
    init_parser.add_argument("--include-family", action="append", choices=["canonical-folder-local", "convenience", "orientation", "os-core"], help="Include optional scaffold family")
    init_parser.add_argument("--exclude-family", action="append", choices=["canonical-folder-local", "convenience", "orientation", "os-core"], help="Exclude scaffold family")
    init_parser.add_argument("--write", action="store_true", help="Create missing scaffold folders/files without overwriting existing ones")
    init_parser.add_argument("--json", action="store_true", help="Print JSON output")
    init_parser.set_defaults(func=cmd_init)

    status_parser = setup_sub.add_parser("status", help="Show current setup state example")
    status_parser.add_argument("--json", action="store_true", help="Print JSON output")
    status_parser.set_defaults(func=cmd_status)

    provider_parser = setup_sub.add_parser("provider", help="Provider setup surfaces")
    provider_parser.add_argument("setup_command", choices=["list", "show", "wizard", "validate"], help="Provider setup command")
    provider_parser.add_argument("target_id", nargs="?", default=None, help="Provider id for show/wizard")
    provider_parser.add_argument("--apply", action="store_true", help="Apply wizard-proposed non-secret setup state")
    provider_parser.add_argument("--json", action="store_true", help="Print JSON output")
    provider_parser.set_defaults(func=cmd_provider)

    integration_parser = setup_sub.add_parser("integration", help="Integration setup surfaces")
    integration_parser.add_argument("setup_command", choices=["list", "show", "wizard", "validate"], help="Integration setup command")
    integration_parser.add_argument("target_id", nargs="?", default=None, help="Integration id for show/wizard")
    integration_parser.add_argument("--apply", action="store_true", help="Apply wizard-proposed non-secret setup state")
    integration_parser.add_argument("--json", action="store_true", help="Print JSON output")
    integration_parser.set_defaults(func=cmd_integration)

    discord_parser = setup_sub.add_parser("discord", help="Discord control-plane binding setup surfaces")
    discord_parser.add_argument("setup_command", choices=["validate"], help="Discord setup command")
    discord_parser.add_argument("--vault-root", default=None, metavar="PATH", help="Override vault root path")
    discord_parser.add_argument("--json", action="store_true", help="Print JSON output")
    discord_parser.set_defaults(func=cmd_discord)

    validate_parser = setup_sub.add_parser("validate", help="Validate current setup state")
    validate_parser.add_argument("--json", action="store_true", help="Print JSON output")
    validate_parser.set_defaults(func=cmd_validate)

    set_parser = setup_sub.add_parser("set", help="Update non-secret setup state flags")
    set_parser.add_argument("target_kind", choices=["provider", "integration"], help="Target kind")
    set_parser.add_argument("target_id", help="Target id")
    set_parser.add_argument("items", nargs="+", help="Patch items in key=value form")
    set_parser.add_argument("--dry-run", action="store_true", help="Preview non-secret setup state update without writing")
    set_parser.add_argument("--json", action="store_true", help="Print JSON output")
    set_parser.set_defaults(func=cmd_set)

    menu_parser = setup_sub.add_parser("menu", help="Show the setup menu")
    menu_parser.add_argument("--json", action="store_true", help="Print JSON output")
    menu_parser.set_defaults(func=cmd_menu)

    path_parser = setup_sub.add_parser(
        "path",
        help="Add vault .venv/Scripts to Windows user PATH (one-time setup)",
    )
    path_parser.add_argument("--vault-root", dest="vault_root", default=None, metavar="PATH", help="Vault root (default: cwd)")
    path_parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Show what would be added without modifying PATH")
    path_parser.add_argument("--json", action="store_true", help="Print JSON output")
    path_parser.set_defaults(func=cmd_path)

    return setup_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ChaseOS setup CLI foothold")
    subparsers = parser.add_subparsers(dest="family", required=True)
    add_setup_subcommands(subparsers, root_name=None)

    return parser


def main() -> int:
    load_chaseos_env()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
