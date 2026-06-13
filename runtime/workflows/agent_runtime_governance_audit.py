"""VentureOps agent runtime governance audit workflow.

This is the first executable VentureOps workflow slice. It ingests declared
local ChaseOS governance/runtime files, summarizes permission posture, and
returns a proof-card writeback for AOR Stage 7. It does not call providers,
open browsers, send messages, read secrets, or mutate canonical state.
"""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.ventureops.proof_cards import build_proof_card
from runtime.ventureops.validation import (
    validate_agent_scorecard,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
)


WORKFLOW_ID = "agent_runtime_governance_audit"
SECRET_PATH_TOKENS = (
    ".env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "token",
    "private_key",
    "seed",
    "wallet",
    "cookie",
)
DEFAULT_SOURCE_PATHS = (
    "06_AGENTS/Agent-Control-Plane.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
    "06_AGENTS/Backends-Supported.md",
    "runtime/codex/capabilities.yaml",
    "runtime/workflows/registry/use_case_registry.yaml",
)
BLOCKED_SURFACES = (
    "External send: blocked without explicit human approval",
    "Provider/model call: blocked in this workflow",
    "Browser action: blocked in this workflow",
    "Credential or secret read: blocked",
    "Canonical-state mutation: blocked",
    "Payment or CRM mutation: blocked",
    "Live trading execution: blocked",
)


class WorkflowExecutionError(Exception):
    """Fail-closed workflow error surfaced by AOR as an escalation."""


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug[:80] or "run"


def _as_source_list(value: Any) -> list[str]:
    if value is None:
        return list(DEFAULT_SOURCE_PATHS)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise WorkflowExecutionError("source_paths must be a list or comma-separated string")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_text(value: Any, *, fallback: str = "not specified") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    sanitized = re.sub(r"[\r\n]+", " ", text)
    return sanitized[:240]


def _required_safe_text(value: Any, *, field_name: str) -> str:
    text = _safe_text(value, fallback="")
    if not text:
        raise WorkflowExecutionError(f"{field_name} is required")
    return text


def _approval_decision(value: Any) -> str:
    decision = str(value or "").strip().lower()
    if decision not in {"approved", "denied"}:
        raise WorkflowExecutionError("approval_decision must be approved or denied")
    return decision


def _load_registered_actors(vault_root: Path) -> frozenset[str]:
    """Return valid approval actors: literal 'operator' plus every runtime_id in identity ledgers.

    Fail-open per ledger — a malformed or missing ledger is skipped; at minimum
    the literal 'operator' string is always valid (represents the human vault owner).
    """
    actors: set[str] = {"operator"}
    ledger_dir = vault_root / "runtime" / "memory" / "adapters"
    if not ledger_dir.exists():
        return frozenset(actors)
    for ledger_path in sorted(ledger_dir.glob("*/identity-ledger.json")):
        try:
            data = json.loads(ledger_path.read_text(encoding="utf-8"))
            runtime_id = data.get("runtime_id")
            if runtime_id and isinstance(runtime_id, str) and runtime_id.strip():
                actors.add(runtime_id.strip())
        except Exception:
            pass
    return frozenset(actors)


def _validate_actor(
    actor: str,
    vault_root: Path,
    *,
    field_name: str = "approval_decision_actor",
) -> None:
    """Fail closed: raise WorkflowExecutionError if actor is not registered."""
    registered = _load_registered_actors(vault_root)
    if actor not in registered:
        raise WorkflowExecutionError(
            f"{field_name} {actor!r} is not a registered operator or runtime; "
            f"registered: {sorted(registered)}"
        )


def _validate_source_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip().lstrip("/")
    lowered = normalized.lower()
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        raise WorkflowExecutionError(f"invalid source path: {path!r}")
    if any(token in lowered for token in SECRET_PATH_TOKENS):
        raise WorkflowExecutionError(f"refuses secret-like source path: {path}")
    return normalized


def _read_sources(vault_root: Path, source_paths: list[str]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    root = vault_root.resolve()
    for raw_path in source_paths:
        relative = _validate_source_path(raw_path)
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise WorkflowExecutionError(f"source path escapes vault root: {raw_path}") from exc
        if not path.exists() or not path.is_file():
            raise WorkflowExecutionError(f"required source path missing: {relative}")
        text = path.read_text(encoding="utf-8", errors="replace")
        sources.append(
            {
                "path": relative,
                "characters": len(text),
                "excerpt": text[:1200],
            }
        )
    return sources


def _signal_counts(text: str) -> dict[str, int]:
    lowered = text.lower()
    terms = {
        "approval": "approval",
        "secret": "secret",
        "credential": "credential",
        "external_send": "external send",
        "provider": "provider",
        "browser": "browser",
        "trading": "trading",
        "canonical": "canonical",
        "agent_bus": "agent bus",
        "write": "write",
    }
    return {key: lowered.count(term) for key, term in terms.items()}


def _build_markdown(
    *,
    run_id: str,
    run_date: str,
    sources: list[dict[str, Any]],
    aggregate_counts: dict[str, int],
    proof_card: dict[str, Any],
    proof_path: str,
    client_report_path: str,
    scorecard_path: str,
    files_written: list[str],
) -> str:
    source_lines = "\n".join(
        f"- `{source['path']}` ({source['characters']} chars ingested)"
        for source in sources
    )
    blocked_lines = "\n".join(f"- {item}" for item in BLOCKED_SURFACES)
    counts_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(aggregate_counts.items()))
    files_written_lines = "\n".join(f"- `{path}`" for path in files_written)
    proof_json = json.dumps(proof_card, indent=2, sort_keys=True)
    return f"""---
type: workflow-proof
workflow_id: {WORKFLOW_ID}
run_id: {run_id}
date: {run_date}
status: internal_run_passed
---

# Agent Runtime Governance Audit

## Real Source Ingestion

This proof was generated from declared local governance/runtime sources selected for this run.

{source_lines}

## Boundary Summary

{blocked_lines}

## Signal Counts

{counts_lines}

## Findings

- Runtime/governance files were readable from declared paths only.
- Permission, approval, provider, browser, credential, and writeback language was detected and summarized.
- No secret-shaped source paths were accepted.
- No provider/model call, browser action, external send, payment/CRM mutation, canonical-state mutation, or live trading execution was attempted.

## Files Prepared

{files_written_lines}

## Proof Card

```json
{proof_json}
```
"""


def _build_client_report(
    *,
    run_id: str,
    run_date: str,
    source_count: int,
    aggregate_counts: dict[str, int],
    proof_path: str,
    scorecard_path: str,
    recommended_next_action: str,
) -> str:
    counts_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(aggregate_counts.items()))
    return f"""---
type: ventureops-client-report
workflow_id: {WORKFLOW_ID}
run_id: {run_id}
date: {run_date}
status: internal_run_passed
delivery_status: draft_only_not_externally_sent
---

# Client-Safe Agent Runtime Governance Audit Report

Delivery status: draft only - not externally sent

## Client-Safe Summary

ChaseOS completed a bounded internal governance audit over {source_count} declared runtime and governance sources. The run checked for permission-boundary language, approval language, writeback posture, runtime/provider references, browser authority, external-send posture, and live-trading boundaries.

## Boundary Results

- Provider/model calls: blocked
- Browser actions: blocked
- External sends: blocked
- Credential or secret reads: blocked
- Canonical-state mutation: blocked
- Payment or CRM mutation: blocked
- Live trading execution: blocked

## Signal Summary

{counts_lines}

## Evidence

- Internal proof artifact: `{proof_path}`
- Standalone scorecard artifact: `{scorecard_path}`

## Current Status

- Status label: internal_run_passed
- Client readiness: draft only
- External delivery: not performed
- Revenue claim: not made

## Recommended Next Action

{recommended_next_action}
"""


def _build_scorecard(
    *,
    run_id: str,
    proof_card: dict[str, Any],
    source_count: int,
    proof_path: str,
    client_report_path: str,
) -> dict[str, Any]:
    scorecard = {
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "runtime": "Codex+AOR",
        "operator": "local-operator",
        "timestamp": proof_card["timestamp"],
        "status": "internal_run_passed",
        "metrics": {
            "source_count": source_count,
            "proof_artifact_written": True,
            "client_report_written": True,
            "scorecard_written": True,
            "provider_calls": 0,
            "browser_actions": 0,
            "external_sends": 0,
            "canonical_mutations": 0,
            "secret_like_paths_blocked": True,
        },
        "evidence_links": [proof_path, client_report_path],
        "unresolved_risks": list(proof_card["unresolved_risks"]),
        "recommended_next_action": (
            "Run a second internal audit against a synthetic client-style fixture before external delivery."
        ),
    }
    validation = validate_agent_scorecard(scorecard)
    if not validation["ok"]:
        raise WorkflowExecutionError("; ".join(validation["errors"]))
    return scorecard


