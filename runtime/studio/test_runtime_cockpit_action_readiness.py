"""Tests for Phase 10AC Runtime Cockpit action readiness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.runtime_cockpit_action_readiness import (
    RuntimeCockpitActionReadinessError,
    build_runtime_cockpit_action_readiness,
    queue_runtime_cockpit_action_request,
)
from runtime.studio.service import StudioService


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "runtime" / "lifecycle").mkdir(parents=True)
    for runtime_id, runtime_name in {
        "codex": "Codex",
        "hermes": "Hermes",
        "openclaw": "OpenClaw",
    }.items():
        (vault / "runtime" / "lifecycle" / f"{runtime_id}.lifecycle.yaml").write_text(
            f"runtime_id: {runtime_id}\n"
            f"coordination_watch:\n"
            f"  runtime_name: {runtime_name}\n"
            f"health:\n"
            f"  kind: fixture\n",
            encoding="utf-8",
        )
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    return vault


def test_runtime_cockpit_action_readiness_reports_boundaries(tmp_path: Path) -> None:
    model = build_runtime_cockpit_action_readiness(_vault(tmp_path))

    assert model["ok"] is True
    assert model["surface"] == "studio_runtime_cockpit_action_readiness"
    assert model["status"] == "COMPLETE / APPROVAL-GATED / VERIFIED"
    assert model["write_mode"] == "approval_gated"
    assert model["summary"]["action_count"] >= model["summary"]["requestable_action_count"]
    assert model["authority_boundary"]["approval_packet_request_allowed"] is True
    assert model["authority_boundary"]["direct_runtime_execution_allowed"] is False
    assert model["authority_boundary"]["host_mutation_allowed"] is False
    assert model["authority_boundary"]["agent_bus_task_writes_allowed"] is False
    assert model["readiness"]["no_provider_or_connector_calls"] is True
    assert model["next_recommended_pass"] == "phase10f1-open-folder-compatibility-readiness"


def test_runtime_cockpit_action_readiness_has_blocked_lifecycle_actions(tmp_path: Path) -> None:
    model = build_runtime_cockpit_action_readiness(_vault(tmp_path))
    lifecycle = [item for item in model["action_readiness"] if item["category"] == "runtime-lifecycle"]

    assert lifecycle
    assert all(item["status"] == "blocked" for item in lifecycle)
    assert all(item["approval_packet_requestable"] is False for item in lifecycle)
    assert all(item["authority_boundary"]["executes_runtime_action"] is False for item in lifecycle)


def test_runtime_cockpit_action_readiness_names_blocked_backend_taxonomy(tmp_path: Path) -> None:
    model = build_runtime_cockpit_action_readiness(_vault(tmp_path), runtime_id="hermes")
    actions = {item["action_id"]: item for item in model["action_readiness"]}

    agent_bus = actions["readiness:hermes:agent-bus-review"]
    provider = actions["readiness:hermes:provider-config-review"]

    assert agent_bus["status"] == "blocked"
    assert agent_bus["approval_packet_requestable"] is False
    assert "agent-bus-task-write-not-mounted-from-runtime-cockpit" in agent_bus["blockers"]
    assert agent_bus["authority_boundary"]["writes_agent_bus_task"] is False
    assert provider["status"] == "blocked"
    assert provider["approval_packet_requestable"] is False
    assert "provider-config-apply-not-mounted-from-runtime-cockpit" in provider["blockers"]
    assert "provider-calls-forbidden" in provider["blockers"]
    assert provider["authority_boundary"]["calls_provider"] is False


def test_runtime_cockpit_action_readiness_filters_to_openclaw_without_execution(tmp_path: Path) -> None:
    model = build_runtime_cockpit_action_readiness(_vault(tmp_path), runtime_id="openclaw")

    assert model["runtime_filter"] == "openclaw"
    assert model["action_readiness"]
    assert {item["runtime_id"] for item in model["action_readiness"]} == {"openclaw"}
    assert model["summary"]["runtime_execution_allowed"] is False
    assert model["summary"]["host_mutation_allowed"] is False
    assert model["summary"]["agent_bus_task_writes_allowed"] is False
    assert model["summary"]["provider_calls_allowed"] is False


def test_runtime_cockpit_action_request_queues_approval_only(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    model = build_runtime_cockpit_action_readiness(vault)
    requestable = model["requestable_actions"]
    if not requestable:
        pytest.skip("fixture/runtime settings expose no requestable startup surfaces")

    resp = queue_runtime_cockpit_action_request(
        vault,
        action_id=requestable[0]["action_id"],
        note="test request",
        requested_by="codex-test",
    )

    assert resp["ok"] is True
    assert resp["requires_approval"] is True
    assert resp["boundary"]["direct_runtime_execution_allowed"] is False
    assert not (vault / resp["target_path"]).exists()
    approvals = list((vault / StudioService.APPROVAL_DIR).glob("*.json"))
    assert len(approvals) == 1
    approval_payload = json.loads(approvals[0].read_text(encoding="utf-8"))
    assert approval_payload["status"] == "pending"
    assert approval_payload["action_spec"]["action_type"] == "create_file"
    assert approval_payload["action_spec"]["metadata"]["approval_packet_only"] is True
    assert approval_payload["action_spec"]["metadata"]["executes_runtime_action"] is False
    assert approval_payload["action_spec"]["metadata"]["writes_agent_bus_task"] is False


def test_runtime_cockpit_blocked_action_cannot_queue_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    model = build_runtime_cockpit_action_readiness(vault)
    blocked = next(item for item in model["action_readiness"] if item["approval_packet_requestable"] is False)

    with pytest.raises(RuntimeCockpitActionReadinessError):
        queue_runtime_cockpit_action_request(vault, action_id=blocked["action_id"])

    assert not (vault / StudioService.APPROVAL_DIR).exists()
