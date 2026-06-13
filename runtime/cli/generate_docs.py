"""Generate ChaseOS CLI command reference docs from the command contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "runtime" / "cli" / "command_contract.json"
DOC_PATH = ROOT / "06_AGENTS" / "ChaseOS-CLI-Command-Reference.md"
HANDBOOK_PATH = ROOT / "06_AGENTS" / "ChaseOS-CLI-Operator-Handbook.md"
HANDBOOK_METADATA_PATH = ROOT / "runtime" / "cli" / "operator_handbook_metadata.json"


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_operator_metadata(path: Path = HANDBOOK_METADATA_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"families": {}, "commands": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _expand_args(contract: dict[str, Any], args: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for arg in args:
        include = arg.get("include")
        if include:
            expanded.extend(_expand_args(contract, contract["arg_sets"][include]))
        else:
            expanded.append(arg)
    return expanded


def _format_arg(arg: dict[str, Any]) -> str:
    choices = arg.get("choices")
    value = "|".join(str(choice) for choice in choices) if choices else str(arg.get("value") or arg.get("dest", "")).upper()
    required = bool(arg.get("required", False))
    flags = arg.get("flags") or []
    if arg.get("kind") == "flag":
        text = flags[0]
    elif flags:
        text = f"{flags[0]} {value}"
    else:
        text = value
    return text if required else f"[{text}]"


def _command_usage(contract: dict[str, Any], command: dict[str, Any]) -> str:
    args = _expand_args(contract, command.get("args", []))
    suffix = " ".join(_format_arg(arg) for arg in args)
    command_path = " ".join(command["path"])
    return f"chaseos {command_path} {suffix}".strip()


def _command_key(command: dict[str, Any]) -> str:
    return " ".join(command["path"])


def _family_rows(contract: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    families = contract.get("families", {})
    if isinstance(families, dict):
        return [(str(family), meta if isinstance(meta, dict) else {}) for family, meta in families.items()]
    if isinstance(families, list):
        rows: list[tuple[str, dict[str, Any]]] = []
        for family in families:
            if isinstance(family, str):
                rows.append((family, {}))
            elif isinstance(family, dict):
                name = str(family.get("name") or family.get("family") or family.get("id") or "")
                if name:
                    rows.append((name, family))
        return rows
    return []


def _humanize_path(path: list[str]) -> str:
    return " ".join(part.replace("-", " ") for part in path)


def _safety_class(command: dict[str, Any]) -> str:
    effects = " ".join(command.get("side_effects", [])).lower()
    path = " ".join(command.get("path", [])).lower()
    if "approval" in path or "approve" in path:
        return "approval-governed"
    if "write" in effects or "mutate" in effects or "execute" in effects:
        return "mutating-or-execution-adjacent"
    if command.get("json_shape") == "text":
        return "text-or-contract-only"
    return "read-only"


def _ratchet_status_by_path() -> tuple[dict[tuple[str, ...], str], dict[str, dict[str, Any]]]:
    from runtime.cli.contract_ratchet import (
        DEFERRED_SMOKE_COMMANDS,
        SMOKE_COMMANDS,
        family_ratchet_dispositions,
    )

    smoke_paths: dict[tuple[str, ...], str] = {}
    for spec in SMOKE_COMMANDS:
        expected_action = spec.get("expected_action")
        if expected_action:
            path = tuple(str(expected_action).split("."))
            existing = smoke_paths.get(path)
            label = str(spec["name"])
            smoke_paths[path] = f"{existing}, {label}" if existing else f"ratchet-smoked: {label}"

    family_rows = {row["family"]: row for row in family_ratchet_dispositions(load_contract())}
    for spec in DEFERRED_SMOKE_COMMANDS:
        family = str((spec.get("argv") or [spec["name"].split(".", 1)[0]])[0])
        family_rows.setdefault(
            family,
            {
                "family": family,
                "status": "deferred",
                "deferred_commands": [],
                "smoke_commands": [],
            },
        )
    return smoke_paths, family_rows


def _deferred_closure_rows() -> list[dict[str, Any]]:
    from runtime.cli.contract_ratchet import deferred_smoke_closure_map

    return deferred_smoke_closure_map()


def _command_ratchet_status(command: dict[str, Any], smoke_paths: dict[tuple[str, ...], str], family_rows: dict[str, dict[str, Any]]) -> str:
    path = tuple(command["path"])
    if path in smoke_paths:
        return smoke_paths[path]
    family = command["family"]
    family_row = family_rows.get(family, {})
    if family_row.get("status") == "deferred":
        return "family-deferred: see deferred smoke map"
    if family_row.get("status") == "contract_docs_only":
        return "contract/docs only"
    return "covered by family ratchet"


def render_operator_handbook(
    contract: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    contract = contract or load_contract()
    metadata = metadata or load_operator_metadata()
    family_meta = metadata.get("families", {})
    command_meta = metadata.get("commands", {})
    smoke_paths, family_rows = _ratchet_status_by_path()

    lines: list[str] = [
        "---",
        "title: ChaseOS CLI Operator Handbook",
        "type: generated-operator-handbook",
        "status: generated",
        "generated_from:",
        "  - runtime/cli/command_contract.json",
        "  - runtime/cli/contract_ratchet.py",
        "  - runtime/cli/operator_handbook_metadata.json",
        "---",
        "",
        "# ChaseOS CLI Operator Handbook",
        "",
        "> Generated by `python -m runtime.cli.generate_docs --write`.",
        "> Do not hand-edit command coverage. Update the command contract, ratchet specs, or operator handbook metadata.",
        "",
        "**Approval Center routing:** generated approval-center and approval-queue command references should point operators to [[ChaseOS-Approval-Center]] for current cross-feature Approval Center semantics.",
        "",
        "This handbook is the operator-facing companion to `ChaseOS-CLI-Command-Reference.md`. It explains what each command is for, how it is expected to be used, and how the CLI ratchet currently treats it.",
        "",
        "## Ratchet Status Legend",
        "",
        "- `ratchet-smoked`: representative command is executed by `chaseos test cli-contract`.",
        "- `family-deferred`: the command family has known safety, fixture, readiness, or normalization blockers recorded in the deferred closure map.",
        "- `closed_...` deferred entries are intentionally not routine-smoked and have a representative safe smoke plus a promotion boundary.",
        "- `contract/docs only`: parser, contract, action, and docs are checked, but no live smoke is run.",
        "- `covered by family ratchet`: another command in the same family represents this command's parser/JSON surface.",
        "",
    ]

    deferred_rows = _deferred_closure_rows()
    if deferred_rows:
        lines.extend(
            [
                "## Deferred Smoke Closure Map",
                "",
                "These entries are intentionally excluded from routine smoke execution. Each one must keep a representative smoke, fixture/readiness posture, forbidden ratchet actions, and promotion condition so deferrals stay auditable.",
                "",
                "| Deferred command | Status | Blocker | Representative smoke | Fixture readiness | Forbidden during ratchet | Promotion condition |",
                "|------------------|--------|---------|----------------------|-------------------|--------------------------|---------------------|",
            ]
        )
        for row in deferred_rows:
            forbidden = ", ".join(row.get("forbidden_during_ratchet", []))
            lines.append(
                "| "
                f"`{row['command']}` | "
                f"`{row['closure_status']}` | "
                f"`{row['blocker_type']}` | "
                f"`{row['representative_smoke']}` | "
                f"{row['fixture_readiness']} | "
                f"{forbidden} | "
                f"{row['promotion_condition']} |"
            )
        lines.append("")

    commands_by_family: dict[str, list[dict[str, Any]]] = {}
    for command in contract.get("commands", []):
        commands_by_family.setdefault(command["family"], []).append(command)

    for family, meta in _family_rows(contract):
        commands = commands_by_family.get(family, [])
        if not commands:
            continue
        configured = family_meta.get(family, {})
        family_status = family_rows.get(family, {}).get("status", "contract_docs_only")
        lines.extend(
            [
                f"## {family}",
                "",
                configured.get("description")
                or meta.get("summary")
                or f"Operator commands for the `{family}` family.",
                "",
                f"**Ratchet disposition:** `{family_status}`",
                "",
                f"**Real-world use case:** {configured.get('use_case') or f'Use `{family}` commands when operating this ChaseOS subsystem from a shell or automation surface.'}",
                "",
                "| Command | Purpose | Example | Safety | Ratchet | Real-world scenario |",
                "|---------|---------|---------|--------|---------|---------------------|",
            ]
        )
        for command in commands:
            key = _command_key(command)
            override = command_meta.get(key, {})
            usage = _command_usage(contract, command)
            purpose = override.get("purpose") or f"{_humanize_path(command['path']).capitalize()}."
            example = override.get("example") or usage
            scenario = override.get("scenario") or configured.get("scenario") or configured.get("use_case") or (
                f"Use this when you need the `{key}` surface during ChaseOS operation."
            )
            ratchet_status = _command_ratchet_status(command, smoke_paths, family_rows)
            lines.append(
                "| "
                f"`{usage}` | "
                f"{purpose} | "
                f"`{example}` | "
                f"`{_safety_class(command)}` | "
                f"`{ratchet_status}` | "
                f"{scenario} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def operator_handbook_coverage_failures(contract: dict[str, Any], rendered: str) -> list[str]:
    failures: list[str] = []
    for command in contract.get("commands", []):
        usage = _command_usage(contract, command)
        if f"`{usage}`" not in rendered:
            failures.append(f"operator handbook missing command path: {usage}")
    return failures


def render_markdown(contract: dict[str, Any] | None = None) -> str:
    contract = contract or load_contract()
    family_rows = _family_rows(contract)
    lines: list[str] = [
        "---",
        "title: ChaseOS CLI Command Reference",
        "type: generated-reference",
        "status: generated",
        f"generated_from: runtime/cli/command_contract.json",
        "---",
        "",
        "# ChaseOS CLI Command Reference",
        "",
        "> Generated from `runtime/cli/command_contract.json`.",
        "> Regenerate with `python -m runtime.cli.generate_docs --write`.",
        "",
        "**Approval Center routing:** generated approval-center and approval-queue command references should point operators to [[ChaseOS-Approval-Center]] for current cross-feature Approval Center semantics.",
        "",
        "Do not edit command tables by hand. Update `runtime.cli.main` and the command contract, then regenerate.",
        "",
        "## Entrypoints",
        "",
    ]

    for entrypoint in contract.get("entrypoints", []):
        lines.append(f"- `{entrypoint}`")

    envelope_keys = contract.get("json_contract", {}).get("envelope_keys", [])
    lines.extend(
        [
            "",
            "## JSON Envelope",
            "",
            "Canonical `--json` output is wrapped with:",
            "",
            "| Key |",
            "|-----|",
        ]
    )
    for key in envelope_keys:
        lines.append(f"| `{key}` |")

    lines.extend(
        [
            "",
            "## Deprecation Rules",
            "",
            "- `chaseos.py` is a compatibility shim only.",
            "- `runtime/cli.py` is a compatibility shim only.",
            "- New commands must be registered through `runtime.cli.main` or command modules imported by `runtime.cli.main`.",
            "- Do not add subprocess forwarding or independent parser trees to compatibility shims.",
            "",
            "## Command Families",
            "",
            "| Family | Maturity | Summary |",
            "|--------|----------|---------|",
        ]
    )
    for family, meta in family_rows:
        maturity = meta.get("default_maturity", meta.get("maturity", ""))
        lines.append(
            f"| `{family}` | {maturity} | {meta.get('summary', '')} |"
        )

    lines.extend(["", "## Commands", ""])
    commands_by_family: dict[str, list[dict[str, Any]]] = {}
    for command in contract.get("commands", []):
        commands_by_family.setdefault(command["family"], []).append(command)

    for family, _meta in family_rows:
        commands = commands_by_family.get(family, [])
        if not commands:
            continue
        lines.extend(
            [
                f"### {family}",
                "",
                "| Command | Handler | JSON Shape | Side Effects |",
                "|---------|---------|------------|--------------|",
            ]
        )
        for command in commands:
            usage = _command_usage(contract, command)
            side_effects = ", ".join(command.get("side_effects", []))
            lines.append(
                f"| `{usage}` | `{command.get('handler', '')}` | `{command.get('json_shape', '')}` | {side_effects} |"
            )
        lines.append("")

    lines.extend(
        [
            "",
            "## Graph Hygiene Governance Links",
            "",
            "*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate ChaseOS CLI command reference docs")
    parser.add_argument("--write", action="store_true", help="Write the generated markdown reference")
    parser.add_argument("--check", action="store_true", help="Fail if the generated docs are stale")
    parser.add_argument("--handbook", action="store_true", help="Print only the operator handbook")
    args = parser.parse_args(argv)

    rendered = render_markdown()
    handbook = render_operator_handbook()

    if args.check:
        existing = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        existing_handbook = HANDBOOK_PATH.read_text(encoding="utf-8") if HANDBOOK_PATH.exists() else ""
        failures = []
        if existing != rendered:
            failures.append(f"{DOC_PATH} is stale; run: python -m runtime.cli.generate_docs --write")
        if existing_handbook != handbook:
            failures.append(f"{HANDBOOK_PATH} is stale; run: python -m runtime.cli.generate_docs --write")
        failures.extend(operator_handbook_coverage_failures(load_contract(), existing_handbook or handbook))
        if failures:
            for failure in failures:
                print(failure)
            return 1
        print(f"{DOC_PATH} is up to date.")
        print(f"{HANDBOOK_PATH} is up to date.")
        return 0

    if args.write:
        DOC_PATH.write_text(rendered, encoding="utf-8")
        HANDBOOK_PATH.write_text(handbook, encoding="utf-8")
        print(f"Wrote {DOC_PATH}")
        print(f"Wrote {HANDBOOK_PATH}")
        return 0

    print(handbook if args.handbook else rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
