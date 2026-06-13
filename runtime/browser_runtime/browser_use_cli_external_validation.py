"""Bounded external Browser Use CLI validation.

This module validates that an operator-provided Browser Use CLI executable is
callable through a help-surface probe. It does not run browser commands, launch
a browser, use profiles, read credentials/cookies, call providers, start
tunnels, activate skills, enqueue Agent Bus work, mutate Gate, or write
canonical ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_use_cli_validation import (
    build_browser_use_cli_validation_status,
)
from runtime.browser_runtime.env_config import browser_use_cli_executable_from_env
from runtime.studio.external_runtime_branch_gate import (
    BRANCH_BROWSER_USE,
    STATUS_READY as BRANCH_GATE_READY,
    build_studio_external_runtime_branch_gate,
)
from runtime.studio.external_runtime_readiness import build_studio_external_runtime_readiness


RECORD_TYPE = "browser_use_cli_external_validation"
SCHEMA_VERSION = "browser.browser_use_cli_external_validation.v1"
STATUS_BLOCKED_PREFLIGHT = "blocked_browser_use_cli_external_validation_preflight_not_ready"
STATUS_BLOCKED_BRANCH_GATE = "blocked_browser_use_cli_external_validation_branch_gate_not_ready"
STATUS_READY_NO_EXECUTION = "browser_use_cli_external_validation_ready_no_execution"
STATUS_COMPLETE_HELP_PROBE = "browser_use_cli_external_validation_complete_help_probe_no_browser"
STATUS_FAILED_HELP_PROBE = "blocked_browser_use_cli_external_validation_help_probe_failed"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Browser-Runs")
DEFAULT_TIMEOUT_SECONDS = 45
HELP_COMMAND_TOKENS = (
    "install",
    "doctor",
    "open",
    "click",
    "extract",
    "cookies",
    "tunnel",
    "profile",
)

FORBIDDEN_EFFECTS = (
    "dependency_install",
    "browser_command_execution",
    "browser_launch",
    "browser_use_cli_browser_action",
    "real_profile_access",
    "credential_or_cookie_read",
    "cookie_export",
    "browser_profile_sync",
    "public_tunnel",
    "cloud_api_call",
    "llm_or_provider_call",
    "trusted_skill_write",
    "skill_activation",
    "agent_bus_enqueue",
    "gate_mutation",
    "canonical_writeback",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _browser_use_executable(executable: str | None = None, *, from_env: bool = False) -> str:
    configured = (executable or "").strip()
    if configured:
        return configured
    if from_env:
        return browser_use_cli_executable_from_env()[0]
    return "browser-use"


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    raise TypeError("status object must be a dict or expose to_dict()")


def _excerpt(text: str, *, limit: int = 1200) -> str:
    clean = text.replace("\r\n", "\n").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_help_probe(executable: str, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [executable, "--help"],
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "attempted": True,
            "timed_out": True,
            "exit_code": None,
            "stdout_excerpt": _excerpt(exc.stdout or ""),
            "stderr_excerpt": _excerpt(exc.stderr or ""),
            "expected_help_surface_present": False,
            "observed_command_tokens": [],
        }
    except OSError as exc:
        return {
            "attempted": True,
            "timed_out": False,
            "exit_code": None,
            "stdout_excerpt": "",
            "stderr_excerpt": str(exc),
            "expected_help_surface_present": False,
            "observed_command_tokens": [],
        }

    stdout = completed.stdout or ""
    combined = f"{stdout}\n{completed.stderr or ''}"
    observed = tuple(token for token in HELP_COMMAND_TOKENS if token in combined)
    return {
        "attempted": True,
        "timed_out": False,
        "exit_code": completed.returncode,
        "stdout_excerpt": _excerpt(stdout),
        "stderr_excerpt": _excerpt(completed.stderr or ""),
        "expected_help_surface_present": (
            completed.returncode == 0
            and "Browser automation CLI" in combined
            and "open" in observed
            and "cookies" in observed
        ),
        "observed_command_tokens": list(observed),
    }


def _markdown(report: "BrowserUseCLIExternalValidation") -> str:
    payload = report.to_dict()
    lines = [
        "# Browser Use CLI External Validation",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Executable: {payload['executable']}",
        f"- Executable path: {payload.get('executable_path') or ''}",
        f"- Help probe attempted: {payload['help_probe_attempted']}",
        f"- Help probe exit code: {payload.get('help_probe_exit_code')}",
        f"- Next allowed step: {payload['next_allowed_step']}",
        "",
        "## Blockers",
    ]
    for blocker in payload["blockers"]:
        lines.append(f"- {blocker}")
    if not payload["blockers"]:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Boundaries",
            "- Help probe only; no Browser Use browser command execution.",
            "- No dependency install, browser launch, real profile, credential/cookie access, public tunnel, cloud API call, provider call, skill activation, Agent Bus write, Gate mutation, or canonical writeback.",
            "",
        ]
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class BrowserUseCLIExternalValidation:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    vault_root: str
    executable: str
    executable_path: str | None
    preflight: dict[str, Any]
    branch_gate: dict[str, Any]
    help_probe_attempted: bool
    help_probe_timed_out: bool
    help_probe_exit_code: int | None
    help_probe_stdout_excerpt: str
    help_probe_stderr_excerpt: str
    expected_help_surface_present: bool
    observed_command_tokens: tuple[str, ...]
    blockers: tuple[str, ...]
    next_allowed_step: str
    read_only: bool = True
    writes_evidence: bool = False
    subprocess_probe_attempted: bool = False
    dependency_install_attempted: bool = False
    browser_command_execution_attempted: bool = False
    browser_launch_attempted: bool = False
    browser_use_cli_browser_action_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    public_tunnel_attempted: bool = False
    cloud_api_call_attempted: bool = False
    llm_or_provider_call_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    forbidden_effects: tuple[str, ...] = FORBIDDEN_EFFECTS

    def validate(self) -> None:
        if self.record_type != RECORD_TYPE:
            raise ValueError("invalid Browser Use CLI external validation record type")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("invalid Browser Use CLI external validation schema version")
        if self.status not in {
            STATUS_BLOCKED_PREFLIGHT,
            STATUS_BLOCKED_BRANCH_GATE,
            STATUS_READY_NO_EXECUTION,
            STATUS_COMPLETE_HELP_PROBE,
            STATUS_FAILED_HELP_PROBE,
        }:
            raise ValueError("invalid Browser Use CLI external validation status")
        if not self.read_only:
            raise ValueError("Browser Use CLI external validation must remain read-only")
        if self.status.startswith("blocked_") and not self.blockers:
            raise ValueError("blocked Browser Use CLI external validation requires blockers")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.browser_command_execution_attempted,
            self.browser_launch_attempted,
            self.browser_use_cli_browser_action_attempted,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.cookie_export_attempted,
            self.browser_profile_sync_attempted,
            self.public_tunnel_attempted,
            self.cloud_api_call_attempted,
            self.llm_or_provider_call_attempted,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.agent_bus_enqueue_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Browser Use CLI external validation attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["observed_command_tokens"] = list(self.observed_command_tokens)
        payload["blockers"] = list(self.blockers)
        payload["forbidden_effects"] = list(self.forbidden_effects)
        return payload


def build_browser_use_cli_external_validation(
    vault_root: str | Path,
    *,
    executable: str | None = None,
    from_env: bool = False,
    execute_help_probe: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    generated_at: str | None = None,
) -> BrowserUseCLIExternalValidation:
    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    selected_executable = _browser_use_executable(executable, from_env=from_env)
    preflight = build_browser_use_cli_validation_status(
        vault,
        executable=selected_executable,
        generated_at=timestamp,
    ).to_dict()
    readiness = build_studio_external_runtime_readiness(
        vault,
        generated_at=timestamp,
        browser_use_executable=selected_executable,
    )
    branch_gate = build_studio_external_runtime_branch_gate(
        vault,
        branch=BRANCH_BROWSER_USE,
        generated_at=timestamp,
        readiness=readiness,
    ).to_dict()

    blockers: list[str] = []
    help_probe = {
        "attempted": False,
        "timed_out": False,
        "exit_code": None,
        "stdout_excerpt": "",
        "stderr_excerpt": "",
        "expected_help_surface_present": False,
        "observed_command_tokens": [],
    }
    if not preflight.get("ready_for_future_live_validation"):
        blockers.extend(f"preflight:{blocker}" for blocker in preflight.get("blockers", ()))
        status = STATUS_BLOCKED_PREFLIGHT
        next_allowed_step = "restore-browser-use-cli-preflight-readiness"
    elif branch_gate.get("status") != BRANCH_GATE_READY or not branch_gate.get("can_start_branch"):
        blockers.extend(f"branch_gate:{blocker}" for blocker in branch_gate.get("blockers", ()))
        status = STATUS_BLOCKED_BRANCH_GATE
        next_allowed_step = "rerun-studio-external-runtime-branch-gate"
    elif not execute_help_probe:
        status = STATUS_READY_NO_EXECUTION
        blockers.append("browser_use_cli_external_help_probe_not_run")
        next_allowed_step = "rerun-with---execute-help-probe"
    else:
        executable_path = preflight.get("executable_path") or selected_executable
        help_probe = _run_help_probe(str(executable_path), timeout_seconds)
        if help_probe["expected_help_surface_present"]:
            status = STATUS_COMPLETE_HELP_PROBE
            next_allowed_step = "browser-use-cli-no-account-safe-url-validation-design"
        else:
            status = STATUS_FAILED_HELP_PROBE
            blockers.append("browser_use_cli_help_probe_failed")
            if help_probe["timed_out"]:
                blockers.append("browser_use_cli_help_probe_timed_out")
            elif help_probe["exit_code"] not in (0, None):
                blockers.append(f"browser_use_cli_help_probe_exit_code:{help_probe['exit_code']}")
            next_allowed_step = "inspect-browser-use-cli-install"

    report = BrowserUseCLIExternalValidation(
        record_type=RECORD_TYPE,
        schema_version=SCHEMA_VERSION,
        generated_at=timestamp,
        status=status,
        vault_root=str(vault),
        executable=selected_executable,
        executable_path=preflight.get("executable_path"),
        preflight=preflight,
        branch_gate=branch_gate,
        help_probe_attempted=bool(help_probe["attempted"]),
        help_probe_timed_out=bool(help_probe["timed_out"]),
        help_probe_exit_code=help_probe["exit_code"],
        help_probe_stdout_excerpt=str(help_probe["stdout_excerpt"]),
        help_probe_stderr_excerpt=str(help_probe["stderr_excerpt"]),
        expected_help_surface_present=bool(help_probe["expected_help_surface_present"]),
        observed_command_tokens=tuple(help_probe["observed_command_tokens"]),
        blockers=tuple(blockers),
        next_allowed_step=next_allowed_step,
        subprocess_probe_attempted=bool(help_probe["attempted"]),
    )
    report.validate()
    return report


def write_browser_use_cli_external_validation_evidence(
    vault_root: str | Path,
    report: BrowserUseCLIExternalValidation,
    *,
    run_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT
    if root.is_absolute():
        raise ValueError("evidence root must be vault-relative")
    slug = run_slug or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-browser-use-cli-external-validation"
    )
    base = vault / root / slug
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    _write_json(json_path, report.to_dict())
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown(report), encoding="utf-8")
    return {
        "written": True,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run bounded external Browser Use CLI validation without browser automation."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--executable", default="", metavar="PATH_OR_NAME")
    parser.add_argument("--from-env", action="store_true")
    parser.add_argument("--execute-help-probe", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--run-slug", default=None, metavar="SLUG")
    parser.add_argument(
        "--evidence-root",
        default=None,
        metavar="PATH",
        help="Vault-relative evidence root; defaults to 07_LOGS/Browser-Runs",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report = build_browser_use_cli_external_validation(
        args.vault_root,
        executable=args.executable,
        from_env=args.from_env,
        execute_help_probe=args.execute_help_probe,
        timeout_seconds=args.timeout_seconds,
    )
    payload = report.to_dict()
    if args.write_evidence:
        payload["evidence_write"] = write_browser_use_cli_external_validation_evidence(
            args.vault_root,
            report,
            run_slug=args.run_slug,
            evidence_root=args.evidence_root,
        )
        payload["writes_evidence"] = True
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"executable_path: {payload.get('executable_path')}")
        print(f"help_probe_attempted: {payload['help_probe_attempted']}")
        print(f"next_allowed_step: {payload['next_allowed_step']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
    return 0 if report.status in {STATUS_READY_NO_EXECUTION, STATUS_COMPLETE_HELP_PROBE} else 1


if __name__ == "__main__":
    raise SystemExit(main())
