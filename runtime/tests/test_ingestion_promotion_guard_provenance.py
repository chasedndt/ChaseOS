"""Focused tests for ingestion_promotion_guard provenance integration."""

from __future__ import annotations

import importlib.util
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
_HOOK_PATH = _VAULT_ROOT / ".claude" / "hooks" / "ingestion_promotion_guard.py"

_spec = importlib.util.spec_from_file_location("ingestion_promotion_guard", _HOOK_PATH)
assert _spec is not None and _spec.loader is not None
_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_guard)


def test_approved_knowledge_write_with_missing_provenance_is_blocked() -> None:
    allowed, reason = _guard.evaluate_write_request(
        write_target="02_KNOWLEDGE/AI-Agents/new-note.md",
        content="---\ntitle: New Note\nknowledge_class: source-derived\n---\n\n# New Note\n",
        promotion_approved=True,
    )

    assert allowed is False
    assert "verification_status" in reason


def test_approved_knowledge_write_with_minimum_provenance_is_allowed() -> None:
    allowed, reason = _guard.evaluate_write_request(
        write_target="02_KNOWLEDGE/AI-Agents/new-note.md",
        content=(
            "---\n"
            "title: New Note\n"
            "knowledge_class: source-derived\n"
            "verification_status: unverified\n"
            "promoted_from: 03_INPUTS/00_QUARANTINE/source/example.md\n"
            "---\n\n"
            "# New Note\n"
        ),
        promotion_approved=True,
    )

    assert allowed is True
    assert "passed" in reason.lower()


def test_non_knowledge_write_remains_not_applicable() -> None:
    allowed, reason = _guard.evaluate_write_request(
        write_target="07_LOGS/Build-Logs/example.md",
        content="# Example\n",
        promotion_approved=False,
    )

    assert allowed is True
    assert "not targeting" in reason.lower()
