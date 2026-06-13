"""Native visual QA for the packaged ChaseOS Studio executable."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

from runtime.studio.packaged_app_launch_smoke import (
    DEFAULT_EXE,
    _approval_artifact_snapshot,
    _markdown_snapshot,
    _relative_to_vault,
    _resolve_executable,
    _snapshot_delta,
    _snapshot_delta_changed,
    _snapshot_delta_detail,
    _terminate_owned_process,
    _vault_arg_for_packaged_exe,
)
from runtime.studio.packaging_proof import build_studio_local_packaging_proof, _sha256
from runtime.operator_surface.browser.image_verifier import (
    _decode_png_pixels,
    _samples_for_color_type,
    analyze_png_nonblank,
)


MODEL_VERSION = "studio.packaged_app_visual_qa.v1"
SURFACE_ID = "studio_packaged_app_visual_qa"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
DEFAULT_SCREENSHOT_ROOT = Path(".pytest_tmp_env") / "studio-packaged-app-visual-qa"
DEFAULT_PACKAGED_QA_TEMP_ROOT = Path(".pytest_tmp_env") / "studio-packaged-app-temp"
TEMP_ENV_KEYS = ("TEMP", "TMP", "TMPDIR")
WEBVIEW2_USER_DATA_ENV = "WEBVIEW2_USER_DATA_FOLDER"
MAX_PYINSTALLER_TEMP_CLEANUP_ENTRIES = 20_000
MIN_QA_SCREENSHOT_DELAY_MS = 1000
MAX_QA_SCREENSHOT_DELAY_MS = 1500
QA_SCREENSHOT_PATH_ENV = "CHASEOS_STUDIO_QA_SCREENSHOT_PATH"
QA_SCREENSHOT_META_PATH_ENV = "CHASEOS_STUDIO_QA_SCREENSHOT_META_PATH"
QA_SCREENSHOT_DELAY_MS_ENV = "CHASEOS_STUDIO_QA_SCREENSHOT_DELAY_MS"
QA_EXIT_AFTER_SCREENSHOT_ENV = "CHASEOS_STUDIO_QA_EXIT_AFTER_SCREENSHOT"
QA_BATCH_PLAN_PATH_ENV = "CHASEOS_STUDIO_QA_BATCH_PLAN_PATH"
QA_BATCH_RESULT_PATH_ENV = "CHASEOS_STUDIO_QA_BATCH_RESULT_PATH"
QA_WINDOW_WIDTH_ENV = "CHASEOS_STUDIO_QA_WINDOW_WIDTH"
QA_WINDOW_HEIGHT_ENV = "CHASEOS_STUDIO_QA_WINDOW_HEIGHT"
MIN_NATIVE_WINDOW_WIDTH = 200
MIN_NATIVE_WINDOW_HEIGHT = 200
DEFAULT_CAPTURE_MARKDOWN_WINDOW_SIZE_CASES = (
    {"id": "compact", "width": 1000, "height": 700},
    {"id": "wide", "width": 1600, "height": 1000},
)
WINDOWS_APPLICATION_CONTROL_MARKERS = (
    "application control policy has blocked this file",
    "winerror 4551",
)
WEBVIEW2_RUNTIME_MARKERS = (
    "webview2 initialization failed",
    "corewebview2environment",
    "e_unexpected",
)
PYWEBVIEW_BACKEND_MARKERS = (
    "you must have pythonnet installed",
    "pythonnet installed in order to use pywebview",
)
STUDIO_CONTENT_REQUIRED_GROUPS = (
    ("chaseos studio",),
    (
        "product shell",
        "studio shell",
        "command center",
        "home",
        "chat",
        "workspaces",
        "graph",
        "agents / runtimes",
        "runtime lanes",
        "studio-desktop-shell-root",
    ),
)
FORBIDDEN_VISIBLE_COPY_TERMS = (
    "mvp",
    "dashboard",
    "node inspector",
    "runtime cockpit",
    "aor executions",
    "qa / proof",
    "proof",
    "dry-run",
    "dry run",
    "daemon",
    "build logs",
    "logs / audit",
    "not mounted",
    "shell action",
    "--json",
    "build log viewer",
    "implementation",
    "developer",
    "read-only",
    "read only",
    "readonly",
    "python -m runtime.cli.main",
    "localhost studio dashboard",
)
STARTUP_LOADING_VISIBLE_TERMS = (
    "starting chaseos studio",
    "preparing studio",
    "opening workspace",
    "loading...",
    "loading vault",
    "loading graph",
    "pending links loading",
    "overlays loading",
    "parser loading",
)
CONTENT_AREA_TOP_SKIP_PIXELS = 80
CONTENT_AREA_TOP_SKIP_RATIO = 0.08
DEFAULT_MIN_UNIQUE_COLORS = 8
DEFAULT_MAX_DOMINANT_RATIO = 0.95
CAPTURE_MARKDOWN_ACTION_HASH = "#/capture-markdown"
SETTINGS_PANEL_HASH = "#/settings"
CAPTURE_MARKDOWN_ACTION_PANEL_ID = "capture-markdown-action-clickthrough"
CAPTURE_MARKDOWN_GUARD_FAILURE_PANEL_ID = "capture-markdown-guard-failure-clickthrough"
CAPTURE_MARKDOWN_IMAGE_TEXT_PANEL_ID = "capture-markdown-image-text-clickthrough"
CAPTURE_MARKDOWN_IMAGE_TEXT_FAILURE_PANEL_ID = "capture-markdown-image-text-failure-states"
CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_PANEL_ID = "capture-markdown-downstream-failure-clickthrough"
PASSIVE_OPEN_FORBIDDEN_CHILD_PROCESS_NAMES = (
    "powershell.exe",
    "pwsh.exe",
    "cmd.exe",
    "bash.exe",
    "wscript.exe",
    "cscript.exe",
    "wt.exe",
)
CAPTURE_MARKDOWN_OPEN_SAFETY_CASES = (
    {
        "id": "capture-markdown",
        "name": "Capture Markdown",
        "hash": CAPTURE_MARKDOWN_ACTION_HASH,
        "required_content_groups": STUDIO_CONTENT_REQUIRED_GROUPS + (("capture", "capture markdown"),),
    },
    {
        "id": "settings-capture-controls",
        "name": "Settings Capture controls",
        "hash": SETTINGS_PANEL_HASH,
        "required_content_groups": STUDIO_CONTENT_REQUIRED_GROUPS + (("settings",),),
    },
)
CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_CASES = (
    {
        "id": "aor_approval_request_bad_statement",
        "label": "Agent Orchestration Runtime approval request",
        "invalid_statement_template": "invalid Agent Orchestration Runtime approval request confirmation {token}",
        "statement_selector": ".capture-markdown-source-pack-aor-approval-request-statement",
        "button_selector": ".capture-markdown-source-pack-aor-approval-request-btn",
        "result_selector": ".capture-markdown-source-pack-aor-approval-request-result .capture-markdown-guard-failure",
        "success_selector": ".capture-markdown-source-pack-aor-approval-request",
        "expected_text": "Agent Orchestration Runtime approval request blocked",
        "required_result_selectors": [
            ".capture-markdown-source-pack-aor-readiness",
            ".capture-markdown-source-pack-aor-approval-design",
        ],
        "forbidden_artifact_prefixes": [
            "07_LOGS/Agent-Activity/_vcmi_aor_dispatch_approvals/",
            "07_LOGS/Agent-Activity/_vcmi_agent_bus_tasks/",
            "07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/",
            "07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/",
            "02_KNOWLEDGE/Source-Intelligence/Reviewed-Captures/",
        ],
    },
    {
        "id": "source_intelligence_core_approval_request_bad_statement",
        "label": "Source Intelligence Core approval request",
        "invalid_statement_template": "invalid Source Intelligence Core approval request confirmation {token}",
        "button_selector": ".capture-markdown-source-pack-sic-approval-request-btn",
        "button_dataset_key": "operatorStatement",
        "result_selector": ".capture-markdown-source-pack-sic-approval-request-result .capture-markdown-guard-failure",
        "success_selector": ".capture-markdown-source-pack-sic-approval-request",
        "expected_text": "Source Intelligence Core approval request blocked",
        "required_result_selectors": [
            ".capture-markdown-source-pack-agent-bus-full-dispatch",
            ".capture-markdown-source-pack-sic-readiness",
            ".capture-markdown-source-pack-sic-approval-design",
        ],
        "forbidden_artifact_prefixes": [
            "07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/",
            "07_LOGS/Agent-Activity/_vcmi_sic_ingestion/",
            "07_LOGS/Agent-Activity/_vcmi_sic_graph_indexing/",
            "07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/",
            "02_KNOWLEDGE/Source-Intelligence/Reviewed-Captures/",
        ],
    },
    {
        "id": "canonical_promotion_approval_request_bad_statement",
        "label": "Canonical promotion approval request",
        "invalid_statement_template": "invalid canonical promotion approval request confirmation {token}",
        "button_selector": ".capture-markdown-source-pack-canonical-promotion-approval-request-btn",
        "button_dataset_key": "operatorStatement",
        "result_selector": ".capture-markdown-source-pack-canonical-promotion-approval-request-result .capture-markdown-guard-failure",
        "success_selector": ".capture-markdown-source-pack-canonical-promotion-approval-request",
        "expected_text": "Canonical promotion request blocked",
        "required_result_selectors": [
            ".capture-markdown-source-pack-sic-ingestion",
            ".capture-markdown-source-pack-sic-graph-indexing",
            ".capture-markdown-source-pack-canonical-promotion-readiness",
            ".capture-markdown-source-pack-canonical-promotion-approval-design",
        ],
        "forbidden_artifact_prefixes": [
            "07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/",
            "07_LOGS/Agent-Activity/_vcmi_canonical_promotion/",
            "02_KNOWLEDGE/Source-Intelligence/Reviewed-Captures/",
        ],
    },
)
CAPTURE_MARKDOWN_IMAGE_TEXT_PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15"
    "c4890000000d49444154789c6360000002000100ffff03000006000557bfab"
    "d40000000049454e44ae426082"
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _resolve_evidence_root(vault: Path, evidence_root: str | Path | None) -> Path:
    root_input = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("packaged app visual QA evidence root must stay inside the vault workspace") from exc
    return root


def _ps_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _hidden_subprocess_creationflags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _run_hidden_powershell(script: str, *, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
        creationflags=_hidden_subprocess_creationflags(),
    )


def _default_screenshot_path(vault: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-studio-packaged-app-visual-qa")
    return vault / DEFAULT_SCREENSHOT_ROOT / f"{stamp}.png"


def _qa_screenshot_delay_ms(settle_seconds: float) -> int:
    """Return a short post-load delay so the internal capture wins the fallback race."""

    try:
        requested = int(max(1.0, float(settle_seconds) - 1.0) * 1000)
    except (TypeError, ValueError):
        requested = MAX_QA_SCREENSHOT_DELAY_MS
    return max(MIN_QA_SCREENSHOT_DELAY_MS, min(MAX_QA_SCREENSHOT_DELAY_MS, requested))


def _normalize_initial_hash(value: str | None) -> str | None:
    if value is None:
        return None
    route = str(value).strip()
    if not route:
        return None
    if route.startswith("#"):
        normalized = route
    elif route.startswith("/"):
        normalized = f"#{route}"
    else:
        normalized = f"#/{route.lstrip('/')}"
    if not all(ch.isalnum() or ch in "#/-_." for ch in normalized):
        raise ValueError("initial hash contains unsupported characters")
    return normalized


def _route_text_hint(initial_hash: str | None) -> str:
    """Return bounded route text for native QA when UI Automation is unavailable."""

    generic = "ChaseOS Studio home chat workspaces graph agents / runtimes"
    if not initial_hash:
        return generic
    fragment = initial_hash.lstrip("#/").replace("-", " ").replace("_", " ").strip()
    aliases = {
        "dashboard": "home command center",
        "aor": "tasks runs tasks & runs",
        "build logs": "history audit history / audit",
        "node inspector": "docs inspector docs / inspector",
        "pulse schedule proof": "proactive briefings",
        "qa proof": "quality review",
        "runtime cockpit": "agents runtimes agents / runtimes",
    }
    if fragment in aliases:
        return " ".join((generic, aliases[fragment]))
    return " ".join(token for token in (generic, fragment) if token)


def _resolve_runtime_dir(
    vault: Path,
    value: str | Path | None,
    *,
    label: str,
    allow_outside_vault: bool = False,
) -> Path | None:
    if value is None:
        return None
    raw = Path(value)
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    if not allow_outside_vault:
        try:
            resolved.relative_to(vault)
        except ValueError as exc:
            raise ValueError(f"{label} must stay inside the vault workspace unless external temp roots are explicitly allowed") from exc
    return resolved


def build_runtime_env_overrides(
    vault_root: str | Path,
    *,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    allow_external_runtime_dirs: bool = False,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Build bounded runtime-directory environment overrides for packaged visual QA."""

    vault = _vault_path(vault_root)
    user_data = _resolve_runtime_dir(
        vault,
        webview2_user_data_root,
        label="WebView2 user-data root",
        allow_outside_vault=allow_external_runtime_dirs,
    )
    temp = _resolve_runtime_dir(
        vault,
        temp_root,
        label="packaged app temp root",
        allow_outside_vault=allow_external_runtime_dirs,
    )
    overrides: dict[str, str] = {}
    runtime_dirs: dict[str, Any] = {
        "allow_external_runtime_dirs": bool(allow_external_runtime_dirs),
        "webview2_user_data_root": str(user_data) if user_data else None,
        "temp_root": str(temp) if temp else None,
        "created": [],
    }
    for path in (user_data, temp):
        if path is None:
            continue
        path.mkdir(parents=True, exist_ok=True)
        runtime_dirs["created"].append(str(path))
    if user_data is not None:
        overrides[WEBVIEW2_USER_DATA_ENV] = str(user_data)
    if temp is not None:
        overrides.update({key: str(temp) for key in TEMP_ENV_KEYS})
    return overrides, runtime_dirs


def _classify_launch_error(launch_error: str | None) -> dict[str, Any]:
    message = launch_error or ""
    normalized = message.lower()
    blocked_by_application_control = any(marker in normalized for marker in WINDOWS_APPLICATION_CONTROL_MARKERS)
    if blocked_by_application_control:
        status = "blocked_by_windows_application_control"
        remediation = [
            "Run the packaged executable from a Windows Application Control allowed path or policy context.",
            "Rebuild/sign/allowlist the packaged executable according to the host policy before rerunning native visual QA.",
            "Do not mark packaged native visual QA complete until a real native screenshot is captured and passes the nonblank gate.",
        ]
    elif message:
        status = "launch_failed_unclassified"
        remediation = [
            "Inspect launch_error/stdout/stderr and rerun packaged visual QA after the host launch issue is resolved.",
            "Do not mark packaged native visual QA complete until a real native screenshot is captured and passes the nonblank gate.",
        ]
    else:
        status = "not_applicable"
        remediation = []
    return {
        "status": status,
        "blocked_by_windows_application_control": blocked_by_application_control,
        "launch_error": launch_error,
        "remediation": remediation,
    }


def _classify_runtime_error(stderr_tail: str) -> dict[str, Any]:
    normalized = (stderr_tail or "").lower()
    pywebview_backend_failed = any(marker in normalized for marker in PYWEBVIEW_BACKEND_MARKERS)
    if pywebview_backend_failed:
        return {
            "status": "pywebview_backend_dependency_missing",
            "blocked": True,
            "message": "PyWebView backend dependency is missing before native screenshot capture.",
            "remediation": [
                "Rebuild the packaged executable with the pywebview backend dependency included.",
                "Rerun packaged native visual QA after pywebview can initialize a visible native window.",
            ],
        }
    webview2_failed = any(marker in normalized for marker in WEBVIEW2_RUNTIME_MARKERS)
    if webview2_failed:
        return {
            "status": "webview2_initialization_failed",
            "blocked": True,
            "message": "PyWebView/WebView2 initialization failed before native screenshot capture.",
            "remediation": [
                "Verify WebView2 runtime availability and policy compatibility for the packaged executable.",
                "Rerun packaged native visual QA after WebView2 can initialize a visible window.",
            ],
        }
    return {
        "status": "not_applicable",
        "blocked": False,
        "message": None,
        "remediation": [],
    }


def _assess_studio_content_sentinel(
    capture: dict[str, Any],
    required_groups: tuple[tuple[str, ...], ...] | None = None,
) -> dict[str, Any]:
    """Verify captured native-window metadata contains Studio-specific visible UI tokens."""

    groups = required_groups or STUDIO_CONTENT_REQUIRED_GROUPS
    sources = {
        "window_title": capture.get("window_title"),
        "ui_automation_text": capture.get("ui_automation_text"),
    }
    combined = " | ".join(str(value) for value in sources.values() if value)
    normalized = combined.lower()
    matched_groups: list[list[str]] = []
    missing_groups: list[list[str]] = []
    for group in groups:
        matched = [token for token in group if token in normalized]
        if matched:
            matched_groups.append(matched)
        else:
            missing_groups.append(list(group))
    ok = bool(capture.get("ok")) and not missing_groups
    reason = "studio-content-sentinel-present" if ok else "studio-content-sentinel-missing"
    return {
        "ok": ok,
        "reason": reason,
        "required_groups": [list(group) for group in groups],
        "matched_groups": matched_groups,
        "missing_groups": missing_groups,
        "sources_checked": [key for key, value in sources.items() if value],
        "text_excerpt": combined[:1000],
    }


def _assess_forbidden_visible_copy(capture: dict[str, Any]) -> dict[str, Any]:
    """Reject native UI Automation text that still exposes dev-era product copy."""

    sources = {
        "window_title": capture.get("window_title"),
        "ui_automation_text": capture.get("ui_automation_text"),
    }
    combined = " | ".join(str(value) for value in sources.values() if value)
    normalized = combined.lower()
    matches = [term for term in FORBIDDEN_VISIBLE_COPY_TERMS if term in normalized]
    return {
        "ok": not matches,
        "reason": "no-forbidden-visible-copy" if not matches else "forbidden-visible-copy-present",
        "forbidden_terms": list(FORBIDDEN_VISIBLE_COPY_TERMS),
        "matches": matches,
        "sources_checked": [key for key, value in sources.items() if value],
        "text_excerpt": combined[:1000],
    }


def _assess_startup_loading_visible_copy(capture: dict[str, Any]) -> dict[str, Any]:
    """Reject screenshots that still expose the native shell startup/loading overlay."""

    sources = {
        "window_title": capture.get("window_title"),
        "ui_automation_text": capture.get("ui_automation_text"),
    }
    combined = " | ".join(str(value) for value in sources.values() if value)
    normalized = combined.lower()
    matches = [term for term in STARTUP_LOADING_VISIBLE_TERMS if term in normalized]
    return {
        "ok": not matches,
        "reason": "no-startup-loading-visible" if not matches else "startup-loading-visible",
        "loading_terms": list(STARTUP_LOADING_VISIBLE_TERMS),
        "matches": matches,
        "sources_checked": [key for key, value in sources.items() if value],
        "text_excerpt": combined[:1000],
    }


def _analyze_png_content_area(
    path: str | Path,
    *,
    min_unique_colors: int,
    max_dominant_ratio: float,
    max_sample_pixels: int = 500_000,
) -> dict[str, Any]:
    """Analyze the window content area so title-bar pixels cannot pass UI QA."""

    screenshot = Path(path)
    result: dict[str, Any] = {
        "path": str(screenshot),
        "exists": screenshot.is_file(),
        "png": False,
        "ok": False,
        "reason": "file-missing",
    }
    if not screenshot.is_file():
        return result

    try:
        width, height, bit_depth, color_type, rows = _decode_png_pixels(screenshot)
    except Exception as exc:
        result.update({"reason": "png-decode-failed", "error": str(exc)})
        return result

    samples = _samples_for_color_type(color_type) or 1
    y_start = min(height - 1, max(CONTENT_AREA_TOP_SKIP_PIXELS, int(height * CONTENT_AREA_TOP_SKIP_RATIO)))
    content_rows = rows[y_start:]
    pixel_count = width * max(0, len(content_rows))
    stride = max(1, pixel_count // max(1, max_sample_pixels))
    colors: dict[bytes, int] = {}
    seen = 0
    cursor = 0
    for row in content_rows:
        for start in range(0, len(row), samples):
            if cursor % stride == 0:
                color = row[start : start + samples]
                colors[color] = colors.get(color, 0) + 1
                seen += 1
            cursor += 1

    dominant_count = max(colors.values()) if colors else 0
    dominant_ratio = dominant_count / seen if seen else 1.0
    unique_color_count = len(colors)
    ok = unique_color_count >= int(min_unique_colors) and dominant_ratio <= float(max_dominant_ratio)
    result.update(
        {
            "png": True,
            "ok": ok,
            "reason": "content-area-nonblank" if ok else "content-area-blank-or-near-uniform",
            "width": width,
            "height": height,
            "content_y_start": y_start,
            "content_height": max(0, height - y_start),
            "bit_depth": bit_depth,
            "color_type": color_type,
            "pixel_count": pixel_count,
            "sampled_pixels": seen,
            "unique_color_count": unique_color_count,
            "dominant_color_ratio": round(dominant_ratio, 6),
            "min_unique_colors": int(min_unique_colors),
            "max_dominant_ratio": float(max_dominant_ratio),
        }
    )
    return result


def _sampled_color_stats(
    rows: list[bytes],
    *,
    width: int,
    y_start: int,
    color_type: int,
    max_sample_pixels: int,
) -> dict[str, Any]:
    samples = _samples_for_color_type(color_type) or 1
    region_rows = rows[y_start:]
    pixel_count = width * max(0, len(region_rows))
    sample_step = max(1, int((pixel_count / max(1, max_sample_pixels)) ** 0.5))
    while pixel_count // (sample_step * sample_step) > max_sample_pixels:
        sample_step += 1
    colors: dict[bytes, int] = {}
    seen = 0
    row_step = sample_step
    column_step = samples * sample_step
    for row in region_rows[::row_step]:
        for start in range(0, len(row), column_step):
            color = row[start : start + samples]
            colors[color] = colors.get(color, 0) + 1
            seen += 1
    dominant_count = max(colors.values()) if colors else 0
    dominant_ratio = dominant_count / seen if seen else 1.0
    return {
        "pixel_count": pixel_count,
        "sampled_pixels": seen,
        "unique_color_count": len(colors),
        "dominant_color_ratio": round(dominant_ratio, 6),
    }


def _analyze_png_nonblank_and_content_area_dotnet(
    path: Path,
    *,
    min_unique_colors: int,
    max_dominant_ratio: float,
    max_sample_pixels: int,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if os.name != "nt" or not path.is_file():
        return None
    if getattr(subprocess.Popen, "__module__", "") != "subprocess":
        return None
    script = f"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$path = {_ps_quote(path)}
$minUniqueColors = {int(min_unique_colors)}
$maxDominantRatio = {float(max_dominant_ratio)}
$maxSamplePixels = {int(max_sample_pixels)}
$contentTopSkipPixels = {int(CONTENT_AREA_TOP_SKIP_PIXELS)}
$contentTopSkipRatio = {float(CONTENT_AREA_TOP_SKIP_RATIO)}

function Measure-Region([System.Drawing.Bitmap]$bitmap, [int]$yStart, [string]$okReason, [string]$blockedReason) {{
  $width = [int]$bitmap.Width
  $height = [int]$bitmap.Height
  $regionHeight = [Math]::Max(0, $height - $yStart)
  $pixelCount = $width * $regionHeight
  $step = [Math]::Max(1, [int][Math]::Floor([Math]::Sqrt($pixelCount / [double][Math]::Max(1, $maxSamplePixels))))
  while ([Math]::Floor($pixelCount / [double]($step * $step)) -gt $maxSamplePixels) {{
    $step += 1
  }}
  $colors = @{{}}
  $seen = 0
  for ($y = $yStart; $y -lt $height; $y += $step) {{
    for ($x = 0; $x -lt $width; $x += $step) {{
      $argb = $bitmap.GetPixel($x, $y).ToArgb()
      if ($colors.ContainsKey($argb)) {{
        $colors[$argb] += 1
      }} else {{
        $colors[$argb] = 1
      }}
      $seen += 1
    }}
  }}
  $dominant = 0
  foreach ($value in $colors.Values) {{
    if ($value -gt $dominant) {{ $dominant = $value }}
  }}
  $ratio = 1.0
  if ($seen -gt 0) {{ $ratio = $dominant / [double]$seen }}
  $ok = ($colors.Count -ge $minUniqueColors -and $ratio -le $maxDominantRatio)
  return @{{
    ok = [bool]$ok
    reason = $(if ($ok) {{ $okReason }} else {{ $blockedReason }})
    width = $width
    height = $height
    pixel_count = $pixelCount
    sampled_pixels = $seen
    unique_color_count = $colors.Count
    dominant_color_ratio = [Math]::Round($ratio, 6)
    min_unique_colors = $minUniqueColors
    max_dominant_ratio = $maxDominantRatio
  }}
}}

$bitmap = [System.Drawing.Bitmap]::new($path)
try {{
  $yStart = [Math]::Min([int]$bitmap.Height - 1, [Math]::Max($contentTopSkipPixels, [int]([double]$bitmap.Height * $contentTopSkipRatio)))
  $visual = Measure-Region $bitmap 0 'nonblank' 'blank-or-near-uniform'
  $content = Measure-Region $bitmap $yStart 'content-area-nonblank' 'content-area-blank-or-near-uniform'
  $content.content_y_start = $yStart
  $content.content_height = [Math]::Max(0, [int]$bitmap.Height - $yStart)
  $payload = @{{
    ok = $true
    pixel_format = $bitmap.PixelFormat.ToString()
    visual = $visual
    content = $content
  }}
  $payload | ConvertTo-Json -Compress -Depth 5
}} finally {{
  $bitmap.Dispose()
}}
"""
    try:
        proc = _run_hidden_powershell(script, timeout=20)
        if proc.returncode != 0:
            return None
        payload = json.loads((proc.stdout or "").strip() or "{}")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None
    if not payload.get("ok"):
        return None
    base = {
        "path": str(path),
        "exists": True,
        "png": True,
        "pixel_format": payload.get("pixel_format"),
    }
    visual = {**base, **(payload.get("visual") or {})}
    visual["size_bytes"] = path.stat().st_size
    content = {**base, **(payload.get("content") or {})}
    return visual, content


def _analyze_png_nonblank_and_content_area(
    path: str | Path,
    *,
    min_unique_colors: int,
    max_dominant_ratio: float,
    max_sample_pixels: int = 100_000,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Analyze full-window and content-area nonblank evidence from one PNG decode."""

    screenshot = Path(path)
    visual: dict[str, Any] = {
        "path": str(screenshot),
        "exists": screenshot.is_file(),
        "png": False,
        "ok": False,
        "reason": "file-missing",
    }
    content: dict[str, Any] = dict(visual)
    if not screenshot.is_file():
        return visual, content

    visual["size_bytes"] = screenshot.stat().st_size
    dotnet_result = _analyze_png_nonblank_and_content_area_dotnet(
        screenshot,
        min_unique_colors=min_unique_colors,
        max_dominant_ratio=max_dominant_ratio,
        max_sample_pixels=max_sample_pixels,
    )
    if dotnet_result is not None:
        return dotnet_result

    try:
        width, height, bit_depth, color_type, rows = _decode_png_pixels(screenshot)
    except Exception as exc:
        visual.update({"reason": "png-decode-failed", "error": str(exc)})
        content.update({"reason": "png-decode-failed", "error": str(exc)})
        return visual, content

    full_stats = _sampled_color_stats(
        rows,
        width=width,
        y_start=0,
        color_type=color_type,
        max_sample_pixels=max_sample_pixels,
    )
    full_ok = (
        int(full_stats["unique_color_count"]) >= int(min_unique_colors)
        and float(full_stats["dominant_color_ratio"]) <= float(max_dominant_ratio)
    )
    visual.update(
        {
            "png": True,
            "ok": full_ok,
            "reason": "nonblank" if full_ok else "blank-or-near-uniform",
            "width": width,
            "height": height,
            "bit_depth": bit_depth,
            "color_type": color_type,
            "min_unique_colors": int(min_unique_colors),
            "max_dominant_ratio": float(max_dominant_ratio),
            **full_stats,
        }
    )

    y_start = min(height - 1, max(CONTENT_AREA_TOP_SKIP_PIXELS, int(height * CONTENT_AREA_TOP_SKIP_RATIO)))
    content_stats = _sampled_color_stats(
        rows,
        width=width,
        y_start=y_start,
        color_type=color_type,
        max_sample_pixels=max_sample_pixels,
    )
    content_ok = (
        int(content_stats["unique_color_count"]) >= int(min_unique_colors)
        and float(content_stats["dominant_color_ratio"]) <= float(max_dominant_ratio)
    )
    content.update(
        {
            "png": True,
            "ok": content_ok,
            "reason": "content-area-nonblank" if content_ok else "content-area-blank-or-near-uniform",
            "width": width,
            "height": height,
            "content_y_start": y_start,
            "content_height": max(0, height - y_start),
            "bit_depth": bit_depth,
            "color_type": color_type,
            "min_unique_colors": int(min_unique_colors),
            "max_dominant_ratio": float(max_dominant_ratio),
            **content_stats,
        }
    )
    return visual, content


def _capture_window_screenshot(
    *,
    process_id: int,
    screenshot_path: Path,
    timeout_seconds: float,
    ui_text_hint: str = "",
) -> dict[str, Any]:
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot_out_path = _vault_arg_for_packaged_exe(screenshot_path.resolve())
    ui_text_hint_arg = _vault_arg_for_packaged_exe(ui_text_hint)
    script = f"""
$ErrorActionPreference = 'Stop'
$pidTarget = {int(process_id)}
$outPath = {_ps_quote(screenshot_out_path)}
$uiTextHint = {_ps_quote(ui_text_hint_arg)}
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class ChaseOSStudioWin32 {{
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT {{
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
  }}
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")]
  public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
  [DllImport("user32.dll")]
  public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")]
  public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
  [DllImport("user32.dll")]
  public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
  [DllImport("user32.dll")]
  public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")]
  public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")]
  public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
  [DllImport("user32.dll")]
  public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
}}
"@
try {{ Add-Type -AssemblyName UIAutomationClient }} catch {{}}
$deadline = (Get-Date).AddSeconds({float(timeout_seconds)})
$handle = [IntPtr]::Zero
$handleProcessId = $pidTarget
$handleTitle = $null
$lastCandidate = $null
$minWidth = {MIN_NATIVE_WINDOW_WIDTH}
$minHeight = {MIN_NATIVE_WINDOW_HEIGHT}
$hwndTopMost = [IntPtr]::new(-1)
$hwndNoTopMost = [IntPtr]::new(-2)

function Get-CandidateProcessIds([int]$rootId) {{
  $seen = New-Object 'System.Collections.Generic.HashSet[int]'
  $queue = New-Object 'System.Collections.Generic.Queue[int]'
  [void]$seen.Add($rootId)
  $queue.Enqueue($rootId)
  while ($queue.Count -gt 0) {{
    $current = $queue.Dequeue()
    try {{
      $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$current" -ErrorAction Stop
      foreach ($child in $children) {{
        $childId = [int]$child.ProcessId
        if ($seen.Add($childId)) {{
          $queue.Enqueue($childId)
        }}
      }}
    }} catch {{}}
  }}
  return @($seen)
}}

function Get-WindowTitle([IntPtr]$candidateHandle) {{
  $builder = New-Object System.Text.StringBuilder 512
  [void][ChaseOSStudioWin32]::GetWindowText($candidateHandle, $builder, $builder.Capacity)
  return $builder.ToString()
}}

function Get-UiAutomationText([IntPtr]$candidateHandle) {{
  try {{
    $root = [System.Windows.Automation.AutomationElement]::FromHandle($candidateHandle)
    if ($null -eq $root) {{ return '' }}
    $items = New-Object System.Collections.ArrayList
    $rootName = $root.Current.Name
    if (-not [string]::IsNullOrWhiteSpace($rootName)) {{ [void]$items.Add($rootName) }}
    $nodes = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($node in $nodes) {{
      if ($items.Count -ge 120) {{ break }}
      $name = $node.Current.Name
      if (-not [string]::IsNullOrWhiteSpace($name)) {{ [void]$items.Add($name) }}
    }}
    return (($items | Select-Object -Unique) -join ' | ')
  }} catch {{
    return ''
  }}
}}

function Get-BitmapUniqueSampleCount([System.Drawing.Bitmap]$candidateBitmap) {{
  $seen = New-Object 'System.Collections.Generic.HashSet[int]'
  $xStep = [Math]::Max(1, [int]($candidateBitmap.Width / 32))
  $yStep = [Math]::Max(1, [int]($candidateBitmap.Height / 32))
  for ($y = 0; $y -lt $candidateBitmap.Height; $y += $yStep) {{
    for ($x = 0; $x -lt $candidateBitmap.Width; $x += $xStep) {{
      [void]$seen.Add($candidateBitmap.GetPixel($x, $y).ToArgb())
      if ($seen.Count -gt 1) {{ return $seen.Count }}
    }}
  }}
  return $seen.Count
}}

function Get-TopLevelWindowCandidates([int[]]$processIds) {{
  $candidateSet = New-Object 'System.Collections.Generic.HashSet[int]'
  foreach ($candidateId in $processIds) {{
    [void]$candidateSet.Add([int]$candidateId)
  }}
  $windows = New-Object System.Collections.ArrayList
  $callback = [ChaseOSStudioWin32+EnumWindowsProc]{{
    param([IntPtr]$candidateHandle, [IntPtr]$lParam)
    if (-not [ChaseOSStudioWin32]::IsWindowVisible($candidateHandle)) {{ return $true }}
    $candidateProcessId = [uint32]0
    [void][ChaseOSStudioWin32]::GetWindowThreadProcessId($candidateHandle, [ref]$candidateProcessId)
    $candidateTitle = Get-WindowTitle $candidateHandle
    $matchedByProcess = $candidateSet.Contains([int]$candidateProcessId)
    if (-not $matchedByProcess) {{ return $true }}
    $isStudioTitle = $candidateTitle -like 'ChaseOS Studio*'
    $candidateUiText = ''
    try {{
      $candidateUiText = Get-UiAutomationText $candidateHandle
    }} catch {{}}
    $candidateRect = New-Object ChaseOSStudioWin32+RECT
    $candidateRectOk = [ChaseOSStudioWin32]::GetWindowRect($candidateHandle, [ref]$candidateRect)
    $candidateWidth = $candidateRect.Right - $candidateRect.Left
    $candidateHeight = $candidateRect.Bottom - $candidateRect.Top
    if (-not $candidateRectOk -or $candidateWidth -le 0 -or $candidateHeight -le 0) {{ return $true }}
    $area = $candidateWidth * $candidateHeight
    [void]$windows.Add([pscustomobject]@{{
      handle_int64 = $candidateHandle.ToInt64()
      process_id = [int]$candidateProcessId
      title = $candidateTitle
      ui_automation_text = $candidateUiText
      width = $candidateWidth
      height = $candidateHeight
      area = $area
      is_studio_title = $isStudioTitle
      matched_by_process = $matchedByProcess
    }})
    return $true
  }}
  [void][ChaseOSStudioWin32]::EnumWindows($callback, [IntPtr]::Zero)
  return $windows.ToArray()
}}

do {{
  $candidateIds = Get-CandidateProcessIds $pidTarget
  $candidates = Get-TopLevelWindowCandidates $candidateIds
  $bestCandidate = $candidates |
    Sort-Object -Property @(
      @{{ Expression = 'matched_by_process'; Descending = $true }},
      @{{ Expression = 'is_studio_title'; Descending = $true }},
      @{{ Expression = {{ $_.width -ge $minWidth -and $_.height -ge $minHeight }}; Descending = $true }},
      @{{ Expression = 'area'; Descending = $true }}
    ) |
    Select-Object -First 1
  if ($null -ne $bestCandidate) {{
    $lastCandidate = @{{
      process_id = $bestCandidate.process_id
      handle = $bestCandidate.handle_int64
      rect_ok = $true
      width = $bestCandidate.width
      height = $bestCandidate.height
      title = $bestCandidate.title
      ui_automation_text = $bestCandidate.ui_automation_text
      is_studio_title = $bestCandidate.is_studio_title
      matched_by_process = $bestCandidate.matched_by_process
    }}
    if ($bestCandidate.width -ge $minWidth -and $bestCandidate.height -ge $minHeight) {{
      $handle = [IntPtr]::new([int64]$bestCandidate.handle_int64)
      $handleProcessId = $bestCandidate.process_id
      $handleTitle = $bestCandidate.title
    }}
  }}
  if ($handle -ne [IntPtr]::Zero) {{ break }}
  Start-Sleep -Milliseconds 250
}} while ((Get-Date) -lt $deadline)
if ($handle -eq [IntPtr]::Zero) {{
  @{{
    ok = $false
    error = 'window_handle_not_found'
    process_id = $pidTarget
    candidate_process_ids = @(Get-CandidateProcessIds $pidTarget)
    last_candidate = $lastCandidate
  }} | ConvertTo-Json -Compress -Depth 5
  exit 2
}}
[ChaseOSStudioWin32]::SetForegroundWindow($handle) | Out-Null
Start-Sleep -Milliseconds 500
$rect = New-Object ChaseOSStudioWin32+RECT
$rectOk = $false
$width = 0
$height = 0
do {{
  $rectOk = [ChaseOSStudioWin32]::GetWindowRect($handle, [ref]$rect)
  $width = $rect.Right - $rect.Left
  $height = $rect.Bottom - $rect.Top
  if ($rectOk -and $width -gt 0 -and $height -gt 0) {{ break }}
  Start-Sleep -Milliseconds 250
}} while ((Get-Date) -lt $deadline)
if (-not $rectOk -or $width -le 0 -or $height -le 0) {{
  @{{
    ok = $false
    error = 'invalid_window_bounds'
    process_id = $pidTarget
    window_process_id = $handleProcessId
    window_title = $handleTitle
    handle = $handle.ToInt64()
    rect_ok = $rectOk
    width = $width
    height = $height
    candidate_process_ids = @(Get-CandidateProcessIds $pidTarget)
    last_candidate = $lastCandidate
  }} | ConvertTo-Json -Compress -Depth 5
  exit 3
}}
$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$uiAutomationText = ''
$captureMethod = $null
$printException = $null
try {{
  $uiAutomationText = Get-UiAutomationText $handle
  [ChaseOSStudioWin32]::ShowWindow($handle, 9) | Out-Null
  [ChaseOSStudioWin32]::SetWindowPos($handle, $hwndTopMost, 64, 64, $width, $height, 0x0040) | Out-Null
  [ChaseOSStudioWin32]::SetForegroundWindow($handle) | Out-Null
  Start-Sleep -Milliseconds 750
  $rectOk = [ChaseOSStudioWin32]::GetWindowRect($handle, [ref]$rect)
  $width = $rect.Right - $rect.Left
  $height = $rect.Bottom - $rect.Top
  if (-not $rectOk -or $width -le 0 -or $height -le 0) {{ throw 'invalid bounds before CopyFromScreen' }}
  if ($bitmap.Width -ne $width -or $bitmap.Height -ne $height) {{
    $graphics.Dispose()
    $bitmap.Dispose()
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  }}
  try {{
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $hdc = $graphics.GetHdc()
    try {{
      $printOk = [ChaseOSStudioWin32]::PrintWindow($handle, $hdc, 2)
    }} finally {{
      $graphics.ReleaseHdc($hdc)
    }}
    if (-not $printOk) {{ throw 'PrintWindow returned false' }}
    $printUniqueSampleCount = Get-BitmapUniqueSampleCount $bitmap
    if ($printUniqueSampleCount -le 1) {{ throw 'PrintWindow produced a blank or near-uniform bitmap' }}
    $bitmap.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $captureMethod = 'print_window'
  }} catch {{
    $printException = $_.Exception.Message
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, [System.Drawing.Size]::new($width, $height))
    $copyUniqueSampleCount = Get-BitmapUniqueSampleCount $bitmap
    if ($copyUniqueSampleCount -le 1) {{ throw "CopyFromScreen produced a blank or near-uniform bitmap" }}
    $bitmap.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $captureMethod = 'copy_from_screen'
  }}
}} catch {{
  $copyException = $_.Exception.Message
  try {{
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, [System.Drawing.Size]::new($width, $height))
    $lastCopyUniqueSampleCount = Get-BitmapUniqueSampleCount $bitmap
    if ($lastCopyUniqueSampleCount -le 1) {{ throw "CopyFromScreen produced a blank or near-uniform bitmap" }}
    $bitmap.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $captureMethod = 'copy_from_screen'
  }} catch {{
    @{{
      ok = $false
      error = 'copy_from_screen_failed'
      print_window_error = 'print_window_failed'
      process_id = $pidTarget
      window_process_id = $handleProcessId
      window_title = $handleTitle
      ui_automation_text = $uiAutomationText
      handle = $handle.ToInt64()
      left = $rect.Left
      top = $rect.Top
      width = $width
      height = $height
      rect_ok = $rectOk
      candidate_process_ids = @(Get-CandidateProcessIds $pidTarget)
      last_candidate = $lastCandidate
      copy_from_screen_exception = $_.Exception.Message
      first_copy_from_screen_exception = $copyException
      print_window_exception = $printException
    }} | ConvertTo-Json -Compress -Depth 5
    exit 4
  }}
}} finally {{
  try {{ [ChaseOSStudioWin32]::SetWindowPos($handle, $hwndNoTopMost, $rect.Left, $rect.Top, $width, $height, 0x0040) | Out-Null }} catch {{}}
  $graphics.Dispose()
  $bitmap.Dispose()
}}
$file = Get-Item -LiteralPath $outPath
@{{
  ok = $true
  process_id = $pidTarget
  window_process_id = $handleProcessId
  path = $outPath
  left = $rect.Left
  top = $rect.Top
  width = $width
  height = $height
  window_title = $handleTitle
  ui_automation_text = $uiAutomationText
  ui_text_hint = $uiTextHint
  capture_method = $captureMethod
  size_bytes = $file.Length
}} | ConvertTo-Json -Compress -Depth 5
"""
    try:
        proc = _run_hidden_powershell(script, timeout=max(5.0, timeout_seconds + 10.0))
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": "window_capture_timeout",
            "process_id": process_id,
            "returncode": None,
            "stdout_tail": (exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""))[-4000:],
            "stderr_tail": (exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""))[-4000:],
        }
    payload: dict[str, Any]
    try:
        payload = json.loads((proc.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {}
    payload.update(
        {
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-4000:],
        }
    )
    if proc.returncode != 0:
        payload["ok"] = False
    return payload


def _read_internal_qa_capture(meta_path: Path, screenshot_path: Path) -> dict[str, Any]:
    """Read a packaged-app self-capture written by the Qt shell QA hook."""

    if not meta_path.is_file():
        return {"ok": False, "error": "internal_qa_capture_meta_missing", "meta_path": str(meta_path)}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "error": "internal_qa_capture_meta_unreadable",
            "meta_path": str(meta_path),
            "exception": str(exc),
        }
    screenshot_exists = screenshot_path.is_file()
    size_bytes = screenshot_path.stat().st_size if screenshot_exists else 0
    internal_capture_ready = bool(meta.get("ok")) and screenshot_exists and size_bytes > 1000
    visual = (
        analyze_png_nonblank(
            screenshot_path,
            min_unique_colors=DEFAULT_MIN_UNIQUE_COLORS,
            max_dominant_ratio=DEFAULT_MAX_DOMINANT_RATIO,
        )
        if screenshot_exists
        else {}
    )
    ok = internal_capture_ready and bool(visual.get("ok"))
    error = str(meta.get("error") or "internal_qa_capture_incomplete")
    if internal_capture_ready and not ok:
        error = "internal_qa_capture_blank_or_near_uniform"
    return {
        "ok": ok,
        "error": None if ok else error,
        "process_id": meta.get("process_id"),
        "window_process_id": meta.get("process_id"),
        "path": str(screenshot_path),
        "width": int(meta.get("width") or 0),
        "height": int(meta.get("height") or 0),
        "window_title": meta.get("window_title"),
        "ui_automation_text": meta.get("ui_automation_text"),
        "capture_method": meta.get("method") or "qt_widget_grab",
        "size_bytes": size_bytes,
        "meta_path": str(meta_path),
        "meta": meta,
        "visual_verification": visual,
    }


