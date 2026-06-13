"""Shell/API tests for Phase 10F3 general Markdown inference preview."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.general_markdown_inference_preview import NEXT_RECOMMENDED_PASS
from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.config import frontend_dir
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_NEXT_PASS = "ventureops-operator-readiness-gate"
QA_NEXT_PASS = "phase11-chat-browser-dispatch-readiness-contract"


def test_api_get_general_markdown_inference_preview() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_general_markdown_inference_preview(max_files=1000, max_nodes=2000, max_edges=4000)

    assert resp["ok"] is True
    assert resp["surface"] == "general_markdown_inference_preview"
    assert resp["data"]["surface"] == "studio_general_markdown_inference_preview"
    assert resp["data"]["pass"] == "phase10f3-general-markdown-inference-preview"
    assert resp["data"]["performance_contract"]["bounded_scan"] is True
    assert resp["data"]["performance_contract"]["uses_parser_backed_graph_input"] is True
    assert resp["data"]["authority_boundary"]["writes_sidecar_hints"] is False


def test_api_scan_folder_embeds_general_markdown_inference_preview(tmp_path: Path) -> None:
    (tmp_path / "Index.md").write_text("[[Target]]\n", encoding="utf-8")
    (tmp_path / "Target.md").write_text("# Target\n", encoding="utf-8")
    api = StudioAPI(VAULT_ROOT)

    resp = api.scan_folder(str(tmp_path))

    assert resp["ok"] is True
    data = resp["data"]
    assert data["general_markdown_inference_preview"]["surface"] == "studio_general_markdown_inference_preview"
    assert data["general_markdown_inference_preview"]["summary"]["preview_ready"] is True
    assert data["general_markdown_inference_preview"]["authority_boundary"]["writes_graph_index"] is False
    assert data["general_markdown_inference_preview"]["readiness"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_workspace_entry_panel_embeds_10f3_preview() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_workspace_entry_panel()

    assert resp["ok"] is True
    data = resp["data"]
    assert data["workspace_entry"]["general_markdown_inference_preview_ready"] is True
    assert "inspect-general-markdown-inference-preview" in data["workspace_entry"]["allowed_actions"]
    assert data["general_markdown_inference_preview"]["surface"] == "studio_general_markdown_inference_preview"
    assert data["general_markdown_inference_preview"]["authority_boundary"]["writes_sidecar_hints"] is False


def test_panel_registry_marks_10f3_mounted_and_advances() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panel = next(item for item in registry["panels"] if item["id"] == "workspace-entry")

    assert registry["readiness"]["general_markdown_inference_preview_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == REGISTRY_NEXT_PASS
    assert panel["read_only"] is True
    assert "get_general_markdown_inference_preview" in panel["api_methods"]
    assert panel["possible_writes"] == []


def test_frontend_has_10f3_workspace_entry_tokens() -> None:
    frontend = frontend_dir()
    html = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "app.js").read_text(encoding="utf-8")
    styles = (frontend / "styles.css").read_text(encoding="utf-8")

    assert 'id="panel-workspace-entry"' in html
    assert "general_markdown_inference_preview" in app
    assert "10F3 Inference Preview" in app
    assert "workspace-inference-preview" in app
    assert ".workspace-inference-preview" in styles


def test_general_markdown_inference_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="general-markdown-inference-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True, [item for item in report["checks"] if not item["ok"]]
    assert report["status"] == "passed"
    assert report["writes_performed"] is False
    assert report["next_recommended_pass"] == QA_NEXT_PASS
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["composes_parser_backed_preview"]["ok"] is True
    assert checks["authority_preview_only_no_writes"]["ok"] is True
    assert checks["workspace_entry_registry_exposes_10f3"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_approval_artifact_writes"]["ok"] is True




