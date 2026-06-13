"""Tests for read-only Browser Runtime completion status."""

from __future__ import annotations

import inspect
import io
import json
import os
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.completion_status as completion_module
from runtime.browser_runtime.completion_status import (
    BROWSER_RUNTIME_OVERALL_COMPLETE,
    BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED,
    build_browser_runtime_completion_status,
    main as completion_main,
)

_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_completion_status"


def _workspace_test_root(name: str) -> Path:
    root = _TMP_ROOT / name
    if root.exists():
        _remove_test_root(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _remove_test_root(root: Path) -> None:
    resolved = root.resolve()
    if resolved.parent != _TMP_ROOT.resolve():
        raise AssertionError(f"refusing to remove unexpected path: {resolved}")
    shutil.rmtree(resolved, ignore_errors=True)
    try:
        _TMP_ROOT.rmdir()
    except OSError:
        pass


def _write(path: Path, content: str = "evidence") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _safe_run_record(run_id: str) -> dict[str, object]:
    return {
        "record_type": "browser_run_log",
        "run_id": run_id,
        "status": "succeeded",
        "server": {
            "bind_host": "127.0.0.1",
            "public_tunnel": False,
        },
        "governance": {
            "canonical_writeback": False,
            "skill_activation": False,
            "trusted_skill_write": False,
            "siteops_skill_card_write": False,
            "real_profile_allowed": False,
            "real_profile_used": False,
            "credentials_allowed": False,
            "credentials_used": False,
            "cookies_exported": False,
            "browser_history_imported": False,
            "cdp_connection_used": False,
            "browser_harness_used": False,
            "browser_use_cli_used": False,
            "public_tunnel_used": False,
            "agent_bus_enqueue": False,
            "provider_call": False,
            "gate_policy_mutation": False,
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_bounded_mvp_evidence(root: Path, *, unsafe: bool = False) -> None:
    for relative in (
        "runtime/browser_runtime/models.py",
        "runtime/browser_runtime/adapter.py",
        "runtime/browser_runtime/adapters/browser_use_cli.py",
        "runtime/browser_runtime/test_targets/vincisos_shadow.html",
        "runtime/browser_runtime/artifacts.py",
        "06_AGENTS/Browser-Skills/_drafts/draft-vincisos-inapp-browser-20260430.md",
        "06_AGENTS/Browser-Skills/_drafts/replay-vincisos-draft-skill-20260501.md",
    ):
        _write(root / relative)
    (root / "07_LOGS" / "Browser-Runs").mkdir(parents=True, exist_ok=True)
    (root / "07_LOGS" / "Agent-Activity").mkdir(parents=True, exist_ok=True)

    for relative in (
        "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_screenshot.png",
        "07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_screenshot.png",
        "07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_screenshot.png",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"png-bytes")

    for relative in (
        "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json",
        "07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_success.json",
        "07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_success.json",
        "07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_success.json",
    ):
        record = _safe_run_record(Path(relative).stem)
        if unsafe and relative.endswith("vincisos_inapp_browser_20260430_success.json"):
            governance = record["governance"]
            assert isinstance(governance, dict)
            governance["real_profile_used"] = True
        _write_json(root / relative, record)


def _seed_cdp_activation_evidence(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/cdp_live.py",
        "runtime/browser_runtime/cdp_executor_spec.py",
        "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-bounded-live-executor-implementation.md",
    ):
        _write(root / relative)
    _write(
        root / "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-operational-environment-activation.md",
        "\n".join(
            [
                "status: implemented_cdp_read_only_proof_complete",
                "approval_consumed: True",
                "idempotency_marker_written: True",
                "browser_launch_attempted: True",
                "cdp_connection_attempted: True",
                "used isolated throwaway browser profile",
                "no canonical writeback",
            ]
        ),
    )


def _seed_browser_use_cli_validation_preflight(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/browser_use_cli_validation.py",
        "runtime/browser_runtime/test_browser_use_cli_validation.py",
    ):
        _write(root / relative)


def _seed_browser_use_cli_live_unavailable_evidence(root: Path, *, unsafe: bool = False) -> None:
    record = {
        "run_id": "browser_use_cli_live_validation_20260502_blocked_unavailable",
        "status": "blocked_browser_use_cli_unavailable",
        "executable": "browser-use",
        "executable_found": False,
        "executable_path": None,
        "wrapper_present": True,
        "config_present": True,
        "config_policy_ok": True,
        "ready_for_future_live_validation": False,
        "blockers": ["browser_use_cli_executable_not_found"],
        "dependency_install_attempted": False,
        "subprocess_probe_attempted": False,
        "browser_launch_attempted": False,
        "browser_use_cli_live_run_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "public_tunnel_attempted": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        record["browser_use_cli_live_run_attempted"] = True
    _write_json(
        root / "07_LOGS/Browser-Runs/browser_use_cli_live_validation_20260502_blocked_unavailable.json",
        record,
    )


def _seed_browser_use_cli_safe_url_run(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/browser_use_cli_safe_url_validation_run.py",
        "runtime/browser_runtime/test_browser_use_cli_safe_url_validation_run.py",
    ):
        _write(root / relative)
    _write_json(
        root / "07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-run-20260505.json",
        {
            "status": "browser_use_cli_safe_url_validation_run_complete",
            "target_url": "http://127.0.0.1:8770/",
            "browser_use_cli_open_attempted": True,
            "browser_use_cli_exit_code": 0,
            "browser_use_open_succeeded": True,
            "browser_use_cli_close_attempted": True,
            "browser_use_cli_close_exit_code": 0,
            "browser_use_close_succeeded": True,
            "browser_dependency_install_command_run": False,
            "dependency_install_command_attempted": False,
            "real_profile_access_attempted": False,
            "credential_or_cookie_read_attempted": False,
            "cookie_export_attempted": False,
            "public_tunnel_attempted": False,
            "cloud_api_call_attempted": False,
            "llm_or_provider_call_attempted": False,
            "agent_bus_enqueue_attempted": False,
            "gate_mutation_attempted": False,
            "canonical_writeback_attempted": False,
        },
    )


def _seed_vincisos_product_ui_target_probe(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/vincisos_product_ui_target_probe.py",
        "runtime/browser_runtime/test_browser_runtime.py",
    ):
        _write(root / relative)


def _seed_vincisos_product_ui_launch_readiness(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/vincisos_product_ui_launch_readiness.py",
        "runtime/browser_runtime/test_browser_runtime.py",
    ):
        _write(root / relative)


def _seed_vincisos_product_ui_browser_proof(root: Path, *, unsafe: bool = False) -> None:
    record = _safe_run_record("vincisos_product_ui_browser_proof_20260502_success")
    record.update(
        {
            "provider": "codex-in-app-browser",
            "provider_backend": "iab",
            "url": "http://127.0.0.1:8770/",
            "browser_state": {
                "post_action_status": "Panel inspected in safe mode.",
                "selector_counts": {
                    "root": 1,
                    "safe_mode_banner": 1,
                    "panel_overview": 1,
                    "panel_approvals": 1,
                    "panel_workflow": 1,
                    "tab_overview": 1,
                    "tab_approvals": 1,
                    "tab_workflow": 1,
                    "task_table": 1,
                    "approval_table": 1,
                    "action_status": 1,
                    "harmless_action": 1,
                    "task_rows": 3,
                    "approval_rows": 2,
                },
            },
        }
    )
    if unsafe:
        governance = record["governance"]
        assert isinstance(governance, dict)
        governance["cookies_exported"] = True
    _write_json(
        root / "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json",
        record,
    )
    screenshot = root / "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    screenshot.write_bytes(b"png-bytes")
    for relative in (
        "07_LOGS/Agent-Activity/2026-05-02-codex-vincisos-product-ui-browser-proof.md",
        "06_AGENTS/Browser-Skills/_drafts/draft-vincisos-product-ui-browser-proof-20260502.md",
        "03_INPUTS/Browser-Skill-Candidates/127-0-0-1/20260502__candidate-vincisos-product-ui-browser-proof-20260502.md",
    ):
        _write(root / relative)


def _seed_browser_harness_adoption_decision(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/browser_harness_adoption.py",
        "runtime/browser_runtime/test_browser_harness_adoption.py",
        "06_AGENTS/Browser-Harness-Adoption-Decision.md",
    ):
        _write(root / relative)


def _seed_browser_workflow_cache_foundation(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflows.py",
        "runtime/browser_runtime/test_browser_workflow_cache.py",
        "06_AGENTS/Browser-Workflow-Cache.md",
    ):
        _write(root / relative)
    _write_json(
        root / "runtime/browser_workflows/metadata.json",
        {
            "record_type": "browser_workflow_cache_metadata",
            "schema_version": "browser.workflow_cache.v1",
            "status": "empty_initialized",
            "activation_allowed": False,
            "replay_allowed": False,
            "trusted_write_allowed": False,
            "external_code_copied": False,
            "workflows": [],
        },
    )


def _seed_workflow_replay_executor_design_preflight(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflow_replay_executor_design.py",
        "runtime/browser_runtime/test_workflow_replay_executor_design.py",
        "06_AGENTS/Browser-Workflow-Replay-Executor-Design.md",
    ):
        _write(root / relative)


def _seed_workflow_replay_executor_implementation_request(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflow_replay_executor_request.py",
        "runtime/browser_runtime/test_workflow_replay_executor_request.py",
        "06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Request.md",
    ):
        _write(root / relative)


def _seed_workflow_replay_executor_implementation_approval(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflow_replay_executor_approval.py",
        "runtime/browser_runtime/test_workflow_replay_executor_approval.py",
        "06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Approval.md",
    ):
        _write(root / relative)


def _seed_workflow_replay_executor_implementation(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflow_replay_executor.py",
        "runtime/browser_runtime/test_workflow_replay_executor.py",
        "06_AGENTS/Browser-Workflow-Replay-Executor.md",
    ):
        _write(root / relative)


def _seed_workflow_replay_execution_readiness_preflight(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflow_replay_execution_readiness.py",
        "runtime/browser_runtime/test_workflow_replay_execution_readiness.py",
        "06_AGENTS/Browser-Workflow-Replay-Execution-Readiness.md",
    ):
        _write(root / relative)


def _seed_workflow_replay_trial_candidate_selection(root: Path) -> None:
    workflow_id = "wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502"
    for relative in (
        "runtime/browser_runtime/workflow_replay_trial_candidate.py",
        "runtime/browser_runtime/test_workflow_replay_trial_candidate.py",
        "06_AGENTS/Browser-Workflow-Replay-Trial-Candidate.md",
    ):
        _write(root / relative)
    entry_path = root / "runtime" / "browser_workflows" / "workflows" / f"{workflow_id}.workflow.json"
    _write_json(
        entry_path,
        {
            "record_type": "browser_workflow_cache_entry",
            "schema_version": "browser.workflow_cache.v1",
            "workflow_id": workflow_id,
            "domain": "127.0.0.1",
            "intent": "VincisOS local product UI safe-panel inspection trial",
            "source_run_id": "vincisos_product_ui_browser_proof_20260502_success",
            "source_run_log_path": "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json",
            "created_at": "2026-05-02T20:17:00Z",
            "status": "reviewed_for_trial",
            "allowed_domains": ["127.0.0.1"],
            "source_url": "http://127.0.0.1:8770/",
            "steps": [
                {
                    "step_id": "step_01_open",
                    "action_type": "open",
                    "target": "http://127.0.0.1:8770/",
                    "status": "succeeded",
                    "source_action_index": 0,
                }
            ],
            "review_required": True,
            "activation_allowed": False,
            "replay_allowed": True,
            "trusted_write_allowed": False,
            "external_code_copied": False,
        },
    )
    _write_json(
        root / "runtime/browser_workflows/metadata.json",
        {
            "record_type": "browser_workflow_cache_metadata",
            "schema_version": "browser.workflow_cache.v1",
            "status": "inactive_review_cache",
            "activation_allowed": False,
            "replay_allowed": False,
            "trusted_write_allowed": False,
            "external_code_copied": False,
            "workflows": [
                {
                    "workflow_id": workflow_id,
                    "domain": "127.0.0.1",
                    "status": "reviewed_for_trial",
                    "path": f"runtime/browser_workflows/workflows/{workflow_id}.workflow.json",
                    "source_run_id": "vincisos_product_ui_browser_proof_20260502_success",
                    "activation_allowed": False,
                    "replay_allowed": True,
                    "trusted_write_allowed": False,
                    "external_code_copied": False,
                    "trial_candidate": True,
                }
            ],
        },
    )


def _seed_workflow_replay_execution_approval_idempotency(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflow_replay_execution_approval.py",
        "runtime/browser_runtime/test_workflow_replay_execution_approval.py",
        "06_AGENTS/Browser-Workflow-Replay-Execution-Approval.md",
    ):
        _write(root / relative)


def _seed_workflow_replay_execution_proof_implementation(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/workflow_replay_execution_proof.py",
        "runtime/browser_runtime/test_workflow_replay_execution_proof.py",
        "06_AGENTS/Browser-Workflow-Replay-Execution-Proof.md",
    ):
        _write(root / relative)


def _seed_workflow_replay_execution_proof_success(root: Path) -> None:
    _seed_workflow_replay_execution_proof_implementation(root)
    _write_json(
        root / "07_LOGS/Browser-Runs/safe-local-workflow-replay-execution-proof-20260503_success.json",
        {
            "record_type": "browser_workflow_replay_execution_proof",
            "schema_version": "browser.workflow_replay_execution_proof.v1",
            "status": "workflow_replay_execution_proof_complete",
            "run_id": "safe-local-workflow-replay-execution-proof-20260503",
            "workflow_id": "wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502",
            "target_url": "http://127.0.0.1:8770/",
            "allow_real_profile": False,
            "allow_credentials": False,
            "trusted_skill_write_allowed": False,
            "activation_allowed": False,
            "canonical_writeback_allowed": False,
            "external_code_copied": False,
            "workflow_use_reference_only": True,
            "browser_harness_reference_only": True,
        },
    )


def _seed_excalidraw_mcp_proof_prep(root: Path, *, unsafe: bool = False) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_mcp_proof_prep.py",
        "runtime/browser_runtime/test_excalidraw_mcp_proof_prep.py",
        "06_AGENTS/Excalidraw-Browser-MCP-Proof-Prep.md",
    ):
        _write(root / relative)
    record = {
        "record_type": "excalidraw_local_browser_mcp_proof_prep",
        "schema_version": "browser.excalidraw_mcp_proof_prep.v1",
        "status": "excalidraw_local_browser_mcp_proof_prep_ready_no_execution",
        "run_slug": "excalidraw-local-browser-mcp-proof-20260503",
        "prep_artifact_written": True,
        "live_proof_allowed_in_this_pass": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "mcp_server_invoked": False,
        "mcp_tool_call_attempted": False,
        "network_navigation_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "public_tunnel_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "workflow_use_code_copied": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        record["real_profile_access_attempted"] = True
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json",
        record,
    )


def _seed_excalidraw_mcp_live_readiness(
    root: Path,
    *,
    status: str = "blocked_excalidraw_live_readiness_missing_local_target",
    unsafe: bool = False,
) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_mcp_live_readiness.py",
        "runtime/browser_runtime/test_excalidraw_mcp_live_readiness.py",
        "06_AGENTS/Excalidraw-Browser-MCP-Live-Readiness.md",
    ):
        _write(root / relative)
    record = {
        "record_type": "excalidraw_local_browser_mcp_live_readiness",
        "schema_version": "browser.excalidraw_mcp_live_readiness.v1",
        "status": status,
        "readiness_artifact_written": True,
        "prep_evidence_ready": True,
        "browser_controller_ready": True,
        "local_target_url": "" if status == "blocked_excalidraw_live_readiness_missing_local_target" else "http://127.0.0.1:9230/",
        "local_target_host": "" if status == "blocked_excalidraw_live_readiness_missing_local_target" else "127.0.0.1",
        "blockers": (
            ["local_excalidraw_target_url_not_provided"]
            if status == "blocked_excalidraw_live_readiness_missing_local_target"
            else []
        ),
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "mcp_server_invoked": False,
        "mcp_tool_call_attempted": False,
        "network_navigation_attempted": False,
        "dependency_install_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "public_tunnel_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "workflow_use_code_copied": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        record["mcp_server_invoked"] = True
    path = (
        "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
        if status == "blocked_excalidraw_live_readiness_missing_local_target"
        else "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_ready.json"
    )
    _write_json(root / path, record)


def _seed_excalidraw_target_setup_instructions(root: Path, *, unsafe: bool = False) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_target_setup_instructions.py",
        "runtime/browser_runtime/test_excalidraw_target_setup_instructions.py",
        "06_AGENTS/Excalidraw-Local-Target-Setup-Instructions.md",
    ):
        _write(root / relative)
    record = {
        "record_type": "excalidraw_local_target_setup_instructions",
        "schema_version": "browser.excalidraw_target_setup_instructions.v1",
        "status": "excalidraw_local_target_setup_instructions_ready_no_execution",
        "setup_artifact_written": True,
        "previous_readiness_safe": True,
        "allowed_target_hosts": ["127.0.0.1", "::1", "localhost"],
        "live_proof_command_not_authorized": "No live proof command is authorized by this setup-instructions pass.",
        "dependency_install_attempted": False,
        "mcp_server_start_attempted": False,
        "mcp_tool_call_attempted": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "network_navigation_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "public_tunnel_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "workflow_use_code_copied": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        record["mcp_server_start_attempted"] = True
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json",
        record,
    )


def _seed_excalidraw_target_contract_request(root: Path, *, unsafe: bool = False) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_target_contract.py",
        "runtime/browser_runtime/test_excalidraw_target_contract.py",
        "06_AGENTS/Excalidraw-Local-Target-Contract.md",
    ):
        _write(root / relative)
    record = {
        "record_type": "excalidraw_local_target_contract",
        "schema_version": "browser.excalidraw_target_contract.v1",
        "status": "excalidraw_local_target_contract_request_ready_no_execution",
        "contract_artifact_written": True,
        "target_url": "",
        "dependency_install_attempted": False,
        "server_start_attempted": False,
        "network_probe_attempted": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "mcp_invocation_attempted": False,
        "mcp_tool_call_attempted": False,
        "target_navigation_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "public_tunnel_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "workflow_use_code_copied": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        record["network_probe_attempted"] = True
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json",
        record,
    )


def _seed_excalidraw_target_response_intake(root: Path, *, unsafe: bool = False) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_target_response.py",
        "runtime/browser_runtime/test_excalidraw_target_response.py",
        "06_AGENTS/Excalidraw-Local-Target-Response-Intake.md",
    ):
        _write(root / relative)
    record = {
        "record_type": "excalidraw_local_target_response",
        "schema_version": "browser.excalidraw_target_response.v1",
        "status": "excalidraw_local_target_response_pending_external_runtime",
        "response_artifact_written": True,
        "target_url": "",
        "dependency_install_attempted": False,
        "server_start_attempted": False,
        "network_probe_attempted": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "mcp_invocation_attempted": False,
        "mcp_tool_call_attempted": False,
        "target_navigation_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "public_tunnel_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "workflow_use_code_copied": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        record["network_probe_attempted"] = True
    _write_json(
        root / "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json",
        record,
    )


def _seed_excalidraw_target_response_resolver(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_target_response_resolver.py",
        "runtime/browser_runtime/test_excalidraw_target_response_resolver.py",
        "06_AGENTS/Excalidraw-Target-Response-Latest-Resolver.md",
    ):
        _write(root / relative)


def _seed_excalidraw_readiness_from_response(root: Path, *, unsafe: bool = False) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_readiness_from_response.py",
        "runtime/browser_runtime/test_excalidraw_readiness_from_response.py",
        "06_AGENTS/Excalidraw-Readiness-From-Target-Response.md",
    ):
        _write(root / relative)
    record = {
        "record_type": "excalidraw_readiness_from_target_response",
        "schema_version": "browser.excalidraw_readiness_from_response.v1",
        "status": "blocked_excalidraw_readiness_from_response_pending_external_runtime",
        "bridge_artifact_written": True,
        "source_response_status": "excalidraw_local_target_response_pending_external_runtime",
        "target_url": "",
        "blockers": ["excalidraw_target_response_pending_external_runtime"],
        "dependency_install_attempted": False,
        "server_start_attempted": False,
        "network_probe_attempted": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "mcp_invocation_attempted": False,
        "mcp_tool_call_attempted": False,
        "target_navigation_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "public_tunnel_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "workflow_use_code_copied": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        record["browser_launch_attempted"] = True
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json",
        record,
    )


