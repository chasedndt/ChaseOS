"""Draft-only site skill candidate writer for Browser Runtime evidence."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.browser_runtime.models import (
    BrowserRunResult,
    SiteSkillDraft,
    domain_from_url,
    now_iso,
    slugify,
)


def skill_drafts_dir(root: Path | str | None = None) -> Path:
    base = Path(root) if root else _default_root()
    return base / "06_AGENTS" / "Browser-Skills" / "_drafts"


def _default_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def generate_site_skill_draft(
    result: BrowserRunResult,
    *,
    root: Path | str | None = None,
    source_log_path: str | None = None,
) -> SiteSkillDraft:
    """Build a draft-only skill candidate from browser run evidence."""
    domain = domain_from_url(result.url) or "local-file"
    safe_actions = sorted(
        {
            action.action_type
            for action in result.actions
            if action.status == "succeeded" and action.action_type not in {"type", "form_submit", "credential_field_fill"}
        }
    )
    draft = SiteSkillDraft(
        draft_id=f"draft_{result.run_id}",
        domain=domain,
        status="draft",
        run_id=result.run_id,
        source_log_path=source_log_path or result.browser_run_log_path or "",
        observed_urls=[result.url],
        safe_actions=safe_actions,
        forbidden_actions=[
            "credential_field_fill",
            "cookie_export",
            "form_submit",
            "real_profile_reuse",
            "skill_auto_activation",
        ],
        selectors=[],
        workflow_notes=[
            "Generated as draft-only Browser Runtime Adapter evidence.",
            "Requires review before promotion to SiteOps Site Skill Card or workflow manifest.",
            "No secrets, cookies, credentials, or user profile data were retained.",
        ],
        evidence_links=[path for path in [source_log_path or result.browser_run_log_path, result.agent_activity_log_path] if path],
        review_required=True,
        activation_allowed=False,
    )
    return draft


def write_site_skill_draft(draft: SiteSkillDraft, *, root: Path | str | None = None) -> str:
    """Write a draft skill candidate under 06_AGENTS/Browser-Skills/_drafts/."""
    directory = skill_drafts_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slugify(draft.draft_id, 'site-skill-draft')}.md"
    payload = json.dumps(draft.as_dict(), indent=2)
    lines = [
        "---",
        "type: browser-site-skill-draft",
        f"status: {draft.status}",
        f"created: {draft.created_at}",
        f"domain: {draft.domain}",
        f"run_id: {draft.run_id}",
        "activation_allowed: false",
        "review_required: true",
        "---",
        "",
        f"# Browser Site Skill Draft - {draft.domain}",
        "",
        "This draft was generated from browser run evidence. It is not active runtime memory.",
        "",
        "## Review Boundary",
        "",
        "- Status: draft only",
        "- Activation allowed: false",
        "- Promotion target: reviewed SiteOps Site Skill Card or Workflow Manifest only after approval",
        "- Secrets/cookies/credentials/session tokens: forbidden",
        "",
        "## Evidence",
        "",
        f"- Source run: `{draft.source_log_path}`",
        *[f"- Evidence link: `{link}`" for link in draft.evidence_links],
        "",
        "## Safe Actions Observed",
        "",
        *[f"- `{action}`" for action in draft.safe_actions],
        "",
        "## Forbidden Actions",
        "",
        *[f"- `{action}`" for action in draft.forbidden_actions],
        "",
        "## Machine Record",
        "",
        "```json",
        payload,
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def create_and_write_site_skill_draft(
    result: BrowserRunResult,
    *,
    root: Path | str | None = None,
    source_log_path: str | None = None,
) -> tuple[SiteSkillDraft, str]:
    draft = generate_site_skill_draft(result, root=root, source_log_path=source_log_path)
    path = write_site_skill_draft(draft, root=root)
    return draft, path
