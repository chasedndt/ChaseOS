"""Phase 10 real-target upgrade path-policy guard helpers.

The helpers in this module are intentionally no-mutation validators for the future
``approved_target_upgrade_executor`` lane.  They inspect an operator-selected
root and a planned create-only operation list, then report whether every planned
write would remain inside the selected root without touching protected/canonical
ChaseOS surfaces or overwriting existing content.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable


MODEL_VERSION = "studio.target_write_path_policy.v1"
ALLOWED_CREATE_OPERATIONS = {"create_file", "create_directory"}

PROTECTED_EXACT_PATHS = {
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
    "06_AGENTS/Agent-Security-Model.md",
}
PROTECTED_PREFIXES = ("06_AGENTS/Permission-Matrix", "06_AGENTS/Trust-Tiers", "06_AGENTS/Agent-Security-Model")
CANONICAL_PREFIXES = ("02_KNOWLEDGE/",)
CONTROL_POLICY_PREFIXES = ("runtime/policy/", "runtime/workflows/registry/")


def _policy_key(path: str) -> str:
    """Return the comparison key used for ChaseOS path-policy checks.

    The displayed ``normalized_relative_path`` intentionally preserves operator
    casing, but protected/canonical/control comparisons must fail closed on
    Windows-mounted targets where case-drifted names can address the same file.
    """

    return path.casefold()


PROTECTED_EXACT_PATH_KEYS = {_policy_key(path) for path in PROTECTED_EXACT_PATHS}
PROTECTED_PREFIX_KEYS = tuple(_policy_key(prefix) for prefix in PROTECTED_PREFIXES)
CANONICAL_PREFIX_KEYS = tuple(_policy_key(prefix) for prefix in CANONICAL_PREFIXES)
CONTROL_POLICY_PREFIX_KEYS = tuple(_policy_key(prefix) for prefix in CONTROL_POLICY_PREFIXES)


def _is_absolute_planned_path(raw_path: str) -> bool:
    normalized = raw_path.replace("\\", "/")
    return bool(PureWindowsPath(raw_path).drive or PureWindowsPath(raw_path).root or PurePosixPath(normalized).is_absolute())


def _normalize_relative_path(raw_path: Any) -> tuple[str, list[str]]:
    blockers: list[str] = []
    text = str(raw_path or "").strip()
    normalized = text.replace("\\", "/")
    if not normalized:
        return "", ["empty-planned-target-path"]
    if _is_absolute_planned_path(text):
        blockers.append("absolute-planned-target-path")

    parts = [part for part in normalized.split("/") if part and part != "."]
    if any(part == ".." for part in parts):
        blockers.append("foreign-folder-escape")
    safe_parts = [part for part in parts if part != ".."]
    return "/".join(safe_parts), blockers


def _path_policy_blockers(normalized_relative: str) -> list[str]:
    blockers: list[str] = []
    policy_relative = _policy_key(normalized_relative)
    policy_without_trailing = policy_relative.rstrip("/")
    if policy_without_trailing in PROTECTED_EXACT_PATH_KEYS or any(
        policy_without_trailing == prefix or policy_without_trailing.startswith(prefix + "/")
        for prefix in PROTECTED_PREFIX_KEYS
    ):
        blockers.append("protected-target-path")
    if any(policy_relative == prefix.rstrip("/") or policy_relative.startswith(prefix) for prefix in CANONICAL_PREFIX_KEYS):
        blockers.append("canonical-target-path")
    if any(
        policy_relative == prefix.rstrip("/") or policy_relative.startswith(prefix)
        for prefix in CONTROL_POLICY_PREFIX_KEYS
    ):
        blockers.append("control-policy-target-path")
    return blockers


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _relative_display(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def validate_target_write_plan(target_root: str | Path, planned_writes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Validate a create-only target-write plan without mutating the target.

    The future real-target executor must run a guard like this before reserving
    markers, consuming approvals, invoking scaffold generation, or writing target
    files.  This helper deliberately returns ``write_enabled: False`` and
    ``target_writes_performed: False`` so callers cannot mistake policy readiness
    for execution authority.
    """

    root = Path(target_root).resolve()
    operations: list[dict[str, Any]] = []
    all_blockers: list[str] = []

    for index, op in enumerate(planned_writes or []):
        raw_relative = op.get("relative_path", op.get("target_path", "")) if isinstance(op, dict) else ""
        operation_type = str(op.get("operation_type", "") if isinstance(op, dict) else "").strip()
        normalized_relative, blockers = _normalize_relative_path(raw_relative)
        blockers.extend(_path_policy_blockers(normalized_relative))
        if operation_type not in ALLOWED_CREATE_OPERATIONS:
            blockers.append("unsupported-write-operation")

        raw_path_text = str(raw_relative or "").strip()
        raw_join_text = raw_path_text.replace("\\", "/")
        candidate = Path(raw_path_text) if _is_absolute_planned_path(raw_path_text) else root / raw_join_text
        resolved_candidate = candidate.resolve(strict=False)
        resolved_within_target = False
        try:
            resolved_candidate.relative_to(root)
            resolved_within_target = True
        except ValueError:
            resolved_within_target = False

        if not resolved_within_target and "foreign-folder-escape" not in blockers:
            blockers.append("symlink-escape")

        would_overwrite = resolved_candidate.exists()
        if would_overwrite:
            blockers.append("target-path-already-exists")

        blockers = _dedupe(blockers)
        all_blockers.extend(blockers)
        operations.append(
            {
                "operation_id": op.get("operation_id", f"operation-{index}") if isinstance(op, dict) else f"operation-{index}",
                "operation_type": operation_type,
                "relative_path": str(raw_relative),
                "normalized_relative_path": normalized_relative,
                "resolved_path": _relative_display(root, resolved_candidate),
                "resolved_within_target": resolved_within_target,
                "would_overwrite": would_overwrite,
                "allowed": not blockers,
                "blockers": blockers,
            }
        )

    aggregate_blockers = _dedupe(all_blockers)
    return {
        "ok": not aggregate_blockers,
        "schema_version": MODEL_VERSION,
        "policy": "create-only-target-write-no-overwrite-no-protected-canonical-foreign-symlink",
        "target_root": str(root),
        "planned_write_count": len(operations),
        "write_enabled": False,
        "target_writes_performed": False,
        "approval_consumed": False,
        "scaffold_execution_performed": False,
        "blockers": aggregate_blockers,
        "operations": operations,
    }
