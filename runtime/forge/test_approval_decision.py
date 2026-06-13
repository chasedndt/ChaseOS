from __future__ import annotations

import json
from pathlib import Path

from runtime.forge.approval_decision import (
    FORGE_APPROVAL_DECISION_RECORD_TYPE,
    FORGE_APPROVAL_DECISION_SURFACE_ID,
    build_forge_approval_decision_handoff,
    forge_rejection_confirmation_text,
)
from runtime.forge.panel import load_demo_manifest
from runtime.forge.registry import (
    LIVE_INSTALL_APPROVAL_RECORD_TYPE,
    LIVE_INSTALL_APPROVAL_RELATIVE_DIR,
    LIVE_INSTALL_APPROVAL_SCOPE,
    build_sandbox_install_approval,
    build_sandbox_registry_write_execution,
)


def _sandbox_request(vault: Path) -> tuple[dict, Path]:
    manifest = load_demo_manifest()
    preview = build_sandbox_install_approval(vault, manifest=manifest)
    request = build_sandbox_install_approval(
        vault,
        manifest=manifest,
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    return request, vault / request["approval_artifact_path"]


def test_forge_approval_decision_preview_does_not_write(tmp_path: Path) -> None:
    request, artifact_path = _sandbox_request(tmp_path)

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=request["approval_artifact_path"],
        decision="approved",
        expected_request_digest=request["request_digest_sha256"],
    )

    assert handoff["ok"] is True
    assert handoff["surface"] == FORGE_APPROVAL_DECISION_SURFACE_ID
    assert handoff["status"] == "forge_approval_decision_preview_ready"
    assert handoff["decision_artifact_written"] is False
    assert handoff["approval_artifact_mutated"] is False
    assert not (tmp_path / handoff["decision_artifact_path"]).exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pending_operator_decision"
    assert payload["operator_decision"] == "pending"


def test_forge_approval_decision_approves_source_artifact_without_execution(tmp_path: Path) -> None:
    request, artifact_path = _sandbox_request(tmp_path)
    source_payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=request["approval_artifact_path"],
        decision="approve",
        expected_request_digest=request["request_digest_sha256"],
        operator_statement=source_payload["operator_confirmation_text"],
        write_decision=True,
        reviewer_id="operator",
        generated_at="2026-05-20T00:00:00Z",
    )

    assert handoff["ok"] is True
    assert handoff["status"] == "forge_approval_decision_recorded"
    assert handoff["decision_artifact_written"] is True
    assert handoff["approval_artifact_mutated"] is True
    assert handoff["approval_consumed"] is False
    assert handoff["registry_written"] is False
    assert handoff["extension_files_written"] == []
    assert handoff["exact_once_marker_reserved"] is False

    decision_artifact = tmp_path / handoff["decision_artifact_path"]
    assert decision_artifact.is_file()
    decision_payload = json.loads(decision_artifact.read_text(encoding="utf-8"))
    assert decision_payload["record_type"] == FORGE_APPROVAL_DECISION_RECORD_TYPE
    assert decision_payload["operator_decision"] == "approved"
    assert decision_payload["approval_consumed"] is False
    assert decision_payload["registry_written"] is False
    assert decision_payload["extension_files_written"] == []

    approved_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approved_payload["status"] == "approved"
    assert approved_payload["operator_decision"] == "approved"
    assert approved_payload["operator_approval_statement"] == approved_payload["operator_confirmation_text"]
    assert approved_payload["approval_consumed"] is False
    assert approved_payload["decision_artifact_path"] == handoff["decision_artifact_path"]

    ready = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=load_demo_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=False,
    )
    assert ready["ok"] is True
    assert ready["registry_written"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()
    assert not (tmp_path / request["future_exact_once_marker_path"]).exists()


def test_forge_executor_blocks_tampered_decision_sidecar(tmp_path: Path) -> None:
    request, artifact_path = _sandbox_request(tmp_path)
    source_payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=request["approval_artifact_path"],
        decision="approved",
        expected_request_digest=request["request_digest_sha256"],
        operator_statement=source_payload["operator_confirmation_text"],
        write_decision=True,
        generated_at="2026-05-20T00:00:00Z",
    )
    assert handoff["ok"] is True
    decision_artifact = tmp_path / handoff["decision_artifact_path"]
    decision_payload = json.loads(decision_artifact.read_text(encoding="utf-8"))
    decision_payload["operator_decision"] = "rejected"
    decision_artifact.write_text(json.dumps(decision_payload, indent=2) + "\n", encoding="utf-8")

    blocked = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=load_demo_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=True,
    )

    assert blocked["ok"] is False
    assert blocked["registry_written"] is False
    assert "approval_decision_not_approved" in blocked["blockers"]
    assert "approval_decision_digest_mismatch" in blocked["blockers"]
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()
    assert not (tmp_path / request["future_exact_once_marker_path"]).exists()


