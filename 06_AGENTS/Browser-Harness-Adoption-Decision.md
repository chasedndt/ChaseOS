---
title: Browser Harness Adoption Decision
type: architecture-decision
status: complete targeted / reference-only
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
knowledge_class: canonical-state
---

# Browser Harness Adoption Decision

## Decision

ChaseOS will **adapt Browser Harness patterns, not adopt raw Browser Harness authority**.

Machine-readable decision:

```powershell
python -m runtime.browser_runtime.browser_harness_adoption --json
```

Current result:

```text
status: reference_only_raw_harness_not_adopted
adoption_mode: adapt_patterns_do_not_copy_or_run
browser_harness_adopted: false
browser_harness_js_adopted: false
raw_cdp_surface_adopted: false
```

This resolves the Browser Harness adoption-decision blocker. It does not authorize Browser Harness execution, real-profile attachment, remote browser provisioning, profile sync, raw CDP snippets, trusted skill writes, skill activation, Agent Bus enqueue, provider calls, Gate mutation, or canonical writeback.

## External Repos Inspected

Checked on 2026-05-02:

| Repo | License | Relevant pattern | ChaseOS decision |
| --- | --- | --- | --- |
| `browser-use/browser-harness` | MIT | Thin CDP harness, domain skills, interaction skills, persistent daemon | Reference only; adapt skills lifecycle behind AOR/Gate/SiteOps |
| `browser-use/browser-harness-js` | MIT | Typed direct CDP method surface over persistent session | Reference only; too much raw CDP authority for direct adoption |
| `browser-use/workflow-use` | AGPL-3.0 | Generate/store/replay workflows | Concept reference only; no code copy without license review |

Primary sources:

- `https://github.com/browser-use/browser-harness`
- `https://github.com/browser-use/browser-harness/blob/main/SKILL.md`
- `https://github.com/browser-use/browser-harness-js`
- `https://github.com/browser-use/workflow-use`

## Adopted Patterns

ChaseOS adopts these ideas as ChaseOS-owned patterns:

- domain skill memory as reviewed SiteOps/BOSL candidates,
- interaction skill taxonomy for reusable browser mechanics,
- screenshots and page observations as run evidence,
- search existing site skills before inventing a new site flow,
- contribute durable selectors, waits, traps, and failure patterns back as reviewable candidates.

## Rejected Patterns

ChaseOS rejects these by default:

- attaching directly to the operator's real Chrome profile,
- running free-form browser Python or CDP snippets from prompt text,
- allowing agents to edit live helper files mid-run as an authority path,
- syncing cookies or browser profiles into the runtime by default,
- provisioning remote/cloud browser sessions without an explicit approval contract,
- auto-promoting generated domain skills into active runtime memory.

## Gated Future Patterns

These may be considered later only through separate architecture, policy, and verification passes:

- ChaseOS-native Browser Harness compatibility wrapper with throwaway profile only,
- domain-skill import from external repos into untrusted review candidates,
- interaction-skill taxonomy import into docs or inactive registry records,
- workflow replay cache after license and implementation review,
- authenticated/session-bearing runs only through explicit AOR manifests and approvals.

## Required ChaseOS Controls

Any future harness-derived adapter must require:

- AOR workflow manifest,
- Gate operation check,
- allowed-domain policy,
- throwaway browser profile by default,
- no credential/cookie/profile export,
- Agent Activity log,
- Browser Run log,
- draft-only skill candidate generation,
- human/operator review before promotion,
- no canonical writeback from browser evidence.

## Current Status

Status: COMPLETE TARGETED / REFERENCE ONLY.

Browser Harness is not installed, not run, not imported as code, and not adopted as a runtime authority layer. The useful patterns are now represented in ChaseOS policy and completion status.

Production Browser Runtime remains not done because full VincisOS product UI proof, Browser Use CLI live validation, workflow replay/cache, live Excalidraw browser/MCP proof, and Studio/operator UI remain incomplete or deferred.

## Graph Links

[[Browser-Runtime-Feature-Readiness-Tracker]] - [[Browser-Runtime-Completion-Status]] - [[Browser-Runtime-Harness]] - [[Browser-Harness-Boundaries]] - [[Browser-Runtime-Test-Plan]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