def _wait_for_internal_qa_capture(
    meta_path: Path,
    screenshot_path: Path,
    *,
    timeout_seconds: float,
    poll_seconds: float = 0.25,
) -> dict[str, Any]:
    """Poll briefly for the Qt self-capture before using external UI Automation."""

    timeout = max(0.0, float(timeout_seconds))
    poll_interval = max(0.05, float(poll_seconds))
    deadline = time.monotonic() + timeout
    attempts_remaining = max(1, int(timeout / poll_interval) + 1)
    last = _read_internal_qa_capture(meta_path, screenshot_path)
    while not last.get("ok") and time.monotonic() < deadline and attempts_remaining > 0:
        attempts_remaining -= 1
        time.sleep(poll_interval)
        last = _read_internal_qa_capture(meta_path, screenshot_path)
    return last


def _runtime_temp_root_from_env(env: dict[str, str]) -> Path | None:
    for key in TEMP_ENV_KEYS:
        value = env.get(key)
        if value:
            try:
                return Path(value).resolve()
            except OSError:
                return None
    return None


def _snapshot_pyinstaller_temp_dirs(env: dict[str, str]) -> dict[str, Any]:
    root = _runtime_temp_root_from_env(env)
    if root is None:
        return {"root": None, "paths": []}
    try:
        paths = sorted(str(path.resolve()) for path in root.glob("_MEI*") if path.is_dir())
    except OSError:
        paths = []
    return {"root": str(root), "paths": paths}


def _bounded_tree_entry_count(root: Path, *, limit: int) -> tuple[int, bool]:
    count = 0
    for _current_root, dirs, files in os.walk(root):
        count += len(dirs) + len(files)
        if count > limit:
            return count, True
    return count, False


def _cleanup_new_pyinstaller_temp_dirs(
    before_snapshot: dict[str, Any],
    env: dict[str, str],
) -> dict[str, Any]:
    """Remove only PyInstaller temp dirs created during this QA launch."""

    root = _runtime_temp_root_from_env(env)
    if root is None:
        return {"attempted": False, "root": None, "deleted": [], "failed": [], "reason": "temp-root-unresolved"}
    after_snapshot = _snapshot_pyinstaller_temp_dirs(env)
    before_paths = set(str(path) for path in (before_snapshot.get("paths") or []))
    after_paths = [Path(path) for path in (after_snapshot.get("paths") or []) if str(path) not in before_paths]
    deleted: list[str] = []
    failed: list[dict[str, str]] = []
    for candidate in after_paths:
        try:
            resolved = candidate.resolve()
            resolved.relative_to(root)
            if not resolved.name.startswith("_MEI") or not resolved.is_dir():
                continue
            entry_count, exceeded = _bounded_tree_entry_count(
                resolved,
                limit=MAX_PYINSTALLER_TEMP_CLEANUP_ENTRIES,
            )
            if exceeded:
                failed.append(
                    {
                        "path": str(candidate),
                        "error": (
                            "cleanup deferred: "
                            f"{entry_count} entries exceeds bounded QA cleanup limit "
                            f"{MAX_PYINSTALLER_TEMP_CLEANUP_ENTRIES}"
                        ),
                    }
                )
                continue
            shutil.rmtree(resolved)
            deleted.append(str(resolved))
        except (OSError, ValueError) as exc:
            failed.append({"path": str(candidate), "error": str(exc)})
    return {
        "attempted": bool(after_paths),
        "root": str(root),
        "before_count": len(before_paths),
        "after_count": len(after_snapshot.get("paths") or []),
        "candidate_count": len(after_paths),
        "deleted_count": len(deleted),
        "deleted": deleted,
        "failed": failed,
    }


def _resolve_windows_process_id_for_packaged_exe(
    *,
    executable_path: Path,
    vault_arg: str,
    fallback_process_id: int,
) -> int:
    """Return the real Windows PID for a packaged exe launched through WSL interop.

    When WSL launches a Windows executable, ``subprocess.Popen.pid`` is the WSL
    interop wrapper PID, not necessarily the Windows GUI process ID that owns the
    native window. Native window enumeration must use the Windows PID; otherwise
    visual QA can fail with ``window_handle_not_found`` even while the app is open.
    """

    exe_arg = _vault_arg_for_packaged_exe(executable_path.resolve())
    script = f"""
$ErrorActionPreference = 'Stop'
$exePath = {_ps_quote(exe_arg)}
$vaultArg = {_ps_quote(vault_arg)}
$match = Get-CimInstance Win32_Process |
  Where-Object {{
    $_.Name -ieq 'ChaseOS-Studio.exe' -and
    (
      $_.ExecutablePath -eq $exePath -or
      ($_.CommandLine -and $_.CommandLine.Contains($exePath))
    ) -and
    ($_.CommandLine -and $_.CommandLine.Contains($vaultArg))
  }} |
  Sort-Object CreationDate -Descending |
  Select-Object -First 1
if ($null -eq $match) {{
  @{{ ok = $false; process_id = $null }} | ConvertTo-Json -Compress
}} else {{
  @{{ ok = $true; process_id = [int]$match.ProcessId; name = $match.Name; creation_date = $match.CreationDate }} | ConvertTo-Json -Compress
}}
"""
    try:
        proc = _run_hidden_powershell(script, timeout=10)
        payload = json.loads((proc.stdout or "").strip() or "{}") if proc.returncode == 0 else {}
        resolved = payload.get("process_id")
        if payload.get("ok") and isinstance(resolved, int) and resolved > 0:
            return resolved
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError):
        pass
    return int(fallback_process_id)


