"""Shell/API tests for Phase 10F4 ChaseOS bootstrap wizard preview."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.chaseos_bootstrap_wizard_preview import NEXT_RECOMMENDED_PASS
from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.config import frontend_dir
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_NEXT_PASS = "ventureops-operator-readiness-gate"
QA_NEXT_PASS = "phase11-chat-browser-dispatch-readiness-contract"


def test_api_get_chaseos_bootstrap_wizard_preview() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_chaseos_bootstrap_wizard_preview(str(VAULT_ROOT), "chaseos_obsidian")

    assert resp["ok"] is True
    assert resp["surface"] == "chaseos_bootstrap_wizard_preview"
    assert resp["data"]["surface"] == "studio_chaseos_bootstrap_wizard_preview"
    assert resp["data"]["pass"] == "phase10f4-chaseos-bootstrap-wizard-preview"
    assert resp["data"]["authority_boundary"]["writes_selected_folder"] is False
    assert resp["data"]["authority_boundary"]["writes_approval_artifacts"] is False


def test_api_scan_folder_embeds_bootstrap_preview(tmp_path: Path) -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.scan_folder(str(tmp_path))

    assert resp["ok"] is True
    data = resp["data"]
    assert data["chaseos_bootstrap_wizard_preview"]["surface"] == "studio_chaseos_bootstrap_wizard_preview"
    assert data["chaseos_bootstrap_wizard_preview"]["summary"]["preview_ready"] is True
    assert data["chaseos_bootstrap_wizard_preview"]["authority_boundary"]["writes_target_files"] is False
    assert data["chaseos_bootstrap_wizard_preview"]["readiness"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_workspace_entry_panel_embeds_10f4_preview() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_workspace_entry_panel()

    assert resp["ok"] is True
    data = resp["data"]
    assert data["workspace_entry"]["chaseos_bootstrap_wizard_preview_ready"] is True
    assert "inspect-chaseos-bootstrap-wizard-preview" in data["workspace_entry"]["allowed_actions"]
    assert data["chaseos_bootstrap_wizard_preview"]["surface"] == "studio_chaseos_bootstrap_wizard_preview"
    assert data["chaseos_bootstrap_wizard_preview"]["authority_boundary"]["invokes_scaffold_generator"] is False


def test_panel_registry_marks_10f4_mounted_and_advances() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panel = next(item for item in registry["panels"] if item["id"] == "workspace-entry")

    assert registry["readiness"]["chaseos_bootstrap_wizard_preview_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == REGISTRY_NEXT_PASS
    assert panel["read_only"] is True
    assert "get_chaseos_bootstrap_wizard_preview" in panel["api_methods"]
    assert panel["possible_writes"] == []


def test_frontend_has_10f4_workspace_entry_tokens() -> None:
    frontend = frontend_dir()
    html = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "app.js").read_text(encoding="utf-8")
    styles = (frontend / "styles.css").read_text(encoding="utf-8")

    assert 'id="panel-workspace-entry"' in html
    assert "chaseos_bootstrap_wizard_preview" in app
    assert "10F4 Bootstrap Preview" in app
    assert "workspace-bootstrap-preview" in app
    assert ".workspace-bootstrap-preview" in styles


def test_chaseos_bootstrap_wizard_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="chaseos-bootstrap-wizard-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True, [item for item in report["checks"] if not item["ok"]]
    assert report["status"] == "passed"
    assert report["writes_performed"] is False
    assert report["next_recommended_pass"] == QA_NEXT_PASS
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["target_plan_present"]["ok"] is True
    assert checks["authority_preview_only_no_writes"]["ok"] is True
    assert checks["workspace_entry_registry_exposes_10f4"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_approval_artifact_writes"]["ok"] is True



