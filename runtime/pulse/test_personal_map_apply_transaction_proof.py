from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    build_personal_map_node_candidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.candidate_apply import _personal_map_graph_path, apply_reviewed_candidates
from runtime.pulse.personal_map_apply_transaction_proof import (
    build_personal_map_apply_transaction_proof,
    write_personal_map_apply_transaction_proof,
)
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    return vault


def _approved_candidate(vault: Path) -> tuple[str, str]:
    node = PersonalMapNode(
        node_id="personal_map_transaction_goal",
        node_type="goal",
        label="Prove Personal Map apply transaction",
        summary="A fixture candidate for transaction proof.",
    )
    candidate = build_personal_map_node_candidate(
        node,
        reason="transaction proof fixture",
        source_card_id="card-transaction-proof-001",
    )
    persist_personal_map_candidate(vault, candidate)
    decision = build_review_decision(
        candidate,
        decision_type="approve_for_future_apply",
        reviewer="Codex",
        operator_note="Approved in isolated test fixture.",
    )
    persist_review_decision(vault, decision)
    return candidate.candidate_id, decision.decision_id


def test_transaction_proof_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    before = _snapshot(vault)

    proof = build_personal_map_apply_transaction_proof(
        vault,
        generated_at="2026-05-03T21:00:00+01:00",
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["transaction_status"] == "blocked_no_ready_personal_map_candidates"
    assert payload["ready_candidate_count"] == 0
    assert payload["transaction_entry_count"] == 0
    assert payload["live_apply_allowed"] is False
    assert payload["writes_runtime_memory_graph"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_transaction_proof_builds_ready_entries_without_graph_write(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    candidate_id, decision_id = _approved_candidate(vault)
    before = _snapshot(vault)

    proof = build_personal_map_apply_transaction_proof(
        vault,
        generated_at="2026-05-03T21:05:00+01:00",
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["transaction_status"] == "transaction_proof_ready"
    assert payload["transaction_id"].startswith("personal-map-apply-txn-")
    assert payload["ready_candidate_count"] == 1
    assert payload["dry_run_apply_count"] == 1
    assert payload["dry_run_error_count"] == 0
    entry = payload["entries"][0]
    assert entry["candidate_id"] == candidate_id
    assert entry["decision_id"] == decision_id
    assert entry["planned_write_target"] == "runtime/memory/personal-map/graph.json"
    assert entry["idempotency_key"] == f"personal_map_apply:{decision_id}"
    assert entry["live_apply_allowed"] is False
    assert not _personal_map_graph_path(vault).exists()


def test_transaction_proof_blocks_already_applied_decisions(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _approved_candidate(vault)
    result = apply_reviewed_candidates(vault, dry_run=False, candidate_kind="personal_map")
    result.validate()
    assert _personal_map_graph_path(vault).exists()

    proof = build_personal_map_apply_transaction_proof(vault)
    payload = proof.to_dict()

    assert payload["transaction_status"] == "blocked_no_ready_personal_map_candidates"
    assert payload["ready_candidate_count"] == 0
    assert payload["transaction_entry_count"] == 0
    assert payload["graph_present_before"] is True
    assert payload["graph_sha256_before"]


def test_transaction_proof_write_is_artifact_only(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _approved_candidate(vault)

    proof = write_personal_map_apply_transaction_proof(
        vault,
        generated_at="2026-05-03T21:10:00+01:00",
    )
    payload = proof.to_dict()

    assert payload["write_executed"] is True
    assert payload["writes_artifacts"] is True
    assert len(payload["writes"]) == 1
    rel_path = payload["writes"][0]
    assert rel_path.startswith("07_LOGS/Pulse-Decks/personal-map-apply-transactions/")
    written = json.loads((vault / rel_path).read_text(encoding="utf-8"))
    assert written["transaction_status"] == "transaction_proof_ready"
    assert written["live_apply_allowed"] is False
    assert written["writes_runtime_memory_graph"] is False
    assert written["canonical_writeback_allowed"] is False


def test_transaction_proof_write_guard_rejects_outside_root(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    with pytest.raises(ValueError, match="must be written under"):
        write_personal_map_apply_transaction_proof(
            vault,
            output_path="07_LOGS/not-personal-map-transaction.json",
        )


def test_current_repo_transaction_proof_has_no_apply_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    proof = build_personal_map_apply_transaction_proof(vault)
    payload = proof.to_dict()

    assert payload["transaction_status"] in {
        "blocked_no_ready_personal_map_candidates",
        "transaction_proof_ready",
    }
    assert payload["live_apply_allowed"] is False
    assert payload["applies_personal_map_candidates"] is False
    assert payload["writes_runtime_memory_graph"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert payload["rd_workbook_update_allowed"] is False