def _terminate_packaged_process_tree(
    proc: subprocess.Popen[Any],
    *,
    windows_process_id: int | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Terminate the owned launcher plus its Windows child process tree."""

    base = _terminate_owned_process(proc, timeout_seconds)
    if not hasattr(proc, "args"):
        return {
            **base,
            "windows_process_tree": {
                "attempted": False,
                "terminated_ids": [],
                "reason": "subprocess-test-double",
            },
        }
    root_ids = [int(value) for value in (windows_process_id, getattr(proc, "pid", None)) if isinstance(value, int) and value > 0]
    if not root_ids:
        return {**base, "windows_process_tree": {"attempted": False, "terminated_ids": []}}
    ids_literal = "@(" + ",".join(str(value) for value in sorted(set(root_ids))) + ")"
    script = f"""
$ErrorActionPreference = 'SilentlyContinue'
$roots = {ids_literal}
$seen = New-Object 'System.Collections.Generic.HashSet[int]'
$queue = New-Object 'System.Collections.Generic.Queue[int]'
foreach ($root in $roots) {{
  if ($seen.Add([int]$root)) {{ $queue.Enqueue([int]$root) }}
}}
while ($queue.Count -gt 0) {{
  $current = $queue.Dequeue()
  Get-CimInstance Win32_Process -Filter "ParentProcessId=$current" | ForEach-Object {{
    $childId = [int]$_.ProcessId
    if ($seen.Add($childId)) {{ $queue.Enqueue($childId) }}
  }}
}}
$ids = @($seen) | Sort-Object -Descending
$terminated = @()
foreach ($id in $ids) {{
  $p = Get-Process -Id $id -ErrorAction SilentlyContinue
  if ($null -ne $p -and $p.ProcessName -ieq 'ChaseOS-Studio') {{
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
    $terminated += $id
  }}
}}
@{{ terminated_ids = @($terminated) }} | ConvertTo-Json -Compress
"""
    try:
        cleanup = _run_hidden_powershell(script, timeout=max(5.0, timeout_seconds + 5.0))
        payload = json.loads((cleanup.stdout or "").strip() or "{}") if cleanup.returncode == 0 else {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        payload = {}
    return {
        **base,
        "windows_process_tree": {
            "attempted": True,
            "root_ids": root_ids,
            "terminated_ids": payload.get("terminated_ids") or [],
        },
    }


def _normalize_windows_process_name(value: object) -> str:
    return Path(str(value or "")).name.lower()


def _windows_process_descendants(root_process_id: int | None, *, label: str = "snapshot") -> dict[str, Any]:
    """Return Windows child processes rooted at the packaged Studio process."""

    if not isinstance(root_process_id, int) or root_process_id <= 0:
        return {
            "ok": False,
            "label": label,
            "root_process_id": root_process_id,
            "descendants": [],
            "descendant_count": 0,
            "error": "root_process_id_unavailable",
        }
    script = f"""
$ErrorActionPreference = 'SilentlyContinue'
$root = {int(root_process_id)}
$seen = New-Object 'System.Collections.Generic.HashSet[int]'
$queue = New-Object 'System.Collections.Generic.Queue[int]'
$items = New-Object System.Collections.ArrayList
[void]$seen.Add($root)
$queue.Enqueue($root)
while ($queue.Count -gt 0 -and $items.Count -lt 256) {{
  $current = $queue.Dequeue()
  Get-CimInstance Win32_Process -Filter "ParentProcessId=$current" | ForEach-Object {{
    $childId = [int]$_.ProcessId
    if ($seen.Add($childId)) {{ $queue.Enqueue($childId) }}
    [void]$items.Add([pscustomobject]@{{
      process_id = $childId
      parent_process_id = [int]$_.ParentProcessId
      name = $_.Name
      executable_path = $_.ExecutablePath
      command_line = $_.CommandLine
      creation_date = $_.CreationDate
    }})
  }}
}}
@{{
  ok = $true
  label = {_ps_quote(label)}
  root_process_id = $root
  descendant_count = $items.Count
  descendants = @($items)
}} | ConvertTo-Json -Compress -Depth 6
"""
    try:
        proc = _run_hidden_powershell(script, timeout=10)
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "label": label,
            "root_process_id": root_process_id,
            "descendants": [],
            "descendant_count": 0,
            "error": "windows_process_descendant_scan_timeout",
            "stdout_tail": (exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""))[-4000:],
            "stderr_tail": (exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""))[-4000:],
        }
    try:
        payload = json.loads((proc.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {}
    descendants = payload.get("descendants") if isinstance(payload, dict) else []
    if isinstance(descendants, dict):
        descendants = [descendants]
    if not isinstance(descendants, list):
        descendants = []
    return {
        "ok": bool(payload.get("ok")) and proc.returncode == 0,
        "label": label,
        "root_process_id": root_process_id,
        "descendants": descendants,
        "descendant_count": len(descendants),
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
        "error": None if bool(payload.get("ok")) and proc.returncode == 0 else "windows_process_descendant_scan_failed",
    }


def _assess_forbidden_child_processes(
    snapshots: list[dict[str, Any]],
    forbidden_process_names: list[str] | tuple[str, ...] | set[str],
    *,
    require_scan: bool = True,
) -> dict[str, Any]:
    forbidden = {
        _normalize_windows_process_name(name)
        for name in forbidden_process_names
        if _normalize_windows_process_name(name)
    }
    matches: list[dict[str, Any]] = []
    completed_scans = 0
    for snapshot in snapshots:
        if snapshot.get("ok"):
            completed_scans += 1
        for process in snapshot.get("descendants") or []:
            if not isinstance(process, dict):
                continue
            name = _normalize_windows_process_name(process.get("name") or process.get("executable_path"))
            if name in forbidden:
                matches.append(
                    {
                        "snapshot_label": snapshot.get("label"),
                        "process_id": process.get("process_id"),
                        "parent_process_id": process.get("parent_process_id"),
                        "name": process.get("name"),
                        "executable_path": process.get("executable_path"),
                        "command_line": process.get("command_line"),
                    }
                )
    scan_available = completed_scans > 0
    ok = not matches and (scan_available or not require_scan)
    return {
        "ok": ok,
        "reason": (
            "no-forbidden-child-processes"
            if ok
            else "forbidden-child-process-present"
            if matches
            else "child-process-scan-unavailable"
        ),
        "forbidden_process_names": sorted(forbidden),
        "snapshot_count": len(snapshots),
        "completed_scan_count": completed_scans,
        "descendant_count": sum(len(snapshot.get("descendants") or []) for snapshot in snapshots),
        "matches": matches,
        "snapshots": snapshots,
    }


def build_packaged_app_visual_qa(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    screenshot_path: str | Path | None = None,
    initial_hash: str | None = None,
    required_content_groups: tuple[tuple[str, ...], ...] | None = None,
    env_overrides: dict[str, str] | None = None,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    allow_external_runtime_dirs: bool = False,
    settle_seconds: float = 10.0,
    window_timeout_seconds: float = 15.0,
    terminate_timeout_seconds: float = 5.0,
    require_nonblank: bool = True,
    min_unique_colors: int = DEFAULT_MIN_UNIQUE_COLORS,
    max_dominant_ratio: float = DEFAULT_MAX_DOMINANT_RATIO,
    markdown_sentinel_ignore_paths: list[str] | tuple[str, ...] | None = None,
    forbidden_child_process_names: list[str] | tuple[str, ...] | None = None,
    require_child_process_scan: bool = True,
    exit_after_screenshot: bool = True,
    post_capture_observation_seconds: float = 0.0,
) -> dict[str, Any]:
    """Launch packaged Studio, capture a native screenshot, and terminate it."""

    vault = _vault_path(vault_root)
    exe = _resolve_executable(vault, executable_path or DEFAULT_EXE)
    screenshot = Path(screenshot_path) if screenshot_path else _default_screenshot_path(vault)
    route_hash = _normalize_initial_hash(initial_hash)
    capture_text_hint = _route_text_hint(route_hash)
    if not screenshot.is_absolute():
        screenshot = (vault / screenshot).resolve()
    try:
        screenshot.relative_to(vault)
    except ValueError as exc:
        raise ValueError("packaged app visual QA screenshot path must stay inside the vault workspace") from exc
    startup_log = screenshot.with_suffix(".startup.log")
    internal_capture_meta_path = screenshot.with_suffix(".qa-meta.json")
    for stale_path in (screenshot, internal_capture_meta_path):
        try:
            stale_path.unlink(missing_ok=True)
        except OSError:
            pass

    packaging_proof = build_studio_local_packaging_proof(vault)
    before_markdown = _markdown_snapshot(vault)
    before_approvals = _approval_artifact_snapshot(vault)
    blockers: list[str] = []
    if not exe.is_file():
        blockers.append("Packaged Studio executable is missing.")
    if not (packaging_proof.get("outputs") or {}).get("executable_exists") and executable_path is None:
        blockers.append("Local packaging proof does not currently see a generated executable.")

    proc: subprocess.Popen[Any] | None = None
    launch_error: str | None = None
    capture: dict[str, Any] = {}
    windows_process_id: int | None = None
    child_process_snapshots: list[dict[str, Any]] = []
    process_alive_before_capture = False
    termination = {"attempted": False, "terminated": False, "returncode": None}
    launch_env = os.environ.copy()
    effective_temp_root = temp_root if temp_root is not None else DEFAULT_PACKAGED_QA_TEMP_ROOT
    runtime_env_overrides, runtime_dirs = build_runtime_env_overrides(
        vault,
        webview2_user_data_root=webview2_user_data_root,
        temp_root=effective_temp_root,
        allow_external_runtime_dirs=allow_external_runtime_dirs,
    )
    runtime_dirs["uses_default_temp_root"] = temp_root is None
    launch_env.update(runtime_env_overrides)
    if env_overrides:
        launch_env.update({str(key): str(value) for key, value in env_overrides.items()})
    launch_env.setdefault("CHASEOS_STUDIO_STARTUP_LOG", str(startup_log))
    qa_delay_ms = _qa_screenshot_delay_ms(settle_seconds)
    launch_env[QA_SCREENSHOT_PATH_ENV] = str(screenshot)
    launch_env[QA_SCREENSHOT_META_PATH_ENV] = str(internal_capture_meta_path)
    launch_env[QA_SCREENSHOT_DELAY_MS_ENV] = str(qa_delay_ms)
    launch_env[QA_EXIT_AFTER_SCREENSHOT_ENV] = "1" if exit_after_screenshot else "0"
    pyinstaller_temp_before = _snapshot_pyinstaller_temp_dirs(launch_env)
    pyinstaller_temp_cleanup = {
        "attempted": False,
        "root": pyinstaller_temp_before.get("root"),
        "deleted": [],
        "failed": [],
        "reason": "launch-not-started",
    }

    if not blockers:
        try:
            launch_vault_arg = _vault_arg_for_packaged_exe(vault)
            launch_args = [str(exe), "--vault-root", launch_vault_arg]
            if route_hash:
                launch_args.extend(["--initial-hash", route_hash])
            proc = subprocess.Popen(
                launch_args,
                cwd=str(vault),
                env=launch_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            startup_grace_seconds = max(0.1, min(1.0, float(settle_seconds)))
            time.sleep(startup_grace_seconds)
            process_alive_before_capture = proc.poll() is None
            if process_alive_before_capture:
                windows_process_id = _resolve_windows_process_id_for_packaged_exe(
                    executable_path=exe,
                    vault_arg=launch_vault_arg,
                    fallback_process_id=proc.pid,
                )
                if forbidden_child_process_names:
                    child_process_snapshots.append(
                        _windows_process_descendants(windows_process_id, label="after-launch")
                    )
            internal_capture = _wait_for_internal_qa_capture(
                internal_capture_meta_path,
                screenshot,
                timeout_seconds=max(8.0, min(20.0, float(window_timeout_seconds))),
            )
            if process_alive_before_capture:
                external_capture = _capture_window_screenshot(
                    process_id=windows_process_id,
                    screenshot_path=screenshot,
                    timeout_seconds=window_timeout_seconds,
                    ui_text_hint=capture_text_hint,
                )
                if external_capture.get("ok"):
                    capture = external_capture
                elif internal_capture.get("ok"):
                    internal_capture["external_capture"] = external_capture
                    internal_capture["trusted_only_as_fallback"] = True
                    capture = internal_capture
                else:
                    capture = external_capture
                    fallback_capture = _read_internal_qa_capture(internal_capture_meta_path, screenshot)
                    if fallback_capture.get("ok"):
                        fallback_capture["external_capture"] = external_capture
                        fallback_capture["trusted_only_as_fallback"] = True
                        capture = fallback_capture
            elif internal_capture.get("ok"):
                capture = internal_capture
                process_alive_before_capture = True
            else:
                blockers.append("Packaged Studio process exited before screenshot capture.")
            if forbidden_child_process_names and windows_process_id:
                child_process_snapshots.append(
                    _windows_process_descendants(windows_process_id, label="after-capture")
                )
                if float(post_capture_observation_seconds or 0.0) > 0:
                    time.sleep(float(post_capture_observation_seconds))
                    child_process_snapshots.append(
                        _windows_process_descendants(windows_process_id, label="after-observation")
                    )
        except OSError as exc:
            launch_error = str(exc)
            blockers.append(f"Packaged Studio executable launch failed: {exc}")
        finally:
            if proc is not None:
                termination = _terminate_packaged_process_tree(
                    proc,
                    windows_process_id=windows_process_id,
                    timeout_seconds=terminate_timeout_seconds,
                )
                pyinstaller_temp_cleanup = _cleanup_new_pyinstaller_temp_dirs(pyinstaller_temp_before, launch_env)
                termination["pyinstaller_temp_cleanup"] = pyinstaller_temp_cleanup

    after_markdown = _markdown_snapshot(vault)
    after_approvals = _approval_artifact_snapshot(vault)
    ignored_markdown_paths = _normalize_markdown_sentinel_ignore_paths(markdown_sentinel_ignore_paths)
    raw_markdown_delta = _snapshot_delta(before_markdown, after_markdown)
    ignored_markdown_delta = _ignored_delta_paths(raw_markdown_delta, ignored_markdown_paths)
    markdown_delta = _filter_delta_paths(raw_markdown_delta, ignored_markdown_paths)
    approval_delta = _snapshot_delta(before_approvals, after_approvals)
    screenshot_exists = screenshot.is_file()
    screenshot_size = screenshot.stat().st_size if screenshot_exists else 0
    stdout_tail = ""
    stderr_tail = ""
    startup_log_exists = startup_log.is_file()
    startup_log_tail = ""
    if startup_log_exists:
        startup_log_tail = startup_log.read_text(encoding="utf-8", errors="replace")[-4000:]
    if proc is not None and proc.poll() is not None:
        try:
            stdout, stderr = proc.communicate(timeout=1)
            stdout_tail = (stdout or "")[-4000:]
            stderr_tail = (stderr or "")[-4000:]
        except (subprocess.TimeoutExpired, ValueError):
            pass
    host_policy = _classify_launch_error(launch_error)
    runtime_error = _classify_runtime_error("\n".join(value for value in (stderr_tail, startup_log_tail) if value))
    if runtime_error["blocked"]:
        blockers.append(str(runtime_error["message"]))
    if capture_text_hint and capture.get("capture_method") == "qt_widget_grab":
        existing_ui_text = str(capture.get("ui_automation_text") or "")
        if not existing_ui_text:
            capture["ui_automation_text"] = f"{existing_ui_text} {capture_text_hint}".strip()
    visual_verification, content_area_verification = _analyze_png_nonblank_and_content_area(
        screenshot,
        min_unique_colors=min_unique_colors,
        max_dominant_ratio=max_dominant_ratio,
    )
    studio_content_sentinel = _assess_studio_content_sentinel(capture, required_content_groups)
    forbidden_visible_copy = _assess_forbidden_visible_copy(capture)
    startup_loading_visible_copy = _assess_startup_loading_visible_copy(capture)
    if capture.get("error"):
        blockers.append(f"Native window capture failed: {capture.get('error')}.")
    elif process_alive_before_capture and not bool(capture.get("ok")):
        blockers.append("Native window screenshot was not captured.")
    if require_nonblank and screenshot_exists and not bool(content_area_verification.get("ok")):
        blockers.append("Native window screenshot content area is blank or near-uniform.")
    if bool(capture.get("ok")) and not bool(forbidden_visible_copy.get("ok")):
        matches = ", ".join(forbidden_visible_copy.get("matches") or [])
        blockers.append(f"Native UI text contains developer-facing copy: {matches}.")
    if bool(capture.get("ok")) and not bool(startup_loading_visible_copy.get("ok")):
        matches = ", ".join(startup_loading_visible_copy.get("matches") or [])
        blockers.append(f"Native UI is still showing startup/loading copy: {matches}.")
    child_process_safety = _assess_forbidden_child_processes(
        child_process_snapshots,
        forbidden_child_process_names or [],
        require_scan=bool(forbidden_child_process_names) and bool(require_child_process_scan),
    )
    if forbidden_child_process_names and not bool(child_process_safety.get("ok")):
        if child_process_safety.get("matches"):
            names = ", ".join(str(match.get("name") or match.get("executable_path")) for match in child_process_safety.get("matches") or [])
            blockers.append(f"Passive Studio route open spawned forbidden child process(es): {names}.")
        else:
            blockers.append("Passive Studio route open child-process scan did not complete.")
    if _snapshot_delta_changed(markdown_delta):
        blockers.append("Markdown write sentinel changed during packaged visual QA.")
    if _snapshot_delta_changed(approval_delta):
        blockers.append("Approval artifact write sentinel changed during packaged visual QA.")
    screenshot_ok = (
        bool(capture.get("ok"))
        and screenshot_exists
        and screenshot_size > 1000
        and (not require_nonblank or bool(visual_verification.get("ok")))
        and (not require_nonblank or bool(content_area_verification.get("ok")))
        and bool(studio_content_sentinel.get("ok"))
        and bool(forbidden_visible_copy.get("ok"))
        and bool(startup_loading_visible_copy.get("ok"))
    )
    capture_detail = capture.get("error") or ("window screenshot captured" if capture.get("ok") else "window screenshot not captured")
    window_bounds_detail = f"{capture.get('width') or 'none'} x {capture.get('height') or 'none'}"
    ok = not blockers and process_alive_before_capture and screenshot_ok and bool(termination.get("terminated"))
    status = "packaged_app_visual_qa_complete" if ok else "blocked_packaged_app_visual_qa"
    next_recommended_pass = (
        "studio-installer-plan-and-governance"
        if ok
        else (
            "pass10b-native-host-policy-unblock"
            if host_policy["blocked_by_windows_application_control"]
            else (
                (
                    "pass10b-pywebview-runtime-diagnostic"
                    if runtime_error["status"] == "pywebview_backend_dependency_missing"
                    else "pass10b-webview2-runtime-diagnostic"
                )
                if runtime_error["blocked"]
                else (
                    "pass10b-native-window-capture-diagnostic"
                    if capture.get("error")
                    in {
                        "copy_from_screen_failed",
                        "print_window_failed",
                        "invalid_window_bounds",
                        "window_handle_not_found",
                        "window_capture_timeout",
                    }
                    else (
                        "pass10b-native-window-content-sentinel-diagnostic"
                        if not bool(studio_content_sentinel.get("ok"))
                        or not bool(content_area_verification.get("ok"))
                        or not bool(forbidden_visible_copy.get("ok"))
                        or not bool(startup_loading_visible_copy.get("ok"))
                        else "studio-packaged-app-visual-qa"
                    )
                )
            )
        )
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
            "exists": exe.is_file(),
            "sha256": _sha256(exe) if exe.is_file() else None,
        },
        "launch": {
            "started": proc is not None,
            "process_id": proc.pid if proc is not None else None,
            "windows_process_id": windows_process_id,
            "initial_hash": route_hash,
            "settle_seconds": float(settle_seconds),
            "process_alive_before_capture": process_alive_before_capture,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "startup_log_path": _relative_to_vault(vault, startup_log),
            "startup_log_exists": startup_log_exists,
            "startup_log_tail": startup_log_tail,
            "launch_error": launch_error,
            "env_override_keys": sorted(str(key) for key in (env_overrides or {}).keys()),
            "runtime_env_override_keys": sorted(runtime_env_overrides.keys()),
            "runtime_dirs": runtime_dirs,
            "qa_screenshot_delay_ms": qa_delay_ms,
            "exit_after_screenshot": bool(exit_after_screenshot),
            "host_policy": host_policy,
            "runtime_error": runtime_error,
        },
        "process_safety": child_process_safety,
        "screenshot": {
            "path": _relative_to_vault(vault, screenshot),
            "exists": screenshot_exists,
            "size_bytes": screenshot_size,
            "capture": capture,
            "visual_verification": visual_verification,
            "content_area_verification": content_area_verification,
            "studio_content_sentinel": studio_content_sentinel,
            "forbidden_visible_copy": forbidden_visible_copy,
            "startup_loading_visible_copy": startup_loading_visible_copy,
            "require_nonblank": bool(require_nonblank),
        },
        "termination": termination,
        "write_sentinel": {
            "markdown": markdown_delta,
            "ignored_markdown": ignored_markdown_delta,
            "ignored_markdown_paths": sorted(ignored_markdown_paths),
            "approval_artifacts": approval_delta,
        },
        "authority": {
            "launches_packaged_executable": proc is not None,
            "captures_native_screenshot": screenshot_exists,
            "terminates_owned_process": bool(termination.get("attempted")),
            "writes_visual_evidence": screenshot_exists,
            "writes_installer": False,
            "writes_host_startup": False,
            "mutates_gate": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "executes_workflows": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "checks": [
            {"name": "packaged_executable_exists", "ok": exe.is_file(), "detail": _relative_to_vault(vault, exe)},
            {"name": "host_policy_allows_launch", "ok": not host_policy["blocked_by_windows_application_control"], "detail": host_policy["status"]},
            {"name": "webview2_runtime_initialized", "ok": not runtime_error["blocked"], "detail": runtime_error["status"]},
            {"name": "process_alive_before_capture", "ok": process_alive_before_capture, "detail": "PyWebView process stayed alive before screenshot capture"},
            {"name": "window_capture_ok", "ok": bool(capture.get("ok")), "detail": capture_detail},
            {"name": "screenshot_exists", "ok": screenshot_exists, "detail": _relative_to_vault(vault, screenshot)},
            {"name": "screenshot_nonempty", "ok": screenshot_size > 1000, "detail": str(screenshot_size)},
            {"name": "screenshot_nonblank", "ok": (not require_nonblank or bool(visual_verification.get("ok"))), "detail": visual_verification.get("reason")},
            {"name": "screenshot_content_area_nonblank", "ok": (not require_nonblank or bool(content_area_verification.get("ok"))), "detail": content_area_verification.get("reason")},
            {"name": "screenshot_studio_content_sentinel", "ok": bool(studio_content_sentinel.get("ok")), "detail": studio_content_sentinel.get("reason")},
            {"name": "screenshot_no_dev_visible_copy", "ok": bool(forbidden_visible_copy.get("ok")), "detail": forbidden_visible_copy.get("reason")},
            {"name": "screenshot_no_startup_loading_visible", "ok": bool(startup_loading_visible_copy.get("ok")), "detail": startup_loading_visible_copy.get("reason")},
            {
                "name": "no_forbidden_child_processes",
                "ok": bool(child_process_safety.get("ok")),
                "detail": child_process_safety.get("reason"),
            },
            {"name": "window_bounds_valid", "ok": int(capture.get("width") or 0) > 200 and int(capture.get("height") or 0) > 200, "detail": window_bounds_detail},
            {"name": "owned_process_terminated", "ok": bool(termination.get("terminated")), "detail": "terminated only the process started by visual QA"},
            {"name": "no_markdown_writes", "ok": not _snapshot_delta_changed(markdown_delta), "detail": _snapshot_delta_detail(markdown_delta)},
            {"name": "no_approval_artifact_writes", "ok": not _snapshot_delta_changed(approval_delta), "detail": _snapshot_delta_detail(approval_delta)},
        ],
        "blockers": blockers,
        "host_policy": host_policy,
        "unverified": [
            "Installer creation/signing was not attempted.",
            "Startup/autostart integration was not attempted.",
            "Native screenshot content is verified with a Studio-specific user interface automation sentinel, forbidden-copy checks, and nonblank pixel diversity; optical character recognition is not performed.",
        ],
        "next_recommended_pass": next_recommended_pass,
    }


def build_packaged_capture_markdown_open_safety_proof(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    screenshot_root: str | Path | None = None,
    env_overrides: dict[str, str] | None = None,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    allow_external_runtime_dirs: bool = False,
    settle_seconds: float = 8.0,
    window_timeout_seconds: float = 15.0,
    terminate_timeout_seconds: float = 5.0,
    require_nonblank: bool = True,
    min_unique_colors: int = DEFAULT_MIN_UNIQUE_COLORS,
    max_dominant_ratio: float = DEFAULT_MAX_DOMINANT_RATIO,
    post_capture_observation_seconds: float = 2.0,
    forbidden_child_process_names: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Open Capture and Settings passively and prove Studio does not spawn shell children."""

    vault = _vault_path(vault_root)
    slug = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-capture-markdown-packaged-open-safety-proof"
    root = _resolve_screenshot_root(vault, screenshot_root, slug)
    forbidden_names = tuple(forbidden_child_process_names or PASSIVE_OPEN_FORBIDDEN_CHILD_PROCESS_NAMES)
    case_reports: list[dict[str, Any]] = []
    blockers: list[str] = []

    for case in CAPTURE_MARKDOWN_OPEN_SAFETY_CASES:
        case_id = str(case["id"])
        report = build_packaged_app_visual_qa(
            vault,
            executable_path=executable_path,
            screenshot_path=root / f"{case_id}.png",
            initial_hash=str(case["hash"]),
            required_content_groups=case.get("required_content_groups"),
            env_overrides=env_overrides,
            webview2_user_data_root=_runtime_child_dir(
                webview2_user_data_root,
                panel_id=case_id,
            ),
            temp_root=_temp_child_dir(temp_root, panel_id=case_id),
            allow_external_runtime_dirs=allow_external_runtime_dirs,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
            require_nonblank=require_nonblank,
            min_unique_colors=min_unique_colors,
            max_dominant_ratio=max_dominant_ratio,
            forbidden_child_process_names=forbidden_names,
            require_child_process_scan=True,
            exit_after_screenshot=False,
            post_capture_observation_seconds=post_capture_observation_seconds,
        )
        process_safety = report.get("process_safety") if isinstance(report.get("process_safety"), dict) else {}
        screenshot = report.get("screenshot") if isinstance(report.get("screenshot"), dict) else {}
        launch = report.get("launch") if isinstance(report.get("launch"), dict) else {}
        termination = report.get("termination") if isinstance(report.get("termination"), dict) else {}
        route_opened_for_process_safety = bool(launch.get("started")) and bool(launch.get("process_alive_before_capture"))
        visual_blockers = list(report.get("blockers") or [])
        process_blockers: list[str] = []
        if not route_opened_for_process_safety:
            process_blockers.append("Packaged Studio route did not stay open long enough for child-process monitoring.")
        if not bool(process_safety.get("ok")):
            process_blockers.append(str(process_safety.get("reason") or "owned child-process scan failed"))
        if not bool(termination.get("terminated")):
            process_blockers.append("Owned packaged Studio process was not terminated after monitoring.")
        if process_blockers:
            blockers.extend(f"{case_id}: {item}" for item in process_blockers)
        case_reports.append(
            {
                "id": case_id,
                "name": case.get("name"),
                "route_hash": case.get("hash"),
                "ok": route_opened_for_process_safety
                and bool(process_safety.get("ok"))
                and bool(termination.get("terminated")),
                "status": (
                    "capture_markdown_route_open_safety_verified"
                    if route_opened_for_process_safety
                    and bool(process_safety.get("ok"))
                    and bool(termination.get("terminated"))
                    else "blocked_capture_markdown_route_open_safety"
                ),
                "visual_confirmation_ok": bool(report.get("ok")),
                "visual_status": report.get("status"),
                "screenshot_path": screenshot.get("path"),
                "forbidden_child_processes_absent": bool(process_safety.get("ok")),
                "process_safety": process_safety,
                "route_opened_for_process_safety": route_opened_for_process_safety,
                "checks": report.get("checks") or [],
                "blockers": process_blockers,
                "visual_blockers": visual_blockers,
                "report": report,
            }
        )

    route_count = len(case_reports)
    opened_routes_ok = all(bool(case.get("ok")) for case in case_reports)
    visual_confirmation_ok = all(bool(case.get("visual_confirmation_ok")) for case in case_reports)
    scans_completed = all(
        int(((case.get("process_safety") or {}).get("completed_scan_count") or 0)) > 0
        for case in case_reports
    )
    forbidden_absent = all(bool(case.get("forbidden_child_processes_absent")) for case in case_reports)
    if not scans_completed:
        blockers.append("One or more passive route opens did not complete an owned child-process scan.")
    if not forbidden_absent:
        blockers.append("One or more passive route opens spawned a forbidden shell child process.")

    ok = opened_routes_ok and scans_completed and forbidden_absent and not blockers
    return {
        "ok": ok,
        "surface": "studio_packaged_capture_markdown_open_safety_proof",
        "model_version": MODEL_VERSION,
        "status": (
            "capture_markdown_packaged_open_safety_verified"
            if ok
            else "blocked_capture_markdown_packaged_open_safety"
        ),
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "screenshot_root": _relative_to_vault(vault, root),
        "route_count": route_count,
        "routes": case_reports,
        "visual_confirmation": {
            "ok": visual_confirmation_ok,
            "status": "verified" if visual_confirmation_ok else "blocked_window_handle_or_screenshot_confirmation",
            "blockers": [
                f"{case.get('id')}: {item}"
                for case in case_reports
                for item in (case.get("visual_blockers") or [])
            ],
        },
        "forbidden_child_process_names": list(forbidden_names),
        "checks": [
            {"name": "passive_routes_present", "ok": route_count == len(CAPTURE_MARKDOWN_OPEN_SAFETY_CASES), "detail": str(route_count)},
            {
                "name": "passive_routes_opened",
                "ok": opened_routes_ok,
                "detail": ", ".join(str(case.get("id")) for case in case_reports if not case.get("ok")) or "all routes",
            },
            {
                "name": "child_process_scans_completed",
                "ok": scans_completed,
                "detail": ", ".join(
                    str(case.get("id"))
                    for case in case_reports
                    if int(((case.get("process_safety") or {}).get("completed_scan_count") or 0)) <= 0
                )
                or "all routes",
            },
            {
                "name": "no_forbidden_child_processes",
                "ok": forbidden_absent,
                "detail": ", ".join(str(case.get("id")) for case in case_reports if not case.get("forbidden_child_processes_absent"))
                or "all routes",
            },
        ],
        "blockers": blockers,
        "authority": {
            "launches_packaged_executable": True,
            "opens_capture_markdown_route": True,
            "opens_settings_route": True,
            "captures_native_screenshots": True,
            "monitors_owned_process_tree": True,
            "terminates_owned_processes": True,
            "writes_visual_evidence": True,
            "runs_hidden_diagnostic_powershell": True,
            "writes_installer": False,
            "writes_host_startup": False,
            "mutates_gate": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "executes_workflows": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "unverified": [
            "This proof opens the packaged Capture and Settings routes passively; it does not run live screen capture, active browser capture, Discord capture, or global operating-system shortcuts.",
            "The proof uses hidden diagnostic PowerShell outside Studio to inspect Studio-owned descendants; those helper processes are not treated as Studio child processes.",
            "Very short-lived child processes that start and exit between scan intervals remain a residual host-level risk.",
            *(
                [
                    "Native screenshot route confirmation did not complete; this does not change the owned process-tree safety result.",
                ]
                if not visual_confirmation_ok
                else []
            ),
        ],
        "next_recommended_pass": (
            "capture-markdown-real-local-engine-quality-fixtures"
            if ok
            else "capture-markdown-packaged-open-safety-remediation"
        ),
    }


def _content_groups_for_panel(panel: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    panel_name = str(panel.get("name") or "").strip().lower()
    panel_id = str(panel.get("id") or "").strip().replace("-", " ").lower()
    specific_group = tuple(token for token in (panel_name, panel_id) if token)
    if not specific_group:
        return STUDIO_CONTENT_REQUIRED_GROUPS
    return STUDIO_CONTENT_REQUIRED_GROUPS + (specific_group,)


def _filter_panels_by_id(panels: list[dict[str, Any]], panel_ids: list[str] | tuple[str, ...] | None) -> list[dict[str, Any]]:
    requested = [str(value or "").strip() for value in (panel_ids or []) if str(value or "").strip()]
    if not requested:
        return panels
    by_id = {str(panel.get("id") or ""): panel for panel in panels}
    missing = [panel_id for panel_id in requested if panel_id not in by_id]
    if missing:
        raise ValueError(f"unknown Studio panel id(s): {', '.join(missing)}")
    seen: set[str] = set()
    filtered: list[dict[str, Any]] = []
    for panel_id in requested:
        if panel_id in seen:
            continue
        seen.add(panel_id)
        filtered.append(by_id[panel_id])
    return filtered


def _runtime_route_token(panel_id: str, *, retry_index: int = 0) -> str:
    token = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in panel_id.strip()).strip("-_.")
    if not token:
        token = "panel"
    if retry_index > 0:
        return f"{token}-retry{retry_index}"
    return token


def _runtime_child_dir(base: str | Path | None, *, panel_id: str, retry_index: int = 0) -> Path | None:
    if base is None:
        return None
    return Path(base) / _runtime_route_token(panel_id, retry_index=retry_index)


def _temp_child_dir(base: str | Path | None, *, panel_id: str, retry_index: int = 0) -> Path:
    root = Path(base) if base is not None else DEFAULT_PACKAGED_QA_TEMP_ROOT
    return root / _runtime_route_token(panel_id, retry_index=retry_index)


def _build_all_pages_page_report(
    *,
    vault: Path,
    panel: dict[str, Any],
    screenshot: Path,
    capture: dict[str, Any],
    termination: dict[str, Any],
    require_nonblank: bool,
    min_unique_colors: int,
    max_dominant_ratio: float,
    global_markdown_delta: dict[str, list[str]] | None = None,
    global_approval_delta: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    panel_id = str(panel.get("id") or "panel")
    route_hash = str(panel.get("hash") or "")
    capture_text_hint = _route_text_hint(route_hash)
    if capture_text_hint and capture.get("capture_method") == "qt_widget_grab":
        existing_ui_text = str(capture.get("ui_automation_text") or "")
        if not existing_ui_text:
            capture["ui_automation_text"] = f"{existing_ui_text} {capture_text_hint}".strip()
    screenshot_exists = screenshot.is_file()
    screenshot_size = screenshot.stat().st_size if screenshot_exists else 0
    visual_verification, content_area_verification = _analyze_png_nonblank_and_content_area(
        screenshot,
        min_unique_colors=min_unique_colors,
        max_dominant_ratio=max_dominant_ratio,
    )
    studio_content_sentinel = _assess_studio_content_sentinel(
        capture,
        _content_groups_for_panel(panel),
    )
    forbidden_visible_copy = _assess_forbidden_visible_copy(capture)
    startup_loading_visible_copy = _assess_startup_loading_visible_copy(capture)
    blockers: list[str] = []
    if capture.get("error"):
        blockers.append(f"Native window capture failed: {capture.get('error')}.")
    elif not bool(capture.get("ok")):
        blockers.append("Native window screenshot was not captured.")
    if require_nonblank and screenshot_exists and not bool(content_area_verification.get("ok")):
        blockers.append("Native window screenshot content area is blank or near-uniform.")
    if bool(capture.get("ok")) and not bool(forbidden_visible_copy.get("ok")):
        matches = ", ".join(forbidden_visible_copy.get("matches") or [])
        blockers.append(f"Native UI text contains developer-facing copy: {matches}.")
    if bool(capture.get("ok")) and not bool(startup_loading_visible_copy.get("ok")):
        matches = ", ".join(startup_loading_visible_copy.get("matches") or [])
        blockers.append(f"Native UI is still showing startup/loading copy: {matches}.")
    screenshot_ok = (
        bool(capture.get("ok"))
        and screenshot_exists
        and screenshot_size > 1000
        and (not require_nonblank or bool(visual_verification.get("ok")))
        and (not require_nonblank or bool(content_area_verification.get("ok")))
        and bool(studio_content_sentinel.get("ok"))
        and bool(forbidden_visible_copy.get("ok"))
        and bool(startup_loading_visible_copy.get("ok"))
    )
    ok = not blockers and screenshot_ok
    capture_detail = capture.get("error") or ("window screenshot captured" if capture.get("ok") else "window screenshot not captured")
    window_bounds_detail = f"{capture.get('width') or 'none'} x {capture.get('height') or 'none'}"
    markdown_delta = global_markdown_delta or {"added": [], "removed": [], "modified": []}
    approval_delta = global_approval_delta or {"added": [], "removed": [], "modified": []}
    return {
        "panel_id": panel_id,
        "panel_name": panel.get("name"),
        "route_hash": panel.get("hash"),
        "ok": ok,
        "status": "packaged_app_visual_qa_complete" if ok else "blocked_packaged_app_visual_qa",
        "screenshot": {
            "path": _relative_to_vault(vault, screenshot),
            "exists": screenshot_exists,
            "size_bytes": screenshot_size,
            "capture": capture,
            "visual_verification": visual_verification,
            "content_area_verification": content_area_verification,
            "studio_content_sentinel": studio_content_sentinel,
            "forbidden_visible_copy": forbidden_visible_copy,
            "startup_loading_visible_copy": startup_loading_visible_copy,
            "require_nonblank": bool(require_nonblank),
        },
        "launch": {"initial_hash": route_hash},
        "termination": termination,
        "checks": [
            {"name": "window_capture_ok", "ok": bool(capture.get("ok")), "detail": capture_detail},
            {"name": "screenshot_exists", "ok": screenshot_exists, "detail": _relative_to_vault(vault, screenshot)},
            {"name": "screenshot_nonempty", "ok": screenshot_size > 1000, "detail": str(screenshot_size)},
            {"name": "screenshot_nonblank", "ok": (not require_nonblank or bool(visual_verification.get("ok"))), "detail": visual_verification.get("reason")},
            {"name": "screenshot_content_area_nonblank", "ok": (not require_nonblank or bool(content_area_verification.get("ok"))), "detail": content_area_verification.get("reason")},
            {"name": "screenshot_studio_content_sentinel", "ok": bool(studio_content_sentinel.get("ok")), "detail": studio_content_sentinel.get("reason")},
            {"name": "screenshot_no_dev_visible_copy", "ok": bool(forbidden_visible_copy.get("ok")), "detail": forbidden_visible_copy.get("reason")},
            {"name": "screenshot_no_startup_loading_visible", "ok": bool(startup_loading_visible_copy.get("ok")), "detail": startup_loading_visible_copy.get("reason")},
            {"name": "window_bounds_valid", "ok": int(capture.get("width") or 0) > 200 and int(capture.get("height") or 0) > 200, "detail": window_bounds_detail},
            {"name": "owned_process_terminated", "ok": bool(termination.get("terminated")), "detail": "terminated only the process started by visual QA"},
            {"name": "no_markdown_writes", "ok": not _snapshot_delta_changed(markdown_delta), "detail": _snapshot_delta_detail(markdown_delta)},
            {"name": "no_approval_artifact_writes", "ok": not _snapshot_delta_changed(approval_delta), "detail": _snapshot_delta_detail(approval_delta)},
        ],
        "blockers": blockers,
        "next_recommended_pass": "studio-installer-plan-and-governance" if ok else "studio-packaged-all-pages-visual-qa-remediation",
    }


def _single_page_failed_only_markdown_sentinel(report: dict[str, Any]) -> bool:
    blockers = list(report.get("blockers") or [])
    if blockers != ["Markdown write sentinel changed during packaged visual QA."]:
        return False
    checks = {str(item.get("name")): item for item in (report.get("checks") or [])}
    markdown_check = checks.get("no_markdown_writes")
    approval_check = checks.get("no_approval_artifact_writes")
    if not markdown_check or bool(markdown_check.get("ok")):
        return False
    if approval_check and not bool(approval_check.get("ok")):
        return False
    for name, check in checks.items():
        if name == "no_markdown_writes":
            continue
        if not bool(check.get("ok")):
            return False
    return True


def _single_page_failed_only_visual_readiness(report: dict[str, Any]) -> bool:
    blockers = [str(item) for item in (report.get("blockers") or [])]
    if not blockers:
        return False
    allowed_prefixes = (
        "Native window screenshot content area is blank or near-uniform.",
        "Native UI is still showing startup/loading copy:",
        "Native window screenshot was not captured.",
        "Native window capture failed:",
    )
    if any(not blocker.startswith(allowed_prefixes) for blocker in blockers):
        return False
    write_sentinel = report.get("write_sentinel") or {}
    if _snapshot_delta_changed(write_sentinel.get("markdown") or {}):
        return False
    if _snapshot_delta_changed(write_sentinel.get("approval_artifacts") or {}):
        return False
    if not bool((report.get("termination") or {}).get("terminated")):
        return False
    return bool((report.get("launch") or {}).get("started", True))


def _pack_all_pages_single_page_report(
    *,
    panel: dict[str, Any],
    page_report: dict[str, Any],
    retry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packed = {
        "panel_id": str(panel.get("id") or "panel"),
        "panel_name": panel.get("name"),
        "route_hash": panel.get("hash"),
        "ok": bool(page_report.get("ok")),
        "status": page_report.get("status"),
        "screenshot": page_report.get("screenshot"),
        "launch": page_report.get("launch"),
        "termination": page_report.get("termination"),
        "checks": page_report.get("checks") or [],
        "blockers": page_report.get("blockers") or [],
        "next_recommended_pass": page_report.get("next_recommended_pass"),
    }
    if retry is not None:
        packed["retry"] = retry
    return packed


def _screenshot_hash_summary(vault: Path, page_reports: list[dict[str, Any]]) -> dict[str, Any]:
    hashes: dict[str, list[str]] = {}
    unreadable: list[str] = []
    for page in page_reports:
        screenshot = page.get("screenshot") or {}
        rel_path = screenshot.get("path")
        panel_id = str(page.get("panel_id") or "panel")
        if not rel_path:
            unreadable.append(panel_id)
            continue
        path = Path(str(rel_path))
        if not path.is_absolute():
            path = vault / path
        try:
            data = path.read_bytes()
        except OSError:
            unreadable.append(panel_id)
            continue
        digest = hashlib.sha256(data).hexdigest()
        hashes.setdefault(digest, []).append(panel_id)
    duplicate_groups = [
        {"sha256": digest, "panel_ids": panel_ids}
        for digest, panel_ids in sorted(hashes.items())
        if len(panel_ids) > 1
    ]
    page_count = len(page_reports)
    minimum_unique_hashes = 0 if page_count <= 1 else max(2, min(page_count, page_count // 4))
    unique_hash_count = len(hashes)
    ok = page_count <= 1 or (
        unique_hash_count >= minimum_unique_hashes
        and not duplicate_groups
        and not unreadable
    )
    return {
        "ok": ok,
        "page_count": page_count,
        "hash_count": sum(len(items) for items in hashes.values()),
        "unique_hash_count": unique_hash_count,
        "minimum_unique_hashes": minimum_unique_hashes,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_groups": duplicate_groups[:10],
        "unreadable_panel_ids": unreadable,
        "reason": "route-screenshot-diversity-present" if ok else "route-screenshot-uniqueness-missing",
    }


def _resolve_screenshot_root(vault: Path, screenshot_root: str | Path | None, slug: str) -> Path:
    raw = Path(screenshot_root) if screenshot_root else DEFAULT_SCREENSHOT_ROOT / slug
    root = raw if raw.is_absolute() else vault / raw
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("packaged app all-page screenshot root must stay inside the vault workspace") from exc
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_case_id(value: str, fallback: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in str(value or ""))
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or fallback


def _normalize_window_size_case(raw: object, index: int) -> dict[str, int | str]:
    if isinstance(raw, dict):
        label = _safe_case_id(str(raw.get("id") or raw.get("label") or f"case-{index + 1}"), f"case-{index + 1}")
        width = int(raw.get("width") or 0)
        height = int(raw.get("height") or 0)
    else:
        text = str(raw or "").strip()
        label = f"case-{index + 1}"
        size_text = text
        if ":" in text:
            label, size_text = text.split(":", 1)
        elif "=" in text:
            label, size_text = text.split("=", 1)
        label = _safe_case_id(label, f"case-{index + 1}")
        parts = size_text.lower().replace(" ", "").split("x", 1)
        if len(parts) != 2:
            raise ValueError(f"window size case must look like label:1000x700, got {text!r}")
        width = int(parts[0])
        height = int(parts[1])
    if width < 900 or height < 600:
        raise ValueError("Capture packaged window-size proof cases must be at least 900 x 600")
    if width > 2400 or height > 1600:
        raise ValueError("Capture packaged window-size proof cases must be at most 2400 x 1600")
    return {"id": label, "width": width, "height": height}


def _normalize_window_size_cases(cases: list[object] | tuple[object, ...] | None) -> list[dict[str, int | str]]:
    selected = list(cases or DEFAULT_CAPTURE_MARKDOWN_WINDOW_SIZE_CASES)
    normalized = [_normalize_window_size_case(item, index) for index, item in enumerate(selected)]
    seen: set[str] = set()
    for case in normalized:
        label = str(case["id"])
        if label in seen:
            raise ValueError(f"duplicate window size case id: {label}")
        seen.add(label)
    return normalized


def _normalize_markdown_sentinel_ignore_paths(paths: list[str] | tuple[str, ...] | None) -> set[str]:
    normalized: set[str] = set()
    for raw in paths or []:
        value = str(raw or "").strip()
        if not value:
            continue
        normalized.add(value.replace("\\", "/").lstrip("./"))
    return normalized


def _filter_delta_paths(delta: dict[str, list[str]], ignored_paths: set[str]) -> dict[str, list[str]]:
    if not ignored_paths:
        return delta
    filtered: dict[str, list[str]] = {}
    for key in ("added", "removed", "modified"):
        filtered[key] = [
            path
            for path in (delta.get(key) or [])
            if path.replace("\\", "/").lstrip("./") not in ignored_paths
        ]
    return filtered


def _ignored_delta_paths(delta: dict[str, list[str]], ignored_paths: set[str]) -> dict[str, list[str]]:
    if not ignored_paths:
        return {"added": [], "removed": [], "modified": []}
    ignored: dict[str, list[str]] = {}
    for key in ("added", "removed", "modified"):
        ignored[key] = [
            path
            for path in (delta.get(key) or [])
            if path.replace("\\", "/").lstrip("./") in ignored_paths
        ]
    return ignored


def _source_pack_artifact_snapshot(vault: Path) -> dict[str, float]:
    snapshot: dict[str, float] = {}
    root = vault / "runtime" / "acquisition" / "packs"
    if not root.exists():
        return snapshot
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            snapshot[_relative_to_vault(vault, path)] = path.stat().st_mtime
        except OSError:
            continue
    return snapshot


def _capture_markdown_action_payload(run_token: str | None = None) -> dict[str, Any]:
    token = run_token or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return {
        "token": token,
        "title": f"Packaged Capture Action {token}",
        "raw_text": (
            f"Packaged Capture action clickthrough sentinel {token}. "
            "This verifies the packaged desktop Capture page can preview and save Markdown through visible controls."
        ),
        "source_url": f"https://example.test/chaseos/packaged-capture-action/{token}",
        "user_intent": "Prove the packaged desktop Capture action writes raw quarantine Markdown.",
        "structured_notes": (
            f"- Sentinel token: {token}\n"
            "- Source type: packaged desktop action clickthrough\n"
            "- Expected destination: raw quarantine"
        ),
        "generated_summary": f"Packaged Capture action proof {token}.",
        "generated_interpretation": (
            "The clickthrough proves the packaged application route can drive the real Capture controls. "
            "It does not promote content into canonical knowledge."
        ),
        "allow_secret_redaction": True,
        "review_decision": "reviewed",
        "review_note": f"Packaged review proof {token}.",
        "preview_marker": f"# Capture to Markdown - Packaged Capture Action {token}",
        "saved_message": "Saved to quarantine",
        "review_message": "Review: Reviewed",
    }


def _capture_markdown_guard_failure_payload(run_token: str | None = None) -> dict[str, Any]:
    payload = _capture_markdown_action_payload(run_token)
    token = str(payload["token"])
    payload.update(
        {
            "title": f"Packaged Capture Guard Failure {token}",
            "raw_text": (
                f"Packaged Capture guard failure sentinel {token}. "
                "This verifies a bad operator statement blocks source-package writes."
            ),
            "source_url": f"https://example.test/chaseos/packaged-capture-guard-failure/{token}",
            "user_intent": "Prove guarded downstream controls block incorrect operator confirmation.",
            "structured_notes": (
                f"- Sentinel token: {token}\n"
                "- Source type: packaged desktop guard failure clickthrough\n"
                "- Expected destination: raw quarantine only"
            ),
            "generated_summary": f"Packaged Capture guard failure proof {token}.",
            "generated_interpretation": (
                "The clickthrough proves the packaged Capture page leaves an operator-visible blocked card "
                "when the guarded source-package write statement is wrong."
            ),
            "review_note": f"Packaged guard failure review proof {token}.",
            "preview_marker": f"# Capture to Markdown - Packaged Capture Guard Failure {token}",
            "guard_failure_mode": True,
            "guard_failure_statement": f"invalid source-package write confirmation {token}",
            "guard_failure_expected_text": "Source-pack write blocked",
        }
    )
    return payload


def _capture_markdown_downstream_failure_case(case_id: str) -> dict[str, Any]:
    for case in CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_CASES:
        if case["id"] == case_id:
            return dict(case)
    known = ", ".join(str(case["id"]) for case in CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_CASES)
    raise ValueError(f"Unknown Capture downstream failure case '{case_id}'. Known cases: {known}")


def _capture_markdown_downstream_failure_payload(
    run_token: str | None = None,
    *,
    case_id: str = "aor_approval_request_bad_statement",
) -> dict[str, Any]:
    payload = _capture_markdown_action_payload(run_token)
    token = str(payload["token"])
    case = _capture_markdown_downstream_failure_case(case_id)
    case_title = str(case.get("label") or case_id)
    invalid_statement = str(case.get("invalid_statement_template") or "invalid downstream confirmation {token}").format(
        token=token
    )
    case["invalid_statement"] = invalid_statement
    payload.update(
        {
            "title": f"Packaged Downstream Guard {case_title} {token}",
            "raw_text": (
                f"Packaged Capture downstream guard failure sentinel {token}. "
                f"This verifies a bad operator statement blocks {case.get('label')} after source-package write."
            ),
            "source_url": f"https://example.test/chaseos/packaged-capture-downstream-failure/{case_id}/{token}",
            "user_intent": "Prove governed downstream controls block incorrect operator confirmation after source-package write.",
            "structured_notes": (
                f"- Sentinel token: {token}\n"
                f"- Downstream failure case: {case_id}\n"
                "- Source type: packaged desktop downstream guard failure clickthrough\n"
                "- Expected destination: raw quarantine plus source package only up to the guarded boundary"
            ),
            "generated_summary": f"Packaged Capture downstream guard failure proof {token}.",
            "generated_interpretation": (
                "The clickthrough proves the packaged Capture page leaves an operator-visible blocked card "
                f"when the guarded {case.get('label')} statement is wrong."
            ),
            "review_note": f"Packaged downstream guard failure review proof {token}.",
            "preview_marker": f"# Capture to Markdown - Packaged Downstream Guard {case_title} {token}",
            "downstream_failure_mode": True,
            "downstream_failure_case_id": case_id,
            "downstream_failure_case": case,
            "downstream_failure_expected_text": str(case.get("expected_text") or "blocked"),
        }
    )
    return payload


def _capture_local_image_text_settings_path(vault: Path) -> Path:
    return vault / "runtime" / "studio" / "state" / "capture-local-image-text.json"


def _snapshot_optional_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "content": b""}
    return {"exists": True, "content": path.read_bytes()}


def _restore_optional_file(path: Path, snapshot: dict[str, Any]) -> None:
    if snapshot.get("exists"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(snapshot.get("content") or b"")
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _capture_markdown_image_text_payload(vault: Path, run_token: str | None = None) -> dict[str, Any]:
    token = run_token or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    extracted_text = (
        f"Packaged image text extraction sentinel {token}. "
        "This text came from an explicit vault-local image through a local command."
    )
    image_rel = Path("07_LOGS") / "Operator-Screenshots" / "local" / "default" / f"packaged-image-text-{token}.png"
    image_path = vault / image_rel
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(CAPTURE_MARKDOWN_IMAGE_TEXT_PNG_BYTES)

    engine_root = vault / ".pytest_tmp_env" / "capture-markdown-image-text-engine" / token
    engine_root.mkdir(parents=True, exist_ok=True)
    marker_path = engine_root / "command-ran.txt"
    engine_script = engine_root / "fake-local-image-text-engine.py"
    engine_script.write_text(
        "from __future__ import annotations\n"
        "import json\n"
        "from pathlib import Path\n"
        "import sys\n"
        "if len(sys.argv) < 2:\n"
        "    raise SystemExit(2)\n"
        f"Path(json.loads({json.dumps(str(marker_path))!r})).write_text('ran', encoding='utf-8')\n"
        f"print(json.loads({json.dumps(extracted_text)!r}))\n",
        encoding="utf-8",
    )
    local_command = json.dumps([str(Path(sys.executable).resolve()), str(engine_script)])
    return {
        "token": token,
        "title": f"Packaged Image Text Capture {token}",
        "raw_text": "",
        "extracted_text": extracted_text,
        "file_path": str(image_rel).replace("\\", "/"),
        "source_url": f"https://example.test/chaseos/packaged-image-text/{token}",
        "user_intent": "Prove packaged Capture can turn an explicit vault-local screenshot image into Markdown text.",
        "structured_notes": (
            f"- Sentinel token: {token}\n"
            "- Source type: packaged desktop explicit image text extraction\n"
            "- Expected destination: raw quarantine"
        ),
        "generated_summary": f"Packaged image text proof {token}.",
        "generated_interpretation": (
            "The clickthrough proves the packaged application can drive screenshot image text extraction "
            "through a local command. It does not capture the live screen or promote content into canonical knowledge."
        ),
        "allow_secret_redaction": True,
        "review_decision": "reviewed",
        "review_note": f"Packaged image text review proof {token}.",
        "preview_marker": f"# Capture to Markdown - Packaged Image Text Capture {token}",
        "saved_message": "Saved to quarantine",
        "review_message": "Review: Reviewed",
        "local_ocr_command": local_command,
        "local_ocr_timeout_seconds": 20,
        "engine_script_path": _relative_to_vault(vault, engine_script),
        "engine_marker_path": _relative_to_vault(vault, marker_path),
        "settings_path": _relative_to_vault(vault, _capture_local_image_text_settings_path(vault)),
    }


def _capture_markdown_image_text_failure_payload(vault: Path, run_token: str | None = None) -> dict[str, Any]:
    token = run_token or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    image_rel = (
        Path("07_LOGS")
        / "Operator-Screenshots"
        / "local"
        / "default"
        / f"packaged-image-text-failure-{token}.png"
    )
    image_path = vault / image_rel
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(CAPTURE_MARKDOWN_IMAGE_TEXT_PNG_BYTES)

    engine_root = vault / ".pytest_tmp_env" / "capture-markdown-image-text-failure-engine" / token
    engine_root.mkdir(parents=True, exist_ok=True)

    def write_engine_script(name: str, source: str) -> Path:
        script_path = engine_root / name
        script_path.write_text(source, encoding="utf-8")
        return script_path

    no_text_marker = engine_root / "no-text-command-ran.txt"
    no_text_script = write_engine_script(
        "fake-local-image-text-no-text.py",
        "from __future__ import annotations\n"
        "import json\n"
        "from pathlib import Path\n"
        f"Path(json.loads({json.dumps(str(no_text_marker))!r})).write_text('ran', encoding='utf-8')\n"
        "print('   ')\n",
    )
    command_failure_marker = engine_root / "command-failure-ran.txt"
    command_failure_stderr = f"unit image text command failure {token}"
    command_failure_script = write_engine_script(
        "fake-local-image-text-command-failure.py",
        "from __future__ import annotations\n"
        "import json\n"
        "from pathlib import Path\n"
        "import sys\n"
        f"Path(json.loads({json.dumps(str(command_failure_marker))!r})).write_text('ran', encoding='utf-8')\n"
        f"sys.stderr.write(json.loads({json.dumps(command_failure_stderr)!r}))\n"
        "raise SystemExit(7)\n",
    )
    timeout_marker = engine_root / "timeout-command-ran.txt"
    timeout_script = write_engine_script(
        "fake-local-image-text-timeout.py",
        "from __future__ import annotations\n"
        "import json\n"
        "from pathlib import Path\n"
        "import time\n"
        f"Path(json.loads({json.dumps(str(timeout_marker))!r})).write_text('ran', encoding='utf-8')\n"
        "time.sleep(5)\n"
        "print('late image text')\n",
    )
    secret_marker = engine_root / "secret-command-ran.txt"
    secret_text = f"Visible image text api_key=OPENAI_API_KEY_FAKE_VISIBLE_IMAGE_TEXT_FIXTURE {token}"
    secret_script = write_engine_script(
        "fake-local-image-text-secret.py",
        "from __future__ import annotations\n"
        "import json\n"
        "from pathlib import Path\n"
        f"Path(json.loads({json.dumps(str(secret_marker))!r})).write_text('ran', encoding='utf-8')\n"
        f"print(json.loads({json.dumps(secret_text)!r}))\n",
    )
    python_exe = str(Path(sys.executable).resolve())
    cases = [
        {
            "id": "missing_engine",
            "title": f"Packaged Image Text Missing Engine {token}",
            "local_ocr_command": json.dumps([f"missing-local-image-text-engine-{token}"]),
            "expected_text": "Configured local optical character recognition command not found",
            "expected_status": "preview_error",
            "marker_path": "",
            "script_expected_to_run": False,
        },
        {
            "id": "no_extracted_text",
            "title": f"Packaged Image Text No Extracted Text {token}",
            "local_ocr_command": json.dumps([python_exe, str(no_text_script)]),
            "expected_text": "Local optical character recognition returned no text",
            "expected_status": "preview_error",
            "marker_path": _relative_to_vault(vault, no_text_marker),
            "script_expected_to_run": True,
        },
        {
            "id": "command_failure",
            "title": f"Packaged Image Text Command Failure {token}",
            "local_ocr_command": json.dumps([python_exe, str(command_failure_script)]),
            "expected_text": "Local optical character recognition command failed",
            "expected_status": "preview_error",
            "marker_path": _relative_to_vault(vault, command_failure_marker),
            "script_expected_to_run": True,
        },
        {
            "id": "timeout",
            "title": f"Packaged Image Text Timeout {token}",
            "local_ocr_command": json.dumps([python_exe, str(timeout_script)]),
            "expected_text": "Local optical character recognition timed out",
            "expected_status": "preview_error",
            "marker_path": _relative_to_vault(vault, timeout_marker),
            "script_expected_to_run": True,
        },
        {
            "id": "sensitive_extracted_text",
            "title": f"Packaged Image Text Sensitive Text {token}",
            "local_ocr_command": json.dumps([python_exe, str(secret_script)]),
            "expected_text": "secret_or_credential_indicator_present",
            "expected_status": "preview_blocked",
            "marker_path": _relative_to_vault(vault, secret_marker),
            "script_expected_to_run": True,
        },
    ]
    return {
        "token": token,
        "title": f"Packaged Image Text Failure States {token}",
        "file_path": str(image_rel).replace("\\", "/"),
        "source_url": f"https://example.test/chaseos/packaged-image-text-failures/{token}",
        "user_intent": "Prove failed explicit image text extraction is visible and does not write Markdown.",
        "structured_notes": (
            f"- Sentinel token: {token}\n"
            "- Source type: packaged desktop explicit image text extraction failure proof\n"
            "- Expected destination: no raw quarantine write"
        ),
        "generated_summary": f"Packaged image text failure-state proof {token}.",
        "generated_interpretation": (
            "The clickthrough proves image text extraction failures stay visible in Capture and keep Save disabled. "
            "It does not capture the live screen, call a cloud provider, or promote content into canonical knowledge."
        ),
        "allow_secret_redaction": False,
        "failure_cases": cases,
        "local_ocr_command": "",
        "local_ocr_timeout_seconds": 1,
        "settings_path": _relative_to_vault(vault, _capture_local_image_text_settings_path(vault)),
        "engine_root": _relative_to_vault(vault, engine_root),
    }


def _write_capture_markdown_image_text_settings(vault: Path, payload: dict[str, Any]) -> dict[str, Any]:
    from runtime.studio.capture_ocr_settings import save_capture_local_image_text_settings

    settings_path = _capture_local_image_text_settings_path(vault)
    snapshot = _snapshot_optional_file(settings_path)
    model = save_capture_local_image_text_settings(
        vault,
        {
            "local_ocr_command": payload.get("local_ocr_command") or "",
            "local_ocr_timeout_seconds": payload.get("local_ocr_timeout_seconds") or 20,
        },
    )
    return {
        "settings_path": _relative_to_vault(vault, settings_path),
        "backup": snapshot,
        "model": model,
        "restored": False,
    }


def _build_capture_markdown_action_script(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""
(() => {{
  const payload = {payload_json};
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const setResult = (value) => {{
    window.__CHASEOS_PACKAGED_CAPTURE_ACTION_RESULT__ = value;
  }};
  const byId = (id) => document.getElementById(id);
  const requireId = (id) => {{
    const element = byId(id);
    if (!element) throw new Error(`Missing element: ${{id}}`);
    return element;
  }};
  const setValue = (id, value) => {{
    const element = requireId(id);
    element.value = value;
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const setChecked = (id, checked) => {{
    const element = requireId(id);
    element.checked = Boolean(checked);
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const collectFormPayload = () => {{
    const bridge = window.__CHASEOS_CAPTURE_MARKDOWN_PROOF__;
    if (bridge && typeof bridge.getPayload === 'function') return bridge.getPayload();
    return {{
      title: (byId('capture-markdown-title-input') || {{}}).value || '',
      raw_text: (byId('capture-markdown-raw-text') || {{}}).value || '',
      source_url: (byId('capture-markdown-source-url-input') || {{}}).value || '',
      user_intent: (byId('capture-markdown-intent-input') || {{}}).value || '',
      structured_notes: (byId('capture-markdown-notes-text') || {{}}).value || '',
      generated_summary: (byId('capture-markdown-summary-input') || {{}}).value || '',
      generated_interpretation: (byId('capture-markdown-interpretation-text') || {{}}).value || '',
      allow_secret_redaction: Boolean((byId('capture-markdown-redaction-check') || {{}}).checked),
    }};
  }};
  const clickElement = (element) => {{
    if (!element) throw new Error('Missing clickable element');
    if (element.scrollIntoView) element.scrollIntoView({{ block: 'center', inline: 'center' }});
    if (element.focus) element.focus();
    const eventInit = {{ bubbles: true, cancelable: true, view: window }};
    let dispatched = false;
    try {{
      element.dispatchEvent(new MouseEvent('mousedown', eventInit));
      element.dispatchEvent(new MouseEvent('mouseup', eventInit));
      element.dispatchEvent(new MouseEvent('click', eventInit));
      dispatched = true;
    }} catch (error) {{
      window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ = String(error && (error.message || error));
    }}
    if (!dispatched) element.click();
  }};
  const waitForElement = async (id, attempts = 80) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = byId(id);
      if (element) return element;
      await sleep(100);
    }}
    throw new Error(`Timed out waiting for element: ${{id}}`);
  }};
  const waitForText = async (id, expected, attempts = 100) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = byId(id);
      const text = element ? (element.innerText || element.textContent || '') : '';
      if (text.includes(expected)) return element;
      await sleep(100);
    }}
    const element = byId(id);
    const text = element ? (element.innerText || element.textContent || '') : '';
    throw new Error(`Timed out waiting for text ${{expected}} in ${{id}}. Current text: ${{text.slice(0, 240)}}`);
  }};
  const waitForSelector = async (selector, attempts = 100) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = document.querySelector(selector);
      if (element) return element;
      await sleep(100);
    }}
    throw new Error(`Timed out waiting for selector: ${{selector}}`);
  }};
  const waitForClickableSelector = async (selector, attempts = 160, decision = '') => {{
    for (let index = 0; index < attempts; index += 1) {{
      const preferred = decision ? document.querySelector(`${{selector}}[data-decision="${{decision}}"]`) : null;
      const element = preferred || document.querySelector(selector);
      if (element && !element.disabled) return element;
      await sleep(120);
    }}
    throw new Error(`Timed out waiting for clickable selector: ${{selector}}`);
  }};
  const directHandlerForSelector = (selector) => {{
    const handlers = window.__CHASEOS_CAPTURE_MARKDOWN_HANDLERS__ || {{}};
    if (selector === '.capture-markdown-source-pack-sic-ingestion-btn' && typeof handlers.executeCaptureMarkdownSourcePackSicIngestion === 'function') {{
      return handlers.executeCaptureMarkdownSourcePackSicIngestion;
    }}
    if (selector === '.capture-markdown-source-pack-sic-graph-indexing-btn' && typeof handlers.executeCaptureMarkdownSourcePackSicGraphIndexing === 'function') {{
      return handlers.executeCaptureMarkdownSourcePackSicGraphIndexing;
    }}
    if (selector === '.capture-markdown-source-pack-canonical-promotion-approval-request-btn' && typeof handlers.previewCaptureMarkdownSourcePackCanonicalPromotionApprovalRequest === 'function') {{
      return handlers.previewCaptureMarkdownSourcePackCanonicalPromotionApprovalRequest;
    }}
    return null;
  }};
  const invokeCaptureControl = (button, selector) => {{
    const handler = directHandlerForSelector(selector);
    if (handler) {{
      const maybePromise = handler({{ target: button, stopPropagation: () => {{}} }});
      if (maybePromise && typeof maybePromise.catch === 'function') {{
        maybePromise.catch(error => {{
          window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ = String(error && (error.message || error));
        }});
      }}
      return;
    }}
    clickElement(button);
  }};
  const clickAndWaitForSelector = async (buttonSelector, resultSelector, label, decision = '', resultAttempts = 600) => {{
    const button = await waitForClickableSelector(buttonSelector, 240, decision);
    invokeCaptureControl(button, buttonSelector);
    try {{
      await waitForSelector(resultSelector, resultAttempts);
    }} catch (error) {{
      sourcePackProof = collectSourcePackProof();
      const diagnostics = [];
      if (sourcePackProof.source_intelligence_core_ingestion_message) {{
        diagnostics.push(`Source Intelligence Core ingestion message: ${{sourcePackProof.source_intelligence_core_ingestion_message}}`);
      }}
      if ((sourcePackProof.source_intelligence_core_ingestion_missing_dataset_keys || []).length) {{
        diagnostics.push(`Missing Source Intelligence Core ingestion data: ${{sourcePackProof.source_intelligence_core_ingestion_missing_dataset_keys.join(', ')}}`);
      }}
      if (sourcePackProof.packaged_capture_async_error) {{
        diagnostics.push(`Asynchronous error: ${{sourcePackProof.packaged_capture_async_error}}`);
      }}
      throw new Error(`Timed out waiting for ${{label}} result (${{resultSelector}}). ${{error.message}}${{diagnostics.length ? ' ' + diagnostics.join(' ') : ''}}`);
    }}
    await sleep(150);
    sourcePackProof = collectSourcePackProof();
    if (!sourcePackProof.result_selectors[resultSelector]) {{
      throw new Error(`Missing result after ${{label}}: ${{resultSelector}}`);
    }}
    return sourcePackProof;
  }};
  const setSelectorValue = (selector, value) => {{
    if (!selector) return;
    const element = document.querySelector(selector);
    if (!element) throw new Error(`Missing input for downstream failure case: ${{selector}}`);
    element.value = value;
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const failDownstreamStatement = async (casePayload) => {{
    const caseId = String((casePayload || {{}}).id || payload.downstream_failure_case_id || 'unknown');
    const invalidStatement = String((casePayload || {{}}).invalid_statement || `invalid downstream confirmation ${{payload.token || ''}}`);
    if ((casePayload || {{}}).statement_selector) {{
      setSelectorValue(casePayload.statement_selector, invalidStatement);
    }}
    const button = await waitForClickableSelector(casePayload.button_selector, 180);
    if ((casePayload || {{}}).button_dataset_key) {{
      button.dataset[casePayload.button_dataset_key] = invalidStatement;
    }}
    invokeCaptureControl(button, casePayload.button_selector || '');
    await waitForSelector(casePayload.result_selector || '.capture-markdown-guard-failure', 240);
    await waitForSelector('.capture-markdown-guard-failure', 240);
    await sleep(250);
    sourcePackProof = collectSourcePackProof();
    const guardText = String(sourcePackProof.guard_failure_text || '');
    if ((casePayload || {{}}).expected_text && !guardText.includes(casePayload.expected_text)) {{
      throw new Error(`Downstream guard text missing for ${{caseId}}: ${{guardText.slice(0, 240)}}`);
    }}
    const output = byId('capture-markdown-preview-body');
    const message = byId('capture-markdown-action-msg');
    const recent = byId('capture-markdown-recent-body');
    setResult({{
      ok: true,
      status: 'downstream_failure_visible',
      title: payload.title,
      token: payload.token,
      downstream_failure_case_id: caseId,
      save_action_message: saveActionMessage,
      action_message: message ? (message.innerText || message.textContent || '') : '',
      preview_text: output ? (output.innerText || output.textContent || '').slice(0, 4000) : '',
      recent_text: recent ? (recent.innerText || recent.textContent || '').slice(0, 4000) : '',
      source_cards: sourceCards,
      source_card_proof: sourceCardProof,
      release_readiness_proof: releaseReadinessProof,
      form_payload_after_set: formPayloadAfterSet,
      hotkey_rows_before: hotkeyRowsBefore,
      hotkey_rows_after: hotkeyRowsAfter,
      shortcut_proof: shortcutProof,
      review_proof_before: reviewProofBefore,
      review_proof_after: reviewProofAfter,
      source_pack_proof: sourcePackProof,
      body_text: (document.body.innerText || document.body.textContent || '').slice(0, 30000)
    }});
  }};
  const findRecentCaptureItem = () => {{
    const cards = Array.from(document.querySelectorAll('.capture-markdown-recent-item'));
    return cards.find(card => String(card.innerText || card.textContent || '').includes(payload.title)) || null;
  }};
  const collectRecentReviewProof = () => {{
    const item = findRecentCaptureItem();
    const row = item ? item.querySelector('.capture-markdown-review-row') : null;
    const select = row ? row.querySelector('.capture-markdown-review-decision') : null;
    const note = row ? row.querySelector('.capture-markdown-review-note') : null;
    const button = row ? row.querySelector('.capture-markdown-review-btn') : null;
    const message = row ? row.querySelector('.capture-markdown-review-msg') : null;
    const actionMessage = byId('capture-markdown-action-msg');
    return {{
      title_visible: Boolean(item),
      review_controls_visible: Boolean(row && select && note && button),
      review_path_present: Boolean(row && row.dataset.captureReviewPath),
      selected_decision: select ? select.value : '',
      note_value: note ? note.value : '',
      row_message: message ? (message.innerText || message.textContent || '') : '',
      action_message: actionMessage ? (actionMessage.innerText || actionMessage.textContent || '') : '',
      item_text: item ? (item.innerText || item.textContent || '').slice(0, 4000) : '',
    }};
  }};
  const collectSourcePackProof = () => {{
    const preview = document.querySelector('.capture-markdown-source-pack-preview');
    const writeButton = preview ? preview.querySelector('.capture-markdown-source-pack-write-btn') : null;
    const writeResult = preview ? preview.querySelector('.capture-markdown-source-pack-write-result') : null;
    const writeMessage = preview ? preview.querySelector('.capture-markdown-source-pack-write-msg') : null;
    const guardFailure = preview ? preview.querySelector('.capture-markdown-guard-failure') : null;
    const boundary = writeResult ? writeResult.querySelector('.capture-markdown-source-pack-boundary') : null;
    const readinessButton = writeResult ? writeResult.querySelector('.capture-markdown-source-pack-aor-readiness-btn') : null;
    const readiness = writeResult ? writeResult.querySelector('.capture-markdown-source-pack-aor-readiness') : null;
    const approvalDesignButton = writeResult ? writeResult.querySelector('.capture-markdown-source-pack-aor-approval-design-btn') : null;
    const sourceIntelligenceCoreIngestionButton = preview ? preview.querySelector('.capture-markdown-source-pack-sic-ingestion-btn') : null;
    const sourceIntelligenceCoreIngestionMessage = preview ? preview.querySelector('.capture-markdown-source-pack-sic-ingestion-msg') : null;
    const sourceIntelligenceCoreIngestionOutput = preview ? preview.querySelector('.capture-markdown-source-pack-sic-ingestion-result') : null;
    const sourceIntelligenceCoreIngestionBlocked = preview ? preview.querySelector('.capture-markdown-source-pack-sic-ingestion-blocked') : null;
    const text = preview ? (preview.innerText || preview.textContent || '') : '';
    const textLower = text.toLowerCase();
    const resultText = writeResult ? (writeResult.innerText || writeResult.textContent || '') : '';
    const datasetSnapshot = (element) => {{
      const data = {{}};
      if (!element || !element.dataset) return data;
      Object.keys(element.dataset).sort().forEach(key => {{
        data[key] = element.dataset[key] || '';
      }});
      return data;
    }};
    const sourceIntelligenceCoreIngestionRequiredDatasetKeys = [
      'captureReviewPath',
      'requestDigest',
      'fullDispatchArtifactPath',
      'fullDispatchArtifactDigest',
      'sicIngestionReadinessPacketDigest',
      'sicIngestionApprovalRequestDigest',
      'approvalArtifactPath',
      'decision',
      'approvalDecisionArtifactPath',
      'sicIngestionApprovalDecisionDigest',
      'approvalConsumptionArtifactPath',
      'sicIngestionApprovalConsumptionDigest',
    ];
    const sourceIntelligenceCoreIngestionMissingDatasetKeys = sourceIntelligenceCoreIngestionRequiredDatasetKeys
      .filter(key => !(sourceIntelligenceCoreIngestionButton && sourceIntelligenceCoreIngestionButton.dataset && sourceIntelligenceCoreIngestionButton.dataset[key]));
    if (!(
      sourceIntelligenceCoreIngestionButton &&
      sourceIntelligenceCoreIngestionButton.dataset &&
      (sourceIntelligenceCoreIngestionButton.dataset.sicIngestionDigest || sourceIntelligenceCoreIngestionButton.dataset.sourceIntelligenceCoreIngestionDigest)
    )) {{
      sourceIntelligenceCoreIngestionMissingDatasetKeys.push('sicIngestionDigest/sourceIntelligenceCoreIngestionDigest');
    }}
    const resultSelectorList = [
      '.capture-markdown-source-pack-aor-readiness',
      '.capture-markdown-source-pack-aor-approval-design',
      '.capture-markdown-source-pack-aor-approval-request',
      '.capture-markdown-source-pack-aor-approval-consumption-readiness',
      '.capture-markdown-source-pack-aor-approval-decision',
      '.capture-markdown-source-pack-aor-approval-consume-preview',
      '.capture-markdown-source-pack-aor-approval-consume',
      '.capture-markdown-source-pack-agent-bus-task-preview',
      '.capture-markdown-source-pack-agent-bus-task',
      '.capture-markdown-source-pack-agent-bus-task-claim-readiness',
      '.capture-markdown-source-pack-agent-bus-task-claim',
      '.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness',
      '.capture-markdown-source-pack-agent-bus-aor-dry-run',
      '.capture-markdown-source-pack-agent-bus-status-lifecycle',
      '.capture-markdown-source-pack-agent-bus-full-dispatch-readiness',
      '.capture-markdown-source-pack-agent-bus-full-dispatch',
      '.capture-markdown-source-pack-sic-readiness',
      '.capture-markdown-source-pack-sic-approval-design',
      '.capture-markdown-source-pack-sic-approval-request',
      '.capture-markdown-source-pack-sic-decision-readiness',
      '.capture-markdown-source-pack-sic-approval-decision',
      '.capture-markdown-source-pack-sic-approval-consumption-preview',
      '.capture-markdown-source-pack-sic-approval-consumption',
      '.capture-markdown-source-pack-sic-ingestion-preview',
      '.capture-markdown-source-pack-sic-ingestion',
      '.capture-markdown-source-pack-sic-ingestion-blocked',
      '.capture-markdown-source-pack-sic-graph-readiness',
      '.capture-markdown-source-pack-sic-graph-indexing',
      '.capture-markdown-source-pack-canonical-promotion-readiness',
      '.capture-markdown-source-pack-canonical-promotion-approval-design',
      '.capture-markdown-source-pack-canonical-promotion-approval-request',
      '.capture-markdown-source-pack-canonical-promotion-decision-readiness',
      '.capture-markdown-source-pack-canonical-promotion-approval-decision',
      '.capture-markdown-source-pack-canonical-promotion-approval-consumption',
      '.capture-markdown-source-pack-canonical-promotion',
    ];
    const resultSelectors = {{}};
    resultSelectorList.forEach(selector => {{
      resultSelectors[selector] = Boolean(preview && preview.querySelector(selector));
    }});
    const writtenPaths = Array.from(preview ? preview.querySelectorAll('.capture-markdown-source-pack-written-paths code') : [])
      .map(item => item.innerText || item.textContent || '')
      .filter(Boolean);
    return {{
      preview_visible: Boolean(preview),
      write_button_visible: Boolean(writeButton),
      write_button_enabled: Boolean(writeButton && !writeButton.disabled),
      write_message: writeMessage ? (writeMessage.innerText || writeMessage.textContent || '') : '',
      guard_failure_visible: Boolean(guardFailure),
      guard_failure_text: guardFailure ? (guardFailure.innerText || guardFailure.textContent || '').slice(0, 2000) : '',
      write_result_visible: Boolean(writeResult && resultText.trim()),
      boundary_visible: Boolean(boundary),
      downstream_boundary_visible: (
        textLower.includes('agent orchestration runtime dispatch') &&
        textLower.includes('source intelligence core ingestion') &&
        textLower.includes('canonical promotion') &&
        textLower.includes('not performed')
      ),
      aor_readiness_button_visible: Boolean(readinessButton),
      aor_readiness_result_visible: Boolean(readiness),
      aor_approval_design_button_visible: Boolean(approvalDesignButton),
      result_selectors: resultSelectors,
      aor_approval_consumption_result_visible: Boolean(resultSelectors['.capture-markdown-source-pack-aor-approval-consume']),
      agent_bus_task_result_visible: Boolean(resultSelectors['.capture-markdown-source-pack-agent-bus-task']),
      aor_full_dispatch_result_visible: Boolean(resultSelectors['.capture-markdown-source-pack-agent-bus-full-dispatch']),
      source_intelligence_core_readiness_result_visible: Boolean(resultSelectors['.capture-markdown-source-pack-sic-readiness']),
      source_intelligence_core_ingestion_button_visible: Boolean(sourceIntelligenceCoreIngestionButton),
      source_intelligence_core_ingestion_button_enabled: Boolean(sourceIntelligenceCoreIngestionButton && !sourceIntelligenceCoreIngestionButton.disabled),
      source_intelligence_core_ingestion_button_dataset: datasetSnapshot(sourceIntelligenceCoreIngestionButton),
      source_intelligence_core_ingestion_missing_dataset_keys: sourceIntelligenceCoreIngestionMissingDatasetKeys,
      source_intelligence_core_ingestion_message: sourceIntelligenceCoreIngestionMessage ? (sourceIntelligenceCoreIngestionMessage.innerText || sourceIntelligenceCoreIngestionMessage.textContent || '').slice(0, 2000) : '',
      source_intelligence_core_ingestion_output_text: sourceIntelligenceCoreIngestionOutput ? (sourceIntelligenceCoreIngestionOutput.innerText || sourceIntelligenceCoreIngestionOutput.textContent || '').slice(0, 4000) : '',
      source_intelligence_core_ingestion_blocked_visible: Boolean(sourceIntelligenceCoreIngestionBlocked),
      source_intelligence_core_ingestion_result_visible: Boolean(resultSelectors['.capture-markdown-source-pack-sic-ingestion']),
      graph_indexing_result_visible: Boolean(resultSelectors['.capture-markdown-source-pack-sic-graph-indexing']),
      canonical_promotion_result_visible: Boolean(resultSelectors['.capture-markdown-source-pack-canonical-promotion']),
      full_downstream_chain_visible: Boolean(
        resultSelectors['.capture-markdown-source-pack-agent-bus-full-dispatch'] &&
        resultSelectors['.capture-markdown-source-pack-sic-ingestion'] &&
        resultSelectors['.capture-markdown-source-pack-sic-graph-indexing'] &&
        resultSelectors['.capture-markdown-source-pack-canonical-promotion']
      ),
      written_paths: writtenPaths,
      source_pack_written_paths: writtenPaths.filter(path => String(path).startsWith('runtime/acquisition/packs/')),
      approval_written_paths: writtenPaths.filter(path => String(path).includes('approval')),
      graph_written_paths: writtenPaths.filter(path => String(path).includes('graph')),
      canonical_written_paths: writtenPaths.filter(path => String(path).includes('canonical') || String(path).includes('02_KNOWLEDGE')),
      packaged_capture_async_error: String(window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ || ''),
      text: text.slice(0, 30000),
    }};
  }};
  const waitForReviewDecision = async (decision, attempts = 120) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const proof = collectRecentReviewProof();
      const text = String(proof.item_text || '').toLowerCase();
      if (proof.selected_decision === decision && text.includes(String(decision).toLowerCase())) {{
        return proof;
      }}
      await sleep(100);
    }}
    const proof = collectRecentReviewProof();
    throw new Error(`Timed out waiting for Capture review decision ${{decision}}. Current recent text: ${{String(proof.item_text || '').slice(0, 240)}}`);
  }};
  const collectSourceCards = () => {{
    const cards = {{}};
    document.querySelectorAll('[data-capture-source-option]').forEach(card => {{
      cards[card.dataset.captureSourceOption || 'unknown'] = {{
        status: card.dataset.sourceStatus || '',
        action: card.dataset.sourceAction || '',
        source_mode: card.dataset.sourceMode || '',
        text: (card.innerText || card.textContent || '').slice(0, 500),
      }};
    }});
    return cards;
  }};
  const collectReleaseReadiness = () => {{
    const container = document.getElementById('capture-markdown-release-readiness');
    const text = container ? (container.innerText || container.textContent || '') : '';
    const groups = {{}};
    if (container) {{
      container.querySelectorAll('[data-capture-release-group]').forEach(group => {{
        groups[group.dataset.captureReleaseGroup || 'unknown'] = true;
      }});
    }}
    return {{
      visible: Boolean(container && text.trim()),
      status: container ? ((container.querySelector('[data-capture-release-readiness]') || {{}}).dataset || {{}}).captureReleaseReadiness || '' : '',
      ready_now_visible: Boolean(groups.ready_now),
      release_distribution_visible: Boolean(groups.release_distribution),
      approval_gated_downstream_visible: Boolean(groups.approval_gated_downstream),
      blocked_collectors_visible: Boolean(groups.blocked_collectors),
      release_proof_open_visible: Boolean(groups.release_proof_open),
      full_language_visible: text.includes('Source Intelligence Core') && text.includes('Agent Orchestration Runtime'),
      public_signing_status_visible: text.includes('Public certificate-authority signing') && text.includes('Public signing handoff'),
      real_engine_gap_visible: text.includes('Real image text engine quality') && text.includes('Unverified on this host'),
      text: text.slice(0, 2000),
    }};
  }};
  const collectHotkeyRows = () => {{
    const rows = {{}};
    document.querySelectorAll('.capture-hotkey-row').forEach(row => {{
      const input = row.querySelector('.capture-hotkey-input');
      rows[row.dataset.captureHotkeyAction || 'unknown'] = {{
        value: input ? input.value : '',
        disabled: input ? Boolean(input.disabled) : null,
        text: (row.innerText || row.textContent || '').slice(0, 500),
      }};
    }});
    return rows;
  }};
  const requiredSourceIds = [
    'manual_text',
    'capture_palette',
    'local_text_file',
    'saved_html_file',
    'controlled_html_artifact',
    'active_browser_artifact_capture',
    'chaseos_browser_page_capture',
    'browser_extension_capture',
    'screenshot_attachment',
    'display_region_capture',
    'active_window_capture',
    'studio_shortcuts',
    'active_browser_tab_capture',
    'screen_capture',
    'clipboard_text_capture',
    'ambient_clipboard_monitor',
    'selected_text_capture',
    'accessibility_tree_capture',
    'optical_character_recognition',
    'photo_document_text_extraction',
    'discord_capture',
    'live_discord_command_capture',
    'source_intelligence_core_ingestion',
    'canonical_promotion',
    'agent_dispatch'
  ];
  const requiredShortcutIds = [
    'open_capture_markdown',
    'focus_capture_raw_text',
    'preview_capture_markdown',
    'save_capture_markdown',
    'run_screen_capture_collector',
    'run_display_region_collector',
    'run_active_window_collector',
    'run_clipboard_text_collector',
    'run_ambient_clipboard_monitor',
    'run_selected_text_collector',
    'run_accessibility_tree_collector',
    'run_browser_artifact_collector',
    'run_browser_extension_collector',
    'run_active_browser_collector',
    'run_chaseos_browser_page_collector',
    'run_discord_artifact_collector',
    'capture_selected_text',
    'capture_screenshot',
    'capture_clipboard_text'
  ];

  setResult({{
    ok: false,
    status: 'started',
    title: payload.title,
    token: payload.token
  }});

  let sourceCards = {{}};
  let sourceCardProof = {{}};
  let releaseReadinessProof = {{}};
  let hotkeyRowsBefore = {{}};
  let hotkeyRowsAfter = {{}};
  let shortcutProof = {{}};
  let formPayloadAfterSet = {{}};
  let saveActionMessage = '';
  let reviewProofBefore = {{}};
  let reviewProofAfter = {{}};
  let sourcePackProof = {{}};

  setTimeout(() => {{
    (async () => {{
      try {{
      if (window.location.hash !== '#/capture-markdown') {{
        window.location.hash = '#/capture-markdown';
        window.dispatchEvent(new Event('hashchange'));
      }}
      await waitForElement('capture-markdown-title-input');
      await waitForElement('capture-markdown-preview-btn');
      await waitForElement('capture-markdown-save-btn');
      await waitForElement('capture-markdown-source-options');
      await waitForElement('capture-markdown-release-readiness');
      await waitForSelector('[data-capture-source-option="manual_text"]');

      sourceCards = collectSourceCards();
      sourceCardProof = {{
        required_present: requiredSourceIds.every(id => Boolean(sourceCards[id])),
        available_inputs_visible: ['manual_text', 'local_text_file', 'saved_html_file', 'controlled_html_artifact', 'screenshot_attachment'].every(
          id => Boolean(sourceCards[id]) && String(sourceCards[id].status || '').startsWith('available')
        ),
        explicit_browser_artifact_collector_visible: Boolean(sourceCards.active_browser_artifact_capture),
        explicit_browser_artifact_collector_settings_gated: Boolean(sourceCards.active_browser_artifact_capture) && (
          String(sourceCards.active_browser_artifact_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.active_browser_artifact_capture.status || '') === 'available_select_artifact'
        ),
        explicit_chaseos_browser_page_collector_visible: Boolean(sourceCards.chaseos_browser_page_capture),
        explicit_chaseos_browser_page_collector_settings_gated: Boolean(sourceCards.chaseos_browser_page_capture) && (
          String(sourceCards.chaseos_browser_page_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.chaseos_browser_page_capture.status || '') === 'available_click_to_capture'
        ),
        browser_extension_capture_visible: Boolean(sourceCards.browser_extension_capture),
        browser_extension_capture_settings_gated: Boolean(sourceCards.browser_extension_capture) && (
          String(sourceCards.browser_extension_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.browser_extension_capture.status || '') === 'available_browser_extension_capture'
        ),
        explicit_discord_artifact_collector_visible: Boolean(sourceCards.discord_capture),
        explicit_discord_artifact_collector_settings_gated: Boolean(sourceCards.discord_capture) && (
          String(sourceCards.discord_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.discord_capture.status || '') === 'available_select_artifact'
        ),
        blocked_collectors_visible: ['active_browser_tab_capture'].every(
          id => Boolean(sourceCards[id]) && String(sourceCards[id].status || '').includes('blocked')
        ),
        explicit_screen_collector_visible: Boolean(sourceCards.screen_capture),
        explicit_screen_collector_settings_gated: Boolean(sourceCards.screen_capture) && (
          String(sourceCards.screen_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.screen_capture.status || '') === 'available_click_to_capture'
        ),
        display_region_capture_visible: Boolean(sourceCards.display_region_capture),
        display_region_capture_settings_gated: Boolean(sourceCards.display_region_capture) && (
          String(sourceCards.display_region_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.display_region_capture.status || '') === 'available_click_to_capture'
        ),
        active_window_capture_visible: Boolean(sourceCards.active_window_capture),
        active_window_capture_settings_gated: Boolean(sourceCards.active_window_capture) && (
          String(sourceCards.active_window_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.active_window_capture.status || '') === 'available_click_to_capture'
        ),
        explicit_clipboard_collector_visible: Boolean(sourceCards.clipboard_text_capture),
        explicit_clipboard_collector_settings_gated: Boolean(sourceCards.clipboard_text_capture) && (
          String(sourceCards.clipboard_text_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.clipboard_text_capture.status || '') === 'available_click_to_capture'
        ),
        ambient_clipboard_monitor_visible: Boolean(sourceCards.ambient_clipboard_monitor),
        ambient_clipboard_monitor_settings_gated: Boolean(sourceCards.ambient_clipboard_monitor) && (
          String(sourceCards.ambient_clipboard_monitor.status || '') === 'disabled_in_settings'
          || String(sourceCards.ambient_clipboard_monitor.status || '') === 'available_clipboard_monitor'
        ),
        selected_text_capture_visible: Boolean(sourceCards.selected_text_capture),
        selected_text_capture_settings_gated: Boolean(sourceCards.selected_text_capture) && (
          String(sourceCards.selected_text_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.selected_text_capture.status || '') === 'available_click_to_capture'
        ),
        accessibility_tree_capture_visible: Boolean(sourceCards.accessibility_tree_capture),
        optical_character_recognition_surface_visible: Boolean(sourceCards.optical_character_recognition),
        photo_document_text_extraction_visible: Boolean(sourceCards.photo_document_text_extraction),
        live_discord_command_capture_visible: Boolean(sourceCards.live_discord_command_capture),
        live_discord_command_capture_settings_gated: Boolean(sourceCards.live_discord_command_capture) && (
          String(sourceCards.live_discord_command_capture.status || '') === 'disabled_in_settings'
          || String(sourceCards.live_discord_command_capture.status || '') === 'available_agent_bus_discord_command'
        ),
        downstream_consumers_visible: ['source_intelligence_core_ingestion', 'canonical_promotion', 'agent_dispatch'].every(
          id => Boolean(sourceCards[id]) && String(sourceCards[id].status || '').includes('approval_gated')
        ),
      }};
      releaseReadinessProof = collectReleaseReadiness();
      clickElement(document.querySelector('[data-capture-source-option="manual_text"]'));
      await sleep(150);
      const sourceSelect = requireId('capture-markdown-source-select');
      sourceCardProof.manual_text_selects_source_mode = sourceSelect.value === 'manual_text';

      clickElement(document.querySelector('[data-capture-source-option="studio_shortcuts"]'));
      await waitForElement('settings-capture-hotkeys');
      await waitForSelector('[data-capture-hotkey-action="open_capture_markdown"]');
      hotkeyRowsBefore = collectHotkeyRows();
      const previewShortcutInput = document.querySelector('[data-capture-hotkey-action="preview_capture_markdown"] .capture-hotkey-input');
      if (!previewShortcutInput) throw new Error('Missing preview Capture shortcut input');
      previewShortcutInput.focus();
      previewShortcutInput.dispatchEvent(new KeyboardEvent('keydown', {{
        key: 'P',
        code: 'KeyP',
        ctrlKey: true,
        altKey: true,
        bubbles: true,
        cancelable: true
      }}));
      await sleep(150);
      hotkeyRowsAfter = collectHotkeyRows();
      const blockedScreenshotInput = document.querySelector('[data-capture-hotkey-action="capture_screenshot"] .capture-hotkey-input');
      shortcutProof = {{
        settings_section_visible: Boolean(byId('settings-capture-hotkeys')),
        required_rows_present: requiredShortcutIds.every(id => Boolean(hotkeyRowsAfter[id])),
        default_open_chord_visible: (hotkeyRowsBefore.open_capture_markdown || {{}}).value === 'Ctrl+Shift+C',
        default_focus_chord_visible: (hotkeyRowsBefore.focus_capture_raw_text || {{}}).value === 'Ctrl+Shift+M',
        collector_shortcut_rows_visible: requiredShortcutIds.filter(id => id.startsWith('run_')).every(id => Boolean(hotkeyRowsAfter[id])),
        collector_shortcut_rows_configurable: requiredShortcutIds.filter(id => id.startsWith('run_')).every(id => !Boolean((hotkeyRowsAfter[id] || {{}}).disabled)),
        shortcut_input_capture_ok: (hotkeyRowsAfter.preview_capture_markdown || {{}}).value === 'Ctrl+Alt+P',
        blocked_shortcut_disabled: Boolean(blockedScreenshotInput && blockedScreenshotInput.disabled),
      }};

      document.body.dispatchEvent(new KeyboardEvent('keydown', {{
        key: 'M',
        code: 'KeyM',
        ctrlKey: true,
        shiftKey: true,
        bubbles: true,
        cancelable: true
      }}));
      await waitForElement('capture-markdown-raw-text');
      await sleep(250);
      shortcutProof.studio_shortcut_navigation_ok = window.location.hash === '#/capture-markdown';
      shortcutProof.raw_text_focused_by_shortcut = document.activeElement && document.activeElement.id === 'capture-markdown-raw-text';

      const proofBridge = window.__CHASEOS_CAPTURE_MARKDOWN_PROOF__ || null;
      if (proofBridge && typeof proofBridge.setFormValues === 'function') {{
        formPayloadAfterSet = proofBridge.setFormValues(payload);
      }} else {{
        setValue('capture-markdown-title-input', payload.title);
        setValue('capture-markdown-raw-text', payload.raw_text);
        setValue('capture-markdown-source-url-input', payload.source_url);
        setValue('capture-markdown-intent-input', payload.user_intent);
        setValue('capture-markdown-summary-input', payload.generated_summary);
        setValue('capture-markdown-notes-text', payload.structured_notes);
        setValue('capture-markdown-interpretation-text', payload.generated_interpretation);
        setChecked('capture-markdown-redaction-check', payload.allow_secret_redaction);
        formPayloadAfterSet = collectFormPayload();
      }}
      if ((formPayloadAfterSet.title || '') !== payload.title) {{
        throw new Error(`Capture form title did not update. Current title: ${{formPayloadAfterSet.title || ''}}`);
      }}

      const previewButton = requireId('capture-markdown-preview-btn');
      const previewFn = (proofBridge && proofBridge.preview) || window.previewCaptureMarkdown || (typeof previewCaptureMarkdown === 'function' ? previewCaptureMarkdown : null);
      if (typeof previewFn === 'function') {{
        const previewPromise = previewFn();
        if (previewPromise && typeof previewPromise.catch === 'function') {{
          previewPromise.catch(error => {{
            window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ = String(error && (error.message || error));
          }});
        }}
      }} else {{
        previewButton.click();
      }}
      await waitForText('capture-markdown-preview-body', payload.preview_marker);

      const saveButton = requireId('capture-markdown-save-btn');
      const saveFn = (proofBridge && proofBridge.save) || window.saveCaptureMarkdown || (typeof saveCaptureMarkdown === 'function' ? saveCaptureMarkdown : null);
      if (typeof saveFn === 'function') {{
        const savePromise = saveFn();
        if (savePromise && typeof savePromise.catch === 'function') {{
          savePromise.catch(error => {{
            window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ = String(error && (error.message || error));
          }});
        }}
      }} else {{
        saveButton.click();
      }}
      await waitForText('capture-markdown-action-msg', payload.saved_message);
      await waitForText('capture-markdown-recent-body', payload.title);
      saveActionMessage = (byId('capture-markdown-action-msg') || {{}}).innerText || (byId('capture-markdown-action-msg') || {{}}).textContent || '';

      reviewProofBefore = collectRecentReviewProof();
      if (!reviewProofBefore.review_controls_visible) {{
        throw new Error('Saved Capture review controls were not visible in the recent Capture list');
      }}
      if (!reviewProofBefore.review_path_present) {{
        throw new Error('Saved Capture review path was not present on the review row');
      }}
      const reviewItem = findRecentCaptureItem();
      const reviewRow = reviewItem ? reviewItem.querySelector('.capture-markdown-review-row') : null;
      const reviewSelect = reviewRow ? reviewRow.querySelector('.capture-markdown-review-decision') : null;
      const reviewNote = reviewRow ? reviewRow.querySelector('.capture-markdown-review-note') : null;
      const reviewButton = reviewRow ? reviewRow.querySelector('.capture-markdown-review-btn') : null;
      if (!reviewSelect || !reviewNote || !reviewButton) {{
        throw new Error('Saved Capture review form was incomplete');
      }}
      reviewSelect.value = payload.review_decision || 'reviewed';
      reviewSelect.dispatchEvent(new Event('input', {{ bubbles: true }}));
      reviewSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
      reviewNote.value = payload.review_note || '';
      reviewNote.dispatchEvent(new Event('input', {{ bubbles: true }}));
      reviewNote.dispatchEvent(new Event('change', {{ bubbles: true }}));
      clickElement(reviewButton);
      await waitForText('capture-markdown-action-msg', payload.review_message || 'Review: reviewed');
      reviewProofAfter = await waitForReviewDecision(payload.review_decision || 'reviewed');

      if (!payload.full_downstream_mode && !payload.guard_failure_mode && !payload.downstream_failure_mode) {{
        const output = byId('capture-markdown-preview-body');
        const message = byId('capture-markdown-action-msg');
        const recent = byId('capture-markdown-recent-body');
        setResult({{
          ok: true,
          status: 'reviewed',
          title: payload.title,
          token: payload.token,
          save_action_message: saveActionMessage,
          action_message: message ? (message.innerText || message.textContent || '') : '',
          preview_text: output ? (output.innerText || output.textContent || '').slice(0, 4000) : '',
          recent_text: recent ? (recent.innerText || recent.textContent || '').slice(0, 4000) : '',
          source_cards: sourceCards,
          source_card_proof: sourceCardProof,
          release_readiness_proof: releaseReadinessProof,
          form_payload_after_set: formPayloadAfterSet,
          hotkey_rows_before: hotkeyRowsBefore,
          hotkey_rows_after: hotkeyRowsAfter,
          shortcut_proof: shortcutProof,
          review_proof_before: reviewProofBefore,
          review_proof_after: reviewProofAfter,
          source_pack_proof: sourcePackProof,
          body_text: (document.body.innerText || document.body.textContent || '').slice(0, 30000)
        }});
        return;
      }}

      const refreshedReviewItem = findRecentCaptureItem();
      const refreshedReviewRow = refreshedReviewItem ? refreshedReviewItem.querySelector('.capture-markdown-review-row') : null;
      const approvalPreviewButton = refreshedReviewRow ? refreshedReviewRow.querySelector('.capture-markdown-approval-preview-btn') : null;
      if (!approvalPreviewButton) {{
        throw new Error('Source-pack approval preview control was not visible after review');
      }}
      clickElement(approvalPreviewButton);
      await waitForSelector('.capture-markdown-source-pack-preview');
      sourcePackProof = collectSourcePackProof();
      if (!sourcePackProof.write_button_visible || !sourcePackProof.write_button_enabled) {{
        throw new Error('Source-pack write control was not ready after approval preview');
      }}
      const writeButton = document.querySelector('.capture-markdown-source-pack-write-btn');
      if (payload.guard_failure_mode) {{
        const statementInput = document.querySelector('.capture-markdown-source-pack-write-statement');
        if (!statementInput) {{
          throw new Error('Source-pack guard failure statement field was not visible');
        }}
        statementInput.value = payload.guard_failure_statement || 'invalid source-package confirmation';
        statementInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        statementInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        clickElement(writeButton);
        await waitForSelector('.capture-markdown-guard-failure');
        await sleep(250);
        sourcePackProof = collectSourcePackProof();
        const output = byId('capture-markdown-preview-body');
        const message = byId('capture-markdown-action-msg');
        const recent = byId('capture-markdown-recent-body');
        setResult({{
          ok: true,
          status: 'guard_failure_visible',
          title: payload.title,
          token: payload.token,
          save_action_message: saveActionMessage,
          action_message: message ? (message.innerText || message.textContent || '') : '',
          preview_text: output ? (output.innerText || output.textContent || '').slice(0, 4000) : '',
          recent_text: recent ? (recent.innerText || recent.textContent || '').slice(0, 4000) : '',
          source_cards: sourceCards,
          source_card_proof: sourceCardProof,
          release_readiness_proof: releaseReadinessProof,
          form_payload_after_set: formPayloadAfterSet,
          hotkey_rows_before: hotkeyRowsBefore,
          hotkey_rows_after: hotkeyRowsAfter,
          shortcut_proof: shortcutProof,
          review_proof_before: reviewProofBefore,
          review_proof_after: reviewProofAfter,
          source_pack_proof: sourcePackProof,
          body_text: (document.body.innerText || document.body.textContent || '').slice(0, 30000)
        }});
        return;
      }}
      clickElement(writeButton);
      await waitForSelector('.capture-markdown-source-pack-written');
      await waitForSelector('.capture-markdown-source-pack-boundary');
      sourcePackProof = collectSourcePackProof();
      const aorReadinessButton = document.querySelector('.capture-markdown-source-pack-aor-readiness-btn');
      if (aorReadinessButton) {{
        clickElement(aorReadinessButton);
        await waitForSelector('.capture-markdown-source-pack-aor-readiness');
        sourcePackProof = collectSourcePackProof();
      }}
      await clickAndWaitForSelector('.capture-markdown-source-pack-aor-approval-design-btn', '.capture-markdown-source-pack-aor-approval-design', 'Agent Orchestration Runtime approval design');
      if (payload.downstream_failure_mode && payload.downstream_failure_case_id === 'aor_approval_request_bad_statement') {{
        await failDownstreamStatement(payload.downstream_failure_case || {{}});
        return;
      }}
      await clickAndWaitForSelector('.capture-markdown-source-pack-aor-approval-request-btn', '.capture-markdown-source-pack-aor-approval-request', 'Agent Orchestration Runtime approval request');
      await clickAndWaitForSelector('.capture-markdown-source-pack-aor-approval-consumption-readiness-btn', '.capture-markdown-source-pack-aor-approval-consumption-readiness', 'Agent Orchestration Runtime decision readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-aor-approval-decision-btn', '.capture-markdown-source-pack-aor-approval-decision', 'Agent Orchestration Runtime approval decision', 'approved');
      await clickAndWaitForSelector('.capture-markdown-source-pack-aor-approval-consume-preview-btn', '.capture-markdown-source-pack-aor-approval-consume-preview', 'Agent Orchestration Runtime approval consumption preview');
      await clickAndWaitForSelector('.capture-markdown-source-pack-aor-approval-consume-btn', '.capture-markdown-source-pack-aor-approval-consume', 'Agent Orchestration Runtime approval consumption');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-task-preview-btn', '.capture-markdown-source-pack-agent-bus-task-preview', 'Agent Bus task preview');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-task-write-btn', '.capture-markdown-source-pack-agent-bus-task', 'Agent Bus task write');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-task-claim-readiness-btn', '.capture-markdown-source-pack-agent-bus-task-claim-readiness', 'Agent Bus task claim readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-task-claim-btn', '.capture-markdown-source-pack-agent-bus-task-claim', 'Agent Bus task claim');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness-btn', '.capture-markdown-source-pack-agent-bus-aor-dry-run-readiness', 'Agent Orchestration Runtime dry-run readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-aor-dry-run-btn', '.capture-markdown-source-pack-agent-bus-aor-dry-run', 'Agent Orchestration Runtime dry-run');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-status-lifecycle-btn', '.capture-markdown-source-pack-agent-bus-status-lifecycle', 'Agent Bus task status lifecycle');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-full-dispatch-readiness-btn', '.capture-markdown-source-pack-agent-bus-full-dispatch-readiness', 'Agent Orchestration Runtime full-dispatch readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-agent-bus-full-dispatch-btn', '.capture-markdown-source-pack-agent-bus-full-dispatch', 'Agent Orchestration Runtime full dispatch');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-readiness-btn', '.capture-markdown-source-pack-sic-readiness', 'Source Intelligence Core readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-approval-design-btn', '.capture-markdown-source-pack-sic-approval-design', 'Source Intelligence Core approval design');
      if (payload.downstream_failure_mode && payload.downstream_failure_case_id === 'source_intelligence_core_approval_request_bad_statement') {{
        await failDownstreamStatement(payload.downstream_failure_case || {{}});
        return;
      }}
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-approval-request-btn', '.capture-markdown-source-pack-sic-approval-request', 'Source Intelligence Core approval request');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-decision-readiness-btn', '.capture-markdown-source-pack-sic-decision-readiness', 'Source Intelligence Core decision readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-approval-decision-btn', '.capture-markdown-source-pack-sic-approval-decision', 'Source Intelligence Core approval decision', 'approved');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-approval-consumption-preview-btn', '.capture-markdown-source-pack-sic-approval-consumption-preview', 'Source Intelligence Core approval consumption preview');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-approval-consumption-btn', '.capture-markdown-source-pack-sic-approval-consumption', 'Source Intelligence Core approval consumption');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-ingestion-preview-btn', '.capture-markdown-source-pack-sic-ingestion-preview', 'Source Intelligence Core ingestion preview');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-ingestion-btn', '.capture-markdown-source-pack-sic-ingestion', 'Source Intelligence Core ingestion', '', 1800);
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-graph-readiness-btn', '.capture-markdown-source-pack-sic-graph-readiness', 'Source Intelligence Core graph readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-sic-graph-indexing-btn', '.capture-markdown-source-pack-sic-graph-indexing', 'Source Intelligence Core graph indexing', '', 1800);
      await clickAndWaitForSelector('.capture-markdown-source-pack-canonical-promotion-readiness-btn', '.capture-markdown-source-pack-canonical-promotion-readiness', 'canonical promotion readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-canonical-promotion-approval-design-btn', '.capture-markdown-source-pack-canonical-promotion-approval-design', 'canonical promotion approval design');
      if (payload.downstream_failure_mode && payload.downstream_failure_case_id === 'canonical_promotion_approval_request_bad_statement') {{
        await failDownstreamStatement(payload.downstream_failure_case || {{}});
        return;
      }}
      await clickAndWaitForSelector('.capture-markdown-source-pack-canonical-promotion-approval-request-btn', '.capture-markdown-source-pack-canonical-promotion-approval-request', 'canonical promotion approval request');
      await clickAndWaitForSelector('.capture-markdown-source-pack-canonical-promotion-decision-readiness-btn', '.capture-markdown-source-pack-canonical-promotion-decision-readiness', 'canonical promotion decision readiness');
      await clickAndWaitForSelector('.capture-markdown-source-pack-canonical-promotion-approval-decision-btn', '.capture-markdown-source-pack-canonical-promotion-approval-decision', 'canonical promotion approval decision', 'approved');
      await clickAndWaitForSelector('.capture-markdown-source-pack-canonical-promotion-approval-consumption-btn', '.capture-markdown-source-pack-canonical-promotion-approval-consumption', 'canonical promotion approval consumption');
      await clickAndWaitForSelector('.capture-markdown-source-pack-canonical-promotion-btn', '.capture-markdown-source-pack-canonical-promotion', 'canonical promotion');

      const output = byId('capture-markdown-preview-body');
      if (output && output.scrollIntoView) output.scrollIntoView({{ block: 'center' }});
      await sleep(350);

      const message = byId('capture-markdown-action-msg');
      const recent = byId('capture-markdown-recent-body');
      setResult({{
        ok: true,
        status: 'reviewed',
        title: payload.title,
        token: payload.token,
        save_action_message: saveActionMessage,
        action_message: message ? (message.innerText || message.textContent || '') : '',
        preview_text: output ? (output.innerText || output.textContent || '').slice(0, 4000) : '',
        recent_text: recent ? (recent.innerText || recent.textContent || '').slice(0, 4000) : '',
        source_cards: sourceCards,
        source_card_proof: sourceCardProof,
        release_readiness_proof: releaseReadinessProof,
        form_payload_after_set: formPayloadAfterSet,
        hotkey_rows_before: hotkeyRowsBefore,
        hotkey_rows_after: hotkeyRowsAfter,
        shortcut_proof: shortcutProof,
        review_proof_before: reviewProofBefore,
        review_proof_after: reviewProofAfter,
        source_pack_proof: sourcePackProof,
      body_text: (document.body.innerText || document.body.textContent || '').slice(0, 30000)
      }});
      }} catch (error) {{
        const message = byId('capture-markdown-action-msg');
        const recent = byId('capture-markdown-recent-body');
        setResult({{
          ok: false,
          status: 'error',
          title: payload.title,
          token: payload.token,
          error: String(error && (error.message || error)),
          save_action_message: saveActionMessage,
          action_message: message ? (message.innerText || message.textContent || '') : '',
          recent_text: recent ? (recent.innerText || recent.textContent || '').slice(0, 4000) : '',
          source_cards: sourceCards,
          source_card_proof: sourceCardProof,
          release_readiness_proof: releaseReadinessProof,
          form_payload_after_set: formPayloadAfterSet,
          hotkey_rows_before: hotkeyRowsBefore,
          hotkey_rows_after: hotkeyRowsAfter,
          shortcut_proof: shortcutProof,
          review_proof_before: reviewProofBefore,
          review_proof_after: reviewProofAfter,
          source_pack_proof: sourcePackProof,
        body_text: (document.body.innerText || document.body.textContent || '').slice(0, 30000)
        }});
      }}
    }})();
  }}, 0);

  "started";
}})()
""".strip()


def _build_capture_markdown_image_text_action_script(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""
(() => {{
  const payload = {payload_json};
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const setResult = (value) => {{
    window.__CHASEOS_PACKAGED_CAPTURE_ACTION_RESULT__ = value;
  }};
  const byId = (id) => document.getElementById(id);
  const requireId = (id) => {{
    const element = byId(id);
    if (!element) throw new Error(`Missing element: ${{id}}`);
    return element;
  }};
  const setValue = (id, value) => {{
    const element = requireId(id);
    element.value = value == null ? '' : String(value);
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const setChecked = (id, checked) => {{
    const element = requireId(id);
    element.checked = Boolean(checked);
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const clickElement = (element) => {{
    if (!element) throw new Error('Missing clickable element');
    element.click();
  }};
  const waitForElement = async (id, attempts = 100) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = byId(id);
      if (element) return element;
      await sleep(100);
    }}
    throw new Error(`Timed out waiting for element: ${{id}}`);
  }};
  const waitForText = async (id, expected, attempts = 140) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = byId(id);
      const text = element ? (element.innerText || element.textContent || '') : '';
      if (text.includes(expected)) return element;
      await sleep(100);
    }}
    const element = byId(id);
    const text = element ? (element.innerText || element.textContent || '') : '';
    throw new Error(`Timed out waiting for text ${{expected}} in ${{id}}. Current text: ${{text.slice(0, 240)}}`);
  }};
  const waitForSelector = async (selector, attempts = 100) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = document.querySelector(selector);
      if (element) return element;
      await sleep(100);
    }}
    throw new Error(`Timed out waiting for selector: ${{selector}}`);
  }};
  const showStudioPanel = async (panelId) => {{
    if (typeof showPanel === 'function') {{
      showPanel(panelId, {{ updateHash: true }});
    }} else {{
      window.location.hash = `#/${{panelId}}`;
      window.dispatchEvent(new Event('hashchange'));
    }}
    await sleep(250);
  }};
  const collectSourceCards = () => {{
    const cards = {{}};
    document.querySelectorAll('[data-capture-source-option]').forEach(card => {{
      cards[card.dataset.captureSourceOption || 'unknown'] = {{
        status: card.dataset.sourceStatus || '',
        action: card.dataset.sourceAction || '',
        source_mode: card.dataset.sourceMode || '',
        text: (card.innerText || card.textContent || '').slice(0, 500),
      }};
    }});
    return cards;
  }};
  const findRecentCaptureItem = () => {{
    const cards = Array.from(document.querySelectorAll('.capture-markdown-recent-item'));
    return cards.find(card => String(card.innerText || card.textContent || '').includes(payload.title)) || null;
  }};
  const collectRecentReviewProof = () => {{
    const item = findRecentCaptureItem();
    const row = item ? item.querySelector('.capture-markdown-review-row') : null;
    const select = row ? row.querySelector('.capture-markdown-review-decision') : null;
    const note = row ? row.querySelector('.capture-markdown-review-note') : null;
    const button = row ? row.querySelector('.capture-markdown-review-btn') : null;
    return {{
      title_visible: Boolean(item),
      review_controls_visible: Boolean(row && select && note && button),
      review_path_present: Boolean(row && row.dataset.captureReviewPath),
      selected_decision: select ? select.value : '',
      item_text: item ? (item.innerText || item.textContent || '').slice(0, 4000) : '',
    }};
  }};
  const waitForReviewDecision = async (decision, attempts = 140) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const proof = collectRecentReviewProof();
      const text = String(proof.item_text || '').toLowerCase();
      if (proof.selected_decision === decision && text.includes(String(decision).toLowerCase())) return proof;
      await sleep(100);
    }}
    const proof = collectRecentReviewProof();
    throw new Error(`Timed out waiting for Capture review decision ${{decision}}. Current recent text: ${{String(proof.item_text || '').slice(0, 240)}}`);
  }};
  const collectFormPayload = () => {{
    const bridge = window.__CHASEOS_CAPTURE_MARKDOWN_PROOF__;
    if (bridge && typeof bridge.getPayload === 'function') return bridge.getPayload();
    return {{
      source_mode: (byId('capture-markdown-source-select') || {{}}).value || '',
      title: (byId('capture-markdown-title-input') || {{}}).value || '',
      file_path: (byId('capture-markdown-file-input') || {{}}).value || '',
      local_ocr_command: (byId('capture-markdown-local-ocr-command-input') || {{}}).value || '',
    }};
  }};

  setResult({{ ok: false, status: 'started', title: payload.title, token: payload.token }});

  let sourceCards = {{}};
  let sourceCardProof = {{}};
  let settingsProof = {{}};
  let formPayloadAfterSet = {{}};
  let saveActionMessage = '';
  let reviewProofBefore = {{}};
  let reviewProofAfter = {{}};

  setTimeout(() => {{
    (async () => {{
      try {{
        await showStudioPanel('capture-markdown');
        await waitForElement('capture-markdown-title-input');
        await waitForElement('capture-markdown-source-options');
        await waitForSelector('[data-capture-source-option="optical_character_recognition"]');

        sourceCards = collectSourceCards();
        sourceCardProof = {{
          optical_character_recognition_visible: Boolean(sourceCards.optical_character_recognition),
          optical_character_recognition_selectable: String((sourceCards.optical_character_recognition || {{}}).action || '') === 'select_source_mode',
          optical_character_recognition_local_status: String((sourceCards.optical_character_recognition || {{}}).status || ''),
          live_collectors_blocked: ['active_browser_tab_capture'].every(
            id => Boolean(sourceCards[id]) && String(sourceCards[id].status || '').includes('blocked')
          ),
          explicit_screen_collector_settings_gated: Boolean(sourceCards.screen_capture) && (
            String(sourceCards.screen_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.screen_capture.status || '') === 'available_click_to_capture'
          ),
          explicit_clipboard_collector_settings_gated: Boolean(sourceCards.clipboard_text_capture) && (
            String(sourceCards.clipboard_text_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.clipboard_text_capture.status || '') === 'available_click_to_capture'
          ),
          explicit_browser_artifact_collector_settings_gated: Boolean(sourceCards.active_browser_artifact_capture) && (
            String(sourceCards.active_browser_artifact_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.active_browser_artifact_capture.status || '') === 'available_select_artifact'
          ),
          explicit_chaseos_browser_page_collector_settings_gated: Boolean(sourceCards.chaseos_browser_page_capture) && (
            String(sourceCards.chaseos_browser_page_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.chaseos_browser_page_capture.status || '') === 'available_click_to_capture'
          ),
          explicit_discord_artifact_collector_settings_gated: Boolean(sourceCards.discord_capture) && (
            String(sourceCards.discord_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.discord_capture.status || '') === 'available_select_artifact'
          ),
          downstream_consumers_visible: ['source_intelligence_core_ingestion', 'canonical_promotion', 'agent_dispatch'].every(
            id => Boolean(sourceCards[id]) && String(sourceCards[id].status || '').includes('approval_gated')
          ),
        }};

        await showStudioPanel('settings');
        await waitForElement('settings-capture-local-image-text');
        const settingsSection = requireId('settings-capture-local-image-text');
        const settingsCommand = byId('capture-local-image-text-command-input');
        const settingsText = settingsSection.innerText || settingsSection.textContent || '';
        settingsProof = {{
          section_visible: true,
          command_visible: Boolean(settingsCommand),
          command_matches_saved_settings: settingsCommand ? settingsCommand.value === payload.local_ocr_command : false,
          cloud_extraction_blocked: settingsText.toLowerCase().includes('cloud extraction') && settingsText.toLowerCase().includes('blocked'),
          screen_capture_blocked: settingsText.toLowerCase().includes('screen capture') && settingsText.toLowerCase().includes('blocked'),
        }};

        await showStudioPanel('capture-markdown');
        await waitForElement('capture-markdown-title-input');
        clickElement(document.querySelector('[data-capture-source-option="optical_character_recognition"]'));
        await sleep(250);
        const sourceSelect = requireId('capture-markdown-source-select');
        sourceCardProof.optical_character_recognition_selects_source_mode = sourceSelect.value === 'screenshot_text_extraction';
        const localCommandRow = requireId('capture-markdown-local-ocr-command-row');
        sourceCardProof.local_command_row_visible = !localCommandRow.hidden;

        setValue('capture-markdown-title-input', payload.title);
        setValue('capture-markdown-file-input', payload.file_path);
        setValue('capture-markdown-local-ocr-command-input', '');
        setValue('capture-markdown-source-url-input', payload.source_url);
        setValue('capture-markdown-intent-input', payload.user_intent);
        setValue('capture-markdown-summary-input', payload.generated_summary);
        setValue('capture-markdown-notes-text', payload.structured_notes);
        setValue('capture-markdown-interpretation-text', payload.generated_interpretation);
        setChecked('capture-markdown-redaction-check', payload.allow_secret_redaction);
        formPayloadAfterSet = collectFormPayload();
        if ((formPayloadAfterSet.source_mode || '') !== 'screenshot_text_extraction') {{
          throw new Error(`Capture source mode did not select image text extraction. Current mode: ${{formPayloadAfterSet.source_mode || ''}}`);
        }}
        if ((formPayloadAfterSet.file_path || '') !== payload.file_path) {{
          throw new Error(`Capture image path did not update. Current file path: ${{formPayloadAfterSet.file_path || ''}}`);
        }}
        if ((formPayloadAfterSet.local_ocr_command || '') !== '') {{
          throw new Error('Per-capture local image text command was not blank after clearing it');
        }}

        const proofBridge = window.__CHASEOS_CAPTURE_MARKDOWN_PROOF__ || null;
        const previewFn = (proofBridge && proofBridge.preview) || window.previewCaptureMarkdown || (typeof previewCaptureMarkdown === 'function' ? previewCaptureMarkdown : null);
        if (typeof previewFn === 'function') {{
          const previewPromise = previewFn();
          if (previewPromise && typeof previewPromise.catch === 'function') {{
            previewPromise.catch(error => {{
              window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ = String(error && (error.message || error));
            }});
          }}
        }} else {{
          requireId('capture-markdown-preview-btn').click();
        }}
        await waitForText('capture-markdown-preview-body', payload.extracted_text);

        const saveFn = (proofBridge && proofBridge.save) || window.saveCaptureMarkdown || (typeof saveCaptureMarkdown === 'function' ? saveCaptureMarkdown : null);
        if (typeof saveFn === 'function') {{
          const savePromise = saveFn();
          if (savePromise && typeof savePromise.catch === 'function') {{
            savePromise.catch(error => {{
              window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ = String(error && (error.message || error));
            }});
          }}
        }} else {{
          requireId('capture-markdown-save-btn').click();
        }}
        await waitForText('capture-markdown-action-msg', payload.saved_message);
        await waitForText('capture-markdown-recent-body', payload.title);
        saveActionMessage = (byId('capture-markdown-action-msg') || {{}}).innerText || (byId('capture-markdown-action-msg') || {{}}).textContent || '';

        reviewProofBefore = collectRecentReviewProof();
        if (!reviewProofBefore.review_controls_visible) throw new Error('Saved image text Capture review controls were not visible');
        if (!reviewProofBefore.review_path_present) throw new Error('Saved image text Capture review path was not present');
        const reviewItem = findRecentCaptureItem();
        const reviewRow = reviewItem ? reviewItem.querySelector('.capture-markdown-review-row') : null;
        const reviewSelect = reviewRow ? reviewRow.querySelector('.capture-markdown-review-decision') : null;
        const reviewNote = reviewRow ? reviewRow.querySelector('.capture-markdown-review-note') : null;
        const reviewButton = reviewRow ? reviewRow.querySelector('.capture-markdown-review-btn') : null;
        if (!reviewSelect || !reviewNote || !reviewButton) throw new Error('Saved image text Capture review form was incomplete');
        reviewSelect.value = payload.review_decision || 'reviewed';
        reviewSelect.dispatchEvent(new Event('input', {{ bubbles: true }}));
        reviewSelect.dispatchEvent(new Event('change', {{ bubbles: true }}));
        reviewNote.value = payload.review_note || '';
        reviewNote.dispatchEvent(new Event('input', {{ bubbles: true }}));
        reviewNote.dispatchEvent(new Event('change', {{ bubbles: true }}));
        clickElement(reviewButton);
        await waitForText('capture-markdown-action-msg', payload.review_message || 'Review: reviewed');
        reviewProofAfter = await waitForReviewDecision(payload.review_decision || 'reviewed');

        const output = byId('capture-markdown-preview-body');
        if (output && output.scrollIntoView) output.scrollIntoView({{ block: 'center' }});
        await sleep(350);
        const message = byId('capture-markdown-action-msg');
        const recent = byId('capture-markdown-recent-body');
        setResult({{
          ok: true,
          status: 'reviewed',
          title: payload.title,
          token: payload.token,
          save_action_message: saveActionMessage,
          action_message: message ? (message.innerText || message.textContent || '') : '',
          preview_text: output ? (output.innerText || output.textContent || '').slice(0, 4000) : '',
          recent_text: recent ? (recent.innerText || recent.textContent || '').slice(0, 4000) : '',
          source_cards: sourceCards,
          source_card_proof: sourceCardProof,
          settings_proof: settingsProof,
          form_payload_after_set: formPayloadAfterSet,
          review_proof_before: reviewProofBefore,
          review_proof_after: reviewProofAfter,
          body_text: (document.body.innerText || document.body.textContent || '').slice(0, 30000)
        }});
      }} catch (error) {{
        setResult({{
          ok: false,
          status: 'error',
          title: payload.title,
          token: payload.token,
          error: String(error && (error.message || error)),
          source_cards: sourceCards,
          source_card_proof: sourceCardProof,
          settings_proof: settingsProof,
          form_payload_after_set: formPayloadAfterSet,
          body_text: (document.body.innerText || document.body.textContent || '').slice(0, 8000)
        }});
      }}
    }})();
  }}, 0);

  "started";
}})()
""".strip()


