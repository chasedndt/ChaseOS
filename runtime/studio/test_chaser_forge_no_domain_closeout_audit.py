from __future__ import annotations

import hashlib
import json
from pathlib import Path

from runtime.forge.marketplace import FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES
from runtime.studio.chaser_forge_no_domain_closeout_audit import (
    HANDOVER_PATH,
    NEXT_RECOMMENDED_PASS,
    PREFILL_ROOT,
    SURFACE_ID,
    build_chaser_forge_no_domain_closeout_audit,
)
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


def _write_static_publication_fixture(vault: Path) -> tuple[str, str]:
    publication_dir = (
        vault
        / "07_LOGS"
        / "Workflow-Proofs"
        / "Forge-Marketplace-Static-Host-Publications"
        / "local-operator-static-test"
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
        "hosted-bundle.json": json.dumps(
            {"record_type": "forge_marketplace_hosted_export_bundle"},
            sort_keys=True,
        )
        + "\n",
        "publication-manifest.json": json.dumps(
            {"record_type": "forge_marketplace_static_host_publication"},
            sort_keys=True,
        )
        + "\n",
    }
    for name, text in files.items():
        (publication_dir / name).write_text(text, encoding="utf-8")
    checksums = {
        "record_type": "forge_marketplace_static_host_publication_checksums",
        "files": [
            {
                "path": name,
                "digest_sha256": hashlib.sha256(
                    (publication_dir / name).read_text(encoding="utf-8").encode("utf-8")
                ).hexdigest(),
            }
            for name in sorted(files)
        ],
    }
    (publication_dir / "checksums.json").write_text(
        json.dumps(checksums, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert sorted(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES) == sorted(
        path.name for path in publication_dir.iterdir()
    )
    index_sha256 = hashlib.sha256(
        (publication_dir / "index.json").read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    return publication_dir.relative_to(vault).as_posix(), index_sha256


def _seed_no_domain_fixture(vault: Path) -> Path:
    static_dir, index_sha256 = _write_static_publication_fixture(vault)
    prefill_dir = vault / PREFILL_ROOT
    prefill_dir.mkdir(parents=True, exist_ok=True)
    packet_path = prefill_dir / "live-index-input-prefill-test.json"
    packet = {
        "packet_type": "chaser_forge_live_index_json_verification_input",
        "schema_version": "chaser_forge.live_index_json_input.v1",
        "public_index_url": "https://<official-chaseos-domain>/chaser-forge/index.json",
        "hosted_base_url": "https://<official-chaseos-domain>/chaser-forge",
        "host_label": "official ChaseOS domain pending",
        "local_static_publication_dir": static_dir,
        "local_index_sha256": index_sha256,
        "uploaded_files": list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES),
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
        "notes": "Local prefill generated from a fixture static publication.",
    }
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    packet_path.with_suffix(".md").write_text(
        "# Chaser Forge Live index.json Input Packet Prefill\n",
        encoding="utf-8",
    )
    handover = vault / HANDOVER_PATH
    handover.parent.mkdir(parents=True, exist_ok=True)
    handover.write_text(
        "The live hosted fetch remains deferred until the official ChaseOS domain is purchased.\n"
        "Studio marks this as Hosted Marketplace - Coming Soon.\n"
        f"Packet: {packet_path.name}\n",
        encoding="utf-8",
    )
    return packet_path


def test_no_domain_closeout_audit_proves_ui_prefill_and_domain_deferral(tmp_path: Path) -> None:
    packet_path = _seed_no_domain_fixture(tmp_path)

    audit = build_chaser_forge_no_domain_closeout_audit(
        tmp_path,
        input_packet_path=packet_path.relative_to(tmp_path).as_posix(),
    )

    assert audit["surface"] == SURFACE_ID
    assert audit["summary"]["ui_wired_to_studio"] is True
    assert audit["summary"]["prefill_packet_ready"] is True, {
        "packet": audit["packet"],
        "static_publication": audit["static_publication"],
    }
    assert audit["ok"] is True, audit["code_owned_blockers"]
    assert audit["code_owned_blockers"] == []
    assert audit["summary"]["hosted_marketplace_coming_soon"] is True
    assert audit["summary"]["live_fetch_deferred"] is True
    assert audit["summary"]["code_owned_no_domain_work_remaining"] is False
    assert audit["summary"]["operator_owned_domain_work_remaining"] is True
    assert audit["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert "domain_purchase_deferred_until_official_domain_is_purchased" in audit[
        "operator_owned_domain_blockers"
    ]


def test_no_domain_closeout_audit_is_exposed_by_studio_api_and_registry(tmp_path: Path) -> None:
    _seed_no_domain_fixture(tmp_path)

    response = StudioAPI(tmp_path).get_chaser_forge_no_domain_closeout_audit()
    registry = build_native_shell_panel_registry(tmp_path)
    panel = {item["id"]: item for item in registry["panels"]}["chaser-forge"]

    assert response["ok"] is True, response
    assert response["data"]["ok"] is True, response["data"]["code_owned_blockers"]
    assert "get_chaser_forge_no_domain_closeout_audit" in panel["api_methods"]
    assert registry["readiness"]["chaser_forge_no_domain_closeout_audit_built"] is True
    assert (
        registry["readiness"][
            "chaser_forge_no_domain_closeout_audit_no_code_owned_domain_work_remaining"
        ]
        is True
    )
    assert (
        registry["readiness"]["chaser_forge_no_domain_closeout_audit_operator_domain_action_required"]
        is True
    )


def test_no_domain_closeout_audit_frontend_and_registry_checks_are_explicit(tmp_path: Path) -> None:
    packet_path = _seed_no_domain_fixture(tmp_path)

    audit = build_chaser_forge_no_domain_closeout_audit(
        tmp_path,
        input_packet_path=packet_path.relative_to(tmp_path).as_posix(),
    )
    checks = {item["id"]: item for item in audit["checks"]}

    for check_id in [
        "studio_panel_registered",
        "studio_frontend_target_wired",
        "studio_api_methods_wired",
        "frontend_source_tokens_present",
        "prefill_packet_materialized",
        "live_fetch_domain_deferred",
        "handover_records_deferred_domain",
        "hosted_marketplace_coming_soon",
    ]:
        assert checks[check_id]["satisfied"] is True, checks[check_id]

    assert audit["registry"]["frontend_target"] == "panel-chaser-forge"
    assert audit["registry"]["route_hint"] == "#/chaser-forge"
    assert audit["frontend"]["missing_app_tokens"] == []
    assert audit["frontend"]["missing_index_tokens"] == []
    assert audit["authority"]["network_fetch_allowed"] is False
    assert audit["authority"]["external_registry_mutation_allowed"] is False
