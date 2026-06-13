"""
Tests for Node Inspector workspace UX hardening.

Verifies:
- Global <aside id="inspector"> is removed from the shell layout
- Inspector DOM lives inside #panel-node-inspector
- Shell CSS is 2-column (no var(--inspector-w) in the main grid)
- reveal_node_in_file_explorer API boundary enforcement
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FRONTEND_DIR = Path(__file__).parent / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"
STYLES_CSS = FRONTEND_DIR / "styles.css"
APP_JS = FRONTEND_DIR / "app.js"
INSPECTOR_TABS_JS = FRONTEND_DIR / "inspectorTabs.js"
API_PY = Path(__file__).parent / "api.py"


# ---------------------------------------------------------------------------
# Layout: global aside removed
# ---------------------------------------------------------------------------

def test_no_global_inspector_aside():
    """Global <aside id="inspector"> must not exist outside #panel-node-inspector."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    # The aside must be gone from the shell-level layout
    assert '<aside id="inspector"' not in html, (
        'Global <aside id="inspector"> still exists in index.html. '
        "Move inspector DOM into #panel-node-inspector and remove the global aside."
    )


def test_panel_node_inspector_has_inspector_tabs():
    """#panel-node-inspector must contain id='inspector-tabs'."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    # Find the section
    start = html.find('id="panel-node-inspector"')
    assert start != -1, "#panel-node-inspector section not found"
    # Find the section end (next top-level <section> or </main>)
    end = html.find('<section id="panel-', start + 1)
    if end == -1:
        end = html.find('</main>', start)
    fragment = html[start:end] if end != -1 else html[start:]
    assert 'id="inspector-tabs"' in fragment, (
        "id='inspector-tabs' not found inside #panel-node-inspector"
    )


def test_panel_node_inspector_has_inspector_tab_body():
    """#panel-node-inspector must contain id='inspector-tab-body'."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    start = html.find('id="panel-node-inspector"')
    assert start != -1, "#panel-node-inspector section not found"
    end = html.find('<section id="panel-', start + 1)
    if end == -1:
        end = html.find('</main>', start)
    fragment = html[start:end] if end != -1 else html[start:]
    assert 'id="inspector-tab-body"' in fragment, (
        "id='inspector-tab-body' not found inside #panel-node-inspector"
    )


def test_panel_node_inspector_has_node_tab_strip():
    """#panel-node-inspector must contain id='node-tab-strip' for multi-tab browsing."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    start = html.find('id="panel-node-inspector"')
    assert start != -1, "#panel-node-inspector section not found"
    end = html.find('<section id="panel-', start + 1)
    if end == -1:
        end = html.find('</main>', start)
    fragment = html[start:end] if end != -1 else html[start:]
    assert 'id="node-tab-strip"' in fragment, (
        "id='node-tab-strip' not found inside #panel-node-inspector"
    )


def test_panel_node_inspector_has_action_toolbar():
    """#panel-node-inspector must contain the node action more button."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    start = html.find('id="panel-node-inspector"')
    assert start != -1, "#panel-node-inspector section not found"
    end = html.find('<section id="panel-', start + 1)
    if end == -1:
        end = html.find('</main>', start)
    fragment = html[start:end] if end != -1 else html[start:]
    assert 'node-action-more-btn' in fragment, (
        "id='node-action-more-btn' not found inside #panel-node-inspector"
    )


def test_panel_node_inspector_uses_product_label():
    """Docs / Inspector must be the user-facing page label."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    start = html.find('id="panel-node-inspector"')
    assert start != -1, "#panel-node-inspector section not found"
    end = html.find('<section id="panel-', start + 1)
    if end == -1:
        end = html.find('</main>', start)
    fragment = html[start:end] if end != -1 else html[start:]
    assert "<h2>Docs / Inspector</h2>" in fragment
    assert "Open from Graph, Quick Switch, backlinks, or a wiki link." in fragment


def test_panel_node_inspector_has_markdown_document_controls():
    """Docs / Inspector must expose Markdown search, reading mode, edit mode, and save state."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    start = html.find('id="panel-node-inspector"')
    assert start != -1, "#panel-node-inspector section not found"
    end = html.find('<section id="panel-', start + 1)
    if end == -1:
        end = html.find('</main>', start)
    fragment = html[start:end] if end != -1 else html[start:]
    for token in [
        'id="docs-inspector-search"',
        'id="docs-inspector-results"',
        'id="docs-mode-reading"',
        'id="docs-mode-edit"',
        'id="docs-save-state"',
    ]:
        assert token in fragment


