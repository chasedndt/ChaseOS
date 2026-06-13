"""Read-only Studio markdown scan contract.

This module gives Phase 10A a bounded scanner model for future graph/index
work. It can read limited markdown file contents to extract structural signals
such as frontmatter keys, headings, links, tags, tasks, and block-id markers.
It does not write node IDs, build a graph index, mutate files, execute
workflows, call providers/connectors, or write canonical state.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_view_browser_qa import (
    STATIC_GRAPH_BROWSER_QA_PASS,
    next_graph_view_pass_after_browser_qa,
    static_graph_browser_qa_evidence_built,
)
from runtime.studio.open_folder_readiness import build_open_folder_readiness


MODEL_VERSION = "studio.markdown_scan_contract.v1"
SURFACE_ID = "studio_markdown_scan_contract"

DEFAULT_MAX_FILES = 200
DEFAULT_MAX_BYTES_PER_FILE = 65536
MAX_SAMPLE_ITEMS = 12

_IGNORED_DIR_NAMES = {
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
_WIKILINK_RE = re.compile(r"\[\[([^\]\n]{1,240})\]\]")
_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]\n]{1,160})\]\(([^)\s]{1,500})(?:\s+[^)]*)?\)")
_TASK_RE = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s+(.+?)\s*$")
_BLOCK_ID_RE = re.compile(r"\^[A-Za-z0-9_-]+")
_TAG_RE = re.compile(r"(?<![\w/#])#([A-Za-z][A-Za-z0-9_/-]*)")
_FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*:")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_positive_int(value: int | None, default: int) -> int:
    if value is None:
        return default
    return max(1, int(value))


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
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _rel_exists(vault: Path, rel_path: str) -> bool:
    return (vault / rel_path).exists()


def _append_sample(samples: list[Any], item: Any, limit: int = MAX_SAMPLE_ITEMS) -> None:
    if len(samples) < limit:
        samples.append(item)


def _discover_markdown_files(target: Path, max_files: int) -> dict[str, Any]:
    if not target.exists() or not target.is_dir():
        return {
            "files": [],
            "discovered_file_count": 0,
            "scanned_file_count": 0,
            "truncated": False,
            "ignored_dir_names": sorted(_IGNORED_DIR_NAMES),
            "errors": [],
        }

    files: list[Path] = []
    discovered = 0
    truncated = False
    errors: list[str] = []
    try:
        for root, dirnames, filenames in os.walk(target):
            dirnames[:] = sorted(
                name for name in dirnames if name not in _IGNORED_DIR_NAMES
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
        "ignored_dir_names": sorted(_IGNORED_DIR_NAMES),
        "errors": errors,
    }


def _read_markdown_sample(path: Path, max_bytes_per_file: int) -> dict[str, Any]:
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


def _frontmatter_summary(lines: list[str]) -> dict[str, Any]:
    if not lines or lines[0].strip() != "---":
        return {
            "present": False,
            "closed": False,
            "keys": [],
            "line_count": 0,
        }

    keys: list[str] = []
    closed_at = None
    for index, line in enumerate(lines[1:80], start=1):
        if line.strip() == "---":
            closed_at = index
            break
        match = _FRONTMATTER_KEY_RE.match(line.strip())
        if match:
            key = match.group(1)
            if key not in keys:
                keys.append(key)

    return {
        "present": True,
        "closed": closed_at is not None,
        "keys": keys,
        "line_count": closed_at + 1 if closed_at is not None else min(len(lines), 80),
    }


def _scan_text(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    frontmatter = _frontmatter_summary(lines)
    headings: list[dict[str, Any]] = []
    wikilinks: list[str] = []
    markdown_links: list[dict[str, Any]] = []
    tags: list[str] = []
    task_samples: list[str] = []
    block_id_samples: list[str] = []
    heading_count = 0
    wikilink_count = 0
    markdown_link_count = 0
    tag_count = 0
    task_count = 0
    block_id_marker_count = 0

    for line_number, line in enumerate(lines, start=1):
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            heading_count += 1
            _append_sample(
                headings,
                {
                    "line": line_number,
                    "level": len(heading_match.group(1)),
                    "text": heading_match.group(2)[:160],
                },
            )
            continue

        task_match = _TASK_RE.match(line)
        if task_match:
            task_count += 1
            _append_sample(task_samples, task_match.group(1)[:160])

        for tag_match in _TAG_RE.finditer(line):
            tag_count += 1
            tag = tag_match.group(1)
            if tag not in tags and len(tags) < MAX_SAMPLE_ITEMS:
                tags.append(tag)

        for block_match in _BLOCK_ID_RE.finditer(line):
            block_id_marker_count += 1
            _append_sample(block_id_samples, block_match.group(0))

    for match in _WIKILINK_RE.finditer(text):
        wikilink_count += 1
        target = match.group(1).split("|", 1)[0].strip()
        if target and target not in wikilinks and len(wikilinks) < MAX_SAMPLE_ITEMS:
            wikilinks.append(target[:220])

    for match in _MARKDOWN_LINK_RE.finditer(text):
        markdown_link_count += 1
        _append_sample(
            markdown_links,
            {
                "text": match.group(1)[:120],
                "target": match.group(2)[:240],
                "external": bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", match.group(2))),
            },
        )

    return {
        "line_count_sampled": len(lines),
        "frontmatter": frontmatter,
        "headings": {"count": heading_count, "sample": headings},
        "wikilinks": {"count": wikilink_count, "sample": wikilinks},
        "markdown_links": {"count": markdown_link_count, "sample": markdown_links},
        "tags": {"count": tag_count, "sample": tags},
        "block_candidates": {
            "heading_count": heading_count,
            "task_count": task_count,
            "task_sample": task_samples,
            "block_id_marker_count": block_id_marker_count,
            "block_id_sample": block_id_samples,
        },
    }


def _scan_file(path: Path, target: Path, max_bytes_per_file: int) -> dict[str, Any]:
    read_result = _read_markdown_sample(path, max_bytes_per_file)
    record: dict[str, Any] = {
        "path": _relative_to(path, target),
        "size_bytes": read_result["size_bytes"],
        "bytes_read": read_result["bytes_read"],
        "truncated": read_result["truncated"],
        "read_error": read_result["error"],
    }
    if not read_result["ok"]:
        record["signals"] = {}
        return record
    record["signals"] = _scan_text(read_result["text"])
    return record


def _aggregate(file_records: list[dict[str, Any]]) -> dict[str, Any]:
    frontmatter_keys: list[str] = []
    wikilink_targets: list[str] = []
    markdown_link_targets: list[str] = []
    heading_samples: list[dict[str, Any]] = []
    error_count = 0
    frontmatter_file_count = 0
    files_with_unclosed_frontmatter = 0
    heading_count = 0
    wikilink_count = 0
    markdown_link_count = 0
    tag_count = 0
    task_count = 0
    block_id_marker_count = 0

    for record in file_records:
        if record.get("read_error"):
            error_count += 1
            continue
        signals = record.get("signals") or {}
        frontmatter = signals.get("frontmatter") or {}
        if frontmatter.get("present"):
            frontmatter_file_count += 1
            if not frontmatter.get("closed"):
                files_with_unclosed_frontmatter += 1
            for key in frontmatter.get("keys", []):
                if key not in frontmatter_keys and len(frontmatter_keys) < MAX_SAMPLE_ITEMS:
                    frontmatter_keys.append(key)

        headings = signals.get("headings") or {}
        heading_count += int(headings.get("count", 0))
        for sample in headings.get("sample", []):
            if len(heading_samples) >= MAX_SAMPLE_ITEMS:
                break
            heading_samples.append({"path": record["path"], **sample})

        wikilinks = signals.get("wikilinks") or {}
        wikilink_count += int(wikilinks.get("count", 0))
        for target in wikilinks.get("sample", []):
            if target not in wikilink_targets and len(wikilink_targets) < MAX_SAMPLE_ITEMS:
                wikilink_targets.append(target)

        markdown_links = signals.get("markdown_links") or {}
        markdown_link_count += int(markdown_links.get("count", 0))
        for link in markdown_links.get("sample", []):
            target = link.get("target")
            if target and target not in markdown_link_targets and len(markdown_link_targets) < MAX_SAMPLE_ITEMS:
                markdown_link_targets.append(target)

        tags = signals.get("tags") or {}
        tag_count += int(tags.get("count", 0))
        blocks = signals.get("block_candidates") or {}
        task_count += int(blocks.get("task_count", 0))
        block_id_marker_count += int(blocks.get("block_id_marker_count", 0))

    return {
        "file_records_with_errors": error_count,
        "frontmatter_file_count": frontmatter_file_count,
        "files_with_unclosed_frontmatter": files_with_unclosed_frontmatter,
        "frontmatter_key_sample": frontmatter_keys,
        "heading_count": heading_count,
        "heading_sample": heading_samples,
        "wikilink_count": wikilink_count,
        "wikilink_target_sample": wikilink_targets,
        "markdown_link_count": markdown_link_count,
        "markdown_link_target_sample": markdown_link_targets,
        "tag_count": tag_count,
        "task_count": task_count,
        "block_id_marker_count": block_id_marker_count,
    }


def build_markdown_scan_contract(
    vault_root: str | Path,
    folder_path: str | Path | None = None,
    *,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
) -> dict[str, Any]:
    """Return the read-only Phase 10A markdown scan contract."""

    file_limit = _as_positive_int(max_files, DEFAULT_MAX_FILES)
    byte_limit = _as_positive_int(max_bytes_per_file, DEFAULT_MAX_BYTES_PER_FILE)
    vault, target = _resolve_target(vault_root, folder_path)
    open_folder = build_open_folder_readiness(vault, folder_path=folder_path)
    open_target = open_folder.get("target") or {}
    open_readiness = open_folder.get("readiness") or {}
    blockers = list(open_readiness.get("blockers", []))
    warnings = list(open_readiness.get("warnings", []))

    discovery = _discover_markdown_files(target, file_limit)
    file_records: list[dict[str, Any]] = []
    if not blockers and open_target.get("is_directory"):
        for path in discovery["files"]:
            file_records.append(_scan_file(path, target, byte_limit))

    if not blockers and discovery["discovered_file_count"] == 0:
        warnings.append("no-markdown-files-discovered")
    if discovery["truncated"]:
        warnings.append("markdown-file-scan-limit-reached")
    if any(record.get("truncated") for record in file_records):
        warnings.append("markdown-file-byte-limit-reached")

    aggregate = _aggregate(file_records)
    scan_ready = not blockers and open_target.get("is_directory") is True
    content_scan_ready = scan_ready and discovery["discovered_file_count"] > 0
    graph_index_contract_built = _rel_exists(vault, "runtime/studio/graph_index_contract.py")
    node_inspector_contract_built = _rel_exists(vault, "runtime/studio/node_inspector_contract.py")
    graph_view_contract_built = _rel_exists(vault, "runtime/studio/graph_view_contract.py")
    static_graph_renderer_built = _rel_exists(vault, "runtime/studio/graph_view_static_renderer.py")
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(vault)
    next_pass = "phase10-studio-start-new-bootstrap-contract"
    if content_scan_ready:
        if not graph_index_contract_built:
            next_pass = "phase10-studio-graph-index-contract"
        elif not node_inspector_contract_built:
            next_pass = "phase10-studio-node-inspector-readonly"
        elif not graph_view_contract_built:
            next_pass = "phase10-studio-graph-view-readonly-contract"
        elif not static_graph_renderer_built:
            next_pass = "phase10-studio-graph-view-local-static-render"
        elif not static_graph_browser_qa_built:
            next_pass = STATIC_GRAPH_BROWSER_QA_PASS
        else:
            next_pass = next_graph_view_pass_after_browser_qa(vault)
    return {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Markdown Scan Contract",
        "phase": "Phase 10A - Studio Core Shell",
        "status": (
            "PARTIAL / READ-ONLY MARKDOWN SCAN CONTRACT BUILT / GRAPH INDEX CONTRACT BUILT / PERSISTED GRAPH ENGINE NOT BUILT"
            if graph_index_contract_built
            else "PARTIAL / READ-ONLY MARKDOWN SCAN CONTRACT BUILT / GRAPH INDEX NOT BUILT"
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
        "scan_summary": {
            "discovered_file_count": discovery["discovered_file_count"],
            "scanned_file_count": discovery["scanned_file_count"],
            "file_scan_truncated": discovery["truncated"],
            "read_error_count": aggregate["file_records_with_errors"],
            "frontmatter_file_count": aggregate["frontmatter_file_count"],
            "files_with_unclosed_frontmatter": aggregate["files_with_unclosed_frontmatter"],
            "heading_count": aggregate["heading_count"],
            "wikilink_count": aggregate["wikilink_count"],
            "markdown_link_count": aggregate["markdown_link_count"],
            "tag_count": aggregate["tag_count"],
            "task_count": aggregate["task_count"],
            "block_id_marker_count": aggregate["block_id_marker_count"],
        },
        "samples": {
            "frontmatter_keys": aggregate["frontmatter_key_sample"],
            "headings": aggregate["heading_sample"],
            "wikilink_targets": aggregate["wikilink_target_sample"],
            "markdown_link_targets": aggregate["markdown_link_target_sample"],
            "files": [record["path"] for record in file_records[:MAX_SAMPLE_ITEMS]],
        },
        "files": file_records,
        "readiness": {
            "scan_contract_ready": True,
            "folder_scan_ready": scan_ready,
            "content_scan_ready": content_scan_ready,
            "graph_index_ready": False,
            "graph_index_contract_ready": graph_index_contract_built,
            "node_inspector_contract_ready": node_inspector_contract_built,
            "graph_view_contract_ready": graph_view_contract_built,
            "static_graph_renderer_ready": static_graph_renderer_built,
            "browser_visual_qa_ready": static_graph_browser_qa_built,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": next_pass,
        },
        "scanner_truth": {
            "markdown_scan_contract_built": True,
            "bounded_file_discovery_built": True,
            "bounded_content_sampling_built": True,
            "frontmatter_key_detection_built": True,
            "heading_detection_built": True,
            "wikilink_detection_built": True,
            "markdown_link_detection_built": True,
            "block_candidate_detection_built": True,
            "graph_index_contract_built": graph_index_contract_built,
            "graph_index_built": False,
            "node_id_writer_built": False,
            "node_inspector_contract_built": node_inspector_contract_built,
            "graph_view_contract_built": graph_view_contract_built,
            "static_graph_renderer_built": static_graph_renderer_built,
            "static_graph_browser_qa_built": static_graph_browser_qa_built,
            "graph_view_built": False,
            "canonical_node_model_built": False,
            "node_inspector_built": False,
        },
        "authority": {
            "read_only": True,
            "reads_file_contents": True,
            "bounded_file_count": file_limit,
            "bounded_bytes_per_file": byte_limit,
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_settings": False,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-markdown-scan-contract"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-02-ChaseOS-phase10-studio-markdown-scan-contract.md",
        ],
    }
