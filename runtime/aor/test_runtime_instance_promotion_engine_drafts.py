"""
test_runtime_instance_promotion_engine_drafts.py — ChaseOS Phase 9

Draft-only engine-awareness tests for runtime-instance promotion workflows.

Covers:
  - OpenClaw draft promotion workflow escalates at workflow_lookup
  - Hermes draft promotion workflow escalates at workflow_lookup
  - Draft workflows still write audit records on escalation
  - Escalation preserves the constitutional rule that only status='active' may execute

Running:
  .venv/Scripts/python.exe -m pytest runtime/aor/test_runtime_instance_promotion_engine_drafts.py -q
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.engine import run_workflow


def _make_temp_vault() -> Path:
    scratch_root = _VAULT_ROOT / "runtime" / "aor" / "_tmp_tests"
    scratch_root.mkdir(parents=True, exist_ok=True)
    root = scratch_root / f"promotion-engine-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)

    (root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
    (root / "00_HOME").mkdir(parents=True, exist_ok=True)
    (root / "00_HOME" / "Now.md").write_text("# Now\n\nPhase 9 ACTIVE.\n", encoding="utf-8")
    (root / "07_LOGS" / "Agent-Activity").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True, exist_ok=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "aor").mkdir(parents=True, exist_ok=True)
    return root


def _copy_runtime_instance_promotion_drafts(root: Path) -> None:
    files_to_copy = [
        ("runtime/workflows/registry/openclaw_promote_note.yaml", "runtime/workflows/registry/openclaw_promote_note.yaml"),
        ("runtime/workflows/registry/hermes_promote_note.yaml", "runtime/workflows/registry/hermes_promote_note.yaml"),
        ("06_AGENTS/role-cards/openclaw-promotion-review.yaml", "06_AGENTS/role-cards/openclaw-promotion-review.yaml"),
        ("06_AGENTS/role-cards/hermes-promotion-review.yaml", "06_AGENTS/role-cards/hermes-promotion-review.yaml"),
        ("runtime/aor/task_type_table.yaml", "runtime/aor/task_type_table.yaml"),
    ]

    for src_rel, dst_rel in files_to_copy:
        src = _VAULT_ROOT / src_rel
        dst = root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)



def _latest_audit_record(root: Path) -> dict:
    audit_dir = root / "07_LOGS" / "Agent-Activity"
    audit_files = sorted(audit_dir.glob("*.json"))
    assert audit_files, "expected an audit record to be written"
    return json.loads(audit_files[-1].read_text(encoding="utf-8"))



def test_openclaw_draft_promotion_workflow_escalates_before_execution() -> None:
    root = _make_temp_vault()
    try:
        _copy_runtime_instance_promotion_drafts(root)

        result = run_workflow(
            "openclaw_promote_note",
            inputs={"candidate_path": "02_KNOWLEDGE/test.md"},
            vault_root=root,
            runtime_id="openclaw",
        )

        assert result.status == "escalated"
        assert result.stage_reached == "workflow_lookup"
        assert "status='active'" in (result.escalation_reason or "")

        audit = _latest_audit_record(root)
        assert audit["workflow_id"] == "openclaw_promote_note"
        assert audit["status"] == "escalated"
        assert audit["stage_reached"] == "workflow_lookup"
    finally:
        shutil.rmtree(root, ignore_errors=True)



def test_hermes_draft_promotion_workflow_escalates_before_execution() -> None:
    root = _make_temp_vault()
    try:
        _copy_runtime_instance_promotion_drafts(root)

        result = run_workflow(
            "hermes_promote_note",
            inputs={"candidate_path": "02_KNOWLEDGE/test.md"},
            vault_root=root,
            runtime_id="hermes",
        )

        assert result.status == "escalated"
        assert result.stage_reached == "workflow_lookup"
        assert "status='active'" in (result.escalation_reason or "")

        audit = _latest_audit_record(root)
        assert audit["workflow_id"] == "hermes_promote_note"
        assert audit["status"] == "escalated"
        assert audit["stage_reached"] == "workflow_lookup"
    finally:
        shutil.rmtree(root, ignore_errors=True)
