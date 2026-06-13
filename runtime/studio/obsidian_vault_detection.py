"""Phase 10F2 bounded read-only Obsidian vault detection.

This pass deepens 10F1 Open Folder compatibility readiness for Obsidian-shaped
workspaces. It reads only bounded config and Markdown samples, returns counts
and examples, and never writes `.obsidian`, vault files, approvals, graph
indexes, migration packets, or canonical state.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from runtime.studio.open_folder_compatibility_readiness import (
    COMMON_ATTACHMENT_SUFFIXES,
    IGNORED_DIR_NAMES,
    build_open_folder_compatibility_readiness,
)


MODEL_VERSION = "studio.obsidian_vault_detection.v1"
SURFACE_ID = "studio_obsidian_vault_detection"
PASS_ID = "phase10f2-obsidian-vault-detection"

MAX_DIRECTORY_VISITS = 900
MAX_FILE_VISITS = 2500
MAX_MARKDOWN_FILES_ANALYZED = 300
MAX_BYTES_PER_MARKDOWN = 65536
MAX_CONFIG_BYTES = 131072
MAX_CANVAS_FILES_ANALYZED = 80
MAX_BYTES_PER_CANVAS = 131072
MAX_SAMPLE = 40

WIKILINK_RE = re.compile(r"(!?)\[\[([^\]\n]+)\]\]")
MARKDOWN_EMBED_RE = re.compile(r"!\[[^\]\n]*\]\(([^)\n]+)\)")
BLOCK_ID_RE = re.compile(r"(?:^|\s)\^[A-Za-z0-9_-]{3,}\b", re.MULTILINE)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_target(vault_root: str | Path, folder_path: str | Path | None = None) -> tuple[Path, Path]:
    vault = Path(vault_root).resolve()
    if folder_path is None or str(folder_path).strip() == "":
        return vault, vault
    candidate = Path(folder_path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    return vault, candidate.resolve()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _safe_read_text(path: Path, *, max_bytes: int, errors: list[str], label: str) -> str:
    try:
        with path.open("rb") as handle:
            raw = handle.read(max_bytes + 1)
    except OSError as exc:
        errors.append(f"{label}: {exc}")
        return ""
    if len(raw) > max_bytes:
        errors.append(f"{label}: bounded-read-truncated")
        raw = raw[:max_bytes]
    return raw.decode("utf-8", errors="replace")


def _safe_json(path: Path, *, max_bytes: int, errors: list[str], label: str) -> Any:
    if not path.is_file():
        return None
    text = _safe_read_text(path, max_bytes=max_bytes, errors=errors, label=label)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: malformed-json:{exc.msg}")
        return None


def _obsidian_config(target: Path) -> dict[str, Any]:
    obsidian = target / ".obsidian"
    errors: list[str] = []
    community_plugins = _safe_json(
        obsidian / "community-plugins.json",
        max_bytes=MAX_CONFIG_BYTES,
        errors=errors,
        label=".obsidian/community-plugins.json",
    )
    app_config = _safe_json(
        obsidian / "app.json",
        max_bytes=MAX_CONFIG_BYTES,
        errors=errors,
        label=".obsidian/app.json",
    )
    workspace = _safe_json(
        obsidian / "workspace.json",
        max_bytes=MAX_CONFIG_BYTES,
        errors=errors,
        label=".obsidian/workspace.json",
    )
    appearance = _safe_json(
        obsidian / "appearance.json",
        max_bytes=MAX_CONFIG_BYTES,
        errors=errors,
        label=".obsidian/appearance.json",
    )

    plugin_dirs: list[str] = []
    plugins_dir = obsidian / "plugins"
    if plugins_dir.is_dir():
        try:
            plugin_dirs = sorted(
                child.name for child in plugins_dir.iterdir() if child.is_dir()
            )[:MAX_SAMPLE]
        except OSError as exc:
            errors.append(f".obsidian/plugins: {exc}")

    snippets: list[str] = []
    snippets_dir = obsidian / "snippets"
    if snippets_dir.is_dir():
        try:
            snippets = sorted(
                child.name for child in snippets_dir.iterdir() if child.is_file() and child.suffix.lower() == ".css"
            )[:MAX_SAMPLE]
        except OSError as exc:
            errors.append(f".obsidian/snippets: {exc}")

    enabled_plugins: list[str] = []
    if isinstance(community_plugins, list):
        enabled_plugins = [str(item) for item in community_plugins[:MAX_SAMPLE]]

    return {
        "has_obsidian_dir": obsidian.is_dir(),
        "has_app_json": (obsidian / "app.json").is_file(),
        "has_workspace_json": (obsidian / "workspace.json").is_file(),
        "has_appearance_json": (obsidian / "appearance.json").is_file(),
        "has_community_plugins_json": (obsidian / "community-plugins.json").is_file(),
        "plugin_dir_count": len(plugin_dirs),
        "plugin_dir_sample": plugin_dirs,
        "enabled_plugin_count": len(enabled_plugins),
        "enabled_plugin_sample": enabled_plugins,
        "snippet_count": len(snippets),
        "snippet_sample": snippets,
        "app_config_keys": sorted(app_config.keys())[:MAX_SAMPLE] if isinstance(app_config, dict) else [],
        "workspace_top_keys": sorted(workspace.keys())[:MAX_SAMPLE] if isinstance(workspace, dict) else [],
        "appearance_keys": sorted(appearance.keys())[:MAX_SAMPLE] if isinstance(appearance, dict) else [],
        "config_errors": errors,
    }


def _frontmatter_aliases(text: str) -> tuple[int, list[str], bool]:
    if not text.startswith("---"):
        return 0, [], False
    end = text.find("\n---", 3)
    if end == -1:
        return 0, [], True
    frontmatter = text[3:end]
    aliases: list[str] = []
    lines = frontmatter.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        lowered = stripped.lower()
        if lowered.startswith("aliases:") or lowered.startswith("alias:"):
            raw = stripped.split(":", 1)[1].strip()
            if raw.startswith("[") and raw.endswith("]"):
                aliases.extend(
                    item.strip().strip("\"'")
                    for item in raw[1:-1].split(",")
                    if item.strip()
                )
            elif raw:
                aliases.append(raw.strip("\"'"))
            else:
                probe = idx + 1
                while probe < len(lines):
                    child = lines[probe]
                    if not child.startswith((" ", "\t", "-")):
                        break
                    child_clean = child.strip()
                    if child_clean.startswith("-"):
                        value = child_clean[1:].strip().strip("\"'")
                        if value:
                            aliases.append(value)
                    probe += 1
        idx += 1
    return len(aliases), aliases[:MAX_SAMPLE], False


def _scan_vault_content(target: Path) -> dict[str, Any]:
    inventory = {
        "directory_visit_limit": MAX_DIRECTORY_VISITS,
        "file_visit_limit": MAX_FILE_VISITS,
        "markdown_files_analyzed_limit": MAX_MARKDOWN_FILES_ANALYZED,
        "max_bytes_per_markdown": MAX_BYTES_PER_MARKDOWN,
        "canvas_files_analyzed_limit": MAX_CANVAS_FILES_ANALYZED,
        "directories_visited": 0,
        "files_visited": 0,
        "markdown_file_count_seen": 0,
        "markdown_files_analyzed": 0,
        "canvas_file_count": 0,
        "canvas_files_analyzed": 0,
        "attachment_file_count": 0,
        "wikilink_count": 0,
        "embed_count": 0,
        "markdown_embed_count": 0,
        "alias_count": 0,
        "frontmatter_file_count": 0,
        "malformed_frontmatter_count": 0,
        "block_id_count": 0,
        "wikilink_sample": [],
        "embed_sample": [],
        "alias_sample": [],
        "markdown_sample": [],
        "canvas_sample": [],
        "attachment_sample": [],
        "errors": [],
        "truncated": False,
        "truncation_reasons": [],
    }
    if not target.exists() or not target.is_dir():
        return inventory

    queue: deque[Path] = deque([target])
    while queue:
        folder = queue.popleft()
        inventory["directories_visited"] += 1
        if inventory["directories_visited"] > MAX_DIRECTORY_VISITS:
            inventory["truncated"] = True
            inventory["truncation_reasons"].append("directory_visit_limit_reached")
            break
        try:
            children = sorted(folder.iterdir(), key=lambda item: item.name.lower())
        except OSError as exc:
            inventory["errors"].append(f"{_rel(folder, target)}: {exc}")
            continue
        for child in children:
            try:
                is_dir = child.is_dir()
                is_file = child.is_file()
            except OSError as exc:
                inventory["errors"].append(f"{_rel(child, target)}: {exc}")
                continue
            if is_dir:
                if child.name in IGNORED_DIR_NAMES:
                    continue
                queue.append(child)
                continue
            if not is_file:
                continue
            inventory["files_visited"] += 1
            if inventory["files_visited"] > MAX_FILE_VISITS:
                inventory["truncated"] = True
                inventory["truncation_reasons"].append("file_visit_limit_reached")
                queue.clear()
                break
            suffix = child.suffix.lower()
            rel = _rel(child, target)
            if suffix == ".md":
                inventory["markdown_file_count_seen"] += 1
                if inventory["markdown_files_analyzed"] >= MAX_MARKDOWN_FILES_ANALYZED:
                    inventory["truncated"] = True
                    if "markdown_analysis_limit_reached" not in inventory["truncation_reasons"]:
                        inventory["truncation_reasons"].append("markdown_analysis_limit_reached")
                    continue
                text = _safe_read_text(
                    child,
                    max_bytes=MAX_BYTES_PER_MARKDOWN,
                    errors=inventory["errors"],
                    label=rel,
                )
                inventory["markdown_files_analyzed"] += 1
                if len(inventory["markdown_sample"]) < MAX_SAMPLE:
                    inventory["markdown_sample"].append(rel)
                alias_count, aliases, malformed_fm = _frontmatter_aliases(text)
                if text.startswith("---"):
                    inventory["frontmatter_file_count"] += 1
                if malformed_fm:
                    inventory["malformed_frontmatter_count"] += 1
                inventory["alias_count"] += alias_count
                for alias in aliases:
                    if len(inventory["alias_sample"]) < MAX_SAMPLE:
                        inventory["alias_sample"].append({"file": rel, "alias": alias})
                for match in WIKILINK_RE.finditer(text):
                    is_embed = bool(match.group(1))
                    target_text = match.group(2).strip()
                    if is_embed:
                        inventory["embed_count"] += 1
                        if len(inventory["embed_sample"]) < MAX_SAMPLE:
                            inventory["embed_sample"].append({"file": rel, "target": target_text, "kind": "wikilink_embed"})
                    else:
                        inventory["wikilink_count"] += 1
                        if len(inventory["wikilink_sample"]) < MAX_SAMPLE:
                            inventory["wikilink_sample"].append({"file": rel, "target": target_text})
                for match in MARKDOWN_EMBED_RE.finditer(text):
                    inventory["embed_count"] += 1
                    inventory["markdown_embed_count"] += 1
                    if len(inventory["embed_sample"]) < MAX_SAMPLE:
                        inventory["embed_sample"].append({"file": rel, "target": match.group(1).strip(), "kind": "markdown_embed"})
                inventory["block_id_count"] += len(BLOCK_ID_RE.findall(text))
            elif suffix == ".canvas":
                inventory["canvas_file_count"] += 1
                if len(inventory["canvas_sample"]) < MAX_SAMPLE:
                    inventory["canvas_sample"].append(rel)
                if inventory["canvas_files_analyzed"] < MAX_CANVAS_FILES_ANALYZED:
                    _safe_json(child, max_bytes=MAX_BYTES_PER_CANVAS, errors=inventory["errors"], label=rel)
                    inventory["canvas_files_analyzed"] += 1
            elif suffix in COMMON_ATTACHMENT_SUFFIXES:
                inventory["attachment_file_count"] += 1
                if len(inventory["attachment_sample"]) < MAX_SAMPLE:
                    inventory["attachment_sample"].append(rel)
    return inventory


def _classification(config: dict[str, Any], content: dict[str, Any], compatibility: dict[str, Any]) -> str:
    mode = (compatibility.get("summary") or {}).get("mode")
    if mode in {"invalid_missing", "invalid_not_directory"}:
        return mode
    if config["has_obsidian_dir"]:
        if config["has_workspace_json"] or config["has_app_json"]:
            return "obsidian_vault_detected"
        return "obsidian_config_partial"
    if content["wikilink_count"] or content["embed_count"] or content["alias_count"] or content["canvas_file_count"]:
        return "markdown_with_obsidian_features"
    if content["markdown_file_count_seen"]:
        return "markdown_without_obsidian_features"
    return "not_obsidian"


def _risk_notes(config: dict[str, Any], content: dict[str, Any], classification: str) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    if classification == "obsidian_config_partial":
        notes.append({"level": "warn", "code": "partial-obsidian-config", "message": "`.obsidian` exists without the usual app/workspace config files."})
    if config["enabled_plugin_count"] or config["plugin_dir_count"]:
        notes.append({"level": "info", "code": "community-plugins-present", "message": "Community plugin state is detected for review only; Studio will not activate or edit plugins."})
    if content["canvas_file_count"]:
        notes.append({"level": "info", "code": "canvas-files-present", "message": "Canvas files are detected as compatibility inputs; canvas import remains preview-only."})
    if content["malformed_frontmatter_count"]:
        notes.append({"level": "warn", "code": "malformed-frontmatter-present", "message": "Some sampled Markdown files appear to have unterminated frontmatter."})
    if content["truncated"]:
        notes.append({"level": "warn", "code": "bounded-scan-truncated", "message": "The detector reached one or more scan limits; counts are bounded samples."})
    if content["errors"] or config["config_errors"]:
        notes.append({"level": "warn", "code": "read-errors-present", "message": "Some config or content samples could not be read cleanly."})
    if classification == "markdown_without_obsidian_features":
        notes.append({"level": "info", "code": "no-obsidian-features-detected", "message": "Markdown exists, but sampled files do not show Obsidian-specific links, aliases, embeds, or canvases."})
    return notes


def build_obsidian_vault_detection(
    vault_root: str | Path,
    folder_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return a bounded read-only Obsidian compatibility detector payload."""

    vault, target = _resolve_target(vault_root, folder_path)
    compatibility = build_open_folder_compatibility_readiness(vault, folder_path=target)
    config = _obsidian_config(target)
    content = _scan_vault_content(target)
    classification = _classification(config, content, compatibility)
    blockers: list[str] = []
    if classification == "invalid_missing":
        blockers.append("target-folder-does-not-exist")
    elif classification == "invalid_not_directory":
        blockers.append("target-path-is-not-a-directory")

    risk_notes = _risk_notes(config, content, classification)
    warnings = [note["code"] for note in risk_notes if note.get("level") == "warn"]
    ok = not blockers
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "COMPLETE / READ-ONLY / VERIFIED",
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Obsidian Vault Detection",
        "vault_root": str(vault),
        "target": {
            "requested_path": str(folder_path) if folder_path is not None else None,
            "resolved_path": str(target),
            "exists": target.exists(),
            "is_directory": target.is_dir() if target.exists() else False,
            "classification": classification,
        },
        "summary": {
            "classification": classification,
            "has_obsidian_dir": config["has_obsidian_dir"],
            "has_workspace_json": config["has_workspace_json"],
            "enabled_plugin_count": config["enabled_plugin_count"],
            "plugin_dir_count": config["plugin_dir_count"],
            "markdown_files_analyzed": content["markdown_files_analyzed"],
            "wikilink_count": content["wikilink_count"],
            "embed_count": content["embed_count"],
            "alias_count": content["alias_count"],
            "canvas_file_count": content["canvas_file_count"],
            "attachment_file_count": content["attachment_file_count"],
            "truncated": content["truncated"] or (compatibility.get("summary") or {}).get("truncated", False),
        },
        "obsidian_config": config,
        "content_signals": content,
        "compatibility_readiness": compatibility,
        "risk_notes": risk_notes,
        "readiness": {
            "ok": ok,
            "obsidian_detection_ready": ok,
            "classification": classification,
            "blockers": blockers,
            "warnings": warnings,
            "migration_readiness_state": "preview_only",
            "next_recommended_pass": "phase10f5-upgrade-plan-approval-packet",
            "approval_packet_required_for_migration": True,
            "upgrade_execution_available": False,
        },
        "performance_contract": {
            "bounded_scan": True,
            "reads_markdown_contents": True,
            "reads_markdown_contents_bounded": True,
            "max_markdown_files_analyzed": MAX_MARKDOWN_FILES_ANALYZED,
            "max_bytes_per_markdown": MAX_BYTES_PER_MARKDOWN,
            "max_config_bytes": MAX_CONFIG_BYTES,
            "does_not_build_graph": True,
            "does_not_persist_index": True,
            "returns_counts_and_samples_only": True,
        },
        "authority_boundary": {
            "read_only": True,
            "writes_selected_folder": False,
            "writes_obsidian_config": False,
            "activates_plugins": False,
            "writes_vault": False,
            "writes_approval_artifacts": False,
            "migration_writer_built": False,
            "upgrade_executor_built": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "workflow_execution_allowed": False,
            "agent_bus_task_writes_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "allowed_actions": ["inspect-obsidian-vault-detection"],
        "possible_writes": [],
        "future_passes": [
            "10F4-chaseos-bootstrap-wizard-preview",
            "10F5-upgrade-plan-approval-packet",
            "10F6-approved-upgrade-execution-proof",
        ],
    }
