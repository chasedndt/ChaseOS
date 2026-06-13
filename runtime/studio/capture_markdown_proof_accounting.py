"""Focused Capture to Markdown proof accounting.

This verifier keeps the product-facing proof lanes in one machine-readable
bundle so the Capture overlay/palette proof is accounted for beside the other
operator-requested Capture to Markdown proofs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "chaseos.capture_markdown.proof_accounting.v1"
DEFAULT_OUTPUT_DIR = Path("07_LOGS/Visual-QA/2026-05-31-capture-markdown-proof-accounting")

PROOF_LANES: tuple[dict[str, str], ...] = (
    {
        "id": "capture_overlay_palette",
        "label": "Capture overlay/palette",
        "path": "07_LOGS/Visual-QA/2026-05-29-capture-markdown-palette-proof/capture-palette-proof-summary.json",
        "expected": "Palette source option, overlay readiness, frontend open/close, action buttons, styling, existing source-action dispatch, no Markdown write on open, no new capture authority.",
    },
    {
        "id": "display_region_capture",
        "label": "Display-region capture",
        "path": "07_LOGS/Visual-QA/2026-05-29-capture-markdown-display-region-proof/display-region-proof-summary.json",
        "expected": "Drag-selected display region can be captured and converted through the Capture to Markdown path.",
    },
    {
        "id": "operating_system_wide_hotkeys",
        "label": "Operating-system-wide hotkeys",
        "path": "07_LOGS/Visual-QA/2026-05-29-capture-markdown-global-hotkey-proof/global-hotkey-proof-summary.json",
        "expected": "Configured global hotkey registration is available outside the Studio-window shortcut scope.",
    },
    {
        "id": "browser_extension_capture",
        "label": "Browser extension capture",
        "path": "07_LOGS/Visual-QA/2026-05-29-capture-markdown-browser-extension-proof/browser-extension-proof-summary.json",
        "expected": "ChaseOS browser extension artifact import path is enabled, guarded, and converts the selected artifact to Markdown input.",
    },
    {
        "id": "discord_command_capture",
        "label": "Discord command capture",
        "path": "07_LOGS/Visual-QA/2026-05-29-capture-markdown-live-discord-command-proof/live-discord-command-proof-summary.json",
        "expected": "Discord-origin command capture through ChaseOS Agent Bus ingress is available without direct Discord token, webhook, or event-listener reads.",
    },
    {
        "id": "retention_controls",
        "label": "Attachment deletion/retention controls",
        "path": "07_LOGS/Visual-QA/2026-05-29-capture-markdown-attachment-retention-proof/attachment-retention-proof-summary.json",
        "expected": "Captured attachments expose retention/deletion decision state and guarded cleanup for copied quarantine-local attachments.",
    },
    {
        "id": "stronger_image_text_extraction",
        "label": "Stronger image text extraction",
        "path": "07_LOGS/Visual-QA/2026-05-29-capture-markdown-windows-photo-text-proof/windows-photo-text-proof-summary.json",
        "expected": "Windows Media Optical Character Recognition local engine extracts text from a photo/image proof without a cloud provider call.",
    },
)


def build_proof_accounting(
    vault_root: str | Path,
    *,
    output_dir: str | Path | None = None,
    generated_at: str | None = None,
    write: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    timestamp = generated_at or _now_utc()
    lanes = [_lane_status(vault, lane) for lane in PROOF_LANES]
    missing = [lane["id"] for lane in lanes if not lane["exists"]]
    not_ok = [lane["id"] for lane in lanes if lane["exists"] and lane.get("ok") is not True]
    palette_lane = next((lane for lane in lanes if lane["id"] == "capture_overlay_palette"), {})
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "ok": not missing and not not_ok,
        "status": "complete" if not missing and not not_ok else "incomplete",
        "lane_count": len(lanes),
        "missing_lanes": missing,
        "not_ok_lanes": not_ok,
        "palette_accounted_alongside_other_lanes": bool(
            palette_lane.get("ok") is True and len(lanes) == len(PROOF_LANES)
        ),
        "lanes": lanes,
        "boundaries": {
            "feature_code_changed": False,
            "provider_call_performed": False,
            "discord_application_programming_interface_call_performed": False,
            "browser_profile_read_performed": False,
            "canonical_promotion_performed": False,
        },
    }
    result["proof_accounting_digest_sha256"] = _stable_digest(result)
    if write:
        destination = vault / (Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR)
        destination.mkdir(parents=True, exist_ok=True)
        summary_path = destination / "proof-accounting-summary.json"
        markdown_path = destination / "proof-accounting-summary.md"
        summary_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path.write_text(_markdown_summary(result), encoding="utf-8")
        result["summary_path"] = str(summary_path.relative_to(vault))
        result["markdown_path"] = str(markdown_path.relative_to(vault))
        result["proof_accounting_digest_sha256"] = _stable_digest(result)
        summary_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path.write_text(_markdown_summary(result), encoding="utf-8")
    return result


def _lane_status(vault: Path, lane: dict[str, str]) -> dict[str, Any]:
    relative = Path(lane["path"])
    path = vault / relative
    exists = path.exists() and path.is_file()
    payload: dict[str, Any] = {}
    errors: list[str] = []
    if exists:
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                payload = loaded
            else:
                errors.append("proof_summary_must_be_object")
        except json.JSONDecodeError:
            errors.append("proof_summary_json_invalid")
    return {
        "id": lane["id"],
        "label": lane["label"],
        "proof_path": lane["path"],
        "exists": exists,
        "ok": payload.get("ok") if payload else None,
        "status": payload.get("status", "") if payload else "",
        "proof_type": payload.get("proof_type", "") if payload else "",
        "capture_method": payload.get("capture_method", "") if payload else "",
        "expected": lane["expected"],
        "sha256": _sha256_file(path) if exists else "",
        "errors": errors,
        "palette_details": _palette_details(payload) if lane["id"] == "capture_overlay_palette" else {},
    }


def _palette_details(payload: dict[str, Any]) -> dict[str, Any]:
    readiness = payload.get("readiness") if isinstance(payload.get("readiness"), dict) else {}
    authority = payload.get("authority") if isinstance(payload.get("authority"), dict) else {}
    frontend = payload.get("frontend_wiring") if isinstance(payload.get("frontend_wiring"), dict) else {}
    return {
        "palette_option_available": bool(payload.get("palette_option_available")),
        "palette_action": str(payload.get("palette_action") or ""),
        "capture_palette_overlay_ready": bool(readiness.get("capture_palette_overlay_ready")),
        "capture_palette_overlay_blocked": bool(readiness.get("capture_palette_overlay_blocked")),
        "adds_new_capture_authority": bool(authority.get("adds_new_capture_authority")),
        "writes_markdown_on_palette_open": bool(authority.get("writes_markdown_on_palette_open")),
        "open_capture_palette_function": bool(frontend.get("open_capture_palette_function")),
        "close_capture_palette_function": bool(frontend.get("close_capture_palette_function")),
        "source_action_dispatch_function": bool(frontend.get("source_action_dispatch_function")),
        "palette_button": bool(frontend.get("palette_button")),
        "palette_action_buttons": bool(frontend.get("palette_action_buttons")),
        "palette_css": bool(frontend.get("palette_css")),
        "palette_action_css": bool(frontend.get("palette_action_css")),
        "required_actions_present": frontend.get("required_actions_present", {}),
    }


def _markdown_summary(result: dict[str, Any]) -> str:
    lane_rows = "\n".join(
        f"| {lane['label']} | `{lane['proof_path']}` | `{lane.get('ok')}` | `{lane.get('sha256')}` |"
        for lane in result["lanes"]
    )
    palette = next(lane for lane in result["lanes"] if lane["id"] == "capture_overlay_palette")
    details = palette["palette_details"]
    return f"""# Capture to Markdown Proof Accounting

