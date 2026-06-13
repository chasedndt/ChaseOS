from __future__ import annotations

from pathlib import Path

from runtime.aor.registry import load_manifest
from runtime.aor.role_cards import load_card
from runtime.aor.task_router import classify


def test_aiso_recent_artifact_locator_manifest_role_and_task_are_registered() -> None:
    vault_root = Path(__file__).resolve().parents[2]

    manifest = load_manifest("aiso_recent_artifact_locator", vault_root)
    role_card = load_card("aiso-recent-artifact-locator", vault_root)
    task_type = classify("aiso-recent-artifact-locator", vault_root)

    assert manifest is not None
    assert manifest["id"] == "aiso_recent_artifact_locator"
    assert manifest["task_type"] == "aiso-recent-artifact-locator"
    assert manifest["role_card"] == "aiso-recent-artifact-locator"
    assert manifest["permission_ceiling"] == "read_only"
    assert role_card is not None
    assert role_card["id"] == "aiso-recent-artifact-locator"
    assert role_card["write_scope"] == []
    assert "send_email" in role_card["forbidden_actions"]
    assert task_type["id"] == "aiso-recent-artifact-locator"
    assert task_type["runtime_class"] == "read-only"
    assert task_type["permission_ceiling"] == "read_only"