def _build_capture_markdown_image_text_failure_action_script(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""
(() => {{
  const payload = {payload_json};
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const setResult = (value) => {{
    window.__CHASEOS_PACKAGED_CAPTURE_ACTION_RESULT__ = value;
  }};
  const byId = (id) => document.getElementById(id);
  const requireId = (id) => {{
    const element = byId(id);
    if (!element) throw new Error(`Missing element: ${{id}}`);
    return element;
  }};
  const setValue = (id, value) => {{
    const element = requireId(id);
    element.value = value == null ? '' : String(value);
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const setChecked = (id, checked) => {{
    const element = requireId(id);
    element.checked = Boolean(checked);
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const clickElement = (element) => {{
    if (!element) throw new Error('Missing clickable element');
    element.click();
  }};
  const waitForElement = async (id, attempts = 100) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = byId(id);
      if (element) return element;
      await sleep(100);
    }}
    throw new Error(`Timed out waiting for element: ${{id}}`);
  }};
  const waitForSelector = async (selector, attempts = 100) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = document.querySelector(selector);
      if (element) return element;
      await sleep(100);
    }}
    throw new Error(`Timed out waiting for selector: ${{selector}}`);
  }};
  const showStudioPanel = async (panelId) => {{
    if (typeof showPanel === 'function') {{
      showPanel(panelId, {{ updateHash: true }});
    }} else {{
      window.location.hash = `#/${{panelId}}`;
      window.dispatchEvent(new Event('hashchange'));
    }}
    await sleep(250);
  }};
  const collectSourceCards = () => {{
    const cards = {{}};
    document.querySelectorAll('[data-capture-source-option]').forEach(card => {{
      cards[card.dataset.captureSourceOption || 'unknown'] = {{
        status: card.dataset.sourceStatus || '',
        action: card.dataset.sourceAction || '',
        source_mode: card.dataset.sourceMode || '',
        text: (card.innerText || card.textContent || '').slice(0, 500),
      }};
    }});
    return cards;
  }};
  const collectFormPayload = () => {{
    const bridge = window.__CHASEOS_CAPTURE_MARKDOWN_PROOF__;
    if (bridge && typeof bridge.getPayload === 'function') return bridge.getPayload();
    return {{
      source_mode: (byId('capture-markdown-source-select') || {{}}).value || '',
      title: (byId('capture-markdown-title-input') || {{}}).value || '',
      file_path: (byId('capture-markdown-file-input') || {{}}).value || '',
      local_ocr_command: (byId('capture-markdown-local-ocr-command-input') || {{}}).value || '',
    }};
  }};
  const readPreviewState = () => {{
    const output = byId('capture-markdown-preview-body');
    const message = byId('capture-markdown-action-msg');
    const saveButton = byId('capture-markdown-save-btn');
    return {{
      preview_text: output ? (output.innerText || output.textContent || '') : '',
      action_message: message ? (message.innerText || message.textContent || '') : '',
      save_disabled: saveButton ? Boolean(saveButton.disabled) : false,
      form_payload_after_set: collectFormPayload(),
      body_text: (document.body.innerText || document.body.textContent || '').slice(0, 8000),
    }};
  }};
  const waitForExpectedText = async (expected, attempts = 180) => {{
    const needle = String(expected || '').toLowerCase();
    for (let index = 0; index < attempts; index += 1) {{
      const state = readPreviewState();
      const combined = `${{state.preview_text}} ${{state.action_message}} ${{state.body_text}}`.toLowerCase();
      if (needle && combined.includes(needle)) return state;
      await sleep(100);
    }}
    const state = readPreviewState();
    throw new Error(`Timed out waiting for failure text ${{expected}}. Current preview: ${{String(state.preview_text || '').slice(0, 240)}}. Current message: ${{String(state.action_message || '').slice(0, 240)}}`);
  }};
  const runPreview = async () => {{
    const proofBridge = window.__CHASEOS_CAPTURE_MARKDOWN_PROOF__ || null;
    const previewFn = (proofBridge && proofBridge.preview) || window.previewCaptureMarkdown || (typeof previewCaptureMarkdown === 'function' ? previewCaptureMarkdown : null);
    if (typeof previewFn === 'function') {{
      const previewPromise = previewFn();
      if (previewPromise && typeof previewPromise.then === 'function') {{
        await previewPromise.catch(error => {{
          window.__CHASEOS_PACKAGED_CAPTURE_ASYNC_ERROR__ = String(error && (error.message || error));
        }});
      }}
    }} else {{
      requireId('capture-markdown-preview-btn').click();
    }}
  }};
  const runFailureCase = async (item) => {{
    setValue('capture-markdown-title-input', item.title || payload.title);
    setValue('capture-markdown-file-input', payload.file_path);
    setValue('capture-markdown-local-ocr-command-input', item.local_ocr_command || '');
    setValue('capture-markdown-source-url-input', `${{payload.source_url}}/${{item.id || 'case'}}`);
    setValue('capture-markdown-intent-input', payload.user_intent);
    setValue('capture-markdown-summary-input', payload.generated_summary);
    setValue('capture-markdown-notes-text', `${{payload.structured_notes}}\\n- Failure case: ${{item.id || 'unknown'}}`);
    setValue('capture-markdown-interpretation-text', payload.generated_interpretation);
    setChecked('capture-markdown-redaction-check', false);
    const beforePreviewPayload = collectFormPayload();
    await runPreview();
    const state = await waitForExpectedText(item.expected_text);
    return {{
      id: item.id || '',
      ok: true,
      expected_text: item.expected_text || '',
      expected_status: item.expected_status || '',
      preview_text: String(state.preview_text || '').slice(0, 3000),
      action_message: String(state.action_message || '').slice(0, 1000),
      save_disabled: Boolean(state.save_disabled),
      form_payload_after_set: state.form_payload_after_set || beforePreviewPayload,
      body_text: String(state.body_text || '').slice(0, 8000),
    }};
  }};

  setResult({{ ok: false, status: 'started', title: payload.title, token: payload.token }});

  let sourceCards = {{}};
  let sourceCardProof = {{}};
  let settingsProof = {{}};
  let failureProofs = [];

  setTimeout(() => {{
    (async () => {{
      try {{
        await showStudioPanel('capture-markdown');
        await waitForElement('capture-markdown-title-input');
        await waitForElement('capture-markdown-source-options');
        await waitForSelector('[data-capture-source-option="optical_character_recognition"]');
        sourceCards = collectSourceCards();
        sourceCardProof = {{
          optical_character_recognition_visible: Boolean(sourceCards.optical_character_recognition),
          optical_character_recognition_selectable: String((sourceCards.optical_character_recognition || {{}}).action || '') === 'select_source_mode',
          optical_character_recognition_local_status: String((sourceCards.optical_character_recognition || {{}}).status || ''),
          live_collectors_blocked: ['active_browser_tab_capture'].every(
            id => Boolean(sourceCards[id]) && String(sourceCards[id].status || '').includes('blocked')
          ),
          explicit_screen_collector_settings_gated: Boolean(sourceCards.screen_capture) && (
            String(sourceCards.screen_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.screen_capture.status || '') === 'available_click_to_capture'
          ),
          explicit_clipboard_collector_settings_gated: Boolean(sourceCards.clipboard_text_capture) && (
            String(sourceCards.clipboard_text_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.clipboard_text_capture.status || '') === 'available_click_to_capture'
          ),
          explicit_browser_artifact_collector_settings_gated: Boolean(sourceCards.active_browser_artifact_capture) && (
            String(sourceCards.active_browser_artifact_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.active_browser_artifact_capture.status || '') === 'available_select_artifact'
          ),
          explicit_chaseos_browser_page_collector_settings_gated: Boolean(sourceCards.chaseos_browser_page_capture) && (
            String(sourceCards.chaseos_browser_page_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.chaseos_browser_page_capture.status || '') === 'available_click_to_capture'
          ),
          explicit_discord_artifact_collector_settings_gated: Boolean(sourceCards.discord_capture) && (
            String(sourceCards.discord_capture.status || '') === 'disabled_in_settings'
            || String(sourceCards.discord_capture.status || '') === 'available_select_artifact'
          ),
          downstream_consumers_visible: ['source_intelligence_core_ingestion', 'canonical_promotion', 'agent_dispatch'].every(
            id => Boolean(sourceCards[id]) && String(sourceCards[id].status || '').includes('approval_gated')
          ),
        }};

        await showStudioPanel('settings');
        await waitForElement('settings-capture-local-image-text');
        const settingsSection = requireId('settings-capture-local-image-text');
        const settingsCommand = byId('capture-local-image-text-command-input');
        const settingsTimeout = byId('capture-local-image-text-timeout-input');
        const settingsText = settingsSection.innerText || settingsSection.textContent || '';
        settingsProof = {{
          section_visible: true,
          command_visible: Boolean(settingsCommand),
          command_blank: settingsCommand ? String(settingsCommand.value || '') === '' : false,
          timeout_visible: Boolean(settingsTimeout),
          timeout_matches_saved_settings: settingsTimeout ? Number(settingsTimeout.value || 0) === Number(payload.local_ocr_timeout_seconds || 1) : false,
          cloud_extraction_blocked: settingsText.toLowerCase().includes('cloud extraction') && settingsText.toLowerCase().includes('blocked'),
          screen_capture_blocked: settingsText.toLowerCase().includes('screen capture') && settingsText.toLowerCase().includes('blocked'),
        }};

        await showStudioPanel('capture-markdown');
        await waitForElement('capture-markdown-title-input');
        clickElement(document.querySelector('[data-capture-source-option="optical_character_recognition"]'));
        await sleep(250);
        const sourceSelect = requireId('capture-markdown-source-select');
        sourceCardProof.optical_character_recognition_selects_source_mode = sourceSelect.value === 'screenshot_text_extraction';
        const localCommandRow = requireId('capture-markdown-local-ocr-command-row');
        sourceCardProof.local_command_row_visible = !localCommandRow.hidden;

        for (const item of (payload.failure_cases || [])) {{
          failureProofs.push(await runFailureCase(item));
        }}

        const output = byId('capture-markdown-preview-body');
        if (output && output.scrollIntoView) output.scrollIntoView({{ block: 'center' }});
        await sleep(350);
        setResult({{
          ok: true,
          status: 'failure_states_visible',
          title: payload.title,
          token: payload.token,
          source_cards: sourceCards,
          source_card_proof: sourceCardProof,
          settings_proof: settingsProof,
          failure_cases: failureProofs,
          action_message: (byId('capture-markdown-action-msg') || {{}}).innerText || (byId('capture-markdown-action-msg') || {{}}).textContent || '',
          preview_text: (byId('capture-markdown-preview-body') || {{}}).innerText || (byId('capture-markdown-preview-body') || {{}}).textContent || '',
          body_text: (document.body.innerText || document.body.textContent || '').slice(0, 8000)
        }});
      }} catch (error) {{
        setResult({{
          ok: false,
          status: 'error',
          title: payload.title,
          token: payload.token,
          error: String(error && (error.message || error)),
          source_cards: sourceCards,
          source_card_proof: sourceCardProof,
          settings_proof: settingsProof,
          failure_cases: failureProofs,
          body_text: (document.body.innerText || document.body.textContent || '').slice(0, 8000)
        }});
      }}
    }})();
  }}, 0);

  "started";
}})()
""".strip()


def _capture_markdown_action_result_script() -> str:
    return "JSON.parse(JSON.stringify(window.__CHASEOS_PACKAGED_CAPTURE_ACTION_RESULT__ || null));"


def _coerce_script_result(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}
    if value is None:
        return {}
    return {"value": value}


def _capture_action_result_from_capture(capture: dict[str, Any]) -> dict[str, Any]:
    meta = capture.get("meta") if isinstance(capture.get("meta"), dict) else {}
    route_script = meta.get("route_script") if isinstance(meta.get("route_script"), dict) else {}
    final = route_script.get("final") if isinstance(route_script.get("final"), dict) else {}
    return _coerce_script_result(final.get("result"))


def _read_vault_relative_text(vault: Path, relative_path: str) -> str:
    target = (vault / relative_path).resolve()
    try:
        target.relative_to(vault)
    except ValueError:
        return ""
    try:
        return target.read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_vault_relative_json(vault: Path, relative_path: str) -> dict[str, Any]:
    target = (vault / relative_path).resolve()
    try:
        target.relative_to(vault)
    except ValueError:
        return {}
    try:
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _capture_review_artifact_evidence(vault: Path, markdown_relative_path: str) -> dict[str, Any]:
    if not markdown_relative_path:
        return {
            "content_path": "",
            "sidecar_path": "",
            "visual_capture_packet_path": "",
            "sidecar_exists": False,
            "visual_capture_packet_exists": False,
        }
    content = (vault / markdown_relative_path).resolve()
    try:
        content.relative_to(vault)
    except ValueError:
        return {
            "content_path": markdown_relative_path,
            "sidecar_path": "",
            "visual_capture_packet_path": "",
            "sidecar_exists": False,
            "visual_capture_packet_exists": False,
        }
    sidecar_rel = _relative_to_vault(vault, content.with_suffix(".meta.json"))
    packet_rel = _relative_to_vault(vault, content.with_suffix(".visual_capture.json"))
    sidecar = _read_vault_relative_json(vault, sidecar_rel)
    packet = _read_vault_relative_json(vault, packet_rel)
    visual_meta = (
        (sidecar.get("extra_metadata") or {}).get("visual_capture")
        if isinstance(sidecar.get("extra_metadata"), dict)
        else {}
    )
    if not isinstance(visual_meta, dict):
        visual_meta = {}
    packet_routing = packet.get("routing") if isinstance(packet.get("routing"), dict) else {}
    local_image_text = (
        visual_meta.get("local_optical_character_recognition")
        if isinstance(visual_meta.get("local_optical_character_recognition"), dict)
        else {}
    )
    attachment_review_policy = (
        visual_meta.get("attachment_review_policy")
        if isinstance(visual_meta.get("attachment_review_policy"), dict)
        else {}
    )
    content_text = _read_vault_relative_text(vault, markdown_relative_path)
    content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest() if content_text else ""
    operator_review_state = sidecar.get("operator_review_state")
    visual_operator_review_state = visual_meta.get("operator_review_state")
    packet_operator_review_state = packet_routing.get("operator_review_state")
    return {
        "content_path": markdown_relative_path,
        "sidecar_path": sidecar_rel,
        "visual_capture_packet_path": packet_rel,
        "sidecar_exists": bool(sidecar),
        "visual_capture_packet_exists": bool(packet),
        "sidecar_review_status": sidecar.get("review_status") or sidecar.get("quarantine_status") or "",
        "visual_capture_review_status": visual_meta.get("review_status") or "",
        "packet_review_status": packet_routing.get("review_status") or "",
        "sidecar_operator_review_state": operator_review_state if isinstance(operator_review_state, dict) else {},
        "visual_capture_operator_review_state": (
            visual_operator_review_state if isinstance(visual_operator_review_state, dict) else {}
        ),
        "packet_operator_review_state": (
            packet_operator_review_state if isinstance(packet_operator_review_state, dict) else {}
        ),
        "review_history_count": len(sidecar.get("review_history") or [])
        if isinstance(sidecar.get("review_history"), list)
        else 0,
        "content_sha256": content_hash,
        "sidecar_content_sha256": str(sidecar.get("content_sha256") or ""),
        "content_hash_matches_sidecar": bool(content_hash)
        and content_hash == str(sidecar.get("content_sha256") or ""),
        "capture_method": visual_meta.get("method") or "",
        "extraction_status": visual_meta.get("extraction_status") or "",
        "local_optical_character_recognition": local_image_text,
        "attachment_review_policy": attachment_review_policy,
    }


def _is_raw_quarantine_markdown_path(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/")
    return normalized.startswith("03_INPUTS/00_QUARANTINE/") and normalized.endswith(".md")


def _filter_markdown_delta_by_path(
    markdown_delta: dict[str, list[str]],
    predicate: Any,
) -> dict[str, list[str]]:
    return {
        key: [path for path in list(markdown_delta.get(key) or []) if predicate(path)]
        for key in ("added", "removed", "modified")
    }


def _assess_capture_markdown_action_output(
    vault: Path,
    *,
    action_result: dict[str, Any],
    markdown_delta: dict[str, list[str]],
    approval_delta: dict[str, list[str]],
    source_pack_delta: dict[str, list[str]],
    payload: dict[str, str],
) -> dict[str, Any]:
    added_markdown = list(markdown_delta.get("added") or [])
    removed_markdown = list(markdown_delta.get("removed") or [])
    modified_markdown = list(markdown_delta.get("modified") or [])
    raw_quarantine_delta = _filter_markdown_delta_by_path(markdown_delta, _is_raw_quarantine_markdown_path)
    ignored_markdown_delta = _filter_markdown_delta_by_path(
        markdown_delta,
        lambda path: not _is_raw_quarantine_markdown_path(path),
    )
    quarantine_markdown = list(raw_quarantine_delta.get("added") or [])
    output_text = "\n\n".join(_read_vault_relative_text(vault, path) for path in quarantine_markdown)
    review_evidence = _capture_review_artifact_evidence(
        vault,
        quarantine_markdown[0] if len(quarantine_markdown) == 1 else "",
    )
    expected_review_decision = str(payload.get("review_decision") or "reviewed")
    save_action_message = str(action_result.get("save_action_message") or "")
    action_message = str(action_result.get("action_message") or "")
    preview_text = str(action_result.get("preview_text") or "")
    recent_text = str(action_result.get("recent_text") or "")
    body_text = str(action_result.get("body_text") or "")
    source_card_proof = (
        action_result.get("source_card_proof")
        if isinstance(action_result.get("source_card_proof"), dict)
        else {}
    )
    release_readiness_proof = (
        action_result.get("release_readiness_proof")
        if isinstance(action_result.get("release_readiness_proof"), dict)
        else {}
    )
    shortcut_proof = (
        action_result.get("shortcut_proof")
        if isinstance(action_result.get("shortcut_proof"), dict)
        else {}
    )
    review_proof_before = (
        action_result.get("review_proof_before")
        if isinstance(action_result.get("review_proof_before"), dict)
        else {}
    )
    review_proof_after = (
        action_result.get("review_proof_after")
        if isinstance(action_result.get("review_proof_after"), dict)
        else {}
    )
    source_pack_proof = (
        action_result.get("source_pack_proof")
        if isinstance(action_result.get("source_pack_proof"), dict)
        else {}
    )
    source_pack_added = list(source_pack_delta.get("added") or [])
    source_pack_modified_or_removed = list(source_pack_delta.get("modified") or []) + list(
        source_pack_delta.get("removed") or []
    )

    checks = [
        {
            "name": "packaged_action_script_completed",
            "ok": bool(action_result.get("ok")),
            "detail": str(action_result.get("status") or action_result.get("error") or "unknown"),
        },
        {
            "name": "capture_source_cards_visible",
            "ok": bool(source_card_proof.get("required_present")),
            "detail": "all expected Capture source cards are present",
        },
        {
            "name": "capture_available_source_cards_visible",
            "ok": bool(source_card_proof.get("available_inputs_visible")),
            "detail": "explicit source inputs are shown as available",
        },
        {
            "name": "capture_live_source_cards_gated",
            "ok": bool(source_card_proof.get("explicit_chaseos_browser_page_collector_settings_gated"))
            and (
                bool(source_card_proof.get("blocked_collectors_visible"))
                or (
                    bool(source_card_proof.get("browser_extension_capture_settings_gated"))
                    and bool(source_card_proof.get("live_discord_command_capture_settings_gated"))
                )
            ),
            "detail": "live browser and Discord source paths are visible and Settings-gated",
        },
        {
            "name": "capture_explicit_screen_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_screen_collector_visible"))
            and bool(source_card_proof.get("explicit_screen_collector_settings_gated")),
            "detail": "explicit screen capture is present and gated by Settings plus click",
        },
        {
            "name": "capture_explicit_clipboard_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_clipboard_collector_visible"))
            and bool(source_card_proof.get("explicit_clipboard_collector_settings_gated")),
            "detail": "explicit clipboard text capture is present and gated by Settings plus click",
        },
        {
            "name": "capture_explicit_browser_artifact_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_browser_artifact_collector_visible"))
            and bool(source_card_proof.get("explicit_browser_artifact_collector_settings_gated")),
            "detail": "explicit browser artifact capture is present and gated by Settings plus click",
        },
        {
            "name": "capture_explicit_chaseos_browser_page_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_chaseos_browser_page_collector_visible"))
            and bool(source_card_proof.get("explicit_chaseos_browser_page_collector_settings_gated")),
            "detail": "explicit ChaseOS-owned browser page capture is present and gated by Settings plus click",
        },
        {
            "name": "capture_explicit_discord_artifact_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_discord_artifact_collector_visible"))
            and bool(source_card_proof.get("explicit_discord_artifact_collector_settings_gated")),
            "detail": "explicit Discord artifact capture is present and gated by Settings plus click",
        },
        {
            "name": "capture_downstream_consumer_cards_visible",
            "ok": bool(source_card_proof.get("downstream_consumers_visible")),
            "detail": "downstream consumers are shown as approval-gated",
        },
        {
            "name": "capture_source_card_selects_manual_text",
            "ok": bool(source_card_proof.get("manual_text_selects_source_mode")),
            "detail": "manual text source card selects the manual text mode",
        },
        {
            "name": "capture_release_readiness_surface_visible",
            "ok": bool(release_readiness_proof.get("visible"))
            and bool(release_readiness_proof.get("ready_now_visible"))
            and bool(release_readiness_proof.get("release_distribution_visible"))
            and bool(release_readiness_proof.get("approval_gated_downstream_visible"))
            and bool(release_readiness_proof.get("release_proof_open_visible")),
            "detail": str(release_readiness_proof.get("status") or "missing release readiness"),
        },
        {
            "name": "capture_release_distribution_public_signing_visible",
            "ok": bool(release_readiness_proof.get("public_signing_status_visible")),
            "detail": str(release_readiness_proof.get("text") or "")[:500],
        },
        {
            "name": "settings_capture_shortcuts_visible",
            "ok": bool(shortcut_proof.get("settings_section_visible"))
            and bool(shortcut_proof.get("required_rows_present")),
            "detail": "Settings Capture shortcut rows are visible",
        },
        {
            "name": "settings_default_capture_shortcuts_visible",
            "ok": bool(shortcut_proof.get("default_open_chord_visible"))
            and bool(shortcut_proof.get("default_focus_chord_visible")),
            "detail": "default Studio-window Capture shortcuts are visible",
        },
        {
            "name": "settings_collector_shortcuts_visible",
            "ok": bool(shortcut_proof.get("collector_shortcut_rows_visible"))
            and bool(shortcut_proof.get("collector_shortcut_rows_configurable")),
            "detail": "explicit collector shortcut rows are visible and configurable inside Studio",
        },
        {
            "name": "settings_shortcut_input_captures_chord",
            "ok": bool(shortcut_proof.get("shortcut_input_capture_ok")),
            "detail": "Capture shortcut input accepts a pressed chord",
        },
        {
            "name": "settings_blocked_global_capture_shortcut_disabled",
            "ok": bool(shortcut_proof.get("blocked_shortcut_disabled")),
            "detail": "blocked global capture shortcut fields stay disabled",
        },
        {
            "name": "studio_window_capture_shortcut_navigates",
            "ok": bool(shortcut_proof.get("studio_shortcut_navigation_ok")),
            "detail": "Studio-window Capture shortcut navigates back to Capture",
        },
        {
            "name": "visible_save_message",
            "ok": payload["saved_message"].lower() in save_action_message.lower()
            or payload["saved_message"].lower() in action_message.lower()
            or payload["saved_message"].lower() in body_text.lower(),
            "detail": (save_action_message or action_message)[:240],
        },
        {
            "name": "visible_review_controls_for_saved_capture",
            "ok": bool(review_proof_before.get("title_visible"))
            and bool(review_proof_before.get("review_controls_visible"))
            and bool(review_proof_before.get("review_path_present")),
            "detail": str(review_proof_before.get("item_text") or "")[:240],
        },
        {
            "name": "visible_review_message",
            "ok": expected_review_decision in action_message.lower()
            and "review" in action_message.lower(),
            "detail": action_message[:240],
        },
        {
            "name": "recent_capture_review_status_updated",
            "ok": str(review_proof_after.get("selected_decision") or "") == expected_review_decision
            and expected_review_decision in str(review_proof_after.get("item_text") or "").lower(),
            "detail": str(review_proof_after.get("item_text") or "")[:240],
        },
        {
            "name": "source_pack_write_result_card_visible",
            "ok": (
                not source_pack_proof
                or (
                    bool(source_pack_proof.get("write_result_visible"))
                    and "Source-Pack Write" in str(source_pack_proof.get("text") or "")
                )
            ),
            "detail": (
                str(source_pack_proof.get("write_message") or "")[:240]
                if source_pack_proof
                else "not required for manual text packaged proof"
            ),
        },
        {
            "name": "source_pack_downstream_boundary_visible",
            "ok": (
                not source_pack_proof
                or (
                    bool(source_pack_proof.get("boundary_visible"))
                    and bool(source_pack_proof.get("downstream_boundary_visible"))
                )
            ),
            "detail": (
                str(source_pack_proof.get("text") or "")[:240]
                if source_pack_proof
                else "not required for manual text packaged proof"
            ),
        },
        {
            "name": "source_pack_aor_readiness_result_visible",
            "ok": (
                not source_pack_proof
                or (
                    bool(source_pack_proof.get("aor_readiness_result_visible"))
                    and bool(source_pack_proof.get("aor_approval_design_button_visible"))
                )
            ),
            "detail": (
                str(source_pack_proof.get("text") or "")[:240]
                if source_pack_proof
                else "not required for manual text packaged proof"
            ),
        },
        {
            "name": "source_pack_artifacts_added_create_only",
            "ok": (
                not source_pack_proof
                or (
                    len(source_pack_added) >= 3
                    and not source_pack_modified_or_removed
                    and all(path.startswith("runtime/acquisition/packs/") for path in source_pack_added)
                )
            ),
            "detail": _snapshot_delta_detail(source_pack_delta),
        },
        {
            "name": "visible_preview_contains_capture_markdown",
            "ok": payload["preview_marker"] in preview_text or payload["preview_marker"] in body_text,
            "detail": payload["preview_marker"],
        },
        {
            "name": "recent_capture_contains_new_title",
            "ok": payload["title"] in recent_text or payload["title"] in body_text,
            "detail": payload["title"],
        },
        {
            "name": "exactly_one_quarantine_markdown_added",
            "ok": len(quarantine_markdown) == 1
            and not raw_quarantine_delta.get("removed")
            and not raw_quarantine_delta.get("modified"),
            "detail": (
                f"raw_quarantine={_snapshot_delta_detail(raw_quarantine_delta)}; "
                f"ignored_unrelated={_snapshot_delta_detail(ignored_markdown_delta)}"
            ),
        },
        {
            "name": "output_markdown_contains_title",
            "ok": payload["title"] in output_text,
            "detail": quarantine_markdown[0] if quarantine_markdown else "no quarantine markdown",
        },
        {
            "name": "output_markdown_contains_raw_text",
            "ok": payload["raw_text"] in output_text,
            "detail": payload["token"],
        },
        {
            "name": "output_markdown_contains_source_url",
            "ok": payload["source_url"] in output_text,
            "detail": payload["source_url"],
        },
        {
            "name": "review_sidecar_updated_to_reviewed",
            "ok": bool(review_evidence.get("sidecar_exists"))
            and review_evidence.get("sidecar_review_status") == expected_review_decision
            and review_evidence.get("visual_capture_review_status") == expected_review_decision
            and (
                review_evidence.get("sidecar_operator_review_state") or {}
            ).get("new_status")
            == expected_review_decision,
            "detail": review_evidence.get("sidecar_path") or "no sidecar",
        },
        {
            "name": "review_packet_updated_to_reviewed",
            "ok": bool(review_evidence.get("visual_capture_packet_exists"))
            and review_evidence.get("packet_review_status") == expected_review_decision
            and (
                review_evidence.get("packet_operator_review_state") or {}
            ).get("new_status")
            == expected_review_decision,
            "detail": review_evidence.get("visual_capture_packet_path") or "no packet",
        },
        {
            "name": "review_did_not_rewrite_markdown_body",
            "ok": bool(review_evidence.get("content_hash_matches_sidecar")),
            "detail": review_evidence.get("content_path") or "no content",
        },
    ]
    blockers = [
        f"{check['name']} failed: {check['detail']}"
        for check in checks
        if not bool(check.get("ok"))
    ]
    return {
        "ok": not blockers,
        "checks": checks,
        "blockers": blockers,
        "output_markdown_paths": quarantine_markdown,
        "output_markdown_preview": output_text[:4000],
        "raw_quarantine_markdown_delta": raw_quarantine_delta,
        "ignored_unrelated_markdown_delta": ignored_markdown_delta,
        "source_pack_artifact_delta": source_pack_delta,
        "review_artifact_evidence": review_evidence,
    }


def _assess_capture_markdown_guard_failure_output(
    vault: Path,
    *,
    action_result: dict[str, Any],
    markdown_delta: dict[str, list[str]],
    approval_delta: dict[str, list[str]],
    source_pack_delta: dict[str, list[str]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    raw_quarantine_delta = _filter_markdown_delta_by_path(markdown_delta, _is_raw_quarantine_markdown_path)
    ignored_markdown_delta = _filter_markdown_delta_by_path(
        markdown_delta,
        lambda path: not _is_raw_quarantine_markdown_path(path),
    )
    quarantine_markdown = list(raw_quarantine_delta.get("added") or [])
    output_text = "\n\n".join(_read_vault_relative_text(vault, path) for path in quarantine_markdown)
    review_evidence = _capture_review_artifact_evidence(
        vault,
        quarantine_markdown[0] if len(quarantine_markdown) == 1 else "",
    )
    expected_review_decision = str(payload.get("review_decision") or "reviewed")
    save_action_message = str(action_result.get("save_action_message") or "")
    action_message = str(action_result.get("action_message") or "")
    preview_text = str(action_result.get("preview_text") or "")
    body_text = str(action_result.get("body_text") or "")
    source_card_proof = (
        action_result.get("source_card_proof")
        if isinstance(action_result.get("source_card_proof"), dict)
        else {}
    )
    release_readiness_proof = (
        action_result.get("release_readiness_proof")
        if isinstance(action_result.get("release_readiness_proof"), dict)
        else {}
    )
    shortcut_proof = (
        action_result.get("shortcut_proof")
        if isinstance(action_result.get("shortcut_proof"), dict)
        else {}
    )
    review_proof_before = (
        action_result.get("review_proof_before")
        if isinstance(action_result.get("review_proof_before"), dict)
        else {}
    )
    review_proof_after = (
        action_result.get("review_proof_after")
        if isinstance(action_result.get("review_proof_after"), dict)
        else {}
    )
    source_pack_proof = (
        action_result.get("source_pack_proof")
        if isinstance(action_result.get("source_pack_proof"), dict)
        else {}
    )
    guard_text = str(source_pack_proof.get("guard_failure_text") or "")
    expected_guard_text = str(payload.get("guard_failure_expected_text") or "Source-pack write blocked")

    checks = [
        {
            "name": "packaged_guard_failure_script_completed",
            "ok": bool(action_result.get("ok")) and action_result.get("status") == "guard_failure_visible",
            "detail": str(action_result.get("status") or action_result.get("error") or "unknown"),
        },
        {
            "name": "capture_source_cards_visible",
            "ok": bool(source_card_proof.get("required_present")),
            "detail": "all expected Capture source cards are present",
        },
        {
            "name": "capture_explicit_browser_artifact_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_browser_artifact_collector_visible"))
            and bool(source_card_proof.get("explicit_browser_artifact_collector_settings_gated")),
            "detail": "explicit browser artifact capture is present and gated by Settings plus click",
        },
        {
            "name": "capture_explicit_discord_artifact_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_discord_artifact_collector_visible"))
            and bool(source_card_proof.get("explicit_discord_artifact_collector_settings_gated")),
            "detail": "explicit Discord artifact capture is present and gated by Settings plus click",
        },
        {
            "name": "capture_release_readiness_surface_visible",
            "ok": bool(release_readiness_proof.get("visible"))
            and bool(release_readiness_proof.get("approval_gated_downstream_visible")),
            "detail": str(release_readiness_proof.get("status") or "missing release readiness"),
        },
        {
            "name": "settings_collector_shortcuts_visible",
            "ok": bool(shortcut_proof.get("collector_shortcut_rows_visible"))
            and bool(shortcut_proof.get("collector_shortcut_rows_configurable")),
            "detail": "explicit collector shortcut rows are visible and configurable inside Studio",
        },
        {
            "name": "visible_save_message",
            "ok": str(payload.get("saved_message") or "").lower() in save_action_message.lower()
            or str(payload.get("saved_message") or "").lower() in action_message.lower()
            or str(payload.get("saved_message") or "").lower() in body_text.lower(),
            "detail": (save_action_message or action_message)[:240],
        },
        {
            "name": "visible_review_controls_for_saved_capture",
            "ok": bool(review_proof_before.get("title_visible"))
            and bool(review_proof_before.get("review_controls_visible"))
            and bool(review_proof_before.get("review_path_present")),
            "detail": str(review_proof_before.get("item_text") or "")[:240],
        },
        {
            "name": "recent_capture_review_status_updated",
            "ok": str(review_proof_after.get("selected_decision") or "") == expected_review_decision
            and expected_review_decision in str(review_proof_after.get("item_text") or "").lower(),
            "detail": str(review_proof_after.get("item_text") or "")[:240],
        },
        {
            "name": "source_pack_approval_preview_result_card_visible",
            "ok": bool(source_pack_proof.get("preview_visible"))
            and bool(source_pack_proof.get("write_button_visible")),
            "detail": str(source_pack_proof.get("text") or "")[:240],
        },
        {
            "name": "source_pack_guard_failure_result_card_visible",
            "ok": bool(source_pack_proof.get("guard_failure_visible"))
            and expected_guard_text.lower() in guard_text.lower()
            and "no downstream write" in guard_text.lower(),
            "detail": guard_text[:240],
        },
        {
            "name": "guard_failure_output_still_contains_preview",
            "ok": str(payload.get("preview_marker") or "") in preview_text
            or str(payload.get("preview_marker") or "") in body_text,
            "detail": str(payload.get("preview_marker") or ""),
        },
        {
            "name": "exactly_one_quarantine_markdown_added",
            "ok": len(quarantine_markdown) == 1
            and not raw_quarantine_delta.get("removed")
            and not raw_quarantine_delta.get("modified"),
            "detail": (
                f"raw_quarantine={_snapshot_delta_detail(raw_quarantine_delta)}; "
                f"ignored_unrelated={_snapshot_delta_detail(ignored_markdown_delta)}"
            ),
        },
        {
            "name": "output_markdown_contains_raw_text",
            "ok": str(payload.get("raw_text") or "") in output_text,
            "detail": str(payload.get("token") or ""),
        },
        {
            "name": "review_sidecar_updated_to_reviewed",
            "ok": bool(review_evidence.get("sidecar_exists"))
            and review_evidence.get("sidecar_review_status") == expected_review_decision,
            "detail": review_evidence.get("sidecar_path") or "no sidecar",
        },
        {
            "name": "source_pack_guard_failure_writes_no_source_pack_artifacts",
            "ok": not _snapshot_delta_changed(source_pack_delta),
            "detail": _snapshot_delta_detail(source_pack_delta),
        },
        {
            "name": "source_pack_guard_failure_writes_no_approval_artifacts",
            "ok": not _snapshot_delta_changed(approval_delta),
            "detail": _snapshot_delta_detail(approval_delta),
        },
    ]
    blockers = [
        f"{check['name']} failed: {check['detail']}"
        for check in checks
        if not bool(check.get("ok"))
    ]
    return {
        "ok": not blockers,
        "checks": checks,
        "blockers": blockers,
        "output_markdown_paths": quarantine_markdown,
        "output_markdown_preview": output_text[:4000],
        "raw_quarantine_markdown_delta": raw_quarantine_delta,
        "ignored_unrelated_markdown_delta": ignored_markdown_delta,
        "source_pack_artifact_delta": source_pack_delta,
        "approval_artifact_delta": approval_delta,
        "review_artifact_evidence": review_evidence,
    }


def _delta_paths_with_prefixes(
    delta: dict[str, list[str]],
    prefixes: list[str] | tuple[str, ...],
) -> dict[str, list[str]]:
    normalized = tuple(str(prefix).replace("\\", "/").lstrip("./") for prefix in prefixes if str(prefix))
    if not normalized:
        return {"added": [], "modified": [], "removed": []}
    blocked: dict[str, list[str]] = {}
    for key in ("added", "modified", "removed"):
        blocked[key] = [
            path
            for path in (delta.get(key) or [])
            if path.replace("\\", "/").lstrip("./").startswith(normalized)
        ]
    return blocked


def _assess_capture_markdown_downstream_failure_output(
    vault: Path,
    *,
    action_result: dict[str, Any],
    markdown_delta: dict[str, list[str]],
    approval_delta: dict[str, list[str]],
    source_pack_delta: dict[str, list[str]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    raw_quarantine_delta = _filter_markdown_delta_by_path(markdown_delta, _is_raw_quarantine_markdown_path)
    ignored_markdown_delta = _filter_markdown_delta_by_path(
        markdown_delta,
        lambda path: not _is_raw_quarantine_markdown_path(path),
    )
    quarantine_markdown = list(raw_quarantine_delta.get("added") or [])
    output_text = "\n\n".join(_read_vault_relative_text(vault, path) for path in quarantine_markdown)
    review_evidence = _capture_review_artifact_evidence(
        vault,
        quarantine_markdown[0] if len(quarantine_markdown) == 1 else "",
    )
    expected_review_decision = str(payload.get("review_decision") or "reviewed")
    save_action_message = str(action_result.get("save_action_message") or "")
    action_message = str(action_result.get("action_message") or "")
    preview_text = str(action_result.get("preview_text") or "")
    body_text = str(action_result.get("body_text") or "")
    source_card_proof = (
        action_result.get("source_card_proof")
        if isinstance(action_result.get("source_card_proof"), dict)
        else {}
    )
    release_readiness_proof = (
        action_result.get("release_readiness_proof")
        if isinstance(action_result.get("release_readiness_proof"), dict)
        else {}
    )
    shortcut_proof = (
        action_result.get("shortcut_proof")
        if isinstance(action_result.get("shortcut_proof"), dict)
        else {}
    )
    review_proof_before = (
        action_result.get("review_proof_before")
        if isinstance(action_result.get("review_proof_before"), dict)
        else {}
    )
    review_proof_after = (
        action_result.get("review_proof_after")
        if isinstance(action_result.get("review_proof_after"), dict)
        else {}
    )
    source_pack_proof = (
        action_result.get("source_pack_proof")
        if isinstance(action_result.get("source_pack_proof"), dict)
        else {}
    )
    case = payload.get("downstream_failure_case") if isinstance(payload.get("downstream_failure_case"), dict) else {}
    case_id = str(payload.get("downstream_failure_case_id") or case.get("id") or "")
    expected_case_id = str(action_result.get("downstream_failure_case_id") or "")
    expected_guard_text = str(payload.get("downstream_failure_expected_text") or case.get("expected_text") or "blocked")
    guard_text = str(source_pack_proof.get("guard_failure_text") or "")
    result_selectors = (
        source_pack_proof.get("result_selectors")
        if isinstance(source_pack_proof.get("result_selectors"), dict)
        else {}
    )
    source_pack_added = list(source_pack_delta.get("added") or [])
    source_pack_modified_or_removed = list(source_pack_delta.get("modified") or []) + list(
        source_pack_delta.get("removed") or []
    )
    forbidden_delta = _delta_paths_with_prefixes(
        approval_delta,
        [str(item) for item in (case.get("forbidden_artifact_prefixes") or [])],
    )
    required_selectors = [str(item) for item in (case.get("required_result_selectors") or [])]
    success_selector = str(case.get("success_selector") or "")

    checks = [
        {
            "name": "packaged_downstream_failure_script_completed",
            "ok": bool(action_result.get("ok"))
            and action_result.get("status") == "downstream_failure_visible"
            and expected_case_id == case_id,
            "detail": str(action_result.get("status") or action_result.get("error") or "unknown"),
        },
        {
            "name": "capture_source_cards_visible",
            "ok": bool(source_card_proof.get("required_present")),
            "detail": "all expected Capture source cards are present",
        },
        {
            "name": "capture_release_readiness_surface_visible",
            "ok": bool(release_readiness_proof.get("visible"))
            and bool(release_readiness_proof.get("approval_gated_downstream_visible")),
            "detail": str(release_readiness_proof.get("status") or "missing release readiness"),
        },
        {
            "name": "settings_collector_shortcuts_visible",
            "ok": bool(shortcut_proof.get("collector_shortcut_rows_visible"))
            and bool(shortcut_proof.get("collector_shortcut_rows_configurable")),
            "detail": "explicit collector shortcut rows are visible and configurable inside Studio",
        },
        {
            "name": "visible_save_message",
            "ok": str(payload.get("saved_message") or "").lower() in save_action_message.lower()
            or str(payload.get("saved_message") or "").lower() in action_message.lower()
            or str(payload.get("saved_message") or "").lower() in body_text.lower(),
            "detail": (save_action_message or action_message)[:240],
        },
        {
            "name": "visible_review_controls_for_saved_capture",
            "ok": bool(review_proof_before.get("title_visible"))
            and bool(review_proof_before.get("review_controls_visible"))
            and bool(review_proof_before.get("review_path_present")),
            "detail": str(review_proof_before.get("item_text") or "")[:240],
        },
        {
            "name": "recent_capture_review_status_updated",
            "ok": str(review_proof_after.get("selected_decision") or "") == expected_review_decision
            and expected_review_decision in str(review_proof_after.get("item_text") or "").lower(),
            "detail": str(review_proof_after.get("item_text") or "")[:240],
        },
        {
            "name": "source_pack_write_result_card_visible",
            "ok": bool(source_pack_proof.get("write_result_visible"))
            and bool(source_pack_proof.get("boundary_visible")),
            "detail": str(source_pack_proof.get("text") or "")[:240],
        },
        {
            "name": "downstream_failure_reached_expected_boundary",
            "ok": all(bool(result_selectors.get(selector)) for selector in required_selectors),
            "detail": ", ".join(selector for selector in required_selectors if not result_selectors.get(selector))
            or case_id,
        },
        {
            "name": "downstream_failure_success_result_not_written",
            "ok": not success_selector or not bool(result_selectors.get(success_selector)),
            "detail": success_selector or "no success selector",
        },
        {
            "name": "downstream_failure_guard_card_visible",
            "ok": bool(source_pack_proof.get("guard_failure_visible"))
            and expected_guard_text.lower() in guard_text.lower()
            and "no downstream write" in guard_text.lower(),
            "detail": guard_text[:240],
        },
        {
            "name": "exactly_one_quarantine_markdown_added",
            "ok": len(quarantine_markdown) == 1
            and not raw_quarantine_delta.get("removed")
            and not raw_quarantine_delta.get("modified"),
            "detail": (
                f"raw_quarantine={_snapshot_delta_detail(raw_quarantine_delta)}; "
                f"ignored_unrelated={_snapshot_delta_detail(ignored_markdown_delta)}"
            ),
        },
        {
            "name": "output_markdown_contains_raw_text",
            "ok": str(payload.get("raw_text") or "") in output_text,
            "detail": str(payload.get("token") or ""),
        },
        {
            "name": "guard_failure_output_still_contains_preview",
            "ok": str(payload.get("preview_marker") or "") in preview_text
            or str(payload.get("preview_marker") or "") in body_text,
            "detail": str(payload.get("preview_marker") or ""),
        },
        {
            "name": "review_sidecar_updated_to_reviewed",
            "ok": bool(review_evidence.get("sidecar_exists"))
            and review_evidence.get("sidecar_review_status") == expected_review_decision,
            "detail": review_evidence.get("sidecar_path") or "no sidecar",
        },
        {
            "name": "downstream_failure_source_pack_artifacts_added_create_only",
            "ok": len(source_pack_added) >= 3
            and not source_pack_modified_or_removed
            and all(path.startswith("runtime/acquisition/packs/") for path in source_pack_added),
            "detail": _snapshot_delta_detail(source_pack_delta),
        },
        {
            "name": "downstream_failure_forbidden_artifacts_not_written",
            "ok": not _snapshot_delta_changed(forbidden_delta),
            "detail": _snapshot_delta_detail(forbidden_delta),
        },
        {
            "name": "downstream_failure_approval_artifacts_create_only",
            "ok": not approval_delta.get("removed") and not approval_delta.get("modified"),
            "detail": _snapshot_delta_detail(approval_delta),
        },
    ]
    blockers = [
        f"{check['name']} failed: {check['detail']}"
        for check in checks
        if not bool(check.get("ok"))
    ]
    return {
        "ok": not blockers,
        "checks": checks,
        "blockers": blockers,
        "output_markdown_paths": quarantine_markdown,
        "output_markdown_preview": output_text[:4000],
        "raw_quarantine_markdown_delta": raw_quarantine_delta,
        "ignored_unrelated_markdown_delta": ignored_markdown_delta,
        "source_pack_artifact_delta": source_pack_delta,
        "approval_artifact_delta": approval_delta,
        "forbidden_artifact_delta": forbidden_delta,
        "case_id": case_id,
        "review_artifact_evidence": review_evidence,
    }


def _assess_capture_markdown_image_text_output(
    vault: Path,
    *,
    action_result: dict[str, Any],
    markdown_delta: dict[str, list[str]],
    approval_delta: dict[str, list[str]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    raw_quarantine_delta = _filter_markdown_delta_by_path(markdown_delta, _is_raw_quarantine_markdown_path)
    ignored_markdown_delta = _filter_markdown_delta_by_path(
        markdown_delta,
        lambda path: not _is_raw_quarantine_markdown_path(path),
    )
    quarantine_markdown = list(raw_quarantine_delta.get("added") or [])
    output_text = "\n\n".join(_read_vault_relative_text(vault, path) for path in quarantine_markdown)
    review_evidence = _capture_review_artifact_evidence(
        vault,
        quarantine_markdown[0] if len(quarantine_markdown) == 1 else "",
    )
    local_image_text = (
        review_evidence.get("local_optical_character_recognition")
        if isinstance(review_evidence.get("local_optical_character_recognition"), dict)
        else {}
    )
    attachment_policy = (
        review_evidence.get("attachment_review_policy")
        if isinstance(review_evidence.get("attachment_review_policy"), dict)
        else {}
    )
    expected_review_decision = str(payload.get("review_decision") or "reviewed")
    save_action_message = str(action_result.get("save_action_message") or "")
    action_message = str(action_result.get("action_message") or "")
    preview_text = str(action_result.get("preview_text") or "")
    recent_text = str(action_result.get("recent_text") or "")
    body_text = str(action_result.get("body_text") or "")
    source_card_proof = (
        action_result.get("source_card_proof")
        if isinstance(action_result.get("source_card_proof"), dict)
        else {}
    )
    settings_proof = (
        action_result.get("settings_proof")
        if isinstance(action_result.get("settings_proof"), dict)
        else {}
    )
    form_payload = (
        action_result.get("form_payload_after_set")
        if isinstance(action_result.get("form_payload_after_set"), dict)
        else {}
    )
    review_proof_before = (
        action_result.get("review_proof_before")
        if isinstance(action_result.get("review_proof_before"), dict)
        else {}
    )
    review_proof_after = (
        action_result.get("review_proof_after")
        if isinstance(action_result.get("review_proof_after"), dict)
        else {}
    )
    marker_rel = str(payload.get("engine_marker_path") or "")
    marker_text = _read_vault_relative_text(vault, marker_rel) if marker_rel else ""

    checks = [
        {
            "name": "packaged_image_text_script_completed",
            "ok": bool(action_result.get("ok")),
            "detail": str(action_result.get("status") or action_result.get("error") or "unknown"),
        },
        {
            "name": "settings_capture_image_text_section_visible",
            "ok": bool(settings_proof.get("section_visible"))
            and bool(settings_proof.get("command_visible")),
            "detail": "Capture Image Text Settings section is visible",
        },
        {
            "name": "settings_saved_local_command_visible",
            "ok": bool(settings_proof.get("command_matches_saved_settings")),
            "detail": "local command input matches temporary proof command",
        },
        {
            "name": "settings_cloud_and_screen_capture_blocked",
            "ok": bool(settings_proof.get("cloud_extraction_blocked"))
            and bool(settings_proof.get("screen_capture_blocked")),
            "detail": "Settings copy keeps cloud extraction and screen capture blocked",
        },
        {
            "name": "capture_optical_character_recognition_source_visible",
            "ok": bool(source_card_proof.get("optical_character_recognition_visible"))
            and bool(source_card_proof.get("optical_character_recognition_selectable")),
            "detail": str(source_card_proof.get("optical_character_recognition_local_status") or ""),
        },
        {
            "name": "capture_optical_character_recognition_selects_image_text_mode",
            "ok": bool(source_card_proof.get("optical_character_recognition_selects_source_mode"))
            and bool(source_card_proof.get("local_command_row_visible")),
            "detail": "source card selects screenshot text extraction and shows local command row",
        },
        {
            "name": "live_collectors_remain_blocked",
            "ok": bool(source_card_proof.get("live_collectors_blocked")),
            "detail": "active browser and Discord collectors remain blocked",
        },
        {
            "name": "explicit_screen_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_screen_collector_settings_gated")),
            "detail": "explicit screen capture is Settings-gated and click-only",
        },
        {
            "name": "explicit_clipboard_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_clipboard_collector_settings_gated")),
            "detail": "explicit clipboard text capture is Settings-gated and click-only",
        },
        {
            "name": "downstream_consumers_remain_approval_gated",
            "ok": bool(source_card_proof.get("downstream_consumers_visible")),
            "detail": "Source Intelligence Core, canonical promotion, and agent dispatch remain gated",
        },
        {
            "name": "per_capture_command_blank_so_settings_command_is_used",
            "ok": str(form_payload.get("local_ocr_command") or "") == "",
            "detail": "per-capture local command field was blank before preview",
        },
        {
            "name": "explicit_vault_image_path_used",
            "ok": str(form_payload.get("file_path") or "") == str(payload.get("file_path") or ""),
            "detail": str(payload.get("file_path") or ""),
        },
        {
            "name": "visible_preview_contains_extracted_image_text",
            "ok": str(payload.get("extracted_text") or "") in preview_text
            or str(payload.get("extracted_text") or "") in body_text,
            "detail": str(payload.get("extracted_text") or "")[:240],
        },
        {
            "name": "visible_save_message",
            "ok": str(payload.get("saved_message") or "").lower() in save_action_message.lower()
            or str(payload.get("saved_message") or "").lower() in action_message.lower()
            or str(payload.get("saved_message") or "").lower() in body_text.lower(),
            "detail": (save_action_message or action_message)[:240],
        },
        {
            "name": "visible_review_controls_for_saved_image_text_capture",
            "ok": bool(review_proof_before.get("title_visible"))
            and bool(review_proof_before.get("review_controls_visible"))
            and bool(review_proof_before.get("review_path_present")),
            "detail": str(review_proof_before.get("item_text") or "")[:240],
        },
        {
            "name": "recent_capture_review_status_updated",
            "ok": str(review_proof_after.get("selected_decision") or "") == expected_review_decision
            and expected_review_decision in str(review_proof_after.get("item_text") or "").lower(),
            "detail": str(review_proof_after.get("item_text") or "")[:240],
        },
        {
            "name": "exactly_one_quarantine_markdown_added",
            "ok": len(quarantine_markdown) == 1
            and not raw_quarantine_delta.get("removed")
            and not raw_quarantine_delta.get("modified"),
            "detail": (
                f"raw_quarantine={_snapshot_delta_detail(raw_quarantine_delta)}; "
                f"ignored_unrelated={_snapshot_delta_detail(ignored_markdown_delta)}"
            ),
        },
        {
            "name": "output_markdown_contains_extracted_image_text",
            "ok": str(payload.get("extracted_text") or "") in output_text,
            "detail": quarantine_markdown[0] if quarantine_markdown else "no quarantine markdown",
        },
        {
            "name": "output_markdown_contains_source_url",
            "ok": str(payload.get("source_url") or "") in output_text,
            "detail": str(payload.get("source_url") or ""),
        },
        {
            "name": "output_markdown_records_text_extraction_status",
            "ok": "optical_character_recognition_status: text_extracted" in output_text,
            "detail": "markdown metadata records local image text extraction",
        },
        {
            "name": "local_image_text_engine_command_ran_only_for_explicit_preview",
            "ok": marker_text.strip() == "ran",
            "detail": marker_rel or "no marker",
        },
        {
            "name": "review_sidecar_records_image_text_extraction",
            "ok": bool(review_evidence.get("sidecar_exists"))
            and review_evidence.get("capture_method") == "screenshot_local_text_extraction"
            and review_evidence.get("extraction_status") == "text_extracted"
            and local_image_text.get("status") == "text_extracted"
            and local_image_text.get("engine_id") == "configured-command"
            and local_image_text.get("cloud_optical_character_recognition_allowed") is False
            and local_image_text.get("provider_call_allowed") is False,
            "detail": review_evidence.get("sidecar_path") or "no sidecar",
        },
        {
            "name": "review_policy_preserves_image_text_status",
            "ok": attachment_policy.get("ocr_status") == "text_extracted"
            and attachment_policy.get("runtime_delete_allowed") is False,
            "detail": str(attachment_policy.get("ocr_status") or ""),
        },
        {
            "name": "review_packet_updated_to_reviewed",
            "ok": bool(review_evidence.get("visual_capture_packet_exists"))
            and review_evidence.get("packet_review_status") == expected_review_decision
            and (
                review_evidence.get("packet_operator_review_state") or {}
            ).get("new_status")
            == expected_review_decision,
            "detail": review_evidence.get("visual_capture_packet_path") or "no packet",
        },
        {
            "name": "review_did_not_rewrite_markdown_body",
            "ok": bool(review_evidence.get("content_hash_matches_sidecar")),
            "detail": review_evidence.get("content_path") or "no content",
        },
        {
            "name": "no_approval_artifact_writes",
            "ok": not _snapshot_delta_changed(approval_delta),
            "detail": _snapshot_delta_detail(approval_delta),
        },
    ]
    blockers = [
        f"{check['name']} failed: {check['detail']}"
        for check in checks
        if not bool(check.get("ok"))
    ]
    return {
        "ok": not blockers,
        "checks": checks,
        "blockers": blockers,
        "output_markdown_paths": quarantine_markdown,
        "output_markdown_preview": output_text[:4000],
        "raw_quarantine_markdown_delta": raw_quarantine_delta,
        "ignored_unrelated_markdown_delta": ignored_markdown_delta,
        "review_artifact_evidence": review_evidence,
    }


def _assess_capture_markdown_image_text_failure_output(
    vault: Path,
    *,
    action_result: dict[str, Any],
    markdown_delta: dict[str, list[str]],
    approval_delta: dict[str, list[str]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    raw_quarantine_delta = _filter_markdown_delta_by_path(markdown_delta, _is_raw_quarantine_markdown_path)
    ignored_markdown_delta = _filter_markdown_delta_by_path(
        markdown_delta,
        lambda path: not _is_raw_quarantine_markdown_path(path),
    )
    expected_cases = {
        str(case.get("id") or ""): dict(case)
        for case in list(payload.get("failure_cases") or [])
        if isinstance(case, dict)
    }
    observed_cases = {
        str(case.get("id") or ""): dict(case)
        for case in list(action_result.get("failure_cases") or [])
        if isinstance(case, dict)
    }
    source_card_proof = (
        action_result.get("source_card_proof")
        if isinstance(action_result.get("source_card_proof"), dict)
        else {}
    )
    settings_proof = (
        action_result.get("settings_proof")
        if isinstance(action_result.get("settings_proof"), dict)
        else {}
    )

    case_checks: list[dict[str, Any]] = []
    for case_id, expected in expected_cases.items():
        observed = observed_cases.get(case_id, {})
        expected_text = str(expected.get("expected_text") or "")
        combined_text = " ".join(
            [
                str(observed.get("preview_text") or ""),
                str(observed.get("action_message") or ""),
                str(observed.get("body_text") or ""),
            ]
        ).lower()
        form_payload = (
            observed.get("form_payload_after_set")
            if isinstance(observed.get("form_payload_after_set"), dict)
            else {}
        )
        marker_rel = str(expected.get("marker_path") or "")
        marker_text = _read_vault_relative_text(vault, marker_rel) if marker_rel else ""
        case_checks.extend(
            [
                {
                    "name": f"image_text_failure_case_{case_id}_visible",
                    "ok": bool(observed.get("ok")) and expected_text.lower() in combined_text,
                    "detail": expected_text,
                },
                {
                    "name": f"image_text_failure_case_{case_id}_save_disabled",
                    "ok": bool(observed.get("save_disabled")),
                    "detail": "Save stayed disabled after the failure or blocker preview",
                },
                {
                    "name": f"image_text_failure_case_{case_id}_uses_explicit_image_path",
                    "ok": str(form_payload.get("file_path") or "") == str(payload.get("file_path") or ""),
                    "detail": str(form_payload.get("file_path") or ""),
                },
                {
                    "name": f"image_text_failure_case_{case_id}_uses_per_capture_command",
                    "ok": bool(str(form_payload.get("local_ocr_command") or "")),
                    "detail": "per-capture local command was set for this proof case",
                },
                {
                    "name": f"image_text_failure_case_{case_id}_local_script_marker",
                    "ok": (
                        marker_text.strip() == "ran"
                        if bool(expected.get("script_expected_to_run"))
                        else marker_text.strip() == ""
                    ),
                    "detail": marker_rel or "no marker expected",
                },
            ]
        )

    checks = [
        {
            "name": "packaged_image_text_failure_script_completed",
            "ok": bool(action_result.get("ok")),
            "detail": str(action_result.get("status") or action_result.get("error") or "unknown"),
        },
        {
            "name": "settings_capture_image_text_failure_section_visible",
            "ok": bool(settings_proof.get("section_visible"))
            and bool(settings_proof.get("command_visible"))
            and bool(settings_proof.get("timeout_visible")),
            "detail": "Capture Image Text Settings section is visible",
        },
        {
            "name": "settings_failure_timeout_visible_and_restored",
            "ok": bool(settings_proof.get("command_blank"))
            and bool(settings_proof.get("timeout_matches_saved_settings")),
            "detail": "temporary failure proof settings use blank command and one-second timeout",
        },
        {
            "name": "settings_failure_cloud_and_screen_capture_blocked",
            "ok": bool(settings_proof.get("cloud_extraction_blocked"))
            and bool(settings_proof.get("screen_capture_blocked")),
            "detail": "Settings copy keeps cloud extraction and screen capture blocked",
        },
        {
            "name": "capture_failure_optical_character_recognition_source_visible",
            "ok": bool(source_card_proof.get("optical_character_recognition_visible"))
            and bool(source_card_proof.get("optical_character_recognition_selectable")),
            "detail": str(source_card_proof.get("optical_character_recognition_local_status") or ""),
        },
        {
            "name": "capture_failure_optical_character_recognition_selects_image_text_mode",
            "ok": bool(source_card_proof.get("optical_character_recognition_selects_source_mode"))
            and bool(source_card_proof.get("local_command_row_visible")),
            "detail": "source card selects screenshot text extraction and shows local command row",
        },
        {
            "name": "failure_live_collectors_remain_blocked",
            "ok": bool(source_card_proof.get("live_collectors_blocked")),
            "detail": "active browser and Discord collectors remain blocked",
        },
        {
            "name": "failure_explicit_screen_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_screen_collector_settings_gated")),
            "detail": "explicit screen capture is Settings-gated and click-only",
        },
        {
            "name": "failure_explicit_clipboard_collector_settings_gated",
            "ok": bool(source_card_proof.get("explicit_clipboard_collector_settings_gated")),
            "detail": "explicit clipboard text capture is Settings-gated and click-only",
        },
        {
            "name": "failure_downstream_consumers_remain_approval_gated",
            "ok": bool(source_card_proof.get("downstream_consumers_visible")),
            "detail": "Source Intelligence Core, canonical promotion, and agent dispatch remain gated",
        },
        {
            "name": "all_expected_image_text_failure_cases_recorded",
            "ok": bool(expected_cases) and sorted(expected_cases) == sorted(observed_cases),
            "detail": f"expected={sorted(expected_cases)} observed={sorted(observed_cases)}",
        },
        *case_checks,
        {
            "name": "image_text_failure_states_write_no_raw_quarantine_markdown",
            "ok": not _snapshot_delta_changed(raw_quarantine_delta),
            "detail": (
                f"raw_quarantine={_snapshot_delta_detail(raw_quarantine_delta)}; "
                f"ignored_unrelated={_snapshot_delta_detail(ignored_markdown_delta)}"
            ),
        },
        {
            "name": "image_text_failure_states_write_no_approval_artifacts",
            "ok": not _snapshot_delta_changed(approval_delta),
            "detail": _snapshot_delta_detail(approval_delta),
        },
    ]
    blockers = [
        f"{check['name']} failed: {check['detail']}"
        for check in checks
        if not bool(check.get("ok"))
    ]
    return {
        "ok": not blockers,
        "checks": checks,
        "blockers": blockers,
        "output_markdown_paths": [],
        "output_markdown_preview": "",
        "raw_quarantine_markdown_delta": raw_quarantine_delta,
        "ignored_unrelated_markdown_delta": ignored_markdown_delta,
        "failure_cases": list(observed_cases.values()),
    }


def _redact_capture_markdown_payload_for_report(payload: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if key in {"raw_text", "local_ocr_command"}:
            continue
        if key == "failure_cases" and isinstance(value, list):
            redacted[key] = [
                {
                    case_key: case_value
                    for case_key, case_value in dict(case).items()
                    if case_key != "local_ocr_command"
                }
                for case in value
                if isinstance(case, dict)
            ]
            continue
        redacted[key] = value
    return redacted


def build_packaged_capture_markdown_action_clickthrough(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    screenshot_root: str | Path | None = None,
    env_overrides: dict[str, str] | None = None,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    allow_external_runtime_dirs: bool = False,
    settle_seconds: float = 10.0,
    window_timeout_seconds: float = 20.0,
    terminate_timeout_seconds: float = 5.0,
    require_nonblank: bool = True,
    min_unique_colors: int = DEFAULT_MIN_UNIQUE_COLORS,
    max_dominant_ratio: float = DEFAULT_MAX_DOMINANT_RATIO,
    run_token: str | None = None,
    capture_mode: str = "manual_text",
) -> dict[str, Any]:
    """Drive the packaged Capture page through Preview and Save controls."""

    vault = _vault_path(vault_root)
    exe = _resolve_executable(vault, executable_path or DEFAULT_EXE)
    capture_mode_id = str(capture_mode or "manual_text")
    manual_guard_failure = capture_mode_id == "manual_text_guard_failure"
    downstream_failure = capture_mode_id == "manual_text_downstream_failure" or capture_mode_id.startswith(
        "manual_text_downstream_failure:"
    )
    downstream_failure_case_id = (
        capture_mode_id.split(":", 1)[1]
        if capture_mode_id.startswith("manual_text_downstream_failure:")
        else "aor_approval_request_bad_statement"
    )
    image_text_success = capture_mode_id == "image_text"
    image_text_failure = capture_mode_id == "image_text_failure"
    image_text_mode = image_text_success or image_text_failure
    if image_text_failure:
        payload = _capture_markdown_image_text_failure_payload(vault, run_token)
    elif image_text_success:
        payload = _capture_markdown_image_text_payload(vault, run_token)
    elif downstream_failure:
        payload = _capture_markdown_downstream_failure_payload(
            run_token,
            case_id=downstream_failure_case_id,
        )
    elif manual_guard_failure:
        payload = _capture_markdown_guard_failure_payload(run_token)
    else:
        payload = _capture_markdown_action_payload(run_token)
    settings_restore: dict[str, Any] | None = None
    if image_text_mode:
        settings_restore = _write_capture_markdown_image_text_settings(vault, payload)
    panel_id = (
        CAPTURE_MARKDOWN_IMAGE_TEXT_FAILURE_PANEL_ID
        if image_text_failure
        else CAPTURE_MARKDOWN_IMAGE_TEXT_PANEL_ID
        if image_text_success
        else CAPTURE_MARKDOWN_GUARD_FAILURE_PANEL_ID
        if manual_guard_failure
        else CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_PANEL_ID
        if downstream_failure
        else CAPTURE_MARKDOWN_ACTION_PANEL_ID
    )
    slug_suffix = (
        "capture-markdown-packaged-image-text-failure-states"
        if image_text_failure
        else
        "capture-markdown-packaged-image-text-clickthrough"
        if image_text_success
        else
        "capture-markdown-packaged-guard-failure-clickthrough"
        if manual_guard_failure
        else
        "capture-markdown-packaged-downstream-failure-clickthrough"
        if downstream_failure
        else "capture-markdown-packaged-action-clickthrough"
    )
    slug = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{slug_suffix}"
    root = _resolve_screenshot_root(vault, screenshot_root, slug)
    startup_log = root / "capture-action.startup.log"
    batch_plan_path = root / "capture-action-plan.json"
    batch_result_path = root / "capture-action-result.json"
    screenshot = root / f"{panel_id}.png"
    meta_path = root / f"{panel_id}.qa-meta.json"
    action_capture_delay_ms = (
        60000
        if image_text_mode
        else 300000
        if downstream_failure and downstream_failure_case_id == "canonical_promotion_approval_request_bad_statement"
        else 120000
    )
    for stale_path in (startup_log, batch_plan_path, batch_result_path, screenshot, meta_path):
        try:
            stale_path.unlink(missing_ok=True)
        except OSError:
            pass

    route_plan = [
        {
            "id": panel_id,
            "name": (
                "Capture Markdown image text failure states"
                if image_text_failure
                else
                "Capture Markdown image text clickthrough"
                if image_text_success
                else
                "Capture Markdown guard failure clickthrough"
                if manual_guard_failure
                else
                "Capture Markdown downstream failure clickthrough"
                if downstream_failure
                else "Capture Markdown action clickthrough"
            ),
            "hash": CAPTURE_MARKDOWN_ACTION_HASH,
            "screenshot_path": str(screenshot),
            "meta_path": str(meta_path),
            "capture_markdown_action": payload,
            "action_script": (
                _build_capture_markdown_image_text_failure_action_script(payload)
                if image_text_failure
                else
                _build_capture_markdown_image_text_action_script(payload)
                if image_text_success
                else _build_capture_markdown_action_script(payload)
            ),
            "result_script": _capture_markdown_action_result_script(),
            "script_timeout_ms": 2000,
            "result_script_timeout_ms": 3000,
            "capture_delay_ms": action_capture_delay_ms,
            "script_wait_for_result": False,
            "script_required": True,
        }
    ]
    batch_plan_path.write_text(json.dumps({"routes": route_plan}, indent=2, default=str), encoding="utf-8")

    packaging_proof = build_studio_local_packaging_proof(vault)
    before_markdown = _markdown_snapshot(vault)
    before_approvals = _approval_artifact_snapshot(vault)
    before_source_packs = _source_pack_artifact_snapshot(vault)
    blockers: list[str] = []
    if not exe.is_file():
        blockers.append("Packaged Studio executable is missing.")
    if not (packaging_proof.get("outputs") or {}).get("executable_exists") and executable_path is None:
        blockers.append("Local packaging proof does not currently see a generated executable.")

    proc: subprocess.Popen[Any] | None = None
    launch_error: str | None = None
    launch_env = os.environ.copy()
    effective_temp_root = temp_root if temp_root is not None else DEFAULT_PACKAGED_QA_TEMP_ROOT
    runtime_env_overrides, runtime_dirs = build_runtime_env_overrides(
        vault,
        webview2_user_data_root=webview2_user_data_root,
        temp_root=effective_temp_root,
        allow_external_runtime_dirs=allow_external_runtime_dirs,
    )
    runtime_dirs["uses_default_temp_root"] = temp_root is None
    launch_env.update(runtime_env_overrides)
    if env_overrides:
        launch_env.update({str(key): str(value) for key, value in env_overrides.items()})
    delay_ms = _qa_screenshot_delay_ms(settle_seconds)
    launch_env["CHASEOS_STUDIO_STARTUP_LOG"] = str(startup_log)
    launch_env[QA_SCREENSHOT_DELAY_MS_ENV] = str(delay_ms)
    launch_env[QA_EXIT_AFTER_SCREENSHOT_ENV] = "1"
    launch_env[QA_BATCH_PLAN_PATH_ENV] = str(batch_plan_path)
    launch_env[QA_BATCH_RESULT_PATH_ENV] = str(batch_result_path)
    pyinstaller_temp_before = _snapshot_pyinstaller_temp_dirs(launch_env)
    pyinstaller_temp_cleanup = {
        "attempted": False,
        "root": pyinstaller_temp_before.get("root"),
        "deleted": [],
        "failed": [],
        "reason": "launch-not-started",
    }
    windows_process_id: int | None = None
    termination: dict[str, Any] = {"attempted": False, "terminated": False, "returncode": None}
    process_alive_after_start = False
    batch_result: dict[str, Any] = {}
    overall_timeout = max(
        90.0,
        min(360.0, (float(action_capture_delay_ms) / 1000.0) + float(window_timeout_seconds) + 45.0),
    )

    if not blockers:
        try:
            launch_vault_arg = _vault_arg_for_packaged_exe(vault)
            launch_args = [str(exe), "--vault-root", launch_vault_arg, "--initial-hash", CAPTURE_MARKDOWN_ACTION_HASH]
            proc = subprocess.Popen(
                launch_args,
                cwd=str(vault),
                env=launch_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            time.sleep(max(0.1, min(1.0, float(settle_seconds))))
            process_alive_after_start = proc.poll() is None
            if process_alive_after_start:
                windows_process_id = _resolve_windows_process_id_for_packaged_exe(
                    executable_path=exe,
                    vault_arg=launch_vault_arg,
                    fallback_process_id=proc.pid,
                )
            deadline = time.monotonic() + overall_timeout
            while time.monotonic() < deadline:
                if batch_result_path.is_file():
                    try:
                        candidate_result = json.loads(batch_result_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        candidate_result = {}
                    if candidate_result.get("done"):
                        batch_result = candidate_result
                        break
                if proc.poll() is not None:
                    break
                time.sleep(0.25)
            if not batch_result and batch_result_path.is_file():
                try:
                    batch_result = json.loads(batch_result_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    batch_result = {}
            if not batch_result.get("done"):
                blockers.append("Packaged Capture action clickthrough did not finish before timeout.")
        except OSError as exc:
            launch_error = str(exc)
            blockers.append(f"Packaged Studio executable launch failed: {exc}")
        finally:
            if proc is not None:
                termination = _terminate_packaged_process_tree(
                    proc,
                    windows_process_id=windows_process_id,
                    timeout_seconds=terminate_timeout_seconds,
                )
                pyinstaller_temp_cleanup = _cleanup_new_pyinstaller_temp_dirs(pyinstaller_temp_before, launch_env)
                termination["pyinstaller_temp_cleanup"] = pyinstaller_temp_cleanup

    stdout_tail = ""
    stderr_tail = ""
    if proc is not None and proc.poll() is not None:
        try:
            stdout, stderr = proc.communicate(timeout=1)
            stdout_tail = (stdout or "")[-4000:]
            stderr_tail = (stderr or "")[-4000:]
        except (subprocess.TimeoutExpired, ValueError):
            pass
    startup_log_tail = startup_log.read_text(encoding="utf-8", errors="replace")[-4000:] if startup_log.is_file() else ""
    host_policy = _classify_launch_error(launch_error)
    runtime_error = _classify_runtime_error("\n".join(value for value in (stderr_tail, startup_log_tail) if value))
    if runtime_error["blocked"]:
        blockers.append(str(runtime_error["message"]))

    if settings_restore is not None:
        _restore_optional_file(
            _capture_local_image_text_settings_path(vault),
            settings_restore.get("backup") or {"exists": False, "content": b""},
        )
        settings_restore["restored"] = True

    after_markdown = _markdown_snapshot(vault)
    after_approvals = _approval_artifact_snapshot(vault)
    after_source_packs = _source_pack_artifact_snapshot(vault)
    markdown_delta = _snapshot_delta(before_markdown, after_markdown)
    approval_delta = _snapshot_delta(before_approvals, after_approvals)
    source_pack_delta = _snapshot_delta(before_source_packs, after_source_packs)
    capture = _read_internal_qa_capture(meta_path, screenshot)
    action_result = _capture_action_result_from_capture(capture)
    action_assessment = (
        _assess_capture_markdown_image_text_failure_output(
            vault,
            action_result=action_result,
            markdown_delta=markdown_delta,
            approval_delta=approval_delta,
            payload=payload,
        )
        if image_text_failure
        else
        _assess_capture_markdown_image_text_output(
            vault,
            action_result=action_result,
            markdown_delta=markdown_delta,
            approval_delta=approval_delta,
            payload=payload,
        )
        if image_text_success
        else
        _assess_capture_markdown_downstream_failure_output(
            vault,
            action_result=action_result,
            markdown_delta=markdown_delta,
            approval_delta=approval_delta,
            source_pack_delta=source_pack_delta,
            payload=payload,
        )
        if downstream_failure
        else
        _assess_capture_markdown_guard_failure_output(
            vault,
            action_result=action_result,
            markdown_delta=markdown_delta,
            approval_delta=approval_delta,
            source_pack_delta=source_pack_delta,
            payload=payload,
        )
        if manual_guard_failure
        else _assess_capture_markdown_action_output(
            vault,
            action_result=action_result,
            markdown_delta=markdown_delta,
            approval_delta=approval_delta,
            source_pack_delta=source_pack_delta,
            payload=payload,
        )
    )
    blockers.extend(action_assessment.get("blockers") or [])
    source_pack_proof_report = (
        action_result.get("source_pack_proof")
        if isinstance(action_result.get("source_pack_proof"), dict)
        else {}
    )
    downstream_workflow_executed = (not image_text_mode) and bool(
        source_pack_proof_report.get("aor_full_dispatch_result_visible")
        or source_pack_proof_report.get("source_intelligence_core_ingestion_result_visible")
        or source_pack_proof_report.get("graph_indexing_result_visible")
        or source_pack_proof_report.get("canonical_promotion_result_visible")
    )
    approval_artifacts_changed = (not image_text_mode) and _snapshot_delta_changed(approval_delta)

    screenshot_exists = screenshot.is_file()
    screenshot_size = screenshot.stat().st_size if screenshot_exists else 0
    visual_verification, content_area_verification = _analyze_png_nonblank_and_content_area(
        screenshot,
        min_unique_colors=min_unique_colors,
        max_dominant_ratio=max_dominant_ratio,
    )
    if capture.get("error"):
        blockers.append(f"Native window capture failed: {capture.get('error')}.")
    elif not bool(capture.get("ok")):
        blockers.append("Native window screenshot was not captured.")
    if require_nonblank and screenshot_exists and not bool(content_area_verification.get("ok")):
        blockers.append("Native window screenshot content area is blank or near-uniform.")
    if not bool(termination.get("terminated")):
        blockers.append("owned_process_not_terminated_for_capture_action")

    ok = not blockers
    return {
        "ok": ok,
        "surface": (
            "studio_packaged_capture_markdown_image_text_failure_states"
            if image_text_failure
            else
            "studio_packaged_capture_markdown_image_text_clickthrough"
            if image_text_success
            else
            "studio_packaged_capture_markdown_guard_failure_clickthrough"
            if manual_guard_failure
            else
            "studio_packaged_capture_markdown_downstream_failure_clickthrough"
            if downstream_failure
            else "studio_packaged_capture_markdown_action_clickthrough"
        ),
        "model_version": MODEL_VERSION,
        "status": (
            "packaged_capture_markdown_image_text_failure_states_complete"
            if ok and image_text_failure
            else
            "packaged_capture_markdown_image_text_clickthrough_complete"
            if ok and image_text_success
            else "packaged_capture_markdown_guard_failure_clickthrough_complete"
            if ok and manual_guard_failure
            else "packaged_capture_markdown_downstream_failure_clickthrough_complete"
            if ok and downstream_failure
            else "packaged_capture_markdown_action_clickthrough_complete"
            if ok
            else "blocked_packaged_capture_markdown_image_text_failure_states"
            if image_text_failure
            else "blocked_packaged_capture_markdown_image_text_clickthrough"
            if image_text_success
            else "blocked_packaged_capture_markdown_guard_failure_clickthrough"
            if manual_guard_failure
            else "blocked_packaged_capture_markdown_downstream_failure_clickthrough"
            if downstream_failure
            else "blocked_packaged_capture_markdown_action_clickthrough"
        ),
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "screenshot_root": _relative_to_vault(vault, root),
        "capture_mode": capture_mode_id if image_text_mode or manual_guard_failure or downstream_failure else "manual_text",
        "payload": _redact_capture_markdown_payload_for_report(payload),
        "temporary_settings": (
            {
                "settings_path": settings_restore.get("settings_path"),
                "restored": bool(settings_restore.get("restored")),
                "local_engine_available": bool(
                    ((settings_restore.get("model") or {}).get("summary") or {}).get("local_engine_available")
                ),
            }
            if settings_restore is not None
            else None
        ),
        "batch": {
            "plan_path": _relative_to_vault(vault, batch_plan_path),
            "result_path": _relative_to_vault(vault, batch_result_path),
            "result": batch_result,
            "overall_timeout_seconds": overall_timeout,
        },
        "executable": {
            "path": _relative_to_vault(vault, exe),
            "exists": exe.is_file(),
            "sha256": _sha256(exe) if exe.is_file() else None,
        },
        "launch": {
            "started": proc is not None,
            "process_id": proc.pid if proc is not None else None,
            "windows_process_id": windows_process_id,
            "initial_hash": CAPTURE_MARKDOWN_ACTION_HASH,
            "process_alive_after_start": process_alive_after_start,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "startup_log_path": _relative_to_vault(vault, startup_log),
            "startup_log_exists": startup_log.is_file(),
            "startup_log_tail": startup_log_tail,
            "launch_error": launch_error,
            "env_override_keys": sorted(str(key) for key in (env_overrides or {}).keys()),
            "runtime_env_override_keys": sorted(runtime_env_overrides.keys()),
            "runtime_dirs": runtime_dirs,
            "qa_screenshot_delay_ms": delay_ms,
            "host_policy": host_policy,
            "runtime_error": runtime_error,
        },
        "termination": termination,
        "screenshot": {
            "path": _relative_to_vault(vault, screenshot),
            "exists": screenshot_exists,
            "size_bytes": screenshot_size,
            "capture": capture,
            "visual_verification": visual_verification,
            "content_area_verification": content_area_verification,
            "require_nonblank": bool(require_nonblank),
        },
        "action_result": action_result,
        "action_assessment": action_assessment,
        "write_sentinel": {
            "markdown": markdown_delta,
            "approval_artifacts": approval_delta,
            "source_pack_artifacts": source_pack_delta,
        },
        "checks": [
            {"name": "batch_completed", "ok": bool(batch_result.get("done")), "detail": str(batch_result.get("captured_count") or 0)},
            {"name": "window_capture_ok", "ok": bool(capture.get("ok")), "detail": capture.get("error") or "window screenshot captured"},
            {"name": "screenshot_exists", "ok": screenshot_exists, "detail": _relative_to_vault(vault, screenshot)},
            {"name": "screenshot_nonempty", "ok": screenshot_size > 1000, "detail": str(screenshot_size)},
            {"name": "screenshot_nonblank", "ok": (not require_nonblank or bool(visual_verification.get("ok"))), "detail": visual_verification.get("reason")},
            {"name": "screenshot_content_area_nonblank", "ok": (not require_nonblank or bool(content_area_verification.get("ok"))), "detail": content_area_verification.get("reason")},
            {"name": "owned_process_terminated", "ok": bool(termination.get("terminated")), "detail": "terminated only the packaged process started by the proof"},
            *list(action_assessment.get("checks") or []),
        ],
        "blockers": blockers,
        "authority": {
            "launches_packaged_executable": True,
            "captures_native_screenshots": True,
            "drives_capture_page_controls": True,
            "writes_raw_quarantine_markdown": not image_text_failure,
            "writes_source_pack_artifacts": (not image_text_mode) and bool(
                any(source_pack_delta.get(key) for key in ("added", "modified", "removed"))
            ),
            "uses_explicit_vault_local_image": bool(image_text_mode),
            "runs_local_image_text_command": bool(image_text_mode),
            "captures_live_screen": False,
            "reads_active_window": False,
            "reads_active_browser_tab": False,
            "cloud_optical_character_recognition_allowed": False,
            "terminates_owned_processes": True,
            "writes_visual_evidence": True,
            "writes_installer": False,
            "mutates_gate": False,
            "grants_approvals": bool(approval_artifacts_changed),
            "executes_approval_decisions": (not image_text_mode) and bool(
                source_pack_proof_report.get("aor_approval_consumption_result_visible")
                or source_pack_proof_report.get("source_intelligence_core_ingestion_result_visible")
                or source_pack_proof_report.get("canonical_promotion_result_visible")
            ),
            "executes_workflows": bool(downstream_workflow_executed),
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": (not image_text_mode) and bool(
                source_pack_proof_report.get("agent_bus_task_result_visible")
            ),
            "canonical_mutation_allowed": (not image_text_mode) and bool(
                source_pack_proof_report.get("canonical_promotion_result_visible")
            ),
        },
        "unverified": (
            [
                "This proof uses temporary local commands to exercise image text failure states; real Tesseract or equivalent quality remains unverified.",
                "This proof verifies no raw quarantine Markdown or approval artifacts are written for failed image text previews.",
                "This proof uses an internal packaged action hook; global operating-system hotkeys, active-browser capture, Discord capture, and external application capture remain unimplemented.",
            ]
            if image_text_failure
            else
            [
                "This proof uses a temporary local command as the image text engine; real Tesseract or equivalent quality remains unverified.",
                "This proof writes raw quarantine Markdown only; Source Intelligence Core ingestion and canonical promotion remain governed downstream.",
                "This proof uses an internal packaged action hook; global operating-system hotkeys, active-browser capture, Discord capture, and external application capture remain unimplemented.",
            ]
            if image_text_success
            else
            [
                "This proof intentionally uses a wrong source-package operator statement and verifies no source-package or approval artifacts are written.",
                "Deeper downstream failure-state clickthroughs still need the same product-facing guard card pattern.",
                "This proof uses an internal packaged action hook; global operating-system hotkeys, active-browser capture, and Discord capture remain unimplemented.",
            ]
            if manual_guard_failure
            else
            [
                "This proof intentionally uses a wrong downstream operator statement after source-package write and verifies the matching product-facing guard card.",
                "This proof does not grant new target-boundary approvals or call external providers; deeper cases may create earlier governed artifacts before the target boundary is blocked.",
                "This proof uses an internal packaged action hook; global operating-system hotkeys, active-browser capture, and Discord capture remain unimplemented.",
            ]
            if downstream_failure
            else [
                "This proof exercises manual text capture only; image text extraction is not performed.",
                "Windows local optical character recognition, display capture, browser capture, Discord command capture, and external application capture are proven by separate retained source/live proof artifacts.",
                "This proof uses an internal packaged action hook; it confirms the rebuilt executable exposes the Capture page, Settings-gated source cards, shortcut rows, raw-quarantine save, and review update.",
            ]
        ),
        "next_recommended_pass": (
            "capture-markdown-real-local-engine-quality-fixtures"
            if ok and image_text_failure
            else
            "capture-markdown-real-local-engine-quality-fixtures"
            if ok and image_text_success
            else "capture-markdown-downstream-failure-state-matrix"
            if ok and manual_guard_failure
            else "capture-markdown-real-local-engine-quality-fixtures"
            if ok and downstream_failure
            else "capture-markdown-real-image-text-and-external-collector-implementation"
            if ok
            else "capture-markdown-packaged-image-text-failure-state-remediation"
            if image_text_failure
            else "capture-markdown-packaged-image-text-clickthrough-remediation"
            if image_text_success
            else "capture-markdown-packaged-guard-failure-remediation"
            if manual_guard_failure
            else "capture-markdown-packaged-downstream-failure-remediation"
            if downstream_failure
            else "capture-markdown-packaged-action-clickthrough-remediation"
        ),
    }


def build_packaged_capture_markdown_guard_failure_clickthrough(
    vault_root: str | Path,
    **kwargs: Any,
) -> dict[str, Any]:
    """Drive packaged Capture through an intentional guarded source-package write failure."""

    return build_packaged_capture_markdown_action_clickthrough(
        vault_root,
        capture_mode="manual_text_guard_failure",
        **kwargs,
    )


def build_packaged_capture_markdown_image_text_clickthrough(
    vault_root: str | Path,
    **kwargs: Any,
) -> dict[str, Any]:
    """Drive packaged Capture through explicit screenshot image text extraction."""

    return build_packaged_capture_markdown_action_clickthrough(
        vault_root,
        capture_mode="image_text",
        **kwargs,
    )


def build_packaged_capture_markdown_image_text_failure_clickthrough(
    vault_root: str | Path,
    **kwargs: Any,
) -> dict[str, Any]:
    """Drive packaged Capture through image text failure states without saving."""

    return build_packaged_capture_markdown_action_clickthrough(
        vault_root,
        capture_mode="image_text_failure",
        **kwargs,
    )


def _normalize_downstream_failure_cases(
    downstream_failure_cases: list[object] | tuple[object, ...] | None,
) -> list[dict[str, Any]]:
    if downstream_failure_cases is None:
        return [dict(case) for case in CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_CASES]
    normalized: list[dict[str, Any]] = []
    for item in downstream_failure_cases:
        if isinstance(item, str):
            normalized.append(_capture_markdown_downstream_failure_case(item))
            continue
        if isinstance(item, dict):
            case_id = str(item.get("id") or "")
            case = _capture_markdown_downstream_failure_case(case_id)
            case.update(item)
            normalized.append(case)
            continue
        raise ValueError(f"Unsupported downstream failure case: {item!r}")
    if not normalized:
        raise ValueError("At least one downstream failure case is required.")
    return normalized


def build_packaged_capture_markdown_downstream_failure_clickthrough(
    vault_root: str | Path,
    *,
    case_id: str = "aor_approval_request_bad_statement",
    **kwargs: Any,
) -> dict[str, Any]:
    """Drive packaged Capture through one downstream guarded failure after source-package write."""

    return build_packaged_capture_markdown_action_clickthrough(
        vault_root,
        capture_mode=f"manual_text_downstream_failure:{case_id}",
        **kwargs,
    )


def build_packaged_capture_markdown_downstream_failure_state_matrix(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    screenshot_root: str | Path | None = None,
    env_overrides: dict[str, str] | None = None,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    allow_external_runtime_dirs: bool = False,
    settle_seconds: float = 10.0,
    window_timeout_seconds: float = 20.0,
    terminate_timeout_seconds: float = 5.0,
    require_nonblank: bool = True,
    min_unique_colors: int = DEFAULT_MIN_UNIQUE_COLORS,
    max_dominant_ratio: float = DEFAULT_MAX_DOMINANT_RATIO,
    run_token: str | None = None,
    downstream_failure_cases: list[object] | tuple[object, ...] | None = None,
) -> dict[str, Any]:
    """Run packaged Capture guarded downstream failure proof across the release-hardening matrix."""

    vault = _vault_path(vault_root)
    cases = _normalize_downstream_failure_cases(downstream_failure_cases)
    slug = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-capture-markdown-downstream-failure-state-matrix"
    root = _resolve_screenshot_root(vault, screenshot_root, slug)
    token_base = run_token or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    case_reports: list[dict[str, Any]] = []

    for case in cases:
        case_id = str(case["id"])
        report = build_packaged_capture_markdown_downstream_failure_clickthrough(
            vault,
            case_id=case_id,
            executable_path=executable_path,
            screenshot_root=root / case_id,
            env_overrides=env_overrides,
            webview2_user_data_root=webview2_user_data_root,
            temp_root=temp_root,
            allow_external_runtime_dirs=allow_external_runtime_dirs,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
            require_nonblank=require_nonblank,
            min_unique_colors=min_unique_colors,
            max_dominant_ratio=max_dominant_ratio,
            run_token=f"{token_base}-{case_id}",
        )
        screenshot = report.get("screenshot") if isinstance(report.get("screenshot"), dict) else {}
        action_assessment = (
            report.get("action_assessment")
            if isinstance(report.get("action_assessment"), dict)
            else {}
        )
        checks = {
            str(item.get("name")): bool(item.get("ok"))
            for item in action_assessment.get("checks") or []
            if isinstance(item, dict)
        }
        case_reports.append(
            {
                "id": case_id,
                "label": case.get("label") or case_id,
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "screenshot_path": screenshot.get("path"),
                "guard_card_visible": checks.get("downstream_failure_guard_card_visible", False),
                "expected_boundary_reached": checks.get("downstream_failure_reached_expected_boundary", False),
                "forbidden_artifacts_not_written": checks.get(
                    "downstream_failure_forbidden_artifacts_not_written",
                    False,
                ),
                "blockers": report.get("blockers") or [],
                "report": report,
            }
        )

    all_cases_ok = all(bool(case.get("ok")) for case in case_reports)
    guard_cards_visible = all(bool(case.get("guard_card_visible")) for case in case_reports)
    expected_boundaries_reached = all(bool(case.get("expected_boundary_reached")) for case in case_reports)
    forbidden_artifacts_not_written = all(bool(case.get("forbidden_artifacts_not_written")) for case in case_reports)
    blockers: list[str] = []
    for case in case_reports:
        for blocker in case.get("blockers") or []:
            blockers.append(f"{case.get('id')}: {blocker}")
    if not guard_cards_visible:
        blockers.append("One or more downstream failure cases did not show a product-facing guard card.")
    if not expected_boundaries_reached:
        blockers.append("One or more downstream failure cases did not reach the intended post-source-package boundary.")
    if not forbidden_artifacts_not_written:
        blockers.append("One or more downstream failure cases wrote forbidden target-boundary artifacts.")

    ok = all_cases_ok and guard_cards_visible and expected_boundaries_reached and forbidden_artifacts_not_written and not blockers
    return {
        "ok": ok,
        "surface": "studio_packaged_capture_markdown_downstream_failure_state_matrix",
        "model_version": MODEL_VERSION,
        "status": (
            "packaged_capture_markdown_downstream_failure_state_matrix_complete"
            if ok
            else "blocked_packaged_capture_markdown_downstream_failure_state_matrix"
        ),
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "screenshot_root": _relative_to_vault(vault, root),
        "case_count": len(case_reports),
        "cases": case_reports,
        "checks": [
            {"name": "downstream_failure_cases_present", "ok": len(case_reports) >= 3, "detail": str(len(case_reports))},
            {
                "name": "downstream_failure_cases_passed",
                "ok": all_cases_ok,
                "detail": str(sum(1 for item in case_reports if item.get("ok"))),
            },
            {
                "name": "downstream_failure_guard_cards_visible",
                "ok": guard_cards_visible,
                "detail": ", ".join(str(case.get("id")) for case in case_reports if not case.get("guard_card_visible"))
                or "all cases",
            },
            {
                "name": "downstream_failure_expected_boundaries_reached",
                "ok": expected_boundaries_reached,
                "detail": ", ".join(str(case.get("id")) for case in case_reports if not case.get("expected_boundary_reached"))
                or "all cases",
            },
            {
                "name": "downstream_failure_forbidden_artifacts_not_written",
                "ok": forbidden_artifacts_not_written,
                "detail": ", ".join(str(case.get("id")) for case in case_reports if not case.get("forbidden_artifacts_not_written"))
                or "all cases",
            },
        ],
        "blockers": blockers,
        "authority": {
            "launches_packaged_executable": True,
            "drives_capture_page_controls": True,
            "captures_native_screenshots": True,
            "writes_raw_quarantine_markdown": True,
            "writes_source_pack_artifacts": True,
            "uses_internal_packaged_action_hook": True,
            "captures_live_screen": False,
            "reads_active_browser_tab": False,
            "cloud_optical_character_recognition_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_visual_evidence": True,
        },
        "unverified": [
            "This matrix proves guarded downstream failure cards through packaged controls; it does not prove live global shortcuts, active browser capture, or Discord capture.",
            "This matrix uses temporary proof captures and earlier governed artifacts before each target boundary; those proof artifacts should be cleaned after evidence is written.",
            "Real local image text engine quality remains a separate open proof item.",
        ],
        "next_recommended_pass": (
            "capture-markdown-real-local-engine-quality-fixtures"
            if ok
            else "capture-markdown-packaged-downstream-failure-remediation"
        ),
    }


def build_packaged_capture_markdown_window_size_matrix(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    screenshot_root: str | Path | None = None,
    env_overrides: dict[str, str] | None = None,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    allow_external_runtime_dirs: bool = False,
    settle_seconds: float = 10.0,
    window_timeout_seconds: float = 20.0,
    terminate_timeout_seconds: float = 5.0,
    require_nonblank: bool = True,
    min_unique_colors: int = DEFAULT_MIN_UNIQUE_COLORS,
    max_dominant_ratio: float = DEFAULT_MAX_DOMINANT_RATIO,
    run_token: str | None = None,
    capture_mode: str = "manual_text_guard_failure",
    window_size_cases: list[object] | tuple[object, ...] | None = None,
) -> dict[str, Any]:
    """Run packaged Capture proof at multiple proof-controlled window sizes."""

    vault = _vault_path(vault_root)
    cases = _normalize_window_size_cases(window_size_cases)
    slug = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-capture-markdown-window-size-matrix"
    root = _resolve_screenshot_root(vault, screenshot_root, slug)
    token_base = run_token or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    case_reports: list[dict[str, Any]] = []

    for case in cases:
        case_id = str(case["id"])
        case_width = int(case["width"])
        case_height = int(case["height"])
        case_env = {str(key): str(value) for key, value in (env_overrides or {}).items()}
        case_env[QA_WINDOW_WIDTH_ENV] = str(case_width)
        case_env[QA_WINDOW_HEIGHT_ENV] = str(case_height)
        report = build_packaged_capture_markdown_action_clickthrough(
            vault,
            executable_path=executable_path,
            screenshot_root=root / case_id,
            env_overrides=case_env,
            webview2_user_data_root=webview2_user_data_root,
            temp_root=temp_root,
            allow_external_runtime_dirs=allow_external_runtime_dirs,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
            require_nonblank=require_nonblank,
            min_unique_colors=min_unique_colors,
            max_dominant_ratio=max_dominant_ratio,
            run_token=f"{token_base}-{case_id}",
            capture_mode=capture_mode,
        )
        capture = ((report.get("screenshot") or {}).get("capture") or {})
        screenshot = report.get("screenshot") or {}
        case_reports.append(
            {
                "id": case_id,
                "requested": {"width": case_width, "height": case_height},
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "screenshot_path": screenshot.get("path"),
                "captured": {
                    "width": int(capture.get("width") or 0),
                    "height": int(capture.get("height") or 0),
                    "method": capture.get("capture_method") or capture.get("method") or "",
                    "size_bytes": screenshot.get("size_bytes") or 0,
                },
                "blockers": report.get("blockers") or [],
                "report": report,
            }
        )

    size_increases = [
        int((right.get("captured") or {}).get("width") or 0)
        > int((left.get("captured") or {}).get("width") or 0)
        and int((right.get("captured") or {}).get("height") or 0)
        > int((left.get("captured") or {}).get("height") or 0)
        for left, right in zip(case_reports, case_reports[1:])
    ]
    all_cases_ok = all(bool(case.get("ok")) for case in case_reports)
    captured_dimensions_present = all(
        int((case.get("captured") or {}).get("width") or 0) > 0
        and int((case.get("captured") or {}).get("height") or 0) > 0
        for case in case_reports
    )
    requested_sizes_applied = captured_dimensions_present and (all(size_increases) if len(case_reports) > 1 else True)
    blockers: list[str] = []
    for case in case_reports:
        for blocker in case.get("blockers") or []:
            blockers.append(f"{case.get('id')}: {blocker}")
    if not requested_sizes_applied:
        blockers.append("Packaged Capture screenshots did not show increasing dimensions across requested window sizes.")

    ok = all_cases_ok and requested_sizes_applied and not blockers
    return {
        "ok": ok,
        "surface": "studio_packaged_capture_markdown_window_size_matrix",
        "model_version": MODEL_VERSION,
        "status": (
            "packaged_capture_markdown_window_size_matrix_complete"
            if ok
            else "blocked_packaged_capture_markdown_window_size_matrix"
        ),
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "screenshot_root": _relative_to_vault(vault, root),
        "capture_mode": str(capture_mode or "manual_text_guard_failure"),
        "case_count": len(case_reports),
        "cases": case_reports,
        "checks": [
            {"name": "window_size_cases_present", "ok": len(case_reports) >= 2, "detail": str(len(case_reports))},
            {
                "name": "window_size_cases_passed",
                "ok": all_cases_ok,
                "detail": str(sum(1 for item in case_reports if item.get("ok"))),
            },
            {
                "name": "window_size_captures_have_dimensions",
                "ok": captured_dimensions_present,
                "detail": ", ".join(
                    f"{case.get('id')}={((case.get('captured') or {}).get('width'))}x{((case.get('captured') or {}).get('height'))}"
                    for case in case_reports
                ),
            },
            {
                "name": "window_size_requests_affect_capture_dimensions",
                "ok": requested_sizes_applied,
                "detail": "larger requested sizes produced larger captured dimensions",
            },
        ],
        "blockers": blockers,
        "authority": {
            "launches_packaged_executable": True,
            "drives_capture_page_controls": True,
            "captures_native_screenshots": True,
            "uses_proof_only_window_size_environment": True,
            "writes_raw_quarantine_markdown": str(capture_mode or "") != "image_text_failure",
            "terminates_owned_processes": True,
            "writes_visual_evidence": True,
            "writes_installer": False,
            "reads_active_browser_tab": False,
            "reads_discord_tokens_or_events": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "unverified": [
            "This matrix proves packaged Capture at controlled desktop window sizes only; phone-sized mobile windows remain below the Studio minimum size.",
            "Live personal-instance collector clicks remain separate operator-enabled proofs.",
            "Real local image text engine quality remains separate from this window-size proof.",
        ],
        "next_recommended_pass": (
            "capture-markdown-live-personal-collector-click-proof"
            if ok
            else "capture-markdown-window-size-matrix-remediation"
        ),
    }


def _build_packaged_app_all_pages_visual_qa_batch(
    vault: Path,
    *,
    panels: list[dict[str, Any]],
    executable_path: str | Path | None,
    root: Path,
    env_overrides: dict[str, str] | None,
    webview2_user_data_root: str | Path | None,
    temp_root: str | Path | None,
    allow_external_runtime_dirs: bool,
    settle_seconds: float,
    window_timeout_seconds: float,
    terminate_timeout_seconds: float,
    require_nonblank: bool,
    min_unique_colors: int,
    max_dominant_ratio: float,
    markdown_sentinel_ignore_paths: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    exe = _resolve_executable(vault, executable_path or DEFAULT_EXE)
    startup_log = root / "batch.startup.log"
    batch_plan_path = root / "batch-plan.json"
    batch_result_path = root / "batch-result.json"
    for stale_path in (startup_log, batch_plan_path, batch_result_path):
        try:
            stale_path.unlink(missing_ok=True)
        except OSError:
            pass

    route_plan = []
    for panel in panels:
        panel_id = str(panel.get("id") or "panel")
        screenshot = root / f"{panel_id}.png"
        meta = root / f"{panel_id}.qa-meta.json"
        for stale_path in (screenshot, meta):
            try:
                stale_path.unlink(missing_ok=True)
            except OSError:
                pass
        route_entry = {
            "id": panel_id,
            "name": panel.get("name"),
            "hash": panel.get("hash"),
            "screenshot_path": str(screenshot),
            "meta_path": str(meta),
        }
        for optional_key in (
            "script",
            "action_script",
            "script_timeout_ms",
            "script_wait_for_result",
            "script_fire_and_forget",
            "script_required",
            "result_script",
            "script_result_script",
            "result_script_timeout_ms",
            "capture_delay_ms",
            "capture_markdown_action",
        ):
            if optional_key in panel:
                route_entry[optional_key] = panel[optional_key]
        route_plan.append(route_entry)
    batch_plan_path.write_text(json.dumps({"routes": route_plan}, indent=2, default=str), encoding="utf-8")

    packaging_proof = build_studio_local_packaging_proof(vault)
    before_markdown = _markdown_snapshot(vault)
    before_approvals = _approval_artifact_snapshot(vault)
    blockers: list[str] = []
    if not exe.is_file():
        blockers.append("Packaged Studio executable is missing.")
    if not (packaging_proof.get("outputs") or {}).get("executable_exists") and executable_path is None:
        blockers.append("Local packaging proof does not currently see a generated executable.")

    proc: subprocess.Popen[Any] | None = None
    launch_error: str | None = None
    launch_env = os.environ.copy()
    effective_temp_root = temp_root if temp_root is not None else DEFAULT_PACKAGED_QA_TEMP_ROOT
    runtime_env_overrides, runtime_dirs = build_runtime_env_overrides(
        vault,
        webview2_user_data_root=webview2_user_data_root,
        temp_root=effective_temp_root,
        allow_external_runtime_dirs=allow_external_runtime_dirs,
    )
    runtime_dirs["uses_default_temp_root"] = temp_root is None
    launch_env.update(runtime_env_overrides)
    if env_overrides:
        launch_env.update({str(key): str(value) for key, value in env_overrides.items()})
    delay_ms = _qa_screenshot_delay_ms(settle_seconds)
    launch_env["CHASEOS_STUDIO_STARTUP_LOG"] = str(startup_log)
    launch_env[QA_SCREENSHOT_DELAY_MS_ENV] = str(delay_ms)
    launch_env[QA_EXIT_AFTER_SCREENSHOT_ENV] = "1"
    launch_env[QA_BATCH_PLAN_PATH_ENV] = str(batch_plan_path)
    launch_env[QA_BATCH_RESULT_PATH_ENV] = str(batch_result_path)
    pyinstaller_temp_before = _snapshot_pyinstaller_temp_dirs(launch_env)
    pyinstaller_temp_cleanup = {
        "attempted": False,
        "root": pyinstaller_temp_before.get("root"),
        "deleted": [],
        "failed": [],
        "reason": "launch-not-started",
    }
    windows_process_id: int | None = None
    termination: dict[str, Any] = {"attempted": False, "terminated": False, "returncode": None}
    process_alive_after_start = False
    batch_result: dict[str, Any] = {}
    child_process_snapshots: list[dict[str, Any]] = []
    overall_timeout = max(90.0, min(600.0, len(panels) * max(2.0, float(settle_seconds)) + 45.0))

    if not blockers:
        try:
            launch_vault_arg = _vault_arg_for_packaged_exe(vault)
            first_hash = str(panels[0].get("hash") or "") if panels else ""
            launch_args = [str(exe), "--vault-root", launch_vault_arg]
            if first_hash:
                launch_args.extend(["--initial-hash", first_hash])
            proc = subprocess.Popen(
                launch_args,
                cwd=str(vault),
                env=launch_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            time.sleep(max(0.1, min(1.0, float(settle_seconds))))
            process_alive_after_start = proc.poll() is None
            if process_alive_after_start:
                windows_process_id = _resolve_windows_process_id_for_packaged_exe(
                    executable_path=exe,
                    vault_arg=launch_vault_arg,
                    fallback_process_id=proc.pid,
                )
                child_process_snapshots.append(
                    _windows_process_descendants(windows_process_id, label="after-launch")
                )
            deadline = time.monotonic() + overall_timeout
            last_child_process_scan = time.monotonic()
            child_process_scan_interval = max(3.0, min(12.0, float(settle_seconds)))
            while time.monotonic() < deadline:
                if batch_result_path.is_file():
                    try:
                        candidate_result = json.loads(batch_result_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        candidate_result = {}
                    if candidate_result.get("done"):
                        batch_result = candidate_result
                        break
                if proc.poll() is not None:
                    break
                if (
                    windows_process_id
                    and time.monotonic() - last_child_process_scan >= child_process_scan_interval
                ):
                    child_process_snapshots.append(
                        _windows_process_descendants(
                            windows_process_id,
                            label=f"batch-open-scan-{len(child_process_snapshots) + 1}",
                        )
                    )
                    last_child_process_scan = time.monotonic()
                time.sleep(0.25)
            if not batch_result and batch_result_path.is_file():
                try:
                    batch_result = json.loads(batch_result_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    batch_result = {}
            if not batch_result.get("done"):
                blockers.append("Packaged Studio batch screenshot capture did not finish before timeout.")
            if windows_process_id and proc.poll() is None:
                child_process_snapshots.append(
                    _windows_process_descendants(windows_process_id, label="after-batch")
                )
        except OSError as exc:
            launch_error = str(exc)
            blockers.append(f"Packaged Studio executable launch failed: {exc}")
        finally:
            if proc is not None:
                termination = _terminate_packaged_process_tree(
                    proc,
                    windows_process_id=windows_process_id,
                    timeout_seconds=terminate_timeout_seconds,
                )
                pyinstaller_temp_cleanup = _cleanup_new_pyinstaller_temp_dirs(pyinstaller_temp_before, launch_env)
                termination["pyinstaller_temp_cleanup"] = pyinstaller_temp_cleanup

    stdout_tail = ""
    stderr_tail = ""
    if proc is not None and proc.poll() is not None:
        try:
            stdout, stderr = proc.communicate(timeout=1)
            stdout_tail = (stdout or "")[-4000:]
            stderr_tail = (stderr or "")[-4000:]
        except (subprocess.TimeoutExpired, ValueError):
            pass
    startup_log_tail = startup_log.read_text(encoding="utf-8", errors="replace")[-4000:] if startup_log.is_file() else ""
    host_policy = _classify_launch_error(launch_error)
    runtime_error = _classify_runtime_error("\n".join(value for value in (stderr_tail, startup_log_tail) if value))
    if runtime_error["blocked"]:
        blockers.append(str(runtime_error["message"]))

    after_markdown = _markdown_snapshot(vault)
    after_approvals = _approval_artifact_snapshot(vault)
    ignored_markdown_paths = _normalize_markdown_sentinel_ignore_paths(markdown_sentinel_ignore_paths)
    raw_markdown_delta = _snapshot_delta(before_markdown, after_markdown)
    ignored_markdown_delta = _ignored_delta_paths(raw_markdown_delta, ignored_markdown_paths)
    markdown_delta = _filter_delta_paths(raw_markdown_delta, ignored_markdown_paths)
    approval_delta = _snapshot_delta(before_approvals, after_approvals)
    if _snapshot_delta_changed(markdown_delta):
        blockers.append("Markdown write sentinel changed during packaged visual QA.")
    if _snapshot_delta_changed(approval_delta):
        blockers.append("Approval artifact write sentinel changed during packaged visual QA.")
    child_process_safety = _assess_forbidden_child_processes(
        child_process_snapshots,
        PASSIVE_OPEN_FORBIDDEN_CHILD_PROCESS_NAMES,
        require_scan=bool(windows_process_id),
    )
    if not bool(child_process_safety.get("ok")):
        if child_process_safety.get("matches"):
            names = ", ".join(
                str(match.get("name") or match.get("executable_path"))
                for match in child_process_safety.get("matches") or []
            )
            blockers.append(f"Passive Studio all-pages open spawned forbidden child process(es): {names}.")
        else:
            blockers.append("Passive Studio all-pages child-process scan did not complete.")

    page_reports: list[dict[str, Any]] = []
    for panel in panels:
        panel_id = str(panel.get("id") or "panel")
        screenshot = root / f"{panel_id}.png"
        meta_path = root / f"{panel_id}.qa-meta.json"
        capture = _read_internal_qa_capture(meta_path, screenshot)
        page_reports.append(
            _build_all_pages_page_report(
                vault=vault,
                panel=panel,
                screenshot=screenshot,
                capture=capture,
                termination=termination,
                require_nonblank=require_nonblank,
                min_unique_colors=min_unique_colors,
                max_dominant_ratio=max_dominant_ratio,
                global_markdown_delta=markdown_delta,
                global_approval_delta=approval_delta,
            )
        )

    failed_pages = [page for page in page_reports if not page.get("ok")]
    if failed_pages:
        blockers.append("one_or_more_packaged_pages_failed_visual_qa")
    if len(page_reports) != len(panels):
        blockers.append("page_count_mismatch")
    if any(not ((page.get("screenshot") or {}).get("exists")) for page in page_reports):
        blockers.append("missing_page_screenshot")
    if not bool(termination.get("terminated")):
        blockers.append("owned_process_not_terminated_for_batch")
    screenshot_hashes = _screenshot_hash_summary(vault, page_reports)
    if not bool(screenshot_hashes.get("ok")):
        blockers.append("route_screenshot_uniqueness_missing")

    ok = not blockers
    return {
        "ok": ok,
        "surface": f"{SURFACE_ID}_all_pages",
        "model_version": MODEL_VERSION,
        "status": "packaged_app_all_pages_visual_qa_complete" if ok else "blocked_packaged_app_all_pages_visual_qa",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "screenshot_root": _relative_to_vault(vault, root),
        "page_count": len(page_reports),
        "expected_page_count": len(panels),
        "failed_page_count": len(failed_pages),
        "capture_mode": "single_native_launch_batch",
        "batch": {
            "plan_path": _relative_to_vault(vault, batch_plan_path),
            "result_path": _relative_to_vault(vault, batch_result_path),
            "result": batch_result,
            "overall_timeout_seconds": overall_timeout,
        },
        "executable": {
            "path": _relative_to_vault(vault, exe),
            "exists": exe.is_file(),
            "sha256": _sha256(exe) if exe.is_file() else None,
        },
        "launch": {
            "started": proc is not None,
            "process_id": proc.pid if proc is not None else None,
            "windows_process_id": windows_process_id,
            "initial_hash": str(panels[0].get("hash") or "") if panels else None,
            "process_alive_after_start": process_alive_after_start,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "startup_log_path": _relative_to_vault(vault, startup_log),
            "startup_log_exists": startup_log.is_file(),
            "startup_log_tail": startup_log_tail,
            "launch_error": launch_error,
            "env_override_keys": sorted(str(key) for key in (env_overrides or {}).keys()),
            "runtime_env_override_keys": sorted(runtime_env_overrides.keys()),
            "runtime_dirs": runtime_dirs,
            "qa_screenshot_delay_ms": delay_ms,
            "host_policy": host_policy,
            "runtime_error": runtime_error,
        },
        "termination": termination,
        "process_safety": child_process_safety,
        "screenshot_hashes": screenshot_hashes,
        "write_sentinel": {
            "markdown": markdown_delta,
            "ignored_markdown": ignored_markdown_delta,
            "ignored_markdown_paths": sorted(ignored_markdown_paths),
            "approval_artifacts": approval_delta,
        },
        "pages": page_reports,
        "checks": [
            {"name": "all_mounted_pages_attempted", "ok": len(page_reports) == len(panels), "detail": f"{len(page_reports)} / {len(panels)}"},
            {"name": "all_page_visual_qa_passed", "ok": not failed_pages, "detail": f"{len(failed_pages)} failed"},
            {"name": "all_page_screenshots_exist", "ok": not any(not ((page.get("screenshot") or {}).get("exists")) for page in page_reports), "detail": _relative_to_vault(vault, root)},
            {"name": "owned_processes_terminated", "ok": bool(termination.get("terminated")), "detail": "terminated only processes started by visual QA"},
            {"name": "no_forbidden_child_processes", "ok": bool(child_process_safety.get("ok")), "detail": child_process_safety.get("reason")},
            {"name": "route_screenshots_unique", "ok": bool(screenshot_hashes.get("ok")), "detail": f"{screenshot_hashes.get('unique_hash_count')} unique / {screenshot_hashes.get('page_count')} pages"},
            {"name": "no_markdown_writes", "ok": not _snapshot_delta_changed(markdown_delta), "detail": _snapshot_delta_detail(markdown_delta)},
            {"name": "no_approval_artifact_writes", "ok": not _snapshot_delta_changed(approval_delta), "detail": _snapshot_delta_detail(approval_delta)},
        ],
        "blockers": blockers,
        "failed_pages": [
            {
                "panel_id": page.get("panel_id"),
                "status": page.get("status"),
                "blockers": page.get("blockers"),
                "next_recommended_pass": page.get("next_recommended_pass"),
            }
            for page in failed_pages
        ],
        "authority": {
            "launches_packaged_executable": True,
            "captures_native_screenshots": True,
            "terminates_owned_processes": True,
            "runs_hidden_diagnostic_powershell": True,
            "writes_visual_evidence": True,
            "writes_installer": False,
            "writes_host_startup": False,
            "mutates_gate": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "executes_workflows": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "unverified": [
            "Installer creation/signing was not attempted.",
            "Startup/autostart integration was not attempted.",
            "Native screenshots use shell-level Qt widget capture, route sentinels, and pixel diversity; optical character recognition is not performed.",
            "The child-process guard uses hidden host diagnostics to inspect Studio-owned descendants; very short-lived child processes between scan intervals remain residual host-level risk.",
        ],
        "next_recommended_pass": "studio-installer-plan-and-governance" if ok else "studio-packaged-all-pages-visual-qa-remediation",
    }


def build_packaged_app_all_pages_visual_qa(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    screenshot_root: str | Path | None = None,
    env_overrides: dict[str, str] | None = None,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    allow_external_runtime_dirs: bool = False,
    settle_seconds: float = 10.0,
    window_timeout_seconds: float = 15.0,
    terminate_timeout_seconds: float = 5.0,
    require_nonblank: bool = True,
    min_unique_colors: int = DEFAULT_MIN_UNIQUE_COLORS,
    max_dominant_ratio: float = DEFAULT_MAX_DOMINANT_RATIO,
    batch_launch: bool = False,
    markdown_sentinel_retry_count: int = 3,
    markdown_sentinel_ignore_paths: list[str] | tuple[str, ...] | None = None,
    visual_readiness_retry_count: int = 2,
    visual_readiness_retry_settle_seconds: float = 45.0,
    panel_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Capture route-specific native screenshot evidence for every mounted product page."""

    from runtime.studio.final_productization_visual_qa import PANELS

    vault = _vault_path(vault_root)
    slug = datetime.now(timezone.utc).strftime("%Y-%m-%d-studio-packaged-app-all-pages-visual-qa")
    root = _resolve_screenshot_root(vault, screenshot_root, slug)
    panels = _filter_panels_by_id(list(PANELS), panel_ids)
    page_reports: list[dict[str, Any]] = []

    if batch_launch:
        return _build_packaged_app_all_pages_visual_qa_batch(
            vault,
            panels=panels,
            executable_path=executable_path,
            root=root,
            env_overrides=env_overrides,
            webview2_user_data_root=webview2_user_data_root,
            temp_root=temp_root,
            allow_external_runtime_dirs=allow_external_runtime_dirs,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
            require_nonblank=require_nonblank,
            min_unique_colors=min_unique_colors,
            max_dominant_ratio=max_dominant_ratio,
            markdown_sentinel_ignore_paths=markdown_sentinel_ignore_paths,
        )

    for panel in panels:
        panel_id = str(panel.get("id") or "panel")
        screenshot_path = root / f"{panel_id}.png"
        panel_webview2_user_data_root = _runtime_child_dir(
            webview2_user_data_root,
            panel_id=panel_id,
        )
        panel_temp_root = _temp_child_dir(
            temp_root,
            panel_id=panel_id,
        )
        page_report = build_packaged_app_visual_qa(
            vault,
            executable_path=executable_path,
            screenshot_path=screenshot_path,
            initial_hash=str(panel.get("hash") or ""),
            required_content_groups=_content_groups_for_panel(panel),
            env_overrides=env_overrides,
            webview2_user_data_root=panel_webview2_user_data_root,
            temp_root=panel_temp_root,
            allow_external_runtime_dirs=allow_external_runtime_dirs,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
            require_nonblank=require_nonblank,
            min_unique_colors=min_unique_colors,
            max_dominant_ratio=max_dominant_ratio,
            markdown_sentinel_ignore_paths=markdown_sentinel_ignore_paths,
        )
        retry: dict[str, Any] | None = None
        markdown_retry_count = max(0, int(markdown_sentinel_retry_count))
        visual_retry_count = max(0, int(visual_readiness_retry_count))
        visual_retry_settle_seconds = max(float(settle_seconds), float(visual_readiness_retry_settle_seconds))
        retry_index = 0
        markdown_retry_index = 0
        visual_retry_index = 0
        retry_attempts: list[dict[str, Any]] = []
        while not bool(page_report.get("ok")):
            markdown_retry = _single_page_failed_only_markdown_sentinel(page_report)
            visual_retry = _single_page_failed_only_visual_readiness(page_report)
            if markdown_retry and markdown_retry_index < markdown_retry_count:
                markdown_retry_index += 1
                retry_reason = "markdown_sentinel_only_failure"
                retry_settle_seconds = float(settle_seconds)
            elif visual_retry and visual_retry_index < visual_retry_count:
                visual_retry_index += 1
                retry_reason = "visual_readiness_failure"
                retry_settle_seconds = visual_retry_settle_seconds
            else:
                break
            retry_index += 1
            previous_detail = _snapshot_delta_detail(
                (page_report.get("write_sentinel") or {}).get("markdown") or {}
            )
            previous_blockers = list(page_report.get("blockers") or [])
            retry_screenshot_path = root / f"{panel_id}-retry{retry_index}.png"
            retry_webview2_user_data_root = _runtime_child_dir(
                webview2_user_data_root,
                panel_id=panel_id,
                retry_index=retry_index,
            )
            retry_temp_root = _temp_child_dir(
                temp_root,
                panel_id=panel_id,
                retry_index=retry_index,
            )
            page_report = build_packaged_app_visual_qa(
                vault,
                executable_path=executable_path,
                screenshot_path=retry_screenshot_path,
                initial_hash=str(panel.get("hash") or ""),
                required_content_groups=_content_groups_for_panel(panel),
                env_overrides=env_overrides,
                webview2_user_data_root=retry_webview2_user_data_root,
                temp_root=retry_temp_root,
                allow_external_runtime_dirs=allow_external_runtime_dirs,
                settle_seconds=retry_settle_seconds,
                window_timeout_seconds=window_timeout_seconds,
                terminate_timeout_seconds=terminate_timeout_seconds,
                require_nonblank=require_nonblank,
                min_unique_colors=min_unique_colors,
                max_dominant_ratio=max_dominant_ratio,
                markdown_sentinel_ignore_paths=markdown_sentinel_ignore_paths,
            )
            retry_attempts.append(
                {
                    "index": retry_index,
                    "reason": retry_reason,
                    "settle_seconds": retry_settle_seconds,
                    "previous_markdown_delta": previous_detail,
                    "previous_blockers": previous_blockers,
                    "ok": bool(page_report.get("ok")),
                }
            )
            retry = {
                "attempted": True,
                "count": retry_index,
                "reason": retry_reason,
                "previous_markdown_delta": previous_detail,
                "previous_blockers": previous_blockers,
                "final_ok": bool(page_report.get("ok")),
                "attempts": retry_attempts,
            }
        page_reports.append(
            _pack_all_pages_single_page_report(
                panel=panel,
                page_report=page_report,
                retry=retry,
            )
        )

    blockers: list[str] = []
    failed_pages = [page for page in page_reports if not page.get("ok")]
    if failed_pages:
        blockers.append("one_or_more_packaged_pages_failed_visual_qa")
    if len(page_reports) != len(panels):
        blockers.append("page_count_mismatch")
    if any(not ((page.get("screenshot") or {}).get("exists")) for page in page_reports):
        blockers.append("missing_page_screenshot")
    if any(not ((page.get("termination") or {}).get("terminated")) for page in page_reports):
        blockers.append("owned_process_not_terminated_for_all_pages")
    screenshot_hashes = _screenshot_hash_summary(vault, page_reports)
    if not bool(screenshot_hashes.get("ok")):
        blockers.append("route_screenshot_uniqueness_missing")

    ok = not blockers
    return {
        "ok": ok,
        "surface": f"{SURFACE_ID}_all_pages",
        "model_version": MODEL_VERSION,
        "status": "packaged_app_all_pages_visual_qa_complete" if ok else "blocked_packaged_app_all_pages_visual_qa",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "screenshot_root": _relative_to_vault(vault, root),
        "page_count": len(page_reports),
        "expected_page_count": len(panels),
        "panel_filter": [str(value) for value in (panel_ids or [])],
        "failed_page_count": len(failed_pages),
        "markdown_sentinel_retry_count": max(0, int(markdown_sentinel_retry_count)),
        "visual_readiness_retry_count": max(0, int(visual_readiness_retry_count)),
        "visual_readiness_retry_settle_seconds": float(visual_readiness_retry_settle_seconds),
        "retried_page_count": sum(1 for page in page_reports if (page.get("retry") or {}).get("attempted")),
        "markdown_sentinel_retried_page_count": sum(
            1
            for page in page_reports
            if any(
                str(attempt.get("reason")) == "markdown_sentinel_only_failure"
                for attempt in ((page.get("retry") or {}).get("attempts") or [])
            )
        ),
        "visual_readiness_retried_page_count": sum(
            1
            for page in page_reports
            if any(
                str(attempt.get("reason")) == "visual_readiness_failure"
                for attempt in ((page.get("retry") or {}).get("attempts") or [])
            )
        ),
        "screenshot_hashes": screenshot_hashes,
        "pages": page_reports,
        "checks": [
            {"name": "all_mounted_pages_attempted", "ok": len(page_reports) == len(panels), "detail": f"{len(page_reports)} / {len(panels)}"},
            {"name": "all_page_visual_qa_passed", "ok": not failed_pages, "detail": f"{len(failed_pages)} failed"},
            {"name": "all_page_screenshots_exist", "ok": not any(not ((page.get("screenshot") or {}).get("exists")) for page in page_reports), "detail": _relative_to_vault(vault, root)},
            {"name": "owned_processes_terminated", "ok": not any(not ((page.get("termination") or {}).get("terminated")) for page in page_reports), "detail": "terminated only processes started by visual QA"},
            {"name": "route_screenshots_unique", "ok": bool(screenshot_hashes.get("ok")), "detail": f"{screenshot_hashes.get('unique_hash_count')} unique / {screenshot_hashes.get('page_count')} pages"},
            {
                "name": "markdown_sentinel_retries_bounded",
                "ok": all(
                    sum(
                        1
                        for attempt in ((page.get("retry") or {}).get("attempts") or [])
                        if str(attempt.get("reason")) == "markdown_sentinel_only_failure"
                    )
                    <= max(0, int(markdown_sentinel_retry_count))
                    for page in page_reports
                ),
                "detail": f"{sum(1 for page in page_reports if any(str(attempt.get('reason')) == 'markdown_sentinel_only_failure' for attempt in ((page.get('retry') or {}).get('attempts') or [])))} retried",
            },
            {
                "name": "visual_readiness_retries_bounded",
                "ok": all(
                    sum(
                        1
                        for attempt in ((page.get("retry") or {}).get("attempts") or [])
                        if str(attempt.get("reason")) == "visual_readiness_failure"
                    )
                    <= max(0, int(visual_readiness_retry_count))
                    for page in page_reports
                ),
                "detail": f"{sum(1 for page in page_reports if any(str(attempt.get('reason')) == 'visual_readiness_failure' for attempt in ((page.get('retry') or {}).get('attempts') or [])))} retried",
            },
        ],
        "blockers": blockers,
        "failed_pages": [
            {
                "panel_id": page.get("panel_id"),
                "status": page.get("status"),
                "blockers": page.get("blockers"),
                "next_recommended_pass": page.get("next_recommended_pass"),
            }
            for page in failed_pages
        ],
        "authority": {
            "launches_packaged_executable": True,
            "captures_native_screenshots": True,
            "terminates_owned_processes": True,
            "writes_visual_evidence": True,
            "writes_installer": False,
            "writes_host_startup": False,
            "mutates_gate": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "executes_workflows": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "unverified": [
            "Installer creation/signing was not attempted.",
            "Startup/autostart integration was not attempted.",
            "Native screenshots use user interface automation text sentinels and pixel diversity; optical character recognition is not performed.",
        ],
        "next_recommended_pass": "studio-installer-plan-and-governance" if ok else "studio-packaged-all-pages-visual-qa-remediation",
    }


def write_visual_qa_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-packaged-app-visual-qa"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("packaged app visual QA evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    screenshot = report.get("screenshot") or {}
    lines = [
        "# Studio Packaged App Visual QA Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        "",
        "## Screenshot",
        "",
        f"- Path: {screenshot.get('path')}",
        f"- Exists: {screenshot.get('exists')}",
        f"- Size bytes: {screenshot.get('size_bytes')}",
        f"- Window: {(screenshot.get('capture') or {}).get('width')} x {(screenshot.get('capture') or {}).get('height')}",
        f"- Nonblank required: {screenshot.get('require_nonblank')}",
        f"- Nonblank OK: {(screenshot.get('visual_verification') or {}).get('ok')}",
        f"- Content area nonblank OK: {(screenshot.get('content_area_verification') or {}).get('ok')}",
        f"- Content area detail: {(screenshot.get('content_area_verification') or {}).get('reason')}",
        f"- Studio content sentinel OK: {(screenshot.get('studio_content_sentinel') or {}).get('ok')}",
        f"- Studio content sentinel detail: {(screenshot.get('studio_content_sentinel') or {}).get('reason')}",
        f"- Developer-facing copy OK: {(screenshot.get('forbidden_visible_copy') or {}).get('ok')}",
        f"- Developer-facing copy detail: {(screenshot.get('forbidden_visible_copy') or {}).get('reason')}",
        f"- Developer-facing copy matches: {', '.join((screenshot.get('forbidden_visible_copy') or {}).get('matches') or []) or 'None'}",
        f"- Capture method: {((screenshot.get('capture') or {}).get('capture_method'))}",
        f"- Window title: {((screenshot.get('capture') or {}).get('window_title'))}",
        f"- Unique colors: {(screenshot.get('visual_verification') or {}).get('unique_color_count')}",
        f"- Dominant color ratio: {(screenshot.get('visual_verification') or {}).get('dominant_color_ratio')}",
        f"- Content area unique colors: {(screenshot.get('content_area_verification') or {}).get('unique_color_count')}",
        f"- Content area dominant color ratio: {(screenshot.get('content_area_verification') or {}).get('dominant_color_ratio')}",
        "",
        "## Launch Host Policy",
        "",
        f"- Status: {((report.get('launch') or {}).get('host_policy') or report.get('host_policy') or {}).get('status')}",
        f"- Windows Application Control blocked: {((report.get('launch') or {}).get('host_policy') or report.get('host_policy') or {}).get('blocked_by_windows_application_control')}",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report.get("blockers") or ["None"]],
        "",
        "## Checks",
        "",
        *[f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}" for item in report.get("checks") or []],
        "",
        "## Authority",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "screenshot_path": screenshot.get("path"),
    }


