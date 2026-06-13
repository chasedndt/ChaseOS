from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import textwrap

from runtime.studio.phase11_chat_agent_bus_dispatch_bridge import (
    dispatch_chat_agent_bus_aor_bridge,
    preview_chat_agent_bus_dispatch_bridge,
)


@dataclass
class FakeAORResult:
    workflow_id: str
    status: str = "dry_run_ok"
    audit_id: str = "audit-fake-123"
    stage_reached: str = "dry_run_exit"
    manifest_snapshot: dict | None = None


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def _seed_vault(root: Path) -> None:
    _write(root / "CLAUDE.md", "# test vault")
    _write(root / "00_HOME" / "Now.md", "# Now\nCurrent phase: test")
    (root / "07_LOGS" / "Agent-Activity").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "agent_bus").mkdir(parents=True, exist_ok=True)
    _write(
        root / "runtime" / "codex" / "capabilities.yaml",
        """
        runtime: Codex
        bus_name: Codex
        display_name: Codex
        retained_runtime_name: Axiom-Codex
        description: Test Codex runtime
        handles:
          - task_type: coordination
            priority: primary
        priority_ceiling: high
        max_concurrent_tasks: 1
        heartbeat_stale_seconds: 900
        """,
    )
    _write(
        root / "06_AGENTS" / "role-cards" / "review.yaml",
        """
        id: review
        name: Review
        version: "1.0"
        description: Test review card
        owner: operator
        allowed_actions:
          - read_vault
          - write_logs
        forbidden_actions:
          - canonical_write
        write_scope:
          - "07_LOGS/Agent-Activity/"
        forbidden_write_zones:
          - "02_KNOWLEDGE/"
        escalation_rules:
          - block on canonical writes
        runtime_expectations:
          - dry-run safe
        required_reads:
          - "00_HOME/Now.md"
        optional_reads:
          - "07_LOGS/Agent-Activity/"
        """,
    )
    _write(
        root / "runtime" / "workflows" / "registry" / "codex_watch.yaml",
        """
        id: codex_watch
        name: Codex Watch
        version: "1.0"
        description: Test workflow bound to Codex
        task_type: coordination
        role_card: review
        trigger_type: manual
        owner: operator
        status: active
        runtime_adapter: Codex
        permission_ceiling: bus_result_only
        inputs:
          - task_id
        outputs:
          - task_id
        writeback_targets:
          - "07_LOGS/Agent-Activity/"
        failure_behavior: escalate
        approval_rule: none
        """,
    )


def _approval_for_preview(preview: dict, approval_id: str) -> dict:
    return {
        "approval_id": approval_id,
        "decision": "approved",
        "applied_to_execution": True,
        "binding": dict(preview["approval_binding"]["expected"]),
    }


