"""
test_phase9_pass4_maintenance_workflows.py - Focused tests for Pass 4 workflows.

Running:
  .venv/Scripts/python.exe runtime/aor/test_phase9_pass4_maintenance_workflows.py
"""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

import yaml


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.engine import run_workflow


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


def _make_temp_vault() -> Path:
    scratch_root = _VAULT_ROOT / ".codex_tmp_test"
    scratch_root.mkdir(parents=True, exist_ok=True)
    root = scratch_root / f"phase9-pass4-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    (root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")

    required_files = {
        "06_AGENTS/Vault-Map.md": "# Vault Map\n",
        "06_AGENTS/Knowledge-Taxonomy.md": "# Knowledge Taxonomy\n",
        "06_AGENTS/AI-Generated-Output-Bridge.md": "# Bridge\n",
        "00_HOME/Now.md": "# Now\n",
        "README.md": "# Readme\nSee [[Missing-Note]]\n",
        "PROJECT_FOUNDATION.md": "# Project Foundation\n",
        "ROADMAP.md": "# Roadmap\n",
        "01_PROJECTS/ChaseOS/ChaseOS-OS.md": "# ChaseOS OS\n",
        "02_KNOWLEDGE/Knowledge-Index.md": "# Knowledge Index\n",
        "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md": (
            "---\nknowledge_class: source-derived\ntrust_tier: tier-3\nverified_status: verified\n"
            "domain: AI-Agents\n---\n# AI Agent Engineering\n"
        ),
        "02_KNOWLEDGE/AI-Agents/orphan-note.md": "# Orphan\n",
        "02_KNOWLEDGE/AI-Agents/Generated-Ideas/idea-draft.md": (
            "---\nknowledge_class: generated-ideas\ntrust_tier: tier-3\nverified_status: unverified-labeled\n"
            "domain: AI-Agents\nendorsement_status: unendorsed\ngenerated_with: human+claude\npromotion_status: candidate\n---\n"
            "# Idea Draft\n"
        ),
        "03_INPUTS/00_QUARANTINE/ideas/queued-idea.md": (
            "---\npromotion_status: candidate\ndomain: AI-Agents\ngenerated_with: claude\n---\n# Queued Idea\n"
        ),
    }
    for rel_path, content in required_files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    _write_yaml(
        root / "06_AGENTS/role-cards/vault-maintenance.yaml",
        {
            "id": "vault-maintenance",
            "name": "Vault Maintenance Role Card",
            "version": "1.0",
            "description": "Proposal-only graph hygiene role card",
            "owner": "operator",
            "allowed_actions": ["read_vault", "write_hygiene_report"],
            "forbidden_actions": ["write_knowledge_notes", "delete_any_file"],
            "write_scope": ["07_LOGS/Hygiene-Reports/", "07_LOGS/Agent-Activity/"],
            "forbidden_write_zones": ["00_HOME/Now.md", "02_KNOWLEDGE/"],
            "escalation_rules": ["any mutation requested"],
            "required_reads": ["06_AGENTS/Vault-Map.md", "06_AGENTS/Knowledge-Taxonomy.md"],
            "runtime_expectations": ["proposal only"],
        },
    )
    _write_yaml(
        root / "06_AGENTS/role-cards/idea-graduation.yaml",
        {
            "id": "idea-graduation",
            "name": "Idea Graduation Role Card",
            "version": "1.0",
            "description": "Proposal-only idea graduation role card",
            "owner": "operator",
            "allowed_actions": ["read_quarantine", "write_graduation_proposal"],
            "forbidden_actions": ["write_knowledge_notes", "delete_any_file"],
            "write_scope": ["07_LOGS/Graduation-Proposals/", "07_LOGS/Agent-Activity/"],
            "forbidden_write_zones": ["00_HOME/Now.md", "02_KNOWLEDGE/"],
            "escalation_rules": ["any promotion requested"],
            "required_reads": [
                "03_INPUTS/00_QUARANTINE/",
                "06_AGENTS/Knowledge-Taxonomy.md",
                "06_AGENTS/AI-Generated-Output-Bridge.md",
            ],
            "runtime_expectations": ["proposal only"],
        },
    )
    _write_yaml(
        root / "runtime/workflows/registry/graph_hygiene.yaml",
        {
            "id": "graph_hygiene",
            "name": "Graph Hygiene",
            "version": "1.0",
            "description": "Proposal-only graph hygiene workflow",
            "task_type": "graph-hygiene",
            "role_card": "vault-maintenance",
            "trigger_type": "manual",
            "owner": "operator",
            "status": "active",
            "permission_ceiling": "proposal_log_only",
            "writeback_targets": ["07_LOGS/Hygiene-Reports/"],
            "failure_behavior": "escalate",
        },
    )
    _write_yaml(
        root / "runtime/workflows/registry/graduate_ideas.yaml",
        {
            "id": "graduate_ideas",
            "name": "Graduate Ideas",
            "version": "1.0",
            "description": "Proposal-only idea graduation workflow",
            "task_type": "idea-graduation",
            "role_card": "idea-graduation",
            "trigger_type": "manual",
            "owner": "operator",
            "status": "active",
            "permission_ceiling": "proposal_log_only",
            "writeback_targets": ["07_LOGS/Graduation-Proposals/"],
            "failure_behavior": "escalate",
        },
    )
    _write_yaml(
        root / "runtime/aor/task_type_table.yaml",
        {
            "task_types": [
                {
                    "id": "graph-hygiene",
                    "description": "Graph hygiene",
                    "required_reads": ["06_AGENTS/Vault-Map.md", "06_AGENTS/Knowledge-Taxonomy.md"],
                    "optional_reads": ["03_INPUTS/00_QUARANTINE/"],
                    "runtime_class": "read-heavy",
                    "permission_set": ["read_vault", "write_logs"],
                    "permission_ceiling": "proposal_log_only",
                    "writeback_expectations": "report only",
                    "escalation_trigger": ["any mutation requested"],
                },
                {
                    "id": "idea-graduation",
                    "description": "Idea graduation",
                    "required_reads": [
                        "03_INPUTS/00_QUARANTINE/",
                        "06_AGENTS/Knowledge-Taxonomy.md",
                        "06_AGENTS/AI-Generated-Output-Bridge.md",
                    ],
                    "optional_reads": ["02_KNOWLEDGE/"],
                    "runtime_class": "read-heavy",
                    "permission_set": ["read_vault", "write_logs"],
                    "permission_ceiling": "proposal_log_only",
                    "writeback_expectations": "proposal only",
                    "escalation_trigger": ["any canonical write requested"],
                },
                {
                    "id": "unclassified",
                    "description": "sentinel",
                    "required_reads": [],
                    "optional_reads": [],
                    "runtime_class": "escalate",
                    "permission_set": [],
                    "permission_ceiling": "none",
                    "writeback_expectations": "none",
                    "escalation_trigger": ["always"],
                },
            ]
        },
    )
    return root


def test_graph_hygiene_writes_report_only() -> None:
    root = _make_temp_vault()
    try:
        result = run_workflow("graph_hygiene", inputs={"date": "2026-04-09"}, vault_root=root)
        assert result.status == "success"
        report_path = root / "07_LOGS" / "Hygiene-Reports" / "2026-04-09-graph-hygiene.md"
        assert report_path.exists()
        assert "Broken Links" in report_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_graduate_ideas_writes_proposal_only() -> None:
    root = _make_temp_vault()
    try:
        result = run_workflow("graduate_ideas", inputs={"date": "2026-04-09"}, vault_root=root)
        assert result.status == "success"
        proposal_path = root / "07_LOGS" / "Graduation-Proposals" / "2026-04-09-graduate-ideas.md"
        assert proposal_path.exists()
        proposal_text = proposal_path.read_text(encoding="utf-8")
        assert "Suggested destination" in proposal_text
        assert not (root / "02_KNOWLEDGE" / "AI-Agents" / "Queued-Idea.md").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_graph_hygiene_writes_report_only()
    test_graduate_ideas_writes_proposal_only()
    print("Pass 4 maintenance workflow tests passed.")
