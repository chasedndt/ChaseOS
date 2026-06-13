"""Local stdio client for Runtime MCP smoke tests.

This is a process-boundary test harness, not a privileged adapter. It starts
the local ChaseOS Runtime MCP server as a child process and exchanges
newline-delimited JSON-RPC messages over stdin/stdout.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, TextIO


class MCPStdioClientError(RuntimeError):
    """Raised when the local stdio smoke client cannot complete a request."""


class MCPStdioSmokeClient:
    """Minimal local JSON-RPC stdio client for ChaseOS Runtime MCP."""

    def __init__(
        self,
        *,
        command: list[str] | None = None,
        cwd: Path | None = None,
        vault_root: Path | None = None,
        timeout_s: float = 5.0,
        env: dict[str, str] | None = None,
    ) -> None:
        self.command = command or [sys.executable, "-m", "runtime.mcp.server"]
        self.cwd = cwd or Path(__file__).resolve().parents[2]
        self.vault_root = vault_root
        self.timeout_s = timeout_s
        self.env = env or {}
        self._process: subprocess.Popen[str] | None = None
        self._stdout: queue.Queue[str] = queue.Queue()
        self._stderr: queue.Queue[str] = queue.Queue()
        self._next_id = 1

    def __enter__(self) -> "MCPStdioSmokeClient":
        return self.start()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def start(self) -> "MCPStdioSmokeClient":
        if self._process is not None:
            return self
        env = os.environ.copy()
        env.update(self.env)
        env["PYTHONUNBUFFERED"] = "1"
        if self.vault_root is not None:
            env["CHASEOS_MCP_VAULT_ROOT"] = str(self.vault_root)
        self._process = subprocess.Popen(
            self.command,
            cwd=str(self.cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=env,
        )
        if self._process.stdout is not None:
            threading.Thread(target=self._drain_stream, args=(self._process.stdout, self._stdout), daemon=True).start()
        if self._process.stderr is not None:
            threading.Thread(target=self._drain_stream, args=(self._process.stderr, self._stderr), daemon=True).start()
        return self

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass
        try:
            process.terminate()
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        request_id: str | int | None = None,
    ) -> dict[str, Any]:
        if request_id is None:
            request_id = self._next_id
            self._next_id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)
        return self.read_response()

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)

    def send(self, payload: dict[str, Any]) -> None:
        process = self._require_process()
        if process.stdin is None:
            raise MCPStdioClientError("Runtime MCP subprocess stdin is unavailable")
        if process.poll() is not None:
            raise MCPStdioClientError(f"Runtime MCP subprocess already exited: {self.stderr_text()}")
        process.stdin.write(json.dumps(payload, sort_keys=True) + "\n")
        process.stdin.flush()

    def read_response(self) -> dict[str, Any]:
        try:
            line = self._stdout.get(timeout=self.timeout_s)
        except queue.Empty as exc:
            process = self._require_process()
            status = process.poll()
            detail = f" process_exit={status}" if status is not None else ""
            stderr = self.stderr_text()
            raise MCPStdioClientError(f"Timed out waiting for Runtime MCP response.{detail} stderr={stderr}") from exc
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MCPStdioClientError(f"Runtime MCP returned invalid JSON: {line}") from exc
        if not isinstance(payload, dict):
            raise MCPStdioClientError(f"Runtime MCP returned non-object JSON: {line}")
        return payload

    def stderr_text(self) -> str:
        lines: list[str] = []
        while True:
            try:
                lines.append(self._stderr.get_nowait())
            except queue.Empty:
                break
        return "".join(lines).strip()

    def _require_process(self) -> subprocess.Popen[str]:
        if self._process is None:
            self.start()
        if self._process is None:
            raise MCPStdioClientError("Runtime MCP subprocess did not start")
        return self._process

    @staticmethod
    def _drain_stream(stream: TextIO, target: queue.Queue[str]) -> None:
        for line in stream:
            target.put(line)
