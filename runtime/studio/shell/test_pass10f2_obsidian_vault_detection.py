"""Shell/API tests for Phase 10F2 Obsidian vault detection."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.config import frontend_dir
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT_ROOT = Path(__file__).resolve().parents[3]
COMPONENT_NEXT_PASS = "phase10f5-upgrade-plan-approval-packet"
REGISTRY_NEXT_PASS = "ventureops-operator-readiness-gate"
QA_NEXT_PASS = "phase11-chat-browser-dispatch-readiness-contract"


def test_api_get_obsidian_vault_detection() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_obsidian_vault_detection()

    assert resp["ok"] is True
    assert resp["surface"] == "obsidian_vault_detection"
    assert resp["data"]["surface"] == "studio_obsidian_vault_detection"
    assert resp["data"]["pass"] == "phase10f2-obsidian-vault-detection"
    assert resp["data"]["performance_contract"]["bounded_scan"] is True
    assert resp["data"]["performance_contract"]["reads_markdown_contents_bounded"] is True
    assert resp["data"]["authority_boundary"]["writes_obsidian_config"] is False


def test_api_scan_folder_embeds_obsidian_detection(tmp_path: Path) -> None:
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "workspace.json").write_text('{"main": {}}', encoding="utf-8")
    (tmp_path / "note.md").write_text("[[Other]]\n", encoding="utf-8")
    api = StudioAPI(VAULT_ROOT)

    resp = api.scan_folder(str(tmp_path))

    assert resp["ok"] is True
    data = resp["data"]
    assert data["obsidian_vault_detection"]["summary"]["classification"] == "obsidian_vault_detected"
    assert data["obsidian_vault_detection"]["authority_boundary"]["activates_plugins"] is False
    assert data["obsidian_vault_detection"]["readiness"]["next_recommended_pass"] == COMPONENT_NEXT_PASS


def test_workspace_entry_panel_embeds_10f2_detection() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_workspace_entry_panel()

    assert resp["ok"] is True
    data = resp["data"]
    assert data["workspace_entry"]["obsidian_vault_detection_ready"] is True
    assert "inspect-obsidian-vault-detection" in data["workspace_entry"]["allowed_actions"]
    assert data["obsidian_vault_detection"]["surface"] == "studio_obsidian_vault_detection"
    assert data["obsidian_vault_detection"]["authority_boundary"]["writes_obsidian_config"] is False


def test_panel_registry_marks_10f2_mounted_and_advances() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panel = next(item for item in registry["panels"] if item["id"] == "workspace-entry")

    assert registry["readiness"]["obsidian_vault_detection_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == REGISTRY_NEXT_PASS
    assert panel["read_only"] is True
    assert "get_obsidian_vault_detection" in panel["api_methods"]
    assert panel["possible_writes"] == []


def test_frontend_has_10f2_workspace_entry_tokens() -> None:
    frontend = frontend_dir()
    html = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "app.js").read_text(encoding="utf-8")

    assert 'id="panel-workspace-entry"' in html
    assert "obsidian_vault_detection" in app
    assert "Obsidian Detection" in app
    assert "10F2 Obsidian Detection" in app


def test_obsidian_vault_detection_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="obsidian-vault-detection",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["writes_performed"] is False
    assert report["next_recommended_pass"] == QA_NEXT_PASS
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["bounded_content_scan_counts_only"]["ok"] is True
    assert checks["authority_read_only_no_obsidian_writes"]["ok"] is True
    assert checks["workspace_entry_registry_exposes_10f2"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_approval_artifact_writes"]["ok"] is True





