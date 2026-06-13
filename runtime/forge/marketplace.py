"""Local marketplace package/import foundation for Chaser Forge."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from runtime.forge.registry import (
    BLOCKED_AUTHORITY,
    SANDBOX_APPROVAL_RELATIVE_DIR,
    build_extension_registry,
    build_sandbox_install_approval,
    build_sandbox_registry_write_execution,
)
from runtime.forge.validator import validate_manifest


FORGE_MARKETPLACE_PACKAGE_RECORD_TYPE = "forge_marketplace_template_package"
FORGE_MARKETPLACE_PACKAGE_SCHEMA_VERSION = "forge.marketplace_package.v1"
FORGE_MARKETPLACE_SURFACE_ID = "chaser_forge_marketplace_import_export_foundation"
FORGE_MARKETPLACE_EXPORT_API_METHOD = "get_chaser_forge_marketplace_export_package"
FORGE_MARKETPLACE_WRITE_API_METHOD = "write_chaser_forge_marketplace_export_package"
FORGE_MARKETPLACE_IMPORT_API_METHOD = "get_chaser_forge_marketplace_import_preview"
FORGE_MARKETPLACE_PACKAGE_RELATIVE_DIR = Path("07_LOGS") / "Workflow-Proofs" / "Forge-Marketplace-Packages"
FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE = "forge_marketplace_import_sandbox_approval_request"
FORGE_MARKETPLACE_IMPORT_APPROVAL_SCHEMA_VERSION = "forge.marketplace_import_approval.v1"
FORGE_MARKETPLACE_IMPORT_APPROVAL_SURFACE_ID = "chaser_forge_marketplace_import_sandbox_approval"
FORGE_MARKETPLACE_IMPORT_APPROVAL_API_METHOD = "request_chaser_forge_marketplace_import_sandbox_approval"
FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE = "forge.marketplace_import.sandbox_review"
FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR = (
    Path("07_LOGS") / "Agent-Activity" / "_forge_marketplace_import_approvals"
)
FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_SCHEMA_VERSION = "forge.marketplace_import_sandbox_request.v1"
FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_SURFACE_ID = "chaser_forge_marketplace_import_sandbox_request"
FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_API_METHOD = "request_chaser_forge_marketplace_import_sandbox_request"
FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_PREVIEW_API_METHOD = "get_chaser_forge_marketplace_import_sandbox_request"
FORGE_MARKETPLACE_CATALOG_RECORD_TYPE = "forge_marketplace_catalog"
FORGE_MARKETPLACE_CATALOG_SCHEMA_VERSION = "forge.marketplace_catalog.v1"
FORGE_MARKETPLACE_CATALOG_SURFACE_ID = "chaser_forge_marketplace_catalog"
FORGE_MARKETPLACE_CATALOG_API_METHOD = "get_chaser_forge_marketplace_catalog"
FORGE_MARKETPLACE_PUBLISH_RECORD_TYPE = "forge_marketplace_catalog_listing"
FORGE_MARKETPLACE_PUBLISH_SCHEMA_VERSION = "forge.marketplace_publish.v1"
FORGE_MARKETPLACE_PUBLISH_SURFACE_ID = "chaser_forge_marketplace_publish"
FORGE_MARKETPLACE_PUBLISH_PREVIEW_API_METHOD = "get_chaser_forge_marketplace_publish_preview"
FORGE_MARKETPLACE_PUBLISH_API_METHOD = "publish_chaser_forge_marketplace_package"
FORGE_MARKETPLACE_INSTALL_SCHEMA_VERSION = "forge.marketplace_install_executor.v1"
FORGE_MARKETPLACE_INSTALL_SURFACE_ID = "chaser_forge_marketplace_install_executor"
FORGE_MARKETPLACE_INSTALL_API_METHOD = "execute_chaser_forge_marketplace_install"
FORGE_MARKETPLACE_LOCAL_LIBRARY_SCHEMA_VERSION = "forge.marketplace_local_library.v1"
FORGE_MARKETPLACE_LOCAL_LIBRARY_SURFACE_ID = "chaser_forge_marketplace_local_library"
FORGE_MARKETPLACE_LOCAL_LIBRARY_API_METHOD = "get_chaser_forge_marketplace_local_library"
FORGE_MARKETPLACE_REMOTE_INDEX_RECORD_TYPE = "forge_marketplace_remote_index"
FORGE_MARKETPLACE_REMOTE_LISTING_RECORD_TYPE = "forge_marketplace_remote_listing"
FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION = "forge.marketplace_remote_index.v1"
FORGE_MARKETPLACE_REMOTE_LISTING_SCHEMA_VERSION = "forge.marketplace_remote_listing.v1"
FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID = "chaser_forge_marketplace_remote_distribution"
FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_API_METHOD = "get_chaser_forge_marketplace_remote_distribution"
FORGE_MARKETPLACE_REMOTE_INDEX_WRITE_API_METHOD = "write_chaser_forge_marketplace_remote_index"
FORGE_MARKETPLACE_REMOTE_INGEST_API_METHOD = "ingest_chaser_forge_marketplace_remote_listing"
FORGE_MARKETPLACE_REMOTE_INDEX_RELATIVE_DIR = (
    Path("07_LOGS") / "Workflow-Proofs" / "Forge-Marketplace-Remote-Indexes"
)
FORGE_MARKETPLACE_HOSTED_BUNDLE_RECORD_TYPE = "forge_marketplace_hosted_export_bundle"
FORGE_MARKETPLACE_HOSTED_BUNDLE_SCHEMA_VERSION = "forge.marketplace_hosted_bundle.v1"
FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID = "chaser_forge_marketplace_hosted_export_bundle"
FORGE_MARKETPLACE_HOSTED_BUNDLE_API_METHOD = "get_chaser_forge_marketplace_hosted_export_bundle"
FORGE_MARKETPLACE_HOSTED_BUNDLE_WRITE_API_METHOD = "write_chaser_forge_marketplace_hosted_export_bundle"
FORGE_MARKETPLACE_HOSTED_BUNDLE_RELATIVE_DIR = (
    Path("07_LOGS") / "Workflow-Proofs" / "Forge-Marketplace-Hosted-Bundles"
)
FORGE_MARKETPLACE_STATIC_PUBLICATION_RECORD_TYPE = "forge_marketplace_static_host_publication"
FORGE_MARKETPLACE_STATIC_PUBLICATION_SCHEMA_VERSION = "forge.marketplace_static_host_publication.v1"
FORGE_MARKETPLACE_STATIC_PUBLICATION_SURFACE_ID = "chaser_forge_marketplace_static_host_publication"
FORGE_MARKETPLACE_STATIC_PUBLICATION_API_METHOD = "get_chaser_forge_marketplace_static_host_publication"
FORGE_MARKETPLACE_STATIC_PUBLICATION_WRITE_API_METHOD = "write_chaser_forge_marketplace_static_host_publication"
FORGE_MARKETPLACE_STATIC_PUBLICATION_RELATIVE_DIR = (
    Path("07_LOGS") / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Publications"
)
FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RECORD_TYPE = "forge_marketplace_static_host_upload_handoff"
FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SCHEMA_VERSION = "forge.marketplace_static_host_upload_handoff.v1"
FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SURFACE_ID = "chaser_forge_marketplace_static_host_upload_handoff"
FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_API_METHOD = "get_chaser_forge_marketplace_static_host_upload_handoff"
FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_WRITE_API_METHOD = "write_chaser_forge_marketplace_static_host_upload_handoff"
FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RELATIVE_DIR = (
    Path("07_LOGS") / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Upload-Handoffs"
)
FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_RECORD_TYPE = "forge_marketplace_static_host_upload_receipt"
FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SCHEMA_VERSION = "forge.marketplace_static_host_upload_receipt.v1"
FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SURFACE_ID = "chaser_forge_marketplace_static_host_upload_receipt"
FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_API_METHOD = "get_chaser_forge_marketplace_static_host_upload_receipt"
FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_WRITE_API_METHOD = "write_chaser_forge_marketplace_static_host_upload_receipt"
FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_RELATIVE_DIR = (
    Path("07_LOGS") / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Upload-Receipts"
)
FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_RECORD_TYPE = (
    "forge_marketplace_published_static_index_registration"
)
FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SCHEMA_VERSION = (
    "forge.marketplace_published_static_index_registration.v1"
)
FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SURFACE_ID = (
    "chaser_forge_marketplace_published_static_index_registration"
)
FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_API_METHOD = (
    "get_chaser_forge_marketplace_published_static_index_registration"
)
FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_WRITE_API_METHOD = (
    "write_chaser_forge_marketplace_published_static_index_registration"
)
FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_RELATIVE_DIR = (
    Path("07_LOGS") / "Workflow-Proofs" / "Forge-Marketplace-Published-Static-Index-Registrations"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_RECORD_TYPE = "forge_marketplace_live_index_input_readiness"
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SCHEMA_VERSION = (
    "forge.marketplace_live_index_input_readiness.v1"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID = (
    "chaser_forge_marketplace_live_index_input_readiness"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_API_METHOD = (
    "get_chaser_forge_marketplace_live_index_input_readiness"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_RECORD_TYPE = "forge_marketplace_live_index_input_prefill"
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SCHEMA_VERSION = (
    "forge.marketplace_live_index_input_prefill.v1"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID = (
    "chaser_forge_marketplace_live_index_input_prefill"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_API_METHOD = (
    "get_chaser_forge_marketplace_live_index_input_prefill"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_WRITE_API_METHOD = (
    "write_chaser_forge_marketplace_live_index_input_prefill"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_RELATIVE_DIR = (
    Path("07_LOGS") / "Operator-Briefs" / "Chaser-Forge-Live-Index-Input-Prefills"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PACKET_TEMPLATE_RELATIVE_PATH = (
    Path("07_LOGS")
    / "Operator-Briefs"
    / "2026-05-24-chaser-forge-live-index-json-input-packet-template.json"
)
FORGE_MARKETPLACE_LIVE_INDEX_INPUT_HANDOVER_RELATIVE_PATH = (
    Path("07_LOGS")
    / "Operator-Briefs"
    / "2026-05-24-chaser-forge-live-index-json-input-handover.md"
)
FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES = (
    "README.md",
    "checksums.json",
    "hosted-bundle.json",
    "index.json",
    "publication-manifest.json",
)
FORGE_MARKETPLACE_CATALOG_RELATIVE_PATH = Path("runtime") / "forge" / "registry" / "marketplace-catalog.json"

FORGE_APPROVAL_DECISION_RECORD_TYPE = "forge_approval_decision_handoff"
FORGE_APPROVAL_DECISION_SCHEMA_VERSION = "forge.approval_decision.v1"
FORGE_APPROVAL_DECISION_SURFACE_ID = "chaser_forge_approval_center_decision_handoff"
FORGE_APPROVAL_DECISION_API_METHOD = "review_chaser_forge_approval_decision"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _safe_identifier(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    return safe or "forge-marketplace-package"


def _package_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    payload_without_digest = deepcopy(payload)
    payload_without_digest.pop("package_digest_sha256", None)
    payload_without_digest.pop("generated_at", None)
    return payload_without_digest


def _package_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_package_payload_for_digest(payload))


def _target_paths(manifest: dict[str, Any]) -> list[str]:
    install = manifest.get("install") if isinstance(manifest.get("install"), dict) else {}
    paths = install.get("targetPaths") if isinstance(install, dict) else []
    return [str(item) for item in paths if isinstance(item, str)]


def _marketplace_template_points(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    points = manifest.get("extensionPoints")
    if not isinstance(points, list):
        return []
    return [deepcopy(point) for point in points if isinstance(point, dict) and point.get("type") == "marketplace.template"]


def _package_artifact_path(vault: Path, package_id: str, package_digest: str) -> Path:
    filename = f"{_safe_identifier(package_id)[:48]}-{package_digest[:12]}.json"
    return (vault / FORGE_MARKETPLACE_PACKAGE_RELATIVE_DIR / filename).resolve()


def _remote_index_artifact_path(vault: Path, publisher_id: str, index_digest: str) -> Path:
    filename = f"{_safe_identifier(publisher_id)[:48]}-remote-index-{index_digest[:12]}.json"
    return (vault / FORGE_MARKETPLACE_REMOTE_INDEX_RELATIVE_DIR / filename).resolve()


def _hosted_bundle_artifact_path(vault: Path, publisher_id: str, bundle_digest: str) -> Path:
    filename = f"{_safe_identifier(publisher_id)[:48]}-hosted-bundle-{bundle_digest[:12]}.json"
    return (vault / FORGE_MARKETPLACE_HOSTED_BUNDLE_RELATIVE_DIR / filename).resolve()


def _static_publication_dir(vault: Path, publisher_id: str, publication_digest: str) -> Path:
    dirname = f"{_safe_identifier(publisher_id)[:24]}-static-{publication_digest[:12]}"
    return (vault / FORGE_MARKETPLACE_STATIC_PUBLICATION_RELATIVE_DIR / dirname).resolve()


def _static_upload_handoff_artifact_paths(vault: Path, publisher_id: str, handoff_digest: str) -> tuple[Path, Path]:
    stem = f"{_safe_identifier(publisher_id)[:48]}-static-upload-handoff-{handoff_digest[:12]}"
    root = (vault / FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RELATIVE_DIR).resolve()
    return (root / f"{stem}.json").resolve(), (root / f"{stem}.md").resolve()


def _static_upload_receipt_artifact_paths(vault: Path, publisher_id: str, receipt_digest: str) -> tuple[Path, Path]:
    stem = f"{_safe_identifier(publisher_id)[:48]}-static-upload-receipt-{receipt_digest[:12]}"
    root = (vault / FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_RELATIVE_DIR).resolve()
    return (root / f"{stem}.json").resolve(), (root / f"{stem}.md").resolve()


def _published_static_index_registration_artifact_paths(
    vault: Path,
    publisher_id: str,
    registration_digest: str,
) -> tuple[Path, Path]:
    stem = f"{_safe_identifier(publisher_id)[:32]}-pub-index-reg-{registration_digest[:12]}"
    root = (vault / FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_RELATIVE_DIR).resolve()
    return (root / f"{stem}.json").resolve(), (root / f"{stem}.md").resolve()


def _live_index_input_prefill_artifact_paths(vault: Path, prefill_digest: str) -> tuple[Path, Path]:
    stem = f"live-index-input-prefill-{prefill_digest[:12]}"
    root = (vault / FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_RELATIVE_DIR).resolve()
    return (root / f"{stem}.json").resolve(), (root / f"{stem}.md").resolve()


def _catalog_path(vault: Path) -> Path:
    return (vault / FORGE_MARKETPLACE_CATALOG_RELATIVE_PATH).resolve()


def _safe_json_path(vault: Path, relative_dir: Path, stem: str) -> Path:
    filename = f"{_safe_identifier(stem)[:96]}.json"
    return (vault / relative_dir / filename).resolve()


def _read_json_file(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_remote_index_path(vault: Path, remote_index_artifact_path: str | Path | None) -> tuple[dict[str, Any] | None, str, list[str]]:
    if remote_index_artifact_path in (None, ""):
        return None, "", ["remote_index_artifact_path_required"]
    raw_path = Path(str(remote_index_artifact_path))
    path = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
    blockers: list[str] = []
    try:
        path.relative_to(vault)
    except ValueError:
        return None, str(remote_index_artifact_path), ["remote_index_artifact_path_outside_vault_root"]
    if path.suffix.lower() != ".json":
        blockers.append("remote_index_artifact_must_be_json")
    if not path.is_file():
        blockers.append("remote_index_artifact_missing")
        return None, _rel(vault, path), blockers
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, _rel(vault, path), blockers + ["remote_index_artifact_unreadable"]
    if not isinstance(payload, dict):
        return None, _rel(vault, path), blockers + ["remote_index_artifact_not_object"]
    return payload, _rel(vault, path), blockers


def _read_hosted_bundle_path(vault: Path, hosted_bundle_artifact_path: str | Path | None) -> tuple[dict[str, Any] | None, str, list[str]]:
    if hosted_bundle_artifact_path in (None, ""):
        return None, "", ["hosted_bundle_artifact_path_required"]
    raw_path = Path(str(hosted_bundle_artifact_path))
    path = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
    blockers: list[str] = []
    try:
        path.relative_to(vault)
    except ValueError:
        return None, str(hosted_bundle_artifact_path), ["hosted_bundle_artifact_path_outside_vault_root"]
    if path.suffix.lower() != ".json":
        blockers.append("hosted_bundle_artifact_must_be_json")
    if not path.is_file():
        blockers.append("hosted_bundle_artifact_missing")
        return None, _rel(vault, path), blockers
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, _rel(vault, path), blockers + ["hosted_bundle_artifact_unreadable"]
    if not isinstance(payload, dict):
        return None, _rel(vault, path), blockers + ["hosted_bundle_artifact_not_object"]
    return payload, _rel(vault, path), blockers


def _read_static_upload_handoff_path(
    vault: Path,
    upload_handoff_artifact_path: str | Path | None,
) -> tuple[dict[str, Any] | None, str, list[str]]:
    if upload_handoff_artifact_path in (None, ""):
        return None, "", ["upload_handoff_artifact_path_required"]
    raw_path = Path(str(upload_handoff_artifact_path))
    path = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
    blockers: list[str] = []
    try:
        path.relative_to(vault)
    except ValueError:
        return None, str(upload_handoff_artifact_path), ["upload_handoff_artifact_path_outside_vault_root"]
    if path.suffix.lower() != ".json":
        blockers.append("upload_handoff_artifact_must_be_json")
    if not path.is_file():
        blockers.append("upload_handoff_artifact_missing")
        return None, _rel(vault, path), blockers
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, _rel(vault, path), blockers + ["upload_handoff_artifact_unreadable"]
    if not isinstance(payload, dict):
        return None, _rel(vault, path), blockers + ["upload_handoff_artifact_not_object"]
    return payload, _rel(vault, path), blockers


def _read_static_upload_receipt_path(
    vault: Path,
    upload_receipt_artifact_path: str | Path | None,
) -> tuple[dict[str, Any] | None, str, list[str]]:
    if upload_receipt_artifact_path in (None, ""):
        return None, "", ["upload_receipt_artifact_path_required"]
    raw_path = Path(str(upload_receipt_artifact_path))
    path = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
    blockers: list[str] = []
    try:
        path.relative_to(vault)
    except ValueError:
        return None, str(upload_receipt_artifact_path), ["upload_receipt_artifact_path_outside_vault_root"]
    if path.suffix.lower() != ".json":
        blockers.append("upload_receipt_artifact_must_be_json")
    if not path.is_file():
        blockers.append("upload_receipt_artifact_missing")
        return None, _rel(vault, path), blockers
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, _rel(vault, path), blockers + ["upload_receipt_artifact_unreadable"]
    if not isinstance(payload, dict):
        return None, _rel(vault, path), blockers + ["upload_receipt_artifact_not_object"]
    return payload, _rel(vault, path), blockers


def _resolve_marketplace_import_approval_path(
    vault: Path,
    path_value: str | Path | None,
) -> tuple[Path | None, list[str]]:
    if path_value in (None, ""):
        return None, ["marketplace_import_approval_artifact_path_required"]
    root = (vault / FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR).resolve()
    raw = Path(str(path_value))
    path = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    blockers: list[str] = []
    try:
        relative = path.relative_to(root)
    except ValueError:
        return None, ["marketplace_import_approval_artifact_path_outside_root"]
    if len(relative.parts) != 1 or path.suffix.lower() != ".json":
        blockers.append("marketplace_import_approval_artifact_path_must_be_direct_json")
    return path, blockers


def _read_sandbox_approval_payload_for_install(
    vault: Path,
    path_value: str | Path | None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if path_value in (None, ""):
        return None, None
    root = (vault / SANDBOX_APPROVAL_RELATIVE_DIR).resolve()
    raw = Path(str(path_value))
    path = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return path, None
    if len(relative.parts) != 1 or path.suffix.lower() != ".json":
        return path, None
    return path, _read_json_file(path) if path.is_file() else None


def _path_matches(vault: Path, value: str | Path | None, expected: Path) -> bool:
    if value in (None, ""):
        return False
    raw = Path(str(value))
    resolved = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    return resolved == expected.resolve()


def _authority(
    *,
    package_written: bool = False,
    approval_written: bool = False,
    sandbox_approval_written: bool = False,
    catalog_written: bool = False,
    install_executed: bool = False,
    marketplace_import_consumed: bool = False,
) -> dict[str, Any]:
    return {
        **dict(BLOCKED_AUTHORITY),
        "writes_marketplace_package_artifact": bool(package_written),
        "writes_marketplace_import_approval_artifact": bool(approval_written),
        "writes_sandbox_approval_artifact": bool(sandbox_approval_written),
        "writes_marketplace_catalog": bool(catalog_written),
        "marketplace_package_only": True,
        "marketplace_publish_allowed": bool(catalog_written),
        "marketplace_remote_call_allowed": False,
        "marketplace_import_install_allowed": bool(install_executed),
        "auto_install_allowed": bool(install_executed),
        "writes_extension_registry": bool(install_executed),
        "writes_extension_files": bool(install_executed),
        "consumes_approval": bool(install_executed or marketplace_import_consumed),
        "consumes_marketplace_import_approval": bool(marketplace_import_consumed),
        "executes_forge": bool(install_executed),
        "reserves_exact_once_marker": bool(install_executed),
    }


def _operator_import_confirmation_text(material: dict[str, Any]) -> str:
    target_paths = [str(item) for item in material.get("target_paths") or []]
    lines = [
        "APPROVE FORGE MARKETPLACE IMPORT SANDBOX REVIEW ONLY:",
        f"- approval_packet_id: {material.get('approval_packet_id') or 'unknown'}",
        f"- request_digest_sha256: {material.get('request_digest_sha256') or 'unknown'}",
        f"- package_digest_sha256: {material.get('package_digest_sha256') or 'unknown'}",
        f"- extension_id: {material.get('extension_id') or 'unknown-extension'}",
        "",
        "This approval records operator review intent only.",
        "No package install.",
        "No remote marketplace publish or call.",
        "No Forge registry write.",
        "No extension file mutation.",
        "No exact-once marker reservation.",
        "No protected-core, Studio shell, runtime policy, schedule, Agent Bus, provider, credential, external connector, or canonical mutation.",
    ]
    if target_paths:
        lines.extend(["", "Target paths declared by package manifest:", *[f"- {path}" for path in target_paths]])
    return "\n".join(lines)


def _remote_listing_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("listing_digest_sha256", None)
    package_payload = material.get("package_payload")
    if isinstance(package_payload, dict):
        package_payload.pop("generated_at", None)
    return material


def _remote_listing_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_remote_listing_payload_for_digest(payload))


def _remote_index_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("remote_index_digest_sha256", None)
    material.pop("publisher_attestation_digest_sha256", None)
    material.pop("generated_at", None)
    material.pop("updated_at", None)
    entries = material.get("entries")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            package_payload = entry.get("package_payload")
            if isinstance(package_payload, dict):
                package_payload.pop("generated_at", None)
    return material


def _remote_index_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_remote_index_payload_for_digest(payload))


def _hosted_bundle_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("hosted_bundle_digest_sha256", None)
    material.pop("generated_at", None)
    material.pop("updated_at", None)
    remote_index = material.get("remote_index_payload")
    if isinstance(remote_index, dict):
        remote_index.pop("generated_at", None)
        remote_index.pop("updated_at", None)
        entries = remote_index.get("entries")
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                package_payload = entry.get("package_payload")
                if isinstance(package_payload, dict):
                    package_payload.pop("generated_at", None)
    return material


def _hosted_bundle_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_hosted_bundle_payload_for_digest(payload))


def _static_text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _static_publication_payload_for_file(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("generated_at", None)
    material.pop("updated_at", None)

    remote_index = material.get("remote_index_payload")
    if isinstance(remote_index, dict):
        remote_index.pop("generated_at", None)
        remote_index.pop("updated_at", None)
        entries = remote_index.get("entries")
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                package_payload = entry.get("package_payload")
                if isinstance(package_payload, dict):
                    package_payload.pop("generated_at", None)

    entries = material.get("entries")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            package_payload = entry.get("package_payload")
            if isinstance(package_payload, dict):
                package_payload.pop("generated_at", None)

    return material


def _static_publication_digest(publication_manifest: dict[str, Any]) -> str:
    material = deepcopy(publication_manifest)
    material.pop("static_publication_digest_sha256", None)
    material.pop("generated_at", None)
    material.pop("updated_at", None)
    material.pop("source_hosted_bundle_artifact_path", None)
    return _sha256_payload(material)


def _static_upload_handoff_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("upload_handoff_digest_sha256", None)
    material.pop("generated_at", None)
    material.pop("updated_at", None)
    material.pop("file_statuses", None)
    return material


def _static_upload_handoff_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_static_upload_handoff_payload_for_digest(payload))


def _static_upload_receipt_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("upload_receipt_digest_sha256", None)
    material.pop("generated_at", None)
    material.pop("updated_at", None)
    material.pop("receipt_written_at", None)
    material.pop("operator_receipt_statement", None)
    material.pop("operator_receipt_statement_sha256", None)
    material.pop("operator_receipt_markdown", None)
    material.pop("operator_receipt_recorded", None)
    material.pop("operator_manual_upload_claim_recorded", None)
    material.pop("source_handoff_file_statuses", None)
    receipts = material.get("hosted_file_receipts")
    if isinstance(receipts, list):
        for receipt in receipts:
            if isinstance(receipt, dict):
                receipt.pop("operator_declared_uploaded", None)
    return material


def _static_upload_receipt_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_static_upload_receipt_payload_for_digest(payload))


def _required_static_upload_receipt_statement(
    *,
    publisher_id: str,
    remote_index_digest: str,
    hosted_bundle_digest: str,
    static_publication_digest: str,
    upload_handoff_digest: str,
    hosted_base_url: str,
) -> str:
    return (
        "CONFIRM CHASER FORGE STATIC HOST UPLOAD RECEIPT "
        f"publisher={publisher_id} "
        f"remote_index={remote_index_digest} "
        f"hosted_bundle={hosted_bundle_digest} "
        f"static_publication={static_publication_digest} "
        f"upload_handoff={upload_handoff_digest} "
        f"hosted_base={hosted_base_url}"
    )


def _hosted_url(base_url: str, path: str) -> str:
    base = (base_url or "operator-provided-static-host").rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _static_upload_receipt_markdown(payload: dict[str, Any]) -> str:
    files = [item for item in payload.get("hosted_file_receipts") or [] if isinstance(item, dict)]
    lines = [
        "# Chaser Forge Static Host Upload Receipt",
        "",
        f"- Publisher: `{payload.get('publisher_id') or ''}`",
        f"- Hosted base URL: `{payload.get('operator_uploaded_base_url') or ''}`",
        f"- Remote index digest: `{payload.get('remote_index_digest_sha256') or ''}`",
        f"- Hosted bundle digest: `{payload.get('hosted_bundle_digest_sha256') or ''}`",
        f"- Static publication digest: `{payload.get('static_publication_digest_sha256') or ''}`",
        f"- Upload handoff digest: `{payload.get('upload_handoff_digest_sha256') or ''}`",
        f"- Upload receipt digest: `{payload.get('upload_receipt_digest_sha256') or ''}`",
        "",
        "## Operator Receipt Statement",
        "",
        f"`{payload.get('required_operator_receipt_statement') or ''}`",
        "",
        "## Hosted File Receipts",
        "",
    ]
    for item in files:
        lines.append(
            f"- `{item.get('path') or ''}` -> `{item.get('hosted_url') or ''}` "
            f"`{item.get('expected_digest_sha256') or ''}`"
        )
    lines.extend(
        [
            "",
            "## Verification Boundary",
            "",
            "- Operator receipt recorded: `"
            + str(bool(payload.get("operator_receipt_recorded"))).lower()
            + "`",
            "- Network fetch performed: `false`",
            "- Network upload performed: `false`",
            "- External registry mutation performed: `false`",
            "- Payment mutation performed: `false`",
            "- License checkout performed: `false`",
            "- Package install performed: `false`",
            "",
            "This is a local operator receipt over a manual static-host upload claim.",
            "It does not contact the host and does not prove external availability by network fetch.",
            "",
        ]
    )
    return "\n".join(lines)


def _published_static_index_registration_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("published_static_index_registration_digest_sha256", None)
    material.pop("generated_at", None)
    material.pop("updated_at", None)
    material.pop("registration_written_at", None)
    material.pop("operator_registration_statement", None)
    material.pop("operator_registration_statement_sha256", None)
    material.pop("operator_registration_markdown", None)
    material.pop("operator_registration_recorded", None)
    material.pop("operator_declared_published_index_registered", None)
    material.pop("source_receipt_hosted_file_receipts", None)
    return material


def _published_static_index_registration_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_published_static_index_registration_payload_for_digest(payload))


def _live_index_input_prefill_payload_for_digest(payload: dict[str, Any]) -> dict[str, Any]:
    material = deepcopy(payload)
    material.pop("prefill_digest_sha256", None)
    material.pop("generated_at", None)
    material.pop("updated_at", None)
    material.pop("prefill_written_at", None)
    material.pop("prefill_markdown", None)
    material.pop("static_publication", None)
    material.pop("static_publication_preview", None)
    return material


def _live_index_input_prefill_digest(payload: dict[str, Any]) -> str:
    return _sha256_payload(_live_index_input_prefill_payload_for_digest(payload))


def _live_index_input_prefill_markdown(payload: dict[str, Any]) -> str:
    packet = payload.get("packet_payload") if isinstance(payload.get("packet_payload"), dict) else {}
    static_publication = (
        payload.get("static_publication")
        if isinstance(payload.get("static_publication"), dict)
        else {}
    )
    remaining = [str(item) for item in payload.get("remaining_operator_inputs") or []]
    lines = [
        "# Chaser Forge Live index.json Input Packet Prefill",
        "",
        f"- Status: `{payload.get('prefill_status') or payload.get('status') or ''}`",
        f"- Prefill digest: `{payload.get('prefill_digest_sha256') or ''}`",
        f"- Packet path: `{payload.get('prefilled_input_packet_json_path') or ''}`",
        f"- Local static publication: `{packet.get('local_static_publication_dir') or ''}`",
        f"- Local index SHA-256: `{packet.get('local_index_sha256') or ''}`",
        f"- Domain deferred: `{str(bool(payload.get('domain_purchase_deferred'))).lower()}`",
        f"- Static publication present: `{str(bool(static_publication.get('present'))).lower()}`",
        "",
        "## Packet Values",
        "",
        "```json",
        json.dumps(packet, indent=2, ensure_ascii=True, sort_keys=True, default=str),
        "```",
        "",
        "## Still Needed",
        "",
    ]
    lines.extend([f"- {item}" for item in remaining] or ["- None"])
    lines.extend(
        [
            "",
            "## Authority Boundary",
            "",
            "- Network fetch performed: `false`",
            "- Network upload performed: `false`",
            "- External registry mutation performed: `false`",
            "- Payment mutation performed: `false`",
            "- License checkout performed: `false`",
            "- Package install performed: `false`",
            "- Provider/model call performed: `false`",
            "- Agent Bus dispatch performed: `false`",
            "",
            "This packet is a local prefill only. Domain, hosted URL, upload confirmation, and bounded fetch approval remain operator-owned until the official ChaseOS domain is available.",
            "",
        ]
    )
    return "\n".join(lines)


def _published_static_index_url_blockers(url: str) -> list[str]:
    value = str(url or "").strip()
    if not value:
        return ["published_static_index_url_required"]
    parsed = urlparse(value)
    blockers: list[str] = []
    if parsed.scheme != "https":
        blockers.append("published_static_index_url_must_use_https")
    if not parsed.netloc or not parsed.hostname:
        blockers.append("published_static_index_url_host_required")
    if parsed.username or parsed.password:
        blockers.append("published_static_index_url_must_not_include_credentials")
    if parsed.query:
        blockers.append("published_static_index_url_query_not_allowed")
    if parsed.fragment:
        blockers.append("published_static_index_url_fragment_not_allowed")
    if not parsed.path or not parsed.path.rstrip("/").endswith("/index.json"):
        blockers.append("published_static_index_url_must_end_with_index_json")
    return blockers


def _live_index_value_unfilled(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    lowered = text.lower()
    placeholder_tokens = (
        "<",
        ">",
        "hosted_base_url",
        "local_static_publication_dir",
        "<sha256",
        "real-host",
        "yourdomain",
    )
    return any(token in lowered for token in placeholder_tokens)


def _hosted_base_url_blockers(url: str) -> list[str]:
    value = str(url or "").strip()
    if not value:
        return ["hosted_base_url_required"]
    parsed = urlparse(value)
    blockers: list[str] = []
    if parsed.scheme != "https":
        blockers.append("hosted_base_url_must_use_https")
    if not parsed.netloc or not parsed.hostname:
        blockers.append("hosted_base_url_host_required")
    if parsed.username or parsed.password:
        blockers.append("hosted_base_url_must_not_include_credentials")
    if parsed.query:
        blockers.append("hosted_base_url_query_not_allowed")
    if parsed.fragment:
        blockers.append("hosted_base_url_fragment_not_allowed")
    if parsed.path.rstrip("/").endswith("/index.json"):
        blockers.append("hosted_base_url_must_be_directory_not_index_json")
    return blockers


def _live_index_parent_url(public_index_url: str) -> str:
    parsed = urlparse(public_index_url)
    parent_path = parsed.path.rsplit("/index.json", 1)[0].rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{parent_path}".rstrip("/")


def _resolve_vault_child(vault: Path, value: str | Path) -> tuple[Path, str]:
    raw = Path(str(value))
    path = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    try:
        path.relative_to(vault)
    except ValueError:
        return path, "path_outside_vault_root"
    return path, ""


def _latest_static_publication_dir(vault: Path) -> Path | None:
    root = (vault / FORGE_MARKETPLACE_STATIC_PUBLICATION_RELATIVE_DIR).resolve()
    try:
        root.relative_to(vault)
    except ValueError:
        return None
    if not root.is_dir():
        return None
    candidates: list[tuple[int, float, str, Path]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        present = sum(1 for name in FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES if (child / name).is_file())
        if present <= 0:
            continue
        try:
            newest = max(
                ((child / name).stat().st_mtime for name in FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES if (child / name).is_file()),
                default=child.stat().st_mtime,
            )
        except OSError:
            newest = 0.0
        candidates.append((present, newest, child.name, child))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item[0], item[1], item[2]))[-1][3]


def _inspect_static_publication_dir(vault: Path, publication_dir: Path | None) -> dict[str, Any]:
    blockers: list[str] = []
    if publication_dir is None:
        return {
            "present": False,
            "path": "",
            "index_sha256": "",
            "required_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
            "missing_required_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
            "file_statuses": [],
            "blockers": ["local_static_publication_candidate_missing"],
        }

    try:
        publication_dir.relative_to(vault)
    except ValueError:
        return {
            "present": False,
            "path": _rel(vault, publication_dir),
            "index_sha256": "",
            "required_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
            "missing_required_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
            "file_statuses": [],
            "blockers": ["local_static_publication_dir_outside_vault_root"],
        }

    if not publication_dir.is_dir():
        return {
            "present": False,
            "path": _rel(vault, publication_dir),
            "index_sha256": "",
            "required_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
            "missing_required_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
            "file_statuses": [],
            "blockers": ["local_static_publication_dir_missing"],
        }

    checksums = _read_json_file(publication_dir / "checksums.json") or {}
    checksum_records = {
        str(item.get("path") or ""): item
        for item in checksums.get("files") or []
        if isinstance(item, dict) and item.get("path")
    }
    file_statuses: list[dict[str, Any]] = []
    missing_required: list[str] = []
    index_sha256 = ""
    for name in FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES:
        target = (publication_dir / name).resolve()
        try:
            target.relative_to(publication_dir)
        except ValueError:
            blockers.append(f"static_publication_file_outside_publication_dir:{name}")
            continue
        exists = target.is_file()
        digest = ""
        expected_digest = str((checksum_records.get(name) or {}).get("digest_sha256") or "")
        digest_matches = False
        size_bytes = 0
        if exists:
            try:
                text = target.read_text(encoding="utf-8")
                digest = _static_text_digest(text)
                size_bytes = len(text.encode("utf-8"))
            except OSError:
                blockers.append(f"static_publication_file_unreadable:{name}")
            if name == "index.json":
                index_sha256 = digest
            digest_matches = bool(digest and (not expected_digest or expected_digest == digest))
            if expected_digest and digest != expected_digest:
                blockers.append(f"static_publication_file_digest_mismatch:{name}")
            if checksums and name != "checksums.json" and not expected_digest:
                blockers.append(f"static_publication_checksum_record_missing:{name}")
        else:
            missing_required.append(name)
            blockers.append(f"static_publication_required_file_missing:{name}")
        file_statuses.append(
            {
                "path": name,
                "exists": exists,
                "digest_sha256": digest,
                "expected_digest_sha256": expected_digest,
                "digest_matches": digest_matches,
                "size_bytes": size_bytes,
            }
        )

    return {
        "present": True,
        "path": _rel(vault, publication_dir),
        "index_sha256": index_sha256,
        "static_publication_digest_sha256": str(checksums.get("static_publication_digest_sha256") or ""),
        "remote_index_digest_sha256": str(checksums.get("remote_index_digest_sha256") or ""),
        "hosted_bundle_digest_sha256": str(checksums.get("hosted_bundle_digest_sha256") or ""),
        "checksums_present": bool(checksums),
        "checksums_file_record_count": len(checksum_records),
        "required_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
        "missing_required_files": missing_required,
        "file_statuses": file_statuses,
        "all_required_files_present": not missing_required,
        "blockers": list(dict.fromkeys(blockers)),
    }


def _required_published_static_index_registration_statement(
    *,
    publisher_id: str,
    published_static_index_url: str,
    remote_index_digest: str,
    hosted_bundle_digest: str,
    static_publication_digest: str,
    upload_handoff_digest: str,
    upload_receipt_digest: str,
) -> str:
    return (
        "CONFIRM CHASER FORGE PUBLISHED STATIC INDEX REGISTRATION "
        f"publisher={publisher_id} "
        f"published_index={published_static_index_url} "
        f"remote_index={remote_index_digest} "
        f"hosted_bundle={hosted_bundle_digest} "
        f"static_publication={static_publication_digest} "
        f"upload_handoff={upload_handoff_digest} "
        f"upload_receipt={upload_receipt_digest}"
    )


def _published_static_index_registration_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Chaser Forge Published Static Index Registration",
        "",
        f"- Publisher: `{payload.get('publisher_id') or ''}`",
        f"- Published static index URL: `{payload.get('operator_published_static_index_url') or ''}`",
        f"- Remote index digest: `{payload.get('remote_index_digest_sha256') or ''}`",
        f"- Hosted bundle digest: `{payload.get('hosted_bundle_digest_sha256') or ''}`",
        f"- Static publication digest: `{payload.get('static_publication_digest_sha256') or ''}`",
        f"- Upload handoff digest: `{payload.get('upload_handoff_digest_sha256') or ''}`",
        f"- Upload receipt digest: `{payload.get('upload_receipt_digest_sha256') or ''}`",
        f"- Registration digest: `{payload.get('published_static_index_registration_digest_sha256') or ''}`",
        "",
        "## Operator Registration Statement",
        "",
        f"`{payload.get('required_operator_registration_statement') or ''}`",
        "",
        "## Verification Boundary",
        "",
        "- Operator registration recorded: `"
        + str(bool(payload.get("operator_registration_recorded"))).lower()
        + "`",
        "- Live URL fetch performed: `false`",
        "- Network upload performed: `false`",
        "- External registry mutation performed: `false`",
        "- Payment mutation performed: `false`",
        "- License checkout performed: `false`",
        "- Package install performed: `false`",
        "",
        "This is a local registration of an operator-declared published index URL.",
        "It does not fetch the URL and does not mutate an external registry.",
        "",
    ]
    return "\n".join(lines)


def _static_upload_handoff_markdown(payload: dict[str, Any]) -> str:
    files = [item for item in payload.get("upload_file_checklist") or [] if isinstance(item, dict)]
    lines = [
        "# Chaser Forge Static Host Upload Handoff",
        "",
        f"- Publisher: `{payload.get('publisher_id') or ''}`",
        f"- Static publication digest: `{payload.get('static_publication_digest_sha256') or ''}`",
        f"- Remote index digest: `{payload.get('remote_index_digest_sha256') or ''}`",
        f"- Hosted bundle digest: `{payload.get('hosted_bundle_digest_sha256') or ''}`",
        f"- Source directory: `{payload.get('static_publication_dir_path') or ''}`",
        f"- Declared static base URL: `{payload.get('declared_static_base_url') or ''}`",
        "",
        "## Upload Checklist",
        "",
    ]
    for item in files:
        lines.append(
            f"- `{item.get('path') or ''}` `{item.get('digest_sha256') or ''}` "
            f"({item.get('size_bytes') or 0} bytes)"
        )
    lines.extend(
        [
            "",
            "## Authority Boundary",
            "",
            "- Network upload performed: `false`",
            "- External registry mutation performed: `false`",
            "- Payment mutation performed: `false`",
            "- License checkout performed: `false`",
            "- Package install performed: `false`",
            "",
            "The operator may manually upload the listed files to an operator-controlled static host.",
            "This handoff is local evidence only and does not contact the host.",
            "",
        ]
    )
    return "\n".join(lines)


def _hosted_bundle_readme(
    *,
    publisher_id: str,
    remote_index_digest: str,
    entry_count: int,
    static_base_url: str,
) -> str:
    base_url = static_base_url or "manual-static-host"
    return "\n".join(
        [
            "# Chaser Forge Hosted Marketplace Bundle",
            "",
            f"- Publisher: `{publisher_id}`",
            f"- Remote index digest: `{remote_index_digest}`",
            f"- Listing count: `{entry_count}`",
            f"- Intended static host: `{base_url}`",
            "",
            "This bundle is a portable ChaseOS Forge distribution artifact.",
            "It can be manually mirrored to a static host after operator review.",
            "It does not perform network publication, payment mutation, license checkout, or package installation.",
            "",
        ]
    )


def _publisher_fingerprint(publisher_id: str, fingerprint: str | None) -> str:
    if fingerprint and str(fingerprint).strip():
        return str(fingerprint).strip()
    return hashlib.sha256(f"chaseos-forge-publisher:{publisher_id}".encode("utf-8")).hexdigest()[:32]


def _remote_publisher_attestation_digest(index_digest: str, publisher_id: str, public_key_fingerprint: str) -> str:
    return _sha256_payload(
        {
            "scope": "chaseos-forge-remote-index-v1",
            "index_digest_sha256": index_digest,
            "publisher_id": publisher_id,
            "publisher_public_key_fingerprint": public_key_fingerprint,
        }
    )


def _remote_ingest_confirmation_text(material: dict[str, Any]) -> str:
    lines = [
        "APPROVE FORGE REMOTE LISTING INGEST ONLY:",
        f"- remote_index_digest_sha256: {material.get('remote_index_digest_sha256') or 'unknown'}",
        f"- listing_digest_sha256: {material.get('listing_digest_sha256') or 'unknown'}",
        f"- package_digest_sha256: {material.get('package_digest_sha256') or 'unknown'}",
        f"- publisher_id: {material.get('publisher_id') or 'unknown-publisher'}",
        f"- extension_id: {material.get('extension_id') or 'unknown-extension'}",
        "",
        "This approval imports a verified remote listing into the local Forge catalog only.",
        "No package install.",
        "No payment or license mutation.",
        "No remote network call.",
        "No Forge registry write.",
        "No extension file mutation.",
        "No approval consumption.",
        "No exact-once marker reservation.",
        "No protected-core, Studio shell, runtime policy, schedule, Agent Bus, provider, credential, external connector, Pulse, Personal Map, R&D truth-state, or canonical mutation.",
    ]
    return "\n".join(lines)


def build_forge_marketplace_export_package(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    package_id: str | None = None,
    category: str | None = None,
    license_id: str | None = None,
    publisher_id: str = "local-operator",
    write_package: bool = False,
    expected_package_digest: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Preview or write a local digest-bound Forge marketplace package artifact."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    manifest_payload = deepcopy(manifest or {})
    validation = validate_manifest(manifest_payload)
    blockers: list[str] = []
    if not validation.get("valid"):
        blockers.append("manifest_validation_failed")

    extension_id = str(manifest_payload.get("id") or "")
    extension_name = str(manifest_payload.get("name") or extension_id)
    extension_version = str(manifest_payload.get("version") or "")
    resolved_package_id = package_id or f"{extension_id or 'forge-extension'}-template"
    manifest_digest = _sha256_payload(manifest_payload) if manifest_payload else ""
    marketplace_points = _marketplace_template_points(manifest_payload)
    if not marketplace_points:
        blockers.append("marketplace_template_extension_point_missing")
    marketplace_point = marketplace_points[0] if marketplace_points else {}
    provenance = marketplace_point.get("provenance") if isinstance(marketplace_point.get("provenance"), dict) else {}
    resolved_category = category or str(marketplace_point.get("category") or "local-template")
    resolved_license = license_id or str(marketplace_point.get("license") or "local-review-only")
    resolved_publisher = publisher_id or str(provenance.get("publisher") or "local-operator")

    package_payload = {
        "record_type": FORGE_MARKETPLACE_PACKAGE_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_PACKAGE_SCHEMA_VERSION,
        "generated_at": timestamp,
        "surface": FORGE_MARKETPLACE_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_EXPORT_API_METHOD,
        "package_id": resolved_package_id,
        "extension_id": extension_id,
        "extension_name": extension_name,
        "extension_version": extension_version,
        "manifest_digest_sha256": manifest_digest,
        "manifest": manifest_payload,
        "manifest_validation": validation,
        "marketplace": {
            "category": resolved_category,
            "license": resolved_license,
            "publisher_id": resolved_publisher,
            "visibility": "local-review-only",
            "template_extension_point_declared": bool(marketplace_points),
            "template_points": marketplace_points,
            "publish_allowed": False,
            "remote_marketplace_call_allowed": False,
            "import_install_allowed": False,
            "auto_install_allowed": False,
        },
        "included_artifacts": {
            "manifest_json": True,
            "target_path_refs": _target_paths(manifest_payload),
            "ui_schema_refs": [
                item.get("entry")
                for item in (manifest_payload.get("ui") or {}).get("components", [])
                if isinstance(item, dict) and item.get("entry")
            ],
            "workflow_template_refs": [item.get("id") for item in manifest_payload.get("workflows", []) if isinstance(item, dict)],
            "agent_preset_refs": [item.get("id") for item in manifest_payload.get("agents", []) if isinstance(item, dict)],
            "data_schema_refs": [item.get("collection") for item in manifest_payload.get("dataSchemas", []) if isinstance(item, dict)],
            "mock_data_included": False,
            "binary_assets_included": False,
            "secrets_included": False,
            "credentials_included": False,
        },
        "permission_disclosure": {
            "permissions": sorted(set(str(item) for item in manifest_payload.get("permissions", []) if isinstance(item, str))),
            "required_approvals": validation.get("requiredApprovals") or [],
            "risk_level": validation.get("riskLevel") or "unknown",
            "hidden_permissions_allowed": False,
            "secrets_publish_allowed": False,
            "core_mutation_allowed": False,
        },
        "import_contract": {
            "api_method": FORGE_MARKETPLACE_IMPORT_API_METHOD,
            "requires_package_digest": True,
            "requires_manifest_validation": True,
            "requires_operator_approval_before_install": True,
            "future_install_path": "request_chaser_forge_sandbox_approval",
            "auto_install_allowed": False,
        },
        "authority": _authority(package_written=False),
    }
    package_payload["package_digest_sha256"] = _package_digest(package_payload)
    package_path = _package_artifact_path(vault, resolved_package_id, package_payload["package_digest_sha256"])

    if write_package:
        if not expected_package_digest:
            blockers.append("expected_package_digest_required")
        elif expected_package_digest != package_payload["package_digest_sha256"]:
            blockers.append("expected_package_digest_mismatch")
        if package_path.exists():
            blockers.append("package_artifact_already_present")

    blockers = list(dict.fromkeys(blockers))
    can_package = not blockers
    package_written = False
    if write_package and can_package:
        package_path.parent.mkdir(parents=True, exist_ok=True)
        package_path.write_text(json.dumps(package_payload, indent=2, ensure_ascii=True, default=str) + "\n", encoding="utf-8")
        package_written = True

    status = (
        "forge_marketplace_package_written"
        if package_written
        else "forge_marketplace_export_package_preview_ready"
        if can_package
        else "blocked_forge_marketplace_export_package"
    )
    return {
        "ok": can_package,
        "surface": FORGE_MARKETPLACE_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_PACKAGE_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not package_written,
        "write_package_requested": bool(write_package),
        "package_artifact_written": package_written,
        "package_artifact_path": _rel(vault, package_path),
        "package_digest_sha256": package_payload["package_digest_sha256"],
        "expected_package_digest_sha256": expected_package_digest or "",
        "manifest_digest_sha256": manifest_digest,
        "extension_id": extension_id,
        "extension_name": extension_name,
        "extension_version": extension_version,
        "marketplace_template_declared": bool(marketplace_points),
        "manifest_validation": validation,
        "package_payload": package_payload,
        "authority": _authority(package_written=package_written),
        "marketplace_publish_allowed": False,
        "marketplace_remote_call_allowed": False,
        "import_install_allowed": False,
        "auto_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "exact_once_marker_reserved": False,
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-marketplace-package-approval-or-import-sandbox-request"
            if can_package
            else "chaser-forge-marketplace-package-contract-repair"
        ),
    }


def _read_package_path(vault: Path, package_artifact_path: str | Path | None) -> tuple[dict[str, Any] | None, str, list[str]]:
    if package_artifact_path in (None, ""):
        return None, "", ["package_artifact_path_required"]
    raw_path = Path(str(package_artifact_path))
    path = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
    blockers: list[str] = []
    try:
        path.relative_to(vault)
    except ValueError:
        return None, str(package_artifact_path), ["package_artifact_path_outside_vault_root"]
    if path.suffix.lower() != ".json":
        blockers.append("package_artifact_must_be_json")
    if not path.is_file():
        blockers.append("package_artifact_missing")
        return None, _rel(vault, path), blockers
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, _rel(vault, path), blockers + ["package_artifact_unreadable"]
    if not isinstance(payload, dict):
        return None, _rel(vault, path), blockers + ["package_artifact_not_object"]
    return payload, _rel(vault, path), blockers


def build_forge_marketplace_import_preview(
    vault_root: str | Path,
    *,
    package_artifact_path: str | Path | None = None,
    package_payload: dict[str, Any] | None = None,
    expected_package_digest: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate a Forge marketplace package for future import without installing it."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    source_ref = ""
    payload = deepcopy(package_payload) if isinstance(package_payload, dict) else None
    if payload is None:
        payload, source_ref, blockers = _read_package_path(vault, package_artifact_path)
    else:
        source_ref = str(package_artifact_path or "inline_package_payload")

    if payload is None:
        payload = {}
    if payload.get("record_type") != FORGE_MARKETPLACE_PACKAGE_RECORD_TYPE:
        blockers.append("package_record_type_mismatch")
    if payload.get("schema_version") != FORGE_MARKETPLACE_PACKAGE_SCHEMA_VERSION:
        blockers.append("package_schema_version_mismatch")
    if payload.get("surface") != FORGE_MARKETPLACE_SURFACE_ID:
        blockers.append("package_surface_mismatch")
    source_digest = str(payload.get("package_digest_sha256") or "")
    recomputed_digest = _package_digest(payload)
    if not source_digest:
        blockers.append("package_digest_missing")
    elif source_digest != recomputed_digest:
        blockers.append("package_digest_mismatch")
    if expected_package_digest and expected_package_digest != source_digest:
        blockers.append("expected_package_digest_mismatch")

    manifest = payload.get("manifest") if isinstance(payload.get("manifest"), dict) else {}
    validation = validate_manifest(manifest)
    if not validation.get("valid"):
        blockers.append("package_manifest_validation_failed")
    recomputed_manifest_digest = _sha256_payload(manifest) if manifest else ""
    source_manifest_digest = str(payload.get("manifest_digest_sha256") or "")
    if not source_manifest_digest:
        blockers.append("manifest_digest_missing")
    elif source_manifest_digest != recomputed_manifest_digest:
        blockers.append("manifest_digest_mismatch")
    if not _marketplace_template_points(manifest):
        blockers.append("marketplace_template_extension_point_missing")
    marketplace = payload.get("marketplace") if isinstance(payload.get("marketplace"), dict) else {}
    if marketplace.get("publish_allowed") is True or marketplace.get("remote_marketplace_call_allowed") is True:
        blockers.append("package_publish_authority_unexpected")
    if marketplace.get("auto_install_allowed") is True or marketplace.get("import_install_allowed") is True:
        blockers.append("package_install_authority_unexpected")

    blockers = list(dict.fromkeys(blockers))
    can_import_preview = not blockers
    return {
        "ok": can_import_preview,
        "surface": FORGE_MARKETPLACE_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_PACKAGE_SCHEMA_VERSION,
        "status": "forge_marketplace_import_preview_ready" if can_import_preview else "blocked_forge_marketplace_import_preview",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": True,
        "package_artifact_path": source_ref,
        "package_digest_sha256": source_digest,
        "recomputed_package_digest_sha256": recomputed_digest,
        "expected_package_digest_sha256": expected_package_digest or "",
        "manifest_digest_sha256": source_manifest_digest,
        "recomputed_manifest_digest_sha256": recomputed_manifest_digest,
        "extension_id": manifest.get("id") or "",
        "extension_name": manifest.get("name") or "",
        "extension_version": manifest.get("version") or "",
        "marketplace_template_declared": bool(_marketplace_template_points(manifest)),
        "manifest_validation": validation,
        "future_import_requires": [
            "matching package digest",
            "clean manifest validation",
            "operator approval before sandbox install request",
            "source-specific Forge approval decision before any executor can consume",
        ],
        "authority": _authority(package_written=False),
        "marketplace_publish_allowed": False,
        "marketplace_remote_call_allowed": False,
        "import_install_allowed": False,
        "auto_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "exact_once_marker_reserved": False,
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-marketplace-import-sandbox-request"
            if can_import_preview
            else "chaser-forge-marketplace-package-contract-repair"
        ),
    }


def _empty_catalog(*, generated_at: str) -> dict[str, Any]:
    return {
        "record_type": FORGE_MARKETPLACE_CATALOG_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_CATALOG_SCHEMA_VERSION,
        "generated_at": generated_at,
        "updated_at": generated_at,
        "surface": FORGE_MARKETPLACE_CATALOG_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_CATALOG_API_METHOD,
        "visibility": "local_public_catalog",
        "transport": "vault_local_json",
        "remote_marketplace_call_allowed": False,
        "entries": [],
    }


def _load_catalog_payload(vault: Path, *, generated_at: str) -> tuple[dict[str, Any], list[str]]:
    path = _catalog_path(vault)
    if not path.exists():
        return _empty_catalog(generated_at=generated_at), []
    payload = _read_json_file(path)
    blockers: list[str] = []
    if payload is None:
        return _empty_catalog(generated_at=generated_at), ["marketplace_catalog_unreadable"]
    if payload.get("record_type") != FORGE_MARKETPLACE_CATALOG_RECORD_TYPE:
        blockers.append("marketplace_catalog_record_type_mismatch")
    if payload.get("schema_version") != FORGE_MARKETPLACE_CATALOG_SCHEMA_VERSION:
        blockers.append("marketplace_catalog_schema_version_mismatch")
    if not isinstance(payload.get("entries"), list):
        blockers.append("marketplace_catalog_entries_not_list")
        payload["entries"] = []
    return payload, blockers


def _catalog_entry_for_package(catalog: dict[str, Any], package_digest: str) -> dict[str, Any] | None:
    for entry in catalog.get("entries") or []:
        if isinstance(entry, dict) and entry.get("package_digest_sha256") == package_digest:
            return entry
    return None


def _catalog_entry_for_listing(catalog: dict[str, Any], listing_id: str | None, listing_digest: str | None) -> dict[str, Any] | None:
    for entry in catalog.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        if listing_id and entry.get("listing_id") == listing_id:
            return entry
        if listing_digest and entry.get("listing_digest_sha256") == listing_digest:
            return entry
    return None


def _marketplace_listing_material(
    *,
    package_payload: dict[str, Any],
    package_artifact_path: str,
    import_preview: dict[str, Any],
    listing_title: str | None,
    description: str | None,
    tags: list[str] | None,
    publisher_id: str,
) -> dict[str, Any]:
    manifest = package_payload.get("manifest") if isinstance(package_payload.get("manifest"), dict) else {}
    marketplace = package_payload.get("marketplace") if isinstance(package_payload.get("marketplace"), dict) else {}
    extension_id = str(import_preview.get("extension_id") or manifest.get("id") or "")
    extension_name = str(import_preview.get("extension_name") or manifest.get("name") or extension_id)
    extension_version = str(import_preview.get("extension_version") or manifest.get("version") or "")
    return {
        "record_type": FORGE_MARKETPLACE_PUBLISH_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_PUBLISH_SCHEMA_VERSION,
        "package_id": package_payload.get("package_id") or "",
        "package_artifact_path": package_artifact_path,
        "package_digest_sha256": import_preview.get("package_digest_sha256") or "",
        "manifest_digest_sha256": import_preview.get("manifest_digest_sha256") or "",
        "extension_id": extension_id,
        "extension_name": extension_name,
        "extension_version": extension_version,
        "listing_title": listing_title or extension_name,
        "description": description or f"{extension_name} Forge marketplace template",
        "category": marketplace.get("category") or "local-template",
        "license": marketplace.get("license") or "local-review-only",
        "publisher_id": publisher_id or marketplace.get("publisher_id") or "local-operator",
        "tags": sorted(set(str(item).strip() for item in (tags or []) if str(item).strip())),
        "visibility": "local_public_catalog",
        "transport": "vault_local_json",
        "install_api_method": FORGE_MARKETPLACE_INSTALL_API_METHOD,
        "remote_marketplace_call_allowed": False,
        "requires_marketplace_import_review": True,
        "requires_sandbox_approval": True,
        "requires_source_specific_decisions": True,
    }


def _catalog_entry_from_material(material: dict[str, Any], *, listing_id: str, listing_digest: str, generated_at: str) -> dict[str, Any]:
    return {
        **deepcopy(material),
        "listing_id": listing_id,
        "listing_digest_sha256": listing_digest,
        "published_at": generated_at,
        "updated_at": generated_at,
        "local_public_catalog_published": True,
        "remote_public_marketplace_published": False,
        "package_install_requires_approval_chain": True,
        "package_auto_install_without_approval_allowed": False,
    }


def build_forge_marketplace_catalog(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return the ChaseOS-owned local Forge marketplace catalog."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    path = _catalog_path(vault)
    catalog, blockers = _load_catalog_payload(vault, generated_at=timestamp)
    entries = [deepcopy(entry) for entry in catalog.get("entries") or [] if isinstance(entry, dict)]
    return {
        "ok": not blockers,
        "surface": FORGE_MARKETPLACE_CATALOG_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_CATALOG_SCHEMA_VERSION,
        "status": "forge_marketplace_catalog_ready" if not blockers else "blocked_forge_marketplace_catalog",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "catalog_path": _rel(vault, path),
        "catalog_exists": path.is_file(),
        "entry_count": len(entries),
        "entries": entries,
        "listing_ids": [str(entry.get("listing_id") or "") for entry in entries],
        "package_digests": [str(entry.get("package_digest_sha256") or "") for entry in entries],
        "local_public_catalog_available": True,
        "remote_marketplace_call_allowed": False,
        "authority": _authority(catalog_written=False),
        "blockers": list(dict.fromkeys(blockers)),
    }


def _target_path_evidence(vault: Path, registry_entry: dict[str, Any] | None) -> list[dict[str, Any]]:
    target_paths = []
    if isinstance(registry_entry, dict):
        target_paths = [
            str(item)
            for item in registry_entry.get("target_paths") or []
            if isinstance(item, str) and item.strip()
        ]
    evidence: list[dict[str, Any]] = []
    for path_value in target_paths:
        raw_path = Path(path_value)
        resolved = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
        inside_vault = True
        try:
            resolved.relative_to(vault.resolve())
        except ValueError:
            inside_vault = False
        evidence.append(
            {
                "path": path_value,
                "inside_vault": inside_vault,
                "exists": inside_vault and resolved.exists(),
                "is_file": inside_vault and resolved.is_file(),
                "is_dir": inside_vault and resolved.is_dir(),
            }
        )
    return evidence


def _library_item_from_catalog_entry(
    *,
    vault: Path,
    catalog_entry: dict[str, Any],
    registry_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    target_evidence = _target_path_evidence(vault, registry_entry)
    installed = registry_entry is not None
    registry_status = str((registry_entry or {}).get("registry_status") or "")
    install_environment = str((registry_entry or {}).get("install_environment") or "")
    install_state = (
        f"installed_{install_environment or registry_status}"
        if installed
        else "not_installed"
    )
    return {
        "item_id": str(catalog_entry.get("listing_id") or catalog_entry.get("extension_id") or ""),
        "source": "remote_verified_catalog" if catalog_entry.get("remote_distribution_source") else "local_catalog",
        "catalog_status": "listed",
        "install_state": install_state,
        "installed": installed,
        "listing_id": str(catalog_entry.get("listing_id") or ""),
        "listing_title": str(catalog_entry.get("listing_title") or catalog_entry.get("extension_name") or ""),
        "listing_digest_sha256": str(catalog_entry.get("listing_digest_sha256") or ""),
        "package_id": str(catalog_entry.get("package_id") or ""),
        "package_digest_sha256": str(catalog_entry.get("package_digest_sha256") or ""),
        "manifest_digest_sha256": str(catalog_entry.get("manifest_digest_sha256") or ""),
        "extension_id": str(catalog_entry.get("extension_id") or ""),
        "extension_name": str(catalog_entry.get("extension_name") or ""),
        "extension_version": str(catalog_entry.get("extension_version") or ""),
        "category": str(catalog_entry.get("category") or ""),
        "publisher_id": str(catalog_entry.get("publisher_id") or ""),
        "publisher_public_key_fingerprint": str(catalog_entry.get("publisher_public_key_fingerprint") or ""),
        "publisher_attestation_verified": catalog_entry.get("publisher_attestation_verified") is True,
        "remote_distribution_source": str(catalog_entry.get("remote_distribution_source") or ""),
        "remote_index_digest_sha256": str(catalog_entry.get("remote_index_digest_sha256") or ""),
        "remote_listing_digest_sha256": str(catalog_entry.get("remote_listing_digest_sha256") or ""),
        "payment_mutation_allowed": catalog_entry.get("payment_mutation_allowed") is True,
        "license_checkout_allowed": catalog_entry.get("license_checkout_allowed") is True,
        "install_api_method": str(catalog_entry.get("install_api_method") or FORGE_MARKETPLACE_INSTALL_API_METHOD),
        "requires_marketplace_import_review": catalog_entry.get("requires_marketplace_import_review") is True,
        "requires_sandbox_approval": catalog_entry.get("requires_sandbox_approval") is True,
        "requires_source_specific_decisions": catalog_entry.get("requires_source_specific_decisions") is True,
        "registry_status": registry_status,
        "install_environment": install_environment,
        "registry_entry": deepcopy(registry_entry) if isinstance(registry_entry, dict) else {},
        "target_path_count": len(target_evidence),
        "target_paths_existing_count": sum(1 for item in target_evidence if item.get("exists") is True),
        "target_path_evidence": target_evidence,
        "remote_marketplace_call_allowed": False,
        "third_party_package_exchange_allowed": False,
        "unauthorized_auto_install_allowed": False,
    }


def _library_item_from_unlisted_registry_entry(vault: Path, registry_entry: dict[str, Any]) -> dict[str, Any]:
    target_evidence = _target_path_evidence(vault, registry_entry)
    registry_status = str(registry_entry.get("registry_status") or "")
    install_environment = str(registry_entry.get("install_environment") or "")
    return {
        "item_id": str(registry_entry.get("extension_id") or ""),
        "source": "forge_registry",
        "catalog_status": "not_listed",
        "install_state": f"installed_{install_environment or registry_status}",
        "installed": True,
        "listing_id": "",
        "listing_title": str(registry_entry.get("name") or registry_entry.get("extension_id") or ""),
        "listing_digest_sha256": "",
        "package_id": "",
        "package_digest_sha256": "",
        "manifest_digest_sha256": str(registry_entry.get("manifest_digest_sha256") or ""),
        "extension_id": str(registry_entry.get("extension_id") or ""),
        "extension_name": str(registry_entry.get("name") or ""),
        "extension_version": str(registry_entry.get("version") or ""),
        "category": "",
        "publisher_id": "",
        "install_api_method": FORGE_MARKETPLACE_INSTALL_API_METHOD,
        "requires_marketplace_import_review": True,
        "requires_sandbox_approval": True,
        "requires_source_specific_decisions": True,
        "registry_status": registry_status,
        "install_environment": install_environment,
        "registry_entry": deepcopy(registry_entry),
        "target_path_count": len(target_evidence),
        "target_paths_existing_count": sum(1 for item in target_evidence if item.get("exists") is True),
        "target_path_evidence": target_evidence,
        "remote_marketplace_call_allowed": False,
        "third_party_package_exchange_allowed": False,
        "unauthorized_auto_install_allowed": False,
    }


def build_forge_marketplace_local_library(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return the local Marketplace Library read model for Studio operator use.

    This joins vault-local catalog listings with the Forge extension registry so
    Studio can show which local packages are listed, installed, or installed but
    not listed. It is inspection-only and grants no publish, install, remote
    exchange, approval-consumption, registry, or extension-file authority.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    catalog = build_forge_marketplace_catalog(vault, generated_at=timestamp)
    registry = build_extension_registry(vault)
    blockers = list(catalog.get("blockers") or []) + list(registry.get("blockers") or [])
    catalog_entries = [entry for entry in catalog.get("entries") or [] if isinstance(entry, dict)]
    registry_entries = [entry for entry in registry.get("entries") or [] if isinstance(entry, dict)]
    registry_by_extension: dict[str, dict[str, Any]] = {}
    for entry in registry_entries:
        extension_id = str(entry.get("extension_id") or "")
        if extension_id and extension_id not in registry_by_extension:
            registry_by_extension[extension_id] = entry

    listed_extension_ids: set[str] = set()
    listed_items: list[dict[str, Any]] = []
    for catalog_entry in catalog_entries:
        extension_id = str(catalog_entry.get("extension_id") or "")
        if extension_id:
            listed_extension_ids.add(extension_id)
        listed_items.append(
            _library_item_from_catalog_entry(
                vault=vault,
                catalog_entry=catalog_entry,
                registry_entry=registry_by_extension.get(extension_id),
            )
        )

    installed_unlisted_items = [
        _library_item_from_unlisted_registry_entry(vault, entry)
        for entry in registry_entries
        if str(entry.get("extension_id") or "") not in listed_extension_ids
    ]
    items = listed_items + installed_unlisted_items
    installed_items = [item for item in items if item.get("installed") is True]
    listed_installed_items = [item for item in listed_items if item.get("installed") is True]
    blockers = list(dict.fromkeys(str(item) for item in blockers if item))
    ready = not blockers
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_LOCAL_LIBRARY_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_LOCAL_LIBRARY_SCHEMA_VERSION,
        "status": "forge_marketplace_local_library_ready" if ready else "blocked_forge_marketplace_local_library",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "api_method": FORGE_MARKETPLACE_LOCAL_LIBRARY_API_METHOD,
        "catalog_path": catalog.get("catalog_path") or _rel(vault, _catalog_path(vault)),
        "catalog_exists": bool(catalog.get("catalog_exists")),
        "registry_path": registry.get("registry_path") or "",
        "registry_exists": bool(registry.get("registry_exists")),
        "local_catalog_entry_count": len(catalog_entries),
        "installed_extension_count": len(registry_entries),
        "library_item_count": len(items),
        "listed_installed_count": len(listed_installed_items),
        "listed_not_installed_count": len(listed_items) - len(listed_installed_items),
        "installed_unlisted_count": len(installed_unlisted_items),
        "items": items,
        "listed_items": listed_items,
        "installed_unlisted_items": installed_unlisted_items,
        "catalog": {
            "ok": catalog.get("ok"),
            "status": catalog.get("status") or "",
            "entry_count": catalog.get("entry_count") or 0,
            "remote_marketplace_call_allowed": catalog.get("remote_marketplace_call_allowed") is True,
        },
        "registry": {
            "ok": registry.get("ok"),
            "status": registry.get("status") or "",
            "entry_count": registry.get("entry_count") or 0,
        },
        "authority": _authority()
        | {
            "local_marketplace_library_read_only": True,
            "marketplace_package_only": False,
            "writes_marketplace_package_artifact": False,
            "writes_marketplace_catalog": False,
            "writes_marketplace_import_approval_artifact": False,
            "writes_sandbox_approval_artifact": False,
            "marketplace_publish_allowed": False,
            "marketplace_remote_call_allowed": False,
            "third_party_package_exchange_allowed": False,
            "marketplace_import_install_allowed": False,
            "auto_install_allowed": False,
            "unauthorized_auto_install_allowed": False,
            "writes_extension_registry": False,
            "writes_extension_files": False,
            "consumes_approval": False,
            "executes_forge": False,
            "reserves_exact_once_marker": False,
        },
        "remote_marketplace_call_allowed": False,
        "third_party_package_exchange_allowed": False,
        "unauthorized_auto_install_allowed": False,
        "blockers": blockers,
        "next_recommended_pass": "chaser-forge-local-marketplace-library-studio-use-smoke" if ready else "chaser-forge-local-marketplace-library-repair",
    }


def build_forge_marketplace_publish(
    vault_root: str | Path,
    *,
    package_artifact_path: str | Path | None = None,
    package_payload: dict[str, Any] | None = None,
    expected_package_digest: str | None = None,
    expected_listing_digest: str | None = None,
    write_listing: bool = False,
    listing_title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    publisher_id: str = "local-operator",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Publish a validated Forge package into the local public marketplace catalog."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    payload = deepcopy(package_payload) if isinstance(package_payload, dict) else None
    source_ref = str(package_artifact_path or "inline_package_payload")
    if payload is None:
        payload, source_ref, blockers = _read_package_path(vault, package_artifact_path)
    if payload is None:
        payload = {}

    import_preview = build_forge_marketplace_import_preview(
        vault,
        package_artifact_path=package_artifact_path if not package_payload else None,
        package_payload=payload if payload else None,
        expected_package_digest=expected_package_digest,
        generated_at=timestamp,
    )
    blockers.extend(str(item) for item in import_preview.get("blockers") or [])
    if not import_preview.get("ok"):
        blockers.append("marketplace_package_import_preview_blocked")

    material = _marketplace_listing_material(
        package_payload=payload,
        package_artifact_path=source_ref,
        import_preview=import_preview,
        listing_title=listing_title,
        description=description,
        tags=tags,
        publisher_id=publisher_id,
    )
    listing_digest = _sha256_payload(material)
    listing_id = f"forge-listing-{_safe_identifier(str(material.get('package_id') or material.get('extension_id') or 'package'))}-{listing_digest[:12]}"
    entry_preview = _catalog_entry_from_material(
        material,
        listing_id=listing_id,
        listing_digest=listing_digest,
        generated_at=timestamp,
    )
    catalog_payload, catalog_blockers = _load_catalog_payload(vault, generated_at=timestamp)
    blockers.extend(catalog_blockers)
    entries = [entry for entry in catalog_payload.get("entries") or [] if isinstance(entry, dict)]
    existing_matching = any(entry.get("listing_digest_sha256") == listing_digest for entry in entries)
    listing_conflicts = [
        entry
        for entry in entries
        if entry.get("package_id") == material.get("package_id")
        and entry.get("extension_version") == material.get("extension_version")
        and entry.get("listing_digest_sha256") != listing_digest
    ]
    if listing_conflicts:
        blockers.append("marketplace_catalog_listing_version_conflict")
    if write_listing and expected_listing_digest != listing_digest:
        blockers.append("expected_listing_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    catalog_written = False
    listing_reused = False
    if write_listing and ready:
        if existing_matching:
            listing_reused = True
        else:
            catalog_path = _catalog_path(vault)
            catalog_payload["entries"] = entries + [entry_preview]
            catalog_payload["updated_at"] = timestamp
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            catalog_path.write_text(
                json.dumps(catalog_payload, indent=2, ensure_ascii=True, default=str) + "\n",
                encoding="utf-8",
            )
            catalog_written = True

    status = (
        "forge_marketplace_catalog_listing_published"
        if catalog_written
        else "forge_marketplace_catalog_listing_existing_matching"
        if listing_reused or existing_matching
        else "forge_marketplace_publish_preview_ready"
        if ready
        else "blocked_forge_marketplace_publish"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_PUBLISH_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_PUBLISH_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "catalog_path": _rel(vault, _catalog_path(vault)),
        "preview_only": not catalog_written,
        "write_listing_requested": bool(write_listing),
        "catalog_listing_written": catalog_written,
        "catalog_listing_reused": listing_reused,
        "listing_id": listing_id,
        "listing_digest_sha256": listing_digest,
        "expected_listing_digest_sha256": expected_listing_digest or "",
        "catalog_entry_preview": entry_preview,
        "package_artifact_path": source_ref,
        "package_digest_sha256": import_preview.get("package_digest_sha256") or "",
        "manifest_digest_sha256": import_preview.get("manifest_digest_sha256") or "",
        "extension_id": material.get("extension_id") or "",
        "extension_name": material.get("extension_name") or "",
        "extension_version": material.get("extension_version") or "",
        "local_public_catalog_published": catalog_written or listing_reused or existing_matching,
        "remote_marketplace_call_allowed": False,
        "remote_public_marketplace_published": False,
        "import_preview": import_preview,
        "authority": _authority(catalog_written=catalog_written)
        | {
            "local_marketplace_publish_allowed": bool(catalog_written),
            "remote_marketplace_call_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-marketplace-install-from-catalog"
            if ready
            else "chaser-forge-marketplace-publish-repair"
        ),
    }


def _remote_license_policy(license_id: str | None, license_policy: dict[str, Any] | None) -> dict[str, Any]:
    policy = deepcopy(license_policy) if isinstance(license_policy, dict) else {}
    return {
        "license_id": str(policy.get("license_id") or license_id or "local-review-only"),
        "requires_acceptance": bool(policy.get("requires_acceptance", False)),
        "license_checkout_allowed": False,
        "license_mutation_allowed": False,
        "enforced_by": "operator_review",
    }


def _remote_payment_policy(payment_policy: dict[str, Any] | None) -> dict[str, Any]:
    policy = deepcopy(payment_policy) if isinstance(payment_policy, dict) else {}
    return {
        "payment_required": bool(policy.get("payment_required", False)),
        "payment_provider": str(policy.get("payment_provider") or ""),
        "checkout_url": str(policy.get("checkout_url") or ""),
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "payment_execution_surface": "not_configured",
    }


def _remote_listing_material(
    *,
    package_payload: dict[str, Any],
    package_artifact_path: str,
    import_preview: dict[str, Any],
    listing_title: str | None,
    description: str | None,
    tags: list[str] | None,
    publisher_id: str,
    publisher_public_key_fingerprint: str,
    distribution_channel: str,
    license_policy: dict[str, Any],
    payment_policy: dict[str, Any],
) -> dict[str, Any]:
    local_material = _marketplace_listing_material(
        package_payload=package_payload,
        package_artifact_path=package_artifact_path,
        import_preview=import_preview,
        listing_title=listing_title,
        description=description,
        tags=tags,
        publisher_id=publisher_id,
    )
    return {
        **local_material,
        "record_type": FORGE_MARKETPLACE_REMOTE_LISTING_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_REMOTE_LISTING_SCHEMA_VERSION,
        "visibility": "operator_verified_remote_index",
        "transport": "digest_bound_remote_index_json",
        "distribution_channel": distribution_channel,
        "publisher_public_key_fingerprint": publisher_public_key_fingerprint,
        "package_payload": deepcopy(package_payload),
        "remote_distribution_artifact_only": True,
        "publisher_attestation_required": True,
        "remote_marketplace_call_allowed": False,
        "remote_network_fetch_allowed": False,
        "remote_network_publish_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "license_policy": license_policy,
        "payment_policy": payment_policy,
        "third_party_package_exchange_allowed": False,
    }


def _remote_local_catalog_material(listing: dict[str, Any], *, remote_index_path: str, remote_index_digest: str) -> dict[str, Any]:
    material = deepcopy(listing)
    material["record_type"] = FORGE_MARKETPLACE_PUBLISH_RECORD_TYPE
    material["schema_version"] = FORGE_MARKETPLACE_PUBLISH_SCHEMA_VERSION
    material["visibility"] = "remote_verified_local_catalog_entry"
    material["transport"] = "verified_remote_index_json"
    material["remote_index_artifact_path"] = remote_index_path
    material["remote_index_digest_sha256"] = remote_index_digest
    material["remote_distribution_source"] = "verified_remote_index"
    material["remote_listing_digest_sha256"] = listing.get("listing_digest_sha256") or ""
    material["local_public_catalog_published"] = False
    material["remote_public_marketplace_published"] = False
    material["publisher_attestation_verified"] = True
    material["remote_marketplace_call_allowed"] = False
    material["remote_network_fetch_allowed"] = False
    material["remote_network_publish_allowed"] = False
    material["payment_mutation_allowed"] = False
    material["license_checkout_allowed"] = False
    material["third_party_package_exchange_allowed"] = False
    return material


def build_forge_marketplace_remote_distribution(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    package_artifact_path: str | Path | None = None,
    package_payload: dict[str, Any] | None = None,
    expected_package_digest: str | None = None,
    expected_remote_index_digest: str | None = None,
    write_index: bool = False,
    listing_title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    publisher_id: str = "local-operator",
    publisher_display_name: str = "Local Operator",
    publisher_public_key_fingerprint: str | None = None,
    publisher_trust_tier: str = "operator-approved",
    distribution_channel: str = "operator-approved-remote-index",
    license_policy: dict[str, Any] | None = None,
    payment_policy: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or write a governed remote-distribution index artifact.

    The index is a portable JSON artifact for declared remote distribution. It
    does not call a network, charge payments, or install packages.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    payload = deepcopy(package_payload) if isinstance(package_payload, dict) else None
    source_ref = str(package_artifact_path or "inline_package_payload")
    export_preview: dict[str, Any] = {}
    if payload is None and not package_artifact_path:
        export_preview = build_forge_marketplace_export_package(
            vault,
            manifest=manifest or {},
            publisher_id=publisher_id,
            write_package=False,
            generated_at=timestamp,
        )
        blockers.extend(str(item) for item in export_preview.get("blockers") or [])
        payload = deepcopy(export_preview.get("package_payload")) if isinstance(export_preview.get("package_payload"), dict) else {}
        source_ref = "inline_package_payload"
    elif payload is None:
        payload, source_ref, path_blockers = _read_package_path(vault, package_artifact_path)
        blockers.extend(path_blockers)
    if payload is None:
        payload = {}

    import_preview = build_forge_marketplace_import_preview(
        vault,
        package_artifact_path=package_artifact_path if package_payload is None and package_artifact_path else None,
        package_payload=payload if payload else None,
        expected_package_digest=expected_package_digest,
        generated_at=timestamp,
    )
    blockers.extend(str(item) for item in import_preview.get("blockers") or [])
    if not import_preview.get("ok"):
        blockers.append("remote_distribution_package_import_preview_blocked")
    if not publisher_id:
        blockers.append("remote_publisher_id_required")

    fingerprint = _publisher_fingerprint(publisher_id, publisher_public_key_fingerprint)
    marketplace = payload.get("marketplace") if isinstance(payload.get("marketplace"), dict) else {}
    resolved_license_policy = _remote_license_policy(str(marketplace.get("license") or ""), license_policy)
    resolved_payment_policy = _remote_payment_policy(payment_policy)
    listing_material = _remote_listing_material(
        package_payload=payload,
        package_artifact_path=source_ref,
        import_preview=import_preview,
        listing_title=listing_title,
        description=description,
        tags=tags,
        publisher_id=publisher_id,
        publisher_public_key_fingerprint=fingerprint,
        distribution_channel=distribution_channel,
        license_policy=resolved_license_policy,
        payment_policy=resolved_payment_policy,
    )
    listing_digest = _remote_listing_digest(listing_material)
    remote_listing = {
        **listing_material,
        "listing_digest_sha256": listing_digest,
    }
    index_payload = {
        "record_type": FORGE_MARKETPLACE_REMOTE_INDEX_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION,
        "generated_at": timestamp,
        "updated_at": timestamp,
        "surface": FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_API_METHOD,
        "write_api_method": FORGE_MARKETPLACE_REMOTE_INDEX_WRITE_API_METHOD,
        "ingest_api_method": FORGE_MARKETPLACE_REMOTE_INGEST_API_METHOD,
        "publisher": {
            "publisher_id": publisher_id,
            "display_name": publisher_display_name,
            "public_key_fingerprint": fingerprint,
            "trust_tier": publisher_trust_tier,
        },
        "distribution_channel": distribution_channel,
        "transport": "digest_bound_remote_index_json",
        "remote_network_publish_allowed": False,
        "remote_network_fetch_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "entries": [remote_listing],
        "entry_count": 1,
    }
    index_digest = _remote_index_digest(index_payload)
    index_payload["remote_index_digest_sha256"] = index_digest
    index_payload["publisher_attestation_digest_sha256"] = _remote_publisher_attestation_digest(
        index_digest,
        publisher_id,
        fingerprint,
    )
    index_path = _remote_index_artifact_path(vault, publisher_id, index_digest)
    existing_payload = _read_json_file(index_path) if index_path.is_file() else None
    existing_matches = bool(
        existing_payload
        and existing_payload.get("remote_index_digest_sha256") == index_digest
        and _remote_index_digest(existing_payload) == index_digest
        and existing_payload.get("publisher_attestation_digest_sha256")
        == index_payload["publisher_attestation_digest_sha256"]
    )
    if index_path.exists() and not existing_matches:
        blockers.append("remote_index_artifact_already_present_mismatch")
    if write_index and expected_remote_index_digest != index_digest:
        blockers.append("expected_remote_index_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    index_written = False
    index_reused = False
    if write_index and ready:
        if existing_matches:
            index_reused = True
        else:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(
                json.dumps(index_payload, indent=2, ensure_ascii=True, default=str) + "\n",
                encoding="utf-8",
            )
            index_written = True

    status = (
        "forge_marketplace_remote_index_written"
        if index_written
        else "forge_marketplace_remote_index_existing_matching"
        if index_reused or existing_matches
        else "forge_marketplace_remote_distribution_ready"
        if ready
        else "blocked_forge_marketplace_remote_distribution"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not index_written,
        "write_index_requested": bool(write_index),
        "remote_index_artifact_written": index_written,
        "remote_index_artifact_reused": index_reused,
        "remote_index_artifact_path": _rel(vault, index_path),
        "remote_index_digest_sha256": index_digest,
        "publisher_attestation_digest_sha256": index_payload["publisher_attestation_digest_sha256"],
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "listing_digest_sha256": listing_digest,
        "package_digest_sha256": import_preview.get("package_digest_sha256") or "",
        "manifest_digest_sha256": import_preview.get("manifest_digest_sha256") or "",
        "publisher_id": publisher_id,
        "publisher_public_key_fingerprint": fingerprint,
        "publisher_trust_tier": publisher_trust_tier,
        "distribution_channel": distribution_channel,
        "remote_index_payload": index_payload,
        "remote_listing": remote_listing,
        "export_preview": export_preview,
        "import_preview": import_preview,
        "authority": _authority()
        | {
            "writes_marketplace_remote_index_artifact": bool(index_written),
            "writes_marketplace_catalog": False,
            "remote_distribution_index_write_allowed": bool(index_written),
            "remote_marketplace_call_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "remote_distribution_enabled": ready,
        "publisher_identity_required": True,
        "publisher_attestation_required": True,
        "remote_network_publish_allowed": False,
        "remote_network_fetch_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-remote-listing-ingest"
            if ready
            else "chaser-forge-remote-distribution-contract-repair"
        ),
    }


def build_forge_marketplace_hosted_export_bundle(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    package_payload: dict[str, Any] | None = None,
    remote_index_artifact_path: str | Path | None = None,
    remote_index_payload: dict[str, Any] | None = None,
    expected_remote_index_digest: str | None = None,
    expected_hosted_bundle_digest: str | None = None,
    write_bundle: bool = False,
    publisher_id: str = "local-operator",
    publisher_display_name: str = "Local Operator",
    publisher_public_key_fingerprint: str | None = None,
    static_base_url: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or write a static-host export bundle for a verified remote index.

    The bundle is a local artifact that can be manually mirrored to external
    hosting later. This function never performs network publication, payment
    mutation, license checkout, or package installation.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    source_ref = str(remote_index_artifact_path or "inline_remote_index_payload")
    distribution_preview: dict[str, Any] = {}
    index_payload = deepcopy(remote_index_payload) if isinstance(remote_index_payload, dict) else None

    if index_payload is None and not remote_index_artifact_path:
        distribution_preview = build_forge_marketplace_remote_distribution(
            vault,
            manifest=manifest or {},
            package_payload=package_payload,
            publisher_id=publisher_id,
            publisher_display_name=publisher_display_name,
            publisher_public_key_fingerprint=publisher_public_key_fingerprint,
            generated_at=timestamp,
        )
        blockers.extend(str(item) for item in distribution_preview.get("blockers") or [])
        index_payload = deepcopy(distribution_preview.get("remote_index_payload")) if isinstance(
            distribution_preview.get("remote_index_payload"),
            dict,
        ) else {}
        source_ref = "inline_remote_index_payload"
    elif index_payload is None:
        index_payload, source_ref, path_blockers = _read_remote_index_path(vault, remote_index_artifact_path)
        blockers.extend(path_blockers)
    if index_payload is None:
        index_payload = {}

    source_index_digest = str(index_payload.get("remote_index_digest_sha256") or "")
    recomputed_index_digest = _remote_index_digest(index_payload)
    if not source_index_digest:
        blockers.append("remote_index_digest_missing")
    elif source_index_digest != recomputed_index_digest:
        blockers.append("remote_index_digest_mismatch")
    if expected_remote_index_digest and expected_remote_index_digest != source_index_digest:
        blockers.append("expected_remote_index_digest_mismatch")

    ingest_preview = build_forge_marketplace_remote_ingest_preview(
        vault,
        remote_index_payload=index_payload,
        expected_remote_index_digest=expected_remote_index_digest or source_index_digest or None,
        trusted_publisher_ids=[publisher_id],
        generated_at=timestamp,
    )
    blockers.extend(str(item) for item in ingest_preview.get("blockers") or [])
    if not ingest_preview.get("ok"):
        blockers.append("hosted_bundle_remote_index_verification_blocked")

    publisher = index_payload.get("publisher") if isinstance(index_payload.get("publisher"), dict) else {}
    resolved_publisher_id = str(publisher.get("publisher_id") or publisher_id)
    entries = [entry for entry in index_payload.get("entries") or [] if isinstance(entry, dict)]
    readme = _hosted_bundle_readme(
        publisher_id=resolved_publisher_id,
        remote_index_digest=source_index_digest,
        entry_count=len(entries),
        static_base_url=static_base_url,
    )
    publication_manifest = {
        "publication_mode": "manual_static_host",
        "static_base_url": static_base_url or "",
        "files": [
            {
                "path": "index.json",
                "role": "remote_index",
                "content_type": "application/json",
                "digest_sha256": source_index_digest,
                "required": True,
            },
            {
                "path": "README.md",
                "role": "operator_readme",
                "content_type": "text/markdown",
                "digest_sha256": hashlib.sha256(readme.encode("utf-8")).hexdigest(),
                "required": True,
            },
        ],
        "operator_steps": [
            "review hosted_bundle_payload and remote_index_payload",
            "mirror index.json and README.md to an operator-controlled static host",
            "share the remote index digest with downstream ChaseOS operators",
        ],
        "network_publish_allowed": False,
        "credentials_included": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
    }
    bundle_payload = {
        "record_type": FORGE_MARKETPLACE_HOSTED_BUNDLE_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_HOSTED_BUNDLE_SCHEMA_VERSION,
        "generated_at": timestamp,
        "updated_at": timestamp,
        "surface": FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_HOSTED_BUNDLE_API_METHOD,
        "write_api_method": FORGE_MARKETPLACE_HOSTED_BUNDLE_WRITE_API_METHOD,
        "publisher": {
            "publisher_id": resolved_publisher_id,
            "display_name": str(publisher.get("display_name") or publisher_display_name),
            "public_key_fingerprint": str(publisher.get("public_key_fingerprint") or ""),
            "trust_tier": str(publisher.get("trust_tier") or "operator-approved"),
        },
        "source_remote_index_artifact_path": source_ref,
        "remote_index_digest_sha256": source_index_digest,
        "publisher_attestation_digest_sha256": str(index_payload.get("publisher_attestation_digest_sha256") or ""),
        "entry_count": len(entries),
        "remote_index_payload": deepcopy(index_payload),
        "publication_manifest": publication_manifest,
        "hosted_readme_markdown": readme,
        "transport": "manual_static_host_bundle_json",
        "remote_network_publish_allowed": False,
        "remote_network_fetch_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "third_party_package_exchange_allowed": False,
    }
    bundle_digest = _hosted_bundle_digest(bundle_payload)
    bundle_payload["hosted_bundle_digest_sha256"] = bundle_digest
    bundle_path = _hosted_bundle_artifact_path(vault, resolved_publisher_id, bundle_digest)
    existing_payload = _read_json_file(bundle_path) if bundle_path.is_file() else None
    existing_matches = bool(
        existing_payload
        and existing_payload.get("hosted_bundle_digest_sha256") == bundle_digest
        and _hosted_bundle_digest(existing_payload) == bundle_digest
    )
    if bundle_path.exists() and not existing_matches:
        blockers.append("hosted_bundle_artifact_already_present_mismatch")
    if write_bundle and expected_remote_index_digest != source_index_digest:
        blockers.append("expected_remote_index_digest_required_or_mismatched")
    if write_bundle and expected_hosted_bundle_digest != bundle_digest:
        blockers.append("expected_hosted_bundle_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    bundle_written = False
    bundle_reused = False
    if write_bundle and ready:
        if existing_matches:
            bundle_reused = True
        else:
            bundle_path.parent.mkdir(parents=True, exist_ok=True)
            bundle_path.write_text(
                json.dumps(bundle_payload, indent=2, ensure_ascii=True, default=str) + "\n",
                encoding="utf-8",
            )
            bundle_written = True

    status = (
        "forge_marketplace_hosted_export_bundle_written"
        if bundle_written
        else "forge_marketplace_hosted_export_bundle_existing_matching"
        if bundle_reused or existing_matches
        else "forge_marketplace_hosted_export_bundle_ready"
        if ready
        else "blocked_forge_marketplace_hosted_export_bundle"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_HOSTED_BUNDLE_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not bundle_written,
        "write_bundle_requested": bool(write_bundle),
        "hosted_bundle_artifact_written": bundle_written,
        "hosted_bundle_artifact_reused": bundle_reused,
        "hosted_bundle_artifact_path": _rel(vault, bundle_path),
        "hosted_bundle_digest_sha256": bundle_digest,
        "expected_hosted_bundle_digest_sha256": expected_hosted_bundle_digest or "",
        "remote_index_artifact_path": source_ref,
        "remote_index_digest_sha256": source_index_digest,
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "publisher_id": resolved_publisher_id,
        "publisher_attestation_verified": bool(ingest_preview.get("publisher_attestation_verified")),
        "publisher_trusted": bool(ingest_preview.get("publisher_trusted")),
        "entry_count": len(entries),
        "publication_manifest": publication_manifest,
        "hosted_bundle_payload": bundle_payload,
        "remote_index_payload": deepcopy(index_payload),
        "remote_distribution_preview": distribution_preview,
        "remote_ingest_preview": ingest_preview,
        "authority": _authority()
        | {
            "writes_marketplace_hosted_bundle_artifact": bool(bundle_written),
            "writes_marketplace_remote_index_artifact": False,
            "writes_marketplace_catalog": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "hosted_export_enabled": ready,
        "manual_static_host_ready": ready,
        "remote_network_publish_allowed": False,
        "remote_network_fetch_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "operator-manual-static-host-publication-or-live-hosted-marketplace-if-authorized"
            if ready
            else "chaser-forge-hosted-export-bundle-repair"
        ),
    }


def build_forge_marketplace_static_host_publication(
    vault_root: str | Path,
    *,
    hosted_bundle_artifact_path: str | Path | None = None,
    hosted_bundle_payload: dict[str, Any] | None = None,
    expected_remote_index_digest: str | None = None,
    expected_hosted_bundle_digest: str | None = None,
    expected_static_publication_digest: str | None = None,
    write_publication: bool = False,
    static_base_url: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Preview or write upload-ready static-host files from a hosted bundle.

    The write target is a local proof directory only. This function never
    uploads, mutates an external registry, calls payment/license providers, or
    installs packages.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    bundle_payload = deepcopy(hosted_bundle_payload) if isinstance(hosted_bundle_payload, dict) else None
    source_ref = str(hosted_bundle_artifact_path or "predicted_hosted_bundle_artifact")

    if bundle_payload is None and hosted_bundle_artifact_path:
        bundle_payload, source_ref, path_blockers = _read_hosted_bundle_path(vault, hosted_bundle_artifact_path)
        blockers.extend(path_blockers)
    if bundle_payload is None:
        hosted_preview = build_forge_marketplace_hosted_export_bundle(
            vault,
            static_base_url=static_base_url,
            generated_at=timestamp,
        )
        blockers.extend(str(item) for item in hosted_preview.get("blockers") or [])
        bundle_payload = deepcopy(hosted_preview.get("hosted_bundle_payload")) if isinstance(
            hosted_preview.get("hosted_bundle_payload"),
            dict,
        ) else {}
        source_ref = str(hosted_preview.get("hosted_bundle_artifact_path") or source_ref)
    if bundle_payload is None:
        bundle_payload = {}

    if bundle_payload.get("record_type") != FORGE_MARKETPLACE_HOSTED_BUNDLE_RECORD_TYPE:
        blockers.append("hosted_bundle_record_type_mismatch")
    if bundle_payload.get("schema_version") != FORGE_MARKETPLACE_HOSTED_BUNDLE_SCHEMA_VERSION:
        blockers.append("hosted_bundle_schema_version_mismatch")
    if bundle_payload.get("surface") != FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID:
        blockers.append("hosted_bundle_surface_mismatch")

    source_bundle_digest = str(bundle_payload.get("hosted_bundle_digest_sha256") or "")
    recomputed_bundle_digest = _hosted_bundle_digest(bundle_payload)
    if not source_bundle_digest:
        blockers.append("hosted_bundle_digest_missing")
    elif source_bundle_digest != recomputed_bundle_digest:
        blockers.append("hosted_bundle_digest_mismatch")
    if expected_hosted_bundle_digest and expected_hosted_bundle_digest != source_bundle_digest:
        blockers.append("expected_hosted_bundle_digest_mismatch")

    remote_index_payload = (
        deepcopy(bundle_payload.get("remote_index_payload"))
        if isinstance(bundle_payload.get("remote_index_payload"), dict)
        else {}
    )
    source_remote_index_digest = str(bundle_payload.get("remote_index_digest_sha256") or "")
    recomputed_remote_index_digest = _remote_index_digest(remote_index_payload)
    if not source_remote_index_digest:
        blockers.append("remote_index_digest_missing")
    elif source_remote_index_digest != recomputed_remote_index_digest:
        blockers.append("remote_index_digest_mismatch")
    if expected_remote_index_digest and expected_remote_index_digest != source_remote_index_digest:
        blockers.append("expected_remote_index_digest_mismatch")

    if bundle_payload.get("remote_network_publish_allowed") is True:
        blockers.append("hosted_bundle_network_publish_authority_unexpected")
    if bundle_payload.get("payment_mutation_allowed") is True:
        blockers.append("hosted_bundle_payment_mutation_authority_unexpected")
    if bundle_payload.get("license_checkout_allowed") is True:
        blockers.append("hosted_bundle_license_checkout_authority_unexpected")
    if bundle_payload.get("package_install_allowed") is True:
        blockers.append("hosted_bundle_package_install_authority_unexpected")

    publisher = bundle_payload.get("publisher") if isinstance(bundle_payload.get("publisher"), dict) else {}
    publisher_id = str(publisher.get("publisher_id") or "local-operator")
    ingest_preview = build_forge_marketplace_remote_ingest_preview(
        vault,
        remote_index_payload=remote_index_payload,
        expected_remote_index_digest=expected_remote_index_digest or source_remote_index_digest or None,
        trusted_publisher_ids=[publisher_id],
        generated_at=timestamp,
    )
    blockers.extend(str(item) for item in ingest_preview.get("blockers") or [])
    if not ingest_preview.get("ok"):
        blockers.append("static_publication_remote_index_verification_blocked")

    readme = str(bundle_payload.get("hosted_readme_markdown") or "")
    if not readme:
        readme = _hosted_bundle_readme(
            publisher_id=publisher_id,
            remote_index_digest=source_remote_index_digest,
            entry_count=int(bundle_payload.get("entry_count") or 0),
            static_base_url=static_base_url,
        )
    hosted_bundle_file_payload = _static_publication_payload_for_file(bundle_payload)
    remote_index_file_payload = _static_publication_payload_for_file(remote_index_payload)
    hosted_bundle_text = json.dumps(hosted_bundle_file_payload, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n"
    remote_index_text = json.dumps(remote_index_file_payload, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n"
    readme_text = readme.rstrip() + "\n"
    base_files = {
        "index.json": remote_index_text,
        "README.md": readme_text,
        "hosted-bundle.json": hosted_bundle_text,
    }
    base_file_records = [
        {
            "path": path,
            "digest_sha256": _static_text_digest(content),
            "size_bytes": len(content.encode("utf-8")),
        }
        for path, content in sorted(base_files.items())
    ]
    publication_manifest = {
        "record_type": FORGE_MARKETPLACE_STATIC_PUBLICATION_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_STATIC_PUBLICATION_SCHEMA_VERSION,
        "surface": FORGE_MARKETPLACE_STATIC_PUBLICATION_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_STATIC_PUBLICATION_API_METHOD,
        "write_api_method": FORGE_MARKETPLACE_STATIC_PUBLICATION_WRITE_API_METHOD,
        "publication_mode": "manual_static_host_publication_proof",
        "static_base_url": static_base_url or "",
        "publisher": deepcopy(publisher),
        "remote_index_digest_sha256": source_remote_index_digest,
        "hosted_bundle_digest_sha256": source_bundle_digest,
        "entry_count": bundle_payload.get("entry_count") or 0,
        "files": base_file_records,
        "operator_steps": [
            "review all staged files in the local static-host publication directory",
            "manually upload index.json, README.md, hosted-bundle.json, publication-manifest.json, and checksums.json to an operator-controlled static host",
            "share the remote index digest and static publication digest with downstream ChaseOS operators",
        ],
        "network_upload_performed": False,
        "remote_network_publish_allowed": False,
        "external_registry_mutation_allowed": False,
        "credentials_included": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "third_party_package_exchange_allowed": False,
    }
    static_digest = _static_publication_digest(publication_manifest)
    publication_manifest["static_publication_digest_sha256"] = static_digest
    manifest_text = json.dumps(publication_manifest, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n"
    static_files = dict(base_files)
    static_files["publication-manifest.json"] = manifest_text
    checksum_records = [
        {
            "path": path,
            "digest_sha256": _static_text_digest(content),
            "size_bytes": len(content.encode("utf-8")),
        }
        for path, content in sorted(static_files.items())
    ]
    checksums_payload = {
        "record_type": "forge_marketplace_static_host_publication_checksums",
        "schema_version": "forge.marketplace_static_host_publication_checksums.v1",
        "static_publication_digest_sha256": static_digest,
        "remote_index_digest_sha256": source_remote_index_digest,
        "hosted_bundle_digest_sha256": source_bundle_digest,
        "files": checksum_records,
    }
    static_files["checksums.json"] = json.dumps(checksums_payload, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n"
    all_file_records = [
        {
            "path": path,
            "digest_sha256": _static_text_digest(content),
            "size_bytes": len(content.encode("utf-8")),
        }
        for path, content in sorted(static_files.items())
    ]

    publication_dir = _static_publication_dir(vault, publisher_id, static_digest)
    try:
        publication_dir.relative_to(vault)
    except ValueError:
        blockers.append("static_publication_dir_outside_vault_root")
    if write_publication and expected_remote_index_digest != source_remote_index_digest:
        blockers.append("expected_remote_index_digest_required_or_mismatched")
    if write_publication and expected_hosted_bundle_digest != source_bundle_digest:
        blockers.append("expected_hosted_bundle_digest_required_or_mismatched")
    if write_publication and expected_static_publication_digest != static_digest:
        blockers.append("expected_static_publication_digest_required_or_mismatched")
    for rel_path, content in static_files.items():
        target = (publication_dir / rel_path).resolve()
        try:
            target.relative_to(publication_dir)
        except ValueError:
            blockers.append("static_publication_file_outside_publication_dir")
            continue
        if target.exists() and _static_text_digest(target.read_text(encoding="utf-8")) != _static_text_digest(content):
            blockers.append(f"static_publication_file_already_present_mismatch:{rel_path}")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    written_files: list[str] = []
    reused_files: list[str] = []
    if write_publication and ready:
        publication_dir.mkdir(parents=True, exist_ok=True)
        for rel_path, content in sorted(static_files.items()):
            target = (publication_dir / rel_path).resolve()
            if target.is_file():
                reused_files.append(rel_path)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                written_files.append(rel_path)

    all_files_exist = all((publication_dir / path).is_file() for path in static_files)
    publication_written = bool(write_publication and written_files and ready)
    publication_reused = bool(write_publication and ready and all_files_exist and not written_files)
    status = (
        "forge_marketplace_static_host_publication_written"
        if publication_written
        else "forge_marketplace_static_host_publication_existing_matching"
        if ready and (publication_reused or (not write_publication and all_files_exist))
        else "forge_marketplace_static_host_publication_ready"
        if ready
        else "blocked_forge_marketplace_static_host_publication"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_STATIC_PUBLICATION_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_STATIC_PUBLICATION_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not publication_written,
        "write_publication_requested": bool(write_publication),
        "static_publication_written": publication_written,
        "static_publication_reused": publication_reused,
        "static_publication_dir_path": _rel(vault, publication_dir),
        "static_publication_digest_sha256": static_digest,
        "expected_static_publication_digest_sha256": expected_static_publication_digest or "",
        "remote_index_digest_sha256": source_remote_index_digest,
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "hosted_bundle_digest_sha256": source_bundle_digest,
        "expected_hosted_bundle_digest_sha256": expected_hosted_bundle_digest or "",
        "source_hosted_bundle_artifact_path": source_ref,
        "publisher_id": publisher_id,
        "file_count": len(static_files),
        "files": all_file_records,
        "written_files": written_files,
        "reused_files": reused_files,
        "publication_manifest": publication_manifest,
        "checksums": checksums_payload,
        "remote_ingest_preview": ingest_preview,
        "authority": _authority()
        | {
            "writes_marketplace_static_host_publication_artifacts": bool(publication_written),
            "writes_marketplace_hosted_bundle_artifact": False,
            "writes_marketplace_remote_index_artifact": False,
            "writes_marketplace_catalog": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
            "external_registry_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "static_host_publication_ready": ready,
        "manual_upload_ready": ready,
        "network_upload_performed": False,
        "remote_network_publish_allowed": False,
        "remote_network_fetch_allowed": False,
        "external_registry_mutation_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "operator-manual-static-host-upload-or-live-hosted-marketplace-if-authorized"
            if ready
            else "chaser-forge-static-host-publication-repair"
        ),
    }


def build_forge_marketplace_static_host_upload_handoff(
    vault_root: str | Path,
    *,
    static_publication_preview: dict[str, Any] | None = None,
    static_publication_dir_path: str | Path | None = None,
    expected_remote_index_digest: str | None = None,
    expected_hosted_bundle_digest: str | None = None,
    expected_static_publication_digest: str | None = None,
    expected_upload_handoff_digest: str | None = None,
    write_handoff: bool = False,
    declared_static_base_url: str = "",
    operator_static_host_label: str = "operator-controlled static host",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or write a local operator handoff for manual static-host upload.

    This is a local evidence and checklist artifact. It never uploads files,
    mutates an external registry, calls payment/license providers, or installs
    packages.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    preview = deepcopy(static_publication_preview) if isinstance(static_publication_preview, dict) else None
    if preview is None and static_publication_dir_path:
        raw_path = Path(str(static_publication_dir_path))
        publication_dir = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
        try:
            publication_dir.relative_to(vault)
        except ValueError:
            blockers.append("static_publication_dir_path_outside_vault_root")
        manifest = _read_json_file(publication_dir / "publication-manifest.json")
        checksums = _read_json_file(publication_dir / "checksums.json")
        preview = {
            "ok": bool(manifest and checksums),
            "status": "static_publication_dir_loaded" if manifest and checksums else "blocked_static_publication_dir_load",
            "static_publication_dir_path": _rel(vault, publication_dir),
            "static_publication_digest_sha256": (manifest or {}).get("static_publication_digest_sha256") or "",
            "remote_index_digest_sha256": (manifest or {}).get("remote_index_digest_sha256") or "",
            "hosted_bundle_digest_sha256": (manifest or {}).get("hosted_bundle_digest_sha256") or "",
            "publisher_id": ((manifest or {}).get("publisher") or {}).get("publisher_id") or "local-operator",
            "file_count": len((checksums or {}).get("files") or []),
            "files": (checksums or {}).get("files") or [],
            "publication_manifest": manifest or {},
            "checksums": checksums or {},
            "blockers": [] if manifest and checksums else ["static_publication_manifest_or_checksums_missing"],
        }
    if preview is None:
        preview = build_forge_marketplace_static_host_publication(
            vault,
            expected_remote_index_digest=expected_remote_index_digest,
            expected_hosted_bundle_digest=expected_hosted_bundle_digest,
            expected_static_publication_digest=expected_static_publication_digest,
            static_base_url=declared_static_base_url,
            generated_at=timestamp,
        )

    blockers.extend(str(item) for item in preview.get("blockers") or [])
    if not preview.get("ok"):
        blockers.append("static_publication_not_ready_for_upload_handoff")

    publication_manifest = (
        deepcopy(preview.get("publication_manifest"))
        if isinstance(preview.get("publication_manifest"), dict)
        else {}
    )
    checksums = deepcopy(preview.get("checksums")) if isinstance(preview.get("checksums"), dict) else {}
    file_records = [item for item in preview.get("files") or [] if isinstance(item, dict)]
    checksum_records = [item for item in checksums.get("files") or [] if isinstance(item, dict)]
    if not file_records and checksum_records:
        file_records = checksum_records

    required_files = {
        "index.json",
        "README.md",
        "hosted-bundle.json",
        "publication-manifest.json",
        "checksums.json",
    }
    file_paths = {str(item.get("path") or "") for item in file_records}
    missing_required_files = sorted(required_files - file_paths)
    if missing_required_files:
        blockers.append("static_publication_required_files_missing_from_manifest")

    source_remote_index_digest = str(preview.get("remote_index_digest_sha256") or "")
    source_hosted_bundle_digest = str(preview.get("hosted_bundle_digest_sha256") or "")
    source_static_publication_digest = str(preview.get("static_publication_digest_sha256") or "")
    if expected_remote_index_digest and expected_remote_index_digest != source_remote_index_digest:
        blockers.append("expected_remote_index_digest_mismatch")
    if expected_hosted_bundle_digest and expected_hosted_bundle_digest != source_hosted_bundle_digest:
        blockers.append("expected_hosted_bundle_digest_mismatch")
    if expected_static_publication_digest and expected_static_publication_digest != source_static_publication_digest:
        blockers.append("expected_static_publication_digest_mismatch")

    if publication_manifest:
        recomputed_static_digest = _static_publication_digest(publication_manifest)
        if source_static_publication_digest and recomputed_static_digest != source_static_publication_digest:
            blockers.append("static_publication_digest_mismatch")
        if publication_manifest.get("network_upload_performed") is True:
            blockers.append("static_publication_network_upload_unexpected")
        if publication_manifest.get("external_registry_mutation_allowed") is True:
            blockers.append("static_publication_external_registry_authority_unexpected")
        if publication_manifest.get("payment_mutation_allowed") is True:
            blockers.append("static_publication_payment_authority_unexpected")
        if publication_manifest.get("license_checkout_allowed") is True:
            blockers.append("static_publication_license_authority_unexpected")
        if publication_manifest.get("package_install_allowed") is True:
            blockers.append("static_publication_install_authority_unexpected")

    publication_dir_ref = str(preview.get("static_publication_dir_path") or static_publication_dir_path or "")
    publication_dir = (vault / publication_dir_ref).resolve() if publication_dir_ref else None
    file_statuses: list[dict[str, Any]] = []
    all_files_exist = False
    if publication_dir is not None:
        try:
            publication_dir.relative_to(vault)
        except ValueError:
            blockers.append("static_publication_dir_path_outside_vault_root")
        all_files_exist = True
        for item in sorted(file_records, key=lambda record: str(record.get("path") or "")):
            rel_path = str(item.get("path") or "")
            target = (publication_dir / rel_path).resolve()
            try:
                target.relative_to(publication_dir)
            except ValueError:
                blockers.append("static_publication_file_outside_publication_dir")
                all_files_exist = False
                continue
            exists = target.is_file()
            actual_digest = _static_text_digest(target.read_text(encoding="utf-8")) if exists else ""
            expected_digest = str(item.get("digest_sha256") or "")
            digest_matches = bool(exists and actual_digest == expected_digest)
            if not exists:
                all_files_exist = False
            elif not digest_matches:
                all_files_exist = False
                blockers.append(f"static_publication_file_digest_mismatch:{rel_path}")
            file_statuses.append(
                {
                    "path": rel_path,
                    "expected_digest_sha256": expected_digest,
                    "actual_digest_sha256": actual_digest,
                    "size_bytes": item.get("size_bytes") or 0,
                    "exists": exists,
                    "digest_matches": digest_matches,
                    "ready_for_manual_upload": bool(exists and digest_matches),
                }
            )
    if write_handoff and not all_files_exist:
        blockers.append("static_publication_files_required_before_upload_handoff_write")

    publisher = publication_manifest.get("publisher") if isinstance(publication_manifest.get("publisher"), dict) else {}
    publisher_id = str(preview.get("publisher_id") or publisher.get("publisher_id") or "local-operator")
    upload_file_checklist = [
        {
            "path": str(item.get("path") or ""),
            "digest_sha256": str(item.get("digest_sha256") or item.get("expected_digest_sha256") or ""),
            "size_bytes": item.get("size_bytes") or 0,
            "required": True,
        }
        for item in sorted(file_records, key=lambda record: str(record.get("path") or ""))
    ]
    handoff_payload = {
        "record_type": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SCHEMA_VERSION,
        "generated_at": timestamp,
        "updated_at": timestamp,
        "surface": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_API_METHOD,
        "write_api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_WRITE_API_METHOD,
        "publisher_id": publisher_id,
        "operator_static_host_label": operator_static_host_label,
        "declared_static_base_url": declared_static_base_url or "",
        "static_publication_dir_path": publication_dir_ref,
        "static_publication_digest_sha256": source_static_publication_digest,
        "remote_index_digest_sha256": source_remote_index_digest,
        "hosted_bundle_digest_sha256": source_hosted_bundle_digest,
        "file_count": len(upload_file_checklist),
        "upload_file_checklist": upload_file_checklist,
        "file_statuses": file_statuses,
        "operator_steps": [
            "open the local static publication directory",
            "verify every file in upload_file_checklist is present and digest-matched",
            "manually upload index.json, README.md, hosted-bundle.json, publication-manifest.json, and checksums.json to the declared operator-controlled static host",
            "after manual upload, verify hosted files out of band before sharing the remote index digest",
        ],
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "remote_network_publish_allowed": False,
        "remote_network_fetch_allowed": False,
        "external_registry_mutation_allowed": False,
        "credentials_included": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "third_party_package_exchange_allowed": False,
        "operator_manual_action_required": True,
    }
    handoff_markdown = _static_upload_handoff_markdown(handoff_payload)
    handoff_payload["operator_handoff_markdown"] = handoff_markdown
    upload_handoff_digest = _static_upload_handoff_digest(handoff_payload)
    handoff_payload["upload_handoff_digest_sha256"] = upload_handoff_digest
    json_path, markdown_path = _static_upload_handoff_artifact_paths(vault, publisher_id, upload_handoff_digest)

    existing_json = _read_json_file(json_path) if json_path.is_file() else None
    existing_json_matches = bool(
        existing_json
        and existing_json.get("upload_handoff_digest_sha256") == upload_handoff_digest
        and _static_upload_handoff_digest(existing_json) == upload_handoff_digest
    )
    existing_markdown_matches = bool(
        markdown_path.is_file()
        and _static_text_digest(markdown_path.read_text(encoding="utf-8")) == _static_text_digest(handoff_markdown.rstrip() + "\n")
    )
    if json_path.exists() and not existing_json_matches:
        blockers.append("static_upload_handoff_json_already_present_mismatch")
    if markdown_path.exists() and not existing_markdown_matches:
        blockers.append("static_upload_handoff_markdown_already_present_mismatch")
    if write_handoff and expected_upload_handoff_digest != upload_handoff_digest:
        blockers.append("expected_upload_handoff_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    json_written = False
    markdown_written = False
    json_reused = False
    markdown_reused = False
    if write_handoff and ready:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        if existing_json_matches:
            json_reused = True
        else:
            json_path.write_text(
                json.dumps(handoff_payload, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
            json_written = True
        if existing_markdown_matches:
            markdown_reused = True
        else:
            markdown_path.write_text(handoff_markdown.rstrip() + "\n", encoding="utf-8")
            markdown_written = True

    handoff_written = bool(json_written or markdown_written)
    handoff_reused = bool(write_handoff and ready and not handoff_written and json_reused and markdown_reused)
    status = (
        "forge_marketplace_static_host_upload_handoff_written"
        if handoff_written
        else "forge_marketplace_static_host_upload_handoff_existing_matching"
        if handoff_reused or (ready and not write_handoff and existing_json_matches and existing_markdown_matches)
        else "forge_marketplace_static_host_upload_handoff_ready"
        if ready
        else "blocked_forge_marketplace_static_host_upload_handoff"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not handoff_written,
        "write_handoff_requested": bool(write_handoff),
        "upload_handoff_written": handoff_written,
        "upload_handoff_reused": handoff_reused,
        "upload_handoff_json_path": _rel(vault, json_path),
        "upload_handoff_markdown_path": _rel(vault, markdown_path),
        "upload_handoff_digest_sha256": upload_handoff_digest,
        "expected_upload_handoff_digest_sha256": expected_upload_handoff_digest or "",
        "static_publication_dir_path": publication_dir_ref,
        "static_publication_digest_sha256": source_static_publication_digest,
        "expected_static_publication_digest_sha256": expected_static_publication_digest or "",
        "remote_index_digest_sha256": source_remote_index_digest,
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "hosted_bundle_digest_sha256": source_hosted_bundle_digest,
        "expected_hosted_bundle_digest_sha256": expected_hosted_bundle_digest or "",
        "publisher_id": publisher_id,
        "file_count": len(upload_file_checklist),
        "upload_file_checklist": upload_file_checklist,
        "file_statuses": file_statuses,
        "handoff_payload": handoff_payload,
        "operator_handoff_markdown": handoff_markdown,
        "authority": _authority()
        | {
            "writes_marketplace_static_upload_handoff_artifacts": bool(handoff_written),
            "writes_marketplace_static_host_publication_artifacts": False,
            "writes_marketplace_hosted_bundle_artifact": False,
            "writes_marketplace_remote_index_artifact": False,
            "writes_marketplace_catalog": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
            "network_upload_allowed": False,
            "external_registry_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "manual_upload_handoff_ready": ready,
        "static_publication_files_present": all_files_exist,
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "remote_network_publish_allowed": False,
        "remote_network_fetch_allowed": False,
        "external_registry_mutation_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "operator-perform-manual-static-host-upload-or-live-hosted-marketplace-if-authorized"
            if ready
            else "chaser-forge-static-host-upload-handoff-repair"
        ),
    }


def build_forge_marketplace_static_host_upload_receipt(
    vault_root: str | Path,
    *,
    upload_handoff_preview: dict[str, Any] | None = None,
    upload_handoff_artifact_path: str | Path | None = None,
    expected_remote_index_digest: str | None = None,
    expected_hosted_bundle_digest: str | None = None,
    expected_static_publication_digest: str | None = None,
    expected_upload_handoff_digest: str | None = None,
    expected_upload_receipt_digest: str | None = None,
    write_receipt: bool = False,
    operator_uploaded_base_url: str = "operator-provided-static-host",
    operator_static_host_label: str = "operator-controlled static host",
    operator_receipt_statement: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or write a local receipt for an operator-confirmed manual upload.

    The receipt records an operator declaration that the handoff files were
    manually uploaded to a declared static host. It never fetches hosted files,
    uploads files, mutates an external registry, calls payment/license
    providers, or installs packages.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    source_ref = "inline_upload_handoff_preview"
    handoff_result = deepcopy(upload_handoff_preview) if isinstance(upload_handoff_preview, dict) else None
    if handoff_result is None and upload_handoff_artifact_path:
        loaded, source_ref, read_blockers = _read_static_upload_handoff_path(vault, upload_handoff_artifact_path)
        blockers.extend(read_blockers)
        handoff_result = loaded
    if handoff_result is None:
        handoff_result = build_forge_marketplace_static_host_upload_handoff(
            vault,
            expected_remote_index_digest=expected_remote_index_digest,
            expected_hosted_bundle_digest=expected_hosted_bundle_digest,
            expected_static_publication_digest=expected_static_publication_digest,
            declared_static_base_url=operator_uploaded_base_url,
            operator_static_host_label=operator_static_host_label,
            generated_at=timestamp,
        )
    if not isinstance(handoff_result, dict):
        handoff_result = {}

    handoff_payload = (
        deepcopy(handoff_result.get("handoff_payload"))
        if isinstance(handoff_result.get("handoff_payload"), dict)
        else deepcopy(handoff_result)
        if isinstance(handoff_result, dict)
        else {}
    )
    blockers.extend(str(item) for item in handoff_result.get("blockers") or [])
    if not handoff_result.get("ok", True) and handoff_result.get("record_type") != FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RECORD_TYPE:
        blockers.append("upload_handoff_not_ready_for_receipt")
    if handoff_payload.get("record_type") != FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RECORD_TYPE:
        blockers.append("upload_handoff_record_type_mismatch")
    if handoff_payload.get("schema_version") != FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SCHEMA_VERSION:
        blockers.append("upload_handoff_schema_version_mismatch")

    source_remote_index_digest = str(
        handoff_result.get("remote_index_digest_sha256")
        or handoff_payload.get("remote_index_digest_sha256")
        or ""
    )
    source_hosted_bundle_digest = str(
        handoff_result.get("hosted_bundle_digest_sha256")
        or handoff_payload.get("hosted_bundle_digest_sha256")
        or ""
    )
    source_static_publication_digest = str(
        handoff_result.get("static_publication_digest_sha256")
        or handoff_payload.get("static_publication_digest_sha256")
        or ""
    )
    source_upload_handoff_digest = str(
        handoff_result.get("upload_handoff_digest_sha256")
        or handoff_payload.get("upload_handoff_digest_sha256")
        or ""
    )
    if source_upload_handoff_digest:
        recomputed_handoff_digest = _static_upload_handoff_digest(handoff_payload)
        if recomputed_handoff_digest != source_upload_handoff_digest:
            blockers.append("upload_handoff_digest_mismatch")
    else:
        blockers.append("upload_handoff_digest_missing")
    if expected_remote_index_digest and expected_remote_index_digest != source_remote_index_digest:
        blockers.append("expected_remote_index_digest_mismatch")
    if expected_hosted_bundle_digest and expected_hosted_bundle_digest != source_hosted_bundle_digest:
        blockers.append("expected_hosted_bundle_digest_mismatch")
    if expected_static_publication_digest and expected_static_publication_digest != source_static_publication_digest:
        blockers.append("expected_static_publication_digest_mismatch")
    if expected_upload_handoff_digest and expected_upload_handoff_digest != source_upload_handoff_digest:
        blockers.append("expected_upload_handoff_digest_mismatch")

    for key, blocker in (
        ("network_upload_allowed", "upload_handoff_network_upload_authority_unexpected"),
        ("remote_network_publish_allowed", "upload_handoff_remote_publish_authority_unexpected"),
        ("remote_network_fetch_allowed", "upload_handoff_remote_fetch_authority_unexpected"),
        ("external_registry_mutation_allowed", "upload_handoff_external_registry_authority_unexpected"),
        ("payment_mutation_allowed", "upload_handoff_payment_authority_unexpected"),
        ("license_checkout_allowed", "upload_handoff_license_authority_unexpected"),
        ("package_install_allowed", "upload_handoff_install_authority_unexpected"),
    ):
        if handoff_payload.get(key) is True:
            blockers.append(blocker)

    hosted_base_url = (
        operator_uploaded_base_url
        or str(handoff_payload.get("declared_static_base_url") or "")
        or "operator-provided-static-host"
    )
    if write_receipt and not hosted_base_url:
        blockers.append("operator_uploaded_base_url_required_for_receipt_write")
    publisher_id = str(handoff_payload.get("publisher_id") or "local-operator")
    checklist = [item for item in handoff_payload.get("upload_file_checklist") or [] if isinstance(item, dict)]
    if not checklist:
        blockers.append("upload_handoff_file_checklist_missing")
    source_file_statuses = [item for item in handoff_payload.get("file_statuses") or [] if isinstance(item, dict)]
    if (
        write_receipt
        and source_file_statuses
        and any(item.get("ready_for_manual_upload") is not True for item in source_file_statuses)
    ):
        blockers.append("upload_handoff_files_not_ready_for_manual_upload")

    hosted_file_receipts = [
        {
            "path": str(item.get("path") or ""),
            "hosted_url": _hosted_url(hosted_base_url, str(item.get("path") or "")),
            "expected_digest_sha256": str(item.get("digest_sha256") or item.get("expected_digest_sha256") or ""),
            "size_bytes": item.get("size_bytes") or 0,
            "operator_declared_uploaded": bool(write_receipt),
            "network_fetch_performed": False,
            "network_fetch_allowed": False,
            "network_fetch_verified": False,
            "observed_digest_sha256": "",
        }
        for item in sorted(checklist, key=lambda record: str(record.get("path") or ""))
    ]
    required_statement = _required_static_upload_receipt_statement(
        publisher_id=publisher_id,
        remote_index_digest=source_remote_index_digest,
        hosted_bundle_digest=source_hosted_bundle_digest,
        static_publication_digest=source_static_publication_digest,
        upload_handoff_digest=source_upload_handoff_digest,
        hosted_base_url=hosted_base_url,
    )
    statement_matches = bool(operator_receipt_statement and operator_receipt_statement == required_statement)
    if write_receipt and not statement_matches:
        blockers.append("operator_receipt_statement_required_or_mismatched")

    receipt_payload = {
        "record_type": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SCHEMA_VERSION,
        "generated_at": timestamp,
        "updated_at": timestamp,
        "surface": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_API_METHOD,
        "write_api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_WRITE_API_METHOD,
        "publisher_id": publisher_id,
        "operator_static_host_label": operator_static_host_label,
        "operator_uploaded_base_url": hosted_base_url,
        "source_upload_handoff_artifact_path": source_ref
        if source_ref != "inline_upload_handoff_preview"
        else str(handoff_result.get("upload_handoff_json_path") or ""),
        "upload_handoff_digest_sha256": source_upload_handoff_digest,
        "static_publication_digest_sha256": source_static_publication_digest,
        "remote_index_digest_sha256": source_remote_index_digest,
        "hosted_bundle_digest_sha256": source_hosted_bundle_digest,
        "file_count": len(hosted_file_receipts),
        "hosted_file_receipts": hosted_file_receipts,
        "source_handoff_file_statuses": source_file_statuses,
        "required_operator_receipt_statement": required_statement,
        "operator_receipt_statement": operator_receipt_statement if statement_matches else "",
        "operator_receipt_statement_sha256": _static_text_digest(operator_receipt_statement) if statement_matches else "",
        "operator_receipt_recorded": bool(write_receipt and statement_matches),
        "operator_manual_upload_claim_recorded": bool(write_receipt and statement_matches),
        "operator_manual_upload_claim_only": True,
        "hosted_upload_verified_by_network_fetch": False,
        "network_fetch_performed": False,
        "network_fetch_allowed": False,
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "remote_network_publish_allowed": False,
        "external_registry_mutation_allowed": False,
        "credentials_included": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "third_party_package_exchange_allowed": False,
        "operator_manual_action_required": True,
    }
    upload_receipt_digest = _static_upload_receipt_digest(receipt_payload)
    receipt_payload["upload_receipt_digest_sha256"] = upload_receipt_digest
    receipt_markdown = _static_upload_receipt_markdown(receipt_payload)
    receipt_payload["operator_receipt_markdown"] = receipt_markdown
    json_path, markdown_path = _static_upload_receipt_artifact_paths(vault, publisher_id, upload_receipt_digest)

    existing_json = _read_json_file(json_path) if json_path.is_file() else None
    existing_json_matches = bool(
        existing_json
        and existing_json.get("upload_receipt_digest_sha256") == upload_receipt_digest
        and _static_upload_receipt_digest(existing_json) == upload_receipt_digest
        and existing_json.get("operator_receipt_statement") == required_statement
    )
    existing_markdown_matches = bool(
        markdown_path.is_file()
        and _static_text_digest(markdown_path.read_text(encoding="utf-8")) == _static_text_digest(receipt_markdown.rstrip() + "\n")
    )
    if json_path.exists() and not existing_json_matches:
        blockers.append("static_upload_receipt_json_already_present_mismatch")
    if markdown_path.exists() and not existing_markdown_matches:
        blockers.append("static_upload_receipt_markdown_already_present_mismatch")
    if write_receipt and expected_upload_receipt_digest != upload_receipt_digest:
        blockers.append("expected_upload_receipt_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    json_written = False
    markdown_written = False
    json_reused = False
    markdown_reused = False
    if write_receipt and ready:
        receipt_payload["receipt_written_at"] = timestamp
        json_path.parent.mkdir(parents=True, exist_ok=True)
        if existing_json_matches:
            json_reused = True
        else:
            json_path.write_text(
                json.dumps(receipt_payload, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
            json_written = True
        if existing_markdown_matches:
            markdown_reused = True
        else:
            markdown_path.write_text(receipt_markdown.rstrip() + "\n", encoding="utf-8")
            markdown_written = True

    receipt_written = bool(json_written or markdown_written)
    receipt_reused = bool(write_receipt and ready and not receipt_written and json_reused and markdown_reused)
    status = (
        "forge_marketplace_static_host_upload_receipt_written"
        if receipt_written
        else "forge_marketplace_static_host_upload_receipt_existing_matching"
        if receipt_reused or (ready and not write_receipt and existing_json_matches and existing_markdown_matches)
        else "forge_marketplace_static_host_upload_receipt_ready"
        if ready
        else "blocked_forge_marketplace_static_host_upload_receipt"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not receipt_written,
        "write_receipt_requested": bool(write_receipt),
        "upload_receipt_written": receipt_written,
        "upload_receipt_reused": receipt_reused,
        "upload_receipt_json_path": _rel(vault, json_path),
        "upload_receipt_markdown_path": _rel(vault, markdown_path),
        "upload_receipt_digest_sha256": upload_receipt_digest,
        "expected_upload_receipt_digest_sha256": expected_upload_receipt_digest or "",
        "source_upload_handoff_artifact_path": receipt_payload["source_upload_handoff_artifact_path"],
        "upload_handoff_digest_sha256": source_upload_handoff_digest,
        "expected_upload_handoff_digest_sha256": expected_upload_handoff_digest or "",
        "static_publication_digest_sha256": source_static_publication_digest,
        "expected_static_publication_digest_sha256": expected_static_publication_digest or "",
        "remote_index_digest_sha256": source_remote_index_digest,
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "hosted_bundle_digest_sha256": source_hosted_bundle_digest,
        "expected_hosted_bundle_digest_sha256": expected_hosted_bundle_digest or "",
        "publisher_id": publisher_id,
        "operator_uploaded_base_url": hosted_base_url,
        "operator_static_host_label": operator_static_host_label,
        "file_count": len(hosted_file_receipts),
        "hosted_file_receipts": hosted_file_receipts,
        "required_operator_receipt_statement": required_statement,
        "operator_receipt_statement_recorded": statement_matches if write_receipt else False,
        "receipt_payload": receipt_payload,
        "operator_receipt_markdown": receipt_markdown,
        "authority": _authority()
        | {
            "writes_marketplace_static_upload_receipt_artifacts": bool(receipt_written),
            "writes_marketplace_static_upload_handoff_artifacts": False,
            "writes_marketplace_static_host_publication_artifacts": False,
            "writes_marketplace_hosted_bundle_artifact": False,
            "writes_marketplace_remote_index_artifact": False,
            "writes_marketplace_catalog": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
            "network_upload_allowed": False,
            "external_registry_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "manual_upload_receipt_ready": ready,
        "operator_manual_upload_claim_recorded": bool(write_receipt and statement_matches and ready),
        "operator_manual_upload_claim_only": True,
        "hosted_upload_verified_by_network_fetch": False,
        "network_fetch_performed": False,
        "network_fetch_allowed": False,
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "remote_network_publish_allowed": False,
        "external_registry_mutation_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "operator-activate-live-hosted-marketplace-if-authorized-or-register-published-static-index"
            if ready
            else "chaser-forge-static-host-upload-receipt-repair"
        ),
    }


def build_forge_marketplace_published_static_index_registration(
    vault_root: str | Path,
    *,
    upload_receipt_preview: dict[str, Any] | None = None,
    upload_receipt_artifact_path: str | Path | None = None,
    expected_remote_index_digest: str | None = None,
    expected_hosted_bundle_digest: str | None = None,
    expected_static_publication_digest: str | None = None,
    expected_upload_handoff_digest: str | None = None,
    expected_upload_receipt_digest: str | None = None,
    expected_published_static_index_registration_digest: str | None = None,
    write_registration: bool = False,
    operator_published_static_index_url: str = "https://example.invalid/chaser-forge/index.json",
    operator_registration_statement: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or write a local registration for an operator-published static index.

    This records the operator-declared public `index.json` URL after the local
    upload receipt lane. It validates source digests and the URL shape, but it
    never fetches the URL, uploads files, mutates an external registry, calls
    payment/license providers, or installs packages.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    source_ref = "inline_upload_receipt_preview"
    receipt_result = deepcopy(upload_receipt_preview) if isinstance(upload_receipt_preview, dict) else None
    if receipt_result is None and upload_receipt_artifact_path:
        loaded, source_ref, read_blockers = _read_static_upload_receipt_path(vault, upload_receipt_artifact_path)
        blockers.extend(read_blockers)
        receipt_result = loaded
    if receipt_result is None:
        receipt_result = build_forge_marketplace_static_host_upload_receipt(
            vault,
            expected_remote_index_digest=expected_remote_index_digest,
            expected_hosted_bundle_digest=expected_hosted_bundle_digest,
            expected_static_publication_digest=expected_static_publication_digest,
            expected_upload_handoff_digest=expected_upload_handoff_digest,
            operator_uploaded_base_url="https://example.invalid/chaser-forge",
            generated_at=timestamp,
        )
    if not isinstance(receipt_result, dict):
        receipt_result = {}

    receipt_payload = (
        deepcopy(receipt_result.get("receipt_payload"))
        if isinstance(receipt_result.get("receipt_payload"), dict)
        else deepcopy(receipt_result)
        if isinstance(receipt_result, dict)
        else {}
    )
    blockers.extend(str(item) for item in receipt_result.get("blockers") or [])
    if receipt_payload.get("record_type") != FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_RECORD_TYPE:
        blockers.append("upload_receipt_record_type_mismatch")
    if receipt_payload.get("schema_version") != FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SCHEMA_VERSION:
        blockers.append("upload_receipt_schema_version_mismatch")

    source_remote_index_digest = str(
        receipt_result.get("remote_index_digest_sha256")
        or receipt_payload.get("remote_index_digest_sha256")
        or ""
    )
    source_hosted_bundle_digest = str(
        receipt_result.get("hosted_bundle_digest_sha256")
        or receipt_payload.get("hosted_bundle_digest_sha256")
        or ""
    )
    source_static_publication_digest = str(
        receipt_result.get("static_publication_digest_sha256")
        or receipt_payload.get("static_publication_digest_sha256")
        or ""
    )
    source_upload_handoff_digest = str(
        receipt_result.get("upload_handoff_digest_sha256")
        or receipt_payload.get("upload_handoff_digest_sha256")
        or ""
    )
    source_upload_receipt_digest = str(
        receipt_result.get("upload_receipt_digest_sha256")
        or receipt_payload.get("upload_receipt_digest_sha256")
        or ""
    )
    if source_upload_receipt_digest:
        recomputed_receipt_digest = _static_upload_receipt_digest(receipt_payload)
        if recomputed_receipt_digest != source_upload_receipt_digest:
            blockers.append("upload_receipt_digest_mismatch")
    else:
        blockers.append("upload_receipt_digest_missing")

    if expected_remote_index_digest and expected_remote_index_digest != source_remote_index_digest:
        blockers.append("expected_remote_index_digest_mismatch")
    if expected_hosted_bundle_digest and expected_hosted_bundle_digest != source_hosted_bundle_digest:
        blockers.append("expected_hosted_bundle_digest_mismatch")
    if expected_static_publication_digest and expected_static_publication_digest != source_static_publication_digest:
        blockers.append("expected_static_publication_digest_mismatch")
    if expected_upload_handoff_digest and expected_upload_handoff_digest != source_upload_handoff_digest:
        blockers.append("expected_upload_handoff_digest_mismatch")
    if expected_upload_receipt_digest and expected_upload_receipt_digest != source_upload_receipt_digest:
        blockers.append("expected_upload_receipt_digest_mismatch")
    if write_registration and receipt_payload.get("operator_manual_upload_claim_recorded") is not True:
        blockers.append("upload_receipt_operator_manual_claim_required_for_registration_write")

    for key, blocker in (
        ("network_fetch_allowed", "upload_receipt_network_fetch_authority_unexpected"),
        ("network_upload_allowed", "upload_receipt_network_upload_authority_unexpected"),
        ("remote_network_publish_allowed", "upload_receipt_remote_publish_authority_unexpected"),
        ("external_registry_mutation_allowed", "upload_receipt_external_registry_authority_unexpected"),
        ("payment_mutation_allowed", "upload_receipt_payment_authority_unexpected"),
        ("license_checkout_allowed", "upload_receipt_license_authority_unexpected"),
        ("package_install_allowed", "upload_receipt_install_authority_unexpected"),
    ):
        if receipt_payload.get(key) is True:
            blockers.append(blocker)

    published_url = str(operator_published_static_index_url or "").strip()
    blockers.extend(_published_static_index_url_blockers(published_url))
    publisher_id = str(receipt_payload.get("publisher_id") or "local-operator")
    required_statement = _required_published_static_index_registration_statement(
        publisher_id=publisher_id,
        published_static_index_url=published_url,
        remote_index_digest=source_remote_index_digest,
        hosted_bundle_digest=source_hosted_bundle_digest,
        static_publication_digest=source_static_publication_digest,
        upload_handoff_digest=source_upload_handoff_digest,
        upload_receipt_digest=source_upload_receipt_digest,
    )
    statement_matches = bool(operator_registration_statement and operator_registration_statement == required_statement)
    if write_registration and not statement_matches:
        blockers.append("operator_registration_statement_required_or_mismatched")

    registration_payload = {
        "record_type": FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SCHEMA_VERSION,
        "generated_at": timestamp,
        "updated_at": timestamp,
        "surface": FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_API_METHOD,
        "write_api_method": FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_WRITE_API_METHOD,
        "publisher_id": publisher_id,
        "operator_published_static_index_url": published_url,
        "source_upload_receipt_artifact_path": source_ref
        if source_ref != "inline_upload_receipt_preview"
        else str(receipt_result.get("upload_receipt_json_path") or ""),
        "source_operator_uploaded_base_url": str(receipt_payload.get("operator_uploaded_base_url") or ""),
        "remote_index_digest_sha256": source_remote_index_digest,
        "hosted_bundle_digest_sha256": source_hosted_bundle_digest,
        "static_publication_digest_sha256": source_static_publication_digest,
        "upload_handoff_digest_sha256": source_upload_handoff_digest,
        "upload_receipt_digest_sha256": source_upload_receipt_digest,
        "source_receipt_hosted_file_receipts": [
            deepcopy(item) for item in receipt_payload.get("hosted_file_receipts") or [] if isinstance(item, dict)
        ],
        "required_operator_registration_statement": required_statement,
        "operator_registration_statement": operator_registration_statement if statement_matches else "",
        "operator_registration_statement_sha256": _static_text_digest(operator_registration_statement)
        if statement_matches
        else "",
        "operator_registration_recorded": bool(write_registration and statement_matches),
        "operator_declared_published_index_registered": bool(write_registration and statement_matches),
        "operator_registration_only": True,
        "live_url_verified": False,
        "hosted_url_verified_by_network_fetch": False,
        "network_fetch_performed": False,
        "network_fetch_allowed": False,
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "remote_network_publish_allowed": False,
        "external_registry_mutation_performed": False,
        "external_registry_mutation_allowed": False,
        "credentials_included": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "third_party_package_exchange_allowed": False,
        "operator_manual_action_required": True,
    }
    registration_digest = _published_static_index_registration_digest(registration_payload)
    registration_payload["published_static_index_registration_digest_sha256"] = registration_digest
    registration_markdown = _published_static_index_registration_markdown(registration_payload)
    registration_payload["operator_registration_markdown"] = registration_markdown
    json_path, markdown_path = _published_static_index_registration_artifact_paths(
        vault,
        publisher_id,
        registration_digest,
    )

    existing_json = _read_json_file(json_path) if json_path.is_file() else None
    existing_json_matches = bool(
        existing_json
        and existing_json.get("published_static_index_registration_digest_sha256") == registration_digest
        and _published_static_index_registration_digest(existing_json) == registration_digest
        and existing_json.get("operator_registration_statement") == required_statement
    )
    existing_markdown_matches = bool(
        markdown_path.is_file()
        and _static_text_digest(markdown_path.read_text(encoding="utf-8"))
        == _static_text_digest(registration_markdown.rstrip() + "\n")
    )
    if json_path.exists() and not existing_json_matches:
        blockers.append("published_static_index_registration_json_already_present_mismatch")
    if markdown_path.exists() and not existing_markdown_matches:
        blockers.append("published_static_index_registration_markdown_already_present_mismatch")
    if (
        write_registration
        and expected_published_static_index_registration_digest != registration_digest
    ):
        blockers.append("expected_published_static_index_registration_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    json_written = False
    markdown_written = False
    json_reused = False
    markdown_reused = False
    if write_registration and ready:
        registration_payload["registration_written_at"] = timestamp
        json_path.parent.mkdir(parents=True, exist_ok=True)
        if existing_json_matches:
            json_reused = True
        else:
            json_path.write_text(
                json.dumps(registration_payload, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
            json_written = True
        if existing_markdown_matches:
            markdown_reused = True
        else:
            markdown_path.write_text(registration_markdown.rstrip() + "\n", encoding="utf-8")
            markdown_written = True

    registration_written = bool(json_written or markdown_written)
    registration_reused = bool(write_registration and ready and not registration_written and json_reused and markdown_reused)
    status = (
        "forge_marketplace_published_static_index_registration_written"
        if registration_written
        else "forge_marketplace_published_static_index_registration_existing_matching"
        if registration_reused or (ready and not write_registration and existing_json_matches and existing_markdown_matches)
        else "forge_marketplace_published_static_index_registration_ready"
        if ready
        else "blocked_forge_marketplace_published_static_index_registration"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not registration_written,
        "write_registration_requested": bool(write_registration),
        "published_static_index_registration_written": registration_written,
        "published_static_index_registration_reused": registration_reused,
        "published_static_index_registration_json_path": _rel(vault, json_path),
        "published_static_index_registration_markdown_path": _rel(vault, markdown_path),
        "published_static_index_registration_digest_sha256": registration_digest,
        "expected_published_static_index_registration_digest_sha256": (
            expected_published_static_index_registration_digest or ""
        ),
        "operator_published_static_index_url": published_url,
        "source_upload_receipt_artifact_path": registration_payload["source_upload_receipt_artifact_path"],
        "upload_receipt_digest_sha256": source_upload_receipt_digest,
        "expected_upload_receipt_digest_sha256": expected_upload_receipt_digest or "",
        "upload_handoff_digest_sha256": source_upload_handoff_digest,
        "expected_upload_handoff_digest_sha256": expected_upload_handoff_digest or "",
        "static_publication_digest_sha256": source_static_publication_digest,
        "expected_static_publication_digest_sha256": expected_static_publication_digest or "",
        "remote_index_digest_sha256": source_remote_index_digest,
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "hosted_bundle_digest_sha256": source_hosted_bundle_digest,
        "expected_hosted_bundle_digest_sha256": expected_hosted_bundle_digest or "",
        "publisher_id": publisher_id,
        "required_operator_registration_statement": required_statement,
        "operator_registration_statement_recorded": statement_matches if write_registration else False,
        "registration_payload": registration_payload,
        "operator_registration_markdown": registration_markdown,
        "authority": _authority()
        | {
            "writes_marketplace_published_static_index_registration_artifacts": bool(registration_written),
            "writes_marketplace_static_upload_receipt_artifacts": False,
            "writes_marketplace_static_upload_handoff_artifacts": False,
            "writes_marketplace_static_host_publication_artifacts": False,
            "writes_marketplace_hosted_bundle_artifact": False,
            "writes_marketplace_remote_index_artifact": False,
            "writes_marketplace_catalog": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
            "network_upload_allowed": False,
            "external_registry_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "published_static_index_registration_ready": ready,
        "operator_declared_published_index_registered": bool(write_registration and statement_matches and ready),
        "operator_registration_only": True,
        "live_url_verified": False,
        "hosted_url_verified_by_network_fetch": False,
        "network_fetch_performed": False,
        "network_fetch_allowed": False,
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "remote_network_publish_allowed": False,
        "external_registry_mutation_performed": False,
        "external_registry_mutation_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "operator-authorize-live-url-fetch-verification-or-external-registry-publication"
            if ready
            else "chaser-forge-published-static-index-registration-repair"
        ),
    }


def build_forge_marketplace_live_index_input_prefill(
    vault_root: str | Path,
    *,
    static_publication_preview: dict[str, Any] | None = None,
    materialize_static_publication: bool = False,
    write_prefill: bool = False,
    expected_prefill_digest: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Create a local prefilled live `index.json` input packet.

    The prefill writes only local operator packet artifacts when requested. It
    may also materialize the existing digest-gated static publication proof
    files, but it never fetches the future URL, uploads files, mutates an
    external registry, calls providers, or installs packages.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    warnings: list[str] = []

    publication_source = "provided_preview" if isinstance(static_publication_preview, dict) else "local_builder"
    publication_preview = (
        deepcopy(static_publication_preview)
        if isinstance(static_publication_preview, dict)
        else build_forge_marketplace_static_host_publication(vault, generated_at=timestamp)
    )
    blockers.extend(str(item) for item in publication_preview.get("blockers") or [])
    if not publication_preview.get("ok"):
        blockers.append("static_publication_preview_not_ready")

    publication_result = publication_preview
    if materialize_static_publication and publication_preview.get("ok"):
        if isinstance(static_publication_preview, dict):
            publication_dir, path_blocker = _resolve_vault_child(
                vault,
                str(publication_preview.get("static_publication_dir_path") or ""),
            )
            if path_blocker:
                blockers.append("static_publication_dir_outside_vault_root")
            inspected = _inspect_static_publication_dir(vault, publication_dir)
            if inspected.get("present"):
                publication_result = publication_preview
            else:
                blockers.append("provided_static_publication_preview_not_materialized")
        else:
            publication_result = build_forge_marketplace_static_host_publication(
                vault,
                expected_remote_index_digest=str(publication_preview.get("remote_index_digest_sha256") or ""),
                expected_hosted_bundle_digest=str(publication_preview.get("hosted_bundle_digest_sha256") or ""),
                expected_static_publication_digest=str(
                    publication_preview.get("static_publication_digest_sha256") or ""
                ),
                write_publication=True,
                generated_at=timestamp,
            )
            blockers.extend(str(item) for item in publication_result.get("blockers") or [])
            if not publication_result.get("ok"):
                blockers.append("static_publication_materialization_failed")

    publication_dir_ref = str(publication_result.get("static_publication_dir_path") or "")
    publication_dir, publication_path_blocker = _resolve_vault_child(vault, publication_dir_ref)
    if publication_path_blocker:
        blockers.append("static_publication_dir_outside_vault_root")
    local_publication = _inspect_static_publication_dir(vault, publication_dir)

    index_digest = ""
    for item in publication_result.get("files") or []:
        if isinstance(item, dict) and item.get("path") == "index.json":
            index_digest = str(item.get("digest_sha256") or "")
            break
    if not index_digest:
        index_digest = str(local_publication.get("index_sha256") or "")
    if not index_digest:
        blockers.append("local_index_sha256_unavailable")

    public_index_url = "https://<official-chaseos-domain>/chaser-forge/index.json"
    hosted_base_url = "https://<official-chaseos-domain>/chaser-forge"
    uploaded_files = [
        "index.json",
        "README.md",
        "hosted-bundle.json",
        "publication-manifest.json",
        "checksums.json",
    ]
    packet_payload = {
        "packet_type": "chaser_forge_live_index_json_verification_input",
        "schema_version": "chaser_forge.live_index_json_input.v1",
        "public_index_url": public_index_url,
        "hosted_base_url": hosted_base_url,
        "host_label": "official ChaseOS domain pending",
        "local_static_publication_dir": publication_dir_ref,
        "local_index_sha256": index_digest,
        "uploaded_files": uploaded_files,
        "operator_upload_confirmation": (
            "PENDING: the local Chaser Forge static publication files are staged locally, "
            "but no public-domain upload has been confirmed yet."
        ),
        "operator_fetch_approval_statement": (
            "PENDING: provide the real public index.json URL and approve one bounded fetch "
            "after the official ChaseOS domain is purchased and the static files are uploaded. "
            "Do not approve upload, external registry mutation, package install, payment/license "
            "mutation, credential use, provider/model calls, Agent Bus dispatch, or protected-core mutation."
        ),
        "notes": (
            "Local prefill generated from the current static publication candidate. "
            "Domain, upload, and live fetch verification remain deferred."
        ),
    }
    prefill_payload = {
        "record_type": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SCHEMA_VERSION,
        "surface": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_API_METHOD,
        "write_api_method": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_WRITE_API_METHOD,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "prefill_status": "DOMAIN DEFERRED / LOCAL PREFILL",
        "publication_source": publication_source,
        "packet_payload": packet_payload,
        "static_publication": local_publication,
        "static_publication_preview": publication_result,
        "domain_purchase_deferred": True,
        "ready_for_live_verification": False,
        "network_fetch_performed": False,
        "network_fetch_allowed": False,
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "external_registry_mutation_performed": False,
        "external_registry_mutation_allowed": False,
        "credentials_included": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "third_party_package_exchange_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "remaining_operator_inputs": [
            "purchase and configure the official ChaseOS domain",
            "upload the five static publication files to the public hosted_base_url",
            "replace public_index_url and hosted_base_url with the real HTTPS domain paths",
            "replace host_label with the real host/domain label",
            "replace operator_upload_confirmation with a real upload confirmation",
            "replace operator_fetch_approval_statement with exact approval for one bounded future fetch",
        ],
    }
    prefill_digest = _live_index_input_prefill_digest(prefill_payload)
    prefill_payload["prefill_digest_sha256"] = prefill_digest
    json_path, markdown_path = _live_index_input_prefill_artifact_paths(vault, prefill_digest)
    prefill_payload["prefilled_input_packet_json_path"] = _rel(vault, json_path)
    prefill_payload["prefill_markdown_path"] = _rel(vault, markdown_path)
    prefill_payload["prefill_markdown"] = _live_index_input_prefill_markdown(prefill_payload)

    try:
        json_path.relative_to(vault)
        markdown_path.relative_to(vault)
    except ValueError:
        blockers.append("live_index_input_prefill_path_outside_vault_root")

    packet_text = json.dumps(packet_payload, indent=2, ensure_ascii=True, sort_keys=True, default=str) + "\n"
    markdown_text = str(prefill_payload.get("prefill_markdown") or "").rstrip() + "\n"
    existing_json = _read_json_file(json_path) if json_path.is_file() else None
    existing_markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.is_file() else None
    existing_matches = (
        isinstance(existing_json, dict)
        and _sha256_payload(existing_json) == _sha256_payload(packet_payload)
        and existing_markdown == markdown_text
    )
    if json_path.is_file() and not existing_matches:
        blockers.append("live_index_input_prefill_json_already_present_mismatch")
    if markdown_path.is_file() and not existing_matches:
        blockers.append("live_index_input_prefill_markdown_already_present_mismatch")
    if write_prefill and expected_prefill_digest != prefill_digest:
        blockers.append("expected_prefill_digest_required_or_mismatched")
    if write_prefill and not materialize_static_publication and not local_publication.get("present"):
        blockers.append("static_publication_must_be_materialized_for_prefill_write")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    prefill_written = False
    prefill_reused = False
    if write_prefill and ready:
        if existing_matches:
            prefill_reused = True
        else:
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(packet_text, encoding="utf-8")
            markdown_path.write_text(markdown_text, encoding="utf-8")
            prefill_written = True

    status = (
        "forge_marketplace_live_index_input_prefill_written"
        if prefill_written
        else "forge_marketplace_live_index_input_prefill_existing_matching"
        if prefill_reused or existing_matches
        else "forge_marketplace_live_index_input_prefill_ready"
        if ready
        else "blocked_forge_marketplace_live_index_input_prefill"
    )
    return prefill_payload | {
        "ok": ready,
        "status": status,
        "preview_only": not prefill_written,
        "write_prefill_requested": bool(write_prefill),
        "materialize_static_publication_requested": bool(materialize_static_publication),
        "static_publication_materialized": bool(publication_result.get("static_publication_written"))
        or bool(publication_result.get("static_publication_reused"))
        or bool(local_publication.get("present")),
        "prefill_written": prefill_written,
        "prefill_reused": prefill_reused,
        "authority": _authority()
        | {
            "writes_marketplace_live_index_input_prefill_artifacts": bool(prefill_written),
            "writes_marketplace_static_host_publication_artifacts": bool(
                publication_result.get("static_publication_written")
            ),
            "writes_marketplace_live_index_input_readiness_artifacts": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_fetch_allowed": False,
            "remote_network_publish_allowed": False,
            "network_upload_allowed": False,
            "external_registry_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
        },
        "warnings": warnings,
        "blockers": blockers,
        "next_recommended_pass": (
            "operator-purchase-domain-upload-static-files-and-finalize-live-index-input-packet"
            if ready
            else "chaser-forge-live-index-input-prefill-repair"
        ),
    }


def build_forge_marketplace_live_index_input_readiness(
    vault_root: str | Path,
    *,
    input_packet_path: str | Path | None = None,
    handover_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Inspect whether the future live `index.json` verification input is ready.

    This is a read-only local readiness surface. It reads the operator packet
    template and handover note, inspects local static publication files if
    available, and never fetches a URL, uploads files, mutates registries, calls
    payment/license providers, or installs packages.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    warnings: list[str] = []

    packet_ref = input_packet_path or FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PACKET_TEMPLATE_RELATIVE_PATH
    packet_path, packet_path_blocker = _resolve_vault_child(vault, packet_ref)
    packet_payload: dict[str, Any] = {}
    if packet_path_blocker:
        blockers.append("live_index_input_packet_path_outside_vault_root")
    elif not packet_path.is_file():
        blockers.append("live_index_input_packet_template_missing")
    else:
        loaded = _read_json_file(packet_path)
        if loaded is None:
            blockers.append("live_index_input_packet_template_unreadable")
        else:
            packet_payload = loaded

    handover_ref = handover_path or FORGE_MARKETPLACE_LIVE_INDEX_INPUT_HANDOVER_RELATIVE_PATH
    handover_file, handover_path_blocker = _resolve_vault_child(vault, handover_ref)
    handover_text = ""
    if handover_path_blocker:
        warnings.append("live_index_input_handover_path_outside_vault_root")
    elif handover_file.is_file():
        try:
            handover_text = handover_file.read_text(encoding="utf-8")
        except OSError:
            warnings.append("live_index_input_handover_unreadable")
    else:
        warnings.append("live_index_input_handover_missing")

    handover_lower = handover_text.lower()
    domain_purchase_deferred = bool(
        "blocked on domain purchase" in handover_lower
        or "official chaseos domain is purchased" in handover_lower
        or "domain is purchased" in handover_lower
    )
    if domain_purchase_deferred:
        blockers.append("domain_purchase_deferred_until_official_domain_is_purchased")

    public_index_url = str(packet_payload.get("public_index_url") or "").strip()
    hosted_base_url = str(packet_payload.get("hosted_base_url") or "").strip()
    host_label = str(packet_payload.get("host_label") or "").strip()
    local_publication_dir_ref = str(packet_payload.get("local_static_publication_dir") or "").strip()
    local_index_sha256 = str(packet_payload.get("local_index_sha256") or "").strip()
    upload_confirmation = str(packet_payload.get("operator_upload_confirmation") or "").strip()
    fetch_approval_statement = str(packet_payload.get("operator_fetch_approval_statement") or "").strip()
    uploaded_files = [
        str(item).strip()
        for item in packet_payload.get("uploaded_files") or []
        if str(item).strip()
    ]

    field_values = {
        "public_index_url": public_index_url,
        "hosted_base_url": hosted_base_url,
        "host_label": host_label,
        "local_static_publication_dir": local_publication_dir_ref,
        "local_index_sha256": local_index_sha256,
        "operator_upload_confirmation": upload_confirmation,
        "operator_fetch_approval_statement": fetch_approval_statement,
    }
    placeholder_fields = [
        key for key, value in field_values.items() if _live_index_value_unfilled(value)
    ]

    public_index_url_supplied = "public_index_url" not in placeholder_fields
    if public_index_url_supplied:
        blockers.extend(_published_static_index_url_blockers(public_index_url))
    else:
        blockers.append("public_index_url_required")

    hosted_base_url_supplied = "hosted_base_url" not in placeholder_fields
    if hosted_base_url_supplied:
        blockers.extend(_hosted_base_url_blockers(hosted_base_url))
    else:
        blockers.append("hosted_base_url_required")

    if public_index_url_supplied and hosted_base_url_supplied:
        parent_url = _live_index_parent_url(public_index_url)
        if parent_url and parent_url != hosted_base_url.rstrip("/"):
            blockers.append("hosted_base_url_must_match_public_index_url_parent")

    if "host_label" in placeholder_fields:
        blockers.append("host_label_required")

    required_uploaded_files = list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES)
    uploaded_file_set = set(uploaded_files)
    missing_uploaded_file_names = sorted(set(required_uploaded_files) - uploaded_file_set)
    if missing_uploaded_file_names:
        blockers.append("uploaded_files_required_list_incomplete")

    local_publication_dir_supplied = "local_static_publication_dir" not in placeholder_fields
    local_publication_source = "input_packet" if local_publication_dir_supplied else "latest_local_candidate"
    if local_publication_dir_supplied:
        local_publication_dir, path_blocker = _resolve_vault_child(vault, local_publication_dir_ref)
        if path_blocker:
            blockers.append("local_static_publication_dir_outside_vault_root")
    else:
        local_publication_dir = _latest_static_publication_dir(vault)
        blockers.append("local_static_publication_dir_required")
    local_publication = _inspect_static_publication_dir(vault, local_publication_dir)
    blockers.extend(str(item) for item in local_publication.get("blockers") or [])

    local_index_sha256_supplied = "local_index_sha256" not in placeholder_fields
    local_index_sha256_valid_shape = bool(
        len(local_index_sha256) == 64 and all(char in "0123456789abcdefABCDEF" for char in local_index_sha256)
    )
    candidate_index_sha256 = str(local_publication.get("index_sha256") or "")
    if not local_index_sha256_supplied:
        blockers.append("local_index_sha256_required")
    elif not local_index_sha256_valid_shape:
        blockers.append("local_index_sha256_must_be_sha256_hex")
    elif candidate_index_sha256 and local_index_sha256.lower() != candidate_index_sha256.lower():
        blockers.append("local_index_sha256_mismatch")

    if "operator_upload_confirmation" in placeholder_fields:
        blockers.append("operator_upload_confirmation_required")
    elif "uploaded" not in upload_confirmation.lower():
        blockers.append("operator_upload_confirmation_must_confirm_upload")

    future_fetch_approval_statement_present = "operator_fetch_approval_statement" not in placeholder_fields
    if not future_fetch_approval_statement_present:
        blockers.append("operator_fetch_approval_statement_required")
    else:
        if public_index_url_supplied and public_index_url not in fetch_approval_statement:
            blockers.append("operator_fetch_approval_statement_must_name_public_index_url")
        if local_index_sha256_supplied and local_index_sha256 not in fetch_approval_statement:
            blockers.append("operator_fetch_approval_statement_must_name_local_index_sha256")
        required_denials = (
            "do not approve upload",
            "external registry mutation",
            "package install",
            "credential",
            "agent bus",
            "protected-core mutation",
        )
        approval_lower = fetch_approval_statement.lower()
        if not all(phrase in approval_lower for phrase in required_denials):
            blockers.append("operator_fetch_approval_statement_must_preserve_authority_limits")

    next_operator_inputs: list[str] = []
    if domain_purchase_deferred:
        next_operator_inputs.append("purchase and configure the official ChaseOS domain")
    if not public_index_url_supplied:
        next_operator_inputs.append("public_index_url ending in /index.json")
    if not hosted_base_url_supplied:
        next_operator_inputs.append("hosted_base_url matching the public index parent directory")
    if "host_label" in placeholder_fields:
        next_operator_inputs.append("host_label for the static host/domain")
    if not local_publication_dir_supplied:
        next_operator_inputs.append("local_static_publication_dir for the uploaded static publication")
    if not local_index_sha256_supplied:
        next_operator_inputs.append("local_index_sha256 for the selected local index.json")
    if "operator_upload_confirmation" in placeholder_fields:
        next_operator_inputs.append("operator upload confirmation with no credentials")
    if not future_fetch_approval_statement_present:
        next_operator_inputs.append("operator fetch approval statement for one bounded future fetch")

    blockers = list(dict.fromkeys(blockers))
    ready_for_live_verification = not blockers
    status = (
        "forge_marketplace_live_index_input_ready"
        if ready_for_live_verification
        else "blocked_forge_marketplace_live_index_input_domain_deferred"
        if domain_purchase_deferred
        else "blocked_forge_marketplace_live_index_input_required"
    )
    return {
        "ok": True,
        "record_type": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SCHEMA_VERSION,
        "surface": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID,
        "api_method": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_API_METHOD,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": True,
        "input_packet_path": _rel(vault, packet_path),
        "input_packet_template_present": bool(packet_payload),
        "input_packet_has_placeholders": bool(placeholder_fields),
        "placeholder_fields": placeholder_fields,
        "handover_path": _rel(vault, handover_file),
        "handover_present": bool(handover_text),
        "domain_purchase_deferred": domain_purchase_deferred,
        "domain_purchase_required": domain_purchase_deferred,
        "public_index_url": public_index_url,
        "public_index_url_supplied": public_index_url_supplied,
        "hosted_base_url": hosted_base_url,
        "hosted_base_url_supplied": hosted_base_url_supplied,
        "host_label": host_label,
        "local_static_publication_dir_supplied": local_publication_dir_supplied,
        "local_static_publication_source": local_publication_source,
        "local_static_publication": local_publication,
        "local_static_publication_candidate_present": bool(local_publication.get("present")),
        "local_static_publication_dir": str(local_publication.get("path") or ""),
        "candidate_local_index_sha256": candidate_index_sha256,
        "local_index_sha256": local_index_sha256,
        "local_index_sha256_supplied": local_index_sha256_supplied,
        "local_index_sha256_matches_candidate": bool(
            local_index_sha256_valid_shape
            and candidate_index_sha256
            and local_index_sha256.lower() == candidate_index_sha256.lower()
        ),
        "required_uploaded_files": required_uploaded_files,
        "uploaded_files": uploaded_files,
        "missing_uploaded_files": missing_uploaded_file_names,
        "operator_upload_confirmation_present": "operator_upload_confirmation" not in placeholder_fields,
        "operator_fetch_approval_statement_present": future_fetch_approval_statement_present,
        "ready_for_live_verification": ready_for_live_verification,
        "live_url_verified": False,
        "network_fetch_performed": False,
        "network_fetch_allowed": False,
        "network_upload_performed": False,
        "network_upload_allowed": False,
        "remote_network_publish_allowed": False,
        "external_registry_mutation_performed": False,
        "external_registry_mutation_allowed": False,
        "credentials_included": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "third_party_package_exchange_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "authority": _authority()
        | {
            "writes_marketplace_live_index_input_readiness_artifacts": False,
            "writes_marketplace_published_static_index_registration_artifacts": False,
            "writes_marketplace_static_upload_receipt_artifacts": False,
            "writes_marketplace_static_upload_handoff_artifacts": False,
            "writes_marketplace_static_host_publication_artifacts": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_fetch_allowed": False,
            "remote_network_publish_allowed": False,
            "network_upload_allowed": False,
            "external_registry_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
        },
        "warnings": warnings,
        "blockers": blockers,
        "next_operator_inputs": next_operator_inputs,
        "next_recommended_pass": (
            "chaser-forge-live-index-url-fetch-verification"
            if ready_for_live_verification
            else "operator-purchase-domain-and-fill-live-index-json-input-packet"
            if domain_purchase_deferred
            else "operator-fill-live-index-json-input-packet"
        ),
    }


def build_forge_marketplace_remote_ingest_preview(
    vault_root: str | Path,
    *,
    remote_index_artifact_path: str | Path | None = None,
    remote_index_payload: dict[str, Any] | None = None,
    expected_remote_index_digest: str | None = None,
    expected_listing_digest: str | None = None,
    trusted_publisher_ids: list[str] | tuple[str, ...] | None = None,
    trusted_publisher_fingerprints: list[str] | tuple[str, ...] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate a declared remote Forge index before local catalog ingest."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    index_payload = deepcopy(remote_index_payload) if isinstance(remote_index_payload, dict) else None
    source_ref = str(remote_index_artifact_path or "inline_remote_index_payload")
    if index_payload is None:
        index_payload, source_ref, blockers = _read_remote_index_path(vault, remote_index_artifact_path)
    if index_payload is None:
        index_payload = {}

    if index_payload.get("record_type") != FORGE_MARKETPLACE_REMOTE_INDEX_RECORD_TYPE:
        blockers.append("remote_index_record_type_mismatch")
    if index_payload.get("schema_version") != FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION:
        blockers.append("remote_index_schema_version_mismatch")
    if index_payload.get("surface") != FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID:
        blockers.append("remote_index_surface_mismatch")
    source_index_digest = str(index_payload.get("remote_index_digest_sha256") or "")
    recomputed_index_digest = _remote_index_digest(index_payload)
    if not source_index_digest:
        blockers.append("remote_index_digest_missing")
    elif source_index_digest != recomputed_index_digest:
        blockers.append("remote_index_digest_mismatch")
    if expected_remote_index_digest and expected_remote_index_digest != source_index_digest:
        blockers.append("expected_remote_index_digest_mismatch")

    publisher = index_payload.get("publisher") if isinstance(index_payload.get("publisher"), dict) else {}
    publisher_id = str(publisher.get("publisher_id") or "")
    fingerprint = str(publisher.get("public_key_fingerprint") or "")
    expected_attestation = _remote_publisher_attestation_digest(source_index_digest, publisher_id, fingerprint)
    source_attestation = str(index_payload.get("publisher_attestation_digest_sha256") or "")
    if not publisher_id:
        blockers.append("remote_publisher_id_missing")
    if not fingerprint:
        blockers.append("remote_publisher_fingerprint_missing")
    if not source_attestation:
        blockers.append("publisher_attestation_digest_missing")
    elif source_attestation != expected_attestation:
        blockers.append("publisher_attestation_digest_mismatch")

    default_trusted_ids = {"local-operator", "StudioAPI"}
    trusted_ids = {str(item) for item in (trusted_publisher_ids if trusted_publisher_ids is not None else default_trusted_ids) if str(item)}
    trusted_fingerprints = {str(item) for item in (trusted_publisher_fingerprints or []) if str(item)}
    publisher_trusted = publisher_id in trusted_ids or fingerprint in trusted_fingerprints
    if not publisher_trusted:
        blockers.append("remote_publisher_not_trusted")

    entries = [entry for entry in index_payload.get("entries") or [] if isinstance(entry, dict)]
    if not entries:
        blockers.append("remote_index_entries_missing")
    selected_listing = None
    for entry in entries:
        if expected_listing_digest and entry.get("listing_digest_sha256") != expected_listing_digest:
            continue
        selected_listing = entry
        break
    if selected_listing is None and entries:
        selected_listing = entries[0]
    if selected_listing is None:
        selected_listing = {}

    if selected_listing.get("record_type") != FORGE_MARKETPLACE_REMOTE_LISTING_RECORD_TYPE:
        blockers.append("remote_listing_record_type_mismatch")
    if selected_listing.get("schema_version") != FORGE_MARKETPLACE_REMOTE_LISTING_SCHEMA_VERSION:
        blockers.append("remote_listing_schema_version_mismatch")
    source_listing_digest = str(selected_listing.get("listing_digest_sha256") or "")
    recomputed_listing_digest = _remote_listing_digest(selected_listing)
    if not source_listing_digest:
        blockers.append("remote_listing_digest_missing")
    elif source_listing_digest != recomputed_listing_digest:
        blockers.append("remote_listing_digest_mismatch")
    if expected_listing_digest and expected_listing_digest != source_listing_digest:
        blockers.append("expected_listing_digest_mismatch")
    if selected_listing.get("publisher_id") != publisher_id:
        blockers.append("remote_listing_publisher_id_mismatch")
    if selected_listing.get("publisher_public_key_fingerprint") != fingerprint:
        blockers.append("remote_listing_publisher_fingerprint_mismatch")
    if selected_listing.get("remote_marketplace_call_allowed") is True:
        blockers.append("remote_listing_network_call_authority_unexpected")
    if selected_listing.get("payment_mutation_allowed") is True:
        blockers.append("remote_listing_payment_mutation_authority_unexpected")
    if selected_listing.get("license_checkout_allowed") is True:
        blockers.append("remote_listing_license_checkout_authority_unexpected")

    package_payload = selected_listing.get("package_payload") if isinstance(selected_listing.get("package_payload"), dict) else {}
    import_preview = build_forge_marketplace_import_preview(
        vault,
        package_payload=package_payload,
        expected_package_digest=str(selected_listing.get("package_digest_sha256") or ""),
        generated_at=timestamp,
    )
    blockers.extend(str(item) for item in import_preview.get("blockers") or [])
    if not import_preview.get("ok"):
        blockers.append("remote_listing_package_import_preview_blocked")

    material = {
        "remote_index_digest_sha256": source_index_digest,
        "listing_digest_sha256": source_listing_digest,
        "package_digest_sha256": selected_listing.get("package_digest_sha256") or "",
        "publisher_id": publisher_id,
        "extension_id": selected_listing.get("extension_id") or "",
    }
    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION,
        "status": "forge_marketplace_remote_ingest_preview_ready" if ready else "blocked_forge_marketplace_remote_ingest_preview",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": True,
        "remote_index_artifact_path": source_ref,
        "remote_index_digest_sha256": source_index_digest,
        "recomputed_remote_index_digest_sha256": recomputed_index_digest,
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "publisher_id": publisher_id,
        "publisher_public_key_fingerprint": fingerprint,
        "publisher_attestation_digest_sha256": source_attestation,
        "publisher_attestation_verified": source_attestation == expected_attestation and bool(source_attestation),
        "publisher_trusted": publisher_trusted,
        "trusted_publisher_ids": sorted(trusted_ids),
        "trusted_publisher_fingerprints": sorted(trusted_fingerprints),
        "listing_digest_sha256": source_listing_digest,
        "recomputed_listing_digest_sha256": recomputed_listing_digest,
        "expected_listing_digest_sha256": expected_listing_digest or "",
        "selected_listing": deepcopy(selected_listing),
        "package_digest_sha256": selected_listing.get("package_digest_sha256") or "",
        "manifest_digest_sha256": selected_listing.get("manifest_digest_sha256") or "",
        "extension_id": selected_listing.get("extension_id") or "",
        "extension_name": selected_listing.get("extension_name") or "",
        "extension_version": selected_listing.get("extension_version") or "",
        "license_policy": deepcopy(selected_listing.get("license_policy") or {}),
        "payment_policy": deepcopy(selected_listing.get("payment_policy") or {}),
        "operator_confirmation_text": _remote_ingest_confirmation_text(material),
        "import_preview": import_preview,
        "future_import_requires": [
            "trusted publisher id or fingerprint",
            "matching remote index digest",
            "matching listing digest",
            "publisher attestation digest",
            "operator confirmation before local catalog ingest",
            "separate marketplace-import and sandbox approvals before any install execution",
        ],
        "authority": _authority()
        | {
            "writes_marketplace_remote_index_artifact": False,
            "writes_marketplace_catalog": False,
            "remote_marketplace_call_allowed": False,
            "remote_network_fetch_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "remote_marketplace_call_allowed": False,
        "remote_network_fetch_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-remote-listing-catalog-ingest"
            if ready
            else "chaser-forge-remote-listing-trust-repair"
        ),
    }


def build_forge_marketplace_remote_listing_ingest(
    vault_root: str | Path,
    *,
    remote_index_artifact_path: str | Path | None = None,
    remote_index_payload: dict[str, Any] | None = None,
    expected_remote_index_digest: str | None = None,
    expected_listing_digest: str | None = None,
    trusted_publisher_ids: list[str] | tuple[str, ...] | None = None,
    trusted_publisher_fingerprints: list[str] | tuple[str, ...] | None = None,
    operator_confirmation: str | None = None,
    write_listing: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Ingest a verified remote listing into the local catalog without installing it."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    preview = build_forge_marketplace_remote_ingest_preview(
        vault,
        remote_index_artifact_path=remote_index_artifact_path,
        remote_index_payload=remote_index_payload,
        expected_remote_index_digest=expected_remote_index_digest,
        expected_listing_digest=expected_listing_digest,
        trusted_publisher_ids=trusted_publisher_ids,
        trusted_publisher_fingerprints=trusted_publisher_fingerprints,
        generated_at=timestamp,
    )
    blockers = [str(item) for item in preview.get("blockers") or []]
    if not preview.get("ok"):
        blockers.append("remote_ingest_preview_blocked")
    if write_listing:
        if expected_remote_index_digest != preview.get("remote_index_digest_sha256"):
            blockers.append("expected_remote_index_digest_required_or_mismatched")
        if expected_listing_digest != preview.get("listing_digest_sha256"):
            blockers.append("expected_listing_digest_required_or_mismatched")
        if operator_confirmation != preview.get("operator_confirmation_text"):
            blockers.append("operator_confirmation_required_or_mismatched")

    selected_listing = deepcopy(preview.get("selected_listing") or {})
    remote_index_ref = str(remote_index_artifact_path or preview.get("remote_index_artifact_path") or "inline_remote_index_payload")
    material = _remote_local_catalog_material(
        selected_listing,
        remote_index_path=remote_index_ref,
        remote_index_digest=str(preview.get("remote_index_digest_sha256") or ""),
    )
    listing_digest = str(preview.get("listing_digest_sha256") or "")
    listing_id = f"forge-remote-listing-{_safe_identifier(str(material.get('package_id') or material.get('extension_id') or 'package'))}-{listing_digest[:12]}"
    entry_preview = _catalog_entry_from_material(
        material,
        listing_id=listing_id,
        listing_digest=listing_digest,
        generated_at=timestamp,
    )
    entry_preview["local_public_catalog_published"] = True
    entry_preview["remote_distribution_source"] = "verified_remote_index"
    entry_preview["remote_listing_ingested_at"] = timestamp

    catalog_payload, catalog_blockers = _load_catalog_payload(vault, generated_at=timestamp)
    blockers.extend(catalog_blockers)
    entries = [entry for entry in catalog_payload.get("entries") or [] if isinstance(entry, dict)]
    existing_matching = any(entry.get("listing_digest_sha256") == listing_digest for entry in entries)
    listing_conflicts = [
        entry
        for entry in entries
        if entry.get("package_id") == material.get("package_id")
        and entry.get("extension_version") == material.get("extension_version")
        and entry.get("listing_digest_sha256") != listing_digest
    ]
    if listing_conflicts:
        blockers.append("marketplace_catalog_remote_listing_version_conflict")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    catalog_written = False
    listing_reused = False
    if write_listing and ready:
        if existing_matching:
            listing_reused = True
        else:
            catalog_path = _catalog_path(vault)
            catalog_payload["entries"] = entries + [entry_preview]
            catalog_payload["updated_at"] = timestamp
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            catalog_path.write_text(
                json.dumps(catalog_payload, indent=2, ensure_ascii=True, default=str) + "\n",
                encoding="utf-8",
            )
            catalog_written = True

    status = (
        "forge_marketplace_remote_listing_ingested"
        if catalog_written
        else "forge_marketplace_remote_listing_existing_matching"
        if listing_reused or existing_matching
        else "forge_marketplace_remote_listing_ingest_ready"
        if ready
        else "blocked_forge_marketplace_remote_listing_ingest"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "catalog_path": _rel(vault, _catalog_path(vault)),
        "preview_only": not catalog_written,
        "write_listing_requested": bool(write_listing),
        "catalog_listing_written": catalog_written,
        "catalog_listing_reused": listing_reused,
        "listing_id": listing_id,
        "listing_digest_sha256": listing_digest,
        "expected_listing_digest_sha256": expected_listing_digest or "",
        "remote_index_artifact_path": remote_index_ref,
        "remote_index_digest_sha256": preview.get("remote_index_digest_sha256") or "",
        "expected_remote_index_digest_sha256": expected_remote_index_digest or "",
        "catalog_entry_preview": entry_preview,
        "package_digest_sha256": preview.get("package_digest_sha256") or "",
        "manifest_digest_sha256": preview.get("manifest_digest_sha256") or "",
        "extension_id": preview.get("extension_id") or "",
        "extension_name": preview.get("extension_name") or "",
        "extension_version": preview.get("extension_version") or "",
        "publisher_id": preview.get("publisher_id") or "",
        "publisher_attestation_verified": bool(preview.get("publisher_attestation_verified")),
        "publisher_trusted": bool(preview.get("publisher_trusted")),
        "operator_confirmation_text": preview.get("operator_confirmation_text") or "",
        "ingest_preview": preview,
        "remote_listing_ingested": catalog_written or listing_reused or existing_matching,
        "authority": _authority(catalog_written=catalog_written)
        | {
            "writes_marketplace_remote_index_artifact": False,
            "remote_listing_local_catalog_ingest_allowed": bool(catalog_written),
            "remote_marketplace_call_allowed": False,
            "remote_network_fetch_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "approval_chain_required_for_install": True,
        },
        "remote_marketplace_call_allowed": False,
        "remote_network_fetch_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "package_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-remote-listing-import-approval-or-sandbox-install"
            if ready
            else "chaser-forge-remote-listing-ingest-repair"
        ),
    }


def _import_approval_material(
    *,
    package_payload: dict[str, Any],
    package_artifact_path: str,
    import_preview: dict[str, Any],
) -> dict[str, Any]:
    manifest = package_payload.get("manifest") if isinstance(package_payload.get("manifest"), dict) else {}
    marketplace = package_payload.get("marketplace") if isinstance(package_payload.get("marketplace"), dict) else {}
    return {
        "requested_action": "request_forge_marketplace_import_sandbox_review",
        "approval_effect": (
            "records operator approval intent for a future package-to-sandbox request only; "
            "no package install, registry write, extension file mutation, or exact-once marker reservation occurs"
        ),
        "manifest": deepcopy(manifest),
        "manifest_validation": deepcopy(import_preview.get("manifest_validation") or {}),
        "package_record_type": package_payload.get("record_type") or "",
        "package_schema_version": package_payload.get("schema_version") or "",
        "package_id": package_payload.get("package_id") or "",
        "package_artifact_path": package_artifact_path,
        "package_digest_sha256": import_preview.get("package_digest_sha256") or "",
        "recomputed_package_digest_sha256": import_preview.get("recomputed_package_digest_sha256") or "",
        "manifest_digest_sha256": import_preview.get("manifest_digest_sha256") or "",
        "recomputed_manifest_digest_sha256": import_preview.get("recomputed_manifest_digest_sha256") or "",
        "extension_id": import_preview.get("extension_id") or manifest.get("id") or "",
        "extension_name": import_preview.get("extension_name") or manifest.get("name") or "",
        "extension_version": import_preview.get("extension_version") or manifest.get("version") or "",
        "target_paths": _target_paths(manifest),
        "permission_disclosure": deepcopy(package_payload.get("permission_disclosure") or {}),
        "marketplace": {
            "category": marketplace.get("category") or "",
            "license": marketplace.get("license") or "",
            "publisher_id": marketplace.get("publisher_id") or "",
            "visibility": marketplace.get("visibility") or "",
            "publish_allowed": False,
            "remote_marketplace_call_allowed": False,
            "import_install_allowed": False,
            "auto_install_allowed": False,
        },
        "import_preview_status": import_preview.get("status") or "",
        "future_import_requires": list(import_preview.get("future_import_requires") or []),
        "future_sandbox_request_api_method": FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_API_METHOD,
        "future_install_requires_separate_approval": True,
        "future_sandbox_request_bridge_built": True,
        "future_executor_not_built": True,
    }


def _import_approval_artifact_payload(
    *,
    packet_id: str,
    request_digest: str,
    material: dict[str, Any],
    approval_path: Path,
    requested_by: str,
    generated_at: str,
) -> dict[str, Any]:
    material_with_request = dict(material) | {
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
    }
    return {
        "record_type": FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE,
        "schema_version": FORGE_MARKETPLACE_IMPORT_APPROVAL_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "pending_operator_decision",
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": "pending",
        "approval_scope": FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE,
        "requested_by": requested_by,
        "extension_id": material.get("extension_id") or "",
        "extension_name": material.get("extension_name") or "",
        "extension_version": material.get("extension_version") or "",
        "package_id": material.get("package_id") or "",
        "package_artifact_path": material.get("package_artifact_path") or "",
        "package_digest_sha256": material.get("package_digest_sha256") or "",
        "manifest_digest_sha256": material.get("manifest_digest_sha256") or "",
        "approval_artifact_path": str(approval_path),
        "future_extension_target_paths": list(material.get("target_paths") or []),
        "future_sandbox_request_api_method": material.get("future_sandbox_request_api_method") or "",
        "operator_confirmation_text": _operator_import_confirmation_text(material_with_request),
        "approved_material": material,
        "future_executor_requirements": [
            "operator_decision must be recorded through source-specific Forge decision handoff",
            "approval_packet_id and request_digest_sha256 must match",
            "package digest must be revalidated before any future sandbox request",
            "manifest digest and protected-core target paths must be revalidated",
            "future package-to-sandbox request requires a separate implementation pass",
        ],
        "approval_consumed": False,
        "marketplace_import_approval_request_only": True,
        "package_install_allowed_in_this_pass": False,
        "sandbox_install_allowed_in_this_pass": False,
        "live_install_allowed_in_this_pass": False,
        "registry_write_allowed_in_this_pass": False,
        "extension_file_write_allowed_in_this_pass": False,
        "exact_once_marker_reservation_allowed_in_this_pass": False,
        **BLOCKED_AUTHORITY,
    }


def _import_approval_matches(payload: dict[str, Any] | None, packet_id: str, request_digest: str) -> bool:
    return bool(
        payload
        and payload.get("record_type") == FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("status") == "pending_operator_decision"
        and payload.get("operator_decision") == "pending"
        and payload.get("approval_scope") == FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE
        and payload.get("marketplace_import_approval_request_only") is True
        and payload.get("package_install_allowed_in_this_pass") is False
        and payload.get("registry_write_allowed_in_this_pass") is False
    )


def build_forge_marketplace_import_sandbox_approval(
    vault_root: str | Path,
    *,
    package_artifact_path: str | Path | None = None,
    package_payload: dict[str, Any] | None = None,
    expected_package_digest: str | None = None,
    approval_packet_id: str | None = None,
    request_digest: str | None = None,
    write_approval_request: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or write a digest-gated package import sandbox review request.

    This request records operator review intent only. It never installs a package,
    mutates the Forge registry, writes extension files, or consumes approval.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    payload = deepcopy(package_payload) if isinstance(package_payload, dict) else None
    source_ref = str(package_artifact_path or "inline_package_payload")
    if payload is None:
        payload, source_ref, blockers = _read_package_path(vault, package_artifact_path)
    if payload is None:
        payload = {}

    import_preview = build_forge_marketplace_import_preview(
        vault,
        package_artifact_path=package_artifact_path if not package_payload else None,
        package_payload=payload if payload else None,
        expected_package_digest=expected_package_digest,
        generated_at=timestamp,
    )
    blockers.extend(str(item) for item in import_preview.get("blockers") or [])

    material = _import_approval_material(
        package_payload=payload,
        package_artifact_path=source_ref,
        import_preview=import_preview,
    )
    digest = _sha256_payload(material)
    extension_id = str(material.get("extension_id") or "invalid-extension")
    package_id = str(material.get("package_id") or "marketplace-package")
    packet_id = approval_packet_id or f"forge-marketplace-import-appr-{_safe_identifier(extension_id)}-{digest[:12]}"
    approval_path = _safe_json_path(vault, FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR, packet_id)
    existing_payload = _read_package_path(vault, _rel(vault, approval_path))[0] if approval_path.is_file() else None
    existing_matches = _import_approval_matches(existing_payload, packet_id, digest)
    approval_preview = _import_approval_artifact_payload(
        packet_id=packet_id,
        request_digest=digest,
        material=material,
        approval_path=approval_path,
        requested_by=requested_by,
        generated_at=timestamp,
    )

    if not import_preview.get("ok"):
        blockers.append("marketplace_import_preview_blocked")
    if approval_path.exists() and not existing_matches:
        blockers.append("existing_marketplace_import_approval_artifact_mismatch")
    if write_approval_request and request_digest != digest:
        blockers.append("request_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready_for_operator_decision = not blockers
    approval_written = False
    approval_reused = False
    if write_approval_request and ready_for_operator_decision:
        if existing_matches:
            approval_reused = True
        else:
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            approval_path.write_text(
                json.dumps(approval_preview, indent=2, ensure_ascii=True, default=str) + "\n",
                encoding="utf-8",
            )
            approval_written = True

    status = (
        "forge_marketplace_import_sandbox_approval_request_written"
        if approval_written
        else "forge_marketplace_import_sandbox_approval_request_existing_matching"
        if approval_reused or existing_matches
        else "forge_marketplace_import_sandbox_approval_request_ready"
        if ready_for_operator_decision
        else "blocked_forge_marketplace_import_sandbox_approval_request"
    )
    return {
        "ok": ready_for_operator_decision,
        "surface": FORGE_MARKETPLACE_IMPORT_APPROVAL_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_IMPORT_APPROVAL_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not approval_written,
        "approval_request_write_requested": bool(write_approval_request),
        "approval_request_written": approval_written,
        "approval_request_reused": approval_reused,
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "approval_artifact_path": _rel(vault, approval_path),
        "approval_artifact_exists": approval_path.is_file(),
        "approval_artifact_preview": approval_preview,
        "operator_confirmation_text": approval_preview["operator_confirmation_text"],
        "package_id": package_id,
        "package_artifact_path": source_ref,
        "package_digest_sha256": material.get("package_digest_sha256") or "",
        "manifest_digest_sha256": material.get("manifest_digest_sha256") or "",
        "extension_id": extension_id,
        "extension_name": material.get("extension_name") or "",
        "extension_version": material.get("extension_version") or "",
        "future_extension_target_paths": list(material.get("target_paths") or []),
        "future_sandbox_request_api_method": material.get("future_sandbox_request_api_method") or "",
        "import_preview": import_preview,
        "approved_material": material,
        "authority": _authority(approval_written=approval_written)
        | {
            "approval_request_surface_only": True,
            "marketplace_import_sandbox_review_only": True,
            "future_sandbox_request_bridge_available": True,
            "future_sandbox_install_execution_requires_separate_pass": True,
        },
        "marketplace_publish_allowed": False,
        "marketplace_remote_call_allowed": False,
        "package_install_allowed": False,
        "import_install_allowed": False,
        "auto_install_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "exact_once_marker_reserved": False,
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-marketplace-import-decision-or-sandbox-request-consumption"
            if ready_for_operator_decision
            else "chaser-forge-marketplace-package-contract-repair"
        ),
    }


def _marketplace_import_decision_sidecar_blockers(
    *,
    vault: Path,
    approval_path: Path,
    approval_payload: dict[str, Any],
    request_digest: str,
) -> list[str]:
    blockers: list[str] = []
    if approval_payload.get("approval_decision_recorded") is not True:
        blockers.append("approval_decision_record_missing")
    if approval_payload.get("approval_decision_family") != "marketplace-import":
        blockers.append("approval_decision_family_mismatch")
    if approval_payload.get("approval_decision_record_type") != FORGE_APPROVAL_DECISION_RECORD_TYPE:
        blockers.append("approval_decision_record_type_mismatch")

    source_decision_digest = str(approval_payload.get("approval_decision_digest_sha256") or "")
    if not source_decision_digest:
        blockers.append("approval_decision_digest_missing")

    handoff = approval_payload.get("approval_decision_handoff")
    if not isinstance(handoff, dict):
        blockers.append("approval_decision_handoff_metadata_missing")
    else:
        if handoff.get("surface") != FORGE_APPROVAL_DECISION_SURFACE_ID:
            blockers.append("approval_decision_handoff_surface_mismatch")
        if handoff.get("api_method") != FORGE_APPROVAL_DECISION_API_METHOD:
            blockers.append("approval_decision_handoff_api_method_mismatch")
        if handoff.get("source_specific") is not True:
            blockers.append("approval_decision_handoff_not_source_specific")
        if handoff.get("generic_approval_center_control") is not False:
            blockers.append("approval_decision_handoff_generic_control_unexpected")
        if handoff.get("approval_consumed") is not False:
            blockers.append("approval_decision_handoff_consumed_unexpected")
        if handoff.get("forge_execution_allowed") is not False:
            blockers.append("approval_decision_handoff_execution_unexpected")
        if source_decision_digest and handoff.get("decision_record_digest_sha256") != source_decision_digest:
            blockers.append("approval_decision_handoff_digest_mismatch")

    decision_path_value = approval_payload.get("decision_artifact_path")
    if not decision_path_value:
        blockers.append("approval_decision_artifact_path_missing")
        return blockers

    decision_root = (vault / FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR / "_decisions").resolve()
    raw_decision_path = Path(str(decision_path_value))
    decision_path = raw_decision_path.resolve() if raw_decision_path.is_absolute() else (vault / raw_decision_path).resolve()
    try:
        decision_relative = decision_path.relative_to(decision_root)
    except ValueError:
        blockers.append("approval_decision_artifact_path_outside_decision_root")
        decision_relative = None
    if decision_relative is not None and (len(decision_relative.parts) != 1 or decision_path.suffix.lower() != ".json"):
        blockers.append("approval_decision_artifact_path_not_direct_json")
    if not decision_path.is_file():
        blockers.append("approval_decision_artifact_missing")
        return blockers

    decision_payload = _read_json_file(decision_path)
    if decision_payload is None:
        blockers.append("approval_decision_artifact_unreadable")
        return blockers

    decision_record_digest = str(decision_payload.get("decision_record_digest_sha256") or "")
    if not decision_record_digest:
        blockers.append("approval_decision_digest_missing")
    elif source_decision_digest and decision_record_digest != source_decision_digest:
        blockers.append("approval_decision_source_digest_mismatch")
    recompute_payload = dict(decision_payload)
    recompute_payload.pop("decision_record_digest_sha256", None)
    if decision_record_digest and _sha256_payload(recompute_payload) != decision_record_digest:
        blockers.append("approval_decision_digest_mismatch")

    if decision_payload.get("record_type") != FORGE_APPROVAL_DECISION_RECORD_TYPE:
        blockers.append("approval_decision_artifact_record_type_mismatch")
    if decision_payload.get("schema_version") != FORGE_APPROVAL_DECISION_SCHEMA_VERSION:
        blockers.append("approval_decision_artifact_schema_version_mismatch")
    if decision_payload.get("status") != "forge_approval_decision_recorded":
        blockers.append("approval_decision_artifact_status_mismatch")
    if decision_payload.get("surface") != FORGE_APPROVAL_DECISION_SURFACE_ID:
        blockers.append("approval_decision_artifact_surface_mismatch")
    if decision_payload.get("api_method") != FORGE_APPROVAL_DECISION_API_METHOD:
        blockers.append("approval_decision_artifact_api_method_mismatch")
    if decision_payload.get("source_specific") is not True:
        blockers.append("approval_decision_artifact_not_source_specific")
    if decision_payload.get("generic_approval_center_control") is not False:
        blockers.append("approval_decision_artifact_generic_control_unexpected")
    if decision_payload.get("family") != "marketplace-import":
        blockers.append("approval_decision_artifact_family_mismatch")
    if decision_payload.get("operator_decision") != "approved":
        blockers.append("approval_decision_not_approved")
    if decision_payload.get("approval_packet_id") != approval_payload.get("approval_packet_id"):
        blockers.append("approval_decision_packet_id_mismatch")
    if decision_payload.get("request_digest_sha256") != request_digest:
        blockers.append("approval_decision_request_digest_mismatch")
    if decision_payload.get("source_approval_record_type") != FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE:
        blockers.append("approval_decision_source_record_type_mismatch")
    if decision_payload.get("source_approval_schema_version") != FORGE_MARKETPLACE_IMPORT_APPROVAL_SCHEMA_VERSION:
        blockers.append("approval_decision_source_schema_version_mismatch")
    if decision_payload.get("approval_scope") != FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE:
        blockers.append("approval_decision_scope_mismatch")
    if not _path_matches(vault, decision_payload.get("source_approval_artifact_path"), approval_path):
        blockers.append("approval_decision_source_artifact_path_mismatch")
    if not _path_matches(vault, decision_payload.get("decision_artifact_path"), decision_path):
        blockers.append("approval_decision_artifact_path_mismatch")
    if isinstance(handoff, dict) and handoff.get("decision_artifact_path") != approval_payload.get("decision_artifact_path"):
        blockers.append("approval_decision_handoff_path_mismatch")

    mutation = decision_payload.get("approval_artifact_mutation")
    if not isinstance(mutation, dict):
        blockers.append("approval_decision_artifact_mutation_missing")
    else:
        if mutation.get("status_after") != "approved":
            blockers.append("approval_decision_artifact_mutation_status_mismatch")
        if mutation.get("approval_consumed_after") is not False:
            blockers.append("approval_decision_artifact_mutation_consumed_unexpected")
    if decision_payload.get("approval_consumed") is not False:
        blockers.append("approval_decision_consumed_unexpected")
    if decision_payload.get("forge_execution_allowed") is not False:
        blockers.append("approval_decision_execution_allowed_unexpected")
    if decision_payload.get("registry_written") is not False:
        blockers.append("approval_decision_registry_written_unexpected")
    if decision_payload.get("extension_files_written") != []:
        blockers.append("approval_decision_extension_files_written_unexpected")
    if decision_payload.get("extension_files_deleted") != []:
        blockers.append("approval_decision_extension_files_deleted_unexpected")
    if decision_payload.get("exact_once_marker_reserved") is not False:
        blockers.append("approval_decision_exact_once_marker_reserved_unexpected")
    return blockers


def _marketplace_import_approval_blockers(
    *,
    vault: Path,
    approval_path: Path | None,
    approval_payload: dict[str, Any] | None,
    expected_import_request_digest: str | None,
    write_sandbox_request: bool,
) -> tuple[dict[str, Any], list[str]]:
    material: dict[str, Any] = {}
    blockers: list[str] = []
    if approval_payload is None:
        return material, ["marketplace_import_approval_artifact_missing_or_unreadable"]
    if approval_payload.get("record_type") != FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE:
        blockers.append("marketplace_import_approval_record_type_mismatch")
    if approval_payload.get("schema_version") != FORGE_MARKETPLACE_IMPORT_APPROVAL_SCHEMA_VERSION:
        blockers.append("marketplace_import_approval_schema_version_mismatch")
    if approval_payload.get("approval_scope") != FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE:
        blockers.append("marketplace_import_approval_scope_mismatch")
    if approval_payload.get("status") != "approved":
        blockers.append("marketplace_import_approval_status_not_approved")
    if approval_payload.get("operator_decision") != "approved":
        blockers.append("marketplace_import_operator_decision_not_approved")
    if approval_payload.get("approval_consumed") is not False:
        blockers.append("marketplace_import_approval_already_consumed")
    if approval_payload.get("package_install_allowed_in_this_pass") is not False:
        blockers.append("marketplace_import_package_install_flag_unexpected")
    if approval_payload.get("registry_write_allowed_in_this_pass") is not False:
        blockers.append("marketplace_import_registry_write_flag_unexpected")
    if approval_payload.get("extension_file_write_allowed_in_this_pass") is not False:
        blockers.append("marketplace_import_extension_file_write_flag_unexpected")

    request_digest = str(approval_payload.get("request_digest_sha256") or "")
    if not request_digest:
        blockers.append("marketplace_import_request_digest_missing")
    if expected_import_request_digest:
        if expected_import_request_digest != request_digest:
            blockers.append("expected_import_request_digest_mismatch")
    elif write_sandbox_request:
        blockers.append("expected_import_request_digest_required")

    approval_statement = str(approval_payload.get("operator_approval_statement") or "").strip()
    confirmation_text = str(approval_payload.get("operator_confirmation_text") or "").strip()
    if not confirmation_text or approval_statement != confirmation_text:
        blockers.append("marketplace_import_operator_statement_missing_or_mismatched")

    approved_material = approval_payload.get("approved_material")
    if not isinstance(approved_material, dict):
        blockers.append("marketplace_import_approved_material_missing")
    else:
        material = deepcopy(approved_material)
        if request_digest and _sha256_payload(approved_material) != request_digest:
            blockers.append("marketplace_import_approved_material_digest_mismatch")
        manifest = approved_material.get("manifest")
        if not isinstance(manifest, dict):
            blockers.append("marketplace_import_manifest_missing")
        else:
            manifest_digest = _sha256_payload(manifest)
            if approved_material.get("manifest_digest_sha256") != manifest_digest:
                blockers.append("marketplace_import_manifest_digest_mismatch")
            validation = validate_manifest(manifest)
            if not validation.get("valid"):
                blockers.append("marketplace_import_manifest_validation_failed")

    if approval_path is not None:
        blockers.extend(
            _marketplace_import_decision_sidecar_blockers(
                vault=vault,
                approval_path=approval_path,
                approval_payload=approval_payload,
                request_digest=request_digest,
            )
        )
    return material, blockers


def _sandbox_bridge_material(
    *,
    vault: Path,
    source_approval_path: Path,
    source_payload: dict[str, Any],
    approved_material: dict[str, Any],
    sandbox_preview: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_SCHEMA_VERSION,
        "requested_action": "write_forge_sandbox_approval_request_from_marketplace_import_review",
        "source_marketplace_import_approval_path": _rel(vault, source_approval_path),
        "source_marketplace_import_approval_packet_id": source_payload.get("approval_packet_id") or "",
        "source_marketplace_import_request_digest_sha256": source_payload.get("request_digest_sha256") or "",
        "source_marketplace_import_decision_artifact_path": source_payload.get("decision_artifact_path") or "",
        "package_id": approved_material.get("package_id") or "",
        "package_digest_sha256": approved_material.get("package_digest_sha256") or "",
        "manifest_digest_sha256": approved_material.get("manifest_digest_sha256") or "",
        "extension_id": approved_material.get("extension_id") or "",
        "extension_name": approved_material.get("extension_name") or "",
        "extension_version": approved_material.get("extension_version") or "",
        "target_paths": list(approved_material.get("target_paths") or []),
        "sandbox_approval_packet_id": sandbox_preview.get("approval_packet_id") or "",
        "sandbox_request_digest_sha256": sandbox_preview.get("request_digest_sha256") or "",
        "sandbox_approval_artifact_path": sandbox_preview.get("approval_artifact_path") or "",
        "effect": (
            "writes or reuses one pending Forge sandbox approval request from an approved "
            "marketplace-import review; does not install the package or consume either approval"
        ),
        "marketplace_import_approval_consumed": False,
        "sandbox_approval_consumed": False,
        "registry_write_allowed": False,
        "extension_file_write_allowed": False,
        "exact_once_marker_reservation_allowed": False,
    }


def build_forge_marketplace_import_sandbox_request(
    vault_root: str | Path,
    *,
    import_approval_artifact_path: str | Path | None = None,
    expected_import_request_digest: str | None = None,
    request_digest: str | None = None,
    sandbox_approval_packet_id: str | None = None,
    write_sandbox_request: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Preview or write a pending sandbox approval request from an approved marketplace-import review.

    This bridge never installs a package, writes the Forge registry, writes
    extension files, consumes approvals, or reserves exact-once markers.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    source_path, blockers = _resolve_marketplace_import_approval_path(vault, import_approval_artifact_path)
    source_payload = _read_json_file(source_path) if source_path and source_path.is_file() else None
    approved_material, approval_blockers = _marketplace_import_approval_blockers(
        vault=vault,
        approval_path=source_path,
        approval_payload=source_payload,
        expected_import_request_digest=expected_import_request_digest,
        write_sandbox_request=write_sandbox_request,
    )
    blockers.extend(approval_blockers)

    manifest = approved_material.get("manifest") if isinstance(approved_material.get("manifest"), dict) else {}
    extension_id = str(approved_material.get("extension_id") or manifest.get("id") or "invalid-extension")
    sandbox_preview_packet_id = sandbox_approval_packet_id
    if sandbox_preview_packet_id is None and manifest:
        sandbox_probe = build_sandbox_install_approval(vault, manifest=manifest, generated_at=timestamp)
        sandbox_digest = str(sandbox_probe.get("request_digest_sha256") or "")
        sandbox_preview_packet_id = f"forge-marketplace-sandbox-appr-{_safe_identifier(extension_id)}-{sandbox_digest[:12]}"

    sandbox_preview = build_sandbox_install_approval(
        vault,
        manifest=manifest if manifest else {},
        approval_packet_id=sandbox_preview_packet_id,
        generated_at=timestamp,
    )
    if not sandbox_preview.get("ok"):
        blockers.extend(str(item) for item in sandbox_preview.get("blockers") or [])
        blockers.append("sandbox_approval_request_preview_blocked")

    bridge_material = _sandbox_bridge_material(
        vault=vault,
        source_approval_path=source_path or (vault / FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR / "missing.json"),
        source_payload=source_payload or {},
        approved_material=approved_material,
        sandbox_preview=sandbox_preview,
    )
    bridge_digest = _sha256_payload(bridge_material)
    if write_sandbox_request and request_digest != bridge_digest:
        blockers.append("request_digest_required_or_mismatched")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    sandbox_written = False
    sandbox_reused = False
    sandbox_result = sandbox_preview
    if write_sandbox_request and ready:
        sandbox_result = build_sandbox_install_approval(
            vault,
            manifest=manifest,
            approval_packet_id=str(sandbox_preview.get("approval_packet_id") or sandbox_preview_packet_id or ""),
            request_digest=str(sandbox_preview.get("request_digest_sha256") or ""),
            write_approval_request=True,
            requested_by=requested_by,
            generated_at=timestamp,
        )
        sandbox_written = bool(sandbox_result.get("approval_request_written"))
        sandbox_reused = bool(sandbox_result.get("approval_request_reused"))
        if not sandbox_result.get("ok"):
            blockers.extend(str(item) for item in sandbox_result.get("blockers") or [])
            ready = False

    status = (
        "forge_marketplace_import_sandbox_request_written"
        if sandbox_written
        else "forge_marketplace_import_sandbox_request_existing_matching"
        if sandbox_reused
        else "forge_marketplace_import_sandbox_request_ready"
        if ready
        else "blocked_forge_marketplace_import_sandbox_request"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not sandbox_written,
        "sandbox_request_write_requested": bool(write_sandbox_request),
        "sandbox_approval_request_written": sandbox_written,
        "sandbox_approval_request_reused": sandbox_reused,
        "request_digest_sha256": bridge_digest,
        "expected_import_request_digest_sha256": expected_import_request_digest or "",
        "source_import_approval_artifact_path": _rel(vault, source_path) if source_path else "",
        "source_import_approval_artifact_exists": bool(source_path and source_path.is_file()),
        "source_import_approval_packet_id": (source_payload or {}).get("approval_packet_id", ""),
        "source_import_request_digest_sha256": (source_payload or {}).get("request_digest_sha256", ""),
        "source_import_approval_consumed": False,
        "marketplace_import_approval_consumed": False,
        "package_id": approved_material.get("package_id") or "",
        "package_digest_sha256": approved_material.get("package_digest_sha256") or "",
        "manifest_digest_sha256": approved_material.get("manifest_digest_sha256") or "",
        "extension_id": extension_id,
        "extension_name": approved_material.get("extension_name") or manifest.get("name") or "",
        "extension_version": approved_material.get("extension_version") or manifest.get("version") or "",
        "future_extension_target_paths": list(approved_material.get("target_paths") or []),
        "sandbox_approval_packet_id": sandbox_result.get("approval_packet_id") or "",
        "sandbox_request_digest_sha256": sandbox_result.get("request_digest_sha256") or "",
        "sandbox_approval_artifact_path": sandbox_result.get("approval_artifact_path") or "",
        "sandbox_approval_artifact_exists": bool(
            sandbox_result.get("approval_artifact_path") and (vault / str(sandbox_result.get("approval_artifact_path"))).is_file()
        ),
        "sandbox_approval_request": sandbox_result,
        "approved_material": bridge_material,
        "authority": _authority(sandbox_approval_written=sandbox_written)
        | {
            "marketplace_import_sandbox_request_bridge_only": True,
            "writes_sandbox_approval_artifact": sandbox_written,
            "consumes_marketplace_import_approval": False,
            "consumes_sandbox_approval": False,
            "executes_sandbox_install": False,
            "writes_extension_registry": False,
            "writes_extension_files": False,
            "reserves_exact_once_marker": False,
        },
        "marketplace_publish_allowed": False,
        "marketplace_remote_call_allowed": False,
        "package_install_allowed": False,
        "import_install_allowed": False,
        "auto_install_allowed": False,
        "sandbox_install_executed": False,
        "registry_written": False,
        "extension_files_written": [],
        "exact_once_marker_reserved": False,
        "approval_consumed": False,
        "blockers": list(dict.fromkeys(blockers)),
        "next_recommended_pass": (
            "chaser-forge-marketplace-import-to-sandbox-approval-visual-qa"
            if ready
            else "chaser-forge-marketplace-import-sandbox-request-repair"
        ),
    }


def _consume_marketplace_import_approval(
    *,
    path: Path,
    payload: dict[str, Any],
    install_result: dict[str, Any],
    generated_at: str,
    requested_by: str,
) -> bool:
    consumed = dict(payload)
    consumed.update(
        {
            "status": "consumed",
            "approval_consumed": True,
            "consumed_at": generated_at,
            "consumed_by": requested_by,
            "marketplace_install_execution_result": {
                "schema_version": FORGE_MARKETPLACE_INSTALL_SCHEMA_VERSION,
                "sandbox_approval_artifact_path": install_result.get("approval_artifact_path") or "",
                "sandbox_request_digest_sha256": install_result.get("request_digest_sha256") or "",
                "registry_path": install_result.get("registry_path") or "",
                "extension_files_written": list(install_result.get("extension_files_written") or []),
                "exact_once_marker_path": install_result.get("future_exact_once_marker_path") or "",
            },
            "package_install_allowed_in_this_pass": True,
            "sandbox_install_allowed_in_this_pass": True,
            "registry_write_allowed_in_this_pass": bool(install_result.get("registry_written")),
            "extension_file_write_allowed_in_this_pass": bool(install_result.get("extension_files_written")),
            "exact_once_marker_reservation_allowed_in_this_pass": bool(install_result.get("exact_once_marker_written")),
        }
    )
    path.write_text(json.dumps(consumed, indent=2, ensure_ascii=True, default=str) + "\n", encoding="utf-8")
    return True


def build_forge_marketplace_install_execution(
    vault_root: str | Path,
    *,
    import_approval_artifact_path: str | Path | None = None,
    expected_import_request_digest: str | None = None,
    expected_listing_digest: str | None = None,
    listing_id: str | None = None,
    bridge_request_digest: str | None = None,
    sandbox_approval_artifact_path: str | Path | None = None,
    sandbox_request_digest: str | None = None,
    sandbox_approval_packet_id: str | None = None,
    execute: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Execute an approved marketplace package install into the Forge sandbox.

    The executor requires a package already published in the local marketplace
    catalog, an approved marketplace-import review with a source-specific
    decision sidecar, and an approved sandbox approval with its own
    source-specific decision sidecar. The actual registry/file writes are
    delegated to the existing sandbox registry writer.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    source_path, blockers = _resolve_marketplace_import_approval_path(vault, import_approval_artifact_path)
    source_payload = _read_json_file(source_path) if source_path and source_path.is_file() else None
    approved_material, approval_blockers = _marketplace_import_approval_blockers(
        vault=vault,
        approval_path=source_path,
        approval_payload=source_payload,
        expected_import_request_digest=expected_import_request_digest,
        write_sandbox_request=True,
    )
    blockers.extend(approval_blockers)
    sandbox_artifact_path_for_read, sandbox_payload = _read_sandbox_approval_payload_for_install(
        vault,
        sandbox_approval_artifact_path,
    )
    sandbox_generated_at = str((sandbox_payload or {}).get("generated_at") or timestamp)
    resolved_sandbox_packet_id = str(
        sandbox_approval_packet_id or (sandbox_payload or {}).get("approval_packet_id") or ""
    )

    package_digest = str(approved_material.get("package_digest_sha256") or "")
    catalog = build_forge_marketplace_catalog(vault, generated_at=timestamp)
    if catalog.get("ok") is not True:
        blockers.extend(str(item) for item in catalog.get("blockers") or [])
    listing = _catalog_entry_for_listing(
        {"entries": catalog.get("entries") or []},
        listing_id,
        expected_listing_digest,
    )
    if listing is None and package_digest:
        listing = _catalog_entry_for_package({"entries": catalog.get("entries") or []}, package_digest)
    if listing is None:
        blockers.append("marketplace_catalog_listing_missing")
    else:
        if package_digest and listing.get("package_digest_sha256") != package_digest:
            blockers.append("marketplace_catalog_listing_package_digest_mismatch")
        if expected_listing_digest and listing.get("listing_digest_sha256") != expected_listing_digest:
            blockers.append("expected_listing_digest_mismatch")
        if listing_id and listing.get("listing_id") != listing_id:
            blockers.append("marketplace_catalog_listing_id_mismatch")

    if sandbox_payload is not None and sandbox_artifact_path_for_read is not None:
        sandbox_preview = {
            "ok": True,
            "approval_packet_id": sandbox_payload.get("approval_packet_id") or "",
            "request_digest_sha256": sandbox_payload.get("request_digest_sha256") or "",
            "approval_artifact_path": _rel(vault, sandbox_artifact_path_for_read),
            "blockers": [],
        }
        bridge_material = _sandbox_bridge_material(
            vault=vault,
            source_approval_path=source_path or (vault / FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR / "missing.json"),
            source_payload=source_payload or {},
            approved_material=approved_material,
            sandbox_preview=sandbox_preview,
        )
        bridge_preview = {
            "ok": True,
            "status": "forge_marketplace_import_sandbox_request_existing_sandbox_artifact",
            "request_digest_sha256": _sha256_payload(bridge_material),
            "sandbox_approval_packet_id": sandbox_preview["approval_packet_id"],
            "sandbox_request_digest_sha256": sandbox_preview["request_digest_sha256"],
            "sandbox_approval_artifact_path": sandbox_preview["approval_artifact_path"],
            "sandbox_approval_artifact_exists": True,
            "approved_material": bridge_material,
            "blockers": [],
        }
    else:
        bridge_preview = build_forge_marketplace_import_sandbox_request(
            vault,
            import_approval_artifact_path=import_approval_artifact_path,
            expected_import_request_digest=expected_import_request_digest,
            sandbox_approval_packet_id=resolved_sandbox_packet_id or sandbox_approval_packet_id,
            write_sandbox_request=False,
            requested_by=requested_by,
            generated_at=sandbox_generated_at,
        )
        if bridge_preview.get("ok") is not True:
            blockers.extend(str(item) for item in bridge_preview.get("blockers") or [])
            blockers.append("marketplace_import_sandbox_request_preview_blocked")
    if not bridge_request_digest:
        blockers.append("bridge_request_digest_required")
    elif bridge_request_digest != bridge_preview.get("request_digest_sha256"):
        blockers.append("bridge_request_digest_mismatch")

    sandbox_artifact_rel = str(
        sandbox_approval_artifact_path
        or (sandbox_artifact_path_for_read and _rel(vault, sandbox_artifact_path_for_read))
        or bridge_preview.get("sandbox_approval_artifact_path")
        or ""
    )
    if not sandbox_artifact_rel:
        blockers.append("sandbox_approval_artifact_path_required")
    if not sandbox_request_digest:
        blockers.append("sandbox_request_digest_required")
    if sandbox_artifact_rel and bridge_preview.get("sandbox_approval_artifact_path") and sandbox_artifact_rel != bridge_preview.get("sandbox_approval_artifact_path"):
        blockers.append("sandbox_approval_artifact_path_mismatch")

    manifest = approved_material.get("manifest") if isinstance(approved_material.get("manifest"), dict) else {}
    sandbox_result = build_sandbox_registry_write_execution(
        vault,
        manifest=manifest,
        approval_packet_id=str(bridge_preview.get("sandbox_approval_packet_id") or resolved_sandbox_packet_id or ""),
        request_digest=sandbox_request_digest or "",
        approval_artifact_path=sandbox_artifact_rel or None,
        execute=bool(execute),
        requested_by=requested_by,
        generated_at=sandbox_generated_at,
    )
    if sandbox_result.get("ok") is not True:
        blockers.extend(str(item) for item in sandbox_result.get("blockers") or [])
        blockers.append("sandbox_registry_write_execution_blocked")

    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    marketplace_import_consumed = False
    if execute and ready and source_path is not None and source_payload is not None and sandbox_result.get("registry_written"):
        marketplace_import_consumed = _consume_marketplace_import_approval(
            path=source_path,
            payload=source_payload,
            install_result=sandbox_result,
            generated_at=timestamp,
            requested_by=requested_by,
        )

    status = (
        "forge_marketplace_install_executed"
        if marketplace_import_consumed and sandbox_result.get("registry_written")
        else "forge_marketplace_install_execution_ready"
        if ready
        else "blocked_forge_marketplace_install_execution"
    )
    return {
        "ok": ready,
        "surface": FORGE_MARKETPLACE_INSTALL_SURFACE_ID,
        "model_version": FORGE_MARKETPLACE_INSTALL_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "execute_requested": bool(execute),
        "listing_id": (listing or {}).get("listing_id", ""),
        "listing_digest_sha256": (listing or {}).get("listing_digest_sha256", ""),
        "package_digest_sha256": package_digest,
        "manifest_digest_sha256": approved_material.get("manifest_digest_sha256") or "",
        "extension_id": approved_material.get("extension_id") or manifest.get("id") or "",
        "extension_name": approved_material.get("extension_name") or manifest.get("name") or "",
        "extension_version": approved_material.get("extension_version") or manifest.get("version") or "",
        "import_approval_artifact_path": _rel(vault, source_path) if source_path else "",
        "expected_import_request_digest_sha256": expected_import_request_digest or "",
        "marketplace_import_approval_consumed": marketplace_import_consumed,
        "bridge_request_digest_sha256": bridge_preview.get("request_digest_sha256") or "",
        "sandbox_approval_artifact_path": sandbox_artifact_rel,
        "sandbox_request_digest_sha256": sandbox_request_digest or "",
        "sandbox_registry_write": sandbox_result,
        "marketplace_install_executed": bool(marketplace_import_consumed and sandbox_result.get("registry_written")),
        "registry_written": bool(sandbox_result.get("registry_written")),
        "registry_path": sandbox_result.get("registry_path") or "",
        "extension_files_written": list(sandbox_result.get("extension_files_written") or []),
        "exact_once_marker_reserved": bool(sandbox_result.get("exact_once_marker_written")),
        "sandbox_approval_consumed": bool(sandbox_result.get("approval_consumed")),
        "authority": _authority(
            install_executed=bool(marketplace_import_consumed and sandbox_result.get("registry_written")),
            marketplace_import_consumed=marketplace_import_consumed,
        )
        | {
            "local_marketplace_catalog_required": True,
            "source_specific_decisions_required": True,
            "remote_marketplace_call_allowed": False,
            "protected_core_mutation_allowed": False,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-marketplace-studio-ui-release-qa"
            if ready
            else "chaser-forge-marketplace-install-repair"
        ),
    }
