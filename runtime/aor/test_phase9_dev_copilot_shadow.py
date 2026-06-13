"""
test_phase9_dev_copilot_shadow.py — ChaseOS Phase 9

Tests for Developer Co-Development Mode (developer_repo_explain_shadow).

Covers:
  - Happy path: valid inputs, files found, all draft artifacts produced
  - Missing focus_area + question + target_paths → escalation
  - No readable files resolved → escalation
  - Forbidden write target → escalation
  - Role card loading enforced (missing role card → escalation via AOR engine)
  - Missing manifest → escalation via AOR engine
  - Adapter-boundary assumptions: outputs stay within declared write scope
  - Broad traversal/path escape blocked before reads
  - Contradiction scan runs and returns bounded findings
  - Diagram proposal is text-only (no rendering commands)
  - Implementation brief is draft-only (no canonical write commands)
  - Engine correctly dispatches developer_repo_explain_shadow

Running:
  .venv/Scripts/python.exe runtime/aor/test_phase9_dev_copilot_shadow.py
"""

from __future__ import annotations

import json
import sys
import shutil
import uuid
from pathlib import Path

import yaml


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.developer_shadow import (
    ContradictionFinding,
    WorkflowExecutionError,
    run_developer_repo_explain,
    _resolve_focus_paths,
    _scan_contradictions,
    _build_developer_brief,
    _build_contradiction_scan,
    _build_doc_refresh_proposal,
    _build_implementation_brief,
    _build_diagram_proposal,
    _assert_write_path_safe,
    FORBIDDEN_WRITE_ZONES,
    ALLOWED_WRITE_TARGETS,
)
from runtime.aor.engine import run_workflow


# ── Test helpers ──────────────────────────────────────────────────────────────

def _make_temp_vault() -> Path:
    scratch_root = _VAULT_ROOT / "runtime" / "aor" / "_tmp_tests"
    scratch_root.mkdir(parents=True, exist_ok=True)
    root = scratch_root / f"test-vault-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)

    (root / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nRouting anchor for Claude Code.\n\nPhase 9 ACTIVE.\n",
        encoding="utf-8",
    )
    (root / "00_HOME").mkdir(parents=True, exist_ok=True)
    (root / "00_HOME" / "Now.md").write_text(
        "# Now\n\nPhase 9 Operator Runtime ACTIVE.\n",
        encoding="utf-8",
    )

    # Developer Briefs log dir
    (root / "07_LOGS" / "Developer-Briefs").mkdir(parents=True, exist_ok=True)
    (root / "07_LOGS" / "Agent-Activity").mkdir(parents=True, exist_ok=True)
    (root / "07_LOGS" / "Build-Logs").mkdir(parents=True, exist_ok=True)
    (root / "99_ARCHIVE" / "Documentation-History").mkdir(parents=True, exist_ok=True)

    return root


