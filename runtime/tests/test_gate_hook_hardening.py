"""
test_gate_hook_hardening.py — Gate Hook Hardening Pass Tests (G-1, G-2, G-3)

Covers:
  G-1: protected_write_guard.py fail-closed on all policy load errors
  G-2: ingestion_promotion_guard.py fail-closed on stdin parse error + break-glass
  G-3: protected_write_guard.py separator-boundary path matching fix

All tests exercise the public API (evaluate_write_protection, is_protected,
load_protected_files, evaluate_write_request, is_gate_disabled) directly,
plus integration tests via main() subprocess calls to prove exit codes.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest import mock

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
_WRITE_GUARD_PATH = _VAULT_ROOT / ".claude" / "hooks" / "protected_write_guard.py"
_INGEST_GUARD_PATH = _VAULT_ROOT / ".claude" / "hooks" / "ingestion_promotion_guard.py"

# ---------------------------------------------------------------------------
# Module loaders — import hooks directly (avoids sys.path pollution)
# ---------------------------------------------------------------------------

def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"Could not load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_write_guard = _load_module(_WRITE_GUARD_PATH, "protected_write_guard")
_ingest_guard = _load_module(_INGEST_GUARD_PATH, "ingestion_promotion_guard")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_YAML = textwrap.dedent("""\
    protected_files:
      - SOUL.md
      - README.md
      - CLAUDE.md
      - 06_AGENTS/Permission-Matrix.md
      - 00_HOME/Principles.md
      - 00_HOME/Operating-System.md
      - 00_HOME/Assistant-Contract.md
      - PROJECT_FOUNDATION.md
      - ROADMAP.md
      - FORKING.md
      - 06_AGENTS/Agent-Control-Plane.md
      - 06_AGENTS/Trust-Tiers.md
      - 06_AGENTS/Handoff-Protocol.md
