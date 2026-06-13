from __future__ import annotations

import json
import shutil
from pathlib import Path

from runtime.subagents.cli_surfaces import (
    build_subagent_agent_bus_task_packet_preview,
    build_subagent_approval_consumption_decision_binding,
    build_subagent_approval_consumption_dry_run,
    build_subagent_approval_consumption_exact_once_marker_contract,
    build_subagent_approval_packet_preview,
    build_subagent_approval_review_decision,
    build_subagent_approval_request,
    build_subagent_list,
    build_subagent_route_preview,
    build_subagent_show,
    build_subagent_validation,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _minimal_subagent_vault(tmp_path: Path) -> Path:
    preset_source = VAULT_ROOT / "subagents" / "presets" / "site-ops" / "site-ops-worker.md"
    preset_target = tmp_path / "subagents" / "presets" / "site-ops" / "site-ops-worker.md"
    preset_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(preset_source, preset_target)
    return tmp_path


def _test_availability() -> dict[str, dict[str, object]]:
    return {
        "OpenClaw": {"registered": True, "retired": False},
        "Hermes": {"registered": True, "retired": False},
        "OpenHuman": {"registered": False, "retired": True},
    }


def _write_pending_approval_request(vault: Path, *, task_id: str = "siteops-task-123") -> tuple[dict, dict]:
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id=task_id,
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id=task_id,
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    return preview, written


def _write_approval_decision(
    vault: Path,
    approval_artifact_path: str,
    work_fingerprint: str,
    *,
    decision: str = "approved",
) -> dict:
    return build_subagent_approval_review_decision(
        approval_artifact_path,
        decision=decision,
        reviewer_id="operator-test",
        reason="Recorded by a focused unit test.",
        expected_work_fingerprint=work_fingerprint,
        write_approval_decision=True,
        vault_root=vault,
        availability=_test_availability(),
    )


def _write_consumption_marker(
    vault: Path,
    approval_artifact_path: str,
    decision_artifact_path: str,
    work_fingerprint: str,
) -> dict:
    return build_subagent_approval_consumption_exact_once_marker_contract(
        approval_artifact_path,
        decision_artifact_path,
        expected_work_fingerprint=work_fingerprint,
        write_consumption_marker=True,
        consumed_by="operator-test",
        vault_root=vault,
        availability=_test_availability(),
    )


def test_subagent_list_surface_is_read_only() -> None:
    payload = build_subagent_list(VAULT_ROOT)

    assert payload["ok"] is True
    assert payload["preset_count"] >= 9
    assert payload["writes_performed"] is False
    assert payload["authority_flags"]["agent_bus_enqueue_allowed"] is False


def test_subagent_validation_surface_reads_capabilities_without_writes() -> None:
    payload = build_subagent_validation(VAULT_ROOT)

    assert payload["ok"] is True
    assert payload["error_count"] == 0
    assert payload["runtime_availability"]["OpenHuman"]["registered"] is False
    assert payload["runtime_availability"]["OpenClaw"]["registered"] is True


def test_subagent_show_surface_returns_preset_contract() -> None:
    payload = build_subagent_show("qa-testing-worker", VAULT_ROOT)

    assert payload["ok"] is True
    assert payload["summary"]["id"] == "qa-testing-worker"
    assert "Tests Run" in payload["summary"]["required_sections"]
    assert payload["authority_flags"]["runtime_dispatch_allowed"] is False


def test_subagent_route_preview_builds_task_scoped_activation_without_dispatch() -> None:
    payload = build_subagent_route_preview(
        "site-ops-worker",
        mode="site_ops",
        task_id="task-preview",
        objective="Preview site-ops worker route.",
        vault_root=VAULT_ROOT,
    )

    assert payload["ok"] is True
    assert payload["route"]["selected_runtime"] == "OpenClaw"
    assert payload["activation_context_preview"]["state"] == "activated"
    assert payload["activation_context_preview"]["daemon_started"] is False
    assert payload["activation_context_preview"]["is_task_scoped"] is True
    assert payload["authority_flags"]["agent_bus_enqueue_allowed"] is False


def test_subagent_route_preview_rejects_unsupported_mode() -> None:
    payload = build_subagent_route_preview(
        "site-ops-worker",
        mode="workspace",
        vault_root=VAULT_ROOT,
    )

    assert payload["ok"] is False
    assert payload["status"] == "mode_invalid"
    assert "does not support mode" in payload["errors"][0]


def test_subagent_approval_preview_builds_stable_non_writing_packet() -> None:
    payload = build_subagent_approval_packet_preview(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Review one site profile without external actions.",
        requested_by="codex-test",
        vault_root=VAULT_ROOT,
    )
    second = build_subagent_approval_packet_preview(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Review one site profile without external actions.",
        requested_by="codex-test",
        vault_root=VAULT_ROOT,
    )

    assert payload["ok"] is True
    assert payload["status"] == "ready_for_operator_decision"
    assert payload["approval_packet_id"].startswith("subagent-activation-appr-")
    assert payload["work_fingerprint"] == second["work_fingerprint"]
    assert payload["approval_packet_id"] == second["approval_packet_id"]
    assert payload["approval_request_created"] is False
    assert payload["approval_artifact_written"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_consumed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["daemon_started"] is False
    assert payload["runtime_dispatched"] is False
    assert payload["route"]["selected_runtime"] == "OpenClaw"
    assert payload["activation_context_preview"]["daemon_started"] is False
    assert payload["authority_flags"]["approval_artifact_write_allowed"] is False
    assert payload["authority_flags"]["approval_consumption_allowed"] is False
    assert payload["authority_flags"]["agent_bus_enqueue_allowed"] is False
    assert "operator_approval_statement" in payload["future_approval_requirements"][0]
    assert "approval_grant" in payload["blocked_effects"]


def test_subagent_approval_preview_requires_mode_for_decision() -> None:
    payload = build_subagent_approval_packet_preview(
        "site-ops-worker",
        task_id="siteops-task-123",
        vault_root=VAULT_ROOT,
    )

    assert payload["ok"] is False
    assert payload["status"] == "blocked"
    assert payload["ready_for_operator_decision"] is False
    assert "mode_required_for_activation_approval" in payload["blockers"]
    assert payload["activation_context_preview"] is None
    assert payload["writes_performed"] is False


def test_subagent_approval_preview_rejects_unsupported_mode_without_consuming_approval() -> None:
    payload = build_subagent_approval_packet_preview(
        "site-ops-worker",
        mode="workspace",
        task_id="siteops-task-123",
        vault_root=VAULT_ROOT,
    )

    assert payload["ok"] is False
    assert payload["status"] == "blocked"
    assert "mode_invalid" in payload["blockers"]
    assert "does not support mode" in payload["errors"][0]
    assert payload["approval_consumed"] is False
    assert payload["agent_bus_task_written"] is False


def test_subagent_approval_request_preview_does_not_write_artifact() -> None:
    payload = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=VAULT_ROOT,
    )

    assert payload["ok"] is True
    assert payload["status"] == "ready_for_operator_decision"
    assert payload["approval_request_written"] is False
    assert payload["approval_artifact_written"] is False
    assert payload["writes_performed"] is False
    assert payload["approval_artifact_path"].endswith(f'{payload["approval_packet_id"]}.json')
    assert payload["approval_artifact_preview"]["status"] == "pending_operator_decision"
    assert payload["approval_artifact_preview"]["approval_granted"] is False
    assert payload["approval_artifact_preview"]["approval_consumed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["runtime_dispatched"] is False
    assert "No Agent Bus task creation." in payload["operator_confirmation_text"]


def test_subagent_approval_request_write_requires_exact_fingerprint(tmp_path: Path) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    artifact_path = vault / written["approval_artifact_path"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert written["ok"] is True
    assert written["status"] == "approval_request_written"
    assert written["approval_request_written"] is True
    assert written["work_fingerprint_matched"] is True
    assert written["approval_consumed"] is False
    assert written["agent_bus_task_written"] is False
    assert artifact_path.exists()
    assert artifact["status"] == "pending_operator_decision"
    assert artifact["work_fingerprint"] == preview["work_fingerprint"]
    assert artifact["approval_granted"] is False
    assert artifact["agent_bus_task_written"] is False


def test_subagent_approval_request_refuses_fingerprint_mismatch(tmp_path: Path) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    payload = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint="not-the-preview-fingerprint",
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    assert payload["ok"] is False
    assert "expected_work_fingerprint_mismatch" in payload["blockers"]
    assert payload["approval_request_written"] is False
    assert not (vault / payload["approval_artifact_path"]).exists()


def test_subagent_approval_request_refuses_duplicate_artifact(tmp_path: Path) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    first = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    duplicate = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    assert first["approval_request_written"] is True
    assert duplicate["ok"] is False
    assert duplicate["approval_request_written"] is False
    assert "approval_artifact_already_exists_no_overwrite" in duplicate["blockers"]


def test_subagent_approval_consumption_dry_run_validates_pending_artifact_without_consuming(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    dry_run = build_subagent_approval_consumption_dry_run(
        written["approval_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
        availability=_test_availability(),
    )

    assert dry_run["ok"] is True
    assert dry_run["status"] == "blocked_pending_operator_decision"
    assert dry_run["approval_artifact_loaded"] is True
    assert dry_run["work_fingerprint"] == preview["work_fingerprint"]
    assert dry_run["work_fingerprint_matched"] is True
    assert dry_run["current_work_fingerprint"] == preview["work_fingerprint"]
    assert dry_run["approval_consumption_ready"] is False
    assert dry_run["approval_consumed"] is False
    assert dry_run["approval_consumption_marker_written"] is False
    assert dry_run["agent_bus_task_written"] is False
    assert dry_run["runtime_dispatched"] is False
    assert dry_run["checks"]["current_route_matches_artifact"] is True
    assert dry_run["checks"]["future_consumption_marker_absent"] is True
    assert "operator_approval_decision_required" in dry_run["blockers"]
    assert not (vault / dry_run["future_consumption_marker_path"]).exists()


def test_subagent_approval_consumption_dry_run_refuses_missing_artifact(tmp_path: Path) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    dry_run = build_subagent_approval_consumption_dry_run(
        "07_LOGS/Agent-Activity/_subagent_activation_approvals/missing.json",
        vault_root=vault,
        availability=_test_availability(),
    )

    assert dry_run["ok"] is False
    assert dry_run["approval_artifact_loaded"] is False
    assert "approval_artifact_missing" in dry_run["blockers"]
    assert dry_run["approval_consumed"] is False
    assert dry_run["agent_bus_task_written"] is False


def test_subagent_approval_consumption_dry_run_refuses_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    dry_run = build_subagent_approval_consumption_dry_run(
        written["approval_artifact_path"],
        expected_work_fingerprint="not-the-preview-fingerprint",
        vault_root=vault,
        availability=_test_availability(),
    )

    assert dry_run["ok"] is False
    assert dry_run["work_fingerprint_matched"] is False
    assert "expected_work_fingerprint_mismatch" in dry_run["blockers"]
    assert dry_run["approval_consumed"] is False
    assert dry_run["runtime_dispatched"] is False


def test_subagent_approval_review_decision_preview_does_not_write(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    decision = build_subagent_approval_review_decision(
        written["approval_artifact_path"],
        decision="approve",
        reviewer_id="operator-test",
        vault_root=vault,
        availability=_test_availability(),
    )

    assert decision["ok"] is True
    assert decision["status"] == "ready_to_write_approval_decision_approved_no_execution"
    assert decision["decision_record_writable"] is True
    assert decision["approval_decision_written"] is False
    assert decision["writes_performed"] is False
    assert decision["approval_consumed"] is False
    assert decision["agent_bus_task_written"] is False
    assert decision["runtime_dispatched"] is False
    assert decision["checks"]["current_route_matches_artifact"] is True
    assert not (vault / decision["decision_artifact_path"]).exists()


def test_subagent_approval_review_decision_write_requires_exact_fingerprint(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    decision = build_subagent_approval_review_decision(
        written["approval_artifact_path"],
        decision="approved",
        reviewer_id="operator-test",
        reason="Approved in test for one future sub-agent activation.",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_decision=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    decision_path = vault / decision["decision_artifact_path"]
    decision_artifact = json.loads(decision_path.read_text(encoding="utf-8"))
    request_artifact = json.loads((vault / written["approval_artifact_path"]).read_text(encoding="utf-8"))

    assert decision["ok"] is True
    assert decision["status"] == "approval_decision_written_approved_no_execution"
    assert decision["approval_decision_written"] is True
    assert decision["work_fingerprint_matched"] is True
    assert decision["approval_consumed"] is False
    assert decision["agent_bus_task_written"] is False
    assert decision_path.exists()
    assert decision_artifact["operator_decision"] == "approved"
    assert decision_artifact["approval_decision_written"] is True
    assert decision_artifact["approval_consumed"] is False
    assert decision_artifact["agent_bus_task_written"] is False
    assert request_artifact["status"] == "pending_operator_decision"
    assert request_artifact["approval_consumed"] is False


def test_subagent_approval_review_decision_refuses_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    decision = build_subagent_approval_review_decision(
        written["approval_artifact_path"],
        decision="approve",
        expected_work_fingerprint="not-the-preview-fingerprint",
        write_approval_decision=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    assert decision["ok"] is False
    assert decision["approval_decision_written"] is False
    assert "expected_work_fingerprint_mismatch" in decision["blockers"]
    assert not (vault / decision["decision_artifact_path"]).exists()


def test_subagent_approval_review_decision_refuses_duplicate_decision_artifact(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    written = build_subagent_approval_request(
        "site-ops-worker",
        mode="site_ops",
        task_id="siteops-task-123",
        objective="Prepare a governed approval request.",
        requested_by="codex-test",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_request=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    first = build_subagent_approval_review_decision(
        written["approval_artifact_path"],
        decision="approve",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_decision=True,
        vault_root=vault,
        availability=_test_availability(),
    )
    duplicate = build_subagent_approval_review_decision(
        written["approval_artifact_path"],
        decision="approve",
        expected_work_fingerprint=preview["work_fingerprint"],
        write_approval_decision=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    assert first["approval_decision_written"] is True
    assert duplicate["ok"] is False
    assert duplicate["approval_decision_written"] is False
    assert "approval_decision_artifact_already_exists_no_overwrite" in duplicate["blockers"]


def test_subagent_approval_consumption_decision_binding_accepts_approved_decision_without_writes(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )

    binding = build_subagent_approval_consumption_decision_binding(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
        availability=_test_availability(),
    )

    assert decision["approval_decision_written"] is True
    assert binding["ok"] is True
    assert binding["status"] == "approval_consumption_decision_binding_ready_no_execution"
    assert binding["approval_decision_accepted"] is True
    assert binding["approval_consumption_preflight_ready"] is True
    assert binding["approval_consumption_ready_for_future_executor"] is True
    assert binding["approval_consumption_ready"] is False
    assert binding["approval_granted"] is False
    assert binding["approval_consumed"] is False
    assert binding["decision_consumed"] is False
    assert binding["approval_consumption_marker_written"] is False
    assert binding["agent_bus_task_written"] is False
    assert binding["daemon_started"] is False
    assert binding["runtime_dispatched"] is False
    assert binding["writes_performed"] is False
    assert binding["future_consumption_marker_exists"] is False
    assert not (vault / binding["future_consumption_marker_path"]).exists()
    assert binding["blockers"] == []


def test_subagent_approval_consumption_decision_binding_blocks_denied_decision(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="denied",
    )

    binding = build_subagent_approval_consumption_decision_binding(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
        availability=_test_availability(),
    )

    assert decision["approval_decision_written"] is True
    assert binding["ok"] is False
    assert binding["status"] == "blocked_approval_decision_denied"
    assert binding["operator_decision"] == "denied"
    assert binding["approval_decision_accepted"] is False
    assert binding["approval_consumption_ready_for_future_executor"] is False
    assert binding["approval_consumed"] is False
    assert binding["decision_consumed"] is False
    assert "approval_decision_denied" in binding["blockers"]


def test_subagent_approval_consumption_decision_binding_refuses_mismatched_decision(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    first_preview, first_written = _write_pending_approval_request(vault, task_id="siteops-task-123")
    second_preview, second_written = _write_pending_approval_request(vault, task_id="siteops-task-456")
    second_decision = _write_approval_decision(
        vault,
        second_written["approval_artifact_path"],
        second_preview["work_fingerprint"],
        decision="approved",
    )

    binding = build_subagent_approval_consumption_decision_binding(
        first_written["approval_artifact_path"],
        second_decision["decision_artifact_path"],
        expected_work_fingerprint=first_preview["work_fingerprint"],
        vault_root=vault,
        availability=_test_availability(),
    )

    assert binding["ok"] is False
    assert binding["approval_decision_accepted"] is False
    assert "approval_decision_artifact_path_mismatch" in binding["blockers"]
    assert "approval_decision_packet_id_mismatch" in binding["blockers"]
    assert "approval_decision_work_fingerprint_mismatch" in binding["blockers"]


def test_subagent_approval_consumption_decision_binding_refuses_missing_decision(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)

    binding = build_subagent_approval_consumption_decision_binding(
        written["approval_artifact_path"],
        "07_LOGS/Agent-Activity/_subagent_activation_approvals/_decisions/missing.json",
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
        availability=_test_availability(),
    )

    assert binding["ok"] is False
    assert binding["decision_artifact_loaded"] is False
    assert binding["approval_consumption_ready_for_future_executor"] is False
    assert "approval_decision_artifact_missing" in binding["blockers"]


def test_subagent_approval_consumption_exact_once_marker_preview_does_not_write(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )

    marker = build_subagent_approval_consumption_exact_once_marker_contract(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
        availability=_test_availability(),
    )

    assert marker["ok"] is True
    assert marker["status"] == "ready_to_write_approval_consumption_marker_no_execution"
    assert marker["marker_record_writable"] is True
    assert marker["approval_consumption_marker_written"] is False
    assert marker["writes_performed"] is False
    assert marker["approval_consumed"] is False
    assert marker["decision_consumed"] is False
    assert marker["agent_bus_task_written"] is False
    assert marker["runtime_dispatched"] is False
    assert not (vault / marker["consumption_marker_path"]).exists()


def test_subagent_approval_consumption_exact_once_marker_write_requires_exact_fingerprint(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )

    marker = build_subagent_approval_consumption_exact_once_marker_contract(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        write_consumption_marker=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    assert marker["ok"] is False
    assert marker["approval_consumption_marker_written"] is False
    assert "expected_work_fingerprint_required_for_marker_write" in marker["blockers"]
    assert not (vault / marker["consumption_marker_path"]).exists()


def test_subagent_approval_consumption_exact_once_marker_writes_create_only_marker(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )

    marker = build_subagent_approval_consumption_exact_once_marker_contract(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        write_consumption_marker=True,
        consumed_by="operator-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    duplicate = build_subagent_approval_consumption_exact_once_marker_contract(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        write_consumption_marker=True,
        consumed_by="operator-test",
        vault_root=vault,
        availability=_test_availability(),
    )
    request_artifact = json.loads((vault / written["approval_artifact_path"]).read_text())
    decision_artifact = json.loads((vault / decision["decision_artifact_path"]).read_text())
    marker_artifact = json.loads((vault / marker["consumption_marker_path"]).read_text())

    assert marker["ok"] is True
    assert marker["status"] == "approval_consumption_marker_written_no_execution"
    assert marker["approval_consumption_marker_written"] is True
    assert marker["approval_consumption_marker_reserved"] is True
    assert marker["writes_performed"] is True
    assert marker["approval_consumed"] is False
    assert marker["decision_consumed"] is False
    assert marker["agent_bus_task_written"] is False
    assert marker["runtime_dispatched"] is False
    assert marker_artifact["marker_status"] == "recorded"
    assert marker_artifact["approval_packet_id"] == written["approval_packet_id"]
    assert marker_artifact["work_fingerprint"] == preview["work_fingerprint"]
    assert marker_artifact["consumption_policy"] == "exact_once"
    assert marker_artifact["marker_write_mode"] == "exclusive_create"
    assert request_artifact["approval_consumed"] is False
    assert decision_artifact["decision_consumed"] is False
    assert duplicate["ok"] is False
    assert duplicate["approval_consumption_marker_written"] is False
    assert "approval_consumption_marker_already_exists" in duplicate["blockers"]


def test_subagent_approval_consumption_exact_once_marker_blocks_denied_decision(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="denied",
    )

    marker = build_subagent_approval_consumption_exact_once_marker_contract(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        write_consumption_marker=True,
        vault_root=vault,
        availability=_test_availability(),
    )

    assert marker["ok"] is False
    assert marker["approval_consumption_marker_written"] is False
    assert "approval_decision_denied" in marker["blockers"]
    assert not (vault / marker["consumption_marker_path"]).exists()


def test_subagent_agent_bus_task_packet_preview_requires_recorded_marker(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )

    packet = build_subagent_agent_bus_task_packet_preview(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
    )

    assert packet["ok"] is False
    assert packet["agent_bus_task_preview_ready"] is False
    assert packet["agent_bus_task_packet_preview"] is None
    assert packet["agent_bus_task_written"] is False
    assert packet["runtime_dispatched"] is False
    assert "approval_consumption_marker_missing" in packet["blockers"]
    assert not (vault / "runtime" / "agent_bus" / "agent_bus.sqlite").exists()


def test_subagent_agent_bus_task_packet_preview_builds_inert_packet_after_marker(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )
    marker = _write_consumption_marker(
        vault,
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        preview["work_fingerprint"],
    )

    packet = build_subagent_agent_bus_task_packet_preview(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        consumption_marker_path=marker["consumption_marker_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
    )
    task_packet = packet["agent_bus_task_packet_preview"]

    assert packet["ok"] is True
    assert packet["status"] == "agent_bus_task_packet_preview_ready_no_enqueue"
    assert packet["agent_bus_task_preview_ready"] is True
    assert packet["agent_bus_task_written"] is False
    assert packet["agent_bus_enqueue_performed"] is False
    assert packet["daemon_started"] is False
    assert packet["runtime_dispatched"] is False
    assert packet["authority_flags"]["agent_bus_task_preview_allowed"] is True
    assert packet["authority_flags"]["agent_bus_enqueue_allowed"] is False
    assert task_packet["from"] == "Operator"
    assert task_packet["to"] == "OpenClaw"
    assert task_packet["intent"] == "TASK"
    assert task_packet["status"] == "open"
    assert task_packet["work_fingerprint"] == preview["work_fingerprint"]
    assert task_packet["execution_constraints"] == {
        "allow_shell_commands": False,
        "allow_live_subprocess": False,
        "allowed_write_paths": [],
        "write_policy": "none",
    }
    assert written["approval_artifact_path"] in task_packet["artifacts"]
    assert decision["decision_artifact_path"] in task_packet["artifacts"]
    assert marker["consumption_marker_path"] in task_packet["artifacts"]
    assert packet["agent_bus_task_packet_digest_sha256"]
    assert not (vault / "runtime" / "agent_bus" / "agent_bus.sqlite").exists()


def test_subagent_agent_bus_task_packet_preview_blocks_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )
    marker = _write_consumption_marker(
        vault,
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        preview["work_fingerprint"],
    )

    packet = build_subagent_agent_bus_task_packet_preview(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        consumption_marker_path=marker["consumption_marker_path"],
        expected_work_fingerprint="wrong",
        vault_root=vault,
    )

    assert packet["ok"] is False
    assert packet["agent_bus_task_packet_preview"] is None
    assert packet["agent_bus_task_written"] is False
    assert "expected_work_fingerprint_mismatch" in packet["blockers"]


def test_subagent_agent_bus_task_packet_preview_blocks_tampered_marker(
    tmp_path: Path,
) -> None:
    vault = _minimal_subagent_vault(tmp_path)
    preview, written = _write_pending_approval_request(vault)
    decision = _write_approval_decision(
        vault,
        written["approval_artifact_path"],
        preview["work_fingerprint"],
        decision="approved",
    )
    marker = _write_consumption_marker(
        vault,
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        preview["work_fingerprint"],
    )
    marker_path = vault / marker["consumption_marker_path"]
    marker_artifact = json.loads(marker_path.read_text())
    marker_artifact["work_fingerprint"] = "tampered"
    marker_path.write_text(json.dumps(marker_artifact, indent=2) + "\n")

    packet = build_subagent_agent_bus_task_packet_preview(
        written["approval_artifact_path"],
        decision["decision_artifact_path"],
        consumption_marker_path=marker["consumption_marker_path"],
        expected_work_fingerprint=preview["work_fingerprint"],
        vault_root=vault,
    )

    assert packet["ok"] is False
    assert packet["agent_bus_task_packet_preview"] is None
    assert packet["agent_bus_task_written"] is False
    assert "approval_consumption_marker_work_fingerprint_mismatch" in packet["blockers"]
    assert "approval_consumption_marker_digest_mismatch" in packet["blockers"]
