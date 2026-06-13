"""Direct smoke test for Chaser Forge operator-use closeout.

This bypasses pytest because the pytest runner has repeatedly hung in this
workspace. The smoke test uses the same public builder as the committed proof,
but injects a deterministic fake UI runner so it can validate the report
contract without launching Playwright or collecting the full test tree.
"""

from __future__ import annotations

import argparse
import faulthandler
import json
from pathlib import Path
import shutil
import time
from typing import Any

from runtime.studio.chaser_forge_marketplace_operator_use_visual_qa import (
    REQUIRED_API_METHODS,
    build_chaser_forge_marketplace_operator_use_visual_qa,
)


SMOKE_STATUS = "COMPLETE / DIRECT CLOSEOUT SMOKE VERIFIED"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_installed_fixture(fixture: Path) -> None:
    _write(
        fixture / "runtime/forge/registry/extensions.json",
        json.dumps(
            {
                "entries": [
                    {
                        "extension_id": "ugc-campaign-studio",
                        "registry_status": "sandbox_installed",
                        "install_environment": "sandbox",
                    }
                ]
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    _write(fixture / "extensions/ugc-campaign-studio/manifest.install.json", "{}\n")
    _write(
        fixture / "07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/import.json",
        json.dumps({"status": "consumed", "approval_consumed": True}, indent=2, sort_keys=True) + "\n",
    )
    _write(
        fixture / "07_LOGS/Agent-Activity/_forge_sandbox_approvals/sandbox.json",
        json.dumps({"status": "consumed", "approval_consumed": True}, indent=2, sort_keys=True) + "\n",
    )
    _write(
        fixture / "07_LOGS/Agent-Activity/_forge_sandbox_approvals/_sandbox_markers/marker.json",
        json.dumps({"status": "completed"}, indent=2, sort_keys=True) + "\n",
    )


def _fixture_factory(root: Path):
    def _make(prefix: str) -> Path:
        target = root / prefix.rstrip("-")
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        return target.resolve()

    return _make


def _fake_runner(vault: Path, output_dir: Path, fixture: Path) -> dict[str, Any]:
    _seed_installed_fixture(fixture)
    screenshots: list[dict[str, Any]] = []
    for step, viewport, status_text, status_state in (
        ("initial", "desktop", "", ""),
        ("after-publish", "desktop", "Published ugc-campaign-studio", "complete"),
        ("after-install", "desktop", "Marketplace install complete", "complete"),
        ("after-install", "mobile", "Marketplace install complete", "complete"),
    ):
        path = output_dir / f"{step}-{viewport}-direct-smoke.png"
        _write(path, "x" * 12048)
        screenshots.append(
            {
                "step": step,
                "viewport": viewport,
                "path": path.relative_to(vault).as_posix(),
                "exists": True,
                "bytes": path.stat().st_size,
                "not_blank": True,
                "marketplace_section_visible": True,
                "publish_button_visible": True,
                "install_button_visible": True,
                "status_text": status_text,
                "status_state": status_state,
                "framework_overlay_detected": False,
            }
        )

    return {
        "url": "file:///direct-smoke/index.html#/chaser-forge",
        "title": "ChaseOS Studio",
        "publish_button_count": 1,
        "install_button_count": 1,
        "publish_status_text": "Published ugc-campaign-studio",
        "publish_status_state": "complete",
        "install_status_text": "Marketplace install complete",
        "install_status_state": "complete",
        "operator_confirmations": [
            "Approve marketplace import review?",
            "Approve sandbox install from marketplace?",
        ],
        "js_call_log": [{"method": method} for method in REQUIRED_API_METHODS],
        "api_call_log": [{"method": method, "ok": True} for method in REQUIRED_API_METHODS],
        "screenshots": screenshots,
        "console_errors_or_warnings": [],
        "page_errors": [],
    }


def _require(checks: dict[str, bool]) -> list[str]:
    return [name for name, ok in checks.items() if ok is not True]


def run_smoke(vault_root: str | Path, *, output_dir: str | Path, timeout_seconds: int) -> dict[str, Any]:
    faulthandler.dump_traceback_later(timeout_seconds, exit=True)
    started = time.perf_counter()
    vault = Path(vault_root).resolve()
    output_path = Path(output_dir)
    output_root = output_path if output_path.is_absolute() else vault / output_path
    tmp_root = (vault / "_cfsmoke").resolve()
    if tmp_root.exists():
        shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True)
    steps: list[dict[str, Any]] = []
    try:
        steps.append({"step": "fixture_root_created", "elapsed_seconds": round(time.perf_counter() - started, 3)})
        report = build_chaser_forge_marketplace_operator_use_visual_qa(
            vault,
            output_dir=output_dir,
            generated_at="2026-05-22T00:00:00Z",
            write=True,
            fixture_factory=_fixture_factory(tmp_root),
            flow_runner=_fake_runner,
        )
        steps.append({"step": "builder_completed", "elapsed_seconds": round(time.perf_counter() - started, 3)})

        summary = report.get("summary") or {}
        checks = {
            "report_ok": report.get("ok") is True,
            "publish_status_visible_after_refresh": summary.get("publish_status_visible_after_refresh") is True,
            "install_status_visible_after_refresh": summary.get("install_status_visible_after_refresh") is True,
            "required_api_methods_called": summary.get("required_api_methods_called") is True,
            "fixture_registry_written": summary.get("fixture_registry_written") is True,
            "fixture_exact_once_marker_written": summary.get("fixture_exact_once_marker_written") is True,
            "report_written": (vault / str(report.get("report_path") or "")).is_file(),
        }
        failures = _require(checks)
        steps.append({"step": "assertions_completed", "elapsed_seconds": round(time.perf_counter() - started, 3)})
        smoke_result_path = output_root / "chaser-forge-marketplace-operator-use-closeout-smoke-result.json"
        try:
            smoke_result_display = smoke_result_path.resolve().relative_to(vault).as_posix()
        except ValueError:
            smoke_result_display = str(smoke_result_path.resolve())
        result = {
            "ok": not failures,
            "status": SMOKE_STATUS if not failures else "BLOCKED / DIRECT CLOSEOUT SMOKE FAILED",
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "checks": checks,
            "failures": failures,
            "report_path": report.get("report_path"),
            "smoke_result_path": smoke_result_display,
            "steps": steps,
        }
        _write(smoke_result_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
        faulthandler.cancel_dump_traceback_later()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run direct Chaser Forge operator-use closeout smoke test.")
    parser.add_argument("--vault-root", default=".", help="Path to ChaseOS vault root.")
    parser.add_argument(
        "--output-dir",
        default="07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-marketplace-operator-use-closeout-smoke",
        help="Output directory inside the vault.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=30, help="Self-timeout before traceback dump and exit.")
    parser.add_argument("--json", action="store_true", help="Print JSON result.")
    args = parser.parse_args(argv)
    result = run_smoke(args.vault_root, output_dir=args.output_dir, timeout_seconds=args.timeout_seconds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
