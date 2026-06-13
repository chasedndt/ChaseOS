"""Static Studio visual quality assurance for the Capture Markdown panel.

The harness renders the production Studio shell with a temporary reviewed Capture to Markdown
fixture, captures desktop/mobile screenshots, and clicks the source-pack
approval preview, approved source-pack write, Agent Orchestration Runtime dispatch readiness,
Agent Orchestration Runtime approval-design preview, and create-only Agent Orchestration Runtime approval-request writer
controls plus the read-only approval decision/consumption readiness action
and create-only approval decision writer plus the exact-once approval
consumption executor, the guarded Agent Bus task writer, the read-only task
claim-readiness proof, the guarded task-claim executor, the read-only
claimed-task Agent Orchestration Runtime preview readiness proof, and the guarded full-dispatch
executor plus the read-only Source Intelligence Core ingestion readiness proof
and Source Intelligence Core ingestion approval-design proof plus the
create-only Source Intelligence Core ingestion approval-request writer and
read-only Source Intelligence Core approval decision/consumption readiness
plus the create-only Source Intelligence Core approval decision writer
and exact-once Source Intelligence Core approval-consumption executor
plus read-only Source Intelligence Core graph-indexing readiness preview,
guarded Source Intelligence Core graph snapshot writing, read-only
canonical-promotion readiness, read-only canonical-promotion approval design,
the create-only canonical-promotion approval-request writer, and read-only
canonical-promotion approval decision/consumption readiness, create-only
canonical-promotion approval decision writing, and exact-once canonical-promotion
approval consumption plus the guarded canonical-promotion executor through the
real Studio panel adapter.
It writes visual quality assurance evidence only in the selected output directory and
temporary source-pack/request/decision/consumption/full-dispatch/Source Intelligence Core request artifacts
inside disposable fixtures.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any

from runtime.studio.capture_to_markdown_panel import (
    build_capture_to_markdown_panel,
    claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task,
    execute_capture_to_markdown_source_pack_write,
    preview_capture_to_markdown_source_pack_approval,
    preview_capture_to_markdown_source_pack_aor_dispatch_approval_design,
    preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness,
    preview_capture_to_markdown_source_pack_aor_dispatch_readiness,
    request_capture_to_markdown_source_pack_aor_dispatch_approval,
    review_capture_to_markdown,
    save_capture_to_markdown,
    consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision,
    consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision,
    preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness,
    preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness,
    execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run,
    execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle,
    execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch,
    preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness,
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision_consumption_readiness,
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision,
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_design,
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_request,
    preview_capture_to_markdown_source_pack_sic_ingestion_readiness,
    ingest_capture_to_markdown_source_pack_sic_ingestion,
    index_capture_to_markdown_source_pack_sic_graph_indexing,
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_design,
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision,
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption,
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness,
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_request,
    preview_capture_to_markdown_source_pack_canonical_promotion,
    preview_capture_to_markdown_source_pack_canonical_promotion_readiness,
    preview_capture_to_markdown_source_pack_sic_graph_indexing_readiness,
    write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task,
    write_capture_to_markdown_source_pack_aor_dispatch_approval_decision,
)


MODEL_VERSION = "studio.capture_markdown_visual_qa.v33"
SURFACE_ID = "capture_markdown_visual_qa"
PASS_ID = (
    "visual-capture-markdown-ingestion-pass44-source-pack-canonical-promotion-executor"
)
STATUS = "PARTIAL / CAPTURE MARKDOWN SOURCE-PACK CANONICAL PROMOTION EXECUTOR USER INTERFACE / VERIFIED"
NEXT_RECOMMENDED_PASS = (
    "visual-capture-markdown-ingestion-pass45-live-capture-ocr-and-packaged-desktop-proof"
)
DEFAULT_OUTPUT_DIR = Path("07_LOGS") / "Studio-Visual-QA" / "2026-05-27-vcmi-pass44-source-pack-canonical-promotion-executor-user-interface"
UI_TIMEOUT_MS = 30_000
TEXT_TIMEOUT_MS = 10_000

PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15"
    "c4890000000d49444154789c6360000002000100ffff03000006000557bfab"
    "d40000000049454e44ae426082"
)

REQUIRED_TOKENS = (
    "Attachment disposition",
    "metadata policy only",
    "delete-requested",
    "blocked",
    "Recent Captures",
    "Review",
    "Needs redaction",
    "Source-Pack Approval Preview",
    "Approval preview",
    "Digest",
    "Write targets",
    "Write Pack",
    "Source-Pack Write",
    "Written",
    "Agent Orchestration Runtime Readiness",
    "Agent Orchestration Runtime Dispatch Readiness",
    "Agent Orchestration Runtime dispatch",
    "Agent Bus",
    "Approval Design",
    "Agent Orchestration Runtime Approval Design",
    "Approval digest",
    "Future approval",
    "Approval artifact",
    "not written",
    "Write Request",
    "Approval Request",
    "Request written",
    "Approval decision",
    "Decision Readiness",
    "Approval Decision Readiness",
    "Request verified",
    "Decision writer",
    "future ready",
    "Approve",
    "Reject",
    "Approval Decision",
    "Decision written",
    "Consumption Preview",
    "Approval Consumption Preview",
    "Consume Decision",
    "Approval Consumption",
    "Decision consumed",
    "Marker written",
    "Consumption written",
    "Agent Bus Task Preview",
    "Task digest",
    "Write Agent Bus Task",
    "Agent Bus Task",
    "Task written",
    "Task artifact",
    "Task claimed",
    "Task Claim Readiness",
    "Claim Task",
    "Task Claim",
    "Claimable",
    "Route",
    "Runtime liveness",
    "Claim executor",
    "Agent Orchestration Runtime Preview Readiness",
    "Claimed task",
    "Agent Orchestration Runtime contracts",
    "Preview packet",
    "Agent Orchestration Runtime called",
    "Agent Orchestration Runtime preview OK",
    "Preview marker",
    "OSRIL session",
    "OSRIL event",
    "Agent Orchestration Runtime audit",
    "Preview artifact",
    "Request Task Review",
    "Task Status Lifecycle",
    "Review requested",
    "Status marker",
    "Status artifact",
    "Full Dispatch Readiness",
    "Ready for executor",
    "Future packet",
    "Run Full Dispatch",
    "Full dispatch complete",
    "Full Dispatch",
    "Agent Orchestration Runtime result",
    "Source-pack writeback",
    "Source Intelligence Core Readiness",
    "Source Intelligence Core Ingestion Readiness",
    "Source Intelligence Core readiness verified",
    "Source Intelligence Core contracts",
    "Source Intelligence Core Approval Design",
    "Source Intelligence Core approval design ready",
    "Approval packet",
    "Approval request",
    "Source packages",
    "Write Source Intelligence Core Approval Request",
    "Source Intelligence Core Approval Request",
    "Source Intelligence Core approval request written",
    "Source Intelligence Core Decision Readiness",
    "Source Intelligence Core decision readiness verified",
    "Approve Source Intelligence Core",
    "Source Intelligence Core Approval Decision",
    "Source Intelligence Core approval decision written",
    "Ready for approval consumption",
    "Source Intelligence Core Approval Consumption Preview",
    "Source Intelligence Core approval consumption preview ready",
    "Consume Source Intelligence Core Decision",
    "Source Intelligence Core Approval Consumption",
    "Source Intelligence Core approval decision consumed",
    "Artifact written",
    "Approval consumed",
    "Source Intelligence Core Ingestion Preview",
    "Source Intelligence Core ingestion preview ready",
    "Ingest into Source Intelligence Core",
    "Source Intelligence Core Ingestion",
    "Source Intelligence Core ingestion complete",
    "Graph Indexing Readiness Preview",
    "Graph indexing executor preview ready",
    "Graph Readiness",
    "Candidate digest",
    "Write Graph Snapshot",
    "Graph snapshot written",
    "Graph store",
    "Canonical Promotion Readiness",
    "Canonical promotion readiness ready",
    "Canonical readiness",
    "Canonical Approval Design",
    "Canonical approval design ready",
    "Canonical approval",
    "Request digest",
    "Future targets",
    "Write Canonical Request",
    "Canonical request written",
    "Canonical Decision Readiness",
    "Canonical decision readiness verified",
    "Decision options",
    "Approve Canonical Promotion",
    "Canonical Approval Decision",
    "Canonical approval decision written",
    "Ready for approval consumption",
    "Consume Canonical Decision",
    "Canonical Approval Consumption",
    "Canonical approval decision consumed",
    "Promote Canonical Knowledge",
    "Canonical knowledge promoted",
    "Canonical Promotion",
    "Knowledge note",
    "Knowledge index",
    "Request verified",
    "Decision writer ready",
    "Executor ready",
    "Canonical write",
    "Workspace written",
    "Source package written",
    "Workspace membership",
    "Future packet",
    "Graph",
    "Provider",
    "External",
    "Runtime process",
    "No Agent Bus task body execution",
    "I approve dispatching this reviewed Capture to Markdown source pack through Agent Orchestration Runtime.",
    "I approve writing this reviewed Capture to Markdown capture as an acquisition source pack.",
    "I approve Capture to Markdown Agent Orchestration Runtime dispatch approval request",
    "I consume Capture to Markdown Agent Orchestration Runtime dispatch approval decision",
    "I write Capture to Markdown Agent Orchestration Runtime dispatch Agent Bus task",
    "I run Capture to Markdown Agent Orchestration Runtime preview",
    "I update Capture to Markdown Agent Bus task",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _relative_to_vault(vault: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = vault / resolved
    try:
        return resolved.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_output_dir(vault: Path, output_dir: str | Path | None) -> Path:
    raw = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Capture Markdown visual quality assurance output must stay inside the vault") from exc
    return resolved


def _write_png(vault: Path) -> Path:
    target = vault / "07_LOGS" / "Operator-Screenshots" / "local" / "default" / "screenshot.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PNG_BYTES)
    return target


def _seed_downstream_contracts(vault: Path) -> None:
    now = vault / "00_HOME" / "Now.md"
    now.parent.mkdir(parents=True, exist_ok=True)
    now.write_text(
        "# Now\n\n## Current Phase\nPhase 9 visual quality assurance fixture\n\n## Active Now\n- Capture Markdown Agent Orchestration Runtime preview fixture\n",
        encoding="utf-8",
    )
    workflow = vault / "runtime" / "workflows" / "registry" / "source_pack_builder.yaml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "\n".join(
            [
                "id: source_pack_builder",
                "workflow_id: source_pack_builder",
                "name: Source Pack Builder",
                "version: '1.0'",
                "description: Source pack builder visual quality assurance fixture",
                "status: active",
                "task_type: source-pack-builder",
                "role_card: source-pack-builder",
                "trigger_type: manual",
                "owner: operator",
                "permission_ceiling: acquisition_pack_only",
                "connector_policy:",
                "  browser_automation: disabled",
                "writeback_targets:",
                "  - runtime/acquisition/packs/",
                "  - 07_LOGS/Acquisition-Packs/",
                "non_goals:",
                "  - no canonical state mutation",
                "failure_behavior: escalate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    task_table = vault / "runtime" / "aor" / "task_type_table.yaml"
    task_table.parent.mkdir(parents=True, exist_ok=True)
    task_table.write_text(
        "\n".join(
            [
                "task_types:",
                "  - id: source-pack-builder",
                "    permission_ceiling: acquisition_pack_only",
                "    notes: no canonical mutations; canonical mutation requested must escalate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    role_card = vault / "06_AGENTS" / "role-cards" / "source-pack-builder.yaml"
    role_card.parent.mkdir(parents=True, exist_ok=True)
    role_card.write_text(
        "\n".join(
            [
                "id: source-pack-builder",
                "name: Source Pack Builder",
                "version: '1.0'",
                "description: Source pack builder visual quality assurance role card",
                "owner: operator",
                "allowed_actions:",
                "  - read_declared_source_files",
                "  - write_runtime_acquisition_pack",
                "forbidden_actions:",
                "  - access_credentials",
                "  - browse_live_web",
                "  - mutate_canonical_state",
                "write_scope:",
                "  - runtime/acquisition/packs/",
                "  - 07_LOGS/Acquisition-Packs/",
                "forbidden_write_zones:",
                "  - 00_HOME/",
                "  - 02_KNOWLEDGE/",
                "escalation_rules:",
                "  - unsupported source scope",
                "runtime_expectations:",
                "  - dry run skips writeback",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    schema = vault / "runtime" / "source_intelligence" / "schemas" / "source_package_schema.md"
    schema.parent.mkdir(parents=True, exist_ok=True)
    schema.write_text(
        "# Source Package Schema\n\n"
        "Required normalized source-package fields include `normalized_text`, "
        "`origin_path`, and `user_trust_level`.\n",
        encoding="utf-8",
    )
    (vault / "runtime" / "source_intelligence" / "workspaces").mkdir(parents=True, exist_ok=True)
    openclaw_caps = vault / "runtime" / "openclaw" / "capabilities.yaml"
    openclaw_caps.parent.mkdir(parents=True, exist_ok=True)
    openclaw_caps.write_text(
        "\n".join(
            [
                "runtime: openclaw",
                "bus_name: OpenClaw",
                "handles:",
                "  - task_type: source-pack-builder",
                "    priority: primary",
                "max_concurrent_tasks: 3",
                "heartbeat_stale_seconds: 900",
                "priority_ceiling: normal",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _seed_fixture(vault: Path) -> dict[str, Any]:
    _seed_downstream_contracts(vault)
    _write_png(vault)
    saved = save_capture_to_markdown(
        vault,
        {
            "source_mode": "screenshot_attachment",
            "profile": "research_note",
            "title": "Capture to Markdown Pass 14 quality assurance",
            "file_path": "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            "user_intent": "verify Studio visual quality assurance and attachment disposition policy",
            "structured_notes": "- temporary fixture only",
        },
    )
    if not saved.get("ok"):
        raise RuntimeError(f"failed to seed Capture to Markdown visual quality assurance fixture: {saved}")
    review_capture_to_markdown(
        vault,
        {
            "sidecar_path": saved["sidecar_path"],
            "decision": "reviewed",
            "reviewed_by": "visual-qa",
            "review_note": "reviewed fixture for source-pack approval preview visual quality assurance",
        },
    )
    panel = build_capture_to_markdown_panel(vault, recent_limit=10)
    return {"saved": saved, "panel": panel}


def _pywebview_stub(panel_data: dict[str, Any]) -> str:
    payload = json.dumps(panel_data, sort_keys=True, default=str)
    return f"""
