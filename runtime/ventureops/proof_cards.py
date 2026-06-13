"""Proof-card builders for VentureOps dry-run and internal evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import ProofCard
from .validation import validate_proof_card


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_proof_card(
    *,
    workflow_id: str,
    run_id: str,
    before_state: str,
    after_state: str,
    input_sources: list[str],
    runtimes_used: list[str],
    actions_taken: list[str],
    outputs_generated: list[str],
    files_written: list[str] | None = None,
    approvals_used: list[str] | None = None,
    unresolved_risks: list[str] | None = None,
    internal_audit_link: str = "",
    customer_facing_summary: str = "",
    cta_or_follow_up: str = "",
) -> dict[str, Any]:
    card = ProofCard(
        workflow_id=workflow_id,
        run_id=run_id,
        timestamp=_now_utc(),
        before_state=before_state,
        after_state=after_state,
        input_sources=input_sources,
        runtimes_used=runtimes_used,
        actions_taken=actions_taken,
        approvals_used=approvals_used or [],
        outputs_generated=outputs_generated,
        files_written=files_written or [],
        screenshots_or_logs=[],
        scorecard_summary={"status": "untested", "score": 0},
        result="draft_internal_proof",
        unresolved_risks=unresolved_risks or [],
        customer_facing_summary=customer_facing_summary,
        internal_audit_link=internal_audit_link,
        cta_or_follow_up=cta_or_follow_up,
    ).to_dict()
    validate_proof_card(card)
    return card
