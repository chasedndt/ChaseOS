"""
runtime.chaser.artifacts

Artifact manifest contracts for ChaserAgent Phase A.
Manifests are provenance references only; this module writes nothing.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from runtime.chaser.models import ArtifactRef, UNTRUSTED_TIER
from runtime.chaser.policies import build_no_authority_report


ALLOWED_ARTIFACT_TYPES = ("file", "link", "image", "log", "export", "proposal", "patch", "risk")


def _digest(value: Any) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_artifact_manifest_item(
    *,
    artifact_type: str,
    title: str = "",
    path_or_uri: str = "",
    source: str = "",
    generated: bool = True,
) -> dict[str, Any]:
    kind = str(artifact_type or "").strip().lower()
    material = {
        "artifact_type": kind,
        "title": title,
        "path_or_uri": path_or_uri,
        "source": source,
        "generated": bool(generated),
    }
    item = ArtifactRef(
        artifact_id=f"chaser-artifact-{_digest(material)[:16]}",
        artifact_type=kind,
        title=str(title or ""),
        path_or_uri=str(path_or_uri or ""),
        source=str(source or ""),
        trust_tier=UNTRUSTED_TIER,
        generated=bool(generated),
    ).to_dict()
    item["authority"] = build_no_authority_report()
    item["valid"] = validate_artifact_manifest_item(item)["ok"]
    return item


def validate_artifact_manifest_item(item: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(item, dict):
        return {"ok": False, "errors": ["artifact_not_object"]}
    if item.get("artifact_type") not in ALLOWED_ARTIFACT_TYPES:
        errors.append("artifact_type_not_allowed")
    if not item.get("artifact_id"):
        errors.append("missing_artifact_id")
    if item.get("trust_tier") != UNTRUSTED_TIER:
        errors.append("artifact_trust_tier_must_be_untrusted")
    if any(bool(value) for value in (item.get("authority") or {}).values()):
        errors.append("artifact_authority_flags_must_be_false")
    return {"ok": not errors, "errors": errors}


def build_manifest(items: list[dict[str, Any]]) -> dict[str, Any]:
    validated = [validate_artifact_manifest_item(item) for item in items if isinstance(item, dict)]
    errors = [error for report in validated for error in report["errors"]]
    return {
        "ok": not errors,
        "artifact_count": len(items),
        "items": list(items),
        "errors": errors,
        "authority": build_no_authority_report(),
    }
