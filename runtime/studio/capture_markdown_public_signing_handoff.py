"""Public certificate-authority signing handoff for Capture to Markdown."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

from runtime.studio.capture_markdown_release_distribution import (
    _code_signing_certificate_inventory,
)


PUBLIC_HANDOFF_SCHEMA_VERSION = "chaseos.capture_markdown.public_signing_handoff.v1"
LOCAL_SIGNING_SUBJECT_PREFIX = "CN=ChaseOS Capture Markdown Local Code Signing"
OPERATOR_BRIEF_DIR = Path("07_LOGS/Operator-Briefs")
RELEASE_MANIFEST = Path("dist/release/capture-markdown")
STUDIO_EXE = Path("dist/studio/ChaseOS-Studio.exe")
INSTALLER_EXE = Path("dist/studio/ChaseOS-Installer.exe")

CertificateReader = Callable[[], dict[str, Any]]


def build_public_signing_handoff(
    vault_root: str | Path,
    *,
    release_date: str | None = None,
    generated_at: str | None = None,
    certificate_reader: CertificateReader | None = None,
    write_report: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    date = release_date or datetime.now().strftime("%Y-%m-%d")
    timestamp = generated_at or _now_utc()
    manifest_path = vault / RELEASE_MANIFEST / date / "release-manifest.json"
    manifest = _read_json(manifest_path)
    inventory = (
        certificate_reader()
        if certificate_reader is not None
        else _code_signing_certificate_inventory()
    )
    public_candidates = _public_certificate_candidates(inventory)
    selected = public_candidates[0] if public_candidates else None
    local_release_ready = bool(manifest.get("release_ready"))
    current_scope = (
        (manifest.get("signing_posture") or {}).get("release_distribution_scope")
        if isinstance(manifest.get("signing_posture"), dict)
        else ""
    )
    errors: list[str] = []
    warnings: list[str] = []
    if not manifest_path.exists():
        errors.append("release_manifest_missing")
    if not public_candidates:
        errors.append("public_certificate_authority_certificate_missing")
    if current_scope == "local_current_user_signed":
        warnings.append("current_release_signed_with_local_current_user_certificate")

    status = (
        "ready_to_sign_public_release"
        if public_candidates and local_release_ready and not errors
        else "public_certificate_authority_certificate_required"
    )
    result: dict[str, Any] = {
        "schema_version": PUBLIC_HANDOFF_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "release_date": date,
        "status": status,
        "ready_to_attempt_public_signing": status == "ready_to_sign_public_release",
        "vault_root": str(vault),
        "release_manifest_path": _relative_or_absolute(manifest_path, vault),
        "local_release_ready": local_release_ready,
        "current_release_distribution_scope": current_scope,
        "current_public_certificate_authority_release": bool(
            (manifest.get("signing_posture") or {}).get("public_certificate_authority_release")
            if isinstance(manifest.get("signing_posture"), dict)
            else False
        ),
        "studio_executable": _artifact_presence(vault, STUDIO_EXE),
        "installer_executable": _artifact_presence(vault, INSTALLER_EXE),
        "certificate_inventory": inventory,
        "public_certificate_candidates": public_candidates,
        "selected_public_certificate_candidate": selected or {},
        "commands": _commands(vault, date, selected),
        "report_path": str(OPERATOR_BRIEF_DIR / f"{date}-capture-markdown-public-signing-handoff.json"),
        "markdown_report_path": str(OPERATOR_BRIEF_DIR / f"{date}-capture-markdown-public-signing-handoff.md"),
        "errors": errors,
        "warnings": warnings,
        "boundaries": {
            "read_raw_private_key_or_secret": False,
            "signed_artifacts": False,
            "created_certificate": False,
            "requested_external_certificate": False,
            "published_external_release": False,
            "installed_browser_extension": False,
            "mutated_host_startup": False,
        },
    }
    if write_report:
        report_path = Path(result["report_path"])
        markdown_path = Path(result["markdown_report_path"])
        report_full_path = vault / report_path
        markdown_full_path = vault / markdown_path
        report_full_path.parent.mkdir(parents=True, exist_ok=True)
        report_full_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        markdown_full_path.write_text(_markdown_report(result), encoding="utf-8")
        report_full_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def _public_certificate_candidates(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for cert in inventory.get("certificates") or []:
        subject = str(cert.get("Subject") or "")
        if not cert.get("Thumbprint") or cert.get("HasPrivateKey") is not True:
            continue
        if subject.startswith(LOCAL_SIGNING_SUBJECT_PREFIX):
            continue
        candidates.append(
            {
                "StoreLocation": str(cert.get("StoreLocation") or cert.get("Store") or "CurrentUser"),
                "Subject": subject,
                "Thumbprint": str(cert.get("Thumbprint") or ""),
                "NotAfter": str(cert.get("NotAfter") or ""),
                "HasPrivateKey": True,
            }
        )
    return sorted(candidates, key=lambda item: (item["StoreLocation"], item["Subject"]))


def _commands(vault: Path, date: str, selected: dict[str, Any] | None) -> dict[str, str]:
    thumbprint = (selected or {}).get("Thumbprint") or "<PUBLIC_CERTIFICATE_THUMBPRINT>"
    store = (selected or {}).get("StoreLocation") or "CurrentUser"
    return {
        "sign_existing_studio_executable": (
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"$cert=Get-Item Cert:\\{store}\\My\\{thumbprint}; "
            f"Set-AuthenticodeSignature -FilePath '{vault / STUDIO_EXE}' -Certificate $cert\""
        ),
        "sign_existing_installer_executable": (
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"$cert=Get-Item Cert:\\{store}\\My\\{thumbprint}; "
            f"Set-AuthenticodeSignature -FilePath '{vault / INSTALLER_EXE}' -Certificate $cert\""
        ),
        "regenerate_public_release_manifest": (
            "python -m runtime.studio.capture_markdown_release_distribution "
            f"--vault-root \"{vault}\" --release-date {date} "
            "--require-public-certificate-authority --json"
        ),
    }


def _artifact_presence(vault: Path, relative: Path) -> dict[str, Any]:
    path = vault / relative
    return {
        "path": str(relative),
        "exists": path.exists() and path.is_file(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
    }


def _markdown_report(result: dict[str, Any]) -> str:
    candidates = result.get("public_certificate_candidates") or []
    candidate_lines = "\n".join(
        f"- `{item['Subject']}` / `{item['StoreLocation']}` / `{item['Thumbprint']}`"
        for item in candidates
    ) or "- None found"
    errors = "\n".join(f"- {item}" for item in result.get("errors", [])) or "- None"
    warnings = "\n".join(f"- {item}" for item in result.get("warnings", [])) or "- None"
    commands = result.get("commands", {})
    return f"""# Capture to Markdown Public Signing Handoff - {result['release_date']}