def test_forge_approval_decision_blocks_wrong_digest_without_writes(tmp_path: Path) -> None:
    request, artifact_path = _sandbox_request(tmp_path)
    source_payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=request["approval_artifact_path"],
        decision="approved",
        expected_request_digest="wrong-digest",
        operator_statement=source_payload["operator_confirmation_text"],
        write_decision=True,
    )

    assert handoff["ok"] is False
    assert "expected_request_digest_mismatch" in handoff["blockers"]
    assert handoff["decision_artifact_written"] is False
    assert handoff["approval_artifact_mutated"] is False
    assert not (tmp_path / handoff["decision_artifact_path"]).exists()
    unchanged_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert unchanged_payload["status"] == "pending_operator_decision"
    assert unchanged_payload["operator_decision"] == "pending"


def test_forge_approval_decision_rejects_and_keeps_executor_blocked(tmp_path: Path) -> None:
    request, artifact_path = _sandbox_request(tmp_path)
    source_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    rejection_statement = forge_rejection_confirmation_text(source_payload, "sandbox")

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=request["approval_artifact_path"],
        decision="rejected",
        expected_request_digest=request["request_digest_sha256"],
        operator_statement=rejection_statement,
        write_decision=True,
        generated_at="2026-05-20T00:00:00Z",
    )

    assert handoff["ok"] is True
    assert handoff["decision_artifact_written"] is True
    rejected_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert rejected_payload["status"] == "rejected"
    assert rejected_payload["operator_decision"] == "rejected"
    assert rejected_payload["operator_rejection_statement"] == rejection_statement
    assert rejected_payload["approval_consumed"] is False

    blocked = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=load_demo_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=False,
    )
    assert blocked["ok"] is False
    assert "approval_status_not_approved" in blocked["blockers"]
    assert "operator_decision_not_approved" in blocked["blockers"]
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / "extensions" / "ugc-campaign-studio").exists()
    assert not (tmp_path / request["future_exact_once_marker_path"]).exists()


def test_forge_approval_decision_routes_live_family_decisions_to_live_decision_root(tmp_path: Path) -> None:
    root = tmp_path / LIVE_INSTALL_APPROVAL_RELATIVE_DIR
    root.mkdir(parents=True)
    artifact_path = root / "live.json"
    payload = {
        "record_type": LIVE_INSTALL_APPROVAL_RECORD_TYPE,
        "schema_version": "forge.live_install_approval_request.v1",
        "status": "pending_operator_decision",
        "approval_packet_id": "forge-live-install-appr-demo",
        "request_digest_sha256": "live-digest",
        "operator_decision": "pending",
        "approval_scope": LIVE_INSTALL_APPROVAL_SCOPE,
        "extension_id": "ugc-campaign-studio",
        "extension_name": "UGC Campaign Studio",
        "extension_version": "0.1.0",
        "operator_confirmation_text": "APPROVE FORGE LIVE TEST REQUEST ONLY",
        "approved_material": {"requested_action": "request_forge_live_install", "extension_id": "ugc-campaign-studio"},
        "approval_consumed": False,
    }
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=artifact_path,
        decision="approved",
        expected_request_digest="live-digest",
        operator_statement=payload["operator_confirmation_text"],
        write_decision=True,
    )

    assert handoff["ok"] is True
    assert handoff["family"] == "live-install"
    assert handoff["decision_artifact_path"].startswith(
        "07_LOGS/Agent-Activity/_forge_live_install_approvals/_decisions/"
    )
    assert (tmp_path / handoff["decision_artifact_path"]).is_file()
    updated = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert updated["status"] == "approved"
    assert updated["operator_decision"] == "approved"
    assert updated["approval_consumed"] is False
