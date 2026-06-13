---
type: browser-site-skill-draft
status: draft
created: 2026-04-30T22:04:08+01:00
domain: 127.0.0.1
run_id: vincisos_inapp_browser_20260430_success
activation_allowed: false
review_required: true
---

# Browser Site Skill Draft - VincisOS Local Shadow Target

This draft was generated from a ChaseOS-controlled in-app browser run against the local VincisOS shadow fixture. It is not active runtime memory and must not be promoted without review.

## Review Boundary

- Status: draft only.
- Activation allowed: false.
- Trusted Browser Skill write: false.
- SiteOps Skill Card write: false.
- Canonical ChaseOS writeback: false.
- Secrets, cookies, credentials, session tokens, browser history, real profile paths, and account data are forbidden.

## Evidence

- Source run: `07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json`
- Screenshot: `07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_screenshot.png`
- Agent activity: `07_LOGS/Agent-Activity/2026-04-30-codex-vincisos-inapp-browser-proof.md`
- Build log: `07_LOGS/Build-Logs/2026-04-30-ChaseOS-vincisos-inapp-browser-proof.md`

## Scope

- Domain scope: `127.0.0.1`
- Path observed: `/vincisos_shadow.html`
- Fixture source: `runtime/browser_runtime/test_targets/vincisos_shadow.html`
- Auth required: false
- External assets: false
- Public tunnel: false

## Safe Actions Observed

- Start a temporary loopback HTTP server for the static fixture.
- Navigate the in-app browser to `http://127.0.0.1:<port>/vincisos_shadow.html`.
- Read the page title and visible body text.
- Click the local harmless control selector `[data-test-action="toggle-runtime-state"]`.
- Verify state through `#runtime-state`.
- Capture screenshot evidence under `07_LOGS/Browser-Runs/`.
- Stop the temporary loopback server after the run.

## Durable Site Knowledge

- The fixture title is `VincisOS Shadow Test Target`.
- The main fixture element declares `data-vincisos-testbed="true"` in source, but the in-app browser DOM snapshot used in this run did not expose that attribute in the reduced snapshot.
- The `Inspect State` button is selected by `[data-test-action="toggle-runtime-state"]`.
- Successful inspection changes `#runtime-state` text from `Shadow state: idle` to `Shadow state: inspected`.
- Successful inspection changes `#runtime-state` `data-state` from `idle` to `inspected`.
- `#event-log` is not present in the current fixture and should not be used for verification.

## Forbidden Actions

- Do not use a real Chrome profile.
- Do not read or reuse saved credentials.
- Do not export cookies or session state.
- Do not import real browser history.
- Do not attach Browser Harness or raw CDP to a real profile.
- Do not submit forms or mutate accounts.
- Do not activate this skill automatically.
- Do not write trusted Browser Skill or SiteOps Skill Card artifacts without explicit promotion review.

## Machine Record

```json
{
  "draft_id": "draft-vincisos-inapp-browser-20260430",
  "status": "draft",
  "domain": "127.0.0.1",
  "run_id": "vincisos_inapp_browser_20260430_success",
  "source_log_path": "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json",
  "observed_urls": [
    "http://127.0.0.1:64929/vincisos_shadow.html"
  ],
  "safe_actions": [
    "navigate",
    "inspect_dom_state",
    "click",
    "read_selector",
    "screenshot"
  ],
  "selectors": [
    "[data-test-action=\"toggle-runtime-state\"]",
    "#runtime-state",
    "body"
  ],
  "negative_selectors": [
    "#event-log"
  ],
  "workflow_notes": [
    "Serve only the repo-local static fixture over 127.0.0.1.",
    "Use the Inspect State button as the first harmless action.",
    "Verify state through #runtime-state text and data-state attribute.",
    "Retain screenshots only under Browser-Runs evidence paths."
  ],
  "evidence_links": [
    "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json",
    "07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_screenshot.png",
    "07_LOGS/Agent-Activity/2026-04-30-codex-vincisos-inapp-browser-proof.md"
  ],
  "review_required": true,
  "activation_allowed": false
}
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
