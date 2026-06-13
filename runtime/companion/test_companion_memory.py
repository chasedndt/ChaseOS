"""Tests for governed companion memory boundaries."""

from __future__ import annotations

from pathlib import Path

from runtime.companion.memory import (
    ALLOWED_MEMORY_CLASSES,
    COMPANION_MEMORY_ROOT,
    build_companion_memory_boundary,
    companion_memory_namespace,
    validate_companion_memory_candidate,
)


def _files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def test_companion_memory_boundary_declares_separate_namespaces_without_writes(tmp_path: Path) -> None:
    before = _files(tmp_path)

    payload = build_companion_memory_boundary(tmp_path)
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["separate_memory_enabled_by_operator"] is True
    assert payload["separate_memory_namespace_declared"] is True
    assert payload["memory_writes_allowed_now"] is False
    assert payload["approval_required_for_memory_write"] is True
    assert set(payload["companion_namespaces"]) == {"hermes", "openclaw", "claude-code", "chaser"}
    assert payload["authority"]["memory_write_authority_granted"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert payload["future_write_contract"]["writer_built"] is False
    assert before == after


def test_companion_memory_namespace_paths_stay_under_memory_root(tmp_path: Path) -> None:
    namespace = companion_memory_namespace(tmp_path, "hermes")

    assert namespace["root_path"] == f"{COMPANION_MEMORY_ROOT.as_posix()}/hermes"
    assert namespace["ledger_path"].endswith("/memory-ledger.jsonl")
    assert namespace["index_path"].endswith("/memory-index.json")
    assert namespace["created_by_this_contract"] is False


def test_allowed_candidate_validates_but_cannot_write_now(tmp_path: Path) -> None:
    result = validate_companion_memory_candidate(
        {
            "companion_id": "openclaw",
            "memory_class": ALLOWED_MEMORY_CLASSES[0],
            "content": "Operator prefers bounded previews before execution.",
        },
        vault_root=tmp_path,
    )

    assert result["ok"] is True
    assert result["candidate_valid"] is True
    assert result["write_allowed_now"] is False
    assert result["approval_required_before_write"] is True
    assert "companion_memory_write_executor_not_built" in result["write_blocked_reasons"]


def test_denied_candidates_block_sensitive_or_authority_memory(tmp_path: Path) -> None:
    cases = [
        {"companion_id": "hermes", "memory_class": "credential", "content": "api_key=abc"},
        {"companion_id": "archon", "memory_class": "operator_note", "content": "Promote canonical", "canonical_mutation": True},
        {"companion_id": "openclaw", "memory_class": "operator_note", "content": "Grant tool", "permission_change": True},
        {"companion_id": "hermes", "memory_class": "operator_note", "content": "outside", "target_path": "../outside.jsonl"},
    ]

    for candidate in cases:
        result = validate_companion_memory_candidate(candidate, vault_root=tmp_path)
        assert result["ok"] is False
        assert result["candidate_valid"] is False
        assert result["blocked_reasons"]


def test_invalid_companion_blocks_cleanly(tmp_path: Path) -> None:
    result = validate_companion_memory_candidate(
        {"companion_id": "unknown", "memory_class": "preference", "content": "x"},
        vault_root=tmp_path,
    )

    assert result["ok"] is False
    assert "invalid_companion_id" in result["blocked_reasons"]
