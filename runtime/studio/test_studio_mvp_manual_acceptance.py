"""Tests for Studio MVP manual install/launch acceptance intake."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.studio_mvp_manual_acceptance as acceptance_module
import runtime.studio.studio_mvp_operator_decision as decision_module
from runtime.studio.studio_mvp_manual_acceptance import (
    SURFACE_ID,
    build_studio_mvp_manual_acceptance,
    format_studio_mvp_manual_acceptance,
    validate_studio_mvp_manual_acceptance_evidence,
)
from runtime.studio.studio_mvp_operator_decision import (
    build_studio_mvp_closure_gate,
    build_studio_mvp_operator_decision_packet,
)
from runtime.studio.test_studio_mvp_operator_decision import _fake_closeout


def _visual_qa(vault: Path) -> Path:
    path = vault / "07_LOGS" / "Studio-Graph-Views" / "visual.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "surface": "studio_packaged_app_visual_qa",
                "status": "packaged_app_visual_qa_complete",
                "launch": {"started": True, "process_alive_before_capture": True},
                "screenshot": {
                    "exists": True,
                    "size_bytes": 1234,
                    "path": "07_LOGS/Studio-Graph-Views/visual.png",
                    "capture": {"window_title": "ChaseOS Studio"},
                    "visual_verification": {
                        "ok": True,
                        "reason": "nonblank",
                        "unique_color_count": 100,
                        "dominant_color_ratio": 0.3,
                    },
                },
                "termination": {"terminated": True},
                "authority": {
                    "writes_installer": False,
                    "writes_host_startup": False,
                    "mutates_gate": False,
                    "grants_approvals": False,
                    "executes_approval_decisions": False,
                    "executes_workflows": False,
                    "provider_calls_allowed": False,
                    "connector_calls_allowed": False,
                    "writes_agent_bus_tasks": False,
                    "canonical_mutation_allowed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _decision(vault: Path, monkeypatch) -> Path:
    monkeypatch.setattr(decision_module, "build_studio_mvp_deferral_closeout_audit", lambda *_args, **_kwargs: _fake_closeout())
    monkeypatch.setattr(acceptance_module, "build_studio_mvp_deferral_closeout_audit", lambda *_args, **_kwargs: _fake_closeout())
    packet = build_studio_mvp_operator_decision_packet(
        vault,
        acknowledge_preapproved_deferrals=True,
        write_decision=True,
        decision_slug="decision",
    )
    return vault / packet["evidence"]["json_path"]


def test_manual_acceptance_requires_operator_statement_even_with_valid_visual_qa(tmp_path: Path, monkeypatch) -> None:
    decision_path = _decision(tmp_path, monkeypatch)
    visual_path = _visual_qa(tmp_path)

    report = build_studio_mvp_manual_acceptance(
        tmp_path,
        decision_path=decision_path,
        automated_visual_qa_path=visual_path,
        accept_existing_automated_evidence=True,
    )

    assert report["accepted"] is False
    assert report["summary"]["automated_visual_qa_valid"] is True
    assert report["summary"]["operator_acceptance_statement_present"] is False
    assert "operator_acceptance_statement_missing" in report["blockers"]


def test_manual_acceptance_writes_valid_acceptance_evidence_and_closes_gate(tmp_path: Path, monkeypatch) -> None:
    decision_path = _decision(tmp_path, monkeypatch)
    visual_path = _visual_qa(tmp_path)

    report = build_studio_mvp_manual_acceptance(
        tmp_path,
        decision_path=decision_path,
        automated_visual_qa_path=visual_path,
        accept_existing_automated_evidence=True,
        operator_acceptance_statement="Operator accepts the existing packaged visual QA as sufficient for internal portable MVP launch acceptance.",
        write_acceptance=True,
        acceptance_slug="accepted",
    )
    validation = validate_studio_mvp_manual_acceptance_evidence(tmp_path, report["evidence"]["json_path"])
    packet = build_studio_mvp_operator_decision_packet(
        tmp_path,
        acknowledge_preapproved_deferrals=True,
        manual_acceptance_status="accepted",
        manual_acceptance_evidence_path=report["evidence"]["json_path"],
        write_decision=True,
        decision_slug="accepted-decision",
    )
    gate = build_studio_mvp_closure_gate(tmp_path, decision_path=packet["evidence"]["json_path"])

    assert report["accepted"] is True
    assert validation["valid"] is True
    assert packet["closed"] is True
    assert gate["closed"] is True
    assert gate["blockers"] == []


def test_manual_acceptance_formatter_and_validator_reject_invalid_file(tmp_path: Path, monkeypatch) -> None:
    decision_path = _decision(tmp_path, monkeypatch)
    visual_path = _visual_qa(tmp_path)
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"accepted": True}), encoding="utf-8")

    report = build_studio_mvp_manual_acceptance(
        tmp_path,
        decision_path=decision_path,
        automated_visual_qa_path=visual_path,
        accept_existing_automated_evidence=False,
        write_acceptance=True,
        acceptance_slug="preview",
    )
    text = format_studio_mvp_manual_acceptance(report)
    validation = validate_studio_mvp_manual_acceptance_evidence(tmp_path, invalid)

    assert report["surface"] == SURFACE_ID
    assert "Studio MVP Manual Install/Launch Acceptance" in text
    assert "no app launch" in text
    assert validation["valid"] is False