""")


def _make_payload(file_path: str, tool_name: str = "Write") -> str:
    return json.dumps({
        "session_id": "test-session",
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path, "content": "# test"},
    })


def _run_hook(hook_path: Path, stdin_data: str, env: dict | None = None) -> subprocess.CompletedProcess:
    merged_env = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(hook_path)],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=merged_env,
    )


# ===========================================================================
# G-1: protected_write_guard — fail-closed on policy load errors
# ===========================================================================

class TestWriteGuardPolicyLoadFailClosed:
    """G-1: Every policy load failure path must block writes (exit 2)."""

    def test_missing_yaml_file_returns_error(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.yaml"
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", nonexistent):
            files, error = _write_guard.load_protected_files()
        assert files == []
        assert error is not None
        assert "not found" in error.lower()

    def test_missing_yaml_file_verdict_is_policy_error(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.yaml"
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", nonexistent):
            result = _write_guard.load_protected_files()
            verdict, reason = _write_guard.evaluate_write_protection("SOUL.md", result)
        assert verdict == "policy_error"
        assert reason is not None

    def test_corrupt_yaml_returns_error(self, tmp_path):
        bad_yaml = tmp_path / "corrupt.yaml"
        bad_yaml.write_text("{{{{ not valid yaml ~~~~", encoding="utf-8")
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", bad_yaml):
            files, error = _write_guard.load_protected_files()
        assert files == []
        assert error is not None

    def test_corrupt_yaml_verdict_is_policy_error(self, tmp_path):
        bad_yaml = tmp_path / "corrupt.yaml"
        bad_yaml.write_text("{{{{ not valid yaml ~~~~", encoding="utf-8")
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", bad_yaml):
            result = _write_guard.load_protected_files()
            verdict, reason = _write_guard.evaluate_write_protection("SOUL.md", result)
        assert verdict == "policy_error"

    def test_yaml_missing_protected_files_key_returns_error(self, tmp_path):
        bad_yaml = tmp_path / "bad_structure.yaml"
        bad_yaml.write_text("something_else:\n  - foo\n", encoding="utf-8")
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", bad_yaml):
            files, error = _write_guard.load_protected_files()
        assert files == []
        assert error is not None
        assert "missing" in error.lower() or "protected_files" in error.lower()

    def test_yaml_empty_file_returns_error(self, tmp_path):
        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("", encoding="utf-8")
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", empty_yaml):
            files, error = _write_guard.load_protected_files()
        assert files == []
        assert error is not None

    def test_no_pyyaml_returns_error(self):
        with mock.patch.object(_write_guard, "YAML_AVAILABLE", False):
            files, error = _write_guard.load_protected_files()
        assert files == []
        assert error is not None
        assert "pyyaml" in error.lower() or "yaml" in error.lower()

    def test_policy_error_verdict_blocks_any_file(self, tmp_path):
        nonexistent = tmp_path / "missing.yaml"
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", nonexistent):
            result = _write_guard.load_protected_files()
        # Even a totally innocuous file should be blocked when policy load fails
        verdict, _ = _write_guard.evaluate_write_protection("07_LOGS/daily.md", result)
        assert verdict == "policy_error"

    def test_valid_yaml_loads_successfully(self, tmp_path):
        good_yaml = tmp_path / "good.yaml"
        good_yaml.write_text(_VALID_YAML, encoding="utf-8")
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", good_yaml):
            files, error = _write_guard.load_protected_files()
        assert error is None
        assert len(files) > 0
        assert any("SOUL.md" in str(f) for f in files)


# ===========================================================================
# G-3: protected_write_guard — separator-boundary path matching
# ===========================================================================

class TestWriteGuardPathMatching:
    """G-3: is_protected() must use separator-boundary suffix matching."""

    def _files(self, tmp_path: Path) -> tuple[list[Path], None]:
        good_yaml = tmp_path / "policy.yaml"
        good_yaml.write_text(_VALID_YAML, encoding="utf-8")
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", good_yaml):
            return _write_guard.load_protected_files()

    def test_exact_relative_match_is_protected(self, tmp_path):
        files, _ = self._files(tmp_path)
        assert _write_guard.is_protected("SOUL.md", files) is True

    def test_nested_path_suffix_match_is_protected(self, tmp_path):
        files, _ = self._files(tmp_path)
        # Absolute vault path should match the relative entry
        target = str(_VAULT_ROOT / "SOUL.md")
        assert _write_guard.is_protected(target, files) is True

    def test_nested_agent_file_match(self, tmp_path):
        files, _ = self._files(tmp_path)
        assert _write_guard.is_protected("06_AGENTS/Permission-Matrix.md", files) is True

    def test_nested_agent_file_absolute_path_match(self, tmp_path):
        files, _ = self._files(tmp_path)
        target = str(_VAULT_ROOT / "06_AGENTS" / "Permission-Matrix.md")
        assert _write_guard.is_protected(target, files) is True

    def test_false_positive_prevention_my_readme(self, tmp_path):
        """G-3 core fix: 'MY_README.md' must NOT match 'README.md'."""
        files, _ = self._files(tmp_path)
        assert _write_guard.is_protected("MY_README.md", files) is False

    def test_false_positive_prevention_prefix_soul(self, tmp_path):
        """'NOSOUL.md' must NOT match 'SOUL.md'."""
        files, _ = self._files(tmp_path)
        assert _write_guard.is_protected("NOSOUL.md", files) is False

    def test_false_positive_prevention_suffix_clause(self, tmp_path):
        """'SUBCLAUSE.md' must NOT match 'CLAUSE.md' (not in list, but tests boundary)."""
        files, _ = self._files(tmp_path)
        # README.md is in list
        assert _write_guard.is_protected("SUBREADME.md", files) is False

    def test_false_positive_prevention_path_prefix_overlap(self, tmp_path):
        """'99_README.md' must NOT match 'README.md'."""
        files, _ = self._files(tmp_path)
        assert _write_guard.is_protected("99_README.md", files) is False

    def test_unprotected_log_file_not_matched(self, tmp_path):
        files, _ = self._files(tmp_path)
        assert _write_guard.is_protected("07_LOGS/Build-Logs/2026-05-11-test.md", files) is False

    def test_unprotected_knowledge_file_not_matched(self, tmp_path):
        files, _ = self._files(tmp_path)
        assert _write_guard.is_protected("02_KNOWLEDGE/AI-Agents/new-note.md", files) is False

    def test_all_listed_protected_files_match(self, tmp_path):
        """Every file in _VALID_YAML must be detected as protected."""
        files, _ = self._files(tmp_path)
        protected_entries = [
            "SOUL.md", "README.md", "CLAUDE.md",
            "06_AGENTS/Permission-Matrix.md",
            "00_HOME/Principles.md",
            "00_HOME/Operating-System.md",
            "00_HOME/Assistant-Contract.md",
            "PROJECT_FOUNDATION.md", "ROADMAP.md", "FORKING.md",
            "06_AGENTS/Agent-Control-Plane.md",
            "06_AGENTS/Trust-Tiers.md",
            "06_AGENTS/Handoff-Protocol.md",
        ]
        for entry in protected_entries:
            assert _write_guard.is_protected(entry, files) is True, (
                f"Expected {entry!r} to be protected"
            )


# ===========================================================================
# G-1 + G-3: evaluate_write_protection — full verdict table
# ===========================================================================

class TestEvaluateWriteProtection:
    """Verify all four verdict paths of evaluate_write_protection()."""

    def _good_result(self, tmp_path: Path):
        good_yaml = tmp_path / "policy.yaml"
        good_yaml.write_text(_VALID_YAML, encoding="utf-8")
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", good_yaml):
            return _write_guard.load_protected_files()

    def _bad_result(self, tmp_path: Path):
        missing = tmp_path / "missing.yaml"
        with mock.patch.object(_write_guard, "PROTECTED_FILES_PATH", missing):
            return _write_guard.load_protected_files()

    def test_non_protected_file_is_allow(self, tmp_path):
        result = self._good_result(tmp_path)
        verdict, reason = _write_guard.evaluate_write_protection("07_LOGS/test.md", result)
        assert verdict == "allow"
        assert "not a protected file" in reason

    def test_protected_file_without_approval_is_block(self, tmp_path):
        result = self._good_result(tmp_path)
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: ""}):
            verdict, reason = _write_guard.evaluate_write_protection("SOUL.md", result)
        assert verdict == "block"
        assert "protected file" in reason.lower()

    def test_protected_file_with_correct_approval_is_allow_approved(self, tmp_path):
        result = self._good_result(tmp_path)
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: "SOUL.md"}):
            verdict, reason = _write_guard.evaluate_write_protection("SOUL.md", result)
        assert verdict == "allow_approved"
        assert "approved" in reason.lower()

    def test_protected_file_with_wrong_approval_is_block(self, tmp_path):
        result = self._good_result(tmp_path)
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: "README.md"}):
            verdict, reason = _write_guard.evaluate_write_protection("SOUL.md", result)
        assert verdict == "block"

    def test_policy_error_produces_policy_error_verdict(self, tmp_path):
        result = self._bad_result(tmp_path)
        verdict, reason = _write_guard.evaluate_write_protection("SOUL.md", result)
        assert verdict == "policy_error"

    def test_policy_error_applies_to_non_protected_paths_too(self, tmp_path):
        result = self._bad_result(tmp_path)
        verdict, _ = _write_guard.evaluate_write_protection("07_LOGS/anything.md", result)
        assert verdict == "policy_error"

    def test_approval_normalized_absolute_vs_relative(self, tmp_path):
        result = self._good_result(tmp_path)
        abs_soul = str(_VAULT_ROOT / "SOUL.md")
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: abs_soul}):
            verdict, _ = _write_guard.evaluate_write_protection("SOUL.md", result)
        assert verdict == "allow_approved"


# ===========================================================================
# Break-glass: both hooks
# ===========================================================================

class TestBreakGlass:
    """CHASEOS_GATE_DISABLE=1 must allow any write in both hooks."""

    def test_write_guard_break_glass_is_recognized(self):
        with mock.patch.dict(os.environ, {_write_guard.GATE_DISABLE_ENV_VAR: "1"}):
            assert _write_guard.is_gate_disabled() is True

    def test_write_guard_break_glass_off_by_default(self):
        clean_env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        with mock.patch.dict(os.environ, clean_env, clear=True):
            assert _write_guard.is_gate_disabled() is False

    def test_write_guard_break_glass_requires_exact_value(self):
        with mock.patch.dict(os.environ, {_write_guard.GATE_DISABLE_ENV_VAR: "true"}):
            assert _write_guard.is_gate_disabled() is False
        with mock.patch.dict(os.environ, {_write_guard.GATE_DISABLE_ENV_VAR: "yes"}):
            assert _write_guard.is_gate_disabled() is False
        with mock.patch.dict(os.environ, {_write_guard.GATE_DISABLE_ENV_VAR: " 1 "}):
            assert _write_guard.is_gate_disabled() is True  # strip() handles whitespace

    def test_ingest_guard_break_glass_is_recognized(self):
        with mock.patch.dict(os.environ, {_ingest_guard.GATE_DISABLE_ENV_VAR: "1"}):
            assert _ingest_guard.is_gate_disabled() is True

    def test_ingest_guard_break_glass_off_by_default(self):
        clean_env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        with mock.patch.dict(os.environ, clean_env, clear=True):
            assert _ingest_guard.is_gate_disabled() is False

    def test_write_guard_main_break_glass_exits_zero(self, tmp_path):
        """Break-glass must produce exit 0 even when policy file is missing."""
        env = {**os.environ, "CHASEOS_GATE_DISABLE": "1"}
        # Remove any real policy path side effects — stdin parse will block by default
        payload = _make_payload("SOUL.md")
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=env)
        assert result.returncode == 0
        assert "gate enforcement is DISABLED" in result.stderr

    def test_ingest_guard_main_break_glass_exits_zero(self):
        """Break-glass must produce exit 0 for ingest guard regardless of stdin."""
        env = {**os.environ, "CHASEOS_GATE_DISABLE": "1"}
        payload = _make_payload("02_KNOWLEDGE/AI-Agents/test.md")
        result = _run_hook(_INGEST_GUARD_PATH, payload, env=env)
        assert result.returncode == 0
        assert "DISABLED" in result.stderr


# ===========================================================================
# G-2: ingestion_promotion_guard — fail-closed on parse error
# ===========================================================================

class TestIngestGuardFailClosed:
    """G-2: ingestion_promotion_guard must exit 1 (not 0) on stdin parse failure."""

    def test_garbage_stdin_exits_nonzero(self):
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_INGEST_GUARD_PATH, "not json at all {{", env=env)
        assert result.returncode != 0

    def test_empty_stdin_exits_nonzero(self):
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_INGEST_GUARD_PATH, "", env=env)
        assert result.returncode != 0

    def test_partial_json_exits_nonzero(self):
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_INGEST_GUARD_PATH, '{"tool_input":', env=env)
        assert result.returncode != 0

    def test_parse_error_message_mentions_gate(self):
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_INGEST_GUARD_PATH, "garbage", env=env)
        assert "ChaseOS Gate" in result.stderr or "BLOCKED" in result.stderr

    def test_break_glass_overrides_parse_failure(self):
        """Even garbage stdin should exit 0 when break-glass is set."""
        env = {**os.environ, "CHASEOS_GATE_DISABLE": "1"}
        result = _run_hook(_INGEST_GUARD_PATH, "garbage", env=env)
        assert result.returncode == 0


# ===========================================================================
# G-1: protected_write_guard — fail-closed on parse error (integration)
# ===========================================================================

class TestWriteGuardFailClosed:
    """G-1: protected_write_guard must exit 2 (not 0) on stdin parse failure."""

    def test_garbage_stdin_exits_nonzero(self):
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_WRITE_GUARD_PATH, "not valid json {{{", env=env)
        assert result.returncode != 0

    def test_empty_stdin_exits_nonzero(self):
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_WRITE_GUARD_PATH, "", env=env)
        assert result.returncode != 0

    def test_parse_error_message_mentions_gate(self):
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_WRITE_GUARD_PATH, "{{bad", env=env)
        assert "ChaseOS Gate" in result.stderr or "BLOCKED" in result.stderr

    def test_break_glass_overrides_parse_failure(self):
        env = {**os.environ, "CHASEOS_GATE_DISABLE": "1"}
        result = _run_hook(_WRITE_GUARD_PATH, "garbage", env=env)
        assert result.returncode == 0

    def test_missing_file_path_exits_zero(self):
        """Payload with no file_path should allow (cannot evaluate without a path)."""
        payload = json.dumps({"session_id": "s", "tool_name": "Write", "tool_input": {}})
        env = {k: v for k, v in os.environ.items() if k != "CHASEOS_GATE_DISABLE"}
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=env)
        assert result.returncode == 0


# ===========================================================================
# Integration: write guard exit codes for real protected files
# ===========================================================================

class TestWriteGuardIntegration:
    """Full subprocess integration tests for exit code correctness."""

    def _env_no_gate(self) -> dict:
        return {k: v for k, v in os.environ.items() if k not in ("CHASEOS_GATE_DISABLE", "CHASEOS_APPROVED_FILE")}

    def test_non_protected_write_exits_zero(self):
        payload = _make_payload("07_LOGS/Build-Logs/2026-05-11-test.md")
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 0

    def test_protected_soul_write_exits_one(self):
        payload = _make_payload("SOUL.md")
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr

    def test_protected_readme_write_exits_one(self):
        payload = _make_payload("README.md")
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 1

    def test_approved_soul_write_exits_zero(self):
        payload = _make_payload("SOUL.md")
        env = {**self._env_no_gate(), "CHASEOS_APPROVED_FILE": "SOUL.md"}
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=env)
        assert result.returncode == 0

    def test_tool_input_nested_path_is_extracted(self):
        """Ensure payload["tool_input"]["file_path"] is used, not top-level."""
        payload = json.dumps({
            "session_id": "s",
            "tool_name": "Write",
            "file_path": "SOUL.md",  # top-level — must be ignored
            "tool_input": {"file_path": "07_LOGS/safe.md", "content": "safe"},
        })
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 0

    def test_top_level_fallback_path_extraction(self):
        """When tool_input is absent, top-level file_path is used as fallback."""
        payload = json.dumps({"session_id": "s", "file_path": "07_LOGS/safe.md"})
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 0

    def test_g3_my_readme_is_not_blocked(self):
        """G-3 regression: MY_README.md must not trigger README.md protection."""
        payload = _make_payload("MY_README.md")
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 0

    def test_absolute_protected_path_is_blocked(self):
        """Absolute paths to protected files must still be blocked."""
        abs_path = str(_VAULT_ROOT / "SOUL.md")
        payload = _make_payload(abs_path)
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 1

    def test_absolute_protected_nested_path_is_blocked(self):
        abs_path = str(_VAULT_ROOT / "06_AGENTS" / "Permission-Matrix.md")
        payload = _make_payload(abs_path)
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 1

    def test_knowledge_write_exits_zero_unrelated_to_write_guard(self):
        """02_KNOWLEDGE writes are not protected by write guard (handled by ingest guard)."""
        payload = _make_payload("02_KNOWLEDGE/AI-Agents/new-note.md")
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 0

    def test_memory_write_exits_zero(self):
        payload = _make_payload(".claude/projects/test/memory/test.md")
        result = _run_hook(_WRITE_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 0


# ===========================================================================
# Integration: ingest guard exit codes
# ===========================================================================

class TestIngestGuardIntegration:
    """Full subprocess integration tests for ingestion_promotion_guard exit codes."""

    def _env_no_gate(self) -> dict:
        return {k: v for k, v in os.environ.items() if k not in ("CHASEOS_GATE_DISABLE", "CHASEOS_PROMOTION_APPROVED")}

    def test_non_knowledge_write_exits_zero(self):
        payload = _make_payload("07_LOGS/Build-Logs/test.md")
        result = _run_hook(_INGEST_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 0

    def test_knowledge_write_without_approval_exits_one(self):
        payload = _make_payload("02_KNOWLEDGE/AI-Agents/new-note.md")
        result = _run_hook(_INGEST_GUARD_PATH, payload, env=self._env_no_gate())
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr

    def test_knowledge_write_with_approval_and_valid_provenance_exits_zero(self):
        content = (
            "---\n"
            "title: Test\n"
            "knowledge_class: source-derived\n"
            "verification_status: unverified\n"
            "promoted_from: 03_INPUTS/00_QUARANTINE/source/example.md\n"
            "---\n\n# Test\n"
        )
        payload = json.dumps({
            "session_id": "s",
            "tool_name": "Write",
            "tool_input": {"file_path": "02_KNOWLEDGE/AI-Agents/new-note.md", "content": content},
        })
        env = {**self._env_no_gate(), "CHASEOS_PROMOTION_APPROVED": "1"}
        result = _run_hook(_INGEST_GUARD_PATH, payload, env=env)
        assert result.returncode == 0


# ===========================================================================
# is_approved() normalization tests
# ===========================================================================

class TestIsApproved:
    """Test path normalization in is_approved()."""

    def test_exact_match_approved(self):
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: "SOUL.md"}):
            assert _write_guard.is_approved("SOUL.md") is True

    def test_different_file_not_approved(self):
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: "README.md"}):
            assert _write_guard.is_approved("SOUL.md") is False

    def test_empty_approval_env_not_approved(self):
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: ""}):
            assert _write_guard.is_approved("SOUL.md") is False

    def test_missing_approval_env_not_approved(self):
        env = {k: v for k, v in os.environ.items() if k != _write_guard.APPROVAL_ENV_VAR}
        with mock.patch.dict(os.environ, env, clear=True):
            assert _write_guard.is_approved("SOUL.md") is False

    def test_absolute_approval_matches_relative_target(self):
        abs_soul = str(_VAULT_ROOT / "SOUL.md")
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: abs_soul}):
            assert _write_guard.is_approved("SOUL.md") is True

    def test_relative_approval_matches_absolute_target(self):
        abs_soul = str(_VAULT_ROOT / "SOUL.md")
        with mock.patch.dict(os.environ, {_write_guard.APPROVAL_ENV_VAR: "SOUL.md"}):
            assert _write_guard.is_approved(abs_soul) is True


# ===========================================================================
# normalize_path tests
# ===========================================================================

class TestNormalizePath:
    """Verify path normalization handles both absolute and relative inputs."""

    def test_relative_path_returned_as_is(self):
        p = _write_guard.normalize_path("SOUL.md")
        assert p == Path("SOUL.md")

    def test_absolute_vault_path_relativized(self):
        abs_path = str(_VAULT_ROOT / "SOUL.md")
        p = _write_guard.normalize_path(abs_path)
        assert p == Path("SOUL.md")

    def test_absolute_outside_vault_returned_as_is(self):
        outside = "C:/some/other/location/file.md"
        p = _write_guard.normalize_path(outside)
        # Should return something that doesn't crash
        assert isinstance(p, Path)

    def test_nested_relative_path(self):
        p = _write_guard.normalize_path("06_AGENTS/Permission-Matrix.md")
        assert p == Path("06_AGENTS/Permission-Matrix.md")

    def test_absolute_nested_path_relativized(self):
        abs_path = str(_VAULT_ROOT / "06_AGENTS" / "Permission-Matrix.md")
        p = _write_guard.normalize_path(abs_path)
        assert p == Path("06_AGENTS/Permission-Matrix.md")
