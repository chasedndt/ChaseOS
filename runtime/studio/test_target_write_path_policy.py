"""Tests for Phase 10 real-target upgrade target-write path policy."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from runtime.studio.target_write_path_policy import validate_target_write_plan


def _write_op(relative_path: str, operation_type: str = "create_file") -> dict[str, str]:
    return {
        "operation_id": f"op-{relative_path.replace('/', '-')}",
        "operation_type": operation_type,
        "relative_path": relative_path,
    }


def test_target_write_path_policy_allows_create_only_missing_anchor_inside_target(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    model = validate_target_write_plan(target, [_write_op("00_HOME/README.md")])

    assert model["ok"] is True
    assert model["write_enabled"] is False
    assert model["target_writes_performed"] is False
    assert model["planned_write_count"] == 1
    assert model["operations"][0]["allowed"] is True
    assert (target / "00_HOME" / "README.md").exists() is False


def test_target_write_path_policy_blocks_protected_and_canonical_paths(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    model = validate_target_write_plan(
        target,
        [
            _write_op("06_AGENTS/Permission-Matrix.md"),
            _write_op("02_KNOWLEDGE/Topic.md"),
            _write_op("runtime/policy/gateway_allowlists.json"),
        ],
    )

    assert model["ok"] is False
    assert "protected-target-path" in model["blockers"]
    assert "canonical-target-path" in model["blockers"]
    assert "control-policy-target-path" in model["blockers"]
    assert all(item["allowed"] is False for item in model["operations"])


def test_target_write_path_policy_blocks_case_drifted_protected_and_control_paths(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    model = validate_target_write_plan(
        target,
        [
            _write_op("06_agents/Permission-Matrix.md"),
            _write_op("06_agents/trust-tiers.md"),
            _write_op("06_AGENTS/agent-security-model.md"),
            _write_op("02_knowledge/Topic.md"),
            _write_op("Runtime/Policy/gateway_allowlists.json"),
            _write_op("RUNTIME/workflows/registry/example.json"),
            _write_op("06_Agents/trust-tiers/draft.md"),
        ],
    )

    assert model["ok"] is False
    assert "protected-target-path" in model["blockers"]
    assert "canonical-target-path" in model["blockers"]
    assert "control-policy-target-path" in model["blockers"]
    assert [item["normalized_relative_path"] for item in model["operations"]] == [
        "06_agents/Permission-Matrix.md",
        "06_agents/trust-tiers.md",
        "06_AGENTS/agent-security-model.md",
        "02_knowledge/Topic.md",
        "Runtime/Policy/gateway_allowlists.json",
        "RUNTIME/workflows/registry/example.json",
        "06_Agents/trust-tiers/draft.md",
    ]
    assert all(item["allowed"] is False for item in model["operations"])
    assert model["write_enabled"] is False
    assert model["target_writes_performed"] is False
    assert model["approval_consumed"] is False
    assert model["scaffold_execution_performed"] is False


def test_target_write_path_policy_blocks_foreign_parent_escape(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    model = validate_target_write_plan(target, [_write_op("../foreign/outside.md")])

    assert model["ok"] is False
    assert "foreign-folder-escape" in model["blockers"]
    assert model["operations"][0]["resolved_within_target"] is False
    assert (tmp_path / "foreign" / "outside.md").exists() is False


def test_target_write_path_policy_blocks_absolute_planned_target_paths(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    absolute_target = target / "00_HOME" / "README.md"

    model = validate_target_write_plan(target, [_write_op(str(absolute_target))])

    assert model["ok"] is False
    assert "absolute-planned-target-path" in model["blockers"]
    assert model["operations"][0]["allowed"] is False


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation requires elevated privileges on Windows")
def test_target_write_path_policy_blocks_symlink_escapes(tmp_path: Path) -> None:
    target = tmp_path / "target"
    foreign = tmp_path / "foreign"
    target.mkdir()
    foreign.mkdir()
    (target / "linked-foreign").symlink_to(foreign, target_is_directory=True)

    model = validate_target_write_plan(target, [_write_op("linked-foreign/escape.md")])

    assert model["ok"] is False
    assert "symlink-escape" in model["blockers"]
    assert model["operations"][0]["resolved_within_target"] is False
    assert (foreign / "escape.md").exists() is False


def test_target_write_path_policy_blocks_no_overwrite_existing_files(tmp_path: Path) -> None:
    target = tmp_path / "target"
    existing = target / "00_HOME" / "README.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("keep me", encoding="utf-8")

    model = validate_target_write_plan(target, [_write_op("00_HOME/README.md")])

    assert model["ok"] is False
    assert "target-path-already-exists" in model["blockers"]
    assert model["operations"][0]["would_overwrite"] is True
    assert existing.read_text(encoding="utf-8") == "keep me"


def test_target_write_path_policy_blocks_non_create_operations(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    model = validate_target_write_plan(target, [_write_op("00_HOME/README.md", operation_type="update_file")])

    assert model["ok"] is False
    assert "unsupported-write-operation" in model["blockers"]
    assert model["operations"][0]["allowed"] is False
