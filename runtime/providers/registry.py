"""runtime.providers.registry — Phase 9 Runtime Shell provider/model registry.

Read-only inventory layer built from existing setup-state and setup-profile truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path(__file__).resolve().parents[1]
SETUP_REGISTRY = RUNTIME_DIR / "setup_registry.json"
SETUP_PROVIDER_PROFILES = RUNTIME_DIR / "setup_provider_profiles.json"
SETUP_STATE_PATH = RUNTIME_DIR / "setup_state.json"
SETUP_STATE_EXAMPLE = RUNTIME_DIR / "setup_state.example.json"

_PROVIDER_REQUIRED_FIELDS = {"id", "label", "setup_kind", "status"}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_setup_state() -> dict[str, Any]:
    path = SETUP_STATE_PATH if SETUP_STATE_PATH.exists() else SETUP_STATE_EXAMPLE
    return _load_json(path)


def load_provider_catalog() -> list[dict[str, Any]]:
    payload = _load_json(SETUP_REGISTRY)
    providers = payload.get("providers", [])
    if not isinstance(providers, list):
        raise ValueError("setup_registry providers must be a list")

    validated: list[dict[str, Any]] = []
    for entry in providers:
        if not isinstance(entry, dict):
            raise ValueError("provider registry entries must be objects")
        missing = sorted(field for field in _PROVIDER_REQUIRED_FIELDS if field not in entry)
        if missing:
            raise ValueError(f"provider registry entry missing required fields: {missing}")
        validated.append(dict(entry))
    return validated


def load_provider_profiles() -> dict[str, Any]:
    payload = _load_json(SETUP_PROVIDER_PROFILES)
    if not isinstance(payload, dict):
        raise ValueError("provider profiles must be a mapping")
    return payload


def _probe_state_validation(profile: dict[str, Any], state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    missing: list[str] = []
    for check_name in profile.get("validation_checks", []) or []:
        passed = bool(state.get(check_name, False))
        checks.append({"check": check_name, "passed": passed})
        if not passed:
            missing.append(check_name)
    return checks, missing


def list_provider_status() -> list[dict[str, Any]]:
    catalog = load_provider_catalog()
    profiles = load_provider_profiles()
    state = _load_setup_state().get("providers", {})

    results: list[dict[str, Any]] = []
    for entry in catalog:
        provider_id = str(entry["id"])
        profile = profiles.get(provider_id, {}) or {}
        provider_state = state.get(provider_id, {}) or {}
        checks, missing = _probe_state_validation(profile, provider_state)
        results.append(
            {
                "provider_id": provider_id,
                "label": entry.get("label"),
                "configured": bool(provider_state.get("configured", False)),
                "default_model": provider_state.get("default_model"),
                "reasoning_policy": provider_state.get("reasoning_policy"),
                "secret_reference_present": bool(provider_state.get("secret_reference_present", False)),
                "checks": checks,
                "missing": missing,
                "valid": bool(provider_state.get("configured", False)) and not missing,
                "notes": entry.get("notes"),
            }
        )
    return results


def list_model_bindings() -> list[dict[str, Any]]:
    catalog = load_provider_catalog()
    state = _load_setup_state().get("providers", {})

    bindings: list[dict[str, Any]] = []
    for entry in catalog:
        provider_id = str(entry["id"])
        provider_state = state.get(provider_id, {}) or {}
        model_id = (
            provider_state.get("default_model")
            or provider_state.get("model_id_or_registry")
            or provider_state.get("endpoint_url")
            or f"unconfigured:{provider_id}"
        )
        bindings.append(
            {
                "provider_id": provider_id,
                "provider_label": entry.get("label"),
                "model_id": model_id,
                "configured": bool(provider_state.get("configured", False)),
                "primary": bool(provider_state.get("configured", False) and provider_state.get("default_model")),
                "reasoning_policy": provider_state.get("reasoning_policy"),
            }
        )
    return bindings