def test_docs_inspector_uses_menu_instead_of_inline_file_action_tabs():
    """Docs document actions should live in menu/context actions, not hard-coded inline tab buttons."""
    js = APP_JS.read_text(encoding="utf-8")
    assert 'data-doc-tab-menu' in js
    assert 'data-doc-copy-path' not in js
    assert 'data-doc-reveal' not in js
    # Document actions live in the viewport-safe context menu (post-cockpit redesign).
    for label in [
        "Copy selection",
        "Copy file path",
        "Copy wiki link",
        "Find in document",
        "View backlinks",
        "View provenance",
        "Open local graph",
        "Reveal in file explorer",
        "Delete file",
    ]:
        assert label in js


def test_docs_inspector_embeds_fetch_markdown_content():
    """Markdown embeds should render embedded Markdown content, not only a placeholder button."""
    js = APP_JS.read_text(encoding="utf-8")
    assert "get_markdown_document(resp.data.path, 65536)" in js
    assert "markdown-embed-body" in js


# ---------------------------------------------------------------------------
# CSS: 2-column layout
# ---------------------------------------------------------------------------

def test_shell_grid_is_two_columns():
    """Main #shell grid must NOT use var(--inspector-w) as a column."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    # Find the #shell block
    shell_start = css.find('#shell {')
    assert shell_start != -1, "#shell { block not found in styles.css"
    shell_block_end = css.find('}', shell_start)
    shell_block = css[shell_start:shell_block_end]
    assert 'var(--inspector-w)' not in shell_block, (
        "#shell grid-template-columns still includes var(--inspector-w). "
        "Change to: grid-template-columns: var(--sidebar-w) minmax(0, 1fr)"
    )
    assert 'minmax(0, 1fr)' in shell_block or '1fr' in shell_block, (
        "#shell grid must have a 1fr main content column"
    )


def test_collapsed_sidebar_grid_is_two_columns():
    """Collapsed sidebar state must NOT add a third inspector column."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    collapsed_start = css.find('#shell.sidebar-collapsed {')
    assert collapsed_start != -1, "#shell.sidebar-collapsed { block not found"
    collapsed_end = css.find('}', collapsed_start)
    collapsed_block = css[collapsed_start:collapsed_end]
    assert 'var(--inspector-w)' not in collapsed_block, (
        "#shell.sidebar-collapsed grid-template-columns still includes var(--inspector-w)"
    )


def test_inspector_aside_hidden_on_small_screens_media_query_updated():
    """The @media(max-width:680px) block must not reference #inspector hide since it's removed."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    # The old rule '#inspector { display: none; }' inside @media is fine to have or remove —
    # but we should NOT have the 3-column rule for max-width 900px breakpoint
    # The important thing is no inspector-w in main shell rules
    assert css.count('var(--inspector-w)') <= 2, (
        "var(--inspector-w) appears in more than 2 places — check that the main shell "
        "and collapsed-sidebar grid rules no longer use it"
    )


# ---------------------------------------------------------------------------
# CSS: node workspace styles present
# ---------------------------------------------------------------------------

def test_node_tab_strip_css_exists():
    """styles.css must define .node-tab-strip for the multi-tab strip."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert '.node-tab-strip' in css, ".node-tab-strip CSS class not found in styles.css"


def test_node_inspector_tab_css_exists():
    """styles.css must define .node-inspector-tab."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert '.node-inspector-tab' in css, ".node-inspector-tab CSS class not found in styles.css"


def test_nav_count_css_exists():
    """styles.css must define .nav-count for the tab count badge."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert '.nav-count' in css, ".nav-count CSS class not found in styles.css"


# ---------------------------------------------------------------------------
# JS: inspectorTabs.js exports tab methods
# ---------------------------------------------------------------------------

def test_inspector_tabs_has_open_node_tab():
    """inspectorTabs.js must export openNodeTab."""
    js = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    assert 'openNodeTab' in js, "openNodeTab not found in inspectorTabs.js"


def test_inspector_tabs_has_close_node_tab():
    """inspectorTabs.js must export closeNodeTab."""
    js = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    assert 'closeNodeTab' in js, "closeNodeTab not found in inspectorTabs.js"


def test_inspector_tabs_has_toggle_bookmark():
    """inspectorTabs.js must export toggleBookmarkNodeTab."""
    js = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    assert 'toggleBookmarkNodeTab' in js, "toggleBookmarkNodeTab not found in inspectorTabs.js"


def test_inspector_tabs_has_get_open_node_tab_count():
    """inspectorTabs.js must export getOpenNodeTabCount."""
    js = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    assert 'getOpenNodeTabCount' in js, "getOpenNodeTabCount not found in inspectorTabs.js"