def _seed_excalidraw_mcp_execution_approval(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_mcp_execution_approval.py",
        "runtime/browser_runtime/test_excalidraw_mcp_execution_approval.py",
        "06_AGENTS/Excalidraw-Browser-MCP-Execution-Approval.md",
    ):
        _write(root / relative)


def _seed_excalidraw_mcp_proof_execution_shell(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_mcp_proof_execution.py",
        "runtime/browser_runtime/test_excalidraw_mcp_proof_execution.py",
        "06_AGENTS/Excalidraw-Browser-MCP-Proof-Execution-Shell.md",
    ):
        _write(root / relative)


def _seed_excalidraw_live_chain_readiness(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_live_chain_readiness.py",
        "runtime/browser_runtime/test_excalidraw_live_chain_readiness.py",
        "06_AGENTS/Excalidraw-Live-Chain-Readiness.md",
    ):
        _write(root / relative)


def _seed_excalidraw_public_live_browser_proof(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/excalidraw_live_browser_proof.py",
        "runtime/browser_runtime/test_excalidraw_live_browser_proof.py",
    ):
        _write(root / relative)
    screenshot_path = "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png"
    _write(root / screenshot_path, "png")
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json",
        {
            "ok": True,
            "version": "browser.excalidraw_live_browser_proof.v1",
            "target_url": "https://excalidraw.com",
            "status": "excalidraw_live_browser_proof_complete",
            "checks": [
                {"name": "navigation_succeeded", "ok": True},
                {"name": "title_matches_excalidraw", "ok": True},
                {"name": "canvas_element_present", "ok": True},
                {"name": "screenshot_captured", "ok": True},
            ],
            "blockers": [],
            "screenshot_path": screenshot_path,
            "page_title": "Excalidraw Whiteboard",
            "canvas_found": True,
            "authority": {
                "navigates_to_excalidraw_com": True,
                "target_hardcoded": False,
                "target_registered_in_chaseos": True,
                "target_registry_id": "excalidraw",
                "env_var_required": False,
                "headless_browser_only": True,
                "no_login_profile_cookies": True,
                "no_cdp_raw_manipulation": True,
                "no_browser_use_cli": True,
                "screenshot_written_to_logs": True,
                "no_vault_markdown_writes": True,
                "no_agent_bus_writes": True,
                "no_gate_mutation": True,
                "no_canonical_mutation": True,
                "no_provider_calls": True,
            },
        },
    )


