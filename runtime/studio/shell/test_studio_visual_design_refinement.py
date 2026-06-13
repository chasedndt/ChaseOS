from pathlib import Path


SHELL_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = SHELL_DIR / "frontend"
STYLES = FRONTEND_DIR / "styles.css"
INDEX = FRONTEND_DIR / "index.html"
APP = FRONTEND_DIR / "app.js"
MAIN = SHELL_DIR / "main.py"


def read_styles() -> str:
    return STYLES.read_text(encoding="utf-8")


def read_index() -> str:
    return INDEX.read_text(encoding="utf-8")


def read_app() -> str:
    return APP.read_text(encoding="utf-8")


def read_main() -> str:
    return MAIN.read_text(encoding="utf-8")


def test_product_shell_visual_state_tokens_present() -> None:
    css = read_styles()
    for token in (
        "--state-live",
        "--state-read",
        "--state-gated",
        "--state-soon",
        "--state-blocked",
        "--focus-ring",
    ):
        assert token in css


def test_nav_buttons_use_product_icon_system_instead_of_acronym_tiles() -> None:
    css = read_styles()
    assert ".nav-icon::before" in css
    assert ".nav-icon::after" in css
    assert "font-size: 0;" in css

    expected_panel_mappings = (
        "dashboard",
        "chat",
        "project-workspace",
        "workflow-packs",
        "chaser-forge",
        "graph",
        "node-inspector",
        "graph-hygiene",
        "provenance-explorer",
        "intake",
        "capture-markdown",
        "acquisition",
        "sic",
        "runtime-cockpit",
        "aor",
        "bus",
        "schedules",
        "browser-runtime",
        "siteops",
        "runtime-navigation",
        "runtime-memory-inspector",
        "context-import",
        "memory-ledger",
        "pulse-schedule-proof",
        "pulse-enqueue",
        "approval-center",
        "build-logs",
        "decision-ledger",
        "settings",
        "qa-proof",
        "feature-filter",
        "workflow-registry",
        "role-cards",
        "pivot-log",
        "app-launcher",
        "workspace-entry",
    )
    missing = [
        panel
        for panel in expected_panel_mappings
        if f'.nav-btn[data-panel="{panel}"] .nav-icon::before' not in css
    ]
    assert missing == []


def test_existing_nav_authority_posture_remains_explicit() -> None:
    html = read_index()
    for state in ("live", "read-only", "approval-gated", "coming-soon"):
        assert f'data-state="{state}"' in html
    assert 'data-authority="proposal-only"' in html
    assert 'data-authority="coming-soon"' in html


def test_product_copy_polish_covers_remaining_developer_terms() -> None:
    app = read_app()
    for token in (
        "dry[- ]run",
        "daemon",
        "MVP",
        "proof",
        "read[- ]only",
        "Build Logs",
        "Logs / Audit",
        "Visual QA",
        "no-write",
        "not mounted",
        "Shell action",
        "chaseos studio",
        "--json",
    ):
        assert token in app


def test_topbar_has_product_mark_and_icon_framed_controls() -> None:
    css = read_styles()
    for selector in (
        "#topbar-logo::before",
        "#topbar-quick-create-btn::before",
        "#topbar-voice-btn::before",
        "#topbar-feature-help-btn::before",
        "#topbar-settings-btn::before",
    ):
        assert selector in css


def test_status_chips_and_authority_chips_have_shared_visual_language() -> None:
    css = read_styles()
    for selector in (
        "#topbar-status::before",
        ".panel-status-pill::before",
        ".panel-status-pill.status-ok",
        ".panel-status-pill.status-loading",
        ".panel-status-pill.status-error",
        ".runtime-authority-row span",
    ):
        assert selector in css


def test_shared_page_template_and_empty_states_are_refined() -> None:
    css = read_styles()
    for selector in (
        ".panel-title-row > div:first-child",
        "overflow-wrap: anywhere",
        ".empty-state",
        ".empty-state-icon",
        ".panel-loading",
        ".panel-error",
        ".error-state",
    ):
        assert selector in css


def test_native_batch_visual_qa_uses_direct_timer_callbacks() -> None:
    main = read_main()
    assert "QTimer.singleShot(delay_ms, _capture_batch_next)" in main
    assert "QTimer.singleShot(delay_ms + 2000, _capture_batch_next)" in main
    assert "QTimer.singleShot(1000, _capture_current_route)" in main
    assert "QTimer.singleShot(250, _capture_batch_next)" in main
    assert "qt_webengine_runJavaScript" in main
    assert "target.page().runJavaScript(script)" in main
    assert "new Event('hashchange')" in main
    assert "QTimer.singleShot(delay_ms, bridge.captureBatchNext)" not in main
    assert "QTimer.singleShot(1000, bridge.captureBatchCurrent)" not in main
