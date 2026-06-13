"""Launcher update checks.

The source file was recovered from a preserved Python bytecode artifact during
the 2026-05-25 updater implementation session. Keep this wrapper small: it
loads the last known compiled implementation, then applies source-level
extensions below it.
"""

from __future__ import annotations

import marshal as _marshal
import hashlib as _wrapper_hashlib
from pathlib import Path as _Path

_RECOVERED_BYTECODE_PATH = _Path(__file__).with_name(
    "recovery"
) / (
    "launcher_update_check_recovered_20260525_012321.cpython-314.bytecode"
)
_RECOVERED_BYTECODE_EXPECTED_SHA256 = (
    "7ce02c54d8efdf2353e2857e0e31e1af00b9fe2cef4564847df0353644580f84"
)

if not _RECOVERED_BYTECODE_PATH.exists():
    raise ImportError(
        "Recovered launcher update bytecode is missing: "
        f"{_RECOVERED_BYTECODE_PATH}"
    )

_RECOVERED_BYTECODE_BYTES = _RECOVERED_BYTECODE_PATH.read_bytes()
_RECOVERED_BYTECODE_SHA256 = _wrapper_hashlib.sha256(
    _RECOVERED_BYTECODE_BYTES
).hexdigest()
if _RECOVERED_BYTECODE_SHA256 != _RECOVERED_BYTECODE_EXPECTED_SHA256:
    raise ImportError(
        "Recovered launcher update bytecode hash mismatch: "
        f"{_RECOVERED_BYTECODE_PATH}"
    )
_RECOVERED_BYTECODE_CODE = _marshal.loads(_RECOVERED_BYTECODE_BYTES[16:])
exec(_RECOVERED_BYTECODE_CODE, globals())
del _RECOVERED_BYTECODE_BYTES
del _RECOVERED_BYTECODE_CODE


from datetime import datetime as _extension_datetime, timezone as _extension_timezone
import inspect as _extension_inspect
import ast as _extension_ast
import importlib.util as _extension_importlib_util
import shutil as _extension_shutil
import json as _extension_json


PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SURFACE_ID = (
    "studio_launcher_update_production_primary_relaunch_receipt_boundary_proof"
)
PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SCHEMA_VERSION = (
    "chaser.update_production_primary_relaunch_receipt_boundary.v1"
)
PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_OPERATOR_STATEMENT_PREFIX = (
    "VALIDATE CHASEOS PRIMARY RELAUNCH RECEIPT BOUNDARY ONLY"
)
SOURCE_RECOVERY_CLEANUP_SURFACE_ID = (
    "studio_launcher_update_source_recovery_cleanup_proof"
)
SOURCE_RECOVERY_CLEANUP_SCHEMA_VERSION = (
    "chaser.update_source_recovery_cleanup.v1"
)
NORMAL_SOURCE_RESTORATION_READINESS_SURFACE_ID = (
    "studio_launcher_update_normal_source_restoration_readiness"
)
NORMAL_SOURCE_RESTORATION_READINESS_SCHEMA_VERSION = (
    "chaser.update_normal_source_restoration_readiness.v1"
)
NORMAL_SOURCE_CANDIDATE_VERIFICATION_SURFACE_ID = (
    "studio_launcher_update_normal_source_candidate_verification_proof"
)
NORMAL_SOURCE_CANDIDATE_VERIFICATION_SCHEMA_VERSION = (
    "chaser.update_normal_source_candidate_verification.v1"
)
NORMAL_SOURCE_CANDIDATE_VERIFICATION_OPERATOR_STATEMENT_PREFIX = (
    "VERIFY CHASEOS NORMAL SOURCE CANDIDATES ONLY"
)
NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SURFACE_ID = (
    "studio_launcher_update_normal_source_candidate_restore_executor_proof"
)
NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SCHEMA_VERSION = (
    "chaser.update_normal_source_candidate_restore_executor.v1"
)
NORMAL_SOURCE_CANDIDATE_RESTORE_OPERATOR_STATEMENT_PREFIX = (
    "RESTORE CHASEOS NORMAL SOURCE CANDIDATES ONLY"
)
SOURCE_REGENERATION_READINESS_SURFACE_ID = (
    "studio_launcher_update_source_regeneration_readiness"
)
SOURCE_REGENERATION_READINESS_SCHEMA_VERSION = (
    "chaser.update_source_regeneration_readiness.v1"
)
SOURCE_REGENERATION_RUNNER_BOUNDARY_SURFACE_ID = (
    "studio_launcher_update_source_regeneration_runner_boundary_proof"
)
SOURCE_REGENERATION_RUNNER_BOUNDARY_SCHEMA_VERSION = (
    "chaser.update_source_regeneration_runner_boundary.v1"
)
SOURCE_REGENERATION_RUNNER_OPERATOR_STATEMENT_PREFIX = (
    "RUN CHASEOS SOURCE REGENERATION CANDIDATE WRITER ONLY"
)
SOURCE_REGENERATION_CANDIDATE_RESTORE_SURFACE_ID = (
    "studio_launcher_update_source_regeneration_candidate_verification_restore_proof"
)
SOURCE_REGENERATION_CANDIDATE_RESTORE_SCHEMA_VERSION = (
    "chaser.update_source_regeneration_candidate_verification_restore.v1"
)
SOURCE_REGENERATION_LIVE_SOURCE_RESTORATION_CLOSEOUT_SURFACE_ID = (
    "studio_launcher_update_source_regeneration_live_source_restoration_closeout_proof"
)
SOURCE_REGENERATION_LIVE_SOURCE_RESTORATION_CLOSEOUT_SCHEMA_VERSION = (
    "chaser.update_source_regeneration_live_source_restoration_closeout.v1"
)
REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SURFACE_ID = (
    "studio_launcher_update_real_source_restoration_execution_regression_boundary_proof"
)
REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SCHEMA_VERSION = (
    "chaser.update_real_source_restoration_execution_regression_boundary.v1"
)
CURRENT_VAULT_SOURCE_RESTORATION_CLOSEOUT_READINESS_SURFACE_ID = (
    "studio_launcher_update_current_vault_source_restoration_closeout_readiness"
)
CURRENT_VAULT_SOURCE_RESTORATION_CLOSEOUT_READINESS_SCHEMA_VERSION = (
    "chaser.update_current_vault_source_restoration_closeout_readiness.v1"
)
SOURCE_CANDIDATE_INVENTORY_WRAPPER_REMOVAL_PREFLIGHT_SURFACE_ID = (
    "studio_launcher_update_source_candidate_inventory_wrapper_removal_preflight"
)
SOURCE_CANDIDATE_INVENTORY_WRAPPER_REMOVAL_PREFLIGHT_SCHEMA_VERSION = (
    "chaser.update_source_candidate_inventory_wrapper_removal_preflight.v1"
)
AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SURFACE_ID = (
    "studio_launcher_update_authoritative_normal_source_candidate_supply_packet"
)
AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SCHEMA_VERSION = (
    "chaser.update_authoritative_normal_source_candidate_supply.v1"
)
AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_OPERATOR_STATEMENT_PREFIX = (
    "SUPPLY CHASEOS AUTHORITATIVE NORMAL SOURCE CANDIDATES ONLY"
)
AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SURFACE_ID = (
    "studio_launcher_update_authoritative_source_candidate_import_boundary_proof"
)
AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SCHEMA_VERSION = (
    "chaser.update_authoritative_source_candidate_import_boundary.v1"
)
AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_OPERATOR_STATEMENT_PREFIX = (
    "IMPORT CHASEOS AUTHORITATIVE SOURCE CANDIDATES ONLY"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_READINESS_SURFACE_ID = (
    "studio_launcher_update_real_authoritative_source_candidate_supply_readiness"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_READINESS_SCHEMA_VERSION = (
    "chaser.update_real_authoritative_source_candidate_supply_readiness.v1"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SURFACE_ID = (
    "studio_launcher_update_real_authoritative_source_candidate_materialization_proof"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SCHEMA_VERSION = (
    "chaser.update_real_authoritative_source_candidate_materialization.v1"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_OPERATOR_STATEMENT_PREFIX = (
    "MATERIALIZE CHASEOS REAL AUTHORITATIVE SOURCE CANDIDATES ONLY"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SURFACE_ID = (
    "studio_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SCHEMA_VERSION = (
    "chaser.update_real_authoritative_source_candidate_import_from_materialization.v1"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_OPERATOR_STATEMENT_PREFIX = (
    "IMPORT CHASEOS REAL AUTHORITATIVE SOURCE CANDIDATES FROM MATERIALIZATION ONLY"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID = (
    "studio_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SCHEMA_VERSION = (
    "chaser.update_real_authoritative_source_candidate_supply_verification_from_materialization_import.v1"
)
REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_OPERATOR_STATEMENT_PREFIX = (
    "VERIFY CHASEOS REAL AUTHORITATIVE SOURCE CANDIDATES FROM MATERIALIZATION IMPORT ONLY"
)
CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SURFACE_ID = (
    "studio_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof"
)
CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SCHEMA_VERSION = (
    "chaser.update_current_vault_wrapper_removal_from_materialization_import_execution.v1"
)
CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_OPERATOR_STATEMENT_PREFIX = (
    "EXECUTE CHASEOS CURRENT VAULT WRAPPER REMOVAL FROM MATERIALIZATION IMPORT ONLY"
)
POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID = (
    "studio_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof"
)
POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SCHEMA_VERSION = (
    "chaser.update_post_wrapper_removal_regression_from_materialization_import.v1"
)
POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_OPERATOR_STATEMENT_PREFIX = (
    "VERIFY CHASEOS POST WRAPPER REMOVAL REGRESSION FROM MATERIALIZATION IMPORT ONLY"
)
CURRENT_VAULT_SOURCE_CLOSEOUT_FROM_MATERIALIZATION_IMPORT_REGRESSION_SURFACE_ID = (
    "studio_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof"
)
CURRENT_VAULT_SOURCE_CLOSEOUT_FROM_MATERIALIZATION_IMPORT_REGRESSION_SCHEMA_VERSION = (
    "chaser.update_current_vault_source_closeout_from_materialization_import_regression.v1"
)
PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID = (
    "studio_launcher_update_production_primary_closeout_after_source_recovery_proof"
)
PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SCHEMA_VERSION = (
    "chaser.update_production_primary_closeout_after_source_recovery.v1"
)
FINAL_PRODUCTION_AUTO_UPDATE_CLOSEOUT_AUDIT_SURFACE_ID = (
    "studio_launcher_update_final_production_auto_update_closeout_audit"
)
FINAL_PRODUCTION_AUTO_UPDATE_CLOSEOUT_AUDIT_SCHEMA_VERSION = (
    "chaser.update_final_production_auto_update_closeout_audit.v1"
)
GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID = (
    "studio_launcher_update_governed_live_completion_evidence_packet"
)
GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SCHEMA_VERSION = (
    "chaser.update_governed_live_completion_evidence_packet.v1"
)
GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_OPERATOR_STATEMENT_PREFIX = (
    "APPROVE CHASEOS GOVERNED LIVE COMPLETION EVIDENCE PACKET ONLY"
)
CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SURFACE_ID = (
    "studio_launcher_update_controlled_live_installer_evidence_runner"
)
CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SCHEMA_VERSION = (
    "chaser.update_controlled_live_installer_evidence_runner.v1"
)
CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_OPERATOR_STATEMENT_PREFIX = (
    "RUN CHASEOS CONTROLLED LIVE INSTALLER EVIDENCE RUNNER ONLY"
)
APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SURFACE_ID = (
    "studio_launcher_update_approved_live_evidence_runner_adapter"
)
APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SCHEMA_VERSION = (
    "chaser.update_approved_live_evidence_runner_adapter.v1"
)
APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_OPERATOR_STATEMENT_PREFIX = (
    "ADAPT CHASEOS APPROVED LIVE EVIDENCE RUNNER RECEIPTS ONLY"
)
APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SURFACE_ID = (
    "studio_launcher_update_approved_live_evidence_runner_real_dry_run"
)
APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SCHEMA_VERSION = (
    "chaser.update_approved_live_evidence_runner_real_dry_run.v1"
)
APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_OPERATOR_STATEMENT_PREFIX = (
    "DRY RUN CHASEOS APPROVED LIVE EVIDENCE RUNNER ONLY"
)
LIVE_RECEIPT_DIGEST_CONSISTENCY_CLOSEOUT_SURFACE_ID = (
    "studio_launcher_update_live_receipt_digest_consistency_closeout"
)
LIVE_RECEIPT_DIGEST_CONSISTENCY_CLOSEOUT_SCHEMA_VERSION = (
    "chaser.update_live_receipt_digest_consistency_closeout.v1"
)
REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SURFACE_ID = (
    "studio_launcher_update_real_live_receipt_capture_boundary"
)
REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SCHEMA_VERSION = (
    "chaser.update_real_live_receipt_capture_boundary.v1"
)
REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_OPERATOR_STATEMENT_PREFIX = (
    "CAPTURE CHASEOS REAL LIVE UPDATER RECEIPTS ONLY"
)
EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SURFACE_ID = (
    "external_chaseos_real_live_updater_receipt_bundle"
)
EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SCHEMA_VERSION = (
    "chaser.external_real_live_updater_receipt_bundle.v1"
)
REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID = (
    "studio_launcher_update_real_live_receipt_bundle_production_runner"
)
REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SCHEMA_VERSION = (
    "chaser.update_real_live_receipt_bundle_production_runner.v1"
)
REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_OPERATOR_STATEMENT_PREFIX = (
    "RUN CHASEOS REAL LIVE RECEIPT BUNDLE PRODUCTION RUNNER ONLY"
)
PRODUCTION_RUNNER_FINAL_CLOSEOUT_BRIDGE_SURFACE_ID = (
    "studio_launcher_update_production_runner_final_closeout_bridge"
)
PRODUCTION_RUNNER_FINAL_CLOSEOUT_BRIDGE_SCHEMA_VERSION = (
    "chaser.update_production_runner_final_closeout_bridge.v1"
)
APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_SURFACE_ID = (
    "studio_launcher_update_approved_production_runner_real_evidence_capture"
)
APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_SCHEMA_VERSION = (
    "chaser.update_approved_production_runner_real_evidence_capture.v1"
)
APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_OPERATOR_STATEMENT_PREFIX = (
    "CAPTURE CHASEOS APPROVED PRODUCTION RUNNER REAL EVIDENCE ONLY"
)
INSTALLER_REAL_ARTIFACT_BUILD_OUTPUT_CAPTURE_SURFACE_ID = (
    "studio_launcher_update_installer_real_artifact_build_output_capture"
)
INSTALLER_REAL_ARTIFACT_BUILD_OUTPUT_CAPTURE_SCHEMA_VERSION = (
    "chaser.update_installer_real_artifact_build_output_capture.v1"
)
DIST_ARTIFACT_ISOLATION_COHABITATION_PROOF_SURFACE_ID = (
    "studio_launcher_update_dist_artifact_isolation_cohabitation_proof"
)
DIST_ARTIFACT_ISOLATION_COHABITATION_PROOF_SCHEMA_VERSION = (
    "chaser.update_dist_artifact_isolation_cohabitation_proof.v1"
)
SIGNED_ARTIFACT_VERIFICATION_CLOSEOUT_SURFACE_ID = (
    "studio_launcher_update_signed_artifact_verification_closeout"
)
SIGNED_ARTIFACT_VERIFICATION_CLOSEOUT_SCHEMA_VERSION = (
    "chaser.update_signed_artifact_verification_closeout.v1"
)
LOCAL_INSTALLER_DISPOSABLE_DRY_RUN_SURFACE_ID = (
    "studio_launcher_update_local_installer_disposable_dry_run_proof"
)
LOCAL_INSTALLER_DISPOSABLE_DRY_RUN_SCHEMA_VERSION = (
    "chaser.update_local_installer_disposable_dry_run.v1"
)
LOCAL_MANIFEST_BACKGROUND_PROMPT_SURFACE_ID = (
    "studio_launcher_update_local_manifest_background_prompt_settings_action"
)
LOCAL_MANIFEST_BACKGROUND_PROMPT_SCHEMA_VERSION = (
    "chaser.update_local_manifest_background_prompt_settings_action.v1"
)
LOCAL_UPDATE_MANIFEST_SCHEMA_VERSION = "chaser.local_update_manifest.v1"
LOCAL_UPDATE_MANIFEST_DEFAULT_RELATIVE_PATH = (
    ".chaseos/updates/local-update-manifest.json"
)
LOCAL_RELEASE_CHANNEL_BLOCKER_CLOSEOUT_SURFACE_ID = (
    "studio_launcher_update_local_release_channel_blocker_closeout"
)
LOCAL_RELEASE_CHANNEL_BLOCKER_CLOSEOUT_SCHEMA_VERSION = (
    "chaser.update_local_release_channel_blocker_closeout.v1"
)
FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS = (
    "github_release_publication_verified",
    "live_release_manifest_readback_verified",
    "release_manifest_signature_verified",
    "live_binary_download_verified",
    "downloaded_artifact_signature_verified",
    "chaseos_installer_signed_output_verified",
    "operator_digest_approval_verified",
    "prompted_install_flow_verified",
    "chaseos_installer_launch_receipt_verified",
    "primary_exe_replacement_verified_live",
    "primary_relaunch_verified_live",
    "rollback_audit_receipt_verified",
    "startup_background_prompt_verified",
    "installed_version_matches_manifest",
)
FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS = (
    "silent_install_performed",
    "secrets_or_private_keys_read_by_chaseos",
    "source_write_performed_by_final_audit",
    "primary_replacement_performed_by_final_audit",
    "github_mutation_performed_by_final_audit",
    "download_performed_by_final_audit",
    "installer_launch_performed_by_final_audit",
)
AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SURFACE_ID = (
    "studio_launcher_update_authoritative_candidate_supply_verification_after_import_proof"
)
AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SCHEMA_VERSION = (
    "chaser.update_authoritative_candidate_supply_verification_after_import.v1"
)
CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_SURFACE_ID = (
    "studio_launcher_update_current_vault_wrapper_removal_after_import_execution_proof"
)
CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_SCHEMA_VERSION = (
    "chaser.update_current_vault_wrapper_removal_after_import_execution.v1"
)
CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_OPERATOR_STATEMENT_PREFIX = (
    "EXECUTE CHASEOS CURRENT VAULT WRAPPER REMOVAL FROM IMPORT ONLY"
)
CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_BOUNDARY_SURFACE_ID = (
    "studio_launcher_update_current_vault_wrapper_removal_executor_boundary_proof"
)
CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_BOUNDARY_SCHEMA_VERSION = (
    "chaser.update_current_vault_wrapper_removal_executor_boundary.v1"
)
CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_OPERATOR_STATEMENT_PREFIX = (
    "REMOVE CHASEOS CURRENT VAULT SOURCE WRAPPERS ONLY"
)
_API_RECOVERED_BYTECODE_RELATIVE_PATH = _Path("recovery") / (
    "api_recovered_20260525_012321.cpython-314.bytecode"
)
_API_RECOVERED_BYTECODE_EXPECTED_SHA256 = (
    "3358fb4015e0d29cf2a871cf2635fa9296f47c77129214fe4ba0b7ff4981af4b"
)

_ORIGINAL_AUTHORITY_FOR_PRIMARY_RELAUNCH = _authority
_ORIGINAL_AUTHORITY_FOR_PRIMARY_RELAUNCH_PARAMETERS = set(
    _extension_inspect.signature(_ORIGINAL_AUTHORITY_FOR_PRIMARY_RELAUNCH).parameters
)
_ORIGINAL_READINESS_FOR_PRIMARY_RELAUNCH = _readiness


def _extension_timestamp(generated_at):
    if generated_at:
        return str(generated_at)
    return (
        _extension_datetime.now(_extension_timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _extension_digest_without(payload, digest_key):
    if not isinstance(payload, dict):
        return ""
    digest_payload = dict(payload)
    digest_payload.pop(digest_key, None)
    return _manifest_digest(digest_payload)


def _extension_unwrap_api_data(payload, expected_surface):
    if not isinstance(payload, dict):
        return payload
    if payload.get("surface") == expected_surface and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload


def _extension_bool(value):
    return bool(value) is True


def _authority(*args, **kwargs):
    original_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in _ORIGINAL_AUTHORITY_FOR_PRIMARY_RELAUNCH_PARAMETERS
    }
    authority = _ORIGINAL_AUTHORITY_FOR_PRIMARY_RELAUNCH(*args, **original_kwargs)
    primary_real_replacement = bool(
        kwargs.get(
            "update_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_performed",
            False,
        )
    )
    authority.update(
        {
            "updater_source_recovery_cleanup_proof_built": bool(
                kwargs.get("source_recovery_cleanup_proof_built", False)
            ),
            "updater_source_recovery_cleanup_recovery_artifacts_pinned": bool(
                kwargs.get("source_recovery_cleanup_recovery_artifacts_pinned", False)
            ),
            "updater_source_recovery_cleanup_normal_source_restored": bool(
                kwargs.get("source_recovery_cleanup_normal_source_restored", False)
            ),
            "updater_source_recovery_cleanup_final_closeout_blocked": bool(
                kwargs.get("source_recovery_cleanup_final_closeout_blocked", False)
            ),
            "updater_normal_source_restoration_readiness_built": bool(
                kwargs.get("normal_source_restoration_readiness_built", False)
            ),
            "updater_normal_source_restoration_ready": bool(
                kwargs.get("normal_source_restoration_ready", False)
            ),
            "updater_normal_source_restoration_candidates_available": bool(
                kwargs.get("normal_source_restoration_candidates_available", False)
            ),
            "updater_normal_source_restoration_final_closeout_blocked": bool(
                kwargs.get("normal_source_restoration_final_closeout_blocked", False)
            ),
            "updater_normal_source_candidate_verification_proof_built": bool(
                kwargs.get("normal_source_candidate_verification_proof_built", False)
            ),
            "updater_normal_source_candidate_verification_ready": bool(
                kwargs.get("normal_source_candidate_verification_ready", False)
            ),
            "updater_normal_source_candidate_verification_source_replacement_performed": bool(
                kwargs.get(
                    "normal_source_candidate_verification_source_replacement_performed",
                    False,
                )
            ),
            "updater_normal_source_candidate_verification_final_closeout_blocked": bool(
                kwargs.get(
                    "normal_source_candidate_verification_final_closeout_blocked",
                    False,
                )
            ),
            "updater_normal_source_candidate_restore_executor_proof_built": bool(
                kwargs.get("normal_source_candidate_restore_executor_proof_built", False)
            ),
            "updater_normal_source_candidate_restore_executor_ready": bool(
                kwargs.get("normal_source_candidate_restore_executor_ready", False)
            ),
            "updater_normal_source_candidate_restore_source_write_performed": bool(
                kwargs.get(
                    "normal_source_candidate_restore_source_write_performed",
                    False,
                )
            ),
            "updater_normal_source_candidate_restore_final_closeout_blocked": bool(
                kwargs.get(
                    "normal_source_candidate_restore_final_closeout_blocked",
                    False,
                )
            ),
            "updater_source_regeneration_readiness_built": bool(
                kwargs.get("source_regeneration_readiness_built", False)
            ),
            "updater_source_regeneration_tool_available": bool(
                kwargs.get("source_regeneration_tool_available", False)
            ),
            "updater_source_regeneration_execution_performed": bool(
                kwargs.get("source_regeneration_execution_performed", False)
            ),
            "updater_source_regeneration_final_closeout_blocked": bool(
                kwargs.get("source_regeneration_final_closeout_blocked", False)
            ),
            "updater_source_regeneration_runner_boundary_built": bool(
                kwargs.get("source_regeneration_runner_boundary_built", False)
            ),
            "updater_source_regeneration_runner_execution_performed": bool(
                kwargs.get("source_regeneration_runner_execution_performed", False)
            ),
            "updater_source_regeneration_candidate_write_performed": bool(
                kwargs.get("source_regeneration_candidate_write_performed", False)
            ),
            "updater_source_regeneration_live_source_write_performed": bool(
                kwargs.get("source_regeneration_live_source_write_performed", False)
            ),
            "updater_source_regeneration_runner_final_closeout_blocked": bool(
                kwargs.get("source_regeneration_runner_final_closeout_blocked", False)
            ),
            "updater_source_regeneration_candidate_restore_chain_built": bool(
                kwargs.get(
                    "source_regeneration_candidate_restore_chain_built",
                    False,
                )
            ),
            "updater_source_regeneration_candidate_verification_ready": bool(
                kwargs.get(
                    "source_regeneration_candidate_verification_ready",
                    False,
                )
            ),
            "updater_source_regeneration_candidate_restore_performed": bool(
                kwargs.get(
                    "source_regeneration_candidate_restore_performed",
                    False,
                )
            ),
            "updater_source_regeneration_candidate_live_source_write_performed": bool(
                kwargs.get(
                    "source_regeneration_candidate_live_source_write_performed",
                    False,
                )
            ),
            "updater_source_regeneration_candidate_restore_final_closeout_blocked": bool(
                kwargs.get(
                    "source_regeneration_candidate_restore_final_closeout_blocked",
                    False,
                )
            ),
            "updater_source_regeneration_live_source_restoration_closeout_built": bool(
                kwargs.get(
                    "source_regeneration_live_source_restoration_closeout_built",
                    False,
                )
            ),
            "updater_source_regeneration_live_source_restoration_verified": bool(
                kwargs.get(
                    "source_regeneration_live_source_restoration_verified",
                    False,
                )
            ),
            "updater_source_regeneration_live_source_wrappers_removed": bool(
                kwargs.get(
                    "source_regeneration_live_source_wrappers_removed",
                    False,
                )
            ),
            "updater_source_regeneration_live_source_closeout_source_write_performed": bool(
                kwargs.get(
                    "source_regeneration_live_source_closeout_source_write_performed",
                    False,
                )
            ),
            "updater_source_regeneration_live_source_closeout_final_closeout_blocked": bool(
                kwargs.get(
                    "source_regeneration_live_source_closeout_final_closeout_blocked",
                    False,
                )
            ),
            "updater_real_source_restoration_execution_regression_boundary_built": bool(
                kwargs.get(
                    "real_source_restoration_execution_regression_boundary_built",
                    False,
                )
            ),
            "updater_real_source_restoration_execution_performed": bool(
                kwargs.get("real_source_restoration_execution_performed", False)
            ),
            "updater_real_source_restoration_closeout_verified": bool(
                kwargs.get("real_source_restoration_closeout_verified", False)
            ),
            "updater_real_source_restoration_regression_evidence_verified": bool(
                kwargs.get(
                    "real_source_restoration_regression_evidence_verified",
                    False,
                )
            ),
            "updater_real_source_restoration_settings_write_control_exposed": bool(
                kwargs.get(
                    "real_source_restoration_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_real_source_restoration_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "real_source_restoration_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_real_source_restoration_final_closeout_blocked": bool(
                kwargs.get("real_source_restoration_final_closeout_blocked", False)
            ),
            "updater_current_vault_source_restoration_closeout_readiness_built": bool(
                kwargs.get(
                    "current_vault_source_restoration_closeout_readiness_built",
                    False,
                )
            ),
            "updater_current_vault_source_restoration_cleanup_ready": bool(
                kwargs.get("current_vault_source_restoration_cleanup_ready", False)
            ),
            "updater_current_vault_source_restoration_regression_boundary_verified": bool(
                kwargs.get(
                    "current_vault_source_restoration_regression_boundary_verified",
                    False,
                )
            ),
            "updater_current_vault_source_restoration_closeout_ready": bool(
                kwargs.get("current_vault_source_restoration_closeout_ready", False)
            ),
            "updater_current_vault_source_restoration_settings_write_control_exposed": bool(
                kwargs.get(
                    "current_vault_source_restoration_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_current_vault_source_restoration_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "current_vault_source_restoration_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_current_vault_source_restoration_final_closeout_blocked": bool(
                kwargs.get(
                    "current_vault_source_restoration_final_closeout_blocked",
                    False,
                )
            ),
            "updater_source_candidate_inventory_wrapper_removal_preflight_built": bool(
                kwargs.get(
                    "source_candidate_inventory_wrapper_removal_preflight_built",
                    False,
                )
            ),
            "updater_source_candidate_inventory_authoritative_candidates_available": bool(
                kwargs.get(
                    "source_candidate_inventory_authoritative_candidates_available",
                    False,
                )
            ),
            "updater_source_candidate_inventory_wrapper_removal_plan_ready": bool(
                kwargs.get(
                    "source_candidate_inventory_wrapper_removal_plan_ready",
                    False,
                )
            ),
            "updater_source_candidate_inventory_decompiler_execution_performed": bool(
                kwargs.get(
                    "source_candidate_inventory_decompiler_execution_performed",
                    False,
                )
            ),
            "updater_source_candidate_inventory_settings_write_control_exposed": bool(
                kwargs.get(
                    "source_candidate_inventory_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_source_candidate_inventory_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "source_candidate_inventory_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_source_candidate_inventory_final_closeout_blocked": bool(
                kwargs.get(
                    "source_candidate_inventory_final_closeout_blocked",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_packet_built": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_packet_built",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_candidates_available": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_candidates_available",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_ready_for_verifier": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_ready_for_verifier",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_operator_statement_matched": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_operator_statement_matched",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_source_write_performed": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_source_write_performed",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_settings_write_control_exposed": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_authoritative_normal_source_candidate_supply_final_closeout_blocked": bool(
                kwargs.get(
                    "authoritative_normal_source_candidate_supply_final_closeout_blocked",
                    False,
                )
            ),
            "updater_authoritative_source_candidate_import_boundary_built": bool(
                kwargs.get(
                    "authoritative_source_candidate_import_boundary_built",
                    False,
                )
            ),
            "updater_authoritative_source_candidate_import_plan_ready": bool(
                kwargs.get(
                    "authoritative_source_candidate_import_plan_ready",
                    False,
                )
            ),
            "updater_authoritative_source_candidate_import_statement_matched": bool(
                kwargs.get(
                    "authoritative_source_candidate_import_statement_matched",
                    False,
                )
            ),
            "updater_authoritative_source_candidate_import_candidate_write_performed": bool(
                kwargs.get(
                    "authoritative_source_candidate_import_candidate_write_performed",
                    False,
                )
            ),
            "updater_authoritative_source_candidate_import_settings_write_control_exposed": bool(
                kwargs.get(
                    "authoritative_source_candidate_import_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_authoritative_source_candidate_import_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "authoritative_source_candidate_import_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_authoritative_source_candidate_import_final_closeout_blocked": bool(
                kwargs.get(
                    "authoritative_source_candidate_import_final_closeout_blocked",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_readiness_built": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_readiness_built",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_candidates_available": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_candidates_available",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_ready_for_import_boundary": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_ready_for_import_boundary",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_source_write_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_source_write_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_candidate_import_write_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_candidate_import_write_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_settings_write_control_exposed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_supply_final_closeout_blocked": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_supply_final_closeout_blocked",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_built": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_built",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_plan_ready": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_plan_ready",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_statement_matched": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_statement_matched",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_source_materializer_execution_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_source_materializer_execution_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_candidate_write_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_candidate_write_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_ready_for_import_boundary": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_ready_for_import_boundary",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_source_write_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_source_write_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_candidate_import_write_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_candidate_import_write_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_settings_write_control_exposed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_materialization_final_closeout_blocked": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_materialization_final_closeout_blocked",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_built": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_built",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_plan_ready": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_plan_ready",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_statement_matched": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_statement_matched",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_candidate_import_write_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_candidate_import_write_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_ready_for_candidate_supply_approval": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_ready_for_candidate_supply_approval",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_source_write_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_source_write_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_settings_write_control_exposed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_real_authoritative_source_candidate_import_from_materialization_final_closeout_blocked": bool(
                kwargs.get(
                    "real_authoritative_source_candidate_import_from_materialization_final_closeout_blocked",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_built": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_built",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_boundary_verified": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_boundary_verified",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_supply_packet_ready": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_supply_packet_ready",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_candidate_verification_ready": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_candidate_verification_ready",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_ready_for_wrapper_removal_executor": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_ready_for_wrapper_removal_executor",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_source_write_performed": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_source_write_performed",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_settings_write_control_exposed": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_authoritative_candidate_supply_verification_after_import_final_closeout_blocked": bool(
                kwargs.get(
                    "authoritative_candidate_supply_verification_after_import_final_closeout_blocked",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_built": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_built",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_after_import_verified": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_after_import_verified",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_plan_ready": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_plan_ready",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_statement_matched": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_statement_matched",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_source_write_performed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_source_write_performed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_wrappers_removed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_wrappers_removed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_settings_write_control_exposed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_after_import_execution_final_closeout_blocked": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_after_import_execution_final_closeout_blocked",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_built": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_built",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_supply_verification_verified": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_supply_verification_verified",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_plan_ready": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_plan_ready",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_statement_matched": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_statement_matched",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_source_write_performed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_source_write_performed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_wrappers_removed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_wrappers_removed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_settings_write_control_exposed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_final_closeout_blocked": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_from_materialization_import_execution_final_closeout_blocked",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_built": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_built",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_wrapper_removal_verified": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_wrapper_removal_verified",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_evidence_verified": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_evidence_verified",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_statement_matched": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_statement_matched",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_commands_executed": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_commands_executed",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_source_write_performed": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_source_write_performed",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_settings_write_control_exposed": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_post_wrapper_removal_regression_from_materialization_import_final_closeout_blocked": bool(
                kwargs.get(
                    "post_wrapper_removal_regression_from_materialization_import_final_closeout_blocked",
                    False,
                )
            ),
            "updater_current_vault_source_closeout_from_materialization_import_regression_built": bool(
                kwargs.get(
                    "current_vault_source_closeout_from_materialization_import_regression_built",
                    False,
                )
            ),
            "updater_current_vault_source_closeout_from_materialization_import_regression_post_wrapper_regression_verified": bool(
                kwargs.get(
                    "current_vault_source_closeout_from_materialization_import_regression_post_wrapper_regression_verified",
                    False,
                )
            ),
            "updater_current_vault_source_closeout_from_materialization_import_regression_source_cleanup_ready": bool(
                kwargs.get(
                    "current_vault_source_closeout_from_materialization_import_regression_source_cleanup_ready",
                    False,
                )
            ),
            "updater_current_vault_source_closeout_from_materialization_import_regression_closeout_ready": bool(
                kwargs.get(
                    "current_vault_source_closeout_from_materialization_import_regression_closeout_ready",
                    False,
                )
            ),
            "updater_current_vault_source_closeout_from_materialization_import_regression_settings_write_control_exposed": bool(
                kwargs.get(
                    "current_vault_source_closeout_from_materialization_import_regression_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_current_vault_source_closeout_from_materialization_import_regression_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "current_vault_source_closeout_from_materialization_import_regression_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_current_vault_source_closeout_from_materialization_import_regression_final_closeout_blocked": bool(
                kwargs.get(
                    "current_vault_source_closeout_from_materialization_import_regression_final_closeout_blocked",
                    False,
                )
            ),
            "updater_production_primary_closeout_after_source_recovery_built": bool(
                kwargs.get(
                    "production_primary_closeout_after_source_recovery_built",
                    False,
                )
            ),
            "updater_production_primary_closeout_after_source_recovery_source_closeout_ready": bool(
                kwargs.get(
                    "production_primary_closeout_after_source_recovery_source_closeout_ready",
                    False,
                )
            ),
            "updater_production_primary_closeout_after_source_recovery_primary_relaunch_receipt_ready": bool(
                kwargs.get(
                    "production_primary_closeout_after_source_recovery_primary_relaunch_receipt_ready",
                    False,
                )
            ),
            "updater_production_primary_closeout_after_source_recovery_ready_for_final_closeout_audit": bool(
                kwargs.get(
                    "production_primary_closeout_after_source_recovery_ready_for_final_closeout_audit",
                    False,
                )
            ),
            "updater_production_primary_closeout_after_source_recovery_settings_write_control_exposed": bool(
                kwargs.get(
                    "production_primary_closeout_after_source_recovery_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_production_primary_closeout_after_source_recovery_primary_replacement_performed_by_chaseos": bool(
                kwargs.get(
                    "production_primary_closeout_after_source_recovery_primary_replacement_performed_by_chaseos",
                    False,
                )
            ),
            "updater_production_primary_closeout_after_source_recovery_production_auto_update_complete": bool(
                kwargs.get(
                    "production_primary_closeout_after_source_recovery_production_auto_update_complete",
                    False,
                )
            ),
            "updater_final_production_auto_update_closeout_audit_built": bool(
                kwargs.get("final_production_auto_update_closeout_audit_built", False)
            ),
            "updater_final_production_auto_update_closeout_audit_primary_closeout_ready": bool(
                kwargs.get(
                    "final_production_auto_update_closeout_audit_primary_closeout_ready",
                    False,
                )
            ),
            "updater_final_production_auto_update_closeout_audit_live_evidence_verified": bool(
                kwargs.get(
                    "final_production_auto_update_closeout_audit_live_evidence_verified",
                    False,
                )
            ),
            "updater_final_production_auto_update_closeout_audit_production_auto_update_complete": bool(
                kwargs.get(
                    "final_production_auto_update_closeout_audit_production_auto_update_complete",
                    False,
                )
            ),
            "updater_final_production_auto_update_closeout_audit_settings_install_control_exposed": bool(
                kwargs.get(
                    "final_production_auto_update_closeout_audit_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_final_production_auto_update_closeout_audit_helper_launch_performed_by_this_proof": bool(
                kwargs.get(
                    "final_production_auto_update_closeout_audit_helper_launch_performed_by_this_proof",
                    False,
                )
            ),
            "updater_final_production_auto_update_closeout_audit_primary_replacement_performed_by_this_proof": bool(
                kwargs.get(
                    "final_production_auto_update_closeout_audit_primary_replacement_performed_by_this_proof",
                    False,
                )
            ),
            "updater_governed_live_completion_evidence_packet_built": bool(
                kwargs.get("governed_live_completion_evidence_packet_built", False)
            ),
            "updater_governed_live_completion_evidence_packet_ready": bool(
                kwargs.get("governed_live_completion_evidence_packet_ready", False)
            ),
            "updater_governed_live_completion_evidence_packet_claims_verified": bool(
                kwargs.get(
                    "governed_live_completion_evidence_packet_claims_verified",
                    False,
                )
            ),
            "updater_governed_live_completion_evidence_packet_settings_install_control_exposed": bool(
                kwargs.get(
                    "governed_live_completion_evidence_packet_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_governed_live_completion_evidence_packet_helper_launch_performed_by_this_proof": bool(
                kwargs.get(
                    "governed_live_completion_evidence_packet_helper_launch_performed_by_this_proof",
                    False,
                )
            ),
            "updater_governed_live_completion_evidence_packet_primary_replacement_performed_by_this_proof": bool(
                kwargs.get(
                    "governed_live_completion_evidence_packet_primary_replacement_performed_by_this_proof",
                    False,
                )
            ),
            "updater_controlled_live_installer_evidence_runner_built": bool(
                kwargs.get("controlled_live_installer_evidence_runner_built", False)
            ),
            "updater_controlled_live_installer_evidence_runner_executed": bool(
                kwargs.get("controlled_live_installer_evidence_runner_executed", False)
            ),
            "updater_controlled_live_installer_evidence_runner_packet_ready": bool(
                kwargs.get(
                    "controlled_live_installer_evidence_runner_packet_ready",
                    False,
                )
            ),
            "updater_controlled_live_installer_evidence_runner_settings_install_control_exposed": bool(
                kwargs.get(
                    "controlled_live_installer_evidence_runner_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_controlled_live_installer_evidence_runner_primary_replacement_performed_by_runner": bool(
                kwargs.get(
                    "controlled_live_installer_evidence_runner_primary_replacement_performed_by_runner",
                    False,
                )
            ),
            "updater_approved_live_evidence_runner_adapter_built": bool(
                kwargs.get("approved_live_evidence_runner_adapter_built", False)
            ),
            "updater_approved_live_evidence_runner_adapter_ready": bool(
                kwargs.get("approved_live_evidence_runner_adapter_ready", False)
            ),
            "updater_approved_live_evidence_runner_adapter_controlled_packet_ready": bool(
                kwargs.get(
                    "approved_live_evidence_runner_adapter_controlled_packet_ready",
                    False,
                )
            ),
            "updater_approved_live_evidence_runner_adapter_settings_install_control_exposed": bool(
                kwargs.get(
                    "approved_live_evidence_runner_adapter_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_approved_live_evidence_runner_adapter_primary_replacement_performed_by_adapter": bool(
                kwargs.get(
                    "approved_live_evidence_runner_adapter_primary_replacement_performed_by_adapter",
                    False,
                )
            ),
            "updater_approved_live_evidence_runner_real_dry_run_built": bool(
                kwargs.get("approved_live_evidence_runner_real_dry_run_built", False)
            ),
            "updater_approved_live_evidence_runner_real_dry_run_source_proofs_checked": bool(
                kwargs.get(
                    "approved_live_evidence_runner_real_dry_run_source_proofs_checked",
                    False,
                )
            ),
            "updater_approved_live_evidence_runner_real_dry_run_adapter_packet_ready": bool(
                kwargs.get(
                    "approved_live_evidence_runner_real_dry_run_adapter_packet_ready",
                    False,
                )
            ),
            "updater_approved_live_evidence_runner_real_dry_run_final_audit_ready": bool(
                kwargs.get(
                    "approved_live_evidence_runner_real_dry_run_final_audit_ready",
                    False,
                )
            ),
            "updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed": bool(
                kwargs.get(
                    "approved_live_evidence_runner_real_dry_run_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_live_receipt_digest_consistency_closeout_built": bool(
                kwargs.get("live_receipt_digest_consistency_closeout_built", False)
            ),
            "updater_live_receipt_digest_consistency_closeout_ready": bool(
                kwargs.get("live_receipt_digest_consistency_closeout_ready", False)
            ),
            "updater_live_receipt_digest_consistency_closeout_normalized_blocked_receipts": bool(
                kwargs.get(
                    "live_receipt_digest_consistency_closeout_normalized_blocked_receipts",
                    False,
                )
            ),
            "updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed": bool(
                kwargs.get(
                    "live_receipt_digest_consistency_closeout_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_real_live_receipt_capture_boundary_built": bool(
                kwargs.get("real_live_receipt_capture_boundary_built", False)
            ),
            "updater_real_live_receipt_capture_boundary_ready": bool(
                kwargs.get("real_live_receipt_capture_boundary_ready", False)
            ),
            "updater_real_live_receipt_capture_boundary_receipt_bundle_valid": bool(
                kwargs.get(
                    "real_live_receipt_capture_boundary_receipt_bundle_valid",
                    False,
                )
            ),
            "updater_real_live_receipt_capture_boundary_source_receipts_ready": bool(
                kwargs.get(
                    "real_live_receipt_capture_boundary_source_receipts_ready",
                    False,
                )
            ),
            "updater_real_live_receipt_capture_boundary_dry_run_packet_ready": bool(
                kwargs.get(
                    "real_live_receipt_capture_boundary_dry_run_packet_ready",
                    False,
                )
            ),
            "updater_real_live_receipt_capture_boundary_settings_install_control_exposed": bool(
                kwargs.get(
                    "real_live_receipt_capture_boundary_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_real_live_receipt_bundle_production_runner_built": bool(
                kwargs.get("real_live_receipt_bundle_production_runner_built", False)
            ),
            "updater_real_live_receipt_bundle_production_runner_executed": bool(
                kwargs.get("real_live_receipt_bundle_production_runner_executed", False)
            ),
            "updater_real_live_receipt_bundle_production_runner_capture_boundary_ready": bool(
                kwargs.get(
                    "real_live_receipt_bundle_production_runner_capture_boundary_ready",
                    False,
                )
            ),
            "updater_real_live_receipt_bundle_production_runner_packet_ready": bool(
                kwargs.get(
                    "real_live_receipt_bundle_production_runner_packet_ready",
                    False,
                )
            ),
            "updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed": bool(
                kwargs.get(
                    "real_live_receipt_bundle_production_runner_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_real_live_receipt_bundle_production_runner_primary_replacement_performed_by_runner": bool(
                kwargs.get(
                    "real_live_receipt_bundle_production_runner_primary_replacement_performed_by_runner",
                    False,
                )
            ),
            "updater_production_runner_final_closeout_bridge_built": bool(
                kwargs.get("production_runner_final_closeout_bridge_built", False)
            ),
            "updater_production_runner_final_closeout_bridge_runner_ready": bool(
                kwargs.get("production_runner_final_closeout_bridge_runner_ready", False)
            ),
            "updater_production_runner_final_closeout_bridge_primary_closeout_ready": bool(
                kwargs.get(
                    "production_runner_final_closeout_bridge_primary_closeout_ready",
                    False,
                )
            ),
            "updater_production_runner_final_closeout_bridge_final_audit_ready": bool(
                kwargs.get(
                    "production_runner_final_closeout_bridge_final_audit_ready",
                    False,
                )
            ),
            "updater_production_runner_final_closeout_bridge_production_auto_update_complete": bool(
                kwargs.get(
                    "production_runner_final_closeout_bridge_production_auto_update_complete",
                    False,
                )
            ),
            "updater_production_runner_final_closeout_bridge_settings_install_control_exposed": bool(
                kwargs.get(
                    "production_runner_final_closeout_bridge_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_approved_production_runner_real_evidence_capture_built": bool(
                kwargs.get(
                    "approved_production_runner_real_evidence_capture_built",
                    False,
                )
            ),
            "updater_approved_production_runner_real_evidence_capture_files_read": bool(
                kwargs.get(
                    "approved_production_runner_real_evidence_capture_files_read",
                    False,
                )
            ),
            "updater_approved_production_runner_real_evidence_capture_bridge_ready": bool(
                kwargs.get(
                    "approved_production_runner_real_evidence_capture_bridge_ready",
                    False,
                )
            ),
            "updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed": bool(
                kwargs.get(
                    "approved_production_runner_real_evidence_capture_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_installer_real_artifact_build_output_capture_built": bool(
                kwargs.get(
                    "installer_real_artifact_build_output_capture_built",
                    False,
                )
            ),
            "updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact": bool(
                kwargs.get(
                    "installer_real_artifact_build_output_capture_reads_dist_installer_artifact",
                    False,
                )
            ),
            "updater_installer_real_artifact_build_output_capture_settings_install_control_exposed": bool(
                kwargs.get(
                    "installer_real_artifact_build_output_capture_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_dist_artifact_isolation_cohabitation_built": bool(
                kwargs.get("dist_artifact_isolation_cohabitation_built", False)
            ),
            "updater_dist_artifact_isolation_cohabitation_ready": bool(
                kwargs.get("dist_artifact_isolation_cohabitation_ready", False)
            ),
            "updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed": bool(
                kwargs.get(
                    "dist_artifact_isolation_cohabitation_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_signed_artifact_verification_closeout_built": bool(
                kwargs.get("signed_artifact_verification_closeout_built", False)
            ),
            "updater_signed_artifact_verification_closeout_ready": bool(
                kwargs.get("signed_artifact_verification_closeout_ready", False)
            ),
            "updater_signed_artifact_verification_closeout_signature_probe_performed": bool(
                kwargs.get(
                    "signed_artifact_verification_closeout_signature_probe_performed",
                    False,
                )
            ),
            "updater_signed_artifact_verification_closeout_settings_install_control_exposed": bool(
                kwargs.get(
                    "signed_artifact_verification_closeout_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_local_installer_disposable_dry_run_built": bool(
                kwargs.get("local_installer_disposable_dry_run_built", False)
            ),
            "updater_local_installer_disposable_dry_run_plan_valid": bool(
                kwargs.get("local_installer_disposable_dry_run_plan_valid", False)
            ),
            "updater_local_installer_disposable_dry_run_executed": bool(
                kwargs.get("local_installer_disposable_dry_run_executed", False)
            ),
            "updater_local_installer_disposable_dry_run_receipt_written": bool(
                kwargs.get("local_installer_disposable_dry_run_receipt_written", False)
            ),
            "updater_local_installer_disposable_dry_run_primary_install_mutation_performed": bool(
                kwargs.get(
                    "local_installer_disposable_dry_run_primary_install_mutation_performed",
                    False,
                )
            ),
            "updater_local_installer_disposable_dry_run_settings_install_control_exposed": bool(
                kwargs.get(
                    "local_installer_disposable_dry_run_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_local_manifest_background_prompt_built": bool(
                kwargs.get("local_manifest_background_prompt_built", False)
            ),
            "updater_local_manifest_background_prompt_manifest_checked": bool(
                kwargs.get(
                    "local_manifest_background_prompt_manifest_checked",
                    False,
                )
            ),
            "updater_local_manifest_background_prompt_update_available": bool(
                kwargs.get(
                    "local_manifest_background_prompt_update_available",
                    False,
                )
            ),
            "updater_local_manifest_background_prompt_installer_plan_ready": bool(
                kwargs.get(
                    "local_manifest_background_prompt_installer_plan_ready",
                    False,
                )
            ),
            "updater_local_manifest_background_prompt_settings_prompt_visible": bool(
                kwargs.get(
                    "local_manifest_background_prompt_settings_prompt_visible",
                    False,
                )
            ),
            "updater_local_manifest_background_prompt_settings_install_control_exposed": bool(
                kwargs.get(
                    "local_manifest_background_prompt_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_local_release_channel_blocker_closeout_built": bool(
                kwargs.get("local_release_channel_blocker_closeout_built", False)
            ),
            "updater_local_release_channel_blocker_closeout_local_ready": bool(
                kwargs.get("local_release_channel_blocker_closeout_local_ready", False)
            ),
            "updater_local_release_channel_blocker_closeout_only_external_blockers_remain": bool(
                kwargs.get(
                    "local_release_channel_blocker_closeout_only_external_blockers_remain",
                    False,
                )
            ),
            "updater_local_release_channel_blocker_closeout_settings_install_control_exposed": bool(
                kwargs.get(
                    "local_release_channel_blocker_closeout_settings_install_control_exposed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_executor_boundary_built": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_executor_boundary_built",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_executor_plan_ready": bool(
                kwargs.get("current_vault_wrapper_removal_executor_plan_ready", False)
            ),
            "updater_current_vault_wrapper_removal_executor_statement_matched": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_executor_statement_matched",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_executor_source_write_performed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_executor_source_write_performed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_executor_wrappers_removed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_executor_wrappers_removed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_executor_settings_write_control_exposed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_executor_settings_write_control_exposed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_executor_primary_real_exe_replacement_performed": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_executor_primary_real_exe_replacement_performed",
                    False,
                )
            ),
            "updater_current_vault_wrapper_removal_executor_final_closeout_blocked": bool(
                kwargs.get(
                    "current_vault_wrapper_removal_executor_final_closeout_blocked",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_built": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_built",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_ready": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_ready",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_statement_matched": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_statement_matched",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_receipt_valid": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_receipt_valid",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_external_helper_primary_relaunch_reported": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_external_helper_primary_relaunch_reported",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_performed": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_chaseos_relaunch_performed",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_primary_install_mutation_performed": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_primary_install_mutation_performed",
                    False,
                )
            ),
            "updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_performed": primary_real_replacement,
            "updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_verified_live": bool(
                kwargs.get(
                    "update_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_verified_live",
                    False,
                )
            ),
        }
    )
    authority["executable_replacement_performed"] = bool(
        authority.get("executable_replacement_performed") or primary_real_replacement
    )
    return authority


def _readiness():
    readiness = _ORIGINAL_READINESS_FOR_PRIMARY_RELAUNCH()
    readiness.update(
        {
            "updater_source_recovery_cleanup_proof_built": True,
            "updater_source_recovery_cleanup_recovery_bytecode_hash_pinning_enabled": True,
            "updater_source_recovery_cleanup_normal_source_restoration_required": True,
            "updater_source_recovery_cleanup_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_normal_source_restoration_readiness_proof_built": True,
            "updater_normal_source_restoration_readiness_default_enabled": False,
            "updater_normal_source_restoration_requires_launcher_update_check_source": True,
            "updater_normal_source_restoration_requires_studio_api_source": True,
            "updater_normal_source_restoration_requires_wrapper_removal": True,
            "updater_normal_source_restoration_requires_authoritative_candidate": True,
            "updater_normal_source_restoration_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_normal_source_candidate_verification_proof_built": True,
            "updater_normal_source_candidate_verification_default_enabled": False,
            "updater_normal_source_candidate_verification_requires_candidate_paths": True,
            "updater_normal_source_candidate_verification_requires_exact_operator_statement": True,
            "updater_normal_source_candidate_verification_parses_ast_only": True,
            "updater_normal_source_candidate_verification_source_write_enabled": False,
            "updater_normal_source_candidate_verification_source_replacement_enabled": False,
            "updater_normal_source_candidate_verification_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_normal_source_candidate_restore_executor_proof_built": True,
            "updater_normal_source_candidate_restore_executor_default_enabled": False,
            "updater_normal_source_candidate_restore_executor_requires_verified_candidates": True,
            "updater_normal_source_candidate_restore_executor_requires_restore_root": True,
            "updater_normal_source_candidate_restore_executor_requires_exact_operator_statement": True,
            "updater_normal_source_candidate_restore_executor_rechecks_candidate_hashes": True,
            "updater_normal_source_candidate_restore_executor_source_write_enabled_with_explicit_approval": True,
            "updater_normal_source_candidate_restore_executor_settings_write_control_exposed": False,
            "updater_normal_source_candidate_restore_executor_decompiler_enabled": False,
            "updater_normal_source_candidate_restore_executor_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_source_regeneration_readiness_proof_built": True,
            "updater_source_regeneration_readiness_default_enabled": False,
            "updater_source_regeneration_requires_bytecode_artifact_hash_pinning": True,
            "updater_source_regeneration_requires_local_decompiler_or_operator_source": True,
            "updater_source_regeneration_decompiler_execution_enabled": False,
            "updater_source_regeneration_source_write_enabled": False,
            "updater_source_regeneration_settings_write_control_exposed": False,
            "updater_source_regeneration_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_source_regeneration_runner_boundary_proof_built": True,
            "updater_source_regeneration_runner_boundary_default_enabled": False,
            "updater_source_regeneration_runner_requires_readiness_proof": True,
            "updater_source_regeneration_runner_requires_injected_runner": True,
            "updater_source_regeneration_runner_requires_output_root": True,
            "updater_source_regeneration_runner_requires_exact_operator_statement": True,
            "updater_source_regeneration_runner_candidate_writes_enabled_with_explicit_approval": True,
            "updater_source_regeneration_runner_live_source_write_enabled": False,
            "updater_source_regeneration_runner_settings_write_control_exposed": False,
            "updater_source_regeneration_runner_primary_real_exe_replacement_enabled": False,
            "updater_source_regeneration_runner_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_source_regeneration_candidate_restore_chain_proof_built": True,
            "updater_source_regeneration_candidate_restore_chain_default_enabled": False,
            "updater_source_regeneration_candidate_restore_chain_requires_runner_boundary": True,
            "updater_source_regeneration_candidate_restore_chain_requires_candidate_verification_statement": True,
            "updater_source_regeneration_candidate_restore_chain_requires_restore_root": True,
            "updater_source_regeneration_candidate_restore_chain_requires_restore_statement": True,
            "updater_source_regeneration_candidate_restore_chain_fixture_restore_enabled_with_explicit_approval": True,
            "updater_source_regeneration_candidate_restore_chain_live_source_write_enabled_with_explicit_approval": True,
            "updater_source_regeneration_candidate_restore_chain_settings_write_control_exposed": False,
            "updater_source_regeneration_candidate_restore_chain_primary_real_exe_replacement_enabled": False,
            "updater_source_regeneration_candidate_restore_chain_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_source_regeneration_live_source_restoration_closeout_proof_built": True,
            "updater_source_regeneration_live_source_restoration_closeout_default_enabled": False,
            "updater_source_regeneration_live_source_restoration_closeout_requires_live_restore_proof": True,
            "updater_source_regeneration_live_source_restoration_closeout_rechecks_restore_digest": True,
            "updater_source_regeneration_live_source_restoration_closeout_scans_wrapper_tokens": True,
            "updater_source_regeneration_live_source_restoration_closeout_read_only": True,
            "updater_source_regeneration_live_source_restoration_closeout_settings_write_control_exposed": False,
            "updater_source_regeneration_live_source_restoration_closeout_primary_real_exe_replacement_enabled": False,
            "updater_source_regeneration_live_source_restoration_closeout_final_auto_update_closeout_blocked_until_primary_exe_replaced": True,
            "updater_real_source_restoration_execution_regression_boundary_proof_built": True,
            "updater_real_source_restoration_execution_regression_boundary_default_enabled": False,
            "updater_real_source_restoration_execution_requires_generated_restore_proof": True,
            "updater_real_source_restoration_execution_requires_explicit_restore_root": True,
            "updater_real_source_restoration_execution_can_write_only_with_existing_exact_approvals": True,
            "updater_real_source_restoration_execution_rechecks_restore_digest": True,
            "updater_real_source_restoration_execution_rechecks_closeout_digest": True,
            "updater_real_source_restoration_execution_requires_regression_evidence": True,
            "updater_real_source_restoration_execution_runs_regression_commands": False,
            "updater_real_source_restoration_execution_settings_write_control_exposed": False,
            "updater_real_source_restoration_execution_primary_real_exe_replacement_enabled": False,
            "updater_real_source_restoration_execution_final_auto_update_closeout_blocked_until_primary_exe_replaced": True,
            "updater_current_vault_source_restoration_closeout_readiness_proof_built": True,
            "updater_current_vault_source_restoration_closeout_default_enabled": False,
            "updater_current_vault_source_restoration_closeout_requires_source_cleanup_ready": True,
            "updater_current_vault_source_restoration_closeout_requires_wrapper_removal": True,
            "updater_current_vault_source_restoration_closeout_requires_regression_boundary": True,
            "updater_current_vault_source_restoration_closeout_rechecks_source_cleanup_digest": True,
            "updater_current_vault_source_restoration_closeout_rechecks_regression_boundary_digest": True,
            "updater_current_vault_source_restoration_closeout_settings_write_control_exposed": False,
            "updater_current_vault_source_restoration_closeout_primary_real_exe_replacement_enabled": False,
            "updater_current_vault_source_restoration_closeout_final_auto_update_closeout_blocked_until_primary_exe_replaced": True,
            "updater_source_candidate_inventory_wrapper_removal_preflight_proof_built": True,
            "updater_source_candidate_inventory_wrapper_removal_preflight_default_enabled": False,
            "updater_source_candidate_inventory_scans_current_vault_sources": True,
            "updater_source_candidate_inventory_scans_build_lib_candidates": True,
            "updater_source_candidate_inventory_scans_recovery_bytecode_artifacts": True,
            "updater_source_candidate_inventory_requires_authoritative_candidates": True,
            "updater_source_candidate_inventory_requires_wrapper_removal": True,
            "updater_source_candidate_inventory_decompiler_execution_enabled": False,
            "updater_source_candidate_inventory_source_write_enabled": False,
            "updater_source_candidate_inventory_wrapper_removal_enabled": False,
            "updater_source_candidate_inventory_settings_write_control_exposed": False,
            "updater_source_candidate_inventory_primary_real_exe_replacement_enabled": False,
            "updater_source_candidate_inventory_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_authoritative_normal_source_candidate_supply_packet_built": True,
            "updater_authoritative_normal_source_candidate_supply_default_enabled": False,
            "updater_authoritative_normal_source_candidate_supply_requires_inventory_preflight": True,
            "updater_authoritative_normal_source_candidate_supply_requires_candidate_files_inside_vault": True,
            "updater_authoritative_normal_source_candidate_supply_requires_required_symbols": True,
            "updater_authoritative_normal_source_candidate_supply_rejects_recovery_wrappers": True,
            "updater_authoritative_normal_source_candidate_supply_requires_exact_operator_statement": True,
            "updater_authoritative_normal_source_candidate_supply_source_write_enabled": False,
            "updater_authoritative_normal_source_candidate_supply_decompiler_execution_enabled": False,
            "updater_authoritative_normal_source_candidate_supply_wrapper_removal_enabled": False,
            "updater_authoritative_normal_source_candidate_supply_settings_write_control_exposed": False,
            "updater_authoritative_normal_source_candidate_supply_primary_real_exe_replacement_enabled": False,
            "updater_authoritative_normal_source_candidate_supply_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_authoritative_source_candidate_import_boundary_proof_built": True,
            "updater_authoritative_source_candidate_import_default_enabled": False,
            "updater_authoritative_source_candidate_import_requires_import_candidate_paths": True,
            "updater_authoritative_source_candidate_import_requires_target_candidate_root_inside_vault": True,
            "updater_authoritative_source_candidate_import_requires_required_symbols": True,
            "updater_authoritative_source_candidate_import_rejects_recovery_wrappers": True,
            "updater_authoritative_source_candidate_import_requires_exact_operator_statement": True,
            "updater_authoritative_source_candidate_import_requires_explicit_candidate_write_flag": True,
            "updater_authoritative_source_candidate_import_candidate_write_enabled_with_explicit_approval": True,
            "updater_authoritative_source_candidate_import_source_write_enabled": False,
            "updater_authoritative_source_candidate_import_wrapper_removal_enabled": False,
            "updater_authoritative_source_candidate_import_decompiler_execution_enabled": False,
            "updater_authoritative_source_candidate_import_settings_write_control_exposed": False,
            "updater_authoritative_source_candidate_import_primary_real_exe_replacement_enabled": False,
            "updater_authoritative_source_candidate_import_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_real_authoritative_source_candidate_supply_readiness_proof_built": True,
            "updater_real_authoritative_source_candidate_supply_default_enabled": False,
            "updater_real_authoritative_source_candidate_supply_scans_configured_roots": True,
            "updater_real_authoritative_source_candidate_supply_requires_wrapper_free_candidates": True,
            "updater_real_authoritative_source_candidate_supply_rejects_current_live_sources": True,
            "updater_real_authoritative_source_candidate_supply_prepares_import_boundary": True,
            "updater_real_authoritative_source_candidate_supply_candidate_import_write_enabled": False,
            "updater_real_authoritative_source_candidate_supply_source_write_enabled": False,
            "updater_real_authoritative_source_candidate_supply_wrapper_removal_enabled": False,
            "updater_real_authoritative_source_candidate_supply_decompiler_execution_enabled": False,
            "updater_real_authoritative_source_candidate_supply_settings_write_control_exposed": False,
            "updater_real_authoritative_source_candidate_supply_primary_real_exe_replacement_enabled": False,
            "updater_real_authoritative_source_candidate_supply_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_real_authoritative_source_candidate_materialization_proof_built": True,
            "updater_real_authoritative_source_candidate_materialization_default_enabled": False,
            "updater_real_authoritative_source_candidate_materialization_requires_supply_readiness": True,
            "updater_real_authoritative_source_candidate_materialization_requires_source_regeneration_readiness": True,
            "updater_real_authoritative_source_candidate_materialization_requires_injected_source_materializer": True,
            "updater_real_authoritative_source_candidate_materialization_requires_exact_operator_statement": True,
            "updater_real_authoritative_source_candidate_materialization_requires_explicit_candidate_write_flag": True,
            "updater_real_authoritative_source_candidate_materialization_candidate_writes_enabled_with_explicit_approval": True,
            "updater_real_authoritative_source_candidate_materialization_candidate_import_write_enabled": False,
            "updater_real_authoritative_source_candidate_materialization_source_write_enabled": False,
            "updater_real_authoritative_source_candidate_materialization_decompiler_execution_enabled": False,
            "updater_real_authoritative_source_candidate_materialization_candidate_source_execution_enabled": False,
            "updater_real_authoritative_source_candidate_materialization_settings_write_control_exposed": False,
            "updater_real_authoritative_source_candidate_materialization_primary_real_exe_replacement_enabled": False,
            "updater_real_authoritative_source_candidate_materialization_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_proof_built": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_default_enabled": False,
            "updater_real_authoritative_source_candidate_import_from_materialization_requires_materialization_proof": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_rechecks_materialization_digest": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_revalidates_materialized_candidate_hashes": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_requires_exact_operator_statement": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_requires_explicit_candidate_import_write_flag": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_candidate_import_write_enabled_with_explicit_approval": True,
            "updater_real_authoritative_source_candidate_import_from_materialization_source_write_enabled": False,
            "updater_real_authoritative_source_candidate_import_from_materialization_decompiler_execution_enabled": False,
            "updater_real_authoritative_source_candidate_import_from_materialization_candidate_source_execution_enabled": False,
            "updater_real_authoritative_source_candidate_import_from_materialization_settings_write_control_exposed": False,
            "updater_real_authoritative_source_candidate_import_from_materialization_primary_real_exe_replacement_enabled": False,
            "updater_real_authoritative_source_candidate_import_from_materialization_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof_built": True,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_default_enabled": False,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_import_from_materialization_proof": True,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_rechecks_import_from_materialization_digest": True,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_reuses_after_import_verifier": True,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_requires_exact_operator_statement": True,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_source_write_enabled": False,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_decompiler_execution_enabled": False,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_candidate_source_execution_enabled": False,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_settings_write_control_exposed": False,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_primary_real_exe_replacement_enabled": False,
            "updater_real_authoritative_source_candidate_supply_verification_from_materialization_import_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_proof_built": True,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_default_enabled": False,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_supply_verification_from_materialization_import_proof": True,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_rechecks_supply_verification_from_materialization_import_digest": True,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_reuses_after_import_wrapper_removal_executor": True,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_exact_operator_statement": True,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_requires_explicit_source_write_flag": True,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_source_write_enabled": False,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_decompiler_execution_enabled": False,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_candidate_source_execution_enabled": False,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_settings_write_control_exposed": False,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_primary_real_exe_replacement_enabled": False,
            "updater_current_vault_wrapper_removal_from_materialization_import_execution_final_auto_update_closeout_blocked_until_regression": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_proof_built": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_default_enabled": False,
            "updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_from_materialization_import_execution_proof": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_rechecks_wrapper_removal_from_materialization_import_execution_digest": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_requires_wrapper_removal_performed": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_requires_supplied_regression_evidence": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_does_not_execute_regression_commands": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_requires_exact_operator_statement": True,
            "updater_post_wrapper_removal_regression_from_materialization_import_source_write_enabled": False,
            "updater_post_wrapper_removal_regression_from_materialization_import_decompiler_execution_enabled": False,
            "updater_post_wrapper_removal_regression_from_materialization_import_candidate_source_execution_enabled": False,
            "updater_post_wrapper_removal_regression_from_materialization_import_settings_write_control_exposed": False,
            "updater_post_wrapper_removal_regression_from_materialization_import_primary_real_exe_replacement_enabled": False,
            "updater_post_wrapper_removal_regression_from_materialization_import_final_auto_update_closeout_blocked_until_source_closeout": True,
            "updater_current_vault_source_closeout_from_materialization_import_regression_proof_built": True,
            "updater_current_vault_source_closeout_from_materialization_import_regression_default_enabled": False,
            "updater_current_vault_source_closeout_from_materialization_import_regression_requires_post_wrapper_removal_regression_from_materialization_import_proof": True,
            "updater_current_vault_source_closeout_from_materialization_import_regression_rechecks_post_wrapper_removal_regression_digest": True,
            "updater_current_vault_source_closeout_from_materialization_import_regression_requires_source_cleanup_ready": True,
            "updater_current_vault_source_closeout_from_materialization_import_regression_requires_wrapper_free_current_vault_sources": True,
            "updater_current_vault_source_closeout_from_materialization_import_regression_read_only": True,
            "updater_current_vault_source_closeout_from_materialization_import_regression_settings_write_control_exposed": False,
            "updater_current_vault_source_closeout_from_materialization_import_regression_primary_real_exe_replacement_enabled": False,
            "updater_current_vault_source_closeout_from_materialization_import_regression_final_auto_update_closeout_blocked_until_primary_exe_replaced": True,
            "updater_production_primary_closeout_after_source_recovery_proof_built": True,
            "updater_production_primary_closeout_after_source_recovery_default_enabled": False,
            "updater_production_primary_closeout_after_source_recovery_requires_current_vault_source_closeout": True,
            "updater_production_primary_closeout_after_source_recovery_rechecks_source_closeout_digest": True,
            "updater_production_primary_closeout_after_source_recovery_requires_primary_relaunch_receipt_boundary": True,
            "updater_production_primary_closeout_after_source_recovery_rechecks_primary_relaunch_receipt_boundary_digest": True,
            "updater_production_primary_closeout_after_source_recovery_requires_external_chaseos_installer_primary_relaunch_receipt": True,
            "updater_production_primary_closeout_after_source_recovery_source_write_enabled": False,
            "updater_production_primary_closeout_after_source_recovery_helper_launch_enabled": False,
            "updater_production_primary_closeout_after_source_recovery_primary_real_exe_replacement_enabled": False,
            "updater_production_primary_closeout_after_source_recovery_settings_install_control_exposed": False,
            "updater_production_primary_closeout_after_source_recovery_production_auto_update_complete": False,
            "updater_production_primary_closeout_after_source_recovery_final_auto_update_closeout_blocked_until_live_primary_audit": True,
            "updater_final_production_auto_update_closeout_audit_proof_built": True,
            "updater_final_production_auto_update_closeout_audit_default_enabled": False,
            "updater_final_production_auto_update_closeout_audit_requires_production_primary_closeout_after_source_recovery": True,
            "updater_final_production_auto_update_closeout_audit_rechecks_primary_closeout_digest": True,
            "updater_final_production_auto_update_closeout_audit_requires_live_completion_evidence": True,
            "updater_final_production_auto_update_closeout_audit_rechecks_live_evidence_digest": True,
            "updater_final_production_auto_update_closeout_audit_requires_github_release_publication_verified": True,
            "updater_final_production_auto_update_closeout_audit_requires_live_manifest_readback_verified": True,
            "updater_final_production_auto_update_closeout_audit_requires_signed_download_and_signature_verification": True,
            "updater_final_production_auto_update_closeout_audit_requires_chaseos_installer_signed_verified": True,
            "updater_final_production_auto_update_closeout_audit_requires_chaseos_installer_launch_receipt": True,
            "updater_final_production_auto_update_closeout_audit_requires_primary_replacement_verified_live": True,
            "updater_final_production_auto_update_closeout_audit_requires_primary_relaunch_verified_live": True,
            "updater_final_production_auto_update_closeout_audit_requires_startup_background_prompt_verified": True,
            "updater_final_production_auto_update_closeout_audit_read_only": True,
            "updater_final_production_auto_update_closeout_audit_helper_launch_enabled_by_this_proof": False,
            "updater_final_production_auto_update_closeout_audit_primary_real_exe_replacement_enabled_by_this_proof": False,
            "updater_final_production_auto_update_closeout_audit_settings_install_control_exposed": False,
            "updater_final_production_auto_update_closeout_audit_production_auto_update_complete_default": False,
            "updater_governed_live_completion_evidence_packet_proof_built": True,
            "updater_governed_live_completion_evidence_packet_default_enabled": False,
            "updater_governed_live_completion_evidence_packet_requires_live_claims": True,
            "updater_governed_live_completion_evidence_packet_requires_all_final_audit_true_claims": True,
            "updater_governed_live_completion_evidence_packet_requires_all_final_audit_false_claims": True,
            "updater_governed_live_completion_evidence_packet_requires_exact_operator_statement": True,
            "updater_governed_live_completion_evidence_packet_rechecks_live_evidence_digest": True,
            "updater_governed_live_completion_evidence_packet_feeds_final_closeout_audit": True,
            "updater_governed_live_completion_evidence_packet_read_only": True,
            "updater_governed_live_completion_evidence_packet_source_write_enabled": False,
            "updater_governed_live_completion_evidence_packet_github_mutation_enabled": False,
            "updater_governed_live_completion_evidence_packet_download_enabled": False,
            "updater_governed_live_completion_evidence_packet_helper_launch_enabled": False,
            "updater_governed_live_completion_evidence_packet_primary_real_exe_replacement_enabled": False,
            "updater_governed_live_completion_evidence_packet_settings_install_control_exposed": False,
            "updater_governed_live_completion_evidence_packet_production_auto_update_complete_default": False,
            "updater_governed_live_completion_evidence_packet_final_auto_update_closeout_blocked_until_final_audit_consumes_packet": True,
            "updater_controlled_live_installer_evidence_runner_proof_built": True,
            "updater_controlled_live_installer_evidence_runner_default_enabled": False,
            "updater_controlled_live_installer_evidence_runner_requires_injected_runner": True,
            "updater_controlled_live_installer_evidence_runner_requires_exact_operator_statement": True,
            "updater_controlled_live_installer_evidence_runner_requires_live_release_readback_approval": True,
            "updater_controlled_live_installer_evidence_runner_requires_live_download_approval": True,
            "updater_controlled_live_installer_evidence_runner_requires_installer_launch_approval": True,
            "updater_controlled_live_installer_evidence_runner_requires_primary_replacement_approval": True,
            "updater_controlled_live_installer_evidence_runner_requires_startup_prompt_verification_approval": True,
            "updater_controlled_live_installer_evidence_runner_sanitizes_runner_receipt": True,
            "updater_controlled_live_installer_evidence_runner_builds_governed_evidence_packet": True,
            "updater_controlled_live_installer_evidence_runner_rechecks_packet_digest": True,
            "updater_controlled_live_installer_evidence_runner_settings_install_control_exposed": False,
            "updater_controlled_live_installer_evidence_runner_source_write_enabled": False,
            "updater_controlled_live_installer_evidence_runner_default_live_download_enabled": False,
            "updater_controlled_live_installer_evidence_runner_default_installer_launch_enabled": False,
            "updater_controlled_live_installer_evidence_runner_default_primary_replacement_enabled": False,
            "updater_controlled_live_installer_evidence_runner_production_auto_update_complete_default": False,
            "updater_controlled_live_installer_evidence_runner_final_auto_update_closeout_blocked_until_final_audit": True,
            "updater_approved_live_evidence_runner_adapter_proof_built": True,
            "updater_approved_live_evidence_runner_adapter_default_enabled": False,
            "updater_approved_live_evidence_runner_adapter_requires_signed_manifest_live_readback": True,
            "updater_approved_live_evidence_runner_adapter_requires_live_download_staging": True,
            "updater_approved_live_evidence_runner_adapter_requires_downloaded_staged_signature_verification": True,
            "updater_approved_live_evidence_runner_adapter_requires_installer_signed_output_verification": True,
            "updater_approved_live_evidence_runner_adapter_requires_primary_relaunch_receipt_boundary": True,
            "updater_approved_live_evidence_runner_adapter_requires_startup_background_prompt": True,
            "updater_approved_live_evidence_runner_adapter_requires_startup_background_prompt_verification": True,
            "updater_approved_live_evidence_runner_adapter_requires_exact_operator_statement": True,
            "updater_approved_live_evidence_runner_adapter_rechecks_source_digests": True,
            "updater_approved_live_evidence_runner_adapter_adapts_to_controlled_live_installer_evidence_runner": True,
            "updater_approved_live_evidence_runner_adapter_builds_controlled_runner_receipt": True,
            "updater_approved_live_evidence_runner_adapter_builds_governed_evidence_packet": True,
            "updater_approved_live_evidence_runner_adapter_settings_install_control_exposed": False,
            "updater_approved_live_evidence_runner_adapter_live_download_enabled_by_default": False,
            "updater_approved_live_evidence_runner_adapter_installer_launch_enabled_by_default": False,
            "updater_approved_live_evidence_runner_adapter_primary_replacement_enabled_by_default": False,
            "updater_approved_live_evidence_runner_adapter_download_performed_by_adapter": False,
            "updater_approved_live_evidence_runner_adapter_installer_launch_performed_by_adapter": False,
            "updater_approved_live_evidence_runner_adapter_primary_real_exe_replacement_performed_by_adapter": False,
            "updater_approved_live_evidence_runner_adapter_production_auto_update_complete_default": False,
            "updater_approved_live_evidence_runner_real_dry_run_proof_built": True,
            "updater_approved_live_evidence_runner_real_dry_run_default_enabled": False,
            "updater_approved_live_evidence_runner_real_dry_run_collects_current_vault_source_proofs": True,
            "updater_approved_live_evidence_runner_real_dry_run_requires_source_proof_readiness": True,
            "updater_approved_live_evidence_runner_real_dry_run_requires_exact_operator_statement": True,
            "updater_approved_live_evidence_runner_real_dry_run_adapts_to_approved_live_evidence_runner_adapter": True,
            "updater_approved_live_evidence_runner_real_dry_run_can_preview_final_audit": True,
            "updater_approved_live_evidence_runner_real_dry_run_download_performed_by_dry_run": False,
            "updater_approved_live_evidence_runner_real_dry_run_installer_launch_performed_by_dry_run": False,
            "updater_approved_live_evidence_runner_real_dry_run_primary_real_exe_replacement_performed_by_dry_run": False,
            "updater_approved_live_evidence_runner_real_dry_run_settings_install_control_exposed": False,
            "updater_approved_live_evidence_runner_real_dry_run_production_auto_update_complete_default": False,
            "updater_live_receipt_digest_consistency_closeout_proof_built": True,
            "updater_live_receipt_digest_consistency_closeout_default_enabled": False,
            "updater_live_receipt_digest_consistency_closeout_collects_current_vault_source_proofs": True,
            "updater_live_receipt_digest_consistency_closeout_normalizes_blocked_receipt_digests_only": True,
            "updater_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch": True,
            "updater_live_receipt_digest_consistency_closeout_download_performed": False,
            "updater_live_receipt_digest_consistency_closeout_installer_launch_performed": False,
            "updater_live_receipt_digest_consistency_closeout_primary_real_exe_replacement_performed": False,
            "updater_live_receipt_digest_consistency_closeout_settings_install_control_exposed": False,
            "updater_live_receipt_digest_consistency_closeout_production_auto_update_complete_default": False,
            "updater_real_live_receipt_capture_boundary_proof_built": True,
            "updater_real_live_receipt_capture_boundary_default_enabled": False,
            "updater_real_live_receipt_capture_boundary_requires_external_receipt_bundle": True,
            "updater_real_live_receipt_capture_boundary_requires_all_six_source_receipts": True,
            "updater_real_live_receipt_capture_boundary_rechecks_bundle_digest": True,
            "updater_real_live_receipt_capture_boundary_rechecks_source_receipt_digests": True,
            "updater_real_live_receipt_capture_boundary_rejects_ready_digest_mismatch": True,
            "updater_real_live_receipt_capture_boundary_feeds_approved_real_dry_run": True,
            "updater_real_live_receipt_capture_boundary_download_performed": False,
            "updater_real_live_receipt_capture_boundary_installer_launch_performed": False,
            "updater_real_live_receipt_capture_boundary_primary_real_exe_replacement_performed": False,
            "updater_real_live_receipt_capture_boundary_settings_install_control_exposed": False,
            "updater_real_live_receipt_capture_boundary_production_auto_update_complete_default": False,
            "updater_real_live_receipt_bundle_production_runner_proof_built": True,
            "updater_real_live_receipt_bundle_production_runner_default_enabled": False,
            "updater_real_live_receipt_bundle_production_runner_requires_injected_runner": True,
            "updater_real_live_receipt_bundle_production_runner_requires_exact_operator_statement": True,
            "updater_real_live_receipt_bundle_production_runner_requires_live_action_approvals": True,
            "updater_real_live_receipt_bundle_production_runner_produces_external_receipt_bundle": True,
            "updater_real_live_receipt_bundle_production_runner_feeds_capture_boundary": True,
            "updater_real_live_receipt_bundle_production_runner_feeds_real_live_receipt_capture_boundary": True,
            "updater_real_live_receipt_bundle_production_runner_default_live_download_enabled": False,
            "updater_real_live_receipt_bundle_production_runner_download_enabled_by_default": False,
            "updater_real_live_receipt_bundle_production_runner_default_installer_launch_enabled": False,
            "updater_real_live_receipt_bundle_production_runner_installer_launch_enabled_by_default": False,
            "updater_real_live_receipt_bundle_production_runner_default_primary_replacement_enabled": False,
            "updater_real_live_receipt_bundle_production_runner_primary_replacement_enabled_by_default": False,
            "updater_real_live_receipt_bundle_production_runner_settings_install_control_exposed": False,
            "updater_real_live_receipt_bundle_production_runner_production_auto_update_complete_default": False,
            "updater_production_runner_final_closeout_bridge_proof_built": True,
            "updater_production_runner_final_closeout_bridge_default_enabled": False,
            "updater_production_runner_final_closeout_bridge_requires_ready_production_runner_proof": True,
            "updater_production_runner_final_closeout_bridge_requires_primary_closeout_after_source_recovery": True,
            "updater_production_runner_final_closeout_bridge_rechecks_runner_digest": True,
            "updater_production_runner_final_closeout_bridge_rechecks_governed_packet_digest": True,
            "updater_production_runner_final_closeout_bridge_feeds_final_closeout_audit": True,
            "updater_production_runner_final_closeout_bridge_executes_runner_by_default": False,
            "updater_production_runner_final_closeout_bridge_download_enabled_by_default": False,
            "updater_production_runner_final_closeout_bridge_installer_launch_enabled_by_default": False,
            "updater_production_runner_final_closeout_bridge_primary_replacement_enabled_by_default": False,
            "updater_production_runner_final_closeout_bridge_settings_install_control_exposed": False,
            "updater_production_runner_final_closeout_bridge_production_auto_update_complete_default": False,
            "updater_approved_production_runner_real_evidence_capture_proof_built": True,
            "updater_approved_production_runner_real_evidence_capture_default_enabled": False,
            "updater_approved_production_runner_real_evidence_capture_requires_in_vault_evidence_root": True,
            "updater_approved_production_runner_real_evidence_capture_requires_exact_operator_statement": True,
            "updater_approved_production_runner_real_evidence_capture_requires_explicit_file_read_flag": True,
            "updater_approved_production_runner_real_evidence_capture_reads_json_evidence_only": True,
            "updater_approved_production_runner_real_evidence_capture_rechecks_runner_digest": True,
            "updater_approved_production_runner_real_evidence_capture_rechecks_primary_closeout_digest": True,
            "updater_approved_production_runner_real_evidence_capture_feeds_final_closeout_bridge": True,
            "updater_approved_production_runner_real_evidence_capture_executes_runner_by_default": False,
            "updater_approved_production_runner_real_evidence_capture_download_enabled_by_default": False,
            "updater_approved_production_runner_real_evidence_capture_installer_launch_enabled_by_default": False,
            "updater_approved_production_runner_real_evidence_capture_primary_replacement_enabled_by_default": False,
            "updater_approved_production_runner_real_evidence_capture_settings_install_control_exposed": False,
            "updater_approved_production_runner_real_evidence_capture_production_auto_update_complete_default": False,
            "updater_installer_real_artifact_build_output_capture_built": True,
            "updater_installer_real_artifact_build_output_capture_reads_dist_installer_artifact": True,
            "updater_installer_real_artifact_build_output_capture_requires_exact_installer_name": True,
            "updater_installer_real_artifact_build_output_capture_requires_build_script_studio_hash_guard": True,
            "updater_installer_real_artifact_build_output_capture_signature_probe_required_for_signed_output": True,
            "updater_installer_real_artifact_build_output_capture_download_enabled_by_default": False,
            "updater_installer_real_artifact_build_output_capture_installer_launch_enabled_by_default": False,
            "updater_installer_real_artifact_build_output_capture_primary_replacement_enabled_by_default": False,
            "updater_installer_real_artifact_build_output_capture_settings_install_control_exposed": False,
            "updater_installer_real_artifact_build_output_capture_production_auto_update_complete_default": False,
            "updater_dist_artifact_isolation_cohabitation_proof_built": True,
            "updater_dist_artifact_isolation_cohabitation_requires_both_artifacts": True,
            "updater_dist_artifact_isolation_cohabitation_requires_isolated_studio_dist": True,
            "updater_dist_artifact_isolation_cohabitation_requires_isolated_installer_dist": True,
            "updater_dist_artifact_isolation_cohabitation_requires_cross_artifact_hash_guards": True,
            "updater_dist_artifact_isolation_cohabitation_download_enabled_by_default": False,
            "updater_dist_artifact_isolation_cohabitation_installer_launch_enabled_by_default": False,
            "updater_dist_artifact_isolation_cohabitation_primary_replacement_enabled_by_default": False,
            "updater_dist_artifact_isolation_cohabitation_settings_install_control_exposed": False,
            "updater_dist_artifact_isolation_cohabitation_production_auto_update_complete_default": False,
            "updater_signed_artifact_verification_closeout_proof_built": True,
            "updater_signed_artifact_verification_closeout_requires_dist_artifact_isolation_cohabitation": True,
            "updater_signed_artifact_verification_closeout_requires_signature_probe": True,
            "updater_signed_artifact_verification_closeout_requires_studio_signed_output": True,
            "updater_signed_artifact_verification_closeout_requires_installer_signed_output": True,
            "updater_signed_artifact_verification_closeout_rechecks_artifact_hashes": True,
            "updater_signed_artifact_verification_closeout_rejects_secret_like_signature_probe": True,
            "updater_signed_artifact_verification_closeout_download_enabled_by_default": False,
            "updater_signed_artifact_verification_closeout_installer_launch_enabled_by_default": False,
            "updater_signed_artifact_verification_closeout_primary_replacement_enabled_by_default": False,
            "updater_signed_artifact_verification_closeout_settings_install_control_exposed": False,
            "updater_signed_artifact_verification_closeout_production_auto_update_complete_default": False,
            "updater_local_installer_disposable_dry_run_proof_built": True,
            "updater_local_installer_disposable_dry_run_default_enabled": False,
            "updater_local_installer_disposable_dry_run_requires_plan_file": True,
            "updater_local_installer_disposable_dry_run_requires_disposable_target_root": True,
            "updater_local_installer_disposable_dry_run_requires_explicit_execution_flag": True,
            "updater_local_installer_disposable_dry_run_uses_chaseos_installer": True,
            "updater_local_installer_disposable_dry_run_creates_backup": True,
            "updater_local_installer_disposable_dry_run_writes_receipt": True,
            "updater_local_installer_disposable_dry_run_blocks_primary_dist_target": True,
            "updater_local_installer_disposable_dry_run_live_install_enabled_by_default": False,
            "updater_local_installer_disposable_dry_run_primary_replacement_enabled_by_default": False,
            "updater_local_installer_disposable_dry_run_settings_install_control_exposed": False,
            "updater_local_installer_disposable_dry_run_production_auto_update_complete_default": False,
            "updater_local_manifest_background_prompt_proof_built": True,
            "updater_local_manifest_background_prompt_default_enabled": False,
            "updater_local_manifest_background_prompt_requires_manifest_file": True,
            "updater_local_manifest_background_prompt_validates_manifest_schema": True,
            "updater_local_manifest_background_prompt_compares_current_latest": True,
            "updater_local_manifest_background_prompt_prompted_only": True,
            "updater_local_manifest_background_prompt_local_file_manifest_supported": True,
            "updater_local_manifest_background_prompt_background_poll_enabled_by_default": False,
            "updater_local_manifest_background_prompt_download_enabled_by_default": False,
            "updater_local_manifest_background_prompt_installer_launch_enabled_by_default": False,
            "updater_local_manifest_background_prompt_primary_replacement_enabled_by_default": False,
            "updater_local_manifest_background_prompt_settings_install_control_exposed": False,
            "updater_local_manifest_background_prompt_github_or_domain_required": False,
            "updater_local_manifest_background_prompt_can_preview_disposable_installer_plan": True,
            "updater_local_manifest_background_prompt_production_auto_update_complete_default": False,
            "updater_local_release_channel_blocker_closeout_proof_built": True,
            "updater_local_release_channel_blocker_closeout_rechecks_dist_artifacts": True,
            "updater_local_release_channel_blocker_closeout_rechecks_local_manifest_prompt": True,
            "updater_local_release_channel_blocker_closeout_classifies_external_blockers": True,
            "updater_local_release_channel_blocker_closeout_download_enabled_by_default": False,
            "updater_local_release_channel_blocker_closeout_installer_launch_enabled_by_default": False,
            "updater_local_release_channel_blocker_closeout_primary_replacement_enabled_by_default": False,
            "updater_local_release_channel_blocker_closeout_startup_mutation_enabled_by_default": False,
            "updater_local_release_channel_blocker_closeout_settings_install_control_exposed": False,
            "updater_local_release_channel_blocker_closeout_production_auto_update_complete_default": False,
            "updater_authoritative_candidate_supply_verification_after_import_proof_built": True,
            "updater_authoritative_candidate_supply_verification_after_import_default_enabled": False,
            "updater_authoritative_candidate_supply_verification_after_import_requires_import_boundary": True,
            "updater_authoritative_candidate_supply_verification_after_import_rechecks_import_digest": True,
            "updater_authoritative_candidate_supply_verification_after_import_revalidates_imported_candidate_hashes": True,
            "updater_authoritative_candidate_supply_verification_after_import_requires_supply_approval": True,
            "updater_authoritative_candidate_supply_verification_after_import_requires_candidate_verification_approval": True,
            "updater_authoritative_candidate_supply_verification_after_import_source_write_enabled": False,
            "updater_authoritative_candidate_supply_verification_after_import_wrapper_removal_enabled": False,
            "updater_authoritative_candidate_supply_verification_after_import_decompiler_execution_enabled": False,
            "updater_authoritative_candidate_supply_verification_after_import_settings_write_control_exposed": False,
            "updater_authoritative_candidate_supply_verification_after_import_primary_real_exe_replacement_enabled": False,
            "updater_authoritative_candidate_supply_verification_after_import_final_auto_update_closeout_blocked_until_source_restored": True,
            "updater_current_vault_wrapper_removal_after_import_execution_proof_built": True,
            "updater_current_vault_wrapper_removal_after_import_execution_default_enabled": False,
            "updater_current_vault_wrapper_removal_after_import_execution_requires_after_import_proof": True,
            "updater_current_vault_wrapper_removal_after_import_execution_rechecks_after_import_digest": True,
            "updater_current_vault_wrapper_removal_after_import_execution_reuses_wrapper_removal_executor": True,
            "updater_current_vault_wrapper_removal_after_import_execution_requires_exact_operator_statement": True,
            "updater_current_vault_wrapper_removal_after_import_execution_requires_explicit_source_write_flag": True,
            "updater_current_vault_wrapper_removal_after_import_execution_decompiler_execution_enabled": False,
            "updater_current_vault_wrapper_removal_after_import_execution_candidate_source_execution_enabled": False,
            "updater_current_vault_wrapper_removal_after_import_execution_settings_write_control_exposed": False,
            "updater_current_vault_wrapper_removal_after_import_execution_primary_real_exe_replacement_enabled": False,
            "updater_current_vault_wrapper_removal_after_import_execution_final_auto_update_closeout_blocked_until_regression": True,
            "updater_current_vault_wrapper_removal_executor_boundary_proof_built": True,
            "updater_current_vault_wrapper_removal_executor_default_enabled": False,
            "updater_current_vault_wrapper_removal_executor_requires_supply_packet": True,
            "updater_current_vault_wrapper_removal_executor_requires_candidate_verification": True,
            "updater_current_vault_wrapper_removal_executor_requires_exact_operator_statement": True,
            "updater_current_vault_wrapper_removal_executor_requires_explicit_source_write_flag": True,
            "updater_current_vault_wrapper_removal_executor_rechecks_candidate_hashes": True,
            "updater_current_vault_wrapper_removal_executor_scans_wrapper_tokens_after_write": True,
            "updater_current_vault_wrapper_removal_executor_decompiler_execution_enabled": False,
            "updater_current_vault_wrapper_removal_executor_settings_write_control_exposed": False,
            "updater_current_vault_wrapper_removal_executor_primary_real_exe_replacement_enabled": False,
            "updater_current_vault_wrapper_removal_executor_final_auto_update_closeout_blocked_until_regression": True,
            "updater_production_primary_relaunch_receipt_boundary_proof_built": True,
            "updater_production_primary_relaunch_receipt_boundary_default_enabled": False,
            "updater_production_primary_relaunch_receipt_boundary_requires_primary_replacement_receipt_boundary": True,
            "updater_production_primary_relaunch_receipt_boundary_requires_exact_operator_statement": True,
            "updater_production_primary_relaunch_receipt_boundary_requires_external_receipt": True,
            "updater_production_primary_relaunch_receipt_boundary_uses_chaseos_installer": True,
            "updater_production_primary_relaunch_receipt_boundary_external_helper_relaunch_receipt_supported": True,
            "updater_production_primary_relaunch_receipt_boundary_chaseos_relaunch_enabled": False,
            "updater_production_primary_relaunch_receipt_boundary_os_process_spawn_enabled": False,
            "updater_production_primary_relaunch_receipt_boundary_primary_install_mutation_enabled": False,
            "updater_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_enabled": False,
            "updater_production_primary_relaunch_receipt_boundary_settings_install_control_exposed": False,
            "updater_production_primary_relaunch_receipt_boundary_production_auto_update_complete": False,
            "next_recommended_pass": (
                "launcher-update-controlled-live-installer-evidence-runner"
            ),
        }
    )
    return readiness


def _production_primary_relaunch_command_packet(vault, primary_replacement_boundary):
    replacement_command = (
        primary_replacement_boundary.get("primary_replacement_command_packet") or {}
    )
    replacement_receipt = primary_replacement_boundary.get("replacement_receipt") or {}
    primary_executable_path = str(
        replacement_command.get("primary_executable_path")
        or replacement_receipt.get("primary_executable_path")
        or ""
    )
    primary_install_root = str(
        replacement_command.get("primary_install_root")
        or replacement_receipt.get("primary_install_root")
        or ""
    )
    command_packet = {
        "schema_version": PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SCHEMA_VERSION,
        "surface": PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SURFACE_ID,
        "command_kind": "primary_relaunch_receipt_boundary",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "artifact_name": primary_replacement_boundary.get("artifact_name")
        or replacement_command.get("artifact_name")
        or CURRENT_ARTIFACT_NAME,
        "latest_version": primary_replacement_boundary.get("latest_version")
        or replacement_command.get("latest_version")
        or "",
        "vault_root": str(_Path(vault).resolve()),
        "primary_install_root": primary_install_root,
        "primary_executable_path": primary_executable_path,
        "source_primary_replacement_receipt_boundary_digest_sha256": primary_replacement_boundary.get(
            "primary_replacement_receipt_boundary_digest_sha256", ""
        ),
        "source_primary_rollback_audit_boundary_digest_sha256": primary_replacement_boundary.get(
            "source_primary_rollback_audit_boundary_digest_sha256", ""
        ),
        "primary_replacement_command_packet_digest_sha256": primary_replacement_boundary.get(
            "primary_replacement_command_packet_digest_sha256", ""
        )
        or replacement_command.get("primary_replacement_command_packet_digest_sha256", ""),
        "primary_replacement_artifact_descriptor_digest_sha256": primary_replacement_boundary.get(
            "primary_replacement_artifact_descriptor_digest_sha256", ""
        )
        or replacement_command.get(
            "primary_replacement_artifact_descriptor_digest_sha256", ""
        ),
        "post_replacement_sha256": replacement_receipt.get("post_replacement_sha256")
        or replacement_command.get("replacement_artifact_sha256")
        or "",
        "relaunch_argv": [primary_executable_path, "--vault-root", str(_Path(vault).resolve())],
        "requires_external_helper_relaunch_receipt": True,
        "network_allowed": False,
        "secret_values_allowed": False,
        "relaunch_performed_by_chaseos_allowed": False,
        "os_process_spawn_performed_by_chaseos_allowed": False,
        "primary_install_mutation_allowed": False,
        "startup_mutation_allowed": False,
        "primary_real_executable_replacement_allowed": False,
        "settings_install_control_exposed": False,
    }
    command_packet["primary_relaunch_command_packet_digest_sha256"] = (
        _extension_digest_without(
            command_packet,
            "primary_relaunch_command_packet_digest_sha256",
        )
    )
    return command_packet


def required_update_production_primary_relaunch_receipt_boundary_operator_statement(
    primary_replacement_boundary, relaunch_command_packet
):
    return (
        f"{PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_OPERATOR_STATEMENT_PREFIX} "
        f"version={relaunch_command_packet.get('latest_version', '')} "
        f"artifact={relaunch_command_packet.get('artifact_name', CURRENT_ARTIFACT_NAME)} "
        "source_primary_replacement_receipt_boundary_digest_sha256="
        f"{primary_replacement_boundary.get('primary_replacement_receipt_boundary_digest_sha256', '')} "
        "primary_relaunch_command_packet_digest_sha256="
        f"{relaunch_command_packet.get('primary_relaunch_command_packet_digest_sha256', '')}"
    )


def _sanitize_production_primary_relaunch_receipt(raw_receipt):
    if raw_receipt is None:
        return {}, ["primary_relaunch_receipt_required"]
    if not isinstance(raw_receipt, dict):
        return {}, ["primary_relaunch_receipt_malformed"]

    scalar_fields = {
        "ok",
        "status",
        "helper_binary_name",
        "artifact_name",
        "latest_version",
        "primary_install_root",
        "primary_executable_path",
        "vault_root",
        "source_primary_replacement_receipt_boundary_digest_sha256",
        "source_primary_rollback_audit_boundary_digest_sha256",
        "primary_replacement_command_packet_digest_sha256",
        "primary_replacement_artifact_descriptor_digest_sha256",
        "primary_relaunch_command_packet_digest_sha256",
        "post_replacement_sha256",
        "relaunch_exit_code",
        "receipt_validation_performed",
        "relaunch_command_validated",
        "relaunch_performed_by_helper",
        "target_process_start_requested",
        "target_process_start_confirmed",
        "replacement_receipt_verified",
        "post_replacement_hash_verified",
        "relaunch_performed_by_chaseos",
        "os_process_spawn_performed_by_chaseos",
        "primary_install_mutation_performed",
        "startup_mutation_performed",
        "real_executable_replacement_performed",
        "primary_real_executable_replacement_performed",
        "settings_install_control_exposed",
        "stdout_sha256",
        "stderr_sha256",
        "started_at_utc",
        "completed_at_utc",
    }
    list_fields = {"relaunch_argv", "argv", "helper_argv"}
    receipt = {}
    errors = []
    for key, value in raw_receipt.items():
        normalized_key = _normalize_live_runner_policy_key(key)
        if _policy_key_is_forbidden_secret_field(normalized_key):
            errors.append(f"primary_relaunch_receipt_forbidden_secret_field:{key}")
            continue
        if key in scalar_fields:
            if isinstance(value, (str, int, float, bool)) or value is None:
                receipt[key] = value
            else:
                errors.append(f"primary_relaunch_receipt_{key}_must_be_scalar")
            continue
        if key in list_fields:
            if isinstance(value, list) and all(
                isinstance(item, (str, int, float, bool)) or item is None
                for item in value
            ):
                receipt[key] = list(value)
            else:
                errors.append(f"primary_relaunch_receipt_{key}_must_be_scalar_list")
            continue
        errors.append(f"primary_relaunch_receipt_unexpected_field:{key}")
    return receipt, errors


def _production_primary_relaunch_receipt_boundary_result(
    *,
    vault,
    timestamp,
    status,
    ok,
    blockers,
    source_result,
    primary_replacement_boundary,
    relaunch_command_packet,
    required_statement,
    operator_statement_matched,
    receipt,
    relaunch_boundary,
):
    boundary_digest = relaunch_boundary.get(
        "primary_relaunch_receipt_boundary_digest_sha256", ""
    )
    command_digest = relaunch_command_packet.get(
        "primary_relaunch_command_packet_digest_sha256", ""
    )
    source_boundary_digest = relaunch_command_packet.get(
        "source_primary_replacement_receipt_boundary_digest_sha256", ""
    )
    replacement_command_digest = relaunch_command_packet.get(
        "primary_replacement_command_packet_digest_sha256", ""
    )
    replacement_artifact_digest = relaunch_command_packet.get(
        "primary_replacement_artifact_descriptor_digest_sha256", ""
    )
    rollback_boundary_digest = relaunch_command_packet.get(
        "source_primary_rollback_audit_boundary_digest_sha256", ""
    )
    receipt_valid = bool(relaunch_boundary.get("primary_relaunch_receipt_valid"))
    external_relaunch = bool(
        relaunch_boundary.get("external_helper_primary_relaunch_reported")
    )
    chaseos_relaunch = bool(relaunch_boundary.get("relaunch_performed_by_chaseos"))
    primary_install_mutation = bool(
        relaunch_boundary.get("primary_install_mutation_performed")
    )
    primary_real_replacement = bool(
        relaunch_boundary.get("primary_real_executable_replacement_performed")
    )
    replacement_reported = bool(
        relaunch_boundary.get("external_helper_primary_replacement_reported")
    )
    return {
        "ok": bool(ok),
        "surface": PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SURFACE_ID,
        "schema_version": PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(_Path(vault).resolve()),
        "artifact_name": relaunch_command_packet.get("artifact_name", CURRENT_ARTIFACT_NAME),
        "latest_version": relaunch_command_packet.get("latest_version", ""),
        "errors": list(blockers),
        "warnings": [],
        "production_primary_replacement_receipt_boundary": source_result,
        "primary_replacement_receipt_boundary": primary_replacement_boundary,
        "primary_relaunch_command_packet": relaunch_command_packet,
        "primary_relaunch_command_packet_digest_sha256": command_digest,
        "required_operator_statement": required_statement,
        "operator_statement_matched": bool(operator_statement_matched),
        "relaunch_receipt": receipt,
        "primary_relaunch_receipt_boundary": relaunch_boundary,
        "primary_relaunch_receipt_boundary_digest_sha256": boundary_digest,
        "source_primary_replacement_receipt_boundary_digest_sha256": source_boundary_digest,
        "source_primary_rollback_audit_boundary_digest_sha256": rollback_boundary_digest,
        "primary_replacement_command_packet_digest_sha256": replacement_command_digest,
        "primary_replacement_artifact_descriptor_digest_sha256": replacement_artifact_digest,
        "post_replacement_sha256": relaunch_command_packet.get("post_replacement_sha256", ""),
        "primary_relaunch_receipt_boundary_ready": bool(ok),
        "primary_relaunch_receipt_valid": receipt_valid,
        "external_helper_primary_relaunch_reported": external_relaunch,
        "external_helper_primary_replacement_reported": replacement_reported,
        "relaunch_performed_by_chaseos": chaseos_relaunch,
        "os_process_spawn_performed_by_chaseos": False,
        "primary_install_mutation_performed": primary_install_mutation,
        "startup_mutation_performed": False,
        "real_executable_replacement_performed": False,
        "primary_real_executable_replacement_performed": primary_real_replacement,
        "primary_real_executable_replacement_verified_live": False,
        "settings_install_control_exposed": False,
        "production_auto_update_complete": False,
        "requires_final_update_closeout_audit": True,
        "authority": _authority(
            update_production_primary_relaunch_receipt_boundary_built=True,
            update_production_primary_relaunch_receipt_boundary_ready=bool(ok),
            update_production_primary_relaunch_receipt_boundary_statement_matched=bool(
                operator_statement_matched
            ),
            update_production_primary_relaunch_receipt_boundary_receipt_valid=receipt_valid,
            update_production_primary_relaunch_receipt_boundary_external_helper_primary_relaunch_reported=external_relaunch,
            update_production_primary_relaunch_receipt_boundary_chaseos_relaunch_performed=chaseos_relaunch,
            update_production_primary_relaunch_receipt_boundary_primary_install_mutation_performed=primary_install_mutation,
            update_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_performed=primary_real_replacement,
            update_production_primary_relaunch_receipt_boundary_primary_real_exe_replacement_verified_live=False,
        ),
        "readiness": _readiness(),
    }


def build_launcher_update_production_primary_relaunch_receipt_boundary_proof(
    vault_root,
    *,
    production_primary_replacement_receipt_boundary=None,
    relaunch_receipt=None,
    operator_approved_primary_relaunch_receipt_boundary=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    blockers = []

    source_result = production_primary_replacement_receipt_boundary
    if source_result is None:
        source_result = build_launcher_update_production_primary_replacement_receipt_boundary_proof(
            vault,
            generated_at=timestamp,
        )
        blockers.append("production_primary_replacement_receipt_boundary_required")
    source_result = _extension_unwrap_api_data(
        source_result,
        "launcher_update_production_primary_replacement_receipt_boundary_proof",
    )
    if not isinstance(source_result, dict):
        source_result = {}
        blockers.append("production_primary_replacement_receipt_boundary_malformed")

    source_surface = source_result.get("surface", "")
    if source_surface and source_surface != PRODUCTION_PRIMARY_REPLACEMENT_RECEIPT_BOUNDARY_SURFACE_ID:
        blockers.append("production_primary_replacement_receipt_boundary_surface_mismatch")

    primary_replacement_boundary = (
        source_result.get("primary_replacement_receipt_boundary") or {}
    )
    if not isinstance(primary_replacement_boundary, dict):
        primary_replacement_boundary = {}
        blockers.append("primary_replacement_receipt_boundary_malformed")

    if not bool(source_result.get("ok")):
        blockers.append("primary_replacement_receipt_boundary_not_ready")
    if not bool(source_result.get("primary_replacement_receipt_boundary_ready")):
        blockers.append("primary_replacement_receipt_boundary_ready_required")
    if not bool(source_result.get("primary_replacement_receipt_valid")):
        blockers.append("primary_replacement_receipt_valid_required")
    if not bool(source_result.get("external_helper_primary_replacement_reported")):
        blockers.append("external_helper_primary_replacement_report_required")

    source_boundary_digest = (
        source_result.get("primary_replacement_receipt_boundary_digest_sha256")
        or primary_replacement_boundary.get(
            "primary_replacement_receipt_boundary_digest_sha256", ""
        )
    )
    if primary_replacement_boundary:
        computed_source_boundary_digest = _extension_digest_without(
            primary_replacement_boundary,
            "primary_replacement_receipt_boundary_digest_sha256",
        )
        if source_boundary_digest != computed_source_boundary_digest:
            blockers.append("source_primary_replacement_receipt_boundary_digest_mismatch")

    source_command_packet = (
        source_result.get("primary_replacement_command_packet")
        or primary_replacement_boundary.get("primary_replacement_command_packet")
        or {}
    )
    if not isinstance(source_command_packet, dict):
        source_command_packet = {}
        blockers.append("primary_replacement_command_packet_malformed")
    source_command_digest = (
        source_result.get("primary_replacement_command_packet_digest_sha256")
        or source_command_packet.get("primary_replacement_command_packet_digest_sha256", "")
    )
    if source_command_packet:
        computed_source_command_digest = _extension_digest_without(
            source_command_packet,
            "primary_replacement_command_packet_digest_sha256",
        )
        if source_command_digest != computed_source_command_digest:
            blockers.append("primary_replacement_command_packet_digest_mismatch")

    replacement_descriptor = (
        source_result.get("primary_replacement_artifact_descriptor")
        or primary_replacement_boundary.get("primary_replacement_artifact_descriptor")
        or {}
    )
    if not isinstance(replacement_descriptor, dict):
        replacement_descriptor = {}
        blockers.append("primary_replacement_artifact_descriptor_malformed")
    descriptor_digest = (
        source_result.get("primary_replacement_artifact_descriptor_digest_sha256")
        or replacement_descriptor.get(
            "primary_replacement_artifact_descriptor_digest_sha256", ""
        )
    )
    if replacement_descriptor:
        computed_descriptor_digest = _extension_digest_without(
            replacement_descriptor,
            "primary_replacement_artifact_descriptor_digest_sha256",
        )
        if descriptor_digest != computed_descriptor_digest:
            blockers.append("primary_replacement_artifact_descriptor_digest_mismatch")

    for source_flag in (
        "primary_replacement_performed_by_chaseos",
        "os_process_spawn_performed_by_chaseos",
        "primary_install_mutation_performed",
        "startup_mutation_performed",
        "real_executable_replacement_performed",
        "primary_real_executable_replacement_performed",
        "settings_install_control_exposed",
    ):
        if bool(source_result.get(source_flag)) or bool(
            primary_replacement_boundary.get(source_flag)
        ):
            blockers.append(f"source_primary_replacement_{source_flag}_must_be_false")

    relaunch_command_packet = _production_primary_relaunch_command_packet(
        vault,
        {
            **primary_replacement_boundary,
            "primary_replacement_command_packet": source_command_packet,
            "primary_replacement_receipt_boundary_digest_sha256": source_boundary_digest,
            "primary_replacement_artifact_descriptor_digest_sha256": descriptor_digest,
            "primary_replacement_command_packet_digest_sha256": source_command_digest,
        },
    )
    required_statement = (
        required_update_production_primary_relaunch_receipt_boundary_operator_statement(
            {
                **primary_replacement_boundary,
                "primary_replacement_receipt_boundary_digest_sha256": source_boundary_digest,
            },
            relaunch_command_packet,
        )
    )

    operator_statement_matched = (
        bool(operator_approved_primary_relaunch_receipt_boundary)
        and str(operator_statement) == required_statement
    )
    if not operator_approved_primary_relaunch_receipt_boundary:
        blockers.append("operator_primary_relaunch_receipt_boundary_approval_required")
    elif not operator_statement_matched:
        blockers.append("operator_primary_relaunch_receipt_boundary_statement_mismatch")

    receipt, receipt_errors = _sanitize_production_primary_relaunch_receipt(
        relaunch_receipt
    )
    blockers.extend(receipt_errors)
    if receipt:
        expected_fields = (
            "helper_binary_name",
            "artifact_name",
            "latest_version",
            "primary_install_root",
            "primary_executable_path",
            "vault_root",
            "source_primary_replacement_receipt_boundary_digest_sha256",
            "source_primary_rollback_audit_boundary_digest_sha256",
            "primary_replacement_command_packet_digest_sha256",
            "primary_replacement_artifact_descriptor_digest_sha256",
            "primary_relaunch_command_packet_digest_sha256",
            "post_replacement_sha256",
        )
        for field in expected_fields:
            if receipt.get(field) != relaunch_command_packet.get(field):
                blockers.append(f"primary_relaunch_receipt_{field}_mismatch")
        if receipt.get("relaunch_argv") != relaunch_command_packet.get("relaunch_argv"):
            blockers.append("primary_relaunch_receipt_relaunch_argv_mismatch")
        if receipt.get("ok") is not True:
            blockers.append("primary_relaunch_receipt_ok_required")
        if receipt.get("status") != "primary_relaunch_receipt_ready":
            blockers.append("primary_relaunch_receipt_status_mismatch")
        for required_true in (
            "receipt_validation_performed",
            "relaunch_command_validated",
            "relaunch_performed_by_helper",
            "target_process_start_requested",
            "target_process_start_confirmed",
            "replacement_receipt_verified",
            "post_replacement_hash_verified",
        ):
            if receipt.get(required_true) is not True:
                blockers.append(f"primary_relaunch_receipt_{required_true}_required")
        for required_false in (
            "relaunch_performed_by_chaseos",
            "os_process_spawn_performed_by_chaseos",
            "primary_install_mutation_performed",
            "startup_mutation_performed",
            "real_executable_replacement_performed",
            "primary_real_executable_replacement_performed",
            "settings_install_control_exposed",
        ):
            if receipt.get(required_false) is not False:
                blockers.append(
                    f"primary_relaunch_receipt_{required_false}_must_be_false"
                )

    status = "launcher_update_production_primary_relaunch_receipt_boundary_blocked"
    ok = not blockers
    if ok:
        status = "launcher_update_production_primary_relaunch_receipt_boundary_ready"

    primary_relaunch_receipt_valid = bool(ok and receipt)
    external_helper_primary_relaunch_reported = bool(
        primary_relaunch_receipt_valid and receipt.get("relaunch_performed_by_helper")
    )
    relaunch_boundary = {
        "schema_version": PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SCHEMA_VERSION,
        "surface": PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SURFACE_ID,
        "generated_at_utc": timestamp,
        "helper_binary_name": "ChaseOS-Installer.exe",
        "artifact_name": relaunch_command_packet.get("artifact_name", CURRENT_ARTIFACT_NAME),
        "latest_version": relaunch_command_packet.get("latest_version", ""),
        "source_primary_replacement_receipt_boundary_digest_sha256": source_boundary_digest,
        "source_primary_rollback_audit_boundary_digest_sha256": relaunch_command_packet.get(
            "source_primary_rollback_audit_boundary_digest_sha256", ""
        ),
        "primary_replacement_command_packet_digest_sha256": relaunch_command_packet.get(
            "primary_replacement_command_packet_digest_sha256", ""
        ),
        "primary_replacement_artifact_descriptor_digest_sha256": relaunch_command_packet.get(
            "primary_replacement_artifact_descriptor_digest_sha256", ""
        ),
        "primary_relaunch_command_packet": relaunch_command_packet,
        "primary_relaunch_command_packet_digest_sha256": relaunch_command_packet.get(
            "primary_relaunch_command_packet_digest_sha256", ""
        ),
        "post_replacement_sha256": relaunch_command_packet.get(
            "post_replacement_sha256", ""
        ),
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "relaunch_receipt": receipt,
        "primary_relaunch_receipt_valid": primary_relaunch_receipt_valid,
        "external_helper_primary_relaunch_reported": external_helper_primary_relaunch_reported,
        "external_helper_primary_replacement_reported": bool(
            source_result.get("external_helper_primary_replacement_reported")
        ),
        "relaunch_performed_by_chaseos": False,
        "os_process_spawn_performed_by_chaseos": False,
        "primary_install_mutation_performed": False,
        "startup_mutation_performed": False,
        "real_executable_replacement_performed": False,
        "primary_real_executable_replacement_performed": False,
        "primary_real_executable_replacement_verified_live": False,
        "settings_install_control_exposed": False,
        "production_auto_update_complete": False,
        "requires_final_update_closeout_audit": True,
    }
    relaunch_boundary["primary_relaunch_receipt_boundary_digest_sha256"] = (
        _extension_digest_without(
            relaunch_boundary,
            "primary_relaunch_receipt_boundary_digest_sha256",
        )
    )

    return _production_primary_relaunch_receipt_boundary_result(
        vault=vault,
        timestamp=timestamp,
        status=status,
        ok=ok,
        blockers=blockers,
        source_result=source_result,
        primary_replacement_boundary=primary_replacement_boundary,
        relaunch_command_packet=relaunch_command_packet,
        required_statement=required_statement,
        operator_statement_matched=operator_statement_matched,
        receipt=receipt,
        relaunch_boundary=relaunch_boundary,
    )


def _source_recovery_artifact_descriptor(path, expected_sha256):
    artifact_path = _Path(path)
    descriptor = {
        "path": str(artifact_path.resolve()),
        "exists": artifact_path.exists(),
        "expected_sha256": expected_sha256,
        "actual_sha256": "",
        "sha256_matches": False,
        "size_bytes": 0,
    }
    if artifact_path.exists() and artifact_path.is_file():
        payload = artifact_path.read_bytes()
        actual_sha256 = _wrapper_hashlib.sha256(payload).hexdigest()
        descriptor.update(
            {
                "actual_sha256": actual_sha256,
                "sha256_matches": actual_sha256 == expected_sha256,
                "size_bytes": len(payload),
            }
        )
    return descriptor


def build_launcher_update_source_recovery_cleanup_proof(
    vault_root,
    *,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    launcher_source_path = _Path(__file__).resolve()
    api_source_path = launcher_source_path.parent / "shell" / "api.py"
    launcher_artifact = _source_recovery_artifact_descriptor(
        _RECOVERED_BYTECODE_PATH,
        _RECOVERED_BYTECODE_EXPECTED_SHA256,
    )
    api_artifact = _source_recovery_artifact_descriptor(
        launcher_source_path.parent / _API_RECOVERED_BYTECODE_RELATIVE_PATH,
        _API_RECOVERED_BYTECODE_EXPECTED_SHA256,
    )
    launcher_source_text = launcher_source_path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    api_source_text = api_source_path.read_text(encoding="utf-8", errors="replace")
    launcher_wrapper_active = "exec(_RECOVERED_BYTECODE_CODE, globals())" in launcher_source_text
    api_wrapper_active = "exec(_RECOVERED_BYTECODE_CODE, globals())" in api_source_text
    launcher_hash_pinned = (
        _RECOVERED_BYTECODE_EXPECTED_SHA256 in launcher_source_text
        and launcher_artifact["sha256_matches"]
    )
    api_hash_pinned = (
        _API_RECOVERED_BYTECODE_EXPECTED_SHA256 in api_source_text
        and api_artifact["sha256_matches"]
    )
    recovery_artifacts_pinned = bool(launcher_hash_pinned and api_hash_pinned)
    normal_source_restored = not (launcher_wrapper_active or api_wrapper_active)
    blockers = []
    if not launcher_artifact["exists"]:
        blockers.append("launcher_update_recovered_bytecode_missing")
    if not api_artifact["exists"]:
        blockers.append("studio_api_recovered_bytecode_missing")
    if not launcher_hash_pinned:
        blockers.append("launcher_update_recovered_bytecode_hash_not_pinned")
    if not api_hash_pinned:
        blockers.append("studio_api_recovered_bytecode_hash_not_pinned")
    if not normal_source_restored:
        blockers.append("normal_source_restoration_required")

    ready = recovery_artifacts_pinned and normal_source_restored
    status = "launcher_update_source_recovery_cleanup_blocked"
    if recovery_artifacts_pinned and not normal_source_restored:
        status = "launcher_update_source_recovery_cleanup_pinned_but_source_wrapped"
    if ready:
        status = "launcher_update_source_recovery_cleanup_ready"

    proof = {
        "ok": ready,
        "surface": SOURCE_RECOVERY_CLEANUP_SURFACE_ID,
        "schema_version": SOURCE_RECOVERY_CLEANUP_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": blockers,
        "warnings": [],
        "source_recovery_cleanup_ready": ready,
        "recovery_artifacts_pinned": recovery_artifacts_pinned,
        "normal_source_restored": normal_source_restored,
        "final_auto_update_closeout_blocked": not normal_source_restored,
        "production_auto_update_complete": False,
        "launcher_update_check_source": {
            "path": str(launcher_source_path),
            "wrapper_active": launcher_wrapper_active,
            "hash_pinned": launcher_hash_pinned,
            "recovered_artifact": launcher_artifact,
        },
        "studio_shell_api_source": {
            "path": str(api_source_path),
            "wrapper_active": api_wrapper_active,
            "hash_pinned": api_hash_pinned,
            "recovered_artifact": api_artifact,
        },
        "authority": _authority(
            source_recovery_cleanup_proof_built=True,
            source_recovery_cleanup_recovery_artifacts_pinned=recovery_artifacts_pinned,
            source_recovery_cleanup_normal_source_restored=normal_source_restored,
            source_recovery_cleanup_final_closeout_blocked=not normal_source_restored,
        ),
        "readiness": _readiness(),
    }
    proof["source_recovery_cleanup_digest_sha256"] = _extension_digest_without(
        proof,
        "source_recovery_cleanup_digest_sha256",
    )
    return proof


def _normal_source_candidate_descriptor(path, role, required_tokens):
    candidate_path = _Path(path)
    descriptor = {
        "role": role,
        "path": str(candidate_path),
        "resolved_path": "",
        "exists": candidate_path.exists(),
        "is_file": False,
        "size_bytes": 0,
        "sha256": "",
        "text_readable": False,
        "wrapper_active": False,
        "required_tokens": list(required_tokens),
        "missing_required_tokens": list(required_tokens),
        "required_tokens_present": False,
        "normal_source_candidate": False,
        "candidate_status": "missing",
    }
    if not candidate_path.exists():
        return descriptor

    try:
        resolved = candidate_path.resolve()
    except OSError:
        resolved = candidate_path
    descriptor["resolved_path"] = str(resolved)
    descriptor["is_file"] = candidate_path.is_file()
    if not candidate_path.is_file():
        descriptor["candidate_status"] = "not_file"
        return descriptor

    payload = candidate_path.read_bytes()
    descriptor["size_bytes"] = len(payload)
    descriptor["sha256"] = _wrapper_hashlib.sha256(payload).hexdigest()
    text = payload.decode("utf-8", errors="replace")
    descriptor["text_readable"] = True
    wrapper_tokens = [
        "exec(_RECOVERED_BYTECODE_CODE, globals())",
        "_RECOVERED_BYTECODE_PATH",
        "marshal as _marshal",
    ]
    descriptor["wrapper_active"] = any(token in text for token in wrapper_tokens)
    missing = [token for token in required_tokens if token not in text]
    descriptor["missing_required_tokens"] = missing
    descriptor["required_tokens_present"] = not missing
    if descriptor["wrapper_active"]:
        descriptor["candidate_status"] = "wrapper_backed_source"
    elif missing:
        descriptor["candidate_status"] = "stale_or_incomplete_source"
    else:
        descriptor["candidate_status"] = "normal_source_candidate"
        descriptor["normal_source_candidate"] = True
    return descriptor


def _normal_source_default_candidate_paths(vault, launcher_source_path):
    repo_root = launcher_source_path.parents[2]
    api_source_path = launcher_source_path.parent / "shell" / "api.py"
    shell_test_source_path = launcher_source_path.parent / "shell" / "test_pass10a_shell.py"
    roots = []
    for root in (vault, repo_root):
        if root not in roots:
            roots.append(root)
    build_launcher_paths = [
        root / "build" / "lib" / "runtime" / "studio" / "launcher_update_check.py"
        for root in roots
    ]
    build_api_paths = [
        root / "build" / "lib" / "runtime" / "studio" / "shell" / "api.py"
        for root in roots
    ]
    build_shell_test_paths = [
        root
        / "build"
        / "lib"
        / "runtime"
        / "studio"
        / "shell"
        / "test_pass10a_shell.py"
        for root in roots
    ]
    return {
        "launcher_update_check": [launcher_source_path, *build_launcher_paths],
        "studio_shell_api": [api_source_path, *build_api_paths],
        "studio_shell_test_pass10a": [shell_test_source_path, *build_shell_test_paths],
    }


def build_launcher_update_normal_source_restoration_readiness(
    vault_root,
    *,
    candidate_paths=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    launcher_source_path = _Path(__file__).resolve()
    source_cleanup = build_launcher_update_source_recovery_cleanup_proof(
        vault,
        generated_at=timestamp,
    )
    candidate_map = candidate_paths or _normal_source_default_candidate_paths(
        vault,
        launcher_source_path,
    )
    token_requirements = {
        "launcher_update_check": [
            "build_launcher_update_source_recovery_cleanup_proof",
            "build_launcher_update_production_primary_relaunch_receipt_boundary_proof",
            "build_launcher_update_normal_source_restoration_readiness",
            "build_launcher_update_source_candidate_inventory_wrapper_removal_preflight",
        ],
        "studio_shell_api": [
            "class StudioAPI",
            "get_launcher_update_source_recovery_cleanup_proof",
            "get_launcher_update_production_primary_relaunch_receipt_boundary_proof",
            "get_launcher_update_normal_source_restoration_readiness",
            "get_launcher_update_source_candidate_inventory_wrapper_removal_preflight",
        ],
        "studio_shell_test_pass10a": [
            "TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell",
            "test_api_returns_source_recovery_cleanup_proof_envelope",
            "test_api_returns_normal_source_restoration_readiness_envelope",
            "test_api_returns_source_candidate_inventory_wrapper_removal_preflight_envelope",
        ],
    }
    candidates = {}
    for role, paths in candidate_map.items():
        required_tokens = token_requirements.get(role, [])
        candidates[role] = [
            _normal_source_candidate_descriptor(path, role, required_tokens)
            for path in paths
        ]

    launcher_candidate_found = any(
        item.get("normal_source_candidate")
        for item in candidates.get("launcher_update_check", [])
    )
    api_candidate_found = any(
        item.get("normal_source_candidate")
        for item in candidates.get("studio_shell_api", [])
    )
    shell_test_candidate_found = any(
        item.get("normal_source_candidate")
        for item in candidates.get("studio_shell_test_pass10a", [])
    )
    module_candidates_available = bool(launcher_candidate_found and api_candidate_found)
    current_wrappers_active = bool(
        (source_cleanup.get("launcher_update_check_source") or {}).get("wrapper_active")
        or (source_cleanup.get("studio_shell_api_source") or {}).get("wrapper_active")
    )
    normal_source_restoration_ready = bool(
        source_cleanup.get("normal_source_restored")
        and module_candidates_available
        and not current_wrappers_active
    )

    errors = []
    warnings = []
    if not source_cleanup.get("recovery_artifacts_pinned"):
        errors.append("recovery_artifacts_not_pinned")
    if not launcher_candidate_found:
        errors.append("launcher_update_normal_source_candidate_missing")
    if not api_candidate_found:
        errors.append("studio_api_normal_source_candidate_missing_or_stale")
    if current_wrappers_active:
        errors.append("normal_source_wrappers_still_active")
    if not shell_test_candidate_found:
        warnings.append("shell_test_prior_local_source_unverified")
    if not normal_source_restoration_ready:
        errors.append("normal_source_restoration_required_before_final_closeout")

    status = "launcher_update_normal_source_restoration_readiness_blocked"
    if module_candidates_available and current_wrappers_active:
        status = "launcher_update_normal_source_candidates_found_but_not_restored"
    if normal_source_restoration_ready:
        status = "launcher_update_normal_source_restoration_ready"

    readiness = {
        "ok": normal_source_restoration_ready,
        "surface": NORMAL_SOURCE_RESTORATION_READINESS_SURFACE_ID,
        "schema_version": NORMAL_SOURCE_RESTORATION_READINESS_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "source_recovery_cleanup_status": source_cleanup.get("status"),
        "recovery_artifacts_pinned": bool(source_cleanup.get("recovery_artifacts_pinned")),
        "current_source_wrappers_active": current_wrappers_active,
        "launcher_update_normal_source_candidate_found": launcher_candidate_found,
        "studio_api_normal_source_candidate_found": api_candidate_found,
        "shell_test_normal_source_candidate_found": shell_test_candidate_found,
        "normal_source_candidates_available": module_candidates_available,
        "normal_source_restoration_ready": normal_source_restoration_ready,
        "final_auto_update_closeout_blocked": not normal_source_restoration_ready,
        "production_auto_update_complete": False,
        "candidate_requirements": token_requirements,
        "candidates": candidates,
        "source_cleanup_digest_sha256": _extension_digest_without(
            source_cleanup,
            "source_recovery_cleanup_digest_sha256",
        ),
        "authority": _authority(
            normal_source_restoration_readiness_built=True,
            normal_source_restoration_ready=normal_source_restoration_ready,
            normal_source_restoration_candidates_available=module_candidates_available,
            normal_source_restoration_final_closeout_blocked=not normal_source_restoration_ready,
        ),
        "readiness": _readiness(),
    }
    readiness["normal_source_restoration_readiness_digest_sha256"] = (
        _extension_digest_without(
            readiness,
            "normal_source_restoration_readiness_digest_sha256",
        )
    )
    return readiness


def _normal_source_candidate_default_required_symbols():
    return {
        "launcher_update_check": [
            "build_launcher_update_status",
            "build_launcher_update_check",
            "build_launcher_update_source_recovery_cleanup_proof",
            "build_launcher_update_normal_source_restoration_readiness",
            "build_launcher_update_normal_source_candidate_verification_proof",
            "build_launcher_update_source_regeneration_candidate_verification_restore_proof",
            "build_launcher_update_source_regeneration_live_source_restoration_closeout_proof",
            "build_launcher_update_real_source_restoration_execution_regression_boundary_proof",
            "build_launcher_update_current_vault_source_restoration_closeout_readiness",
            "build_launcher_update_source_candidate_inventory_wrapper_removal_preflight",
            "build_launcher_update_authoritative_normal_source_candidate_supply_packet",
            "required_update_authoritative_normal_source_candidate_supply_operator_statement",
            "build_launcher_update_authoritative_source_candidate_import_boundary_proof",
            "required_update_authoritative_source_candidate_import_operator_statement",
            "build_launcher_update_real_authoritative_source_candidate_supply_readiness",
            "build_launcher_update_real_authoritative_source_candidate_materialization_proof",
            "required_update_real_authoritative_source_candidate_materialization_operator_statement",
            "build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof",
            "required_update_real_authoritative_source_candidate_import_from_materialization_operator_statement",
            "build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof",
            "required_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_operator_statement",
            "build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof",
            "required_update_current_vault_wrapper_removal_from_materialization_import_operator_statement",
            "build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof",
            "required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement",
            "build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof",
            "build_launcher_update_production_primary_closeout_after_source_recovery_proof",
            "build_launcher_update_final_production_auto_update_closeout_audit",
            "build_launcher_update_governed_live_completion_evidence_packet",
            "required_update_governed_live_completion_evidence_operator_statement",
            "build_launcher_update_controlled_live_installer_evidence_runner",
            "required_update_controlled_live_installer_evidence_runner_operator_statement",
            "build_launcher_update_approved_live_evidence_runner_adapter",
            "required_update_approved_live_evidence_runner_adapter_operator_statement",
            "build_launcher_update_approved_live_evidence_runner_real_dry_run",
            "required_update_approved_live_evidence_runner_real_dry_run_operator_statement",
            "build_launcher_update_live_receipt_digest_consistency_closeout",
            "build_launcher_update_real_live_receipt_capture_boundary",
            "required_update_real_live_receipt_capture_boundary_operator_statement",
            "build_launcher_update_real_live_receipt_bundle_production_runner",
            "required_update_real_live_receipt_bundle_production_runner_operator_statement",
            "build_launcher_update_production_runner_final_closeout_bridge",
            "build_launcher_update_approved_production_runner_real_evidence_capture",
            "required_update_approved_production_runner_real_evidence_capture_operator_statement",
            "build_launcher_update_installer_real_artifact_build_output_capture",
            "build_launcher_update_dist_artifact_isolation_cohabitation_proof",
            "build_launcher_update_signed_artifact_verification_closeout",
            "build_launcher_update_local_installer_disposable_dry_run_proof",
            "build_launcher_update_local_manifest_background_prompt_settings_action",
            "build_launcher_update_local_release_channel_blocker_closeout",
            "build_launcher_update_authoritative_candidate_supply_verification_after_import_proof",
            "build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof",
            "required_update_current_vault_wrapper_removal_after_import_operator_statement",
            "build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof",
            "required_update_current_vault_wrapper_removal_operator_statement",
            "build_launcher_update_production_primary_relaunch_receipt_boundary_proof",
        ],
        "studio_shell_api": [
            "class StudioAPI",
            "get_launcher_update_source_recovery_cleanup_proof",
            "get_launcher_update_normal_source_restoration_readiness",
            "get_launcher_update_normal_source_candidate_verification_proof",
            "get_launcher_update_source_regeneration_candidate_verification_restore_proof",
            "get_launcher_update_source_regeneration_live_source_restoration_closeout_proof",
            "get_launcher_update_real_source_restoration_execution_regression_boundary_proof",
            "get_launcher_update_current_vault_source_restoration_closeout_readiness",
            "get_launcher_update_source_candidate_inventory_wrapper_removal_preflight",
            "get_launcher_update_authoritative_normal_source_candidate_supply_packet",
            "get_launcher_update_authoritative_source_candidate_import_boundary_proof",
            "get_launcher_update_real_authoritative_source_candidate_supply_readiness",
            "get_launcher_update_real_authoritative_source_candidate_materialization_proof",
            "get_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof",
            "get_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof",
            "get_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof",
            "get_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof",
            "get_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof",
            "get_launcher_update_production_primary_closeout_after_source_recovery_proof",
            "get_launcher_update_final_production_auto_update_closeout_audit",
            "get_launcher_update_governed_live_completion_evidence_packet",
            "get_launcher_update_controlled_live_installer_evidence_runner",
            "get_launcher_update_approved_live_evidence_runner_adapter",
            "get_launcher_update_approved_live_evidence_runner_real_dry_run",
            "get_launcher_update_live_receipt_digest_consistency_closeout",
            "get_launcher_update_real_live_receipt_capture_boundary",
            "get_launcher_update_real_live_receipt_bundle_production_runner",
            "get_launcher_update_production_runner_final_closeout_bridge",
            "get_launcher_update_approved_production_runner_real_evidence_capture",
            "get_launcher_update_installer_real_artifact_build_output_capture",
            "get_launcher_update_dist_artifact_isolation_cohabitation_proof",
            "get_launcher_update_signed_artifact_verification_closeout",
            "get_launcher_update_local_installer_disposable_dry_run_proof",
            "get_launcher_update_local_manifest_background_prompt_settings_action",
            "get_launcher_update_local_release_channel_blocker_closeout",
            "get_launcher_update_authoritative_candidate_supply_verification_after_import_proof",
            "get_launcher_update_current_vault_wrapper_removal_after_import_execution_proof",
            "get_launcher_update_current_vault_wrapper_removal_executor_boundary_proof",
            "get_launcher_update_production_primary_relaunch_receipt_boundary_proof",
        ],
        "studio_shell_test_pass10a": [
            "TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell",
            "test_api_returns_source_recovery_cleanup_proof_envelope",
            "test_api_returns_normal_source_restoration_readiness_envelope",
            "test_api_returns_normal_source_candidate_verification_proof_envelope",
            "test_api_returns_source_regeneration_candidate_verification_restore_envelope",
            "test_api_returns_source_regeneration_live_source_restoration_closeout_envelope",
            "test_api_returns_real_source_restoration_execution_regression_boundary_envelope",
            "test_api_returns_current_vault_source_restoration_closeout_readiness_envelope",
            "test_api_returns_source_candidate_inventory_wrapper_removal_preflight_envelope",
            "test_api_returns_authoritative_normal_source_candidate_supply_packet_envelope",
            "test_api_returns_authoritative_source_candidate_import_boundary_envelope",
            "test_api_returns_real_authoritative_source_candidate_supply_readiness_envelope",
            "test_api_returns_real_authoritative_source_candidate_materialization_envelope",
            "test_api_returns_real_authoritative_source_candidate_import_from_materialization_envelope",
            "test_api_returns_real_authoritative_source_candidate_supply_verification_from_materialization_import_envelope",
            "test_api_returns_current_vault_wrapper_removal_from_materialization_import_execution_envelope",
            "test_api_returns_post_wrapper_removal_regression_from_materialization_import_envelope",
            "test_api_returns_current_vault_source_closeout_from_materialization_import_regression_envelope",
            "test_api_returns_production_primary_closeout_after_source_recovery_envelope",
            "test_api_returns_final_production_auto_update_closeout_audit_envelope",
            "test_api_returns_governed_live_completion_evidence_packet_envelope",
            "test_api_returns_controlled_live_installer_evidence_runner_envelope",
            "test_api_returns_approved_live_evidence_runner_adapter_envelope",
            "test_api_returns_approved_live_evidence_runner_real_dry_run_envelope",
            "test_api_returns_live_receipt_digest_consistency_closeout_envelope",
            "test_api_returns_real_live_receipt_capture_boundary_envelope",
            "test_api_returns_real_live_receipt_bundle_production_runner_envelope",
            "test_api_returns_production_runner_final_closeout_bridge_envelope",
            "test_api_returns_approved_production_runner_real_evidence_capture_envelope",
            "test_api_returns_installer_real_artifact_build_output_capture_envelope",
            "test_api_returns_dist_artifact_isolation_cohabitation_envelope",
            "test_api_returns_signed_artifact_verification_closeout_envelope",
            "test_api_returns_local_installer_disposable_dry_run_envelope",
            "test_api_returns_local_manifest_background_prompt_settings_action_envelope",
            "test_api_returns_local_release_channel_blocker_closeout_envelope",
            "test_api_returns_authoritative_candidate_supply_verification_after_import_envelope",
            "test_api_returns_current_vault_wrapper_removal_after_import_execution_envelope",
            "test_api_returns_current_vault_wrapper_removal_executor_boundary_envelope",
        ],
    }


def _extension_path_is_relative_to(path, root):
    try:
        _Path(path).resolve().relative_to(_Path(root).resolve())
        return True
    except ValueError:
        return False
    except OSError:
        return False


def _normal_source_candidate_verification_descriptor(
    *,
    vault,
    role,
    path,
    required_symbols,
):
    candidate_path = _Path(path) if path else _Path()
    descriptor = {
        "role": role,
        "path": str(path or ""),
        "resolved_path": "",
        "exists": bool(path) and candidate_path.exists(),
        "is_file": False,
        "inside_vault_root": False,
        "extension_allowed": False,
        "size_bytes": 0,
        "sha256": "",
        "text_readable": False,
        "ast_parse_ok": False,
        "wrapper_tokens_present": [],
        "required_symbols": list(required_symbols),
        "missing_required_symbols": list(required_symbols),
        "candidate_verification_passed": False,
        "candidate_status": "missing",
        "errors": [],
    }
    if not path:
        descriptor["errors"].append("candidate_path_required")
        return descriptor
    if not candidate_path.exists():
        descriptor["errors"].append("candidate_path_missing")
        return descriptor

    try:
        resolved = candidate_path.resolve()
    except OSError:
        resolved = candidate_path
    descriptor["resolved_path"] = str(resolved)
    descriptor["inside_vault_root"] = _extension_path_is_relative_to(resolved, vault)
    if not descriptor["inside_vault_root"]:
        descriptor["errors"].append("candidate_path_outside_vault_root")
    descriptor["is_file"] = candidate_path.is_file()
    if not descriptor["is_file"]:
        descriptor["errors"].append("candidate_path_not_file")
    descriptor["extension_allowed"] = candidate_path.suffix.lower() == ".py"
    if not descriptor["extension_allowed"]:
        descriptor["errors"].append("candidate_extension_not_py")
    if descriptor["errors"]:
        descriptor["candidate_status"] = "invalid_path"
        return descriptor

    payload = candidate_path.read_bytes()
    descriptor["size_bytes"] = len(payload)
    descriptor["sha256"] = _wrapper_hashlib.sha256(payload).hexdigest()
    text = payload.decode("utf-8", errors="replace")
    descriptor["text_readable"] = True
    wrapper_tokens = [
        "exec(_RECOVERED_BYTECODE_CODE, globals())",
        "_RECOVERED_BYTECODE_PATH",
        "marshal as _marshal",
    ]
    present_wrapper_tokens = [token for token in wrapper_tokens if token in text]
    descriptor["wrapper_tokens_present"] = present_wrapper_tokens
    if present_wrapper_tokens:
        descriptor["errors"].append("candidate_contains_recovery_wrapper_tokens")

    try:
        _extension_ast.parse(text, filename=str(resolved))
        descriptor["ast_parse_ok"] = True
    except SyntaxError as exc:
        descriptor["errors"].append(f"candidate_ast_parse_failed:{exc.msg}")

    missing_symbols = [token for token in required_symbols if token not in text]
    descriptor["missing_required_symbols"] = missing_symbols
    if missing_symbols:
        descriptor["errors"].append("candidate_missing_required_symbols")

    if descriptor["errors"]:
        descriptor["candidate_status"] = "failed_verification"
        return descriptor

    descriptor["candidate_verification_passed"] = True
    descriptor["candidate_status"] = "verified_normal_source_candidate"
    return descriptor


def _normal_source_candidate_role_paths(candidate_paths, role):
    if not candidate_paths:
        return []
    value = candidate_paths.get(role) if isinstance(candidate_paths, dict) else None
    if not value:
        return []
    if isinstance(value, (str, _Path)):
        return [value]
    return list(value)


def required_update_normal_source_candidate_verification_operator_statement(
    candidate_set,
):
    digest = str(
        (candidate_set or {}).get("candidate_set_digest_sha256")
        or _extension_digest_without(candidate_set or {}, "candidate_set_digest_sha256")
    )
    return f"{NORMAL_SOURCE_CANDIDATE_VERIFICATION_OPERATOR_STATEMENT_PREFIX} {digest}"


def build_launcher_update_normal_source_candidate_verification_proof(
    vault_root,
    *,
    candidate_paths=None,
    required_symbols_by_role=None,
    operator_approved_candidate_verification=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    source_readiness = build_launcher_update_normal_source_restoration_readiness(
        vault,
        generated_at=timestamp,
    )
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    roles = [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]
    candidates = {}
    role_readiness = {}
    errors = []
    warnings = []
    for role in roles:
        role_paths = _normal_source_candidate_role_paths(candidate_paths, role)
        if not role_paths:
            descriptor = _normal_source_candidate_verification_descriptor(
                vault=vault,
                role=role,
                path="",
                required_symbols=required_symbols.get(role, []),
            )
            candidates[role] = [descriptor]
        else:
            candidates[role] = [
                _normal_source_candidate_verification_descriptor(
                    vault=vault,
                    role=role,
                    path=path,
                    required_symbols=required_symbols.get(role, []),
                )
                for path in role_paths
            ]
        role_ready = any(
            item.get("candidate_verification_passed")
            for item in candidates.get(role, [])
        )
        role_readiness[role] = role_ready
        if not role_ready:
            errors.append(f"{role}_candidate_verification_required")

    candidate_set_complete = all(role_readiness.values())
    candidate_set = {
        "schema_version": NORMAL_SOURCE_CANDIDATE_VERIFICATION_SCHEMA_VERSION,
        "surface": NORMAL_SOURCE_CANDIDATE_VERIFICATION_SURFACE_ID,
        "candidate_roles": roles,
        "role_readiness": role_readiness,
        "candidate_set_complete": candidate_set_complete,
        "required_symbols_by_role": required_symbols,
        "candidates": candidates,
        "source_readiness_status": source_readiness.get("status"),
        "current_source_wrappers_active": bool(
            source_readiness.get("current_source_wrappers_active")
        ),
    }
    candidate_set["candidate_set_digest_sha256"] = _extension_digest_without(
        candidate_set,
        "candidate_set_digest_sha256",
    )
    required_statement = (
        required_update_normal_source_candidate_verification_operator_statement(
            candidate_set
        )
    )
    operator_statement_matched = bool(
        operator_approved_candidate_verification
        and str(operator_statement) == required_statement
    )
    if not operator_approved_candidate_verification:
        errors.append("operator_candidate_verification_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_candidate_verification_statement_mismatch")
    if source_readiness.get("current_source_wrappers_active"):
        warnings.append("current_source_wrappers_still_active")

    verification_ready = bool(candidate_set_complete and operator_statement_matched)
    status = "launcher_update_normal_source_candidate_verification_blocked"
    if candidate_set_complete and not operator_statement_matched:
        status = "launcher_update_normal_source_candidate_verification_pending_approval"
    if verification_ready:
        status = "launcher_update_normal_source_candidate_verification_ready"

    proof = {
        "ok": verification_ready,
        "surface": NORMAL_SOURCE_CANDIDATE_VERIFICATION_SURFACE_ID,
        "schema_version": NORMAL_SOURCE_CANDIDATE_VERIFICATION_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "source_restoration_candidate_verification_ready": verification_ready,
        "candidate_set_complete": candidate_set_complete,
        "role_readiness": role_readiness,
        "candidates": candidates,
        "normal_source_restoration_ready": False,
        "source_replacement_performed": False,
        "source_write_enabled": False,
        "source_rewrite_from_bytecode_performed": False,
        "decompiler_execution_performed": False,
        "final_auto_update_closeout_blocked": True,
        "production_auto_update_complete": False,
        "candidate_set": candidate_set,
        "source_readiness": {
            "status": source_readiness.get("status"),
            "normal_source_restoration_ready": bool(
                source_readiness.get("normal_source_restoration_ready")
            ),
            "final_auto_update_closeout_blocked": bool(
                source_readiness.get("final_auto_update_closeout_blocked")
            ),
        },
        "authority": _authority(
            normal_source_candidate_verification_proof_built=True,
            normal_source_candidate_verification_ready=verification_ready,
            normal_source_candidate_verification_source_replacement_performed=False,
            normal_source_candidate_verification_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["normal_source_candidate_verification_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "normal_source_candidate_verification_digest_sha256",
        )
    )
    return proof


def build_launcher_update_source_regeneration_candidate_verification_restore_proof(
    vault_root,
    *,
    source_regeneration_runner_boundary_proof=None,
    restore_root=None,
    restore_targets_by_role=None,
    required_symbols_by_role=None,
    operator_approved_candidate_verification=False,
    candidate_verification_statement="",
    operator_approved_restore=False,
    restore_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    if source_regeneration_runner_boundary_proof is None:
        source_regeneration_runner_boundary_proof = (
            build_launcher_update_source_regeneration_runner_boundary_proof(
                vault,
                generated_at=timestamp,
            )
        )
    runner_proof = _extension_unwrap_api_data(
        source_regeneration_runner_boundary_proof,
        "launcher_update_source_regeneration_runner_boundary_proof",
    )
    runner_proof = _extension_unwrap_api_data(
        runner_proof or {},
        SOURCE_REGENERATION_RUNNER_BOUNDARY_SURFACE_ID,
    )
    if not isinstance(runner_proof, dict):
        runner_proof = {}

    errors = []
    warnings = []
    if runner_proof.get("warnings"):
        warnings.extend(str(item) for item in runner_proof.get("warnings") or [])
    if not runner_proof:
        errors.append("source_regeneration_runner_boundary_proof_required")
    elif runner_proof.get("surface") != SOURCE_REGENERATION_RUNNER_BOUNDARY_SURFACE_ID:
        errors.append("source_regeneration_runner_boundary_surface_mismatch")

    runner_digest = str(
        runner_proof.get("source_regeneration_runner_boundary_digest_sha256") or ""
    )
    computed_runner_digest = (
        _extension_digest_without(
            runner_proof,
            "source_regeneration_runner_boundary_digest_sha256",
        )
        if runner_proof
        else ""
    )
    runner_digest_matched = bool(
        runner_digest and runner_digest == computed_runner_digest
    )
    if runner_proof and not runner_digest_matched:
        errors.append("source_regeneration_runner_boundary_digest_mismatch")

    runner_candidates_written = bool(
        runner_proof.get("ok")
        and runner_proof.get("status")
        == "launcher_update_source_regeneration_runner_candidates_written"
        and runner_proof.get("source_regeneration_output_written")
        and runner_proof.get("candidate_set_complete")
    )
    if runner_proof and not runner_candidates_written:
        errors.append("source_regeneration_runner_candidates_required")

    generated_candidate_paths = (
        runner_proof.get("generated_candidate_paths")
        if isinstance(runner_proof.get("generated_candidate_paths"), dict)
        else {}
    )
    if runner_candidates_written and not generated_candidate_paths:
        errors.append("source_regeneration_generated_candidate_paths_required")

    required_symbols = (
        required_symbols_by_role
        or (runner_proof.get("execution_plan") or {}).get("required_symbols_by_role")
        or _normal_source_candidate_default_required_symbols()
    )
    candidate_verification_preview = {}
    candidate_verification_proof = {}
    candidate_set_complete = False
    candidate_verification_ready = False
    required_candidate_verification_statement = ""
    candidate_verification_statement_matched = False

    candidates_ready_for_verification = bool(
        runner_candidates_written and runner_digest_matched and generated_candidate_paths
    )
    if candidates_ready_for_verification:
        candidate_verification_preview = (
            build_launcher_update_normal_source_candidate_verification_proof(
                vault,
                candidate_paths=generated_candidate_paths,
                required_symbols_by_role=required_symbols,
                generated_at=timestamp,
            )
        )
        candidate_set_complete = bool(
            candidate_verification_preview.get("candidate_set_complete")
        )
        required_candidate_verification_statement = str(
            candidate_verification_preview.get("required_operator_statement") or ""
        )
        candidate_verification_statement_matched = bool(
            operator_approved_candidate_verification
            and str(candidate_verification_statement)
            == required_candidate_verification_statement
        )
        if not candidate_set_complete:
            errors.append("source_regeneration_generated_candidates_not_verifiable")
        if not operator_approved_candidate_verification:
            errors.append("source_regeneration_candidate_verification_approval_required")
        elif not candidate_verification_statement_matched:
            errors.append("source_regeneration_candidate_verification_statement_mismatch")

        if candidate_verification_statement_matched:
            candidate_verification_proof = (
                build_launcher_update_normal_source_candidate_verification_proof(
                    vault,
                    candidate_paths=generated_candidate_paths,
                    required_symbols_by_role=required_symbols,
                    operator_approved_candidate_verification=True,
                    operator_statement=candidate_verification_statement,
                    generated_at=timestamp,
                )
            )
            candidate_verification_ready = bool(
                candidate_verification_proof.get("ok")
                and candidate_verification_proof.get(
                    "source_restoration_candidate_verification_ready"
                )
            )
            if not candidate_verification_ready:
                errors.append("source_regeneration_candidate_verification_not_ready")
        else:
            candidate_verification_proof = candidate_verification_preview

    restore_root_explicit = restore_root is not None
    resolved_restore_root = _Path(restore_root).resolve() if restore_root else _Path()
    restore_root_is_live_vault = bool(
        restore_root_explicit and resolved_restore_root == vault
    )
    restore_preview = {}
    restore_executor_proof = {}
    required_restore_statement = ""
    restore_plan_ready = False
    restore_statement_matched = False
    source_write_performed = False

    if candidate_verification_ready:
        if not restore_root_explicit:
            errors.append("source_regeneration_candidate_restore_root_required")
        else:
            restore_preview = (
                build_launcher_update_normal_source_candidate_restore_executor_proof(
                    vault,
                    candidate_verification_proof=candidate_verification_proof,
                    restore_root=resolved_restore_root,
                    restore_targets_by_role=restore_targets_by_role,
                    required_symbols_by_role=required_symbols,
                    generated_at=timestamp,
                )
            )
            required_restore_statement = str(
                restore_preview.get("required_operator_statement") or ""
            )
            restore_plan_ready = bool(restore_preview.get("restore_plan_ready"))
            restore_statement_matched = bool(
                operator_approved_restore
                and str(restore_statement) == required_restore_statement
            )
            if not restore_plan_ready:
                errors.append("source_regeneration_candidate_restore_plan_not_ready")
            if not operator_approved_restore:
                errors.append("source_regeneration_candidate_restore_approval_required")
            elif not restore_statement_matched:
                errors.append("source_regeneration_candidate_restore_statement_mismatch")

            if restore_statement_matched:
                restore_executor_proof = (
                    build_launcher_update_normal_source_candidate_restore_executor_proof(
                        vault,
                        candidate_verification_proof=candidate_verification_proof,
                        restore_root=resolved_restore_root,
                        restore_targets_by_role=restore_targets_by_role,
                        required_symbols_by_role=required_symbols,
                        operator_approved_restore=True,
                        operator_statement=restore_statement,
                        generated_at=timestamp,
                    )
                )
                source_write_performed = bool(
                    restore_executor_proof.get("source_write_performed")
                )
                if not source_write_performed:
                    errors.append("source_regeneration_candidate_restore_failed")
            else:
                restore_executor_proof = restore_preview

    live_source_write_performed = bool(
        source_write_performed and restore_root_is_live_vault
    )
    status = "launcher_update_source_regeneration_candidate_restore_blocked"
    if candidates_ready_for_verification and not candidate_verification_ready:
        status = (
            "launcher_update_source_regeneration_candidate_restore_"
            "pending_candidate_verification_approval"
        )
    if (
        candidate_verification_ready
        and restore_root_explicit
        and restore_plan_ready
        and not restore_statement_matched
    ):
        status = (
            "launcher_update_source_regeneration_candidate_restore_"
            "pending_restore_approval"
        )
    if source_write_performed:
        status = (
            "launcher_update_source_regeneration_candidate_restore_live_source_restored"
            if live_source_write_performed
            else "launcher_update_source_regeneration_candidate_restore_fixture_restored"
        )

    proof = {
        "ok": source_write_performed,
        "surface": SOURCE_REGENERATION_CANDIDATE_RESTORE_SURFACE_ID,
        "schema_version": SOURCE_REGENERATION_CANDIDATE_RESTORE_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "runner_boundary_status": runner_proof.get("status", ""),
        "runner_boundary_digest_sha256": runner_digest,
        "runner_boundary_digest_matched": runner_digest_matched,
        "runner_candidates_written": runner_candidates_written,
        "generated_candidate_paths": generated_candidate_paths,
        "required_symbols_by_role": required_symbols,
        "candidate_verification_preview": candidate_verification_preview,
        "candidate_verification_proof": candidate_verification_proof,
        "candidate_set_complete": candidate_set_complete,
        "candidate_verification_ready": candidate_verification_ready,
        "required_candidate_verification_statement": (
            required_candidate_verification_statement
        ),
        "candidate_verification_statement_matched": (
            candidate_verification_statement_matched
        ),
        "restore_root": str(resolved_restore_root) if restore_root_explicit else "",
        "restore_root_is_live_vault": restore_root_is_live_vault,
        "restore_preview": restore_preview,
        "restore_executor_proof": restore_executor_proof,
        "restore_plan_ready": restore_plan_ready,
        "required_restore_statement": required_restore_statement,
        "restore_statement_matched": restore_statement_matched,
        "source_regeneration_execution_performed": False,
        "source_regeneration_runner_execution_previously_performed": bool(
            runner_proof.get("runner_execution_performed")
        ),
        "source_regeneration_output_written": False,
        "source_regeneration_output_previously_written": bool(
            runner_proof.get("source_regeneration_output_written")
        ),
        "source_restore_performed": source_write_performed,
        "source_write_performed": source_write_performed,
        "live_source_write_performed": live_source_write_performed,
        "source_file_replacement_performed": source_write_performed,
        "source_rewrite_from_bytecode_performed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": "restore_verified_normal_source_or_remove_wrapper_modules",
        "authority": _authority(
            source_regeneration_candidate_restore_chain_built=True,
            source_regeneration_candidate_verification_ready=candidate_verification_ready,
            source_regeneration_candidate_restore_performed=source_write_performed,
            source_regeneration_candidate_live_source_write_performed=(
                live_source_write_performed
            ),
            source_regeneration_candidate_restore_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["source_regeneration_candidate_restore_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "source_regeneration_candidate_restore_digest_sha256",
        )
    )
    return proof


def _normal_source_candidate_restore_default_targets():
    return {
        "launcher_update_check": "runtime/studio/launcher_update_check.py",
        "studio_shell_api": "runtime/studio/shell/api.py",
        "studio_shell_test_pass10a": "runtime/studio/shell/test_pass10a_shell.py",
    }


def _source_recovery_wrapper_tokens():
    return [
        "_RECOVERED_BYTECODE_PATH",
        "_RECOVERED_BYTECODE_CODE",
        "exec(_RECOVERED_BYTECODE_CODE, globals())",
        "_RECOVERED_TEST_BYTECODE_PATH",
        "_RECOVERED_TEST_CODE",
        "exec(_RECOVERED_TEST_CODE, globals())",
        "_marshal.loads(",
    ]


def _live_source_restoration_target_paths(vault, restore_targets_by_role=None):
    target_values = _normal_source_candidate_restore_targets(
        vault,
        restore_targets_by_role,
    )
    targets = {}
    for role, target_value in target_values.items():
        target_path = _Path(target_value)
        targets[role] = (
            target_path.resolve()
            if target_path.is_absolute()
            else (vault / target_path).resolve()
        )
    return targets


def _live_source_restoration_target_descriptor(
    *,
    vault,
    role,
    path,
    required_symbols,
):
    descriptor = _normal_source_candidate_verification_descriptor(
        vault=vault,
        role=role,
        path=path,
        required_symbols=required_symbols,
    )
    text = ""
    if descriptor.get("exists") and descriptor.get("is_file"):
        try:
            text = _Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    wrapper_tokens_present = [
        token for token in _source_recovery_wrapper_tokens() if token in text
    ]
    descriptor["recovery_wrapper_tokens_present"] = wrapper_tokens_present
    descriptor["recovery_wrapper_present"] = bool(wrapper_tokens_present)
    descriptor["live_source_file_ready"] = bool(
        descriptor.get("candidate_verification_passed")
        and not descriptor.get("recovery_wrapper_present")
    )
    if descriptor["recovery_wrapper_present"]:
        descriptor["errors"].append("live_source_contains_recovery_wrapper_tokens")
        descriptor["candidate_status"] = "recovery_wrapper_still_active"
        descriptor["candidate_verification_passed"] = False
        descriptor["live_source_file_ready"] = False
    return descriptor


def build_launcher_update_source_regeneration_live_source_restoration_closeout_proof(
    vault_root,
    *,
    source_regeneration_candidate_restore_proof=None,
    restore_targets_by_role=None,
    required_symbols_by_role=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    if source_regeneration_candidate_restore_proof is None:
        source_regeneration_candidate_restore_proof = (
            build_launcher_update_source_regeneration_candidate_verification_restore_proof(
                vault,
                generated_at=timestamp,
            )
        )

    restore_proof = _extension_unwrap_api_data(
        source_regeneration_candidate_restore_proof,
        "launcher_update_source_regeneration_candidate_verification_restore_proof",
    )
    restore_proof = _extension_unwrap_api_data(
        restore_proof or {},
        SOURCE_REGENERATION_CANDIDATE_RESTORE_SURFACE_ID,
    )
    if not isinstance(restore_proof, dict):
        restore_proof = {}

    errors = []
    warnings = []
    if restore_proof.get("warnings"):
        warnings.extend(str(item) for item in restore_proof.get("warnings") or [])
    if not restore_proof:
        errors.append("source_regeneration_candidate_restore_proof_required")
    elif restore_proof.get("surface") != SOURCE_REGENERATION_CANDIDATE_RESTORE_SURFACE_ID:
        errors.append("source_regeneration_candidate_restore_surface_mismatch")

    restore_digest = str(
        restore_proof.get("source_regeneration_candidate_restore_digest_sha256") or ""
    )
    computed_restore_digest = (
        _extension_digest_without(
            restore_proof,
            "source_regeneration_candidate_restore_digest_sha256",
        )
        if restore_proof
        else ""
    )
    restore_digest_matched = bool(
        restore_digest and restore_digest == computed_restore_digest
    )
    if restore_proof and not restore_digest_matched:
        errors.append("source_regeneration_candidate_restore_digest_mismatch")

    live_restore_proof_ready = bool(
        restore_proof.get("ok")
        and restore_proof.get("source_restore_performed")
        and restore_proof.get("source_write_performed")
        and restore_proof.get("live_source_write_performed")
        and restore_digest_matched
    )
    if restore_proof and not live_restore_proof_ready:
        errors.append("source_regeneration_candidate_restore_proof_not_live")

    required_symbols = (
        required_symbols_by_role
        or restore_proof.get("required_symbols_by_role")
        or _normal_source_candidate_default_required_symbols()
    )
    target_paths = _live_source_restoration_target_paths(
        vault,
        restore_targets_by_role,
    )
    target_readiness = {}
    for role, path in target_paths.items():
        descriptor = _live_source_restoration_target_descriptor(
            vault=vault,
            role=role,
            path=path,
            required_symbols=required_symbols.get(role, []),
        )
        target_readiness[role] = descriptor
        if not descriptor.get("live_source_file_ready"):
            errors.append(f"{role}_live_source_file_not_ready")

    wrapper_removal_verified = bool(
        target_readiness
        and all(
            item.get("live_source_file_ready")
            and not item.get("recovery_wrapper_present")
            for item in target_readiness.values()
        )
    )
    live_source_restoration_verified = bool(
        live_restore_proof_ready and wrapper_removal_verified
    )

    status = "launcher_update_source_regeneration_live_source_restoration_closeout_blocked"
    if live_restore_proof_ready and not wrapper_removal_verified:
        status = (
            "launcher_update_source_regeneration_live_source_restoration_"
            "closeout_wrapper_removal_required"
        )
    if live_source_restoration_verified:
        status = (
            "launcher_update_source_regeneration_live_source_restoration_"
            "closeout_verified"
        )

    proof = {
        "ok": live_source_restoration_verified,
        "surface": SOURCE_REGENERATION_LIVE_SOURCE_RESTORATION_CLOSEOUT_SURFACE_ID,
        "schema_version": (
            SOURCE_REGENERATION_LIVE_SOURCE_RESTORATION_CLOSEOUT_SCHEMA_VERSION
        ),
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "source_regeneration_candidate_restore_status": restore_proof.get("status", ""),
        "source_regeneration_candidate_restore_digest_sha256": restore_digest,
        "source_regeneration_candidate_restore_digest_matched": restore_digest_matched,
        "live_restore_proof_ready": live_restore_proof_ready,
        "target_paths": {
            role: str(path) for role, path in target_paths.items()
        },
        "target_readiness": target_readiness,
        "wrapper_removal_verified": wrapper_removal_verified,
        "live_source_restoration_verified": live_source_restoration_verified,
        "source_regeneration_execution_performed": False,
        "source_regeneration_output_written": False,
        "source_restore_performed": False,
        "source_restore_previously_performed": bool(
            restore_proof.get("source_restore_performed")
        ),
        "source_write_performed": False,
        "source_write_previously_performed": bool(
            restore_proof.get("source_write_performed")
        ),
        "live_source_write_performed": False,
        "live_source_write_previously_performed": bool(
            restore_proof.get("live_source_write_performed")
        ),
        "source_file_replacement_performed": False,
        "source_file_replacement_previously_performed": bool(
            restore_proof.get("source_file_replacement_performed")
        ),
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_full_post_restore_regression_then_resume_primary_exe_closeout"
            if live_source_restoration_verified
            else "perform_live_source_restore_with_verified_candidates"
        ),
        "authority": _authority(
            source_regeneration_live_source_restoration_closeout_built=True,
            source_regeneration_live_source_restoration_verified=(
                live_source_restoration_verified
            ),
            source_regeneration_live_source_wrappers_removed=wrapper_removal_verified,
            source_regeneration_live_source_closeout_source_write_performed=False,
            source_regeneration_live_source_closeout_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["source_regeneration_live_source_restoration_closeout_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "source_regeneration_live_source_restoration_closeout_digest_sha256",
        )
    )
    return proof


def _real_source_restoration_regression_command_plan():
    return [
        {
            "id": "py_compile_touched_updater_files",
            "command": (
                "python -m py_compile "
                "runtime\\studio\\launcher_update_check.py "
                "runtime\\studio\\shell\\api.py "
                "runtime\\studio\\shell\\panel_registry.py "
                "runtime\\studio\\settings_runtime_controls_panel.py "
                "runtime\\studio\\test_launcher_update_check.py "
                "runtime\\studio\\shell\\test_pass10a_shell.py"
            ),
            "required_exit_code": 0,
        },
        {
            "id": "launcher_source_recovery_slice",
            "command": (
                "pytest runtime\\studio\\test_launcher_update_check.py -q "
                "-k \"source_regeneration or real_source_restoration or "
                "normal_source_candidate or normal_source_restoration or "
                "source_recovery_cleanup\""
            ),
            "required_exit_code": 0,
        },
        {
            "id": "shell_source_recovery_slice",
            "command": (
                "pytest runtime\\studio\\shell\\test_pass10a_shell.py -q "
                "-k \"source_regeneration or real_source_restoration or "
                "normal_source_candidate or normal_source_restoration or "
                "source_recovery or panel_registry\""
            ),
            "required_exit_code": 0,
        },
        {
            "id": "settings_runtime_controls",
            "command": "pytest runtime\\studio\\test_settings_runtime_controls_panel.py -q",
            "required_exit_code": 0,
        },
    ]


def _real_source_restoration_regression_evidence_descriptor(
    regression_evidence,
    command_plan,
):
    evidence = regression_evidence or {}
    if not isinstance(evidence, dict):
        evidence = {}
    raw_entries = evidence.get("commands", evidence)
    if isinstance(raw_entries, list):
        entries = {
            str(item.get("id") or ""): item
            for item in raw_entries
            if isinstance(item, dict)
        }
    elif isinstance(raw_entries, dict):
        entries = raw_entries
    else:
        entries = {}

    command_results = {}
    missing = []
    mismatched = []
    failed = []
    for command in command_plan:
        command_id = command["id"]
        raw = entries.get(command_id)
        if not isinstance(raw, dict):
            raw = {}
        command_matched = str(raw.get("command") or "") == command["command"]
        exit_code_ok = raw.get("exit_code") == command["required_exit_code"]
        passed = bool(raw.get("passed")) is True
        present = bool(raw)
        if not present:
            missing.append(command_id)
        elif not command_matched:
            mismatched.append(command_id)
        elif not exit_code_ok or not passed:
            failed.append(command_id)
        command_results[command_id] = {
            "id": command_id,
            "expected_command": command["command"],
            "reported_command": str(raw.get("command") or ""),
            "required_exit_code": command["required_exit_code"],
            "reported_exit_code": raw.get("exit_code"),
            "passed": passed,
            "present": present,
            "command_matched": command_matched,
            "exit_code_ok": exit_code_ok,
            "verified": bool(present and command_matched and exit_code_ok and passed),
        }

    verified = bool(
        command_plan
        and not missing
        and not mismatched
        and not failed
        and all(item["verified"] for item in command_results.values())
    )
    return {
        "schema_version": REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SCHEMA_VERSION,
        "surface": REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SURFACE_ID,
        "evidence_supplied": bool(regression_evidence),
        "expected_command_ids": [item["id"] for item in command_plan],
        "command_results": command_results,
        "missing_command_ids": missing,
        "mismatched_command_ids": mismatched,
        "failed_command_ids": failed,
        "regression_evidence_verified": verified,
    }


def _post_wrapper_removal_regression_from_materialization_import_command_plan():
    return [
        {
            "id": "py_compile_updater_runtime_and_tests",
            "command": (
                "python -m py_compile "
                "runtime\\studio\\launcher_update_check.py "
                "runtime\\studio\\shell\\api.py "
                "runtime\\studio\\shell\\panel_registry.py "
                "runtime\\studio\\settings_runtime_controls_panel.py "
                "runtime\\studio\\test_launcher_update_check.py "
                "runtime\\studio\\shell\\test_pass10a_shell.py "
                "runtime\\studio\\test_settings_runtime_controls_panel.py"
            ),
            "required_exit_code": 0,
        },
        {
            "id": "launcher_materialization_import_wrapper_regression",
            "command": (
                "python -m pytest runtime\\studio\\test_launcher_update_check.py -q "
                "-k \"post_wrapper_removal_regression_from_materialization_import "
                "or wrapper_removal_from_materialization_import "
                "or real_authoritative_source_candidate_supply_verification_from_materialization_import\""
            ),
            "required_exit_code": 0,
        },
        {
            "id": "shell_materialization_import_api_registry",
            "command": (
                "python -m pytest runtime\\studio\\shell\\test_pass10a_shell.py -q "
                "-k \"post_wrapper_removal_regression_from_materialization_import "
                "or wrapper_removal_from_materialization_import or panel_registry\""
            ),
            "required_exit_code": 0,
        },
        {
            "id": "settings_runtime_controls",
            "command": "python -m pytest runtime\\studio\\test_settings_runtime_controls_panel.py -q",
            "required_exit_code": 0,
        },
    ]


def _post_wrapper_removal_regression_from_materialization_import_evidence_descriptor(
    regression_evidence,
    command_plan,
):
    descriptor = _real_source_restoration_regression_evidence_descriptor(
        regression_evidence,
        command_plan,
    )
    descriptor["schema_version"] = (
        POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SCHEMA_VERSION
    )
    descriptor["surface"] = (
        POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID
    )
    return descriptor


def build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
    vault_root,
    *,
    source_regeneration_runner_boundary_proof=None,
    source_regeneration_candidate_restore_proof=None,
    live_source_restoration_closeout_proof=None,
    restore_root=None,
    restore_targets_by_role=None,
    required_symbols_by_role=None,
    operator_approved_candidate_verification=False,
    candidate_verification_statement="",
    operator_approved_restore=False,
    restore_statement="",
    regression_evidence=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    restore_proof_supplied = source_regeneration_candidate_restore_proof is not None

    if source_regeneration_candidate_restore_proof is None:
        source_regeneration_candidate_restore_proof = (
            build_launcher_update_source_regeneration_candidate_verification_restore_proof(
                vault,
                source_regeneration_runner_boundary_proof=(
                    source_regeneration_runner_boundary_proof
                ),
                restore_root=restore_root,
                restore_targets_by_role=restore_targets_by_role,
                required_symbols_by_role=required_symbols_by_role,
                operator_approved_candidate_verification=(
                    operator_approved_candidate_verification
                ),
                candidate_verification_statement=candidate_verification_statement,
                operator_approved_restore=operator_approved_restore,
                restore_statement=restore_statement,
                generated_at=timestamp,
            )
        )

    restore_proof = _extension_unwrap_api_data(
        source_regeneration_candidate_restore_proof,
        "launcher_update_source_regeneration_candidate_verification_restore_proof",
    )
    restore_proof = _extension_unwrap_api_data(
        restore_proof or {},
        SOURCE_REGENERATION_CANDIDATE_RESTORE_SURFACE_ID,
    )
    if not isinstance(restore_proof, dict):
        restore_proof = {}
    if restore_proof.get("warnings"):
        warnings.extend(str(item) for item in restore_proof.get("warnings") or [])
    if not restore_proof:
        errors.append("source_regeneration_candidate_restore_proof_required")
    elif restore_proof.get("surface") != SOURCE_REGENERATION_CANDIDATE_RESTORE_SURFACE_ID:
        errors.append("source_regeneration_candidate_restore_surface_mismatch")

    restore_digest = str(
        restore_proof.get("source_regeneration_candidate_restore_digest_sha256") or ""
    )
    computed_restore_digest = (
        _extension_digest_without(
            restore_proof,
            "source_regeneration_candidate_restore_digest_sha256",
        )
        if restore_proof
        else ""
    )
    restore_digest_matched = bool(
        restore_digest and restore_digest == computed_restore_digest
    )
    if restore_proof and not restore_digest_matched:
        errors.append("source_regeneration_candidate_restore_digest_mismatch")

    real_source_restore_attempted = bool(
        restore_proof_supplied
        or operator_approved_candidate_verification
        or operator_approved_restore
        or restore_root is not None
    )
    real_source_restore_performed = bool(
        restore_proof.get("ok")
        and restore_proof.get("source_restore_performed")
        and restore_proof.get("source_write_performed")
        and restore_proof.get("live_source_write_performed")
        and restore_digest_matched
    )
    if restore_proof and not real_source_restore_performed:
        errors.append("real_source_restore_evidence_required")

    if live_source_restoration_closeout_proof is None:
        live_source_restoration_closeout_proof = (
            build_launcher_update_source_regeneration_live_source_restoration_closeout_proof(
                vault,
                source_regeneration_candidate_restore_proof=restore_proof,
                restore_targets_by_role=restore_targets_by_role,
                required_symbols_by_role=(
                    required_symbols_by_role
                    or restore_proof.get("required_symbols_by_role")
                ),
                generated_at=timestamp,
            )
        )

    closeout_proof = _extension_unwrap_api_data(
        live_source_restoration_closeout_proof,
        "launcher_update_source_regeneration_live_source_restoration_closeout_proof",
    )
    closeout_proof = _extension_unwrap_api_data(
        closeout_proof or {},
        SOURCE_REGENERATION_LIVE_SOURCE_RESTORATION_CLOSEOUT_SURFACE_ID,
    )
    if not isinstance(closeout_proof, dict):
        closeout_proof = {}
    if closeout_proof.get("warnings"):
        warnings.extend(str(item) for item in closeout_proof.get("warnings") or [])
    if not closeout_proof:
        errors.append("live_source_restoration_closeout_proof_required")
    elif (
        closeout_proof.get("surface")
        != SOURCE_REGENERATION_LIVE_SOURCE_RESTORATION_CLOSEOUT_SURFACE_ID
    ):
        errors.append("live_source_restoration_closeout_surface_mismatch")

    closeout_digest = str(
        closeout_proof.get(
            "source_regeneration_live_source_restoration_closeout_digest_sha256"
        )
        or ""
    )
    computed_closeout_digest = (
        _extension_digest_without(
            closeout_proof,
            "source_regeneration_live_source_restoration_closeout_digest_sha256",
        )
        if closeout_proof
        else ""
    )
    closeout_digest_matched = bool(
        closeout_digest and closeout_digest == computed_closeout_digest
    )
    if closeout_proof and not closeout_digest_matched:
        errors.append("live_source_restoration_closeout_digest_mismatch")

    live_source_restoration_closeout_verified = bool(
        closeout_proof.get("ok")
        and closeout_proof.get("live_source_restoration_verified")
        and closeout_proof.get("wrapper_removal_verified")
        and closeout_digest_matched
    )
    if closeout_proof and not live_source_restoration_closeout_verified:
        errors.append("live_source_restoration_closeout_verification_required")

    command_plan = _real_source_restoration_regression_command_plan()
    regression_descriptor = _real_source_restoration_regression_evidence_descriptor(
        regression_evidence,
        command_plan,
    )
    regression_evidence_required = bool(live_source_restoration_closeout_verified)
    regression_evidence_verified = bool(
        regression_descriptor.get("regression_evidence_verified")
    )
    if regression_evidence_required and not regression_evidence_verified:
        errors.append("real_source_restoration_regression_evidence_required")

    status = (
        "launcher_update_real_source_restoration_execution_regression_boundary_blocked"
    )
    if real_source_restore_performed and not live_source_restoration_closeout_verified:
        status = (
            "launcher_update_real_source_restoration_execution_"
            "restored_pending_closeout"
        )
    if (
        real_source_restore_performed
        and live_source_restoration_closeout_verified
        and not regression_evidence_verified
    ):
        status = (
            "launcher_update_real_source_restoration_execution_"
            "restored_pending_regression_evidence"
        )
    if (
        real_source_restore_performed
        and live_source_restoration_closeout_verified
        and regression_evidence_verified
    ):
        status = (
            "launcher_update_real_source_restoration_execution_"
            "regression_verified"
        )

    boundary_verified = bool(
        real_source_restore_performed
        and live_source_restoration_closeout_verified
        and regression_evidence_verified
    )
    proof = {
        "ok": boundary_verified,
        "surface": REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SURFACE_ID,
        "schema_version": (
            REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SCHEMA_VERSION
        ),
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "source_regeneration_candidate_restore_status": restore_proof.get("status", ""),
        "source_regeneration_candidate_restore_digest_sha256": restore_digest,
        "source_regeneration_candidate_restore_digest_matched": restore_digest_matched,
        "live_source_restoration_closeout_status": closeout_proof.get("status", ""),
        "source_regeneration_live_source_restoration_closeout_digest_sha256": (
            closeout_digest
        ),
        "source_regeneration_live_source_restoration_closeout_digest_matched": (
            closeout_digest_matched
        ),
        "real_source_restore_attempted": real_source_restore_attempted,
        "real_source_restore_performed": real_source_restore_performed,
        "live_source_restoration_closeout_verified": (
            live_source_restoration_closeout_verified
        ),
        "regression_command_plan": command_plan,
        "regression_evidence_required": regression_evidence_required,
        "regression_evidence_verified": regression_evidence_verified,
        "regression_evidence": regression_descriptor,
        "source_regeneration_candidate_restore_proof": restore_proof,
        "live_source_restoration_closeout_proof": closeout_proof,
        "source_regeneration_execution_performed": False,
        "source_regeneration_output_written": False,
        "source_restore_performed": False,
        "source_restore_previously_performed": bool(
            restore_proof.get("source_restore_performed")
        ),
        "source_write_performed": False,
        "source_write_previously_performed": bool(
            restore_proof.get("source_write_performed")
        ),
        "live_source_write_performed": False,
        "live_source_write_previously_performed": bool(
            restore_proof.get("live_source_write_performed")
        ),
        "source_file_replacement_performed": False,
        "source_file_replacement_previously_performed": bool(
            restore_proof.get("source_file_replacement_performed")
        ),
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "regression_commands_executed_by_chaseos": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "resume_primary_exe_closeout_after_current_vault_regression"
            if boundary_verified
            else (
                "supply_post_restore_regression_evidence"
                if live_source_restoration_closeout_verified
                else "perform_live_source_restore_with_verified_candidates"
            )
        ),
        "authority": _authority(
            real_source_restoration_execution_regression_boundary_built=True,
            real_source_restoration_execution_performed=real_source_restore_performed,
            real_source_restoration_closeout_verified=(
                live_source_restoration_closeout_verified
            ),
            real_source_restoration_regression_evidence_verified=(
                regression_evidence_verified
            ),
            real_source_restoration_settings_write_control_exposed=False,
            real_source_restoration_primary_real_exe_replacement_performed=False,
            real_source_restoration_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["real_source_restoration_execution_regression_boundary_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "real_source_restoration_execution_regression_boundary_digest_sha256",
        )
    )
    return proof


def build_launcher_update_current_vault_source_restoration_closeout_readiness(
    vault_root,
    *,
    real_source_restoration_execution_regression_boundary_proof=None,
    source_recovery_cleanup_proof=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    if real_source_restoration_execution_regression_boundary_proof is None:
        real_source_restoration_execution_regression_boundary_proof = (
            build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
                vault,
                generated_at=timestamp,
            )
        )
    boundary_proof = _extension_unwrap_api_data(
        real_source_restoration_execution_regression_boundary_proof,
        "launcher_update_real_source_restoration_execution_regression_boundary_proof",
    )
    boundary_proof = _extension_unwrap_api_data(
        boundary_proof or {},
        REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SURFACE_ID,
    )
    if not isinstance(boundary_proof, dict):
        boundary_proof = {}
    if boundary_proof.get("warnings"):
        warnings.extend(str(item) for item in boundary_proof.get("warnings") or [])
    if not boundary_proof:
        errors.append("real_source_restoration_regression_boundary_proof_required")
    elif (
        boundary_proof.get("surface")
        != REAL_SOURCE_RESTORATION_EXECUTION_REGRESSION_BOUNDARY_SURFACE_ID
    ):
        errors.append("real_source_restoration_regression_boundary_surface_mismatch")

    boundary_digest = str(
        boundary_proof.get(
            "real_source_restoration_execution_regression_boundary_digest_sha256"
        )
        or ""
    )
    computed_boundary_digest = (
        _extension_digest_without(
            boundary_proof,
            "real_source_restoration_execution_regression_boundary_digest_sha256",
        )
        if boundary_proof
        else ""
    )
    boundary_digest_matched = bool(
        boundary_digest and boundary_digest == computed_boundary_digest
    )
    if boundary_proof and not boundary_digest_matched:
        errors.append("real_source_restoration_regression_boundary_digest_mismatch")

    regression_boundary_verified = bool(
        boundary_proof.get("ok")
        and boundary_proof.get("real_source_restore_performed")
        and boundary_proof.get("live_source_restoration_closeout_verified")
        and boundary_proof.get("regression_evidence_verified")
        and boundary_digest_matched
    )
    if boundary_proof and not regression_boundary_verified:
        errors.append("real_source_restoration_regression_boundary_not_verified")

    if source_recovery_cleanup_proof is None:
        source_recovery_cleanup_proof = build_launcher_update_source_recovery_cleanup_proof(
            vault,
            generated_at=timestamp,
        )
    cleanup_proof = _extension_unwrap_api_data(
        source_recovery_cleanup_proof,
        "launcher_update_source_recovery_cleanup_proof",
    )
    cleanup_proof = _extension_unwrap_api_data(
        cleanup_proof or {},
        SOURCE_RECOVERY_CLEANUP_SURFACE_ID,
    )
    if not isinstance(cleanup_proof, dict):
        cleanup_proof = {}
    if cleanup_proof.get("warnings"):
        warnings.extend(str(item) for item in cleanup_proof.get("warnings") or [])
    if not cleanup_proof:
        errors.append("source_recovery_cleanup_proof_required")
    elif cleanup_proof.get("surface") != SOURCE_RECOVERY_CLEANUP_SURFACE_ID:
        errors.append("source_recovery_cleanup_surface_mismatch")

    cleanup_digest = str(
        cleanup_proof.get("source_recovery_cleanup_digest_sha256") or ""
    )
    computed_cleanup_digest = (
        _extension_digest_without(
            cleanup_proof,
            "source_recovery_cleanup_digest_sha256",
        )
        if cleanup_proof
        else ""
    )
    cleanup_digest_matched = bool(
        cleanup_digest and cleanup_digest == computed_cleanup_digest
    )
    if cleanup_proof and not cleanup_digest_matched:
        errors.append("source_recovery_cleanup_digest_mismatch")

    source_cleanup_ready = bool(
        cleanup_proof.get("ok")
        and cleanup_proof.get("source_recovery_cleanup_ready")
        and cleanup_proof.get("normal_source_restored")
        and not cleanup_proof.get("final_auto_update_closeout_blocked")
        and cleanup_digest_matched
    )
    launcher_wrapper_active = bool(
        (cleanup_proof.get("launcher_update_check_source") or {}).get("wrapper_active")
    )
    api_wrapper_active = bool(
        (cleanup_proof.get("studio_shell_api_source") or {}).get("wrapper_active")
    )
    current_vault_wrappers_removed = bool(
        source_cleanup_ready and not launcher_wrapper_active and not api_wrapper_active
    )
    if cleanup_proof and not source_cleanup_ready:
        errors.append("source_recovery_cleanup_not_ready")
    if launcher_wrapper_active or api_wrapper_active:
        errors.append("current_vault_source_wrappers_still_active")

    closeout_ready = bool(regression_boundary_verified and current_vault_wrappers_removed)
    status = "launcher_update_current_vault_source_restoration_closeout_blocked"
    if regression_boundary_verified and not current_vault_wrappers_removed:
        status = (
            "launcher_update_current_vault_source_restoration_"
            "closeout_wrapper_removal_required"
        )
    if current_vault_wrappers_removed and not regression_boundary_verified:
        status = (
            "launcher_update_current_vault_source_restoration_"
            "closeout_regression_boundary_required"
        )
    if closeout_ready:
        status = "launcher_update_current_vault_source_restoration_closeout_ready"

    proof = {
        "ok": closeout_ready,
        "surface": CURRENT_VAULT_SOURCE_RESTORATION_CLOSEOUT_READINESS_SURFACE_ID,
        "schema_version": (
            CURRENT_VAULT_SOURCE_RESTORATION_CLOSEOUT_READINESS_SCHEMA_VERSION
        ),
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "real_source_restoration_regression_boundary_status": boundary_proof.get(
            "status",
            "",
        ),
        "real_source_restoration_regression_boundary_digest_sha256": boundary_digest,
        "real_source_restoration_regression_boundary_digest_matched": (
            boundary_digest_matched
        ),
        "real_source_restoration_regression_boundary_verified": (
            regression_boundary_verified
        ),
        "source_recovery_cleanup_status": cleanup_proof.get("status", ""),
        "source_recovery_cleanup_digest_sha256": cleanup_digest,
        "source_recovery_cleanup_digest_matched": cleanup_digest_matched,
        "source_recovery_cleanup_ready": source_cleanup_ready,
        "current_vault_wrappers_removed": current_vault_wrappers_removed,
        "launcher_update_check_wrapper_active": launcher_wrapper_active,
        "studio_shell_api_wrapper_active": api_wrapper_active,
        "current_vault_source_restoration_closeout_ready": closeout_ready,
        "source_restoration_closeout_ready_for_primary_exe_resume": closeout_ready,
        "real_source_restoration_execution_regression_boundary_proof": boundary_proof,
        "source_recovery_cleanup_proof": cleanup_proof,
        "source_regeneration_execution_performed": False,
        "source_restore_performed": False,
        "source_write_performed": False,
        "live_source_write_performed": False,
        "regression_commands_executed_by_chaseos": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "resume_primary_exe_closeout_after_source_recovery"
            if closeout_ready
            else (
                "remove_current_vault_source_wrappers"
                if regression_boundary_verified
                else "verify_real_source_restoration_regression_boundary"
            )
        ),
        "authority": _authority(
            current_vault_source_restoration_closeout_readiness_built=True,
            current_vault_source_restoration_cleanup_ready=source_cleanup_ready,
            current_vault_source_restoration_regression_boundary_verified=(
                regression_boundary_verified
            ),
            current_vault_source_restoration_closeout_ready=closeout_ready,
            current_vault_source_restoration_settings_write_control_exposed=False,
            current_vault_source_restoration_primary_real_exe_replacement_performed=False,
            current_vault_source_restoration_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["current_vault_source_restoration_closeout_readiness_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "current_vault_source_restoration_closeout_readiness_digest_sha256",
        )
    )
    return proof


def _source_candidate_inventory_decompiler_tools():
    module_names = ["uncompyle6", "decompyle3", "xdis"]
    tools = {}
    for module_name in module_names:
        spec = _extension_importlib_util.find_spec(module_name)
        tools[module_name] = {
            "kind": "python_module",
            "available": spec is not None,
            "origin": str(getattr(spec, "origin", "") or "") if spec else "",
        }
    pycdc_path = _extension_shutil.which("pycdc")
    tools["pycdc"] = {
        "kind": "executable",
        "available": bool(pycdc_path),
        "origin": str(pycdc_path or ""),
    }
    return tools


def _source_candidate_inventory_default_candidate_paths(vault, launcher_source_path):
    candidate_map = _normal_source_default_candidate_paths(vault, launcher_source_path)
    return {
        role: list(paths)
        for role, paths in candidate_map.items()
    }


def _source_candidate_inventory_recovery_artifacts(launcher_source_path):
    return {
        "launcher_update_check": _source_recovery_artifact_descriptor(
            _RECOVERED_BYTECODE_PATH,
            _RECOVERED_BYTECODE_EXPECTED_SHA256,
        ),
        "studio_shell_api": _source_recovery_artifact_descriptor(
            launcher_source_path.parent / _API_RECOVERED_BYTECODE_RELATIVE_PATH,
            _API_RECOVERED_BYTECODE_EXPECTED_SHA256,
        ),
        "launcher_update_tests": _source_recovery_artifact_descriptor(
            launcher_source_path.parent
            / "recovery"
            / "test_launcher_update_check_recovered_20260525_025258.cpython-314.bytecode",
            "2ee2dc1c4bd243051edef9a9323346f20d353293f19ae377805d994e327db30c",
        ),
    }


def _source_candidate_inventory_descriptor(
    *,
    vault,
    role,
    path,
    required_symbols,
    live_source_paths,
):
    candidate_path = _Path(path)
    basic = _normal_source_candidate_descriptor(path, role, required_symbols)
    verification = _normal_source_candidate_verification_descriptor(
        vault=vault,
        role=role,
        path=path,
        required_symbols=required_symbols,
    )
    try:
        resolved_path = candidate_path.resolve()
    except OSError:
        resolved_path = candidate_path
    is_live_source = any(
        str(resolved_path).lower() == str(_Path(live_path).resolve()).lower()
        for live_path in live_source_paths
    )
    wrapper_tokens_present = list(verification.get("wrapper_tokens_present") or [])
    candidate_class = "missing"
    if basic.get("exists") and basic.get("is_file"):
        if is_live_source and wrapper_tokens_present:
            candidate_class = "current_vault_recovery_wrapper_source"
        elif wrapper_tokens_present:
            candidate_class = "recovery_wrapper_source"
        elif verification.get("candidate_verification_passed"):
            candidate_class = "verified_wrapper_free_normal_source_candidate"
        elif basic.get("text_readable"):
            candidate_class = "wrapper_free_stale_or_incomplete_source_candidate"
        else:
            candidate_class = "unreadable_source_candidate"
    elif basic.get("exists") and not basic.get("is_file"):
        candidate_class = "not_file"

    return {
        "role": role,
        "path": str(path),
        "resolved_path": str(resolved_path),
        "candidate_class": candidate_class,
        "is_live_source": is_live_source,
        "exists": bool(basic.get("exists")),
        "is_file": bool(basic.get("is_file")),
        "size_bytes": int(basic.get("size_bytes") or 0),
        "sha256": str(basic.get("sha256") or ""),
        "wrapper_active": bool(basic.get("wrapper_active")),
        "wrapper_tokens_present": wrapper_tokens_present,
        "required_symbols": list(required_symbols),
        "missing_required_symbols": list(
            verification.get("missing_required_symbols") or []
        ),
        "ast_parse_ok": bool(verification.get("ast_parse_ok")),
        "inside_vault_root": bool(verification.get("inside_vault_root")),
        "candidate_verification_passed": bool(
            verification.get("candidate_verification_passed")
        ),
        "candidate_status": verification.get("candidate_status")
        or basic.get("candidate_status"),
        "errors": list(verification.get("errors") or []),
    }


def build_launcher_update_source_candidate_inventory_wrapper_removal_preflight(
    vault_root,
    *,
    candidate_paths=None,
    required_symbols_by_role=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    launcher_source_path = _Path(__file__).resolve()
    api_source_path = launcher_source_path.parent / "shell" / "api.py"
    shell_test_source_path = launcher_source_path.parent / "shell" / "test_pass10a_shell.py"
    source_cleanup = build_launcher_update_source_recovery_cleanup_proof(
        vault,
        generated_at=timestamp,
    )
    normal_source_readiness = build_launcher_update_normal_source_restoration_readiness(
        vault,
        candidate_paths=candidate_paths,
        generated_at=timestamp,
    )
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    roles = [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]
    candidate_map = (
        candidate_paths
        or _source_candidate_inventory_default_candidate_paths(vault, launcher_source_path)
    )
    live_source_paths = [launcher_source_path, api_source_path, shell_test_source_path]
    candidates = {}
    role_readiness = {}
    role_candidate_classes = {}
    for role in roles:
        role_paths = _normal_source_candidate_role_paths(candidate_map, role)
        if not role_paths:
            role_paths = []
        candidates[role] = [
            _source_candidate_inventory_descriptor(
                vault=vault,
                role=role,
                path=path,
                required_symbols=required_symbols.get(role, []),
                live_source_paths=live_source_paths,
            )
            for path in role_paths
        ]
        role_readiness[role] = any(
            item.get("candidate_verification_passed")
            for item in candidates.get(role, [])
        )
        role_candidate_classes[role] = sorted(
            {
                str(item.get("candidate_class") or "")
                for item in candidates.get(role, [])
                if item.get("candidate_class")
            }
        )

    decompiler_tools = _source_candidate_inventory_decompiler_tools()
    decompiler_tool_available = any(
        bool(tool.get("available")) for tool in decompiler_tools.values()
    )
    recovery_artifacts = _source_candidate_inventory_recovery_artifacts(
        launcher_source_path
    )
    recovery_artifacts_pinned = all(
        bool(item.get("sha256_matches")) for item in recovery_artifacts.values()
    )
    launcher_wrapper_active = bool(
        (source_cleanup.get("launcher_update_check_source") or {}).get(
            "wrapper_active"
        )
    )
    api_wrapper_active = bool(
        (source_cleanup.get("studio_shell_api_source") or {}).get("wrapper_active")
    )
    current_vault_wrappers_active = bool(
        launcher_wrapper_active or api_wrapper_active
    )
    authoritative_candidates_available = all(role_readiness.values())
    wrapper_removal_plan_ready = bool(
        authoritative_candidates_available and current_vault_wrappers_active
    )

    errors = []
    warnings = []
    if not recovery_artifacts_pinned:
        errors.append("source_recovery_artifacts_not_hash_pinned")
    if launcher_wrapper_active:
        errors.append("launcher_update_check_wrapper_active")
    if api_wrapper_active:
        errors.append("studio_shell_api_wrapper_active")
    if not role_readiness.get("launcher_update_check"):
        errors.append("launcher_update_check_authoritative_source_candidate_missing")
    if not role_readiness.get("studio_shell_api"):
        errors.append("studio_shell_api_authoritative_source_candidate_missing")
    if not role_readiness.get("studio_shell_test_pass10a"):
        errors.append("studio_shell_test_pass10a_authoritative_source_candidate_missing")
    if not authoritative_candidates_available and not decompiler_tool_available:
        errors.append("decompiler_tool_unavailable_or_operator_source_required")
    elif not decompiler_tool_available:
        warnings.append("decompiler_tool_unavailable")
    if not wrapper_removal_plan_ready:
        errors.append("current_vault_wrapper_removal_preflight_not_ready")

    status = "launcher_update_source_candidate_inventory_wrapper_removal_preflight_blocked"
    if current_vault_wrappers_active and not authoritative_candidates_available:
        status = "launcher_update_source_candidate_inventory_authoritative_candidates_missing"
    if authoritative_candidates_available and not current_vault_wrappers_active:
        status = "launcher_update_source_candidate_inventory_current_vault_already_wrapper_free"
    if wrapper_removal_plan_ready:
        status = "launcher_update_source_candidate_inventory_wrapper_removal_preflight_ready"

    proof = {
        "ok": wrapper_removal_plan_ready,
        "surface": SOURCE_CANDIDATE_INVENTORY_WRAPPER_REMOVAL_PREFLIGHT_SURFACE_ID,
        "schema_version": (
            SOURCE_CANDIDATE_INVENTORY_WRAPPER_REMOVAL_PREFLIGHT_SCHEMA_VERSION
        ),
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "source_recovery_cleanup_status": source_cleanup.get("status"),
        "normal_source_restoration_readiness_status": normal_source_readiness.get(
            "status"
        ),
        "source_recovery_artifacts_pinned": recovery_artifacts_pinned,
        "current_vault_wrappers_active": current_vault_wrappers_active,
        "launcher_update_check_wrapper_active": launcher_wrapper_active,
        "studio_shell_api_wrapper_active": api_wrapper_active,
        "authoritative_source_candidates_available": authoritative_candidates_available,
        "wrapper_removal_plan_ready": wrapper_removal_plan_ready,
        "role_readiness": role_readiness,
        "role_candidate_classes": role_candidate_classes,
        "required_symbols_by_role": required_symbols,
        "candidate_inventory": candidates,
        "recovery_artifacts": recovery_artifacts,
        "decompiler_tools": decompiler_tools,
        "decompiler_tool_available": decompiler_tool_available,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "source_write_performed": False,
        "wrapper_removal_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_approved_wrapper_removal_restore_executor_with_verified_candidates"
            if wrapper_removal_plan_ready
            else "supply_authoritative_wrapper_free_normal_source_candidates"
        ),
        "source_recovery_cleanup_digest_sha256": source_cleanup.get(
            "source_recovery_cleanup_digest_sha256",
            "",
        ),
        "normal_source_restoration_readiness_digest_sha256": (
            normal_source_readiness.get(
                "normal_source_restoration_readiness_digest_sha256",
                "",
            )
        ),
        "authority": _authority(
            source_candidate_inventory_wrapper_removal_preflight_built=True,
            source_candidate_inventory_authoritative_candidates_available=(
                authoritative_candidates_available
            ),
            source_candidate_inventory_wrapper_removal_plan_ready=(
                wrapper_removal_plan_ready
            ),
            source_candidate_inventory_decompiler_execution_performed=False,
            source_candidate_inventory_settings_write_control_exposed=False,
            source_candidate_inventory_primary_real_exe_replacement_performed=False,
            source_candidate_inventory_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["source_candidate_inventory_wrapper_removal_preflight_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "source_candidate_inventory_wrapper_removal_preflight_digest_sha256",
        )
    )
    return proof


def _authoritative_normal_source_candidate_supply_root(vault, candidate_root=None):
    if candidate_root:
        root = _Path(candidate_root)
        if not root.is_absolute():
            root = vault / root
        return root.resolve()
    return (
        vault
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "authoritative-normal-source"
    ).resolve()


def _authoritative_normal_source_candidate_expected_paths(candidate_root):
    return {
        "launcher_update_check": [
            candidate_root / "runtime" / "studio" / "launcher_update_check.py"
        ],
        "studio_shell_api": [
            candidate_root / "runtime" / "studio" / "shell" / "api.py"
        ],
        "studio_shell_test_pass10a": [
            candidate_root
            / "runtime"
            / "studio"
            / "shell"
            / "test_pass10a_shell.py"
        ],
    }


def _authoritative_normal_source_candidate_expected_files(
    vault,
    expected_candidate_paths,
):
    expected_files = {}
    for role, paths in expected_candidate_paths.items():
        role_files = []
        for path in paths:
            candidate_path = _Path(path)
            try:
                relative_path = str(candidate_path.resolve().relative_to(vault))
            except (ValueError, OSError):
                relative_path = str(candidate_path)
            role_files.append(
                {
                    "role": role,
                    "path": str(candidate_path),
                    "relative_path": relative_path,
                    "extension_required": ".py",
                    "must_be_inside_vault_root": True,
                    "must_be_wrapper_free": True,
                    "must_parse_as_python_ast": True,
                }
            )
        expected_files[role] = role_files
    return expected_files


def required_update_authoritative_normal_source_candidate_supply_operator_statement(
    candidate_supply_contract,
):
    digest = str(
        (candidate_supply_contract or {}).get(
            "candidate_supply_contract_digest_sha256"
        )
        or _extension_digest_without(
            candidate_supply_contract or {},
            "candidate_supply_contract_digest_sha256",
        )
    )
    return (
        f"{AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_authoritative_normal_source_candidate_supply_packet(
    vault_root,
    *,
    candidate_root=None,
    candidate_paths=None,
    required_symbols_by_role=None,
    operator_approved_candidate_supply=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    supply_root = _authoritative_normal_source_candidate_supply_root(
        vault,
        candidate_root,
    )
    expected_candidate_paths = (
        candidate_paths
        or _authoritative_normal_source_candidate_expected_paths(supply_root)
    )
    normalized_candidate_paths = {
        role: [str(path) for path in _normal_source_candidate_role_paths(
            expected_candidate_paths,
            role,
        )]
        for role in [
            "launcher_update_check",
            "studio_shell_api",
            "studio_shell_test_pass10a",
        ]
    }
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    inventory = build_launcher_update_source_candidate_inventory_wrapper_removal_preflight(
        vault,
        candidate_paths=normalized_candidate_paths,
        required_symbols_by_role=required_symbols,
        generated_at=timestamp,
    )
    inventory_digest = inventory.get(
        "source_candidate_inventory_wrapper_removal_preflight_digest_sha256",
        "",
    )
    forbidden_wrapper_tokens = [
        "exec(_RECOVERED_BYTECODE_CODE, globals())",
        "_RECOVERED_BYTECODE_PATH",
        "marshal as _marshal",
    ]
    candidate_supply_contract = {
        "schema_version": AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SCHEMA_VERSION,
        "surface": AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SURFACE_ID,
        "candidate_root": str(supply_root),
        "candidate_paths": normalized_candidate_paths,
        "expected_candidate_files": _authoritative_normal_source_candidate_expected_files(
            vault,
            normalized_candidate_paths,
        ),
        "candidate_roles": [
            "launcher_update_check",
            "studio_shell_api",
            "studio_shell_test_pass10a",
        ],
        "required_symbols_by_role": required_symbols,
        "forbidden_wrapper_tokens": forbidden_wrapper_tokens,
        "source_candidate_inventory_status": inventory.get("status"),
        "source_candidate_inventory_digest_sha256": inventory_digest,
        "role_readiness": dict(inventory.get("role_readiness") or {}),
        "authoritative_source_candidates_available": bool(
            inventory.get("authoritative_source_candidates_available")
        ),
        "current_vault_wrappers_active": bool(
            inventory.get("current_vault_wrappers_active")
        ),
        "source_write_allowed": False,
        "wrapper_removal_allowed": False,
        "decompiler_execution_allowed": False,
        "candidate_source_execution_allowed": False,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
    }
    candidate_supply_contract["candidate_supply_contract_digest_sha256"] = (
        _extension_digest_without(
            candidate_supply_contract,
            "candidate_supply_contract_digest_sha256",
        )
    )
    required_statement = (
        required_update_authoritative_normal_source_candidate_supply_operator_statement(
            candidate_supply_contract
        )
    )
    operator_statement_matched = bool(
        operator_approved_candidate_supply
        and str(operator_statement) == required_statement
    )
    authoritative_candidates_available = bool(
        candidate_supply_contract["authoritative_source_candidates_available"]
    )
    ready_for_verifier = bool(
        authoritative_candidates_available and operator_statement_matched
    )

    errors = []
    warnings = []
    if inventory.get("warnings"):
        warnings.extend(str(item) for item in inventory.get("warnings") or [])
    if not authoritative_candidates_available:
        errors.append("authoritative_normal_source_candidates_missing")
        for role, ready in (inventory.get("role_readiness") or {}).items():
            if not ready:
                errors.append(f"{role}_authoritative_candidate_missing")
    if not operator_approved_candidate_supply:
        errors.append("operator_candidate_supply_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_candidate_supply_statement_mismatch")
    if inventory.get("current_vault_wrappers_active"):
        warnings.append("current_vault_wrappers_still_active")

    status = "launcher_update_authoritative_normal_source_candidate_supply_blocked"
    if authoritative_candidates_available and not operator_statement_matched:
        status = (
            "launcher_update_authoritative_normal_source_candidate_supply_"
            "pending_approval"
        )
    if ready_for_verifier:
        status = (
            "launcher_update_authoritative_normal_source_candidate_supply_"
            "ready_for_verifier"
        )

    proof = {
        "ok": ready_for_verifier,
        "surface": AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SURFACE_ID,
        "schema_version": AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "candidate_root": str(supply_root),
        "errors": errors,
        "warnings": warnings,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "candidate_supply_packet_ready": ready_for_verifier,
        "ready_for_candidate_verifier": ready_for_verifier,
        "authoritative_source_candidates_available": authoritative_candidates_available,
        "current_vault_wrappers_active": bool(
            inventory.get("current_vault_wrappers_active")
        ),
        "role_readiness": dict(inventory.get("role_readiness") or {}),
        "candidate_paths": normalized_candidate_paths,
        "expected_candidate_files": candidate_supply_contract[
            "expected_candidate_files"
        ],
        "required_symbols_by_role": required_symbols,
        "forbidden_wrapper_tokens": forbidden_wrapper_tokens,
        "source_candidate_inventory": inventory,
        "candidate_supply_contract": candidate_supply_contract,
        "source_write_performed": False,
        "source_write_enabled": False,
        "wrapper_removal_performed": False,
        "wrapper_removal_enabled": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_normal_source_candidate_verifier_or_wrapper_removal_restore_executor"
            if ready_for_verifier
            else "place_authoritative_wrapper_free_candidates_at_expected_paths"
        ),
        "authority": _authority(
            authoritative_normal_source_candidate_supply_packet_built=True,
            authoritative_normal_source_candidate_supply_candidates_available=(
                authoritative_candidates_available
            ),
            authoritative_normal_source_candidate_supply_ready_for_verifier=(
                ready_for_verifier
            ),
            authoritative_normal_source_candidate_supply_operator_statement_matched=(
                operator_statement_matched
            ),
            authoritative_normal_source_candidate_supply_source_write_performed=False,
            authoritative_normal_source_candidate_supply_settings_write_control_exposed=False,
            authoritative_normal_source_candidate_supply_primary_real_exe_replacement_performed=False,
            authoritative_normal_source_candidate_supply_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["authoritative_normal_source_candidate_supply_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "authoritative_normal_source_candidate_supply_digest_sha256",
        )
    )
    return proof


def _authoritative_source_candidate_import_targets(vault, candidate_root=None):
    supply_root = _authoritative_normal_source_candidate_supply_root(
        vault,
        candidate_root,
    )
    return _authoritative_normal_source_candidate_expected_paths(supply_root)


def _authoritative_source_candidate_import_target_descriptor(
    *,
    vault,
    role,
    target_path,
):
    target = _Path(target_path or "")
    descriptor = {
        "role": role,
        "target_path": str(target_path or ""),
        "resolved_target_path": "",
        "inside_vault_root": False,
        "extension_allowed": False,
        "target_exists_before_import": False,
        "target_is_file_or_missing": False,
        "errors": [],
    }
    if not target_path:
        descriptor["errors"].append("import_target_required")
        return descriptor
    try:
        resolved = target.resolve()
    except OSError:
        resolved = target
    descriptor["resolved_target_path"] = str(resolved)
    descriptor["inside_vault_root"] = _extension_path_is_relative_to(resolved, vault)
    if not descriptor["inside_vault_root"]:
        descriptor["errors"].append("import_target_outside_vault_root")
    descriptor["extension_allowed"] = resolved.suffix.lower() == ".py"
    if not descriptor["extension_allowed"]:
        descriptor["errors"].append("import_target_extension_not_py")
    descriptor["target_exists_before_import"] = resolved.exists()
    descriptor["target_is_file_or_missing"] = (not resolved.exists()) or resolved.is_file()
    if not descriptor["target_is_file_or_missing"]:
        descriptor["errors"].append("import_target_not_file")
    return descriptor


def _authoritative_source_candidate_verified_import_descriptor(descriptors):
    for descriptor in descriptors or []:
        if descriptor.get("candidate_verification_passed"):
            return descriptor
    return {}


def required_update_authoritative_source_candidate_import_operator_statement(
    candidate_import_plan,
):
    digest = str(
        (candidate_import_plan or {}).get("candidate_import_plan_digest_sha256")
        or _extension_digest_without(
            candidate_import_plan or {},
            "candidate_import_plan_digest_sha256",
        )
    )
    return (
        f"{AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_authoritative_source_candidate_import_boundary_proof(
    vault_root,
    *,
    import_candidate_paths=None,
    candidate_root=None,
    required_symbols_by_role=None,
    operator_approved_candidate_import=False,
    operator_statement="",
    allow_candidate_import_write=False,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    roles = [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    target_root = _authoritative_normal_source_candidate_supply_root(
        vault,
        candidate_root,
    )
    target_paths = _authoritative_source_candidate_import_targets(
        vault,
        target_root,
    )
    normalized_target_paths = {
        role: [str(_Path(path).resolve()) for path in _normal_source_candidate_role_paths(target_paths, role)]
        for role in roles
    }
    target_root_inside_vault = _extension_path_is_relative_to(target_root, vault)

    plan_errors = []
    if not target_root_inside_vault:
        plan_errors.append("authoritative_source_candidate_import_root_outside_vault")

    import_candidates = {}
    role_readiness = {}
    role_plan = {}
    for role in roles:
        role_paths = _normal_source_candidate_role_paths(import_candidate_paths, role)
        if not role_paths:
            descriptors = [
                _normal_source_candidate_verification_descriptor(
                    vault=vault,
                    role=role,
                    path="",
                    required_symbols=required_symbols.get(role, []),
                )
            ]
        else:
            descriptors = [
                _normal_source_candidate_verification_descriptor(
                    vault=vault,
                    role=role,
                    path=path,
                    required_symbols=required_symbols.get(role, []),
                )
                for path in role_paths
            ]
        import_candidates[role] = descriptors
        verified = _authoritative_source_candidate_verified_import_descriptor(
            descriptors
        )
        role_ready = bool(verified)
        role_readiness[role] = role_ready
        target_values = _normal_source_candidate_role_paths(
            normalized_target_paths,
            role,
        )
        target = _authoritative_source_candidate_import_target_descriptor(
            vault=vault,
            role=role,
            target_path=target_values[0] if target_values else "",
        )
        item_errors = []
        if not role_ready:
            item_errors.append("import_candidate_verification_required")
        if target.get("errors"):
            item_errors.extend(target["errors"])
        if (
            verified.get("resolved_path")
            and verified.get("resolved_path") == target.get("resolved_target_path")
        ):
            item_errors.append("import_source_and_target_must_differ")
        if item_errors:
            plan_errors.append(f"{role}_import_plan_invalid")
        role_plan[role] = {
            "role": role,
            "source": {
                "path": verified.get("path", ""),
                "resolved_path": verified.get("resolved_path", ""),
                "sha256": verified.get("sha256", ""),
                "size_bytes": verified.get("size_bytes", 0),
                "candidate_status": verified.get("candidate_status", ""),
                "candidate_verification_passed": bool(
                    verified.get("candidate_verification_passed")
                ),
            },
            "target": target,
            "ready": not item_errors,
            "errors": item_errors,
        }

    plan_ready = not plan_errors and all(
        item.get("ready") for item in role_plan.values()
    )
    candidate_import_plan = {
        "schema_version": AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SCHEMA_VERSION,
        "surface": AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SURFACE_ID,
        "vault_root": str(vault),
        "candidate_root": str(target_root),
        "candidate_root_inside_vault": target_root_inside_vault,
        "candidate_roles": roles,
        "import_candidate_paths": {
            role: [str(path) for path in _normal_source_candidate_role_paths(import_candidate_paths, role)]
            for role in roles
        },
        "target_candidate_paths": normalized_target_paths,
        "required_symbols_by_role": required_symbols,
        "role_readiness": role_readiness,
        "role_plan": role_plan,
        "plan_ready": plan_ready,
        "errors": plan_errors,
        "candidate_import_write_allowed_only_with_explicit_flag": True,
        "source_write_allowed": False,
        "wrapper_removal_allowed": False,
        "decompiler_execution_allowed": False,
        "candidate_source_execution_allowed": False,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
        "forbidden_behaviors": [
            "write_live_source",
            "remove_current_vault_wrappers",
            "decompile_bytecode",
            "execute_candidate_source",
            "launch_installer",
            "launch_helper",
            "replace_primary_exe",
            "mutate_startup",
            "publish_github_release",
        ],
    }
    candidate_import_plan["candidate_import_plan_digest_sha256"] = (
        _extension_digest_without(
            candidate_import_plan,
            "candidate_import_plan_digest_sha256",
        )
    )
    required_statement = (
        required_update_authoritative_source_candidate_import_operator_statement(
            candidate_import_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_candidate_import
        and str(operator_statement) == required_statement
    )

    errors = list(plan_errors)
    warnings = []
    if not operator_approved_candidate_import:
        errors.append("operator_authoritative_source_candidate_import_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_authoritative_source_candidate_import_statement_mismatch")
    if plan_ready and operator_statement_matched and not allow_candidate_import_write:
        errors.append("authoritative_source_candidate_import_write_flag_required")

    candidate_import_results = {}
    candidate_import_write_performed = False
    if plan_ready and operator_statement_matched and allow_candidate_import_write:
        for role, item in role_plan.items():
            source_path = _Path(item["source"]["resolved_path"])
            target_path = _Path(item["target"]["resolved_target_path"])
            before_hash = ""
            before_size = 0
            if target_path.exists() and target_path.is_file():
                before_payload = target_path.read_bytes()
                before_hash = _wrapper_hashlib.sha256(before_payload).hexdigest()
                before_size = len(before_payload)
            payload = source_path.read_bytes()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(payload)
            after_payload = target_path.read_bytes()
            after_hash = _wrapper_hashlib.sha256(after_payload).hexdigest()
            write_verified = after_hash == item["source"]["sha256"]
            if not write_verified:
                errors.append(f"{role}_authoritative_import_write_hash_mismatch")
            candidate_import_results[role] = {
                "role": role,
                "source_path": str(source_path),
                "target_path": str(target_path),
                "before_sha256": before_hash,
                "before_size_bytes": before_size,
                "after_sha256": after_hash,
                "after_size_bytes": len(after_payload),
                "write_performed": True,
                "write_verified": write_verified,
            }
        candidate_import_write_performed = bool(
            candidate_import_results
            and all(
                item.get("write_verified")
                for item in candidate_import_results.values()
            )
        )

    post_import_supply_packet_preview = (
        build_launcher_update_authoritative_normal_source_candidate_supply_packet(
            vault,
            candidate_root=target_root,
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
    )
    supply_packet_candidates_available = bool(
        post_import_supply_packet_preview.get(
            "authoritative_source_candidates_available"
        )
    )

    status = "launcher_update_authoritative_source_candidate_import_blocked"
    if plan_ready and not operator_statement_matched:
        status = "launcher_update_authoritative_source_candidate_import_pending_approval"
    if plan_ready and operator_statement_matched and not allow_candidate_import_write:
        status = "launcher_update_authoritative_source_candidate_import_write_flag_required"
    if candidate_import_write_performed:
        status = "launcher_update_authoritative_source_candidate_import_imported"

    proof = {
        "ok": candidate_import_write_performed,
        "surface": AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SURFACE_ID,
        "schema_version": AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "candidate_root": str(target_root),
        "errors": errors,
        "warnings": warnings,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "candidate_import_plan_ready": plan_ready,
        "candidate_import_write_enabled": bool(allow_candidate_import_write),
        "candidate_import_write_performed": candidate_import_write_performed,
        "candidate_import_performed": candidate_import_write_performed,
        "role_readiness": role_readiness,
        "import_candidates": import_candidates,
        "target_candidate_paths": normalized_target_paths,
        "candidate_import_plan": candidate_import_plan,
        "candidate_import_results": candidate_import_results,
        "post_import_supply_packet_preview": post_import_supply_packet_preview,
        "post_import_supply_packet_candidates_available": (
            supply_packet_candidates_available
        ),
        "ready_for_candidate_supply_approval": bool(
            candidate_import_write_performed and supply_packet_candidates_available
        ),
        "source_write_performed": False,
        "wrapper_removal_performed": False,
        "current_vault_wrappers_removed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "approve_authoritative_candidate_supply_and_run_verifier"
            if candidate_import_write_performed
            else "provide_verified_import_candidates_and_exact_import_approval"
        ),
        "authority": _authority(
            authoritative_source_candidate_import_boundary_built=True,
            authoritative_source_candidate_import_plan_ready=plan_ready,
            authoritative_source_candidate_import_statement_matched=(
                operator_statement_matched
            ),
            authoritative_source_candidate_import_candidate_write_performed=(
                candidate_import_write_performed
            ),
            authoritative_source_candidate_import_settings_write_control_exposed=False,
            authoritative_source_candidate_import_primary_real_exe_replacement_performed=False,
            authoritative_source_candidate_import_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["authoritative_source_candidate_import_boundary_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "authoritative_source_candidate_import_boundary_digest_sha256",
        )
    )
    return proof


def _real_authoritative_source_candidate_supply_default_roots(vault):
    repo_root = _Path(__file__).resolve().parents[2]
    roots = [
        _authoritative_normal_source_candidate_supply_root(vault),
        (
            vault
            / ".chaseos"
            / "updates"
            / "source-candidates"
            / "operator-supplied-normal-source"
        ),
        vault / "build" / "lib",
        repo_root / "build" / "lib",
    ]
    resolved_roots = []
    seen = set()
    for root in roots:
        try:
            resolved = _Path(root).resolve()
        except OSError:
            resolved = _Path(root)
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        resolved_roots.append(resolved)
    return resolved_roots


def _real_authoritative_source_candidate_normalized_roots(vault, candidate_roots):
    roots = candidate_roots or _real_authoritative_source_candidate_supply_default_roots(vault)
    normalized = []
    seen = set()
    for root in roots:
        path = _Path(root)
        if not path.is_absolute():
            path = vault / path
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(resolved)
    return normalized


def _real_authoritative_source_candidate_root_descriptor(vault, root):
    root = _Path(root)
    inside_vault = _extension_path_is_relative_to(root, vault)
    errors = []
    if not inside_vault:
        errors.append("candidate_root_outside_vault_root")
    return {
        "path": str(root),
        "inside_vault_root": inside_vault,
        "exists": root.exists(),
        "is_dir": root.is_dir(),
        "scan_allowed": bool(inside_vault and ((not root.exists()) or root.is_dir())),
        "errors": errors,
    }


def _real_authoritative_source_candidate_descriptor(
    *,
    vault,
    candidate_root,
    role,
    path,
    required_symbols,
    live_source_paths,
):
    descriptor = _normal_source_candidate_verification_descriptor(
        vault=vault,
        role=role,
        path=path,
        required_symbols=required_symbols,
    )
    resolved_path = str(descriptor.get("resolved_path") or "")
    is_live_source = False
    if resolved_path:
        is_live_source = any(
            str(_Path(live_source).resolve()).lower() == resolved_path.lower()
            for live_source in live_source_paths
        )
    if is_live_source:
        descriptor.setdefault("errors", []).append(
            "current_live_source_not_accepted_as_authoritative_candidate"
        )
        descriptor["candidate_verification_passed"] = False
        descriptor["candidate_status"] = "current_live_source_rejected"
    descriptor["candidate_root"] = str(candidate_root)
    descriptor["is_current_live_source"] = is_live_source
    descriptor["accepted_as_real_authoritative_candidate"] = bool(
        descriptor.get("candidate_verification_passed") and not is_live_source
    )
    return descriptor


def build_launcher_update_real_authoritative_source_candidate_supply_readiness(
    vault_root,
    *,
    candidate_roots=None,
    candidate_root=None,
    required_symbols_by_role=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    roles = [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    launcher_source_path = _Path(__file__).resolve()
    live_source_paths = [
        launcher_source_path,
        launcher_source_path.parent / "shell" / "api.py",
        launcher_source_path.parent / "shell" / "test_pass10a_shell.py",
    ]
    scan_roots = _real_authoritative_source_candidate_normalized_roots(
        vault,
        candidate_roots,
    )
    target_candidate_root = _authoritative_normal_source_candidate_supply_root(
        vault,
        candidate_root,
    )
    root_descriptors = [
        _real_authoritative_source_candidate_root_descriptor(vault, root)
        for root in scan_roots
    ]

    candidates_by_role = {role: [] for role in roles}
    for root, root_descriptor in zip(scan_roots, root_descriptors):
        expected_paths = _authoritative_normal_source_candidate_expected_paths(root)
        for role in roles:
            for path in _normal_source_candidate_role_paths(expected_paths, role):
                descriptor = _real_authoritative_source_candidate_descriptor(
                    vault=vault,
                    candidate_root=root,
                    role=role,
                    path=path,
                    required_symbols=required_symbols.get(role, []),
                    live_source_paths=live_source_paths,
                )
                if root_descriptor.get("errors"):
                    descriptor.setdefault("errors", []).extend(
                        root_descriptor.get("errors") or []
                    )
                    descriptor["candidate_verification_passed"] = False
                    descriptor["accepted_as_real_authoritative_candidate"] = False
                    descriptor["candidate_status"] = "invalid_candidate_root"
                candidates_by_role[role].append(descriptor)

    selected_candidates = {}
    role_readiness = {}
    candidate_import_paths = {}
    for role in roles:
        selected = {}
        for descriptor in candidates_by_role.get(role, []):
            if descriptor.get("accepted_as_real_authoritative_candidate"):
                selected = descriptor
                break
        selected_candidates[role] = selected
        role_readiness[role] = bool(selected)
        candidate_import_paths[role] = (
            [selected.get("resolved_path")]
            if selected.get("resolved_path")
            else []
        )

    real_candidates_available = all(role_readiness.values())
    import_preview = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        vault,
        import_candidate_paths=candidate_import_paths,
        candidate_root=target_candidate_root,
        required_symbols_by_role=required_symbols,
        generated_at=timestamp,
    )
    import_plan_ready = bool(import_preview.get("candidate_import_plan_ready"))
    ready_for_import_boundary = bool(real_candidates_available and import_plan_ready)

    source_supply_plan = {
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_READINESS_SCHEMA_VERSION,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_READINESS_SURFACE_ID,
        "vault_root": str(vault),
        "scan_roots": [str(root) for root in scan_roots],
        "target_candidate_root": str(target_candidate_root),
        "candidate_roles": roles,
        "required_symbols_by_role": required_symbols,
        "role_readiness": role_readiness,
        "candidate_import_paths": candidate_import_paths,
        "candidate_import_plan_ready": import_plan_ready,
        "ready_for_authoritative_import_boundary": ready_for_import_boundary,
        "source_write_allowed": False,
        "candidate_import_write_allowed": False,
        "wrapper_removal_allowed": False,
        "decompiler_execution_allowed": False,
        "candidate_source_execution_allowed": False,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
    }
    source_supply_plan["real_authoritative_source_candidate_supply_plan_digest_sha256"] = (
        _extension_digest_without(
            source_supply_plan,
            "real_authoritative_source_candidate_supply_plan_digest_sha256",
        )
    )

    errors = []
    warnings = []
    for root_descriptor in root_descriptors:
        errors.extend(root_descriptor.get("errors") or [])
    for role, ready in role_readiness.items():
        if not ready:
            errors.append(f"{role}_real_authoritative_candidate_missing")
    if not real_candidates_available:
        errors.append("real_authoritative_source_candidates_missing")
    if real_candidates_available and not import_plan_ready:
        errors.append("authoritative_source_candidate_import_plan_not_ready")
    if import_preview.get("warnings"):
        warnings.extend(str(item) for item in import_preview.get("warnings") or [])

    status = "launcher_update_real_authoritative_source_candidate_supply_blocked"
    if ready_for_import_boundary:
        status = (
            "launcher_update_real_authoritative_source_candidate_supply_"
            "ready_for_import_boundary"
        )

    proof = {
        "ok": ready_for_import_boundary,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_READINESS_SURFACE_ID,
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_READINESS_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "candidate_root": str(target_candidate_root),
        "errors": errors,
        "warnings": warnings,
        "candidate_roots": [str(root) for root in scan_roots],
        "candidate_root_descriptors": root_descriptors,
        "required_symbols_by_role": required_symbols,
        "candidate_inventory": candidates_by_role,
        "selected_candidates": selected_candidates,
        "role_readiness": role_readiness,
        "real_authoritative_source_candidates_available": real_candidates_available,
        "candidate_import_paths": candidate_import_paths,
        "candidate_import_preview": import_preview,
        "candidate_import_plan_ready": import_plan_ready,
        "required_candidate_import_operator_statement": import_preview.get(
            "required_operator_statement",
            "",
        ),
        "ready_for_authoritative_import_boundary": ready_for_import_boundary,
        "ready_for_candidate_import_approval": ready_for_import_boundary,
        "source_supply_plan": source_supply_plan,
        "source_write_performed": False,
        "candidate_import_write_performed": False,
        "candidate_import_performed": False,
        "wrapper_removal_performed": False,
        "current_vault_wrappers_removed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_authoritative_source_candidate_import_boundary_with_exact_approval"
            if ready_for_import_boundary
            else "supply_real_authoritative_wrapper_free_candidates_inside_vault"
        ),
        "authority": _authority(
            real_authoritative_source_candidate_supply_readiness_built=True,
            real_authoritative_source_candidate_supply_candidates_available=(
                real_candidates_available
            ),
            real_authoritative_source_candidate_supply_ready_for_import_boundary=(
                ready_for_import_boundary
            ),
            real_authoritative_source_candidate_supply_source_write_performed=False,
            real_authoritative_source_candidate_supply_candidate_import_write_performed=False,
            real_authoritative_source_candidate_supply_settings_write_control_exposed=False,
            real_authoritative_source_candidate_supply_primary_real_exe_replacement_performed=False,
            real_authoritative_source_candidate_supply_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["real_authoritative_source_candidate_supply_readiness_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "real_authoritative_source_candidate_supply_readiness_digest_sha256",
        )
    )
    return proof


def _real_authoritative_source_candidate_materialization_root(
    vault,
    materialization_root=None,
):
    if materialization_root:
        root = _Path(materialization_root)
        if not root.is_absolute():
            root = vault / root
        return root.resolve()
    return (
        vault
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "operator-supplied-normal-source"
    ).resolve()


def _real_authoritative_source_candidate_materialization_root_descriptor(vault, root):
    root = _Path(root)
    try:
        resolved = root.resolve()
    except OSError:
        resolved = root
    exists = root.exists()
    is_directory = (not exists) or root.is_dir()
    inside_vault = _extension_path_is_relative_to(resolved, vault)
    errors = []
    if not inside_vault:
        errors.append("source_candidate_materialization_root_outside_vault_root")
    if not is_directory:
        errors.append("source_candidate_materialization_root_not_directory")
    return {
        "path": str(root),
        "resolved_path": str(resolved),
        "exists": exists,
        "is_directory": is_directory,
        "inside_vault_root": inside_vault,
        "candidate_write_scope": "candidate_root_only",
        "errors": errors,
    }


def _real_authoritative_source_candidate_materialization_targets(
    materialization_root,
    roles,
):
    expected_paths = _authoritative_normal_source_candidate_expected_paths(
        _Path(materialization_root)
    )
    return {
        role: _normal_source_candidate_role_paths(expected_paths, role)[0]
        for role in roles
    }


def _real_authoritative_source_candidate_materialization_target_descriptors(
    vault,
    targets,
):
    descriptors = {}
    for role, path in targets.items():
        try:
            resolved = _Path(path).resolve()
        except OSError:
            resolved = _Path(path)
        try:
            relative_path = str(resolved.relative_to(vault))
        except (ValueError, OSError):
            relative_path = str(path)
        descriptors[role] = {
            "role": role,
            "path": str(path),
            "resolved_path": str(resolved),
            "relative_path": relative_path,
            "exists": _Path(path).exists(),
            "would_write": True,
            "create_only": True,
            "must_be_inside_vault_root": True,
            "must_parse_as_python_ast": True,
            "must_be_wrapper_free": True,
        }
    return descriptors


def required_update_real_authoritative_source_candidate_materialization_operator_statement(
    materialization_plan,
):
    digest = str(
        (materialization_plan or {}).get("materialization_plan_digest_sha256")
        or _extension_digest_without(
            materialization_plan or {},
            "materialization_plan_digest_sha256",
        )
    )
    return (
        f"{REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def _real_authoritative_source_candidate_materializer_receipt_summary(receipt):
    if not isinstance(receipt, dict):
        return {}
    summary = {}
    for key, value in receipt.items():
        if key == "generated_sources":
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            summary[key] = value
        elif isinstance(value, list) and all(
            isinstance(item, (str, int, float, bool)) or item is None
            for item in value
        ):
            summary[key] = list(value)
    return summary


def build_launcher_update_real_authoritative_source_candidate_materialization_proof(
    vault_root,
    *,
    materialization_root=None,
    source_candidate_supply_readiness=None,
    source_regeneration_readiness=None,
    source_materializer=None,
    source_materializer_label="injected_source_candidate_materializer",
    required_symbols_by_role=None,
    operator_approved_candidate_materialization=False,
    operator_statement="",
    allow_candidate_materialization_write=False,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    roles = [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    root = _real_authoritative_source_candidate_materialization_root(
        vault,
        materialization_root,
    )
    root_descriptor = (
        _real_authoritative_source_candidate_materialization_root_descriptor(
            vault,
            root,
        )
    )
    targets = _real_authoritative_source_candidate_materialization_targets(root, roles)
    target_descriptors = (
        _real_authoritative_source_candidate_materialization_target_descriptors(
            vault,
            targets,
        )
    )

    if source_candidate_supply_readiness is None:
        source_candidate_supply_readiness = (
            build_launcher_update_real_authoritative_source_candidate_supply_readiness(
                vault,
                generated_at=timestamp,
            )
        )
    source_candidate_supply_readiness = _extension_unwrap_api_data(
        source_candidate_supply_readiness,
        REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_READINESS_SURFACE_ID,
    )
    if not isinstance(source_candidate_supply_readiness, dict):
        source_candidate_supply_readiness = {}
    supply_digest = str(
        source_candidate_supply_readiness.get(
            "real_authoritative_source_candidate_supply_readiness_digest_sha256"
        )
        or ""
    )
    supply_digest_matched = bool(
        supply_digest
        and supply_digest
        == _extension_digest_without(
            source_candidate_supply_readiness,
            "real_authoritative_source_candidate_supply_readiness_digest_sha256",
        )
    )
    supply_ready = bool(
        source_candidate_supply_readiness.get("ok")
        and source_candidate_supply_readiness.get(
            "ready_for_authoritative_import_boundary"
        )
        and supply_digest_matched
    )

    if source_regeneration_readiness is None:
        source_regeneration_readiness = build_launcher_update_source_regeneration_readiness(
            vault,
            generated_at=timestamp,
        )
    source_regeneration_readiness = _extension_unwrap_api_data(
        source_regeneration_readiness,
        SOURCE_REGENERATION_READINESS_SURFACE_ID,
    )
    if not isinstance(source_regeneration_readiness, dict):
        source_regeneration_readiness = {}
    regeneration_digest = str(
        source_regeneration_readiness.get("source_regeneration_readiness_digest_sha256")
        or ""
    )
    regeneration_digest_matched = bool(
        regeneration_digest
        and regeneration_digest
        == _extension_digest_without(
            source_regeneration_readiness,
            "source_regeneration_readiness_digest_sha256",
        )
    )
    regeneration_ready = bool(
        source_regeneration_readiness.get("source_regeneration_ready")
        and regeneration_digest_matched
    )

    materialization_plan = {
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SCHEMA_VERSION,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SURFACE_ID,
        "vault_root": str(vault),
        "materialization_root": root_descriptor,
        "candidate_roles": roles,
        "target_candidate_paths": target_descriptors,
        "required_symbols_by_role": required_symbols,
        "source_materializer_label": str(source_materializer_label or ""),
        "source_candidate_supply_readiness_status": (
            source_candidate_supply_readiness.get("status")
        ),
        "source_candidate_supply_readiness_digest_sha256": supply_digest,
        "source_candidate_supply_readiness_digest_matched": supply_digest_matched,
        "source_candidate_supply_already_ready": supply_ready,
        "source_regeneration_readiness_status": source_regeneration_readiness.get(
            "status"
        ),
        "source_regeneration_readiness_digest_sha256": regeneration_digest,
        "source_regeneration_readiness_digest_matched": regeneration_digest_matched,
        "source_regeneration_ready": regeneration_ready,
        "requires_exact_operator_statement": True,
        "requires_explicit_candidate_write_flag": True,
        "writes_candidate_root_only": True,
        "writes_live_source_targets": False,
        "runs_decompiler": False,
        "imports_candidates": False,
        "launches_installer_or_helper": False,
        "replaces_primary_exe": False,
    }
    materialization_plan["materialization_plan_digest_sha256"] = (
        _extension_digest_without(
            materialization_plan,
            "materialization_plan_digest_sha256",
        )
    )
    required_statement = (
        required_update_real_authoritative_source_candidate_materialization_operator_statement(
            materialization_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_candidate_materialization
        and str(operator_statement) == required_statement
    )

    errors = []
    warnings = []
    errors.extend(root_descriptor.get("errors") or [])
    if not source_candidate_supply_readiness:
        errors.append("real_authoritative_source_candidate_supply_readiness_required")
    elif not supply_digest_matched:
        errors.append("real_authoritative_source_candidate_supply_readiness_digest_mismatch")
    if not source_regeneration_readiness:
        errors.append("source_regeneration_readiness_required")
    elif not regeneration_digest_matched:
        errors.append("source_regeneration_readiness_digest_mismatch")
    if not supply_ready:
        errors.append("real_authoritative_source_candidates_missing")
    if not regeneration_ready:
        warnings.append("source_regeneration_readiness_not_ready")
    if not supply_ready and source_materializer is None:
        errors.append("source_materializer_required")
    if not supply_ready and not operator_approved_candidate_materialization:
        errors.append("operator_candidate_materialization_approval_required")
    elif not supply_ready and not operator_statement_matched:
        errors.append("operator_candidate_materialization_statement_mismatch")

    plan_ready = bool(
        (not supply_ready)
        and source_materializer is not None
        and not root_descriptor.get("errors")
        and supply_digest_matched
        and regeneration_digest_matched
    )
    if plan_ready and operator_statement_matched and not allow_candidate_materialization_write:
        errors.append("candidate_materialization_write_flag_required")

    source_materializer_execution_performed = False
    candidate_materialization_write_performed = False
    materialized_candidate_paths = {}
    materialized_candidates = {}
    materializer_receipt = {}

    if plan_ready and operator_statement_matched and allow_candidate_materialization_write:
        materializer_context = {
            "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SCHEMA_VERSION,
            "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SURFACE_ID,
            "generated_at_utc": timestamp,
            "vault_root": str(vault),
            "materialization_root": root_descriptor.get("resolved_path"),
            "source_materializer_label": str(source_materializer_label or ""),
            "candidate_roles": roles,
            "target_candidate_paths": target_descriptors,
            "required_symbols_by_role": required_symbols,
            "source_candidate_supply_readiness_digest_sha256": supply_digest,
            "source_regeneration_readiness_digest_sha256": regeneration_digest,
        }
        try:
            materializer_receipt = source_materializer(materializer_context)
            source_materializer_execution_performed = True
        except Exception as exc:
            materializer_receipt = {
                "ok": False,
                "error": f"source_candidate_materializer_failed:{exc.__class__.__name__}",
            }
            errors.append("source_candidate_materializer_failed")

        generated_sources = {}
        if isinstance(materializer_receipt, dict):
            generated_sources = materializer_receipt.get("generated_sources") or {}
        if source_materializer_execution_performed:
            missing_roles = [role for role in roles if role not in generated_sources]
            if missing_roles:
                errors.append("source_candidate_materializer_missing_roles")
            pending_writes = {}
            for role in roles:
                raw_source = generated_sources.get(role)
                if isinstance(raw_source, str):
                    payload = raw_source.encode("utf-8")
                elif isinstance(raw_source, bytes):
                    payload = raw_source
                else:
                    payload = b""
                if not payload:
                    errors.append(f"{role}_materialized_source_missing")
                    continue
                target_path = targets[role]
                if target_path.exists():
                    errors.append(f"{role}_materialized_candidate_already_exists")
                    continue
                pending_writes[role] = (target_path, payload)
            if not any(
                error.endswith("_materialized_source_missing")
                or error.endswith("_materialized_candidate_already_exists")
                for error in errors
            ) and "source_candidate_materializer_missing_roles" not in errors:
                for role, (target_path, payload) in pending_writes.items():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_bytes(payload)
                    materialized_candidate_paths[role] = [str(target_path)]
                    materialized_candidates[role] = {
                        "role": role,
                        "path": str(target_path),
                        "size_bytes": len(payload),
                        "sha256": _wrapper_hashlib.sha256(payload).hexdigest(),
                    }
                candidate_materialization_write_performed = bool(
                    materialized_candidate_paths
                )

    post_materialization_supply_readiness = (
        build_launcher_update_real_authoritative_source_candidate_supply_readiness(
            vault,
            candidate_roots=[root],
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
    )
    post_materialization_ready = bool(
        post_materialization_supply_readiness.get("ok")
        and post_materialization_supply_readiness.get(
            "ready_for_authoritative_import_boundary"
        )
    )
    if post_materialization_ready:
        errors = [
            error
            for error in errors
            if error != "real_authoritative_source_candidates_missing"
        ]
    if candidate_materialization_write_performed and not post_materialization_ready:
        errors.append("materialized_candidates_failed_real_supply_readiness")

    ready_for_import_boundary = bool(supply_ready or post_materialization_ready)
    candidate_import_preview = (
        source_candidate_supply_readiness.get("candidate_import_preview")
        if supply_ready
        else post_materialization_supply_readiness.get("candidate_import_preview")
    ) or {}
    candidate_import_statement = candidate_import_preview.get(
        "required_operator_statement",
        "",
    )

    status = "launcher_update_real_authoritative_source_candidate_materialization_blocked"
    if supply_ready:
        status = (
            "launcher_update_real_authoritative_source_candidate_materialization_"
            "already_ready_for_import_boundary"
        )
    elif plan_ready and not operator_statement_matched:
        status = (
            "launcher_update_real_authoritative_source_candidate_materialization_"
            "pending_approval"
        )
    elif plan_ready and operator_statement_matched and not allow_candidate_materialization_write:
        status = (
            "launcher_update_real_authoritative_source_candidate_materialization_"
            "write_flag_required"
        )
    elif candidate_materialization_write_performed and post_materialization_ready:
        status = (
            "launcher_update_real_authoritative_source_candidate_materialization_"
            "candidates_materialized"
        )

    proof = {
        "ok": ready_for_import_boundary,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SURFACE_ID,
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "materialization_root": str(root),
        "errors": errors,
        "warnings": warnings,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "materialization_plan_ready": plan_ready,
        "candidate_materialization_write_enabled": bool(
            allow_candidate_materialization_write
        ),
        "candidate_materialization_write_performed": (
            candidate_materialization_write_performed
        ),
        "source_materializer_execution_performed": (
            source_materializer_execution_performed
        ),
        "source_materializer_label": str(source_materializer_label or ""),
        "source_candidate_supply_ready": supply_ready,
        "source_candidate_supply_readiness_digest_matched": supply_digest_matched,
        "source_regeneration_ready": regeneration_ready,
        "source_regeneration_readiness_digest_matched": regeneration_digest_matched,
        "materialization_plan": materialization_plan,
        "materializer_receipt": (
            _real_authoritative_source_candidate_materializer_receipt_summary(
                materializer_receipt
            )
        ),
        "materialized_candidate_paths": materialized_candidate_paths,
        "materialized_candidates": materialized_candidates,
        "post_materialization_supply_readiness": post_materialization_supply_readiness,
        "post_materialization_ready_for_import_boundary": post_materialization_ready,
        "ready_for_authoritative_import_boundary": ready_for_import_boundary,
        "ready_for_candidate_import_approval": ready_for_import_boundary,
        "candidate_import_preview": candidate_import_preview,
        "required_candidate_import_operator_statement": candidate_import_statement,
        "source_write_performed": False,
        "candidate_import_write_performed": False,
        "candidate_import_performed": False,
        "wrapper_removal_performed": False,
        "current_vault_wrappers_removed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_authoritative_source_candidate_import_boundary_with_exact_approval"
            if ready_for_import_boundary
            else "provide_injected_source_materializer_and_exact_materialization_approval"
        ),
        "authority": _authority(
            real_authoritative_source_candidate_materialization_built=True,
            real_authoritative_source_candidate_materialization_plan_ready=plan_ready,
            real_authoritative_source_candidate_materialization_statement_matched=(
                operator_statement_matched
            ),
            real_authoritative_source_candidate_materialization_source_materializer_execution_performed=(
                source_materializer_execution_performed
            ),
            real_authoritative_source_candidate_materialization_candidate_write_performed=(
                candidate_materialization_write_performed
            ),
            real_authoritative_source_candidate_materialization_ready_for_import_boundary=(
                ready_for_import_boundary
            ),
            real_authoritative_source_candidate_materialization_source_write_performed=False,
            real_authoritative_source_candidate_materialization_candidate_import_write_performed=False,
            real_authoritative_source_candidate_materialization_settings_write_control_exposed=False,
            real_authoritative_source_candidate_materialization_primary_real_exe_replacement_performed=False,
            real_authoritative_source_candidate_materialization_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["real_authoritative_source_candidate_materialization_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "real_authoritative_source_candidate_materialization_digest_sha256",
        )
    )
    return proof


def _real_authoritative_source_candidate_import_paths_from_materialization(
    materialization_proof,
):
    paths = (materialization_proof or {}).get("materialized_candidate_paths") or {}
    if paths:
        return paths
    post_supply = (
        (materialization_proof or {}).get("post_materialization_supply_readiness")
        or {}
    )
    paths = post_supply.get("candidate_import_paths") or {}
    if paths:
        return paths
    import_preview = (materialization_proof or {}).get("candidate_import_preview") or {}
    return import_preview.get("import_candidate_paths") or {}


def required_update_real_authoritative_source_candidate_import_from_materialization_operator_statement(
    import_from_materialization_plan,
):
    digest = str(
        (import_from_materialization_plan or {}).get(
            "import_from_materialization_plan_digest_sha256"
        )
        or _extension_digest_without(
            import_from_materialization_plan or {},
            "import_from_materialization_plan_digest_sha256",
        )
    )
    return (
        f"{REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
    vault_root,
    *,
    materialization_proof=None,
    candidate_root=None,
    required_symbols_by_role=None,
    operator_approved_import_from_materialization=False,
    operator_statement="",
    allow_candidate_import_write=False,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    materialization = _extension_unwrap_api_data(
        materialization_proof or {},
        "launcher_update_real_authoritative_source_candidate_materialization_proof",
    )
    materialization = _extension_unwrap_api_data(
        materialization or {},
        REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SURFACE_ID,
    )
    if not isinstance(materialization, dict):
        materialization = {}

    errors = []
    warnings = []
    if materialization.get("warnings"):
        warnings.extend(str(item) for item in materialization.get("warnings") or [])
    if not materialization:
        errors.append("real_authoritative_source_candidate_materialization_proof_required")
    elif materialization.get("surface") != REAL_AUTHORITATIVE_SOURCE_CANDIDATE_MATERIALIZATION_SURFACE_ID:
        errors.append("real_authoritative_source_candidate_materialization_surface_mismatch")

    materialization_digest = str(
        materialization.get(
            "real_authoritative_source_candidate_materialization_digest_sha256"
        )
        or ""
    )
    materialization_digest_matched = False
    if materialization:
        materialization_digest_matched = bool(
            materialization_digest
            and materialization_digest
            == _extension_digest_without(
                materialization,
                "real_authoritative_source_candidate_materialization_digest_sha256",
            )
        )
        if not materialization_digest_matched:
            errors.append("real_authoritative_source_candidate_materialization_digest_mismatch")

    materialization_ready = bool(
        materialization.get("ok")
        and materialization.get("ready_for_authoritative_import_boundary")
        and materialization_digest_matched
    )
    if materialization and not materialization_ready:
        errors.append("real_authoritative_source_candidate_materialization_not_ready")

    import_candidate_paths = (
        _real_authoritative_source_candidate_import_paths_from_materialization(
            materialization
        )
    )
    target_candidate_root = _authoritative_normal_source_candidate_supply_root(
        vault,
        candidate_root,
    )
    import_preview = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        vault,
        import_candidate_paths=import_candidate_paths,
        candidate_root=target_candidate_root,
        required_symbols_by_role=required_symbols,
        generated_at=timestamp,
    )
    import_plan_ready = bool(import_preview.get("candidate_import_plan_ready"))
    import_plan_digest = str(
        (import_preview.get("candidate_import_plan") or {}).get(
            "candidate_import_plan_digest_sha256"
        )
        or ""
    )
    required_import_boundary_statement = str(
        import_preview.get("required_operator_statement") or ""
    )
    if import_preview.get("warnings"):
        warnings.extend(str(item) for item in import_preview.get("warnings") or [])
    if materialization_ready and not import_plan_ready:
        errors.append("authoritative_source_candidate_import_plan_not_ready")

    import_from_materialization_plan = {
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SCHEMA_VERSION,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SURFACE_ID,
        "vault_root": str(vault),
        "source_materialization_digest_sha256": materialization_digest,
        "source_materialization_status": materialization.get("status"),
        "source_materialization_digest_matched": materialization_digest_matched,
        "source_materialization_ready": materialization_ready,
        "target_candidate_root": str(target_candidate_root),
        "import_candidate_paths": {
            role: [
                str(path)
                for path in _normal_source_candidate_role_paths(
                    import_candidate_paths,
                    role,
                )
            ]
            for role in [
                "launcher_update_check",
                "studio_shell_api",
                "studio_shell_test_pass10a",
            ]
        },
        "authoritative_import_plan_ready": import_plan_ready,
        "authoritative_import_plan_digest_sha256": import_plan_digest,
        "required_authoritative_import_operator_statement": (
            required_import_boundary_statement
        ),
        "required_symbols_by_role": required_symbols,
        "requires_exact_operator_statement": True,
        "requires_explicit_candidate_import_write_flag": True,
        "delegates_to_authoritative_source_candidate_import_boundary": True,
        "writes_authoritative_candidate_staging_root_only": True,
        "writes_live_source_targets": False,
        "runs_decompiler": False,
        "executes_candidate_source": False,
        "launches_installer_or_helper": False,
        "replaces_primary_exe": False,
    }
    import_from_materialization_plan[
        "import_from_materialization_plan_digest_sha256"
    ] = _extension_digest_without(
        import_from_materialization_plan,
        "import_from_materialization_plan_digest_sha256",
    )
    required_statement = (
        required_update_real_authoritative_source_candidate_import_from_materialization_operator_statement(
            import_from_materialization_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_import_from_materialization
        and str(operator_statement) == required_statement
    )

    plan_ready = bool(materialization_ready and import_plan_ready)
    if plan_ready and not operator_approved_import_from_materialization:
        errors.append("operator_import_from_materialization_approval_required")
    elif plan_ready and not operator_statement_matched:
        errors.append("operator_import_from_materialization_statement_mismatch")
    if plan_ready and operator_statement_matched and not allow_candidate_import_write:
        errors.append("candidate_import_from_materialization_write_flag_required")

    authoritative_import_proof = {}
    candidate_import_write_performed = False
    if plan_ready and operator_statement_matched and allow_candidate_import_write:
        authoritative_import_proof = (
            build_launcher_update_authoritative_source_candidate_import_boundary_proof(
                vault,
                import_candidate_paths=import_candidate_paths,
                candidate_root=target_candidate_root,
                required_symbols_by_role=required_symbols,
                operator_approved_candidate_import=True,
                operator_statement=required_import_boundary_statement,
                allow_candidate_import_write=True,
                generated_at=timestamp,
            )
        )
        if authoritative_import_proof.get("warnings"):
            warnings.extend(
                str(item) for item in authoritative_import_proof.get("warnings") or []
            )
        if authoritative_import_proof.get("errors"):
            errors.extend(
                str(item) for item in authoritative_import_proof.get("errors") or []
            )
        candidate_import_write_performed = bool(
            authoritative_import_proof.get("ok")
            and authoritative_import_proof.get("candidate_import_write_performed")
        )

    post_import_supply_packet_preview = (
        authoritative_import_proof.get("post_import_supply_packet_preview") or {}
    )
    post_import_supply_packet_candidates_available = bool(
        authoritative_import_proof.get("post_import_supply_packet_candidates_available")
    )
    ready_for_candidate_supply_approval = bool(
        candidate_import_write_performed
        and authoritative_import_proof.get("ready_for_candidate_supply_approval")
    )

    status = (
        "launcher_update_real_authoritative_source_candidate_import_from_materialization_blocked"
    )
    if plan_ready and not operator_statement_matched:
        status = (
            "launcher_update_real_authoritative_source_candidate_import_from_"
            "materialization_pending_approval"
        )
    if plan_ready and operator_statement_matched and not allow_candidate_import_write:
        status = (
            "launcher_update_real_authoritative_source_candidate_import_from_"
            "materialization_write_flag_required"
        )
    if candidate_import_write_performed:
        status = (
            "launcher_update_real_authoritative_source_candidate_import_from_"
            "materialization_imported"
        )

    proof = {
        "ok": candidate_import_write_performed,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SURFACE_ID,
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "candidate_root": str(target_candidate_root),
        "errors": errors,
        "warnings": warnings,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "materialization_digest_sha256": materialization_digest,
        "materialization_digest_matched": materialization_digest_matched,
        "materialization_ready_for_import_boundary": materialization_ready,
        "import_from_materialization_plan_ready": plan_ready,
        "candidate_import_write_enabled": bool(allow_candidate_import_write),
        "candidate_import_write_performed": candidate_import_write_performed,
        "candidate_import_performed": candidate_import_write_performed,
        "import_from_materialization_plan": import_from_materialization_plan,
        "import_candidate_paths": import_candidate_paths,
        "authoritative_import_preview": import_preview,
        "required_authoritative_import_operator_statement": (
            required_import_boundary_statement
        ),
        "authoritative_source_candidate_import_boundary_proof": (
            authoritative_import_proof
        ),
        "post_import_supply_packet_preview": post_import_supply_packet_preview,
        "post_import_supply_packet_candidates_available": (
            post_import_supply_packet_candidates_available
        ),
        "ready_for_candidate_supply_approval": ready_for_candidate_supply_approval,
        "source_write_performed": False,
        "wrapper_removal_performed": False,
        "current_vault_wrappers_removed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "approve_authoritative_candidate_supply_and_run_verifier"
            if ready_for_candidate_supply_approval
            else "provide_ready_materialization_proof_and_exact_import_approval"
        ),
        "authority": _authority(
            real_authoritative_source_candidate_import_from_materialization_built=True,
            real_authoritative_source_candidate_import_from_materialization_plan_ready=(
                plan_ready
            ),
            real_authoritative_source_candidate_import_from_materialization_statement_matched=(
                operator_statement_matched
            ),
            real_authoritative_source_candidate_import_from_materialization_candidate_import_write_performed=(
                candidate_import_write_performed
            ),
            real_authoritative_source_candidate_import_from_materialization_ready_for_candidate_supply_approval=(
                ready_for_candidate_supply_approval
            ),
            real_authoritative_source_candidate_import_from_materialization_source_write_performed=False,
            real_authoritative_source_candidate_import_from_materialization_settings_write_control_exposed=False,
            real_authoritative_source_candidate_import_from_materialization_primary_real_exe_replacement_performed=False,
            real_authoritative_source_candidate_import_from_materialization_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["real_authoritative_source_candidate_import_from_materialization_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "real_authoritative_source_candidate_import_from_materialization_digest_sha256",
        )
    )
    return proof


def required_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_operator_statement(
    supply_verification_from_materialization_import_plan,
):
    digest = str(
        (
            supply_verification_from_materialization_import_plan
            or {}
        ).get("supply_verification_from_materialization_import_plan_digest_sha256")
        or _extension_digest_without(
            supply_verification_from_materialization_import_plan or {},
            "supply_verification_from_materialization_import_plan_digest_sha256",
        )
    )
    return (
        f"{REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
    vault_root,
    *,
    import_from_materialization_proof=None,
    candidate_root=None,
    required_symbols_by_role=None,
    operator_approved_supply_verification_from_materialization_import=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    errors = []
    warnings = []

    import_from_materialization = _extension_unwrap_api_data(
        import_from_materialization_proof or {},
        "launcher_update_real_authoritative_source_candidate_import_from_materialization_proof",
    )
    import_from_materialization = _extension_unwrap_api_data(
        import_from_materialization or {},
        REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SURFACE_ID,
    )
    if not isinstance(import_from_materialization, dict):
        import_from_materialization = {}

    if import_from_materialization.get("warnings"):
        warnings.extend(
            str(item) for item in import_from_materialization.get("warnings") or []
        )
    if not import_from_materialization:
        errors.append(
            "real_authoritative_source_candidate_import_from_materialization_proof_required"
        )
    elif (
        import_from_materialization.get("surface")
        != REAL_AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_FROM_MATERIALIZATION_SURFACE_ID
    ):
        errors.append(
            "real_authoritative_source_candidate_import_from_materialization_surface_mismatch"
        )

    import_from_materialization_digest = str(
        import_from_materialization.get(
            "real_authoritative_source_candidate_import_from_materialization_digest_sha256"
        )
        or ""
    )
    import_from_materialization_digest_matched = False
    if import_from_materialization:
        import_from_materialization_digest_matched = bool(
            import_from_materialization_digest
            and import_from_materialization_digest
            == _extension_digest_without(
                import_from_materialization,
                "real_authoritative_source_candidate_import_from_materialization_digest_sha256",
            )
        )
        if not import_from_materialization_digest_matched:
            errors.append(
                "real_authoritative_source_candidate_import_from_materialization_digest_mismatch"
            )

    import_from_materialization_ready = bool(
        import_from_materialization_digest_matched
        and import_from_materialization.get("ok")
        and import_from_materialization.get("candidate_import_write_performed")
        and import_from_materialization.get("ready_for_candidate_supply_approval")
    )
    if import_from_materialization and not import_from_materialization_ready:
        errors.append(
            "real_authoritative_source_candidate_import_from_materialization_not_ready"
        )

    embedded_import_boundary = (
        import_from_materialization.get(
            "authoritative_source_candidate_import_boundary_proof"
        )
        or {}
    )
    embedded_import_boundary = _extension_unwrap_api_data(
        embedded_import_boundary,
        "launcher_update_authoritative_source_candidate_import_boundary_proof",
    )
    embedded_import_boundary = _extension_unwrap_api_data(
        embedded_import_boundary or {},
        AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SURFACE_ID,
    )
    if not isinstance(embedded_import_boundary, dict):
        embedded_import_boundary = {}

    embedded_import_boundary_digest = str(
        embedded_import_boundary.get(
            "authoritative_source_candidate_import_boundary_digest_sha256"
        )
        or ""
    )
    embedded_import_boundary_digest_matched = False
    if embedded_import_boundary:
        embedded_import_boundary_digest_matched = bool(
            embedded_import_boundary_digest
            and embedded_import_boundary_digest
            == _extension_digest_without(
                embedded_import_boundary,
                "authoritative_source_candidate_import_boundary_digest_sha256",
            )
        )
        if not embedded_import_boundary_digest_matched:
            errors.append(
                "authoritative_source_candidate_import_boundary_from_materialization_digest_mismatch"
            )

    embedded_import_boundary_ready = bool(
        embedded_import_boundary_digest_matched
        and embedded_import_boundary.get("ok")
        and embedded_import_boundary.get("candidate_import_write_performed")
        and embedded_import_boundary.get("ready_for_candidate_supply_approval")
    )
    if import_from_materialization_ready and not embedded_import_boundary_ready:
        errors.append(
            "authoritative_source_candidate_import_boundary_from_materialization_not_ready"
        )

    resolved_candidate_root = _authoritative_normal_source_candidate_supply_root(
        vault,
        candidate_root
        or import_from_materialization.get("candidate_root")
        or embedded_import_boundary.get("candidate_root")
        or None,
    )
    after_import_verification_preview = {}
    if embedded_import_boundary:
        after_import_verification_preview = (
            build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
                vault,
                source_candidate_import_boundary_proof=embedded_import_boundary,
                candidate_root=resolved_candidate_root,
                required_symbols_by_role=required_symbols,
                generated_at=timestamp,
            )
        )
        if after_import_verification_preview.get("warnings"):
            warnings.extend(
                str(item)
                for item in after_import_verification_preview.get("warnings") or []
            )

    after_import_preview_import_verified = bool(
        after_import_verification_preview.get("import_boundary_verified")
    )
    required_candidate_supply_statement = str(
        (
            after_import_verification_preview.get("candidate_supply_preview")
            or {}
        ).get("required_operator_statement")
        or ""
    )
    required_candidate_verification_statement = str(
        (
            after_import_verification_preview.get("candidate_verification_preview")
            or {}
        ).get("required_operator_statement")
        or ""
    )
    after_import_preview_digest = str(
        after_import_verification_preview.get(
            "authoritative_candidate_supply_verification_after_import_digest_sha256"
        )
        or ""
    )

    plan_ready = bool(
        import_from_materialization_ready
        and embedded_import_boundary_ready
        and after_import_preview_import_verified
        and required_candidate_supply_statement
        and required_candidate_verification_statement
    )
    if import_from_materialization_ready and not plan_ready:
        errors.append(
            "authoritative_candidate_supply_verification_from_materialization_import_plan_not_ready"
        )

    supply_verification_plan = {
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SCHEMA_VERSION,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID,
        "vault_root": str(vault),
        "candidate_root": str(resolved_candidate_root),
        "source_import_from_materialization_digest_sha256": (
            import_from_materialization_digest
        ),
        "source_import_from_materialization_digest_matched": (
            import_from_materialization_digest_matched
        ),
        "source_import_from_materialization_ready": (
            import_from_materialization_ready
        ),
        "source_import_candidate_write_already_performed": bool(
            import_from_materialization.get("candidate_import_write_performed")
        ),
        "embedded_import_boundary_digest_sha256": embedded_import_boundary_digest,
        "embedded_import_boundary_digest_matched": (
            embedded_import_boundary_digest_matched
        ),
        "embedded_import_boundary_ready": embedded_import_boundary_ready,
        "after_import_preview_digest_sha256": after_import_preview_digest,
        "after_import_preview_import_verified": after_import_preview_import_verified,
        "required_candidate_supply_operator_statement": (
            required_candidate_supply_statement
        ),
        "required_candidate_verification_operator_statement": (
            required_candidate_verification_statement
        ),
        "plan_ready_for_after_import_verifier": plan_ready,
        "required_symbols_by_role": required_symbols,
        "requires_exact_operator_statement": True,
        "delegates_to_authoritative_candidate_supply_verification_after_import": True,
        "reuses_imported_materialized_candidates": True,
        "writes_live_source_targets": False,
        "runs_decompiler": False,
        "executes_candidate_source": False,
        "launches_installer_or_helper": False,
        "replaces_primary_exe": False,
        "settings_write_control_exposed": False,
    }
    supply_verification_plan[
        "supply_verification_from_materialization_import_plan_digest_sha256"
    ] = _extension_digest_without(
        supply_verification_plan,
        "supply_verification_from_materialization_import_plan_digest_sha256",
    )
    required_statement = (
        required_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_operator_statement(
            supply_verification_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_supply_verification_from_materialization_import
        and str(operator_statement) == required_statement
    )
    if plan_ready:
        if (
            not operator_approved_supply_verification_from_materialization_import
        ):
            errors.append(
                "operator_supply_verification_from_materialization_import_approval_required"
            )
        elif not operator_statement_matched:
            errors.append(
                "operator_supply_verification_from_materialization_import_statement_mismatch"
            )

    after_import_verification_proof = {}
    if plan_ready and operator_statement_matched:
        after_import_verification_proof = (
            build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
                vault,
                source_candidate_import_boundary_proof=embedded_import_boundary,
                candidate_root=resolved_candidate_root,
                required_symbols_by_role=required_symbols,
                operator_approved_candidate_supply=True,
                candidate_supply_statement=required_candidate_supply_statement,
                operator_approved_candidate_verification=True,
                candidate_verification_statement=required_candidate_verification_statement,
                generated_at=timestamp,
            )
        )
        if after_import_verification_proof.get("warnings"):
            warnings.extend(
                str(item)
                for item in after_import_verification_proof.get("warnings") or []
            )
        if after_import_verification_proof.get("errors"):
            errors.extend(
                str(item)
                for item in after_import_verification_proof.get("errors") or []
            )

    ready_for_wrapper_removal_executor = bool(
        after_import_verification_proof.get("ok")
        and after_import_verification_proof.get("ready_for_wrapper_removal_executor")
    )
    candidate_supply_packet_ready = bool(
        after_import_verification_proof.get("candidate_supply_packet_ready")
    )
    candidate_verification_ready = bool(
        after_import_verification_proof.get("candidate_verification_ready")
    )
    if plan_ready and operator_statement_matched and not ready_for_wrapper_removal_executor:
        errors.append(
            "authoritative_candidate_supply_verification_from_materialization_import_not_ready"
        )

    status = (
        "launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_blocked"
    )
    if plan_ready and not operator_statement_matched:
        status = (
            "launcher_update_real_authoritative_source_candidate_supply_verification_"
            "from_materialization_import_pending_approval"
        )
    if plan_ready and operator_statement_matched and not ready_for_wrapper_removal_executor:
        status = (
            "launcher_update_real_authoritative_source_candidate_supply_verification_"
            "from_materialization_import_verification_failed"
        )
    if ready_for_wrapper_removal_executor:
        status = (
            "launcher_update_real_authoritative_source_candidate_supply_verification_"
            "from_materialization_import_ready_for_wrapper_removal_executor"
        )

    proof = {
        "ok": ready_for_wrapper_removal_executor,
        "surface": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID,
        "schema_version": REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "candidate_root": str(resolved_candidate_root),
        "errors": errors,
        "warnings": warnings,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "import_from_materialization_digest_sha256": (
            import_from_materialization_digest
        ),
        "import_from_materialization_digest_matched": (
            import_from_materialization_digest_matched
        ),
        "import_from_materialization_ready_for_supply_verification": (
            import_from_materialization_ready
        ),
        "embedded_import_boundary_digest_sha256": embedded_import_boundary_digest,
        "embedded_import_boundary_digest_matched": (
            embedded_import_boundary_digest_matched
        ),
        "embedded_import_boundary_ready": embedded_import_boundary_ready,
        "supply_verification_from_materialization_import_plan_ready": plan_ready,
        "supply_verification_from_materialization_import_plan": (
            supply_verification_plan
        ),
        "after_import_verification_preview": after_import_verification_preview,
        "required_candidate_supply_operator_statement": (
            required_candidate_supply_statement
        ),
        "required_candidate_verification_operator_statement": (
            required_candidate_verification_statement
        ),
        "after_import_verification_proof": after_import_verification_proof,
        "candidate_supply_packet_ready": candidate_supply_packet_ready,
        "candidate_verification_ready": candidate_verification_ready,
        "ready_for_wrapper_removal_executor": ready_for_wrapper_removal_executor,
        "source_import_candidate_write_already_performed": bool(
            import_from_materialization.get("candidate_import_write_performed")
        ),
        "candidate_import_write_performed": False,
        "source_write_performed": False,
        "wrapper_removal_performed": False,
        "current_vault_wrappers_removed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_current_vault_wrapper_removal_after_materialization_import_execution_with_exact_approval"
            if ready_for_wrapper_removal_executor
            else "provide_ready_import_from_materialization_proof_and_exact_supply_verification_approval"
        ),
        "authority": _authority(
            real_authoritative_source_candidate_supply_verification_from_materialization_import_built=True,
            real_authoritative_source_candidate_supply_verification_from_materialization_import_plan_ready=plan_ready,
            real_authoritative_source_candidate_supply_verification_from_materialization_import_statement_matched=operator_statement_matched,
            real_authoritative_source_candidate_supply_verification_from_materialization_import_ready_for_wrapper_removal_executor=ready_for_wrapper_removal_executor,
            real_authoritative_source_candidate_supply_verification_from_materialization_import_source_write_performed=False,
            real_authoritative_source_candidate_supply_verification_from_materialization_import_settings_write_control_exposed=False,
            real_authoritative_source_candidate_supply_verification_from_materialization_import_primary_real_exe_replacement_performed=False,
            real_authoritative_source_candidate_supply_verification_from_materialization_import_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof[
        "real_authoritative_source_candidate_supply_verification_from_materialization_import_digest_sha256"
    ] = _extension_digest_without(
        proof,
        "real_authoritative_source_candidate_supply_verification_from_materialization_import_digest_sha256",
    )
    return proof


def _authoritative_import_target_candidate_paths(import_proof, vault, candidate_root):
    paths = (
        (import_proof or {}).get("target_candidate_paths")
        if isinstance((import_proof or {}).get("target_candidate_paths"), dict)
        else {}
    )
    if paths:
        return paths
    return {
        role: [str(path) for path in role_paths]
        for role, role_paths in _authoritative_source_candidate_import_targets(
            vault,
            candidate_root,
        ).items()
    }


def _authoritative_import_target_revalidation(
    *,
    vault,
    candidate_paths,
    required_symbols_by_role,
    import_results,
):
    revalidation = {}
    for role in [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]:
        descriptors = [
            _normal_source_candidate_verification_descriptor(
                vault=vault,
                role=role,
                path=path,
                required_symbols=required_symbols_by_role.get(role, []),
            )
            for path in _normal_source_candidate_role_paths(candidate_paths, role)
        ]
        verified = _authoritative_source_candidate_verified_import_descriptor(
            descriptors
        )
        expected_hash = str(
            ((import_results or {}).get(role) or {}).get("after_sha256") or ""
        )
        hash_matches_import_receipt = bool(
            verified
            and (not expected_hash or verified.get("sha256") == expected_hash)
        )
        revalidation[role] = {
            "role": role,
            "candidate_paths": [
                item.get("path", "") for item in descriptors
            ],
            "candidate_verification_passed": bool(
                verified.get("candidate_verification_passed")
            ),
            "sha256": str(verified.get("sha256") or ""),
            "expected_import_receipt_sha256": expected_hash,
            "hash_matches_import_receipt": hash_matches_import_receipt,
            "errors": [
                error
                for item in descriptors
                for error in (item.get("errors") or [])
            ],
        }
        if not descriptors:
            revalidation[role]["errors"].append("import_target_candidate_path_required")
    return revalidation


def build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
    vault_root,
    *,
    source_candidate_import_boundary_proof=None,
    candidate_root=None,
    required_symbols_by_role=None,
    operator_approved_candidate_supply=False,
    candidate_supply_statement="",
    operator_approved_candidate_verification=False,
    candidate_verification_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    errors = []
    warnings = []

    import_proof = _extension_unwrap_api_data(
        source_candidate_import_boundary_proof or {},
        "launcher_update_authoritative_source_candidate_import_boundary_proof",
    )
    import_proof = _extension_unwrap_api_data(
        import_proof or {},
        AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SURFACE_ID,
    )
    if not isinstance(import_proof, dict):
        import_proof = {}

    if import_proof.get("warnings"):
        warnings.extend(str(item) for item in import_proof.get("warnings") or [])
    if not import_proof:
        errors.append("authoritative_source_candidate_import_boundary_proof_required")
    elif import_proof.get("surface") != AUTHORITATIVE_SOURCE_CANDIDATE_IMPORT_BOUNDARY_SURFACE_ID:
        errors.append("authoritative_source_candidate_import_boundary_surface_mismatch")

    import_digest = str(
        import_proof.get("authoritative_source_candidate_import_boundary_digest_sha256")
        or ""
    )
    import_digest_valid = False
    if import_proof:
        import_digest_valid = bool(
            import_digest
            and import_digest
            == _extension_digest_without(
                import_proof,
                "authoritative_source_candidate_import_boundary_digest_sha256",
            )
        )
        if not import_digest_valid:
            errors.append("authoritative_source_candidate_import_boundary_digest_mismatch")
        if not (
            import_proof.get("ok")
            and import_proof.get("candidate_import_performed")
            and import_proof.get("candidate_import_write_performed")
        ):
            errors.append("authoritative_source_candidate_import_boundary_not_imported")

    resolved_candidate_root = _authoritative_normal_source_candidate_supply_root(
        vault,
        candidate_root or import_proof.get("candidate_root") or None,
    )
    imported_candidate_paths = _authoritative_import_target_candidate_paths(
        import_proof,
        vault,
        resolved_candidate_root,
    )
    target_revalidation = _authoritative_import_target_revalidation(
        vault=vault,
        candidate_paths=imported_candidate_paths,
        required_symbols_by_role=required_symbols,
        import_results=import_proof.get("candidate_import_results") or {},
    )
    target_revalidation_ready = bool(
        target_revalidation
        and all(
            item.get("candidate_verification_passed")
            and item.get("hash_matches_import_receipt")
            for item in target_revalidation.values()
        )
    )
    if import_proof and not target_revalidation_ready:
        errors.append("authoritative_source_candidate_import_targets_revalidation_failed")

    import_boundary_verified = bool(
        import_digest_valid
        and import_proof.get("ok")
        and import_proof.get("candidate_import_performed")
        and target_revalidation_ready
    )

    candidate_supply_preview = {}
    authoritative_candidate_supply_packet = {}
    supply_packet_ready = False
    supply_statement_matched = False
    if import_boundary_verified:
        candidate_supply_preview = (
            build_launcher_update_authoritative_normal_source_candidate_supply_packet(
                vault,
                candidate_root=resolved_candidate_root,
                required_symbols_by_role=required_symbols,
                generated_at=timestamp,
            )
        )
        expected_supply_statement = candidate_supply_preview.get(
            "required_operator_statement",
            "",
        )
        supply_statement_matched = bool(
            operator_approved_candidate_supply
            and str(candidate_supply_statement) == expected_supply_statement
        )
        if not operator_approved_candidate_supply:
            errors.append("operator_candidate_supply_approval_required")
        elif not supply_statement_matched:
            errors.append("operator_candidate_supply_statement_mismatch")
        authoritative_candidate_supply_packet = (
            build_launcher_update_authoritative_normal_source_candidate_supply_packet(
                vault,
                candidate_root=resolved_candidate_root,
                required_symbols_by_role=required_symbols,
                operator_approved_candidate_supply=operator_approved_candidate_supply,
                operator_statement=candidate_supply_statement,
                generated_at=timestamp,
            )
        )
        if authoritative_candidate_supply_packet.get("warnings"):
            warnings.extend(
                str(item)
                for item in authoritative_candidate_supply_packet.get("warnings") or []
            )
        supply_packet_ready = bool(
            authoritative_candidate_supply_packet.get("ok")
            and authoritative_candidate_supply_packet.get("ready_for_candidate_verifier")
        )

    candidate_paths_for_verifier = (
        authoritative_candidate_supply_packet.get("candidate_paths")
        or imported_candidate_paths
    )
    candidate_verification_preview = {}
    candidate_verification_proof = {}
    candidate_verification_ready = False
    candidate_verification_statement_matched = False
    if import_boundary_verified:
        candidate_verification_preview = (
            build_launcher_update_normal_source_candidate_verification_proof(
                vault,
                candidate_paths=candidate_paths_for_verifier,
                required_symbols_by_role=required_symbols,
                generated_at=timestamp,
            )
        )
        expected_verification_statement = candidate_verification_preview.get(
            "required_operator_statement",
            "",
        )
        candidate_verification_statement_matched = bool(
            operator_approved_candidate_verification
            and str(candidate_verification_statement)
            == expected_verification_statement
        )
        if supply_packet_ready:
            if not operator_approved_candidate_verification:
                errors.append("operator_candidate_verification_approval_required")
            elif not candidate_verification_statement_matched:
                errors.append("operator_candidate_verification_statement_mismatch")
        if supply_packet_ready:
            candidate_verification_proof = (
                build_launcher_update_normal_source_candidate_verification_proof(
                    vault,
                    candidate_paths=candidate_paths_for_verifier,
                    required_symbols_by_role=required_symbols,
                    operator_approved_candidate_verification=operator_approved_candidate_verification,
                    operator_statement=candidate_verification_statement,
                    generated_at=timestamp,
                )
            )
            candidate_verification_ready = bool(
                candidate_verification_proof.get("ok")
                and candidate_verification_proof.get(
                    "source_restoration_candidate_verification_ready"
                )
            )

    role_candidate_path_matches = _current_vault_wrapper_removal_candidate_paths_match(
        authoritative_candidate_supply_packet,
        candidate_verification_proof,
    )
    ready_for_wrapper_removal_executor = bool(
        import_boundary_verified
        and supply_packet_ready
        and candidate_verification_ready
        and role_candidate_path_matches
        and all(role_candidate_path_matches.values())
    )

    readiness_bundle = {
        "schema_version": AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SCHEMA_VERSION,
        "surface": AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SURFACE_ID,
        "source_candidate_import_boundary_digest_sha256": import_digest,
        "candidate_root": str(resolved_candidate_root),
        "import_boundary_verified": import_boundary_verified,
        "supply_packet_ready": supply_packet_ready,
        "candidate_verification_ready": candidate_verification_ready,
        "role_candidate_path_matches": role_candidate_path_matches,
        "ready_for_wrapper_removal_executor": ready_for_wrapper_removal_executor,
        "source_write_allowed": False,
        "wrapper_removal_allowed": False,
        "decompiler_execution_allowed": False,
        "candidate_source_execution_allowed": False,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
        "forbidden_behaviors": [
            "write_live_source",
            "remove_current_vault_wrappers",
            "decompile_bytecode",
            "execute_candidate_source",
            "launch_installer",
            "launch_helper",
            "replace_primary_exe",
            "mutate_startup",
            "publish_github_release",
        ],
    }
    readiness_bundle["readiness_bundle_digest_sha256"] = (
        _extension_digest_without(
            readiness_bundle,
            "readiness_bundle_digest_sha256",
        )
    )

    status = "launcher_update_authoritative_candidate_supply_verification_after_import_blocked"
    if import_boundary_verified and not supply_packet_ready:
        status = (
            "launcher_update_authoritative_candidate_supply_verification_after_import_"
            "pending_supply_approval"
        )
    if supply_packet_ready and not candidate_verification_ready:
        status = (
            "launcher_update_authoritative_candidate_supply_verification_after_import_"
            "pending_candidate_verification_approval"
        )
    if ready_for_wrapper_removal_executor:
        status = (
            "launcher_update_authoritative_candidate_supply_verification_after_import_"
            "ready_for_wrapper_removal_executor"
        )

    proof = {
        "ok": ready_for_wrapper_removal_executor,
        "surface": AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SURFACE_ID,
        "schema_version": AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "candidate_root": str(resolved_candidate_root),
        "errors": errors,
        "warnings": warnings,
        "import_boundary_digest_valid": import_digest_valid,
        "import_boundary_digest_sha256": import_digest,
        "import_boundary_verified": import_boundary_verified,
        "target_revalidation": target_revalidation,
        "target_revalidation_ready": target_revalidation_ready,
        "candidate_supply_preview": candidate_supply_preview,
        "authoritative_candidate_supply_packet": authoritative_candidate_supply_packet,
        "candidate_supply_statement_matched": supply_statement_matched,
        "candidate_supply_packet_ready": supply_packet_ready,
        "candidate_verification_preview": candidate_verification_preview,
        "candidate_verification_proof": candidate_verification_proof,
        "candidate_verification_statement_matched": candidate_verification_statement_matched,
        "candidate_verification_ready": candidate_verification_ready,
        "role_candidate_path_matches": role_candidate_path_matches,
        "readiness_bundle": readiness_bundle,
        "ready_for_wrapper_removal_executor": ready_for_wrapper_removal_executor,
        "source_write_performed": False,
        "wrapper_removal_performed": False,
        "current_vault_wrappers_removed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_current_vault_wrapper_removal_executor_with_exact_approval"
            if ready_for_wrapper_removal_executor
            else "import_candidates_then_approve_supply_and_candidate_verification"
        ),
        "authority": _authority(
            authoritative_candidate_supply_verification_after_import_built=True,
            authoritative_candidate_supply_verification_after_import_boundary_verified=import_boundary_verified,
            authoritative_candidate_supply_verification_after_import_supply_packet_ready=supply_packet_ready,
            authoritative_candidate_supply_verification_after_import_candidate_verification_ready=candidate_verification_ready,
            authoritative_candidate_supply_verification_after_import_ready_for_wrapper_removal_executor=ready_for_wrapper_removal_executor,
            authoritative_candidate_supply_verification_after_import_source_write_performed=False,
            authoritative_candidate_supply_verification_after_import_settings_write_control_exposed=False,
            authoritative_candidate_supply_verification_after_import_primary_real_exe_replacement_performed=False,
            authoritative_candidate_supply_verification_after_import_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["authoritative_candidate_supply_verification_after_import_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "authoritative_candidate_supply_verification_after_import_digest_sha256",
        )
    )
    return proof


def _current_vault_wrapper_removal_candidate_paths_match(
    supply_packet,
    candidate_proof,
):
    supplied_paths = (supply_packet or {}).get("candidate_paths") or {}
    candidates = (
        (candidate_proof or {}).get("candidates")
        or ((candidate_proof or {}).get("candidate_set") or {}).get("candidates")
        or {}
    )
    role_matches = {}
    for role in [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]:
        supplied_role_paths = {
            str(_Path(path).resolve()).lower()
            for path in _normal_source_candidate_role_paths(supplied_paths, role)
        }
        verified_role_paths = {
            str(
                _Path(
                    descriptor.get("resolved_path")
                    or descriptor.get("path")
                    or ""
                ).resolve()
            ).lower()
            for descriptor in candidates.get(role, []) or []
            if descriptor.get("candidate_verification_passed")
        }
        role_matches[role] = bool(
            supplied_role_paths
            and verified_role_paths
            and bool(supplied_role_paths.intersection(verified_role_paths))
        )
    return role_matches


def _current_vault_wrapper_removal_target_checks(
    *,
    vault,
    restore_targets_by_role,
    required_symbols_by_role,
):
    target_paths = _live_source_restoration_target_paths(
        vault,
        restore_targets_by_role,
    )
    checks = {}
    for role, target_path in target_paths.items():
        descriptor = _normal_source_candidate_verification_descriptor(
            vault=vault,
            role=role,
            path=target_path,
            required_symbols=(required_symbols_by_role or {}).get(role, []),
        )
        wrapper_tokens_present = list(descriptor.get("wrapper_tokens_present") or [])
        checks[role] = {
            "role": role,
            "target_path": str(target_path),
            "exists": bool(descriptor.get("exists")),
            "sha256": str(descriptor.get("sha256") or ""),
            "size_bytes": int(descriptor.get("size_bytes") or 0),
            "ast_parse_ok": bool(descriptor.get("ast_parse_ok")),
            "wrapper_tokens_present": wrapper_tokens_present,
            "wrapper_free": not wrapper_tokens_present,
            "target_verification_passed": bool(
                descriptor.get("candidate_verification_passed")
            ),
            "errors": list(descriptor.get("errors") or []),
        }
    return checks


def required_update_current_vault_wrapper_removal_operator_statement(
    wrapper_removal_plan,
):
    digest = str(
        (wrapper_removal_plan or {}).get("wrapper_removal_plan_digest_sha256")
        or _extension_digest_without(
            wrapper_removal_plan or {},
            "wrapper_removal_plan_digest_sha256",
        )
    )
    return (
        f"{CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(
    vault_root,
    *,
    authoritative_candidate_supply_packet=None,
    candidate_verification_proof=None,
    restore_targets_by_role=None,
    required_symbols_by_role=None,
    allow_current_vault_source_write=False,
    operator_approved_current_vault_wrapper_removal=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    supply_packet = _extension_unwrap_api_data(
        authoritative_candidate_supply_packet
        or build_launcher_update_authoritative_normal_source_candidate_supply_packet(
            vault,
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        ),
        "launcher_update_authoritative_normal_source_candidate_supply_packet",
    )
    supply_packet = _extension_unwrap_api_data(
        supply_packet or {},
        AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SURFACE_ID,
    )
    candidate_proof = _extension_unwrap_api_data(
        candidate_verification_proof or {},
        "launcher_update_normal_source_candidate_verification_proof",
    )
    candidate_proof = _extension_unwrap_api_data(
        candidate_proof or {},
        NORMAL_SOURCE_CANDIDATE_VERIFICATION_SURFACE_ID,
    )

    errors = []
    warnings = []
    if supply_packet.get("warnings"):
        warnings.extend(str(item) for item in supply_packet.get("warnings") or [])
    if candidate_proof.get("warnings"):
        warnings.extend(str(item) for item in candidate_proof.get("warnings") or [])

    if not supply_packet:
        errors.append("authoritative_candidate_supply_packet_required")
    elif supply_packet.get("surface") != AUTHORITATIVE_NORMAL_SOURCE_CANDIDATE_SUPPLY_SURFACE_ID:
        errors.append("authoritative_candidate_supply_packet_surface_mismatch")

    supply_digest = str(
        supply_packet.get("authoritative_normal_source_candidate_supply_digest_sha256")
        or ""
    )
    supply_digest_valid = False
    if supply_packet:
        supply_digest_valid = bool(
            supply_digest
            and supply_digest
            == _extension_digest_without(
                supply_packet,
                "authoritative_normal_source_candidate_supply_digest_sha256",
            )
        )
        if not supply_digest_valid:
            errors.append("authoritative_candidate_supply_packet_digest_mismatch")
        if not (
            supply_packet.get("ok")
            and supply_packet.get("ready_for_candidate_verifier")
        ):
            errors.append("authoritative_candidate_supply_packet_not_ready")

    if not candidate_proof:
        errors.append("candidate_verification_proof_required")
    elif candidate_proof.get("surface") != NORMAL_SOURCE_CANDIDATE_VERIFICATION_SURFACE_ID:
        errors.append("candidate_verification_proof_surface_mismatch")
    elif not (
        candidate_proof.get("ok")
        and candidate_proof.get("source_restoration_candidate_verification_ready")
    ):
        errors.append("candidate_verification_proof_not_ready")

    candidate_digest = str(
        candidate_proof.get("normal_source_candidate_verification_digest_sha256")
        or ""
    )
    candidate_digest_valid = False
    if candidate_proof:
        candidate_digest_valid = bool(
            candidate_digest
            and candidate_digest
            == _extension_digest_without(
                candidate_proof,
                "normal_source_candidate_verification_digest_sha256",
            )
        )
        if not candidate_digest_valid:
            errors.append("candidate_verification_proof_digest_mismatch")

    role_candidate_path_matches = _current_vault_wrapper_removal_candidate_paths_match(
        supply_packet,
        candidate_proof,
    )
    if supply_packet and candidate_proof:
        for role, matched in role_candidate_path_matches.items():
            if not matched:
                errors.append(f"{role}_candidate_not_linked_to_supply_packet")

    restore_plan = {
        "schema_version": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SCHEMA_VERSION,
        "surface": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SURFACE_ID,
        "restore_root": str(vault),
        "plan_ready": False,
        "errors": list(errors),
        "restore_plan_digest_sha256": "",
    }
    if (
        supply_digest_valid
        and candidate_digest_valid
        and supply_packet.get("ok")
        and candidate_proof.get("ok")
        and all(role_candidate_path_matches.values())
    ):
        restore_plan = _normal_source_candidate_restore_plan(
            vault=vault,
            candidate_verification_proof=candidate_proof,
            restore_root=vault,
            restore_targets_by_role=restore_targets_by_role,
            required_symbols_by_role=required_symbols,
        )
        errors.extend(restore_plan.get("errors") or [])

    post_write_source_checks_before = _current_vault_wrapper_removal_target_checks(
        vault=vault,
        restore_targets_by_role=restore_targets_by_role,
        required_symbols_by_role=required_symbols,
    )
    wrapper_removal_plan = {
        "schema_version": CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_BOUNDARY_SCHEMA_VERSION,
        "surface": CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_BOUNDARY_SURFACE_ID,
        "vault_root": str(vault),
        "authoritative_candidate_supply_digest_sha256": supply_digest,
        "candidate_verification_digest_sha256": candidate_digest,
        "supply_packet_ready": bool(
            supply_packet.get("ok") and supply_packet.get("ready_for_candidate_verifier")
        ),
        "candidate_verification_ready": bool(
            candidate_proof.get("ok")
            and candidate_proof.get("source_restoration_candidate_verification_ready")
        ),
        "role_candidate_path_matches": role_candidate_path_matches,
        "restore_plan_digest_sha256": restore_plan.get(
            "restore_plan_digest_sha256",
            "",
        ),
        "restore_plan_ready": bool(restore_plan.get("plan_ready")),
        "restore_targets_by_role": _normal_source_candidate_restore_targets(
            vault,
            restore_targets_by_role,
        ),
        "pre_write_source_checks": post_write_source_checks_before,
        "source_write_allowed_only_with_explicit_flag": True,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
        "forbidden_behaviors": [
            "decompile_bytecode",
            "execute_candidate_source",
            "launch_installer",
            "launch_helper",
            "replace_primary_exe",
            "mutate_startup",
            "publish_github_release",
        ],
    }
    wrapper_removal_plan["wrapper_removal_plan_digest_sha256"] = (
        _extension_digest_without(
            wrapper_removal_plan,
            "wrapper_removal_plan_digest_sha256",
        )
    )
    required_statement = (
        required_update_current_vault_wrapper_removal_operator_statement(
            wrapper_removal_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_current_vault_wrapper_removal
        and str(operator_statement) == required_statement
    )
    if not operator_approved_current_vault_wrapper_removal:
        errors.append("operator_current_vault_wrapper_removal_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_current_vault_wrapper_removal_statement_mismatch")

    restore_plan_ready = bool(restore_plan.get("plan_ready"))
    if restore_plan_ready and operator_statement_matched and not allow_current_vault_source_write:
        errors.append("current_vault_source_write_flag_required")

    source_restore_results = {}
    source_write_performed = False
    if restore_plan_ready and operator_statement_matched and allow_current_vault_source_write:
        for role, item in (restore_plan.get("role_plan") or {}).items():
            source_path = _Path(item["candidate"]["resolved_path"])
            target_path = _Path(item["target"]["resolved_target_path"])
            before_hash = ""
            before_size = 0
            if target_path.exists() and target_path.is_file():
                before_payload = target_path.read_bytes()
                before_hash = _wrapper_hashlib.sha256(before_payload).hexdigest()
                before_size = len(before_payload)
            payload = source_path.read_bytes()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(payload)
            after_payload = target_path.read_bytes()
            after_hash = _wrapper_hashlib.sha256(after_payload).hexdigest()
            write_verified = after_hash == item["candidate"]["sha256"]
            if not write_verified:
                errors.append(f"{role}_current_vault_write_hash_mismatch")
            source_restore_results[role] = {
                "role": role,
                "source_path": str(source_path),
                "target_path": str(target_path),
                "before_sha256": before_hash,
                "before_size_bytes": before_size,
                "after_sha256": after_hash,
                "after_size_bytes": len(after_payload),
                "write_performed": True,
                "write_verified": write_verified,
            }
        source_write_performed = bool(
            source_restore_results
            and all(item.get("write_verified") for item in source_restore_results.values())
        )

    post_write_source_checks = _current_vault_wrapper_removal_target_checks(
        vault=vault,
        restore_targets_by_role=restore_targets_by_role,
        required_symbols_by_role=required_symbols,
    )
    wrappers_removed = bool(
        source_write_performed
        and post_write_source_checks
        and all(
            item.get("target_verification_passed") and item.get("wrapper_free")
            for item in post_write_source_checks.values()
        )
    )
    if source_write_performed and not wrappers_removed:
        errors.append("current_vault_wrapper_removal_post_write_verification_failed")

    status = "launcher_update_current_vault_wrapper_removal_executor_blocked"
    if restore_plan_ready and not operator_statement_matched:
        status = "launcher_update_current_vault_wrapper_removal_executor_pending_approval"
    if restore_plan_ready and operator_statement_matched and not allow_current_vault_source_write:
        status = "launcher_update_current_vault_wrapper_removal_executor_write_flag_required"
    if wrappers_removed:
        status = "launcher_update_current_vault_wrapper_removal_executor_restored"

    proof = {
        "ok": wrappers_removed,
        "surface": CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_BOUNDARY_SURFACE_ID,
        "schema_version": CURRENT_VAULT_WRAPPER_REMOVAL_EXECUTOR_BOUNDARY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "authoritative_candidate_supply_digest_valid": supply_digest_valid,
        "authoritative_candidate_supply_digest_sha256": supply_digest,
        "candidate_verification_proof_digest_valid": candidate_digest_valid,
        "candidate_verification_digest_sha256": candidate_digest,
        "role_candidate_path_matches": role_candidate_path_matches,
        "restore_plan": restore_plan,
        "wrapper_removal_plan": wrapper_removal_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "restore_plan_ready": restore_plan_ready,
        "current_vault_source_write_enabled": bool(allow_current_vault_source_write),
        "source_write_performed": source_write_performed,
        "source_restore_results": source_restore_results,
        "post_write_source_checks": post_write_source_checks,
        "current_vault_wrappers_removed": wrappers_removed,
        "wrapper_removal_performed": wrappers_removed,
        "source_file_replacement_performed": source_write_performed,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_post_wrapper_removal_regression_and_source_closeout"
            if wrappers_removed
            else "supply_verified_candidates_and_exact_wrapper_removal_approval"
        ),
        "authority": _authority(
            current_vault_wrapper_removal_executor_boundary_built=True,
            current_vault_wrapper_removal_executor_plan_ready=restore_plan_ready,
            current_vault_wrapper_removal_executor_statement_matched=(
                operator_statement_matched
            ),
            current_vault_wrapper_removal_executor_source_write_performed=(
                source_write_performed
            ),
            current_vault_wrapper_removal_executor_wrappers_removed=wrappers_removed,
            current_vault_wrapper_removal_executor_settings_write_control_exposed=False,
            current_vault_wrapper_removal_executor_primary_real_exe_replacement_performed=False,
            current_vault_wrapper_removal_executor_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["current_vault_wrapper_removal_executor_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "current_vault_wrapper_removal_executor_digest_sha256",
        )
    )
    return proof


def required_update_current_vault_wrapper_removal_after_import_operator_statement(
    wrapper_removal_after_import_execution_plan,
):
    digest = str(
        (
            wrapper_removal_after_import_execution_plan
            or {}
        ).get("wrapper_removal_after_import_execution_plan_digest_sha256")
        or _extension_digest_without(
            wrapper_removal_after_import_execution_plan or {},
            "wrapper_removal_after_import_execution_plan_digest_sha256",
        )
    )
    return (
        f"{CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def _current_vault_after_import_executor_blocking_errors(executor_proof):
    ignored = {
        "operator_current_vault_wrapper_removal_approval_required",
        "current_vault_source_write_flag_required",
    }
    return [
        str(item)
        for item in (executor_proof or {}).get("errors") or []
        if str(item) not in ignored
    ]


def build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(
    vault_root,
    *,
    authoritative_candidate_supply_verification_after_import_proof=None,
    restore_targets_by_role=None,
    required_symbols_by_role=None,
    allow_current_vault_source_write=False,
    operator_approved_current_vault_wrapper_removal_after_import=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    errors = []
    warnings = []

    after_import_proof = _extension_unwrap_api_data(
        authoritative_candidate_supply_verification_after_import_proof or {},
        "launcher_update_authoritative_candidate_supply_verification_after_import_proof",
    )
    after_import_proof = _extension_unwrap_api_data(
        after_import_proof or {},
        AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SURFACE_ID,
    )
    if not isinstance(after_import_proof, dict):
        after_import_proof = {}

    if after_import_proof.get("warnings"):
        warnings.extend(str(item) for item in after_import_proof.get("warnings") or [])
    if not after_import_proof:
        errors.append("authoritative_candidate_supply_verification_after_import_proof_required")
    elif (
        after_import_proof.get("surface")
        != AUTHORITATIVE_CANDIDATE_SUPPLY_VERIFICATION_AFTER_IMPORT_SURFACE_ID
    ):
        errors.append(
            "authoritative_candidate_supply_verification_after_import_surface_mismatch"
        )

    after_import_digest = str(
        after_import_proof.get(
            "authoritative_candidate_supply_verification_after_import_digest_sha256"
        )
        or ""
    )
    after_import_digest_valid = False
    if after_import_proof:
        after_import_digest_valid = bool(
            after_import_digest
            and after_import_digest
            == _extension_digest_without(
                after_import_proof,
                "authoritative_candidate_supply_verification_after_import_digest_sha256",
            )
        )
        if not after_import_digest_valid:
            errors.append(
                "authoritative_candidate_supply_verification_after_import_digest_mismatch"
            )
        if not (
            after_import_proof.get("ok")
            and after_import_proof.get("ready_for_wrapper_removal_executor")
        ):
            errors.append(
                "authoritative_candidate_supply_verification_after_import_not_ready"
            )

    after_import_ready = bool(
        after_import_digest_valid
        and after_import_proof.get("ok")
        and after_import_proof.get("ready_for_wrapper_removal_executor")
    )
    supply_packet = (
        after_import_proof.get("authoritative_candidate_supply_packet") or {}
    )
    candidate_proof = after_import_proof.get("candidate_verification_proof") or {}

    executor_preview = {}
    executor_blocking_errors = []
    executor_plan_ready = False
    if after_import_ready:
        executor_preview = build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(
            vault,
            authoritative_candidate_supply_packet=supply_packet,
            candidate_verification_proof=candidate_proof,
            restore_targets_by_role=restore_targets_by_role,
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
        if executor_preview.get("warnings"):
            warnings.extend(str(item) for item in executor_preview.get("warnings") or [])
        executor_blocking_errors = _current_vault_after_import_executor_blocking_errors(
            executor_preview
        )
        if executor_blocking_errors:
            errors.extend(executor_blocking_errors)
        executor_plan_ready = bool(
            executor_preview.get("restore_plan_ready")
            and not executor_blocking_errors
        )
        if not executor_plan_ready:
            errors.append("current_vault_wrapper_removal_executor_plan_not_ready")

    executor_preview_digest = str(
        executor_preview.get("current_vault_wrapper_removal_executor_digest_sha256")
        or ""
    )
    wrapper_removal_plan = executor_preview.get("wrapper_removal_plan") or {}
    after_import_execution_plan = {
        "schema_version": CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_SCHEMA_VERSION,
        "surface": CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_SURFACE_ID,
        "vault_root": str(vault),
        "source_after_import_digest_sha256": after_import_digest,
        "after_import_digest_valid": after_import_digest_valid,
        "after_import_ready_for_wrapper_removal_executor": after_import_ready,
        "wrapper_removal_executor_preview_digest_sha256": executor_preview_digest,
        "wrapper_removal_plan_digest_sha256": wrapper_removal_plan.get(
            "wrapper_removal_plan_digest_sha256",
            "",
        ),
        "restore_plan_digest_sha256": (
            executor_preview.get("restore_plan") or {}
        ).get("restore_plan_digest_sha256", ""),
        "restore_plan_ready": executor_plan_ready,
        "restore_targets_by_role": _normal_source_candidate_restore_targets(
            vault,
            restore_targets_by_role,
        ),
        "requires_existing_wrapper_removal_executor": True,
        "requires_exact_operator_statement": True,
        "requires_explicit_source_write_flag": True,
        "source_write_allowed_only_with_explicit_flag": True,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
        "forbidden_behaviors": [
            "decompile_bytecode",
            "execute_candidate_source",
            "launch_installer",
            "launch_helper",
            "replace_primary_exe",
            "mutate_startup",
            "publish_github_release",
        ],
    }
    after_import_execution_plan[
        "wrapper_removal_after_import_execution_plan_digest_sha256"
    ] = _extension_digest_without(
        after_import_execution_plan,
        "wrapper_removal_after_import_execution_plan_digest_sha256",
    )
    required_statement = (
        required_update_current_vault_wrapper_removal_after_import_operator_statement(
            after_import_execution_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_current_vault_wrapper_removal_after_import
        and str(operator_statement) == required_statement
    )
    if executor_plan_ready:
        if not operator_approved_current_vault_wrapper_removal_after_import:
            errors.append(
                "operator_current_vault_wrapper_removal_after_import_approval_required"
            )
        elif not operator_statement_matched:
            errors.append(
                "operator_current_vault_wrapper_removal_after_import_statement_mismatch"
            )
        elif not allow_current_vault_source_write:
            errors.append("current_vault_source_write_flag_required")

    executor_execution_proof = {}
    if executor_plan_ready and operator_statement_matched and allow_current_vault_source_write:
        executor_execution_proof = build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(
            vault,
            authoritative_candidate_supply_packet=supply_packet,
            candidate_verification_proof=candidate_proof,
            restore_targets_by_role=restore_targets_by_role,
            required_symbols_by_role=required_symbols,
            allow_current_vault_source_write=True,
            operator_approved_current_vault_wrapper_removal=True,
            operator_statement=str(executor_preview.get("required_operator_statement") or ""),
            generated_at=timestamp,
        )
        if executor_execution_proof.get("warnings"):
            warnings.extend(
                str(item)
                for item in executor_execution_proof.get("warnings") or []
            )
        execution_blocking_errors = _current_vault_after_import_executor_blocking_errors(
            executor_execution_proof
        )
        if execution_blocking_errors:
            errors.extend(execution_blocking_errors)

    source_write_performed = bool(
        executor_execution_proof.get("source_write_performed")
    )
    wrappers_removed = bool(
        executor_execution_proof.get("current_vault_wrappers_removed")
    )
    status = "launcher_update_current_vault_wrapper_removal_after_import_execution_blocked"
    if executor_plan_ready and not operator_statement_matched:
        status = (
            "launcher_update_current_vault_wrapper_removal_after_import_execution_"
            "pending_approval"
        )
    if executor_plan_ready and operator_statement_matched and not allow_current_vault_source_write:
        status = (
            "launcher_update_current_vault_wrapper_removal_after_import_execution_"
            "write_flag_required"
        )
    if wrappers_removed:
        status = (
            "launcher_update_current_vault_wrapper_removal_after_import_execution_"
            "restored"
        )

    proof = {
        "ok": wrappers_removed,
        "surface": CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_SURFACE_ID,
        "schema_version": CURRENT_VAULT_WRAPPER_REMOVAL_AFTER_IMPORT_EXECUTION_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "after_import_digest_valid": after_import_digest_valid,
        "after_import_digest_sha256": after_import_digest,
        "after_import_ready_for_wrapper_removal_executor": after_import_ready,
        "wrapper_removal_executor_preview": executor_preview,
        "wrapper_removal_executor_preview_digest_sha256": executor_preview_digest,
        "wrapper_removal_after_import_execution_plan": after_import_execution_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "restore_plan_ready": executor_plan_ready,
        "current_vault_source_write_enabled": bool(allow_current_vault_source_write),
        "wrapper_removal_executor_execution_proof": executor_execution_proof,
        "source_write_performed": source_write_performed,
        "wrapper_removal_performed": wrappers_removed,
        "current_vault_wrappers_removed": wrappers_removed,
        "source_file_replacement_performed": source_write_performed,
        "post_write_source_checks": executor_execution_proof.get(
            "post_write_source_checks",
            executor_preview.get("post_write_source_checks", {}),
        ),
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_post_wrapper_removal_regression_and_source_closeout"
            if wrappers_removed
            else "provide_ready_after_import_evidence_and_exact_wrapper_removal_after_import_approval"
        ),
        "authority": _authority(
            current_vault_wrapper_removal_after_import_execution_built=True,
            current_vault_wrapper_removal_after_import_execution_after_import_verified=after_import_ready,
            current_vault_wrapper_removal_after_import_execution_plan_ready=executor_plan_ready,
            current_vault_wrapper_removal_after_import_execution_statement_matched=operator_statement_matched,
            current_vault_wrapper_removal_after_import_execution_source_write_performed=source_write_performed,
            current_vault_wrapper_removal_after_import_execution_wrappers_removed=wrappers_removed,
            current_vault_wrapper_removal_after_import_execution_settings_write_control_exposed=False,
            current_vault_wrapper_removal_after_import_execution_primary_real_exe_replacement_performed=False,
            current_vault_wrapper_removal_after_import_execution_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["current_vault_wrapper_removal_after_import_execution_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "current_vault_wrapper_removal_after_import_execution_digest_sha256",
        )
    )
    return proof


def required_update_current_vault_wrapper_removal_from_materialization_import_operator_statement(
    wrapper_removal_from_materialization_import_execution_plan,
):
    digest = str(
        (
            wrapper_removal_from_materialization_import_execution_plan
            or {}
        ).get(
            "wrapper_removal_from_materialization_import_execution_plan_digest_sha256"
        )
        or _extension_digest_without(
            wrapper_removal_from_materialization_import_execution_plan or {},
            "wrapper_removal_from_materialization_import_execution_plan_digest_sha256",
        )
    )
    return (
        f"{CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def _current_vault_from_materialization_import_executor_blocking_errors(
    after_import_execution_proof,
):
    ignored = {
        "operator_current_vault_wrapper_removal_after_import_approval_required",
        "current_vault_source_write_flag_required",
    }
    return [
        str(item)
        for item in (after_import_execution_proof or {}).get("errors") or []
        if str(item) not in ignored
    ]


def build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(
    vault_root,
    *,
    supply_verification_from_materialization_import_proof=None,
    restore_targets_by_role=None,
    required_symbols_by_role=None,
    allow_current_vault_source_write=False,
    operator_approved_current_vault_wrapper_removal_from_materialization_import=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    errors = []
    warnings = []

    source_proof = _extension_unwrap_api_data(
        supply_verification_from_materialization_import_proof or {},
        "launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof",
    )
    source_proof = _extension_unwrap_api_data(
        source_proof or {},
        REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID,
    )
    if not isinstance(source_proof, dict):
        source_proof = {}

    if source_proof.get("warnings"):
        warnings.extend(str(item) for item in source_proof.get("warnings") or [])
    if not source_proof:
        errors.append(
            "real_authoritative_source_candidate_supply_verification_from_materialization_import_proof_required"
        )
    elif (
        source_proof.get("surface")
        != REAL_AUTHORITATIVE_SOURCE_CANDIDATE_SUPPLY_VERIFICATION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID
    ):
        errors.append(
            "real_authoritative_source_candidate_supply_verification_from_materialization_import_surface_mismatch"
        )

    source_digest_key = (
        "real_authoritative_source_candidate_supply_verification_from_materialization_import_digest_sha256"
    )
    source_digest = str(source_proof.get(source_digest_key) or "")
    source_digest_valid = False
    if source_proof:
        source_digest_valid = bool(
            source_digest
            and source_digest
            == _extension_digest_without(source_proof, source_digest_key)
        )
        if not source_digest_valid:
            errors.append(
                "real_authoritative_source_candidate_supply_verification_from_materialization_import_digest_mismatch"
            )
        if not (
            source_proof.get("ok")
            and source_proof.get("ready_for_wrapper_removal_executor")
        ):
            errors.append(
                "real_authoritative_source_candidate_supply_verification_from_materialization_import_not_ready"
            )

    source_ready = bool(
        source_digest_valid
        and source_proof.get("ok")
        and source_proof.get("ready_for_wrapper_removal_executor")
    )
    after_import_verification_proof = (
        source_proof.get("after_import_verification_proof") or {}
    )
    if source_ready and not after_import_verification_proof:
        errors.append(
            "after_import_verification_proof_missing_from_materialization_import"
        )

    after_import_execution_preview = {}
    preview_blocking_errors = []
    executor_plan_ready = False
    if source_ready and after_import_verification_proof:
        after_import_execution_preview = build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(
            vault,
            authoritative_candidate_supply_verification_after_import_proof=after_import_verification_proof,
            restore_targets_by_role=restore_targets_by_role,
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
        if after_import_execution_preview.get("warnings"):
            warnings.extend(
                str(item)
                for item in after_import_execution_preview.get("warnings") or []
            )
        preview_blocking_errors = (
            _current_vault_from_materialization_import_executor_blocking_errors(
                after_import_execution_preview
            )
        )
        if preview_blocking_errors:
            errors.extend(preview_blocking_errors)
        executor_plan_ready = bool(
            after_import_execution_preview.get("restore_plan_ready")
            and not preview_blocking_errors
        )
        if not executor_plan_ready:
            errors.append(
                "current_vault_wrapper_removal_from_materialization_import_executor_plan_not_ready"
            )

    after_import_execution_preview_digest = str(
        after_import_execution_preview.get(
            "current_vault_wrapper_removal_after_import_execution_digest_sha256"
        )
        or ""
    )
    after_import_execution_plan = (
        after_import_execution_preview.get(
            "wrapper_removal_after_import_execution_plan"
        )
        or {}
    )
    from_materialization_import_execution_plan = {
        "schema_version": CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SCHEMA_VERSION,
        "surface": CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SURFACE_ID,
        "vault_root": str(vault),
        "source_supply_verification_from_materialization_import_digest_sha256": source_digest,
        "source_supply_verification_from_materialization_import_digest_valid": source_digest_valid,
        "source_supply_verification_from_materialization_import_ready": source_ready,
        "after_import_verification_digest_sha256": str(
            after_import_verification_proof.get(
                "authoritative_candidate_supply_verification_after_import_digest_sha256"
            )
            or ""
        ),
        "wrapper_removal_after_import_preview_digest_sha256": after_import_execution_preview_digest,
        "wrapper_removal_after_import_execution_plan_digest_sha256": str(
            after_import_execution_plan.get(
                "wrapper_removal_after_import_execution_plan_digest_sha256"
            )
            or ""
        ),
        "restore_plan_digest_sha256": str(
            after_import_execution_plan.get("restore_plan_digest_sha256") or ""
        ),
        "restore_plan_ready": executor_plan_ready,
        "restore_targets_by_role": _normal_source_candidate_restore_targets(
            vault,
            restore_targets_by_role,
        ),
        "requires_supply_verification_from_materialization_import_proof": True,
        "requires_existing_after_import_wrapper_removal_executor": True,
        "requires_exact_operator_statement": True,
        "requires_explicit_source_write_flag": True,
        "source_write_allowed_only_with_explicit_flag": True,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
        "forbidden_behaviors": [
            "decompile_bytecode",
            "execute_candidate_source",
            "launch_installer",
            "launch_helper",
            "replace_primary_exe",
            "mutate_startup",
            "publish_github_release",
        ],
    }
    from_materialization_import_execution_plan[
        "wrapper_removal_from_materialization_import_execution_plan_digest_sha256"
    ] = _extension_digest_without(
        from_materialization_import_execution_plan,
        "wrapper_removal_from_materialization_import_execution_plan_digest_sha256",
    )
    required_statement = (
        required_update_current_vault_wrapper_removal_from_materialization_import_operator_statement(
            from_materialization_import_execution_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_current_vault_wrapper_removal_from_materialization_import
        and str(operator_statement) == required_statement
    )
    if executor_plan_ready:
        if not operator_approved_current_vault_wrapper_removal_from_materialization_import:
            errors.append(
                "operator_current_vault_wrapper_removal_from_materialization_import_approval_required"
            )
        elif not operator_statement_matched:
            errors.append(
                "operator_current_vault_wrapper_removal_from_materialization_import_statement_mismatch"
            )
        elif not allow_current_vault_source_write:
            errors.append("current_vault_source_write_flag_required")

    after_import_execution_proof = {}
    if (
        executor_plan_ready
        and operator_statement_matched
        and allow_current_vault_source_write
    ):
        after_import_execution_proof = build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(
            vault,
            authoritative_candidate_supply_verification_after_import_proof=after_import_verification_proof,
            restore_targets_by_role=restore_targets_by_role,
            required_symbols_by_role=required_symbols,
            allow_current_vault_source_write=True,
            operator_approved_current_vault_wrapper_removal_after_import=True,
            operator_statement=str(
                after_import_execution_preview.get("required_operator_statement")
                or ""
            ),
            generated_at=timestamp,
        )
        if after_import_execution_proof.get("warnings"):
            warnings.extend(
                str(item)
                for item in after_import_execution_proof.get("warnings") or []
            )
        execution_blocking_errors = (
            _current_vault_from_materialization_import_executor_blocking_errors(
                after_import_execution_proof
            )
        )
        if execution_blocking_errors:
            errors.extend(execution_blocking_errors)

    source_write_performed = bool(
        after_import_execution_proof.get("source_write_performed")
    )
    wrappers_removed = bool(
        after_import_execution_proof.get("current_vault_wrappers_removed")
    )
    status = (
        "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_blocked"
    )
    if executor_plan_ready and not operator_statement_matched:
        status = (
            "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_"
            "pending_approval"
        )
    if (
        executor_plan_ready
        and operator_statement_matched
        and not allow_current_vault_source_write
    ):
        status = (
            "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_"
            "write_flag_required"
        )
    if wrappers_removed:
        status = (
            "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_"
            "restored"
        )

    proof = {
        "ok": wrappers_removed,
        "surface": CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SURFACE_ID,
        "schema_version": CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "supply_verification_from_materialization_import_digest_valid": source_digest_valid,
        "supply_verification_from_materialization_import_digest_sha256": source_digest,
        "supply_verification_from_materialization_import_ready": source_ready,
        "after_import_verification_digest_sha256": from_materialization_import_execution_plan[
            "after_import_verification_digest_sha256"
        ],
        "wrapper_removal_after_import_execution_preview": after_import_execution_preview,
        "wrapper_removal_after_import_execution_preview_digest_sha256": after_import_execution_preview_digest,
        "wrapper_removal_from_materialization_import_execution_plan_ready": executor_plan_ready,
        "wrapper_removal_from_materialization_import_execution_plan": from_materialization_import_execution_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "restore_plan_ready": executor_plan_ready,
        "current_vault_source_write_enabled": bool(
            allow_current_vault_source_write
        ),
        "wrapper_removal_after_import_execution_proof": after_import_execution_proof,
        "source_write_performed": source_write_performed,
        "wrapper_removal_performed": wrappers_removed,
        "current_vault_wrappers_removed": wrappers_removed,
        "source_file_replacement_performed": source_write_performed,
        "post_write_source_checks": after_import_execution_proof.get(
            "post_write_source_checks",
            after_import_execution_preview.get("post_write_source_checks", {}),
        ),
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_post_wrapper_removal_regression_and_source_closeout"
            if wrappers_removed
            else "provide_ready_supply_verification_from_materialization_import_and_exact_wrapper_removal_approval"
        ),
        "authority": _authority(
            current_vault_wrapper_removal_from_materialization_import_execution_built=True,
            current_vault_wrapper_removal_from_materialization_import_execution_supply_verification_verified=source_ready,
            current_vault_wrapper_removal_from_materialization_import_execution_plan_ready=executor_plan_ready,
            current_vault_wrapper_removal_from_materialization_import_execution_statement_matched=operator_statement_matched,
            current_vault_wrapper_removal_from_materialization_import_execution_source_write_performed=source_write_performed,
            current_vault_wrapper_removal_from_materialization_import_execution_wrappers_removed=wrappers_removed,
            current_vault_wrapper_removal_from_materialization_import_execution_settings_write_control_exposed=False,
            current_vault_wrapper_removal_from_materialization_import_execution_primary_real_exe_replacement_performed=False,
            current_vault_wrapper_removal_from_materialization_import_execution_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof[
        "current_vault_wrapper_removal_from_materialization_import_execution_digest_sha256"
    ] = _extension_digest_without(
        proof,
        "current_vault_wrapper_removal_from_materialization_import_execution_digest_sha256",
    )
    return proof


def required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
    post_wrapper_removal_regression_plan,
):
    digest = str(
        (post_wrapper_removal_regression_plan or {}).get(
            "post_wrapper_removal_regression_from_materialization_import_plan_digest_sha256"
        )
        or _extension_digest_without(
            post_wrapper_removal_regression_plan or {},
            "post_wrapper_removal_regression_from_materialization_import_plan_digest_sha256",
        )
    )
    return (
        f"{POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
    vault_root,
    *,
    wrapper_removal_from_materialization_import_execution_proof=None,
    regression_evidence=None,
    operator_approved_post_wrapper_removal_regression=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    wrapper_proof = _extension_unwrap_api_data(
        wrapper_removal_from_materialization_import_execution_proof or {},
        "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof",
    )
    wrapper_proof = _extension_unwrap_api_data(
        wrapper_proof or {},
        CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SURFACE_ID,
    )
    if not isinstance(wrapper_proof, dict):
        wrapper_proof = {}

    if wrapper_proof.get("warnings"):
        warnings.extend(str(item) for item in wrapper_proof.get("warnings") or [])
    if not wrapper_proof:
        errors.append(
            "current_vault_wrapper_removal_from_materialization_import_execution_proof_required"
        )
    elif (
        wrapper_proof.get("surface")
        != CURRENT_VAULT_WRAPPER_REMOVAL_FROM_MATERIALIZATION_IMPORT_EXECUTION_SURFACE_ID
    ):
        errors.append(
            "current_vault_wrapper_removal_from_materialization_import_execution_surface_mismatch"
        )

    wrapper_digest_key = (
        "current_vault_wrapper_removal_from_materialization_import_execution_digest_sha256"
    )
    wrapper_digest = str(wrapper_proof.get(wrapper_digest_key) or "")
    wrapper_digest_valid = False
    if wrapper_proof:
        wrapper_digest_valid = bool(
            wrapper_digest
            and wrapper_digest
            == _extension_digest_without(wrapper_proof, wrapper_digest_key)
        )
        if not wrapper_digest_valid:
            errors.append(
                "current_vault_wrapper_removal_from_materialization_import_execution_digest_mismatch"
            )
        if not (
            wrapper_proof.get("ok")
            and wrapper_proof.get("source_write_performed")
            and wrapper_proof.get("wrapper_removal_performed")
            and wrapper_proof.get("current_vault_wrappers_removed")
        ):
            errors.append(
                "current_vault_wrapper_removal_from_materialization_import_execution_not_restored"
            )

    wrapper_removal_verified = bool(
        wrapper_digest_valid
        and wrapper_proof.get("ok")
        and wrapper_proof.get("source_write_performed")
        and wrapper_proof.get("wrapper_removal_performed")
        and wrapper_proof.get("current_vault_wrappers_removed")
    )

    command_plan = (
        _post_wrapper_removal_regression_from_materialization_import_command_plan()
    )
    regression_plan = {
        "schema_version": POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SCHEMA_VERSION,
        "surface": POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID,
        "vault_root": str(vault),
        "wrapper_removal_from_materialization_import_execution_digest_sha256": wrapper_digest,
        "wrapper_removal_from_materialization_import_execution_digest_valid": (
            wrapper_digest_valid
        ),
        "wrapper_removal_from_materialization_import_verified": (
            wrapper_removal_verified
        ),
        "requires_wrapper_removal_from_materialization_import_execution_proof": True,
        "requires_wrapper_removal_performed": True,
        "requires_supplied_regression_evidence": True,
        "requires_exact_operator_statement": True,
        "regression_commands_executed_by_chaseos": False,
        "settings_write_control_exposed": False,
        "primary_real_exe_replacement_allowed": False,
        "regression_command_plan": command_plan,
        "forbidden_behaviors": [
            "run_regression_commands_from_settings",
            "write_source",
            "decompile_bytecode",
            "execute_candidate_source",
            "launch_installer",
            "launch_helper",
            "replace_primary_exe",
            "mutate_startup",
            "publish_github_release",
        ],
    }
    regression_plan[
        "post_wrapper_removal_regression_from_materialization_import_plan_digest_sha256"
    ] = _extension_digest_without(
        regression_plan,
        "post_wrapper_removal_regression_from_materialization_import_plan_digest_sha256",
    )
    required_statement = (
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
            regression_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_post_wrapper_removal_regression
        and str(operator_statement) == required_statement
    )

    regression_descriptor = (
        _post_wrapper_removal_regression_from_materialization_import_evidence_descriptor(
            regression_evidence,
            command_plan,
        )
    )
    regression_evidence_required = bool(wrapper_removal_verified)
    regression_evidence_supplied = bool(regression_evidence)
    regression_evidence_verified = bool(
        regression_descriptor.get("regression_evidence_verified")
    )
    if regression_evidence_required and not regression_evidence_verified:
        errors.append(
            "post_wrapper_removal_regression_from_materialization_import_regression_evidence_required"
        )
    if regression_evidence_required and regression_evidence_verified:
        if not operator_approved_post_wrapper_removal_regression:
            errors.append(
                "operator_post_wrapper_removal_regression_from_materialization_import_approval_required"
            )
        elif not operator_statement_matched:
            errors.append(
                "operator_post_wrapper_removal_regression_from_materialization_import_statement_mismatch"
            )

    status = (
        "launcher_update_post_wrapper_removal_regression_from_materialization_import_blocked"
    )
    if wrapper_removal_verified and not regression_evidence_verified:
        status = (
            "launcher_update_post_wrapper_removal_regression_from_materialization_import_"
            "regression_evidence_required"
        )
    if wrapper_removal_verified and regression_evidence_verified and not operator_statement_matched:
        status = (
            "launcher_update_post_wrapper_removal_regression_from_materialization_import_"
            "pending_approval"
        )
    regression_verified = bool(
        wrapper_removal_verified
        and regression_evidence_verified
        and operator_statement_matched
    )
    if regression_verified:
        status = (
            "launcher_update_post_wrapper_removal_regression_from_materialization_import_"
            "verified"
        )

    proof = {
        "ok": regression_verified,
        "surface": POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID,
        "schema_version": POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "wrapper_removal_from_materialization_import_execution_digest_sha256": wrapper_digest,
        "wrapper_removal_from_materialization_import_execution_digest_valid": (
            wrapper_digest_valid
        ),
        "wrapper_removal_from_materialization_import_verified": (
            wrapper_removal_verified
        ),
        "wrapper_removal_from_materialization_import_execution_status": (
            wrapper_proof.get("status", "")
        ),
        "post_write_source_checks": wrapper_proof.get("post_write_source_checks", {}),
        "regression_command_plan_ready": bool(command_plan),
        "regression_command_plan": command_plan,
        "post_wrapper_removal_regression_from_materialization_import_plan": (
            regression_plan
        ),
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "regression_evidence_required": regression_evidence_required,
        "regression_evidence_supplied": regression_evidence_supplied,
        "regression_evidence_verified": regression_evidence_verified,
        "regression_evidence": regression_descriptor,
        "wrapper_removal_from_materialization_import_execution_proof": wrapper_proof,
        "source_write_performed": False,
        "source_write_previously_performed": bool(
            wrapper_proof.get("source_write_performed")
        ),
        "wrapper_removal_performed": False,
        "wrapper_removal_previously_performed": bool(
            wrapper_proof.get("wrapper_removal_performed")
        ),
        "current_vault_wrappers_removed": wrapper_removal_verified,
        "source_file_replacement_performed": False,
        "source_file_replacement_previously_performed": bool(
            wrapper_proof.get("source_file_replacement_performed")
        ),
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "regression_commands_executed_by_chaseos": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_current_vault_source_restoration_closeout"
            if regression_verified
            else (
                "supply_post_wrapper_removal_regression_evidence"
                if wrapper_removal_verified
                else "perform_wrapper_removal_from_materialization_import_first"
            )
        ),
        "authority": _authority(
            post_wrapper_removal_regression_from_materialization_import_built=True,
            post_wrapper_removal_regression_from_materialization_import_wrapper_removal_verified=wrapper_removal_verified,
            post_wrapper_removal_regression_from_materialization_import_evidence_verified=regression_evidence_verified,
            post_wrapper_removal_regression_from_materialization_import_statement_matched=operator_statement_matched,
            post_wrapper_removal_regression_from_materialization_import_commands_executed=False,
            post_wrapper_removal_regression_from_materialization_import_source_write_performed=False,
            post_wrapper_removal_regression_from_materialization_import_settings_write_control_exposed=False,
            post_wrapper_removal_regression_from_materialization_import_primary_real_exe_replacement_performed=False,
            post_wrapper_removal_regression_from_materialization_import_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof[
        "post_wrapper_removal_regression_from_materialization_import_digest_sha256"
    ] = _extension_digest_without(
        proof,
        "post_wrapper_removal_regression_from_materialization_import_digest_sha256",
    )
    return proof


def build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
    vault_root,
    *,
    post_wrapper_removal_regression_from_materialization_import_proof=None,
    source_recovery_cleanup_proof=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    if post_wrapper_removal_regression_from_materialization_import_proof is None:
        post_wrapper_removal_regression_from_materialization_import_proof = (
            build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
                vault,
                generated_at=timestamp,
            )
        )
        errors.append(
            "post_wrapper_removal_regression_from_materialization_import_proof_required"
        )

    regression_proof = _extension_unwrap_api_data(
        post_wrapper_removal_regression_from_materialization_import_proof,
        "launcher_update_post_wrapper_removal_regression_from_materialization_import_proof",
    )
    regression_proof = _extension_unwrap_api_data(
        regression_proof or {},
        POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID,
    )
    if not isinstance(regression_proof, dict):
        regression_proof = {}

    if regression_proof.get("warnings"):
        warnings.extend(str(item) for item in regression_proof.get("warnings") or [])
    if not regression_proof:
        errors.append(
            "post_wrapper_removal_regression_from_materialization_import_proof_malformed"
        )
    elif (
        regression_proof.get("surface")
        != POST_WRAPPER_REMOVAL_REGRESSION_FROM_MATERIALIZATION_IMPORT_SURFACE_ID
    ):
        errors.append(
            "post_wrapper_removal_regression_from_materialization_import_surface_mismatch"
        )

    regression_digest_key = (
        "post_wrapper_removal_regression_from_materialization_import_digest_sha256"
    )
    regression_digest = str(regression_proof.get(regression_digest_key) or "")
    regression_digest_matched = bool(
        regression_digest
        and regression_digest
        == _extension_digest_without(regression_proof, regression_digest_key)
    )
    if regression_proof and not regression_digest_matched:
        errors.append(
            "post_wrapper_removal_regression_from_materialization_import_digest_mismatch"
        )

    post_wrapper_regression_verified = bool(
        regression_digest_matched
        and regression_proof.get("ok")
        and regression_proof.get(
            "wrapper_removal_from_materialization_import_verified"
        )
        and regression_proof.get("regression_evidence_verified")
        and regression_proof.get("operator_statement_matched")
        and regression_proof.get("current_vault_wrappers_removed")
        and not regression_proof.get("regression_commands_executed_by_chaseos")
    )
    if regression_proof and not post_wrapper_regression_verified:
        errors.append(
            "post_wrapper_removal_regression_from_materialization_import_not_verified"
        )
    if regression_proof.get("regression_commands_executed_by_chaseos"):
        errors.append(
            "post_wrapper_removal_regression_from_materialization_import_unexpected_command_execution"
        )

    if source_recovery_cleanup_proof is None:
        source_recovery_cleanup_proof = build_launcher_update_source_recovery_cleanup_proof(
            vault,
            generated_at=timestamp,
        )
    cleanup_proof = _extension_unwrap_api_data(
        source_recovery_cleanup_proof,
        "launcher_update_source_recovery_cleanup_proof",
    )
    cleanup_proof = _extension_unwrap_api_data(
        cleanup_proof or {},
        SOURCE_RECOVERY_CLEANUP_SURFACE_ID,
    )
    if not isinstance(cleanup_proof, dict):
        cleanup_proof = {}
    if cleanup_proof.get("warnings"):
        warnings.extend(str(item) for item in cleanup_proof.get("warnings") or [])
    if not cleanup_proof:
        errors.append("source_recovery_cleanup_proof_required")
    elif cleanup_proof.get("surface") != SOURCE_RECOVERY_CLEANUP_SURFACE_ID:
        errors.append("source_recovery_cleanup_surface_mismatch")

    cleanup_digest_key = "source_recovery_cleanup_digest_sha256"
    cleanup_digest = str(cleanup_proof.get(cleanup_digest_key) or "")
    cleanup_digest_matched = bool(
        cleanup_digest
        and cleanup_digest == _extension_digest_without(cleanup_proof, cleanup_digest_key)
    )
    if cleanup_proof and not cleanup_digest_matched:
        errors.append("source_recovery_cleanup_digest_mismatch")

    source_cleanup_ready = bool(
        cleanup_digest_matched
        and cleanup_proof.get("ok")
        and cleanup_proof.get("source_recovery_cleanup_ready")
        and cleanup_proof.get("normal_source_restored")
        and not cleanup_proof.get("final_auto_update_closeout_blocked")
    )
    launcher_wrapper_active = bool(
        (cleanup_proof.get("launcher_update_check_source") or {}).get("wrapper_active")
    )
    api_wrapper_active = bool(
        (cleanup_proof.get("studio_shell_api_source") or {}).get("wrapper_active")
    )
    current_vault_wrappers_removed = bool(
        post_wrapper_regression_verified
        and source_cleanup_ready
        and regression_proof.get("current_vault_wrappers_removed")
        and not launcher_wrapper_active
        and not api_wrapper_active
    )
    if cleanup_proof and not source_cleanup_ready:
        errors.append("source_recovery_cleanup_not_ready")
    if launcher_wrapper_active or api_wrapper_active:
        errors.append("current_vault_source_wrappers_still_active")

    closeout_ready = bool(
        post_wrapper_regression_verified and current_vault_wrappers_removed
    )
    status = (
        "launcher_update_current_vault_source_closeout_from_materialization_import_"
        "regression_blocked"
    )
    if post_wrapper_regression_verified and not current_vault_wrappers_removed:
        status = (
            "launcher_update_current_vault_source_closeout_from_materialization_import_"
            "regression_source_cleanup_required"
        )
    if current_vault_wrappers_removed and not post_wrapper_regression_verified:
        status = (
            "launcher_update_current_vault_source_closeout_from_materialization_import_"
            "regression_post_wrapper_regression_required"
        )
    if closeout_ready:
        status = (
            "launcher_update_current_vault_source_closeout_from_materialization_import_"
            "regression_ready"
        )

    proof = {
        "ok": closeout_ready,
        "surface": (
            CURRENT_VAULT_SOURCE_CLOSEOUT_FROM_MATERIALIZATION_IMPORT_REGRESSION_SURFACE_ID
        ),
        "schema_version": (
            CURRENT_VAULT_SOURCE_CLOSEOUT_FROM_MATERIALIZATION_IMPORT_REGRESSION_SCHEMA_VERSION
        ),
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "post_wrapper_removal_regression_from_materialization_import_status": (
            regression_proof.get("status", "")
        ),
        "post_wrapper_removal_regression_from_materialization_import_digest_sha256": (
            regression_digest
        ),
        "post_wrapper_removal_regression_from_materialization_import_digest_matched": (
            regression_digest_matched
        ),
        "post_wrapper_removal_regression_from_materialization_import_verified": (
            post_wrapper_regression_verified
        ),
        "wrapper_removal_from_materialization_import_verified": bool(
            regression_proof.get(
                "wrapper_removal_from_materialization_import_verified"
            )
        ),
        "regression_evidence_verified": bool(
            regression_proof.get("regression_evidence_verified")
        ),
        "source_recovery_cleanup_status": cleanup_proof.get("status", ""),
        "source_recovery_cleanup_digest_sha256": cleanup_digest,
        "source_recovery_cleanup_digest_matched": cleanup_digest_matched,
        "source_recovery_cleanup_ready": source_cleanup_ready,
        "current_vault_wrappers_removed": current_vault_wrappers_removed,
        "launcher_update_check_wrapper_active": launcher_wrapper_active,
        "studio_shell_api_wrapper_active": api_wrapper_active,
        "current_vault_source_closeout_from_materialization_import_regression_ready": closeout_ready,
        "source_restoration_closeout_ready_for_primary_exe_resume": closeout_ready,
        "post_wrapper_removal_regression_from_materialization_import_proof": (
            regression_proof
        ),
        "source_recovery_cleanup_proof": cleanup_proof,
        "source_write_performed": False,
        "source_write_previously_performed": bool(
            regression_proof.get("source_write_previously_performed")
        ),
        "wrapper_removal_performed": False,
        "wrapper_removal_previously_performed": bool(
            regression_proof.get("wrapper_removal_previously_performed")
        ),
        "source_file_replacement_performed": False,
        "source_file_replacement_previously_performed": bool(
            regression_proof.get("source_file_replacement_previously_performed")
        ),
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "regression_commands_executed_by_chaseos": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "settings_write_control_exposed": False,
        "settings_primary_real_exe_enabled": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "resume_primary_exe_closeout_after_materialization_import_source_closeout"
            if closeout_ready
            else (
                "restore_current_vault_normal_source_cleanup"
                if post_wrapper_regression_verified
                else "verify_post_wrapper_removal_regression_from_materialization_import"
            )
        ),
        "authority": _authority(
            current_vault_source_closeout_from_materialization_import_regression_built=True,
            current_vault_source_closeout_from_materialization_import_regression_post_wrapper_regression_verified=post_wrapper_regression_verified,
            current_vault_source_closeout_from_materialization_import_regression_source_cleanup_ready=source_cleanup_ready,
            current_vault_source_closeout_from_materialization_import_regression_closeout_ready=closeout_ready,
            current_vault_source_closeout_from_materialization_import_regression_settings_write_control_exposed=False,
            current_vault_source_closeout_from_materialization_import_regression_primary_real_exe_replacement_performed=False,
            current_vault_source_closeout_from_materialization_import_regression_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof[
        "current_vault_source_closeout_from_materialization_import_regression_digest_sha256"
    ] = _extension_digest_without(
        proof,
        "current_vault_source_closeout_from_materialization_import_regression_digest_sha256",
    )
    return proof


def build_launcher_update_production_primary_closeout_after_source_recovery_proof(
    vault_root,
    *,
    current_vault_source_closeout_from_materialization_import_regression_proof=None,
    production_primary_relaunch_receipt_boundary_proof=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    if current_vault_source_closeout_from_materialization_import_regression_proof is None:
        current_vault_source_closeout_from_materialization_import_regression_proof = (
            build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
                vault,
                generated_at=timestamp,
            )
        )
        errors.append(
            "current_vault_source_closeout_from_materialization_import_regression_proof_required"
        )

    source_proof = _extension_unwrap_api_data(
        current_vault_source_closeout_from_materialization_import_regression_proof,
        "launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof",
    )
    source_proof = _extension_unwrap_api_data(
        source_proof or {},
        CURRENT_VAULT_SOURCE_CLOSEOUT_FROM_MATERIALIZATION_IMPORT_REGRESSION_SURFACE_ID,
    )
    if not isinstance(source_proof, dict):
        source_proof = {}
    if source_proof.get("warnings"):
        warnings.extend(str(item) for item in source_proof.get("warnings") or [])
    if not source_proof:
        errors.append("current_vault_source_closeout_proof_malformed")
    elif (
        source_proof.get("surface")
        != CURRENT_VAULT_SOURCE_CLOSEOUT_FROM_MATERIALIZATION_IMPORT_REGRESSION_SURFACE_ID
    ):
        errors.append("current_vault_source_closeout_surface_mismatch")

    source_digest_key = (
        "current_vault_source_closeout_from_materialization_import_regression_digest_sha256"
    )
    source_digest = str(source_proof.get(source_digest_key) or "")
    source_digest_matched = bool(
        source_digest
        and source_digest == _extension_digest_without(source_proof, source_digest_key)
    )
    if source_proof and not source_digest_matched:
        errors.append("current_vault_source_closeout_digest_mismatch")

    source_closeout_ready = bool(
        source_digest_matched
        and source_proof.get("ok")
        and source_proof.get(
            "current_vault_source_closeout_from_materialization_import_regression_ready"
        )
        and source_proof.get("source_restoration_closeout_ready_for_primary_exe_resume")
        and source_proof.get("current_vault_wrappers_removed")
        and not source_proof.get("source_write_performed")
        and not source_proof.get("wrapper_removal_performed")
        and not source_proof.get("regression_commands_executed_by_chaseos")
    )
    if source_proof and not source_closeout_ready:
        errors.append("current_vault_source_closeout_not_ready")
    for blocked_flag in (
        "source_write_performed",
        "wrapper_removal_performed",
        "regression_commands_executed_by_chaseos",
        "decompiler_execution_performed",
        "candidate_source_execution_performed",
        "settings_write_control_exposed",
        "primary_exe_replacement_performed",
    ):
        if bool(source_proof.get(blocked_flag)):
            errors.append(f"source_closeout_{blocked_flag}_must_be_false")

    if production_primary_relaunch_receipt_boundary_proof is None:
        production_primary_relaunch_receipt_boundary_proof = (
            build_launcher_update_production_primary_relaunch_receipt_boundary_proof(
                vault,
                generated_at=timestamp,
            )
        )
        errors.append("production_primary_relaunch_receipt_boundary_proof_required")

    primary_proof = _extension_unwrap_api_data(
        production_primary_relaunch_receipt_boundary_proof,
        "launcher_update_production_primary_relaunch_receipt_boundary_proof",
    )
    primary_proof = _extension_unwrap_api_data(
        primary_proof or {},
        PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SURFACE_ID,
    )
    if not isinstance(primary_proof, dict):
        primary_proof = {}
    if primary_proof.get("warnings"):
        warnings.extend(str(item) for item in primary_proof.get("warnings") or [])
    if not primary_proof:
        errors.append("production_primary_relaunch_receipt_boundary_proof_malformed")
    elif primary_proof.get("surface") != PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SURFACE_ID:
        errors.append("production_primary_relaunch_receipt_boundary_surface_mismatch")

    primary_boundary = primary_proof.get("primary_relaunch_receipt_boundary") or {}
    if not isinstance(primary_boundary, dict):
        primary_boundary = {}
        errors.append("primary_relaunch_receipt_boundary_malformed")
    primary_digest_key = "primary_relaunch_receipt_boundary_digest_sha256"
    primary_digest = str(
        primary_proof.get(primary_digest_key)
        or primary_boundary.get(primary_digest_key)
        or ""
    )
    primary_digest_matched = bool(
        primary_digest
        and primary_boundary
        and primary_digest
        == _extension_digest_without(primary_boundary, primary_digest_key)
    )
    if primary_proof and not primary_digest_matched:
        errors.append("primary_relaunch_receipt_boundary_digest_mismatch")

    primary_relaunch_ready = bool(
        primary_digest_matched
        and primary_proof.get("ok")
        and primary_proof.get("primary_relaunch_receipt_boundary_ready")
        and primary_proof.get("primary_relaunch_receipt_valid")
        and primary_proof.get("external_helper_primary_relaunch_reported")
        and primary_proof.get("external_helper_primary_replacement_reported")
        and not primary_proof.get("relaunch_performed_by_chaseos")
        and not primary_proof.get("os_process_spawn_performed_by_chaseos")
        and not primary_proof.get("settings_install_control_exposed")
    )
    if primary_proof and not primary_relaunch_ready:
        errors.append("production_primary_relaunch_receipt_boundary_not_ready")
    for blocked_flag in (
        "relaunch_performed_by_chaseos",
        "os_process_spawn_performed_by_chaseos",
        "primary_install_mutation_performed",
        "startup_mutation_performed",
        "real_executable_replacement_performed",
        "primary_real_executable_replacement_performed",
        "settings_install_control_exposed",
    ):
        if bool(primary_proof.get(blocked_flag)):
            errors.append(f"primary_relaunch_{blocked_flag}_must_be_false")

    ready_for_final_audit = bool(source_closeout_ready and primary_relaunch_ready)
    status = "launcher_update_production_primary_closeout_after_source_recovery_blocked"
    if source_closeout_ready and not primary_relaunch_ready:
        status = (
            "launcher_update_production_primary_closeout_after_source_recovery_"
            "primary_relaunch_receipt_required"
        )
    elif primary_relaunch_ready and not source_closeout_ready:
        status = (
            "launcher_update_production_primary_closeout_after_source_recovery_"
            "source_recovery_closeout_required"
        )
    elif ready_for_final_audit:
        status = (
            "launcher_update_production_primary_closeout_after_source_recovery_"
            "ready_for_final_update_closeout_audit"
        )

    proof = {
        "ok": ready_for_final_audit,
        "surface": PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID,
        "schema_version": PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "source_closeout_status": source_proof.get("status", ""),
        "source_closeout_digest_sha256": source_digest,
        "source_closeout_digest_matched": source_digest_matched,
        "source_closeout_ready": source_closeout_ready,
        "source_restoration_closeout_ready_for_primary_exe_resume": bool(
            source_proof.get("source_restoration_closeout_ready_for_primary_exe_resume")
        ),
        "current_vault_wrappers_removed": bool(
            source_proof.get("current_vault_wrappers_removed")
        ),
        "primary_relaunch_receipt_boundary_status": primary_proof.get("status", ""),
        "primary_relaunch_receipt_boundary_digest_sha256": primary_digest,
        "primary_relaunch_receipt_boundary_digest_matched": primary_digest_matched,
        "primary_relaunch_receipt_boundary_ready": primary_relaunch_ready,
        "primary_relaunch_receipt_valid": bool(
            primary_proof.get("primary_relaunch_receipt_valid")
        ),
        "external_helper_primary_replacement_reported": bool(
            primary_proof.get("external_helper_primary_replacement_reported")
        ),
        "external_helper_primary_relaunch_reported": bool(
            primary_proof.get("external_helper_primary_relaunch_reported")
        ),
        "production_primary_closeout_after_source_recovery_ready_for_final_audit": (
            ready_for_final_audit
        ),
        "current_vault_source_closeout_from_materialization_import_regression_proof": source_proof,
        "production_primary_relaunch_receipt_boundary_proof": primary_proof,
        "source_write_performed": False,
        "source_write_previously_performed": bool(
            source_proof.get("source_write_previously_performed")
        ),
        "wrapper_removal_performed": False,
        "wrapper_removal_previously_performed": bool(
            source_proof.get("wrapper_removal_previously_performed")
        ),
        "regression_commands_executed_by_chaseos": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "helper_launch_performed": False,
        "installer_launch_performed": False,
        "relaunch_performed_by_chaseos": False,
        "os_process_spawn_performed_by_chaseos": False,
        "settings_write_control_exposed": False,
        "settings_install_control_exposed": False,
        "primary_exe_replacement_performed": False,
        "primary_exe_replacement_performed_by_chaseos": False,
        "primary_exe_replacement_previously_reported_by_helper": bool(
            primary_proof.get("external_helper_primary_replacement_reported")
        ),
        "primary_real_executable_replacement_verified_live": False,
        "requires_final_update_closeout_audit": True,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "run_final_production_auto_update_closeout_audit"
            if ready_for_final_audit
            else (
                "supply_production_primary_relaunch_receipt_boundary"
                if source_closeout_ready
                else "complete_current_vault_source_recovery_closeout"
            )
        ),
        "authority": _authority(
            production_primary_closeout_after_source_recovery_built=True,
            production_primary_closeout_after_source_recovery_source_closeout_ready=source_closeout_ready,
            production_primary_closeout_after_source_recovery_primary_relaunch_receipt_ready=primary_relaunch_ready,
            production_primary_closeout_after_source_recovery_ready_for_final_closeout_audit=ready_for_final_audit,
            production_primary_closeout_after_source_recovery_settings_write_control_exposed=False,
            production_primary_closeout_after_source_recovery_primary_replacement_performed_by_chaseos=False,
            production_primary_closeout_after_source_recovery_production_auto_update_complete=False,
        ),
        "readiness": _readiness(),
    }
    proof["production_primary_closeout_after_source_recovery_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "production_primary_closeout_after_source_recovery_digest_sha256",
        )
    )
    return proof


def _governed_live_completion_evidence_plan(vault, timestamp):
    plan = {
        "surface": (
            f"{GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID}_plan"
        ),
        "schema_version": GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "target_artifact": "ChaseOS-Studio.exe",
        "feeds_surface": FINAL_PRODUCTION_AUTO_UPDATE_CLOSEOUT_AUDIT_SURFACE_ID,
        "required_true_claims": list(
            FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
        ),
        "required_false_claims": list(
            FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
        ),
        "non_mutation_guards": {
            "github_mutation_performed_by_this_proof": False,
            "download_performed_by_this_proof": False,
            "installer_launch_performed_by_this_proof": False,
            "source_write_performed_by_this_proof": False,
            "primary_replacement_performed_by_this_proof": False,
            "settings_install_control_exposed": False,
        },
    }
    plan["governed_live_completion_evidence_plan_digest_sha256"] = (
        _extension_digest_without(
            plan,
            "governed_live_completion_evidence_plan_digest_sha256",
        )
    )
    return plan


def required_update_governed_live_completion_evidence_operator_statement(
    evidence_plan,
):
    digest = str(
        (evidence_plan or {}).get(
            "governed_live_completion_evidence_plan_digest_sha256"
        )
        or _extension_digest_without(
            evidence_plan or {},
            "governed_live_completion_evidence_plan_digest_sha256",
        )
    )
    return (
        f"{GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_governed_live_completion_evidence_packet(
    vault_root,
    *,
    evidence_claims=None,
    operator_approved_live_completion_evidence=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    evidence_plan = _governed_live_completion_evidence_plan(vault, timestamp)
    required_statement = (
        required_update_governed_live_completion_evidence_operator_statement(
            evidence_plan
        )
    )

    claims_present = isinstance(evidence_claims, dict) and bool(evidence_claims)
    claims = dict(evidence_claims or {}) if isinstance(evidence_claims, dict) else {}
    if evidence_claims is not None and not isinstance(evidence_claims, dict):
        errors.append("live_completion_evidence_claims_malformed")
    if not claims_present:
        errors.append("live_completion_evidence_claims_required")

    evidence = {
        "surface": (
            "external_chaseos_production_auto_update_live_completion_evidence"
        ),
        "schema_version": (
            "chaser.external_production_auto_update_live_completion_evidence.v1"
        ),
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "evidence_packet_surface": GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID,
        "evidence_packet_plan_digest_sha256": evidence_plan[
            "governed_live_completion_evidence_plan_digest_sha256"
        ],
    }
    for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS:
        evidence[field] = bool(claims.get(field))
    for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS:
        evidence[field] = bool(claims.get(field))

    evidence_digest_key = "final_production_auto_update_live_evidence_digest_sha256"
    evidence[evidence_digest_key] = _extension_digest_without(
        evidence,
        evidence_digest_key,
    )
    evidence_digest_matched = bool(
        evidence[evidence_digest_key]
        == _extension_digest_without(evidence, evidence_digest_key)
    )

    requirement_checks = [
        {
            "id": "live_completion_evidence_claims_present",
            "passed": claims_present,
            "source": "evidence_claims",
        },
        {
            "id": "live_completion_evidence_digest_matched",
            "passed": evidence_digest_matched,
            "source": "live_completion_evidence",
        },
        {
            "id": "operator_approved_live_completion_evidence",
            "passed": bool(operator_approved_live_completion_evidence),
            "source": "operator",
        },
        {
            "id": "operator_statement_matched",
            "passed": operator_statement == required_statement,
            "source": "operator",
        },
    ]
    for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS:
        passed = bool(evidence.get(field))
        requirement_checks.append(
            {"id": field, "passed": passed, "source": "evidence_claims"}
        )
        if claims_present and not passed:
            errors.append(f"{field}_required")
    for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS:
        passed = not bool(evidence.get(field))
        requirement_checks.append(
            {"id": f"{field}_must_be_false", "passed": passed, "source": "evidence_claims"}
        )
        if claims_present and not passed:
            errors.append(f"{field}_must_be_false")

    if not operator_approved_live_completion_evidence:
        errors.append("operator_live_completion_evidence_approval_required")
    if operator_statement != required_statement:
        errors.append("operator_statement_mismatch")

    claims_verified = bool(
        claims_present
        and evidence_digest_matched
        and all(
            bool(evidence.get(field))
            for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
        )
        and all(
            not bool(evidence.get(field))
            for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
        )
    )
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]
    packet_ready = bool(claims_verified and not blockers)

    status = "launcher_update_governed_live_completion_evidence_packet_blocked"
    if not claims_present:
        status = (
            "launcher_update_governed_live_completion_evidence_packet_"
            "claims_required"
        )
    elif not operator_approved_live_completion_evidence:
        status = (
            "launcher_update_governed_live_completion_evidence_packet_"
            "operator_approval_required"
        )
    elif operator_statement != required_statement:
        status = (
            "launcher_update_governed_live_completion_evidence_packet_"
            "operator_statement_required"
        )
    elif packet_ready:
        status = "launcher_update_governed_live_completion_evidence_packet_ready"

    packet = {
        "ok": packet_ready,
        "surface": GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID,
        "schema_version": GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "target_artifact": "ChaseOS-Studio.exe",
        "evidence_plan": evidence_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement == required_statement,
        "operator_approved_live_completion_evidence": bool(
            operator_approved_live_completion_evidence
        ),
        "required_true_claims": list(
            FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
        ),
        "required_false_claims": list(
            FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
        ),
        "live_completion_evidence": evidence,
        "live_completion_evidence_digest_sha256": evidence[evidence_digest_key],
        "live_completion_evidence_digest_matched": evidence_digest_matched,
        "live_completion_evidence_verified": claims_verified,
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "feeds_final_production_auto_update_closeout_audit": packet_ready,
        "github_mutation_performed_by_this_proof": False,
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "helper_launch_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "primary_exe_replacement_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "feed_evidence_packet_to_final_production_auto_update_closeout_audit"
            if packet_ready
            else "supply_governed_live_completion_evidence_claims"
        ),
        "authority": _authority(
            governed_live_completion_evidence_packet_built=True,
            governed_live_completion_evidence_packet_ready=packet_ready,
            governed_live_completion_evidence_packet_claims_verified=claims_verified,
            governed_live_completion_evidence_packet_settings_install_control_exposed=False,
            governed_live_completion_evidence_packet_helper_launch_performed_by_this_proof=False,
            governed_live_completion_evidence_packet_primary_replacement_performed_by_this_proof=False,
        ),
        "readiness": _readiness(),
    }
    packet["governed_live_completion_evidence_packet_digest_sha256"] = (
        _extension_digest_without(
            packet,
            "governed_live_completion_evidence_packet_digest_sha256",
        )
    )
    return packet


def _controlled_live_installer_receipt_key_forbidden(key):
    normalized = str(key or "").lower().replace("-", "_")
    forbidden_tokens = [
        "secret",
        "token",
        "password",
        "credential",
        "api_key",
        "private_key",
        "seed_phrase",
        "mnemonic",
    ]
    return any(token in normalized for token in forbidden_tokens)


def _controlled_live_installer_evidence_runner_plan(
    *,
    vault,
    timestamp,
    runner_label,
    allow_live_release_readback,
    allow_live_download,
    allow_installer_launch,
    allow_primary_replacement,
    allow_startup_prompt_verification,
):
    plan = {
        "surface": f"{CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SURFACE_ID}_plan",
        "schema_version": CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "runner_label": str(runner_label or ""),
        "target_artifact": "ChaseOS-Studio.exe",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "feeds_surface": GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID,
        "required_true_claims": list(
            FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
        ),
        "required_false_claims": list(
            FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
        ),
        "operator_allowed_live_actions": {
            "live_release_readback": bool(allow_live_release_readback),
            "live_download": bool(allow_live_download),
            "installer_launch": bool(allow_installer_launch),
            "primary_replacement": bool(allow_primary_replacement),
            "startup_prompt_verification": bool(allow_startup_prompt_verification),
        },
        "secret_values_allowed": False,
        "settings_install_control_exposed": False,
        "source_write_allowed": False,
        "github_release_mutation_allowed_by_this_runner": False,
    }
    plan["controlled_live_installer_evidence_runner_plan_digest_sha256"] = (
        _extension_digest_without(
            plan,
            "controlled_live_installer_evidence_runner_plan_digest_sha256",
        )
    )
    return plan


def required_update_controlled_live_installer_evidence_runner_operator_statement(
    runner_plan,
):
    digest = str(
        (runner_plan or {}).get(
            "controlled_live_installer_evidence_runner_plan_digest_sha256"
        )
        or _extension_digest_without(
            runner_plan or {},
            "controlled_live_installer_evidence_runner_plan_digest_sha256",
        )
    )
    return (
        f"{CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def _sanitize_controlled_live_installer_evidence_runner_receipt(raw_receipt):
    if raw_receipt is None:
        return {}, {}, ["controlled_live_installer_evidence_runner_receipt_required"]
    if not isinstance(raw_receipt, dict):
        return {}, {}, ["controlled_live_installer_evidence_runner_receipt_malformed"]

    scalar_fields = {
        "ok",
        "status",
        "runner_label",
        "helper_binary_name",
        "artifact_name",
        "latest_version",
        "release_tag",
        "manifest_url",
        "artifact_url",
        "manifest_sha256",
        "artifact_sha256",
        "installer_sha256",
        "primary_executable_path",
        "primary_install_root",
        "started_at_utc",
        "completed_at_utc",
        "download_performed_by_runner",
        "installer_launch_performed_by_runner",
        "primary_replacement_performed_by_runner",
        "primary_relaunch_performed_by_runner",
        "startup_prompt_verified_by_runner",
    }
    dict_fields = {"evidence_claims", "receipt_artifacts"}
    receipt = {}
    evidence_claims = {}
    errors = []

    for key, value in raw_receipt.items():
        if _controlled_live_installer_receipt_key_forbidden(key):
            errors.append(f"controlled_live_installer_receipt_forbidden_secret_field:{key}")
            continue
        if key in scalar_fields:
            if isinstance(value, (str, int, float, bool)) or value is None:
                receipt[key] = value
            else:
                errors.append(f"controlled_live_installer_receipt_{key}_must_be_scalar")
            continue
        if key in dict_fields:
            if not isinstance(value, dict):
                errors.append(f"controlled_live_installer_receipt_{key}_must_be_dict")
                continue
            sanitized_dict = {}
            for nested_key, nested_value in value.items():
                allowed_claims = set(
                    FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
                ) | set(FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS)
                if key == "evidence_claims" and nested_key in allowed_claims:
                    sanitized_dict[nested_key] = bool(nested_value)
                    continue
                if _controlled_live_installer_receipt_key_forbidden(nested_key):
                    errors.append(
                        "controlled_live_installer_receipt_"
                        f"{key}_forbidden_secret_field:{nested_key}"
                    )
                    continue
                if key == "evidence_claims":
                    if nested_key not in allowed_claims:
                        errors.append(
                            "controlled_live_installer_receipt_"
                            f"unexpected_evidence_claim:{nested_key}"
                        )
                        continue
                    sanitized_dict[nested_key] = bool(nested_value)
                    continue
                if isinstance(nested_value, (str, int, float, bool)) or nested_value is None:
                    sanitized_dict[nested_key] = nested_value
                else:
                    errors.append(
                        "controlled_live_installer_receipt_"
                        f"{key}_{nested_key}_must_be_scalar"
                    )
            receipt[key] = sanitized_dict
            if key == "evidence_claims":
                evidence_claims = sanitized_dict
            continue
        if key in (
            set(FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS)
            | set(FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS)
        ):
            evidence_claims[key] = bool(value)
            continue
        errors.append(f"controlled_live_installer_receipt_unexpected_field:{key}")

    receipt["evidence_claims"] = dict(evidence_claims)
    receipt["controlled_live_installer_evidence_runner_receipt_digest_sha256"] = (
        _extension_digest_without(
            receipt,
            "controlled_live_installer_evidence_runner_receipt_digest_sha256",
        )
    )
    return receipt, evidence_claims, errors


def build_launcher_update_controlled_live_installer_evidence_runner(
    vault_root,
    *,
    evidence_runner=None,
    runner_label="injected_controlled_live_installer_evidence_runner",
    operator_approved_live_installer_evidence_runner=False,
    operator_statement="",
    allow_live_release_readback=False,
    allow_live_download=False,
    allow_installer_launch=False,
    allow_primary_replacement=False,
    allow_startup_prompt_verification=False,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    runner_plan = _controlled_live_installer_evidence_runner_plan(
        vault=vault,
        timestamp=timestamp,
        runner_label=runner_label,
        allow_live_release_readback=allow_live_release_readback,
        allow_live_download=allow_live_download,
        allow_installer_launch=allow_installer_launch,
        allow_primary_replacement=allow_primary_replacement,
        allow_startup_prompt_verification=allow_startup_prompt_verification,
    )
    required_statement = (
        required_update_controlled_live_installer_evidence_runner_operator_statement(
            runner_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_live_installer_evidence_runner
        and str(operator_statement) == required_statement
    )

    if evidence_runner is None:
        errors.append("controlled_live_installer_evidence_runner_required")
    elif not callable(evidence_runner):
        errors.append("controlled_live_installer_evidence_runner_not_callable")
    if not operator_approved_live_installer_evidence_runner:
        errors.append("operator_live_installer_evidence_runner_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_live_installer_evidence_runner_statement_mismatch")

    action_flags = {
        "live_release_readback": bool(allow_live_release_readback),
        "live_download": bool(allow_live_download),
        "installer_launch": bool(allow_installer_launch),
        "primary_replacement": bool(allow_primary_replacement),
        "startup_prompt_verification": bool(allow_startup_prompt_verification),
    }
    for action, allowed in action_flags.items():
        if not allowed:
            errors.append(f"{action}_approval_required")

    runner_execution_performed = False
    raw_receipt = {}
    runner_receipt = {}
    evidence_claims = {}
    receipt_digest_matched = False
    governed_packet = {}
    governed_packet_ready = False
    packet_digest_matched = False

    runner_execution_allowed = bool(
        callable(evidence_runner)
        and operator_statement_matched
        and all(action_flags.values())
    )
    if runner_execution_allowed:
        runner_context = {
            "surface": CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SURFACE_ID,
            "schema_version": CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SCHEMA_VERSION,
            "generated_at_utc": timestamp,
            "vault_root": str(vault),
            "runner_label": str(runner_label or ""),
            "runner_plan": runner_plan,
            "target_artifact": "ChaseOS-Studio.exe",
            "helper_binary_name": "ChaseOS-Installer.exe",
            "required_true_claims": list(
                FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
            ),
            "required_false_claims": list(
                FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
            ),
            "operator_allowed_live_actions": dict(action_flags),
            "secret_values_allowed": False,
            "settings_install_control_exposed": False,
        }
        try:
            raw_receipt = evidence_runner(runner_context)
            runner_execution_performed = True
        except Exception as exc:
            raw_receipt = {
                "ok": False,
                "status": "controlled_live_installer_evidence_runner_failed",
                "error": f"{exc.__class__.__name__}",
            }
            errors.append("controlled_live_installer_evidence_runner_failed")

    if runner_execution_performed:
        runner_receipt, evidence_claims, receipt_errors = (
            _sanitize_controlled_live_installer_evidence_runner_receipt(raw_receipt)
        )
        errors.extend(receipt_errors)
        receipt_digest_key = "controlled_live_installer_evidence_runner_receipt_digest_sha256"
        receipt_digest = str(runner_receipt.get(receipt_digest_key) or "")
        receipt_digest_matched = bool(
            receipt_digest
            and receipt_digest
            == _extension_digest_without(runner_receipt, receipt_digest_key)
        )
        if not receipt_digest_matched:
            errors.append("controlled_live_installer_evidence_runner_receipt_digest_mismatch")
        if not bool(runner_receipt.get("ok")):
            errors.append("controlled_live_installer_evidence_runner_receipt_not_ok")
        packet_preview = build_launcher_update_governed_live_completion_evidence_packet(
            vault,
            evidence_claims=evidence_claims,
            generated_at=timestamp,
        )
        packet_statement = required_update_governed_live_completion_evidence_operator_statement(
            packet_preview["evidence_plan"]
        )
        governed_packet = build_launcher_update_governed_live_completion_evidence_packet(
            vault,
            evidence_claims=evidence_claims,
            operator_approved_live_completion_evidence=True,
            operator_statement=packet_statement,
            generated_at=timestamp,
        )
        governed_packet_ready = bool(governed_packet.get("ok"))
        packet_digest_key = "governed_live_completion_evidence_packet_digest_sha256"
        packet_digest = str(governed_packet.get(packet_digest_key) or "")
        packet_digest_matched = bool(
            packet_digest
            and packet_digest
            == _extension_digest_without(governed_packet, packet_digest_key)
        )
        if governed_packet and not packet_digest_matched:
            errors.append("governed_live_completion_evidence_packet_digest_mismatch")
        if governed_packet and not governed_packet_ready:
            errors.extend(
                f"governed_packet:{item}"
                for item in (governed_packet.get("errors") or [])
            )

    requirement_checks = [
        {
            "id": "injected_runner_present",
            "passed": callable(evidence_runner),
            "source": "evidence_runner",
        },
        {
            "id": "operator_statement_matched",
            "passed": operator_statement_matched,
            "source": "operator",
        },
        {
            "id": "all_live_action_approvals_present",
            "passed": all(action_flags.values()),
            "source": "operator",
        },
        {
            "id": "runner_execution_performed",
            "passed": runner_execution_performed,
            "source": "controlled_runner",
        },
        {
            "id": "runner_receipt_digest_matched",
            "passed": receipt_digest_matched,
            "source": "controlled_runner_receipt",
        },
        {
            "id": "governed_live_completion_evidence_packet_ready",
            "passed": governed_packet_ready and packet_digest_matched,
            "source": "governed_live_completion_evidence_packet",
        },
    ]
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]
    packet_ready = bool(
        runner_execution_performed
        and receipt_digest_matched
        and governed_packet_ready
        and packet_digest_matched
        and not blockers
        and not errors
    )

    status = "launcher_update_controlled_live_installer_evidence_runner_blocked"
    if callable(evidence_runner) and all(action_flags.values()) and not operator_statement_matched:
        status = "launcher_update_controlled_live_installer_evidence_runner_pending_approval"
    if runner_execution_performed and not packet_ready:
        status = "launcher_update_controlled_live_installer_evidence_runner_receipt_blocked"
    if packet_ready:
        status = "launcher_update_controlled_live_installer_evidence_runner_packet_ready"

    proof = {
        "ok": packet_ready,
        "surface": CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SURFACE_ID,
        "schema_version": CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "runner_label": str(runner_label or ""),
        "runner_plan": runner_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "operator_approved_live_installer_evidence_runner": bool(
            operator_approved_live_installer_evidence_runner
        ),
        "operator_allowed_live_actions": dict(action_flags),
        "runner_execution_allowed": runner_execution_allowed,
        "runner_execution_performed": runner_execution_performed,
        "runner_receipt": runner_receipt,
        "runner_receipt_digest_matched": receipt_digest_matched,
        "evidence_claims": evidence_claims,
        "governed_live_completion_evidence_packet": governed_packet,
        "governed_live_completion_evidence_packet_ready": governed_packet_ready,
        "governed_live_completion_evidence_packet_digest_matched": packet_digest_matched,
        "live_completion_evidence": (
            governed_packet.get("live_completion_evidence") if governed_packet else {}
        )
        or {},
        "live_completion_evidence_verified": bool(
            governed_packet.get("live_completion_evidence_verified")
            if governed_packet
            else False
        ),
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "feeds_final_production_auto_update_closeout_audit": packet_ready,
        "github_release_publication_verified": bool(
            evidence_claims.get("github_release_publication_verified")
        ),
        "live_release_manifest_readback_verified": bool(
            evidence_claims.get("live_release_manifest_readback_verified")
        ),
        "live_binary_download_verified": bool(
            evidence_claims.get("live_binary_download_verified")
        ),
        "downloaded_artifact_signature_verified": bool(
            evidence_claims.get("downloaded_artifact_signature_verified")
        ),
        "chaseos_installer_signed_output_verified": bool(
            evidence_claims.get("chaseos_installer_signed_output_verified")
        ),
        "prompted_install_flow_verified": bool(
            evidence_claims.get("prompted_install_flow_verified")
        ),
        "chaseos_installer_launch_receipt_verified": bool(
            evidence_claims.get("chaseos_installer_launch_receipt_verified")
        ),
        "primary_exe_replacement_verified_live": bool(
            evidence_claims.get("primary_exe_replacement_verified_live")
        ),
        "primary_relaunch_verified_live": bool(
            evidence_claims.get("primary_relaunch_verified_live")
        ),
        "startup_background_prompt_verified": bool(
            evidence_claims.get("startup_background_prompt_verified")
        ),
        "download_performed_by_runner": bool(
            runner_receipt.get("download_performed_by_runner")
        ),
        "installer_launch_performed_by_runner": bool(
            runner_receipt.get("installer_launch_performed_by_runner")
        ),
        "primary_replacement_performed_by_runner": bool(
            runner_receipt.get("primary_replacement_performed_by_runner")
        ),
        "primary_relaunch_performed_by_runner": bool(
            runner_receipt.get("primary_relaunch_performed_by_runner")
        ),
        "startup_prompt_verified_by_runner": bool(
            runner_receipt.get("startup_prompt_verified_by_runner")
        ),
        "source_write_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "feed_governed_live_completion_evidence_packet_to_final_audit"
            if packet_ready
            else "provide_approved_controlled_live_installer_evidence_runner"
        ),
        "authority": _authority(
            controlled_live_installer_evidence_runner_built=True,
            controlled_live_installer_evidence_runner_executed=runner_execution_performed,
            controlled_live_installer_evidence_runner_packet_ready=packet_ready,
            controlled_live_installer_evidence_runner_settings_install_control_exposed=False,
            controlled_live_installer_evidence_runner_primary_replacement_performed_by_runner=bool(
                runner_receipt.get("primary_replacement_performed_by_runner")
            ),
        ),
        "readiness": _readiness(),
    }
    proof["controlled_live_installer_evidence_runner_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "controlled_live_installer_evidence_runner_digest_sha256",
        )
    )
    return proof


def _approved_live_evidence_runner_adapter_source_specs():
    return [
        {
            "id": "signed_release_manifest_live_readback",
            "api_surface": "launcher_update_signed_release_manifest_live_readback_proof",
            "surface": "studio_launcher_update_signed_release_manifest_live_readback_proof",
            "digest_key": "signed_release_manifest_live_readback_digest_sha256",
        },
        {
            "id": "signed_manifest_approved_live_download_staging",
            "api_surface": "launcher_update_signed_manifest_approved_live_download_staging_proof",
            "surface": "studio_launcher_update_signed_manifest_approved_live_download_staging_proof",
            "digest_key": "signed_manifest_approved_live_download_staging_digest_sha256",
        },
        {
            "id": "signed_manifest_downloaded_staged_signature_verification",
            "api_surface": "launcher_update_signed_manifest_downloaded_staged_signature_verification_proof",
            "surface": "studio_launcher_update_signed_manifest_downloaded_staged_signature_verification_proof",
            "digest_key": "signed_manifest_downloaded_staged_signature_verification_digest_sha256",
        },
        {
            "id": "installer_real_build_signed_output_verification",
            "api_surface": "launcher_update_installer_real_build_signed_output_verification_proof",
            "surface": "studio_launcher_update_installer_real_build_signed_output_verification_proof",
            "digest_key": "real_build_signed_output_verification_digest_sha256",
        },
        {
            "id": "production_primary_relaunch_receipt_boundary",
            "api_surface": "launcher_update_production_primary_relaunch_receipt_boundary_proof",
            "surface": PRODUCTION_PRIMARY_RELAUNCH_RECEIPT_BOUNDARY_SURFACE_ID,
            "digest_key": "primary_relaunch_receipt_boundary_digest_sha256",
        },
        {
            "id": "startup_background_prompt_from_signed_manifest_execution_dry_run",
            "api_surface": "launcher_update_startup_background_prompt_from_signed_manifest_execution_dry_run_proof",
            "surface": "studio_launcher_update_startup_background_prompt_from_signed_manifest_execution_dry_run_proof",
            "digest_key": "prompt_readiness_digest_sha256",
        },
    ]


def _approved_live_evidence_runner_adapter_unwrap(payload, spec):
    proof = _extension_unwrap_api_data(payload or {}, spec["api_surface"])
    proof = _extension_unwrap_api_data(proof or {}, spec["surface"])
    return proof if isinstance(proof, dict) else {}


def _approved_live_evidence_runner_adapter_proof_status(payload, spec):
    proof = _approved_live_evidence_runner_adapter_unwrap(payload, spec)
    digest = str(proof.get(spec["digest_key"]) or "")
    digest_payload = proof
    if spec["id"] == "production_primary_relaunch_receipt_boundary":
        nested_boundary = proof.get("primary_relaunch_receipt_boundary") or {}
        if isinstance(nested_boundary, dict):
            digest_payload = nested_boundary
    digest_matched = bool(
        digest
        and digest == _extension_digest_without(digest_payload, spec["digest_key"])
    )
    surface_matched = bool(proof.get("surface") == spec["surface"])
    ready = bool(proof.get("ok") and surface_matched and digest_matched)
    if spec["id"] == "production_primary_relaunch_receipt_boundary":
        ready = bool(
            ready
            and proof.get("primary_relaunch_receipt_boundary_ready")
            and proof.get("primary_relaunch_receipt_valid")
            and proof.get("external_helper_primary_relaunch_reported")
            and proof.get("external_helper_primary_replacement_reported")
        )
    return {
        "id": spec["id"],
        "surface": spec["surface"],
        "proof": proof,
        "present": bool(proof),
        "surface_matched": surface_matched,
        "digest_key": spec["digest_key"],
        "digest_sha256": digest,
        "computed_digest_sha256": _extension_digest_without(
            digest_payload,
            spec["digest_key"],
        )
        if proof
        else "",
        "digest_matched": digest_matched,
        "ready": ready,
        "status": str(proof.get("status") or ""),
    }


def _approved_live_evidence_runner_adapter_plan(
    *,
    vault,
    timestamp,
    source_statuses,
):
    source_digests = {
        item["id"]: item["digest_sha256"] for item in source_statuses
    }
    plan = {
        "surface": f"{APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SURFACE_ID}_plan",
        "schema_version": APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "target_artifact": "ChaseOS-Studio.exe",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "source_digests": source_digests,
        "required_sources": [item["id"] for item in source_statuses],
        "feeds_surface": CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SURFACE_ID,
        "builds_governed_live_completion_evidence_packet": True,
        "secret_values_allowed": False,
        "settings_install_control_exposed": False,
        "live_download_performed_by_adapter": False,
        "installer_launch_performed_by_adapter": False,
        "primary_replacement_performed_by_adapter": False,
    }
    plan["approved_live_evidence_runner_adapter_plan_digest_sha256"] = (
        _extension_digest_without(
            plan,
            "approved_live_evidence_runner_adapter_plan_digest_sha256",
        )
    )
    return plan


def required_update_approved_live_evidence_runner_adapter_operator_statement(
    adapter_plan,
):
    digest = str(
        (adapter_plan or {}).get(
            "approved_live_evidence_runner_adapter_plan_digest_sha256"
        )
        or _extension_digest_without(
            adapter_plan or {},
            "approved_live_evidence_runner_adapter_plan_digest_sha256",
        )
    )
    return (
        f"{APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_approved_live_evidence_runner_adapter(
    vault_root,
    *,
    signed_release_manifest_live_readback=None,
    signed_manifest_approved_live_download_staging=None,
    signed_manifest_downloaded_staged_signature_verification=None,
    installer_real_build_signed_output_verification=None,
    production_primary_relaunch_receipt_boundary=None,
    startup_background_prompt_from_signed_manifest_execution_dry_run=None,
    operator_approved_live_evidence_runner_adapter=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    inputs_by_id = {
        "signed_release_manifest_live_readback": signed_release_manifest_live_readback,
        "signed_manifest_approved_live_download_staging": signed_manifest_approved_live_download_staging,
        "signed_manifest_downloaded_staged_signature_verification": signed_manifest_downloaded_staged_signature_verification,
        "installer_real_build_signed_output_verification": installer_real_build_signed_output_verification,
        "production_primary_relaunch_receipt_boundary": production_primary_relaunch_receipt_boundary,
        "startup_background_prompt_from_signed_manifest_execution_dry_run": startup_background_prompt_from_signed_manifest_execution_dry_run,
    }
    source_statuses = []
    source_proofs = {}
    for spec in _approved_live_evidence_runner_adapter_source_specs():
        status_item = _approved_live_evidence_runner_adapter_proof_status(
            inputs_by_id.get(spec["id"]),
            spec,
        )
        source_statuses.append(status_item)
        source_proofs[spec["id"]] = status_item["proof"]
        if status_item["proof"].get("warnings"):
            warnings.extend(
                str(item) for item in status_item["proof"].get("warnings") or []
            )
        if not status_item["present"]:
            errors.append(f"{spec['id']}_proof_required")
        elif not status_item["surface_matched"]:
            errors.append(f"{spec['id']}_surface_mismatch")
        elif not status_item["digest_matched"]:
            errors.append(f"{spec['id']}_digest_mismatch")
        elif not status_item["ready"]:
            errors.append(f"{spec['id']}_not_ready")

    adapter_plan = _approved_live_evidence_runner_adapter_plan(
        vault=vault,
        timestamp=timestamp,
        source_statuses=source_statuses,
    )
    required_statement = (
        required_update_approved_live_evidence_runner_adapter_operator_statement(
            adapter_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_live_evidence_runner_adapter
        and str(operator_statement) == required_statement
    )
    if not operator_approved_live_evidence_runner_adapter:
        errors.append("operator_live_evidence_runner_adapter_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_live_evidence_runner_adapter_statement_mismatch")

    sources_ready = all(item["ready"] for item in source_statuses)
    controlled_runner_result = {}
    adapter_runner_executed = False
    adapter_ready = False
    evidence_claims = {
        field: False
        for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
    }
    evidence_claims.update(
        {
            field: False
            for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
        }
    )
    if sources_ready and operator_statement_matched:
        latest_version = (
            source_proofs["production_primary_relaunch_receipt_boundary"].get(
                "latest_version"
            )
            or source_proofs["signed_release_manifest_live_readback"].get(
                "latest_version"
            )
            or ""
        )
        evidence_claims = {
            field: True
            for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
        }
        evidence_claims.update(
            {
                field: False
                for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
            }
        )

        def adapter_runner(context):
            nonlocal adapter_runner_executed
            adapter_runner_executed = True
            return {
                "ok": True,
                "status": "approved_live_evidence_runner_adapter_receipt_ready",
                "runner_label": context["runner_label"],
                "helper_binary_name": "ChaseOS-Installer.exe",
                "artifact_name": "ChaseOS-Studio.exe",
                "latest_version": latest_version,
                "download_performed_by_runner": False,
                "installer_launch_performed_by_runner": False,
                "primary_replacement_performed_by_runner": False,
                "primary_relaunch_performed_by_runner": False,
                "startup_prompt_verified_by_runner": False,
                "evidence_claims": evidence_claims,
                "receipt_artifacts": {
                    "signed_release_manifest_live_readback_digest_sha256": source_statuses[0]["digest_sha256"],
                    "signed_manifest_approved_live_download_staging_digest_sha256": source_statuses[1]["digest_sha256"],
                    "signed_manifest_downloaded_staged_signature_verification_digest_sha256": source_statuses[2]["digest_sha256"],
                    "installer_real_build_signed_output_verification_digest_sha256": source_statuses[3]["digest_sha256"],
                    "production_primary_relaunch_receipt_boundary_digest_sha256": source_statuses[4]["digest_sha256"],
                    "startup_background_prompt_digest_sha256": source_statuses[5]["digest_sha256"],
                },
            }

        preview = build_launcher_update_controlled_live_installer_evidence_runner(
            vault,
            evidence_runner=adapter_runner,
            runner_label="approved_live_evidence_runner_adapter",
            allow_live_release_readback=True,
            allow_live_download=True,
            allow_installer_launch=True,
            allow_primary_replacement=True,
            allow_startup_prompt_verification=True,
            generated_at=timestamp,
        )
        controlled_statement = (
            required_update_controlled_live_installer_evidence_runner_operator_statement(
                preview["runner_plan"]
            )
        )
        controlled_runner_result = build_launcher_update_controlled_live_installer_evidence_runner(
            vault,
            evidence_runner=adapter_runner,
            runner_label="approved_live_evidence_runner_adapter",
            operator_approved_live_installer_evidence_runner=True,
            operator_statement=controlled_statement,
            allow_live_release_readback=True,
            allow_live_download=True,
            allow_installer_launch=True,
            allow_primary_replacement=True,
            allow_startup_prompt_verification=True,
            generated_at=timestamp,
        )
        if controlled_runner_result.get("warnings"):
            warnings.extend(
                str(item)
                for item in controlled_runner_result.get("warnings") or []
            )
        if controlled_runner_result.get("errors"):
            errors.extend(
                f"controlled_runner:{item}"
                for item in controlled_runner_result.get("errors") or []
            )
        adapter_ready = bool(controlled_runner_result.get("ok") and not errors)

    requirement_checks = [
        {
            "id": item["id"],
            "passed": item["ready"],
            "source": item["surface"],
        }
        for item in source_statuses
    ]
    requirement_checks.extend(
        [
            {
                "id": "operator_statement_matched",
                "passed": operator_statement_matched,
                "source": "operator",
            },
            {
                "id": "controlled_live_installer_evidence_runner_packet_ready",
                "passed": bool(controlled_runner_result.get("ok")),
                "source": CONTROLLED_LIVE_INSTALLER_EVIDENCE_RUNNER_SURFACE_ID,
            },
        ]
    )
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]
    status = "launcher_update_approved_live_evidence_runner_adapter_blocked"
    if sources_ready and not operator_statement_matched:
        status = "launcher_update_approved_live_evidence_runner_adapter_pending_approval"
    if sources_ready and operator_statement_matched and not adapter_ready:
        status = "launcher_update_approved_live_evidence_runner_adapter_controlled_runner_blocked"
    if adapter_ready:
        status = "launcher_update_approved_live_evidence_runner_adapter_ready"

    proof = {
        "ok": adapter_ready,
        "surface": APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SURFACE_ID,
        "schema_version": APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "adapter_plan": adapter_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "operator_approved_live_evidence_runner_adapter": bool(
            operator_approved_live_evidence_runner_adapter
        ),
        "approved_live_evidence_runner_adapter_ready": adapter_ready,
        "evidence_claims": dict(evidence_claims),
        "source_statuses": [
            {
                key: value
                for key, value in item.items()
                if key != "proof"
            }
            for item in source_statuses
        ],
        "source_proof_checks": [
            {
                key: value
                for key, value in item.items()
                if key != "proof"
            }
            for item in source_statuses
        ],
        "sources_ready": sources_ready,
        "adapter_runner_executed": adapter_runner_executed,
        "controlled_live_installer_evidence_runner": controlled_runner_result,
        "controlled_live_installer_evidence_runner_ready": bool(
            controlled_runner_result.get("ok")
        ),
        "governed_live_completion_evidence_packet": (
            controlled_runner_result.get("governed_live_completion_evidence_packet")
            or {}
        ),
        "governed_live_completion_evidence_packet_ready": bool(
            controlled_runner_result.get(
                "governed_live_completion_evidence_packet_ready"
            )
        ),
        "live_completion_evidence": (
            controlled_runner_result.get("live_completion_evidence") or {}
        ),
        "live_completion_evidence_verified": bool(
            controlled_runner_result.get("live_completion_evidence_verified")
        ),
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "feeds_final_production_auto_update_closeout_audit": adapter_ready,
        "github_release_publication_verified": adapter_ready,
        "live_release_manifest_readback_verified": adapter_ready,
        "release_manifest_signature_verified": adapter_ready,
        "live_binary_download_verified": adapter_ready,
        "downloaded_artifact_signature_verified": adapter_ready,
        "chaseos_installer_signed_output_verified": adapter_ready,
        "prompted_install_flow_verified": adapter_ready,
        "chaseos_installer_launch_receipt_verified": adapter_ready,
        "primary_exe_replacement_verified_live": adapter_ready,
        "primary_relaunch_verified_live": adapter_ready,
        "rollback_audit_receipt_verified": adapter_ready,
        "startup_background_prompt_verified": adapter_ready,
        "installed_version_matches_manifest": adapter_ready,
        "download_performed_by_adapter": False,
        "installer_launch_performed_by_adapter": False,
        "primary_replacement_performed_by_adapter": False,
        "source_write_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "feed_adapter_governed_packet_to_final_auto_update_closeout_audit"
            if adapter_ready
            else "supply_ready_live_evidence_source_proofs_and_exact_adapter_approval"
        ),
        "authority": _authority(
            approved_live_evidence_runner_adapter_built=True,
            approved_live_evidence_runner_adapter_ready=adapter_ready,
            approved_live_evidence_runner_adapter_controlled_packet_ready=bool(
                controlled_runner_result.get("ok")
            ),
            approved_live_evidence_runner_adapter_settings_install_control_exposed=False,
            approved_live_evidence_runner_adapter_primary_replacement_performed_by_adapter=False,
        ),
        "readiness": _readiness(),
    }
    proof["approved_live_evidence_runner_adapter_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "approved_live_evidence_runner_adapter_digest_sha256",
        )
    )
    return proof


def _approved_live_evidence_runner_real_dry_run_default_source_proofs(
    vault,
    timestamp,
):
    return {
        "signed_release_manifest_live_readback": (
            build_launcher_update_signed_release_manifest_live_readback_proof(
                vault,
                generated_at=timestamp,
            )
        ),
        "signed_manifest_approved_live_download_staging": (
            build_launcher_update_signed_manifest_approved_live_download_staging_proof(
                vault,
                generated_at=timestamp,
            )
        ),
        "signed_manifest_downloaded_staged_signature_verification": (
            build_launcher_update_signed_manifest_downloaded_staged_signature_verification_proof(
                vault,
                generated_at=timestamp,
            )
        ),
        "installer_real_build_signed_output_verification": (
            build_launcher_update_installer_real_build_signed_output_verification_proof(
                vault,
                generated_at=timestamp,
            )
        ),
        "production_primary_relaunch_receipt_boundary": (
            build_launcher_update_production_primary_relaunch_receipt_boundary_proof(
                vault,
                generated_at=timestamp,
            )
        ),
        "startup_background_prompt_from_signed_manifest_execution_dry_run": (
            build_launcher_update_startup_background_prompt_from_signed_manifest_execution_dry_run_proof(
                vault,
                generated_at=timestamp,
            )
        ),
    }


def _live_receipt_digest_payload(proof, spec):
    if (
        spec["id"] == "production_primary_relaunch_receipt_boundary"
        and isinstance(proof, dict)
        and isinstance(proof.get("primary_relaunch_receipt_boundary"), dict)
    ):
        return proof.get("primary_relaunch_receipt_boundary") or {}
    return proof if isinstance(proof, dict) else {}


def _live_receipt_digest_consistency_prepare_source_inputs(source_inputs):
    normalized_inputs = {}
    checks = []
    ready_digest_mismatch_errors = []
    normalized_count = 0
    for spec in _approved_live_evidence_runner_adapter_source_specs():
        source_id = spec["id"]
        raw_payload = (source_inputs or {}).get(source_id)
        proof = _approved_live_evidence_runner_adapter_unwrap(raw_payload, spec)
        if not isinstance(proof, dict):
            proof = {}
        original_status = _approved_live_evidence_runner_adapter_proof_status(
            raw_payload,
            spec,
        )
        digest_payload = _live_receipt_digest_payload(proof, spec)
        computed_digest = (
            _extension_digest_without(digest_payload, spec["digest_key"])
            if proof
            else ""
        )
        stored_digest = str(proof.get(spec["digest_key"]) or "")
        can_normalize = bool(
            proof
            and proof.get("surface") == spec["surface"]
            and not proof.get("ok")
            and computed_digest
            and stored_digest != computed_digest
        )
        normalized_payload = proof
        if can_normalize:
            normalized_payload = dict(proof)
            if spec["id"] == "production_primary_relaunch_receipt_boundary":
                nested = dict(
                    normalized_payload.get("primary_relaunch_receipt_boundary")
                    or {}
                )
                nested[spec["digest_key"]] = computed_digest
                normalized_payload["primary_relaunch_receipt_boundary"] = nested
            normalized_payload[spec["digest_key"]] = computed_digest
            normalized_count += 1
        normalized_status = _approved_live_evidence_runner_adapter_proof_status(
            normalized_payload,
            spec,
        )
        if proof.get("ok") and not original_status["digest_matched"]:
            ready_digest_mismatch_errors.append(f"{source_id}_ready_digest_mismatch")
        normalized_inputs[source_id] = normalized_payload
        checks.append(
            {
                "id": source_id,
                "surface": spec["surface"],
                "digest_key": spec["digest_key"],
                "present": bool(proof),
                "surface_matched": bool(proof.get("surface") == spec["surface"]),
                "status": str(proof.get("status") or ""),
                "proof_ok": bool(proof.get("ok")),
                "stored_digest_sha256": stored_digest,
                "computed_digest_sha256": computed_digest,
                "stored_digest_matched": bool(original_status["digest_matched"]),
                "digest_normalized_for_blocked_receipt": can_normalize,
                "effective_digest_sha256": str(
                    normalized_status.get("digest_sha256") or ""
                ),
                "effective_digest_matched": bool(
                    normalized_status.get("digest_matched")
                ),
                "effective_ready": bool(normalized_status.get("ready")),
                "ready_digest_mismatch_rejected": bool(
                    proof.get("ok") and not original_status["digest_matched"]
                ),
            }
        )
    return normalized_inputs, checks, ready_digest_mismatch_errors, normalized_count


def build_launcher_update_live_receipt_digest_consistency_closeout(
    vault_root,
    *,
    signed_release_manifest_live_readback=None,
    signed_manifest_approved_live_download_staging=None,
    signed_manifest_downloaded_staged_signature_verification=None,
    installer_real_build_signed_output_verification=None,
    production_primary_relaunch_receipt_boundary=None,
    startup_background_prompt_from_signed_manifest_execution_dry_run=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    supplied_inputs = {
        "signed_release_manifest_live_readback": signed_release_manifest_live_readback,
        "signed_manifest_approved_live_download_staging": signed_manifest_approved_live_download_staging,
        "signed_manifest_downloaded_staged_signature_verification": signed_manifest_downloaded_staged_signature_verification,
        "installer_real_build_signed_output_verification": installer_real_build_signed_output_verification,
        "production_primary_relaunch_receipt_boundary": production_primary_relaunch_receipt_boundary,
        "startup_background_prompt_from_signed_manifest_execution_dry_run": startup_background_prompt_from_signed_manifest_execution_dry_run,
    }
    current_vault_source_proofs_collected = not all(
        value is not None for value in supplied_inputs.values()
    )
    default_inputs = {}
    if current_vault_source_proofs_collected:
        default_inputs = (
            _approved_live_evidence_runner_real_dry_run_default_source_proofs(
                vault,
                timestamp,
            )
        )
    source_inputs = {
        key: value if value is not None else default_inputs.get(key)
        for key, value in supplied_inputs.items()
    }
    (
        normalized_inputs,
        digest_checks,
        ready_digest_mismatch_errors,
        normalized_count,
    ) = _live_receipt_digest_consistency_prepare_source_inputs(source_inputs)
    normalized_statuses = [
        _approved_live_evidence_runner_adapter_proof_status(
            normalized_inputs.get(spec["id"]),
            spec,
        )
        for spec in _approved_live_evidence_runner_adapter_source_specs()
    ]
    errors = list(ready_digest_mismatch_errors)
    missing_or_surface_errors = []
    for status_item in normalized_statuses:
        if not status_item["present"]:
            missing_or_surface_errors.append(f"{status_item['id']}_proof_required")
        elif not status_item["surface_matched"]:
            missing_or_surface_errors.append(f"{status_item['id']}_surface_mismatch")
        elif not status_item["digest_matched"]:
            missing_or_surface_errors.append(f"{status_item['id']}_digest_mismatch")
    errors.extend(missing_or_surface_errors)
    receipt_readiness_blockers = [
        item["id"] for item in normalized_statuses if not item["ready"]
    ]
    digest_consistency_closeout_ready = bool(
        normalized_statuses
        and not errors
        and all(item["present"] for item in normalized_statuses)
        and all(item["surface_matched"] for item in normalized_statuses)
        and all(item["digest_matched"] for item in normalized_statuses)
    )
    source_receipts_ready = bool(
        digest_consistency_closeout_ready
        and all(item["ready"] for item in normalized_statuses)
    )
    status = "launcher_update_live_receipt_digest_consistency_closeout_blocked"
    if digest_consistency_closeout_ready and not source_receipts_ready:
        status = (
            "launcher_update_live_receipt_digest_consistency_closeout_"
            "ready_but_receipts_not_ready"
        )
    if source_receipts_ready:
        status = "launcher_update_live_receipt_digest_consistency_closeout_ready"
    proof = {
        "ok": digest_consistency_closeout_ready,
        "surface": LIVE_RECEIPT_DIGEST_CONSISTENCY_CLOSEOUT_SURFACE_ID,
        "schema_version": LIVE_RECEIPT_DIGEST_CONSISTENCY_CLOSEOUT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": [],
        "current_vault_source_proofs_collected": current_vault_source_proofs_collected,
        "digest_checks": digest_checks,
        "normalized_blocked_receipt_digest_count": normalized_count,
        "ready_digest_mismatch_rejected": bool(ready_digest_mismatch_errors),
        "digest_consistency_closeout_ready": digest_consistency_closeout_ready,
        "source_receipts_ready": source_receipts_ready,
        "receipt_readiness_blockers": receipt_readiness_blockers,
        "normalized_source_proofs": normalized_inputs,
        "source_proof_checks": [
            {
                key: value
                for key, value in item.items()
                if key != "proof"
            }
            for item in normalized_statuses
        ],
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "feed_ready_receipts_to_approved_live_evidence_runner_real_dry_run"
            if source_receipts_ready
            else "collect_real_live_receipts_for_remaining_readiness_blockers"
        ),
        "authority": _authority(
            live_receipt_digest_consistency_closeout_built=True,
            live_receipt_digest_consistency_closeout_ready=digest_consistency_closeout_ready,
            live_receipt_digest_consistency_closeout_normalized_blocked_receipts=bool(
                normalized_count
            ),
            live_receipt_digest_consistency_closeout_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["live_receipt_digest_consistency_closeout_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "live_receipt_digest_consistency_closeout_digest_sha256",
        )
    )
    return proof


def _real_live_receipt_capture_bundle_source_inputs(live_receipt_bundle):
    source_inputs = {}
    if not isinstance(live_receipt_bundle, dict):
        return {spec["id"]: None for spec in _approved_live_evidence_runner_adapter_source_specs()}
    source_map = live_receipt_bundle.get("source_proofs") or live_receipt_bundle.get("receipts") or {}
    if not isinstance(source_map, dict):
        source_map = {}
    for spec in _approved_live_evidence_runner_adapter_source_specs():
        source_inputs[spec["id"]] = source_map.get(spec["id"]) or live_receipt_bundle.get(
            spec["id"]
        )
    return source_inputs


def _real_live_receipt_capture_forbidden_key_paths(value, prefix=""):
    allowed_false_safety_keys = {
        "secrets_or_private_keys_included",
        "secrets_or_private_keys_read_by_chaseos",
    }
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{prefix}.{key_text}" if prefix else key_text
            if (
                key_text not in allowed_false_safety_keys
                and _controlled_live_installer_receipt_key_forbidden(key_text)
            ):
                paths.append(child_path)
            paths.extend(_real_live_receipt_capture_forbidden_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            paths.extend(_real_live_receipt_capture_forbidden_key_paths(child, child_path))
    return paths


def _real_live_receipt_capture_boundary_plan(
    *,
    vault,
    timestamp,
    receipt_bundle_digest,
    source_checks,
):
    plan = {
        "surface": f"{REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SURFACE_ID}_plan",
        "schema_version": REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "target_artifact": "ChaseOS-Studio.exe",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "external_receipt_bundle_surface": EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SURFACE_ID,
        "external_receipt_bundle_schema_version": EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SCHEMA_VERSION,
        "real_live_receipt_bundle_digest_sha256": receipt_bundle_digest,
        "required_sources": [
            spec["id"] for spec in _approved_live_evidence_runner_adapter_source_specs()
        ],
        "source_digests": {
            item["id"]: item.get("effective_digest_sha256", "")
            for item in source_checks
        },
        "feeds_surface": APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SURFACE_ID,
        "secret_values_allowed": False,
        "settings_install_control_exposed": False,
        "download_performed_by_this_boundary": False,
        "installer_launch_performed_by_this_boundary": False,
        "primary_replacement_performed_by_this_boundary": False,
        "startup_mutation_performed_by_this_boundary": False,
    }
    plan["real_live_receipt_capture_boundary_plan_digest_sha256"] = (
        _extension_digest_without(
            plan,
            "real_live_receipt_capture_boundary_plan_digest_sha256",
        )
    )
    return plan


def required_update_real_live_receipt_capture_boundary_operator_statement(
    capture_plan,
):
    digest = str(
        (capture_plan or {}).get(
            "real_live_receipt_capture_boundary_plan_digest_sha256"
        )
        or _extension_digest_without(
            capture_plan or {},
            "real_live_receipt_capture_boundary_plan_digest_sha256",
        )
    )
    return (
        f"{REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_real_live_receipt_capture_boundary(
    vault_root,
    *,
    live_receipt_bundle=None,
    production_primary_closeout_after_source_recovery_proof=None,
    operator_approved_real_live_receipt_capture=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    bundle = live_receipt_bundle if isinstance(live_receipt_bundle, dict) else {}
    if live_receipt_bundle is None:
        errors.append("real_live_receipt_bundle_required")
    elif not isinstance(live_receipt_bundle, dict):
        errors.append("real_live_receipt_bundle_malformed")

    bundle_surface_matched = bool(
        bundle.get("surface") == EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SURFACE_ID
    )
    bundle_schema_matched = bool(
        bundle.get("schema_version") == EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SCHEMA_VERSION
    )
    if bundle and not bundle_surface_matched:
        errors.append("real_live_receipt_bundle_surface_mismatch")
    if bundle and not bundle_schema_matched:
        errors.append("real_live_receipt_bundle_schema_mismatch")
    if bundle and bundle.get("target_artifact") != "ChaseOS-Studio.exe":
        errors.append("real_live_receipt_bundle_target_artifact_mismatch")
    if bundle and bundle.get("helper_binary_name") != "ChaseOS-Installer.exe":
        errors.append("real_live_receipt_bundle_helper_binary_mismatch")

    bundle_digest_key = "real_live_receipt_bundle_digest_sha256"
    stored_bundle_digest = str(bundle.get(bundle_digest_key) or "")
    computed_bundle_digest = (
        _extension_digest_without(bundle, bundle_digest_key) if bundle else ""
    )
    bundle_digest_matched = bool(
        stored_bundle_digest and stored_bundle_digest == computed_bundle_digest
    )
    if bundle and not stored_bundle_digest:
        errors.append("real_live_receipt_bundle_digest_required")
    elif bundle and not bundle_digest_matched:
        errors.append("real_live_receipt_bundle_digest_mismatch")

    forbidden_key_paths = _real_live_receipt_capture_forbidden_key_paths(bundle)
    if forbidden_key_paths:
        errors.append("real_live_receipt_bundle_secret_like_keys_rejected")

    for false_flag in (
        "download_performed_by_this_boundary",
        "installer_launch_performed_by_this_boundary",
        "primary_replacement_performed_by_this_boundary",
        "startup_mutation_performed_by_this_boundary",
        "settings_install_control_exposed",
        "secrets_or_private_keys_included",
    ):
        if bool(bundle.get(false_flag)):
            errors.append(f"real_live_receipt_bundle_{false_flag}_must_be_false")

    source_inputs = _real_live_receipt_capture_bundle_source_inputs(bundle)
    digest_closeout = build_launcher_update_live_receipt_digest_consistency_closeout(
        vault,
        **source_inputs,
        generated_at=timestamp,
    )
    if digest_closeout.get("warnings"):
        warnings.extend(str(item) for item in digest_closeout.get("warnings") or [])
    if digest_closeout.get("errors"):
        errors.extend(
            f"receipt_digest_closeout:{item}"
            for item in digest_closeout.get("errors") or []
        )
    if not digest_closeout.get("digest_consistency_closeout_ready"):
        errors.append("real_live_receipt_digest_consistency_not_ready")
    if not digest_closeout.get("source_receipts_ready"):
        errors.append("real_live_source_receipts_not_ready")

    capture_plan = _real_live_receipt_capture_boundary_plan(
        vault=vault,
        timestamp=timestamp,
        receipt_bundle_digest=stored_bundle_digest,
        source_checks=digest_closeout.get("digest_checks") or [],
    )
    required_statement = (
        required_update_real_live_receipt_capture_boundary_operator_statement(
            capture_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_real_live_receipt_capture
        and str(operator_statement) == required_statement
    )
    if not operator_approved_real_live_receipt_capture:
        errors.append("operator_real_live_receipt_capture_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_real_live_receipt_capture_statement_mismatch")

    receipt_bundle_valid = bool(
        bundle
        and bundle_surface_matched
        and bundle_schema_matched
        and bundle_digest_matched
        and not forbidden_key_paths
        and not any(
            str(item).startswith("real_live_receipt_bundle_")
            and str(item).endswith("_must_be_false")
            for item in errors
        )
    )
    source_receipts_ready = bool(digest_closeout.get("source_receipts_ready"))
    capture_ready = bool(
        receipt_bundle_valid
        and source_receipts_ready
        and operator_statement_matched
    )

    dry_run_result = {}
    if capture_ready:
        normalized_source_proofs = digest_closeout.get("normalized_source_proofs") or {}
        dry_run_preview = build_launcher_update_approved_live_evidence_runner_real_dry_run(
            vault,
            **normalized_source_proofs,
            production_primary_closeout_after_source_recovery_proof=production_primary_closeout_after_source_recovery_proof,
            generated_at=timestamp,
        )
        dry_run_statement = (
            required_update_approved_live_evidence_runner_real_dry_run_operator_statement(
                dry_run_preview["dry_run_plan"]
            )
        )
        dry_run_result = build_launcher_update_approved_live_evidence_runner_real_dry_run(
            vault,
            **normalized_source_proofs,
            production_primary_closeout_after_source_recovery_proof=production_primary_closeout_after_source_recovery_proof,
            operator_approved_live_evidence_runner_real_dry_run=True,
            operator_statement=dry_run_statement,
            generated_at=timestamp,
        )
        if dry_run_result.get("warnings"):
            warnings.extend(str(item) for item in dry_run_result.get("warnings") or [])
        if dry_run_result.get("errors"):
            errors.extend(
                f"approved_real_dry_run:{item}"
                for item in dry_run_result.get("errors") or []
            )

    dry_run_packet_ready = bool(
        dry_run_result.get("governed_live_completion_evidence_packet_ready")
    )
    final_audit_ready = bool(
        dry_run_result.get("final_production_auto_update_closeout_audit_ready")
    )
    boundary_ready = bool(capture_ready and dry_run_packet_ready)

    requirement_checks = [
        {
            "id": "real_live_receipt_bundle_valid",
            "passed": receipt_bundle_valid,
            "source": EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SURFACE_ID,
        },
        {
            "id": "receipt_digest_consistency_closeout_ready",
            "passed": bool(digest_closeout.get("digest_consistency_closeout_ready")),
            "source": LIVE_RECEIPT_DIGEST_CONSISTENCY_CLOSEOUT_SURFACE_ID,
        },
        {
            "id": "source_receipts_ready",
            "passed": source_receipts_ready,
            "source": LIVE_RECEIPT_DIGEST_CONSISTENCY_CLOSEOUT_SURFACE_ID,
        },
        {
            "id": "operator_statement_matched",
            "passed": operator_statement_matched,
            "source": "operator",
        },
        {
            "id": "approved_live_evidence_runner_real_dry_run_packet_ready",
            "passed": dry_run_packet_ready,
            "source": APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SURFACE_ID,
        },
    ]
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]

    status = "launcher_update_real_live_receipt_capture_boundary_blocked"
    if receipt_bundle_valid and source_receipts_ready and not operator_statement_matched:
        status = "launcher_update_real_live_receipt_capture_boundary_operator_approval_required"
    if capture_ready and not dry_run_packet_ready:
        status = "launcher_update_real_live_receipt_capture_boundary_dry_run_blocked"
    if boundary_ready:
        status = "launcher_update_real_live_receipt_capture_boundary_packet_ready"
    if boundary_ready and final_audit_ready:
        status = "launcher_update_real_live_receipt_capture_boundary_final_audit_ready"

    proof = {
        "ok": boundary_ready,
        "surface": REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SURFACE_ID,
        "schema_version": REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "receipt_bundle": bundle,
        "receipt_bundle_surface_matched": bundle_surface_matched,
        "receipt_bundle_schema_matched": bundle_schema_matched,
        "receipt_bundle_digest_sha256": stored_bundle_digest,
        "computed_receipt_bundle_digest_sha256": computed_bundle_digest,
        "receipt_bundle_digest_matched": bundle_digest_matched,
        "receipt_bundle_forbidden_key_paths": forbidden_key_paths,
        "receipt_bundle_valid": receipt_bundle_valid,
        "capture_plan": capture_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "operator_approved_real_live_receipt_capture": bool(
            operator_approved_real_live_receipt_capture
        ),
        "receipt_digest_consistency_closeout": digest_closeout,
        "digest_consistency_closeout_ready": bool(
            digest_closeout.get("digest_consistency_closeout_ready")
        ),
        "source_receipts_ready": source_receipts_ready,
        "receipt_readiness_blockers": list(
            digest_closeout.get("receipt_readiness_blockers") or []
        ),
        "source_proof_checks": list(digest_closeout.get("source_proof_checks") or []),
        "approved_live_evidence_runner_real_dry_run": dry_run_result,
        "approved_live_evidence_runner_real_dry_run_ready": bool(
            dry_run_result.get("ok")
        ),
        "governed_live_completion_evidence_packet": (
            dry_run_result.get("governed_live_completion_evidence_packet") or {}
        ),
        "governed_live_completion_evidence_packet_ready": dry_run_packet_ready,
        "final_production_auto_update_closeout_audit": (
            dry_run_result.get("final_production_auto_update_closeout_audit") or {}
        ),
        "final_production_auto_update_closeout_audit_ready": final_audit_ready,
        "feeds_final_production_auto_update_closeout_audit": dry_run_packet_ready,
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": not final_audit_ready,
        "next_required_step": (
            "feed_captured_governed_packet_to_final_closeout_audit"
            if dry_run_packet_ready
            else "supply_real_live_receipt_bundle_for_all_six_source_receipts"
        ),
        "authority": _authority(
            real_live_receipt_capture_boundary_built=True,
            real_live_receipt_capture_boundary_ready=boundary_ready,
            real_live_receipt_capture_boundary_receipt_bundle_valid=receipt_bundle_valid,
            real_live_receipt_capture_boundary_source_receipts_ready=source_receipts_ready,
            real_live_receipt_capture_boundary_dry_run_packet_ready=dry_run_packet_ready,
            real_live_receipt_capture_boundary_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["real_live_receipt_capture_boundary_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "real_live_receipt_capture_boundary_digest_sha256",
        )
    )
    return proof


def _real_live_receipt_bundle_production_runner_action_flags(
    *,
    allow_live_release_readback,
    allow_live_download,
    allow_staged_signature_verification,
    allow_installer_signed_output_verification,
    allow_installer_launch,
    allow_primary_replacement,
    allow_startup_prompt_verification,
):
    return {
        "live_release_readback": bool(allow_live_release_readback),
        "live_download": bool(allow_live_download),
        "staged_signature_verification": bool(allow_staged_signature_verification),
        "installer_signed_output_verification": bool(
            allow_installer_signed_output_verification
        ),
        "installer_launch": bool(allow_installer_launch),
        "primary_replacement": bool(allow_primary_replacement),
        "startup_prompt_verification": bool(allow_startup_prompt_verification),
    }


def _real_live_receipt_bundle_production_runner_plan(
    *,
    vault,
    timestamp,
    runner_label,
    action_flags,
):
    plan = {
        "surface": f"{REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID}_plan",
        "schema_version": REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "runner_label": str(runner_label or ""),
        "target_artifact": "ChaseOS-Studio.exe",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "external_receipt_bundle_surface": EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SURFACE_ID,
        "required_sources": [
            spec["id"] for spec in _approved_live_evidence_runner_adapter_source_specs()
        ],
        "feeds_surface": REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SURFACE_ID,
        "operator_allowed_live_actions": dict(action_flags),
        "secret_values_allowed": False,
        "settings_install_control_exposed": False,
        "github_release_mutation_allowed_by_this_runner": False,
        "source_write_allowed": False,
    }
    plan["real_live_receipt_bundle_production_runner_plan_digest_sha256"] = (
        _extension_digest_without(
            plan,
            "real_live_receipt_bundle_production_runner_plan_digest_sha256",
        )
    )
    return plan


def required_update_real_live_receipt_bundle_production_runner_operator_statement(
    runner_plan,
):
    digest = str(
        (runner_plan or {}).get(
            "real_live_receipt_bundle_production_runner_plan_digest_sha256"
        )
        or _extension_digest_without(
            runner_plan or {},
            "real_live_receipt_bundle_production_runner_plan_digest_sha256",
        )
    )
    return (
        f"{REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def _real_live_receipt_bundle_production_runner_extract_bundle(raw_result):
    if not isinstance(raw_result, dict):
        return {}
    if raw_result.get("surface") == EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SURFACE_ID:
        return raw_result
    bundle = raw_result.get("live_receipt_bundle") or raw_result.get("receipt_bundle")
    return bundle if isinstance(bundle, dict) else {}


def build_launcher_update_real_live_receipt_bundle_production_runner(
    vault_root,
    *,
    receipt_bundle_runner=None,
    runner_label="injected_real_live_receipt_bundle_production_runner",
    production_primary_closeout_after_source_recovery_proof=None,
    operator_approved_real_live_receipt_bundle_runner=False,
    operator_statement="",
    allow_live_release_readback=False,
    allow_live_download=False,
    allow_staged_signature_verification=False,
    allow_installer_signed_output_verification=False,
    allow_installer_launch=False,
    allow_primary_replacement=False,
    allow_startup_prompt_verification=False,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    action_flags = _real_live_receipt_bundle_production_runner_action_flags(
        allow_live_release_readback=allow_live_release_readback,
        allow_live_download=allow_live_download,
        allow_staged_signature_verification=allow_staged_signature_verification,
        allow_installer_signed_output_verification=allow_installer_signed_output_verification,
        allow_installer_launch=allow_installer_launch,
        allow_primary_replacement=allow_primary_replacement,
        allow_startup_prompt_verification=allow_startup_prompt_verification,
    )
    runner_plan = _real_live_receipt_bundle_production_runner_plan(
        vault=vault,
        timestamp=timestamp,
        runner_label=runner_label,
        action_flags=action_flags,
    )
    required_statement = (
        required_update_real_live_receipt_bundle_production_runner_operator_statement(
            runner_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_real_live_receipt_bundle_runner
        and str(operator_statement) == required_statement
    )

    if receipt_bundle_runner is None:
        errors.append("real_live_receipt_bundle_runner_required")
    elif not callable(receipt_bundle_runner):
        errors.append("real_live_receipt_bundle_runner_not_callable")
    if not operator_approved_real_live_receipt_bundle_runner:
        errors.append("operator_real_live_receipt_bundle_runner_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_real_live_receipt_bundle_runner_statement_mismatch")
    for action, allowed in action_flags.items():
        if not allowed:
            errors.append(f"{action}_approval_required")

    runner_execution_allowed = bool(
        callable(receipt_bundle_runner)
        and operator_statement_matched
        and all(action_flags.values())
    )
    runner_execution_performed = False
    raw_runner_result = {}
    if runner_execution_allowed:
        runner_context = {
            "surface": REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID,
            "schema_version": REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SCHEMA_VERSION,
            "generated_at_utc": timestamp,
            "vault_root": str(vault),
            "runner_label": str(runner_label or ""),
            "runner_plan": runner_plan,
            "target_artifact": "ChaseOS-Studio.exe",
            "helper_binary_name": "ChaseOS-Installer.exe",
            "external_receipt_bundle_surface": EXTERNAL_REAL_LIVE_RECEIPT_BUNDLE_SURFACE_ID,
            "operator_allowed_live_actions": dict(action_flags),
            "secret_values_allowed": False,
            "settings_install_control_exposed": False,
        }
        try:
            raw_runner_result = receipt_bundle_runner(runner_context)
            runner_execution_performed = True
        except Exception as exc:
            raw_runner_result = {
                "ok": False,
                "status": "real_live_receipt_bundle_production_runner_failed",
                "error": f"{exc.__class__.__name__}",
            }
            errors.append("real_live_receipt_bundle_production_runner_failed")

    runner_result_valid = False
    runner_result_forbidden_key_paths = []
    live_receipt_bundle = {}
    capture_result = {}
    capture_boundary_ready = False
    if runner_execution_performed:
        if not isinstance(raw_runner_result, dict):
            errors.append("real_live_receipt_bundle_runner_result_malformed")
            raw_runner_result = {}
        runner_result_forbidden_key_paths = _real_live_receipt_capture_forbidden_key_paths(
            raw_runner_result
        )
        if runner_result_forbidden_key_paths:
            errors.append("real_live_receipt_bundle_runner_secret_like_keys_rejected")
        if raw_runner_result.get("ok") is not True:
            errors.append("real_live_receipt_bundle_runner_result_not_ok")
        live_receipt_bundle = _real_live_receipt_bundle_production_runner_extract_bundle(
            raw_runner_result
        )
        if not live_receipt_bundle:
            errors.append("real_live_receipt_bundle_runner_bundle_required")
        runner_result_valid = bool(
            raw_runner_result
            and raw_runner_result.get("ok") is True
            and live_receipt_bundle
            and not runner_result_forbidden_key_paths
        )

    if runner_result_valid:
        capture_preview = build_launcher_update_real_live_receipt_capture_boundary(
            vault,
            live_receipt_bundle=live_receipt_bundle,
            production_primary_closeout_after_source_recovery_proof=production_primary_closeout_after_source_recovery_proof,
            generated_at=timestamp,
        )
        capture_statement = (
            required_update_real_live_receipt_capture_boundary_operator_statement(
                capture_preview["capture_plan"]
            )
        )
        capture_result = build_launcher_update_real_live_receipt_capture_boundary(
            vault,
            live_receipt_bundle=live_receipt_bundle,
            production_primary_closeout_after_source_recovery_proof=production_primary_closeout_after_source_recovery_proof,
            operator_approved_real_live_receipt_capture=True,
            operator_statement=capture_statement,
            generated_at=timestamp,
        )
        if capture_result.get("warnings"):
            warnings.extend(str(item) for item in capture_result.get("warnings") or [])
        if capture_result.get("errors"):
            errors.extend(
                f"capture_boundary:{item}"
                for item in capture_result.get("errors") or []
            )
        capture_boundary_ready = bool(capture_result.get("ok"))

    governed_packet_ready = bool(
        capture_result.get("governed_live_completion_evidence_packet_ready")
    )
    final_audit_ready = bool(
        capture_result.get("final_production_auto_update_closeout_audit_ready")
    )
    runner_ready = bool(
        runner_execution_performed
        and runner_result_valid
        and capture_boundary_ready
        and governed_packet_ready
        and not any(str(item).startswith("capture_boundary:") for item in errors)
    )

    requirement_checks = [
        {
            "id": "injected_runner_present",
            "passed": callable(receipt_bundle_runner),
            "source": "receipt_bundle_runner",
        },
        {
            "id": "operator_statement_matched",
            "passed": operator_statement_matched,
            "source": "operator",
        },
        {
            "id": "all_live_action_approvals_present",
            "passed": all(action_flags.values()),
            "source": "operator",
        },
        {
            "id": "runner_execution_performed",
            "passed": runner_execution_performed,
            "source": "receipt_bundle_runner",
        },
        {
            "id": "runner_result_valid",
            "passed": runner_result_valid,
            "source": "receipt_bundle_runner",
        },
        {
            "id": "capture_boundary_ready",
            "passed": capture_boundary_ready,
            "source": REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SURFACE_ID,
        },
        {
            "id": "governed_live_completion_evidence_packet_ready",
            "passed": governed_packet_ready,
            "source": GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID,
        },
    ]
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]
    status = "launcher_update_real_live_receipt_bundle_production_runner_blocked"
    if callable(receipt_bundle_runner) and all(action_flags.values()) and not operator_statement_matched:
        status = "launcher_update_real_live_receipt_bundle_production_runner_pending_approval"
    if runner_execution_performed and not runner_ready:
        status = "launcher_update_real_live_receipt_bundle_production_runner_capture_blocked"
    if runner_ready:
        status = "launcher_update_real_live_receipt_bundle_production_runner_packet_ready"
    if runner_ready and final_audit_ready:
        status = "launcher_update_real_live_receipt_bundle_production_runner_final_audit_ready"

    proof = {
        "ok": runner_ready,
        "surface": REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID,
        "schema_version": REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "runner_label": str(runner_label or ""),
        "runner_plan": runner_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "operator_approved_real_live_receipt_bundle_runner": bool(
            operator_approved_real_live_receipt_bundle_runner
        ),
        "operator_allowed_live_actions": dict(action_flags),
        "runner_execution_allowed": runner_execution_allowed,
        "runner_execution_performed": runner_execution_performed,
        "runner_result": raw_runner_result,
        "runner_result_valid": runner_result_valid,
        "runner_result_forbidden_key_paths": runner_result_forbidden_key_paths,
        "live_receipt_bundle": live_receipt_bundle,
        "real_live_receipt_capture_boundary": capture_result,
        "capture_boundary_ready": capture_boundary_ready,
        "receipt_bundle_valid": bool(capture_result.get("receipt_bundle_valid")),
        "source_receipts_ready": bool(capture_result.get("source_receipts_ready")),
        "governed_live_completion_evidence_packet": (
            capture_result.get("governed_live_completion_evidence_packet") or {}
        ),
        "governed_live_completion_evidence_packet_ready": governed_packet_ready,
        "final_production_auto_update_closeout_audit": (
            capture_result.get("final_production_auto_update_closeout_audit") or {}
        ),
        "final_production_auto_update_closeout_audit_ready": final_audit_ready,
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "feeds_final_production_auto_update_closeout_audit": governed_packet_ready,
        "download_performed_by_runner": bool(
            raw_runner_result.get("download_performed_by_runner")
        ),
        "installer_launch_performed_by_runner": bool(
            raw_runner_result.get("installer_launch_performed_by_runner")
        ),
        "primary_replacement_performed_by_runner": bool(
            raw_runner_result.get("primary_replacement_performed_by_runner")
        ),
        "primary_relaunch_performed_by_runner": bool(
            raw_runner_result.get("primary_relaunch_performed_by_runner")
        ),
        "startup_prompt_verified_by_runner": bool(
            raw_runner_result.get("startup_prompt_verified_by_runner")
        ),
        "download_performed_by_this_proof": bool(
            raw_runner_result.get("download_performed_by_runner")
        ),
        "installer_launch_performed_by_this_proof": bool(
            raw_runner_result.get("installer_launch_performed_by_runner")
        ),
        "primary_replacement_performed_by_this_proof": bool(
            raw_runner_result.get("primary_replacement_performed_by_runner")
        ),
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "github_mutation_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": not final_audit_ready,
        "next_required_step": (
            "feed_runner_governed_packet_to_final_closeout_audit"
            if governed_packet_ready
            else "approve_and_run_real_live_receipt_bundle_production_runner"
        ),
        "authority": _authority(
            real_live_receipt_bundle_production_runner_built=True,
            real_live_receipt_bundle_production_runner_executed=runner_execution_performed,
            real_live_receipt_bundle_production_runner_capture_boundary_ready=capture_boundary_ready,
            real_live_receipt_bundle_production_runner_packet_ready=governed_packet_ready,
            real_live_receipt_bundle_production_runner_settings_install_control_exposed=False,
            real_live_receipt_bundle_production_runner_primary_replacement_performed_by_runner=bool(
                raw_runner_result.get("primary_replacement_performed_by_runner")
            ),
        ),
        "readiness": _readiness(),
    }
    proof["real_live_receipt_bundle_production_runner_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "real_live_receipt_bundle_production_runner_digest_sha256",
        )
    )
    return proof


def _production_runner_final_closeout_bridge_digest_matched(proof, digest_key):
    digest = str((proof or {}).get(digest_key) or "")
    return bool(
        digest
        and isinstance(proof, dict)
        and digest == _extension_digest_without(proof, digest_key)
    )


def build_launcher_update_production_runner_final_closeout_bridge(
    vault_root,
    *,
    real_live_receipt_bundle_production_runner_proof=None,
    production_primary_closeout_after_source_recovery_proof=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    if real_live_receipt_bundle_production_runner_proof is None:
        real_live_receipt_bundle_production_runner_proof = (
            build_launcher_update_real_live_receipt_bundle_production_runner(
                vault,
                generated_at=timestamp,
            )
        )
        errors.append("real_live_receipt_bundle_production_runner_proof_required")

    runner_proof = _extension_unwrap_api_data(
        real_live_receipt_bundle_production_runner_proof,
        "launcher_update_real_live_receipt_bundle_production_runner",
    )
    runner_proof = _extension_unwrap_api_data(
        runner_proof or {},
        REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID,
    )
    if not isinstance(runner_proof, dict):
        runner_proof = {}
    if runner_proof.get("warnings"):
        warnings.extend(str(item) for item in runner_proof.get("warnings") or [])
    if not runner_proof:
        errors.append("real_live_receipt_bundle_production_runner_proof_malformed")
    elif runner_proof.get("surface") != REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID:
        errors.append("real_live_receipt_bundle_production_runner_surface_mismatch")

    runner_digest_key = "real_live_receipt_bundle_production_runner_digest_sha256"
    runner_digest = str(runner_proof.get(runner_digest_key) or "")
    runner_digest_matched = _production_runner_final_closeout_bridge_digest_matched(
        runner_proof,
        runner_digest_key,
    )
    if runner_proof and not runner_digest_matched:
        errors.append("real_live_receipt_bundle_production_runner_digest_mismatch")

    capture_boundary = runner_proof.get("real_live_receipt_capture_boundary") or {}
    if not isinstance(capture_boundary, dict):
        capture_boundary = {}
        if runner_proof:
            errors.append("real_live_receipt_capture_boundary_malformed")
    capture_digest_key = "real_live_receipt_capture_boundary_digest_sha256"
    capture_digest_matched = _production_runner_final_closeout_bridge_digest_matched(
        capture_boundary,
        capture_digest_key,
    )
    if capture_boundary and not capture_digest_matched:
        errors.append("real_live_receipt_capture_boundary_digest_mismatch")

    governed_packet = runner_proof.get("governed_live_completion_evidence_packet") or {}
    if not isinstance(governed_packet, dict):
        governed_packet = {}
        if runner_proof:
            errors.append("governed_live_completion_evidence_packet_malformed")
    packet_digest_key = "governed_live_completion_evidence_packet_digest_sha256"
    governed_packet_digest_matched = (
        _production_runner_final_closeout_bridge_digest_matched(
            governed_packet,
            packet_digest_key,
        )
    )
    if governed_packet and not governed_packet_digest_matched:
        errors.append("governed_live_completion_evidence_packet_digest_mismatch")
    if governed_packet and not (
        governed_packet.get("ok")
        and governed_packet.get("live_completion_evidence_verified")
    ):
        errors.append("governed_live_completion_evidence_packet_not_ready")

    runner_ready = bool(
        runner_digest_matched
        and runner_proof.get("ok")
        and runner_proof.get("runner_execution_performed")
        and runner_proof.get("runner_result_valid")
        and runner_proof.get("capture_boundary_ready")
        and runner_proof.get("governed_live_completion_evidence_packet_ready")
        and capture_digest_matched
        and governed_packet_digest_matched
        and governed_packet.get("ok")
        and not runner_proof.get("settings_install_control_exposed")
    )
    if runner_proof and not runner_ready:
        errors.append("real_live_receipt_bundle_production_runner_not_ready")
    for flag in (
        "download_performed_by_runner",
        "installer_launch_performed_by_runner",
        "primary_replacement_performed_by_runner",
        "primary_relaunch_performed_by_runner",
        "startup_prompt_verified_by_runner",
    ):
        if runner_proof and not bool(runner_proof.get(flag)):
            errors.append(f"real_live_receipt_bundle_production_runner_{flag}_required")
    for blocked_flag in (
        "settings_install_control_exposed",
        "settings_write_control_exposed",
        "source_write_performed_by_this_proof",
        "github_mutation_performed_by_this_proof",
    ):
        if bool(runner_proof.get(blocked_flag)):
            errors.append(
                f"real_live_receipt_bundle_production_runner_{blocked_flag}_must_be_false"
            )

    if production_primary_closeout_after_source_recovery_proof is None:
        production_primary_closeout_after_source_recovery_proof = (
            build_launcher_update_production_primary_closeout_after_source_recovery_proof(
                vault,
                generated_at=timestamp,
            )
        )
        errors.append("production_primary_closeout_after_source_recovery_proof_required")

    primary_closeout = _extension_unwrap_api_data(
        production_primary_closeout_after_source_recovery_proof,
        "launcher_update_production_primary_closeout_after_source_recovery_proof",
    )
    primary_closeout = _extension_unwrap_api_data(
        primary_closeout or {},
        PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID,
    )
    if not isinstance(primary_closeout, dict):
        primary_closeout = {}
    if primary_closeout.get("warnings"):
        warnings.extend(str(item) for item in primary_closeout.get("warnings") or [])
    if not primary_closeout:
        errors.append("production_primary_closeout_after_source_recovery_malformed")
    elif primary_closeout.get("surface") != PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID:
        errors.append("production_primary_closeout_after_source_recovery_surface_mismatch")

    primary_digest_key = "production_primary_closeout_after_source_recovery_digest_sha256"
    primary_digest = str(primary_closeout.get(primary_digest_key) or "")
    primary_digest_matched = _production_runner_final_closeout_bridge_digest_matched(
        primary_closeout,
        primary_digest_key,
    )
    if primary_closeout and not primary_digest_matched:
        errors.append("production_primary_closeout_after_source_recovery_digest_mismatch")
    primary_closeout_ready = bool(
        primary_digest_matched
        and primary_closeout.get("ok")
        and primary_closeout.get(
            "production_primary_closeout_after_source_recovery_ready_for_final_audit"
        )
        and primary_closeout.get("source_closeout_ready")
        and primary_closeout.get("primary_relaunch_receipt_boundary_ready")
    )
    if primary_closeout and not primary_closeout_ready:
        errors.append("production_primary_closeout_after_source_recovery_not_ready")

    final_audit = {}
    if runner_ready and primary_closeout_ready:
        final_audit = build_launcher_update_final_production_auto_update_closeout_audit(
            vault,
            production_primary_closeout_after_source_recovery_proof=primary_closeout,
            live_completion_evidence=governed_packet,
            generated_at=timestamp,
        )
        if final_audit.get("warnings"):
            warnings.extend(str(item) for item in final_audit.get("warnings") or [])
        if final_audit.get("errors"):
            errors.extend(f"final_audit:{item}" for item in final_audit.get("errors") or [])

    final_audit_ready = bool(
        final_audit.get("ok") and final_audit.get("production_auto_update_complete")
    )
    requirement_checks = [
        {
            "id": "production_runner_proof_ready",
            "passed": runner_ready,
            "source": REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID,
        },
        {
            "id": "production_runner_digest_matched",
            "passed": runner_digest_matched,
            "source": REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID,
        },
        {
            "id": "capture_boundary_digest_matched",
            "passed": capture_digest_matched,
            "source": REAL_LIVE_RECEIPT_CAPTURE_BOUNDARY_SURFACE_ID,
        },
        {
            "id": "governed_packet_digest_matched",
            "passed": governed_packet_digest_matched,
            "source": GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID,
        },
        {
            "id": "primary_closeout_ready",
            "passed": primary_closeout_ready,
            "source": PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID,
        },
        {
            "id": "primary_closeout_digest_matched",
            "passed": primary_digest_matched,
            "source": PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID,
        },
        {
            "id": "final_closeout_audit_ready",
            "passed": final_audit_ready,
            "source": FINAL_PRODUCTION_AUTO_UPDATE_CLOSEOUT_AUDIT_SURFACE_ID,
        },
    ]
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]

    status = "launcher_update_production_runner_final_closeout_bridge_blocked"
    if runner_ready and not primary_closeout_ready:
        status = (
            "launcher_update_production_runner_final_closeout_bridge_"
            "primary_closeout_required"
        )
    if primary_closeout_ready and not runner_ready:
        status = (
            "launcher_update_production_runner_final_closeout_bridge_"
            "production_runner_required"
        )
    if runner_ready and primary_closeout_ready and not final_audit_ready:
        status = (
            "launcher_update_production_runner_final_closeout_bridge_"
            "final_audit_blocked"
        )
    if final_audit_ready:
        status = (
            "launcher_update_production_runner_final_closeout_bridge_verified_complete"
        )

    proof = {
        "ok": final_audit_ready,
        "surface": PRODUCTION_RUNNER_FINAL_CLOSEOUT_BRIDGE_SURFACE_ID,
        "schema_version": PRODUCTION_RUNNER_FINAL_CLOSEOUT_BRIDGE_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "runner_proof_status": runner_proof.get("status", ""),
        "runner_proof_digest_sha256": runner_digest,
        "runner_proof_digest_matched": runner_digest_matched,
        "runner_proof_ready": runner_ready,
        "runner_execution_previously_performed": bool(
            runner_proof.get("runner_execution_performed")
        ),
        "capture_boundary_digest_matched": capture_digest_matched,
        "governed_live_completion_evidence_packet_digest_matched": (
            governed_packet_digest_matched
        ),
        "governed_live_completion_evidence_packet_ready": bool(
            runner_proof.get("governed_live_completion_evidence_packet_ready")
        ),
        "primary_closeout_status": primary_closeout.get("status", ""),
        "primary_closeout_digest_sha256": primary_digest,
        "primary_closeout_digest_matched": primary_digest_matched,
        "primary_closeout_ready": primary_closeout_ready,
        "final_production_auto_update_closeout_audit": final_audit,
        "final_production_auto_update_closeout_audit_ready": final_audit_ready,
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "real_live_receipt_bundle_production_runner_proof": runner_proof,
        "production_primary_closeout_after_source_recovery_proof": primary_closeout,
        "governed_live_completion_evidence_packet": governed_packet,
        "download_previously_verified_by_runner": bool(
            runner_proof.get("download_performed_by_runner")
        ),
        "installer_launch_previously_verified_by_runner": bool(
            runner_proof.get("installer_launch_performed_by_runner")
        ),
        "primary_replacement_previously_verified_by_runner": bool(
            runner_proof.get("primary_replacement_performed_by_runner")
        ),
        "primary_relaunch_previously_verified_by_runner": bool(
            runner_proof.get("primary_relaunch_performed_by_runner")
        ),
        "startup_prompt_previously_verified_by_runner": bool(
            runner_proof.get("startup_prompt_verified_by_runner")
        ),
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "github_mutation_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": final_audit_ready,
        "final_auto_update_closeout_blocked": not final_audit_ready,
        "next_required_step": (
            "production_auto_update_complete"
            if final_audit_ready
            else (
                "supply_ready_primary_closeout_after_source_recovery"
                if runner_ready
                else "supply_ready_real_live_receipt_bundle_production_runner_proof"
            )
        ),
        "authority": _authority(
            production_runner_final_closeout_bridge_built=True,
            production_runner_final_closeout_bridge_runner_ready=runner_ready,
            production_runner_final_closeout_bridge_primary_closeout_ready=primary_closeout_ready,
            production_runner_final_closeout_bridge_final_audit_ready=final_audit_ready,
            production_runner_final_closeout_bridge_production_auto_update_complete=final_audit_ready,
            production_runner_final_closeout_bridge_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["production_runner_final_closeout_bridge_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "production_runner_final_closeout_bridge_digest_sha256",
        )
    )
    return proof


def _approved_production_runner_real_evidence_capture_default_root(vault):
    return (
        _Path(vault)
        / ".chaseos"
        / "updates"
        / "real-evidence"
        / "approved-production-runner"
    )


def _approved_production_runner_real_evidence_capture_plan(
    *,
    vault,
    timestamp,
    evidence_root,
    evidence_root_supplied,
    runner_proof_filename,
    primary_closeout_filename,
):
    root = _Path(evidence_root)
    runner_path = root / str(runner_proof_filename or "")
    primary_path = root / str(primary_closeout_filename or "")
    plan = {
        "surface": (
            f"{APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_SURFACE_ID}_plan"
        ),
        "schema_version": (
            APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_SCHEMA_VERSION
        ),
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "target_artifact": "ChaseOS-Studio.exe",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "evidence_root": str(root),
        "evidence_root_supplied": bool(evidence_root_supplied),
        "runner_proof_filename": str(runner_proof_filename or ""),
        "primary_closeout_filename": str(primary_closeout_filename or ""),
        "runner_proof_path": str(runner_path),
        "primary_closeout_path": str(primary_path),
        "required_evidence_surfaces": [
            REAL_LIVE_RECEIPT_BUNDLE_PRODUCTION_RUNNER_SURFACE_ID,
            PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID,
        ],
        "feeds_surface": PRODUCTION_RUNNER_FINAL_CLOSEOUT_BRIDGE_SURFACE_ID,
        "reads_json_files_only": True,
        "requires_explicit_file_read_flag": True,
        "secret_values_allowed": False,
        "runner_execution_allowed_by_this_capture": False,
        "download_allowed_by_this_capture": False,
        "installer_launch_allowed_by_this_capture": False,
        "primary_replacement_allowed_by_this_capture": False,
        "settings_install_control_exposed": False,
    }
    plan[
        "approved_production_runner_real_evidence_capture_plan_digest_sha256"
    ] = _extension_digest_without(
        plan,
        "approved_production_runner_real_evidence_capture_plan_digest_sha256",
    )
    return plan


def required_update_approved_production_runner_real_evidence_capture_operator_statement(
    capture_plan,
):
    digest = str(
        (capture_plan or {}).get(
            "approved_production_runner_real_evidence_capture_plan_digest_sha256"
        )
        or _extension_digest_without(
            capture_plan or {},
            "approved_production_runner_real_evidence_capture_plan_digest_sha256",
        )
    )
    return (
        f"{APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def _approved_production_runner_real_evidence_capture_filename_valid(filename):
    if not filename:
        return False
    text = str(filename)
    return (
        text == _Path(text).name
        and text.lower().endswith(".json")
        and "/" not in text
        and "\\" not in text
    )


def _approved_production_runner_real_evidence_capture_forbidden_key_paths(
    value,
    prefix="",
):
    allowed_false_safety_keys = {
        "secret_values_allowed",
        "secrets_or_private_keys_included",
        "secrets_or_private_keys_read_by_chaseos",
    }
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in allowed_false_safety_keys:
                if child is not False:
                    paths.append(child_path)
                continue
            normalized_key = key_text.lower().replace("-", "_")
            structural_token_key = any(
                token in normalized_key
                for token in (
                    "wrapper_token",
                    "required_token",
                    "missing_required_token",
                    "token_requirements",
                )
            )
            secret_like_key = any(
                token in normalized_key
                for token in (
                    "secret",
                    "password",
                    "credential",
                    "api_key",
                    "private_key",
                    "seed_phrase",
                    "mnemonic",
                )
            ) or normalized_key in {
                "token",
                "access_token",
                "refresh_token",
                "auth_token",
                "bearer_token",
                "github_token",
            } or normalized_key.endswith("_token")
            if secret_like_key and not structural_token_key:
                if isinstance(child, bool) or child is None:
                    continue
                paths.append(child_path)
            paths.extend(
                _approved_production_runner_real_evidence_capture_forbidden_key_paths(
                    child,
                    child_path,
                )
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            paths.extend(
                _approved_production_runner_real_evidence_capture_forbidden_key_paths(
                    child,
                    child_path,
                )
            )
    return paths


def _approved_production_runner_real_evidence_capture_read_json(path, vault):
    descriptor = {
        "path": str(path),
        "exists": False,
        "is_file": False,
        "inside_vault_root": False,
        "suffix_allowed": False,
        "size_bytes": 0,
        "size_limit_bytes": 16 * 1024 * 1024,
        "sha256": "",
        "json_read": False,
        "json_object": False,
        "forbidden_key_paths": [],
    }
    errors = []
    payload = {}
    try:
        candidate = _Path(path).resolve()
        descriptor["path"] = str(candidate)
        descriptor["exists"] = candidate.exists()
        descriptor["inside_vault_root"] = _extension_path_is_relative_to(
            candidate,
            vault,
        )
        descriptor["suffix_allowed"] = candidate.suffix.lower() == ".json"
        if not descriptor["exists"]:
            errors.append("evidence_file_missing")
            return payload, descriptor, errors
        descriptor["is_file"] = candidate.is_file()
        if not descriptor["is_file"]:
            errors.append("evidence_path_not_file")
            return payload, descriptor, errors
        if not descriptor["inside_vault_root"]:
            errors.append("evidence_file_outside_vault_root")
            return payload, descriptor, errors
        if not descriptor["suffix_allowed"]:
            errors.append("evidence_file_extension_not_json")
            return payload, descriptor, errors
        descriptor["size_bytes"] = candidate.stat().st_size
        if descriptor["size_bytes"] > descriptor["size_limit_bytes"]:
            errors.append("evidence_file_too_large")
            return payload, descriptor, errors
        raw = candidate.read_bytes()
        descriptor["sha256"] = _wrapper_hashlib.sha256(raw).hexdigest()
        try:
            parsed = _extension_json.loads(raw.decode("utf-8"))
        except Exception:
            errors.append("evidence_file_json_malformed")
            return payload, descriptor, errors
        descriptor["json_read"] = True
        descriptor["json_object"] = isinstance(parsed, dict)
        if not descriptor["json_object"]:
            errors.append("evidence_file_json_object_required")
            return payload, descriptor, errors
        descriptor["forbidden_key_paths"] = (
            _approved_production_runner_real_evidence_capture_forbidden_key_paths(
                parsed
            )
        )
        if descriptor["forbidden_key_paths"]:
            errors.append("evidence_file_secret_like_keys_rejected")
            errors.append(
                "evidence_file_secret_like_key_paths:"
                + ",".join(str(item) for item in descriptor["forbidden_key_paths"][:10])
            )
            return payload, descriptor, errors
        payload = parsed
        return payload, descriptor, errors
    except OSError:
        errors.append("evidence_file_read_failed")
        return payload, descriptor, errors


def build_launcher_update_approved_production_runner_real_evidence_capture(
    vault_root,
    *,
    evidence_root=None,
    runner_proof_filename="real-live-receipt-bundle-production-runner.json",
    primary_closeout_filename="production-primary-closeout-after-source-recovery.json",
    operator_approved_real_evidence_capture=False,
    operator_statement="",
    allow_evidence_file_read=False,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    evidence_root_supplied = evidence_root is not None
    root = (
        _Path(evidence_root).resolve()
        if evidence_root_supplied
        else _approved_production_runner_real_evidence_capture_default_root(vault)
    )
    root_inside_vault = _extension_path_is_relative_to(root, vault)
    runner_filename_valid = (
        _approved_production_runner_real_evidence_capture_filename_valid(
            runner_proof_filename
        )
    )
    primary_filename_valid = (
        _approved_production_runner_real_evidence_capture_filename_valid(
            primary_closeout_filename
        )
    )
    capture_plan = _approved_production_runner_real_evidence_capture_plan(
        vault=vault,
        timestamp=timestamp,
        evidence_root=root,
        evidence_root_supplied=evidence_root_supplied,
        runner_proof_filename=runner_proof_filename,
        primary_closeout_filename=primary_closeout_filename,
    )
    required_statement = (
        required_update_approved_production_runner_real_evidence_capture_operator_statement(
            capture_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_real_evidence_capture
        and str(operator_statement) == required_statement
    )

    if not evidence_root_supplied:
        errors.append("approved_production_runner_real_evidence_root_required")
    if evidence_root_supplied and not root_inside_vault:
        errors.append("approved_production_runner_real_evidence_root_outside_vault")
    if not runner_filename_valid:
        errors.append("approved_production_runner_runner_proof_filename_invalid")
    if not primary_filename_valid:
        errors.append("approved_production_runner_primary_closeout_filename_invalid")
    if not allow_evidence_file_read:
        errors.append("approved_production_runner_evidence_file_read_flag_required")
    if not operator_approved_real_evidence_capture:
        errors.append("operator_real_evidence_capture_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_real_evidence_capture_statement_mismatch")

    read_allowed = bool(
        evidence_root_supplied
        and root_inside_vault
        and runner_filename_valid
        and primary_filename_valid
        and allow_evidence_file_read
        and operator_statement_matched
    )
    runner_path = root / str(runner_proof_filename or "")
    primary_path = root / str(primary_closeout_filename or "")
    runner_payload = {}
    primary_payload = {}
    runner_descriptor = {
        "path": str(runner_path),
        "json_read": False,
        "json_object": False,
        "forbidden_key_paths": [],
    }
    primary_descriptor = {
        "path": str(primary_path),
        "json_read": False,
        "json_object": False,
        "forbidden_key_paths": [],
    }
    if read_allowed:
        runner_payload, runner_descriptor, runner_errors = (
            _approved_production_runner_real_evidence_capture_read_json(
                runner_path,
                vault,
            )
        )
        errors.extend(f"runner_evidence:{item}" for item in runner_errors)
        primary_payload, primary_descriptor, primary_errors = (
            _approved_production_runner_real_evidence_capture_read_json(
                primary_path,
                vault,
            )
        )
        errors.extend(f"primary_closeout_evidence:{item}" for item in primary_errors)

    bridge_result = {}
    bridge_ready = False
    if (
        runner_descriptor.get("json_object")
        and primary_descriptor.get("json_object")
        and not runner_descriptor.get("forbidden_key_paths")
        and not primary_descriptor.get("forbidden_key_paths")
    ):
        bridge_result = build_launcher_update_production_runner_final_closeout_bridge(
            vault,
            real_live_receipt_bundle_production_runner_proof=runner_payload,
            production_primary_closeout_after_source_recovery_proof=primary_payload,
            generated_at=timestamp,
        )
        if bridge_result.get("warnings"):
            warnings.extend(str(item) for item in bridge_result.get("warnings") or [])
        if bridge_result.get("errors"):
            errors.extend(f"final_closeout_bridge:{item}" for item in bridge_result.get("errors") or [])
        bridge_ready = bool(
            bridge_result.get("ok")
            and bridge_result.get("production_auto_update_complete")
        )

    files_read = bool(
        runner_descriptor.get("json_read") and primary_descriptor.get("json_read")
    )
    requirement_checks = [
        {
            "id": "evidence_root_supplied",
            "passed": evidence_root_supplied,
            "source": "operator",
        },
        {
            "id": "evidence_root_inside_vault",
            "passed": root_inside_vault,
            "source": "path_scope",
        },
        {
            "id": "operator_statement_matched",
            "passed": operator_statement_matched,
            "source": "operator",
        },
        {
            "id": "evidence_file_read_flag_present",
            "passed": bool(allow_evidence_file_read),
            "source": "operator",
        },
        {
            "id": "runner_evidence_file_read",
            "passed": bool(runner_descriptor.get("json_read")),
            "source": str(runner_path),
        },
        {
            "id": "runner_evidence_json_object",
            "passed": bool(runner_descriptor.get("json_object")),
            "source": str(runner_path),
        },
        {
            "id": "runner_evidence_secret_scan_clear",
            "passed": not bool(runner_descriptor.get("forbidden_key_paths")),
            "source": str(runner_path),
        },
        {
            "id": "primary_closeout_evidence_file_read",
            "passed": bool(primary_descriptor.get("json_read")),
            "source": str(primary_path),
        },
        {
            "id": "primary_closeout_evidence_json_object",
            "passed": bool(primary_descriptor.get("json_object")),
            "source": str(primary_path),
        },
        {
            "id": "primary_closeout_evidence_secret_scan_clear",
            "passed": not bool(primary_descriptor.get("forbidden_key_paths")),
            "source": str(primary_path),
        },
        {
            "id": "production_runner_final_closeout_bridge_ready",
            "passed": bridge_ready,
            "source": PRODUCTION_RUNNER_FINAL_CLOSEOUT_BRIDGE_SURFACE_ID,
        },
    ]
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]
    status = "launcher_update_approved_production_runner_real_evidence_capture_blocked"
    if (
        evidence_root_supplied
        and root_inside_vault
        and allow_evidence_file_read
        and not operator_statement_matched
    ):
        status = (
            "launcher_update_approved_production_runner_real_evidence_capture_"
            "pending_approval"
        )
    if files_read and not bridge_ready:
        status = (
            "launcher_update_approved_production_runner_real_evidence_capture_"
            "bridge_blocked"
        )
    if bridge_ready:
        status = (
            "launcher_update_approved_production_runner_real_evidence_capture_"
            "verified_complete"
        )

    proof = {
        "ok": bridge_ready,
        "surface": APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_SURFACE_ID,
        "schema_version": (
            APPROVED_PRODUCTION_RUNNER_REAL_EVIDENCE_CAPTURE_SCHEMA_VERSION
        ),
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "capture_plan": capture_plan,
        "required_operator_statement": required_statement,
        "operator_approved_real_evidence_capture": bool(
            operator_approved_real_evidence_capture
        ),
        "operator_statement_matched": operator_statement_matched,
        "allow_evidence_file_read": bool(allow_evidence_file_read),
        "evidence_root": str(root),
        "evidence_root_supplied": evidence_root_supplied,
        "evidence_root_inside_vault": root_inside_vault,
        "runner_proof_filename": str(runner_proof_filename or ""),
        "primary_closeout_filename": str(primary_closeout_filename or ""),
        "runner_evidence_descriptor": runner_descriptor,
        "primary_closeout_evidence_descriptor": primary_descriptor,
        "evidence_file_read_performed": files_read,
        "runner_evidence_file_read": bool(runner_descriptor.get("json_read")),
        "primary_closeout_evidence_file_read": bool(
            primary_descriptor.get("json_read")
        ),
        "real_live_receipt_bundle_production_runner_proof": runner_payload,
        "production_primary_closeout_after_source_recovery_proof": primary_payload,
        "production_runner_final_closeout_bridge": bridge_result,
        "production_runner_final_closeout_bridge_ready": bridge_ready,
        "feeds_final_production_auto_update_closeout_audit": bridge_ready,
        "final_production_auto_update_closeout_audit": (
            bridge_result.get("final_production_auto_update_closeout_audit") or {}
        ),
        "final_production_auto_update_closeout_audit_ready": bool(
            bridge_result.get("final_production_auto_update_closeout_audit_ready")
        ),
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "runner_execution_performed_by_this_proof": False,
        "runner_execution_previously_performed": bool(
            bridge_result.get("runner_execution_previously_performed")
        ),
        "download_previously_verified_by_runner": bool(
            bridge_result.get("download_previously_verified_by_runner")
        ),
        "installer_launch_previously_verified_by_runner": bool(
            bridge_result.get("installer_launch_previously_verified_by_runner")
        ),
        "primary_replacement_previously_verified_by_runner": bool(
            bridge_result.get("primary_replacement_previously_verified_by_runner")
        ),
        "primary_relaunch_previously_verified_by_runner": bool(
            bridge_result.get("primary_relaunch_previously_verified_by_runner")
        ),
        "startup_prompt_previously_verified_by_runner": bool(
            bridge_result.get("startup_prompt_previously_verified_by_runner")
        ),
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "github_mutation_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": bridge_ready,
        "final_auto_update_closeout_blocked": not bridge_ready,
        "next_required_step": (
            "production_auto_update_complete_from_captured_real_evidence"
            if bridge_ready
            else (
                "supply_in_vault_real_evidence_root"
                if not evidence_root_supplied
                else "supply_ready_runner_and_primary_closeout_evidence_files"
            )
        ),
        "authority": _authority(
            approved_production_runner_real_evidence_capture_built=True,
            approved_production_runner_real_evidence_capture_files_read=files_read,
            approved_production_runner_real_evidence_capture_bridge_ready=bridge_ready,
            approved_production_runner_real_evidence_capture_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof[
        "approved_production_runner_real_evidence_capture_digest_sha256"
    ] = _extension_digest_without(
        proof,
        "approved_production_runner_real_evidence_capture_digest_sha256",
    )
    return proof


def build_launcher_update_installer_real_artifact_build_output_capture(
    vault_root,
    *,
    installer_path=None,
    studio_path=None,
    build_script_path=None,
    signature_probe=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    dist_root = vault / "dist" / "studio"
    installer = (
        _Path(installer_path).resolve()
        if installer_path is not None
        else dist_root / "ChaseOS-Installer.exe"
    )
    studio = (
        _Path(studio_path).resolve()
        if studio_path is not None
        else dist_root / "ChaseOS-Studio.exe"
    )
    build_script = (
        _Path(build_script_path).resolve()
        if build_script_path is not None
        else vault / "runtime" / "studio" / "shell" / "build_installer.ps1"
    )

    errors = []
    warnings = []
    installer_inside_vault = _extension_path_is_relative_to(installer, vault)
    studio_inside_vault = _extension_path_is_relative_to(studio, vault)
    build_script_inside_vault = _extension_path_is_relative_to(build_script, vault)
    installer_exact_name = installer.name == "ChaseOS-Installer.exe"
    studio_exact_name = studio.name == "ChaseOS-Studio.exe"
    build_script_exact_name = build_script.name == "build_installer.ps1"

    if not installer_inside_vault:
        errors.append("installer_artifact_path_outside_vault")
    if not studio_inside_vault:
        errors.append("studio_artifact_path_outside_vault")
    if not build_script_inside_vault:
        errors.append("build_script_path_outside_vault")
    if not installer_exact_name:
        errors.append("installer_artifact_exact_name_required")
    if not studio_exact_name:
        errors.append("studio_artifact_exact_name_required")
    if not build_script_exact_name:
        errors.append("build_script_exact_name_required")

    installer_descriptor = {
        "path": str(installer),
        "present": False,
        "filename": installer.name,
        "exact_name": installer_exact_name,
        "inside_vault": installer_inside_vault,
        "size_bytes": 0,
        "sha256": "",
    }
    try:
        if installer_inside_vault and installer.is_file():
            installer_bytes = installer.read_bytes()
            installer_descriptor.update(
                {
                    "present": True,
                    "size_bytes": len(installer_bytes),
                    "sha256": _wrapper_hashlib.sha256(
                        installer_bytes
                    ).hexdigest(),
                }
            )
        else:
            errors.append("installer_artifact_missing")
    except OSError:
        errors.append("installer_artifact_read_failed")

    studio_descriptor = {
        "path": str(studio),
        "present": False,
        "filename": studio.name,
        "exact_name": studio_exact_name,
        "inside_vault": studio_inside_vault,
        "sha256": "",
    }
    try:
        if studio_inside_vault and studio.is_file():
            studio_bytes = studio.read_bytes()
            studio_descriptor.update(
                {
                    "present": True,
                    "sha256": _wrapper_hashlib.sha256(studio_bytes).hexdigest(),
                }
            )
        else:
            warnings.append("studio_artifact_missing_for_hash_guard_readback")
    except OSError:
        errors.append("studio_artifact_read_failed")

    build_script_required_tokens = [
        "InstallerDistPath",
        "InstallerBuildOutput",
        "ExpectedOutput",
        "StudioPath",
        "StudioHashBefore",
        "StudioHashAfter",
        "Get-FileHash",
        "Copy-Item",
        "--distpath $InstallerDistPath",
        "ChaseOS-Installer.exe",
        "ChaseOS-Studio.exe",
    ]
    build_script_text = ""
    build_script_descriptor = {
        "path": str(build_script),
        "present": False,
        "filename": build_script.name,
        "exact_name": build_script_exact_name,
        "inside_vault": build_script_inside_vault,
        "required_tokens": build_script_required_tokens,
        "missing_tokens": list(build_script_required_tokens),
        "studio_hash_guard_ready": False,
        "isolated_installer_dist_ready": False,
        "copies_only_installer_output": False,
    }
    try:
        if build_script_inside_vault and build_script.is_file():
            build_script_text = build_script.read_text(encoding="utf-8")
            missing_tokens = [
                token
                for token in build_script_required_tokens
                if token not in build_script_text
            ]
            build_script_descriptor.update(
                {
                    "present": True,
                    "missing_tokens": missing_tokens,
                    "studio_hash_guard_ready": (
                        "StudioHashBefore" in build_script_text
                        and "StudioHashAfter" in build_script_text
                        and "Get-FileHash" in build_script_text
                    ),
                    "isolated_installer_dist_ready": (
                        "InstallerDistPath" in build_script_text
                        and "--distpath $InstallerDistPath" in build_script_text
                    ),
                    "copies_only_installer_output": (
                        "Copy-Item" in build_script_text
                        and "InstallerBuildOutput" in build_script_text
                        and "ExpectedOutput" in build_script_text
                    ),
                }
            )
            if missing_tokens:
                errors.append("build_script_missing_required_hardening_tokens")
        else:
            errors.append("build_script_missing")
    except OSError:
        errors.append("build_script_read_failed")

    signature_probe_performed = callable(signature_probe)
    signature_probe_result = {}
    signature_probe_forbidden_key_paths = []
    installer_signed_output_verified = False
    if signature_probe_performed:
        try:
            probe_result = signature_probe(str(installer))
            if isinstance(probe_result, dict):
                signature_probe_result = probe_result
                signature_probe_forbidden_key_paths = (
                    _approved_production_runner_real_evidence_capture_forbidden_key_paths(
                        probe_result
                    )
                )
                if signature_probe_forbidden_key_paths:
                    errors.append("signature_probe_secret_like_keys_rejected")
                probe_status = str(probe_result.get("status", "")).lower()
                installer_signed_output_verified = bool(
                    not signature_probe_forbidden_key_paths
                    and installer_descriptor.get("present")
                    and (
                        probe_result.get("verified") is True
                        or probe_result.get("valid") is True
                        or probe_status in {"valid", "verified", "signed_valid"}
                    )
                )
            else:
                errors.append("signature_probe_result_object_required")
        except Exception:
            errors.append("signature_probe_failed")

    build_script_hardening_ready = bool(
        build_script_descriptor.get("present")
        and not build_script_descriptor.get("missing_tokens")
        and build_script_descriptor.get("studio_hash_guard_ready")
        and build_script_descriptor.get("isolated_installer_dist_ready")
        and build_script_descriptor.get("copies_only_installer_output")
    )
    artifact_capture_ready = bool(
        installer_descriptor.get("present")
        and installer_inside_vault
        and installer_exact_name
        and build_script_hardening_ready
        and not errors
    )
    status = "launcher_update_installer_real_artifact_build_output_capture_blocked"
    if artifact_capture_ready and installer_signed_output_verified:
        status = (
            "launcher_update_installer_real_artifact_build_output_capture_"
            "signed_output_verified"
        )
    elif artifact_capture_ready:
        status = (
            "launcher_update_installer_real_artifact_build_output_capture_"
            "captured_unsigned"
        )

    proof = {
        "ok": artifact_capture_ready,
        "surface": INSTALLER_REAL_ARTIFACT_BUILD_OUTPUT_CAPTURE_SURFACE_ID,
        "schema_version": (
            INSTALLER_REAL_ARTIFACT_BUILD_OUTPUT_CAPTURE_SCHEMA_VERSION
        ),
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "installer_artifact_descriptor": installer_descriptor,
        "studio_artifact_descriptor": studio_descriptor,
        "build_script_descriptor": build_script_descriptor,
        "installer_path": str(installer),
        "studio_path": str(studio),
        "build_script_path": str(build_script),
        "installer_artifact_present": bool(installer_descriptor.get("present")),
        "studio_artifact_present": bool(studio_descriptor.get("present")),
        "build_script_present": bool(build_script_descriptor.get("present")),
        "installer_artifact_exact_name": installer_exact_name,
        "studio_artifact_exact_name": studio_exact_name,
        "build_script_exact_name": build_script_exact_name,
        "installer_artifact_inside_vault": installer_inside_vault,
        "studio_artifact_inside_vault": studio_inside_vault,
        "build_script_inside_vault": build_script_inside_vault,
        "installer_artifact_size_bytes": installer_descriptor.get("size_bytes", 0),
        "installer_artifact_sha256": installer_descriptor.get("sha256", ""),
        "studio_artifact_sha256": studio_descriptor.get("sha256", ""),
        "build_script_hardening_ready": build_script_hardening_ready,
        "build_script_studio_hash_guard_ready": bool(
            build_script_descriptor.get("studio_hash_guard_ready")
        ),
        "build_script_isolated_installer_dist_ready": bool(
            build_script_descriptor.get("isolated_installer_dist_ready")
        ),
        "build_script_copies_only_installer_output": bool(
            build_script_descriptor.get("copies_only_installer_output")
        ),
        "signature_probe_performed": signature_probe_performed,
        "signature_probe_result": signature_probe_result,
        "signature_probe_forbidden_key_paths": signature_probe_forbidden_key_paths,
        "signing_required": True,
        "installer_signed_output_verified": installer_signed_output_verified,
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "github_mutation_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "sign_chaseos_installer_and_verify_authenticode"
            if artifact_capture_ready and not installer_signed_output_verified
            else (
                "capture_signed_release_manifest_live_readback"
                if installer_signed_output_verified
                else "build_dist_chaseos_installer_with_hardened_script"
            )
        ),
        "authority": _authority(
            installer_real_artifact_build_output_capture_built=True,
            installer_real_artifact_build_output_capture_reads_dist_installer_artifact=True,
            installer_real_artifact_build_output_capture_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof[
        "installer_real_artifact_build_output_capture_digest_sha256"
    ] = _extension_digest_without(
        proof,
        "installer_real_artifact_build_output_capture_digest_sha256",
    )
    return proof


def build_launcher_update_dist_artifact_isolation_cohabitation_proof(
    vault_root,
    *,
    studio_path=None,
    installer_path=None,
    studio_build_script_path=None,
    installer_build_script_path=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    dist_root = vault / "dist" / "studio"
    studio = (
        _Path(studio_path).resolve()
        if studio_path is not None
        else dist_root / "ChaseOS-Studio.exe"
    )
    installer = (
        _Path(installer_path).resolve()
        if installer_path is not None
        else dist_root / "ChaseOS-Installer.exe"
    )
    studio_script = (
        _Path(studio_build_script_path).resolve()
        if studio_build_script_path is not None
        else vault / "runtime" / "studio" / "shell" / "build_exe.ps1"
    )
    installer_script = (
        _Path(installer_build_script_path).resolve()
        if installer_build_script_path is not None
        else vault / "runtime" / "studio" / "shell" / "build_installer.ps1"
    )
    errors = []
    warnings = []

    def artifact_descriptor(path, expected_name, missing_error):
        inside_vault = _extension_path_is_relative_to(path, vault)
        exact_name = path.name == expected_name
        descriptor = {
            "path": str(path),
            "present": False,
            "filename": path.name,
            "expected_filename": expected_name,
            "exact_name": exact_name,
            "inside_vault": inside_vault,
            "size_bytes": 0,
            "sha256": "",
        }
        if not inside_vault:
            errors.append(f"{expected_name}:path_outside_vault")
        if not exact_name:
            errors.append(f"{expected_name}:exact_name_required")
        try:
            if inside_vault and path.is_file():
                raw = path.read_bytes()
                descriptor.update(
                    {
                        "present": True,
                        "size_bytes": len(raw),
                        "sha256": _wrapper_hashlib.sha256(raw).hexdigest(),
                    }
                )
            else:
                errors.append(missing_error)
        except OSError:
            errors.append(f"{expected_name}:read_failed")
        return descriptor

    def script_descriptor(path, expected_name, required_tokens, isolated_token):
        inside_vault = _extension_path_is_relative_to(path, vault)
        exact_name = path.name == expected_name
        descriptor = {
            "path": str(path),
            "present": False,
            "filename": path.name,
            "expected_filename": expected_name,
            "exact_name": exact_name,
            "inside_vault": inside_vault,
            "required_tokens": list(required_tokens),
            "missing_tokens": list(required_tokens),
            "isolated_dist_ready": False,
            "copy_only_expected_output_ready": False,
            "cross_artifact_hash_guard_ready": False,
        }
        if not inside_vault:
            errors.append(f"{expected_name}:path_outside_vault")
        if not exact_name:
            errors.append(f"{expected_name}:exact_name_required")
        try:
            if inside_vault and path.is_file():
                text = path.read_text(encoding="utf-8")
                missing = [token for token in required_tokens if token not in text]
                descriptor.update(
                    {
                        "present": True,
                        "missing_tokens": missing,
                        "isolated_dist_ready": (
                            "DistPath" in text
                            and "--distpath" in text
                            and isolated_token in text
                        ),
                        "copy_only_expected_output_ready": (
                            "Copy-Item" in text and "ExpectedOutput" in text
                        ),
                        "cross_artifact_hash_guard_ready": (
                            "HashBefore" in text and "HashAfter" in text
                        ),
                    }
                )
                if missing:
                    errors.append(f"{expected_name}:missing_required_tokens")
            else:
                errors.append(f"{expected_name}:missing")
        except OSError:
            errors.append(f"{expected_name}:read_failed")
        return descriptor

    studio_descriptor = artifact_descriptor(
        studio,
        "ChaseOS-Studio.exe",
        "studio_artifact_missing",
    )
    installer_descriptor = artifact_descriptor(
        installer,
        "ChaseOS-Installer.exe",
        "installer_artifact_missing",
    )
    studio_script_descriptor = script_descriptor(
        studio_script,
        "build_exe.ps1",
        [
            "StudioDistPath",
            "StudioBuildOutput",
            "ExpectedOutput",
            "InstallerPath",
            "InstallerHashBefore",
            "InstallerHashAfter",
            "Copy-Item",
            "ChaseOS-Studio.exe",
            "ChaseOS-Installer.exe",
        ],
        "build\\studio-dist",
    )
    installer_script_descriptor = script_descriptor(
        installer_script,
        "build_installer.ps1",
        [
            "InstallerDistPath",
            "InstallerBuildOutput",
            "ExpectedOutput",
            "StudioPath",
            "StudioHashBefore",
            "StudioHashAfter",
            "Copy-Item",
            "ChaseOS-Installer.exe",
            "ChaseOS-Studio.exe",
        ],
        "build\\studio-installer-dist",
    )

    studio_script_ready = bool(
        studio_script_descriptor.get("present")
        and not studio_script_descriptor.get("missing_tokens")
        and studio_script_descriptor.get("isolated_dist_ready")
        and studio_script_descriptor.get("copy_only_expected_output_ready")
        and studio_script_descriptor.get("cross_artifact_hash_guard_ready")
    )
    installer_script_ready = bool(
        installer_script_descriptor.get("present")
        and not installer_script_descriptor.get("missing_tokens")
        and installer_script_descriptor.get("isolated_dist_ready")
        and installer_script_descriptor.get("copy_only_expected_output_ready")
        and installer_script_descriptor.get("cross_artifact_hash_guard_ready")
    )
    both_artifacts_present = bool(
        studio_descriptor.get("present") and installer_descriptor.get("present")
    )
    cohabitation_ready = bool(
        both_artifacts_present
        and studio_script_ready
        and installer_script_ready
        and not errors
    )
    status = "launcher_update_dist_artifact_isolation_cohabitation_blocked"
    if cohabitation_ready:
        status = (
            "launcher_update_dist_artifact_isolation_cohabitation_"
            "verified_unsigned"
        )

    proof = {
        "ok": cohabitation_ready,
        "surface": DIST_ARTIFACT_ISOLATION_COHABITATION_PROOF_SURFACE_ID,
        "schema_version": DIST_ARTIFACT_ISOLATION_COHABITATION_PROOF_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "dist_root": str(dist_root),
        "studio_artifact_descriptor": studio_descriptor,
        "installer_artifact_descriptor": installer_descriptor,
        "studio_build_script_descriptor": studio_script_descriptor,
        "installer_build_script_descriptor": installer_script_descriptor,
        "studio_artifact_present": bool(studio_descriptor.get("present")),
        "installer_artifact_present": bool(installer_descriptor.get("present")),
        "both_artifacts_present": both_artifacts_present,
        "studio_artifact_sha256": studio_descriptor.get("sha256", ""),
        "installer_artifact_sha256": installer_descriptor.get("sha256", ""),
        "studio_artifact_size_bytes": studio_descriptor.get("size_bytes", 0),
        "installer_artifact_size_bytes": installer_descriptor.get("size_bytes", 0),
        "studio_build_script_isolated_dist_ready": studio_script_ready,
        "installer_build_script_isolated_dist_ready": installer_script_ready,
        "cross_artifact_hash_guards_ready": bool(
            studio_script_descriptor.get("cross_artifact_hash_guard_ready")
            and installer_script_descriptor.get("cross_artifact_hash_guard_ready")
        ),
        "cohabitation_ready": cohabitation_ready,
        "signing_required": True,
        "signed_output_verified": False,
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "github_mutation_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "sign_chaseos_installer_and_studio_outputs"
            if cohabitation_ready
            else "restore_both_artifacts_and_harden_shared_dist_builds"
        ),
        "authority": _authority(
            dist_artifact_isolation_cohabitation_built=True,
            dist_artifact_isolation_cohabitation_ready=cohabitation_ready,
            dist_artifact_isolation_cohabitation_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof[
        "dist_artifact_isolation_cohabitation_digest_sha256"
    ] = _extension_digest_without(
        proof,
        "dist_artifact_isolation_cohabitation_digest_sha256",
    )
    return proof


def _signed_artifact_signature_descriptor(
    *,
    role,
    path,
    signature_probe,
    expected_signer_subject,
    expected_certificate_thumbprint,
    errors,
):
    descriptor = {
        "role": role,
        "path": str(path),
        "signature_probe_performed": callable(signature_probe),
        "signature_probe_result": {},
        "signature_probe_forbidden_key_paths": [],
        "status": "not_checked",
        "valid": False,
        "verified": False,
        "signer_subject": "",
        "certificate_thumbprint": "",
        "expected_signer_subject": expected_signer_subject or "",
        "expected_certificate_thumbprint": expected_certificate_thumbprint or "",
        "expected_signer_subject_matched": not bool(expected_signer_subject),
        "expected_certificate_thumbprint_matched": not bool(
            expected_certificate_thumbprint
        ),
        "signed_output_verified": False,
    }
    if not callable(signature_probe):
        errors.append(f"{role}_signature_probe_required")
        return descriptor

    try:
        probe_result = signature_probe(str(path))
    except Exception:
        errors.append(f"{role}_signature_probe_failed")
        return descriptor

    if not isinstance(probe_result, dict):
        errors.append(f"{role}_signature_probe_result_object_required")
        return descriptor

    forbidden_key_paths = (
        _approved_production_runner_real_evidence_capture_forbidden_key_paths(
            probe_result
        )
    )
    descriptor["signature_probe_forbidden_key_paths"] = forbidden_key_paths
    if forbidden_key_paths:
        errors.append(f"{role}_signature_probe_secret_like_keys_rejected")
    else:
        descriptor["signature_probe_result"] = dict(probe_result)

    status = str(probe_result.get("status", "")).strip()
    status_normalized = status.lower()
    signer_subject = str(
        probe_result.get("signer_subject")
        or probe_result.get("subject")
        or probe_result.get("certificate_subject")
        or ""
    )
    certificate_thumbprint = str(
        probe_result.get("certificate_thumbprint")
        or probe_result.get("thumbprint")
        or probe_result.get("signer_thumbprint")
        or ""
    )
    signature_valid = bool(
        not forbidden_key_paths
        and (
            probe_result.get("verified") is True
            or probe_result.get("valid") is True
            or status_normalized in {"valid", "verified", "signed_valid"}
        )
    )
    expected_subject_matched = True
    if expected_signer_subject:
        expected_subject_matched = (
            str(expected_signer_subject).lower() in signer_subject.lower()
        )
        if not expected_subject_matched:
            errors.append(f"{role}_expected_signer_subject_mismatch")

    def _normalize_thumbprint(value):
        return "".join(str(value).split()).lower()

    expected_thumbprint_matched = True
    if expected_certificate_thumbprint:
        expected_thumbprint_matched = _normalize_thumbprint(
            certificate_thumbprint
        ) == _normalize_thumbprint(expected_certificate_thumbprint)
        if not expected_thumbprint_matched:
            errors.append(f"{role}_expected_certificate_thumbprint_mismatch")

    if not signature_valid:
        errors.append(f"{role}_signature_not_valid")

    descriptor.update(
        {
            "status": status or "unknown",
            "valid": bool(probe_result.get("valid")),
            "verified": bool(probe_result.get("verified")),
            "signer_subject": signer_subject,
            "certificate_thumbprint": certificate_thumbprint,
            "expected_signer_subject_matched": expected_subject_matched,
            "expected_certificate_thumbprint_matched": expected_thumbprint_matched,
            "signed_output_verified": bool(
                signature_valid
                and expected_subject_matched
                and expected_thumbprint_matched
            ),
        }
    )
    return descriptor


def build_launcher_update_signed_artifact_verification_closeout(
    vault_root,
    *,
    studio_path=None,
    installer_path=None,
    cohabitation_proof=None,
    signature_probe=None,
    expected_signer_subject="",
    expected_certificate_thumbprint="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    dist_root = vault / "dist" / "studio"
    studio = (
        _Path(studio_path).resolve()
        if studio_path is not None
        else dist_root / "ChaseOS-Studio.exe"
    )
    installer = (
        _Path(installer_path).resolve()
        if installer_path is not None
        else dist_root / "ChaseOS-Installer.exe"
    )
    errors = []
    warnings = []

    current_cohabitation = build_launcher_update_dist_artifact_isolation_cohabitation_proof(
        vault,
        studio_path=studio,
        installer_path=installer,
        generated_at=generated_at,
    )
    supplied_cohabitation = (
        cohabitation_proof if isinstance(cohabitation_proof, dict) else None
    )
    if cohabitation_proof is not None and supplied_cohabitation is None:
        errors.append("cohabitation_proof_object_required")
    if supplied_cohabitation:
        for key in (
            "studio_artifact_sha256",
            "installer_artifact_sha256",
            "studio_artifact_size_bytes",
            "installer_artifact_size_bytes",
        ):
            if supplied_cohabitation.get(key) != current_cohabitation.get(key):
                errors.append(f"cohabitation_proof_{key}_mismatch")
        if not supplied_cohabitation.get("cohabitation_ready"):
            errors.append("supplied_cohabitation_proof_not_ready")

    cohabitation_ready = bool(
        current_cohabitation.get("cohabitation_ready")
        and not [
            error
            for error in errors
            if str(error).startswith("cohabitation_proof_")
            or error == "supplied_cohabitation_proof_not_ready"
        ]
    )
    if not current_cohabitation.get("cohabitation_ready"):
        errors.append("dist_artifact_isolation_cohabitation_required")
        warnings.extend(str(item) for item in current_cohabitation.get("errors") or [])

    signature_probe_performed = callable(signature_probe)
    studio_signature = _signed_artifact_signature_descriptor(
        role="studio",
        path=studio,
        signature_probe=signature_probe,
        expected_signer_subject=expected_signer_subject,
        expected_certificate_thumbprint=expected_certificate_thumbprint,
        errors=errors,
    )
    installer_signature = _signed_artifact_signature_descriptor(
        role="installer",
        path=installer,
        signature_probe=signature_probe,
        expected_signer_subject=expected_signer_subject,
        expected_certificate_thumbprint=expected_certificate_thumbprint,
        errors=errors,
    )

    studio_signed_output_verified = bool(
        cohabitation_ready and studio_signature.get("signed_output_verified")
    )
    installer_signed_output_verified = bool(
        cohabitation_ready and installer_signature.get("signed_output_verified")
    )
    signed_artifacts_verified = bool(
        studio_signed_output_verified
        and installer_signed_output_verified
        and not errors
    )
    status = "launcher_update_signed_artifact_verification_closeout_blocked"
    if signed_artifacts_verified:
        status = "launcher_update_signed_artifact_verification_closeout_verified"
    elif cohabitation_ready and not signature_probe_performed:
        status = (
            "launcher_update_signed_artifact_verification_closeout_"
            "signature_probe_required"
        )
    elif cohabitation_ready and signature_probe_performed:
        status = (
            "launcher_update_signed_artifact_verification_closeout_"
            "signatures_blocked"
        )

    proof = {
        "ok": signed_artifacts_verified,
        "surface": SIGNED_ARTIFACT_VERIFICATION_CLOSEOUT_SURFACE_ID,
        "schema_version": SIGNED_ARTIFACT_VERIFICATION_CLOSEOUT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "dist_root": str(dist_root),
        "errors": errors,
        "warnings": warnings,
        "cohabitation_proof": current_cohabitation,
        "cohabitation_ready": cohabitation_ready,
        "cohabitation_digest_sha256": current_cohabitation.get(
            "dist_artifact_isolation_cohabitation_digest_sha256",
            "",
        ),
        "studio_artifact_descriptor": current_cohabitation.get(
            "studio_artifact_descriptor", {}
        ),
        "installer_artifact_descriptor": current_cohabitation.get(
            "installer_artifact_descriptor", {}
        ),
        "studio_artifact_present": bool(
            current_cohabitation.get("studio_artifact_present")
        ),
        "installer_artifact_present": bool(
            current_cohabitation.get("installer_artifact_present")
        ),
        "both_artifacts_present": bool(
            current_cohabitation.get("both_artifacts_present")
        ),
        "studio_artifact_sha256": current_cohabitation.get(
            "studio_artifact_sha256", ""
        ),
        "installer_artifact_sha256": current_cohabitation.get(
            "installer_artifact_sha256", ""
        ),
        "studio_artifact_size_bytes": current_cohabitation.get(
            "studio_artifact_size_bytes", 0
        ),
        "installer_artifact_size_bytes": current_cohabitation.get(
            "installer_artifact_size_bytes", 0
        ),
        "signature_policy": {
            "requires_valid_authenticode": True,
            "requires_studio_signed_output": True,
            "requires_installer_signed_output": True,
            "requires_expected_signer_when_configured": True,
            "expected_signer_subject": expected_signer_subject or "",
            "expected_certificate_thumbprint": expected_certificate_thumbprint
            or "",
        },
        "signature_probe_performed": signature_probe_performed,
        "studio_signature": studio_signature,
        "installer_signature": installer_signature,
        "studio_signed_output_verified": studio_signed_output_verified,
        "installer_signed_output_verified": installer_signed_output_verified,
        "signed_artifacts_verified": signed_artifacts_verified,
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "github_mutation_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "feed_signed_artifacts_into_live_download_and_installer_receipts"
            if signed_artifacts_verified
            else (
                "run_authenticode_signature_probe_for_both_artifacts"
                if cohabitation_ready and not signature_probe_performed
                else (
                    "sign_chaseos_studio_and_installer_outputs"
                    if cohabitation_ready
                    else "restore_dist_artifact_cohabitation"
                )
            )
        ),
        "authority": _authority(
            signed_artifact_verification_closeout_built=True,
            signed_artifact_verification_closeout_ready=signed_artifacts_verified,
            signed_artifact_verification_closeout_signature_probe_performed=signature_probe_performed,
            signed_artifact_verification_closeout_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["signed_artifact_verification_closeout_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "signed_artifact_verification_closeout_digest_sha256",
        )
    )
    return proof


def _local_installer_disposable_sha256(path):
    digest = _wrapper_hashlib.sha256()
    with _Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _local_installer_disposable_path_descriptor(path, root, vault):
    resolved = _Path(path).resolve() if path else _Path(".").resolve()
    primary_dist = vault / "dist" / "studio"
    descriptor = {
        "path": str(path or ""),
        "resolved_path": str(resolved),
        "exists": resolved.exists(),
        "is_file": resolved.is_file(),
        "filename": resolved.name,
        "inside_disposable_root": (
            _extension_path_is_relative_to(resolved, root) if root else False
        ),
        "inside_primary_dist": _extension_path_is_relative_to(resolved, primary_dist),
        "size_bytes": 0,
        "sha256": "",
        "errors": [],
    }
    if descriptor["is_file"]:
        try:
            descriptor["size_bytes"] = resolved.stat().st_size
            descriptor["sha256"] = _local_installer_disposable_sha256(resolved)
        except OSError:
            descriptor["errors"].append("file_read_failed")
    return descriptor


def build_launcher_update_local_installer_disposable_dry_run_proof(
    vault_root,
    *,
    disposable_root=None,
    current_executable_path=None,
    staged_artifact_path=None,
    backup_executable_path=None,
    receipt_path=None,
    plan_file_path=None,
    allow_disposable_execution=False,
    generated_at=None,
):
    """Build and optionally run a local-only ChaseOS-Installer dry run.

    The optional execution path writes only under the supplied disposable root.
    It never targets the current vault `dist/studio` artifact, never enables
    live install flags, and never marks production auto-update complete.
    """

    from runtime.studio.launcher_update_helper import (
        INSTALLER_DISPOSABLE_UPDATE_MODE,
        INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION,
        execute_launcher_update_installer_disposable_update_plan,
    )

    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    disposable = _Path(disposable_root).resolve() if disposable_root else None

    if disposable is None:
        errors.append("disposable_root_required")
    elif disposable == vault:
        errors.append("disposable_root_must_not_be_vault_root")

    def _default_path(*parts):
        return disposable.joinpath(*parts) if disposable is not None else _Path("")

    current_path = (
        _Path(current_executable_path).resolve()
        if current_executable_path is not None
        else _default_path("installed", "ChaseOS-Studio.exe")
    )
    staged_path = (
        _Path(staged_artifact_path).resolve()
        if staged_artifact_path is not None
        else _default_path("staged", "ChaseOS-Studio.exe")
    )
    backup_path = (
        _Path(backup_executable_path).resolve()
        if backup_executable_path is not None
        else _default_path("backup", "ChaseOS-Studio.exe.bak")
    )
    receipt = (
        _Path(receipt_path).resolve()
        if receipt_path is not None
        else _default_path("receipts", "installer-disposable-update-receipt.json")
    )
    plan_file = (
        _Path(plan_file_path).resolve()
        if plan_file_path is not None
        else _default_path("plans", "chaseos-installer-disposable-update-plan.json")
    )

    path_descriptors = {
        "current_executable": _local_installer_disposable_path_descriptor(
            current_path,
            disposable,
            vault,
        ),
        "staged_artifact": _local_installer_disposable_path_descriptor(
            staged_path,
            disposable,
            vault,
        ),
        "backup_executable": _local_installer_disposable_path_descriptor(
            backup_path,
            disposable,
            vault,
        ),
        "receipt": _local_installer_disposable_path_descriptor(
            receipt,
            disposable,
            vault,
        ),
        "plan_file": _local_installer_disposable_path_descriptor(
            plan_file,
            disposable,
            vault,
        ),
    }

    for key, descriptor in path_descriptors.items():
        if disposable is not None and not descriptor.get("inside_disposable_root"):
            errors.append(f"{key}_path_not_inside_disposable_root")
        if descriptor.get("inside_primary_dist"):
            errors.append(f"{key}_path_must_not_target_primary_dist")
    if current_path.name != "ChaseOS-Studio.exe":
        errors.append("current_executable_name_mismatch")
    if staged_path.name != "ChaseOS-Studio.exe":
        errors.append("staged_artifact_name_mismatch")
    if receipt.suffix.lower() != ".json":
        errors.append("receipt_path_must_be_json")
    if plan_file.suffix.lower() != ".json":
        errors.append("plan_file_path_must_be_json")

    current_hash = path_descriptors["current_executable"].get("sha256", "")
    staged_hash = path_descriptors["staged_artifact"].get("sha256", "")
    if allow_disposable_execution:
        if not path_descriptors["current_executable"].get("is_file"):
            errors.append("current_executable_required_for_disposable_execution")
        if not path_descriptors["staged_artifact"].get("is_file"):
            errors.append("staged_artifact_required_for_disposable_execution")
        if path_descriptors["backup_executable"].get("exists"):
            errors.append("backup_executable_must_not_exist_before_execution")
        if path_descriptors["receipt"].get("exists"):
            errors.append("receipt_must_not_exist_before_execution")
        if path_descriptors["plan_file"].get("exists"):
            errors.append("plan_file_must_not_exist_before_execution")

    plan = {
        "schema_version": INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION,
        "mode": INSTALLER_DISPOSABLE_UPDATE_MODE,
        "generated_at_utc": timestamp,
        "helper_binary_name": "ChaseOS-Installer.exe",
        "target_artifact_name": "ChaseOS-Studio.exe",
        "target_root_kind": "disposable",
        "target_root": str(disposable or ""),
        "current_executable_path": str(current_path),
        "staged_artifact_path": str(staged_path),
        "backup_executable_path": str(backup_path),
        "receipt_path": str(receipt),
        "expected_current_sha256": current_hash,
        "expected_staged_sha256": staged_hash,
        "allow_live_install": False,
        "allow_primary_install_mutation": False,
        "relaunch_after_update": False,
        "github_release_publication_enabled": False,
        "startup_mutation_enabled": False,
        "production_auto_update_complete": False,
    }
    plan["plan_digest_sha256"] = _extension_digest_without(
        plan,
        "plan_digest_sha256",
    )

    plan_file_write_performed = False
    executor_result = {}
    if allow_disposable_execution and not errors:
        try:
            plan_file.parent.mkdir(parents=True, exist_ok=True)
            plan_file.write_text(
                _extension_json.dumps(plan, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            plan_file_write_performed = True
        except OSError as exc:
            errors.append(f"installer_disposable_plan_write_failed:{exc.__class__.__name__}")

    if plan_file_write_performed:
        executor_result = execute_launcher_update_installer_disposable_update_plan(
            plan_file,
            vault_root=vault,
            execute_disposable=True,
            generated_at=timestamp,
        )
        if executor_result.get("errors"):
            errors.extend(str(item) for item in executor_result.get("errors") or [])
        if executor_result.get("warnings"):
            warnings.extend(str(item) for item in executor_result.get("warnings") or [])

    dry_run_executed = bool(
        executor_result.get("disposable_target_update_performed")
        and executor_result.get("receipt_written")
    )
    receipt_payload = executor_result.get("receipt_payload") or {}
    receipt_verified = bool(
        dry_run_executed
        and receipt_payload.get("target_replaced") is True
        and receipt_payload.get("replacement_verified") is True
        and receipt_payload.get("primary_install_mutation_performed") is False
        and receipt_payload.get("live_install_performed") is False
    )
    plan_preview_ready = bool(
        disposable is not None
        and not [
            error
            for error in errors
            if error
            not in {
                "current_executable_required_for_disposable_execution",
                "staged_artifact_required_for_disposable_execution",
                "backup_executable_must_not_exist_before_execution",
                "receipt_must_not_exist_before_execution",
                "plan_file_must_not_exist_before_execution",
            }
        ]
    )

    status = "launcher_update_local_installer_disposable_dry_run_blocked"
    if plan_preview_ready and not allow_disposable_execution:
        status = "launcher_update_local_installer_disposable_dry_run_plan_ready_execution_disabled"
    if dry_run_executed and receipt_verified:
        status = "launcher_update_local_installer_disposable_dry_run_receipt_verified"

    proof = {
        "ok": receipt_verified,
        "surface": LOCAL_INSTALLER_DISPOSABLE_DRY_RUN_SURFACE_ID,
        "schema_version": LOCAL_INSTALLER_DISPOSABLE_DRY_RUN_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": list(dict.fromkeys(str(item) for item in errors if str(item))),
        "warnings": list(dict.fromkeys(str(item) for item in warnings if str(item))),
        "helper_binary_name": "ChaseOS-Installer.exe",
        "target_artifact_name": "ChaseOS-Studio.exe",
        "disposable_root": str(disposable or ""),
        "path_descriptors": path_descriptors,
        "plan": plan,
        "plan_file_path": str(plan_file),
        "plan_file_write_performed": plan_file_write_performed,
        "executor_result": executor_result,
        "receipt_path": str(receipt),
        "receipt_payload": receipt_payload,
        "receipt_verified": receipt_verified,
        "local_installer_disposable_dry_run_plan_valid": bool(
            executor_result.get("validation", {}).get("plan_digest_valid")
            if executor_result
            else plan_preview_ready
        ),
        "local_installer_disposable_dry_run_executed": dry_run_executed,
        "local_installer_disposable_dry_run_receipt_written": bool(
            executor_result.get("receipt_written")
        ),
        "backup_created": bool(executor_result.get("backup_created")),
        "disposable_target_update_performed": dry_run_executed,
        "installer_execution_performed": dry_run_executed,
        "executable_replacement_performed": dry_run_executed,
        "primary_install_mutation_performed": False,
        "live_install_performed": False,
        "relaunch_performed": False,
        "github_release_publication_performed": False,
        "startup_mutation_performed": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "package_and_run_chaseos_installer_exe_against_disposable_plan"
            if receipt_verified
            else (
                "run_disposable_target_installer_plan_with_explicit_flag"
                if plan_preview_ready
                else "supply_disposable_target_root_and_fixture_artifacts"
            )
        ),
        "authority": _authority(
            local_installer_disposable_dry_run_built=True,
            local_installer_disposable_dry_run_plan_valid=bool(
                executor_result.get("validation", {}).get("plan_digest_valid")
                if executor_result
                else plan_preview_ready
            ),
            local_installer_disposable_dry_run_executed=dry_run_executed,
            local_installer_disposable_dry_run_receipt_written=bool(
                executor_result.get("receipt_written")
            ),
            local_installer_disposable_dry_run_primary_install_mutation_performed=False,
            local_installer_disposable_dry_run_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["local_installer_disposable_dry_run_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "local_installer_disposable_dry_run_digest_sha256",
        )
    )
    return proof


def _local_manifest_background_prompt_version_tuple(value):
    text = str(value or "").strip()
    if text.lower().startswith("v"):
        text = text[1:]
    parts = text.split(".")
    if not text or len(parts) not in {2, 3, 4}:
        return None
    parsed = []
    for part in parts:
        if not part.isdigit():
            return None
        parsed.append(int(part))
    while len(parsed) < 4:
        parsed.append(0)
    return tuple(parsed)


def _local_manifest_background_prompt_is_sha256(value):
    text = str(value or "").strip().lower()
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _local_manifest_background_prompt_manifest_descriptor(
    manifest_path,
    vault,
):
    candidate = (
        _Path(manifest_path).resolve()
        if manifest_path
        else (vault / LOCAL_UPDATE_MANIFEST_DEFAULT_RELATIVE_PATH).resolve()
    )
    descriptor = {
        "configured_path": str(manifest_path or LOCAL_UPDATE_MANIFEST_DEFAULT_RELATIVE_PATH),
        "path": str(candidate),
        "resolved_path": str(candidate),
        "exists": candidate.exists(),
        "is_file": candidate.is_file(),
        "inside_vault_root": _extension_path_is_relative_to(candidate, vault),
        "default_path_used": manifest_path is None,
        "errors": [],
    }
    if not descriptor["inside_vault_root"]:
        descriptor["errors"].append("manifest_path_outside_vault_root")
    if descriptor["exists"] and not descriptor["is_file"]:
        descriptor["errors"].append("manifest_path_not_file")
    return descriptor


def _local_manifest_background_prompt_download_descriptor(download_url):
    raw = str(download_url or "").strip()
    descriptor = {
        "url": raw,
        "configured": bool(raw),
        "scheme": "",
        "network_url": False,
        "file_url": False,
        "usable_for_this_pass": False,
        "errors": [],
        "warnings": [],
    }
    if not raw:
        return descriptor
    lowered = raw.lower()
    if "://" not in lowered:
        descriptor["warnings"].append("download_url_is_placeholder_or_relative")
        return descriptor
    scheme = lowered.split("://", 1)[0]
    descriptor["scheme"] = scheme
    if scheme in {"http", "https"}:
        descriptor["network_url"] = True
        descriptor["warnings"].append("network_download_blocked_in_local_manifest_pass")
    elif scheme == "file":
        descriptor["file_url"] = True
        descriptor["warnings"].append("file_url_not_consumed_without_artifact_path")
    else:
        descriptor["errors"].append("download_url_scheme_unsupported")
    return descriptor


def _local_manifest_background_prompt_artifact_descriptor(
    artifact_path,
    *,
    manifest_file,
    vault,
    expected_artifact_name,
    expected_sha256,
):
    descriptor = {
        "path": str(artifact_path or ""),
        "resolved_path": "",
        "exists": False,
        "is_file": False,
        "filename": "",
        "inside_vault_root": False,
        "inside_manifest_directory": False,
        "size_bytes": 0,
        "sha256": "",
        "expected_sha256": str(expected_sha256 or "").strip().lower(),
        "sha256_format_valid": True,
        "sha256_matches_expected": False,
        "ready": False,
        "errors": [],
        "warnings": [],
    }
    if not artifact_path:
        descriptor["warnings"].append("artifact_path_missing")
        return descriptor
    raw_path = _Path(artifact_path)
    if not raw_path.is_absolute():
        raw_path = manifest_file.parent / raw_path
    try:
        resolved = raw_path.resolve()
    except OSError:
        resolved = raw_path
    descriptor["resolved_path"] = str(resolved)
    descriptor["exists"] = resolved.exists()
    descriptor["is_file"] = resolved.is_file()
    descriptor["filename"] = resolved.name
    descriptor["inside_vault_root"] = _extension_path_is_relative_to(resolved, vault)
    descriptor["inside_manifest_directory"] = _extension_path_is_relative_to(
        resolved,
        manifest_file.parent,
    )
    if descriptor["filename"] != expected_artifact_name:
        descriptor["errors"].append("artifact_filename_mismatch")
    if not descriptor["inside_vault_root"]:
        descriptor["errors"].append("artifact_path_outside_vault_root")
    if descriptor["expected_sha256"] and not _local_manifest_background_prompt_is_sha256(
        descriptor["expected_sha256"]
    ):
        descriptor["sha256_format_valid"] = False
        descriptor["errors"].append("artifact_sha256_invalid")
    if descriptor["is_file"]:
        try:
            descriptor["size_bytes"] = resolved.stat().st_size
            descriptor["sha256"] = _local_installer_disposable_sha256(resolved)
        except OSError:
            descriptor["errors"].append("artifact_read_failed")
    elif descriptor["exists"]:
        descriptor["errors"].append("artifact_path_not_file")
    else:
        descriptor["warnings"].append("artifact_file_not_present")
    if descriptor["expected_sha256"] and descriptor["sha256"]:
        descriptor["sha256_matches_expected"] = (
            descriptor["sha256"].lower() == descriptor["expected_sha256"]
        )
        if not descriptor["sha256_matches_expected"]:
            descriptor["errors"].append("artifact_sha256_mismatch")
    descriptor["ready"] = bool(
        descriptor["is_file"]
        and descriptor["inside_vault_root"]
        and descriptor["filename"] == expected_artifact_name
        and descriptor["sha256_format_valid"]
        and (
            not descriptor["expected_sha256"]
            or descriptor["sha256_matches_expected"]
        )
        and not descriptor["errors"]
    )
    return descriptor


def build_launcher_update_local_manifest_background_prompt_settings_action(
    vault_root,
    *,
    manifest_path=None,
    current_version=None,
    disposable_root=None,
    current_executable_path=None,
    generated_at=None,
):
    """Read a local update manifest and build Settings prompt state only.

    This is a local-file check lane. It performs no network fetch, no download,
    no installer launch, no startup mutation, and no primary EXE replacement.
    """

    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    status_model = {}
    try:
        status_model = build_launcher_update_status(vault)
    except Exception:
        status_model = {}
    installed_version = str(
        current_version
        or status_model.get("current_version")
        or "0.0.0"
    )
    current_tuple = _local_manifest_background_prompt_version_tuple(installed_version)
    manifest_descriptor = _local_manifest_background_prompt_manifest_descriptor(
        manifest_path,
        vault,
    )
    manifest_file = _Path(manifest_descriptor["resolved_path"])
    manifest_configured = bool(
        (manifest_path is not None) or manifest_descriptor.get("exists")
    )
    errors = list(manifest_descriptor.get("errors") or [])
    warnings = []
    manifest = {}
    manifest_read_performed = False
    manifest_json_valid = False
    manifest_schema_valid = False
    manifest_valid = False
    latest_version = ""
    latest_tuple = None
    artifact_name = "ChaseOS-Studio.exe"
    expected_sha256 = ""
    release_date = ""
    release_notes_summary = ""
    download_descriptor = _local_manifest_background_prompt_download_descriptor("")
    artifact_descriptor = _local_manifest_background_prompt_artifact_descriptor(
        "",
        manifest_file=manifest_file,
        vault=vault,
        expected_artifact_name=artifact_name,
        expected_sha256="",
    )

    if not manifest_configured and not errors:
        status = "launcher_update_local_manifest_background_prompt_no_manifest_configured"
    elif manifest_descriptor.get("exists") and not errors:
        try:
            raw_manifest = manifest_file.read_text(encoding="utf-8")
            manifest_read_performed = True
            loaded_manifest = _extension_json.loads(raw_manifest)
            manifest_json_valid = isinstance(loaded_manifest, dict)
            if manifest_json_valid:
                manifest = loaded_manifest
            else:
                errors.append("manifest_json_object_required")
        except OSError as exc:
            errors.append(f"manifest_read_failed:{exc.__class__.__name__}")
        except ValueError:
            errors.append("manifest_json_malformed")

        if manifest_json_valid:
            schema_version = str(manifest.get("schema_version") or "")
            if schema_version and schema_version != LOCAL_UPDATE_MANIFEST_SCHEMA_VERSION:
                warnings.append("manifest_schema_version_unknown")
            latest_version = str(manifest.get("latest_version") or "").strip()
            latest_tuple = _local_manifest_background_prompt_version_tuple(
                latest_version
            )
            artifact_name = str(manifest.get("artifact_name") or "").strip()
            release_date = str(manifest.get("release_date") or "").strip()
            release_notes_summary = str(
                manifest.get("release_notes_summary")
                or manifest.get("release_notes")
                or ""
            ).strip()
            expected_sha256 = str(
                manifest.get("sha256")
                or manifest.get("artifact_sha256")
                or manifest.get("checksum_sha256")
                or ""
            ).strip().lower()
            download_descriptor = _local_manifest_background_prompt_download_descriptor(
                manifest.get("download_url")
            )
            if not latest_version:
                errors.append("latest_version_required")
            elif latest_tuple is None:
                errors.append("latest_version_malformed")
            if current_tuple is None:
                errors.append("current_version_malformed")
            if not artifact_name:
                errors.append("artifact_name_required")
            elif artifact_name != "ChaseOS-Studio.exe":
                errors.append("artifact_name_mismatch")
            if expected_sha256 and not _local_manifest_background_prompt_is_sha256(
                expected_sha256
            ):
                errors.append("artifact_sha256_invalid")
            artifact_descriptor = _local_manifest_background_prompt_artifact_descriptor(
                manifest.get("artifact_path") or manifest.get("local_artifact_path"),
                manifest_file=manifest_file,
                vault=vault,
                expected_artifact_name="ChaseOS-Studio.exe",
                expected_sha256=expected_sha256,
            )
            errors.extend(download_descriptor.get("errors") or [])
            if artifact_descriptor.get("path"):
                errors.extend(artifact_descriptor.get("errors") or [])
            warnings.extend(download_descriptor.get("warnings") or [])
            warnings.extend(artifact_descriptor.get("warnings") or [])
            manifest_schema_valid = bool(
                latest_tuple is not None
                and current_tuple is not None
                and artifact_name == "ChaseOS-Studio.exe"
            )
        manifest_valid = bool(manifest_json_valid and manifest_schema_valid and not errors)
        status = "launcher_update_local_manifest_background_prompt_malformed_manifest"
    else:
        if manifest_configured:
            errors.append("manifest_file_missing")
        status = "launcher_update_local_manifest_background_prompt_manifest_unavailable"

    update_available = bool(
        manifest_valid
        and latest_tuple is not None
        and current_tuple is not None
        and latest_tuple > current_tuple
    )
    manifest_older_than_current = bool(
        manifest_valid
        and latest_tuple is not None
        and current_tuple is not None
        and latest_tuple < current_tuple
    )
    installed_up_to_date = bool(
        manifest_valid
        and latest_tuple is not None
        and current_tuple is not None
        and latest_tuple <= current_tuple
    )
    staged_artifact_ready = bool(artifact_descriptor.get("ready"))
    installer_plan_preview = {}
    installer_plan_preview_ready = False
    if update_available and staged_artifact_ready and disposable_root:
        installer_plan_preview = build_launcher_update_local_installer_disposable_dry_run_proof(
            vault,
            disposable_root=disposable_root,
            current_executable_path=current_executable_path,
            staged_artifact_path=artifact_descriptor.get("resolved_path"),
            allow_disposable_execution=False,
            generated_at=timestamp,
        )
        installer_plan_preview_ready = bool(
            installer_plan_preview.get("status")
            == "launcher_update_local_installer_disposable_dry_run_plan_ready_execution_disabled"
        )

    if manifest_valid:
        if update_available and installer_plan_preview_ready:
            status = (
                "launcher_update_local_manifest_background_prompt_"
                "prompt_ready_installer_plan_preview"
            )
        elif update_available and staged_artifact_ready:
            status = "launcher_update_local_manifest_background_prompt_prompt_ready"
        elif update_available:
            status = (
                "launcher_update_local_manifest_background_prompt_"
                "update_available_staging_required"
            )
        else:
            status = "launcher_update_local_manifest_background_prompt_up_to_date"

    latest_version_label = (
        latest_version
        if latest_version and manifest_json_valid
        else ("Unavailable" if manifest_configured else "Not checked")
    )
    settings_prompt_visible = bool(update_available and manifest_valid)
    settings_action_state = {
        "manual_check_action_visible": True,
        "background_prompt_enabled_by_default": False,
        "settings_prompt_visible": settings_prompt_visible,
        "prompted_only": True,
        "primary_action_label": "Review update" if settings_prompt_visible else "Check for update",
        "download_action_exposed": False,
        "install_action_exposed": False,
        "current_version_line": f"Current version: {installed_version}",
        "latest_version_line": f"Latest available version: {latest_version_label}",
        "message": (
            f"Update available: {installed_version} -> {latest_version}."
            if settings_prompt_visible
            else (
                "Installed version is up to date."
                if installed_up_to_date
                else (
                    "No local update manifest is configured."
                    if not manifest_configured
                    else "Local update manifest is not usable."
                )
            )
        ),
    }
    proof = {
        "ok": bool(manifest_valid and (settings_prompt_visible or installed_up_to_date)),
        "surface": LOCAL_MANIFEST_BACKGROUND_PROMPT_SURFACE_ID,
        "schema_version": LOCAL_MANIFEST_BACKGROUND_PROMPT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": list(dict.fromkeys(str(item) for item in errors if str(item))),
        "warnings": list(dict.fromkeys(str(item) for item in warnings if str(item))),
        "current_version": installed_version,
        "latest_available_version": latest_version or "",
        "latest_version_label": latest_version_label,
        "version_comparison": {
            "current_version": installed_version,
            "latest_version": latest_version,
            "current_version_tuple": list(current_tuple or []),
            "latest_version_tuple": list(latest_tuple or []),
            "update_available": update_available,
            "manifest_older_than_current": manifest_older_than_current,
            "installed_up_to_date": installed_up_to_date,
        },
        "manifest_configured": manifest_configured,
        "manifest_read_performed": manifest_read_performed,
        "manifest_json_valid": manifest_json_valid,
        "manifest_schema_valid": manifest_schema_valid,
        "manifest_valid": manifest_valid,
        "manifest_descriptor": manifest_descriptor,
        "manifest_schema_version": str(manifest.get("schema_version") or ""),
        "local_update_manifest_schema_version": LOCAL_UPDATE_MANIFEST_SCHEMA_VERSION,
        "release_date": release_date,
        "release_notes_summary": release_notes_summary,
        "artifact_name": artifact_name or "ChaseOS-Studio.exe",
        "target_artifact_name": "ChaseOS-Studio.exe",
        "download_url_descriptor": download_descriptor,
        "artifact_descriptor": artifact_descriptor,
        "staged_artifact_ready": staged_artifact_ready,
        "installer_plan_preview": installer_plan_preview,
        "installer_plan_preview_ready": installer_plan_preview_ready,
        "update_available": update_available,
        "settings_action_state": settings_action_state,
        "settings_prompt_visible": settings_prompt_visible,
        "settings_install_control_exposed": False,
        "settings_download_control_exposed": False,
        "background_poll_enabled_by_default": False,
        "manifest_network_fetch_performed": False,
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "github_release_publication_performed_by_this_proof": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": (
            "connect_github_or_domain_release_manifest_last"
            if settings_prompt_visible
            else (
                "write_or_configure_local_update_manifest"
                if not manifest_configured
                else "fix_local_update_manifest"
            )
        ),
        "authority": _authority(
            local_manifest_background_prompt_built=True,
            local_manifest_background_prompt_manifest_checked=manifest_read_performed,
            local_manifest_background_prompt_update_available=update_available,
            local_manifest_background_prompt_installer_plan_ready=installer_plan_preview_ready,
            local_manifest_background_prompt_settings_prompt_visible=settings_prompt_visible,
            local_manifest_background_prompt_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["local_manifest_background_prompt_digest_sha256"] = _extension_digest_without(
        proof,
        "local_manifest_background_prompt_digest_sha256",
    )
    return proof


def build_launcher_update_local_release_channel_blocker_closeout(
    vault_root,
    *,
    manifest_path=None,
    signature_probe=None,
    generated_at=None,
):
    """Close the local updater lane before hosted release/signing work.

    This surface classifies what remains after the local prompt/check and
    disposable-installer lanes. It performs no network fetch, no download, no
    installer launch, no startup mutation, and no primary EXE replacement.
    """

    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    status_model = {}
    try:
        status_model = build_launcher_update_status(vault)
    except Exception as exc:
        warnings.append(f"launcher_update_status_unavailable:{exc.__class__.__name__}")
    dist_proof = build_launcher_update_dist_artifact_isolation_cohabitation_proof(
        vault,
        generated_at=timestamp,
    )
    if dist_proof.get("warnings"):
        warnings.extend(str(item) for item in dist_proof.get("warnings") or [])
    if dist_proof.get("errors"):
        errors.extend(
            f"dist_artifact_isolation_cohabitation:{item}"
            for item in dist_proof.get("errors") or []
        )
    signed_proof = build_launcher_update_signed_artifact_verification_closeout(
        vault,
        signature_probe=signature_probe,
        generated_at=timestamp,
    )
    if signed_proof.get("warnings"):
        warnings.extend(str(item) for item in signed_proof.get("warnings") or [])
    local_manifest_prompt = (
        build_launcher_update_local_manifest_background_prompt_settings_action(
            vault,
            manifest_path=manifest_path,
            generated_at=timestamp,
        )
    )
    if local_manifest_prompt.get("warnings"):
        warnings.extend(
            str(item) for item in local_manifest_prompt.get("warnings") or []
        )

    readiness = _readiness()
    dangerous_defaults_disabled = bool(
        not readiness.get(
            "updater_local_manifest_background_prompt_background_poll_enabled_by_default"
        )
        and not readiness.get(
            "updater_local_manifest_background_prompt_download_enabled_by_default"
        )
        and not readiness.get(
            "updater_local_manifest_background_prompt_installer_launch_enabled_by_default"
        )
        and not readiness.get(
            "updater_local_manifest_background_prompt_primary_replacement_enabled_by_default"
        )
        and not readiness.get(
            "updater_local_installer_disposable_dry_run_live_install_enabled_by_default"
        )
        and not readiness.get(
            "updater_local_installer_disposable_dry_run_primary_replacement_enabled_by_default"
        )
    )
    settings_install_control_disabled = bool(
        not local_manifest_prompt.get("settings_install_control_exposed")
        and not dist_proof.get("settings_install_control_exposed")
        and not signed_proof.get("settings_install_control_exposed")
    )
    local_manifest_surface_ready = bool(
        readiness.get("updater_local_manifest_background_prompt_proof_built")
        and readiness.get("updater_local_manifest_background_prompt_validates_manifest_schema")
        and readiness.get("updater_local_manifest_background_prompt_compares_current_latest")
        and readiness.get("updater_local_manifest_background_prompt_prompted_only")
    )
    local_installer_surface_ready = bool(
        readiness.get("updater_local_installer_disposable_dry_run_proof_built")
        and readiness.get("updater_local_installer_disposable_dry_run_uses_chaseos_installer")
        and readiness.get("updater_local_installer_disposable_dry_run_blocks_primary_dist_target")
        and readiness.get("updater_local_installer_disposable_dry_run_requires_explicit_execution_flag")
    )

    def requirement(identifier, passed, evidence, blocker_kind="local"):
        return {
            "id": identifier,
            "passed": bool(passed),
            "evidence": evidence,
            "blocker_kind": blocker_kind,
        }

    local_requirement_checks = [
        requirement(
            "current_version_metadata_available",
            bool(status_model.get("current_version")),
            "build_launcher_update_status.current_version",
        ),
        requirement(
            "dist_artifacts_cohabitation_ready",
            dist_proof.get("ok") and dist_proof.get("cohabitation_ready"),
            DIST_ARTIFACT_ISOLATION_COHABITATION_PROOF_SURFACE_ID,
        ),
        requirement(
            "chaseos_studio_artifact_present",
            dist_proof.get("studio_artifact_present"),
            "dist/studio/ChaseOS-Studio.exe",
        ),
        requirement(
            "chaseos_installer_artifact_present",
            dist_proof.get("installer_artifact_present"),
            "dist/studio/ChaseOS-Installer.exe",
        ),
        requirement(
            "local_manifest_prompt_surface_ready",
            local_manifest_surface_ready,
            LOCAL_MANIFEST_BACKGROUND_PROMPT_SURFACE_ID,
        ),
        requirement(
            "local_installer_disposable_surface_ready",
            local_installer_surface_ready,
            LOCAL_INSTALLER_DISPOSABLE_DRY_RUN_SURFACE_ID,
        ),
        requirement(
            "settings_install_control_disabled",
            settings_install_control_disabled,
            "settings_update_card",
        ),
        requirement(
            "dangerous_defaults_disabled",
            dangerous_defaults_disabled,
            "readiness_flags",
        ),
    ]
    non_external_blockers = [
        item["id"] for item in local_requirement_checks if not item["passed"]
    ]
    signing_verified = bool(signed_proof.get("signed_artifacts_verified"))
    local_manifest_configured = bool(local_manifest_prompt.get("manifest_configured"))
    external_blockers = []
    if not local_manifest_configured:
        external_blockers.append(
            {
                "id": "release_channel_hosting_not_connected",
                "category": "github_or_domain_release_channel",
                "why_external": (
                    "A real release manifest requires a GitHub Release or "
                    "standalone domain decision and hosted artifact URL."
                ),
                "current_status": local_manifest_prompt.get("status", ""),
            }
        )
    if not signing_verified:
        external_blockers.append(
            {
                "id": "production_signing_not_verified",
                "category": "production_signing",
                "why_external": (
                    "Both ChaseOS-Studio.exe and ChaseOS-Installer.exe must be "
                    "signed and verified outside this local no-signing pass."
                ),
                "current_status": signed_proof.get("status", ""),
            }
        )
    external_blockers.append(
        {
            "id": "production_installer_deployment_receipts_missing",
            "category": "installer_deployment",
            "why_external": (
                "Primary replacement, relaunch, rollback, and startup prompt "
                "receipts require a real hosted or deployment-channel install run."
            ),
            "current_status": "not_run_by_local_closeout",
        }
    )
    external_blockers.append(
        {
            "id": "live_download_install_receipts_missing",
            "category": "release_download_install",
            "why_external": (
                "A live binary download and real install receipt cannot be "
                "proved until the release channel exists."
            ),
            "current_status": "not_run_by_local_closeout",
        }
    )
    external_blocker_ids = [item["id"] for item in external_blockers]
    local_closeout_ready = not non_external_blockers
    only_external_blockers_remain = bool(local_closeout_ready and external_blockers)
    status = "launcher_update_local_release_channel_blocker_closeout_local_blockers_remaining"
    if only_external_blockers_remain:
        status = (
            "launcher_update_local_release_channel_blocker_closeout_"
            "only_external_blockers_remain"
        )

    closeout_summary = {
        "local_passes_remaining_before_external_blocker": (
            0 if local_closeout_ready else len(non_external_blockers)
        ),
        "estimated_passes_after_hosting_and_signing": "2-3",
        "release_channel_options": ["github_releases", "standalone_domain"],
        "recommended_next_action": (
            "choose_github_or_domain_release_channel_and_sign_artifacts"
            if local_closeout_ready
            else "fix_local_closeout_blockers"
        ),
        "plain_language_status": (
            "Local updater scaffolding is closed enough to stop local passes; "
            "the remaining work needs release hosting, signing, and a real "
            "installer deployment run."
            if local_closeout_ready
            else "Local updater scaffolding still has blockers that can be fixed in repo."
        ),
    }
    proof = {
        "ok": local_closeout_ready,
        "surface": LOCAL_RELEASE_CHANNEL_BLOCKER_CLOSEOUT_SURFACE_ID,
        "schema_version": LOCAL_RELEASE_CHANNEL_BLOCKER_CLOSEOUT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": list(dict.fromkeys(str(item) for item in errors if str(item))),
        "warnings": list(dict.fromkeys(str(item) for item in warnings if str(item))),
        "current_version": str(status_model.get("current_version") or ""),
        "latest_available_version": str(
            local_manifest_prompt.get("latest_available_version") or ""
        ),
        "local_closeout_ready": local_closeout_ready,
        "only_external_blockers_remain": only_external_blockers_remain,
        "local_requirement_checks": local_requirement_checks,
        "non_external_blockers": non_external_blockers,
        "external_blockers": external_blockers,
        "external_blocker_ids": external_blocker_ids,
        "release_channel_connected": False,
        "release_channel_kind": "not_configured",
        "release_channel_decision_required": True,
        "local_manifest_configured": local_manifest_configured,
        "local_manifest_prompt": local_manifest_prompt,
        "dist_artifact_isolation_cohabitation_proof": dist_proof,
        "signed_artifact_verification_closeout": signed_proof,
        "dist_artifacts_cohabitation_ready": bool(dist_proof.get("cohabitation_ready")),
        "signed_artifacts_verified": signing_verified,
        "settings_install_control_exposed": False,
        "settings_download_control_exposed": False,
        "background_poll_enabled_by_default": False,
        "download_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "primary_replacement_performed_by_this_proof": False,
        "startup_mutation_performed_by_this_proof": False,
        "github_release_publication_performed_by_this_proof": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "closeout_summary": closeout_summary,
        "next_required_step": closeout_summary["recommended_next_action"],
        "authority": _authority(
            local_release_channel_blocker_closeout_built=True,
            local_release_channel_blocker_closeout_local_ready=local_closeout_ready,
            local_release_channel_blocker_closeout_only_external_blockers_remain=only_external_blockers_remain,
            local_release_channel_blocker_closeout_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["local_release_channel_blocker_closeout_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "local_release_channel_blocker_closeout_digest_sha256",
        )
    )
    return proof


def _approved_live_evidence_runner_real_dry_run_plan(
    *,
    vault,
    timestamp,
    source_statuses,
):
    plan = {
        "surface": f"{APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SURFACE_ID}_plan",
        "schema_version": APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "target_artifact": "ChaseOS-Studio.exe",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "required_sources": [item["id"] for item in source_statuses],
        "source_digests": {
            item["id"]: item["digest_sha256"] for item in source_statuses
        },
        "source_statuses": [
            {
                key: value
                for key, value in item.items()
                if key != "proof"
            }
            for item in source_statuses
        ],
        "feeds_surface": APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SURFACE_ID,
        "can_preview_final_closeout_audit": True,
        "secret_values_allowed": False,
        "settings_install_control_exposed": False,
        "download_performed_by_dry_run": False,
        "installer_launch_performed_by_dry_run": False,
        "primary_replacement_performed_by_dry_run": False,
        "startup_mutation_performed_by_dry_run": False,
    }
    plan["approved_live_evidence_runner_real_dry_run_plan_digest_sha256"] = (
        _extension_digest_without(
            plan,
            "approved_live_evidence_runner_real_dry_run_plan_digest_sha256",
        )
    )
    return plan


def required_update_approved_live_evidence_runner_real_dry_run_operator_statement(
    dry_run_plan,
):
    digest = str(
        (dry_run_plan or {}).get(
            "approved_live_evidence_runner_real_dry_run_plan_digest_sha256"
        )
        or _extension_digest_without(
            dry_run_plan or {},
            "approved_live_evidence_runner_real_dry_run_plan_digest_sha256",
        )
    )
    return (
        f"{APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_OPERATOR_STATEMENT_PREFIX} "
        f"{digest}"
    )


def build_launcher_update_approved_live_evidence_runner_real_dry_run(
    vault_root,
    *,
    signed_release_manifest_live_readback=None,
    signed_manifest_approved_live_download_staging=None,
    signed_manifest_downloaded_staged_signature_verification=None,
    installer_real_build_signed_output_verification=None,
    production_primary_relaunch_receipt_boundary=None,
    startup_background_prompt_from_signed_manifest_execution_dry_run=None,
    production_primary_closeout_after_source_recovery_proof=None,
    operator_approved_live_evidence_runner_real_dry_run=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    supplied_inputs = {
        "signed_release_manifest_live_readback": signed_release_manifest_live_readback,
        "signed_manifest_approved_live_download_staging": signed_manifest_approved_live_download_staging,
        "signed_manifest_downloaded_staged_signature_verification": signed_manifest_downloaded_staged_signature_verification,
        "installer_real_build_signed_output_verification": installer_real_build_signed_output_verification,
        "production_primary_relaunch_receipt_boundary": production_primary_relaunch_receipt_boundary,
        "startup_background_prompt_from_signed_manifest_execution_dry_run": startup_background_prompt_from_signed_manifest_execution_dry_run,
    }
    default_source_readback_performed = not all(
        value is not None for value in supplied_inputs.values()
    )
    default_inputs = {}
    if default_source_readback_performed:
        default_inputs = (
            _approved_live_evidence_runner_real_dry_run_default_source_proofs(
                vault,
                timestamp,
            )
        )
    source_inputs = {
        key: value if value is not None else default_inputs.get(key)
        for key, value in supplied_inputs.items()
    }
    (
        source_inputs,
        source_digest_checks,
        ready_digest_mismatch_errors,
        normalized_blocked_receipt_digest_count,
    ) = _live_receipt_digest_consistency_prepare_source_inputs(source_inputs)
    errors.extend(ready_digest_mismatch_errors)

    source_statuses = []
    for spec in _approved_live_evidence_runner_adapter_source_specs():
        status_item = _approved_live_evidence_runner_adapter_proof_status(
            source_inputs.get(spec["id"]),
            spec,
        )
        source_statuses.append(status_item)
        proof = status_item["proof"]
        if proof.get("warnings"):
            warnings.extend(str(item) for item in proof.get("warnings") or [])
        if proof.get("errors"):
            warnings.extend(
                f"{spec['id']}:{item}" for item in (proof.get("errors") or [])
            )
        if not status_item["present"]:
            errors.append(f"{spec['id']}_proof_required")
        elif not status_item["surface_matched"]:
            errors.append(f"{spec['id']}_surface_mismatch")
        elif not status_item["digest_matched"]:
            errors.append(f"{spec['id']}_digest_mismatch")
        elif not status_item["ready"]:
            errors.append(f"{spec['id']}_not_ready")

    sources_ready = all(item["ready"] for item in source_statuses)
    source_digest_consistency_closeout_ready = bool(
        source_statuses
        and not ready_digest_mismatch_errors
        and all(item["present"] for item in source_statuses)
        and all(item["surface_matched"] for item in source_statuses)
        and all(item["digest_matched"] for item in source_statuses)
    )
    dry_run_plan = _approved_live_evidence_runner_real_dry_run_plan(
        vault=vault,
        timestamp=timestamp,
        source_statuses=source_statuses,
    )
    required_statement = (
        required_update_approved_live_evidence_runner_real_dry_run_operator_statement(
            dry_run_plan
        )
    )
    operator_statement_matched = bool(
        operator_approved_live_evidence_runner_real_dry_run
        and str(operator_statement) == required_statement
    )
    if not operator_approved_live_evidence_runner_real_dry_run:
        errors.append("operator_live_evidence_runner_real_dry_run_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_live_evidence_runner_real_dry_run_statement_mismatch")

    adapter_result = {}
    final_audit = {}
    if sources_ready and operator_statement_matched:
        adapter_preview = build_launcher_update_approved_live_evidence_runner_adapter(
            vault,
            **source_inputs,
            generated_at=timestamp,
        )
        adapter_statement = (
            required_update_approved_live_evidence_runner_adapter_operator_statement(
                adapter_preview["adapter_plan"]
            )
        )
        adapter_result = build_launcher_update_approved_live_evidence_runner_adapter(
            vault,
            **source_inputs,
            operator_approved_live_evidence_runner_adapter=True,
            operator_statement=adapter_statement,
            generated_at=timestamp,
        )
        if adapter_result.get("warnings"):
            warnings.extend(str(item) for item in adapter_result.get("warnings") or [])
        if adapter_result.get("errors"):
            errors.extend(f"adapter:{item}" for item in adapter_result.get("errors") or [])
        if adapter_result.get("governed_live_completion_evidence_packet_ready"):
            final_audit = build_launcher_update_final_production_auto_update_closeout_audit(
                vault,
                production_primary_closeout_after_source_recovery_proof=production_primary_closeout_after_source_recovery_proof,
                live_completion_evidence=adapter_result[
                    "governed_live_completion_evidence_packet"
                ],
                generated_at=timestamp,
            )
            if final_audit.get("warnings"):
                warnings.extend(str(item) for item in final_audit.get("warnings") or [])

    adapter_packet_ready = bool(
        adapter_result.get("governed_live_completion_evidence_packet_ready")
    )
    final_audit_ready = bool(final_audit.get("production_auto_update_complete"))
    requirement_checks = [
        {
            "id": item["id"],
            "passed": item["ready"],
            "source": item["surface"],
        }
        for item in source_statuses
    ]
    requirement_checks.extend(
        [
            {
                "id": "operator_statement_matched",
                "passed": operator_statement_matched,
                "source": "operator",
            },
            {
                "id": "approved_live_evidence_runner_adapter_packet_ready",
                "passed": adapter_packet_ready,
                "source": APPROVED_LIVE_EVIDENCE_RUNNER_ADAPTER_SURFACE_ID,
            },
            {
                "id": "final_closeout_audit_ready",
                "passed": final_audit_ready,
                "source": FINAL_PRODUCTION_AUTO_UPDATE_CLOSEOUT_AUDIT_SURFACE_ID,
            },
        ]
    )
    blockers = [item["id"] for item in requirement_checks if not item["passed"]]
    dry_run_ready = bool(
        sources_ready
        and operator_statement_matched
        and adapter_packet_ready
        and not any(str(item).startswith("adapter:") for item in errors)
    )

    status = "launcher_update_approved_live_evidence_runner_real_dry_run_blocked"
    if sources_ready and not operator_statement_matched:
        status = "launcher_update_approved_live_evidence_runner_real_dry_run_pending_approval"
    if sources_ready and operator_statement_matched and not adapter_packet_ready:
        status = "launcher_update_approved_live_evidence_runner_real_dry_run_adapter_blocked"
    if dry_run_ready:
        status = "launcher_update_approved_live_evidence_runner_real_dry_run_packet_ready"
    if final_audit_ready:
        status = "launcher_update_approved_live_evidence_runner_real_dry_run_final_audit_ready"

    proof = {
        "ok": dry_run_ready,
        "surface": APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SURFACE_ID,
        "schema_version": APPROVED_LIVE_EVIDENCE_RUNNER_REAL_DRY_RUN_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "dry_run_plan": dry_run_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "operator_approved_live_evidence_runner_real_dry_run": bool(
            operator_approved_live_evidence_runner_real_dry_run
        ),
        "current_vault_source_proofs_collected": default_source_readback_performed,
        "source_digest_checks": source_digest_checks,
        "source_digest_consistency_closeout_ready": source_digest_consistency_closeout_ready,
        "normalized_blocked_receipt_digest_count": normalized_blocked_receipt_digest_count,
        "ready_digest_mismatch_rejected": bool(ready_digest_mismatch_errors),
        "source_proof_checks": [
            {
                key: value
                for key, value in item.items()
                if key != "proof"
            }
            for item in source_statuses
        ],
        "sources_ready": sources_ready,
        "approved_live_evidence_runner_adapter": adapter_result,
        "approved_live_evidence_runner_adapter_ready": bool(
            adapter_result.get("ok")
        ),
        "governed_live_completion_evidence_packet": (
            adapter_result.get("governed_live_completion_evidence_packet") or {}
        ),
        "governed_live_completion_evidence_packet_ready": adapter_packet_ready,
        "final_production_auto_update_closeout_audit": final_audit,
        "final_production_auto_update_closeout_audit_ready": final_audit_ready,
        "final_audit_production_auto_update_complete": final_audit_ready,
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "feeds_final_production_auto_update_closeout_audit": adapter_packet_ready,
        "download_performed_by_dry_run": False,
        "installer_launch_performed_by_dry_run": False,
        "primary_replacement_performed_by_dry_run": False,
        "startup_mutation_performed_by_dry_run": False,
        "source_write_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": not final_audit_ready,
        "next_required_step": (
            "review_final_closeout_audit_and_promote_completion_only_if_real_receipts"
            if final_audit_ready
            else (
                "feed_real_adapter_packet_to_final_closeout_audit"
                if adapter_packet_ready
                else "collect_real_signed_manifest_download_installer_relaunch_startup_receipts"
            )
        ),
        "authority": _authority(
            approved_live_evidence_runner_real_dry_run_built=True,
            approved_live_evidence_runner_real_dry_run_source_proofs_checked=True,
            approved_live_evidence_runner_real_dry_run_adapter_packet_ready=adapter_packet_ready,
            approved_live_evidence_runner_real_dry_run_final_audit_ready=final_audit_ready,
            approved_live_evidence_runner_real_dry_run_settings_install_control_exposed=False,
        ),
        "readiness": _readiness(),
    }
    proof["approved_live_evidence_runner_real_dry_run_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "approved_live_evidence_runner_real_dry_run_digest_sha256",
        )
    )
    return proof


def build_launcher_update_final_production_auto_update_closeout_audit(
    vault_root,
    *,
    production_primary_closeout_after_source_recovery_proof=None,
    live_completion_evidence=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []

    if production_primary_closeout_after_source_recovery_proof is None:
        production_primary_closeout_after_source_recovery_proof = (
            build_launcher_update_production_primary_closeout_after_source_recovery_proof(
                vault,
                generated_at=timestamp,
            )
        )
        errors.append(
            "production_primary_closeout_after_source_recovery_proof_required"
        )

    primary_closeout_proof = _extension_unwrap_api_data(
        production_primary_closeout_after_source_recovery_proof,
        "launcher_update_production_primary_closeout_after_source_recovery_proof",
    )
    primary_closeout_proof = _extension_unwrap_api_data(
        primary_closeout_proof or {},
        PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID,
    )
    if not isinstance(primary_closeout_proof, dict):
        primary_closeout_proof = {}
    if primary_closeout_proof.get("warnings"):
        warnings.extend(
            str(item) for item in primary_closeout_proof.get("warnings") or []
        )
    if not primary_closeout_proof:
        errors.append("production_primary_closeout_after_source_recovery_malformed")
    elif (
        primary_closeout_proof.get("surface")
        != PRODUCTION_PRIMARY_CLOSEOUT_AFTER_SOURCE_RECOVERY_SURFACE_ID
    ):
        errors.append("production_primary_closeout_after_source_recovery_surface_mismatch")

    primary_closeout_digest_key = (
        "production_primary_closeout_after_source_recovery_digest_sha256"
    )
    primary_closeout_digest = str(
        primary_closeout_proof.get(primary_closeout_digest_key) or ""
    )
    primary_closeout_digest_matched = bool(
        primary_closeout_digest
        and primary_closeout_digest
        == _extension_digest_without(
            primary_closeout_proof,
            primary_closeout_digest_key,
        )
    )
    if primary_closeout_proof and not primary_closeout_digest_matched:
        errors.append("production_primary_closeout_after_source_recovery_digest_mismatch")

    primary_closeout_ready = bool(
        primary_closeout_digest_matched
        and primary_closeout_proof.get("ok")
        and primary_closeout_proof.get(
            "production_primary_closeout_after_source_recovery_ready_for_final_audit"
        )
        and primary_closeout_proof.get("source_closeout_ready")
        and primary_closeout_proof.get("primary_relaunch_receipt_boundary_ready")
    )
    if primary_closeout_proof and not primary_closeout_ready:
        errors.append("production_primary_closeout_after_source_recovery_not_ready")

    evidence = live_completion_evidence or {}
    evidence = _extension_unwrap_api_data(
        evidence,
        "launcher_update_governed_live_completion_evidence_packet",
    )
    evidence = _extension_unwrap_api_data(
        evidence,
        GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID,
    )
    governed_live_completion_evidence_packet = {}
    governed_live_completion_evidence_packet_digest_matched = False
    if (
        isinstance(evidence, dict)
        and evidence.get("surface")
        == GOVERNED_LIVE_COMPLETION_EVIDENCE_PACKET_SURFACE_ID
    ):
        governed_live_completion_evidence_packet = evidence
        packet_digest_key = "governed_live_completion_evidence_packet_digest_sha256"
        packet_digest = str(governed_live_completion_evidence_packet.get(packet_digest_key) or "")
        governed_live_completion_evidence_packet_digest_matched = bool(
            packet_digest
            and packet_digest
            == _extension_digest_without(
                governed_live_completion_evidence_packet,
                packet_digest_key,
            )
        )
        if not governed_live_completion_evidence_packet_digest_matched:
            errors.append("governed_live_completion_evidence_packet_digest_mismatch")
            evidence = {}
        elif not (
            governed_live_completion_evidence_packet.get("ok")
            and governed_live_completion_evidence_packet.get(
                "live_completion_evidence_verified"
            )
        ):
            errors.append("governed_live_completion_evidence_packet_not_ready")
            evidence = {}
        else:
            evidence = (
                governed_live_completion_evidence_packet.get(
                    "live_completion_evidence"
                )
                or {}
            )
    if not isinstance(evidence, dict):
        evidence = {}
        errors.append("live_completion_evidence_malformed")
    if not evidence:
        errors.append("live_completion_evidence_required")

    evidence_digest_key = "final_production_auto_update_live_evidence_digest_sha256"
    evidence_digest = str(evidence.get(evidence_digest_key) or "")
    evidence_digest_matched = bool(
        evidence_digest
        and evidence_digest == _extension_digest_without(evidence, evidence_digest_key)
    )
    if evidence and not evidence_digest_matched:
        errors.append("live_completion_evidence_digest_mismatch")

    required_true_evidence_fields = list(
        FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS
    )
    required_false_evidence_fields = list(
        FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS
    )

    requirement_checks = [
        {
            "id": "production_primary_closeout_after_source_recovery_ready",
            "passed": primary_closeout_ready,
            "source": "production_primary_closeout_after_source_recovery_proof",
        },
        {
            "id": "production_primary_closeout_digest_matched",
            "passed": primary_closeout_digest_matched,
            "source": "production_primary_closeout_after_source_recovery_proof",
        },
        {
            "id": "live_completion_evidence_digest_matched",
            "passed": evidence_digest_matched,
            "source": "live_completion_evidence",
        },
    ]
    for field in required_true_evidence_fields:
        passed = bool(evidence.get(field))
        requirement_checks.append(
            {"id": field, "passed": passed, "source": "live_completion_evidence"}
        )
        if evidence and not passed:
            errors.append(f"{field}_required")
    for field in required_false_evidence_fields:
        passed = not bool(evidence.get(field))
        requirement_checks.append(
            {"id": f"{field}_must_be_false", "passed": passed, "source": "live_completion_evidence"}
        )
        if evidence and not passed:
            errors.append(f"{field}_must_be_false")

    blockers = [item["id"] for item in requirement_checks if not item["passed"]]
    live_completion_evidence_verified = bool(
        evidence_digest_matched
        and evidence
        and all(bool(evidence.get(field)) for field in required_true_evidence_fields)
        and all(not bool(evidence.get(field)) for field in required_false_evidence_fields)
    )
    production_auto_update_complete = bool(
        primary_closeout_ready and live_completion_evidence_verified and not blockers
    )

    status = "launcher_update_final_production_auto_update_closeout_audit_blocked"
    if primary_closeout_ready and not evidence:
        status = (
            "launcher_update_final_production_auto_update_closeout_audit_"
            "live_completion_evidence_required"
        )
    elif production_auto_update_complete:
        status = (
            "launcher_update_final_production_auto_update_closeout_audit_"
            "verified_complete"
        )

    proof = {
        "ok": production_auto_update_complete,
        "surface": FINAL_PRODUCTION_AUTO_UPDATE_CLOSEOUT_AUDIT_SURFACE_ID,
        "schema_version": FINAL_PRODUCTION_AUTO_UPDATE_CLOSEOUT_AUDIT_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "production_primary_closeout_after_source_recovery_status": (
            primary_closeout_proof.get("status", "")
        ),
        "production_primary_closeout_after_source_recovery_digest_sha256": (
            primary_closeout_digest
        ),
        "production_primary_closeout_after_source_recovery_digest_matched": (
            primary_closeout_digest_matched
        ),
        "production_primary_closeout_after_source_recovery_ready_for_final_audit": (
            primary_closeout_ready
        ),
        "governed_live_completion_evidence_packet_supplied": bool(
            governed_live_completion_evidence_packet
        ),
        "governed_live_completion_evidence_packet_digest_matched": (
            governed_live_completion_evidence_packet_digest_matched
        ),
        "live_completion_evidence_digest_sha256": evidence_digest,
        "live_completion_evidence_digest_matched": evidence_digest_matched,
        "live_completion_evidence_verified": live_completion_evidence_verified,
        "requirement_checks": requirement_checks,
        "blocking_requirements": blockers,
        "production_primary_closeout_after_source_recovery_proof": primary_closeout_proof,
        "live_completion_evidence": evidence,
        "github_release_publication_verified": bool(
            evidence.get("github_release_publication_verified")
        ),
        "live_release_manifest_readback_verified": bool(
            evidence.get("live_release_manifest_readback_verified")
        ),
        "live_binary_download_verified": bool(
            evidence.get("live_binary_download_verified")
        ),
        "downloaded_artifact_signature_verified": bool(
            evidence.get("downloaded_artifact_signature_verified")
        ),
        "chaseos_installer_signed_output_verified": bool(
            evidence.get("chaseos_installer_signed_output_verified")
        ),
        "chaseos_installer_launch_receipt_verified": bool(
            evidence.get("chaseos_installer_launch_receipt_verified")
        ),
        "primary_exe_replacement_verified_live": bool(
            evidence.get("primary_exe_replacement_verified_live")
        ),
        "primary_relaunch_verified_live": bool(
            evidence.get("primary_relaunch_verified_live")
        ),
        "startup_background_prompt_verified": bool(
            evidence.get("startup_background_prompt_verified")
        ),
        "prompted_install_flow_verified": bool(
            evidence.get("prompted_install_flow_verified")
        ),
        "silent_install_performed": bool(evidence.get("silent_install_performed")),
        "helper_launch_performed_by_this_proof": False,
        "installer_launch_performed_by_this_proof": False,
        "download_performed_by_this_proof": False,
        "github_mutation_performed_by_this_proof": False,
        "source_write_performed_by_this_proof": False,
        "primary_exe_replacement_performed_by_this_proof": False,
        "settings_install_control_exposed": False,
        "settings_write_control_exposed": False,
        "helper_launch_previously_verified_by_evidence": bool(
            evidence.get("chaseos_installer_launch_receipt_verified")
        ),
        "primary_exe_replacement_previously_verified_by_evidence": bool(
            evidence.get("primary_exe_replacement_verified_live")
        ),
        "requires_final_update_closeout_audit": False,
        "production_auto_update_complete": production_auto_update_complete,
        "final_auto_update_closeout_blocked": not production_auto_update_complete,
        "next_required_step": (
            "production_auto_update_complete"
            if production_auto_update_complete
            else (
                "supply_live_completion_evidence"
                if primary_closeout_ready
                else "complete_production_primary_closeout_after_source_recovery"
            )
        ),
        "authority": _authority(
            final_production_auto_update_closeout_audit_built=True,
            final_production_auto_update_closeout_audit_primary_closeout_ready=primary_closeout_ready,
            final_production_auto_update_closeout_audit_live_evidence_verified=live_completion_evidence_verified,
            final_production_auto_update_closeout_audit_production_auto_update_complete=production_auto_update_complete,
            final_production_auto_update_closeout_audit_settings_install_control_exposed=False,
            final_production_auto_update_closeout_audit_helper_launch_performed_by_this_proof=False,
            final_production_auto_update_closeout_audit_primary_replacement_performed_by_this_proof=False,
        ),
        "readiness": _readiness(),
    }
    proof["final_production_auto_update_closeout_audit_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "final_production_auto_update_closeout_audit_digest_sha256",
        )
    )
    return proof


def _normal_source_candidate_restore_target_descriptor(
    *,
    restore_root,
    role,
    target_value,
):
    target = _Path(target_value or "")
    if target.is_absolute():
        target_path = target.resolve()
        relative_target = str(target_path)
    else:
        target_path = (restore_root / target).resolve()
        relative_target = str(target)
    descriptor = {
        "role": role,
        "target": str(target_value or ""),
        "target_relative_path": relative_target,
        "resolved_target_path": str(target_path),
        "inside_restore_root": _extension_path_is_relative_to(target_path, restore_root),
        "extension_allowed": target_path.suffix.lower() == ".py",
        "target_exists_before_restore": target_path.exists(),
        "target_is_file_or_missing": (not target_path.exists()) or target_path.is_file(),
        "errors": [],
    }
    if not descriptor["inside_restore_root"]:
        descriptor["errors"].append("restore_target_outside_restore_root")
    if not descriptor["extension_allowed"]:
        descriptor["errors"].append("restore_target_extension_not_py")
    if not descriptor["target_is_file_or_missing"]:
        descriptor["errors"].append("restore_target_not_file")
    return descriptor


def _normal_source_candidate_restore_targets(restore_root, restore_targets_by_role):
    default_targets = _normal_source_candidate_restore_default_targets()
    supplied_targets = restore_targets_by_role or {}
    targets = {}
    for role, default_target in default_targets.items():
        targets[role] = supplied_targets.get(role, default_target)
    return targets


def _normal_source_candidate_verified_descriptor(candidate_proof, role):
    candidates = (
        (candidate_proof or {}).get("candidates")
        or ((candidate_proof or {}).get("candidate_set") or {}).get("candidates")
        or {}
    )
    for descriptor in candidates.get(role, []) or []:
        if descriptor.get("candidate_verification_passed"):
            return descriptor
    return {}


def _normal_source_candidate_restore_plan(
    *,
    vault,
    candidate_verification_proof,
    restore_root,
    restore_targets_by_role,
    required_symbols_by_role,
):
    roles = [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]
    required_symbols = (
        required_symbols_by_role
        or (candidate_verification_proof.get("candidate_set") or {}).get(
            "required_symbols_by_role"
        )
        or _normal_source_candidate_default_required_symbols()
    )
    restore_targets = _normal_source_candidate_restore_targets(
        restore_root,
        restore_targets_by_role,
    )
    role_plan = {}
    errors = []
    for role in roles:
        candidate = _normal_source_candidate_verified_descriptor(
            candidate_verification_proof,
            role,
        )
        if not candidate:
            errors.append(f"{role}_verified_candidate_required")
            role_plan[role] = {
                "role": role,
                "candidate": {},
                "target": {},
                "ready": False,
                "errors": [f"{role}_verified_candidate_required"],
            }
            continue
        rechecked = _normal_source_candidate_verification_descriptor(
            vault=vault,
            role=role,
            path=candidate.get("path"),
            required_symbols=required_symbols.get(role, []),
        )
        target = _normal_source_candidate_restore_target_descriptor(
            restore_root=restore_root,
            role=role,
            target_value=restore_targets.get(role),
        )
        item_errors = []
        if not rechecked.get("candidate_verification_passed"):
            item_errors.append("candidate_revalidation_failed")
        if rechecked.get("sha256") != candidate.get("sha256"):
            item_errors.append("candidate_hash_mismatch")
        if target.get("errors"):
            item_errors.extend(target["errors"])
        if (
            rechecked.get("resolved_path")
            and rechecked.get("resolved_path") == target.get("resolved_target_path")
        ):
            item_errors.append("candidate_source_and_restore_target_must_differ")
        if item_errors:
            errors.append(f"{role}_restore_plan_invalid")
        role_plan[role] = {
            "role": role,
            "candidate": {
                "path": candidate.get("path"),
                "resolved_path": rechecked.get("resolved_path"),
                "sha256": rechecked.get("sha256"),
                "size_bytes": rechecked.get("size_bytes"),
                "candidate_status": rechecked.get("candidate_status"),
                "candidate_verification_passed": rechecked.get(
                    "candidate_verification_passed"
                ),
            },
            "target": target,
            "ready": not item_errors,
            "errors": item_errors,
        }
    plan_ready = not errors and all(item.get("ready") for item in role_plan.values())
    plan = {
        "schema_version": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SCHEMA_VERSION,
        "surface": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SURFACE_ID,
        "candidate_verification_digest_sha256": candidate_verification_proof.get(
            "normal_source_candidate_verification_digest_sha256"
        ),
        "candidate_set_digest_sha256": (
            candidate_verification_proof.get("candidate_set") or {}
        ).get("candidate_set_digest_sha256"),
        "restore_root": str(restore_root),
        "roles": roles,
        "role_plan": role_plan,
        "plan_ready": plan_ready,
        "errors": errors,
        "forbidden_behaviors": [
            "decompile_bytecode",
            "execute_candidate_source",
            "launch_installer",
            "replace_primary_exe",
            "mutate_startup",
            "publish_github_release",
        ],
    }
    plan["restore_plan_digest_sha256"] = _extension_digest_without(
        plan,
        "restore_plan_digest_sha256",
    )
    return plan


def required_update_normal_source_candidate_restore_operator_statement(restore_plan):
    digest = str(
        (restore_plan or {}).get("restore_plan_digest_sha256")
        or _extension_digest_without(restore_plan or {}, "restore_plan_digest_sha256")
    )
    return f"{NORMAL_SOURCE_CANDIDATE_RESTORE_OPERATOR_STATEMENT_PREFIX} {digest}"


def build_launcher_update_normal_source_candidate_restore_executor_proof(
    vault_root,
    *,
    candidate_verification_proof=None,
    restore_root=None,
    restore_targets_by_role=None,
    required_symbols_by_role=None,
    operator_approved_restore=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    errors = []
    warnings = []
    source_restore_results = {}
    source_write_performed = False

    candidate_proof = _extension_unwrap_api_data(
        candidate_verification_proof or {},
        "launcher_update_normal_source_candidate_verification_proof",
    )
    candidate_proof = _extension_unwrap_api_data(
        candidate_proof or {},
        NORMAL_SOURCE_CANDIDATE_VERIFICATION_SURFACE_ID,
    )
    if not candidate_proof:
        errors.append("candidate_verification_proof_required")
    elif candidate_proof.get("surface") != NORMAL_SOURCE_CANDIDATE_VERIFICATION_SURFACE_ID:
        errors.append("candidate_verification_proof_surface_mismatch")
    elif not (
        candidate_proof.get("ok")
        and candidate_proof.get("source_restoration_candidate_verification_ready")
    ):
        errors.append("candidate_verification_proof_not_ready")

    candidate_proof_digest = ""
    candidate_proof_digest_valid = False
    if candidate_proof:
        candidate_proof_digest = str(
            candidate_proof.get("normal_source_candidate_verification_digest_sha256")
            or ""
        )
        recomputed_candidate_proof_digest = _extension_digest_without(
            candidate_proof,
            "normal_source_candidate_verification_digest_sha256",
        )
        candidate_proof_digest_valid = bool(
            candidate_proof_digest
            and candidate_proof_digest == recomputed_candidate_proof_digest
        )
        if not candidate_proof_digest_valid:
            errors.append("candidate_verification_proof_digest_mismatch")

    restore_root_explicit = restore_root is not None
    resolved_restore_root = _Path(restore_root).resolve() if restore_root else _Path()
    restore_root_valid = False
    if not restore_root_explicit:
        errors.append("restore_root_required")
    else:
        restore_root_valid = _extension_path_is_relative_to(resolved_restore_root, vault)
        if not restore_root_valid:
            errors.append("restore_root_outside_vault_root")

    restore_plan = {
        "schema_version": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SCHEMA_VERSION,
        "surface": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SURFACE_ID,
        "restore_root": str(resolved_restore_root) if restore_root_explicit else "",
        "plan_ready": False,
        "errors": list(errors),
        "restore_plan_digest_sha256": "",
    }
    if candidate_proof and candidate_proof_digest_valid and restore_root_valid:
        restore_plan = _normal_source_candidate_restore_plan(
            vault=vault,
            candidate_verification_proof=candidate_proof,
            restore_root=resolved_restore_root,
            restore_targets_by_role=restore_targets_by_role,
            required_symbols_by_role=required_symbols_by_role,
        )
        errors.extend(restore_plan.get("errors") or [])

    required_statement = (
        required_update_normal_source_candidate_restore_operator_statement(restore_plan)
    )
    operator_statement_matched = bool(
        operator_approved_restore and str(operator_statement) == required_statement
    )
    if not operator_approved_restore:
        errors.append("operator_source_restore_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_source_restore_statement_mismatch")

    restore_plan_ready = bool(restore_plan.get("plan_ready"))
    if restore_plan_ready and operator_statement_matched:
        for role, item in (restore_plan.get("role_plan") or {}).items():
            source_path = _Path(item["candidate"]["resolved_path"])
            target_path = _Path(item["target"]["resolved_target_path"])
            before_hash = ""
            before_size = 0
            if target_path.exists() and target_path.is_file():
                before_payload = target_path.read_bytes()
                before_hash = _wrapper_hashlib.sha256(before_payload).hexdigest()
                before_size = len(before_payload)
            payload = source_path.read_bytes()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(payload)
            after_payload = target_path.read_bytes()
            after_hash = _wrapper_hashlib.sha256(after_payload).hexdigest()
            write_verified = after_hash == item["candidate"]["sha256"]
            if not write_verified:
                errors.append(f"{role}_restore_write_hash_mismatch")
            source_restore_results[role] = {
                "role": role,
                "source_path": str(source_path),
                "target_path": str(target_path),
                "before_sha256": before_hash,
                "before_size_bytes": before_size,
                "after_sha256": after_hash,
                "after_size_bytes": len(after_payload),
                "write_performed": True,
                "write_verified": write_verified,
            }
        source_write_performed = bool(
            source_restore_results
            and all(item.get("write_verified") for item in source_restore_results.values())
        )

    status = "launcher_update_normal_source_candidate_restore_executor_blocked"
    if restore_plan_ready and not operator_statement_matched:
        status = "launcher_update_normal_source_candidate_restore_executor_pending_approval"
    if source_write_performed:
        status = "launcher_update_normal_source_candidate_restore_executor_restored"

    proof = {
        "ok": source_write_performed,
        "surface": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SURFACE_ID,
        "schema_version": NORMAL_SOURCE_CANDIDATE_RESTORE_EXECUTOR_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "candidate_verification_proof_digest_valid": candidate_proof_digest_valid,
        "candidate_verification_digest_sha256": candidate_proof_digest,
        "restore_plan": restore_plan,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "restore_plan_ready": restore_plan_ready,
        "source_restore_performed": source_write_performed,
        "source_write_performed": source_write_performed,
        "source_file_replacement_performed": source_write_performed,
        "source_restore_results": source_restore_results,
        "normal_source_restoration_ready": False,
        "source_rewrite_from_bytecode_performed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "authority": _authority(
            normal_source_candidate_restore_executor_proof_built=True,
            normal_source_candidate_restore_executor_ready=source_write_performed,
            normal_source_candidate_restore_source_write_performed=source_write_performed,
            normal_source_candidate_restore_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["normal_source_candidate_restore_executor_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "normal_source_candidate_restore_executor_digest_sha256",
        )
    )
    return proof


def _source_regeneration_recovered_bytecode_inputs(vault):
    return {
        "launcher_update_check": _Path(__file__).with_name("recovery")
        / "launcher_update_check_recovered_20260525_012321.cpython-314.bytecode",
        "studio_shell_api": _Path(__file__).with_name("recovery")
        / "api_recovered_20260525_012321.cpython-314.bytecode",
        "launcher_update_tests": _Path(__file__).with_name("recovery")
        / "test_launcher_update_check_recovered_20260525_025258.cpython-314.bytecode",
    }


def _source_regeneration_code_object_names(code):
    names = []
    for item in getattr(code, "co_consts", ()) or ():
        if hasattr(item, "co_name"):
            names.append(str(item.co_name))
            names.extend(_source_regeneration_code_object_names(item))
    return names


def _source_regeneration_bytecode_descriptor(role, path, vault):
    descriptor = {
        "role": role,
        "path": str(path),
        "resolved_path": "",
        "exists": False,
        "inside_vault_root": False,
        "size_bytes": 0,
        "sha256": "",
        "marshal_load_ok": False,
        "code_filename": "",
        "code_object_count": 0,
        "code_object_names_sample": [],
        "errors": [],
    }
    bytecode_path = _Path(path)
    descriptor["exists"] = bytecode_path.exists()
    if not descriptor["exists"]:
        descriptor["errors"].append("bytecode_artifact_missing")
        return descriptor
    try:
        resolved = bytecode_path.resolve()
    except OSError:
        resolved = bytecode_path
    descriptor["resolved_path"] = str(resolved)
    descriptor["inside_vault_root"] = _extension_path_is_relative_to(resolved, vault)
    if not descriptor["inside_vault_root"]:
        descriptor["errors"].append("bytecode_artifact_outside_vault_root")
    payload = bytecode_path.read_bytes()
    descriptor["size_bytes"] = len(payload)
    descriptor["sha256"] = _wrapper_hashlib.sha256(payload).hexdigest()
    try:
        code = _marshal.loads(payload[16:])
        descriptor["marshal_load_ok"] = True
        descriptor["code_filename"] = str(getattr(code, "co_filename", ""))
        names = _source_regeneration_code_object_names(code)
        descriptor["code_object_count"] = len(names)
        descriptor["code_object_names_sample"] = names[:40]
    except Exception as exc:
        descriptor["errors"].append(f"bytecode_marshal_load_failed:{exc.__class__.__name__}")
    return descriptor


def _source_regeneration_tool_descriptor(command_names, module_names):
    command_descriptors = []
    for command in command_names:
        resolved = _extension_shutil.which(command)
        command_descriptors.append(
            {
                "command": command,
                "available": bool(resolved),
                "resolved_path": str(resolved or ""),
            }
        )
    module_descriptors = []
    for module_name in module_names:
        spec = _extension_importlib_util.find_spec(module_name)
        module_descriptors.append(
            {
                "module": module_name,
                "available": bool(spec),
                "origin": str(getattr(spec, "origin", "") or "") if spec else "",
            }
        )
    return {
        "commands": command_descriptors,
        "modules": module_descriptors,
        "any_command_available": any(item["available"] for item in command_descriptors),
        "any_module_available": any(item["available"] for item in module_descriptors),
    }


def build_launcher_update_source_regeneration_readiness(
    vault_root,
    *,
    decompiler_command_candidates=None,
    decompiler_module_candidates=None,
    recovered_bytecode_inputs=None,
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    source_readiness = build_launcher_update_normal_source_restoration_readiness(
        vault,
        generated_at=timestamp,
    )
    bytecode_inputs = {
        role: _source_regeneration_bytecode_descriptor(role, path, vault)
        for role, path in (
            recovered_bytecode_inputs
            or _source_regeneration_recovered_bytecode_inputs(vault)
        ).items()
    }
    bytecode_artifacts_ready = all(
        item.get("exists")
        and item.get("inside_vault_root")
        and item.get("sha256")
        and item.get("marshal_load_ok")
        for item in bytecode_inputs.values()
    )
    tool_status = _source_regeneration_tool_descriptor(
        decompiler_command_candidates or ["pycdc", "uncompyle6", "decompyle3"],
        decompiler_module_candidates or ["uncompyle6", "decompyle3", "xdis"],
    )
    tool_available = bool(
        tool_status.get("any_command_available")
        or tool_status.get("any_module_available")
    )
    normal_source_candidates_available = bool(
        source_readiness.get("normal_source_candidates_available")
    )
    errors = []
    warnings = []
    if not bytecode_artifacts_ready:
        errors.append("recovered_bytecode_artifacts_not_ready")
    if not tool_available:
        errors.append("source_regeneration_tool_unavailable")
    if not normal_source_candidates_available and not tool_available:
        errors.append("authoritative_normal_source_candidates_missing")
    if source_readiness.get("current_source_wrappers_active"):
        warnings.append("current_source_wrappers_still_active")

    regeneration_ready = bool(
        bytecode_artifacts_ready
        and (tool_available or normal_source_candidates_available)
    )
    status = "launcher_update_source_regeneration_readiness_blocked"
    if regeneration_ready:
        status = "launcher_update_source_regeneration_readiness_ready_for_operator_plan"

    readiness = {
        "ok": regeneration_ready,
        "surface": SOURCE_REGENERATION_READINESS_SURFACE_ID,
        "schema_version": SOURCE_REGENERATION_READINESS_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "bytecode_artifacts_ready": bytecode_artifacts_ready,
        "bytecode_inputs": bytecode_inputs,
        "decompiler_tool_available": tool_available,
        "decompiler_tools": tool_status,
        "normal_source_candidates_available": normal_source_candidates_available,
        "source_readiness_status": source_readiness.get("status"),
        "source_regeneration_ready": regeneration_ready,
        "source_regeneration_execution_enabled": False,
        "source_regeneration_execution_performed": False,
        "source_regeneration_output_written": False,
        "source_restore_performed": False,
        "source_write_performed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "required_external_inputs": [
            "authoritative_normal_source_candidates_for_launcher_update_check_and_studio_api",
            "or_operator_approved_local_decompiler_tooling_with_no_secret_or_network_dependency",
            "post_regeneration_candidate_verification_proof",
            "post_regeneration_restore_executor_proof",
            "full_post_restore_launcher_update_regression",
        ],
        "authority": _authority(
            source_regeneration_readiness_built=True,
            source_regeneration_tool_available=tool_available,
            source_regeneration_execution_performed=False,
            source_regeneration_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    readiness["source_regeneration_readiness_digest_sha256"] = (
        _extension_digest_without(
            readiness,
            "source_regeneration_readiness_digest_sha256",
        )
    )
    return readiness


def _source_regeneration_candidate_output_filenames():
    return {
        "launcher_update_check": "launcher_update_check.py",
        "studio_shell_api": "api.py",
        "studio_shell_test_pass10a": "test_pass10a_shell.py",
    }


def _source_regeneration_candidate_output_root_descriptor(vault, candidate_output_root):
    descriptor = {
        "path": str(candidate_output_root or ""),
        "resolved_path": "",
        "exists": False,
        "is_directory": False,
        "inside_vault_root": False,
        "errors": [],
    }
    if not candidate_output_root:
        descriptor["errors"].append("candidate_output_root_required")
        return descriptor
    output_root = _Path(candidate_output_root)
    try:
        resolved = output_root.resolve()
    except OSError:
        resolved = output_root
    descriptor["resolved_path"] = str(resolved)
    descriptor["exists"] = output_root.exists()
    descriptor["is_directory"] = (not descriptor["exists"]) or output_root.is_dir()
    descriptor["inside_vault_root"] = _extension_path_is_relative_to(resolved, vault)
    if not descriptor["inside_vault_root"]:
        descriptor["errors"].append("candidate_output_root_outside_vault_root")
    if not descriptor["is_directory"]:
        descriptor["errors"].append("candidate_output_root_not_directory")
    return descriptor


def _source_regeneration_candidate_output_targets(candidate_output_root, roles):
    output_root = _Path(candidate_output_root)
    filenames = _source_regeneration_candidate_output_filenames()
    return {role: output_root / filenames.get(role, f"{role}.py") for role in roles}


def required_update_source_regeneration_runner_operator_statement(execution_plan):
    digest = str(
        (execution_plan or {}).get("execution_plan_digest_sha256")
        or _extension_digest_without(
            execution_plan or {},
            "execution_plan_digest_sha256",
        )
    )
    return f"{SOURCE_REGENERATION_RUNNER_OPERATOR_STATEMENT_PREFIX} {digest}"


def build_launcher_update_source_regeneration_runner_boundary_proof(
    vault_root,
    *,
    source_regeneration_readiness_proof=None,
    candidate_output_root=None,
    source_regeneration_runner=None,
    runner_label="injected_source_regeneration_runner",
    required_symbols_by_role=None,
    operator_approved_source_regeneration=False,
    operator_statement="",
    generated_at=None,
):
    vault = _Path(vault_root).resolve()
    timestamp = _extension_timestamp(generated_at)
    if source_regeneration_readiness_proof is None:
        source_regeneration_readiness_proof = (
            build_launcher_update_source_regeneration_readiness(
                vault,
                generated_at=timestamp,
            )
        )
    readiness_proof = _extension_unwrap_api_data(
        source_regeneration_readiness_proof,
        SOURCE_REGENERATION_READINESS_SURFACE_ID,
    )
    if not isinstance(readiness_proof, dict):
        readiness_proof = {}

    readiness_digest = str(
        readiness_proof.get("source_regeneration_readiness_digest_sha256") or ""
    )
    computed_readiness_digest = _extension_digest_without(
        readiness_proof,
        "source_regeneration_readiness_digest_sha256",
    )
    readiness_digest_matched = bool(
        readiness_digest and readiness_digest == computed_readiness_digest
    )
    readiness_ready = bool(
        readiness_proof.get("ok")
        and readiness_proof.get("source_regeneration_ready")
        and readiness_digest_matched
    )
    roles = [
        "launcher_update_check",
        "studio_shell_api",
        "studio_shell_test_pass10a",
    ]
    required_symbols = (
        required_symbols_by_role
        or _normal_source_candidate_default_required_symbols()
    )
    output_root_descriptor = _source_regeneration_candidate_output_root_descriptor(
        vault,
        candidate_output_root,
    )
    output_targets = _source_regeneration_candidate_output_targets(
        candidate_output_root or "",
        roles,
    )
    output_target_descriptors = {
        role: {
            "role": role,
            "path": str(path),
            "resolved_path": str(path.resolve()) if candidate_output_root else "",
            "exists": path.exists() if candidate_output_root else False,
            "would_write": bool(candidate_output_root),
        }
        for role, path in output_targets.items()
    }
    execution_plan = {
        "schema_version": SOURCE_REGENERATION_RUNNER_BOUNDARY_SCHEMA_VERSION,
        "surface": SOURCE_REGENERATION_RUNNER_BOUNDARY_SURFACE_ID,
        "readiness_digest_sha256": readiness_digest,
        "readiness_status": readiness_proof.get("status"),
        "candidate_output_root": output_root_descriptor,
        "output_targets": output_target_descriptors,
        "runner_label": str(runner_label or ""),
        "candidate_roles": roles,
        "required_symbols_by_role": required_symbols,
        "writes_live_source_targets": False,
        "launches_installer_or_helper": False,
        "replaces_primary_exe": False,
    }
    execution_plan["execution_plan_digest_sha256"] = _extension_digest_without(
        execution_plan,
        "execution_plan_digest_sha256",
    )
    required_statement = required_update_source_regeneration_runner_operator_statement(
        execution_plan
    )
    operator_statement_matched = bool(
        operator_approved_source_regeneration
        and str(operator_statement) == required_statement
    )

    errors = []
    warnings = []
    if not readiness_proof:
        errors.append("source_regeneration_readiness_proof_required")
    if not readiness_digest_matched:
        errors.append("source_regeneration_readiness_digest_mismatch")
    if not readiness_ready:
        errors.append("source_regeneration_readiness_not_ready")
    errors.extend(output_root_descriptor.get("errors") or [])
    if source_regeneration_runner is None:
        errors.append("source_regeneration_runner_required")
    if not operator_approved_source_regeneration:
        errors.append("operator_source_regeneration_approval_required")
    elif not operator_statement_matched:
        errors.append("operator_source_regeneration_statement_mismatch")
    if readiness_proof.get("warnings"):
        warnings.extend(str(item) for item in readiness_proof.get("warnings") or [])

    runner_execution_performed = False
    candidate_source_write_performed = False
    generated_candidate_paths = {}
    generated_candidates = {}
    runner_receipt = {}
    candidate_verification_preview = {}
    candidate_set_complete = False
    plan_ready = bool(
        readiness_ready
        and not output_root_descriptor.get("errors")
        and source_regeneration_runner is not None
    )

    if plan_ready and operator_statement_matched:
        runner_context = {
            "schema_version": SOURCE_REGENERATION_RUNNER_BOUNDARY_SCHEMA_VERSION,
            "surface": SOURCE_REGENERATION_RUNNER_BOUNDARY_SURFACE_ID,
            "generated_at_utc": timestamp,
            "vault_root": str(vault),
            "runner_label": str(runner_label or ""),
            "candidate_output_root": output_root_descriptor.get("resolved_path"),
            "candidate_roles": roles,
            "bytecode_inputs": readiness_proof.get("bytecode_inputs") or {},
            "required_symbols_by_role": required_symbols,
        }
        try:
            runner_receipt = source_regeneration_runner(runner_context)
            runner_execution_performed = True
        except Exception as exc:
            runner_receipt = {
                "ok": False,
                "error": f"source_regeneration_runner_failed:{exc.__class__.__name__}",
            }
            errors.append("source_regeneration_runner_failed")

        generated_sources = {}
        if isinstance(runner_receipt, dict):
            generated_sources = runner_receipt.get("generated_sources") or {}
        if runner_execution_performed:
            missing_roles = [role for role in roles if role not in generated_sources]
            if missing_roles:
                errors.append("source_regeneration_runner_missing_roles")
            pending_writes = {}
            for role in roles:
                raw_source = generated_sources.get(role)
                if isinstance(raw_source, str):
                    payload = raw_source.encode("utf-8")
                elif isinstance(raw_source, bytes):
                    payload = raw_source
                else:
                    payload = b""
                if not payload:
                    errors.append(f"{role}_generated_source_missing")
                    continue
                target_path = output_targets[role]
                if target_path.exists():
                    errors.append(f"{role}_candidate_output_already_exists")
                    continue
                pending_writes[role] = (target_path, payload)
            if not any(error.endswith("_generated_source_missing") for error in errors) and not any(
                error.endswith("_candidate_output_already_exists") for error in errors
            ) and "source_regeneration_runner_missing_roles" not in errors:
                for role, (target_path, payload) in pending_writes.items():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_bytes(payload)
                    generated_candidate_paths[role] = [str(target_path)]
                    generated_candidates[role] = {
                        "role": role,
                        "path": str(target_path),
                        "size_bytes": len(payload),
                        "sha256": _wrapper_hashlib.sha256(payload).hexdigest(),
                    }
                candidate_source_write_performed = bool(generated_candidate_paths)

    if generated_candidate_paths:
        candidate_verification_preview = (
            build_launcher_update_normal_source_candidate_verification_proof(
                vault,
                candidate_paths=generated_candidate_paths,
                required_symbols_by_role=required_symbols,
                generated_at=timestamp,
            )
        )
        candidate_set_complete = bool(
            candidate_verification_preview.get("candidate_set_complete")
        )
        if not candidate_set_complete:
            errors.append("generated_candidates_failed_verification_preview")

    status = "launcher_update_source_regeneration_runner_boundary_blocked"
    if plan_ready and not operator_statement_matched:
        status = "launcher_update_source_regeneration_runner_boundary_pending_approval"
    if runner_execution_performed and candidate_source_write_performed and candidate_set_complete:
        status = "launcher_update_source_regeneration_runner_candidates_written"

    proof_ok = bool(
        runner_execution_performed
        and candidate_source_write_performed
        and candidate_set_complete
    )
    proof = {
        "ok": proof_ok,
        "surface": SOURCE_REGENERATION_RUNNER_BOUNDARY_SURFACE_ID,
        "schema_version": SOURCE_REGENERATION_RUNNER_BOUNDARY_SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": errors,
        "warnings": warnings,
        "required_operator_statement": required_statement,
        "operator_statement_matched": operator_statement_matched,
        "source_regeneration_readiness_ready": readiness_ready,
        "source_regeneration_readiness_digest_matched": readiness_digest_matched,
        "execution_plan": execution_plan,
        "runner_label": str(runner_label or ""),
        "runner_execution_performed": runner_execution_performed,
        "runner_receipt": runner_receipt if isinstance(runner_receipt, dict) else {},
        "candidate_output_root": output_root_descriptor,
        "generated_candidate_paths": generated_candidate_paths,
        "generated_candidates": generated_candidates,
        "candidate_verification_preview": candidate_verification_preview,
        "candidate_set_complete": candidate_set_complete,
        "source_regeneration_execution_performed": runner_execution_performed,
        "source_regeneration_output_written": candidate_source_write_performed,
        "candidate_source_write_performed": candidate_source_write_performed,
        "source_write_performed": candidate_source_write_performed,
        "live_source_write_performed": False,
        "source_restore_performed": False,
        "source_file_replacement_performed": False,
        "decompiler_execution_performed": False,
        "candidate_source_execution_performed": False,
        "installer_launch_performed": False,
        "helper_launch_performed": False,
        "primary_exe_replacement_performed": False,
        "production_auto_update_complete": False,
        "final_auto_update_closeout_blocked": True,
        "next_required_step": "verify_generated_candidates_with_digest_bound_candidate_verifier",
        "authority": _authority(
            source_regeneration_runner_boundary_built=True,
            source_regeneration_runner_execution_performed=runner_execution_performed,
            source_regeneration_candidate_write_performed=candidate_source_write_performed,
            source_regeneration_live_source_write_performed=False,
            source_regeneration_runner_final_closeout_blocked=True,
        ),
        "readiness": _readiness(),
    }
    proof["source_regeneration_runner_boundary_digest_sha256"] = (
        _extension_digest_without(
            proof,
            "source_regeneration_runner_boundary_digest_sha256",
        )
    )
    return proof
