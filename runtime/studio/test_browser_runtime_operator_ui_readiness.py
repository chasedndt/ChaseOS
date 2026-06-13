"""Tests for Studio Browser Runtime operator UI readiness contract."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout

import runtime.studio.browser_runtime_operator_ui_readiness as readiness_module
from runtime.browser_runtime.completion_status import (
    BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED,
    BROWSER_RUNTIME_OVERALL_COMPLETE,
    BrowserRuntimeCompletionStatus,
)
from runtime.studio.browser_runtime_operator_ui_readiness import (
    MODEL_VERSION,
    SURFACE_ID,
    build_studio_browser_runtime_operator_ui_readiness,
    main as readiness_main,
)


def _status() -> BrowserRuntimeCompletionStatus:
    return BrowserRuntimeCompletionStatus(
        generated_at="2026-05-04T02:00:00Z",
        overall_status=BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED,
        bounded_mvp_done=True,
        production_feature_done=False,
        next_recommended_pass="excalidraw-local-browser-mcp-live-readiness-with-target",
        blocked_reasons=(
            "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target",
            "browser_use_cli_live_validation_blocked_unavailable",
            "excalidraw_live_browser_mcp_proof_not_run",
            "studio_operator_ui_not_built",
        ),
        items=(),
    )


def _production_complete_status() -> BrowserRuntimeCompletionStatus:
    return BrowserRuntimeCompletionStatus(
        generated_at="2026-05-05T20:00:00Z",
        overall_status=BROWSER_RUNTIME_OVERALL_COMPLETE,
        bounded_mvp_done=True,
        production_feature_done=True,
        next_recommended_pass="phase10-studio-product-hardening",
        blocked_reasons=(),
        items=(),
    )


def test_module_does_not_import_browser_or_writer_surfaces() -> None:
    source = inspect.getsource(readiness_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "playwright",
        "import browser_use",
        "from browser_use",
        "import mcp_excalidraw",
        "from mcp_excalidraw",
        "write_text(",
        "mkdir(",
        "open(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_readiness_contract_exposes_required_panels_without_ui_authority() -> None:
    model = build_studio_browser_runtime_operator_ui_readiness(
        ".",
        generated_at="2026-05-04T02:05:00Z",
        completion_status=_status(),
    )

    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["summary"]["bounded_mvp_done"] is True
    assert model["summary"]["production_feature_done"] is False
    assert model["summary"]["next_recommended_pass"] == (
        "excalidraw-local-browser-mcp-live-readiness-with-target"
    )
    assert model["summary"]["remaining_major_passes_min"] == 5
    assert model["summary"]["remaining_major_passes_max"] in {9, 10}
    assert model["panel_group"]["missing_panel_ids"] == []
    assert [panel["panel_id"] for panel in model["panels"]] == [
        "browser-runtime-completion-summary",
        "browser-runtime-remaining-passes",
        "browser-runtime-external-dependencies",
        "browser-runtime-excalidraw-chain",
        "browser-runtime-provider-validation",
        "browser-runtime-site-skill-memory",
        "browser-runtime-approval-queue",
        "browser-runtime-run-evidence",
    ]
    assert model["readiness"]["operator_ui_readiness_contract_ready"] is True
    assert model["readiness"]["studio_operator_ui_built"] is False
    assert model["readiness"]["interactive_approval_ui_built"] is False
    assert model["readiness"]["site_skill_inspector_built"] is False
    assert model["readiness"]["skill_promotion_ui_built"] is False
    assert model["readiness"]["live_browser_control_ui_built"] is False
    assert model["readiness"]["ui_blockers"] == ["studio_operator_ui_not_built"]


def test_readiness_contract_keeps_forbidden_effects_false() -> None:
    model = build_studio_browser_runtime_operator_ui_readiness(
        ".",
        generated_at="2026-05-04T02:10:00Z",
        completion_status=_status(),
    )
    authority = model["authority"]

    assert authority["read_only"] is True
    assert authority["local_only"] is True
    assert authority["starts_servers"] is False
    assert authority["opens_browser"] is False
    assert authority["launches_browser"] is False
    assert authority["connects_cdp"] is False
    assert authority["invokes_mcp"] is False
    assert authority["captures_screenshots"] is False
    assert authority["writes_browser_run_logs"] is False
    assert authority["writes_draft_skills"] is False
    assert authority["writes_trusted_skills"] is False
    assert authority["activates_skills"] is False
    assert authority["reads_real_profiles"] is False
    assert authority["reads_credentials_or_cookies"] is False
    assert authority["runs_browser_use_cli_live"] is False
    assert authority["writes_agent_bus_tasks"] is False
    assert authority["gate_mutation_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_current_evidence_is_path_existence_only() -> None:
    model = build_studio_browser_runtime_operator_ui_readiness(
        ".",
        generated_at="2026-05-04T02:15:00Z",
        completion_status=_status(),
    )

    for record in model["current_evidence"].values():
        assert sorted(record.keys()) == ["exists", "path"]
        assert isinstance(record["exists"], bool)


def test_production_complete_readiness_uses_completion_reporter_next_pass() -> None:
    model = build_studio_browser_runtime_operator_ui_readiness(
        ".",
        generated_at="2026-05-05T20:05:00Z",
        completion_status=_production_complete_status(),
    )

    assert model["summary"]["production_feature_done"] is True
    assert model["summary"]["remaining_major_passes_min"] == 0
    assert model["summary"]["remaining_major_passes_max"] == 0
    assert model["summary"]["next_recommended_pass"] == "phase10-studio-product-hardening"
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-product-hardening"


def test_cli_prints_json_without_writes() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = readiness_main(["--vault-root", ".", "--json"])
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["surface"] == SURFACE_ID
    assert payload["authority"]["read_only"] is True
    assert payload["authority"]["launches_browser"] is False
    assert payload["authority"]["connects_cdp"] is False
    assert payload["authority"]["invokes_mcp"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
