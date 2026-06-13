"""Approved personal context import preview execution proof.

This governed executor consumes one digest-bound personal-context import preview
approval from ``StudioService`` and writes only review artifacts exactly once.
It requires the operator to provide the matching source text again so the source
digest can be verified before any raw intake file is created.

It does not create canonical personal nodes, update dashboards/indexes/projects,
apply Personal Map candidates, dispatch runtimes, call providers, write Agent
Bus tasks, or mutate runtime memory.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.personal_context_import import (
    PERSONAL_MAP_CANDIDATE_DIR,
    RAW_INTAKE_DIR,
)
from runtime.studio.personal_context_import_preview_writer import (
    APPROVAL_CLASS,
    MODEL_VERSION as WRITER_MODEL_VERSION,
    PREVIEW_ROOT,
    SURFACE_ID as WRITER_SURFACE_ID,
    _canonical_json,
    _scan_secrets,
    _sha256_text,
)
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.personal_context_import_approved_preview_execution_proof.v1"
SURFACE_ID = "studio_personal_context_import_approved_preview_execution_proof"
PASS_ID = "personal-context-import-approved-preview-execution-proof"
STATUS = "COMPLETE / APPROVED-PREVIEW ARTIFACTS WRITTEN / CANONICAL WRITES BLOCKED"
BLOCKED_STATUS = "BLOCKED / APPROVED-PREVIEW EXECUTION / NO PERSONAL CONTEXT ARTIFACT WRITE"
FAILED_STATUS = "FAILED / APPROVED-PREVIEW EXECUTION / PARTIAL ARTIFACT CHECK REQUIRED"
NEXT_RECOMMENDED_PASS = "personal-context-import-personal-map-apply-readiness"
MARKER_DIR = Path("runtime/studio/approvals/personal-context-import/_execution_markers")
PROOF_ROOT = Path("runtime/studio/context-import/execution-proofs")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"

REQUIRED_ARTIFACT_IDS = (
    "raw_context_source",
    "source_digest",
    "node_coverage_audit",
    "index_patch_preview",
    "personal_map_candidate_log",
    "personal_map_candidate_review",
    "approval_preview_packet",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in str(value or "")) or "unknown"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]  # Use Studio's durable queue writer.


def _write_text_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(content)


def _write_json_new(path: Path, payload: dict[str, Any]) -> None:
    _write_text_new(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_json_existing(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _authority(written: bool) -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "approved_preview_artifact_write_allowed": True,
        "approved_preview_artifact_write_performed": bool(written),
        "raw_context_file_write_allowed_after_source_digest_match": True,
        "source_digest_file_write_allowed": True,
        "node_coverage_audit_write_allowed": True,
        "index_patch_preview_write_allowed": True,
        "personal_map_candidate_write_allowed": True,
        "approval_preview_packet_write_allowed": True,
        "personal_map_apply_allowed": False,
        "dashboard_write_allowed": False,
        "personal_operator_index_write_allowed": False,
        "operating_system_write_allowed": False,
        "projects_hub_write_allowed": False,
        "knowledge_index_write_allowed": False,
        "root_knowledge_index_write_allowed": False,
        "node_file_creation_allowed": False,
        "canonical_mutation_allowed": False,
        "runtime_memory_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
    }


def _effect_flags(written: bool = False) -> dict[str, bool]:
    return {
        "approved_preview_artifacts_written": bool(written),
        "raw_context_file_written": bool(written),
        "source_digest_file_written": bool(written),
        "node_coverage_audit_written": bool(written),
        "index_patch_preview_written": bool(written),
        "personal_map_candidate_log_written": bool(written),
        "personal_map_candidate_review_written": bool(written),
        "approval_preview_packet_written": bool(written),
        "personal_map_applied": False,
        "dashboard_updated": False,
        "personal_operator_index_updated": False,
        "operating_system_updated": False,
        "projects_hub_updated": False,
        "knowledge_index_updated": False,
        "root_knowledge_index_updated": False,
        "node_files_created": False,
        "canonical_mutation_performed": False,
        "runtime_memory_mutated": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "provider_call_performed": False,
        "credential_value_read": False,
    }


def _load_content_payload(req: ApprovalRequest | None) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    if req is None:
        return None, None, "approval_request_missing"
    try:
        content = json.loads(str(req.action_spec.content or "{}"))
    except json.JSONDecodeError as exc:
        return None, None, f"approval_content_json_malformed:{exc}"
    if not isinstance(content, dict):
        return None, None, "approval_content_json_not_object"
    packet = content.get("proposal_packet")
    if not isinstance(packet, dict):
        return content, None, "approval_content_missing_proposal_packet"
    return content, packet, None


def _artifact_by_id(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in packet.get("planned_artifacts") or []:
        if isinstance(item, dict) and item.get("id"):
            result[str(item["id"])] = dict(item)
    return result


def _resolve_vault_relative(vault: Path, relative_path: str) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    normalized = str(relative_path or "").replace("\\", "/").strip()
    if not normalized:
        return None, ["artifact_path_required"]
    if Path(normalized).is_absolute():
        blockers.append("artifact_path_must_be_vault_relative")
    target = (vault / normalized).resolve()
    try:
        target.relative_to(vault.resolve())
    except ValueError:
        blockers.append("artifact_path_escapes_vault")
    return target, blockers


def _artifact_path_blockers(vault: Path, artifact_id: str, relative_path: str) -> tuple[Path | None, list[str]]:
    target, blockers = _resolve_vault_relative(vault, relative_path)
    normalized = str(relative_path or "").replace("\\", "/").strip()
    if artifact_id in {
        "raw_context_source",
        "source_digest",
        "node_coverage_audit",
        "index_patch_preview",
    }:
        if not normalized.startswith(f"{RAW_INTAKE_DIR}/"):
            blockers.append(f"artifact_path_not_raw_intake:{artifact_id}")
        if not normalized.endswith(".md"):
            blockers.append(f"artifact_path_not_markdown:{artifact_id}")
    elif artifact_id == "personal_map_candidate_log":
        if not normalized.startswith(f"{PERSONAL_MAP_CANDIDATE_DIR}/"):
            blockers.append("artifact_path_not_personal_map_candidates:personal_map_candidate_log")
        if not normalized.endswith(".jsonl"):
            blockers.append("artifact_path_not_jsonl:personal_map_candidate_log")
    elif artifact_id == "personal_map_candidate_review":
        if not normalized.startswith(f"{PERSONAL_MAP_CANDIDATE_DIR}/"):
            blockers.append("artifact_path_not_personal_map_candidates:personal_map_candidate_review")
        if not normalized.endswith(".md"):
            blockers.append("artifact_path_not_markdown:personal_map_candidate_review")
    elif artifact_id == "approval_preview_packet":
        if not normalized.startswith(f"{PREVIEW_ROOT}/"):
            blockers.append("artifact_path_not_context_import_preview_root:approval_preview_packet")
        if not normalized.endswith(".json"):
            blockers.append("artifact_path_not_json:approval_preview_packet")
    else:
        blockers.append(f"artifact_id_not_allowed:{artifact_id}")
    return target, blockers


def _planned_output_paths(
    *,
    vault: Path,
    approval_id: str,
    packet: dict[str, Any] | None,
) -> tuple[dict[str, Path], list[str]]:
    blockers: list[str] = []
    outputs: dict[str, Path] = {}
    artifacts = _artifact_by_id(packet or {})

    for artifact_id in REQUIRED_ARTIFACT_IDS:
        item = artifacts.get(artifact_id)
        if not item:
            blockers.append(f"planned_artifact_missing:{artifact_id}")
            continue
        target, item_blockers = _artifact_path_blockers(vault, artifact_id, str(item.get("path") or ""))
        blockers.extend(item_blockers)
        if target is not None:
            outputs[artifact_id] = target

    proof_dir = (vault / PROOF_ROOT / _safe_id(approval_id)).resolve()
    try:
        proof_dir.relative_to((vault / PROOF_ROOT).resolve())
    except ValueError:
        blockers.append("execution_proof_path_escapes_proof_root")
    outputs["artifact_manifest"] = proof_dir / "artifact-manifest.json"
    outputs["rollback_plan"] = proof_dir / "rollback-plan.json"
    outputs["execution_evidence"] = proof_dir / "execution-evidence.json"
    return outputs, blockers


def _content_blockers(
    *,
    req: ApprovalRequest | None,
    content: dict[str, Any] | None,
    packet: dict[str, Any] | None,
    expected_import_preview_digest: str,
    source_digest_sha256: str,
) -> list[str]:
    blockers: list[str] = []
    if req is None:
        return ["approval_not_found"]
    metadata = req.action_spec.metadata or {}
    content = content or {}
    packet = packet or {}
    packet_digest = str(packet.get("import_preview_digest") or "")
    metadata_digest = str(metadata.get("personal_context_import_preview_digest") or "")
    metadata_source_digest = str(metadata.get("personal_context_import_source_sha256") or "")
    packet_source_digest = str(packet.get("source_digest_sha256") or "")
    target_path = str(req.action_spec.target_path or "").replace("\\", "/")
    packet_target = str(packet.get("target_path") or "").replace("\\", "/")

    if req.status not in {"pending", "approved"}:
        blockers.append(f"approval_status_not_pending_or_approved:{req.status}")
    if req.action_spec.action_type != "create_file":
        blockers.append("approval_action_type_not_context_import_preview_create_file")
    if metadata.get("personal_context_import_preview_writer") is not True:
        blockers.append("approval_not_personal_context_import_preview_writer_artifact")
    if metadata.get("personal_context_import_preview_execution_blocked") is not True:
        blockers.append("approval_missing_preview_execution_block")
    if metadata.get("source_surface") != WRITER_SURFACE_ID:
        blockers.append("approval_source_surface_not_preview_writer")
    if metadata.get("required_approval_class") != APPROVAL_CLASS:
        blockers.append("approval_class_mismatch")
    if content.get("record_type") != "personal_context_import_preview_packet":
        blockers.append("approval_content_record_type_mismatch")
    if content.get("schema_version") != WRITER_MODEL_VERSION:
        blockers.append("approval_content_writer_schema_mismatch")
    if content.get("source_text_included") is not False:
        blockers.append("approval_content_source_text_included")
    if content.get("raw_source_text_included") is not False:
        blockers.append("approval_content_raw_source_text_included")
    if content.get("future_executor_requires_matching_source_digest") is not True:
        blockers.append("approval_content_missing_source_digest_requirement")
    if packet.get("source_text_included") is not False:
        blockers.append("proposal_packet_source_text_included")
    if target_path != packet_target:
        blockers.append("approval_target_path_content_mismatch")
    if not expected_import_preview_digest:
        blockers.append("expected_import_preview_digest_required")
    elif packet_digest and packet_digest != expected_import_preview_digest:
        blockers.append("expected_import_preview_digest_mismatch")
    if metadata_digest and packet_digest and metadata_digest != packet_digest:
        blockers.append("approval_metadata_packet_digest_mismatch")
    if metadata_digest and expected_import_preview_digest and metadata_digest != expected_import_preview_digest:
        blockers.append("approval_metadata_expected_digest_mismatch")
    if not packet_digest:
        blockers.append("proposal_packet_import_preview_digest_missing")
    if not packet_source_digest:
        blockers.append("proposal_packet_source_digest_missing")
    if metadata_source_digest and packet_source_digest and metadata_source_digest != packet_source_digest:
        blockers.append("approval_metadata_packet_source_digest_mismatch")
    if source_digest_sha256 and packet_source_digest and source_digest_sha256 != packet_source_digest:
        blockers.append("source_digest_mismatch")

    for key, expected in {
        "raw_context_file_written": False,
        "source_digest_file_written": False,
        "node_coverage_audit_written": False,
        "index_patch_preview_written": False,
        "personal_map_candidates_written": False,
        "dashboard_updated": False,
        "personal_operator_index_updated": False,
        "projects_hub_updated": False,
        "knowledge_index_updated": False,
        "provider_call_performed": False,
        "agent_bus_task_written": False,
        "runtime_memory_mutated": False,
        "canonical_mutation_allowed": False,
    }.items():
        if key in packet and bool(packet.get(key)) is not expected:
            blockers.append(f"proposal_packet_effect_flag_not_false:{key}")
        if key in metadata and bool(metadata.get(key)) is not expected:
            blockers.append(f"approval_metadata_effect_flag_not_false:{key}")
    return blockers


def _statement_blockers(statement: str, expected_import_preview_digest: str) -> list[str]:
    if not statement.strip():
        return ["operator_approval_statement_required"]
    blockers: list[str] = []
    lowered = statement.lower()
    if expected_import_preview_digest and expected_import_preview_digest not in statement:
        blockers.append("operator_approval_statement_digest_missing")
    if "approve" not in lowered or "personal context" not in lowered:
        blockers.append("operator_approval_statement_phrase_missing")
    return blockers


def _summary(
    *,
    approval_id: str,
    packet: dict[str, Any] | None,
    expected_import_preview_digest: str,
    source_digest_sha256: str,
    approval_status: str | None = None,
    operator_approval_recorded: bool = False,
    approval_consumed: bool = False,
    exact_once_marker_written: bool = False,
    artifact_count: int = 0,
    duplicate_blocked_before_artifact_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    packet = packet or {}
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded,
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "expected_import_preview_digest_provided": bool(expected_import_preview_digest),
        "import_preview_digest": packet.get("import_preview_digest"),
        "source_digest_sha256": source_digest_sha256 or packet.get("source_digest_sha256"),
        "proposal_id": packet.get("proposal_id"),
        "node_proposal_count": len(packet.get("node_proposals") or []),
        "edge_proposal_count": len(packet.get("edge_proposals") or []),
        "index_patch_target_count": len(packet.get("index_patch_plan") or []),
        "artifact_count": artifact_count,
        "duplicate_blocked_before_artifact_write": duplicate_blocked_before_artifact_write,
        **_effect_flags(written=artifact_count > 0 and approval_consumed),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_import_preview_digest: str,
    source_digest_sha256: str,
    packet: dict[str, Any] | None,
    marker_path: Path,
    output_paths: dict[str, Path],
    blockers: list[str],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": BLOCKED_STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=approval_id,
            packet=packet,
            expected_import_preview_digest=expected_import_preview_digest,
            source_digest_sha256=source_digest_sha256,
            duplicate_blocked_before_artifact_write="exact_once_marker_already_present" in unique,
            blocker_count=len(unique),
        ),
        "digest_proof": {
            "expected_import_preview_digest": expected_import_preview_digest or None,
            "import_preview_digest": (packet or {}).get("import_preview_digest"),
            "import_preview_digest_matched": False,
            "source_digest_sha256": source_digest_sha256 or None,
            "source_digest_matched": False,
            "executor_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": False,
            "duplicate_blocked_before_artifact_write": "exact_once_marker_already_present" in unique,
        },
        "artifact_writes": {
            "artifact_paths": {key: _rel(vault, value) for key, value in sorted(output_paths.items())},
            "artifact_count": 0,
            **_effect_flags(False),
        },
        "execution_record": {
            "execution_id": None,
            "execution_status": None,
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(False),
        "blocked_reasons": unique,
    }


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    import_preview_digest: str,
    executor_digest: str,
    source_digest_sha256: str,
    operator_id: str,
    written_artifacts: list[str],
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "personal_context_import_approved_preview_execution_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "import_preview_digest": import_preview_digest,
        "executor_digest": executor_digest,
        "source_digest_sha256": source_digest_sha256,
        "operator_id": operator_id,
        "written_artifacts": written_artifacts,
        **_effect_flags(written=bool(written_artifacts) and status == "executed"),
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    escaped = [[" ".join(str(cell).replace("|", "\\|").split()) for cell in row] for row in rows]
    widths = [max(len(row[index]) for row in escaped) for index in range(len(escaped[0]))]
    lines: list[str] = []
    for row_index, row in enumerate(escaped):
        line = "| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)) + " |"
        lines.append(line)
        if row_index == 0:
            lines.append("| " + " | ".join("-" * widths[index] for index in range(len(row))) + " |")
    return "\n".join(lines)


def _render_raw_source(
    *,
    source_text: str,
    packet: dict[str, Any],
    approval_id: str,
    execution_id: str,
) -> str:
    return f"""---
