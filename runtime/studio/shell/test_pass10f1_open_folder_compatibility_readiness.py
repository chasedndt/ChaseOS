"""Shell/API tests for Phase 10F1 Open Folder compatibility readiness."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.config import frontend_dir
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_NEXT_PASS = "ventureops-operator-readiness-gate"
QA_NEXT_PASS = "phase11-chat-browser-dispatch-readiness-contract"


def test_api_get_open_folder_compatibility_readiness() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_open_folder_compatibility_readiness()

    assert resp["ok"] is True
    assert resp["surface"] == "open_folder_compatibility_readiness"
    assert resp["data"]["surface"] == "studio_open_folder_compatibility_readiness"
    assert resp["data"]["pass"] == "phase10f1-open-folder-compatibility-readiness"
    assert resp["data"]["performance_contract"]["bounded_scan"] is True
    assert resp["data"]["performance_contract"]["reads_markdown_contents"] is False


def test_api_scan_folder_embeds_compatibility_readiness(tmp_path: Path) -> None:
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / "note.md").write_text("# Note\n", encoding="utf-8")
    api = StudioAPI(VAULT_ROOT)

    resp = api.scan_folder(str(tmp_path))

    assert resp["ok"] is True
    data = resp["data"]
    assert data["scan"]["mode"] == "general_markdown"
    assert data["compatibility_readiness"]["target"]["mode"] == "obsidian_vault"
    assert data["compatibility_readiness"]["authority_boundary"]["writes_selected_folder"] is False


def test_workspace_entry_panel_embeds_10f1_readiness() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_workspace_entry_panel()

    assert resp["ok"] is True
    data = resp["data"]
    assert data["workspace_entry"]["open_folder_compatibility_readiness_ready"] is True
    assert "inspect-open-folder-compatibility-readiness" in data["workspace_entry"]["allowed_actions"]
    assert data["compatibility_readiness"]["surface"] == "studio_open_folder_compatibility_readiness"
    assert data["compatibility_readiness"]["authority_boundary"]["migration_writer_built"] is False


def test_panel_registry_marks_10f1_mounted_and_advances() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panel = next(item for item in registry["panels"] if item["id"] == "workspace-entry")

    assert registry["readiness"]["open_folder_compatibility_readiness_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == REGISTRY_NEXT_PASS
    assert panel["read_only"] is True
    assert "get_open_folder_compatibility_readiness" in panel["api_methods"]
    assert panel["possible_writes"] == []


def test_frontend_has_10f1_workspace_entry_tokens() -> None:
    frontend = frontend_dir()
    html = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "app.js").read_text(encoding="utf-8")
    styles = (frontend / "styles.css").read_text(encoding="utf-8")

    assert 'id="panel-workspace-entry"' in html
    assert "compatibility_readiness" in app
    assert "Compatibility Readiness" in app
    assert "10F1 Readiness" in app
    assert "workspace-compatibility-readiness" in app
    assert ".workspace-compatibility-readiness" in styles


def test_open_folder_compatibility_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="open-folder-compatibility-readiness",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["writes_performed"] is False
    assert report["next_recommended_pass"] == QA_NEXT_PASS
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["bounded_scan_no_content_reads"]["ok"] is True
    assert checks["authority_read_only_no_migration"]["ok"] is True
    assert checks["workspace_entry_registry_exposes_10f1"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_approval_artifact_writes"]["ok"] is True





