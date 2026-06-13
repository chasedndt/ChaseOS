from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from runtime.forge.approval_decision import build_forge_approval_decision_handoff
from runtime.forge.registry import (
    LIVE_INSTALL_APPROVAL_RECORD_TYPE,
    LIVE_INSTALL_MARKER_RECORD_TYPE,
    REGISTRY_RELATIVE_PATH,
    ROLLBACK_APPROVAL_RECORD_TYPE,
    ROLLBACK_MARKER_RECORD_TYPE,
    SANDBOX_APPROVAL_RECORD_TYPE,
    build_extension_registry,
    build_live_install_approval,
    build_live_install_execution,
    build_registry_entry,
    build_rollback_approval,
    build_rollback_execution,
    build_sandbox_install_approval,
    build_sandbox_registry_write_execution,
)
from runtime.forge.validator import validate_manifest


DEMO_MANIFEST = Path(__file__).with_name("examples") / "ugc_campaign_studio.manifest.json"


def _manifest() -> dict:
    return json.loads(DEMO_MANIFEST.read_text(encoding="utf-8"))


def _record_approved_decision(vault: Path, artifact_path: Path) -> None:
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    handoff = build_forge_approval_decision_handoff(
        vault,
        approval_artifact_path=artifact_path,
        decision="approved",
        expected_request_digest=payload["request_digest_sha256"],
        operator_statement=payload["operator_confirmation_text"],
        write_decision=True,
        reviewer_id="operator",
        generated_at="2026-05-20T00:00:00Z",
    )
    assert handoff["ok"] is True, handoff


