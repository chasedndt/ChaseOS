"""Protected-core path guard for generated Chaser Forge extension files."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
import re


PROTECTED_CORE_PATH_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.*",
    ".claude/**",
    ".codex/**",
    ".github/**",
    ".obsidian/**",
    "secrets/**",
    "credentials/**",
    "README.md",
    "PROJECT_FOUNDATION.md",
    "ROADMAP.md",
    "CLAUDE.md",
    "HERMES.md",
    "00_HOME/**",
    "01_PROJECTS/**",
    "02_KNOWLEDGE/**",
    "03_INPUTS/**",
    "04_SOPS/**",
    "06_AGENTS/**",
    "07_LOGS/**",
    "99_ARCHIVE/**",
    "runtime/policy/**",
    "runtime/schedules/**",
    "runtime/adapters/**",
    "runtime/agent_bus/**",
    "runtime/mcp/**",
    "runtime/aor/**",
    "runtime/studio/shell/api.py",
    "runtime/studio/shell/frontend/app.js",
    "runtime/studio/shell/frontend/index.html",
    "runtime/studio/shell/frontend/styles.css",
    "runtime/studio/shell/panel_registry.py",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
)

GENERATED_EXTENSION_ROOT_PATTERNS: tuple[str, ...] = (
    "extensions/{extension_id}/",
    "runtime/forge/extensions/{extension_id}/",
)

_WINDOWS_DRIVE_RE = re.compile(r"^[a-zA-Z]:")


@dataclass(frozen=True)
class PathGuardIssue:
    path: str
    code: str
    message: str
    severity: str = "blocked"
    pattern: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {
            "path": self.path,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.pattern:
            data["pattern"] = self.pattern
        return data


def normalize_repo_path(path: str) -> tuple[str, PathGuardIssue | None]:
    raw = str(path or "").strip().replace("\\", "/")
    if not raw:
        return "", PathGuardIssue(str(path), "empty_path", "Target path is empty")
    if raw.startswith("/") or raw.startswith("//") or _WINDOWS_DRIVE_RE.match(raw):
        return raw, PathGuardIssue(raw, "absolute_path", "Generated extension paths must be repo-relative")

    parts: list[str] = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return raw, PathGuardIssue(raw, "parent_traversal", "Generated extension paths cannot traverse upward")
        parts.append(part)
    return "/".join(parts), None


def protected_pattern_for_path(repo_path: str) -> str | None:
    for pattern in PROTECTED_CORE_PATH_PATTERNS:
        if fnmatch(repo_path, pattern):
            return pattern
    return None


def is_protected_path(path: str) -> bool:
    normalized, issue = normalize_repo_path(path)
    if issue:
        return True
    return protected_pattern_for_path(normalized) is not None


def is_under_generated_extension_root(repo_path: str, extension_id: str) -> bool:
    roots = [pattern.format(extension_id=extension_id).rstrip("/") + "/" for pattern in GENERATED_EXTENSION_ROOT_PATTERNS]
    return any(repo_path == root.rstrip("/") or repo_path.startswith(root) for root in roots)


def validate_generated_extension_paths(extension_id: str, target_paths: list[str] | tuple[str, ...] | None) -> dict[str, object]:
    issues: list[PathGuardIssue] = []
    normalized_paths: list[str] = []
    for path in target_paths or []:
        normalized, issue = normalize_repo_path(path)
        if issue:
            issues.append(issue)
            continue
        normalized_paths.append(normalized)
        protected_pattern = protected_pattern_for_path(normalized)
        if protected_pattern:
            issues.append(
                PathGuardIssue(
                    normalized,
                    "protected_core_path",
                    "Generated extensions cannot write protected ChaseOS core or governance paths",
                    pattern=protected_pattern,
                )
            )
            continue
        if not is_under_generated_extension_root(normalized, extension_id):
            issues.append(
                PathGuardIssue(
                    normalized,
                    "outside_extension_root",
                    "Generated extension files must stay under the extension-owned root",
                )
            )

    return {
        "valid": not issues,
        "normalized_paths": normalized_paths,
        "issues": [issue.to_dict() for issue in issues],
        "protected_path_patterns": list(PROTECTED_CORE_PATH_PATTERNS),
        "generated_extension_roots": [
            pattern.format(extension_id=extension_id) for pattern in GENERATED_EXTENSION_ROOT_PATTERNS
        ],
        "core_mutation_allowed": False,
    }
