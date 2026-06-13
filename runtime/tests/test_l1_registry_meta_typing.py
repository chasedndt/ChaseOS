"""
runtime/tests/test_l1_registry_meta_typing.py

Tests for L-1 hardening: is_schema/is_template frontmatter on _-prefixed
registry meta files, the defense-in-depth type-check assertion in
list_manifests(), and deprecated status support (complement to M-3).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
import yaml

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.registry import (  # noqa: E402
    VALID_STATUSES,
    _assert_meta_file_typed,
    _validate_manifest,
    list_manifests,
    load_manifest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_manifest(workflow_id: str = "test_wf") -> dict:
    return {
        "id": workflow_id,
        "name": "Test Workflow",
        "version": "1.0",
        "description": "Test manifest.",
        "task_type": "operator-briefing",
        "role_card": "operator-briefing",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "permission_ceiling": "no_protected_file_writes",
        "writeback_targets": ["07_LOGS/Operator-Briefs/"],
        "failure_behavior": "escalate",
    }


def _write_registry(tmp_path: Path, files: dict[str, str]) -> Path:
    """Create a minimal fake vault with a workflow registry."""
    vault = tmp_path / "vault"
    registry = vault / "runtime" / "workflows" / "registry"
    registry.mkdir(parents=True)
    (vault / "CLAUDE.md").write_text("# stub")
    for name, content in files.items():
        (registry / name).write_text(content, encoding="utf-8")
    return vault


# ---------------------------------------------------------------------------
# 1 — _schema.yaml has is_schema: true
# ---------------------------------------------------------------------------

class TestSchemaYamlFrontmatter:
    """Real file on disk must declare is_schema: true."""

    def _load_schema_yaml(self) -> dict:
        path = _VAULT_ROOT / "runtime" / "workflows" / "registry" / "_schema.yaml"
        assert path.exists(), "_schema.yaml not found"
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f.read())
        return data or {}

    def test_parses_as_dict(self):
        data = self._load_schema_yaml()
        assert isinstance(data, dict)

    def test_is_schema_true(self):
        data = self._load_schema_yaml()
        assert data.get("is_schema") is True

    def test_no_is_template(self):
        data = self._load_schema_yaml()
        assert "is_template" not in data

    def test_file_starts_with_underscore(self):
        path = _VAULT_ROOT / "runtime" / "workflows" / "registry" / "_schema.yaml"
        assert path.name.startswith("_")


# ---------------------------------------------------------------------------
# 2 — _sbp_base_template.yaml has is_template: true
# ---------------------------------------------------------------------------

class TestSbpBaseTemplateFrontmatter:
    """Real file on disk must declare is_template: true."""

    def _load_template_yaml(self) -> dict:
        path = _VAULT_ROOT / "runtime" / "workflows" / "registry" / "_sbp_base_template.yaml"
        assert path.exists(), "_sbp_base_template.yaml not found"
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f.read())
        return data or {}

    def test_parses_as_dict(self):
        data = self._load_template_yaml()
        assert isinstance(data, dict)

    def test_is_template_true(self):
        data = self._load_template_yaml()
        assert data.get("is_template") is True

    def test_no_is_schema(self):
        data = self._load_template_yaml()
        assert "is_schema" not in data

    def test_file_starts_with_underscore(self):
        path = _VAULT_ROOT / "runtime" / "workflows" / "registry" / "_sbp_base_template.yaml"
        assert path.name.startswith("_")


# ---------------------------------------------------------------------------
# 3 — deprecated status accepted by VALID_STATUSES and _validate_manifest
# ---------------------------------------------------------------------------

class TestDeprecatedStatus:
    """VALID_STATUSES must include deprecated (complement to M-3 shadow manifests)."""

    def test_deprecated_in_valid_statuses(self):
        assert "deprecated" in VALID_STATUSES

    def test_active_still_valid(self):
        assert "active" in VALID_STATUSES

    def test_draft_still_valid(self):
        assert "draft" in VALID_STATUSES

    def test_disabled_still_valid(self):
        assert "disabled" in VALID_STATUSES

    def test_validate_manifest_accepts_deprecated(self, tmp_path):
        reg = tmp_path / "runtime" / "workflows" / "registry"
        reg.mkdir(parents=True)
        m = _valid_manifest("my_wf")
        m["status"] = "deprecated"
        path = reg / "my_wf.yaml"
        _validate_manifest(m, path)  # must not raise

    def test_validate_manifest_rejects_unknown_status(self, tmp_path):
        reg = tmp_path / "runtime" / "workflows" / "registry"
        reg.mkdir(parents=True)
        m = _valid_manifest("my_wf")
        m["status"] = "retired"
        path = reg / "my_wf.yaml"
        with pytest.raises(ValueError, match="status must be one of"):
            _validate_manifest(m, path)


# ---------------------------------------------------------------------------
# 4 — _assert_meta_file_typed unit tests
# ---------------------------------------------------------------------------

class TestAssertMetaFileTyped:
    """Unit tests for the defense-in-depth type-check helper."""

    def test_no_warning_for_is_schema_true(self, tmp_path, capsys):
        f = tmp_path / "_myschema.yaml"
        f.write_text("is_schema: true\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" not in captured.err

    def test_no_warning_for_is_template_true(self, tmp_path, capsys):
        f = tmp_path / "_mytemplate.yaml"
        f.write_text("is_template: true\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" not in captured.err

    def test_warning_for_missing_type_flags(self, tmp_path, capsys):
        f = tmp_path / "_untyped.yaml"
        f.write_text("some_key: some_value\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "_untyped.yaml" in captured.err

    def test_warning_for_empty_yaml(self, tmp_path, capsys):
        f = tmp_path / "_empty.yaml"
        f.write_text("# comment only\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err

    def test_warning_message_mentions_is_schema_is_template(self, tmp_path, capsys):
        f = tmp_path / "_bad.yaml"
        f.write_text("foo: bar\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "is_schema" in captured.err or "is_template" in captured.err

    def test_fail_open_on_unreadable_file(self, tmp_path, capsys):
        f = tmp_path / "_ghost.yaml"
        # Don't create the file — triggers FileNotFoundError inside helper
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err

    def test_is_schema_false_triggers_warning(self, tmp_path, capsys):
        f = tmp_path / "_falseschema.yaml"
        f.write_text("is_schema: false\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err

    def test_is_template_false_triggers_warning(self, tmp_path, capsys):
        f = tmp_path / "_falsetemplate.yaml"
        f.write_text("is_template: false\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err

    def test_both_flags_present_no_warning(self, tmp_path, capsys):
        f = tmp_path / "_both.yaml"
        f.write_text("is_schema: true\nis_template: true\n", encoding="utf-8")
        _assert_meta_file_typed(f)
        captured = capsys.readouterr()
        assert "WARNING" not in captured.err


# ---------------------------------------------------------------------------
# 5 — list_manifests integration: _ files produce no warnings in real vault
# ---------------------------------------------------------------------------

class TestListManifestsMetaIntegration:
    """Real-vault integration: _schema.yaml and _sbp_base_template.yaml must not
    trigger type warnings when list_manifests() runs."""

    def test_list_manifests_no_meta_warning(self, capsys):
        _ = list_manifests(_VAULT_ROOT)
        captured = capsys.readouterr()
        # No type-frontmatter warnings from real _ files
        assert "lacks is_schema/is_template" not in captured.err

    def test_list_manifests_excludes_underscore_files(self):
        manifests = list_manifests(_VAULT_ROOT)
        ids = {m["id"] for m in manifests}
        assert "_schema" not in ids
        assert "_sbp_base_template" not in ids

    def test_list_manifests_returns_list(self):
        result = list_manifests(_VAULT_ROOT)
        assert isinstance(result, list)

    def test_list_manifests_includes_operator_today(self):
        manifests = list_manifests(_VAULT_ROOT)
        ids = {m["id"] for m in manifests}
        assert "operator_today" in ids


# ---------------------------------------------------------------------------
# 6 — list_manifests warns for untyped _ file in synthetic registry
# ---------------------------------------------------------------------------

class TestListManifestsSyntheticWarning:
    """Synthetic registry: list_manifests() must warn for untyped _ files."""

    def _minimal_manifest_yaml(self, wf_id: str) -> str:
        return (
            f"id: {wf_id}\n"
            "name: Test\nversion: '1.0'\ndescription: test\n"
            "task_type: operator-briefing\nrole_card: operator-briefing\n"
            "trigger_type: manual\nowner: operator\nstatus: active\n"
            "permission_ceiling: no_protected_file_writes\n"
            "writeback_targets:\n  - '07_LOGS/Test/'\n"
            "failure_behavior: escalate\n"
        )

    def test_warns_for_untyped_underscore_file(self, tmp_path, capsys):
        vault = _write_registry(tmp_path, {
            "real_wf.yaml": self._minimal_manifest_yaml("real_wf"),
            "_untyped.yaml": "some_key: value\n",
        })
        list_manifests(vault)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "_untyped.yaml" in captured.err

    def test_no_warning_for_typed_schema_file(self, tmp_path, capsys):
        vault = _write_registry(tmp_path, {
            "real_wf.yaml": self._minimal_manifest_yaml("real_wf"),
            "_typed_schema.yaml": "is_schema: true\n",
        })
        list_manifests(vault)
        captured = capsys.readouterr()
        assert "lacks is_schema/is_template" not in captured.err

    def test_no_warning_for_typed_template_file(self, tmp_path, capsys):
        vault = _write_registry(tmp_path, {
            "real_wf.yaml": self._minimal_manifest_yaml("real_wf"),
            "_typed_tmpl.yaml": "is_template: true\n",
        })
        list_manifests(vault)
        captured = capsys.readouterr()
        assert "lacks is_schema/is_template" not in captured.err

    def test_untyped_file_still_skipped_from_results(self, tmp_path):
        vault = _write_registry(tmp_path, {
            "real_wf.yaml": self._minimal_manifest_yaml("real_wf"),
            "_untyped.yaml": "some_key: value\n",
        })
        result = list_manifests(vault)
        ids = {m["id"] for m in result}
        assert "real_wf" in ids
        assert "_untyped" not in ids

    def test_non_underscore_files_load_normally(self, tmp_path):
        vault = _write_registry(tmp_path, {
            "real_wf.yaml": self._minimal_manifest_yaml("real_wf"),
            "_schema.yaml": "is_schema: true\n",
        })
        result = list_manifests(vault)
        assert len(result) == 1
        assert result[0]["id"] == "real_wf"
