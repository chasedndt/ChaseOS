"""Read-only host-policy unblock readiness for packaged Studio visual QA."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.packaged_app_launch_smoke import DEFAULT_EXE, _relative_to_vault, _resolve_executable
from runtime.studio.packaged_app_visual_qa import build_packaged_app_visual_qa
from runtime.studio.packaging_proof import _sha256, build_studio_local_packaging_proof


MODEL_VERSION = "studio.packaged_app_host_policy_unblock.v1"
SURFACE_ID = "studio_packaged_app_host_policy_unblock"
DEFAULT_HANDOFF_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "host-policy-unblock-handoffs"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _check(report: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in report.get("checks") or []:
        if item.get("name") == name:
            return item
    return None


def _host_policy_from_probe(report: dict[str, Any] | None) -> dict[str, Any]:
    if not report:
        return {
            "status": "not_probed",
            "blocked_by_windows_application_control": None,
            "launch_error": None,
            "remediation": [
                "Run the bounded host-policy probe before retrying native visual QA.",
            ],
        }
    return (report.get("host_policy") or (report.get("launch") or {}).get("host_policy") or {})


def build_packaged_app_host_policy_unblock_readiness(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    probe_launch: bool = False,
    settle_seconds: float = 1.0,
    window_timeout_seconds: float = 1.0,
    terminate_timeout_seconds: float = 1.0,
) -> dict[str, Any]:
    """Build a read-only operator handoff for clearing packaged-app host policy blocks."""

    vault = _vault_path(vault_root)
    explicit_executable_path_supplied = executable_path is not None
    exe = _resolve_executable(vault, executable_path or DEFAULT_EXE)
    packaging_proof = build_studio_local_packaging_proof(vault)
    visual_probe: dict[str, Any] | None = None
    packaging_output_seen = bool((packaging_proof.get("outputs") or {}).get("executable_exists"))
    executable_exists = exe.is_file()
    packaging_executable_seen = bool(
        packaging_output_seen or (explicit_executable_path_supplied and executable_exists)
    )
    if probe_launch and executable_exists and packaging_executable_seen:
        visual_probe = build_packaged_app_visual_qa(
            vault,
            executable_path=exe,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
        )

    host_policy = _host_policy_from_probe(visual_probe)
    host_policy_check = _check(visual_probe or {}, "host_policy_allows_launch")
    no_markdown_writes = _check(visual_probe or {}, "no_markdown_writes")
    no_approval_artifact_writes = _check(visual_probe or {}, "no_approval_artifact_writes")
    host_policy_allows_launch = bool(host_policy_check and host_policy_check.get("ok"))
    visual_qa_complete = bool(visual_probe and visual_probe.get("ok"))
    executable_sha256 = (
        _sha256(exe)
        if explicit_executable_path_supplied and executable_exists
        else (packaging_proof.get("outputs") or {}).get("executable_sha256")
    )

    blockers: list[str] = []
    if not executable_exists:
        blockers.append("Packaged Studio executable is missing.")
    if not packaging_executable_seen:
        blockers.append("Local packaging proof does not currently see a generated executable.")
    if not probe_launch:
        blockers.append("Host-policy launch probe has not been run.")
    elif host_policy.get("blocked_by_windows_application_control"):
        blockers.append("Windows Application Control blocks the packaged Studio executable.")
    elif not host_policy_allows_launch:
        blockers.append("Packaged Studio executable still has an unclassified launch blocker.")

    if visual_qa_complete:
        status = "host_policy_unblocked_native_visual_qa_complete"
    elif host_policy.get("blocked_by_windows_application_control"):
        status = "blocked_by_windows_application_control"
    elif probe_launch and host_policy_allows_launch:
        status = "host_policy_unblocked_visual_qa_retry_needed"
    elif not probe_launch:
        status = "host_policy_probe_required"
    else:
        status = "host_policy_unblock_blocked"

    ok = bool(visual_qa_complete)
    next_recommended_pass = (
        "studio-installer-plan-and-governance"
        if visual_qa_complete
        else (
            "pass10b-native-visual-qa-rerun"
            if probe_launch and host_policy_allows_launch
            else "pass10b-native-host-policy-unblock"
        )
    )

    probe_command = (
        "python -m chaseos studio packaged-app-host-policy-unblock-readiness "
        "--probe-launch --settle-seconds 1 --window-timeout-seconds 1 --terminate-timeout-seconds 1 --json"
    )
    visual_qa_command = (
        "python -m chaseos studio packaged-app-visual-qa "
        "--settle-seconds 3 --window-timeout-seconds 10 --terminate-timeout-seconds 5 --json"
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "executable": {
            "path": _relative_to_vault(vault, exe),
            "exists": executable_exists,
            "sha256": executable_sha256,
            "source": "explicit_executable_path" if explicit_executable_path_supplied else "default_packaging_proof",
        },
        "probe": {
            "probe_launch": bool(probe_launch),
            "settle_seconds": float(settle_seconds),
            "window_timeout_seconds": float(window_timeout_seconds),
            "terminate_timeout_seconds": float(terminate_timeout_seconds),
            "visual_qa_report": visual_probe,
        },
        "host_policy": host_policy,
        "readiness": {
            "packaged_executable_ready_for_probe": bool(executable_exists and packaging_executable_seen),
            "host_policy_probe_performed": bool(probe_launch),
            "host_policy_allows_launch": host_policy_allows_launch,
            "native_visual_qa_complete": visual_qa_complete,
            "native_visual_qa_can_retry": bool(probe_launch and host_policy_allows_launch and not visual_qa_complete),
            "operator_action_required": not ok,
            "next_recommended_pass": next_recommended_pass,
            "blockers": blockers,
        },
        "operator_handoff": {
            "required_external_actions": [
                "Resolve Windows Application Control policy for the packaged Studio executable path.",
                "Use an operator/admin-approved path such as signing, allowlisting, or rebuilding under an allowed policy context.",
                "Rerun the bounded host-policy probe before claiming native visual QA is unblocked.",
                "Rerun packaged native visual QA and require real screenshot capture plus nonblank verification.",
            ],
            "acceptance_criteria": [
                "`host_policy_allows_launch=true`",
                "`process_alive_before_capture=true`",
                "`window_capture_ok=true`",
                "`screenshot_nonblank=true`",
                "`no_markdown_writes=true`",
                "`no_approval_artifact_writes=true`",
            ],
            "probe_command": probe_command,
            "visual_qa_command": visual_qa_command,
        },
        "authority": {
            "mutates_host_policy": False,
            "signs_executable": False,
            "allowlists_executable": False,
            "writes_installer": False,
            "writes_host_startup": False,
            "executes_approval_decisions": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "checks": [
            {"name": "packaged_executable_exists", "ok": executable_exists, "detail": _relative_to_vault(vault, exe)},
            {"name": "packaging_proof_executable_seen", "ok": packaging_executable_seen, "detail": packaging_proof.get("status", "")},
            {"name": "host_policy_probe_performed", "ok": bool(probe_launch), "detail": "bounded launch probe requested"},
            {"name": "host_policy_allows_launch", "ok": host_policy_allows_launch, "detail": host_policy.get("status")},
            {"name": "native_visual_qa_complete", "ok": visual_qa_complete, "detail": (visual_probe or {}).get("status", "not_run")},
            {
                "name": "codex_did_not_mutate_host_policy",
                "ok": True,
                "detail": "report is read-only; host policy changes require operator/admin action",
            },
            {
                "name": "no_markdown_writes",
                "ok": bool(no_markdown_writes.get("ok")) if no_markdown_writes else True,
                "detail": (no_markdown_writes or {}).get("detail", "no probe markdown write observed"),
            },
            {
                "name": "no_approval_artifact_writes",
                "ok": bool(no_approval_artifact_writes.get("ok")) if no_approval_artifact_writes else True,
                "detail": (no_approval_artifact_writes or {}).get("detail", "no approval artifact write observed"),
            },
        ],
        "blockers": blockers,
        "unverified": [
            "Host-policy unblock itself must be performed outside Codex by the operator or host administrator.",
            "Native screenshot proof remains unverified until the packaged executable can launch.",
            "Native semantic UI and text-overlap checks remain unverified until screenshot capture succeeds.",
        ],
        "next_recommended_pass": next_recommended_pass,
    }


def format_packaged_app_host_policy_unblock_readiness(report: dict[str, Any]) -> str:
    readiness = report.get("readiness") or {}
    host_policy = report.get("host_policy") or {}
    handoff = report.get("operator_handoff") or {}
    lines = [
        f"Studio packaged app host-policy unblock readiness: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  executable: {(report.get('executable') or {}).get('path')}",
        f"  executable_exists: {(report.get('executable') or {}).get('exists')}",
        f"  host_policy_status: {host_policy.get('status')}",
        f"  host_policy_allows_launch: {readiness.get('host_policy_allows_launch')}",
        f"  native_visual_qa_complete: {readiness.get('native_visual_qa_complete')}",
        f"  operator_action_required: {readiness.get('operator_action_required')}",
        f"  next: {readiness.get('next_recommended_pass')}",
        f"  probe_command: {handoff.get('probe_command')}",
        f"  visual_qa_command: {handoff.get('visual_qa_command')}",
    ]
    blockers = readiness.get("blockers") or []
    if blockers:
        lines.append(f"  blockers: {', '.join(str(item) for item in blockers)}")
    return "\n".join(lines)


def write_packaged_app_host_policy_unblock_handoff(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    handoff_slug: str | None = None,
    handoff_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write a durable operator handoff without mutating host policy."""

    vault = _vault_path(vault_root)
    root = Path(handoff_root) if handoff_root else DEFAULT_HANDOFF_ROOT
    if not root.is_absolute():
        root = vault / root
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("host-policy unblock handoff root must stay inside the vault workspace") from exc
    slug = handoff_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-pass10b-native-host-policy-unblock"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("host-policy unblock handoff output must stay inside the handoff root") from exc
    root.mkdir(parents=True, exist_ok=True)

    handoff = report.get("operator_handoff") or {}
    readiness = report.get("readiness") or {}
    host_policy = report.get("host_policy") or {}
    payload = {
        "handoff_type": "pass10b_native_host_policy_unblock",
        "generated_at": _now_utc(),
        "status": report.get("status"),
        "ok": report.get("ok"),
        "executable": report.get("executable"),
        "host_policy": host_policy,
        "readiness": readiness,
        "operator_handoff": handoff,
        "authority": report.get("authority"),
        "checks": report.get("checks"),
        "blockers": report.get("blockers"),
        "note": "This handoff is review-only. It does not sign, allowlist, install, mutate host policy, or complete native visual QA.",
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    actions = handoff.get("required_external_actions") or []
    criteria = handoff.get("acceptance_criteria") or []
    lines = [
        "# Pass 10B Native Host Policy Unblock Handoff",
        "",
        f"Generated: {payload['generated_at']}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        "",
        "## Executable",
        "",
        f"- Path: {(report.get('executable') or {}).get('path')}",
        f"- Exists: {(report.get('executable') or {}).get('exists')}",
        f"- SHA-256: {(report.get('executable') or {}).get('sha256')}",
        "",
        "## Host Policy",
        "",
        f"- Status: {host_policy.get('status')}",
        f"- Windows Application Control blocked: {host_policy.get('blocked_by_windows_application_control')}",
        "",
        "## Required External Actions",
        "",
        *[f"- {item}" for item in actions],
        "",
        "## Acceptance Criteria",
        "",
        *[f"- {item}" for item in criteria],
        "",
        "## Rerun Commands",
        "",
        f"- Probe: `{handoff.get('probe_command')}`",
        f"- Visual QA: `{handoff.get('visual_qa_command')}`",
        "",
        "## Authority Boundary",
        "",
        "- This handoff is review-only.",
        "- It does not sign or allowlist the executable.",
        "- It does not mutate Windows Application Control, installer, startup, approval, Agent Bus, workflow, provider, connector, graph, or canonical state.",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
