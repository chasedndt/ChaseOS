"""Focused tests for the read-only trace_idea workflow foothold."""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

import yaml


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.engine import run_workflow  # noqa: E402
from runtime.aor.registry import load_manifest  # noqa: E402
from runtime.aor.role_cards import load_card  # noqa: E402
from runtime.workflows.trace_idea import run_trace_idea  # noqa: E402


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _make_temp_vault() -> Path:
    scratch_root = _VAULT_ROOT / ".codex_tmp_test"
    scratch_root.mkdir(parents=True, exist_ok=True)
    root = scratch_root / f"trace-idea-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    (root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")

    for rel_path, content in {
        "07_LOGS/Build-Logs/2026-04-24-demo-build-log.md": (
            "# Demo Build Log\n\n"
            "Generated output artifact: report-001\n"
            "Normalized source pack: nsp-demo\n"
        ),
        "07_LOGS/Agent-Activity/Agent-Activity-Index.md": "# Agent Activity Index\n",
        "07_LOGS/Build-Logs/Build-Logs-Index.md": "# Build Logs Index\n",
        "00_HOME/Now.md": "# Now\n- Trace demo run\n",
        "runtime/source_intelligence/workspaces/demo/source_packages/demo_source_package.json": json.dumps(
            {
                "id": "spkg-demo-1",
                "title": "Demo source package",
                "origin_path": "03_INPUTS/00_QUARANTINE/source/demo-note.md",
                "origin_url": None,
                "intake_date": "2026-04-24",
                "package_created_date": "2026-04-24",
                "created_at": "2026-04-24T09:00:00Z",
                "updated_at": "2026-04-24T09:00:00Z",
                "source_type": "markdown",
                "normalized_text": "demo package",
                "normalized_text_char_count": 12,
                "extraction_status": "complete",
                "injection_scan_status": "scanned-clean",
                "user_trust_level": "reviewed",
                "embedding_status": "not-embedded",
            },
            indent=2,
        ),
    }.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    _write_json(
        root / "runtime/acquisition/packs/demo/source_packet_001.json",
        {
            "artifact_id": "sp-demo-1",
            "artifact_type": "source_packet",
            "created_at": "2026-04-24T09:00:00Z",
            "source_id": "spkg-demo-1",
            "source_class": "source_package",
            "source_origin": {
                "kind": "source_package",
                "ref": "runtime/source_intelligence/workspaces/demo/source_packages/demo_source_package.json",
            },
            "provenance": {
                "source_ids": ["spkg-demo-1"],
                "processing_stage": "source_package",
                "verification_status": "operator_reviewed",
                "lineage_chain": [
                    {
                        "stage": "source_package",
                        "ref": "runtime/source_intelligence/workspaces/demo/source_packages/demo_source_package.json",
                        "timestamp": "2026-04-24T09:00:00Z",
                    }
                ],
                "created_at": "2026-04-24T09:00:00Z",
                "last_modified_at": "2026-04-24T09:00:00Z",
                "operator_reviewed_at": "2026-04-24T09:05:00Z",
                "source_refs": ["runtime/source_intelligence/workspaces/demo/source_packages/demo_source_package.json"],
                "audit_refs": ["07_LOGS/Build-Logs/2026-04-24-demo-build-log.md"],
            },
        },
    )
    _write_json(
        root / "runtime/acquisition/packs/demo/source_packet_002.json",
        {
            "artifact_id": "sp-demo-2",
            "artifact_type": "source_packet",
            "created_at": "2026-04-24T09:01:00Z",
            "source_id": "manual-note-1",
            "source_class": "quarantine_note",
            "source_origin": {
                "kind": "quarantine",
                "ref": "03_INPUTS/00_QUARANTINE/source/demo-note.md",
            },
        },
    )
    _write_json(
        root / "runtime/acquisition/packs/demo/normalized_source_pack.json",
        {
            "artifact_id": "nsp-demo",
            "artifact_type": "normalized_source_pack",
            "created_at": "2026-04-24T09:10:00Z",
            "source_packet_refs": ["sp-demo-1", "sp-demo-2"],
            "source_packet_count": 2,
            "audit": {
                "activity_log_ref": "07_LOGS/Agent-Activity/trace-seed.json",
            },
        },
    )
    _write_json(
        root / "runtime/workflows/fixtures/generated/report-001.json",
        {
            "artifact_id": "report-001",
            "artifact_type": "generated_output",
            "created_at": "2026-04-24T10:00:00Z",
            "summary": "Daily report generated from normalized pack",
            "provenance": {
                "source_ids": ["nsp-demo"],
                "processing_stage": "generated",
                "verification_status": "unverified",
                "lineage_chain": [
                    {
                        "stage": "generated",
                        "ref": "runtime/workflows/fixtures/generated/report-001.json",
                        "timestamp": "2026-04-24T10:00:00Z",
                    },
                    {
                        "stage": "normalized",
                        "ref": "runtime/acquisition/packs/demo/normalized_source_pack.json",
                        "timestamp": "2026-04-24T09:10:00Z",
                    },
                ],
                "created_at": "2026-04-24T10:00:00Z",
                "last_modified_at": "2026-04-24T10:00:00Z",
                "operator_reviewed_at": None,
                "source_refs": ["runtime/acquisition/packs/demo/normalized_source_pack.json"],
                "audit_refs": [
                    "07_LOGS/Build-Logs/2026-04-24-demo-build-log.md",
                    "07_LOGS/Agent-Activity/trace-seed.json",
                ],
            },
        },
    )

    _write_yaml(
        root / "runtime/aor/task_type_table.yaml",
        {
            "task_types": [
                {
                    "id": "trace-idea",
                    "description": "Read-only provenance trace workflow",
                    "required_reads": [
                        "runtime/acquisition/",
                        "07_LOGS/Build-Logs/",
                        "07_LOGS/Agent-Activity/",
                    ],
                    "optional_reads": [
                        "runtime/source_intelligence/",
                        "03_INPUTS/00_QUARANTINE/",
                    ],
                    "runtime_class": "read-heavy",
                    "permission_set": ["read_vault", "write_logs"],
                    "permission_ceiling": "report_only",
                    "writeback_expectations": "trace report only; no canonical mutations",
                    "escalation_trigger": [
                        "write outside Trace-Reports or Agent-Activity",
                        "any canonical mutation requested",
                    ],
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
    _write_yaml(
        root / "06_AGENTS/role-cards/trace-idea-readonly.yaml",
        {
            "id": "trace-idea-readonly",
            "name": "Trace Idea Readonly Role Card",
            "version": "1.0",
            "description": "Read-only lineage tracing role card",
            "owner": "operator",
            "allowed_actions": ["read_vault", "write_trace_report", "write_agent_activity_log"],
            "forbidden_actions": [
                "write_protected_files",
                "write_knowledge_notes",
                "write_project_os_files",
                "promote_to_canonical",
                "execute_external_commands",
                "access_network",
            ],
            "write_scope": ["07_LOGS/Trace-Reports/", "07_LOGS/Agent-Activity/"],
            "forbidden_write_zones": ["02_KNOWLEDGE/", "06_AGENTS/", "runtime/", "PROJECT_FOUNDATION.md", "ROADMAP.md"],
            "escalation_rules": ["any canonical mutation requested", "write outside trace reports"],
            "runtime_expectations": ["read-only lineage traversal", "partial lineage is reported honestly"],
        },
    )
    _write_yaml(
        root / "runtime/workflows/registry/trace_idea.yaml",
        {
            "id": "trace_idea",
            "name": "Trace Idea",
            "version": "1.0",
            "description": "Read-only provenance trace workflow",
            "task_type": "trace-idea",
            "role_card": "trace-idea-readonly",
            "trigger_type": "manual",
            "owner": "operator",
            "status": "active",
            "permission_ceiling": "report_only",
            "writeback_targets": ["07_LOGS/Trace-Reports/"],
            "failure_behavior": "escalate",
        },
    )

    return root


def test_trace_idea_returns_ordered_lineage_for_known_artifact() -> None:
    root = _make_temp_vault()
    try:
        result = run_trace_idea(
            inputs={"artifact_id": "report-001", "date": "2026-04-24"},
            vault_root=root,
        )
        trace_result = result["trace_result"]
        assert trace_result["found"] is True
        ordered_ids = [item.get("artifact_id") for item in trace_result["lineage_items"] if item.get("artifact_id")]
        assert ordered_ids[:4] == ["report-001", "nsp-demo", "sp-demo-1", "sp-demo-2"]
        assert "spkg-demo-1" in ordered_ids
        assert trace_result["summary"]["source_artifact_count"] == 3
        assert trace_result["summary"]["derived_artifact_count"] >= 2
        assert any(item.get("classification") == "source_artifact" for item in trace_result["lineage_items"])
        assert any(item.get("classification") == "derived_artifact" for item in trace_result["lineage_items"])
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_trace_idea_returns_clean_not_found_result() -> None:
    root = _make_temp_vault()
    try:
        result = run_trace_idea(
            inputs={"artifact_id": "missing-idea", "date": "2026-04-24"},
            vault_root=root,
        )
        trace_result = result["trace_result"]
        assert trace_result["found"] is False
        assert trace_result["lineage_items"] == []
        assert "not found" in trace_result["message"].lower()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_trace_idea_workflow_writes_only_trace_report_destination() -> None:
    root = _make_temp_vault()
    try:
        result = run_workflow(
            "trace_idea",
            inputs={"artifact_id": "report-001", "date": "2026-04-24"},
            vault_root=root,
        )
        assert result.status == "success"
        assert result.outputs["writeback"]["files_written"] == ["07_LOGS/Trace-Reports/2026-04-24-trace-report-001.md"]
        assert (root / "07_LOGS/Trace-Reports/2026-04-24-trace-report-001.md").exists()
        assert not (root / "02_KNOWLEDGE/new-trace-note.md").exists()
        assert any(path.name.endswith(".json") for path in (root / "07_LOGS/Agent-Activity").glob("*.json"))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_live_manifest_and_role_card_validate() -> None:
    manifest = load_manifest("trace_idea", vault_root=_VAULT_ROOT)
    role_card = load_card("trace-idea-readonly", vault_root=_VAULT_ROOT)

    assert manifest is not None
    assert manifest["writeback_targets"] == ["07_LOGS/Trace-Reports/"]
    assert role_card is not None
    assert "07_LOGS/Trace-Reports/" in role_card["write_scope"]
