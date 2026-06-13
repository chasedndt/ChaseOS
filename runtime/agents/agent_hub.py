"""AgentHub registry facade for runtime profiles and brains."""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.agents.runtime_brain import AgentRuntimeBrain
from runtime.agents.runtime_profile import RuntimeProfile


@dataclass
class AgentHub:
    profiles: dict[str, RuntimeProfile] = field(default_factory=dict)
    brains: dict[str, AgentRuntimeBrain] = field(default_factory=dict)

    def register_profile(self, profile: RuntimeProfile) -> None:
        profile.validate()
        self.profiles[profile.runtime_id] = profile
        self.brains.setdefault(
            profile.runtime_id,
            AgentRuntimeBrain(runtime_id=profile.runtime_id, profile=profile),
        )

    def get_profile(self, runtime_id: str) -> RuntimeProfile | None:
        return self.profiles.get(runtime_id)

    def get_brain(self, runtime_id: str) -> AgentRuntimeBrain | None:
        brain = self.brains.get(runtime_id)
        if brain:
            brain.validate()
        return brain

    def runtime_ids(self) -> list[str]:
        return sorted(self.profiles)

    def to_dict(self) -> dict:
        return {
            "runtime_ids": self.runtime_ids(),
            "profiles": {key: value.to_dict() for key, value in self.profiles.items()},
            "brains": {key: value.to_dict() for key, value in self.brains.items()},
            "governance": {
                "authority_expansion": False,
                "canonical_promotion_authority": False,
            },
        }


def create_runtime_profile(
    runtime_id: str,
    *,
    provider: str,
    execution_surface: str,
    access_mode: str,
    trust_tier: str,
    status: str = "draft",
) -> RuntimeProfile:
    profile = RuntimeProfile(
        runtime_id=runtime_id,
        provider=provider,
        execution_surface=execution_surface,
        access_mode=access_mode,
        trust_tier=trust_tier,
        status=status,
    )
    profile.validate()
    return profile
