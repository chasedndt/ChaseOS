"""Tests for Personal Context Import canonical-promotion approved executor."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.personal_context_import_canonical_promotion_approval_preview import (
    build_personal_context_import_canonical_promotion_approval_preview,
)
from runtime.studio.personal_context_import_canonical_promotion_approved_executor import (
    SURFACE_ID,
    execute_personal_context_import_canonical_promotion_approved_executor,
    format_personal_context_import_canonical_promotion_approved_executor,
)
from runtime.studio.service import StudioService
from runtime.studio.test_personal_context_import import _seed_import_ready_vault


CANONICAL_TARGETS = (
    "00_HOME/Dashboard.md",
    "00_HOME/Personal-Operator-Index.md",
    "00_HOME/Operating-System.md",
    "01_PROJECTS/Projects-Hub.md",
    "02_KNOWLEDGE/Knowledge-Index.md",
    "00_HOME/Personal-Domains/Personal-Domains-Index.md",
    "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md",
)


def _files(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def _queued_approval(vault: Path) -> tuple[str, str]:
    preview = build_personal_context_import_canonical_promotion_approval_preview(vault)
    digest = preview["digest_proof"]["canonical_promotion_digest"]
    queued = build_personal_context_import_canonical_promotion_approval_preview(
        vault,
        expected_canonical_promotion_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    return queued["approval_record"]["approval_id"], digest


def _statement(digest: str) -> str:
    return (
        "I approve personal context canonical promotion "
        f"{digest} including protected target 00_HOME/Operating-System.md."
    )


def test_canonical_promotion_executor_requires_execute_flag_and_exact_digest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    approval_id, digest = _queued_approval(vault)
    before = _files(vault)

    blocked = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest=digest,
        operator_approval_statement=_statement(digest),
        include_protected_targets=True,
        execute=False,
    )
    mismatch = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest="wrong",
        operator_approval_statement=_statement(digest),
        include_protected_targets=True,
        execute=True,
    )

    assert blocked["ok"] is False
    assert "execute_flag_required" in blocked["blocked_reasons"]
    assert mismatch["ok"] is False
    assert "expected_canonical_promotion_digest_mismatch" in mismatch["blocked_reasons"]
    assert before == _files(vault)


def test_canonical_promotion_executor_writes_managed_canonical_route_blocks(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    approval_id, digest = _queued_approval(vault)

    result = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest=digest,
        operator_approval_statement=_statement(digest),
        include_protected_targets=True,
        execute=True,
        operator_id="test",
    )

    assert result["ok"] is True
    assert result["surface"] == SURFACE_ID
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["canonical_writes_performed"] is True
    assert result["summary"]["personal_map_apply_performed"] is False
    assert result["summary"]["runtime_memory_mutation_performed"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["credential_read_performed"] is False
    assert result["exact_once_marker"]["marker_written"] is True
    assert result["canonical_writes"]["canonical_write_count"] == len(CANONICAL_TARGETS)
    assert set(result["canonical_writes"]["written_paths"]) == set(CANONICAL_TARGETS)
    assert result["evidence_record"]["evidence_written"] is True
    assert result["audit_record"]["audit_written"] is True

    marker = f"CHASEOS:PERSONAL-CONTEXT-CANONICAL-PROMOTION:{digest}:START"
    for rel_path in CANONICAL_TARGETS:
        text = (vault / rel_path).read_text(encoding="utf-8")
        assert marker in text
        assert "Personal Map apply performed: `false`" in text
        assert "Credential read performed: `false`" in text

    approval = StudioService(vault).get_approval(approval_id)
    assert approval is not None
    assert approval.status == "executed"
    assert approval.action_spec.metadata["canonical_writes_performed"] is True


def test_canonical_promotion_executor_blocks_duplicate_before_rewrite(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    approval_id, digest = _queued_approval(vault)
    first = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest=digest,
        operator_approval_statement=_statement(digest),
        include_protected_targets=True,
        execute=True,
    )
    before = _files(vault)

    duplicate = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest=digest,
        operator_approval_statement=_statement(digest),
        include_protected_targets=True,
        execute=True,
    )

    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blocked_reasons"]
    assert before == _files(vault)


def test_canonical_promotion_executor_requires_protected_target_flag(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    approval_id, digest = _queued_approval(vault)
    before = _files(vault)

    blocked = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest=digest,
        operator_approval_statement=_statement(digest),
        include_protected_targets=False,
        execute=True,
    )

    assert blocked["ok"] is False
    assert "protected_targets_require_explicit_flag" in blocked["blocked_reasons"]
    assert before == _files(vault)


def test_canonical_promotion_executor_is_secret_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    approval_id, digest = _queued_approval(vault)

    result = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest=digest,
        operator_approval_statement=_statement(digest),
        include_protected_targets=True,
        execute=True,
    )
    encoded = json.dumps(result, sort_keys=True)

    assert result["ok"] is True
    assert "fixture-secret-not-returned" not in encoded
    assert "API_KEY" not in encoded.upper()
    assert result["summary"]["credential_read_performed"] is False


def test_api_and_registry_expose_canonical_promotion_executor(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_result = StudioAPI(vault).get_personal_context_import_canonical_promotion_approved_executor()
    registry = build_native_shell_panel_registry(vault)
    context_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "context-import"), {})

    assert api_result["ok"] is True
    assert api_result["surface"] == "personal_context_import_canonical_promotion_approved_executor"
    assert api_result["data"]["ok"] is False
    assert "execute_flag_required" in api_result["data"]["blocked_reasons"]
    assert "get_personal_context_import_canonical_promotion_approved_executor" in (context_panel.get("api_methods") or [])
    assert "execute_personal_context_import_canonical_promotion_approved_executor" in (context_panel.get("api_methods") or [])
    assert registry["readiness"]["personal_context_import_canonical_promotion_approved_executor_ready"] is True


def test_format_canonical_promotion_executor_summarizes_boundaries(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    approval_id, digest = _queued_approval(vault)
    result = execute_personal_context_import_canonical_promotion_approved_executor(
        vault,
        approval_id=approval_id,
        expected_canonical_promotion_digest=digest,
        operator_approval_statement=_statement(digest),
        include_protected_targets=True,
        execute=True,
    )

    text = format_personal_context_import_canonical_promotion_approved_executor(result)

    assert "Personal Context Import Canonical Promotion Approved Executor" in text
    assert "Approval consumed: True" in text
    assert "Canonical write count: 7" in text
    assert "Personal Map apply performed: False" in text
    assert "Credential read performed: False" in text
