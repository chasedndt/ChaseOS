from __future__ import annotations

import json
from copy import deepcopy

from runtime.browser_skills.registry import load_skill
from runtime.browser_skills.shadow_runner import (
    BrowserSkillShadowError,
    _build_result,
    assert_shadow_safe_skill,
    format_untrusted_candidate,
    normalize_allowed_domains,
    run_skill_shadow_proof,
)
from runtime.browser_skills.validator import validate_skill


def test_allowed_domain_normalization_accepts_origins_and_domains() -> None:
    assert normalize_allowed_domains(["https://excalidraw.com", "localhost:8765/path"]) == [
        "excalidraw.com",
        "localhost",
    ]


def test_excalidraw_shadow_proof_is_plan_only_without_persisting() -> None:
    proof = run_skill_shadow_proof("excalidraw.draw_basic_shape", persist=False)

    assert proof.ok is True
    assert proof.skill_id == "excalidraw.draw_basic_shape"
    assert proof.live_browser_control is False
    assert proof.browser_run_log_path is None
    assert proof.candidate_path is None
    assert any(action["action_type"] == "drag" for action in proof.planned_actions)
    assert all(action["status"] == "planned" for action in proof.planned_actions)


def test_shadow_safety_rejects_non_shadow_mode() -> None:
    skill = deepcopy(load_skill("excalidraw.draw_basic_shape"))
    assert skill is not None
    skill["mode"] = "approved_action"

    try:
        assert_shadow_safe_skill(skill)
    except BrowserSkillShadowError as exc:
        assert "mode=shadow" in str(exc)
    else:
        raise AssertionError("non-shadow skill should be rejected")


def test_shadow_safety_rejects_canonical_output_destination() -> None:
    skill = deepcopy(load_skill("excalidraw.draw_basic_shape"))
    assert skill is not None
    skill["outputs_schema"]["canonical_note"] = {
        "type": "string",
        "destination": "02_KNOWLEDGE/AI-Agents/",
    }

    try:
        assert_shadow_safe_skill(skill)
    except BrowserSkillShadowError as exc:
        assert "canonical" in str(exc)
    else:
        raise AssertionError("canonical output destination should be rejected")


def test_candidate_markdown_stays_untrusted() -> None:
    skill = load_skill("excalidraw.draw_basic_shape")
    assert skill is not None
    proof = run_skill_shadow_proof("excalidraw.draw_basic_shape", persist=False)
    _, result = _build_result(skill, run_id=proof.run_id)

    text = format_untrusted_candidate(skill, result, validation_warnings=[])

    assert "status: candidate_untrusted" in text
    assert "activation_allowed: false" in text
    assert "UNTRUSTED CANDIDATE" in text
    assert '"live_browser_control": false' in text


def test_candidate_markdown_contains_validator_compatible_machine_candidate() -> None:
    skill = load_skill("excalidraw.draw_basic_shape")
    assert skill is not None
    proof = run_skill_shadow_proof("excalidraw.draw_basic_shape", persist=False)
    _, result = _build_result(skill, run_id=proof.run_id)

    text = format_untrusted_candidate(skill, result, validation_warnings=[])
    machine_json = text.split("```json", 1)[1].split("```", 1)[0].strip()
    machine_candidate = json.loads(machine_json)
    validation = validate_skill(machine_candidate, candidate=True)

    assert "## Machine Candidate" in text
    assert validation.ok is True
    assert machine_candidate["candidate_id"].startswith("candidate_bosl_shadow_")
    assert machine_candidate["approval_status"] == "candidate_untrusted"
    assert machine_candidate["activation_allowed"] is False
    assert machine_candidate["live_browser_control"] is False
