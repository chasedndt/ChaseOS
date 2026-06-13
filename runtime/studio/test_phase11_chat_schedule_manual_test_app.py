"""Tests for the Studio Chat schedule manual test app."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_chat_schedule_manual_test_app import (
    build_schedule_manual_test_app_plan,
    execute_schedule_manual_test_action,
    render_schedule_manual_test_app_html,
    smoke_test_schedule_manual_test_app,
)


def _seed_operator_today_workflow(root: Path) -> None:
    registry = root / "runtime" / "workflows" / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    (registry / "operator_today.yaml").write_text(
        "\n".join(
            [
                "id: operator_today",
                "name: Operator Today",
                "version: '1.0'",
                "description: Test operator briefing workflow.",
                "task_type: operator-briefing",
                "role_card: operator-briefing",
                "trigger_type: manual",
                "owner: operator",
                "status: active",
                "permission_ceiling: standard",
                "writeback_targets:",
                "  - 07_LOGS/Operator-Briefs/",
                "failure_behavior: escalate",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_manual_test_app_plan_is_loopback_and_boundary_safe(tmp_path: Path) -> None:
    plan = build_schedule_manual_test_app_plan(tmp_path, port=8791)

    assert plan["ok"] is True
    assert plan["surface"] == "phase11_chat_schedule_manual_test_app"
    assert plan["manual_ui_test_ready"] is True
    assert plan["authority"]["binds_loopback_only"] is True
    assert plan["authority"]["secret_fields_rendered"] is False
    assert plan["authority"]["external_scheduler_mutation_allowed"] is False
    assert plan["authority"]["runtime_dispatch_allowed"] is False
    assert plan["authority"]["discord_api_calls_allowed"] is False
    assert plan["authority"]["provider_calls_allowed"] is False
    assert plan["authority"]["credential_values_visible"] is False
    assert plan["authority"]["canonical_mutation_allowed"] is False


def test_manual_test_app_html_exposes_expected_buttons_without_secret_fields(tmp_path: Path) -> None:
    plan = build_schedule_manual_test_app_plan(tmp_path)
    html = render_schedule_manual_test_app_html(plan)

    assert "Manual Controls" in html
    assert "Preview Proposal" in html
    assert "Queue Proposal" in html
    assert "Consume Proposal" in html
    assert "Write Intent" in html
    assert "Preview Activation" in html
    assert "Queue Activation" in html
    assert "Activate" in html
    assert "Preview Export" in html
    assert "Queue Export" in html
    assert "Write Export Packet" in html
    assert "OPENAI_API_KEY" not in html
    assert "DISCORD_TOKEN" not in html


def test_manual_test_action_preview_uses_existing_studio_api(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)

    response = execute_schedule_manual_test_action(
        tmp_path,
        "preview-proposal",
        {
            "workflowId": "operator_today",
            "cronExpression": "17 9 * * 1-5",
            "timezoneName": "Europe/London",
            "runtimeAdapterTarget": "openclaw",
            "scheduleSummary": "Manual test.",
        },
    )

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_schedule_proposal_packet"
    assert response["data"]["summary"]["approval_request_created"] is False
    assert response["data"]["digest_proof"]["schedule_digest"]


def test_manual_test_action_blocks_secret_like_inputs(tmp_path: Path) -> None:
    response = execute_schedule_manual_test_action(
        tmp_path,
        "preview-proposal",
        {"scheduleSummary": "OPENAI_API_KEY=test-key-test"},
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "secret_indicator_blocked"


def test_manual_test_app_smoke_starts_and_stops(tmp_path: Path) -> None:
    smoke = smoke_test_schedule_manual_test_app(tmp_path)

    assert smoke["ok"] is True
    assert smoke["server_stopped"] is True
    assert smoke["manual_ui_test_ready"] is True
    assert smoke["visual_browser_qa_complete"] is False
    assert any(item["route"] == "/" and item["manual_controls_present"] for item in smoke["checks"])
    assert not any(item["secret_field_present"] for item in smoke["checks"])
