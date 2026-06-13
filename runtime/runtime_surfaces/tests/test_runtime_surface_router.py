from __future__ import annotations

import json
from pathlib import Path

from runtime.runtime_surfaces.models import RuntimeSurfaceManifest
from runtime.runtime_surfaces.registry import RuntimeSurfaceRegistry, load_runtime_surface_registry
from runtime.runtime_surfaces.router import propose_route


ROOT = Path(__file__).resolve().parents[3]


def _blocked_registry() -> RuntimeSurfaceRegistry:
    data = {
        "schema_version": 1,
        "surface_id": "test.blocked.surface",
        "display_name": "Blocked Test Surface",
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
                "capability_id": "test.secret",
                "maps_to": "test.secret",
                "risk_class": "credential_sensitive",
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
    manifest = RuntimeSurfaceManifest.from_dict(data, vault_root=ROOT)
    return RuntimeSurfaceRegistry(manifests_by_id={manifest.surface_id: manifest})


def test_proposes_read_only_route_for_low_risk_capability():
    registry = load_runtime_surface_registry(ROOT)

    decision = propose_route("code.review", registry=registry)

    assert decision.decision == "proposed"
    assert decision.selected_surface == "agent.codex.bus"
    assert decision.authority_layer == "runtime/agent_bus"
    assert decision.execution_performed is False
    assert decision.ledger_written is False


def test_external_ui_mutation_requires_approval():
    registry = load_runtime_surface_registry(ROOT)

    decision = propose_route("browser.click", registry=registry)

    assert decision.decision == "approval_required"
    assert decision.selected_surface == "browser.operator.playwright"
    assert decision.gate_required is True
    assert decision.approval_required == "conditional"


def test_provider_fallback_routes_to_rpgl_and_requires_approval():
    registry = load_runtime_surface_registry(ROOT)

    decision = propose_route("provider.fallback_decision", registry=registry)

    assert decision.decision == "approval_required"
    assert decision.selected_surface == "provider.runtime.rpgl"
    assert decision.authority_layer == "runtime/providers"
    assert decision.risk_class == "provider_fallback"


def test_unknown_capability_denies_without_fallback():
    registry = load_runtime_surface_registry(ROOT)

    decision = propose_route("browser.do_anything", registry=registry)

    assert decision.decision == "deny_unknown"
    assert decision.selected_surface is None
    assert decision.candidate_surfaces == ()
    assert decision.gate_required is True


def test_surface_filter_selects_matching_surface():
    registry = load_runtime_surface_registry(ROOT)

    decision = propose_route("browser.screenshot", registry=registry, requested_surface_id="browser.operator.playwright")

    assert decision.decision == "proposed"
    assert decision.selected_surface == "browser.operator.playwright"


def test_surface_filter_denies_mismatch():
    registry = load_runtime_surface_registry(ROOT)

    decision = propose_route("browser.click", registry=registry, requested_surface_id="agent.codex.bus")

    assert decision.decision == "deny_unknown"
    assert decision.selected_surface is None
    assert "agent.codex.bus.browser.click" in decision.denial_reasons[0]


def test_blocked_policy_routes_blocked():
    decision = propose_route("test.secret", registry=_blocked_registry())

    assert decision.decision == "blocked"
    assert decision.selected_surface == "test.blocked.surface"
    assert decision.risk_class == "credential_sensitive"
    assert decision.execution_performed is False


def test_route_decision_is_json_serializable():
    registry = load_runtime_surface_registry(ROOT)
    decision = propose_route("code.patch", registry=registry)

    encoded = json.dumps(decision.to_dict())

    assert "approval_required" in encoded
    assert '"ledger_written": false' in encoded