Status: `{result['status']}`

Ready to attempt public signing: `{result['ready_to_attempt_public_signing']}`

Local release ready: `{result['local_release_ready']}`

Current signing scope: `{result['current_release_distribution_scope']}`

## Public Certificate Candidates

{candidate_lines}

## Commands

Sign existing Studio executable:

```powershell
{commands.get('sign_existing_studio_executable', '')}
```

Sign existing installer executable:

```powershell
{commands.get('sign_existing_installer_executable', '')}
```

Regenerate public release manifest:

```powershell
{commands.get('regenerate_public_release_manifest', '')}
```

## Errors

{errors}

## Warnings

{warnings}

## Boundary

This report does not read raw private keys or secrets, create a certificate, request an external certificate, sign artifacts, publish a release, install a browser extension, or mutate host startup.
"""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare a Capture to Markdown public signing handoff report."
    )
    parser.add_argument("--vault-root", default=".", help="ChaseOS vault/repository root.")
    parser.add_argument("--release-date", default="", help="Release date folder.")
    parser.add_argument("--write-report", action="store_true", help="Write JSON and Markdown reports.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_public_signing_handoff(
        args.vault_root,
        release_date=args.release_date or None,
        write_report=args.write_report,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result["status"])
        if result.get("markdown_report_path"):
            print(result["markdown_report_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
