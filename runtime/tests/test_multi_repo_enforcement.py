"""AOR multi-repo and multi-directory boundary tests."""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

import pytest


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.aor.engine as engine  # noqa: E402
from runtime.aor.registry import _validate_manifest, load_manifest  # noqa: E402
from runtime.aor.role_cards import _validate_card, load_card  # noqa: E402


def _valid_manifest(workflow_id: str = "operator_today") -> dict:
    return {
        "id": workflow_id,
        "name": "Boundary Test Workflow",
        "version": "1.0",
        "description": "Boundary test manifest.",
        "task_type": "operator-briefing",
        "role_card": "operator-briefing",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "permission_ceiling": "no_protected_file_writes",
        "writeback_targets": ["07_LOGS/Operator-Briefs/"],
        "failure_behavior": "escalate",
    }


def _valid_role_card(card_id: str = "operator-briefing") -> dict:
    return {
        "id": card_id,
        "name": "Boundary Test Role",
        "version": "1.0",
        "description": "Boundary test role card.",
        "owner": "operator",
        "allowed_actions": ["read_vault", "write_logs"],
        "forbidden_actions": ["write_protected_files"],
        "write_scope": ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"],
        "forbidden_write_zones": ["00_HOME/Now.md", "runtime/"],
        "escalation_rules": ["write outside scope"],
        "runtime_expectations": ["vault root accessible"],
        "required_reads": [
            "00_HOME/Now.md",
            "03_INPUTS/",
            "07_LOGS/Build-Logs/",
            "07_LOGS/Decision-Ledger/",
        ],
    }


def _make_temp_vault() -> Path:
    root = _VAULT_ROOT / ".pytest-tmp" / f"multi-repo-enforcement-{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    for relative in (
        "runtime/workflows/registry",
        "06_AGENTS/role-cards",
        "00_HOME",
        "03_INPUTS",
        "07_LOGS/Build-Logs",
        "07_LOGS/Decision-Ledger",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    (root / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    return root


def _write_yaml(path: Path, data: dict) -> None:
    import yaml

    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_current_repo_manifest_and_role_card_path_declarations_load() -> None:
    manifest = load_manifest("developer_repo_explain_shadow", _VAULT_ROOT)
    card = load_card("operator-briefing", _VAULT_ROOT)

    assert manifest is not None
    assert manifest["repo_scope"]["primary_repo"] == "."
    assert card is not None
    assert "07_LOGS/Operator-Briefs/" in card["write_scope"]


def test_manifest_validation_blocks_required_read_escape() -> None:
    manifest = _valid_manifest("escape")
    manifest["required_reads"] = ["../sibling-repo/secret.md"]

    with pytest.raises(ValueError, match="required_reads"):
        _validate_manifest(manifest, Path("escape.yaml"))


def test_manifest_validation_requires_cross_repo_policy_reference() -> None:
    manifest = _valid_manifest("cross_repo")
    manifest["repo_scope"] = {
        "primary_repo": ".",
        "extra_dirs": [],
        "cross_repo_access": True,
    }

    with pytest.raises(ValueError, match="policy_ref|policy_path"):
        _validate_manifest(manifest, Path("cross_repo.yaml"))


def test_manifest_validation_blocks_extra_dirs_until_executor_policy_exists() -> None:
    manifest = _valid_manifest("extra_dirs")
    manifest["repo_scope"] = {
        "primary_repo": ".",
        "extra_dirs": [{"path": "../external-repo", "access": "read_write"}],
        "cross_repo_access": True,
        "policy_ref": "runtime/policy/repo-scopes/example.yaml",
    }

    with pytest.raises(ValueError, match="extra_dirs"):
        _validate_manifest(manifest, Path("extra_dirs.yaml"))


def test_role_card_validation_blocks_absolute_write_scope() -> None:
    card = _valid_role_card("unsafe-role")
    card["write_scope"] = ["C:/Users/chaseos/outside-repo/"]

    with pytest.raises(ValueError, match="write_scope"):
        _validate_card(card, Path("unsafe-role.yaml"))


def test_aor_writeback_blocks_handler_path_traversal(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_temp_vault()
    try:
        _write_yaml(root / "runtime" / "workflows" / "registry" / "operator_today.yaml", _valid_manifest())
        _write_yaml(root / "06_AGENTS" / "role-cards" / "operator-briefing.yaml", _valid_role_card())

        def fake_handler(inputs: dict, vault_root: Path) -> dict:
            return {
                "handler_status": "executed",
                "writebacks": [
                    {
                        "path": "07_LOGS/Operator-Briefs/../../../../outside.md",
                        "content": "should not write",
                    }
                ],
            }

        monkeypatch.setattr(engine, "_resolve_workflow_handler", lambda workflow_id: fake_handler)

        result = engine.run_workflow("operator_today", inputs={"date": "2026-04-28"}, vault_root=root)

        assert result.status == "escalated"
        assert result.stage_reached == "writeback_handling"
        assert "may not leave the vault root" in (result.escalation_reason or "")
        assert not (root.parent / "outside.md").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)
