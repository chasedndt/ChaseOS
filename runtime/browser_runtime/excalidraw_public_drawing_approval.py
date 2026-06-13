"""Approval packet for a future public Excalidraw drawing proof.

This module records the governed approval boundary for one future no-login
public Excalidraw drawing proof. It requires existing public reachability
evidence, defines the exact drawing action, computes the future exact-once
marker path, and optionally writes the approval packet. It does not launch a
browser, navigate, draw, invoke MCP, read profiles/cookies, or mutate canonical
ChaseOS state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_targets import get_known_browser_target
from runtime.browser_runtime.models import slugify


EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_RECORD_TYPE = (
    "excalidraw_public_browser_drawing_proof_approval"
)
EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_VERSION = (
    "browser.excalidraw_public_drawing_approval.v1"
)
EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_READY = (
    "excalidraw_public_browser_drawing_proof_approval_ready_no_execution"
)
EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN = (
    "excalidraw_public_browser_drawing_proof_approval_written_no_execution"
)
EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED = (
    "blocked_excalidraw_public_browser_drawing_proof_approval"
)

APPROVAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals")
IDEMPOTENCY_MARKER_RELATIVE_DIR = APPROVAL_RELATIVE_DIR / "_execution_markers"

DENIED_EFFECTS = (
    "browser_launch_attempted",
    "target_navigation_attempted",
    "drawing_action_attempted",
    "mcp_invocation_attempted",
    "mcp_tool_call_attempted",
    "screenshot_attempted",
    "browser_run_log_written",
    "agent_activity_log_written",
    "draft_skill_written",
    "untrusted_candidate_written",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "cookie_export_attempted",
    "browser_profile_sync_attempted",
    "browser_history_import_attempted",
    "public_tunnel_attempted",
    "browser_harness_used",
    "browser_use_cli_live_used",
    "workflow_use_code_copied",
    "shell_execution_from_browser_runtime_attempted",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
    "canonical_writeback_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    safe_id = slugify(identifier, "excalidraw-public-drawing-approval")
    path = (vault / base_relative / f"{safe_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw approval path escapes base directory: {path}") from exc
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _relative_or_posix(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return path.as_posix()


def _public_reachability_payload_ok(vault: Path, payload: dict[str, Any]) -> bool:
    target = get_known_browser_target("excalidraw")
    screenshot_path = payload.get("screenshot_path")
    screenshot_ok = isinstance(screenshot_path, str) and bool(screenshot_path)
    if screenshot_ok:
        screenshot_ok = (vault / screenshot_path).exists()
    authority = payload.get("authority")
    target_authority_ok = (
        isinstance(authority, dict)
        and (
            (
                authority.get("target_registered_in_chaseos") is True
                and authority.get("target_registry_id") == target.target_id
            )
            or authority.get("target_hardcoded") is True
        )
    )
    authority_ok = (
        isinstance(authority, dict)
        and target_authority_ok
        and authority.get("env_var_required") is False
        and authority.get("no_login_profile_cookies") is True
        and authority.get("no_browser_use_cli") is True
        and authority.get("no_agent_bus_writes") is True
        and authority.get("no_gate_mutation") is True
        and authority.get("no_canonical_mutation") is True
        and authority.get("no_provider_calls") is True
    )
    return (
        payload.get("ok") is True
        and payload.get("status") == "excalidraw_live_browser_proof_complete"
        and str(payload.get("target_url") or "").rstrip("/") == target.url
        and payload.get("canvas_found") is True
        and screenshot_ok
        and authority_ok
    )


def _latest_public_reachability_evidence(vault: Path) -> tuple[str, dict[str, Any] | None]:
    candidates = sorted(
        (vault / "07_LOGS/Browser-Runs").glob("excalidraw_live_proof_*.json"),
        key=lambda path: path.name,
        reverse=True,
    )
    for path in candidates:
        payload = _read_json(path)
        if payload is not None and _public_reachability_payload_ok(vault, payload):
            return _relative_or_posix(vault, path), payload
    return "", None


def _approval_material(
    *,
    target_id: str,
    target_url: str,
    source_reachability_evidence_path: str,
    requested_by: str,
    operator_id: str,
    proof_mode: str,
    drawing_label: str,
) -> dict[str, Any]:
    return {
        "schema_version": EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_VERSION,
        "operation": "excalidraw_public_no_login_browser_drawing_proof",
        "target_registry_id": target_id,
        "target_url": target_url,
        "allowed_domains": ["excalidraw.com"],
        "source_reachability_evidence_path": source_reachability_evidence_path,
        "requested_by": requested_by,
        "operator_id": operator_id,
        "proof_mode": proof_mode,
        "drawing_label": drawing_label,
        "browser_profile_policy": "throwaway_only",
        "allow_login": False,
        "allow_real_profile": False,
        "allow_credentials": False,
        "allow_cookie_export": False,
        "allow_public_tunnel": False,
        "allow_provider_calls": False,
        "allow_agent_bus_enqueue": False,
        "allow_gate_mutation": False,
        "allow_skill_activation": False,
        "allow_trusted_skill_write": False,
        "allow_canonical_writeback": False,
    }


def _approval_id(material: dict[str, Any]) -> str:
    digest = _sha256(material)
    target_slug = slugify(str(material.get("target_registry_id") or "excalidraw"), "excalidraw")
    return f"excalidraw-public-drawing-appr-{target_slug}-{digest[:16]}"


def _action_plan(drawing_label: str, proof_mode: str) -> dict[str, Any]:
    return {
        "proof_mode": proof_mode,
        "allowed_actions": [
            {
                "action": "open_known_target",
                "target_registry_id": "excalidraw",
                "target_url": "https://excalidraw.com",
            },
            {
                "action": "draw_rectangle",
                "shape": "rectangle",
                "count": 1,
                "bounds_policy": "canvas_center_safe_region",
            },
            {
                "action": "add_text_label",
                "text": drawing_label,
                "count": 1,
                "bounds_policy": "near_rectangle_safe_region",
            },
            {
                "action": "capture_screenshot",
                "write_target": "07_LOGS/Browser-Runs/<run-id>_screenshot.png",
            },
            {
                "action": "write_json_evidence",
                "write_target": "07_LOGS/Browser-Runs/<run-id>.json",
            },
        ],
        "forbidden_actions": [
            "account_login",
            "real_profile_use",
            "credential_or_cookie_read",
            "cookie_export",
            "public_tunnel",
            "provider_call",
            "connector_call",
            "agent_bus_enqueue",
            "gate_mutation",
            "trusted_skill_write",
            "skill_activation",
            "canonical_writeback",
        ],
    }


def _write_approval(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = _read_json(path)
        if (
            existing
            and existing.get("approval_id") == payload.get("approval_id")
            and existing.get("request_digest_sha256") == payload.get("request_digest_sha256")
        ):
            return "existing_matching_approval_reused"
        raise ValueError(f"approval artifact already exists with different content: {path}")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return "approval_artifact_written"


@dataclass(frozen=True)
class ExcalidrawPublicDrawingApprovalRequest:
    requested_by: str = "Codex"
    operator_id: str = "operator"
    proof_mode: str = "browser_only_no_login_public_canvas"
    drawing_label: str = "ChaseOS proof"
    write_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExcalidrawPublicDrawingApproval:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    approval_id: str
    request_digest_sha256: str
    target_registry_id: str
    target_url: str
    allowed_domains: tuple[str, ...]
    source_reachability_evidence_path: str
    approval_artifact_path: str
    approval_artifact_written: bool
    approval_artifact_write_status: str
    idempotency_marker_path: str
    idempotency_marker_exists: bool
    future_single_run_approved: bool
    execution_allowed_in_this_pass: bool
    request: ExcalidrawPublicDrawingApprovalRequest
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    action_plan: dict[str, Any] = field(default_factory=dict)
    execution_requirements: tuple[str, ...] = ()
    next_step: str = "excalidraw-public-browser-drawing-proof-run"
    browser_launch_attempted: bool = False
    target_navigation_attempted: bool = False
    drawing_action_attempted: bool = False
    mcp_invocation_attempted: bool = False
    mcp_tool_call_attempted: bool = False
    screenshot_attempted: bool = False
    browser_run_log_written: bool = False
    agent_activity_log_written: bool = False
    draft_skill_written: bool = False
    untrusted_candidate_written: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    browser_history_import_attempted: bool = False
    public_tunnel_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    workflow_use_code_copied: bool = False
    shell_execution_from_browser_runtime_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    denied_effects: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.to_dict()
        payload["allowed_domains"] = list(self.allowed_domains)
        payload["blockers"] = list(self.blockers)
        payload["execution_requirements"] = list(self.execution_requirements)
        return payload

    def validate(self) -> None:
        if self.record_type != EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_RECORD_TYPE:
            raise ValueError("invalid public drawing approval record type")
        if self.schema_version != EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_VERSION:
            raise ValueError("invalid public drawing approval schema version")
        if self.status not in {
            EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_READY,
            EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN,
            EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED,
        }:
            raise ValueError("invalid public drawing approval status")
        if self.status == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED and not self.blockers:
            raise ValueError("blocked public drawing approval requires blockers")
        if self.status != EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED and self.blockers:
            raise ValueError("ready public drawing approval cannot include blockers")
        if self.execution_allowed_in_this_pass:
            raise ValueError("approval pass cannot allow execution in this pass")
        for name in DENIED_EFFECTS:
            if getattr(self, name, False):
                raise ValueError(f"{name} must remain false")
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} denied effect must be false")


def build_excalidraw_public_drawing_approval(
    vault_root: str | Path,
    request: ExcalidrawPublicDrawingApprovalRequest | None = None,
    *,
    generated_at: str | None = None,
) -> ExcalidrawPublicDrawingApproval:
    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    approval_request = request or ExcalidrawPublicDrawingApprovalRequest()
    target = get_known_browser_target("excalidraw")
    reachability_path, reachability_payload = _latest_public_reachability_evidence(vault)
    material = _approval_material(
        target_id=target.target_id,
        target_url=target.url,
        source_reachability_evidence_path=reachability_path,
        requested_by=approval_request.requested_by,
        operator_id=approval_request.operator_id,
        proof_mode=approval_request.proof_mode,
        drawing_label=approval_request.drawing_label,
    )
    approval_id = _approval_id(material)
    request_digest = _sha256(material)
    approval_path = _safe_json_path(vault, APPROVAL_RELATIVE_DIR, approval_id)
    marker_path = _safe_json_path(vault, IDEMPOTENCY_MARKER_RELATIVE_DIR, approval_id)
    marker_exists = marker_path.exists()

    checks = {
        "known_target_registered": {
            "passed": target.target_id == "excalidraw" and target.url == "https://excalidraw.com",
            "target_registry_id": target.target_id,
            "target_url": target.url,
        },
        "public_reachability_evidence_ready": {
            "passed": reachability_payload is not None,
            "source_reachability_evidence_path": reachability_path,
        },
        "drawing_scope_defined": {
            "passed": bool(approval_request.drawing_label.strip()),
            "drawing_label": approval_request.drawing_label,
        },
        "idempotency_marker_absent": {
            "passed": marker_exists is False,
            "idempotency_marker_path": _relative_or_posix(vault, marker_path),
            "idempotency_marker_exists": marker_exists,
        },
        "no_execution_in_approval_pass": {
            "passed": True,
            "browser_launch_attempted": False,
            "drawing_action_attempted": False,
            "mcp_invocation_attempted": False,
        },
    }
    blockers = tuple(name for name, check in checks.items() if not bool(check["passed"]))
    write_status = "not_requested"
    status = (
        EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED
        if blockers
        else EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_READY
    )
    artifact_written = False
    future_approved = False

    result = ExcalidrawPublicDrawingApproval(
        record_type=EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_RECORD_TYPE,
        schema_version=EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_VERSION,
        generated_at=timestamp,
        status=status,
        approval_id=approval_id,
        request_digest_sha256=request_digest,
        target_registry_id=target.target_id,
        target_url=target.url,
        allowed_domains=target.allowed_domains,
        source_reachability_evidence_path=reachability_path,
        approval_artifact_path=_relative_or_posix(vault, approval_path),
        approval_artifact_written=False,
        approval_artifact_write_status=write_status,
        idempotency_marker_path=_relative_or_posix(vault, marker_path),
        idempotency_marker_exists=marker_exists,
        future_single_run_approved=False,
        execution_allowed_in_this_pass=False,
        request=approval_request,
        checks=checks,
        blockers=blockers,
        action_plan=_action_plan(approval_request.drawing_label, approval_request.proof_mode),
        execution_requirements=(
            "consume this approval artifact by matching approval_id and request_digest_sha256",
            "reserve exact-once idempotency marker before browser launch",
            "use throwaway browser context only",
            "do not log in or read credentials/cookies/profile state",
            "draw exactly one rectangle plus the approved text label",
            "write Browser Run JSON and screenshot evidence",
            "write Agent Activity evidence",
            "do not activate or trust any generated skill",
            "do not call providers/connectors, Agent Bus, Gate, or canonical writeback",
        ),
        denied_effects={name: False for name in DENIED_EFFECTS},
        next_step=(
            "excalidraw-public-browser-drawing-proof-run"
            if not blockers
            else "excalidraw-public-live-browser-proof"
        ),
    )
    result.validate()

    if approval_request.write_approval and not blockers:
        payload = result.to_dict()
        payload["status"] = EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN
        payload["approval_artifact_written"] = True
        payload["approval_artifact_write_status"] = "approval_artifact_written"
        payload["future_single_run_approved"] = True
        write_status = _write_approval(approval_path, payload)
        artifact_written = True
        future_approved = True
        result = replace(
            result,
            status=EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN,
            approval_artifact_written=artifact_written,
            approval_artifact_write_status=write_status,
            future_single_run_approved=future_approved,
        )
        result.validate()

    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build public Excalidraw drawing proof approval packet.")
    parser.add_argument("--vault-root", default=".", help="Path to ChaseOS vault root.")
    parser.add_argument("--requested-by", default="Codex")
    parser.add_argument("--operator-id", default="operator")
    parser.add_argument("--proof-mode", default="browser_only_no_login_public_canvas")
    parser.add_argument("--drawing-label", default="ChaseOS proof")
    parser.add_argument("--write-approval", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = build_excalidraw_public_drawing_approval(
        args.vault_root,
        ExcalidrawPublicDrawingApprovalRequest(
            requested_by=args.requested_by,
            operator_id=args.operator_id,
            proof_mode=args.proof_mode,
            drawing_label=args.drawing_label,
            write_approval=args.write_approval,
        ),
    )
    payload = result.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {result.status}")
        print(f"approval_id: {result.approval_id}")
        print(f"approval_artifact_written: {result.approval_artifact_written}")
        print(f"next_step: {result.next_step}")
        for blocker in result.blockers:
            print(f"blocker: {blocker}")
    return 0 if result.status != EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED else 1


if __name__ == "__main__":
    raise SystemExit(main())
