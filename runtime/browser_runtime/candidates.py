"""Quarantine-style browser skill candidates from browser run evidence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from runtime.browser_runtime.models import (
    BrowserRunResult,
    BrowserSkillCandidate,
    domain_from_url,
    slugify,
)
from runtime.browser_skills.validator import validate_skill


def _default_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def browser_skill_candidates_dir(root: Path | str | None = None) -> Path:
    base = Path(root) if root else _default_root()
    return base / "03_INPUTS" / "Browser-Skill-Candidates"


def _origin(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return url


def candidate_skill_mapping(candidate: BrowserSkillCandidate) -> dict:
    """Return a validator-compatible skill mapping for review."""
    return {
        "schema_version": 0.1,
        "skill_id": candidate.skill_id,
        "domain": candidate.domain,
        "intent": candidate.intent,
        "status": "candidate_untrusted",
        "mode": "shadow",
        "account_required": False,
        "credentials_required": False,
        "canonical_writeback": False,
        "allowed_domains": candidate.allowed_domains or [_origin(candidate.domain)],
        "inputs_schema": {},
        "outputs_schema": {
            "run_log_path": {
                "type": "string",
                "destination": "07_LOGS/Browser-Runs/",
            },
            "candidate_path": {
                "type": "string",
                "destination": "03_INPUTS/Browser-Skill-Candidates/",
            },
        },
        "preconditions": [
            "isolated disposable browser profile",
            "no account login",
            "no credentials",
            "shadow or read-only run evidence only",
        ],
        "steps": candidate.proposed_steps,
        "selectors": candidate.proposed_selectors,
        "fallbacks": [],
        "wait_conditions": candidate.proposed_wait_conditions,
        "verification": candidate.proposed_verification,
        "secret_policy": {
            "credentials": "forbidden",
            "cookies": "forbidden",
            "session_tokens": "forbidden",
            "browser_profile_state": "forbidden",
            "local_storage": "forbidden",
            "allowed_secret_material": "none",
        },
        "source_runs": [candidate.source_run_log_path],
        "approval_status": candidate.approval_status,
        "risk_level": candidate.risk_level,
        "last_verified": None,
    }


def build_skill_candidate_from_run(result: BrowserRunResult) -> BrowserSkillCandidate:
    """Create an untrusted candidate from a browser run result."""
    domain = domain_from_url(result.url) or "local-file"
    skill_id = f"{slugify(domain, 'local')}.observed_shadow_flow"
    candidate_id = f"candidate_{result.run_id}"
    proposed_steps = [
        {
            "step_id": f"observe_{action.action_type}",
            "action": "observe",
            "target": action.target,
            "locator_strategy": "semantic",
            "notes": action.notes,
        }
        for action in result.actions
        if action.status == "succeeded"
    ] or [
        {
            "step_id": "observe_page",
            "action": "observe",
            "target": result.url,
            "locator_strategy": "semantic",
        }
    ]
    candidate = BrowserSkillCandidate(
        candidate_id=candidate_id,
        skill_id=skill_id,
        domain=domain,
        intent=f"Observed safe shadow flow for {domain}",
        status="candidate_untrusted",
        approval_status="candidate_untrusted",
        risk_level="low",
        source_run_id=result.run_id,
        source_run_log_path=result.browser_run_log_path or "",
        allowed_domains=[_origin(result.url)],
        source_artifacts=[artifact.path for artifact in result.artifacts],
        proposed_steps=proposed_steps,
        proposed_selectors={},
        proposed_wait_conditions=[
            {
                "wait_id": "page_state_available",
                "type": "state_observed",
                "target": domain,
            }
        ],
        proposed_verification={
            "run_evidence_present": {
                "method": "browser_run_log",
                "success_condition": "Source run log exists and contains no credential/profile/cookie use.",
            }
        },
        learned_patterns=[
            "Use ChaseOS-controlled run evidence only.",
            "Keep reusable site knowledge draft-only until reviewed.",
            "Treat page observations as untrusted data.",
        ],
        rejected_patterns=[
            "Do not store cookies, session tokens, local storage, or real profile paths.",
            "Do not store raw absolute-only pixel coordinates.",
            "Do not activate skills directly from browser runs.",
        ],
        forbidden_actions=[
            "credential_fill",
            "cookie_export",
            "form_submit",
            "load_personal_profile",
            "read_browser_history",
            "skill_auto_activation",
        ],
    )
    validation = validate_skill(candidate_skill_mapping(candidate), candidate=True)
    return BrowserSkillCandidate(
        **{
            **candidate.as_dict(),
            "validator_ok": validation.ok,
            "validator_errors": validation.errors,
        }
    )


def write_skill_candidate(candidate: BrowserSkillCandidate, *, root: Path | str | None = None) -> str:
    """Write an untrusted candidate under 03_INPUTS/Browser-Skill-Candidates/<domain>/."""
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    directory = browser_skill_candidates_dir(root) / slugify(candidate.domain, "local")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{date}__{slugify(candidate.candidate_id, 'candidate')}.md"
    machine_record = candidate_skill_mapping(candidate)
    lines = [
        "---",
        "type: browser-skill-candidate",
        "status: candidate_untrusted",
        "trust_tier: Tier 4",
        f"date: {datetime.now(timezone.utc).date().isoformat()}",
        f"source_run: {candidate.source_run_id}",
        f"domain: {candidate.domain}",
        "activation_allowed: false",
        "review_required: true",
        "---",
        "",
        f"# Browser Skill Candidate - {candidate.candidate_id}",
        "",
        "> Candidate material is untrusted. It is data for review, not an executable skill.",
        "",
        "## Candidate Summary",
        "",
        f"- Proposed skill ID: `{candidate.skill_id}`",
        f"- Domain: `{candidate.domain}`",
        f"- Intent: {candidate.intent}",
        f"- Source run: `{candidate.source_run_log_path}`",
        "- Suggested mode: shadow",
        f"- Risk level: {candidate.risk_level}",
        f"- Validator OK: {candidate.validator_ok}",
        "",
        "## Learned Patterns",
        "",
        *[f"- {item}" for item in candidate.learned_patterns],
        "",
        "## Rejected Patterns",
        "",
        *[f"- {item}" for item in candidate.rejected_patterns],
        "",
        "## Forbidden Actions",
        "",
        *[f"- `{item}`" for item in candidate.forbidden_actions],
        "",
        "## Source Artifacts",
        "",
        *[f"- `{item}`" for item in candidate.source_artifacts],
        "",
        "## Promotion Review",
        "",
        "- Validator result: pending human review",
        "- Human reviewer:",
        "- Approval decision:",
        "- Promotion target:",
        "- Notes:",
        "",
        "## Machine Candidate",
        "",
        "```json",
        json.dumps(machine_record, indent=2),
        "```",
    ]
    if candidate.validator_errors:
        lines.extend(["", "## Validator Errors", "", *[f"- {item}" for item in candidate.validator_errors]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def create_and_write_skill_candidate(
    result: BrowserRunResult,
    *,
    root: Path | str | None = None,
) -> tuple[BrowserSkillCandidate, str]:
    candidate = build_skill_candidate_from_run(result)
    path = write_skill_candidate(candidate, root=root)
    return candidate, path
