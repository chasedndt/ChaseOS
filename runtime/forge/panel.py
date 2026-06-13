"""Studio panel model for the Chaser Forge Extensions surface."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.forge.approval_decision import (
    FORGE_APPROVAL_DECISION_API_METHOD,
    FORGE_APPROVAL_DECISION_SURFACE_ID,
    SUPPORTED_DECISIONS,
)
from runtime.forge.approval_decision_form import (
    FORGE_APPROVAL_DECISION_FORM_API_METHOD,
    FORGE_APPROVAL_DECISION_FORM_SURFACE_ID,
)
from runtime.forge.extension_points import AUDIT_EVENTS, LIFECYCLE_MODEL, list_approved_extension_points
from runtime.forge.marketplace import (
    FORGE_MARKETPLACE_CATALOG_API_METHOD,
    FORGE_MARKETPLACE_CATALOG_SURFACE_ID,
    FORGE_MARKETPLACE_EXPORT_API_METHOD,
    FORGE_MARKETPLACE_HOSTED_BUNDLE_API_METHOD,
    FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID,
    FORGE_MARKETPLACE_HOSTED_BUNDLE_WRITE_API_METHOD,
    FORGE_MARKETPLACE_IMPORT_APPROVAL_API_METHOD,
    FORGE_MARKETPLACE_IMPORT_APPROVAL_SURFACE_ID,
    FORGE_MARKETPLACE_IMPORT_API_METHOD,
    FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_API_METHOD,
    FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_PREVIEW_API_METHOD,
    FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_SURFACE_ID,
    FORGE_MARKETPLACE_INSTALL_API_METHOD,
    FORGE_MARKETPLACE_INSTALL_SURFACE_ID,
    FORGE_MARKETPLACE_LOCAL_LIBRARY_API_METHOD,
    FORGE_MARKETPLACE_LOCAL_LIBRARY_SURFACE_ID,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_API_METHOD,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_WRITE_API_METHOD,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_API_METHOD,
    FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID,
    FORGE_MARKETPLACE_PUBLISH_API_METHOD,
    FORGE_MARKETPLACE_PUBLISH_PREVIEW_API_METHOD,
    FORGE_MARKETPLACE_PUBLISH_SURFACE_ID,
    FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_API_METHOD,
    FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SURFACE_ID,
    FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_WRITE_API_METHOD,
    FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_API_METHOD,
    FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID,
    FORGE_MARKETPLACE_REMOTE_INDEX_WRITE_API_METHOD,
    FORGE_MARKETPLACE_REMOTE_INGEST_API_METHOD,
    FORGE_MARKETPLACE_STATIC_PUBLICATION_API_METHOD,
    FORGE_MARKETPLACE_STATIC_PUBLICATION_SURFACE_ID,
    FORGE_MARKETPLACE_STATIC_PUBLICATION_WRITE_API_METHOD,
    FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_API_METHOD,
    FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SURFACE_ID,
    FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_WRITE_API_METHOD,
    FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_API_METHOD,
    FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SURFACE_ID,
    FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_WRITE_API_METHOD,
    FORGE_MARKETPLACE_SURFACE_ID,
    FORGE_MARKETPLACE_WRITE_API_METHOD,
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
    build_forge_marketplace_static_host_publication,
    build_forge_marketplace_static_host_upload_handoff,
    build_forge_marketplace_static_host_upload_receipt,
)
from runtime.forge.proof_deck import build_chaser_forge_proof_deck
from runtime.forge.protected_core import PROTECTED_CORE_PATH_PATTERNS
from runtime.forge.registry import (
    build_extension_registry,
    build_live_install_approval,
    build_live_install_execution,
    build_rollback_approval,
    build_rollback_execution,
    build_sandbox_install_approval,
    build_sandbox_registry_write_execution,
)
from runtime.forge.validator import validate_manifest


MODEL_VERSION = "chaser_forge.panel.v1"
SURFACE_ID = "chaser_forge_panel"
DEMO_MANIFEST_PATH = Path(__file__).with_name("examples") / "ugc_campaign_studio.manifest.json"
_DEMO_MANIFEST_FALLBACK = {
    "schemaVersion": "forge.extension.v1",
    "id": "ugc-campaign-studio",
    "name": "UGC Campaign Studio",
    "description": "A sandbox-safe workspace page for planning creator briefs, drafts, and campaign reports.",
    "version": "0.1.0",
    "status": "draft",
    "createdBy": {"runtime": "Codex", "surface": "Chaser Forge packaged demo"},
    "compatibility": {"minChaseOS": "2026.05", "requiresStudio": True},
    "risk": {
        "level": "medium",
        "reason": "Uses extension-owned data writes and approval-gated agent/workflow templates only.",
    },
    "permissions": [
        "workspace.read.basic",
        "extension.data.read",
        "extension.data.write",
        "ui.render.preview",
        "ui.render.workspace_page",
        "dashboard.widget.render",
        "report.render",
        "agent.run.approval_gated",
        "workflow.run.approval_gated",
    ],
    "extensionPoints": [
        {
            "type": "sidebar.nav.item",
            "id": "ugc-campaign-studio.nav",
            "label": "UGC Campaign Studio",
            "route": "/workspace/{workspaceId}/extensions/ugc-campaign-studio",
        },
        {
            "type": "workspace.page",
            "id": "ugc-campaign-studio.page",
            "title": "UGC Campaign Studio",
            "route": "/workspace/{workspaceId}/extensions/ugc-campaign-studio",
            "component": {
                "type": "studio_panel",
                "entry": "extensions/ugc-campaign-studio/ui/page.json",
            },
            "permissions": [
                "workspace.read.basic",
                "extension.data.read",
                "extension.data.write",
            ],
        },
        {
            "type": "dashboard.widget",
            "id": "ugc-campaign-studio.widget",
            "title": "Campaign Pipeline",
            "component": {
                "type": "dashboard_widget",
                "entry": "extensions/ugc-campaign-studio/ui/widget.json",
            },
            "permissions": ["dashboard.widget.render", "extension.data.read"],
        },
        {
            "type": "agent.preset",
            "id": "ugc-campaign-studio.brief-agent",
            "name": "Campaign Brief Drafter",
            "permissions": ["agent.run.approval_gated"],
        },
        {
            "type": "workflow.template",
            "id": "ugc-campaign-studio.review-workflow",
            "name": "Creator Brief Review",
            "permissions": ["workflow.run.approval_gated"],
        },
    ],
    "ui": {
        "routes": ["/workspace/{workspaceId}/extensions/ugc-campaign-studio"],
        "components": [
            {
                "type": "studio_panel",
                "entry": "extensions/ugc-campaign-studio/ui/page.json",
            },
            {
                "type": "dashboard_widget",
                "entry": "extensions/ugc-campaign-studio/ui/widget.json",
            },
        ],
    },
    "workflows": [
        {
            "id": "ugc-campaign-studio.brief-review",
            "steps": [
                {"type": "preview.render"},
                {"type": "approval.request"},
                {"type": "extension.data.write"},
                {"type": "report.render"},
            ],
            "approvalRule": "operator-explicit",
        }
    ],
    "agents": [
        {
            "id": "ugc-campaign-studio.brief-agent",
            "tools": [
                "content.generate",
                "content.review",
                "data.read.extension",
                "data.write.extension",
                "workflow.run.approval_gated",
            ],
            "memoryScopes": [
                "extension.local",
                "project.reference",
                "session.ephemeral",
            ],
        }
    ],
    "dataSchemas": [
        {
            "collection": "ext_ugc_campaign_studio_campaigns",
            "fields": ["campaign_id", "brief", "creator", "status", "report"],
        }
    ],
    "preview": {
        "productionWrites": False,
        "externalCalls": False,
        "scheduleActivation": False,
        "secretsAccess": False,
    },
    "install": {
        "targetPaths": [
            "extensions/ugc-campaign-studio/manifest.json",
            "extensions/ugc-campaign-studio/ui/page.json",
            "extensions/ugc-campaign-studio/ui/widget.json",
            "extensions/ugc-campaign-studio/workflows/brief-review.json",
        ],
        "lifecycle": ["draft", "preview", "sandbox", "active", "disabled", "archived"],
        "liveInstallRequires": [
            "operator_approval",
            "clean_validation",
            "rollback_snapshot",
        ],
    },
    "rollback": {
        "strategy": "disable_extension_and_restore_previous_registry_snapshot",
        "snapshotPolicy": "manifest_and_extension_owned_data",
        "versionRetention": 3,
    },
}

_AUTHORITY = {
    "read_only": False,
    "local_package_artifact_write_allowed": True,
    "local_catalog_write_allowed": True,
    "source_specific_decision_write_allowed": True,
    "source_specific_approval_consumption_allowed": True,
    "governed_extension_owned_file_write_allowed": True,
    "manual_static_artifact_write_allowed": True,
    "generic_approval_consumption_allowed": False,
    "ambient_remote_marketplace_calls_allowed": False,
    "network_upload_allowed": False,
    "network_fetch_allowed": False,
    "external_registry_mutation_allowed": False,
    "payment_mutation_allowed": False,
    "license_checkout_allowed": False,
    "provider_calls_allowed": False,
    "agent_bus_dispatch_allowed": False,
    "runtime_policy_write_allowed": False,
    "protected_core_mutation_allowed": False,
    "studio_shell_patch_by_extension_allowed": False,
    "installer_writes_allowed": False,
    "secret_or_credential_access_allowed": False,
    "pulse_memory_mutation_allowed": False,
    "personal_map_mutation_allowed": False,
    "rnd_truth_state_mutation_allowed": False,
    "canonical_mutation_allowed": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_demo_manifest() -> dict[str, Any]:
    if DEMO_MANIFEST_PATH.exists():
        return json.loads(DEMO_MANIFEST_PATH.read_text(encoding="utf-8"))
    return dict(_DEMO_MANIFEST_FALLBACK)


def _extension_operating_context(
    *,
    summary: dict[str, Any],
    registry: dict[str, Any],
    marketplace_library: dict[str, Any],
    points: list[dict[str, Any]],
    lifecycle: list[dict[str, Any]],
    proof_deck: dict[str, Any],
) -> dict[str, Any]:
    return {
        "title": "Extension Operating Context",
        "description": (
            "Governed local extension builder for validating manifests, inspecting local catalog/library state, "
            "and moving packages through source-specific review/install lanes."
        ),
        "source": "runtime/forge registry, validator, review lifecycle, marketplace model, and quality records",
        "safe_action": (
            "Inspect extension capability, write local/manual records, and use existing review-gated "
            "Forge controls. Remote exchange, provider calls, Agent Bus dispatch, protected-core changes, "
            "payment/license changes, and installer writes remain unavailable here."
        ),
        "cards": [
            {
                "label": "Approved extension points",
                "value": len(points),
                "note": "allowed tabs, pages, cards, forms, workflows, presets, templates, commands, reports, tools, and demos",
                "status": "policy-ready",
            },
            {
                "label": "Lifecycle gates",
                "value": len(lifecycle),
                "note": "sandbox, live install, rollback, marketplace import, and install review lanes",
                "status": "review-gated",
            },
            {
                "label": "Local library",
                "value": marketplace_library.get("library_item_count", 0),
                "note": f"{marketplace_library.get('listed_installed_count', 0)} listed installed; {registry.get('entry_count', 0)} registry entries",
                "status": "local-catalog",
            },
            {
                "label": "Quality records",
                "value": "verified" if proof_deck.get("ok") else "needs evidence",
                "note": summary.get("local_mvp_completion_status") or "quality record readback",
                "status": "evidence",
            },
        ],
    }


def _extension_readiness(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": (
            "Extensions can be validated, cataloged locally, packaged for manual/static distribution, and installed only "
            "through existing source-specific review gates."
        ),
        "rows": [
            {
                "label": "Manifest validation and extension-point policy",
                "status": "ready" if summary.get("demo_manifest_valid") else "blocked",
                "note": "Demo extension validates against approved extension points and protected-core policy.",
            },
            {
                "label": "Local marketplace and library",
                "status": "ready" if summary.get("marketplace_catalog_ready") and summary.get("marketplace_local_library_ready") else "blocked",
                "note": "Local catalog publish/readback and library inspection are mounted.",
            },
            {
                "label": "Governed install lifecycle",
                "status": "review-gated" if summary.get("marketplace_install_executor_built") else "blocked",
                "note": "Install writes require source-specific marketplace-import and sandbox review records.",
            },
            {
                "label": "Manual/static distribution artifacts",
                "status": "ready" if summary.get("marketplace_static_upload_receipt_ready") else "blocked",
                "note": "Remote index, hosted bundle, static publication, upload handoff, receipt, and index registration are local/manual artifact lanes.",
            },
            {
                "label": "External marketplace authority",
                "status": "blocked",
                "note": "No ambient network fetch/upload, untrusted third-party exchange, payment/license mutation, provider call, Agent Bus dispatch, or external registry mutation.",
            },
        ],
    }


def _extension_feature_family_coverage() -> list[dict[str, str]]:
    return [
        {
            "family": "Chaser Forge / Extensions",
            "capability": "Approved extension points, manifest validation, protected-core guard",
            "product_surface": "Main / Extensions",
            "status": "COMPLETE / VERIFIED",
            "evidence": "runtime/forge validator, extension_points, protected_core, tests, feature register",
            "boundary": "Generated extensions cannot mutate core, protected governance docs, secrets, runtime policy, schedules, or Studio shell files.",
        },
        {
            "family": "Chaser Forge / Extensions",
            "capability": "Local catalog, local library, marketplace import/install lifecycle",
            "product_surface": "Extensions / Local Library",
            "status": "COMPLETE / GOVERNED LOCAL MVP",
            "evidence": "Forge marketplace, Studio panel, operator-use smoke, and local-library smoke",
            "boundary": "Install writes are extension-owned and require source-specific review decisions.",
        },
        {
            "family": "Chaser Forge / Marketplace",
            "capability": "Remote index, hosted export bundle, static publication, upload handoff, upload receipt, published index registration",
            "product_surface": "Extensions / Distribution",
            "status": "COMPLETE / LOCAL-MANUAL ARTIFACT LANES VERIFIED",
            "evidence": "2026-05-22/23 Chaser Forge remote/static proof logs and smoke harnesses",
            "boundary": "No network upload/fetch, external registry mutation, live URL verification, payment, license checkout, or third-party exchange.",
        },
        {
            "family": "Governance",
            "capability": "Source-specific review decision handoff and package validation",
            "product_surface": "Extensions / Review Gates",
            "status": "COMPLETE / VERIFIED",
            "evidence": "approval_decision, approval_decision_form, registry executors, quality records",
            "boundary": "Global queue controls do not consume Forge reviews; execution stays decision-bound.",
        },
        {
            "family": "Interface / Experience Layer",
            "capability": "Extensions Studio product surface",
            "product_surface": "Main / Extensions",
            "status": "READY / STUDIO SURFACE VERIFIED",
            "evidence": "Studio shell Chaser Forge panel and rendered source QA",
            "boundary": "The surface exposes posture and existing governed controls; it does not grant new runtime, provider, or host authority.",
        },
    ]


def _extension_product_model(
    *,
    summary: dict[str, Any],
    marketplace_library: dict[str, Any],
    marketplace_static_upload_receipt: dict[str, Any],
    marketplace_live_index_input_readiness: dict[str, Any],
) -> dict[str, Any]:
    package_ready = bool(summary.get("marketplace_export_preview_ready"))
    library_count = marketplace_library.get("library_item_count", 0)
    distribution_ready = bool(summary.get("marketplace_static_host_publication_ready")) or bool(
        marketplace_static_upload_receipt.get("status")
    )
    domain_deferred = bool(marketplace_live_index_input_readiness.get("domain_purchase_deferred"))
    return {
        "title": "Extension Model",
        "summary": (
            "One guided lane for local package creation, library review, review-controlled installs, "
            "manual distribution records, and the fixed safety boundary."
        ),
        "status": "Review controlled",
        "stages": [
            {
                "label": "Package Builder",
                "status": "Ready" if package_ready else "Needs review",
                "detail": "Validate manifests and prepare local extension package records.",
                "state": "ready" if package_ready else "neutral",
            },
            {
                "label": "Local Library",
                "status": f"{library_count} listed",
                "detail": "Browse local listings and installed extension records.",
                "state": "ready" if summary.get("marketplace_local_library_ready") else "neutral",
            },
            {
                "label": "Review Gates",
                "status": "Review required",
                "detail": "Sandbox, install, rollback, and import actions stay source-specific.",
                "state": "gated",
            },
            {
                "label": "Distribution",
                "status": "Coming soon" if domain_deferred else "Ready" if distribution_ready else "Preparing",
                "detail": "Static publication and upload records stay local until the official channel is approved.",
                "state": "blocked" if domain_deferred else "ready" if distribution_ready else "neutral",
            },
            {
                "label": "Safety Boundary",
                "status": "Closed",
                "detail": "No provider call, Agent Bus dispatch, payment, external registry, installer, or protected-core write starts here.",
                "state": "blocked",
            },
        ],
    }


def _extension_product_objects(
    *,
    summary: dict[str, Any],
    registry: dict[str, Any],
    marketplace_library: dict[str, Any],
    marketplace_remote_distribution: dict[str, Any],
    marketplace_static_upload_receipt: dict[str, Any],
    proof_deck: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "id": "forge-foundation",
            "title": "Local Extension Builder",
            "status": summary.get("local_mvp_completion_status", "local build"),
            "kind": "Extension Surface",
            "detail": "Manifest validation, approved extension points, lifecycle gates, and protected-core policy.",
            "ref": "runtime/forge/",
            "mode": "local builder",
        },
        {
            "id": "local-library",
            "title": "Local Marketplace Library",
            "status": marketplace_library.get("status", "local_library"),
            "kind": "Local Catalog",
            "detail": f"{marketplace_library.get('library_item_count', 0)} library items; {registry.get('entry_count', 0)} registry entries.",
            "ref": marketplace_library.get("catalog_path") or "runtime/forge/registry/extensions.json",
            "mode": "local library",
        },
        {
            "id": "governed-install",
            "title": "Governed Install Lifecycle",
            "status": "review-gated",
            "kind": "Review Lane",
            "detail": "Sandbox, live install, rollback, marketplace import, sandbox request, and install lanes require source-specific decisions.",
            "ref": "07_LOGS/Agent-Activity/_forge_*",
            "mode": "review gate",
        },
        {
            "id": "static-distribution",
            "title": "Static Distribution Artifacts",
            "status": marketplace_static_upload_receipt.get("status", marketplace_remote_distribution.get("status", "manual-static")),
            "kind": "Manual Distribution",
            "detail": "Remote index, hosted bundle, static publication, upload handoff, receipt, and index registration are local/manual artifacts.",
            "ref": marketplace_remote_distribution.get("remote_index_artifact_path") or "07_LOGS/Workflow-Proofs",
            "mode": "manual records",
        },
        {
            "id": "proof-chain",
            "title": "Quality Record Chain",
            "status": "ready" if proof_deck.get("ok") else "needs-records",
            "kind": "Records",
            "detail": "Forge proof deck, completion audit, and distribution evidence are linked for review.",
            "ref": proof_deck.get("markdown_path") or "07_LOGS/Workflow-Proofs",
            "mode": "quality records",
        },
        {
            "id": "blocked-authority",
            "title": "Blocked Authority",
            "status": "blocked-by-design",
            "kind": "Boundary",
            "detail": "No ambient remote exchange, network upload/fetch, external registry mutation, payment/license mutation, provider calls, Agent Bus dispatch, or protected-core mutation.",
            "ref": "06_AGENTS/Chaser-Forge-Feature-Family.md",
            "mode": "boundary",
        },
    ]


def _extension_workspace_views(
    *,
    summary: dict[str, Any],
    marketplace_library: dict[str, Any],
    marketplace_live_index_input_readiness: dict[str, Any],
    proof_deck: dict[str, Any],
) -> list[dict[str, Any]]:
    domain_deferred = bool(marketplace_live_index_input_readiness.get("domain_purchase_deferred"))
    records_ready = bool(proof_deck.get("ok")) and not bool(proof_deck.get("blockers"))
    return [
        {
            "id": "overview",
            "label": "Overview",
            "count": summary.get("extension_point_count", 0),
            "status": "Ready",
            "description": "Model, capability map, and safety boundary.",
        },
        {
            "id": "library",
            "label": "Library",
            "count": marketplace_library.get("library_item_count", 0),
            "status": "Ready" if summary.get("marketplace_local_library_ready") else "Needs records",
            "description": "Local listings and installed extension records.",
        },
        {
            "id": "review",
            "label": "Review Gates",
            "count": 4,
            "status": "Review required",
            "description": "Sandbox, live install, rollback, and marketplace import gates.",
        },
        {
            "id": "distribution",
            "label": "Distribution",
            "count": 5,
            "status": "Coming soon" if domain_deferred else "Ready",
            "description": "Manual/static distribution records and upload receipts.",
        },
        {
            "id": "records",
            "label": "Records",
            "count": len(proof_deck.get("slides") or []),
            "status": "Ready" if records_ready else "Needs records",
            "description": "Quality records and gate details.",
        },
    ]


def _extension_product_hardening_contract() -> dict[str, Any]:
    return {
        "purpose_statement": (
            "Choose a Forge extension, validate its manifest, review permissions and sandbox proof, "
            "then prepare the exact approval handoff before any install or rollback can run."
        ),
        "primary_operator_action": {
            "label": "Choose extension and preview install",
            "kind": "blocked-action-preview",
            "enabled": False,
            "blocked_reason": (
                "No extension install runs until manifest validation, permission disclosure, "
                "sandbox proof, and source-specific operator approval are present."
            ),
            "next_step": (
                "Open the local library or package preview, copy the generated review packet, "
                "then record a source-specific approval before running an executor."
            ),
        },
        "install_import_flow": [
            {
                "id": "choose_extension",
                "label": "Choose extension",
                "state": "preview",
                "detail": "Select a local catalog listing or package preview; no remote fetch is started here.",
            },
            {
                "id": "validate_manifest",
                "label": "Validate manifest",
                "state": "ready",
                "detail": "Check schema version, approved extension points, target paths, lifecycle, and protected-core policy.",
            },
            {
                "id": "disclose_permissions",
                "label": "Disclose permissions",
                "state": "ready",
                "detail": "Show requested workspace, UI, dashboard, report, agent, workflow, data, and preview permissions in plain English.",
            },
            {
                "id": "prove_sandbox",
                "label": "Prove sandbox",
                "state": "gated",
                "detail": "Prepare sandbox approval and registry-write preview records before any extension-owned write can run.",
            },
            {
                "id": "handoff_approval",
                "label": "Approval handoff",
                "state": "gated",
                "detail": "Copy the source-specific operator statement and expected digest into the Forge review handoff.",
            },
            {
                "id": "rollback_readiness",
                "label": "Rollback readiness",
                "state": "gated",
                "detail": "Require a rollback snapshot and rollback approval packet before live install execution can be treated as ready.",
            },
        ],
        "plain_english_sections": [
            {
                "title": "What this page does",
                "body": "Turns a local Forge package into a reviewable install/import preview with manifest validation, permission disclosure, sandbox proof, and rollback checks.",
            },
            {
                "title": "What it produces",
                "body": "Local package previews, approval request records, sandbox request records, install/rollback readiness signals, and evidence links for operator review.",
            },
            {
                "title": "What is blocked",
                "body": "Unapproved install, ambient remote marketplace fetch, external registry mutation, payment/license changes, provider calls, Agent Bus dispatch, and protected-core writes.",
            },
            {
                "title": "What to do next",
                "body": "Choose a local listing or package preview, review validation and permissions, create the source-specific approval handoff, then run the executor only after approval exists.",
            },
        ],
        "empty_states": {
            "local_library": (
                "No local marketplace listings yet. Publish or import a package preview first; "
                "this page will not fetch remote listings by itself."
            ),
            "approval_queue": (
                "No pending Forge approval packets. Generate an import, sandbox, install, or rollback request before using the decision helper."
            ),
            "sandbox_proof": (
                "No sandbox proof is written yet. Run the sandbox request preview and keep writes disabled until review is recorded."
            ),
        },
        "error_states": {
            "manifest_invalid": (
                "Manifest validation failed. Fix the listed schema, extension-point, permission, "
                "or protected-path issue before requesting approval."
            ),
            "approval_digest_mismatch": (
                "Approval digest does not match the source packet. Re-open the current packet and copy the exact digest before submitting."
            ),
            "sandbox_proof_missing": (
                "Sandbox proof is missing. Do not run install execution until sandbox review and rollback readiness are both present."
            ),
        },
        "authority_boundary": {
            "live_install_without_approval": False,
            "remote_marketplace_fetch": False,
            "external_registry_mutation": False,
            "payment_or_license_mutation": False,
            "provider_or_agent_bus_dispatch": False,
            "protected_core_write": False,
        },
    }


def build_chaser_forge_panel(vault_root: str | Path) -> dict[str, Any]:
    manifest = load_demo_manifest()
    validation = validate_manifest(manifest)
    registry = build_extension_registry(vault_root)
    sandbox_approval = build_sandbox_install_approval(vault_root, manifest=manifest)
    sandbox_writer = build_sandbox_registry_write_execution(vault_root, manifest=manifest)
    live_approval = build_live_install_approval(vault_root, manifest=manifest)
    live_executor = build_live_install_execution(vault_root, manifest=manifest)
    rollback_approval = build_rollback_approval(vault_root, manifest=manifest)
    rollback_executor = build_rollback_execution(vault_root, manifest=manifest)
    proof_deck = build_chaser_forge_proof_deck(vault_root, write=False)
    marketplace_export = build_forge_marketplace_export_package(vault_root, manifest=manifest)
    marketplace_import_preview = build_forge_marketplace_import_preview(
        vault_root,
        package_payload=marketplace_export.get("package_payload") or {},
    )
    marketplace_import_approval = build_forge_marketplace_import_sandbox_approval(
        vault_root,
        package_payload=marketplace_export.get("package_payload") or {},
    )
    marketplace_catalog = build_forge_marketplace_catalog(vault_root)
    marketplace_publish = build_forge_marketplace_publish(
        vault_root,
        package_payload=marketplace_export.get("package_payload") or {},
    )
    marketplace_remote_distribution = build_forge_marketplace_remote_distribution(
        vault_root,
        package_payload=marketplace_export.get("package_payload") or {},
        publisher_id="local-operator",
        publisher_display_name="Local Operator",
    )
    marketplace_remote_ingest_preview = build_forge_marketplace_remote_ingest_preview(
        vault_root,
        remote_index_payload=marketplace_remote_distribution.get("remote_index_payload") or {},
        expected_remote_index_digest=str(marketplace_remote_distribution.get("remote_index_digest_sha256") or ""),
        expected_listing_digest=str(marketplace_remote_distribution.get("listing_digest_sha256") or ""),
        trusted_publisher_ids=["local-operator"],
    )
    marketplace_hosted_export_bundle = build_forge_marketplace_hosted_export_bundle(
        vault_root,
        remote_index_payload=marketplace_remote_distribution.get("remote_index_payload") or {},
        expected_remote_index_digest=str(marketplace_remote_distribution.get("remote_index_digest_sha256") or ""),
        publisher_id="local-operator",
        publisher_display_name="Local Operator",
    )
    marketplace_static_host_publication = build_forge_marketplace_static_host_publication(
        vault_root,
        hosted_bundle_payload=marketplace_hosted_export_bundle.get("hosted_bundle_payload") or {},
        expected_remote_index_digest=str(marketplace_hosted_export_bundle.get("remote_index_digest_sha256") or ""),
        expected_hosted_bundle_digest=str(marketplace_hosted_export_bundle.get("hosted_bundle_digest_sha256") or ""),
    )
    marketplace_static_upload_handoff = build_forge_marketplace_static_host_upload_handoff(
        vault_root,
        static_publication_preview=marketplace_static_host_publication,
        expected_remote_index_digest=str(marketplace_static_host_publication.get("remote_index_digest_sha256") or ""),
        expected_hosted_bundle_digest=str(marketplace_static_host_publication.get("hosted_bundle_digest_sha256") or ""),
        expected_static_publication_digest=str(marketplace_static_host_publication.get("static_publication_digest_sha256") or ""),
    )
    marketplace_static_upload_receipt = build_forge_marketplace_static_host_upload_receipt(
        vault_root,
        upload_handoff_preview=marketplace_static_upload_handoff,
        expected_remote_index_digest=str(marketplace_static_upload_handoff.get("remote_index_digest_sha256") or ""),
        expected_hosted_bundle_digest=str(marketplace_static_upload_handoff.get("hosted_bundle_digest_sha256") or ""),
        expected_static_publication_digest=str(marketplace_static_upload_handoff.get("static_publication_digest_sha256") or ""),
        expected_upload_handoff_digest=str(marketplace_static_upload_handoff.get("upload_handoff_digest_sha256") or ""),
        operator_uploaded_base_url="https://example.invalid/chaser-forge",
    )
    marketplace_published_static_index_registration = build_forge_marketplace_published_static_index_registration(
        vault_root,
        upload_receipt_preview=marketplace_static_upload_receipt,
        expected_remote_index_digest=str(marketplace_static_upload_receipt.get("remote_index_digest_sha256") or ""),
        expected_hosted_bundle_digest=str(marketplace_static_upload_receipt.get("hosted_bundle_digest_sha256") or ""),
        expected_static_publication_digest=str(marketplace_static_upload_receipt.get("static_publication_digest_sha256") or ""),
        expected_upload_handoff_digest=str(marketplace_static_upload_receipt.get("upload_handoff_digest_sha256") or ""),
        expected_upload_receipt_digest=str(marketplace_static_upload_receipt.get("upload_receipt_digest_sha256") or ""),
        operator_published_static_index_url="https://example.invalid/chaser-forge/index.json",
    )
    marketplace_live_index_input_prefill = build_forge_marketplace_live_index_input_prefill(
        vault_root,
        static_publication_preview=marketplace_static_host_publication,
    )
    marketplace_live_index_input_readiness = build_forge_marketplace_live_index_input_readiness(vault_root)
    marketplace_import_sandbox_request = build_forge_marketplace_import_sandbox_request(
        vault_root,
        import_approval_artifact_path=marketplace_import_approval.get("approval_artifact_path") or "",
    )
    marketplace_install_executor = build_forge_marketplace_install_execution(vault_root)
    marketplace_local_library = build_forge_marketplace_local_library(vault_root)
    points = list_approved_extension_points()
    live_control_proof = proof_deck.get("live_studio_control_proof") if isinstance(proof_deck.get("live_studio_control_proof"), dict) else {}
    operator_use_proof = proof_deck.get("operator_use_studio_proof") if isinstance(proof_deck.get("operator_use_studio_proof"), dict) else {}
    local_mvp_complete = bool(
        validation["valid"]
        and proof_deck.get("ok")
        and live_control_proof.get("ok")
        and operator_use_proof.get("ok")
    )
    local_mvp_open_loops = [] if local_mvp_complete else [
        "complete live StudioAPI control proof",
        "refresh proof deck with live control evidence",
        "sync feature register and feature fit register",
    ]
    decision_handoff = {
        "surface": FORGE_APPROVAL_DECISION_SURFACE_ID,
        "api_method": FORGE_APPROVAL_DECISION_API_METHOD,
        "status": "source_specific_handoff_built",
        "source_specific": True,
        "generic_approval_center_control": False,
        "supported_families": ["sandbox", "live-install", "rollback", "marketplace-import"],
        "supported_decisions": list(SUPPORTED_DECISIONS),
        "write_requires": [
            "existing pending Forge approval artifact",
            "expected request digest matching the source artifact",
            "exact operator approval or rejection statement",
            "source-specific Studio API call",
        ],
        "writes_decision_artifact": True,
        "updates_source_approval_artifact": True,
        "approval_consumption_allowed": False,
        "forge_execution_allowed": False,
        "registry_write_allowed": False,
        "extension_file_write_allowed": False,
        "exact_once_marker_reservation_allowed": False,
        "protected_core_mutation_allowed": False,
        "executor_consumption_bound_to_decision_sidecar": True,
        "decision_record_digest_required_by_executor": True,
    }
    decision_form = {
        "surface": FORGE_APPROVAL_DECISION_FORM_SURFACE_ID,
        "api_method": FORGE_APPROVAL_DECISION_FORM_API_METHOD,
        "submit_api_method": FORGE_APPROVAL_DECISION_API_METHOD,
        "status": "source_specific_operator_form_contract_built",
        "source_specific": True,
        "generic_approval_center_control": False,
        "supported_families": ["sandbox", "live-install", "rollback", "marketplace-import"],
        "supported_decisions": list(SUPPORTED_DECISIONS),
        "prepares_copyable_operator_statement": True,
        "prepares_submit_payload": True,
        "write_enabled_by_form_preview": False,
        "approval_consumption_allowed": False,
        "forge_execution_allowed": False,
        "registry_write_allowed": False,
        "extension_file_write_allowed": False,
        "exact_once_marker_reservation_allowed": False,
        "write_requires": [
            "existing pending Forge approval artifact",
            "selected approve/reject decision",
            "expected request digest copied from the source artifact",
            "exact operator approval or rejection statement",
            "source-specific Studio review API call",
        ],
    }
    summary = {
        "builder_surface": "Chaser Forge",
        "implementation_stage": (
            "Chaser Forge marketplace, install lifecycle, proof chain, Studio surface, and operator-use button proof complete"
            if local_mvp_complete
            else "MVP approved rollback executor plus marketplace publish/install foundation"
        ),
        "local_mvp_completion_status": (
            "COMPLETE / LOCAL GOVERNED MVP VERIFIED"
            if local_mvp_complete
            else "PARTIAL / LOCAL MVP EVIDENCE CHAIN NOT YET CLOSED"
        ),
        "local_mvp_implemented": local_mvp_complete,
        "live_studio_control_proof_verified": bool(live_control_proof.get("ok")),
        "operator_use_studio_proof_verified": bool(operator_use_proof.get("ok")),
        "public_marketplace_deferred": bool(marketplace_live_index_input_readiness.get("domain_purchase_deferred")),
        "public_marketplace_status": (
            "DEFERRED / DOMAIN PURCHASE REQUIRED / LIVE INDEX INPUT NOT READY"
            if marketplace_live_index_input_readiness.get("domain_purchase_deferred")
            else "READY FOR LIVE FETCH INPUT"
            if marketplace_live_index_input_readiness.get("ready_for_live_verification")
            else "COMPLETE LOCALLY / LIVE INDEX INPUT REQUIRED"
        ),
        "remaining_local_mvp_open_loops": local_mvp_open_loops,
        "remaining_external_open_loops": list(
            marketplace_live_index_input_readiness.get("next_operator_inputs") or []
        ),
        "extension_point_count": len(points),
        "lifecycle_stage_count": len(LIFECYCLE_MODEL),
        "protected_core_pattern_count": len(PROTECTED_CORE_PATH_PATTERNS),
        "registry_entry_count": registry.get("entry_count", 0),
        "demo_manifest_valid": bool(validation["valid"]),
        "generated_core_mutation_allowed": False,
        "installer_writes_enabled": False,
        "sandbox_install_model_declared": True,
        "sandbox_approval_preview_ready": bool(sandbox_approval.get("ok")),
        "sandbox_approval_request_written": bool(sandbox_approval.get("approval_request_written")),
        "sandbox_registry_writer_built": True,
        "sandbox_registry_writer_ready": bool(sandbox_writer.get("ok")),
        "sandbox_registry_execution_enabled": False,
        "registry_writer_built": True,
        "live_install_approval_packet_built": True,
        "live_install_approval_preview_ready": bool(live_approval.get("ok")),
        "live_install_approval_request_written": bool(live_approval.get("approval_request_written")),
        "live_install_executor_built": True,
        "live_install_executor_ready": bool(live_executor.get("ok")),
        "live_install_execution_enabled": False,
        "live_install_requires_operator_approval": True,
        "rollback_approval_packet_built": True,
        "rollback_approval_preview_ready": bool(rollback_approval.get("ok")),
        "rollback_approval_request_written": bool(rollback_approval.get("approval_request_written")),
        "rollback_executor_built": True,
        "rollback_executor_ready": bool(rollback_executor.get("ok")),
        "rollback_execution_enabled": False,
        "rollback_requires_operator_approval": True,
        "approval_center_decision_handoff_built": True,
        "operator_decision_form_contract_built": True,
        "operator_decision_form_write_enabled": False,
        "operator_decision_form_generic_control": False,
        "approval_decision_write_enabled_by_panel": False,
        "approval_decision_consumption_allowed": False,
        "decision_bound_executor_validation_ready": True,
        "executor_requires_decision_sidecar": True,
        "proof_deck_packaged": bool(proof_deck.get("ok")),
        "proof_deck_log_only": bool(proof_deck.get("log_only")),
        "proof_deck_write_executed": bool(proof_deck.get("write_executed")),
        "proof_deck_read_only": bool(proof_deck.get("read_only")),
        "proof_deck_blocker_count": len(proof_deck.get("blockers") or []),
        "proof_deck_feature_status": proof_deck.get("feature_status") or "",
        "marketplace_export_package_built": True,
        "marketplace_export_preview_ready": bool(marketplace_export.get("ok")),
        "marketplace_package_write_enabled_by_panel": True,
        "marketplace_catalog_built": True,
        "marketplace_catalog_ready": bool(marketplace_catalog.get("ok")),
        "marketplace_catalog_entry_count": marketplace_catalog.get("entry_count", 0),
        "marketplace_publish_built": True,
        "marketplace_publish_preview_ready": bool(marketplace_publish.get("ok")),
        "marketplace_publish_allowed": bool(marketplace_publish.get("ok")),
        "marketplace_publish_write_enabled_by_panel": True,
        "marketplace_import_preview_built": True,
        "marketplace_import_preview_ready": bool(marketplace_import_preview.get("ok")),
        "marketplace_import_approval_packet_built": True,
        "marketplace_import_approval_preview_ready": bool(marketplace_import_approval.get("ok")),
        "marketplace_import_approval_request_written": bool(
            marketplace_import_approval.get("approval_request_written")
        ),
        "marketplace_import_approval_consumption_allowed": True,
        "marketplace_import_approval_consumption_requires_install_executor": True,
        "marketplace_import_sandbox_request_bridge_built": True,
        "marketplace_import_sandbox_request_preview_ready": bool(marketplace_import_sandbox_request.get("ok")),
        "marketplace_import_sandbox_request_written": bool(
            marketplace_import_sandbox_request.get("sandbox_approval_request_written")
        ),
        "marketplace_import_approval_consumed_by_bridge": False,
        "marketplace_import_sandbox_execution_allowed": bool(marketplace_install_executor.get("surface")),
        "marketplace_install_executor_built": True,
        "marketplace_install_executor_ready": bool(marketplace_install_executor.get("ok")),
        "marketplace_governed_auto_install_available": True,
        "marketplace_auto_install_allowed": True,
        "marketplace_auto_install_requires_approval": True,
        "marketplace_unauthorized_auto_install_allowed": False,
        "marketplace_local_library_built": True,
        "marketplace_local_library_ready": bool(marketplace_local_library.get("ok")),
        "marketplace_local_library_read_only": True,
        "marketplace_local_library_item_count": marketplace_local_library.get("library_item_count", 0),
        "marketplace_local_library_listed_installed_count": marketplace_local_library.get("listed_installed_count", 0),
        "marketplace_local_library_installed_unlisted_count": marketplace_local_library.get("installed_unlisted_count", 0),
        "marketplace_local_library_remote_exchange_blocked": not bool(
            marketplace_local_library.get("remote_marketplace_call_allowed")
        ),
        "marketplace_remote_distribution_built": True,
        "marketplace_remote_distribution_ready": bool(marketplace_remote_distribution.get("ok")),
        "marketplace_remote_index_write_digest_gated": True,
        "marketplace_remote_ingest_preview_ready": bool(marketplace_remote_ingest_preview.get("ok")),
        "marketplace_remote_ingest_digest_gated": True,
        "marketplace_remote_network_calls_blocked": not bool(
            marketplace_remote_distribution.get("remote_network_publish_allowed")
        ),
        "marketplace_remote_payment_mutation_blocked": not bool(
            marketplace_remote_distribution.get("payment_mutation_allowed")
        ),
        "marketplace_remote_publisher_attestation_verified": bool(
            marketplace_remote_ingest_preview.get("publisher_attestation_verified")
        ),
        "marketplace_hosted_export_bundle_built": True,
        "marketplace_hosted_export_bundle_ready": bool(marketplace_hosted_export_bundle.get("ok")),
        "marketplace_hosted_export_bundle_digest_gated": True,
        "marketplace_hosted_export_manual_static_ready": bool(
            marketplace_hosted_export_bundle.get("manual_static_host_ready")
        ),
        "marketplace_hosted_export_network_publish_blocked": not bool(
            marketplace_hosted_export_bundle.get("remote_network_publish_allowed")
        ),
        "marketplace_hosted_export_payment_mutation_blocked": not bool(
            marketplace_hosted_export_bundle.get("payment_mutation_allowed")
        ),
        "marketplace_static_host_publication_built": True,
        "marketplace_static_host_publication_ready": bool(marketplace_static_host_publication.get("ok")),
        "marketplace_static_host_publication_digest_gated": True,
        "marketplace_static_host_publication_manual_upload_ready": bool(
            marketplace_static_host_publication.get("manual_upload_ready")
        ),
        "marketplace_static_host_publication_network_upload_blocked": not bool(
            marketplace_static_host_publication.get("remote_network_publish_allowed")
        ),
        "marketplace_static_host_publication_payment_mutation_blocked": not bool(
            marketplace_static_host_publication.get("payment_mutation_allowed")
        ),
        "marketplace_static_upload_handoff_built": True,
        "marketplace_static_upload_handoff_ready": bool(marketplace_static_upload_handoff.get("ok")),
        "marketplace_static_upload_handoff_digest_gated": True,
        "marketplace_static_upload_handoff_manual_action_required": bool(
            (marketplace_static_upload_handoff.get("handoff_payload") or {}).get("operator_manual_action_required")
        ),
        "marketplace_static_upload_handoff_network_upload_blocked": not bool(
            marketplace_static_upload_handoff.get("network_upload_allowed")
        ),
        "marketplace_static_upload_handoff_external_registry_blocked": not bool(
            marketplace_static_upload_handoff.get("external_registry_mutation_allowed")
        ),
        "marketplace_static_upload_receipt_built": True,
        "marketplace_static_upload_receipt_ready": bool(marketplace_static_upload_receipt.get("ok")),
        "marketplace_static_upload_receipt_digest_gated": True,
        "marketplace_static_upload_receipt_operator_statement_required": bool(
            marketplace_static_upload_receipt.get("required_operator_receipt_statement")
        ),
        "marketplace_static_upload_receipt_network_fetch_blocked": not bool(
            marketplace_static_upload_receipt.get("network_fetch_allowed")
        ),
        "marketplace_static_upload_receipt_external_registry_blocked": not bool(
            marketplace_static_upload_receipt.get("external_registry_mutation_allowed")
        ),
        "marketplace_published_static_index_registration_built": True,
        "marketplace_published_static_index_registration_ready": bool(
            marketplace_published_static_index_registration.get("ok")
        ),
        "marketplace_published_static_index_registration_digest_gated": True,
        "marketplace_published_static_index_registration_operator_statement_required": bool(
            marketplace_published_static_index_registration.get("required_operator_registration_statement")
        ),
        "marketplace_published_static_index_registration_network_fetch_blocked": not bool(
            marketplace_published_static_index_registration.get("network_fetch_allowed")
        ),
        "marketplace_published_static_index_registration_external_registry_blocked": not bool(
            marketplace_published_static_index_registration.get("external_registry_mutation_allowed")
        ),
        "marketplace_published_static_index_registration_live_url_unverified": not bool(
            marketplace_published_static_index_registration.get("live_url_verified")
        ),
        "marketplace_live_index_input_prefill_built": True,
        "marketplace_live_index_input_prefill_ready": bool(
            marketplace_live_index_input_prefill.get("ok")
        ),
        "marketplace_live_index_input_prefill_domain_deferred": bool(
            marketplace_live_index_input_prefill.get("domain_purchase_deferred")
        ),
        "marketplace_live_index_input_prefill_network_fetch_blocked": not bool(
            marketplace_live_index_input_prefill.get("network_fetch_allowed")
        ),
        "marketplace_live_index_input_prefill_external_registry_blocked": not bool(
            marketplace_live_index_input_prefill.get("external_registry_mutation_allowed")
        ),
        "marketplace_live_index_input_readiness_built": True,
        "marketplace_live_index_input_ready_for_verification": bool(
            marketplace_live_index_input_readiness.get("ready_for_live_verification")
        ),
        "marketplace_live_index_input_domain_deferred": bool(
            marketplace_live_index_input_readiness.get("domain_purchase_deferred")
        ),
        "marketplace_live_index_input_network_fetch_blocked": not bool(
            marketplace_live_index_input_readiness.get("network_fetch_allowed")
        ),
        "marketplace_live_index_input_external_registry_blocked": not bool(
            marketplace_live_index_input_readiness.get("external_registry_mutation_allowed")
        ),
    }
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault_root),
        "status": "local_mvp_complete" if local_mvp_complete else "mvp_foundation_ready" if validation["valid"] else "blocked",
        "summary": summary,
        "authority": dict(_AUTHORITY),
        "operating_context": _extension_operating_context(
            summary=summary,
            registry=registry,
            marketplace_library=marketplace_local_library,
            points=points,
            lifecycle=list(LIFECYCLE_MODEL),
            proof_deck=proof_deck,
        ),
        "readiness": _extension_readiness(summary),
        "product_hardening": _extension_product_hardening_contract(),
        "feature_family_coverage": _extension_feature_family_coverage(),
        "extension_model": _extension_product_model(
            summary=summary,
            marketplace_library=marketplace_local_library,
            marketplace_static_upload_receipt=marketplace_static_upload_receipt,
            marketplace_live_index_input_readiness=marketplace_live_index_input_readiness,
        ),
        "extension_views": _extension_workspace_views(
            summary=summary,
            marketplace_library=marketplace_local_library,
            marketplace_live_index_input_readiness=marketplace_live_index_input_readiness,
            proof_deck=proof_deck,
        ),
        "product_objects": _extension_product_objects(
            summary=summary,
            registry=registry,
            marketplace_library=marketplace_local_library,
            marketplace_remote_distribution=marketplace_remote_distribution,
            marketplace_static_upload_receipt=marketplace_static_upload_receipt,
            proof_deck=proof_deck,
        ),
        "blocked_authority": {
            "direct_core_rewrite": False,
            "protected_file_write": False,
            "runtime_policy_write": False,
            "schedule_activation": False,
            "secret_or_credential_access": False,
            "agent_bus_direct_dispatch": False,
            "studio_shell_patch_by_extension": False,
        },
        "extension_points": points,
        "lifecycle_model": list(LIFECYCLE_MODEL),
        "audit_events": list(AUDIT_EVENTS),
        "registry": registry,
        "sandbox_approval": sandbox_approval,
        "sandbox_registry_writer": sandbox_writer,
        "live_install_approval": live_approval,
        "live_install_executor": live_executor,
        "rollback_approval": rollback_approval,
        "rollback_executor": rollback_executor,
        "approval_decision_handoff": decision_handoff,
        "approval_decision_form": decision_form,
        "proof_deck": proof_deck,
        "marketplace": {
            "surface": FORGE_MARKETPLACE_SURFACE_ID,
            "catalog_surface": FORGE_MARKETPLACE_CATALOG_SURFACE_ID,
            "catalog_api_method": FORGE_MARKETPLACE_CATALOG_API_METHOD,
            "export_api_method": FORGE_MARKETPLACE_EXPORT_API_METHOD,
            "write_api_method": FORGE_MARKETPLACE_WRITE_API_METHOD,
            "publish_surface": FORGE_MARKETPLACE_PUBLISH_SURFACE_ID,
            "publish_preview_api_method": FORGE_MARKETPLACE_PUBLISH_PREVIEW_API_METHOD,
            "publish_api_method": FORGE_MARKETPLACE_PUBLISH_API_METHOD,
            "import_api_method": FORGE_MARKETPLACE_IMPORT_API_METHOD,
            "import_approval_surface": FORGE_MARKETPLACE_IMPORT_APPROVAL_SURFACE_ID,
            "import_approval_api_method": FORGE_MARKETPLACE_IMPORT_APPROVAL_API_METHOD,
            "import_sandbox_request_surface": FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_SURFACE_ID,
            "import_sandbox_request_preview_api_method": FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_PREVIEW_API_METHOD,
            "import_sandbox_request_api_method": FORGE_MARKETPLACE_IMPORT_SANDBOX_REQUEST_API_METHOD,
            "install_surface": FORGE_MARKETPLACE_INSTALL_SURFACE_ID,
            "install_api_method": FORGE_MARKETPLACE_INSTALL_API_METHOD,
            "local_library_surface": FORGE_MARKETPLACE_LOCAL_LIBRARY_SURFACE_ID,
            "local_library_api_method": FORGE_MARKETPLACE_LOCAL_LIBRARY_API_METHOD,
            "remote_distribution_surface": FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_SURFACE_ID,
            "remote_distribution_api_method": FORGE_MARKETPLACE_REMOTE_DISTRIBUTION_API_METHOD,
            "remote_index_write_api_method": FORGE_MARKETPLACE_REMOTE_INDEX_WRITE_API_METHOD,
            "remote_ingest_api_method": FORGE_MARKETPLACE_REMOTE_INGEST_API_METHOD,
            "hosted_export_bundle_surface": FORGE_MARKETPLACE_HOSTED_BUNDLE_SURFACE_ID,
            "hosted_export_bundle_api_method": FORGE_MARKETPLACE_HOSTED_BUNDLE_API_METHOD,
            "hosted_export_bundle_write_api_method": FORGE_MARKETPLACE_HOSTED_BUNDLE_WRITE_API_METHOD,
            "static_host_publication_surface": FORGE_MARKETPLACE_STATIC_PUBLICATION_SURFACE_ID,
            "static_host_publication_api_method": FORGE_MARKETPLACE_STATIC_PUBLICATION_API_METHOD,
            "static_host_publication_write_api_method": FORGE_MARKETPLACE_STATIC_PUBLICATION_WRITE_API_METHOD,
            "static_upload_handoff_surface": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_SURFACE_ID,
            "static_upload_handoff_api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_API_METHOD,
            "static_upload_handoff_write_api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_HANDOFF_WRITE_API_METHOD,
            "static_upload_receipt_surface": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_SURFACE_ID,
            "static_upload_receipt_api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_API_METHOD,
            "static_upload_receipt_write_api_method": FORGE_MARKETPLACE_STATIC_UPLOAD_RECEIPT_WRITE_API_METHOD,
            "published_static_index_registration_surface": (
                FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_SURFACE_ID
            ),
            "published_static_index_registration_api_method": (
                FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_API_METHOD
            ),
            "published_static_index_registration_write_api_method": (
                FORGE_MARKETPLACE_PUBLISHED_STATIC_INDEX_REGISTRATION_WRITE_API_METHOD
            ),
            "live_index_input_prefill_surface": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_SURFACE_ID,
            "live_index_input_prefill_api_method": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_API_METHOD,
            "live_index_input_prefill_write_api_method": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_PREFILL_WRITE_API_METHOD,
            "live_index_input_readiness_surface": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_SURFACE_ID,
            "live_index_input_readiness_api_method": FORGE_MARKETPLACE_LIVE_INDEX_INPUT_READINESS_API_METHOD,
            "write_enabled_by_panel": True,
            "publish_allowed": bool(marketplace_publish.get("ok")),
            "auto_install_allowed": True,
            "auto_install_requires_approval": True,
            "export_package": marketplace_export,
            "catalog": marketplace_catalog,
            "publish_preview": marketplace_publish,
            "import_preview": marketplace_import_preview,
            "import_approval_request": marketplace_import_approval,
            "import_sandbox_request": marketplace_import_sandbox_request,
            "install_executor": marketplace_install_executor,
            "local_library": marketplace_local_library,
            "remote_distribution": marketplace_remote_distribution,
            "remote_ingest_preview": marketplace_remote_ingest_preview,
            "hosted_export_bundle": marketplace_hosted_export_bundle,
            "static_host_publication": marketplace_static_host_publication,
            "static_upload_handoff": marketplace_static_upload_handoff,
            "static_upload_receipt": marketplace_static_upload_receipt,
            "published_static_index_registration": marketplace_published_static_index_registration,
            "live_index_input_prefill": marketplace_live_index_input_prefill,
            "live_index_input_readiness": marketplace_live_index_input_readiness,
        },
        "demo_manifest": {
            "path": str(DEMO_MANIFEST_PATH),
            "id": manifest.get("id"),
            "name": manifest.get("name"),
            "status": manifest.get("status"),
            "extension_point_types": [point.get("type") for point in manifest.get("extensionPoints", [])],
            "target_paths": (manifest.get("install") or {}).get("targetPaths", []),
            "validation": validation,
        },
        "next_actions": [
            "Use the Local Marketplace Library section to inspect listed and installed local Forge packages after publish/install.",
            "Use the Remote Distribution section to write a digest-gated remote index artifact and ingest trusted listings into the local catalog before the normal approval/install chain.",
            "Use the Hosted Export Bundle control to create a digest-gated manual static-host bundle for operator-reviewed external mirroring.",
            "Use the Static Host Publication control to materialize the hosted bundle into upload-ready local static files before any manual external host upload.",
            "Use the Upload Receipt control after manual upload to record an exact-statement local operator receipt without network fetch or external registry mutation.",
            "Use the Published Index Registration control after receipt to record an operator-declared public index URL without live fetch or external registry mutation.",
            "Use the Live Input Prefill control to write a local domain-deferred input packet with local static-publication fields filled.",
            "Use the Live Index Input Readiness surface to confirm the domain-deferred JSON packet is filled before any future bounded live fetch verification.",
            "Use the source-specific Forge operator decision form to prepare the exact approve/reject handoff for one pending Forge artifact.",
            "After recording a source-specific Forge decision, run executor preview separately.",
            "Use the marketplace export digest to write a local package artifact, then preview import review without installing it.",
            "Use the marketplace import approval request digest to write a pending package import review artifact.",
            "After marketplace-import review approval is recorded, use the import sandbox request digest to write a pending sandbox approval request.",
            "After the sandbox approval is source-specifically approved, use the marketplace install executor to consume both approvals and write the sandbox registry/files through the existing governed writer.",
        ],
    }
