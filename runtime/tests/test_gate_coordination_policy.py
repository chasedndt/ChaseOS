"""Focused tests for Gate-enforced coordination policy checks."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.chaseos_gate import (  # noqa: E402
    check_coordination_path,
    load_adapter_manifest,
    load_task_profile,
    load_protected_files,
    validate_manifest,
)
import runtime.chaseos_gate as gate_mod  # noqa: E402


def test_runtime_and_harness_manifests_now_include_valid_coordination_policy() -> None:
    for adapter_id in (
        "claude-harness",
        "openclaw",
        "hermes",
        "local_oss",
        "n8n-workflow",
        "openai-chat",
    ):
        manifest = load_adapter_manifest(adapter_id)
        assert manifest, f"manifest missing for {adapter_id}"
        assert validate_manifest(manifest) == []
        assert manifest["coordination_policy"]["coordination_source_of_truth"] == "runtime/agent_bus/"


def test_claude_harness_blocks_coordination_sensitive_work_outside_bus() -> None:
    allowed, reason = check_coordination_path(
        "claude-harness",
        coordination_sensitive=True,
        via_bus=False,
        target_runtime="OpenClaw",
    )

    assert allowed is False
    assert "runtime/agent_bus/" in reason


def test_openclaw_and_hermes_allow_coordination_sensitive_work_via_bus() -> None:
    for adapter_id, target_runtime in (("openclaw", "Hermes"), ("hermes", "OpenClaw")):
        allowed, reason = check_coordination_path(
            adapter_id,
            coordination_sensitive=True,
            via_bus=True,
            target_runtime=target_runtime,
        )

        assert allowed is True
        assert "allowed via runtime/agent_bus/" in reason


def test_advisory_surface_is_not_approved_for_coordination_sensitive_runtime_work() -> None:
    allowed, reason = check_coordination_path(
        "openai-chat",
        coordination_sensitive=True,
        via_bus=True,
        target_runtime="Hermes",
    )

    assert allowed is False
    assert "not approved for coordination-sensitive runtime work" in reason


def test_non_coordination_sensitive_work_does_not_require_bus_path() -> None:
    allowed, reason = check_coordination_path(
        "claude-harness",
        coordination_sensitive=False,
        via_bus=False,
    )

    assert allowed is True
    assert "not required" in reason


def test_gate_loader_fallback_without_pyyaml_for_adapter_manifest() -> None:
    with patch.object(gate_mod, "yaml", None):
        manifest = load_adapter_manifest("openclaw")

    assert manifest
    assert manifest["adapter_id"] == "openclaw"
    assert manifest["coordination_policy"]["coordination_source_of_truth"] == "runtime/agent_bus/"
    assert validate_manifest(manifest) == []


def test_gate_loader_fallback_without_pyyaml_for_task_profile_and_protected_files() -> None:
    with patch.object(gate_mod, "yaml", None):
        profile = load_task_profile("docs_pass")
        protected = load_protected_files()

    assert profile
    assert protected
    assert isinstance(protected, list)
