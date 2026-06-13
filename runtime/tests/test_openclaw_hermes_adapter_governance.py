from __future__ import annotations

import copy
import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.adapters.runtime_governance as runtime_governance
from runtime.adapters.runtime_governance import (
    APPROVED_HERMES_WORKFLOWS,
    REQUIRED_HERMES_FORBIDDEN_COMMANDS,
    build_rpgl_adapter_consumption_report,
    evaluate_runtime_adapter_governance,
    validate_runtime_adapter_governance,
)


def _load_yaml(relative_path: str) -> dict:
    return runtime_governance._load_yaml(_VAULT_ROOT / relative_path)


def _current_inputs() -> dict[str, dict]:
    return {
        "openclaw_manifest": _load_yaml("runtime/policy/adapters/openclaw.yaml"),
        "hermes_manifest": _load_yaml("runtime/policy/adapters/hermes.yaml"),
        "hermes_config": _load_yaml(".chaseos/hermes_config.yaml"),
        "openclaw_capabilities": _load_yaml("runtime/openclaw/capabilities.yaml"),
    }


def test_current_openclaw_hermes_governance_validates() -> None:
    report = validate_runtime_adapter_governance(vault_root_path=_VAULT_ROOT)

    assert report["ok"] is True
    assert report["blocking_issues"] == []
    assert report["cross_runtime"]["same_tier2_ceiling"] is True
    assert report["cross_runtime"]["both_use_agent_bus_for_runtime_coordination"] is True


def test_runtime_governance_validation_does_not_require_pyyaml(monkeypatch) -> None:
    monkeypatch.setattr(runtime_governance, "_pyyaml", None)

    report = validate_runtime_adapter_governance(vault_root_path=_VAULT_ROOT)
    capabilities = runtime_governance._load_yaml(_VAULT_ROOT / "runtime/openclaw/capabilities.yaml")

    assert report["ok"] is True
    assert report["blocking_issues"] == []
    assert capabilities["handles"][0]["task_type"] == "operator-briefing"
    assert capabilities["handles"][0]["priority"] == "primary"
    assert capabilities["max_concurrent_tasks"] == 3


def test_adapter_manifests_remain_fail_closed_for_promotion_and_external_side_effects() -> None:
    report = validate_runtime_adapter_governance(vault_root_path=_VAULT_ROOT)

    for adapter_id in ("openclaw", "hermes"):
        checks = report["adapters"][adapter_id]["checks"]
        assert checks["promotion_blocked"] is True
        assert checks["external_side_effects_blocked"] is True
        assert checks["required_denied_write_targets_present"] is True
        assert checks["protected_write_flags_blocked"] is True
        assert checks["approval_mode_manifest_bounded"] is True


def test_hermes_config_remains_bounded_and_blocks_high_risk_commands() -> None:
    report = validate_runtime_adapter_governance(vault_root_path=_VAULT_ROOT)
    hermes_config = report["runtime_configs"]["hermes"]

    assert hermes_config["status"] == "shadow-active"
    assert set(hermes_config["approved_workflows"]) == APPROVED_HERMES_WORKFLOWS
    assert hermes_config["checks"]["bounded_workflows_only"] is True
    assert hermes_config["checks"]["forbidden_commands_present"] is True
    assert hermes_config["checks"]["connectors_disabled"] is True
    assert hermes_config["checks"]["promotion_writeback_blocked"] is True

    current_config = _load_yaml(".chaseos/hermes_config.yaml")
    assert REQUIRED_HERMES_FORBIDDEN_COMMANDS.issubset(
        set(current_config["forbidden_command_families"])
    )


def test_openclaw_capability_manifest_does_not_declare_forbidden_surfaces() -> None:
    report = validate_runtime_adapter_governance(vault_root_path=_VAULT_ROOT)
    capabilities = report["runtime_configs"]["openclaw_capabilities"]

    assert capabilities["runtime"] == "openclaw"
    assert capabilities["bus_name"] == "OpenClaw"
    assert capabilities["checks"]["forbidden_capability_terms_absent"] is True
    assert capabilities["checks"]["concurrency_bounded"] is True
    assert capabilities["checks"]["priority_ceiling_bounded"] is True
    assert "operator-briefing" in capabilities["handled_task_types"]
    assert "graph-hygiene" in capabilities["handled_task_types"]
    assert "source-pack-builder" in capabilities["handled_task_types"]


def test_openclaw_manifest_declares_bounded_source_pack_builder_scope() -> None:
    report = validate_runtime_adapter_governance(vault_root_path=_VAULT_ROOT)
    manifest = report["adapters"]["openclaw"]
    current_manifest = _load_yaml("runtime/policy/adapters/openclaw.yaml")

    assert "source-pack-builder" in manifest["allowed_task_types"]
    assert current_manifest["allowed_write_targets"].get("acquisition_packs") is True
    assert current_manifest["external_side_effect_policy"]["may_call_external_apis"] == "no"
    assert current_manifest["promotion_behavior"]["autonomous_promotion"] is False


def test_adapter_governance_reports_rpgl_consumption() -> None:
    report = validate_runtime_adapter_governance(vault_root_path=_VAULT_ROOT)
    rpgl = report["rpgl_consumption"]

    assert rpgl["ok"] is True
    assert report["ok"] is True
    assert rpgl["shared_execution_adapter"]["checks"]["imports_governance_layer"] is True
    assert rpgl["shared_execution_adapter"]["checks"]["imports_route_task"] is True
    assert rpgl["shared_execution_adapter"]["checks"]["fallback_activation_after_capability_gate"] is True
    assert rpgl["shared_execution_adapter"]["checks"]["high_authority_queues_before_fallback"] is True
    assert rpgl["hermes"]["checks"]["imports_shared_execution_adapter"] is True
    assert rpgl["hermes"]["checks"]["uses_hermes_adapter_identity"] is True
    assert rpgl["hermes"]["checks"]["no_direct_provider_calls"] is True
    assert rpgl["openclaw"]["checks"]["no_direct_provider_calls"] is True
    assert rpgl["openclaw"]["checks"]["bus_dispatch_only"] is True
    assert rpgl["openclaw"]["checks"]["does_not_import_shared_synthesis_adapter"] is True


def test_rpgl_consumption_report_has_no_direct_provider_markers_for_adapters() -> None:
    report = build_rpgl_adapter_consumption_report(_VAULT_ROOT)

    assert report["ok"] is True
    assert report["hermes"]["direct_provider_markers_present"] == []
    assert report["openclaw"]["direct_provider_markers_present"] == []


def test_validator_blocks_autonomous_promotion_regression() -> None:
    inputs = copy.deepcopy(_current_inputs())
    inputs["openclaw_manifest"]["promotion_behavior"]["may_promote_to_knowledge"] = "yes"
    inputs["openclaw_manifest"]["promotion_behavior"]["autonomous_promotion"] = True

    report = evaluate_runtime_adapter_governance(**inputs)

    assert report["ok"] is False
    assert any("openclaw.promotion" in issue for issue in report["blocking_issues"])
    assert any("cross_runtime.fail_closed" in issue for issue in report["blocking_issues"])


def test_validator_blocks_hermes_shell_unblock_regression() -> None:
    inputs = copy.deepcopy(_current_inputs())
    inputs["hermes_config"]["forbidden_command_families"].remove("shell.execute")

    report = evaluate_runtime_adapter_governance(**inputs)

    assert report["ok"] is False
    assert any("hermes.config.forbidden_commands" in issue for issue in report["blocking_issues"])
