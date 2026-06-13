"""Pass 10V â€” Role Cards Panel tests.

Covers:
- get_role_cards() API method
- get_role_card_detail() API method
- path-traversal guard
- _* file exclusion (schema files)
- parsed field extraction (id/name/version/owner/counts)
- panel_registry.py role-cards panel entry
- readiness keys
- HTML panel structure
- sidebar button
- CSS classes
- JS functions
- panel switch wiring
- init wiring
"""

from __future__ import annotations

import re
from pathlib import Path
import sys

import pytest

VAULT = Path(__file__).resolve().parents[3]
SHELL = Path(__file__).resolve().parent
sys.path.insert(0, str(VAULT))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def api(tmp_path):
    from runtime.studio.shell.api import StudioAPI
    cards_dir = tmp_path / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    (cards_dir / "operator-briefing.yaml").write_text(
        "id: operator-briefing\n"
        "name: Operator Briefing Role\n"
        "version: '1.0'\n"
        "owner: openclaw\n"
        "description: Briefing writer role card\n"
        "allowed_actions:\n"
        "  - read_now_md\n"
        "  - write_daily_log\n"
        "forbidden_actions:\n"
        "  - delete_vault_files\n"
        "  - canonical_write\n"
        "  - modify_protected\n"
        "write_scope:\n"
        "  - 07_LOGS/Daily/\n",
        encoding="utf-8",
    )
    (cards_dir / "vault-maintenance.yaml").write_text(
        "id: vault-maintenance\n"
        "name: Vault Maintenance\n"
        "version: '1.1'\n"
        "owner: openclaw\n"
        "description: Vault hygiene role\n"
        "allowed_actions:\n"
        "  - graduate_ideas\n"
        "forbidden_actions:\n"
        "  - delete_files\n"
        "write_scope:\n"
        "  - 02_KNOWLEDGE/\n"
        "  - 01_PROJECTS/\n",
        encoding="utf-8",
    )
    (cards_dir / "_schema.yaml").write_text("schema: true\n", encoding="utf-8")
    return StudioAPI(str(tmp_path))


@pytest.fixture()
def registry(tmp_path):
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
    return build_native_shell_panel_registry(str(tmp_path))


@pytest.fixture()
def html_text():
    return (SHELL / "frontend" / "index.html").read_text(encoding="utf-8")


@pytest.fixture()
def css_text():
    return (SHELL / "frontend" / "styles.css").read_text(encoding="utf-8")


@pytest.fixture()
def js_text():
    return (SHELL / "frontend" / "app.js").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# API: get_role_cards
# ---------------------------------------------------------------------------


