"""
studio/provenance.py — Studio Provenance Inspector

Traces any vault note or quarantine file back through its capture history by
reading its .meta.json sidecar. Cross-references with the dedup registry to
show whether the original content is known to the system.

Read-only — never modifies vault, sidecar, or dedup registry.

Outputs:
  - Provenance chain model: sidecar fields + dedup status + trust state

Governance:
  - Read-only: no vault writes
  - Sidecar data is presented as-is; injection_scan field is always surfaced
  - No content is read — only metadata
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BOUNDARY = {
    "reads_sidecar": True,
    "reads_dedup_registry": True,
    "writes_vault": False,
    "writes_sidecar": False,
    "canonical_mutation_allowed": False,
}

_SIDECAR_SUFFIX = ".meta.json"
_DEDUP_REGISTRY_PATH = ".chaseos/dedup_registry.json"

# Fields from the sidecar that constitute the provenance chain
_PROVENANCE_FIELDS = [
    "schema_version",
    "capture_id",
    "content_filename",
    "content_sha256",
    "input_class",
    "source_platform",
    "title",
    "captured_at",
    "capture_method",
    "source_url",
    "author",
    "knowledge_class",
    "injection_scan",
    "promotion_status",
    "quarantine_status",
    "origin_kind",
    "desired_output_kind",
    "domain_hint",
    "project_hint",
    "topic_hint",
    "event_date_hint",
    "original_name",
    "original_path_or_uri",
    "detected_mime",
    "route_reason",
    "source_package_status",
    "workspace_hint",
]


# ── Sidecar locator ───────────────────────────────────────────────────────────

def _find_sidecar(target: Path) -> Optional[Path]:
    """Locate .meta.json for a given file path.

    Checks adjacent sidecar first (file.md → file.meta.json), then
    file-named sidecar (file.meta.json alongside the content file).
    """
    candidate = target.with_suffix(_SIDECAR_SUFFIX)
    if candidate.exists():
        return candidate
    # Try full name + suffix
    candidate2 = target.parent / (target.name + _SIDECAR_SUFFIX)
    if candidate2.exists():
        return candidate2
    return None


def _load_dedup_registry(vault: Path) -> dict:
    reg_path = vault / _DEDUP_REGISTRY_PATH
    if not reg_path.exists():
        return {}
    try:
        return json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── Public API ────────────────────────────────────────────────────────────────

def inspect_provenance(
    vault_root: str | Path,
    file_path: str | Path,
) -> dict[str, Any]:
    """
    Return a provenance chain model for the given file.

    Locates the file's .meta.json sidecar, reads all provenance fields,
    and cross-references with the dedup registry to determine if the content
    SHA is known.

    Returns an error model if the file or its sidecar cannot be found.
    """
    vault = Path(vault_root).resolve()
    target = Path(file_path)
    if not target.is_absolute():
        target = (vault / file_path).resolve()

    if not target.exists():
        return {
            "ok": False,
            "error": f"File not found: {target}",
            "surface": "studio_provenance_inspector",
            "boundary": _BOUNDARY,
        }

    sidecar_path = _find_sidecar(target)
    if sidecar_path is None:
        return {
            "ok": False,
            "error": f"No sidecar found for: {target.name}",
            "surface": "studio_provenance_inspector",
            "file_path": str(target),
            "boundary": _BOUNDARY,
        }

    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Failed to read sidecar: {exc}",
            "surface": "studio_provenance_inspector",
            "file_path": str(target),
            "sidecar_path": str(sidecar_path),
            "boundary": _BOUNDARY,
        }

    # Extract all known provenance fields
    chain: dict[str, Any] = {}
    for field in _PROVENANCE_FIELDS:
        if field in sidecar:
            chain[field] = sidecar[field]

    # Dedup registry cross-reference
    sha = sidecar.get("content_sha256")
    dedup_status = "unknown"
    dedup_entry = None
    if sha:
        registry = _load_dedup_registry(vault)
        if sha in registry:
            dedup_status = "known"
            dedup_entry = registry[sha]
        else:
            dedup_status = "not_in_registry"

    # Trust state summary
    injection_scan = sidecar.get("injection_scan", "not-scanned")
    promotion_status = sidecar.get("promotion_status", "unknown")
    trust_state = _derive_trust_state(injection_scan, promotion_status)

    return {
        "ok": True,
        "surface": "studio_provenance_inspector",
        "file_path": str(target),
        "file_name": target.name,
        "sidecar_path": str(sidecar_path),
        "schema_version": sidecar.get("schema_version"),
        "chain": chain,
        "dedup_status": dedup_status,
        "dedup_entry": dedup_entry,
        "trust_state": trust_state,
        "injection_scan": injection_scan,
        "promotion_status": promotion_status,
        "extra_metadata": sidecar.get("extra_metadata", {}),
        "boundary": _BOUNDARY,
    }


def _derive_trust_state(injection_scan: str, promotion_status: str) -> str:
    """Derive a human-readable trust state from sidecar fields."""
    if promotion_status == "promoted":
        return "promoted"
    if injection_scan == "clean":
        return "scanned-clean"
    if injection_scan == "flagged":
        return "flagged"
    if injection_scan == "not-scanned":
        return "unscanned-quarantine"
    return "unknown"


def list_quarantine_provenance(
    vault_root: str | Path,
    *,
    input_class: Optional[str] = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    List provenance summaries for all files in the quarantine directory.

    Optionally filter by input_class. Returns up to `limit` results.
    """
    vault = Path(vault_root).resolve()
    quarantine_root = vault / "03_INPUTS" / "00_QUARANTINE"

    if not quarantine_root.exists():
        return {
            "ok": True,
            "surface": "studio_provenance_list",
            "results": [],
            "result_count": 0,
            "limit": limit,
            "input_class_filter": input_class,
            "boundary": _BOUNDARY,
        }

    results = []
    seen_sidecars: set[str] = set()

    # Walk all .meta.json sidecars in quarantine tree
    for sidecar_path in sorted(quarantine_root.rglob("*.meta.json")):
        if str(sidecar_path) in seen_sidecars:
            continue
        seen_sidecars.add(str(sidecar_path))

        try:
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        cls = sidecar.get("input_class")
        if input_class and cls != input_class:
            continue

        sha = sidecar.get("content_sha256", "")
        injection_scan = sidecar.get("injection_scan", "not-scanned")
        promotion_status = sidecar.get("promotion_status", "unknown")

        results.append({
            "file_name": sidecar.get("content_filename", sidecar_path.stem),
            "capture_id": sidecar.get("capture_id"),
            "input_class": cls,
            "source_platform": sidecar.get("source_platform"),
            "captured_at": sidecar.get("captured_at"),
            "title": sidecar.get("title"),
            "sha256": sha[:12] + "…" if sha else None,
            "trust_state": _derive_trust_state(injection_scan, promotion_status),
            "promotion_status": promotion_status,
        })

        if len(results) >= limit:
            break

    return {
        "ok": True,
        "surface": "studio_provenance_list",
        "results": results,
        "result_count": len(results),
        "limit": limit,
        "input_class_filter": input_class,
        "boundary": _BOUNDARY,
    }
