"""No-execution CDP adapter design preflight for ChaseOS browser runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse


LOCAL_CDP_HOSTS = {"127.0.0.1", "localhost", "::1"}
FORBIDDEN_CDP_ACTIONS = {
    "raw_cdp",
    "runtime.evaluate",
    "network.getallcookies",
    "network.getcookies",
    "storage.getstoragekeyforframe",
    "storage.getcookies",
    "browser.grantpermissions",
    "browser.setdownloadbehavior",
    "page.setdownloadbehavior",
    "dom.setattributevalue",
    "input.inserttext",
    "input.dispatchkeyevent",
    "filechooser.setfiles",
}
SAFE_DESIGN_ACTIONS = {
    "page.navigate",
    "page.capture_screenshot",
    "dom.snapshot",
    "page.read_title",
    "page.read_url",
    "page.read_visible_text",
    "wait_for",
}


@dataclass(frozen=True)
class CDPAdapterDesignRequest:
    """A proposed future CDP adapter configuration.

    This request is intentionally not executable. It exists so ChaseOS can
    review CDP authority before a live adapter is ever implemented.
    """

    cdp_endpoint: str
    target_url: str
    allowed_domains: list[str]
    mode: str = "shadow"
    launch_strategy: str = "chaseos_launch_isolated"
    allowed_actions: list[str] = field(default_factory=lambda: sorted(SAFE_DESIGN_ACTIONS))
    use_existing_profile: bool = False
    allow_credentials: bool = False
    allow_cookie_access: bool = False
    expose_raw_cdp: bool = False
    allow_runtime_evaluate: bool = False
    allow_public_endpoint: bool = False
    allow_canonical_writeback: bool = False
    allow_trusted_skill_write: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_cdp_adapter_design(request: CDPAdapterDesignRequest) -> dict[str, Any]:
    """Return a fail-closed review packet for a future CDP adapter.

    The function never opens a socket, never launches a browser, never reads a
    profile, and never writes artifacts. A blocker-free packet only means the
    proposed configuration is reviewable as a future design.
    """
    blockers: list[dict[str, Any]] = []
    warnings: list[str] = []

    endpoint = urlparse(request.cdp_endpoint)
    endpoint_host = endpoint.hostname or ""
    if endpoint.scheme not in {"http", "https", "ws", "wss"}:
        blockers.append(_blocker("unsupported_cdp_endpoint_scheme", request.cdp_endpoint))
    if endpoint_host not in LOCAL_CDP_HOSTS and not request.allow_public_endpoint:
        blockers.append(_blocker("cdp_endpoint_not_local", endpoint_host or "<missing>"))
    if request.allow_public_endpoint:
        blockers.append(_blocker("public_cdp_endpoint_forbidden", request.cdp_endpoint))

    target = urlparse(request.target_url)
    if target.scheme not in {"http", "https", "file"}:
        blockers.append(_blocker("unsupported_target_url_scheme", target.scheme or "<missing>"))
    target_domain = target.hostname or ""
    allowed = {domain.lower() for domain in request.allowed_domains}
    if target.scheme != "file" and target_domain.lower() not in allowed:
        blockers.append(_blocker("target_domain_not_allowlisted", target_domain or "<missing>"))

    if request.mode not in {"shadow", "read_only"}:
        blockers.append(_blocker("unsupported_mode", request.mode))
    if request.launch_strategy != "chaseos_launch_isolated":
        blockers.append(_blocker("launch_strategy_not_isolated", request.launch_strategy))
    if request.use_existing_profile:
        blockers.append(_blocker("existing_profile_forbidden", "use_existing_profile=true"))
    if request.allow_credentials:
        blockers.append(_blocker("credentials_forbidden", "allow_credentials=true"))
    if request.allow_cookie_access:
        blockers.append(_blocker("cookie_access_forbidden", "allow_cookie_access=true"))
    if request.expose_raw_cdp:
        blockers.append(_blocker("raw_cdp_exposure_forbidden", "expose_raw_cdp=true"))
    if request.allow_runtime_evaluate:
        blockers.append(_blocker("runtime_evaluate_forbidden", "allow_runtime_evaluate=true"))
    if request.allow_canonical_writeback:
        blockers.append(_blocker("canonical_writeback_forbidden", "allow_canonical_writeback=true"))
    if request.allow_trusted_skill_write:
        blockers.append(_blocker("trusted_skill_write_forbidden", "allow_trusted_skill_write=true"))

    normalized_actions = [action.strip().lower() for action in request.allowed_actions if action.strip()]
    forbidden_actions = sorted({action for action in normalized_actions if action in FORBIDDEN_CDP_ACTIONS})
    if forbidden_actions:
        blockers.append(_blocker("forbidden_cdp_actions_requested", forbidden_actions))
    unknown_actions = sorted({action for action in normalized_actions if action not in SAFE_DESIGN_ACTIONS})
    if unknown_actions:
        warnings.append(f"unknown actions require future review: {', '.join(unknown_actions)}")

    status = "blocked_cdp_adapter_design_policy" if blockers else "cdp_adapter_design_preflight_ready_no_execution"
    return {
        "ok": not blockers,
        "status": status,
        "request": request.as_dict(),
        "blockers": blockers,
        "warnings": warnings,
        "safe_design_actions": sorted(SAFE_DESIGN_ACTIONS),
        "forbidden_cdp_actions": sorted(FORBIDDEN_CDP_ACTIONS),
        "adapter_implemented": False,
        "execution_allowed": False,
        "browser_launch_allowed": False,
        "cdp_connection_attempted": False,
        "raw_cdp_exposed": False,
        "existing_profile_allowed": False,
        "credentials_allowed": False,
        "cookie_access_allowed": False,
        "trusted_skill_write_allowed": False,
        "canonical_writeback_allowed": False,
        "boundary": (
            "CDP adapter design preflight only; no socket connection, browser launch, "
            "profile access, cookie/session access, raw CDP exposure, trusted skill "
            "write, activation, or canonical writeback is performed"
        ),
    }


def _blocker(blocker_id: str, detail: Any) -> dict[str, Any]:
    return {"blocker_id": blocker_id, "detail": detail, "blocks_execution": True}