class TestGetRoleCards:
    def test_ok_true(self, api):
        r = api.get_role_cards()
        assert r["ok"] is True

    def test_surface(self, api):
        r = api.get_role_cards()
        assert r["surface"] == "role_cards"

    def test_returns_role_cards_list(self, api):
        r = api.get_role_cards()
        assert isinstance(r["data"]["role_cards"], list)

    def test_count_excludes_schema(self, api):
        r = api.get_role_cards()
        assert r["data"]["role_card_count"] == 2

    def test_schema_file_excluded(self, api):
        r = api.get_role_cards()
        ids = [c["filename"] for c in r["data"]["role_cards"]]
        assert "_schema.yaml" not in ids

    def test_card_has_filename(self, api):
        r = api.get_role_cards()
        for card in r["data"]["role_cards"]:
            assert "filename" in card

    def test_card_has_id(self, api):
        r = api.get_role_cards()
        ids = {c["id"] for c in r["data"]["role_cards"]}
        assert "operator-briefing" in ids

    def test_card_has_name(self, api):
        r = api.get_role_cards()
        names = {c["name"] for c in r["data"]["role_cards"]}
        assert "Operator Briefing Role" in names

    def test_card_has_version(self, api):
        r = api.get_role_cards()
        ob = next(c for c in r["data"]["role_cards"] if c["id"] == "operator-briefing")
        assert ob["version"] == "1.0"

    def test_card_has_owner(self, api):
        r = api.get_role_cards()
        ob = next(c for c in r["data"]["role_cards"] if c["id"] == "operator-briefing")
        assert ob["owner"] == "openclaw"

    def test_allowed_action_count(self, api):
        r = api.get_role_cards()
        ob = next(c for c in r["data"]["role_cards"] if c["id"] == "operator-briefing")
        assert ob["allowed_action_count"] == 2

    def test_forbidden_action_count(self, api):
        r = api.get_role_cards()
        ob = next(c for c in r["data"]["role_cards"] if c["id"] == "operator-briefing")
        assert ob["forbidden_action_count"] == 3

    def test_write_scope_count(self, api):
        r = api.get_role_cards()
        ob = next(c for c in r["data"]["role_cards"] if c["id"] == "operator-briefing")
        assert ob["write_scope_count"] == 1

    def test_vault_maintenance_card_present(self, api):
        r = api.get_role_cards()
        ids = {c["id"] for c in r["data"]["role_cards"]}
        assert "vault-maintenance" in ids

    def test_vault_maintenance_write_scope(self, api):
        r = api.get_role_cards()
        vm = next(c for c in r["data"]["role_cards"] if c["id"] == "vault-maintenance")
        assert vm["write_scope_count"] == 2

    def test_no_cards_dir(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        r = StudioAPI(str(tmp_path)).get_role_cards()
        assert r["ok"] is True
        assert r["data"]["role_card_count"] == 0

    def test_no_cards_dir_warning(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        r = StudioAPI(str(tmp_path)).get_role_cards()
        assert r.get("warnings") is not None

    def test_size_bytes_present(self, api):
        r = api.get_role_cards()
        for card in r["data"]["role_cards"]:
            assert isinstance(card["size_bytes"], int)

    def test_cards_dir_in_data(self, api):
        r = api.get_role_cards()
        assert "cards_dir" in r["data"]

    def test_role_card_count_matches_list(self, api):
        r = api.get_role_cards()
        assert r["data"]["role_card_count"] == len(r["data"]["role_cards"])


# ---------------------------------------------------------------------------
# API: get_role_card_detail
# ---------------------------------------------------------------------------


class TestGetRoleCardDetail:
    def test_ok_true(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["ok"] is True

    def test_surface(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["surface"] == "role_card_detail"

    def test_raw_content_present(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert "raw_content" in r["data"]
        assert "operator-briefing" in r["data"]["raw_content"]

    def test_parsed_id(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["data"]["id"] == "operator-briefing"

    def test_parsed_name(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["data"]["name"] == "Operator Briefing Role"

    def test_parsed_version(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["data"]["version"] == "1.0"

    def test_parsed_owner(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["data"]["owner"] == "openclaw"

    def test_parsed_allowed_count(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["data"]["allowed_action_count"] == 2

    def test_parsed_forbidden_count(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["data"]["forbidden_action_count"] == 3

    def test_parsed_write_scope_count(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert r["data"]["write_scope_count"] == 1

    def test_size_bytes(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert isinstance(r["data"]["size_bytes"], int)
        assert r["data"]["size_bytes"] > 0

    def test_line_count(self, api):
        r = api.get_role_card_detail("operator-briefing.yaml")
        assert isinstance(r["data"]["line_count"], int)
        assert r["data"]["line_count"] > 0

    def test_not_found(self, api):
        r = api.get_role_card_detail("nonexistent.yaml")
        assert r["ok"] is False
        assert r["error"]["code"] == "not_found"

    def test_path_traversal_blocked(self, api):
        r = api.get_role_card_detail("../CLAUDE.md")
        assert r["ok"] is False

    def test_path_traversal_slash(self, api):
        r = api.get_role_card_detail("sub/dir/file.yaml")
        assert r["ok"] is False

    def test_path_traversal_backslash(self, api):
        r = api.get_role_card_detail("sub\\file.yaml")
        assert r["ok"] is False

    def test_non_yaml_extension_blocked(self, api):
        r = api.get_role_card_detail("operator-briefing.json")
        assert r["ok"] is False
        assert r["error"]["code"] == "invalid_filename"

    def test_schema_file_blocked(self, api):
        r = api.get_role_card_detail("_schema.yaml")
        assert r["ok"] is False
        assert r["error"]["code"] == "schema_file"

    def test_empty_filename_blocked(self, api):
        r = api.get_role_card_detail("")
        assert r["ok"] is False

    def test_vault_maintenance_detail(self, api):
        r = api.get_role_card_detail("vault-maintenance.yaml")
        assert r["ok"] is True
        assert r["data"]["write_scope_count"] == 2


# ---------------------------------------------------------------------------
# Panel Registry
# ---------------------------------------------------------------------------


class TestPanelRegistry:
    def test_role_cards_panel_present(self, registry):
        ids = [p["id"] for p in registry["panels"]]
        assert "role-cards" in ids

    def test_role_cards_status_mounted(self, registry):
        panel = next(p for p in registry["panels"] if p["id"] == "role-cards")
        assert panel["status"] == "mounted"

    def test_role_cards_api_methods(self, registry):
        panel = next(p for p in registry["panels"] if p["id"] == "role-cards")
        assert "get_role_cards" in panel["api_methods"]
        assert "get_role_card_detail" in panel["api_methods"]

    def test_role_cards_read_only(self, registry):
        panel = next(p for p in registry["panels"] if p["id"] == "role-cards")
        assert panel["read_only"] is True

    def test_role_cards_canonical_mutation_blocked(self, registry):
        panel = next(p for p in registry["panels"] if p["id"] == "role-cards")
        assert panel["blocked_authority"]["canonical_mutation"] is False

    def test_role_cards_readiness_key(self, registry):
        assert registry["readiness"]["role_cards_panel_mounted"] is True

    def test_next_pass_advanced(self, registry):
        nxt = registry["readiness"]["next_recommended_pass"]
        assert nxt == "ventureops-operator-readiness-gate"
        assert "role-cards" not in nxt

    def test_declared_count_includes_role_cards(self, registry):
        assert registry["readiness"]["declared_panel_count"] >= 27

    def test_mounted_count_includes_role_cards(self, registry):
        assert registry["readiness"]["mounted_panel_count"] >= 27


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------


class TestHTML:
    def test_sidebar_button_present(self, html_text):
        assert "panel-role-cards" in html_text

    def test_sidebar_button_label(self, html_text):
        assert "[Z]" in html_text or "role-cards" in html_text

    def test_panel_div_present(self, html_text):
        assert 'id="panel-role-cards"' in html_text

    def test_search_input_present(self, html_text):
        assert 'id="role-cards-search"' in html_text

    def test_list_div_present(self, html_text):
        assert 'id="role-cards-list"' in html_text

    def test_viewer_div_present(self, html_text):
        assert 'id="role-cards-viewer"' in html_text

    def test_viewer_title_present(self, html_text):
        assert 'id="role-cards-viewer-title"' in html_text

    def test_viewer_close_present(self, html_text):
        assert 'id="role-cards-viewer-close"' in html_text

    def test_viewer_content_present(self, html_text):
        assert 'id="role-cards-viewer-content"' in html_text

    def test_read_only_kicker(self, html_text):
        assert "READ-ONLY" in html_text or "read-only" in html_text.lower()


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------


class TestCSS:
    def test_role_cards_panel_class(self, css_text):
        assert ".role-cards-panel" in css_text

    def test_role_cards_toolbar_class(self, css_text):
        assert ".role-cards-toolbar" in css_text

    def test_role_card_item_class(self, css_text):
        assert ".role-card-item" in css_text

    def test_role_card_item_active_class(self, css_text):
        assert ".role-card-item--active" in css_text

    def test_role_cards_viewer_class(self, css_text):
        assert ".role-cards-viewer" in css_text

    def test_role_card_raw_class(self, css_text):
        assert ".role-card-raw" in css_text

    def test_role_card_detail_summary_class(self, css_text):
        assert ".role-card-detail-summary" in css_text


# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------


class TestJS:
    def test_load_role_cards_function(self, js_text):
        assert "async function loadRoleCards" in js_text

    def test_render_role_card_list_function(self, js_text):
        assert "function renderRoleCardList" in js_text

    def test_load_role_card_detail_function(self, js_text):
        assert "async function loadRoleCardDetail" in js_text

    def test_init_role_cards_panel_function(self, js_text):
        assert "function _initRoleCardsPanel" in js_text

    def test_role_cards_loaded_var(self, js_text):
        assert "roleCardsLoaded" in js_text

    def test_role_cards_all_var(self, js_text):
        assert "_roleCardsAll" in js_text

    def test_panel_switch_wired(self, js_text):
        assert "if (id === 'role-cards') loadRoleCards()" in js_text

    def test_init_called_in_on_shell_ready(self, js_text):
        assert "_initRoleCardsPanel()" in js_text

    def test_get_role_cards_api_call(self, js_text):
        assert "get_role_cards" in js_text

    def test_get_role_card_detail_api_call(self, js_text):
        assert "get_role_card_detail" in js_text

    def test_role_cards_use_product_labels(self, js_text):
        assert "function roleCardDisplayName" in js_text
        assert "roleCardSafeText" in js_text
        assert "Allowed ${escHtml(card.allowed_action_count || 0)}" in js_text

    def test_role_card_detail_no_longer_renders_raw_yaml(self, js_text):
        assert "content.innerHTML = renderRoleCardDetailSummary(d || {})" in js_text
        assert "content.textContent = d.raw_content" not in js_text

    def test_esc_attr_used_in_render(self, js_text):
        assert "escAttr" in js_text

    def test_role_cards_viewer_close_handler(self, js_text):
        assert "role-cards-viewer-close" in js_text
