"""Fingerprint-keyed cache for the (expensive) vault graph scan.

The Studio graph scan re-reads and re-parses every Markdown file in the vault on
every graph load — on a large vault this takes **minutes**, which is why the
graph "loads slow" and feels nothing like Obsidian (Obsidian caches its graph and
only reparses changed files).

This module caches the scanner output keyed by a cheap *content fingerprint*
(path + mtime + size of every ``.md`` file — stat only, no reads). When the vault
is unchanged the cached scan is returned instantly; when any file changes the
fingerprint changes and the scan is rebuilt.

Governance: derived-only. The cache lives in the Studio user state dir
(``~/.chaseos/studio/graph/scan_cache/``), never the vault. It stores only the
already-derived, read-only scan contract. No source writes, no network.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

_SKIP_DIRS = {
    ".venv", ".git", "node_modules", "__pycache__", ".chaseos",
    "dist", "build", "recovery", ".gr", ".github", ".idea", ".vscode",
}

CACHE_SCHEMA_VERSION = "chaseos.graph.scan_cache.v1"


def _enabled() -> bool:
    return os.environ.get("CHASEOS_GRAPH_SCAN_CACHE", "1") not in ("0", "false", "no")


def _cache_dir() -> Path:
    env = os.environ.get("CHASEOS_GRAPH_SCAN_CACHE_DIR")
    if env:
        return Path(env)
    return Path.home() / ".chaseos" / "studio" / "graph" / "scan_cache"


def _scan_root(vault_root: str | Path, folder_path: Any) -> Path:
    vault = Path(vault_root).resolve()
    if folder_path:
        candidate = (vault / str(folder_path)).resolve()
        if str(candidate).startswith(str(vault)) and candidate.exists():
            return candidate
    return vault


def vault_md_fingerprint(vault_root: str | Path, folder_path: Any = None) -> tuple[str, int]:
    """Cheap content fingerprint of all ``.md`` files under the scan root.

    Stat only (mtime + size) — no file contents are read. Returns
    ``(hex_digest, file_count)``. Deterministic for a given file set/state.
    """
    root = _scan_root(vault_root, folder_path)
    digest = hashlib.sha256()
    digest.update(CACHE_SCHEMA_VERSION.encode("utf-8"))
    count = 0
    entries: list[tuple[str, int, int]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for filename in filenames:
            if filename[-3:].lower() != ".md":
                continue
            path = Path(dirpath) / filename
            try:
                stat = path.stat()
            except OSError:
                continue
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                rel = path.name
            entries.append((rel, int(stat.st_mtime), int(stat.st_size)))
            count += 1
    # Sort so the digest is independent of os.walk ordering.
    for rel, mtime, size in sorted(entries):
        digest.update(f"{rel}\x1f{mtime}\x1f{size}\n".encode("utf-8"))
    return digest.hexdigest()[:40], count


def _cache_key(vault_root: str | Path, params: dict[str, Any]) -> str:
    payload = json.dumps(
        {"vault": str(Path(vault_root).resolve()), "params": params},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


# ── In-process scan memo ────────────────────────────────────────────────────
# Collapses the redundant scans that happen *within* a single graph load (and
# rapid repeat loads) into one. Unlike the file fingerprint cache, the memo does
# NOT re-stat the vault — so it stays a hit even while another agent (Hermes) is
# writing files, for a short TTL. This is what makes "the load triggers the scan
# 2-3x" collapse to one scan, and makes interactive repeat loads instant, even
# under concurrent vault writes. The trade-off is bounded staleness (<= TTL).
_MEMO: dict[str, tuple[float, dict[str, Any]]] = {}
_MEMO_MAX = 32


def _memo_ttl() -> float:
    try:
        return float(os.environ.get("CHASEOS_GRAPH_SCAN_MEMO_TTL", "30"))
    except (TypeError, ValueError):
        return 30.0


def clear_scan_memo() -> None:
    """Drop all memoized scans (e.g. for an explicit operator 'refresh')."""
    _MEMO.clear()


def memo_lookup(vault_root: str | Path, params: dict[str, Any]) -> dict[str, Any] | None:
    """Return a memoized scan for (vault, params) within the TTL, else None.

    Does not touch the filesystem — immune to concurrent vault writes for the
    TTL window. Fail-open.
    """
    if not _enabled():
        return None
    ttl = _memo_ttl()
    if ttl <= 0:
        return None
    key = _cache_key(vault_root, params)
    entry = _MEMO.get(key)
    if entry is None:
        return None
    ts, result = entry
    if (time.monotonic() - ts) > ttl:
        _MEMO.pop(key, None)
        return None
    out = dict(result)
    out["_scan_cache"] = {"hit": True, "source": "memo"}
    return out


def memo_store(vault_root: str | Path, params: dict[str, Any], result: dict[str, Any], *, only_if_nodes: bool = True) -> None:
    """Memoize a fresh scan result for (vault, params). Fail-open."""
    if not _enabled():
        return
    if only_if_nodes and not ((result.get("graph_input") or {}).get("nodes")):
        return
    key = _cache_key(vault_root, params)
    _MEMO[key] = (time.monotonic(), result)
    if len(_MEMO) > _MEMO_MAX:
        oldest_key = min(_MEMO.items(), key=lambda kv: kv[1][0])[0]
        _MEMO.pop(oldest_key, None)


# ── Persistent incremental parse store ──────────────────────────────────────
# Caches each file's parse record keyed by (relpath, mtime, size). On a scan,
# unchanged files reuse their cached record and only *changed* files are
# re-read/re-parsed. This is what makes even a COLD load fast — and fast under
# concurrent writes (Hermes): only the files Hermes touched get reparsed, not
# the whole vault.
PARSE_INDEX_SCHEMA = "chaseos.graph.parse_index.v1"
PARSE_INDEX_MAX_FILES = 30000


def _parse_index_dir() -> Path:
    env = os.environ.get("CHASEOS_GRAPH_PARSE_INDEX_DIR")
    if env:
        return Path(env)
    return Path.home() / ".chaseos" / "studio" / "graph" / "parse_index"


def _parse_index_path(vault_root: str | Path, folder_path: Any, byte_limit: Any) -> Path:
    key_src = json.dumps(
        {"vault": str(Path(vault_root).resolve()), "folder": str(folder_path) if folder_path else None, "byte_limit": byte_limit},
        sort_keys=True,
        default=str,
    )
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]
    return _parse_index_dir() / f"{key}.json"


def _load_parse_index(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if payload.get("schema_version") != PARSE_INDEX_SCHEMA:
        return {}
    files = payload.get("files")
    return files if isinstance(files, dict) else {}


def _save_parse_index(path: Path, files: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps({"schema_version": PARSE_INDEX_SCHEMA, "files": files}, default=str),
            encoding="utf-8",
        )
        os.replace(tmp, path)
    except Exception:
        pass


def _rel_posix(path: Path, target: Path) -> str:
    try:
        return path.relative_to(target).as_posix()
    except ValueError:
        return path.name


def incremental_parse(
    files: list[Path],
    target: str | Path,
    byte_limit: int,
    parse_one,
    *,
    vault_root: str | Path,
    folder_path: Any = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Parse ``files`` reusing cached records for unchanged files.

    ``parse_one(path)`` must read+parse one file and return its record. Returns
    ``(records, stats)`` where ``stats`` is ``{reused, reparsed, total}``.
    Fail-open: any error falls back to a full parse of every file.
    """
    target_path = Path(target)
    total = len(files)
    if not _enabled() or total > PARSE_INDEX_MAX_FILES:
        records = [parse_one(p) for p in files]
        return records, {"reused": 0, "reparsed": total, "total": total}

    try:
        index_path = _parse_index_path(vault_root, folder_path, byte_limit)
        index = _load_parse_index(index_path)
    except Exception:
        records = [parse_one(p) for p in files]
        return records, {"reused": 0, "reparsed": total, "total": total}

    records: list[dict[str, Any]] = []
    new_index: dict[str, Any] = {}
    reused = 0
    reparsed = 0
    for path in files:
        try:
            stat = path.stat()
            mtime = int(stat.st_mtime)
            size = int(stat.st_size)
        except OSError:
            mtime = -1
            size = -1
        rel = _rel_posix(path, target_path)
        cached = index.get(rel)
        if (
            isinstance(cached, dict)
            and cached.get("mtime") == mtime
            and cached.get("size") == size
            and cached.get("byte_limit") == byte_limit
            and isinstance(cached.get("record"), dict)
        ):
            record = cached["record"]
            reused += 1
        else:
            record = parse_one(path)
            reparsed += 1
        records.append(record)
        new_index[rel] = {"mtime": mtime, "size": size, "byte_limit": byte_limit, "record": record}

    if reparsed or set(new_index) != set(index):
        _save_parse_index(index_path, new_index)
    return records, {"reused": reused, "reparsed": reparsed, "total": total}


