"""Bounded live Browser CDP launcher/client primitives.

These primitives are intentionally small and dependency-light. They only support the read-only
proof path: isolated local browser launch, navigation, title/url/visible text/DOM snapshot, and
screenshot capture. They do not use a real profile and they do not read cookies, storage,
credentials, or browser history.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_controller_setup_readiness import resolve_browser_executable


class BrowserCDPLiveError(RuntimeError):
    """Raised when bounded live CDP proof primitives cannot proceed."""


def _find_browser_executable() -> str:
    executable = resolve_browser_executable()
    if executable:
        return executable
    raise BrowserCDPLiveError(
        "No Chromium-compatible browser executable found. Set CHASEOS_BROWSER_CDP_EXECUTABLE."
    )


class IsolatedBrowserLauncher:
    """Launch an isolated local Chromium-compatible browser with remote debugging enabled."""

    def __init__(self, *, port: int = 0, headless: bool = True, timeout_seconds: int = 10) -> None:
        self.port = port or _free_port()
        self.headless = headless
        self.timeout_seconds = timeout_seconds
        self.user_data_dir: str | None = None
        self.process: subprocess.Popen[str] | None = None

    def ensure_available(self) -> dict[str, Any]:
        executable = _find_browser_executable()
        return {"browser_executable_found": True, "browser_executable": executable}

    def launch(self) -> dict[str, Any]:
        executable = _find_browser_executable()
        self.user_data_dir = tempfile.mkdtemp(prefix="chaseos-cdp-profile-", dir=str(_profile_temp_root()))
        args = [
            executable,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-sync",
            "--disable-extensions",
            "--disable-background-networking",
            "about:blank",
        ]
        if self.headless:
            args.insert(1, "--headless=new")
            args.insert(2, "--disable-gpu")
        popen_kwargs: dict[str, Any] = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
        }
        creationflags = _hidden_subprocess_creationflags()
        if creationflags:
            popen_kwargs["creationflags"] = creationflags
        self.process = subprocess.Popen(args, **popen_kwargs)
        endpoint = f"http://127.0.0.1:{self.port}"
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"{endpoint}/json/version", timeout=1) as response:
                    if response.status == 200:
                        return {
                            "cdp_endpoint": endpoint,
                            "browser_pid": self.process.pid,
                            "user_data_dir": "[REDACTED]",
                            "profile_policy": "throwaway_only",
                        }
            except Exception:
                time.sleep(0.1)
        self.close()
        raise BrowserCDPLiveError("Timed out waiting for browser CDP endpoint")

    def close(self) -> None:
        proc = self.process
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        if self.user_data_dir:
            shutil.rmtree(self.user_data_dir, ignore_errors=True)
            self.user_data_dir = None


def _profile_temp_root() -> Path:
    """Return a writable parent for throwaway browser profiles."""
    env_root = os.environ.get("CHASEOS_BROWSER_CDP_PROFILE_ROOT", "").strip()
    candidates = [Path(env_root)] if env_root else []
    candidates.extend(
        [
            Path.cwd() / "07_LOGS" / "Browser-Runs" / "_tmp_cdp_profiles",
            Path(r"C:\tmp"),
            Path(tempfile.gettempdir()),
        ]
    )
    for candidate in candidates:
        if not str(candidate):
            continue
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = tempfile.mkdtemp(prefix="chaseos-cdp-profile-probe-", dir=str(candidate))
            shutil.rmtree(probe, ignore_errors=True)
            return candidate
        except Exception:
            continue
    raise BrowserCDPLiveError("No writable directory available for throwaway browser profile")


def _hidden_subprocess_creationflags() -> int:
    """Return Windows flags that prevent transient console windows."""
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class MinimalCDPClient:
    """Minimal CDP websocket client for the read-only proof path."""

    def __init__(self, *, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds
        self.sock: socket.socket | None = None
        self.next_id = 0
        self.endpoint = ""

    def connect(self, endpoint: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        target = self._open_or_create_page_target()
        ws_url = target.get("webSocketDebuggerUrl")
        if not ws_url:
            raise BrowserCDPLiveError("CDP target did not expose webSocketDebuggerUrl")
        self.sock = _open_websocket(str(ws_url), timeout=self.timeout_seconds)
        self._call("Page.enable")
        self._call("Runtime.enable")

    def navigate(self, target_url: str) -> None:
        self._call("Page.navigate", {"url": target_url})
        time.sleep(0.5)

    def read_state(self) -> dict[str, Any]:
        title = self._eval("document.title")
        url = self._eval("location.href")
        visible_text = self._eval("document.body ? document.body.innerText.slice(0, 5000) : ''")
        dom_outer = self._eval("document.documentElement ? document.documentElement.outerHTML.slice(0, 100000) : ''")
        return {
            "title": title,
            "url": url,
            "visible_text": visible_text,
            "dom_snapshot": {"outer_html_preview": dom_outer},
        }

    def capture_screenshot(self) -> bytes:
        result = self._call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        data = result.get("data")
        if not isinstance(data, str):
            raise BrowserCDPLiveError("CDP screenshot did not return base64 data")
        return base64.b64decode(data)

    def move(self, x: float, y: float) -> None:
        """Dispatch a bounded mouse move in viewport coordinates."""
        self._call(
            "Input.dispatchMouseEvent",
            {"type": "mouseMoved", "x": x, "y": y, "button": "none"},
        )

    def click(self, x: float, y: float) -> None:
        """Dispatch a bounded left-click in viewport coordinates."""
        self.move(x, y)
        self._call(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
        )
        self._call(
            "Input.dispatchMouseEvent",
            {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1},
        )

    def drag(self, start_x: float, start_y: float, end_x: float, end_y: float, *, steps: int = 8) -> None:
        """Dispatch a bounded mouse drag in viewport coordinates."""
        self.move(start_x, start_y)
        self._call(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": start_x, "y": start_y, "button": "left", "clickCount": 1},
        )
        safe_steps = max(1, steps)
        for index in range(1, safe_steps + 1):
            ratio = index / safe_steps
            self._call(
                "Input.dispatchMouseEvent",
                {
                    "type": "mouseMoved",
                    "x": start_x + ((end_x - start_x) * ratio),
                    "y": start_y + ((end_y - start_y) * ratio),
                    "button": "left",
                    "buttons": 1,
                },
            )
        self._call(
            "Input.dispatchMouseEvent",
            {"type": "mouseReleased", "x": end_x, "y": end_y, "button": "left", "clickCount": 1},
        )

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _open_or_create_page_target(self) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.endpoint}/json/new?about:blank",
            method="PUT",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, dict):
            return payload
        raise BrowserCDPLiveError("CDP /json/new response was not an object")

    def _eval(self, expression: str) -> Any:
        result = self._call("Runtime.evaluate", {"expression": expression, "returnByValue": True})
        value = result.get("result", {}).get("value")
        return value

    def _call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.sock:
            raise BrowserCDPLiveError("CDP websocket is not connected")
        self.next_id += 1
        msg_id = self.next_id
        _send_ws_json(self.sock, {"id": msg_id, "method": method, "params": params or {}})
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            payload = _recv_ws_json(self.sock)
            if payload.get("id") != msg_id:
                continue
            if "error" in payload:
                raise BrowserCDPLiveError(f"CDP error for {method}: {payload['error']}")
            return dict(payload.get("result") or {})
        raise BrowserCDPLiveError(f"Timed out waiting for CDP response to {method}")


def _open_websocket(ws_url: str, *, timeout: int) -> socket.socket:
    # Supports ws://host:port/path only; local browser CDP never requires TLS here.
    if not ws_url.startswith("ws://"):
        raise BrowserCDPLiveError("Only local ws:// CDP websocket endpoints are supported")
    rest = ws_url[len("ws://") :]
    host_port, path = rest.split("/", 1)
    if ":" in host_port:
        host, port_text = host_port.rsplit(":", 1)
        port = int(port_text)
    else:
        host, port = host_port, 80
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    sock = socket.create_connection((host, port), timeout=timeout)
    request = (
        f"GET /{path} HTTP/1.1\r\n"
        f"Host: {host_port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.sendall(request.encode("ascii"))
    response = sock.recv(4096)
    if b" 101 " not in response.split(b"\r\n", 1)[0]:
        sock.close()
        raise BrowserCDPLiveError("CDP websocket handshake failed")
    return sock


def _send_ws_json(sock: socket.socket, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = bytearray([0x81])
    length = len(data)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.extend([0x80 | 126, *struct.pack("!H", length)])
    else:
        header.extend([0x80 | 127, *struct.pack("!Q", length)])
    mask = os.urandom(4)
    masked = bytes(byte ^ mask[i % 4] for i, byte in enumerate(data))
    sock.sendall(bytes(header) + mask + masked)


def _recv_ws_json(sock: socket.socket) -> dict[str, Any]:
    first = sock.recv(2)
    if len(first) < 2:
        raise BrowserCDPLiveError("CDP websocket closed")
    opcode = first[0] & 0x0F
    length = first[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", _recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact(sock, 8))[0]
    data = _recv_exact(sock, length)
    if opcode == 8:
        raise BrowserCDPLiveError("CDP websocket closed")
    if opcode not in {1, 2}:
        return {}
    return json.loads(data.decode("utf-8"))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise BrowserCDPLiveError("CDP websocket closed while reading frame")
        chunks.extend(chunk)
    return bytes(chunks)
