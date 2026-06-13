from __future__ import annotations

from pathlib import Path

from runtime.forge.panel import build_chaser_forge_panel


def test_chaser_forge_panel_exposes_operator_import_hardening_contract(tmp_path: Path) -> None:
    panel = build_chaser_forge_panel(tmp_path)

    hardening = panel["product_hardening"]

    assert hardening["purpose_statement"] == (
        "Choose a Forge extension, validate its manifest, review permissions and sandbox proof, "
        "then prepare the exact approval handoff before any install or rollback can run."
    )
    assert hardening["primary_operator_action"] == {
        "label": "Choose extension and preview install",
        "kind": "blocked-action-preview",
        "enabled": False,
        "blocked_reason": "No extension install runs until manifest validation, permission disclosure, sandbox proof, and source-specific operator approval are present.",
        "next_step": "Open the local library or package preview, copy the generated review packet, then record a source-specific approval before running an executor.",
    }
    assert [step["id"] for step in hardening["install_import_flow"]] == [
        "choose_extension",
        "validate_manifest",
        "disclose_permissions",
        "prove_sandbox",
        "handoff_approval",
        "rollback_readiness",
    ]
    assert [section["title"] for section in hardening["plain_english_sections"]] == [
        "What this page does",
        "What it produces",
        "What is blocked",
        "What to do next",
    ]
    assert hardening["empty_states"]["local_library"] == (
        "No local marketplace listings yet. Publish or import a package preview first; this page will not fetch remote listings by itself."
    )
    assert hardening["error_states"]["manifest_invalid"] == (
        "Manifest validation failed. Fix the listed schema, extension-point, permission, or protected-path issue before requesting approval."
    )
    assert hardening["authority_boundary"] == {
        "live_install_without_approval": False,
        "remote_marketplace_fetch": False,
        "external_registry_mutation": False,
        "payment_or_license_mutation": False,
        "provider_or_agent_bus_dispatch": False,
        "protected_core_write": False,
    }
