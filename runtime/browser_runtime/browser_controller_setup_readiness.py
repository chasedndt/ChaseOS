"""Read-only browser controller setup readiness for Browser Runtime replay proof.

This module does not launch a browser. It only checks whether ChaseOS can find a
Chromium-compatible executable for the throwaway-profile CDP controller and
returns operator handoff instructions for the next live replay proof.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


READINESS_VERSION = "browser.controller_setup_readiness.v1"
ENV_VAR_NAME = "CHASEOS_BROWSER_CDP_EXECUTABLE"
KNOWN_BROWSER_COMMANDS = (
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "chrome",
    "msedge",
    "microsoft-edge",
)
WINDOWS_BROWSER_PATHS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
)
SAFE_REPLAY_COMMAND = (
    "python -m runtime.browser_runtime.workflow_replay_execution_proof "
    "--vault-root . "
    "--workflow-id wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502 "
    "--target-url http://127.0.0.1:8770/ "
    "--allowed-domain 127.0.0.1 "
    "--execute-local-replay "
    "--run-slug safe-local-workflow-replay-execution-proof-20260503 "
    "--json"
)


@dataclass(frozen=True)
class BrowserExecutableCandidate:
    source: str
    label: str
    candidate: str
    resolved_path: str
    exists: bool
    usable: bool
    reason: str


@dataclass(frozen=True)
class BrowserControllerSetupReadiness:
    record_type: str
    version: str
    generated_at: str
    status: str
    env_var_name: str
    env_var_value_present: bool
    selected_executable: str
    selected_source: str
    blockers: list[str]
    candidates: list[BrowserExecutableCandidate]
    operator_handoff: dict[str, str]
    browser_launch_attempted: bool
    cdp_connection_attempted: bool
    real_profile_access_attempted: bool
    credential_or_cookie_read_attempted: bool
    browser_profile_sync_attempted: bool
    browser_use_cli_invoked: bool
    browser_harness_used: bool
    gate_mutation_attempted: bool
    canonical_writeback_attempted: bool
    next_step: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["candidates"] = [asdict(candidate) for candidate in self.candidates]
        return payload


def evaluate_browser_controller_setup_readiness(
    *,
    env: dict[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
    known_paths: Iterable[str] | None = None,
    generated_at: str | None = None,
) -> BrowserControllerSetupReadiness:
    env_map = dict(os.environ if env is None else env)
    candidates: list[BrowserExecutableCandidate] = []

    env_value = env_map.get(ENV_VAR_NAME, "").strip()
    if env_value:
        candidates.append(_candidate_from_env(env_value, which=which))

    for command in KNOWN_BROWSER_COMMANDS:
        resolved = which(command)
        candidates.append(
            BrowserExecutableCandidate(
                source="path",
                label=command,
                candidate=command,
                resolved_path=resolved or "",
                exists=bool(resolved),
                usable=bool(resolved),
                reason="found_on_path" if resolved else "not_found_on_path",
            )
        )

    for path_text in known_paths if known_paths is not None else _default_known_paths(env_map):
        path = Path(path_text)
        exists = path.is_file()
        candidates.append(
            BrowserExecutableCandidate(
                source="well_known_path",
                label=path.name or path_text,
                candidate=path_text,
                resolved_path=str(path) if exists else "",
                exists=exists,
                usable=exists,
                reason="file_exists" if exists else "file_not_found",
            )
        )

    selected = next((candidate for candidate in candidates if candidate.usable), None)
    blockers: list[str] = []
    if selected is None:
        blockers.append("chromium_compatible_executable_not_found")

    return BrowserControllerSetupReadiness(
        record_type="browser_controller_setup_readiness",
        version=READINESS_VERSION,
        generated_at=generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        status="browser_controller_setup_ready_no_launch" if selected else "blocked_browser_controller_setup",
        env_var_name=ENV_VAR_NAME,
        env_var_value_present=bool(env_value),
        selected_executable=selected.resolved_path if selected else "",
        selected_source=selected.source if selected else "",
        blockers=blockers,
        candidates=candidates,
        operator_handoff=_operator_handoff(selected.resolved_path if selected else ""),
        browser_launch_attempted=False,
        cdp_connection_attempted=False,
        real_profile_access_attempted=False,
        credential_or_cookie_read_attempted=False,
        browser_profile_sync_attempted=False,
        browser_use_cli_invoked=False,
        browser_harness_used=False,
        gate_mutation_attempted=False,
        canonical_writeback_attempted=False,
        next_step=(
            "rerun_safe_local_workflow_replay_execution_proof"
            if selected
            else "install_or_locate_chromium_and_set_chaseos_browser_cdp_executable"
        ),
    )


def resolve_browser_executable() -> str:
    """Return the first usable Chromium-compatible executable without launching it."""

    result = evaluate_browser_controller_setup_readiness()
    return result.selected_executable


def _candidate_from_env(value: str, *, which: Callable[[str], str | None]) -> BrowserExecutableCandidate:
    path_like = any(sep in value for sep in ("\\", "/")) or value.lower().endswith(".exe")
    if path_like:
        path = Path(value)
        exists = path.is_file()
        return BrowserExecutableCandidate(
            source="env",
            label=ENV_VAR_NAME,
            candidate=value,
            resolved_path=str(path) if exists else "",
            exists=exists,
            usable=exists,
            reason="env_path_exists" if exists else "env_path_not_found",
        )
    resolved = which(value)
    return BrowserExecutableCandidate(
        source="env",
        label=ENV_VAR_NAME,
        candidate=value,
        resolved_path=resolved or "",
        exists=bool(resolved),
        usable=bool(resolved),
        reason="env_command_found_on_path" if resolved else "env_command_not_found_on_path",
    )


def _default_known_paths(env: dict[str, str]) -> list[str]:
    paths = list(WINDOWS_BROWSER_PATHS)
    local_appdata = env.get("LOCALAPPDATA", "").strip()
    if local_appdata:
        paths.append(str(Path(local_appdata) / "Google" / "Chrome" / "Application" / "chrome.exe"))
        paths.append(str(Path(local_appdata) / "Microsoft" / "Edge" / "Application" / "msedge.exe"))
    return paths


def _operator_handoff(selected_executable: str) -> dict[str, str]:
    executable_hint = selected_executable or r"C:\Path\To\chrome.exe"
    return {
        "purpose": "Configure a Chromium-compatible executable for ChaseOS throwaway-profile CDP proof only.",
        "session_env_powershell": f"$env:{ENV_VAR_NAME}='{executable_hint}'",
        "verify_command": "python -m runtime.browser_runtime.browser_controller_setup_readiness --json",
        "safe_replay_command": SAFE_REPLAY_COMMAND,
        "profile_policy": "throwaway_only; do not use a real Chrome profile or saved credentials.",
        "forbidden": "No real profile, cookies, credentials, profile sync, Browser Harness authority, or canonical writeback.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only browser controller setup readiness.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args(argv)
    result = evaluate_browser_controller_setup_readiness()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"status: {result.status}")
        if result.selected_executable:
            print(f"selected_executable: {result.selected_executable}")
        for blocker in result.blockers:
            print(f"blocker: {blocker}")
        print(f"next_step: {result.next_step}")
    return 0 if not result.blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
