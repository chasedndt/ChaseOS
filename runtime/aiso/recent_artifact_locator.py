from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Any

VIDEO_SUFFIXES = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi")
DEFAULT_SAFE_ROOTS = (
    "03_INPUTS/00_QUARANTINE",
    "runtime/acquisition/packs",
    "07_LOGS/Workflow-Proofs",
)
_BLOCKED_ROOT_TOKENS = (
    ".env",
    "credential",
    "credentials",
    "secret",
    "secrets",
    "password",
    "token",
    "tokens",
    "browser profile",
    "browser-profile",
    "user data",
    "user-data",
    "cookies",
    "keychain",
    "appdata/local/google/chrome/user data",
)


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "write_performed": False,
        "file_content_read": False,
        "hash_performed": False,
        "provider_call_performed": False,
        "provider_call_allowed": False,
        "browser_access_performed": False,
        "browser_access_allowed": False,
        "email_or_external_send_allowed": False,
        "submission_allowed": False,
        "rename_allowed": False,
        "package_write_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _parse_since(since: str | None) -> float | None:
    if not since:
        return None
    text = since.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _iso_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _is_blocked_root(path_text: str) -> bool:
    normalized = path_text.replace("\\", "/").lower()
    parts = [part.lower() for part in Path(path_text).parts]
    if any(part in {".env", ".ssh", ".gnupg"} for part in parts):
        return True
    return any(token in normalized for token in _BLOCKED_ROOT_TOKENS)


def _resolve_declared_root(vault_root: Path, root: str) -> tuple[Path | None, dict[str, str] | None]:
    raw = str(root).strip()
    if not raw:
        return None, {"root": raw, "reason": "empty_root"}
    if _is_blocked_root(raw):
        return None, {"root": raw, "reason": "credential_or_browser_profile_root_blocked"}
    candidate = Path(raw)
    resolved = candidate.resolve() if candidate.is_absolute() else (vault_root / candidate).resolve()
    if not _is_relative_to(resolved, vault_root):
        return None, {"root": raw, "reason": "root_outside_vault"}
    if _is_blocked_root(resolved.as_posix()):
        return None, {"root": raw, "reason": "credential_or_browser_profile_root_blocked"}
    if not resolved.exists():
        return None, {"root": raw, "reason": "root_missing"}
    if not resolved.is_dir():
        return None, {"root": raw, "reason": "root_not_directory"}
    return resolved, None


def _coerce_suffixes(suffixes: Iterable[str] | None) -> set[str]:
    values = list(suffixes or VIDEO_SUFFIXES)
    normalized: set[str] = set()
    for suffix in values:
        text = str(suffix).strip().lower()
        if not text:
            continue
        normalized.add(text if text.startswith(".") else f".{text}")
    return normalized or set(VIDEO_SUFFIXES)


def locate_recent_artifacts(
    *,
    vault_root: str | Path,
    roots: Iterable[str] | None = None,
    suffixes: Iterable[str] | None = None,
    limit: int = 25,
    since: str | None = None,
) -> dict[str, Any]:
    """Locate recent artifact metadata from declared vault-local roots only.

    First AISO slice: metadata-only and read-only. It does not hash, copy, open
    media content, transcribe, OCR, rename, package, browse, email, or submit.
    """

    vault = Path(vault_root).resolve()
    declared_roots = [str(root) for root in (roots or DEFAULT_SAFE_ROOTS)]
    suffix_set = _coerce_suffixes(suffixes)
    since_timestamp = _parse_since(since)
    max_items = max(0, int(limit))

    scanned_roots: list[str] = []
    blocked_roots: list[dict[str, str]] = []
    candidates: list[dict[str, Any]] = []

    for root in declared_roots:
        resolved_root, blocked = _resolve_declared_root(vault, root)
        if blocked is not None:
            blocked_roots.append(blocked)
            continue
        assert resolved_root is not None
        scanned_roots.append(resolved_root.relative_to(vault).as_posix())
        for path in resolved_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in suffix_set:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            if since_timestamp is not None and stat.st_mtime < since_timestamp:
                continue
            candidates.append(
                {
                    "relative_path": path.resolve().relative_to(vault).as_posix(),
                    "filename": path.name,
                    "suffix": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified_at_utc": _iso_utc(stat.st_mtime),
                    "rank_reasons": [
                        "declared_safe_root",
                        "suffix_match",
                        "recent_metadata_match",
                    ],
                }
            )

    candidates.sort(key=lambda item: (item["modified_at_utc"], item["relative_path"]), reverse=True)
    limited = candidates[:max_items] if max_items else []
    return {
        "ok": True,
        "surface": "aiso_recent_artifact_locator",
        "status": "read_only_first_slice",
        "vault_root": str(vault),
        "declared_roots": declared_roots,
        "scanned_roots": scanned_roots,
        "blocked_roots": blocked_roots,
        "suffixes": sorted(suffix_set),
        "limit": max_items,
        "since": since or "",
        "candidate_count_before_limit": len(candidates),
        "artifact_count": len(limited),
        "artifacts": limited,
        "authority": _authority(),
        "warnings": [
            "metadata_only_no_media_content_read",
            "media_derived_text_would_be_untrusted_data",
            "no_rename_package_email_browser_provider_or_submission_authority",
        ],
    }
