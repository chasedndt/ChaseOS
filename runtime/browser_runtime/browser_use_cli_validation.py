"""Read-only Browser Use CLI validation preflight.

This module checks whether ChaseOS is ready for a future Browser Use CLI live
validation. It does not install dependencies, invoke browser-use, launch a
browser, read profiles, inspect credentials, write artifacts, or promote skills.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BROWSER_USE_CLI_VALIDATION_BLOCKED_EFFECTS = (
    "dependency_install",
    "subprocess_probe",
    "browser_launch",
    "browser_use_cli_live_run",
    "real_profile_access",
    "credential_or_cookie_read",
    "cookie_export",
    "browser_profile_sync",
    "public_tunnel",
    "trusted_skill_write",
    "skill_activation",
    "agent_bus_enqueue",
    "provider_call",
    "gate_mutation",
    "canonical_writeback",
)

BROWSER_USE_CLI_VALIDATION_STATUSES = {
    "blocked_browser_use_cli_unavailable",
    "blocked_wrapper_missing",
    "blocked_policy_not_throwaway_only",
    "ready_for_operator_authorized_live_validation_no_execution",
}

CONFIG_POLICY_REQUIREMENTS = {
    "browser_profile_policy": "throwaway_only",
    "allow_real_profile": "false",
    "allow_credentials": "false",
    "allow_shell_execution": "false",
    "allow_cookie_export": "false",
    "allow_browser_profile_sync": "false",
    "allow_public_tunnel": "false",
    "canonical_writeback": "false",
    "automatic_skill_activation": "false",
    "skill_generation": "draft_only",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _read_scalar_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value:
            values[key.strip()] = value.strip("'\"").lower()
    return values


@dataclass(frozen=True)
class BrowserUseCLIConfigFinding:
    key: str
    expected: str
    observed: str | None
    ok: bool

    def validate(self) -> None:
        if not self.key:
            raise ValueError("config finding key is required")
        if not self.expected:
            raise ValueError("config finding expected value is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "key": self.key,
            "expected": self.expected,
            "observed": self.observed,
            "ok": self.ok,
        }


@dataclass(frozen=True)
class BrowserUseCLIValidationStatus:
    generated_at: str
    status: str
    executable: str
    executable_found: bool
    executable_path: str | None
    wrapper_present: bool
    config_present: bool
    config_policy_ok: bool
    config_findings: tuple[BrowserUseCLIConfigFinding, ...]
    ready_for_future_live_validation: bool
    blockers: tuple[str, ...]
    next_allowed_step: str
    read_only: bool = True
    dependency_install_attempted: bool = False
    subprocess_probe_attempted: bool = False
    browser_launch_attempted: bool = False
    browser_use_cli_live_run_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    public_tunnel_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    blocked_effects: tuple[str, ...] = BROWSER_USE_CLI_VALIDATION_BLOCKED_EFFECTS

    def validate(self) -> None:
        if self.status not in BROWSER_USE_CLI_VALIDATION_STATUSES:
            raise ValueError("invalid Browser Use CLI validation status")
        if not self.executable:
            raise ValueError("executable is required")
        if not self.next_allowed_step:
            raise ValueError("next allowed step is required")
        for finding in self.config_findings:
            finding.validate()
        forbidden_flags = (
            self.dependency_install_attempted,
            self.subprocess_probe_attempted,
            self.browser_launch_attempted,
            self.browser_use_cli_live_run_attempted,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.cookie_export_attempted,
            self.browser_profile_sync_attempted,
            self.public_tunnel_attempted,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Browser Use CLI validation preflight attempted a forbidden effect")
        if not self.read_only:
            raise ValueError("Browser Use CLI validation preflight must be read-only")
        if not self.blocked_effects:
            raise ValueError("blocked effects must be declared")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "status": self.status,
            "executable": self.executable,
            "executable_found": self.executable_found,
            "executable_path": self.executable_path,
            "wrapper_present": self.wrapper_present,
            "config_present": self.config_present,
            "config_policy_ok": self.config_policy_ok,
            "config_findings": [finding.to_dict() for finding in self.config_findings],
            "ready_for_future_live_validation": self.ready_for_future_live_validation,
            "blockers": list(self.blockers),
            "next_allowed_step": self.next_allowed_step,
            "read_only": self.read_only,
            "dependency_install_attempted": self.dependency_install_attempted,
            "subprocess_probe_attempted": self.subprocess_probe_attempted,
            "browser_launch_attempted": self.browser_launch_attempted,
            "browser_use_cli_live_run_attempted": self.browser_use_cli_live_run_attempted,
            "real_profile_access_attempted": self.real_profile_access_attempted,
            "credential_or_cookie_read_attempted": self.credential_or_cookie_read_attempted,
            "cookie_export_attempted": self.cookie_export_attempted,
            "browser_profile_sync_attempted": self.browser_profile_sync_attempted,
            "public_tunnel_attempted": self.public_tunnel_attempted,
            "trusted_skill_write_attempted": self.trusted_skill_write_attempted,
            "skill_activation_attempted": self.skill_activation_attempted,
            "agent_bus_enqueue_attempted": self.agent_bus_enqueue_attempted,
            "provider_call_attempted": self.provider_call_attempted,
            "gate_mutation_attempted": self.gate_mutation_attempted,
            "canonical_writeback_attempted": self.canonical_writeback_attempted,
            "blocked_effects": list(self.blocked_effects),
        }


def _build_config_findings(config_values: dict[str, str]) -> tuple[BrowserUseCLIConfigFinding, ...]:
    findings: list[BrowserUseCLIConfigFinding] = []
    for key, expected in CONFIG_POLICY_REQUIREMENTS.items():
        observed = config_values.get(key)
        findings.append(
            BrowserUseCLIConfigFinding(
                key=key,
                expected=expected,
                observed=observed,
                ok=observed == expected,
            )
        )
    return tuple(findings)


def build_browser_use_cli_validation_status(
    vault_root: str | Path,
    *,
    executable: str = "browser-use",
    generated_at: str | None = None,
) -> BrowserUseCLIValidationStatus:
    """Build a read-only validation preflight for the browser-use CLI wrapper."""
    vault = _vault_path(vault_root)
    wrapper_present = (vault / "runtime/browser_runtime/adapters/browser_use_cli.py").is_file()
    config_path = vault / "runtime/browser_runtime/config.yaml"
    config_present = config_path.is_file()
    config_findings = _build_config_findings(_read_scalar_config(config_path))
    config_policy_ok = config_present and all(finding.ok for finding in config_findings)
    executable_path = shutil.which(executable)
    executable_found = executable_path is not None

    blockers: list[str] = []
    if not wrapper_present:
        blockers.append("browser_use_cli_wrapper_missing")
    if not config_present:
        blockers.append("browser_runtime_config_missing")
    if config_present and not config_policy_ok:
        blockers.append("browser_runtime_policy_not_throwaway_only")
    if not executable_found:
        blockers.append("browser_use_cli_executable_not_found")

    if not wrapper_present:
        status = "blocked_wrapper_missing"
        next_allowed_step = "Restore the fail-closed Browser Use CLI adapter wrapper before any live validation."
    elif not config_policy_ok:
        status = "blocked_policy_not_throwaway_only"
        next_allowed_step = "Restore throwaway-only browser runtime policy before any live validation."
    elif not executable_found:
        status = "blocked_browser_use_cli_unavailable"
        next_allowed_step = (
            "Install browser-use outside ChaseOS and rerun this preflight; ChaseOS does not install it automatically."
        )
    else:
        status = "ready_for_operator_authorized_live_validation_no_execution"
        blockers.append("browser_use_cli_live_validation_not_run")
        next_allowed_step = (
            "Run a separate operator-approved no-account Browser Use CLI validation against an allowed safe URL."
        )

    ready = status == "ready_for_operator_authorized_live_validation_no_execution"
    result = BrowserUseCLIValidationStatus(
        generated_at=generated_at or _now_utc(),
        status=status,
        executable=executable,
        executable_found=executable_found,
        executable_path=executable_path,
        wrapper_present=wrapper_present,
        config_present=config_present,
        config_policy_ok=config_policy_ok,
        config_findings=config_findings,
        ready_for_future_live_validation=ready,
        blockers=tuple(blockers),
        next_allowed_step=next_allowed_step,
    )
    result.validate()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a read-only Browser Use CLI validation preflight.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--executable", default="browser-use", help="Browser Use CLI executable name.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    status = build_browser_use_cli_validation_status(args.vault_root, executable=args.executable)
    payload = status.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"executable_found: {payload['executable_found']}")
        print(f"ready_for_future_live_validation: {payload['ready_for_future_live_validation']}")
        print("blockers:")
        for blocker in payload["blockers"]:
            print(f"- {blocker}")
        print(f"next_allowed_step: {payload['next_allowed_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