def scanner_cache_lookup(
    vault_root: str | Path, params: dict[str, Any]
) -> tuple[dict[str, Any] | None, str, str]:
    """Return ``(cached_contract_or_None, fingerprint, cache_key)``.

    A hit requires the stored fingerprint to match the current vault fingerprint.
    Fail-open: any error returns a miss.
    """
    fingerprint, _count = vault_md_fingerprint(vault_root, params.get("folder_path"))
    key = _cache_key(vault_root, params)
    if not _enabled():
        return None, fingerprint, key
    path = _cache_dir() / f"{key}.json"
    if not path.exists():
        return None, fingerprint, key
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, fingerprint, key
    if payload.get("schema_version") != CACHE_SCHEMA_VERSION:
        return None, fingerprint, key
    if payload.get("fingerprint") != fingerprint:
        return None, fingerprint, key
    contract = payload.get("contract")
    if not isinstance(contract, dict):
        return None, fingerprint, key
    result = dict(contract)
    result["_scan_cache"] = {"hit": True, "fingerprint": fingerprint}
    return result, fingerprint, key


def scanner_cache_store(
    cache_key: str,
    fingerprint: str,
    contract: dict[str, Any],
    *,
    only_if_nodes: bool = True,
) -> bool:
    """Persist ``contract`` under ``cache_key``. Fail-open; returns True on write."""
    if not _enabled():
        return False
    if only_if_nodes:
        nodes = ((contract.get("graph_input") or {}).get("nodes")) or []
        if not nodes:
            return False  # don't cache empty/blocked scans
    try:
        directory = _cache_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{cache_key}.json"
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                {
                    "schema_version": CACHE_SCHEMA_VERSION,
                    "fingerprint": fingerprint,
                    "contract": contract,
                },
                default=str,
            ),
            encoding="utf-8",
        )
        os.replace(tmp, path)
        return True
    except Exception:
        return False
