from __future__ import annotations

import json
from pathlib import Path

from runtime.forge.approval_decision import (
    build_forge_approval_decision_handoff,
    forge_rejection_confirmation_text,
)
from runtime.forge.approval_decision_form import (
    FORGE_APPROVAL_DECISION_FORM_API_METHOD,
    FORGE_APPROVAL_DECISION_FORM_SURFACE_ID,
    build_forge_approval_decision_form,
)
from runtime.forge.panel import load_demo_manifest
from runtime.forge.registry import build_sandbox_install_approval, build_sandbox_registry_write_execution


def _sandbox_request(vault: Path) -> tuple[dict, Path, dict]:
    manifest = load_demo_manifest()
    preview = build_sandbox_install_approval(vault, manifest=manifest)
    request = build_sandbox_install_approval(
        vault,
        manifest=manifest,
        request_digest=preview["request_digest_sha256"],
        write_approval_request=True,
    )
    payload = json.loads((vault / request["approval_artifact_path"]).read_text(encoding="utf-8"))
    return request, vault / request["approval_artifact_path"], payload


def _option(form: dict, decision: str) -> dict:
    return next(item for item in form["decision_options"] if item["decision"] == decision)


def test_forge_operator_decision_form_prepares_exact_source_specific_payloads_without_writes(tmp_path: Path) -> None:
    request, artifact_path, source_payload = _sandbox_request(tmp_path)

    form = build_forge_approval_decision_form(
        tmp_path,
        approval_artifact_path=request["approval_artifact_path"],
        generated_at="2026-05-20T00:00:00Z",
    )

    assert form["ok"] is True
    assert form["surface"] == FORGE_APPROVAL_DECISION_FORM_SURFACE_ID
    assert form["status"] == "forge_approval_decision_form_ready"
    assert form["source_specific"] is True
    assert form["generic_approval_center_control"] is False
    assert form["preview_only"] is True
    assert form["form_preview_only"] is True
    assert form["write_decision_enabled_by_form_preview"] is False
    assert form["approval_artifact_mutated"] is False
    assert form["decision_artifact_written"] is False
    assert form["approval_consumption_allowed"] is False
    assert form["forge_execution_allowed"] is False
    assert form["registry_write_allowed"] is False
    assert form["extension_file_write_allowed"] is False
    assert form["exact_once_marker_reservation_allowed"] is False
    assert form["submit_contract"]["api_method"] == "review_chaser_forge_approval_decision"
    assert form["submit_contract"]["requires_exact_operator_statement"] is True
    assert form["available_decisions"] == ["approved", "rejected"]

    approved = _option(form, "approved")
    rejected = _option(form, "rejected")
    assert approved["required_operator_statement"] == source_payload["operator_confirmation_text"]
    assert rejected["required_operator_statement"] == forge_rejection_confirmation_text(source_payload, "sandbox")
    assert approved["submit_api_method"] == "review_chaser_forge_approval_decision"
    assert approved["submit_payload"]["approval_artifact_path"] == request["approval_artifact_path"]
    assert approved["submit_payload"]["expected_request_digest"] == request["request_digest_sha256"]
    assert approved["submit_payload"]["operator_statement"] == source_payload["operator_confirmation_text"]
    assert approved["submit_payload"]["write_decision"] is True
    assert not (tmp_path / approved["future_decision_artifact_path"]).exists()
    assert not (tmp_path / rejected["future_decision_artifact_path"]).exists()

    unchanged_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert unchanged_payload["status"] == "pending_operator_decision"
    assert unchanged_payload["operator_decision"] == "pending"
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()
    assert not (tmp_path / request["future_exact_once_marker_path"]).exists()


def test_forge_operator_decision_form_submit_payload_records_decision_without_execution(tmp_path: Path) -> None:
    request, artifact_path, _source_payload = _sandbox_request(tmp_path)
    form = build_forge_approval_decision_form(tmp_path, approval_artifact_path=request["approval_artifact_path"])
    approved = _option(form, "approved")

    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=approved["submit_payload"]["approval_artifact_path"],
        decision=approved["submit_payload"]["decision"],
        expected_request_digest=approved["submit_payload"]["expected_request_digest"],
        operator_statement=approved["submit_payload"]["operator_statement"],
        write_decision=approved["submit_payload"]["write_decision"],
        generated_at="2026-05-20T00:00:00Z",
    )

    assert handoff["ok"] is True
    assert handoff["status"] == "forge_approval_decision_recorded"
    assert handoff["decision_artifact_written"] is True
    assert handoff["approval_artifact_mutated"] is True
    assert handoff["approval_consumed"] is False
    assert (tmp_path / handoff["decision_artifact_path"]).is_file()
    approved_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approved_payload["status"] == "approved"
    assert approved_payload["approval_consumed"] is False

    ready = build_sandbox_registry_write_execution(
        tmp_path,
        manifest=load_demo_manifest(),
        request_digest=request["request_digest_sha256"],
        execute=False,
    )
    assert ready["ok"] is True
    assert ready["registry_written"] is False
    assert not (tmp_path / "runtime" / "forge" / "registry" / "extensions.json").exists()


def test_forge_operator_decision_form_blocks_decided_artifacts(tmp_path: Path) -> None:
    request, _artifact_path, _source_payload = _sandbox_request(tmp_path)
    form = build_forge_approval_decision_form(tmp_path, approval_artifact_path=request["approval_artifact_path"])
    approved = _option(form, "approved")
    handoff = build_forge_approval_decision_handoff(
        tmp_path,
        approval_artifact_path=approved["submit_payload"]["approval_artifact_path"],
        decision="approved",
        expected_request_digest=approved["submit_payload"]["expected_request_digest"],
        operator_statement=approved["submit_payload"]["operator_statement"],
        write_decision=True,
    )
    assert handoff["ok"] is True

    blocked = build_forge_approval_decision_form(tmp_path, approval_artifact_path=request["approval_artifact_path"])

    assert blocked["ok"] is False
    assert blocked["status"] == "blocked_forge_approval_decision_form"
    assert "approval_status_not_pending_operator_decision" in blocked["blockers"]
    assert "operator_decision_not_pending" in blocked["blockers"]
    assert blocked["approval_consumption_allowed"] is False
    assert blocked["forge_execution_allowed"] is False
    assert blocked["decision_artifact_written"] is False
    assert blocked["submit_contract"]["api_method"] == "review_chaser_forge_approval_decision"


def test_forge_operator_decision_form_blocks_outside_forge_approval_roots(tmp_path: Path) -> None:
    outside = tmp_path / "07_LOGS" / "not-forge.json"
    outside.parent.mkdir(parents=True)
    outside.write_text("{}", encoding="utf-8")

    form = build_forge_approval_decision_form(tmp_path, approval_artifact_path=outside)

    assert form["ok"] is False
    assert form["surface"] == FORGE_APPROVAL_DECISION_FORM_SURFACE_ID
    assert form["submit_contract"]["api_method"] == "review_chaser_forge_approval_decision"
    assert "approval_artifact_path_outside_forge_approval_roots" in form["blockers"]
    assert form["generic_approval_center_control"] is False
    assert form["approval_consumption_allowed"] is False
    assert form["forge_execution_allowed"] is False
    assert FORGE_APPROVAL_DECISION_FORM_API_METHOD == "get_chaser_forge_approval_decision_form"
