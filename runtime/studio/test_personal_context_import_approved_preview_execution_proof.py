"""Tests for the approved personal context import preview execution proof."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.personal_context_import_approved_preview_execution_proof import (
    NEXT_RECOMMENDED_PASS,
    SURFACE_ID,
    execute_personal_context_import_approved_preview_execution_proof,
)
from runtime.studio.personal_context_import_preview_writer import (
    build_personal_context_import_preview_writer,
)
from runtime.studio.service import StudioService, StudioServiceError
from runtime.studio.test_personal_context_import_preview_writer import SOURCE_TEXT


def _queue_context_import_preview(root: Path) -> dict:
    preview = build_personal_context_import_preview_writer(root, source_text=SOURCE_TEXT, operator_id="test")
    digest = str(preview["digest_proof"]["import_preview_digest"])
    queued = build_personal_context_import_preview_writer(
        root,
        source_text=SOURCE_TEXT,
        expected_import_preview_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    return {
        "approval_id": queued["approval_record"]["approval_id"],
        "digest": digest,
        "source_digest": preview["digest_proof"]["source_digest_sha256"],
        "queued": queued,
    }


def _approval_statement(digest: str) -> str:
    return f"approve personal context import preview execution {digest}"


def test_execution_requires_execute_flag_before_artifact_writes(tmp_path: Path) -> None:
    queued = _queue_context_import_preview(tmp_path)

    result = execute_personal_context_import_approved_preview_execution_proof(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_import_preview_digest=queued["digest"],
        source_text=SOURCE_TEXT,
        operator_approval_statement=_approval_statement(queued["digest"]),
        operator_id="test",
        execute=False,
    )

    assert result["ok"] is False
    assert "execute_flag_required" in result["blocked_reasons"]
    assert result["exact_once_marker"]["marker_written"] is False
    assert not (tmp_path / "03_INPUTS" / "Personal-Context-Intake").exists()
    assert not (tmp_path / "07_LOGS" / "Pulse-Decks" / "memory-candidates" / "personal-map").exists()


def test_execution_consumes_pending_approval_and_writes_review_artifacts_only(tmp_path: Path) -> None:
    queued = _queue_context_import_preview(tmp_path)

    result = execute_personal_context_import_approved_preview_execution_proof(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_import_preview_digest=queued["digest"],
        source_text=SOURCE_TEXT,
        operator_approval_statement=_approval_statement(queued["digest"]),
        operator_id="test",
        execute=True,
    )

    marker_path = tmp_path / result["exact_once_marker"]["marker_path"]
    approval_path = tmp_path / StudioService.APPROVAL_DIR / f"{queued['approval_id']}.json"
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    raw_source = tmp_path / result["artifact_writes"]["artifact_paths"]["raw_context_source"]
    candidate_log = tmp_path / result["artifact_writes"]["artifact_paths"]["personal_map_candidate_log"]
    evidence = tmp_path / result["artifact_writes"]["artifact_paths"]["execution_evidence"]

    assert result["ok"] is True
    assert result["surface"] == SURFACE_ID
    assert result["status"] == "COMPLETE / APPROVED-PREVIEW ARTIFACTS WRITTEN / CANONICAL WRITES BLOCKED"
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["operator_approval_recorded_from_statement"] is True
    assert result["summary"]["exact_once_marker_written"] is True
    assert result["summary"]["raw_context_file_written"] is True
    assert result["summary"]["personal_map_candidate_log_written"] is True
    assert result["summary"]["personal_map_applied"] is False
    assert result["summary"]["dashboard_updated"] is False
    assert result["summary"]["knowledge_index_updated"] is False
    assert result["summary"]["node_files_created"] is False
    assert result["summary"]["canonical_mutation_performed"] is False
    assert result["summary"]["runtime_memory_mutated"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result["digest_proof"]["import_preview_digest_matched"] is True
    assert result["digest_proof"]["source_digest_matched"] is True
    assert marker_path.exists()
    assert raw_source.exists()
    assert SOURCE_TEXT.strip() in raw_source.read_text(encoding="utf-8")
    assert candidate_log.exists()
    assert evidence.exists()
    assert approval_payload["status"] == "executed"
    assert approval_payload["execution_status"] == "completed"
    assert approval_payload["action_spec"]["metadata"]["approval_consumed"] is True
    assert approval_payload["action_spec"]["metadata"]["source_digest_matched"] is True
    assert approval_payload["action_spec"]["metadata"]["canonical_mutation_performed"] is False
    assert not (tmp_path / "00_HOME").exists()
    assert not (tmp_path / "01_PROJECTS").exists()
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "06_AGENTS").exists()


def test_wrong_digest_or_source_blocks_without_marker_or_artifacts(tmp_path: Path) -> None:
    queued = _queue_context_import_preview(tmp_path)

    wrong_digest = execute_personal_context_import_approved_preview_execution_proof(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_import_preview_digest="wrong-digest",
        source_text=SOURCE_TEXT,
        operator_approval_statement="approve personal context import preview execution wrong-digest",
        operator_id="test",
        execute=True,
    )
    wrong_source = execute_personal_context_import_approved_preview_execution_proof(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_import_preview_digest=queued["digest"],
        source_text="Different personal context without matching digest.",
        operator_approval_statement=_approval_statement(queued["digest"]),
        operator_id="test",
        execute=True,
    )

    assert wrong_digest["ok"] is False
    assert "expected_import_preview_digest_mismatch" in wrong_digest["blocked_reasons"]
    assert wrong_digest["exact_once_marker"]["marker_written"] is False
    assert wrong_source["ok"] is False
    assert "source_digest_mismatch" in wrong_source["blocked_reasons"]
    assert not (tmp_path / "03_INPUTS" / "Personal-Context-Intake").exists()


def test_secret_like_source_blocks_execution_without_echoing_secret(tmp_path: Path) -> None:
    queued = _queue_context_import_preview(tmp_path)
    secret = "test-key-abcdefghijklmnopqrstuvwxyz123456"

    result = execute_personal_context_import_approved_preview_execution_proof(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_import_preview_digest=queued["digest"],
        source_text=f"{SOURCE_TEXT}\napi_key={secret}",
        operator_approval_statement=_approval_statement(queued["digest"]),
        operator_id="test",
        execute=True,
    )

    encoded = json.dumps(result)
    assert result["ok"] is False
    assert "secret_or_credential_indicator_present" in result["blocked_reasons"]
    assert secret not in encoded
    assert "[REDACTED_SECRET]" not in encoded
    assert not (tmp_path / "03_INPUTS" / "Personal-Context-Intake").exists()


def test_duplicate_execution_blocks_before_second_artifact_write(tmp_path: Path) -> None:
    queued = _queue_context_import_preview(tmp_path)
    first = execute_personal_context_import_approved_preview_execution_proof(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_import_preview_digest=queued["digest"],
        source_text=SOURCE_TEXT,
        operator_approval_statement=_approval_statement(queued["digest"]),
        operator_id="test",
        execute=True,
    )
    raw_path = tmp_path / first["artifact_writes"]["artifact_paths"]["raw_context_source"]
    raw_bytes = raw_path.read_bytes()

    duplicate = execute_personal_context_import_approved_preview_execution_proof(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_import_preview_digest=queued["digest"],
        source_text=SOURCE_TEXT,
        operator_approval_statement=_approval_statement(queued["digest"]),
        operator_id="test",
        execute=True,
    )

    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blocked_reasons"]
    assert duplicate["summary"]["duplicate_blocked_before_artifact_write"] is True
    assert raw_path.read_bytes() == raw_bytes


def test_ambient_studio_execution_still_blocks_and_api_registry_expose_executor(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    queued = _queue_context_import_preview(tmp_path)
    service = StudioService(tmp_path)
    service.approve(queued["approval_id"], reviewed_by="test")

    try:
        service.execute_approved(queued["approval_id"])
    except StudioServiceError as exc:
        error = str(exc)
    else:  # pragma: no cover
        error = ""

    api_result = StudioAPI(tmp_path).execute_personal_context_import_approved_preview_execution(
        queued["approval_id"],
        queued["digest"],
        SOURCE_TEXT,
        _approval_statement(queued["digest"]),
        operator_id="test",
    )
    registry = build_native_shell_panel_registry(tmp_path)
    context_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "context-import"), {})

    assert "Personal context import preview" in error
    assert api_result["ok"] is True
    assert api_result["surface"] == "personal_context_import_approved_preview_execution_proof"
    assert "get_personal_context_import_approved_preview_execution_proof" in (context_panel.get("api_methods") or [])
    assert "execute_personal_context_import_approved_preview_execution" in (context_panel.get("api_methods") or [])
    assert "get_personal_context_import_multi_instance_fixture_harness" in (context_panel.get("api_methods") or [])
    assert "personal_context_import_review_artifacts" in (context_panel.get("possible_writes") or [])
    assert "personal_context_import_fixture_harness_temp_artifacts" in (context_panel.get("possible_writes") or [])
    assert registry["readiness"]["personal_context_import_approved_preview_execution_proof_ready"] is True
    assert registry["readiness"]["personal_context_import_multi_instance_fixture_harness_ready"] is True