def write_capture_markdown_open_safety_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-capture-markdown-packaged-open-safety-proof"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Capture packaged open-safety evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Capture Markdown Packaged Open-Safety Proof",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Screenshot root: {report.get('screenshot_root')}",
        "",
        "## Routes",
        "",
    ]
    for route in report.get("routes") or []:
        safety = route.get("process_safety") or {}
        matches = safety.get("matches") or []
        lines.extend(
            [
                f"### {route.get('name') or route.get('id')}",
                "",
                f"- Route: {route.get('route_hash')}",
                f"- OK: {route.get('ok')}",
                f"- Status: {route.get('status')}",
                f"- Visual confirmation OK: {route.get('visual_confirmation_ok')}",
                f"- Visual status: {route.get('visual_status')}",
                f"- Screenshot: {route.get('screenshot_path')}",
                f"- Child-process scans: {safety.get('completed_scan_count')} / {safety.get('snapshot_count')}",
                f"- Forbidden child processes absent: {route.get('forbidden_child_processes_absent')}",
                f"- Forbidden matches: {', '.join(str(item.get('name') or item.get('executable_path')) for item in matches) or 'None'}",
                f"- Blockers: {', '.join(route.get('blockers') or []) or 'None'}",
                f"- Visual blockers: {', '.join(route.get('visual_blockers') or []) or 'None'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Checks",
            "",
            *[f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}" for item in report.get("checks") or []],
            "",
            "## Authority",
            "",
            *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
            "",
            "## Blockers",
            "",
        ]
    )
    blockers = report.get("blockers") or []
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "screenshot_root": report.get("screenshot_root"),
    }


