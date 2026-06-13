"""Tests for the MVP user-facing Studio shell App Launcher panel."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.shell.api import StudioAPI


FRONTEND = Path(__file__).parent / "frontend"


def test_studio_api_exposes_app_launcher_contract(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    response = StudioAPI(vault).get_app_launcher()

    assert response["ok"] is True
    data = response["data"]
    assert data["surface"] == "studio_app_launcher_local_app"
    assert data["app_count"] >= 6
    app = {entry["id"]: entry for entry in data["apps"]}["studio-dashboard-app"]
    assert app["runtime_status"]["checked"] is True
    assert app["runtime_status"]["last_checked"]
    assert {action["label"] for action in app["actions"]} == {"Open", "Launch / Start Request", "Health", "Authority"}
    assert all(action["executes_in_launcher"] is False for action in app["actions"])


def test_shell_frontend_app_launcher_uses_cards_buttons_not_cli_table() -> None:
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")

    assert 'id="app-launcher-body"' in html
    assert "loadAppLauncher" in js
    assert "get_app_launcher" in js
    assert "app-launcher-card" in js
    assert "Launch / Start Request" in js
    assert "Last Checked" in js
    assert "Advanced/debug command" in js
    assert "data-confirmation-required" in js
    assert "executes_in_launcher" in js
    assert "command-table" not in js
