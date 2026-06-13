"""Tests for the provider call-surface audit artifact."""

from __future__ import annotations

import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.providers.call_surface_audit import (  # noqa: E402
    load_provider_call_surface_audit,
    provider_state_ledger_surfaces,
    surfaces_by_policy,
)


EXPECTED_SURFACE_IDS = {
    "runtime.execution_adapter",
    "workflow.sbp_strikezone_digest",
    "workflow.hermes_review_synthesis",
    "source_intelligence.output_anthropic_generation",
    "source_intelligence.openai_embedding",
    "connector.perplexity_capture",
    "connector.grok_capture",
    "acquisition.live_sources_orchestrator",
    "acquisition.connector_health_ledger",
    "acquisition.google_docs_drive",
    "acquisition.email_imap",
    "acquisition.rss_fetch",
    "acquisition.web_scrape",
    "delivery.discord_webhook",
    "delivery.whop_api",
    "delivery.health_ledger",
    "runtime.lifecycle_http_health_probe",
    "setup.endpoint_probe",
    "adapter.openai_responses_mcp_dry_run",
    "adapter.n8n_call_draft",
    "workflow.openai_operator_research_shadow",
}


def test_provider_call_surface_audit_loads_expected_surfaces() -> None:
    audit = load_provider_call_surface_audit(_VAULT_ROOT)

    surfaces = audit["surfaces"]
    ids = {surface["id"] for surface in surfaces}

    assert EXPECTED_SURFACE_IDS.issubset(ids)
    assert len(ids) == len(surfaces)


def test_provider_call_surface_audit_classifies_ledger_vs_non_ledger_surfaces() -> None:
    audit = load_provider_call_surface_audit(_VAULT_ROOT)
    by_id = {surface["id"]: surface for surface in audit["surfaces"]}

    ledger_ids = {surface["id"] for surface in provider_state_ledger_surfaces(audit)}
    assert ledger_ids == {
        "runtime.execution_adapter",
        "workflow.sbp_strikezone_digest",
        "workflow.hermes_review_synthesis",
    }

    assert by_id["source_intelligence.output_anthropic_generation"]["provider_state_policy"] == "source_intelligence_telemetry"
    assert by_id["source_intelligence.openai_embedding"]["provider_state_policy"] == "source_intelligence_telemetry"
    assert by_id["connector.perplexity_capture"]["provider_state_policy"] == "connector_health_telemetry"
    assert by_id["connector.grok_capture"]["provider_state_policy"] == "connector_health_telemetry"
    assert by_id["delivery.discord_webhook"]["provider_state_policy"] == "delivery_health_telemetry"
    assert by_id["delivery.whop_api"]["provider_state_policy"] == "delivery_health_telemetry"
    assert by_id["delivery.health_ledger"]["provider_state_policy"] == "delivery_health_telemetry"
    assert by_id["workflow.openai_operator_research_shadow"]["provider_state_policy"] == "dry_run_control_plane_audit"

    connector_ids = {surface["id"] for surface in surfaces_by_policy(audit, "connector_health_telemetry")}
    assert "connector.perplexity_capture" in connector_ids
    assert "acquisition.web_scrape" in connector_ids


def test_provider_call_surface_evidence_markers_match_files() -> None:
    audit = load_provider_call_surface_audit(_VAULT_ROOT)

    for surface in audit["surfaces"]:
        text = (_VAULT_ROOT / surface["path"]).read_text(encoding="utf-8", errors="replace")
        for marker in surface["evidence_markers"]:
            assert marker in text, f"{surface['id']} missing marker {marker!r}"
