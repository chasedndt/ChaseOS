"""Shell/API tests for Phase 10AA controlled node create/edit."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.service import StudioService
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.config import frontend_dir
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT_ROOT = Path(__file__).resolve().parents[3]


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    for rel in [
        "02_KNOWLEDGE/general",
        "07_LOGS/Agent-Activity",
    ]:
        (vault / rel).mkdir(parents=True, exist_ok=True)
    return vault


def test_api_preview_create_node_returns_target_without_writing(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    api = StudioAPI(vault)

    resp = api.preview_create_node("knowledge_doc", "Preview Me", "general")

    assert resp["ok"] is True
    assert resp["data"]["ok"] is True
    assert resp["data"]["target_path"] == "02_KNOWLEDGE/general/preview-me.md"
    assert not (vault / resp["data"]["target_path"]).exists()
    assert not (vault / StudioService.APPROVAL_DIR).exists()


def test_api_create_node_always_queues_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    api = StudioAPI(vault)

    resp = api.create_node("knowledge_doc", "Queue Me", "general")

    assert resp["ok"] is False
    assert resp["status"] == "requires_approval"
    assert resp["approval"]["action_type"] == "create_file"
    assert resp["approval"]["target_path"] == "02_KNOWLEDGE/general/queue-me.md"
    assert resp["data"]["pass"] == "phase10aa-controlled-node-create-edit"
    assert not (vault / "02_KNOWLEDGE/general/queue-me.md").exists()
    assert len(list((vault / StudioService.APPROVAL_DIR).glob("*.json"))) == 1


def test_api_metadata_edit_model_and_update_are_approval_gated(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/edit.md"
    (vault / rel).write_text("---\ntitle: Old\nstatus: draft\n---\n\n# Old\n", encoding="utf-8")
    api = StudioAPI(vault)

    model = api.get_node_metadata_edit_model("", rel)
    update = api.update_node_metadata("", {"title": "New", "status": "active"}, rel)

    assert model["ok"] is True
    assert model["data"]["write_mode"] == "approval_gated"
    assert "title" in model["data"]["editable_fields"]
    assert update["ok"] is False
    assert update["status"] == "requires_approval"
    assert update["approval"]["target_path"] == rel
    assert (vault / rel).read_text(encoding="utf-8").startswith("---\ntitle: Old")


def test_api_metadata_update_restricted_field_blocks_without_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/edit.md"
    (vault / rel).write_text("---\ntitle: Old\ntrust_state: raw\n---\n\n# Old\n", encoding="utf-8")
    api = StudioAPI(vault)

    resp = api.update_node_metadata("", {"trust_state": "canonical"}, rel)

    assert resp["ok"] is False
    assert resp["error"]["code"] == "restricted_fields"
    assert not (vault / StudioService.APPROVAL_DIR).exists()


def test_panel_registry_marks_graph_and_node_inspector_approval_gated() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panels = {panel["id"]: panel for panel in registry["panels"]}

    assert registry["readiness"]["all_declared_panels_safe_or_approval_gated"] is True
    assert registry["readiness"]["controlled_node_create_edit_mounted"] is True
    assert registry["readiness"]["visual_link_approval_flow_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
    assert panels["graph"]["write_mode"] == "approval_gated"
    assert panels["graph"]["read_only"] is False
    assert "preview_create_node" in panels["graph"]["api_methods"]
    assert "create_node_approval_request" in panels["graph"]["possible_writes"]
    assert panels["node-inspector"]["write_mode"] == "approval_gated"
    assert panels["node-inspector"]["read_only"] is False
    assert "get_node_metadata_edit_model" in panels["node-inspector"]["api_methods"]
    assert "metadata_update_approval_request" in panels["node-inspector"]["possible_writes"]
    assert all(panel["blocked_authority"]["vault_source_file_writes"] is False for panel in registry["panels"])


def test_frontend_has_create_preview_and_metadata_edit_tokens() -> None:
    frontend = frontend_dir()
    html = (frontend / "index.html").read_text(encoding="utf-8")
    write_actions = (frontend / "writeActions.js").read_text(encoding="utf-8")
    inspector_tabs = (frontend / "inspectorTabs.js").read_text(encoding="utf-8")
    styles = (frontend / "styles.css").read_text(encoding="utf-8")

    assert 'data-write-mode="approval-gated"' in html
    assert "create-node-target-preview" in html
    assert "create-node-approval-posture" in html
    assert "preview_create_node" in write_actions
    assert "refreshAfterApproval" in write_actions
    assert "metadata-edit-drawer" in inspector_tabs
    assert "get_node_metadata_edit_model" in inspector_tabs
    assert "update_node_metadata" in inspector_tabs
    assert "approval-gated" in inspector_tabs
    assert ".metadata-edit-drawer" in styles


def test_controlled_node_create_edit_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="controlled-node-create-edit",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["writes_performed"] is False
    assert report["next_recommended_pass"] == "phase10ab-visual-link-approval-flow"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["controlled_status_ok"]["ok"] is True
    assert checks["graph_panel_approval_gated"]["ok"] is True
    assert checks["node_inspector_panel_approval_gated"]["ok"] is True
    assert checks["frontend_create_preview_tokens_present"]["ok"] is True
    assert checks["frontend_metadata_edit_tokens_present"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_approval_artifact_writes"]["ok"] is True





