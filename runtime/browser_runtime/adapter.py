"""Adapter contracts and shadow proof provider for ChaseOS browser runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from runtime.browser_runtime.models import (
    BrowserActionRecord,
    BrowserArtifact,
    BrowserRunRequest,
    BrowserRunResult,
    BrowserRuntimeConfig,
    BrowserRuntimeProvider,
    domain_from_url,
    now_iso,
)


class BrowserRuntimePolicyError(ValueError):
    """Raised when a browser run request violates the bounded runtime policy."""


class BrowserRuntimeAdapter(ABC):
    """Base interface for bounded browser runtime providers."""

    provider: BrowserRuntimeProvider

    def __init__(self, config: BrowserRuntimeConfig | None = None):
        self.config = config or BrowserRuntimeConfig()

    @abstractmethod
    def run_task(self, request: BrowserRunRequest, *, vault_root: Path | str | None = None) -> BrowserRunResult:
        """Run one bounded browser task."""

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        """Return current browser state if available."""

    @abstractmethod
    def capture_screenshot(self, path: Path | str) -> BrowserArtifact:
        """Capture a screenshot or proof artifact."""

    @abstractmethod
    def close(self) -> None:
        """Close or release provider resources."""

    @abstractmethod
    def summarize_run(self, result: BrowserRunResult) -> str:
        """Summarize a run for logs and draft skill evidence."""

    def validate_request(self, request: BrowserRunRequest) -> None:
        """Fail closed if the run asks for a forbidden browser authority."""
        if not self.config.enabled:
            raise BrowserRuntimePolicyError("browser runtime is disabled by configuration")
        if request.provider.value not in self.config.allowed_providers:
            raise BrowserRuntimePolicyError(f"provider not allowed: {request.provider.value}")
        if request.mode != "shadow":
            raise BrowserRuntimePolicyError("only shadow mode is enabled in this spike")
        if request.use_real_profile or self.config.allow_real_profile:
            raise BrowserRuntimePolicyError("real browser profiles are forbidden by default")
        if request.allow_credentials or self.config.allow_credentials:
            raise BrowserRuntimePolicyError("credential access is forbidden by default")
        if self.config.allow_shell_execution:
            raise BrowserRuntimePolicyError("browser runtime shell execution is forbidden")
        if self.config.allow_cookie_export:
            raise BrowserRuntimePolicyError("cookie export is forbidden")
        if self.config.allow_public_tunnel:
            raise BrowserRuntimePolicyError("public browser tunnels are forbidden")

        parsed = urlparse(request.url)
        if parsed.scheme not in {"http", "https", "file"}:
            raise BrowserRuntimePolicyError(f"unsupported URL scheme: {parsed.scheme or '<none>'}")
        if parsed.scheme != "file" and not parsed.hostname:
            raise BrowserRuntimePolicyError("URL must include a hostname")

        domain = domain_from_url(request.url)
        combined_allowed = set(self.config.allowed_domains) | set(request.allowed_domains)
        if parsed.scheme != "file" and combined_allowed and domain not in combined_allowed:
            raise BrowserRuntimePolicyError(f"domain is not allowlisted for this spike: {domain}")
        for forbidden in self.config.forbidden_domains:
            if forbidden and forbidden in domain:
                raise BrowserRuntimePolicyError(f"domain is forbidden for browser runtime spike: {domain}")


class ShadowBrowserRuntimeAdapter(BrowserRuntimeAdapter):
    """Safe proof provider that records a browser-shaped run without live browsing."""

    provider = BrowserRuntimeProvider.SHADOW

    def __init__(self, config: BrowserRuntimeConfig | None = None):
        super().__init__(config=config or BrowserRuntimeConfig(enabled=True))
        self._state: dict[str, Any] = {}

    def run_task(self, request: BrowserRunRequest, *, vault_root: Path | str | None = None) -> BrowserRunResult:
        self.validate_request(request)
        run_id = request.effective_run_id()
        started = now_iso()
        domain = domain_from_url(request.url) or "local-file"
        self._state = {
            "url": request.url,
            "domain": domain,
            "title": f"Shadow state for {domain}",
            "mode": request.mode,
            "provider": self.provider.value,
            "live_browser": False,
        }

        actions = [
            BrowserActionRecord(
                action_type="open",
                target=request.url,
                status="succeeded",
                notes="Shadow proof only; no live browser profile, cookies, or credentials used.",
            ),
            BrowserActionRecord(
                action_type="get_state",
                target=domain,
                status="succeeded",
                metadata=self._state,
            ),
        ]
        if request.harmless_action:
            actions.append(
                BrowserActionRecord(
                    action_type=request.harmless_action,
                    target=request.url,
                    status="succeeded",
                    notes="Harmless shadow observation recorded for adapter proof.",
                )
            )

        artifact_path = Path(vault_root or ".") / "07_LOGS" / "Browser-Runs" / f"{run_id}-shadow-screenshot.txt"
        artifact = self.capture_screenshot(artifact_path)
        result = BrowserRunResult(
            run_id=run_id,
            status="succeeded",
            provider=self.provider,
            mode=request.mode,
            url=request.url,
            task=request.task,
            actions=actions,
            artifacts=[artifact],
            summary="Shadow browser runtime proof completed without live browser control.",
            started_at=started,
            ended_at=now_iso(),
            security_flags={
                "real_profile_used": False,
                "credentials_allowed": False,
                "cookies_exported": False,
                "canonical_writeback": False,
                "skill_activation": False,
                "live_browser_control": False,
            },
        )
        return result

    def get_state(self) -> dict[str, Any]:
        return dict(self._state)

    def capture_screenshot(self, path: Path | str) -> BrowserArtifact:
        proof_path = Path(path)
        proof_path.parent.mkdir(parents=True, exist_ok=True)
        proof_path.write_text(
            "ChaseOS Browser Runtime shadow screenshot placeholder.\n"
            "No live browser was launched and no credentials/profile were used.\n",
            encoding="utf-8",
        )
        return BrowserArtifact(
            artifact_type="shadow_screenshot_placeholder",
            path=str(proof_path),
            description="Text placeholder for screenshot proof in shadow mode.",
            redacted=False,
            metadata={"live_browser": False},
        )

    def close(self) -> None:
        self._state = {}

    def summarize_run(self, result: BrowserRunResult) -> str:
        return (
            f"{result.provider.value} run {result.run_id} ended with status {result.status}; "
            "no real profile, credentials, cookies, or canonical writeback used."
        )
