"""Tests for the personal context import multi-instance fixture harness."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.personal_context_import_multi_instance_fixture_harness import (
    NEXT_RECOMMENDED_PASS,
    SURFACE_ID,
    build_personal_context_import_multi_instance_fixture_harness,
)


def test_multi_instance_fixture_harness_covers_required_rules_and_boundaries(tmp_path: Path) -> None:
    result = build_personal_context_import_multi_instance_fixture_harness(
        tmp_path / "vault",
        fixture_root=tmp_path / "f",
    )

    assert result["ok"] is True
    assert result["surface"] == SURFACE_ID
    assert result["status"] == "COMPLETE / MULTI-INSTANCE FIXTURE HARNESS READY / CANONICAL WRITES BLOCKED"
    assert result["source_text_included_in_payload"] is False
    assert result["summary"]["positive_fixture_count"] >= 3
    assert result["summary"]["positive_pass_count"] == result["summary"]["positive_fixture_count"]
    assert result["summary"]["negative_pass_count"] == result["summary"]["negative_fixture_count"]
    assert result["summary"]["missing_required_rule_id_count"] == 0
    assert result["summary"]["canonical_write_violation_count"] == 0
    assert result["summary"]["execution_success_count"] == result["summary"]["positive_fixture_count"]
    assert result["coverage"]["missing_required_rule_ids"] == []
    assert "prompt_engineering" in result["coverage"]["matched_rule_ids"]
    assert "agent_engineering" in result["coverage"]["matched_rule_ids"]
    assert "runtime_engineering" in result["coverage"]["matched_rule_ids"]
    assert "mandarin_hsk1" in result["coverage"]["matched_rule_ids"]
    assert "content_creation_youtube_monetization" in result["coverage"]["matched_rule_ids"]
    assert result["readiness"]["multi_instance_test_harness_built"] is True
    assert result["readiness"]["canonical_write_block_verified"] is True
    assert result["readiness"]["runtime_consumption_live_verified"] is False
    assert result["readiness"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result["authority"]["writes_live_vault"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False


def test_multi_instance_fixture_harness_blocks_secret_fixture_without_echoing_source(tmp_path: Path) -> None:
    result = build_personal_context_import_multi_instance_fixture_harness(
        tmp_path / "vault",
        fixture_root=tmp_path / "f",
    )
    encoded = json.dumps(result)
    negative = result["negative_fixture_results"][0]

    assert result["ok"] is True
    assert negative["ok"] is True
    assert negative["preview_ok_expected_false"] is True
    assert negative["expected_blockers_present"] is True
    assert "secret_or_credential_indicator_present" in negative["blocked_reasons"]
    assert negative["approval_request_created"] is False
    assert "fixture-secret-value-123456789" not in encoded
    assert "An anonymized context packet mentions Mandarin" not in encoded
    assert result["fixture_run"]["fixture_run_root_exists_after"] is True


def test_api_and_registry_expose_multi_instance_fixture_harness(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_result = StudioAPI(tmp_path).get_personal_context_import_multi_instance_fixture_harness()
    registry = build_native_shell_panel_registry(tmp_path)
    context_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "context-import"), {})

    assert api_result["ok"] is True
    assert api_result["surface"] == "personal_context_import_multi_instance_fixture_harness"
    assert api_result["data"]["readiness"]["multi_instance_test_harness_built"] is True
    assert "get_personal_context_import_multi_instance_fixture_harness" in (context_panel.get("api_methods") or [])
    assert "personal_context_import_fixture_harness_temp_artifacts" in (context_panel.get("possible_writes") or [])
    assert registry["readiness"]["personal_context_import_multi_instance_fixture_harness_ready"] is True
    assert registry["readiness"]["personal_context_import_fixture_writes_temp_only"] is True
