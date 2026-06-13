"""Known Browser Runtime targets that do not require operator URL input."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class KnownBrowserTarget:
    target_id: str
    url: str
    allowed_domains: tuple[str, ...]
    public_target: bool
    login_required: bool
    env_required: bool
    authority_profile: str
    notes: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["allowed_domains"] = list(self.allowed_domains)
        return payload


KNOWN_BROWSER_TARGETS: dict[str, KnownBrowserTarget] = {
    "excalidraw": KnownBrowserTarget(
        target_id="excalidraw",
        url="https://excalidraw.com",
        allowed_domains=("excalidraw.com",),
        public_target=True,
        login_required=False,
        env_required=False,
        authority_profile="public_no_login_browser_proof",
        notes=(
            "Known public Excalidraw canvas target. Public reachability and "
            "future no-login drawing proofs do not require CHASEOS_EXCALIDRAW_TARGET_URL."
        ),
    ),
}


def get_known_browser_target(target_id: str) -> KnownBrowserTarget:
    key = target_id.strip().lower()
    try:
        return KNOWN_BROWSER_TARGETS[key]
    except KeyError as exc:
        raise ValueError(f"unknown browser target: {target_id}") from exc


def list_known_browser_targets() -> tuple[KnownBrowserTarget, ...]:
    return tuple(KNOWN_BROWSER_TARGETS[key] for key in sorted(KNOWN_BROWSER_TARGETS))

