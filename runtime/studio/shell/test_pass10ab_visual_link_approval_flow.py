"""Shell/API tests for Phase 10AB visual link approval flow."""

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


def _write_note(vault: Path, rel_path: str, title: str) -> None:
    path = vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: {title}\n---\n\n# {title}\n\nBody.\n", encoding="utf-8")


def test_api_preview_and_create_link_are_approval_gated(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, source_rel, "Source")
    _write_note(vault, target_rel, "Target")
    original = (vault / source_rel).read_text(encoding="utf-8")
    api = StudioAPI(vault)

    preview = api.preview_visual_link(
        "",
        "",
        source_rel,
        target_rel,
        "Source",
        "Target",
        "suggested",
        "depends_on",
        "needs target",
        "operator selected edge",
    )
    queued = api.create_link(
        "",
        "",
        source_rel,
        target_rel,
        "Source",
        "Target",
        "suggested",
        "depends_on",
        "needs target",
        "operator selected edge",
    )

    assert preview["ok"] is True
    assert preview["data"]["requires_approval"] is True
    assert preview["data"]["preview_edge"]["pending_visual_link"] is True
    assert "content" not in preview["data"]
    assert queued["ok"] is False
    assert queued["status"] == "requires_approval"
    assert queued["approval"]["action_type"] == "write_file"
    assert queued["approval"]["target_path"] == source_rel
    assert queued["data"]["pass"] == "phase10ab-visual-link-approval-flow"
    assert queued["data"]["preview_edge"]["edge_layer"] == "suggested"
    assert (vault / source_rel).read_text(encoding="utf-8") == original
    assert len(list((vault / StudioService.APPROVAL_DIR).glob("*.json"))) == 1


def test_api_visual_link_overlay_reports_pending_edges_without_markdown_reads(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, source_rel, "Source")
    _write_note(vault, target_rel, "Target")
    api = StudioAPI(vault)

    queued = api.create_link("", "", source_rel, target_rel, "Source", "Target")
    overlay = api.get_visual_link_overlay(250)

    assert queued["status"] == "requires_approval"
    assert overlay["ok"] is True
    assert overlay["data"]["overlay_edge_count"] == 1
    assert overlay["data"]["overlay_edges"][0]["approval_id"] == queued["approval"]["approval_id"]
    assert overlay["data"]["performance_contract"]["selected_markdown_reads"] == 0
    assert overlay["data"]["performance_contract"]["does_not_duplicate_full_graph_payload"] is True
    assert overlay["data"]["authority_boundary"]["writes_vault"] is False


def test_panel_registry_marks_graph_visual_link_approval_gated() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panels = {panel["id"]: panel for panel in registry["panels"]}
    graph_panel = panels["graph"]

    assert registry["readiness"]["visual_link_approval_flow_mounted"] is True
    assert registry["readiness"]["graph_pending_link_overlay_ready"] is True
    assert registry["readiness"]["graph_large_vault_overlay_memory_posture"] == "bounded-lightweight-overlay"
    assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
    assert graph_panel["write_mode"] == "approval_gated"
    assert graph_panel["read_only"] is False
    assert "preview_visual_link" in graph_panel["api_methods"]
    assert "create_link" in graph_panel["api_methods"]
    assert "get_visual_link_overlay" in graph_panel["api_methods"]
    assert "visual_link_approval_request" in graph_panel["possible_writes"]
    assert graph_panel["blocked_authority"]["vault_source_file_writes"] is False
    assert graph_panel["blocked_authority"]["canonical_mutation"] is False


def test_frontend_has_visual_link_modal_overlay_and_filter_tokens() -> None:
    frontend = frontend_dir()
    html = (frontend / "index.html").read_text(encoding="utf-8")
    write_actions = (frontend / "writeActions.js").read_text(encoding="utf-8")
    app_js = (frontend / "app.js").read_text(encoding="utf-8")
    graph_styles = (frontend / "graphStyles.js").read_text(encoding="utf-8")
    styles = (frontend / "styles.css").read_text(encoding="utf-8")

    assert "visual-link-modal" in html
    assert "ctx-start-link" in html
    assert "ctx-finish-link" in html
    assert "graph-link-overlay-summary" in html
    assert "preview_visual_link" in write_actions
    assert "create_link" in write_actions
    assert "get_visual_link_overlay" in write_actions
    assert "refreshVisualLinkOverlay" in write_actions
    assert "shiftKey" in write_actions
    assert "pending_visual_link" in write_actions
    assert "pendingVisualLink" in app_js
    assert "refreshVisualLinkOverlay" in app_js
    assert "visual-link-pending" in graph_styles
    assert "visual-link-approved" in graph_styles
    assert ".visual-link-node-pair" in styles
    # D3 refactor: .graph-link-overlay-summary replaced by .graph-status-dock/.graph-status-chip
    assert ".graph-status-dock" in styles


def test_visual_link_approval_flow_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="visual-link-approval-flow",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["writes_performed"] is False
    assert report["next_recommended_pass"] == "phase10ac-runtime-cockpit-action-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["visual_link_status_ok"]["ok"] is True
    assert checks["graph_panel_visual_link_approval_gated"]["ok"] is True
    assert checks["overlay_api_static_no_markdown_reads"]["ok"] is True
    assert checks["frontend_visual_link_modal_tokens_present"]["ok"] is True
    assert checks["frontend_pending_edge_renderer_tokens_present"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_approval_artifact_writes"]["ok"] is True





