"""Compatibility entrypoint for the canonical ChaseOS CLI.

The installed `chaseos` and `chase` console scripts now point at
`runtime.cli.main:main`. This module remains so direct invocations such as
`python chaseos.py ...` and older tests keep using the same package-native
parser instead of carrying a second command spine.

Deprecation rule: do not add general command registration, dispatch logic, or
subprocess forwarding here. New commands belong in `runtime.cli.main` or imported
command modules registered by `runtime.cli.main`.

Exception: latency-critical Studio panel JSON smokes below use a tiny fast path
that mirrors their canonical handlers without importing the full all-command CLI
parser. This keeps operator readiness probes bounded while preserving the same
read-only model builders and JSON envelope shape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from runtime.cli.main import build_parser  # re-exported so `chaseos.build_parser is cli.build_parser`


def _arg_value(argv: list[str], flag: str) -> str | None:
    try:
        index = argv.index(flag)
    except ValueError:
        return None
    if index + 1 >= len(argv):
        return None
    return argv[index + 1]


def _fast_studio_panel_json(argv: list[str]) -> int | None:
    if len(argv) < 3 or argv[0] != "studio" or "--json" not in argv:
        return None
    vault_root = Path(_arg_value(argv, "--vault-root") or ".").resolve()
    if argv[1] == "approval-center-panel":
        from runtime.studio.approval_center_panel import build_approval_center_panel

        model = build_approval_center_panel(vault_root, source_timeout_seconds=0.0)
        envelope = {
            "ok": True,
            "action": "studio.approval-center-panel",
            "result": model,
            "errors": [],
            "warnings": list(model.get("warnings") or []),
            "audit_id": None,
        }
        print(json.dumps(envelope, indent=2, default=str))
        return 0
    if argv[1] == "runtime-cockpit":
        from runtime.studio.runtime_cockpit import build_runtime_cockpit_contract

        model = build_runtime_cockpit_contract(
            vault_root,
            runtime_id=_arg_value(argv, "--runtime"),
            probe_child_apps=False,
            service_timeout_seconds=0.0,
        )
        exit_code = 0 if model.get("ok", True) else 1
        envelope = {
            "ok": exit_code == 0,
            "action": "studio.runtime-cockpit",
            "result": model,
            "errors": list(model.get("errors") or []),
            "warnings": list(model.get("warnings") or []),
            "audit_id": model.get("audit_id"),
        }
        print(json.dumps(envelope, indent=2, default=str))
        return exit_code
    return None


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    fast_exit = _fast_studio_panel_json(args)
    if fast_exit is not None:
        return fast_exit

    from runtime.cli.main import main as canonical_main

    return canonical_main(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