def _seed_failed_excalidraw_public_live_browser_proof(root: Path) -> None:
    failed_path = root / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-175802.json"
    _write_json(
        failed_path,
        {
            "ok": False,
            "version": "browser.excalidraw_live_browser_proof.v1",
            "target_url": "https://excalidraw.com",
            "status": "excalidraw_live_browser_proof_failed",
            "checks": [{"name": "playwright_session", "ok": False}],
            "blockers": ["playwright_error"],
            "screenshot_path": None,
            "page_title": None,
            "canvas_found": False,
            "authority": {
                "navigates_to_excalidraw_com": True,
                "target_hardcoded": True,
                "env_var_required": False,
                "headless_browser_only": True,
                "no_login_profile_cookies": True,
                "no_cdp_raw_manipulation": True,
                "no_browser_use_cli": True,
                "screenshot_written_to_logs": True,
                "no_vault_markdown_writes": True,
                "no_agent_bus_writes": True,
                "no_gate_mutation": True,
                "no_canonical_mutation": True,
                "no_provider_calls": True,
            },
        },
    )
    success_path = root / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json"
    newer_mtime = success_path.stat().st_mtime + 10
    os.utime(failed_path, (newer_mtime, newer_mtime))


def _seed_excalidraw_public_drawing_approval(root: Path) -> None:
    _seed_excalidraw_public_live_browser_proof(root)
    _write_json(
        root
        / "07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals/"
        / "excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285.json",
        {
            "record_type": "excalidraw_public_browser_drawing_proof_approval",
            "schema_version": "browser.excalidraw_public_drawing_approval.v1",
            "status": "excalidraw_public_browser_drawing_proof_approval_written_no_execution",
            "approval_id": "excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285",
            "request_digest_sha256": "97ced9c2f559a285ea43b33d487b6b03b340ba3491f72d09c4feb1e84424a628",
            "target_registry_id": "excalidraw",
            "target_url": "https://excalidraw.com",
            "approval_artifact_written": True,
            "future_single_run_approved": True,
            "execution_allowed_in_this_pass": False,
            "source_reachability_evidence_path": "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json",
            "idempotency_marker_path": "07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals/_execution_markers/excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285.json",
            "blockers": [],
            "browser_launch_attempted": False,
            "target_navigation_attempted": False,
            "drawing_action_attempted": False,
            "mcp_invocation_attempted": False,
            "mcp_tool_call_attempted": False,
            "screenshot_attempted": False,
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
            "draft_skill_written": False,
            "untrusted_candidate_written": False,
            "trusted_skill_write_attempted": False,
            "skill_activation_attempted": False,
            "real_profile_access_attempted": False,
            "credential_or_cookie_read_attempted": False,
            "cookie_export_attempted": False,
            "browser_profile_sync_attempted": False,
            "browser_history_import_attempted": False,
            "public_tunnel_attempted": False,
            "browser_harness_used": False,
            "browser_use_cli_live_used": False,
            "workflow_use_code_copied": False,
            "shell_execution_from_browser_runtime_attempted": False,
            "agent_bus_enqueue_attempted": False,
            "provider_call_attempted": False,
            "gate_mutation_attempted": False,
            "canonical_writeback_attempted": False,
        },
    )
    for relative in (
        "runtime/browser_runtime/excalidraw_public_drawing_approval.py",
        "runtime/browser_runtime/test_excalidraw_public_drawing_approval.py",
        "06_AGENTS/Excalidraw-Public-Browser-Drawing-Proof-Approval.md",
    ):
        _write(root / relative)


