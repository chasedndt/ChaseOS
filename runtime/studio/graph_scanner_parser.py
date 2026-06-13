"""Parser-backed read-only graph scanner for ChaseOS Studio.

This is the Phase 10X graph input layer. It scans Markdown/Obsidian/ChaseOS
folders, parses source structure into a deterministic graph input model, and
keeps all source/canonical writes disabled. Optional evidence writes are scoped
to the Studio graph evidence directory and require an explicit write call.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse

from runtime.studio.open_folder_readiness import build_open_folder_readiness


MODEL_VERSION = "studio.graph_scanner_parser.v1"
SURFACE_ID = "studio_graph_scanner_parser"
DEFAULT_MAX_FILES = 10000
DEFAULT_MAX_BYTES_PER_FILE = 262144
DEFAULT_MAX_NODES = 20000
DEFAULT_MAX_EDGES = 50000
MAX_SAMPLE_ITEMS = 24
EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"

IGNORED_DIR_NAMES = {
    ".codex",
    ".codex-pytest-osril",
    ".codex-tmp",
    ".codex_tmp_test",
    ".git",
    ".hermes",
    ".mypy_cache",
    ".pytest-tmp",
    ".pytest_cache",
    ".pytest_tmp",
    ".pytest_tmp_env",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_WIKILINK_RE = re.compile(r"(!)?\[\[([^\]\n]{1,500})\]\]")
_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]\n]{1,220})\]\(([^)\s]{1,700})(?:\s+[^)]*)?\)")
_TASK_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.+?)\s*$")
_BLOCK_ID_RE = re.compile(r"(?<![\w^])\^([A-Za-z0-9_-]+)\b")
_TAG_RE = re.compile(r"(?<![\w/#])#([A-Za-z][A-Za-z0-9_/-]*)")
_FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_positive_int(value: int | None, default: int) -> int:
    if value is None:
        return default
    return max(1, int(value))


def _digest(*parts: object, length: int = 18) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def _node_id(node_type: str, stable_key: str) -> str:
    return f"studio:{node_type}:{_digest(node_type, stable_key)}"


def _edge_id(relation: str, source_id: str, target_id: str, stable_key: str) -> str:
    return f"studio:edge:{_digest(relation, source_id, target_id, stable_key)}"


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _resolve_target(vault_root: str | Path, folder_path: str | Path | None) -> tuple[Path, Path]:
    vault = Path(vault_root).resolve()
    if folder_path is None:
        return vault, vault
    candidate = Path(folder_path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    return vault, candidate.resolve()


def _relative_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _append_sample(samples: list[Any], item: Any, limit: int = MAX_SAMPLE_ITEMS) -> None:
    if len(samples) < limit:
        samples.append(item)


def _slug(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "section"


def _is_external_target(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme and re.match(r"^[A-Za-z][A-Za-z0-9+.-]*$", parsed.scheme))


def _split_link_target(raw: str) -> dict[str, Any]:
    body, alias = (raw.split("|", 1) + [None])[:2] if "|" in raw else (raw, None)
    body = body.strip()
    file_part = body
    anchor = None
    block_ref = None
    if "#" in body:
        file_part, anchor = body.split("#", 1)
        file_part = file_part.strip()
        anchor = anchor.strip()
        if anchor.startswith("^"):
            block_ref = anchor[1:].strip()
    return {
        "raw": raw,
        "target": file_part.strip(),
        "anchor": anchor,
        "block_ref": block_ref,
        "alias": alias.strip() if isinstance(alias, str) and alias.strip() else None,
    }


def _parse_inline_value(value: str) -> Any:
    text = value.strip()
    if not text:
        return None
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    return text.strip("'\"")


def _parse_frontmatter(lines: list[str]) -> dict[str, Any]:
    if not lines or lines[0].strip() != "---":
        return {
            "present": False,
            "closed": False,
            "start_line": None,
            "end_line": None,
            "keys": [],
            "data": {},
            "warnings": [],
        }

    data: dict[str, Any] = {}
    keys: list[str] = []
    current_key: str | None = None
    closed_at: int | None = None
    warnings: list[str] = []
    for index, line in enumerate(lines[1:], start=2):
        stripped = line.strip()
        if stripped == "---":
            closed_at = index
            break
        match = _FRONTMATTER_KEY_RE.match(stripped)
        if match:
            current_key = match.group(1)
            if current_key not in keys:
                keys.append(current_key)
            data[current_key] = _parse_inline_value(match.group(2))
            continue
        if current_key and stripped.startswith("- "):
            existing = data.get(current_key)
            if not isinstance(existing, list):
                existing = [] if existing is None else [existing]
            existing.append(stripped[2:].strip().strip("'\""))
            data[current_key] = existing

    if closed_at is None:
        warnings.append("frontmatter-unclosed")

    aliases = data.get("aliases") or data.get("alias") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    if not isinstance(aliases, list):
        aliases = []

    return {
        "present": True,
        "closed": closed_at is not None,
        "start_line": 1,
        "end_line": closed_at,
        "keys": keys,
        "data": data,
        "aliases": [str(item) for item in aliases if str(item).strip()],
        "warnings": warnings,
    }


def _parse_markdown_text(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    frontmatter = _parse_frontmatter(lines)
    headings: list[dict[str, Any]] = []
    wikilinks: list[dict[str, Any]] = []
    markdown_links: list[dict[str, Any]] = []
    embeds: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    block_ids: list[dict[str, Any]] = []
    warnings: list[str] = list(frontmatter.get("warnings") or [])
    in_fence = False

    for line_number, line in enumerate(lines, start=1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            text_value = heading_match.group(2).strip()
            headings.append(
                {
                    "line": line_number,
                    "level": len(heading_match.group(1)),
                    "text": text_value,
                    "slug": _slug(text_value),
                }
            )

        task_match = _TASK_RE.match(line)
        if task_match:
            tasks.append(
                {
                    "line": line_number,
                    "checked": task_match.group(1).lower() == "x",
                    "text": task_match.group(2).strip(),
                }
            )

        for tag_match in _TAG_RE.finditer(line):
            tags.append(
                {
                    "line": line_number,
                    "tag": tag_match.group(1).strip(),
                }
            )

        for block_match in _BLOCK_ID_RE.finditer(line):
            block_ids.append(
                {
                    "line": line_number,
                    "block_id": block_match.group(1).strip(),
                }
            )

        for link_match in _WIKILINK_RE.finditer(line):
            split = _split_link_target(link_match.group(2).strip())
            row = {
                "line": line_number,
                "raw": split["raw"],
                "target": split["target"],
                "anchor": split["anchor"],
                "block_ref": split["block_ref"],
                "alias": split["alias"],
                "embed": bool(link_match.group(1)),
            }
            if row["embed"]:
                embeds.append(row)
            else:
                wikilinks.append(row)

        for link_match in _MARKDOWN_LINK_RE.finditer(line):
            target = link_match.group(2).strip()
            split = _split_link_target(target)
            markdown_links.append(
                {
                    "line": line_number,
                    "text": link_match.group(1).strip(),
                    "target": target,
                    "target_path": split["target"],
                    "anchor": split["anchor"],
                    "block_ref": split["block_ref"],
                    "external": _is_external_target(target),
                }
            )

    if in_fence:
        warnings.append("code-fence-unclosed")

    return {
        "line_count": len(lines),
        "frontmatter": frontmatter,
        "headings": headings,
        "wikilinks": wikilinks,
        "markdown_links": markdown_links,
        "embeds": embeds,
        "tags": tags,
        "tasks": tasks,
        "block_ids": block_ids,
        "warnings": warnings,
    }


def _discover_markdown_files(target: Path, max_files: int) -> dict[str, Any]:
    if not target.exists() or not target.is_dir():
        return {
            "files": [],
            "discovered_file_count": 0,
            "scanned_file_count": 0,
            "truncated": False,
            "errors": [],
            "ignored_dir_names": sorted(IGNORED_DIR_NAMES),
        }

    files: list[Path] = []
    discovered = 0
    truncated = False
    errors: list[str] = []
    try:
        for root, dirnames, filenames in os.walk(target):
            dirnames[:] = sorted(
                name for name in dirnames if name not in IGNORED_DIR_NAMES
            )
            for filename in sorted(filenames, key=str.lower):
                if not filename.lower().endswith(".md"):
                    continue
                discovered += 1
                if len(files) >= max_files:
                    truncated = True
                    continue
                files.append(Path(root) / filename)
    except OSError as exc:
        errors.append(str(exc))

    return {
        "files": files,
        "discovered_file_count": discovered,
        "scanned_file_count": len(files),
        "truncated": truncated,
        "errors": errors,
        "ignored_dir_names": sorted(IGNORED_DIR_NAMES),
    }


def _read_file(path: Path, max_bytes_per_file: int) -> dict[str, Any]:
    try:
        size_bytes = path.stat().st_size
        with path.open("rb") as handle:
            raw = handle.read(max_bytes_per_file + 1)
    except OSError as exc:
        return {
            "ok": False,
            "text": "",
            "size_bytes": None,
            "bytes_read": 0,
            "truncated": False,
            "error": str(exc),
        }

    truncated = len(raw) > max_bytes_per_file
    if truncated:
        raw = raw[:max_bytes_per_file]
    return {
        "ok": True,
        "text": raw.decode("utf-8", errors="replace"),
        "size_bytes": size_bytes,
        "bytes_read": len(raw),
        "truncated": truncated,
        "error": None,
    }


def _domain_for_path(path: str) -> str:
    normalized = _normalize_path(path)
    if "/" not in normalized:
        return "root"
    first = normalized.split("/", 1)[0]
    return {
        "00_HOME": "home",
        "01_PROJECTS": "projects",
        "02_KNOWLEDGE": "knowledge",
        "03_INPUTS": "inputs",
        "04_SOPS": "sops",
        "05_TEMPLATES": "templates",
        "06_AGENTS": "agents",
        "07_LOGS": "logs",
        "99_ARCHIVE": "archive",
        "runtime": "runtime",
    }.get(first, first.lower())


def _file_label(path: str) -> str:
    name = PurePosixPath(path).name
    return name[:-3] if name.lower().endswith(".md") else name


def _frontmatter_value(record: dict[str, Any], key: str) -> Any:
    return (((record.get("parsed") or {}).get("frontmatter") or {}).get("data") or {}).get(key)


def _file_node_type(path: str, record: dict[str, Any], open_folder_mode: str | None) -> str:
    normalized = _normalize_path(path)
    if normalized.startswith("07_LOGS/Build-Logs/"):
        return "build_log"
    if normalized.startswith("99_ARCHIVE/Documentation-History/"):
        return "documentation_history_note"
    if normalized.startswith("07_LOGS/Daily/"):
        return "daily_note"
    if normalized.startswith("07_LOGS/"):
        return "log_audit"
    if normalized.startswith("06_AGENTS/"):
        return "agent_control_doc"
    if normalized.startswith("00_HOME/"):
        return "home_doc"
    if normalized.startswith("01_PROJECTS/"):
        return "project_doc"
    if normalized.startswith("02_KNOWLEDGE/"):
        return "knowledge_doc"
    if normalized.startswith("03_INPUTS/"):
        return "intake_doc"
    if normalized.startswith("04_SOPS/") or normalized.startswith("05_TEMPLATES/"):
        return "sop_template_doc"
    if normalized.startswith("runtime/"):
        return "runtime_doc"
    if "decision" in normalized.lower():
        return "decision_doc"
    if normalized in {"README.md", "PROJECT_FOUNDATION.md", "ROADMAP.md"}:
        return "system_root_doc"
    if open_folder_mode == "chaseos_native_detected":
        return "chaseos_markdown_doc"
    return "markdown_note"


def _trust_state_for_record(path: str, record: dict[str, Any]) -> str:
    normalized = _normalize_path(path).lower()
    status = str(_frontmatter_value(record, "status") or "").lower()
    knowledge_class = str(_frontmatter_value(record, "knowledge_class") or "").lower()
    if normalized.startswith("99_archive/") or "archived" in status:
        return "archived"
    if "quarantine" in normalized or normalized.startswith("03_inputs/"):
        return "quarantined"
    if "generated" in knowledge_class or "generated" in normalized:
        return "generated"
    if "canonical" in knowledge_class or "canonical" in status:
        return "canonical"
    if "promoted" in status:
        return "promoted"
    if "disputed" in status:
        return "disputed"
    if "suggested" in status:
        return "suggested"
    return "raw"


def _node_family_for_type(node_type: str) -> str:
    return {
        "project_doc": "project",
        "knowledge_doc": "knowledge",
        "system_root_doc": "knowledge",
        "home_doc": "knowledge",
        "chaseos_markdown_doc": "knowledge",
        "markdown_note": "knowledge",
        "source_doc": "source",
        "intake_doc": "intake",
        "generated_artifact_doc": "generated_artifact",
        "sop_template_doc": "sop_template",
        "workflow_doc": "workflow",
        "agent_control_doc": "agent",
        "runtime_doc": "runtime",
        "decision_doc": "decision",
        "build_log": "log_audit",
        "documentation_history_note": "log_audit",
        "daily_note": "log_audit",
        "log_audit": "log_audit",
    }.get(node_type, "entity_object")


def _scan_file(path: Path, target: Path, max_bytes_per_file: int) -> dict[str, Any]:
    read = _read_file(path, max_bytes_per_file)
    record: dict[str, Any] = {
        "path": _relative_to(path, target),
        "size_bytes": read["size_bytes"],
        "bytes_read": read["bytes_read"],
        "content_truncated": read["truncated"],
        "read_error": read["error"],
        "parsed": {},
    }
    if not read["ok"]:
        return record
    record["parsed"] = _parse_markdown_text(read["text"])
    return record


def _local_link_candidates(source_path: str, target: str) -> list[str]:
    normalized_target = _normalize_path(unquote(target).split("#", 1)[0].strip())
    if not normalized_target:
        return []
    source_parent = PurePosixPath(_normalize_path(source_path)).parent
    candidates = [normalized_target]
    if str(source_parent) != ".":
        candidates.append((source_parent / normalized_target).as_posix())
    if not normalized_target.lower().endswith(".md"):
        candidates.append(f"{normalized_target}.md")
        if str(source_parent) != ".":
            candidates.append((source_parent / f"{normalized_target}.md").as_posix())
    deduped: list[str] = []
    for candidate in candidates:
        clean = _normalize_path(candidate)
        if clean not in deduped:
            deduped.append(clean)
    return deduped


def _make_node(
    *,
    node_type: str,
    stable_key: str,
    label: str,
    confidence: str,
    properties: dict[str, Any] | None = None,
    node_family: str | None = None,
) -> dict[str, Any]:
    family = node_family or _node_family_for_type(node_type)
    trust_state = (properties or {}).get("trust_state") or ("suggested" if node_type.startswith("unresolved_") else "raw")
    return {
        "id": _node_id(node_type, stable_key),
        "node_type": node_type,
        "node_family": family,
        "label": label[:180],
        "stable_key": stable_key,
        "confidence": confidence,
        "source": "parsed_markdown_graph_scanner",
        "properties": {"trust_state": trust_state, **(properties or {})},
    }


def _make_edge(
    *,
    relation: str,
    source_id: str,
    target_id: str,
    stable_key: str,
    confidence: str,
    edge_layer: str,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": _edge_id(relation, source_id, target_id, stable_key),
        "source": source_id,
        "target": target_id,
        "relation": relation,
        "edge_layer": edge_layer,
        "stable_key": stable_key,
        "confidence": confidence,
        "source_contract": SURFACE_ID,
        "properties": properties or {},
    }


def _add_node(
    nodes_by_id: dict[str, dict[str, Any]],
    node: dict[str, Any],
    *,
    max_nodes: int,
    warnings: list[str],
) -> bool:
    if node["id"] in nodes_by_id:
        return True
    if len(nodes_by_id) >= max_nodes:
        if "graph-parser-node-output-limit-reached" not in warnings:
            warnings.append("graph-parser-node-output-limit-reached")
        return False
    nodes_by_id[node["id"]] = node
    return True


def _add_edge(
    edges_by_id: dict[str, dict[str, Any]],
    edge: dict[str, Any],
    *,
    max_edges: int,
    warnings: list[str],
) -> bool:
    if edge["id"] in edges_by_id:
        return True
    if len(edges_by_id) >= max_edges:
        if "graph-parser-edge-output-limit-reached" not in warnings:
            warnings.append("graph-parser-edge-output-limit-reached")
        return False
    edges_by_id[edge["id"]] = edge
    return True


def _build_lookup(records: list[dict[str, Any]], open_folder_mode: str | None) -> dict[str, Any]:
    by_path: dict[str, str] = {}
    by_stem: dict[str, str] = {}
    by_alias: dict[str, str] = {}
    heading_by_file_slug: dict[tuple[str, str], str] = {}
    block_by_file_id: dict[tuple[str, str], str] = {}
    for record in records:
        path = _normalize_path(str(record.get("path", "")))
        if not path:
            continue
        node_id = _node_id(_file_node_type(path, record, open_folder_mode), path)
        by_path[path.lower()] = node_id
        by_stem.setdefault(PurePosixPath(path).stem.lower(), node_id)
        parsed = record.get("parsed") or {}
        frontmatter = parsed.get("frontmatter") or {}
        for alias in frontmatter.get("aliases") or []:
            by_alias.setdefault(str(alias).strip().lower(), node_id)
        for heading in parsed.get("headings") or []:
            heading_node_id = _node_id(
                "markdown_heading",
                f"{path}#heading:{heading.get('line')}:{heading.get('slug')}",
            )
            heading_by_file_slug[(path.lower(), str(heading.get("slug", "")).lower())] = heading_node_id
        for block in parsed.get("block_ids") or []:
            block_node_id = _node_id(
                "obsidian_block_marker",
                f"{path}#block:{block.get('block_id')}",
            )
            block_by_file_id[(path.lower(), str(block.get("block_id", "")).lower())] = block_node_id
    return {
        "by_path": by_path,
        "by_stem": by_stem,
        "by_alias": by_alias,
        "heading_by_file_slug": heading_by_file_slug,
        "block_by_file_id": block_by_file_id,
    }


def _resolve_file_target(source_path: str, target: str, lookup: dict[str, Any]) -> str | None:
    normalized = _normalize_path(unquote(target).strip())
    if not normalized:
        return lookup["by_path"].get(source_path.lower())
    lower = normalized.lower()
    if lower in lookup["by_path"]:
        return lookup["by_path"][lower]
    if not lower.endswith(".md") and f"{lower}.md" in lookup["by_path"]:
        return lookup["by_path"][f"{lower}.md"]
    if lower in lookup["by_alias"]:
        return lookup["by_alias"][lower]
    for candidate in _local_link_candidates(source_path, normalized):
        candidate_lower = candidate.lower()
        if candidate_lower in lookup["by_path"]:
            return lookup["by_path"][candidate_lower]
        stem = PurePosixPath(candidate).stem.lower()
        if stem in lookup["by_stem"]:
            return lookup["by_stem"][stem]
    return lookup["by_stem"].get(PurePosixPath(normalized).stem.lower())


def _resolve_link_target(source_path: str, link: dict[str, Any], lookup: dict[str, Any]) -> tuple[str | None, str]:
    file_target = str(link.get("target") or link.get("target_path") or "")
    file_id = _resolve_file_target(source_path, file_target, lookup)
    if not file_id:
        return None, "unresolved"
    target_path_lower = None
    for path_lower, node_id in lookup["by_path"].items():
        if node_id == file_id:
            target_path_lower = path_lower
            break
    if target_path_lower is None:
        target_path_lower = source_path.lower()
    block_ref = link.get("block_ref")
    if block_ref:
        block_id = lookup["block_by_file_id"].get((target_path_lower, str(block_ref).lower()))
        return (block_id or file_id), "block" if block_id else "file"
    anchor = link.get("anchor")
    if anchor:
        heading_id = lookup["heading_by_file_slug"].get((target_path_lower, _slug(str(anchor)).lower()))
        return (heading_id or file_id), "heading" if heading_id else "file"
    return file_id, "file"


def _derive_graph_input(
    records: list[dict[str, Any]],
    open_folder_mode: str | None,
    *,
    max_nodes: int,
    max_edges: int,
) -> dict[str, Any]:
    nodes_by_id: dict[str, dict[str, Any]] = {}
    edges_by_id: dict[str, dict[str, Any]] = {}
    unresolved_references: list[dict[str, Any]] = []
    warnings: list[str] = []
    lookup = _build_lookup(records, open_folder_mode)

    for record in records:
        path = _normalize_path(str(record.get("path", "")))
        if not path:
            continue
        node_type = _file_node_type(path, record, open_folder_mode)
        file_node = _make_node(
            node_type=node_type,
            node_family=_node_family_for_type(node_type),
            stable_key=path,
            label=_file_label(path),
            confidence="direct_file_scan",
            properties={
                "path": path,
                "domain": _domain_for_path(path),
                "trust_state": _trust_state_for_record(path, record),
                "size_bytes": record.get("size_bytes"),
                "bytes_read": record.get("bytes_read"),
                "truncated": bool(record.get("content_truncated")),
                "read_error": record.get("read_error"),
            },
        )
        _add_node(nodes_by_id, file_node, max_nodes=max_nodes, warnings=warnings)

    lookup = _build_lookup(records, open_folder_mode)
    for record in records:
        path = _normalize_path(str(record.get("path", "")))
        source_id = lookup["by_path"].get(path.lower())
        if not source_id:
            continue
        parsed = record.get("parsed") or {}

        for heading in parsed.get("headings") or []:
            stable_key = f"{path}#heading:{heading.get('line')}:{heading.get('slug')}"
            node = _make_node(
                node_type="markdown_heading",
                stable_key=stable_key,
                label=str(heading.get("text") or f"Heading {heading.get('line')}"),
                confidence="derived_heading",
                properties={
                    "path": path,
                    "line": heading.get("line"),
                    "level": heading.get("level"),
                    "slug": heading.get("slug"),
                    "trust_state": _trust_state_for_record(path, record),
                },
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="contains_heading",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=stable_key,
                        confidence="direct_markdown_structure",
                        edge_layer="structural",
                        properties={"line": heading.get("line"), "level": heading.get("level")},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        for tag in parsed.get("tags") or []:
            tag_text = str(tag.get("tag") or "")
            if not tag_text:
                continue
            stable_key = tag_text.lower()
            node = _make_node(
                node_type="markdown_tag",
                stable_key=stable_key,
                label=f"#{tag_text}",
                confidence="derived_tag",
                properties={"trust_state": "raw"},
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="has_tag",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=f"{path}#tag:{stable_key}:{tag.get('line')}",
                        confidence="direct_markdown_structure",
                        edge_layer="structural",
                        properties={"line": tag.get("line")},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        for task in parsed.get("tasks") or []:
            stable_key = f"{path}#task:{task.get('line')}:{task.get('text')}"
            node = _make_node(
                node_type="markdown_task",
                stable_key=stable_key,
                label=str(task.get("text") or f"Task {task.get('line')}"),
                confidence="derived_task_candidate",
                properties={
                    "path": path,
                    "line": task.get("line"),
                    "checked": bool(task.get("checked")),
                    "trust_state": _trust_state_for_record(path, record),
                },
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="contains_task",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=stable_key,
                        confidence="direct_markdown_structure",
                        edge_layer="structural",
                        properties={"line": task.get("line"), "checked": bool(task.get("checked"))},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        for block in parsed.get("block_ids") or []:
            stable_key = f"{path}#block:{block.get('block_id')}"
            node = _make_node(
                node_type="obsidian_block_marker",
                stable_key=stable_key,
                label=f"^{block.get('block_id')}",
                confidence="derived_block_marker",
                properties={
                    "path": path,
                    "line": block.get("line"),
                    "block_id": block.get("block_id"),
                    "trust_state": _trust_state_for_record(path, record),
                },
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="contains_block_marker",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=stable_key,
                        confidence="direct_markdown_structure",
                        edge_layer="structural",
                        properties={"line": block.get("line")},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        for link_kind, relation_resolved, relation_unresolved in (
            ("wikilinks", "links_to_note", "links_to_unresolved_wikilink"),
            ("embeds", "embeds_note", "embeds_unresolved_note"),
        ):
            for link in parsed.get(link_kind) or []:
                target_id, resolution_kind = _resolve_link_target(path, link, lookup)
                raw_target = str(link.get("raw") or link.get("target") or "")
                if target_id:
                    relation = "links_to_heading" if resolution_kind == "heading" else relation_resolved
                    if resolution_kind == "block":
                        relation = "links_to_block"
                    _add_edge(
                        edges_by_id,
                        _make_edge(
                            relation=relation,
                            source_id=source_id,
                            target_id=target_id,
                            stable_key=f"{path}#{link_kind}:{raw_target}:{link.get('line')}",
                            confidence=f"resolved_{link_kind[:-1]}",
                            edge_layer="explicit",
                            properties={
                                "line": link.get("line"),
                                "raw_target": raw_target,
                                "alias": link.get("alias"),
                                "anchor": link.get("anchor"),
                                "resolved": True,
                            },
                        ),
                        max_edges=max_edges,
                        warnings=warnings,
                    )
                    continue

                normalized = _normalize_path(raw_target.split("|", 1)[0].split("#", 1)[0].strip())
                node = _make_node(
                    node_type="unresolved_wikilink",
                    stable_key=normalized.lower(),
                    label=normalized or raw_target,
                    confidence="unresolved_reference",
                    properties={"raw_target": raw_target, "trust_state": "suggested"},
                )
                if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                    _add_edge(
                        edges_by_id,
                        _make_edge(
                            relation=relation_unresolved,
                            source_id=source_id,
                            target_id=node["id"],
                            stable_key=f"{path}#{link_kind}:{raw_target}:{link.get('line')}",
                            confidence="unresolved_reference",
                            edge_layer="suggested",
                            properties={"line": link.get("line"), "raw_target": raw_target, "resolved": False},
                        ),
                        max_edges=max_edges,
                        warnings=warnings,
                    )
                _append_sample(unresolved_references, {"source_path": path, "target": raw_target, "kind": link_kind})

        for link in parsed.get("markdown_links") or []:
            target = str(link.get("target") or "")
            if bool(link.get("external")):
                node = _make_node(
                    node_type="external_resource",
                    stable_key=target,
                    label=str(link.get("text") or target),
                    confidence="external_markdown_link",
                    properties={"target": target, "trust_state": "raw"},
                )
                if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                    _add_edge(
                        edges_by_id,
                        _make_edge(
                            relation="links_to_external_resource",
                            source_id=source_id,
                            target_id=node["id"],
                            stable_key=f"{path}#markdown-link:{target}:{link.get('line')}",
                            confidence="direct_markdown_link",
                            edge_layer="explicit",
                            properties={"line": link.get("line"), "text": link.get("text"), "target": target},
                        ),
                        max_edges=max_edges,
                        warnings=warnings,
                    )
                continue

            target_id, resolution_kind = _resolve_link_target(path, link, lookup)
            if target_id:
                relation = "links_to_heading" if resolution_kind == "heading" else "links_to_file"
                if resolution_kind == "block":
                    relation = "links_to_block"
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation=relation,
                        source_id=source_id,
                        target_id=target_id,
                        stable_key=f"{path}#markdown-link:{target}:{link.get('line')}",
                        confidence="resolved_markdown_link",
                        edge_layer="explicit",
                        properties={
                            "line": link.get("line"),
                            "text": link.get("text"),
                            "raw_target": target,
                            "resolved": True,
                        },
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )
                continue

            normalized = _normalize_path(str(link.get("target_path") or target))
            node = _make_node(
                node_type="unresolved_markdown_link",
                stable_key=normalized.lower(),
                label=str(link.get("text") or normalized),
                confidence="unresolved_reference",
                properties={"raw_target": target, "trust_state": "suggested"},
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="links_to_unresolved_markdown_link",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=f"{path}#markdown-link:{target}:{link.get('line')}",
                        confidence="unresolved_markdown_link",
                        edge_layer="suggested",
                        properties={"line": link.get("line"), "text": link.get("text"), "raw_target": target},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )
            _append_sample(unresolved_references, {"source_path": path, "target": target, "kind": "markdown_link"})

    nodes = list(nodes_by_id.values())
    edges = list(edges_by_id.values())
    node_type_counts: dict[str, int] = {}
    node_family_counts: dict[str, int] = {}
    trust_state_counts: dict[str, int] = {}
    relation_counts: dict[str, int] = {}
    edge_layer_counts: dict[str, int] = {}
    for node in nodes:
        node_type = str(node.get("node_type"))
        node_family = str(node.get("node_family") or "entity_object")
        trust_state = str((node.get("properties") or {}).get("trust_state") or "raw")
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
        node_family_counts[node_family] = node_family_counts.get(node_family, 0) + 1
        trust_state_counts[trust_state] = trust_state_counts.get(trust_state, 0) + 1
    for edge in edges:
        relation = str(edge.get("relation"))
        layer = str(edge.get("edge_layer") or "explicit")
        relation_counts[relation] = relation_counts.get(relation, 0) + 1
        edge_layer_counts[layer] = edge_layer_counts.get(layer, 0) + 1

    return {
        "nodes": nodes,
        "edges": edges,
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "node_family_counts": dict(sorted(node_family_counts.items())),
        "trust_state_counts": dict(sorted(trust_state_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "edge_layer_counts": dict(sorted(edge_layer_counts.items())),
        "unresolved_references": unresolved_references,
        "warnings": warnings,
    }


def _aggregate(records: list[dict[str, Any]], discovery: dict[str, Any]) -> dict[str, Any]:
    counts = {
        "frontmatter_file_count": 0,
        "files_with_unclosed_frontmatter": 0,
        "heading_count": 0,
        "wikilink_count": 0,
        "markdown_link_count": 0,
        "embed_count": 0,
        "tag_count": 0,
        "task_count": 0,
        "block_id_marker_count": 0,
        "parser_warning_count": 0,
        "read_error_count": 0,
    }
    frontmatter_keys: list[str] = []
    samples: dict[str, list[Any]] = {
        "files": [],
        "frontmatter_keys": [],
        "headings": [],
        "wikilinks": [],
        "markdown_links": [],
        "embeds": [],
        "tags": [],
        "tasks": [],
        "block_ids": [],
        "warnings": [],
    }
    for record in records:
        _append_sample(samples["files"], record.get("path"))
        if record.get("read_error"):
            counts["read_error_count"] += 1
            continue
        parsed = record.get("parsed") or {}
        frontmatter = parsed.get("frontmatter") or {}
        if frontmatter.get("present"):
            counts["frontmatter_file_count"] += 1
            if not frontmatter.get("closed"):
                counts["files_with_unclosed_frontmatter"] += 1
            for key in frontmatter.get("keys") or []:
                if key not in frontmatter_keys:
                    frontmatter_keys.append(key)
                    _append_sample(samples["frontmatter_keys"], key)
        for key, target in (
            ("headings", "heading_count"),
            ("wikilinks", "wikilink_count"),
            ("markdown_links", "markdown_link_count"),
            ("embeds", "embed_count"),
            ("tags", "tag_count"),
            ("tasks", "task_count"),
            ("block_ids", "block_id_marker_count"),
        ):
            items = parsed.get(key) or []
            counts[target] += len(items)
            for item in items:
                sample = {"path": record.get("path"), **item} if isinstance(item, dict) else item
                _append_sample(samples[key], sample)
        warnings = parsed.get("warnings") or []
        counts["parser_warning_count"] += len(warnings)
        for warning in warnings:
            _append_sample(samples["warnings"], {"path": record.get("path"), "warning": warning})

    return {
        "discovered_file_count": discovery.get("discovered_file_count", 0),
        "scanned_file_count": discovery.get("scanned_file_count", 0),
        "file_scan_truncated": discovery.get("truncated", False),
        **counts,
        "samples": samples,
    }


def build_graph_scanner_parser(
    vault_root: str | Path,
    folder_path: str | Path | None = None,
    *,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
) -> dict[str, Any]:
    """Return a read-only parser-backed graph input model."""

    file_limit = _as_positive_int(max_files, DEFAULT_MAX_FILES)
    byte_limit = _as_positive_int(max_bytes_per_file, DEFAULT_MAX_BYTES_PER_FILE)
    node_limit = _as_positive_int(max_nodes, DEFAULT_MAX_NODES)
    edge_limit = _as_positive_int(max_edges, DEFAULT_MAX_EDGES)
    vault, target = _resolve_target(vault_root, folder_path)
    open_folder = build_open_folder_readiness(vault, folder_path=folder_path)
    open_target = open_folder.get("target") or {}
    open_readiness = open_folder.get("readiness") or {}
    blockers = list(open_readiness.get("blockers", []))
    warnings = list(open_readiness.get("warnings", []))
    discovery = _discover_markdown_files(target, file_limit)
    warnings.extend(f"discovery:{item}" for item in discovery.get("errors") or [])
    records: list[dict[str, Any]] = []
    if not blockers and open_target.get("is_directory"):
        for path in discovery["files"]:
            records.append(_scan_file(path, target, byte_limit))

    if not blockers and discovery["discovered_file_count"] == 0:
        warnings.append("no-markdown-files-discovered")
    if discovery["truncated"]:
        warnings.append("graph-parser-file-scan-limit-reached")
    if any(record.get("content_truncated") for record in records):
        warnings.append("graph-parser-file-byte-limit-reached")

    aggregate = _aggregate(records, discovery)
    graph_input = _derive_graph_input(
        records,
        open_target.get("mode"),
        max_nodes=node_limit,
        max_edges=edge_limit,
    )
    warnings.extend(item for item in graph_input["warnings"] if item not in warnings)
    parser_ready = not blockers and bool(open_target.get("is_directory")) and aggregate["scanned_file_count"] > 0
    graph_input_ready = parser_ready and bool(graph_input["nodes"])
    return {
        "ok": parser_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Graph Scanner Parser",
        "phase": "Phase 10X - Parser-Backed Graph Input",
        "status": (
            "COMPLETE / READ-ONLY PARSER-BACKED GRAPH INPUT BUILT"
            if graph_input_ready
            else "BLOCKED / PARSER-BACKED GRAPH INPUT NOT READY"
        ),
        "vault_root": str(vault),
        "target": {
            "requested_path": str(folder_path) if folder_path is not None else None,
            "resolved_path": str(target),
            "exists": target.exists(),
            "is_directory": target.is_dir() if target.exists() else False,
            "open_folder_mode": open_target.get("mode"),
        },
        "scan_limits": {
            "max_files": file_limit,
            "max_bytes_per_file": byte_limit,
            "max_nodes": node_limit,
            "max_edges": edge_limit,
            "sample_limit": MAX_SAMPLE_ITEMS,
            "ignored_dir_names": discovery["ignored_dir_names"],
        },
        "open_folder_readiness": {
            "surface": open_folder.get("surface"),
            "ok": open_folder.get("ok"),
            "recommended_mode": open_readiness.get("recommended_mode"),
            "workspace_import_ready": open_readiness.get("workspace_import_ready"),
            "chaseos_native_ready": open_readiness.get("chaseos_native_ready"),
            "general_markdown_ready": open_readiness.get("general_markdown_ready"),
        },
        "parser_summary": {
            key: value
            for key, value in aggregate.items()
            if key != "samples"
        },
        "graph_summary": {
            "node_count": len(graph_input["nodes"]),
            "edge_count": len(graph_input["edges"]),
            "unresolved_reference_count": len(graph_input["unresolved_references"]),
            "node_output_truncated": "graph-parser-node-output-limit-reached" in warnings,
            "edge_output_truncated": "graph-parser-edge-output-limit-reached" in warnings,
            "node_type_counts": graph_input["node_type_counts"],
            "node_family_counts": graph_input["node_family_counts"],
            "trust_state_counts": graph_input["trust_state_counts"],
            "relation_counts": graph_input["relation_counts"],
            "edge_layer_counts": graph_input["edge_layer_counts"],
        },
        "samples": {
            **aggregate["samples"],
            "nodes": graph_input["nodes"][:MAX_SAMPLE_ITEMS],
            "edges": graph_input["edges"][:MAX_SAMPLE_ITEMS],
            "unresolved_references": graph_input["unresolved_references"][:MAX_SAMPLE_ITEMS],
        },
        "files": records,
        "graph_input": {
            "schema_version": "studio.graph_input.v1",
            "nodes": graph_input["nodes"],
            "edges": graph_input["edges"],
        },
        "readiness": {
            "graph_scanner_parser_ready": parser_ready,
            "parser_backed_graph_input_ready": graph_input_ready,
            "full_file_scanner_ready": parser_ready,
            "frontmatter_parser_ready": True,
            "markdown_structure_parser_ready": True,
            "obsidian_link_parser_ready": True,
            "deterministic_graph_input_ready": graph_input_ready,
            "persisted_graph_index_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": "phase10aa-controlled-node-create-edit" if graph_input_ready else "phase10x-graph-scanner-parser",
        },
        "graph_scanner_truth": {
            "parser_backed_graph_input_built": True,
            "full_file_scanner_built": True,
            "frontmatter_parser_built": True,
            "heading_parser_built": True,
            "tag_parser_built": True,
            "wikilink_parser_built": True,
            "markdown_link_parser_built": True,
            "embed_parser_built": True,
            "task_parser_built": True,
            "block_id_parser_built": True,
            "stable_node_identity_built": True,
            "stable_edge_identity_built": True,
            "persisted_graph_index_built": False,
            "node_id_writer_built": False,
            "canonical_graph_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "reads_file_contents": True,
            "derives_graph_in_memory": True,
            "writes_opened_folder": False,
            "writes_vault_source_files": False,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "writes_snapshot": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-graph-scanner-parser"],
        "evidence": {"written": False, "json_path": None, "markdown_path": None},
    }


def _safe_slug(value: str | None) -> str:
    source = value or datetime.now(timezone.utc).strftime("%Y-%m-%d-phase10x-graph-scanner-parser")
    safe = "".join(ch if ch.isalnum() else "-" for ch in source)
    return "-".join(part for part in safe.split("-") if part)[:96]


def _assert_inside(path: Path, root: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("graph scanner parser evidence path must stay under the evidence root") from exc


def write_graph_scanner_parser_evidence(
    vault_root: str | Path,
    *,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    """Write explicit QA evidence for the parser model under Studio evidence."""

    model = build_graph_scanner_parser(
        vault_root,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    vault = Path(vault_root).resolve()
    root = vault / (Path(evidence_root) if evidence_root else EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    _assert_inside(root, vault)
    slug = _safe_slug(evidence_slug)
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    _assert_inside(json_path, root)
    _assert_inside(markdown_path, root)
    model["evidence"] = {
        "written": True,
        "json_path": _relative_to(json_path, vault),
        "markdown_path": _relative_to(markdown_path, vault),
    }
    summary = model.get("parser_summary") or {}
    graph_summary = model.get("graph_summary") or {}
    markdown = "\n".join(
        [
            "# Studio Graph Scanner Parser Evidence",
            "",
            f"Generated: {model.get('generated_at')}",
            "Runtime: Codex",
            f"Status: {model.get('status')}",
            "",
            "## Summary",
            "",
            f"- scanned_file_count: {summary.get('scanned_file_count')}",
            f"- heading_count: {summary.get('heading_count')}",
            f"- wikilink_count: {summary.get('wikilink_count')}",
            f"- markdown_link_count: {summary.get('markdown_link_count')}",
            f"- embed_count: {summary.get('embed_count')}",
            f"- graph_nodes: {graph_summary.get('node_count')}",
            f"- graph_edges: {graph_summary.get('edge_count')}",
            f"- unresolved_references: {graph_summary.get('unresolved_reference_count')}",
            "",
            "## Boundary",
            "",
            "This evidence was written only because the operator requested explicit graph scanner parser evidence. The scanner did not write source Markdown, node ids, graph indexes, snapshots, provider/connector state, workflows, schedules, or canonical ChaseOS state.",
            "",
        ]
    )
    json_path.write_text(json.dumps(model, indent=2, default=str), encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
    return model
