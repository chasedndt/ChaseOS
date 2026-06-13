"""Tests for Personal Context Import canonical-promotion approval preview."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.personal_context_import_canonical_promotion_approval_preview import (
    NEXT_RECOMMENDED_PASS,
    SURFACE_ID,
    build_personal_context_import_canonical_promotion_approval_preview,
    format_personal_context_import_canonical_promotion_approval_preview,
)
from runtime.studio.service import StudioService, StudioServiceError
from runtime.studio.test_personal_context_import import _seed_import_ready_vault


def _files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def test_canonical_promotion_preview_lists_targets_without_canonical_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    before = _files(vault)

    payload = build_personal_context_import_canonical_promotion_approval_preview(vault)
    after = _files(vault)

    assert payload["ok"] is True
    assert payload["surface"] == SURFACE_ID
    assert payload["pass"] == "personal-context-import-canonical-promotion-approval-preview"
    assert payload["status"] == "READY / CANONICAL PROMOTION APPROVAL PREVIEW / CANONICAL WRITES BLOCKED"
    assert payload["summary"]["canonical_promotion_approval_preview_ready"] is True
    assert payload["summary"]["canonical_promotion_approval_request_created"] is False
    assert payload["summary"]["canonical_target_count"] >= 6
    assert payload["summary"]["protected_target_count"] >= 1
    assert payload["summary"]["canonical_writes_performed"] is False
    assert payload["summary"]["personal_map_apply_performed"] is False
    assert payload["summary"]["runtime_memory_mutation_performed"] is False
    assert payload["summary"]["agent_bus_task_written"] is False
    assert payload["summary"]["provider_call_performed"] is False
    assert payload["summary"]["credential_read_performed"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS

    packet = payload["canonical_promotion_packet_preview"]
    targets = {item["target_id"]: item for item in packet["canonical_target_plan"]}
    assert {"dashboard", "personal_operator_index", "operating_system", "projects_hub", "knowledge_index_master"} <= set(targets)
    assert packet["source_text_included"] is False
    assert packet["raw_full_memory_injection_allowed"] is False
    assert packet["canonical_writes_performed"] is False
    assert payload["authority"]["canonical_writes_allowed"] is False
    assert payload["authority"]["credential_reads_allowed"] is False
    assert before == after


def test_canonical_promotion_approval_requires_exact_digest_and_blocks_duplicates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    preview = build_personal_context_import_canonical_promotion_approval_preview(vault)
    digest = preview["digest_proof"]["canonical_promotion_digest"]

    mismatch = build_personal_context_import_canonical_promotion_approval_preview(
        vault,
        expected_canonical_promotion_digest="wrong",
        write_approval=True,
    )
    queued = build_personal_context_import_canonical_promotion_approval_preview(
        vault,
        expected_canonical_promotion_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    duplicate = build_personal_context_import_canonical_promotion_approval_preview(
        vault,
        expected_canonical_promotion_digest=digest,
        write_approval=True,
        operator_id="test",
    )

    assert mismatch["ok"] is False
    assert "expected_canonical_promotion_digest_mismatch" in mismatch["blocked_reasons"]
    assert queued["ok"] is True
    assert queued["summary"]["canonical_promotion_approval_request_created"] is True
    assert queued["approval_record"]["approval_id"]
    assert queued["approval_record"]["approval_path"]
    assert queued["approval_record"]["audit_path"]
    assert duplicate["ok"] is False
    assert "approval_queue_request_already_exists_for_digest" in duplicate["blocked_reasons"]


def test_canonical_promotion_approval_cannot_be_ambient_executed(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    preview = build_personal_context_import_canonical_promotion_approval_preview(vault)
    digest = preview["digest_proof"]["canonical_promotion_digest"]
    queued = build_personal_context_import_canonical_promotion_approval_preview(
        vault,
        expected_canonical_promotion_digest=digest,
        write_approval=True,
    )
    approval_id = queued["approval_record"]["approval_id"]
    service = StudioService(vault)
    service.approve(approval_id, reviewed_by="test")

    before = _files(vault)
    try:
        service.execute_approved(approval_id)
    except StudioServiceError as exc:
        message = str(exc)
    else:
        raise AssertionError("ambient canonical promotion execution should be blocked")
    after = _files(vault)

    assert "canonical-promotion approval requests" in message
    assert before == after


def test_canonical_promotion_preview_is_secret_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)

    payload = build_personal_context_import_canonical_promotion_approval_preview(vault)
    encoded = json.dumps(payload, sort_keys=True)

    assert "fixture-secret-not-returned" not in encoded
    assert "API_KEY" not in encoded.upper()
    assert payload["readiness"]["personal_context_import_credential_reads_blocked"] is True


def test_api_and_registry_expose_canonical_promotion_preview(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_result = StudioAPI(vault).get_personal_context_import_canonical_promotion_approval_preview()
    registry = build_native_shell_panel_registry(vault)
    context_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "context-import"), {})

    assert api_result["ok"] is True
    assert api_result["surface"] == "personal_context_import_canonical_promotion_approval_preview"
    assert api_result["data"]["readiness"]["personal_context_import_canonical_promotion_approval_preview_ready"] is True
    assert "get_personal_context_import_canonical_promotion_approval_preview" in (context_panel.get("api_methods") or [])
    assert "request_personal_context_import_canonical_promotion_approval" in (context_panel.get("api_methods") or [])
    assert registry["readiness"]["personal_context_import_canonical_promotion_approval_preview_ready"] is True


def test_format_canonical_promotion_preview_summarizes_deferred_effects(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    payload = build_personal_context_import_canonical_promotion_approval_preview(vault)

    text = format_personal_context_import_canonical_promotion_approval_preview(payload)

    assert "Personal Context Import Canonical Promotion Approval Preview" in text
    assert "Canonical writes performed: False" in text
    assert "Personal Map apply performed: False" in text
    assert "Provider call performed: False" in text
    assert "Credential read performed: False" in text
