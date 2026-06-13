from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from runtime.forge.marketplace import (
    FORGE_MARKETPLACE_EXPORT_API_METHOD,
    FORGE_MARKETPLACE_HOSTED_BUNDLE_RECORD_TYPE,
    FORGE_MARKETPLACE_HOSTED_BUNDLE_SCHEMA_VERSION,
    FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID,
    FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE,
    FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID,
    FORGE_MARKETPLACE_PACKAGE_RECORD_TYPE,
    FORGE_MARKETPLACE_PACKAGE_SCHEMA_VERSION,
    FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_RECORD_TYPE,
    FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SCHEMA_VERSION,
    FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID,
    FORGE_MARKETPLACE_REMOTE_INDEX_RECORD_TYPE,
    FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION,
    FORGE_MARKETPLACE_STATIC_PUBLICATION_RECORD_TYPE,
    FORGE_MARKETPLACE_STATIC_PUBLICATION_SCHEMA_VERSION,
    FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RECORD_TYPE,
    FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SCHEMA_VERSION,
    FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_RECORD_TYPE,
    FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SCHEMA_VERSION,
    FORGE_MARKETPLACE_SURFACE_ID,
    build_forge_marketplace_catalog,
    build_forge_marketplace_export_package,
    build_forge_marketplace_hosted_export_bundle,
    build_forge_marketplace_import_preview,
    build_forge_marketplace_import_sandbox_approval,
    build_forge_marketplace_import_sandbox_request,
    build_forge_marketplace_install_execution,
    build_forge_marketplace_local_library,
    build_forge_marketplace_live_index_input_prefill,
    build_forge_marketplace_live_index_input_readiness,
    build_forge_marketplace_publish,
    build_forge_marketplace_published_static_index_registration,
    build_forge_marketplace_remote_distribution,
    build_forge_marketplace_remote_ingest_preview,
    build_forge_marketplace_remote_listing_ingest,
    build_forge_marketplace_static_host_publication,
    build_forge_marketplace_static_host_upload_handoff,
    build_forge_marketplace_static_host_upload_receipt,
)
from runtime.forge.approval_decision import build_forge_approval_decision_handoff
from runtime.forge.panel import load_demo_manifest
from runtime.forge.registry import SANDBOX_APPROVAL_RECORD_TYPE, SANDBOX_APPROVAL_SCOPE