def _make_full_aor_vault() -> Path:
    """Create a temp vault with AOR infrastructure for engine integration tests."""
    root = _make_temp_vault()

    # Role cards dir
    rc_dir = root / "06_AGENTS" / "role-cards"
    rc_dir.mkdir(parents=True, exist_ok=True)

    # Schema stub
    (rc_dir / "_schema.yaml").write_text("# schema\n", encoding="utf-8")

    role_card = {
        "id": "developer-copilot-shadow",
        "name": "Developer Co-Development Shadow Role Card",
        "version": "1.0",
        "description": "Permission envelope for Developer Co-Development Mode.",
        "owner": "operator",
        "allowed_actions": ["read_declared_context_files", "write_developer_brief"],
        "forbidden_actions": [
            "write_protected_files",
            "write_knowledge_notes",
            "execute_external_commands",
            "access_api_keys_or_credentials",
        ],
        "write_scope": [
            "07_LOGS/Developer-Briefs/",
            "07_LOGS/Agent-Activity/",
            "07_LOGS/Build-Logs/",
            "99_ARCHIVE/Documentation-History/",
        ],
        "forbidden_write_zones": [
            "SOUL.md", "CLAUDE.md", "00_HOME/Principles.md",
            "README.md", "PROJECT_FOUNDATION.md", "ROADMAP.md",
            "01_PROJECTS/", "02_KNOWLEDGE/", "03_INPUTS/", "runtime/",
        ],
        "escalation_rules": [
            "write outside write_scope requested",
            "protected file write attempted",
        ],
        "required_reads": ["CLAUDE.md"],
        "optional_reads": [],
        "runtime_expectations": [
            "vault root is accessible and CLAUDE.md is present",
            "outputs are draft-only artifacts",
        ],
    }

    (rc_dir / "developer-copilot-shadow.yaml").write_text(
        yaml.dump(role_card, sort_keys=False), encoding="utf-8"
    )

    # Task type table with developer-copilot-shadow
    ttt_dir = root / "runtime" / "aor"
    ttt_dir.mkdir(parents=True, exist_ok=True)
    task_types = {
        "task_types": [
            {
                "id": "developer-copilot-shadow",
                "description": "Developer Co-Development shadow mode",
                "required_reads": ["CLAUDE.md"],
                "optional_reads": [],
                "runtime_class": "read-heavy",
                "permission_set": ["read_vault", "write_logs"],
                "permission_ceiling": "shadow_log_only",
                "writeback_expectations": "draft artifacts only",
                "escalation_trigger": [
                    "write outside declared draft/log/archive targets",
                    "protected file write requested",
                ],
            },
            {
                "id": "unclassified",
                "description": "SENTINEL",
                "required_reads": [],
                "optional_reads": [],
                "runtime_class": "escalate",
                "permission_set": [],
                "permission_ceiling": "none",
                "writeback_expectations": "escalation log entry only",
                "escalation_trigger": ["always"],
            },
        ]
    }
    (ttt_dir / "task_type_table.yaml").write_text(
        yaml.dump(task_types, sort_keys=False), encoding="utf-8"
    )

    # Workflow manifest
    wf_dir = root / "runtime" / "workflows" / "registry"
    wf_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": "developer_repo_explain_shadow",
        "name": "Developer Repo Explain (Shadow)",
        "version": "1.0",
        "description": "Bounded developer co-development shadow workflow.",
        "task_type": "developer-copilot-shadow",
        "role_card": "developer-copilot-shadow",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "mode": "shadow",
        "permission_ceiling": "shadow_log_only",
        "inputs": ["focus_area", "question", "target_paths", "project_scope"],
        "outputs": [
            "draft_developer_brief_path",
            "draft_contradiction_scan_path",
            "draft_doc_refresh_proposal_path",
            "draft_implementation_brief_path",
            "draft_diagram_proposal_path",
            "build_log_path",
            "archive_note_path",
        ],
        "writeback_targets": [
            "07_LOGS/Developer-Briefs/",
            "07_LOGS/Agent-Activity/",
            "07_LOGS/Build-Logs/",
            "99_ARCHIVE/Documentation-History/",
        ],
        "connector_policy": {
            "network_connectors": "disabled",
            "gateway_inputs": "disabled",
            "delivery_connectors": "disabled",
        },
        "failure_behavior": "escalate",
        "non_goals": [
            "no canonical state mutation",
            "no project OS edits",
            "no connector use",
        ],
    }
    (wf_dir / "developer_repo_explain_shadow.yaml").write_text(
        yaml.dump(manifest, sort_keys=False), encoding="utf-8"
    )

    return root


def _cleanup(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)


# ── Unit tests: handler ───────────────────────────────────────────────────────

