"""Gate coverage for event-triggered workflow dispatch."""

from __future__ import annotations

import sys
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.events.dispatcher as dispatcher  # noqa: E402


def _populate_event_dispatch_vault(root: Path) -> None:
    (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    (root / "runtime" / "events" / "rules").mkdir(parents=True)
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
    (root / "runtime" / "events" / "rules" / "acquisition.yaml").write_text(
        "\n".join(
            [
                'schema_version: "1.0"',
                "rule_id: acquisition-to-operator-today",
                "enabled: true",
                "event_type: acquisition.new_item",
                "dispatch:",
                "  mode: aor_workflow",
                "  target_workflow_id: operator_today",
                "  runtime_adapter: openclaw",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "runtime" / "workflows" / "registry" / "operator_today.yaml").write_text(
        "\n".join(
            [
                "id: operator_today",
                "name: Operator Today",
                'version: "1.0"',
                "description: Test operator brief workflow",
                "task_type: operator-briefing",
                "role_card: operator-briefing",
                "trigger_type: manual",
                "owner: operator",
                "status: active",
                "permission_ceiling: no_protected_file_writes",
                "writeback_targets:",
                "  - 07_LOGS/Operator-Briefs/",
                "failure_behavior: escalate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _event() -> dispatcher.RuntimeEvent:
    return dispatcher.RuntimeEvent(
        event_id="evt-test",
        event_type="acquisition.new_item",
        created_at="2026-04-28T00:00:00Z",
        source={"kind": "workflow", "workflow_id": "strikezone_acquisition"},
        subject={"kind": "briefing_ready_input_set", "ref": "runtime/acquisition/packs/test.json"},
        payload={},
        status="pending",
    )


def test_execute_dispatch_gate_blocks_before_aor_call(monkeypatch: pytest.MonkeyPatch) -> None:
    scratch = _VAULT_ROOT / ".codex_tmp_test"
    scratch.mkdir(parents=True, exist_ok=True)
    vault_root = scratch / f"events-dispatch-gate-{uuid.uuid4().hex}"
    vault_root.mkdir()
    _populate_event_dispatch_vault(vault_root)
    called = {"run": False}

    def fake_check_runtime_operation(*args, **kwargs):
        return False, "blocked-by-gateway-dispatch-policy"

    def fake_run_workflow(*args, **kwargs):
        called["run"] = True
        return SimpleNamespace(status="success")

    monkeypatch.setattr(dispatcher, "check_runtime_operation", fake_check_runtime_operation)
    monkeypatch.setattr(dispatcher, "run_workflow", fake_run_workflow)

    try:
        with pytest.raises(dispatcher.DispatchError, match="gateway.workflow.dispatch"):
            dispatcher.dispatch_event(_event(), vault_root=vault_root, execute=True)

        assert called["run"] is False
    finally:
        shutil.rmtree(vault_root, ignore_errors=True)
