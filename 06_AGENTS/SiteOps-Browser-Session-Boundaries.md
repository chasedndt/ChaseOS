---
title: SiteOps Browser Session Boundaries
status: PARTIAL
date: 2026-04-30
---

# SiteOps Browser Session Boundaries

Browser profiles are user/tenant-scoped opaque references.

## Built Now

UserBrowserProfileRef objects include:
- `browser_profile_ref_id`
- `tenant_id`
- `user_id`
- provider identifier such as `local_browser_use` or `local_playwright`
- allowed domains
- status and verification timestamps

Checks enforce tenant and user ownership. CLI output reports profile status only and does not expose cookies, localStorage, session values, or opaque session store internals.

## Not Built

No live Browser Use, Playwright, Browserbase, or Stagehand execution is invoked in this pass. Manual takeover, browser recording/replay, and cloud session stores remain future work.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
