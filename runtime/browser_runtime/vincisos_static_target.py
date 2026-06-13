"""Temporary local static target proof for future VincisOS browser tests.

This helper starts a local HTTP server only long enough to prove the target URL
passes the no-execution VincisOS readiness preflight. It never opens a browser.
"""

from __future__ import annotations

import argparse
import json
import threading
from dataclasses import asdict, dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from runtime.browser_runtime.vincisos_preflight import (
    VincisOSBrowserPreflightRequest,
    evaluate_vincisos_browser_preflight,
)


TARGET_DIR = Path(__file__).resolve().parent / "test_targets"
TARGET_FILE = TARGET_DIR / "vincisos_shadow.html"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    """HTTP handler with request logging suppressed for clean test output."""

    def log_message(self, format: str, *args: Any) -> None:
        return None


@dataclass(frozen=True)
class VincisOSStaticTargetPreflightResult:
    ok: bool
    status: str
    target_url: str | None
    target_file: str
    server_started: bool
    server_stopped: bool
    preflight: dict[str, Any] | None
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    screenshot_attempted: bool = False
    trusted_write_attempted: bool = False
    canonical_writeback_attempted: bool = False
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_vincisos_static_target_preflight(host: str = "127.0.0.1", port: int = 0) -> VincisOSStaticTargetPreflightResult:
    """Serve the static target briefly and run the local-only readiness check."""
    if not TARGET_FILE.exists():
        return VincisOSStaticTargetPreflightResult(
            ok=False,
            status="blocked_static_target_missing",
            target_url=None,
            target_file=str(TARGET_FILE),
            server_started=False,
            server_stopped=True,
            preflight=None,
            error="Static VincisOS target file is missing.",
        )

    handler = partial(QuietStaticHandler, directory=str(TARGET_DIR))
    server: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    server_started = False
    server_stopped = False
    target_url: str | None = None

    try:
        server = ThreadingHTTPServer((host, port), handler)
        server_started = True
        actual_port = int(server.server_address[1])
        target_url = f"http://{host}:{actual_port}/{TARGET_FILE.name}"
        thread = threading.Thread(target=server.serve_forever, name="vincisos-static-target", daemon=True)
        thread.start()
        preflight = evaluate_vincisos_browser_preflight(
            VincisOSBrowserPreflightRequest(
                target_url=target_url,
                target_name="VincisOS static shadow target",
                require_running_target=True,
                probe_reachability=True,
            )
        )
        server.shutdown()
        server.server_close()
        server_stopped = True
        server = None
        if thread is not None:
            thread.join(timeout=2.0)
            thread = None
        return VincisOSStaticTargetPreflightResult(
            ok=preflight.ok,
            status="static_target_preflight_ready_no_browser" if preflight.ok else "blocked_static_target_preflight",
            target_url=target_url,
            target_file=str(TARGET_FILE),
            server_started=server_started,
            server_stopped=server_stopped,
            preflight=preflight.as_dict(),
        )
    except OSError as exc:
        return VincisOSStaticTargetPreflightResult(
            ok=False,
            status="blocked_static_target_server_error",
            target_url=target_url,
            target_file=str(TARGET_FILE),
            server_started=server_started,
            server_stopped=server_stopped,
            preflight=None,
            error=str(exc),
        )
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
            server_stopped = True
        if thread is not None:
            thread.join(timeout=2.0)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the no-browser VincisOS static target preflight.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text output is not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = run_vincisos_static_target_preflight(host=args.host, port=args.port)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
