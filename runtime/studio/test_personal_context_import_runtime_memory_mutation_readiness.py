"""Tests for Personal Context Import runtime memory mutation readiness surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.personal_context_import_runtime_memory_mutation_readiness import (
    APPROVAL_CLASS,
    MODEL_VERSION,
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    SURFACE_ID,
    _PERSONAL_CONTEXT_ROUTE_HINTS,
    _RUNTIME_IDS,
    _compute_mutation_digest,
    _runtime_nav_map_path,
    _runtime_state,
    build_personal_context_import_runtime_memory_mutation_readiness,
    request_personal_context_import_runtime_memory_mutation_readiness_approval,
)


def _write(vault: Path, rel: str, text: str) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _write_json(vault: Path, rel: str, obj: dict) -> None:
    _write(vault, rel, json.dumps(obj, indent=2) + "\n")


def _seed_nav_map(vault: Path, runtime_id: str, *, with_routes: bool = False) -> None:
    data: dict = {"runtime": runtime_id}
    if with_routes:
        data["personal_context_routes"] = [{"route_id": "personal_operator_index"}]
    _write_json(vault, _runtime_nav_map_path(runtime_id).as_posix(), data)


# --- Basic contract ---

def test_readiness_ok_empty_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert result["ok"] is True
    assert result["surface"] == SURFACE_ID
    assert result["model_version"] == MODEL_VERSION
    assert result["pass"] == PASS_ID


def test_readiness_runtimes_ids_covered(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    runtime_ids = {s["runtime_id"] for s in result["runtime_states"]}
    assert runtime_ids == set(_RUNTIME_IDS)


def test_readiness_all_need_mutation_when_no_nav_maps(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert len(result["runtimes_needing_mutation"]) == len(_RUNTIME_IDS)


def test_readiness_no_mutation_needed_when_routes_present(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    for rid in _RUNTIME_IDS:
        _seed_nav_map(vault, rid, with_routes=True)
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert len(result["runtimes_needing_mutation"]) == 0
    assert result["status"] == "personal_context_routes_already_present_in_all_nav_maps"


def test_readiness_partial_mutation_needed(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_nav_map(vault, "codex", with_routes=True)
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    # hermes and archon still need mutation
    assert "codex" not in result["runtimes_needing_mutation"]
    assert len(result["runtimes_needing_mutation"]) == 2


def test_readiness_mutation_digest_stable(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    r1 = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    r2 = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert r1["mutation_digest"] == r2["mutation_digest"]


def test_readiness_route_hints_count(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert len(result["personal_context_route_hints"]) == len(_PERSONAL_CONTEXT_ROUTE_HINTS)


def test_readiness_authority_no_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    auth = result["authority"]
    assert auth["runtime_memory_mutation_allowed"] is False
    assert auth["nav_map_write_allowed"] is False
    assert auth["canonical_writeback_allowed"] is False
    assert auth["secret_values_read"] is False


def test_readiness_next_pass(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_readiness_can_request_approval(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert result["can_request_approval"] is True


# --- Approval queueing ---

def test_request_approval_digest_mismatch(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = request_personal_context_import_runtime_memory_mutation_readiness_approval(
        vault, expected_mutation_digest="wrong"
    )
    assert result["ok"] is False
    assert "mutation_digest_mismatch" in result["blockers"]


def test_request_approval_empty_digest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = request_personal_context_import_runtime_memory_mutation_readiness_approval(
        vault, expected_mutation_digest=""
    )
    assert result["ok"] is False
    assert "expected_mutation_digest_required" in result["blockers"]


def test_request_approval_success(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    readiness = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    digest = readiness["mutation_digest"]
    result = request_personal_context_import_runtime_memory_mutation_readiness_approval(
        vault, expected_mutation_digest=digest
    )
    assert result["ok"] is True
    assert result["approval_queued"] is True
    assert result["approval_id"]
    assert result["mutation_digest"] == digest


def test_request_approval_idempotent(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    readiness = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    digest = readiness["mutation_digest"]
    r1 = request_personal_context_import_runtime_memory_mutation_readiness_approval(
        vault, expected_mutation_digest=digest
    )
    r2 = request_personal_context_import_runtime_memory_mutation_readiness_approval(
        vault, expected_mutation_digest=digest
    )
    assert r1["approval_id"] == r2["approval_id"]
    assert r2.get("approval_already_exists") is True


# --- Runtime state helper ---

def test_runtime_state_nav_map_absent(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state = _runtime_state(vault, "codex")
    assert state["runtime_id"] == "codex"
    assert state["nav_map_present"] is False
    assert state["mutation_needed"] is True


def test_runtime_state_nav_map_present_no_routes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_nav_map(vault, "hermes", with_routes=False)
    state = _runtime_state(vault, "hermes")
    assert state["nav_map_present"] is True
    assert state["personal_context_routes_already_present"] is False
    assert state["mutation_needed"] is True


def test_runtime_state_nav_map_present_with_routes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_nav_map(vault, "archon", with_routes=True)
    state = _runtime_state(vault, "archon")
    assert state["nav_map_present"] is True
    assert state["personal_context_routes_already_present"] is True
    assert state["mutation_needed"] is False
