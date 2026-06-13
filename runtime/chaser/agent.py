"""
runtime.chaser.agent

Bounded ChaserAgent Phase A preview interface.

This module creates in-memory proposal packets. It does not execute tools, call
providers, claim Agent Bus tasks, write memory, or mutate canonical state.
"""

from __future__ import annotations

from typing import Any

from runtime.chaser.artifacts import build_artifact_manifest_item
from runtime.chaser.board import create_board_card, validate_board_card
from runtime.chaser.memory import build_memory_boundary
from runtime.chaser.policies import build_policy_snapshot, merge_authority_evidence
from runtime.chaser.profiles import get_profile, validate_profile_view
from runtime.chaser.toolsets import get_toolset, validate_toolset_view


def preview_chaser_task(
    *,
    operator_intent: str,
    vault_root: str = ".",
    profile_id: str = "default",
    toolset_id: str = "none",
    target_workspace: str = "",
    target_session: str = "",
    result_shape: str = "proposal",
) -> dict[str, Any]:
    """Build a no-authority ChaserAgent task preview."""

    profile = get_profile(profile_id)
    toolset = get_toolset(toolset_id)
    card = create_board_card(
        operator_intent=operator_intent,
        target_workspace=target_workspace,
        target_session=target_session,
        proposed_profile=profile["profile_id"],
        proposed_toolset=toolset["toolset_id"],
        result_shape=result_shape,
    )
    artifact = build_artifact_manifest_item(
        artifact_type="proposal",
        title="ChaserAgent task preview",
        source=card["task_id"],
    )
    memory_boundary = build_memory_boundary(vault_root)
    authority = merge_authority_evidence(
        profile,
        toolset,
        card.get("validation", {}),
        artifact,
        memory_boundary,
    )
    profile_validation = validate_profile_view(profile)
    toolset_validation = validate_toolset_view(toolset)
    board_validation = validate_board_card(card)
    blocked_reasons = []
    for report in (profile_validation, toolset_validation, board_validation, authority):
        blocked_reasons.extend(report.get("errors", []) or report.get("blocked_reasons", []))
    return {
        "ok": not blocked_reasons,
        "runtime_id": "chaser",
        "status": "preview_only_not_live",
        "operator_intent": str(operator_intent or ""),
        "board_card": card,
        "profile": profile,
        "toolset": toolset,
        "artifact_manifest": {"ok": artifact["valid"], "items": [artifact]},
        "memory_boundary": memory_boundary,
        "policy_snapshot": build_policy_snapshot(),
        "authority": authority["authority"],
        "authority_ok": authority["ok"],
        "blocked_reasons": blocked_reasons,
        "external_effects_performed": False,
    }


class ChaserAgent:
    """Tiny no-authority facade for future backend/API callers."""

    def __init__(self, *, vault_root: str = ".") -> None:
        self.vault_root = vault_root

    def preview_task(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("vault_root", self.vault_root)
        return preview_chaser_task(**kwargs)
