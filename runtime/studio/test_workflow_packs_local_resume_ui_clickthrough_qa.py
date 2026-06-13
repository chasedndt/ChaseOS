from __future__ import annotations

from pathlib import Path

from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.workflow_packs_local_resume_ui_clickthrough_qa import (
    PASS_ID,
    WORKFLOW_PACK_METHOD_CHAIN,
    build_workflow_packs_local_resume_ui_clickthrough_qa,
    format_workflow_packs_local_resume_ui_clickthrough_qa,
)


def test_workflow_packs_local_resume_ui_clickthrough_static_contract_writes_report(
    tmp_path: Path,
) -> None:
    report = build_workflow_packs_local_resume_ui_clickthrough_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-workflow-packs-clickthrough",
        capture_screenshots=False,
    )

    assert report["ok"] is True
    assert report["pass"] == PASS_ID
    assert report["summary"]["static_contract_ready"] is True
    assert report["summary"]["screenshot_captured"] is False
    assert report["static_contract"]["frontend_index_has_panel"] is True
    assert report["static_contract"]["frontend_runner_present"] is True
    assert report["static_contract"]["frontend_action_controls_present"] is True
    assert report["static_contract"]["frontend_action_styles_present"] is True
    assert report["static_contract"]["panel_has_pending_gate"] is True
    assert report["static_contract"]["panel_local_resume_ready"] is True
    assert report["static_contract"]["fixture_vault_persisted"] is False
    assert report["authority"]["real_vault_workflow_pack_state_write_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["evidence"]["written"] is True
    assert (tmp_path / str(report["evidence"]["report_path"])).is_file()
    assert (tmp_path / str(report["evidence"]["markdown_path"])).is_file()
    assert not (
        tmp_path
        / "07_LOGS/Studio-Visual-QA/test-workflow-packs-clickthrough/_fixture_static_contract"
    ).exists()


def test_workflow_packs_local_resume_ui_clickthrough_accepts_injected_runner(
    tmp_path: Path,
) -> None:
    def fake_runner(**kwargs):
        output_dir = Path(kwargs["output_dir"])
        screenshots = []
        for name in ("desktop", "mobile"):
            path = output_dir / f"{name}-workflow-packs-local-resume-clickthrough.png"
            path.write_bytes(b"fake-png" * 2048)
            screenshots.append(
                {
                    "viewport": name,
                    "url": "file:///tmp/index.html#/workflow-packs",
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "not_blank": True,
                    "approval_buttons_before": 2,
                    "approve_button_visible_before": True,
                    "reject_button_visible_before": True,
                    "no_review_items_after": True,
                    "run_status_after": "approved",
                    "approval_gate_removed_after": True,
                    "method_sequence": list(WORKFLOW_PACK_METHOD_CHAIN),
                    "expected_method_chain_present": True,
                    "resume_execute_summary": {
                        "external_actions_performed": False,
                        "provider_calls_performed": False,
                        "agent_bus_dispatch_performed": False,
                    },
                    "required_tokens_missing": [],
                    "framework_overlay_detected": False,
                    "console_errors_or_warnings": [],
                    "page_errors": [],
                }
            )
        return screenshots

    report = build_workflow_packs_local_resume_ui_clickthrough_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-workflow-packs-clickthrough",
        capture_screenshots=True,
        screenshot_runner=fake_runner,
    )

    assert report["ok"] is True
    assert report["summary"]["screenshot_captured"] is True
    assert report["summary"]["desktop_and_mobile_checked"] is True
    assert report["summary"]["clickthrough_verified"] is True
    assert len(report["screenshots"]) == 2
    assert all(item["expected_method_chain_present"] is True for item in report["screenshots"])
    assert all((tmp_path / item["path"]).is_file() for item in report["screenshots"])


def test_workflow_packs_local_resume_ui_clickthrough_text_output_states_boundary(
    tmp_path: Path,
) -> None:
    report = build_workflow_packs_local_resume_ui_clickthrough_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-workflow-packs-clickthrough",
        capture_screenshots=False,
    )
    output = format_workflow_packs_local_resume_ui_clickthrough_qa(report)

    assert "Workflow Packs Local Resume UI Clickthrough QA" in output
    assert "static_contract_ready: True" in output
    assert "screenshot_captured: False" in output
    assert "Boundary: temporary fixture only" in output


def test_studio_qa_runner_routes_workflow_packs_local_resume_static_contract(tmp_path: Path) -> None:
    report = run_studio_qa_runner(
        tmp_path,
        surface="workflow-packs-local-resume-ui-clickthrough",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "workflow-packs-local-resume-ui-clickthrough"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["writes_real_vault_workflow_pack_state"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["next_recommended_pass"] == (
        "product-workflow-packs-external-action-executor-design-only-if-authorized"
    )
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["workflow_packs_local_resume_static_contract_ready"]["ok"] is True
    assert checks["workflow_packs_frontend_action_controls_wired"]["ok"] is True
    assert checks["workflow_packs_temporary_fixture_cleaned"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
