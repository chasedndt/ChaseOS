"""Pass 10A shell tests — import, structure, API contracts, no pywebview window."""
from __future__ import annotations

import json
from pathlib import Path
import hashlib
import sys
import pytest

VAULT_ROOT = Path(__file__).parents[3]


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_readonly_shell_vault(root: Path) -> None:
    files = {
        "README.md": "# Seed ChaseOS Vault\n\n[[06_AGENTS/Vault-Map|Vault Map]]\n",
        "00_HOME/Now.md": "# Now\n\n- Seeded shell no-write fixture.\n",
        "06_AGENTS/Vault-Map.md": "# Vault Map\n",
        "06_AGENTS/Agent-Registry.md": "# Agent Registry\n",
        "06_AGENTS/Trust-Tiers.md": "# Trust Tiers\n",
        "06_AGENTS/Backends-Supported.md": "# Backends Supported\n",
        "01_PROJECTS/Alpha.md": "# Alpha\n\n[[README]]\n",
    }
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


# ── config.py ─────────────────────────────────────────────────────────────
class TestConfig:
    def test_frontend_dir_exists(self):
        from runtime.studio.shell.config import frontend_dir
        assert frontend_dir().is_dir()

    def test_frontend_index_html_exists(self):
        from runtime.studio.shell.config import frontend_dir
        assert (frontend_dir() / "index.html").exists()

    def test_frontend_app_js_exists(self):
        from runtime.studio.shell.config import frontend_dir
        assert (frontend_dir() / "app.js").exists()

    def test_frontend_styles_css_exists(self):
        from runtime.studio.shell.config import frontend_dir
        assert (frontend_dir() / "styles.css").exists()

    def test_cytoscape_bundled(self):
        from runtime.studio.shell.config import frontend_dir
        cy = frontend_dir() / "assets" / "cytoscape.min.js"
        assert cy.exists()
        assert cy.stat().st_size > 100_000, "cytoscape.min.js looks too small"

    def test_studio_state_dir_created(self):
        from runtime.studio.shell.config import studio_state_dir
        d = studio_state_dir()
        assert d.is_dir()

    def test_resolve_vault_root_with_explicit_path(self):
        from runtime.studio.shell.config import resolve_vault_root
        root = resolve_vault_root(str(VAULT_ROOT))
        assert root == VAULT_ROOT.resolve()

    def test_resolve_vault_root_invalid_raises(self):
        from runtime.studio.shell.config import resolve_vault_root
        with pytest.raises((ValueError, FileNotFoundError)):
            resolve_vault_root("/nonexistent/path/that/does/not/exist")

    def test_is_dev_mode_returns_bool(self):
        from runtime.studio.shell.config import is_dev_mode
        assert isinstance(is_dev_mode(), bool)


# ── api.py ─────────────────────────────────────────────────────────────────
class TestAPIEnvelopes:
    def setup_method(self):
        from runtime.studio.shell.api import StudioAPI
        self.api = StudioAPI(str(VAULT_ROOT))

    def _check_ok(self, result):
        assert isinstance(result, dict)
        assert "ok" in result
        assert "status" in result
        assert "warnings" in result
        assert "blocked_authority" in result

    def test_get_dashboard_returns_envelope(self):
        r = self.api.get_dashboard()
        self._check_ok(r)

    def test_get_dashboard_ok_true(self):
        r = self.api.get_dashboard()
        assert r["ok"] is True

    def test_get_dashboard_surface(self):
        r = self.api.get_dashboard()
        assert r.get("surface") == "dashboard"

    def test_get_graph_contract_returns_envelope(self):
        r = self.api.get_graph_contract(max_nodes=50)
        self._check_ok(r)

    def test_get_graph_contract_ok_true(self):
        r = self.api.get_graph_contract(max_nodes=50)
        assert r["ok"] is True

    def test_get_graph_contract_has_data(self):
        r = self.api.get_graph_contract(max_nodes=50)
        assert isinstance(r.get("data"), dict)

    def test_get_graph_contract_data_has_view_model(self):
        r = self.api.get_graph_contract(max_nodes=50)
        data = r.get("data", {})
        assert "view_model" in data

    def test_get_graph_contract_nodes_list(self):
        r = self.api.get_graph_contract(max_nodes=50)
        nodes = r["data"]["view_model"].get("nodes", [])
        assert isinstance(nodes, list)

    def test_get_graph_contract_edges_list(self):
        r = self.api.get_graph_contract(max_nodes=50)
        edges = r["data"]["view_model"].get("edges", [])
        assert isinstance(edges, list)

    def test_get_graph_contract_json_serializable(self):
        r = self.api.get_graph_contract(max_nodes=20)
        json.dumps(r)  # must not raise

    def test_get_graph_contract_truncation_flag(self):
        r = self.api.get_graph_contract(max_nodes=1)
        data = r.get("data", {})
        vm = data.get("view_model", {})
        vp = vm.get("viewport", {})
        # either truncated=True or we got a single node
        assert isinstance(vp.get("visible_node_count"), int)

    def test_get_node_with_valid_id_returns_envelope(self):
        # first fetch a node id from the graph
        gr = self.api.get_graph_contract(max_nodes=5)
        nodes = gr["data"]["view_model"].get("nodes", [])
        if not nodes:
            pytest.skip("No nodes in graph")
        node_id = str(nodes[0]["id"])
        r = self.api.get_node(node_id)
        self._check_ok(r)

    def test_get_node_with_invalid_id_returns_envelope(self):
        r = self.api.get_node("chaseos:path:nonexistent000000000000000000000000000000000000000000")
        self._check_ok(r)
        # ok may be False for missing node — just must not crash

    def test_get_node_json_serializable(self):
        r = self.api.get_node("any:id:that:may:not:exist")
        json.dumps(r)

    def test_get_workspace_info_returns_envelope(self):
        r = self.api.get_workspace_info()
        self._check_ok(r)

    def test_get_workspace_info_ok(self):
        r = self.api.get_workspace_info()
        assert r["ok"] is True

    def test_get_workspace_entry_panel_returns_read_only_envelope(self):
        r = self.api.get_workspace_entry_panel()
        self._check_ok(r)
        assert r["surface"] == "workspace_entry_panel"
        assert r["data"]["native_panel"]["mounted"] is True
        assert r["data"]["native_panel"]["panel_id"] == "workspace-entry"
        assert r["data"]["authority"]["read_only"] is True
        assert r["data"]["workspace_entry"]["workspace_upgrade_writer_built"] is False
        assert r["data"]["workspace_entry"]["migration_writer_built"] is False
        assert r["data"]["authority"]["canonical_mutation_allowed"] is False

    def test_get_settings_runtime_controls_panel_returns_operator_control_envelope(self):
        r = self.api.get_settings_runtime_controls_panel()
        self._check_ok(r)
        assert r["surface"] == "settings_runtime_controls_panel"
        assert r["data"]["native_panel"]["mounted"] is True
        assert r["data"]["native_panel"]["panel_id"] == "settings"
        assert r["data"]["authority"]["read_only"] is False
        assert r["data"]["authority"]["writes_config"] is False
        assert r["data"]["authority"]["writes_host_startup"] is True
        assert r["data"]["authority"]["executes_runtime_actions"] is True
        assert r["data"]["authority"]["canonical_mutation_allowed"] is False
        assert r["data"]["runtime_status"]["gateway_controls"]["authority"]["starts_gateways"] is True
        assert r["data"]["provider_readiness"]["summary"]["readiness_status"]
        assert r["data"]["provider_readiness"]["authority"]["provider_switch_allowed"] is False
        assert r["data"]["provider_readiness"]["live_probe_readiness"]["studio_executes_live_probe"] is False
        assert r["data"]["action_posture"]["native_ui_action_buttons_enabled"] is True
        assert r["data"]["security"]["secret_values_included"] is False

    def test_get_config_summary_has_vault_root(self):
        r = self.api.get_config_summary()
        assert r["ok"] is True
        assert "vault_root" in r["data"]

    def test_get_config_summary_json_serializable(self):
        r = self.api.get_config_summary()
        json.dumps(r)

    def test_get_schedule_summary_returns_envelope(self):
        r = self.api.get_schedule_summary()
        self._check_ok(r)

    def test_get_pulse_summary_returns_envelope(self):
        r = self.api.get_pulse_summary()
        self._check_ok(r)

    def test_get_siteops_summary_returns_envelope(self):
        r = self.api.get_siteops_summary()
        self._check_ok(r)

    def test_get_aor_summary_returns_envelope(self):
        r = self.api.get_aor_summary()
        self._check_ok(r)

    def test_get_sic_workspaces_returns_envelope(self):
        r = self.api.get_sic_workspaces()
        self._check_ok(r)

    def test_get_approval_queue_returns_envelope(self):
        r = self.api.get_approval_queue()
        self._check_ok(r)

    def test_get_approval_center_panel_returns_read_only_envelope(self):
        r = self.api.get_approval_center_panel()
        self._check_ok(r)
        assert r["surface"] == "approval_center_panel"
        assert r["data"]["native_panel"]["mounted"] is True
        assert r["data"]["native_panel"]["panel_id"] == "approval-center"
        assert r["data"]["authority"]["read_only"] is True
        assert r["data"]["authority"]["grants_approvals"] is False
        assert r["data"]["authority"]["executes_approvals"] is False
        assert r["data"]["authority"]["consumes_approval_decisions"] is False
        assert r["data"]["authority"]["resumes_runtimes"] is False
        assert r["data"]["authority"]["canonical_mutation_allowed"] is False

    def test_get_runtime_cockpit_panel_returns_approval_gated_envelope(self):
        r = self.api.get_runtime_cockpit_panel()
        self._check_ok(r)
        assert r["surface"] == "runtime_cockpit_panel"
        assert r["data"]["native_panel"]["mounted"] is True
        assert r["data"]["native_panel"]["panel_id"] == "runtime-cockpit"
        assert r["data"]["authority"]["read_only"] is False
        assert r["data"]["authority"]["write_mode"] == "approval_gated"
        assert r["data"]["authority"]["approval_packet_request_allowed"] is True
        assert r["data"]["authority"]["starts_runtimes"] is False
        assert r["data"]["authority"]["stops_runtimes"] is False
        assert r["data"]["authority"]["restarts_runtimes"] is False
        assert r["data"]["authority"]["executes_runtime_actions"] is False
        assert r["data"]["authority"]["canonical_mutation_allowed"] is False
        assert r["data"]["possible_writes"] == ["runtime_action_approval_request"]
        assert r["data"]["readiness"]["health_depth_visible"] is True
        assert r["data"]["readiness"]["logs_visible"] is True
        assert r["data"]["readiness"]["runtime_cockpit_action_readiness_ready"] is True

    def test_get_runtime_intelligence_panels_return_read_only_envelopes(self):
        cases = [
            (self.api.get_provenance_explorer_panel(), "provenance_explorer_panel", "provenance-explorer"),
            (self.api.get_memory_ledger_panel(), "memory_ledger_panel", "memory-ledger"),
            (self.api.get_agent_identity_panel(), "agent_identity_panel", "agent-identity"),
            (self.api.get_runtime_navigation_map_panel(), "runtime_navigation_map_panel", "runtime-navigation"),
        ]
        for r, surface, panel_id in cases:
            self._check_ok(r)
            assert r["surface"] == surface
            assert r["data"]["native_panel"]["mounted"] is True
            assert r["data"]["native_panel"]["panel_id"] == panel_id
            assert r["data"]["native_panel"]["read_only"] is True
            assert r["data"]["authority"]["read_only"] is True
            assert r["data"]["authority"]["writes_memory"] is False
            assert r["data"]["authority"]["writes_agent_bus_tasks"] is False
            assert r["data"]["authority"]["provider_calls_allowed"] is False
            assert r["data"]["authority"]["connector_calls_allowed"] is False
            assert r["data"]["authority"]["canonical_mutation_allowed"] is False
            assert r["data"]["possible_writes"] == []

    def test_get_panel_registry_returns_envelope(self):
        r = self.api.get_panel_registry()
        self._check_ok(r)
        assert r["surface"] == "native_shell_panel_registry"
        assert r["data"]["readiness"]["native_shell_panel_registry_ready"] is True

    def test_get_browser_runtime_panel_returns_read_only_envelope(self):
        r = self.api.get_browser_runtime_panel()
        self._check_ok(r)
        assert r["surface"] == "browser_runtime_panel"
        assert r["data"]["native_panel"]["mounted"] is True
        assert r["data"]["authority"]["read_only"] is True
        assert r["data"]["authority"]["launches_browser"] is False
        assert r["data"]["authority"]["connects_cdp"] is False
        assert r["data"]["authority"]["runs_browser_use_cli_live"] is False
        assert r["data"]["authority"]["canonical_mutation_allowed"] is False

    def test_get_provenance_returns_read_only_envelope(self):
        r = self.api.get_provenance("README.md")
        self._check_ok(r)
        assert r["surface"] == "provenance"
        assert r["data"]["boundary"]["writes_vault"] is False
        assert r["data"]["boundary"]["canonical_mutation_allowed"] is False