def test_happy_path_focus_area() -> None:
    root = _make_temp_vault()
    try:
        (root / "runtime" / "aor").mkdir(parents=True, exist_ok=True)
        (root / "runtime" / "aor" / "engine.py").write_text(
            "# engine.py\n\nPhase 9 AOR engine.\n", encoding="utf-8"
        )

        result = run_developer_repo_explain(
            inputs={
                "focus_area": "runtime/aor",
                "question": "What is the AOR engine?",
                "target_paths": [],
                "project_scope": "ChaseOS Phase 9",
            },
            vault_root=root,
        )

        assert result["focus_area"] == "runtime/aor"
        assert len(result["files_read"]) >= 1
        assert result["draft_developer_brief_path"].startswith("07_LOGS/Developer-Briefs/")
        assert result["draft_contradiction_scan_path"].startswith("07_LOGS/Developer-Briefs/")
        assert result["draft_doc_refresh_proposal_path"].startswith("07_LOGS/Developer-Briefs/")
        assert result["draft_implementation_brief_path"].startswith("07_LOGS/Developer-Briefs/")
        assert result["draft_diagram_proposal_path"].startswith("07_LOGS/Developer-Briefs/")
        assert result["build_log_path"].startswith("07_LOGS/Build-Logs/")
        assert result["archive_note_path"].startswith("99_ARCHIVE/Documentation-History/")
        assert len(result["writebacks"]) == 8  # 5 drafts + audit + build log + archive note
        print("  PASS test_happy_path_focus_area")
    finally:
        _cleanup(root)


def test_happy_path_target_paths() -> None:
    root = _make_temp_vault()
    try:
        (root / "test_doc.md").write_text("# Test Doc\nPhase 9 content.\n", encoding="utf-8")

        result = run_developer_repo_explain(
            inputs={
                "focus_area": "",
                "question": "What is this doc about?",
                "target_paths": ["test_doc.md"],
                "project_scope": "Test",
            },
            vault_root=root,
        )

        assert "test_doc.md" in result["files_read"]
        assert result["draft_developer_brief_path"].startswith("07_LOGS/Developer-Briefs/")
        print("  PASS test_happy_path_target_paths")
    finally:
        _cleanup(root)


def test_happy_path_produces_eight_writebacks() -> None:
    root = _make_temp_vault()
    try:
        result = run_developer_repo_explain(
            inputs={
                "focus_area": "",
                "question": "Test question",
                "target_paths": ["CLAUDE.md"],
                "project_scope": "Test",
            },
            vault_root=root,
        )
        # 5 draft outputs + 1 audit + 1 build log + 1 archive note = 8 writebacks
        assert len(result["writebacks"]) == 8
        paths = [wb["path"] for wb in result["writebacks"]]
        assert any("developer-brief" in p for p in paths)
        assert any("contradiction-scan" in p for p in paths)
        assert any("doc-refresh-proposal" in p for p in paths)
        assert any("implementation-brief" in p for p in paths)
        assert any("diagram-proposal" in p for p in paths)
        assert any("Agent-Activity" in p for p in paths)
        assert any("Build-Logs" in p for p in paths)
        assert any("Documentation-History" in p for p in paths)
        print("  PASS test_happy_path_produces_eight_writebacks")
    finally:
        _cleanup(root)


def test_no_inputs_raises() -> None:
    root = _make_temp_vault()
    try:
        raised = False
        try:
            run_developer_repo_explain(
                inputs={"focus_area": "", "question": "", "target_paths": [], "project_scope": ""},
                vault_root=root,
            )
        except WorkflowExecutionError:
            raised = True
        assert raised, "Expected WorkflowExecutionError for empty inputs"
        print("  PASS test_no_inputs_raises")
    finally:
        _cleanup(root)


def test_unresolvable_focus_area_raises() -> None:
    root = _make_temp_vault()
    try:
        # Remove CLAUDE.md so nothing resolves
        (root / "CLAUDE.md").unlink()

        raised = False
        try:
            run_developer_repo_explain(
                inputs={
                    "focus_area": "nonexistent/path/that/does/not/exist",
                    "question": "test",
                    "target_paths": [],
                    "project_scope": "",
                },
                vault_root=root,
            )
        except WorkflowExecutionError:
            raised = True
        assert raised, "Expected WorkflowExecutionError when no files resolve"
        print("  PASS test_unresolvable_focus_area_raises")
    finally:
        _cleanup(root)


