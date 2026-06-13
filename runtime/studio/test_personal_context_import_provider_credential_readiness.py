"""Tests for Personal Context Import provider credential readiness surface."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.studio.personal_context_import_provider_credential_readiness import (
    APPROVAL_CLASS,
    MODEL_VERSION,
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    SURFACE_ID,
    _PROVIDERS,
    build_personal_context_import_provider_credential_readiness,
    compute_provider_credential_readiness_digest,
    format_personal_context_import_provider_credential_readiness,
    request_personal_context_import_provider_credential_readiness_approval,
)


# --- Helpers ---

def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


def _env_with_key() -> dict[str, str]:
    return {**os.environ, "OPENAI_API_KEY": "test-key-present"}


def _env_without_key() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}


# --- Basic contract ---

def test_readiness_ok(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_credential_readiness(vault)
    assert result["ok"] is True
    assert result["surface"] == SURFACE_ID
    assert result["model_version"] == MODEL_VERSION
    assert result["pass"] == PASS_ID


def test_readiness_providers_listed(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_credential_readiness(vault)
    provider_ids = {p["provider_id"] for p in result["provider_states"]}
    for p in _PROVIDERS:
        assert p["provider_id"] in provider_ids


def test_readiness_key_present(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        result = build_personal_context_import_provider_credential_readiness(vault)
    openai_state = next(p for p in result["provider_states"] if p["provider_id"] == "openai")
    assert openai_state["credential_present"] is True
    assert openai_state["status"] == "credential_present"
    assert result["required_credentials_present"] is True
    assert result["status"] in {"all_credentials_present", "required_credentials_present_optional_missing"}


def test_readiness_key_absent(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        result = build_personal_context_import_provider_credential_readiness(vault)
    openai_state = next(p for p in result["provider_states"] if p["provider_id"] == "openai")
    assert openai_state["credential_present"] is False
    assert openai_state["status"] == "credential_missing"
    assert result["required_credentials_present"] is False
    assert "openai" in result["missing_required"]


def test_readiness_credential_blockers_when_key_absent(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        result = build_personal_context_import_provider_credential_readiness(vault)
    assert len(result["credential_blockers"]) > 0
    assert any("openai" in b.lower() for b in result["credential_blockers"])


def test_readiness_no_blockers_when_key_present(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        result = build_personal_context_import_provider_credential_readiness(vault)
    assert len(result["credential_blockers"]) == 0


def test_readiness_does_not_log_secret_value(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    secret = "test-key-very-secret-key-value"
    with patch.dict(os.environ, {"OPENAI_API_KEY": secret}, clear=False):
        result = build_personal_context_import_provider_credential_readiness(vault)
    result_str = str(result)
    assert secret not in result_str


def test_readiness_authority_no_values_read(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_credential_readiness(vault)
    auth = result["authority"]
    assert auth["reads_env_var_values"] is False
    assert auth["secret_values_read"] is False
    assert auth["provider_api_call_allowed"] is False
    assert auth["canonical_writeback_allowed"] is False


def test_readiness_digest_stable_no_key(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        r1 = build_personal_context_import_provider_credential_readiness(vault)
        r2 = build_personal_context_import_provider_credential_readiness(vault)
    assert r1["readiness_digest"] == r2["readiness_digest"]


def test_readiness_digest_differs_key_present_vs_absent(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        r_absent = build_personal_context_import_provider_credential_readiness(vault)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        r_present = build_personal_context_import_provider_credential_readiness(vault)
    assert r_absent["readiness_digest"] != r_present["readiness_digest"]


def test_readiness_next_pass(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_credential_readiness(vault)
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_readiness_can_request_approval_always(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_credential_readiness(vault)
    assert result["can_request_approval"] is True


# --- Approval queueing ---

def test_request_approval_digest_mismatch(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = request_personal_context_import_provider_credential_readiness_approval(
        vault, expected_readiness_digest="wrong"
    )
    assert result["ok"] is False
    assert "readiness_digest_mismatch" in result["blockers"]


def test_request_approval_empty_digest(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = request_personal_context_import_provider_credential_readiness_approval(
        vault, expected_readiness_digest=""
    )
    assert result["ok"] is False
    assert "expected_readiness_digest_required" in result["blockers"]


def test_request_approval_success(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    readiness = build_personal_context_import_provider_credential_readiness(vault)
    digest = readiness["readiness_digest"]
    result = request_personal_context_import_provider_credential_readiness_approval(
        vault, expected_readiness_digest=digest
    )
    assert result["ok"] is True
    assert result["approval_queued"] is True
    assert result["approval_id"]
    assert result["readiness_digest"] == digest


def test_request_approval_idempotent(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    readiness = build_personal_context_import_provider_credential_readiness(vault)
    digest = readiness["readiness_digest"]
    r1 = request_personal_context_import_provider_credential_readiness_approval(
        vault, expected_readiness_digest=digest
    )
    r2 = request_personal_context_import_provider_credential_readiness_approval(
        vault, expected_readiness_digest=digest
    )
    assert r1["approval_id"] == r2["approval_id"]
    assert r2.get("approval_already_exists") is True


# --- Format ---

def test_format_output(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = build_personal_context_import_provider_credential_readiness(vault)
    text = format_personal_context_import_provider_credential_readiness(result)
    assert "Status:" in text
    assert "Readiness digest:" in text
    assert "Required credentials present:" in text
    assert "Next recommended pass:" in text


def test_format_shows_blockers_when_key_absent(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        result = build_personal_context_import_provider_credential_readiness(vault)
    text = format_personal_context_import_provider_credential_readiness(result)
    assert "Credential blockers:" in text
