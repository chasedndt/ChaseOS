"""
runtime.operator_surface.tests.test_browser_pass4

Browser Operator Surface — Pass 4 tests
Command Surface Integration

Tests:
  - Contract tests (no browser): input validation, scope building, error paths,
    JSON output format, list-runs helpers, replay error path
  - Integration tests (browser required): end-to-end command execution via
    the CLI entrypoint

Pass 4 acceptance criteria:
  A. `chaseos operate browser open URL` — runs end-to-end, returns 0 for valid URL
  B. `chaseos operate browser inspect URL` — returns 0, structured output
  C. `chaseos operate browser screenshot URL` — file written or stub path returned
  D. `chaseos operate browser replay RUN_ID` — loads real audit artifact, returns 0
  E. `chaseos operate browser list-runs` — returns 0, JSON keys present
  F. Invalid URL returns exit code 1
  G. All commands support --json flag
  H. Audit artifact is always written (check run_id in JSON output)
"""

from __future__ import annotations

import json
import sys
import tempfile
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.operator_surface.browser.operator import (
    _validate_url,
    _extract_origin,
    _build_browser_scope,
    _extract_step_outputs,
    _print_error,
    run_open,
    run_inspect,
    run_snapshot,
    run_screenshot,
    run_replay,
    run_list_runs,
)
from runtime.operator_surface.browser.actions import snapshot_interactive
from runtime.operator_surface.contracts import OperatorScope
from runtime.operator_surface.capabilities import SurfaceType
from runtime.operator_surface.browser.image_verifier import analyze_png_nonblank


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_audit(outcome="COMPLETE", run_id="test-run-001", error=None, events=None):
    """Build a minimal fake OperatorRunAudit-like object."""
    audit = MagicMock()
    audit.outcome = outcome
    audit.run_id = run_id
    audit.error = error
    audit.events = events or []
    audit.steps_completed = 4
    audit.steps_planned = 4
    audit.steps_failed = 0
    audit.adapter_payload = {
        "adapter_mode": "stub",
        "playwright_available": False,
        "playwright_launch_error": None,
        "chromium_executable_path": None,
        "implementation_note": "pass4-test",
    }
    return audit


def _fake_step_event(result: dict):
    """Build a fake STEP_COMPLETE event."""
    from runtime.operator_surface.events import OperatorEventType
    event = MagicMock()
    event.event_type = OperatorEventType.STEP_COMPLETE
    event.payload = {"result": result}
    return event


def _write_png(path: Path, width: int, height: int, pixels: list[bytes]) -> None:
    rows = []
    for row_index in range(height):
        start = row_index * width
        rows.append(b"\x00" + b"".join(pixels[start : start + width]))
    raw = zlib.compress(b"".join(rows))

    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk("IHDR".encode("ascii"), struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk("IDAT".encode("ascii"), raw)
        + chunk("IEND".encode("ascii"), b"")
    )


# ── Contract tests: URL validation ───────────────────────────────────────────

class TestValidateUrl:
    def test_valid_https(self):
        assert _validate_url("https://example.com") is None

    def test_valid_http(self):
        assert _validate_url("http://localhost:8080/path?q=1") is None

    def test_empty_url(self):
        assert _validate_url("") is not None

    def test_no_scheme(self):
        assert _validate_url("example.com") is not None

    def test_ftp_scheme_rejected(self):
        assert _validate_url("ftp://example.com") is not None

    def test_no_host(self):
        assert _validate_url("https://") is not None


# ── Contract tests: origin extraction ────────────────────────────────────────

class TestExtractOrigin:
    def test_https_host(self):
        assert _extract_origin("https://example.com/page") == "https://example.com"

    def test_http_with_port(self):
        assert _extract_origin("http://localhost:3000/path") == "http://localhost:3000"

    def test_invalid_url_passthrough(self):
        result = _extract_origin("not-a-url")
        assert result == "not-a-url"


# ── Contract tests: scope building ───────────────────────────────────────────

