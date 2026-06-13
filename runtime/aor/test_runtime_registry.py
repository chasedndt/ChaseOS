"""
test_runtime_registry.py — Phase 9 Runtime Registry substrate

Initial focused TDD slice:
- runtime registry entries exist for Hermes and OpenClaw
- runtime registry loader returns canonical fields
- lifecycle state and trust ceiling are validated
- registry list surface is stable and sorted
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.aor.runtime_registry import (
    REGISTRY_ENTRY_REQUIRED_FIELDS,
    VALID_LIFECYCLE_STATES,
    load_runtime_entry,
    list_runtime_entries,
)


class TestRuntimeRegistryEntries:
    def test_openclaw_entry_loads(self):
        entry = load_runtime_entry("openclaw")
        assert entry is not None
        assert entry["runtime_id"] == "openclaw"
        assert entry["provider"] == "openclaw"
        assert entry["surface_type"]
        assert entry["lifecycle_state"] in VALID_LIFECYCLE_STATES

    def test_hermes_entry_loads(self):
        entry = load_runtime_entry("hermes")
        assert entry is not None
        assert entry["runtime_id"] == "hermes"
        assert entry["provider"] == "hermes"
        assert entry["surface_type"]
        assert entry["lifecycle_state"] in VALID_LIFECYCLE_STATES

    def test_registry_entry_contains_required_fields(self):
        entry = load_runtime_entry("openclaw")
        missing = [field for field in REGISTRY_ENTRY_REQUIRED_FIELDS if field not in entry]
        assert missing == []

    def test_openclaw_policy_binding_record_is_repo_relative(self):
        entry = load_runtime_entry("openclaw")
        assert entry is not None
        policy_binding_record = entry["policy_binding_record"]
        assert policy_binding_record == "runtime/aor/runtime_registry/openclaw/policy_binding.yaml"
        assert "C:\\Users\\" not in policy_binding_record
        assert not Path(policy_binding_record).is_absolute()

    def test_missing_runtime_returns_none(self):
        assert load_runtime_entry("does-not-exist") is None

    def test_fallback_parser_without_pyyaml(self, tmp_path: Path):
        registry_dir = tmp_path / "runtime" / "aor" / "runtime_registry" / "fallback"
        registry_dir.mkdir(parents=True)
        (tmp_path / "CLAUDE.md").write_text("# ChaseOS", encoding="utf-8")
        (registry_dir / "registry_entry.yaml").write_text(
            "runtime_id: \"fallback\"\nprovider: \"openclaw\"\nsurface_type: \"cli\"\n"
            "adapter_binding_status: \"bound\"\ntrust_ceiling: \"tier-4\"\n"
            "allowed_task_families:\n  - \"operator-briefing\"\n"
            "lifecycle_state: \"declared\"\ninitial_scope_posture: \"read-only\"\n",
            encoding="utf-8",
        )
        import runtime.aor.runtime_registry as runtime_registry_mod
        with patch.object(runtime_registry_mod, "yaml", None):
            entry = load_runtime_entry("fallback", vault_root=tmp_path)
        assert entry is not None
        assert entry["runtime_id"] == "fallback"
        assert entry["allowed_task_families"] == ["operator-briefing"]


class TestRuntimeRegistryListSurface:
    def test_lists_seeded_runtime_entries(self):
        entries = list_runtime_entries()
        runtime_ids = [entry["runtime_id"] for entry in entries]
        assert runtime_ids == sorted(runtime_ids)
        assert "hermes" in runtime_ids
        assert "openclaw" in runtime_ids

    def test_list_entries_only_returns_registry_entry_records(self, tmp_path: Path):
        registry_dir = tmp_path / "runtime" / "aor" / "runtime_registry"
        (registry_dir / "alpha").mkdir(parents=True)
        (registry_dir / "alpha" / "registry_entry.yaml").write_text(
            "runtime_id: \"alpha\"\nprovider: \"alpha\"\nsurface_type: \"cli\"\n"
            "adapter_binding_status: \"bound\"\ntrust_ceiling: \"tier-4\"\n"
            "allowed_task_families:\n  - \"operator-briefing\"\n"
            "lifecycle_state: \"declared\"\ninitial_scope_posture: \"read-only\"\n",
            encoding="utf-8",
        )
        (registry_dir / "README.md").write_text("ignore me", encoding="utf-8")

        entries = list_runtime_entries(vault_root=tmp_path)
        assert len(entries) == 1
        assert entries[0]["runtime_id"] == "alpha"


class TestRuntimeRegistryValidation:
    def test_invalid_lifecycle_state_raises(self, tmp_path: Path):
        registry_dir = tmp_path / "runtime" / "aor" / "runtime_registry" / "broken"
        registry_dir.mkdir(parents=True)
        (registry_dir / "registry_entry.yaml").write_text(
            "runtime_id: \"broken\"\nprovider: \"broken\"\nsurface_type: \"cli\"\n"
            "adapter_binding_status: \"bound\"\ntrust_ceiling: \"tier-4\"\n"
            "allowed_task_families:\n  - \"operator-briefing\"\n"
            "lifecycle_state: \"wrong\"\ninitial_scope_posture: \"read-only\"\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="lifecycle_state"):
            load_runtime_entry("broken", vault_root=tmp_path)
