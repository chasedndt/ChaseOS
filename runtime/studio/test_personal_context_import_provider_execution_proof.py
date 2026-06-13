"""Tests for Personal Context Import provider execution proof surface."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from runtime.studio.personal_context_import_provider_execution_proof import (
    MODEL_VERSION,
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    SURFACE_ID,
    STATUS_CREDENTIAL_BLOCKER,
    STATUS_PROOF_PREVIEW,
    STATUS_PROOF_COMPLETE,
    STATUS_PROOF_FAILED,
    _build_call_structure,
    _build_unblock_packet,
    build_personal_context_import_provider_execution_proof,
    format_personal_context_import_provider_execution_proof,
)


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


# --- Call structure ---

def test_call_structure_no_key_value(tmp_path: Path) -> None:
    structure = _build_call_structure()
    assert "OPENAI_API_KEY" in structure["auth_header"]
    assert "value not shown" in structure["auth_header"]
    assert structure["endpoint"].startswith("https://")
    assert structure["model"]
    assert len(structure["messages"]) >= 2


def test_call_structure_does_not_contain_env_value(tmp_path: Path) -> None:
    secret = "test-key-secret-test-value"
    with patch.dict(os.environ, {"OPENAI_API_KEY": secret}, clear=False):
        structure = _build_call_structure()
    assert secret not in str(structure)


# --- Unblock packet ---

def test_unblock_packet_structure(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    packet = _build_unblock_packet(vault)
    assert packet["blocker_type"] == "operator_credential_required"
    assert packet["required_env_var"] == "OPENAI_API_KEY"
    assert "action_required" in packet
    assert "call_structure_preview" in packet


# --- Build proof: key absent ---

def test_proof_credential_blocker_when_key_absent(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    assert result["ok"] is False
    assert result["status"] == STATUS_CREDENTIAL_BLOCKER
    assert result["credential_present"] is False
    assert result["provider_call_executed"] is False
    assert result["unblock_packet"] is not None


def test_proof_credential_blocker_has_instructions(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    up = result["unblock_packet"]
    assert up["required_env_var"] == "OPENAI_API_KEY"
    assert "call_structure_preview" in up


def test_proof_credential_blocker_does_not_log_secret(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    assert "sk-" not in str(result)


# --- Build proof: key present, execute=False ---

def test_proof_preview_when_key_present_execute_false(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    assert result["ok"] is True
    assert result["status"] == STATUS_PROOF_PREVIEW
    assert result["credential_present"] is True
    assert result["provider_call_executed"] is False
    assert result["unblock_packet"] is None


def test_proof_preview_call_structure_present(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    assert "call_structure" in result
    assert result["call_structure"]["endpoint"].startswith("https://")


def test_proof_preview_does_not_expose_key(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    secret = "test-key-my-test-secret-value"
    with patch.dict(os.environ, {"OPENAI_API_KEY": secret}, clear=False):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    assert secret not in str(result)


# --- Build proof: key present, execute=True, no statement ---

def test_proof_blocked_execute_true_no_statement(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        result = build_personal_context_import_provider_execution_proof(
            vault, execute=True, operator_approval_statement=""
        )
    assert result["ok"] is True  # still ok because key present, just not executed
    assert result["status"] == STATUS_PROOF_PREVIEW
    assert "operator_approval_statement_required" in (result.get("blocked_reasons") or [])


def test_proof_blocked_execute_true_weak_statement(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        result = build_personal_context_import_provider_execution_proof(
            vault, execute=True, operator_approval_statement="I allow this"
        )
    assert result["status"] == STATUS_PROOF_PREVIEW
    assert any("approve" in r or "statement" in r for r in (result.get("blocked_reasons") or []))


# --- Build proof: key present, execute=True, valid statement, mocked API ---

def test_proof_execute_success_with_mocked_api(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id":"chatcmpl-test","choices":[{"message":{"content":"Received."},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":5},"model":"gpt-4o-mini"}'
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with (
        patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False),
        patch("urllib.request.urlopen", return_value=mock_response),
    ):
        result = build_personal_context_import_provider_execution_proof(
            vault,
            execute=True,
            operator_approval_statement="I approve provider execution proof for personal context.",
        )
    assert result["ok"] is True
    assert result["status"] == STATUS_PROOF_COMPLETE
    assert result["provider_call_executed"] is True
    call_result = result["provider_call_result"]
    assert call_result["ok"] is True
    assert "Received" in call_result["response_content"]


def test_proof_execute_failure_on_http_error(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    import urllib.error
    with (
        patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False),
        patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 401, "Unauthorized", {}, None)),
    ):
        result = build_personal_context_import_provider_execution_proof(
            vault,
            execute=True,
            operator_approval_statement="I approve provider execution proof for personal context.",
        )
    assert result["ok"] is False
    assert result["status"] == STATUS_PROOF_FAILED
    assert result["provider_call_result"]["ok"] is False
    assert "401" in result["provider_call_result"]["error"]


# --- Authority ---

def test_proof_authority_no_canonical_writes(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    auth = result["authority"]
    assert auth["canonical_writeback_allowed"] is False
    assert auth["secret_values_logged"] is False
    assert auth["personal_map_apply_allowed"] is False
    assert auth["agent_bus_dispatch_allowed"] is False


def test_proof_next_pass(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


# --- Format ---

def test_format_credential_blocker(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    text = format_personal_context_import_provider_execution_proof(result)
    assert "Status:" in text
    assert "CREDENTIAL BLOCKER" in text
    assert "OPENAI_API_KEY" in text


def test_format_proof_preview(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        result = build_personal_context_import_provider_execution_proof(vault, execute=False)
    text = format_personal_context_import_provider_execution_proof(result)
    assert "Status:" in text
    assert "Credential present:" in text
