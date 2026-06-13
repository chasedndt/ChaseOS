"""Proposal staging, validation, and diff preview tools.

Protected file list and write scope frozen against ChaseOS-MCP-Proposal-Staging.md v1.0.
Response shapes frozen against ChaseOS-MCP-Data-Contracts.md v1.0.
"""

from __future__ import annotations

import difflib
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.errors import (
    ERR_PATH_DENIED,
    ERR_PROTECTED_FILE,
    ERR_PROPOSAL_NOT_FOUND,
    domain_error,
    input_error,
    system_error,
)
from runtime.mcp.staging.store import ProposalStore
from runtime.mcp.types import HandlerResult, PermissionEnvelope, ProposalArtifact


# Frozen protected file list per ChaseOS-MCP-Proposal-Staging.md Section "Protected File List".
# These files may be staged but proposal.validate returns a governance violation.
PROTECTED_EXACT = {
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
    "CLAUDE.md",
    "04_SOPS/Credential-Boundaries-SOP.md",
    "04_SOPS/Untrusted-Input-Handling-SOP.md",
    "runtime/aor/engine.py",
}

# Prefix-based protected patterns (runtime policy adapter YAML files).
PROTECTED_PREFIX_PATTERNS: list[tuple[str, str | None]] = [
    ("runtime/policy/adapters/", ".yaml"),
]

# Paths that are always forbidden as proposal targets (credentials, internal hooks).
FORBIDDEN_PREFIXES = {
    ".claude/",
    ".env",
    ".secret",
}

VALID_CHANGE_TYPES = {"create", "update", "delete"}


def normalize_target(value: Any) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "target_file is required"
    raw = value.replace("\\", "/").strip().lstrip("/")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        return None, "target_file must be a vault-relative path without traversal"
    return raw, None


def is_protected_file(target_file: str) -> bool:
    if target_file in PROTECTED_EXACT:
        return True
    for prefix, ext in PROTECTED_PREFIX_PATTERNS:
        if target_file.startswith(prefix):
            if ext is None or target_file.endswith(ext):
                return True
    return False