class TestBuildBrowserScope:
    def test_returns_operator_scope(self):
        scope = _build_browser_scope("https://example.com")
        assert isinstance(scope, OperatorScope)

    def test_surface_is_browser(self):
        scope = _build_browser_scope("https://example.com")
        assert scope.surface == SurfaceType.BROWSER

    def test_run_id_empty_for_executor(self):
        scope = _build_browser_scope("https://example.com")
        assert scope.run_id == ""

    def test_origin_extracted_from_url(self):
        scope = _build_browser_scope("https://example.com/path?q=1")
        assert "https://example.com" in scope.allowed_origins

    def test_extra_origins_appended(self):
        scope = _build_browser_scope(
            "https://example.com", extra_origins=["https://cdn.example.com"]
        )
        assert "https://cdn.example.com" in scope.allowed_origins

    def test_no_credential_access(self):
        scope = _build_browser_scope("https://example.com")
        assert scope.credential_access is False

    def test_external_network_true(self):
        scope = _build_browser_scope("https://example.com")
        assert scope.external_network is True

    def test_target_uris_contains_url(self):
        scope = _build_browser_scope("https://example.com/page")
        assert "https://example.com/page" in scope.target_uris


# ── Contract tests: step output extraction ───────────────────────────────────

class TestExtractStepOutputs:
    def test_empty_events(self):
        audit = _fake_audit(events=[])
        state = _extract_step_outputs(audit)
        assert state == {}

    def test_url_extracted(self):
        audit = _fake_audit(events=[
            _fake_step_event({"url": "https://example.com/final"})
        ])
        state = _extract_step_outputs(audit)
        assert state["url"] == "https://example.com/final"

    def test_title_extracted(self):
        audit = _fake_audit(events=[
            _fake_step_event({"title": "Example Domain"})
        ])
        state = _extract_step_outputs(audit)
        assert state["title"] == "Example Domain"

    def test_text_extracted_with_char_count(self):
        audit = _fake_audit(events=[
            _fake_step_event({"text": "Hello world", "char_count": 11})
        ])
        state = _extract_step_outputs(audit)
        assert state["text"] == "Hello world"
        assert state["char_count"] == 11

    def test_screenshot_path_extracted(self):
        audit = _fake_audit(events=[
            _fake_step_event({"path": "/tmp/ss.png", "bytes_length": 5000})
        ])
        state = _extract_step_outputs(audit)
        assert state["screenshot_path"] == "/tmp/ss.png"
        assert state["screenshot_bytes_length"] == 5000

    def test_interactive_snapshot_extracted(self):
        elements = [{"index": 1, "role": "button", "label": "Submit", "selector": "button"}]
        audit = _fake_audit(events=[
            _fake_step_event({"interactive_elements": elements, "interactive_count": 1})
        ])
        state = _extract_step_outputs(audit)
        assert state["interactive_elements"] == elements
        assert state["interactive_count"] == 1

    def test_non_step_events_ignored(self):
        from runtime.operator_surface.events import OperatorEventType
        event = MagicMock()
        event.event_type = OperatorEventType.PLAN_READY
        event.payload = {"result": {"url": "should-not-appear"}}
        audit = _fake_audit(events=[event])
        state = _extract_step_outputs(audit)
        assert "url" not in state


# ── Contract tests: print_error ──────────────────────────────────────────────

class TestPrintError:
    def test_json_mode_writes_valid_json(self, capsys):
        _print_error("something went wrong", output_json=True)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["success"] is False
        assert "something went wrong" in data["error"]

    def test_human_mode_writes_to_stderr(self, capsys):
        _print_error("something went wrong", output_json=False)
        err = capsys.readouterr().err
        assert "something went wrong" in err


