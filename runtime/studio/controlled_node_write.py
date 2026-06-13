"""Approval-gated node create/edit controller for Studio Phase 10AA."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from runtime.studio.graph_index_contract import build_graph_index_contract
from runtime.studio.service import ActionSpec, StudioService
from runtime.studio.shell.graph_style_registry import NODE_TYPE_TO_FAMILY
from runtime.studio.shell.write_surface import (
    _NODE_TYPE_PATH_MAP,
    build_target_path,
    resolve_node_file_path,
)


PASS_ID = "phase10aa-controlled-node-create-edit"
NEXT_RECOMMENDED_PASS = "phase10ab-visual-link-approval-flow"

EDITABLE_METADATA_FIELDS: tuple[str, ...] = (
    "title",
    "domain",
    "project",
    "tags",
    "aliases",
    "summary",
    "status",
)

BLOCKED_METADATA_FIELDS: tuple[str, ...] = (
    "trust_state",
    "trust_tier",
    "canonical",
    "canonical_id",
    "generated",
    "generated_by",
    "generated_from",
    "provenance",
    "provenance_chain",
    "source_provenance",
    "runtime_authority",
    "authority_boundary",
    "permissions",
    "node_type",
    "node_family",
    "phase10aa",
)

BLOCKED_METADATA_PREFIXES: tuple[str, ...] = (
    "trust_",
    "canonical_",
    "generated_",
    "provenance_",
    "runtime_",
    "authority_",
)

DOMAIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,79}$")
TITLE_RE = re.compile(r"^[^\r\n\\/]{1,120}$")


@dataclass(frozen=True)
class ControlledNodeType:
    node_type: str
    target_node_type: str
    family: str
    label: str


def _node_type_family(node_type: str) -> str:
    return NODE_TYPE_TO_FAMILY.get(node_type, NODE_TYPE_TO_FAMILY.get("knowledge_doc", "knowledge"))


CONTROLLED_NODE_TYPES: dict[str, ControlledNodeType] = {
    key: ControlledNodeType(
        node_type=key,
        target_node_type=key,
        family=_node_type_family(key),
        label=key.replace("_", " ").title(),
    )
    for key in sorted(_NODE_TYPE_PATH_MAP)
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_stamp() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _rel_path(path: Path, vault_root: Path) -> str:
    return path.resolve().relative_to(vault_root.resolve()).as_posix()


def _safe_vault_path(vault_root: Path, rel_path: str) -> Path | None:
    try:
        candidate = (vault_root / rel_path).resolve()
        candidate.relative_to(vault_root.resolve())
    except Exception:
        return None
    return candidate


def _approval_dir(vault_root: Path) -> Path:
    return vault_root / "runtime" / "studio" / "approvals"


def _active_approval_payloads(vault_root: Path) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    approval_dir = _approval_dir(vault_root)
    if not approval_dir.exists():
        return payloads
    for approval_file in approval_dir.glob("*.json"):
        try:
            payload = yaml.safe_load(approval_file.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if str(payload.get("status") or "").lower() not in {"pending", "approved", "executing"}:
            continue
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _pending_approval_targets(vault_root: Path) -> set[str]:
    targets: set[str] = set()
    for payload in _active_approval_payloads(vault_root):
        spec = payload.get("action_spec") or {}
        target = str(spec.get("target_path") or "").replace("\\", "/").strip("/")
        if target:
            targets.add(target)
    return targets


def _active_metadata_field_conflict(vault_root: Path, target_path: str, fields: list[str]) -> dict[str, Any]:
    requested = set(fields)
    for payload in _active_approval_payloads(vault_root):
        spec = payload.get("action_spec") or {}
        if str(spec.get("action_type") or "") != "write_file":
            continue
        target = str(spec.get("target_path") or "").replace("\\", "/").strip("/")
        if target != target_path:
            continue
        metadata = spec.get("metadata") or {}
        if metadata.get("pass") != PASS_ID:
            continue
        existing_fields = {str(item) for item in (metadata.get("editable_fields") or [])}
        overlap = sorted(requested & existing_fields)
        if overlap:
            return {
                "conflicted": True,
                "conflict_type": "pending_target_collision",
                "target_path": target_path,
                "overlapping_fields": overlap,
                "approval_id": payload.get("approval_id") or "",
                "approval_status": payload.get("status") or "",
            }
    return {"conflicted": False, "conflict_type": "none", "target_path": target_path, "overlapping_fields": []}


def _normalize_domain(domain: str | None) -> str:
    domain = (domain or "general").strip()
    return domain or "general"


def validate_create_node_input(node_type: str, title: str, domain: str | None) -> dict[str, Any]:
    normalized_type = (node_type or "").strip()
    normalized_title = (title or "").strip()
    normalized_domain = _normalize_domain(domain)
    errors: list[str] = []

    if normalized_type not in CONTROLLED_NODE_TYPES:
        errors.append(f"unsupported node_type: {normalized_type or '<missing>'}")
    if not normalized_title or not TITLE_RE.match(normalized_title) or ".." in normalized_title:
        errors.append("title must be 1-120 characters and cannot contain path separators or traversal")
    if not DOMAIN_RE.match(normalized_domain) or ".." in normalized_domain:
        errors.append("domain must be a simple folder-safe value")

    return {
        "ok": not errors,
        "errors": errors,
        "node_type": normalized_type,
        "title": normalized_title,
        "domain": normalized_domain,
    }


def _create_node_content(
    *,
    title: str,
    node_type: str,
    domain: str,
    family: str,
    source_graph_context: dict[str, Any] | None = None,
) -> str:
    metadata: dict[str, Any] = {
        "title": title,
        "node_type": node_type,
        "node_family": family,
        "domain": domain,
        "trust_state": "raw",
        "created": _date_stamp(),
        "created_by": "studio",
        "phase10aa": True,
        "controlled_write_pass": PASS_ID,
    }
    if source_graph_context:
        metadata["source_graph_context"] = source_graph_context
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=False).strip()
    return f"---\n{frontmatter}\n---\n\n# {title}\n\n"


def _direct_mutation_denials() -> dict[str, bool]:
    return {
        "direct_write_allowed": False,
        "writes_without_approval_allowed": False,
        "canonical_graph_writeback_allowed": False,
        "persisted_graph_index_write_allowed": False,
        "node_id_writeback_allowed": False,
        "trust_promotion_allowed": False,
        "provenance_writeback_allowed": False,
        "source_pack_promotion_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_shell_connector_allowed": False,
        "credential_config_mutation_allowed": False,
    }


def _execution_boundary() -> dict[str, Any]:
    return {
        "studio_surface": "proposal_preview_and_approval_artifact_only",
        "executor_contract_required": True,
        "canonical_mutation_authority": "lower_phase_gate_backend_required",
        "approval_consumption_in_scope": False,
    }


def _approval_scope(action_type: str) -> dict[str, Any]:
    return {
        "requires_approval": True,
        "approval_artifact_action_type": action_type,
        "approval_queue_only": True,
        "direct_execution_in_preview_allowed": False,
    }


def _safe_create_summary(content: str, metadata: dict[str, Any]) -> dict[str, Any]:
    body_lines = [line for line in content.splitlines() if line.strip() and not line.startswith("---")]
    return {
        "content_stripped": False,
        "summary_type": "create_node_frontmatter_outline",
        "frontmatter_keys": sorted(metadata),
        "frontmatter_preview": {key: metadata.get(key) for key in sorted(metadata) if key != "source_graph_context"},
        "body_outline": body_lines[:3],
        "line_count": len(content.splitlines()),
    }


def _field_changes(before: dict[str, Any], after: dict[str, Any], fields: list[str]) -> dict[str, dict[str, Any]]:
    return {field: {"before": before.get(field, ""), "after": after.get(field, "")} for field in fields}


def _proposal_packet(
    *,
    operation_type: str,
    source_path: str = "",
    target_path: str = "",
    before_after_summary: dict[str, Any] | None = None,
    non_canonical_preview_edges: list[dict[str, Any]] | None = None,
    conflict_state: dict[str, Any] | None = None,
    approval_action_type: str,
) -> dict[str, Any]:
    return {
        "operation_type": operation_type,
        "source_path": source_path,
        "target_path": target_path,
        "before_after_summary": before_after_summary or {},
        "non_canonical_preview_edges": non_canonical_preview_edges or [],
        "conflict_state": conflict_state or {"conflicted": False, "conflict_type": "none"},
        "approval_scope": _approval_scope(approval_action_type),
        "execution_boundary": _execution_boundary(),
        "denied_direct_mutation_flags": _direct_mutation_denials(),
    }


def build_create_node_preview(
    vault_root: Path | str,
    node_type: str,
    title: str,
    domain: str | None = None,
    *,
    source_graph_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root)
    validation = validate_create_node_input(node_type, title, domain)
    if not validation["ok"]:
        return {
            "ok": False,
            "code": "invalid_create_node_input",
            "errors": validation["errors"],
            "pass": PASS_ID,
        }

    node_spec = CONTROLLED_NODE_TYPES[validation["node_type"]]
    target_path = build_target_path(
        node_spec.target_node_type,
        validation["title"],
        validation["domain"],
    )
    target = _safe_vault_path(vault, target_path)
    if target is None or target.suffix.lower() != ".md":
        return {
            "ok": False,
            "code": "invalid_target_path",
            "errors": ["target path must stay inside the vault and end with .md"],
            "target_path": target_path,
            "pass": PASS_ID,
        }

    pending_targets = _pending_approval_targets(vault)
    collision = target.exists()
    approval_collision = target_path in pending_targets
    metadata = {
        "pass": PASS_ID,
        "node_type": validation["node_type"],
        "node_family": node_spec.family,
        "trust_state": "raw",
        "domain": validation["domain"],
        "source_graph_context": source_graph_context or {},
    }
    content = _create_node_content(
        title=validation["title"],
        node_type=validation["node_type"],
        domain=validation["domain"],
        family=node_spec.family,
        source_graph_context=source_graph_context,
    )

    safe_diff_summary = _safe_create_summary(content, metadata)
    conflict_state = {
        "conflicted": collision or approval_collision,
        "conflict_type": "pending_target_collision" if approval_collision else ("target_exists" if collision else "none"),
        "target_path": target_path,
        "target_exists": collision,
        "pending_approval_collision": approval_collision,
    }

    return {
        "ok": not collision and not approval_collision,
        "code": "ok" if not collision and not approval_collision else "target_collision",
        "errors": [] if not collision and not approval_collision else ["target path already exists or has a pending approval"],
        "pass": PASS_ID,
        "node_type": validation["node_type"],
        "node_family": node_spec.family,
        "title": validation["title"],
        "domain": validation["domain"],
        "target_path": target_path,
        "target_exists": collision,
        "pending_approval_collision": approval_collision,
        "conflict_state": conflict_state,
        "requires_approval": True,
        "direct_write_allowed": False,
        "metadata": metadata,
        "safe_diff_summary": safe_diff_summary,
        "proposal_packet": _proposal_packet(
            operation_type="create_node",
            target_path=target_path,
            before_after_summary=safe_diff_summary,
            conflict_state=conflict_state,
            approval_action_type="create_file",
        ),
        "content": content,
    }


def queue_create_node_approval(
    vault_root: Path | str,
    node_type: str,
    title: str,
    domain: str | None = None,
    *,
    source_graph_context: dict[str, Any] | None = None,
    service: StudioService | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root)
    preview = build_create_node_preview(
        vault,
        node_type,
        title,
        domain,
        source_graph_context=source_graph_context,
    )
    if not preview.get("ok"):
        return preview | {"requires_approval": False}

    studio_service = service or StudioService(vault)
    spec = ActionSpec(
        action_type="create_file",
        target_path=preview["target_path"],
        content=preview["content"],
        metadata=preview["metadata"],
        submitted_by="studio",
        note=f"Phase 10AA approval-gated create node: {preview['title']}",
    )
    validation = studio_service.validate_action(spec)
    if not validation.valid or validation.gate_blocked:
        return {
            "ok": False,
            "code": "validation_blocked",
            "errors": validation.errors,
            "warnings": validation.warnings,
            "target_path": preview["target_path"],
            "pass": PASS_ID,
        }

    request = studio_service.queue_for_approval(spec)
    return {
        "ok": True,
        "status": "requires_approval",
        "requires_approval": True,
        "approval_id": request.approval_id,
        "approval_status": request.status,
        "target_path": preview["target_path"],
        "preview": _preview_without_content(preview),
        "pass": PASS_ID,
    }


def _preview_without_content(preview: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(preview)
    trimmed.pop("content", None)
    if isinstance(trimmed.get("safe_diff_summary"), dict):
        trimmed["safe_diff_summary"] = dict(trimmed["safe_diff_summary"]) | {"content_stripped": True}
    if isinstance(trimmed.get("proposal_packet"), dict):
        packet = dict(trimmed["proposal_packet"])
        summary = packet.get("before_after_summary")
        if isinstance(summary, dict):
            packet["before_after_summary"] = dict(summary) | {"content_stripped": True}
        trimmed["proposal_packet"] = packet
    return trimmed


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter_strict(content: str) -> dict[str, Any]:
    if not content.startswith("---"):
        return {
            "ok": True,
            "has_frontmatter": False,
            "frontmatter": {},
            "body": content,
            "raw_frontmatter": "",
        }

    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", content, re.DOTALL)
    if not match:
        return {
            "ok": False,
            "code": "malformed_frontmatter",
            "error": "frontmatter opening fence is missing a valid closing fence",
        }

    raw = match.group(1)
    body = match.group(2)
    try:
        parsed = yaml.safe_load(raw) if raw.strip() else {}
    except yaml.YAMLError as exc:
        return {
            "ok": False,
            "code": "malformed_frontmatter",
            "error": str(exc),
        }
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        return {
            "ok": False,
            "code": "malformed_frontmatter",
            "error": "frontmatter must be a mapping",
        }
    return {
        "ok": True,
        "has_frontmatter": True,
        "frontmatter": parsed,
        "body": body,
        "raw_frontmatter": raw,
    }


def _normalize_metadata_updates(fields: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in fields.items():
        clean_key = str(key).strip()
        if clean_key in {"tags", "aliases"}:
            if isinstance(value, str):
                normalized[clean_key] = [
                    item.strip()
                    for item in re.split(r"[,;\n]", value)
                    if item.strip()
                ]
            elif isinstance(value, list):
                normalized[clean_key] = [str(item).strip() for item in value if str(item).strip()]
            else:
                normalized[clean_key] = []
        else:
            normalized[clean_key] = str(value).strip() if value is not None else ""
    return normalized


def _blocked_field_reason(field: str) -> str | None:
    if field in BLOCKED_METADATA_FIELDS:
        return "restricted_fields"
    if any(field.startswith(prefix) for prefix in BLOCKED_METADATA_PREFIXES):
        return "restricted_fields"
    if field not in EDITABLE_METADATA_FIELDS:
        return "unsupported_fields"
    return None


def validate_metadata_update_fields(fields: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fields, dict) or not fields:
        return {
            "ok": False,
            "code": "missing_metadata_fields",
            "errors": ["at least one editable metadata field is required"],
        }

    restricted: list[str] = []
    unsupported: list[str] = []
    for field in fields:
        reason = _blocked_field_reason(str(field).strip())
        if reason == "restricted_fields":
            restricted.append(str(field))
        elif reason == "unsupported_fields":
            unsupported.append(str(field))

    if restricted:
        return {
            "ok": False,
            "code": "restricted_fields",
            "errors": [f"restricted metadata fields cannot be edited: {', '.join(sorted(restricted))}"],
            "restricted_fields": sorted(restricted),
        }
    if unsupported:
        return {
            "ok": False,
            "code": "unsupported_fields",
            "errors": [f"unsupported metadata fields: {', '.join(sorted(unsupported))}"],
            "unsupported_fields": sorted(unsupported),
        }

    return {
        "ok": True,
        "fields": _normalize_metadata_updates(fields),
    }


def _resolve_from_graph_index(vault_root: Path, node_id: str) -> Path | None:
    try:
        contract = build_graph_index_contract(vault_root)
    except Exception:
        return None
    graph = contract.get("graph") or {}
    for node in graph.get("nodes") or []:
        if str(node.get("id") or "") != node_id:
            continue
        properties = node.get("properties") or {}
        for key in ("path", "file_path", "source_path"):
            rel = str(properties.get(key) or "").strip()
            if not rel:
                continue
            candidate = _safe_vault_path(vault_root, rel)
            if candidate and candidate.exists() and candidate.suffix.lower() == ".md":
                return candidate
    return None


def resolve_metadata_edit_path(
    vault_root: Path | str,
    *,
    node_id: str | None = None,
    file_path: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    normalized_file_path = (file_path or "").strip()
    normalized_node_id = (node_id or "").strip()

    if normalized_file_path:
        candidate = Path(normalized_file_path)
        if candidate.is_absolute():
            try:
                candidate = candidate.resolve()
                candidate.relative_to(vault)
            except Exception:
                return {
                    "ok": False,
                    "code": "path_outside_vault",
                    "errors": ["file_path must stay inside the vault"],
                }
        else:
            safe = _safe_vault_path(vault, normalized_file_path)
            if safe is None:
                return {
                    "ok": False,
                    "code": "path_outside_vault",
                    "errors": ["file_path must stay inside the vault"],
                }
            candidate = safe
        if not candidate.exists() or candidate.suffix.lower() != ".md":
            return {
                "ok": False,
                "code": "file_not_found",
                "errors": ["metadata edit target must be an existing markdown file"],
            }
        return {
            "ok": True,
            "path": candidate,
            "target_path": _rel_path(candidate, vault),
            "node_id": normalized_node_id,
        }

    if normalized_node_id:
        resolved = resolve_node_file_path(vault, normalized_node_id) or _resolve_from_graph_index(vault, normalized_node_id)
        if resolved and resolved.exists() and resolved.suffix.lower() == ".md":
            return {
                "ok": True,
                "path": resolved.resolve(),
                "target_path": _rel_path(resolved, vault),
                "node_id": normalized_node_id,
            }

    return {
        "ok": False,
        "code": "node_not_found",
        "errors": ["node_id or file_path did not resolve to an editable markdown file"],
    }


def build_node_metadata_edit_model(
    vault_root: Path | str,
    *,
    node_id: str | None = None,
    file_path: str | None = None,
) -> dict[str, Any]:
    resolved = resolve_metadata_edit_path(vault_root, node_id=node_id, file_path=file_path)
    if not resolved.get("ok"):
        return resolved | {
            "pass": PASS_ID,
            "editable_fields": list(EDITABLE_METADATA_FIELDS),
            "read_only": False,
            "write_mode": "approval_gated",
        }

    content = _read_text(resolved["path"])
    parsed = _parse_frontmatter_strict(content)
    if not parsed.get("ok"):
        return {
            "ok": False,
            "code": parsed.get("code", "malformed_frontmatter"),
            "errors": [parsed.get("error", "frontmatter could not be parsed")],
            "target_path": resolved["target_path"],
            "node_id": resolved.get("node_id", ""),
            "pass": PASS_ID,
        }

    frontmatter = parsed["frontmatter"]
    current = {field: frontmatter.get(field, "" if field not in {"tags", "aliases"} else []) for field in EDITABLE_METADATA_FIELDS}
    return {
        "ok": True,
        "pass": PASS_ID,
        "node_id": resolved.get("node_id", ""),
        "target_path": resolved["target_path"],
        "editable_fields": list(EDITABLE_METADATA_FIELDS),
        "blocked_fields": list(BLOCKED_METADATA_FIELDS),
        "current": current,
        "has_frontmatter": parsed["has_frontmatter"],
        "write_mode": "approval_gated",
        "read_only": False,
        "possible_writes": ["metadata_update_approval_request"],
        "authority_boundary": {
            "direct_write_allowed": False,
            "trust_promotion_allowed": False,
            "provenance_writeback_allowed": False,
            "canonical_state_mutation_allowed": False,
        },
    }


def _patched_metadata_content(content: str, fields: dict[str, Any]) -> dict[str, Any]:
    parsed = _parse_frontmatter_strict(content)
    if not parsed.get("ok"):
        return {
            "ok": False,
            "code": parsed.get("code", "malformed_frontmatter"),
            "errors": [parsed.get("error", "frontmatter could not be parsed")],
        }
    frontmatter = dict(parsed["frontmatter"])
    frontmatter.update(fields)
    rendered = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=False).strip()
    return {
        "ok": True,
        "content": f"---\n{rendered}\n---\n{parsed['body']}",
        "has_frontmatter": parsed["has_frontmatter"],
        "frontmatter": frontmatter,
    }


def queue_metadata_update_approval(
    vault_root: Path | str,
    *,
    node_id: str | None = None,
    file_path: str | None = None,
    fields: dict[str, Any] | None = None,
    service: StudioService | None = None,
) -> dict[str, Any]:
    validation = validate_metadata_update_fields(fields or {})
    if not validation.get("ok"):
        return validation | {"pass": PASS_ID}

    resolved = resolve_metadata_edit_path(vault_root, node_id=node_id, file_path=file_path)
    if not resolved.get("ok"):
        return resolved | {"pass": PASS_ID}

    existing = _read_text(resolved["path"])
    parsed_existing = _parse_frontmatter_strict(existing)
    current_frontmatter = parsed_existing.get("frontmatter") if parsed_existing.get("ok") else {}
    patched = _patched_metadata_content(existing, validation["fields"])
    if not patched.get("ok"):
        return patched | {"target_path": resolved["target_path"], "pass": PASS_ID}

    sorted_fields = sorted(validation["fields"])
    conflict_state = _active_metadata_field_conflict(Path(vault_root), resolved["target_path"], sorted_fields)
    if conflict_state.get("conflicted"):
        safe_diff_summary = {
            "content_stripped": True,
            "summary_type": "metadata_field_diff",
            "target_path": resolved["target_path"],
            "field_changes": _field_changes(current_frontmatter or {}, patched.get("frontmatter") or {}, sorted_fields),
            "changed_fields": sorted_fields,
        }
        return {
            "ok": False,
            "code": "pending_target_collision",
            "errors": ["an active approval already edits at least one requested field on this target"],
            "target_path": resolved["target_path"],
            "fields": sorted_fields,
            "conflict_state": conflict_state,
            "safe_diff_summary": safe_diff_summary,
            "proposal_packet": _proposal_packet(
                operation_type="edit_metadata",
                target_path=resolved["target_path"],
                before_after_summary=safe_diff_summary,
                conflict_state=conflict_state,
                approval_action_type="write_file",
            ),
            "pass": PASS_ID,
        }

    safe_diff_summary = {
        "content_stripped": False,
        "summary_type": "metadata_field_diff",
        "target_path": resolved["target_path"],
        "field_changes": _field_changes(current_frontmatter or {}, patched.get("frontmatter") or {}, sorted_fields),
        "changed_fields": sorted_fields,
    }
    proposal_packet = _proposal_packet(
        operation_type="edit_metadata",
        target_path=resolved["target_path"],
        before_after_summary=safe_diff_summary,
        conflict_state=conflict_state,
        approval_action_type="write_file",
    )

    studio_service = service or StudioService(Path(vault_root))
    spec = ActionSpec(
        action_type="write_file",
        target_path=resolved["target_path"],
        content=patched["content"],
        metadata={
            "pass": PASS_ID,
            "node_id": resolved.get("node_id", ""),
            "target_path": resolved["target_path"],
            "editable_fields": sorted_fields,
            "write_mode": "approval_gated",
            "safe_diff_summary": safe_diff_summary | {"content_stripped": True},
            "proposal_packet": proposal_packet,
        },
        submitted_by="studio",
        note=f"Phase 10AA approval-gated metadata edit: {resolved['target_path']}",
    )
    service_validation = studio_service.validate_action(spec)
    if not service_validation.valid or service_validation.gate_blocked:
        return {
            "ok": False,
            "code": "validation_blocked",
            "errors": service_validation.errors,
            "warnings": service_validation.warnings,
            "target_path": resolved["target_path"],
            "pass": PASS_ID,
        }

    request = studio_service.queue_for_approval(spec)
    return {
        "ok": True,
        "status": "requires_approval",
        "requires_approval": True,
        "approval_id": request.approval_id,
        "approval_status": request.status,
        "target_path": resolved["target_path"],
        "fields": sorted_fields,
        "safe_diff_summary": safe_diff_summary,
        "proposal_packet": proposal_packet,
        "pass": PASS_ID,
    }


def build_controlled_node_create_edit_status(vault_root: Path | str) -> dict[str, Any]:
    vault = Path(vault_root)
    pending_targets = _pending_approval_targets(vault)
    return {
        "ok": True,
        "surface": "controlled-node-create-edit",
        "pass": PASS_ID,
        "status": "COMPLETE / APPROVAL-GATED / VERIFIED",
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "read_only": False,
        "write_mode": "approval_gated",
        "allowed_node_types": [
            {
                "node_type": spec.node_type,
                "target_node_type": spec.target_node_type,
                "family": spec.family,
                "label": spec.label,
                "target_root": _NODE_TYPE_PATH_MAP[spec.target_node_type],
            }
            for spec in CONTROLLED_NODE_TYPES.values()
        ],
        "editable_metadata_fields": list(EDITABLE_METADATA_FIELDS),
        "blocked_metadata_fields": list(BLOCKED_METADATA_FIELDS),
        "authority_boundary": {
            "direct_write_allowed": False,
            "writes_without_approval_allowed": False,
            "trust_promotion_allowed": False,
            "canonical_state_mutation_allowed": False,
            "provenance_writeback_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "host_mutation_allowed": False,
        },
        "approval_queue": {
            "pending_target_count": len(pending_targets),
            "existing_pending_targets_sample": sorted(pending_targets)[:10],
        },
        "checks": {
            "create_node_always_approval_gated": True,
            "metadata_edit_always_approval_gated": True,
            "malformed_frontmatter_blocks": True,
            "missing_frontmatter_tolerated": True,
            "restricted_metadata_fields_blocked": True,
            "path_traversal_blocked": True,
        },
    }
