from __future__ import annotations

import json
from pathlib import Path
import zipfile

from runtime.studio.capture_markdown_release_distribution import (
    REQUIRED_PROOFS,
    build_release_distribution,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fake_signature(
    status: str,
    subject: str = "CN=ChaseOS Test",
    thumbprint: str = "A" * 40,
):
    def reader(_path: Path) -> dict[str, str]:
        return {
            "status": status,
            "subject": subject,
            "thumbprint": thumbprint,
            "status_message": "",
        }

    return reader


def _fake_certificates(
    available: bool = True,
    subject: str = "CN=ChaseOS Test",
    thumbprint: str = "A" * 40,
):
    def reader() -> dict:
        return {
            "available": available,
            "usable_count": 1 if available else 0,
            "certificates": [
                {
                    "StoreLocation": "CurrentUser",
                    "Subject": subject,
                    "Thumbprint": thumbprint,
                    "HasPrivateKey": available,
                    "NotAfter": "2027-01-01T00:00:00.0000000Z",
                }
            ]
            if available
            else [],
            "errors": [],
        }

    return reader


def _seed_release_vault(root: Path) -> None:
    extension = root / "runtime/browser_extension/capture_to_markdown"
    extension.mkdir(parents=True)
    _write_json(
        extension / "manifest.json",
        {
            "manifest_version": 3,
            "name": "ChaseOS Capture to Markdown",
            "version": "0.1.0",
            "permissions": ["activeTab", "downloads", "scripting", "tabs"],
        },
    )
    (extension / "popup.html").write_text("<button>Capture</button>", encoding="utf-8")
    (extension / "popup.js").write_text("console.log('capture');", encoding="utf-8")
    (extension / "service_worker.js").write_text("console.log('worker');", encoding="utf-8")
    (extension / "content_script.js").write_text("document.body.innerText;", encoding="utf-8")
    (extension / "README.md").write_text("Capture to Markdown", encoding="utf-8")
    studio = root / "dist/studio/ChaseOS-Studio.exe"
    installer = root / "dist/studio/ChaseOS-Installer.exe"
    studio.parent.mkdir(parents=True)
    studio.write_bytes(b"studio")
    installer.write_bytes(b"installer")
    for proof_path in REQUIRED_PROOFS.values():
        _write_json(root / proof_path, {"ok": True, "status": "ok"})


def test_release_distribution_packages_extension_and_notes(tmp_path: Path) -> None:
    _seed_release_vault(tmp_path)

    result = build_release_distribution(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        signature_reader=_fake_signature("Valid"),
        certificate_reader=_fake_certificates(True),
    )

    package_path = tmp_path / result["browser_extension_package"]["path"]
    manifest_path = tmp_path / result["release_manifest_path"]
    notes_path = tmp_path / result["operator_release_notes_path"]

    assert result["release_ready"] is True
    assert result["signed_installer_refresh_complete"] is True
    assert result["browser_extension_distribution_package_complete"] is True
    assert result["signing_certificate_inventory"]["available"] is True
    assert result["next_signing_commands"]["certificate_available"] is True
    assert result["signing_posture"]["release_distribution_scope"] == "certificate_authority_signed"
    assert result["signing_posture"]["public_certificate_authority_release"] is True
    assert package_path.exists()
    assert manifest_path.exists()
    assert notes_path.exists()
    with zipfile.ZipFile(package_path, "r") as archive:
        assert "manifest.json" in archive.namelist()
        assert "service_worker.js" in archive.namelist()


def test_release_distribution_reports_unsigned_installer_not_ready(tmp_path: Path) -> None:
    _seed_release_vault(tmp_path)

    result = build_release_distribution(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        signature_reader=_fake_signature("NotSigned"),
        certificate_reader=_fake_certificates(False),
    )

    assert result["release_ready"] is False
    assert result["signed_installer_refresh_complete"] is False
    assert result["browser_extension_distribution_package_complete"] is True
    assert result["signing_certificate_inventory"]["available"] is False
    assert result["signing_posture"]["release_distribution_scope"] == "unsigned"
    assert "installer_executable_not_signed" in result["warnings"]


def test_release_distribution_reports_local_current_user_signing_scope(tmp_path: Path) -> None:
    _seed_release_vault(tmp_path)
    subject = "CN=ChaseOS Capture Markdown Local Code Signing 2026-05-31"
    thumbprint = "C" * 40

    result = build_release_distribution(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        signature_reader=_fake_signature("Valid", subject=subject, thumbprint=thumbprint),
        certificate_reader=_fake_certificates(True, subject=subject, thumbprint=thumbprint),
    )

    notes_path = tmp_path / result["operator_release_notes_path"]
    notes = notes_path.read_text(encoding="utf-8")

    assert result["release_ready"] is True
    assert result["signing_posture"]["release_distribution_scope"] == "local_current_user_signed"
    assert result["signing_posture"]["local_current_user_certificate_used"] is True
    assert result["signing_posture"]["public_certificate_authority_release"] is False
    assert result["signing_posture"]["signature_subjects"] == [subject]
    assert result["signing_posture"]["signature_thumbprints"] == [thumbprint]
    assert "local_current_user_code_signing_certificate_used" in result["warnings"]
    assert "not a public certificate-authority release" in notes


def test_release_distribution_can_require_public_certificate_authority(tmp_path: Path) -> None:
    _seed_release_vault(tmp_path)
    subject = "CN=ChaseOS Capture Markdown Local Code Signing 2026-05-31"
    thumbprint = "C" * 40

    result = build_release_distribution(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        require_public_certificate_authority=True,
        signature_reader=_fake_signature("Valid", subject=subject, thumbprint=thumbprint),
        certificate_reader=_fake_certificates(True, subject=subject, thumbprint=thumbprint),
    )

    notes_path = tmp_path / result["operator_release_notes_path"]
    notes = notes_path.read_text(encoding="utf-8")

    assert result["release_ready"] is False
    assert result["public_certificate_authority_release_required"] is True
    assert result["signing_posture"]["release_distribution_scope"] == "local_current_user_signed"
    assert result["signing_posture"]["public_certificate_authority_release"] is False
    assert "public_certificate_authority_signature_required" in result["errors"]
    assert "local_current_user_signature_not_public_distribution_ready" in result["warnings"]
    assert "Public certificate-authority required by this manifest: `yes`" in notes


def test_release_distribution_public_certificate_authority_requirement_passes(
    tmp_path: Path,
) -> None:
    _seed_release_vault(tmp_path)

    result = build_release_distribution(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        require_public_certificate_authority=True,
        signature_reader=_fake_signature("Valid", subject="CN=ChaseOS Public Release"),
        certificate_reader=_fake_certificates(True, subject="CN=ChaseOS Public Release"),
    )

    assert result["release_ready"] is True
    assert result["public_certificate_authority_release_required"] is True
    assert result["signing_posture"]["release_distribution_scope"] == "certificate_authority_signed"
    assert result["signing_posture"]["public_certificate_authority_release"] is True
    assert "public_certificate_authority_signature_required" not in result["errors"]