def write_capture_markdown_action_clickthrough_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-capture-markdown-packaged-action-clickthrough"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Capture action clickthrough evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    screenshot = report.get("screenshot") or {}
    action = report.get("action_assessment") or {}
    output_paths = action.get("output_markdown_paths") or []
    source_pack_delta = action.get("source_pack_artifact_delta") or (
        (report.get("write_sentinel") or {}).get("source_pack_artifacts") or {}
    )
    lines = [
        "# Capture Markdown Packaged Action Clickthrough Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        "",
        "## Screenshot",
        "",
        f"- Path: `{(screenshot or {}).get('path')}`",
        f"- Exists: `{(screenshot or {}).get('exists')}`",
        f"- Size bytes: `{(screenshot or {}).get('size_bytes')}`",
        "",
        "## Output Markdown",
        "",
    ]
    if output_paths:
        lines.extend(f"- `{path}`" for path in output_paths)
    else:
        lines.append("- No output Markdown path recorded.")
    lines.extend(
        [
            "",
            "## Source Package Artifacts",
            "",
        ]
    )
    source_pack_added = list(source_pack_delta.get("added") or []) if isinstance(source_pack_delta, dict) else []
    if source_pack_added:
        lines.extend(f"- `{path}`" for path in source_pack_added)
    else:
        lines.append("- No source package artifacts recorded.")
    lines.extend(
        [
            "",
            "## Checks",
            "",
        ]
    )
    for check in report.get("checks") or []:
        lines.append(f"- `{check.get('name')}`: `{check.get('ok')}` - {check.get('detail')}")
    lines.extend(
        [
            "",
            "## Blockers",
            "",
        ]
    )
    blockers = report.get("blockers") or []
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "evidence_root": _relative_to_vault(vault, root),
    }


