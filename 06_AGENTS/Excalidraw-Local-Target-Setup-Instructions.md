---
title: Excalidraw Local Target Setup Instructions
type: browser-runtime-operator-handoff
status: COMPLETE TARGETED / NO EXECUTION
created: 2026-05-03
updated: 2026-05-03
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Excalidraw Local Target Setup Instructions

This document defines the operator/runtime handoff required before ChaseOS runs an Excalidraw browser/MCP proof.

This is an instruction artifact only. It does not install dependencies, start an MCP server, launch a browser, connect to CDP, navigate to a target, write trusted skills, activate skills, enqueue Agent Bus work, call providers, mutate Gate policy, or write canonical ChaseOS state.

## Current Blocker

The previous live-readiness pass is safely blocked because no local loopback Excalidraw/canvas target URL was provided.

Evidence:

- `07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json`

The readiness evidence confirms:

- prep evidence exists,
- browser controller posture is ready without launch,
- no real profile, credentials, cookies, public tunnel, MCP invocation, browser launch, CDP connection, trusted skill write, activation, Agent Bus enqueue, provider call, Gate mutation, or canonical writeback occurred.

## Required External Runtime Action

An external runtime or the operator must provide a safe local target before the next ChaseOS pass.

Acceptable target URL shape:

```text
http://127.0.0.1:<port>/
http://localhost:<port>/
```

Preferred setup modes:

| Mode | Use | Boundary |
| --- | --- | --- |
| Local static canvas fixture | First target availability proof | Loopback only; no account; no MCP required |
| Local Excalidraw/MCP target | Future browser/MCP canvas proof | Loopback only; no public tunnel; no account |
| Public Excalidraw fallback | Later fallback only | Requires separate explicit approval; no account |

ChaseOS should receive only the loopback URL. ChaseOS should not install, start, or own the target in this pass.

## Readiness Rerun

After the external runtime provides a loopback target, rerun readiness:

```powershell
python -m runtime.browser_runtime.excalidraw_mcp_live_readiness --vault-root . --local-target-url http://127.0.0.1:<port>/ --write-readiness --json
```

The operator can first persist the loopback target response through the canonical `chaseos` CLI:

```powershell
$env:CHASEOS_EXCALIDRAW_TARGET_URL = "http://127.0.0.1:<port>/"
chaseos operate browser excalidraw-target-response --from-env --write-response --json
```

This intake command validates loopback URL shape only. It does not probe the target, launch a browser, or invoke MCP.

This command is still a no-execution readiness command. It should not launch a browser or invoke MCP. It only verifies that ChaseOS has a local target URL and records readiness evidence.

## Future Live Proof Boundary

The live browser/MCP proof is a separate later pass. It will require explicit approval after target readiness is recorded.

Future proof goal:

```text
draw one rectangle and label it "ChaseOS"
```

Future outputs, if approved:

- Browser Run log under `07_LOGS/Browser-Runs/`
- screenshot under `07_LOGS/Browser-Runs/`
- Agent Activity log under `07_LOGS/Agent-Activity/`
- draft skill under `06_AGENTS/Browser-Skills/_drafts/`
- untrusted candidate under `03_INPUTS/Browser-Skill-Candidates/`

## Skill Memory Rule

Any Excalidraw knowledge learned from a future proof must remain draft/untrusted until reviewed.

Allowed durable memory:

- canvas bounds strategy,
- stable selectors or page structure,
- waits and traps,
- verification approach,
- failed selectors or brittle approaches to avoid.

Forbidden memory:

- secrets,
- cookies,
- session tokens,
- account state,
- collaboration/share links,
- raw personal data,
- real browser history,
- durable raw pixel coordinates as the primary skill.

## Generated Evidence

The setup-instructions pass writes:

- `07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json`

Status after this pass:

```text
COMPLETE TARGETED / NO EXECUTION
```

Next recommended pass:

```text
excalidraw-local-browser-mcp-live-readiness-with-target
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