def write_scope_allowed(target_file: str) -> bool:
    """Return True if the target is in an acceptable proposal write scope.

    Deny only clearly forbidden zones (credentials, internal hooks).
    Everything else in the vault is a legitimate proposal target.
    """
    for forbidden in FORBIDDEN_PREFIXES:
        if target_file.startswith(forbidden) or target_file == forbidden:
            return False
    return True


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _current_sha256(vault_root: Path, target_file: str) -> str | None:
    path = vault_root / target_file
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proposal_submit(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    target_file, target_error = normalize_target(params.get("target_file"))
    if target_error:
        return HandlerResult(False, error=input_error(ERR_PATH_DENIED, target_error))

    proposed_content = params.get("proposed_content")
    change_type = params.get("change_type", "update")
    if change_type not in VALID_CHANGE_TYPES:
        return HandlerResult(
            False,
            error=input_error("invalid_field_value", f"change_type must be one of {sorted(VALID_CHANGE_TYPES)}"),
        )
    if change_type != "delete" and not isinstance(proposed_content, str):
        return HandlerResult(
            False,
            error=input_error("missing_required_field", "proposed_content must be a string for create/update"),
        )
    description = params.get("description") or params.get("rationale", "")
    if not isinstance(description, str):
        description = str(description)

    assert target_file is not None
    protected = is_protected_file(target_file)
    scope_ok = write_scope_allowed(target_file)

    if not scope_ok:
        return HandlerResult(
            False,
            error=domain_error(ERR_PATH_DENIED, "Target file is outside Runtime MCP proposal write scope.", target_file=target_file),
        )

    proposal_id = f"proposal-{uuid.uuid4().hex}"
    staged_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    cur_sha = _current_sha256(config.vault_root, target_file)
    prop_sha = _sha256(proposed_content) if isinstance(proposed_content, str) else None

    artifact = ProposalArtifact(
        schema_version="1.0",
        proposal_id=proposal_id,
        staged_at=staged_at,
        runtime_id=envelope.runtime_id,
        safety_mode_at_staging=envelope.mode,
        change_type=change_type,
        target_file=target_file,
        description=description,
        proposed_content=proposed_content if change_type != "delete" else None,
        current_sha256=cur_sha,
        proposed_sha256=prop_sha,
        governance_flags={
            "is_protected_file": protected,
            "permission_ceiling_respected": True,
            "writeback_scope_declared": scope_ok,
        },
        status="staged",
        status_history=[{"status": "staged", "at": staged_at}],
    )

    try:
        ProposalStore(config.staging_dir).stage(artifact)
    except Exception as exc:  # noqa: BLE001
        return HandlerResult(
            False,
            error=system_error("proposal_staging_write_error", str(exc), proposal_id=proposal_id),
        )

    governance_warnings: list[str] = []
    if protected:
        governance_warnings.append(
            "Target file is protected; proposal.validate will return a governance violation."
        )

    return HandlerResult(
        True,
        {
            "proposal_id": proposal_id,
            "proposal_status": "staged",
            "staged_at": staged_at,
            "target_file": target_file,
            "change_type": change_type,
            "preliminary_validation": {
                "is_protected_file": protected,
                "governance_warnings": governance_warnings,
            },
        },
        files_written=[str(config.staging_dir.relative_to(config.vault_root) / "")],
        audit_metadata={
            "tool": "proposal.submit",
            "proposal_id": proposal_id,
            "target_file": target_file,
            "is_protected_file": protected,
        },
        rollback_proposal_id=proposal_id,
    )


def proposal_validate(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    proposal_id = params.get("proposal_id")
    if not isinstance(proposal_id, str) or not proposal_id:
        return HandlerResult(False, error=input_error(ERR_PROPOSAL_NOT_FOUND, "proposal_id is required"))

    artifact = ProposalStore(config.staging_dir).read(proposal_id)
    if artifact is None:
        return HandlerResult(
            False,
            error=domain_error(ERR_PROPOSAL_NOT_FOUND, "Proposal artifact was not found.", proposal_id=proposal_id),
        )

    errors: list[dict[str, Any]] = []
    if artifact.governance_flags.get("is_protected_file"):
        errors.append(
            {
                "error_type": "domain_error",
                "error_code": ERR_PROTECTED_FILE,
                "message": "Target file is protected. MCP may stage and surface this proposal for human review, but it has no apply path.",
            }
        )
    if not artifact.governance_flags.get("writeback_scope_declared", True):
        errors.append(
            {
                "error_type": "domain_error",
                "error_code": ERR_PATH_DENIED,
                "message": "Target file is outside Runtime MCP proposal write scope.",
            }
        )

    is_valid = not errors
    protected_flag = artifact.governance_flags.get("is_protected_file", False)

    return HandlerResult(
        True,
        {
            "proposal_id": proposal_id,
            "is_valid": is_valid,
            "protected_file_flag": protected_flag,
            "errors": errors,
            "warnings": [],
            "governance_checks": {
                "permission_ceiling_ok": artifact.governance_flags.get("permission_ceiling_respected", True),
                "target_path_in_allowed_writeback_scope": artifact.governance_flags.get("writeback_scope_declared", True),
                "proposed_content_schema_valid": None,
            },
        },
        audit_metadata={
            "tool": "proposal.validate",
            "proposal_id": proposal_id,
            "is_valid": is_valid,
        },
    )


def proposal_diff_preview(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    proposal_id = params.get("proposal_id")
    if not isinstance(proposal_id, str) or not proposal_id:
        return HandlerResult(False, error=input_error(ERR_PROPOSAL_NOT_FOUND, "proposal_id is required"))

    artifact = ProposalStore(config.staging_dir).read(proposal_id)
    if artifact is None:
        return HandlerResult(
            False,
            error=domain_error(ERR_PROPOSAL_NOT_FOUND, "Proposal artifact was not found.", proposal_id=proposal_id),
        )

    if artifact.governance_flags.get("is_protected_file"):
        return HandlerResult(
            False,
            error=domain_error(
                ERR_PROTECTED_FILE,
                "Diff preview is blocked for protected-file proposals.",
                proposal_id=proposal_id,
            ),
        )

    current_path = config.vault_root / artifact.target_file
    current = ""
    if current_path.exists() and current_path.is_file():
        current = current_path.read_text(encoding="utf-8", errors="replace")

    proposed = artifact.proposed_content or ""
    diff_lines = list(
        difflib.unified_diff(
            current.splitlines(),
            proposed.splitlines(),
            fromfile=f"a/{artifact.target_file}",
            tofile=f"b/{artifact.target_file}",
            lineterm="",
        )
    )
    diff_content = "\n".join(diff_lines)
    lines_added = sum(1 for ln in diff_lines if ln.startswith("+") and not ln.startswith("+++"))
    lines_removed = sum(1 for ln in diff_lines if ln.startswith("-") and not ln.startswith("---"))

    return HandlerResult(
        True,
        {
            "proposal_id": proposal_id,
            "target_file": artifact.target_file,
            "diff_format": "unified",
            "current_sha256": artifact.current_sha256,
            "proposed_sha256": artifact.proposed_sha256,
            "diff_content": diff_content,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
        },
        files_read=[artifact.target_file] if current_path.exists() else [],
        audit_metadata={"tool": "proposal.diff_preview", "proposal_id": proposal_id},
    )
