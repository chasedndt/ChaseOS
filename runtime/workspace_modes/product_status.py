"""Read-only product status and artifact ledger for Workspace Mode Layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .loader import load_workspace_profile
from .profile_rollout_plan import DEFAULT_ROLLOUT_CANDIDATES, build_workspace_profile_rollout_plan


PROFILE_APPROVAL_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_profile_write_approvals")
AOR_APPROVAL_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_aor_live_execution_approvals")
AOR_DECISION_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_aor_live_execution_decisions")
AOR_CONSUMPTION_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_aor_live_execution_consumptions")
AOR_MARKER_ROOT = AOR_CONSUMPTION_ROOT / "_markers"

CORE_RUNTIME_MODULES: tuple[str, ...] = (
    "runtime/workspace_modes/models.py",
    "runtime/workspace_modes/loader.py",
    "runtime/workspace_modes/inference.py",
    "runtime/workspace_modes/aor_routing_preview.py",
    "runtime/workspace_modes/profile_rollout_plan.py",
    "runtime/workspace_modes/profile_draft_packet.py",
    "runtime/workspace_modes/profile_write_approval_request.py",
    "runtime/workspace_modes/profile_guarded_writer.py",
    "runtime/workspace_modes/aor_dispatch_gate.py",
    "runtime/workspace_modes/aor_dispatch_dry_run_executor.py",
    "runtime/workspace_modes/aor_live_execution_approval_gate.py",
    "runtime/workspace_modes/aor_live_executor.py",
    "runtime/workspace_modes/product_status.py",
)


def _detect_vault_root() -> Path:
    here = Path(__file__).resolve()
    vault_root = here.parents[2]
    if not (vault_root / "CLAUDE.md").exists():
        raise RuntimeError(f"could not detect ChaseOS vault root from {here}")
    return vault_root


def _safe_relative(path: Path, vault_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(vault_root.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path).replace("\\", "/")


def _json_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": str(exc)}
    return data if isinstance(data, dict) else {"_read_error": "json_root_not_mapping"}


def _artifact_rows(root: Path, vault_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _json_files(root):
        data = _read_json(path)
        rows.append(
            {
                "path": _safe_relative(path, vault_root),
                "approval_packet_id": data.get("approval_packet_id") or path.stem,
                "schema_version": data.get("schema_version"),
                "status": data.get("status") or data.get("decision") or data.get("consumption_status"),
                "workspace_path": (data.get("approval_scope") or {}).get("workspace_path")
                or data.get("workspace_path"),
                "workflow_id": (data.get("approval_scope") or {}).get("workflow_id")
                or data.get("requested_workflow_id"),
                "read_error": data.get("_read_error"),
            }
        )
    return rows


def _approval_ledger(vault_root: Path) -> dict[str, Any]:
    roots = {
        "profile_write_requests": PROFILE_APPROVAL_ROOT,
        "aor_live_execution_requests": AOR_APPROVAL_ROOT,
        "aor_live_execution_decisions": AOR_DECISION_ROOT,
        "aor_live_execution_consumptions": AOR_CONSUMPTION_ROOT,
        "aor_live_execution_markers": AOR_MARKER_ROOT,
    }
    sections: dict[str, Any] = {}
    for label, rel_root in roots.items():
        abs_root = vault_root / rel_root
        rows = _artifact_rows(abs_root, vault_root)
        sections[label] = {
            "root": str(rel_root).replace("\\", "/"),
            "present": abs_root.exists(),
            "count": len(rows),
            "artifacts": rows,
        }
    return {
        "surface": "workspace_mode_approval_ledger",
        "preview_only": True,
        "vault_root": str(vault_root),
        "sections": sections,
        "total_artifacts": sum(int(section["count"]) for section in sections.values()),
        "profile_files_written": False,
        "workflow_execution_performed": False,
        "approval_consumed": False,
        "agent_bus_task_written": False,
        "provider_or_model_call_performed": False,
        "browser_or_external_action_performed": False,
        "canonical_write_performed": False,
    }


def build_workspace_mode_approval_ledger(
    *,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(vault_root).resolve() if vault_root is not None else _detect_vault_root()
    payload = _approval_ledger(root)
    payload["ok"] = True
    return payload


def _profile_coverage(vault_root: Path) -> dict[str, Any]:
    rollout = build_workspace_profile_rollout_plan(vault_root=vault_root)
    rows: list[dict[str, Any]] = []
    valid_count = 0
    present_count = 0
    for candidate in rollout.get("candidates") or []:
        profile_path = str(candidate.get("profile_path") or "")
        abs_path = vault_root / profile_path
        present = abs_path.exists()
        valid = False
        validation_error = None
        if present:
            present_count += 1
            try:
                loaded = load_workspace_profile(abs_path)
                valid = True
                valid_count += 1
            except Exception as exc:
                validation_error = str(exc)
                loaded = None
        else:
            loaded = None
        rows.append(
            {
                "workspace_path": candidate.get("workspace_path"),
                "profile_path": profile_path,
                "expected_mode": candidate.get("recommended_mode"),
                "profile_present": present,
                "profile_valid": valid,
                "loaded_mode": getattr(loaded, "workspace_mode", None),
                "allowed_workflows": list(getattr(loaded, "allowed_workflows", ()) or []),
                "validation_error": validation_error,
            }
        )
    expected_count = len(DEFAULT_ROLLOUT_CANDIDATES)
    return {
        "expected_profile_count": expected_count,
        "profiles_present_count": present_count,
        "profiles_valid_count": valid_count,
        "profiles_missing_count": expected_count - present_count,
        "profile_coverage_complete": present_count == expected_count and valid_count == expected_count,
        "profiles": rows,
        "missing_profile_paths": [
            row["profile_path"] for row in rows if not bool(row["profile_present"])
        ],
        "invalid_profile_paths": [
            row["profile_path"] for row in rows if bool(row["profile_present"]) and not bool(row["profile_valid"])
        ],
    }


def _core_runtime(vault_root: Path) -> dict[str, Any]:
    rows = []
    for rel_path in CORE_RUNTIME_MODULES:
        path = vault_root / rel_path
        rows.append({"path": rel_path, "present": path.exists()})
    return {
        "required_module_count": len(rows),
        "present_module_count": sum(1 for row in rows if row["present"]),
        "core_runtime_complete": all(row["present"] for row in rows),
        "modules": rows,
    }


def build_workspace_mode_product_status(
    *,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a read-only WML product status derived from repo evidence."""

    root = Path(vault_root).resolve() if vault_root is not None else _detect_vault_root()
    profile_coverage = _profile_coverage(root)
    core_runtime = _core_runtime(root)
    ledger = _approval_ledger(root)
    cli_docs_present = (root / "06_AGENTS/ChaseOS-CLI-Command-Reference.md").exists()
    operator_docs_present = (root / "06_AGENTS/ChaseOS-CLI-Operator-Handbook.md").exists()
    architecture_docs_present = all(
        (root / rel_path).exists()
        for rel_path in (
            "06_AGENTS/Workspace-Mode-Profile-Standard.md",
            "06_AGENTS/Use-Case-Mode-Architecture.md",
        )
    )
    product_feature_complete = bool(
        core_runtime["core_runtime_complete"]
        and profile_coverage["profile_coverage_complete"]
        and cli_docs_present
        and operator_docs_present
        and architecture_docs_present
    )
    blockers: list[str] = []
    if not core_runtime["core_runtime_complete"]:
        blockers.append("core_runtime_modules_missing")
    if not profile_coverage["profile_coverage_complete"]:
        blockers.append("workspace_mode_profile_coverage_incomplete")
    if not cli_docs_present or not operator_docs_present:
        blockers.append("generated_cli_docs_missing")
    if not architecture_docs_present:
        blockers.append("workspace_mode_architecture_docs_missing")

    return {
        "ok": True,
        "surface": "workspace_mode_product_status",
        "status": "COMPLETE" if product_feature_complete else "PARTIAL",
        "wml_product_feature_complete": product_feature_complete,
        "preview_only": True,
        "vault_root": str(root),
        "core_runtime": core_runtime,
        "profile_coverage": profile_coverage,
        "approval_ledger_summary": {
            "total_artifacts": ledger["total_artifacts"],
            "profile_write_requests": ledger["sections"]["profile_write_requests"]["count"],
            "aor_live_execution_requests": ledger["sections"]["aor_live_execution_requests"]["count"],
            "aor_live_execution_decisions": ledger["sections"]["aor_live_execution_decisions"]["count"],
            "aor_live_execution_consumptions": ledger["sections"]["aor_live_execution_consumptions"]["count"],
            "aor_live_execution_markers": ledger["sections"]["aor_live_execution_markers"]["count"],
        },
        "docs_status": {
            "cli_command_reference_present": cli_docs_present,
            "cli_operator_handbook_present": operator_docs_present,
            "architecture_docs_present": architecture_docs_present,
        },
        "authority_flags": {
            "profile_files_written": False,
            "workflow_execution_performed": False,
            "approval_consumed": False,
            "agent_bus_task_written": False,
            "provider_or_model_call_performed": False,
            "browser_or_external_action_performed": False,
            "canonical_write_performed": False,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "workspace-mode-product-doc-closeout-and-operator-guide"
            if product_feature_complete
            else "workspace-mode-full-profile-rollout-or-doc-sync"
        ),
    }


