"""Browser/site profile proposal helpers for VentureOps Mission Mode."""

from __future__ import annotations

from datetime import date
from typing import Any


def build_site_profile_candidate(
    *,
    site_name: str,
    domain: str,
    purpose: str,
    workflow_use_cases: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "site_name": site_name,
        "domain": domain,
        "purpose": purpose,
        "user_approved_workflow_use_cases": list(workflow_use_cases),
        "safe_read_actions": ["view_public_page", "capture_operator_approved_screenshot"],
        "safe_proposal_actions": ["draft_navigation_plan", "draft_selector_candidate", "record_friction_note"],
        "approval_required_actions": ["form_fill", "message_send", "listing_publish", "purchase", "account_mutation"],
        "forbidden_actions": ["credential_read", "cookie_capture", "token_capture", "session_file_read", "unsupervised_purchase"],
        "known_navigation_patterns": [],
        "known_friction_points": [],
        "selector_candidates": [],
        "screenshot_proof_requirements": ["redact private data", "link browser run log"],
        "credential_boundaries": "No cookies, tokens, passwords, API keys, seed phrases, or session files may be read or stored.",
        "cookie_session_token_handling": "forbidden",
        "browser_skill_candidates": [],
        "last_reviewed_date": date.today().isoformat(),
        "status": "candidate",
        "browser_skill_activation_allowed": False,
        "authority_boundary": {
            "candidate_only": True,
            "bosl_review_required": True,
            "gate_approval_required_before_activation": True,
        },
    }