def _write_approved_marketplace_import(vault: Path) -> tuple[dict[str, object], Path]:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(vault, manifest=manifest)
    approval_preview = build_forge_marketplace_import_sandbox_approval(
        vault,
        package_payload=package_preview["package_payload"],
    )
    written = build_forge_marketplace_import_sandbox_approval(
        vault,
        package_payload=package_preview["package_payload"],
        write_approval_request=True,
        request_digest=approval_preview["request_digest_sha256"],
    )
    artifact_path = vault / str(written["approval_artifact_path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    handoff = build_forge_approval_decision_handoff(
        vault,
        approval_artifact_path=written["approval_artifact_path"],
        decision="approved",
        expected_request_digest=str(written["request_digest_sha256"]),
        operator_statement=payload["operator_confirmation_text"],
        write_decision=True,
        reviewer_id="operator",
    )

    assert handoff["ok"] is True, handoff
    return written, artifact_path


def _write_live_index_static_publication_fixture(vault: Path, dirname: str = "local-operator-test") -> tuple[Path, str]:
    publication_dir = (
        vault
        / "07_LOGS"
        / "Workflow-Proofs"
        / "Forge-Marketplace-Static-Host-Publications"
        / dirname
    )
    publication_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "index.json": json.dumps(
            {
                "record_type": "forge_marketplace_remote_index",
                "schema_version": "forge.marketplace_remote_index.v1",
                "entries": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        "README.md": "# Chaser Forge Marketplace\n",
        "hosted-bundle.json": json.dumps({"record_type": "forge_marketplace_hosted_export_bundle"}, sort_keys=True)
        + "\n",
        "publication-manifest.json": json.dumps(
            {
                "record_type": FORGE_MARKETPLACE_STATIC_PUBLICATION_RECORD_TYPE,
                "schema_version": FORGE_MARKETPLACE_STATIC_PUBLICATION_SCHEMA_VERSION,
                "static_publication_digest_sha256": "fixture-static-publication",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    }
    for name, text in files.items():
        (publication_dir / name).write_text(text, encoding="utf-8")
    checksum_payload = {
        "record_type": "forge_marketplace_static_host_publication_checksums",
        "schema_version": "forge.marketplace_static_host_publication_checksums.v1",
        "static_publication_digest_sha256": "fixture-static-publication",
        "remote_index_digest_sha256": "fixture-remote-index",
        "hosted_bundle_digest_sha256": "fixture-hosted-bundle",
        "files": [
            {
                "path": name,
                "digest_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "size_bytes": len(text.encode("utf-8")),
            }
            for name, text in sorted(files.items())
        ],
    }
    (publication_dir / "checksums.json").write_text(
        json.dumps(checksum_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    index_sha256 = hashlib.sha256(files["index.json"].encode("utf-8")).hexdigest()
    return publication_dir, index_sha256


def _write_live_index_packet(
    vault: Path,
    *,
    public_index_url: str,
    hosted_base_url: str,
    host_label: str,
    local_static_publication_dir: str,
    local_index_sha256: str,
) -> Path:
    packet_path = vault / "live-index-input.json"
    packet_path.write_text(
        json.dumps(
            {
                "packet_type": "chaser_forge_live_index_json_verification_input",
                "schema_version": "chaser_forge.live_index_json_input.v1",
                "public_index_url": public_index_url,
                "hosted_base_url": hosted_base_url,
                "host_label": host_label,
                "local_static_publication_dir": local_static_publication_dir,
                "local_index_sha256": local_index_sha256,
                "uploaded_files": [
                    "index.json",
                    "README.md",
                    "hosted-bundle.json",
                    "publication-manifest.json",
                    "checksums.json",
                ],
                "operator_upload_confirmation": (
                    "I confirm I uploaded the five Chaser Forge static publication files from "
                    f"{local_static_publication_dir} to {hosted_base_url} without modification."
                ),
                "operator_fetch_approval_statement": (
                    f"I approve Codex to fetch {public_index_url} once for Chaser Forge live index verification, "
                    f"compare it against local_index_sha256={local_index_sha256}, and write local JSON/Markdown "
                    "verification evidence only. I do not approve upload, external registry mutation, package install, "
                    "payment/license mutation, credential use, provider/model calls, Agent Bus dispatch, or "
                    "protected-core mutation."
                ),
                "notes": "",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return packet_path


def test_marketplace_export_preview_packages_valid_manifest_without_writes(tmp_path: Path) -> None:
    manifest = load_demo_manifest()

    preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)

    assert preview["ok"] is True
    assert preview["surface"] == FORGE_MARKETPLACE_SURFACE_ID
    assert preview["status"] == "forge_marketplace_export_package_preview_ready"
    assert preview["preview_only"] is True
    assert preview["package_artifact_written"] is False
    assert preview["marketplace_template_declared"] is True
    assert preview["package_payload"]["record_type"] == FORGE_MARKETPLACE_PACKAGE_RECORD_TYPE
    assert preview["package_payload"]["schema_version"] == FORGE_MARKETPLACE_PACKAGE_SCHEMA_VERSION
    assert preview["package_payload"]["api_method"] == FORGE_MARKETPLACE_EXPORT_API_METHOD
    assert preview["package_payload"]["package_digest_sha256"] == preview["package_digest_sha256"]
    assert preview["package_payload"]["marketplace"]["publish_allowed"] is False
    assert preview["package_payload"]["marketplace"]["auto_install_allowed"] is False
    assert preview["authority"]["writes_marketplace_package_artifact"] is False
    assert preview["registry_written"] is False
    assert preview["extension_files_written"] == []
    assert not (tmp_path / preview["package_artifact_path"]).exists()


def test_marketplace_export_write_requires_exact_digest(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)

    wrong = build_forge_marketplace_export_package(
        tmp_path,
        manifest=manifest,
        write_package=True,
        expected_package_digest="wrong",
    )
    assert wrong["ok"] is False
    assert wrong["package_artifact_written"] is False
    assert "expected_package_digest_mismatch" in wrong["blockers"]
    assert not (tmp_path / wrong["package_artifact_path"]).exists()

    written = build_forge_marketplace_export_package(
        tmp_path,
        manifest=manifest,
        write_package=True,
        expected_package_digest=preview["package_digest_sha256"],
    )
    artifact_path = tmp_path / written["package_artifact_path"]
    assert written["ok"] is True
    assert written["package_artifact_written"] is True
    assert written["package_digest_sha256"] == preview["package_digest_sha256"]
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["package_digest_sha256"] == preview["package_digest_sha256"]
    assert payload["marketplace"]["remote_marketplace_call_allowed"] is False
    assert payload["marketplace"]["import_install_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()

    duplicate = build_forge_marketplace_export_package(
        tmp_path,
        manifest=manifest,
        write_package=True,
        expected_package_digest=preview["package_digest_sha256"],
    )
    assert duplicate["ok"] is False
    assert duplicate["package_artifact_written"] is False
    assert "package_artifact_already_present" in duplicate["blockers"]


def test_marketplace_import_preview_validates_written_package_without_install(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    written = build_forge_marketplace_export_package(
        tmp_path,
        manifest=manifest,
        write_package=True,
        expected_package_digest=preview["package_digest_sha256"],
    )

    import_preview = build_forge_marketplace_import_preview(
        tmp_path,
        package_artifact_path=written["package_artifact_path"],
        expected_package_digest=preview["package_digest_sha256"],
    )

    assert import_preview["ok"] is True
    assert import_preview["status"] == "forge_marketplace_import_preview_ready"
    assert import_preview["package_digest_sha256"] == preview["package_digest_sha256"]
    assert import_preview["recomputed_package_digest_sha256"] == preview["package_digest_sha256"]
    assert import_preview["marketplace_publish_allowed"] is False
    assert import_preview["auto_install_allowed"] is False
    assert import_preview["registry_written"] is False
    assert import_preview["extension_files_written"] == []
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_publish_writes_local_public_catalog_with_exact_digest(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)

    publish_preview = build_forge_marketplace_publish(
        tmp_path,
        package_payload=package_preview["package_payload"],
    )
    assert publish_preview["ok"] is True
    assert publish_preview["status"] == "forge_marketplace_publish_preview_ready"
    assert publish_preview["catalog_listing_written"] is False
    assert publish_preview["remote_marketplace_call_allowed"] is False

    wrong = build_forge_marketplace_publish(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_listing=True,
        expected_listing_digest="wrong",
    )
    assert wrong["ok"] is False
    assert wrong["catalog_listing_written"] is False
    assert "expected_listing_digest_required_or_mismatched" in wrong["blockers"]

    published = build_forge_marketplace_publish(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_listing=True,
        expected_listing_digest=publish_preview["listing_digest_sha256"],
    )
    assert published["ok"] is True
    assert published["catalog_listing_written"] is True
    assert published["local_public_catalog_published"] is True

    catalog = build_forge_marketplace_catalog(tmp_path)
    assert catalog["ok"] is True
    assert catalog["catalog_exists"] is True
    assert catalog["entry_count"] == 1
    assert catalog["entries"][0]["listing_digest_sha256"] == publish_preview["listing_digest_sha256"]
    assert catalog["entries"][0]["package_digest_sha256"] == package_preview["package_digest_sha256"]
    assert catalog["entries"][0]["remote_marketplace_call_allowed"] is False

    duplicate = build_forge_marketplace_publish(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_listing=True,
        expected_listing_digest=publish_preview["listing_digest_sha256"],
    )
    assert duplicate["ok"] is True
    assert duplicate["catalog_listing_reused"] is True
    assert build_forge_marketplace_catalog(tmp_path)["entry_count"] == 1


def test_marketplace_remote_distribution_writes_digest_bound_index_without_network_or_payment(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)

    preview = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    assert preview["ok"] is True
    assert preview["surface"] == FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID
    assert preview["status"] == "forge_marketplace_remote_distribution_ready"
    assert preview["remote_index_artifact_written"] is False
    assert preview["remote_index_payload"]["record_type"] == FORGE_MARKETPLACE_REMOTE_INDEX_RECORD_TYPE
    assert preview["remote_index_payload"]["schema_version"] == FORGE_MARKETPLACE_REMOTE_INDEX_SCHEMA_VERSION
    assert preview["remote_index_payload"]["remote_index_digest_sha256"] == preview["remote_index_digest_sha256"]
    assert preview["remote_index_payload"]["publisher_attestation_digest_sha256"] == preview["publisher_attestation_digest_sha256"]
    assert preview["remote_network_publish_allowed"] is False
    assert preview["payment_mutation_allowed"] is False
    assert preview["license_checkout_allowed"] is False
    assert preview["package_install_allowed"] is False
    assert preview["authority"]["writes_marketplace_remote_index_artifact"] is False

    wrong = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest="wrong",
    )
    assert wrong["ok"] is False
    assert wrong["remote_index_artifact_written"] is False
    assert "expected_remote_index_digest_required_or_mismatched" in wrong["blockers"]

    written = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=preview["remote_index_digest_sha256"],
    )
    artifact_path = tmp_path / written["remote_index_artifact_path"]
    assert written["ok"] is True
    assert written["remote_index_artifact_written"] is True
    assert written["authority"]["writes_marketplace_remote_index_artifact"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["remote_network_publish_allowed"] is False
    assert payload["payment_mutation_allowed"] is False
    assert payload["license_checkout_allowed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_remote_ingest_verifies_publisher_and_writes_local_catalog_only(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    distribution_preview = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    written_index = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=distribution_preview["remote_index_digest_sha256"],
    )

    untrusted = build_forge_marketplace_remote_ingest_preview(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_listing_digest=written_index["listing_digest_sha256"],
        trusted_publisher_ids=["different-publisher"],
    )
    assert untrusted["ok"] is False
    assert "remote_publisher_not_trusted" in untrusted["blockers"]

    preview = build_forge_marketplace_remote_ingest_preview(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_listing_digest=written_index["listing_digest_sha256"],
        trusted_publisher_ids=["local-operator"],
    )
    assert preview["ok"] is True
    assert preview["publisher_trusted"] is True
    assert preview["publisher_attestation_verified"] is True
    assert preview["payment_mutation_allowed"] is False
    assert preview["license_checkout_allowed"] is False
    assert preview["package_install_allowed"] is False

    wrong = build_forge_marketplace_remote_listing_ingest(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_listing_digest=written_index["listing_digest_sha256"],
        trusted_publisher_ids=["local-operator"],
        operator_confirmation="wrong",
        write_listing=True,
    )
    assert wrong["ok"] is False
    assert wrong["catalog_listing_written"] is False
    assert "operator_confirmation_required_or_mismatched" in wrong["blockers"]

    ingested = build_forge_marketplace_remote_listing_ingest(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_listing_digest=written_index["listing_digest_sha256"],
        trusted_publisher_ids=["local-operator"],
        operator_confirmation=preview["operator_confirmation_text"],
        write_listing=True,
    )
    assert ingested["ok"] is True
    assert ingested["catalog_listing_written"] is True
    assert ingested["remote_listing_ingested"] is True
    assert ingested["remote_marketplace_call_allowed"] is False
    assert ingested["payment_mutation_allowed"] is False
    assert ingested["license_checkout_allowed"] is False
    assert ingested["package_install_allowed"] is False

    catalog = build_forge_marketplace_catalog(tmp_path)
    assert catalog["entry_count"] == 1
    assert catalog["entries"][0]["remote_distribution_source"] == "verified_remote_index"
    assert catalog["entries"][0]["publisher_attestation_verified"] is True
    assert catalog["entries"][0]["listing_digest_sha256"] == written_index["listing_digest_sha256"]
    library = build_forge_marketplace_local_library(tmp_path)
    assert library["library_item_count"] == 1
    assert library["items"][0]["source"] == "remote_verified_catalog"
    assert library["items"][0]["publisher_attestation_verified"] is True
    assert library["items"][0]["installed"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_hosted_export_bundle_writes_static_artifact_without_network_or_payment(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    distribution_preview = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    written_index = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=distribution_preview["remote_index_digest_sha256"],
    )

    preview = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        publisher_id="local-operator",
        static_base_url="https://example.invalid/chaser-forge",
    )
    assert preview["ok"] is True
    assert preview["surface"] == FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID
    assert preview["status"] == "forge_marketplace_hosted_export_bundle_ready"
    assert preview["hosted_bundle_artifact_written"] is False
    assert preview["hosted_bundle_payload"]["record_type"] == FORGE_MARKETPLACE_HOSTED_BUNDLE_RECORD_TYPE
    assert preview["hosted_bundle_payload"]["schema_version"] == FORGE_MARKETPLACE_HOSTED_BUNDLE_SCHEMA_VERSION
    assert preview["hosted_bundle_payload"]["hosted_bundle_digest_sha256"] == preview["hosted_bundle_digest_sha256"]
    assert preview["hosted_bundle_payload"]["remote_index_digest_sha256"] == written_index["remote_index_digest_sha256"]
    assert preview["publication_manifest"]["publication_mode"] == "manual_static_host"
    assert preview["publication_manifest"]["network_publish_allowed"] is False
    assert preview["payment_mutation_allowed"] is False
    assert preview["license_checkout_allowed"] is False
    assert preview["package_install_allowed"] is False
    assert preview["authority"]["writes_marketplace_hosted_bundle_artifact"] is False

    wrong = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_hosted_bundle_digest="wrong",
        write_bundle=True,
        publisher_id="local-operator",
    )
    assert wrong["ok"] is False
    assert wrong["hosted_bundle_artifact_written"] is False
    assert "expected_hosted_bundle_digest_required_or_mismatched" in wrong["blockers"]

    written = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=preview["hosted_bundle_digest_sha256"],
        write_bundle=True,
        publisher_id="local-operator",
        static_base_url="https://example.invalid/chaser-forge",
    )
    artifact_path = tmp_path / written["hosted_bundle_artifact_path"]
    assert written["ok"] is True
    assert written["hosted_bundle_artifact_written"] is True
    assert written["authority"]["writes_marketplace_hosted_bundle_artifact"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["hosted_bundle_digest_sha256"] == preview["hosted_bundle_digest_sha256"]
    assert payload["remote_network_publish_allowed"] is False
    assert payload["payment_mutation_allowed"] is False
    assert payload["license_checkout_allowed"] is False
    assert payload["publication_manifest"]["credentials_included"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_static_host_publication_writes_upload_ready_files_without_network_or_payment(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    distribution_preview = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    written_index = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=distribution_preview["remote_index_digest_sha256"],
    )
    hosted_preview = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        publisher_id="local-operator",
    )
    hosted_written = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_preview["hosted_bundle_digest_sha256"],
        publisher_id="local-operator",
        write_bundle=True,
    )

    preview = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
    )

    assert preview["ok"] is True
    assert preview["status"] == "forge_marketplace_static_host_publication_ready"
    assert preview["static_publication_written"] is False
    assert preview["publication_manifest"]["record_type"] == FORGE_MARKETPLACE_STATIC_PUBLICATION_RECORD_TYPE
    assert preview["publication_manifest"]["schema_version"] == FORGE_MARKETPLACE_STATIC_PUBLICATION_SCHEMA_VERSION
    assert preview["publication_manifest"]["static_publication_digest_sha256"] == preview["static_publication_digest_sha256"]
    assert preview["manual_upload_ready"] is True
    assert preview["network_upload_performed"] is False
    assert preview["remote_network_publish_allowed"] is False
    assert preview["external_registry_mutation_allowed"] is False
    assert preview["payment_mutation_allowed"] is False
    assert preview["license_checkout_allowed"] is False
    assert preview["package_install_allowed"] is False

    wrong = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest="wrong",
        write_publication=True,
    )
    assert wrong["ok"] is False
    assert wrong["static_publication_written"] is False
    assert "expected_static_publication_digest_required_or_mismatched" in wrong["blockers"]

    written = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=preview["static_publication_digest_sha256"],
        write_publication=True,
    )
    publication_dir = tmp_path / written["static_publication_dir_path"]
    assert written["ok"] is True
    assert written["static_publication_written"] is True
    assert written["authority"]["writes_marketplace_static_host_publication_artifacts"] is True
    assert publication_dir.is_dir()
    assert sorted(path.name for path in publication_dir.iterdir()) == [
        "README.md",
        "checksums.json",
        "hosted-bundle.json",
        "index.json",
        "publication-manifest.json",
    ]
    manifest_payload = json.loads((publication_dir / "publication-manifest.json").read_text(encoding="utf-8"))
    assert manifest_payload["static_publication_digest_sha256"] == preview["static_publication_digest_sha256"]
    assert manifest_payload["network_upload_performed"] is False
    assert manifest_payload["external_registry_mutation_allowed"] is False
    assert manifest_payload["payment_mutation_allowed"] is False
    assert manifest_payload["license_checkout_allowed"] is False
    assert manifest_payload["package_install_allowed"] is False


def test_marketplace_static_host_upload_handoff_writes_operator_handoff_without_network(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    distribution_preview = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    written_index = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=distribution_preview["remote_index_digest_sha256"],
    )
    hosted_preview = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        publisher_id="local-operator",
    )
    hosted_written = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_preview["hosted_bundle_digest_sha256"],
        publisher_id="local-operator",
        write_bundle=True,
    )
    publication_preview = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
    )
    publication_written = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_preview["static_publication_digest_sha256"],
        write_publication=True,
    )

    preview = build_forge_marketplace_static_host_upload_handoff(
        tmp_path,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
    )

    assert preview["ok"] is True, preview
    assert preview["status"] == "forge_marketplace_static_host_upload_handoff_ready"
    assert preview["static_publication_files_present"] is True
    assert preview["handoff_payload"]["record_type"] == FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_RECORD_TYPE
    assert preview["handoff_payload"]["schema_version"] == FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SCHEMA_VERSION

    wrong = build_forge_marketplace_static_host_upload_handoff(
        tmp_path,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest="wrong",
        write_handoff=True,
    )
    assert wrong["ok"] is False
    assert "expected_upload_handoff_digest_required_or_mismatched" in wrong["blockers"]

    written = build_forge_marketplace_static_host_upload_handoff(
        tmp_path,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=preview["upload_handoff_digest_sha256"],
        write_handoff=True,
    )

    assert written["ok"] is True, written
    assert written["status"] == "forge_marketplace_static_host_upload_handoff_written"
    assert written["upload_handoff_written"] is True
    assert (tmp_path / written["upload_handoff_json_path"]).is_file()
    assert (tmp_path / written["upload_handoff_markdown_path"]).is_file()
    assert written["network_upload_performed"] is False
    assert written["network_upload_allowed"] is False
    assert written["external_registry_mutation_allowed"] is False
    assert written["payment_mutation_allowed"] is False
    assert written["license_checkout_allowed"] is False
    assert written["package_install_allowed"] is False
    assert written["authority"]["writes_marketplace_static_upload_handoff_artifacts"] is True


