"""Tests for Personal Context Import Personal Map apply readiness surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    APPROVED,
    APPLIED,
    PENDING_REVIEW,
    PersonalMapCandidate,
    build_personal_map_node_candidate,
    personal_map_candidate_log_path,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.studio.personal_context_import_personal_map_apply_readiness import (
    APPROVAL_CLASS,
    MODEL_VERSION,
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    SURFACE_ID,
    build_personal_context_import_personal_map_apply_readiness,
    compute_personal_map_apply_readiness_digest,
    format_personal_context_import_personal_map_apply_readiness,
    request_personal_context_import_personal_map_apply_readiness_approval,
)


def _write(vault: Path, rel: str, text: str) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _make_node(node_id: str, label: str = "Test") -> PersonalMapNode:
    return PersonalMapNode(node_id=node_id, label=label, node_type="domain")


def _seed_pending_candidate(vault: Path, node_id: str = "test-node-1") -> PersonalMapCandidate:
    node = _make_node(node_id)
    candidate = build_personal_map_node_candidate(node, reason="Test candidate")
    log_path = personal_map_candidate_log_path(vault)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(candidate.to_dict(), sort_keys=True) + "\n")
    return candidate


def _seed_approved_candidate(vault: Path, node_id: str = "test-node-2") -> PersonalMapCandidate:
    node = _make_node(node_id)
    pending = build_personal_map_node_candidate(node, reason="Approved candidate")
    log_path = personal_map_candidate_log_path(vault)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    approved = PersonalMapCandidate(
        candidate_id=pending.candidate_id,
        candidate_type="node",
        reason=pending.reason,
        node=node,
        status=APPROVED,
        review_required=True,
        candidate_only=True,
        no_secret_scan={"passed": True},
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(pending.to_dict(), sort_keys=True) + "\n")
        f.write(json.dumps(approved.to_dict(), sort_keys=True) + "\n")
    return approved


# --- Basic contract ---

def test_readiness_ok_with_no_candidates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    assert result["ok"] is True
    assert result["surface"] == SURFACE_ID
    assert result["model_version"] == MODEL_VERSION
    assert result["pass"] == PASS_ID
    assert "readiness_digest" in result
    assert "candidate_summary" in result


def test_readiness_status_no_candidates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    assert result["status"] in {"no_candidates_found", "no_actionable_candidates"}


def test_readiness_with_pending_candidates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "node-a")
    _seed_pending_candidate(vault, "node-b")
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    assert result["ok"] is True
    summary = result["candidate_summary"]
    assert summary["total_candidate_count"] >= 2
    assert summary["pending_review_count"] >= 2
    assert result["status"] == "pending_review_candidates_available"


def test_readiness_with_approved_candidates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_approved_candidate(vault, "node-approved")
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    summary = result["candidate_summary"]
    assert summary["approved_count"] >= 1
    assert result["status"] in {
        "approved_candidates_ready_for_apply",
        "pending_review_candidates_available",
    }


def test_readiness_digest_is_stable(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "stable-node")
    r1 = build_personal_context_import_personal_map_apply_readiness(vault)
    r2 = build_personal_context_import_personal_map_apply_readiness(vault)
    assert r1["readiness_digest"] == r2["readiness_digest"]


def test_readiness_digest_changes_when_candidate_status_changes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "change-node")
    r1 = build_personal_context_import_personal_map_apply_readiness(vault)
    _seed_approved_candidate(vault, "extra-node")
    r2 = build_personal_context_import_personal_map_apply_readiness(vault)
    assert r1["readiness_digest"] != r2["readiness_digest"]


def test_readiness_next_pass(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_readiness_authority_no_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    auth = result["authority"]
    assert auth["personal_map_apply_allowed"] is False
    assert auth["graph_write_allowed"] is False
    assert auth["canonical_writeback_allowed"] is False
    assert auth["secret_values_read"] is False


def test_readiness_gate_requirements_present(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    reqs = result["apply_gate_requirements"]
    assert any("approval_id" in r for r in reqs)
    assert any("execute=True" in r for r in reqs)


def test_readiness_can_request_approval_when_candidates_present(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "approval-node")
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    assert result["can_request_approval"] is True


def test_readiness_can_not_request_approval_when_no_candidates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    assert result["can_request_approval"] is False


# --- Approval queueing ---

def test_request_approval_digest_mismatch(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "node-x")
    result = request_personal_context_import_personal_map_apply_readiness_approval(
        vault, expected_readiness_digest="wrong-digest"
    )
    assert result["ok"] is False
    assert "readiness_digest_mismatch" in result["blockers"]


def test_request_approval_no_candidates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = request_personal_context_import_personal_map_apply_readiness_approval(
        vault, expected_readiness_digest="any"
    )
    assert result["ok"] is False
    assert "no_candidates_to_apply" in result["blockers"]


def test_request_approval_success(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "node-q")
    readiness = build_personal_context_import_personal_map_apply_readiness(vault)
    digest = readiness["readiness_digest"]
    result = request_personal_context_import_personal_map_apply_readiness_approval(
        vault, expected_readiness_digest=digest
    )
    assert result["ok"] is True
    assert result["approval_queued"] is True
    assert result["approval_id"]
    assert result["readiness_digest"] == digest


def test_request_approval_idempotent(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "node-idem")
    readiness = build_personal_context_import_personal_map_apply_readiness(vault)
    digest = readiness["readiness_digest"]
    r1 = request_personal_context_import_personal_map_apply_readiness_approval(
        vault, expected_readiness_digest=digest
    )
    r2 = request_personal_context_import_personal_map_apply_readiness_approval(
        vault, expected_readiness_digest=digest
    )
    assert r1["approval_id"] == r2["approval_id"]
    assert r2.get("approval_already_exists") is True


# --- Format ---

def test_format_output(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_pending_candidate(vault, "format-node")
    result = build_personal_context_import_personal_map_apply_readiness(vault)
    text = format_personal_context_import_personal_map_apply_readiness(result)
    assert "Status:" in text
    assert "Readiness digest:" in text
    assert "Total candidates:" in text
    assert "Next recommended pass:" in text
