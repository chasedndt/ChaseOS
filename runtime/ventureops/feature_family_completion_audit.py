"""Whole-feature-family completion audit for ChaseOS VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.real_evidence_closeout_readiness import build_real_evidence_closeout_readiness
from runtime.ventureops.registry import load_use_case_registry, workflow_records
from runtime.ventureops.validation import (
    audit_external_readiness_completion,
    validate_registry,
    validate_schema_templates,
)


OBJECTIVE = (
    "Build the ChaseOS VentureOps feature family as a portable, instance-aware, governed "
    "workflow-pack system with architecture, registry, templates, personalization/readiness, "
    "workflow-pack examples, proof standards, validation tests, truth-sync docs, reviewed "
    "VentureOps-externaal handover, and external completion evidence."
)

SUCCESS_CRITERIA = [
    "feature-family architecture and governance docs exist",
    "portable instance-aware profiling and recommendation helpers exist",
    "workflow registry validates and contains required workflow families",
    "schema templates and operator templates exist",
    "at least two workflow-pack examples exist",
    "proof-card and scorecard standards exist",
    "TDD-backed validation tests exist",
    "truth-sync docs and session logs are indexed",
    "VentureOps-externaal readiness handover is reviewed and valid",
    "external live client workflow proof exists",
    "live revenue workflow proof exists",
    "ready final evidence bundle validation report exists",
]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _item(requirement: str, status: str, evidence: list[str], notes: str) -> dict[str, Any]:
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "notes": notes,
    }


def _existing(root: Path, paths: list[str]) -> list[str]:
    return [path for path in paths if (root / path).exists()]


def _resolve_report_target(path: str | Path, root: Path) -> tuple[Path | None, str | None, str | None]:
    raw = Path(path)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None, None, f"report_path escapes vault root: {path}"
    return resolved, str(relative).replace("\\", "/"), None


def build_feature_family_completion_audit(vault_root: str | Path) -> dict[str, Any]:
    """Map the VentureOps feature-family objective to concrete repo evidence."""
    root = Path(vault_root).resolve()
    goal_path = root / "docs" / "goal.md"
    goal_text = _read_text(goal_path)
    registry_validation = validate_registry(root)
    schema_validation = validate_schema_templates(root)
    external = audit_external_readiness_completion(root)
    closeout = build_real_evidence_closeout_readiness(root)
    records = workflow_records(load_use_case_registry(root))
    pack_paths = sorted((root / "runtime" / "workflows" / "registry" / "packs").glob("*.yaml"))

    architecture_docs = [
        "06_AGENTS/VentureOps-Architecture.md",
        "06_AGENTS/VentureOps-Instance-Intelligence.md",
        "06_AGENTS/Workflow-Recommendation-Engine.md",
        "06_AGENTS/Revenue-Workflow-Registry.md",
        "06_AGENTS/Workflow-Pack-Standard.md",
        "06_AGENTS/Customer-Proof-Artifact-Standard.md",
        "06_AGENTS/Agent-Scorecard-Standard.md",
        "06_AGENTS/Runtime-Adapter-Use-Case-Matrix.md",
        "06_AGENTS/Workflow-Exchange-Readiness-Standard.md",
    ]
    foundation_helpers = [
        "runtime/ventureops/instance_profile.py",
        "runtime/ventureops/recommendations.py",
        "runtime/ventureops/registry.py",
        "runtime/ventureops/proof_cards.py",
        "runtime/ventureops/validation.py",
    ]
    operator_templates = [
        "05_TEMPLATES/Workflow-Pack-Template.md",
        "05_TEMPLATES/Proof-of-Run-Template.md",
        "05_TEMPLATES/Agent-Scorecard-Template.md",
        "05_TEMPLATES/Domain-Playbook-Template.md",
        "05_TEMPLATES/Runtime-Adapter-Checklist.md",
        "05_TEMPLATES/Workflow-Monetization-Canvas.md",
        "05_TEMPLATES/Workflow-Exchange-Listing-Template.md",
        "05_TEMPLATES/Real-Client-Scope-Approval-Template.md",
        "05_TEMPLATES/Real-Client-Scope-Evidence-Template.md",
        "05_TEMPLATES/Live-Revenue-Evidence-Template.md",
    ]
    proof_standards = [
        "06_AGENTS/Customer-Proof-Artifact-Standard.md",
        "06_AGENTS/Agent-Scorecard-Standard.md",
        "runtime/workflows/registry/templates/proof_card_schema.yaml",
        "runtime/workflows/registry/templates/agent_scorecard_schema.yaml",
        "runtime/ventureops/proof_cards.py",
    ]
    tdd_evidence = [
        "runtime/ventureops/test_ventureops.py",
        "runtime/ventureops/test_agent_runtime_governance_audit_workflow.py",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-real-evidence-closeout-readiness.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-scope-evidence-approval-prerequisite.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-scope-evidence-full-validation-cli.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-externaal-handover-next-pass-correction.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-audit-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-closeout-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-next-real-use-pass.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-invalid-packet-status-hardening.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-live-client-readiness-fields.md",
        "07_LOGS/Build-Logs/2026-05-11-ChaseOS-ventureops-runbook-contract-readiness-disclosure.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-proof-cli-dynamic-date-default.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-input-manifest.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-intake-workflow-proof-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-readiness-workflow-proof-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-completion-audit-current-truth-sync.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-real-client-input-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-input-manifest-dated-report-default.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-revenue-readiness-report-freshness.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-discovery-real-client-input-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-output-requirement.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-scope-output-requirement.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-scope-output-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-externaal-scope-output-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-feature-audit-externaal-route-surface.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-no-evidence-manifest-scope-output-routing.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-packet-output-collision-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-guarded-proof-output-collision-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-revenue-completion-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-source-digest-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-completion-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-reference-consistency-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-revenue-reference-consistency-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-receipt-artifact-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-evidence-bundle-validation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-bundle-validation-step.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-evidence-bundle-packet-builder.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-bundle-packet-authoring-step.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-packet-path-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-external-packet-path-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-completion-gate.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-feature-audit-success-criteria-final-bundle.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-output-path-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-report-dated-default.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-validation-report-default-collision-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-client-scope-packet-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-revenue-packet-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-bundle-report-reference-revalidation.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-validation-report-write-route.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-audit-report-write-route.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-audit-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-external-readiness-audit-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-final-runbook-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-evidence-closeout-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-evidence-intake-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-report-audit-flags.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-real-client-manifest-contract-report-disclosure.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-live-readiness-report-write-guard.md",
        "07_LOGS/Build-Logs/2026-05-12-ChaseOS-ventureops-client-safe-delivery-artifact-validation.md",
    ]
    truth_sync_evidence = [
        "README.md",
        "ROADMAP.md",
        "00_HOME/Now.md",
        "docs/goal.md",
        "07_LOGS/Build-Logs/Build-Logs-Index.md",
        "99_ARCHIVE/Documentation-History/Documentation-History-Index.md",
        "07_LOGS/Daily/2026-05-11.md",
        "07_LOGS/Daily/2026-05-12.md",
        "07_LOGS/Daily/Daily-Index.md",
    ]

    architecture_verified = len(_existing(root, architecture_docs)) == len(architecture_docs)
    foundation_verified = len(_existing(root, foundation_helpers)) == len(foundation_helpers)
    templates_verified = schema_validation["ok"] and len(_existing(root, operator_templates)) == len(operator_templates)
    examples_verified = len(pack_paths) >= 2
    proof_standards_verified = len(_existing(root, proof_standards)) == len(proof_standards)
    tdd_verified = len(_existing(root, tdd_evidence)) == len(tdd_evidence)
    truth_sync_verified = len(_existing(root, truth_sync_evidence)) == len(truth_sync_evidence)
    handover_verified = bool(external.get("requested_handover_alias_valid"))
    handover_scope_output_route_verified = bool(external.get("requested_handover_scope_output_route_valid"))
    real_client_input_manifest_report_write_guard_verified = bool(
        external.get("real_client_input_manifest_report_write_guard_valid")
    )
    real_client_input_manifest_report_dated_default_verified = bool(
        external.get("real_client_input_manifest_report_dated_default_valid")
    )
    real_client_input_manifest_report_default_collision_guard_verified = bool(
        external.get("real_client_input_manifest_report_default_collision_guard_valid")
    )
    live_readiness_report_write_guard_verified = bool(external.get("live_readiness_report_write_guard_valid"))
    live_readiness_report_dated_default_verified = bool(external.get("live_readiness_report_dated_default_valid"))
    live_readiness_report_default_collision_guard_verified = bool(
        external.get("live_readiness_report_default_collision_guard_valid")
    )
    external_readiness_audit_report_write_guard_verified = bool(
        external.get("external_readiness_audit_report_write_guard_valid")
    )
    external_readiness_audit_report_dated_default_verified = bool(
        external.get("external_readiness_audit_report_dated_default_valid")
    )
    external_readiness_audit_report_default_collision_guard_verified = bool(
        external.get("external_readiness_audit_report_default_collision_guard_valid")
    )
    feature_family_completion_audit_report_write_guard_verified = bool(
        external.get("feature_family_completion_audit_report_write_guard_valid")
    )
    feature_family_completion_audit_report_dated_default_verified = bool(
        external.get("feature_family_completion_audit_report_dated_default_valid")
    )
    feature_family_completion_audit_report_default_collision_guard_verified = bool(
        external.get("feature_family_completion_audit_report_default_collision_guard_valid")
    )
    final_external_runbook_report_write_guard_verified = bool(
        external.get("final_external_runbook_report_write_guard_valid")
    )
    final_external_runbook_report_dated_default_verified = bool(
        external.get("final_external_runbook_report_dated_default_valid")
    )
    final_external_runbook_report_default_collision_guard_verified = bool(
        external.get("final_external_runbook_report_default_collision_guard_valid")
    )
    real_evidence_closeout_report_write_guard_verified = bool(
        external.get("real_evidence_closeout_report_write_guard_valid")
    )
    real_evidence_closeout_report_dated_default_verified = bool(
        external.get("real_evidence_closeout_report_dated_default_valid")
    )
    real_evidence_closeout_report_default_collision_guard_verified = bool(
        external.get("real_evidence_closeout_report_default_collision_guard_valid")
    )
    evidence_intake_report_write_guard_verified = bool(external.get("evidence_intake_report_write_guard_valid"))
    evidence_intake_report_dated_default_verified = bool(external.get("evidence_intake_report_dated_default_valid"))
    evidence_intake_report_default_collision_guard_verified = bool(
        external.get("evidence_intake_report_default_collision_guard_valid")
    )
    packet_collision_guard_verified = bool(external.get("external_packet_output_collision_guard_valid"))
    packet_path_guard_verified = bool(external.get("external_packet_path_guard_valid"))
    proof_collision_guard_verified = bool(external.get("guarded_proof_output_collision_guard_valid"))
    revenue_reference_revalidation_verified = bool(external.get("revenue_completion_reference_revalidation_valid"))
    live_revenue_packet_reference_revalidation_verified = bool(
        external.get("live_revenue_packet_reference_revalidation_valid")
    )
    live_client_source_digest_validation_verified = bool(external.get("live_client_source_digest_validation_valid"))
    live_client_reference_revalidation_verified = bool(
        external.get("live_client_completion_reference_revalidation_valid")
    )
    live_client_scope_packet_reference_revalidation_verified = bool(
        external.get("live_client_scope_packet_reference_revalidation_valid")
    )
    live_client_reference_consistency_verified = bool(
        external.get("live_client_reference_consistency_validation_valid")
    )
    revenue_reference_consistency_verified = bool(external.get("revenue_reference_consistency_validation_valid"))
    receipt_artifact_validation_verified = bool(external.get("receipt_artifact_validation_valid"))
    client_safe_delivery_artifact_validation_verified = bool(
        external.get("client_safe_delivery_artifact_validation_valid")
    )
    final_evidence_bundle_validator_verified = bool(external.get("final_evidence_bundle_validator_valid"))
    final_evidence_bundle_validation_report_write_guard_verified = bool(
        external.get("final_evidence_bundle_validation_report_write_guard_valid")
    )
    final_evidence_bundle_validation_report_dated_default_verified = bool(
        external.get("final_evidence_bundle_validation_report_dated_default_valid")
    )
    final_evidence_bundle_validation_report_default_collision_guard_verified = bool(
        external.get("final_evidence_bundle_validation_report_default_collision_guard_valid")
    )
    final_evidence_bundle_packet_builder_verified = bool(
        external.get("final_evidence_bundle_packet_builder_cli_valid")
    )
    final_evidence_bundle_packet_path_guard_verified = bool(
        external.get("final_evidence_bundle_packet_path_guard_valid")
    )
    final_evidence_bundle_report_reference_revalidation_verified = bool(
        external.get("final_evidence_bundle_report_reference_revalidation_valid")
    )
    final_evidence_bundle_validation_ready = bool(external.get("final_evidence_bundle_validation_ready"))
    external_complete = bool(external.get("complete"))
    missing_requirements = list(external.get("missing_requirements") or [])

    checklist = [
        _item(
            "objective restated and tracked",
            "verified" if goal_path.exists() and "OVERALL OBJECTIVE" in goal_text else "failed",
            ["docs/goal.md"] if goal_path.exists() else [],
            "Goal file carries the original VentureOps objective and current honest status.",
        ),
        _item(
            "feature-family architecture docs",
            "verified" if architecture_verified else "failed",
            _existing(root, architecture_docs),
            "Architecture and governance docs define VentureOps as a governed workflow/product layer.",
        ),
        _item(
            "portable instance-aware workflow-pack foundation",
            "verified" if foundation_verified else "failed",
            _existing(root, foundation_helpers),
            "Runtime helpers support profiling, recommendations, registry access, proof cards, and validation.",
        ),
        _item(
            "workflow registry and required workflow families",
            "verified" if registry_validation["ok"] and len(records) >= 15 else "failed",
            ["runtime/workflows/registry/use_case_registry.yaml"],
            f"Registry validation ok={registry_validation['ok']} with {len(records)} workflow records.",
        ),
        _item(
            "templates and schemas",
            "verified" if templates_verified else "failed",
            _existing(root, operator_templates)
            + ["runtime/workflows/registry/templates/" + path.name for path in (root / "runtime/workflows/registry/templates").glob("*.yaml")],
            "Operator templates and machine-readable schema templates exist, including real scope approval, scope evidence, and revenue evidence packets.",
        ),
        _item(
            "first workflow-pack examples",
            "verified" if examples_verified else "failed",
            [str(path.relative_to(root)).replace("\\", "/") for path in pack_paths],
            "At least two portable workflow-pack examples exist.",
        ),
        _item(
            "proof-card and scorecard standards",
            "verified" if proof_standards_verified else "failed",
            _existing(root, proof_standards),
            "Proof artifact and scorecard standards are documented and schema-backed.",
        ),
        _item(
            "TDD-backed validation tests",
            "verified" if tdd_verified else "failed",
            _existing(root, tdd_evidence),
            "VentureOps tests and build logs preserve red -> green -> truth-sync evidence.",
        ),
        _item(
            "truth-sync docs and indexes",
            "verified" if truth_sync_verified else "failed",
            _existing(root, truth_sync_evidence),
            "Current truth docs, build logs, documentation history, daily note, and indexes are present.",
        ),
        _item(
            "requested VentureOps-externaal handover reviewed",
            "verified" if handover_verified and handover_scope_output_route_verified else "failed",
            [str(external.get("requested_handover_path"))]
            if handover_verified and handover_scope_output_route_verified
            else [],
            "Typo-compatible handover alias is validated by the external readiness audit and its scope output route is validated.",
        ),
        _item(
            "real evidence closeout readiness",
            "verified" if closeout.get("ok") else "failed",
            ["runtime/ventureops/real_evidence_closeout_readiness.py"],
            "Closeout command reports final external blockers without execution or completion overclaim.",
        ),
        _item(
            "real evidence closeout report write guard",
            "verified" if real_evidence_closeout_report_write_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if real_evidence_closeout_report_write_guard_verified
            else [],
            "Real evidence closeout report writeback rejects existing report paths and escaped report paths before blocked-state report writeback.",
        ),
        _item(
            "real evidence closeout report dated default",
            "verified" if real_evidence_closeout_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if real_evidence_closeout_report_dated_default_verified
            else [],
            "Real evidence closeout report writeback uses a date-stamped default report path when no explicit report path is supplied.",
        ),
        _item(
            "real evidence closeout report default collision guard",
            "verified" if real_evidence_closeout_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if real_evidence_closeout_report_default_collision_guard_verified
            else [],
            "Real evidence closeout report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "real-client input manifest report write guard",
            "verified" if real_client_input_manifest_report_write_guard_verified else "failed",
            [
                "runtime/ventureops/real_client_input_manifest.py",
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if real_client_input_manifest_report_write_guard_verified
            else [],
            "Real-client input manifest report writeback blocks existing report paths and escaped report paths, while omitted report paths use the next available dated default.",
        ),
        _item(
            "real-client input manifest report dated default",
            "verified" if real_client_input_manifest_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if real_client_input_manifest_report_dated_default_verified
            else [],
            "Real-client input manifest report writeback uses a date-stamped default report path when no explicit report path is supplied.",
        ),
        _item(
            "real-client input manifest report default collision guard",
            "verified" if real_client_input_manifest_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if real_client_input_manifest_report_default_collision_guard_verified
            else [],
            "Real-client input manifest report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "live readiness report write guard",
            "verified" if live_readiness_report_write_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if live_readiness_report_write_guard_verified
            else [],
            "Live client and live revenue readiness report writeback blocks existing report paths and escaped report paths before blocked-state report writeback.",
        ),
        _item(
            "live readiness report dated default",
            "verified" if live_readiness_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if live_readiness_report_dated_default_verified
            else [],
            "Live client and live revenue readiness report writeback uses date-stamped report paths when no explicit report path is supplied.",
        ),
        _item(
            "live readiness report default collision guard",
            "verified" if live_readiness_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if live_readiness_report_default_collision_guard_verified
            else [],
            "Live client and live revenue readiness report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "evidence intake report write guard",
            "verified" if evidence_intake_report_write_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if evidence_intake_report_write_guard_verified
            else [],
            "Evidence intake report writeback rejects existing report paths and escaped report paths before blocked-state report writeback.",
        ),
        _item(
            "evidence intake report dated default",
            "verified" if evidence_intake_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if evidence_intake_report_dated_default_verified
            else [],
            "Evidence intake report writeback uses a date-stamped default report path when no explicit report path is supplied.",
        ),
        _item(
            "evidence intake report default collision guard",
            "verified" if evidence_intake_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if evidence_intake_report_default_collision_guard_verified
            else [],
            "Evidence intake report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "external readiness audit report write guard",
            "verified" if external_readiness_audit_report_write_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if external_readiness_audit_report_write_guard_verified
            else [],
            "External readiness audit report writeback rejects existing report paths and escaped report paths before blocked-state audit report writeback.",
        ),
        _item(
            "external readiness audit report dated default",
            "verified" if external_readiness_audit_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if external_readiness_audit_report_dated_default_verified
            else [],
            "External readiness audit report writeback uses a date-stamped default report path when no explicit report path is supplied.",
        ),
        _item(
            "external readiness audit report default collision guard",
            "verified" if external_readiness_audit_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if external_readiness_audit_report_default_collision_guard_verified
            else [],
            "External readiness audit report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "external packet output collision guard",
            "verified" if packet_collision_guard_verified else "failed",
            [
                "runtime/ventureops/scope_approval_packet_builder.py",
                "runtime/ventureops/scope_evidence_packet_builder.py",
                "runtime/ventureops/delivery_proof_packet_builder.py",
                "runtime/ventureops/revenue_evidence_packet_builder.py",
            ]
            if packet_collision_guard_verified
            else [],
            "External packet builders reject existing output paths so final proof artifacts are create-only at the authoring boundary.",
        ),
        _item(
            "external packet path guard",
            "verified" if packet_path_guard_verified else "failed",
            [
                "runtime/ventureops/scope_approval_packet_builder.py",
                "runtime/ventureops/scope_evidence_packet_builder.py",
                "runtime/ventureops/delivery_proof_packet_builder.py",
                "runtime/ventureops/revenue_evidence_packet_builder.py",
            ]
            if packet_path_guard_verified
            else [],
            "External packet builders block escaped source/proof/output paths without writing outside the vault root.",
        ),
        _item(
            "guarded proof output collision guard",
            "verified" if proof_collision_guard_verified else "failed",
            [
                "runtime/ventureops/live_client_scope_proof.py",
                "runtime/ventureops/live_client_workflow_proof.py",
                "runtime/ventureops/live_revenue_proof.py",
            ]
            if proof_collision_guard_verified
            else [],
            "Guarded proof commands reject existing proof output paths before writing final proof artifacts.",
        ),
        _item(
            "revenue completion reference revalidation",
            "verified" if revenue_reference_revalidation_verified else "failed",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation.validate_live_delivery_proof_artifact",
            ]
            if revenue_reference_revalidation_verified
            else [],
            "Final completion discovery revalidates referenced receipt, delivery proof, and client-safe delivery artifacts instead of trusting embedded revenue-proof flags.",
        ),
        _item(
            "live-revenue packet reference revalidation",
            "verified" if live_revenue_packet_reference_revalidation_verified else "failed",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation.validate_live_revenue_evidence",
            ]
            if live_revenue_packet_reference_revalidation_verified
            else [],
            "Final completion discovery revalidates the referenced revenue packet from disk before accepting proof-only revenue completion.",
        ),
        _item(
            "live-client workflow source digest validation",
            "verified" if live_client_source_digest_validation_verified else "failed",
            [
                "runtime.ventureops.validation.validate_live_client_workflow_proof_artifact",
                "runtime/ventureops/live_client_workflow_proof.py",
            ]
            if live_client_source_digest_validation_verified
            else [],
            "Live-client workflow proof artifacts must carry source digest entries that cover approved read paths.",
        ),
        _item(
            "live-client completion reference revalidation",
            "verified" if live_client_reference_revalidation_verified else "failed",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation.validate_live_client_scope_proof_artifact",
                "runtime.ventureops.validation.validate_agent_scorecard",
            ]
            if live_client_reference_revalidation_verified
            else [],
            "Final completion discovery revalidates referenced scope proof gate, client report, and scorecard artifacts before accepting a live-client workflow proof.",
        ),
        _item(
            "live-client scope packet reference revalidation",
            "verified" if live_client_scope_packet_reference_revalidation_verified else "failed",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation.validate_real_client_scope_evidence",
                "runtime.ventureops.validation.validate_scope_evidence_approval_artifact",
                "runtime.ventureops.validation.validate_scope_evidence_source_paths",
            ]
            if live_client_scope_packet_reference_revalidation_verified
            else [],
            "Final completion discovery revalidates the referenced scope packet, approval artifact, and approved source files before accepting a live-client workflow proof.",
        ),
        _item(
            "live-client reference consistency validation",
            "verified" if live_client_reference_consistency_verified else "failed",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation.validate_live_client_scope_proof_artifact",
                "runtime.ventureops.validation.validate_agent_scorecard",
            ]
            if live_client_reference_consistency_verified
            else [],
            "Final completion discovery verifies referenced scope gate and scorecard artifacts match the workflow proof scope, approval, read paths, workflow id, and run id.",
        ),
        _item(
            "revenue reference consistency validation",
            "verified" if revenue_reference_consistency_verified else "failed",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation.validate_live_delivery_proof_artifact",
            ]
            if revenue_reference_consistency_verified
            else [],
            "Final completion discovery verifies referenced delivery and live-client proof artifacts match the proof-only revenue artifact workflow id and client label.",
        ),
        _item(
            "receipt artifact validation",
            "verified" if receipt_artifact_validation_verified else "failed",
            [
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime.ventureops.validation._validate_redacted_receipt_artifact",
            ]
            if receipt_artifact_validation_verified
            else [],
            "Final completion discovery validates referenced receipt artifacts are JSON objects marked redacted before accepting proof-only revenue completion.",
        ),
        _item(
            "client-safe delivery artifact validation",
            "verified" if client_safe_delivery_artifact_validation_verified else "failed",
            [
                "runtime.ventureops.validation.validate_client_safe_delivery_artifact",
                "runtime.ventureops.validation.discover_external_completion_artifacts",
                "runtime/ventureops/delivery_proof_packet_builder.py",
                "runtime/ventureops/final_external_evidence_bundle.py",
            ]
            if client_safe_delivery_artifact_validation_verified
            else [],
            "Final delivery/revenue closeout rejects arbitrary client-safe delivery files and requires redacted JSON with no side-effect or secret-shaped fields.",
        ),
        _item(
            "final external evidence bundle validator",
            "verified" if final_evidence_bundle_validator_verified else "failed",
            [
                "runtime/ventureops/final_external_evidence_bundle.py",
                "chaseos ventureops final-evidence-bundle",
            ]
            if final_evidence_bundle_validator_verified
            else [],
            "Final bundle validation checks the whole external proof chain before the final completion audit is rerun.",
        ),
        _item(
            "final evidence bundle validation report write guard",
            "verified" if final_evidence_bundle_validation_report_write_guard_verified else "failed",
            [
                "runtime/ventureops/final_external_evidence_bundle.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if final_evidence_bundle_validation_report_write_guard_verified
            else [],
            "Final bundle validation report writeback rejects existing report paths and escaped report paths before final completion audit rerun.",
        ),
        _item(
            "final evidence bundle validation report dated default",
            "verified" if final_evidence_bundle_validation_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if final_evidence_bundle_validation_report_dated_default_verified
            else [],
            "Final bundle validation report writeback uses a date-stamped default report path when no explicit report path is supplied.",
        ),
        _item(
            "final evidence bundle validation report default collision guard",
            "verified" if final_evidence_bundle_validation_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if final_evidence_bundle_validation_report_default_collision_guard_verified
            else [],
            "Final bundle validation report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "feature-family completion audit report write guard",
            "verified" if feature_family_completion_audit_report_write_guard_verified else "failed",
            [
                "runtime/ventureops/feature_family_completion_audit.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if feature_family_completion_audit_report_write_guard_verified
            else [],
            "Feature-family completion audit report writeback rejects existing report paths and escaped report paths before final closeout report writeback.",
        ),
        _item(
            "feature-family completion audit report dated default",
            "verified" if feature_family_completion_audit_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if feature_family_completion_audit_report_dated_default_verified
            else [],
            "Feature-family completion audit report writeback uses a date-stamped default report path when no explicit report path is supplied.",
        ),
        _item(
            "feature-family completion audit report default collision guard",
            "verified" if feature_family_completion_audit_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if feature_family_completion_audit_report_default_collision_guard_verified
            else [],
            "Feature-family completion audit report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "final external runbook report write guard",
            "verified" if final_external_runbook_report_write_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if final_external_runbook_report_write_guard_verified
            else [],
            "Final external runbook report writeback rejects existing report paths and escaped report paths before blocked-state report writeback.",
        ),
        _item(
            "final external runbook report dated default",
            "verified" if final_external_runbook_report_dated_default_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if final_external_runbook_report_dated_default_verified
            else [],
            "Final external runbook report writeback uses a date-stamped default report path when no explicit report path is supplied.",
        ),
        _item(
            "final external runbook report default collision guard",
            "verified" if final_external_runbook_report_default_collision_guard_verified else "failed",
            [
                "runtime/cli/ventureops_commands.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if final_external_runbook_report_default_collision_guard_verified
            else [],
            "Final external runbook report writeback chooses the next available date-stamped default path when the base default already exists.",
        ),
        _item(
            "final evidence bundle packet builder CLI",
            "verified" if final_evidence_bundle_packet_builder_verified else "failed",
            [
                "runtime/ventureops/final_evidence_bundle_packet_builder.py",
                "chaseos ventureops final-evidence-bundle-packet",
            ]
            if final_evidence_bundle_packet_builder_verified
            else [],
            "Builder writes the final evidence bundle envelope that the validator consumes.",
        ),
        _item(
            "final evidence bundle packet path guard",
            "verified" if final_evidence_bundle_packet_path_guard_verified else "failed",
            [
                "runtime/ventureops/final_evidence_bundle_packet_builder.py",
                "runtime/ventureops/test_ventureops.py",
            ]
            if final_evidence_bundle_packet_path_guard_verified
            else [],
            "Builder blocks escaped final bundle packet paths without writing outside the vault root.",
        ),
        _item(
            "final evidence bundle report reference revalidation",
            "verified" if final_evidence_bundle_report_reference_revalidation_verified else "failed",
            [
                "runtime.ventureops.validation.discover_final_evidence_bundle_validation_reports",
                "runtime.ventureops.final_external_evidence_bundle.validate_final_external_evidence_bundle",
            ]
            if final_evidence_bundle_report_reference_revalidation_verified
            else [],
            "Final completion discovery revalidates each report's referenced bundle before accepting a ready final evidence bundle validation report.",
        ),
        _item(
            "final evidence bundle validation report",
            "verified" if final_evidence_bundle_validation_ready else "blocked",
            list((external.get("final_evidence_bundle_validation_reports") or {}).get(
                "valid_final_evidence_bundle_validation_reports"
            ) or []),
            "Final completion requires a ready final-evidence-bundle validation report that matches current final proof artifacts.",
        ),
        _item(
            "external live client and revenue completion",
            "verified" if external_complete else "blocked",
            [],
            "Blocked until all required live-client, live-revenue, and final evidence bundle validation evidence exists.",
        ),
        _item(
            "full feature family completion",
            "verified" if external_complete else "blocked",
            [],
            "Foundation is implemented, but the full feature family cannot be complete until external proof gaps close.",
        ),
    ]

    failed = [item["requirement"] for item in checklist if item["status"] == "failed"]
    blocked = [item["requirement"] for item in checklist if item["status"] == "blocked"]
    complete = not failed and not blocked and not missing_requirements
    return {
        "ok": not failed,
        "complete": complete,
        "ready_for_goal_completion": complete,
        "completion_decision": "complete" if complete else "not_complete",
        "objective": OBJECTIVE,
        "success_criteria": SUCCESS_CRITERIA,
        "status": external.get("status"),
        "registry_valid": bool(registry_validation["ok"]),
        "registry_workflow_count": len(records),
        "schema_templates_valid": bool(schema_validation["ok"]),
        "workflow_pack_example_count": len(pack_paths),
        "requested_handover_alias_valid": handover_verified,
        "requested_handover_scope_output_route_valid": handover_scope_output_route_verified,
        "real_client_input_manifest_report_write_guard_valid": real_client_input_manifest_report_write_guard_verified,
        "real_client_input_manifest_report_dated_default_valid": (
            real_client_input_manifest_report_dated_default_verified
        ),
        "real_client_input_manifest_report_default_collision_guard_valid": (
            real_client_input_manifest_report_default_collision_guard_verified
        ),
        "live_readiness_report_write_guard_valid": live_readiness_report_write_guard_verified,
        "live_readiness_report_dated_default_valid": live_readiness_report_dated_default_verified,
        "live_readiness_report_default_collision_guard_valid": (
            live_readiness_report_default_collision_guard_verified
        ),
        "evidence_intake_report_write_guard_valid": evidence_intake_report_write_guard_verified,
        "evidence_intake_report_dated_default_valid": evidence_intake_report_dated_default_verified,
        "evidence_intake_report_default_collision_guard_valid": (
            evidence_intake_report_default_collision_guard_verified
        ),
        "real_evidence_closeout_report_write_guard_valid": real_evidence_closeout_report_write_guard_verified,
        "real_evidence_closeout_report_dated_default_valid": real_evidence_closeout_report_dated_default_verified,
        "real_evidence_closeout_report_default_collision_guard_valid": (
            real_evidence_closeout_report_default_collision_guard_verified
        ),
        "external_readiness_audit_report_write_guard_valid": external_readiness_audit_report_write_guard_verified,
        "external_readiness_audit_report_dated_default_valid": external_readiness_audit_report_dated_default_verified,
        "external_readiness_audit_report_default_collision_guard_valid": (
            external_readiness_audit_report_default_collision_guard_verified
        ),
        "feature_family_completion_audit_report_write_guard_valid": (
            feature_family_completion_audit_report_write_guard_verified
        ),
        "feature_family_completion_audit_report_dated_default_valid": (
            feature_family_completion_audit_report_dated_default_verified
        ),
        "feature_family_completion_audit_report_default_collision_guard_valid": (
            feature_family_completion_audit_report_default_collision_guard_verified
        ),
        "final_external_runbook_report_write_guard_valid": final_external_runbook_report_write_guard_verified,
        "final_external_runbook_report_dated_default_valid": final_external_runbook_report_dated_default_verified,
        "final_external_runbook_report_default_collision_guard_valid": (
            final_external_runbook_report_default_collision_guard_verified
        ),
        "external_packet_output_collision_guard_valid": packet_collision_guard_verified,
        "external_packet_path_guard_valid": packet_path_guard_verified,
        "guarded_proof_output_collision_guard_valid": proof_collision_guard_verified,
        "revenue_completion_reference_revalidation_valid": revenue_reference_revalidation_verified,
        "live_revenue_packet_reference_revalidation_valid": live_revenue_packet_reference_revalidation_verified,
        "live_client_source_digest_validation_valid": live_client_source_digest_validation_verified,
        "live_client_completion_reference_revalidation_valid": live_client_reference_revalidation_verified,
        "live_client_scope_packet_reference_revalidation_valid": (
            live_client_scope_packet_reference_revalidation_verified
        ),
        "live_client_reference_consistency_validation_valid": live_client_reference_consistency_verified,
        "revenue_reference_consistency_validation_valid": revenue_reference_consistency_verified,
        "receipt_artifact_validation_valid": receipt_artifact_validation_verified,
        "client_safe_delivery_artifact_validation_valid": client_safe_delivery_artifact_validation_verified,
        "final_evidence_bundle_validator_valid": final_evidence_bundle_validator_verified,
        "final_evidence_bundle_validation_report_write_guard_valid": (
            final_evidence_bundle_validation_report_write_guard_verified
        ),
        "final_evidence_bundle_validation_report_dated_default_valid": (
            final_evidence_bundle_validation_report_dated_default_verified
        ),
        "final_evidence_bundle_validation_report_default_collision_guard_valid": (
            final_evidence_bundle_validation_report_default_collision_guard_verified
        ),
        "final_evidence_bundle_packet_builder_cli_valid": final_evidence_bundle_packet_builder_verified,
        "final_evidence_bundle_packet_path_guard_valid": final_evidence_bundle_packet_path_guard_verified,
        "final_evidence_bundle_report_reference_revalidation_valid": (
            final_evidence_bundle_report_reference_revalidation_verified
        ),
        "final_evidence_bundle_validation_ready": final_evidence_bundle_validation_ready,
        "external_readiness_complete": external_complete,
        "external_completion_decision": external.get("completion_decision"),
        "missing_requirements": missing_requirements,
        "next_required_real_use_pass": external.get("next_required_real_use_pass"),
        "next_guarded_command": external.get("next_guarded_command"),
        "next_required_inputs": external.get("next_required_inputs") or [],
        "failed_requirements": failed,
        "blocked_requirements": blocked,
        "prompt_to_artifact_checklist": checklist,
        "report_written": False,
        "report_path": None,
        "live_client_scope_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": (
            "whole-feature-family completion audit only; maps objective requirements to artifacts and refuses "
            "completion until live-client, live-revenue, and final evidence bundle requirements are all satisfied"
        ),
    }


def write_feature_family_completion_audit_report(
    payload: dict[str, Any],
    path: str | Path,
    *,
    vault_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    target, relative, error = _resolve_report_target(path, root)
    if error:
        return {
            **payload,
            "ok": False,
            "report_written": False,
            "report_path": None,
            "report_write_blocked": True,
            "errors": [*list(payload.get("errors") or []), error],
        }
    assert target is not None
    assert relative is not None
    if target.exists():
        return {
            **payload,
            "ok": False,
            "report_written": False,
            "report_path": None,
            "report_write_blocked": True,
            "errors": [
                *list(payload.get("errors") or []),
                f"report path already exists: {relative}",
            ],
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **payload,
        "report_written": True,
        "report_path": str(path) if not Path(path).is_absolute() else str(target),
        "report_write_blocked": False,
        "errors": list(payload.get("errors") or []),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
