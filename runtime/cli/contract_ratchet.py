"""Parser, command-contract, docs, and JSON smoke ratchet for ChaseOS CLI."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
from typing import Any

from runtime.cli.generate_docs import CONTRACT_PATH, DOC_PATH, load_contract, render_markdown
from runtime.cli.json_contract import JSON_CONTRACT_KEYS, build_action


CLI_PACKAGE_ROOT = Path(__file__).resolve().parent
SITEOPS_CANDIDATE_SMOKE_VAULT = (
    CLI_PACKAGE_ROOT / "fixtures" / "browser_skill_candidates_vault"
)
SETUP_STATE_SMOKE_FIXTURE = CLI_PACKAGE_ROOT / "fixtures" / "setup_state" / "setup_state.json"
INTAKE_SMOKE_FIXTURE_VAULT = CLI_PACKAGE_ROOT / "fixtures" / "intake_vault"
MAINTAIN_SMOKE_FIXTURE_VAULT = CLI_PACKAGE_ROOT / "fixtures" / "maintain_vault"
CREATOR_ENGINE_SMOKE_FIXTURE_VAULT = CLI_PACKAGE_ROOT / "fixtures" / "creator_engine_vault"
CREATOR_ENGINE_SMOKE_FIXTURE_TRANSCRIPT = (
    Path("03_INPUTS") / "Transcript-Raw" / "20260520__creator-engine-fixture.md"
)
CREATOR_ENGINE_SMOKE_FIXTURE_MEDIA = (
    Path("03_INPUTS") / "Recordings" / "20260520__creator-engine-fixture.mp4"
)
INTAKE_SMOKE_FIXTURE_ITEM = (
    INTAKE_SMOKE_FIXTURE_VAULT
    / "03_INPUTS"
    / "00_QUARANTINE"
    / "Sources"
    / "20260510__fixture__cli-ratchet-source.md"
)

COMMAND_CHOICE_DESTS = {"runtime_command", "setup_command"}
DEFAULT_PARSE_ARGS_BY_PATH = {
    ("agent-bus", "codex-daemon"): ["--readiness"],
    ("agent-bus", "watch"): ["--once"],
    ("events", "dispatch"): ["--pending"],
    ("events", "watch"): ["--once"],
    ("watch", "run"): ["--once"],
}


STANDARD_JSON_EXPECTATIONS: dict[str, tuple[tuple[str, ...], ...]] = {
    "status": (
        ("result", "status"),
        ("result", "ok"),
        ("result", "gate_status"),
        ("result", "readiness_status"),
        ("result", "completion_status"),
        ("result", "preflight_status"),
        ("result", "readiness"),
    ),
    "blocked_reason": (
        ("result", "blockers"),
        ("result", "blocked_reasons"),
        ("result", "blocked_effects"),
        ("result", "default_verify_error"),
        ("result", "live_smoke_blockers"),
        ("result", "missing_recommended_source_classes"),
        ("result", "action_readiness", "*", "blockers"),
    ),
    "writes": (
        ("result", "writes"),
        ("result", "writes_performed"),
        ("result", "writes_status_artifact"),
        ("result", "files_modified"),
        ("result", "repository_template", "writes"),
        ("result", "authority_boundary", "writes_on_request"),
    ),
    "evidence": (
        ("result", "evidence"),
        ("result", "approval_evidence_slots"),
        ("result", "source_path"),
        ("result", "latest_pointer_path"),
        ("result", "acceptance_criteria", "*", "evidence"),
        ("result", "action_readiness", "*", "evidence_needed"),
    ),
    "authority_flags": (
        ("result", "authority"),
        ("result", "authority_boundary"),
        ("result", "read_only"),
        ("result", "canonical_writeback_allowed"),
        ("result", "activation_allowed"),
        ("result", "promotion_allowed"),
    ),
}


SMOKE_COMMANDS: tuple[dict[str, Any], ...] = (
    {
        "name": "agent.list",
        "argv": ["agent", "list", "--json"],
        "expected_action": "agent.list",
        "required_result_paths": (
            ("result", "runtimes"),
            ("result", "count"),
        ),
    },
    {
        "name": "config.summary",
        "argv": ["config", "summary", "--json"],
        "expected_action": "config.summary",
        "required_result_paths": (
            ("result", "read_only"),
            ("result", "mutates_config"),
            ("result", "governance"),
        ),
    },
    {
        "name": "gate.validate",
        "argv": ["gate", "validate", "--json"],
        "expected_action": "gate.validate",
        "required_result_paths": (
            ("result", "valid"),
            ("result", "errors"),
        ),
    },
    {
        "name": "memory.status",
        "argv": ["memory", "status", "--json"],
        "expected_action": "memory.status",
        "required_result_paths": (
            ("result", "layer_c"),
            ("result", "layer_d"),
        ),
    },
    {
        "name": "schedule.validate",
        "argv": ["schedule", "validate", "--json"],
        "expected_action": "schedule.validate",
        "required_result_paths": (
            ("result", "valid"),
            ("result", "error_count"),
            ("result", "errors"),
        ),
    },
    {
        "name": "models.list",
        "argv": ["models", "list", "--json"],
        "expected_action": "models.list",
        "required_result_paths": (
            ("result", "*", "provider_id"),
            ("result", "*", "model_id"),
            ("result", "*", "configured"),
        ),
    },
    {
        "name": "providers.status",
        "argv": ["providers", "status", "--json"],
        "expected_action": "providers.status",
        "required_result_paths": (
            ("result", "*", "provider_id"),
            ("result", "*", "configured"),
            ("result", "*", "valid"),
        ),
    },
    {
        "name": "osril.resume-ready",
        "argv": ["osril", "resume-ready", "--dry-run", "--json"],
        "expected_action": "osril.resume-ready",
        "required_result_paths": (
            ("result", "dry_run"),
            ("result", "ready_count"),
            ("result", "wait_resume_state"),
        ),
    },
    {
        "name": "sbp.delivery-health",
        "argv": ["sbp", "delivery-health", "--json"],
        "expected_action": "sbp.delivery-health",
        "required_result_paths": (
            ("result", "summary"),
            ("result", "summary", "event_count"),
            ("result", "events"),
        ),
    },
    {
        "name": "watch.list",
        "argv": ["watch", "list", "--json"],
        "expected_action": "watch.list",
        "required_result_paths": (
            ("result", "folders"),
            ("result", "count"),
        ),
    },
    {
        "name": "creator.ingest.dry-run",
        "argv": [
            "creator",
            "ingest",
            "--transcript",
            CREATOR_ENGINE_SMOKE_FIXTURE_TRANSCRIPT.as_posix(),
            "--vault-root",
            str(CREATOR_ENGINE_SMOKE_FIXTURE_VAULT),
            "--source-title",
            "Creator Engine fixture walkthrough",
            "--source-origin",
            "repo fixture",
            "--source-kind",
            "provided-transcript-fixture",
            "--dry-run",
            "--json",
        ],
        "expected_action": "creator.ingest",
        "required_result_paths": (
            ("result", "status"),
            ("result", "dry_run"),
            ("result", "writes_performed"),
            ("result", "files_read"),
            ("result", "manual_source_metadata"),
            ("result", "preview", "content_sha256"),
            ("result", "preview", "word_count"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "creator.ingest.manual-media-dry-run",
        "argv": [
            "creator",
            "ingest",
            "--source",
            "manual-file",
            "--media",
            CREATOR_ENGINE_SMOKE_FIXTURE_MEDIA.as_posix(),
            "--vault-root",
            str(CREATOR_ENGINE_SMOKE_FIXTURE_VAULT),
            "--source-title",
            "Creator Engine fixture media reference",
            "--source-origin",
            "repo fixture",
            "--source-kind",
            "manual-media-fixture",
            "--dry-run",
            "--json",
        ],
        "expected_action": "creator.ingest",
        "required_result_paths": (
            ("result", "status"),
            ("result", "dry_run"),
            ("result", "writes_performed"),
            ("result", "files_read"),
            ("result", "manual_source_metadata"),
            ("result", "preview", "file_sha256"),
            ("result", "preview", "media_kind"),
            ("result", "preview", "probe_status"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "setup.status",
        "argv": ["setup", "status", "--json"],
        "expected_action": "setup.status",
        "setup_state_path": str(SETUP_STATE_SMOKE_FIXTURE),
        "required_result_paths": (
            ("result", "providers"),
            ("result", "integrations"),
        ),
    },
    {
        "name": "setup.provider.list",
        "argv": ["setup", "provider", "list", "--json"],
        "expected_action": "setup.provider.list",
        "required_result_paths": (
            ("result", "*", "id"),
            ("result", "*", "setup_kind"),
            ("result", "*", "status"),
        ),
    },
    {
        "name": "setup.integration.list",
        "argv": ["setup", "integration", "list", "--json"],
        "expected_action": "setup.integration.list",
        "required_result_paths": (
            ("result", "*", "id"),
            ("result", "*", "setup_kind"),
            ("result", "*", "status"),
        ),
    },
    {
        "name": "capture.status",
        "argv": ["capture", "status", "--vault-root", str(INTAKE_SMOKE_FIXTURE_VAULT), "--json"],
        "expected_action": "capture.status",
        "required_result_paths": (
            ("result", "status"),
            ("result", "read_only"),
            ("result", "mutates_capture"),
            ("result", "total_quarantine"),
            ("result", "dedup_registry", "entry_count"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "capture.validate",
        "argv": ["capture", "validate", "--vault-root", str(INTAKE_SMOKE_FIXTURE_VAULT), "--json"],
        "expected_action": "capture.validate",
        "required_result_paths": (
            ("result", "status"),
            ("result", "valid"),
            ("result", "read_only"),
            ("result", "safe_validate_only"),
            ("result", "dedup_registry", "entry_count"),
            ("result", "validated_modes"),
            ("result", "forbidden_actions"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "develop.explain.dry-run",
        "argv": [
            "develop",
            "explain",
            "--question",
            "ratchet smoke dry run",
            "--dry-run",
            "--json",
        ],
        "expected_action": "develop.explain",
        "required_result_paths": (
            ("result", "workflow_id"),
            ("result", "status"),
            ("result", "outputs", "dry_run"),
        ),
    },
    {
        "name": "intake.dedup-stats",
        "argv": ["intake", "dedup-stats", "--vault-root", str(INTAKE_SMOKE_FIXTURE_VAULT), "--json"],
        "expected_action": "intake.dedup-stats",
        "required_result_paths": (
            ("result", "registry_path"),
            ("result", "entry_count"),
            ("result", "registry_exists"),
        ),
    },
    {
        "name": "intake.ls",
        "argv": ["intake", "ls", "--vault-root", str(INTAKE_SMOKE_FIXTURE_VAULT), "--json"],
        "expected_action": "intake.ls",
        "required_result_paths": (
            ("result", "status"),
            ("result", "read_only"),
            ("result", "classes"),
            ("result", "total_quarantine"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "intake.inspect",
        "argv": ["intake", "inspect", str(INTAKE_SMOKE_FIXTURE_ITEM), "--json"],
        "expected_action": "intake.inspect",
        "required_result_paths": (
            ("result", "schema_version"),
            ("result", "capture_id"),
            ("result", "content_filename"),
            ("result", "input_class"),
            ("result", "quarantine_status"),
            ("result", "promotion_status"),
            ("result", "extra_metadata", "writes_performed"),
        ),
    },
    {
        "name": "agent-bus.status",
        "argv": ["agent-bus", "status", "--json"],
        "expected_action": "agent-bus.status",
        "required_result_paths": (
            ("result", "task_count"),
            ("result", "open_count"),
            ("result", "done_count"),
        ),
    },
    {
        "name": "events.validate",
        "argv": ["events", "validate", "--json"],
        "expected_action": "events.validate",
        "required_result_paths": (
            ("result", "valid"),
            ("result", "error_count"),
            ("result", "errors"),
        ),
    },
    {
        "name": "events.rules",
        "argv": ["events", "rules", "--json"],
        "expected_action": "events.rules",
        "required_result_paths": (
            ("result", "count"),
            ("result", "rules"),
        ),
    },
    {
        "name": "context.boot",
        "argv": ["context", "boot", "--json"],
        "expected_action": "context.boot",
        "required_result_paths": (
            ("result", "runtime_id"),
            ("result", "boot_status"),
            ("result", "sources_read"),
        ),
    },
    {
        "name": "operate.browser.policy",
        "argv": ["operate", "browser", "policy", "--json"],
        "expected_action": "operate.browser.policy",
        "required_result_paths": (
            ("result", "read_only"),
            ("result", "mutates_browser"),
            ("result", "governance"),
        ),
    },
    {
        "name": "scorecard.list",
        "argv": ["scorecard", "list", "--json"],
        "expected_action": "scorecard.list",
        "required_result_paths": (
            ("result", "runtime_ids"),
            ("result", "count"),
        ),
    },
    {
        "name": "scaffold.project",
        "argv": ["scaffold", "project", "example", "--json"],
        "expected_action": "scaffold.project",
        "required_result_paths": (
            ("result", "scaffold_type"),
            ("result", "write"),
            ("result", "draft_only"),
        ),
    },
    {
        "name": "run.operator_today.dry-run",
        "argv": ["run", "operator_today", "--dry-run", "--json"],
        "expected_action": "run",
        "required_result_paths": (
            ("result", "workflow_id"),
            ("result", "status"),
            ("result", "dry_run"),
            ("result", "stage_reached"),
            ("result", "outputs", "dry_run"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "core-export.readiness",
        "argv": ["core-export", "readiness", "--json"],
        "expected_action": "core-export.readiness",
        "expected_exit_code": 1,
        "expected_ok": False,
        "required_result_paths": (
            ("result", "readiness_status"),
            ("result", "blocking_issues"),
            ("result", "writes_performed"),
            ("result", "real_export_allowed_without_gate"),
        ),
    },
    {
        "name": "health.openclaw.gateway",
        "argv": ["health", "openclaw", "--timeout", "1", "--json"],
        "expected_action": "health",
        "optional_live_readiness": True,
        "allowed_statuses": {
            "healthy": {"exit_code": 0, "ok": True},
            "unavailable": {"exit_code": 1, "ok": False},
        },
        "required_result_paths": (
            ("result", "runtime_id"),
            ("result", "status"),
            ("result", "gateway_detected"),
            ("result", "candidate_urls"),
            ("result", "candidate_ports"),
            ("result", "probes"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "health.hermes.gateway",
        "argv": ["health", "hermes", "--timeout", "1", "--json"],
        "expected_action": "health",
        "optional_live_readiness": True,
        "allowed_statuses": {
            "healthy": {"exit_code": 0, "ok": True},
            "unavailable": {"exit_code": 1, "ok": False},
        },
        "required_result_paths": (
            ("result", "runtime_id"),
            ("result", "status"),
            ("result", "gateway_detected"),
            ("result", "candidate_urls"),
            ("result", "candidate_ports"),
            ("result", "probes"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "health.codex.session-heartbeat",
        "argv": ["health", "codex", "--json"],
        "expected_action": "health",
        "optional_readiness": True,
        "allowed_statuses": {
            "healthy": {"exit_code": 0, "ok": True},
            "unavailable": {"exit_code": 1, "ok": False},
        },
        "required_result_paths": (
            ("result", "runtime_id"),
            ("result", "kind"),
            ("result", "status"),
            ("result", "heartbeat_runtime"),
            ("result", "heartbeat_present"),
            ("result", "heartbeat_fresh"),
            ("result", "heartbeat_stale_after_seconds"),
            ("result", "probes"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "health.archon.session-heartbeat",
        "argv": ["health", "archon", "--json"],
        "expected_action": "health",
        "optional_readiness": True,
        "allowed_statuses": {
            "healthy": {"exit_code": 0, "ok": True},
            "unavailable": {"exit_code": 1, "ok": False},
        },
        "required_result_paths": (
            ("result", "runtime_id"),
            ("result", "kind"),
            ("result", "status"),
            ("result", "heartbeat_runtime"),
            ("result", "heartbeat_present"),
            ("result", "heartbeat_fresh"),
            ("result", "heartbeat_stale_after_seconds"),
            ("result", "probes"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "n8n.readiness",
        "argv": ["n8n", "readiness", "--json"],
        "expected_action": "n8n.readiness",
        "optional_readiness": True,
        "allowed_statuses": {
            "ready": {"exit_code": 0, "ok": True},
            "blocked": {"exit_code": 1, "ok": False},
        },
        "required_result_paths": (
            ("result", "status"),
            ("result", "readiness_status"),
            ("result", "blocked_reasons"),
            ("result", "live_http_call"),
            ("result", "connection", "blocked_reasons"),
            ("result", "registry", "ok"),
            ("result", "forbidden"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "n8n.dry-run",
        "argv": [
            "n8n",
            "dry-run",
            "send_discord_draft_alert",
            "--caller",
            "chaseos_runtime_mcp",
            "--payload",
            "{}",
            "--json",
        ],
        "expected_action": "n8n.dry-run",
        "required_result_paths": (
            ("result", "status"),
            ("result", "readiness_status"),
            ("result", "workflow_id"),
            ("result", "dry_run"),
            ("result", "live_http_call"),
            ("result", "writes_performed"),
            ("result", "draft", "policy", "current_status"),
            ("result", "forbidden_actions"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "maintain.status",
        "argv": ["maintain", "--status", "--json"],
        "expected_action": "maintain",
        "required_result_paths": (
            ("result", "status"),
            ("result", "read_only"),
            ("result", "mutates_vault"),
            ("result", "full_scan_deferred_from_ratchet"),
            ("result", "stages"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
        ),
    },
    {
        "name": "maintain.fixture-dry-run",
        "argv": [
            "maintain",
            "--dry-run",
            "--fixture-root",
            str(MAINTAIN_SMOKE_FIXTURE_VAULT),
            "--json",
        ],
        "expected_action": "maintain",
        "required_result_paths": (
            ("result", "status"),
            ("result", "dry_run"),
            ("result", "read_only"),
            ("result", "bounded_fixture_mode"),
            ("result", "bounded_fixture_root"),
            ("result", "writes_performed"),
            ("result", "authority_flags"),
            ("result", "stage_1_vault_hygiene", "files_scanned"),
            ("result", "stage_2_daily_hub", "files_scanned"),
            ("result", "stage_3_provenance", "files_scanned"),
        ),
    },
    {
        "name": "studio.runtime-cockpit-action-readiness",
        "argv": ["studio", "runtime-cockpit-action-readiness", "--json"],
        "expected_action": "studio.runtime-cockpit-action-readiness",
        "expectations": ("status", "blocked_reason", "writes", "evidence", "authority_flags"),
    },
    {
        "name": "pulse.final-evidence-gate",
        "argv": ["pulse", "final-evidence-gate", "--json"],
        "expected_action": "pulse.final-evidence-gate",
        "expectations": ("status", "blocked_reason", "writes", "evidence", "authority_flags"),
    },
    {
        "name": "runtime.provider.completion-status",
        "argv": ["runtime", "provider", "completion-status", "--json"],
        "expected_action": "runtime.provider.completion-status",
        "expectations": ("status", "blocked_reason", "writes", "evidence", "authority_flags"),
    },
    {
        "name": "siteops.validate",
        "argv": ["siteops", "validate", "--json"],
        "expected_action": "siteops.validate",
        "expectations": ("status",),
    },
    {
        "name": "subagents.validate",
        "argv": ["subagents", "validate", "--json"],
        "expected_action": "subagents.validate",
        "expectations": ("status", "writes", "authority_flags"),
    },
    {
        "name": "subagents.approval-preview",
        "argv": [
            "subagents",
            "approval-preview",
            "site-ops-worker",
            "--mode",
            "site_ops",
            "--json",
        ],
        "expected_action": "subagents.approval-preview",
        "required_result_paths": (
            ("result", "status"),
            ("result", "work_fingerprint"),
            ("result", "approval_packet_preview"),
            ("result", "approval_packet_preview", "approval_artifact_written"),
            ("result", "authority_flags"),
            ("result", "blocked_effects"),
        ),
    },
    {
        "name": "subagents.write-approval-request",
        "argv": [
            "subagents",
            "write-approval-request",
            "site-ops-worker",
            "--mode",
            "site_ops",
            "--json",
        ],
        "expected_action": "subagents.write-approval-request",
        "required_result_paths": (
            ("result", "status"),
            ("result", "work_fingerprint"),
            ("result", "approval_artifact_preview"),
            ("result", "approval_request_written"),
            ("result", "authority_flags"),
            ("result", "blocked_effects"),
        ),
    },
    {
        "name": "siteops.candidates.preflight",
        "argv": [
            "siteops",
            "candidates",
            "preflight",
            "candidate_run_123",
            "--vault-root",
            str(SITEOPS_CANDIDATE_SMOKE_VAULT),
            "--json",
        ],
        "expected_action": "siteops.candidates.preflight",
        "expectations": ("status", "blocked_reason", "writes", "evidence", "authority_flags"),
    },
    {
        "name": "acquisition.research-status",
        "argv": ["acquisition", "research-status", "--json"],
        "expected_action": "acquisition.research-status",
        "expectations": ("status", "blocked_reason", "writes", "evidence", "authority_flags"),
    },
)


DEFERRED_SMOKE_COMMANDS: tuple[dict[str, Any], ...] = (
    {
        "name": "n8n.execute",
        "argv": ["n8n", "execute"],
        "status": "permanent_deferred_live_execution",
        "reason": "live n8n execution is intentionally excluded from routine CLI preflight; dry-run/readiness smokes cover the safe policy path",
        "closure_status": "closed_by_n8n_readiness_and_dry_run_smokes",
        "blocker_type": "execution_adjacent",
        "representative_smoke": "n8n.dry-run",
        "fixture_readiness": "n8n readiness validates config/registry without HTTP; n8n dry-run validates a call draft without live execution or writes",
        "forbidden_during_ratchet": (
            "workflow_execution",
            "live_http_call",
            "connector_call",
            "external_side_effect",
        ),
        "promotion_condition": "do not promote live execute into routine smoke; live execution requires explicit operator approval and a separate governed runner proof",
    },
    {
        "name": "capture.family",
        "argv": ["capture", "..."],
        "status": "permanent_deferred_mutating_or_external",
        "reason": "mutating capture commands write quarantine artifacts or can call external connectors; validate/status smokes cover the no-write posture",
        "closure_status": "closed_by_capture_status_and_validate_smokes",
        "blocker_type": "mutating_or_external",
        "representative_smoke": "capture.validate",
        "fixture_readiness": "packaged intake fixture vault covers capture status and validate-only posture without quarantine writes, connector calls, or external fetches",
        "forbidden_during_ratchet": (
            "quarantine_write",
            "connector_call",
            "external_fetch",
            "dedup_registry_write",
        ),
        "promotion_condition": "do not promote mutating/external capture commands into routine smoke; add separate no-write validate surfaces for any future capture mode",
    },
)


DEFERRED_CLOSURE_REQUIRED_FIELDS = (
    "name",
    "argv",
    "status",
    "reason",
    "closure_status",
    "blocker_type",
    "representative_smoke",
    "fixture_readiness",
    "forbidden_during_ratchet",
    "promotion_condition",
)


def _format_command(path: tuple[str, ...] | list[str]) -> str:
    return "chaseos " + " ".join(path)


def _format_path(path: tuple[str, ...]) -> str:
    return ".".join(path)


def _format_json_path(path: tuple[str, ...]) -> str:
    return ".".join(path)


def _smoke_family(spec: dict[str, Any]) -> str:
    expected_action = spec.get("expected_action")
    if expected_action:
        return str(expected_action).split(".", 1)[0]
    argv = spec.get("argv") or []
    return str(argv[0]) if argv else "unknown"


def _deferred_family(spec: dict[str, Any]) -> str:
    argv = spec.get("argv") or []
    return str(argv[0]) if argv else str(spec.get("name", "unknown")).split(".", 1)[0]


def family_ratchet_dispositions(contract: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    contract = contract or load_contract(CONTRACT_PATH)
    smoke_by_family: dict[str, list[str]] = {}
    deferred_by_family: dict[str, list[dict[str, Any]]] = {}
    command_counts: dict[str, int] = {}

    for command in contract.get("commands", []):
        family = str(command["family"])
        command_counts[family] = command_counts.get(family, 0) + 1

    for spec in SMOKE_COMMANDS:
        smoke_by_family.setdefault(_smoke_family(spec), []).append(spec["name"])
    for spec in DEFERRED_SMOKE_COMMANDS:
        deferred_by_family.setdefault(_deferred_family(spec), []).append(spec)

    rows: list[dict[str, Any]] = []
    for family in sorted(contract.get("families", {})):
        smoke_names = sorted(smoke_by_family.get(family, []))
        deferred_specs = sorted(deferred_by_family.get(family, []), key=lambda item: item["name"])
        if smoke_names:
            status = "smoke_covered"
        elif deferred_specs:
            status = "deferred"
        else:
            status = "contract_docs_only"
        rows.append(
            {
                "family": family,
                "status": status,
                "command_count": command_counts.get(family, 0),
                "smoke_commands": smoke_names,
                "deferred_commands": [
                    {
                        "name": spec["name"],
                        "status": spec["status"],
                        "closure_status": spec["closure_status"],
                        "blocker_type": spec["blocker_type"],
                        "representative_smoke": spec["representative_smoke"],
                        "promotion_condition": spec["promotion_condition"],
                    }
                    for spec in deferred_specs
                ],
            }
        )
    return rows


def deferred_smoke_closure_map() -> list[dict[str, Any]]:
    smoke_names = {str(spec["name"]) for spec in SMOKE_COMMANDS}
    rows: list[dict[str, Any]] = []
    for spec in DEFERRED_SMOKE_COMMANDS:
        representative_smoke = str(spec["representative_smoke"])
        rows.append(
            {
                "name": spec["name"],
                "command": _format_command(spec["argv"]),
                "status": spec["status"],
                "closure_status": spec["closure_status"],
                "blocker_type": spec["blocker_type"],
                "reason": spec["reason"],
                "representative_smoke": representative_smoke,
                "representative_smoke_present": representative_smoke in smoke_names,
                "fixture_readiness": spec["fixture_readiness"],
                "forbidden_during_ratchet": list(spec["forbidden_during_ratchet"]),
                "promotion_condition": spec["promotion_condition"],
            }
        )
    return rows


def deferred_smoke_closure_failures() -> list[str]:
    failures: list[str] = []
    smoke_names = {str(spec["name"]) for spec in SMOKE_COMMANDS}
    seen: set[str] = set()
    for spec in DEFERRED_SMOKE_COMMANDS:
        name = str(spec.get("name", "<missing-name>"))
        if name in seen:
            failures.append(f"deferred smoke map duplicate entry: {name}")
        seen.add(name)
        for field in DEFERRED_CLOSURE_REQUIRED_FIELDS:
            value = spec.get(field)
            if value in (None, "", (), []):
                failures.append(f"{name} deferred closure map missing field {field}")
        representative_smoke = str(spec.get("representative_smoke", ""))
        if representative_smoke and representative_smoke not in smoke_names:
            failures.append(
                f"{name} representative smoke {representative_smoke} is not present in SMOKE_COMMANDS"
            )
        closure_status = str(spec.get("closure_status", ""))
        if closure_status and not closure_status.startswith("closed_"):
            failures.append(f"{name} deferred closure status must start with closed_: {closure_status}")
        forbidden = spec.get("forbidden_during_ratchet")
        if not isinstance(forbidden, tuple) or not all(isinstance(item, str) and item for item in forbidden):
            failures.append(f"{name} forbidden_during_ratchet must be a non-empty tuple of strings")
    return failures


def _smoke_expectation_profile(spec: dict[str, Any]) -> str:
    if spec.get("optional_live_readiness"):
        return "optional_live_readiness_result_paths"
    if spec.get("optional_readiness"):
        return "optional_readiness_result_paths"
    if spec.get("expected_exit_code", 0) != 0 or spec.get("expected_ok") is False:
        return "read_only_expected_nonzero_result_paths"
    if spec.get("expectations"):
        return "standard_json_expectations"
    if spec.get("required_result_paths"):
        return "read_only_result_paths"
    return "json_envelope_only"


def _subparser_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction | None:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    return None


def _parser_surface_paths(
    cli_module: Any,
    parser: argparse.ArgumentParser | None = None,
    path: tuple[str, ...] = (),
) -> set[tuple[str, ...]]:
    parser = parser or cli_module.build_parser()
    subparser = _subparser_action(parser)
    if subparser is not None:
        paths: set[tuple[str, ...]] = set()
        seen: set[int] = set()
        for name, child in subparser.choices.items():
            if id(child) in seen:
                continue
            seen.add(id(child))
            paths.update(_parser_surface_paths(cli_module, child, path + (name,)))
        return paths

    for action in parser._actions:
        if (
            not action.option_strings
            and action.dest in COMMAND_CHOICE_DESTS
            and getattr(action, "choices", None)
        ):
            return {path + (str(choice),) for choice in action.choices}
    return {path}


def _resolve_parser(
    cli_module: Any,
    path: list[str],
    parser: argparse.ArgumentParser | None = None,
) -> tuple[argparse.ArgumentParser, list[str]]:
    parser = parser or cli_module.build_parser()
    remaining = list(path)
    while remaining:
        subparser = _subparser_action(parser)
        if subparser is None or remaining[0] not in subparser.choices:
            break
        parser = subparser.choices[remaining.pop(0)]
    return parser, remaining


def _expand_args(contract: dict[str, Any], args: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for arg in args:
        include = arg.get("include")
        if include:
            expanded.extend(_expand_args(contract, contract["arg_sets"][include]))
        else:
            expanded.append(arg)
    return expanded


def _contract_paths(contract: dict[str, Any]) -> set[tuple[str, ...]]:
    return {tuple(command["path"]) for command in contract["commands"]}


def _actions_by_dest(
    parser: argparse.ArgumentParser,
    remaining_path: list[str],
) -> tuple[dict[str, argparse.Action], dict[str, argparse.Action]]:
    consumed_choice_dests: set[str] = set()
    for token in remaining_path:
        for action in parser._actions:
            if (
                not action.option_strings
                and getattr(action, "choices", None)
                and token in action.choices
            ):
                consumed_choice_dests.add(action.dest)
                break
        else:
            raise ValueError(f"could not resolve command path token {token!r}")

    option_actions: dict[str, argparse.Action] = {}
    positional_actions: dict[str, argparse.Action] = {}
    for action in parser._actions:
        if action.dest == "help" or isinstance(action, argparse._SubParsersAction):
            continue
        if action.option_strings:
            option_actions[action.dest] = action
        elif action.dest not in consumed_choice_dests:
            positional_actions[action.dest] = action
    return option_actions, positional_actions


def _example_value(arg: dict[str, Any]) -> str:
    choices = arg.get("choices")
    if choices:
        return str(choices[0])
    dest = str(arg.get("dest", "")).lower()
    if dest.endswith("_seconds") or dest in {"seconds", "interval", "limit", "max_cycles"}:
        return "1"
    return {
        "PATH": "example.md",
        "URL": "https://example.com",
        "RUNTIME": "Hermes",
        "RUNTIME_ID": "openclaw",
        "SCHEDULE_ID": "sch-example",
        "WORKFLOW_ID": "operator_today",
        "ADAPTER_ID": "openclaw",
        "TASK_ID": "task-example",
        "KEY=VALUE": "configured=true",
        "KEY": "operator.theme",
        "VALUE": "quiet",
        "NAME": "Example",
        "N": "1",
        "SECONDS": "1",
        "YYYY-MM-DD": "2026-04-27",
    }.get(str(arg.get("value", "")).upper(), "example")


def _parse_example(contract: dict[str, Any], command: dict[str, Any]) -> list[str]:
    argv = list(command["path"])
    provided = set(command.get("parse_args", []))
    expanded_args = _expand_args(contract, command.get("args", []))

    for arg in expanded_args:
        if arg.get("kind") == "positional" and arg.get("required", False):
            argv.append(_example_value(arg))

    for arg in expanded_args:
        flags = arg.get("flags")
        if not flags or not arg.get("required", False):
            continue
        if any(flag in provided for flag in flags):
            continue
        if arg.get("kind") == "flag":
            argv.append(flags[0])
            continue
        argv.extend([flags[0], _example_value(arg)])

    parse_args = command.get("parse_args", [])
    if parse_args:
        argv.extend(parse_args)
    else:
        argv.extend(DEFAULT_PARSE_ARGS_BY_PATH.get(tuple(command["path"]), []))
    return argv


def _append_path_sync_failures(contract: dict[str, Any], cli_module: Any, failures: list[str]) -> None:
    parser_paths = _parser_surface_paths(cli_module)
    contract_paths = _contract_paths(contract)

    for missing in sorted(parser_paths - contract_paths):
        failures.append(f"command contract missing parser command: {_format_command(missing)}")
    for stale in sorted(contract_paths - parser_paths):
        failures.append(f"command contract has stale command path: {_format_command(stale)}")


def _append_uniqueness_failures(contract: dict[str, Any], failures: list[str]) -> None:
    seen: set[tuple[str, ...]] = set()
    for command in contract["commands"]:
        path = tuple(command["path"])
        if path in seen:
            failures.append(f"command contract duplicates command path: {_format_command(path)}")
        seen.add(path)


def _append_metadata_failures(contract: dict[str, Any], failures: list[str]) -> None:
    if contract.get("schema_version") != 1:
        failures.append("command contract schema_version must be 1")
    envelope_keys = contract.get("json_contract", {}).get("envelope_keys")
    if envelope_keys != list(JSON_CONTRACT_KEYS):
        failures.append(
            f"command contract JSON envelope keys are stale: {envelope_keys!r} != {list(JSON_CONTRACT_KEYS)!r}"
        )
    if not contract.get("entrypoints"):
        failures.append("command contract entrypoints list is empty")

    families = contract.get("families", {})
    shapes = contract.get("json_shapes", {})
    for command in contract.get("commands", []):
        command_label = _format_command(command["path"])
        if command.get("family") not in families:
            failures.append(f"{command_label} references unknown family {command.get('family')!r}")
        if not command.get("maturity"):
            failures.append(f"{command_label} is missing maturity")
        if not command.get("handler"):
            failures.append(f"{command_label} is missing handler")
        if command.get("json_shape") not in shapes:
            failures.append(f"{command_label} references unknown json_shape {command.get('json_shape')!r}")
        if not isinstance(command.get("side_effects"), list) or not command.get("side_effects"):
            failures.append(f"{command_label} must declare side_effects")


def _append_arg_sync_failures(contract: dict[str, Any], cli_module: Any, failures: list[str]) -> None:
    root_parser = cli_module.build_parser()
    for command in contract["commands"]:
        command_label = _format_command(command["path"])
        try:
            parser, remaining = _resolve_parser(cli_module, command["path"], parser=root_parser)
            actual_options, actual_positionals = _actions_by_dest(parser, remaining)
        except Exception as exc:
            failures.append(f"{command_label} could not be resolved in argparse: {exc}")
            continue

        expected_args = _expand_args(contract, command.get("args", []))
        expected_options = {arg["dest"]: arg for arg in expected_args if arg.get("flags")}
        expected_positionals = {
            arg["dest"]: arg
            for arg in expected_args
            if arg.get("kind") == "positional"
        }

        for dest in sorted(set(actual_options) - set(expected_options)):
            action = actual_options[dest]
            failures.append(
                f"command contract missing flag for {command_label}: dest={dest!r} flags={list(action.option_strings)!r}"
            )
        for dest in sorted(set(expected_options) - set(actual_options)):
            expected = expected_options[dest]
            failures.append(
                f"command contract has stale flag for {command_label}: dest={dest!r} flags={expected.get('flags')!r}"
            )
        for dest in sorted(set(actual_positionals) - set(expected_positionals)):
            failures.append(f"command contract missing positional for {command_label}: dest={dest!r}")
        for dest in sorted(set(expected_positionals) - set(actual_positionals)):
            failures.append(f"command contract has stale positional for {command_label}: dest={dest!r}")

        for dest in sorted(set(actual_options) & set(expected_options)):
            actual = actual_options[dest]
            expected = expected_options[dest]
            if set(actual.option_strings) != set(expected["flags"]):
                failures.append(
                    f"stale flag declaration for {command_label}: dest={dest!r} "
                    f"contract={expected['flags']!r} parser={list(actual.option_strings)!r}"
                )
            if "required" in expected and actual.required is not expected["required"]:
                failures.append(
                    f"stale required flag metadata for {command_label}: dest={dest!r} "
                    f"contract={expected['required']!r} parser={actual.required!r}"
                )
            actual_choices = getattr(actual, "choices", None)
            if actual_choices is not None:
                if "choices" not in expected:
                    failures.append(f"contract missing choices for {command_label}: dest={dest!r}")
                elif list(actual_choices) != expected["choices"]:
                    failures.append(
                        f"stale choices for {command_label}: dest={dest!r} "
                        f"contract={expected['choices']!r} parser={list(actual_choices)!r}"
                    )
            elif "choices" in expected:
                failures.append(f"contract has stale choices for {command_label}: dest={dest!r}")

        for dest in sorted(set(actual_positionals) & set(expected_positionals)):
            actual = actual_positionals[dest]
            expected = expected_positionals[dest]
            actual_choices = getattr(actual, "choices", None)
            if actual_choices is not None:
                if "choices" not in expected:
                    failures.append(f"contract missing positional choices for {command_label}: dest={dest!r}")
                elif list(actual_choices) != expected["choices"]:
                    failures.append(
                        f"stale positional choices for {command_label}: dest={dest!r} "
                        f"contract={expected['choices']!r} parser={list(actual_choices)!r}"
                    )
            elif "choices" in expected:
                failures.append(f"contract has stale positional choices for {command_label}: dest={dest!r}")
            if "nargs" in expected and actual.nargs != expected["nargs"]:
                failures.append(
                    f"stale positional nargs for {command_label}: dest={dest!r} "
                    f"contract={expected['nargs']!r} parser={actual.nargs!r}"
                )


def _append_parse_failures(contract: dict[str, Any], cli_module: Any, failures: list[str]) -> None:
    parser = cli_module.build_parser()
    for command in contract["commands"]:
        command_label = _format_command(command["path"])
        argv = _parse_example(contract, command)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                parsed = parser.parse_args(argv)
        except SystemExit as exc:
            failures.append(f"{command_label} parse example failed with SystemExit({exc.code}): {argv!r}")
            continue
        if parsed.func.__name__ != command["handler"]:
            failures.append(
                f"{command_label} resolves to handler {parsed.func.__name__!r}, "
                f"contract declares {command['handler']!r}"
            )


def _append_json_shape_failures(contract: dict[str, Any], failures: list[str]) -> None:
    for command in contract["commands"]:
        command_label = _format_command(command["path"])
        args = _expand_args(contract, command.get("args", []))
        has_json_flag = any("--json" in arg.get("flags", []) for arg in args)
        shape = contract["json_shapes"][command["json_shape"]]
        supported = shape.get("supported", shape.get("supports_json_flag"))
        if supported is not has_json_flag:
            failures.append(
                f"JSON shape support drift for {command_label}: json_shape={command['json_shape']!r} "
                f"supported={supported!r} --json flag present={has_json_flag!r}"
            )


def _append_action_failures(contract: dict[str, Any], cli_module: Any, failures: list[str]) -> None:
    parser = cli_module.build_parser()
    for command in contract["commands"]:
        args = _expand_args(contract, command.get("args", []))
        if not any("--json" in arg.get("flags", []) for arg in args):
            continue

        command_label = _format_command(command["path"])
        argv = _parse_example(contract, command)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                parsed = parser.parse_args(argv)
        except SystemExit as exc:
            failures.append(f"{command_label} action example failed with SystemExit({exc.code}): {argv!r}")
            continue

        expected = ".".join(command["path"])
        actual = build_action(parsed)
        if actual != expected:
            failures.append(
                f"JSON action drift for {command_label}: expected action {expected!r}, got {actual!r}"
            )


def _append_docs_failures(contract: dict[str, Any], failures: list[str]) -> None:
    rendered = render_markdown(contract)
    existing = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
    if existing != rendered:
        failures.append(
            f"generated command docs are stale: {DOC_PATH}; run python -m runtime.cli.generate_docs --write"
        )
    from runtime.cli.generate_docs import (
        HANDBOOK_PATH,
        operator_handbook_coverage_failures,
        render_operator_handbook,
    )

    handbook = render_operator_handbook(contract)
    existing_handbook = HANDBOOK_PATH.read_text(encoding="utf-8") if HANDBOOK_PATH.exists() else ""
    if existing_handbook != handbook:
        failures.append(
            f"generated operator handbook is stale: {HANDBOOK_PATH}; run python -m runtime.cli.generate_docs --write"
        )
    failures.extend(operator_handbook_coverage_failures(contract, existing_handbook or handbook))


def _path_present(value: Any, path: tuple[str, ...]) -> bool:
    current = value
    for part in path:
        if part == "*":
            if not isinstance(current, list) or not current:
                return False
            rest = path[path.index(part) + 1 :]
            return any(_path_present(item, rest) for item in current)
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


@contextlib.contextmanager
def _setup_state_fixture_context(spec: dict[str, Any]):
    setup_state_path = spec.get("setup_state_path")
    if not setup_state_path:
        yield
        return

    import runtime.setup_state as setup_state

    original_setup_state_path = setup_state.SETUP_STATE_PATH
    setup_state.SETUP_STATE_PATH = Path(setup_state_path)
    try:
        yield
    finally:
        setup_state.SETUP_STATE_PATH = original_setup_state_path


def _run_cli_json_smoke(cli_module: Any, spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    stdout = io.StringIO()
    stderr = io.StringIO()
    argv = list(spec["argv"])
    command_label = _format_command(argv)
    expected_exit_code = spec.get("expected_exit_code", 0)
    expected_ok = spec.get("expected_ok", expected_exit_code == 0)

    setup_state_path = spec.get("setup_state_path")
    if setup_state_path and not Path(setup_state_path).exists():
        failures.append(f"{command_label} setup state fixture is missing: {setup_state_path}")
        return (
            {
                "name": spec["name"],
                "command": command_label,
                "expectation_profile": _smoke_expectation_profile(spec),
                "exit_code": None,
                "ok": False,
                "expected_exit_code": expected_exit_code,
                "expected_ok": expected_ok,
                "action": None,
                "expected_action": spec["expected_action"],
                "status_snapshot": {},
                "expectations": {},
                "required_result_paths": {},
                "stderr": "",
            },
            failures,
        )

    with (
        _setup_state_fixture_context(spec),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        exit_code = cli_module.main(argv)

    raw_stdout = stdout.getvalue()
    try:
        payload = json.loads(raw_stdout)
    except json.JSONDecodeError as exc:
        failures.append(f"{command_label} did not emit parseable JSON: {exc}")
        return (
            {
                "name": spec["name"],
                "command": command_label,
                "exit_code": exit_code,
                "ok": False,
                "action": None,
                "stderr": stderr.getvalue(),
            },
            failures,
        )

    if tuple(payload.keys()) != JSON_CONTRACT_KEYS:
        failures.append(
            f"{command_label} JSON envelope keys are stale: {tuple(payload.keys())!r} != {JSON_CONTRACT_KEYS!r}"
        )
    allowed_statuses = spec.get("allowed_statuses") or {}
    observed_status = None
    if spec.get("optional_live_readiness") or spec.get("optional_readiness"):
        result_payload = payload.get("result")
        if isinstance(result_payload, dict):
            observed_status = result_payload.get("status")
        status_expectation = allowed_statuses.get(observed_status)
        if not status_expectation:
            failures.append(
                f"{command_label} observed readiness status {observed_status!r}; "
                f"expected one of {sorted(allowed_statuses)}"
            )
        else:
            expected_exit_code = status_expectation["exit_code"]
            expected_ok = status_expectation["ok"]

    if exit_code != expected_exit_code:
        failures.append(f"{command_label} exited {exit_code}; expected {expected_exit_code}")
    if payload.get("ok") is not expected_ok:
        failures.append(f"{command_label} returned ok={payload.get('ok')!r}; expected {expected_ok}")
    if payload.get("action") != spec["expected_action"]:
        failures.append(
            f"{command_label} expected action {spec['expected_action']!r}, "
            f"got {payload.get('action')!r}"
        )

    expectation_results: dict[str, bool] = {}
    for group in spec.get("expectations", ()):
        paths = STANDARD_JSON_EXPECTATIONS[group]
        present = any(_path_present(payload, path) for path in paths)
        expectation_results[group] = present
        if not present:
            failures.append(
                f"{command_label} is missing standard JSON expectation {group!r}; "
                f"checked: {', '.join(_format_json_path(path) for path in paths)}"
            )

    required_result_path_results: dict[str, bool] = {}
    for path in spec.get("required_result_paths", ()):
        present = _path_present(payload, path)
        formatted_path = _format_json_path(path)
        required_result_path_results[formatted_path] = present
        if not present:
            failures.append(f"{command_label} missing required result path {formatted_path}")

    result = payload.get("result") if isinstance(payload, dict) else None
    status_snapshot = {}
    if isinstance(result, dict):
        for key in (
            "status",
            "ok",
            "gate_status",
            "readiness_status",
            "completion_status",
            "preflight_status",
            "readiness",
        ):
            if key in result:
                status_snapshot[key] = result[key]

    return (
        {
            "name": spec["name"],
            "command": command_label,
            "expectation_profile": _smoke_expectation_profile(spec),
            "exit_code": exit_code,
            "ok": payload.get("ok"),
            "expected_exit_code": expected_exit_code,
            "expected_ok": expected_ok,
            "allowed_statuses": allowed_statuses,
            "observed_status": observed_status,
            "action": payload.get("action"),
            "expected_action": spec["expected_action"],
            "setup_state_fixture": str(setup_state_path) if setup_state_path else None,
            "status_snapshot": status_snapshot,
            "expectations": expectation_results,
            "required_result_paths": required_result_path_results,
            "stderr": stderr.getvalue(),
        },
        failures,
    )


def _run_check(checks: list[dict[str, Any]], failures: list[str], name: str, check_fn: Any) -> None:
    before = len(failures)
    try:
        check_fn()
    except Exception as exc:
        failures.append(f"{name} raised {type(exc).__name__}: {exc}")
    new_failures = len(failures) - before
    checks.append(
        {
            "name": name,
            "status": "passed" if new_failures == 0 else "failed",
            "failure_count": new_failures,
        }
    )


def verify_cli_contract_ratchet(*, run_smokes: bool = True) -> dict[str, Any]:
    """Verify parser, command contract, generated docs, and read-only JSON smokes."""
    import runtime.cli.main as cli_module

    contract = load_contract(CONTRACT_PATH)
    failures: list[str] = []
    checks: list[dict[str, Any]] = []
    smoke_results: list[dict[str, Any]] = []

    _run_check(
        checks,
        failures,
        "parser_contract_path_sync",
        lambda: _append_path_sync_failures(contract, cli_module, failures),
    )
    _run_check(
        checks,
        failures,
        "contract_path_uniqueness",
        lambda: _append_uniqueness_failures(contract, failures),
    )
    _run_check(
        checks,
        failures,
        "contract_metadata",
        lambda: _append_metadata_failures(contract, failures),
    )
    _run_check(
        checks,
        failures,
        "argparse_contract_flag_sync",
        lambda: _append_arg_sync_failures(contract, cli_module, failures),
    )
    _run_check(
        checks,
        failures,
        "contract_examples_parse",
        lambda: _append_parse_failures(contract, cli_module, failures),
    )
    _run_check(
        checks,
        failures,
        "json_shape_flag_sync",
        lambda: _append_json_shape_failures(contract, failures),
    )
    _run_check(
        checks,
        failures,
        "json_action_contract_sync",
        lambda: _append_action_failures(contract, cli_module, failures),
    )
    _run_check(
        checks,
        failures,
        "generated_docs_sync",
        lambda: _append_docs_failures(contract, failures),
    )
    _run_check(
        checks,
        failures,
        "deferred_smoke_closure_map",
        lambda: failures.extend(deferred_smoke_closure_failures()),
    )

    if run_smokes:
        before = len(failures)
        for spec in SMOKE_COMMANDS:
            smoke_result, smoke_failures = _run_cli_json_smoke(cli_module, spec)
            smoke_results.append(smoke_result)
            failures.extend(smoke_failures)
        checks.append(
            {
                "name": "cross_family_json_smokes",
                "status": "passed" if len(failures) == before else "failed",
                "failure_count": len(failures) - before,
            }
        )
    else:
        checks.append(
            {
                "name": "cross_family_json_smokes",
                "status": "skipped",
                "failure_count": 0,
            }
        )

    family_count = len(contract.get("families", {}))
    command_count = len(contract.get("commands", []))
    ok = not failures
    return {
        "ok": ok,
        "status": "passed" if ok else "failed",
        "command_count": command_count,
        "family_count": family_count,
        "contract_path": str(Path(CONTRACT_PATH)),
        "docs_path": str(Path(DOC_PATH)),
        "checks": checks,
        "failures": failures,
        "smoke_results": smoke_results,
        "standard_json_expectations": {
            group: [_format_json_path(path) for path in paths]
            for group, paths in STANDARD_JSON_EXPECTATIONS.items()
        },
        "smoke_commands": [
            {
                "name": spec["name"],
                "command": _format_command(spec["argv"]),
                "expected_action": spec["expected_action"],
                "expected_exit_code": spec.get("expected_exit_code", 0),
                "expected_ok": spec.get(
                    "expected_ok",
                    spec.get("expected_exit_code", 0) == 0,
                ),
                "allowed_statuses": spec.get("allowed_statuses", {}),
                "expectation_profile": _smoke_expectation_profile(spec),
                "setup_state_fixture": str(spec.get("setup_state_path")) if spec.get("setup_state_path") else None,
                "expectations": list(spec.get("expectations", ())),
                "required_result_paths": [
                    _format_json_path(path)
                    for path in spec.get("required_result_paths", ())
                ],
            }
            for spec in SMOKE_COMMANDS
        ],
        "deferred_smoke_commands": [
            {
                "name": spec["name"],
                "command": _format_command(spec["argv"]),
                "status": spec["status"],
                "reason": spec["reason"],
                "closure_status": spec["closure_status"],
                "blocker_type": spec["blocker_type"],
                "representative_smoke": spec["representative_smoke"],
                "fixture_readiness": spec["fixture_readiness"],
                "forbidden_during_ratchet": list(spec["forbidden_during_ratchet"]),
                "promotion_condition": spec["promotion_condition"],
            }
            for spec in DEFERRED_SMOKE_COMMANDS
        ],
        "deferred_closure_map": deferred_smoke_closure_map(),
        "family_dispositions": family_ratchet_dispositions(contract),
    }
