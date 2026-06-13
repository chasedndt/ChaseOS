from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.runtime_surfaces.models import RuntimeSurfaceError, RuntimeSurfaceManifest
from runtime.runtime_surfaces.policy import (
    assert_registry_policy_safe,
    build_capability_policy_index,
    capability_policy_records,
    classify_manifest_capabilities,
)
from runtime.runtime_surfaces.registry import load_runtime_surface_registry
from runtime.runtime_surfaces.risk import (
    RuntimeSurfaceRiskError,
    approval_satisfies_floor,
    get_risk_class,
    highest_risk,
    list_risk_classes,
    normalize_approval_required,
)


ROOT = Path(__file__).resolve().parents[3]


def _base_manifest(**overrides) -> RuntimeSurfaceManifest:
    data = {
        "schema_version": 1,
        "surface_id": "test.policy.surface",
        "display_name": "Test Policy Surface",
        "surface_family": "agent_runtime",
        "surface_type": "agent",
        "owner_layer": "runtime/test",
        "status": "PARTIAL",
        "implementation_refs": ["README.md"],
        "docs_refs": ["README.md"],
        "trust_ceiling": "tier-2",
        "permission_model_refs": ["06_AGENTS/Permission-Matrix.md"],
        "gate_operations": [],
        "capabilities": [
            {
                "capability_id": "test.read",
                "maps_to": "test.read",
                "risk_class": "read_local_scoped",
                "approval_required": False,
            }
        ],
        "credential_policy": {
            "credentials_allowed": False,
            "cookies_allowed": False,
            "real_profile_allowed": False,
        },
        "fallback_policy": {
            "sticky_fallback_allowed": False,
        },
        "writeback_surfaces": ["07_LOGS/Agent-Activity/"],
        "audit_targets": ["07_LOGS/Agent-Activity/"],
        "routing_policy": {
            "default": "deny_unknown",
            "authority_layer": "runtime/test",
        },
        "mcp_exposure_policy": {
            "expose_summary": True,
            "expose_raw_manifest": False,
        },
    }
    data.update(overrides)
    return RuntimeSurfaceManifest.from_dict(data, vault_root=ROOT)


def _manifest_with_capability(risk_class: str, approval_required) -> RuntimeSurfaceManifest:
    return _base_manifest(
        capabilities=[
            {
                "capability_id": "test.capability",
                "maps_to": "test.capability",
                "risk_class": risk_class,
                "approval_required": approval_required,
            }
        ]
    )


def test_risk_taxonomy_contains_expected_classes():
    risk_classes = {definition.risk_class for definition in list_risk_classes()}

    assert "provider_fallback" in risk_classes
    assert "external_ui_mutation" in risk_classes
    assert "credential_sensitive" in risk_classes
    assert get_risk_class("destructive_action").blocks_routing is True


def test_unknown_risk_class_fails_closed():
    with pytest.raises(RuntimeSurfaceRiskError, match="Unknown ARSL risk class"):
        get_risk_class("silent_ambient_control")


def test_approval_normalization_and_floor_checks():
    assert normalize_approval_required(False) == "none"
    assert normalize_approval_required("conditional") == "conditional"
    assert normalize_approval_required(True) == "explicit"
    assert approval_satisfies_floor("conditional", "conditional") is True
    assert approval_satisfies_floor(False, "conditional") is False


def test_highest_risk_fails_closed_on_empty_input():
    with pytest.raises(RuntimeSurfaceRiskError, match="At least one risk class"):
        highest_risk([])


def test_first_party_registry_policy_is_safe():
    registry = load_runtime_surface_registry(ROOT)

    assert_registry_policy_safe(registry)


def test_policy_index_classifies_existing_capabilities():
    registry = load_runtime_surface_registry(ROOT)
    index = build_capability_policy_index(registry)

    assert index["provider.fallback_decision"][0].policy_decision == "approval_required"
    assert index["browser.click"][0].risk_class == "external_ui_mutation"
    assert index["browser.click"][0].gate_required is True


def test_unknown_capability_request_fails_closed():
    registry = load_runtime_surface_registry(ROOT)

    with pytest.raises(RuntimeSurfaceError, match="No ARSL capability policy records"):
        capability_policy_records(registry, "browser.do_anything")


def test_surface_filtered_capability_request_fails_closed():
    registry = load_runtime_surface_registry(ROOT)

    with pytest.raises(RuntimeSurfaceError, match="No ARSL capability policy records"):
        capability_policy_records(registry, "browser.click", surface_id="agent.codex.bus")


def test_policy_rejects_approval_below_floor():
    manifest = _manifest_with_capability("external_network_call", False)

    with pytest.raises(RuntimeSurfaceError, match="does not satisfy"):
        classify_manifest_capabilities(manifest)


def test_provider_fallback_requires_conditional_or_explicit_approval():
    manifest = _manifest_with_capability("provider_fallback", False)

    with pytest.raises(RuntimeSurfaceError, match="provider_fallback"):
        classify_manifest_capabilities(manifest)


def test_sensitive_capability_is_blocked_by_policy():
    manifest = _manifest_with_capability("credential_sensitive", False)

    records = classify_manifest_capabilities(manifest)

    assert records[0].policy_decision == "blocked"
    assert records[0].approval_floor == "blocked"


def test_policy_records_are_json_serializable():
    registry = load_runtime_surface_registry(ROOT)
    record = capability_policy_records(registry, "code.patch", surface_id="agent.codex.bus")[0]

    encoded = json.dumps(record.to_dict())

    assert "approval_required" in encoded
