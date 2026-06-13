"""Bounded no-account Browser Use CLI safe-URL validation run.

This module may run exactly one Browser Use CLI browser command: ``open`` against
the ChaseOS-owned loopback Studio Product UI test target. It starts the local
target only when needed, kills only a target process it started, and records a
bounded result even when Browser Use lacks browser dependencies.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from runtime.browser_runtime.browser_use_cli_safe_url_validation_design import (
    ALLOWED_BROWSER_USE_SUBCOMMAND,
    DEFAULT_EVIDENCE_ROOT,
    DEFAULT_TARGET_HOST,
    DEFAULT_TARGET_PORT,
    FORBIDDEN_BROWSER_USE_SUBCOMMANDS,
    LOOPBACK_HOSTS,
    STATUS_READY as DESIGN_STATUS_READY,
    build_browser_use_cli_safe_url_validation_design,
)


RECORD_TYPE = "browser_use_cli_safe_url_validation_run"
SCHEMA_VERSION = "browser.browser_use_cli_safe_url_validation_run.v1"
STATUS_COMPLETE = "browser_use_cli_safe_url_validation_run_complete"
STATUS_BLOCKED_DESIGN = "blocked_browser_use_cli_safe_url_validation_run_design_not_ready"
STATUS_BLOCKED_TARGET = "blocked_browser_use_cli_safe_url_validation_run_target_not_ready"
STATUS_FAILED_BROWSER_USE = "blocked_browser_use_cli_safe_url_validation_run_browser_use_failed"
DEFAULT_DESIGN_EVIDENCE = Path(
    "07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-design-20260505.json"
)
DEFAULT_RUN_TIMEOUT_SECONDS = 90
DEFAULT_TARGET_READY_TIMEOUT_SECONDS = 15
DEFAULT_SESSION_NAME = "chaseos-safe-url-validation"
FORBIDDEN_EFFECTS = (
    "dependency_install_command",
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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _excerpt(text: str | bytes | None, *, limit: int = 1600) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        clean = text.decode("utf-8", errors="replace")
    else:
        clean = text
    clean = clean.replace("\r\n", "\n").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _is_loopback_http(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "http" and parsed.hostname in LOOPBACK_HOSTS


def _health_url_for(target_url: str) -> str:
    parsed = urlparse(target_url)
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}/health.json"


def _probe_url_json(url: str, *, timeout_seconds: float = 2.0) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310 - loopback-only caller.
            body = response.read(256_000)
            payload = json.loads(body.decode("utf-8"))
            return {
                "ok": response.status == 200 and bool(payload.get("ok")),
                "status_code": response.status,
                "payload": payload,
                "error": "",
            }
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return {"ok": False, "status_code": None, "payload": {}, "error": str(exc)}


def _wait_for_health(url: str, *, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last = {"ok": False, "status_code": None, "payload": {}, "error": "not probed"}
    while time.monotonic() < deadline:
        last = _probe_url_json(url)
        if last.get("ok"):
            return last
        time.sleep(0.25)
    return last


def _safe_browser_use_argv(executable: str, target_url: str, session_name: str) -> tuple[str, ...]:
    argv = (
        executable,
        "--json",
        "--session",
        session_name,
        ALLOWED_BROWSER_USE_SUBCOMMAND,
        target_url,
    )
    forbidden = set(FORBIDDEN_BROWSER_USE_SUBCOMMANDS) - {ALLOWED_BROWSER_USE_SUBCOMMAND}
    if any(token in forbidden for token in argv):
        raise ValueError("safe-URL run argv includes a forbidden Browser Use subcommand")
    if "--profile" in argv or "--cdp-url" in argv or "--connect" in argv or "--headed" in argv:
        raise ValueError("safe-URL run argv includes a forbidden browser/profile option")
    if not _is_loopback_http(target_url):
        raise ValueError("safe-URL run target must be loopback http")
    return argv


def _run_browser_use_open(argv: tuple[str, ...], timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(argv),
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
            "stdout_excerpt": _excerpt(exc.stdout),
            "stderr_excerpt": _excerpt(exc.stderr),
        }
    except OSError as exc:
        return {
            "attempted": True,
            "timed_out": False,
            "exit_code": None,
            "stdout_excerpt": "",
            "stderr_excerpt": str(exc),
        }
    return {
        "attempted": True,
        "timed_out": False,
        "exit_code": completed.returncode,
        "stdout_excerpt": _excerpt(completed.stdout),
        "stderr_excerpt": _excerpt(completed.stderr),
    }


def _run_browser_use_close(executable: str, session_name: str, timeout_seconds: int) -> dict[str, Any]:
    argv = (executable, "--json", "--session", session_name, "close")
    try:
        completed = subprocess.run(
            list(argv),
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
            "stdout_excerpt": _excerpt(exc.stdout),
            "stderr_excerpt": _excerpt(exc.stderr),
        }
    except OSError as exc:
        return {
            "attempted": True,
            "timed_out": False,
            "exit_code": None,
            "stdout_excerpt": "",
            "stderr_excerpt": str(exc),
        }
    return {
        "attempted": True,
        "timed_out": False,
        "exit_code": completed.returncode,
        "stdout_excerpt": _excerpt(completed.stdout),
        "stderr_excerpt": _excerpt(completed.stderr),
    }


def _start_target_process(vault_root: Path, host: str, port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "runtime.studio.product_ui_test_app",
            "--host",
            host,
            "--port",
            str(port),
            "--vault-root",
            str(vault_root),
        ],
        cwd=str(vault_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _stop_owned_process(process: subprocess.Popen[str] | None) -> dict[str, Any]:
    if process is None:
        return {"attempted": False, "terminated": False, "exit_code": None}
    if process.poll() is not None:
        return {"attempted": True, "terminated": False, "exit_code": process.returncode}
    process.terminate()
    try:
        process.wait(timeout=5)
        return {"attempted": True, "terminated": True, "exit_code": process.returncode}
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
        return {"attempted": True, "terminated": True, "killed": True, "exit_code": process.returncode}


def _markdown(report: "BrowserUseCLISafeURLValidationRun") -> str:
    payload = report.to_dict()
    lines = [
        "# Browser Use CLI Safe-URL Validation Run",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Target URL: {payload['target_url']}",
        f"- Target process started by runner: {payload['target_process_started_by_runner']}",
        f"- Browser Use attempted: {payload['browser_use_cli_open_attempted']}",
        f"- Browser Use exit code: {payload.get('browser_use_cli_exit_code')}",
        f"- Browser Use timed out: {payload['browser_use_cli_timed_out']}",
        f"- Browser Use close attempted: {payload['browser_use_cli_close_attempted']}",
        f"- Browser Use close exit code: {payload.get('browser_use_cli_close_exit_code')}",
        f"- Next recommended pass: {payload['next_recommended_pass']}",
        "",
        "## Blockers",
    ]
    if payload["blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["blockers"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Boundary",
            "- Allowed Browser Use command: `open` against a ChaseOS-owned loopback URL only.",
            "- No `browser-use install`, real profile, credential/cookie read, tunnel, cloud/provider call, Agent Bus write, Gate mutation, skill activation, or canonical writeback.",
            "",
        ]
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class BrowserUseCLISafeURLValidationRun:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    vault_root: str
    design_evidence_path: str
    target_url: str
    target_health_url: str
    browser_use_executable_path: str
    command_argv: tuple[str, ...]
    command_preview: str
    session_name: str
    target_initially_ready: bool
    target_process_started_by_runner: bool
    target_process_id: int | None
    target_ready_after_start: bool
    target_health: dict[str, Any]
    browser_use_cli_open_attempted: bool
    browser_use_cli_timed_out: bool
    browser_use_cli_exit_code: int | None
    browser_use_cli_stdout_excerpt: str
    browser_use_cli_stderr_excerpt: str
    browser_use_open_succeeded: bool
    browser_use_cli_close_attempted: bool
    browser_use_cli_close_timed_out: bool
    browser_use_cli_close_exit_code: int | None
    browser_use_cli_close_stdout_excerpt: str
    browser_use_cli_close_stderr_excerpt: str
    browser_use_close_succeeded: bool
    browser_dependency_install_command_run: bool
    browser_dependency_download_verified: bool
    browser_dependency_auto_download_possible: bool
    cleanup: dict[str, Any]
    blockers: tuple[str, ...]
    next_recommended_pass: str
    writes_evidence: bool = False
    dependency_install_command_attempted: bool = False
    browser_command_execution_attempted: bool = True
    browser_launch_attempted: bool = True
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
            raise ValueError("invalid Browser Use CLI safe-URL run record type")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("invalid Browser Use CLI safe-URL run schema version")
        if self.status not in {
            STATUS_COMPLETE,
            STATUS_BLOCKED_DESIGN,
            STATUS_BLOCKED_TARGET,
            STATUS_FAILED_BROWSER_USE,
        }:
            raise ValueError("invalid Browser Use CLI safe-URL run status")
        if not _is_loopback_http(self.target_url):
            raise ValueError("safe-URL run target must be loopback http")
        if ALLOWED_BROWSER_USE_SUBCOMMAND not in self.command_argv:
            raise ValueError("safe-URL run must execute Browser Use open")
        if self.browser_dependency_install_command_run:
            raise ValueError("safe-URL run must not run browser-use install")
        forbidden_flags = (
            self.dependency_install_command_attempted,
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
            raise ValueError("safe-URL run attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["command_argv"] = list(self.command_argv)
        payload["blockers"] = list(self.blockers)
        payload["forbidden_effects"] = list(self.forbidden_effects)
        return payload


def build_browser_use_cli_safe_url_validation_run(
    vault_root: str | Path,
    *,
    design_evidence: str | Path | None = None,
    run_browser_use: bool = True,
    run_timeout_seconds: int = DEFAULT_RUN_TIMEOUT_SECONDS,
    target_ready_timeout_seconds: int = DEFAULT_TARGET_READY_TIMEOUT_SECONDS,
    session_name: str = DEFAULT_SESSION_NAME,
    generated_at: str | None = None,
) -> BrowserUseCLISafeURLValidationRun:
    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    design_path = Path(design_evidence) if design_evidence else DEFAULT_DESIGN_EVIDENCE
    if not design_path.is_absolute():
        design_path = vault / design_path
    design_payload = _read_json(design_path)
    design = build_browser_use_cli_safe_url_validation_design(vault)

    blockers: list[str] = []
    if design.status != DESIGN_STATUS_READY or design_payload.get("status") != DESIGN_STATUS_READY:
        blockers.append("safe_url_validation_design_evidence_not_ready")

    target_url = str(design_payload.get("target_url") or design.target_url)
    executable = str(
        design_payload.get("browser_use_executable_path")
        or design_payload.get("browser_use_executable")
        or design.browser_use_executable_path
    )
    if not executable or not Path(executable).is_file():
        blockers.append("browser_use_executable_not_found")
    if not _is_loopback_http(target_url):
        blockers.append("safe_url_target_not_loopback_http")

    health_url = _health_url_for(target_url)
    command_argv = _safe_browser_use_argv(executable or "browser-use", target_url, session_name)
    initial_health = _probe_url_json(health_url)
    initially_ready = bool(initial_health.get("ok"))
    target_process: subprocess.Popen[str] | None = None
    target_started = False
    target_pid: int | None = None
    target_health = initial_health
    ready_after_start = initially_ready
    browser_use_result = {
        "attempted": False,
        "timed_out": False,
        "exit_code": None,
        "stdout_excerpt": "",
        "stderr_excerpt": "",
    }
    browser_use_close_result = {
        "attempted": False,
        "timed_out": False,
        "exit_code": None,
        "stdout_excerpt": "",
        "stderr_excerpt": "",
    }

    try:
        if not blockers and run_browser_use and not initially_ready:
            target_process = _start_target_process(vault, DEFAULT_TARGET_HOST, DEFAULT_TARGET_PORT)
            target_started = True
            target_pid = target_process.pid
            target_health = _wait_for_health(health_url, timeout_seconds=target_ready_timeout_seconds)
            ready_after_start = bool(target_health.get("ok"))
        if not blockers and run_browser_use and not ready_after_start:
            blockers.append("safe_url_target_health_not_ready")
        if not blockers and run_browser_use:
            browser_use_result = _run_browser_use_open(command_argv, run_timeout_seconds)
            if browser_use_result["attempted"]:
                browser_use_close_result = _run_browser_use_close(
                    executable or "browser-use",
                    session_name,
                    min(run_timeout_seconds, 30),
                )
        elif not run_browser_use:
            blockers.append("browser_use_open_not_run")
    finally:
        cleanup = _stop_owned_process(target_process)

    open_succeeded = (
        bool(browser_use_result["attempted"])
        and not bool(browser_use_result["timed_out"])
        and browser_use_result["exit_code"] == 0
    )
    close_succeeded = (
        bool(browser_use_close_result["attempted"])
        and not bool(browser_use_close_result["timed_out"])
        and browser_use_close_result["exit_code"] == 0
    )
    if blockers:
        status = STATUS_BLOCKED_DESIGN if "safe_url_validation_design_evidence_not_ready" in blockers else STATUS_BLOCKED_TARGET
    elif not open_succeeded:
        status = STATUS_FAILED_BROWSER_USE
        blockers.append("browser_use_cli_open_failed")
        if browser_use_result["timed_out"]:
            blockers.append("browser_use_cli_open_timed_out")
        elif browser_use_result["exit_code"] not in (0, None):
            blockers.append(f"browser_use_cli_open_exit_code:{browser_use_result['exit_code']}")
    elif not close_succeeded:
        status = STATUS_FAILED_BROWSER_USE
        blockers.append("browser_use_cli_close_failed")
        if browser_use_close_result["timed_out"]:
            blockers.append("browser_use_cli_close_timed_out")
        elif browser_use_close_result["exit_code"] not in (0, None):
            blockers.append(f"browser_use_cli_close_exit_code:{browser_use_close_result['exit_code']}")
    else:
        status = STATUS_COMPLETE

    next_pass = (
        "browser-runtime-external-validation-closeout"
        if status == STATUS_COMPLETE
        else "inspect-browser-use-cli-safe-url-validation-run-blocker"
    )
    stderr = str(browser_use_result["stderr_excerpt"])
    stdout = str(browser_use_result["stdout_excerpt"])
    browser_dependency_auto_download_possible = (
        "install" in stderr.lower()
        or "chromium" in stderr.lower()
        or "browser" in stderr.lower()
        or "playwright" in stderr.lower()
        or "install" in stdout.lower()
    )

    report = BrowserUseCLISafeURLValidationRun(
        record_type=RECORD_TYPE,
        schema_version=SCHEMA_VERSION,
        generated_at=timestamp,
        status=status,
        vault_root=str(vault),
        design_evidence_path=str(design_path),
        target_url=target_url,
        target_health_url=health_url,
        browser_use_executable_path=executable,
        command_argv=command_argv,
        command_preview=" ".join(command_argv),
        session_name=session_name,
        target_initially_ready=initially_ready,
        target_process_started_by_runner=target_started,
        target_process_id=target_pid,
        target_ready_after_start=ready_after_start,
        target_health=target_health,
        browser_use_cli_open_attempted=bool(browser_use_result["attempted"]),
        browser_use_cli_timed_out=bool(browser_use_result["timed_out"]),
        browser_use_cli_exit_code=browser_use_result["exit_code"],
        browser_use_cli_stdout_excerpt=str(browser_use_result["stdout_excerpt"]),
        browser_use_cli_stderr_excerpt=str(browser_use_result["stderr_excerpt"]),
        browser_use_open_succeeded=open_succeeded,
        browser_use_cli_close_attempted=bool(browser_use_close_result["attempted"]),
        browser_use_cli_close_timed_out=bool(browser_use_close_result["timed_out"]),
        browser_use_cli_close_exit_code=browser_use_close_result["exit_code"],
        browser_use_cli_close_stdout_excerpt=str(browser_use_close_result["stdout_excerpt"]),
        browser_use_cli_close_stderr_excerpt=str(browser_use_close_result["stderr_excerpt"]),
        browser_use_close_succeeded=close_succeeded,
        browser_dependency_install_command_run=False,
        browser_dependency_download_verified=open_succeeded,
        browser_dependency_auto_download_possible=browser_dependency_auto_download_possible,
        cleanup=cleanup,
        blockers=tuple(blockers),
        next_recommended_pass=next_pass,
        browser_command_execution_attempted=bool(browser_use_result["attempted"]),
        browser_launch_attempted=bool(browser_use_result["attempted"]),
    )
    report.validate()
    return report


def write_browser_use_cli_safe_url_validation_run_evidence(
    vault_root: str | Path,
    report: BrowserUseCLISafeURLValidationRun,
    *,
    run_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT
    if root.is_absolute():
        raise ValueError("evidence root must be vault-relative")
    slug = run_slug or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-browser-use-cli-safe-url-validation-run"
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
        description="Run bounded no-account Browser Use CLI safe-URL validation."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--design-evidence", default=None, metavar="PATH")
    parser.add_argument("--run-browser-use", action="store_true")
    parser.add_argument("--run-timeout-seconds", type=int, default=DEFAULT_RUN_TIMEOUT_SECONDS)
    parser.add_argument(
        "--target-ready-timeout-seconds",
        type=int,
        default=DEFAULT_TARGET_READY_TIMEOUT_SECONDS,
    )
    parser.add_argument("--session-name", default=DEFAULT_SESSION_NAME)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--run-slug", default=None, metavar="SLUG")
    parser.add_argument("--evidence-root", default=None, metavar="PATH")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report = build_browser_use_cli_safe_url_validation_run(
        args.vault_root,
        design_evidence=args.design_evidence,
        run_browser_use=args.run_browser_use,
        run_timeout_seconds=args.run_timeout_seconds,
        target_ready_timeout_seconds=args.target_ready_timeout_seconds,
        session_name=args.session_name,
    )
    payload = report.to_dict()
    if args.write_evidence:
        payload["evidence_write"] = write_browser_use_cli_safe_url_validation_run_evidence(
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
        print(f"browser_use_cli_exit_code: {payload['browser_use_cli_exit_code']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
    return 0 if report.status == STATUS_COMPLETE else 1


if __name__ == "__main__":
    raise SystemExit(main())
