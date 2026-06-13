"""Tests for the Live Operator Shell browser no-action panel model."""

from __future__ import annotations

import inspect

import runtime.operator_surface.browser.live_shell_panel as live_shell_panel
from runtime.operator_surface.browser.live_shell_panel import (
    PANEL_MODEL_VERSION,
    SURFACE_ID,
    build_live_operator_shell_browser_panel,
)


def _readiness_model() -> dict[str, object]:
    return {
        "ok": True,
        "surface": "studio_browser_runtime_operator_ui_readiness_contract",
        "model_version": "studio.browser_runtime_operator_ui_readiness.v1",
        "summary": {"overall_status": "MVP_DONE_PRODUCTION_BLOCKED"},
        "readiness": {
            "operator_ui_readiness_contract_ready": True,
            "studio_operator_ui_built": True,
            "live_browser_control_ui_built": False,
        },
        "blocked_reasons": ["browser_use_cli_live_validation_blocked_unavailable"],
        "current_evidence": {
            "browser_run_logs_root": {"path": "07_LOGS/Browser-Runs", "exists": False},
            "agent_activity_root": {"path": "07_LOGS/Agent-Activity", "exists": True},
        },
        "authority": {
            "launches_browser": False,
            "connects_cdp": False,
            "writes_agent_bus_tasks": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _dispatch_manifest(*, hard_denials: list[str], target_url: str = "http://127.0.0.1:4173") -> dict[str, object]:
    return {
        "surface": "chat_studio_browser_runtime_dispatch_lane",
        "target_profile": {
            "profile_id": "siteops.browser_cdp_read_only_loopback.v1",
            "selected_profile_id": "siteops.browser_cdp_read_only_loopback.v1",
            "operator_session_scope": "throwaway-local-only",
            "allowed_target_url": target_url,
        },
        "approval_record": {
            "gate_approval_id": None,
            "artifact_ref": None,
            "approval_status": "missing" if "unapproved" in hard_denials else "approved",
            "structurally_valid": "unapproved" not in hard_denials,
        },
        "readiness": {
            "approved_dispatch_ready": not hard_denials,
            "hard_denials": hard_denials,
        },
        "denial_proofs": {
            key: {"denied": True, "reason": f"{key} reason"} for key in hard_denials
        },
        "visible_control_ux": {
            "required": True,
            "operator_must_see_target_url": target_url,
            "operator_must_see_target_profile": "siteops.browser_cdp_read_only_loopback.v1",
            "operator_must_see_approval_id": None,
            "operator_must_see_denial_reasons": hard_denials,
        },
        "authority": {
            "chat_or_studio_direct_browser_authority": False,
            "approval_consumption_allowed_only_in_executor": True,
            "agent_bus_task_write_allowed": False,
            "provider_call_allowed": False,
            "canonical_writeback_allowed": False,
        },
    }


def test_module_does_not_import_or_call_browser_execution_writer_or_connector_surfaces() -> None:
    source = inspect.getsource(live_shell_panel)
    forbidden_tokens = (
        "execute_chat_studio_browser_runtime_dispatch_lane_proof",
        "execute_cdp_read_only_proof",
        "write_cdp_read_only_approval",
        "OperatorExecutor",
        "BrowserAdapter",
        "subprocess",
        "socket.",
        "requests.",
        "urllib.request",
        "playwright",
        "browser_use",
        "mcp",
        "agent_bus",
        "write_text(",
        "mkdir(",
        "open(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_display_ready_panel_composes_readiness_without_live_target_or_side_effects() -> None:
    panel = build_live_operator_shell_browser_panel(
        ".",
        generated_at="2026-05-12T02:00:00Z",
        readiness_model=_readiness_model(),
    )

    assert panel["ok"] is True
    assert panel["surface"] == SURFACE_ID
    assert panel["model_version"] == PANEL_MODEL_VERSION
    assert panel["current_state"] == "display_ready"
    assert panel["available_states"] >= [
        "display_ready",
        "blocked_missing_backend_contract",
        "blocked_missing_approval",
        "blocked_scope_or_target",
    ]
    assert panel["visible_control"]["runtime"] == "Hermes"
    assert panel["visible_control"]["target_url"] is None
    assert panel["visible_control"]["target_domain"] is None
    assert panel["visible_control"]["manual_takeover_available"] is False
    assert panel["readiness_model"]["surface"] == "studio_browser_runtime_operator_ui_readiness_contract"
    assert panel["dispatch_manifest"] is None
    assert {record["dependency_id"] for record in panel["dependency_routing"]} >= {
        "browser-shell-action-execution-contract",
        "browser-shell-approval-consumption-contract",
        "browser-shell-agent-bus-write-contract",
    }
    authority = panel["authority"]
    assert authority["read_only"] is True
    assert authority["browser_launch_attempted"] is False
    assert authority["cdp_connection_attempted"] is False
    assert authority["browser_use_cli_invoked"] is False
    assert authority["approval_consumed"] is False
    assert authority["idempotency_marker_reserved"] is False
    assert authority["agent_bus_write_performed"] is False
    assert authority["provider_or_connector_called"] is False
    assert authority["credential_or_profile_read"] is False
    assert authority["gate_mutation_performed"] is False
    assert authority["workflow_or_role_card_mutation_performed"] is False
    assert authority["canonical_writeback_performed"] is False


def test_backend_contract_failure_blocks_before_display_ready_with_dependency_metadata() -> None:
    readiness_model = _readiness_model()
    readiness_model["ok"] = False
    readiness_model["status"] = "BLOCKED / OPERATOR UI READINESS CONTRACT INCOMPLETE"
    readiness_model["readiness"] = {
        **dict(readiness_model["readiness"]),
        "operator_ui_readiness_contract_ready": False,
    }
    readiness_model["blocked_reasons"] = [
        "studio_browser_runtime_operator_ui_readiness_contract_missing"
    ]

    panel = build_live_operator_shell_browser_panel(
        ".",
        target_url="http://127.0.0.1:4173",
        generated_at="2026-05-12T02:03:00Z",
        readiness_model=readiness_model,
        dispatch_manifest=_dispatch_manifest(hard_denials=[], target_url="http://127.0.0.1:4173"),
    )

    assert panel["current_state"] == "blocked_missing_backend_contract"
    assert panel["visible_control"]["approved_dispatch_ready"] is True
    assert panel["panels"]["readiness_blockers"]["state"] == "blocked_missing_backend_contract"
    assert panel["panels"]["readiness_blockers"]["browser_runtime_blocked_reasons"] == [
        "studio_browser_runtime_operator_ui_readiness_contract_missing"
    ]
    assert any(
        record["dependency_id"] == "browser-shell-readiness-backend-contract"
        and record["affected_panel"] == "readiness_blockers"
        and record["blocked_action"] == "display-live-browser-shell-as-ready"
        for record in panel["dependency_routing"]
    )
    assert panel["authority"]["browser_launch_attempted"] is False
    assert panel["authority"]["cdp_connection_attempted"] is False
    assert panel["authority"]["agent_bus_write_performed"] is False
    assert panel["authority"]["provider_or_connector_called"] is False
    assert panel["authority"]["canonical_writeback_performed"] is False


def test_incomplete_readiness_backend_model_fails_closed_before_display_ready() -> None:
    readiness_model = _readiness_model()
    readiness_model.pop("ok")
    readiness_model["readiness"] = {}
    readiness_model["blocked_reasons"] = []

    panel = build_live_operator_shell_browser_panel(
        ".",
        target_url="http://127.0.0.1:4173",
        generated_at="2026-05-12T02:04:00Z",
        readiness_model=readiness_model,
        dispatch_manifest=_dispatch_manifest(hard_denials=[], target_url="http://127.0.0.1:4173"),
    )

    assert panel["current_state"] == "blocked_missing_backend_contract"
    assert any(
        record["dependency_id"] == "browser-shell-readiness-backend-contract"
        for record in panel["dependency_routing"]
    )
    assert panel["authority"]["browser_launch_attempted"] is False
    assert panel["authority"]["agent_bus_write_performed"] is False
    assert panel["authority"]["canonical_writeback_performed"] is False


def test_empty_readiness_backend_model_fails_closed_before_display_ready() -> None:
    panel = build_live_operator_shell_browser_panel(
        ".",
        target_url="http://127.0.0.1:4173",
        generated_at="2026-05-12T02:04:30Z",
        readiness_model={},
        dispatch_manifest=_dispatch_manifest(hard_denials=[], target_url="http://127.0.0.1:4173"),
    )

    assert panel["current_state"] == "blocked_missing_backend_contract"
    assert any(
        record["dependency_id"] == "browser-shell-readiness-backend-contract"
        for record in panel["dependency_routing"]
    )
    assert panel["authority"]["browser_launch_attempted"] is False
    assert panel["authority"]["agent_bus_write_performed"] is False
    assert panel["authority"]["canonical_writeback_performed"] is False


def test_malformed_readiness_blocked_reasons_fails_closed_without_crashing() -> None:
    readiness_model = _readiness_model()
    readiness_model["blocked_reasons"] = None

    panel = build_live_operator_shell_browser_panel(
        ".",
        target_url="http://127.0.0.1:4173",
        generated_at="2026-05-12T02:04:45Z",
        readiness_model=readiness_model,
        dispatch_manifest=_dispatch_manifest(hard_denials=[], target_url="http://127.0.0.1:4173"),
    )

    assert panel["current_state"] == "blocked_missing_backend_contract"
    assert any(
        record["dependency_id"] == "browser-shell-readiness-backend-contract"
        for record in panel["dependency_routing"]
    )
    assert panel["authority"]["browser_launch_attempted"] is False
    assert panel["authority"]["agent_bus_write_performed"] is False
    assert panel["authority"]["canonical_writeback_performed"] is False


def test_valid_target_without_approval_reports_blocked_missing_approval_and_visible_control_metadata() -> None:
    panel = build_live_operator_shell_browser_panel(
        ".",
        target_url="http://127.0.0.1:4173/path?q=1",
        gate_approval_id="approval-missing",
        generated_at="2026-05-12T02:05:00Z",
        readiness_model=_readiness_model(),
        dispatch_manifest=_dispatch_manifest(hard_denials=["unapproved"], target_url="http://127.0.0.1:4173/path?q=1"),
    )

    assert panel["current_state"] == "blocked_missing_approval"
    assert panel["visible_control"]["target_url"] == "http://127.0.0.1:4173/path?q=1"
    assert panel["visible_control"]["target_domain"] == "127.0.0.1"
    assert panel["visible_control"]["approval_id"] == "approval-missing"
    assert panel["visible_control"]["approval_status"] == "missing"
    assert panel["visible_control"]["denial_reasons"] == ["unapproved"]
    assert panel["panels"]["approval_context"]["state"] == "blocked_missing_approval"
    assert panel["authority"]["approval_consumed"] is False


def test_scope_or_profile_denial_takes_precedence_over_missing_approval() -> None:
    panel = build_live_operator_shell_browser_panel(
        ".",
        target_url="http://127.0.0.1:4173",
        browser_target_profile="real-profile-browser",
        browser_auth_ref="session:blocked",
        generated_at="2026-05-12T02:10:00Z",
        readiness_model=_readiness_model(),
        dispatch_manifest=_dispatch_manifest(
            hard_denials=["unapproved", "browser_auth_requested", "unsupported_target_profile"]
        ),
    )

    assert panel["current_state"] == "blocked_scope_or_target"
    assert panel["visible_control"]["target_profile"] == "real-profile-browser"
    assert set(panel["visible_control"]["denial_reasons"]) == {
        "unapproved",
        "browser_auth_requested",
        "unsupported_target_profile",
    }
    assert panel["panels"]["readiness_blockers"]["state"] == "blocked_scope_or_target"
    assert any(
        record["missing_contract"] == "Credential/Profile Policy authenticated-session contract"
        for record in panel["dependency_routing"]
    )


def test_panel_builder_calls_only_read_only_composition_builders(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    def fake_readiness(vault_root: object, *, generated_at: str | None = None) -> dict[str, object]:
        calls.append(("readiness", vault_root))
        return _readiness_model()

    def fake_manifest(vault_root: object, **kwargs: object) -> dict[str, object]:
        calls.append(("manifest", kwargs))
        return _dispatch_manifest(hard_denials=["unapproved"], target_url=str(kwargs["target_url"]))

    monkeypatch.setattr(live_shell_panel, "build_studio_browser_runtime_operator_ui_readiness", fake_readiness)
    monkeypatch.setattr(live_shell_panel, "build_chat_studio_browser_runtime_dispatch_lane_manifest", fake_manifest)

    panel = build_live_operator_shell_browser_panel(
        ".",
        target_url="http://127.0.0.1:4173",
        gate_approval_id="approval-missing",
        generated_at="2026-05-12T02:15:00Z",
    )

    assert [call[0] for call in calls] == ["readiness", "manifest"]
    assert panel["current_state"] == "blocked_missing_approval"
    assert panel["authority"]["browser_launch_attempted"] is False
    assert panel["authority"]["agent_bus_write_performed"] is False
