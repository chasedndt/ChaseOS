"""Capture to Markdown release distribution packaging.

This module prepares local release artifacts for the Capture to Markdown lane:
browser extension zip packaging, artifact hash manifest, signature status
readback, and operator release notes. It does not create signing certificates,
publish externally, or mutate host startup state.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from typing import Any, Callable
import zipfile


RELEASE_SCHEMA_VERSION = "chaseos.capture_markdown.release_distribution.v1"
EXTENSION_DIR = Path("runtime/browser_extension/capture_to_markdown")
STUDIO_EXE = Path("dist/studio/ChaseOS-Studio.exe")
INSTALLER_EXE = Path("dist/studio/ChaseOS-Installer.exe")
PROOF_ROOT = Path("07_LOGS/Visual-QA")
OPERATOR_BRIEF_DIR = Path("07_LOGS/Operator-Briefs")

REQUIRED_PROOFS = {
    "capture_overlay_palette": Path(
        "07_LOGS/Visual-QA/2026-05-29-capture-markdown-palette-proof/capture-palette-proof-summary.json"
    ),
    "display_region_capture": Path(
        "07_LOGS/Visual-QA/2026-05-29-capture-markdown-display-region-proof/display-region-proof-summary.json"
    ),
    "operating_system_wide_global_hotkey": Path(
        "07_LOGS/Visual-QA/2026-05-29-capture-markdown-global-hotkey-proof/global-hotkey-proof-summary.json"
    ),
    "browser_extension_capture": Path(
        "07_LOGS/Visual-QA/2026-05-29-capture-markdown-browser-extension-proof/browser-extension-proof-summary.json"
    ),
    "live_discord_command_capture": Path(
        "07_LOGS/Visual-QA/2026-05-29-capture-markdown-live-discord-command-proof/live-discord-command-proof-summary.json"
    ),
    "attachment_retention_controls": Path(
        "07_LOGS/Visual-QA/2026-05-29-capture-markdown-attachment-retention-proof/attachment-retention-proof-summary.json"
    ),
    "windows_media_optical_character_recognition": Path(
        "07_LOGS/Visual-QA/2026-05-29-capture-markdown-windows-photo-text-proof/windows-photo-text-proof-summary.json"
    ),
    "packaged_capture_page": Path(
        "07_LOGS/Visual-QA/2026-05-31-capture-markdown-final-closeout-clickthrough-r2/2026-05-31-capture-markdown-final-closeout-clickthrough-r2.json"
    ),
    "packaged_open_safety": Path(
        "07_LOGS/Visual-QA/2026-05-31-capture-markdown-final-closeout-open-safety-r2/2026-05-31-capture-markdown-final-closeout-open-safety-r2.json"
    ),
}


SignatureReader = Callable[[Path], dict[str, Any]]
CertificateReader = Callable[[], dict[str, Any]]


def build_release_distribution(
    vault_root: str | Path,
    *,
    release_date: str | None = None,
    generated_at: str | None = None,
    require_public_certificate_authority: bool = False,
    signature_reader: SignatureReader | None = None,
    certificate_reader: CertificateReader | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    date = release_date or datetime.now().strftime("%Y-%m-%d")
    timestamp = generated_at or _now_utc()
    extension_dir = vault / EXTENSION_DIR
    studio_exe = vault / STUDIO_EXE
    installer_exe = vault / INSTALLER_EXE
    release_root = vault / "dist" / "release" / "capture-markdown" / date
    extension_dist = vault / "dist" / "browser-extension"
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = extension_dir / "manifest.json"
    extension_manifest = _read_json(manifest_path, errors, "browser_extension_manifest")
    extension_version = str(extension_manifest.get("version") or "0.0.0")
    extension_name = str(extension_manifest.get("name") or "ChaseOS Capture to Markdown")
    extension_package = extension_dist / f"chaseos-capture-to-markdown-{extension_version}.zip"

    if not extension_dir.exists():
        errors.append("browser_extension_directory_missing")
    if extension_manifest.get("manifest_version") != 3:
        errors.append("browser_extension_manifest_v3_required")
    if "activeTab" not in set(extension_manifest.get("permissions") or []):
        errors.append("browser_extension_active_tab_permission_missing")

    release_root.mkdir(parents=True, exist_ok=True)
    extension_dist.mkdir(parents=True, exist_ok=True)

    extension_package_info: dict[str, Any] = {
        "path": str(extension_package.relative_to(vault)),
        "exists": False,
        "size_bytes": 0,
        "sha256": "",
        "manifest_version": extension_manifest.get("manifest_version"),
        "extension_version": extension_version,
        "extension_name": extension_name,
        "contains_manifest_at_zip_root": False,
        "file_count": 0,
    }
    if not errors:
        extension_files = _extension_files(extension_dir)
        if not extension_files:
            errors.append("browser_extension_files_missing")
        else:
            _write_extension_zip(extension_dir, extension_package, extension_files)
            zip_names = _zip_names(extension_package)
            extension_package_info.update(
                {
                    "exists": extension_package.exists(),
                    "size_bytes": extension_package.stat().st_size,
                    "sha256": _sha256_file(extension_package),
                    "contains_manifest_at_zip_root": "manifest.json" in zip_names,
                    "file_count": len(zip_names),
                }
            )
            if not extension_package_info["contains_manifest_at_zip_root"]:
                errors.append("browser_extension_zip_manifest_not_at_root")

    studio_info = _artifact_info(vault, studio_exe, "studio_executable", signature_reader)
    installer_info = _artifact_info(vault, installer_exe, "installer_executable", signature_reader)
    if not studio_info["exists"]:
        errors.append("studio_executable_missing")
    if not installer_info["exists"]:
        errors.append("installer_executable_missing")
    if installer_info["exists"] and studio_info["exists"]:
        try:
            if installer_exe.stat().st_mtime < studio_exe.stat().st_mtime:
                warnings.append("installer_executable_is_older_than_studio_executable")
        except OSError:
            warnings.append("artifact_timestamp_read_failed")

    proof_status = _proof_status(vault)
    for proof_id, proof in proof_status.items():
        if not proof["exists"]:
            errors.append(f"{proof_id}_proof_missing")
        elif proof.get("ok") is not True:
            errors.append(f"{proof_id}_proof_not_ok")

    installer_signed = installer_info["signature_status"] == "Valid"
    studio_signed = studio_info["signature_status"] == "Valid"
    certificate_inventory = (
        certificate_reader()
        if certificate_reader is not None
        else _code_signing_certificate_inventory()
    )
    signed_installer_refresh_complete = bool(installer_info["exists"] and installer_signed)
    signing_posture = _signing_posture(installer_info, studio_info, certificate_inventory)
    if (
        require_public_certificate_authority
        and not signing_posture["public_certificate_authority_release"]
    ):
        errors.append("public_certificate_authority_signature_required")
        if signing_posture["local_current_user_certificate_used"]:
            warnings.append("local_current_user_signature_not_public_distribution_ready")
    release_ready = bool(
        not errors
        and extension_package_info["exists"]
        and signed_installer_refresh_complete
        and studio_info["exists"]
        and all(proof.get("ok") is True for proof in proof_status.values())
    )
    if installer_info["exists"] and not installer_signed:
        warnings.append("installer_executable_not_signed")
    if studio_info["exists"] and not studio_signed:
        warnings.append("studio_executable_not_signed")
    if signing_posture["local_current_user_certificate_used"]:
        warnings.append("local_current_user_code_signing_certificate_used")

    release_manifest = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "release_date": date,
        "release_status": "ready" if release_ready else "not_ready",
        "release_ready": release_ready,
        "public_certificate_authority_release_required": require_public_certificate_authority,
        "signed_installer_refresh_complete": signed_installer_refresh_complete,
        "browser_extension_distribution_package_complete": bool(
            extension_package_info["exists"]
            and extension_package_info["contains_manifest_at_zip_root"]
        ),
        "operator_release_notes_complete": True,
        "vault_root": str(vault),
        "studio_executable": studio_info,
        "installer_executable": installer_info,
        "browser_extension_package": extension_package_info,
        "signing_certificate_inventory": certificate_inventory,
        "signing_posture": signing_posture,
        "next_signing_commands": _next_signing_commands(vault, certificate_inventory),
        "proof_status": proof_status,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "boundaries": {
            "certificate_created_by_release_packager": False,
            "certificate_store_mutated_by_release_packager": False,
            "read_secret_or_private_key": False,
            "published_external_release": False,
            "installed_browser_extension": False,
            "mutated_host_startup": False,
            "replaced_primary_install": False,
        },
    }
    release_manifest["release_manifest_digest_sha256"] = _stable_digest(release_manifest)

    manifest_output = release_root / "release-manifest.json"
    manifest_output.write_text(
        json.dumps(release_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    release_manifest["release_manifest_path"] = str(manifest_output.relative_to(vault))

    notes_path = OPERATOR_BRIEF_DIR / f"{date}-capture-markdown-release-notes.md"
    notes_full_path = vault / notes_path
    notes_full_path.parent.mkdir(parents=True, exist_ok=True)
    notes_full_path.write_text(
        _operator_release_notes(release_manifest),
        encoding="utf-8",
    )
    release_manifest["operator_release_notes_path"] = str(notes_path)

    # Rewrite manifest after adding self-referential output paths.
    release_manifest["release_manifest_digest_sha256"] = _stable_digest(release_manifest)
    manifest_output.write_text(
        json.dumps(release_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return release_manifest


def _artifact_info(
    vault: Path,
    path: Path,
    role: str,
    signature_reader: SignatureReader | None,
) -> dict[str, Any]:
    exists = path.exists() and path.is_file()
    signature = (
        signature_reader(path)
        if signature_reader is not None and exists
        else _authenticode_signature(path)
        if exists
        else {"status": "Missing", "subject": "", "thumbprint": "", "status_message": ""}
    )
    return {
        "role": role,
        "path": str(path.relative_to(vault)) if _path_inside(path, vault) else str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "sha256": _sha256_file(path) if exists else "",
        "last_write_time_utc": _mtime_utc(path) if exists else "",
        "signature_status": signature.get("status", "Unknown"),
        "signature_subject": signature.get("subject", ""),
        "signature_thumbprint": signature.get("thumbprint", ""),
        "signature_status_message": signature.get("status_message", ""),
    }


def _authenticode_signature(path: Path) -> dict[str, str]:
    if platform.system() != "Windows":
        return {
            "status": "Unavailable",
            "subject": "",
            "thumbprint": "",
            "status_message": "Authenticode signature readback requires Windows.",
        }
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "& { param($p) "
                    "$s = Get-AuthenticodeSignature -LiteralPath $p; "
                    "[pscustomobject]@{"
                    "Status=[string]$s.Status;"
                    "StatusMessage=[string]$s.StatusMessage;"
                    "Subject=[string]$s.SignerCertificate.Subject;"
                    "Thumbprint=[string]$s.SignerCertificate.Thumbprint"
                    "} | ConvertTo-Json -Compress }"
                ),
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "status": "Unavailable",
            "subject": "",
            "thumbprint": "",
            "status_message": f"signature_read_failed:{type(exc).__name__}",
        }
    if completed.returncode != 0:
        return {
            "status": "Unavailable",
            "subject": "",
            "thumbprint": "",
            "status_message": completed.stderr.strip()[:500],
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "status": "Unavailable",
            "subject": "",
            "thumbprint": "",
            "status_message": "signature_json_parse_failed",
        }
    return {
        "status": str(payload.get("Status") or "Unknown"),
        "subject": str(payload.get("Subject") or ""),
        "thumbprint": str(payload.get("Thumbprint") or ""),
        "status_message": str(payload.get("StatusMessage") or ""),
    }


def _code_signing_certificate_inventory() -> dict[str, Any]:
    if platform.system() != "Windows":
        return {
            "available": False,
            "usable_count": 0,
            "certificates": [],
            "errors": ["code_signing_certificate_inventory_requires_windows"],
        }
    script = (
        "$items = @(); "
        "foreach ($store in @('CurrentUser','LocalMachine')) { "
        "  $certs = Get-ChildItem \"Cert:\\$store\\My\" -CodeSigningCert -ErrorAction SilentlyContinue; "
        "  foreach ($cert in $certs) { "
        "    $items += [pscustomobject]@{"
        "StoreLocation=$store;"
        "Subject=[string]$cert.Subject;"
        "Thumbprint=[string]$cert.Thumbprint;"
        "HasPrivateKey=[bool]$cert.HasPrivateKey;"
        "NotAfter=$cert.NotAfter.ToUniversalTime().ToString('o')"
        "    } "
        "  } "
        "} "
        "$items | ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "available": False,
            "usable_count": 0,
            "certificates": [],
            "errors": [f"code_signing_certificate_inventory_failed:{type(exc).__name__}"],
        }
    if completed.returncode != 0:
        return {
            "available": False,
            "usable_count": 0,
            "certificates": [],
            "errors": [completed.stderr.strip()[:500] or "code_signing_certificate_inventory_failed"],
        }
    raw = completed.stdout.strip()
    if not raw:
        certificates: list[dict[str, Any]] = []
    else:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "available": False,
                "usable_count": 0,
                "certificates": [],
                "errors": ["code_signing_certificate_inventory_json_invalid"],
            }
        certificates = parsed if isinstance(parsed, list) else [parsed] if isinstance(parsed, dict) else []
    usable = [
        cert
        for cert in certificates
        if cert.get("Thumbprint") and cert.get("HasPrivateKey") is True
    ]
    return {
        "available": bool(usable),
        "usable_count": len(usable),
        "certificates": certificates,
        "errors": [],
    }


def _next_signing_commands(vault: Path, certificate_inventory: dict[str, Any]) -> dict[str, Any]:
    sample_thumbprint = "<THUMBPRINT>"
    sample_store = "CurrentUser"
    for cert in certificate_inventory.get("certificates") or []:
        if cert.get("Thumbprint") and cert.get("HasPrivateKey") is True:
            sample_thumbprint = str(cert["Thumbprint"])
            sample_store = str(cert.get("StoreLocation") or "CurrentUser")
            break
    return {
        "certificate_available": bool(certificate_inventory.get("available")),
        "studio_sign_command": (
            "powershell -NoProfile -ExecutionPolicy Bypass -File "
            "runtime\\studio\\shell\\build_exe.ps1 "
            f"-VaultRoot \"{vault}\" -Clean -NoShortcut "
            f"-SignThumbprint \"{sample_thumbprint}\" -SignStoreLocation {sample_store}"
        ),
        "installer_sign_command": (
            "powershell -NoProfile -ExecutionPolicy Bypass -File "
            "runtime\\studio\\shell\\build_installer.ps1 "
            f"-VaultRoot \"{vault}\" "
            f"-SignThumbprint \"{sample_thumbprint}\" -SignStoreLocation {sample_store}"
        ),
        "requires_real_trusted_certificate": True,
        "creates_certificate": False,
        "reads_raw_private_key_or_secret": False,
    }


def _signing_posture(
    installer_info: dict[str, Any],
    studio_info: dict[str, Any],
    certificate_inventory: dict[str, Any],
) -> dict[str, Any]:
    installer_subject = str(installer_info.get("signature_subject") or "")
    studio_subject = str(studio_info.get("signature_subject") or "")
    installer_thumbprint = str(installer_info.get("signature_thumbprint") or "")
    studio_thumbprint = str(studio_info.get("signature_thumbprint") or "")
    local_subject_prefix = "CN=ChaseOS Capture Markdown Local Code Signing"
    local_certificate_used = bool(
        installer_subject.startswith(local_subject_prefix)
        or studio_subject.startswith(local_subject_prefix)
    )
    same_certificate = bool(
        installer_thumbprint
        and studio_thumbprint
        and installer_thumbprint.upper() == studio_thumbprint.upper()
    )
    certificate_subjects = [
        str(cert.get("Subject") or "")
        for cert in certificate_inventory.get("certificates") or []
    ]
    local_certificate_available = any(
        subject.startswith(local_subject_prefix) for subject in certificate_subjects
    )
    return {
        "installer_signature_valid": installer_info.get("signature_status") == "Valid",
        "studio_signature_valid": studio_info.get("signature_status") == "Valid",
        "same_certificate_used_for_studio_and_installer": same_certificate,
        "local_current_user_certificate_used": local_certificate_used,
        "local_current_user_certificate_available": local_certificate_available,
        "signature_subjects": sorted({item for item in [installer_subject, studio_subject] if item}),
        "signature_thumbprints": sorted({item for item in [installer_thumbprint, studio_thumbprint] if item}),
        "public_certificate_authority_validated": bool(
            certificate_inventory.get("available")
            and not local_certificate_used
            and not local_certificate_available
        ),
        "public_certificate_authority_release": bool(
            installer_info.get("signature_status") == "Valid"
            and studio_info.get("signature_status") == "Valid"
            and certificate_inventory.get("available")
            and not local_certificate_used
            and not local_certificate_available
        ),
        "release_distribution_scope": (
            "local_current_user_signed"
            if local_certificate_used
            else "certificate_authority_signed"
            if certificate_inventory.get("available") and not local_certificate_available
            else "unsigned"
        ),
    }


def _proof_status(vault: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for proof_id, relative in REQUIRED_PROOFS.items():
        path = vault / relative
        payload = _read_json(path, [], proof_id) if path.exists() else {}
        result[proof_id] = {
            "path": str(relative),
            "exists": path.exists() and path.is_file(),
            "ok": payload.get("ok") if isinstance(payload, dict) else None,
            "status": payload.get("status", "") if isinstance(payload, dict) else "",
            "sha256": _sha256_file(path) if path.exists() and path.is_file() else "",
        }
    return result


def _extension_files(extension_dir: Path) -> list[Path]:
    excluded_parts = {"__pycache__"}
    files: list[Path] = []
    for path in extension_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(extension_dir)
        if any(part in excluded_parts for part in relative.parts):
            continue
        if path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(extension_dir).as_posix())


def _write_extension_zip(extension_dir: Path, package_path: Path, files: list[Path]) -> None:
    package_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(extension_dir).as_posix()
            info = zipfile.ZipInfo(relative)
            info.date_time = (2026, 5, 31, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())


def _zip_names(package_path: Path) -> set[str]:
    with zipfile.ZipFile(package_path, "r") as archive:
        return set(archive.namelist())


def _operator_release_notes(manifest: dict[str, Any]) -> str:
    status = "READY" if manifest["release_ready"] else "NOT READY"
    installer = manifest["installer_executable"]
    studio = manifest["studio_executable"]
    extension = manifest["browser_extension_package"]
    proof_lines = "\n".join(
        f"- {proof_id}: `{proof['path']}` (`ok={proof.get('ok')}`)"
        for proof_id, proof in manifest["proof_status"].items()
    )
    warnings = "\n".join(f"- {item}" for item in manifest.get("warnings", [])) or "- None"
    errors = "\n".join(f"- {item}" for item in manifest.get("errors", [])) or "- None"
    signing = manifest["signing_posture"]
    signature_subjects = ", ".join(signing.get("signature_subjects", [])) or "None"
    signature_thumbprints = ", ".join(signing.get("signature_thumbprints", [])) or "None"
    public_release = "yes" if signing.get("public_certificate_authority_release") else "no"
    public_required = "yes" if manifest.get("public_certificate_authority_release_required") else "no"
    local_release_note = (
        "This package is signed with a local CurrentUser ChaseOS certificate. "
        "That proves local integrity on this machine but is not a public certificate-authority release."
        if signing.get("local_current_user_certificate_used")
        else "This package does not use the local ChaseOS development signing certificate."
    )
    return f"""# Capture to Markdown Release Notes - {manifest['release_date']}

