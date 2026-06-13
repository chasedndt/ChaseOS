"""Fail-closed wrapper for the external browser-use CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from runtime.browser_runtime.adapter import BrowserRuntimeAdapter, BrowserRuntimePolicyError
from runtime.browser_runtime.models import (
    BrowserActionRecord,
    BrowserArtifact,
    BrowserRunRequest,
    BrowserRunResult,
    BrowserRuntimeConfig,
    BrowserRuntimeProvider,
    now_iso,
)


class BrowserUseCLIAdapter(BrowserRuntimeAdapter):
    """Minimal wrapper around `browser-use`, disabled unless explicitly available."""

    provider = BrowserRuntimeProvider.BROWSER_USE_CLI

    def __init__(self, config: BrowserRuntimeConfig | None = None, executable: str = "browser-use"):
        super().__init__(config=config)
        self.executable = executable
        self._last_state: dict[str, Any] = {}

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def run_task(self, request: BrowserRunRequest, *, vault_root: Path | str | None = None) -> BrowserRunResult:
        run_id = request.effective_run_id()
        started = now_iso()
        try:
            self.validate_request(request)
        except BrowserRuntimePolicyError as exc:
            return self._blocked_result(request, run_id, started, str(exc))

        if not self.available():
            return self._blocked_result(
                request,
                run_id,
                started,
                "browser-use CLI is not installed or not on PATH; dependencies are not installed automatically.",
            )

        commands = [
            [self.executable, "open", request.url],
            [self.executable, "state"],
        ]
        actions: list[BrowserActionRecord] = []
        for command in commands:
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                    shell=False,
                )
            except Exception as exc:
                return BrowserRunResult(
                    run_id=run_id,
                    status="failed",
                    provider=self.provider,
                    mode=request.mode,
                    url=request.url,
                    task=request.task,
                    actions=actions
                    + [
                        BrowserActionRecord(
                            action_type="browser_use_cli",
                            target=" ".join(command),
                            status="failed",
                            blocked_reason=str(exc),
                        )
                    ],
                    error=str(exc),
                    summary="browser-use CLI invocation failed.",
                    started_at=started,
                    ended_at=now_iso(),
                    security_flags=self._security_flags(live_browser_control=True),
                )

            status = "succeeded" if completed.returncode == 0 else "failed"
            output = (completed.stdout or completed.stderr or "").strip()
            actions.append(
                BrowserActionRecord(
                    action_type=f"browser_use_{command[1]}",
                    target=request.url if command[1] == "open" else "state",
                    status=status,
                    notes=output[:1000],
                    metadata={"returncode": completed.returncode},
                )
            )
            if completed.returncode != 0:
                return BrowserRunResult(
                    run_id=run_id,
                    status="failed",
                    provider=self.provider,
                    mode=request.mode,
                    url=request.url,
                    task=request.task,
                    actions=actions,
                    error=output or f"browser-use {command[1]} failed",
                    summary="browser-use CLI command failed.",
                    started_at=started,
                    ended_at=now_iso(),
                    security_flags=self._security_flags(live_browser_control=True),
                )
            if command[1] == "state":
                self._last_state = {"raw_state": output}

        return BrowserRunResult(
            run_id=run_id,
            status="succeeded",
            provider=self.provider,
            mode=request.mode,
            url=request.url,
            task=request.task,
            actions=actions,
            summary="browser-use CLI opened the URL and returned state.",
            started_at=started,
            ended_at=now_iso(),
            security_flags=self._security_flags(live_browser_control=True),
        )

    def get_state(self) -> dict[str, Any]:
        return dict(self._last_state)

    def capture_screenshot(self, path: Path | str) -> BrowserArtifact:
        if not self.available():
            return BrowserArtifact(
                artifact_type="screenshot",
                path=str(path),
                description="Blocked: browser-use CLI unavailable.",
                redacted=False,
                metadata={"blocked": True},
            )
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [self.executable, "screenshot", str(target)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            shell=False,
        )
        return BrowserArtifact(
            artifact_type="screenshot",
            path=str(target),
            description="browser-use CLI screenshot command result.",
            redacted=False,
            metadata={"returncode": completed.returncode},
        )

    def close(self) -> None:
        if self.available():
            subprocess.run([self.executable, "close"], capture_output=True, text=True, timeout=30, shell=False)
        self._last_state = {}

    def summarize_run(self, result: BrowserRunResult) -> str:
        return (
            f"browser-use-cli run {result.run_id} ended with {result.status}; "
            "real profiles and credentials remained disabled by ChaseOS config."
        )

    def _blocked_result(
        self,
        request: BrowserRunRequest,
        run_id: str,
        started: str,
        reason: str,
    ) -> BrowserRunResult:
        return BrowserRunResult(
            run_id=run_id,
            status="blocked",
            provider=self.provider,
            mode=request.mode,
            url=request.url,
            task=request.task,
            actions=[
                BrowserActionRecord(
                    action_type="browser_use_cli_preflight",
                    target=request.url,
                    status="blocked",
                    blocked_reason=reason,
                )
            ],
            error=reason,
            summary="browser-use CLI adapter failed closed before browser execution.",
            started_at=started,
            ended_at=now_iso(),
            security_flags=self._security_flags(live_browser_control=False),
        )

    def _security_flags(self, *, live_browser_control: bool) -> dict[str, Any]:
        return {
            "real_profile_used": False,
            "credentials_allowed": False,
            "cookies_exported": False,
            "canonical_writeback": False,
            "skill_activation": False,
            "live_browser_control": live_browser_control,
        }
