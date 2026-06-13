"""Phase 11 read-only slash card visual QA evidence builder.

This pass renders the existing read-only slash response cards into a bounded
static HTML artifact for visual inspection. It can optionally capture a local
loopback screenshot, but it never executes slash commands, consumes approvals,
dispatches runtimes, calls providers, writes vault content, or mutates canonical
state.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import re
import threading
from typing import Any, Callable

from runtime.chaseos_gate import check_runtime_operation
from runtime.studio.phase11_chat_readonly_slash_command_responses import (
    build_phase11_chat_readonly_slash_command_responses,
)


MODEL_VERSION = "studio.phase11_readonly_card_visual_qa.v1"
SURFACE_ID = "phase11_readonly_card_visual_qa"
PASS_ID = "phase11-chat-readonly-card-visual-qa"
STATUS = "COMPLETE / VISUAL ARTIFACT READY / LOCAL SCREENSHOT OPTIONAL / NO COMMAND EXECUTION"
NEXT_RECOMMENDED_PASS = "phase11-chat-no-hitl-feature-family-selection-audit"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "phase11-readonly-card-visual-qa"
DEFAULT_SCREENSHOT_ROOT = Path("07_LOGS") / "Operator-Screenshots"

VISUAL_COMMANDS = (
    ("/dashboard", "Dashboard"),
    ("/runtime status", "Runtime Status"),
    ("/pet hermes", "Companion"),
    ("/map README", "Vault Map"),
)
REQUIRED_HTML_TOKENS = (
    "phase11-readonly-card-visual-qa-root",
    "phase11-chat-slash-responses",
    "phase11-chat-slash-card-grid",
    "phase11-chat-slash-response-card",
    "Read-Only Slash Responses",
    "Response Cards Ready",
    "Command Execution",
    "Runtime Dispatch",
    "Provider Calls",
    "Vault Writes",
    "Agent Bus Task Write",
    "Authority Boundary",
)


class _QuietSimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime("%Y-%m-%d-phase11-readonly-card-visual-qa")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "phase11-readonly-card-visual-qa"


def _relative_to_vault(vault: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = vault / resolved
    try:
        return resolved.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_evidence_dir(vault: Path, evidence_root: str | Path | None) -> Path:
    root_input = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Phase 11 read-only card visual QA evidence root must stay inside the vault workspace") from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "visual_evidence_allowed": True,
        "command_execution_allowed": False,
        "approval_action_allowed": False,
        "approval_execution_allowed": False,
        "approval_status_mutation_allowed": False,
        "approval_artifact_write_allowed": False,
        "runtime_control_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "browser_launch_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "provider_switch_allowed": False,
        "vault_writes_allowed": False,
        "conversation_persistence_allowed": False,
        "graph_index_write_allowed": False,
        "node_id_write_allowed": False,
        "profile_write_allowed": False,
        "agent_bus_task_write_allowed": False,
        "schedule_mutation_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _card_title(card: dict[str, Any]) -> str:
    labels = {
        "operator_dashboard": "Dashboard Summary",
        "approval_center": "Approval Center",
        "provider_status": "Provider Status",
        "companion_status": "Companion Status",
        "build_logs": "Recent Build Logs",
        "runtime_status": "Runtime Status",
        "vault_map": "Vault Map",
        "memory_show": "Memory Summary",
        "slash_help": "Slash Help",
    }
    return labels.get(str(card.get("kind") or ""), str(card.get("id") or "Response Card").replace("-", " ").title())


def _card_facts(card: dict[str, Any]) -> list[tuple[str, str]]:
    excluded = {"id", "kind", "read_only", "safe_commands", "warnings", "blockers", "latest_logs", "operator_text"}
    facts: list[tuple[str, str]] = []
    for key, value in card.items():
        if key in excluded:
            continue
        if isinstance(value, (dict, list, tuple, set)):
            continue
        label = key.replace("_", " ").title()
        facts.append((label, str(value)))
        if len(facts) >= 6:
            break
    return facts


def _render_visual_html(*, generated_at: str, samples: list[dict[str, Any]], authority: dict[str, Any]) -> str:
    cards_html: list[str] = []
    for sample in samples:
        command = escape(str(sample.get("command") or ""))
        label = escape(str(sample.get("label") or command))
        for card in sample.get("cards") or []:
            facts = "\n".join(
                f"<li><span>{escape(name)}</span><strong>{escape(value)}</strong></li>"
                for name, value in _card_facts(card)
            )
            operator_text = str(card.get("operator_text") or "")
            cards_html.append(
                "\n".join(
                    [
                        '<article class="phase11-chat-slash-response-card" data-write-mode="read-only">',
                        f"  <p class=\"phase11-card-command\">{command}</p>",
                        f"  <h2>{escape(_card_title(card))}</h2>",
                        f"  <p class=\"phase11-card-kind\">{label} / {escape(str(card.get('kind') or 'card'))}</p>",
                        f"  <p class=\"phase11-card-copy\">{escape(operator_text) if operator_text else 'Read-only card data rendered for visual QA.'}</p>",
                        f"  <ul>{facts}</ul>",
                        "</article>",
                    ]
                )
            )

    boundary_rows = [
        ("Command Execution", authority.get("command_execution_allowed")),
        ("Runtime Dispatch", authority.get("runtime_dispatch_allowed")),
        ("Provider Calls", authority.get("provider_calls_allowed")),
        ("Vault Writes", authority.get("vault_writes_allowed")),
        ("Agent Bus Task Write", authority.get("agent_bus_task_write_allowed")),
        ("Canonical Mutation", authority.get("canonical_mutation_allowed")),
    ]
    boundary_html = "\n".join(
        f"<li><span>{escape(label)}</span><strong>{str(value)}</strong></li>" for label, value in boundary_rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Phase 11 Read-Only Card Visual QA</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --ink: #17211c;
      --muted: #5f6762;
      --line: #d8ddd6;
      --panel: #ffffff;
      --accent: #1f6f59;
      --accent-2: #315f9b;
      --warn: #8a5a18;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      font-size: 15px;
      line-height: 1.45;
    }}
    .phase11-readonly-card-visual-qa-root {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 36px;
    }}
    .phase11-chat-slash-responses header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: end;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(28px, 3vw, 46px);
      line-height: 1.05;
      letter-spacing: 0;
    }}
    .phase11-status-strip {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }}
    .phase11-status-chip {{
      border: 1px solid var(--line);
      background: #eef5f1;
      color: var(--accent);
      padding: 7px 10px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .phase11-chat-slash-card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 12px;
      align-items: stretch;
    }}
    .phase11-chat-slash-response-card,
    .phase11-authority-boundary {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 190px;
      padding: 16px;
      overflow-wrap: anywhere;
    }}
    .phase11-card-command,
    .phase11-card-kind {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .phase11-chat-slash-response-card h2,
    .phase11-authority-boundary h2 {{
      margin: 0 0 8px;
      font-size: 18px;
      letter-spacing: 0;
    }}
    .phase11-card-copy {{
      margin: 0 0 12px;
      color: var(--muted);
      min-height: 42px;
    }}
    ul {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 7px;
    }}
    li {{
      display: flex;
      gap: 10px;
      justify-content: space-between;
      border-top: 1px solid #edf0ec;
      padding-top: 7px;
    }}
    li span {{
      color: var(--muted);
      min-width: 0;
    }}
    li strong {{
      color: var(--ink);
      text-align: right;
      min-width: 0;
    }}
    .phase11-authority-boundary {{
      margin-top: 12px;
      border-color: #d7c99e;
      background: #fffdf6;
    }}
    .phase11-authority-boundary h2 {{ color: var(--warn); }}
    @media (max-width: 720px) {{
      .phase11-chat-slash-responses header {{
        grid-template-columns: 1fr;
        align-items: start;
      }}
      .phase11-status-strip {{
        justify-content: flex-start;
      }}
      .phase11-readonly-card-visual-qa-root {{
        width: min(100vw - 20px, 640px);
        padding-top: 18px;
      }}
    }}
  </style>
</head>
<body>
  <main class="phase11-readonly-card-visual-qa-root phase11-chat-slash-responses" data-write-mode="read-only">
    <header>
      <div>
        <p class="phase11-card-kind">Phase 11 Chat</p>
        <h1>Read-Only Slash Responses</h1>
        <p class="phase11-card-copy">Response Cards Ready for static visual QA. Generated {escape(generated_at)}.</p>
      </div>
      <div class="phase11-status-strip" aria-label="Visual QA readiness">
        <span class="phase11-status-chip">Response Cards Ready</span>
        <span class="phase11-status-chip">Read Only</span>
        <span class="phase11-status-chip">No Command Execution</span>
      </div>
    </header>
    <section class="phase11-chat-slash-card-grid" aria-label="Read-only slash response cards">
      {''.join(cards_html)}
    </section>
    <section class="phase11-authority-boundary" aria-label="Authority Boundary">
      <h2>Authority Boundary</h2>
      <p class="phase11-card-copy">Visual evidence only; the artifact renders already-bounded read-only response data.</p>
      <ul>{boundary_html}</ul>
    </section>
  </main>
</body>
</html>
"""


