---
title: SiteOps Agent Control Visual Affordance Proof
type: runtime-proof
status: COMPLETE TARGETED / LOCAL BROWSER CONTROL VISUAL AFFORDANCE VERIFIED / FULL COMPUTER CONTROL NOT BUILT
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Agent Control Visual Affordance Proof

This pass corrected the product feel of the local SiteOps Canva-style browser
proof. The prior proof used real CDP drag gestures, but normal toolbar actions
were silent DOM clicks, which made the run look robotic and under-signaled.

The local proof target now shows:

- an `Agent control active` HUD,
- a custom cursor icon,
- cursor movement trail dots,
- click and drag feedback rings,
- a browser-lane control indicator,
- future lane labels for `files`, `system`, and `runtime`.

The runtime proof now fails closed unless the final design state proves:

```text
agentControlVisible: true
agentCursorMoved: true
agentClickFeedbackShown: true
agentDragFeedbackShown: true
agentControlLane: browser
```

## Live Proof

Command:

```powershell
python -m runtime.browser_runtime.canva_style_autonomy_proof --vault-root . --execute-browser --run-slug siteops-agent-control-visual-affordance-proof-20260504-final --port 8766 --headed-browser --action-delay-ms 900 --final-pause-seconds 25 --json
```

Result:

```text
status: canva_style_autonomy_proof_complete
run_id: siteops-agent-control-visual-affordance-proof-20260504-final
scope: local/default/local-user
agentControlLane: browser
manualDrawingPointCount: 8
photoFrameSize: 222 x 178
```

Evidence:

```text
07_LOGS/Browser-Runs/local/default/siteops-agent-control-visual-affordance-proof-20260504-final.json
07_LOGS/Browser-Runs/local/default/siteops-agent-control-visual-affordance-proof-20260504-final.png
07_LOGS/Agent-Activity/local/default/2026-05-04-siteops-agent-control-visual-affordance-proof-20260504-final.md
07_LOGS/SiteOps-Runs/local/default/siteops-agent-control-visual-affordance-proof-20260504-final.json
07_LOGS/SiteOps-Audits/local/default/siteops-agent-control-visual-affordance-proof-20260504-final.jsonl
07_LOGS/SiteOps-Approvals/local/default/approval_siteops-agent-control-visual-affordance-proof-20260504-final.json
```

Inspection target:

```text
http://127.0.0.1:8766/siteops_canva_style_shadow.html
```

That static server is for visual inspection only. The live automation run used
a throwaway browser profile and closed after the proof.

## Product Direction

This is still the browser-control lane. The UI language now intentionally points
toward a broader controlled-computer surface where future governed runtimes can
operate browser, file, system, and runtime lanes.

Future expansion must still route through SiteOps/AOR/Gate-style governance:

- per-user sessions,
- explicit approvals for mutation,
- no secrets in prompts or logs,
- scoped artifacts,
- audit/provenance,
- visible operator feedback during control.

## Boundaries

This pass did not:

- open canva.com,
- use a real account,
- use a real browser profile,
- read cookies, tokens, credentials, localStorage, or sessionStorage,
- upload files,
- export or share publicly,
- mutate account settings,
- promote trusted Browser Skill artifacts,
- activate skills,
- enqueue Agent Bus work,
- call providers,
- mutate Gate policy,
- expand Hermes authority,
- implement file explorer/system control,
- write canonical ChaseOS memory/state.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
