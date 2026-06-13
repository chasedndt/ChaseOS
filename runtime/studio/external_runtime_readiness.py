"""Read-only Studio external runtime readiness gate.

This module composes Browser Use CLI and Excalidraw target/readiness status so
Studio agents can decide whether an external branch may start. It does not
install dependencies, invoke browser-use, probe targets, launch browsers,
connect CDP, invoke MCP, grant approvals, write skills, enqueue Agent Bus tasks,
call providers, mutate Gate, or write canonical ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_use_cli_validation import (
    build_browser_use_cli_validation_status,
)
from runtime.browser_runtime.env_config import (
    BROWSER_USE_CLI_ENV,
    browser_use_cli_executable_from_env,
)
from runtime.browser_runtime.excalidraw_live_chain_readiness import (
    EXCALIDRAW_LIVE_CHAIN_READINESS_READY,
    build_excalidraw_live_chain_readiness,
)
from runtime.browser_runtime.excalidraw_target_response_resolver import (
    EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED,
    resolve_excalidraw_target_response,
)


RECORD_TYPE = "studio_external_runtime_readiness"
SCHEMA_VERSION = "studio.external_runtime_readiness.v1"
STATUS_BLOCKED = "blocked_external_runtime_setup_missing"
STATUS_READY_BROWSER_USE = "ready_for_browser_use_cli_validation"
STATUS_READY_EXCALIDRAW = "ready_for_excalidraw_target_or_live_proof"
STATUS_READY_BOTH = "ready_for_external_runtime_branches"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Studio-Graph-Views")

FORBIDDEN_EFFECTS = (
    "dependency_install",
    "subprocess_probe",
    "server_start",
    "network_probe",
    "browser_launch",
    "browser_use_cli_live_run",
    "cdp_connection",
    "mcp_invocation",
    "mcp_tool_call",
    "target_navigation",
    "screenshot_capture",
    "approval_grant",
    "approval_execution",
    "approval_decision_consumed",
    "idempotency_marker_written",
    "real_profile_access",
    "credential_or_cookie_read",
    "cookie_export",
    "browser_profile_sync",
    "public_tunnel",
    "trusted_skill_write",
    "skill_activation",
    "agent_bus_enqueue",
    "provider_call",
    "connector_call",
    "gate_mutation",
    "canonical_writeback",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    raise TypeError("status object must be a dict or expose to_dict()")


def _browser_use_executable(executable: str | None = None) -> str:
    configured = (executable or "").strip()
    if configured:
        return configured
    return browser_use_cli_executable_from_env()[0]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _markdown(report: "StudioExternalRuntimeReadiness") -> str:
    payload = report.to_dict()
    lines = [
        "# Studio External Runtime Readiness",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Browser Use branch ready: {payload['browser_use_branch_ready']}",
        f"- Excalidraw branch ready: {payload['excalidraw_branch_ready']}",
        f"- Next recommended pass: {payload['next_recommended_pass']}",
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
            "- No dependency install.",
            "- No Browser Use CLI live run.",
            "- No Excalidraw live proof.",
            "- No browser launch, CDP connection, MCP invocation, approval execution, Agent Bus write, provider/connector call, Gate mutation, or canonical writeback.",
            "",
        ]
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class StudioExternalRuntimeReadiness:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    vault_root: str
    browser_use_branch_ready: bool
    excalidraw_branch_ready: bool
    next_recommended_pass: str
    blockers: tuple[str, ...]
    browser_use: dict[str, Any]
    excalidraw_target_response: dict[str, Any]
    excalidraw_live_chain: dict[str, Any]
    read_only: bool = True
    writes_evidence: bool = False
    dependency_install_attempted: bool = False
    subprocess_probe_attempted: bool = False
    server_start_attempted: bool = False
    network_probe_attempted: bool = False
    browser_launch_attempted: bool = False
    browser_use_cli_live_run_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_invocation_attempted: bool = False
    mcp_tool_call_attempted: bool = False
    target_navigation_attempted: bool = False
    screenshot_capture_attempted: bool = False
    approval_grant_attempted: bool = False
    approval_execution_attempted: bool = False
    approval_decision_consumed: bool = False
    idempotency_marker_written: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    public_tunnel_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    connector_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    forbidden_effects: tuple[str, ...] = FORBIDDEN_EFFECTS

    def validate(self) -> None:
        if self.record_type != RECORD_TYPE:
            raise ValueError("invalid Studio external runtime readiness record type")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("invalid Studio external runtime readiness schema version")
        if self.status not in {
            STATUS_BLOCKED,
            STATUS_READY_BROWSER_USE,
            STATUS_READY_EXCALIDRAW,
            STATUS_READY_BOTH,
        }:
            raise ValueError("invalid Studio external runtime readiness status")
        if not self.read_only:
            raise ValueError("external runtime readiness must remain read-only")
        if self.status == STATUS_BLOCKED and not self.blockers:
            raise ValueError("blocked external runtime readiness requires blockers")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.subprocess_probe_attempted,
            self.server_start_attempted,
            self.network_probe_attempted,
            self.browser_launch_attempted,
            self.browser_use_cli_live_run_attempted,
            self.cdp_connection_attempted,
            self.mcp_invocation_attempted,
            self.mcp_tool_call_attempted,
            self.target_navigation_attempted,
            self.screenshot_capture_attempted,
            self.approval_grant_attempted,
            self.approval_execution_attempted,
            self.approval_decision_consumed,
            self.idempotency_marker_written,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.cookie_export_attempted,
            self.browser_profile_sync_attempted,
            self.public_tunnel_attempted,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.connector_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Studio external runtime readiness attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["forbidden_effects"] = list(self.forbidden_effects)
        return payload


def build_studio_external_runtime_readiness(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    browser_use_executable: str | None = None,
    browser_use_status: Any | None = None,
    excalidraw_target_response: Any | None = None,
    excalidraw_live_chain: Any | None = None,
) -> StudioExternalRuntimeReadiness:
    """Build a no-execution readiness gate for external Browser Runtime branches."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    browser_use_payload = _to_dict(
        browser_use_status
        or build_browser_use_cli_validation_status(
            vault,
            executable=_browser_use_executable(browser_use_executable),
            generated_at=timestamp,
        )
    )
    target_payload = _to_dict(
        excalidraw_target_response
        or resolve_excalidraw_target_response(vault, generated_at=timestamp)
    )
    chain_payload = _to_dict(
        excalidraw_live_chain
        or build_excalidraw_live_chain_readiness(vault, generated_at=timestamp)
    )

    browser_use_ready = (
        browser_use_payload.get("status")
        == "ready_for_operator_authorized_live_validation_no_execution"
    )
    target_accepted = target_payload.get("status") == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED
    live_chain_ready = chain_payload.get("status") == EXCALIDRAW_LIVE_CHAIN_READINESS_READY
    excalidraw_ready = target_accepted or live_chain_ready

    blockers: list[str] = []
    if not browser_use_ready:
        blockers.extend(
            f"browser_use:{blocker}"
            for blocker in browser_use_payload.get("blockers", ())
        )
        if not browser_use_payload.get("blockers"):
            blockers.append(f"browser_use_status:{browser_use_payload.get('status')}")
    if not excalidraw_ready:
        if target_payload.get("status") != EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED:
            blockers.append(f"excalidraw_target_response:{target_payload.get('status')}")
        for blocker in chain_payload.get("blockers", ()):
            blockers.append(f"excalidraw_live_chain:{blocker}")

    if browser_use_ready and excalidraw_ready:
        status = STATUS_READY_BOTH
        next_pass = "operator-choose-external-browser-use-or-excalidraw-proof-branch"
    elif browser_use_ready:
        status = STATUS_READY_BROWSER_USE
        next_pass = "browser-use-cli-external-runtime-validation"
    elif excalidraw_ready:
        status = STATUS_READY_EXCALIDRAW
        next_pass = "excalidraw-target-and-readiness"
    else:
        status = STATUS_BLOCKED
        next_pass = "external-runtime-provide-browser-use-cli-or-excalidraw-loopback-target"

    report = StudioExternalRuntimeReadiness(
        record_type=RECORD_TYPE,
        schema_version=SCHEMA_VERSION,
        generated_at=timestamp,
        status=status,
        vault_root=str(vault),
        browser_use_branch_ready=browser_use_ready,
        excalidraw_branch_ready=excalidraw_ready,
        next_recommended_pass=next_pass,
        blockers=tuple(blockers),
        browser_use=browser_use_payload,
        excalidraw_target_response=target_payload,
        excalidraw_live_chain=chain_payload,
    )
    report.validate()
    return report