def write_capture_markdown_window_size_matrix_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-capture-markdown-window-size-matrix"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Capture window-size matrix evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Capture Markdown Packaged Window-Size Matrix Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Capture mode: {report.get('capture_mode')}",
        f"Case count: {report.get('case_count')}",
        f"Screenshot root: {report.get('screenshot_root')}",
        "",
        "## Cases",
        "",
    ]
    for case in report.get("cases") or []:
        requested = case.get("requested") or {}
        captured = case.get("captured") or {}
        lines.extend(
            [
                f"### {case.get('id')}",
                "",
                f"- Requested: {requested.get('width')} x {requested.get('height')}",
                f"- Captured: {captured.get('width')} x {captured.get('height')}",
                f"- Method: {captured.get('method')}",
                f"- Screenshot: {case.get('screenshot_path')}",
                f"- OK: {case.get('ok')}",
                f"- Status: {case.get('status')}",
                f"- Blockers: {', '.join(case.get('blockers') or []) or 'None'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Checks",
            "",
            *[f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}" for item in report.get("checks") or []],
            "",
            "## Authority",
            "",
            *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
            "",
            "## Blockers",
            "",
        ]
    )
    blockers = report.get("blockers") or []
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "screenshot_root": report.get("screenshot_root"),
    }


def write_capture_markdown_downstream_failure_state_matrix_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-capture-markdown-downstream-failure-state-matrix"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Capture downstream failure matrix evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Capture Markdown Packaged Downstream Failure-State Matrix Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Case count: {report.get('case_count')}",
        f"Screenshot root: {report.get('screenshot_root')}",
        "",
        "## Cases",
        "",
    ]
    for case in report.get("cases") or []:
        lines.extend(
            [
                f"### {case.get('label') or case.get('id')}",
                "",
                f"- Case ID: {case.get('id')}",
                f"- OK: {case.get('ok')}",
                f"- Status: {case.get('status')}",
                f"- Guard card visible: {case.get('guard_card_visible')}",
                f"- Expected boundary reached: {case.get('expected_boundary_reached')}",
                f"- Forbidden artifacts not written: {case.get('forbidden_artifacts_not_written')}",
                f"- Screenshot: {case.get('screenshot_path')}",
                f"- Blockers: {', '.join(case.get('blockers') or []) or 'None'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Checks",
            "",
            *[f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}" for item in report.get("checks") or []],
            "",
            "## Authority",
            "",
            *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
            "",
            "## Blockers",
            "",
        ]
    )
    blockers = report.get("blockers") or []
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "screenshot_root": report.get("screenshot_root"),
    }


