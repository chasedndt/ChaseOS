"""Tests for graph/source-pack/canonical promotion executor proof."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.graph.canonical_promotion_executor_proof import (
    PROTECTED_DENIAL_TARGET,
    SURFACE_ID,
    build_canonical_promotion_executor_proof,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _seed_vault(root: Path) -> None:
    (root / "runtime" / "acquisition" / "packs").mkdir(parents=True)
    (root / "runtime" / "acquisition" / "packs" / "strikezone-latest.json").write_text(
        json.dumps(
            {
                "profile": "strikezone",
                "reviewed": True,
                "normalized_source_pack": "runtime/acquisition/packs/example/normalized_source_pack.json",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "06_AGENTS").mkdir(parents=True)
    (root / PROTECTED_DENIAL_TARGET).write_text("# Permission Matrix\n", encoding="utf-8")
    (root / "02_KNOWLEDGE").mkdir(parents=True)


def test_canonical_promotion_executor_proof_models_required_gate_boundaries_without_writes(tmp_path: Path) -> None:
    _seed_vault(tmp_path)
    before = _snapshot(tmp_path)

    model = build_canonical_promotion_executor_proof(tmp_path)

    assert _snapshot(tmp_path) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["candidate_packet"]["approved_candidate_packet"] is True
    assert model["candidate_packet"]["candidate_digest_sha256"]
    assert model["derived_vs_canonical_graph"]["derived_graph_may_be_displayed_by_studio_chat"] is True
    assert model["derived_vs_canonical_graph"]["canonical_graph_mutation_performed"] is False
    assert model["derived_vs_canonical_graph"]["knowledge_promotion_performed"] is False
    assert model["source_pack_promotion_state"]["latest_pointer_exists"] is True
    assert model["source_pack_promotion_state"]["reviewed_pointer_observed"] is True
    assert model["source_pack_promotion_state"]["promotion_state_written"] is False
    assert model["protected_file_denial_proof"]["target_path"] == PROTECTED_DENIAL_TARGET
    assert model["protected_file_denial_proof"]["denial_proven"] is True
    assert model["protected_file_denial_proof"]["protected_file_written"] is False
    assert model["rollback_rejection_behavior"]["rollback_path_modeled"] is True
    assert model["rollback_rejection_behavior"]["canonical_state_restored_or_unchanged"] is True
    assert model["authority"]["canonical_graph_write_allowed"] is False
    assert model["authority"]["source_pack_promotion_write_allowed"] is False
    assert model["authority"]["knowledge_promotion_write_allowed"] is False
    assert model["authority"]["studio_chat_direct_apply_allowed"] is False


def test_canonical_promotion_executor_proof_blocks_missing_approval(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    model = build_canonical_promotion_executor_proof(tmp_path, gate_approval_id=None)

    assert model["status"] == "blocked-missing-approved-candidate"
    assert model["candidate_packet"]["approved_candidate_packet"] is False
    assert "approved-candidate-packet-missing" in model["execution_gate"]["blocked_reasons"]
    assert model["execution_gate"]["mutation_execution_allowed_now"] is False


def test_canonical_promotion_executor_proof_writes_only_agent_activity_audit_when_requested(tmp_path: Path) -> None:
    _seed_vault(tmp_path)
    before = set(_snapshot(tmp_path))

    model = build_canonical_promotion_executor_proof(
        tmp_path,
        write_audit=True,
        audit_slug="2026-05-11-hermes-optimus-test-graph-source-pack-proof",
    )

    after = set(_snapshot(tmp_path))
    new_files = sorted(after - before)
    assert new_files == [
        "07_LOGS/Agent-Activity/2026-05-11-hermes-optimus-test-graph-source-pack-proof.json",
        "07_LOGS/Agent-Activity/2026-05-11-hermes-optimus-test-graph-source-pack-proof.md",
    ]
    assert model["provenance_audit"]["audit_written"] is True
    assert model["authority"]["agent_activity_audit_written"] is True
    assert model["authority"]["canonical_graph_write_allowed"] is False
    md = (tmp_path / model["provenance_audit"]["audit_markdown_path"]).read_text(encoding="utf-8")
    assert "[[Hermes-Runtime-Profile]]" in md
    assert "[[Agent-Activity-Index]]" in md
    assert "Canonical graph write allowed: `False`" in md
