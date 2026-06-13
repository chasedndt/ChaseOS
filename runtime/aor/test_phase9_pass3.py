"""
test_phase9_pass3.py -- ChaseOS Phase 9 Pass 3

Tests for operator_close_day — the end-of-day close workflow.

Running:
  PYTHONIOENCODING=utf-8 python runtime/aor/test_phase9_pass3.py
"""

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

from runtime.aor.engine import run_workflow
from runtime.cli.main import main as cli_main


_TESTS: list[tuple[str, object]] = []
_PASS = 0
_FAIL = 0
_ERRORS: list[str] = []


class _LocalTempVault:
    def __init__(self, root: Path) -> None:
        self.name = str(root)

    def cleanup(self) -> None:
        shutil.rmtree(self.name, ignore_errors=True)


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
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
            _FAIL += 1
            _ERRORS.append(f"{name}: {type(exc).__name__}: {exc}")


def _make_temp_vault() -> _LocalTempVault:
    tmp_root = _VAULT_ROOT / ".codex_tmp_test"
    tmp_root.mkdir(parents=True, exist_ok=True)
    root = tmp_root / f"aor-pass3-{uuid.uuid4().hex}"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    return _LocalTempVault(root)


def _populate_close_day_runtime(root: Path, today_logs: bool = True) -> None:
    """Scaffold minimal vault for operator_close_day tests."""
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)
    (root / "00_HOME").mkdir(parents=True)
    (root / "03_INPUTS" / "Sources").mkdir(parents=True)
    (root / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)

    manifest = {
        "id": "operator_close_day",
        "name": "Operator Close Day",
        "version": "1.0",
        "description": "End-of-day close workflow.",
        "task_type": "operator-briefing",
        "role_card": "operator-briefing",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "permission_ceiling": "no_protected_file_writes",
        "writeback_targets": ["07_LOGS/Operator-Briefs/"],
        "failure_behavior": "escalate",
    }
    (root / "runtime" / "workflows" / "registry" / "operator_close_day.yaml").write_text(
        yaml.dump(manifest), encoding="utf-8"
    )

    card = {
        "id": "operator-briefing",
        "name": "Operator Briefing",
        "version": "1.0",
        "description": "Read-only briefing role.",
        "owner": "operator",
        "allowed_actions": ["read_vault", "write_logs"],
        "forbidden_actions": ["write_protected_files"],
        "write_scope": ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"],
        "forbidden_write_zones": ["00_HOME/Now.md", "01_PROJECTS/", "runtime/"],
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

    (root / "00_HOME" / "Now.md").write_text(
        "\n".join([
            "## Current Phase",
            "### Phase 9 — Operator Runtime — ACTIVE — Pass 3 complete.",
            "",
            "- ⬜ Pass 4 (NEXT): graph_hygiene handler",
            "",
            "## Active Now",
            "| Domain | Current focus |",
            "|--------|---------------|",
            "| ChaseOS / System Infrastructure | Phase 9 Pass 3 |",
        ]),
        encoding="utf-8",
    )

    (root / "07_LOGS" / "Decision-Ledger" / "2026-04-09-decision-aor.md").write_text(
        "decision", encoding="utf-8"
    )

    if today_logs:
        (root / "07_LOGS" / "Build-Logs" / "2026-04-09-ChaseOS-pass3.md").write_text(
            "build", encoding="utf-8"
        )


# ── Tests ─────────────────────────────────────────────────────────────────────

@_test("pass3: operator_close_day writes bounded close note and audit trail")
def test_close_day_real_path():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_close_day_runtime(root)

    result = run_workflow("operator_close_day", inputs={"date": "2026-04-09"}, vault_root=root)
    assert result.status == "success", f"expected success, got {result.status}: {result.escalation_reason}"
    assert result.outputs["run"]["handler_status"] == "executed"

    close_path = root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-close-day.md"
    assert close_path.exists(), f"close note not found at {close_path}"
    content = close_path.read_text(encoding="utf-8")
    # v2 output format — four-layer close brief
    assert "Operator Brief" in content and "CLOSE" in content and "2026-04-09" in content
    assert "Session-Close Checklist" in content
    assert "Tomorrow Focus" in content

    audit_files = list((root / "07_LOGS" / "Agent-Activity").glob("*.json"))
    assert len(audit_files) == 1
    record = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert record["workflow_id"] == "operator_close_day"
    assert record["status"] == "success"
    assert "07_LOGS/Operator-Briefs/2026-04-09-operator-close-day.md" in str(
        record["outputs"]["writeback"]["files_written"]
    )
    tmp.cleanup()


@_test("pass3: close note contains today's build log entries")
def test_close_day_today_builds_shown():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_close_day_runtime(root, today_logs=True)

    result = run_workflow("operator_close_day", inputs={"date": "2026-04-09"}, vault_root=root)
    assert result.status == "success"

    close_path = root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-close-day.md"
    content = close_path.read_text(encoding="utf-8")
    assert "2026-04-09-ChaseOS-pass3.md" in content
    tmp.cleanup()


@_test("pass3: operator-provided open_loops appear in close note")
def test_close_day_operator_open_loops():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_close_day_runtime(root)

    result = run_workflow(
        "operator_close_day",
        inputs={"date": "2026-04-09", "open_loops": "Finish graph_hygiene; Write SOP"},
        vault_root=root,
    )
    assert result.status == "success"
    close_path = root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-close-day.md"
    content = close_path.read_text(encoding="utf-8")
    assert "Finish graph_hygiene" in content
    assert "Write SOP" in content
    tmp.cleanup()


@_test("pass3: missing required context fails closed")
def test_close_day_missing_context():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_close_day_runtime(root)
    import shutil as _sh
    _sh.rmtree(root / "07_LOGS" / "Build-Logs")

    result = run_workflow("operator_close_day", inputs={"date": "2026-04-09"}, vault_root=root)
    # Stage 5 (required_reads) or Stage 6 (run) may catch missing build-logs dir
    assert result.status == "escalated", (
        f"expected escalated, got {result.status}; reason={result.escalation_reason}"
    )
    assert result.stage_reached in ("required_reads", "run"), (
        f"unexpected stage: {result.stage_reached}"
    )
    tmp.cleanup()


@_test("pass3: dry_run succeeds without writing files")
def test_close_day_dry_run():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_close_day_runtime(root)

    result = run_workflow(
        "operator_close_day",
        inputs={"date": "2026-04-09"},
        vault_root=root,
        dry_run=True,
    )
    assert result.status == "dry_run_ok"
    close_path = root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-close-day.md"
    assert not close_path.exists(), "dry_run must not write files"
    tmp.cleanup()


@_test("pass3: cli run command executes operator_close_day end-to-end")
def test_cli_close_day():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_close_day_runtime(root)

    exit_code = cli_main([
        "run", "operator_close_day",
        "--date", "2026-04-09",
        "--vault-root", str(root),
    ])
    assert exit_code == 0
    assert (root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-close-day.md").exists()
    tmp.cleanup()


@_test("pass3: operator_today still works after close_day was added")
def test_operator_today_unaffected():
    """Regression: adding operator_close_day must not break operator_today."""
    from runtime.aor.test_phase9_pass2 import _populate_operator_today_runtime

    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_operator_today_runtime(root)

    result = run_workflow("operator_today", inputs={"date": "2026-04-09"}, vault_root=root)
    assert result.status == "success"
    assert (root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-today.md").exists()
    tmp.cleanup()


if __name__ == "__main__":
    print("\nPhase 9 Pass 3 — operator_close_day Tests")
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
