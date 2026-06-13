"""
test_h1_setup_init_split.py — H-1 hardening: setup_init write target split

Verifies that:
  - The old broad "setup_init" key is gone from gateway_allowlists.json
  - "setup_init_scaffold" allows only the exact folder names (no file paths, no globs)
  - "setup_init_seed_files" allows only the specific named files (no /**  globs)
  - All 13 Permission-Matrix-protected files are blocked by setup_init_seed_files
    (they may still be in the list as specific paths but broad glob access is gone)
  - Entire directory globs that previously granted vault-wide access are now blocked:
      02_KNOWLEDGE/**, 03_INPUTS/**, 04_SOPS/**, 05_TEMPLATES/**, 99_ARCHIVE/**
  - setup_cli.py call sites reference the new split keys
  - All required_folders from setup_init_manifest.json pass scaffold check
  - All required_files from setup_init_manifest.json pass seed_files check
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.chaseos_gate import check_gateway_write_target, load_gateway_allowlists


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _scaffold_ok(path: str) -> bool:
    allowed, _ = check_gateway_write_target("setup_init_scaffold", path)
    return allowed


def _seed_ok(path: str) -> bool:
    allowed, _ = check_gateway_write_target("setup_init_seed_files", path)
    return allowed


def _old_key_ok(path: str) -> bool:
    allowed, _ = check_gateway_write_target("setup_init", path)
    return allowed


# ─────────────────────────────────────────────────────────────────────────────
# Old key is gone
# ─────────────────────────────────────────────────────────────────────────────

class TestOldSetupInitKeyRemoved:
    def test_old_setup_init_key_does_not_exist(self):
        allowlists = load_gateway_allowlists()
        assert "setup_init" not in allowlists.get("write_targets", {}), (
            "setup_init broad key must be removed — use setup_init_scaffold or setup_init_seed_files"
        )

    def test_old_key_blocks_all_paths(self):
        # check_gateway_write_target returns False for unknown categories
        for path in ["SOUL.md", "00_HOME/**", "02_KNOWLEDGE/any.md", "ROADMAP.md"]:
            assert not _old_key_ok(path), f"Old setup_init key must not allow: {path}"

    def test_new_scaffold_key_exists(self):
        allowlists = load_gateway_allowlists()
        assert "setup_init_scaffold" in allowlists.get("write_targets", {})

    def test_new_seed_files_key_exists(self):
        allowlists = load_gateway_allowlists()
        assert "setup_init_seed_files" in allowlists.get("write_targets", {})


# ─────────────────────────────────────────────────────────────────────────────
# Scaffold — folder creation only
# ─────────────────────────────────────────────────────────────────────────────

class TestSetupInitScaffold:
    """setup_init_scaffold must allow folder names and block file paths."""

    _REQUIRED_FOLDERS = [
        "00_HOME",
        "01_PROJECTS",
        "02_KNOWLEDGE",
        "03_INPUTS",
        "04_SOPS",
        "05_TEMPLATES",
        "06_AGENTS",
        "07_LOGS",
        "07_LOGS/Build-Logs",
        "07_LOGS/Agent-Activity",
        "07_LOGS/Operator-Briefs",
        "07_LOGS/Documentation-History",
        "99_ARCHIVE",
        "runtime",
        "runtime/bindings",
        "runtime/lifecycle",
        "runtime/state",
        "runtime/policy",
        "runtime/schedules",
    ]

    def test_all_required_folders_pass_scaffold(self):
        for folder in self._REQUIRED_FOLDERS:
            assert _scaffold_ok(folder), f"setup_init_scaffold must allow folder: {folder}"

    def test_scaffold_blocks_file_paths_under_allowed_folders(self):
        # Scaffold is for folder creation only — files inside folders are not scaffold targets
        blocked_files = [
            "00_HOME/Now.md",
            "06_AGENTS/Permission-Matrix.md",
            "SOUL.md",
            "README.md",
        ]
        for path in blocked_files:
            assert not _scaffold_ok(path), f"setup_init_scaffold must NOT allow file: {path}"

    def test_scaffold_blocks_broad_globs(self):
        blocked = [
            "00_HOME/**",
            "06_AGENTS/**",
            "02_KNOWLEDGE/**",
            "99_ARCHIVE/**",
        ]
        for path in blocked:
            assert not _scaffold_ok(path), f"setup_init_scaffold must NOT allow glob: {path}"

    def test_scaffold_blocks_unrelated_runtime_paths(self):
        assert not _scaffold_ok("runtime/workflows/registry/some_workflow.yaml")
        assert not _scaffold_ok("07_LOGS/Build-Logs/my-log.md")


# ─────────────────────────────────────────────────────────────────────────────
# Seed files — explicit named files, no broad globs
# ─────────────────────────────────────────────────────────────────────────────

class TestSetupInitSeedFiles:
    """setup_init_seed_files: explicit paths pass; broad globs and arbitrary paths do not."""

    _EXPLICIT_FILES = [
        "README.md",
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "FORKING.md",
        "SOUL.md",
        "00_HOME/Now.md",
        "00_HOME/Dashboard.md",
        "00_HOME/Operating-System.md",
        "00_HOME/Principles.md",
        "00_HOME/Assistant-Contract.md",
        "06_AGENTS/Vault-Map.md",
        "06_AGENTS/Permission-Matrix.md",
        "06_AGENTS/Agent-Registry.md",
        "06_AGENTS/Tool-Map.md",
        "06_AGENTS/Handoff-Protocol.md",
        "06_AGENTS/Trust-Tiers.md",
        "06_AGENTS/Agent-Control-Plane.md",
        "06_AGENTS/OpenClaw-Runtime-Profile.md",
        "06_AGENTS/Hermes-Runtime-Profile.md",
        "runtime/setup_registry.json",
        "runtime/setup_provider_profiles.json",
        "runtime/setup_state.example.json",
        "runtime/setup_state.schema.json",
        "runtime/SETUP-README.md",
        "System-Status.md",
        "Setup-Instructions.md",
        "Runtime-Registry.md",
        "07_LOGS/Build-Logs/Build-Logs-Index.md",
        "07_LOGS/Agent-Activity/Agent-Activity-Index.md",
        "07_LOGS/Operator-Briefs/Operator-Briefs-Index.md",
        "07_LOGS/Daily/Daily-Index.md",
        "02_KNOWLEDGE/Knowledge-Index.md",
    ]

    def test_all_explicit_seed_files_pass(self):
        for path in self._EXPLICIT_FILES:
            assert _seed_ok(path), f"setup_init_seed_files must allow: {path}"

    def test_broad_glob_paths_are_blocked(self):
        # The core vulnerability: these previously matched via /**  globs
        blocked = [
            "00_HOME/some-random-note.md",
            "02_KNOWLEDGE/any-knowledge-note.md",
            "02_KNOWLEDGE/deep/nested/note.md",
            "03_INPUTS/some-raw-input.md",
            "04_SOPS/any-sop.md",
            "05_TEMPLATES/any-template.md",
            "06_AGENTS/some-unlisted-file.md",
            "07_LOGS/Build-Logs/my-new-log.md",
            "99_ARCHIVE/some-archive-note.md",
            "01_PROJECTS/some-project.md",
        ]
        for path in blocked:
            assert not _seed_ok(path), (
                f"setup_init_seed_files must NOT allow arbitrary path (was allowed by old /**  glob): {path}"
            )

    def test_protected_files_accessible_only_by_exact_path(self):
        # Protected files are in the list as exact paths — arbitrary protected paths are not
        assert _seed_ok("06_AGENTS/Permission-Matrix.md")          # exact — allowed
        assert not _seed_ok("06_AGENTS/Permission-Matrix-v2.md")   # not listed — blocked
        assert _seed_ok("SOUL.md")                                  # exact — allowed
        assert not _seed_ok("SOUL-backup.md")                       # not listed — blocked

    def test_runtime_setup_wildcard_matches(self):
        # runtime/setup_*.json is intentionally a glob for setup files
        assert _seed_ok("runtime/setup_registry.json")
        assert _seed_ok("runtime/setup_state.json")
        assert _seed_ok("runtime/setup_provider_profiles.json")

    def test_seed_files_blocks_folder_only_paths(self):
        # Folder names are scaffold targets, not seed_files targets
        assert not _seed_ok("00_HOME")
        assert not _seed_ok("06_AGENTS")
        assert not _seed_ok("runtime")


# ─────────────────────────────────────────────────────────────────────────────
# Manifest alignment: all required_folders and required_files covered
# ─────────────────────────────────────────────────────────────────────────────

class TestManifestAlignment:
    """All paths from setup_init_manifest.json must pass the correct new key."""

    _MANIFEST_PATH = _VAULT_ROOT / "runtime" / "setup_init_manifest.json"

    def _load_manifest(self) -> dict:
        return json.loads(self._MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_exists(self):
        assert self._MANIFEST_PATH.exists()

    def test_all_required_folders_in_manifest_pass_scaffold(self):
        manifest = self._load_manifest()
        profile = manifest["profiles"]["personal"]
        for folder in profile.get("required_folders", []):
            assert _scaffold_ok(folder), (
                f"Manifest required_folder not in setup_init_scaffold: {folder}"
            )

    def test_all_required_files_in_manifest_pass_seed_files(self):
        manifest = self._load_manifest()
        profile = manifest["profiles"]["personal"]
        for entry in profile.get("required_files", []):
            file_path = entry.get("path") if isinstance(entry, dict) else str(entry)
            assert _seed_ok(file_path), (
                f"Manifest required_file not in setup_init_seed_files: {file_path}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# setup_cli.py call-site regression
# ─────────────────────────────────────────────────────────────────────────────

class TestSetupCliCallSites:
    """setup_cli.py must not reference the old 'setup_init' key."""

    _SETUP_CLI = _VAULT_ROOT / "runtime" / "setup_cli.py"

    def test_old_key_not_referenced_in_setup_cli(self):
        source = self._SETUP_CLI.read_text(encoding="utf-8")
        # The string 'check_gateway_write_target("setup_init"' must not appear
        assert 'check_gateway_write_target("setup_init",' not in source, (
            "setup_cli.py still references the removed 'setup_init' key"
        )

    def test_scaffold_key_referenced_in_setup_cli(self):
        source = self._SETUP_CLI.read_text(encoding="utf-8")
        assert 'check_gateway_write_target("setup_init_scaffold"' in source

    def test_seed_files_key_referenced_in_setup_cli(self):
        source = self._SETUP_CLI.read_text(encoding="utf-8")
        assert 'check_gateway_write_target("setup_init_seed_files"' in source

    def test_seed_files_key_used_for_file_seeding(self):
        source = self._SETUP_CLI.read_text(encoding="utf-8")
        # _seed_missing_file must use setup_init_seed_files
        assert 'check_gateway_write_target("setup_init_seed_files", relative_path)' in source

    def test_scaffold_key_used_for_folder_creation(self):
        source = self._SETUP_CLI.read_text(encoding="utf-8")
        # folder creation loop must use setup_init_scaffold
        assert 'check_gateway_write_target("setup_init_scaffold", folder)' in source
