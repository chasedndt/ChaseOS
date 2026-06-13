"""Tests for Pass 10G — Intake/Quarantine Panel.

Covers:
- API method get_intake_panel() returns correct envelope
- Empty quarantine → empty items list, not an error
- Items populated from list_quarantine_provenance
- JS panel wired in index.html
- CSS present in styles.css
- JS functions present in app.js
- Promote-from-quarantine API method exists and routes through service
- Filter by input_class passes through
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SHELL = Path(__file__).resolve().parent
_FRONTEND = _SHELL / "frontend"
_VAULT = _SHELL.parents[2]


# ── TestAPIGetIntakePanel ──────────────────────────────────────────────────────

class TestAPIGetIntakePanel:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(vault_root))
        return api

    def test_returns_ok_envelope_empty_quarantine(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_intake_panel()
        assert result["ok"] is True
        assert result["surface"] == "intake_panel"
        assert "data" in result
        data = result["data"]
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["items"] == []

    def test_result_count_zero_when_empty(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_intake_panel()
        assert result["data"]["result_count"] == 0

    def test_dedup_stats_present(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_intake_panel()
        assert "dedup_stats" in result["data"]

    def test_items_populated_with_quarantine_content(self, tmp_path):
        quarantine_dir = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "source"
        quarantine_dir.mkdir(parents=True)
        content_file = quarantine_dir / "test_article.txt"
        content_file.write_text("article content", encoding="utf-8")
        sidecar = {
            "capture_id": "test-001",
            "content_filename": "test_article.txt",
            "input_class": "source",
            "source_platform": "web",
            "captured_at": "2026-05-06T10:00:00Z",
            "title": "Test Article",
            "content_sha256": "abc123def456",
            "injection_scan": "not-scanned",
            "promotion_status": "pending",
        }
        (quarantine_dir / "test_article.txt.meta.json").write_text(
            json.dumps(sidecar), encoding="utf-8"
        )
        api = self._make_api(tmp_path)
        result = api.get_intake_panel()
        assert result["ok"] is True
        items = result["data"]["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Test Article"
        assert items[0]["input_class"] == "source"

    def test_filter_by_input_class(self, tmp_path):
        quarantine_dir = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "source"
        quarantine_dir.mkdir(parents=True)
        for cls, name in [("source", "src.txt"), ("digest", "dig.txt")]:
            d = tmp_path / "03_INPUTS" / "00_QUARANTINE" / cls
            d.mkdir(parents=True, exist_ok=True)
            (d / name).write_text("content", encoding="utf-8")
            (d / f"{name}.meta.json").write_text(json.dumps({
                "content_filename": name,
                "input_class": cls,
                "injection_scan": "not-scanned",
                "promotion_status": "pending",
            }), encoding="utf-8")

        api = self._make_api(tmp_path)
        result = api.get_intake_panel(input_class="source")
        items = result["data"]["items"]
        assert all(i.get("input_class") == "source" for i in items)

    def test_limit_parameter_respected(self, tmp_path):
        quarantine_dir = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "source"
        quarantine_dir.mkdir(parents=True)
        for i in range(10):
            f = f"item{i:02d}.txt"
            (quarantine_dir / f).write_text(f"content {i}", encoding="utf-8")
            (quarantine_dir / f"{f}.meta.json").write_text(json.dumps({
                "content_filename": f,
                "input_class": "source",
                "injection_scan": "not-scanned",
                "promotion_status": "pending",
            }), encoding="utf-8")

        api = self._make_api(tmp_path)
        result = api.get_intake_panel(limit=3)
        assert len(result["data"]["items"]) <= 3

    def test_envelope_shape(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_intake_panel()
        for key in ("ok", "status", "surface", "data", "warnings", "blocked_authority"):
            assert key in result


# ── TestIntakeHTMLStructure ────────────────────────────────────────────────────

class TestIntakeHTMLStructure:
    def _html(self):
        return (_FRONTEND / "index.html").read_text(encoding="utf-8")

    def test_sidebar_intake_button(self):
        html = self._html()
        assert 'data-panel="intake"' in html

    def test_sidebar_intake_title(self):
        html = self._html()
        assert 'title="Intake - review new captures"' in html

    def test_productized_intake_header(self):
        html = self._html()
        assert "<h2>Intake</h2>" in html
        assert "Duplicate protection" in html
        assert "No automatic filing" in html

    def test_panel_intake_section(self):
        html = self._html()
        assert 'id="panel-intake"' in html

    def test_intake_body_element(self):
        html = self._html()
        assert 'id="intake-body"' in html

    def test_intake_filter_select(self):
        html = self._html()
        assert 'id="intake-class-filter"' in html

    def test_intake_search_input(self):
        html = self._html()
        assert 'id="intake-search-filter"' in html

    def test_intake_refresh_btn(self):
        html = self._html()
        assert 'id="intake-refresh-btn"' in html

    def test_intake_stats_row(self):
        html = self._html()
        assert 'id="intake-stats-row"' in html

    def test_panel_read_only_marker(self):
        html = self._html()
        import re
        panel_match = re.search(r'id="panel-intake"[^>]*>', html)
        assert panel_match is not None
        assert 'data-read-only="true"' in panel_match.group(0)


# ── TestIntakeCSS ──────────────────────────────────────────────────────────────

class TestIntakeCSS:
    def _css(self):
        return (_FRONTEND / "styles.css").read_text(encoding="utf-8")

    def test_intake_panel_class(self):
        assert ".intake-panel" in self._css()

    def test_intake_item_class(self):
        assert ".intake-item" in self._css()

    def test_intake_trust_badge(self):
        assert ".intake-trust-badge" in self._css()

    def test_intake_meta_tag(self):
        assert ".intake-meta-tag" in self._css()

    def test_intake_promote_btn(self):
        assert ".intake-promote-btn" in self._css()

    def test_trust_state_classes(self):
        css = self._css()
        for cls in (".ts-promoted", ".ts-quarantined", ".ts-disputed", ".ts-suggested", ".ts-raw"):
            assert cls in css


# ── TestIntakeJS ───────────────────────────────────────────────────────────────

class TestIntakeJS:
    def _js(self):
        return (_FRONTEND / "app.js").read_text(encoding="utf-8")

    def test_load_intake_function(self):
        assert "async function loadIntake(" in self._js()

    def test_render_intake_panel_function(self):
        assert "function renderIntakePanel(" in self._js()

    def test_init_intake_panel_function(self):
        assert "function _initIntakePanel(" in self._js()

    def test_intake_panel_switch(self):
        assert "if (id === 'intake') runPanelLoader(loadIntake);" in self._js()

    def test_intake_init_called_on_ready(self):
        assert "_initIntakePanel();" in self._js()

    def test_quarantine_file_watcher_route(self):
        assert "isQuarantine" in self._js()
        assert "00_QUARANTINE" in self._js()

    def test_get_intake_panel_api_call(self):
        assert "get_intake_panel" in self._js()

    def test_promote_from_quarantine_wired(self):
        assert "promote_from_quarantine" in self._js()

    def test_intake_approval_path_builder_present(self):
        js = self._js()
        assert "function _intakeApprovalPath(" in js
        assert "03_INPUTS/00_QUARANTINE" in js

    def test_intake_approval_detail_is_productized(self):
        js = self._js()
        assert "function _intakeApprovalDetail(" in js
        assert "function _intakeApprovalModalPayload(" in js
        assert "Request approval to file" in js
        assert "File capture into knowledge base" in js

    def test_intake_promote_btn_click(self):
        assert "intake-promote-btn" in self._js()

    def test_intake_loaded_flag(self):
        assert "intakeLoaded" in self._js()


# ── TestAPIPromoteFromQuarantine ──────────────────────────────────────────────

class TestAPIPromoteFromQuarantine:
    def test_promote_from_quarantine_exists(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "promote_from_quarantine")
        assert callable(StudioAPI.promote_from_quarantine)

    def test_promote_requires_approval(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(tmp_path))
        result = api.promote_from_quarantine("nonexistent.txt")
        assert result["ok"] is False
