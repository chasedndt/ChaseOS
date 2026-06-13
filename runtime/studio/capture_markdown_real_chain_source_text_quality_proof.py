"""Real web Capture to Markdown replay proof.

This module intentionally uses the governed production executors instead of
test-only helpers. It starts from a controlled saved web artifact, writes a new
visual capture Markdown file, reviews it, carries it through source package
writeback, Agent Orchestration Runtime dispatch, Source Intelligence Core
ingestion, graph indexing, and canonical promotion, then writes a proof report.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.acquisition.visual_capture_source_pack_approval_preview import (
    REQUIRED_OPERATOR_STATEMENT as SOURCE_PACK_WRITE_OPERATOR_STATEMENT,
    build_visual_capture_source_pack_approval_preview,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_agent_bus_task_writer import (
    build_visual_capture_source_pack_aor_dispatch_agent_bus_task,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_consumption_executor import (
    build_visual_capture_source_pack_aor_dispatch_approval_consumption,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_decision_writer import (
    build_visual_capture_source_pack_aor_dispatch_approval_decision,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_design import (
    FUTURE_OPERATOR_APPROVAL_STATEMENT as AGENT_ORCHESTRATION_RUNTIME_APPROVAL_STATEMENT,
    build_visual_capture_source_pack_aor_dispatch_approval_design,
)
from runtime.acquisition.visual_capture_source_pack_aor_dispatch_approval_request_writer import (
    build_visual_capture_source_pack_aor_dispatch_approval_request,
)
from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_consumption_executor import (
    build_visual_capture_source_pack_canonical_promotion_approval_consumption,
)
from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_decision_writer import (
    build_visual_capture_source_pack_canonical_promotion_approval_decision,
)
from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_design import (
    build_visual_capture_source_pack_canonical_promotion_approval_design,
)
from runtime.acquisition.visual_capture_source_pack_canonical_promotion_approval_request_writer import (
    build_visual_capture_source_pack_canonical_promotion_approval_request,
)
from runtime.acquisition.visual_capture_source_pack_canonical_promotion_executor import (
    build_visual_capture_source_pack_canonical_promotion,
)
from runtime.acquisition.visual_capture_source_pack_canonical_promotion_readiness import (
    build_visual_capture_source_pack_canonical_promotion_readiness,
)
from runtime.acquisition.visual_capture_source_pack_sic_graph_indexing_executor import (
    build_visual_capture_source_pack_sic_graph_indexing_executor,
)
from runtime.acquisition.visual_capture_source_pack_sic_graph_indexing_readiness import (
    build_visual_capture_source_pack_sic_graph_indexing_readiness,
)
from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_consumption_executor import (
    build_visual_capture_source_pack_sic_ingestion_approval_consumption,
)
from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_decision_writer import (
    build_visual_capture_source_pack_sic_ingestion_approval_decision,
)
from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_design import (
    build_visual_capture_source_pack_sic_ingestion_approval_design,
)
from runtime.acquisition.visual_capture_source_pack_sic_ingestion_approval_request_writer import (
    build_visual_capture_source_pack_sic_ingestion_approval_request,
)
from runtime.acquisition.visual_capture_source_pack_sic_ingestion_executor import (
    build_visual_capture_source_pack_sic_ingestion,
)
from runtime.acquisition.visual_capture_source_pack_sic_ingestion_readiness import (
    build_visual_capture_source_pack_sic_ingestion_readiness,
)
from runtime.acquisition.visual_capture_source_pack_write_executor import (
    execute_visual_capture_source_pack_write,
)
from runtime.capture.visual_capture import (
    capture_from_controlled_browser_artifact,
    review_visual_capture_artifact,
    save_visual_capture,
)


DEFAULT_TARGET_WORKSPACE_ID = "vcmi-reviewed-captures"
DEFAULT_RUNTIME = "OpenClaw"
PROOF_ROOT = Path("07_LOGS/Agent-Activity")


def run_real_chain_source_text_quality_proof(
    *,
    vault_root: str | Path,
    html_path: str | Path,
    source_url: str,
    allowed_origin: str,
    title: str | None = None,
    target_workspace_id: str = DEFAULT_TARGET_WORKSPACE_ID,
    runtime: str = DEFAULT_RUNTIME,
    reviewed_by: str = "Codex",
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    html = Path(html_path)
    if not html.is_absolute():
        html = (vault / html).resolve()
    run_id = _run_id()
    resolved_title = title or f"Capture to Markdown Real Web Replay {run_id}"

    packet = capture_from_controlled_browser_artifact(
        file_path=html,
        vault_root=vault,
        declared_url=source_url,
        allowed_origin=allowed_origin,
        title=resolved_title,
        profile="research_note",
        user_intent=(
            "Fresh real web replay proof for Capture to Markdown source text "
            "quality propagation."
        ),
    )
    saved = _assert_ok("save visual capture", save_visual_capture(vault_root=vault, packet=packet))
    if saved.get("is_duplicate"):
        raise RuntimeError("fresh real web replay unexpectedly produced a duplicate capture")

    capture_path = _rel(saved["visual_capture_packet_path"], vault)
    content_path = _rel(saved["content_path"], vault)
    sidecar_path = _rel(saved["sidecar_path"], vault)
    review = _assert_ok(
        "review visual capture",
        review_visual_capture_artifact(
            vault,
            sidecar_path,
            decision="reviewed",
            reviewed_by=reviewed_by,
            review_note="Fresh real web replay approved for governed proof run.",
        ),
    )

    source_pack_preview = _assert_ok(
        "source package approval preview",
        build_visual_capture_source_pack_approval_preview(vault, capture_path),
    )
    source_pack_write = _assert_ok(
        "source package write",
        execute_visual_capture_source_pack_write(
            vault,
            capture_path,
            request_digest=source_pack_preview["request_digest"],
            operator_statement=SOURCE_PACK_WRITE_OPERATOR_STATEMENT,
        ),
    )

    setup = {
        "capture_path": capture_path,
        "request_digest": source_pack_preview["request_digest"],
    }
    agent_orchestration = _run_agent_orchestration_dispatch(
        vault,
        setup,
        target_workspace_id=target_workspace_id,
        runtime=runtime,
    )
    source_intelligence = _run_source_intelligence_ingestion(
        vault,
        setup,
        agent_orchestration["full_dispatch"],
        target_workspace_id=target_workspace_id,
        reviewed_by=reviewed_by,
    )
    graph_indexing = _run_graph_indexing(
        vault,
        source_intelligence["ingestion"],
        target_workspace_id=target_workspace_id,
    )
    canonical = _run_canonical_promotion(
        vault,
        graph_indexing,
        promoted_by=reviewed_by,
    )

    verification = _verify_outputs(
        vault=vault,
        html_path=html,
        content_path=content_path,
        source_intelligence=source_intelligence,
        graph_indexing=graph_indexing,
        canonical=canonical,
    )

    proof = {
        "ok": verification["ok"],
        "status": "real_web_capture_to_markdown_chain_verified"
        if verification["ok"]
        else "real_web_capture_to_markdown_chain_failed_verification",
        "run_id": run_id,
        "source_url": source_url,
        "allowed_origin": allowed_origin,
        "controlled_html_artifact_path": _rel(html, vault),
        "capture_markdown_path": content_path,
        "visual_capture_packet_path": capture_path,
        "visual_capture_sidecar_path": sidecar_path,
        "review_result": _summary(review),
        "source_pack_write": _summary(source_pack_write),
        "agent_orchestration_runtime": _agent_orchestration_summary(agent_orchestration),
        "source_intelligence_core": _source_intelligence_summary(source_intelligence),
        "graph_indexing": _summary(graph_indexing),
        "canonical_promotion": _canonical_summary(canonical),
        "verification": verification,
        "proof_artifacts": {},
    }
    proof_paths = _write_proof_artifacts(vault, proof)
    proof["proof_artifacts"] = proof_paths
    return proof


def _run_agent_orchestration_dispatch(
    vault: Path,
    setup: dict[str, str],
    *,
    target_workspace_id: str,
    runtime: str,
) -> dict[str, Any]:
    capture_path = setup["capture_path"]
    request_digest = setup["request_digest"]

    design = _assert_ok(
        "Agent Orchestration Runtime approval design",
        build_visual_capture_source_pack_aor_dispatch_approval_design(
            vault,
            capture_path,
            request_digest=request_digest,
        ),
    )
    expected_request_digest = design["future_aor_dispatch_approval_packet_preview"][
        "approval_request_digest"
    ]
    approval_request = _assert_ok(
        "Agent Orchestration Runtime approval request",
        build_visual_capture_source_pack_aor_dispatch_approval_request(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            operator_statement=AGENT_ORCHESTRATION_RUNTIME_APPROVAL_STATEMENT,
            write_approval_request=True,
        ),
    )
    decision_preview = _assert_ok(
        "Agent Orchestration Runtime approval decision preview",
        build_visual_capture_source_pack_aor_dispatch_approval_decision(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
        ),
    )
    decision = _assert_ok(
        "Agent Orchestration Runtime approval decision",
        build_visual_capture_source_pack_aor_dispatch_approval_decision(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            expected_approval_decision_digest=decision_preview["approval_decision_digest"],
            operator_statement=decision_preview["required_operator_statement"],
            write_approval_decision=True,
        ),
    )
    consumption_preview = _assert_ok(
        "Agent Orchestration Runtime approval consumption preview",
        build_visual_capture_source_pack_aor_dispatch_approval_consumption(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=decision["approval_decision_artifact_path"],
            expected_approval_decision_digest=decision["approval_decision_digest"],
        ),
    )
    consumption = _assert_ok(
        "Agent Orchestration Runtime approval consumption",
        build_visual_capture_source_pack_aor_dispatch_approval_consumption(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=decision["approval_decision_artifact_path"],
            expected_approval_decision_digest=decision["approval_decision_digest"],
            expected_approval_consumption_digest=consumption_preview[
                "approval_consumption_digest"
            ],
            operator_statement=consumption_preview["required_operator_statement"],
            write_consumption_marker=True,
            write_approval_consumption=True,
        ),
    )
    task_preview = _assert_ok(
        "Agent Bus task preview",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_task(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_approval_decision_digest=consumption["approval_decision_digest"],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_approval_consumption_digest=consumption["approval_consumption_digest"],
        ),
    )
    task = _assert_ok(
        "Agent Bus task write",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_task(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_approval_decision_digest=consumption["approval_decision_digest"],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_approval_consumption_digest=consumption["approval_consumption_digest"],
            expected_agent_bus_task_digest=task_preview["agent_bus_task_digest"],
            operator_statement=task_preview["required_operator_statement"],
            write_task_marker=True,
            write_agent_bus_task=True,
        ),
    )
    claim_preview = _assert_ok(
        "Agent Bus task claim preview",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_approval_decision_digest=consumption["approval_decision_digest"],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_approval_consumption_digest=consumption["approval_consumption_digest"],
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            runtime=runtime,
        ),
    )
    claim = _assert_ok(
        "Agent Bus task claim",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_approval_decision_digest=consumption["approval_decision_digest"],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_approval_consumption_digest=consumption["approval_consumption_digest"],
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            expected_agent_bus_task_claim_digest=claim_preview["agent_bus_task_claim_digest"],
            operator_statement=claim_preview["required_operator_statement"],
            runtime=runtime,
            write_claim_marker=True,
            claim_agent_bus_task=True,
            write_claim_artifact=True,
        ),
    )
    dry_run_preview = _assert_ok(
        "Agent Orchestration Runtime dry run preview",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_approval_decision_digest=consumption["approval_decision_digest"],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_approval_consumption_digest=consumption["approval_consumption_digest"],
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            agent_bus_task_claim_artifact_path=claim["agent_bus_task_claim_artifact_path"],
            expected_agent_bus_task_claim_digest=claim["agent_bus_task_claim_digest"],
            runtime=runtime,
        ),
    )
    dry_run = _assert_ok(
        "Agent Orchestration Runtime dry run",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor(
            vault,
            capture_path,
            request_digest=request_digest,
            expected_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_approval_decision_digest=consumption["approval_decision_digest"],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_approval_consumption_digest=consumption["approval_consumption_digest"],
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            agent_bus_task_claim_artifact_path=claim["agent_bus_task_claim_artifact_path"],
            expected_agent_bus_task_claim_digest=claim["agent_bus_task_claim_digest"],
            expected_aor_dry_run_packet_digest=dry_run_preview["aor_dry_run_packet_digest"],
            operator_statement=dry_run_preview["required_operator_statement"],
            runtime=runtime,
            write_aor_dry_run_marker=True,
            run_aor_dry_run=True,
            write_aor_dry_run_artifact=True,
        ),
    )
    status_preview = _assert_ok(
        "Agent Bus task review status preview",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle(
            vault,
            capture_path,
            request_digest=request_digest,
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            agent_bus_task_claim_artifact_path=claim["agent_bus_task_claim_artifact_path"],
            expected_agent_bus_task_claim_digest=claim["agent_bus_task_claim_digest"],
            aor_dry_run_artifact_path=dry_run["aor_dry_run_artifact_path"],
            expected_aor_dry_run_artifact_digest=dry_run["aor_dry_run_artifact"][
                "artifact_digest"
            ],
            runtime=runtime,
        ),
    )
    status_lifecycle = _assert_ok(
        "Agent Bus task review status",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle(
            vault,
            capture_path,
            request_digest=request_digest,
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            agent_bus_task_claim_artifact_path=claim["agent_bus_task_claim_artifact_path"],
            expected_agent_bus_task_claim_digest=claim["agent_bus_task_claim_digest"],
            aor_dry_run_artifact_path=dry_run["aor_dry_run_artifact_path"],
            expected_aor_dry_run_artifact_digest=dry_run["aor_dry_run_artifact"][
                "artifact_digest"
            ],
            operator_statement=status_preview["required_operator_statement"],
            runtime=runtime,
            write_status_lifecycle_marker=True,
            update_agent_bus_task_status=True,
            write_status_lifecycle_artifact=True,
        ),
    )
    full_readiness = _assert_ok(
        "Agent Orchestration Runtime full dispatch readiness",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness(
            vault,
            capture_path,
            request_digest=request_digest,
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            agent_bus_task_claim_artifact_path=claim["agent_bus_task_claim_artifact_path"],
            expected_agent_bus_task_claim_digest=claim["agent_bus_task_claim_digest"],
            aor_dry_run_artifact_path=dry_run["aor_dry_run_artifact_path"],
            expected_aor_dry_run_artifact_digest=dry_run["aor_dry_run_artifact"][
                "artifact_digest"
            ],
            status_lifecycle_artifact_path=status_lifecycle["status_lifecycle_artifact_path"],
            expected_status_lifecycle_artifact_digest=status_lifecycle[
                "status_lifecycle_artifact"
            ]["artifact_digest"],
            runtime=runtime,
        ),
    )
    full_preview = _assert_ok(
        "Agent Orchestration Runtime full dispatch preview",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor(
            vault,
            capture_path,
            request_digest=request_digest,
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            agent_bus_task_claim_artifact_path=claim["agent_bus_task_claim_artifact_path"],
            expected_agent_bus_task_claim_digest=claim["agent_bus_task_claim_digest"],
            aor_dry_run_artifact_path=dry_run["aor_dry_run_artifact_path"],
            expected_aor_dry_run_artifact_digest=dry_run["aor_dry_run_artifact"][
                "artifact_digest"
            ],
            status_lifecycle_artifact_path=status_lifecycle["status_lifecycle_artifact_path"],
            expected_status_lifecycle_artifact_digest=status_lifecycle[
                "status_lifecycle_artifact"
            ]["artifact_digest"],
            runtime=runtime,
        ),
    )
    full_dispatch = _assert_ok(
        "Agent Orchestration Runtime full dispatch",
        build_visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor(
            vault,
            capture_path,
            request_digest=request_digest,
            agent_bus_task_artifact_path=task["agent_bus_task_artifact_path"],
            expected_agent_bus_task_digest=task["agent_bus_task_digest"],
            agent_bus_task_id=task["agent_bus_task_id"],
            agent_bus_task_claim_artifact_path=claim["agent_bus_task_claim_artifact_path"],
            expected_agent_bus_task_claim_digest=claim["agent_bus_task_claim_digest"],
            aor_dry_run_artifact_path=dry_run["aor_dry_run_artifact_path"],
            expected_aor_dry_run_artifact_digest=dry_run["aor_dry_run_artifact"][
                "artifact_digest"
            ],
            status_lifecycle_artifact_path=status_lifecycle["status_lifecycle_artifact_path"],
            expected_status_lifecycle_artifact_digest=status_lifecycle[
                "status_lifecycle_artifact"
            ]["artifact_digest"],
            expected_full_dispatch_packet_digest=full_preview["full_dispatch_packet_digest"],
            operator_statement=full_preview["required_operator_statement"],
            runtime=runtime,
            write_full_dispatch_marker=True,
            run_full_dispatch=True,
            write_full_dispatch_artifact=True,
        ),
    )
    return {
        "design": design,
        "approval_request": approval_request,
        "approval_decision": decision,
        "approval_consumption": consumption,
        "task": task,
        "claim": claim,
        "dry_run": dry_run,
        "status_lifecycle": status_lifecycle,
        "full_readiness": full_readiness,
        "full_dispatch": full_dispatch,
        "target_workspace_id": target_workspace_id,
    }


def _run_source_intelligence_ingestion(
    vault: Path,
    setup: dict[str, str],
    full_dispatch: dict[str, Any],
    *,
    target_workspace_id: str,
    reviewed_by: str,
) -> dict[str, Any]:
    capture_path = setup["capture_path"]
    request_digest = setup["request_digest"]
    readiness = _assert_ok(
        "Source Intelligence Core ingestion readiness",
        build_visual_capture_source_pack_sic_ingestion_readiness(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            target_workspace_id=target_workspace_id,
            reviewed_by=reviewed_by,
        ),
    )
    design = _assert_ok(
        "Source Intelligence Core ingestion approval design",
        build_visual_capture_source_pack_sic_ingestion_approval_design(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=readiness[
                "future_sic_ingestion_packet_digest"
            ],
            target_workspace_id=target_workspace_id,
            reviewed_by=reviewed_by,
        ),
    )
    expected_request_digest = design[
        "future_source_intelligence_core_ingestion_approval_packet_preview"
    ]["approval_request_digest"]
    approval_request = _assert_ok(
        "Source Intelligence Core ingestion approval request",
        build_visual_capture_source_pack_sic_ingestion_approval_request(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=design[
                "source_intelligence_core_readiness_packet_digest"
            ],
            expected_sic_ingestion_approval_request_digest=expected_request_digest,
            operator_statement=design["approval_design"]["future_operator_statement_required"],
            target_workspace_id=target_workspace_id,
            reviewed_by=reviewed_by,
            requested_by=reviewed_by,
            write_approval_request=True,
        ),
    )
    decision_preview = _assert_ok(
        "Source Intelligence Core ingestion approval decision preview",
        build_visual_capture_source_pack_sic_ingestion_approval_decision(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=design[
                "source_intelligence_core_readiness_packet_digest"
            ],
            expected_sic_ingestion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            target_workspace_id=target_workspace_id,
        ),
    )
    decision = _assert_ok(
        "Source Intelligence Core ingestion approval decision",
        build_visual_capture_source_pack_sic_ingestion_approval_decision(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=design[
                "source_intelligence_core_readiness_packet_digest"
            ],
            expected_sic_ingestion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            expected_sic_ingestion_approval_decision_digest=decision_preview[
                "approval_decision_digest"
            ],
            operator_statement=decision_preview["required_operator_statement"],
            target_workspace_id=target_workspace_id,
            write_approval_decision=True,
        ),
    )
    consumption_preview = _assert_ok(
        "Source Intelligence Core ingestion approval consumption preview",
        build_visual_capture_source_pack_sic_ingestion_approval_consumption(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=design[
                "source_intelligence_core_readiness_packet_digest"
            ],
            expected_sic_ingestion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=decision["approval_decision_artifact_path"],
            expected_sic_ingestion_approval_decision_digest=decision[
                "approval_decision_digest"
            ],
            target_workspace_id=target_workspace_id,
        ),
    )
    consumption = _assert_ok(
        "Source Intelligence Core ingestion approval consumption",
        build_visual_capture_source_pack_sic_ingestion_approval_consumption(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=design[
                "source_intelligence_core_readiness_packet_digest"
            ],
            expected_sic_ingestion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=decision["approval_decision_artifact_path"],
            expected_sic_ingestion_approval_decision_digest=decision[
                "approval_decision_digest"
            ],
            expected_sic_ingestion_approval_consumption_digest=consumption_preview[
                "approval_consumption_digest"
            ],
            operator_statement=consumption_preview["required_operator_statement"],
            target_workspace_id=target_workspace_id,
            write_consumption_marker=True,
            write_approval_consumption=True,
        ),
    )
    ingestion_preview = _assert_ok(
        "Source Intelligence Core ingestion preview",
        build_visual_capture_source_pack_sic_ingestion(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=design[
                "source_intelligence_core_readiness_packet_digest"
            ],
            expected_sic_ingestion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_sic_ingestion_approval_decision_digest=consumption[
                "approval_decision_digest"
            ],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_sic_ingestion_approval_consumption_digest=consumption[
                "approval_consumption_digest"
            ],
            target_workspace_id=target_workspace_id,
        ),
    )
    ingestion = _assert_ok(
        "Source Intelligence Core ingestion",
        build_visual_capture_source_pack_sic_ingestion(
            vault,
            capture_path,
            request_digest=request_digest,
            full_dispatch_artifact_path=full_dispatch["full_dispatch_artifact_path"],
            expected_full_dispatch_artifact_digest=full_dispatch["aor_full_dispatch_artifact"][
                "artifact_digest"
            ],
            expected_full_dispatch_packet_digest=full_dispatch["full_dispatch_packet_digest"],
            expected_sic_ingestion_readiness_packet_digest=design[
                "source_intelligence_core_readiness_packet_digest"
            ],
            expected_sic_ingestion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=consumption["approval_decision_artifact_path"],
            expected_sic_ingestion_approval_decision_digest=consumption[
                "approval_decision_digest"
            ],
            approval_consumption_artifact_path=consumption["approval_consumption_artifact_path"],
            expected_sic_ingestion_approval_consumption_digest=consumption[
                "approval_consumption_digest"
            ],
            expected_sic_ingestion_digest=ingestion_preview[
                "source_intelligence_core_ingestion_digest"
            ],
            operator_statement=ingestion_preview["required_operator_statement"],
            target_workspace_id=target_workspace_id,
            write_ingestion_marker=True,
            run_source_intelligence_core_ingestion=True,
            write_ingestion_artifact=True,
        ),
    )
    return {
        "readiness": readiness,
        "design": design,
        "approval_request": approval_request,
        "approval_decision": decision,
        "approval_consumption": consumption,
        "ingestion": ingestion,
    }


def _run_graph_indexing(
    vault: Path,
    ingestion: dict[str, Any],
    *,
    target_workspace_id: str,
) -> dict[str, Any]:
    readiness = _assert_ok(
        "graph indexing readiness",
        build_visual_capture_source_pack_sic_graph_indexing_readiness(
            vault,
            ingestion["source_intelligence_core_ingestion_artifact_path"],
            expected_source_intelligence_core_ingestion_artifact_digest=ingestion[
                "source_intelligence_core_ingestion_artifact"
            ]["artifact_digest"],
            expected_source_intelligence_core_ingestion_digest=ingestion[
                "source_intelligence_core_ingestion_digest"
            ],
            target_workspace_id=target_workspace_id,
        ),
    )
    preview = _assert_ok(
        "graph indexing preview",
        build_visual_capture_source_pack_sic_graph_indexing_executor(
            vault,
            ingestion["source_intelligence_core_ingestion_artifact_path"],
            expected_source_intelligence_core_ingestion_artifact_digest=ingestion[
                "source_intelligence_core_ingestion_artifact"
            ]["artifact_digest"],
            expected_source_intelligence_core_ingestion_digest=ingestion[
                "source_intelligence_core_ingestion_digest"
            ],
            expected_graph_index_preview_packet_digest=readiness[
                "graph_index_preview_packet_digest"
            ],
            target_workspace_id=target_workspace_id,
        ),
    )
    return _assert_ok(
        "graph indexing executor",
        build_visual_capture_source_pack_sic_graph_indexing_executor(
            vault,
            ingestion["source_intelligence_core_ingestion_artifact_path"],
            expected_source_intelligence_core_ingestion_artifact_digest=ingestion[
                "source_intelligence_core_ingestion_artifact"
            ]["artifact_digest"],
            expected_source_intelligence_core_ingestion_digest=ingestion[
                "source_intelligence_core_ingestion_digest"
            ],
            expected_graph_index_preview_packet_digest=readiness[
                "graph_index_preview_packet_digest"
            ],
            operator_statement=preview["required_operator_statement"],
            target_workspace_id=target_workspace_id,
            write_graph_indexing_marker=True,
            write_graph_snapshot=True,
            write_graph_indexing_artifact=True,
        ),
    )


def _run_canonical_promotion(
    vault: Path,
    graph_indexing: dict[str, Any],
    *,
    promoted_by: str,
) -> dict[str, Any]:
    readiness = _assert_ok(
        "canonical promotion readiness",
        build_visual_capture_source_pack_canonical_promotion_readiness(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
        ),
    )
    design = _assert_ok(
        "canonical promotion approval design",
        build_visual_capture_source_pack_canonical_promotion_approval_design(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=readiness[
                "future_canonical_promotion_candidate_digest"
            ],
        ),
    )
    expected_request_digest = design["future_canonical_promotion_approval_packet_preview"][
        "approval_request_digest"
    ]
    approval_request = _assert_ok(
        "canonical promotion approval request",
        build_visual_capture_source_pack_canonical_promotion_approval_request(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=design[
                "future_canonical_promotion_candidate_digest"
            ],
            expected_canonical_promotion_approval_request_digest=expected_request_digest,
            operator_statement=design["approval_design"]["future_operator_statement_required"],
            reviewed_by=promoted_by,
            requested_by=promoted_by,
            write_approval_request=True,
        ),
    )
    decision_preview = _assert_ok(
        "canonical promotion approval decision preview",
        build_visual_capture_source_pack_canonical_promotion_approval_decision(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=design[
                "future_canonical_promotion_candidate_digest"
            ],
            expected_canonical_promotion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
        ),
    )
    decision = _assert_ok(
        "canonical promotion approval decision",
        build_visual_capture_source_pack_canonical_promotion_approval_decision(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=design[
                "future_canonical_promotion_candidate_digest"
            ],
            expected_canonical_promotion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            expected_canonical_promotion_approval_decision_digest=decision_preview[
                "approval_decision_digest"
            ],
            operator_statement=decision_preview["required_operator_statement"],
            write_approval_decision=True,
        ),
    )
    consumption_preview = _assert_ok(
        "canonical promotion approval consumption preview",
        build_visual_capture_source_pack_canonical_promotion_approval_consumption(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=design[
                "future_canonical_promotion_candidate_digest"
            ],
            expected_canonical_promotion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=decision["approval_decision_artifact_path"],
            expected_canonical_promotion_approval_decision_digest=decision[
                "approval_decision_digest"
            ],
        ),
    )
    consumption = _assert_ok(
        "canonical promotion approval consumption",
        build_visual_capture_source_pack_canonical_promotion_approval_consumption(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=design[
                "future_canonical_promotion_candidate_digest"
            ],
            expected_canonical_promotion_approval_request_digest=expected_request_digest,
            approval_artifact_path=approval_request["approval_artifact_path"],
            decision="approved",
            approval_decision_artifact_path=decision["approval_decision_artifact_path"],
            expected_canonical_promotion_approval_decision_digest=decision[
                "approval_decision_digest"
            ],
            expected_canonical_promotion_approval_consumption_digest=consumption_preview[
                "approval_consumption_digest"
            ],
            operator_statement=consumption_preview["required_operator_statement"],
            write_consumption_marker=True,
            write_approval_consumption=True,
        ),
    )
    preview = _assert_ok(
        "canonical promotion preview",
        build_visual_capture_source_pack_canonical_promotion(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=design[
                "future_canonical_promotion_candidate_digest"
            ],
            expected_canonical_promotion_approval_request_digest=expected_request_digest,
            expected_canonical_promotion_approval_decision_digest=consumption[
                "approval_decision_digest"
            ],
            approval_consumption_artifact_path=consumption[
                "approval_consumption_artifact_path"
            ],
            expected_canonical_promotion_approval_consumption_digest=consumption[
                "approval_consumption_digest"
            ],
        ),
    )
    result = _assert_ok(
        "canonical promotion executor",
        build_visual_capture_source_pack_canonical_promotion(
            vault,
            graph_indexing["graph_indexing_artifact_path"],
            expected_graph_indexing_artifact_digest=graph_indexing[
                "graph_indexing_artifact"
            ]["artifact_digest"],
            expected_canonical_promotion_candidate_digest=design[
                "future_canonical_promotion_candidate_digest"
            ],
            expected_canonical_promotion_approval_request_digest=expected_request_digest,
            expected_canonical_promotion_approval_decision_digest=consumption[
                "approval_decision_digest"
            ],
            approval_consumption_artifact_path=consumption[
                "approval_consumption_artifact_path"
            ],
            expected_canonical_promotion_approval_consumption_digest=consumption[
                "approval_consumption_digest"
            ],
            expected_canonical_promotion_digest=preview["canonical_promotion_digest"],
            operator_statement=preview["required_operator_statement"],
            promoted_by=promoted_by,
            write_canonical_promotion_marker=True,
            write_canonical_knowledge_note=True,
            write_canonical_knowledge_index=True,
            write_canonical_promotion_artifact=True,
        ),
    )
    result["_proof_context"] = {
        "readiness": readiness,
        "design": design,
        "approval_request": approval_request,
        "approval_decision": decision,
        "approval_consumption": consumption,
    }
    return result


def _verify_outputs(
    *,
    vault: Path,
    html_path: Path,
    content_path: str,
    source_intelligence: dict[str, Any],
    graph_indexing: dict[str, Any],
    canonical: dict[str, Any],
) -> dict[str, Any]:
    ingestion = source_intelligence["ingestion"]
    source_package_path = ingestion["source_intelligence_core_source_package_path"]
    ingestion_artifact_path = ingestion["source_intelligence_core_ingestion_artifact_path"]
    canonical_note_path = canonical["canonical_knowledge_note_path"]
    canonical_artifact_path = canonical["canonical_promotion_artifact_path"]

    capture_markdown = _read_text(vault / content_path)
    source_package = _load_json(vault / source_package_path)
    ingestion_artifact = _load_json(vault / ingestion_artifact_path)
    canonical_note = _read_text(vault / canonical_note_path)
    canonical_artifact = _load_json(vault / canonical_artifact_path)

    checks = {
        "controlled_html_artifact_exists": html_path.is_file(),
        "capture_markdown_exists": (vault / content_path).is_file(),
        "capture_markdown_contains_example_domain": "Example Domain" in capture_markdown,
        "source_package_exists": (vault / source_package_path).is_file(),
        "source_package_has_source_text_quality": bool(source_package.get("source_text_quality")),
        "source_package_builder_metadata_has_source_text_quality": bool(
            (source_package.get("_builder_meta") or {}).get("source_text_quality")
        ),
        "ingestion_artifact_exists": (vault / ingestion_artifact_path).is_file(),
        "ingestion_artifact_has_source_text_quality": bool(
            ingestion_artifact.get("source_text_quality")
        ),
        "ingestion_result_has_source_text_quality": bool(ingestion.get("source_text_quality")),
        "graph_indexing_artifact_exists": (
            vault / graph_indexing["graph_indexing_artifact_path"]
        ).is_file(),
        "graph_snapshot_exists": (vault / graph_indexing["graph_snapshot_path"]).is_file(),
        "canonical_note_exists": (vault / canonical_note_path).is_file(),
        "canonical_note_has_source_text_quality_section": "## Source Text Quality"
        in canonical_note,
        "canonical_note_has_display_digest": "Display markdown digest" in canonical_note,
        "canonical_artifact_exists": (vault / canonical_artifact_path).is_file(),
        "canonical_artifact_has_source_text_quality": bool(
            canonical_artifact.get("source_text_quality")
        ),
        "canonical_artifact_display_digest_matches_result": canonical_artifact.get(
            "source_markdown_display_digest"
        )
        == canonical.get("source_markdown_display_digest"),
        "canonical_promotion_completed": canonical.get("canonical_promotion_performed")
        is True,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "source_text_quality": ingestion.get("source_text_quality") or {},
        "paths_verified": {
            "capture_markdown_path": content_path,
            "source_package_path": source_package_path,
            "source_intelligence_core_ingestion_artifact_path": ingestion_artifact_path,
            "graph_indexing_artifact_path": graph_indexing["graph_indexing_artifact_path"],
            "graph_snapshot_path": graph_indexing["graph_snapshot_path"],
            "canonical_knowledge_note_path": canonical_note_path,
            "canonical_promotion_artifact_path": canonical_artifact_path,
        },
    }


def _write_proof_artifacts(vault: Path, proof: dict[str, Any]) -> dict[str, str]:
    run_id = proof["run_id"]
    root = vault / PROOF_ROOT
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"2026-05-27-codex-markdown-capture-real-chain-{run_id}.json"
    markdown_path = root / f"2026-05-27-codex-markdown-capture-real-chain-{run_id}.md"
    proof_paths = {
        "proof_json_path": _rel(json_path, vault),
        "proof_markdown_path": _rel(markdown_path, vault),
    }
    payload = dict(proof)
    payload["proof_artifacts"] = proof_paths

    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_proof_markdown(payload), encoding="utf-8")
    return proof_paths


def _proof_markdown(proof: dict[str, Any]) -> str:
    verification = proof["verification"]
    paths = verification["paths_verified"]
    quality = verification.get("source_text_quality") or {}
    checks = verification["checks"]
    check_labels = {
        "controlled_html_artifact_exists": "controlled saved web artifact exists",
        "capture_markdown_exists": "Capture Markdown file exists",
        "capture_markdown_contains_example_domain": "Capture Markdown contains Example Domain",
        "source_package_exists": "source package exists",
        "source_package_has_source_text_quality": "source package has source text quality",
        "source_package_builder_metadata_has_source_text_quality": (
            "source package builder metadata has source text quality"
        ),
        "ingestion_artifact_exists": "Source Intelligence Core ingestion artifact exists",
        "ingestion_artifact_has_source_text_quality": (
            "Source Intelligence Core ingestion artifact has source text quality"
        ),
        "ingestion_result_has_source_text_quality": (
            "Source Intelligence Core ingestion result has source text quality"
        ),
        "graph_indexing_artifact_exists": "graph indexing artifact exists",
        "graph_snapshot_exists": "graph snapshot exists",
        "canonical_note_exists": "canonical note exists",
        "canonical_note_has_source_text_quality_section": (
            "canonical note has source text quality section"
        ),
        "canonical_note_has_display_digest": "canonical note has display digest",
        "canonical_artifact_exists": "canonical artifact exists",
        "canonical_artifact_has_source_text_quality": (
            "canonical artifact has source text quality"
        ),
        "canonical_artifact_display_digest_matches_result": (
            "canonical artifact display digest matches result"
        ),
        "canonical_promotion_completed": "canonical promotion completed",
    }
    check_lines = [
        f"- [{'x' if ok else ' '}] {check_labels.get(name, name.replace('_', ' '))}"
        for name, ok in checks.items()
    ]
    return "\n".join(
        [
            "# Capture to Markdown Real Web Replay Proof",
            "",
            f"- Status: {proof['status']}",
            f"- Source URL: {proof['source_url']}",
            f"- Controlled web artifact: `{proof['controlled_html_artifact_path']}`",
            f"- Capture Markdown: `{paths['capture_markdown_path']}`",
            f"- Source package: `{paths['source_package_path']}`",
            "- Source Intelligence Core ingestion artifact: "
            f"`{paths['source_intelligence_core_ingestion_artifact_path']}`",
            f"- Graph indexing artifact: `{paths['graph_indexing_artifact_path']}`",
            f"- Graph snapshot: `{paths['graph_snapshot_path']}`",
            f"- Canonical knowledge note: `{paths['canonical_knowledge_note_path']}`",
            f"- Canonical promotion artifact: `{paths['canonical_promotion_artifact_path']}`",
            "",
            "## Source Text Quality",
            "",
            f"- Policy: `{quality.get('policy_id', '')}`",
            f"- Encoding repair applied: `{quality.get('encoding_repair_applied')}`",
            "- Replacement count: "
            f"`{quality.get('encoding_repair_replacement_count', quality.get('replacement_count'))}`",
            f"- Normalized text digest: `{quality.get('normalized_text_sha256', '')}`",
            "",
            "## Verification Checks",
            "",
            *check_lines,
            "",
        ]
    )


def _agent_orchestration_summary(payload: dict[str, Any]) -> dict[str, Any]:
    full_dispatch = payload["full_dispatch"]
    return {
        "full_dispatch_artifact_path": full_dispatch.get("full_dispatch_artifact_path"),
        "full_dispatch_packet_digest": full_dispatch.get("full_dispatch_packet_digest"),
        "aor_full_dispatch_performed": full_dispatch.get("aor_full_dispatch_performed"),
        "source_pack_writeback_created": full_dispatch.get("source_pack_writeback_created"),
        "target_workspace_id": payload.get("target_workspace_id"),
    }


def _source_intelligence_summary(payload: dict[str, Any]) -> dict[str, Any]:
    ingestion = payload["ingestion"]
    return {
        "source_intelligence_core_ingestion_artifact_path": ingestion.get(
            "source_intelligence_core_ingestion_artifact_path"
        ),
        "source_intelligence_core_source_package_path": ingestion.get(
            "source_intelligence_core_source_package_path"
        ),
        "source_intelligence_core_ingestion_digest": ingestion.get(
            "source_intelligence_core_ingestion_digest"
        ),
        "source_text_quality": ingestion.get("source_text_quality"),
        "source_intelligence_core_ingestion_performed": ingestion.get(
            "source_intelligence_core_ingestion_performed"
        ),
    }


def _canonical_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_knowledge_note_path": payload.get("canonical_knowledge_note_path"),
        "canonical_promotion_artifact_path": payload.get("canonical_promotion_artifact_path"),
        "canonical_promotion_digest": payload.get("canonical_promotion_digest"),
        "canonical_promotion_performed": payload.get("canonical_promotion_performed"),
        "source_text_quality": payload.get("source_text_quality"),
    }


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": payload.get("ok"),
        "status": payload.get("status"),
        "written_paths": payload.get("written_paths", []),
        "blockers": payload.get("blockers", []),
    }


def _assert_ok(label: str, result: dict[str, Any]) -> dict[str, Any]:
    if result.get("ok") is not True:
        raise RuntimeError(f"{label} failed: {result.get('blockers') or result}")
    return result


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _rel(path: str | Path, root: Path) -> str:
    return Path(path).resolve().relative_to(root.resolve()).as_posix()


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the real web Capture to Markdown source text quality proof."
    )
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--html-path", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--allowed-origin", required=True)
    parser.add_argument("--title")
    parser.add_argument("--target-workspace-id", default=DEFAULT_TARGET_WORKSPACE_ID)
    parser.add_argument("--runtime", default=DEFAULT_RUNTIME)
    parser.add_argument("--reviewed-by", default="Codex")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    proof = run_real_chain_source_text_quality_proof(
        vault_root=args.vault_root,
        html_path=args.html_path,
        source_url=args.source_url,
        allowed_origin=args.allowed_origin,
        title=args.title,
        target_workspace_id=args.target_workspace_id,
        runtime=args.runtime,
        reviewed_by=args.reviewed_by,
    )
    if args.json:
        print(json.dumps(proof, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(
            "Capture to Markdown real web replay "
            f"{'passed' if proof['ok'] else 'failed'}: "
            f"{proof['proof_artifacts']['proof_markdown_path']}"
        )
    return 0 if proof["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
