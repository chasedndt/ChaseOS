"""Tests for the personal context import approval-preview writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.personal_context_import_preview_writer import (
    SURFACE_ID,
    build_personal_context_import_preview_writer,
)
from runtime.studio.service import StudioService, StudioServiceError


SOURCE_TEXT = """
ChaseOS personal OS context update:
- Identity doctrine, discipline, No Zero Days, and decision rules belong in SOUL and Principles.
- Interests include piano, geopolitics, history, and YouTube monetization linked to Content Creation OS.
- Language learning includes Mandarin / HSK 1.
- Technical work includes prompt engineering, agent engineering, runtime engineering, RAG, MCP, and source intelligence.
- University modules include Principles of Software Engineering in the Computer Science degree.
- Fitness, combat, physical discipline, networking, hardware, robotics, trading systems, cybersecurity, and full-stack work all need parent and child routes.
- Goals and preferences should become Personal Map candidates only after review.
"""


def _all_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def test_preview_extracts_parent_child_nodes_without_writes(tmp_path: Path) -> None:
    before = set(_all_files(tmp_path))

    payload = build_personal_context_import_preview_writer(
        tmp_path,
        source_text=SOURCE_TEXT,
        source_label="chatgpt-personal-context-export",
    )

    after = set(_all_files(tmp_path))
    proposal = payload["proposal_packet_preview"]
    node_ids = {item["rule_id"] for item in proposal["node_proposals"]}

    assert payload["ok"] is True
    assert payload["surface"] == SURFACE_ID
    assert payload["summary"]["queue_write_preview_ready"] is True
    assert payload["summary"]["approval_request_created"] is False
    assert payload["summary"]["source_text_included_in_approval_packet"] is False
    assert payload["digest_proof"]["import_preview_digest"]
    assert payload["secret_screen"]["contains_secret"] is False
    assert "prompt_engineering" in node_ids
    assert "agent_engineering" in node_ids
    assert "runtime_engineering" in node_ids
    assert "mandarin_hsk1" in node_ids
    assert "piano_interest" in node_ids
    assert "geopolitics_history_interest" in node_ids
    assert "content_creation_youtube_monetization" in node_ids
    assert payload["target_write_proof"]["target_file_written"] is False
    assert before == after


def test_approval_write_requires_exact_digest_and_preserves_no_raw_source(tmp_path: Path) -> None:
    preview = build_personal_context_import_preview_writer(tmp_path, source_text=SOURCE_TEXT)
    bad = build_personal_context_import_preview_writer(
        tmp_path,
        source_text=SOURCE_TEXT,
        expected_import_preview_digest="wrong",
        write_approval=True,
    )

    assert bad["ok"] is False
    assert "expected_import_preview_digest_mismatch" in bad["blocked_reasons"]
    assert bad["approval_queue_write"]["queue_writer_called"] is False
    assert not (tmp_path / StudioService.APPROVAL_DIR).exists()

    digest = preview["digest_proof"]["import_preview_digest"]
    written = build_personal_context_import_preview_writer(
        tmp_path,
        source_text=SOURCE_TEXT,
        expected_import_preview_digest=digest,
        write_approval=True,
    )
    approval_path = tmp_path / written["approval_record"]["approval_path"]
    audit_path = tmp_path / written["audit_record"]["audit_record_path"]
    encoded = json.dumps(written)
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))

    assert written["ok"] is True
    assert written["summary"]["approval_request_created"] is True
    assert approval_path.exists()
    assert audit_path.exists()
    assert SOURCE_TEXT.strip() not in encoded
    assert SOURCE_TEXT.strip() not in approval_path.read_text(encoding="utf-8")
    assert approval_payload["action_spec"]["metadata"]["personal_context_import_preview_writer"] is True
    assert approval_payload["action_spec"]["metadata"]["personal_context_import_preview_digest"] == digest
    assert written["target_write_proof"]["target_file_written"] is False
    assert not (tmp_path / written["target_write_proof"]["target_path"]).exists()


def test_secret_like_source_blocks_queue_write_and_does_not_echo_secret(tmp_path: Path) -> None:
    raw_secret = "test-key-abcdefghijklmnopqrstuvwxyz123456"
    payload = build_personal_context_import_preview_writer(
        tmp_path,
        source_text=f"Please import this profile with api_key={raw_secret} and Mandarin context.",
        expected_import_preview_digest="not-used",
        write_approval=True,
    )
    encoded = json.dumps(payload)

    assert payload["ok"] is False
    assert "secret_or_credential_indicator_present" in payload["blocked_reasons"]
    assert payload["secret_screen"]["contains_secret"] is True
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert raw_secret not in encoded
    assert "[REDACTED_SECRET]" not in encoded
    assert not (tmp_path / StudioService.APPROVAL_DIR).exists()


def test_ambient_studio_execution_blocks_import_preview_approval(tmp_path: Path) -> None:
    preview = build_personal_context_import_preview_writer(tmp_path, source_text=SOURCE_TEXT)
    digest = preview["digest_proof"]["import_preview_digest"]
    written = build_personal_context_import_preview_writer(
        tmp_path,
        source_text=SOURCE_TEXT,
        expected_import_preview_digest=digest,
        write_approval=True,
    )
    approval_id = written["approval_record"]["approval_id"]
    service = StudioService(tmp_path)
    service.approve(approval_id, reviewed_by="test")

    with pytest.raises(StudioServiceError, match="Personal context import preview"):
        service.execute_approved(approval_id)

    assert not (tmp_path / written["target_write_proof"]["target_path"]).exists()
    assert not (tmp_path / "03_INPUTS" / "Personal-Context-Intake").exists()


def test_api_and_registry_expose_context_import_preview_writer(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_personal_context_import_preview_writer(SOURCE_TEXT)
    registry = build_native_shell_panel_registry(tmp_path)
    context_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "context-import"), {})

    assert api_status["ok"] is True
    assert api_status["surface"] == "personal_context_import_preview_writer"
    assert api_status["data"]["summary"]["queue_write_preview_ready"] is True
    assert "get_personal_context_import_preview_writer" in (context_panel.get("api_methods") or [])
    assert "request_personal_context_import_preview" in (context_panel.get("api_methods") or [])
    assert "get_personal_context_import_approved_preview_execution_proof" in (context_panel.get("api_methods") or [])
    assert "execute_personal_context_import_approved_preview_execution" in (context_panel.get("api_methods") or [])
    assert "get_personal_context_import_multi_instance_fixture_harness" in (context_panel.get("api_methods") or [])
    assert registry["readiness"]["personal_context_import_preview_writer_ready"] is True
    assert registry["readiness"]["personal_context_import_approved_preview_execution_proof_ready"] is True
    assert registry["readiness"]["personal_context_import_multi_instance_fixture_harness_ready"] is True
    assert registry["readiness"]["personal_context_import_approval_queue_write_gated"] is True
