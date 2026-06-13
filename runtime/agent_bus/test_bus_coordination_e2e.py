"""
test_bus_coordination_e2e.py — Agent Bus Coordination End-to-End Tests

Covers:
  - openclaw_post_review_task handler: creates task, routes via bus router, returns task_id
  - hermes_review_execute handler: claims task, reads artifact, produces review, marks done
  - Full lifecycle: created → claimed → in_progress → done
  - Event trail integrity
  - Scope enforcement: artifact outside review scope → escalation
  - No-task case: Hermes returns clean no-op when bus is empty
  - AOR engine: both workflows route through the full 8-stage pipeline
  - Priority ceiling: critical priority rejected at dispatch

These tests use temp vault dirs (no real vault, no network calls).
"""
from __future__ import annotations

import json
import sqlite3
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.agent_bus.bus import (
    init_db,
    db_path,
    list_tasks,
    upsert_heartbeat,
)
from runtime.workflows.openclaw_post_review_task import (
    run_openclaw_post_review_task,
    WorkflowExecutionError as DispatchError,
)
from runtime.workflows.hermes_review_execute import (
    run_hermes_review_execute,
    WorkflowExecutionError as ExecuteError,
    _artifact_in_scope,
    _produce_review,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    v.mkdir()
    (v / "CLAUDE.md").write_text("# test", encoding="utf-8")
    (v / "runtime" / "agent_bus").mkdir(parents=True)
    logs_dir = v / "07_LOGS" / "Agent-Activity"
    logs_dir.mkdir(parents=True)
    return v


def _write_caps(vault: Path, runtime: str, content: str) -> None:
    d = vault / "runtime" / runtime
    d.mkdir(parents=True, exist_ok=True)
    (d / "capabilities.yaml").write_text(content, encoding="utf-8")


def _setup_caps(vault: Path) -> None:
    _write_caps(vault, "openclaw", textwrap.dedent("""\
        bus_name: OpenClaw
        heartbeat_stale_seconds: 900
        max_concurrent_tasks: 3
        priority_ceiling: normal
        handles:
          - task_type: operator-briefing
            priority: primary
          - task_type: review
            priority: secondary
    """))
    _write_caps(vault, "hermes", textwrap.dedent("""\
        bus_name: Hermes
        heartbeat_stale_seconds: 900
        max_concurrent_tasks: 2
        priority_ceiling: high
        handles:
          - task_type: review
            priority: primary
          - task_type: planning
            priority: primary
    """))


def _set_fresh_heartbeat(vault: Path, runtime: str) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    upsert_heartbeat(vault, runtime=runtime, status="idle", health="ok", now_iso=now)


def _make_artifact(vault: Path, rel_path: str, content: str) -> Path:
    full = vault / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return full


def _get_events(vault: Path, task_id: str) -> list[dict]:
    conn = sqlite3.connect(db_path(vault))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM events WHERE task_id = ? ORDER BY created_at ASC", (task_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_task(vault: Path, task_id: str) -> dict | None:
    tasks = list_tasks(vault)
    return next((t for t in tasks if t["task_id"] == task_id), None)


# ── openclaw_post_review_task handler ─────────────────────────────────────────

class TestOpenClawPostReviewTask:
    def test_creates_task_on_bus(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        _set_fresh_heartbeat(vault, "Hermes")
        init_db(vault)

        result = run_openclaw_post_review_task(
            inputs={
                "artifact_path": "07_LOGS/SBP-Runs/2026-04-25-test.md",
                "request": "Review the StrikeZone digest for structural completeness.",
                "expected_output": "Structured review with endorsements and flags.",
            },
            vault_root=vault,
        )

        assert result["task_id"] is not None
        assert result["task_id"].startswith("task-")
        assert result["artifact_path"] == "07_LOGS/SBP-Runs/2026-04-25-test.md"

    def test_task_appears_as_open_on_bus(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        _set_fresh_heartbeat(vault, "Hermes")
        init_db(vault)

        result = run_openclaw_post_review_task(
            inputs={
                "artifact_path": "07_LOGS/Operator-Briefs/2026-04-25-brief.md",
                "request": "Review the operator brief.",
            },
            vault_root=vault,
        )

        tasks = list_tasks(vault, status="open")
        ids = [t["task_id"] for t in tasks]
        assert result["task_id"] in ids

    def test_task_addressed_to_hermes_when_live(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        _set_fresh_heartbeat(vault, "Hermes")
        init_db(vault)

        result = run_openclaw_post_review_task(
            inputs={"artifact_path": "07_LOGS/SBP-Runs/digest.md", "request": "Review."},
            vault_root=vault,
        )

        assert result["recipient"] == "Hermes"

    def test_falls_back_to_hermes_when_all_stale(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        # No heartbeats → all stale → route_recommended=None → default to Hermes
        init_db(vault)

        result = run_openclaw_post_review_task(
            inputs={"artifact_path": "07_LOGS/Build-Logs/test.md", "request": "Review."},
            vault_root=vault,
        )

        assert result["recipient"] == "Hermes"
        assert result["route_recommended"] is None

    def test_returns_route_reason(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        _set_fresh_heartbeat(vault, "Hermes")
        init_db(vault)

        result = run_openclaw_post_review_task(
            inputs={"artifact_path": "07_LOGS/SBP-Runs/digest.md", "request": "Review."},
            vault_root=vault,
        )

        assert isinstance(result["route_reason"], str)
        assert len(result["route_reason"]) > 0

    def test_returns_writeback_entry(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)

        result = run_openclaw_post_review_task(
            inputs={"artifact_path": "07_LOGS/SBP-Runs/digest.md", "request": "Review."},
            vault_root=vault,
        )

        assert "writebacks" in result
        assert len(result["writebacks"]) == 1
        wb = result["writebacks"][0]
        assert "07_LOGS/Agent-Activity/" in wb["path"]
        assert result["task_id"][:12] in wb["path"]

    def test_missing_artifact_path_raises(self, tmp_path):
        vault = _vault(tmp_path)
        init_db(vault)
        with pytest.raises(DispatchError, match="artifact_path"):
            run_openclaw_post_review_task(inputs={}, vault_root=vault)

    def test_critical_priority_raises(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        with pytest.raises(DispatchError, match="critical"):
            run_openclaw_post_review_task(
                inputs={
                    "artifact_path": "07_LOGS/SBP-Runs/digest.md",
                    "request": "Review.",
                    "priority": "critical",
                },
                vault_root=vault,
            )

    def test_audit_content_has_task_id(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)

        result = run_openclaw_post_review_task(
            inputs={"artifact_path": "07_LOGS/SBP-Runs/digest.md", "request": "Review."},
            vault_root=vault,
        )

        wb_content = result["writebacks"][0]["content"]
        assert result["task_id"] in wb_content
        assert "OpenClaw" in wb_content


# ── hermes_review_execute handler ─────────────────────────────────────────────

class TestHermesReviewExecute:
    def _dispatch_task(self, vault: Path, artifact_rel: str = "07_LOGS/SBP-Runs/digest.md") -> str:
        """Helper: dispatch a review task from OpenClaw to Hermes."""
        result = run_openclaw_post_review_task(
            inputs={
                "artifact_path": artifact_rel,
                "request": "Review the artifact for structural completeness.",
                "expected_output": "Endorsements and flags.",
            },
            vault_root=vault,
        )
        return result["task_id"]

    def test_claims_and_marks_done(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        _make_artifact(vault, artifact_path, "# Digest\n2026-04-25\nSome content here.\n")
        task_id = self._dispatch_task(vault, artifact_path)

        result = run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

        assert result["task_id"] == task_id
        assert result["status"] == "done"

    def test_bus_task_status_is_done(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        _make_artifact(vault, artifact_path, "# Digest\n2026-04-25\nContent.\n")
        task_id = self._dispatch_task(vault, artifact_path)

        run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

        task = _get_task(vault, task_id)
        assert task["status"] == "done"
        assert task["owner"] == "Hermes"

    def test_full_event_trail(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        _make_artifact(vault, artifact_path, "# Digest\n2026-04-25\nContent.\n")
        task_id = self._dispatch_task(vault, artifact_path)

        run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

        events = _get_events(vault, task_id)
        event_types = [e["event_type"] for e in events]
        assert "created" in event_types
        assert "claimed" in event_types
        assert "started" in event_types
        assert "result_attached" in event_types

    def test_review_result_in_final_event(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        artifact_path = "07_LOGS/Operator-Briefs/2026-04-25-brief.md"
        _make_artifact(vault, artifact_path, "# Operator Brief\n## Status\n2026-04-25\nAll good.\n")
        task_id = self._dispatch_task(vault, artifact_path)

        result = run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

        # Final event message should contain the review summary
        events = _get_events(vault, task_id)
        result_event = next(e for e in events if e["event_type"] == "result_attached")
        assert "Hermes Review" in result_event["message"]

    def test_endorsed_for_good_artifact(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        good_content = "# Digest\n## Market Summary\n2026-04-25\n" + ("word " * 50)
        _make_artifact(vault, artifact_path, good_content)
        task_id = self._dispatch_task(vault, artifact_path)

        result = run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

        assert len(result["endorsed"]) > 0

    def test_flags_for_missing_artifact(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        # Artifact path is valid scope but file doesn't exist
        artifact_path = "07_LOGS/SBP-Runs/nonexistent.md"
        task_id = self._dispatch_task(vault, artifact_path)

        result = run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

        assert len(result["flags"]) > 0
        assert any("not readable" in f.lower() for f in result["flags"])

    def test_out_of_scope_artifact_raises(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        # SOUL.md is outside review scope
        task_id = self._dispatch_task(vault, "SOUL.md")

        with pytest.raises(ExecuteError, match="outside the review role"):
            run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

    def test_out_of_scope_artifact_marks_bus_blocked(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        task_id = self._dispatch_task(vault, "SOUL.md")

        try:
            run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)
        except ExecuteError:
            pass

        task = _get_task(vault, task_id)
        assert task["status"] == "blocked"

    def test_no_task_returns_clean_noop(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)

        result = run_hermes_review_execute(inputs={}, vault_root=vault)

        assert result["task_id"] is None
        assert result["status"] == "no_task"
        assert result["writebacks"] == []

    def test_returns_writeback_entry_on_success(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        _make_artifact(vault, artifact_path, "# Digest\n2026-04-25\nContent.\n")
        task_id = self._dispatch_task(vault, artifact_path)

        result = run_hermes_review_execute(inputs={"task_id": task_id}, vault_root=vault)

        assert len(result["writebacks"]) == 1
        wb = result["writebacks"][0]
        assert "07_LOGS/Agent-Activity/" in wb["path"]

    def test_wrong_recipient_raises(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        # Create a task addressed to OpenClaw, not Hermes
        from runtime.agent_bus.bus import create_task
        r = create_task(vault, sender="Hermes", recipient="OpenClaw",
                        request="do work", expected_output="result")
        assert r["created"]
        wrong_task_id = r["task_id"]

        with pytest.raises(ExecuteError, match="not Hermes"):
            run_hermes_review_execute(inputs={"task_id": wrong_task_id}, vault_root=vault)


# ── Full end-to-end lifecycle ──────────────────────────────────────────────────

class TestFullBusLifecycle:
    def test_dispatch_then_execute_full_cycle(self, tmp_path):
        """Complete: OpenClaw dispatches → Hermes claims → reviews → done."""
        vault = _vault(tmp_path)
        _setup_caps(vault)
        _set_fresh_heartbeat(vault, "Hermes")
        init_db(vault)

        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-strikezone-digest.md"
        _make_artifact(vault, artifact_path,
            "# StrikeZone Digest\n## Market Summary\n2026-04-25\n"
            + "The markets moved. " * 20)

        # Step 1: OpenClaw dispatches the review task
        dispatch_result = run_openclaw_post_review_task(
            inputs={
                "artifact_path": artifact_path,
                "request": "Review StrikeZone digest for completeness and accuracy flags.",
                "expected_output": "Structured review with endorsements and flags.",
            },
            vault_root=vault,
        )
        task_id = dispatch_result["task_id"]
        assert dispatch_result["recipient"] == "Hermes"

        # Verify bus state after dispatch
        tasks_open = list_tasks(vault, status="open", recipient="Hermes")
        assert any(t["task_id"] == task_id for t in tasks_open)

        # Step 2: Hermes claims and executes the review
        execute_result = run_hermes_review_execute(
            inputs={"task_id": task_id},
            vault_root=vault,
        )

        assert execute_result["task_id"] == task_id
        assert execute_result["status"] == "done"
        assert len(execute_result["endorsed"]) > 0

        # Verify bus state after execution
        task = _get_task(vault, task_id)
        assert task["status"] == "done"
        assert task["owner"] == "Hermes"

        # Verify full event trail
        events = _get_events(vault, task_id)
        event_types = [e["event_type"] for e in events]
        assert event_types == ["created", "claimed", "started", "result_attached"]

    def test_multiple_tasks_claimed_in_order(self, tmp_path):
        """Hermes claims open tasks in FIFO order when no task_id specified."""
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)

        artifact_a = "07_LOGS/Build-Logs/log-a.md"
        artifact_b = "07_LOGS/Build-Logs/log-b.md"
        _make_artifact(vault, artifact_a, "# Log A\n2026-04-25\nFirst log.\n")
        _make_artifact(vault, artifact_b, "# Log B\n2026-04-25\nSecond log.\n")

        result_a = run_openclaw_post_review_task(
            inputs={"artifact_path": artifact_a, "request": "Review A."},
            vault_root=vault,
        )
        result_b = run_openclaw_post_review_task(
            inputs={"artifact_path": artifact_b, "request": "Review B."},
            vault_root=vault,
        )

        # Claim first (no task_id specified → oldest open)
        claimed_first = run_hermes_review_execute(inputs={}, vault_root=vault)
        assert claimed_first["task_id"] == result_a["task_id"]

        # Claim second
        claimed_second = run_hermes_review_execute(inputs={}, vault_root=vault)
        assert claimed_second["task_id"] == result_b["task_id"]

        # Queue empty
        empty = run_hermes_review_execute(inputs={}, vault_root=vault)
        assert empty["task_id"] is None

    def test_dispatch_result_embeds_route_info(self, tmp_path):
        vault = _vault(tmp_path)
        _setup_caps(vault)
        _set_fresh_heartbeat(vault, "Hermes")
        init_db(vault)
        artifact = "07_LOGS/SBP-Runs/digest.md"
        _make_artifact(vault, artifact, "# D\n2026-04-25\nContent.\n")

        result = run_openclaw_post_review_task(
            inputs={"artifact_path": artifact, "request": "Review."},
            vault_root=vault,
        )

        assert result["route_recommended"] == "Hermes"
        assert "Hermes" in result["route_reason"]


# ── Scope check helpers ────────────────────────────────────────────────────────

class TestArtifactScopeCheck:
    def test_sbp_runs_in_scope(self):
        assert _artifact_in_scope("07_LOGS/SBP-Runs/2026-04-25-digest.md")

    def test_operator_briefs_in_scope(self):
        assert _artifact_in_scope("07_LOGS/Operator-Briefs/2026-04-25-brief.md")

    def test_build_logs_in_scope(self):
        assert _artifact_in_scope("07_LOGS/Build-Logs/2026-04-25-log.md")

    def test_agent_activity_in_scope(self):
        assert _artifact_in_scope("07_LOGS/Agent-Activity/some-audit.md")

    def test_runtime_agent_bus_in_scope(self):
        assert _artifact_in_scope("runtime/agent_bus/Agent-Bus-Folder-Guide.md")

    def test_soul_md_out_of_scope(self):
        assert not _artifact_in_scope("SOUL.md")

    def test_now_md_out_of_scope(self):
        assert not _artifact_in_scope("00_HOME/Now.md")

    def test_knowledge_out_of_scope(self):
        assert not _artifact_in_scope("02_KNOWLEDGE/Tech/some-note.md")

    def test_projects_out_of_scope(self):
        assert not _artifact_in_scope("01_PROJECTS/ChaseOS/ChaseOS-OS.md")

    def test_empty_path_out_of_scope(self):
        assert not _artifact_in_scope("")


# ── Structural review logic ────────────────────────────────────────────────────

class TestProduceReview:
    def test_good_artifact_has_endorsements(self):
        content = "# My Brief\n## Section A\n2026-04-25\n" + "word " * 30
        result = _produce_review(request="Review this.", artifact_path="test.md",
                                  artifact_content=content)
        assert len(result["endorsed"]) > 0

    def test_none_content_produces_flag(self):
        result = _produce_review(request="Review this.", artifact_path="test.md",
                                  artifact_content=None)
        assert len(result["flags"]) > 0
        assert "not readable" in result["flags"][0].lower()

    def test_empty_content_flagged(self):
        result = _produce_review(request="Review.", artifact_path="t.md",
                                  artifact_content="hi")
        assert any("short" in f.lower() for f in result["flags"])

    def test_no_headings_flagged(self):
        content = "just some flat text without headings. " * 10 + " 2026-04-25"
        result = _produce_review(request="Review.", artifact_path="t.md",
                                  artifact_content=content)
        assert any("heading" in f.lower() for f in result["flags"])

    def test_no_date_flagged(self):
        content = "# Header\n## Section\n" + "word " * 20
        result = _produce_review(request="Review.", artifact_path="t.md",
                                  artifact_content=content)
        assert any("date" in f.lower() for f in result["flags"])

    def test_summary_contains_verdict(self):
        content = "# Brief\n2026-04-25\n" + "word " * 30
        result = _produce_review(request="Review.", artifact_path="t.md",
                                  artifact_content=content)
        assert "Hermes Review" in result["summary"]
        assert "Verdict" in result["summary"]


# ── AOR engine integration ─────────────────────────────────────────────────────

class TestAOREngineIntegration:
    def _make_full_vault(self, tmp_path: Path) -> Path:
        import shutil
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True, exist_ok=True)

        # AOR engine context boot requires Now.md
        now_dir = vault / "00_HOME"
        now_dir.mkdir(parents=True, exist_ok=True)
        (now_dir / "Now.md").write_text(
            "# Now\n## Phase 9 Active\nTest vault sprint anchor.", encoding="utf-8"
        )

        # AOR registry: copy the real manifests into the test vault
        real_root = Path(__file__).resolve().parents[2]
        registry_src = real_root / "runtime" / "workflows" / "registry"
        registry_dst = vault / "runtime" / "workflows" / "registry"
        registry_dst.mkdir(parents=True, exist_ok=True)
        for f in ["openclaw_post_review_task.yaml", "hermes_review_execute.yaml",
                  "_schema.yaml", "operator_today.yaml"]:
            src = registry_src / f
            if src.exists():
                shutil.copy(src, registry_dst / f)

        # Role cards: copy review.yaml
        role_src = real_root / "06_AGENTS" / "role-cards"
        role_dst = vault / "06_AGENTS" / "role-cards"
        role_dst.mkdir(parents=True, exist_ok=True)
        for f in ["review.yaml", "operator-briefing.yaml"]:
            src = role_src / f
            if src.exists():
                shutil.copy(src, role_dst / f)

        # Task type table
        aor_src = real_root / "runtime" / "aor"
        aor_dst = vault / "runtime" / "aor"
        aor_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy(aor_src / "task_type_table.yaml", aor_dst / "task_type_table.yaml")

        return vault

    def test_openclaw_post_review_routes_through_aor(self, tmp_path):
        from runtime.aor.engine import run_workflow
        vault = self._make_full_vault(tmp_path)
        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        _make_artifact(vault, artifact_path, "# Digest\n2026-04-25\nContent.\n")

        result = run_workflow(
            "openclaw_post_review_task",
            inputs={
                "artifact_path": artifact_path,
                "request": "Review the digest.",
                "expected_output": "Structured review.",
            },
            vault_root=vault,
        )

        assert result.status == "success", f"Unexpected: {result.escalation_reason or result.error}"
        assert "task_id" in result.outputs.get("run", {})

    def test_hermes_review_execute_routes_through_aor(self, tmp_path):
        from runtime.aor.engine import run_workflow
        vault = self._make_full_vault(tmp_path)
        artifact_path = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        _make_artifact(vault, artifact_path, "# Digest\n## Section\n2026-04-25\n" + "word " * 30)

        # Dispatch task first (directly, not via AOR)
        dispatch = run_openclaw_post_review_task(
            inputs={
                "artifact_path": artifact_path,
                "request": "Review the digest.",
                "expected_output": "Structured review.",
            },
            vault_root=vault,
        )
        task_id = dispatch["task_id"]

        result = run_workflow(
            "hermes_review_execute",
            inputs={"task_id": task_id},
            vault_root=vault,
        )

        assert result.status == "success", f"Unexpected: {result.escalation_reason or result.error}"
        run_out = result.outputs.get("run", {})
        assert run_out["task_id"] == task_id
        assert run_out["status"] == "done"

    def test_aor_dry_run_dispatches_cleanly(self, tmp_path):
        from runtime.aor.engine import run_workflow
        vault = self._make_full_vault(tmp_path)

        result = run_workflow(
            "openclaw_post_review_task",
            inputs={
                "artifact_path": "07_LOGS/SBP-Runs/test.md",
                "request": "Review.",
            },
            vault_root=vault,
            dry_run=True,
        )

        assert result.status == "dry_run_ok"

    def test_full_cycle_via_aor(self, tmp_path):
        from runtime.aor.engine import run_workflow
        vault = self._make_full_vault(tmp_path)
        _set_fresh_heartbeat(vault, "Hermes")
        artifact_path = "07_LOGS/Operator-Briefs/2026-04-25-brief.md"
        _make_artifact(vault, artifact_path, "# Brief\n## Sprint\n2026-04-25\n" + "word " * 20)

        # OpenClaw dispatches via AOR
        dispatch = run_workflow(
            "openclaw_post_review_task",
            inputs={"artifact_path": artifact_path, "request": "Review brief."},
            vault_root=vault,
        )
        assert dispatch.status == "success"
        task_id = dispatch.outputs["run"]["task_id"]

        # Hermes executes via AOR
        execute = run_workflow(
            "hermes_review_execute",
            inputs={"task_id": task_id},
            vault_root=vault,
        )
        assert execute.status == "success"
        assert execute.outputs.get("run", {})["status"] == "done"

        # Verify bus is clean
        task = _get_task(vault, task_id)
        assert task["status"] == "done"


# ── SBP StrikeZone digest → review dispatch wiring ────────────────────────────

class TestSBPReviewDispatch:
    """Tests for _attempt_review_dispatch and run_sbp_strikezone_digest wiring."""

    def _make_sbp_vault(self, tmp_path: Path) -> Path:
        vault = _vault(tmp_path)
        _setup_caps(vault)
        init_db(vault)
        # Seed files required by vault-notes adapter
        (vault / "00_HOME").mkdir(parents=True, exist_ok=True)
        (vault / "00_HOME" / "Now.md").write_text(
            "# Now\n## Phase 9 Active\nTest vault sprint anchor.", encoding="utf-8"
        )
        (vault / "01_PROJECTS" / "StrikeZone").mkdir(parents=True, exist_ok=True)
        (vault / "01_PROJECTS" / "StrikeZone" / "StrikeZone-Crypto-OS.md").write_text(
            "# StrikeZone-Crypto-OS\nTest project state.", encoding="utf-8"
        )
        return vault

    def test_attempt_review_dispatch_returns_task_id(self, tmp_path):
        from runtime.workflows.sbp_strikezone_digest import _attempt_review_dispatch
        vault = self._make_sbp_vault(tmp_path)

        result = _attempt_review_dispatch("07_LOGS/SBP-Runs/2026-04-25-digest.md", vault)

        assert result is not None
        assert result.get("created") is True
        assert result.get("task_id", "").startswith("task-")

    def test_attempt_review_dispatch_sender_recipient(self, tmp_path):
        from runtime.workflows.sbp_strikezone_digest import _attempt_review_dispatch
        vault = self._make_sbp_vault(tmp_path)

        _attempt_review_dispatch("07_LOGS/SBP-Runs/2026-04-25-digest.md", vault)

        tasks = list_tasks(vault)
        assert len(tasks) == 1
        t = tasks[0]
        assert t["sender"] == "OpenClaw"
        assert t["recipient"] == "Hermes"
        assert t["intent"] == "REVIEW"
        assert t["priority"] == "normal"

    def test_attempt_review_dispatch_notes_contain_artifact_path(self, tmp_path):
        from runtime.workflows.sbp_strikezone_digest import _attempt_review_dispatch
        vault = self._make_sbp_vault(tmp_path)

        artifact = "07_LOGS/SBP-Runs/2026-04-25-digest.md"
        _attempt_review_dispatch(artifact, vault)

        tasks = list_tasks(vault)
        notes = tasks[0].get("notes", "") or ""
        assert f"artifact_path: {artifact}" in notes

    def test_attempt_review_dispatch_failopen_on_broken_bus(self, tmp_path):
        from runtime.workflows.sbp_strikezone_digest import _attempt_review_dispatch
        vault = self._make_sbp_vault(tmp_path)

        with patch(
            "runtime.agent_bus.bus.create_task",
            side_effect=RuntimeError("simulated bus failure"),
        ):
            result = _attempt_review_dispatch("07_LOGS/SBP-Runs/test.md", vault)

        assert result is None  # fail-open: returns None, does not raise

    def _minimal_manifest(self) -> dict:
        return {
            "id": "sbp_strikezone_digest",
            "sbp_config": {
                "trigger": {"type": "manual"},
                "execution_adapter": "openclaw",
                "input_adapters": [
                    {"type": "vault-notes", "trust_tier": 1,
                     "paths": ["00_HOME/Now.md", "01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md"]},
                ],
                "delivery_adapters": [],
                "guardrail": {"permission_ceiling": "no_protected_file_writes"},
            },
        }

    class _FakeSynthesis:
        text = "# StrikeZone Digest\n## Market\n2026-04-25\n" + "word " * 20
        runtime = "stub"
        model_id = "stub-model"
        fallback_used = False

    def test_run_sbp_strikezone_digest_attaches_review_task(self, tmp_path):
        """run_sbp_strikezone_digest attaches review_task key when digest succeeds."""
        from runtime.workflows.sbp_strikezone_digest import run_sbp_strikezone_digest
        vault = self._make_sbp_vault(tmp_path)

        with patch(
            "runtime.workflows.sbp_strikezone_digest.execute_synthesis",
            return_value=self._FakeSynthesis(),
        ):
            result = run_sbp_strikezone_digest(
                inputs={}, vault_root=vault, manifest=self._minimal_manifest()
            )

        assert "review_task" in result
        assert result["review_task"] is not None
        assert result["review_task"].get("created") is True

    def test_run_sbp_strikezone_digest_review_task_has_correct_artifact(self, tmp_path):
        """review_task notes contain the digest artifact path from writebacks."""
        from runtime.workflows.sbp_strikezone_digest import run_sbp_strikezone_digest
        vault = self._make_sbp_vault(tmp_path)

        with patch(
            "runtime.workflows.sbp_strikezone_digest.execute_synthesis",
            return_value=self._FakeSynthesis(),
        ):
            result = run_sbp_strikezone_digest(
                inputs={}, vault_root=vault, manifest=self._minimal_manifest()
            )

        tasks = list_tasks(vault)
        assert len(tasks) == 1
        notes = tasks[0].get("notes", "") or ""
        assert "07_LOGS/SBP-Runs/" in notes
        assert ".md" in notes

    def test_run_sbp_digest_failopen_when_dispatch_raises(self, tmp_path):
        """Digest completes successfully even if review dispatch fails."""
        from runtime.workflows.sbp_strikezone_digest import run_sbp_strikezone_digest
        vault = self._make_sbp_vault(tmp_path)

        with patch(
            "runtime.workflows.sbp_strikezone_digest.execute_synthesis",
            return_value=self._FakeSynthesis(),
        ), patch(
            "runtime.agent_bus.bus.create_task",
            side_effect=RuntimeError("simulated bus failure"),
        ):
            result = run_sbp_strikezone_digest(
                inputs={}, vault_root=vault, manifest=self._minimal_manifest()
            )

        assert result.get("handler_status") == "executed"
        assert result.get("review_task") is None