def test_marketplace_static_host_upload_receipt_writes_operator_receipt_without_network_fetch(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    distribution_preview = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    written_index = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=distribution_preview["remote_index_digest_sha256"],
    )
    hosted_preview = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        publisher_id="local-operator",
    )
    hosted_written = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_preview["hosted_bundle_digest_sha256"],
        publisher_id="local-operator",
        write_bundle=True,
    )
    publication_preview = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
    )
    publication_written = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_preview["static_publication_digest_sha256"],
        write_publication=True,
    )
    handoff_preview = build_forge_marketplace_static_host_upload_handoff(
        tmp_path,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
    )
    handoff_written = build_forge_marketplace_static_host_upload_handoff(
        tmp_path,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_preview["upload_handoff_digest_sha256"],
        write_handoff=True,
    )

    preview = build_forge_marketplace_static_host_upload_receipt(
        tmp_path,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        operator_uploaded_base_url="https://example.invalid/chaser-forge",
    )

    assert preview["ok"] is True, preview
    assert preview["status"] == "forge_marketplace_static_host_upload_receipt_ready"
    assert preview["upload_receipt_written"] is False
    assert preview["receipt_payload"]["record_type"] == FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_RECORD_TYPE
    assert preview["receipt_payload"]["schema_version"] == FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SCHEMA_VERSION
    assert preview["manual_upload_receipt_ready"] is True
    assert preview["network_fetch_performed"] is False
    assert preview["network_fetch_allowed"] is False

    wrong_receipt = build_forge_marketplace_static_host_upload_receipt(
        tmp_path,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest="wrong",
        operator_uploaded_base_url="https://example.invalid/chaser-forge",
        operator_receipt_statement=preview["required_operator_receipt_statement"],
        write_receipt=True,
    )
    assert wrong_receipt["ok"] is False
    assert "expected_upload_receipt_digest_required_or_mismatched" in wrong_receipt["blockers"]

    wrong_statement = build_forge_marketplace_static_host_upload_receipt(
        tmp_path,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=preview["upload_receipt_digest_sha256"],
        operator_uploaded_base_url="https://example.invalid/chaser-forge",
        operator_receipt_statement="wrong",
        write_receipt=True,
    )
    assert wrong_statement["ok"] is False
    assert "operator_receipt_statement_required_or_mismatched" in wrong_statement["blockers"]

    written = build_forge_marketplace_static_host_upload_receipt(
        tmp_path,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=preview["upload_receipt_digest_sha256"],
        operator_uploaded_base_url="https://example.invalid/chaser-forge",
        operator_receipt_statement=preview["required_operator_receipt_statement"],
        write_receipt=True,
    )

    assert written["ok"] is True, written
    assert written["status"] == "forge_marketplace_static_host_upload_receipt_written"
    assert written["upload_receipt_written"] is True
    assert (tmp_path / written["upload_receipt_json_path"]).is_file()
    assert (tmp_path / written["upload_receipt_markdown_path"]).is_file()
    payload = json.loads((tmp_path / written["upload_receipt_json_path"]).read_text(encoding="utf-8"))
    assert payload["operator_receipt_statement"] == preview["required_operator_receipt_statement"]
    assert written["operator_manual_upload_claim_recorded"] is True
    assert written["hosted_upload_verified_by_network_fetch"] is False
    assert written["network_fetch_performed"] is False
    assert written["network_fetch_allowed"] is False
    assert written["network_upload_allowed"] is False
    assert written["external_registry_mutation_allowed"] is False
    assert written["payment_mutation_allowed"] is False
    assert written["license_checkout_allowed"] is False
    assert written["package_install_allowed"] is False
    assert written["authority"]["writes_marketplace_static_upload_receipt_artifacts"] is True