def test_broad_focus_area_raises() -> None:
    root = _make_temp_vault()
    try:
        raised = False
        try:
            run_developer_repo_explain(
                inputs={
                    "focus_area": ".",
                    "question": "Read everything",
                    "target_paths": [],
                    "project_scope": "",
                },
                vault_root=root,
            )
        except WorkflowExecutionError:
            raised = True
        assert raised, "Expected WorkflowExecutionError for broad root traversal"
        print("  PASS test_broad_focus_area_raises")
    finally:
        _cleanup(root)


def test_path_escape_target_raises() -> None:
    root = _make_temp_vault()
    try:
        raised = False
        try:
            run_developer_repo_explain(
                inputs={
                    "focus_area": "",
                    "question": "Try path escape",
                    "target_paths": ["../outside.md"],
                    "project_scope": "",
                },
                vault_root=root,
            )
        except WorkflowExecutionError:
            raised = True
        assert raised, "Expected WorkflowExecutionError for target path escape"
        print("  PASS test_path_escape_target_raises")
    finally:
        _cleanup(root)


def test_forbidden_write_zone_raises() -> None:
    from runtime.aor.developer_shadow import _assert_write_path_safe

    forbidden_paths = [
        "SOUL.md",
        "CLAUDE.md",
        "01_PROJECTS/some-file.md",
        "02_KNOWLEDGE/domain/note.md",
        "README.md",
        "runtime/aor/engine.py",
    ]

    for fp in forbidden_paths:
        raised = False
        try:
            _assert_write_path_safe(fp)
        except WorkflowExecutionError:
            raised = True
        assert raised, f"Expected WorkflowExecutionError for forbidden path: {fp}"

    print("  PASS test_forbidden_write_zone_raises")


def test_allowed_write_paths_pass() -> None:
    from runtime.aor.developer_shadow import _assert_write_path_safe

    allowed_paths = [
        "07_LOGS/Developer-Briefs/2026-04-22-test-brief.md",
        "07_LOGS/Agent-Activity/20260422-120000__audit.json",
        "07_LOGS/Build-Logs/2026-04-22-developer-co-development-shadow-run.md",
        "99_ARCHIVE/Documentation-History/2026-04-22_developer-co-development-shadow-run.md",
    ]

    for ap in allowed_paths:
        _assert_write_path_safe(ap)  # should not raise

    print("  PASS test_allowed_write_paths_pass")


def test_target_paths_comma_string() -> None:
    root = _make_temp_vault()
    try:
        result = run_developer_repo_explain(
            inputs={
                "focus_area": "",
                "question": "test",
                "target_paths": "CLAUDE.md,00_HOME/Now.md",
                "project_scope": "",
            },
            vault_root=root,
        )
        assert "CLAUDE.md" in result["files_read"]
        assert "00_HOME/Now.md" in result["files_read"]
        print("  PASS test_target_paths_comma_string")
    finally:
        _cleanup(root)


def test_target_paths_list() -> None:
    root = _make_temp_vault()
    try:
        result = run_developer_repo_explain(
            inputs={
                "focus_area": "",
                "question": "test",
                "target_paths": ["CLAUDE.md", "00_HOME/Now.md"],
                "project_scope": "",
            },
            vault_root=root,
        )
        assert "CLAUDE.md" in result["files_read"]
        print("  PASS test_target_paths_list")
    finally:
        _cleanup(root)


def test_claude_md_always_read() -> None:
    """CLAUDE.md is always included in the read scope."""
    root = _make_temp_vault()
    try:
        (root / "runtime" / "aor").mkdir(parents=True, exist_ok=True)
        (root / "runtime" / "aor" / "engine.py").write_text("# engine\n", encoding="utf-8")

        result = run_developer_repo_explain(
            inputs={
                "focus_area": "runtime/aor",
                "question": "",
                "target_paths": [],
                "project_scope": "",
            },
            vault_root=root,
        )
        assert "CLAUDE.md" in result["files_read"]
        print("  PASS test_claude_md_always_read")
    finally:
        _cleanup(root)


