"""Compatibility entrypoint for the ChaseOS Core CLI."""

from __future__ import annotations

import sys

from runtime.cli.main import build_parser  # re-exported so `chaseos.build_parser is cli.build_parser`


def main(argv: list[str] | None = None) -> int:
    from runtime.cli.main import main as canonical_main

    return canonical_main(list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