class TestBrowserInteractiveSnapshot:
    def test_stub_snapshot_returns_mac_like_index_contract(self):
        result = snapshot_interactive(page=None, max_elements=10)
        assert result.success is True
        assert result.output["interactive_elements"] == []
        assert result.output["interactive_count"] == 0
        assert result.output["capture_mode"] == "browser_som"
        assert result.output["status"] == "stub"

    def test_snapshot_command_json_includes_elements_and_boundary(self, capsys):
        elements = [{"index": 1, "role": "link", "label": "Docs", "selector": "a"}]
        audit = _fake_audit(events=[_fake_step_event({
            "interactive_elements": elements,
            "interactive_count": 1,
            "capture_mode": "browser_som",
        })])
        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            return_value=(audit, {
                "url": "https://example.com",
                "title": "Example",
                "interactive_elements": elements,
                "interactive_count": 1,
                "capture_mode": "browser_som",
            }),
        ):
            rc = run_snapshot(
                "https://example.com",
                extra_origins=None,
                vault_root=None,
                max_elements=10,
                output_json=True,
            )
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["success"] is True
        assert data["interactive_count"] == 1
        assert data["interactive_elements"] == elements
        assert data["boundary"]["surface"] == "browser_only"
        assert data["boundary"]["credential_access"] is False


# ── Contract tests: run_open with mocked executor ────────────────────────────

class TestRunOpenContract:
    def _mock_plan(self, state_overrides=None):
        """Patch _run_operate_plan to return a fake audit + state."""
        audit = _fake_audit()
        state = {"url": "https://example.com", "title": "Test", "text": "page text",
                 "char_count": 9}
        if state_overrides:
            state.update(state_overrides)
        return audit, state

    def test_invalid_url_returns_1(self):
        rc = run_open("not-a-url", extra_origins=None, vault_root=None)
        assert rc == 1

    def test_empty_url_returns_1(self):
        rc = run_open("", extra_origins=None, vault_root=None)
        assert rc == 1

    def test_valid_url_with_mock_returns_0(self, capsys):
        audit = _fake_audit(outcome="COMPLETE")
        state = {"url": "https://example.com", "title": "Example", "text": "Hello",
                 "char_count": 5}
        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            return_value=(audit, state),
        ):
            rc = run_open("https://example.com", extra_origins=None, vault_root=Path("/tmp"))
        assert rc == 0

    def test_json_output_format(self, capsys):
        audit = _fake_audit(outcome="COMPLETE", run_id="rr-001")
        state = {"url": "https://example.com", "title": "Example", "text": "Text",
                 "char_count": 4}
        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            return_value=(audit, state),
        ):
            rc = run_open(
                "https://example.com",
                extra_origins=None,
                vault_root=Path("/tmp"),
                output_json=True,
            )
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert "run_id" in out
        assert "url" in out
        assert "title" in out
        assert "text" in out

    def test_text_truncation(self, capsys):
        audit = _fake_audit(outcome="COMPLETE")
        long_text = "A" * 5000
        state = {"url": "https://example.com", "title": "T", "text": long_text,
                 "char_count": 5000}
        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            return_value=(audit, state),
        ):
            run_open(
                "https://example.com",
                extra_origins=None,
                vault_root=Path("/tmp"),
                max_text_chars=100,
                output_json=True,
            )
        out = json.loads(capsys.readouterr().out)
        assert out["text_truncated"] is True
        assert len(out["text"]) == 100


# ── Contract tests: run_inspect ──────────────────────────────────────────────

class TestRunInspectContract:
    def test_invalid_url_returns_1(self):
        rc = run_inspect("ftp://bad", extra_origins=None, vault_root=None)
        assert rc == 1

    def test_json_output_has_steps_fields(self, capsys):
        audit = _fake_audit(outcome="COMPLETE", run_id="insp-001")
        state = {"url": "https://example.com", "title": "X", "text": "y",
                 "char_count": 1}
        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            return_value=(audit, state),
        ):
            run_inspect(
                "https://example.com",
                extra_origins=None,
                vault_root=Path("/tmp"),
                output_json=True,
            )
        out = json.loads(capsys.readouterr().out)
        assert "steps_completed" in out
        assert "steps_planned" in out
        assert "playwright_available" in out


# ── Contract tests: run_screenshot ───────────────────────────────────────────

