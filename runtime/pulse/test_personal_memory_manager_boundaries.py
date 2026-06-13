"""Regression QA for Pulse Personal Memory Manager governance boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    PERSONAL_MAP_CANDIDATE_ROOT,
    PersonalMapCandidate,
    build_personal_map_node_candidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.candidate_apply import APPLY_REGISTRY_ROOT, apply_reviewed_candidates
from runtime.pulse.card_schema import EvidenceRef
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision
PROTECTED_DOCS = (
    "SOUL.md",
    "00_HOME/Operating-System.md",
    "00_HOME/Principles.md",
    "00_HOME/Dashboard.md",
)


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    for rel in PROTECTED_DOCS:
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Protected {rel}\noriginal protected content\n", encoding="utf-8")
    (vault / "SOUL.template.md").write_text(
        "# SOUL Template\n\nGeneric public template. Do not add private facts.\n",
        encoding="utf-8",
    )
    (vault / "core_export" / "templates").mkdir(parents=True, exist_ok=True)
    (vault / "runtime" / "studio").mkdir(parents=True, exist_ok=True)
    return vault


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_node(node_id: str = "node-memory-manager-domain") -> PersonalMapNode:
    return PersonalMapNode(
        node_id=node_id,
        node_type="domain",
        label="Memory Manager QA Domain",
        summary="Safe synthetic domain used for Personal Memory Manager regression QA.",
        evidence=[
            EvidenceRef(
                source_path="SOUL.md",
                source_type="protected_identity_doc",
                summary="Protected document was used as read-only evidence only.",
                trust_label="protected-read-only",
                quote="Synthetic safe quote; no private fact or secret is persisted.",
            )
        ],
        tags=["qa", "personal-memory-manager"],
    )


def test_secret_like_candidate_payload_is_blocked_before_persistence(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(ValueError, match="secret-like"):
        candidate = build_personal_map_node_candidate(
            PersonalMapNode(
                node_id="node-secret-like",
                node_type="preference",
                label="Connector token preference",
                summary="Use API key test-key-live_1234567890abcdef1234567890abcdef for importer tests.",
            ),
            reason="Importer must refuse secret-like payloads before writing candidate logs.",
            source_deck_path="03_INPUTS/00_QUARANTINE/secret-export.md",
            created_at="2026-05-12T10:00:00+00:00",
        )
        persist_personal_map_candidate(vault, candidate)

    candidate_root = vault / PERSONAL_MAP_CANDIDATE_ROOT
    assert not candidate_root.exists() or not list(candidate_root.rglob("*.jsonl"))


def test_no_secret_metadata_is_persisted_without_secret_payload(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    candidate = build_personal_map_node_candidate(
        _safe_node(),
        reason="Safe candidate proves no-secret scan metadata is persisted.",
        created_at="2026-05-12T10:05:00+00:00",
    )

    artifact = persist_personal_map_candidate(vault, candidate)
    line = (vault / artifact.path).read_text(encoding="utf-8").strip()
    payload = json.loads(line)

    assert payload["no_secret_scan"]["passed"] is True
    assert payload["no_secret_scan"]["blocked_secret_like_content"] is False
    assert "test-key-live" not in line


def test_live_apply_preserves_protected_docs_evidence_review_decision_and_idempotency(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    before_hashes = {rel: _sha(vault / rel) for rel in PROTECTED_DOCS}

    candidate = build_personal_map_node_candidate(
        _safe_node(),
        reason="Approved Personal Map candidate with protected-doc evidence.",
        source_deck_path="07_LOGS/Pulse-Decks/users/synthetic-memory-manager-qa.json",
        created_at="2026-05-12T10:10:00+00:00",
    )
    candidate_artifact = persist_personal_map_candidate(vault, candidate)
    decision = build_review_decision(
        candidate,
        decision_type="approve_for_future_apply",
        reviewer="qa-operator",
        operator_note="Approved synthetic safe memory for idempotent apply proof.",
        source_candidate_log_path=candidate_artifact.path,
        created_at="2026-05-12T10:11:00+00:00",
    )
    decision_artifact = persist_review_decision(vault, decision)

    first = apply_reviewed_candidates(vault, dry_run=False, candidate_kind="personal_map")
    second = apply_reviewed_candidates(vault, dry_run=False, candidate_kind="personal_map")

    after_hashes = {rel: _sha(vault / rel) for rel in PROTECTED_DOCS}
    assert after_hashes == before_hashes
    assert first.applied_count == 1
    assert second.applied_count == 0
    assert second.skipped_already_applied == 1

    graph = json.loads((vault / "runtime" / "memory" / "personal-map" / "graph.json").read_text(encoding="utf-8"))
    node = graph["nodes"][candidate.node.node_id]
    assert node["approved_by_decision"] == decision.decision_id
    assert node["evidence"][0]["source_path"] == "SOUL.md"
    assert node["evidence"][0]["trust_label"] == "protected-read-only"

    registry = json.loads((vault / APPLY_REGISTRY_ROOT / "applied-decisions.json").read_text(encoding="utf-8"))
    assert decision.decision_id in registry["applied_decision_ids"]

    persisted_decision = json.loads((vault / decision_artifact.path).read_text(encoding="utf-8").strip())
    assert persisted_decision["reviewer"] == "qa-operator"
    assert persisted_decision["status"] == "recorded"
    assert persisted_decision["source_candidate_log_path"] == candidate_artifact.path
    assert persisted_decision["decision_record_only"] is True


def test_public_core_export_manifest_excludes_private_memory_manager_state() -> None:
    vault_root = Path(__file__).resolve().parents[2]
    template_text = (vault_root / "SOUL.template.md").read_text(encoding="utf-8")
    manifest_path = vault_root / "core_export" / "export_manifest.yaml"
    text = manifest_path.read_text(encoding="utf-8")

    assert "[Your Name]" in template_text
    assert "TradeSync" not in template_text
    assert "StrikeZone" not in template_text
    assert "07_LOGS/Pulse-Decks/memory-candidates" not in text
    assert "07_LOGS/Pulse-Decks/review-decisions" not in text
    assert "runtime/memory/personal-map/graph.json" not in text
    assert "\n  - source: SOUL.md" not in text
