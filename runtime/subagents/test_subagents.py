from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from runtime.subagents.activation import SubAgentActivationManager
from runtime.subagents.models import SubAgentPreset, SubAgentValidationError
from runtime.subagents.output import validate_structured_markdown_output
from runtime.subagents.policies import (
    evaluate_memory_write,
    evaluate_tool_request,
)
from runtime.subagents.registry import SubAgentRegistry
from runtime.subagents.router import SubAgentRuntimeRouter, build_runtime_availability


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_registry_loads_default_presets() -> None:
    registry = SubAgentRegistry(vault_root=VAULT_ROOT)
    presets = registry.list_presets()
    preset_ids = {preset.id for preset in presets}

    assert len(presets) >= 9
    assert {
        "ceo-orchestrator",
        "engineering-worker",
        "marketing-content-worker",
        "memory-documentation-worker",
        "product-analysis-worker",
        "qa-testing-worker",
        "research-worker",
        "site-ops-worker",
        "venture-ops-worker",
    }.issubset(preset_ids)
    assert registry.validate_all() == ()


def test_registry_rejects_secret_shaped_allowed_tool() -> None:
    registry = SubAgentRegistry(vault_root=VAULT_ROOT)
    preset = registry.get_preset("research-worker")
    data = preset.to_dict()
    data["runtimePreferences"] = list(preset.runtime_preferences)
    data["tools"]["allowed"] = ["credentials.readRaw"]

    with pytest.raises(SubAgentValidationError):
        SubAgentPreset.from_mapping(data)


def test_router_blocks_openhuman_and_selects_supported_runtime() -> None:
    registry = SubAgentRegistry(vault_root=VAULT_ROOT)
    preset = registry.get_preset("research-worker")
    preset = replace(preset, runtime_preferences=("OpenHuman", "HermesAgent", "OpenClaw"))
    router = SubAgentRuntimeRouter(
        availability={
            "OpenHuman": {"registered": False, "retired": True},
            "Hermes": {"registered": True, "retired": False},
            "OpenClaw": {"registered": True, "retired": False},
        }
    )

    route = router.select_runtime(preset)

    assert route.route_status == "selected"
    assert route.selected_runtime == "HermesAgent"
    assert route.selected_bus_name == "Hermes"
    assert "OpenHuman" in route.unavailable_preferences
    assert route.blocked_reasons


def test_runtime_availability_reads_real_capability_manifests() -> None:
    availability = build_runtime_availability(VAULT_ROOT)

    assert availability["Hermes"]["registered"] is True
    assert availability["OpenClaw"]["registered"] is True
    assert "operator-briefing" in availability["OpenClaw"]["task_types"]
    assert availability["OpenHuman"]["registered"] is False
    assert availability["OpenHuman"]["retired"] is True


def test_activation_context_is_task_scoped_and_non_daemon() -> None:
    registry = SubAgentRegistry(vault_root=VAULT_ROOT)
    preset = registry.get_preset("site-ops-worker")
    router = SubAgentRuntimeRouter(
        availability={
            "OpenClaw": {"registered": True, "retired": False},
            "Hermes": {"registered": True, "retired": False},
        }
    )
    manager = SubAgentActivationManager(vault_root=VAULT_ROOT, router=router)

    context = manager.build_activation_context(
        preset,
        task_id="task-site-audit",
        objective="Review a site profile without making external changes.",
        mode="site_ops",
        input_payload={"site_profile": "example"},
    )
    checkpoint = manager.checkpoint(context, summary="Collected site profile facts.")
    cleaned = manager.teardown(context)

    assert context.state == "activated"
    assert context.selected_runtime == "OpenClaw"
    assert context.is_task_scoped is True
    assert context.daemon_started is False
    assert context.compute_budget.max_parallel_workers == 1
    assert checkpoint["context_persisted"] is False
    assert cleaned.state == "cleaned_up"


def test_policy_decisions_denied_approval_and_allowed() -> None:
    registry = SubAgentRegistry(vault_root=VAULT_ROOT)
    preset = registry.get_preset("site-ops-worker")

    assert evaluate_tool_request(preset, "site.profile.read").allowed
    assert evaluate_tool_request(preset, "site.publish.live").approval_required
    assert evaluate_tool_request(preset, "credentials.readRaw").decision == "deny"
    assert evaluate_memory_write(preset, "07_LOGS/SiteOps-Approvals").approval_required
    assert evaluate_memory_write(preset, "00_HOME/Now.md").decision == "deny"


def test_structured_markdown_output_contract() -> None:
    registry = SubAgentRegistry(vault_root=VAULT_ROOT)
    preset = registry.get_preset("qa-testing-worker")
    markdown = """
# Summary
QA pass completed.

# Findings
No blocking issue.

# Tests Run
pytest runtime/subagents/test_subagents.py -q

# Residual Risk
No live runtime execution was attempted.
"""

    ok, missing = validate_structured_markdown_output(markdown, preset.output.required_sections)

    assert ok is True
    assert missing == ()
