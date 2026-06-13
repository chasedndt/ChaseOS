"""Focused tests for Gate-adjacent provenance minimum checks."""

from __future__ import annotations

import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.chaseos_gate import check_provenance_minimums  # noqa: E402


def test_promoted_note_missing_provenance_minimums_is_blocked() -> None:
    allowed, reason = check_provenance_minimums(
        "02_KNOWLEDGE/AI-Agents/new-note.md",
        {
            "title": "New Note",
            "knowledge_class": "source-derived",
        },
    )

    assert allowed is False
    assert "verification_status" in reason


def test_promoted_note_with_minimum_provenance_is_allowed() -> None:
    allowed, reason = check_provenance_minimums(
        "02_KNOWLEDGE/AI-Agents/new-note.md",
        {
            "title": "New Note",
            "knowledge_class": "source-derived",
            "verification_status": "unverified",
            "promoted_from": "03_INPUTS/00_QUARANTINE/source/example.md",
        },
    )

    assert allowed is True
    assert "passed" in reason.lower()


def test_provenance_minimums_only_apply_to_relevant_paths() -> None:
    allowed, reason = check_provenance_minimums(
        "07_LOGS/Build-Logs/example.md",
        {},
    )

    assert allowed is True
    assert "not applicable" in reason.lower()
