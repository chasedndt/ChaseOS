from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.capture_markdown_public_signing_handoff import (
    build_public_signing_handoff,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_manifest(root: Path, release_ready: bool = True) -> None:
    _write_json(
        root / "dist/release/capture-markdown/2026-05-31/release-manifest.json",
        {
            "release_ready": release_ready,
            "signing_posture": {
                "release_distribution_scope": "local_current_user_signed",
                "public_certificate_authority_release": False,
            },
        },
    )
    studio = root / "dist/studio/ChaseOS-Studio.exe"
    installer = root / "dist/studio/ChaseOS-Installer.exe"
    studio.parent.mkdir(parents=True, exist_ok=True)
    studio.write_bytes(b"studio")
    installer.write_bytes(b"installer")


def _certificates(*certs: dict):
    def reader() -> dict:
        return {
            "available": bool(certs),
            "usable_count": len(certs),
            "certificates": list(certs),
            "errors": [],
        }

    return reader


def test_public_signing_handoff_reports_missing_public_certificate(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)

    result = build_public_signing_handoff(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        certificate_reader=_certificates(
            {
                "StoreLocation": "CurrentUser",
                "Subject": "CN=ChaseOS Capture Markdown Local Code Signing 2026-05-31",
                "Thumbprint": "C" * 40,
                "HasPrivateKey": True,
                "NotAfter": "2027-01-01T00:00:00Z",
            }
        ),
    )

    assert result["ready_to_attempt_public_signing"] is False
    assert result["public_certificate_candidates"] == []
    assert "public_certificate_authority_certificate_missing" in result["errors"]
    assert "current_release_signed_with_local_current_user_certificate" in result["warnings"]
    assert "<PUBLIC_CERTIFICATE_THUMBPRINT>" in result["commands"]["sign_existing_studio_executable"]


def test_public_signing_handoff_selects_public_candidate(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)
    thumbprint = "A" * 40

    result = build_public_signing_handoff(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        certificate_reader=_certificates(
            {
                "StoreLocation": "CurrentUser",
                "Subject": "CN=ChaseOS Public Release",
                "Thumbprint": thumbprint,
                "HasPrivateKey": True,
                "NotAfter": "2027-01-01T00:00:00Z",
            }
        ),
    )

    assert result["ready_to_attempt_public_signing"] is True
    assert result["selected_public_certificate_candidate"]["Thumbprint"] == thumbprint
    assert thumbprint in result["commands"]["sign_existing_studio_executable"]
    assert "--require-public-certificate-authority" in result["commands"][
        "regenerate_public_release_manifest"
    ]


def test_public_signing_handoff_writes_reports(tmp_path: Path) -> None:
    _seed_manifest(tmp_path)

    result = build_public_signing_handoff(
        tmp_path,
        release_date="2026-05-31",
        generated_at="2026-05-31T00:00:00Z",
        certificate_reader=_certificates(),
        write_report=True,
    )

    assert (tmp_path / result["report_path"]).exists()
    markdown_path = tmp_path / result["markdown_report_path"]
    assert markdown_path.exists()
    assert "Capture to Markdown Public Signing Handoff" in markdown_path.read_text(
        encoding="utf-8"
    )