def _seed_excalidraw_public_drawing_proof(root: Path) -> None:
    _seed_excalidraw_public_drawing_approval(root)
    for relative in (
        "runtime/browser_runtime/excalidraw_public_drawing_proof.py",
        "runtime/browser_runtime/test_excalidraw_public_drawing_proof.py",
        "06_AGENTS/Excalidraw-Public-Browser-Drawing-Proof-Run.md",
    ):
        _write(root / relative)
    screenshot_path = "07_LOGS/Browser-Runs/excalidraw_public_drawing_proof_20260505-191010.png"
    evidence_path = "07_LOGS/Browser-Runs/excalidraw_public_drawing_proof_20260505-191010.json"
    activity_path = "07_LOGS/Agent-Activity/_excalidraw_public_drawing_runs/excalidraw_public_drawing_proof_20260505-191010.json"
    marker_path = "07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals/_execution_markers/excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285.json"
    _write(root / screenshot_path, "png")
    _write_json(
        root / activity_path,
        {
            "record_type": "excalidraw_public_browser_drawing_proof_agent_activity_evidence",
            "schema_version": "browser.excalidraw_public_drawing_proof.v1",
            "run_slug": "20260505-191010",
            "approval_id": "excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285",
            "request_digest_sha256": "97ced9c2f559a285ea43b33d487b6b03b340ba3491f72d09c4feb1e84424a628",
            "status": "excalidraw_public_browser_drawing_proof_complete",
            "ok": True,
        },
    )
    _write_json(
        root / marker_path,
        {
            "record_type": "excalidraw_public_browser_drawing_proof_marker",
            "schema_version": "browser.excalidraw_public_drawing_proof.v1",
            "approval_id": "excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285",
            "request_digest_sha256": "97ced9c2f559a285ea43b33d487b6b03b340ba3491f72d09c4feb1e84424a628",
            "run_slug": "20260505-191010",
            "status": "completed",
            "evidence_json_path": evidence_path,
            "screenshot_path": screenshot_path,
        },
    )
    _write_json(
        root / evidence_path,
        {
            "ok": True,
            "record_type": "excalidraw_public_browser_drawing_proof_run",
            "schema_version": "browser.excalidraw_public_drawing_proof.v1",
            "status": "excalidraw_public_browser_drawing_proof_complete",
            "approval_id": "excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285",
            "request_digest_sha256": "97ced9c2f559a285ea43b33d487b6b03b340ba3491f72d09c4feb1e84424a628",
            "source_reachability_evidence_path": "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json",
            "idempotency_marker_path": marker_path,
            "target_registry_id": "excalidraw",
            "target_url": "https://excalidraw.com",
            "drawing_label": "ChaseOS proof",
            "checks": [
                {"name": "approval_loaded", "ok": True},
                {"name": "playwright_available", "ok": True},
                {"name": "idempotency_marker_reserved", "ok": True},
                {"name": "navigation_succeeded", "ok": True},
                {"name": "title_matches_excalidraw", "ok": True},
                {"name": "canvas_element_present", "ok": True},
                {"name": "rectangle_action_attempted", "ok": True},
                {"name": "text_action_attempted", "ok": True},
                {"name": "screenshot_captured", "ok": True},
                {"name": "visual_change_after_actions", "ok": True},
            ],
            "blockers": [],
            "screenshot_path": screenshot_path,
            "evidence_json_path": evidence_path,
            "agent_activity_evidence_path": activity_path,
            "page_title": "Excalidraw Whiteboard",
            "canvas_found": True,
            "visual_change_after_actions": True,
            "authority": {
                "target_registered_in_chaseos": True,
                "target_registry_id": "excalidraw",
                "target_url": "https://excalidraw.com",
                "throwaway_browser_context_only": True,
                "no_login_profile_cookies": True,
                "no_real_profile": True,
                "no_credentials": True,
                "no_cookie_export": True,
                "no_browser_use_cli": True,
                "no_mcp_invocation": True,
                "no_provider_calls": True,
                "no_agent_bus_writes": True,
                "no_gate_mutation": True,
                "no_trusted_skill_write": True,
                "no_skill_activation": True,
                "no_canonical_mutation": True,
            },
            "mcp_invocation_attempted": False,
            "mcp_tool_call_attempted": False,
            "draft_skill_written": False,
            "untrusted_candidate_written": False,
            "trusted_skill_write_attempted": False,
            "skill_activation_attempted": False,
            "real_profile_access_attempted": False,
            "credential_or_cookie_read_attempted": False,
            "cookie_export_attempted": False,
            "browser_profile_sync_attempted": False,
            "browser_history_import_attempted": False,
            "public_tunnel_attempted": False,
            "browser_harness_used": False,
            "browser_use_cli_live_used": False,
            "workflow_use_code_copied": False,
            "shell_execution_from_browser_runtime_attempted": False,
            "agent_bus_enqueue_attempted": False,
            "provider_call_attempted": False,
            "gate_mutation_attempted": False,
            "canonical_writeback_attempted": False,
        },
    )


def _seed_browser_runtime_completion_estimate(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/completion_estimate.py",
        "runtime/browser_runtime/test_completion_estimate.py",
        "06_AGENTS/Browser-Runtime-Completion-Estimate.md",
    ):
        _write(root / relative)


