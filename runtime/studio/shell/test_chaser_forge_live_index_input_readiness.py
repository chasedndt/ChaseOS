from __future__ import annotations

from pathlib import Path

from runtime.forge.marketplace import (
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID,
)
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


def test_chaser_forge_live_index_input_readiness_is_exposed_by_studio_api(tmp_path: Path) -> None:
    response = StudioAPI(tmp_path).get_chaser_forge_marketplace_live_index_input_readiness()

    assert response["ok"] is True
    data = response["data"]
    assert data["surface"] == FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID
    assert data["ok"] is True
    assert data["ready_for_live_verification"] is False
    assert data["network_fetch_performed"] is False
    assert data["network_fetch_allowed"] is False
    assert data["external_registry_mutation_allowed"] is False


def test_chaser_forge_live_index_input_prefill_is_exposed_by_studio_api(tmp_path: Path) -> None:
    response = StudioAPI(tmp_path).get_chaser_forge_marketplace_live_index_input_prefill()

    assert response["ok"] is True
    data = response["data"]
    assert data["surface"] == FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID
    assert data["ok"] is True
    assert data["domain_purchase_deferred"] is True
    assert data["ready_for_live_verification"] is False
    assert data["network_fetch_performed"] is False
    assert data["network_fetch_allowed"] is False
    assert data["external_registry_mutation_allowed"] is False


def test_chaser_forge_live_index_input_prefill_write_materializes_packet(tmp_path: Path) -> None:
    preview = StudioAPI(tmp_path).get_chaser_forge_marketplace_live_index_input_prefill()
    assert preview["ok"] is True
    digest = preview["data"]["prefill_digest_sha256"]

    response = StudioAPI(tmp_path).write_chaser_forge_marketplace_live_index_input_prefill(digest)

    assert response["ok"] is True, response
    data = response["data"]
    assert data["status"] == "forge_marketplace_live_index_input_prefill_written"
    assert data["prefill_written"] is True
    assert data["static_publication_materialized"] is True
    assert (tmp_path / data["prefilled_input_packet_json_path"]).is_file()
    assert (tmp_path / data["prefill_markdown_path"]).is_file()
    assert data["network_fetch_allowed"] is False
    assert data["network_upload_allowed"] is False


def test_chaser_forge_live_index_input_readiness_is_registered_for_studio_ui(tmp_path: Path) -> None:
    registry = build_native_shell_panel_registry(tmp_path)
    panels = {panel["id"]: panel for panel in registry["panels"]}
    chaser_forge = panels["chaser-forge"]

    assert "get_chaser_forge_marketplace_live_index_input_readiness" in chaser_forge["api_methods"]
    assert "get_chaser_forge_marketplace_live_index_input_prefill" in chaser_forge["api_methods"]
    assert "write_chaser_forge_marketplace_live_index_input_prefill" in chaser_forge["api_methods"]
    assert registry["readiness"]["chaser_forge_marketplace_live_index_input_prefill_built"] is True
    assert registry["readiness"]["chaser_forge_marketplace_live_index_input_prefill_ready"] is True
    assert (
        registry["readiness"]["chaser_forge_marketplace_live_index_input_readiness_built"]
        is True
    )
    assert (
        registry["readiness"]["chaser_forge_marketplace_live_index_input_network_fetch_blocked"]
        is True
    )


def test_chaser_forge_live_index_input_readiness_frontend_tokens_are_present() -> None:
    app_js = (Path(__file__).with_name("frontend") / "app.js").read_text(encoding="utf-8")

    assert "get_chaser_forge_marketplace_live_index_input_readiness" in app_js
    assert "get_chaser_forge_marketplace_live_index_input_prefill" in app_js
    assert "write_chaser_forge_marketplace_live_index_input_prefill" in app_js
    assert "chaser-forge-write-live-index-input-prefill" in app_js
    assert "Hosted Marketplace - Coming Soon" in app_js
    assert "Coming soon: official ChaseOS domain required" in app_js
    assert "chaser-forge-check-live-index-input" in app_js
    assert "marketplaceLiveIndexInputReadiness" in app_js
    assert "marketplaceLiveIndexInputPrefill" in app_js
