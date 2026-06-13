"""Tests for the final 10A0 Pulse cockpit closeout verifier."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from runtime.acquisition.research_imports import initialize_research_repository_template
from runtime.cli.main import main
from runtime.pulse.ten_a0_cockpit_closeout import (
    CONFIRMED_WRITE_CONTROL_IDS,
    READ_ONLY_CONTROL_IDS,
    REQUIRED_CONTROL_IDS,
    SCOPE_STATUS_CLOSED,
    build_pulse_ten_a0_cockpit_closeout,
)


def _make_vault(tmp_path: Path) -> Path:
    initialize_research_repository_template(tmp_path, profile="strikezone", confirm_action=True)
    return tmp_path


def test_ten_a0_cockpit_closeout_closes_scope_with_controls_and_boundaries(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    closeout = build_pulse_ten_a0_cockpit_closeout(vault).to_dict()

    assert closeout["surface"] == "pulse_ten_a0_cockpit_closeout"
    assert closeout["roadmap_item"] == "10A0 - Studio Acquisition Intake Cockpit"
    assert closeout["scope_status"] == SCOPE_STATUS_CLOSED
    assert closeout["closed"] is True
    assert closeout["no_further_10a0_pulse_cockpit_pass_required"] is True
    assert closeout["missing_modules"] == []
    assert closeout["missing_controls"] == []
    assert set(closeout["controls_present"]) == set(REQUIRED_CONTROL_IDS)
    assert closeout["invalid_read_only_controls"] == []
    assert closeout["invalid_confirmed_write_controls"] == []
    assert closeout["invalid_execution_controls"] == []
    assert closeout["missing_required_authority_claims"] == []
    assert closeout["unexpected_true_forbidden_authority_flags"] == []
    assert closeout["unexpected_true_model_authority_flags"] == []
    assert closeout["unexpected_model_writes"] == []
    assert closeout["closeout_failures"] == []
    assert closeout["implementation_evidence"]["authority_expanded"] is False
    assert closeout["implementation_evidence"]["approved_enqueue_action_id"] == "pulse-enqueue-approved"
    assert closeout["out_of_scope_remaining"]


def test_ten_a0_cockpit_closeout_detects_missing_controls(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    with patch("runtime.studio.acquisition_cockpit.build_acquisition_cockpit_model") as model:
        model.return_value = {
            "surface": "studio_acquisition_intake_cockpit",
            "writes": [],
            "authority": {},
            "pulse_roadmap_controls": {
                "status": "ready",
                "controls": [],
                "authority": {},
            },
        }
        closeout = build_pulse_ten_a0_cockpit_closeout(vault).to_dict()

    assert closeout["closed"] is False
    assert sorted(closeout["missing_controls"]) == sorted(REQUIRED_CONTROL_IDS)
    assert closeout["closeout_failures"]


def test_ten_a0_cockpit_closeout_control_sets_are_disjoint() -> None:
    assert not set(READ_ONLY_CONTROL_IDS).intersection(CONFIRMED_WRITE_CONTROL_IDS)
    assert set(READ_ONLY_CONTROL_IDS).issubset(REQUIRED_CONTROL_IDS)
    assert set(CONFIRMED_WRITE_CONTROL_IDS).issubset(REQUIRED_CONTROL_IDS)


def test_cli_reports_ten_a0_cockpit_closeout_json(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    out = StringIO()
    with patch("sys.stdout", out):
        rc = main([
            "pulse",
            "ten-a0-cockpit-closeout",
            "--vault-root",
            str(vault),
            "--json",
        ])

    assert rc == 0
    envelope = json.loads(out.getvalue())
    assert envelope["ok"] is True
    assert envelope["action"] == "pulse.ten-a0-cockpit-closeout"
    assert envelope["result"]["closed"] is True
    assert envelope["result"]["no_further_10a0_pulse_cockpit_pass_required"] is True