type: personal-context-raw-source
trust: TIER 4 RAW INPUT
approval_id: {approval_id}
execution_id: {execution_id}
proposal_id: {packet.get("proposal_id")}
import_preview_digest: {packet.get("import_preview_digest")}
source_digest_sha256: {packet.get("source_digest_sha256")}
canonical_mutation_performed: false
personal_map_applied: false
---

# Personal Context Source

This raw source was written only after a digest-bound approval was consumed by
`{SURFACE_ID}`. It is Tier 4 raw input and must not be treated as canonical
truth until reviewed and promoted through governed ChaseOS writeback.

## Source Text

{source_text.rstrip()}
"""


def _render_source_digest(
    *,
    packet: dict[str, Any],
    approval_id: str,
    execution_id: str,
    source_text_sha256: str,
) -> str:
    stats = packet.get("source_stats") if isinstance(packet.get("source_stats"), dict) else {}
    rows = [
        ["Field", "Value"],
        ["Approval id", approval_id],
        ["Execution id", execution_id],
        ["Proposal id", str(packet.get("proposal_id") or "")],
        ["Import preview digest", str(packet.get("import_preview_digest") or "")],
        ["Source digest sha256", source_text_sha256],
        ["Source chars", str(stats.get("source_chars") or "")],
        ["Source lines", str(stats.get("source_lines") or "")],
        ["Source words", str(stats.get("source_words") or "")],
        ["Node proposals", str(len(packet.get("node_proposals") or []))],
        ["Edge proposals", str(len(packet.get("edge_proposals") or []))],
        ["Canonical writes", "false"],
        ["Personal Map applied", "false"],
    ]
    return (
        "# Personal Context Source Digest\n\n"
        "Digest proof for the approved personal-context import preview execution.\n\n"
        f"{_md_table(rows)}\n\n"
        "## Boundary\n\n"
        "This file proves source matching and artifact staging only. It does not make "
        "the imported profile canonical.\n"
    )


def _render_node_coverage(packet: dict[str, Any]) -> str:
    rows = [["Rule", "Label", "Parent", "Target", "Matched Terms", "State"]]
    for node in packet.get("node_proposals") or []:
        if not isinstance(node, dict):
            continue
        rows.append(
            [
                str(node.get("rule_id") or ""),
                str(node.get("label") or ""),
                str(node.get("parent_path") or ""),
                str(node.get("target_path") or ""),
                ", ".join(str(item) for item in node.get("matched_terms") or []),
                str(node.get("write_state") or "proposed_only"),
            ]
        )
    return (
        "# Personal Context Node Coverage Audit\n\n"
        "Source-derived parent/child route proposals staged for review. No node file, "
        "dashboard, project hub, knowledge index, or Personal Map apply write was performed.\n\n"
        f"{_md_table(rows)}\n"
    )


def _render_index_patch_preview(packet: dict[str, Any]) -> str:
    rows = [["Target", "Operation", "State", "Review Required"]]
    for item in packet.get("index_patch_plan") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            [
                str(item.get("target_path") or ""),
                str(item.get("operation") or ""),
                str(item.get("write_state") or "proposed_only"),
                str(bool(item.get("requires_operator_review", True))).lower(),
            ]
        )
    return (
        "# Personal Context Index Patch Preview\n\n"
        "Proposed routing targets only. This preview intentionally avoids direct writes "
        "to `00_HOME`, `01_PROJECTS`, `02_KNOWLEDGE`, `06_AGENTS`, `SOUL.md`, and "
        "`KNOWLEDGE-INDEX.md`.\n\n"
        f"{_md_table(rows)}\n"
    )


def _candidate_records(
    *,
    packet: dict[str, Any],
    approval_id: str,
    execution_id: str,
    source_digest_sha256: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    digest = str(packet.get("import_preview_digest") or "")
    for node in packet.get("node_proposals") or []:
        if not isinstance(node, dict):
            continue
        records.append(
            {
                "candidate_id": f"{packet.get('proposal_id')}:node:{node.get('rule_id')}",
                "candidate_type": "personal_context_node_route_candidate",
                "approval_id": approval_id,
                "execution_id": execution_id,
                "import_preview_digest": digest,
                "source_digest_sha256": source_digest_sha256,
                "label": node.get("label"),
                "family": node.get("family"),
                "parent_path": node.get("parent_path"),
                "target_path": node.get("target_path"),
                "target_kind": node.get("target_kind"),
                "matched_terms": node.get("matched_terms") or [],
                "status": "pending_review",
                "canonical": False,
                "applied": False,
            }
        )
    for edge in packet.get("edge_proposals") or []:
        if not isinstance(edge, dict):
            continue
        records.append(
            {
                "candidate_id": f"{packet.get('proposal_id')}:{edge.get('id')}",
                "candidate_type": "personal_context_graph_edge_candidate",
                "approval_id": approval_id,
                "execution_id": execution_id,
                "import_preview_digest": digest,
                "source_digest_sha256": source_digest_sha256,
                "source": edge.get("source"),
                "target": edge.get("target"),
                "relation": edge.get("relation"),
                "family": edge.get("family"),
                "status": "pending_review",
                "canonical": False,
                "applied": False,
            }
        )
    return records


def _render_candidate_jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n" for record in records)


def _render_candidate_review(packet: dict[str, Any], records: list[dict[str, Any]]) -> str:
    rows = [["Type", "Family", "Target", "State"]]
    for record in records:
        rows.append(
            [
                str(record.get("candidate_type") or ""),
                str(record.get("family") or ""),
                str(record.get("target_path") or record.get("target") or ""),
                str(record.get("status") or ""),
            ]
        )
    return (
        "# Personal Context Candidate Review\n\n"
        "Review deck for source-derived Personal Map and graph route candidates. "
        "Candidates are staged only; no apply step has run.\n\n"
        f"- Proposal id: `{packet.get('proposal_id')}`\n"
        f"- Import preview digest: `{packet.get('import_preview_digest')}`\n"
        f"- Candidate count: `{len(records)}`\n"
        "- Canonical mutation performed: `false`\n"
        "- Personal Map applied: `false`\n\n"
        f"{_md_table(rows)}\n"
    )


def _preview_packet_payload(
    *,
    packet: dict[str, Any],
    approval_id: str,
    execution_id: str,
    executor_digest: str,
) -> dict[str, Any]:
    payload = dict(packet)
    payload.update(
        {
            "status": "approved_preview_artifacts_recorded",
            "approval_id": approval_id,
            "approval_consumed": True,
            "approval_consumed_by": SURFACE_ID,
            "approval_execution_id": execution_id,
            "executor_digest": executor_digest,
            "next_required_pass": NEXT_RECOMMENDED_PASS,
            **_effect_flags(written=True),
        }
    )
    return payload


def _artifact_manifest_payload(
    *,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    source_digest_sha256: str,
    packet: dict[str, Any],
    written_paths: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "personal_context_import_artifact_manifest.v1",
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "executor_digest": executor_digest,
        "proposal_id": packet.get("proposal_id"),
        "import_preview_digest": packet.get("import_preview_digest"),
        "source_digest_sha256": source_digest_sha256,
        "written_artifacts": written_paths,
        "artifact_count": len(written_paths),
        **_effect_flags(written=True),
        "generated_at_utc": _now_utc(),
    }


def _rollback_plan_payload(
    *,
    approval_id: str,
    execution_id: str,
    written_paths: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "personal_context_import_artifact_rollback_plan.v1",
        "surface": SURFACE_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "rollback_scope": "review_artifacts_only",
        "manual_review_required_before_removal": True,
        "paths_created_by_execution": written_paths,
        "canonical_nodes_to_revert": [],
        "dashboard_or_index_writes_to_revert": [],
        "personal_map_apply_to_revert": [],
        "runtime_memory_to_revert": [],
        "created_at_utc": _now_utc(),
    }


def _execution_evidence_payload(
    *,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    packet: dict[str, Any],
    source_digest_sha256: str,
    output_paths: dict[str, Path],
    vault: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "personal_context_import_execution_evidence.v1",
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "executor_digest": executor_digest,
        "proposal_id": packet.get("proposal_id"),
        "import_preview_digest": packet.get("import_preview_digest"),
        "source_digest_sha256": source_digest_sha256,
        "source_digest_matched": source_digest_sha256 == packet.get("source_digest_sha256"),
        "output_paths": {key: _rel(vault, value) for key, value in sorted(output_paths.items())},
        "node_proposal_count": len(packet.get("node_proposals") or []),
        "edge_proposal_count": len(packet.get("edge_proposals") or []),
        "index_patch_target_count": len(packet.get("index_patch_plan") or []),
        **_effect_flags(written=True),
        "generated_at_utc": _now_utc(),
    }


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    import_preview_digest: str,
    source_digest_sha256: str,
    written_paths: list[str],
    operator_id: str,
) -> str:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{executor_digest[:20]}.md"
    path = base
    counter = 1
    while path.exists():
        counter += 1
        path = root / f"{PASS_ID}-{executor_digest[:20]}-{counter}.md"
    writes = "\n".join(f"- `{item}`" for item in written_paths) or "- none"
    path.write_text(
        f"""---
