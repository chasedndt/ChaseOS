"""CLI entrypoint for the ChaseOS installer/update lane.

This module is intended to be packaged later as `ChaseOS-Installer.exe`, reusing
the existing installer lane if possible. The default behavior still validates
helper-plan files without host mutation. The first execution behavior is a
disposable-target dry run that replaces only files inside an explicit test root.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from runtime.studio.launcher_update_helper import (
    build_launcher_update_helper_disposable_execution_receipt_validation,
    build_launcher_update_helper_executable_scaffold,
    execute_launcher_update_installer_disposable_update_plan,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ChaseOS-Installer.exe",
        description="Validate a ChaseOS installer/update helper plan without executing host mutation.",
    )
    parser.add_argument("--vault-root", default=".", help="Vault root that bounds helper-plan reads.")
    parser.add_argument("--plan-file", default="", help="Helper-plan envelope path inside the vault.")
    parser.add_argument("--approval-digest", default="", help="Expected operator statement SHA-256 digest.")
    parser.add_argument(
        "--execution-boundary-receipt",
        default="",
        help="Disposable-target execution boundary receipt path inside the target root.",
    )
    parser.add_argument(
        "--execution-boundary-digest",
        default="",
        help="Expected disposable-target execution boundary SHA-256 digest.",
    )
    parser.add_argument(
        "--update-plan",
        default="",
        help="Disposable update execution plan JSON path.",
    )
    parser.add_argument(
        "--execute-disposable",
        action="store_true",
        help="Execute a path-bounded disposable target update plan.",
    )
    parser.add_argument("--parent-pid", type=int, default=None, help="Future parent Studio process id.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.update_plan:
        result = execute_launcher_update_installer_disposable_update_plan(
            args.update_plan,
            vault_root=Path(args.vault_root),
            execute_disposable=bool(args.execute_disposable),
        )
    elif args.execution_boundary_receipt:
        result = build_launcher_update_helper_disposable_execution_receipt_validation(
            Path(args.vault_root),
            execution_boundary_receipt_path=args.execution_boundary_receipt,
            execution_boundary_digest=args.execution_boundary_digest,
        )
    else:
        result = build_launcher_update_helper_executable_scaffold(
            Path(args.vault_root),
            plan_file_path=args.plan_file or None,
            approval_digest=args.approval_digest,
            parent_pid=args.parent_pid,
        )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result.get("message") or result.get("status") or "installer/update scaffold validated")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
