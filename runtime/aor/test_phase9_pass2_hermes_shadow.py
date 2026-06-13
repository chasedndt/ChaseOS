"""
test_phase9_pass2_hermes_shadow.py - Focused tests for Hermes shadow activation.

Running:
  .venv/Scripts/python.exe runtime/aor/test_phase9_pass2_hermes_shadow.py
"""

from __future__ import annotations

import sys
import shutil
import uuid
from pathlib import Path

import yaml


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.engine import run_workflow
from runtime.chaseos_gate import load_adapter_manifest, validate_manifest


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


def _make_temp_vault() -> Path:
    scratch_root = _VAULT_ROOT / "runtime" / "aor" / "_tmp_tests"
    scratch_root.mkdir(parents=True, exist_ok=True)
    root = scratch_root / f"test-vault-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    (root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")

    required_reads = {
        "00_HOME/Now.md": "# Now\nPhase 9 - Pass 2 next\n",
        "01_PROJECTS/ChaseOS/ChaseOS-OS.md": "# ChaseOS OS\n",
        "HERMES.md": "# HERMES\n",
        "06_AGENTS/Hermes-Adapter-Spec.md": "# Hermes Adapter Spec\n",
        "06_AGENTS/Hermes-Workflow-Boundaries.md": "# Hermes Workflow Boundaries\n",
        "06_AGENTS/Hermes-Memory-Boundary.md": "# Hermes Memory Boundary\n",
        "07_LOGS/Build-Logs/2026-04-08-ChaseOS-hermes-integration-binding-pass.md": "docs-only\n",
        "07_LOGS/Build-Logs/2026-04-09-ChaseOS-hermes-permission-matrix-closure.md": (
            "Open Loops After This Pass\nNone from the Hermes planning/binding chain.\n"
        ),
    }
    for rel_path, content in required_reads.items():
        full_path = root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    _write_yaml(
        root / ".chaseos/hermes_config.yaml",
        {
            "runtime_id": "hermes-shadow",
            "adapter_manifest": "runtime/policy/adapters/hermes.yaml",
            "status": "shadow-active",
            "mode": "approval-first-shadow",
            "approved_workflows": ["hermes_operator_today_shadow"],
            "readable_path_allowlist": list(required_reads.keys()),
            "writable_path_allowlist": [
                "07_LOGS/Agent-Activity/",
                "07_LOGS/Build-Logs/",
                "07_LOGS/Operator-Briefs/_drafts/",
                "99_ARCHIVE/Documentation-History/",
            ],
            "forbidden_path_list": ["00_HOME/Now.md", "01_PROJECTS/", "02_KNOWLEDGE/"],
            "allowed_command_families": ["filesystem.read_text", "filesystem.write_markdown"],
            "forbidden_command_families": ["shell.execute", "network.http"],
            "connector_policy": {
                "network_connectors": "disabled",
                "gateway_inputs": "disabled",
                "delivery_connectors": "disabled",
            },
            "approval_model": {"default": "deny"},
            "promotion_writeback_rules": {"canonical_promotion": "forbidden"},
        },
    )

    _write_yaml(
        root / "06_AGENTS/role-cards/hermes-operator-shadow.yaml",
        {
            "id": "hermes-operator-shadow",
            "name": "Hermes Operator Shadow Role Card",
            "version": "1.0",
            "description": "Shadow role card",
            "owner": "operator",
            "allowed_actions": ["read_declared_context_files"],
            "forbidden_actions": ["write_protected_files"],
            "write_scope": [
                "07_LOGS/Agent-Activity/",
                "07_LOGS/Build-Logs/",
                "07_LOGS/Operator-Briefs/_drafts/",
                "99_ARCHIVE/Documentation-History/",
            ],
            "forbidden_write_zones": ["00_HOME/Now.md", "01_PROJECTS/", "02_KNOWLEDGE/"],
            "escalation_rules": ["any undeclared read attempted"],
            "required_reads": list(required_reads.keys()),
            "runtime_expectations": ["shadow mode only"],
        },
    )

    _write_yaml(
        root / "runtime/workflows/registry/hermes_operator_today_shadow.yaml",
        {
            "id": "hermes_operator_today_shadow",
            "name": "Hermes Operator Today Shadow",
            "version": "1.0",
            "description": "Shadow workflow",
            "task_type": "operator-briefing-shadow",
            "role_card": "hermes-operator-shadow",
            "trigger_type": "manual",
            "owner": "operator",
            "status": "active",
            "permission_ceiling": "shadow_log_only",
            "writeback_targets": [
                "07_LOGS/Agent-Activity/",
                "07_LOGS/Build-Logs/",
                "07_LOGS/Operator-Briefs/_drafts/",
                "99_ARCHIVE/Documentation-History/",
            ],
            "failure_behavior": "escalate",
            "required_reads": list(required_reads.keys()),
        },
    )
    return root


def test_hermes_adapter_manifest_is_valid() -> None:
    manifest = load_adapter_manifest("hermes")
    assert manifest["adapter_id"] == "hermes"
    assert validate_manifest(manifest) == []


def test_shadow_workflow_creates_only_draft_and_audit_outputs() -> None:
    tmp = _make_temp_vault()
    root = tmp
    try:
        result = run_workflow(
            "hermes_operator_today_shadow",
            inputs={"date": "2026-04-09"},
            vault_root=root,
        )
        assert result.status == "success"
        assert result.outputs["run"]["handler_status"] == "completed"

        created = result.outputs["run"]["created_files"]
        for rel_path in created.values():
            assert (root / rel_path).exists()

        assert not (root / "02_KNOWLEDGE").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_hermes_adapter_manifest_is_valid()
    test_shadow_workflow_creates_only_draft_and_audit_outputs()
    print("Hermes shadow activation tests passed.")