type: agent-activity
runtime: Codex
surface: {SURFACE_ID}
approval_id: {approval_id}
execution_id: {execution_id}
status: executed
---

# Personal Context Import Approved Preview Execution

Runtime: Codex
Task type: approved preview artifact execution proof
Operator id: `{operator_id}`
Import preview digest: `{import_preview_digest}`
Source digest sha256: `{source_digest_sha256}`
Executor digest: `{executor_digest}`

## Writes

{writes}

## Boundary

This pass consumed a digest-bound approval and wrote review artifacts only. It
did not create canonical nodes, update dashboard/index/project truth, apply
Personal Map candidates, dispatch runtimes, call providers, write Agent Bus
tasks, read credentials, or mutate runtime memory.
""",
        encoding="utf-8",
    )
    return _rel(vault, path)


def execute_personal_context_import_approved_preview_execution_proof(
    vault_root: str | Path,
    *,
    approval_id: str,
    expected_import_preview_digest: str,
    source_text: str,
    operator_approval_statement: str = "",
    operator_id: str = "studio-operator",
    execute: bool = False,
) -> dict[str, Any]:
    """Consume an approved context-import preview request and write artifacts once."""

    vault = Path(vault_root).resolve()
    requested_approval_id = str(approval_id or "").strip()
    expected = str(expected_import_preview_digest or "").strip()
    source = str(source_text or "")
    statement = str(operator_approval_statement or "")
    operator = str(operator_id or "studio-operator")
    source_digest = _sha256_text(source) if source else ""
    marker_path = (vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json").resolve()

    blockers: list[str] = []
    if not requested_approval_id:
        blockers.append("approval_id_required")
    if not expected:
        blockers.append("expected_import_preview_digest_required")
    if not source.strip():
        blockers.append("source_text_required")
    if not execute:
        blockers.append("execute_flag_required")

    secret_screen = _scan_secrets(source)
    if secret_screen["contains_secret"]:
        blockers.append("secret_or_credential_indicator_present")

    service = StudioService(vault)
    req = service.get_approval(requested_approval_id) if requested_approval_id else None
    content, packet, content_error = _load_content_payload(req)
    if content_error:
        blockers.append(content_error)

    outputs, output_blockers = _planned_output_paths(vault=vault, approval_id=requested_approval_id, packet=packet)
    blockers.extend(output_blockers)
    blockers.extend(
        _content_blockers(
            req=req,
            content=content,
            packet=packet,
            expected_import_preview_digest=expected,
            source_digest_sha256=source_digest,
        )
    )
    blockers.extend(_statement_blockers(statement, expected))

    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")
    for path in outputs.values():
        if path.exists():
            blockers.append(f"preview_output_collision:{_rel(vault, path)}")

    hard_blockers = list(dict.fromkeys(blockers))
    if hard_blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_import_preview_digest=expected,
            source_digest_sha256=source_digest,
            packet=packet,
            marker_path=marker_path,
            output_paths=outputs,
            blockers=hard_blockers,
        )

    assert req is not None
    assert packet is not None
    assert content is not None

    approved_content = str(req.action_spec.content or "")
    executor_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": requested_approval_id,
        "import_preview_digest": expected,
        "source_digest_sha256": source_digest,
        "approval_content_sha256": hashlib.sha256(approved_content.encode("utf-8")).hexdigest(),
        "output_paths": {key: _rel(vault, value) for key, value in sorted(outputs.items())},
    }
    executor_digest = _sha256_text(_canonical_json(executor_material))
    execution_id = f"personal-context-preview-execution-{executor_digest[:20]}"
    written_paths: list[str] = []
    approval_recorded_from_statement = False

    try:
        if req.status == "pending":
            req.status = "approved"
            req.reviewed_by = operator
            req.reason = statement
            req.updated_at = _now_utc()
            _write_approval(service, req)
            approval_recorded_from_statement = True

        req.status = "executing"
        req.execution_id = execution_id
        req.execution_started_at = _now_utc()
        req.execution_finished_at = None
        req.execution_status = None
        req.result_action_id = None
        req.execution_error = ""
        req.updated_at = req.execution_started_at
        _write_approval(service, req)

        _write_json_new(
            marker_path,
            _marker_payload(
                status="executing",
                approval_id=requested_approval_id,
                execution_id=execution_id,
                import_preview_digest=expected,
                executor_digest=executor_digest,
                source_digest_sha256=source_digest,
                operator_id=operator,
                written_artifacts=[],
            ),
        )

        records = _candidate_records(
            packet=packet,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            source_digest_sha256=source_digest,
        )
        content_by_id = {
            "approval_preview_packet": json.dumps(
                _preview_packet_payload(
                    packet=packet,
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    executor_digest=executor_digest,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            "raw_context_source": _render_raw_source(
                source_text=source,
                packet=packet,
                approval_id=requested_approval_id,
                execution_id=execution_id,
            ),
            "source_digest": _render_source_digest(
                packet=packet,
                approval_id=requested_approval_id,
                execution_id=execution_id,
                source_text_sha256=source_digest,
            ),
            "node_coverage_audit": _render_node_coverage(packet),
            "index_patch_preview": _render_index_patch_preview(packet),
            "personal_map_candidate_log": _render_candidate_jsonl(records),
            "personal_map_candidate_review": _render_candidate_review(packet, records),
        }

        for artifact_id in REQUIRED_ARTIFACT_IDS:
            target = outputs[artifact_id]
            _write_text_new(target, content_by_id[artifact_id])
            written_paths.append(_rel(vault, target))

        manifest_payload = _artifact_manifest_payload(
            approval_id=requested_approval_id,
            execution_id=execution_id,
            executor_digest=executor_digest,
            source_digest_sha256=source_digest,
            packet=packet,
            written_paths=written_paths,
        )
        _write_json_new(outputs["artifact_manifest"], manifest_payload)
        written_paths.append(_rel(vault, outputs["artifact_manifest"]))
        _write_json_new(
            outputs["rollback_plan"],
            _rollback_plan_payload(
                approval_id=requested_approval_id,
                execution_id=execution_id,
                written_paths=written_paths,
            ),
        )
        written_paths.append(_rel(vault, outputs["rollback_plan"]))
        _write_json_new(
            outputs["execution_evidence"],
            _execution_evidence_payload(
                approval_id=requested_approval_id,
                execution_id=execution_id,
                executor_digest=executor_digest,
                packet=packet,
                source_digest_sha256=source_digest,
                output_paths=outputs,
                vault=vault,
            ),
        )
        written_paths.append(_rel(vault, outputs["execution_evidence"]))

        _write_json_existing(
            marker_path,
            _marker_payload(
                status="executed",
                approval_id=requested_approval_id,
                execution_id=execution_id,
                import_preview_digest=expected,
                executor_digest=executor_digest,
                source_digest_sha256=source_digest,
                operator_id=operator,
                written_artifacts=written_paths,
            ),
        )

        req.status = "executed"
        req.execution_finished_at = _now_utc()
        req.execution_status = "completed"
        req.result_action_id = execution_id
        req.execution_error = ""
        req.updated_at = req.execution_finished_at
        metadata = dict(req.action_spec.metadata or {})
        metadata.update(
            {
                "personal_context_import_approved_preview_execution_proof": True,
                "personal_context_import_approved_preview_executor_digest": executor_digest,
                "approval_consumed": True,
                "source_digest_matched": True,
                "next_required_pass": NEXT_RECOMMENDED_PASS,
                **_effect_flags(written=True),
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            executor_digest=executor_digest,
            import_preview_digest=expected,
            source_digest_sha256=source_digest,
            written_paths=written_paths,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            existing_writes = [item for item in written_paths if (vault / item).exists()]
            _write_json_existing(
                marker_path,
                _marker_payload(
                    status="execution_failed",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    import_preview_digest=expected,
                    executor_digest=executor_digest,
                    source_digest_sha256=source_digest,
                    operator_id=operator,
                    written_artifacts=existing_writes,
                    error=error,
                ),
            )
            req.status = "execution_failed"
            req.execution_finished_at = _now_utc()
            req.execution_status = "error"
            req.result_action_id = execution_id
            req.execution_error = error
            req.updated_at = req.execution_finished_at
            _write_approval(service, req)
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_import_preview_digest=expected,
            source_digest_sha256=source_digest,
            packet=packet,
            marker_path=marker_path,
            output_paths=outputs,
            blockers=[f"personal_context_import_preview_execution_failed:{error}"],
        )
        failed["status"] = FAILED_STATUS
        return failed

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=requested_approval_id,
            packet=packet,
            expected_import_preview_digest=expected,
            source_digest_sha256=source_digest,
            approval_status="executed",
            operator_approval_recorded=approval_recorded_from_statement,
            approval_consumed=True,
            exact_once_marker_written=True,
            artifact_count=len(written_paths),
            blocker_count=0,
        ),
        "digest_proof": {
            "expected_import_preview_digest": expected,
            "import_preview_digest": packet.get("import_preview_digest"),
            "import_preview_digest_matched": expected == packet.get("import_preview_digest"),
            "source_digest_sha256": source_digest,
            "source_digest_matched": source_digest == packet.get("source_digest_sha256"),
            "approval_content_sha256": hashlib.sha256(approved_content.encode("utf-8")).hexdigest(),
            "executor_digest": executor_digest,
            "executor_digest_material": executor_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": requested_approval_id,
                        "execution_id": execution_id,
                        "executor_digest": executor_digest,
                        "written_paths": written_paths,
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": True,
            "marker_status": "executed",
            "duplicate_blocked_before_artifact_write": True,
        },
        "artifact_writes": {
            "artifact_paths": {key: _rel(vault, value) for key, value in sorted(outputs.items())},
            "written_paths": written_paths,
            "artifact_count": len(written_paths),
            **_effect_flags(written=True),
        },
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
            "approval_status": "executed",
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(True),
        "blocked_reasons": [],
    }


def format_personal_context_import_approved_preview_execution_proof(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    marker = payload.get("exact_once_marker") or {}
    artifacts = payload.get("artifact_writes") or {}
    lines = [
        "Personal Context Import Approved Preview Execution Proof",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Import preview digest: {digest.get('import_preview_digest') or 'missing'}",
        f"Source digest matched: {digest.get('source_digest_matched')}",
        f"Executor digest: {digest.get('executor_digest') or 'missing'}",
        f"Marker written: {marker.get('marker_written')}",
        f"Artifact count: {artifacts.get('artifact_count') or 0}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: approved preview artifacts only; no canonical nodes, dashboard, "
        "personal operator index, projects hub, knowledge index, Personal Map apply, "
        "runtime dispatch, Agent Bus task, provider call, credential read, or runtime "
        "memory mutation."
    )
    return "\n".join(lines)
