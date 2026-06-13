"""Read-only Full Studio desktop/card UI inventory proof packet.

This generator composes the live native-shell panel registry with the newest
Pass 10B/WebView2 evidence so closure reviewers can compare mounted Studio
card surfaces against the Full Studio desktop/card UI closure criteria without
launching Studio, consuming approvals, or mutating host/canonical state.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.installer_plan import build_studio_installer_plan
from runtime.studio.product_hardening_status import build_studio_product_hardening_status
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

SURFACE_ID = "studio_full_desktop_card_ui_inventory_proof"
MODEL_VERSION = "studio.full_desktop_card_ui_inventory_proof.v1"
DEFAULT_EVIDENCE_DIR = Path("07_LOGS") / "Studio-Graph-Views"
DEFAULT_OUTPUT_DIR = DEFAULT_EVIDENCE_DIR / "full-desktop-card-ui-inventory-proof"
CLOSURE_CRITERIA_PATH = "06_AGENTS/ChaseOS-Studio-Full-Desktop-Card-UI-Closure-Criteria.md"
PANEL_REGISTRY_PATH = "runtime/studio/shell/panel_registry.py"
PRODUCT_HARDENING_PATH = "runtime/studio/product_hardening_status.py"
PASS10B_AUDIT_GLOB = "pass10b-completion-audits/*.json"
VISUAL_QA_GLOB = "*.json"
OPERATOR_PACKET_GLOB = "webview2-operator-remediation-packets/*.json"

PREVIEW_PROOF_KEYWORDS = (
    "preview",
    "proof",
    "readiness",
    "status",
    "plan",
    "contract",
    "diagnostic",
    "audit",
    "queue",
    "handoff",
    "completion",
    "governance",
)

NO_NEW_AUTHORITY = {
    "approval_consumption": False,
    "installer_execution": False,
    "signing_execution": False,
    "startup_mutation": False,
    "release_mutation": False,
    "host_mutation": False,
    "provider_calls": False,
    "connector_calls": False,
    "agent_bus_writes": False,
    "gate_mutation": False,
    "workflow_mutation": False,
    "canonical_writeback": False,
    "packaged_app_launch": False,
    "native_screenshot_capture": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _json_generated_at(path: Path) -> str:
    data = _load_json(path)
    return str(data.get("generated_at") or path.name)


def _latest_json_record(vault: Path, glob_pattern: str, *, predicate: Any | None = None) -> dict[str, Any]:
    root = vault / DEFAULT_EVIDENCE_DIR
    candidates = [path for path in root.glob(glob_pattern) if path.is_file()]
    if predicate is not None:
        candidates = [path for path in candidates if predicate(path, _load_json(path))]
    if not candidates:
        return {"path": None, "exists": False, "loaded": False}
    path = max(candidates, key=_json_generated_at)
    data = _load_json(path)
    return {
        "path": _relative_to_vault(vault, path),
        "exists": True,
        "loaded": bool(data),
        "generated_at": data.get("generated_at"),
        "report_type": data.get("report_type"),
        "surface": data.get("surface"),
        "status": data.get("status"),
        "ok": data.get("ok"),
        "next_recommended_pass": data.get("next_recommended_pass"),
        "current_blockers": data.get("current_blockers") or data.get("blockers") or [],
    }


def _installer_lane_pass10b_record(vault: Path) -> dict[str, Any]:
    """Return the Pass 10B audit preferred by installer governance.

    The Studio installer lane intentionally prefers the latest complete Pass 10B
    visual audit when one exists, while newer WebView2 remediation diagnostics
    remain historical unless that lane is explicitly resumed. The card inventory
    proof exposes this preferred installer-lane audit separately from the latest
    current Pass 10B truth so a newer blocked current audit cannot be hidden by
    an older green installer-lane selection.
    """

    installer_plan = build_studio_installer_plan(vault)
    selected = ((installer_plan.get("evidence") or {}).get("pass10b_completion_audit") or {})
    path_value = selected.get("path")
    path = (vault / str(path_value)).resolve() if path_value else None
    payload = _load_json(path) if path and path.is_file() else {}
    payload = payload.get("result") or payload
    return {
        "path": str(path_value) if path_value else None,
        "exists": bool(selected.get("exists")),
        "loaded": bool(payload),
        "generated_at": payload.get("generated_at"),
        "report_type": payload.get("report_type"),
        "surface": payload.get("surface"),
        "status": selected.get("status") or payload.get("status"),
        "ok": selected.get("ok"),
        "report_type_valid": selected.get("report_type_valid"),
        "native_host_policy_allows_launch": selected.get("native_host_policy_allows_launch"),
        "native_packaged_visual_qa_complete": selected.get("native_packaged_visual_qa_complete"),
        "packaged_visual_qa_saved_report_valid": selected.get("packaged_visual_qa_saved_report_valid"),
        "blocks_installer_visual_qa": selected.get("blocks_installer_visual_qa"),
        "missing_or_blocked_ids": selected.get("missing_or_blocked_ids") or [],
        "selection_source": "studio_installer_plan_preferred_pass10b_audit",
        "installer_plan_ok": installer_plan.get("ok"),
        "installer_plan_status": installer_plan.get("status"),
        "installer_plan_blockers": installer_plan.get("blockers") or [],
        "next_recommended_pass": payload.get("next_recommended_pass"),
        "current_blockers": payload.get("current_blockers") or payload.get("blockers") or [],
    }


def _generated_sort_value(record: dict[str, Any]) -> str:
    return str(record.get("generated_at") or record.get("path") or "")


def _pass10b_current_truth_record(
    installer_lane_record: dict[str, Any],
    latest_raw_record: dict[str, Any],
) -> dict[str, Any]:
    """Choose current Pass 10B truth without losing installer-lane context."""

    current = dict(installer_lane_record)
    current["selection_source"] = "studio_installer_plan_preferred_pass10b_audit"

    raw_is_newer = _generated_sort_value(latest_raw_record) > _generated_sort_value(installer_lane_record)
    raw_is_blocked = latest_raw_record.get("exists") is True and latest_raw_record.get("ok") is False
    if raw_is_newer and raw_is_blocked:
        current = dict(latest_raw_record)
        current["selection_source"] = "latest_current_pass10b_audit_newer_blocked_evidence"
        current["installer_lane_preferred_audit_path"] = installer_lane_record.get("path")
        current["installer_lane_preferred_audit_status"] = installer_lane_record.get("status")
        current["installer_lane_preferred_audit_ok"] = installer_lane_record.get("ok")
    return current


def _panel_posture(panel: dict[str, Any]) -> str:
    if panel.get("write_mode") == "approval_gated":
        return "approval_gated"
    searchable = " ".join(
        [
            str(panel.get("id") or ""),
            str(panel.get("label") or ""),
            str(panel.get("source_contract") or ""),
            " ".join(str(method) for method in panel.get("api_methods") or []),
            str(panel.get("blocked_reason") or ""),
        ]
    ).lower()
    if any(keyword in searchable for keyword in PREVIEW_PROOF_KEYWORDS):
        return "preview_or_proof_only"
    return "mounted_native_read_only"


def _card_record(panel: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": panel.get("id"),
        "label": panel.get("label"),
        "status": panel.get("status"),
        "mount_kind": panel.get("mount_kind"),
        "frontend_target": panel.get("frontend_target"),
        "route_hint": panel.get("route_hint"),
        "write_mode": panel.get("write_mode"),
        "execution_posture": _panel_posture(panel),
        "read_only": panel.get("read_only"),
        "possible_writes": panel.get("possible_writes") or [],
        "api_methods": panel.get("api_methods") or [],
        "source_contract": panel.get("source_contract"),
        "blocked_reason": panel.get("blocked_reason"),
        "blocked_authority": panel.get("blocked_authority") or {},
    }


def build_full_desktop_card_ui_inventory_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the read-only closure evidence packet from live repo truth."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    registry = build_native_shell_panel_registry(vault)
    product_hardening = build_studio_product_hardening_status(vault, generated_at=timestamp)
    panels = [_card_record(panel) for panel in registry.get("panels") or []]
    mounted_cards = [panel for panel in panels if panel.get("status") == "mounted"]
    approval_gated_cards = [panel for panel in panels if panel.get("execution_posture") == "approval_gated"]
    preview_or_proof_only_cards = [
        panel for panel in panels if panel.get("execution_posture") == "preview_or_proof_only"
    ]
    mounted_native_read_only_cards = [
        panel for panel in panels if panel.get("execution_posture") == "mounted_native_read_only"
    ]
    blocked_or_non_executable_cards = [
        panel
        for panel in panels
        if panel.get("blocked_reason") or panel.get("execution_posture") in {"approval_gated", "preview_or_proof_only"}
    ]
    installer_lane_pass10b_audit = _installer_lane_pass10b_record(vault)
    latest_raw_pass10b_audit = _latest_json_record(vault, PASS10B_AUDIT_GLOB)
    latest_pass10b_audit = _pass10b_current_truth_record(installer_lane_pass10b_audit, latest_raw_pass10b_audit)
    latest_operator_packet = _latest_json_record(vault, OPERATOR_PACKET_GLOB)
    latest_packaged_visual_qa = _latest_json_record(
        vault,
        VISUAL_QA_GLOB,
        predicate=lambda path, data: "visual-qa" in path.name and data.get("report_type") != "pass10b_visual_proof_completion_audit",
    )
    pass10b_current_green = (
        latest_pass10b_audit.get("exists") is True
        and latest_pass10b_audit.get("ok") is True
        and latest_pass10b_audit.get("native_packaged_visual_qa_complete") is True
        and latest_pass10b_audit.get("packaged_visual_qa_saved_report_valid") is True
    )
    pass10b_current_state_preserved = latest_pass10b_audit.get("exists") is True and latest_pass10b_audit.get("loaded") is True
    declared_panel_count = len(registry.get("panels") or [])
    live_registry_count = len(mounted_cards)
    approval_gated_count = len(approval_gated_cards)

    checks = [
        {
            "name": "live_registry_loaded",
            "ok": registry.get("surface") == "studio_native_shell_panel_registry" and live_registry_count > 0,
            "detail": PANEL_REGISTRY_PATH,
        },
        {
            "name": "all_live_registry_panels_enumerated",
            "ok": len(panels) == declared_panel_count,
            "detail": {
                "card_records": len(panels),
                "mounted_cards": live_registry_count,
                "declared_panels": declared_panel_count,
            },
        },
        {
            "name": "approval_gated_cards_identified",
            "ok": approval_gated_count == int((registry.get("readiness") or {}).get("approval_gated_panel_count") or 0),
            "detail": [panel.get("id") for panel in approval_gated_cards],
        },
        {
            "name": "preview_or_proof_only_cards_identified",
            "ok": bool(preview_or_proof_only_cards),
            "detail": [panel.get("id") for panel in preview_or_proof_only_cards],
        },
        {
            "name": "pass10b_current_audit_state_preserved",
            "ok": pass10b_current_state_preserved,
            "detail": latest_pass10b_audit,
        },
        {
            "name": "no_new_authority_declared",
            "ok": not any(NO_NEW_AUTHORITY.values()),
            "detail": dict(NO_NEW_AUTHORITY),
        },
    ]
    ok = all(bool(check["ok"]) for check in checks)

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": (
            "card_inventory_packet_incomplete"
            if not ok
            else "card_inventory_packet_ready_pass10b_current_audit_green"
            if pass10b_current_green
            else "card_inventory_packet_ready_pass10b_still_blocked"
        ),
        "generated_at": timestamp,
        "vault_root": str(vault),
        "claim_decision": {
            "full_desktop_card_ui_closed": False,
            "reason": "Live card inventory evidence exists, but the latest current Pass 10B audit remains blocked when newer blocked evidence is present; target-effect execution, installer execution, provider/runtime/browser dispatch, real target workspace migration, and host/release follow-through remain open or explicitly deferred.",
            "blocked_until": "explicit MVP deferral or verified exact-once execution evidence exists for the remaining target-effect, installer, runtime/provider/browser, target-workspace, and host/release closure lanes",
        },
        "product_lane": {
            "native_lane_command": "chaseos studio shell",
            "legacy_compatibility_qa_lane_command": "chaseos studio desktop-shell-app",
        },
        "summary": {
            "live_registry_mounted_panel_count": live_registry_count,
            "live_registry_declared_panel_count": declared_panel_count,
            "parent_snapshot_mounted_panel_count": 30,
            "parent_snapshot_note": (
                f"Parent handoff reported 30 mounted panels; this packet uses live registry truth "
                f"and currently finds {live_registry_count} mounted panels out of {declared_panel_count} declared panels."
            ),
            "approval_gated_panel_count": approval_gated_count,
            "preview_or_proof_only_panel_count": len(preview_or_proof_only_cards),
            "mounted_native_read_only_panel_count": len(mounted_native_read_only_cards),
            "blocked_or_non_executable_panel_count": len(blocked_or_non_executable_cards),
            "pass10b_current_status": latest_pass10b_audit.get("status"),
            "pass10b_current_ok": latest_pass10b_audit.get("ok"),
            "pass10b_current_selection_source": latest_pass10b_audit.get("selection_source"),
            "pass10b_installer_lane_preferred_status": installer_lane_pass10b_audit.get("status"),
            "pass10b_installer_lane_preferred_ok": installer_lane_pass10b_audit.get("ok"),
            "roadmap_item_should_remain_open": True,
        },
        "source_references": {
            "closure_criteria": CLOSURE_CRITERIA_PATH,
            "panel_registry": PANEL_REGISTRY_PATH,
            "product_hardening_status": PRODUCT_HARDENING_PATH,
            "latest_pass10b_completion_audit": latest_pass10b_audit,
            "installer_lane_preferred_pass10b_completion_audit": installer_lane_pass10b_audit,
            "latest_raw_pass10b_completion_audit": latest_raw_pass10b_audit,
            "latest_packaged_visual_qa_report": latest_packaged_visual_qa,
            "latest_webview2_operator_remediation_packet": latest_operator_packet,
            "product_hardening_composed_status": {
                "ok": product_hardening.get("ok"),
                "status": product_hardening.get("status"),
                "summary": product_hardening.get("summary"),
                "source_contracts": product_hardening.get("source_contracts"),
            },
        },
        "card_inventory": {
            "mounted_native_ui": mounted_cards,
            "mounted_native_read_only": mounted_native_read_only_cards,
            "preview_or_proof_only": preview_or_proof_only_cards,
            "approval_gated": approval_gated_cards,
            "blocked_or_non_executable": blocked_or_non_executable_cards,
        },
        "authority": dict(NO_NEW_AUTHORITY),
        "unverified": [
            "This packet does not launch the native shell or packaged executable.",
            "This packet does not capture a screenshot or rerun packaged visual QA.",
            "This packet does not consume approvals or execute target-effect writes.",
            "This packet does not mutate Gate, workflow, Agent Bus, provider/connector, host, release, startup, installer, signing, or canonical state.",
        ],
        "checks": checks,
        "next_recommended_pass": latest_pass10b_audit.get("next_recommended_pass")
        or installer_lane_pass10b_audit.get("next_recommended_pass")
        or "studio-installer-build-approved-execution-proof --execute",
    }


def write_full_desktop_card_ui_inventory_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    packet = build_full_desktop_card_ui_inventory_proof(vault, generated_at=generated_at)
    timestamp = (packet["generated_at"].replace(":", "").replace("-", "").split(".")[0].replace("T", "T"))
    target = Path(output_path) if output_path else vault / DEFAULT_OUTPUT_DIR / f"{timestamp}-full-desktop-card-ui-inventory-proof.json"
    if not target.is_absolute():
        target = vault / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    packet["written_report"] = _relative_to_vault(vault, target)
    target.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Full Studio desktop/card UI inventory proof packet.")
    parser.add_argument("--vault-root", default=".", help="Vault/repo root. Defaults to current directory.")
    parser.add_argument("--generated-at", default=None, help="Override generated_at timestamp for deterministic tests.")
    parser.add_argument("--write-report", action="store_true", help="Write JSON packet under 07_LOGS/Studio-Graph-Views/...")
    parser.add_argument("--output-path", default=None, help="Optional output path for --write-report.")
    parser.add_argument("--json", action="store_true", help="Print JSON payload.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.write_report:
        payload = write_full_desktop_card_ui_inventory_proof(
            args.vault_root,
            generated_at=args.generated_at,
            output_path=args.output_path,
        )
    else:
        payload = build_full_desktop_card_ui_inventory_proof(args.vault_root, generated_at=args.generated_at)
    if args.json or args.write_report:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{payload['status']}: mounted={payload['summary']['live_registry_mounted_panel_count']} approval_gated={payload['summary']['approval_gated_panel_count']} pass10b={payload['summary']['pass10b_current_status']}")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