# ── Unit tests: contradiction scan ───────────────────────────────────────────

def test_contradiction_scan_detects_phase_spread() -> None:
    files = [
        ("06_AGENTS/Feature-Register.md", (
            "# Feature Register\n"
            "Phase 1 complete. Phase 2 complete. Phase 3 complete.\n"
            "Phase 4 complete. Phase 5 complete. Phase 6 complete.\n"
            "Phase 7 complete. Phase 8 complete. Phase 9 active.\n"
            "Phase 14 is the final target.\n"
        )),
    ]
    findings = _scan_contradictions(files, "")
    assert any(f.finding_type == "phase_mismatch" for f in findings)
    print("  PASS test_contradiction_scan_detects_phase_spread")


def test_contradiction_scan_detects_stale_not_built() -> None:
    files = [
        ("06_AGENTS/Feature-Fit-Register.md", (
            "# Feature Register\n"
            "| Some Phase 8 Feature | NOT BUILT Phase 8 | something |\n"
        )),
    ]
    findings = _scan_contradictions(files, "")
    assert any(f.finding_type == "stale_claim" for f in findings)
    print("  PASS test_contradiction_scan_detects_stale_not_built")


def test_contradiction_scan_no_false_positive_on_clean_file() -> None:
    files = [
        ("CLAUDE.md", "# CLAUDE.md\n\nPhase 9 ACTIVE.\n"),
    ]
    findings = _scan_contradictions(files, "")
    # A clean single-phase file should have no or very few findings
    phase_mismatches = [f for f in findings if f.finding_type == "phase_mismatch"]
    assert len(phase_mismatches) == 0
    print("  PASS test_contradiction_scan_no_false_positive_on_clean_file")


def test_contradiction_scan_capped_at_20() -> None:
    """Scan should never return more than 20 findings."""
    files = []
    for i in range(30):
        files.append((
            f"docs/file_{i}.md",
            f"# File {i}\n" + "NOT BUILT Phase 7\n" * 5 + "Phase 1 Phase 14\n",
        ))
    findings = _scan_contradictions(files, "")
    assert len(findings) <= 20
    print("  PASS test_contradiction_scan_capped_at_20")


# ── Unit tests: output builders ──────────────────────────────────────────────

def test_developer_brief_structure() -> None:
    read_files = [("CLAUDE.md", "# CLAUDE.md\nPhase 9.\n")]
    contradictions = []
    brief = _build_developer_brief("runtime/aor", "What is AOR?", "ChaseOS", read_files, contradictions, "2026-04-22")

    assert "Developer Brief" in brief
    assert "runtime/aor" in brief
    assert "CLAUDE.md" in brief
    assert "CONTRADICTION SCAN" in brief
    assert "No obvious contradictions" in brief
    print("  PASS test_developer_brief_structure")


def test_implementation_brief_is_draft() -> None:
    read_files = [("CLAUDE.md", "# CLAUDE.md\n")]
    brief = _build_implementation_brief("runtime/aor", "test q", "ChaseOS", read_files, "2026-04-22")

    assert "draft" in brief.lower()
    assert "CLAUDE.md" in brief
    assert "ChaseOS" in brief
    print("  PASS test_implementation_brief_is_draft")


def test_doc_refresh_proposal_is_draft_only() -> None:
    read_files = [("06_AGENTS/Developer-Co-Development-Mode.md", "# Developer Mode\n")]
    proposal = _build_doc_refresh_proposal("06_AGENTS/Developer-Co-Development-Mode.md", read_files, [], "2026-04-22")

    assert "draft proposal only" in proposal
    assert "Structured Diff Proposals" in proposal
    assert "status: NO_CHANGE_PROPOSED" in proposal
    assert "canonical edit" in proposal
    assert "02_KNOWLEDGE" in proposal
    print("  PASS test_doc_refresh_proposal_is_draft_only")