def test_marketplace_published_static_index_registration_writes_local_record_without_live_fetch(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    distribution_preview = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    written_index = build_forge_marketplace_remote_distribution(
        tmp_path,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=distribution_preview["remote_index_digest_sha256"],
    )
    hosted_preview = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        publisher_id="local-operator",
    )
    hosted_written = build_forge_marketplace_hosted_export_bundle(
        tmp_path,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_preview["hosted_bundle_digest_sha256"],
        publisher_id="local-operator",
        write_bundle=True,
    )
    publication_preview = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
    )
    publication_written = build_forge_marketplace_static_host_publication(
        tmp_path,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_preview["static_publication_digest_sha256"],
        write_publication=True,
    )
    handoff_preview = build_forge_marketplace_static_host_upload_handoff(
        tmp_path,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
    )
    handoff_written = build_forge_marketplace_static_host_upload_handoff(
        tmp_path,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_preview["upload_handoff_digest_sha256"],
        write_handoff=True,
    )
    receipt_preview = build_forge_marketplace_static_host_upload_receipt(
        tmp_path,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        operator_uploaded_base_url="https://example.invalid/chaser-forge",
    )
    receipt_written = build_forge_marketplace_static_host_upload_receipt(
        tmp_path,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_preview["upload_receipt_digest_sha256"],
        operator_uploaded_base_url="https://example.invalid/chaser-forge",
        operator_receipt_statement=receipt_preview["required_operator_receipt_statement"],
        write_receipt=True,
    )

    preview = build_forge_marketplace_published_static_index_registration(
        tmp_path,
        upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
        expected_remote_index_digest=receipt_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=receipt_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=receipt_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=receipt_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_written["upload_receipt_digest_sha256"],
        operator_published_static_index_url="https://example.invalid/chaser-forge/index.json",
    )

    assert preview["ok"] is True, preview
    assert preview["status"] == "forge_marketplace_published_static_index_registration_ready"
    assert preview["published_static_index_registration_written"] is False
    assert preview["registration_payload"]["record_type"] == FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_RECORD_TYPE
    assert preview["registration_payload"]["schema_version"] == FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SCHEMA_VERSION
    assert preview["published_static_index_registration_ready"] is True
    assert preview["live_url_verified"] is False
    assert preview["network_fetch_allowed"] is False

    wrong_url = build_forge_marketplace_published_static_index_registration(
        tmp_path,
        upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
        operator_published_static_index_url="http://example.invalid/chaser-forge/index.json",
    )
    assert wrong_url["ok"] is False
    assert "published_static_index_url_must_use_https" in wrong_url["blockers"]

    wrong_digest = build_forge_marketplace_published_static_index_registration(
        tmp_path,
        upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
        expected_remote_index_digest=receipt_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=receipt_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=receipt_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=receipt_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_written["upload_receipt_digest_sha256"],
        expected_published_static_index_registration_digest="wrong",
        operator_published_static_index_url="https://example.invalid/chaser-forge/index.json",
        operator_registration_statement=preview["required_operator_registration_statement"],
        write_registration=True,
    )
    assert wrong_digest["ok"] is False
    assert "expected_published_static_index_registration_digest_required_or_mismatched" in wrong_digest["blockers"]

    wrong_statement = build_forge_marketplace_published_static_index_registration(
        tmp_path,
        upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
        expected_remote_index_digest=receipt_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=receipt_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=receipt_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=receipt_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_written["upload_receipt_digest_sha256"],
        expected_published_static_index_registration_digest=preview[
            "published_static_index_registration_digest_sha256"
        ],
        operator_published_static_index_url="https://example.invalid/chaser-forge/index.json",
        operator_registration_statement="wrong",
        write_registration=True,
    )
    assert wrong_statement["ok"] is False
    assert "operator_registration_statement_required_or_mismatched" in wrong_statement["blockers"]

    written = build_forge_marketplace_published_static_index_registration(
        tmp_path,
        upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
        expected_remote_index_digest=receipt_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=receipt_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=receipt_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=receipt_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_written["upload_receipt_digest_sha256"],
        expected_published_static_index_registration_digest=preview[
            "published_static_index_registration_digest_sha256"
        ],
        operator_published_static_index_url="https://example.invalid/chaser-forge/index.json",
        operator_registration_statement=preview["required_operator_registration_statement"],
        write_registration=True,
    )

    assert written["ok"] is True, written
    assert written["status"] == "forge_marketplace_published_static_index_registration_written"
    assert written["published_static_index_registration_written"] is True
    assert (tmp_path / written["published_static_index_registration_json_path"]).is_file()
    assert (tmp_path / written["published_static_index_registration_markdown_path"]).is_file()
    payload = json.loads((tmp_path / written["published_static_index_registration_json_path"]).read_text(encoding="utf-8"))
    assert payload["operator_registration_statement"] == preview["required_operator_registration_statement"]
    assert written["operator_declared_published_index_registered"] is True
    assert written["live_url_verified"] is False
    assert written["network_fetch_performed"] is False
    assert written["network_fetch_allowed"] is False
    assert written["network_upload_allowed"] is False
    assert written["external_registry_mutation_allowed"] is False
    assert written["payment_mutation_allowed"] is False
    assert written["license_checkout_allowed"] is False
    assert written["package_install_allowed"] is False
    assert written["authority"]["writes_marketplace_published_static_index_registration_artifacts"] is True


