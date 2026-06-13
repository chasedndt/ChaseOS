from __future__ import annotations

import json
from pathlib import Path

from runtime.runtime_surfaces.browser_skill_memory import normalize_browser_skill_memory
from runtime.runtime_surfaces.registry import load_runtime_surface_registry
from runtime.runtime_surfaces.router import propose_route


ROOT = Path(__file__).resolve().parents[3]


def test_browser_skill_memory_inventory_loads_existing_records():
    inventory = normalize_browser_skill_memory(ROOT)
    counts = inventory.summary()["counts_by_type"]

    assert counts["browser_skill_candidate"] >= 1
    assert counts["siteops_skill_card"] >= 1
    assert counts["siteops_workflow_manifest"] >= 1
    assert counts["browser_trusted_skill_draft"] >= 1
    assert counts["browser_workflow_cache"] >= 1


def test_inventory_is_read_only_and_non_executing():
    inventory = normalize_browser_skill_memory(ROOT)

    assert inventory.writes_performed is False
    assert inventory.browser_execution_performed is False
    assert inventory.promotion_performed is False
    assert inventory.activation_performed is False
    assert all(record.activation_allowed is False for record in inventory.records)
    assert all(record.browser_execution_allowed is False for record in inventory.records)
    assert all(record.trusted_write_allowed is False for record in inventory.records)
    assert all(record.credential_access_allowed is False for record in inventory.records)
    assert all(record.browser_profile_allowed is False for record in inventory.records)


def test_candidate_records_are_redacted_and_review_only():
    inventory = normalize_browser_skill_memory(ROOT)
    candidates = inventory.records_by_type("browser_skill_candidate")

    assert candidates
    assert all(candidate.raw_content_visible is False for candidate in candidates)
    assert all(candidate.review_required is True for candidate in candidates)
    assert all(candidate.promotion_allowed is False for candidate in candidates)
    assert any(candidate.source_path.startswith("03_INPUTS/Browser-Skill-Candidates/") for candidate in candidates)


def test_workflow_cache_declared_replay_does_not_grant_execution():
    inventory = normalize_browser_skill_memory(ROOT)
    workflow_cache = inventory.records_by_type("browser_workflow_cache")

    assert workflow_cache
    assert any(record.declared_replay_allowed is True for record in workflow_cache)
    assert all(record.browser_execution_allowed is False for record in workflow_cache)


def test_browser_skill_memory_manifests_load_and_route_read_only_inventory():
    registry = load_runtime_surface_registry(ROOT)

    assert "browser.skill.memory" in registry.manifests_by_id
    assert "browser.runtime.shadow" in registry.manifests_by_id

    decision = propose_route("browser.skill_memory.inventory", registry=registry)

    assert decision.decision == "proposed"
    assert decision.selected_surface == "browser.skill.memory"
    assert decision.execution_performed is False
    assert decision.ledger_written is False


def test_inventory_is_json_serializable():
    inventory = normalize_browser_skill_memory(ROOT)

    encoded = json.dumps(inventory.to_dict())

    assert "browser_skill_candidate" in encoded
    assert "browser_execution_performed" in encoded
