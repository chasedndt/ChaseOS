---
type: browser-site-skill-replay-evidence
status: draft-replay-evidence
created: 2026-05-01T00:05:13+01:00
domain: 127.0.0.1
run_id: vincisos_draft_skill_replay_20260501_success
source_draft: draft-vincisos-inapp-browser-20260430
activation_allowed: false
review_required: true
---

# VincisOS Draft Skill Replay Evidence

This note records a replay of the draft-only VincisOS local shadow target skill. It is evidence for review, not active runtime memory.

## Source Draft

- Source draft: `06_AGENTS/Browser-Skills/_drafts/draft-vincisos-inapp-browser-20260430.md`
- Source run: `07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json`
- Replay run: `07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_success.json`
- Replay screenshot: `07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_screenshot.png`

## Replay Result

- Result: succeeded with fallback.
- The draft selector `[data-test-action="toggle-runtime-state"]` loaded and resolved to exactly one element.
- The stored verification selector `#runtime-state` worked.
- The stored negative selector `#event-log` still resolved to zero elements.
- The in-app browser selector click failed at the browser click-translation layer.
- The selector `Enter` fallback did not activate the button.
- A visible local fixture click fallback changed `#runtime-state` to `Shadow state: inspected`.

## Durable Memory Update Candidate

- Keep `[data-test-action="toggle-runtime-state"]` as the primary durable selector.
- Keep `#runtime-state` as the primary verification selector.
- Keep `#event-log` as a known absent selector for the current fixture.
- Record that Codex in-app browser selector click can fail on this local fixture when the visible button sits near the left edge of the viewport.
- Do not promote coordinate fallback into durable skill memory except as a local-only troubleshooting note.

## Fresh-Tab Hardening Update

Follow-up evidence on 2026-05-01 showed that a fresh in-app browser tab clicks `[data-test-action="toggle-runtime-state"]` successfully without fallback:

```text
07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_success.json
```

Refined durable candidate:

- Prefer fresh-tab setup before replaying this local fixture.
- Keep the selector; it is not invalid.
- Treat the previous click failure as stale-tab or browser-state behavior unless reproduced from a fresh tab.
- Screenshot capture remains a separate hardening blocker for this pass.

## Review Boundary

- Status: draft replay evidence.
- Active skill promotion: false.
- Trusted Browser Skill write: false.
- SiteOps Skill Card write: false.
- Canonical ChaseOS writeback: false.
- Real profile, saved credentials, cookies, session tokens, browser history, account state, public tunnels, and CDP are forbidden.

## Machine Record

```json
{
  "run_id": "vincisos_draft_skill_replay_20260501_success",
  "source_draft": "06_AGENTS/Browser-Skills/_drafts/draft-vincisos-inapp-browser-20260430.md",
  "status": "draft-replay-evidence",
  "activation_allowed": false,
  "promotion_performed": false,
  "primary_selector": "[data-test-action=\"toggle-runtime-state\"]",
  "verification_selector": "#runtime-state",
  "negative_selector": "#event-log",
  "selector_count": 1,
  "negative_selector_count": 0,
  "final_state": "Shadow state: inspected",
  "final_attr": "inspected",
  "fallback_required": true,
  "fallback_kind": "local-visible-cua-click",
  "do_not_promote": [
    "raw screen coordinates",
    "real profile assumptions",
    "cookies",
    "credentials",
    "session state"
  ]
}
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