def format_workspace_mode_approval_ledger(payload: dict[str, Any]) -> str:
    lines = [
        "Workspace Mode approval ledger",
        f"  total_artifacts: {payload.get('total_artifacts')}",
        "  boundary: read-only ledger; no profile write, workflow execution, approval consumption, Agent Bus task, external action, or canonical writeback.",
    ]
    for label, section in (payload.get("sections") or {}).items():
        lines.append(f"  {label}: {section.get('count')} artifact(s)")
    return "\n".join(lines)


def format_workspace_mode_product_status(payload: dict[str, Any]) -> str:
    coverage = payload.get("profile_coverage") or {}
    lines = [
        "Workspace Mode product status",
        f"  status:                 {payload.get('status')}",
        f"  product_complete:       {payload.get('wml_product_feature_complete')}",
        f"  core_runtime_complete:  {(payload.get('core_runtime') or {}).get('core_runtime_complete')}",
        f"  profile_coverage:       {coverage.get('profiles_valid_count')}/{coverage.get('expected_profile_count')} valid",
        f"  blockers:               {', '.join(payload.get('blockers') or []) or '(none)'}",
        "  boundary: read-only status; no profile write, workflow execution, approval consumption, Agent Bus task, external action, or canonical writeback.",
    ]
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.product_status",
        description="Show WML product status or approval ledger without mutation.",
    )
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--ledger", action="store_true")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)
    payload = (
        build_workspace_mode_approval_ledger(vault_root=args.vault_root)
        if args.ledger
        else build_workspace_mode_product_status(vault_root=args.vault_root)
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    elif args.ledger:
        print(format_workspace_mode_approval_ledger(payload))
    else:
        print(format_workspace_mode_product_status(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