def _manually_approve_artifact_without_decision(artifact_path: Path) -> None:
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    payload["status"] = "approved"
    payload["operator_decision"] = "approved"
    payload["operator_approval_statement"] = payload["operator_confirmation_text"]
    payload["approved_at"] = "2026-05-20T00:00:00Z"
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_approved_sandbox_artifact(tmp_path: Path, manifest: dict | None = None) -> tuple[dict, Path]:
    manifest_payload = manifest or _manifest()
    preview = build_sandbox_install_approval(tmp_path, manifest=manifest_payload)
    request = build_sandbox_install_approval(
        tmp_path,
        manifest=manifest_payload,
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / request["approval_artifact_path"]
    _record_approved_decision(tmp_path, artifact_path)
    return preview, artifact_path


def _execute_sandbox_install(tmp_path: Path, manifest: dict | None = None) -> dict:
    manifest_payload = manifest or _manifest()
    preview, _artifact_path = _write_approved_sandbox_artifact(tmp_path, manifest_payload)
    return build_sandbox_registry_write_execution(
        tmp_path,
        manifest=manifest_payload,
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )


def _write_approved_live_artifact(tmp_path: Path, manifest: dict | None = None) -> tuple[dict, Path]:
    manifest_payload = manifest or _manifest()
    _execute_sandbox_install(tmp_path, manifest_payload)
    preview = build_live_install_approval(tmp_path, manifest=manifest_payload)
    request = build_live_install_approval(
        tmp_path,
        manifest=manifest_payload,
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / request["approval_artifact_path"]
    _record_approved_decision(tmp_path, artifact_path)
    return preview, artifact_path


def _execute_live_install(tmp_path: Path, manifest: dict | None = None) -> dict:
    manifest_payload = manifest or _manifest()
    preview, _artifact_path = _write_approved_live_artifact(tmp_path, manifest_payload)
    return build_live_install_execution(
        tmp_path,
        manifest=manifest_payload,
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )


def _write_approved_rollback_artifact(tmp_path: Path, manifest: dict | None = None) -> tuple[dict, Path]:
    manifest_payload = manifest or _manifest()
    _execute_live_install(tmp_path, manifest_payload)
    preview = build_rollback_approval(tmp_path, manifest=manifest_payload)
    request = build_rollback_approval(
        tmp_path,
        manifest=manifest_payload,
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / request["approval_artifact_path"]
    _record_approved_decision(tmp_path, artifact_path)
    return preview, artifact_path


def test_missing_registry_returns_empty_read_model(tmp_path: Path) -> None:
    model = build_extension_registry(tmp_path)

    assert model["ok"] is True
    assert model["registry_exists"] is False
    assert model["entry_count"] == 0
    assert model["write_policy"]["generated_extensions_may_write_registry_directly"] is False
    assert model["authority"]["writes_extension_registry"] is False


def test_seed_registry_file_loads_entries(tmp_path: Path) -> None:
    registry_path = tmp_path / REGISTRY_RELATIVE_PATH
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps({"schema_version": "forge.registry.v1", "entries": [{"extension_id": "demo"}]}),
        encoding="utf-8",
    )

    model = build_extension_registry(tmp_path)

    assert model["ok"] is True
    assert model["registry_exists"] is True
    assert model["entry_count"] == 1


def test_registry_entry_preview_uses_manifest_digest_and_blocks_authority() -> None:
    manifest = _manifest()
    validation = validate_manifest(manifest)

    entry = build_registry_entry(manifest, validation)

    assert entry["schema_version"] == "forge.registry.entry.v1"
    assert entry["extension_id"] == "ugc-campaign-studio"
    assert entry["registry_status"] == "pending_sandbox_approval"
    assert entry["install_environment"] == "sandbox"
    assert entry["validation_valid"] is True
    assert entry["manifest_digest_sha256"]
    assert entry["authority"]["writes_extension_registry"] is False
    assert entry["target_paths"]


def test_sandbox_approval_preview_does_not_write(tmp_path: Path) -> None:
    result = build_sandbox_install_approval(tmp_path, manifest=_manifest())

    assert result["ok"] is True
    assert result["surface"] == "chaser_forge_sandbox_install_approval"
    assert result["approval_request_written"] is False
    assert result["approval_artifact_exists"] is False
    assert result["authority"]["writes_approval_artifact"] is False
    assert result["authority"]["writes_extension_registry"] is False
    assert not (tmp_path / result["approval_artifact_path"]).exists()
    assert not (tmp_path / REGISTRY_RELATIVE_PATH).exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_sandbox_approval_write_requires_exact_digest(tmp_path: Path) -> None:
    result = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest="wrong",
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in result["blockers"]
    assert not (tmp_path / result["approval_artifact_path"]).exists()


def test_sandbox_approval_writes_only_pending_artifact_with_exact_digest(tmp_path: Path) -> None:
    preview = build_sandbox_install_approval(tmp_path, manifest=_manifest())

    result = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / result["approval_artifact_path"]

    assert result["ok"] is True
    assert result["approval_request_written"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["record_type"] == SANDBOX_APPROVAL_RECORD_TYPE
    assert payload["status"] == "pending_operator_decision"
    assert payload["operator_decision"] == "pending"
    assert payload["approval_consumed"] is False
    assert payload["sandbox_install_allowed_in_this_pass"] is False
    assert payload["registry_write_allowed_in_this_pass"] is False
    assert payload["extension_file_write_allowed_in_this_pass"] is False
    assert not (tmp_path / REGISTRY_RELATIVE_PATH).exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()


def test_sandbox_approval_reuses_existing_matching_artifact(tmp_path: Path) -> None:
    preview = build_sandbox_install_approval(tmp_path, manifest=_manifest())
    first = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    second = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert first["approval_request_written"] is True
    assert second["approval_request_written"] is False
    assert second["approval_request_reused"] is True
    assert second["approval_artifact_path"] == first["approval_artifact_path"]


def test_sandbox_approval_blocks_existing_mismatched_artifact(tmp_path: Path) -> None:
    preview = build_sandbox_install_approval(tmp_path, manifest=_manifest())
    artifact_path = tmp_path / preview["approval_artifact_path"]
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text(json.dumps({"record_type": "mismatch"}), encoding="utf-8")

    result = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "existing_sandbox_approval_artifact_mismatch" in result["blockers"]


def test_sandbox_approval_blocks_existing_exact_once_marker(tmp_path: Path) -> None:
    preview = build_sandbox_install_approval(tmp_path, manifest=_manifest())
    marker_path = tmp_path / preview["future_exact_once_marker_path"]
    marker_path.parent.mkdir(parents=True)
    marker_path.write_text("reserved\n", encoding="utf-8")

    result = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "sandbox_exact_once_marker_already_present" in result["blockers"]


def test_sandbox_approval_blocks_invalid_manifest_without_write(tmp_path: Path) -> None:
    manifest = deepcopy(_manifest())
    manifest["permissions"].append("secrets.read")

    result = build_sandbox_install_approval(
        tmp_path,
        manifest=manifest,
        request_digest="anything",
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "manifest_validation_blocked" in result["blockers"]
    assert not (tmp_path / result["approval_artifact_path"]).exists()


def test_sandbox_registry_writer_blocks_without_approved_artifact(tmp_path: Path) -> None:
    preview = build_sandbox_install_approval(tmp_path, manifest=_manifest())

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
    )

    assert result["ok"] is False
    assert result["registry_written"] is False
    assert result["extension_files_written"] == []
    assert "approved_sandbox_approval_artifact_missing" in result["blockers"]
    assert not (tmp_path / REGISTRY_RELATIVE_PATH).exists()
    assert not (tmp_path / result["future_exact_once_marker_path"]).exists()


def test_sandbox_registry_writer_preview_does_not_write_before_execute(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_sandbox_artifact(tmp_path)

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
    )

    assert result["ok"] is True
    assert result["status"] == "forge_sandbox_registry_write_ready"
    assert result["registry_written"] is False
    assert result["extension_files_written"] == []
    assert result["authority"]["writes_extension_registry"] is False
    assert not (tmp_path / REGISTRY_RELATIVE_PATH).exists()
    assert not (tmp_path / result["future_exact_once_marker_path"]).exists()


def test_sandbox_registry_writer_executes_only_after_approved_artifact(tmp_path: Path) -> None:
    preview, artifact_path = _write_approved_sandbox_artifact(tmp_path)

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is True
    assert result["status"] == "forge_sandbox_registry_write_executed"
    assert result["registry_written"] is True
    assert result["approval_consumed"] is True
    assert result["exact_once_marker_written"] is True
    assert result["authority"]["executes_sandbox_install"] is True
    assert result["authority"]["executes_live_install"] is False
    assert result["authority"]["mutates_protected_core"] is False

    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert registry["entries"][0]["extension_id"] == "ugc-campaign-studio"
    assert registry["entries"][0]["registry_status"] == "sandbox_installed"
    assert registry["entries"][0]["install_environment"] == "sandbox"
    assert registry["entries"][0]["sandbox_execution"]["live_install"] is False

    for repo_path in result["extension_files_written"]:
        path = tmp_path / repo_path
        assert path.is_file()
        assert repo_path.startswith("extensions/ugc-campaign-studio/")

    approval = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approval["status"] == "consumed"
    assert approval["approval_consumed"] is True
    assert approval["sandbox_install_allowed_in_this_pass"] is True
    assert approval["live_install_allowed_in_this_pass"] is False

    marker = json.loads((tmp_path / result["future_exact_once_marker_path"]).read_text(encoding="utf-8"))
    assert marker["reserved_before_writes"] is True
    assert marker["completed"] is True


def test_sandbox_registry_writer_blocks_wrong_digest_before_writes(tmp_path: Path) -> None:
    _preview, _artifact_path = _write_approved_sandbox_artifact(tmp_path)

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest="wrong",
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_written"] is False
    assert "request_digest_required_or_mismatched" in result["blockers"]
    assert not (tmp_path / REGISTRY_RELATIVE_PATH).exists()
    assert not (tmp_path / result["future_exact_once_marker_path"]).exists()


def test_sandbox_registry_writer_requires_operator_approved_artifact(tmp_path: Path) -> None:
    preview = build_sandbox_install_approval(tmp_path, manifest=_manifest())
    request = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_written"] is False
    assert "approval_status_not_approved" in result["blockers"]
    assert "operator_decision_not_approved" in result["blockers"]
    assert "operator_approval_statement_missing_or_mismatched" in result["blockers"]
    assert "approval_decision_record_missing" in result["blockers"]


def test_sandbox_registry_writer_blocks_manual_approval_without_decision_sidecar(tmp_path: Path) -> None:
    preview = build_sandbox_install_approval(tmp_path, manifest=_manifest())
    request = build_sandbox_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / request["approval_artifact_path"]
    _manually_approve_artifact_without_decision(artifact_path)

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_written"] is False
    assert "approval_decision_record_missing" in result["blockers"]
    assert "approval_decision_artifact_path_missing" in result["blockers"]
    assert not (tmp_path / REGISTRY_RELATIVE_PATH).exists()
    assert not (tmp_path / result["future_exact_once_marker_path"]).exists()


def test_sandbox_registry_writer_blocks_duplicate_execution(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_sandbox_artifact(tmp_path)
    first = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )
    second = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert first["registry_written"] is True
    assert second["ok"] is False
    assert second["registry_written"] is False
    assert "sandbox_exact_once_marker_already_present" in second["blockers"]
    assert "approval_already_consumed" in second["blockers"]


def test_sandbox_registry_writer_blocks_existing_extension_target(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_sandbox_artifact(tmp_path)
    conflict_path = tmp_path / "extensions" / "ugc-campaign-studio" / "manifest.json"
    conflict_path.parent.mkdir(parents=True)
    conflict_path.write_text("existing\n", encoding="utf-8")

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_written"] is False
    assert "extension_target_already_exists" in result["blockers"]
    assert not (tmp_path / result["future_exact_once_marker_path"]).exists()


def test_sandbox_registry_writer_blocks_existing_registry_entry(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_sandbox_artifact(tmp_path)
    registry_path = tmp_path / REGISTRY_RELATIVE_PATH
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps({"schema_version": "forge.registry.v1", "entries": [{"extension_id": "ugc-campaign-studio"}]}),
        encoding="utf-8",
    )

    result = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_written"] is False
    assert "registry_entry_already_exists" in result["blockers"]
    assert not (tmp_path / result["future_exact_once_marker_path"]).exists()


def test_live_install_approval_blocks_without_sandbox_registry_entry(tmp_path: Path) -> None:
    result = build_live_install_approval(tmp_path, manifest=_manifest())

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "sandbox_registry_entry_missing" in result["blockers"]
    assert result["authority"]["live_install_executor_built"] is False
    assert result["authority"]["live_install_allowed_in_this_pass"] is False
    assert not (tmp_path / result["approval_artifact_path"]).exists()


def test_live_install_approval_preview_ready_after_sandbox_proof_without_write(tmp_path: Path) -> None:
    sandbox_result = _execute_sandbox_install(tmp_path)

    result = build_live_install_approval(tmp_path, manifest=_manifest())

    assert sandbox_result["registry_written"] is True
    assert result["ok"] is True
    assert result["status"] == "forge_live_install_approval_request_ready"
    assert result["approval_request_written"] is False
    assert result["sandbox_exact_once_marker_exists"] is True
    assert result["sandbox_registry_entry"]["registry_status"] == "sandbox_installed"
    assert result["authority"]["writes_approval_artifact"] is False
    assert result["authority"]["executes_live_install"] is False
    assert not (tmp_path / result["approval_artifact_path"]).exists()
    assert not (tmp_path / result["future_live_exact_once_marker_path"]).exists()


def test_live_install_approval_write_requires_exact_digest(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)

    result = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest="wrong",
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in result["blockers"]
    assert not (tmp_path / result["approval_artifact_path"]).exists()


def test_live_install_approval_writes_pending_artifact_only_with_exact_digest(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())

    result = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / result["approval_artifact_path"]

    assert result["ok"] is True
    assert result["approval_request_written"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["record_type"] == LIVE_INSTALL_APPROVAL_RECORD_TYPE
    assert payload["status"] == "pending_operator_decision"
    assert payload["operator_decision"] == "pending"
    assert payload["approval_consumed"] is False
    assert payload["live_install_allowed_in_this_pass"] is False
    assert payload["live_install_executor_built"] is False
    assert payload["registry_write_allowed_in_this_pass"] is False
    assert payload["extension_file_write_allowed_in_this_pass"] is False
    assert payload["approved_material"]["sandbox_registry_entry_digest_sha256"]
    assert not (tmp_path / result["future_live_exact_once_marker_path"]).exists()

    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert registry["entries"][0]["registry_status"] == "sandbox_installed"
    assert registry["entries"][0]["install_environment"] == "sandbox"


def test_live_install_approval_reuses_existing_matching_artifact(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())
    first = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    second = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert first["approval_request_written"] is True
    assert second["approval_request_written"] is False
    assert second["approval_request_reused"] is True
    assert second["approval_artifact_path"] == first["approval_artifact_path"]


def test_live_install_approval_blocks_existing_mismatched_artifact(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())
    artifact_path = tmp_path / preview["approval_artifact_path"]
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text(json.dumps({"record_type": "mismatch"}), encoding="utf-8")

    result = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "existing_live_install_approval_artifact_mismatch" in result["blockers"]


def test_live_install_approval_blocks_if_sandbox_marker_invalid(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())
    marker_path = tmp_path / preview["sandbox_exact_once_marker_path"]
    marker_path.write_text(json.dumps({"record_type": "mismatch"}), encoding="utf-8")

    result = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "sandbox_marker_record_type_mismatch" in result["blockers"]
    assert "sandbox_marker_schema_version_mismatch" in result["blockers"]
    assert "sandbox_marker_not_completed" in result["blockers"]


def test_live_install_approval_blocks_if_extension_target_missing(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())
    target_path = tmp_path / preview["future_extension_target_paths"][0]
    target_path.unlink()

    result = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "extension_target_missing" in result["blockers"]
    assert not (tmp_path / result["approval_artifact_path"]).exists()


def test_live_install_executor_blocks_without_approved_artifact(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert result["live_install_executed"] is False
    assert "approved_live_install_approval_artifact_missing" in result["blockers"]
    assert not (tmp_path / result["future_live_exact_once_marker_path"]).exists()
    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert registry["entries"][0]["registry_status"] == "sandbox_installed"
    assert registry["entries"][0]["install_environment"] == "sandbox"


def test_live_install_executor_preview_does_not_write_before_execute(tmp_path: Path) -> None:
    preview, artifact_path = _write_approved_live_artifact(tmp_path)

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
    )

    assert result["ok"] is True
    assert result["status"] == "forge_live_install_execution_ready"
    assert result["registry_updated"] is False
    assert result["live_install_executed"] is False
    assert result["extension_files_written"] == []
    assert result["authority"]["executes_live_install"] is False
    assert not (tmp_path / result["future_live_exact_once_marker_path"]).exists()
    approval = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approval["approval_consumed"] is False
    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert registry["entries"][0]["registry_status"] == "sandbox_installed"


def test_live_install_executor_executes_only_after_approved_live_artifact(tmp_path: Path) -> None:
    preview, artifact_path = _write_approved_live_artifact(tmp_path)

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is True
    assert result["status"] == "forge_live_install_executed"
    assert result["registry_updated"] is True
    assert result["live_install_executed"] is True
    assert result["approval_consumed"] is True
    assert result["exact_once_marker_written"] is True
    assert result["extension_files_written"] == []
    assert result["authority"]["executes_live_install"] is True
    assert result["authority"]["writes_extension_registry"] is True
    assert result["authority"]["writes_extension_files"] is False
    assert result["authority"]["mutates_protected_core"] is False

    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    entry = registry["entries"][0]
    assert entry["extension_id"] == "ugc-campaign-studio"
    assert entry["registry_status"] == "live_installed"
    assert entry["install_environment"] == "live"
    assert entry["sandbox_execution"]["live_install"] is False
    assert entry["live_execution"]["live_install"] is True
    assert entry["live_execution"]["extension_files_written"] == []

    approval = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approval["status"] == "consumed"
    assert approval["approval_consumed"] is True
    assert approval["live_install_allowed_in_this_pass"] is True
    assert approval["extension_file_write_allowed_in_this_pass"] is False

    marker = json.loads((tmp_path / result["future_live_exact_once_marker_path"]).read_text(encoding="utf-8"))
    assert marker["record_type"] == LIVE_INSTALL_MARKER_RECORD_TYPE
    assert marker["reserved_before_writes"] is True
    assert marker["completed"] is True
    assert marker["extension_files_written"] == []


def test_live_install_executor_blocks_wrong_digest_before_writes(tmp_path: Path) -> None:
    _write_approved_live_artifact(tmp_path)

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest="wrong",
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "request_digest_required_or_mismatched" in result["blockers"]
    assert not (tmp_path / result["future_live_exact_once_marker_path"]).exists()


def test_live_install_executor_requires_operator_approved_live_artifact(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())
    request = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "approval_status_not_approved" in result["blockers"]
    assert "operator_decision_not_approved" in result["blockers"]
    assert "operator_approval_statement_missing_or_mismatched" in result["blockers"]
    assert "approval_decision_record_missing" in result["blockers"]


def test_live_install_executor_blocks_manual_approval_without_decision_sidecar(tmp_path: Path) -> None:
    _execute_sandbox_install(tmp_path)
    preview = build_live_install_approval(tmp_path, manifest=_manifest())
    request = build_live_install_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / request["approval_artifact_path"]
    _manually_approve_artifact_without_decision(artifact_path)

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "approval_decision_record_missing" in result["blockers"]
    assert "approval_decision_artifact_path_missing" in result["blockers"]
    assert not (tmp_path / result["future_live_exact_once_marker_path"]).exists()


def test_live_install_executor_blocks_duplicate_execution(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_live_artifact(tmp_path)
    first = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )
    second = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert first["live_install_executed"] is True
    assert second["ok"] is False
    assert second["registry_updated"] is False
    assert "live_install_exact_once_marker_already_present" in second["blockers"]
    assert "approval_already_consumed" in second["blockers"]


def test_live_install_executor_blocks_if_sandbox_marker_invalid_before_writes(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_live_artifact(tmp_path)
    marker_path = tmp_path / preview["sandbox_exact_once_marker_path"]
    marker_path.write_text(json.dumps({"record_type": "mismatch"}), encoding="utf-8")

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "sandbox_marker_record_type_mismatch" in result["blockers"]
    assert "sandbox_marker_schema_version_mismatch" in result["blockers"]
    assert "sandbox_marker_not_completed" in result["blockers"]
    assert not (tmp_path / result["future_live_exact_once_marker_path"]).exists()


def test_live_install_executor_blocks_existing_live_marker(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_live_artifact(tmp_path)
    marker_path = tmp_path / preview["future_live_exact_once_marker_path"]
    marker_path.parent.mkdir(parents=True)
    marker_path.write_text(json.dumps({"record_type": LIVE_INSTALL_MARKER_RECORD_TYPE}), encoding="utf-8")

    result = build_live_install_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "live_install_exact_once_marker_already_present" in result["blockers"]


def test_rollback_approval_blocks_without_live_registry_entry(tmp_path: Path) -> None:
    result = build_rollback_approval(tmp_path, manifest=_manifest())

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "live_registry_entry_missing" in result["blockers"]
    assert result["authority"]["rollback_executor_built"] is False
    assert result["authority"]["rollback_allowed_in_this_pass"] is False
    assert not (tmp_path / result["approval_artifact_path"]).exists()


def test_rollback_approval_preview_ready_after_live_execution_without_write(tmp_path: Path) -> None:
    live_result = _execute_live_install(tmp_path)

    result = build_rollback_approval(tmp_path, manifest=_manifest())

    assert live_result["live_install_executed"] is True
    assert result["ok"] is True
    assert result["status"] == "forge_rollback_approval_request_ready"
    assert result["approval_request_written"] is False
    assert result["live_exact_once_marker_exists"] is True
    assert result["live_registry_entry"]["registry_status"] == "live_installed"
    assert result["authority"]["writes_approval_artifact"] is False
    assert result["authority"]["executes_rollback"] is False
    assert not (tmp_path / result["approval_artifact_path"]).exists()
    assert not (tmp_path / result["future_rollback_exact_once_marker_path"]).exists()


def test_rollback_approval_write_requires_exact_digest(tmp_path: Path) -> None:
    _execute_live_install(tmp_path)

    result = build_rollback_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest="wrong",
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "request_digest_required_or_mismatched" in result["blockers"]
    assert not (tmp_path / result["approval_artifact_path"]).exists()


def test_rollback_approval_writes_pending_artifact_only_with_exact_digest(tmp_path: Path) -> None:
    _execute_live_install(tmp_path)
    preview = build_rollback_approval(tmp_path, manifest=_manifest())

    result = build_rollback_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / result["approval_artifact_path"]

    assert result["ok"] is True
    assert result["approval_request_written"] is True
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["record_type"] == ROLLBACK_APPROVAL_RECORD_TYPE
    assert payload["status"] == "pending_operator_decision"
    assert payload["operator_decision"] == "pending"
    assert payload["approval_consumed"] is False
    assert payload["rollback_allowed_in_this_pass"] is False
    assert payload["rollback_executor_built"] is False
    assert payload["registry_write_allowed_in_this_pass"] is False
    assert payload["extension_file_delete_allowed_in_this_pass"] is False
    assert payload["approved_material"]["live_registry_entry_digest_sha256"]
    assert not (tmp_path / result["future_rollback_exact_once_marker_path"]).exists()

    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert registry["entries"][0]["registry_status"] == "live_installed"
    assert registry["entries"][0]["install_environment"] == "live"


def test_rollback_approval_reuses_existing_matching_artifact(tmp_path: Path) -> None:
    _execute_live_install(tmp_path)
    preview = build_rollback_approval(tmp_path, manifest=_manifest())
    first = build_rollback_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    second = build_rollback_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert first["approval_request_written"] is True
    assert second["approval_request_written"] is False
    assert second["approval_request_reused"] is True
    assert second["approval_artifact_path"] == first["approval_artifact_path"]


def test_rollback_approval_blocks_if_live_marker_invalid(tmp_path: Path) -> None:
    _execute_live_install(tmp_path)
    preview = build_rollback_approval(tmp_path, manifest=_manifest())
    marker_path = tmp_path / preview["live_exact_once_marker_path"]
    marker_path.write_text(json.dumps({"record_type": "mismatch"}), encoding="utf-8")

    result = build_rollback_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    assert result["ok"] is False
    assert result["approval_request_written"] is False
    assert "live_marker_record_type_mismatch" in result["blockers"]
    assert "live_marker_schema_version_mismatch" in result["blockers"]
    assert "live_marker_not_completed" in result["blockers"]


def test_rollback_executor_blocks_without_approved_artifact(tmp_path: Path) -> None:
    _execute_live_install(tmp_path)
    preview = build_rollback_approval(tmp_path, manifest=_manifest())

    result = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert result["rollback_executed"] is False
    assert "approved_rollback_approval_artifact_missing" in result["blockers"]
    assert not (tmp_path / result["future_rollback_exact_once_marker_path"]).exists()
    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert registry["entries"][0]["registry_status"] == "live_installed"
    assert registry["entries"][0]["install_environment"] == "live"


def test_rollback_executor_preview_does_not_write_before_execute(tmp_path: Path) -> None:
    preview, artifact_path = _write_approved_rollback_artifact(tmp_path)

    result = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
    )

    assert result["ok"] is True
    assert result["status"] == "forge_rollback_execution_ready"
    assert result["registry_updated"] is False
    assert result["rollback_executed"] is False
    assert result["extension_files_deleted"] == []
    assert result["authority"]["executes_rollback"] is False
    assert not (tmp_path / result["future_rollback_exact_once_marker_path"]).exists()
    approval = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approval["approval_consumed"] is False
    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert registry["entries"][0]["registry_status"] == "live_installed"


def test_rollback_executor_executes_only_after_approved_rollback_artifact(tmp_path: Path) -> None:
    preview, artifact_path = _write_approved_rollback_artifact(tmp_path)
    live_registry_before = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    live_execution = dict(live_registry_before["entries"][0]["live_execution"])

    result = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is True
    assert result["status"] == "forge_rollback_executed"
    assert result["registry_updated"] is True
    assert result["rollback_executed"] is True
    assert result["approval_consumed"] is True
    assert result["exact_once_marker_written"] is True
    assert result["extension_files_deleted"] == []
    assert result["extension_files_written"] == []
    assert result["authority"]["executes_rollback"] is True
    assert result["authority"]["writes_extension_registry"] is True
    assert result["authority"]["writes_extension_files"] is False
    assert result["authority"]["deletes_extension_files"] is False
    assert result["authority"]["mutates_protected_core"] is False

    registry = json.loads((tmp_path / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    entry = registry["entries"][0]
    assert entry["extension_id"] == "ugc-campaign-studio"
    assert entry["registry_status"] == "sandbox_installed"
    assert entry["install_environment"] == "sandbox"
    assert "live_execution" not in entry
    assert entry["live_execution_history"][0] == live_execution
    assert entry["rollback_execution"]["rollback"] is True
    assert entry["rollback_execution"]["extension_files_deleted"] == []

    for repo_path in result["extension_target_paths"]:
        assert (tmp_path / repo_path).is_file()

    approval = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approval["status"] == "consumed"
    assert approval["approval_consumed"] is True
    assert approval["rollback_allowed_in_this_pass"] is True
    assert approval["extension_file_delete_allowed_in_this_pass"] is False

    marker = json.loads((tmp_path / result["future_rollback_exact_once_marker_path"]).read_text(encoding="utf-8"))
    assert marker["record_type"] == ROLLBACK_MARKER_RECORD_TYPE
    assert marker["reserved_before_writes"] is True
    assert marker["completed"] is True
    assert marker["extension_files_deleted"] == []


def test_rollback_executor_blocks_wrong_digest_before_writes(tmp_path: Path) -> None:
    _write_approved_rollback_artifact(tmp_path)

    result = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest="wrong",
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "request_digest_required_or_mismatched" in result["blockers"]
    assert not (tmp_path / result["future_rollback_exact_once_marker_path"]).exists()


def test_rollback_executor_requires_operator_approved_rollback_artifact(tmp_path: Path) -> None:
    _execute_live_install(tmp_path)
    preview = build_rollback_approval(tmp_path, manifest=_manifest())
    request = build_rollback_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )

    result = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "approval_status_not_approved" in result["blockers"]
    assert "operator_decision_not_approved" in result["blockers"]
    assert "operator_approval_statement_missing_or_mismatched" in result["blockers"]
    assert "approval_decision_record_missing" in result["blockers"]


def test_rollback_executor_blocks_manual_approval_without_decision_sidecar(tmp_path: Path) -> None:
    _execute_live_install(tmp_path)
    preview = build_rollback_approval(tmp_path, manifest=_manifest())
    request = build_rollback_approval(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    artifact_path = tmp_path / request["approval_artifact_path"]
    _manually_approve_artifact_without_decision(artifact_path)

    result = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=True,
    )

    assert result["ok"] is False
    assert result["registry_updated"] is False
    assert "approval_decision_record_missing" in result["blockers"]
    assert "approval_decision_artifact_path_missing" in result["blockers"]
    assert not (tmp_path / result["future_rollback_exact_once_marker_path"]).exists()


def test_rollback_executor_blocks_duplicate_execution(tmp_path: Path) -> None:
    preview, _artifact_path = _write_approved_rollback_artifact(tmp_path)
    first = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )
    second = build_rollback_execution(
        tmp_path,
        manifest=_manifest(),
        request_digest=preview["request_digest_sha256"],
        execute=True,
    )

    assert first["rollback_executed"] is True
    assert second["ok"] is False
    assert second["registry_updated"] is False
    assert "rollback_exact_once_marker_already_present" in second["blockers"]
    assert "approval_already_consumed" in second["blockers"]
    assert "live_registry_entry_not_installed" in second["blockers"]
