"""Studio Content + Personal Memory productization tests."""

from pathlib import Path


VAULT = Path(__file__).resolve().parents[3]
FRONTEND = VAULT / "runtime" / "studio" / "shell" / "frontend"


def _html() -> str:
    return (FRONTEND / "index.html").read_text(encoding="utf-8")


def _js() -> str:
    return (FRONTEND / "app.js").read_text(encoding="utf-8")


def _css() -> str:
    return (FRONTEND / "styles.css").read_text(encoding="utf-8")


def test_content_page_headers_are_productized():
    html = _html()

    assert "<h2>Intake</h2>" in html
    assert "<h2>Capture</h2>" in html
    assert "<h2>Sources</h2>" in html
    assert "Source Packs" in html
    assert "Normalized Packs" in html
    assert "Briefing Inputs" in html
    assert "<h2>Research Collections</h2>" in html
    assert "Retrieval posture" in html
    assert "Approval for changes" in html
    assert 'id="sic-summary-row"' in html
    assert 'id="sic-search-input"' in html
    assert "Search collections or sources" in html
    assert "Intake / Quarantine" not in html
    assert "Capture Markdown</h2>" not in html
    assert "Acquisition Cockpit" not in html
    assert "Dry-run proposal" not in html
    assert "SIC Workspaces" not in html
    assert "No ingestion" not in html


def test_personal_memory_page_headers_are_productized():
    html = _html()

    assert "<h2>Memory Manager</h2>" in html
    assert "<h2>Context Import</h2>" in html
    assert "<h2>Memory Ledger</h2>" in html
    assert "<h2>Proactive Briefings</h2>" in html
    assert "<h2>Review Queue</h2>" in html
    assert "Runtime Memory Inspector" not in html
    assert "Pulse Schedule Proofs" not in html
    assert "Pulse Agent Bus Enqueue" not in html


def test_product_authority_posture_is_visible():
    html = _html()

    for text in (
        "New captures",
        "Duplicate protection",
        "No automatic filing",
        "Quarantine save",
        "No auto-run",
        "Source packs",
        "No Personal Map apply",
        "No canonical promotion",
        "No runtime dispatch",
        "No repair apply",
    ):
        assert text in html


def test_selected_content_and_memory_objects_use_right_inspector():
    js = _js()

    assert "function renderObjectInspectorProductContext" in js
    assert "handleProductObjectInspectorAction" in js
    assert "data-capture-ref" in js
    assert "data-intake-ref" in js
    assert "data-sic-source-ref" in js
    assert "data-acquisition-run" in js
    assert "get_sources_product_model(" in js
    assert "_sicRenderSummary" in js
    assert "data-memory-ledger-id" in js
    assert "data-pulse-proof-lane" in js
    assert "data-pulse-queue-ref" in js
    assert "data-selected-product-object" in js


def test_product_click_targets_have_stable_cursor_affordance():
    css = _css()

    for selector in (
        ".capture-markdown-recent-item",
        ".intake-item",
        ".sic-source-row",
        ".acquisition-source-card",
        ".acquisition-run-card",
        ".pulse-schedule-proof-card",
        ".pulse-enqueue-card",
        ".ml-runtime-card",
        ".ml-task-item",
        ".ml-attention-item",
    ):
        assert selector in css
