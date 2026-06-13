"""Shell/API tests for Phase 10F5/10F6 upgrade approval chain."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.config import frontend_dir
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT_ROOT = Path(__file__).resolve().parents[3]


def test_workspace_entry_embeds_upgrade_plan_preview() -> None:
    resp = StudioAPI(VAULT_ROOT).get_workspace_entry_panel()

    assert resp["ok"] is True
    data = resp["data"]
    assert data["upgrade_plan_approval_packet"]["surface"] == "studio_upgrade_plan_approval_packet"
    assert data["workspace_entry"]["upgrade_plan_approval_packet_ready"] is True
    assert "inspect-upgrade-plan-approval-packet" in data["workspace_entry"]["allowed_actions"]


def test_upgrade_plan_api_preview_no_write() -> None:
    resp = StudioAPI(VAULT_ROOT).get_upgrade_plan_approval_packet(str(VAULT_ROOT), "chaseos_obsidian", False)

    assert resp["ok"] is True
    assert resp["surface"] == "upgrade_plan_approval_packet"
    assert resp["data"]["approval_packet"]["artifact_written"] is False
    assert resp["data"]["authority_boundary"]["writes_target_workspace"] is False


def test_scan_folder_embeds_upgrade_plan_preview(tmp_path: Path) -> None:
    resp = StudioAPI(VAULT_ROOT).scan_folder(str(tmp_path))

    assert resp["ok"] is True
    assert resp["data"]["upgrade_plan_approval_packet"]["surface"] == "studio_upgrade_plan_approval_packet"
    assert resp["data"]["upgrade_plan_approval_packet"]["planned_writes"]["count"] >= 1


def test_registry_marks_upgrade_packet_mounted() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panel = next(item for item in registry["panels"] if item["id"] == "workspace-entry")

    assert registry["readiness"]["upgrade_plan_approval_packet_mounted"] is True
    assert "get_upgrade_plan_approval_packet" in panel["api_methods"]
    assert panel["read_only"] is True


def test_frontend_has_upgrade_approval_tokens() -> None:
    frontend = frontend_dir()
    app = (frontend / "app.js").read_text(encoding="utf-8")

    assert "10F5 Upgrade Approval Packet" in app
    assert "Prepare Approval Packet" in app
    assert "requestWorkspaceUpgradeApproval" in app
    assert "Execution button" in app


def test_upgrade_plan_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(VAULT_ROOT, surface="upgrade-plan-approval-packet", mode="static")

    assert report["ok"] is True, [item for item in report["checks"] if not item["ok"]]
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["approval_packet_preview_present"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_upgrade_artifact_writes"]["ok"] is True
    assert report["next_recommended_pass"] in {
        "phase10f6-approved-upgrade-execution-proof",
        "phase11-chat-browser-dispatch-readiness-contract",
    }


def test_approved_upgrade_execution_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(VAULT_ROOT, surface="approved-upgrade-execution-proof", mode="static")

    assert report["ok"] is True, [item for item in report["checks"] if not item["ok"]]
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["approved_upgrade_requires_execute"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_upgrade_artifact_writes"]["ok"] is True
    assert report["next_recommended_pass"] == "phase11-chat-browser-dispatch-readiness-contract"

