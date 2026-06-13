"""Read-only Browser Runtime Adapter completion status.

This module reports whether Browser Runtime Adapter + Site Skill Memory is done
from repo-local evidence. It does not launch browsers, connect to CDP, write
artifacts, promote skills, enqueue Agent Bus tasks, call providers, mutate Gate
policy, or update canonical ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BROWSER_RUNTIME_OVERALL_NOT_STARTED = "not_started"
BROWSER_RUNTIME_OVERALL_PARTIAL = "partial"
BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED = "mvp_done_production_blocked"
BROWSER_RUNTIME_OVERALL_COMPLETE = "complete"
BROWSER_RUNTIME_COMPLETION_STATUSES = {
    BROWSER_RUNTIME_OVERALL_NOT_STARTED,
    BROWSER_RUNTIME_OVERALL_PARTIAL,
    BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED,
    BROWSER_RUNTIME_OVERALL_COMPLETE,
}

BROWSER_RUNTIME_BLOCKED_EFFECTS = (
    "browser_launch",
    "cdp_connection",
    "real_profile_access",
    "credential_or_cookie_read",
    "browser_harness_use",
    "browser_use_cli_live_run",
    "trusted_skill_write",
    "skill_activation",
    "agent_bus_enqueue",
    "provider_call",
    "gate_mutation",
    "canonical_writeback",
)

MVP_REQUIRED_PATHS = {
    "adapter_contract": (
        "runtime/browser_runtime/models.py",
        "runtime/browser_runtime/adapter.py",
    ),
    "fail_closed_provider_wrapper": (
        "runtime/browser_runtime/adapters/browser_use_cli.py",
    ),
    "browser_run_logging": (
        "07_LOGS/Browser-Runs",
        "07_LOGS/Agent-Activity",
    ),
    "draft_skill_generation": (
        "06_AGENTS/Browser-Skills/_drafts",
    ),
    "static_safe_target": (
        "runtime/browser_runtime/test_targets/vincisos_shadow.html",
    ),
    "in_app_browser_proof": (
        "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json",
        "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_screenshot.png",
        "06_AGENTS/Browser-Skills/_drafts/draft-vincisos-inapp-browser-20260430.md",
    ),
    "draft_skill_replay": (
        "07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_success.json",
        "07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_screenshot.png",
        "06_AGENTS/Browser-Skills/_drafts/replay-vincisos-draft-skill-20260501.md",
    ),
    "selector_click_hardening": (
        "07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_success.json",
    ),
    "screenshot_artifact_hardening": (
        "07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_success.json",
        "07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_screenshot.png",
        "runtime/browser_runtime/artifacts.py",
    ),
}

MVP_SAFE_RUN_LOGS = (
    "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json",
    "07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_success.json",
    "07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_success.json",
    "07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_success.json",
)

PRODUCTION_GATES = (
    (
        "full_vincisos_ui_safe_mode_preflight",
        "complete_targeted",
        "runtime/browser_runtime/vincisos_full_ui_preflight.py; "
        "07_LOGS/Browser-Runs/vincisos_full_ui_safe_mode_preflight_20260501_blocked_current_static_fixture.json",
        "Preflight exists and the old static fixture remains correctly blocked; the registered product UI target is handled by the proof evidence gate.",
    ),
    (
        "full_vincisos_ui_target_contract",
        "complete_targeted",
        "runtime/browser_runtime/vincisos_full_ui_target_contract.py; "
        "runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json; "
        "07_LOGS/Browser-Runs/vincisos_full_ui_target_contract_20260501_blocked_static_fixture.json",
        "Target contract validator exists, blocks the old static fixture, and the registered product UI target is covered by the proof evidence gate.",
    ),
    (
        "contract_backed_proof_planner",
        "complete_targeted",
        "runtime/browser_runtime/vincisos_contract_backed_proof.py; "
        "07_LOGS/Browser-Runs/vincisos_contract_backed_proof_plan_20260502_blocked_static_fixture.json",
        "Planner exists, the old static fixture remains blocked, and the registered product UI target proof has now been recorded separately.",
    ),
    (
        "browser_use_cli_live_validation",
        "deferred",
        "runtime/browser_runtime/adapters/browser_use_cli.py",
        "Wrapper fails closed; no live Browser Use CLI run has been authorized or validated.",
    ),
    (
        "workflow_replay_execution",
        "deferred",
        "runtime/browser_runtime/workflow_replay_execution_proof.py",
        "Safe-local replay proof runner is tracked separately; live proof remains blocked until bounded execution evidence exists.",
    ),
    (
        "excalidraw_browser_or_mcp_test",
        "deferred",
        "06_AGENTS/Browser-Runtime-Test-Plan.md",
        "Legacy local Excalidraw browser/MCP proof remains deferred until a safe loopback target is supplied; the approved public no-login drawing proof is tracked by the dedicated public drawing proof item.",
    ),
    (
        "studio_operator_governed_actions",
        "deferred",
        "Phase 10 Studio/operator governed action surface",
        "Read-only Browser Runtime Studio panel is built; approval execution, skill promotion, and local-target MCP execution remain deferred to later governed passes.",
    ),
)

BROWSER_USE_CLI_VALIDATION_PREFLIGHT_PATHS = (
    "runtime/browser_runtime/browser_use_cli_validation.py",
    "runtime/browser_runtime/test_browser_use_cli_validation.py",
)

BROWSER_USE_CLI_VALIDATION_PREFLIGHT_EVIDENCE_TEXT = (
    "runtime/browser_runtime/browser_use_cli_validation.py; "
    "runtime/browser_runtime/test_browser_use_cli_validation.py"
)

BROWSER_USE_CLI_LIVE_UNAVAILABLE_EVIDENCE_PATH = (
    "07_LOGS/Browser-Runs/browser_use_cli_live_validation_20260502_blocked_unavailable.json"
)

BROWSER_USE_CLI_LIVE_UNAVAILABLE_EVIDENCE_TEXT = (
    "07_LOGS/Browser-Runs/browser_use_cli_live_validation_20260502_blocked_unavailable.json"
)

BROWSER_USE_CLI_EXTERNAL_VALIDATION_EVIDENCE_PATH = (
    "07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.json"
)

BROWSER_USE_CLI_EXTERNAL_VALIDATION_EVIDENCE_TEXT = (
    "runtime/browser_runtime/browser_use_cli_external_validation.py; "
    "runtime/browser_runtime/test_browser_use_cli_external_validation.py; "
    "07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.json"
)

BROWSER_USE_CLI_SAFE_URL_DESIGN_EVIDENCE_PATH = (
    "07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-design-20260505.json"
)

BROWSER_USE_CLI_SAFE_URL_DESIGN_EVIDENCE_TEXT = (
    "runtime/browser_runtime/browser_use_cli_safe_url_validation_design.py; "
    "runtime/browser_runtime/test_browser_use_cli_safe_url_validation_design.py; "
    "07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-design-20260505.json"
)

BROWSER_USE_CLI_SAFE_URL_RUN_EVIDENCE_PATH = (
    "07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-run-20260505.json"
)

BROWSER_USE_CLI_SAFE_URL_RUN_EVIDENCE_TEXT = (
    "runtime/browser_runtime/browser_use_cli_safe_url_validation_run.py; "
    "runtime/browser_runtime/test_browser_use_cli_safe_url_validation_run.py; "
    "07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-run-20260505.json"
)

VINCISOS_PRODUCT_UI_TARGET_PROBE_PATHS = (
    "runtime/browser_runtime/vincisos_product_ui_target_probe.py",
    "runtime/browser_runtime/test_browser_runtime.py",
)

VINCISOS_PRODUCT_UI_TARGET_PROBE_EVIDENCE_TEXT = (
    "runtime/browser_runtime/vincisos_product_ui_target_probe.py; "
    "runtime/browser_runtime/test_browser_runtime.py"
)

VINCISOS_PRODUCT_UI_LAUNCH_READINESS_PATHS = (
    "runtime/browser_runtime/vincisos_product_ui_launch_readiness.py",
    "runtime/browser_runtime/test_browser_runtime.py",
)

VINCISOS_PRODUCT_UI_LAUNCH_READINESS_EVIDENCE_TEXT = (
    "runtime/browser_runtime/vincisos_product_ui_launch_readiness.py; "
    "runtime/browser_runtime/test_browser_runtime.py"
)

VINCISOS_PRODUCT_UI_BROWSER_PROOF_PATHS = (
    "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json",
    "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png",
    "07_LOGS/Agent-Activity/2026-05-02-codex-vincisos-product-ui-browser-proof.md",
    "06_AGENTS/Browser-Skills/_drafts/draft-vincisos-product-ui-browser-proof-20260502.md",
    "03_INPUTS/Browser-Skill-Candidates/127-0-0-1/20260502__candidate-vincisos-product-ui-browser-proof-20260502.md",
)

VINCISOS_PRODUCT_UI_BROWSER_PROOF_EVIDENCE_TEXT = (
    "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json; "
    "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png; "
    "07_LOGS/Agent-Activity/2026-05-02-codex-vincisos-product-ui-browser-proof.md; "
    "06_AGENTS/Browser-Skills/_drafts/draft-vincisos-product-ui-browser-proof-20260502.md; "
    "03_INPUTS/Browser-Skill-Candidates/127-0-0-1/20260502__candidate-vincisos-product-ui-browser-proof-20260502.md"
)

BROWSER_HARNESS_ADOPTION_DECISION_PATHS = (
    "runtime/browser_runtime/browser_harness_adoption.py",
    "runtime/browser_runtime/test_browser_harness_adoption.py",
    "06_AGENTS/Browser-Harness-Adoption-Decision.md",
)

BROWSER_HARNESS_ADOPTION_DECISION_EVIDENCE_TEXT = (
    "runtime/browser_runtime/browser_harness_adoption.py; "
    "runtime/browser_runtime/test_browser_harness_adoption.py; "
    "06_AGENTS/Browser-Harness-Adoption-Decision.md"
)

BROWSER_WORKFLOW_CACHE_FOUNDATION_PATHS = (
    "runtime/browser_runtime/workflows.py",
    "runtime/browser_runtime/test_browser_workflow_cache.py",
    "runtime/browser_workflows/metadata.json",
    "06_AGENTS/Browser-Workflow-Cache.md",
)

BROWSER_WORKFLOW_CACHE_FOUNDATION_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflows.py; "
    "runtime/browser_runtime/test_browser_workflow_cache.py; "
    "runtime/browser_workflows/metadata.json; "
    "06_AGENTS/Browser-Workflow-Cache.md"
)

WORKFLOW_REPLAY_EXECUTOR_DESIGN_PREFLIGHT_PATHS = (
    "runtime/browser_runtime/workflow_replay_executor_design.py",
    "runtime/browser_runtime/test_workflow_replay_executor_design.py",
    "06_AGENTS/Browser-Workflow-Replay-Executor-Design.md",
)

WORKFLOW_REPLAY_EXECUTOR_DESIGN_PREFLIGHT_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_executor_design.py; "
    "runtime/browser_runtime/test_workflow_replay_executor_design.py; "
    "06_AGENTS/Browser-Workflow-Replay-Executor-Design.md"
)

WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_REQUEST_PATHS = (
    "runtime/browser_runtime/workflow_replay_executor_request.py",
    "runtime/browser_runtime/test_workflow_replay_executor_request.py",
    "06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Request.md",
)

WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_REQUEST_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_executor_request.py; "
    "runtime/browser_runtime/test_workflow_replay_executor_request.py; "
    "06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Request.md"
)

WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_APPROVAL_PATHS = (
    "runtime/browser_runtime/workflow_replay_executor_approval.py",
    "runtime/browser_runtime/test_workflow_replay_executor_approval.py",
    "06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Approval.md",
)

WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_APPROVAL_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_executor_approval.py; "
    "runtime/browser_runtime/test_workflow_replay_executor_approval.py; "
    "06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Approval.md"
)

WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_PATHS = (
    "runtime/browser_runtime/workflow_replay_executor.py",
    "runtime/browser_runtime/test_workflow_replay_executor.py",
    "06_AGENTS/Browser-Workflow-Replay-Executor.md",
)

WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_executor.py; "
    "runtime/browser_runtime/test_workflow_replay_executor.py; "
    "06_AGENTS/Browser-Workflow-Replay-Executor.md"
)

WORKFLOW_REPLAY_EXECUTION_READINESS_PREFLIGHT_PATHS = (
    "runtime/browser_runtime/workflow_replay_execution_readiness.py",
    "runtime/browser_runtime/test_workflow_replay_execution_readiness.py",
    "06_AGENTS/Browser-Workflow-Replay-Execution-Readiness.md",
)

WORKFLOW_REPLAY_EXECUTION_READINESS_PREFLIGHT_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_execution_readiness.py; "
    "runtime/browser_runtime/test_workflow_replay_execution_readiness.py; "
    "06_AGENTS/Browser-Workflow-Replay-Execution-Readiness.md"
)

WORKFLOW_REPLAY_TRIAL_CANDIDATE_WORKFLOW_ID = (
    "wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502"
)

WORKFLOW_REPLAY_TRIAL_CANDIDATE_ENTRY_PATH = (
    "runtime/browser_workflows/workflows/"
    "wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502.workflow.json"
)

WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTION_PATHS = (
    "runtime/browser_runtime/workflow_replay_trial_candidate.py",
    "runtime/browser_runtime/test_workflow_replay_trial_candidate.py",
    "06_AGENTS/Browser-Workflow-Replay-Trial-Candidate.md",
    WORKFLOW_REPLAY_TRIAL_CANDIDATE_ENTRY_PATH,
)

WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTION_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_trial_candidate.py; "
    "runtime/browser_runtime/test_workflow_replay_trial_candidate.py; "
    "06_AGENTS/Browser-Workflow-Replay-Trial-Candidate.md; "
    f"{WORKFLOW_REPLAY_TRIAL_CANDIDATE_ENTRY_PATH}"
)

WORKFLOW_REPLAY_EXECUTION_APPROVAL_IDEMPOTENCY_PATHS = (
    "runtime/browser_runtime/workflow_replay_execution_approval.py",
    "runtime/browser_runtime/test_workflow_replay_execution_approval.py",
    "06_AGENTS/Browser-Workflow-Replay-Execution-Approval.md",
)

WORKFLOW_REPLAY_EXECUTION_APPROVAL_IDEMPOTENCY_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_execution_approval.py; "
    "runtime/browser_runtime/test_workflow_replay_execution_approval.py; "
    "06_AGENTS/Browser-Workflow-Replay-Execution-Approval.md"
)

WORKFLOW_REPLAY_EXECUTION_PROOF_IMPLEMENTATION_PATHS = (
    "runtime/browser_runtime/workflow_replay_execution_proof.py",
    "runtime/browser_runtime/test_workflow_replay_execution_proof.py",
    "06_AGENTS/Browser-Workflow-Replay-Execution-Proof.md",
)

WORKFLOW_REPLAY_EXECUTION_PROOF_IMPLEMENTATION_EVIDENCE_TEXT = (
    "runtime/browser_runtime/workflow_replay_execution_proof.py; "
    "runtime/browser_runtime/test_workflow_replay_execution_proof.py; "
    "06_AGENTS/Browser-Workflow-Replay-Execution-Proof.md"
)

WORKFLOW_REPLAY_EXECUTION_PROOF_SUCCESS_PATH = (
    "07_LOGS/Browser-Runs/safe-local-workflow-replay-execution-proof-20260503_success.json"
)

WORKFLOW_REPLAY_EXECUTION_PROOF_SUCCESS_EVIDENCE_TEXT = (
    "07_LOGS/Browser-Runs/safe-local-workflow-replay-execution-proof-20260503_success.json"
)

EXCALIDRAW_MCP_PROOF_PREP_PATHS = (
    "runtime/browser_runtime/excalidraw_mcp_proof_prep.py",
    "runtime/browser_runtime/test_excalidraw_mcp_proof_prep.py",
    "06_AGENTS/Excalidraw-Browser-MCP-Proof-Prep.md",
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json",
)

EXCALIDRAW_MCP_PROOF_PREP_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_mcp_proof_prep.py; "
    "runtime/browser_runtime/test_excalidraw_mcp_proof_prep.py; "
    "06_AGENTS/Excalidraw-Browser-MCP-Proof-Prep.md; "
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json"
)

EXCALIDRAW_MCP_LIVE_READINESS_PATHS = (
    "runtime/browser_runtime/excalidraw_mcp_live_readiness.py",
    "runtime/browser_runtime/test_excalidraw_mcp_live_readiness.py",
    "06_AGENTS/Excalidraw-Browser-MCP-Live-Readiness.md",
)

EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET_PATH = (
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
)

EXCALIDRAW_MCP_LIVE_READINESS_READY_PATH = (
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_ready.json"
)

EXCALIDRAW_MCP_LIVE_READINESS_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_mcp_live_readiness.py; "
    "runtime/browser_runtime/test_excalidraw_mcp_live_readiness.py; "
    "06_AGENTS/Excalidraw-Browser-MCP-Live-Readiness.md; "
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
)

EXCALIDRAW_TARGET_SETUP_INSTRUCTIONS_PATHS = (
    "runtime/browser_runtime/excalidraw_target_setup_instructions.py",
    "runtime/browser_runtime/test_excalidraw_target_setup_instructions.py",
    "06_AGENTS/Excalidraw-Local-Target-Setup-Instructions.md",
    "07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json",
)

EXCALIDRAW_TARGET_SETUP_INSTRUCTIONS_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_target_setup_instructions.py; "
    "runtime/browser_runtime/test_excalidraw_target_setup_instructions.py; "
    "06_AGENTS/Excalidraw-Local-Target-Setup-Instructions.md; "
    "07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json"
)

EXCALIDRAW_TARGET_CONTRACT_REQUEST_PATHS = (
    "runtime/browser_runtime/excalidraw_target_contract.py",
    "runtime/browser_runtime/test_excalidraw_target_contract.py",
    "06_AGENTS/Excalidraw-Local-Target-Contract.md",
    "07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json",
)

EXCALIDRAW_TARGET_CONTRACT_REQUEST_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_target_contract.py; "
    "runtime/browser_runtime/test_excalidraw_target_contract.py; "
    "06_AGENTS/Excalidraw-Local-Target-Contract.md; "
    "07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json"
)

EXCALIDRAW_TARGET_RESPONSE_INTAKE_PATHS = (
    "runtime/browser_runtime/excalidraw_target_response.py",
    "runtime/browser_runtime/test_excalidraw_target_response.py",
    "06_AGENTS/Excalidraw-Local-Target-Response-Intake.md",
    "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json",
)

EXCALIDRAW_TARGET_RESPONSE_INTAKE_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_target_response.py; "
    "runtime/browser_runtime/test_excalidraw_target_response.py; "
    "06_AGENTS/Excalidraw-Local-Target-Response-Intake.md; "
    "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json"
)

EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PATHS = (
    "runtime/browser_runtime/excalidraw_target_response_resolver.py",
    "runtime/browser_runtime/test_excalidraw_target_response_resolver.py",
    "06_AGENTS/Excalidraw-Target-Response-Latest-Resolver.md",
)

EXCALIDRAW_TARGET_RESPONSE_RESOLVER_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_target_response_resolver.py; "
    "runtime/browser_runtime/test_excalidraw_target_response_resolver.py; "
    "06_AGENTS/Excalidraw-Target-Response-Latest-Resolver.md"
)

EXCALIDRAW_READINESS_FROM_RESPONSE_PATHS = (
    "runtime/browser_runtime/excalidraw_readiness_from_response.py",
    "runtime/browser_runtime/test_excalidraw_readiness_from_response.py",
    "06_AGENTS/Excalidraw-Readiness-From-Target-Response.md",
    "07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json",
)

EXCALIDRAW_READINESS_FROM_RESPONSE_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_readiness_from_response.py; "
    "runtime/browser_runtime/test_excalidraw_readiness_from_response.py; "
    "06_AGENTS/Excalidraw-Readiness-From-Target-Response.md; "
    "07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json"
)

EXCALIDRAW_MCP_EXECUTION_APPROVAL_PATHS = (
    "runtime/browser_runtime/excalidraw_mcp_execution_approval.py",
    "runtime/browser_runtime/test_excalidraw_mcp_execution_approval.py",
    "06_AGENTS/Excalidraw-Browser-MCP-Execution-Approval.md",
)

EXCALIDRAW_MCP_EXECUTION_APPROVAL_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_mcp_execution_approval.py; "
    "runtime/browser_runtime/test_excalidraw_mcp_execution_approval.py; "
    "06_AGENTS/Excalidraw-Browser-MCP-Execution-Approval.md"
)

EXCALIDRAW_MCP_PROOF_EXECUTION_SHELL_PATHS = (
    "runtime/browser_runtime/excalidraw_mcp_proof_execution.py",
    "runtime/browser_runtime/test_excalidraw_mcp_proof_execution.py",
    "06_AGENTS/Excalidraw-Browser-MCP-Proof-Execution-Shell.md",
)

EXCALIDRAW_MCP_PROOF_EXECUTION_SHELL_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_mcp_proof_execution.py; "
    "runtime/browser_runtime/test_excalidraw_mcp_proof_execution.py; "
    "06_AGENTS/Excalidraw-Browser-MCP-Proof-Execution-Shell.md"
)

EXCALIDRAW_LIVE_CHAIN_READINESS_PATHS = (
    "runtime/browser_runtime/excalidraw_live_chain_readiness.py",
    "runtime/browser_runtime/test_excalidraw_live_chain_readiness.py",
    "06_AGENTS/Excalidraw-Live-Chain-Readiness.md",
)

EXCALIDRAW_LIVE_CHAIN_READINESS_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_live_chain_readiness.py; "
    "runtime/browser_runtime/test_excalidraw_live_chain_readiness.py; "
    "06_AGENTS/Excalidraw-Live-Chain-Readiness.md"
)

EXCALIDRAW_PUBLIC_LIVE_BROWSER_PROOF_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_live_browser_proof.py; "
    "runtime/browser_runtime/test_excalidraw_live_browser_proof.py; "
    "07_LOGS/Browser-Runs/excalidraw_live_proof_*.json; "
    "07_LOGS/Browser-Runs/excalidraw_live_proof_*.png"
)

EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_public_drawing_approval.py; "
    "runtime/browser_runtime/test_excalidraw_public_drawing_approval.py; "
    "06_AGENTS/Excalidraw-Public-Browser-Drawing-Proof-Approval.md; "
    "07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals/*.json"
)

EXCALIDRAW_PUBLIC_DRAWING_PROOF_EVIDENCE_TEXT = (
    "runtime/browser_runtime/excalidraw_public_drawing_proof.py; "
    "runtime/browser_runtime/test_excalidraw_public_drawing_proof.py; "
    "06_AGENTS/Excalidraw-Public-Browser-Drawing-Proof-Run.md; "
    "07_LOGS/Browser-Runs/excalidraw_public_drawing_proof_*.json; "
    "07_LOGS/Browser-Runs/excalidraw_public_drawing_proof_*.png; "
    "07_LOGS/Agent-Activity/_excalidraw_public_drawing_runs/*.json; "
    "07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals/_execution_markers/*.json"
)

BROWSER_RUNTIME_COMPLETION_ESTIMATE_PATHS = (
    "runtime/browser_runtime/completion_estimate.py",
    "runtime/browser_runtime/test_completion_estimate.py",
    "06_AGENTS/Browser-Runtime-Completion-Estimate.md",
)

BROWSER_RUNTIME_COMPLETION_ESTIMATE_EVIDENCE_TEXT = (
    "runtime/browser_runtime/completion_estimate.py; "
    "runtime/browser_runtime/test_completion_estimate.py; "
    "06_AGENTS/Browser-Runtime-Completion-Estimate.md"
)

BROWSER_RUNTIME_PRODUCTION_COMPLETE_EVIDENCE_TEXT = (
    "runtime/browser_runtime/production_closeout.py; "
    "runtime/browser_runtime/test_production_closeout.py; "
    "07_LOGS/Studio-Graph-Views/*browser-runtime-production-complete.json"
)

STUDIO_BROWSER_RUNTIME_OPERATOR_UI_READINESS_PATHS = (
    "runtime/studio/browser_runtime_operator_ui_readiness.py",
    "runtime/studio/test_browser_runtime_operator_ui_readiness.py",
    "06_AGENTS/Studio-Browser-Runtime-Operator-UI-Readiness.md",
)

STUDIO_BROWSER_RUNTIME_OPERATOR_UI_READINESS_EVIDENCE_TEXT = (
    "runtime/studio/browser_runtime_operator_ui_readiness.py; "
    "runtime/studio/test_browser_runtime_operator_ui_readiness.py; "
    "06_AGENTS/Studio-Browser-Runtime-Operator-UI-Readiness.md"
)

STUDIO_BROWSER_RUNTIME_NATIVE_PANEL_EVIDENCE_PATHS = (
    "runtime/studio/browser_runtime_operator_ui_readiness.py",
    "runtime/studio/test_browser_runtime_operator_ui_readiness.py",
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-native-shell-panel-static-qa.md",
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-qa-runner-static-qa.md",
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-browser-qa.md",
)

STUDIO_BROWSER_RUNTIME_NATIVE_PANEL_EVIDENCE_TEXT = (
    "runtime/studio/browser_runtime_operator_ui_readiness.py; "
    "runtime/studio/test_browser_runtime_operator_ui_readiness.py; "
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-native-shell-panel-static-qa.md; "
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-qa-runner-static-qa.md; "
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-browser-qa.md"
)

CDP_OPERATIONAL_EVIDENCE_PATHS = (
    "runtime/browser_runtime/cdp_live.py",
    "runtime/browser_runtime/cdp_executor_spec.py",
    "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-bounded-live-executor-implementation.md",
    "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-operational-environment-activation.md",
)

CDP_OPERATIONAL_EVIDENCE_TEXT = (
    "runtime/browser_runtime/cdp_live.py; runtime/browser_runtime/cdp_executor_spec.py; "
    "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-bounded-live-executor-implementation.md; "
    "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-operational-environment-activation.md"
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _exists(vault: Path, relative_path: str) -> bool:
    return (vault / relative_path).exists()


def _all_exist(vault: Path, relative_paths: tuple[str, ...]) -> bool:
    return all(_exists(vault, path) for path in relative_paths)


def _json_record(vault: Path, relative_path: str) -> dict[str, Any] | None:
    try:
        return json.loads((vault / relative_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _latest_json_record(vault: Path, relative_glob: str) -> dict[str, Any] | None:
    try:
        candidates = sorted(
            vault.glob(relative_glob),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return None
    for candidate in candidates:
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _json_records_newest_first(vault: Path, relative_glob: str) -> tuple[dict[str, Any], ...]:
    try:
        candidates = sorted(
            vault.glob(relative_glob),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return ()
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            record = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(record, dict):
            records.append(record)
    return tuple(records)


def _safety_flags_ok(record: dict[str, Any] | None) -> bool:
    if not isinstance(record, dict):
        return False
    governance = record.get("governance")
    if not isinstance(governance, dict):
        return False
    forbidden_true_keys = (
        "canonical_writeback",
        "skill_activation",
        "trusted_skill_write",
        "siteops_skill_card_write",
        "real_profile_allowed",
        "real_profile_used",
        "credentials_allowed",
        "credentials_used",
        "cookies_exported",
        "browser_history_imported",
        "cdp_connection_used",
        "browser_harness_used",
        "browser_use_cli_used",
        "public_tunnel_used",
        "agent_bus_enqueue",
        "provider_call",
        "gate_policy_mutation",
    )
    if any(governance.get(key) is True for key in forbidden_true_keys):
        return False
    server = record.get("server")
    if isinstance(server, dict) and server.get("public_tunnel") is True:
        return False
    return True


def _mvp_safety_ok(vault: Path) -> bool:
    return all(_safety_flags_ok(_json_record(vault, path)) for path in MVP_SAFE_RUN_LOGS)


def _nonempty_file(vault: Path, relative_path: str) -> bool:
    path = vault / relative_path
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


@dataclass(frozen=True)
class BrowserRuntimeCompletionItem:
    area: str
    status: str
    evidence: str
    complete_for_bounded_mvp: bool
    complete_for_production: bool
    notes: str = ""

    def validate(self) -> None:
        if not self.area:
            raise ValueError("completion item area is required")
        if self.status not in {
            "complete",
            "complete_targeted",
            "complete_targeted_help_probe_no_browser",
            "complete_targeted_safe_url_design_no_execution",
            "complete_targeted_safe_url_open_no_account",
            "complete_targeted_blocked_current_target",
            "partial",
            "missing",
            "blocked",
            "blocked_unavailable",
            "implementation_ready_live_blocked",
            "not_built",
            "deferred",
            "planned",
        }:
            raise ValueError("invalid Browser Runtime completion item status")
        if not self.evidence:
            raise ValueError("completion item evidence is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class BrowserRuntimeCompletionStatus:
    generated_at: str
    overall_status: str
    bounded_mvp_done: bool
    production_feature_done: bool
    next_recommended_pass: str
    blocked_reasons: tuple[str, ...]
    items: tuple[BrowserRuntimeCompletionItem, ...]
    read_only: bool = True
    writes_status_artifact: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    blocked_effects: tuple[str, ...] = BROWSER_RUNTIME_BLOCKED_EFFECTS

    @property
    def item_count(self) -> int:
        return len(self.items)

    def validate(self) -> None:
        if self.overall_status not in BROWSER_RUNTIME_COMPLETION_STATUSES:
            raise ValueError("invalid Browser Runtime overall_status")
        if self.production_feature_done and self.overall_status != BROWSER_RUNTIME_OVERALL_COMPLETE:
            raise ValueError("production_feature_done requires complete overall_status")
        if self.production_feature_done and not self.bounded_mvp_done:
            raise ValueError("production feature cannot be done before bounded MVP")
        if not self.next_recommended_pass:
            raise ValueError("next_recommended_pass is required")
        for item in self.items:
            item.validate()
        if not self.read_only:
            raise ValueError("Browser Runtime completion status must remain read-only")
        if self.writes_status_artifact:
            raise ValueError("Browser Runtime completion status cannot write status artifacts")
        if self.browser_launch_attempted:
            raise ValueError("completion status cannot launch a browser")
        if self.cdp_connection_attempted:
            raise ValueError("completion status cannot connect to CDP")
        if self.real_profile_access_attempted:
            raise ValueError("completion status cannot access real profiles")
        if self.credential_or_cookie_read_attempted:
            raise ValueError("completion status cannot read credentials or cookies")
        if self.browser_harness_used:
            raise ValueError("completion status cannot use Browser Harness")
        if self.browser_use_cli_live_used:
            raise ValueError("completion status cannot run Browser Use CLI live")
        if self.trusted_skill_write_attempted:
            raise ValueError("completion status cannot write trusted skills")
        if self.skill_activation_attempted:
            raise ValueError("completion status cannot activate skills")
        if self.agent_bus_enqueue_attempted:
            raise ValueError("completion status cannot enqueue Agent Bus tasks")
        if self.provider_call_attempted:
            raise ValueError("completion status cannot call providers")
        if self.gate_mutation_attempted:
            raise ValueError("completion status cannot mutate Gate policy")
        if self.canonical_writeback_attempted:
            raise ValueError("completion status cannot write canonical state")
        if set(self.blocked_effects) != set(BROWSER_RUNTIME_BLOCKED_EFFECTS):
            raise ValueError("Browser Runtime completion status must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "overall_status": self.overall_status,
            "bounded_mvp_done": self.bounded_mvp_done,
            "production_feature_done": self.production_feature_done,
            "next_recommended_pass": self.next_recommended_pass,
            "blocked_reasons": list(self.blocked_reasons),
            "item_count": self.item_count,
            "items": [item.to_dict() for item in self.items],
            "read_only": self.read_only,
            "writes_status_artifact": self.writes_status_artifact,
            "browser_launch_attempted": self.browser_launch_attempted,
            "cdp_connection_attempted": self.cdp_connection_attempted,
            "real_profile_access_attempted": self.real_profile_access_attempted,
            "credential_or_cookie_read_attempted": self.credential_or_cookie_read_attempted,
            "browser_harness_used": self.browser_harness_used,
            "browser_use_cli_live_used": self.browser_use_cli_live_used,
            "trusted_skill_write_attempted": self.trusted_skill_write_attempted,
            "skill_activation_attempted": self.skill_activation_attempted,
            "agent_bus_enqueue_attempted": self.agent_bus_enqueue_attempted,
            "provider_call_attempted": self.provider_call_attempted,
            "gate_mutation_attempted": self.gate_mutation_attempted,
            "canonical_writeback_attempted": self.canonical_writeback_attempted,
            "blocked_effects": list(self.blocked_effects),
        }


def _build_mvp_items(vault: Path) -> list[BrowserRuntimeCompletionItem]:
    items: list[BrowserRuntimeCompletionItem] = []
    for area, paths in MVP_REQUIRED_PATHS.items():
        complete = _all_exist(vault, paths)
        status = "complete" if complete else "missing"
        notes = "All required evidence paths exist." if complete else "Missing one or more required evidence paths."
        if area == "selector_click_hardening" and complete:
            status = "complete_targeted"
            notes = "Selector click hardening exists; screenshot hardening is tracked separately."
        items.append(
            BrowserRuntimeCompletionItem(
                area=f"bounded_mvp:{area}",
                status=status,
                evidence="; ".join(paths),
                complete_for_bounded_mvp=complete,
                complete_for_production=False,
                notes=notes,
            )
        )

    safety_ok = _mvp_safety_ok(vault)
    items.append(
        BrowserRuntimeCompletionItem(
            area="bounded_mvp:safety_flags",
            status="complete" if safety_ok else "blocked",
            evidence="; ".join(MVP_SAFE_RUN_LOGS),
            complete_for_bounded_mvp=safety_ok,
            complete_for_production=False,
            notes="MVP run logs keep forbidden profile/credential/CDP/trusted-write/canonical flags false."
            if safety_ok
            else "One or more MVP run logs are missing or unsafe.",
        )
    )

    screenshot_ok = _nonempty_file(
        vault,
        "07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_screenshot.png",
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="bounded_mvp:nonempty_screenshot_artifact",
            status="complete" if screenshot_ok else "blocked",
            evidence="07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_screenshot.png",
            complete_for_bounded_mvp=screenshot_ok,
            complete_for_production=False,
            notes="Screenshot evidence exists and is non-empty." if screenshot_ok else "Screenshot evidence missing or empty.",
        )
    )
    return items


def _cdp_operational_activation_ok(vault: Path) -> bool:
    """Return true when bounded live CDP implementation and activation evidence exist.

    This is a read-only evidence check. It does not import CDP modules, launch a
    browser, connect to a socket, inspect approval artifacts, or read any
    temporary proof directory outside the vault.
    """
    if not _all_exist(vault, CDP_OPERATIONAL_EVIDENCE_PATHS):
        return False
    activation_log = vault / "07_LOGS/Build-Logs/2026-05-02-ChaseOS-hermes-browser-cdp-operational-environment-activation.md"
    try:
        text = activation_log.read_text(encoding="utf-8")
    except OSError:
        return False
    required_markers = (
        "status: implemented_cdp_read_only_proof_complete",
        "approval_consumed: True",
        "idempotency_marker_written: True",
        "browser_launch_attempted: True",
        "cdp_connection_attempted: True",
        "isolated throwaway browser profile",
        "canonical writeback",
    )
    return all(marker in text for marker in required_markers)


def _browser_use_cli_validation_preflight_ok(vault: Path) -> bool:
    """Return true when the read-only Browser Use CLI validation preflight exists."""
    return _all_exist(vault, BROWSER_USE_CLI_VALIDATION_PREFLIGHT_PATHS)


def _browser_use_cli_live_unavailable_evidence_ok(vault: Path) -> bool:
    """Return true when live CLI validation was attempted as a preflight and blocked unavailable."""
    path = vault / BROWSER_USE_CLI_LIVE_UNAVAILABLE_EVIDENCE_PATH
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        payload.get("status") == "blocked_browser_use_cli_unavailable"
        and payload.get("executable_found") is False
        and payload.get("browser_use_cli_live_run_attempted") is False
        and payload.get("browser_launch_attempted") is False
        and payload.get("real_profile_access_attempted") is False
        and payload.get("credential_or_cookie_read_attempted") is False
        and payload.get("canonical_writeback_attempted") is False
    )


def _browser_use_cli_external_validation_ok(vault: Path) -> bool:
    """Return true when Browser Use CLI help-surface validation succeeded without browser execution."""
    if not _all_exist(
        vault,
        (
            "runtime/browser_runtime/browser_use_cli_external_validation.py",
            "runtime/browser_runtime/test_browser_use_cli_external_validation.py",
            BROWSER_USE_CLI_EXTERNAL_VALIDATION_EVIDENCE_PATH,
        ),
    ):
        return False
    payload = _json_record(vault, BROWSER_USE_CLI_EXTERNAL_VALIDATION_EVIDENCE_PATH)
    return (
        payload.get("status") == "browser_use_cli_external_validation_complete_help_probe_no_browser"
        and payload.get("help_probe_attempted") is True
        and payload.get("help_probe_exit_code") == 0
        and payload.get("expected_help_surface_present") is True
        and payload.get("browser_command_execution_attempted") is False
        and payload.get("browser_launch_attempted") is False
        and payload.get("real_profile_access_attempted") is False
        and payload.get("credential_or_cookie_read_attempted") is False
        and payload.get("public_tunnel_attempted") is False
        and payload.get("cloud_api_call_attempted") is False
        and payload.get("llm_or_provider_call_attempted") is False
        and payload.get("canonical_writeback_attempted") is False
    )


def _browser_use_cli_safe_url_design_ok(vault: Path) -> bool:
    """Return true when no-execution safe-URL validation design is ready."""
    if not _all_exist(
        vault,
        (
            "runtime/browser_runtime/browser_use_cli_safe_url_validation_design.py",
            "runtime/browser_runtime/test_browser_use_cli_safe_url_validation_design.py",
            BROWSER_USE_CLI_SAFE_URL_DESIGN_EVIDENCE_PATH,
        ),
    ):
        return False
    payload = _json_record(vault, BROWSER_USE_CLI_SAFE_URL_DESIGN_EVIDENCE_PATH)
    return (
        payload.get("status") == "browser_use_cli_safe_url_validation_design_ready_no_execution"
        and payload.get("target_url") == "http://127.0.0.1:8770/"
        and payload.get("browser_use_package_download_complete") is True
        and payload.get("browser_dependency_download_verified") is False
        and payload.get("browser_dependency_install_command_run") is False
        and payload.get("allowed_subcommand") == "open"
        and payload.get("browser_dependency_download_attempted") is False
        and payload.get("browser_command_execution_attempted") is False
        and payload.get("browser_launch_attempted") is False
        and payload.get("real_profile_access_attempted") is False
        and payload.get("credential_or_cookie_read_attempted") is False
        and payload.get("public_tunnel_attempted") is False
        and payload.get("canonical_writeback_attempted") is False
    )


def _browser_use_cli_safe_url_run_ok(vault: Path) -> bool:
    """Return true when no-account Browser Use safe-URL open validation succeeded."""
    if not _all_exist(
        vault,
        (
            "runtime/browser_runtime/browser_use_cli_safe_url_validation_run.py",
            "runtime/browser_runtime/test_browser_use_cli_safe_url_validation_run.py",
            BROWSER_USE_CLI_SAFE_URL_RUN_EVIDENCE_PATH,
        ),
    ):
        return False
    payload = _json_record(vault, BROWSER_USE_CLI_SAFE_URL_RUN_EVIDENCE_PATH)
    return (
        payload.get("status") == "browser_use_cli_safe_url_validation_run_complete"
        and payload.get("target_url") == "http://127.0.0.1:8770/"
        and payload.get("browser_use_cli_open_attempted") is True
        and payload.get("browser_use_cli_exit_code") == 0
        and payload.get("browser_use_open_succeeded") is True
        and payload.get("browser_use_cli_close_attempted") is True
        and payload.get("browser_use_cli_close_exit_code") == 0
        and payload.get("browser_use_close_succeeded") is True
        and payload.get("browser_dependency_install_command_run") is False
        and payload.get("dependency_install_command_attempted") is False
        and payload.get("real_profile_access_attempted") is False
        and payload.get("credential_or_cookie_read_attempted") is False
        and payload.get("cookie_export_attempted") is False
        and payload.get("public_tunnel_attempted") is False
        and payload.get("cloud_api_call_attempted") is False
        and payload.get("llm_or_provider_call_attempted") is False
        and payload.get("agent_bus_enqueue_attempted") is False
        and payload.get("gate_mutation_attempted") is False
        and payload.get("canonical_writeback_attempted") is False
    )


def _vincisos_product_ui_target_probe_ok(vault: Path) -> bool:
    """Return true when the no-browser product UI target probe surface exists."""
    return _all_exist(vault, VINCISOS_PRODUCT_UI_TARGET_PROBE_PATHS)


def _vincisos_product_ui_launch_readiness_ok(vault: Path) -> bool:
    """Return true when the no-start product UI launch-readiness surface exists."""
    return _all_exist(vault, VINCISOS_PRODUCT_UI_LAUNCH_READINESS_PATHS)


def _vincisos_product_ui_browser_proof_ok(vault: Path) -> bool:
    """Return true when the isolated product UI browser proof evidence is present and safe."""
    if not _all_exist(vault, VINCISOS_PRODUCT_UI_BROWSER_PROOF_PATHS):
        return False
    if not _nonempty_file(vault, "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png"):
        return False
    record = _json_record(vault, "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json")
    if not _safety_flags_ok(record):
        return False
    if record.get("status") != "succeeded":
        return False
    if record.get("provider") != "codex-in-app-browser":
        return False
    if record.get("provider_backend") != "iab":
        return False
    if record.get("url") != "http://127.0.0.1:8770/":
        return False
    browser_state = record.get("browser_state")
    if not isinstance(browser_state, dict):
        return False
    selector_counts = browser_state.get("selector_counts")
    if not isinstance(selector_counts, dict):
        return False
    required_unique = (
        "root",
        "safe_mode_banner",
        "panel_overview",
        "panel_approvals",
        "panel_workflow",
        "tab_overview",
        "tab_approvals",
        "tab_workflow",
        "task_table",
        "approval_table",
        "action_status",
        "harmless_action",
    )
    return (
        all(selector_counts.get(key) == 1 for key in required_unique)
        and selector_counts.get("task_rows") == 3
        and selector_counts.get("approval_rows") == 2
        and browser_state.get("post_action_status") == "Panel inspected in safe mode."
    )


def _browser_harness_adoption_decision_ok(vault: Path) -> bool:
    """Return true when the Browser Harness adoption decision is recorded."""
    return _all_exist(vault, BROWSER_HARNESS_ADOPTION_DECISION_PATHS)


def _browser_workflow_cache_foundation_ok(vault: Path) -> bool:
    """Return true when the inactive workflow cache foundation exists."""
    if not _all_exist(vault, BROWSER_WORKFLOW_CACHE_FOUNDATION_PATHS):
        return False
    record = _json_record(vault, "runtime/browser_workflows/metadata.json")
    if not isinstance(record, dict):
        return False
    forbidden_truthy = (
        "activation_allowed",
        "replay_allowed",
        "trusted_write_allowed",
        "external_code_copied",
    )
    return (
        record.get("record_type") == "browser_workflow_cache_metadata"
        and record.get("schema_version") == "browser.workflow_cache.v1"
        and all(record.get(key) is False for key in forbidden_truthy)
    )


def _workflow_replay_executor_design_preflight_ok(vault: Path) -> bool:
    """Return true when the no-execution replay executor design preflight exists."""
    return _all_exist(vault, WORKFLOW_REPLAY_EXECUTOR_DESIGN_PREFLIGHT_PATHS)


def _workflow_replay_executor_implementation_request_ok(vault: Path) -> bool:
    """Return true when the no-write replay executor implementation request exists."""
    return _all_exist(vault, WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_REQUEST_PATHS)


def _workflow_replay_executor_implementation_approval_ok(vault: Path) -> bool:
    """Return true when the no-write replay executor implementation approval exists."""
    return _all_exist(vault, WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_APPROVAL_PATHS)


def _workflow_replay_executor_implementation_ok(vault: Path) -> bool:
    """Return true when the disabled replay executor implementation exists."""
    return _all_exist(vault, WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_PATHS)


def _workflow_replay_execution_readiness_preflight_ok(vault: Path) -> bool:
    """Return true when the no-execution replay readiness preflight exists."""
    return _all_exist(vault, WORKFLOW_REPLAY_EXECUTION_READINESS_PREFLIGHT_PATHS)


def _workflow_replay_trial_candidate_selection_ok(vault: Path) -> bool:
    """Return true when a reviewed local workflow trial candidate is selected."""
    if not _all_exist(vault, WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTION_PATHS):
        return False
    entry = _json_record(vault, WORKFLOW_REPLAY_TRIAL_CANDIDATE_ENTRY_PATH)
    metadata = _json_record(vault, "runtime/browser_workflows/metadata.json")
    if not isinstance(entry, dict) or not isinstance(metadata, dict):
        return False
    if (
        entry.get("record_type") != "browser_workflow_cache_entry"
        or entry.get("schema_version") != "browser.workflow_cache.v1"
        or entry.get("workflow_id") != WORKFLOW_REPLAY_TRIAL_CANDIDATE_WORKFLOW_ID
        or entry.get("status") != "reviewed_for_trial"
        or entry.get("source_run_id") != "vincisos_product_ui_browser_proof_20260502_success"
        or entry.get("source_run_log_path")
        != "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json"
        or entry.get("source_url") != "http://127.0.0.1:8770/"
        or entry.get("replay_allowed") is not True
        or entry.get("activation_allowed") is not False
        or entry.get("trusted_write_allowed") is not False
        or entry.get("external_code_copied") is not False
        or entry.get("review_required") is not True
    ):
        return False
    allowed_domains = entry.get("allowed_domains")
    if allowed_domains != ["127.0.0.1"]:
        return False
    steps = entry.get("steps")
    if not isinstance(steps, list) or not steps:
        return False
    forbidden_actions = {
        "credential_field_fill",
        "cookie_export",
        "form_submit",
        "payment_submit",
        "account_mutation",
        "download_private_file",
        "upload_file",
    }
    if any(isinstance(step, dict) and step.get("action_type") in forbidden_actions for step in steps):
        return False
    if (
        metadata.get("record_type") != "browser_workflow_cache_metadata"
        or metadata.get("schema_version") != "browser.workflow_cache.v1"
        or metadata.get("activation_allowed") is not False
        or metadata.get("replay_allowed") is not False
        or metadata.get("trusted_write_allowed") is not False
        or metadata.get("external_code_copied") is not False
    ):
        return False
    workflows = metadata.get("workflows")
    if not isinstance(workflows, list):
        return False
    for item in workflows:
        if not isinstance(item, dict):
            continue
        if item.get("workflow_id") == WORKFLOW_REPLAY_TRIAL_CANDIDATE_WORKFLOW_ID:
            return (
                item.get("status") == "reviewed_for_trial"
                and item.get("replay_allowed") is True
                and item.get("activation_allowed") is False
                and item.get("trusted_write_allowed") is False
                and item.get("external_code_copied") is False
                and item.get("trial_candidate") is True
            )
    return False


def _workflow_replay_execution_approval_idempotency_ok(vault: Path) -> bool:
    """Return true when the no-write replay execution approval/idempotency contract exists."""
    return _all_exist(vault, WORKFLOW_REPLAY_EXECUTION_APPROVAL_IDEMPOTENCY_PATHS)


def _workflow_replay_execution_proof_implementation_ok(vault: Path) -> bool:
    """Return true when the safe-local replay proof runner exists."""
    return _all_exist(vault, WORKFLOW_REPLAY_EXECUTION_PROOF_IMPLEMENTATION_PATHS)


def _workflow_replay_execution_proof_success_ok(vault: Path) -> bool:
    """Return true when bounded local replay proof success evidence exists."""
    payload = _json_record(vault, WORKFLOW_REPLAY_EXECUTION_PROOF_SUCCESS_PATH)
    return (
        isinstance(payload, dict)
        and payload.get("status") == "workflow_replay_execution_proof_complete"
        and payload.get("allow_real_profile") is False
        and payload.get("allow_credentials") is False
        and payload.get("trusted_skill_write_allowed") is False
        and payload.get("activation_allowed") is False
        and payload.get("canonical_writeback_allowed") is False
        and payload.get("external_code_copied") is False
        and payload.get("workflow_use_reference_only") is True
        and payload.get("browser_harness_reference_only") is True
    )


def _excalidraw_mcp_proof_prep_ok(vault: Path) -> bool:
    """Return true when the no-execution Excalidraw proof prep packet exists and is safe."""
    if not _all_exist(vault, EXCALIDRAW_MCP_PROOF_PREP_PATHS):
        return False
    payload = _json_record(vault, "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json")
    if not isinstance(payload, dict):
        return False
    forbidden_false = (
        "live_proof_allowed_in_this_pass",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_server_invoked",
        "mcp_tool_call_attempted",
        "network_navigation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    return (
        payload.get("record_type") == "excalidraw_local_browser_mcp_proof_prep"
        and payload.get("schema_version") == "browser.excalidraw_mcp_proof_prep.v1"
        and payload.get("status") == "excalidraw_local_browser_mcp_proof_prep_ready_no_execution"
        and payload.get("prep_artifact_written") is True
        and payload.get("run_slug") == "excalidraw-local-browser-mcp-proof-20260503"
        and all(payload.get(key) is False for key in forbidden_false)
    )


def _excalidraw_mcp_live_readiness_record(vault: Path) -> dict[str, Any] | None:
    for relative_path in (
        EXCALIDRAW_MCP_LIVE_READINESS_READY_PATH,
        EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET_PATH,
    ):
        payload = _json_record(vault, relative_path)
        if isinstance(payload, dict):
            return payload
    return None


def _excalidraw_mcp_live_readiness_status(vault: Path) -> str:
    """Return current no-execution Excalidraw live-readiness evidence status."""
    if not _all_exist(vault, EXCALIDRAW_MCP_LIVE_READINESS_PATHS):
        return "missing"
    payload = _excalidraw_mcp_live_readiness_record(vault)
    if not isinstance(payload, dict):
        return "missing"
    forbidden_false = (
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_server_invoked",
        "mcp_tool_call_attempted",
        "network_navigation_attempted",
        "dependency_install_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    if not (
        payload.get("record_type") == "excalidraw_local_browser_mcp_live_readiness"
        and payload.get("schema_version") == "browser.excalidraw_mcp_live_readiness.v1"
        and payload.get("readiness_artifact_written") is True
        and payload.get("prep_evidence_ready") is True
        and payload.get("browser_controller_ready") is True
        and all(payload.get(key) is False for key in forbidden_false)
    ):
        return "unsafe_or_invalid"
    if payload.get("status") == "excalidraw_local_browser_mcp_live_readiness_ready_no_execution":
        return "ready_no_execution"
    if payload.get("status") == "blocked_excalidraw_live_readiness_missing_local_target":
        blockers = payload.get("blockers")
        if isinstance(blockers, list) and "local_excalidraw_target_url_not_provided" in blockers:
            return "blocked_missing_local_target"
    return "unsafe_or_invalid"


def _excalidraw_target_setup_instructions_ok(vault: Path) -> bool:
    """Return true when no-execution Excalidraw target setup handoff exists."""
    if not _all_exist(vault, EXCALIDRAW_TARGET_SETUP_INSTRUCTIONS_PATHS):
        return False
    payload = _json_record(
        vault,
        "07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json",
    )
    if not isinstance(payload, dict):
        return False
    forbidden_false = (
        "dependency_install_attempted",
        "mcp_server_start_attempted",
        "mcp_tool_call_attempted",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "network_navigation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    return (
        payload.get("record_type") == "excalidraw_local_target_setup_instructions"
        and payload.get("schema_version") == "browser.excalidraw_target_setup_instructions.v1"
        and payload.get("status") == "excalidraw_local_target_setup_instructions_ready_no_execution"
        and payload.get("setup_artifact_written") is True
        and payload.get("previous_readiness_safe") is True
        and payload.get("live_proof_command_not_authorized")
        and all(payload.get(key) is False for key in forbidden_false)
    )


def _excalidraw_target_contract_request_ok(vault: Path) -> bool:
    """Return true when a no-execution Excalidraw target request exists."""
    if not _all_exist(vault, EXCALIDRAW_TARGET_CONTRACT_REQUEST_PATHS):
        return False
    payload = _json_record(
        vault,
        "07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json",
    )
    if not isinstance(payload, dict):
        return False
    forbidden_false = (
        "dependency_install_attempted",
        "server_start_attempted",
        "network_probe_attempted",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_invocation_attempted",
        "mcp_tool_call_attempted",
        "target_navigation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    return (
        payload.get("record_type") == "excalidraw_local_target_contract"
        and payload.get("schema_version") == "browser.excalidraw_target_contract.v1"
        and payload.get("status") == "excalidraw_local_target_contract_request_ready_no_execution"
        and payload.get("contract_artifact_written") is True
        and payload.get("target_url") == ""
        and all(payload.get(key) is False for key in forbidden_false)
    )


def _excalidraw_target_response_intake_ok(vault: Path) -> bool:
    """Return true when no-execution Excalidraw target response intake exists."""
    if not _all_exist(vault, EXCALIDRAW_TARGET_RESPONSE_INTAKE_PATHS):
        return False
    payload = _json_record(
        vault,
        "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json",
    )
    if not isinstance(payload, dict):
        return False
    forbidden_false = (
        "dependency_install_attempted",
        "server_start_attempted",
        "network_probe_attempted",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_invocation_attempted",
        "mcp_tool_call_attempted",
        "target_navigation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    return (
        payload.get("record_type") == "excalidraw_local_target_response"
        and payload.get("schema_version") == "browser.excalidraw_target_response.v1"
        and payload.get("status") == "excalidraw_local_target_response_pending_external_runtime"
        and payload.get("response_artifact_written") is True
        and payload.get("target_url") == ""
        and all(payload.get(key) is False for key in forbidden_false)
    )


def _excalidraw_target_response_resolver_ok(vault: Path) -> bool:
    """Return true when the no-execution latest target-response resolver exists."""
    return _all_exist(vault, EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PATHS)


def _excalidraw_readiness_from_response_ok(vault: Path) -> bool:
    """Return true when no-execution response-to-readiness bridge evidence exists."""
    if not _all_exist(vault, EXCALIDRAW_READINESS_FROM_RESPONSE_PATHS):
        return False
    payload = _json_record(
        vault,
        "07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json",
    )
    if not isinstance(payload, dict):
        return False
    forbidden_false = (
        "dependency_install_attempted",
        "server_start_attempted",
        "network_probe_attempted",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_invocation_attempted",
        "mcp_tool_call_attempted",
        "target_navigation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    blockers = payload.get("blockers")
    return (
        payload.get("record_type") == "excalidraw_readiness_from_target_response"
        and payload.get("schema_version") == "browser.excalidraw_readiness_from_response.v1"
        and payload.get("status") == "blocked_excalidraw_readiness_from_response_pending_external_runtime"
        and payload.get("bridge_artifact_written") is True
        and payload.get("source_response_status") == "excalidraw_local_target_response_pending_external_runtime"
        and payload.get("target_url") == ""
        and isinstance(blockers, list)
        and "excalidraw_target_response_pending_external_runtime" in blockers
        and all(payload.get(key) is False for key in forbidden_false)
    )


def _excalidraw_mcp_execution_approval_ok(vault: Path) -> bool:
    """Return true when the no-write Excalidraw execution approval contract exists."""
    return _all_exist(vault, EXCALIDRAW_MCP_EXECUTION_APPROVAL_PATHS)


def _excalidraw_mcp_proof_execution_shell_ok(vault: Path) -> bool:
    """Return true when the fail-closed Excalidraw proof execution shell exists."""
    return _all_exist(vault, EXCALIDRAW_MCP_PROOF_EXECUTION_SHELL_PATHS)


def _excalidraw_live_chain_readiness_ok(vault: Path) -> bool:
    """Return true when the no-execution Excalidraw live-chain readiness reporter exists."""
    return _all_exist(vault, EXCALIDRAW_LIVE_CHAIN_READINESS_PATHS)


def _excalidraw_public_live_browser_proof_payload_ok(vault: Path, payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    screenshot_path = payload.get("screenshot_path")
    if not isinstance(screenshot_path, str) or not _nonempty_file(vault, screenshot_path):
        return False
    authority = payload.get("authority")
    if not isinstance(authority, dict):
        return False
    required_authority_true = (
        "navigates_to_excalidraw_com",
        "env_var_required",
        "headless_browser_only",
        "no_login_profile_cookies",
        "no_cdp_raw_manipulation",
        "no_browser_use_cli",
        "screenshot_written_to_logs",
        "no_vault_markdown_writes",
        "no_agent_bus_writes",
        "no_gate_mutation",
        "no_canonical_mutation",
        "no_provider_calls",
    )
    if any(authority.get(key) is not True for key in required_authority_true if key != "env_var_required"):
        return False
    if authority.get("env_var_required") is not False:
        return False
    if not (
        authority.get("target_registered_in_chaseos") is True
        or authority.get("target_hardcoded") is True
    ):
        return False
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        return False
    required_checks = {
        "navigation_succeeded",
        "title_matches_excalidraw",
        "canvas_element_present",
        "screenshot_captured",
    }
    passed_checks = {
        check.get("name")
        for check in checks
        if isinstance(check, dict) and check.get("ok") is True
    }
    return (
        payload.get("ok") is True
        and payload.get("version") == "browser.excalidraw_live_browser_proof.v1"
        and payload.get("status") == "excalidraw_live_browser_proof_complete"
        and payload.get("target_url") == "https://excalidraw.com"
        and payload.get("canvas_found") is True
        and "excalidraw" in str(payload.get("page_title") or "").lower()
        and not payload.get("blockers")
        and required_checks.issubset(passed_checks)
    )


def _excalidraw_public_live_browser_proof_ok(vault: Path) -> bool:
    """Return true when public Excalidraw browser reachability proof exists."""
    if not _all_exist(
        vault,
        (
            "runtime/browser_runtime/excalidraw_live_browser_proof.py",
            "runtime/browser_runtime/test_excalidraw_live_browser_proof.py",
        ),
    ):
        return False
    return any(
        _excalidraw_public_live_browser_proof_payload_ok(vault, payload)
        for payload in _json_records_newest_first(
            vault,
            "07_LOGS/Browser-Runs/excalidraw_live_proof_*.json",
        )
    )


def _excalidraw_public_drawing_approval_payload_ok(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    denied_false = (
        "execution_allowed_in_this_pass",
        "browser_launch_attempted",
        "target_navigation_attempted",
        "drawing_action_attempted",
        "mcp_invocation_attempted",
        "mcp_tool_call_attempted",
        "screenshot_attempted",
        "browser_run_log_written",
        "agent_activity_log_written",
        "draft_skill_written",
        "untrusted_candidate_written",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "browser_history_import_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "shell_execution_from_browser_runtime_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    return (
        payload.get("record_type") == "excalidraw_public_browser_drawing_proof_approval"
        and payload.get("schema_version") == "browser.excalidraw_public_drawing_approval.v1"
        and payload.get("status")
        == "excalidraw_public_browser_drawing_proof_approval_written_no_execution"
        and payload.get("target_registry_id") == "excalidraw"
        and payload.get("target_url") == "https://excalidraw.com"
        and payload.get("approval_artifact_written") is True
        and payload.get("future_single_run_approved") is True
        and bool(payload.get("source_reachability_evidence_path"))
        and bool(payload.get("approval_id"))
        and bool(payload.get("request_digest_sha256"))
        and bool(payload.get("idempotency_marker_path"))
        and not payload.get("blockers")
        and all(payload.get(flag) is False for flag in denied_false)
    )


def _excalidraw_public_drawing_approval_ok(vault: Path) -> bool:
    if not _all_exist(
        vault,
        (
            "runtime/browser_runtime/excalidraw_public_drawing_approval.py",
            "runtime/browser_runtime/test_excalidraw_public_drawing_approval.py",
            "06_AGENTS/Excalidraw-Public-Browser-Drawing-Proof-Approval.md",
        ),
    ):
        return False
    return any(
        _excalidraw_public_drawing_approval_payload_ok(payload)
        for payload in _json_records_newest_first(
            vault,
            "07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals/*.json",
        )
    )


def _excalidraw_public_drawing_proof_payload_ok(vault: Path, payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    screenshot_path = payload.get("screenshot_path")
    if not isinstance(screenshot_path, str) or not _nonempty_file(vault, screenshot_path):
        return False
    evidence_json_path = payload.get("evidence_json_path")
    if not isinstance(evidence_json_path, str) or not _nonempty_file(vault, evidence_json_path):
        return False
    activity_path = payload.get("agent_activity_evidence_path")
    if not isinstance(activity_path, str) or not _nonempty_file(vault, activity_path):
        return False
    marker_path = payload.get("idempotency_marker_path")
    if not isinstance(marker_path, str) or not _nonempty_file(vault, marker_path):
        return False
    source_path = payload.get("source_reachability_evidence_path")
    if not isinstance(source_path, str) or not _nonempty_file(vault, source_path):
        return False
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        return False
    required_checks = {
        "approval_loaded",
        "playwright_available",
        "idempotency_marker_reserved",
        "navigation_succeeded",
        "title_matches_excalidraw",
        "canvas_element_present",
        "rectangle_action_attempted",
        "text_action_attempted",
        "screenshot_captured",
        "visual_change_after_actions",
    }
    passed_checks = {
        check.get("name")
        for check in checks
        if isinstance(check, dict) and check.get("ok") is True
    }
    authority = payload.get("authority")
    if not isinstance(authority, dict):
        return False
    required_authority_true = (
        "target_registered_in_chaseos",
        "throwaway_browser_context_only",
        "no_login_profile_cookies",
        "no_real_profile",
        "no_credentials",
        "no_cookie_export",
        "no_browser_use_cli",
        "no_mcp_invocation",
        "no_provider_calls",
        "no_agent_bus_writes",
        "no_gate_mutation",
        "no_trusted_skill_write",
        "no_skill_activation",
        "no_canonical_mutation",
    )
    denied_false = (
        "mcp_invocation_attempted",
        "mcp_tool_call_attempted",
        "draft_skill_written",
        "untrusted_candidate_written",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "cookie_export_attempted",
        "browser_profile_sync_attempted",
        "browser_history_import_attempted",
        "public_tunnel_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "workflow_use_code_copied",
        "shell_execution_from_browser_runtime_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    return (
        payload.get("ok") is True
        and payload.get("record_type") == "excalidraw_public_browser_drawing_proof_run"
        and payload.get("schema_version") == "browser.excalidraw_public_drawing_proof.v1"
        and payload.get("status") == "excalidraw_public_browser_drawing_proof_complete"
        and payload.get("target_registry_id") == "excalidraw"
        and payload.get("target_url") == "https://excalidraw.com"
        and payload.get("canvas_found") is True
        and payload.get("visual_change_after_actions") is True
        and bool(payload.get("approval_id"))
        and bool(payload.get("request_digest_sha256"))
        and bool(payload.get("drawing_label"))
        and "excalidraw" in str(payload.get("page_title") or "").lower()
        and required_checks.issubset(passed_checks)
        and all(authority.get(flag) is True for flag in required_authority_true)
        and all(payload.get(flag) is False for flag in denied_false)
        and not payload.get("blockers")
    )


def _excalidraw_public_drawing_proof_ok(vault: Path) -> bool:
    if not _all_exist(
        vault,
        (
            "runtime/browser_runtime/excalidraw_public_drawing_proof.py",
            "runtime/browser_runtime/test_excalidraw_public_drawing_proof.py",
            "06_AGENTS/Excalidraw-Public-Browser-Drawing-Proof-Run.md",
        ),
    ):
        return False
    return any(
        _excalidraw_public_drawing_proof_payload_ok(vault, payload)
        for payload in _json_records_newest_first(
            vault,
            "07_LOGS/Browser-Runs/excalidraw_public_drawing_proof_*.json",
        )
    )


def _browser_runtime_completion_estimate_ok(vault: Path) -> bool:
    """Return true when the read-only completion estimate reporter exists."""
    return _all_exist(vault, BROWSER_RUNTIME_COMPLETION_ESTIMATE_PATHS)


def _browser_runtime_production_complete_payload_ok(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    forbidden_flags = (
        "dependency_install_attempted",
        "server_start_attempted",
        "network_probe_attempted",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_invocation_attempted",
        "target_navigation_attempted",
        "screenshot_capture_attempted",
        "browser_use_cli_live_used",
        "excalidraw_live_proof_attempted",
        "approval_grant_attempted",
        "approval_execution_attempted",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "connector_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    )
    return (
        payload.get("record_type") == "browser_runtime_production_closeout"
        and payload.get("schema_version") == "browser.production_closeout.v1"
        and payload.get("status") == "browser_runtime_production_complete"
        and payload.get("bounded_mvp_done") is True
        and payload.get("production_feature_done") is True
        and payload.get("internal_studio_panel_lane_complete") is True
        and payload.get("external_runtime_lanes_deferred") is False
        and payload.get("blocker_count") == 0
        and payload.get("remaining_major_passes_min") == 0
        and payload.get("remaining_major_passes_max") == 0
        and payload.get("remaining_internal_passes") == []
        and payload.get("external_deferred_lanes") == []
        and payload.get("blocked_reasons") == []
        and all(payload.get(flag) is False for flag in forbidden_flags)
    )


def _browser_runtime_production_complete_ok(vault: Path) -> bool:
    """Return true when the final no-action production-complete evidence exists."""
    if not _all_exist(
        vault,
        (
            "runtime/browser_runtime/production_closeout.py",
            "runtime/browser_runtime/test_production_closeout.py",
        ),
    ):
        return False
    return any(
        _browser_runtime_production_complete_payload_ok(payload)
        for payload in _json_records_newest_first(
            vault,
            "07_LOGS/Studio-Graph-Views/*browser-runtime-production-complete.json",
        )
    )


def _studio_browser_runtime_operator_ui_readiness_ok(vault: Path) -> bool:
    """Return true when the read-only Studio operator UI readiness contract exists."""
    return _all_exist(vault, STUDIO_BROWSER_RUNTIME_OPERATOR_UI_READINESS_PATHS)


def _studio_browser_runtime_native_panel_ok(vault: Path) -> bool:
    """Return true when the native read-only Studio panel and QA evidence exist."""
    return _all_exist(vault, STUDIO_BROWSER_RUNTIME_NATIVE_PANEL_EVIDENCE_PATHS)


def _build_production_items(vault: Path) -> list[BrowserRuntimeCompletionItem]:
    cdp_ready = _cdp_operational_activation_ok(vault)
    browser_use_cli_preflight_ready = _browser_use_cli_validation_preflight_ok(vault)
    browser_use_cli_live_unavailable = _browser_use_cli_live_unavailable_evidence_ok(vault)
    browser_use_cli_external_validation_ready = _browser_use_cli_external_validation_ok(vault)
    browser_use_cli_safe_url_design_ready = _browser_use_cli_safe_url_design_ok(vault)
    browser_use_cli_safe_url_run_ready = _browser_use_cli_safe_url_run_ok(vault)
    vincisos_target_probe_ready = _vincisos_product_ui_target_probe_ok(vault)
    vincisos_launch_readiness_ready = _vincisos_product_ui_launch_readiness_ok(vault)
    vincisos_product_ui_browser_proof_ready = _vincisos_product_ui_browser_proof_ok(vault)
    browser_harness_decision_ready = _browser_harness_adoption_decision_ok(vault)
    browser_workflow_cache_ready = _browser_workflow_cache_foundation_ok(vault)
    replay_executor_design_ready = _workflow_replay_executor_design_preflight_ok(vault)
    replay_implementation_request_ready = _workflow_replay_executor_implementation_request_ok(vault)
    replay_implementation_approval_ready = _workflow_replay_executor_implementation_approval_ok(vault)
    replay_executor_implementation_ready = _workflow_replay_executor_implementation_ok(vault)
    replay_execution_readiness_ready = _workflow_replay_execution_readiness_preflight_ok(vault)
    replay_trial_candidate_ready = _workflow_replay_trial_candidate_selection_ok(vault)
    replay_execution_approval_ready = _workflow_replay_execution_approval_idempotency_ok(vault)
    replay_execution_proof_implementation_ready = _workflow_replay_execution_proof_implementation_ok(vault)
    replay_execution_proof_success_ready = _workflow_replay_execution_proof_success_ok(vault)
    excalidraw_mcp_proof_prep_ready = _excalidraw_mcp_proof_prep_ok(vault)
    excalidraw_mcp_live_readiness_status = _excalidraw_mcp_live_readiness_status(vault)
    excalidraw_target_setup_ready = _excalidraw_target_setup_instructions_ok(vault)
    excalidraw_target_contract_request_ready = _excalidraw_target_contract_request_ok(vault)
    excalidraw_target_response_intake_ready = _excalidraw_target_response_intake_ok(vault)
    excalidraw_target_response_resolver_ready = _excalidraw_target_response_resolver_ok(vault)
    excalidraw_readiness_from_response_ready = _excalidraw_readiness_from_response_ok(vault)
    excalidraw_mcp_execution_approval_ready = _excalidraw_mcp_execution_approval_ok(vault)
    excalidraw_mcp_proof_execution_shell_ready = _excalidraw_mcp_proof_execution_shell_ok(vault)
    excalidraw_live_chain_readiness_ready = _excalidraw_live_chain_readiness_ok(vault)
    excalidraw_public_live_browser_proof_ready = _excalidraw_public_live_browser_proof_ok(vault)
    excalidraw_public_drawing_approval_ready = _excalidraw_public_drawing_approval_ok(vault)
    excalidraw_public_drawing_proof_ready = _excalidraw_public_drawing_proof_ok(vault)
    browser_runtime_production_complete_ready = _browser_runtime_production_complete_ok(vault)
    studio_browser_runtime_native_panel_ready = _studio_browser_runtime_native_panel_ok(vault)
    completion_estimate_ready = _browser_runtime_completion_estimate_ok(vault)
    studio_browser_runtime_operator_ui_readiness_ready = (
        _studio_browser_runtime_operator_ui_readiness_ok(vault)
    )
    studio_browser_runtime_native_panel_ready = _studio_browser_runtime_native_panel_ok(vault)
    items = [
        BrowserRuntimeCompletionItem(
            area="production:default_live_cdp_launcher_and_client",
            status="complete_targeted" if cdp_ready else "not_built",
            evidence=CDP_OPERATIONAL_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=cdp_ready,
            notes=(
                "Bounded approval-gated live CDP executor and operational activation are evidenced; this does not complete VincisOS product UI proof or unrestricted browser automation."
                if cdp_ready
                else "Default live launcher/client activation evidence is missing."
            ),
        )
    ]
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:browser_use_cli_validation_preflight",
            status="complete_targeted" if browser_use_cli_preflight_ready else "not_built",
            evidence=BROWSER_USE_CLI_VALIDATION_PREFLIGHT_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=browser_use_cli_preflight_ready,
            notes=(
                "Read-only Browser Use CLI preflight exists and performs no dependency install, CLI invocation, browser launch, profile access, credential read, or writeback."
                if browser_use_cli_preflight_ready
                else "Read-only Browser Use CLI validation preflight is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:browser_use_cli_live_validation",
            status=(
                "complete_targeted_safe_url_open_no_account"
                if browser_use_cli_safe_url_run_ready
                else "complete_targeted_safe_url_design_no_execution"
                if browser_use_cli_safe_url_design_ready
                else
                "complete_targeted_help_probe_no_browser"
                if browser_use_cli_external_validation_ready
                else "blocked_unavailable"
                if browser_use_cli_live_unavailable
                else "deferred"
            ),
            evidence=(
                BROWSER_USE_CLI_SAFE_URL_RUN_EVIDENCE_TEXT
                if browser_use_cli_safe_url_run_ready
                else BROWSER_USE_CLI_SAFE_URL_DESIGN_EVIDENCE_TEXT
                if browser_use_cli_safe_url_design_ready
                else BROWSER_USE_CLI_EXTERNAL_VALIDATION_EVIDENCE_TEXT
                if browser_use_cli_external_validation_ready
                else BROWSER_USE_CLI_LIVE_UNAVAILABLE_EVIDENCE_TEXT
                if browser_use_cli_live_unavailable
                else "runtime/browser_runtime/adapters/browser_use_cli.py"
            ),
            complete_for_bounded_mvp=True,
            complete_for_production=browser_use_cli_safe_url_run_ready,
            notes=(
                "No-account Browser Use CLI safe-URL validation opened the ChaseOS-owned localhost Studio Product UI target, closed the named Browser Use session, verified browser dependency availability through successful execution, and preserved no install, profile, credential/cookie, tunnel, provider/cloud, Agent Bus, Gate, skill, or canonical authority."
                if browser_use_cli_safe_url_run_ready
                else "Safe-URL validation design is ready for the ChaseOS-owned localhost product UI target without browser command execution. Browser Use package/executable download is complete; Browser Use browser dependency download is not verified."
                if browser_use_cli_safe_url_design_ready
                else "External Browser Use CLI help-surface validation succeeded without browser command execution, browser launch, profile access, credential/cookie read, provider/cloud call, tunnel, or writeback. A separate no-account safe-URL browser validation remains required."
                if browser_use_cli_external_validation_ready
                else "Live Browser Use CLI validation was checked through the read-only preflight and is blocked because the CLI is unavailable; no live run, browser launch, profile access, credential/cookie read, or writeback occurred."
                if browser_use_cli_live_unavailable
                else "Wrapper fails closed; no live Browser Use CLI run has been authorized or validated."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:vincisos_product_ui_target_availability_probe",
            status="complete_targeted" if vincisos_target_probe_ready else "not_built",
            evidence=VINCISOS_PRODUCT_UI_TARGET_PROBE_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=vincisos_target_probe_ready,
            notes=(
                "No-browser local HTTP availability probe exists; it validates the target contract and keeps browser/CDP/profile/credential/writeback effects false."
                if vincisos_target_probe_ready
                else "No-browser product UI target availability probe is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:vincisos_product_ui_launch_readiness",
            status="complete_targeted" if vincisos_launch_readiness_ready else "not_built",
            evidence=VINCISOS_PRODUCT_UI_LAUNCH_READINESS_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=vincisos_launch_readiness_ready,
            notes=(
                "No-start launch-readiness discovery exists; it checks whether a registered local VincisOS product UI start surface exists before any browser proof."
                if vincisos_launch_readiness_ready
                else "No-start VincisOS product UI launch-readiness surface is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:full_vincisos_product_ui_browser_proof",
            status="complete_targeted" if vincisos_product_ui_browser_proof_ready else "blocked",
            evidence=VINCISOS_PRODUCT_UI_BROWSER_PROOF_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=vincisos_product_ui_browser_proof_ready,
            notes=(
                "Registered local product UI browser proof exists with screenshot, Browser Run, Agent Activity, draft skill, and untrusted candidate evidence while forbidden authority flags remain false."
                if vincisos_product_ui_browser_proof_ready
                else "No safe local product UI browser proof has been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:browser_harness_adoption_decision",
            status="complete_targeted" if browser_harness_decision_ready else "deferred",
            evidence=BROWSER_HARNESS_ADOPTION_DECISION_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=browser_harness_decision_ready,
            notes=(
                "Browser Harness adoption decision is recorded: adapt domain/interaction skill patterns, do not adopt raw harness authority."
                if browser_harness_decision_ready
                else "Browser Harness adoption decision is not yet recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:browser_workflow_cache_foundation",
            status="complete_targeted" if browser_workflow_cache_ready else "not_built",
            evidence=BROWSER_WORKFLOW_CACHE_FOUNDATION_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=browser_workflow_cache_ready,
            notes=(
                "Inactive ChaseOS-native workflow cache foundation exists; replay execution remains deferred."
                if browser_workflow_cache_ready
                else "Inactive browser workflow cache foundation is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_executor_design_preflight",
            status="complete_targeted" if replay_executor_design_ready else "not_built",
            evidence=WORKFLOW_REPLAY_EXECUTOR_DESIGN_PREFLIGHT_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=replay_executor_design_ready,
            notes=(
                "No-execution replay executor design preflight exists; actual replay execution remains deferred."
                if replay_executor_design_ready
                else "No-execution replay executor design preflight is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_executor_implementation_request",
            status="complete_targeted" if replay_implementation_request_ready else "not_built",
            evidence=WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_REQUEST_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=replay_implementation_request_ready,
            notes=(
                "No-write replay executor implementation request exists; actual replay execution remains deferred."
                if replay_implementation_request_ready
                else "No-write replay executor implementation request is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_executor_implementation_approval",
            status="complete_targeted" if replay_implementation_approval_ready else "not_built",
            evidence=WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_APPROVAL_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=replay_implementation_approval_ready,
            notes=(
                "No-write replay executor implementation approval exists; execution remains deferred."
                if replay_implementation_approval_ready
                else "No-write replay executor implementation approval is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_executor_implementation",
            status="complete_targeted" if replay_executor_implementation_ready else "not_built",
            evidence=WORKFLOW_REPLAY_EXECUTOR_IMPLEMENTATION_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=replay_executor_implementation_ready,
            notes=(
                "Disabled-by-default replay executor implementation exists and performs validation/planning only; actual replay execution remains deferred."
                if replay_executor_implementation_ready
                else "Disabled replay executor implementation is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_execution_readiness_preflight",
            status="complete_targeted" if replay_execution_readiness_ready else "not_built",
            evidence=WORKFLOW_REPLAY_EXECUTION_READINESS_PREFLIGHT_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=replay_execution_readiness_ready,
            notes=(
                "Read-only replay execution readiness preflight exists; it identifies selected-workflow and approval blockers without replaying workflows."
                if replay_execution_readiness_ready
                else "Read-only replay execution readiness preflight is missing."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_trial_candidate_selection",
            status="complete_targeted" if replay_trial_candidate_ready else "not_built",
            evidence=WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTION_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=replay_trial_candidate_ready,
            notes=(
                "Reviewed local VincisOS workflow trial candidate is selected for no-execution readiness; activation, trusted writes, and global replay authority remain disabled."
                if replay_trial_candidate_ready
                else "Reviewed local workflow replay trial candidate has not been selected."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_execution_approval_and_idempotency",
            status="complete_targeted" if replay_execution_approval_ready else "not_built",
            evidence=WORKFLOW_REPLAY_EXECUTION_APPROVAL_IDEMPOTENCY_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=replay_execution_approval_ready,
            notes=(
                "No-write replay execution approval/idempotency contract exists; it binds the selected local workflow, future approval request shape, and exact-once marker path without writing approval artifacts or replaying workflows."
                if replay_execution_approval_ready
                else "No-write replay execution approval/idempotency contract has not been built."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:workflow_replay_execution_proof",
            status=(
                "complete_targeted"
                if replay_execution_proof_success_ready
                else (
                    "implementation_ready_live_blocked"
                    if replay_execution_proof_implementation_ready
                    else "not_built"
                )
            ),
            evidence=(
                WORKFLOW_REPLAY_EXECUTION_PROOF_SUCCESS_EVIDENCE_TEXT
                if replay_execution_proof_success_ready
                else WORKFLOW_REPLAY_EXECUTION_PROOF_IMPLEMENTATION_EVIDENCE_TEXT
            ),
            complete_for_bounded_mvp=True,
            complete_for_production=replay_execution_proof_success_ready,
            notes=(
                "Bounded safe-local workflow replay execution proof succeeded with Browser Run evidence and forbidden authority flags false."
                if replay_execution_proof_success_ready
                else (
                    "Safe-local workflow replay proof runner is implemented and tested with an injected controller; live local replay remains blocked until a local browser controller is available and a success artifact is recorded."
                    if replay_execution_proof_implementation_ready
                    else "Safe-local workflow replay proof runner is not built."
                )
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_local_browser_mcp_proof_prep",
            status="complete_targeted" if excalidraw_mcp_proof_prep_ready else "not_built",
            evidence=EXCALIDRAW_MCP_PROOF_PREP_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_mcp_proof_prep_ready,
            notes=(
                "No-execution Excalidraw local browser/MCP proof prep exists; it writes prep evidence only and keeps browser launch, MCP invocation, navigation, trusted writes, activation, and canonical writeback false."
                if excalidraw_mcp_proof_prep_ready
                else "No-execution Excalidraw local browser/MCP proof prep has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_local_browser_mcp_live_readiness",
            status=(
                "complete_targeted"
                if excalidraw_mcp_live_readiness_status == "ready_no_execution"
                else (
                    "complete_targeted_blocked_current_target"
                    if excalidraw_mcp_live_readiness_status == "blocked_missing_local_target"
                    else "not_built"
                )
            ),
            evidence=EXCALIDRAW_MCP_LIVE_READINESS_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_mcp_live_readiness_status == "ready_no_execution",
            notes=(
                "No-execution Excalidraw live-readiness evidence exists and a local loopback target is ready for a separately approved live proof."
                if excalidraw_mcp_live_readiness_status == "ready_no_execution"
                else (
                    "No-execution Excalidraw live-readiness evidence exists and is safely blocked because no local loopback Excalidraw/MCP target URL was provided."
                    if excalidraw_mcp_live_readiness_status == "blocked_missing_local_target"
                    else "No-execution Excalidraw live-readiness evidence has not been recorded."
                )
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_local_target_setup_instructions",
            status="complete_targeted" if excalidraw_target_setup_ready else "not_built",
            evidence=EXCALIDRAW_TARGET_SETUP_INSTRUCTIONS_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_target_setup_ready,
            notes=(
                "No-execution local-target setup instructions exist for an external runtime/operator; ChaseOS did not install, start, launch, navigate, invoke MCP, activate skills, or mutate canonical state."
                if excalidraw_target_setup_ready
                else "No-execution Excalidraw local-target setup instructions have not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_local_target_contract_request",
            status="complete_targeted" if excalidraw_target_contract_request_ready else "not_built",
            evidence=EXCALIDRAW_TARGET_CONTRACT_REQUEST_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_target_contract_request_ready,
            notes=(
                "No-execution Excalidraw target contract/request packet exists for the external runtime/operator; it does not start or probe the target."
                if excalidraw_target_contract_request_ready
                else "No-execution Excalidraw target contract/request packet has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_local_target_response_intake",
            status="complete_targeted" if excalidraw_target_response_intake_ready else "not_built",
            evidence=EXCALIDRAW_TARGET_RESPONSE_INTAKE_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_target_response_intake_ready,
            notes=(
                "No-execution Excalidraw target response intake exists; it writes only an untrusted pending input artifact and does not probe, launch, invoke MCP, activate skills, or mutate canonical state."
                if excalidraw_target_response_intake_ready
                else "No-execution Excalidraw target response intake has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_target_response_latest_resolver",
            status="complete_targeted" if excalidraw_target_response_resolver_ready else "not_built",
            evidence=EXCALIDRAW_TARGET_RESPONSE_RESOLVER_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_target_response_resolver_ready,
            notes=(
                "No-execution Excalidraw target-response latest resolver exists; it scans only the untrusted pending response folder and performs no target probe, browser launch, MCP invocation, trusted write, activation, or canonical mutation."
                if excalidraw_target_response_resolver_ready
                else "No-execution Excalidraw target-response latest resolver has not been built."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_readiness_from_target_response",
            status=(
                "complete_targeted_blocked_current_target"
                if excalidraw_readiness_from_response_ready
                else "not_built"
            ),
            evidence=EXCALIDRAW_READINESS_FROM_RESPONSE_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_readiness_from_response_ready,
            notes=(
                "No-execution Excalidraw response-to-readiness bridge exists; current evidence is safely blocked because the external runtime response is still pending and contains no target URL."
                if excalidraw_readiness_from_response_ready
                else "No-execution Excalidraw response-to-readiness bridge has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_mcp_execution_approval",
            status="complete_targeted_blocked_current_target"
            if excalidraw_mcp_execution_approval_ready
            else "not_built",
            evidence=EXCALIDRAW_MCP_EXECUTION_APPROVAL_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_mcp_execution_approval_ready,
            notes=(
                "No-write Excalidraw browser/MCP execution approval and idempotency contract exists; current live execution remains blocked until an accepted loopback target and ready live-readiness evidence exist."
                if excalidraw_mcp_execution_approval_ready
                else "No-write Excalidraw browser/MCP execution approval contract has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_mcp_proof_execution_shell",
            status="complete_targeted_blocked_current_target"
            if excalidraw_mcp_proof_execution_shell_ready
            else "not_built",
            evidence=EXCALIDRAW_MCP_PROOF_EXECUTION_SHELL_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_mcp_proof_execution_shell_ready,
            notes=(
                "Fail-closed Excalidraw browser/MCP proof execution shell exists; it validates approval/readiness/idempotency posture and refuses execution until a later approved live proof pass."
                if excalidraw_mcp_proof_execution_shell_ready
                else "Fail-closed Excalidraw browser/MCP proof execution shell has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_live_chain_readiness_reporter",
            status="complete_targeted_blocked_current_target"
            if excalidraw_live_chain_readiness_ready
            else "not_built",
            evidence=EXCALIDRAW_LIVE_CHAIN_READINESS_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_live_chain_readiness_ready,
            notes=(
                "No-execution Excalidraw live-chain readiness reporter exists; it composes the target resolver, readiness bridge, approval contract, and proof shell while refusing browser launch, MCP calls, screenshots, run-log writes, skill writes, activation, and canonical writeback."
                if excalidraw_live_chain_readiness_ready
                else "No-execution Excalidraw live-chain readiness reporter has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_public_live_browser_proof",
            status=(
                "complete_targeted"
                if excalidraw_public_live_browser_proof_ready
                else "not_built"
            ),
            evidence=EXCALIDRAW_PUBLIC_LIVE_BROWSER_PROOF_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_public_live_browser_proof_ready,
            notes=(
                "Public Excalidraw browser reachability proof succeeded with title, canvas, screenshot, and no login/profile/cookie/provider/Gate/canonical authority; this does not satisfy the separate MCP drawing proof."
                if excalidraw_public_live_browser_proof_ready
                else "Public Excalidraw browser reachability proof has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_public_browser_drawing_proof_approval",
            status=(
                "complete_targeted"
                if excalidraw_public_drawing_approval_ready
                else "not_built"
            ),
            evidence=EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_public_drawing_approval_ready,
            notes=(
                (
                    "Public Excalidraw no-login drawing proof approval packet exists and has been consumed by the dedicated public drawing proof run."
                    if excalidraw_public_drawing_proof_ready
                    else "Public Excalidraw no-login drawing proof approval packet exists; it authorizes one future browser-only drawing proof after exact-once marker consumption, but no drawing/MCP proof has run yet."
                )
                if excalidraw_public_drawing_approval_ready
                else "Public Excalidraw no-login drawing proof approval packet has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:excalidraw_public_browser_drawing_proof_run",
            status=(
                "complete_targeted"
                if excalidraw_public_drawing_proof_ready
                else "not_built"
            ),
            evidence=EXCALIDRAW_PUBLIC_DRAWING_PROOF_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=excalidraw_public_drawing_proof_ready,
            notes=(
                "Approved public Excalidraw no-login drawing proof ran once, consumed its exact-once marker, drew the bounded rectangle/text proof, and wrote Browser Run plus Agent Activity evidence without MCP, Browser Use CLI, real profile, credentials/cookies, provider, Agent Bus, Gate, skill activation, trusted writes, or canonical writeback."
                if excalidraw_public_drawing_proof_ready
                else "Approved public Excalidraw no-login drawing proof has not run yet."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:browser_runtime_completion_estimate",
            status="complete_targeted" if completion_estimate_ready else "not_built",
            evidence=BROWSER_RUNTIME_COMPLETION_ESTIMATE_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=completion_estimate_ready,
            notes=(
                "Read-only Browser Runtime completion estimate exists; it turns current blockers into an estimated remaining-pass plan without launching browsers, invoking MCP, writing artifacts, activating skills, mutating Gate, or writing canonical state."
                if completion_estimate_ready
                else "Read-only Browser Runtime completion estimate has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:browser_runtime_production_complete",
            status="complete" if browser_runtime_production_complete_ready else "planned",
            evidence=BROWSER_RUNTIME_PRODUCTION_COMPLETE_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=True,
            notes=(
                "Final no-action Browser Runtime production-complete evidence exists; remaining major passes are zero and no Browser Use CLI, Excalidraw, MCP, browser, provider, Agent Bus, Gate, skill, workflow, or canonical action is performed by the closeout."
                if browser_runtime_production_complete_ready
                else "Final no-action production-complete closeout evidence has not been written yet."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:studio_browser_runtime_operator_ui_readiness",
            status=(
                "complete_targeted"
                if studio_browser_runtime_operator_ui_readiness_ready
                else "not_built"
            ),
            evidence=STUDIO_BROWSER_RUNTIME_OPERATOR_UI_READINESS_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=studio_browser_runtime_operator_ui_readiness_ready,
            notes=(
                "Read-only Studio Browser Runtime operator UI readiness contract exists; it defines panels for completion, blockers, Excalidraw chain state, provider validation, draft skill memory, approvals, and run evidence without launching browsers, invoking MCP, writing artifacts, activating skills, mutating Gate, or writing canonical state."
                if studio_browser_runtime_operator_ui_readiness_ready
                else "Read-only Studio Browser Runtime operator UI readiness contract has not been recorded."
            ),
        )
    )
    items.append(
        BrowserRuntimeCompletionItem(
            area="production:studio_browser_runtime_native_panel",
            status=(
                "complete_targeted"
                if studio_browser_runtime_native_panel_ready
                else "not_built"
            ),
            evidence=STUDIO_BROWSER_RUNTIME_NATIVE_PANEL_EVIDENCE_TEXT,
            complete_for_bounded_mvp=True,
            complete_for_production=studio_browser_runtime_native_panel_ready,
            notes=(
                "Read-only Browser Runtime panel is mounted through the native Studio lane and has bounded static QA plus legacy-harness browser support evidence; it does not run Browser Use, Excalidraw, approvals, skills, providers, Agent Bus writes, or canonical writeback."
                if studio_browser_runtime_native_panel_ready
                else "Native read-only Browser Runtime panel mount and QA evidence have not been recorded."
            ),
        )
    )
    items.extend(
        BrowserRuntimeCompletionItem(
            area=f"production:{area}",
            status=status,
            evidence=evidence,
            complete_for_bounded_mvp=True,
            complete_for_production=False,
            notes=notes,
        )
        for area, status, evidence, notes in PRODUCTION_GATES
        if area not in {"browser_use_cli_live_validation", "workflow_replay_execution"}
    )
    return items


def build_browser_runtime_completion_status(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> BrowserRuntimeCompletionStatus:
    """Build a read-only completion status from repo-local browser evidence."""
    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    mvp_items = _build_mvp_items(vault)
    production_items = _build_production_items(vault)
    bounded_mvp_done = all(item.complete_for_bounded_mvp for item in mvp_items)
    excalidraw_public_live_browser_proof_ready = _excalidraw_public_live_browser_proof_ok(vault)
    excalidraw_public_drawing_approval_ready = _excalidraw_public_drawing_approval_ok(vault)
    excalidraw_public_drawing_proof_ready = _excalidraw_public_drawing_proof_ok(vault)
    browser_runtime_production_complete_ready = _browser_runtime_production_complete_ok(vault)
    studio_browser_runtime_native_panel_ready = _studio_browser_runtime_native_panel_ok(vault)

    blocked_reasons: list[str] = []
    if not bounded_mvp_done:
        blocked_reasons.extend(
            item.area
            for item in mvp_items
            if not item.complete_for_bounded_mvp
        )
    if not _vincisos_product_ui_browser_proof_ok(vault):
        blocked_reasons.append("full_vincisos_product_ui_proof_not_run")
    if not _cdp_operational_activation_ok(vault):
        blocked_reasons.append("default_live_cdp_launcher_and_client_not_built")
    if not _browser_use_cli_validation_preflight_ok(vault):
        blocked_reasons.append("browser_use_cli_validation_preflight_not_built")
    if not _vincisos_product_ui_target_probe_ok(vault):
        blocked_reasons.append("vincisos_product_ui_target_probe_not_built")
    if not _vincisos_product_ui_launch_readiness_ok(vault):
        blocked_reasons.append("vincisos_product_ui_launch_readiness_not_built")
    if not _browser_harness_adoption_decision_ok(vault):
        blocked_reasons.append("browser_harness_adoption_decision_not_recorded")
    if not _browser_workflow_cache_foundation_ok(vault):
        blocked_reasons.append("browser_workflow_cache_foundation_not_built")
    if not _workflow_replay_executor_design_preflight_ok(vault):
        blocked_reasons.append("workflow_replay_executor_design_preflight_not_built")
    if not _workflow_replay_executor_implementation_request_ok(vault):
        blocked_reasons.append("workflow_replay_executor_implementation_request_not_built")
    if not _workflow_replay_executor_implementation_approval_ok(vault):
        blocked_reasons.append("workflow_replay_executor_implementation_approval_not_built")
    if not _workflow_replay_executor_implementation_ok(vault):
        blocked_reasons.append("workflow_replay_executor_implementation_not_built")
    if not _workflow_replay_execution_readiness_preflight_ok(vault):
        blocked_reasons.append("workflow_replay_execution_readiness_preflight_not_built")
    if not _workflow_replay_trial_candidate_selection_ok(vault):
        blocked_reasons.append("workflow_replay_trial_candidate_not_selected")
    if not _workflow_replay_execution_approval_idempotency_ok(vault):
        blocked_reasons.append("workflow_replay_execution_approval_idempotency_not_built")
    if not _workflow_replay_execution_proof_implementation_ok(vault):
        blocked_reasons.append("workflow_replay_execution_proof_not_built")
    elif not _workflow_replay_execution_proof_success_ok(vault):
        blocked_reasons.append("workflow_replay_execution_live_proof_not_run")
    if not _excalidraw_mcp_proof_prep_ok(vault):
        blocked_reasons.append("excalidraw_local_browser_mcp_proof_prep_not_built")
    excalidraw_mcp_live_readiness_status = _excalidraw_mcp_live_readiness_status(vault)
    if excalidraw_mcp_live_readiness_status == "missing":
        blocked_reasons.append("excalidraw_local_browser_mcp_live_readiness_not_built")
    elif (
        excalidraw_mcp_live_readiness_status == "blocked_missing_local_target"
        and not excalidraw_public_live_browser_proof_ready
    ):
        blocked_reasons.append("excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target")
    elif excalidraw_mcp_live_readiness_status == "unsafe_or_invalid":
        blocked_reasons.append("excalidraw_local_browser_mcp_live_readiness_unsafe_or_invalid")
    if (
        excalidraw_mcp_live_readiness_status == "blocked_missing_local_target"
        and not _excalidraw_target_setup_instructions_ok(vault)
    ):
        blocked_reasons.append("excalidraw_local_target_setup_instructions_not_built")
    if not _excalidraw_mcp_execution_approval_ok(vault):
        blocked_reasons.append("excalidraw_mcp_execution_approval_not_built")
    if not _excalidraw_mcp_proof_execution_shell_ok(vault):
        blocked_reasons.append("excalidraw_mcp_proof_execution_shell_not_built")
    browser_use_cli_external_validation_ready = _browser_use_cli_external_validation_ok(vault)
    browser_use_cli_safe_url_design_ready = _browser_use_cli_safe_url_design_ok(vault)
    browser_use_cli_safe_url_run_ready = _browser_use_cli_safe_url_run_ok(vault)
    browser_use_cli_live_unavailable = _browser_use_cli_live_unavailable_evidence_ok(vault)
    if not browser_use_cli_safe_url_run_ready:
        blocked_reasons.append(
            "browser_use_cli_no_account_safe_url_validation_run_not_started"
            if browser_use_cli_safe_url_design_ready
            else "browser_use_cli_no_account_safe_url_validation_not_run"
            if browser_use_cli_external_validation_ready
            else "browser_use_cli_live_validation_blocked_unavailable"
            if browser_use_cli_live_unavailable
            else "browser_use_cli_live_validation_deferred"
        )
    if not excalidraw_public_drawing_proof_ready:
        blocked_reasons.append("excalidraw_live_browser_mcp_proof_not_run")
    if not studio_browser_runtime_native_panel_ready:
        blocked_reasons.append("studio_operator_ui_not_built")

    production_feature_done = bounded_mvp_done and not blocked_reasons

    if production_feature_done:
        overall_status = BROWSER_RUNTIME_OVERALL_COMPLETE
    elif bounded_mvp_done:
        overall_status = BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED
    elif any(item.status != "missing" for item in mvp_items):
        overall_status = BROWSER_RUNTIME_OVERALL_PARTIAL
    else:
        overall_status = BROWSER_RUNTIME_OVERALL_NOT_STARTED

    next_recommended_pass = (
        "vincisos-full-ui-local-product-target-proof"
        if not _vincisos_product_ui_browser_proof_ok(vault)
        else (
            (
                "workflow-replay-execution-readiness-preflight"
                if not _workflow_replay_execution_readiness_preflight_ok(vault)
                else (
                    "workflow-replay-trial-candidate-selection"
                    if not _workflow_replay_trial_candidate_selection_ok(vault)
                    else (
                        "workflow-replay-execution-approval-and-idempotency"
                        if not _workflow_replay_execution_approval_idempotency_ok(vault)
                        else (
                            "safe-local-workflow-replay-execution-proof"
                            if not _workflow_replay_execution_proof_success_ok(vault)
                            else (
                                "excalidraw-local-browser-mcp-proof-prep"
                                if not _excalidraw_mcp_proof_prep_ok(vault)
                                else (
                                    "excalidraw-local-browser-mcp-live-readiness"
                                    if excalidraw_mcp_live_readiness_status == "missing"
                                    else (
                                        (
                                            (
                                                "studio-browser-runtime-approval-and-skill-inspection-ui"
                                                if not studio_browser_runtime_native_panel_ready
                                                else "browser-runtime-production-complete"
                                            )
                                            if excalidraw_public_drawing_proof_ready
                                            else (
                                                (
                                                    "excalidraw-public-browser-drawing-proof-run"
                                                    if excalidraw_public_drawing_approval_ready
                                                    else "excalidraw-public-browser-drawing-proof-approval"
                                                )
                                                if excalidraw_public_live_browser_proof_ready
                                                else (
                                                    "external-runtime-provide-excalidraw-target-url"
                                                    if _excalidraw_target_setup_instructions_ok(vault)
                                                    else "excalidraw-local-target-setup-instructions"
                                                )
                                            )
                                        )
                                        if excalidraw_mcp_live_readiness_status
                                        == "blocked_missing_local_target"
                                        else (
                                            (
                                                (
                                                    "excalidraw-local-browser-mcp-proof-execution"
                                                    if _excalidraw_mcp_proof_execution_shell_ok(vault)
                                                    else "excalidraw-local-browser-mcp-proof-execution-shell"
                                                )
                                                if _excalidraw_mcp_execution_approval_ok(vault)
                                                else "excalidraw-local-browser-mcp-proof-execution-approval"
                                            )
                                            if excalidraw_mcp_live_readiness_status
                                            == "ready_no_execution"
                                            else "excalidraw-local-browser-mcp-live-readiness"
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            if (
                browser_use_cli_safe_url_run_ready
                or (
                    browser_use_cli_live_unavailable
                    and not browser_use_cli_external_validation_ready
                )
            )
            else "browser-use-cli-no-account-safe-url-validation-run"
            if browser_use_cli_safe_url_design_ready
            else "browser-use-cli-no-account-safe-url-validation-design"
            if browser_use_cli_external_validation_ready
            else "browser-use-cli-live-validation"
        )
    )
    if production_feature_done and browser_runtime_production_complete_ready:
        next_recommended_pass = "phase10-studio-product-hardening"

    status = BrowserRuntimeCompletionStatus(
        generated_at=timestamp,
        overall_status=overall_status,
        bounded_mvp_done=bounded_mvp_done,
        production_feature_done=production_feature_done,
        next_recommended_pass=next_recommended_pass,
        blocked_reasons=tuple(blocked_reasons),
        items=tuple(mvp_items + production_items),
    )
    status.validate()
    return status


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report read-only Browser Runtime completion status.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    status = build_browser_runtime_completion_status(args.vault_root)
    payload = status.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"overall_status: {payload['overall_status']}")
        print(f"bounded_mvp_done: {payload['bounded_mvp_done']}")
        print(f"production_feature_done: {payload['production_feature_done']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
        print("blocked_reasons:")
        for reason in payload["blocked_reasons"]:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
