"""Read-only intake for supplemental Pass 10B native screenshot evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.operator_surface.browser.image_verifier import analyze_png_nonblank


MODEL_VERSION = "studio.pass10b_native_screenshot_evidence_intake.v1"
SURFACE_ID = "studio_pass10b_native_screenshot_evidence_intake"
NATIVE_DECLARED_SOURCES = {"native-packaged-window", "operator-native-packaged-window"}
ALLOWED_DECLARED_SOURCES = NATIVE_DECLARED_SOURCES | {"browser-static-route", "synthetic-test-fixture", "unknown"}
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "pass10b-native-screenshot-evidence"


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _resolve_inside_vault(vault: Path, path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Pass 10B native screenshot evidence path must stay inside the vault workspace") from exc
    return resolved


def _relative(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_pass10b_native_screenshot_evidence_intake(
    vault_root: str | Path,
    *,
    screenshot_path: str | Path,
    declared_source: str = "unknown",
    min_unique_colors: int = 8,
    max_dominant_ratio: float = 0.995,
) -> dict[str, Any]:
    """Verify a supplied screenshot without treating it as automated packaged QA."""

    vault = _vault_path(vault_root)
    source = declared_source if declared_source in ALLOWED_DECLARED_SOURCES else "unknown"
    screenshot = _resolve_inside_vault(vault, screenshot_path)
    visual = analyze_png_nonblank(
        screenshot,
        min_unique_colors=min_unique_colors,
        max_dominant_ratio=max_dominant_ratio,
    )
    declared_native = source in NATIVE_DECLARED_SOURCES
    visual_ok = bool(visual.get("ok"))
    supplemental_native_evidence_verified = bool(declared_native and visual_ok)
    blockers: list[str] = []
    if source == "unknown":
        blockers.append("Declared screenshot source is unknown.")
    if not declared_native:
        blockers.append("Screenshot is not declared as a native packaged-window capture.")
    if not visual_ok:
        blockers.append(f"Screenshot did not pass nonblank verification: {visual.get('reason')}")

    if supplemental_native_evidence_verified:
        status = "SUPPLEMENTAL_NATIVE_SCREENSHOT_EVIDENCE_VERIFIED"
    elif visual_ok:
        status = "VISUAL_EVIDENCE_NONBLANK_BUT_NOT_NATIVE"
    else:
        status = "BLOCKED_NATIVE_SCREENSHOT_EVIDENCE_INTAKE"

    return {
        "ok": supplemental_native_evidence_verified,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "screenshot": {
            "path": _relative(vault, screenshot),
            "declared_source": source,
            "declared_native_packaged_window": declared_native,
            "visual_verification": visual,
        },
        "readiness": {
            "supplemental_native_screenshot_evidence_verified": supplemental_native_evidence_verified,
            "automated_packaged_visual_qa_complete": False,
            "can_support_manual_review": bool(visual_ok),
            "can_close_pass10b_native_visual_proof": False,
            "next_recommended_pass": (
                "pass10b-native-visual-qa-rerun-after-host-policy-unblock"
                if supplemental_native_evidence_verified
                else "pass10b-native-screenshot-evidence-intake"
            ),
            "blockers": blockers,
        },
        "authority": {
            "launches_packaged_executable": False,
            "captures_native_screenshot": False,
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
            {"name": "screenshot_exists", "ok": bool(visual.get("exists")), "detail": _relative(vault, screenshot)},
            {"name": "screenshot_is_png", "ok": bool(visual.get("png")), "detail": visual.get("reason")},
            {"name": "screenshot_nonblank", "ok": visual_ok, "detail": visual.get("reason")},
            {"name": "declared_native_packaged_window", "ok": declared_native, "detail": source},
            {
                "name": "automated_packaged_visual_qa_complete",
                "ok": False,
                "detail": "manual/supplied evidence intake does not complete automated packaged visual QA",
            },
            {
                "name": "codex_did_not_capture_or_mutate_host",
                "ok": True,
                "detail": "read-only evidence analysis only",
            },
        ],
        "blockers": blockers,
        "unverified": [
            "The command does not prove the screenshot was captured by Codex.",
            "The command does not prove the packaged executable can launch under current host policy.",
            "The command does not complete automated packaged native visual QA.",
        ],
        "next_recommended_pass": (
            "pass10b-native-visual-qa-rerun-after-host-policy-unblock"
            if supplemental_native_evidence_verified
            else "pass10b-native-screenshot-evidence-intake"
        ),
    }


def format_pass10b_native_screenshot_evidence_intake(report: dict[str, Any]) -> str:
    screenshot = report.get("screenshot") or {}
    readiness = report.get("readiness") or {}
    visual = screenshot.get("visual_verification") or {}
    lines = [
        f"Pass 10B native screenshot evidence intake: {report.get('status')}",
        f"  ok: {report.get('ok')}",
        f"  screenshot: {screenshot.get('path')}",
        f"  declared_source: {screenshot.get('declared_source')}",
        f"  screenshot_nonblank: {visual.get('ok')}",
        f"  unique_colors: {visual.get('unique_color_count')}",
        f"  dominant_color_ratio: {visual.get('dominant_color_ratio')}",
        f"  automated_packaged_visual_qa_complete: {readiness.get('automated_packaged_visual_qa_complete')}",
        f"  can_close_pass10b_native_visual_proof: {readiness.get('can_close_pass10b_native_visual_proof')}",
        f"  next: {readiness.get('next_recommended_pass')}",
    ]
    blockers = readiness.get("blockers") or []
    if blockers:
        lines.append(f"  blockers: {', '.join(str(item) for item in blockers)}")
    return "\n".join(lines)


def write_pass10b_native_screenshot_evidence_intake(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write supplemental screenshot evidence without completing automated QA."""

    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    if not root.is_absolute():
        root = vault / root
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Pass 10B native screenshot evidence root must stay inside the vault workspace") from exc

    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-pass10b-native-screenshot-evidence"
    if not slug.endswith(".json"):
        json_name = f"{slug}.json"
    else:
        json_name = slug
        slug = slug[:-5]
    markdown_name = f"{slug}.md"
    json_path = (root / json_name).resolve()
    markdown_path = (root / markdown_name).resolve()
    for candidate in (json_path, markdown_path):
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Pass 10B native screenshot evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)

    payload = {
        "report_type": "pass10b_native_screenshot_evidence_intake",
        "generated_at": _now_utc(),
        "status": report.get("status"),
        "ok": bool(report.get("ok")),
        "surface": report.get("surface"),
        "model_version": report.get("model_version"),
        "screenshot": report.get("screenshot"),
        "readiness": report.get("readiness"),
        "authority": report.get("authority"),
        "checks": report.get("checks"),
        "blockers": report.get("blockers"),
        "unverified": report.get("unverified"),
        "next_recommended_pass": report.get("next_recommended_pass"),
        "authority_note": (
            "This evidence is supplemental and cannot complete automated packaged visual QA. "
            "It does not launch or capture the packaged executable, mutate host policy, sign or allowlist files, "
            "write installer/startup state, execute approvals, call providers/connectors, write Agent Bus tasks, "
            "or mutate canonical state."
        ),
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    screenshot = report.get("screenshot") or {}
    visual = screenshot.get("visual_verification") or {}
    readiness = report.get("readiness") or {}
    checks = report.get("checks") or []
    markdown_lines = [
        "# Pass 10B Native Screenshot Evidence Intake",
        "",
        f"Generated: {payload['generated_at']}",
        f"Status: {payload['status']}",
        f"OK: {payload['ok']}",
        f"Screenshot: {screenshot.get('path')}",
        f"Declared source: {screenshot.get('declared_source')}",
        f"Screenshot nonblank: {visual.get('ok')} ({visual.get('reason')})",
        f"Unique colors: {visual.get('unique_color_count')}",
        f"Dominant color ratio: {visual.get('dominant_color_ratio')}",
        "",
        "## Readiness",
        "",
        f"- supplemental_native_screenshot_evidence_verified: {readiness.get('supplemental_native_screenshot_evidence_verified')}",
        f"- automated_packaged_visual_qa_complete: {readiness.get('automated_packaged_visual_qa_complete')}",
        f"- can_close_pass10b_native_visual_proof: {readiness.get('can_close_pass10b_native_visual_proof')}",
        f"- next_recommended_pass: {readiness.get('next_recommended_pass')}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        markdown_lines.append(f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}")
    blockers = readiness.get("blockers") or []
    if blockers:
        markdown_lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            markdown_lines.append(f"- {blocker}")
    markdown_lines.extend(
        [
            "",
            "## Authority Boundary",
            "",
            "- This report is supplemental evidence only.",
            "- It does not complete automated packaged visual QA.",
            "- It does not launch/capture the packaged executable, mutate host policy, sign or allowlist files, write installer/startup state, execute approvals, call providers/connectors, write Agent Bus tasks, or mutate canonical state.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    return {
        "written": True,
        "json_path": _relative(vault, json_path),
        "markdown_path": _relative(vault, markdown_path),
    }