def _html_contract(html_text: str) -> dict[str, Any]:
    script_tag_count = html_text.lower().count("<script")
    missing = [token for token in REQUIRED_HTML_TOKENS if token not in html_text]
    return {
        "script_tag_count": script_tag_count,
        "script_tags_present": script_tag_count > 0,
        "responsive_viewport_ready": '<meta name="viewport"' in html_text
        and "width=device-width" in html_text,
        "required_tokens_present": [token for token in REQUIRED_HTML_TOKENS if token in html_text],
        "missing_required_tokens": missing,
        "root_selector_present": "phase11-readonly-card-visual-qa-root" in html_text,
    }


def _operator_screenshot_runner(**kwargs: Any) -> dict[str, Any]:
    from runtime.operator_surface.browser.operator import run_screenshot

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = run_screenshot(
            url=str(kwargs["url"]),
            output_path=str(kwargs["output_path"]),
            extra_origins=[],
            vault_root=Path(str(kwargs["vault_root"])),
            output_json=True,
            wait_for_selector=str(kwargs.get("wait_for_selector") or "body"),
            wait_timeout_ms=int(kwargs.get("wait_timeout_ms") or 5000),
            settle_ms=int(kwargs.get("settle_ms") or 250),
            full_page=bool(kwargs.get("full_page", True)),
            clip_selector=kwargs.get("clip_selector"),
            require_nonblank=bool(kwargs.get("require_nonblank")),
            min_unique_colors=int(kwargs.get("min_unique_colors") or 2),
            max_dominant_ratio=float(kwargs.get("max_dominant_ratio") or 0.995),
        )
    raw = buffer.getvalue().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {"raw_output": raw}
    payload["success"] = bool(payload.get("success")) and exit_code == 0
    payload["exit_code"] = exit_code
    return payload