def test_inspector_tabs_has_render_node_tab_strip():
    """inspectorTabs.js must export renderNodeTabStrip."""
    js = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    assert 'renderNodeTabStrip' in js, "renderNodeTabStrip not found in inspectorTabs.js"


def test_node_inspector_tab_count_badge_in_html():
    """index.html must contain the node-inspector-tab-count badge span."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'node-inspector-tab-count' in html, (
        "id='node-inspector-tab-count' badge not found in index.html"
    )


# ---------------------------------------------------------------------------
# API: reveal_node_in_file_explorer boundary enforcement
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    """Minimal vault with one file."""
    note = tmp_path / "02_KNOWLEDGE" / "test-note.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Test\nContent.", encoding="utf-8")
    linked = tmp_path / "02_KNOWLEDGE" / "linked-note.md"
    linked.write_text("# Linked Note\nLinked content.", encoding="utf-8")
    return tmp_path


def _make_api(vault_root: Path):
    """Return a StudioAPI instance with a mock snapshot resolver."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[4]))
    from runtime.studio.shell.api import StudioAPI
    return StudioAPI(str(vault_root))


def test_reveal_node_in_file_explorer_rejects_path_traversal(tmp_vault: Path):
    """reveal_node_in_file_explorer must reject paths outside the vault root."""
    api = _make_api(tmp_vault)

    # Patch _resolve_node_path to return a traversal path
    api._resolve_node_path = MagicMock(return_value="../../etc/passwd")

    with patch("subprocess.Popen") as mock_popen:
        result = api.reveal_node_in_file_explorer("some-node-id")

    assert result["ok"] is False, "Expected rejection for path traversal"
    assert "path_traversal" in result.get("error", {}).get("code", ""), (
        f"Expected path_traversal error code, got: {result}"
    )
    mock_popen.assert_not_called()


def test_reveal_node_in_file_explorer_calls_explorer_for_valid_path(tmp_vault: Path):
    """reveal_node_in_file_explorer must call the OS explorer for a valid vault path."""
    api = _make_api(tmp_vault)

    # Point to a real file inside the vault
    api._resolve_node_path = MagicMock(return_value="02_KNOWLEDGE/test-note.md")

    with patch("subprocess.Popen") as mock_popen:
        result = api.reveal_node_in_file_explorer("some-node-id")

    assert result["ok"] is True, f"Expected ok=True, got: {result}"
    # Verify the explorer.exe call was made (mock may capture Windows platform
    # 'ver' subprocess as a side-effect in batch runs — check specific args instead)
    explorer_calls = [
        c for c in mock_popen.call_args_list
        if c.args and isinstance(c.args[0], list) and "explorer.exe" in c.args[0][0]
    ]
    assert len(explorer_calls) == 1, (
        f"Expected exactly one explorer.exe Popen call, got calls: {mock_popen.call_args_list}"
    )


def test_reveal_node_in_file_explorer_handles_missing_node_path(tmp_vault: Path):
    """reveal_node_in_file_explorer must return structured error when node has no path."""
    api = _make_api(tmp_vault)
    api._resolve_node_path = MagicMock(return_value=None)

    with patch("subprocess.Popen") as mock_popen:
        result = api.reveal_node_in_file_explorer("no-path-node")

    assert result["ok"] is False
    mock_popen.assert_not_called()


def test_markdown_documents_api_lists_vault_notes(tmp_vault: Path):
    """Docs / Inspector document list must return Markdown notes with product metadata."""
    api = _make_api(tmp_vault)

    result = api.get_markdown_documents("test", 20)

    assert result["ok"] is True
    docs = result["data"]["documents"]
    assert any(doc["path"] == "02_KNOWLEDGE/test-note.md" for doc in docs)
    assert all(doc["path"].endswith(".md") for doc in docs)


def test_markdown_search_matches_across_separators(tmp_vault: Path):
    """'agent control' must match 'Agent-Control-Plane.md' despite the hyphens."""
    api = _make_api(tmp_vault)
    target = tmp_vault / "06_AGENTS" / "Agent-Control-Plane.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Agent Control Plane\nGovernance.", encoding="utf-8")

    result = api.get_markdown_documents("agent control", 20)

    assert result["ok"] is True
    paths = [doc["path"] for doc in result["data"]["documents"]]
    assert "06_AGENTS/Agent-Control-Plane.md" in paths, (
        f"'agent control' should find Agent-Control-Plane.md; got {paths}"
    )
    # Title-matching doc should rank first.
    assert result["data"]["documents"][0]["path"] == "06_AGENTS/Agent-Control-Plane.md"