def test_marketplace_live_index_input_readiness_reports_domain_deferred_placeholders(tmp_path: Path) -> None:
    publication_dir, index_sha256 = _write_live_index_static_publication_fixture(tmp_path)
    packet_path = tmp_path / "packet-template.json"
    packet_path.write_text(
        json.dumps(
            {
                "packet_type": "chaser_forge_live_index_json_verification_input",
                "schema_version": "chaser_forge.live_index_json_input.v1",
                "public_index_url": "https://<real-host>/<path>/index.json",
                "hosted_base_url": "https://<real-host>/<path>",
                "host_label": "<static host or domain label>",
                "local_static_publication_dir": (
                    "07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Publications/<directory-name>"
                ),
                "local_index_sha256": "<sha256 of local index.json>",
                "uploaded_files": [
                    "index.json",
                    "README.md",
                    "hosted-bundle.json",
                    "publication-manifest.json",
                    "checksums.json",
                ],
                "operator_upload_confirmation": (
                    "I confirm I uploaded the five Chaser Forge static publication files from the listed "
                    "local_static_publication_dir to hosted_base_url without modification."
                ),
                "operator_fetch_approval_statement": (
                    "I approve Codex to fetch https://<real-host>/<path>/index.json once for Chaser Forge "
                    "live index verification, compare it against local_index_sha256=<sha256>, and write local "
                    "JSON/Markdown verification evidence only. I do not approve upload, external registry "
                    "mutation, package install, payment/license mutation, credential use, provider/model calls, "
                    "Agent Bus dispatch, or protected-core mutation."
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    handover_path = tmp_path / "handover.md"
    handover_path.write_text(
        "## Timeline: Implementation Blocked on Domain Purchase\n"
        "This task will be completed once the official ChaseOS domain is purchased.\n",
        encoding="utf-8",
    )

    readiness = build_forge_marketplace_live_index_input_readiness(
        tmp_path,
        input_packet_path=packet_path,
        handover_path=handover_path,
    )

    assert readiness["ok"] is True
    assert readiness["surface"] == FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID
    assert readiness["status"] == "blocked_forge_marketplace_live_index_input_domain_deferred"
    assert readiness["ready_for_live_verification"] is False
    assert readiness["domain_purchase_deferred"] is True
    assert "domain_purchase_deferred_until_official_domain_is_purchased" in readiness["blockers"]
    assert "public_index_url_required" in readiness["blockers"]
    assert "local_index_sha256_required" in readiness["blockers"]
    assert readiness["local_static_publication_candidate_present"] is True
    assert readiness["local_static_publication"]["path"] == publication_dir.relative_to(tmp_path).as_posix()
    assert readiness["candidate_local_index_sha256"] == index_sha256
    assert readiness["network_fetch_performed"] is False
    assert readiness["network_fetch_allowed"] is False
    assert readiness["external_registry_mutation_allowed"] is False


def test_marketplace_live_index_input_readiness_accepts_complete_packet_without_fetch(tmp_path: Path) -> None:
    publication_dir, index_sha256 = _write_live_index_static_publication_fixture(tmp_path)
    public_index_url = "https://chaseosproject.com/marketplace/index.json"
    packet_path = _write_live_index_packet(
        tmp_path,
        public_index_url=public_index_url,
        hosted_base_url="https://chaseosproject.com/marketplace",
        host_label="ChaseOS project domain",
        local_static_publication_dir=publication_dir.relative_to(tmp_path).as_posix(),
        local_index_sha256=index_sha256,
    )
    handover_path = tmp_path / "handover.md"
    handover_path.write_text("Live input handover without a domain deferral marker.\n", encoding="utf-8")

    readiness = build_forge_marketplace_live_index_input_readiness(
        tmp_path,
        input_packet_path=packet_path,
        handover_path=handover_path,
    )

    assert readiness["ok"] is True
    assert readiness["status"] == "forge_marketplace_live_index_input_ready"
    assert readiness["ready_for_live_verification"] is True
    assert readiness["domain_purchase_deferred"] is False
    assert readiness["public_index_url"] == public_index_url
    assert readiness["local_index_sha256_matches_candidate"] is True
    assert readiness["blockers"] == []
    assert readiness["network_fetch_performed"] is False
    assert readiness["network_fetch_allowed"] is False
    assert readiness["package_install_allowed"] is False


def test_marketplace_live_index_input_readiness_rejects_generic_trusted_homepage(tmp_path: Path) -> None:
    publication_dir, index_sha256 = _write_live_index_static_publication_fixture(tmp_path)
    packet_path = _write_live_index_packet(
        tmp_path,
        public_index_url="https://www.ebay.co.uk/",
        hosted_base_url="https://www.ebay.co.uk",
        host_label="generic trusted homepage",
        local_static_publication_dir=publication_dir.relative_to(tmp_path).as_posix(),
        local_index_sha256=index_sha256,
    )
    handover_path = tmp_path / "handover.md"
    handover_path.write_text("Live input handover without domain deferral.\n", encoding="utf-8")

    readiness = build_forge_marketplace_live_index_input_readiness(
        tmp_path,
        input_packet_path=packet_path,
        handover_path=handover_path,
    )

    assert readiness["ok"] is True
    assert readiness["ready_for_live_verification"] is False
    assert "published_static_index_url_must_end_with_index_json" in readiness["blockers"]
    assert readiness["network_fetch_performed"] is False
    assert readiness["network_fetch_allowed"] is False


def test_marketplace_live_index_input_prefill_writes_local_packet_without_fetch(tmp_path: Path) -> None:
    publication_dir, index_sha256 = _write_live_index_static_publication_fixture(tmp_path)
    static_preview = {
        "ok": True,
        "status": "fixture_static_publication_ready",
        "static_publication_dir_path": publication_dir.relative_to(tmp_path).as_posix(),
        "static_publication_digest_sha256": "fixture-static-publication",
        "remote_index_digest_sha256": "fixture-remote-index",
        "hosted_bundle_digest_sha256": "fixture-hosted-bundle",
        "files": [{"path": "index.json", "digest_sha256": index_sha256}],
        "blockers": [],
    }

    preview = build_forge_marketplace_live_index_input_prefill(
        tmp_path,
        static_publication_preview=static_preview,
    )

    assert preview["ok"] is True, preview
    assert preview["surface"] == FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID
    assert preview["status"] == "forge_marketplace_live_index_input_prefill_ready"
    assert preview["prefill_written"] is False
    assert preview["packet_payload"]["local_static_publication_dir"] == publication_dir.relative_to(tmp_path).as_posix()
    assert preview["packet_payload"]["local_index_sha256"] == index_sha256
    assert preview["packet_payload"]["public_index_url"] == "https://<official-chaseos-domain>/chaser-forge/index.json"
    assert preview["domain_purchase_deferred"] is True
    assert preview["ready_for_live_verification"] is False
    assert preview["network_fetch_performed"] is False
    assert preview["network_fetch_allowed"] is False
    assert preview["external_registry_mutation_allowed"] is False

    wrong = build_forge_marketplace_live_index_input_prefill(
        tmp_path,
        static_publication_preview=static_preview,
        write_prefill=True,
        expected_prefill_digest="wrong",
    )
    assert wrong["ok"] is False
    assert wrong["prefill_written"] is False
    assert "expected_prefill_digest_required_or_mismatched" in wrong["blockers"]

    written = build_forge_marketplace_live_index_input_prefill(
        tmp_path,
        static_publication_preview=static_preview,
        write_prefill=True,
        expected_prefill_digest=preview["prefill_digest_sha256"],
    )

    assert written["ok"] is True, written
    assert written["status"] == "forge_marketplace_live_index_input_prefill_written"
    assert written["prefill_written"] is True
    assert (tmp_path / written["prefilled_input_packet_json_path"]).is_file()
    assert (tmp_path / written["prefill_markdown_path"]).is_file()
    packet = json.loads((tmp_path / written["prefilled_input_packet_json_path"]).read_text(encoding="utf-8"))
    assert packet["local_index_sha256"] == index_sha256
    assert packet["local_static_publication_dir"] == publication_dir.relative_to(tmp_path).as_posix()
    assert "official-chaseos-domain" in packet["public_index_url"]
    assert written["authority"]["writes_marketplace_live_index_input_prefill_artifacts"] is True
    assert written["network_upload_allowed"] is False
    assert written["network_fetch_allowed"] is False
    assert written["package_install_allowed"] is False


def test_marketplace_import_sandbox_approval_requires_exact_request_digest(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    approval_preview = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_preview["package_payload"],
    )

    assert approval_preview["ok"] is True
    assert approval_preview["status"] == "forge_marketplace_import_sandbox_approval_request_ready"
    assert approval_preview["approval_request_written"] is False
    assert approval_preview["package_install_allowed"] is False
    assert approval_preview["registry_written"] is False
    assert approval_preview["extension_files_written"] == []
    assert not (tmp_path / approval_preview["approval_artifact_path"]).exists()

    wrong = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_approval_request=True,
        request_digest="wrong",
    )
    assert wrong["ok"] is False
    assert wrong["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in wrong["blockers"]
    assert not (tmp_path / wrong["approval_artifact_path"]).exists()

    written = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_approval_request=True,
        request_digest=approval_preview["request_digest_sha256"],
    )
    artifact_path = tmp_path / written["approval_artifact_path"]
    assert written["ok"] is True
    assert written["approval_request_written"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["record_type"] == FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE
    assert payload["approval_scope"] == FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE
    assert payload["status"] == "pending_operator_decision"
    assert payload["operator_decision"] == "pending"
    assert payload["package_install_allowed_in_this_pass"] is False
    assert payload["registry_write_allowed_in_this_pass"] is False
    assert payload["extension_file_write_allowed_in_this_pass"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_import_sandbox_approval_blocks_tampered_package(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    package_payload = deepcopy(package_preview["package_payload"])
    package_payload["manifest"]["name"] = "Tampered UGC Campaign Studio"

    approval = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_payload,
        write_approval_request=True,
        request_digest="anything",
    )

    assert approval["ok"] is False
    assert approval["approval_request_written"] is False
    assert "package_digest_mismatch" in approval["blockers"]
    assert "manifest_digest_mismatch" in approval["blockers"]
    assert approval["package_install_allowed"] is False
    assert approval["registry_written"] is False
    assert approval["extension_files_written"] == []


def test_marketplace_import_sandbox_approval_supports_source_specific_decision_without_execution(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    approval_preview = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_preview["package_payload"],
    )
    written = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_approval_request=True,
        request_digest=approval_preview["request_digest_sha256"],
    )
    artifact_path = tmp_path / written["approval_artifact_path"]
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=written["approval_artifact_path"],
        decision="approved",
        expected_request_digest=written["request_digest_sha256"],
        operator_statement=payload["operator_confirmation_text"],
        write_decision=True,
        reviewer_id="operator",
    )

    assert handoff["ok"] is True
    assert handoff["family"] == "marketplace-import"
    approved_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approved_payload["status"] == "approved"
    assert approved_payload["operator_decision"] == "approved"
    assert approved_payload["approval_consumed"] is False
    assert approved_payload["approval_decision_family"] == "marketplace-import"
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_import_sandbox_request_requires_approved_review_and_exact_digest(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    approval_preview = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_preview["package_payload"],
    )
    pending = build_forge_marketplace_import_sandbox_approval(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_approval_request=True,
        request_digest=approval_preview["request_digest_sha256"],
    )
    blocked = build_forge_marketplace_import_sandbox_request(
        tmp_path,
        import_approval_artifact_path=pending["approval_artifact_path"],
        expected_import_request_digest=pending["request_digest_sha256"],
    )

    assert blocked["ok"] is False
    assert blocked["sandbox_approval_request_written"] is False
    assert "marketplace_import_approval_status_not_approved" in blocked["blockers"]
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()

    approved_vault = tmp_path / "approved"
    approved, artifact_path = _write_approved_marketplace_import(approved_vault)
    preview = build_forge_marketplace_import_sandbox_request(
        approved_vault,
        import_approval_artifact_path=approved["approval_artifact_path"],
        expected_import_request_digest=approved["request_digest_sha256"],
    )

    assert preview["ok"] is True
    assert preview["status"] == "forge_marketplace_import_sandbox_request_ready"
    assert preview["sandbox_approval_request"]["ok"] is True
    assert preview["sandbox_approval_request_written"] is False
    assert preview["marketplace_import_approval_consumed"] is False
    assert preview["registry_written"] is False
    assert preview["extension_files_written"] == []
    assert preview["exact_once_marker_reserved"] is False

    wrong = build_forge_marketplace_import_sandbox_request(
        approved_vault,
        import_approval_artifact_path=approved["approval_artifact_path"],
        expected_import_request_digest=approved["request_digest_sha256"],
        write_sandbox_request=True,
        request_digest="wrong",
    )
    assert wrong["ok"] is False
    assert wrong["sandbox_approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in wrong["blockers"]

    written = build_forge_marketplace_import_sandbox_request(
        approved_vault,
        import_approval_artifact_path=approved["approval_artifact_path"],
        expected_import_request_digest=approved["request_digest_sha256"],
        write_sandbox_request=True,
        request_digest=preview["request_digest_sha256"],
    )
    sandbox_artifact_path = approved_vault / str(written["sandbox_approval_artifact_path"])
    sandbox_payload = json.loads(sandbox_artifact_path.read_text(encoding="utf-8"))
    refreshed_import_payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert written["ok"] is True
    assert written["sandbox_approval_request_written"] is True
    assert sandbox_artifact_path.is_file()
    assert sandbox_payload["record_type"] == SANDBOX_APPROVAL_RECORD_TYPE
    assert sandbox_payload["approval_scope"] == SANDBOX_APPROVAL_SCOPE
    assert sandbox_payload["status"] == "pending_operator_decision"
    assert sandbox_payload["approval_consumed"] is False
    assert refreshed_import_payload["status"] == "approved"
    assert refreshed_import_payload["approval_consumed"] is False
    assert written["marketplace_import_approval_consumed"] is False
    assert written["registry_written"] is False
    assert written["extension_files_written"] == []
    assert written["exact_once_marker_reserved"] is False
    assert not (approved_vault / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (approved_vault / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_import_sandbox_request_blocks_tampered_decision_sidecar(tmp_path: Path) -> None:
    approved, artifact_path = _write_approved_marketplace_import(tmp_path)
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    decision_path = tmp_path / payload["decision_artifact_path"]
    sidecar = json.loads(decision_path.read_text(encoding="utf-8"))
    sidecar["operator_decision"] = "rejected"
    decision_path.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    blocked = build_forge_marketplace_import_sandbox_request(
        tmp_path,
        import_approval_artifact_path=approved["approval_artifact_path"],
        expected_import_request_digest=approved["request_digest_sha256"],
        write_sandbox_request=True,
        request_digest="anything",
    )

    assert blocked["ok"] is False
    assert blocked["sandbox_approval_request_written"] is False
    assert "approval_decision_digest_mismatch" in blocked["blockers"]
    assert "approval_decision_not_approved" in blocked["blockers"]
    assert blocked["registry_written"] is False
    assert blocked["extension_files_written"] == []
    assert blocked["exact_once_marker_reserved"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_marketplace_install_execution_consumes_approved_catalog_import_and_sandbox_approval(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    publish_preview = build_forge_marketplace_publish(tmp_path, package_payload=package_preview["package_payload"])
    published = build_forge_marketplace_publish(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_listing=True,
        expected_listing_digest=publish_preview["listing_digest_sha256"],
    )
    assert published["ok"] is True

    approved_import, import_artifact_path = _write_approved_marketplace_import(tmp_path)
    bridge_preview = build_forge_marketplace_import_sandbox_request(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
    )
    bridge_written = build_forge_marketplace_import_sandbox_request(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
        write_sandbox_request=True,
        request_digest=bridge_preview["request_digest_sha256"],
    )
    sandbox_artifact_path = tmp_path / bridge_written["sandbox_approval_artifact_path"]
    sandbox_payload = json.loads(sandbox_artifact_path.read_text(encoding="utf-8"))
    sandbox_decision = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=bridge_written["sandbox_approval_artifact_path"],
        decision="approved",
        expected_request_digest=bridge_written["sandbox_request_digest_sha256"],
        operator_statement=sandbox_payload["operator_confirmation_text"],
        write_decision=True,
        reviewer_id="operator",
    )
    assert sandbox_decision["ok"] is True

    ready = build_forge_marketplace_install_execution(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
        expected_listing_digest=published["listing_digest_sha256"],
        listing_id=published["listing_id"],
        bridge_request_digest=bridge_written["request_digest_sha256"],
        sandbox_approval_artifact_path=bridge_written["sandbox_approval_artifact_path"],
        sandbox_request_digest=bridge_written["sandbox_request_digest_sha256"],
        execute=False,
    )
    assert ready["ok"] is True, ready["blockers"]
    assert ready["status"] == "forge_marketplace_install_execution_ready"
    assert ready["marketplace_install_executed"] is False
    assert ready["registry_written"] is False
    assert ready["marketplace_import_approval_consumed"] is False

    executed = build_forge_marketplace_install_execution(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
        expected_listing_digest=published["listing_digest_sha256"],
        listing_id=published["listing_id"],
        bridge_request_digest=bridge_written["request_digest_sha256"],
        sandbox_approval_artifact_path=bridge_written["sandbox_approval_artifact_path"],
        sandbox_request_digest=bridge_written["sandbox_request_digest_sha256"],
        execute=True,
    )
    assert executed["ok"] is True
    assert executed["status"] == "forge_marketplace_install_executed"
    assert executed["marketplace_install_executed"] is True
    assert executed["registry_written"] is True
    assert executed["extension_files_written"]
    assert executed["exact_once_marker_reserved"] is True
    assert executed["sandbox_approval_consumed"] is True
    assert executed["marketplace_import_approval_consumed"] is True
    assert (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").is_file()
    assert (tmp_path / "extensions" / "ugc-campaign-studio").is_dir()
    refreshed_import = json.loads(import_artifact_path.read_text(encoding="utf-8"))
    assert refreshed_import["status"] == "consumed"
    assert refreshed_import["approval_consumed"] is True

    duplicate = build_forge_marketplace_install_execution(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
        expected_listing_digest=published["listing_digest_sha256"],
        listing_id=published["listing_id"],
        bridge_request_digest=bridge_written["request_digest_sha256"],
        sandbox_approval_artifact_path=bridge_written["sandbox_approval_artifact_path"],
        sandbox_request_digest=bridge_written["sandbox_request_digest_sha256"],
        execute=True,
    )
    assert duplicate["ok"] is False
    assert "marketplace_import_approval_already_consumed" in duplicate["blockers"]


def test_marketplace_local_library_joins_catalog_and_installed_registry(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    package_preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    publish_preview = build_forge_marketplace_publish(tmp_path, package_payload=package_preview["package_payload"])
    published = build_forge_marketplace_publish(
        tmp_path,
        package_payload=package_preview["package_payload"],
        write_listing=True,
        expected_listing_digest=publish_preview["listing_digest_sha256"],
    )

    before_install = build_forge_marketplace_local_library(tmp_path)
    assert before_install["ok"] is True
    assert before_install["status"] == "forge_marketplace_local_library_ready"
    assert before_install["local_catalog_entry_count"] == 1
    assert before_install["listed_not_installed_count"] == 1
    assert before_install["listed_installed_count"] == 0
    assert before_install["items"][0]["installed"] is False
    assert before_install["remote_marketplace_call_allowed"] is False
    assert before_install["authority"]["local_marketplace_library_read_only"] is True
    assert before_install["authority"]["writes_extension_registry"] is False
    assert before_install["authority"]["writes_extension_files"] is False

    approved_import, _import_artifact_path = _write_approved_marketplace_import(tmp_path)
    bridge_preview = build_forge_marketplace_import_sandbox_request(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
    )
    bridge_written = build_forge_marketplace_import_sandbox_request(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
        write_sandbox_request=True,
        request_digest=bridge_preview["request_digest_sha256"],
    )
    sandbox_artifact_path = tmp_path / bridge_written["sandbox_approval_artifact_path"]
    sandbox_payload = json.loads(sandbox_artifact_path.read_text(encoding="utf-8"))
    sandbox_decision = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=bridge_written["sandbox_approval_artifact_path"],
        decision="approved",
        expected_request_digest=bridge_written["sandbox_request_digest_sha256"],
        operator_statement=sandbox_payload["operator_confirmation_text"],
        write_decision=True,
        reviewer_id="operator",
    )
    assert sandbox_decision["ok"] is True

    executed = build_forge_marketplace_install_execution(
        tmp_path,
        import_approval_artifact_path=approved_import["approval_artifact_path"],
        expected_import_request_digest=approved_import["request_digest_sha256"],
        expected_listing_digest=published["listing_digest_sha256"],
        listing_id=published["listing_id"],
        bridge_request_digest=bridge_written["request_digest_sha256"],
        sandbox_approval_artifact_path=bridge_written["sandbox_approval_artifact_path"],
        sandbox_request_digest=bridge_written["sandbox_request_digest_sha256"],
        execute=True,
    )
    assert executed["ok"] is True

    library = build_forge_marketplace_local_library(tmp_path)
    assert library["ok"] is True
    assert library["library_item_count"] == 1
    assert library["installed_extension_count"] == 1
    assert library["listed_installed_count"] == 1
    assert library["installed_unlisted_count"] == 0
    item = library["items"][0]
    assert item["installed"] is True
    assert item["listing_id"] == published["listing_id"]
    assert item["registry_status"] == "sandbox_installed"
    assert item["install_environment"] == "sandbox"
    assert item["target_path_count"] >= 1
    assert item["target_paths_existing_count"] == item["target_path_count"]
    assert item["remote_marketplace_call_allowed"] is False
    assert item["third_party_package_exchange_allowed"] is False


def test_marketplace_import_preview_blocks_tampered_package_digest(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    preview = build_forge_marketplace_export_package(tmp_path, manifest=manifest)
    package_payload = deepcopy(preview["package_payload"])
    package_payload["manifest"]["name"] = "Tampered UGC Campaign Studio"

    import_preview = build_forge_marketplace_import_preview(tmp_path, package_payload=package_payload)

    assert import_preview["ok"] is False
    assert "package_digest_mismatch" in import_preview["blockers"]
    assert "manifest_digest_mismatch" in import_preview["blockers"]
    assert import_preview["import_install_allowed"] is False
    assert import_preview["registry_written"] is False
    assert import_preview["extension_files_written"] == []


def test_marketplace_export_blocks_invalid_manifest_without_writes(tmp_path: Path) -> None:
    manifest = load_demo_manifest()
    manifest["permissions"] = list(manifest["permissions"]) + ["core.file.write"]

    preview = build_forge_marketplace_export_package(
        tmp_path,
        manifest=manifest,
        write_package=True,
        expected_package_digest="anything",
    )

    assert preview["ok"] is False
    assert preview["package_artifact_written"] is False
    assert "manifest_validation_failed" in preview["blockers"]
    assert preview["registry_written"] is False
    assert preview["extension_files_written"] == []
    assert not (tmp_path / preview["package_artifact_path"]).exists()
