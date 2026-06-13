"""Tests for the native Studio Runtime Cockpit panel wrapper."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.runtime_cockpit_panel import build_runtime_cockpit_panel


def test_runtime_cockpit_panel_mounts_read_only_contract(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "runtime" / "lifecycle").mkdir(parents=True)
    (vault / "runtime" / "lifecycle" / "codex.lifecycle.yaml").write_text("runtime: codex\n", encoding="utf-8")
    (vault / "runtime" / "lifecycle" / "run").mkdir()
    (vault / "runtime" / "lifecycle" / "run" / "codex-coordination-watch.json").write_text("{}", encoding="utf-8")

    panel = build_runtime_cockpit_panel(vault, probe_child_apps=False)

    assert panel["ok"] is True
    assert panel["surface"] == "studio_runtime_cockpit_panel"
    assert panel["native_panel"]["mounted"] is True
    assert panel["native_panel"]["panel_id"] == "runtime-cockpit"
    assert panel["native_panel"]["frontend_target"] == "panel-runtime-cockpit"
    assert panel["authority"]["read_only"] is False
    assert panel["authority"]["write_mode"] == "approval_gated"
    assert panel["authority"]["approval_packet_request_allowed"] is True
    assert panel["authority"]["starts_runtimes"] is False
    assert panel["authority"]["stops_runtimes"] is False
    assert panel["authority"]["restarts_runtimes"] is False
    assert panel["authority"]["executes_runtime_actions"] is False
    assert panel["authority"]["canonical_mutation_allowed"] is False
    assert panel["possible_writes"] == ["runtime_action_approval_request"]
    assert panel["allowed_actions"] == ["inspect-runtime-cockpit-panel", "request-runtime-action-approval"]
    assert panel["readiness"]["runtime_cockpit_panel_mounted"] is True
    assert panel["readiness"]["runtime_cockpit_action_readiness_ready"] is True
    assert panel["readiness"]["health_depth_visible"] is True
    assert panel["readiness"]["coordination_watch_visible"] is True
    assert panel["readiness"]["logs_visible"] is True
    assert panel["readiness"]["post_reboot_indicators_visible"] is True
    assert panel["summary"]["runtime_profile_count"] == 1
    assert panel["summary"]["coordination_watch_artifact_count"] == 1
    assert panel["summary"]["runtime_action_count"] >= 0
    assert panel["operating_context"]["title"] == "Runtime Operating Context"
    assert panel["operating_context"]["safe_action"] == "Inspect runtime health and request approval packets only."
    assert panel["feature_family_coverage"]
    assert any(item["capability"] == "Runtime profiles and worker posture" for item in panel["feature_family_coverage"])
    assert any(item["capability"] == "Runtime lifecycle and startup controls" for item in panel["feature_family_coverage"])


def test_runtime_cockpit_panel_json_serializable(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    json.dumps(build_runtime_cockpit_panel(vault, probe_child_apps=False))
