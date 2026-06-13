"""
test_studio_service_layer.py — Tests for ChaseOS Studio Service Layer

Covers:
  TestValidation          (12 tests) — ActionSpec validation rules
  TestApprovalQueue       (8 tests)  — queue/approve/reject/list lifecycle
  TestExecuteWrite        (6 tests)  — no-approval write path
  TestExecuteApproved     (6 tests)  — approval-gated execute path
  TestPathGuards          (6 tests)  — traversal + extension + protected-file guards
  TestAuditLog            (4 tests)  — audit record writing
  TestDryRun              (4 tests)  — dry_run mode
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.service import (
    ActionSpec,
    ActionResult,
    ApprovalRequest,
    StudioService,
    StudioServiceError,
    ValidationResult,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "digest").mkdir(parents=True)
    (vault / "05_TEMPLATES").mkdir(parents=True)
    (vault / "07_LOGS" / "Daily").mkdir(parents=True)
    return vault


def _svc(vault: Path, dry_run: bool = False) -> StudioService:
    return StudioService(vault, dry_run=dry_run)


def _write_spec(path: str = "07_LOGS/Daily/2026-05-01.md", content: str = "# Note") -> ActionSpec:
    return ActionSpec(action_type="write_file", target_path=path, content=content)


def _create_spec(path: str = "07_LOGS/Daily/2026-05-01.md", content: str = "# Note") -> ActionSpec:
    return ActionSpec(action_type="create_file", target_path=path, content=content)


def _delete_spec(path: str = "07_LOGS/Daily/old.md") -> ActionSpec:
    return ActionSpec(action_type="delete_file", target_path=path)


# ── TestValidation ────────────────────────────────────────────────────────────

class TestValidation:
    def test_valid_daily_log_write(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        result = svc.validate_action(_write_spec())
        assert result.valid
        assert not result.gate_blocked
        assert not result.errors

    def test_forbidden_extension_py(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="runtime/evil.py", content="pass")
        result = svc.validate_action(spec)
        assert result.gate_blocked
        assert not result.valid
        assert any(".py" in e for e in result.errors)

    def test_forbidden_extension_sh(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="scripts/evil.sh", content="echo hi")
        result = svc.validate_action(spec)
        assert result.gate_blocked

    def test_protected_file_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="CLAUDE.md", content="# Modified")
        result = svc.validate_action(spec)
        assert result.gate_blocked
        assert any("protected file" in e.lower() for e in result.errors)

    def test_protected_soul_md_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="SOUL.md", content="# Modified")
        result = svc.validate_action(spec)
        assert result.gate_blocked

    def test_delete_requires_approval(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        result = svc.validate_action(_delete_spec())
        assert result.approval_required

    def test_canonical_path_requires_approval(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _write_spec(path="02_KNOWLEDGE/Trading/notes.md")
        result = svc.validate_action(spec)
        assert result.approval_required
        assert result.valid

    def test_daily_log_path_does_not_require_approval(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        result = svc.validate_action(_write_spec())
        assert not result.approval_required

    def test_write_without_content_invalid(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="07_LOGS/Daily/x.md", content=None)
        result = svc.validate_action(spec)
        assert not result.valid
        assert any("content" in e for e in result.errors)

    def test_promote_quarantine_must_target_quarantine_path(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="promote_quarantine", target_path="01_PROJECTS/bad.md")
        result = svc.validate_action(spec)
        assert result.gate_blocked

    def test_promote_quarantine_valid_target(self, tmp_path):
        vault = _make_vault(tmp_path)
        q_path = "03_INPUTS/00_QUARANTINE/digest/item.md"
        (vault / q_path).write_text("# Item", encoding="utf-8")
        svc = _svc(vault)
        spec = ActionSpec(
            action_type="promote_quarantine",
            target_path=q_path,
            metadata={"destination_path": "02_KNOWLEDGE/Domain/item.md"},
        )
        result = svc.validate_action(spec)
        assert not result.gate_blocked

    def test_empty_target_path_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="", content="x")
        result = svc.validate_action(spec)
        assert result.gate_blocked


# ── TestApprovalQueue ─────────────────────────────────────────────────────────

class TestApprovalQueue:
    def test_queue_creates_pending_record(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="delete_file", target_path="07_LOGS/Daily/old.md")
        req = svc.queue_for_approval(spec)
        assert req.status == "pending"
        assert req.approval_id
        approval_dir = vault / StudioService.APPROVAL_DIR
        assert approval_dir.exists()
        assert any(approval_dir.iterdir())

    def test_queue_record_is_loadable(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _delete_spec()
        req = svc.queue_for_approval(spec)
        loaded = svc.get_approval(req.approval_id)
        assert loaded is not None
        assert loaded.approval_id == req.approval_id
        assert loaded.status == "pending"
        assert loaded.action_spec.target_path == spec.target_path

    def test_approve_transitions_to_approved(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        req = svc.queue_for_approval(_delete_spec())
        approved = svc.approve(req.approval_id)
        assert approved.status == "approved"
        assert approved.reviewed_by == "operator"

    def test_reject_transitions_to_rejected(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        req = svc.queue_for_approval(_delete_spec())
        rejected = svc.reject(req.approval_id, reason="not needed")
        assert rejected.status == "rejected"
        assert rejected.reason == "not needed"

    def test_cannot_transition_approved_twice(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        req = svc.queue_for_approval(_delete_spec())
        svc.approve(req.approval_id)
        with pytest.raises(StudioServiceError, match="Only 'pending'"):
            svc.approve(req.approval_id)

    def test_list_pending_returns_only_pending(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        req1 = svc.queue_for_approval(_delete_spec("07_LOGS/Daily/a.md"))
        req2 = svc.queue_for_approval(_delete_spec("07_LOGS/Daily/b.md"))
        svc.approve(req1.approval_id)
        pending = svc.list_pending()
        ids = [r.approval_id for r in pending]
        assert req2.approval_id in ids
        assert req1.approval_id not in ids

    def test_get_nonexistent_approval_returns_none(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        assert svc.get_approval("does-not-exist-xxx") is None

    def test_approval_record_written_as_json(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        req = svc.queue_for_approval(_delete_spec())
        approval_dir = vault / StudioService.APPROVAL_DIR
        json_files = list(approval_dir.glob("*.json"))
        assert len(json_files) == 1
        data = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert data["status"] == "pending"
        assert "action_spec" in data


# ── TestExecuteWrite ──────────────────────────────────────────────────────────

class TestExecuteWrite:
    def test_creates_file_at_target_path(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _create_spec(path="07_LOGS/Daily/2026-05-01.md", content="# Log")
        result = svc.execute_write(spec)
        assert result.status == "completed"
        assert "07_LOGS/Daily/2026-05-01.md" in result.writes
        assert (vault / "07_LOGS" / "Daily" / "2026-05-01.md").exists()

    def test_overwrites_existing_file(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        path = vault / "07_LOGS" / "Daily" / "existing.md"
        path.write_text("old content", encoding="utf-8")
        spec = _write_spec(path="07_LOGS/Daily/existing.md", content="new content")
        result = svc.execute_write(spec)
        assert result.status == "completed"
        assert path.read_text(encoding="utf-8") == "new content"

    def test_raises_on_gate_blocked_spec(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="CLAUDE.md", content="# Modified")
        with pytest.raises(StudioServiceError, match="Gate-blocked"):
            svc.execute_write(spec)

    def test_raises_when_approval_required(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _write_spec(path="02_KNOWLEDGE/Domain/note.md")
        with pytest.raises(StudioServiceError, match="requires approval"):
            svc.execute_write(spec)

    def test_creates_parent_directories(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _create_spec(path="07_LOGS/Daily/nested/deeply/note.md", content="# Deep")
        result = svc.execute_write(spec)
        assert result.status == "completed"
        assert (vault / "07_LOGS/Daily/nested/deeply/note.md").exists()

    def test_result_includes_writes_list(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _create_spec(path="07_LOGS/Daily/2026-05-02.md", content="# Log")
        result = svc.execute_write(spec)
        assert len(result.writes) == 1
        assert result.writes[0] == "07_LOGS/Daily/2026-05-02.md"


# ── TestExecuteApproved ───────────────────────────────────────────────────────

class TestExecuteApproved:
    def test_executes_approved_write(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _write_spec(path="02_KNOWLEDGE/Domain/promoted.md", content="# Promoted")
        req = svc.queue_for_approval(spec)
        svc.approve(req.approval_id)
        result = svc.execute_approved(req.approval_id)
        assert result.status == "completed"
        assert (vault / "02_KNOWLEDGE" / "Domain" / "promoted.md").exists()
        loaded = svc.get_approval(req.approval_id)
        assert loaded.status == "executed"
        assert loaded.execution_status == "completed"
        assert loaded.result_action_id == result.action_id

    def test_result_links_approval_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _delete_spec("07_LOGS/Daily/note.md")
        (vault / "07_LOGS" / "Daily" / "note.md").write_text("# Note", encoding="utf-8")
        req = svc.queue_for_approval(spec)
        svc.approve(req.approval_id)
        result = svc.execute_approved(req.approval_id)
        assert result.approval_id == req.approval_id

    def test_raises_on_missing_approval(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        with pytest.raises(StudioServiceError, match="not found"):
            svc.execute_approved("nonexistent-id")

    def test_raises_on_rejected_approval(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _delete_spec()
        req = svc.queue_for_approval(spec)
        svc.reject(req.approval_id)
        with pytest.raises(StudioServiceError, match="Cannot execute"):
            svc.execute_approved(req.approval_id)

    def test_raises_on_pending_approval(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _delete_spec()
        req = svc.queue_for_approval(spec)
        with pytest.raises(StudioServiceError, match="Cannot execute"):
            svc.execute_approved(req.approval_id)

    def test_delete_removes_file(self, tmp_path):
        vault = _make_vault(tmp_path)
        target = vault / "07_LOGS" / "Daily" / "to-delete.md"
        target.write_text("# Old note", encoding="utf-8")
        svc = _svc(vault)
        spec = _delete_spec("07_LOGS/Daily/to-delete.md")
        req = svc.queue_for_approval(spec)
        svc.approve(req.approval_id)
        result = svc.execute_approved(req.approval_id)
        assert result.status == "completed"
        assert not target.exists()

    def test_duplicate_execute_approved_blocks_after_first_execution(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        req = svc.queue_for_approval(_write_spec(path="02_KNOWLEDGE/Domain/once.md", content="# Once"))
        svc.approve(req.approval_id)
        svc.execute_approved(req.approval_id)

        with pytest.raises(StudioServiceError, match="Only 'approved'"):
            svc.execute_approved(req.approval_id)

        loaded = svc.get_approval(req.approval_id)
        assert loaded.status == "executed"


# ── TestPathGuards ────────────────────────────────────────────────────────────

class TestPathGuards:
    def test_traversal_above_vault_root_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="../../../etc/passwd", content="evil")
        result = svc.validate_action(spec)
        assert result.gate_blocked
        assert any("traversal" in e.lower() for e in result.errors)

    def test_absolute_path_outside_vault_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="/etc/hosts", content="evil")
        result = svc.validate_action(spec)
        assert result.gate_blocked

    def test_ps1_extension_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="07_LOGS/run.ps1", content="echo hi")
        result = svc.validate_action(spec)
        assert result.gate_blocked

    def test_bat_extension_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="07_LOGS/run.bat", content="echo hi")
        result = svc.validate_action(spec)
        assert result.gate_blocked

    def test_markdown_extension_allowed(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _write_spec(path="07_LOGS/Daily/safe.md")
        result = svc.validate_action(spec)
        assert not result.gate_blocked

    def test_json_extension_allowed(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = ActionSpec(action_type="write_file", target_path="07_LOGS/data.json", content="{}")
        result = svc.validate_action(spec)
        assert not result.gate_blocked


# ── TestAuditLog ──────────────────────────────────────────────────────────────

class TestAuditLog:
    def test_execute_write_creates_audit_entry(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _create_spec(path="07_LOGS/Daily/2026-05-01.md", content="# Log")
        svc.execute_write(spec)
        audit_dir = vault / "07_LOGS" / "Agent-Activity"
        entries = list(audit_dir.glob("*studio*"))
        assert len(entries) >= 1

    def test_audit_entry_contains_action_type(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _create_spec(path="07_LOGS/Daily/2026-05-01.md", content="# Log")
        result = svc.execute_write(spec)
        audit_dir = vault / "07_LOGS" / "Agent-Activity"
        entries = list(audit_dir.glob("*studio*"))
        content = entries[0].read_text(encoding="utf-8")
        assert "create_file" in content

    def test_audit_entry_contains_boundary_statement(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _create_spec(path="07_LOGS/Daily/2026-05-01.md", content="# Log")
        svc.execute_write(spec)
        audit_dir = vault / "07_LOGS" / "Agent-Activity"
        entries = list(audit_dir.glob("*studio*"))
        content = entries[0].read_text(encoding="utf-8")
        assert "Studio Service Layer" in content
        assert "No bypasses" in content

    def test_execute_approved_also_creates_audit(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault)
        spec = _write_spec(path="02_KNOWLEDGE/Domain/note.md", content="# Note")
        req = svc.queue_for_approval(spec)
        svc.approve(req.approval_id)
        svc.execute_approved(req.approval_id)
        audit_dir = vault / "07_LOGS" / "Agent-Activity"
        entries = list(audit_dir.glob("*studio*"))
        assert len(entries) >= 1


# ── TestDryRun ────────────────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_does_not_write_file(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault, dry_run=True)
        spec = _create_spec(path="07_LOGS/Daily/dry.md", content="# Dry run")
        result = svc.execute_write(spec)
        assert result.status == "dry_run"
        assert not (vault / "07_LOGS" / "Daily" / "dry.md").exists()

    def test_dry_run_does_not_write_audit(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault, dry_run=True)
        spec = _create_spec(path="07_LOGS/Daily/dry.md", content="# Dry run")
        svc.execute_write(spec)
        audit_dir = vault / "07_LOGS" / "Agent-Activity"
        entries = list(audit_dir.glob("*studio*")) if audit_dir.exists() else []
        assert entries == []

    def test_dry_run_approval_queue_skips_persistence(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault, dry_run=True)
        req = svc.queue_for_approval(_delete_spec())
        approval_dir = vault / StudioService.APPROVAL_DIR
        assert not approval_dir.exists() or not any(approval_dir.iterdir())

    def test_dry_run_validates_normally(self, tmp_path):
        vault = _make_vault(tmp_path)
        svc = _svc(vault, dry_run=True)
        spec = ActionSpec(action_type="write_file", target_path="CLAUDE.md", content="# Modified")
        with pytest.raises(StudioServiceError, match="Gate-blocked"):
            svc.execute_write(spec)
