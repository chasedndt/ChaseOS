"""Read-only Phase 10 Studio-Hermes handover contract.

This module gives Phase 10 Studio and Hermes/Optimus continuation agents a
small deterministic verifier/template for the Studio-Hermes handover. It is
intentionally read-only: callers get handoff artifact expectations, active card
shape, rolling checkpoint fields, Studio MVP blocker routes, and backend
authority denial proof without AOR lifecycle execution, approval consumption,
runtime dispatch, Agent Bus writes, provider/browser/credential calls,
source-pack promotion, protected-file writes, Gate mutation, release/installer
host mutation, or canonical writeback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_VERSION = "studio.studio_hermes_handover_contract.v1"
SURFACE_ID = "studio_hermes_handover_contract"
HANDOVER_STATUS = "READ-ONLY / STUDIO-HERMES HANDOVER / NO-BACKEND AUTHORITY"

BACKEND_AUTHORITY_PROOF_FIELDS = [
    "aor_lifecycle_execution",
    "approval_consumption",
    "runtime_dispatch",
    "agent_bus_task_write",
    "provider_call",
    "browser_control",
    "credential_config_mutation",
    "source_pack_promotion",
    "protected_file_write",
    "gate_policy_mutation",
    "canonical_writeback",
    "release_installer_host_mutation",
]

DEPENDENCY_REPORT_FIELDS = [
    "missing_contract",
    "affected_phase10_or_phase11_surface",
    "lower_phase_owner_or_surface",
    "minimum_proof_needed",
    "blocked_action_reason",
]

CHECKPOINT_REQUIRED_FIELDS = [
    "current_surface",
    "artifact_paths",
    "tests_or_smokes",
    "authority_posture",
    "no_backend_authority_proof",
    "dependency_routes",
    "next_safe_action",
    "stale_or_blocked_card_summary",
]

DEFAULT_ARTIFACT_PATHS = [
    "HERMES.md",
    "06_AGENTS/Hermes-Phase11-Implementation-Handover.md",
    "06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md",
    "07_LOGS/Agent-Activity/YYYY-MM-DD-hermes-optimus-<topic>.md",
    "07_LOGS/Agent-Activity/Agent-Activity-Index.md",
    "runtime/studio/studio_hermes_handover_contract.py",
    "runtime/studio/test_studio_hermes_handover_contract.py",
]

DEFAULT_ACTIVE_CARDS = [
    {
        "id": "t_dfdc821d",
        "title": "P10-10B — Write Phase 10 Studio-Hermes handover and checkpoint narrative",
        "status": "done",
        "surface": "handover narrative",
    },
    {
        "id": "t_484b2c4c",
        "title": "P10-10C — Verify bounded Studio-Hermes handover surfaces without backend authority",
        "status": "done",
        "surface": SURFACE_ID,
    },
    {
        "id": "t_fee4398a",
        "title": "P10-10D — Review Studio-Hermes handover authority, tests, and routing",
        "status": "blocked",
        "surface": "review gate",
    },
    {
        "id": "t_9311101c",
        "title": "P11-11 — Add Phase 11 checkpoint fixture/template coverage",
        "status": "done",
        "surface": "Phase 11 checkpoint fixtures",
    },
]

DEFAULT_STUDIO_MVP_TRUTH = {
    "current_status": "internal portable MVP closed with deferrals",
    "product_status": "INTERNAL_PORTABLE_CLOSED_RELEASE_GRADE_OPEN",
    "internal_portable_mvp_closed": True,
    "release_grade_complete": False,
    "release_grade_status": "release-grade Studio remains open",
}

DEFAULT_STUDIO_MVP_BLOCKERS = [
    {
        "blocker_key": "native_packaged_visual_qa_webview2",
        "status": "release_grade_product_hardening",
        "summary": "Internal portable MVP closed with deferrals; native packaged visual QA/WebView2 evidence is release-grade product-hardening, not an internal portable MVP blocker.",
    },
    {
        "blocker_key": "approval_execution_for_chat_studio_actions",
        "status": "governed_deferred",
        "summary": "Release-grade Studio remains open because important Chat/Studio actions still need exact-once approval consumption/execution and target-effect proof.",
    },
    {
        "blocker_key": "runtime_provider_browser_execution",
        "status": "governed_deferred",
        "summary": "Internal portable MVP closed with deferrals; runtime dispatch, provider/model calls, and browser control remain release-grade/lower-phase governed lanes.",
    },
    {
        "blocker_key": "real_target_workspace_upgrade",
        "status": "release_grade_deferred",
        "summary": "Upgrade/migration proof exists in temp/proof lanes; real operator-selected workspace migration remains a release-grade open lane.",
    },
    {
        "blocker_key": "release_installer_host_mutation",
        "status": "release_grade_deferred",
        "summary": "Release-grade Studio remains open for installer/signing/startup/release work; real host mutation/release publication remains governed future work.",
    },
]

DEFAULT_DEPENDENCY_REPORTS = [
    {
        "dependency_key": "native_packaged_visual_qa_webview2",
        "missing_contract": "native packaged Studio visual QA/WebView2 visible-window release-grade proof",
        "affected_phase10_or_phase11_surface": "Phase 10 Studio product-hardening and release-readiness surface",
        "lower_phase_owner_or_surface": "Studio packaging QA / Windows WebView2 host boundary lane",
        "minimum_proof_needed": "packaged desktop app opens visibly, screenshot capture succeeds, nonblank gate passes, and temp/WebView2 ACL evidence is attached",
        "blocked_action_reason": "Hermes/Optimus may report that the internal portable MVP closed with deferrals, but must not call release-grade Studio complete or mutate host/package policy until visible native QA proof exists",
    },
    {
        "dependency_key": "approval_execution_for_chat_studio_actions",
        "missing_contract": "source-specific approval consumption and target-effect execution proof",
        "affected_phase10_or_phase11_surface": "Phase 10 Studio and Phase 11 Chat approval-gated action surfaces",
        "lower_phase_owner_or_surface": "ChaseOS Gate, approval executor, exact-once marker, and target-effect verification lanes",
        "minimum_proof_needed": "matching approval artifact, digest/scope validation, exact-once marker, duplicate refusal, target-effect evidence, and audit record",
        "blocked_action_reason": "Studio/Chat may preview or queue governed requests but must not consume approvals or perform target writes from the surface lane",
    },
    {
        "dependency_key": "runtime_provider_browser_execution",
        "missing_contract": "bounded runtime/provider/browser execution contract under approval and audit",
        "affected_phase10_or_phase11_surface": "Runtime Cockpit, Phase 11 Chat runtime dispatch, provider answer, and browser-dispatch previews",
        "lower_phase_owner_or_surface": "Phase 9 AOR, Agent Bus, RPGL/provider governance, browser runtime policy, and adapter manifests",
        "minimum_proof_needed": "approved execution envelope, eligible runtime/provider/browser route, non-surface consumer, redacted/no-secret audit proof, and replay/rollback policy",
        "blocked_action_reason": "Hermes/Optimus Studio surfaces may show dispatch/readiness posture but must not dispatch runtimes, call providers, or control browsers directly",
    },
    {
        "dependency_key": "real_target_workspace_upgrade",
        "missing_contract": "operator-selected real workspace upgrade/migration execution and rollback contract",
        "affected_phase10_or_phase11_surface": "Phase 10 workspace import/bootstrap/upgrade surfaces",
        "lower_phase_owner_or_surface": "workspace migration executor, approval gate, rollback/audit workflow, and target-vault safety policy",
        "minimum_proof_needed": "operator-selected target, preflight, approved scope/digest, exact-once execution, rollback plan, before/after proof, and no-unrelated-mutation audit",
        "blocked_action_reason": "Studio may preview upgrade readiness and proof-temp execution but must not mutate a real target workspace from the handover lane",
    },
    {
        "dependency_key": "release_installer_host_mutation",
        "missing_contract": "governed installer install/signing/startup/release host-mutation execution contract",
        "affected_phase10_or_phase11_surface": "Phase 10 release readiness, installer, signing, startup/autostart, and release-promotion surfaces",
        "lower_phase_owner_or_surface": "release governance, Windows host mutation executor, signing policy, rollback/audit lane, and Gate review",
        "minimum_proof_needed": "approved host mutation envelope, signed/installed artifact proof, rollback evidence, post-mutation verification, and operator-visible audit",
        "blocked_action_reason": "Studio-Hermes handover may route the blocker but must not install, sign for production, alter startup/registry/shortcuts, publish release, or mutate host state",
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_posix_list(values: list[str | Path] | None, fallback: list[str]) -> list[str]:
    if not values:
        return list(fallback)
    return [Path(value).as_posix() if isinstance(value, Path) else str(value) for value in values]


def _normalize_dependency_report(report: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {field: str(report.get(field, "")).strip() for field in DEPENDENCY_REPORT_FIELDS}
    if "dependency_key" in report:
        normalized["dependency_key"] = str(report["dependency_key"])
    normalized["complete"] = all(bool(normalized[field]) for field in DEPENDENCY_REPORT_FIELDS)
    return normalized


def _normalize_cards(cards: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    source = cards if cards is not None else DEFAULT_ACTIVE_CARDS
    normalized: list[dict[str, str]] = []
    for card in source:
        normalized.append(
            {
                "id": str(card.get("id", "")).strip(),
                "title": str(card.get("title", "")).strip(),
                "status": str(card.get("status", "unknown")).strip() or "unknown",
                "surface": str(card.get("surface", "Studio/Chat continuation")).strip() or "Studio/Chat continuation",
            }
        )
    return normalized


def _normalize_blockers(blockers: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    source = blockers if blockers is not None else DEFAULT_STUDIO_MVP_BLOCKERS
    normalized: list[dict[str, str]] = []
    for blocker in source:
        normalized.append(
            {
                "blocker_key": str(blocker.get("blocker_key", "")).strip(),
                "status": str(blocker.get("status", "blocked")).strip() or "blocked",
                "summary": str(blocker.get("summary", "")).strip(),
            }
        )
    return normalized


def _blocked_card_summary(cards: list[dict[str, str]], blockers: list[dict[str, str]]) -> str:
    card_bits = [f"{card['id']}={card['status']}" for card in cards if card.get("id")]
    blocker_bits = [f"{blocker['blocker_key']}={blocker['status']}" for blocker in blockers if blocker.get("blocker_key")]
    return "; ".join(card_bits + blocker_bits)


def build_studio_hermes_handover_contract(
    vault_root: str | Path,
    *,
    current_surface: str = "Phase 10 Studio / Hermes-Optimus bounded handover surface",
    artifact_paths: list[str | Path] | None = None,
    active_cards: list[dict[str, Any]] | None = None,
    studio_mvp_blockers: list[dict[str, Any]] | None = None,
    tests_or_smokes: list[str] | None = None,
    dependency_reports: list[dict[str, Any]] | None = None,
    next_safe_action: str = "Continue bounded Studio/Chat surface verification or route backend blockers to Phase 9-and-below lanes.",
) -> dict[str, Any]:
    """Build a read-only Studio-Hermes handover/checkpoint contract."""

    vault = Path(vault_root).resolve()
    artifacts = _as_posix_list(artifact_paths, DEFAULT_ARTIFACT_PATHS)
    cards = _normalize_cards(active_cards)
    blockers = _normalize_blockers(studio_mvp_blockers)
    reports_source = dependency_reports if dependency_reports is not None else DEFAULT_DEPENDENCY_REPORTS
    reports = [_normalize_dependency_report(report) for report in reports_source]
    proof = {field: False for field in BACKEND_AUTHORITY_PROOF_FIELDS}
    checks = tests_or_smokes or [
        "PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_studio_hermes_handover_contract.py -q"
    ]
    checkpoint = {
        "current_surface": current_surface,
        "artifact_paths": artifacts,
        "tests_or_smokes": checks,
        "authority_posture": "Phase 10 Studio surface only; Hermes/Optimus may verify, render, document, and route but not execute backend authority.",
        "no_backend_authority_proof": proof,
        "dependency_routes": reports,
        "next_safe_action": next_safe_action,
        "stale_or_blocked_card_summary": _blocked_card_summary(cards, blockers),
    }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": HANDOVER_STATUS,
        "phase": "Phase 10 Studio",
        "runtime_lane": "Hermes/Optimus",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "handover": {
            "current_surface": current_surface,
            "artifact_paths": artifacts,
            "active_p10_p11_cards": cards,
            "studio_mvp_truth": dict(DEFAULT_STUDIO_MVP_TRUTH),
            "studio_mvp_blockers": blockers,
            "checkpoint_contract": checkpoint,
            "dependency_reports": reports,
            "payoff": "Hermes/OpenClaw summaries can state that the internal portable MVP closed with deferrals while release-grade Studio remains open, without turning either runtime into a canonical truth engine.",
            "os_alignment": "ChaseOS remains the control plane; Studio and Chat are operator surfaces over AOR, Gate, Agent Bus, provider/browser, lifecycle, and canonical-writeback contracts.",
            "testability_now": "This verifier is testable with focused WSL-safe pytest; docs-only handoff work remains verifiable by direct file reads and link/index checks.",
        },
        "template_markdown": _render_template_markdown(
            current_surface=current_surface,
            artifacts=artifacts,
            tests_or_smokes=checks,
            proof=proof,
            reports=reports,
            next_safe_action=next_safe_action,
            blocked_summary=checkpoint["stale_or_blocked_card_summary"],
        ),
        "dependency_report_required_fields": list(DEPENDENCY_REPORT_FIELDS),
        "checkpoint_required_fields": list(CHECKPOINT_REQUIRED_FIELDS),
        "denied_by_this_surface": list(BACKEND_AUTHORITY_PROOF_FIELDS),
        "authority": {
            "surface_handoff_only": True,
            "aor_lifecycle_execution_allowed": False,
            "approval_consumption_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "provider_call_allowed": False,
            "browser_control_allowed": False,
            "credential_config_mutation_allowed": False,
            "source_pack_promotion_allowed": False,
            "protected_file_write_allowed": False,
            "gate_policy_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "release_installer_host_mutation_allowed": False,
        },
    }


def _render_template_markdown(
    *,
    current_surface: str,
    artifacts: list[str],
    tests_or_smokes: list[str],
    proof: dict[str, bool],
    reports: list[dict[str, Any]],
    next_safe_action: str,
    blocked_summary: str,
) -> str:
    proof_line = "; ".join(f"{field}={str(value).lower()}" for field, value in proof.items())
    artifact_lines = "\n".join(f"- {path}" for path in artifacts)
    test_lines = "\n".join(f"- {test}" for test in tests_or_smokes)
    dependency_lines = "\n".join(
        f"- {report.get('dependency_key', 'dependency')}: {report['missing_contract']} -> {report['lower_phase_owner_or_surface']}"
        for report in reports
    )
    return "\n".join(
        [
            "## Studio-Hermes Handover Checkpoint — <UTC timestamp>",
            f"- Current surface: {current_surface}",
            "- Artifact paths:",
            artifact_lines,
            "- Tests or smokes:",
            test_lines,
            f"- Authority posture: Phase 10 Studio surface only; no backend execution authority.",
            f"- No-backend-authority proof: {proof_line}",
            "- Dependency routes:",
            dependency_lines,
            f"- Stale/blocked card summary: {blocked_summary}",
            f"- Next safe action: {next_safe_action}",
        ]
    )
