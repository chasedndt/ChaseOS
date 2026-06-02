"""Production-safe ChaseOS Core CLI entry point."""

from __future__ import annotations

import argparse
import json


def cmd_health(args: argparse.Namespace) -> int:
    payload = {
        "product": "ChaseOS Core",
        "status": "ok",
        "runtime": "production-safe-core-cli",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{payload['product']}: {payload['status']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chaseos",
        description="ChaseOS Core production-safe command surface",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    health = sub.add_parser("health", help="Show production-safe CLI health")
    health.add_argument("--json", action="store_true", help="Emit JSON")
    health.set_defaults(func=cmd_health)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
