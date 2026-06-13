from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from runtime.forge.extension_points import APPROVED_EXTENSION_POINTS, LIFECYCLE_MODEL
from runtime.forge.protected_core import is_protected_path, validate_generated_extension_paths
from runtime.forge.validator import validate_manifest


DEMO_MANIFEST = Path(__file__).with_name("examples") / "ugc_campaign_studio.manifest.json"


def _manifest() -> dict:
    return json.loads(DEMO_MANIFEST.read_text(encoding="utf-8"))


def _codes(result: dict) -> set[str]:
    return {issue["code"] for issue in result.get("issues", [])}


def test_demo_manifest_validates() -> None:
    result = validate_manifest(_manifest())

    assert result["valid"] is True
    assert result["riskLevel"] == "medium"
    assert result["errors"] == []
    assert "forge.live_install.operator_approval" in result["requiredApprovals"]
    assert "forge.rollback.snapshot_required" in result["requiredApprovals"]


def test_extension_points_and_lifecycle_are_explicit() -> None:
    result = validate_manifest(_manifest())

    assert "workspace.page" in APPROVED_EXTENSION_POINTS
    assert "agent.preset" in APPROVED_EXTENSION_POINTS
    assert len(result["approvedExtensionPointTypes"]) == 11
    assert [stage["id"] for stage in LIFECYCLE_MODEL] == [
        "draft",
        "preview",
        "sandbox",
        "active",
        "disabled",
        "archived",
    ]


@pytest.mark.parametrize(
    ("permission", "expected_code"),
    [
        ("secrets.read", "forbidden_permission"),
        ("studio.shell.patch", "forbidden_permission"),
        ("unknown.permission", "unknown_permission"),
    ],
)
def test_forbidden_or_unknown_permissions_are_rejected(permission: str, expected_code: str) -> None:
    manifest = _manifest()
    manifest["permissions"].append(permission)

    result = validate_manifest(manifest)

    assert result["valid"] is False
    assert expected_code in _codes(result)


def test_workspace_routes_must_stay_under_extension_namespace() -> None:
    manifest = _manifest()
    manifest["extensionPoints"][1]["route"] = "/settings"

    result = validate_manifest(manifest)

    assert result["valid"] is False
    assert "unsafe_route_namespace" in _codes(result)


def test_raw_script_ui_components_are_rejected() -> None:
    manifest = _manifest()
    manifest["ui"]["components"][0]["type"] = "raw_script"

    result = validate_manifest(manifest)

    assert result["valid"] is False
    assert "forbidden_ui_component" in _codes(result)


def test_shell_workflow_nodes_are_rejected() -> None:
    manifest = _manifest()
    manifest["workflows"][0]["steps"].append({"type": "shell.execute"})

    result = validate_manifest(manifest)

    assert result["valid"] is False
    assert "forbidden_workflow_node" in _codes(result)


def test_global_agent_memory_scope_is_rejected() -> None:
    manifest = _manifest()
    manifest["agents"][0]["memoryScopes"].append("global")

    result = validate_manifest(manifest)

    assert result["valid"] is False
    assert "forbidden_memory_scope" in _codes(result)


def test_core_collection_names_are_rejected() -> None:
    manifest = _manifest()
    manifest["dataSchemas"][0]["collection"] = "users"

    result = validate_manifest(manifest)

    assert result["valid"] is False
    assert "core_collection_name" in _codes(result)


@pytest.mark.parametrize(
    "target_path",
    [
        ".env",
        "runtime/policy/adapters/codex.yaml",
        "runtime/studio/shell/frontend/app.js",
        "06_AGENTS/Permission-Matrix.md",
    ],
)
def test_protected_core_target_paths_are_rejected(target_path: str) -> None:
    result = validate_manifest(_manifest(), target_paths=[target_path])

    assert result["valid"] is False
    assert "protected_core_path" in _codes(result)


def test_generated_extension_paths_must_stay_in_owned_root() -> None:
    manifest = _manifest()
    result = validate_manifest(manifest, target_paths=["extensions/other-extension/file.json"])

    assert result["valid"] is False
    assert "outside_extension_root" in _codes(result)


def test_path_guard_rejects_absolute_and_parent_traversal() -> None:
    guarded = validate_generated_extension_paths(
        "ugc-campaign-studio",
        ["C:/tmp/extension.json", "../manifest.json"],
    )

    assert guarded["valid"] is False
    assert {issue["code"] for issue in guarded["issues"]} == {"absolute_path", "parent_traversal"}


def test_protected_path_helper_flags_core_paths() -> None:
    assert is_protected_path("runtime/schedules/index.yaml") is True
    assert is_protected_path("extensions/ugc-campaign-studio/manifest.json") is False


def test_validator_does_not_mutate_manifest() -> None:
    manifest = _manifest()
    original = deepcopy(manifest)

    validate_manifest(manifest)

    assert manifest == original
