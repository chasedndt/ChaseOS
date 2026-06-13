"""Browser Use CLI safe-URL validation design.

Produces a read-only design contract describing the bounded parameters under
which a safe-URL validation run may proceed. No browser is launched, no
dependencies are installed, no provider calls are made, and no canonical
ChaseOS state is written.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


RECORD_TYPE = "browser_use_cli_safe_url_validation_design"
SCHEMA_VERSION = "browser.browser_use_cli_safe_url_validation_design.v1"
STATUS_READY = "browser_use_cli_safe_url_validation_design_ready_no_execution"
STATUS_BLOCKED = "browser_use_cli_safe_url_validation_design_blocked"

DEFAULT_TARGET_HOST = "127.0.0.1"
DEFAULT_TARGET_PORT = 8770
DEFAULT_TARGET_URL = f"http://{DEFAULT_TARGET_HOST}:{DEFAULT_TARGET_PORT}/"
DEFAULT_SESSION_NAME = "chaseos-safe-url-validation"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Browser-Runs")
ALLOWED_BROWSER_USE_SUBCOMMAND = "open"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
FORBIDDEN_BROWSER_USE_SUBCOMMANDS = (
    "install",
    "tunnel",
    "cookies",
    "doctor",
    "profile",
)
FORBIDDEN_EFFECTS = (
    "dependency_install_command",
    "browser_command_execution",
    "browser_launch",
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

_SAFE_HELP_PROBE_STATUS = "browser_use_cli_external_validation_complete_help_probe_no_browser"
_FORBIDDEN_PROBE_FLAGS = (
    "browser_command_execution_attempted",
    "browser_launch_attempted",
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "public_tunnel_attempted",
    "canonical_writeback_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _is_loopback_http(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "http" and parsed.hostname in LOOPBACK_HOSTS


def _read_help_probe_evidence(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _help_probe_is_safe(evidence: dict[str, Any]) -> bool:
    if evidence.get("status") != _SAFE_HELP_PROBE_STATUS:
        return False
    if not evidence.get("expected_help_surface_present"):
        return False
    if any(evidence.get(flag) for flag in _FORBIDDEN_PROBE_FLAGS):
        return False
    return True


def _future_command_argv(executable: str, target_url: str, session_name: str) -> list[str]:
    return [
        executable,
        "--json",
        "--session",
        session_name,
        ALLOWED_BROWSER_USE_SUBCOMMAND,
        target_url,
    ]


def _markdown(report: "BrowserUseCLISafeURLValidationDesign") -> str:
    payload = report.to_dict()
    lines = [
        "# Browser Use CLI Safe-URL Validation Design",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Target URL: {payload['target_url']}",
        f"- Allowed subcommand: {payload['allowed_subcommand']}",
        f"- Browser package download complete: {payload['browser_use_package_download_complete']}",
        f"- Future command: {' '.join(payload['future_command_argv'])}",
        "",
        "## Blockers",
    ]
    if payload["blockers"]:
        lines.extend(f"- {b}" for b in payload["blockers"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Boundary",
            "- Read-only design contract. No browser launched, no install run, no provider call, no canonical writeback.",
            "",
        ]
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class BrowserUseCLISafeURLValidationDesign:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    vault_root: str
    target_url: str
    browser_use_executable_path: str
    allowed_subcommand: str
    forbidden_subcommands: tuple[str, ...]
    future_command_argv: tuple[str, ...]
    future_command_preview: str
    browser_use_package_download_complete: bool
    browser_dependency_download_verified: bool
    browser_dependency_install_command_run: bool
    blockers: tuple[str, ...]
    next_recommended_pass: str
    read_only: bool = True
    browser_dependency_download_attempted: bool = False
    browser_command_execution_attempted: bool = False
    browser_launch_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    public_tunnel_attempted: bool = False
    canonical_writeback_attempted: bool = False
    forbidden_effects: tuple[str, ...] = FORBIDDEN_EFFECTS

    def validate(self) -> None:
        if self.record_type != RECORD_TYPE:
            raise ValueError("invalid design record type")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("invalid design schema version")
        if self.status not in {STATUS_READY, STATUS_BLOCKED}:
            raise ValueError("invalid design status")
        if not self.read_only:
            raise ValueError("design must be read-only")
        if "--profile" in self.future_command_argv:
            raise ValueError("future command must not include --profile")
        forbidden_flags = (
            self.browser_command_execution_attempted,
            self.browser_launch_attempted,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.public_tunnel_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("design attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["future_command_argv"] = list(self.future_command_argv)
        payload["forbidden_subcommands"] = list(self.forbidden_subcommands)
        payload["blockers"] = list(self.blockers)
        payload["forbidden_effects"] = list(self.forbidden_effects)
        return payload


def build_browser_use_cli_safe_url_validation_design(
    vault_root: str | Path,
    *,
    target_url: str | None = None,
    help_probe_evidence: str | Path | None = None,
    generated_at: str | None = None,
) -> BrowserUseCLISafeURLValidationDesign:
    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    resolved_target = target_url or DEFAULT_TARGET_URL

    blockers: list[str] = []

    if not _is_loopback_http(resolved_target):
        blockers.append("safe_url_target_not_loopback_http")

    probe_evidence: dict[str, Any] = {}
    executable = "browser-use"
    package_complete = False

    if help_probe_evidence is not None:
        probe_path = Path(help_probe_evidence)
        probe_evidence = _read_help_probe_evidence(probe_path)
        if not _help_probe_is_safe(probe_evidence):
            blockers.append("browser_use_cli_external_help_probe_evidence_not_ready")
        else:
            raw_exe = (
                probe_evidence.get("executable_path")
                or probe_evidence.get("executable")
                or "browser-use"
            )
            exe_path = Path(str(raw_exe))
            if exe_path.is_file():
                executable = str(exe_path)
                package_complete = True
            else:
                executable = str(raw_exe)
                package_complete = bool(raw_exe and raw_exe != "browser-use")

    argv = _future_command_argv(executable, resolved_target, DEFAULT_SESSION_NAME)

    if blockers:
        status = STATUS_BLOCKED
        next_pass = "inspect-browser-use-cli-safe-url-validation-design-blockers"
    else:
        status = STATUS_READY
        next_pass = "browser-use-cli-safe-url-validation-run"

    report = BrowserUseCLISafeURLValidationDesign(
        record_type=RECORD_TYPE,
        schema_version=SCHEMA_VERSION,
        generated_at=timestamp,
        status=status,
        vault_root=str(vault),
        target_url=resolved_target,
        browser_use_executable_path=executable,
        allowed_subcommand=ALLOWED_BROWSER_USE_SUBCOMMAND,
        forbidden_subcommands=FORBIDDEN_BROWSER_USE_SUBCOMMANDS,
        future_command_argv=tuple(argv),
        future_command_preview=" ".join(argv),
        browser_use_package_download_complete=package_complete,
        browser_dependency_download_verified=False,
        browser_dependency_install_command_run=False,
        blockers=tuple(blockers),
        next_recommended_pass=next_pass,
    )
    report.validate()
    return report


def write_browser_use_cli_safe_url_validation_design_evidence(
    vault_root: str | Path,
    report: BrowserUseCLISafeURLValidationDesign,
    *,
    run_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT
    if root.is_absolute():
        raise ValueError("evidence root must be vault-relative")
    slug = run_slug or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-browser-use-cli-safe-url-validation-design"
    )
    base = vault / root / slug
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    _write_json(json_path, report.to_dict())
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown(report), encoding="utf-8")
    return {"written": True, "json_path": str(json_path), "markdown_path": str(md_path)}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a read-only Browser Use CLI safe-URL validation design contract."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--target-url", default=None, metavar="URL")
    parser.add_argument("--help-probe-evidence", default=None, metavar="PATH")
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--run-slug", default=None, metavar="SLUG")
    parser.add_argument("--evidence-root", default=None, metavar="PATH")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report = build_browser_use_cli_safe_url_validation_design(
        args.vault_root,
        target_url=args.target_url,
        help_probe_evidence=args.help_probe_evidence,
    )
    payload = report.to_dict()
    if args.write_evidence:
        payload["evidence_write"] = write_browser_use_cli_safe_url_validation_design_evidence(
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
        print(f"target_url: {payload['target_url']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
    return 0 if report.status == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
