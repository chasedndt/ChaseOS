"""
runtime.chaser.profiles

Read-only ChaserAgent profile views. Profiles describe posture and routing
preferences; they do not grant permissions.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from runtime.chaser.policies import CHASER_RUNTIME_ID, build_no_authority_report


CHASER_PROFILE_DOC = Path("06_AGENTS") / "ChaserAgent-Runtime-Profile.md"

_PROFILES: dict[str, dict[str, Any]] = {
    "default": {
        "profile_id": "default",
        "display_name": "Chaser Default",
        "status": "planned",
        "role": "bounded proposal and coordination preview",
        "recommended_toolsets": ["none"],
    },
    "research": {
        "profile_id": "research",
        "display_name": "Chaser Research",
        "status": "planned",
        "role": "source review and evidence synthesis preview",
        "recommended_toolsets": ["web-preview", "artifact-preview"],
    },
    "ops": {
        "profile_id": "ops",
        "display_name": "Chaser Ops",
        "status": "planned",
        "role": "runtime status and gateway diagnostic preview",
        "recommended_toolsets": ["terminal-preview", "gateway-diagnostic"],
    },
    "local": {
        "profile_id": "local",
        "display_name": "Chaser Local",
        "status": "planned",
        "role": "local-first context and session preview",
        "recommended_toolsets": ["session-preview", "artifact-preview"],
    },
    "builder": {
        "profile_id": "builder",
        "display_name": "Chaser Builder",
        "status": "planned",
        "role": "patch/proposal planning preview",
        "recommended_toolsets": ["repo-preview", "artifact-preview"],
    },
}


def list_profiles() -> list[dict[str, Any]]:
    """Return profile views with explicit no-authority metadata."""

    return [get_profile(profile_id) for profile_id in sorted(_PROFILES)]


def get_profile(profile_id: str = "default") -> dict[str, Any]:
    """Return one profile view; unknown profiles fail closed to default."""

    key = str(profile_id or "default").strip().lower()
    item = deepcopy(_PROFILES.get(key) or _PROFILES["default"])
    item.update(
        {
            "runtime_id": CHASER_RUNTIME_ID,
            "profile_doc": CHASER_PROFILE_DOC.as_posix(),
            "authority": build_no_authority_report(),
            "grants_permission": False,
            "activates_runtime": False,
            "calls_provider": False,
        }
    )
    return item


def validate_profile_view(profile: dict[str, Any]) -> dict[str, Any]:
    """Validate that a profile view remains descriptive only."""

    errors: list[str] = []
    if not isinstance(profile, dict):
        return {"ok": False, "errors": ["profile_not_object"]}
    if not profile.get("profile_id"):
        errors.append("missing_profile_id")
    if profile.get("grants_permission") is not False:
        errors.append("profile_must_not_grant_permission")
    if profile.get("activates_runtime") is not False:
        errors.append("profile_must_not_activate_runtime")
    if profile.get("calls_provider") is not False:
        errors.append("profile_must_not_call_provider")
    authority = profile.get("authority") or {}
    if any(bool(value) for value in authority.values()):
        errors.append("profile_authority_flags_must_be_false")
    return {"ok": not errors, "errors": errors}
