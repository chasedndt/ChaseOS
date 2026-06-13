"""Validation for Browser Operator Skill Layer skill files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .registry import load_yaml_file


REQUIRED_FIELDS = {
    "skill_id",
    "domain",
    "intent",
    "allowed_domains",
    "inputs_schema",
    "outputs_schema",
    "preconditions",
    "steps",
    "selectors",
    "fallbacks",
    "wait_conditions",
    "verification",
    "secret_policy",
    "source_runs",
    "approval_status",
    "risk_level",
    "last_verified",
}

APPROVAL_STATUSES = {
    "candidate_untrusted",
    "draft",
    "needs_review",
    "approved",
    "rejected",
    "deprecated",
}

RISK_LEVELS = {"low", "medium", "high", "blocked"}

CANDIDATE_APPROVAL_STATUSES = {"candidate_untrusted"}

FORBIDDEN_KEY_NAMES = {
    "api_key",
    "apikey",
    "auth_token",
    "authorization",
    "bearer_token",
    "cookie",
    "cookies",
    "credential",
    "credential_value",
    "credentials",
    "indexeddb",
    "local_storage",
    "localstorage",
    "password",
    "password_value",
    "profile_path",
    "session",
    "session_id",
    "session_token",
    "session_tokens",
    "storage_state",
    "token",
    "user_data_dir",
}

FORBIDDEN_ACTIONS = {
    "credential_fill",
    "download_file",
    "execute_shell",
    "file_download",
    "form_submit",
    "import_cookies",
    "load_personal_profile",
    "login",
    "raw_cdp",
    "read_browser_history",
    "shell",
}

SECRET_VALUE_MARKERS = (
    "authorization:",
    "bearer ",
    "cookie:",
    "cookie=",
    "session_token=",
    "sessionid=",
    "set-cookie:",
    "x-api-key:",
)

RELATIVE_COORDINATE_STRATEGIES = {
    "relative",
    "relative_canvas",
    "relative_element",
    "bounding_box_relative",
    "selector",
    "semantic",
}


@dataclass
class BrowserSkillValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skill_id: str | None = None
    approval_status: str | None = None
    risk_level: str | None = None


class BrowserSkillValidationError(ValueError):
    """Raised when a browser skill fails validation."""


def _normalise_key(value: str) -> str:
    return value.strip().replace("-", "_").replace(" ", "_").lower()


def _path_string(path: Iterable[str]) -> str:
    return ".".join(path)


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, path + (str(index),))


def _under_secret_policy(path: tuple[str, ...]) -> bool:
    return bool(path) and path[0] == "secret_policy"


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_required_shape(data: dict[str, Any], errors: list[str]) -> None:
    missing = sorted(field for field in REQUIRED_FIELDS if field not in data)
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    if not isinstance(data.get("allowed_domains"), list) or not data.get("allowed_domains"):
        errors.append("allowed_domains must be a non-empty list")
    if not isinstance(data.get("steps"), list) or not data.get("steps"):
        errors.append("steps must be a non-empty list")
    if not isinstance(data.get("secret_policy"), dict):
        errors.append("secret_policy must be a mapping")


def _validate_approval(data: dict[str, Any], candidate: bool, errors: list[str]) -> None:
    approval_status = data.get("approval_status")
    status = data.get("status")

    if approval_status not in APPROVAL_STATUSES:
        errors.append(
            "approval_status must be one of: "
            + ", ".join(sorted(APPROVAL_STATUSES))
        )
    if data.get("risk_level") not in RISK_LEVELS:
        errors.append("risk_level must be one of: " + ", ".join(sorted(RISK_LEVELS)))

    if candidate and approval_status not in CANDIDATE_APPROVAL_STATUSES:
        errors.append("skill candidates must keep approval_status=candidate_untrusted")

    if status == "approved" and approval_status != "approved":
        errors.append("status=approved requires approval_status=approved")
    if approval_status == "approved" and not data.get("last_verified"):
        errors.append("approved skills require last_verified")


def _validate_forbidden_material(data: dict[str, Any], errors: list[str]) -> None:
    for path, value in _walk(data):
        if not path:
            continue
        key = _normalise_key(path[-1])
        if not _under_secret_policy(path) and key in FORBIDDEN_KEY_NAMES:
            errors.append(f"forbidden browser/secret field present: {_path_string(path)}")
        if isinstance(value, str):
            lower = value.lower()
            if any(marker in lower for marker in SECRET_VALUE_MARKERS):
                errors.append(f"forbidden secret-like value present at {_path_string(path)}")


def _step_coordinate_error(step: dict[str, Any], index: int) -> str | None:
    strategy = str(
        step.get("coordinate_strategy")
        or step.get("target_strategy")
        or step.get("locator_strategy")
        or ""
    ).strip().lower()

    coordinates = step.get("coordinates")
    if isinstance(coordinates, dict):
        has_absolute_xy = _is_number(coordinates.get("x")) and _is_number(coordinates.get("y"))
        has_relative_xy = _is_number(coordinates.get("x_pct")) and _is_number(coordinates.get("y_pct"))
        if has_absolute_xy and not has_relative_xy and strategy not in RELATIVE_COORDINATE_STRATEGIES:
            return f"step {index} uses raw absolute-only pixel coordinates"

    has_step_absolute_xy = _is_number(step.get("x")) and _is_number(step.get("y"))
    has_step_relative_xy = _is_number(step.get("x_pct")) and _is_number(step.get("y_pct"))
    if has_step_absolute_xy and not has_step_relative_xy and strategy not in RELATIVE_COORDINATE_STRATEGIES:
        return f"step {index} uses raw absolute-only x/y pixel coordinates"

    if strategy in {"absolute", "raw_pixels", "pixel", "pixels"}:
        return f"step {index} declares forbidden coordinate_strategy={strategy}"

    return None


def _validate_steps(data: dict[str, Any], errors: list[str]) -> None:
    steps = data.get("steps")
    if not isinstance(steps, list):
        return

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"step {index} must be a mapping")
            continue
        for required in ("step_id", "action", "target"):
            if required not in step:
                errors.append(f"step {index} missing required field: {required}")

        action = str(step.get("action", "")).strip().lower()
        if action in FORBIDDEN_ACTIONS:
            errors.append(f"step {index} uses forbidden action: {action}")

        coordinate_error = _step_coordinate_error(step, index)
        if coordinate_error:
            errors.append(coordinate_error)


def _validate_policy_flags(data: dict[str, Any], errors: list[str]) -> None:
    if data.get("credentials_required") is True:
        errors.append("credentials_required must not be true")
    if data.get("canonical_writeback") is True:
        errors.append("canonical_writeback must not be true")

    secret_policy = data.get("secret_policy")
    if isinstance(secret_policy, dict):
        for key in ("credentials", "cookies", "session_tokens"):
            value = str(secret_policy.get(key, "")).strip().lower()
            if value and value not in {"forbidden", "none", "redacted_only"}:
                errors.append(f"secret_policy.{key} must be forbidden/none/redacted_only")


def validate_skill(
    data: dict[str, Any],
    *,
    source_path: Path | str | None = None,
    candidate: bool | None = None,
) -> BrowserSkillValidationResult:
    """Validate a browser skill mapping."""
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(source_path) if source_path is not None else None
    candidate_mode = bool(candidate)
    if candidate is None and path is not None:
        candidate_mode = "Browser-Skill-Candidates" in path.parts

    _validate_required_shape(data, errors)
    _validate_approval(data, candidate_mode, errors)
    _validate_forbidden_material(data, errors)
    _validate_steps(data, errors)
    _validate_policy_flags(data, errors)

    if data.get("mode") == "shadow" and data.get("approval_status") == "approved":
        warnings.append("approved skill remains in shadow mode")

    return BrowserSkillValidationResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        skill_id=data.get("skill_id"),
        approval_status=data.get("approval_status"),
        risk_level=data.get("risk_level"),
    )


def validate_skill_file(
    path: Path | str,
    *,
    candidate: bool | None = None,
) -> BrowserSkillValidationResult:
    """Load and validate a browser skill YAML file."""
    skill_path = Path(path)
    data = load_yaml_file(skill_path)
    return validate_skill(data, source_path=skill_path, candidate=candidate)


def assert_valid_skill(
    data: dict[str, Any],
    *,
    source_path: Path | str | None = None,
    candidate: bool | None = None,
) -> None:
    """Raise BrowserSkillValidationError when validation fails."""
    result = validate_skill(data, source_path=source_path, candidate=candidate)
    if not result.ok:
        raise BrowserSkillValidationError("; ".join(result.errors))
