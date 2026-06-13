"""Tests for excalidraw_live_browser_proof.py

Unit tests cover the module contract without invoking Playwright.
Integration tests are skipped unless Playwright is installed.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── resolve vault path ─────────────────────────────────────────────────────────
_VAULT = Path(__file__).resolve().parents[2]

from runtime.browser_runtime.excalidraw_live_browser_proof import (
    EXCALIDRAW_CANVAS_SELECTOR,
    EXCALIDRAW_EXPECTED_TITLE_FRAGMENT,
    EXCALIDRAW_TARGET_URL,
    PROOF_VERSION,
    _authority,
    _now_utc,
    _playwright_available,
    _slug,
    run_excalidraw_live_browser_proof,
)


# ── TestConstants ──────────────────────────────────────────────────────────────

class TestConstants:
    def test_target_url_registered_not_env(self):
        assert EXCALIDRAW_TARGET_URL == "https://excalidraw.com"

    def test_expected_title_fragment(self):
        assert "Excalidraw" in EXCALIDRAW_EXPECTED_TITLE_FRAGMENT

    def test_canvas_selector(self):
        assert EXCALIDRAW_CANVAS_SELECTOR == "canvas"

    def test_proof_version_format(self):
        assert PROOF_VERSION.startswith("browser.")
        assert "excalidraw" in PROOF_VERSION

    def test_no_env_var_import(self):
        import runtime.browser_runtime.excalidraw_live_browser_proof as mod
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert "os.environ" not in src
        assert "getenv" not in src


# ── TestAuthority ──────────────────────────────────────────────────────────────

class TestAuthority:
    def test_env_var_not_required(self):
        auth = _authority()
        assert auth["env_var_required"] is False

    def test_target_registered_in_chaseos(self):
        auth = _authority()
        assert auth["target_hardcoded"] is False
        assert auth["target_registered_in_chaseos"] is True
        assert auth["target_registry_id"] == "excalidraw"

    def test_no_browser_use_cli(self):
        auth = _authority()
        assert auth["no_browser_use_cli"] is True

    def test_headless_browser_only(self):
        auth = _authority()
        assert auth["headless_browser_only"] is True

    def test_no_vault_markdown_writes(self):
        auth = _authority()
        assert auth["no_vault_markdown_writes"] is True

    def test_no_agent_bus_writes(self):
        auth = _authority()
        assert auth["no_agent_bus_writes"] is True

    def test_no_canonical_mutation(self):
        auth = _authority()
        assert auth["no_canonical_mutation"] is True

    def test_no_provider_calls(self):
        auth = _authority()
        assert auth["no_provider_calls"] is True


# ── TestHelpers ────────────────────────────────────────────────────────────────

class TestHelpers:
    def test_now_utc_ends_with_z(self):
        ts = _now_utc()
        assert ts.endswith("Z")

    def test_slug_format(self):
        s = _slug()
        assert len(s) == 15  # YYYYMMDD-HHMMSS
        assert s[8] == "-"

    def test_playwright_available_returns_bool(self):
        result = _playwright_available()
        assert isinstance(result, bool)


# ── TestPlaywrightUnavailable ──────────────────────────────────────────────────

class TestPlaywrightUnavailable:
    def test_blocked_result_when_playwright_missing(self, tmp_path):
        with patch(
            "runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available",
            return_value=False,
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)

        assert result["ok"] is False
        assert result["status"] == "blocked_playwright_not_available"
        assert "playwright_not_installed" in result["blockers"]
        assert result["target_url"] == EXCALIDRAW_TARGET_URL
        assert result["canvas_found"] is False
        assert result["screenshot_path"] is None
        assert "note" in result

    def test_blocked_result_has_authority(self, tmp_path):
        with patch(
            "runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available",
            return_value=False,
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)
        assert "authority" in result
        assert result["authority"]["env_var_required"] is False


# ── TestResultShape ────────────────────────────────────────────────────────────

class TestResultShape:
    """Mock Playwright to test full result shape without a network call."""

    def _mock_playwright_session(self, title: str, canvas_found: bool, nav_ok: bool = True):
        mock_canvas = MagicMock() if canvas_found else None
        mock_page = MagicMock()
        mock_page.title.return_value = title
        mock_page.query_selector.return_value = mock_canvas
        mock_page.screenshot.return_value = None
        if not nav_ok:
            mock_page.goto.side_effect = Exception("Navigation timeout")
        mock_ctx = MagicMock()
        mock_ctx.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_ctx
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_sync = MagicMock()
        mock_sync.__enter__ = MagicMock(return_value=mock_pw)
        mock_sync.__exit__ = MagicMock(return_value=False)
        return mock_sync

    def test_success_result_has_all_keys(self, tmp_path):
        mock_sync = self._mock_playwright_session("Excalidraw Whiteboard", canvas_found=True)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)

        for key in ("ok", "version", "target_url", "started_at", "completed_at", "status",
                    "checks", "blockers", "screenshot_path", "page_title", "canvas_found",
                    "run_slug", "authority"):
            assert key in result, f"missing key: {key}"

    def test_success_title_match(self, tmp_path):
        mock_sync = self._mock_playwright_session("Excalidraw Whiteboard", canvas_found=True)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)

        assert result["page_title"] == "Excalidraw Whiteboard"
        assert result["canvas_found"] is True

    def test_title_mismatch_adds_blocker(self, tmp_path):
        mock_sync = self._mock_playwright_session("Some Other Page", canvas_found=False)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)

        assert result["ok"] is False
        assert any("unexpected_title" in b for b in result["blockers"])

    def test_nav_failure_gives_failed_status(self, tmp_path):
        mock_sync = self._mock_playwright_session("", canvas_found=False, nav_ok=False)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)

        assert result["status"] == "excalidraw_live_browser_proof_failed"

    def test_playwright_start_failure_returns_structured_result(self, tmp_path):
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch(
                "runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright",
                side_effect=PermissionError("Access is denied"),
            ),
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)

        assert result["ok"] is False
        assert result["status"] == "excalidraw_live_browser_proof_failed"
        assert result["canvas_found"] is False
        assert any("playwright_error" in blocker for blocker in result["blockers"])

    def test_run_slug_custom(self, tmp_path):
        mock_sync = self._mock_playwright_session("Excalidraw Whiteboard", canvas_found=True)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            result = run_excalidraw_live_browser_proof(
                tmp_path, write_evidence=False, run_slug="test-slug-001"
            )
        assert result["run_slug"] == "test-slug-001"

    def test_write_evidence_false_no_files(self, tmp_path):
        mock_sync = self._mock_playwright_session("Excalidraw Whiteboard", canvas_found=True)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)

        logs_dir = tmp_path / "07_LOGS" / "Browser-Runs"
        json_files = list(logs_dir.glob("*.json")) if logs_dir.exists() else []
        assert json_files == []

    def test_write_evidence_true_creates_json(self, tmp_path):
        mock_sync = self._mock_playwright_session("Excalidraw Whiteboard", canvas_found=True)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            result = run_excalidraw_live_browser_proof(
                tmp_path, write_evidence=True, run_slug="write-test"
            )

        logs_dir = tmp_path / "07_LOGS" / "Browser-Runs"
        assert logs_dir.exists()
        json_files = list(logs_dir.glob("*.json"))
        assert len(json_files) == 1
        payload = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert payload["target_url"] == EXCALIDRAW_TARGET_URL

    def test_result_is_json_serializable(self, tmp_path):
        mock_sync = self._mock_playwright_session("Excalidraw Whiteboard", canvas_found=True)
        with (
            patch("runtime.browser_runtime.excalidraw_live_browser_proof._playwright_available", return_value=True),
            patch("runtime.browser_runtime.excalidraw_live_browser_proof.sync_playwright", return_value=mock_sync),
        ):
            result = run_excalidraw_live_browser_proof(tmp_path, write_evidence=False)
        # Should not raise
        json.dumps(result, default=str)


# ── TestCLIWiring ──────────────────────────────────────────────────────────────

class TestCLIWiring:
    def test_cli_handler_importable(self):
        from runtime.cli.main import cmd_operate_browser_excalidraw_live_proof
        assert callable(cmd_operate_browser_excalidraw_live_proof)

    def test_cli_subcommand_registered(self):
        from runtime.cli.main import build_parser
        parser = build_parser()
        # Verify excalidraw-live-proof parses without error
        args = parser.parse_args(
            ["operate", "browser", "excalidraw-live-proof", "--no-write", "--json"]
        )
        assert args.no_write is True
        assert args.output_json is True

    def test_cli_headed_flag(self):
        from runtime.cli.main import build_parser
        parser = build_parser()
        args = parser.parse_args(["operate", "browser", "excalidraw-live-proof", "--headed"])
        assert args.headed is True

    def test_cli_settle_ms_flag(self):
        from runtime.cli.main import build_parser
        parser = build_parser()
        args = parser.parse_args(
            ["operate", "browser", "excalidraw-live-proof", "--settle-ms", "5000"]
        )
        assert args.settle_ms == 5000


# ── TestIntegrationLive ────────────────────────────────────────────────────────

@pytest.mark.skipif(
    not _playwright_available(),
    reason="playwright not installed — skipping live browser integration test",
)
class TestIntegrationLive:
    """Live integration tests — only run when playwright is installed."""

    def test_excalidraw_live_proof_real(self, tmp_path):
        result = run_excalidraw_live_browser_proof(
            tmp_path,
            headless=True,
            settle_ms=3000,
            write_evidence=True,
        )
        # Page must load and title must match
        assert result["ok"] is True, f"Live proof failed: {result}"
        assert result["canvas_found"] is True
        assert EXCALIDRAW_EXPECTED_TITLE_FRAGMENT.lower() in (result["page_title"] or "").lower()

        # Evidence must be written
        logs_dir = tmp_path / "07_LOGS" / "Browser-Runs"
        json_files = list(logs_dir.glob("*.json"))
        png_files = list(logs_dir.glob("*.png"))
        assert len(json_files) == 1
        assert len(png_files) == 1