Status: {status}

## Release Artifacts

- Studio executable: `{studio['path']}`
- Studio executable SHA-256: `{studio['sha256']}`
- Studio executable signature: `{studio['signature_status']}`
- Installer executable: `{installer['path']}`
- Installer executable SHA-256: `{installer['sha256']}`
- Installer executable signature: `{installer['signature_status']}`
- Browser extension package: `{extension['path']}`
- Browser extension package SHA-256: `{extension['sha256']}`
- Release manifest: `{manifest.get('release_manifest_path', '')}`
- Code-signing certificate available: `{manifest['signing_certificate_inventory']['available']}`
- Signing scope: `{manifest['signing_posture']['release_distribution_scope']}`
- Public certificate-authority required by this manifest: `{public_required}`
- Public certificate-authority release: `{public_release}`
- Signature subject: `{signature_subjects}`
- Signature thumbprint: `{signature_thumbprints}`
- Signing note: {local_release_note}

## Capture to Markdown Proofs

{proof_lines}

## Operator Install Notes

1. Use the Studio executable only from `dist/studio/ChaseOS-Studio.exe`.
2. Install the browser extension package as an unpacked/developer extension or submit the zip to the chosen browser store after separate store review.
3. For this local release, confirm the installer and Studio executable signature statuses are `Valid` before handoff.
4. For public distribution outside this machine, rerun signing with a public certificate-authority code-signing certificate and regenerate the release manifest.

## Warnings

{warnings}

## Errors

{errors}

## Boundaries

- The release packager did not create a certificate.
- No secret or private key was read.
- No external release was published.
- No browser extension was installed automatically.
- No host startup setting was mutated.
"""


def _read_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{label}_missing")
        return {}
    except json.JSONDecodeError:
        errors.append(f"{label}_json_invalid")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{label}_must_be_object")
        return {}
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _stable_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("release_manifest_digest_sha256", None)
    body = json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest().upper()


def _mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def _path_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Capture to Markdown release artifacts.")
    parser.add_argument("--vault-root", default=".", help="ChaseOS vault/repository root.")
    parser.add_argument("--release-date", default="", help="Release date folder, for example 2026-05-31.")
    parser.add_argument(
        "--require-public-certificate-authority",
        action="store_true",
        help=(
            "Require a non-local public certificate-authority code-signing signature "
            "before marking the release ready."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_release_distribution(
        args.vault_root,
        release_date=args.release_date or None,
        require_public_certificate_authority=args.require_public_certificate_authority,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result["release_status"])
        print(result["release_manifest_path"])
        print(result["operator_release_notes_path"])
    return 0 if result["browser_extension_distribution_package_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