def test_preview_is_schema_valid_and_has_no_side_effects(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    payload = preview_chat_agent_bus_dispatch_bridge(
        tmp_path,
        message="Ask Axiom-Codex to coordinate this runtime task",
        workflow_id="codex_watch",
        requested_runtime_id="Axiom-Codex",
        requested_action="coordination",
        origin_message_id="chat-msg-1",
    )

    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["side_effects_performed"] is False
    assert payload["summary"]["task_packet_schema_valid"] is True
    assert payload["summary"]["selected_runtime_id"] == "Codex"
    assert payload["runtime_identity"]["runtime_instance_id_hint"] == "Axiom-Codex"
    assert not (tmp_path / "runtime" / "agent_bus" / "agent_bus.sqlite").exists()


def test_dispatch_blocks_without_approval_and_writes_nothing(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    payload = dispatch_chat_agent_bus_aor_bridge(
        tmp_path,
        message="Ask Codex to coordinate this runtime task",
        workflow_id="codex_watch",
        requested_runtime_id="Codex",
        requested_action="coordination",
        approval_state=None,
    )

    assert payload["ok"] is False
    assert "operator_runtime_dispatch_approval_missing" in payload["blocked_reasons"]
    assert payload["side_effects_performed"] is False
    assert not (tmp_path / "runtime" / "agent_bus" / "agent_bus.sqlite").exists()


def test_approved_dispatch_writes_bus_packet_and_links_aor_audit(tmp_path: Path) -> None:
    _seed_vault(tmp_path)
    calls: list[dict] = []

    def fake_runner(workflow_id: str, **kwargs):
        calls.append({"workflow_id": workflow_id, **kwargs})
        return FakeAORResult(
            workflow_id=workflow_id,
            manifest_snapshot={"id": workflow_id, "task_type": "coordination", "role_card": "review"},
        )

    approval_preview = preview_chat_agent_bus_dispatch_bridge(
        tmp_path,
        message="Ask Axiom-Codex to coordinate this runtime task",
        workflow_id="codex_watch",
        requested_runtime_id="Axiom-Codex",
        requested_action="coordination",
        ingress_context={
            "source_platform": "phase11-chat",
            "source_channel_class": "phase11_chat",
            "conversation_key": "phase11-chat:test-thread",
            "origin_message_id": "chat-msg-2",
        },
    )
    payload = dispatch_chat_agent_bus_aor_bridge(
        tmp_path,
        message="Ask Axiom-Codex to coordinate this runtime task",
        workflow_id="codex_watch",
        requested_runtime_id="Axiom-Codex",
        requested_action="coordination",
        approval_state=_approval_for_preview(approval_preview, "appr-chat-1"),
        ingress_context={
            "source_platform": "phase11-chat",
            "source_channel_class": "phase11_chat",
            "conversation_key": "phase11-chat:test-thread",
            "origin_message_id": "chat-msg-2",
        },
        aor_runner=fake_runner,
    )

    assert payload["ok"] is True
    assert payload["summary"]["agent_bus_task_created"] is True
    assert payload["summary"]["aor_dispatched"] is True
    assert payload["summary"]["aor_dry_run"] is True
    assert payload["summary"]["bus_aor_audit_linked"] is True
    assert calls and calls[0]["dry_run"] is True
    assert calls[0]["inputs"]["operator_approval_ref"] == "appr-chat-1"

    db_path = tmp_path / "runtime" / "agent_bus" / "agent_bus.sqlite"
    assert db_path.exists()
    stored = payload["bus_task"]["stored_task"]
    assert stored["sender"] == "Operator"
    assert stored["recipient"] == "Codex"
    assert stored["status"] == "open"
    assert stored["work_fingerprint"].startswith("chat-dispatch:")
    assert stored["execution_constraints"]["write_policy"] == "none"
    notes = json.loads(stored["notes"])
    assert notes["workflow_id"] == "codex_watch"
    assert notes["approval_id"] == "appr-chat-1"
    audit_path = tmp_path / payload["audit_path"]
    assert audit_path.exists()


def test_dispatch_blocks_workflow_runtime_mismatch(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    payload = dispatch_chat_agent_bus_aor_bridge(
        tmp_path,
        message="Ask Codex to coordinate this runtime task",
        workflow_id="codex_watch",
        requested_runtime_id="NotARealAlias",
        requested_action="coordination",
        approval_state={"approval_id": "appr-chat-2", "decision": "approved"},
    )

    assert payload["ok"] is False
    assert any(reason.startswith("runtime_identity_resolution_failed:") for reason in payload["blocked_reasons"])
    assert payload["side_effects_performed"] is False


def test_approved_dispatch_blocks_when_runtime_lacks_requested_task_type(tmp_path: Path) -> None:
    _seed_vault(tmp_path)
    _write(
        tmp_path / "runtime" / "mismatch" / "capabilities.yaml",
        """
        runtime: Mismatch
        bus_name: Mismatch
        display_name: Mismatch
        description: Test runtime that cannot handle coordination
        handles:
          - task_type: repo.inspect
            priority: primary
        priority_ceiling: high
        max_concurrent_tasks: 1
        heartbeat_stale_seconds: 900
        """,
    )
    _write(
        tmp_path / "runtime" / "workflows" / "registry" / "mismatch_watch.yaml",
        """
        id: mismatch_watch
        name: Mismatch Watch
        version: "1.0"
        description: Test workflow bound to a runtime lacking the workflow task type
        task_type: coordination
        role_card: review
        trigger_type: manual
        owner: operator
        status: active
        runtime_adapter: Mismatch
        permission_ceiling: bus_result_only
        inputs:
          - task_id
        outputs:
          - task_id
        writeback_targets:
          - "07_LOGS/Agent-Activity/"
        failure_behavior: escalate
        approval_rule: none
        """,
    )

    approval_preview = preview_chat_agent_bus_dispatch_bridge(
        tmp_path,
        message="Ask Mismatch to coordinate this runtime task",
        workflow_id="mismatch_watch",
        requested_runtime_id="Mismatch",
        requested_action="coordination",
    )
    payload = dispatch_chat_agent_bus_aor_bridge(
        tmp_path,
        message="Ask Mismatch to coordinate this runtime task",
        workflow_id="mismatch_watch",
        requested_runtime_id="Mismatch",
        requested_action="coordination",
        approval_state=_approval_for_preview(approval_preview, "appr-chat-capability"),
    )

    assert payload["ok"] is False
    assert "selected_runtime_does_not_advertise_task_type" in payload["blocked_reasons"]
    assert payload["side_effects_performed"] is False
    assert not (tmp_path / "runtime" / "agent_bus" / "agent_bus.sqlite").exists()


def test_approved_dispatch_blocks_when_approval_lacks_request_binding(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    payload = dispatch_chat_agent_bus_aor_bridge(
        tmp_path,
        message="Ask Axiom-Codex to coordinate this runtime task",
        workflow_id="codex_watch",
        requested_runtime_id="Axiom-Codex",
        requested_action="coordination",
        approval_state={"approval_id": "appr-chat-unbound", "decision": "approved", "applied_to_execution": True},
    )

    assert payload["ok"] is False
    assert "operator_runtime_dispatch_approval_binding_missing" in payload["blocked_reasons"]
    assert payload["side_effects_performed"] is False
    assert not (tmp_path / "runtime" / "agent_bus" / "agent_bus.sqlite").exists()
