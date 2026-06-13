"""Installer/update helper boundary for the ChaseOS updater lane.

This module models the installer/update executable boundary for
`ChaseOS-Installer.exe`.
It can load and validate a helper-plan file envelope, and it now supports one
local-only execution mode for tests: a disposable-target replacement dry run.
That dry run is path-bounded, requires an explicit disposable plan, and refuses
live primary install mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

try:
    from runtime.studio.launcher_update_check import (
        CURRENT_ARTIFACT_NAME,
        CURRENT_VERSION,
        HELPER_BINARY_CONTRACT_SCHEMA_VERSION,
        HELPER_BINARY_NAME,
        HELPER_PLAN_FILE_SCHEMA_VERSION,
        HELPER_PLAN_SCHEMA_VERSION,
        MAX_BINARY_DOWNLOAD_BYTES,
        PRODUCTION_DISPOSABLE_TARGET_EXECUTION_BOUNDARY_SCHEMA_VERSION,
        PRODUCTION_DISPOSABLE_TARGET_EXECUTION_BOUNDARY_SURFACE_ID,
    )
except ImportError:
    # The packaged installer must be able to run without the Studio updater
    # module's recovery bytecode data files. Keep the constants mirrored here so
    # ChaseOS-Installer.exe can execute disposable plans independently.
    CURRENT_ARTIFACT_NAME = "ChaseOS-Studio.exe"
    CURRENT_VERSION = "0.8.2"
    HELPER_BINARY_CONTRACT_SCHEMA_VERSION = "chaser.update_helper_binary_contract.v1"
    HELPER_BINARY_NAME = "ChaseOS-Installer.exe"
    HELPER_PLAN_FILE_SCHEMA_VERSION = "chaser.update_helper_plan_file.v1"
    HELPER_PLAN_SCHEMA_VERSION = "chaser.update_helper_plan.v1"
    MAX_BINARY_DOWNLOAD_BYTES = 536870912
    PRODUCTION_DISPOSABLE_TARGET_EXECUTION_BOUNDARY_SCHEMA_VERSION = (
        "chaser.update_production_disposable_target_execution_boundary.v1"
    )
    PRODUCTION_DISPOSABLE_TARGET_EXECUTION_BOUNDARY_SURFACE_ID = (
        "studio_launcher_update_production_disposable_target_execution_boundary_proof"
    )


MODEL_VERSION = "studio.launcher_update_helper.v1"
SURFACE_ID = "studio_launcher_update_helper_executable_scaffold"
PLAN_CONSUMPTION_DRY_RUN_SURFACE_ID = "studio_launcher_update_helper_plan_consumption_dry_run"
AUDIT_ENVELOPE_PROOF_SURFACE_ID = "studio_launcher_update_helper_audit_envelope_proof"
AUDIT_ENVELOPE_WRITE_PROOF_SURFACE_ID = "studio_launcher_update_helper_audit_envelope_write_proof"
DISPOSABLE_EXECUTION_RECEIPT_VALIDATION_SURFACE_ID = (
    "studio_launcher_update_helper_disposable_execution_receipt_validation"
)
AUDIT_ENVELOPE_SCHEMA_VERSION = "chaser.update_helper_audit_envelope.v1"
DISPOSABLE_EXECUTION_RECEIPT_VALIDATION_SCHEMA_VERSION = (
    "chaser.update_helper_disposable_execution_receipt_validation.v1"
)
INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION = (
    "chaser.installer_disposable_update_plan.v1"
)
INSTALLER_DISPOSABLE_UPDATE_RECEIPT_SCHEMA_VERSION = (
    "chaser.installer_disposable_update_receipt.v1"
)
INSTALLER_DISPOSABLE_UPDATE_MODE = "disposable_target_update"
INSTALLER_DISPOSABLE_UPDATE_RECEIPT_KIND = (
    "chaseos_installer_disposable_update_receipt"
)
AUDIT_ENVELOPE_WRITE_OPERATOR_STATEMENT_PREFIX = (
    "WRITE CHASER UPDATE HELPER AUDIT ENVELOPE PROOF ONLY"
)
MAX_HELPER_PLAN_FILE_BYTES = 256 * 1024
MAX_INSTALLER_DISPOSABLE_PLAN_FILE_BYTES = 256 * 1024


def execute_launcher_update_installer_disposable_update_plan(
    plan_file_path: str | Path,
    *,
    vault_root: str | Path | None = None,
    execute_disposable: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate and optionally execute a disposable update plan.

    This is the first real installer action. It is intentionally narrower than
    a production update: all paths must stay under an explicit disposable target
    root, live install flags must be false, and the current vault's primary
    `dist/studio` artifact is rejected when `vault_root` is supplied.
    """

    timestamp = generated_at or _now_utc()
    plan_path = Path(plan_file_path).resolve()
    vault = Path(vault_root).resolve() if vault_root is not None else None
    errors: list[str] = []
    warnings: list[str] = []
    plan: dict[str, Any] = {}
    receipt_payload: dict[str, Any] = {}
    validation: dict[str, Any] = {
        "plan_file_loaded": False,
        "plan_file_json_valid": False,
        "plan_schema_valid": False,
        "plan_digest_valid": False,
        "target_root_valid": False,
        "all_paths_inside_disposable_root": False,
        "primary_install_mutation_blocked": True,
        "live_install_blocked": True,
        "current_hash_valid": False,
        "staged_hash_valid": False,
    }

    if not plan_path.exists() or not plan_path.is_file():
        errors.append("installer_disposable_plan_file_missing")
    else:
        try:
            raw = plan_path.read_bytes()
        except OSError as exc:
            errors.append(f"installer_disposable_plan_file_read_failed:{type(exc).__name__}")
            raw = b""
        if len(raw) > MAX_INSTALLER_DISPOSABLE_PLAN_FILE_BYTES:
            errors.append("installer_disposable_plan_file_too_large")
        if raw:
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except UnicodeDecodeError:
                errors.append("installer_disposable_plan_file_not_utf8")
            except json.JSONDecodeError:
                errors.append("installer_disposable_plan_file_json_invalid")
            else:
                if not isinstance(parsed, dict):
                    errors.append("installer_disposable_plan_must_be_object")
                else:
                    plan = parsed
                    validation["plan_file_loaded"] = True
                    validation["plan_file_json_valid"] = True

    paths: dict[str, Path] = {}
    target_root = Path(".").resolve()
    if plan:
        if plan.get("schema_version") != INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION:
            errors.append("installer_disposable_plan_schema_mismatch")
        else:
            validation["plan_schema_valid"] = True
        if plan.get("mode") != INSTALLER_DISPOSABLE_UPDATE_MODE:
            errors.append("installer_disposable_plan_mode_mismatch")
        if plan.get("helper_binary_name") != HELPER_BINARY_NAME:
            errors.append("helper_binary_name_mismatch")
        if plan.get("target_artifact_name") != CURRENT_ARTIFACT_NAME:
            errors.append("target_artifact_name_mismatch")
        if plan.get("allow_live_install") is not False:
            errors.append("live_install_must_be_false_for_disposable_update")
            validation["live_install_blocked"] = False
        if plan.get("allow_primary_install_mutation") is not False:
            errors.append("primary_install_mutation_must_be_false_for_disposable_update")
            validation["primary_install_mutation_blocked"] = False
        if plan.get("relaunch_after_update") is not False:
            errors.append("relaunch_after_update_must_be_false_for_disposable_update")

        expected_plan_digest = str(plan.get("plan_digest_sha256") or "").lower()
        if not _is_sha256(expected_plan_digest):
            errors.append("installer_disposable_plan_digest_required")
        elif _stable_digest({key: value for key, value in plan.items() if key != "plan_digest_sha256"}) != expected_plan_digest:
            errors.append("installer_disposable_plan_digest_mismatch")
        else:
            validation["plan_digest_valid"] = True

        target_root_text = str(plan.get("target_root") or "").strip()
        if not target_root_text:
            errors.append("disposable_target_root_required")
        else:
            target_root = Path(target_root_text).resolve()
            if vault is not None and target_root == vault:
                errors.append("disposable_target_root_must_not_be_vault_root")
            if execute_disposable and not target_root.exists():
                errors.append("disposable_target_root_missing")
            if target_root.exists() and not target_root.is_dir():
                errors.append("disposable_target_root_not_directory")
            if not str(plan.get("target_root_kind") or "").lower() == "disposable":
                errors.append("target_root_kind_must_be_disposable")
            validation["target_root_valid"] = (
                not any(error.startswith("disposable_target_root") for error in errors)
                and not any(error.startswith("target_root_kind") for error in errors)
            )

        for key in (
            "current_executable_path",
            "staged_artifact_path",
            "backup_executable_path",
            "receipt_path",
        ):
            value = str(plan.get(key) or "").strip()
            if not value:
                errors.append(f"{key}_required")
                continue
            resolved = Path(value).resolve()
            paths[key] = resolved
            if target_root and not _path_inside(resolved, target_root):
                errors.append(f"{key}_not_inside_disposable_target_root")

        if len(set(str(path) for path in paths.values())) != len(paths):
            errors.append("installer_disposable_plan_paths_must_be_unique")
        if paths.get("current_executable_path") and paths["current_executable_path"].name != CURRENT_ARTIFACT_NAME:
            errors.append("current_executable_name_mismatch")
        if paths.get("staged_artifact_path") and paths["staged_artifact_path"].name != CURRENT_ARTIFACT_NAME:
            errors.append("staged_artifact_name_mismatch")
        if paths.get("receipt_path") and paths["receipt_path"].suffix.lower() != ".json":
            errors.append("receipt_path_must_be_json")
        if vault is not None:
            primary_dist = vault / "dist" / "studio"
            for key, value in paths.items():
                if _path_inside(value, primary_dist):
                    errors.append(f"{key}_must_not_target_primary_dist_artifact")
        validation["all_paths_inside_disposable_root"] = bool(
            paths
            and not [
                error
                for error in errors
                if error.endswith("_not_inside_disposable_target_root")
                or error.endswith("_must_not_target_primary_dist_artifact")
            ]
        )

        current = paths.get("current_executable_path")
        staged = paths.get("staged_artifact_path")
        backup = paths.get("backup_executable_path")
        receipt = paths.get("receipt_path")
        if current is not None:
            if not current.exists() or not current.is_file():
                errors.append("current_executable_missing")
            else:
                current_hash = _sha256_file(current)
                expected_current = str(plan.get("expected_current_sha256") or "").lower()
                if not _is_sha256(expected_current):
                    errors.append("expected_current_sha256_required")
                elif current_hash != expected_current:
                    errors.append("expected_current_sha256_mismatch")
                else:
                    validation["current_hash_valid"] = True
        if staged is not None:
            if not staged.exists() or not staged.is_file():
                errors.append("staged_artifact_missing")
            else:
                staged_hash = _sha256_file(staged)
                expected_staged = str(plan.get("expected_staged_sha256") or "").lower()
                if not _is_sha256(expected_staged):
                    errors.append("expected_staged_sha256_required")
                elif staged_hash != expected_staged:
                    errors.append("expected_staged_sha256_mismatch")
                else:
                    validation["staged_hash_valid"] = True
        if backup is not None and backup.exists():
            errors.append("backup_executable_already_exists")
        if receipt is not None and receipt.exists():
            errors.append("receipt_path_already_exists")

    executable_replacement_performed = False
    backup_created = False
    receipt_written = False
    current_hash_before = ""
    staged_hash = ""
    backup_hash = ""
    current_hash_after = ""

    if not errors and execute_disposable:
        current = paths["current_executable_path"]
        staged = paths["staged_artifact_path"]
        backup = paths["backup_executable_path"]
        receipt = paths["receipt_path"]
        pending = current.with_name(f"{current.name}.chaseos-update-pending")
        if pending.exists():
            errors.append("pending_replacement_path_already_exists")
        elif not _path_inside(pending, target_root):
            errors.append("pending_replacement_path_not_inside_disposable_target_root")
        else:
            try:
                current_hash_before = _sha256_file(current)
                staged_hash = _sha256_file(staged)
                backup.parent.mkdir(parents=True, exist_ok=True)
                receipt.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(current, backup)
                backup_created = True
                backup_hash = _sha256_file(backup)
                shutil.copy2(staged, pending)
                if _sha256_file(pending) != staged_hash:
                    errors.append("pending_replacement_hash_mismatch")
                else:
                    pending.replace(current)
                    executable_replacement_performed = True
                    current_hash_after = _sha256_file(current)
                    if current_hash_after != staged_hash:
                        errors.append("current_executable_after_hash_mismatch")
            except OSError as exc:
                errors.append(f"installer_disposable_update_execution_failed:{type(exc).__name__}")
            finally:
                if pending.exists():
                    try:
                        pending.unlink()
                    except OSError:
                        warnings.append("pending_replacement_cleanup_failed")

        if not errors and executable_replacement_performed:
            receipt_payload = {
                "receipt_kind": INSTALLER_DISPOSABLE_UPDATE_RECEIPT_KIND,
                "schema_version": INSTALLER_DISPOSABLE_UPDATE_RECEIPT_SCHEMA_VERSION,
                "generated_at_utc": timestamp,
                "ok": True,
                "status": "installer_disposable_update_executed",
                "helper_binary_name": HELPER_BINARY_NAME,
                "target_artifact_name": CURRENT_ARTIFACT_NAME,
                "plan_file_path": str(plan_path),
                "plan_digest_sha256": plan.get("plan_digest_sha256", ""),
                "target_root": str(target_root),
                "current_executable_path": str(current),
                "staged_artifact_path": str(staged),
                "backup_executable_path": str(backup),
                "before_current_sha256": current_hash_before,
                "staged_artifact_sha256": staged_hash,
                "backup_sha256": backup_hash,
                "after_target_sha256": current_hash_after,
                "backup_created": backup_created,
                "target_replaced": executable_replacement_performed,
                "replacement_verified": current_hash_after == staged_hash,
                "disposable_target_update_performed": True,
                "primary_install_mutation_performed": False,
                "live_install_performed": False,
                "relaunch_performed": False,
                "github_release_publication_performed": False,
                "startup_mutation_performed": False,
                "production_auto_update_complete": False,
            }
            receipt_payload["receipt_digest_sha256"] = _stable_digest(receipt_payload)
            try:
                receipt.write_text(
                    json.dumps(receipt_payload, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
                receipt_written = True
            except OSError as exc:
                errors.append(f"installer_disposable_receipt_write_failed:{type(exc).__name__}")

    plan_valid = bool(plan and not errors)
    status = "installer_disposable_update_plan_blocked"
    if plan_valid and not execute_disposable:
        status = "installer_disposable_update_plan_validated_execution_disabled"
    elif executable_replacement_performed and receipt_written:
        status = "installer_disposable_update_executed"

    return {
        "ok": bool(plan_valid if not execute_disposable else executable_replacement_performed and receipt_written),
        "surface": "studio_launcher_update_installer_disposable_update_executor",
        "schema_version": INSTALLER_DISPOSABLE_UPDATE_RECEIPT_SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "generated_at_utc": timestamp,
        "status": status,
        "status_label": status.replace("_", " "),
        "vault_root": str(vault) if vault is not None else "",
        "plan_file_path": str(plan_path),
        "plan": plan,
        "validation": validation,
        "receipt_path": str(paths.get("receipt_path") or ""),
        "receipt_payload": receipt_payload,
        "execute_disposable_requested": bool(execute_disposable),
        "backup_created": backup_created,
        "receipt_written": receipt_written,
        "disposable_target_update_performed": bool(executable_replacement_performed),
        "installer_execution_performed": bool(executable_replacement_performed),
        "executable_replacement_performed": bool(executable_replacement_performed),
        "primary_install_mutation_performed": False,
        "live_install_performed": False,
        "relaunch_performed": False,
        "github_release_publication_performed": False,
        "startup_mutation_performed": False,
        "production_auto_update_complete": False,
        "message": (
            "Disposable target update executed by ChaseOS-Installer plan."
            if executable_replacement_performed and receipt_written
            else (
                "Disposable update plan validated; execution was not requested."
                if plan_valid and not execute_disposable
                else "Disposable update plan is blocked; no executable replacement was performed."
            )
        ),
        "errors": list(dict.fromkeys(str(item) for item in errors if str(item))),
        "warnings": list(dict.fromkeys(str(item) for item in warnings if str(item))),
    }


def build_launcher_update_helper_executable_scaffold(
    vault_root: str | Path,
    *,
    plan_file_path: str | Path | None = None,
    approval_digest: str = "",
    parent_pid: int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate a helper-plan file for the future updater helper.

    This is a scaffold only. A valid result means the future helper would have
    enough read-only input shape to proceed to a later execution design pass; it
    does not grant execution, replacement, rollback, relaunch, or host mutation.
    """

    vault = Path(vault_root).resolve()
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    plan_path: Path | None = None
    payload: dict[str, Any] = {}
    helper_plan: dict[str, Any] = {}
    validation: dict[str, Any] = {
        "plan_file_loaded": False,
        "plan_file_json_valid": False,
        "plan_file_schema_valid": False,
        "approval_digest_valid": False,
        "helper_plan_digest_valid": False,
        "plan_file_payload_digest_valid": False,
        "current_executable_hash_valid": False,
        "staged_artifact_hash_valid": False,
        "path_scope_valid": False,
    }

    approval_text = str(approval_digest or "").strip().lower()
    if not approval_text:
        blockers.append("approval_digest_required")
    elif not _is_sha256(approval_text):
        blockers.append("approval_digest_must_be_sha256")

    plan_text = str(plan_file_path or "").strip()
    if not plan_text:
        blockers.append("helper_plan_file_path_required")
    else:
        candidate_plan_path = Path(plan_text)
        plan_path = (candidate_plan_path if candidate_plan_path.is_absolute() else vault / candidate_plan_path).resolve()
        if not _path_inside(plan_path, vault):
            blockers.append("helper_plan_file_path_not_inside_vault")
        if not plan_path.exists() or not plan_path.is_file():
            blockers.append("helper_plan_file_missing")
        else:
            try:
                raw = plan_path.read_bytes()
            except OSError as exc:
                blockers.append(f"helper_plan_file_read_failed:{type(exc).__name__}")
                raw = b""
            if len(raw) > MAX_HELPER_PLAN_FILE_BYTES:
                blockers.append("helper_plan_file_too_large")
            if raw:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except UnicodeDecodeError:
                    blockers.append("helper_plan_file_not_utf8")
                except json.JSONDecodeError:
                    blockers.append("helper_plan_file_json_invalid")
                else:
                    if not isinstance(parsed, dict):
                        blockers.append("helper_plan_file_must_be_object")
                    else:
                        payload = parsed
                        validation["plan_file_loaded"] = True
                        validation["plan_file_json_valid"] = True

    if payload:
        if payload.get("schema_version") != HELPER_PLAN_FILE_SCHEMA_VERSION:
            blockers.append("helper_plan_file_schema_mismatch")
        else:
            validation["plan_file_schema_valid"] = True
        if payload.get("helper_binary_name") != HELPER_BINARY_NAME:
            blockers.append("helper_binary_name_mismatch")
        if payload.get("helper_plan_schema_version") != HELPER_PLAN_SCHEMA_VERSION:
            blockers.append("helper_plan_schema_version_mismatch")
        if payload.get("helper_binary_contract_schema_version") != HELPER_BINARY_CONTRACT_SCHEMA_VERSION:
            blockers.append("helper_binary_contract_schema_version_mismatch")
        if payload.get("plan_file_create_only") is not True:
            blockers.append("helper_plan_file_must_be_create_only")
        if payload.get("plan_file_fixture_only") is not True:
            blockers.append("helper_plan_file_must_be_fixture_only")
        if payload.get("helper_execution_enabled") is not False:
            blockers.append("helper_execution_must_be_disabled")
        if payload.get("replacement_enabled") is not False:
            blockers.append("replacement_must_be_disabled")
        if payload.get("relaunch_enabled") is not False:
            blockers.append("relaunch_must_be_disabled")
        if payload.get("real_executable_replacement_enabled") is not False:
            blockers.append("real_executable_replacement_must_be_disabled")

        expected_approval_digest = str(payload.get("operator_statement_digest_sha256") or "").lower()
        if not _is_sha256(expected_approval_digest):
            blockers.append("operator_statement_digest_required")
        elif approval_text and approval_text != expected_approval_digest:
            blockers.append("approval_digest_mismatch")
        else:
            validation["approval_digest_valid"] = bool(approval_text)

        expected_payload_digest = str(payload.get("plan_file_payload_digest_sha256") or "").lower()
        payload_without_digest = dict(payload)
        payload_without_digest.pop("plan_file_payload_digest_sha256", None)
        if not _is_sha256(expected_payload_digest):
            blockers.append("plan_file_payload_digest_required")
        elif _stable_digest(payload_without_digest) != expected_payload_digest:
            blockers.append("plan_file_payload_digest_mismatch")
        else:
            validation["plan_file_payload_digest_valid"] = True

        raw_helper_plan = payload.get("helper_plan")
        if not isinstance(raw_helper_plan, dict):
            blockers.append("helper_plan_required")
        else:
            helper_plan = raw_helper_plan
            if helper_plan.get("schema_version") != HELPER_PLAN_SCHEMA_VERSION:
                blockers.append("helper_plan_schema_mismatch")
            expected_plan_digest = str(payload.get("helper_plan_digest_sha256") or "").lower()
            actual_plan_digest = str(helper_plan.get("plan_digest_sha256") or "").lower()
            if not _is_sha256(expected_plan_digest) or not _is_sha256(actual_plan_digest):
                blockers.append("helper_plan_digest_required")
            elif expected_plan_digest != actual_plan_digest:
                blockers.append("helper_plan_digest_mismatch")
            elif _stable_digest({key: value for key, value in helper_plan.items() if key != "plan_digest_sha256"}) != actual_plan_digest:
                blockers.append("helper_plan_digest_recalculation_mismatch")
            else:
                validation["helper_plan_digest_valid"] = True

            path_blockers, path_validation = _validate_helper_plan_paths(vault, helper_plan)
            blockers.extend(path_blockers)
            validation.update(path_validation)

    ok = not blockers
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": timestamp,
        "status": "helper_executable_scaffold_ready" if ok else "helper_executable_scaffold_blocked",
        "status_label": (
            "helper_executable_scaffold_ready" if ok else "helper_executable_scaffold_blocked"
        ).replace("_", " "),
        "vault_root": str(vault),
        "helper_binary_name": HELPER_BINARY_NAME,
        "helper_module": "runtime.studio.launcher_update_helper",
        "current_version": CURRENT_VERSION,
        "latest_version": helper_plan.get("latest_version") or payload.get("latest_version") or "",
        "artifact_name": CURRENT_ARTIFACT_NAME,
        "plan_file_path": str(plan_path) if plan_path else "",
        "parent_pid": parent_pid,
        "plan_file_payload": payload,
        "helper_plan": helper_plan,
        "validation": validation,
        "execution_preview": {
            "would_load_plan": bool(payload),
            "would_wait_for_parent_process_exit": False,
            "would_move_rollback": False,
            "would_replace_executable": False,
            "would_verify_replacement_hash": False,
            "would_relaunch": False,
        },
        "command_line_contract": {
            "binary_name": HELPER_BINARY_NAME,
            "arguments": ["--plan", "--parent-pid", "--vault-root", "--approval-digest", "--json"],
            "network_allowed": False,
            "download_allowed": False,
            "replacement_allowed": False,
            "requires_plan_file": True,
            "requires_approval_digest": True,
        },
        "helper_process_launch_enabled": False,
        "helper_execution_enabled": False,
        "replacement_enabled": False,
        "rollback_move_enabled": False,
        "relaunch_enabled": False,
        "binary_download_enabled": False,
        "github_publication_enabled": False,
        "authority": _authority(
            helper_plan_loaded=bool(payload),
            helper_plan_validated=ok,
        ),
        "readiness": _readiness(),
        "message": (
            "Updater helper executable scaffold validated the plan-file envelope only. "
            "No helper process, relaunch, rollback move, or EXE replacement was performed."
            if ok
            else "Updater helper executable scaffold is blocked. No helper process, relaunch, rollback move, or EXE replacement was performed."
        ),
        "errors": list(dict.fromkeys(str(item) for item in blockers if str(item))),
        "warnings": [],
    }


def build_launcher_update_helper_plan_consumption_dry_run(
    vault_root: str | Path,
    *,
    plan_file_path: str | Path | None = None,
    approval_digest: str = "",
    parent_pid: int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic dry-run report for future helper plan consumption.

    This function intentionally stops after validation and future-step planning.
    It never launches `ChaseOS-Installer.exe`, waits for a process, writes audit
    files, moves rollback files, replaces the executable, relaunches Studio,
    downloads binaries, or publishes GitHub releases.
    """

    vault = Path(vault_root).resolve()
    timestamp = generated_at or _now_utc()
    scaffold = build_launcher_update_helper_executable_scaffold(
        vault,
        plan_file_path=plan_file_path,
        approval_digest=approval_digest,
        parent_pid=parent_pid,
        generated_at=timestamp,
    )
    helper_plan = scaffold.get("helper_plan") if isinstance(scaffold.get("helper_plan"), dict) else {}
    plan_digest = str(helper_plan.get("plan_digest_sha256") or "").lower()
    latest_version = str(helper_plan.get("latest_version") or "")
    dry_run_ready = bool(scaffold.get("ok")) and bool(helper_plan)
    errors = list(scaffold.get("errors") or [])

    consumption_steps = _build_plan_consumption_steps(helper_plan) if helper_plan else []
    audit_preview = _build_audit_preview(vault, helper_plan, consumption_steps) if helper_plan else {}
    dry_run_digest = _stable_digest(
        {
            "surface": PLAN_CONSUMPTION_DRY_RUN_SURFACE_ID,
            "helper_binary_name": HELPER_BINARY_NAME,
            "helper_plan_digest_sha256": plan_digest,
            "plan_file_path": scaffold.get("plan_file_path") or "",
            "consumption_steps": consumption_steps,
            "audit_preview": audit_preview,
            "execution_enabled": False,
            "replacement_enabled": False,
            "relaunch_enabled": False,
        }
    )

    return {
        "ok": dry_run_ready,
        "surface": PLAN_CONSUMPTION_DRY_RUN_SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": timestamp,
        "status": (
            "helper_plan_consumption_dry_run_ready"
            if dry_run_ready
            else "helper_plan_consumption_dry_run_blocked"
        ),
        "status_label": (
            "helper plan consumption dry run ready"
            if dry_run_ready
            else "helper plan consumption dry run blocked"
        ),
        "vault_root": str(vault),
        "helper_binary_name": HELPER_BINARY_NAME,
        "helper_module": "runtime.studio.launcher_update_helper",
        "current_version": CURRENT_VERSION,
        "latest_version": latest_version,
        "artifact_name": CURRENT_ARTIFACT_NAME,
        "plan_file_path": scaffold.get("plan_file_path") or "",
        "parent_pid": parent_pid,
        "helper_scaffold": scaffold,
        "helper_plan": helper_plan,
        "helper_plan_digest_sha256": plan_digest,
        "plan_consumption_ready": dry_run_ready,
        "plan_consumption_dry_run_completed": dry_run_ready,
        "dry_run_digest_sha256": dry_run_digest,
        "consumption_steps": consumption_steps,
        "execution_preview": {
            "would_load_plan": bool(helper_plan),
            "would_validate_plan": bool(helper_plan),
            "would_wait_for_parent_process_exit": bool(
                helper_plan.get("main_process_must_exit_before_replace")
            ),
            "would_move_current_executable_to_rollback": bool(
                helper_plan.get("rollback_required_before_replace")
            ),
            "would_move_staged_artifact_into_place": True if helper_plan else False,
            "would_verify_replacement_hash": bool(
                helper_plan.get("replacement_hash_verification_required")
            ),
            "would_relaunch": bool(helper_plan.get("relaunch_command")),
            "all_mutations_disabled": True,
        },
        "rollback_preview": {
            "rollback_path": str(helper_plan.get("rollback_path") or ""),
            "rollback_required_before_replace": bool(
                helper_plan.get("rollback_required_before_replace")
            ),
            "rollback_move_enabled": False,
            "rollback_move_performed": False,
        },
        "replacement_preview": {
            "current_executable_path": str(helper_plan.get("current_executable_path") or ""),
            "staged_artifact_path": str(helper_plan.get("staged_artifact_path") or ""),
            "expected_replacement_sha256": str(
                helper_plan.get("expected_replacement_sha256") or ""
            ),
            "expected_replacement_size_bytes": int(
                helper_plan.get("expected_replacement_size_bytes") or 0
            ),
            "replacement_enabled": False,
            "replacement_performed": False,
        },
        "relaunch_preview": {
            "command": list(helper_plan.get("relaunch_command") or []),
            "relaunch_enabled": False,
            "relaunch_performed": False,
        },
        "audit_preview": audit_preview,
        "helper_process_launch_enabled": False,
        "helper_execution_enabled": False,
        "replacement_enabled": False,
        "rollback_move_enabled": False,
        "relaunch_enabled": False,
        "binary_download_enabled": False,
        "github_publication_enabled": False,
        "authority": _authority(
            helper_plan_loaded=bool(scaffold.get("authority", {}).get("updater_helper_executable_scaffold_plan_loaded")),
            helper_plan_validated=bool(scaffold.get("authority", {}).get("updater_helper_executable_scaffold_plan_validated")),
            plan_consumption_dry_run_completed=dry_run_ready,
        ),
        "readiness": _readiness(),
        "message": (
            "Updater helper plan consumption dry run completed. No helper process, rollback move, relaunch, or EXE replacement was performed."
            if dry_run_ready
            else "Updater helper plan consumption dry run is blocked. No helper process, rollback move, relaunch, or EXE replacement was performed."
        ),
        "errors": list(dict.fromkeys(str(item) for item in errors if str(item))),
        "warnings": [],
    }


def build_launcher_update_helper_audit_envelope_proof(
    vault_root: str | Path,
    *,
    plan_file_path: str | Path | None = None,
    approval_digest: str = "",
    parent_pid: int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the future helper audit envelope in memory only.

    This proof links a validated helper-plan dry run to the audit payload a
    future `ChaseOS-Installer.exe` execution would write. It intentionally does
    not create audit files, launch the helper, move rollback files, replace the
    executable, relaunch Studio, download binaries, or publish GitHub releases.
    """

    vault = Path(vault_root).resolve()
    timestamp = generated_at or _now_utc()
    dry_run = build_launcher_update_helper_plan_consumption_dry_run(
        vault,
        plan_file_path=plan_file_path,
        approval_digest=approval_digest,
        parent_pid=parent_pid,
        generated_at=timestamp,
    )
    helper_plan = dry_run.get("helper_plan") if isinstance(dry_run.get("helper_plan"), dict) else {}
    plan_digest = str(helper_plan.get("plan_digest_sha256") or "").lower()
    latest_version = str(helper_plan.get("latest_version") or "")
    envelope_ready = bool(dry_run.get("ok")) and bool(helper_plan)
    errors = list(dry_run.get("errors") or [])
    audit_path = _build_audit_envelope_path(vault, helper_plan) if helper_plan else ""
    audit_envelope: dict[str, Any] = {}

    if envelope_ready:
        audit_envelope = {
            "schema_version": AUDIT_ENVELOPE_SCHEMA_VERSION,
            "product": "chaser",
            "surface": AUDIT_ENVELOPE_PROOF_SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at_utc": timestamp,
            "helper_binary_name": HELPER_BINARY_NAME,
            "artifact_name": CURRENT_ARTIFACT_NAME,
            "current_version": CURRENT_VERSION,
            "latest_version": latest_version,
            "plan_file_path": dry_run.get("plan_file_path") or "",
            "helper_plan_digest_sha256": plan_digest,
            "dry_run_digest_sha256": dry_run.get("dry_run_digest_sha256") or "",
            "plan_consumption_status": dry_run.get("status") or "",
            "audit_path": audit_path,
            "current_executable_path": str(helper_plan.get("current_executable_path") or ""),
            "staged_artifact_path": str(helper_plan.get("staged_artifact_path") or ""),
            "rollback_path": str(helper_plan.get("rollback_path") or ""),
            "expected_replacement_sha256": str(
                helper_plan.get("expected_replacement_sha256") or ""
            ),
            "expected_replacement_size_bytes": int(
                helper_plan.get("expected_replacement_size_bytes") or 0
            ),
            "consumption_step_ids": [
                str(step.get("step_id") or "") for step in dry_run.get("consumption_steps") or []
            ],
            "execution_performed": False,
            "replacement_performed": False,
            "rollback_move_performed": False,
            "relaunch_performed": False,
            "audit_write_performed": False,
            "binary_download_performed": False,
            "github_release_publication_performed": False,
            "errors": [],
            "warnings": [],
        }
        audit_envelope["audit_envelope_digest_sha256"] = _stable_digest(audit_envelope)

    return {
        "ok": envelope_ready,
        "surface": AUDIT_ENVELOPE_PROOF_SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": timestamp,
        "status": (
            "helper_audit_envelope_proof_ready"
            if envelope_ready
            else "helper_audit_envelope_proof_blocked"
        ),
        "status_label": (
            "helper audit envelope proof ready"
            if envelope_ready
            else "helper audit envelope proof blocked"
        ),
        "vault_root": str(vault),
        "helper_binary_name": HELPER_BINARY_NAME,
        "helper_module": "runtime.studio.launcher_update_helper",
        "current_version": CURRENT_VERSION,
        "latest_version": latest_version,
        "artifact_name": CURRENT_ARTIFACT_NAME,
        "plan_file_path": dry_run.get("plan_file_path") or "",
        "parent_pid": parent_pid,
        "helper_plan": helper_plan,
        "helper_plan_digest_sha256": plan_digest,
        "helper_plan_dry_run": dry_run,
        "dry_run_digest_sha256": dry_run.get("dry_run_digest_sha256") or "",
        "audit_envelope_ready": envelope_ready,
        "audit_envelope_built": envelope_ready,
        "audit_envelope_written": False,
        "audit_path": audit_path,
        "audit_envelope": audit_envelope,
        "audit_envelope_digest_sha256": audit_envelope.get("audit_envelope_digest_sha256", ""),
        "audit_write_enabled": False,
        "audit_write_performed": False,
        "helper_process_launch_enabled": False,
        "helper_execution_enabled": False,
        "replacement_enabled": False,
        "rollback_move_enabled": False,
        "relaunch_enabled": False,
        "binary_download_enabled": False,
        "github_publication_enabled": False,
        "authority": _authority(
            helper_plan_loaded=bool(
                (dry_run.get("authority") or {}).get(
                    "updater_helper_executable_scaffold_plan_loaded"
                )
            ),
            helper_plan_validated=bool(
                (dry_run.get("authority") or {}).get(
                    "updater_helper_executable_scaffold_plan_validated"
                )
            ),
            plan_consumption_dry_run_completed=bool(
                (dry_run.get("authority") or {}).get(
                    "updater_helper_plan_consumption_dry_run_completed"
                )
            ),
            audit_envelope_ready=envelope_ready,
        ),
        "readiness": _readiness(),
        "message": (
            "Updater helper audit envelope proof is ready in memory only. No helper process, audit file write, rollback move, relaunch, or EXE replacement was performed."
            if envelope_ready
            else "Updater helper audit envelope proof is blocked. No helper process, audit file write, rollback move, relaunch, or EXE replacement was performed."
        ),
        "errors": list(dict.fromkeys(str(item) for item in errors if str(item))),
        "warnings": [],
    }


def required_update_helper_audit_envelope_write_operator_statement(
    audit_envelope: dict[str, Any],
) -> str:
    latest_version = str(audit_envelope.get("latest_version") or "").strip()
    artifact_name = str(audit_envelope.get("artifact_name") or CURRENT_ARTIFACT_NAME).strip()
    plan_digest = str(audit_envelope.get("helper_plan_digest_sha256") or "").strip().lower()
    dry_run_digest = str(audit_envelope.get("dry_run_digest_sha256") or "").strip().lower()
    envelope_digest = str(audit_envelope.get("audit_envelope_digest_sha256") or "").strip().lower()
    return (
        f"{AUDIT_ENVELOPE_WRITE_OPERATOR_STATEMENT_PREFIX}: "
        f"{latest_version} {artifact_name} {plan_digest} {dry_run_digest} {envelope_digest}"
    ).strip()


def build_launcher_update_helper_audit_envelope_write_proof(
    vault_root: str | Path,
    *,
    audit_envelope_proof: dict[str, Any] | None = None,
    plan_file_path: str | Path | None = None,
    approval_digest: str = "",
    parent_pid: int | None = None,
    fixture_root: str | Path | None = None,
    operator_approved_audit_envelope_write: bool = False,
    operator_statement: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write the helper audit envelope as a fixture-only create-only proof.

    This is not the real updater audit write. It can only create a JSON file
    under an explicit fixture root inside the vault root, after exact operator
    approval. It never launches the helper, moves rollback files, replaces the
    executable, relaunches Studio, downloads binaries, or publishes GitHub
    releases.
    """

    vault = Path(vault_root).resolve()
    timestamp = generated_at or _now_utc()
    proof = audit_envelope_proof or build_launcher_update_helper_audit_envelope_proof(
        vault,
        plan_file_path=plan_file_path,
        approval_digest=approval_digest,
        parent_pid=parent_pid,
        generated_at=timestamp,
    )
    audit_envelope = (
        proof.get("audit_envelope") if isinstance(proof.get("audit_envelope"), dict) else {}
    )
    required_statement = (
        required_update_helper_audit_envelope_write_operator_statement(audit_envelope)
        if audit_envelope
        else ""
    )
    provided_statement = str(operator_statement or "").strip()
    blockers: list[str] = []

    if not proof.get("ok") or not proof.get("audit_envelope_ready") or not audit_envelope:
        blockers.append("helper_audit_envelope_not_ready")
        blockers.extend(str(item) for item in proof.get("errors") or [])
    if audit_envelope.get("schema_version") != AUDIT_ENVELOPE_SCHEMA_VERSION:
        blockers.append("helper_audit_envelope_schema_mismatch")

    envelope_digest = str(audit_envelope.get("audit_envelope_digest_sha256") or "").strip().lower()
    digest_payload = dict(audit_envelope)
    digest_payload.pop("audit_envelope_digest_sha256", None)
    if not _is_sha256(envelope_digest):
        blockers.append("helper_audit_envelope_digest_required")
    elif _stable_digest(digest_payload) != envelope_digest:
        blockers.append("helper_audit_envelope_digest_mismatch")
    elif str(proof.get("audit_envelope_digest_sha256") or "").strip().lower() != envelope_digest:
        blockers.append("helper_audit_envelope_proof_digest_mismatch")

    if not operator_approved_audit_envelope_write:
        blockers.append("operator_approved_helper_audit_envelope_write_required")
    if not required_statement:
        blockers.append("required_operator_statement_unavailable")
    elif provided_statement != required_statement:
        blockers.append(
            "operator_statement_must_exactly_match_required_helper_audit_envelope_write_statement"
        )

    fixture_path: Path | None = None
    fixture_text = str(fixture_root or "").strip()
    if not fixture_text:
        blockers.append("fixture_root_required")
    else:
        fixture_path = Path(fixture_text).resolve()
        if not fixture_path.exists() or not fixture_path.is_dir():
            blockers.append("fixture_root_must_exist")
        if not _path_inside(fixture_path, vault):
            blockers.append("fixture_root_not_inside_vault")

    audit_path: Path | None = None
    if fixture_path and envelope_digest:
        audit_path = Path(_build_audit_envelope_path(fixture_path, audit_envelope)).resolve()
        if not _path_inside(audit_path, fixture_path):
            blockers.append("helper_audit_envelope_path_not_inside_fixture_root")
        if not _path_inside(audit_path, vault):
            blockers.append("helper_audit_envelope_path_not_inside_vault")
        if audit_path.exists():
            blockers.append("helper_audit_envelope_file_already_exists")

    if blockers:
        return _audit_envelope_write_result(
            vault=vault,
            timestamp=timestamp,
            status="helper_audit_envelope_write_proof_blocked",
            ok=False,
            blockers=blockers,
            audit_envelope_proof=proof,
            audit_envelope=audit_envelope,
            required_statement=required_statement,
            fixture_root=fixture_path,
            audit_path=audit_path,
        )

    assert fixture_path is not None
    assert audit_path is not None

    try:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_path.open("x", encoding="utf-8") as handle:
            json.dump(audit_envelope, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        return _audit_envelope_write_result(
            vault=vault,
            timestamp=timestamp,
            status="helper_audit_envelope_write_proof_blocked",
            ok=False,
            blockers=["helper_audit_envelope_file_already_exists"],
            audit_envelope_proof=proof,
            audit_envelope=audit_envelope,
            required_statement=required_statement,
            fixture_root=fixture_path,
            audit_path=audit_path,
        )
    except OSError as exc:
        return _audit_envelope_write_result(
            vault=vault,
            timestamp=timestamp,
            status="helper_audit_envelope_write_proof_failed",
            ok=False,
            blockers=[f"helper_audit_envelope_write_failed:{type(exc).__name__}"],
            audit_envelope_proof=proof,
            audit_envelope=audit_envelope,
            required_statement=required_statement,
            fixture_root=fixture_path,
            audit_path=audit_path,
        )

    return _audit_envelope_write_result(
        vault=vault,
        timestamp=timestamp,
        status="helper_audit_envelope_write_proof_written",
        ok=True,
        blockers=[],
        audit_envelope_proof=proof,
        audit_envelope=audit_envelope,
        required_statement=required_statement,
        fixture_root=fixture_path,
        audit_path=audit_path,
        audit_envelope_written=True,
    )


def _validate_helper_plan_paths(vault: Path, helper_plan: dict[str, Any]) -> tuple[list[str], dict[str, bool]]:
    blockers: list[str] = []
    validation = {
        "current_executable_hash_valid": False,
        "staged_artifact_hash_valid": False,
        "path_scope_valid": False,
    }
    current_path = Path(str(helper_plan.get("current_executable_path") or "")).resolve()
    staged_path = Path(str(helper_plan.get("staged_artifact_path") or "")).resolve()
    rollback_path = Path(str(helper_plan.get("rollback_path") or "")).resolve()

    if current_path.name != CURRENT_ARTIFACT_NAME:
        blockers.append("current_executable_filename_mismatch")
    if staged_path.name != CURRENT_ARTIFACT_NAME:
        blockers.append("staged_artifact_filename_mismatch")
    if current_path == staged_path:
        blockers.append("current_executable_must_not_be_staged_artifact")
    if not _path_inside(current_path, vault):
        blockers.append("current_executable_path_not_inside_vault_for_scaffold")
    if not _path_inside(staged_path, vault):
        blockers.append("staged_artifact_path_not_inside_vault_for_scaffold")
    if not _path_inside(rollback_path, vault):
        blockers.append("rollback_path_not_inside_vault_for_scaffold")
    validation["path_scope_valid"] = not blockers

    current_hash, current_error = _hash_existing_file(current_path, "current_executable")
    if current_error:
        blockers.append(current_error)
    elif current_hash.get("sha256") != str(helper_plan.get("current_executable_sha256") or "").lower():
        blockers.append("current_executable_sha256_mismatch")
    elif _int_or_none(current_hash.get("size_bytes")) != _int_or_none(
        helper_plan.get("current_executable_size_bytes")
    ):
        blockers.append("current_executable_size_mismatch")
    else:
        validation["current_executable_hash_valid"] = True

    staged_hash, staged_error = _hash_existing_file(staged_path, "staged_artifact")
    if staged_error:
        blockers.append(staged_error)
    elif staged_hash.get("sha256") != str(helper_plan.get("staged_artifact_sha256") or "").lower():
        blockers.append("staged_artifact_sha256_mismatch")
    elif _int_or_none(staged_hash.get("size_bytes")) != _int_or_none(
        helper_plan.get("staged_artifact_size_bytes")
    ):
        blockers.append("staged_artifact_size_mismatch")
    else:
        validation["staged_artifact_hash_valid"] = True

    return blockers, validation


def _hash_existing_file(path: Path, label: str) -> tuple[dict[str, Any], str]:
    if not path.exists() or not path.is_file():
        return {}, f"{label}_missing"
    try:
        size_bytes = path.stat().st_size
    except OSError as exc:
        return {}, f"{label}_stat_failed:{type(exc).__name__}"
    if size_bytes > MAX_BINARY_DOWNLOAD_BYTES:
        return {}, f"{label}_size_exceeds_max_for_scaffold"
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return {}, f"{label}_read_failed:{type(exc).__name__}"
    return {"size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}, ""


def _build_plan_consumption_steps(helper_plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _consumption_step(
            "load_plan_file",
            "Load helper-plan file envelope",
            read_validation=True,
            validation_passed=True,
        ),
        _consumption_step(
            "validate_approval_digest",
            "Validate operator approval digest against plan envelope",
            read_validation=True,
            validation_passed=True,
        ),
        _consumption_step(
            "revalidate_current_executable",
            "Revalidate current executable size and SHA-256",
            read_validation=True,
            validation_passed=True,
            target_path=helper_plan.get("current_executable_path"),
        ),
        _consumption_step(
            "revalidate_staged_artifact",
            "Revalidate staged artifact size and SHA-256",
            read_validation=True,
            validation_passed=True,
            target_path=helper_plan.get("staged_artifact_path"),
        ),
        _consumption_step(
            "wait_for_parent_process_exit",
            "Wait for parent Studio process to exit",
            future_execution=True,
            target_path=helper_plan.get("current_executable_path"),
        ),
        _consumption_step(
            "move_current_executable_to_rollback",
            "Move current executable to rollback path",
            future_execution=True,
            would_mutate_host=True,
            target_path=helper_plan.get("rollback_path"),
        ),
        _consumption_step(
            "move_staged_artifact_into_place",
            "Move staged artifact into current executable path",
            future_execution=True,
            would_mutate_host=True,
            target_path=helper_plan.get("current_executable_path"),
        ),
        _consumption_step(
            "verify_replacement_hash",
            "Verify replacement hash and size",
            future_execution=True,
            target_path=helper_plan.get("current_executable_path"),
        ),
        _consumption_step(
            "relaunch_studio",
            "Relaunch Studio with the declared command",
            future_execution=True,
            would_mutate_host=True,
            target_path=(helper_plan.get("relaunch_command") or [""])[0],
        ),
        _consumption_step(
            "write_helper_audit",
            "Write helper execution audit evidence",
            future_execution=True,
            would_write_audit=True,
        ),
    ]


def _consumption_step(
    step_id: str,
    label: str,
    *,
    read_validation: bool = False,
    validation_passed: bool = False,
    future_execution: bool = False,
    would_mutate_host: bool = False,
    would_write_audit: bool = False,
    target_path: Any = "",
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "label": label,
        "read_validation": bool(read_validation),
        "validation_passed": bool(validation_passed),
        "future_execution_step": bool(future_execution),
        "would_mutate_host": bool(would_mutate_host),
        "would_write_audit": bool(would_write_audit),
        "enabled_in_this_pass": False,
        "performed": False,
        "target_path": str(target_path or ""),
    }


def _build_audit_preview(
    vault: Path,
    helper_plan: dict[str, Any],
    consumption_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_version = str(helper_plan.get("latest_version") or "unknown").replace("/", "-").replace("\\", "-")
    plan_digest = str(helper_plan.get("plan_digest_sha256") or "unknown")
    audit_path = (
        vault
        / ".chaseos"
        / "updates"
        / "helper-audit"
        / latest_version
        / f"{plan_digest}.dry-run.json"
    ).resolve()
    payload = {
        "schema_version": "chaser.update_helper_audit_preview.v1",
        "helper_binary_name": HELPER_BINARY_NAME,
        "helper_plan_digest_sha256": plan_digest,
        "latest_version": latest_version,
        "consumption_step_ids": [str(step.get("step_id") or "") for step in consumption_steps],
        "execution_performed": False,
        "replacement_performed": False,
        "rollback_move_performed": False,
        "relaunch_performed": False,
    }
    return {
        "audit_schema_version": payload["schema_version"],
        "audit_path": str(audit_path),
        "audit_payload_digest_sha256": _stable_digest(payload),
        "audit_write_enabled": False,
        "audit_write_performed": False,
        "payload_preview": payload,
    }


def _build_audit_envelope_path(vault: Path, helper_plan: dict[str, Any]) -> str:
    latest_version = str(helper_plan.get("latest_version") or "unknown").replace("/", "-").replace("\\", "-")
    plan_digest = str(
        helper_plan.get("plan_digest_sha256")
        or helper_plan.get("helper_plan_digest_sha256")
        or "unknown"
    )
    return str(
        (
            vault
            / ".chaseos"
            / "updates"
            / "helper-audit"
            / latest_version
            / f"{plan_digest}.audit-envelope.json"
        ).resolve()
    )


def _audit_envelope_write_result(
    *,
    vault: Path,
    timestamp: str,
    status: str,
    ok: bool,
    blockers: list[str],
    audit_envelope_proof: dict[str, Any],
    audit_envelope: dict[str, Any],
    required_statement: str,
    fixture_root: Path | None,
    audit_path: Path | None,
    audit_envelope_written: bool = False,
) -> dict[str, Any]:
    audit_file_digest = ""
    if audit_path and audit_path.exists() and audit_path.is_file():
        audit_file_digest = _hash_existing_file(audit_path, "helper_audit_envelope_file")[0].get(
            "sha256", ""
        )
    envelope_digest = str(audit_envelope.get("audit_envelope_digest_sha256") or "")
    return {
        "ok": ok,
        "surface": AUDIT_ENVELOPE_WRITE_PROOF_SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": timestamp,
        "status": status,
        "status_label": status.replace("_", " "),
        "vault_root": str(vault),
        "fixture_root": str(fixture_root) if fixture_root else "",
        "fixture_root_required": True,
        "fixture_root_inside_vault_required": True,
        "helper_binary_name": HELPER_BINARY_NAME,
        "helper_module": "runtime.studio.launcher_update_helper",
        "current_version": CURRENT_VERSION,
        "latest_version": audit_envelope.get("latest_version") or audit_envelope_proof.get("latest_version") or "",
        "artifact_name": CURRENT_ARTIFACT_NAME,
        "audit_envelope_proof_status": audit_envelope_proof.get("status"),
        "audit_envelope_ready": bool(audit_envelope),
        "audit_envelope": audit_envelope,
        "audit_envelope_digest_sha256": envelope_digest,
        "required_operator_statement": required_statement,
        "operator_statement_required": True,
        "operator_statement_exact_match_required": True,
        "audit_path": str(audit_path) if audit_path else "",
        "audit_envelope_written": bool(audit_envelope_written),
        "audit_envelope_create_only": True,
        "audit_envelope_fixture_only": True,
        "audit_file_digest_sha256": audit_file_digest,
        "audit_file_payload_digest_sha256": envelope_digest if audit_envelope_written else "",
        "audit_envelope_write_proof_enabled": bool(audit_envelope_written),
        "fixture_audit_envelope_write_performed": bool(audit_envelope_written),
        "audit_write_enabled": False,
        "audit_write_performed": False,
        "real_helper_audit_write_performed": False,
        "helper_process_launch_enabled": False,
        "helper_execution_enabled": False,
        "replacement_enabled": False,
        "rollback_move_enabled": False,
        "relaunch_enabled": False,
        "binary_download_enabled": False,
        "github_publication_enabled": False,
        "authority": _authority(
            read_only=not audit_envelope_written,
            helper_plan_loaded=bool(
                (audit_envelope_proof.get("authority") or {}).get(
                    "updater_helper_executable_scaffold_plan_loaded"
                )
            ),
            helper_plan_validated=bool(
                (audit_envelope_proof.get("authority") or {}).get(
                    "updater_helper_executable_scaffold_plan_validated"
                )
            ),
            plan_consumption_dry_run_completed=bool(
                (audit_envelope_proof.get("authority") or {}).get(
                    "updater_helper_plan_consumption_dry_run_completed"
                )
            ),
            audit_envelope_ready=bool(
                (audit_envelope_proof.get("authority") or {}).get(
                    "updater_helper_audit_envelope_ready"
                )
            ),
            audit_envelope_write_proof_completed=bool(audit_envelope_written),
        ),
        "readiness": _readiness(),
        "message": (
            "Helper audit envelope write proof wrote a create-only JSON file inside the declared fixture root. No helper process, real audit write, relaunch, rollback move, or packaged EXE replacement was performed."
            if ok
            else "Helper audit envelope write proof is blocked. No helper process, real audit write, relaunch, rollback move, or packaged EXE replacement was performed."
        ),
        "errors": list(dict.fromkeys(str(item) for item in blockers if str(item))),
        "warnings": list(audit_envelope_proof.get("warnings") or []),
    }


def build_launcher_update_helper_disposable_execution_receipt_validation(
    vault_root: str | Path,
    *,
    execution_boundary_receipt_path: str | Path | None = None,
    execution_boundary_digest: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate a disposable-target execution receipt for `ChaseOS-Installer.exe`.

    This helper-side scaffold reads only an execution-boundary receipt under the
    supplied vault/target root and verifies its digest. It performs no rollback,
    relaunch, helper subprocess launch, or executable replacement.
    """

    vault = Path(vault_root).resolve()
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    receipt_path: Path | None = None
    receipt_payload: dict[str, Any] = {}
    execution_boundary: dict[str, Any] = {}
    expected_digest = str(execution_boundary_digest or "").strip().lower()

    if not expected_digest:
        blockers.append("execution_boundary_digest_required")
    elif not _is_sha256(expected_digest):
        blockers.append("execution_boundary_digest_must_be_sha256")

    receipt_text = str(execution_boundary_receipt_path or "").strip()
    if not receipt_text:
        blockers.append("execution_boundary_receipt_path_required")
    else:
        candidate = Path(receipt_text)
        receipt_path = (candidate if candidate.is_absolute() else vault / candidate).resolve()
        if not _path_inside(receipt_path, vault):
            blockers.append("execution_boundary_receipt_path_not_inside_target_root")
        if not receipt_path.exists() or not receipt_path.is_file():
            blockers.append("execution_boundary_receipt_missing")
        else:
            try:
                raw = receipt_path.read_bytes()
            except OSError as exc:
                blockers.append(f"execution_boundary_receipt_read_failed:{type(exc).__name__}")
                raw = b""
            if len(raw) > MAX_HELPER_PLAN_FILE_BYTES:
                blockers.append("execution_boundary_receipt_too_large")
            if raw:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except UnicodeDecodeError:
                    blockers.append("execution_boundary_receipt_not_utf8")
                except json.JSONDecodeError:
                    blockers.append("execution_boundary_receipt_json_invalid")
                else:
                    if not isinstance(parsed, dict):
                        blockers.append("execution_boundary_receipt_must_be_object")
                    else:
                        receipt_payload = parsed

    if receipt_payload:
        if receipt_payload.get("receipt_kind") != "disposable_target_execution_boundary_receipt":
            blockers.append("execution_boundary_receipt_kind_mismatch")
        receipt_digest = str(
            receipt_payload.get("execution_boundary_digest_sha256") or ""
        ).strip().lower()
        if not _is_sha256(receipt_digest):
            blockers.append("execution_boundary_receipt_digest_required")
        elif expected_digest and receipt_digest != expected_digest:
            blockers.append("execution_boundary_receipt_digest_mismatch")

        raw_boundary = receipt_payload.get("execution_boundary")
        if not isinstance(raw_boundary, dict):
            blockers.append("execution_boundary_payload_required")
        else:
            execution_boundary = raw_boundary
            boundary_digest = str(
                execution_boundary.get("execution_boundary_digest_sha256") or ""
            ).strip().lower()
            boundary_without_digest = dict(execution_boundary)
            boundary_without_digest.pop("execution_boundary_digest_sha256", None)
            if execution_boundary.get("surface") != PRODUCTION_DISPOSABLE_TARGET_EXECUTION_BOUNDARY_SURFACE_ID:
                blockers.append("execution_boundary_surface_mismatch")
            if execution_boundary.get("schema_version") != PRODUCTION_DISPOSABLE_TARGET_EXECUTION_BOUNDARY_SCHEMA_VERSION:
                blockers.append("execution_boundary_schema_mismatch")
            if not _is_sha256(boundary_digest):
                blockers.append("execution_boundary_digest_missing")
            elif _stable_digest(boundary_without_digest) != boundary_digest:
                blockers.append("execution_boundary_digest_recalculation_mismatch")
            elif expected_digest and boundary_digest != expected_digest:
                blockers.append("execution_boundary_digest_mismatch")
            if execution_boundary.get("helper_binary_name") != HELPER_BINARY_NAME:
                blockers.append("helper_binary_name_mismatch")
            if execution_boundary.get("artifact_name") != CURRENT_ARTIFACT_NAME:
                blockers.append("artifact_name_mismatch")
            if execution_boundary.get("disposable_executable_replacement_performed") is not True:
                blockers.append("disposable_replacement_required_before_helper_receipt")
            if execution_boundary.get("replacement_verified") is not True:
                blockers.append("replacement_verification_required_before_helper_receipt")
            if execution_boundary.get("primary_install_mutation_performed") is not False:
                blockers.append("primary_install_mutation_must_be_false")

    ok = not blockers
    status = (
        "helper_disposable_execution_receipt_validation_ready"
        if ok
        else "helper_disposable_execution_receipt_validation_blocked"
    )
    return {
        "ok": ok,
        "surface": DISPOSABLE_EXECUTION_RECEIPT_VALIDATION_SURFACE_ID,
        "schema_version": DISPOSABLE_EXECUTION_RECEIPT_VALIDATION_SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "generated_at_utc": timestamp,
        "status": status,
        "status_label": status.replace("_", " "),
        "vault_root": str(vault),
        "helper_binary_name": HELPER_BINARY_NAME,
        "artifact_name": CURRENT_ARTIFACT_NAME,
        "execution_boundary_receipt_path": str(receipt_path) if receipt_path else "",
        "execution_boundary_digest_sha256": expected_digest,
        "receipt_payload": receipt_payload,
        "execution_boundary": execution_boundary,
        "receipt_validation_performed": bool(receipt_payload),
        "helper_process_launch_enabled": False,
        "helper_process_launch_performed": False,
        "rollback_move_performed": False,
        "relaunch_performed": False,
        "executable_replacement_performed": False,
        "primary_install_mutation_performed": False,
        "message": (
            "Disposable-target execution receipt validated for the ChaseOS installer scaffold. No helper process launch, relaunch, or primary install mutation was performed."
            if ok
            else "Disposable-target execution receipt validation is blocked. No helper process launch, relaunch, or primary install mutation was performed."
        ),
        "errors": list(dict.fromkeys(str(item) for item in blockers if str(item))),
        "warnings": [],
    }


def _authority(
    *,
    helper_plan_loaded: bool,
    helper_plan_validated: bool,
    read_only: bool = True,
    plan_consumption_dry_run_completed: bool = False,
    audit_envelope_ready: bool = False,
    audit_envelope_write_proof_completed: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": bool(read_only),
        "updater_helper_executable_scaffold_built": True,
        "updater_helper_executable_scaffold_plan_loaded": bool(helper_plan_loaded),
        "updater_helper_executable_scaffold_plan_validated": bool(helper_plan_validated),
        "updater_helper_plan_consumption_dry_run_built": True,
        "updater_helper_plan_consumption_dry_run_completed": bool(
            plan_consumption_dry_run_completed
        ),
        "updater_helper_plan_consumption_execution_performed": False,
        "updater_helper_plan_consumption_audit_write_performed": False,
        "updater_helper_audit_envelope_proof_built": True,
        "updater_helper_audit_envelope_ready": bool(audit_envelope_ready),
        "updater_helper_audit_envelope_write_proof_built": True,
        "updater_helper_audit_envelope_write_proof_completed": bool(
            audit_envelope_write_proof_completed
        ),
        "updater_helper_audit_envelope_fixture_write_allowed_in_this_pass": bool(
            audit_envelope_write_proof_completed
        ),
        "updater_helper_audit_envelope_fixture_write_performed": bool(
            audit_envelope_write_proof_completed
        ),
        "updater_helper_audit_write_allowed_in_this_pass": False,
        "updater_helper_audit_write_performed": False,
        "updater_helper_process_launch_allowed_in_this_pass": False,
        "updater_helper_process_launch_performed": False,
        "updater_helper_execution_allowed_in_this_pass": False,
        "updater_helper_execution_performed": False,
        "updater_helper_plan_file_write_performed": False,
        "binary_download_performed": False,
        "binary_download_allowed_in_this_pass": False,
        "rollback_move_performed": False,
        "relaunch_performed": False,
        "executable_replacement_performed": False,
        "executable_replacement_allowed_in_this_pass": False,
        "installer_execution_performed": False,
        "installer_execution_allowed_in_this_pass": False,
        "github_release_publication_performed": False,
        "github_release_publication_allowed": False,
        "writes_host_startup": False,
        "writes_registry": False,
        "writes_start_menu": False,
        "writes_desktop_shortcut": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "agent_bus_task_write_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _readiness() -> dict[str, Any]:
    return {
        "helper_executable_scaffold_built": True,
        "helper_binary_name": HELPER_BINARY_NAME,
        "helper_module": "runtime.studio.launcher_update_helper",
        "plan_file_load_built": True,
        "plan_file_validation_built": True,
        "plan_consumption_dry_run_built": True,
        "audit_envelope_proof_built": True,
        "audit_envelope_default_enabled": False,
        "audit_envelope_requires_plan_consumption_dry_run": True,
        "audit_envelope_write_enabled": False,
        "audit_envelope_write_proof_built": True,
        "audit_envelope_write_proof_default_enabled": False,
        "audit_envelope_write_proof_requires_audit_envelope": True,
        "audit_envelope_write_proof_requires_operator_approval": True,
        "audit_envelope_write_proof_requires_exact_operator_statement": True,
        "audit_envelope_write_proof_scope": "fixture_root_inside_vault_only",
        "audit_envelope_write_proof_writes_enabled_in_settings": False,
        "approval_digest_required": True,
        "execution_default_enabled": False,
        "helper_process_launch_enabled": False,
        "rollback_move_enabled": False,
        "relaunch_enabled": False,
        "executable_replacement_enabled": False,
        "audit_write_enabled": False,
        "settings_write_control_exposed": False,
        "next_recommended_pass": "launcher-update-helper-binary-spec-scaffold",
    }


def _stable_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _path_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