def _capture_loopback_screenshot(
    *,
    vault: Path,
    html_path: Path,
    screenshot_path: Path,
    screenshot_runner: Callable[..., dict[str, Any]] | None,
) -> dict[str, Any]:
    rel_screenshot = _relative_to_vault(vault, screenshot_path) or str(screenshot_path)
    allowed, reason = check_runtime_operation(
        "browser.screenshot",
        write_targets=["07_LOGS/Agent-Activity/", rel_screenshot],
        external_api="browser.navigation",
        external_side_effect=True,
    )
    if not allowed:
        return {
            "success": False,
            "blocked": True,
            "gate_reason": reason,
            "screenshot_path": rel_screenshot,
        }

    runner = screenshot_runner or _operator_screenshot_runner
    handler = partial(_QuietSimpleHTTPRequestHandler, directory=str(html_path.parent))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = int(httpd.server_address[1])
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{port}/{html_path.name}"
        result = runner(
            url=url,
            output_path=screenshot_path,
            vault_root=vault,
            wait_for_selector=".phase11-readonly-card-visual-qa-root",
            clip_selector=".phase11-readonly-card-visual-qa-root",
            require_nonblank=True,
            min_unique_colors=8,
            max_dominant_ratio=0.985,
            full_page=False,
            wait_timeout_ms=5000,
            settle_ms=300,
        )
        result["url"] = url
        result["screenshot_path"] = _relative_to_vault(vault, result.get("screenshot_path") or screenshot_path)
        result["gate_reason"] = reason
        return result
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _write_artifacts(
    *,
    vault: Path,
    report: dict[str, Any],
    html_text: str,
    evidence_root: str | Path | None,
    evidence_slug: str | None,
) -> dict[str, Any]:
    evidence_dir = _resolve_evidence_dir(vault, evidence_root)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(evidence_slug)
    html_path = evidence_dir / f"{slug}.html"
    json_path = evidence_dir / f"{slug}.json"
    markdown_path = evidence_dir / f"{slug}.md"
    html_path.write_text(html_text, encoding="utf-8")

    evidence = {
        "written": True,
        "html_path": _relative_to_vault(vault, html_path),
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "screenshot_path": None,
    }
    report["evidence"] = evidence
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    markdown_path.write_text(
        "\n".join(
            [
                "# Phase 11 Read-Only Card Visual QA",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- HTML artifact: {evidence['html_path']}",
                f"- Screenshot artifact: {evidence['screenshot_path'] or 'not captured'}",
                f"- Visual browser QA complete: {(report.get('summary') or {}).get('visual_browser_qa_complete')}",
                f"- Command execution allowed: {(report.get('authority') or {}).get('command_execution_allowed')}",
                f"- Runtime dispatch allowed: {(report.get('authority') or {}).get('runtime_dispatch_allowed')}",
                f"- Provider calls allowed: {(report.get('authority') or {}).get('provider_calls_allowed')}",
                f"- Vault writes allowed: {(report.get('authority') or {}).get('vault_writes_allowed')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def build_phase11_readonly_card_visual_qa(
    vault_root: str | Path,
    *,
    write_evidence: bool = False,
    capture_screenshot: bool = False,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
    screenshot_runner: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a static visual-QA artifact for read-only slash response cards."""

    vault = _vault_path(vault_root)
    generated_at = _now_utc()
    authority = _authority()
    samples: list[dict[str, Any]] = []
    for message, label in VISUAL_COMMANDS:
        payload = build_phase11_chat_readonly_slash_command_responses(vault, message=message, max_nodes=32)
        samples.append(
            {
                "message": message,
                "command": message,
                "label": label,
                "ok": bool(payload.get("ok")),
                "summary": payload.get("summary") or {},
                "cards": list(payload.get("cards") or []),
                "blocked_reasons": list(payload.get("blocked_reasons") or []),
            }
        )

    card_count = sum(len(sample.get("cards") or []) for sample in samples)
    html_text = _render_visual_html(generated_at=generated_at, samples=samples, authority=authority)
    contract = _html_contract(html_text)
    blockers: list[str] = []
    if card_count < 1:
        blockers.append("no_readonly_cards_rendered")
    if contract["script_tags_present"]:
        blockers.append("static_html_contains_script_tag")
    if not contract["responsive_viewport_ready"]:
        blockers.append("responsive_viewport_meta_missing")
    if contract["missing_required_tokens"]:
        blockers.append("required_visual_tokens_missing")

    report: dict[str, Any] = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": generated_at,
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "visual_artifact_ready": not blockers,
            "visual_browser_qa_complete": False,
            "screenshot_captured": False,
            "card_count": card_count,
            "sample_command_count": len(samples),
            "script_tags_present": bool(contract["script_tags_present"]),
            "responsive_viewport_ready": bool(contract["responsive_viewport_ready"]),
            "command_execution_performed": False,
            "approval_execution_performed": False,
            "runtime_dispatch_performed": False,
            "browser_action_performed": False,
            "provider_call_performed": False,
            "vault_write_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "samples": samples,
        "html_contract": contract,
        "artifact_preview": {"html": html_text},
        "authority": authority,
        "evidence": {
            "written": False,
            "html_path": None,
            "json_path": None,
            "markdown_path": None,
            "screenshot_path": None,
        },
        "screenshot": {
            "requested": bool(capture_screenshot),
            "attempted": False,
            "success": False,
            "result": None,
        },
        "blocked_reasons": blockers,
        "readiness": {
            "visual_artifact_ready": not blockers,
            "browser_visual_qa_complete": False,
            "in_app_browser_visual_qa_verified": False,
            "command_execution_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    if write_evidence:
        evidence = _write_artifacts(
            vault=vault,
            report=report,
            html_text=html_text,
            evidence_root=evidence_root,
            evidence_slug=evidence_slug,
        )
        report["evidence"] = evidence

    if capture_screenshot:
        if not write_evidence:
            blockers.append("capture_screenshot_requires_write_evidence")
        else:
            slug = _safe_slug(evidence_slug)
            html_path = vault / str(report["evidence"]["html_path"])
            screenshot_path = vault / DEFAULT_SCREENSHOT_ROOT / f"{slug}.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            screenshot = _capture_loopback_screenshot(
                vault=vault,
                html_path=html_path,
                screenshot_path=screenshot_path,
                screenshot_runner=screenshot_runner,
            )
            captured = bool(screenshot.get("success")) and Path(vault / str(screenshot.get("screenshot_path"))).is_file()
            report["screenshot"] = {
                "requested": True,
                "attempted": True,
                "success": captured,
                "result": screenshot,
            }
            report["summary"]["screenshot_captured"] = captured
            report["summary"]["visual_browser_qa_complete"] = captured and bool(
                (screenshot.get("visual_verification") or {}).get("ok", True)
            )
            report["readiness"]["browser_visual_qa_complete"] = bool(report["summary"]["visual_browser_qa_complete"])
            report["evidence"]["screenshot_path"] = screenshot.get("screenshot_path")
            if not report["summary"]["visual_browser_qa_complete"]:
                blockers.append("browser_visual_qa_screenshot_failed")
            if report["evidence"].get("json_path"):
                json_path = vault / str(report["evidence"]["json_path"])
                json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
            if report["evidence"].get("markdown_path"):
                markdown_path = vault / str(report["evidence"]["markdown_path"])
                markdown_path.write_text(
                    "\n".join(
                        [
                            "# Phase 11 Read-Only Card Visual QA",
                            "",
                            f"- Status: {report.get('status')}",
                            f"- Pass: {report.get('pass')}",
                            f"- HTML artifact: {report['evidence'].get('html_path')}",
                            f"- Screenshot artifact: {report['evidence'].get('screenshot_path') or 'not captured'}",
                            f"- Visual browser QA complete: {report['summary'].get('visual_browser_qa_complete')}",
                            f"- Command execution allowed: {authority.get('command_execution_allowed')}",
                            f"- Runtime dispatch allowed: {authority.get('runtime_dispatch_allowed')}",
                            f"- Provider calls allowed: {authority.get('provider_calls_allowed')}",
                            f"- Vault writes allowed: {authority.get('vault_writes_allowed')}",
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )

    report["blocked_reasons"] = list(dict.fromkeys(blockers))
    report["ok"] = not report["blocked_reasons"]
    report["summary"]["visual_artifact_ready"] = report["ok"] or (
        "browser_visual_qa_screenshot_failed" in report["blocked_reasons"]
        and not any(reason in report["blocked_reasons"] for reason in ("no_readonly_cards_rendered", "static_html_contains_script_tag"))
    )
    return report


def format_phase11_readonly_card_visual_qa(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    authority = payload.get("authority") or {}
    evidence = payload.get("evidence") or {}
    return "\n".join(
        [
            "Phase 11 Read-Only Card Visual QA",
            f"  status: {payload.get('status')}",
            f"  visual_artifact_ready: {summary.get('visual_artifact_ready')}",
            f"  visual_browser_qa_complete: {summary.get('visual_browser_qa_complete')}",
            f"  screenshot_captured: {summary.get('screenshot_captured')}",
            f"  card_count: {summary.get('card_count')}",
            f"  html_path: {evidence.get('html_path') or '(not written)'}",
            f"  screenshot_path: {evidence.get('screenshot_path') or '(not captured)'}",
            f"  command_execution_allowed: {authority.get('command_execution_allowed')}",
            f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
            f"  provider_calls_allowed: {authority.get('provider_calls_allowed')}",
            f"  vault_writes_allowed: {authority.get('vault_writes_allowed')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: visual evidence only; no command execution, approval execution, runtime dispatch, provider/model call, vault write, Agent Bus task write, or canonical mutation.",
        ]
    )
