"""ChaseOS setup state helpers.

This is the first writable setup-state foothold.
It intentionally stores non-secret setup posture only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from runtime.chaseos_gate import check_gateway_write_target, find_credential_boundary_violations
except ModuleNotFoundError:  # pragma: no cover - direct script compatibility
    from chaseos_gate import check_gateway_write_target, find_credential_boundary_violations  # type: ignore


RUNTIME_DIR = Path(__file__).resolve().parent
SETUP_STATE_PATH = RUNTIME_DIR / "setup_state.json"
SETUP_STATE_EXAMPLE = RUNTIME_DIR / "setup_state.example.json"


def validate_setup_state_credential_boundary(state: dict[str, Any]) -> None:
    violations = find_credential_boundary_violations(state, prefix="setup_state")
    if violations:
        detail = "; ".join(violations)
        raise ValueError(f"Setup state credential boundary violation: {detail}")


def load_setup_state() -> dict[str, Any]:
    path = SETUP_STATE_PATH if SETUP_STATE_PATH.exists() else SETUP_STATE_EXAMPLE
    return json.loads(path.read_text(encoding="utf-8"))


def write_setup_state(state: dict[str, Any]) -> Path:
    validate_setup_state_credential_boundary(state)
    allowed, reason = check_gateway_write_target("setup_state", "runtime/setup_state.json")
    if not allowed:
        raise ValueError(f"Setup state write target blocked: {reason}")
    SETUP_STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return SETUP_STATE_PATH


def ensure_setup_state() -> Path:
    if not SETUP_STATE_PATH.exists():
        state = json.loads(SETUP_STATE_EXAMPLE.read_text(encoding="utf-8"))
        return write_setup_state(state)
    return SETUP_STATE_PATH


def update_provider_state(provider_id: str, patch: dict[str, Any]) -> Path:
    state = load_setup_state()
    providers = state.setdefault("providers", {})
    provider_state = providers.setdefault(provider_id, {})
    provider_state.update(patch)
    return write_setup_state(state)


def update_integration_state(integration_id: str, patch: dict[str, Any]) -> Path:
    state = load_setup_state()
    integrations = state.setdefault("integrations", {})
    integration_state = integrations.setdefault(integration_id, {})
    integration_state.update(patch)
    return write_setup_state(state)
