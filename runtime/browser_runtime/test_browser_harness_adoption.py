"""Tests for read-only Browser Harness adoption decision."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout

import runtime.browser_runtime.browser_harness_adoption as adoption_module
from runtime.browser_runtime.browser_harness_adoption import (
    BROWSER_HARNESS_ADOPTION_MODE,
    BROWSER_HARNESS_DECISION_STATUS,
    build_browser_harness_adoption_decision,
    main as adoption_main,
)


def test_adoption_module_does_not_import_or_call_live_surfaces() -> None:
    source = inspect.getsource(adoption_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "Popen",
        "write_text(",
        "mkdir(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_browser_harness_decision_is_reference_only() -> None:
    decision = build_browser_harness_adoption_decision(generated_at="2026-05-02T03:20:00Z")
    payload = decision.to_dict()

    assert payload["status"] == BROWSER_HARNESS_DECISION_STATUS
    assert payload["adoption_mode"] == BROWSER_HARNESS_ADOPTION_MODE
    assert payload["browser_harness_adopted"] is False
    assert payload["browser_harness_js_adopted"] is False
    assert payload["raw_cdp_surface_adopted"] is False
    assert payload["domain_skill_pattern_adopted"] is True
    assert payload["interaction_skill_taxonomy_adopted"] is True
    assert "domain skill memory as reviewed SiteOps/BOSL candidates" in payload["adopted_patterns"]
    assert "attach directly to the operator's real Chrome profile by default" in payload["rejected_patterns"]


def test_external_references_include_license_posture() -> None:
    decision = build_browser_harness_adoption_decision(generated_at="2026-05-02T03:21:00Z")
    references = {item.repo: item for item in decision.external_references}

    assert references["browser-use/browser-harness"].license == "MIT"
    assert references["browser-use/browser-harness-js"].license == "MIT"
    assert references["browser-use/workflow-use"].license == "AGPL-3.0"
    assert "no code copy" in references["browser-use/workflow-use"].chaseos_use


def test_forbidden_effect_flags_remain_false() -> None:
    payload = build_browser_harness_adoption_decision(generated_at="2026-05-02T03:22:00Z").to_dict()

    for key in (
        "dependency_install_attempted",
        "browser_harness_install_attempted",
        "browser_harness_cli_run_attempted",
        "real_browser_profile_attachment_attempted",
        "remote_browser_provisioning_attempted",
        "profile_sync_attempted",
        "cookie_or_session_read_attempted",
        "freeform_cdp_snippet_execution_attempted",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    ):
        assert payload[key] is False


def test_cli_json_output() -> None:
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = adoption_main(["--json"])
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["status"] == BROWSER_HARNESS_DECISION_STATUS
    assert payload["read_only"] is True
    assert payload["browser_harness_adopted"] is False
    assert payload["trusted_skill_write_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