def _seed_studio_browser_runtime_operator_ui_readiness(root: Path) -> None:
    for relative in (
        "runtime/studio/browser_runtime_operator_ui_readiness.py",
        "runtime/studio/test_browser_runtime_operator_ui_readiness.py",
        "06_AGENTS/Studio-Browser-Runtime-Operator-UI-Readiness.md",
    ):
        _write(root / relative)


def _seed_studio_browser_runtime_native_panel(root: Path) -> None:
    _seed_studio_browser_runtime_operator_ui_readiness(root)
    for relative in (
        "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-native-shell-panel-static-qa.md",
        "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-qa-runner-static-qa.md",
        "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-browser-qa.md",
    ):
        _write(root / relative)


def _seed_browser_runtime_production_complete(root: Path) -> None:
    for relative in (
        "runtime/browser_runtime/production_closeout.py",
        "runtime/browser_runtime/test_production_closeout.py",
    ):
        _write(root / relative)
    _write_json(
        root / "07_LOGS/Studio-Graph-Views/2026-05-05-browser-runtime-production-complete.json",
        {
            "record_type": "browser_runtime_production_closeout",
            "schema_version": "browser.production_closeout.v1",
            "status": "browser_runtime_production_complete",
            "bounded_mvp_done": True,
            "production_feature_done": True,
            "internal_studio_panel_lane_complete": True,
            "external_runtime_lanes_deferred": False,
            "blocker_count": 0,
            "remaining_major_passes_min": 0,
            "remaining_major_passes_max": 0,
            "remaining_internal_passes": [],
            "external_deferred_lanes": [],
            "blocked_reasons": [],
            "dependency_install_attempted": False,
            "server_start_attempted": False,
            "network_probe_attempted": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "mcp_invocation_attempted": False,
            "target_navigation_attempted": False,
            "screenshot_capture_attempted": False,
            "browser_use_cli_live_used": False,
            "excalidraw_live_proof_attempted": False,
            "approval_grant_attempted": False,
            "approval_execution_attempted": False,
            "trusted_skill_write_attempted": False,
            "skill_activation_attempted": False,
            "real_profile_access_attempted": False,
            "credential_or_cookie_read_attempted": False,
            "agent_bus_enqueue_attempted": False,
            "provider_call_attempted": False,
            "connector_call_attempted": False,
            "gate_mutation_attempted": False,
            "canonical_writeback_attempted": False,
        },
    )


def test_module_does_not_import_browser_or_writer_surfaces() -> None:
    source = inspect.getsource(completion_module)
    forbidden_tokens = (
        "write_cdp_read_only_approval_request",
        "write_cdp_read_only_approval_decision",
        "execute_cdp_read_only_proof",
        "create_task(",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_empty_repo_reports_not_done_without_writes() -> None:
    root = _workspace_test_root("empty_repo")
    try:
        before = sorted(path.as_posix() for path in root.rglob("*"))
        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T01:55:00Z",
        )
        after = sorted(path.as_posix() for path in root.rglob("*"))

        assert before == after
        assert status.bounded_mvp_done is False
        assert status.production_feature_done is False
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert "bounded_mvp:adapter_contract" in status.blocked_reasons
    finally:
        _remove_test_root(root)


def test_bounded_mvp_done_still_reports_production_blocked() -> None:
    root = _workspace_test_root("bounded_mvp_done")
    try:
        _seed_bounded_mvp_evidence(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T01:56:00Z",
        )
        payload = status.to_dict()

        assert status.overall_status == BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED
        assert status.bounded_mvp_done is True
        assert status.production_feature_done is False
        assert "full_vincisos_product_ui_proof_not_run" in status.blocked_reasons
        assert "default_live_cdp_launcher_and_client_not_built" in status.blocked_reasons
        assert payload["read_only"] is True
        assert payload["browser_launch_attempted"] is False
        assert payload["trusted_skill_write_attempted"] is False
        assert payload["canonical_writeback_attempted"] is False
    finally:
        _remove_test_root(root)


def test_cdp_activation_evidence_removes_cdp_not_built_blocker() -> None:
    root = _workspace_test_root("cdp_activation_evidence")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T02:30:00Z",
        )
        cdp_item = next(item for item in status.items if item.area == "production:default_live_cdp_launcher_and_client")

        assert status.overall_status == BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED
        assert status.bounded_mvp_done is True
        assert status.production_feature_done is False
        assert cdp_item.status == "complete_targeted"
        assert cdp_item.complete_for_production is True
        assert "default_live_cdp_launcher_and_client_not_built" not in status.blocked_reasons
        assert "full_vincisos_product_ui_proof_not_run" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
    finally:
        _remove_test_root(root)


def test_browser_use_cli_validation_preflight_is_tracked_separately_from_live_validation() -> None:
    root = _workspace_test_root("browser_use_cli_validation_preflight")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T03:05:00Z",
        )
        preflight_item = next(
            item for item in status.items if item.area == "production:browser_use_cli_validation_preflight"
        )

        assert preflight_item.status == "complete_targeted"
        assert preflight_item.complete_for_production is True
        assert "browser_use_cli_validation_preflight_not_built" not in status.blocked_reasons
        assert "browser_use_cli_live_validation_deferred" in status.blocked_reasons
        assert status.browser_use_cli_live_used is False
        assert status.browser_launch_attempted is False
    finally:
        _remove_test_root(root)


def test_vincisos_product_ui_target_probe_is_tracked_without_browser_execution() -> None:
    root = _workspace_test_root("vincisos_product_ui_target_probe")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T03:45:00Z",
        )
        probe_item = next(
            item for item in status.items if item.area == "production:vincisos_product_ui_target_availability_probe"
        )

        assert probe_item.status == "complete_targeted"
        assert probe_item.complete_for_production is True
        assert "vincisos_product_ui_target_probe_not_built" not in status.blocked_reasons
        assert "full_vincisos_product_ui_proof_not_run" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.credential_or_cookie_read_attempted is False
    finally:
        _remove_test_root(root)


def test_vincisos_product_ui_launch_readiness_is_tracked_without_starting_servers() -> None:
    root = _workspace_test_root("vincisos_product_ui_launch_readiness")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T10:55:00Z",
        )
        launch_item = next(
            item for item in status.items if item.area == "production:vincisos_product_ui_launch_readiness"
        )

        assert launch_item.status == "complete_targeted"
        assert launch_item.complete_for_production is True
        assert "vincisos_product_ui_launch_readiness_not_built" not in status.blocked_reasons
        assert "full_vincisos_product_ui_proof_not_run" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.credential_or_cookie_read_attempted is False
    finally:
        _remove_test_root(root)


def test_vincisos_product_ui_browser_proof_closes_vincisos_blocker_without_completing_feature() -> None:
    root = _workspace_test_root("vincisos_product_ui_browser_proof")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T14:30:00Z",
        )
        proof_item = next(
            item for item in status.items if item.area == "production:full_vincisos_product_ui_browser_proof"
        )

        assert proof_item.status == "complete_targeted"
        assert proof_item.complete_for_production is True
        assert "full_vincisos_product_ui_proof_not_run" not in status.blocked_reasons
        assert "browser_use_cli_live_validation_deferred" in status.blocked_reasons
        assert status.production_feature_done is False
        assert status.next_recommended_pass == "browser-use-cli-live-validation"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.credential_or_cookie_read_attempted is False
        assert status.trusted_skill_write_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_browser_use_cli_unavailable_evidence_advances_next_recommended_pass() -> None:
    root = _workspace_test_root("browser_use_cli_unavailable_evidence")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T16:55:00Z",
        )
        live_item = next(
            item for item in status.items if item.area == "production:browser_use_cli_live_validation"
        )

        assert live_item.status == "blocked_unavailable"
        assert live_item.complete_for_production is False
        assert "browser_use_cli_live_validation_deferred" not in status.blocked_reasons
        assert "browser_use_cli_live_validation_blocked_unavailable" in status.blocked_reasons
        assert status.next_recommended_pass == "workflow-replay-execution-readiness-preflight"
        assert status.browser_use_cli_live_used is False
        assert status.browser_launch_attempted is False
        assert status.real_profile_access_attempted is False
        assert status.credential_or_cookie_read_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_browser_use_cli_unavailable_evidence_rejects_live_run_effects() -> None:
    root = _workspace_test_root("unsafe_browser_use_cli_unavailable_evidence")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root, unsafe=True)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)

        status = build_browser_runtime_completion_status(root)
        live_item = next(
            item for item in status.items if item.area == "production:browser_use_cli_live_validation"
        )

        assert live_item.status == "deferred"
        assert "browser_use_cli_live_validation_deferred" in status.blocked_reasons
        assert "browser_use_cli_live_validation_blocked_unavailable" not in status.blocked_reasons
        assert status.next_recommended_pass == "browser-use-cli-live-validation"
    finally:
        _remove_test_root(root)


