"""
runtime/tests/test_doctor_hardening.py

Tests for L-3 (credential literal scan) and P-D1 (protected files sync)
doctor checks added to _build_cli_doctor_payload().
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers pulled directly from the module under test
# ---------------------------------------------------------------------------
from runtime.cli.main import (
    _ALLOWED_CREDENTIAL_RE,
    _CREDENTIAL_KEY_FRAGMENTS,
    _SAFE_POLICY_STRINGS,
    _SNAKE_CASE_IDENTIFIER_RE,
    _TEMPLATE_PLACEHOLDER_RE,
    _check_credential_literals,
    _check_protected_files_sync,
    _is_allowed_credential_value,
    _is_credential_key,
    _walk_yaml_values,
)


# ===========================================================================
# L-3 — credential literal scanner
# ===========================================================================


class TestSafePolicyStrings:
    def test_constant_is_frozenset(self):
        assert isinstance(_SAFE_POLICY_STRINGS, frozenset)

    @pytest.mark.parametrize("value", [
        "none", "forbidden", "required", "optional", "allowed", "blocked",
        "restricted", "disabled", "enabled", "operator", "audit",
    ])
    def test_policy_enums_are_allowed(self, value):
        assert _is_allowed_credential_value(value) is True

    def test_case_insensitive_safe_check(self):
        assert _is_allowed_credential_value("FORBIDDEN") is True
        assert _is_allowed_credential_value("None") is True

    def test_actual_secrets_not_in_safe_set(self):
        assert _is_allowed_credential_value("hunter2") is False
        assert _is_allowed_credential_value("test-key-abc123") is False


class TestSnakeCaseIdentifierRe:
    def test_constant_is_pattern(self):
        import re as _re
        assert isinstance(_SNAKE_CASE_IDENTIFIER_RE, _re.Pattern)

    @pytest.mark.parametrize("value", [
        "discord_draft_webhook_reference",
        "calendar_oauth_reference",
        "webhook_auth_reference",
        "exchange_api_key_reference",
        "my_secret_ref",
    ])
    def test_snake_case_references_are_allowed(self, value):
        assert _is_allowed_credential_value(value) is True

    @pytest.mark.parametrize("value", [
        "hunter2",          # no underscore
        "test-key-abc123",        # has hyphen
        "test-test-xox-b-token-token-token-here",  # has hyphens
        "Pass1word",        # mixed case, no underscore
    ])
    def test_non_snake_case_still_flagged(self, value):
        assert _is_allowed_credential_value(value) is False


class TestCredentialKeyFragments:
    def test_constant_is_frozenset(self):
        assert isinstance(_CREDENTIAL_KEY_FRAGMENTS, frozenset)

    def test_contains_expected_fragments(self):
        for frag in ("api_key", "token", "webhook", "password", "client_secret", "private_key", "secret"):
            assert frag in _CREDENTIAL_KEY_FRAGMENTS


class TestWalkYamlValues:
    def test_flat_dict(self):
        pairs = dict(_walk_yaml_values({"a": 1, "b": "x"}))
        assert pairs["a"] == 1
        assert pairs["b"] == "x"

    def test_nested_dict(self):
        pairs = dict(_walk_yaml_values({"outer": {"inner": "val"}}))
        assert pairs["outer.inner"] == "val"

    def test_list_items(self):
        pairs = dict(_walk_yaml_values({"items": [10, 20]}))
        assert pairs["items[0]"] == 10
        assert pairs["items[1]"] == 20

    def test_none_obj_returns_single_pair(self):
        pairs = _walk_yaml_values(None, prefix="x")
        assert pairs == [("x", None)]

    def test_empty_dict_returns_empty(self):
        assert _walk_yaml_values({}) == []


class TestIsCredentialKey:
    @pytest.mark.parametrize("key", [
        "api_key", "token", "password", "client_secret", "private_key", "webhook", "secret",
        "auth.api_key", "config.webhook_url", "outer.inner.token",
    ])
    def test_sensitive_keys_detected(self, key):
        assert _is_credential_key(key) is True

    @pytest.mark.parametrize("key", [
        "url", "host", "port", "name", "description", "enabled", "timeout",
        "task_type", "role_card", "status",
    ])
    def test_benign_keys_not_detected(self, key):
        assert _is_credential_key(key) is False


class TestIsAllowedCredentialValue:
    @pytest.mark.parametrize("value", [
        None, True, False, 0, 42, 3.14,
        "PERPLEXITY_API_KEY",          # env var name
        "DISCORD_WEBHOOK_URL",
        "XAI_API_KEY",
        "MY_SECRET_KEY",
        "${API_KEY}",                  # template placeholder
        "env:MY_TOKEN",
        "<REPLACE_WITH_API_KEY>",
        "REPLACE_ME",
        "...",
        "",
        "   ",
    ])
    def test_allowed_values(self, value):
        assert _is_allowed_credential_value(value) is True

    @pytest.mark.parametrize("value", [
        "test-key-abc123",
        "test-test-xox-b-token-token-slack-token-here",
        "some-literal-webhook-url",
        "hunter2",
        "actualpassword123",
    ])
    def test_literal_values_flagged(self, value):
        assert _is_allowed_credential_value(value) is False


class TestCheckCredentialLiterals:
    def _make_vault(self, tmp_path: Path) -> Path:
        (tmp_path / "runtime").mkdir()
        return tmp_path

    def test_clean_vault_passes(self, tmp_path):
        vault = self._make_vault(tmp_path)
        clean_yaml = vault / "runtime" / "clean.yaml"
        clean_yaml.write_text(
            "name: my_workflow\napi_key: PERPLEXITY_API_KEY\ntoken: MY_TOKEN\n",
            encoding="utf-8",
        )
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        assert len(checks) == 1
        check = checks[0]
        assert check["name"] == "credential literal scan"
        assert check["ok"] is True
        assert check["severity"] == "warning"

    def test_literal_credential_produces_warning(self, tmp_path):
        vault = self._make_vault(tmp_path)
        bad_yaml = vault / "runtime" / "bad.yaml"
        bad_yaml.write_text("name: cfg\napi_key: test-key-actual-secret\n", encoding="utf-8")
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        check = checks[0]
        assert check["ok"] is False
        assert check["severity"] == "warning"
        assert "bad.yaml" in check["detail"]

    def test_underscore_files_skipped(self, tmp_path):
        vault = self._make_vault(tmp_path)
        schema_yaml = vault / "runtime" / "_schema.yaml"
        schema_yaml.write_text("api_key: actual-literal\n", encoding="utf-8")
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        # _schema.yaml is skipped — no flagged hits
        assert checks[0]["ok"] is True

    def test_nested_literal_detected(self, tmp_path):
        vault = self._make_vault(tmp_path)
        nested_yaml = vault / "runtime" / "nested.yaml"
        nested_yaml.write_text(
            "outer:\n  inner:\n    api_key: not-an-env-var\n",
            encoding="utf-8",
        )
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        assert checks[0]["ok"] is False
        assert "nested.yaml" in checks[0]["detail"]

    def test_missing_runtime_dir_skips_cleanly(self, tmp_path):
        # No runtime/ dir at all
        checks: list[dict] = []
        _check_credential_literals(tmp_path, checks)
        assert len(checks) == 1
        assert checks[0]["severity"] == "warning"

    def test_empty_yaml_file_is_harmless(self, tmp_path):
        vault = self._make_vault(tmp_path)
        empty_yaml = vault / "runtime" / "empty.yaml"
        empty_yaml.write_text("", encoding="utf-8")
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        assert checks[0]["ok"] is True

    def test_non_string_literal_not_flagged(self, tmp_path):
        vault = self._make_vault(tmp_path)
        num_yaml = vault / "runtime" / "nums.yaml"
        num_yaml.write_text("token: 0\napi_key: 3.14\n", encoding="utf-8")
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        assert checks[0]["ok"] is True

    def test_many_hits_truncated_in_detail(self, tmp_path):
        vault = self._make_vault(tmp_path)
        lines = "\n".join(f"key_{i}_api_key: literal-secret-{i}" for i in range(10))
        (vault / "runtime" / "many.yaml").write_text(lines, encoding="utf-8")
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        check = checks[0]
        assert check["ok"] is False
        assert "10 hit(s)" in check["detail"]

    def test_check_name_is_credential_literal_scan(self, tmp_path):
        vault = self._make_vault(tmp_path)
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        assert checks[0]["name"] == "credential literal scan"

    def test_policy_enum_values_not_flagged(self, tmp_path):
        """Values like 'forbidden'/'none'/'required' in credential-keyed fields must not warn."""
        vault = self._make_vault(tmp_path)
        policy_yaml = vault / "runtime" / "secret_policy.yaml"
        policy_yaml.write_text(
            "secret_policy:\n  session_tokens: forbidden\n  allowed_secret_material: none\n",
            encoding="utf-8",
        )
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        assert checks[0]["ok"] is True

    def test_real_vault_scan_is_clean(self):
        """Integration: the real vault must have no literal credential warnings."""
        import os
        vault = Path(os.environ.get("CHASEOS_VAULT_ROOT", "C:/Users/chaseos/Documents/chaseos_obsidian"))
        if not (vault / "runtime").is_dir():
            pytest.skip("Real vault not available in this environment")
        checks: list[dict] = []
        _check_credential_literals(vault, checks)
        check = checks[0]
        assert check["ok"] is True, f"Real vault credential scan flagged: {check['detail']}"


# ===========================================================================
# P-D1 — protected files sync
# ===========================================================================


def _make_protected_yaml(path: Path, files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"protected_files": files}
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


def _make_permission_matrix(path: Path, files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(f"| `{f}` | Protected reason |" for f in files)
    # Use string concat (not textwrap.dedent + f-string) to avoid indentation
    # artifacts that would break the \n--- section-boundary regex.
    content = (
        "# Permission Matrix\n\n"
        "## Section 2 — Target File Categories\n\n"
        "### Protected Files\n\n"
        "These files require explicit user approval before any edit:\n\n"
        "| File | Why Protected |\n"
        "|------|--------------|\n"
        f"{rows}\n\n"
        "---\n\n"
        "### Standard Content Files\n\n"
        "Other content with `backtick` values in other tables must not be matched.\n\n"
        "| Value | Meaning |\n"
        "|-------|--------|\n"
        "| `none` | Not a file path |\n"
        "| `git commit` | Not a file path |\n"
    )
    path.write_text(content, encoding="utf-8")


class TestCheckProtectedFilesSync:
    def _paths(self, vault: Path):
        yaml_path = vault / "runtime" / "policy" / "protected_files.yaml"
        matrix_path = vault / "06_AGENTS" / "Permission-Matrix.md"
        return yaml_path, matrix_path

    def test_in_sync_passes(self, tmp_path):
        files = ["SOUL.md", "README.md", "ROADMAP.md"]
        yaml_path, matrix_path = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, files)
        _make_permission_matrix(matrix_path, files)
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        check = checks[0]
        assert check["name"] == "protected files sync"
        assert check["ok"] is True

    def test_in_sync_detail_includes_count(self, tmp_path):
        files = ["SOUL.md", "README.md"]
        yaml_path, matrix_path = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, files)
        _make_permission_matrix(matrix_path, files)
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        assert "2 files" in checks[0]["detail"]

    def test_yaml_has_extra_file(self, tmp_path):
        yaml_path, matrix_path = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, ["SOUL.md", "README.md", "EXTRA.md"])
        _make_permission_matrix(matrix_path, ["SOUL.md", "README.md"])
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        check = checks[0]
        assert check["ok"] is False
        assert "EXTRA.md" in check["detail"]
        assert "in YAML not Matrix" in check["detail"]

    def test_matrix_has_extra_file(self, tmp_path):
        yaml_path, matrix_path = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, ["SOUL.md"])
        _make_permission_matrix(matrix_path, ["SOUL.md", "BONUS.md"])
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        check = checks[0]
        assert check["ok"] is False
        assert "BONUS.md" in check["detail"]
        assert "in Matrix not YAML" in check["detail"]

    def test_both_drift_directions_reported(self, tmp_path):
        yaml_path, matrix_path = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, ["SOUL.md", "YAML_ONLY.md"])
        _make_permission_matrix(matrix_path, ["SOUL.md", "MATRIX_ONLY.md"])
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        check = checks[0]
        assert check["ok"] is False
        assert "YAML_ONLY.md" in check["detail"]
        assert "MATRIX_ONLY.md" in check["detail"]

    def test_missing_yaml_produces_error(self, tmp_path):
        _, matrix_path = self._paths(tmp_path)
        _make_permission_matrix(matrix_path, ["SOUL.md"])
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        assert checks[0]["ok"] is False
        assert "protected_files.yaml not found" in checks[0]["detail"]

    def test_missing_matrix_produces_error(self, tmp_path):
        yaml_path, _ = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, ["SOUL.md"])
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        assert checks[0]["ok"] is False
        assert "Permission-Matrix.md not found" in checks[0]["detail"]

    def test_real_vault_files_are_in_sync(self):
        """Integration: verify the real vault protected_files.yaml matches Permission-Matrix.md."""
        import os
        vault = Path(os.environ.get("CHASEOS_VAULT_ROOT", "C:/Users/chaseos/Documents/chaseos_obsidian"))
        yaml_path = vault / "runtime" / "policy" / "protected_files.yaml"
        matrix_path = vault / "06_AGENTS" / "Permission-Matrix.md"
        if not yaml_path.exists() or not matrix_path.exists():
            pytest.skip("Real vault files not available in this environment")
        checks: list[dict] = []
        _check_protected_files_sync(vault, checks)
        check = checks[0]
        assert check["ok"] is True, f"Real vault drift: {check['detail']}"

    def test_check_name_is_protected_files_sync(self, tmp_path):
        yaml_path, matrix_path = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, ["SOUL.md"])
        _make_permission_matrix(matrix_path, ["SOUL.md"])
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        assert checks[0]["name"] == "protected files sync"

    def test_empty_yaml_list_no_matrix_entries_is_in_sync(self, tmp_path):
        yaml_path, matrix_path = self._paths(tmp_path)
        _make_protected_yaml(yaml_path, [])
        _make_permission_matrix(matrix_path, [])
        checks: list[dict] = []
        _check_protected_files_sync(tmp_path, checks)
        assert checks[0]["ok"] is True
