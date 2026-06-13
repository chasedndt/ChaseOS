"""Safe executable proof for the Browser Runtime Adapter spike."""

from __future__ import annotations

from pathlib import Path

from runtime.browser_runtime.adapter import ShadowBrowserRuntimeAdapter
from runtime.browser_runtime.candidates import create_and_write_skill_candidate
from runtime.browser_runtime.logging import persist_run_evidence, vault_root
from runtime.browser_runtime.models import BrowserRunRequest, BrowserRuntimeConfig, BrowserRuntimeProvider
from runtime.browser_runtime.site_memory import update_site_activity_ledger
from runtime.browser_runtime.skills import create_and_write_site_skill_draft


def run_shadow_smoke(*, root: Path | str | None = None) -> dict:
    """Run the first safe proof without launching a real browser."""
    root_path = vault_root(root)
    config = BrowserRuntimeConfig(
        enabled=True,
        allowed_providers=[BrowserRuntimeProvider.SHADOW.value],
        allowed_domains=["example.com"],
    )
    request = BrowserRunRequest(
        url="https://example.com",
        task="Safe Browser Runtime Adapter shadow proof against a public test page.",
        provider=BrowserRuntimeProvider.SHADOW,
        mode="shadow",
        harmless_action="capture_state_summary",
    )
    adapter = ShadowBrowserRuntimeAdapter(config=config)
    result = adapter.run_task(request, vault_root=root_path)
    persisted = persist_run_evidence(result, request, root=root_path)
    _, draft_path = create_and_write_site_skill_draft(
        persisted,
        root=root_path,
        source_log_path=persisted.browser_run_log_path,
    )
    _, candidate_path = create_and_write_skill_candidate(persisted, root=root_path)
    site_activity_path = update_site_activity_ledger(
        persisted,
        root=root_path,
        candidate_path=candidate_path,
        draft_path=draft_path,
    )
    final = type(persisted)(
        **{
            **persisted.as_dict(),
            "provider": persisted.provider,
            "actions": persisted.actions,
            "artifacts": persisted.artifacts,
            "skill_candidate_path": candidate_path,
            "skill_draft_path": draft_path,
            "site_activity_log_path": site_activity_path,
        }
    )
    persisted_again = persist_run_evidence(final, request, root=root_path)
    return {
        "ok": persisted_again.status == "succeeded",
        "run_id": persisted_again.run_id,
        "browser_run_log_path": persisted_again.browser_run_log_path,
        "agent_activity_log_path": persisted_again.agent_activity_log_path,
        "skill_candidate_path": candidate_path,
        "skill_draft_path": draft_path,
        "site_activity_log_path": site_activity_path,
        "status": persisted_again.status,
        "provider": persisted_again.provider.value,
        "security_flags": persisted_again.security_flags,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_shadow_smoke(), indent=2))