def test_vincisos_product_ui_browser_proof_rejects_unsafe_run_log() -> None:
    root = _workspace_test_root("unsafe_vincisos_product_ui_browser_proof")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root, unsafe=True)

        status = build_browser_runtime_completion_status(root)
        proof_item = next(
            item for item in status.items if item.area == "production:full_vincisos_product_ui_browser_proof"
        )

        assert proof_item.status == "blocked"
        assert proof_item.complete_for_production is False
        assert "full_vincisos_product_ui_proof_not_run" in status.blocked_reasons
    finally:
        _remove_test_root(root)


def test_browser_harness_adoption_decision_removes_decision_blocker_without_harness_use() -> None:
    root = _workspace_test_root("browser_harness_adoption_decision")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_browser_harness_adoption_decision(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T03:25:00Z",
        )
        decision_item = next(
            item for item in status.items if item.area == "production:browser_harness_adoption_decision"
        )

        assert decision_item.status == "complete_targeted"
        assert decision_item.complete_for_production is True
        assert "browser_harness_adoption_decision_not_recorded" not in status.blocked_reasons
        assert "browser_harness_adoption_deferred" not in status.blocked_reasons
        assert status.browser_harness_used is False
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
    finally:
        _remove_test_root(root)


def test_browser_workflow_cache_foundation_removes_cache_blocker_without_replay_execution() -> None:
    root = _workspace_test_root("browser_workflow_cache_foundation")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T11:10:00Z",
        )
        workflow_item = next(
            item for item in status.items if item.area == "production:browser_workflow_cache_foundation"
        )

        assert workflow_item.status == "complete_targeted"
        assert workflow_item.complete_for_production is True
        assert "browser_workflow_cache_foundation_not_built" not in status.blocked_reasons
        assert "workflow_replay_cache_deferred" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_executor_design_preflight_is_tracked_without_replay_execution() -> None:
    root = _workspace_test_root("workflow_replay_executor_design_preflight")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T11:35:00Z",
        )
        replay_design_item = next(
            item for item in status.items if item.area == "production:workflow_replay_executor_design_preflight"
        )

        assert replay_design_item.status == "complete_targeted"
        assert replay_design_item.complete_for_production is True
        assert "workflow_replay_executor_design_preflight_not_built" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_executor_implementation_request_is_tracked_without_execution_or_write() -> None:
    root = _workspace_test_root("workflow_replay_executor_implementation_request")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T11:50:00Z",
        )
        request_item = next(
            item for item in status.items if item.area == "production:workflow_replay_executor_implementation_request"
        )

        assert request_item.status == "complete_targeted"
        assert request_item.complete_for_production is True
        assert "workflow_replay_executor_implementation_request_not_built" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_executor_implementation_approval_is_tracked_without_execution_or_write() -> None:
    root = _workspace_test_root("workflow_replay_executor_implementation_approval")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T12:20:00Z",
        )
        approval_item = next(
            item for item in status.items if item.area == "production:workflow_replay_executor_implementation_approval"
        )

        assert approval_item.status == "complete_targeted"
        assert approval_item.complete_for_production is True
        assert "workflow_replay_executor_implementation_approval_not_built" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_executor_implementation_is_tracked_without_replay_execution() -> None:
    root = _workspace_test_root("workflow_replay_executor_implementation")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T12:50:00Z",
        )
        implementation_item = next(
            item for item in status.items if item.area == "production:workflow_replay_executor_implementation"
        )

        assert implementation_item.status == "complete_targeted"
        assert implementation_item.complete_for_production is True
        assert "workflow_replay_executor_implementation_not_built" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_execution_readiness_preflight_advances_next_self_satisfiable_pass() -> None:
    root = _workspace_test_root("workflow_replay_execution_readiness_preflight")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T17:35:00Z",
        )
        readiness_item = next(
            item for item in status.items if item.area == "production:workflow_replay_execution_readiness_preflight"
        )

        assert readiness_item.status == "complete_targeted"
        assert readiness_item.complete_for_production is True
        assert "workflow_replay_execution_readiness_preflight_not_built" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.next_recommended_pass == "workflow-replay-trial-candidate-selection"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_trial_candidate_selection_advances_to_execution_approval_pass() -> None:
    root = _workspace_test_root("workflow_replay_trial_candidate_selection")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T20:30:00Z",
        )
        trial_item = next(
            item for item in status.items if item.area == "production:workflow_replay_trial_candidate_selection"
        )

        assert trial_item.status == "complete_targeted"
        assert trial_item.complete_for_production is True
        assert "workflow_replay_trial_candidate_not_selected" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.next_recommended_pass == "workflow-replay-execution-approval-and-idempotency"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_execution_approval_idempotency_advances_to_safe_local_replay_proof() -> None:
    root = _workspace_test_root("workflow_replay_execution_approval_idempotency")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-02T21:30:00Z",
        )
        approval_item = next(
            item
            for item in status.items
            if item.area == "production:workflow_replay_execution_approval_and_idempotency"
        )

        assert approval_item.status == "complete_targeted"
        assert approval_item.complete_for_production is True
        assert "workflow_replay_execution_approval_idempotency_not_built" not in status.blocked_reasons
        assert "workflow_replay_execution_proof_not_built" in status.blocked_reasons
        assert status.next_recommended_pass == "safe-local-workflow-replay-execution-proof"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_execution_proof_implementation_is_tracked_until_live_success() -> None:
    root = _workspace_test_root("workflow_replay_execution_proof_implementation")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_implementation(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T08:30:00Z",
        )
        proof_item = next(
            item for item in status.items if item.area == "production:workflow_replay_execution_proof"
        )

        assert proof_item.status == "implementation_ready_live_blocked"
        assert proof_item.complete_for_production is False
        assert "workflow_replay_execution_proof_not_built" not in status.blocked_reasons
        assert "workflow_replay_execution_live_proof_not_run" in status.blocked_reasons
        assert status.next_recommended_pass == "safe-local-workflow-replay-execution-proof"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_workflow_replay_execution_success_advances_to_excalidraw_prep_until_prep_exists() -> None:
    root = _workspace_test_root("workflow_replay_execution_proof_success")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T08:40:00Z",
        )
        proof_item = next(
            item for item in status.items if item.area == "production:workflow_replay_execution_proof"
        )

        assert proof_item.status == "complete_targeted"
        assert proof_item.complete_for_production is True
        assert "workflow_replay_execution_live_proof_not_run" not in status.blocked_reasons
        assert status.next_recommended_pass == "excalidraw-local-browser-mcp-proof-prep"
        assert "excalidraw_local_browser_mcp_proof_prep_not_built" in status.blocked_reasons
        assert "excalidraw_live_browser_mcp_proof_not_run" in status.blocked_reasons
        assert status.production_feature_done is False
    finally:
        _remove_test_root(root)


