from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from runtime.browser_skills.registry import load_skill
from runtime.browser_skills.validator import validate_skill, validate_skill_file


def _valid_skill() -> dict:
    return {
        "schema_version": 0.1,
        "skill_id": "example.safe_skill",
        "domain": "example.com",
        "intent": "Read a public page state.",
        "status": "draft",
        "mode": "shadow",
        "account_required": False,
        "credentials_required": False,
        "canonical_writeback": False,
        "allowed_domains": ["https://example.com"],
        "inputs_schema": {},
        "outputs_schema": {},
        "preconditions": ["isolated browser profile"],
        "steps": [
            {
                "step_id": "open",
                "action": "navigate",
                "target": "https://example.com",
            },
            {
                "step_id": "verify",
                "action": "verify",
                "target": "page_title",
            },
        ],
        "selectors": {"page_title": {"css_candidates": ["title"]}},
        "fallbacks": [],
        "wait_conditions": [],
        "verification": {"page_title": {"method": "read_title"}},
        "secret_policy": {
            "credentials": "forbidden",
            "cookies": "forbidden",
            "session_tokens": "forbidden",
        },
        "source_runs": [],
        "approval_status": "draft",
        "risk_level": "low",
        "last_verified": None,
    }


def test_sample_excalidraw_skill_validates() -> None:
    result = validate_skill_file(
        Path("runtime/browser_skills/skills/excalidraw/draw_basic_shape.yaml")
    )

    assert result.ok is True
    assert result.skill_id == "excalidraw.draw_basic_shape"
    assert result.approval_status == "draft"


def test_registry_loads_sample_skill_by_id() -> None:
    skill = load_skill("excalidraw.draw_basic_shape")

    assert skill is not None
    assert skill["domain"] == "excalidraw.com"
    assert skill["mode"] == "shadow"


def test_invalid_skill_missing_required_fields_rejected() -> None:
    skill = _valid_skill()
    del skill["approval_status"]

    result = validate_skill(skill)

    assert result.ok is False
    assert any("missing required fields" in error for error in result.errors)


def test_secret_cookie_session_fields_rejected() -> None:
    skill = _valid_skill()
    skill["selectors"]["unsafe"] = {"session_token": "abc123"}

    result = validate_skill(skill)

    assert result.ok is False
    assert any("forbidden browser/secret field" in error for error in result.errors)


def test_secret_like_values_rejected() -> None:
    skill = _valid_skill()
    skill["notes"] = ["Authorization: Bearer abc123"]

    result = validate_skill(skill)

    assert result.ok is False
    assert any("forbidden secret-like value" in error for error in result.errors)


def test_raw_absolute_only_pixel_coordinate_skill_rejected() -> None:
    skill = _valid_skill()
    skill["steps"].append(
        {
            "step_id": "unsafe_click",
            "action": "click_selector",
            "target": "canvas",
            "coordinates": {"x": 240, "y": 120},
        }
    )

    result = validate_skill(skill)

    assert result.ok is False
    assert any("absolute-only" in error for error in result.errors)


def test_relative_coordinate_skill_allowed() -> None:
    skill = _valid_skill()
    skill["steps"].append(
        {
            "step_id": "safe_drag",
            "action": "drag",
            "target": "canvas",
            "coordinate_strategy": "relative_canvas",
            "coordinates": {"x_pct": 0.4, "y_pct": 0.6},
        }
    )

    result = validate_skill(skill)

    assert result.ok is True


def test_candidate_remains_untrusted() -> None:
    candidate = _valid_skill()
    candidate["approval_status"] = "approved"
    candidate["last_verified"] = "2026-04-30"

    result = validate_skill(candidate, candidate=True)

    assert result.ok is False
    assert any("candidate_untrusted" in error for error in result.errors)


def test_untrusted_candidate_validates_as_candidate_only() -> None:
    candidate = _valid_skill()
    candidate["status"] = "candidate"
    candidate["approval_status"] = "candidate_untrusted"
    candidate["risk_level"] = "medium"

    result = validate_skill(candidate, candidate=True)

    assert result.ok is True


def test_approved_skill_must_have_matching_approval_status() -> None:
    skill = deepcopy(_valid_skill())
    skill["status"] = "approved"
    skill["approval_status"] = "draft"

    result = validate_skill(skill)

    assert result.ok is False
    assert any("status=approved" in error for error in result.errors)
