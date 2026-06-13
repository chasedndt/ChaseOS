"""Shell/API tests for Phase 10AC Runtime Cockpit action readiness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.qa_runner import run_studio_qa_runner
from runtime.studio.service import StudioService
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.config import frontend_dir
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


VAULT_ROOT = Path(__file__).resolve().parents[3]


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "runtime" / "lifecycle").mkdir(parents=True)
    (vault / "runtime" / "lifecycle" / "codex.lifecycle.yaml").write_text(
        "runtime: codex\n",
        encoding="utf-8",
    )
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    return vault


def test_api_get_runtime_cockpit_action_readiness() -> None:
    api = StudioAPI(VAULT_ROOT)

    resp = api.get_runtime_cockpit_action_readiness()

    assert resp["ok"] is True
    assert resp["surface"] == "runtime_cockpit_action_readiness"
    assert resp["data"]["status"] == "COMPLETE / APPROVAL-GATED / VERIFIED"
    assert resp["data"]["readiness"]["no_direct_runtime_execution"] is True


def test_api_request_runtime_cockpit_action_queues_approval_only(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    api = StudioAPI(vault)
    readiness = api.get_runtime_cockpit_action_readiness()["data"]
    requestable = readiness["requestable_actions"]
    if not requestable:
        pytest.skip("fixture/runtime settings expose no requestable startup surfaces")

    resp = api.request_runtime_cockpit_action(requestable[0]["action_id"], "operator note")

    assert resp["ok"] is False
    assert resp["status"] == "requires_approval"
    assert resp["approval"]["action_type"] == "create_file"
    assert resp["data"]["boundary"]["direct_runtime_execution_allowed"] is False
    assert resp["data"]["boundary"]["agent_bus_task_writes_allowed"] is False
    assert not (vault / resp["approval"]["target_path"]).exists()
    approvals = list((vault / StudioService.APPROVAL_DIR).glob("*.json"))
    assert len(approvals) == 1
    payload = json.loads(approvals[0].read_text(encoding="utf-8"))
    assert payload["action_spec"]["metadata"]["phase"] == "phase10ac-runtime-cockpit-action-readiness"


def test_panel_registry_marks_runtime_cockpit_approval_gated() -> None:
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panel = next(item for item in registry["panels"] if item["id"] == "runtime-cockpit")

    assert registry["readiness"]["runtime_cockpit_action_readiness_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
    assert panel["read_only"] is False
    assert panel["write_mode"] == "approval_gated"
    assert "get_runtime_cockpit_action_readiness" in panel["api_methods"]
    assert "request_runtime_cockpit_action" in panel["api_methods"]
    assert panel["possible_writes"] == ["runtime_action_approval_request"]
    assert panel["blocked_authority"]["startup_mutation"] is False
    assert panel["blocked_authority"]["workflow_execution"] is False


def test_frontend_has_runtime_action_readiness_tokens() -> None:
    frontend = frontend_dir()
    html = (frontend / "index.html").read_text(encoding="utf-8")
    app = (frontend / "app.js").read_text(encoding="utf-8")
    styles = (frontend / "styles.css").read_text(encoding="utf-8")

    assert 'id="panel-runtime-cockpit"' in html
    assert 'data-write-mode="approval-gated"' in html
    assert "<h2>Agents / Runtimes</h2>" in html
    assert "Runtime health, worker posture" in html
    assert 'class="runtime-authority-row"' in html
    assert "renderRuntimeCockpitActionReadiness" in app
    assert "renderRuntimeOperatingContext" in app
    assert "renderRuntimeFeatureCoverage" in app
    assert "Runtime Feature Coverage" in app
    assert "Runtime Capability Gates" in app
    assert 'data-runtime-card="runtime"' in app
    assert "runtime-product-overview" in app
    assert "renderObjectInspectorRuntimeContext" in app
    assert "request_runtime_cockpit_action" in app
    assert "runtime-action-request-btn" in app
    assert ".runtime-context-panel" in styles
    assert ".runtime-feature-coverage" in styles
    assert ".runtime-gate-summary" in styles
    assert ".runtime-cockpit-action-card" in styles
    assert ".runtime-cockpit-action-msg" in styles
    assert ".runtime-product-overview" in styles


def test_runtime_cockpit_action_readiness_static_qa_no_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="runtime-cockpit-action-readiness",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["writes_performed"] is False
    assert report["next_recommended_pass"] == "phase10f1-open-folder-compatibility-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["runtime_cockpit_panel_approval_gated"]["ok"] is True
    assert checks["runtime_cockpit_action_readiness_present"]["ok"] is True
    assert checks["runtime_cockpit_possible_writes_approval_request_only"]["ok"] is True
    assert checks["runtime_cockpit_frontend_api_binding_present"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True