def test_excalidraw_mcp_proof_prep_advances_to_live_readiness_without_execution() -> None:
    root = _workspace_test_root("excalidraw_mcp_proof_prep")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T12:40:00Z",
        )
        prep_item = next(
            item for item in status.items if item.area == "production:excalidraw_local_browser_mcp_proof_prep"
        )

        assert prep_item.status == "complete_targeted"
        assert prep_item.complete_for_production is True
        assert "excalidraw_local_browser_mcp_proof_prep_not_built" not in status.blocked_reasons
        assert "excalidraw_live_browser_mcp_proof_not_run" in status.blocked_reasons
        assert status.next_recommended_pass == "excalidraw-local-browser-mcp-live-readiness"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
        assert status.production_feature_done is False
    finally:
        _remove_test_root(root)


def test_excalidraw_mcp_live_readiness_records_missing_local_target_without_execution() -> None:
    root = _workspace_test_root("excalidraw_mcp_live_readiness_missing_target")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T14:10:00Z",
        )
        readiness_item = next(
            item for item in status.items if item.area == "production:excalidraw_local_browser_mcp_live_readiness"
        )

        assert readiness_item.status == "complete_targeted_blocked_current_target"
        assert readiness_item.complete_for_production is False
        assert "excalidraw_local_browser_mcp_live_readiness_not_built" not in status.blocked_reasons
        assert "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target" in status.blocked_reasons
        assert "excalidraw_live_browser_mcp_proof_not_run" in status.blocked_reasons
        assert status.next_recommended_pass == "excalidraw-local-target-setup-instructions"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
        assert status.production_feature_done is False
    finally:
        _remove_test_root(root)


def test_excalidraw_target_setup_instructions_advance_to_readiness_with_target_pass() -> None:
    root = _workspace_test_root("excalidraw_target_setup_instructions")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T19:45:00Z",
        )
        setup_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_local_target_setup_instructions"
        )

        assert setup_item.status == "complete_targeted"
        assert setup_item.complete_for_production is True
        assert "excalidraw_local_target_setup_instructions_not_built" not in status.blocked_reasons
        assert "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target" in status.blocked_reasons
        assert status.next_recommended_pass == "external-runtime-provide-excalidraw-target-url"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.agent_bus_enqueue_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
        assert status.production_feature_done is False
    finally:
        _remove_test_root(root)


def test_excalidraw_target_setup_instructions_rejects_unsafe_effects() -> None:
    root = _workspace_test_root("excalidraw_target_setup_instructions_unsafe")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root, unsafe=True)

        status = build_browser_runtime_completion_status(root)
        setup_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_local_target_setup_instructions"
        )

        assert setup_item.status == "not_built"
        assert "excalidraw_local_target_setup_instructions_not_built" in status.blocked_reasons
        assert status.next_recommended_pass == "excalidraw-local-target-setup-instructions"
    finally:
        _remove_test_root(root)


def test_excalidraw_target_contract_request_is_tracked_without_changing_url_blocker() -> None:
    root = _workspace_test_root("excalidraw_target_contract_request")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T20:05:00Z",
        )
        contract_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_local_target_contract_request"
        )

        assert contract_item.status == "complete_targeted"
        assert contract_item.complete_for_production is True
        assert "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target" in status.blocked_reasons
        assert status.next_recommended_pass == "external-runtime-provide-excalidraw-target-url"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
        assert status.production_feature_done is False
    finally:
        _remove_test_root(root)


def test_excalidraw_target_response_intake_is_tracked_without_changing_url_blocker() -> None:
    root = _workspace_test_root("excalidraw_target_response_intake")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T20:40:00Z",
        )
        response_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_local_target_response_intake"
        )

        assert response_item.status == "complete_targeted"
        assert response_item.complete_for_production is True
        assert "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target" in status.blocked_reasons
        assert status.next_recommended_pass == "external-runtime-provide-excalidraw-target-url"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.real_profile_access_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_unsafe_excalidraw_target_response_intake_is_not_counted() -> None:
    root = _workspace_test_root("excalidraw_target_response_intake_unsafe")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root, unsafe=True)

        status = build_browser_runtime_completion_status(root)
        response_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_local_target_response_intake"
        )

        assert response_item.status == "not_built"
    finally:
        _remove_test_root(root)


def test_excalidraw_target_response_latest_resolver_is_tracked_without_authority() -> None:
    root = _workspace_test_root("excalidraw_target_response_latest_resolver")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root)
        _seed_excalidraw_target_response_resolver(root)

        status = build_browser_runtime_completion_status(root)
        resolver_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_target_response_latest_resolver"
        )

        assert resolver_item.status == "complete_targeted"
        assert resolver_item.complete_for_production is True
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_excalidraw_readiness_from_response_is_tracked_without_removing_target_blocker() -> None:
    root = _workspace_test_root("excalidraw_readiness_from_response")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root)
        _seed_excalidraw_readiness_from_response(root)
        _seed_excalidraw_mcp_execution_approval(root)
        _seed_excalidraw_mcp_proof_execution_shell(root)
        _seed_excalidraw_live_chain_readiness(root)
        _seed_browser_runtime_completion_estimate(root)
        _seed_studio_browser_runtime_operator_ui_readiness(root)

        status = build_browser_runtime_completion_status(
            root,
            generated_at="2026-05-03T21:20:00Z",
        )
        bridge_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_readiness_from_target_response"
        )

        assert bridge_item.status == "complete_targeted_blocked_current_target"
        assert bridge_item.complete_for_production is True
        approval_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_mcp_execution_approval"
        )
        assert approval_item.status == "complete_targeted_blocked_current_target"
        assert approval_item.complete_for_production is True
        assert "excalidraw_mcp_execution_approval_not_built" not in status.blocked_reasons
        shell_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_mcp_proof_execution_shell"
        )
        assert shell_item.status == "complete_targeted_blocked_current_target"
        assert shell_item.complete_for_production is True
        assert "excalidraw_mcp_proof_execution_shell_not_built" not in status.blocked_reasons
        chain_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_live_chain_readiness_reporter"
        )
        assert chain_item.status == "complete_targeted_blocked_current_target"
        assert chain_item.complete_for_production is True
        estimate_item = next(
            item
            for item in status.items
            if item.area == "production:browser_runtime_completion_estimate"
        )
        assert estimate_item.status == "complete_targeted"
        assert estimate_item.complete_for_production is True
        studio_item = next(
            item
            for item in status.items
            if item.area == "production:studio_browser_runtime_operator_ui_readiness"
        )
        assert studio_item.status == "complete_targeted"
        assert studio_item.complete_for_production is True
        assert "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target" in status.blocked_reasons
        assert status.next_recommended_pass == "external-runtime-provide-excalidraw-target-url"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.real_profile_access_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_excalidraw_public_live_browser_proof_is_tracked_without_clearing_mcp_blocker() -> None:
    root = _workspace_test_root("excalidraw_public_live_browser_proof")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_excalidraw_public_live_browser_proof(root)

        status = build_browser_runtime_completion_status(root)
        item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_public_live_browser_proof"
        )

        assert item.status == "complete_targeted"
        assert item.complete_for_production is True
        assert "excalidraw_live_browser_mcp_proof_not_run" in status.blocked_reasons
        assert "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target" not in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.provider_call_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_excalidraw_public_live_browser_proof_uses_latest_success_not_latest_failure() -> None:
    root = _workspace_test_root("excalidraw_public_live_browser_proof_latest_success")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_excalidraw_public_live_browser_proof(root)
        _seed_failed_excalidraw_public_live_browser_proof(root)

        status = build_browser_runtime_completion_status(root)
        item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_public_live_browser_proof"
        )

        assert item.status == "complete_targeted"
        assert "excalidraw_live_browser_mcp_proof_not_run" in status.blocked_reasons
        assert "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target" not in status.blocked_reasons
    finally:
        _remove_test_root(root)


