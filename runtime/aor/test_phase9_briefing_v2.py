"""
test_phase9_briefing_v2.py -- ChaseOS Phase 9 Briefing V2 Tests

Tests for the four-layer briefing model:
  - operator_today v2: four-layer output, carry-forward, contradiction detection, files-read
  - operator_close_day v2: carry-forward output, runtime record, delta, no canonical writes

Running:
  PYTHONIOENCODING=utf-8 python runtime/aor/test_phase9_briefing_v2.py
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.engine import run_workflow


_TESTS: list[tuple[str, object]] = []
_PASS = 0
_FAIL = 0
_ERRORS: list[str] = []


def _test(name: str):
    def decorator(fn):
        _TESTS.append((name, fn))
        return fn
    return decorator


def _run_all() -> None:
    global _PASS, _FAIL
    for name, fn in _TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
            _PASS += 1
        except AssertionError as exc:
            print(f"  FAIL  {name}: {exc}")
            _FAIL += 1
            _ERRORS.append(f"{name}: {exc}")
        except Exception as exc:
            import traceback
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            _FAIL += 1
            _ERRORS.append(f"{name}: {type(exc).__name__}: {exc}")


def _make_temp_vault() -> Path:
    tmp_root = _VAULT_ROOT / ".codex_tmp_test"
    tmp_root.mkdir(parents=True, exist_ok=True)
    root = tmp_root / f"briefing-v2-{uuid.uuid4().hex}"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    return root


def _cleanup(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)


def _scaffold_minimal_vault(root: Path, today: str = "2026-04-16") -> None:
    """Scaffold the minimal vault structure needed by both briefing handlers."""
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)
    (root / "00_HOME").mkdir(parents=True)
    (root / "03_INPUTS" / "Sources").mkdir(parents=True)
    (root / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
    (root / "07_LOGS" / "Operator-Briefs").mkdir(parents=True)
    (root / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (root / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (root / "01_PROJECTS" / "TradingSystems").mkdir(parents=True)
    (root / "01_PROJECTS" / "StrikeZone").mkdir(parents=True)
    (root / "01_PROJECTS" / "University").mkdir(parents=True)

    # Manifests + role card
    _write_manifest(root, "operator_today")
    _write_manifest(root, "operator_close_day")
    _write_role_card(root)

    # Now.md
    (root / "00_HOME" / "Now.md").write_text(
        "\n".join([
            "## Current Phase",
            "Phase 9 — Operator Runtime (AOR + SBP) — ACTIVE.",
            "",
            "## Active Now",
            "| Domain | Current focus |",
            "|--------|---------------|",
            "| ChaseOS / System Infrastructure | Phase 9 Briefing V2 |",
            "| Trading Systems / Market Ops | Daily execution |",
            "| StrikeZone Crypto | Signal ops |",
            "| University | Coursework |",
            "",
            f"- ⬜ Pass V2 (NEXT): Implement operator_today v2 four-layer model",
        ]),
        encoding="utf-8",
    )

    # ROADMAP.md (with matching phase)
    (root / "ROADMAP.md").write_text(
        "\n".join([
            "# ChaseOS Roadmap",
            "",
            "## Phase 9 — Operator Runtime — ACTIVE",
            "Current phase.",
        ]),
        encoding="utf-8",
    )

    # Project OS files
    (root / "01_PROJECTS" / "ChaseOS" / "ChaseOS-OS.md").write_text(
        "## Open Loops\n- [ ] Complete briefing v2 pass\n",
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "TradingSystems" / "TradingSystems-OS.md").write_text(
        "## 12. Immediate Next Actions\n- [ ] Formalize morning thesis workflow\n",
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "StrikeZone" / "StrikeZone-Crypto-OS.md").write_text(
        "## 🔗 Open Loops\n- [ ] Build testimonial capture system\n",
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "University" / "Degree-OS.md").write_text(
        "## 🔗 Open Loops\n- [ ] Add deadlines and submission dates\n",
        encoding="utf-8",
    )

    # Build logs and decision
    (root / "07_LOGS" / "Build-Logs" / f"{today}-example.md").write_text("build log", encoding="utf-8")
    (root / "07_LOGS" / "Decision-Ledger" / f"{today}-example.md").write_text("decision", encoding="utf-8")


def _write_manifest(root: Path, workflow_id: str) -> None:
    manifest = {
        "id": workflow_id,
        "name": workflow_id,
        "version": "2.0",
        "description": f"{workflow_id} briefing handler.",
        "task_type": "operator-briefing",
        "role_card": "operator-briefing",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "permission_ceiling": "no_protected_file_writes",
        "writeback_targets": ["07_LOGS/Operator-Briefs/"],
        "failure_behavior": "escalate",
    }
    (root / "runtime" / "workflows" / "registry" / f"{workflow_id}.yaml").write_text(
        yaml.dump(manifest), encoding="utf-8"
    )


def _write_role_card(root: Path) -> None:
    card = {
        "id": "operator-briefing",
        "name": "Operator Briefing",
        "version": "2.0",
        "description": "Read-heavy briefing role.",
        "owner": "operator",
        "allowed_actions": ["read_vault", "write_logs"],
        "forbidden_actions": ["write_protected_files"],
        "write_scope": ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"],
        "forbidden_write_zones": ["00_HOME/Now.md", "01_PROJECTS/", "runtime/", "ROADMAP.md"],
        "escalation_rules": ["missing required read"],
        "runtime_expectations": ["vault root accessible"],
        "required_reads": [
            "00_HOME/Now.md",
            "03_INPUTS/",
            "07_LOGS/Build-Logs/",
            "07_LOGS/Decision-Ledger/",
        ],
    }
    (root / "06_AGENTS" / "role-cards" / "operator-briefing.yaml").write_text(
        yaml.dump(card), encoding="utf-8"
    )


def _write_v1_close_note(root: Path, close_date: str, loops: list[str]) -> None:
    """Write a v1-format close note (old Operator-Provided Open Loops section)."""
    content_lines = [
        "---",
        "type: operator-close-note",
        "workflow: operator_close_day",
        f"date: {close_date}",
        "source: aor",
        "---",
        "",
        f"# Operator Close Day — {close_date}",
        "",
        "## Operator-Provided Open Loops",
    ]
    if loops:
        for loop in loops:
            content_lines.append(f"- {loop}")
    else:
        content_lines.append("- None provided.")
    (root / "07_LOGS" / "Operator-Briefs" / f"{close_date}-operator-close-day.md").write_text(
        "\n".join(content_lines), encoding="utf-8"
    )


def _write_v2_close_note(root: Path, close_date: str, loops: list[dict]) -> None:
    """Write a v2-format close note with [CARRY-FORWARD] section."""
    content_lines = [
        "---",
        "type: operator-close-note",
        "workflow: operator_close_day",
        "version: v2",
        f"date: {close_date}",
        "source: aor",
        "---",
        "",
        f"# Operator Brief — CLOSE — {close_date}",
        "",
        "## [CARRY-FORWARD] Open Loops for Tomorrow",
        "",
        "> This section is read by operator_today v2 as Layer 2 carry-forward.",
        "",
    ]
    for lp in loops:
        content_lines.append(f"- status:{lp['status']} — {lp['text']}")
    (root / "07_LOGS" / "Operator-Briefs" / f"{close_date}-operator-close-day.md").write_text(
        "\n".join(content_lines), encoding="utf-8"
    )


def _write_activity_record(root: Path, workflow_id: str, status: str, run_date: str) -> None:
    """Write a fake AOR activity JSON for today."""
    ts_str = run_date.replace("-", "") + "-120000"
    audit_id = uuid.uuid4().hex[:8]
    path = root / "07_LOGS" / "Agent-Activity" / f"{ts_str}__{workflow_id}__{audit_id}.json"
    record = {
        "audit_id": audit_id,
        "workflow_id": workflow_id,
        "timestamp_utc": f"{run_date}T12:00:00+00:00",
        "status": status,
        "stage_reached": "audit_record",
        "escalation_reason": None,
        "error": None,
    }
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


# ═══ operator_today v2 tests ═══════════════════════════════════════════════════

@_test("v2: operator_today output has four-layer section headers")
def test_operator_today_four_layer_headers():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success", f"expected success, got {result.status}: {result.escalation_reason}"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "## [CANONICAL] Current State" in content, "missing [CANONICAL] section"
        assert "## [CARRY-FORWARD:" in content, "missing [CARRY-FORWARD] section"
        assert "## [SOURCED] Operational Context" in content, "missing [SOURCED] section"
        assert "## [SYNTHESIS] Today's Recommendations" in content, "missing [SYNTHESIS] section"
    finally:
        _cleanup(root)


@_test("v2: operator_today brief header includes Generated by, Carry-forward, Files read")
def test_operator_today_header_fields():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "**Generated by:** AOR / operator_today v2" in content
        assert "**Carry-forward from:**" in content
        assert "**Files read:**" in content
    finally:
        _cleanup(root)


@_test("v2: operator_today with no prior close note shows carry-forward none")
def test_operator_today_no_prior_close_note():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    # No close note in Operator-Briefs
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "CARRY-FORWARD: none" in content or "No Prior Close Note" in content, \
            "should indicate no carry-forward when no close note exists"
        assert result.outputs["run"]["carry_forward_date"] == "none"
    finally:
        _cleanup(root)


@_test("v2: operator_today reads carry-forward from v1 close note")
def test_operator_today_reads_v1_carry_forward():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    _write_v1_close_note(root, "2026-04-15", ["Finish graph_hygiene handler", "Write SOP for ingest"])
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "Finish graph_hygiene handler" in content, "v1 carry-forward loop not found"
        assert result.outputs["run"]["carry_forward_date"] == "2026-04-15"
        assert result.outputs["run"]["summary"]["carry_forward_items"] > 0
    finally:
        _cleanup(root)


@_test("v2: operator_today reads carry-forward from v2 close note")
def test_operator_today_reads_v2_carry_forward():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    _write_v2_close_note(root, "2026-04-15", [
        {"status": "open", "text": "Complete MCP architecture doc"},
        {"status": "deferred", "text": "Review StrikeZone signal backlog"},
        {"status": "resolved", "text": "Fix CLI flag regression"},  # resolved — should NOT appear
    ])
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "Complete MCP architecture doc" in content, "open loop from v2 close not found"
        assert "StrikeZone signal backlog" in content, "deferred loop from v2 close not found"
        # Resolved should be excluded from carry-forward
        assert "[resolved] Fix CLI flag regression" not in content, \
            "resolved items should not appear in carry-forward"
    finally:
        _cleanup(root)


@_test("v2: operator_today flags contradiction when phase numbers differ")
def test_operator_today_contradiction_flagging():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    # Override ROADMAP.md to claim Phase 8 is active
    (root / "ROADMAP.md").write_text(
        "# ChaseOS Roadmap\n\n## Phase 8 — Connector/Capture — ACTIVE\nOld phase.\n",
        encoding="utf-8",
    )
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "CONTRADICTION" in content.upper() or "mismatch" in content.lower(), \
            "contradiction should be flagged when Now.md and ROADMAP.md disagree on phase"
        assert result.outputs["run"]["contradictions_flagged"] > 0
    finally:
        _cleanup(root)


@_test("v2: operator_today no contradiction when phases match")
def test_operator_today_no_false_contradiction():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    # ROADMAP matches Now.md (both Phase 9)
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        assert result.outputs["run"]["contradictions_flagged"] == 0, \
            "should not flag contradiction when phases match"
    finally:
        _cleanup(root)


@_test("v2: operator_today writes only to Operator-Briefs — no canonical mutations")
def test_operator_today_no_canonical_writes():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    # Record mtime of protected files before run
    now_mtime = (root / "00_HOME" / "Now.md").stat().st_mtime
    roadmap_mtime = (root / "ROADMAP.md").stat().st_mtime
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        # Now.md and ROADMAP.md must not be touched
        assert (root / "00_HOME" / "Now.md").stat().st_mtime == now_mtime, \
            "operator_today must not modify Now.md"
        assert (root / "ROADMAP.md").stat().st_mtime == roadmap_mtime, \
            "operator_today must not modify ROADMAP.md"
        # No writes to Project-OS files
        for domain_dir in (root / "01_PROJECTS").iterdir():
            for f in domain_dir.iterdir():
                assert f.is_file(), "unexpected dir in project folder"
                # Only original files should exist
        # Output must be in Operator-Briefs only
        brief_path = root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md"
        assert brief_path.exists(), "brief not written"
    finally:
        _cleanup(root)


@_test("v2: operator_today synthesis section labeled as AI analysis")
def test_operator_today_synthesis_labeled():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "AI-synthesized analysis" in content or "AI-generated" in content, \
            "synthesis section must be labeled as AI analysis"
        assert "starting point for your judgment" in content or "not canonical state" in content
    finally:
        _cleanup(root)


@_test("v2: operator_today files_read list is non-empty and explicit")
def test_operator_today_files_read_logged():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        files_read = result.outputs["run"]["files_read"]
        assert isinstance(files_read, list)
        assert len(files_read) > 0, "files_read must not be empty"
        assert "00_HOME/Now.md" in files_read, "Now.md must be in files_read"
        # Verify files_read appears in the output document
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "**Files read:**" in content, "Files read section missing from brief"
        assert "00_HOME/Now.md" in content
    finally:
        _cleanup(root)


@_test("v2: operator_today AOR activity summary appears in SOURCED section")
def test_operator_today_aor_activity_in_sourced():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    # Write a recent activity record
    _write_activity_record(root, "operator_today", "success", "2026-04-16")
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").read_text(encoding="utf-8")
        assert "AOR Activity" in content, "AOR Activity section missing"
    finally:
        _cleanup(root)


# ═══ operator_close_day v2 tests ═══════════════════════════════════════════════

@_test("v2: operator_close_day output has four-layer section headers")
def test_close_day_four_layer_headers():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_close_day", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success", f"expected success: {result.escalation_reason}"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-close-day.md").read_text(encoding="utf-8")
        assert "## [CANONICAL] Phase State at Close" in content, "missing [CANONICAL] section"
        assert "## [CARRY-FORWARD] Open Loops for Tomorrow" in content, "missing [CARRY-FORWARD] section"
        assert "## [RUNTIME RECORD] Today's AOR Activity" in content, "missing [RUNTIME RECORD] section"
        assert "## [SYNTHESIS] Session Summary" in content, "missing [SYNTHESIS] section"
    finally:
        _cleanup(root)


@_test("v2: operator_close_day carry-forward section is parseable by operator_today v2")
def test_close_day_carry_forward_parseable():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow(
            "operator_close_day",
            inputs={"date": "2026-04-16", "open_loops": "Finish graph_hygiene; Review StrikeZone"},
            vault_root=root,
        )
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-close-day.md").read_text(encoding="utf-8")
        # Must have status:X format lines in carry-forward section
        assert "status:open" in content or "status:new" in content or "status:none" in content, \
            "carry-forward section must use status:X format"
        # Must have the operator-provided loops
        assert "Finish graph_hygiene" in content
        assert "Review StrikeZone" in content
    finally:
        _cleanup(root)


@_test("v2: operator_close_day runtime record section present")
def test_close_day_runtime_record_present():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    _write_activity_record(root, "operator_today", "success", "2026-04-16")
    try:
        result = run_workflow("operator_close_day", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-close-day.md").read_text(encoding="utf-8")
        assert "## [RUNTIME RECORD] Today's AOR Activity" in content
        assert "operator_today" in content, "today's activity should appear in runtime record"
    finally:
        _cleanup(root)


@_test("v2: operator_close_day runtime record shows no-activity when empty")
def test_close_day_runtime_record_empty():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    # No activity records written
    try:
        result = run_workflow("operator_close_day", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-close-day.md").read_text(encoding="utf-8")
        assert "## [RUNTIME RECORD] Today's AOR Activity" in content
        assert "No AOR activity records found" in content
    finally:
        _cleanup(root)


@_test("v2: operator_close_day delta from morning brief when morning brief exists")
def test_close_day_delta_from_morning():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    # Write a v2 morning brief with carry-forward
    _write_v2_close_note(root, "2026-04-15", [
        {"status": "open", "text": "Complete briefing v2 pass"},
    ])
    try:
        result = run_workflow(
            "operator_close_day",
            inputs={"date": "2026-04-16", "open_loops": "Complete briefing v2 pass"},
            vault_root=root,
        )
        assert result.status == "success"
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-close-day.md").read_text(encoding="utf-8")
        assert "Delta from Morning" in content or "delta" in content.lower()
    finally:
        _cleanup(root)


@_test("v2: operator_close_day files_read explicitly logged")
def test_close_day_files_read_logged():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_close_day", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        files_read = result.outputs["run"]["files_read"]
        assert isinstance(files_read, list)
        assert len(files_read) > 0
        assert "00_HOME/Now.md" in files_read
        content = (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-close-day.md").read_text(encoding="utf-8")
        assert "**Files read:**" in content
    finally:
        _cleanup(root)


@_test("v2: operator_close_day does not write canonical files")
def test_close_day_no_canonical_writes():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    now_mtime = (root / "00_HOME" / "Now.md").stat().st_mtime
    try:
        result = run_workflow(
            "operator_close_day",
            inputs={"date": "2026-04-16", "open_loops": "some loop"},
            vault_root=root,
        )
        assert result.status == "success"
        assert (root / "00_HOME" / "Now.md").stat().st_mtime == now_mtime, \
            "operator_close_day must not modify Now.md"
        for domain_dir in (root / "01_PROJECTS").iterdir():
            for f in domain_dir.iterdir():
                original_content = f.read_text(encoding="utf-8")
                # Content must not have been written by the handler
                assert "operator_close_day" not in original_content, \
                    f"Project-OS file {f} should not be modified by close handler"
    finally:
        _cleanup(root)


@_test("v2: operator_close_day produces machine-readable carry-forward")
def test_close_day_produces_machine_readable_carry_forward():
    """The carry-forward count in handler output must reflect loops recorded."""
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow(
            "operator_close_day",
            inputs={"date": "2026-04-16", "open_loops": "Loop A; Loop B; Loop C"},
            vault_root=root,
        )
        assert result.status == "success"
        carry_count = result.outputs["run"]["carry_forward_loop_count"]
        assert carry_count >= 3, f"expected at least 3 carry-forward loops, got {carry_count}"
        summary = result.outputs["run"]["summary"]
        assert summary["carry_forward_loops_count"] >= 3
    finally:
        _cleanup(root)


@_test("v2: full day cycle — close note becomes carry-forward in next morning's brief")
def test_full_day_cycle():
    """End-to-end: run close_day with loops, then run operator_today next morning to verify carry-forward."""
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")

    # Close today with open loops
    close_result = run_workflow(
        "operator_close_day",
        inputs={"date": "2026-04-16", "open_loops": "Complete MCP doc; Fix test flakiness"},
        vault_root=root,
    )
    assert close_result.status == "success"

    # scaffold tomorrow's build log
    (root / "07_LOGS" / "Build-Logs" / "2026-04-17-example.md").write_text("build", encoding="utf-8")

    # Run operator_today next morning
    open_result = run_workflow("operator_today", inputs={"date": "2026-04-17"}, vault_root=root)
    assert open_result.status == "success"

    # Tomorrow's brief should include today's loops as carry-forward
    brief_path = root / "07_LOGS" / "Operator-Briefs" / "2026-04-17-operator-today.md"
    assert brief_path.exists()
    content = brief_path.read_text(encoding="utf-8")
    assert "Complete MCP doc" in content or "Fix test flakiness" in content, \
        "operator_today v2 should carry-forward loops from yesterday's close note"
    assert open_result.outputs["run"]["carry_forward_date"] == "2026-04-16"

    _cleanup(root)


# ═══ Regression tests (ensure v1 tests still pass in spirit) ═══════════════════

@_test("regression: operator_today still outputs correct date and writes bounded file")
def test_regression_operator_today_basic():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_today", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        assert result.outputs["run"]["handler_status"] == "executed"
        assert (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-today.md").exists()
        assert result.outputs["run"]["date"] == "2026-04-16"
    finally:
        _cleanup(root)


@_test("regression: operator_close_day still writes bounded close note with audit trail")
def test_regression_close_day_basic():
    root = _make_temp_vault()
    _scaffold_minimal_vault(root, today="2026-04-16")
    try:
        result = run_workflow("operator_close_day", inputs={"date": "2026-04-16"}, vault_root=root)
        assert result.status == "success"
        assert (root / "07_LOGS" / "Operator-Briefs" / "2026-04-16-operator-close-day.md").exists()
        audit_files = list((root / "07_LOGS" / "Agent-Activity").glob("*.json"))
        assert len(audit_files) == 1
        record = json.loads(audit_files[0].read_text(encoding="utf-8"))
        assert record["workflow_id"] == "operator_close_day"
        assert record["status"] == "success"
    finally:
        _cleanup(root)


if __name__ == "__main__":
    print("\nPhase 9 Briefing V2 — Four-Layer Model Tests")
    print("=" * 60)
    _run_all()
    total = _PASS + _FAIL
    print("=" * 60)
    print(f"Result: {_PASS}/{total} passed")
    if _ERRORS:
        print("\nFailures:")
        for err in _ERRORS:
            print(f"  - {err}")
    sys.exit(0 if _FAIL == 0 else 1)
