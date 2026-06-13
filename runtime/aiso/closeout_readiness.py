from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _exists(root: Path, rel_path: str | None) -> bool:
    return bool(rel_path) and (root / rel_path).is_file()


def _proof_dirs(vault: Path) -> list[Path]:
    proof_root = vault / "07_LOGS" / "Workflow-Proofs"
    if not proof_root.exists():
        return []
    return sorted((p for p in proof_root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)


def _find_visual_dry_run(vault: Path) -> dict[str, Any] | None:
    for proof_dir in _proof_dirs(vault):
        manifest_path = proof_dir / "aiso-proof-manifest.json"
        audit_path = proof_dir / "aiso-audit-envelope.json"
        manifest = _load_json(manifest_path)
        audit = _load_json(audit_path)
        if manifest.get("status") != "dry_run_local_proof_packet" or not audit:
            continue
        artifacts = audit.get("visual_proof_artifacts") if isinstance(audit.get("visual_proof_artifacts"), dict) else {}
        required = {
            "manifest": _rel(manifest_path, vault),
            "audit": _rel(audit_path, vault),
            "proof_packet_html": artifacts.get("proof_packet_html"),
            "proof_packet_png": artifacts.get("proof_packet_png"),
            "email_preview_html": artifacts.get("email_preview_html"),
            "email_preview_png": artifacts.get("email_preview_png"),
            "portal_preview_html": artifacts.get("portal_preview_html"),
            "portal_preview_png": artifacts.get("portal_preview_png"),
        }
        missing = [name for name, rel_path in required.items() if not _exists(vault, rel_path)]
        authority = manifest.get("authority") if isinstance(manifest.get("authority"), dict) else {}
        blocked_actions_ok = all(
            authority.get(key) is False
            for key in (
                "original_mutation_performed",
                "provider_call_performed",
                "browser_submit_performed",
                "email_send_performed",
                "credential_access_performed",
                "canonical_promotion_performed",
            )
        )
        if not missing and blocked_actions_ok:
            return {
                "proof_id": proof_dir.name,
                "manifest_path": required["manifest"],
                "audit_path": required["audit"],
                "visual_artifacts": required,
            }
    return None


def _find_rename_package_proof(vault: Path) -> dict[str, Any] | None:
    for proof_dir in _proof_dirs(vault):
        manifest_path = proof_dir / "aiso-proof-manifest.json"
        manifest = _load_json(manifest_path)
        if manifest.get("status") != "package_approval_consumed":
            continue
        package_record = manifest.get("package_approval_consumption")
        authority = manifest.get("authority")
        if not isinstance(package_record, dict) or not isinstance(authority, dict):
            continue
        package_path = str(package_record.get("package_path") or "")
        package_record_path = proof_dir / "aiso-package-approval-consumption.json"
        blocked_actions_ok = all(
            authority.get(key) is False
            for key in (
                "email_send_performed",
                "browser_submit_performed",
                "provider_call_performed",
                "credential_access_performed",
                "canonical_promotion_performed",
            )
        )
        if package_path and (vault / package_path).is_file() and package_record_path.is_file() and blocked_actions_ok:
            return {
                "proof_id": proof_dir.name,
                "manifest_path": _rel(manifest_path, vault),
                "package_record_path": _rel(package_record_path, vault),
                "package_path": package_path,
                "zip_members": package_record.get("zip_members") or [],
            }
    return None


def build_aiso_real_test_closeout_readiness(vault_root: str | Path) -> dict[str, Any]:
    """Summarize whether AISO development is complete before a real-media closeout test.

    This is a read-only status contract. It does not scan ambient folders, rename
    files, create packages, send email, open browsers, call providers, read
    credentials, or promote canonical knowledge.
    """
    vault = Path(vault_root).resolve()
    dry_run = _find_visual_dry_run(vault)
    package_proof = _find_rename_package_proof(vault)
    missing_development = []
    if dry_run is None:
        missing_development.append("visual dry-run proof packet with email/portal screenshot artifacts")
    if package_proof is None:
        missing_development.append("approval-consumed rename plus package/zip proof")

    return {
        "ok": not missing_development,
        "surface": "aiso_real_test_closeout_readiness",
        "ready_for_real_test_closeout": not missing_development,
        "remaining_development_passes": missing_development,
        "remaining_closeout_only": []
        if missing_development
        else [
            "Run one operator-declared safe-root real media test: candidate selection, explicit rename approval, explicit package approval, zip verification, and proof record review."
        ],
        "deferred_external_authority": [
            "live email send adapter",
            "live browser/portal submit adapter",
            "provider-backed transcript/OCR/visual comprehension",
            "credential access",
            "canonical knowledge promotion",
        ],
        "evidence": {
            "dry_run_visual_proof": dry_run,
            "rename_package_proof": package_proof,
        },
        "authority": {
            "read_only_status": True,
            "ambient_scan_performed": False,
            "original_mutation_performed": False,
            "package_write_performed": False,
            "email_send_performed": False,
            "browser_submit_performed": False,
            "provider_call_performed": False,
            "credential_access_performed": False,
            "canonical_promotion_performed": False,
        },
    }