def test_excalidraw_public_drawing_proof_clears_mcp_proof_blocker() -> None:
    root = _workspace_test_root("xdraw_proof")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_excalidraw_public_drawing_proof(root)

        status = build_browser_runtime_completion_status(root)
        item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_public_browser_drawing_proof_run"
        )

        assert item.status == "complete_targeted"
        assert item.complete_for_production is True
        assert "excalidraw_live_browser_mcp_proof_not_run" not in status.blocked_reasons
        assert status.browser_launch_attempted is False
        assert status.provider_call_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_browser_runtime_can_report_production_complete_after_public_drawing_proof() -> None:
    root = _workspace_test_root("prod_complete_xdraw")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_safe_url_run(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root)
        _seed_excalidraw_target_response_resolver(root)
        _seed_excalidraw_readiness_from_response(root)
        _seed_excalidraw_mcp_execution_approval(root)
        _seed_excalidraw_mcp_proof_execution_shell(root)
        _seed_excalidraw_live_chain_readiness(root)
        _seed_excalidraw_public_drawing_proof(root)
        _seed_browser_runtime_completion_estimate(root)
        _seed_studio_browser_runtime_native_panel(root)

        status = build_browser_runtime_completion_status(root)

        assert status.bounded_mvp_done is True
        assert status.production_feature_done is True
        assert status.overall_status == BROWSER_RUNTIME_OVERALL_COMPLETE
        assert status.blocked_reasons == ()
        assert status.next_recommended_pass == "browser-runtime-production-complete"
        assert status.browser_launch_attempted is False
        assert status.cdp_connection_attempted is False
        assert status.provider_call_attempted is False
        assert status.gate_mutation_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_browser_runtime_production_complete_evidence_advances_next_pass() -> None:
    root = _workspace_test_root("prod_complete_closeout")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_safe_url_run(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root)
        _seed_excalidraw_target_response_resolver(root)
        _seed_excalidraw_readiness_from_response(root)
        _seed_excalidraw_mcp_execution_approval(root)
        _seed_excalidraw_mcp_proof_execution_shell(root)
        _seed_excalidraw_live_chain_readiness(root)
        _seed_excalidraw_public_drawing_proof(root)
        _seed_browser_runtime_completion_estimate(root)
        _seed_studio_browser_runtime_native_panel(root)
        _seed_browser_runtime_production_complete(root)

        status = build_browser_runtime_completion_status(root)
        closeout_item = next(
            item
            for item in status.items
            if item.area == "production:browser_runtime_production_complete"
        )

        assert status.production_feature_done is True
        assert status.blocked_reasons == ()
        assert status.next_recommended_pass == "phase10-studio-product-hardening"
        assert closeout_item.status == "complete"
        assert status.browser_launch_attempted is False
        assert status.provider_call_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_studio_native_panel_evidence_removes_operator_ui_blocker() -> None:
    root = _workspace_test_root("studio_native_panel_evidence")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root)
        _seed_excalidraw_readiness_from_response(root)
        _seed_excalidraw_mcp_execution_approval(root)
        _seed_excalidraw_mcp_proof_execution_shell(root)
        _seed_excalidraw_live_chain_readiness(root)
        _seed_browser_runtime_completion_estimate(root)
        _seed_studio_browser_runtime_native_panel(root)

        status = build_browser_runtime_completion_status(root)
        panel_item = next(
            item
            for item in status.items
            if item.area == "production:studio_browser_runtime_native_panel"
        )

        assert panel_item.status == "complete_targeted"
        assert panel_item.complete_for_production is True
        assert "studio_operator_ui_not_built" not in status.blocked_reasons
        assert status.production_feature_done is False
        assert status.browser_launch_attempted is False
        assert status.provider_call_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_unsafe_excalidraw_readiness_from_response_is_not_counted() -> None:
    root = _workspace_test_root("excalidraw_readiness_from_response_unsafe")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root)
        _seed_excalidraw_target_setup_instructions(root)
        _seed_excalidraw_target_contract_request(root)
        _seed_excalidraw_target_response_intake(root)
        _seed_excalidraw_readiness_from_response(root, unsafe=True)

        status = build_browser_runtime_completion_status(root)
        bridge_item = next(
            item
            for item in status.items
            if item.area == "production:excalidraw_readiness_from_target_response"
        )

        assert bridge_item.status == "not_built"
    finally:
        _remove_test_root(root)


def test_excalidraw_mcp_live_readiness_rejects_unsafe_effects() -> None:
    root = _workspace_test_root("excalidraw_mcp_live_readiness_unsafe")
    try:
        _seed_bounded_mvp_evidence(root)
        _seed_cdp_activation_evidence(root)
        _seed_browser_use_cli_validation_preflight(root)
        _seed_browser_use_cli_live_unavailable_evidence(root)
        _seed_vincisos_product_ui_target_probe(root)
        _seed_vincisos_product_ui_launch_readiness(root)
        _seed_vincisos_product_ui_browser_proof(root)
        _seed_browser_harness_adoption_decision(root)
        _seed_browser_workflow_cache_foundation(root)
        _seed_workflow_replay_executor_design_preflight(root)
        _seed_workflow_replay_executor_implementation_request(root)
        _seed_workflow_replay_executor_implementation_approval(root)
        _seed_workflow_replay_executor_implementation(root)
        _seed_workflow_replay_execution_readiness_preflight(root)
        _seed_workflow_replay_trial_candidate_selection(root)
        _seed_workflow_replay_execution_approval_idempotency(root)
        _seed_workflow_replay_execution_proof_success(root)
        _seed_excalidraw_mcp_proof_prep(root)
        _seed_excalidraw_mcp_live_readiness(root, unsafe=True)

        status = build_browser_runtime_completion_status(root)
        readiness_item = next(
            item for item in status.items if item.area == "production:excalidraw_local_browser_mcp_live_readiness"
        )

        assert readiness_item.status == "not_built"
        assert "excalidraw_local_browser_mcp_live_readiness_unsafe_or_invalid" in status.blocked_reasons
        assert status.next_recommended_pass == "excalidraw-local-browser-mcp-live-readiness"
    finally:
        _remove_test_root(root)


def test_unsafe_mvp_run_log_blocks_mvp_done() -> None:
    root = _workspace_test_root("unsafe_mvp")
    try:
        _seed_bounded_mvp_evidence(root, unsafe=True)

        status = build_browser_runtime_completion_status(root)
        safety_item = next(item for item in status.items if item.area == "bounded_mvp:safety_flags")

        assert status.bounded_mvp_done is False
        assert safety_item.status == "blocked"
        assert "bounded_mvp:safety_flags" in status.blocked_reasons
    finally:
        _remove_test_root(root)


def test_rejects_authority_flags() -> None:
    root = _workspace_test_root("authority_flags")
    try:
        status = build_browser_runtime_completion_status(root)

        for flag in (
            "writes_status_artifact",
            "browser_launch_attempted",
            "cdp_connection_attempted",
            "real_profile_access_attempted",
            "credential_or_cookie_read_attempted",
            "browser_harness_used",
            "browser_use_cli_live_used",
            "trusted_skill_write_attempted",
            "skill_activation_attempted",
            "agent_bus_enqueue_attempted",
            "provider_call_attempted",
            "gate_mutation_attempted",
            "canonical_writeback_attempted",
        ):
            with pytest_raises(ValueError):
                type(status)(
                    generated_at=status.generated_at,
                    overall_status=status.overall_status,
                    bounded_mvp_done=status.bounded_mvp_done,
                    production_feature_done=status.production_feature_done,
                    next_recommended_pass=status.next_recommended_pass,
                    blocked_reasons=status.blocked_reasons,
                    items=status.items,
                    **{flag: True},
                ).validate()
    finally:
        _remove_test_root(root)


def test_module_cli_prints_json_without_writes() -> None:
    root = _workspace_test_root("module_cli")
    try:
        _seed_bounded_mvp_evidence(root)

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = completion_main(["--vault-root", str(root), "--json"])
        payload = json.loads(output.getvalue())

        assert exit_code == 0
        assert payload["bounded_mvp_done"] is True
        assert payload["production_feature_done"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["writes_status_artifact"] is False
    finally:
        _remove_test_root(root)


class pytest_raises:
    def __init__(self, expected: type[BaseException]):
        self.expected = expected

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            raise AssertionError(f"expected {self.expected.__name__}")
        if not issubclass(exc_type, self.expected):
            return False
        return True

