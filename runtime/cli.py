"""Compatibility entrypoint for the canonical ChaseOS CLI.

`runtime/cli.py` used to be a runtime-level dispatcher that spawned sibling
scripts. The canonical command surface now lives in `runtime.cli.main`; this
file remains for `python runtime/cli.py ...` and imports the same package
parser instead of defining another one.

Deprecation rule: do not add command registration, dispatch logic, or subprocess
forwarding here. New commands belong in `runtime.cli.main` or imported command
modules registered by `runtime.cli.main`.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.cli.main import build_parser, main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
