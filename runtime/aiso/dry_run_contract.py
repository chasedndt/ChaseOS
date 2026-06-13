from __future__ import annotations

import html
import json
import re
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from runtime.aiso.recent_artifact_locator import locate_recent_artifacts

TEST_COMMANDS = [
    "PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_recent_artifact_locator.py -q",
    "PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_aiso_dry_run_contract.py -q",
    "PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_aiso_result_fallbacks.py -q",
]


def _parse_now(now: str | None) -> datetime:
    if not now:
        return datetime.now(timezone.utc)
    text = now.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _slug(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return normalized or "artifact"


def _authority(*, write_performed: bool) -> dict[str, bool]:
    return {
        "write_performed": write_performed,
        "original_mutation": False,
        "original_mutation_performed": False,
        "provider_call": False,
        "provider_call_performed": False,
        "browser_submit": False,
        "browser_submit_performed": False,
        "email_send": False,
        "email_send_performed": False,
        "credential_access": False,
        "credential_access_performed": False,
        "canonical_promotion": False,
        "canonical_promotion_performed": False,
        "browser_opened": False,
        "external_upload": False,
        "approval_consumed": False,
    }


def _workflow_from_intent(request_text: str) -> dict[str, Any]:
    lowered = request_text.lower()
    university_tokens = ("university", "class", "course", "lecture", "assignment", "submission", "portal", "email")
    task_type = "university_submission_prepare" if any(token in lowered for token in university_tokens) else "university_submission_prepare"
    return {
        "workflow_id": "university_submission_operator",
        "task_type": task_type,
        "mode": "prepare_and_stage",
        "posture": "prepare-and-stage-only",
        "media_derived_text_is_instruction": False,
        "intent_source": "operator_request_text",
        "live_delivery_requested": any(token in lowered for token in ("send", "submit", "upload")),
        "live_delivery_authorized": False,
    }


def _build_metadata_stub(candidate: dict[str, Any], *, now_dt: datetime) -> dict[str, Any]:
    return {
        "status": "deterministic_local_fixture_metadata",
        "provider_call": False,
        "provider_call_performed": False,
        "source": "locator_file_stat_metadata_only",
        "artifact": {
            "relative_path": candidate["relative_path"],
            "filename": candidate["filename"],
            "suffix": candidate["suffix"],
            "size_bytes": candidate["size_bytes"],
            "modified_at_utc": candidate["modified_at_utc"],
        },
        "transcript": {"status": "unavailable_without_provider_or_local_transcriber", "invented": False},
        "ocr": {"status": "unavailable_without_provider_or_local_ocr", "invented": False},
        "keyframes": {"status": "not_sampled_in_first_bounded_dry_run", "invented": False},
        "generated_at_utc": now_dt.isoformat().replace("+00:00", "Z"),
    }


def _build_rename_package_proposal(candidate: dict[str, Any], *, now_dt: datetime) -> dict[str, Any]:
    date = now_dt.date().isoformat()
    suffix = candidate.get("suffix") or Path(candidate["filename"]).suffix
    staged_base = f"university-submission-{date}"
    staged_filename = f"{staged_base}{suffix}"
    original_filename = candidate["filename"]
    original_path = candidate["relative_path"]
    approval_message = {
        "action": "rename_original_file",
        "requires_operator_approval": True,
        "old_filename": original_filename,
        "new_filename": staged_filename,
        "old_path": original_path,
        "new_path": str(Path(original_path).with_name(staged_filename)).replace("\\", "/"),
        "message": (
            "Approval required before renaming the original file: "
            f"old filename '{original_filename}' -> new filename '{staged_filename}'."
        ),
    }
    return {
        "status": "proposal_only",
        "original_path": original_path,
        "original_filename": original_filename,
        "original_size_bytes": candidate["size_bytes"],
        "original_modified_at_utc": candidate["modified_at_utc"],
        "staged_filename": staged_filename,
        "staged_media_path": f"staging/{staged_filename}",
        "staged_package_name": f"{staged_base}.zip",
        "staged_package_path": f"staging/{staged_base}.zip",
        "manifest_path": f"staging/{staged_base}-manifest.json",
        "approval_message": approval_message,
        "checksum_plan": {
            "algorithm": "sha256",
            "status": "planned_not_performed_in_first_dry_run",
            "reason": "avoid_media_content_read_in_bounded_fixture_proof",
        },
        "original_mutation": False,
        "original_mutation_performed": False,
        "package_write_performed": False,
    }


def _rel(path: Path, vault_root: Path) -> str:
    return path.resolve().relative_to(vault_root.resolve()).as_posix()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_html(
    *,
    workflow: dict[str, Any],
    candidate: dict[str, Any],
    proposal: dict[str, Any],
    fallbacks: list[dict[str, Any]] | None = None,
) -> str:
    fallback_rows = ""
    for fallback in fallbacks or []:
        fallback_rows += (
            "<tr>"
            f"<td>{html.escape(fallback['id'])}</td>"
            f"<td>{html.escape(str(fallback['status']))}</td>"
            f"<td>{html.escape(str(fallback.get('blocked_reason', 'dry-run-local')))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>AISO Bounded Dry-Run Proof</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; background: #101827; color: #f8fafc; }}
.card {{ border: 1px solid #3b82f6; border-radius: 12px; padding: 1rem; margin: 1rem 0; background: #172033; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border-bottom: 1px solid #334155; padding: .5rem; text-align: left; }}
.badge {{ color: #bbf7d0; }}
.blocked {{ color: #fecaca; }}
</style>
</head>
<body>
<h1>AISO bounded dry-run proof</h1>
<p class=\"badge\">Mode: {html.escape(workflow['mode'])}; live send/submit/write-to-original blocked.</p>
<div class=\"card\"><h2>Selected fixture artifact</h2><p>{html.escape(candidate['relative_path'])}</p></div>
<div class=\"card\"><h2>Staged proposal only</h2><p>{html.escape(proposal['staged_filename'])} → {html.escape(proposal['staged_package_path'])}</p></div>
<div class=\"card blocked\"><h2>Rename approval required</h2><p>{html.escape(proposal['approval_message']['message'])}</p><p><b>Old:</b> {html.escape(proposal['approval_message']['old_filename'])}<br><b>New:</b> {html.escape(proposal['approval_message']['new_filename'])}</p></div>
<div class=\"card\"><h2>Fallback result paths</h2><table><tr><th>ID</th><th>Status</th><th>Reason</th></tr>{fallback_rows}</table></div>
<div class=\"card blocked\"><h2>Authority envelope</h2><p>provider_call=false; email_send=false; browser_submit=false; credential_access=false; original_mutation=false; canonical_promotion=false.</p></div>
</body>
</html>
"""


def _render_svg(*, workflow: dict[str, Any], proposal: dict[str, Any]) -> str:
    title = html.escape("AISO dry-run proof packet")
    mode = html.escape(workflow["mode"])
    staged = html.escape(proposal["staged_filename"])
    return f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1200\" height=\"720\" viewBox=\"0 0 1200 720\">
  <rect width=\"1200\" height=\"720\" fill=\"#0f172a\"/>
  <rect x=\"60\" y=\"60\" width=\"1080\" height=\"600\" rx=\"32\" fill=\"#172033\" stroke=\"#60a5fa\" stroke-width=\"4\"/>
  <text x=\"100\" y=\"140\" fill=\"#f8fafc\" font-family=\"Arial\" font-size=\"52\" font-weight=\"700\">{title}</text>
  <text x=\"100\" y=\"220\" fill=\"#bbf7d0\" font-family=\"Arial\" font-size=\"34\">mode: {mode}</text>
  <text x=\"100\" y=\"290\" fill=\"#dbeafe\" font-family=\"Arial\" font-size=\"30\">staged filename: {staged}</text>
  <text x=\"100\" y=\"380\" fill=\"#fecaca\" font-family=\"Arial\" font-size=\"30\">blocked live paths: email send, portal submit, provider calls, credentials</text>
  <text x=\"100\" y=\"470\" fill=\"#fef3c7\" font-family=\"Arial\" font-size=\"30\">original mutation: false · canonical promotion: false</text>
  <text x=\"100\" y=\"560\" fill=\"#c4b5fd\" font-family=\"Arial\" font-size=\"30\">local proof packet selected for QA recovery</text>
</svg>
"""


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _write_visual_png(path: Path) -> None:
    """Write a deterministic rendered-image proof without browser automation."""

    width, height = 640, 360
    rows: list[bytes] = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            in_card = 32 <= x <= 608 and 32 <= y <= 328
            stripe = 92 <= y <= 126 or 194 <= y <= 228
            if in_card and stripe:
                row.extend((96, 165, 250))
            elif in_card:
                row.extend((23, 32, 51))
            else:
                row.extend((15, 23, 42))
        rows.append(bytes(row))
    raw = b"".join(rows)
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += _png_chunk(b"IDAT", zlib.compress(raw, 9))
    png += _png_chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def _make_previews(
    *,
    vault: Path,
    proof_dir: Path,
    workflow: dict[str, Any],
    candidate: dict[str, Any],
    proposal: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    email_preview = proof_dir / "aiso-email-draft-preview.html"
    email_png = proof_dir / "aiso-email-draft-preview.png"
    portal_preview = proof_dir / "aiso-portal-draft-preview.html"
    portal_png = proof_dir / "aiso-portal-draft-preview.png"
    proof_preview = proof_dir / "aiso-proof-preview.html"
    proof_svg = proof_dir / "aiso-proof-preview.svg"
    proof_png = proof_dir / "aiso-proof-preview.png"

    email_body = (
        "Draft only — no send performed.\n\n"
        f"Prepared attachment plan: {proposal['staged_package_path']}\n"
        "Recipient remains operator-supplied; credentials were not read."
    )
    portal_actions = [
        "Open portal manually after approval",
        "Attach staged package preview only after approval",
        "Submit button remains blocked in this dry run",
    ]
    fallbacks = [
        {
            "id": "local_proof_packet",
            "status": "available",
            "selected": True,
            "preview_path": _rel(proof_preview, vault),
            "visual_image_path": _rel(proof_svg, vault),
            "visual_screenshot_path": _rel(proof_png, vault),
        },
        {
            "id": "email_draft_preview",
            "status": "preview_created_no_send",
            "selected": False,
            "subject": "Draft: university submission package ready for review",
            "body": email_body,
            "attachment_plan": {"staged_package_path": proposal["staged_package_path"]},
            "preview_path": _rel(email_preview, vault),
            "visual_screenshot_path": _rel(email_png, vault),
            "email_send": False,
            "email_send_performed": False,
            "credential_access": False,
            "credential_access_performed": False,
            "blocked_reason": "email_adapter_and_credentials_not_authorized",
            "fallback_to": "local_proof_packet",
        },
        {
            "id": "browser_portal_draft_preview",
            "status": "preview_created_no_submit",
            "selected": False,
            "portal_action_plan": portal_actions,
            "preview_path": _rel(portal_preview, vault),
            "visual_screenshot_path": _rel(portal_png, vault),
            "browser_opened": False,
            "browser_submit": False,
            "browser_submit_performed": False,
            "blocked_reason": "browser_session_and_portal_submission_not_authorized",
            "fallback_to": "local_proof_packet",
        },
    ]

    _write_text(email_preview, f"<html><body><h1>Email draft preview — no send</h1><pre>{html.escape(email_body)}</pre></body></html>\n")
    _write_visual_png(email_png)
    _write_text(portal_preview, "<html><body><h1>Portal draft preview — no submit</h1><ol>" + "".join(f"<li>{html.escape(step)}</li>" for step in portal_actions) + "</ol></body></html>\n")
    _write_visual_png(portal_png)
    _write_text(proof_preview, _render_html(workflow=workflow, candidate=candidate, proposal=proposal, fallbacks=fallbacks))
    _write_text(proof_svg, _render_svg(workflow=workflow, proposal=proposal))
    _write_visual_png(proof_png)
    return fallbacks, {
        "proof_packet_html": _rel(proof_preview, vault),
        "proof_packet_svg": _rel(proof_svg, vault),
        "proof_packet_png": _rel(proof_png, vault),
        "email_preview_html": _rel(email_preview, vault),
        "email_preview_png": _rel(email_png, vault),
        "portal_preview_html": _rel(portal_preview, vault),
        "portal_preview_png": _rel(portal_png, vault),
    }


def run_aiso_submission_dry_run(
    *,
    vault_root: str | Path,
    request_text: str,
    declared_roots: Iterable[str] | None = None,
    proof_root: str = "07_LOGS/Workflow-Proofs/aiso-dry-run-proof",
    now: str | None = None,
) -> dict[str, Any]:
    """Build a bounded local AISO prepare-and-stage proof packet.

    This function intentionally performs no provider calls, browser submission,
    email send, credential access, original mutation, external upload, approval
    consumption, or canonical promotion. The only writes are dry-run proof files
    under the caller-supplied proof root.
    """

    vault = Path(vault_root).resolve()
    now_dt = _parse_now(now)
    workflow = _workflow_from_intent(request_text)
    locator = locate_recent_artifacts(vault_root=vault, roots=declared_roots, limit=10)
    if not locator["artifacts"]:
        return {
            "ok": False,
            "status": "blocked_no_candidate",
            "workflow": workflow,
            "locator": locator,
            "authority": _authority(write_performed=False),
            "approval_blocking": {
                "proof_packet": {"status": "blocked", "reason": "no_declared_fixture_candidate"},
                "send_or_submit": {"status": "approval_required", "blocked_before_side_effects": True},
            },
        }

    candidate = locator["artifacts"][0]
    metadata_stub = _build_metadata_stub(candidate, now_dt=now_dt)
    proposal = _build_rename_package_proposal(candidate, now_dt=now_dt)
    proof_dir = (vault / proof_root).resolve()
    if not proof_dir.is_relative_to(vault):
        return {
            "ok": False,
            "status": "blocked_proof_root_outside_vault",
            "workflow": workflow,
            "locator": locator,
            "authority": _authority(write_performed=False),
        }

    fallbacks, visual_artifacts = _make_previews(
        vault=vault,
        proof_dir=proof_dir,
        workflow=workflow,
        candidate=candidate,
        proposal=proposal,
    )
    manifest_path = proof_dir / "aiso-proof-manifest.json"
    audit_path = proof_dir / "aiso-audit-envelope.json"
    authority = _authority(write_performed=True)
    blocked_live_paths = {
        "email_send": "approval_required_and_credentials_not_authorized",
        "browser_portal_submit": "approval_required_and_browser_session_not_authorized",
        "provider_call": "not_authorized_for_first_dry_run",
        "credential_access": "not_authorized_for_first_dry_run",
        "original_mutation": "not_authorized_for_first_dry_run",
        "canonical_promotion": "not_authorized_for_first_dry_run",
    }
    audit = {
        "workflow": workflow,
        "authority": authority,
        "selected_fallback_path": "local_proof_packet",
        "blocked_live_paths": blocked_live_paths,
        "test_commands": TEST_COMMANDS,
        "source_fixture_ids": ["runtime/aiso/test_aiso_result_fallbacks.py"],
        "visual_proof_artifacts": visual_artifacts,
        "remaining_blockers": [
            "live email send requires separate approval and credential boundary",
            "portal/browser submission requires separate approval and portal-session boundary",
            "provider-backed transcript/OCR/visual understanding remains unavailable in this dry run",
        ],
    }
    manifest = {
        "status": "dry_run_local_proof_packet",
        "workflow": workflow,
        "selected_candidate": candidate,
        "metadata_stub": metadata_stub,
        "rename_package_proposal": proposal,
        "result_fallbacks": fallbacks,
        "audit_envelope_path": _rel(audit_path, vault),
        "authority": authority,
    }
    _write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _write_text(audit_path, json.dumps(audit, indent=2, sort_keys=True) + "\n")

    proof_packet = {
        "status": "created",
        "manifest_path": _rel(manifest_path, vault),
        "audit_envelope_path": _rel(audit_path, vault),
        "visual_preview_path": fallbacks[0]["preview_path"],
        "visual_image_path": fallbacks[0]["visual_image_path"],
        "visual_screenshot_path": fallbacks[0]["visual_screenshot_path"],
    }
    return {
        "ok": True,
        "status": "approval_needed_before_live_actions",
        "workflow": workflow,
        "locator": locator,
        "selected_candidate": candidate,
        "metadata_stub": metadata_stub,
        "rename_package_proposal": proposal,
        "result_fallbacks": fallbacks,
        "approval_blocking": {
            "send_or_submit": {"status": "approval_required", "blocked_before_side_effects": True},
            "write_or_original_mutation": {"status": "approval_required", "blocked_before_original_side_effects": True},
            "rename_original_file": {
                "status": "approval_required",
                "blocked_before_original_side_effects": True,
                **proposal["approval_message"],
            },
        },
        "proof_packet": proof_packet,
        "audit_envelope": audit,
        "authority": authority,
    }