(() => {{
  let capturePanel = {payload};
  const api = {{
    get_capture_to_markdown_panel: async () => ({{ ok: true, data: capturePanel }}),
    preview_capture_to_markdown: async () => ({{ ok: true, data: {{ status: "preview_only", markdown: "", save_allowed: true, blockers: [] }} }}),
    save_capture_to_markdown: async () => ({{ ok: false, error: {{ message: "visual quality assurance save disabled" }} }}),
    review_capture_to_markdown: async (payload) => {{
      const resp = await window.__vcmiReviewCapture(payload);
      if (resp && resp.ok && resp.data && resp.data.recent_captures) {{
        capturePanel.recent_captures = resp.data.recent_captures;
      }}
      return resp;
    }},
    preview_capture_to_markdown_source_pack_approval: async (payload) => {{
      return await window.__vcmiPreviewSourcePackApproval(payload);
    }},
    execute_capture_to_markdown_source_pack_write: async (payload) => {{
      return await window.__vcmiExecuteSourcePackWrite(payload);
    }},
    preview_capture_to_markdown_source_pack_aor_dispatch_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackAorReadiness(payload);
    }},
    preview_capture_to_markdown_source_pack_aor_dispatch_approval_design: async (payload) => {{
      return await window.__vcmiPreviewSourcePackAorApprovalDesign(payload);
    }},
    request_capture_to_markdown_source_pack_aor_dispatch_approval: async (payload) => {{
      return await window.__vcmiRequestSourcePackAorApproval(payload);
    }},
    preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackAorApprovalConsumptionReadiness(payload);
    }},
    write_capture_to_markdown_source_pack_aor_dispatch_approval_decision: async (payload) => {{
      return await window.__vcmiWriteSourcePackAorApprovalDecision(payload);
    }},
    consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision: async (payload) => {{
      return await window.__vcmiConsumeSourcePackAorApprovalDecision(payload);
    }},
    write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task: async (payload) => {{
      return await window.__vcmiWriteSourcePackAorAgentBusTask(payload);
    }},
    preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackAorAgentBusTaskClaimReadiness(payload);
    }},
    claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task: async (payload) => {{
      return await window.__vcmiClaimSourcePackAorAgentBusTask(payload);
    }},
    preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackAorClaimedTaskDryRunReadiness(payload);
    }},
    execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run: async (payload) => {{
      return await window.__vcmiExecuteSourcePackAorClaimedTaskDryRun(payload);
    }},
    execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle: async (payload) => {{
      return await window.__vcmiExecuteSourcePackAorClaimedTaskStatusLifecycle(payload);
    }},
    preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackAorFullDispatchReadiness(payload);
    }},
    execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch: async (payload) => {{
      return await window.__vcmiExecuteSourcePackAorFullDispatch(payload);
    }},
    preview_capture_to_markdown_source_pack_sic_ingestion_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackSicIngestionReadiness(payload);
    }},
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_design: async (payload) => {{
      return await window.__vcmiPreviewSourcePackSicIngestionApprovalDesign(payload);
    }},
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_request: async (payload) => {{
      return await window.__vcmiPreviewSourcePackSicIngestionApprovalRequest(payload);
    }},
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision_consumption_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackSicIngestionApprovalDecisionReadiness(payload);
    }},
    preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision: async (payload) => {{
      return await window.__vcmiPreviewSourcePackSicIngestionApprovalDecision(payload);
    }},
    consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision: async (payload) => {{
      return await window.__vcmiConsumeSourcePackSicIngestionApprovalDecision(payload);
    }},
    ingest_capture_to_markdown_source_pack_sic_ingestion: async (payload) => {{
      return await window.__vcmiIngestSourcePackSicIngestion(payload);
    }},
    preview_capture_to_markdown_source_pack_sic_graph_indexing_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackSicGraphIndexingReadiness(payload);
    }},
    index_capture_to_markdown_source_pack_sic_graph_indexing: async (payload) => {{
      return await window.__vcmiIndexSourcePackSicGraphIndexing(payload);
    }},
    preview_capture_to_markdown_source_pack_canonical_promotion_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackCanonicalPromotionReadiness(payload);
    }},
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_design: async (payload) => {{
      return await window.__vcmiPreviewSourcePackCanonicalPromotionApprovalDesign(payload);
    }},
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_request: async (payload) => {{
      return await window.__vcmiPreviewSourcePackCanonicalPromotionApprovalRequest(payload);
    }},
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness: async (payload) => {{
      return await window.__vcmiPreviewSourcePackCanonicalPromotionApprovalDecisionReadiness(payload);
    }},
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision: async (payload) => {{
      return await window.__vcmiPreviewSourcePackCanonicalPromotionApprovalDecision(payload);
    }},
    preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption: async (payload) => {{
      return await window.__vcmiPreviewSourcePackCanonicalPromotionApprovalConsumption(payload);
    }},
    preview_capture_to_markdown_source_pack_canonical_promotion: async (payload) => {{
      return await window.__vcmiPreviewSourcePackCanonicalPromotion(payload);
    }},
    get_intake_panel: async () => ({{ ok: true, data: {{ items: [] }} }}),
    get_panel_registry: async () => ({{ ok: true, data: {{ panels: [], readiness: {{}}, authority: {{ read_only_registry: true }} }} }}),
    get_dashboard: async () => ({{ ok: true, data: {{ cards: [], summary: {{}} }} }}),
    get_runtime_status: async () => ({{ ok: true, data: {{ status: "visual-qa-stub" }} }}),
  }};
  window.pywebview = {{
    api: new Proxy(api, {{
      get(target, prop) {{
        return target[prop] || (async () => ({{ ok: true, data: {{}} }}));
      }}
    }})
  }};
}})();
"""


def _authority() -> dict[str, Any]:
    return {
        "visual_evidence_allowed": True,
        "temporary_fixture_created": True,
        "temporary_fixture_persisted": False,
        "review_state_write_allowed_in_fixture": True,
        "source_pack_approval_preview_allowed_in_fixture": True,
        "source_pack_write_allowed_in_fixture": True,
        "source_pack_aor_dispatch_readiness_allowed_in_fixture": True,
        "source_pack_aor_dispatch_approval_design_allowed_in_fixture": True,
        "source_pack_aor_dispatch_approval_request_write_allowed_in_fixture": True,
        "source_pack_aor_dispatch_approval_consumption_readiness_allowed_in_fixture": True,
        "source_pack_aor_dispatch_approval_decision_write_allowed_in_fixture": True,
        "source_pack_aor_dispatch_approval_consumption_allowed_in_fixture": True,
        "source_pack_sic_ingestion_allowed_in_fixture": True,
        "source_pack_sic_graph_indexing_allowed_in_fixture": True,
        "source_pack_canonical_promotion_readiness_allowed_in_fixture": True,
        "source_pack_canonical_promotion_approval_design_allowed_in_fixture": True,
        "source_pack_canonical_promotion_approval_request_write_allowed_in_fixture": True,
        "source_pack_canonical_promotion_approval_decision_readiness_allowed_in_fixture": True,
        "source_pack_canonical_promotion_approval_decision_write_allowed_in_fixture": True,
        "source_pack_canonical_promotion_approval_consumption_allowed_in_fixture": True,
        "source_pack_canonical_promotion_executor_allowed_in_fixture": True,
        "source_pack_sic_graph_indexing_allowed_in_real_vault": False,
        "source_pack_canonical_promotion_allowed_in_real_vault": False,
        "source_pack_aor_dispatch_agent_bus_task_write_allowed_in_fixture": True,
        "source_pack_write_allowed_in_real_vault": False,
        "approval_artifact_write_allowed_in_fixture": True,
        "approval_request_write_allowed_in_fixture": True,
        "approval_artifact_write_allowed_in_real_vault": False,
        "approval_request_write_allowed_in_real_vault": False,
        "approval_decision_write_allowed_in_fixture": True,
        "approval_decision_write_allowed_in_real_vault": False,
        "approval_consumption_allowed": True,
        "approval_consumption_allowed_in_real_vault": False,
        "agent_bus_task_write_allowed": True,
        "agent_bus_task_write_allowed_in_real_vault": False,
        "agent_bus_task_claim_readiness_allowed": True,
        "agent_bus_task_claim_readiness_allowed_in_real_vault": False,
        "agent_bus_task_claim_allowed": True,
        "agent_bus_task_claim_allowed_in_real_vault": False,
        "claimed_task_aor_dry_run_readiness_allowed": True,
        "claimed_task_aor_dry_run_readiness_allowed_in_real_vault": False,
        "claimed_task_aor_dry_run_executor_allowed": True,
        "claimed_task_aor_dry_run_executor_allowed_in_real_vault": False,
        "aor_dry_run_call_allowed": True,
        "aor_dry_run_call_allowed_in_real_vault": False,
        "claimed_task_execution_status_lifecycle_allowed": True,
        "claimed_task_execution_status_lifecycle_allowed_in_real_vault": False,
        "full_dispatch_readiness_allowed": True,
        "full_dispatch_readiness_allowed_in_real_vault": False,
        "full_dispatch_executor_allowed": True,
        "full_dispatch_executor_allowed_in_real_vault": False,
        "source_pack_writeback_allowed": True,
        "source_pack_writeback_allowed_in_real_vault": False,
        "agent_bus_task_execute_allowed": False,
        "real_vault_capture_write_allowed": False,
        "real_vault_review_write_allowed": False,
        "attachment_delete_allowed": False,
        "attachment_cleanup_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "external_send_allowed": False,
        "sic_ingestion_allowed": False,
        "aor_dispatch_allowed": True,
        "aor_dispatch_allowed_in_real_vault": False,
        "canonical_mutation_allowed": False,
        "secret_or_credential_read_allowed": False,
    }


def _run_playwright_visual_qa(vault: Path, output_dir: Path) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    index_path = _repo_root() / "runtime" / "studio" / "shell" / "frontend" / "index.html"
    url = f"{index_path.resolve().as_uri()}#/capture-markdown"
    screenshots: list[dict[str, Any]] = []
    console_messages: list[str] = []
    page_errors: list[str] = []
    fixtures: list[dict[str, Any]] = []
    fixture_base = output_dir.parent / "_vcmi_p44_fixtures"
    write_results: dict[str, dict[str, Any]] = {}
    readiness_results: dict[str, dict[str, Any]] = {}
    approval_design_results: dict[str, dict[str, Any]] = {}
    approval_request_results: dict[str, dict[str, Any]] = {}
    approval_consumption_readiness_results: dict[str, dict[str, Any]] = {}
    approval_decision_results: dict[str, dict[str, Any]] = {}
    approval_consumption_results: dict[str, dict[str, Any]] = {}
    agent_bus_task_results: dict[str, dict[str, Any]] = {}
    agent_bus_task_claim_readiness_results: dict[str, dict[str, Any]] = {}
    agent_bus_task_claim_results: dict[str, dict[str, Any]] = {}
    agent_bus_claimed_task_dry_run_readiness_results: dict[str, dict[str, Any]] = {}
    agent_bus_claimed_task_dry_run_results: dict[str, dict[str, Any]] = {}
    agent_bus_claimed_task_status_lifecycle_results: dict[str, dict[str, Any]] = {}
    agent_bus_full_dispatch_readiness_results: dict[str, dict[str, Any]] = {}
    agent_bus_full_dispatch_preview_results: dict[str, dict[str, Any]] = {}
    agent_bus_full_dispatch_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_readiness_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_approval_design_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_approval_request_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_decision_readiness_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_approval_decision_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_approval_consumption_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_ingestion_preview_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_ingestion_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_graph_readiness_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_graph_indexing_preview_results: dict[str, dict[str, Any]] = {}
    source_pack_sic_graph_indexing_results: dict[str, dict[str, Any]] = {}
    source_pack_canonical_promotion_readiness_results: dict[str, dict[str, Any]] = {}
    source_pack_canonical_promotion_approval_design_results: dict[str, dict[str, Any]] = {}
    source_pack_canonical_promotion_approval_request_results: dict[str, dict[str, Any]] = {}
    source_pack_canonical_promotion_decision_readiness_results: dict[str, dict[str, Any]] = {}
    source_pack_canonical_promotion_approval_decision_results: dict[str, dict[str, Any]] = {}
    source_pack_canonical_promotion_approval_consumption_results: dict[str, dict[str, Any]] = {}
    source_pack_canonical_promotion_results: dict[str, dict[str, Any]] = {}

    for viewport_name, fixture_slug, viewport in (
        ("desktop", "_d", {"width": 1440, "height": 1000}),
        ("mobile", "_m", {"width": 390, "height": 900}),
    ):
        # Keep disposable fixture roots short so guarded marker paths remain
        # under Windows path-length limits during Playwright callback writes.
        fixture_vault = (fixture_base / fixture_slug).resolve()
        if fixture_vault.exists():
            shutil.rmtree(fixture_vault)
        fixture_vault.mkdir(parents=True)
        fixtures.append(
            {
                "viewport_name": viewport_name,
                "viewport": viewport,
                "fixture_vault": fixture_vault,
                "fixture": _seed_fixture(fixture_vault),
            }
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for item in fixtures:
                viewport_name = item["viewport_name"]
                viewport = item["viewport"]
                fixture_vault = item["fixture_vault"]
                fixture = item["fixture"]

                def _review_capture(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = review_capture_to_markdown(fixture_vault, payload or {})
                        return {"ok": True, "data": data}
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_approval(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_approval(fixture_vault, payload or {})
                        return {"ok": True, "data": data}
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _execute_source_pack_write(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = execute_capture_to_markdown_source_pack_write(fixture_vault, payload or {})
                        write_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_aor_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_aor_dispatch_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_aor_approval_design(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_aor_dispatch_approval_design(
                            fixture_vault,
                            payload or {},
                        )
                        approval_design_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _request_source_pack_aor_approval(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = request_capture_to_markdown_source_pack_aor_dispatch_approval(
                            fixture_vault,
                            payload or {},
                        )
                        approval_request_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_aor_approval_consumption_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_aor_dispatch_approval_consumption_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        approval_consumption_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _write_source_pack_aor_approval_decision(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = write_capture_to_markdown_source_pack_aor_dispatch_approval_decision(
                            fixture_vault,
                            payload or {},
                        )
                        approval_decision_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _consume_source_pack_aor_approval_decision(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = consume_capture_to_markdown_source_pack_aor_dispatch_approval_decision(
                            fixture_vault,
                            payload or {},
                        )
                        if data.get("write_performed"):
                            approval_consumption_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _write_source_pack_aor_agent_bus_task(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = write_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task(
                            fixture_vault,
                            payload or {},
                        )
                        if data.get("write_performed"):
                            agent_bus_task_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_aor_agent_bus_task_claim_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task_claim_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        agent_bus_task_claim_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _claim_source_pack_aor_agent_bus_task(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = claim_capture_to_markdown_source_pack_aor_dispatch_agent_bus_task(
                            fixture_vault,
                            payload or {},
                        )
                        if data.get("write_performed"):
                            agent_bus_task_claim_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_aor_claimed_task_dry_run_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = (
                            preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness(
                                fixture_vault,
                                payload or {},
                            )
                        )
                        agent_bus_claimed_task_dry_run_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _execute_source_pack_aor_claimed_task_dry_run(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = (
                            execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run(
                                fixture_vault,
                                payload or {},
                            )
                        )
                        if data.get("write_performed"):
                            agent_bus_claimed_task_dry_run_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _execute_source_pack_aor_claimed_task_status_lifecycle(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = (
                            execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle(
                                fixture_vault,
                                payload or {},
                            )
                        )
                        if data.get("write_performed"):
                            agent_bus_claimed_task_status_lifecycle_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_aor_full_dispatch_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = (
                            preview_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness(
                                fixture_vault,
                                payload or {},
                            )
                        )
                        agent_bus_full_dispatch_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _execute_source_pack_aor_full_dispatch(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        request = payload or {}
                        data = execute_capture_to_markdown_source_pack_aor_dispatch_agent_bus_full_dispatch(
                            fixture_vault,
                            request,
                        )
                        if request.get("run_full_dispatch") or data.get("aor_full_dispatch_performed"):
                            agent_bus_full_dispatch_results[viewport_name] = data
                        else:
                            agent_bus_full_dispatch_preview_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_sic_ingestion_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_sic_ingestion_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_sic_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_sic_ingestion_approval_design(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_sic_ingestion_approval_design(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_sic_approval_design_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_sic_ingestion_approval_request(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_sic_ingestion_approval_request(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_sic_approval_request_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_sic_ingestion_approval_decision_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision_consumption_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_sic_decision_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_sic_ingestion_approval_decision(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_sic_ingestion_approval_decision(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_sic_approval_decision_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _consume_source_pack_sic_ingestion_approval_decision(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = consume_capture_to_markdown_source_pack_sic_ingestion_approval_decision(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_sic_approval_consumption_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _ingest_source_pack_sic_ingestion(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = ingest_capture_to_markdown_source_pack_sic_ingestion(
                            fixture_vault,
                            payload or {},
                        )
                        if data.get("source_intelligence_core_ingestion_performed"):
                            source_pack_sic_ingestion_results[viewport_name] = data
                        else:
                            source_pack_sic_ingestion_preview_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_sic_graph_indexing_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_sic_graph_indexing_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_sic_graph_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _index_source_pack_sic_graph_indexing(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = index_capture_to_markdown_source_pack_sic_graph_indexing(
                            fixture_vault,
                            payload or {},
                        )
                        if payload and (
                            payload.get("write_graph_indexing_marker")
                            or payload.get("write_graph_snapshot")
                            or payload.get("write_graph_indexing_artifact")
                        ):
                            source_pack_sic_graph_indexing_results[viewport_name] = data
                        else:
                            source_pack_sic_graph_indexing_preview_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_canonical_promotion_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_canonical_promotion_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_canonical_promotion_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_canonical_promotion_approval_design(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_canonical_promotion_approval_design(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_canonical_promotion_approval_design_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_canonical_promotion_approval_request(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_canonical_promotion_approval_request(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_canonical_promotion_approval_request_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_canonical_promotion_decision_readiness(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision_consumption_readiness(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_canonical_promotion_decision_readiness_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_canonical_promotion_approval_decision(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_canonical_promotion_approval_decision(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_canonical_promotion_approval_decision_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_canonical_promotion_approval_consumption(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_canonical_promotion_approval_consumption(
                            fixture_vault,
                            payload or {},
                        )
                        source_pack_canonical_promotion_approval_consumption_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                def _preview_source_pack_canonical_promotion(payload: dict[str, Any]) -> dict[str, Any]:
                    try:
                        data = preview_capture_to_markdown_source_pack_canonical_promotion(
                            fixture_vault,
                            payload or {},
                        )
                        if payload and (
                            payload.get("write_canonical_promotion_marker")
                            or payload.get("write_canonical_knowledge_note")
                            or payload.get("write_canonical_knowledge_index")
                            or payload.get("write_canonical_promotion_artifact")
                        ):
                            source_pack_canonical_promotion_results[viewport_name] = data
                        if data.get("ok"):
                            return {"ok": True, "data": data}
                        return {
                            "ok": False,
                            "data": data,
                            "error": {"message": ", ".join(data.get("blockers") or []) or data.get("status")},
                        }
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": {"message": str(exc)}}

                page = browser.new_page(viewport=viewport)
                page.on("console", lambda msg: console_messages.append(f"{msg.type}:{msg.text}"))
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.expose_function("__vcmiReviewCapture", _review_capture)
                page.expose_function("__vcmiPreviewSourcePackApproval", _preview_source_pack_approval)
                page.expose_function("__vcmiExecuteSourcePackWrite", _execute_source_pack_write)
                page.expose_function("__vcmiPreviewSourcePackAorReadiness", _preview_source_pack_aor_readiness)
                page.expose_function(
                    "__vcmiPreviewSourcePackAorApprovalDesign",
                    _preview_source_pack_aor_approval_design,
                )
                page.expose_function("__vcmiRequestSourcePackAorApproval", _request_source_pack_aor_approval)
                page.expose_function(
                    "__vcmiPreviewSourcePackAorApprovalConsumptionReadiness",
                    _preview_source_pack_aor_approval_consumption_readiness,
                )
                page.expose_function(
                    "__vcmiWriteSourcePackAorApprovalDecision",
                    _write_source_pack_aor_approval_decision,
                )
                page.expose_function(
                    "__vcmiConsumeSourcePackAorApprovalDecision",
                    _consume_source_pack_aor_approval_decision,
                )
                page.expose_function(
                    "__vcmiWriteSourcePackAorAgentBusTask",
                    _write_source_pack_aor_agent_bus_task,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackAorAgentBusTaskClaimReadiness",
                    _preview_source_pack_aor_agent_bus_task_claim_readiness,
                )
                page.expose_function(
                    "__vcmiClaimSourcePackAorAgentBusTask",
                    _claim_source_pack_aor_agent_bus_task,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackAorClaimedTaskDryRunReadiness",
                    _preview_source_pack_aor_claimed_task_dry_run_readiness,
                )
                page.expose_function(
                    "__vcmiExecuteSourcePackAorClaimedTaskDryRun",
                    _execute_source_pack_aor_claimed_task_dry_run,
                )
                page.expose_function(
                    "__vcmiExecuteSourcePackAorClaimedTaskStatusLifecycle",
                    _execute_source_pack_aor_claimed_task_status_lifecycle,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackAorFullDispatchReadiness",
                    _preview_source_pack_aor_full_dispatch_readiness,
                )
                page.expose_function(
                    "__vcmiExecuteSourcePackAorFullDispatch",
                    _execute_source_pack_aor_full_dispatch,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackSicIngestionReadiness",
                    _preview_source_pack_sic_ingestion_readiness,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackSicIngestionApprovalDesign",
                    _preview_source_pack_sic_ingestion_approval_design,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackSicIngestionApprovalRequest",
                    _preview_source_pack_sic_ingestion_approval_request,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackSicIngestionApprovalDecisionReadiness",
                    _preview_source_pack_sic_ingestion_approval_decision_readiness,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackSicIngestionApprovalDecision",
                    _preview_source_pack_sic_ingestion_approval_decision,
                )
                page.expose_function(
                    "__vcmiConsumeSourcePackSicIngestionApprovalDecision",
                    _consume_source_pack_sic_ingestion_approval_decision,
                )
                page.expose_function(
                    "__vcmiIngestSourcePackSicIngestion",
                    _ingest_source_pack_sic_ingestion,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackSicGraphIndexingReadiness",
                    _preview_source_pack_sic_graph_indexing_readiness,
                )
                page.expose_function(
                    "__vcmiIndexSourcePackSicGraphIndexing",
                    _index_source_pack_sic_graph_indexing,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackCanonicalPromotionReadiness",
                    _preview_source_pack_canonical_promotion_readiness,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackCanonicalPromotionApprovalDesign",
                    _preview_source_pack_canonical_promotion_approval_design,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackCanonicalPromotionApprovalRequest",
                    _preview_source_pack_canonical_promotion_approval_request,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackCanonicalPromotionApprovalDecisionReadiness",
                    _preview_source_pack_canonical_promotion_decision_readiness,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackCanonicalPromotionApprovalDecision",
                    _preview_source_pack_canonical_promotion_approval_decision,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackCanonicalPromotionApprovalConsumption",
                    _preview_source_pack_canonical_promotion_approval_consumption,
                )
                page.expose_function(
                    "__vcmiPreviewSourcePackCanonicalPromotion",
                    _preview_source_pack_canonical_promotion,
                )
                page.add_init_script(_pywebview_stub(fixture["panel"]))
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_selector("#capture-markdown-policy-body .capture-markdown-policy-chip", timeout=UI_TIMEOUT_MS)
                page.wait_for_selector(".capture-markdown-recent-item", timeout=UI_TIMEOUT_MS)
                before_text = page.locator("#panel-capture-markdown").inner_text(timeout=TEXT_TIMEOUT_MS)
                page.wait_for_selector(".capture-markdown-approval-preview-btn", timeout=UI_TIMEOUT_MS)
                page.locator(".capture-markdown-approval-preview-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent.includes('Source-Pack Approval Preview')",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(".capture-markdown-source-pack-write-btn", timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-write-btn'); return button && !button.disabled && button.dataset.requestDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-write-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent.includes('Source-Pack Write') && (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent.includes('Written')",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(".capture-markdown-source-pack-aor-readiness-btn", timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-aor-readiness-btn'); return button && !button.disabled && button.dataset.requestDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-aor-readiness-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent.includes('Agent Orchestration Runtime Dispatch Readiness') && (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent.includes('blocked')",
                    timeout=UI_TIMEOUT_MS,
                )
                aor_readiness_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                page.wait_for_selector(".capture-markdown-source-pack-aor-approval-design-btn", timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-aor-approval-design-btn'); return button && !button.disabled && button.dataset.requestDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-aor-approval-design-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Agent Orchestration Runtime Approval Design') && text.includes('Approval artifact') && text.includes('not written'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                aor_approval_design_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                page.wait_for_selector(".capture-markdown-source-pack-aor-approval-request-btn", timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-aor-approval-request-btn'); return button && !button.disabled && button.dataset.approvalRequestDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-aor-approval-request-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Approval Request') && text.includes('Request written') && text.includes('Approval decision') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-aor-approval-consumption-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-aor-approval-consumption-readiness-btn'); return button && !button.disabled && button.dataset.approvalRequestDigest && button.dataset.approvalArtifactPath; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-aor-approval-consumption-readiness-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Approval Decision Readiness') && text.includes('Request verified') && text.includes('Consumption') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-aor-approval-decision-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-aor-approval-decision-btn'); return button && !button.disabled && button.dataset.approvalDecisionDigest && button.dataset.decision; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-aor-approval-decision-btn").first.click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Approval Decision') && text.includes('Decision written') && text.includes('Consumption') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-aor-approval-consume-preview-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-aor-approval-consume-preview-btn'); return button && !button.disabled && button.dataset.approvalDecisionArtifactPath && button.dataset.approvalDecisionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-aor-approval-consume-preview-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Approval Consumption Preview') && text.includes('Consumption digest') && text.includes('Consume Decision') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-aor-approval-consume-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-aor-approval-consume-btn'); return button && !button.disabled && button.dataset.approvalConsumptionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-aor-approval-consume-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Approval Consumption') && text.includes('Decision consumed') && text.includes('Marker written') && text.includes('Consumption written') && text.includes('Agent Bus') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-task-preview-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-task-preview-btn'); return button && !button.disabled && button.dataset.approvalConsumptionDigest && button.dataset.approvalConsumptionArtifactPath; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-task-preview-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Agent Bus Task Preview') && text.includes('Task digest') && text.includes('Write Agent Bus Task') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-task-write-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-task-write-btn'); return button && !button.disabled && button.dataset.agentBusTaskDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-task-write-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Agent Bus Task') && text.includes('Task written') && text.includes('Task artifact') && text.includes('Task claimed') && text.includes('Agent Orchestration Runtime dispatch') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-task-claim-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-task-claim-readiness-btn'); return button && !button.disabled && button.dataset.agentBusTaskArtifactPath && button.dataset.agentBusTaskId; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-task-claim-readiness-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Task Claim Readiness') && text.includes('Claimable') && text.includes('Claim executor') && text.includes('blocked'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-task-claim-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-task-claim-btn'); return button && !button.disabled && button.dataset.agentBusTaskClaimDigest && button.dataset.agentBusTaskId; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-task-claim-btn").click(timeout=UI_TIMEOUT_MS)
                try:
                    page.wait_for_function(
                        """
                        () => {
                          const root = document.querySelector('#capture-markdown-source-pack-preview-body');
                          const text = root ? root.textContent : '';
                          const lower = text.toLowerCase();
                          const msg = root ? (root.querySelector('.capture-markdown-source-pack-agent-bus-task-claim-msg') || {}).textContent || '' : '';
                          const success = lower.includes('task claim')
                            && lower.includes('task claimed')
                            && lower.includes('claim artifact')
                            && lower.includes('task executed')
                            && lower.includes('agent orchestration runtime dispatch');
                          const failed = msg.includes('blocked') || msg.includes('Missing') || msg.includes('failed') || msg.includes('mismatch') || msg.includes('not available');
                          return success || failed;
                        }
                        """,
                        timeout=UI_TIMEOUT_MS,
                    )
                except Exception as exc:  # noqa: BLE001
                    state = page.evaluate(
                        """
                        () => {
                          const root = document.querySelector('#capture-markdown-source-pack-preview-body');
                          const msg = root ? root.querySelector('.capture-markdown-source-pack-agent-bus-task-claim-msg') : null;
                          const result = root ? root.querySelector('.capture-markdown-source-pack-agent-bus-task-claim-result') : null;
                          return {
                            text: root ? root.textContent : '',
                            msg: msg ? msg.textContent : '',
                            result: result ? result.textContent : '',
                          };
                        }
                        """
                    )
                    raise AssertionError(
                        "Agent Bus task claim user interface timed out: "
                        + json.dumps(state, sort_keys=True, default=str)[-4000:]
                    ) from exc
                task_claim_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                task_claim_lower = task_claim_text.lower()
                task_claim_required_tokens = [
                    "task claim",
                    "task claimed",
                    "claim artifact",
                    "task executed",
                    "agent orchestration runtime dispatch",
                ]
                if any(token not in task_claim_lower for token in task_claim_required_tokens):
                    raise AssertionError(
                        "Agent Bus task claim user interface did not reach the verified state: "
                        + task_claim_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-btn'); return button && !button.disabled && button.dataset.agentBusTaskClaimDigest && button.dataset.agentBusTaskClaimArtifactPath; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-btn").click(timeout=UI_TIMEOUT_MS)
                try:
                    page.wait_for_function(
                        """
                        () => {
                          const root = document.querySelector('#capture-markdown-source-pack-preview-body');
                          const text = root ? root.textContent : '';
                          const msg = root ? (root.querySelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-msg') || {}).textContent || '' : '';
                          const lower = text.toLowerCase();
                          const packetPreviewVisible = lower.includes('preview packet');
                          const runtimePreviewVisible = lower.includes('agent orchestration runtime preview');
                          const verified = lower.includes('agent orchestration runtime preview readiness') && lower.includes('claimed task') && lower.includes('agent orchestration runtime contracts') && packetPreviewVisible && runtimePreviewVisible && lower.includes('blocked');
                          const failed = msg.includes('blocked') || msg.includes('Missing') || msg.includes('failed') || msg.includes('mismatch') || msg.includes('not available');
                          return verified || failed;
                        }
                        """,
                        timeout=UI_TIMEOUT_MS,
                    )
                except Exception as exc:  # noqa: BLE001
                    state = page.evaluate(
                        """
                        () => {
                          const root = document.querySelector('#capture-markdown-source-pack-preview-body');
                          const button = document.querySelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-btn');
                          const msg = root ? root.querySelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-msg') : null;
                          const result = root ? root.querySelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-result') : null;
                          return {
                            text: root ? root.textContent : '',
                            msg: msg ? msg.textContent : '',
                            result: result ? result.textContent : '',
                            buttonDataset: button ? {...button.dataset} : {},
                            buttonDisabled: button ? button.disabled : null
                          };
                        }
                        """
                    )
                    raise AssertionError(
                        "Agent Orchestration Runtime preview readiness user interface timed out: "
                        + json.dumps(state, sort_keys=True, default=str)[-4000:]
                    ) from exc
                dry_run_readiness_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                dry_run_readiness_lower = dry_run_readiness_text.lower()
                if not (
                    "agent orchestration runtime preview readiness" in dry_run_readiness_lower
                    and "claimed task" in dry_run_readiness_lower
                    and "agent orchestration runtime contracts" in dry_run_readiness_lower
                    and "preview packet" in dry_run_readiness_lower
                    and "agent orchestration runtime preview" in dry_run_readiness_lower
                    and "blocked" in dry_run_readiness_lower
                ):
                    raise AssertionError(
                        "Agent Orchestration Runtime preview readiness user interface did not reach the verified state: "
                        + dry_run_readiness_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-aor-dry-run-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-btn'); return button && !button.disabled && button.dataset.aorDryRunPacketDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-aor-dry-run-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    """
                    () => {
                      const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent || '';
                      const lower = text.toLowerCase();
                      return lower.includes('agent orchestration runtime preview ok')
                        || lower.includes('agent orchestration runtime preview blocked')
                        || lower.includes('agent orchestration runtime preview executor data')
                        || lower.includes('aor_dry_run_')
                        || lower.includes('aor-preview-')
                        || lower.includes('role_card_')
                        || lower.includes('workflow_');
                    }
                    """,
                    timeout=UI_TIMEOUT_MS,
                )
                dry_run_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                dry_run_text_lower = dry_run_text.lower()
                dry_run_required_token_groups = [
                    ("Agent Orchestration Runtime preview OK",),
                    ("OSRIL session",),
                    ("OSRIL event",),
                    ("Agent Orchestration Runtime audit",),
                    ("Preview artifact",),
                    ("Full dispatch",),
                    ("no",),
                ]
                missing_dry_run_groups = [
                    tuple(group)
                    for group in dry_run_required_token_groups
                    if not any(token.lower() in dry_run_text_lower for token in group)
                ]
                if missing_dry_run_groups:
                    raise AssertionError(
                        "Agent Orchestration Runtime preview user interface did not reach the verified state: "
                        + f"missing token groups {missing_dry_run_groups}; "
                        + dry_run_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-status-lifecycle-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-status-lifecycle-btn'); return button && !button.disabled && button.dataset.aorDryRunArtifactDigest && button.dataset.aorDryRunArtifactPath; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-status-lifecycle-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Task Status Lifecycle') && text.includes('Review requested') && text.includes('Status marker') && text.includes('Status artifact') && text.includes('Full dispatch') && text.includes('no'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                status_lifecycle_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                status_lifecycle_required_tokens = [
                    "Task Status Lifecycle",
                    "Review requested",
                    "Status marker",
                    "Status artifact",
                    "Task status",
                    "review",
                    "Full dispatch",
                    "no",
                ]
                status_lifecycle_text_lower = status_lifecycle_text.lower()
                if any(token.lower() not in status_lifecycle_text_lower for token in status_lifecycle_required_tokens):
                    raise AssertionError(
                        "Agent Bus status lifecycle UI did not reach the verified state: "
                        + status_lifecycle_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-full-dispatch-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-full-dispatch-readiness-btn'); return button && !button.disabled && button.dataset.statusLifecycleArtifactDigest && button.dataset.statusLifecycleArtifactPath; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-full-dispatch-readiness-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Full Dispatch Readiness') && text.includes('Ready for executor') && text.includes('Review event') && text.includes('Future packet') && text.includes('Executor preview') && text.includes('Run Full Dispatch'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                full_dispatch_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                full_dispatch_required_tokens = [
                    "Full Dispatch Readiness",
                    "Ready for executor",
                    "Review event",
                    "verified",
                    "Future packet",
                    "Executor preview",
                    "Run Full Dispatch",
                    "Full dispatch",
                    "guarded",
                    "Agent Orchestration Runtime full run",
                    "no",
                ]
                full_dispatch_text_lower = full_dispatch_text.lower()
                if any(token.lower() not in full_dispatch_text_lower for token in full_dispatch_required_tokens):
                    raise AssertionError(
                        "Agent Bus full-dispatch readiness UI did not reach the verified state: "
                        + full_dispatch_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-agent-bus-full-dispatch-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-agent-bus-full-dispatch-btn'); return button && !button.disabled && button.dataset.fullDispatchPacketDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-agent-bus-full-dispatch-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Full dispatch complete') && text.includes('Full Dispatch') && text.includes('Agent Orchestration Runtime result') && text.includes('Source-pack writeback') && text.includes('Provider') && text.includes('External'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                full_dispatch_execution_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                full_dispatch_execution_required_tokens = [
                    "Full dispatch complete",
                    "Full Dispatch",
                    "Agent Orchestration Runtime result",
                    "success",
                    "Source-pack writeback",
                    "written",
                    "Source Intelligence Core",
                    "no",
                    "Canonical",
                    "no",
                    "Graph",
                    "no",
                    "Provider",
                    "no",
                    "External",
                    "no",
                ]
                full_dispatch_execution_text_lower = full_dispatch_execution_text.lower()
                if any(
                    token.lower() not in full_dispatch_execution_text_lower
                    for token in full_dispatch_execution_required_tokens
                ):
                    raise AssertionError(
                        "Agent Bus full-dispatch executor UI did not reach the verified state: "
                        + full_dispatch_execution_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-readiness-btn'); return button && !button.disabled && button.dataset.fullDispatchArtifactPath && button.dataset.fullDispatchArtifactDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-readiness-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core readiness verified') && text.includes('Source Intelligence Core Ingestion Readiness') && text.includes('Source-pack writeback') && text.includes('Source Intelligence Core contracts') && text.includes('Future packet'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_readiness_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                sic_readiness_required_tokens = [
                    "Source Intelligence Core readiness verified",
                    "Source Intelligence Core Ingestion Readiness",
                    "Source-pack writeback",
                    "verified",
                    "Source Intelligence Core contracts",
                    "Future packet",
                    "Executor",
                    "separate pass",
                    "Source Intelligence Core ingested",
                    "no",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                ]
                sic_readiness_text_lower = sic_readiness_text.lower()
                if any(token.lower() not in sic_readiness_text_lower for token in sic_readiness_required_tokens):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core ingestion readiness UI did not reach the verified state: "
                        + sic_readiness_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-approval-design-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-approval-design-btn'); return button && !button.disabled && button.dataset.sicIngestionReadinessPacketDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-approval-design-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core approval design ready') && text.includes('Source Intelligence Core Approval Design') && text.includes('Approval packet') && text.includes('Approval request') && text.includes('Source packages'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_approval_design_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                sic_approval_design_required_tokens = [
                    "Source Intelligence Core approval design ready",
                    "Source Intelligence Core Approval Design",
                    "Approval packet",
                    "ready",
                    "Approval request",
                    "not written",
                    "Executor",
                    "separate pass",
                    "Workspace",
                    "vcmi-reviewed-captures",
                    "Source packages",
                    "not written",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                    "Provider",
                    "no",
                    "External",
                    "no",
                ]
                sic_approval_design_text_lower = sic_approval_design_text.lower()
                if any(
                    token.lower() not in sic_approval_design_text_lower
                    for token in sic_approval_design_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core ingestion approval design UI did not reach the verified state: "
                        + sic_approval_design_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-approval-request-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-approval-request-btn'); return button && !button.disabled && button.dataset.sicIngestionApprovalRequestDigest && button.dataset.operatorStatement; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-approval-request-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core approval request written') && text.includes('Source Intelligence Core Approval Request') && text.includes('Request written') && text.includes('Artifact written'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_approval_request_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                sic_approval_request_required_tokens = [
                    "Source Intelligence Core approval request written",
                    "Source Intelligence Core Approval Request",
                    "Request written",
                    "yes",
                    "Artifact written",
                    "Decision",
                    "pending",
                    "Approval consumed",
                    "no",
                    "Source Intelligence Core ingested",
                    "no",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                    "Provider",
                    "no",
                    "External",
                    "no",
                ]
                sic_approval_request_text_lower = sic_approval_request_text.lower()
                if any(
                    token.lower() not in sic_approval_request_text_lower
                    for token in sic_approval_request_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core ingestion approval request UI did not reach the verified state: "
                        + sic_approval_request_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-decision-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-decision-readiness-btn'); return button && !button.disabled && button.dataset.approvalArtifactPath && button.dataset.sicIngestionApprovalRequestDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-decision-readiness-btn").click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core decision readiness verified') && text.includes('Source Intelligence Core Decision Readiness') && text.includes('Request verified') && text.includes('Decision writer ready'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_decision_readiness_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                sic_decision_readiness_required_tokens = [
                    "Source Intelligence Core decision readiness verified",
                    "Source Intelligence Core Decision Readiness",
                    "Request verified",
                    "yes",
                    "Decision options",
                    "2",
                    "Decision writer ready",
                    "yes",
                    "Ready for ingestion executor",
                    "no",
                    "Source Intelligence Core ingested",
                    "no",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                ]
                sic_decision_readiness_text_lower = sic_decision_readiness_text.lower()
                if any(
                    token.lower() not in sic_decision_readiness_text_lower
                    for token in sic_decision_readiness_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core approval decision readiness UI did not reach the verified state: "
                        + sic_decision_readiness_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-approval-decision-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-approval-decision-btn'); return button && !button.disabled && button.dataset.sicIngestionApprovalDecisionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-approval-decision-btn").first.click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core approval decision written') && text.includes('Source Intelligence Core Approval Decision') && text.includes('Decision written') && text.includes('Ready for approval consumption'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_approval_decision_text = page.locator("#capture-markdown-source-pack-preview-body").inner_text(
                    timeout=TEXT_TIMEOUT_MS
                )
                sic_approval_decision_required_tokens = [
                    "Source Intelligence Core approval decision written",
                    "Source Intelligence Core Approval Decision",
                    "Decision written",
                    "yes",
                    "Approval consumed",
                    "no",
                    "Ready for approval consumption",
                    "yes",
                    "Ready for ingestion executor",
                    "no",
                    "Source Intelligence Core ingested",
                    "no",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                ]
                sic_approval_decision_text_lower = sic_approval_decision_text.lower()
                if any(
                    token.lower() not in sic_approval_decision_text_lower
                    for token in sic_approval_decision_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core approval decision UI did not reach the verified state: "
                        + sic_approval_decision_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-approval-consumption-preview-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-approval-consumption-preview-btn'); return button && !button.disabled && button.dataset.approvalDecisionArtifactPath && button.dataset.sicIngestionApprovalDecisionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-approval-consumption-preview-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core approval consumption preview ready') && text.includes('Source Intelligence Core Approval Consumption Preview') && text.includes('Consume Source Intelligence Core Decision'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_approval_consumption_preview_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                sic_approval_consumption_preview_required_tokens = [
                    "Source Intelligence Core approval consumption preview ready",
                    "Source Intelligence Core Approval Consumption Preview",
                    "Decision",
                    "Consumption digest",
                    "Marker",
                    "not written",
                    "Ready for ingestion executor",
                    "no",
                    "Source Intelligence Core ingested",
                    "no",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                    "Consume Source Intelligence Core Decision",
                ]
                sic_approval_consumption_preview_text_lower = (
                    sic_approval_consumption_preview_text.lower()
                )
                if any(
                    token.lower() not in sic_approval_consumption_preview_text_lower
                    for token in sic_approval_consumption_preview_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core approval consumption preview UI did not reach the verified state: "
                        + sic_approval_consumption_preview_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-approval-consumption-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-approval-consumption-btn'); return button && !button.disabled && button.dataset.sicIngestionApprovalConsumptionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-approval-consumption-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core approval decision consumed') && text.includes('Source Intelligence Core Approval Consumption') && text.includes('Decision consumed') && text.includes('Ready for ingestion executor'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_approval_consumption_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                sic_approval_consumption_required_tokens = [
                    "Source Intelligence Core approval decision consumed",
                    "Source Intelligence Core Approval Consumption",
                    "Decision consumed",
                    "yes",
                    "Marker written",
                    "yes",
                    "Consumption written",
                    "yes",
                    "Ready for ingestion executor",
                    "yes",
                    "Source Intelligence Core ingested",
                    "no",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                    "Provider",
                    "no",
                    "External",
                    "no",
                ]
                sic_approval_consumption_text_lower = sic_approval_consumption_text.lower()
                if any(
                    token.lower() not in sic_approval_consumption_text_lower
                    for token in sic_approval_consumption_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core approval consumption UI did not reach the verified state: "
                        + sic_approval_consumption_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-ingestion-preview-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-ingestion-preview-btn'); return button && !button.disabled && button.dataset.approvalConsumptionArtifactPath && button.dataset.sicIngestionApprovalConsumptionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-ingestion-preview-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core ingestion preview ready') && text.includes('Source Intelligence Core Ingestion Preview') && text.includes('Ingest into Source Intelligence Core'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_ingestion_preview_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                sic_ingestion_preview_required_tokens = [
                    "Source Intelligence Core ingestion preview ready",
                    "Source Intelligence Core Ingestion Preview",
                    "Ingestion digest",
                    "Workspace",
                    "Source package",
                    "Ingested",
                    "no",
                    "Workspace written",
                    "no",
                    "Source package written",
                    "no",
                    "Workspace membership",
                    "no",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                    "Ingest into Source Intelligence Core",
                ]
                sic_ingestion_preview_text_lower = sic_ingestion_preview_text.lower()
                if any(
                    token.lower() not in sic_ingestion_preview_text_lower
                    for token in sic_ingestion_preview_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core ingestion preview UI did not reach the verified state: "
                        + sic_ingestion_preview_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-ingestion-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-ingestion-btn'); return button && !button.disabled && button.dataset.sicIngestionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-ingestion-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Source Intelligence Core ingestion complete') && text.includes('Source Intelligence Core Ingestion') && text.includes('Source package written'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_ingestion_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                sic_ingestion_required_tokens = [
                    "Source Intelligence Core ingestion complete",
                    "Source Intelligence Core Ingestion",
                    "Ingested",
                    "yes",
                    "Workspace written",
                    "yes",
                    "Source package written",
                    "yes",
                    "Workspace membership",
                    "yes",
                    "Graph",
                    "no",
                    "Canonical",
                    "no",
                ]
                sic_ingestion_text_lower = sic_ingestion_text.lower()
                if any(
                    token.lower() not in sic_ingestion_text_lower
                    for token in sic_ingestion_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core ingestion UI did not reach the verified state: "
                        + sic_ingestion_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-graph-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-graph-readiness-btn'); return button && !button.disabled && button.dataset.sicIngestionArtifactPath && button.dataset.sicIngestionArtifactDigest && button.dataset.sicIngestionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-graph-readiness-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Graph indexing executor preview ready') && text.includes('Graph Readiness') && text.includes('Candidate digest') && text.includes('Write Graph Snapshot') && text.includes('Graph snapshot') && text.includes('no'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                sic_graph_readiness_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                sic_graph_readiness_required_tokens = [
                    "Graph indexing executor preview ready",
                    "Graph Readiness",
                    "Candidate digest",
                    "Nodes",
                    "Edges",
                    "Write Graph Snapshot",
                    "Graph snapshot",
                    "no",
                    "Canonical",
                    "no",
                ]
                sic_graph_readiness_text_lower = sic_graph_readiness_text.lower()
                if any(
                    token.lower() not in sic_graph_readiness_text_lower
                    for token in sic_graph_readiness_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack Source Intelligence Core graph-indexing readiness UI did not reach the verified state: "
                        + sic_graph_readiness_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-sic-graph-indexing-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-sic-graph-indexing-btn'); const statement = document.querySelector('.capture-markdown-source-pack-sic-graph-indexing-statement'); return button && !button.disabled && button.dataset.graphIndexPreviewPacketDigest && statement && statement.value.includes('I execute Source Intelligence Core graph indexing'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-sic-graph-indexing-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Graph snapshot written') && text.includes('Graph Indexing') && text.includes('Snapshot written') && text.includes('yes') && text.includes('Current pointer') && text.includes('Canonical') && text.includes('no'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-canonical-promotion-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-canonical-promotion-readiness-btn'); return button && !button.disabled && button.dataset.graphIndexingArtifactPath && button.dataset.graphIndexingArtifactDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-canonical-promotion-readiness-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Canonical promotion readiness ready') && text.includes('Canonical readiness') && text.includes('Candidate digest') && text.includes('Future targets') && text.includes('Canonical write') && text.includes('no'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                canonical_readiness_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                canonical_readiness_required_tokens = [
                    "Canonical promotion readiness ready",
                    "Canonical readiness",
                    "Candidate digest",
                    "Snapshot",
                    "Future targets",
                    "Canonical write",
                    "no",
                ]
                canonical_readiness_text_lower = canonical_readiness_text.lower()
                if any(
                    token.lower() not in canonical_readiness_text_lower
                    for token in canonical_readiness_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack canonical promotion readiness interface did not reach the verified state: "
                        + canonical_readiness_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-canonical-promotion-approval-design-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-canonical-promotion-approval-design-btn'); return button && !button.disabled && button.dataset.graphIndexingArtifactPath && button.dataset.graphIndexingArtifactDigest && button.dataset.canonicalPromotionCandidateDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-canonical-promotion-approval-design-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Canonical approval design ready') && text.includes('Canonical approval') && text.includes('Request digest') && text.includes('Future targets') && text.includes('Request written') && text.includes('Canonical write'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                canonical_approval_design_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                canonical_approval_design_required_tokens = [
                    "Canonical approval design ready",
                    "Canonical approval",
                    "Request digest",
                    "Future targets",
                    "Request written",
                    "Canonical write",
                    "no",
                ]
                canonical_approval_design_text_lower = canonical_approval_design_text.lower()
                if any(
                    token.lower() not in canonical_approval_design_text_lower
                    for token in canonical_approval_design_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack canonical promotion approval design interface did not reach the verified state: "
                        + canonical_approval_design_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-canonical-promotion-approval-request-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-canonical-promotion-approval-request-btn'); return button && !button.disabled && button.dataset.graphIndexingArtifactPath && button.dataset.graphIndexingArtifactDigest && button.dataset.canonicalPromotionCandidateDigest && button.dataset.canonicalPromotionApprovalRequestDigest && button.dataset.operatorStatement; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-canonical-promotion-approval-request-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Canonical request written') && text.includes('Request written') && text.includes('Decision written') && text.includes('Approval consumed') && text.includes('Canonical write'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                canonical_approval_request_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                canonical_approval_request_required_tokens = [
                    "Canonical request written",
                    "Request written",
                    "Decision written",
                    "Approval consumed",
                    "Canonical write",
                    "yes",
                    "no",
                ]
                canonical_approval_request_text_lower = canonical_approval_request_text.lower()
                if any(
                    token.lower() not in canonical_approval_request_text_lower
                    for token in canonical_approval_request_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack canonical promotion approval request interface did not reach the verified state: "
                        + canonical_approval_request_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-canonical-promotion-decision-readiness-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-canonical-promotion-decision-readiness-btn'); return button && !button.disabled && button.dataset.graphIndexingArtifactPath && button.dataset.graphIndexingArtifactDigest && button.dataset.canonicalPromotionCandidateDigest && button.dataset.canonicalPromotionApprovalRequestDigest && button.dataset.approvalArtifactPath; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-canonical-promotion-decision-readiness-btn").click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Canonical decision readiness verified') && text.includes('Request verified') && text.includes('Decision writer ready') && text.includes('Approval consumed') && text.includes('Executor ready') && text.includes('Canonical write'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                canonical_decision_readiness_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                canonical_decision_readiness_required_tokens = [
                    "Canonical decision readiness verified",
                    "Request verified",
                    "Decision writer ready",
                    "Approval consumed",
                    "Executor ready",
                    "Canonical write",
                    "yes",
                    "no",
                ]
                canonical_decision_readiness_text_lower = canonical_decision_readiness_text.lower()
                if any(
                    token.lower() not in canonical_decision_readiness_text_lower
                    for token in canonical_decision_readiness_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack canonical promotion approval decision readiness interface did not reach the verified state: "
                        + canonical_decision_readiness_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-canonical-promotion-approval-decision-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-canonical-promotion-approval-decision-btn'); return button && !button.disabled && button.dataset.canonicalPromotionApprovalDecisionDigest && button.dataset.decision; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(
                    ".capture-markdown-source-pack-canonical-promotion-approval-decision-btn"
                ).first.click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Canonical approval decision written') && text.includes('Canonical Approval Decision') && text.includes('Decision written') && text.includes('Ready for approval consumption') && text.includes('Executor ready') && text.includes('Canonical write') && text.includes('Knowledge note') && text.includes('Knowledge index'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                canonical_approval_decision_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                canonical_approval_decision_required_tokens = [
                    "Canonical approval decision written",
                    "Canonical Approval Decision",
                    "Decision written",
                    "Approval consumed",
                    "Ready for approval consumption",
                    "Executor ready",
                    "Canonical write",
                    "Knowledge note",
                    "Knowledge index",
                    "yes",
                    "no",
                ]
                canonical_approval_decision_text_lower = canonical_approval_decision_text.lower()
                if any(
                    token.lower() not in canonical_approval_decision_text_lower
                    for token in canonical_approval_decision_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack canonical promotion approval decision interface did not reach the verified state: "
                        + canonical_approval_decision_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-canonical-promotion-approval-consumption-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-canonical-promotion-approval-consumption-btn'); return button && !button.disabled && button.dataset.approvalDecisionArtifactPath && button.dataset.canonicalPromotionApprovalDecisionDigest && button.dataset.decision; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(
                    ".capture-markdown-source-pack-canonical-promotion-approval-consumption-btn"
                ).first.click(timeout=UI_TIMEOUT_MS)
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Canonical approval decision consumed') && text.includes('Canonical Approval Consumption') && text.includes('Marker written') && text.includes('Consumption written') && text.includes('Executor ready') && text.includes('Canonical write') && text.includes('Knowledge note') && text.includes('Knowledge index'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                canonical_approval_consumption_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                canonical_approval_consumption_required_tokens = [
                    "Canonical approval decision consumed",
                    "Canonical Approval Consumption",
                    "Marker written",
                    "Consumption written",
                    "Approval consumed",
                    "Executor ready",
                    "Canonical write",
                    "Canonical written",
                    "Knowledge note",
                    "Knowledge index",
                    "Provider",
                    "External",
                    "yes",
                    "no",
                ]
                canonical_approval_consumption_text_lower = canonical_approval_consumption_text.lower()
                if any(
                    token.lower() not in canonical_approval_consumption_text_lower
                    for token in canonical_approval_consumption_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack canonical promotion approval consumption interface did not reach the verified state: "
                        + canonical_approval_consumption_text[-2400:]
                    )
                page.wait_for_selector(
                    ".capture-markdown-source-pack-canonical-promotion-btn",
                    timeout=UI_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => { const button = document.querySelector('.capture-markdown-source-pack-canonical-promotion-btn'); return button && !button.disabled && button.dataset.graphIndexingArtifactPath && button.dataset.graphIndexingArtifactDigest && button.dataset.canonicalPromotionCandidateDigest && button.dataset.canonicalPromotionApprovalRequestDigest && button.dataset.canonicalPromotionApprovalDecisionDigest && button.dataset.approvalConsumptionArtifactPath && button.dataset.canonicalPromotionApprovalConsumptionDigest; }",
                    timeout=UI_TIMEOUT_MS,
                )
                page.locator(".capture-markdown-source-pack-canonical-promotion-btn").first.click(
                    timeout=UI_TIMEOUT_MS
                )
                page.wait_for_function(
                    "() => { const text = (document.querySelector('#capture-markdown-source-pack-preview-body') || {}).textContent; return text.includes('Canonical knowledge promoted') && text.includes('Canonical Promotion') && text.includes('Knowledge note') && text.includes('Knowledge index') && text.includes('Artifact written') && text.includes('Graph mutation') && text.includes('Provider') && text.includes('External'); }",
                    timeout=UI_TIMEOUT_MS,
                )
                canonical_promotion_text = page.locator(
                    "#capture-markdown-source-pack-preview-body"
                ).inner_text(timeout=TEXT_TIMEOUT_MS)
                canonical_promotion_required_tokens = [
                    "Promote Canonical Knowledge",
                    "Canonical knowledge promoted",
                    "Canonical Promotion",
                    "Marker written",
                    "Knowledge note",
                    "Knowledge index",
                    "Artifact written",
                    "Graph mutation",
                    "Provider",
                    "External",
                    "yes",
                    "no",
                ]
                canonical_promotion_text_lower = canonical_promotion_text.lower()
                if any(
                    token.lower() not in canonical_promotion_text_lower
                    for token in canonical_promotion_required_tokens
                ):
                    raise AssertionError(
                        "Source-pack canonical promotion executor interface did not reach the verified state: "
                        + canonical_promotion_text[-2400:]
                    )
                after_text = page.locator("#panel-capture-markdown").inner_text(timeout=TEXT_TIMEOUT_MS)
                input_values = page.evaluate(
                    """
                    () => Array.from(document.querySelectorAll('#panel-capture-markdown input, #panel-capture-markdown textarea'))
                      .map((el) => el.value || '')
                      .join('\\n')
                    """
                )
                dry_run_operator_statement = (
                    (agent_bus_claimed_task_dry_run_results.get(viewport_name) or {}).get(
                        "required_operator_statement"
                    )
                    or ""
                )
                normalized = (
                    f"{before_text}\n{aor_readiness_text}\n{aor_approval_design_text}\n"
                    f"{dry_run_readiness_text}\n{dry_run_text}\n"
                    f"{full_dispatch_text}\n{full_dispatch_execution_text}\n"
                    f"{dry_run_operator_statement}\n"
                    f"{canonical_readiness_text}\n"
                    f"{canonical_approval_design_text}\n"
                    f"{canonical_approval_request_text}\n"
                    f"{canonical_decision_readiness_text}\n"
                    f"{canonical_approval_decision_text}\n"
                    f"{canonical_approval_consumption_text}\n"
                    f"{canonical_promotion_text}\n{after_text}\n{input_values}"
                ).lower()
                required_token_aliases = {
                    "Preview packet": ("Preview packet",),
                    "Agent Orchestration Runtime preview OK": (
                        "Agent Orchestration Runtime preview OK",
                    ),
                    "Preview marker": ("Preview marker",),
                    "Preview artifact": ("Preview artifact",),
                    "Run Agent Orchestration Runtime Preview": (
                        "Run Agent Orchestration Runtime Preview",
                        "Run AOR Dry-Run",
                    ),
                    "I execute Capture to Markdown Agent Orchestration Runtime full dispatch": (
                        "I execute Capture to Markdown Agent Orchestration Runtime full dispatch",
                        "I execute VCMI AOR full-dispatch",
                    ),
                    "I approve dispatching this reviewed Capture to Markdown source pack through Agent Orchestration Runtime.": (
                        "I approve dispatching this reviewed Capture to Markdown source pack through Agent Orchestration Runtime.",
                        "I approve dispatching this reviewed VCMI source pack through AOR.",
                    ),
                    "I approve writing this reviewed Capture to Markdown capture as an acquisition source pack.": (
                        "I approve writing this reviewed Capture to Markdown capture as an acquisition source pack.",
                        "I approve writing this reviewed VCMI capture as an acquisition source pack.",
                    ),
                    "I approve Capture to Markdown Agent Orchestration Runtime dispatch approval request": (
                        "I approve Capture to Markdown Agent Orchestration Runtime dispatch approval request",
                        "I approve VCMI AOR dispatch approval request",
                    ),
                    "I consume Capture to Markdown Agent Orchestration Runtime dispatch approval decision": (
                        "I consume Capture to Markdown Agent Orchestration Runtime dispatch approval decision",
                        "I consume VCMI AOR dispatch approval decision",
                    ),
                    "I write Capture to Markdown Agent Orchestration Runtime dispatch Agent Bus task": (
                        "I write Capture to Markdown Agent Orchestration Runtime dispatch Agent Bus task",
                        "I write VCMI AOR dispatch Agent Bus task",
                    ),
                    "I run Capture to Markdown Agent Orchestration Runtime preview": (
                        "I run Capture to Markdown Agent Orchestration Runtime preview",
                        "I run VCMI AOR dry-run",
                    ),
                    "I update Capture to Markdown Agent Bus task": (
                        "I update Capture to Markdown Agent Bus task",
                        "I update VCMI Agent Bus task",
                    ),
                }
                missing = [
                    token
                    for token in REQUIRED_TOKENS
                    if not any(
                        alias.lower() in normalized
                        for alias in required_token_aliases.get(token, (token,))
                    )
                ]
                sidecar = json.loads(Path(fixture["saved"]["sidecar_path"]).read_text(encoding="utf-8"))
                disposition = (
                    sidecar.get("extra_metadata", {})
                    .get("visual_capture", {})
                    .get("attachment_disposition_policy", {})
                )
                write_result = write_results.get(viewport_name) or {}
                readiness_result = readiness_results.get(viewport_name) or {}
                approval_design_result = approval_design_results.get(viewport_name) or {}
                approval_request_result = approval_request_results.get(viewport_name) or {}
                approval_consumption_result = approval_consumption_readiness_results.get(viewport_name) or {}
                approval_decision_result = approval_decision_results.get(viewport_name) or {}
                approval_consumed_result = approval_consumption_results.get(viewport_name) or {}
                agent_bus_task_result = agent_bus_task_results.get(viewport_name) or {}
                agent_bus_claim_readiness_result = agent_bus_task_claim_readiness_results.get(viewport_name) or {}
                agent_bus_claim_result = agent_bus_task_claim_results.get(viewport_name) or {}
                agent_bus_dry_run_readiness_result = (
                    agent_bus_claimed_task_dry_run_readiness_results.get(viewport_name) or {}
                )
                agent_bus_dry_run_result = agent_bus_claimed_task_dry_run_results.get(viewport_name) or {}
                agent_bus_status_lifecycle_result = (
                    agent_bus_claimed_task_status_lifecycle_results.get(viewport_name) or {}
                )
                agent_bus_full_dispatch_readiness_result = (
                    agent_bus_full_dispatch_readiness_results.get(viewport_name) or {}
                )
                agent_bus_full_dispatch_preview_result = (
                    agent_bus_full_dispatch_preview_results.get(viewport_name) or {}
                )
                agent_bus_full_dispatch_result = agent_bus_full_dispatch_results.get(viewport_name) or {}
                source_pack_sic_readiness_result = source_pack_sic_readiness_results.get(viewport_name) or {}
                source_pack_sic_approval_design_result = (
                    source_pack_sic_approval_design_results.get(viewport_name) or {}
                )
                source_pack_sic_approval_request_result = (
                    source_pack_sic_approval_request_results.get(viewport_name) or {}
                )
                source_pack_sic_decision_readiness_result = (
                    source_pack_sic_decision_readiness_results.get(viewport_name) or {}
                )
                source_pack_sic_approval_decision_result = (
                    source_pack_sic_approval_decision_results.get(viewport_name) or {}
                )
                source_pack_sic_approval_consumption_result = (
                    source_pack_sic_approval_consumption_results.get(viewport_name) or {}
                )
                source_pack_sic_ingestion_preview_result = (
                    source_pack_sic_ingestion_preview_results.get(viewport_name) or {}
                )
                source_pack_sic_ingestion_result = (
                    source_pack_sic_ingestion_results.get(viewport_name) or {}
                )
                source_pack_sic_graph_readiness_result = (
                    source_pack_sic_graph_readiness_results.get(viewport_name) or {}
                )
                source_pack_sic_graph_indexing_preview_result = (
                    source_pack_sic_graph_indexing_preview_results.get(viewport_name) or {}
                )
                source_pack_sic_graph_indexing_result = (
                    source_pack_sic_graph_indexing_results.get(viewport_name) or {}
                )
                source_pack_canonical_promotion_readiness_result = (
                    source_pack_canonical_promotion_readiness_results.get(viewport_name) or {}
                )
                source_pack_canonical_promotion_approval_design_result = (
                    source_pack_canonical_promotion_approval_design_results.get(viewport_name) or {}
                )
                source_pack_canonical_promotion_approval_request_result = (
                    source_pack_canonical_promotion_approval_request_results.get(viewport_name) or {}
                )
                source_pack_canonical_promotion_decision_readiness_result = (
                    source_pack_canonical_promotion_decision_readiness_results.get(viewport_name) or {}
                )
                source_pack_canonical_promotion_approval_decision_result = (
                    source_pack_canonical_promotion_approval_decision_results.get(viewport_name) or {}
                )
                source_pack_canonical_promotion_approval_consumption_result = (
                    source_pack_canonical_promotion_approval_consumption_results.get(viewport_name) or {}
                )
                source_pack_canonical_promotion_result = (
                    source_pack_canonical_promotion_results.get(viewport_name) or {}
                )
                written_paths = list(write_result.get("written_paths") or [])
                written_paths_exist = bool(written_paths) and all((fixture_vault / path).is_file() for path in written_paths)
                approval_request_written_paths = list(approval_request_result.get("written_paths") or [])
                approval_request_written_paths_exist = (
                    bool(approval_request_written_paths)
                    and all((fixture_vault / path).is_file() for path in approval_request_written_paths)
                )
                approval_decision_written_paths = list(approval_decision_result.get("written_paths") or [])
                approval_decision_written_paths_exist = (
                    bool(approval_decision_written_paths)
                    and all((fixture_vault / path).is_file() for path in approval_decision_written_paths)
                )
                approval_consumption_written_paths = list(approval_consumed_result.get("written_paths") or [])
                approval_consumption_written_paths_exist = (
                    bool(approval_consumption_written_paths)
                    and all((fixture_vault / path).is_file() for path in approval_consumption_written_paths)
                )
                source_pack_sic_approval_decision_written_paths = list(
                    source_pack_sic_approval_decision_result.get("written_paths") or []
                )
                source_pack_sic_approval_decision_written_paths_exist = (
                    bool(source_pack_sic_approval_decision_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_sic_approval_decision_written_paths
                    )
                )
                source_pack_sic_approval_consumption_written_paths = list(
                    source_pack_sic_approval_consumption_result.get("written_paths") or []
                )
                source_pack_sic_approval_consumption_written_paths_exist = (
                    bool(source_pack_sic_approval_consumption_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_sic_approval_consumption_written_paths
                    )
                )
                source_pack_sic_ingestion_written_paths = list(
                    source_pack_sic_ingestion_result.get("written_paths") or []
                )
                source_pack_sic_ingestion_written_paths_exist = (
                    bool(source_pack_sic_ingestion_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_sic_ingestion_written_paths
                    )
                )
                source_pack_sic_graph_indexing_written_paths = list(
                    source_pack_sic_graph_indexing_result.get("written_paths") or []
                )
                source_pack_sic_graph_indexing_written_paths_exist = (
                    bool(source_pack_sic_graph_indexing_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_sic_graph_indexing_written_paths
                    )
                )
                source_pack_canonical_promotion_approval_request_written_paths = list(
                    source_pack_canonical_promotion_approval_request_result.get("written_paths") or []
                )
                source_pack_canonical_promotion_approval_request_written_paths_exist = (
                    bool(source_pack_canonical_promotion_approval_request_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_canonical_promotion_approval_request_written_paths
                    )
                )
                source_pack_canonical_promotion_approval_decision_written_paths = list(
                    source_pack_canonical_promotion_approval_decision_result.get("written_paths") or []
                )
                source_pack_canonical_promotion_approval_decision_written_paths_exist = (
                    bool(source_pack_canonical_promotion_approval_decision_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_canonical_promotion_approval_decision_written_paths
                    )
                )
                source_pack_canonical_promotion_approval_consumption_written_paths = list(
                    source_pack_canonical_promotion_approval_consumption_result.get("written_paths") or []
                )
                source_pack_canonical_promotion_approval_consumption_written_paths_exist = (
                    bool(source_pack_canonical_promotion_approval_consumption_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_canonical_promotion_approval_consumption_written_paths
                    )
                )
                source_pack_canonical_promotion_written_paths = list(
                    source_pack_canonical_promotion_result.get("written_paths") or []
                )
                source_pack_canonical_promotion_written_paths_exist = (
                    bool(source_pack_canonical_promotion_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_canonical_promotion_written_paths
                    )
                )
                canonical_promotion_decision_readiness_future_marker = (
                    source_pack_canonical_promotion_decision_readiness_result.get(
                        "future_approval_consumption_marker_path"
                    )
                    or ""
                )
                agent_bus_task_written_paths = list(agent_bus_task_result.get("written_paths") or [])
                agent_bus_task_written_paths_exist = (
                    bool(agent_bus_task_written_paths)
                    and all((fixture_vault / path).is_file() for path in agent_bus_task_written_paths)
                )
                agent_bus_task_claim_written_paths = list(agent_bus_claim_result.get("written_paths") or [])
                agent_bus_task_claim_written_paths_exist = (
                    bool(agent_bus_task_claim_written_paths)
                    and all((fixture_vault / path).is_file() for path in agent_bus_task_claim_written_paths)
                )
                agent_bus_dry_run_written_paths = list(agent_bus_dry_run_result.get("written_paths") or [])
                agent_bus_dry_run_written_paths_exist = (
                    bool(agent_bus_dry_run_written_paths)
                    and all((fixture_vault / path).is_file() for path in agent_bus_dry_run_written_paths)
                )
                agent_bus_status_lifecycle_written_paths = list(
                    agent_bus_status_lifecycle_result.get("written_paths") or []
                )
                agent_bus_status_lifecycle_written_paths_exist = (
                    bool(agent_bus_status_lifecycle_written_paths)
                    and all((fixture_vault / path).is_file() for path in agent_bus_status_lifecycle_written_paths)
                )
                agent_bus_full_dispatch_written_paths = list(
                    agent_bus_full_dispatch_result.get("written_paths") or []
                )
                agent_bus_full_dispatch_written_paths_exist = (
                    bool(agent_bus_full_dispatch_written_paths)
                    and all((fixture_vault / path).is_file() for path in agent_bus_full_dispatch_written_paths)
                )
                source_pack_sic_approval_request_written_paths = list(
                    source_pack_sic_approval_request_result.get("written_paths") or []
                )
                source_pack_sic_approval_request_written_paths_exist = (
                    bool(source_pack_sic_approval_request_written_paths)
                    and all(
                        (fixture_vault / path).is_file()
                        for path in source_pack_sic_approval_request_written_paths
                    )
                )
                agent_bus_db_path = fixture_vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
                screenshot_path = output_dir / f"{viewport_name}-capture-markdown-pass44.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                screenshots.append(
                    {
                        "viewport": viewport_name,
                        "path": _relative_to_vault(vault, screenshot_path),
                        "exists": screenshot_path.is_file(),
                        "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
                        "not_blank": screenshot_path.is_file() and screenshot_path.stat().st_size > 10_000,
                        "policy_visible": "attachment disposition" in normalized,
                        "delete_block_visible": "delete" in normalized and "blocked" in normalized,
                        "review_state_visible": "reviewed" in normalized,
                        "source_pack_approval_preview_visible": "source-pack approval preview" in normalized,
                        "source_pack_request_digest_visible": "digest" in normalized and "not-ready" not in normalized,
                        "source_pack_write_blocked_visible": "source-pack write" in normalized and "blocked" in normalized,
                        "source_pack_write_completed_visible": "source-pack write" in normalized and "written" in normalized,
                        "source_pack_write_result_ok": bool(write_result.get("ok")),
                        "source_pack_written_path_count": len(written_paths),
                        "source_pack_written_paths_exist": written_paths_exist,
                        "source_pack_aor_readiness_visible": "agent orchestration runtime dispatch readiness" in normalized,
                        "source_pack_aor_readiness_result_ok": bool(readiness_result.get("ok")),
                        "source_pack_aor_dispatch_blocked_visible": "aor dispatch" in normalized and "blocked" in normalized,
                        "source_pack_agent_bus_blocked_visible": "agent bus" in normalized and "blocked" in normalized,
                        "source_pack_aor_ready_packet_digest_visible": "packet digest" in normalized,
                        "source_pack_aor_dispatch_allowed_now": readiness_result.get("aor_dispatch_allowed_now"),
                        "source_pack_agent_bus_task_written": readiness_result.get("agent_bus_task_written"),
                        "source_pack_aor_approval_design_visible": "agent orchestration runtime approval design" in normalized,
                        "source_pack_aor_approval_design_result_ok": bool(approval_design_result.get("ok")),
                        "source_pack_aor_approval_digest_visible": "approval digest" in normalized,
                        "source_pack_aor_future_approval_visible": "future approval" in normalized,
                        "source_pack_aor_approval_artifact_not_written_visible": "approval artifact" in normalized and "not written" in normalized,
                        "source_pack_aor_approval_design_request_written": approval_design_result.get("approval_request_written"),
                        "source_pack_aor_approval_design_artifact_written": approval_design_result.get("approval_artifact_written"),
                        "source_pack_aor_approval_design_consumed": approval_design_result.get("approval_consumed"),
                        "source_pack_aor_approval_request_visible": "approval request" in normalized,
                        "source_pack_aor_approval_request_result_ok": bool(approval_request_result.get("ok")),
                        "source_pack_aor_approval_request_written": approval_request_result.get("approval_request_written"),
                        "source_pack_aor_approval_request_artifact_written": approval_request_result.get("approval_artifact_written"),
                        "source_pack_aor_approval_request_written_paths_exist": approval_request_written_paths_exist,
                        "source_pack_aor_approval_request_approval_decision_written": approval_request_result.get("approval_decision_written"),
                        "source_pack_aor_approval_request_consumed": approval_request_result.get("approval_consumed"),
                        "source_pack_aor_approval_request_agent_bus_task_written": approval_request_result.get("agent_bus_task_written"),
                        "source_pack_aor_approval_request_aor_dispatch_allowed_now": approval_request_result.get("aor_dispatch_allowed_now"),
                        "source_pack_aor_approval_consumption_readiness_visible": "approval decision readiness" in normalized,
                        "source_pack_aor_approval_consumption_readiness_result_ok": bool(approval_consumption_result.get("ok")),
                        "source_pack_aor_approval_consumption_request_verified": approval_consumption_result.get("approval_request_artifact_verified"),
                        "source_pack_aor_approval_consumption_decision_writer_ready": approval_consumption_result.get("ready_for_aor_dispatch_approval_decision_writer"),
                        "source_pack_aor_approval_consumption_decision_written": approval_consumption_result.get("approval_decision_written"),
                        "source_pack_aor_approval_consumption_consumed": approval_consumption_result.get("approval_consumed"),
                        "source_pack_aor_approval_consumption_marker_written": approval_consumption_result.get("approval_exact_once_marker_written"),
                        "source_pack_aor_approval_consumption_agent_bus_task_written": approval_consumption_result.get("agent_bus_task_written"),
                        "source_pack_aor_approval_consumption_aor_dispatch_allowed_now": approval_consumption_result.get("aor_dispatch_allowed_now"),
                        "source_pack_aor_approval_consumption_future_marker_exists": approval_consumption_result.get("future_approval_consumption_marker_exists"),
                        "source_pack_aor_approval_decision_visible": "approval decision" in normalized,
                        "source_pack_aor_approval_decision_result_ok": bool(approval_decision_result.get("ok")),
                        "source_pack_aor_approval_decision_written": approval_decision_result.get("approval_decision_written"),
                        "source_pack_aor_approval_decision_artifact_written": approval_decision_result.get("approval_decision_artifact_written"),
                        "source_pack_aor_approval_decision_written_paths_exist": approval_decision_written_paths_exist,
                        "source_pack_aor_approval_decision_consumed": approval_decision_result.get("approval_consumed"),
                        "source_pack_aor_approval_decision_marker_written": approval_decision_result.get("approval_exact_once_marker_written"),
                        "source_pack_aor_approval_decision_agent_bus_task_written": approval_decision_result.get("agent_bus_task_written"),
                        "source_pack_aor_approval_decision_aor_dispatch_allowed_now": approval_decision_result.get("aor_dispatch_allowed_now"),
                        "source_pack_aor_approval_consumption_preview_visible": "approval consumption preview" in normalized,
                        "source_pack_aor_approval_consumption_visible": "approval consumption" in normalized,
                        "source_pack_aor_approval_consumption_result_ok": bool(approval_consumed_result.get("ok")),
                        "source_pack_aor_approval_consumption_written": approval_consumed_result.get("approval_consumed"),
                        "source_pack_aor_approval_consumption_decision_consumed": approval_consumed_result.get("approval_decision_consumed"),
                        "source_pack_aor_approval_consumption_marker_reserved": approval_consumed_result.get("approval_exact_once_marker_written"),
                        "source_pack_aor_approval_consumption_artifact_written": approval_consumed_result.get("approval_consumption_artifact_written"),
                        "source_pack_aor_approval_consumption_ready_for_agent_bus_task_writer": approval_consumed_result.get("ready_for_agent_bus_task_writer"),
                        "source_pack_aor_approval_consumption_written_paths_exist": approval_consumption_written_paths_exist,
                        "source_pack_aor_approval_consumption_agent_bus_task_written_after_consumption": approval_consumed_result.get("agent_bus_task_written"),
                        "source_pack_aor_approval_consumption_aor_dispatch_allowed_after_consumption": approval_consumed_result.get("aor_dispatch_allowed_now"),
                        "source_pack_aor_agent_bus_task_preview_visible": "agent bus task preview" in normalized,
                        "source_pack_aor_agent_bus_task_visible": "agent bus task" in normalized,
                        "source_pack_aor_agent_bus_task_result_ok": bool(agent_bus_task_result.get("ok")),
                        "source_pack_aor_agent_bus_task_marker_written": agent_bus_task_result.get("agent_bus_exact_once_marker_written"),
                        "source_pack_aor_agent_bus_task_written": agent_bus_task_result.get("agent_bus_task_written"),
                        "source_pack_aor_agent_bus_task_artifact_written": agent_bus_task_result.get("agent_bus_task_artifact_written"),
                        "source_pack_aor_agent_bus_task_written_paths_exist": agent_bus_task_written_paths_exist,
                        "source_pack_aor_agent_bus_task_db_exists": agent_bus_db_path.is_file(),
                        "source_pack_aor_agent_bus_task_claimed": agent_bus_task_result.get("agent_bus_task_claimed"),
                        "source_pack_aor_agent_bus_runtime_process_started": agent_bus_task_result.get("runtime_process_started"),
                        "source_pack_aor_agent_bus_aor_dispatch_allowed_after_task_write": agent_bus_task_result.get("aor_dispatch_allowed_now"),
                        "source_pack_aor_agent_bus_aor_dispatch_performed": agent_bus_task_result.get("aor_dispatch_performed"),
                        "source_pack_aor_agent_bus_task_claim_readiness_visible": "task claim readiness" in normalized,
                        "source_pack_aor_agent_bus_task_claim_readiness_result_ok": bool(agent_bus_claim_readiness_result.get("ok")),
                        "source_pack_aor_agent_bus_task_artifact_verified": agent_bus_claim_readiness_result.get("agent_bus_task_artifact_verified"),
                        "source_pack_aor_agent_bus_task_claimable": agent_bus_claim_readiness_result.get("agent_bus_task_claimable"),
                        "source_pack_aor_agent_bus_task_claim_preflight_ready": agent_bus_claim_readiness_result.get("agent_bus_task_claim_preflight_ready"),
                        "source_pack_aor_agent_bus_task_claim_allowed_now": agent_bus_claim_readiness_result.get("agent_bus_task_claim_allowed_now"),
                        "source_pack_aor_agent_bus_route_configured": agent_bus_claim_readiness_result.get("agent_bus_route_configured_for_runtime"),
                        "source_pack_aor_agent_bus_runtime_liveness_ready": agent_bus_claim_readiness_result.get("runtime_liveness_ready"),
                        "source_pack_aor_agent_bus_task_claim_readiness_aor_dispatch_allowed": agent_bus_claim_readiness_result.get("aor_dispatch_allowed_now"),
                        "source_pack_aor_agent_bus_task_claim_visible": "task claim" in normalized,
                        "source_pack_aor_agent_bus_task_claim_result_ok": bool(agent_bus_claim_result.get("ok")),
                        "source_pack_aor_agent_bus_task_claim_marker_written": agent_bus_claim_result.get("agent_bus_task_claim_marker_written"),
                        "source_pack_aor_agent_bus_task_claimed_after_claim": agent_bus_claim_result.get("agent_bus_task_claimed"),
                        "source_pack_aor_agent_bus_task_claim_artifact_written": agent_bus_claim_result.get("agent_bus_task_claim_artifact_written"),
                        "source_pack_aor_agent_bus_task_claim_written_paths_exist": agent_bus_task_claim_written_paths_exist,
                        "source_pack_aor_agent_bus_task_executed_after_claim": agent_bus_claim_result.get("agent_bus_task_executed"),
                        "source_pack_aor_agent_bus_runtime_process_started_after_claim": agent_bus_claim_result.get("runtime_process_started"),
                        "source_pack_aor_agent_bus_aor_dispatch_allowed_after_claim": agent_bus_claim_result.get("aor_dispatch_allowed_now"),
                        "source_pack_aor_agent_bus_claimed_task_dry_run_readiness_visible": "agent orchestration runtime preview readiness" in normalized,
                        "source_pack_aor_agent_bus_claimed_task_dry_run_readiness_result_ok": bool(
                            agent_bus_dry_run_readiness_result.get("ok")
                        ),
                        "source_pack_aor_agent_bus_claimed_task_ready": agent_bus_dry_run_readiness_result.get("agent_bus_task_claimed"),
                        "source_pack_aor_agent_bus_claim_artifact_verified_after_claim": agent_bus_dry_run_readiness_result.get("agent_bus_task_claim_artifact_verified"),
                        "source_pack_aor_agent_bus_aor_contracts_verified": agent_bus_dry_run_readiness_result.get("aor_contracts_verified"),
                        "source_pack_aor_agent_bus_dry_run_packet_ready": agent_bus_dry_run_readiness_result.get("future_aor_dry_run_packet_ready"),
                        "source_pack_aor_agent_bus_aor_dry_run_allowed_now": agent_bus_dry_run_readiness_result.get("aor_dry_run_allowed_now"),
                        "source_pack_aor_agent_bus_aor_dry_run_performed": agent_bus_dry_run_readiness_result.get("aor_dry_run_performed"),
                        "source_pack_aor_agent_bus_claimed_task_dry_run_visible": (
                            "agent orchestration runtime preview ok" in normalized
                        ),
                        "source_pack_aor_agent_bus_claimed_task_dry_run_result_ok": bool(agent_bus_dry_run_result.get("ok")),
                        "source_pack_aor_agent_bus_aor_dry_run_marker_written": agent_bus_dry_run_result.get("aor_dry_run_marker_written"),
                        "source_pack_aor_agent_bus_aor_dry_run_artifact_written": agent_bus_dry_run_result.get("aor_dry_run_artifact_written"),
                        "source_pack_aor_agent_bus_aor_dry_run_written_paths_exist": agent_bus_dry_run_written_paths_exist,
                        "source_pack_aor_agent_bus_aor_dry_run_result_status": agent_bus_dry_run_result.get("aor_result_status"),
                        "source_pack_aor_agent_bus_aor_dry_run_result_stage": agent_bus_dry_run_result.get("aor_result_stage_reached"),
                        "source_pack_aor_agent_bus_aor_dry_run_osril_session_created": agent_bus_dry_run_result.get("osril_session_created"),
                        "source_pack_aor_agent_bus_aor_dry_run_osril_event_written": agent_bus_dry_run_result.get("osril_event_written"),
                        "source_pack_aor_agent_bus_aor_dry_run_aor_audit_written": agent_bus_dry_run_result.get("aor_audit_written"),
                        "source_pack_aor_agent_bus_aor_dry_run_source_pack_writeback_created": agent_bus_dry_run_result.get("source_pack_writeback_created"),
                        "source_pack_aor_agent_bus_task_executed_after_dry_run": agent_bus_dry_run_result.get("agent_bus_task_executed"),
                        "source_pack_aor_agent_bus_task_status_updated_after_dry_run": agent_bus_dry_run_result.get("agent_bus_task_status_updated"),
                        "source_pack_aor_agent_bus_runtime_process_started_after_dry_run": agent_bus_dry_run_result.get("runtime_process_started"),
                        "source_pack_aor_agent_bus_aor_dispatch_performed_after_dry_run": agent_bus_dry_run_result.get("aor_dispatch_performed"),
                        "source_pack_aor_agent_bus_claimed_task_status_lifecycle_visible": "task status lifecycle" in normalized,
                        "source_pack_aor_agent_bus_claimed_task_status_lifecycle_result_ok": bool(
                            agent_bus_status_lifecycle_result.get("ok")
                        ),
                        "source_pack_aor_agent_bus_status_lifecycle_marker_written": agent_bus_status_lifecycle_result.get("status_lifecycle_marker_written"),
                        "source_pack_aor_agent_bus_task_status_updated_after_status_lifecycle": agent_bus_status_lifecycle_result.get("agent_bus_task_status_updated"),
                        "source_pack_aor_agent_bus_task_status_after_status_lifecycle": agent_bus_status_lifecycle_result.get("agent_bus_task_status_after"),
                        "source_pack_aor_agent_bus_task_review_requested_after_status_lifecycle": agent_bus_status_lifecycle_result.get("agent_bus_task_review_requested"),
                        "source_pack_aor_agent_bus_status_lifecycle_artifact_written": agent_bus_status_lifecycle_result.get("status_lifecycle_artifact_written"),
                        "source_pack_aor_agent_bus_status_lifecycle_written_paths_exist": agent_bus_status_lifecycle_written_paths_exist,
                        "source_pack_aor_agent_bus_task_executed_after_status_lifecycle": agent_bus_status_lifecycle_result.get("agent_bus_task_executed"),
                        "source_pack_aor_agent_bus_runtime_process_started_after_status_lifecycle": agent_bus_status_lifecycle_result.get("runtime_process_started"),
                        "source_pack_aor_agent_bus_aor_dispatch_performed_after_status_lifecycle": agent_bus_status_lifecycle_result.get("aor_dispatch_performed"),
                        "source_pack_aor_agent_bus_full_dispatch_readiness_visible": "full dispatch readiness" in normalized,
                        "source_pack_aor_agent_bus_full_dispatch_readiness_result_ok": bool(
                            agent_bus_full_dispatch_readiness_result.get("ok")
                        ),
                        "source_pack_aor_agent_bus_full_dispatch_readiness_ready": agent_bus_full_dispatch_readiness_result.get("aor_full_dispatch_readiness_ready"),
                        "source_pack_aor_agent_bus_full_dispatch_ready_for_executor": agent_bus_full_dispatch_readiness_result.get("ready_for_full_dispatch_executor"),
                        "source_pack_aor_agent_bus_full_dispatch_review_event_verified": agent_bus_full_dispatch_readiness_result.get("review_requested_event_verified"),
                        "source_pack_aor_agent_bus_full_dispatch_future_packet_ready": agent_bus_full_dispatch_readiness_result.get("future_full_dispatch_packet_ready"),
                        "source_pack_aor_agent_bus_full_dispatch_future_packet_digest_visible": "future packet" in normalized,
                        "source_pack_aor_agent_bus_full_dispatch_allowed_now": agent_bus_full_dispatch_readiness_result.get("aor_full_dispatch_allowed_now"),
                        "source_pack_aor_agent_bus_full_dispatch_performed": agent_bus_full_dispatch_readiness_result.get("aor_full_dispatch_performed"),
                        "source_pack_aor_agent_bus_full_dispatch_executor_preview_visible": "executor preview" in normalized,
                        "source_pack_aor_agent_bus_full_dispatch_executor_preview_result_ok": bool(
                            agent_bus_full_dispatch_preview_result.get("ok")
                        ),
                        "source_pack_aor_agent_bus_full_dispatch_executor_preview_ready": agent_bus_full_dispatch_preview_result.get("full_dispatch_executor_preview_ready"),
                        "source_pack_aor_agent_bus_full_dispatch_executor_statement_visible": bool(
                            agent_bus_full_dispatch_preview_result.get("required_operator_statement")
                        ),
                        "source_pack_aor_agent_bus_full_dispatch_visible": "full dispatch complete" in normalized,
                        "source_pack_aor_agent_bus_full_dispatch_result_ok": bool(agent_bus_full_dispatch_result.get("ok")),
                        "source_pack_aor_agent_bus_full_dispatch_marker_written": agent_bus_full_dispatch_result.get("aor_full_dispatch_marker_written"),
                        "source_pack_aor_agent_bus_full_dispatch_artifact_written": agent_bus_full_dispatch_result.get("aor_full_dispatch_artifact_written"),
                        "source_pack_aor_agent_bus_full_dispatch_written_paths_exist": agent_bus_full_dispatch_written_paths_exist,
                        "source_pack_aor_agent_bus_full_dispatch_written_path_count": len(agent_bus_full_dispatch_written_paths),
                        "source_pack_aor_agent_bus_full_dispatch_aor_result_status": agent_bus_full_dispatch_result.get("aor_result_status"),
                        "source_pack_aor_agent_bus_full_dispatch_aor_result_stage": agent_bus_full_dispatch_result.get("aor_result_stage_reached"),
                        "source_pack_aor_agent_bus_full_dispatch_osril_session_created": agent_bus_full_dispatch_result.get("osril_session_created"),
                        "source_pack_aor_agent_bus_full_dispatch_osril_event_written": agent_bus_full_dispatch_result.get("osril_event_written"),
                        "source_pack_aor_agent_bus_full_dispatch_aor_audit_written": agent_bus_full_dispatch_result.get("aor_audit_written"),
                        "source_pack_aor_agent_bus_source_pack_writeback_created": agent_bus_full_dispatch_result.get("source_pack_writeback_created"),
                        "source_pack_aor_agent_bus_source_pack_writeback_path_count": len(
                            agent_bus_full_dispatch_result.get("runtime_acquisition_pack_new_files") or []
                        ),
                        "source_pack_aor_agent_bus_task_body_executed_after_full_dispatch_readiness": agent_bus_full_dispatch_readiness_result.get("agent_bus_task_body_executed"),
                        "source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch_readiness": agent_bus_full_dispatch_readiness_result.get("runtime_process_started"),
                        "source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch_readiness": agent_bus_full_dispatch_readiness_result.get("sic_ingestion_performed"),
                        "source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch_readiness": agent_bus_full_dispatch_readiness_result.get("canonical_mutation_performed"),
                        "source_pack_aor_agent_bus_graph_mutation_after_full_dispatch_readiness": agent_bus_full_dispatch_readiness_result.get("graph_index_mutation_performed"),
                        "source_pack_aor_agent_bus_task_body_executed_after_full_dispatch": agent_bus_full_dispatch_result.get("agent_bus_task_body_executed"),
                        "source_pack_aor_agent_bus_task_executed_after_full_dispatch": agent_bus_full_dispatch_result.get("agent_bus_task_executed"),
                        "source_pack_aor_agent_bus_task_status_updated_after_full_dispatch": agent_bus_full_dispatch_result.get("agent_bus_task_status_updated"),
                        "source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch": agent_bus_full_dispatch_result.get("runtime_process_started"),
                        "source_pack_aor_agent_bus_watch_loop_started_after_full_dispatch": agent_bus_full_dispatch_result.get("agent_bus_watch_loop_started"),
                        "source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch": agent_bus_full_dispatch_result.get("sic_ingestion_performed"),
                        "source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch": agent_bus_full_dispatch_result.get("canonical_mutation_performed"),
                        "source_pack_aor_agent_bus_graph_mutation_after_full_dispatch": agent_bus_full_dispatch_result.get("graph_index_mutation_performed"),
                        "source_pack_aor_agent_bus_provider_call_after_full_dispatch": agent_bus_full_dispatch_result.get("provider_call_performed"),
                        "source_pack_aor_agent_bus_external_send_after_full_dispatch": agent_bus_full_dispatch_result.get("external_send_performed"),
                        "source_pack_aor_agent_bus_attachment_delete_after_full_dispatch": agent_bus_full_dispatch_result.get("attachment_delete_performed"),
                        "source_pack_sic_ingestion_readiness_visible": (
                            "source intelligence core ingestion readiness" in normalized
                        ),
                        "source_pack_sic_ingestion_readiness_result_ok": bool(source_pack_sic_readiness_result.get("ok")),
                        "source_pack_sic_ingestion_writeback_verified": source_pack_sic_readiness_result.get("source_pack_writeback_verified"),
                        "source_pack_sic_ingestion_contracts_verified": source_pack_sic_readiness_result.get("sic_contracts_verified"),
                        "source_pack_sic_ingestion_future_packet_ready": source_pack_sic_readiness_result.get("future_sic_ingestion_packet_preview_ready"),
                        "source_pack_sic_ingestion_ready_for_approval_design": source_pack_sic_readiness_result.get("ready_for_sic_ingestion_approval_design"),
                        "source_pack_sic_ingestion_ready_for_executor": source_pack_sic_readiness_result.get("ready_for_sic_ingestion_executor"),
                        "source_pack_sic_ingestion_allowed_now": source_pack_sic_readiness_result.get("sic_ingestion_allowed_now"),
                        "source_pack_sic_ingestion_performed": source_pack_sic_readiness_result.get("sic_ingestion_performed"),
                        "source_pack_sic_source_package_written": source_pack_sic_readiness_result.get("sic_source_package_written"),
                        "source_pack_sic_workspace_membership_written": source_pack_sic_readiness_result.get("sic_workspace_membership_written"),
                        "source_pack_sic_graph_mutation": source_pack_sic_readiness_result.get("graph_index_mutation_performed"),
                        "source_pack_sic_canonical_mutation": source_pack_sic_readiness_result.get("canonical_mutation_performed"),
                        "source_pack_sic_provider_call": source_pack_sic_readiness_result.get("provider_call_performed"),
                        "source_pack_sic_external_send": source_pack_sic_readiness_result.get("external_send_performed"),
                        "source_pack_sic_ingestion_approval_design_visible": (
                            "source intelligence core approval design" in normalized
                        ),
                        "source_pack_sic_ingestion_approval_design_result_ok": bool(
                            source_pack_sic_approval_design_result.get("ok")
                        ),
                        "source_pack_sic_ingestion_approval_packet_ready": source_pack_sic_approval_design_result.get(
                            "future_source_intelligence_core_ingestion_approval_packet_preview_ready"
                        ),
                        "source_pack_sic_ingestion_approval_request_written": source_pack_sic_approval_design_result.get(
                            "approval_request_written"
                        ),
                        "source_pack_sic_ingestion_executor_ready_after_approval_design": source_pack_sic_approval_design_result.get(
                            "ready_for_source_intelligence_core_ingestion_executor"
                        ),
                        "source_pack_sic_ingestion_allowed_after_approval_design": source_pack_sic_approval_design_result.get(
                            "source_intelligence_core_ingestion_allowed_now"
                        ),
                        "source_pack_sic_ingestion_performed_after_approval_design": source_pack_sic_approval_design_result.get(
                            "source_intelligence_core_ingestion_performed"
                        ),
                        "source_pack_sic_graph_mutation_after_approval_design": source_pack_sic_approval_design_result.get(
                            "graph_index_mutation_performed"
                        ),
                        "source_pack_sic_canonical_mutation_after_approval_design": source_pack_sic_approval_design_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_sic_provider_call_after_approval_design": source_pack_sic_approval_design_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_sic_external_send_after_approval_design": source_pack_sic_approval_design_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_sic_ingestion_approval_request_visible": (
                            "source intelligence core approval request" in normalized
                        ),
                        "source_pack_sic_ingestion_approval_request_result_ok": bool(
                            source_pack_sic_approval_request_result.get("ok")
                        ),
                        "source_pack_sic_ingestion_approval_request_written_after_request": source_pack_sic_approval_request_result.get(
                            "approval_request_written"
                        ),
                        "source_pack_sic_ingestion_approval_artifact_written_after_request": source_pack_sic_approval_request_result.get(
                            "approval_artifact_written"
                        ),
                        "source_pack_sic_ingestion_approval_request_written_paths_exist": source_pack_sic_approval_request_written_paths_exist,
                        "source_pack_sic_ingestion_approval_decision_written_after_request": source_pack_sic_approval_request_result.get(
                            "approval_decision_written"
                        ),
                        "source_pack_sic_ingestion_approval_consumed_after_request": source_pack_sic_approval_request_result.get(
                            "approval_consumed"
                        ),
                        "source_pack_sic_ingestion_approval_decision_readiness_visible": (
                            "source intelligence core decision readiness" in normalized
                        ),
                        "source_pack_sic_ingestion_approval_decision_readiness_result_ok": bool(
                            source_pack_sic_decision_readiness_result.get("ok")
                        ),
                        "source_pack_sic_ingestion_approval_request_verified_for_decision": source_pack_sic_decision_readiness_result.get(
                            "approval_request_artifact_verified"
                        ),
                        "source_pack_sic_ingestion_approval_decision_writer_ready_after_readiness": source_pack_sic_decision_readiness_result.get(
                            "ready_for_source_intelligence_core_approval_decision_writer"
                        ),
                        "source_pack_sic_ingestion_approval_consumed_after_readiness": source_pack_sic_decision_readiness_result.get(
                            "approval_consumed"
                        ),
                        "source_pack_sic_ingestion_approval_decision_visible": (
                            "source intelligence core approval decision" in normalized
                        ),
                        "source_pack_sic_ingestion_approval_decision_result_ok": bool(
                            source_pack_sic_approval_decision_result.get("ok")
                        ),
                        "source_pack_sic_ingestion_approval_decision_written_after_decision": source_pack_sic_approval_decision_result.get(
                            "approval_decision_written"
                        ),
                        "source_pack_sic_ingestion_approval_decision_written_paths_exist": source_pack_sic_approval_decision_written_paths_exist,
                        "source_pack_sic_ingestion_approval_consumed_after_decision": source_pack_sic_approval_decision_result.get(
                            "approval_consumed"
                        ),
                        "source_pack_sic_ingestion_approval_consumption_ready_after_decision": source_pack_sic_approval_decision_result.get(
                            "ready_for_source_intelligence_core_approval_consumption"
                        ),
                        "source_pack_sic_ingestion_executor_ready_after_decision": source_pack_sic_approval_decision_result.get(
                            "ready_for_source_intelligence_core_ingestion_executor"
                        ),
                        "source_pack_sic_ingestion_allowed_after_decision": source_pack_sic_approval_decision_result.get(
                            "source_intelligence_core_ingestion_allowed_now"
                        ),
                        "source_pack_sic_ingestion_performed_after_decision": source_pack_sic_approval_decision_result.get(
                            "source_intelligence_core_ingestion_performed"
                        ),
                        "source_pack_sic_source_package_written_after_decision": source_pack_sic_approval_decision_result.get(
                            "source_intelligence_core_source_package_written"
                        ),
                        "source_pack_sic_workspace_membership_written_after_decision": source_pack_sic_approval_decision_result.get(
                            "source_intelligence_core_workspace_membership_written"
                        ),
                        "source_pack_sic_graph_mutation_after_decision": source_pack_sic_approval_decision_result.get(
                            "graph_index_mutation_performed"
                        ),
                        "source_pack_sic_canonical_mutation_after_decision": source_pack_sic_approval_decision_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_sic_provider_call_after_decision": source_pack_sic_approval_decision_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_sic_external_send_after_decision": source_pack_sic_approval_decision_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_sic_attachment_delete_after_decision": source_pack_sic_approval_decision_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_sic_ingestion_approval_consumption_preview_visible": (
                            "source intelligence core approval consumption preview" in normalized
                        ),
                        "source_pack_sic_ingestion_approval_consumption_visible": (
                            "source intelligence core approval consumption" in normalized
                        ),
                        "source_pack_sic_ingestion_approval_consumption_result_ok": bool(
                            source_pack_sic_approval_consumption_result.get("ok")
                        ),
                        "source_pack_sic_ingestion_approval_consumed_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "approval_consumed"
                        ),
                        "source_pack_sic_ingestion_approval_decision_consumed_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "approval_decision_consumed"
                        ),
                        "source_pack_sic_ingestion_approval_consumption_marker_written": source_pack_sic_approval_consumption_result.get(
                            "approval_exact_once_marker_written"
                        ),
                        "source_pack_sic_ingestion_approval_consumption_artifact_written": source_pack_sic_approval_consumption_result.get(
                            "approval_consumption_artifact_written"
                        ),
                        "source_pack_sic_ingestion_approval_consumption_written_paths_exist": source_pack_sic_approval_consumption_written_paths_exist,
                        "source_pack_sic_ingestion_executor_ready_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "ready_for_source_intelligence_core_ingestion_executor"
                        ),
                        "source_pack_sic_ingestion_allowed_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "source_intelligence_core_ingestion_allowed_now"
                        ),
                        "source_pack_sic_ingestion_performed_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "source_intelligence_core_ingestion_performed"
                        ),
                        "source_pack_sic_source_package_written_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "source_intelligence_core_source_package_written"
                        ),
                        "source_pack_sic_workspace_membership_written_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "source_intelligence_core_workspace_membership_written"
                        ),
                        "source_pack_sic_graph_mutation_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "graph_index_mutation_performed"
                        ),
                        "source_pack_sic_canonical_mutation_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_sic_provider_call_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_sic_external_send_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_sic_attachment_delete_after_consumption": source_pack_sic_approval_consumption_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_sic_ingestion_preview_visible": (
                            "source intelligence core ingestion preview" in normalized
                        ),
                        "source_pack_sic_ingestion_preview_result_ok": bool(
                            source_pack_sic_ingestion_preview_result.get("ok")
                        ),
                        "source_pack_sic_ingestion_preview_ready": source_pack_sic_ingestion_preview_result.get(
                            "source_intelligence_core_ingestion_preview_ready"
                        ),
                        "source_pack_sic_ingestion_digest_ready": bool(
                            source_pack_sic_ingestion_preview_result.get(
                                "source_intelligence_core_ingestion_digest"
                            )
                        ),
                        "source_pack_sic_ingestion_visible": (
                            "source intelligence core ingestion complete" in normalized
                            or "source intelligence core ingestion" in normalized
                        ),
                        "source_pack_sic_ingestion_result_ok": bool(
                            source_pack_sic_ingestion_result.get("ok")
                        ),
                        "source_pack_sic_ingestion_written_paths_exist": source_pack_sic_ingestion_written_paths_exist,
                        "source_pack_sic_ingestion_performed_after_ingestion": source_pack_sic_ingestion_result.get(
                            "source_intelligence_core_ingestion_performed"
                        ),
                        "source_pack_sic_workspace_written_after_ingestion": source_pack_sic_ingestion_result.get(
                            "source_intelligence_core_workspace_written"
                        ),
                        "source_pack_sic_source_package_written_after_ingestion": source_pack_sic_ingestion_result.get(
                            "source_intelligence_core_source_package_written"
                        ),
                        "source_pack_sic_workspace_membership_written_after_ingestion": source_pack_sic_ingestion_result.get(
                            "source_intelligence_core_workspace_membership_written"
                        ),
                        "source_pack_sic_graph_mutation_after_ingestion": source_pack_sic_ingestion_result.get(
                            "graph_index_mutation_performed"
                        ),
                        "source_pack_sic_canonical_mutation_after_ingestion": source_pack_sic_ingestion_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_sic_provider_call_after_ingestion": source_pack_sic_ingestion_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_sic_external_send_after_ingestion": source_pack_sic_ingestion_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_sic_attachment_delete_after_ingestion": source_pack_sic_ingestion_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_sic_graph_indexing_readiness_visible": (
                            "graph indexing executor preview ready" in normalized
                            or "graph readiness" in normalized
                        ),
                        "source_pack_sic_graph_indexing_readiness_result_ok": bool(
                            source_pack_sic_graph_readiness_result.get("ok")
                        ),
                        "source_pack_sic_graph_indexing_readiness_preview_ready": source_pack_sic_graph_readiness_result.get(
                            "graph_indexing_readiness_preview_ready"
                        ),
                        "source_pack_sic_graph_indexing_readiness_packet_digest_ready": bool(
                            source_pack_sic_graph_readiness_result.get("graph_index_preview_packet_digest")
                        ),
                        "source_pack_sic_graph_indexing_candidate_node_count": (
                            source_pack_sic_graph_readiness_result.get("graph_index_candidate_preview") or {}
                        ).get("candidate_node_count"),
                        "source_pack_sic_graph_indexing_candidate_edge_count": (
                            source_pack_sic_graph_readiness_result.get("graph_index_candidate_preview") or {}
                        ).get("candidate_edge_count"),
                        "source_pack_sic_graph_mutation_after_graph_readiness": source_pack_sic_graph_readiness_result.get(
                            "graph_index_mutation_performed"
                        ),
                        "source_pack_sic_graph_snapshot_written_after_graph_readiness": source_pack_sic_graph_readiness_result.get(
                            "graph_snapshot_written"
                        ),
                        "source_pack_sic_canonical_mutation_after_graph_readiness": source_pack_sic_graph_readiness_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_sic_provider_call_after_graph_readiness": source_pack_sic_graph_readiness_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_sic_external_send_after_graph_readiness": source_pack_sic_graph_readiness_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_sic_attachment_delete_after_graph_readiness": source_pack_sic_graph_readiness_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_sic_graph_indexing_preview_result_ok": bool(
                            source_pack_sic_graph_indexing_preview_result.get("ok")
                        ),
                        "source_pack_sic_graph_indexing_preview_ready": source_pack_sic_graph_indexing_preview_result.get(
                            "graph_indexing_executor_preview_ready"
                        ),
                        "source_pack_sic_graph_indexing_write_allowed_preview": source_pack_sic_graph_indexing_preview_result.get(
                            "graph_indexing_write_allowed_now"
                        ),
                        "source_pack_sic_graph_indexing_visible": (
                            "graph snapshot written" in normalized
                        ),
                        "source_pack_sic_graph_indexing_result_ok": bool(
                            source_pack_sic_graph_indexing_result.get("ok")
                        ),
                        "source_pack_sic_graph_indexing_written_paths_exist": source_pack_sic_graph_indexing_written_paths_exist,
                        "source_pack_sic_graph_mutation_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "graph_index_mutation_performed"
                        ),
                        "source_pack_sic_graph_snapshot_written_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "graph_snapshot_written"
                        ),
                        "source_pack_sic_graph_store_manifest_written_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "graph_store_manifest_written"
                        ),
                        "source_pack_sic_graph_current_pointer_written_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "graph_current_pointer_written"
                        ),
                        "source_pack_sic_canonical_mutation_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_sic_provider_call_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_sic_external_send_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_sic_attachment_delete_after_graph_indexing": source_pack_sic_graph_indexing_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_canonical_promotion_readiness_visible": (
                            "canonical promotion readiness ready" in normalized
                            and "canonical readiness" in normalized
                        ),
                        "source_pack_canonical_promotion_readiness_result_ok": bool(
                            source_pack_canonical_promotion_readiness_result.get("ok")
                        ),
                        "source_pack_canonical_promotion_readiness_preview_ready": source_pack_canonical_promotion_readiness_result.get(
                            "canonical_promotion_readiness_preview_ready"
                        ),
                        "source_pack_canonical_promotion_candidate_digest_ready": bool(
                            source_pack_canonical_promotion_readiness_result.get(
                                "future_canonical_promotion_candidate_digest"
                            )
                        ),
                        "source_pack_canonical_promotion_target_count": source_pack_canonical_promotion_readiness_result.get(
                            "canonical_target_count"
                        ),
                        "source_pack_canonical_promotion_graph_store_current_pointer_verified": source_pack_canonical_promotion_readiness_result.get(
                            "graph_store_current_pointer_verified"
                        ),
                        "source_pack_canonical_promotion_canonical_allowed_now": source_pack_canonical_promotion_readiness_result.get(
                            "canonical_mutation_allowed_now"
                        ),
                        "source_pack_canonical_promotion_canonical_mutation_performed": source_pack_canonical_promotion_readiness_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_canonical_promotion_knowledge_promotion_performed": source_pack_canonical_promotion_readiness_result.get(
                            "canonical_knowledge_promotion_performed"
                        ),
                        "source_pack_canonical_promotion_provider_call_performed": source_pack_canonical_promotion_readiness_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_canonical_promotion_external_send_performed": source_pack_canonical_promotion_readiness_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_canonical_promotion_attachment_delete_performed": source_pack_canonical_promotion_readiness_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_canonical_promotion_approval_design_visible": (
                            "canonical approval design ready" in normalized
                            and "canonical approval" in normalized
                        ),
                        "source_pack_canonical_promotion_approval_design_result_ok": bool(
                            source_pack_canonical_promotion_approval_design_result.get("ok")
                        ),
                        "source_pack_canonical_promotion_approval_packet_preview_ready": source_pack_canonical_promotion_approval_design_result.get(
                            "future_canonical_promotion_approval_packet_preview_ready"
                        ),
                        "source_pack_canonical_promotion_approval_request_digest_ready": bool(
                            (
                                source_pack_canonical_promotion_approval_design_result.get(
                                    "future_canonical_promotion_approval_packet_preview"
                                )
                                or {}
                            ).get("approval_request_digest")
                        ),
                        "source_pack_canonical_promotion_approval_request_written_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "approval_request_written"
                        ),
                        "source_pack_canonical_promotion_executor_ready_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "ready_for_canonical_promotion_executor"
                        ),
                        "source_pack_canonical_promotion_allowed_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "canonical_promotion_allowed_now"
                        ),
                        "source_pack_canonical_promotion_performed_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "canonical_promotion_performed"
                        ),
                        "source_pack_canonical_promotion_note_written_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "canonical_knowledge_note_written"
                        ),
                        "source_pack_canonical_promotion_index_written_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "canonical_knowledge_index_written"
                        ),
                        "source_pack_canonical_promotion_provider_call_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_canonical_promotion_external_send_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_canonical_promotion_attachment_delete_after_design": source_pack_canonical_promotion_approval_design_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_canonical_promotion_approval_request_visible": (
                            "canonical request written" in normalized
                            and "request written" in normalized
                        ),
                        "source_pack_canonical_promotion_approval_request_result_ok": bool(
                            source_pack_canonical_promotion_approval_request_result.get("ok")
                        ),
                        "source_pack_canonical_promotion_approval_request_written": source_pack_canonical_promotion_approval_request_result.get(
                            "approval_request_written"
                        ),
                        "source_pack_canonical_promotion_approval_request_artifact_written": source_pack_canonical_promotion_approval_request_result.get(
                            "approval_artifact_written"
                        ),
                        "source_pack_canonical_promotion_approval_request_written_paths_exist": source_pack_canonical_promotion_approval_request_written_paths_exist,
                        "source_pack_canonical_promotion_ready_for_decision_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "ready_for_canonical_promotion_approval_decision"
                        ),
                        "source_pack_canonical_promotion_executor_ready_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "ready_for_canonical_promotion_executor"
                        ),
                        "source_pack_canonical_promotion_allowed_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "canonical_promotion_allowed_now"
                        ),
                        "source_pack_canonical_promotion_performed_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "canonical_promotion_performed"
                        ),
                        "source_pack_canonical_promotion_note_written_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "canonical_knowledge_note_written"
                        ),
                        "source_pack_canonical_promotion_index_written_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "canonical_knowledge_index_written"
                        ),
                        "source_pack_canonical_promotion_provider_call_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_canonical_promotion_external_send_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_canonical_promotion_attachment_delete_after_request": source_pack_canonical_promotion_approval_request_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_visible": (
                            "canonical decision readiness verified" in normalized
                            and "request verified" in normalized
                        ),
                        "source_pack_canonical_promotion_decision_readiness_result_ok": bool(
                            source_pack_canonical_promotion_decision_readiness_result.get("ok")
                        ),
                        "source_pack_canonical_promotion_decision_readiness_request_verified": source_pack_canonical_promotion_decision_readiness_result.get(
                            "approval_request_artifact_verified"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_pending": source_pack_canonical_promotion_decision_readiness_result.get(
                            "approval_request_pending"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_decision_writer_ready": source_pack_canonical_promotion_decision_readiness_result.get(
                            "ready_for_canonical_promotion_approval_decision_writer"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_decision_ready": source_pack_canonical_promotion_decision_readiness_result.get(
                            "ready_for_canonical_promotion_approval_decision"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_decision_option_count": len(
                            source_pack_canonical_promotion_decision_readiness_result.get(
                                "future_approval_decision_options"
                            )
                            or []
                        ),
                        "source_pack_canonical_promotion_decision_readiness_consumption_ready": source_pack_canonical_promotion_decision_readiness_result.get(
                            "ready_for_canonical_promotion_approval_consumption"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_executor_ready": source_pack_canonical_promotion_decision_readiness_result.get(
                            "ready_for_canonical_promotion_executor"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_decision_written": source_pack_canonical_promotion_decision_readiness_result.get(
                            "approval_decision_written"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_approval_consumed": source_pack_canonical_promotion_decision_readiness_result.get(
                            "approval_consumed"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_marker_written": source_pack_canonical_promotion_decision_readiness_result.get(
                            "approval_exact_once_marker_written"
                        ),
                        "source_pack_canonical_promotion_decision_readiness_future_marker_exists": (
                            source_pack_canonical_promotion_decision_readiness_result.get(
                                "future_approval_consumption_marker_exists"
                            )
                        ),
                        "source_pack_canonical_promotion_allowed_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "canonical_promotion_allowed_now"
                        ),
                        "source_pack_canonical_promotion_performed_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "canonical_promotion_performed"
                        ),
                        "source_pack_canonical_promotion_note_written_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "canonical_knowledge_note_written"
                        ),
                        "source_pack_canonical_promotion_index_written_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "canonical_knowledge_index_written"
                        ),
                        "source_pack_canonical_promotion_graph_mutation_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "canonical_graph_mutation_performed"
                        ),
                        "source_pack_canonical_promotion_provider_call_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_canonical_promotion_external_send_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_canonical_promotion_attachment_delete_after_decision_readiness": source_pack_canonical_promotion_decision_readiness_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_canonical_promotion_approval_decision_visible": (
                            "canonical approval decision written" in normalized
                            and "canonical approval decision" in normalized
                        ),
                        "source_pack_canonical_promotion_approval_decision_result_ok": bool(
                            source_pack_canonical_promotion_approval_decision_result.get("ok")
                        ),
                        "source_pack_canonical_promotion_approval_decision_written": source_pack_canonical_promotion_approval_decision_result.get(
                            "approval_decision_written"
                        ),
                        "source_pack_canonical_promotion_approval_decision_artifact_written": source_pack_canonical_promotion_approval_decision_result.get(
                            "approval_decision_artifact_written"
                        ),
                        "source_pack_canonical_promotion_approval_decision_written_paths_exist": source_pack_canonical_promotion_approval_decision_written_paths_exist,
                        "source_pack_canonical_promotion_approval_consumption_ready_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "ready_for_canonical_promotion_approval_consumption"
                        ),
                        "source_pack_canonical_promotion_executor_ready_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "ready_for_canonical_promotion_executor"
                        ),
                        "source_pack_canonical_promotion_approval_consumed_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "approval_consumed"
                        ),
                        "source_pack_canonical_promotion_marker_written_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "approval_exact_once_marker_written"
                        ),
                        "source_pack_canonical_promotion_allowed_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "canonical_promotion_allowed_now"
                        ),
                        "source_pack_canonical_promotion_performed_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "canonical_promotion_performed"
                        ),
                        "source_pack_canonical_promotion_note_written_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "canonical_knowledge_note_written"
                        ),
                        "source_pack_canonical_promotion_index_written_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "canonical_knowledge_index_written"
                        ),
                        "source_pack_canonical_promotion_graph_mutation_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "canonical_graph_mutation_performed"
                        ),
                        "source_pack_canonical_promotion_provider_call_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_canonical_promotion_external_send_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_canonical_promotion_attachment_delete_after_decision": source_pack_canonical_promotion_approval_decision_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_canonical_promotion_approval_consumption_visible": (
                            "canonical approval decision consumed" in normalized
                            and "canonical approval consumption" in normalized
                        ),
                        "source_pack_canonical_promotion_approval_consumption_result_ok": bool(
                            source_pack_canonical_promotion_approval_consumption_result.get("ok")
                        ),
                        "source_pack_canonical_promotion_approval_consumed": source_pack_canonical_promotion_approval_consumption_result.get(
                            "approval_consumed"
                        ),
                        "source_pack_canonical_promotion_approval_consumption_artifact_written": source_pack_canonical_promotion_approval_consumption_result.get(
                            "approval_consumption_artifact_written"
                        ),
                        "source_pack_canonical_promotion_approval_consumption_marker_written": source_pack_canonical_promotion_approval_consumption_result.get(
                            "approval_exact_once_marker_written"
                        ),
                        "source_pack_canonical_promotion_approval_consumption_written_paths_exist": source_pack_canonical_promotion_approval_consumption_written_paths_exist,
                        "source_pack_canonical_promotion_executor_ready_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "ready_for_canonical_promotion_executor"
                        ),
                        "source_pack_canonical_promotion_allowed_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "canonical_promotion_allowed_now"
                        ),
                        "source_pack_canonical_promotion_performed_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "canonical_promotion_performed"
                        ),
                        "source_pack_canonical_promotion_note_written_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "canonical_knowledge_note_written"
                        ),
                        "source_pack_canonical_promotion_index_written_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "canonical_knowledge_index_written"
                        ),
                        "source_pack_canonical_promotion_graph_mutation_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "canonical_graph_mutation_performed"
                        ),
                        "source_pack_canonical_promotion_provider_call_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_canonical_promotion_external_send_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_canonical_promotion_attachment_delete_after_consumption": source_pack_canonical_promotion_approval_consumption_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_canonical_promotion_executor_visible": (
                            "canonical knowledge promoted" in normalized
                            and "canonical promotion" in normalized
                        ),
                        "source_pack_canonical_promotion_executor_result_ok": bool(
                            source_pack_canonical_promotion_result.get("ok")
                        ),
                        "source_pack_canonical_promotion_marker_written": source_pack_canonical_promotion_result.get(
                            "canonical_promotion_marker_written"
                        ),
                        "source_pack_canonical_promotion_note_written": source_pack_canonical_promotion_result.get(
                            "canonical_knowledge_note_written"
                        ),
                        "source_pack_canonical_promotion_index_written": source_pack_canonical_promotion_result.get(
                            "canonical_knowledge_index_written"
                        ),
                        "source_pack_canonical_promotion_artifact_written": source_pack_canonical_promotion_result.get(
                            "canonical_promotion_artifact_written"
                        ),
                        "source_pack_canonical_promotion_written_paths_exist": source_pack_canonical_promotion_written_paths_exist,
                        "source_pack_canonical_promotion_written_path_count": len(
                            source_pack_canonical_promotion_written_paths
                        ),
                        "source_pack_canonical_promotion_canonical_mutation_after_executor": source_pack_canonical_promotion_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_canonical_promotion_graph_mutation_after_executor": source_pack_canonical_promotion_result.get(
                            "canonical_graph_mutation_performed"
                        ),
                        "source_pack_canonical_promotion_source_intelligence_core_rewrite_after_executor": source_pack_canonical_promotion_result.get(
                            "source_intelligence_core_rewrite_performed"
                        ),
                        "source_pack_canonical_promotion_provider_call_after_executor": source_pack_canonical_promotion_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_canonical_promotion_external_send_after_executor": source_pack_canonical_promotion_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_canonical_promotion_attachment_delete_after_executor": source_pack_canonical_promotion_result.get(
                            "attachment_delete_performed"
                        ),
                        "source_pack_sic_ingestion_executor_ready_after_approval_request": source_pack_sic_approval_request_result.get(
                            "ready_for_source_intelligence_core_ingestion_executor"
                        ),
                        "source_pack_sic_ingestion_allowed_after_approval_request": source_pack_sic_approval_request_result.get(
                            "source_intelligence_core_ingestion_allowed_now"
                        ),
                        "source_pack_sic_ingestion_performed_after_approval_request": source_pack_sic_approval_request_result.get(
                            "source_intelligence_core_ingestion_performed"
                        ),
                        "source_pack_sic_source_package_written_after_approval_request": source_pack_sic_approval_request_result.get(
                            "source_intelligence_core_source_package_written"
                        ),
                        "source_pack_sic_workspace_membership_written_after_approval_request": source_pack_sic_approval_request_result.get(
                            "source_intelligence_core_workspace_membership_written"
                        ),
                        "source_pack_sic_graph_mutation_after_approval_request": source_pack_sic_approval_request_result.get(
                            "graph_index_mutation_performed"
                        ),
                        "source_pack_sic_canonical_mutation_after_approval_request": source_pack_sic_approval_request_result.get(
                            "canonical_mutation_performed"
                        ),
                        "source_pack_sic_provider_call_after_approval_request": source_pack_sic_approval_request_result.get(
                            "provider_call_performed"
                        ),
                        "source_pack_sic_external_send_after_approval_request": source_pack_sic_approval_request_result.get(
                            "external_send_performed"
                        ),
                        "source_pack_sic_attachment_delete_after_approval_request": source_pack_sic_approval_request_result.get(
                            "attachment_delete_performed"
                        ),
                        "disposition_policy_id": disposition.get("policy_id"),
                        "disposition_after_review": disposition.get("default_disposition"),
                        "runtime_delete_allowed": disposition.get("runtime_delete_allowed"),
                        "missing_required_tokens": missing,
                    }
                )
                page.close()
        finally:
            browser.close()
            for item in fixtures:
                shutil.rmtree(item["fixture_vault"], ignore_errors=True)

    severe_console = [
        item for item in console_messages
        if item.startswith(("error:", "warning:")) and "favicon" not in item.lower()
    ]
    return {
        "url": url,
        "screenshots": screenshots,
        "console_errors_or_warnings": severe_console,
        "page_errors": page_errors,
    }


def _format_markdown(report: dict[str, Any]) -> str:
    screenshot_lines = "\n".join(
        " ".join(
            [
                f"- {item['viewport']}: `{item['path']}`",
                f"bytes={item['bytes']}",
                f"policy_visible={item['policy_visible']}",
                f"review_state_visible={item.get('review_state_visible')}",
                f"source_pack_write_completed_visible={item.get('source_pack_write_completed_visible')}",
                f"task_status_lifecycle_visible={item.get('source_pack_aor_agent_bus_claimed_task_status_lifecycle_visible')}",
                f"full_dispatch_readiness_visible={item.get('source_pack_aor_agent_bus_full_dispatch_readiness_visible')}",
                f"full_dispatch_visible={item.get('source_pack_aor_agent_bus_full_dispatch_visible')}",
                f"full_dispatch_result_ok={item.get('source_pack_aor_agent_bus_full_dispatch_result_ok')}",
                f"source_pack_writeback_created={item.get('source_pack_aor_agent_bus_source_pack_writeback_created')}",
                "source_intelligence_core_ingestion_readiness_visible="
                f"{item.get('source_pack_sic_ingestion_readiness_visible')}",
                "source_intelligence_core_ingestion_readiness_result_ok="
                f"{item.get('source_pack_sic_ingestion_readiness_result_ok')}",
                "source_intelligence_core_approval_design_visible="
                f"{item.get('source_pack_sic_ingestion_approval_design_visible')}",
                "source_intelligence_core_approval_design_result_ok="
                f"{item.get('source_pack_sic_ingestion_approval_design_result_ok')}",
                "source_intelligence_core_approval_request_visible="
                f"{item.get('source_pack_sic_ingestion_approval_request_visible')}",
                "source_intelligence_core_approval_request_result_ok="
                f"{item.get('source_pack_sic_ingestion_approval_request_result_ok')}",
                "source_intelligence_core_approval_request_written="
                f"{item.get('source_pack_sic_ingestion_approval_request_written_after_request')}",
                "source_intelligence_core_decision_readiness_visible="
                f"{item.get('source_pack_sic_ingestion_approval_decision_readiness_visible')}",
                "source_intelligence_core_decision_readiness_result_ok="
                f"{item.get('source_pack_sic_ingestion_approval_decision_readiness_result_ok')}",
                "source_intelligence_core_decision_writer_ready="
                f"{item.get('source_pack_sic_ingestion_approval_decision_writer_ready_after_readiness')}",
                "source_intelligence_core_approval_decision_visible="
                f"{item.get('source_pack_sic_ingestion_approval_decision_visible')}",
                "source_intelligence_core_approval_decision_result_ok="
                f"{item.get('source_pack_sic_ingestion_approval_decision_result_ok')}",
                "source_intelligence_core_approval_decision_written="
                f"{item.get('source_pack_sic_ingestion_approval_decision_written_after_decision')}",
                "source_intelligence_core_approval_consumption_visible="
                f"{item.get('source_pack_sic_ingestion_approval_consumption_visible')}",
                "source_intelligence_core_approval_consumption_result_ok="
                f"{item.get('source_pack_sic_ingestion_approval_consumption_result_ok')}",
                "source_intelligence_core_approval_consumed="
                f"{item.get('source_pack_sic_ingestion_approval_consumed_after_consumption')}",
                "source_intelligence_core_approval_consumption_written_paths_exist="
                f"{item.get('source_pack_sic_ingestion_approval_consumption_written_paths_exist')}",
                "source_intelligence_core_ingestion_preview_visible="
                f"{item.get('source_pack_sic_ingestion_preview_visible')}",
                "source_intelligence_core_ingestion_preview_result_ok="
                f"{item.get('source_pack_sic_ingestion_preview_result_ok')}",
                "source_intelligence_core_ingestion_digest_ready="
                f"{item.get('source_pack_sic_ingestion_digest_ready')}",
                "source_intelligence_core_ingestion_visible="
                f"{item.get('source_pack_sic_ingestion_visible')}",
                "source_intelligence_core_ingestion_result_ok="
                f"{item.get('source_pack_sic_ingestion_result_ok')}",
                "source_intelligence_core_ingestion_written_paths_exist="
                f"{item.get('source_pack_sic_ingestion_written_paths_exist')}",
                "source_intelligence_core_workspace_written="
                f"{item.get('source_pack_sic_workspace_written_after_ingestion')}",
                "source_intelligence_core_source_package_written="
                f"{item.get('source_pack_sic_source_package_written_after_ingestion')}",
                "source_intelligence_core_workspace_membership_written="
                f"{item.get('source_pack_sic_workspace_membership_written_after_ingestion')}",
                "source_intelligence_core_graph_mutation="
                f"{item.get('source_pack_sic_graph_mutation_after_ingestion')}",
                "source_intelligence_core_canonical_mutation="
                f"{item.get('source_pack_sic_canonical_mutation_after_ingestion')}",
                "canonical_promotion_readiness_visible="
                f"{item.get('source_pack_canonical_promotion_readiness_visible')}",
                "canonical_promotion_readiness_result_ok="
                f"{item.get('source_pack_canonical_promotion_readiness_result_ok')}",
                "canonical_promotion_target_count="
                f"{item.get('source_pack_canonical_promotion_target_count')}",
                "canonical_promotion_canonical_mutation="
                f"{item.get('source_pack_canonical_promotion_canonical_mutation_performed')}",
                "canonical_promotion_approval_design_visible="
                f"{item.get('source_pack_canonical_promotion_approval_design_visible')}",
                "canonical_promotion_approval_design_result_ok="
                f"{item.get('source_pack_canonical_promotion_approval_design_result_ok')}",
                "canonical_promotion_approval_request_digest_ready="
                f"{item.get('source_pack_canonical_promotion_approval_request_digest_ready')}",
                "canonical_promotion_approval_request_written="
                f"{item.get('source_pack_canonical_promotion_approval_request_written_after_design')}",
                "canonical_promotion_approval_request_visible="
                f"{item.get('source_pack_canonical_promotion_approval_request_visible')}",
                "canonical_promotion_approval_request_result_ok="
                f"{item.get('source_pack_canonical_promotion_approval_request_result_ok')}",
                "canonical_promotion_approval_request_artifact_written="
                f"{item.get('source_pack_canonical_promotion_approval_request_artifact_written')}",
                "canonical_promotion_approval_request_paths_exist="
                f"{item.get('source_pack_canonical_promotion_approval_request_written_paths_exist')}",
                "canonical_promotion_decision_readiness_visible="
                f"{item.get('source_pack_canonical_promotion_decision_readiness_visible')}",
                "canonical_promotion_decision_readiness_result_ok="
                f"{item.get('source_pack_canonical_promotion_decision_readiness_result_ok')}",
                "canonical_promotion_decision_readiness_request_verified="
                f"{item.get('source_pack_canonical_promotion_decision_readiness_request_verified')}",
                "canonical_promotion_decision_readiness_decision_writer_ready="
                f"{item.get('source_pack_canonical_promotion_decision_readiness_decision_writer_ready')}",
                "canonical_promotion_executor_visible="
                f"{item.get('source_pack_canonical_promotion_executor_visible')}",
                "canonical_promotion_executor_result_ok="
                f"{item.get('source_pack_canonical_promotion_executor_result_ok')}",
                "canonical_promotion_marker_written="
                f"{item.get('source_pack_canonical_promotion_marker_written')}",
                "canonical_promotion_note_written="
                f"{item.get('source_pack_canonical_promotion_note_written')}",
                "canonical_promotion_index_written="
                f"{item.get('source_pack_canonical_promotion_index_written')}",
                "canonical_promotion_artifact_written="
                f"{item.get('source_pack_canonical_promotion_artifact_written')}",
                "canonical_promotion_written_paths_exist="
                f"{item.get('source_pack_canonical_promotion_written_paths_exist')}",
                "canonical_promotion_graph_mutation_after_executor="
                f"{item.get('source_pack_canonical_promotion_graph_mutation_after_executor')}",
                "canonical_promotion_provider_call_after_executor="
                f"{item.get('source_pack_canonical_promotion_provider_call_after_executor')}",
                "canonical_promotion_external_send_after_executor="
                f"{item.get('source_pack_canonical_promotion_external_send_after_executor')}",
            ]
        )
        for item in report.get("screenshots", [])
    )
    blocker_lines = "\n".join(f"- {item}" for item in report.get("blockers", [])) or "- none"
    return "\n".join(
        [
            "# Capture Markdown Visual Quality Assurance",
            "",
            f"- Status: {report.get('status')}",
            f"- OK: {report.get('ok')}",
            f"- Surface: {report.get('surface')}",
            f"- Browser fallback: {report.get('browser_availability', {}).get('fallback_reason')}",
            "",
            "## Screenshots",
            "",
            screenshot_lines,
            "",
            "## Blockers",
            "",
            blocker_lines,
            "",
        ]
    )


def build_capture_markdown_visual_qa(
    vault_root: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    resolved_output = _resolve_output_dir(vault, output_dir)
    resolved_output.mkdir(parents=True, exist_ok=True)

    visual = _run_playwright_visual_qa(vault, resolved_output)
    screenshots = visual.get("screenshots") if isinstance(visual.get("screenshots"), list) else []
    missing_tokens = sorted(
        {
            token
            for screenshot in screenshots
            for token in (screenshot.get("missing_required_tokens") or [])
        }
    )
    blockers: list[str] = []
    if not screenshots:
        blockers.append("no_screenshots_captured")
    if {shot.get("viewport") for shot in screenshots} != {"desktop", "mobile"}:
        blockers.append("desktop_mobile_coverage_missing")
    if any(not shot.get("not_blank") for shot in screenshots):
        blockers.append("blank_or_tiny_screenshot")
    if any(not shot.get("policy_visible") for shot in screenshots):
        blockers.append("attachment_policy_not_visible")
    if any(not shot.get("delete_block_visible") for shot in screenshots):
        blockers.append("delete_block_not_visible")
    if any(not shot.get("review_state_visible") for shot in screenshots):
        blockers.append("review_state_not_visible")
    if any(not shot.get("source_pack_approval_preview_visible") for shot in screenshots):
        blockers.append("source_pack_approval_preview_not_visible")
    if any(not shot.get("source_pack_request_digest_visible") for shot in screenshots):
        blockers.append("source_pack_request_digest_not_visible")
    if any(not shot.get("source_pack_write_blocked_visible") for shot in screenshots):
        blockers.append("source_pack_write_block_not_visible")
    if any(not shot.get("source_pack_write_completed_visible") for shot in screenshots):
        blockers.append("source_pack_write_completed_not_visible")
    if any(not shot.get("source_pack_write_result_ok") for shot in screenshots):
        blockers.append("source_pack_write_result_not_ok")
    if any(not shot.get("source_pack_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_written_paths_missing")
    if any(not shot.get("source_pack_aor_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_aor_readiness_not_visible")
    if any(not shot.get("source_pack_aor_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_readiness_result_not_ok")
    if any(not shot.get("source_pack_aor_dispatch_blocked_visible") for shot in screenshots):
        blockers.append("source_pack_aor_dispatch_block_not_visible")
    if any(not shot.get("source_pack_agent_bus_blocked_visible") for shot in screenshots):
        blockers.append("source_pack_agent_bus_block_not_visible")
    if any(not shot.get("source_pack_aor_ready_packet_digest_visible") for shot in screenshots):
        blockers.append("source_pack_aor_packet_digest_not_visible")
    if any(shot.get("source_pack_aor_dispatch_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_aor_dispatch_not_blocked")
    if any(shot.get("source_pack_agent_bus_task_written") is not False for shot in screenshots):
        blockers.append("source_pack_agent_bus_task_written")
    if any(not shot.get("source_pack_aor_approval_design_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_design_not_visible")
    if any(not shot.get("source_pack_aor_approval_design_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_approval_design_result_not_ok")
    if any(not shot.get("source_pack_aor_approval_digest_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_digest_not_visible")
    if any(not shot.get("source_pack_aor_future_approval_visible") for shot in screenshots):
        blockers.append("source_pack_aor_future_approval_not_visible")
    if any(not shot.get("source_pack_aor_approval_artifact_not_written_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_artifact_not_written_not_visible")
    if any(shot.get("source_pack_aor_approval_design_request_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_design_request_written")
    if any(shot.get("source_pack_aor_approval_design_artifact_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_design_artifact_written")
    if any(shot.get("source_pack_aor_approval_design_consumed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_design_consumed")
    if any(not shot.get("source_pack_aor_approval_request_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_request_not_visible")
    if any(not shot.get("source_pack_aor_approval_request_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_approval_request_result_not_ok")
    if any(shot.get("source_pack_aor_approval_request_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_request_not_written")
    if any(shot.get("source_pack_aor_approval_request_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_request_artifact_not_written")
    if any(not shot.get("source_pack_aor_approval_request_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_approval_request_written_paths_missing")
    if any(shot.get("source_pack_aor_approval_request_approval_decision_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_written")
    if any(shot.get("source_pack_aor_approval_request_consumed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumed")
    if any(shot.get("source_pack_aor_approval_request_agent_bus_task_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_agent_bus_task_written")
    if any(shot.get("source_pack_aor_approval_request_aor_dispatch_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_dispatch_not_blocked")
    if any(not shot.get("source_pack_aor_approval_consumption_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_readiness_not_visible")
    if any(not shot.get("source_pack_aor_approval_consumption_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_readiness_result_not_ok")
    if any(shot.get("source_pack_aor_approval_consumption_request_verified") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_request_not_verified")
    if any(shot.get("source_pack_aor_approval_consumption_decision_writer_ready") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_decision_writer_not_ready")
    if any(shot.get("source_pack_aor_approval_consumption_decision_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_decision_written")
    if any(shot.get("source_pack_aor_approval_consumption_consumed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_consumed")
    if any(shot.get("source_pack_aor_approval_consumption_marker_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_marker_written")
    if any(shot.get("source_pack_aor_approval_consumption_agent_bus_task_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_agent_bus_task_written")
    if any(shot.get("source_pack_aor_approval_consumption_aor_dispatch_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_dispatch_not_blocked")
    if any(shot.get("source_pack_aor_approval_consumption_future_marker_exists") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_future_marker_exists")
    if any(not shot.get("source_pack_aor_approval_decision_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_not_visible")
    if any(not shot.get("source_pack_aor_approval_decision_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_result_not_ok")
    if any(shot.get("source_pack_aor_approval_decision_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_not_written")
    if any(shot.get("source_pack_aor_approval_decision_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_artifact_not_written")
    if any(not shot.get("source_pack_aor_approval_decision_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_written_paths_missing")
    if any(shot.get("source_pack_aor_approval_decision_consumed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_consumed")
    if any(shot.get("source_pack_aor_approval_decision_marker_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_marker_written")
    if any(shot.get("source_pack_aor_approval_decision_agent_bus_task_written") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_agent_bus_task_written")
    if any(shot.get("source_pack_aor_approval_decision_aor_dispatch_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_decision_dispatch_not_blocked")
    if any(not shot.get("source_pack_aor_approval_consumption_preview_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_preview_not_visible")
    if any(not shot.get("source_pack_aor_approval_consumption_visible") for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_not_visible")
    if any(not shot.get("source_pack_aor_approval_consumption_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_result_not_ok")
    if any(shot.get("source_pack_aor_approval_consumption_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_not_written")
    if any(shot.get("source_pack_aor_approval_consumption_decision_consumed") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_decision_not_consumed")
    if any(shot.get("source_pack_aor_approval_consumption_marker_reserved") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_marker_not_reserved")
    if any(shot.get("source_pack_aor_approval_consumption_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_artifact_not_written")
    if any(shot.get("source_pack_aor_approval_consumption_ready_for_agent_bus_task_writer") is not True for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_not_agent_bus_ready")
    if any(not shot.get("source_pack_aor_approval_consumption_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_written_paths_missing")
    if any(shot.get("source_pack_aor_approval_consumption_agent_bus_task_written_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_agent_bus_task_written_after_consumption")
    if any(shot.get("source_pack_aor_approval_consumption_aor_dispatch_allowed_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_aor_approval_consumption_dispatch_not_blocked_after_consumption")
    if any(not shot.get("source_pack_aor_agent_bus_task_preview_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_preview_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_task_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_task_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_task_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_marker_not_written")
    if any(shot.get("source_pack_aor_agent_bus_task_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_not_written")
    if any(shot.get("source_pack_aor_agent_bus_task_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_artifact_not_written")
    if any(not shot.get("source_pack_aor_agent_bus_task_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_written_paths_missing")
    if any(not shot.get("source_pack_aor_agent_bus_task_db_exists") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_db_missing")
    if any(shot.get("source_pack_aor_agent_bus_task_claimed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claimed")
    if any(shot.get("source_pack_aor_agent_bus_runtime_process_started") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_runtime_process_started")
    if any(shot.get("source_pack_aor_agent_bus_aor_dispatch_allowed_after_task_write") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_dispatch_not_blocked_after_task_write")
    if any(shot.get("source_pack_aor_agent_bus_aor_dispatch_performed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_dispatch_performed")
    if any(not shot.get("source_pack_aor_agent_bus_task_claim_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_readiness_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_task_claim_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_readiness_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_task_artifact_verified") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_artifact_not_verified")
    if any(shot.get("source_pack_aor_agent_bus_task_claimable") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_not_claimable")
    if any(shot.get("source_pack_aor_agent_bus_task_claim_preflight_ready") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_preflight_not_ready")
    if any(shot.get("source_pack_aor_agent_bus_route_configured") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_route_not_configured")
    if any(shot.get("source_pack_aor_agent_bus_task_claim_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_allowed_in_readiness_pass")
    if any(shot.get("source_pack_aor_agent_bus_task_claim_readiness_aor_dispatch_allowed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_dispatch_allowed_in_claim_readiness_pass")
    if any(not shot.get("source_pack_aor_agent_bus_task_claim_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_task_claim_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_task_claim_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_marker_not_written")
    if any(shot.get("source_pack_aor_agent_bus_task_claimed_after_claim") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_not_claimed_after_claim")
    if any(shot.get("source_pack_aor_agent_bus_task_claim_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_artifact_not_written")
    if any(not shot.get("source_pack_aor_agent_bus_task_claim_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_claim_written_paths_missing")
    if any(shot.get("source_pack_aor_agent_bus_task_executed_after_claim") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_executed_after_claim")
    if any(shot.get("source_pack_aor_agent_bus_runtime_process_started_after_claim") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_runtime_process_started_after_claim")
    if any(shot.get("source_pack_aor_agent_bus_aor_dispatch_allowed_after_claim") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_dispatch_allowed_after_claim")
    if any(not shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claimed_task_dry_run_readiness_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claimed_task_dry_run_readiness_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_claimed_task_ready") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claimed_task_not_ready_for_dry_run")
    if any(shot.get("source_pack_aor_agent_bus_claim_artifact_verified_after_claim") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claim_artifact_not_verified_after_claim")
    if any(shot.get("source_pack_aor_agent_bus_aor_contracts_verified") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_contracts_not_verified")
    if any(shot.get("source_pack_aor_agent_bus_dry_run_packet_ready") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_dry_run_packet_not_ready")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_allowed_in_readiness_pass")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_performed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_performed_in_readiness_pass")
    if any(not shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claimed_task_dry_run_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claimed_task_dry_run_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_marker_not_written")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_artifact_not_written")
    if any(not shot.get("source_pack_aor_agent_bus_aor_dry_run_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_written_paths_missing")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_result_status") != "dry_run_ok" for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_result_stage") != "dry_run_exit" for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_stage_not_dry_run_exit")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_osril_session_created") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_osril_session_not_created")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_osril_event_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_osril_event_not_written")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_aor_audit_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_aor_audit_not_written")
    if any(shot.get("source_pack_aor_agent_bus_aor_dry_run_source_pack_writeback_created") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dry_run_source_pack_writeback_created")
    if any(shot.get("source_pack_aor_agent_bus_task_executed_after_dry_run") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_executed_after_dry_run")
    if any(shot.get("source_pack_aor_agent_bus_task_status_updated_after_dry_run") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_status_updated_after_dry_run")
    if any(shot.get("source_pack_aor_agent_bus_runtime_process_started_after_dry_run") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_runtime_process_started_after_dry_run")
    if any(shot.get("source_pack_aor_agent_bus_aor_dispatch_performed_after_dry_run") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dispatch_performed_after_dry_run")
    if any(not shot.get("source_pack_aor_agent_bus_claimed_task_status_lifecycle_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claimed_task_status_lifecycle_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_claimed_task_status_lifecycle_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_claimed_task_status_lifecycle_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_status_lifecycle_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_status_lifecycle_marker_not_written")
    if any(shot.get("source_pack_aor_agent_bus_task_status_updated_after_status_lifecycle") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_status_not_updated_after_status_lifecycle")
    if any(shot.get("source_pack_aor_agent_bus_task_status_after_status_lifecycle") != "review" for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_status_after_status_lifecycle_not_review")
    if any(shot.get("source_pack_aor_agent_bus_task_review_requested_after_status_lifecycle") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_review_not_requested_after_status_lifecycle")
    if any(shot.get("source_pack_aor_agent_bus_status_lifecycle_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_status_lifecycle_artifact_not_written")
    if any(not shot.get("source_pack_aor_agent_bus_status_lifecycle_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_status_lifecycle_written_paths_missing")
    if any(shot.get("source_pack_aor_agent_bus_task_executed_after_status_lifecycle") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_executed_after_status_lifecycle")
    if any(shot.get("source_pack_aor_agent_bus_runtime_process_started_after_status_lifecycle") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_runtime_process_started_after_status_lifecycle")
    if any(shot.get("source_pack_aor_agent_bus_aor_dispatch_performed_after_status_lifecycle") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_aor_dispatch_performed_after_status_lifecycle")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_readiness_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_readiness_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_readiness_ready") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_readiness_not_ready")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_ready_for_executor") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_not_ready_for_executor")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_review_event_verified") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_review_event_not_verified")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_future_packet_ready") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_future_packet_not_ready")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_future_packet_digest_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_future_packet_digest_not_visible")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_allowed_now")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_performed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_performed")
    if any(shot.get("source_pack_aor_agent_bus_task_body_executed_after_full_dispatch_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_body_executed_after_full_dispatch_readiness")
    if any(shot.get("source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch_readiness")
    if any(shot.get("source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch_readiness")
    if any(shot.get("source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch_readiness")
    if any(shot.get("source_pack_aor_agent_bus_graph_mutation_after_full_dispatch_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_graph_mutation_after_full_dispatch_readiness")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_executor_preview_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_executor_preview_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_executor_preview_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_executor_preview_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_executor_preview_ready") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_executor_preview_not_ready")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_executor_statement_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_executor_statement_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_visible") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_not_visible")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_result_ok") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_result_not_ok")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_marker_not_written")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_performed") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_readiness_performed")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_artifact_not_written")
    if any(not shot.get("source_pack_aor_agent_bus_full_dispatch_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_written_paths_missing")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_aor_result_status") != "success" for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_aor_result_not_success")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_osril_session_created") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_osril_session_not_created")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_osril_event_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_osril_event_not_written")
    if any(shot.get("source_pack_aor_agent_bus_full_dispatch_aor_audit_written") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_full_dispatch_aor_audit_not_written")
    if any(shot.get("source_pack_aor_agent_bus_source_pack_writeback_created") is not True for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_source_pack_writeback_not_created")
    if any(shot.get("source_pack_aor_agent_bus_task_body_executed_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_body_executed_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_task_executed_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_executed_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_task_status_updated_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_task_status_updated_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_watch_loop_started_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_watch_loop_started_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_graph_mutation_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_graph_mutation_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_provider_call_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_provider_call_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_external_send_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_external_send_after_full_dispatch")
    if any(shot.get("source_pack_aor_agent_bus_attachment_delete_after_full_dispatch") is not False for shot in screenshots):
        blockers.append("source_pack_aor_agent_bus_attachment_delete_after_full_dispatch")
    if any(not shot.get("source_pack_sic_ingestion_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_readiness_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_readiness_result_not_ok")
    if any(shot.get("source_pack_sic_ingestion_writeback_verified") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_writeback_not_verified")
    if any(shot.get("source_pack_sic_ingestion_contracts_verified") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_contracts_not_verified")
    if any(shot.get("source_pack_sic_ingestion_future_packet_ready") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_future_packet_not_ready")
    if any(shot.get("source_pack_sic_ingestion_ready_for_approval_design") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_not_ready_for_approval_design")
    if any(shot.get("source_pack_sic_ingestion_ready_for_executor") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_executor_unexpectedly_ready")
    if any(shot.get("source_pack_sic_ingestion_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_allowed_now")
    if any(shot.get("source_pack_sic_ingestion_performed") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_performed")
    if any(shot.get("source_pack_sic_source_package_written") is not False for shot in screenshots):
        blockers.append("source_pack_sic_source_package_written")
    if any(shot.get("source_pack_sic_workspace_membership_written") is not False for shot in screenshots):
        blockers.append("source_pack_sic_workspace_membership_written")
    if any(shot.get("source_pack_sic_graph_mutation") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation")
    if any(shot.get("source_pack_sic_canonical_mutation") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation")
    if any(shot.get("source_pack_sic_provider_call") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call")
    if any(shot.get("source_pack_sic_external_send") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send")
    if any(not shot.get("source_pack_sic_ingestion_approval_design_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_design_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_approval_design_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_design_result_not_ok")
    if any(shot.get("source_pack_sic_ingestion_approval_packet_ready") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_packet_not_ready")
    if any(shot.get("source_pack_sic_ingestion_approval_request_written") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_request_written")
    if any(shot.get("source_pack_sic_ingestion_executor_ready_after_approval_design") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_executor_ready_after_approval_design")
    if any(shot.get("source_pack_sic_ingestion_allowed_after_approval_design") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_allowed_after_approval_design")
    if any(shot.get("source_pack_sic_ingestion_performed_after_approval_design") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_performed_after_approval_design")
    if any(shot.get("source_pack_sic_graph_mutation_after_approval_design") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation_after_approval_design")
    if any(shot.get("source_pack_sic_canonical_mutation_after_approval_design") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation_after_approval_design")
    if any(shot.get("source_pack_sic_provider_call_after_approval_design") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call_after_approval_design")
    if any(shot.get("source_pack_sic_external_send_after_approval_design") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send_after_approval_design")
    if any(not shot.get("source_pack_sic_ingestion_approval_request_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_request_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_approval_request_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_request_result_not_ok")
    if any(shot.get("source_pack_sic_ingestion_approval_request_written_after_request") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_request_not_written")
    if any(shot.get("source_pack_sic_ingestion_approval_artifact_written_after_request") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_artifact_not_written")
    if any(not shot.get("source_pack_sic_ingestion_approval_request_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_request_written_paths_missing")
    if any(shot.get("source_pack_sic_ingestion_approval_decision_written_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_written_after_request")
    if any(shot.get("source_pack_sic_ingestion_approval_consumed_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumed_after_request")
    if any(not shot.get("source_pack_sic_ingestion_approval_decision_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_readiness_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_approval_decision_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_readiness_result_not_ok")
    if any(shot.get("source_pack_sic_ingestion_approval_request_verified_for_decision") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_request_not_verified_for_decision")
    if any(shot.get("source_pack_sic_ingestion_approval_decision_writer_ready_after_readiness") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_writer_not_ready_after_readiness")
    if any(shot.get("source_pack_sic_ingestion_approval_consumed_after_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumed_after_readiness")
    if any(not shot.get("source_pack_sic_ingestion_approval_decision_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_approval_decision_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_result_not_ok")
    if any(shot.get("source_pack_sic_ingestion_approval_decision_written_after_decision") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_not_written")
    if any(not shot.get("source_pack_sic_ingestion_approval_decision_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_written_paths_missing")
    if any(shot.get("source_pack_sic_ingestion_approval_consumed_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumed_after_decision")
    if any(shot.get("source_pack_sic_ingestion_approval_consumption_ready_after_decision") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumption_not_ready_after_decision")
    if any(shot.get("source_pack_sic_ingestion_executor_ready_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_executor_ready_after_decision")
    if any(shot.get("source_pack_sic_ingestion_allowed_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_allowed_after_decision")
    if any(shot.get("source_pack_sic_ingestion_performed_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_performed_after_decision")
    if any(shot.get("source_pack_sic_source_package_written_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_source_package_written_after_decision")
    if any(shot.get("source_pack_sic_workspace_membership_written_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_workspace_membership_written_after_decision")
    if any(shot.get("source_pack_sic_graph_mutation_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation_after_decision")
    if any(shot.get("source_pack_sic_canonical_mutation_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation_after_decision")
    if any(shot.get("source_pack_sic_provider_call_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call_after_decision")
    if any(shot.get("source_pack_sic_external_send_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send_after_decision")
    if any(shot.get("source_pack_sic_attachment_delete_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_sic_attachment_delete_after_decision")
    if any(not shot.get("source_pack_sic_ingestion_approval_consumption_preview_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumption_preview_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_approval_consumption_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumption_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_approval_consumption_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumption_result_not_ok")
    if any(shot.get("source_pack_sic_ingestion_approval_consumed_after_consumption") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_not_consumed_after_consumption")
    if any(shot.get("source_pack_sic_ingestion_approval_decision_consumed_after_consumption") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_decision_not_consumed_after_consumption")
    if any(shot.get("source_pack_sic_ingestion_approval_consumption_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumption_marker_not_written")
    if any(shot.get("source_pack_sic_ingestion_approval_consumption_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumption_artifact_not_written")
    if any(not shot.get("source_pack_sic_ingestion_approval_consumption_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_approval_consumption_written_paths_missing")
    if any(shot.get("source_pack_sic_ingestion_executor_ready_after_consumption") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_executor_not_ready_after_consumption")
    if any(shot.get("source_pack_sic_ingestion_allowed_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_allowed_after_consumption")
    if any(shot.get("source_pack_sic_ingestion_performed_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_performed_after_consumption")
    if any(shot.get("source_pack_sic_source_package_written_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_source_package_written_after_consumption")
    if any(shot.get("source_pack_sic_workspace_membership_written_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_workspace_membership_written_after_consumption")
    if any(shot.get("source_pack_sic_graph_mutation_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation_after_consumption")
    if any(shot.get("source_pack_sic_canonical_mutation_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation_after_consumption")
    if any(shot.get("source_pack_sic_provider_call_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call_after_consumption")
    if any(shot.get("source_pack_sic_external_send_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send_after_consumption")
    if any(shot.get("source_pack_sic_attachment_delete_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_sic_attachment_delete_after_consumption")
    if any(not shot.get("source_pack_sic_ingestion_preview_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_preview_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_preview_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_preview_result_not_ok")
    if any(shot.get("source_pack_sic_ingestion_preview_ready") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_preview_not_ready")
    if any(shot.get("source_pack_sic_ingestion_digest_ready") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_digest_missing")
    if any(not shot.get("source_pack_sic_ingestion_visible") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_not_visible")
    if any(not shot.get("source_pack_sic_ingestion_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_result_not_ok")
    if any(not shot.get("source_pack_sic_ingestion_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_written_paths_missing")
    if any(shot.get("source_pack_sic_ingestion_performed_after_ingestion") is not True for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_not_performed_after_ingestion")
    if any(shot.get("source_pack_sic_workspace_written_after_ingestion") is not True for shot in screenshots):
        blockers.append("source_pack_sic_workspace_not_written_after_ingestion")
    if any(shot.get("source_pack_sic_source_package_written_after_ingestion") is not True for shot in screenshots):
        blockers.append("source_pack_sic_source_package_not_written_after_ingestion")
    if any(shot.get("source_pack_sic_workspace_membership_written_after_ingestion") is not True for shot in screenshots):
        blockers.append("source_pack_sic_workspace_membership_not_written_after_ingestion")
    if any(shot.get("source_pack_sic_graph_mutation_after_ingestion") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation_after_ingestion")
    if any(shot.get("source_pack_sic_canonical_mutation_after_ingestion") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation_after_ingestion")
    if any(shot.get("source_pack_sic_provider_call_after_ingestion") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call_after_ingestion")
    if any(shot.get("source_pack_sic_external_send_after_ingestion") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send_after_ingestion")
    if any(shot.get("source_pack_sic_attachment_delete_after_ingestion") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_sic_attachment_delete_after_ingestion")
    if any(not shot.get("source_pack_sic_graph_indexing_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_readiness_not_visible")
    if any(not shot.get("source_pack_sic_graph_indexing_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_readiness_result_not_ok")
    if any(shot.get("source_pack_sic_graph_indexing_readiness_preview_ready") is not True for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_readiness_preview_not_ready")
    if any(shot.get("source_pack_sic_graph_indexing_readiness_packet_digest_ready") is not True for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_readiness_packet_digest_missing")
    if any((shot.get("source_pack_sic_graph_indexing_candidate_node_count") or 0) < 4 for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_candidate_node_count_too_low")
    if any((shot.get("source_pack_sic_graph_indexing_candidate_edge_count") or 0) < 3 for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_candidate_edge_count_too_low")
    if any(shot.get("source_pack_sic_graph_mutation_after_graph_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation_after_graph_readiness")
    if any(shot.get("source_pack_sic_graph_snapshot_written_after_graph_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_snapshot_written_after_graph_readiness")
    if any(shot.get("source_pack_sic_canonical_mutation_after_graph_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation_after_graph_readiness")
    if any(shot.get("source_pack_sic_provider_call_after_graph_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call_after_graph_readiness")
    if any(shot.get("source_pack_sic_external_send_after_graph_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send_after_graph_readiness")
    if any(shot.get("source_pack_sic_attachment_delete_after_graph_readiness") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_sic_attachment_delete_after_graph_readiness")
    if any(not shot.get("source_pack_sic_graph_indexing_preview_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_preview_result_not_ok")
    if any(shot.get("source_pack_sic_graph_indexing_preview_ready") is not True for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_preview_not_ready")
    if any(shot.get("source_pack_sic_graph_indexing_write_allowed_preview") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_write_allowed_in_preview")
    if any(not shot.get("source_pack_sic_graph_indexing_visible") for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_not_visible")
    if any(not shot.get("source_pack_sic_graph_indexing_result_ok") for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_result_not_ok")
    if any(not shot.get("source_pack_sic_graph_indexing_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_sic_graph_indexing_written_paths_missing")
    if any(shot.get("source_pack_sic_graph_mutation_after_graph_indexing") is not True for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation_after_graph_indexing_not_true")
    if any(shot.get("source_pack_sic_graph_snapshot_written_after_graph_indexing") is not True for shot in screenshots):
        blockers.append("source_pack_sic_graph_snapshot_written_after_graph_indexing_not_true")
    if any(shot.get("source_pack_sic_graph_store_manifest_written_after_graph_indexing") is not True for shot in screenshots):
        blockers.append("source_pack_sic_graph_store_manifest_written_after_graph_indexing_not_true")
    if any(shot.get("source_pack_sic_graph_current_pointer_written_after_graph_indexing") is not True for shot in screenshots):
        blockers.append("source_pack_sic_graph_current_pointer_written_after_graph_indexing_not_true")
    if any(shot.get("source_pack_sic_canonical_mutation_after_graph_indexing") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation_after_graph_indexing")
    if any(shot.get("source_pack_sic_provider_call_after_graph_indexing") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call_after_graph_indexing")
    if any(shot.get("source_pack_sic_external_send_after_graph_indexing") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send_after_graph_indexing")
    if any(shot.get("source_pack_sic_attachment_delete_after_graph_indexing") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_sic_attachment_delete_after_graph_indexing")
    if any(not shot.get("source_pack_canonical_promotion_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_readiness_not_visible")
    if any(not shot.get("source_pack_canonical_promotion_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_readiness_result_not_ok")
    if any(shot.get("source_pack_canonical_promotion_readiness_preview_ready") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_readiness_preview_not_ready")
    if any(shot.get("source_pack_canonical_promotion_candidate_digest_ready") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_candidate_digest_missing")
    if any((shot.get("source_pack_canonical_promotion_target_count") or 0) < 2 for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_target_count_too_low")
    if any(shot.get("source_pack_canonical_promotion_graph_store_current_pointer_verified") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_graph_store_current_pointer_not_verified")
    if any(shot.get("source_pack_canonical_promotion_canonical_allowed_now") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_allowed_now")
    if any(shot.get("source_pack_canonical_promotion_canonical_mutation_performed") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_canonical_mutation_performed")
    if any(shot.get("source_pack_canonical_promotion_knowledge_promotion_performed") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_knowledge_promotion_performed")
    if any(shot.get("source_pack_canonical_promotion_provider_call_performed") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_provider_call_performed")
    if any(shot.get("source_pack_canonical_promotion_external_send_performed") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_external_send_performed")
    if any(shot.get("source_pack_canonical_promotion_attachment_delete_performed") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_attachment_delete_performed")
    if any(not shot.get("source_pack_canonical_promotion_approval_design_visible") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_design_not_visible")
    if any(not shot.get("source_pack_canonical_promotion_approval_design_result_ok") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_design_result_not_ok")
    if any(shot.get("source_pack_canonical_promotion_approval_packet_preview_ready") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_packet_preview_not_ready")
    if any(shot.get("source_pack_canonical_promotion_approval_request_digest_ready") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_request_digest_missing")
    if any(shot.get("source_pack_canonical_promotion_approval_request_written_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_request_written_after_design")
    if any(shot.get("source_pack_canonical_promotion_executor_ready_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_executor_ready_after_design")
    if any(shot.get("source_pack_canonical_promotion_allowed_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_allowed_after_design")
    if any(shot.get("source_pack_canonical_promotion_performed_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_performed_after_design")
    if any(shot.get("source_pack_canonical_promotion_note_written_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_note_written_after_design")
    if any(shot.get("source_pack_canonical_promotion_index_written_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_index_written_after_design")
    if any(shot.get("source_pack_canonical_promotion_provider_call_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_provider_call_after_design")
    if any(shot.get("source_pack_canonical_promotion_external_send_after_design") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_external_send_after_design")
    if any(shot.get("source_pack_canonical_promotion_attachment_delete_after_design") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_attachment_delete_after_design")
    if any(not shot.get("source_pack_canonical_promotion_approval_request_visible") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_request_not_visible")
    if any(not shot.get("source_pack_canonical_promotion_approval_request_result_ok") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_request_result_not_ok")
    if any(shot.get("source_pack_canonical_promotion_approval_request_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_request_not_written")
    if any(shot.get("source_pack_canonical_promotion_approval_request_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_request_artifact_not_written")
    if any(not shot.get("source_pack_canonical_promotion_approval_request_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_request_written_paths_missing")
    if any(shot.get("source_pack_canonical_promotion_ready_for_decision_after_request") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_not_ready_for_decision_after_request")
    if any(shot.get("source_pack_canonical_promotion_executor_ready_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_executor_ready_after_request")
    if any(shot.get("source_pack_canonical_promotion_allowed_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_allowed_after_request")
    if any(shot.get("source_pack_canonical_promotion_performed_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_performed_after_request")
    if any(shot.get("source_pack_canonical_promotion_note_written_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_note_written_after_request")
    if any(shot.get("source_pack_canonical_promotion_index_written_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_index_written_after_request")
    if any(shot.get("source_pack_canonical_promotion_provider_call_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_provider_call_after_request")
    if any(shot.get("source_pack_canonical_promotion_external_send_after_request") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_external_send_after_request")
    if any(shot.get("source_pack_canonical_promotion_attachment_delete_after_request") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_attachment_delete_after_request")
    if any(not shot.get("source_pack_canonical_promotion_decision_readiness_visible") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_not_visible")
    if any(not shot.get("source_pack_canonical_promotion_decision_readiness_result_ok") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_result_not_ok")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_request_verified") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_request_not_verified")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_pending") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_request_not_pending")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_decision_writer_ready") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_decision_writer_not_ready")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_decision_ready") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_decision_not_ready")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_decision_option_count") != 2 for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_decision_options_missing")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_consumption_ready") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_consumption_ready")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_executor_ready") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_executor_ready")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_decision_written") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_decision_written")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_approval_consumed") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_approval_consumed")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_marker_written") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_marker_written")
    if any(shot.get("source_pack_canonical_promotion_decision_readiness_future_marker_exists") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_decision_readiness_future_marker_exists")
    if any(shot.get("source_pack_canonical_promotion_allowed_after_decision_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_allowed_after_decision_readiness")
    if any(shot.get("source_pack_canonical_promotion_performed_after_decision_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_performed_after_decision_readiness")
    if any(shot.get("source_pack_canonical_promotion_note_written_after_decision_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_note_written_after_decision_readiness")
    if any(shot.get("source_pack_canonical_promotion_index_written_after_decision_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_index_written_after_decision_readiness")
    if any(shot.get("source_pack_canonical_promotion_graph_mutation_after_decision_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_graph_mutation_after_decision_readiness")
    if any(shot.get("source_pack_canonical_promotion_provider_call_after_decision_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_provider_call_after_decision_readiness")
    if any(shot.get("source_pack_canonical_promotion_external_send_after_decision_readiness") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_external_send_after_decision_readiness")
    if any(shot.get("source_pack_canonical_promotion_attachment_delete_after_decision_readiness") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_attachment_delete_after_decision_readiness")
    if any(not shot.get("source_pack_canonical_promotion_approval_decision_visible") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_decision_not_visible")
    if any(not shot.get("source_pack_canonical_promotion_approval_decision_result_ok") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_decision_result_not_ok")
    if any(shot.get("source_pack_canonical_promotion_approval_decision_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_decision_not_written")
    if any(shot.get("source_pack_canonical_promotion_approval_decision_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_decision_artifact_not_written")
    if any(not shot.get("source_pack_canonical_promotion_approval_decision_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_decision_written_paths_missing")
    if any(shot.get("source_pack_canonical_promotion_approval_consumption_ready_after_decision") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_consumption_not_ready_after_decision")
    if any(shot.get("source_pack_canonical_promotion_executor_ready_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_executor_ready_after_decision")
    if any(shot.get("source_pack_canonical_promotion_approval_consumed_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_consumed_after_decision")
    if any(shot.get("source_pack_canonical_promotion_marker_written_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_marker_written_after_decision")
    if any(shot.get("source_pack_canonical_promotion_allowed_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_allowed_after_decision")
    if any(shot.get("source_pack_canonical_promotion_performed_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_performed_after_decision")
    if any(shot.get("source_pack_canonical_promotion_note_written_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_note_written_after_decision")
    if any(shot.get("source_pack_canonical_promotion_index_written_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_index_written_after_decision")
    if any(shot.get("source_pack_canonical_promotion_graph_mutation_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_graph_mutation_after_decision")
    if any(shot.get("source_pack_canonical_promotion_provider_call_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_provider_call_after_decision")
    if any(shot.get("source_pack_canonical_promotion_external_send_after_decision") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_external_send_after_decision")
    if any(shot.get("source_pack_canonical_promotion_attachment_delete_after_decision") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_attachment_delete_after_decision")
    if any(not shot.get("source_pack_canonical_promotion_approval_consumption_visible") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_consumption_not_visible")
    if any(not shot.get("source_pack_canonical_promotion_approval_consumption_result_ok") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_consumption_result_not_ok")
    if any(shot.get("source_pack_canonical_promotion_approval_consumed") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_not_consumed")
    if any(shot.get("source_pack_canonical_promotion_approval_consumption_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_consumption_artifact_not_written")
    if any(shot.get("source_pack_canonical_promotion_approval_consumption_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_consumption_marker_not_written")
    if any(not shot.get("source_pack_canonical_promotion_approval_consumption_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_approval_consumption_written_paths_missing")
    if any(shot.get("source_pack_canonical_promotion_executor_ready_after_consumption") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_executor_not_ready_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_allowed_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_allowed_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_performed_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_performed_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_note_written_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_note_written_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_index_written_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_index_written_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_graph_mutation_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_graph_mutation_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_provider_call_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_provider_call_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_external_send_after_consumption") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_external_send_after_consumption")
    if any(shot.get("source_pack_canonical_promotion_attachment_delete_after_consumption") not in (False, None) for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_attachment_delete_after_consumption")
    if any(not shot.get("source_pack_canonical_promotion_executor_visible") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_executor_not_visible")
    if any(not shot.get("source_pack_canonical_promotion_executor_result_ok") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_executor_result_not_ok")
    if any(shot.get("source_pack_canonical_promotion_marker_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_marker_not_written")
    if any(shot.get("source_pack_canonical_promotion_note_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_note_not_written")
    if any(shot.get("source_pack_canonical_promotion_index_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_index_not_written")
    if any(shot.get("source_pack_canonical_promotion_artifact_written") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_artifact_not_written")
    if any(not shot.get("source_pack_canonical_promotion_written_paths_exist") for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_written_paths_missing")
    if any(shot.get("source_pack_canonical_promotion_canonical_mutation_after_executor") is not True for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_canonical_mutation_not_recorded")
    if any(shot.get("source_pack_canonical_promotion_graph_mutation_after_executor") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_graph_mutation_after_executor")
    if any(shot.get("source_pack_canonical_promotion_source_intelligence_core_rewrite_after_executor") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_source_intelligence_core_rewrite_after_executor")
    if any(shot.get("source_pack_canonical_promotion_provider_call_after_executor") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_provider_call_after_executor")
    if any(shot.get("source_pack_canonical_promotion_external_send_after_executor") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_external_send_after_executor")
    if any(shot.get("source_pack_canonical_promotion_attachment_delete_after_executor") is not False for shot in screenshots):
        blockers.append("source_pack_canonical_promotion_attachment_delete_after_executor")
    if any(shot.get("source_pack_sic_ingestion_executor_ready_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_executor_ready_after_approval_request")
    if any(shot.get("source_pack_sic_ingestion_allowed_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_allowed_after_approval_request")
    if any(shot.get("source_pack_sic_ingestion_performed_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_ingestion_performed_after_approval_request")
    if any(shot.get("source_pack_sic_source_package_written_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_source_package_written_after_approval_request")
    if any(shot.get("source_pack_sic_workspace_membership_written_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_workspace_membership_written_after_approval_request")
    if any(shot.get("source_pack_sic_graph_mutation_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_graph_mutation_after_approval_request")
    if any(shot.get("source_pack_sic_canonical_mutation_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_canonical_mutation_after_approval_request")
    if any(shot.get("source_pack_sic_provider_call_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_provider_call_after_approval_request")
    if any(shot.get("source_pack_sic_external_send_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_external_send_after_approval_request")
    if any(shot.get("source_pack_sic_attachment_delete_after_approval_request") is not False for shot in screenshots):
        blockers.append("source_pack_sic_attachment_delete_after_approval_request")
    if any(shot.get("disposition_policy_id") != "vcmi.attachment_disposition.v1" for shot in screenshots):
        blockers.append("attachment_disposition_policy_missing_from_sidecar")
    if any(shot.get("disposition_after_review") != "retain" for shot in screenshots):
        blockers.append("attachment_disposition_not_updated_after_review")
    if any(shot.get("runtime_delete_allowed") is not False for shot in screenshots):
        blockers.append("runtime_delete_not_blocked")
    if missing_tokens:
        blockers.extend(f"missing_required_token:{token}" for token in missing_tokens)
    if visual.get("console_errors_or_warnings"):
        blockers.append("console_errors_or_warnings_present")
    if visual.get("page_errors"):
        blockers.append("page_errors_present")

    report = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "schema_version": MODEL_VERSION,
        "pass_id": PASS_ID,
        "status": STATUS if not blockers else "BLOCKED / CAPTURE MARKDOWN STATIC STUDIO VISUAL QUALITY ASSURANCE FAILED",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "output_dir": _relative_to_vault(vault, resolved_output),
        "browser_availability": {
            "browser_plugin_listed": True,
            "browser_plugin_callable": False,
            "fallback_used": "playwright_sync_local_static_render",
            "fallback_reason": "Browser plugin is listed and node_repl js is exposed, but Browser setup returned `Browser is not available: iab`; the repo Playwright harness verifies the local file target with Python-backed pywebview API stubs and temporary fixture functions.",
        },
        "summary": {
            "desktop_and_mobile_checked": {shot.get("viewport") for shot in screenshots} == {"desktop", "mobile"},
            "attachment_policy_visible": bool(screenshots) and all(shot.get("policy_visible") for shot in screenshots),
            "review_state_visible": bool(screenshots) and all(shot.get("review_state_visible") for shot in screenshots),
            "source_pack_approval_preview_verified": bool(screenshots) and all(
                shot.get("source_pack_approval_preview_visible") for shot in screenshots
            ),
            "source_pack_request_digest_visible": bool(screenshots) and all(
                shot.get("source_pack_request_digest_visible") for shot in screenshots
            ),
            "source_pack_write_blocked": bool(screenshots) and all(
                shot.get("source_pack_write_blocked_visible") for shot in screenshots
            ),
            "source_pack_write_completed_verified": bool(screenshots) and all(
                shot.get("source_pack_write_completed_visible") and shot.get("source_pack_write_result_ok")
                for shot in screenshots
            ),
            "source_pack_written_paths_verified_before_fixture_cleanup": bool(screenshots) and all(
                shot.get("source_pack_written_paths_exist") for shot in screenshots
            ),
            "source_pack_aor_dispatch_readiness_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_readiness_visible") and shot.get("source_pack_aor_readiness_result_ok")
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_dispatch_blocked_visible")
                and shot.get("source_pack_aor_dispatch_allowed_now") is False
                for shot in screenshots
            ),
            "source_pack_agent_bus_dispatch_blocked": bool(screenshots) and all(
                shot.get("source_pack_agent_bus_blocked_visible")
                and shot.get("source_pack_agent_bus_task_written") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_approval_design_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_design_visible")
                and shot.get("source_pack_aor_approval_design_result_ok")
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_approval_request_written_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_request_visible")
                and shot.get("source_pack_aor_approval_request_result_ok")
                and shot.get("source_pack_aor_approval_request_written") is True
                and shot.get("source_pack_aor_approval_request_artifact_written") is True
                and shot.get("source_pack_aor_approval_request_written_paths_exist")
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_approval_decision_consumption_and_dispatch_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_request_approval_decision_written") is False
                and shot.get("source_pack_aor_approval_request_consumed") is False
                and shot.get("source_pack_aor_approval_request_agent_bus_task_written") is False
                and shot.get("source_pack_aor_approval_request_aor_dispatch_allowed_now") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_approval_consumption_readiness_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_consumption_readiness_visible")
                and shot.get("source_pack_aor_approval_consumption_readiness_result_ok")
                and shot.get("source_pack_aor_approval_consumption_request_verified") is True
                and shot.get("source_pack_aor_approval_consumption_decision_writer_ready") is True
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_approval_consumption_still_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_consumption_decision_written") is False
                and shot.get("source_pack_aor_approval_consumption_consumed") is False
                and shot.get("source_pack_aor_approval_consumption_marker_written") is False
                and shot.get("source_pack_aor_approval_consumption_agent_bus_task_written") is False
                and shot.get("source_pack_aor_approval_consumption_aor_dispatch_allowed_now") is False
                and shot.get("source_pack_aor_approval_consumption_future_marker_exists") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_approval_decision_written_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_decision_visible")
                and shot.get("source_pack_aor_approval_decision_result_ok")
                and shot.get("source_pack_aor_approval_decision_written") is True
                and shot.get("source_pack_aor_approval_decision_artifact_written") is True
                and shot.get("source_pack_aor_approval_decision_written_paths_exist")
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_after_decision_still_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_decision_consumed") is False
                and shot.get("source_pack_aor_approval_decision_marker_written") is False
                and shot.get("source_pack_aor_approval_decision_agent_bus_task_written") is False
                and shot.get("source_pack_aor_approval_decision_aor_dispatch_allowed_now") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_approval_consumption_written_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_consumption_preview_visible")
                and shot.get("source_pack_aor_approval_consumption_visible")
                and shot.get("source_pack_aor_approval_consumption_result_ok")
                and shot.get("source_pack_aor_approval_consumption_written") is True
                and shot.get("source_pack_aor_approval_consumption_decision_consumed") is True
                and shot.get("source_pack_aor_approval_consumption_marker_reserved") is True
                and shot.get("source_pack_aor_approval_consumption_artifact_written") is True
                and shot.get("source_pack_aor_approval_consumption_written_paths_exist")
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_after_consumption_agent_bus_ready_but_dispatch_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_approval_consumption_ready_for_agent_bus_task_writer") is True
                and shot.get("source_pack_aor_approval_consumption_agent_bus_task_written_after_consumption") is False
                and shot.get("source_pack_aor_approval_consumption_aor_dispatch_allowed_after_consumption") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_task_written_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_agent_bus_task_preview_visible")
                and shot.get("source_pack_aor_agent_bus_task_visible")
                and shot.get("source_pack_aor_agent_bus_task_result_ok")
                and shot.get("source_pack_aor_agent_bus_task_marker_written") is True
                and shot.get("source_pack_aor_agent_bus_task_written") is True
                and shot.get("source_pack_aor_agent_bus_task_artifact_written") is True
                and shot.get("source_pack_aor_agent_bus_task_written_paths_exist")
                and shot.get("source_pack_aor_agent_bus_task_db_exists")
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_task_open_unclaimed": bool(screenshots) and all(
                shot.get("source_pack_aor_agent_bus_task_claimed") is False
                and shot.get("source_pack_aor_agent_bus_runtime_process_started") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_after_agent_bus_task_still_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_agent_bus_aor_dispatch_allowed_after_task_write") is False
                and shot.get("source_pack_aor_agent_bus_aor_dispatch_performed") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_task_claim_readiness_verified": bool(screenshots) and all(
                shot.get("source_pack_aor_agent_bus_task_claim_readiness_visible")
                and shot.get("source_pack_aor_agent_bus_task_claim_readiness_result_ok")
                and shot.get("source_pack_aor_agent_bus_task_artifact_verified") is True
                and shot.get("source_pack_aor_agent_bus_task_claimable") is True
                and shot.get("source_pack_aor_agent_bus_task_claim_preflight_ready") is True
                and shot.get("source_pack_aor_agent_bus_route_configured") is True
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_after_claim_readiness_still_unclaimed_and_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_agent_bus_task_claim_allowed_now") is False
                and shot.get("source_pack_aor_agent_bus_task_claim_readiness_aor_dispatch_allowed") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_task_claimed_execution_blocked": bool(screenshots) and all(
                shot.get("source_pack_aor_agent_bus_task_claim_visible")
                and shot.get("source_pack_aor_agent_bus_task_claim_result_ok")
                and shot.get("source_pack_aor_agent_bus_task_claim_marker_written") is True
                and shot.get("source_pack_aor_agent_bus_task_claimed_after_claim") is True
                and shot.get("source_pack_aor_agent_bus_task_claim_artifact_written") is True
                and shot.get("source_pack_aor_agent_bus_task_claim_written_paths_exist")
                and shot.get("source_pack_aor_agent_bus_task_executed_after_claim") is False
                and shot.get("source_pack_aor_agent_bus_runtime_process_started_after_claim") is False
                and shot.get("source_pack_aor_agent_bus_aor_dispatch_allowed_after_claim") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness_verified": bool(screenshots)
            and all(
                shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_readiness_visible")
                and shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_readiness_result_ok")
                and shot.get("source_pack_aor_agent_bus_claimed_task_ready") is True
                and shot.get("source_pack_aor_agent_bus_claim_artifact_verified_after_claim") is True
                and shot.get("source_pack_aor_agent_bus_aor_contracts_verified") is True
                and shot.get("source_pack_aor_agent_bus_dry_run_packet_ready") is True
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_allowed_now") is False
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_performed") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor_verified": bool(screenshots)
            and all(
                shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_visible")
                and shot.get("source_pack_aor_agent_bus_claimed_task_dry_run_result_ok")
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_marker_written") is True
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_artifact_written") is True
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_written_paths_exist")
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_result_status") == "dry_run_ok"
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_result_stage") == "dry_run_exit"
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_osril_session_created") is True
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_osril_event_written") is True
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_aor_audit_written") is True
                and shot.get("source_pack_aor_agent_bus_aor_dry_run_source_pack_writeback_created") is False
                and shot.get("source_pack_aor_agent_bus_task_executed_after_dry_run") is False
                and shot.get("source_pack_aor_agent_bus_task_status_updated_after_dry_run") is False
                and shot.get("source_pack_aor_agent_bus_runtime_process_started_after_dry_run") is False
                and shot.get("source_pack_aor_agent_bus_aor_dispatch_performed_after_dry_run") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_claimed_task_status_lifecycle_verified": bool(screenshots)
            and all(
                shot.get("source_pack_aor_agent_bus_claimed_task_status_lifecycle_visible")
                and shot.get("source_pack_aor_agent_bus_claimed_task_status_lifecycle_result_ok")
                and shot.get("source_pack_aor_agent_bus_status_lifecycle_marker_written") is True
                and shot.get("source_pack_aor_agent_bus_task_status_updated_after_status_lifecycle") is True
                and shot.get("source_pack_aor_agent_bus_task_status_after_status_lifecycle") == "review"
                and shot.get("source_pack_aor_agent_bus_task_review_requested_after_status_lifecycle") is True
                and shot.get("source_pack_aor_agent_bus_status_lifecycle_artifact_written") is True
                and shot.get("source_pack_aor_agent_bus_status_lifecycle_written_paths_exist")
                and shot.get("source_pack_aor_agent_bus_task_executed_after_status_lifecycle") is False
                and shot.get("source_pack_aor_agent_bus_runtime_process_started_after_status_lifecycle") is False
                and shot.get("source_pack_aor_agent_bus_aor_dispatch_performed_after_status_lifecycle") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_full_dispatch_readiness_verified": bool(screenshots)
            and all(
                shot.get("source_pack_aor_agent_bus_full_dispatch_readiness_visible")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_readiness_result_ok")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_readiness_ready") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_ready_for_executor") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_review_event_verified") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_future_packet_ready") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_allowed_now") is False
                and shot.get("source_pack_aor_agent_bus_full_dispatch_performed") is False
                and shot.get("source_pack_aor_agent_bus_task_body_executed_after_full_dispatch_readiness") is False
                and shot.get("source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch_readiness") is False
                and shot.get("source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch_readiness") is False
                and shot.get("source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch_readiness") is False
                and shot.get("source_pack_aor_agent_bus_graph_mutation_after_full_dispatch_readiness") is False
                for shot in screenshots
            ),
            "source_pack_aor_dispatch_agent_bus_full_dispatch_executor_verified": bool(screenshots)
            and all(
                shot.get("source_pack_aor_agent_bus_full_dispatch_executor_preview_visible")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_executor_preview_result_ok")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_executor_preview_ready") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_executor_statement_visible")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_visible")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_result_ok")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_marker_written") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_artifact_written") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_written_paths_exist")
                and shot.get("source_pack_aor_agent_bus_full_dispatch_aor_result_status") == "success"
                and shot.get("source_pack_aor_agent_bus_full_dispatch_osril_session_created") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_osril_event_written") is True
                and shot.get("source_pack_aor_agent_bus_full_dispatch_aor_audit_written") is True
                and shot.get("source_pack_aor_agent_bus_source_pack_writeback_created") is True
                and shot.get("source_pack_aor_agent_bus_task_body_executed_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_task_executed_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_task_status_updated_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_runtime_process_started_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_watch_loop_started_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_sic_ingestion_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_canonical_mutation_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_graph_mutation_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_provider_call_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_external_send_after_full_dispatch") is False
                and shot.get("source_pack_aor_agent_bus_attachment_delete_after_full_dispatch") is False
                for shot in screenshots
            ),
            "source_pack_sic_ingestion_readiness_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_ingestion_readiness_visible")
                and shot.get("source_pack_sic_ingestion_readiness_result_ok")
                and shot.get("source_pack_sic_ingestion_writeback_verified") is True
                and shot.get("source_pack_sic_ingestion_contracts_verified") is True
                and shot.get("source_pack_sic_ingestion_future_packet_ready") is True
                and shot.get("source_pack_sic_ingestion_ready_for_approval_design") is True
                and shot.get("source_pack_sic_ingestion_ready_for_executor") is False
                and shot.get("source_pack_sic_ingestion_allowed_now") is False
                and shot.get("source_pack_sic_ingestion_performed") is False
                and shot.get("source_pack_sic_source_package_written") is False
                and shot.get("source_pack_sic_workspace_membership_written") is False
                and shot.get("source_pack_sic_graph_mutation") is False
                and shot.get("source_pack_sic_canonical_mutation") is False
                and shot.get("source_pack_sic_provider_call") is False
                and shot.get("source_pack_sic_external_send") is False
                for shot in screenshots
            ),
            "source_pack_sic_ingestion_approval_design_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_ingestion_approval_design_visible")
                and shot.get("source_pack_sic_ingestion_approval_design_result_ok")
                and shot.get("source_pack_sic_ingestion_approval_packet_ready") is True
                and shot.get("source_pack_sic_ingestion_approval_request_written") is False
                and shot.get("source_pack_sic_ingestion_executor_ready_after_approval_design") is False
                and shot.get("source_pack_sic_ingestion_allowed_after_approval_design") is False
                and shot.get("source_pack_sic_ingestion_performed_after_approval_design") is False
                and shot.get("source_pack_sic_graph_mutation_after_approval_design") is False
                and shot.get("source_pack_sic_canonical_mutation_after_approval_design") is False
                and shot.get("source_pack_sic_provider_call_after_approval_design") is False
                and shot.get("source_pack_sic_external_send_after_approval_design") is False
                for shot in screenshots
            ),
            "source_pack_sic_ingestion_approval_request_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_ingestion_approval_request_visible")
                and shot.get("source_pack_sic_ingestion_approval_request_result_ok")
                and shot.get("source_pack_sic_ingestion_approval_request_written_after_request") is True
                and shot.get("source_pack_sic_ingestion_approval_artifact_written_after_request") is True
                and shot.get("source_pack_sic_ingestion_approval_request_written_paths_exist")
                and shot.get("source_pack_sic_ingestion_approval_decision_written_after_request") is False
                and shot.get("source_pack_sic_ingestion_approval_consumed_after_request") is False
                and shot.get("source_pack_sic_ingestion_executor_ready_after_approval_request") is False
                and shot.get("source_pack_sic_ingestion_allowed_after_approval_request") is False
                and shot.get("source_pack_sic_ingestion_performed_after_approval_request") is False
                and shot.get("source_pack_sic_source_package_written_after_approval_request") is False
                and shot.get("source_pack_sic_workspace_membership_written_after_approval_request") is False
                and shot.get("source_pack_sic_graph_mutation_after_approval_request") is False
                and shot.get("source_pack_sic_canonical_mutation_after_approval_request") is False
                and shot.get("source_pack_sic_provider_call_after_approval_request") is False
                and shot.get("source_pack_sic_external_send_after_approval_request") is False
                and shot.get("source_pack_sic_attachment_delete_after_approval_request") is False
                for shot in screenshots
            ),
            "source_pack_sic_ingestion_approval_decision_readiness_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_ingestion_approval_decision_readiness_visible")
                and shot.get("source_pack_sic_ingestion_approval_decision_readiness_result_ok")
                and shot.get("source_pack_sic_ingestion_approval_request_verified_for_decision") is True
                and shot.get("source_pack_sic_ingestion_approval_decision_writer_ready_after_readiness") is True
                and shot.get("source_pack_sic_ingestion_approval_consumed_after_readiness") is False
                for shot in screenshots
            ),
            "source_pack_sic_ingestion_approval_decision_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_ingestion_approval_decision_visible")
                and shot.get("source_pack_sic_ingestion_approval_decision_result_ok")
                and shot.get("source_pack_sic_ingestion_approval_decision_written_after_decision") is True
                and shot.get("source_pack_sic_ingestion_approval_decision_written_paths_exist")
                and shot.get("source_pack_sic_ingestion_approval_consumed_after_decision") is False
                and shot.get("source_pack_sic_ingestion_approval_consumption_ready_after_decision") is True
                and shot.get("source_pack_sic_ingestion_executor_ready_after_decision") is False
                and shot.get("source_pack_sic_ingestion_allowed_after_decision") is False
                and shot.get("source_pack_sic_ingestion_performed_after_decision") is False
                and shot.get("source_pack_sic_source_package_written_after_decision") is False
                and shot.get("source_pack_sic_workspace_membership_written_after_decision") is False
                and shot.get("source_pack_sic_graph_mutation_after_decision") is False
                and shot.get("source_pack_sic_canonical_mutation_after_decision") is False
                and shot.get("source_pack_sic_provider_call_after_decision") is False
                and shot.get("source_pack_sic_external_send_after_decision") is False
                and shot.get("source_pack_sic_attachment_delete_after_decision") is False
                for shot in screenshots
            ),
            "source_pack_sic_ingestion_approval_consumption_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_ingestion_approval_consumption_preview_visible")
                and shot.get("source_pack_sic_ingestion_approval_consumption_visible")
                and shot.get("source_pack_sic_ingestion_approval_consumption_result_ok")
                and shot.get("source_pack_sic_ingestion_approval_consumed_after_consumption") is True
                and shot.get("source_pack_sic_ingestion_approval_decision_consumed_after_consumption") is True
                and shot.get("source_pack_sic_ingestion_approval_consumption_marker_written") is True
                and shot.get("source_pack_sic_ingestion_approval_consumption_artifact_written") is True
                and shot.get("source_pack_sic_ingestion_approval_consumption_written_paths_exist")
                and shot.get("source_pack_sic_ingestion_executor_ready_after_consumption") is True
                and shot.get("source_pack_sic_ingestion_allowed_after_consumption") is False
                and shot.get("source_pack_sic_ingestion_performed_after_consumption") is False
                and shot.get("source_pack_sic_source_package_written_after_consumption") is False
                and shot.get("source_pack_sic_workspace_membership_written_after_consumption") is False
                and shot.get("source_pack_sic_graph_mutation_after_consumption") is False
                and shot.get("source_pack_sic_canonical_mutation_after_consumption") is False
                and shot.get("source_pack_sic_provider_call_after_consumption") is False
                and shot.get("source_pack_sic_external_send_after_consumption") is False
                and shot.get("source_pack_sic_attachment_delete_after_consumption") is False
                for shot in screenshots
            ),
            "source_pack_sic_ingestion_executor_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_ingestion_preview_visible")
                and shot.get("source_pack_sic_ingestion_preview_result_ok")
                and shot.get("source_pack_sic_ingestion_preview_ready") is True
                and shot.get("source_pack_sic_ingestion_digest_ready") is True
                and shot.get("source_pack_sic_ingestion_visible")
                and shot.get("source_pack_sic_ingestion_result_ok")
                and shot.get("source_pack_sic_ingestion_written_paths_exist")
                and shot.get("source_pack_sic_ingestion_performed_after_ingestion") is True
                and shot.get("source_pack_sic_workspace_written_after_ingestion") is True
                and shot.get("source_pack_sic_source_package_written_after_ingestion") is True
                and shot.get("source_pack_sic_workspace_membership_written_after_ingestion") is True
                and shot.get("source_pack_sic_graph_mutation_after_ingestion") is False
                and shot.get("source_pack_sic_canonical_mutation_after_ingestion") is False
                and shot.get("source_pack_sic_provider_call_after_ingestion") is False
                and shot.get("source_pack_sic_external_send_after_ingestion") is False
                and shot.get("source_pack_sic_attachment_delete_after_ingestion") in (False, None)
                for shot in screenshots
            ),
            "source_pack_sic_graph_indexing_readiness_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_graph_indexing_readiness_visible")
                and shot.get("source_pack_sic_graph_indexing_readiness_result_ok")
                and shot.get("source_pack_sic_graph_indexing_readiness_preview_ready") is True
                and shot.get("source_pack_sic_graph_indexing_readiness_packet_digest_ready") is True
                and (shot.get("source_pack_sic_graph_indexing_candidate_node_count") or 0) >= 4
                and (shot.get("source_pack_sic_graph_indexing_candidate_edge_count") or 0) >= 3
                and shot.get("source_pack_sic_graph_mutation_after_graph_readiness") is False
                and shot.get("source_pack_sic_graph_snapshot_written_after_graph_readiness") is False
                and shot.get("source_pack_sic_canonical_mutation_after_graph_readiness") is False
                and shot.get("source_pack_sic_provider_call_after_graph_readiness") is False
                and shot.get("source_pack_sic_external_send_after_graph_readiness") is False
                and shot.get("source_pack_sic_attachment_delete_after_graph_readiness") in (False, None)
                for shot in screenshots
            ),
            "source_pack_sic_graph_indexing_executor_verified": bool(screenshots)
            and all(
                shot.get("source_pack_sic_graph_indexing_preview_result_ok")
                and shot.get("source_pack_sic_graph_indexing_preview_ready") is True
                and shot.get("source_pack_sic_graph_indexing_write_allowed_preview") is False
                and shot.get("source_pack_sic_graph_indexing_visible")
                and shot.get("source_pack_sic_graph_indexing_result_ok")
                and shot.get("source_pack_sic_graph_indexing_written_paths_exist")
                and shot.get("source_pack_sic_graph_mutation_after_graph_indexing") is True
                and shot.get("source_pack_sic_graph_snapshot_written_after_graph_indexing") is True
                and shot.get("source_pack_sic_graph_store_manifest_written_after_graph_indexing") is True
                and shot.get("source_pack_sic_graph_current_pointer_written_after_graph_indexing") is True
                and shot.get("source_pack_sic_canonical_mutation_after_graph_indexing") is False
                and shot.get("source_pack_sic_provider_call_after_graph_indexing") is False
                and shot.get("source_pack_sic_external_send_after_graph_indexing") is False
                and shot.get("source_pack_sic_attachment_delete_after_graph_indexing") in (False, None)
                for shot in screenshots
            ),
            "source_pack_canonical_promotion_readiness_verified": bool(screenshots)
            and all(
                shot.get("source_pack_canonical_promotion_readiness_visible")
                and shot.get("source_pack_canonical_promotion_readiness_result_ok")
                and shot.get("source_pack_canonical_promotion_readiness_preview_ready") is True
                and shot.get("source_pack_canonical_promotion_candidate_digest_ready") is True
                and (shot.get("source_pack_canonical_promotion_target_count") or 0) >= 2
                and shot.get("source_pack_canonical_promotion_graph_store_current_pointer_verified") is True
                and shot.get("source_pack_canonical_promotion_canonical_allowed_now") is False
                and shot.get("source_pack_canonical_promotion_canonical_mutation_performed") is False
                and shot.get("source_pack_canonical_promotion_knowledge_promotion_performed") is False
                and shot.get("source_pack_canonical_promotion_provider_call_performed") is False
                and shot.get("source_pack_canonical_promotion_external_send_performed") is False
                and shot.get("source_pack_canonical_promotion_attachment_delete_performed") in (False, None)
                for shot in screenshots
            ),
            "source_pack_canonical_promotion_approval_design_verified": bool(screenshots)
            and all(
                shot.get("source_pack_canonical_promotion_approval_design_visible")
                and shot.get("source_pack_canonical_promotion_approval_design_result_ok")
                and shot.get("source_pack_canonical_promotion_approval_packet_preview_ready") is True
                and shot.get("source_pack_canonical_promotion_approval_request_digest_ready") is True
                and shot.get("source_pack_canonical_promotion_approval_request_written_after_design") is False
                and shot.get("source_pack_canonical_promotion_executor_ready_after_design") is False
                and shot.get("source_pack_canonical_promotion_allowed_after_design") is False
                and shot.get("source_pack_canonical_promotion_performed_after_design") is False
                and shot.get("source_pack_canonical_promotion_note_written_after_design") is False
                and shot.get("source_pack_canonical_promotion_index_written_after_design") is False
                and shot.get("source_pack_canonical_promotion_provider_call_after_design") is False
                and shot.get("source_pack_canonical_promotion_external_send_after_design") is False
                and shot.get("source_pack_canonical_promotion_attachment_delete_after_design") in (False, None)
                for shot in screenshots
            ),
            "source_pack_canonical_promotion_approval_request_verified": bool(screenshots)
            and all(
                shot.get("source_pack_canonical_promotion_approval_request_visible")
                and shot.get("source_pack_canonical_promotion_approval_request_result_ok")
                and shot.get("source_pack_canonical_promotion_approval_request_written") is True
                and shot.get("source_pack_canonical_promotion_approval_request_artifact_written") is True
                and shot.get("source_pack_canonical_promotion_approval_request_written_paths_exist")
                and shot.get("source_pack_canonical_promotion_ready_for_decision_after_request") is True
                and shot.get("source_pack_canonical_promotion_executor_ready_after_request") is False
                and shot.get("source_pack_canonical_promotion_allowed_after_request") is False
                and shot.get("source_pack_canonical_promotion_performed_after_request") is False
                and shot.get("source_pack_canonical_promotion_note_written_after_request") is False
                and shot.get("source_pack_canonical_promotion_index_written_after_request") is False
                and shot.get("source_pack_canonical_promotion_provider_call_after_request") is False
                and shot.get("source_pack_canonical_promotion_external_send_after_request") is False
                and shot.get("source_pack_canonical_promotion_attachment_delete_after_request") in (False, None)
                for shot in screenshots
            ),
            "source_pack_canonical_promotion_approval_decision_readiness_verified": bool(screenshots)
            and all(
                shot.get("source_pack_canonical_promotion_decision_readiness_visible")
                and shot.get("source_pack_canonical_promotion_decision_readiness_result_ok")
                and shot.get("source_pack_canonical_promotion_decision_readiness_request_verified") is True
                and shot.get("source_pack_canonical_promotion_decision_readiness_pending") is True
                and shot.get("source_pack_canonical_promotion_decision_readiness_decision_writer_ready") is True
                and shot.get("source_pack_canonical_promotion_decision_readiness_decision_ready") is True
                and shot.get("source_pack_canonical_promotion_decision_readiness_decision_option_count") == 2
                and shot.get("source_pack_canonical_promotion_decision_readiness_consumption_ready") is False
                and shot.get("source_pack_canonical_promotion_decision_readiness_executor_ready") is False
                and shot.get("source_pack_canonical_promotion_decision_readiness_decision_written") is False
                and shot.get("source_pack_canonical_promotion_decision_readiness_approval_consumed") is False
                and shot.get("source_pack_canonical_promotion_decision_readiness_marker_written") is False
                and shot.get("source_pack_canonical_promotion_decision_readiness_future_marker_exists") is False
                and shot.get("source_pack_canonical_promotion_allowed_after_decision_readiness") is False
                and shot.get("source_pack_canonical_promotion_performed_after_decision_readiness") is False
                and shot.get("source_pack_canonical_promotion_note_written_after_decision_readiness") is False
                and shot.get("source_pack_canonical_promotion_index_written_after_decision_readiness") is False
                and shot.get("source_pack_canonical_promotion_graph_mutation_after_decision_readiness") is False
                and shot.get("source_pack_canonical_promotion_provider_call_after_decision_readiness") is False
                and shot.get("source_pack_canonical_promotion_external_send_after_decision_readiness") is False
                and shot.get("source_pack_canonical_promotion_attachment_delete_after_decision_readiness") in (False, None)
                for shot in screenshots
            ),
            "source_pack_canonical_promotion_approval_decision_verified": bool(screenshots)
            and all(
                shot.get("source_pack_canonical_promotion_approval_decision_visible")
                and shot.get("source_pack_canonical_promotion_approval_decision_result_ok")
                and shot.get("source_pack_canonical_promotion_approval_decision_written") is True
                and shot.get("source_pack_canonical_promotion_approval_decision_artifact_written") is True
                and shot.get("source_pack_canonical_promotion_approval_decision_written_paths_exist")
                and shot.get("source_pack_canonical_promotion_approval_consumption_ready_after_decision") is True
                and shot.get("source_pack_canonical_promotion_executor_ready_after_decision") is False
                and shot.get("source_pack_canonical_promotion_approval_consumed_after_decision") is False
                and shot.get("source_pack_canonical_promotion_marker_written_after_decision") is False
                and shot.get("source_pack_canonical_promotion_allowed_after_decision") is False
                and shot.get("source_pack_canonical_promotion_performed_after_decision") is False
                and shot.get("source_pack_canonical_promotion_note_written_after_decision") is False
                and shot.get("source_pack_canonical_promotion_index_written_after_decision") is False
                and shot.get("source_pack_canonical_promotion_graph_mutation_after_decision") is False
                and shot.get("source_pack_canonical_promotion_provider_call_after_decision") is False
                and shot.get("source_pack_canonical_promotion_external_send_after_decision") is False
                and shot.get("source_pack_canonical_promotion_attachment_delete_after_decision") in (False, None)
                for shot in screenshots
            ),
            "source_pack_canonical_promotion_approval_consumption_verified": bool(screenshots)
            and all(
                shot.get("source_pack_canonical_promotion_approval_consumption_visible")
                and shot.get("source_pack_canonical_promotion_approval_consumption_result_ok")
                and shot.get("source_pack_canonical_promotion_approval_consumed") is True
                and shot.get("source_pack_canonical_promotion_approval_consumption_artifact_written") is True
                and shot.get("source_pack_canonical_promotion_approval_consumption_marker_written") is True
                and shot.get("source_pack_canonical_promotion_approval_consumption_written_paths_exist")
                and shot.get("source_pack_canonical_promotion_executor_ready_after_consumption") is True
                and shot.get("source_pack_canonical_promotion_allowed_after_consumption") is False
                and shot.get("source_pack_canonical_promotion_performed_after_consumption") is False
                and shot.get("source_pack_canonical_promotion_note_written_after_consumption") is False
                and shot.get("source_pack_canonical_promotion_index_written_after_consumption") is False
                and shot.get("source_pack_canonical_promotion_graph_mutation_after_consumption") is False
                and shot.get("source_pack_canonical_promotion_provider_call_after_consumption") is False
                and shot.get("source_pack_canonical_promotion_external_send_after_consumption") is False
                and shot.get("source_pack_canonical_promotion_attachment_delete_after_consumption") in (False, None)
                for shot in screenshots
            ),
            "source_pack_canonical_promotion_executor_verified": bool(screenshots)
            and all(
                shot.get("source_pack_canonical_promotion_executor_visible")
                and shot.get("source_pack_canonical_promotion_executor_result_ok")
                and shot.get("source_pack_canonical_promotion_marker_written") is True
                and shot.get("source_pack_canonical_promotion_note_written") is True
                and shot.get("source_pack_canonical_promotion_index_written") is True
                and shot.get("source_pack_canonical_promotion_artifact_written") is True
                and shot.get("source_pack_canonical_promotion_written_paths_exist")
                and shot.get("source_pack_canonical_promotion_canonical_mutation_after_executor") is True
                and shot.get("source_pack_canonical_promotion_graph_mutation_after_executor") is False
                and shot.get("source_pack_canonical_promotion_source_intelligence_core_rewrite_after_executor") is False
                and shot.get("source_pack_canonical_promotion_provider_call_after_executor") is False
                and shot.get("source_pack_canonical_promotion_external_send_after_executor") is False
                and shot.get("source_pack_canonical_promotion_attachment_delete_after_executor") is False
                for shot in screenshots
            ),
            "runtime_delete_blocked": bool(screenshots) and all(shot.get("runtime_delete_allowed") is False for shot in screenshots),
            "fixture_vault_persisted": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "screenshots": screenshots,
        "console_errors_or_warnings": visual.get("console_errors_or_warnings") or [],
        "page_errors": visual.get("page_errors") or [],
        "required_tokens": list(REQUIRED_TOKENS),
        "missing_required_tokens": missing_tokens,
        "authority": _authority(),
        "blockers": list(dict.fromkeys(blockers)),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    json_path = resolved_output / "capture-markdown-visual-qa-report.json"
    md_path = resolved_output / "capture-markdown-visual-qa-report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(_format_markdown(report), encoding="utf-8")
    report["report_path"] = _relative_to_vault(vault, json_path)
    report["markdown_report_path"] = _relative_to_vault(vault, md_path)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Capture Markdown Studio visual quality assurance.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory inside the vault.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args(argv)
    report = build_capture_markdown_visual_qa(args.vault_root, output_dir=args.output_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"ok={report['ok']} report={report.get('report_path')}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