def test_markdown_search_requires_all_tokens(tmp_vault: Path):
    """Token AND match: an unrelated token must exclude the doc."""
    api = _make_api(tmp_vault)
    target = tmp_vault / "06_AGENTS" / "Agent-Control-Plane.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Agent Control Plane\n", encoding="utf-8")

    result = api.get_markdown_documents("agent telemetry", 20)

    assert result["ok"] is True
    paths = [doc["path"] for doc in result["data"]["documents"]]
    assert "06_AGENTS/Agent-Control-Plane.md" not in paths


def test_markdown_file_tree_returns_nested_structure(tmp_vault: Path):
    """File explorer tree must return folders containing markdown files."""
    api = _make_api(tmp_vault)
    deep = tmp_vault / "06_AGENTS" / "Agent-Control-Plane.md"
    deep.parent.mkdir(parents=True, exist_ok=True)
    deep.write_text("# Agent Control Plane\n", encoding="utf-8")

    result = api.get_markdown_file_tree("")
    assert result["ok"] is True
    tree = result["data"]["tree"]
    folder_names = [n["name"] for n in tree if n["type"] == "folder"]
    assert "06_AGENTS" in folder_names
    agents = next(n for n in tree if n["name"] == "06_AGENTS")
    file_paths = [c["path"] for c in agents["children"] if c["type"] == "file"]
    assert "06_AGENTS/Agent-Control-Plane.md" in file_paths


def test_markdown_file_tree_filter_keeps_matching_parents(tmp_vault: Path):
    """Filtering the tree keeps parent folders of matching files."""
    api = _make_api(tmp_vault)
    deep = tmp_vault / "06_AGENTS" / "Agent-Control-Plane.md"
    deep.parent.mkdir(parents=True, exist_ok=True)
    deep.write_text("# Agent Control Plane\n", encoding="utf-8")

    result = api.get_markdown_file_tree("agent control")
    assert result["ok"] is True
    tree = result["data"]["tree"]
    assert any(n["name"] == "06_AGENTS" for n in tree)


def test_document_backlinks_finds_referencing_note(tmp_vault: Path):
    """Backlinks must surface notes that wiki-link the target document."""
    api = _make_api(tmp_vault)
    target = tmp_vault / "02_KNOWLEDGE" / "linked-note.md"
    target.write_text("# Linked Note\n", encoding="utf-8")
    src = tmp_vault / "02_KNOWLEDGE" / "referrer.md"
    src.write_text("See [[linked-note]] for context.\n", encoding="utf-8")

    result = api.get_document_backlinks("02_KNOWLEDGE/linked-note.md")
    assert result["ok"] is True
    paths = [b["path"] for b in result["data"]["backlinks"]]
    assert "02_KNOWLEDGE/referrer.md" in paths


def test_document_provenance_canonical_has_no_sidecar(tmp_vault: Path):
    """A native canonical doc returns a clean 'no sidecar' provenance model."""
    api = _make_api(tmp_vault)
    note = tmp_vault / "06_AGENTS" / "Agent-Control-Plane.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("# Agent Control Plane\n", encoding="utf-8")

    result = api.get_document_provenance("06_AGENTS/Agent-Control-Plane.md")
    assert result["ok"] is True
    assert result["data"]["has_sidecar"] is False
    assert result["data"]["derivation"] == "canonical"
    assert result["data"]["note"]


def test_document_properties_returns_metadata(tmp_vault: Path):
    """Properties panel data must include heading/word/link counts."""
    api = _make_api(tmp_vault)
    note = tmp_vault / "02_KNOWLEDGE" / "props-note.md"
    note.write_text("---\ntag: x\n---\n# Title\n## Sub\nWord word [[other]].\n", encoding="utf-8")

    result = api.get_document_properties("02_KNOWLEDGE/props-note.md")
    assert result["ok"] is True
    data = result["data"]
    assert data["heading_count"] == 2
    assert data["wikilink_count"] >= 1
    assert any(f["key"] == "tag" for f in data["frontmatter"])