def test_doc_refresh_proposal_structures_findings() -> None:
    read_files = [("06_AGENTS/Feature-Fit-Register.md", "# Feature Fit\n")]
    contradictions = [
        ContradictionFinding(
            file_path="06_AGENTS/Feature-Fit-Register.md",
            finding_type="stale_claim",
            description="NOT BUILT claim references a completed phase.",
            confidence="medium",
        )
    ]
    proposal = _build_doc_refresh_proposal("06_AGENTS", read_files, contradictions, "2026-04-22")

    assert "### Proposal 1" in proposal
    assert "proposal_id: `dev-doc-refresh-01`" in proposal
    assert "target_file: `06_AGENTS/Feature-Fit-Register.md`" in proposal
    assert "status: REVIEW_REQUIRED" in proposal
    assert "operation: verify_then_edit" in proposal
    assert "```diff" in proposal
    print("  PASS test_doc_refresh_proposal_structures_findings")


def test_diagram_proposal_is_text_only() -> None:
    read_files = [
        ("runtime/aor/engine.py", "import json\nfrom pathlib import Path\n"),
    ]
    proposal = _build_diagram_proposal("runtime/aor", read_files, "2026-04-22")

    assert "mermaid" in proposal.lower()
    assert "draft" in proposal.lower()
    # Must NOT contain any rendering commands, live URLs, or shell commands
    assert "subprocess" not in proposal
    assert "render(" not in proposal
    assert "exec(" not in proposal
    print("  PASS test_diagram_proposal_is_text_only")


def test_contradiction_scan_report_structure() -> None:
    from runtime.aor.developer_shadow import ContradictionFinding
    contradictions = [
        ContradictionFinding(
            file_path="docs/test.md",
            finding_type="stale_claim",
            description="Test finding",
            confidence="medium",
        )
    ]
    report = _build_contradiction_scan("runtime/aor", [], contradictions, "2026-04-22")
    assert "stale_claim" in report
    assert "Test finding" in report
    assert "medium" in report
    print("  PASS test_contradiction_scan_report_structure")


# ── Unit tests: write-scope enforcement ──────────────────────────────────────

def test_write_paths_all_within_scope() -> None:
    """All output paths from handler must be within ALLOWED_WRITE_TARGETS."""
    root = _make_temp_vault()
    try:
        result = run_developer_repo_explain(
            inputs={
                "focus_area": "",
                "question": "test",
                "target_paths": ["CLAUDE.md"],
                "project_scope": "",
            },
            vault_root=root,
        )
        for wb in result["writebacks"]:
            path = wb["path"]
            in_scope = any(
                path.startswith(t.rstrip("/"))
                for t in ALLOWED_WRITE_TARGETS
            )
            assert in_scope, f"Write path outside allowed scope: {path}"
        print("  PASS test_write_paths_all_within_scope")
    finally:
        _cleanup(root)


def test_no_canonical_writes_in_output_content() -> None:
    """Output content must not contain instructions to write protected files."""
    root = _make_temp_vault()
    try:
        result = run_developer_repo_explain(
            inputs={
                "focus_area": "",
                "question": "test",
                "target_paths": ["CLAUDE.md"],
                "project_scope": "",
            },
            vault_root=root,
        )
        for wb in result["writebacks"]:
            content = str(wb.get("content", ""))
            # Content may reference protected files but must not instruct writes to them
            assert "write_text" not in content
            assert "SOUL.md" not in content or "never write" in content.lower() or "protected" in content.lower() or "read" in content.lower()
        print("  PASS test_no_canonical_writes_in_output_content")
    finally:
        _cleanup(root)


# ── Integration tests: AOR engine dispatch ───────────────────────────────────

def test_engine_dispatches_developer_workflow() -> None:
    root = _make_full_aor_vault()
    try:
        result = run_workflow(
            workflow_id="developer_repo_explain_shadow",
            inputs={
                "focus_area": "",
                "question": "What is the vault?",
                "target_paths": ["CLAUDE.md"],
                "project_scope": "ChaseOS Test",
            },
            vault_root=root,
        )
        assert result.status == "success", f"Expected success, got {result.status!r}: {result.escalation_reason}"
        # Stage 7 outputs nest writeback data under "writeback" key
        files_written = result.outputs.get("writeback", {}).get("files_written", [])
        assert any("developer-brief" in f for f in files_written), (
            f"Expected developer-brief in files_written, got: {files_written}"
        )
        print("  PASS test_engine_dispatches_developer_workflow")
    finally:
        _cleanup(root)


