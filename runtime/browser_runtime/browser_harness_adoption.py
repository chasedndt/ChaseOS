"""Read-only Browser Harness adoption decision for ChaseOS.

The decision is intentionally conservative: ChaseOS adapts Browser Harness
patterns for domain/interaction skill memory, but does not adopt the raw
harness authority model.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


BROWSER_HARNESS_DECISION_STATUS = "reference_only_raw_harness_not_adopted"
BROWSER_HARNESS_ADOPTION_MODE = "adapt_patterns_do_not_copy_or_run"

BROWSER_HARNESS_BLOCKED_EFFECTS = (
    "dependency_install",
    "browser_harness_install",
    "browser_harness_cli_run",
    "real_browser_profile_attachment",
    "remote_browser_provisioning",
    "profile_sync",
    "cookie_or_session_read",
    "freeform_cdp_snippet_execution",
    "trusted_skill_write",
    "skill_activation",
    "agent_bus_enqueue",
    "provider_call",
    "gate_mutation",
    "canonical_writeback",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class BrowserHarnessExternalReference:
    repo: str
    url: str
    license: str
    observed_pattern: str
    chaseos_use: str

    def validate(self) -> None:
        if not self.repo:
            raise ValueError("external reference repo is required")
        if not self.url.startswith("https://github.com/"):
            raise ValueError("external reference must be a GitHub URL")
        if not self.license:
            raise ValueError("external reference license is required")
        if not self.observed_pattern:
            raise ValueError("external reference observed pattern is required")
        if not self.chaseos_use:
            raise ValueError("external reference ChaseOS use is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "repo": self.repo,
            "url": self.url,
            "license": self.license,
            "observed_pattern": self.observed_pattern,
            "chaseos_use": self.chaseos_use,
        }


@dataclass(frozen=True)
class BrowserHarnessAdoptionDecision:
    generated_at: str
    decision_id: str
    status: str
    adoption_mode: str
    browser_harness_adopted: bool
    browser_harness_js_adopted: bool
    raw_cdp_surface_adopted: bool
    domain_skill_pattern_adopted: bool
    interaction_skill_taxonomy_adopted: bool
    external_references: tuple[BrowserHarnessExternalReference, ...]
    adopted_patterns: tuple[str, ...]
    rejected_patterns: tuple[str, ...]
    gated_future_patterns: tuple[str, ...]
    required_chaseos_controls: tuple[str, ...]
    next_allowed_step: str
    read_only: bool = True
    dependency_install_attempted: bool = False
    browser_harness_install_attempted: bool = False
    browser_harness_cli_run_attempted: bool = False
    real_browser_profile_attachment_attempted: bool = False
    remote_browser_provisioning_attempted: bool = False
    profile_sync_attempted: bool = False
    cookie_or_session_read_attempted: bool = False
    freeform_cdp_snippet_execution_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    blocked_effects: tuple[str, ...] = BROWSER_HARNESS_BLOCKED_EFFECTS

    def validate(self) -> None:
        if self.status != BROWSER_HARNESS_DECISION_STATUS:
            raise ValueError("invalid Browser Harness adoption decision status")
        if self.adoption_mode != BROWSER_HARNESS_ADOPTION_MODE:
            raise ValueError("invalid Browser Harness adoption mode")
        if self.browser_harness_adopted:
            raise ValueError("raw Browser Harness must not be marked adopted")
        if self.browser_harness_js_adopted:
            raise ValueError("Browser Harness JS must not be marked adopted")
        if self.raw_cdp_surface_adopted:
            raise ValueError("raw CDP surface must not be marked adopted")
        if not self.domain_skill_pattern_adopted:
            raise ValueError("domain skill pattern should be adopted as ChaseOS-reviewed memory")
        if not self.interaction_skill_taxonomy_adopted:
            raise ValueError("interaction skill taxonomy should be adopted as a ChaseOS design pattern")
        if not self.external_references:
            raise ValueError("external references are required")
        for reference in self.external_references:
            reference.validate()
        if not self.adopted_patterns:
            raise ValueError("adopted patterns are required")
        if not self.rejected_patterns:
            raise ValueError("rejected patterns are required")
        if not self.gated_future_patterns:
            raise ValueError("gated future patterns are required")
        if not self.required_chaseos_controls:
            raise ValueError("required ChaseOS controls are required")
        if not self.next_allowed_step:
            raise ValueError("next allowed step is required")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.browser_harness_install_attempted,
            self.browser_harness_cli_run_attempted,
            self.real_browser_profile_attachment_attempted,
            self.remote_browser_provisioning_attempted,
            self.profile_sync_attempted,
            self.cookie_or_session_read_attempted,
            self.freeform_cdp_snippet_execution_attempted,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Browser Harness adoption decision attempted a forbidden effect")
        if not self.read_only:
            raise ValueError("Browser Harness adoption decision must be read-only")
        if not self.blocked_effects:
            raise ValueError("blocked effects must be declared")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "decision_id": self.decision_id,
            "status": self.status,
            "adoption_mode": self.adoption_mode,
            "browser_harness_adopted": self.browser_harness_adopted,
            "browser_harness_js_adopted": self.browser_harness_js_adopted,
            "raw_cdp_surface_adopted": self.raw_cdp_surface_adopted,
            "domain_skill_pattern_adopted": self.domain_skill_pattern_adopted,
            "interaction_skill_taxonomy_adopted": self.interaction_skill_taxonomy_adopted,
            "external_references": [reference.to_dict() for reference in self.external_references],
            "adopted_patterns": list(self.adopted_patterns),
            "rejected_patterns": list(self.rejected_patterns),
            "gated_future_patterns": list(self.gated_future_patterns),
            "required_chaseos_controls": list(self.required_chaseos_controls),
            "next_allowed_step": self.next_allowed_step,
            "read_only": self.read_only,
            "dependency_install_attempted": self.dependency_install_attempted,
            "browser_harness_install_attempted": self.browser_harness_install_attempted,
            "browser_harness_cli_run_attempted": self.browser_harness_cli_run_attempted,
            "real_browser_profile_attachment_attempted": self.real_browser_profile_attachment_attempted,
            "remote_browser_provisioning_attempted": self.remote_browser_provisioning_attempted,
            "profile_sync_attempted": self.profile_sync_attempted,
            "cookie_or_session_read_attempted": self.cookie_or_session_read_attempted,
            "freeform_cdp_snippet_execution_attempted": self.freeform_cdp_snippet_execution_attempted,
            "trusted_skill_write_attempted": self.trusted_skill_write_attempted,
            "skill_activation_attempted": self.skill_activation_attempted,
            "agent_bus_enqueue_attempted": self.agent_bus_enqueue_attempted,
            "provider_call_attempted": self.provider_call_attempted,
            "gate_mutation_attempted": self.gate_mutation_attempted,
            "canonical_writeback_attempted": self.canonical_writeback_attempted,
            "blocked_effects": list(self.blocked_effects),
        }


def build_browser_harness_adoption_decision(
    *,
    generated_at: str | None = None,
) -> BrowserHarnessAdoptionDecision:
    """Return the current ChaseOS Browser Harness adoption decision."""
    decision = BrowserHarnessAdoptionDecision(
        generated_at=generated_at or _now_utc(),
        decision_id="browser_harness_adoption_decision_20260502",
        status=BROWSER_HARNESS_DECISION_STATUS,
        adoption_mode=BROWSER_HARNESS_ADOPTION_MODE,
        browser_harness_adopted=False,
        browser_harness_js_adopted=False,
        raw_cdp_surface_adopted=False,
        domain_skill_pattern_adopted=True,
        interaction_skill_taxonomy_adopted=True,
        external_references=(
            BrowserHarnessExternalReference(
                repo="browser-use/browser-harness",
                url="https://github.com/browser-use/browser-harness",
                license="MIT",
                observed_pattern="Thin CDP harness with domain-skills and interaction-skills.",
                chaseos_use="Reference pattern only; adapt skills lifecycle behind AOR/Gate/SiteOps.",
            ),
            BrowserHarnessExternalReference(
                repo="browser-use/browser-harness-js",
                url="https://github.com/browser-use/browser-harness-js",
                license="MIT",
                observed_pattern="Typed direct CDP method surface over a persistent session.",
                chaseos_use="Reference only; too much raw CDP authority for direct adoption.",
            ),
            BrowserHarnessExternalReference(
                repo="browser-use/workflow-use",
                url="https://github.com/browser-use/workflow-use",
                license="AGPL-3.0",
                observed_pattern="Workflow generation, storage, replay, and graph UI.",
                chaseos_use="Concept reference only; no code copy without license review.",
            ),
        ),
        adopted_patterns=(
            "domain skill memory as reviewed SiteOps/BOSL candidates",
            "interaction skill taxonomy for reusable browser mechanics",
            "screenshots and page observations as run evidence",
            "search existing site skills before inventing a new flow",
            "contribute durable selectors, waits, traps, and failure patterns back as reviewable candidates",
        ),
        rejected_patterns=(
            "attach directly to the operator's real Chrome profile by default",
            "run free-form browser Python or CDP snippets from prompts",
            "allow the agent to edit live helper files mid-run as an authority path",
            "sync cookies or browser profiles into the runtime by default",
            "provision remote/cloud browser sessions without an explicit approval contract",
            "auto-promote generated domain skills into active runtime memory",
        ),
        gated_future_patterns=(
            "ChaseOS-native Browser Harness compatibility wrapper with throwaway profile only",
            "domain-skill import from external repos into untrusted review candidates",
            "interaction-skill taxonomy import into docs or inactive registry records",
            "workflow replay cache after separate license and implementation review",
            "authenticated/session-bearing runs only through explicit AOR manifests and approvals",
        ),
        required_chaseos_controls=(
            "AOR workflow manifest",
            "Gate operation check",
            "allowed-domain policy",
            "throwaway browser profile default",
            "no credential/cookie/profile export",
            "Agent Activity log",
            "Browser Run log",
            "draft-only skill candidate generation",
            "human/operator review before promotion",
            "no canonical writeback from browser evidence",
        ),
        next_allowed_step=(
            "Keep Browser Harness reference-only; continue production work through full VincisOS product UI proof or a separate workflow-cache design pass."
        ),
    )
    decision.validate()
    return decision


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report the read-only Browser Harness adoption decision.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    decision = build_browser_harness_adoption_decision()
    payload = decision.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"adoption_mode: {payload['adoption_mode']}")
        print(f"browser_harness_adopted: {payload['browser_harness_adopted']}")
        print(f"next_allowed_step: {payload['next_allowed_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