def write_studio_external_runtime_readiness_evidence(
    vault_root: str | Path,
    report: StudioExternalRuntimeReadiness,
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT
    if root.is_absolute():
        raise ValueError("evidence root must be vault-relative")
    slug = evidence_slug or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-studio-external-runtime-readiness"
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
        description="Report whether external Browser Use CLI or Excalidraw branches may start."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--write-evidence", action="store_true", help="Write JSON/Markdown evidence.")
    parser.add_argument("--evidence-slug", default=None, metavar="SLUG")
    parser.add_argument(
        "--evidence-root",
        default=None,
        metavar="PATH",
        help="Vault-relative evidence root; defaults to 07_LOGS/Studio-Graph-Views",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report = build_studio_external_runtime_readiness(args.vault_root)
    payload = report.to_dict()
    if args.write_evidence:
        payload["evidence_write"] = write_studio_external_runtime_readiness_evidence(
            args.vault_root,
            report,
            evidence_slug=args.evidence_slug,
            evidence_root=args.evidence_root,
        )
        payload["writes_evidence"] = True
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"browser_use_branch_ready: {payload['browser_use_branch_ready']}")
        print(f"excalidraw_branch_ready: {payload['excalidraw_branch_ready']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
    return 0 if report.status != STATUS_BLOCKED else 1


if __name__ == "__main__":
    raise SystemExit(main())