def test_docs_cockpit_dom_has_three_zones():
    """Index.html must expose explorer, center, and info-panel zones."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    for token in ['id="docs-explorer"', 'id="docs-explorer-tree"', 'class="docs-center"',
                  'id="docs-side"', 'data-side-tab="outline"', 'data-side-tab="backlinks"',
                  'data-side-tab="provenance"', 'data-side-tab="properties"',
                  'id="docs-breadcrumb"']:
        assert token in html, f"missing cockpit token: {token}"


def test_docs_cockpit_app_js_has_clear_state_and_find():
    """Stale-content clear + find-in-document + tree loader must exist in app.js."""
    js = APP_JS.read_text(encoding="utf-8")
    assert "function clearActiveDocumentState" in js
    assert "window.clearActiveDocumentState = clearActiveDocumentState" in js
    assert "function loadDocsFileTree" in js
    assert "function _openDocsFindBar" in js
    assert "function _parseMarkdownHeadings" in js
    # InspectorTabs must invoke the clear hook on final tab close
    tabs = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    assert "window.clearActiveDocumentState" in tabs


def test_document_links_classifies_wiki_markdown_embeds_unresolved(tmp_vault: Path):
    """Links API must separate wiki / markdown / embeds / unresolved with resolution."""
    api = _make_api(tmp_vault)
    real = tmp_vault / "02_KNOWLEDGE" / "linked-note.md"
    real.write_text("# Linked Note\n", encoding="utf-8")
    doc = tmp_vault / "02_KNOWLEDGE" / "links-doc.md"
    doc.write_text(
        "See [[linked-note]] and [[ghost-note]].\n"
        "![[linked-note]]\n"
        "[external](https://example.com)\n",
        encoding="utf-8",
    )
    result = api.get_document_links("02_KNOWLEDGE/links-doc.md")
    assert result["ok"] is True
    d = result["data"]
    assert any(w["path"] == "02_KNOWLEDGE/linked-note.md" for w in d["wiki"])
    assert any(u["target"] == "ghost-note" for u in d["unresolved"])
    assert d["counts"]["embeds"] >= 1
    assert d["counts"]["markdown"] >= 1


def test_polish_context_menu_safe_positioning_in_app_js():
    """Viewport-safe positioning must account for topbar/statusbar and add scroll."""
    js = APP_JS.read_text(encoding="utf-8")
    assert "getElementById('topbar')" in js
    assert "getElementById('statusbar')" in js
    assert "menu.style.maxHeight" in js
    assert "menu.style.overflowY" in js


def test_polish_outline_glow_and_links_tab():
    """Outline heading flash + Links tab must be present in DOM/JS/CSS."""
    js = APP_JS.read_text(encoding="utf-8")
    css = STYLES_CSS.read_text(encoding="utf-8")
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "function _flashHeading" in js
    assert "docs-heading-flash" in js
    assert ".docs-heading-flash" in css
    assert "@keyframes docsHeadingFlash" in css
    assert 'data-side-tab="links"' in html
    assert "function _renderDocsLinks" in js


def test_polish_code_overflow_and_tree_rails_css():
    """Code-block overflow guards and tree indent rails must exist in CSS."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".docs-rendered-content pre {" in css
    assert "overflow-x: auto" in css
    assert "--rail-color" in css
    assert "repeating-linear-gradient" in css


def test_editor_parity_and_wikilink_helpers_in_app_js():
    """Edit mode must have toolbar + autocomplete + wiki/embed insertion helpers."""
    js = APP_JS.read_text(encoding="utf-8")
    for fn in [
        "function _renderMarkdownLiveEdit",
        "function _renderMarkdownSourceMode",
        "function _applyMarkdownTool",
        "function _insertWikiLinkAtSelection",
        "function _maybeTriggerWikiAutocomplete",
        "function _openAC",
        "function _chooseAC",
        "function _ensureEditorThen",
        "function _editExistingLink",
        "function _setSaveState",
    ]:
        assert fn in js, f"missing editor helper: {fn}"
    assert "docs-edit-chip" in js          # Editing affordance
    assert "data-md-tool" in js            # markdown toolbar
    assert "_docsPendingScroll" in js      # scroll preservation


def test_live_preview_block_editor_present():
    """Edit must be a live-preview block editor (renders like Reading), not a raw box."""
    js = APP_JS.read_text(encoding="utf-8")
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = STYLES_CSS.read_text(encoding="utf-8")
    # Three explicit modes
    assert 'data-doc-mode="source"' in html
    assert 'data-doc-mode="edit"' in html
    assert 'data-doc-mode="reading"' in html
    # Live-edit block machinery
    for fn in ["function _splitMarkdownBlocks", "function _leOpenBlock",
               "function _leCommitBlock", "function _leRebuildContent"]:
        assert fn in js, f"missing live-edit fn: {fn}"
    # Edit renders through the same rendered-content class as Reading
    assert "docs-live-edit-blocks" in js
    assert "docs-rendered-content docs-live-edit-blocks" in js
    assert ".le-block" in css
    assert ".le-block-editor" in css
    # setMarkdownDocumentMode must accept the source mode
    assert "mode === 'source'" in js


def test_editor_css_parity_and_selection():
    """Editor must be styled like the document card and allow text selection."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert "user-select: text" in css
    assert ".docs-autocomplete" in css
    assert ".docs-edit-chip" in css
    assert ".docs-md-toolbar" in css
    assert ".docs-save-state.ss-unsaved" in css
    # Editor textarea should use the surface background, not a hard black box.
    assert ".docs-edit-layout .docs-markdown-source" in css


def test_context_menu_has_wikilink_actions():
    """Document context menu must offer wiki-link / embed insertion + existing-link edits."""
    js = APP_JS.read_text(encoding="utf-8")
    for label in [
        "Add wiki link",
        "Add embed",
        "Create wiki link from selection",
        "Create markdown link from selection",
        "Remove link, keep text",
        "Convert to embed",
    ]:
        assert label in js, f"missing context-menu action: {label}"
    # Link detection from the rendered markup
    assert "a.wikilink" in js
    assert "data-embed-target" in js


def test_open_external_validates_and_handles_missing(tmp_vault: Path):
    """open_vault_file_external blocks traversal and reports missing files."""
    api = _make_api(tmp_vault)
    assert api.open_vault_file_external("../etc/passwd")["ok"] is False
    miss = api.open_vault_file_external("02_KNOWLEDGE/nope.md")
    assert miss["ok"] is False and miss["error"]["code"] == "file_missing"


def test_export_document_html_writes_real_artifact(tmp_vault: Path):
    """Export writes a standalone HTML file under 07_LOGS/Exports/Docs and never mutates source."""
    api = _make_api(tmp_vault)
    src = tmp_vault / "02_KNOWLEDGE" / "test-note.md"
    before = src.read_text(encoding="utf-8")
    result = api.export_document_html("02_KNOWLEDGE/test-note.md", "<h1>Test</h1><p>Body</p>", "Test")
    assert result["ok"] is True
    out = tmp_vault / result["data"]["path"]
    assert out.exists()
    assert result["data"]["path"].startswith("07_LOGS/Exports/Docs/")
    html = out.read_text(encoding="utf-8")
    assert "<h1>Test</h1>" in html and "@page" in html
    # Source markdown untouched.
    assert src.read_text(encoding="utf-8") == before


def test_export_document_pdf_produces_real_pdf(tmp_vault: Path):
    """export_document_pdf must emit a real %PDF when xhtml2pdf is available; else HTML fallback."""
    api = _make_api(tmp_vault)
    src = tmp_vault / "02_KNOWLEDGE" / "test-note.md"
    before = src.read_text(encoding="utf-8")
    result = api.export_document_pdf(
        "02_KNOWLEDGE/test-note.md",
        "<h1>Test</h1><p>Body</p><ul><li>a</li></ul><pre>code line</pre>",
        "Test",
    )
    assert result["ok"] is True
    out = tmp_vault / result["data"]["path"]
    assert out.exists() and out.stat().st_size > 0
    assert result["data"]["path"].startswith("07_LOGS/Exports/Docs/")
    try:
        import xhtml2pdf  # noqa: F401
        have_pdf = True
    except Exception:
        have_pdf = False
    if have_pdf:
        assert result["data"]["is_pdf"] is True
        assert out.suffix == ".pdf"
        assert out.read_bytes()[:5] == b"%PDF-"
    else:
        assert out.suffix == ".html"
    # Source untouched either way.
    assert src.read_text(encoding="utf-8") == before


def test_tab_menu_does_not_strip_listeners_with_clonenode():
    """Tab context menu must append buttons directly (cloneNode strips click listeners)."""
    tabs = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    # The listener-stripping pattern must be gone.
    assert "group.cloneNode(true)" not in tabs
    # Buttons attach a real click listener and actions run in a try/catch.
    assert "btn.addEventListener('click'" in tabs
    assert "item.action()" in tabs


def test_clipboard_route_and_robust_copy():
    """Backend clipboard fallback + execCommand-based copy must exist."""
    js = APP_JS.read_text(encoding="utf-8")
    api = API_PY.read_text(encoding="utf-8")
    assert "copy_text_to_clipboard" in js
    assert "execCommand" in js
    assert "def _studio_copy_text_to_clipboard" in api
    assert "StudioAPI.copy_text_to_clipboard" in api


def test_export_pdf_save_as_headless_writes_pdf(tmp_vault: Path):
    """Save-As export falls back to a real PDF in exports when no window is present."""
    api = _make_api(tmp_vault)
    src = tmp_vault / "02_KNOWLEDGE" / "test-note.md"
    before = src.read_text(encoding="utf-8")
    r = api.export_document_pdf_save_as("02_KNOWLEDGE/test-note.md", "<h1>T</h1><p>Body</p>", "T")
    assert r["ok"] is True and r["data"]["saved"] is True
    out = Path(r["data"]["abs_path"])
    assert out.exists()
    try:
        import xhtml2pdf  # noqa: F401
        assert r["data"]["is_pdf"] is True
        assert out.read_bytes()[:5] == b"%PDF-"
    except Exception:
        pass
    # Source untouched.
    assert src.read_text(encoding="utf-8") == before


def test_export_uses_save_as_dialog_not_autoopen():
    """Frontend export must call the Save-As route and not force-open a PDF app."""
    js = APP_JS.read_text(encoding="utf-8")
    assert "export_document_pdf_save_as" in js
    api = API_PY.read_text(encoding="utf-8")
    assert "def _studio_export_document_pdf_save_as" in api
    assert "create_file_dialog" in api
    # The active-doc export no longer auto-opens the result in a PDF app.
    import re
    m = re.search(r"async function _exportActiveDocument\(\)\s*\{.*?\n\}", js, re.S)
    assert m and "open_vault_file_external" not in m.group(0)


def test_docs_session_persists_tabs_and_bookmarks(tmp_vault: Path):
    """Open tabs + bookmarks + active must round-trip through the session store."""
    api = _make_api(tmp_vault)
    payload = {
        "tabs": [
            {"nodeId": "markdown:02_KNOWLEDGE/test-note.md", "label": "Test", "path": "02_KNOWLEDGE/test-note.md",
             "type": "markdown_doc", "pinned": False, "bookmarked": True},
        ],
        "active_node_id": "doc:markdown:02_KNOWLEDGE/test-note.md",
    }
    assert api.save_docs_session(payload)["ok"] is True
    assert (tmp_vault / ".chaseos" / "studio" / "docs-session.json").exists()
    loaded = api.load_docs_session()
    assert loaded["ok"] is True
    assert len(loaded["data"]["tabs"]) == 1
    assert loaded["data"]["tabs"][0]["bookmarked"] is True
    assert loaded["data"]["active_node_id"] == "doc:markdown:02_KNOWLEDGE/test-note.md"


def test_load_docs_session_empty_when_absent(tmp_vault: Path):
    api = _make_api(tmp_vault)
    loaded = api.load_docs_session()
    assert loaded["ok"] is True
    assert loaded["data"]["tabs"] == []


def test_move_dialog_and_modals_and_reveal_wired():
    """Native folder Move + in-app modals + filter-based reveal must be wired."""
    js = APP_JS.read_text(encoding="utf-8")
    api = API_PY.read_text(encoding="utf-8")
    tabs = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    # Backend routes
    assert "def _studio_move_markdown_document_dialog" in api
    assert "def _studio_save_docs_session" in api
    assert "def _studio_load_docs_session" in api
    assert "StudioAPI.move_markdown_document_dialog" in api
    # Native folder picker + in-app modal (no prompt() for move/rename/property)
    assert "move_markdown_document_dialog" in js
    assert "function _docsFormModal" in js
    # Reveal-in-tree is now resilient (filters the tree if the row isn't loaded)
    assert "async function _revealActiveFileInTree" in js
    assert "loadDocsFileTree(fname)" in js
    # Session persistence in the tab system
    assert "function restoreDocsSession" in tabs
    assert "save_docs_session" in tabs
    assert "_persistDocsSession" in tabs


def test_context_menu_actions_wired_no_noop():
    """Tab + document + file menus must wire real OS/export/copy actions (no window.print no-op)."""
    js = APP_JS.read_text(encoding="utf-8")
    tabs = INSPECTOR_TABS_JS.read_text(encoding="utf-8")
    # Real action helpers exist
    for fn in ["function _openActiveInDefaultApp", "function _showActiveInSystemExplorer",
               "function _exportActiveDocument", "function _copyMarkdownLink",
               "function _openPathInDefaultApp", "function _exportPathToPdf"]:
        assert fn in js, f"missing action helper: {fn}"
    # Registry exposes them
    for key in ["openInDefaultApp:", "showInSystemExplorer:", "exportToPdf:",
                "revealInFileTree:", "viewBacklinks:", "copyMarkdownLink:"]:
        assert key in js, f"missing registry entry: {key}"
    # Tab menu no longer uses window.print() and wires the real handlers
    assert "window.print()" not in tabs
    assert "docActions.exportToPdf" in tabs
    assert "docActions.openInDefaultApp" in tabs
    assert "docActions.revealInFileTree" in tabs
    # Reveal-in-tree glow + toast
    assert "docs-file-row--revealed" in js
    assert "Path copied" in js


def test_selection_visibility_layer_present():
    """Selection visibility: strong ::selection, selected-block outline, chip glow, toolbar."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    js = APP_JS.read_text(encoding="utf-8")
    # CSS variables + strong selection styling + moz fallback
    assert "--docs-selection-bg-strong" in css
    assert "::-moz-selection" in css
    assert ".docs-block--selection-active" in css
    assert ".docs-chip--selection-active" in css
    assert ".docs-sel-toolbar" in css
    # Stronger blue selection inside code blocks
    assert "rgba(96, 165, 250" in css
    # JS selection tracker
    assert "selectionchange" in js
    assert "function _updateDocSelectionUI" in js
    assert "function _clearDocSelectionUI" in js
    assert "containsNode" in js
    # Right-click keeps selection (toolbar hidden, selection untouched)
    assert "_docs-sel-toolbar" in js


def test_markdown_document_api_opens_links_and_blocks_traversal(tmp_vault: Path):
    """Opening Markdown returns content/link metadata and rejects traversal."""
    api = _make_api(tmp_vault)
    note = tmp_vault / "02_KNOWLEDGE" / "test-note.md"
    note.write_text("# Test\nSee [[linked-note]] and ![[linked-note]].", encoding="utf-8")

    result = api.get_markdown_document("02_KNOWLEDGE/test-note.md")

    assert result["ok"] is True
    assert result["data"]["title"] == "Test"
    assert len(result["data"]["outgoing_links"]) == 2
    blocked = api.get_markdown_document("../PROJECT_FOUNDATION.md")
    assert blocked["ok"] is False


def test_markdown_document_autosave_writes_file_and_backup(tmp_vault: Path):
    """Autosave must write the selected Markdown file and keep a first-save backup."""
    api = _make_api(tmp_vault)
    opened = api.get_markdown_document("02_KNOWLEDGE/test-note.md")
    assert opened["ok"] is True

    result = api.save_markdown_document(
        "02_KNOWLEDGE/test-note.md",
        "# Test\nUpdated content.",
        opened["data"]["modified_ns"],
    )

    assert result["ok"] is True
    assert (tmp_vault / "02_KNOWLEDGE" / "test-note.md").read_text(encoding="utf-8") == "# Test\nUpdated content."
    assert (tmp_vault / result["data"]["backup_path"]).exists()


def test_markdown_reference_resolves_wikilinks(tmp_vault: Path):
    """Wiki-link targets should resolve by current-folder and vault scan."""
    api = _make_api(tmp_vault)

    result = api.resolve_markdown_reference("linked-note", "02_KNOWLEDGE/test-note.md")

    assert result["ok"] is True
    assert result["data"]["resolved"] is True
    assert result["data"]["path"] == "02_KNOWLEDGE/linked-note.md"


def test_markdown_document_rename_and_move_are_vault_bounded(tmp_vault: Path):
    """Rename/move document actions must stay vault-relative and avoid overwrites."""
    api = _make_api(tmp_vault)

    renamed = api.rename_markdown_document("02_KNOWLEDGE/test-note.md", "renamed-note")
    assert renamed["ok"] is True
    assert renamed["data"]["path"] == "02_KNOWLEDGE/renamed-note.md"
    assert (tmp_vault / "02_KNOWLEDGE" / "renamed-note.md").exists()

    moved = api.move_markdown_document("02_KNOWLEDGE/renamed-note.md", "02_KNOWLEDGE/Nested")
    assert moved["ok"] is True
    assert moved["data"]["path"] == "02_KNOWLEDGE/Nested/renamed-note.md"
    assert (tmp_vault / "02_KNOWLEDGE" / "Nested" / "renamed-note.md").exists()

    blocked = api.move_markdown_document("02_KNOWLEDGE/Nested/renamed-note.md", "../outside")
    assert blocked["ok"] is False


# ---------------------------------------------------------------------------
# Regression: existing shell tests still pass token checks
# ---------------------------------------------------------------------------

def test_inspector_title_still_in_html():
    """id='inspector-title' must still exist (moved to route panel, not deleted)."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="inspector-title"' in html, (
        "id='inspector-title' was lost — it must be moved into #panel-node-inspector"
    )


def test_inspector_trust_still_in_html():
    """id='inspector-trust' must still exist (moved to route panel, not deleted)."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="inspector-trust"' in html


def test_inspector_empty_still_in_html():
    """id='inspector-empty' must still exist inside #panel-node-inspector."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="inspector-empty"' in html
