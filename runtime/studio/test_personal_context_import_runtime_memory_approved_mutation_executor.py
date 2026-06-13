"""Tests for Personal Context Import runtime memory approved mutation executor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.personal_context_import_runtime_memory_mutation_readiness import (
    _PERSONAL_CONTEXT_ROUTE_HINTS,
    _RUNTIME_IDS,
    _runtime_nav_map_path,
    build_personal_context_import_runtime_memory_mutation_readiness,
    request_personal_context_import_runtime_memory_mutation_readiness_approval,
)
from runtime.studio.personal_context_import_runtime_memory_approved_mutation_executor import (
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    STATUS_BLOCKED,
    STATUS_OK,
    SURFACE_ID,
    execute_personal_context_import_runtime_memory_approved_mutation,
    format_personal_context_import_runtime_memory_approved_mutation,
)
from runtime.studio.service import StudioService


def _write_json(vault: Path, rel: str, obj: dict) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def _get_approval(vault: Path) -> tuple[str, str]:
    readiness = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    digest = readiness["mutation_digest"]
    result = request_personal_context_import_runtime_memory_mutation_readiness_approval(
        vault, expected_mutation_digest=digest
    )
    service = StudioService(vault)
    service.approve(result["approval_id"], reviewed_by="test")
    return result["approval_id"], digest


def _statement(digest: str) -> str:
    return f"I approve runtime memory mutation {digest} for personal context import."


# --- Blocked: missing params ---

def test_executor_blocked_no_execute_flag(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=False,
    )
    assert result["ok"] is False
    assert result["status"] == STATUS_BLOCKED
    assert "execute_flag_required" in result["blocked_reasons"]


def test_executor_blocked_missing_approval_id(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    readiness = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    digest = readiness["mutation_digest"]
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id="", expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    assert result["ok"] is False
    assert "approval_id_required" in result["blocked_reasons"]


def test_executor_blocked_wrong_digest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest="wrong-digest",
        operator_approval_statement=_statement("wrong-digest"), execute=True,
    )
    assert result["ok"] is False
    assert any("digest" in r for r in result["blocked_reasons"])


def test_executor_blocked_missing_statement(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement="", execute=True,
    )
    assert result["ok"] is False
    assert "operator_approval_statement_required" in result["blocked_reasons"]


def test_executor_blocked_statement_missing_phrase(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=f"I allow {digest}",
        execute=True,
    )
    assert result["ok"] is False
    assert "operator_approval_statement_phrase_missing" in result["blocked_reasons"]


def test_executor_blocked_exact_once_marker_present(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    from runtime.studio.personal_context_import_runtime_memory_approved_mutation_executor import MARKER_DIR
    marker = vault / MARKER_DIR / f"{approval_id}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"status":"executed"}', encoding="utf-8")
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    assert result["ok"] is False
    assert "exact_once_marker_already_present" in result["blocked_reasons"]


# --- Successful execution ---

def test_executor_success_writes_nav_maps(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    assert result["ok"] is True, f"Blocked: {result.get('blocked_reasons')}"
    assert result["status"] == STATUS_OK
    assert result["runtime_memory_mutation_performed"] is True
    assert len(result["written_nav_maps"]) == len(_RUNTIME_IDS)


def test_executor_success_nav_map_content(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    for rid in _RUNTIME_IDS:
        nav_path = vault / _runtime_nav_map_path(rid)
        assert nav_path.exists()
        data = json.loads(nav_path.read_text(encoding="utf-8"))
        assert "personal_context_routes" in data
        route_ids = {r["route_id"] for r in data["personal_context_routes"]}
        for hint in _PERSONAL_CONTEXT_ROUTE_HINTS:
            assert hint["route_id"] in route_ids


def test_executor_success_idempotent_routes(tmp_path: Path) -> None:
    """Running twice (different approvals) should not duplicate routes."""
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    # A second run would be blocked by different digest (routes now present)
    new_readiness = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    assert new_readiness["status"] == "personal_context_routes_already_present_in_all_nav_maps"


def test_executor_success_writes_marker(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    from runtime.studio.personal_context_import_runtime_memory_approved_mutation_executor import MARKER_DIR
    marker = vault / MARKER_DIR / f"{approval_id}.json"
    assert marker.exists()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["status"] == "executed"


def test_executor_success_no_canonical_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    assert result["canonical_writeback_allowed"] is False
    assert result["agent_bus_task_written"] is False
    assert result["provider_call_performed"] is False
    assert result["personal_map_apply_performed"] is False


def test_executor_success_next_pass(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_executor_idempotent_blocked_by_marker(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    stmt = _statement(digest)
    r1 = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=stmt, execute=True,
    )
    assert r1["ok"] is True
    r2 = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=stmt, execute=True,
    )
    assert r2["ok"] is False
    assert "exact_once_marker_already_present" in r2["blocked_reasons"]


# --- Format ---

def test_format_blocked_output(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id="", expected_mutation_digest="",
        operator_approval_statement="", execute=False,
    )
    text = format_personal_context_import_runtime_memory_approved_mutation(result)
    assert "Status:" in text
    assert "Blocked reasons:" in text


def test_format_successful_output(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_runtime_memory_approved_mutation(
        vault, approval_id=approval_id, expected_mutation_digest=digest,
        operator_approval_statement=_statement(digest), execute=True,
    )
    text = format_personal_context_import_runtime_memory_approved_mutation(result)
    assert "Status:" in text
    assert "Runtime memory mutation performed:" in text