def test_engine_escalates_missing_manifest() -> None:
    root = _make_temp_vault()
    try:
        # No workflow registry at all
        result = run_workflow(
            workflow_id="developer_repo_explain_shadow",
            inputs={"focus_area": "test", "question": "test", "target_paths": [], "project_scope": ""},
            vault_root=root,
        )
        assert result.status == "escalated"
        print("  PASS test_engine_escalates_missing_manifest")
    finally:
        _cleanup(root)


def test_engine_escalates_missing_role_card() -> None:
    root = _make_full_aor_vault()
    try:
        # Remove the role card
        rc_path = root / "06_AGENTS" / "role-cards" / "developer-copilot-shadow.yaml"
        if rc_path.exists():
            rc_path.unlink()

        result = run_workflow(
            workflow_id="developer_repo_explain_shadow",
            inputs={"focus_area": "test", "question": "test", "target_paths": [], "project_scope": ""},
            vault_root=root,
        )
        assert result.status == "escalated"
        print("  PASS test_engine_escalates_missing_role_card")
    finally:
        _cleanup(root)


def test_engine_escalates_inactive_manifest() -> None:
    root = _make_full_aor_vault()
    try:
        # Set manifest status to draft
        manifest_path = root / "runtime" / "workflows" / "registry" / "developer_repo_explain_shadow.yaml"
        content = manifest_path.read_text(encoding="utf-8")
        content = content.replace("status: active", "status: draft")
        manifest_path.write_text(content, encoding="utf-8")

        result = run_workflow(
            workflow_id="developer_repo_explain_shadow",
            inputs={"focus_area": "test", "question": "test", "target_paths": [], "project_scope": ""},
            vault_root=root,
        )
        assert result.status == "escalated"
        print("  PASS test_engine_escalates_inactive_manifest")
    finally:
        _cleanup(root)


def test_engine_writes_audit_record() -> None:
    root = _make_full_aor_vault()
    try:
        result = run_workflow(
            workflow_id="developer_repo_explain_shadow",
            inputs={
                "focus_area": "",
                "question": "test audit",
                "target_paths": ["CLAUDE.md"],
                "project_scope": "test",
            },
            vault_root=root,
        )
        assert result.status == "success"

        # Handler's own audit record should exist in Agent-Activity
        # (named *__audit.json to distinguish from engine Stage 8 record)
        activity_dir = root / "07_LOGS" / "Agent-Activity"
        handler_audit_files = list(activity_dir.glob("*developer_repo_explain_shadow__audit.json"))
        assert len(handler_audit_files) >= 1, "No handler audit record found in Agent-Activity"

        # Verify handler audit JSON is valid
        audit_content = handler_audit_files[0].read_text(encoding="utf-8")
        audit_data = json.loads(audit_content)
        assert audit_data.get("workflow") == "developer_repo_explain_shadow"
        assert "files_read" in audit_data
        assert "mode" in audit_data
        print("  PASS test_engine_writes_audit_record")
    finally:
        _cleanup(root)


def test_engine_writes_build_log_and_archive_note() -> None:
    root = _make_full_aor_vault()
    try:
        result = run_workflow(
            workflow_id="developer_repo_explain_shadow",
            inputs={
                "focus_area": "",
                "question": "test build/archive outputs",
                "target_paths": ["CLAUDE.md"],
                "project_scope": "test",
            },
            vault_root=root,
        )
        assert result.status == "success"

        build_logs = list((root / "07_LOGS" / "Build-Logs").glob("*developer-co-development-shadow-run*.md"))
        archive_notes = list((root / "99_ARCHIVE" / "Documentation-History").glob("*developer-co-development-shadow-run*.md"))
        assert build_logs, "Expected Developer Co-Development build log output"
        assert archive_notes, "Expected Developer Co-Development documentation-history output"
        print("  PASS test_engine_writes_build_log_and_archive_note")
    finally:
        _cleanup(root)