class TestRunScreenshotContract:
    def test_invalid_url_returns_1(self):
        rc = run_screenshot("bad", output_path=None, extra_origins=None, vault_root=None)
        assert rc == 1

    def test_json_output_has_screenshot_path(self, capsys, tmp_path):
        audit = _fake_audit(outcome="COMPLETE", run_id="ss-001")
        png = tmp_path / "ss.png"
        _write_png(png, 2, 1, [b"\xff\xff\xff", b"\x00\x00\x00"])
        state = {"screenshot_path": str(png), "screenshot_bytes_length": png.stat().st_size}
        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            return_value=(audit, state),
        ):
            run_screenshot(
                "https://example.com",
                output_path=str(png),
                extra_origins=None,
                vault_root=tmp_path,
                output_json=True,
                wait_for_selector=".ready",
                settle_ms=123,
                full_page=False,
                clip_selector=".graph-wrap",
                require_nonblank=True,
            )
        out = json.loads(capsys.readouterr().out)
        assert "screenshot_path" in out
        assert "run_id" in out
        assert out["screenshot_bytes_length"] == png.stat().st_size
        assert out["wait_for_selector"] == ".ready"
        assert out["settle_ms"] == 123
        assert out["full_page"] is False
        assert out["clip_selector"] == ".graph-wrap"
        assert out["visual_verification"]["ok"] is True
        assert out["require_nonblank"] is True
        assert out["playwright_available"] is False
        assert "playwright_launch_error" in out
        assert "chromium_executable_path" in out

    def test_require_nonblank_rejects_blank_png(self, capsys, tmp_path):
        png = tmp_path / "blank.png"
        _write_png(png, 3, 1, [b"\xff\xff\xff", b"\xff\xff\xff", b"\xff\xff\xff"])
        audit = _fake_audit(outcome="COMPLETE", run_id="ss-blank")
        state = {"screenshot_path": str(png), "screenshot_bytes_length": png.stat().st_size}
        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            return_value=(audit, state),
        ):
            rc = run_screenshot(
                "https://example.com",
                output_path=str(png),
                extra_origins=None,
                vault_root=tmp_path,
                output_json=True,
                require_nonblank=True,
            )
        out = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert out["success"] is False
        assert out["visual_verification"]["ok"] is False
        assert out["visual_verification"]["reason"] == "blank-or-near-uniform"

    def test_plan_waits_for_selector_before_screenshot(self, tmp_path):
        captured = {}
        audit = _fake_audit(outcome="COMPLETE", run_id="ss-002")

        def fake_run_operate_plan(**kwargs):
            captured["plan"] = kwargs["plan"]
            return audit, {"screenshot_path": str(tmp_path / "ss.png")}

        with patch(
            "runtime.operator_surface.browser.operator._run_operate_plan",
            side_effect=fake_run_operate_plan,
        ):
            rc = run_screenshot(
                "https://example.com",
                output_path=str(tmp_path / "ss.png"),
                extra_origins=None,
                vault_root=tmp_path,
                wait_for_selector=".graph",
                wait_timeout_ms=777,
                settle_ms=321,
                full_page=False,
                clip_selector=".graph-wrap",
            )

        assert rc == 0
        assert [step["action_type"] for step in captured["plan"]] == [
            "navigate",
            "wait_for",
            "screenshot",
        ]
        assert captured["plan"][1]["target"] == ".graph"
        assert captured["plan"][1]["timeout_ms"] == 777
        assert captured["plan"][2]["settle_ms"] == 321
        assert captured["plan"][2]["full_page"] is False
        assert captured["plan"][2]["clip_selector"] == ".graph-wrap"


class TestPngVisualVerifier:
    def test_blank_png_is_not_nonblank(self, tmp_path):
        png = tmp_path / "blank.png"
        _write_png(png, 2, 2, [b"\xff\xff\xff"] * 4)
        result = analyze_png_nonblank(png)
        assert result["png"] is True
        assert result["ok"] is False
        assert result["unique_color_count"] == 1

    def test_multicolor_png_is_nonblank(self, tmp_path):
        png = tmp_path / "graphish.png"
        _write_png(
            png,
            2,
            2,
            [b"\xff\xff\xff", b"\x00\x00\x00", b"\x38\xbd\xf8", b"\x63\x66\xf1"],
        )
        result = analyze_png_nonblank(png)
        assert result["png"] is True
        assert result["ok"] is True
        assert result["unique_color_count"] == 4