class TestNativePanelRegistry:
    def test_registry_shape_and_mounts(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT_ROOT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        assert registry["model_version"] == "studio.native_shell.panel_registry.v1"
        assert registry["readiness"]["native_shell_primary"] is True
        assert registry["readiness"]["legacy_localhost_harness_primary"] is False
        assert panels["graph"]["status"] == "mounted"
        assert panels["node-inspector"]["mount_kind"] in {"side_panel", "main_panel"}  # upgraded to main_panel in Phase E
        assert panels["dashboard"]["frontend_target"] == "panel-dashboard"
        assert panels["browser-runtime"]["status"] == "mounted"
        assert panels["browser-runtime"]["frontend_target"] == "panel-browser-runtime"
        assert panels["workspace-entry"]["status"] == "mounted"
        assert panels["workspace-entry"]["frontend_target"] == "panel-workspace-entry"
        assert panels["settings"]["status"] == "mounted"
        assert panels["settings"]["frontend_target"] == "panel-settings"
        assert panels["approval-center"]["status"] == "mounted"
        assert panels["approval-center"]["frontend_target"] == "panel-approval-center"
        assert panels["runtime-cockpit"]["status"] == "mounted"
        assert panels["runtime-cockpit"]["frontend_target"] == "panel-runtime-cockpit"
        assert panels["provenance-explorer"]["status"] == "mounted"
        assert panels["provenance-explorer"]["frontend_target"] == "panel-provenance-explorer"
        assert panels["memory-ledger"]["status"] == "mounted"
        assert panels["memory-ledger"]["frontend_target"] == "panel-memory-ledger"
        assert panels["agent-identity"]["status"] == "mounted"
        assert panels["agent-identity"]["frontend_target"] == "panel-agent-identity"
        assert panels["runtime-navigation"]["status"] == "mounted"
        assert panels["runtime-navigation"]["frontend_target"] == "panel-runtime-navigation"
        assert panels["project-workspace"]["status"] == "mounted"
        assert panels["project-workspace"]["frontend_target"] == "panel-project-workspace"
        assert panels["intake"]["status"] == "mounted"
        assert panels["intake"]["frontend_target"] == "panel-intake"
        assert panels["sic"]["status"] == "mounted"
        assert panels["sic"]["frontend_target"] == "panel-sic"
        assert panels["aor"]["status"] == "mounted"
        assert panels["aor"]["frontend_target"] == "panel-aor"
        assert panels["schedules"]["status"] == "mounted"
        assert panels["schedules"]["frontend_target"] == "panel-schedules"
        assert panels["siteops"]["status"] == "mounted"
        assert panels["siteops"]["frontend_target"] == "panel-siteops"
        assert panels["acquisition"]["status"] == "mounted"
        assert panels["acquisition"]["frontend_target"] == "panel-acquisition"
        assert panels["bus"]["status"] == "mounted"
        assert panels["bus"]["frontend_target"] == "panel-bus"
        assert registry["readiness"]["browser_runtime_panel_mounted"] is True
        assert registry["readiness"]["workspace_entry_panel_mounted"] is True
        assert registry["readiness"]["settings_governed_panel_mounted"] is True
        assert registry["readiness"]["approval_center_mounted"] is True
        assert registry["readiness"]["runtime_cockpit_mounted"] is True
        assert registry["readiness"]["provenance_explorer_mounted"] is True
        assert registry["readiness"]["memory_ledger_mounted"] is True
        assert registry["readiness"]["agent_identity_mounted"] is True
        assert registry["readiness"]["runtime_navigation_mounted"] is True
        assert registry["readiness"]["runtime_intelligence_panels_mounted"] is True
        assert registry["readiness"]["project_workspace_panel_mounted"] is True
        assert registry["readiness"]["intake_panel_mounted"] is True
        assert registry["readiness"]["sic_panel_mounted"] is True
        assert registry["readiness"]["aor_panel_mounted"] is True
        assert registry["readiness"]["schedules_panel_mounted"] is True
        assert registry["readiness"]["siteops_panel_mounted"] is True
        assert registry["readiness"]["acquisition_panel_mounted"] is True
        assert registry["readiness"]["bus_diagnostics_panel_mounted"] is True
        assert registry["readiness"]["graph_filter_bar_mounted"] is True

    def test_registry_is_read_only_and_blocks_authority(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT_ROOT)
        assert registry["authority"]["read_only_registry"] is True
        assert registry["authority"]["possible_writes"] == []
        assert registry["readiness"]["all_declared_panels_safe_or_approval_gated"] is True
        assert registry["readiness"]["direct_write_authority_blocked"] is True
        _safe_write_modes = {"approval_gated", "operator_control"}
        for panel in registry["panels"]:
            # Every panel must be read-only OR use a safe gated write mode
            assert panel["read_only"] is True or panel.get("write_mode") in _safe_write_modes, (
                f"Panel {panel['id']} has read_only={panel['read_only']} "
                f"and write_mode={panel.get('write_mode')!r}"
            )
            # Non-read-only panels: verify write-mode contract
            if not panel["read_only"]:
                assert panel.get("write_mode") in _safe_write_modes
                if panel["write_mode"] == "approval_gated":
                    assert panel["possible_writes"], (
                        f"approval_gated panel {panel['id']} must declare possible_writes"
                    )
            # Spot-check: key panels that must specifically be approval_gated
            if panel["id"] in {"graph", "node-inspector", "runtime-cockpit", "graph-hygiene"}:
                assert panel["write_mode"] == "approval_gated"
                assert panel["possible_writes"]
            # settings must use operator_control (daemon/gateway, capture shortcuts)
            if panel["id"] == "settings":
                assert panel["write_mode"] == "operator_control"
            blocked = panel["blocked_authority"]
            assert blocked["vault_source_file_writes"] is False
            assert blocked["graph_index_writes"] is False
            assert blocked["node_id_writes"] is False
            assert blocked["node_editing"] is False
            assert blocked["provider_calls"] is False
            assert blocked["connector_calls"] is False
            assert blocked["workflow_execution"] is False
            assert blocked["canonical_mutation"] is False

    def test_registry_json_serializable(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        json.dumps(build_native_shell_panel_registry(VAULT_ROOT))


class TestAPIWriteBlocked:
    """Baseline shell tests keep the real vault static/read-only.

    Pass 10C owns governed write-surface behavior in isolated tests. These 10A
    checks must not invoke live write APIs against the repository vault.
    """

    def setup_method(self):
        from runtime.studio.shell.api import StudioAPI
        self.api = StudioAPI(str(VAULT_ROOT))

    def test_write_surface_methods_exist_for_10c_governed_path(self):
        assert callable(self.api.preview_create_node)
        assert callable(self.api.create_node)
        assert callable(self.api.create_link)
        assert callable(self.api.submit_approval)
        assert callable(self.api.promote_from_quarantine)
        assert callable(self.api.get_node_metadata_edit_model)
        assert callable(self.api.update_node_metadata)

    def test_no_vault_writes(self, tmp_path):
        vault_root = tmp_path
        _seed_readonly_shell_vault(vault_root)
        before = {
            str(p): _file_digest(p)
            for p in vault_root.rglob("*.md")
            if not any(part.startswith(".") for part in p.parts)
            and not any(part.startswith("_tmp") for part in p.parts)
            and "07_LOGS" not in p.parts
            and "99_ARCHIVE" not in p.parts
            and len(list(p.parts)) < 20  # avoid deep paths
        }
        approval_root = vault_root / "runtime" / "studio" / "approvals"
        before_approvals = {
            str(p): _file_digest(p)
            for p in approval_root.glob("*.json")
        } if approval_root.is_dir() else {}
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(vault_root))
        api.get_dashboard()
        api.get_panel_registry()
        api.get_browser_runtime_panel()
        api.get_workspace_entry_panel()
        api.get_settings_runtime_controls_panel()
        api.get_approval_center_panel()
        api.get_runtime_cockpit_panel()
        api.get_provenance_explorer_panel()
        api.get_memory_ledger_panel()
        api.get_agent_identity_panel()
        api.get_runtime_navigation_map_panel()
        api.get_graph_contract(max_nodes=20)
        api.get_workspace_info()
        api.get_provenance("README.md")
        after = {
            str(p): _file_digest(p)
            for p in vault_root.rglob("*.md")
            if not any(part.startswith(".") for part in p.parts)
            and not any(part.startswith("_tmp") for part in p.parts)
            and "07_LOGS" not in p.parts
            and "99_ARCHIVE" not in p.parts
            and len(list(p.parts)) < 20
        }
        after_approvals = {
            str(p): _file_digest(p)
            for p in approval_root.glob("*.json")
        } if approval_root.is_dir() else {}
        new_files = set(after) - set(before)
        assert not new_files, f"Write operations created files: {new_files}"
        assert before == after
        assert before_approvals == after_approvals


# ── main.py ────────────────────────────────────────────────────────────────
class TestMainModule:
    def test_main_importable(self):
        import runtime.studio.shell.main  # noqa: F401

    def test_main_has_main_function(self):
        from runtime.studio.shell import main as m
        assert callable(m.main)

    def test_qa_window_dimension_is_bounded(self, monkeypatch):
        from runtime.studio.shell import main as m

        monkeypatch.setenv(m.QA_WINDOW_WIDTH_ENV, "1000")
        assert m._qa_window_dimension(m.QA_WINDOW_WIDTH_ENV, default=1400, minimum=900, maximum=2400) == 1000

        monkeypatch.setenv(m.QA_WINDOW_WIDTH_ENV, "10")
        assert m._qa_window_dimension(m.QA_WINDOW_WIDTH_ENV, default=1400, minimum=900, maximum=2400) == 900

        monkeypatch.setenv(m.QA_WINDOW_WIDTH_ENV, "9999")
        assert m._qa_window_dimension(m.QA_WINDOW_WIDTH_ENV, default=1400, minimum=900, maximum=2400) == 2400

        monkeypatch.setenv(m.QA_WINDOW_WIDTH_ENV, "not-a-size")
        assert m._qa_window_dimension(m.QA_WINDOW_WIDTH_ENV, default=1400, minimum=900, maximum=2400) == 1400


# ── Frontend files ──────────────────────────────────────────────────────────
class TestFrontendFiles:
    def setup_method(self):
        from runtime.studio.shell.config import frontend_dir
        self.frontend = frontend_dir()

    def test_index_html_has_cy_div(self):
        # Phase 2 replaced Cytoscape 2D (id="cy") with 3d-force-graph (id="graph-3d")
        html = (self.frontend / "index.html").read_text(encoding="utf-8")
        assert 'id="graph-3d"' in html

    def test_index_html_has_inspector(self):
        html = (self.frontend / "index.html").read_text(encoding="utf-8")
        assert 'id="inspector"' in html

    def test_index_html_has_native_panel_registry_markers(self):
        html = (self.frontend / "index.html").read_text(encoding="utf-8")
        assert 'data-panel-registry="native-shell-v1"' in html
        assert 'data-panel-id="graph"' in html
        assert 'data-panel-id="node-inspector"' in html
        assert 'data-panel-id="dashboard"' in html
        assert 'data-panel-id="browser-runtime"' in html
        assert 'data-panel-id="workspace-entry"' in html
        assert 'data-panel-id="settings"' in html
        assert 'data-panel-id="approval-center"' in html
        assert 'data-panel-id="runtime-cockpit"' in html
        assert 'data-panel-id="provenance-explorer"' in html
        assert 'data-panel-id="memory-ledger"' in html
        assert 'data-panel-id="agent-identity"' in html
        assert 'data-panel-id="runtime-navigation"' in html
        assert 'id="panel-browser-runtime"' in html
        assert 'id="browser-runtime-body"' in html
        assert 'id="panel-workspace-entry"' in html
        assert 'id="workspace-entry-body"' in html
        assert 'id="panel-settings"' in html
        assert 'id="settings-runtime-body"' in html
        assert 'id="panel-approval-center"' in html
        assert 'id="approval-center-body"' in html
        assert 'id="panel-runtime-cockpit"' in html
        assert 'id="runtime-cockpit-body"' in html
        assert 'id="panel-provenance-explorer"' in html
        assert 'id="provenance-explorer-body"' in html
        assert 'id="panel-memory-ledger"' in html
        assert 'id="memory-ledger-body"' in html
        assert 'id="panel-agent-identity"' in html
        assert 'id="agent-identity-body"' in html
        assert 'id="panel-runtime-navigation"' in html
        assert 'id="runtime-navigation-body"' in html
        assert 'data-read-only="true"' in html
        assert 'id="panel-registry-status"' in html

    def test_index_html_has_graph_filter_panel(self):
        html = (self.frontend / "index.html").read_text(encoding="utf-8")
        assert 'id="graph-filter-panel"' in html
        assert 'id="node-type-filters"' in html
        assert 'id="trust-state-filters"' in html
        assert 'id="domain-filters"' in html
        assert 'id="relation-filters"' in html

    def test_index_html_loads_cytoscape_from_assets(self):
        # Phase 2 replaced Cytoscape 2D with 3d-force-graph (Three.js WebGL)
        html = (self.frontend / "index.html").read_text(encoding="utf-8")
        assert "assets/3d-force-graph.min.js" in html
        # Must NOT load from CDN
        assert "cdnjs.cloudflare" not in html
        assert "unpkg.com" not in html
        assert "jsdelivr.net" not in html

    def test_index_html_loads_app_js(self):
        html = (self.frontend / "index.html").read_text(encoding="utf-8")
        assert "app.js" in html

    def test_index_html_loads_styles_css(self):
        html = (self.frontend / "index.html").read_text(encoding="utf-8")
        assert "styles.css" in html

    def test_app_js_calls_get_graph_contract(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        assert "get_graph_contract" in js

    def test_app_js_calls_get_node(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        assert "get_node" in js

    def test_app_js_calls_get_panel_registry(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        assert "get_panel_registry" in js
        assert "loadPanelRegistry" in js
        assert "all_declared_panels_safe_or_approval_gated" in js

    def test_app_js_mounts_browser_runtime_panel(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "get_browser_runtime_panel",
            "loadBrowserRuntime",
            "renderBrowserRuntimePanel",
            "browserRuntimeLoaded",
            "runs_browser_use_cli_live",
            "Canonical mutation",
        ]:
            assert token in js

    def test_app_js_mounts_workspace_entry_panel(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "get_workspace_entry_panel",
            "loadWorkspaceEntry",
            "renderWorkspaceEntryPanel",
            "workspaceEntryLoaded",
            "renderWorkspaceEntryHome",
            "handleOpenDifferentFolder",
            "renderFolderScanResult",
            "handleBootstrapWizard",
            "renderBootstrapWizard",
        ]:
            assert token in js, f"missing token: {token}"

    def test_app_js_mounts_settings_runtime_controls_panel(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "get_settings_runtime_controls_panel",
            "loadSettingsRuntimeControls",
            "renderSettingsRuntimeControlsPanel",
            "settings-capture-hotkeys",
            "save_capture_hotkey_settings",
            "get_capture_hotkey_settings",
            "settingsLoaded",
            "native_ui_action_buttons_enabled",
            "Provider Readiness",
            "provider_switch_allowed",
            "studio_executes_live_probe",
            "Canonical mutation",
        ]:
            assert token in js

    def test_app_js_mounts_approval_center_panel(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "get_approval_center_panel",
            "loadApprovalCenter",
            "renderApprovalCenterPanel",
            "approvalCenterLoaded",
            "consumes_approval_decisions",
            "Canonical mutation",
        ]:
            assert token in js

    def test_app_js_mounts_runtime_cockpit_panel(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "get_runtime_cockpit_panel",
            "loadRuntimeCockpit",
            "renderRuntimeCockpitPanel",
            "runtimeCockpitLoaded",
            "executes_runtime_actions",
            "Canonical mutation",
        ]:
            assert token in js

    def test_app_js_mounts_runtime_intelligence_panels(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "get_provenance_explorer_panel",
            "loadProvenanceExplorer",
            "renderProvenanceExplorerPanel",
            "provenanceExplorerLoaded",
            "get_memory_ledger_panel",
            "loadMemoryLedger",
            "renderMemoryLedgerPanel",
            "memoryLedgerLoaded",
            "get_agent_identity_panel",
            "loadAgentIdentity",
            "renderAgentIdentityPanel",
            "agentIdentityLoaded",
            "get_runtime_navigation_map_panel",
            "loadRuntimeNavigation",
            "renderRuntimeNavigationPanel",
            "runtimeNavigationLoaded",
            "approves_memory",
            "updates_trust_tiers",
            "writes_runtime_navigation_map",
            "Canonical mutation",
        ]:
            assert token in js

    def test_inspector_tabs_has_provenance_hydration(self):
        js = (self.frontend / "inspectorTabs.js").read_text(encoding="utf-8")
        for token in [
            "get_provenance",
            "_hydrateProvenance",
            "selected_node",
            "source_excerpt",
            "Derived Graph Provenance",
            "Sidecar Provenance",
            "Dedup Status",
        ]:
            assert token in js

    def test_app_js_has_pass10b_graph_visual_mappings(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "NODE_TYPE_FAMILIES",
            "EDGE_STYLE_FAMILIES",
            "nodeShape",
            "edgeStyleFamily",
            "underlay-color",
        ]:
            assert token in js

    def test_app_js_has_ui_local_graph_filters(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        for token in [
            "renderGraphControls",
            "renderFilterGroup",
            "applyGraphFilters",
            "graphFilters",
            "data-filter-kind",
            "domain-filters",
            "inferNodeDomain",
        ]:
            assert token in js

    def test_app_js_pywebview_api(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        assert "pywebview.api" in js

    def test_styles_css_trust_colors_defined(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for ts in ["ts-raw", "ts-quarantined", "ts-promoted", "ts-canonical", "ts-generated"]:
            assert ts in css, f"Trust state {ts} not in styles.css"

    def test_styles_css_has_filter_and_legend_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in ["#graph-filter-panel", ".graph-filter-bar", ".filter-option", "#graph-legend", ".legend-line"]:
            assert token in css

    def test_styles_css_has_panel_registry_status(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        assert ".panel-registry-status" in css

    def test_styles_css_has_browser_runtime_panel_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in [
            "#panel-browser-runtime",
            ".browser-runtime-summary",
            ".browser-runtime-section",
            ".browser-runtime-list-item",
            ".browser-runtime-next",
        ]:
            assert token in css

    def test_styles_css_has_workspace_entry_panel_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in [
            "#panel-workspace-entry",
            ".workspace-entry-summary",
            ".workspace-entry-section",
            ".workspace-entry-list-item",
            ".workspace-entry-next",
        ]:
            assert token in css

    def test_styles_css_has_settings_runtime_controls_panel_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in [
            "#panel-settings",
            ".studio-settings-summary",
            ".studio-settings-section",
            ".studio-settings-list-item",
            ".studio-settings-next",
            ".capture-hotkey-row",
            ".capture-hotkey-input",
        ]:
            assert token in css

    def test_styles_css_has_approval_center_panel_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in [
            "#panel-approval-center",
            ".approval-center-summary",
            ".approval-center-section",
            ".approval-center-list-item",
            ".approval-center-next",
        ]:
            assert token in css

    def test_styles_css_has_runtime_cockpit_panel_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in [
            "#panel-runtime-cockpit",
            ".runtime-cockpit-summary",
            ".runtime-cockpit-section",
            ".runtime-cockpit-list-item",
            ".runtime-cockpit-next",
        ]:
            assert token in css

    def test_styles_css_has_runtime_intelligence_panel_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in [
            "#panel-provenance-explorer",
            "#panel-memory-ledger",
            "#panel-agent-identity",
            "#panel-runtime-navigation",
            ".runtime-intelligence-panel",
            ".runtime-intel-summary",
            ".runtime-intel-section",
            ".runtime-intel-row",
            ".runtime-intel-list-item",
            ".runtime-intel-next",
        ]:
            assert token in css

    def test_styles_css_has_inspector_tab_layout(self):
        css = (self.frontend / "styles.css").read_text(encoding="utf-8")
        for token in [
            ".inspector-tab-btn",
            ".inspector-section",
            ".inspector-row",
            ".inspector-provenance-status",
        ]:
            assert token in css

    def test_app_js_no_cdn_urls(self):
        js = (self.frontend / "app.js").read_text(encoding="utf-8")
        assert "cdnjs" not in js
        assert "unpkg" not in js
        assert "jsdelivr" not in js


class TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell:
    def test_api_returns_source_recovery_cleanup_proof_envelope(self):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_source_recovery_cleanup_proof()

        assert result["ok"] is True
        assert result["surface"] == "launcher_update_source_recovery_cleanup_proof"
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_source_recovery_cleanup_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_source_recovery_cleanup_pinned_but_source_wrapped"
        )
        assert result["data"]["recovery_artifacts_pinned"] is True
        assert result["data"]["normal_source_restored"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True

    def test_api_returns_normal_source_restoration_readiness_envelope(self):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_normal_source_restoration_readiness()

        assert result["ok"] is True
        assert result["surface"] == "launcher_update_normal_source_restoration_readiness"
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_normal_source_restoration_readiness"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_normal_source_restoration_readiness_blocked"
        )
        assert result["data"]["normal_source_restoration_ready"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert "normal_source_wrappers_still_active" in result["data"]["errors"]

    def test_api_returns_normal_source_candidate_verification_proof_envelope(self):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_normal_source_candidate_verification_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_normal_source_candidate_verification_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_normal_source_candidate_verification_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_normal_source_candidate_verification_blocked"
        )
        assert result["data"]["source_replacement_performed"] is False
        assert result["data"]["normal_source_restoration_ready"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert (
            "operator_candidate_verification_approval_required"
            in result["data"]["errors"]
        )

    def test_api_returns_normal_source_candidate_restore_executor_proof_envelope(self):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_normal_source_candidate_restore_executor_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_normal_source_candidate_restore_executor_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_normal_source_candidate_restore_executor_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_normal_source_candidate_restore_executor_blocked"
        )
        assert result["data"]["source_restore_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert "candidate_verification_proof_required" in result["data"]["errors"]
        assert "operator_source_restore_approval_required" in result["data"]["errors"]

    def test_api_returns_source_regeneration_readiness_envelope(self):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_source_regeneration_readiness()

        assert result["ok"] is True
        assert result["surface"] == "launcher_update_source_regeneration_readiness"
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_source_regeneration_readiness"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_source_regeneration_readiness_blocked"
        )
        assert result["data"]["bytecode_artifacts_ready"] is True
        assert result["data"]["source_regeneration_execution_performed"] is False
        assert result["data"]["source_regeneration_output_written"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["decompiler_execution_performed"] is False
        assert result["data"]["candidate_source_execution_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True

    def test_api_returns_source_regeneration_runner_boundary_envelope(self):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_source_regeneration_runner_boundary_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_source_regeneration_runner_boundary_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_source_regeneration_runner_boundary_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_source_regeneration_runner_boundary_blocked"
        )
        assert result["data"]["runner_execution_performed"] is False
        assert result["data"]["source_regeneration_output_written"] is False
        assert result["data"]["live_source_write_performed"] is False
        assert result["data"]["source_restore_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert "candidate_output_root_required" in result["data"]["errors"]
        assert "source_regeneration_runner_required" in result["data"]["errors"]

    def test_api_returns_source_regeneration_candidate_verification_restore_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = (
            api.get_launcher_update_source_regeneration_candidate_verification_restore_proof()
        )

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_source_regeneration_candidate_verification_restore_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_source_regeneration_candidate_verification_restore_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_source_regeneration_candidate_restore_blocked"
        )
        assert result["data"]["runner_candidates_written"] is False
        assert result["data"]["candidate_verification_ready"] is False
        assert result["data"]["source_regeneration_execution_performed"] is False
        assert result["data"]["source_restore_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["live_source_write_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert "source_regeneration_runner_candidates_required" in result["data"]["errors"]

    def test_api_returns_source_regeneration_live_source_restoration_closeout_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = (
            api.get_launcher_update_source_regeneration_live_source_restoration_closeout_proof()
        )

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_source_regeneration_live_source_restoration_closeout_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_source_regeneration_live_source_restoration_closeout_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_source_regeneration_live_source_restoration_closeout_blocked"
        )
        assert result["data"]["live_restore_proof_ready"] is False
        assert result["data"]["wrapper_removal_verified"] is False
        assert result["data"]["live_source_restoration_verified"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["live_source_write_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert (
            "source_regeneration_candidate_restore_proof_not_live"
            in result["data"]["errors"]
        )

    def test_api_returns_real_source_restoration_execution_regression_boundary_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = (
            api.get_launcher_update_real_source_restoration_execution_regression_boundary_proof()
        )

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_real_source_restoration_execution_regression_boundary_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_real_source_restoration_execution_regression_boundary_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_real_source_restoration_execution_regression_boundary_blocked"
        )
        assert result["data"]["real_source_restore_performed"] is False
        assert result["data"]["live_source_restoration_closeout_verified"] is False
        assert result["data"]["regression_evidence_verified"] is False
        assert result["data"]["regression_commands_executed_by_chaseos"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert "real_source_restore_evidence_required" in result["data"]["errors"]

    def test_api_returns_current_vault_source_restoration_closeout_readiness_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_current_vault_source_restoration_closeout_readiness()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_current_vault_source_restoration_closeout_readiness"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_current_vault_source_restoration_closeout_readiness"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_current_vault_source_restoration_closeout_blocked"
        )
        assert (
            result["data"]["real_source_restoration_regression_boundary_verified"]
            is False
        )
        assert result["data"]["source_recovery_cleanup_ready"] is False
        assert result["data"]["current_vault_wrappers_removed"] is False
        assert (
            result["data"]["source_restoration_closeout_ready_for_primary_exe_resume"]
            is False
        )
        assert result["data"]["regression_commands_executed_by_chaseos"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert (
            "real_source_restoration_regression_boundary_not_verified"
            in result["data"]["errors"]
        )

    def test_api_returns_source_candidate_inventory_wrapper_removal_preflight_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_source_candidate_inventory_wrapper_removal_preflight()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_source_candidate_inventory_wrapper_removal_preflight"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_source_candidate_inventory_wrapper_removal_preflight"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_source_candidate_inventory_authoritative_candidates_missing"
        )
        assert result["data"]["current_vault_wrappers_active"] is True
        assert result["data"]["authoritative_source_candidates_available"] is False
        assert result["data"]["wrapper_removal_plan_ready"] is False
        assert result["data"]["decompiler_execution_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert (
            "launcher_update_check_authoritative_source_candidate_missing"
            in result["data"]["errors"]
        )

    def test_api_returns_authoritative_normal_source_candidate_supply_packet_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_authoritative_normal_source_candidate_supply_packet()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_authoritative_normal_source_candidate_supply_packet"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_authoritative_normal_source_candidate_supply_packet"
        )
        assert result["data"]["status"] == (
            "launcher_update_authoritative_normal_source_candidate_supply_blocked"
        )
        assert result["data"]["candidate_supply_packet_ready"] is False
        assert result["data"]["ready_for_candidate_verifier"] is False
        assert result["data"]["authoritative_source_candidates_available"] is False
        assert result["data"]["current_vault_wrappers_active"] is True
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "authoritative_normal_source_candidates_missing"
            in result["data"]["errors"]
        )

    def test_api_returns_authoritative_source_candidate_import_boundary_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_authoritative_source_candidate_import_boundary_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_authoritative_source_candidate_import_boundary_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_authoritative_source_candidate_import_boundary_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_authoritative_source_candidate_import_blocked"
        )
        assert result["data"]["candidate_import_plan_ready"] is False
        assert result["data"]["candidate_import_write_enabled"] is False
        assert result["data"]["candidate_import_write_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "operator_authoritative_source_candidate_import_approval_required"
            in result["data"]["errors"]
        )

    def test_api_returns_real_authoritative_source_candidate_supply_readiness_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_real_authoritative_source_candidate_supply_readiness()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_real_authoritative_source_candidate_supply_readiness"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_real_authoritative_source_candidate_supply_readiness"
        )
        assert result["data"]["status"] == (
            "launcher_update_real_authoritative_source_candidate_supply_blocked"
        )
        assert result["data"]["real_authoritative_source_candidates_available"] is False
        assert result["data"]["ready_for_authoritative_import_boundary"] is False
        assert result["data"]["candidate_import_plan_ready"] is False
        assert result["data"]["candidate_import_write_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "real_authoritative_source_candidates_missing"
            in result["data"]["errors"]
        )

    def test_api_returns_real_authoritative_source_candidate_materialization_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = (
            api.get_launcher_update_real_authoritative_source_candidate_materialization_proof()
        )

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_real_authoritative_source_candidate_materialization_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_real_authoritative_source_candidate_materialization_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_real_authoritative_source_candidate_materialization_blocked"
        )
        assert result["data"]["materialization_plan_ready"] is False
        assert result["data"]["source_materializer_execution_performed"] is False
        assert result["data"]["candidate_materialization_write_performed"] is False
        assert result["data"]["candidate_import_write_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["decompiler_execution_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert "source_materializer_required" in result["data"]["errors"]

    def test_api_returns_real_authoritative_source_candidate_import_from_materialization_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = (
            api.get_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof()
        )

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_real_authoritative_source_candidate_import_from_materialization_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_real_authoritative_source_candidate_import_from_materialization_blocked"
        )
        assert result["data"]["import_from_materialization_plan_ready"] is False
        assert result["data"]["materialization_ready_for_import_boundary"] is False
        assert result["data"]["candidate_import_write_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["decompiler_execution_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "real_authoritative_source_candidate_materialization_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_real_authoritative_source_candidate_supply_verification_from_materialization_import_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = (
            api.get_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof()
        )

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_blocked"
        )
        assert (
            result["data"][
                "supply_verification_from_materialization_import_plan_ready"
            ]
            is False
        )
        assert (
            result["data"][
                "import_from_materialization_ready_for_supply_verification"
            ]
            is False
        )
        assert result["data"]["ready_for_wrapper_removal_executor"] is False
        assert result["data"]["candidate_import_write_performed"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["decompiler_execution_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "real_authoritative_source_candidate_import_from_materialization_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_current_vault_wrapper_removal_from_materialization_import_execution_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_blocked"
        )
        assert (
            result["data"]["supply_verification_from_materialization_import_ready"]
            is False
        )
        assert (
            result["data"][
                "wrapper_removal_from_materialization_import_execution_plan_ready"
            ]
            is False
        )
        assert result["data"]["restore_plan_ready"] is False
        assert result["data"]["current_vault_source_write_enabled"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "real_authoritative_source_candidate_supply_verification_from_materialization_import_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_post_wrapper_removal_regression_from_materialization_import_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_post_wrapper_removal_regression_from_materialization_import_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_post_wrapper_removal_regression_from_materialization_import_blocked"
        )
        assert (
            result["data"]["wrapper_removal_from_materialization_import_verified"]
            is False
        )
        assert result["data"]["regression_command_plan_ready"] is True
        assert result["data"]["regression_evidence_required"] is False
        assert result["data"]["regression_evidence_verified"] is False
        assert result["data"]["regression_commands_executed_by_chaseos"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "current_vault_wrapper_removal_from_materialization_import_execution_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_current_vault_source_closeout_from_materialization_import_regression_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_current_vault_source_closeout_from_materialization_import_"
            "regression_blocked"
        )
        assert (
            result["data"][
                "post_wrapper_removal_regression_from_materialization_import_verified"
            ]
            is False
        )
        assert result["data"]["source_recovery_cleanup_ready"] is False
        assert result["data"]["current_vault_wrappers_removed"] is False
        assert (
            result["data"][
                "current_vault_source_closeout_from_materialization_import_regression_ready"
            ]
            is False
        )
        assert result["data"]["regression_commands_executed_by_chaseos"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "post_wrapper_removal_regression_from_materialization_import_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_production_primary_closeout_after_source_recovery_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_production_primary_closeout_after_source_recovery_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_production_primary_closeout_after_source_recovery_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_production_primary_closeout_after_source_recovery_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_production_primary_closeout_after_source_recovery_blocked"
        )
        assert result["data"]["source_closeout_ready"] is False
        assert result["data"]["primary_relaunch_receipt_boundary_ready"] is False
        assert (
            result["data"][
                "production_primary_closeout_after_source_recovery_ready_for_final_audit"
            ]
            is False
        )
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["helper_launch_performed"] is False
        assert result["data"]["installer_launch_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert (
            "current_vault_source_closeout_from_materialization_import_regression_proof_required"
            in result["data"]["errors"]
        )
        assert (
            "production_primary_relaunch_receipt_boundary_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_final_production_auto_update_closeout_audit_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_final_production_auto_update_closeout_audit()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_final_production_auto_update_closeout_audit"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_final_production_auto_update_closeout_audit"
        )
        assert result["data"]["status"] == (
            "launcher_update_final_production_auto_update_closeout_audit_blocked"
        )
        assert (
            result["data"][
                "production_primary_closeout_after_source_recovery_ready_for_final_audit"
            ]
            is False
        )
        assert result["data"]["live_completion_evidence_verified"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert result["data"]["helper_launch_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["github_mutation_performed_by_this_proof"] is False
        assert result["data"]["primary_exe_replacement_performed_by_this_proof"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert (
            "production_primary_closeout_after_source_recovery_proof_required"
            in result["data"]["errors"]
        )
        assert "live_completion_evidence_required" in result["data"]["errors"]

    def test_api_returns_governed_live_completion_evidence_packet_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_governed_live_completion_evidence_packet()

        assert result["ok"] is True
        assert result["surface"] == (
            "launcher_update_governed_live_completion_evidence_packet"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_governed_live_completion_evidence_packet"
        )
        assert result["data"]["status"] == (
            "launcher_update_governed_live_completion_evidence_packet_claims_required"
        )
        assert result["data"]["live_completion_evidence_verified"] is False
        assert (
            result["data"]["feeds_final_production_auto_update_closeout_audit"]
            is False
        )
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert result["data"]["github_mutation_performed_by_this_proof"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["helper_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_exe_replacement_performed_by_this_proof"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert "live_completion_evidence_claims_required" in result["data"]["errors"]

    def test_api_returns_controlled_live_installer_evidence_runner_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_controlled_live_installer_evidence_runner()

        assert result["ok"] is True
        assert result["surface"] == (
            "launcher_update_controlled_live_installer_evidence_runner"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_controlled_live_installer_evidence_runner"
        )
        assert result["data"]["status"] == (
            "launcher_update_controlled_live_installer_evidence_runner_blocked"
        )
        assert result["data"]["runner_execution_allowed"] is False
        assert result["data"]["runner_execution_performed"] is False
        assert result["data"]["governed_live_completion_evidence_packet_ready"] is False
        assert (
            result["data"]["feeds_final_production_auto_update_closeout_audit"]
            is False
        )
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert result["data"]["settings_install_control_exposed"] is False
        assert (
            "controlled_live_installer_evidence_runner_required"
            in result["data"]["errors"]
        )

    def test_api_returns_approved_live_evidence_runner_adapter_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_approved_live_evidence_runner_adapter()

        assert result["ok"] is True
        assert result["surface"] == (
            "launcher_update_approved_live_evidence_runner_adapter"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_approved_live_evidence_runner_adapter"
        )
        assert result["data"]["status"] == (
            "launcher_update_approved_live_evidence_runner_adapter_blocked"
        )
        assert result["data"]["approved_live_evidence_runner_adapter_ready"] is False
        assert result["data"]["sources_ready"] is False
        assert result["data"]["adapter_runner_executed"] is False
        assert result["data"]["governed_live_completion_evidence_packet_ready"] is False
        assert (
            result["data"]["feeds_final_production_auto_update_closeout_audit"]
            is False
        )
        assert result["data"]["download_performed_by_adapter"] is False
        assert result["data"]["installer_launch_performed_by_adapter"] is False
        assert result["data"]["primary_replacement_performed_by_adapter"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["final_auto_update_closeout_blocked"] is True
        assert result["data"]["settings_install_control_exposed"] is False
        assert (
            "signed_release_manifest_live_readback_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_approved_live_evidence_runner_real_dry_run_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_approved_live_evidence_runner_real_dry_run()

        assert result["ok"] is True
        assert result["surface"] == (
            "launcher_update_approved_live_evidence_runner_real_dry_run"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_approved_live_evidence_runner_real_dry_run"
        )
        assert result["data"]["status"] == (
            "launcher_update_approved_live_evidence_runner_real_dry_run_blocked"
        )
        assert result["data"]["current_vault_source_proofs_collected"] is True
        assert result["data"]["sources_ready"] is False
        assert result["data"]["approved_live_evidence_runner_adapter_ready"] is False
        assert result["data"]["governed_live_completion_evidence_packet_ready"] is False
        assert result["data"]["final_production_auto_update_closeout_audit_ready"] is False
        assert result["data"]["download_performed_by_dry_run"] is False
        assert result["data"]["installer_launch_performed_by_dry_run"] is False
        assert result["data"]["primary_replacement_performed_by_dry_run"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert (
            "operator_live_evidence_runner_real_dry_run_approval_required"
            in result["data"]["errors"]
        )

    def test_api_returns_live_receipt_digest_consistency_closeout_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_live_receipt_digest_consistency_closeout()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_live_receipt_digest_consistency_closeout"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_live_receipt_digest_consistency_closeout"
        )
        assert result["data"]["status"] == (
            "launcher_update_live_receipt_digest_consistency_closeout_"
            "ready_but_receipts_not_ready"
        )
        assert result["data"]["current_vault_source_proofs_collected"] is True
        assert result["data"]["digest_consistency_closeout_ready"] is True
        assert result["data"]["source_receipts_ready"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False

    def test_api_returns_real_live_receipt_capture_boundary_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_real_live_receipt_capture_boundary()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_real_live_receipt_capture_boundary"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_real_live_receipt_capture_boundary"
        )
        assert result["data"]["status"] == (
            "launcher_update_real_live_receipt_capture_boundary_blocked"
        )
        assert result["data"]["receipt_bundle_valid"] is False
        assert result["data"]["source_receipts_ready"] is False
        assert result["data"]["governed_live_completion_evidence_packet_ready"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert "real_live_receipt_bundle_required" in result["data"]["errors"]

    def test_api_returns_real_live_receipt_bundle_production_runner_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_real_live_receipt_bundle_production_runner()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_real_live_receipt_bundle_production_runner"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_real_live_receipt_bundle_production_runner"
        )
        assert result["data"]["status"] == (
            "launcher_update_real_live_receipt_bundle_production_runner_blocked"
        )
        assert result["data"]["runner_execution_performed"] is False
        assert result["data"]["receipt_bundle_valid"] is False
        assert result["data"]["capture_boundary_ready"] is False
        assert result["data"]["governed_live_completion_evidence_packet_ready"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert "real_live_receipt_bundle_runner_required" in result["data"]["errors"]

    def test_api_returns_production_runner_final_closeout_bridge_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_production_runner_final_closeout_bridge()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_production_runner_final_closeout_bridge"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_production_runner_final_closeout_bridge"
        )
        assert result["data"]["status"] == (
            "launcher_update_production_runner_final_closeout_bridge_blocked"
        )
        assert result["data"]["runner_proof_ready"] is False
        assert result["data"]["primary_closeout_ready"] is False
        assert (
            result["data"]["final_production_auto_update_closeout_audit_ready"]
            is False
        )
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert (
            "real_live_receipt_bundle_production_runner_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_approved_production_runner_real_evidence_capture_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_approved_production_runner_real_evidence_capture()

        assert result["ok"] is True
        assert result["surface"] == (
            "launcher_update_approved_production_runner_real_evidence_capture"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_approved_production_runner_real_evidence_capture"
        )
        assert result["data"]["status"] == (
            "launcher_update_approved_production_runner_real_evidence_capture_blocked"
        )
        assert result["data"]["evidence_file_read_performed"] is False
        assert result["data"]["production_runner_final_closeout_bridge_ready"] is False
        assert result["data"]["runner_execution_performed_by_this_proof"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert (
            "approved_production_runner_real_evidence_root_required"
            in result["data"]["errors"]
        )

    def test_api_returns_installer_real_artifact_build_output_capture_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_installer_real_artifact_build_output_capture()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_installer_real_artifact_build_output_capture"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_installer_real_artifact_build_output_capture"
        )
        assert result["data"]["status"] in {
            "launcher_update_installer_real_artifact_build_output_capture_blocked",
            (
                "launcher_update_installer_real_artifact_build_output_capture_"
                "captured_unsigned"
            ),
            (
                "launcher_update_installer_real_artifact_build_output_capture_"
                "signed_output_verified"
            ),
        }
        assert result["data"]["installer_artifact_exact_name"] is True
        assert result["data"]["build_script_studio_hash_guard_ready"] is True
        assert result["data"]["build_script_isolated_installer_dist_ready"] is True
        assert result["data"]["signature_probe_performed"] is False
        assert result["data"]["signing_required"] is True
        assert result["data"]["installer_signed_output_verified"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False

    def test_api_returns_dist_artifact_isolation_cohabitation_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_dist_artifact_isolation_cohabitation_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_dist_artifact_isolation_cohabitation_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_dist_artifact_isolation_cohabitation_proof"
        )
        assert result["data"]["status"] in {
            "launcher_update_dist_artifact_isolation_cohabitation_blocked",
            "launcher_update_dist_artifact_isolation_cohabitation_verified_unsigned",
        }
        assert result["data"]["studio_artifact_present"] is True
        assert result["data"]["installer_artifact_present"] is True
        assert result["data"]["both_artifacts_present"] is True
        assert result["data"]["studio_build_script_isolated_dist_ready"] is True
        assert result["data"]["installer_build_script_isolated_dist_ready"] is True
        assert result["data"]["cross_artifact_hash_guards_ready"] is True
        assert result["data"]["signing_required"] is True
        assert result["data"]["signed_output_verified"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False

    def test_api_returns_signed_artifact_verification_closeout_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_signed_artifact_verification_closeout()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_signed_artifact_verification_closeout"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_signed_artifact_verification_closeout"
        )
        assert result["data"]["status"] in {
            "launcher_update_signed_artifact_verification_closeout_blocked",
            (
                "launcher_update_signed_artifact_verification_closeout_"
                "signature_probe_required"
            ),
            (
                "launcher_update_signed_artifact_verification_closeout_"
                "signatures_blocked"
            ),
            "launcher_update_signed_artifact_verification_closeout_verified",
        }
        assert result["data"]["cohabitation_ready"] is True
        assert result["data"]["signature_probe_performed"] is False
        assert result["data"]["studio_signed_output_verified"] is False
        assert result["data"]["installer_signed_output_verified"] is False
        assert result["data"]["signed_artifacts_verified"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False

    def test_api_returns_local_installer_disposable_dry_run_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_local_installer_disposable_dry_run_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_local_installer_disposable_dry_run_proof"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_local_installer_disposable_dry_run_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_local_installer_disposable_dry_run_blocked"
        )
        assert result["data"]["helper_binary_name"] == "ChaseOS-Installer.exe"
        assert result["data"]["local_installer_disposable_dry_run_executed"] is False
        assert result["data"]["plan_file_write_performed"] is False
        assert result["data"]["installer_execution_performed"] is False
        assert result["data"]["primary_install_mutation_performed"] is False
        assert result["data"]["production_auto_update_complete"] is False
        assert result["data"]["settings_install_control_exposed"] is False

    def test_api_returns_local_manifest_background_prompt_settings_action_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_local_manifest_background_prompt_settings_action()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_local_manifest_background_prompt_settings_action"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_local_manifest_background_prompt_settings_action"
        )
        assert result["data"]["status"] == (
            "launcher_update_local_manifest_background_prompt_no_manifest_configured"
        )
        assert result["data"]["settings_prompt_visible"] is False
        assert result["data"]["settings_install_control_exposed"] is False
        assert result["data"]["settings_download_control_exposed"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False

    def test_api_returns_local_release_channel_blocker_closeout_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_local_release_channel_blocker_closeout()

        assert result["ok"] is True
        assert result["surface"] == (
            "launcher_update_local_release_channel_blocker_closeout"
        )
        assert result["data"]["surface"] == (
            "studio_launcher_update_local_release_channel_blocker_closeout"
        )
        assert result["data"]["ok"] is True
        assert result["data"]["only_external_blockers_remain"] is True
        assert result["data"]["non_external_blockers"] == []
        assert "release_channel_hosting_not_connected" in result["data"][
            "external_blocker_ids"
        ]
        assert result["data"]["settings_install_control_exposed"] is False
        assert result["data"]["download_performed_by_this_proof"] is False
        assert result["data"]["installer_launch_performed_by_this_proof"] is False
        assert result["data"]["primary_replacement_performed_by_this_proof"] is False
        assert result["data"]["production_auto_update_complete"] is False

    def test_api_returns_authoritative_candidate_supply_verification_after_import_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_authoritative_candidate_supply_verification_after_import_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_authoritative_candidate_supply_verification_after_import_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_authoritative_candidate_supply_verification_after_import_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_authoritative_candidate_supply_verification_after_import_blocked"
        )
        assert result["data"]["import_boundary_verified"] is False
        assert result["data"]["candidate_supply_packet_ready"] is False
        assert result["data"]["candidate_verification_ready"] is False
        assert result["data"]["ready_for_wrapper_removal_executor"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "authoritative_source_candidate_import_boundary_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_current_vault_wrapper_removal_after_import_execution_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_current_vault_wrapper_removal_after_import_execution_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_current_vault_wrapper_removal_after_import_execution_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_current_vault_wrapper_removal_after_import_execution_proof"
        )
        assert result["data"]["status"] == (
            "launcher_update_current_vault_wrapper_removal_after_import_execution_blocked"
        )
        assert result["data"]["after_import_ready_for_wrapper_removal_executor"] is False
        assert result["data"]["restore_plan_ready"] is False
        assert result["data"]["current_vault_source_write_enabled"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "authoritative_candidate_supply_verification_after_import_proof_required"
            in result["data"]["errors"]
        )

    def test_api_returns_current_vault_wrapper_removal_executor_boundary_envelope(
        self,
    ):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_current_vault_wrapper_removal_executor_boundary_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_current_vault_wrapper_removal_executor_boundary_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_current_vault_wrapper_removal_executor_boundary_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_current_vault_wrapper_removal_executor_blocked"
        )
        assert result["data"]["restore_plan_ready"] is False
        assert result["data"]["current_vault_source_write_enabled"] is False
        assert result["data"]["source_write_performed"] is False
        assert result["data"]["wrapper_removal_performed"] is False
        assert result["data"]["primary_exe_replacement_performed"] is False
        assert result["data"]["settings_write_control_exposed"] is False
        assert (
            "authoritative_candidate_supply_packet_not_ready"
            in result["data"]["errors"]
        )

    def test_api_returns_blocked_primary_relaunch_receipt_boundary_envelope(self):
        from runtime.studio.shell.api import StudioAPI

        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_launcher_update_production_primary_relaunch_receipt_boundary_proof()

        assert result["ok"] is True
        assert (
            result["surface"]
            == "launcher_update_production_primary_relaunch_receipt_boundary_proof"
        )
        assert (
            result["data"]["surface"]
            == "studio_launcher_update_production_primary_relaunch_receipt_boundary_proof"
        )
        assert (
            result["data"]["status"]
            == "launcher_update_production_primary_relaunch_receipt_boundary_blocked"
        )
        assert (
            "production_primary_replacement_receipt_boundary_required"
            in result["data"]["errors"]
        )
        assert result["data"]["primary_relaunch_receipt_boundary_ready"] is False
        assert result["data"]["primary_relaunch_receipt_valid"] is False
        assert result["data"]["external_helper_primary_relaunch_reported"] is False
        assert result["data"]["relaunch_performed_by_chaseos"] is False
        assert result["data"]["authority"]["executable_replacement_performed"] is False

    def test_panel_registry_exposes_primary_relaunch_receipt_boundary_api(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT_ROOT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        settings = panels["settings"]

        assert (
            "get_launcher_update_source_recovery_cleanup_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_normal_source_restoration_readiness"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_normal_source_candidate_verification_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_normal_source_candidate_restore_executor_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_source_regeneration_readiness"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_source_regeneration_runner_boundary_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_source_regeneration_candidate_verification_restore_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_source_regeneration_live_source_restoration_closeout_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_real_source_restoration_execution_regression_boundary_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_current_vault_source_restoration_closeout_readiness"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_source_candidate_inventory_wrapper_removal_preflight"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_authoritative_normal_source_candidate_supply_packet"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_authoritative_source_candidate_import_boundary_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_real_authoritative_source_candidate_supply_readiness"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_real_authoritative_source_candidate_materialization_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_production_primary_closeout_after_source_recovery_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_final_production_auto_update_closeout_audit"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_governed_live_completion_evidence_packet"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_controlled_live_installer_evidence_runner"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_approved_live_evidence_runner_adapter"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_approved_live_evidence_runner_real_dry_run"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_live_receipt_digest_consistency_closeout"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_real_live_receipt_capture_boundary"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_real_live_receipt_bundle_production_runner"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_production_runner_final_closeout_bridge"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_approved_production_runner_real_evidence_capture"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_installer_real_artifact_build_output_capture"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_dist_artifact_isolation_cohabitation_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_signed_artifact_verification_closeout"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_local_installer_disposable_dry_run_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_local_manifest_background_prompt_settings_action"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_local_release_channel_blocker_closeout"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_authoritative_candidate_supply_verification_after_import_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_current_vault_wrapper_removal_after_import_execution_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_current_vault_wrapper_removal_executor_boundary_proof"
            in settings["api_methods"]
        )
        assert (
            "get_launcher_update_production_primary_relaunch_receipt_boundary_proof"
            in settings["api_methods"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_source_recovery_cleanup_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_normal_source_restoration_readiness"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_normal_source_candidate_verification_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_normal_source_candidate_restore_executor_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_source_regeneration_readiness"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_source_regeneration_runner_boundary_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_source_regeneration_candidate_verification_restore_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_source_regeneration_live_source_restoration_closeout_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_real_source_restoration_execution_regression_boundary_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_current_vault_source_restoration_closeout_readiness"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_source_candidate_inventory_wrapper_removal_preflight"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_authoritative_normal_source_candidate_supply_packet"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_authoritative_source_candidate_import_boundary_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_real_authoritative_source_candidate_supply_readiness"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_real_authoritative_source_candidate_materialization_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_production_primary_closeout_after_source_recovery_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_final_production_auto_update_closeout_audit"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_governed_live_completion_evidence_packet"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_controlled_live_installer_evidence_runner"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_approved_live_evidence_runner_adapter"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_approved_live_evidence_runner_real_dry_run"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_live_receipt_digest_consistency_closeout"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_real_live_receipt_capture_boundary"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_real_live_receipt_bundle_production_runner"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_production_runner_final_closeout_bridge"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_approved_production_runner_real_evidence_capture"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_installer_real_artifact_build_output_capture"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_dist_artifact_isolation_cohabitation_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_signed_artifact_verification_closeout"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_local_installer_disposable_dry_run_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_local_manifest_background_prompt_settings_action"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_local_release_channel_blocker_closeout"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_authoritative_candidate_supply_verification_after_import_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof"
            in settings["source_contract"]
        )
        assert (
            "runtime.studio.launcher_update_check.build_launcher_update_production_primary_relaunch_receipt_boundary_proof"
            in settings["source_contract"]
        )