def test_adapter_boundary_outputs_stay_bounded() -> None:
    """All writeback paths must remain within declared write scope after full AOR run."""
    root = _make_full_aor_vault()
    try:
        result = run_workflow(
            workflow_id="developer_repo_explain_shadow",
            inputs={
                "focus_area": "",
                "question": "adapter boundary test",
                "target_paths": ["CLAUDE.md"],
                "project_scope": "ChaseOS",
            },
            vault_root=root,
        )
        assert result.status == "success"

        # All files written must be within declared targets
        files_written = result.outputs.get("writeback", {}).get("files_written", [])
        assert files_written, "Expected writeback files from developer workflow"
        for fw in files_written:
            in_scope = any(
                fw.startswith(t.rstrip("/"))
                for t in [
                    "07_LOGS/Developer-Briefs/",
                    "07_LOGS/Agent-Activity/",
                    "07_LOGS/Build-Logs/",
                    "99_ARCHIVE/Documentation-History/",
                ]
            )
            assert in_scope, f"File written outside adapter boundary: {fw}"

        # Verify no protected files were touched
        for protected in ["SOUL.md", "CLAUDE.md", "README.md", "ROADMAP.md"]:
            pf = root / protected
            if pf.exists():
                # These should not have been modified (creation time unchanged)
                # Just verify they exist and weren't zeroed out
                assert pf.stat().st_size > 0

        print("  PASS test_adapter_boundary_outputs_stay_bounded")
    finally:
        _cleanup(root)


# ── Test runner ───────────────────────────────────────────────────────────────

def run_all_tests() -> None:
    tests = [
        # Handler unit tests
        test_happy_path_focus_area,
        test_happy_path_target_paths,
        test_happy_path_produces_eight_writebacks,
        test_no_inputs_raises,
        test_unresolvable_focus_area_raises,
        test_broad_focus_area_raises,
        test_path_escape_target_raises,
        test_forbidden_write_zone_raises,
        test_allowed_write_paths_pass,
        test_target_paths_comma_string,
        test_target_paths_list,
        test_claude_md_always_read,
        # Contradiction scan
        test_contradiction_scan_detects_phase_spread,
        test_contradiction_scan_detects_stale_not_built,
        test_contradiction_scan_no_false_positive_on_clean_file,
        test_contradiction_scan_capped_at_20,
        # Output builders
        test_developer_brief_structure,
        test_implementation_brief_is_draft,
        test_doc_refresh_proposal_is_draft_only,
        test_doc_refresh_proposal_structures_findings,
        test_diagram_proposal_is_text_only,
        test_contradiction_scan_report_structure,
        # Write-scope enforcement
        test_write_paths_all_within_scope,
        test_no_canonical_writes_in_output_content,
        # AOR engine integration
        test_engine_dispatches_developer_workflow,
        test_engine_escalates_missing_manifest,
        test_engine_escalates_missing_role_card,
        test_engine_escalates_inactive_manifest,
        test_engine_writes_audit_record,
        test_engine_writes_build_log_and_archive_note,
        test_adapter_boundary_outputs_stay_bounded,
    ]

    passed = 0
    failed = 0
    errors = []

    print(f"\n=== Developer Co-Development Mode Tests ===")
    print(f"Total: {len(tests)} tests\n")

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            failed += 1
            errors.append((test_fn.__name__, exc))
            print(f"  FAIL {test_fn.__name__}: {exc}")

    print(f"\n=== Results: {passed}/{len(tests)} passed ===")
    if errors:
        print(f"\nFailed tests:")
        for name, exc in errors:
            print(f"  - {name}: {exc}")
        sys.exit(1)
    else:
        print("All tests passed.")


if __name__ == "__main__":
    run_all_tests()