def _build_offer_packet(
    *,
    run_id: str,
    run_date: str,
    source_count: int,
    proof_path: str,
    client_report_path: str,
    scorecard_path: str,
) -> str:
    return f"""---
type: ventureops-offer-packet
workflow_id: {WORKFLOW_ID}
run_id: {run_id}
date: {run_date}
status: draft_offer_packet
delivery_status: blocked_until_explicit_approval
---

# Client-Safe Runtime Governance Audit Offer Packet

External delivery: blocked until explicit approval

## Offer

Runtime Governance Audit for AI-native teams and founders.

## Synthetic Client Fixture

Synthetic client fixture: verified

This offer packet was produced from {source_count} declared synthetic client-style runtime/governance files. It is safe for internal review and service design. It is not a claim that an external customer system has been audited.

## Included

- Declared runtime/governance source review
- Permission and approval-boundary signal summary
- Client-safe audit report draft
- Standalone agent scorecard
- Redacted proof artifact reference
- Recommended next action and unresolved risk list

## Not Included

- provider/model execution: not included
- browser action: not included
- payment/crm mutation: not included
- credential or secret inspection: not included
- external send: not included
- live remediation: not included

## Evidence

- Internal proof artifact: `{proof_path}`
- Client-safe draft report: `{client_report_path}`
- Standalone scorecard: `{scorecard_path}`

## Approval Boundary

This packet may be reviewed inside ChaseOS. Sending it to a client, using it as a paid offer, or attaching it to CRM/payment/delivery surfaces requires explicit operator approval and a client-specific scope record.
"""


def _build_client_scope_record(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    engagement_type: str,
    approved_use: str,
    delivery_channels: str,
    proof_path: str,
    client_report_path: str,
    scorecard_path: str,
    offer_packet_path: str,
) -> str:
    return f"""---
type: ventureops-client-scope-record
workflow_id: {WORKFLOW_ID}
run_id: {run_id}
date: {run_date}
status: scoped_internal_review_only
external_delivery_approved: false
---

# Client Scope Record

Client label: {client_label}

Engagement type: {engagement_type}

Approved use: {approved_use}

Delivery channels: {delivery_channels}

## Scope Boundary

- This record scopes an internal VentureOps runtime governance audit review.
- External delivery is not approved by this record.
- Paid delivery, CRM mutation, payment mutation, provider/model execution, browser action, and live remediation remain outside scope.
- Any future client-facing send requires a separate delivery approval decision and evidence of the exact materials to send.

## Evidence Under Scope

- Internal proof artifact: `{proof_path}`
- Client-safe draft report: `{client_report_path}`
- Standalone scorecard: `{scorecard_path}`
- Offer packet draft: `{offer_packet_path}`
"""


def _build_delivery_approval_contract(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    client_scope_path: str,
    proof_path: str,
    client_report_path: str,
    scorecard_path: str,
    offer_packet_path: str,
) -> str:
    return f"""---
type: ventureops-delivery-approval-contract
workflow_id: {WORKFLOW_ID}
run_id: {run_id}
date: {run_date}
status: blocked
external_delivery_approved: false
---

# Delivery Approval Contract

Delivery approval status: blocked

Client label: {client_label}

External delivery may not occur from this workflow run.

## Required Before Any External Delivery

- Explicit operator approval for the exact delivery packet.
- Confirmed client scope record.
- Review of redacted proof, report, scorecard, and offer packet.
- Confirmation that no secrets, credentials, browser session data, wallet keys, or private runtime data are present.
- Confirmation that delivery channel, recipient, and pricing language are approved.

## Not Authorized

- provider/model execution: not authorized
- browser action: not authorized
- payment/crm mutation: not authorized
- external send: not authorized
- live remediation: not authorized
- canonical-state mutation: not authorized

## Evidence To Review

- Client scope record: `{client_scope_path}`
- Internal proof artifact: `{proof_path}`
- Client-safe draft report: `{client_report_path}`
- Standalone scorecard: `{scorecard_path}`
- Offer packet draft: `{offer_packet_path}`
"""


def _build_delivery_packet_preview(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    proof_path: str,
    client_report_path: str,
    scorecard_path: str,
    offer_packet_path: str,
    client_scope_path: str,
    delivery_approval_contract_path: str,
) -> str:
    return f"""---
type: ventureops-delivery-packet-preview
workflow_id: {WORKFLOW_ID}
run_id: {run_id}
date: {run_date}
status: no_send_preview
external_delivery_approved: false
external_send_performed: false
---

# Delivery Packet Preview

Preview status: no-send

Client label: {client_label}

External send: not performed

Approval status: not approved

## Packet Contents For Review

- Client-safe draft report: `{client_report_path}`
- Standalone scorecard: `{scorecard_path}`
- Offer packet draft: `{offer_packet_path}`
- Client scope record: `{client_scope_path}`
- Delivery approval contract: `{delivery_approval_contract_path}`
- Internal proof artifact: `{proof_path}`

## Not Authorized

- provider/model execution: not authorized
- browser action: not authorized
- payment/crm mutation: not authorized
- external send: not authorized
- live remediation: not authorized
- canonical-state mutation: not authorized

## Operator Decision Required

This preview only assembles the materials that would be reviewed before a future delivery approval. It does not create an approval artifact, consume an approval, contact a recipient, mutate a CRM, collect payment, or send externally.
"""


