"""Lightweight ChaseOS Core secret/path scan.

This is a fallback scanner for private baseline readiness when tools such as
gitleaks or trufflehog are not available. It scans Git-candidate files only:
tracked, staged, and untracked files that are not ignored by `.gitignore`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Iterable


SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_pat": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b"),
    "openai_key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "anthropic_key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "discord_webhook": re.compile(r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9._-]+"),
    "private_key_header": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "generic_assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|client[_-]?secret)\b\s*[:=]\s*['\"]?[^'\"\s]{10,}"
    ),
}

PATH_PATTERNS = {
    "windows_user_path": re.compile(r"C:\\Users\\[^\\\s]+\\"),
    "wsl_user_path": re.compile("/mnt/c/" + r"Users/[^/\s]+/"),
    "home_path": re.compile("/" + r"home/[^/\s]+/"),
    "private_vault_name": re.compile("chaseos" + r"_Obsidian", re.IGNORECASE),
    "raw_transcript_path": re.compile(
        "03_INPUTS" + r"[\\/](?:Transcript-Raw|Personal-Context-Intake)",
        re.IGNORECASE,
    ),
    "db_file_reference": re.compile(r"\b[\w.-]+\.(?:db|sqlite|sqlite3|duckdb)\b", re.IGNORECASE),
}

TEXT_EXTENSIONS = {
    ".bat",
    ".cfg",
    ".css",
    ".csv",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".ps1",
    ".py",
    ".rst",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

MAX_FILE_BYTES = 2_000_000


def git_candidate_files(root: Path) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    names = [name for name in proc.stdout.decode("utf-8", errors="replace").split("\0") if name]
    return [root / name for name in names]


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return path.name in {".gitignore", "README", "LICENSE"}


def iter_matches(patterns: dict[str, re.Pattern[str]], text: str) -> Iterable[tuple[str, int, str]]:
    for label, pattern in patterns.items():
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            yield label, line_no, match.group(0)[:160]


def scan(root: Path) -> dict[str, object]:
    files = git_candidate_files(root)
    secret_findings: list[dict[str, object]] = []
    path_findings: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []

    for path in files:
        rel = path.relative_to(root).as_posix()
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            skipped.append({"path": rel, "reason": f"stat_failed:{exc.__class__.__name__}"})
            continue
        if size > MAX_FILE_BYTES:
            skipped.append({"path": rel, "reason": f"too_large:{size}"})
            continue
        if not is_probably_text(path):
            skipped.append({"path": rel, "reason": "non_text_extension"})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            skipped.append({"path": rel, "reason": f"read_failed:{exc.__class__.__name__}"})
            continue

        for label, line_no, sample in iter_matches(SECRET_PATTERNS, text):
            secret_findings.append({"path": rel, "line": line_no, "type": label, "sample": sample})
        for label, line_no, sample in iter_matches(PATH_PATTERNS, text):
            path_findings.append({"path": rel, "line": line_no, "type": label, "sample": sample})

    return {
        "scanner": "security/core_safety_scan.py",
        "scope": "git_candidates_from_git_ls_files_cached_others_exclude_standard",
        "root": str(root),
        "files_considered": len(files),
        "files_skipped": len(skipped),
        "secret_findings": len(secret_findings),
        "path_findings": len(path_findings),
        "secret_counts_by_type": dict(Counter(item["type"] for item in secret_findings)),
        "path_counts_by_type": dict(Counter(item["type"] for item in path_findings)),
        "secret_counts_by_top_dir": dict(Counter(str(item["path"]).split("/", 1)[0] for item in secret_findings)),
        "path_counts_by_top_dir": dict(Counter(str(item["path"]).split("/", 1)[0] for item in path_findings)),
        "secret_findings_sample": secret_findings[:100],
        "path_findings_sample": path_findings[:100],
        "skipped_sample": skipped[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Git-candidate files for secret/path indicators.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = scan(root)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"scanner: {result['scanner']}")
        print(f"files_considered: {result['files_considered']}")
        print(f"files_skipped: {result['files_skipped']}")
        print(f"secret_findings: {result['secret_findings']}")
        print(f"path_findings: {result['path_findings']}")
        print(f"secret_counts_by_type: {result['secret_counts_by_type']}")
        print(f"path_counts_by_type: {result['path_counts_by_type']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
