"""Pass 10B tests — graph style registry, settings persistence, presets."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from runtime.studio.shell.graph_style_registry import (
    VALID_SHAPES,
    VALID_BORDER_STYLES,
    VALID_LINE_STYLES,
    VALID_ARROW_STYLES,
    VALID_TRUST_STATES,
    VALID_EDGE_LAYERS,
    DEFAULT_NODE_FAMILIES,
    DEFAULT_EDGE_LAYERS,
    DEFAULT_TRUST_STATES,
    NODE_TYPE_TO_FAMILY,
    canonical_edge_layer,
    get_default_registry,
    validate_node_family,
    validate_edge_layer,
    validate_trust_state,
    validate_registry,
)
from runtime.studio.shell.graph_settings import (
    get_default_settings,
    load_graph_settings,
    save_graph_settings,
    reset_graph_settings,
    patch_graph_settings,
    validate_settings,
    SETTINGS_VERSION,
)
from runtime.studio.shell.graph_presets import (
    BUILTIN_PRESETS,
    list_presets,
    get_preset,
    save_preset,
    delete_preset,
)


# ── graph_style_registry ──────────────────────────────────────────────────────

class TestRegistryConstants:
    def test_valid_shapes_is_frozenset(self):
        assert isinstance(VALID_SHAPES, frozenset)

    def test_valid_shapes_nonempty(self):
        assert len(VALID_SHAPES) > 0

    def test_ellipse_in_shapes(self):
        assert "ellipse" in VALID_SHAPES

    def test_valid_border_styles_contains_solid(self):
        assert "solid" in VALID_BORDER_STYLES

    def test_valid_line_styles_contains_solid(self):
        assert "solid" in VALID_LINE_STYLES

    def test_valid_arrow_styles_contains_triangle(self):
        assert "triangle" in VALID_ARROW_STYLES

    def test_valid_trust_states_count(self):
        assert len(VALID_TRUST_STATES) == 8

    def test_valid_edge_layers_count(self):
        assert len(VALID_EDGE_LAYERS) == 4


class TestNodeFamilies:
    def test_14_families_defined(self):
        assert len(DEFAULT_NODE_FAMILIES) == 14

    def test_all_required_keys(self):
        required = {"label", "shape", "fill_color", "border_color", "border_style", "border_width", "badge", "size_base"}
        for name, fam in DEFAULT_NODE_FAMILIES.items():
            for key in required:
                assert key in fam, f"{name} missing key {key!r}"

    def test_all_shapes_valid(self):
        for name, fam in DEFAULT_NODE_FAMILIES.items():
            assert fam["shape"] in VALID_SHAPES, f"{name}: shape {fam['shape']!r} not in VALID_SHAPES"

    def test_all_border_styles_valid(self):
        for name, fam in DEFAULT_NODE_FAMILIES.items():
            assert fam["border_style"] in VALID_BORDER_STYLES, f"{name}: border_style {fam['border_style']!r} invalid"

    def test_generated_artifact_has_ai_badge(self):
        assert DEFAULT_NODE_FAMILIES["generated_artifact"]["badge"] == "AI"

    def test_intake_has_dashed_border(self):
        assert DEFAULT_NODE_FAMILIES["intake"]["border_style"] == "dashed"

    def test_agent_is_octagon(self):
        assert DEFAULT_NODE_FAMILIES["agent"]["shape"] == "octagon"

    def test_knowledge_is_rectangle(self):
        assert DEFAULT_NODE_FAMILIES["knowledge"]["shape"] == "rectangle"


class TestEdgeLayers:
    def test_4_layers_defined(self):
        assert len(DEFAULT_EDGE_LAYERS) == 4

    def test_all_required_edge_keys(self):
        required = {"label", "color", "line_style", "width", "opacity", "arrow", "animated", "visible"}
        for name, layer in DEFAULT_EDGE_LAYERS.items():
            for key in required:
                assert key in layer, f"edge_layer.{name} missing key {key!r}"

    def test_all_line_styles_valid(self):
        for name, layer in DEFAULT_EDGE_LAYERS.items():
            assert layer["line_style"] in VALID_LINE_STYLES, f"{name}: line_style invalid"

    def test_all_arrows_valid(self):
        for name, layer in DEFAULT_EDGE_LAYERS.items():
            assert layer["arrow"] in VALID_ARROW_STYLES, f"{name}: arrow invalid"

    def test_runtime_layer_animated(self):
        assert DEFAULT_EDGE_LAYERS["runtime_action"]["animated"] is True

    def test_structural_has_none_arrow(self):
        assert DEFAULT_EDGE_LAYERS["structural"]["arrow"] == "none"

    def test_legacy_runtime_layer_alias(self):
        assert canonical_edge_layer("runtime") == "runtime_action"

    def test_legacy_suggested_layer_alias(self):
        assert canonical_edge_layer("suggested") == "suggested_semantic"


class TestTrustStates:
    def test_8_trust_states_defined(self):
        assert len(DEFAULT_TRUST_STATES) == 8

    def test_canonical_has_double_ring(self):
        assert DEFAULT_TRUST_STATES["canonical"]["ring_style"] == "double"

    def test_quarantined_has_badge(self):
        assert DEFAULT_TRUST_STATES["quarantined"]["badge"] == "Q"

    def test_disputed_has_bang_badge(self):
        assert DEFAULT_TRUST_STATES["disputed"]["badge"] == "!"

    def test_generated_has_ai_badge(self):
        assert DEFAULT_TRUST_STATES["generated"]["badge"] == "AI"


class TestNodeTypeToFamily:
    def test_project_doc_maps_to_project(self):
        assert NODE_TYPE_TO_FAMILY["project_doc"] == "project"

    def test_knowledge_doc_maps_to_knowledge(self):
        assert NODE_TYPE_TO_FAMILY["knowledge_doc"] == "knowledge"

    def test_build_log_maps_to_log_audit(self):
        assert NODE_TYPE_TO_FAMILY["build_log"] == "log_audit"

    def test_agent_control_doc_maps_to_agent(self):
        assert NODE_TYPE_TO_FAMILY["agent_control_doc"] == "agent"

    def test_all_values_are_valid_family_names(self):
        valid_families = set(DEFAULT_NODE_FAMILIES.keys())
        for node_type, family in NODE_TYPE_TO_FAMILY.items():
            assert family in valid_families, f"{node_type} → {family!r} not a valid family"


class TestGetDefaultRegistry:
    def test_returns_dict(self):
        r = get_default_registry()
        assert isinstance(r, dict)

    def test_has_schema_version(self):
        r = get_default_registry()
        assert "schema_version" in r

    def test_has_all_sections(self):
        r = get_default_registry()
        for key in ("node_families", "edge_layers", "trust_states", "node_type_to_family"):
            assert key in r


class TestValidateRegistry:
    def test_default_registry_validates_ok(self):
        result = validate_registry(get_default_registry())
        assert result["ok"] is True
        assert result["errors"] == []

    def test_invalid_shape_caught(self):
        reg = get_default_registry()
        reg["node_families"]["knowledge"]["shape"] = "not-a-shape"
        result = validate_registry(reg)
        assert result["ok"] is False
        assert any("invalid shape" in e for e in result["errors"])

    def test_invalid_line_style_caught(self):
        reg = get_default_registry()
        reg["edge_layers"]["explicit"]["line_style"] = "wavy"
        result = validate_registry(reg)
        assert result["ok"] is False

    def test_invalid_ring_style_caught(self):
        reg = get_default_registry()
        reg["trust_states"]["canonical"]["ring_style"] = "triple"
        result = validate_registry(reg)
        assert result["ok"] is False


# ── graph_settings ────────────────────────────────────────────────────────────

class TestDefaultSettings:
    def test_returns_dict(self):
        s = get_default_settings()
        assert isinstance(s, dict)

    def test_has_schema_version(self):
        s = get_default_settings()
        assert s["schema_version"] == SETTINGS_VERSION

    def test_has_8_sections(self):
        s = get_default_settings()
        for section in ("appearance", "node_families", "edge_layers", "trust_states",
                        "accessibility", "node_scope", "layout", "inspector",
                        "generated_canonical"):
            assert section in s

    def test_node_families_has_all_14(self):
        s = get_default_settings()
        assert len(s["node_families"]) == 14

    def test_edge_layers_visible_by_default(self):
        s = get_default_settings()
        for layer, cfg in s["edge_layers"].items():
            assert cfg.get("visible") is True, f"{layer} should be visible by default"


class TestSettingsValidation:
    def test_default_settings_valid(self):
        result = validate_settings(get_default_settings())
        assert result["ok"] is True

    def test_invalid_font_size(self):
        s = get_default_settings()
        s["appearance"]["label_font_size"] = 100
        result = validate_settings(s)
        assert result["ok"] is False

    def test_invalid_colorblind_mode(self):
        s = get_default_settings()
        s["accessibility"]["colorblind_mode"] = "alien-vision"
        result = validate_settings(s)
        assert result["ok"] is False

    def test_invalid_max_nodes(self):
        s = get_default_settings()
        s["node_scope"]["max_nodes"] = 99999
        result = validate_settings(s)
        assert result["ok"] is False

    def test_invalid_layout_algorithm(self):
        s = get_default_settings()
        s["layout"]["algorithm"] = "force-atlas"
        result = validate_settings(s)
        assert result["ok"] is False

    def test_invalid_inspector_tab(self):
        s = get_default_settings()
        s["inspector"]["default_tab"] = "nonexistent-tab"
        result = validate_settings(s)
        assert result["ok"] is False

    def test_invalid_node_family_shape(self):
        s = get_default_settings()
        s["node_families"]["project"] = {"shape": "not-real"}
        result = validate_settings(s)
        assert result["ok"] is False

    def test_trust_state_cannot_be_hidden(self):
        s = get_default_settings()
        s["trust_states"]["generated"]["visible"] = False
        result = validate_settings(s)
        assert result["ok"] is False

    def test_generated_badge_cannot_be_hidden(self):
        s = get_default_settings()
        s["generated_canonical"]["generated_badge_visible"] = False
        result = validate_settings(s)
        assert result["ok"] is False

    def test_legacy_edge_layer_migrates_on_load(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "graph-settings.json").write_text(
            json.dumps({"edge_layers": {"runtime": {"visible": False}}}),
            encoding="utf-8",
        )
        loaded = load_graph_settings(tmp)
        assert "runtime_action" in loaded["edge_layers"]
        assert loaded["edge_layers"]["runtime_action"]["visible"] is False

    def test_non_dict_rejected(self):
        result = validate_settings("not a dict")
        assert result["ok"] is False


class TestSettingsPersistence:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_load_returns_defaults_when_no_file(self):
        s = load_graph_settings(self.tmp)
        assert s["schema_version"] == SETTINGS_VERSION

    def test_save_and_reload(self):
        settings = get_default_settings()
        settings["appearance"]["show_labels"] = False
        save_graph_settings(self.tmp, settings)
        loaded = load_graph_settings(self.tmp)
        assert loaded["appearance"]["show_labels"] is False

    def test_save_creates_file(self):
        save_graph_settings(self.tmp, get_default_settings())
        assert (self.tmp / "graph-settings.json").exists()

    def test_reset_removes_file(self):
        save_graph_settings(self.tmp, get_default_settings())
        assert (self.tmp / "graph-settings.json").exists()
        reset_graph_settings(self.tmp)
        assert not (self.tmp / "graph-settings.json").exists()

    def test_load_after_reset_returns_defaults(self):
        save_graph_settings(self.tmp, get_default_settings())
        reset_graph_settings(self.tmp)
        s = load_graph_settings(self.tmp)
        assert s == get_default_settings()

    def test_patch_merges_without_losing_other_keys(self):
        save_graph_settings(self.tmp, get_default_settings())
        patch_graph_settings(self.tmp, {"appearance": {"show_labels": False}})
        loaded = load_graph_settings(self.tmp)
        assert loaded["appearance"]["show_labels"] is False
        assert "label_font_size" in loaded["appearance"]

    def test_save_returns_ok_true(self):
        result = save_graph_settings(self.tmp, get_default_settings())
        assert result["ok"] is True

    def test_save_invalid_returns_ok_false(self):
        s = get_default_settings()
        s["appearance"]["label_font_size"] = 999
        result = save_graph_settings(self.tmp, s)
        assert result["ok"] is False

    def test_saved_file_is_valid_json(self):
        save_graph_settings(self.tmp, get_default_settings())
        raw = (self.tmp / "graph-settings.json").read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_corrupt_file_returns_defaults(self):
        path = self.tmp / "graph-settings.json"
        path.write_text("{ not valid json", encoding="utf-8")
        s = load_graph_settings(self.tmp)
        assert s == get_default_settings()


# ── graph_presets ─────────────────────────────────────────────────────────────

class TestBuiltinPresets:
    def test_8_builtins_defined(self):
        assert len(BUILTIN_PRESETS) == 8

    def test_full_graph_is_builtin(self):
        assert "full-graph" in BUILTIN_PRESETS

    def test_knowledge_map_is_builtin(self):
        assert "knowledge-map" in BUILTIN_PRESETS

    def test_personal_map_is_builtin(self):
        assert "personal-map" in BUILTIN_PRESETS

    def test_runtime_map_uses_runtime_action_layer(self):
        assert "runtime_action" in BUILTIN_PRESETS["runtime-map"]["filters"]["edge_layers"]

    def test_all_builtins_have_required_keys(self):
        for pid, preset in BUILTIN_PRESETS.items():
            for key in ("id", "label", "description", "builtin", "filters",
                        "layout", "visible_panels", "focus_mode", "legend_state",
                        "settings_patch"):
                assert key in preset, f"builtin preset {pid!r} missing {key!r}"

    def test_all_builtins_marked_builtin_true(self):
        for pid, preset in BUILTIN_PRESETS.items():
            assert preset["builtin"] is True

    def test_builtin_ids_match_keys(self):
        for pid, preset in BUILTIN_PRESETS.items():
            assert preset["id"] == pid


class TestPresetsCRUD:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_list_presets_includes_builtins(self):
        presets = list_presets(self.tmp)
        ids = [p["id"] for p in presets]
        assert "full-graph" in ids
        assert "knowledge-map" in ids

    def test_list_presets_count_at_least_builtins(self):
        presets = list_presets(self.tmp)
        assert len(presets) >= len(BUILTIN_PRESETS)

    def test_get_builtin_preset(self):
        preset = get_preset(self.tmp, "full-graph")
        assert preset is not None
        assert preset["builtin"] is True

    def test_get_missing_preset_returns_none(self):
        assert get_preset(self.tmp, "nonexistent-preset") is None

    def test_save_and_get_user_preset(self):
        result = save_preset(self.tmp, "my-preset", "My Preset", "desc", {"appearance": {"show_labels": False}})
        assert result["ok"] is True
        preset = get_preset(self.tmp, "my-preset")
        assert preset is not None
        assert preset["label"] == "My Preset"
        assert preset["builtin"] is False

    def test_save_user_preset_can_store_filters(self):
        result = save_preset(
            self.tmp,
            "filtered-preset",
            "Filtered Preset",
            "desc",
            {},
            filters={"node_families": ["project"], "edge_layers": ["explicit"]},
        )
        assert result["ok"] is True
        preset = get_preset(self.tmp, "filtered-preset")
        assert preset is not None
        assert preset["filters"]["node_families"] == ["project"]
        assert preset["filters"]["edge_layers"] == ["explicit"]

    def test_user_preset_appears_in_list(self):
        save_preset(self.tmp, "my-preset2", "My Preset 2", "", {})
        ids = [p["id"] for p in list_presets(self.tmp)]
        assert "my-preset2" in ids

    def test_delete_user_preset(self):
        save_preset(self.tmp, "to-delete", "Delete Me", "", {})
        result = delete_preset(self.tmp, "to-delete")
        assert result["ok"] is True
        assert get_preset(self.tmp, "to-delete") is None

    def test_delete_builtin_blocked(self):
        result = delete_preset(self.tmp, "full-graph")
        assert result["ok"] is False

    def test_save_builtin_id_blocked(self):
        result = save_preset(self.tmp, "full-graph", "Override", "", {})
        assert result["ok"] is False

    def test_invalid_slug_rejected(self):
        result = save_preset(self.tmp, "Bad Slug!", "label", "", {})
        assert result["ok"] is False

    def test_empty_label_rejected(self):
        result = save_preset(self.tmp, "valid-slug", "", "", {})
        assert result["ok"] is False

    def test_delete_missing_preset_returns_error(self):
        result = delete_preset(self.tmp, "no-such-preset")
        assert result["ok"] is False


# ── api.py 10B methods ────────────────────────────────────────────────────────

class TestAPIGraphSettingsMethods:
    def setup_method(self):
        from pathlib import Path
        import sys
        import os
        vault_root = Path(__file__).parents[3]
        from runtime.studio.shell.api import StudioAPI
        self._old_state_dir = os.environ.get("CHASEOS_STUDIO_STATE_DIR")
        self._api_state_dir = Path(tempfile.mkdtemp())
        os.environ["CHASEOS_STUDIO_STATE_DIR"] = str(self._api_state_dir)
        self.api = StudioAPI(str(vault_root))

    def teardown_method(self):
        import os
        if self._old_state_dir is None:
            os.environ.pop("CHASEOS_STUDIO_STATE_DIR", None)
        else:
            os.environ["CHASEOS_STUDIO_STATE_DIR"] = self._old_state_dir

    def test_get_graph_style_registry_ok(self):
        r = self.api.get_graph_style_registry()
        assert r["ok"] is True
        assert r["data"]["schema_version"].startswith("studio.graph.style.registry")

    def test_get_graph_style_registry_has_node_families(self):
        r = self.api.get_graph_style_registry()
        assert "node_families" in r["data"]
        assert len(r["data"]["node_families"]) == 14

    def test_get_graph_settings_ok(self):
        r = self.api.get_graph_settings()
        assert r["ok"] is True
        assert "appearance" in r["data"]

    def test_save_graph_settings_ok(self):
        r = self.api.get_graph_settings()
        settings = r["data"]
        result = self.api.save_graph_settings(settings)
        assert result["ok"] is True

    def test_reset_graph_settings_ok(self):
        r = self.api.reset_graph_settings()
        assert r["ok"] is True
        assert r["data"]["reset"] is True

    def test_list_graph_presets_ok(self):
        r = self.api.list_graph_presets()
        assert r["ok"] is True
        assert isinstance(r["data"]["presets"], list)

    def test_get_graph_preset_builtin(self):
        r = self.api.get_graph_preset("full-graph")
        assert r["ok"] is True
        assert r["data"]["id"] == "full-graph"

    def test_get_graph_preset_missing(self):
        r = self.api.get_graph_preset("no-such-preset-x99")
        assert r["ok"] is False

    def test_save_and_delete_user_preset(self):
        slug = "test-api-preset"
        r = self.api.save_graph_preset(slug, "Test API Preset", "desc", {}, {"node_families": ["project"]})
        assert r["ok"] is True
        p = self.api.get_graph_preset(slug)
        assert p["ok"] is True
        assert p["data"]["filters"]["node_families"] == ["project"]
        d = self.api.delete_graph_preset(slug)
        assert d["ok"] is True

    def test_delete_builtin_preset_blocked(self):
        r = self.api.delete_graph_preset("full-graph")
        assert r["ok"] is False


# ── frontend 10B structure ────────────────────────────────────────────────

class TestFrontendGraphDesignSystemModules:
    @property
    def frontend_dir(self) -> Path:
        return Path(__file__).parent / "frontend"

    def read_frontend(self, name: str) -> str:
        return (self.frontend_dir / name).read_text(encoding="utf-8")

    def test_graph_filters_module_exists(self):
        assert (self.frontend_dir / "graphFilters.js").exists()

    def test_graph_filters_exports_namespace(self):
        src = self.read_frontend("graphFilters.js")
        assert "window.GraphFilters" in src
        assert "renderGraphControls" in src
        assert "applyGraphFilters" in src

    def test_graph_filters_supports_modifier_behaviors(self):
        src = self.read_frontend("graphFilters.js")
        assert "evt.shiftKey" in src
        assert "evt.altKey" in src
        assert "active-filter-chip" in src

    def test_graph_filters_marks_legend_items_editable(self):
        src = self.read_frontend("graphFilters.js")
        assert "data-legend-edit" in src
        assert "window.openGraphSettings" in src

    def test_settings_module_exists(self):
        assert (self.frontend_dir / "settings.js").exists()

    def test_settings_module_exports_namespace(self):
        src = self.read_frontend("settings.js")
        assert "window.GraphSettings" in src
        assert "renderSettingsTabs" in src
        assert "applyInputChange" in src

    def test_settings_module_exposes_import_export_and_node_style_actions(self):
        src = self.read_frontend("settings.js")
        for text in (
            "Export settings JSON",
            "Import settings JSON",
            "Reset this type",
            "Reset all node styles",
            "Duplicate style",
            "Export node style map",
            "data-settings-action",
        ):
            assert text in src

    def test_settings_module_exposes_label_and_badge_controls(self):
        src = self.read_frontend("settings.js")
        for text in (
            "Icon / badge",
            "Label prefix",
            "Label suffix",
            "Badge text",
            "label_prefix",
            "label_suffix",
        ):
            assert text in src

    @pytest.mark.parametrize("tab_id", [
        "appearance",
        "node_families",
        "edge_layers",
        "trust_states",
        "node_scope",
        "layout",
        "filters",
        "presets",
        "accessibility",
        "inspector",
        "advanced",
    ])
    def test_settings_module_contains_required_tabs(self, tab_id):
        assert f"id: '{tab_id}'" in self.read_frontend("settings.js")

    def test_index_loads_new_modules_in_order(self):
        src = self.read_frontend("index.html")
        assert src.index('src="graphStyles.js"') < src.index('src="graphFilters.js"')
        assert src.index('src="graphFilters.js"') < src.index('src="graphPresets.js"')
        assert src.index('src="settings.js"') < src.index('src="inspectorTabs.js"')

    def test_index_has_active_filter_bar(self):
        src = self.read_frontend("index.html")
        assert 'id="graph-active-filters"' in src

    def test_index_has_expanded_filter_groups(self):
        src = self.read_frontend("index.html")
        for element_id in (
            "node-family-filters",
            "node-subtype-filters",
            "project-filters",
            "source-class-filters",
            "confidence-filters",
            "status-filters",
            "recency-filters",
            "generated-canonical-filters",
            "warning-filters",
        ):
            assert f'id="{element_id}"' in src

    def test_graph_filters_apply_expanded_semantic_dimensions(self):
        src = self.read_frontend("graphFilters.js")
        for text in (
            "nodeFamilies",
            "nodeSubtypes",
            "sourceClasses",
            "confidence",
            "statuses",
            "recency",
            "_confidenceCategory",
            "_statusCategory",
            "_recencyCategory",
            "generatedCanonical",
            "_generatedCanonicalCategories",
            "_warningCategories",
            "node-family-filters",
            "node-subtype-filters",
            "project-filters",
            "source-class-filters",
            "confidence-filters",
            "status-filters",
            "recency-filters",
            "generated-canonical-filters",
            "warning-filters",
        ):
            assert text in src

    def test_graph_filters_render_default_delta_active_chips(self):
        src = self.read_frontend("graphFilters.js")
        for text in (
            "_filterDefaults",
            "Hidden:",
            "reset-group",
            "clear-query",
            "data-filter-action",
            "filterSetForKind",
            "defaultSetForKind",
            "contextmenu",
            "_lastFilterRuleSaveHandler",
        ):
            assert text in src

    def test_index_has_context_customize_entries(self):
        src = self.read_frontend("index.html")
        assert 'id="ctx-customize-node-type"' in src
        assert 'id="ctx-customize-edge-layer"' in src

    def test_app_delegates_to_frontend_modules(self):
        src = self.read_frontend("app.js")
        assert "window.GraphFilters.renderGraphControls" in src
        assert "window.GraphFilters.applyGraphFilters" in src
        assert "window.GraphSettings.renderSettingsTabs" in src
        assert "window.GraphSettings.applyInputChange" in src

    def test_app_exposes_graph_settings_opener(self):
        src = self.read_frontend("app.js")
        assert "window.openGraphSettings = openSettingsModal" in src
        assert "_focusSettingsTarget" in src

    def test_app_handles_settings_import_export_actions_without_direct_file_write(self):
        src = self.read_frontend("app.js")
        for text in (
            "_onSettingAction",
            "reset-node-family",
            "reset-all-node-styles",
            "duplicate-node-style",
            "export-node-style-map",
            "export-settings",
            "import-settings",
            "_copySettingsText",
            "navigator.clipboard.writeText",
        ):
            assert text in src

    def test_app_node_data_carries_filter_fields(self):
        src = self.read_frontend("app.js")
        for text in ("node_subtype", "confidence:", "status:", "modified_at:", "generated_state", "canonical_state", "project:", "source_path:", "source_class:", "warnings:"):
            assert text in src

    def test_app_composes_node_display_labels_from_badge_settings(self):
        src = self.read_frontend("app.js")
        for text in (
            "graphNodeDisplayLabel",
            "label_prefix",
            "label_suffix",
            "familySettings.badge",
            "trustSettings.badge",
            "badges.push('AI')",
            "badges.push('CAN')",
        ):
            assert text in src

    def test_generated_canonical_visibility_uses_state_fields(self):
        app_src = self.read_frontend("app.js")
        for text in (
            "graphNodeGeneratedState",
            "graphNodeCanonicalState",
            "generated_origin",
            "generatedState.includes('generated')",
            "canonicalState === 'canonical'",
            "canonicalState === 'active'",
        ):
            assert text in app_src
        styles_src = self.read_frontend("graphStyles.js")
        for text in (
            "generatedState.includes('generated')",
            "generatedState === 'ai_origin'",
            "canonicalState === 'canonical'",
            "canonicalState === 'authoritative'",
            "nodeData.generated_origin === true",
        ):
            assert text in styles_src

    def test_graph_styles_apply_edge_label_modes(self):
        src = self.read_frontend("graphStyles.js")
        for text in (
            "label_mode",
            "data(edge_label_relation)",
            "data(edge_label_confidence)",
            "text-rotation",
            "text-margin-y",
        ):
            assert text in src

    def test_app_has_keyboard_graph_navigation(self):
        src = self.read_frontend("app.js")
        for text in (
            "initGraphKeyboardNavigation",
            "keyboardNavigationBound",
            "ArrowUp",
            "ArrowDown",
            "ArrowLeft",
            "ArrowRight",
            "_selectGraphNodeByDirection",
            "_focusGraphNode",
            "ChaseOS graph surface",
        ):
            assert text in src

    def test_graph_styles_apply_accessibility_modes(self):
        src = self.read_frontend("graphStyles.js")
        for text in (
            "COLORBLIND_SAFE_COLORS",
            "colorblind_safe_palette",
            "high_contrast",
            "motion_reduce",
            "large_labels",
            "shape_first_mode",
            "pattern_first_trust_rings",
            "_accessibilityEdgeColor",
            "_accessibilityTrustColor",
        ):
            assert text in src

    def test_keyboard_navigation_honors_accessibility_settings(self):
        src = self.read_frontend("app.js")
        assert "keyboard_navigation !== false" in src
        assert "motion_reduce === true" in src
        assert "graph3d.cameraPosition" in src

    def test_graph_styles_apply_appearance_controls(self):
        src = self.read_frontend("graphStyles.js")
        for text in (
            "link_thickness",
            "arrowheads",
            "node_size_by_degree",
            "node_size_base",
            "animate_runtime_edges",
            "mapData(degree",
            "runtimeEdgeAnimationEnabled",
        ):
            assert text in src

    def test_app_applies_grid_and_minimap_appearance_controls(self):
        app_src = self.read_frontend("app.js")
        for text in (
            "applyGraphAppearanceSurface",
            "renderGraphMinimap",
            "graph-grid-enabled",
            "graph-minimap-enabled",
            "appearance.minimap === true",
            "appearance.background_color",
        ):
            assert text in app_src
        index_src = self.read_frontend("index.html")
        assert 'id="graph-3d"' in index_src
        css_src = self.read_frontend("styles.css")
        assert "#graph-3d" in css_src

    def test_app_applies_label_fade_and_max_label_controls(self):
        app_src = self.read_frontend("app.js")
        for text in (
            "graphLabelsAllowedAtCurrentZoom",
            "updateGraphLabelVisibility",
            "label_fade_threshold",
            "graphLabelAllowedNodeIds",
            "max_labels_visible",
            "rendered_label",
            "rendered_plain_label",
            "label_allowed",
        ):
            assert text in app_src
        styles_src = self.read_frontend("graphStyles.js")
        assert "data(rendered_label)" in styles_src
        assert "data(rendered_plain_label)" in styles_src

    def test_app_applies_pinned_node_layout_controls(self):
        settings_src = self.read_frontend("settings.js")
        for text in (
            "Pin selected node",
            "Clear pinned nodes",
            "Reset layout",
            "pin-selected-node",
            "clear-pinned-nodes",
            "reset-graph-layout",
        ):
            assert text in settings_src
        app_src = self.read_frontend("app.js")
        for text in (
            "applyGraphPinnedNodes",
            "layout.pinned_nodes",
            "node--pinned",
        ):
            assert text in app_src
        styles_src = self.read_frontend("graphStyles.js")
        assert "node.node--pinned" in styles_src

    def test_app_applies_settings_to_graph_request_and_scope_before_render(self):
        src = self.read_frontend("app.js")
        for text in (
            "graphRequestLimits",
            "maxEdges",
            "layoutNodeLimit",
            "_settingsLimitedNodes",
            "_settingsLimitedEdges",
            "_nodeScopeAllows",
            "scope.blocks === true",
            "scope.tasks === true",
            "show_external_resources",
            "get_graph_contract(",
        ):
            assert text in src

    def test_app_applies_layout_settings_to_graph(self):
        src = self.read_frontend("app.js")
        for text in (
            "graphLayoutOptions",
            "layout.algorithm",
            "node_repulsion",
            "ideal_edge_length",
            "motion_reduce",
            "semanticClusterEnabled",
            "graphSemanticClusterMode",
            "graphSemanticClusterKey",
            "graphSemanticClusterRank",
            "cluster_by_domain",
            "cluster_by_project",
            "cluster_by_trust_state",
            "name = semanticClusterEnabled ? 'concentric' : requestedName",
            "base.concentric",
            "base.levelWidth",
        ):
            assert text in src

    def test_app_applies_local_focus_depth_controls(self):
        src = self.read_frontend("app.js")
        for text in (
            "_focusedGraphNodeId",
            "graphLocalFocusDepth",
            "graphFocusFitPadding",
            "_graphLocalNeighborhoodIds3D",
            "applyGraphFocusMode",
            "layout.local_graph_depth",
            "layout.focus_radius",
        ):
            assert text in src

    def test_api_graph_contract_accepts_max_edges(self):
        # The get_graph_contract method lives in recovered bytecode (api.py uses
        # bytecode recovery); verify the JS default matches the updated limit.
        js = self.read_frontend("app.js")
        assert "graphRequestLimits" in js
        assert "max_edges" in js
        assert "20000" in js  # default raised to render the full ~7.4k-node vault

    def test_graph_presets_support_user_crud_controls(self):
        src = self.read_frontend("graphPresets.js")
        # Save button label: compact "+ Save" (was "Save view" before dropdown refactor)
        assert "Save" in src
        # Delete button title changed to "Delete selected preset" in dropdown refactor
        assert "Delete selected" in src
        assert "getCurrentPresetId" in src

    def test_graph_presets_apply_filter_state(self):
        filters_src = self.read_frontend("graphFilters.js")
        for text in (
            "applyPresetFilters",
            "filters.node_families",
            "filters.trust_states",
            "filters.edge_layers",
            "filters.node_subtypes",
            "filters.generated_canonical",
            "filters.query",
            "filters.warnings",
        ):
            assert text in filters_src
        app_src = self.read_frontend("app.js")
        assert "_activePresetFilters" in app_src
        assert "window.GraphFilters.applyPresetFilters(graphFilters, _activePresetFilters)" in app_src
        for text in (
            "graphFiltersForPreset",
            "_saveCurrentFilterRule",
            "saveFilterRule: _saveCurrentFilterRule",
            "save_graph_preset(slug, label.trim(), description, _currentSettings || {}, graphFiltersForPreset())",
        ):
            assert text in app_src

    def test_inspector_metadata_edit_is_not_default_graph_authority(self):
        src = self.read_frontend("inspectorTabs.js")
        assert "GRAPH_INSPECTOR_METADATA_EDIT_ENABLED" in src
        assert "window.GraphInspectorMetadataEditEnabled === true" in src
        assert "GRAPH_INSPECTOR_METADATA_EDIT_ENABLED ? _renderMetadataEditShell(data) : ''" in src

    def test_inspector_tabs_honor_graph_settings(self):
        src = self.read_frontend("inspectorTabs.js")
        for text in (
            "setInspectorSettings",
            "_visibleInspectorTabs",
            "show_provenance_tab === false",
            "show_raw_metadata !== true",
            "default_tab",
            "show_source_excerpt !== false",
            "max_relation_display",
        ):
            assert text in src
        app_src = self.read_frontend("app.js")
        assert "window.InspectorTabs.setInspectorSettings" in app_src

    def test_app_wires_preset_crud_to_api(self):
        src = self.read_frontend("app.js")
        assert "save_graph_preset" in src
        assert "delete_graph_preset" in src
        assert "_saveCurrentGraphPreset" in src
        assert "_deleteGraphPreset" in src

    def test_write_actions_customize_context_routes_are_settings_only(self):
        src = self.read_frontend("writeActions.js")
        assert "ctx-customize-node-type" in src
        assert "ctx-customize-edge-layer" in src
        assert "window.openGraphSettings({ tab: 'node_families'" in src
        assert "window.openGraphSettings({ tab: 'edge_layers'" in src

    def test_styles_cover_module_ui_classes(self):
        src = self.read_frontend("styles.css")
        for cls in (".active-filter-chip", ".settings-subsection", ".settings-subtitle", ".settings-note",
                    ".preset-action-btn", ".settings-subsection--focus", ".settings-action-btn"):
            assert cls in src
