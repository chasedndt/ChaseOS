"""Controlled live proof for screen image Capture to Markdown conversion."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from runtime.capture.visual_capture.local_image_text_engine import (
    extract_text_from_pixel_image,
    local_image_text_engine_command,
    render_pixel_text_png,
)
from runtime.studio.capture_collector_settings import (
    ScreenCaptureImage,
    capture_collector_settings_path,
    capture_current_screen_for_markdown,
    save_capture_collector_settings,
)
from runtime.studio.capture_to_markdown_panel import (
    preview_capture_to_markdown,
    save_capture_to_markdown,
)


MODEL_VERSION = "studio.capture_markdown.image_to_markdown_live_proof.v1"
DEFAULT_DESCRIPTOR = "capture-markdown-image-to-markdown-live-proof"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Studio-Graph-Views")
PROOF_LINES = (
    "CHASEOS CAPTURE PROOF",
    "IMAGE TO MARKDOWN",
    "TEXT 2026 05 28",
)
PROOF_TEXT = "\n".join(PROOF_LINES)

SCALE = 6
MARGIN = 18
CHAR_SPACING = 6
LINE_SPACING = 18


def run_capture_markdown_image_to_markdown_live_proof(
    *,
    vault_root: str | Path,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    evidence_slug: str | None = None,
    run_id: str | None = None,
    save_markdown: bool = True,
    write_evidence: bool = True,
) -> dict[str, Any]:
    """Capture a controlled proof image, extract its text, and save Markdown."""

    vault = Path(vault_root).resolve()
    slug = _safe_slug(evidence_slug or f"{_date_slug()}-{DEFAULT_DESCRIPTOR}")
    capture_run_id = _safe_slug(run_id or slug)[:48].strip("._-") or DEFAULT_DESCRIPTOR
    settings_path = capture_collector_settings_path(vault)
    original_settings_text = _read_text_if_exists(settings_path)
    original_settings_existed = original_settings_text is not None
    settings_restored = False
    image_bytes, width, height = render_proof_image(PROOF_LINES)
    expected_image_sha256 = hashlib.sha256(image_bytes).hexdigest()
    capture: dict[str, Any] = {}
    preview: dict[str, Any] = {}
    saved: dict[str, Any] = {}

    try:
        save_capture_collector_settings(vault, {"screen_capture_enabled": True})
        capture = capture_current_screen_for_markdown(
            vault,
            {
                "operator_confirmed": True,
                "run_id": capture_run_id,
                "title": "Image to Markdown Live Proof",
            },
            image_provider=lambda: ScreenCaptureImage(
                png_bytes=image_bytes,
                width=width,
                height=height,
                source="codex_controlled_pixel_text_fixture",
            ),
        )
        if capture.get("ok"):
            markdown_payload = {
                "source_mode": "screenshot_text_extraction",
                "profile": "research_note",
                "title": "Image to Markdown Live Proof",
                "file_path": capture.get("file_path") or "",
                "source_url": "chaseos://controlled-proof/image-to-markdown",
                "user_intent": "controlled live proof that screen image capture becomes Markdown",
                "structured_notes": "The captured proof image contains high-contrast pixel text.",
                "local_ocr_command": json.dumps(local_image_text_engine_command()),
                "local_ocr_timeout_seconds": 20,
            }
            preview = preview_capture_to_markdown(vault, markdown_payload)
            if save_markdown:
                saved = save_capture_to_markdown(vault, markdown_payload)
    finally:
        settings_restored = _restore_settings_file(
            settings_path,
            original_settings_text,
            original_settings_existed=original_settings_existed,
        )

    verification = _verify_image_to_markdown_live_proof(
        vault=vault,
        capture=capture,
        preview=preview,
        saved=saved,
        save_markdown=save_markdown,
        settings_restored=settings_restored,
        expected_image_sha256=expected_image_sha256,
    )
    proof: dict[str, Any] = {
        "ok": verification["ok"],
        "status": (
            "capture_markdown_image_to_markdown_live_proof_verified"
            if verification["ok"]
            else "capture_markdown_image_to_markdown_live_proof_failed"
        ),
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "run_id": capture_run_id,
        "proof_text": PROOF_TEXT,
        "image": {
            "width": width,
            "height": height,
            "sha256": expected_image_sha256,
            "rendering": "repo_local_high_contrast_pixel_font",
        },
        "authority": {
            "settings_temporarily_enabled": True,
            "settings_restored_after_run": settings_restored,
            "operator_click_simulated_for_controlled_proof": True,
            "uses_screen_capture_collector": True,
            "captures_personal_ambient_screen": False,
            "uses_controlled_image_provider": True,
            "uses_local_image_text_command": True,
            "calls_cloud_optical_character_recognition": False,
            "calls_model_provider": False,
            "reads_browser_profile": False,
            "reads_clipboard": False,
            "calls_discord": False,
            "save_markdown_requested": save_markdown,
            "canonical_mutation_allowed": False,
            "graph_index_mutation_allowed": False,
        },
        "capture": _summarize_capture(capture),
        "preview": _summarize_preview(preview),
        "save": _summarize_save(saved),
        "verification": verification,
        "evidence": {},
    }
    if write_evidence:
        proof["evidence"] = write_capture_markdown_image_to_markdown_live_proof_evidence(
            vault,
            proof,
            evidence_root=evidence_root,
            evidence_slug=slug,
        )
    return proof


def render_proof_image(lines: tuple[str, ...] = PROOF_LINES) -> tuple[bytes, int, int]:
    return render_pixel_text_png(
        lines,
        scale=SCALE,
        margin=MARGIN,
        char_spacing=CHAR_SPACING,
        line_spacing=LINE_SPACING,
        foreground=(0, 0, 0),
        background=(255, 255, 255),
    )


def decode_proof_image_text(file_path: str | Path) -> str:
    return extract_text_from_pixel_image(file_path)


def write_capture_markdown_image_to_markdown_live_proof_evidence(
    vault_root: str | Path,
    proof: dict[str, Any],
    *,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    evidence_slug: str,
) -> dict[str, str]:
    vault = Path(vault_root).resolve()
    root = Path(evidence_root)
    root = root if root.is_absolute() else vault / root
    root.mkdir(parents=True, exist_ok=True)
    safe_slug = _safe_slug(evidence_slug)
    json_path = root / f"{safe_slug}.json"
    markdown_path = root / f"{safe_slug}.md"
    json_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    markdown_path.write_text(_proof_markdown(proof), encoding="utf-8")
    return {
        "json_path": _rel(json_path, vault),
        "markdown_path": _rel(markdown_path, vault),
    }


def _verify_image_to_markdown_live_proof(
    *,
    vault: Path,
    capture: dict[str, Any],
    preview: dict[str, Any],
    saved: dict[str, Any],
    save_markdown: bool,
    settings_restored: bool,
    expected_image_sha256: str,
) -> dict[str, Any]:
    screenshot_path = _resolve_optional_path(vault, capture.get("file_path"))
    audit_path = _resolve_optional_path(vault, capture.get("audit_path"))
    saved_markdown_path = _resolve_optional_path(vault, saved.get("content_path"))
    saved_packet_path = _resolve_optional_path(vault, saved.get("visual_capture_packet_path"))
    preview_data = preview if "markdown" in preview else preview.get("data", {})
    preview_markdown = str(preview_data.get("markdown") or "")
    saved_markdown = _read_text_if_exists(saved_markdown_path) if saved_markdown_path else ""
    extracted_text_present = all(line in preview_markdown for line in PROOF_LINES)
    saved_text_present = all(line in saved_markdown for line in PROOF_LINES)
    screenshot_sha256 = _file_sha256(screenshot_path) if screenshot_path and screenshot_path.is_file() else ""

    checks = {
        "screen_collector_capture_ok": bool(capture.get("ok")),
        "screen_collector_ready_for_markdown": capture.get("status") == "screen_capture_ready_for_markdown",
        "screen_collector_source_mode_screenshot_attachment": capture.get("source_mode") == "screenshot_attachment",
        "screen_collector_writes_image_evidence": capture.get("write_performed") is True,
        "screen_collector_does_not_write_markdown": capture.get("writes_raw_quarantine_markdown") is False,
        "screen_collector_next_action_preview_or_save": capture.get("next_action") == "preview_or_save_capture_to_markdown",
        "captured_image_exists": bool(screenshot_path and screenshot_path.is_file()),
        "captured_image_sha256_matches_rendered_fixture": screenshot_sha256 == expected_image_sha256,
        "capture_audit_exists": bool(audit_path and audit_path.is_file()),
        "preview_ok": bool(preview.get("ok")),
        "preview_write_free": preview.get("write_performed") is False,
        "preview_capture_method_image_text_extraction": (
            ((preview.get("packet") or {}).get("capture_method") if isinstance(preview.get("packet"), dict) else "")
            == "screenshot_local_text_extraction"
        ),
        "preview_contains_extracted_image_text": extracted_text_present,
        "preview_marks_local_image_text_extraction": "local_optical_character_recognition_performed" in preview_markdown,
        "settings_restored_after_run": settings_restored,
    }
    if save_markdown:
        checks.update(
            {
                "save_ok": bool(saved.get("ok")),
                "save_markdown_written": saved.get("write_performed") is True,
                "saved_markdown_file_exists": bool(saved_markdown_path and saved_markdown_path.is_file()),
                "saved_visual_capture_packet_exists": bool(saved_packet_path and saved_packet_path.is_file()),
                "saved_markdown_contains_extracted_image_text": saved_text_present,
                "saved_markdown_marks_text_extracted": "Extraction status: `text_extracted`" in saved_markdown,
            }
        )
    else:
        checks["save_markdown_not_requested"] = not saved

    return {
        "ok": all(checks.values()),
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "artifact_paths": {
            "captured_image": _rel(screenshot_path, vault) if screenshot_path else "",
            "capture_audit": _rel(audit_path, vault) if audit_path else "",
            "saved_markdown": _rel(saved_markdown_path, vault) if saved_markdown_path else "",
            "saved_packet": _rel(saved_packet_path, vault) if saved_packet_path else "",
        },
    }


def _summarize_capture(capture: dict[str, Any]) -> dict[str, Any]:
    screenshot = capture.get("screenshot") if isinstance(capture.get("screenshot"), dict) else {}
    return {
        "ok": bool(capture.get("ok")),
        "status": str(capture.get("status") or ""),
        "source_mode": str(capture.get("source_mode") or ""),
        "file_path": str(capture.get("file_path") or ""),
        "audit_path": str(capture.get("audit_relative_path") or capture.get("audit_path") or ""),
        "image_sha256": str(screenshot.get("sha256") or ""),
        "width": int(screenshot.get("width") or 0),
        "height": int(screenshot.get("height") or 0),
        "write_performed": bool(capture.get("write_performed")),
        "writes_raw_quarantine_markdown": bool(capture.get("writes_raw_quarantine_markdown")),
        "blockers": list(capture.get("blockers") or []),
    }


def _summarize_preview(preview: dict[str, Any]) -> dict[str, Any]:
    packet = preview.get("packet") if isinstance(preview.get("packet"), dict) else {}
    markdown = str(preview.get("markdown") or "")
    return {
        "ok": bool(preview.get("ok")),
        "status": str(preview.get("status") or ""),
        "write_performed": bool(preview.get("write_performed")),
        "capture_method": str(packet.get("capture_method") or ""),
        "contains_extracted_text": all(line in markdown for line in PROOF_LINES),
        "markdown_char_count": len(markdown),
    }


def _summarize_save(saved: dict[str, Any]) -> dict[str, Any]:
    return {
        "requested": bool(saved),
        "ok": bool(saved.get("ok")) if saved else False,
        "status": str(saved.get("status") or ""),
        "write_performed": bool(saved.get("write_performed")) if saved else False,
        "content_path": str(saved.get("content_path") or ""),
        "visual_capture_packet_path": str(saved.get("visual_capture_packet_path") or ""),
        "is_duplicate": bool(saved.get("is_duplicate")) if saved else False,
        "blockers": list(saved.get("blockers") or []) if saved else [],
    }


def _proof_markdown(proof: dict[str, Any]) -> str:
    verification = proof.get("verification") if isinstance(proof.get("verification"), dict) else {}
    checks = verification.get("checks") if isinstance(verification.get("checks"), dict) else {}
    artifacts = verification.get("artifact_paths") if isinstance(verification.get("artifact_paths"), dict) else {}
    lines = [
        "# Capture to Markdown Image to Markdown Live Proof",
        "",
        f"- Status: `{proof.get('status')}`",
        f"- Run: `{proof.get('run_id')}`",
        f"- Captured image: `{artifacts.get('captured_image', '')}`",
        f"- Capture audit: `{artifacts.get('capture_audit', '')}`",
        f"- Saved Markdown: `{artifacts.get('saved_markdown', '')}`",
        f"- Saved packet: `{artifacts.get('saved_packet', '')}`",
        "- Cloud optical character recognition: `not called`",
        "- Model provider calls: `not called`",
        "",
        "## Extracted Text",
        "",
        "```text",
        str(proof.get("proof_text") or ""),
        "```",
        "",
        "## Verification Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{str(value).lower()}`" for name, value in checks.items())
    return "\n".join(lines) + "\n"


def _restore_settings_file(
    settings_path: Path,
    original_settings_text: str | None,
    *,
    original_settings_existed: bool,
) -> bool:
    try:
        if original_settings_existed:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(original_settings_text or "", encoding="utf-8")
        elif settings_path.exists():
            settings_path.unlink()
    except OSError:
        return False
    return _read_text_if_exists(settings_path) == original_settings_text


def _resolve_optional_path(vault: Path, value: Any) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = vault / path
    return path.resolve()


def _file_sha256(path: Path | None) -> str:
    if not path or not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_text_if_exists(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _rel(path: Path | None, vault: Path) -> str:
    if not path:
        return ""
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _safe_slug(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value)
    safe = "-".join(part for part in safe.split("-") if part)
    return safe.strip("._-")[:120] or DEFAULT_DESCRIPTOR


def _date_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--engine":
        if len(args) < 2:
            raise SystemExit("usage: capture_markdown_image_to_markdown_live_proof.py --engine <image-path>")
        print(decode_proof_image_text(args[1]))
        return 0

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--evidence-slug", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--no-save-markdown", action="store_true")
    parser.add_argument("--no-write-evidence", action="store_true")
    parsed = parser.parse_args(args)
    proof = run_capture_markdown_image_to_markdown_live_proof(
        vault_root=parsed.vault_root,
        evidence_slug=parsed.evidence_slug,
        run_id=parsed.run_id,
        save_markdown=not parsed.no_save_markdown,
        write_evidence=not parsed.no_write_evidence,
    )
    print(json.dumps(proof, indent=2, sort_keys=True, default=str))
    return 0 if proof.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
