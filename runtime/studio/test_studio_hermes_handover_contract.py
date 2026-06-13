"""Tests for the bounded Phase 10 Studio-Hermes handover contract."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.studio_hermes_handover_contract import (
    BACKEND_AUTHORITY_PROOF_FIELDS,
    CHECKPOINT_REQUIRED_FIELDS,
    DEPENDENCY_REPORT_FIELDS,
    build_studio_hermes_handover_contract,
)


def test_studio_hermes_handover_contract_exposes_phase10_checkpoint_shape(tmp_path: Path) -> None:
    contract = build_studio_hermes_handover_contract(
        tmp_path,
        current_surface="Phase 10 Studio / Hermes-Optimus handover verifier",
        active_cards=[
            {"id": "t_dfdc821d", "title": "P10-10B handover narrative", "status": "todo"},
            {"id": "t_484b2c4c", "title": "P10-10C verifier", "status": "running"},
        ],
        tests_or_smokes=[
            "PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_studio_hermes_handover_contract.py -q"
        ],
    )
    handover = contract["handover"]
    checkpoint = handover["checkpoint_contract"]

    assert contract["ok"] is True
    assert contract["read_only"] is True
    assert contract["surface"] == "studio_hermes_handover_contract"
    assert contract["phase"] == "Phase 10 Studio"
    assert contract["runtime_lane"] == "Hermes/Optimus"
    assert handover["current_surface"] == "Phase 10 Studio / Hermes-Optimus handover verifier"
    assert {card["id"] for card in handover["active_p10_p11_cards"]} == {"t_dfdc821d", "t_484b2c4c"}
    assert checkpoint["tests_or_smokes"] == [
        "PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_studio_hermes_handover_contract.py -q"
    ]
    assert set(CHECKPOINT_REQUIRED_FIELDS).issubset(checkpoint)
    assert checkpoint["authority_posture"].startswith("Phase 10 Studio surface only")
    assert checkpoint["stale_or_blocked_card_summary"]


def test_studio_hermes_handover_defaults_track_live_card_status_and_mvp_truth(tmp_path: Path) -> None:
    contract = build_studio_hermes_handover_contract(tmp_path)
    handover = contract["handover"]
    cards = {card["id"]: card["status"] for card in handover["active_p10_p11_cards"]}
    encoded = json.dumps(contract, sort_keys=True)

    assert cards["t_dfdc821d"] == "done"
    assert cards["t_484b2c4c"] == "done"
    assert cards["t_fee4398a"] == "blocked"
    assert cards["t_9311101c"] == "done"
    assert handover["studio_mvp_truth"] == {
        "current_status": "internal portable MVP closed with deferrals",
        "product_status": "INTERNAL_PORTABLE_CLOSED_RELEASE_GRADE_OPEN",
        "internal_portable_mvp_closed": True,
        "release_grade_complete": False,
        "release_grade_status": "release-grade Studio remains open",
    }
    assert "internal portable MVP closed with deferrals" in encoded
    assert "release-grade Studio remains open" in encoded
    assert "PARTIAL / NOT FULLY CLOSED" not in encoded


def test_studio_hermes_handover_dependency_reports_use_required_fields(tmp_path: Path) -> None:
    contract = build_studio_hermes_handover_contract(tmp_path)
    reports = contract["handover"]["dependency_reports"]

    assert contract["dependency_report_required_fields"] == DEPENDENCY_REPORT_FIELDS
    assert len(reports) >= 5
    for report in reports:
        for field in DEPENDENCY_REPORT_FIELDS:
            assert report[field]
        assert report["complete"] is True

    keys = {report["dependency_key"] for report in reports}
    assert "native_packaged_visual_qa_webview2" in keys
    assert "approval_execution_for_chat_studio_actions" in keys
    assert "runtime_provider_browser_execution" in keys
    assert "real_target_workspace_upgrade" in keys
    assert "release_installer_host_mutation" in keys


def test_studio_hermes_handover_denies_backend_authority(tmp_path: Path) -> None:
    contract = build_studio_hermes_handover_contract(tmp_path)
    proof = contract["handover"]["checkpoint_contract"]["no_backend_authority_proof"]
    authority = contract["authority"]

    assert list(proof) == BACKEND_AUTHORITY_PROOF_FIELDS
    assert all(value is False for value in proof.values())
    assert authority == {
        "surface_handoff_only": True,
        "aor_lifecycle_execution_allowed": False,
        "approval_consumption_allowed": False,
        "runtime_dispatch_allowed": False,
        "agent_bus_task_write_allowed": False,
        "provider_call_allowed": False,
        "browser_control_allowed": False,
        "credential_config_mutation_allowed": False,
        "source_pack_promotion_allowed": False,
        "protected_file_write_allowed": False,
        "gate_policy_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "release_installer_host_mutation_allowed": False,
    }


def test_studio_hermes_handover_marks_incomplete_custom_dependency_reports(tmp_path: Path) -> None:
    contract = build_studio_hermes_handover_contract(
        tmp_path,
        dependency_reports=[
            {
                "dependency_key": "approval_execution",
                "missing_contract": "approval consumption executor",
                "affected_phase10_or_phase11_surface": "Studio action preview",
                "lower_phase_owner_or_surface": "Gate and approval executor lane",
                "minimum_proof_needed": "exact-once marker and target-effect proof",
                # blocked_action_reason intentionally omitted to prove validation.
            }
        ],
    )
    report = contract["handover"]["dependency_reports"][0]

    assert report["dependency_key"] == "approval_execution"
    assert report["blocked_action_reason"] == ""
    assert report["complete"] is False


def test_studio_hermes_handover_template_is_json_safe_secret_free_and_no_write(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    contract = build_studio_hermes_handover_contract(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    encoded = json.dumps(contract, sort_keys=True)
    template = contract["template_markdown"]

    assert before == after
    assert "## Studio-Hermes Handover Checkpoint — <UTC timestamp>" in template
    assert "aor_lifecycle_execution=false" in template
    assert "approval_consumption=false" in template
    assert "runtime_dispatch=false" in template
    assert "agent_bus_task_write=false" in template
    assert "provider_call=false" in template
    assert "browser_control=false" in template
    assert "canonical_writeback=false" in template
    assert "fixture-secret-not-returned" not in encoded
    assert "API_KEY" not in encoded.upper()
