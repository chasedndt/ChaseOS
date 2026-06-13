"""Shadow-only runner for Browser Operator Skill Layer proof runs."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from runtime.browser_runtime.logging import write_agent_activity_log, write_browser_run_log
from runtime.browser_runtime.models import (
    BrowserActionRecord,
    BrowserArtifact,
    BrowserRunRequest,
    BrowserRunResult,
    BrowserRuntimeProvider,
    now_iso,
    slugify,
)

from .registry import detect_vault_root, load_skill
from .validator import validate_skill


DEFAULT_SHADOW_SKILL_ID = "excalidraw.draw_basic_shape"

SHADOW_SAFE_APPROVAL_STATUSES = {"candidate_untrusted", "draft", "needs_review", "approved"}
SHADOW_SAFE_ACTIONS = {
    "navigate",
    "wait_for",
    "read_url",
    "read_title",
    "read_visible_text",
    "screenshot",
    "select_tool",
    "click_selector",
    "drag",
    "verify",
    "keypress",
    "halt",
}
CANONICAL_DESTINATION_PREFIXES = ("00_HOME/", "01_PROJECTS/", "02_KNOWLEDGE/")


class BrowserSkillShadowError(ValueError):
    """Raised when a BOSL skill cannot be used for a shadow proof."""


@dataclass(frozen=True)
class BrowserSkillShadowProof:
    """Structured result for one BOSL shadow proof."""

    ok: bool
    skill_id: str
    run_id: str
    status: str
    mode: str
    live_browser_control: bool
    validation_warnings: list[str] = field(default_factory=list)
    browser_run_log_path: str | None = None
    agent_activity_log_path: str | None = None
    candidate_path: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    planned_actions: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_allowed_domain(value: str) -> str:
    """Convert an origin/URL/domain declaration to a hostname-like value."""
    candidate = str(value).strip()
    if not candidate:
        return ""
    if "://" in candidate:
        parsed = urlparse(candidate)
        return parsed.hostname or ""
    return candidate.split("/", 1)[0].split(":", 1)[0]


def normalize_allowed_domains(values: list[str]) -> list[str]:
    """Return stable hostnames from a skill allowed_domains list."""
    domains = {normalize_allowed_domain(value) for value in values}
    return sorted(domain for domain in domains if domain)


def _target_url_for_skill(skill: dict[str, Any]) -> str:
    for step in skill.get("steps", []):
        if isinstance(step, dict) and step.get("action") == "navigate":
            target = str(step.get("target", "")).strip()
            if target:
                return target
    allowed = skill.get("allowed_domains") or []
    first = str(allowed[0]).strip() if allowed else ""
    if first.startswith(("http://", "https://")):
        return first
    return f"https://{first}" if first else ""


def _destination_values(value: Any) -> list[str]:
    destinations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() == "destination" and isinstance(child, str):
                destinations.append(child.replace("\\", "/"))
            destinations.extend(_destination_values(child))
    elif isinstance(value, list):
        for child in value:
            destinations.extend(_destination_values(child))
    return destinations


def assert_shadow_safe_skill(skill: dict[str, Any]) -> list[str]:
    """Validate that a skill is eligible for non-executing shadow proof."""
    result = validate_skill(skill)
    errors = list(result.errors)

    if skill.get("mode") != "shadow":
        errors.append("BOSL shadow proof requires mode=shadow")
    if skill.get("approval_status") not in SHADOW_SAFE_APPROVAL_STATUSES:
        errors.append("approval_status is not eligible for a shadow proof")
    if skill.get("risk_level") == "blocked":
        errors.append("risk_level=blocked cannot be used for a shadow proof")
    if skill.get("account_required") is not False:
        errors.append("account_required must be false for this shadow proof")
    if skill.get("credentials_required") is not False:
        errors.append("credentials_required must be false for this shadow proof")
    if skill.get("canonical_writeback") is not False:
        errors.append("canonical_writeback must be false for this shadow proof")

    allowed_domains = normalize_allowed_domains(skill.get("allowed_domains") or [])
    if not allowed_domains:
        errors.append("allowed_domains must resolve to at least one hostname")

    target_url = _target_url_for_skill(skill)
    parsed_target = urlparse(target_url)
    if parsed_target.hostname and parsed_target.hostname not in allowed_domains:
        errors.append(f"navigate target host is outside allowed_domains: {parsed_target.hostname}")

    for index, step in enumerate(skill.get("steps") or []):
        if not isinstance(step, dict):
            continue
        action = str(step.get("action", "")).strip()
        if action not in SHADOW_SAFE_ACTIONS:
            errors.append(f"step {index} uses an action outside the shadow allowlist: {action}")

    for destination in _destination_values(skill.get("outputs_schema", {})):
        if destination.startswith(CANONICAL_DESTINATION_PREFIXES):
            errors.append(f"outputs_schema destination is canonical and forbidden: {destination}")

    if errors:
        raise BrowserSkillShadowError("; ".join(errors))
    return result.warnings


def _planned_actions_from_skill(skill: dict[str, Any]) -> list[BrowserActionRecord]:
    actions: list[BrowserActionRecord] = []
    for step in skill.get("steps") or []:
        if not isinstance(step, dict):
            continue
        metadata = {
            "step_id": step.get("step_id"),
            "coordinate_strategy": step.get("coordinate_strategy"),
            "verification_ref": step.get("verification_ref"),
            "executed": False,
            "shadow_plan_only": True,
        }
        actions.append(
            BrowserActionRecord(
                action_type=str(step.get("action", "")),
                target=str(step.get("target", "")),
                status="planned",
                notes="BOSL shadow proof only; step was validated but not executed.",
                metadata={key: value for key, value in metadata.items() if value is not None},
            )
        )
    return actions


def _build_result(skill: dict[str, Any], *, run_id: str) -> tuple[BrowserRunRequest, BrowserRunResult]:
    target_url = _target_url_for_skill(skill)
    allowed_domains = normalize_allowed_domains(skill.get("allowed_domains") or [])
    request = BrowserRunRequest(
        url=target_url,
        task=f"BOSL shadow proof for {skill.get('skill_id')}: {skill.get('intent')}",
        provider=BrowserRuntimeProvider.SHADOW,
        mode="shadow",
        run_id=run_id,
        harmless_action="validate_skill_plan",
        allowed_domains=allowed_domains,
        use_real_profile=False,
        allow_credentials=False,
        write_skill_draft=False,
    )
    actions = [
        BrowserActionRecord(
            action_type="validate_skill",
            target=str(skill.get("skill_id")),
            status="succeeded",
            notes="BOSL validator and shadow safety checks passed.",
        ),
        BrowserActionRecord(
            action_type="shadow_open_intent",
            target=target_url,
            status="planned",
            notes="No browser was launched; navigation intent only.",
            metadata={"allowed_domains": allowed_domains, "executed": False},
        ),
        *_planned_actions_from_skill(skill),
    ]
    result = BrowserRunResult(
        run_id=run_id,
        status="succeeded",
        provider=BrowserRuntimeProvider.SHADOW,
        mode="shadow",
        url=target_url,
        task=request.task,
        actions=actions,
        artifacts=[],
        summary="BOSL shadow proof completed: skill validated and planned without live browser execution.",
        started_at=now_iso(),
        ended_at=now_iso(),
        security_flags={
            "real_profile_used": False,
            "credentials_allowed": False,
            "cookies_exported": False,
            "canonical_writeback": False,
            "skill_activation": False,
            "live_browser_control": False,
            "browser_launched": False,
            "network_request_made": False,
            "candidate_trust": "untrusted",
        },
    )
    return request, result


def _with_result_paths(
    result: BrowserRunResult,
    *,
    artifacts: list[BrowserArtifact] | None = None,
    browser_run_log_path: str | None = None,
    agent_activity_log_path: str | None = None,
    candidate_path: str | None = None,
) -> BrowserRunResult:
    return BrowserRunResult(
        **{
            **result.as_dict(),
            "provider": result.provider,
            "actions": result.actions,
            "artifacts": artifacts if artifacts is not None else result.artifacts,
            "browser_run_log_path": browser_run_log_path if browser_run_log_path is not None else result.browser_run_log_path,
            "agent_activity_log_path": agent_activity_log_path
            if agent_activity_log_path is not None
            else result.agent_activity_log_path,
            "skill_candidate_path": candidate_path if candidate_path is not None else result.skill_candidate_path,
            "skill_draft_path": result.skill_draft_path,
        }
    )


def _write_shadow_artifact(root: Path, run_id: str, skill_id: str) -> BrowserArtifact:
    path = root / "07_LOGS" / "Browser-Runs" / f"{run_id}-shadow-proof.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "ChaseOS BOSL shadow proof artifact.\n"
        f"Skill: {skill_id}\n"
        "No browser was launched.\n"
        "No network request, real profile, cookie, credential, or canonical writeback was used.\n",
        encoding="utf-8",
    )
    return BrowserArtifact(
        artifact_type="bosl_shadow_proof",
        path=str(path),
        description="Text proof artifact for a non-executing BOSL shadow run.",
        redacted=True,
        metadata={"live_browser": False, "network_request_made": False},
    )


def format_untrusted_candidate(
    skill: dict[str, Any],
    result: BrowserRunResult,
    *,
    validation_warnings: list[str],
) -> str:
    """Render an untrusted browser skill candidate markdown artifact."""
    source_run_ref = result.browser_run_log_path or result.run_id
    machine_record = {
        **deepcopy(skill),
        "record_type": "browser_skill_candidate",
        "candidate_id": f"candidate_{result.run_id}",
        "proposed_skill_id": skill.get("skill_id"),
        "status": "candidate_untrusted",
        "approval_status": "candidate_untrusted",
        "source_run_id": result.run_id,
        "source_runs": [source_run_ref] if source_run_ref else [],
        "last_verified": None,
        "activation_allowed": False,
        "live_browser_control": False,
        "validation_warnings": validation_warnings,
        "forbidden_material_excluded": [
            "credentials",
            "cookies",
            "session_tokens",
            "browser_profile_state",
            "canonical_writeback",
        ],
    }
    return "\n".join(
        [
            "---",
            "type: browser-skill-candidate",
            "status: candidate_untrusted",
            "approval_status: candidate_untrusted",
            "trust_tier: Tier 4",
            f"created: {now_iso()}",
            f"skill_id: {skill.get('skill_id')}",
            f"domain: {skill.get('domain')}",
            f"source_run_id: {result.run_id}",
            "activation_allowed: false",
            "live_browser_control: false",
            "---",
            "",
            f"# Browser Skill Candidate - {skill.get('skill_id')}",
            "",
            "UNTRUSTED CANDIDATE. This file is data for review, not an executable plan.",
            "",
            "## Boundary",
            "",
            "- Candidate remains Tier 4 until reviewed and promoted.",
            "- No live browser was launched for this proof.",
            "- No credentials, cookies, session tokens, real profile data, or canonical writeback were used.",
            "- Trusted skill files were not modified by this run.",
            "",
            "## Source Evidence",
            "",
            f"- Run ID: `{result.run_id}`",
            f"- Browser run log: `{result.browser_run_log_path}`",
            f"- Agent activity log: `{result.agent_activity_log_path}`",
            "",
            "## Machine Candidate",
            "",
            "```json",
            json.dumps(machine_record, indent=2),
            "```",
            "",
        ]
    )


def write_untrusted_candidate(
    skill: dict[str, Any],
    result: BrowserRunResult,
    *,
    root: Path,
    validation_warnings: list[str],
) -> str:
    directory = root / "03_INPUTS" / "Browser-Skill-Candidates"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slugify(result.run_id, 'browser-skill-shadow')}-candidate.md"
    path.write_text(
        format_untrusted_candidate(skill, result, validation_warnings=validation_warnings),
        encoding="utf-8",
    )
    return str(path)


def run_skill_shadow_proof(
    skill_id: str = DEFAULT_SHADOW_SKILL_ID,
    *,
    root: Path | str | None = None,
    persist: bool = True,
    write_candidate: bool = True,
) -> BrowserSkillShadowProof:
    """Validate a BOSL skill and produce a non-executing shadow proof."""
    vault_root = Path(root) if root is not None else detect_vault_root()
    skill = load_skill(skill_id, vault_root)
    if skill is None:
        raise BrowserSkillShadowError(f"browser skill not found: {skill_id}")

    validation_warnings = assert_shadow_safe_skill(skill)
    run_id = f"bosl_shadow_{now_iso().replace(':', '').replace('+', 'z')}_{slugify(skill_id)}"
    request, result = _build_result(skill, run_id=run_id)

    candidate_path: str | None = None
    artifact_paths: list[str] = []
    if persist:
        artifact = _write_shadow_artifact(vault_root, run_id, skill_id)
        result = _with_result_paths(result, artifacts=[artifact])
        browser_run_log_path = write_browser_run_log(
            result,
            request,
            root=vault_root,
            extra={
                "bosl_skill_id": skill_id,
                "shadow_plan_only": True,
                "trusted_skill_mutated": False,
                "candidate_home": "03_INPUTS/Browser-Skill-Candidates/",
            },
        )
        result = _with_result_paths(result, browser_run_log_path=browser_run_log_path)
        if write_candidate:
            candidate_path = write_untrusted_candidate(
                skill,
                result,
                root=vault_root,
                validation_warnings=validation_warnings,
            )
            result = _with_result_paths(result, candidate_path=candidate_path)
        agent_activity_log_path = write_agent_activity_log(result, request, root=vault_root)
        result = _with_result_paths(result, agent_activity_log_path=agent_activity_log_path)
        if candidate_path:
            write_untrusted_candidate(
                skill,
                result,
                root=vault_root,
                validation_warnings=validation_warnings,
            )
        write_browser_run_log(
            result,
            request,
            root=vault_root,
            extra={
                "bosl_skill_id": skill_id,
                "shadow_plan_only": True,
                "trusted_skill_mutated": False,
                "candidate_path": candidate_path,
            },
        )
        artifact_paths = [artifact.path]

    planned_actions = [action.as_dict() for action in result.actions if action.status == "planned"]
    return BrowserSkillShadowProof(
        ok=result.status == "succeeded",
        skill_id=skill_id,
        run_id=run_id,
        status=result.status,
        mode=result.mode,
        live_browser_control=False,
        validation_warnings=validation_warnings,
        browser_run_log_path=result.browser_run_log_path,
        agent_activity_log_path=result.agent_activity_log_path,
        candidate_path=candidate_path,
        artifact_paths=artifact_paths,
        planned_actions=planned_actions,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a BOSL skill in shadow-plan mode.")
    parser.add_argument("skill_id", nargs="?", default=DEFAULT_SHADOW_SKILL_ID)
    parser.add_argument("--root", help="ChaseOS vault root. Defaults to auto-detection.")
    parser.add_argument("--no-persist", action="store_true", help="Validate and plan only; do not write logs.")
    parser.add_argument("--no-candidate", action="store_true", help="Do not write an untrusted candidate.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        proof = run_skill_shadow_proof(
            args.skill_id,
            root=args.root,
            persist=not args.no_persist,
            write_candidate=not args.no_candidate,
        )
    except BrowserSkillShadowError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(proof.as_dict(), indent=2))
    return 0 if proof.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
