"""Packaged Capture to Markdown passive open-safety proof runner."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from runtime.studio.packaged_app_visual_qa import (
    DEFAULT_EVIDENCE_ROOT,
    build_packaged_capture_markdown_open_safety_proof,
    write_capture_markdown_open_safety_evidence,
)


def _resolve_vault_root(value: str | None) -> Path:
    return Path(value or ".").resolve()


def _resolve_evidence_root(vault: Path, value: str | None) -> Path:
    root = Path(value) if value else DEFAULT_EVIDENCE_ROOT
    return (root if root.is_absolute() else vault / root).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open the packaged Capture and Settings routes and verify they do not spawn Studio-owned shell child processes.",
    )
    parser.add_argument("--vault-root", default=None, help="Workspace vault root. Defaults to the current directory.")
    parser.add_argument("--executable-path", default=None, help="Packaged ChaseOS Studio executable path.")
    parser.add_argument("--screenshot-root", default=None, help="Vault-relative screenshot root for this run.")
    parser.add_argument("--evidence-root", default=None, help="Vault-relative evidence root.")
    parser.add_argument("--evidence-slug", default=None, help="Evidence file slug.")
    parser.add_argument("--settle-seconds", type=float, default=8.0, help="Initial packaged app settle time.")
    parser.add_argument("--window-timeout-seconds", type=float, default=15.0, help="Native screenshot timeout budget.")
    parser.add_argument("--terminate-timeout-seconds", type=float, default=5.0, help="Owned process termination timeout.")
    parser.add_argument(
        "--post-capture-observation-seconds",
        type=float,
        default=2.0,
        help="Seconds to keep each route open after screenshot capture while scanning Studio-owned child processes.",
    )
    parser.add_argument("--min-unique-colors", type=int, default=8, help="Minimum unique screenshot colors.")
    parser.add_argument("--max-dominant-ratio", type=float, default=0.95, help="Maximum dominant color ratio.")
    parser.add_argument("--allow-blank-screenshot", action="store_true", help="Do not fail on blank screenshots.")
    parser.add_argument("--write-evidence", action="store_true", help="Write Markdown and JSON evidence files.")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Print the full report as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    vault = _resolve_vault_root(args.vault_root)
    evidence_slug = args.evidence_slug or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-capture-markdown-packaged-open-safety-proof"
    )
    screenshot_root = args.screenshot_root
    if args.write_evidence and screenshot_root is None:
        evidence_root = _resolve_evidence_root(vault, args.evidence_root)
        screenshot_root = evidence_root / f"{evidence_slug}-screenshots"

    report = build_packaged_capture_markdown_open_safety_proof(
        vault,
        executable_path=args.executable_path,
        screenshot_root=screenshot_root,
        settle_seconds=args.settle_seconds,
        window_timeout_seconds=args.window_timeout_seconds,
        terminate_timeout_seconds=args.terminate_timeout_seconds,
        require_nonblank=not args.allow_blank_screenshot,
        min_unique_colors=args.min_unique_colors,
        max_dominant_ratio=args.max_dominant_ratio,
        post_capture_observation_seconds=args.post_capture_observation_seconds,
    )
    if args.write_evidence:
        report["evidence"] = write_capture_markdown_open_safety_evidence(
            vault,
            report,
            evidence_slug=evidence_slug,
            evidence_root=args.evidence_root,
        )
        report["writes_performed"] = True
    else:
        report["writes_performed"] = False

    if args.output_json:
        print(json.dumps(report, indent=2, default=str))
    else:
        status = "OK" if report.get("ok") else "BLOCKED"
        print(f"{status}: {report.get('status')}")
        for blocker in report.get("blockers") or []:
            print(f"- {blocker}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
