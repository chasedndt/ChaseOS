"""
test_phase9_pass2.py -- ChaseOS Phase 9 Pass 2

Focused tests for the first live AOR execution path.

Running:
  PYTHONIOENCODING=utf-8 python runtime/aor/test_phase9_pass2.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
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


def _make_temp_vault() -> tempfile.TemporaryDirectory:
    tmp_root = _VAULT_ROOT / ".codex_tmp_test"
    tmp_root.mkdir(parents=True, exist_ok=True)
    root = tmp_root / f"aor-pass2-{uuid.uuid4().hex}"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    return _LocalTempVault(root)


def _populate_operator_today_runtime(root: Path) -> None:
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)
    (root / "00_HOME").mkdir(parents=True)
    (root / "03_INPUTS" / "Sources").mkdir(parents=True)
    (root / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
    (root / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (root / "01_PROJECTS" / "TradingSystems").mkdir(parents=True)
    (root / "01_PROJECTS" / "StrikeZone").mkdir(parents=True)
    (root / "01_PROJECTS" / "University").mkdir(parents=True)

    manifest = {
        "id": "operator_today",
        "name": "Operator Today Briefing",
        "version": "1.0",
        "description": "Daily operator briefing.",
        "task_type": "operator-briefing",
        "role_card": "operator-briefing",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "permission_ceiling": "no_protected_file_writes",
        "writeback_targets": ["07_LOGS/Operator-Briefs/"],
        "failure_behavior": "escalate",
    }
    (root / "runtime" / "workflows" / "registry" / "operator_today.yaml").write_text(
        yaml.dump(manifest),
        encoding="utf-8",
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
        yaml.dump(card),
        encoding="utf-8",
    )

    (root / "00_HOME" / "Now.md").write_text(
        "\n".join(
            [
                "## Current Phase",
                "Phase 9 — Operator Runtime (AOR + SBP) — ACTIVE.",
                "",
                "## Active Now",
                "| Domain | Current focus |",
                "|--------|---------------|",
                "| ChaseOS / System Infrastructure | Phase 9 Pass 2 |",
                "| Trading Systems / Market Ops | Daily execution |",
                "| StrikeZone Crypto | Signal ops |",
                "| University | Coursework |",
                "",
                "- ⬜ Pass 2 (NEXT): Continue Phase 9 handler enablement",
            ]
        ),
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "ChaseOS" / "ChaseOS-OS.md").write_text(
        "## Open Loops\n- [ ] Keep AOR moving\n",
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
    (root / "07_LOGS" / "Build-Logs" / "2026-04-09-example.md").write_text("build", encoding="utf-8")
    (root / "07_LOGS" / "Decision-Ledger" / "2026-04-09-example.md").write_text("decision", encoding="utf-8")
    (root / "03_INPUTS" / "Sources" / "20260409-000000__source__item.md").write_text(
        "capture",
        encoding="utf-8",
    )


@_test("pass2: operator_today writes bounded brief and audit trail")
def test_operator_today_real_path():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_operator_today_runtime(root)

    result = run_workflow("operator_today", inputs={"date": "2026-04-09"}, vault_root=root)
    assert result.status == "success"
    assert result.outputs["run"]["handler_status"] == "executed"

    brief_path = root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-today.md"
    assert brief_path.exists()
    content = brief_path.read_text(encoding="utf-8")
    # v2 output format — four-layer brief
    assert "Operator Brief" in content and "OPEN" in content and "2026-04-09" in content
    assert "[CANONICAL]" in content or "[SOURCED]" in content or "[SYNTHESIS]" in content

    audit_files = list((root / "07_LOGS" / "Agent-Activity").glob("*.json"))
    assert len(audit_files) == 1
    record = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert record["workflow_id"] == "operator_today"
    assert record["outputs"]["writeback"]["files_written"] == [
        "07_LOGS/Operator-Briefs/2026-04-09-operator-today.md"
    ]
    tmp.cleanup()


@_test("pass2: missing project context fails closed")
def test_operator_today_missing_context():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_operator_today_runtime(root)
    (root / "01_PROJECTS" / "StrikeZone" / "StrikeZone-Crypto-OS.md").unlink()

    result = run_workflow("operator_today", inputs={"date": "2026-04-09"}, vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "run"
    assert "required project file missing" in (result.escalation_reason or "")
    tmp.cleanup()


@_test("pass2: cli run command executes operator_today end-to-end")
def test_cli_run_command():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    _populate_operator_today_runtime(root)

    exit_code = cli_main(["run", "operator_today", "--date", "2026-04-09", "--vault-root", str(root)])
    assert exit_code == 0
    assert (root / "07_LOGS" / "Operator-Briefs" / "2026-04-09-operator-today.md").exists()
    tmp.cleanup()


if __name__ == "__main__":
    print("\nPhase 9 Pass 2 — AOR Handler Enablement Tests")
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
