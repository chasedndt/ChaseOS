"""Browser Operator Skill Layer helpers."""

from .candidates import (
    BrowserSkillCandidateError,
    candidate_promotion_preflight,
    list_candidate_records,
    preflight_candidate_promotion,
    show_candidate_record,
    storage_reconciliation,
)
from .registry import iter_skill_paths, list_skills, load_skill
from .validator import (
    BrowserSkillValidationError,
    BrowserSkillValidationResult,
    assert_valid_skill,
    validate_skill,
    validate_skill_file,
)

_SHADOW_EXPORTS = {
    "BrowserSkillShadowError",
    "BrowserSkillShadowProof",
    "run_skill_shadow_proof",
}


def __getattr__(name: str):
    """Lazy-load shadow runner exports so `python -m` execution stays clean."""
    if name in _SHADOW_EXPORTS:
        from . import shadow_runner

        return getattr(shadow_runner, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BrowserSkillCandidateError",
    "BrowserSkillValidationError",
    "BrowserSkillValidationResult",
    "BrowserSkillShadowError",
    "BrowserSkillShadowProof",
    "assert_valid_skill",
    "candidate_promotion_preflight",
    "iter_skill_paths",
    "list_candidate_records",
    "list_skills",
    "load_skill",
    "preflight_candidate_promotion",
    "run_skill_shadow_proof",
    "show_candidate_record",
    "storage_reconciliation",
    "validate_skill",
    "validate_skill_file",
]
