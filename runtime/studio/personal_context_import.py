"""Studio personal context import readiness surface.

This surface describes how an operator-provided context memory export should be
ingested into ChaseOS without letting raw personal memory rewrite canonical
state. This panel is a read-only planner/readiness model; approved writes live
in separate digest-gated executors.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.personal_operator_context_index import (
    ROOT_HUB_PATH,
    build_personal_operator_context_index,
)


MODEL_VERSION = "studio.personal_context_import.v1"
SURFACE_ID = "studio_personal_context_import_panel"

CANONICAL_KNOWLEDGE_INDEX_PATH = "02_KNOWLEDGE/Knowledge-Index.md"
ROOT_KNOWLEDGE_SHIM_PATH = "KNOWLEDGE-INDEX.md"
RAW_INTAKE_DIR = "03_INPUTS/Personal-Context-Intake"
PERSONAL_MAP_CANDIDATE_DIR = "07_LOGS/Pulse-Decks/memory-candidates/personal-map"
FEATURE_CONTRACT_PATH = "06_AGENTS/Personal-Context-Import-Feature.md"
PREVIEW_WRITER_SURFACE_ID = "studio_personal_context_import_preview_writer"
APPROVED_PREVIEW_EXECUTOR_SURFACE_ID = "studio_personal_context_import_approved_preview_execution_proof"
MULTI_INSTANCE_HARNESS_SURFACE_ID = "studio_personal_context_import_multi_instance_fixture_harness"
RUNTIME_CONSUMPTION_READINESS_SURFACE_ID = "studio_personal_context_import_runtime_consumption_readiness"
CANONICAL_PROMOTION_APPROVAL_PREVIEW_SURFACE_ID = "studio_personal_context_import_canonical_promotion_approval_preview"
CANONICAL_PROMOTION_APPROVED_EXECUTOR_SURFACE_ID = "studio_personal_context_import_canonical_promotion_approved_executor"
PREVIEW_WRITER_API_METHODS = [
    "get_personal_context_import_preview_writer",
    "request_personal_context_import_preview",
]
APPROVED_PREVIEW_EXECUTOR_API_METHODS = [
    "get_personal_context_import_approved_preview_execution_proof",
    "execute_personal_context_import_approved_preview_execution",
]
MULTI_INSTANCE_HARNESS_API_METHODS = [
    "get_personal_context_import_multi_instance_fixture_harness",
]
RUNTIME_CONSUMPTION_READINESS_API_METHODS = [
    "get_personal_context_import_runtime_consumption_readiness",
]
CANONICAL_PROMOTION_APPROVAL_PREVIEW_API_METHODS = [
    "get_personal_context_import_canonical_promotion_approval_preview",
    "request_personal_context_import_canonical_promotion_approval",
]
CANONICAL_PROMOTION_APPROVED_EXECUTOR_API_METHODS = [
    "get_personal_context_import_canonical_promotion_approved_executor",
    "execute_personal_context_import_canonical_promotion_approved_executor",
]
NEXT_RECOMMENDED_PASS = "personal-context-import-100-percent-closeout"


_ENTRYPOINTS: tuple[dict[str, str], ...] = (
    {
        "id": "settings",
        "label": "Settings",
        "surface": "studio_settings_runtime_controls_panel",
        "route_hint": "#/settings",
        "role": "Primary operator entry point for choosing/import-preview posture.",
    },
    {
        "id": "context_import_panel",
        "label": "Context Import",
        "surface": SURFACE_ID,
        "route_hint": "#/context-import",
        "role": "Dedicated import readiness, parent-child plan, and storage/security overview.",
    },
    {
        "id": "dashboard",
        "label": "Dashboard",
        "surface": "studio_dashboard",
        "route_hint": "#/dashboard",
        "role": "Top-level readiness card and personal-instance wiring status.",
    },
    {
        "id": "personal_operator_context",
        "label": "Personal Operator Context",
        "surface": "studio_personal_operator_context_index",
        "route_hint": "dashboard.personal_operator_context_panel",
        "role": "Grouped read model for the currently imported personal instance.",
    },
    {
        "id": "runtime_memory_inspector",
        "label": "Runtime Memory Inspector",
        "surface": "studio_memory_inspector",
        "route_hint": "#/runtime-memory-inspector",
        "role": "Runtime-facing memory posture review; read-only, no memory apply.",
    },
    {
        "id": "workspace_mode",
        "label": "Workspace Mode",
        "surface": "studio_workspace_mode_panel",
        "route_hint": "dashboard.workspace_mode_panel",
        "role": "Routes imported context through the personal_os WML profile before runtime use.",
    },
    {
        "id": "graph_node_inspector",
        "label": "Graph / Node Inspector",
        "surface": "studio_graph_and_node_inspector",
        "route_hint": "#/graph",
        "role": "Review proposed parent/child nodes and edges before controlled write requests.",
    },
    {
        "id": "approval_center",
        "label": "Approval Center",
        "surface": "studio_approval_center",
        "route_hint": "#/approval-center",
        "role": "Future approval lane for any context-import write or Personal Map apply.",
    },
)


_PIPELINE_STAGES: tuple[dict[str, Any], ...] = (
    {
        "id": "capture_raw_context",
        "label": "Capture raw context export",
        "trust_posture": "TIER 4 RAW INPUT",
        "writes_preview": [f"{RAW_INTAKE_DIR}/YYYY-MM-DD_personal-context-source.md"],
        "requires_operator_review": True,
    },
    {
        "id": "normalize_and_screen",
        "label": "Normalize, redact, and screen for unsafe input",
        "trust_posture": "UNTRUSTED UNTIL REVIEWED",
        "writes_preview": [f"{RAW_INTAKE_DIR}/YYYY-MM-DD_personal-context-source-digest.md"],
        "requires_operator_review": True,
    },
    {
        "id": "extract_nodes_and_edges",
        "label": "Extract parent nodes, child nodes, and graph edges",
        "trust_posture": "SOURCE-DERIVED / REVIEW REQUIRED",
        "writes_preview": [f"{RAW_INTAKE_DIR}/YYYY-MM-DD_personal-context-node-coverage-audit.md"],
        "requires_operator_review": True,
    },
    {
        "id": "route_to_personal_instance",
        "label": "Route approved context to personal OS, projects, knowledge, and domains",
        "trust_posture": "REVIEW-GATED ROUTING",
        "writes_preview": [
            "00_HOME/Personal-Operator-Index.md",
            "00_HOME/Dashboard.md",
            "00_HOME/Operating-System.md",
            "01_PROJECTS/Projects-Hub.md",
            CANONICAL_KNOWLEDGE_INDEX_PATH,
        ],
        "requires_operator_review": True,
    },
    {
        "id": "stage_personal_map_candidates",
        "label": "Stage Personal Map candidates",
        "trust_posture": "CANDIDATE / NOT APPLIED",
        "writes_preview": [
            f"{PERSONAL_MAP_CANDIDATE_DIR}/YYYY-MM-DD-personal-map-candidates.jsonl",
            f"{PERSONAL_MAP_CANDIDATE_DIR}/YYYY-MM-DD-personal-context-candidates-review.md",
        ],
        "requires_operator_review": True,
    },
    {
        "id": "runtime_read_model_refresh",
        "label": "Refresh runtime-facing read models",
        "trust_posture": "READ-ONLY CONTEXT DELIVERY",
        "writes_preview": [],
        "requires_operator_review": False,
    },
)


_REQUIRED_HUBS: tuple[dict[str, str], ...] = (
    {"id": "soul", "label": "SOUL", "path": "SOUL.md", "role": "Identity and agent soul"},
    {"id": "dashboard", "label": "Dashboard", "path": "00_HOME/Dashboard.md", "role": "Control tower"},
    {"id": "operating_system", "label": "Operating System", "path": "00_HOME/Operating-System.md", "role": "A-R personal domains"},
    {"id": "personal_operator_index", "label": "Personal Operator Index", "path": ROOT_HUB_PATH, "role": "Personal context hub"},
    {"id": "projects_hub", "label": "Projects Hub", "path": "01_PROJECTS/Projects-Hub.md", "role": "Project operating index"},
    {"id": "knowledge_index_master", "label": "Knowledge Index - Master", "path": CANONICAL_KNOWLEDGE_INDEX_PATH, "role": "Canonical knowledge taxonomy"},
    {"id": "knowledge_index_root_shim", "label": "Root Knowledge Index Shim", "path": ROOT_KNOWLEDGE_SHIM_PATH, "role": "Root/agent compatibility route only"},
    {"id": "personal_domains_index", "label": "Personal Domains Index", "path": "00_HOME/Personal-Domains/Personal-Domains-Index.md", "role": "Life-domain parent index"},
    {"id": "personal_map_architecture", "label": "Personal Map Architecture", "path": "06_AGENTS/Personal-Map-Architecture.md", "role": "Governed profile graph architecture"},
    {"id": "workspace_mode_architecture", "label": "Workspace Mode Layer", "path": "06_AGENTS/Use-Case-Mode-Architecture.md", "role": "Mode-aware runtime context routing"},
)


_NODE_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "identity_doctrine",
        "parent": "SOUL / Principles / Doctrine",
        "children": ["values", "doctrine", "discipline", "decision rules", "agent behavior preferences"],
        "index_targets": ["SOUL.md", "00_HOME/Principles.md", "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md"],
    },
    {
        "id": "personal_domains",
        "parent": "00_HOME/Operating-System.md",
        "children": ["fitness", "interests", "languages", "networking", "hardware", "future domains"],
        "index_targets": ["00_HOME/Personal-Domains/Personal-Domains-Index.md"],
    },
    {
        "id": "project_operating_files",
        "parent": "01_PROJECTS/Projects-Hub.md",
        "children": ["active projects", "paused projects", "module-to-project bridges", "creator/business lanes"],
        "index_targets": ["01_PROJECTS/*/*-OS.md", "01_PROJECTS/University/Modules/Modules.md"],
    },
    {
        "id": "knowledge_domains",
        "parent": CANONICAL_KNOWLEDGE_INDEX_PATH,
        "children": ["technical disciplines", "trading", "doctrine", "fitness", "language", "content", "runtime ops"],
        "index_targets": ["02_KNOWLEDGE/*/*.md"],
    },
    {
        "id": "personal_map_candidates",
        "parent": "06_AGENTS/Personal-Map-Architecture.md",
        "children": ["profile nodes", "profile edges", "candidate review deck", "apply decision trail"],
        "index_targets": [PERSONAL_MAP_CANDIDATE_DIR],
    },
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _presence(vault: Path, item: dict[str, str]) -> dict[str, Any]:
    path = vault / item["path"]
    return {
        "id": item["id"],
        "label": item["label"],
        "path": item["path"],
        "role": item["role"],
        "exists": path.exists(),
    }


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_vault": False,
        "writes_raw_intake": False,
        "writes_personal_map": False,
        "applies_personal_map": False,
        "writes_project_truth": False,
        "writes_knowledge": False,
        "writes_settings": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "workflow_execution_allowed": False,
        "agent_bus_dispatch_allowed": False,
        "canonical_mutation_allowed": False,
        "secret_values_read": False,
        "secret_values_stored": False,
    }


def _operator_context_summary(vault: Path) -> dict[str, Any]:
    try:
        context = build_personal_operator_context_index(vault)
        summary = dict(context.get("summary") or {})
        return {
            "ok": bool(context.get("ok")),
            "status": context.get("status"),
            "summary": summary,
            "missing_file_count": int(summary.get("missing_file_count") or 0),
            "link_blocker_count": int(summary.get("link_blocker_count") or 0),
            "link_warning_count": int(summary.get("link_warning_count") or 0),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "unavailable",
            "error": str(exc),
            "summary": {},
            "missing_file_count": 0,
            "link_blocker_count": 1,
            "link_warning_count": 0,
        }


def build_personal_context_import_panel(vault_root: str | Path) -> dict[str, Any]:
    """Return the personal-context import feature plan and readiness model."""

    vault = Path(vault_root).resolve()
    required_hubs = [_presence(vault, item) for item in _REQUIRED_HUBS]
    missing_required = [item for item in required_hubs if not item["exists"]]
    operator_context = _operator_context_summary(vault)
    root_shim = next(item for item in required_hubs if item["id"] == "knowledge_index_root_shim")
    canonical_index = next(item for item in required_hubs if item["id"] == "knowledge_index_master")

    status = "ready_for_review_preview"
    if missing_required:
        status = "blocked_missing_required_hubs"
    elif operator_context["link_blocker_count"]:
        status = "blocked_personal_context_links"
    elif operator_context["link_warning_count"]:
        status = "ready_with_context_warnings"

    readiness = {
        "personal_context_import_panel_mounted": True,
        "settings_entrypoint_ready": True,
        "dashboard_entrypoint_ready": True,
        "personal_operator_context_index_compatible": bool(operator_context.get("ok")),
        "workspace_mode_personal_os_target_declared": (vault / "00_HOME/.workspace-mode.yaml").exists(),
        "root_knowledge_index_resolved_as_shim": bool(root_shim["exists"]),
        "canonical_knowledge_index_available": bool(canonical_index["exists"]),
        "parent_child_plan_available": True,
        "raw_intake_storage_declared": True,
        "personal_map_candidate_storage_declared": True,
        "secret_storage_blocked": True,
        "approved_preview_writer_built": True,
        "approved_preview_writer_digest_gated": True,
        "approved_preview_writer_stores_source_text": False,
        "approved_preview_execution_proof_built": True,
        "approved_preview_execution_proof_digest_gated": True,
        "approved_preview_execution_proof_source_digest_gated": True,
        "approved_preview_artifact_writes_enabled": True,
        "writer_built": False,
        "approved_writer_built": False,
        "live_import_writes_enabled": False,
        "multi_instance_test_harness_built": True,
        "multi_instance_fixture_harness_temp_only": True,
        "multi_instance_fixture_harness_source_text_returned": False,
        "runtime_consumption_readiness_built": True,
        "runtime_reference_packet_ready": bool(operator_context.get("ok")),
        "runtime_reference_packet_source_text_returned": False,
        "raw_full_memory_injection_blocked": True,
        "canonical_promotion_approval_preview_built": True,
        "canonical_promotion_approval_queue_write_gated": True,
        "canonical_promotion_executor_built": True,
        "canonical_promotion_executor_approval_gated": True,
        "canonical_promotion_executor_exact_once": True,
        "canonical_promotion_protected_target_flag_required": True,
        "canonical_promotion_writes_enabled_after_approval": True,
        "runtime_consumption_live_verified": False,
        "personal_map_apply_readiness_built": True,
        "personal_map_apply_readiness_approval_queue_gated": True,
        "personal_map_approved_apply_executor_built": True,
        "personal_map_approved_apply_executor_exact_once": True,
        "personal_map_approved_apply_executor_approval_gated": True,
        "runtime_memory_mutation_readiness_built": True,
        "runtime_memory_mutation_readiness_approval_queue_gated": True,
        "runtime_memory_approved_mutation_executor_built": True,
        "runtime_memory_approved_mutation_executor_exact_once": True,
        "runtime_memory_approved_mutation_executor_approval_gated": True,
        "agent_bus_dispatch_packet_built": True,
        "agent_bus_dispatch_packet_preview_only": True,
        "provider_credential_readiness_built": True,
        "provider_credential_readiness_presence_only": True,
        "provider_execution_proof_built": True,
        "provider_execution_proof_keyed_on_env_presence": True,
        "end_to_end_manual_test_orchestrator_built": True,
        "next_recommended_pass": "personal-context-import-100-percent-closeout",
    }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "status": status,
        "headline": "Personal context import",
        "implementation_status": "READY_FOR_MANUAL_TESTING / 100_PERCENT_IMPLEMENTED_FOR_LOCAL_MANUAL_TEST",
        "feature_contract_path": FEATURE_CONTRACT_PATH,
        "summary": {
            "entrypoint_count": len(_ENTRYPOINTS),
            "pipeline_stage_count": len(_PIPELINE_STAGES),
            "required_hub_count": len(required_hubs),
            "missing_required_hub_count": len(missing_required),
            "node_family_count": len(_NODE_FAMILIES),
            "approved_preview_writer_ready": True,
            "approved_preview_execution_proof_ready": True,
            "multi_instance_fixture_harness_ready": True,
            "runtime_consumption_readiness_ready": True,
            "canonical_promotion_approval_preview_ready": True,
            "canonical_promotion_approved_executor_ready": True,
            "operator_context_status": operator_context.get("status"),
            "operator_context_link_blocker_count": operator_context.get("link_blocker_count"),
            "operator_context_link_warning_count": operator_context.get("link_warning_count"),
            "current_context_tracked_file_count": (operator_context.get("summary") or {}).get("tracked_file_count", 0),
        },
        "preview_writer": {
            "surface": PREVIEW_WRITER_SURFACE_ID,
            "status": "READY / DIGEST-GATED / APPROVAL QUEUE ONLY",
            "api_methods": list(PREVIEW_WRITER_API_METHODS),
            "queue_write_allowed_after_exact_digest": True,
            "source_text_stored_in_approval_packet": False,
            "raw_intake_writes_enabled": False,
            "personal_map_candidate_writes_enabled": False,
            "canonical_writes_enabled": False,
            "ambient_studio_execution_blocked": True,
            "next_recommended_pass": "personal-context-import-approved-preview-execution-proof",
        },
        "approved_preview_execution_proof": {
            "surface": APPROVED_PREVIEW_EXECUTOR_SURFACE_ID,
            "status": "READY / DIGEST-GATED / REVIEW ARTIFACT WRITES ONLY",
            "api_methods": list(APPROVED_PREVIEW_EXECUTOR_API_METHODS),
            "requires_approval_id": True,
            "requires_exact_import_preview_digest": True,
            "requires_matching_source_text_again": True,
            "writes_raw_intake_after_digest_match": True,
            "writes_review_artifacts_after_digest_match": True,
            "personal_map_candidates_staged_not_applied": True,
            "canonical_writes_enabled": False,
            "ambient_studio_execution_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "multi_instance_fixture_harness": {
            "surface": MULTI_INSTANCE_HARNESS_SURFACE_ID,
            "status": "READY / TEMP-FIXTURE PROOF / LIVE VAULT WRITES BLOCKED",
            "api_methods": list(MULTI_INSTANCE_HARNESS_API_METHODS),
            "runs_preview_writer": True,
            "runs_approved_preview_execution_proof": True,
            "uses_anonymized_fixture_packets": True,
            "writes_fixture_vaults_only": True,
            "writes_live_vault": False,
            "source_text_returned_in_payload": False,
            "checks_parent_child_rule_coverage": True,
            "checks_secret_blocking": True,
            "checks_canonical_write_block": True,
            "canonical_writes_enabled": False,
            "runtime_consumption_live_verified": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "runtime_consumption_readiness": {
            "surface": RUNTIME_CONSUMPTION_READINESS_SURFACE_ID,
            "status": "READY / REFERENCES ONLY / LIVE RUNTIME DISPATCH BLOCKED",
            "api_methods": list(RUNTIME_CONSUMPTION_READINESS_API_METHODS),
            "builds_runtime_reference_packet": True,
            "uses_personal_operator_context_index": True,
            "uses_workspace_mode_personal_os": True,
            "context_refs_only": True,
            "source_text_returned_in_payload": False,
            "raw_full_memory_injection_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "runtime_memory_mutation_allowed": False,
            "personal_map_apply_allowed": False,
            "canonical_writes_enabled": False,
            "runtime_consumption_live_verified": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "canonical_promotion_approval_preview": {
            "surface": CANONICAL_PROMOTION_APPROVAL_PREVIEW_SURFACE_ID,
            "status": "READY / DIGEST-GATED APPROVAL PREVIEW / CANONICAL WRITES BLOCKED",
            "api_methods": list(CANONICAL_PROMOTION_APPROVAL_PREVIEW_API_METHODS),
            "previews_dashboard_personal_operator_projects_knowledge_targets": True,
            "requires_exact_canonical_promotion_digest": True,
            "approval_queue_write_allowed_after_exact_digest": True,
            "canonical_executor_built": True,
            "canonical_writes_enabled": False,
            "personal_map_apply_allowed": False,
            "runtime_memory_mutation_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "provider_calls_allowed": False,
            "credential_reads_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "canonical_promotion_approved_executor": {
            "surface": CANONICAL_PROMOTION_APPROVED_EXECUTOR_SURFACE_ID,
            "status": "READY / APPROVAL-CONSUMED / CANONICAL ROUTE BLOCK WRITER",
            "api_methods": list(CANONICAL_PROMOTION_APPROVED_EXECUTOR_API_METHODS),
            "requires_approval_id": True,
            "requires_exact_canonical_promotion_digest": True,
            "requires_operator_approval_statement": True,
            "requires_execute_flag": True,
            "requires_protected_target_flag_for_operating_system": True,
            "writes_dashboard_personal_operator_projects_knowledge_targets": True,
            "writes_managed_route_blocks_only": True,
            "exact_once_marker_required": True,
            "rollback_snapshot_written": True,
            "canonical_writes_enabled_after_approval": True,
            "personal_map_apply_allowed": False,
            "runtime_memory_mutation_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "provider_calls_allowed": False,
            "credential_reads_allowed": False,
            "raw_full_memory_injection_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "knowledge_index_resolution": {
            "canonical_index_path": CANONICAL_KNOWLEDGE_INDEX_PATH,
            "root_shim_path": ROOT_KNOWLEDGE_SHIM_PATH,
            "root_file_role": "routing_shim_not_canonical",
            "duplicates_resolved_by_policy": True,
            "rule": "Use the 02_KNOWLEDGE master index for domain taxonomy; use the root uppercase file only for compatibility routing.",
        },
        "entrypoints": [dict(item) for item in _ENTRYPOINTS],
        "pipeline_stages": [dict(item) for item in _PIPELINE_STAGES],
        "required_hubs": required_hubs,
        "missing_required_hubs": missing_required,
        "node_families": [dict(item) for item in _NODE_FAMILIES],
        "storage_policy": {
            "raw_context_dir": RAW_INTAKE_DIR,
            "review_maps_dir": RAW_INTAKE_DIR,
            "personal_map_candidate_dir": PERSONAL_MAP_CANDIDATE_DIR,
            "canonical_targets": [
                "00_HOME/",
                "01_PROJECTS/",
                "02_KNOWLEDGE/",
                "06_AGENTS/",
            ],
            "canonical_targets_require_review": True,
            "public_core_export_policy": "populated personal context stays private or becomes templates/redacted examples",
            "secrets_policy": "Do not store credentials, wallet keys, exchange keys, API keys, passwords, webhook URLs, or token values in context imports.",
        },
        "runtime_context_contract": {
            "workspace_mode": "personal_os",
            "primary_read_model": "runtime.studio.personal_operator_context_index.build_personal_operator_context_index",
            "reference_packet_readiness": "runtime.studio.personal_context_import_runtime_consumption_readiness.build_personal_context_import_runtime_consumption_readiness",
            "runtime_delivery": [
                "agents receive bounded context references rather than raw context bodies",
                "agents read Personal Operator Index and relevant project/knowledge nodes only when explicitly referenced",
                "WML supplies mode-aware route context but does not grant permission",
                "Personal Map candidates remain review/apply-gated before runtime memory use",
                "Agent Bus tasks should receive scoped reference packets only after a later approved dispatch path",
            ],
        },
        "future_test_strategy": [
            "Run the preview planner and approved-preview execution proof against multiple anonymized personal-context packets.",
            "Assert parent nodes, child nodes, graph links, dashboard, project hub, and knowledge index routes are proposed.",
            "Assert raw imports remain Tier 4 and no secrets are surfaced.",
            "Assert fixture executions write only temp raw/review/proof artifacts and no live vault canonical state.",
            "Assert runtimes can consume the Personal Operator Context read model without provider calls or canonical mutation.",
        ],
        "operator_context": operator_context,
        "readiness": readiness,
        "authority": _authority(),
    }