Generated: {result['generated_at_utc']}
Status: {result['status'].upper()}

## Proof Lanes

| Lane | Proof path | ok | SHA-256 |
|------|------------|----|---------|
{lane_rows}

## Capture Overlay/Palette Details

- Palette option available: `{details.get('palette_option_available')}`
- Palette action: `{details.get('palette_action')}`
- Overlay ready: `{details.get('capture_palette_overlay_ready')}`
- Overlay blocked: `{details.get('capture_palette_overlay_blocked')}`
- Adds new capture authority: `{details.get('adds_new_capture_authority')}`
- Writes Markdown on open: `{details.get('writes_markdown_on_palette_open')}`
- Frontend open function: `{details.get('open_capture_palette_function')}`
- Frontend close function: `{details.get('close_capture_palette_function')}`
- Source-action dispatch function: `{details.get('source_action_dispatch_function')}`
- Palette button: `{details.get('palette_button')}`
- Palette action buttons: `{details.get('palette_action_buttons')}`
- Palette styling: `{details.get('palette_css')}`
- Palette action styling: `{details.get('palette_action_css')}`

## Boundaries

- Feature code changed: `{result['boundaries']['feature_code_changed']}`
- Provider call performed: `{result['boundaries']['provider_call_performed']}`
- Discord application programming interface call performed: `{result['boundaries']['discord_application_programming_interface_call_performed']}`
- Browser profile read performed: `{result['boundaries']['browser_profile_read_performed']}`
- Canonical promotion performed: `{result['boundaries']['canonical_promotion_performed']}`
"""


def _stable_digest(payload: dict[str, Any]) -> str:
    copy = dict(payload)
    copy.pop("proof_accounting_digest_sha256", None)
    body = json.dumps(copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify Capture to Markdown proof accounting.")
    parser.add_argument("--vault-root", default=".", help="ChaseOS vault/repository root.")
    parser.add_argument("--output-dir", default="", help="Output directory for written summaries.")
    parser.add_argument("--write", action="store_true", help="Write JSON and Markdown summaries.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_proof_accounting(
        args.vault_root,
        output_dir=args.output_dir or None,
        write=args.write,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result["status"])
        if result.get("summary_path"):
            print(result["summary_path"])
        if result.get("markdown_path"):
            print(result["markdown_path"])
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
