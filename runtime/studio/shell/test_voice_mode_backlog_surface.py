from __future__ import annotations

from pathlib import Path

VAULT = Path(__file__).resolve().parents[3]
FRONTEND = Path(__file__).resolve().parent / "frontend"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestVoiceModeSurface:
    def test_voice_mode_nav_route_panel_and_catalog_are_mounted_read_only(self):
        index = _read(FRONTEND / "index.html")
        app = _read(FRONTEND / "app.js")

        assert 'data-panel="voice-mode"' in index
        assert 'id="panel-voice-mode"' in index
        assert 'data-read-only="true"' in index
        assert "No microphone" in index
        assert "No provider call" in index
        assert "No runtime dispatch" in index
        assert "'voice-mode': '#/voice-mode'" in app
        assert "id: 'voice-mode'" in app
        assert "No microphone capture" in app or "No microphone" in app

    def test_voice_mode_registry_entry_is_mounted_without_actions(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}

        assert "voice-mode" in panels
        voice = panels["voice-mode"]
        assert voice["status"] == "mounted"
        assert voice["mount_kind"] == "main_panel"
        assert voice["frontend_target"] == "panel-voice-mode"
        assert voice["read_only"] is True
        assert voice["write_mode"] == "read_only"
        assert voice["possible_writes"] == []
        assert "Microphone capture" in voice["blocked_reason"]
        assert "provider/model calls" in voice["blocked_reason"]


class TestBacklogAndPublicContextCleanup:
    def test_not_built_backlog_exists_and_maps_voice_mode_to_studio(self):
        backlog = _read(VAULT / "docs" / "features" / "chaseos_not_built_backlog.md")

        assert "# ChaseOS Not-Built / Partial Feature Backlog" in backlog
        assert "NB-030" in backlog
        assert "Voice Mode" in backlog
        assert "#/voice-mode" in backlog
        assert "runtime/studio/shell/frontend/index.html#panel-voice-mode" in backlog
        assert "No microphone" in backlog

    def test_readme_and_project_foundation_neutralize_specific_private_examples(self):
        readme = _read(VAULT / "README.md")
        foundation = _read(VAULT / "PROJECT_FOUNDATION.md")

        assert "TradeSync-OS.md" not in foundation
        assert "StrikeZone-Crypto-OS.md" not in foundation
        assert "real API references" not in foundation
        assert "professional leveraged trading operation" not in readme
        assert "Signal community and Whop revenue" not in readme
        assert "Greenwich" not in readme
        assert "Implementation-specific material" in foundation or "implementation-specific material" in foundation
