---
type: browser-site-skill-draft
status: draft
created: 2026-04-30T01:56:55.856600+00:00
domain: example.com
run_id: browser_runtime_20260430_015655_example-com
activation_allowed: false
review_required: true
---

# Browser Site Skill Draft - example.com

This draft was generated from browser run evidence. It is not active runtime memory.

## Review Boundary

- Status: draft only
- Activation allowed: false
- Promotion target: reviewed SiteOps Site Skill Card or Workflow Manifest only after approval
- Secrets/cookies/credentials/session tokens: forbidden

## Evidence

- Source run: `%CHASEOS_VAULT_ROOT%\07_LOGS\Browser-Runs\browser_runtime_20260430_015655_example-com.json`
- Evidence link: `%CHASEOS_VAULT_ROOT%\07_LOGS\Browser-Runs\browser_runtime_20260430_015655_example-com.json`
- Evidence link: `%CHASEOS_VAULT_ROOT%\07_LOGS\Agent-Activity\browser-runtime-20260430-015655-example-com.md`

## Safe Actions Observed

- `capture_state_summary`
- `get_state`
- `open`

## Forbidden Actions

- `credential_field_fill`
- `cookie_export`
- `form_submit`
- `real_profile_reuse`
- `skill_auto_activation`

## Machine Record

```json
{
  "draft_id": "draft_browser_runtime_20260430_015655_example-com",
  "domain": "example.com",
  "status": "draft",
  "run_id": "browser_runtime_20260430_015655_example-com",
  "source_log_path": "%CHASEOS_VAULT_ROOT%\\07_LOGS\\Browser-Runs\\browser_runtime_20260430_015655_example-com.json",
  "created_at": "2026-04-30T01:56:55.856600+00:00",
  "observed_urls": [
    "https://example.com"
  ],
  "safe_actions": [
    "capture_state_summary",
    "get_state",
    "open"
  ],
  "forbidden_actions": [
    "credential_field_fill",
    "cookie_export",
    "form_submit",
    "real_profile_reuse",
    "skill_auto_activation"
  ],
  "selectors": [],
  "workflow_notes": [
    "Generated as draft-only Browser Runtime Adapter evidence.",
    "Requires review before promotion to SiteOps Site Skill Card or workflow manifest.",
    "No secrets, cookies, credentials, or user profile data were retained."
  ],
  "evidence_links": [
    "%CHASEOS_VAULT_ROOT%\\07_LOGS\\Browser-Runs\\browser_runtime_20260430_015655_example-com.json",
    "%CHASEOS_VAULT_ROOT%\\07_LOGS\\Agent-Activity\\browser-runtime-20260430-015655-example-com.md"
  ],
  "review_required": true,
  "activation_allowed": false
}
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
