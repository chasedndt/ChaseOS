from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.runtime_surfaces.models import RuntimeSurfaceError
from runtime.runtime_surfaces.registry import (
    load_runtime_surface_registry,
    load_surface_manifest,
    schema_path,
)


ROOT = Path(__file__).resolve().parents[3]


def _base_manifest(**overrides):
    data = {
        "schema_version": 1,
        "surface_id": "test.surface",
        "display_name": "Test Surface",
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
    return data


def _write_manifest(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def test_loads_first_party_manifests():
    registry = load_runtime_surface_registry(ROOT)

    assert {
        "agent.archon.bus",
        "agent.codex.bus",
        "agent.hermes.bus",
        "agent.openclaw.bus",
        "browser.operator.playwright",
        "client.studio.sandboxed_static_mount",
        "provider.local_ollama.timeout_contract",
        "provider.openai.responses_mcp_dry_run",
        "provider.runtime.rpgl",
        "runtime.mcp.chaseos",
        "siteops.skill.runtime",
    }.issubset(registry.manifests_by_id)


def test_registry_filters_capabilities_by_risk():
    registry = load_runtime_surface_registry(ROOT)

    proposal_caps = registry.capabilities_by_risk("proposal_write")

    assert "agent.archon.bus" in proposal_caps
    assert "implementation" in proposal_caps["agent.archon.bus"]
    assert "agent.codex.bus" in proposal_caps
    assert "code.patch" in proposal_caps["agent.codex.bus"]
    assert "agent.hermes.bus" in proposal_caps
    assert "operator-briefing" in proposal_caps["agent.hermes.bus"]
    assert "agent.openclaw.bus" in proposal_caps
    assert "scheduled-briefing" in proposal_caps["agent.openclaw.bus"]


def test_registry_finds_surface_for_capability():
    registry = load_runtime_surface_registry(ROOT)

    surfaces = registry.surfaces_for_capability("browser.screenshot")

    assert [surface.surface_id for surface in surfaces] == ["browser.operator.playwright"]


def test_agent_runtime_manifest_expansion_registers_existing_bus_lanes():
    registry = load_runtime_surface_registry(ROOT)

    archon = registry.get_surface("agent.archon.bus")
    hermes = registry.get_surface("agent.hermes.bus")
    openclaw = registry.get_surface("agent.openclaw.bus")

    assert archon.owner_layer == "runtime/agent_bus"
    assert hermes.owner_layer == "runtime/agent_bus"
    assert openclaw.owner_layer == "runtime/agent_bus"
    assert archon.routing_policy["authority_layer"] == "runtime/agent_bus"
    assert hermes.routing_policy["authority_layer"] == "runtime/agent_bus"
    assert openclaw.routing_policy["authority_layer"] == "runtime/agent_bus"
    assert archon.credential_policy["credentials_allowed"] is False
    assert hermes.credential_policy["credentials_allowed"] is False
    assert openclaw.credential_policy["credentials_allowed"] is False
    assert archon.fallback_policy["sticky_fallback_allowed"] is False
    assert hermes.fallback_policy["sticky_fallback_allowed"] is False
    assert openclaw.fallback_policy["sticky_fallback_allowed"] is False
    assert archon.mcp_exposure_policy["expose_raw_manifest"] is False
    assert hermes.mcp_exposure_policy["expose_raw_manifest"] is False
    assert openclaw.mcp_exposure_policy["expose_raw_manifest"] is False


def test_provider_specific_manifests_are_bounded_metadata_only():
    registry = load_runtime_surface_registry(ROOT)

    openai = registry.get_surface("provider.openai.responses_mcp_dry_run")
    ollama = registry.get_surface("provider.local_ollama.timeout_contract")

    assert openai.routing_policy["authority_layer"] == "runtime/adapters/openai"
    assert ollama.routing_policy["authority_layer"] == "runtime/providers"
    assert openai.credential_policy["credentials_allowed"] is False
    assert ollama.credential_policy["credentials_allowed"] is False
    assert openai.credential_policy["real_profile_allowed"] is False
    assert ollama.credential_policy["real_profile_allowed"] is False
    assert openai.fallback_policy["sticky_fallback_allowed"] is False
    assert ollama.fallback_policy["sticky_fallback_allowed"] is False
    assert openai.mcp_exposure_policy["expose_raw_manifest"] is False
    assert ollama.mcp_exposure_policy["expose_raw_manifest"] is False
    assert "openai.responses_mcp_payload.build" in openai.capability_ids()
    assert "provider.ollama_timeout_contract" in ollama.capability_ids()


def test_client_embedded_manifest_registers_studio_static_mount_only():
    registry = load_runtime_surface_registry(ROOT)

    surface = registry.get_surface("client.studio.sandboxed_static_mount")

    assert surface.surface_family == "client_embedded_runtime"
    assert surface.surface_type == "client_embedded"
    assert surface.owner_layer == "runtime/studio"
    assert surface.routing_policy["authority_layer"] == "runtime/studio"
    assert surface.credential_policy["credentials_allowed"] is False
    assert surface.credential_policy["cookies_allowed"] is False
    assert surface.credential_policy["real_profile_allowed"] is False
    assert surface.fallback_policy["sticky_fallback_allowed"] is False
    assert surface.mcp_exposure_policy["expose_raw_manifest"] is False
    assert {
        "client.embedded.static_artifact.inspect",
        "client.embedded.static_artifact.mount_read_only",
        "client.embedded.local_http_smoke",
        "client.embedded.artifact_refresh.plan",
    }.issubset(surface.capability_ids())
    assert all(capability.risk_class in {"read_local_scoped", "draft_only"} for capability in surface.capabilities)


def test_schema_file_is_json_and_declares_required_fields():
    schema = json.loads(schema_path(ROOT).read_text(encoding="utf-8"))

    assert schema["properties"]["schema_version"]["const"] == 1
    assert "trust_ceiling" in schema["required"]
    assert "credential_policy" in schema["required"]


def test_missing_trust_ceiling_fails_closed(tmp_path):
    data = _base_manifest()
    data.pop("trust_ceiling")
    path = _write_manifest(tmp_path / "missing-trust.yaml", data)

    with pytest.raises(RuntimeSurfaceError, match="missing fields"):
        load_surface_manifest(path, vault_root=ROOT)


def test_unknown_surface_type_fails_closed(tmp_path):
    path = _write_manifest(tmp_path / "surface.yaml", _base_manifest(surface_type="ambient_browser"))

    with pytest.raises(RuntimeSurfaceError, match="surface_type"):
        load_surface_manifest(path, vault_root=ROOT)


def test_unknown_risk_class_fails_closed(tmp_path):
    data = _base_manifest()
    data["capabilities"][0]["risk_class"] = "quietly_do_anything"
    path = _write_manifest(tmp_path / "surface.yaml", data)

    with pytest.raises(RuntimeSurfaceError, match="risk_class"):
        load_surface_manifest(path, vault_root=ROOT)


def test_credentials_allowed_fails_closed(tmp_path):
    data = _base_manifest()
    data["credential_policy"]["credentials_allowed"] = True
    path = _write_manifest(tmp_path / "surface.yaml", data)

    with pytest.raises(RuntimeSurfaceError, match="credential"):
        load_surface_manifest(path, vault_root=ROOT)


def test_sticky_fallback_fails_closed(tmp_path):
    data = _base_manifest()
    data["fallback_policy"]["sticky_fallback_allowed"] = True
    path = _write_manifest(tmp_path / "surface.yaml", data)

    with pytest.raises(RuntimeSurfaceError, match="sticky fallback"):
        load_surface_manifest(path, vault_root=ROOT)


def test_raw_mcp_manifest_exposure_fails_closed(tmp_path):
    data = _base_manifest()
    data["mcp_exposure_policy"]["expose_raw_manifest"] = True
    path = _write_manifest(tmp_path / "surface.yaml", data)

    with pytest.raises(RuntimeSurfaceError, match="raw manifests"):
        load_surface_manifest(path, vault_root=ROOT)


def test_duplicate_surface_ids_fail_closed(tmp_path):
    _write_manifest(tmp_path / "one.yaml", _base_manifest())
    _write_manifest(tmp_path / "two.yaml", _base_manifest())

    with pytest.raises(RuntimeSurfaceError, match="duplicate runtime surface id"):
        load_runtime_surface_registry(ROOT, manifests_dir=tmp_path)


def test_missing_referenced_file_fails_when_required(tmp_path):
    path = _write_manifest(
        tmp_path / "surface.yaml",
        _base_manifest(implementation_refs=["runtime/nope/not-here.py"]),
    )

    with pytest.raises(RuntimeSurfaceError, match="does not exist"):
        load_surface_manifest(path, vault_root=ROOT)