# ── Contract tests: run_replay ────────────────────────────────────────────────

class TestRunReplayContract:
    def test_empty_run_id_returns_1(self):
        rc = run_replay("", vault_root=None)
        assert rc == 1

    def test_missing_run_id_returns_1(self, tmp_path):
        rc = run_replay("no-such-run-999", vault_root=tmp_path)
        assert rc == 1


# ── Contract tests: run_list_runs ─────────────────────────────────────────────

class TestRunListRunsContract:
    def test_empty_dir_returns_0(self, tmp_path):
        # Creates 07_LOGS/Agent-Activity so get_audit_dir doesn't fail
        (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
        rc = run_list_runs(vault_root=tmp_path)
        assert rc == 0

    def test_json_output_has_runs_key(self, tmp_path, capsys):
        (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
        run_list_runs(vault_root=tmp_path, output_json=True)
        out = json.loads(capsys.readouterr().out)
        assert "runs" in out
        assert "count" in out

    def test_surface_filter_applied(self, tmp_path, capsys):
        audit_dir = tmp_path / "07_LOGS" / "Agent-Activity"
        audit_dir.mkdir(parents=True)
        # Write a fake audit JSON with surface=browser
        (audit_dir / "run-browser-001.json").write_text(json.dumps({
            "run_id": "run-browser-001",
            "workflow_id": "browser_open",
            "surface": "browser",
            "outcome": "COMPLETE",
            "started_at": "2026-04-16T10:00:00Z",
            "steps_completed": 4,
            "steps_planned": 4,
        }), encoding="utf-8")
        # Write a fake audit JSON with surface=other
        (audit_dir / "run-other-001.json").write_text(json.dumps({
            "run_id": "run-other-001",
            "workflow_id": "some_workflow",
            "surface": "other",
            "outcome": "COMPLETE",
            "started_at": "2026-04-16T09:00:00Z",
            "steps_completed": 1,
            "steps_planned": 1,
        }), encoding="utf-8")
        run_list_runs(vault_root=tmp_path, surface_filter="browser", output_json=True)
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 1
        assert out["runs"][0]["surface"] == "browser"


# ── CLI integration: parser wiring ────────────────────────────────────────────

class TestCliParserWiring:
    def test_operate_browser_open_parses(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args(["operate", "browser", "open", "https://example.com"])
        assert args.url == "https://example.com"
        assert args.func.__name__ == "cmd_operate_browser_open"

    def test_operate_browser_inspect_parses(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args(["operate", "browser", "inspect", "https://example.com"])
        assert args.url == "https://example.com"
        assert args.func.__name__ == "cmd_operate_browser_inspect"

    def test_operate_browser_screenshot_parses(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args(["operate", "browser", "screenshot", "https://example.com"])
        assert args.url == "https://example.com"
        assert args.func.__name__ == "cmd_operate_browser_screenshot"

    def test_operate_browser_screenshot_output_flag(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args([
            "operate", "browser", "screenshot", "https://example.com",
            "--output", "/tmp/ss.png"
        ])
        assert args.output == "/tmp/ss.png"

    def test_operate_browser_screenshot_readiness_flags(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args([
            "operate", "browser", "screenshot", "https://example.com",
            "--wait-for", ".graph",
            "--wait-timeout-ms", "7000",
            "--settle-ms", "500",
            "--viewport-only",
            "--clip-selector", ".graph-wrap",
            "--require-nonblank",
            "--min-unique-colors", "4",
            "--max-dominant-ratio", "0.9",
        ])
        assert args.wait_for == ".graph"
        assert args.wait_timeout_ms == 7000
        assert args.settle_ms == 500
        assert args.viewport_only is True
        assert args.clip_selector == ".graph-wrap"
        assert args.require_nonblank is True
        assert args.min_unique_colors == 4
        assert args.max_dominant_ratio == 0.9

    def test_operate_browser_replay_parses(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args(["operate", "browser", "replay", "abc123"])
        assert args.run_id == "abc123"
        assert args.func.__name__ == "cmd_operate_browser_replay"

    def test_operate_browser_list_runs_parses(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args(["operate", "browser", "list-runs"])
        assert args.func.__name__ == "cmd_operate_browser_list_runs"

    def test_json_flag_parses(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args([
            "operate", "browser", "open", "https://example.com", "--json"
        ])
        assert args.output_json is True

    def test_allowed_origin_flag_repeatable(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args([
            "operate", "browser", "open", "https://example.com",
            "--allowed-origin", "https://cdn.example.com",
            "--allowed-origin", "https://api.example.com",
        ])
        assert "https://cdn.example.com" in args.allowed_origin
        assert "https://api.example.com" in args.allowed_origin

    def test_max_text_flag(self):
        from runtime.cli.main import _build_parser
        p = _build_parser()
        args = p.parse_args([
            "operate", "browser", "open", "https://example.com",
            "--max-text", "500",
        ])
        assert args.max_text == 500


# ── Integration tests (require real browser) ─────────────────────────────────

@pytest.mark.skipif(
    not __import__("runtime.operator_surface.tests.conftest", fromlist=["PLAYWRIGHT_AVAILABLE"]).PLAYWRIGHT_AVAILABLE,
    reason="playwright not installed"
)
class TestBrowserIntegration:
    """
    End-to-end integration tests requiring a real Chromium instance.
    Skipped if playwright is not installed; individual tests skip if browser
    cannot be launched.
    """

    def test_run_open_live(self, browser_available, tmp_path):
        if not browser_available:
            pytest.skip("Browser not available")
        (tmp_path / "CLAUDE.md").write_text("# test vault")
        (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
        rc = run_open(
            "https://example.com",
            extra_origins=None,
            vault_root=tmp_path,
            output_json=False,
        )
        assert rc == 0

    def test_run_inspect_live_json(self, browser_available, tmp_path, capsys):
        if not browser_available:
            pytest.skip("Browser not available")
        (tmp_path / "CLAUDE.md").write_text("# test vault")
        (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
        rc = run_inspect(
            "https://example.com",
            extra_origins=None,
            vault_root=tmp_path,
            output_json=True,
        )
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert "run_id" in out
        assert out["run_id"]

    def test_run_screenshot_live(self, browser_available, tmp_path):
        if not browser_available:
            pytest.skip("Browser not available")
        (tmp_path / "CLAUDE.md").write_text("# test vault")
        (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
        out_path = str(tmp_path / "test_ss.png")
        rc = run_screenshot(
            "https://example.com",
            output_path=out_path,
            extra_origins=None,
            vault_root=tmp_path,
        )
        assert rc == 0
        # In real mode, file should exist and be non-trivial
        p = Path(out_path)
        if p.exists():
            assert p.stat().st_size > 1000

    def test_run_open_then_replay(self, browser_available, tmp_path, capsys):
        if not browser_available:
            pytest.skip("Browser not available")
        (tmp_path / "CLAUDE.md").write_text("# test vault")
        (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
        # Run open and capture JSON to get run_id
        rc = run_open(
            "https://example.com",
            extra_origins=None,
            vault_root=tmp_path,
            output_json=True,
        )
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        run_id = out["run_id"]
        assert run_id
        # Now replay it
        capsys.readouterr()
        rc2 = run_replay(run_id, vault_root=tmp_path)
        assert rc2 == 0

    def test_list_runs_includes_live_run(self, browser_available, tmp_path, capsys):
        if not browser_available:
            pytest.skip("Browser not available")
        (tmp_path / "CLAUDE.md").write_text("# test vault")
        (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
        # Run first so there's at least one artifact
        run_open(
            "https://example.com",
            extra_origins=None,
            vault_root=tmp_path,
            output_json=False,
        )
        capsys.readouterr()
        rc = run_list_runs(vault_root=tmp_path, output_json=True)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] >= 1
        assert any(r["surface"] == "browser" for r in out["runs"])