def _build_approval_request_artifact(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    proof_path: str,
    client_report_path: str,
    scorecard_path: str,
    offer_packet_path: str,
    client_scope_path: str,
    delivery_approval_contract_path: str,
    delivery_packet_preview_path: str,
) -> dict[str, Any]:
    return {
        "type": "ventureops-delivery-approval-request",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "pending_operator_review",
        "requested_decision": "approve_or_reject_external_delivery",
        "approval_consumed": False,
        "external_delivery_approved": False,
        "external_send_performed": False,
        "artifacts_under_review": [
            proof_path,
            client_report_path,
            scorecard_path,
            offer_packet_path,
            client_scope_path,
            delivery_approval_contract_path,
            delivery_packet_preview_path,
        ],
        "required_operator_checks": [
            "review exact delivery packet",
            "confirm client scope",
            "confirm recipient and delivery channel",
            "confirm no secrets or private runtime data are present",
            "approve or reject external delivery explicitly",
        ],
        "forbidden_actions": [
            "provider_model_execution",
            "browser_action",
            "external_send",
            "payment_crm_mutation",
            "live_remediation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-agent-runtime-governance-audit-approval-consumption-proof",
    }


def _build_approval_consumption_proof(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    approval_decision_id: str,
    approval_decision: str,
    approval_decision_actor: str,
    approval_request_artifact_path: str,
    approval_request_artifact_json: str,
) -> dict[str, Any]:
    approved = approval_decision == "approved"
    return {
        "type": "ventureops-delivery-approval-consumption-proof",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "approval_consumed_no_send" if approved else "approval_denied_no_send",
        "approval_decision_id": approval_decision_id,
        "approval_decision": approval_decision,
        "approval_decision_actor": approval_decision_actor,
        "approval_request_artifact_path": approval_request_artifact_path,
        "approval_request_run_id": run_id,
        "approval_request_digest_sha256": hashlib.sha256(
            approval_request_artifact_json.encode("utf-8")
        ).hexdigest(),
        "approval_consumed": True,
        "external_delivery_approved": approved,
        "external_send_performed": False,
        "external_sends": 0,
        "send_blocked_until_exact_once_gate": True,
        "required_before_send": [
            "exact-once delivery gate",
            "external send dry-run proof",
            "approved external-send connector proof",
        ],
        "forbidden_actions": [
            "provider_model_execution",
            "browser_action",
            "external_send",
            "payment_crm_mutation",
            "live_remediation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-agent-runtime-governance-audit-exact-once-delivery-gate",
    }


def _build_exact_once_delivery_gate(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    approval_decision_id: str,
    approval_consumption_proof_path: str,
    approval_consumption_proof_json: str,
    delivery_gate_marker_path: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    consumption_digest = hashlib.sha256(approval_consumption_proof_json.encode("utf-8")).hexdigest()
    marker_key = hashlib.sha256(f"{WORKFLOW_ID}:{run_id}:{approval_decision_id}:{consumption_digest}".encode("utf-8")).hexdigest()
    gate = {
        "type": "ventureops-exact-once-delivery-gate",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "exact_once_gate_reserved_no_send",
        "approval_decision_id": approval_decision_id,
        "approval_consumption_proof_path": approval_consumption_proof_path,
        "approval_consumption_digest_sha256": consumption_digest,
        "delivery_gate_marker_path": delivery_gate_marker_path,
        "marker_key": marker_key,
        "duplicate_delivery_attempt_blocked": True,
        "approval_reuse_allowed": False,
        "external_delivery_gate_reserved": True,
        "external_send_performed": False,
        "external_sends": 0,
        "forbidden_actions": [
            "provider_model_execution",
            "browser_action",
            "external_send",
            "payment_crm_mutation",
            "live_remediation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-agent-runtime-governance-audit-external-send-dry-run",
    }
    marker = {
        "type": "ventureops-delivery-gate-marker",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "status": "reserved",
        "approval_decision_id": approval_decision_id,
        "marker_key": marker_key,
        "approval_consumption_proof_path": approval_consumption_proof_path,
        "approval_consumption_digest_sha256": consumption_digest,
        "external_send_performed": False,
        "external_sends": 0,
    }
    return gate, marker


def _build_external_send_dry_run(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    external_delivery_channel: str,
    external_recipient_label: str,
    external_recipient_route: str,
    approval_decision_id: str,
    approval_consumption_proof_path: str,
    exact_once_delivery_gate_path: str,
    delivery_gate_marker_path: str,
    delivery_gate_marker_json: str,
) -> dict[str, Any]:
    route_digest = hashlib.sha256(external_recipient_route.encode("utf-8")).hexdigest()
    marker_digest = hashlib.sha256(delivery_gate_marker_json.encode("utf-8")).hexdigest()
    return {
        "type": "ventureops-external-send-dry-run",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "external_send_dry_run_verified_no_send",
        "dry_run": True,
        "approval_decision_id": approval_decision_id,
        "approval_consumption_proof_path": approval_consumption_proof_path,
        "exact_once_delivery_gate_path": exact_once_delivery_gate_path,
        "delivery_gate_marker_path": delivery_gate_marker_path,
        "delivery_gate_marker_digest_sha256": marker_digest,
        "external_delivery_channel": external_delivery_channel,
        "external_recipient_label": external_recipient_label,
        "recipient_route_digest_sha256": route_digest,
        "recipient_route_present": True,
        "raw_recipient_route_persisted": False,
        "connector_dispatch_performed": False,
        "external_send_performed": False,
        "external_sends": 0,
        "dry_run_validations": [
            "approval consumption proof present",
            "exact-once delivery gate present",
            "delivery gate marker reserved",
            "recipient route hashed but not persisted",
            "connector dispatch blocked",
        ],
        "forbidden_actions": [
            "provider_model_execution",
            "browser_action",
            "external_send",
            "payment_crm_mutation",
            "live_remediation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-agent-runtime-governance-audit-approved-external-send",
    }


def _build_approved_external_send_proof(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    external_send_approval_id: str,
    external_send_approval_decision: str,
    external_send_approval_actor: str,
    external_send_dry_run_path: str,
    external_send_dry_run: dict[str, Any],
    external_send_dry_run_json: str,
    delivery_gate_marker_path: str,
) -> dict[str, Any]:
    if external_send_approval_decision != "approved":
        raise WorkflowExecutionError("external_send_approval_decision must be approved for approved-send proof")
    dry_run_digest = hashlib.sha256(external_send_dry_run_json.encode("utf-8")).hexdigest()
    return {
        "type": "ventureops-approved-external-send-proof",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "approved_external_send_proof_recorded_no_live_external_delivery",
        "external_send_approval_id": external_send_approval_id,
        "external_send_approval_decision": external_send_approval_decision,
        "external_send_approval_actor": external_send_approval_actor,
        "external_send_dry_run_path": external_send_dry_run_path,
        "external_send_dry_run_digest_sha256": dry_run_digest,
        "delivery_gate_marker_path": delivery_gate_marker_path,
        "connector_type": "local_proof_sink",
        "connector_dispatch_performed": True,
        "local_proof_sink_dispatches": 1,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "external_sends": 0,
        "external_delivery_channel": external_send_dry_run["external_delivery_channel"],
        "external_recipient_label": external_send_dry_run["external_recipient_label"],
        "recipient_route_digest_sha256": external_send_dry_run["recipient_route_digest_sha256"],
        "raw_recipient_route_persisted": False,
        "dispatch_evidence": [
            "approval-gated local proof sink selected",
            "dry-run evidence consumed",
            "delivery gate marker bound",
            "recipient route digest reused from dry-run",
            "live external connector not invoked",
        ],
        "forbidden_actions": [
            "provider_model_execution",
            "browser_action",
            "live_external_send",
            "payment_crm_mutation",
            "live_remediation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-crm-draft-integration",
    }


def _build_crm_draft(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    crm_system: str,
    crm_record_type: str,
    proof_path: str,
    client_scope_path: str,
    delivery_packet_preview_path: str,
    approved_external_send_proof_path: str,
) -> dict[str, Any]:
    return {
        "type": "ventureops-crm-draft",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "crm_draft_prepared_no_mutation",
        "crm_system": crm_system,
        "crm_record_type": crm_record_type,
        "proof_path": proof_path,
        "client_scope_path": client_scope_path,
        "delivery_packet_preview_path": delivery_packet_preview_path,
        "approved_external_send_proof_path": approved_external_send_proof_path,
        "draft_record": {
            "client_label": client_label,
            "workflow_id": WORKFLOW_ID,
            "engagement_status": "delivery-proof-ready",
            "next_action": "review CRM draft before any CRM mutation",
        },
        "crm_mutation_performed": False,
        "crm_records_mutated": 0,
        "approval_required_before_crm_mutation": True,
        "forbidden_actions": [
            "crm_api_call",
            "crm_record_mutation",
            "payment_mutation",
            "provider_model_execution",
            "browser_action",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-payment-invoice-draft-integration",
    }


def _build_payment_invoice_draft(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    payment_system: str,
    invoice_record_type: str,
    invoice_currency: str,
    invoice_amount: str,
    proof_path: str,
    client_scope_path: str,
    delivery_packet_preview_path: str,
    approved_external_send_proof_path: str,
    crm_draft_path: str,
) -> dict[str, Any]:
    return {
        "type": "ventureops-payment-invoice-draft",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "payment_invoice_draft_prepared_no_mutation",
        "payment_system": payment_system,
        "invoice_record_type": invoice_record_type,
        "invoice_currency": invoice_currency,
        "invoice_amount": invoice_amount,
        "proof_path": proof_path,
        "client_scope_path": client_scope_path,
        "delivery_packet_preview_path": delivery_packet_preview_path,
        "approved_external_send_proof_path": approved_external_send_proof_path,
        "crm_draft_path": crm_draft_path,
        "draft_record": {
            "client_label": client_label,
            "workflow_id": WORKFLOW_ID,
            "invoice_status": "draft-only",
            "next_action": "review payment/invoice draft before any invoice send or payment mutation",
        },
        "payment_mutation_performed": False,
        "payment_records_mutated": 0,
        "payment_collections_attempted": 0,
        "invoices_sent": 0,
        "approval_required_before_payment_mutation": True,
        "approval_required_before_invoice_send": True,
        "forbidden_actions": [
            "payment_api_call",
            "payment_record_mutation",
            "invoice_send",
            "crm_record_mutation",
            "provider_model_execution",
            "browser_action",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-workflow-exchange-publication-preview",
    }


def _workflow_pack_example_count(root: Path) -> int:
    pack_root = root / "runtime" / "workflows" / "registry" / "packs"
    if not pack_root.exists():
        return 0
    return sum(1 for path in pack_root.glob("*.yaml") if path.is_file())


def _build_workflow_exchange_publication_preview(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    publication_surface: str,
    listing_visibility: str,
    workflow_pack_examples_detected: int,
    proof_path: str,
    client_scope_path: str,
    delivery_packet_preview_path: str,
    approved_external_send_proof_path: str,
    crm_draft_path: str,
    payment_invoice_draft_path: str,
) -> dict[str, Any]:
    return {
        "type": "ventureops-workflow-exchange-publication-preview",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "publication_preview_prepared_no_publication",
        "publication_surface": publication_surface,
        "listing_visibility": listing_visibility,
        "workflow_pack_examples_detected": workflow_pack_examples_detected,
        "workflow_pack_supply_verified": workflow_pack_examples_detected >= 2,
        "proof_path": proof_path,
        "client_scope_path": client_scope_path,
        "delivery_packet_preview_path": delivery_packet_preview_path,
        "approved_external_send_proof_path": approved_external_send_proof_path,
        "crm_draft_path": crm_draft_path,
        "payment_invoice_draft_path": payment_invoice_draft_path,
        "listing_preview": {
            "title": "Safe Agent Runtime Governance Kit",
            "workflow_id": WORKFLOW_ID,
            "visibility": listing_visibility,
            "claim_boundary": "draft preview only; no publication, revenue claim, or external delivery",
        },
        "marketplace_publication_performed": False,
        "public_listing_created": False,
        "revenue_claim_made": False,
        "approval_required_before_publication": True,
        "forbidden_actions": [
            "marketplace_publication",
            "public_listing_creation",
            "revenue_claim",
            "payment_api_call",
            "crm_record_mutation",
            "provider_model_execution",
            "browser_action",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-live-client-scope-proof",
    }


def _build_live_client_scope_contract(
    *,
    run_id: str,
    run_date: str,
    client_label: str,
    proof_path: str,
    workflow_exchange_publication_preview_path: str,
    payment_invoice_draft_path: str,
) -> dict[str, Any]:
    return {
        "type": "ventureops-live-client-scope-contract",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "client_label": client_label,
        "status": "blocked_real_client_scope_required",
        "proof_path": proof_path,
        "workflow_exchange_publication_preview_path": workflow_exchange_publication_preview_path,
        "payment_invoice_draft_path": payment_invoice_draft_path,
        "real_client_scope_required": True,
        "real_client_scope_present": False,
        "live_client_scope_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "approval_required_before_live_client_run": True,
        "required_real_client_inputs": [
            "client-approved scope identifier",
            "declared read paths",
            "redaction policy",
            "operator approval id",
            "delivery boundary",
        ],
        "forbidden_actions": [
            "live_client_data_ingestion_without_scope",
            "broad_filesystem_read",
            "external_send",
            "provider_model_execution",
            "browser_action",
            "payment_api_call",
            "crm_record_mutation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-live-client-scope-proof",
    }


def _load_real_client_scope_evidence(
    *,
    vault_root: Path,
    scope_evidence_path: Any,
) -> tuple[str, dict[str, Any], list[str]]:
    evidence_relative = _required_safe_text(
        scope_evidence_path,
        field_name="real_client_scope_evidence_path",
    )
    evidence_relative = _validate_source_path(evidence_relative)
    evidence_path = (vault_root / evidence_relative).resolve()
    try:
        evidence_path.relative_to(vault_root)
    except ValueError as exc:
        raise WorkflowExecutionError("real_client_scope_evidence_path escapes vault root") from exc
    if not evidence_path.exists() or not evidence_path.is_file():
        raise WorkflowExecutionError(f"real_client_scope_evidence_path missing: {evidence_relative}")
    if evidence_path.suffix.lower() != ".json":
        raise WorkflowExecutionError("real_client_scope_evidence_path must be a JSON file")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowExecutionError("real_client_scope_evidence_path did not parse as JSON") from exc
    if not isinstance(evidence, dict):
        raise WorkflowExecutionError("real client scope evidence must be a JSON object")
    validation = validate_real_client_scope_evidence(evidence)
    if not validation["ok"]:
        if any(str(error).startswith("approved_read_paths contains unsafe path") for error in validation["errors"]):
            raise WorkflowExecutionError("scope evidence contains unsafe approved_read_paths")
        raise WorkflowExecutionError(f"real client scope evidence invalid: {validation['errors']}")
    approval_validation = validate_scope_evidence_approval_artifact(vault_root, evidence)
    if not approval_validation["ok"]:
        raise WorkflowExecutionError(f"real client scope approval artifact invalid: {approval_validation['errors']}")
    safe_read_paths = [str(path) for path in validation["safe_read_paths"]]
    try:
        for safe_path in safe_read_paths:
            _validate_source_path(safe_path)
    except WorkflowExecutionError as exc:
        raise WorkflowExecutionError("scope evidence contains unsafe approved_read_paths") from exc
    return evidence_relative, evidence, safe_read_paths


def _build_live_client_scope_proof_gate(
    *,
    run_id: str,
    run_date: str,
    proof_path: str,
    live_client_scope_contract_path: str,
    real_client_scope_evidence_path: str,
    scope_evidence: dict[str, Any],
    safe_read_paths: list[str],
) -> dict[str, Any]:
    return {
        "type": "ventureops-live-client-scope-proof-gate",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "status": "real_client_scope_evidence_validated_no_live_client_run",
        "proof_path": proof_path,
        "live_client_scope_contract_path": live_client_scope_contract_path,
        "real_client_scope_evidence_path": real_client_scope_evidence_path,
        "client_approved_scope_id": _safe_text(scope_evidence.get("client_approved_scope_id"), fallback=""),
        "client_label": _safe_text(scope_evidence.get("client_label"), fallback="client"),
        "approval_id": _safe_text(scope_evidence.get("approval_id"), fallback=""),
        "approval_status": "approved",
        "redaction_policy": _safe_text(scope_evidence.get("redaction_policy"), fallback="not specified"),
        "delivery_boundary": _safe_text(scope_evidence.get("delivery_boundary"), fallback="not specified"),
        "approved_read_path_count": len(safe_read_paths),
        "approved_read_paths_validated": True,
        "approved_read_paths": safe_read_paths,
        "real_client_scope_present": True,
        "real_client_scope_approved": True,
        "live_client_scope_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "forbidden_actions": [
            "broad_filesystem_read",
            "external_send",
            "provider_model_execution",
            "browser_action",
            "payment_api_call",
            "crm_record_mutation",
            "canonical_state_mutation",
        ],
        "next_required_pass": "ventureops-live-client-scope-proof",
    }


def build_agent_runtime_governance_audit(
    *,
    inputs: dict[str, Any] | None = None,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    inputs = inputs or {}
    root = Path(vault_root).resolve() if vault_root is not None else Path(__file__).resolve().parents[2]
    run_date = str(inputs.get("date") or _today_utc())
    run_id = _safe_slug(str(inputs.get("run_id") or f"{run_date}-internal-run"))
    include_offer_packet = _as_bool(inputs.get("include_offer_packet"))
    include_delivery_approval_contract = _as_bool(inputs.get("include_delivery_approval_contract"))
    include_delivery_packet_preview = _as_bool(inputs.get("include_delivery_packet_preview"))
    include_approval_request_artifact = _as_bool(inputs.get("include_approval_request_artifact"))
    include_approval_consumption_proof = _as_bool(inputs.get("include_approval_consumption_proof"))
    include_exact_once_delivery_gate = _as_bool(inputs.get("include_exact_once_delivery_gate"))
    include_external_send_dry_run = _as_bool(inputs.get("include_external_send_dry_run"))
    include_approved_external_send_proof = _as_bool(inputs.get("include_approved_external_send_proof"))
    include_crm_draft = _as_bool(inputs.get("include_crm_draft"))
    include_payment_invoice_draft = _as_bool(inputs.get("include_payment_invoice_draft"))
    include_workflow_exchange_publication_preview = _as_bool(inputs.get("include_workflow_exchange_publication_preview"))
    include_live_client_scope_contract = _as_bool(inputs.get("include_live_client_scope_contract"))
    include_live_client_scope_proof_gate = _as_bool(inputs.get("include_live_client_scope_proof_gate"))
    recommended_next_action = (
        "Review validated real client scope evidence before running live client proof."
        if include_live_client_scope_proof_gate
        else (
            "Provide explicit real client-approved scope evidence before live client proof can run."
            if include_live_client_scope_contract
            else (
                "Run a live client scope proof after Workflow Exchange preview is reviewed."
                if include_workflow_exchange_publication_preview
                else (
                    "Add Workflow Exchange publication preview after payment/invoice draft is reviewed."
                    if include_payment_invoice_draft
                    else (
                        "Add payment/invoice draft integration after CRM draft is reviewed."
                        if include_crm_draft
                        else (
                            "Add draft-first CRM integration after approved-send proof is reviewed."
                            if include_approved_external_send_proof
                            else (
                                "Add approved external-send proof after dry-run evidence is reviewed."
                                if include_external_send_dry_run
                                else (
                                    "Add external-send dry-run proof before any approved external send."
                                    if include_exact_once_delivery_gate
                                    else (
                                        "Add exact-once delivery gating before any external send can proceed."
                                        if include_approval_consumption_proof
                                        else (
                                            "Consume an explicit approval decision before any external delivery can proceed."
                                            if include_approval_request_artifact
                                            else (
                                                "Create an approval request for the reviewed delivery packet before any external send."
                                                if include_delivery_packet_preview
                                                else (
                                                    "Seek explicit delivery approval before any external client send."
                                                    if include_delivery_approval_contract
                                                    else "Run a second internal audit against a synthetic client-style fixture before external delivery."
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    source_paths = _as_source_list(inputs.get("source_paths"))
    sources = _read_sources(root, source_paths)
    combined = "\n\n".join(str(source["excerpt"]) for source in sources)
    aggregate_counts = _signal_counts(combined)
    proof_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}.md"
    client_report_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_client-report.md"
    scorecard_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_scorecard.json"
    offer_packet_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_offer-packet.md"
    client_scope_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_client-scope.md"
    delivery_approval_contract_path = (
        f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_delivery-approval-contract.md"
    )
    delivery_packet_preview_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_delivery-packet-preview.md"
    approval_request_artifact_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_approval-request.json"
    approval_consumption_proof_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_approval-consumption.json"
    exact_once_delivery_gate_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_exact-once-delivery-gate.json"
    delivery_gate_marker_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_delivery-gate-marker.json"
    external_send_dry_run_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_external-send-dry-run.json"
    approved_external_send_proof_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_approved-external-send.json"
    crm_draft_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_crm-draft.json"
    payment_invoice_draft_path = f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_payment-invoice-draft.json"
    workflow_exchange_publication_preview_path = (
        f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_workflow-exchange-publication-preview.json"
    )
    live_client_scope_contract_path = (
        f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_live-client-scope-contract.json"
    )
    live_client_scope_proof_gate_path = (
        f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_live-client-scope-proof-gate.json"
    )
    scope_evidence_relative = ""
    scope_evidence: dict[str, Any] = {}
    scope_safe_read_paths: list[str] = []
    if include_live_client_scope_proof_gate:
        scope_evidence_relative, scope_evidence, scope_safe_read_paths = _load_real_client_scope_evidence(
            vault_root=root,
            scope_evidence_path=inputs.get("real_client_scope_evidence_path"),
        )
    client_label = _safe_text(inputs.get("client_label"), fallback="synthetic client")
    engagement_type = _safe_text(inputs.get("engagement_type"), fallback="runtime governance audit")
    approved_use = _safe_text(inputs.get("approved_use"), fallback="internal review only")
    delivery_channels = _safe_text(inputs.get("delivery_channels"), fallback="none")
    external_delivery_channel = _safe_text(inputs.get("external_delivery_channel"), fallback="")
    external_recipient_label = _safe_text(
        inputs.get("external_recipient_label"),
        fallback=client_label,
    )
    external_recipient_route = _safe_text(inputs.get("external_recipient_route"), fallback="")
    external_send_approval_id = _safe_text(inputs.get("external_send_approval_id"), fallback="")
    external_send_approval_decision = (
        _approval_decision(inputs.get("external_send_approval_decision"))
        if include_approved_external_send_proof
        else ""
    )
    external_send_approval_actor = _safe_text(inputs.get("external_send_approval_actor"), fallback="operator")
    approval_decision_actor = _safe_text(inputs.get("approval_decision_actor"), fallback="operator")
    crm_system = _safe_text(inputs.get("crm_system"), fallback="local-draft-crm")
    crm_record_type = _safe_text(inputs.get("crm_record_type"), fallback="deal")
    payment_system = _safe_text(inputs.get("payment_system"), fallback="local-draft-invoice")
    invoice_record_type = _safe_text(inputs.get("invoice_record_type"), fallback="invoice")
    invoice_currency = _safe_text(inputs.get("invoice_currency"), fallback="USD")
    invoice_amount = _safe_text(inputs.get("invoice_amount"), fallback="0.00")
    publication_surface = _safe_text(inputs.get("publication_surface"), fallback="workflow-exchange-preview")
    listing_visibility = _safe_text(inputs.get("listing_visibility"), fallback="draft-private")
    input_sources = [str(source["path"]) for source in sources]
    files_written = [proof_path, client_report_path, scorecard_path]
    outputs_generated = [
        "agent runtime governance audit proof card",
        "client-safe draft audit report",
        "standalone agent runtime scorecard",
    ]
    actions_taken = [
        "read declared local governance/runtime files",
        "counted governance and permission-boundary signals",
        "prepared internal proof card",
        "prepared client-safe draft report",
        "prepared standalone agent scorecard",
        "blocked provider, browser, external-send, secret, canonical, payment, CRM, and live-trading actions",
    ]
    if include_offer_packet:
        files_written.append(offer_packet_path)
        outputs_generated.append("client-safe runtime governance audit offer packet")
        actions_taken.append("prepared redacted internal offer packet draft")
    if include_delivery_approval_contract:
        if not include_offer_packet:
            raise WorkflowExecutionError("delivery approval contract requires include_offer_packet=true")
        files_written.extend([client_scope_path, delivery_approval_contract_path])
        outputs_generated.extend(["client scope record", "blocked delivery approval contract"])
        actions_taken.append("prepared client scope and blocked delivery approval contract")
    if include_delivery_packet_preview:
        if not include_delivery_approval_contract:
            raise WorkflowExecutionError("delivery packet preview requires include_delivery_approval_contract=true")
        files_written.append(delivery_packet_preview_path)
        outputs_generated.append("no-send delivery packet preview")
        actions_taken.append("prepared no-send delivery packet preview")
    if include_approval_request_artifact:
        if not include_delivery_packet_preview:
            raise WorkflowExecutionError("approval request artifact requires include_delivery_packet_preview=true")
        files_written.append(approval_request_artifact_path)
        outputs_generated.append("pending delivery approval request artifact")
        actions_taken.append("prepared pending approval request artifact without consuming approval")
    if include_approval_consumption_proof:
        if not include_approval_request_artifact:
            raise WorkflowExecutionError("approval consumption proof requires include_approval_request_artifact=true")
        approval_request_run_id = _required_safe_text(
            inputs.get("approval_request_run_id"),
            field_name="approval_request_run_id",
        )
        if approval_request_run_id != run_id:
            raise WorkflowExecutionError("approval_request_run_id does not match approval request")
        _required_safe_text(inputs.get("approval_decision_id"), field_name="approval_decision_id")
        _approval_decision(inputs.get("approval_decision"))
        _validate_actor(approval_decision_actor, root, field_name="approval_decision_actor")
        files_written.append(approval_consumption_proof_path)
        outputs_generated.append("approval consumption proof without external send")
        actions_taken.append("consumed explicit approval decision without external send")
    if include_exact_once_delivery_gate:
        if not include_approval_consumption_proof:
            raise WorkflowExecutionError("exact-once delivery gate requires include_approval_consumption_proof=true")
        marker_absolute_path = (root / delivery_gate_marker_path).resolve()
        try:
            marker_absolute_path.relative_to(root)
        except ValueError as exc:
            raise WorkflowExecutionError("delivery gate marker path escapes vault root") from exc
        if marker_absolute_path.exists():
            raise WorkflowExecutionError("duplicate delivery gate marker already exists")
        files_written.extend([exact_once_delivery_gate_path, delivery_gate_marker_path])
        outputs_generated.extend(["exact-once delivery gate proof", "delivery gate marker"])
        actions_taken.append("reserved exact-once delivery gate without external send")
    if include_external_send_dry_run:
        if not include_exact_once_delivery_gate:
            raise WorkflowExecutionError("external send dry-run requires include_exact_once_delivery_gate=true")
        if not external_delivery_channel:
            raise WorkflowExecutionError("external_delivery_channel is required")
        if not external_recipient_route:
            raise WorkflowExecutionError("external_recipient_route is required")
        files_written.append(external_send_dry_run_path)
        outputs_generated.append("external send connector dry-run proof")
        actions_taken.append("validated external send connector package without dispatch")
    if include_approved_external_send_proof:
        if not include_external_send_dry_run:
            raise WorkflowExecutionError("approved external-send proof requires include_external_send_dry_run=true")
        if not external_send_approval_id:
            raise WorkflowExecutionError("external_send_approval_id is required")
        if external_send_approval_decision != "approved":
            raise WorkflowExecutionError("external_send_approval_decision must be approved")
        _validate_actor(external_send_approval_actor, root, field_name="external_send_approval_actor")
        files_written.append(approved_external_send_proof_path)
        outputs_generated.append("approved external-send proof via local proof sink")
        actions_taken.append("recorded approved external-send proof through local proof sink without live delivery")
    if include_crm_draft:
        if not include_approved_external_send_proof:
            raise WorkflowExecutionError("CRM draft requires include_approved_external_send_proof=true")
        files_written.append(crm_draft_path)
        outputs_generated.append("draft CRM record without CRM mutation")
        actions_taken.append("prepared draft CRM record without CRM mutation")
    if include_payment_invoice_draft:
        if not include_crm_draft:
            raise WorkflowExecutionError("payment/invoice draft requires include_crm_draft=true")
        files_written.append(payment_invoice_draft_path)
        outputs_generated.append("draft payment/invoice record without payment mutation")
        actions_taken.append("prepared draft payment/invoice record without payment mutation or invoice send")
    if include_workflow_exchange_publication_preview:
        if not include_payment_invoice_draft:
            raise WorkflowExecutionError("Workflow Exchange publication preview requires include_payment_invoice_draft=true")
        files_written.append(workflow_exchange_publication_preview_path)
        outputs_generated.append("Workflow Exchange publication preview without marketplace publication")
        actions_taken.append("prepared Workflow Exchange publication preview without public listing or revenue claim")
    if include_live_client_scope_contract:
        if not include_workflow_exchange_publication_preview:
            raise WorkflowExecutionError("live client scope contract requires include_workflow_exchange_publication_preview=true")
        files_written.append(live_client_scope_contract_path)
        outputs_generated.append("live client scope contract blocked until real client scope exists")
        actions_taken.append("prepared live client scope contract without ingesting live client data")
    if include_live_client_scope_proof_gate:
        if not include_live_client_scope_contract:
            raise WorkflowExecutionError("live client scope proof gate requires include_live_client_scope_contract=true")
        files_written.append(live_client_scope_proof_gate_path)
        outputs_generated.append("live client scope proof gate without live client data ingestion")
        actions_taken.append("validated real client scope evidence without running live client workflow")
    unresolved_risks = [
        "This is an internal read-only proof and client-safe draft, not an externally delivered client audit.",
        "No external customer runtime was audited in this pass.",
        "No live remediation workflow was executed.",
    ]
    if include_live_client_scope_proof_gate:
        unresolved_risks.insert(
            2,
            "Real client scope evidence is validated, but live client workflow and live revenue proof remain unperformed.",
        )
    elif include_live_client_scope_contract:
        unresolved_risks.insert(
            2,
            "Live client scope proof remains blocked until explicit real client-approved scope evidence exists.",
        )
    elif include_workflow_exchange_publication_preview:
        unresolved_risks.insert(
            2,
            "Workflow Exchange publication preview is draft-only; no marketplace listing or revenue claim has occurred.",
        )
    elif include_payment_invoice_draft:
        unresolved_risks.insert(
            2,
            "Payment/invoice integration is draft-only; no payment system mutation or invoice send has occurred.",
        )
    elif include_crm_draft:
        unresolved_risks.insert(
            2,
            "CRM integration is draft-only; no CRM system mutation has occurred.",
        )
    elif include_approved_external_send_proof:
        unresolved_risks.insert(
            2,
            "Approved-send proof used a local proof sink; live external delivery remains unperformed.",
        )
    elif include_external_send_dry_run:
        unresolved_risks.insert(
            2,
            "External send remains blocked until approved-send proof exists.",
        )
    elif include_exact_once_delivery_gate:
        unresolved_risks.insert(
            2,
            "External send remains blocked until connector dry-run proof and approved-send proof exist.",
        )
    elif include_approval_consumption_proof:
        unresolved_risks.insert(
            2,
            "External send remains blocked until exact-once delivery gating and connector dry-run proof exist.",
        )
    else:
        unresolved_risks.insert(
            2,
            "External delivery remains blocked until a separate approval decision is granted.",
        )
    proof_card = build_proof_card(
        workflow_id=WORKFLOW_ID,
        run_id=run_id,
        before_state="VentureOps runtime audit workflow had no proof-of-run for real ChaseOS governance inputs.",
        after_state="Read-only governance/runtime source ingestion completed and proof artifact was prepared.",
        input_sources=input_sources,
        runtimes_used=["Codex", "AOR"],
        actions_taken=actions_taken,
        outputs_generated=outputs_generated,
        files_written=files_written,
        approvals_used=["manual local workflow invocation"],
        unresolved_risks=unresolved_risks,
        internal_audit_link=proof_path,
        customer_facing_summary=(
            "ChaseOS can run a bounded runtime governance audit over declared local sources "
            "and produce a redacted proof artifact without external side effects."
        ),
        cta_or_follow_up=recommended_next_action,
    )
    proof_card["result"] = "internal_run_passed"
    proof_card["scorecard_summary"] = {"status": "internal_run_passed", "score": 1}
    scorecard = _build_scorecard(
        run_id=run_id,
        proof_card=proof_card,
        source_count=len(sources),
        proof_path=proof_path,
        client_report_path=client_report_path,
    )
    if include_offer_packet:
        scorecard["evidence_links"].append(offer_packet_path)
        scorecard["metrics"]["offer_packet_written"] = True
    if include_delivery_approval_contract:
        scorecard["evidence_links"].extend([client_scope_path, delivery_approval_contract_path])
        scorecard["metrics"]["client_scope_written"] = True
        scorecard["metrics"]["delivery_approval_contract_written"] = True
        scorecard["metrics"]["external_delivery_approved"] = False
        scorecard["recommended_next_action"] = "Seek explicit delivery approval before any external client send."
    if include_delivery_packet_preview:
        scorecard["evidence_links"].append(delivery_packet_preview_path)
        scorecard["metrics"]["delivery_packet_preview_written"] = True
        scorecard["metrics"]["external_delivery_approved"] = False
        scorecard["metrics"]["external_sends"] = 0
        scorecard["recommended_next_action"] = (
            "Create an approval request for the reviewed delivery packet before any external send."
        )
    if include_approval_request_artifact:
        scorecard["evidence_links"].append(approval_request_artifact_path)
        scorecard["metrics"]["approval_request_artifact_written"] = True
        scorecard["metrics"]["approval_consumed"] = False
        scorecard["metrics"]["external_delivery_approved"] = False
        scorecard["metrics"]["external_sends"] = 0
        scorecard["recommended_next_action"] = (
            "Consume an explicit approval decision before any external delivery can proceed."
        )
    if include_approval_consumption_proof:
        approval_decision = _approval_decision(inputs.get("approval_decision"))
        scorecard["evidence_links"].append(approval_consumption_proof_path)
        scorecard["metrics"]["approval_consumption_proof_written"] = True
        scorecard["metrics"]["approval_consumed"] = True
        scorecard["metrics"]["approval_decision"] = approval_decision
        scorecard["metrics"]["external_delivery_approved"] = approval_decision == "approved"
        scorecard["metrics"]["external_send_performed"] = False
        scorecard["metrics"]["external_sends"] = 0
        scorecard["recommended_next_action"] = (
            "Add exact-once delivery gating before any external send can proceed."
        )
    if include_exact_once_delivery_gate:
        scorecard["evidence_links"].extend([exact_once_delivery_gate_path, delivery_gate_marker_path])
        scorecard["metrics"]["exact_once_delivery_gate_written"] = True
        scorecard["metrics"]["delivery_gate_marker_written"] = True
        scorecard["metrics"]["approval_reuse_allowed"] = False
        scorecard["metrics"]["external_send_performed"] = False
        scorecard["metrics"]["external_sends"] = 0
        scorecard["recommended_next_action"] = (
            "Add external-send dry-run proof before any approved external send."
        )
    if include_external_send_dry_run:
        scorecard["evidence_links"].append(external_send_dry_run_path)
        scorecard["metrics"]["external_send_dry_run_written"] = True
        scorecard["metrics"]["external_send_dry_run_passed"] = True
        scorecard["metrics"]["connector_dispatch_performed"] = False
        scorecard["metrics"]["external_send_performed"] = False
        scorecard["metrics"]["external_sends"] = 0
        scorecard["recommended_next_action"] = (
            "Add approved external-send proof after dry-run evidence is reviewed."
        )
    if include_approved_external_send_proof:
        scorecard["evidence_links"].append(approved_external_send_proof_path)
        scorecard["metrics"]["approved_external_send_proof_written"] = True
        scorecard["metrics"]["external_send_approval_decision"] = external_send_approval_decision
        scorecard["metrics"]["local_proof_sink_dispatches"] = 1
        scorecard["metrics"]["connector_dispatch_performed"] = True
        scorecard["metrics"]["live_external_send_performed"] = False
        scorecard["metrics"]["external_send_performed"] = False
        scorecard["metrics"]["external_sends"] = 0
        scorecard["recommended_next_action"] = (
            "Add draft-first CRM integration after approved-send proof is reviewed."
        )
    if include_crm_draft:
        scorecard["evidence_links"].append(crm_draft_path)
        scorecard["metrics"]["crm_draft_written"] = True
        scorecard["metrics"]["crm_mutation_performed"] = False
        scorecard["metrics"]["crm_records_mutated"] = 0
        scorecard["recommended_next_action"] = (
            "Add payment/invoice draft integration after CRM draft is reviewed."
        )
    if include_payment_invoice_draft:
        scorecard["evidence_links"].append(payment_invoice_draft_path)
        scorecard["metrics"]["payment_invoice_draft_written"] = True
        scorecard["metrics"]["payment_mutation_performed"] = False
        scorecard["metrics"]["payment_records_mutated"] = 0
        scorecard["metrics"]["payment_collections_attempted"] = 0
        scorecard["metrics"]["invoices_sent"] = 0
        scorecard["recommended_next_action"] = (
            "Add Workflow Exchange publication preview after payment/invoice draft is reviewed."
        )
    workflow_pack_examples_detected = _workflow_pack_example_count(root)
    if include_workflow_exchange_publication_preview:
        scorecard["evidence_links"].append(workflow_exchange_publication_preview_path)
        scorecard["metrics"]["workflow_exchange_publication_preview_written"] = True
        scorecard["metrics"]["workflow_pack_examples_detected"] = workflow_pack_examples_detected
        scorecard["metrics"]["workflow_pack_supply_verified"] = workflow_pack_examples_detected >= 2
        scorecard["metrics"]["marketplace_publication_performed"] = False
        scorecard["metrics"]["public_listing_created"] = False
        scorecard["metrics"]["revenue_claim_made"] = False
        scorecard["recommended_next_action"] = (
            "Run a live client scope proof after Workflow Exchange preview is reviewed."
        )
    if include_live_client_scope_contract:
        scorecard["evidence_links"].append(live_client_scope_contract_path)
        scorecard["metrics"]["live_client_scope_contract_written"] = True
        scorecard["metrics"]["live_client_scope_proof_performed"] = False
        scorecard["metrics"]["real_client_scope_present"] = False
        scorecard["metrics"]["live_client_data_ingested"] = False
        scorecard["metrics"]["live_external_delivery_performed"] = False
        scorecard["recommended_next_action"] = (
            "Provide explicit real client-approved scope evidence before live client proof can run."
        )
    if include_live_client_scope_proof_gate:
        scorecard["evidence_links"].append(live_client_scope_proof_gate_path)
        scorecard["metrics"]["live_client_scope_proof_gate_written"] = True
        scorecard["metrics"]["real_client_scope_present"] = True
        scorecard["metrics"]["real_client_scope_approved"] = True
        scorecard["metrics"]["approved_read_path_count"] = len(scope_safe_read_paths)
        scorecard["metrics"]["live_client_scope_proof_performed"] = False
        scorecard["metrics"]["live_client_data_ingested"] = False
        scorecard["metrics"]["live_external_delivery_performed"] = False
        scorecard["recommended_next_action"] = (
            "Review validated real client scope evidence before running live client proof."
        )
    client_report_markdown = _build_client_report(
        run_id=run_id,
        run_date=run_date,
        source_count=len(sources),
        aggregate_counts=aggregate_counts,
        proof_path=proof_path,
        scorecard_path=scorecard_path,
        recommended_next_action=recommended_next_action,
    )
    scorecard_json = json.dumps(scorecard, indent=2, sort_keys=True) + "\n"
    offer_packet_markdown = _build_offer_packet(
        run_id=run_id,
        run_date=run_date,
        source_count=len(sources),
        proof_path=proof_path,
        client_report_path=client_report_path,
        scorecard_path=scorecard_path,
    ) if include_offer_packet else ""
    client_scope_markdown = _build_client_scope_record(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        engagement_type=engagement_type,
        approved_use=approved_use,
        delivery_channels=delivery_channels,
        proof_path=proof_path,
        client_report_path=client_report_path,
        scorecard_path=scorecard_path,
        offer_packet_path=offer_packet_path,
    ) if include_delivery_approval_contract else ""
    delivery_approval_contract_markdown = _build_delivery_approval_contract(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        client_scope_path=client_scope_path,
        proof_path=proof_path,
        client_report_path=client_report_path,
        scorecard_path=scorecard_path,
        offer_packet_path=offer_packet_path,
    ) if include_delivery_approval_contract else ""
    delivery_packet_preview_markdown = _build_delivery_packet_preview(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        proof_path=proof_path,
        client_report_path=client_report_path,
        scorecard_path=scorecard_path,
        offer_packet_path=offer_packet_path,
        client_scope_path=client_scope_path,
        delivery_approval_contract_path=delivery_approval_contract_path,
    ) if include_delivery_packet_preview else ""
    approval_request_artifact = _build_approval_request_artifact(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        proof_path=proof_path,
        client_report_path=client_report_path,
        scorecard_path=scorecard_path,
        offer_packet_path=offer_packet_path,
        client_scope_path=client_scope_path,
        delivery_approval_contract_path=delivery_approval_contract_path,
        delivery_packet_preview_path=delivery_packet_preview_path,
    ) if include_approval_request_artifact else {}
    approval_request_artifact_json = (
        json.dumps(approval_request_artifact, indent=2, sort_keys=True) + "\n"
        if include_approval_request_artifact
        else ""
    )
    approval_consumption_proof = _build_approval_consumption_proof(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        approval_decision_id=_required_safe_text(
            inputs.get("approval_decision_id"),
            field_name="approval_decision_id",
        ),
        approval_decision=_approval_decision(inputs.get("approval_decision")),
        approval_decision_actor=approval_decision_actor,
        approval_request_artifact_path=approval_request_artifact_path,
        approval_request_artifact_json=approval_request_artifact_json,
    ) if include_approval_consumption_proof else {}
    approval_consumption_proof_json = (
        json.dumps(approval_consumption_proof, indent=2, sort_keys=True) + "\n"
        if include_approval_consumption_proof
        else ""
    )
    exact_once_delivery_gate, delivery_gate_marker = _build_exact_once_delivery_gate(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        approval_decision_id=_required_safe_text(
            inputs.get("approval_decision_id"),
            field_name="approval_decision_id",
        ),
        approval_consumption_proof_path=approval_consumption_proof_path,
        approval_consumption_proof_json=approval_consumption_proof_json,
        delivery_gate_marker_path=delivery_gate_marker_path,
    ) if include_exact_once_delivery_gate else ({}, {})
    exact_once_delivery_gate_json = (
        json.dumps(exact_once_delivery_gate, indent=2, sort_keys=True) + "\n"
        if include_exact_once_delivery_gate
        else ""
    )
    delivery_gate_marker_json = (
        json.dumps(delivery_gate_marker, indent=2, sort_keys=True) + "\n"
        if include_exact_once_delivery_gate
        else ""
    )
    external_send_dry_run = _build_external_send_dry_run(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        external_delivery_channel=external_delivery_channel,
        external_recipient_label=external_recipient_label,
        external_recipient_route=external_recipient_route,
        approval_decision_id=_required_safe_text(
            inputs.get("approval_decision_id"),
            field_name="approval_decision_id",
        ),
        approval_consumption_proof_path=approval_consumption_proof_path,
        exact_once_delivery_gate_path=exact_once_delivery_gate_path,
        delivery_gate_marker_path=delivery_gate_marker_path,
        delivery_gate_marker_json=delivery_gate_marker_json,
    ) if include_external_send_dry_run else {}
    external_send_dry_run_json = (
        json.dumps(external_send_dry_run, indent=2, sort_keys=True) + "\n"
        if include_external_send_dry_run
        else ""
    )
    approved_external_send_proof = _build_approved_external_send_proof(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        external_send_approval_id=external_send_approval_id,
        external_send_approval_decision=external_send_approval_decision,
        external_send_approval_actor=external_send_approval_actor,
        external_send_dry_run_path=external_send_dry_run_path,
        external_send_dry_run=external_send_dry_run,
        external_send_dry_run_json=external_send_dry_run_json,
        delivery_gate_marker_path=delivery_gate_marker_path,
    ) if include_approved_external_send_proof else {}
    approved_external_send_proof_json = (
        json.dumps(approved_external_send_proof, indent=2, sort_keys=True) + "\n"
        if include_approved_external_send_proof
        else ""
    )
    crm_draft = _build_crm_draft(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        crm_system=crm_system,
        crm_record_type=crm_record_type,
        proof_path=proof_path,
        client_scope_path=client_scope_path,
        delivery_packet_preview_path=delivery_packet_preview_path,
        approved_external_send_proof_path=approved_external_send_proof_path,
    ) if include_crm_draft else {}
    crm_draft_json = (
        json.dumps(crm_draft, indent=2, sort_keys=True) + "\n"
        if include_crm_draft
        else ""
    )
    payment_invoice_draft = _build_payment_invoice_draft(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        payment_system=payment_system,
        invoice_record_type=invoice_record_type,
        invoice_currency=invoice_currency,
        invoice_amount=invoice_amount,
        proof_path=proof_path,
        client_scope_path=client_scope_path,
        delivery_packet_preview_path=delivery_packet_preview_path,
        approved_external_send_proof_path=approved_external_send_proof_path,
        crm_draft_path=crm_draft_path,
    ) if include_payment_invoice_draft else {}
    payment_invoice_draft_json = (
        json.dumps(payment_invoice_draft, indent=2, sort_keys=True) + "\n"
        if include_payment_invoice_draft
        else ""
    )
    workflow_exchange_publication_preview = _build_workflow_exchange_publication_preview(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        publication_surface=publication_surface,
        listing_visibility=listing_visibility,
        workflow_pack_examples_detected=workflow_pack_examples_detected,
        proof_path=proof_path,
        client_scope_path=client_scope_path,
        delivery_packet_preview_path=delivery_packet_preview_path,
        approved_external_send_proof_path=approved_external_send_proof_path,
        crm_draft_path=crm_draft_path,
        payment_invoice_draft_path=payment_invoice_draft_path,
    ) if include_workflow_exchange_publication_preview else {}
    workflow_exchange_publication_preview_json = (
        json.dumps(workflow_exchange_publication_preview, indent=2, sort_keys=True) + "\n"
        if include_workflow_exchange_publication_preview
        else ""
    )
    live_client_scope_contract = _build_live_client_scope_contract(
        run_id=run_id,
        run_date=run_date,
        client_label=client_label,
        proof_path=proof_path,
        workflow_exchange_publication_preview_path=workflow_exchange_publication_preview_path,
        payment_invoice_draft_path=payment_invoice_draft_path,
    ) if include_live_client_scope_contract else {}
    live_client_scope_contract_json = (
        json.dumps(live_client_scope_contract, indent=2, sort_keys=True) + "\n"
        if include_live_client_scope_contract
        else ""
    )
    live_client_scope_proof_gate = _build_live_client_scope_proof_gate(
        run_id=run_id,
        run_date=run_date,
        proof_path=proof_path,
        live_client_scope_contract_path=live_client_scope_contract_path,
        real_client_scope_evidence_path=scope_evidence_relative,
        scope_evidence=scope_evidence,
        safe_read_paths=scope_safe_read_paths,
    ) if include_live_client_scope_proof_gate else {}
    live_client_scope_proof_gate_json = (
        json.dumps(live_client_scope_proof_gate, indent=2, sort_keys=True) + "\n"
        if include_live_client_scope_proof_gate
        else ""
    )
    proof_markdown = _build_markdown(
        run_id=run_id,
        run_date=run_date,
        sources=sources,
        aggregate_counts=aggregate_counts,
        proof_card=proof_card,
        proof_path=proof_path,
        client_report_path=client_report_path,
        scorecard_path=scorecard_path,
        files_written=files_written,
    )
    writebacks = [
        {"path": proof_path, "content": proof_markdown},
        {"path": client_report_path, "content": client_report_markdown},
        {"path": scorecard_path, "content": scorecard_json},
    ]
    if include_offer_packet:
        writebacks.append({"path": offer_packet_path, "content": offer_packet_markdown})
    if include_delivery_approval_contract:
        writebacks.extend(
            [
                {"path": client_scope_path, "content": client_scope_markdown},
                {"path": delivery_approval_contract_path, "content": delivery_approval_contract_markdown},
            ]
        )
    if include_delivery_packet_preview:
        writebacks.append({"path": delivery_packet_preview_path, "content": delivery_packet_preview_markdown})
    if include_approval_request_artifact:
        writebacks.append({"path": approval_request_artifact_path, "content": approval_request_artifact_json})
    if include_approval_consumption_proof:
        writebacks.append({"path": approval_consumption_proof_path, "content": approval_consumption_proof_json})
    if include_exact_once_delivery_gate:
        writebacks.extend(
            [
                {"path": exact_once_delivery_gate_path, "content": exact_once_delivery_gate_json},
                {"path": delivery_gate_marker_path, "content": delivery_gate_marker_json},
            ]
        )
    if include_external_send_dry_run:
        writebacks.append({"path": external_send_dry_run_path, "content": external_send_dry_run_json})
    if include_approved_external_send_proof:
        writebacks.append({"path": approved_external_send_proof_path, "content": approved_external_send_proof_json})
    if include_crm_draft:
        writebacks.append({"path": crm_draft_path, "content": crm_draft_json})
    if include_payment_invoice_draft:
        writebacks.append({"path": payment_invoice_draft_path, "content": payment_invoice_draft_json})
    if include_workflow_exchange_publication_preview:
        writebacks.append(
            {
                "path": workflow_exchange_publication_preview_path,
                "content": workflow_exchange_publication_preview_json,
            }
        )
    if include_live_client_scope_contract:
        writebacks.append({"path": live_client_scope_contract_path, "content": live_client_scope_contract_json})
    if include_live_client_scope_proof_gate:
        writebacks.append({"path": live_client_scope_proof_gate_path, "content": live_client_scope_proof_gate_json})
    result = {
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "input_sources": input_sources,
        "source_count": len(sources),
        "signal_counts": aggregate_counts,
        "blocked_surfaces": list(BLOCKED_SURFACES),
        "proof_path": proof_path,
        "client_report_path": client_report_path,
        "scorecard_path": scorecard_path,
        "proof_card": proof_card,
        "scorecard": scorecard,
        "proof_markdown": proof_markdown,
        "client_report_markdown": client_report_markdown,
        "scorecard_json": scorecard_json,
        "writebacks": writebacks,
    }
    if include_offer_packet:
        result["offer_packet_path"] = offer_packet_path
        result["offer_packet_markdown"] = offer_packet_markdown
    if include_delivery_approval_contract:
        result["client_scope_path"] = client_scope_path
        result["client_scope_markdown"] = client_scope_markdown
        result["delivery_approval_contract_path"] = delivery_approval_contract_path
        result["delivery_approval_contract_markdown"] = delivery_approval_contract_markdown
    if include_delivery_packet_preview:
        result["delivery_packet_preview_path"] = delivery_packet_preview_path
        result["delivery_packet_preview_markdown"] = delivery_packet_preview_markdown
    if include_approval_request_artifact:
        result["approval_request_artifact_path"] = approval_request_artifact_path
        result["approval_request_artifact"] = approval_request_artifact
        result["approval_request_artifact_json"] = approval_request_artifact_json
    if include_approval_consumption_proof:
        result["approval_consumption_proof_path"] = approval_consumption_proof_path
        result["approval_consumption_proof"] = approval_consumption_proof
        result["approval_consumption_proof_json"] = approval_consumption_proof_json
    if include_exact_once_delivery_gate:
        result["exact_once_delivery_gate_path"] = exact_once_delivery_gate_path
        result["exact_once_delivery_gate"] = exact_once_delivery_gate
        result["exact_once_delivery_gate_json"] = exact_once_delivery_gate_json
        result["delivery_gate_marker_path"] = delivery_gate_marker_path
        result["delivery_gate_marker"] = delivery_gate_marker
        result["delivery_gate_marker_json"] = delivery_gate_marker_json
    if include_external_send_dry_run:
        result["external_send_dry_run_path"] = external_send_dry_run_path
        result["external_send_dry_run"] = external_send_dry_run
        result["external_send_dry_run_json"] = external_send_dry_run_json
    if include_approved_external_send_proof:
        result["approved_external_send_proof_path"] = approved_external_send_proof_path
        result["approved_external_send_proof"] = approved_external_send_proof
        result["approved_external_send_proof_json"] = approved_external_send_proof_json
    if include_crm_draft:
        result["crm_draft_path"] = crm_draft_path
        result["crm_draft"] = crm_draft
        result["crm_draft_json"] = crm_draft_json
    if include_payment_invoice_draft:
        result["payment_invoice_draft_path"] = payment_invoice_draft_path
        result["payment_invoice_draft"] = payment_invoice_draft
        result["payment_invoice_draft_json"] = payment_invoice_draft_json
    if include_workflow_exchange_publication_preview:
        result["workflow_exchange_publication_preview_path"] = workflow_exchange_publication_preview_path
        result["workflow_exchange_publication_preview"] = workflow_exchange_publication_preview
        result["workflow_exchange_publication_preview_json"] = workflow_exchange_publication_preview_json
    if include_live_client_scope_contract:
        result["live_client_scope_contract_path"] = live_client_scope_contract_path
        result["live_client_scope_contract"] = live_client_scope_contract
        result["live_client_scope_contract_json"] = live_client_scope_contract_json
    if include_live_client_scope_proof_gate:
        result["live_client_scope_proof_gate_path"] = live_client_scope_proof_gate_path
        result["live_client_scope_proof_gate"] = live_client_scope_proof_gate
        result["live_client_scope_proof_gate_json"] = live_client_scope_proof_gate_json
    return result


def run_agent_runtime_governance_audit(
    *,
    inputs: dict[str, Any] | None = None,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault_root)
