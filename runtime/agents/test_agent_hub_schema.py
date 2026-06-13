from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.agents.agent_hub import AgentHub, create_runtime_profile
from runtime.agents.runtime_brain import RuntimeReflection
from runtime.agents.runtime_profile import RuntimeProfile
from runtime.pulse.card_schema import EvidenceRef


def test_agent_hub_registers_profile_and_brain_without_authority_expansion() -> None:
    profile = create_runtime_profile(
        "codex",
        provider="OpenAI",
        execution_surface="Codex development harness",
        access_mode="repo-aware coding agent",
        trust_tier="Tier 2 ceiling",
        status="registered",
    )
    hub = AgentHub()
    hub.register_profile(profile)

    payload = hub.to_dict()
    assert payload["runtime_ids"] == ["codex"]
    assert payload["governance"]["authority_expansion"] is False
    assert payload["governance"]["canonical_promotion_authority"] is False


def test_runtime_profile_cannot_grant_canonical_promotion() -> None:
    profile = RuntimeProfile(
        runtime_id="bad",
        provider="Unknown",
        execution_surface="test",
        access_mode="test",
        trust_tier="Tier 4",
        canonical_promotion_authority=True,
    )

    try:
        profile.validate()
    except ValueError as exc:
        assert "canonical promotion authority" in str(exc)
    else:
        raise AssertionError("profile should not grant canonical promotion")


def test_runtime_brain_reflection_can_emit_agent_pulse_card() -> None:
    profile = create_runtime_profile(
        "hermes",
        provider="Hermes",
        execution_surface="bounded bus lane",
        access_mode="workflow-manifest-declared",
        trust_tier="Tier 2 bounded",
        status="shadow",
    )
    hub = AgentHub()
    hub.register_profile(profile)
    brain = hub.get_brain("hermes")
    assert brain is not None
    brain.add_reflection(
        RuntimeReflection(
            reflection_id="r1",
            summary="Hermes stayed inside declared bus workflow boundaries.",
            evidence=[
                EvidenceRef(
                    source_path="HERMES.md",
                    source_type="runtime_doc",
                    summary="Hermes is bounded to approved workflows.",
                )
            ],
        )
    )

    card = brain.latest_reflection_card()
    assert card is not None
    assert card.audience == "agent"
    assert card.card_class == "Runtime Reflection"
    assert card.canonical_writeback_enabled is False


def test_runtime_brain_self_upgrade_is_blocked() -> None:
    profile = create_runtime_profile(
        "openclaw",
        provider="OpenClaw",
        execution_surface="bounded operator runtime",
        access_mode="schedule executor",
        trust_tier="Tier 2 bounded",
    )
    hub = AgentHub()
    hub.register_profile(profile)
    brain = hub.get_brain("openclaw")
    assert brain is not None
    brain.self_upgrade_active = True

    try:
        brain.validate()
    except ValueError as exc:
        assert "self-upgrade is not active" in str(exc)
    else:
        raise AssertionError("self-upgrade should be blocked")