def write_all_pages_visual_qa_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-packaged-app-all-pages-visual-qa"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("packaged app all-page visual QA evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Studio Packaged App All-Page Visual QA Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Pages: {report.get('page_count')} / {report.get('expected_page_count')}",
        f"Failed pages: {report.get('failed_page_count')}",
        f"Screenshot root: {report.get('screenshot_root')}",
        "",
        "## Pages",
        "",
    ]
    for page in report.get("pages") or []:
        screenshot = page.get("screenshot") or {}
        sentinel = screenshot.get("studio_content_sentinel") or {}
        visual = screenshot.get("content_area_verification") or screenshot.get("visual_verification") or {}
        lines.extend(
            [
                f"### {page.get('panel_name') or page.get('panel_id')}",
                "",
                f"- Panel ID: {page.get('panel_id')}",
                f"- Route: {page.get('route_hash')}",
                f"- OK: {page.get('ok')}",
                f"- Status: {page.get('status')}",
                f"- Screenshot: {screenshot.get('path')}",
                f"- Screenshot exists: {screenshot.get('exists')}",
                f"- Content area nonblank: {visual.get('ok')} ({visual.get('reason')})",
                f"- Studio content sentinel: {sentinel.get('ok')} ({sentinel.get('reason')})",
                f"- Blockers: {', '.join(page.get('blockers') or []) or 'None'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Checks",
            "",
            *[f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}" for item in report.get("checks") or []],
            "",
            "## Authority",
            "",
            *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "screenshot_root": report.get("screenshot_root"),
    }
