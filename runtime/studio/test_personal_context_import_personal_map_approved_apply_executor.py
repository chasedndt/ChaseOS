"""Tests for Personal Context Import Personal Map approved apply executor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    APPROVED,
    PENDING_REVIEW,
    PersonalMapCandidate,
    build_personal_map_node_candidate,
    personal_map_candidate_log_path,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.studio.personal_context_import_personal_map_apply_readiness import (
    build_personal_context_import_personal_map_apply_readiness,
    request_personal_context_import_personal_map_apply_readiness_approval,
)
from runtime.studio.personal_context_import_personal_map_approved_apply_executor import (
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    STATUS_BLOCKED,
    STATUS_OK,
    SURFACE_ID,
    execute_personal_context_import_personal_map_approved_apply,
    format_personal_context_import_personal_map_approved_apply,
)
from runtime.studio.service import StudioService


def _write(vault: Path, rel: str, text: str) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _make_node(node_id: str) -> PersonalMapNode:
    return PersonalMapNode(node_id=node_id, label=node_id.replace("-", " ").title(), node_type="domain")


def _seed_candidate(vault: Path, node_id: str = "test-node") -> PersonalMapCandidate:
    node = _make_node(node_id)
    candidate = build_personal_map_node_candidate(node, reason="Test candidate for executor")
    log_path = personal_map_candidate_log_path(vault)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(candidate.to_dict(), sort_keys=True) + "\n")
    return candidate


def _get_approval(vault: Path) -> tuple[str, str]:
    """Seed candidate, get readiness, queue approval. Returns (approval_id, digest)."""
    readiness = build_personal_context_import_personal_map_apply_readiness(vault)
    digest = readiness["readiness_digest"]
    result = request_personal_context_import_personal_map_apply_readiness_approval(
        vault, expected_readiness_digest=digest
    )
    # Manually mark as approved
    service = StudioService(vault)
    req = service.get_approval(result["approval_id"])
    assert req is not None
    service.approve(result["approval_id"], reviewed_by="test")
    return result["approval_id"], digest


def _statement(digest: str) -> str:
    return f"I approve personal map apply {digest} — personal map context import."


# --- Blocked: missing params ---

def test_executor_blocked_no_execute_flag(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "no-exec-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=False,
    )
    assert result["ok"] is False
    assert result["status"] == STATUS_BLOCKED
    assert "execute_flag_required" in result["blocked_reasons"]
    assert result["personal_map_apply_performed"] is False


def test_executor_blocked_missing_approval_id(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "missing-id-node")
    readiness = build_personal_context_import_personal_map_apply_readiness(vault)
    digest = readiness["readiness_digest"]
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id="",
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    assert result["ok"] is False
    assert "approval_id_required" in result["blocked_reasons"]


def test_executor_blocked_missing_digest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "missing-digest-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest="",
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    assert result["ok"] is False
    assert "expected_readiness_digest_required" in result["blocked_reasons"]


def test_executor_blocked_wrong_digest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "wrong-digest-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest="wrong-digest-value",
        operator_approval_statement=_statement("wrong-digest-value"),
        execute=True,
    )
    assert result["ok"] is False
    assert any("digest" in r for r in result["blocked_reasons"])


def test_executor_blocked_missing_statement(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "no-stmt-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement="",
        execute=True,
    )
    assert result["ok"] is False
    assert "operator_approval_statement_required" in result["blocked_reasons"]


def test_executor_blocked_statement_missing_phrase(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "bad-phrase-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=f"I authorize {digest}",
        execute=True,
    )
    assert result["ok"] is False
    assert "operator_approval_statement_phrase_missing" in result["blocked_reasons"]


def test_executor_blocked_approval_not_found(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "no-approval-node")
    readiness = build_personal_context_import_personal_map_apply_readiness(vault)
    digest = readiness["readiness_digest"]
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id="nonexistent-id",
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    assert result["ok"] is False
    assert any("not_found" in r or "approval" in r for r in result["blocked_reasons"])


def test_executor_blocked_exact_once_marker_already_present(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "once-node")
    approval_id, digest = _get_approval(vault)
    # Pre-place the marker
    from runtime.studio.personal_context_import_personal_map_approved_apply_executor import MARKER_DIR
    marker_path = vault / MARKER_DIR / f"{approval_id}.json"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text('{"status": "executed"}', encoding="utf-8")
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    assert result["ok"] is False
    assert "exact_once_marker_already_present" in result["blocked_reasons"]


# --- Successful execution ---

def test_executor_success_writes_graph(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "fitness")
    _seed_candidate(vault, "language")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    assert result["ok"] is True, f"Blocked: {result.get('blocked_reasons')}"
    assert result["status"] == STATUS_OK
    assert result["personal_map_apply_performed"] is True
    graph_path = vault / "runtime/memory/personal-map/graph.json"
    assert graph_path.exists()


def test_executor_success_writes_marker(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "marker-test-node")
    approval_id, digest = _get_approval(vault)
    execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    from runtime.studio.personal_context_import_personal_map_approved_apply_executor import MARKER_DIR
    marker_path = vault / MARKER_DIR / f"{approval_id}.json"
    assert marker_path.exists()
    marker_data = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker_data["status"] == "executed"


def test_executor_success_writes_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "evidence-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    evidence_record = result.get("evidence_record") or {}
    evidence_paths = evidence_record.get("evidence_paths") or {}
    assert evidence_paths.get("execution_evidence")
    evidence_path = vault / evidence_paths["execution_evidence"]
    assert evidence_path.exists()


def test_executor_success_no_canonical_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "no-canonical-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    assert result["personal_map_apply_performed"] is True
    assert result["agent_bus_task_written"] is False
    assert result["provider_call_performed"] is False
    assert result["runtime_memory_mutation_performed"] is False


def test_executor_success_next_pass(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "next-pass-node")
    approval_id, digest = _get_approval(vault)
    result = execute_personal_context_import_personal_map_approved_apply(
        vault,
        approval_id=approval_id,
        expected_readiness_digest=digest,
        operator_approval_statement=_statement(digest),
        execute=True,
    )
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_executor_idempotent_blocked_by_marker(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_candidate(vault, "idem-node")
    approval_id, digest = _get_approval(vault)
    stmt = _statement(digest)
    r1 = execute_personal_context_import_personal_map_approved_apply(
        vault, approval_id=approval_id, expected_readiness_digest=digest,
        operator_approval_statement=stmt, execute=True,
    )
    assert r1["ok"] is True
    r2 = execute_personal_context_import_personal_map_approved_apply(
        vault, approval_id=approval_id, expected_readiness_digest=digest,
        operator_approval_statement=stmt, execute=True,
    )
    assert r2["ok"] is False
    assert "exact_once_marker_already_present" in r2["blocked_reasons"]


# --- Format ---

def test_format_blocked(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = execute_personal_context_import_personal_map_approved_apply(
        vault, approval_id="", expected_readiness_digest="",
        operator_approval_statement="", execute=False,
    )
    text = format_personal_context_import_personal_map_approved_apply(result)
    assert "Status:" in text
    assert "Blocked reasons:" in text
