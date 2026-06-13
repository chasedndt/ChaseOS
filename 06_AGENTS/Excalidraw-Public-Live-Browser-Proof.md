---
title: Excalidraw Public Live Browser Proof
type: browser-runtime-proof
status: complete-targeted / public reachability proven / public drawing proof complete separately
created: 2026-05-05
updated: 2026-05-05
runtime: Codex
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio external branch
---

# Excalidraw Public Live Browser Proof

## Summary

The operator explicitly supplied the public Excalidraw target:

```text
https://excalidraw.com/
```

Codex ran the bounded public-site live browser proof through the existing ChaseOS command:

```powershell
chaseos operate browser excalidraw-live-proof --settle-ms 6000 --json
```

The proof succeeded. It verified public Excalidraw browser reachability, page title, canvas presence, and screenshot capture.

This is not the final Excalidraw browser/MCP drawing proof. It did not draw a rectangle, add text, invoke an MCP tool, consume an approval decision, reserve an idempotency marker, write a draft skill, or mutate canonical ChaseOS state.

## Target Configuration Truth

The public Excalidraw website is now registered inside ChaseOS as known Browser Runtime target `excalidraw`.

```text
target_id: excalidraw
url: https://excalidraw.com
allowed_domain: excalidraw.com
env_required: false
```

Future public Excalidraw reachability or no-login drawing-proof passes should use the ChaseOS known-target registry instead of asking the operator to paste the public URL again.

Do not set `CHASEOS_EXCALIDRAW_TARGET_URL` to `https://excalidraw.com`. That environment variable remains reserved for the stricter local loopback Excalidraw target-response lane.

## Live Result

```text
status: excalidraw_live_browser_proof_complete
target_url: https://excalidraw.com
title: Excalidraw Whiteboard
canvas_found: true
screenshot_bytes: 58227
```

Evidence:

```text
07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json
07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png
07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.md
```

There is also a later failed sandbox artifact from a non-escalated Playwright launch attempt. It is retained as failure evidence, but it does not invalidate the successful public proof above. The completion reporter scans for a valid successful proof record so sandbox failures do not make the status stale.

## Boundary

The run was limited to public read-only navigation and screenshot evidence. It preserved:

- no account login,
- no real browser profile,
- no credential read,
- no cookie export,
- no Browser Use CLI invocation,
- no raw CDP manipulation,
- no MCP invocation,
- no provider or connector call,
- no Agent Bus write,
- no Gate mutation,
- no approval execution,
- no vault markdown write from the browser command,
- no trusted skill write,
- no canonical ChaseOS mutation.

The command wrote only Browser Run evidence under `07_LOGS/Browser-Runs/`.

## Reporter Truth

`runtime.browser_runtime.completion_status` now recognizes this evidence as:

```text
production:excalidraw_public_live_browser_proof = complete_targeted
```

The separate no-login drawing-proof approval and run passes are now complete targeted:

```text
excalidraw-public-browser-drawing-proof-approval
status: excalidraw_public_browser_drawing_proof_approval_written_no_execution
approval_artifact: 07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals/excalidraw-public-drawing-appr-excalidraw-97ced9c2f559a285.json
excalidraw-public-browser-drawing-proof-run
status: excalidraw_public_browser_drawing_proof_complete
proof_artifact: 07_LOGS/Browser-Runs/excalidraw_public_drawing_proof_20260505-192722.json
```

The completion reporter now returns:

```text
overall_status: complete
production_feature_done: true
next_recommended_pass: phase10-studio-product-hardening
```

## Completed Drawing Proof Handoff

The completed drawing proof did the separate work required after this reachability proof:

- consumed the approval artifact by matching `approval_id` and `request_digest_sha256`,
- reserved and completed the exact-once idempotency marker before browser launch,
- drew exactly one rectangle plus the approved `ChaseOS proof` text label,
- used a throwaway isolated browser context,
- captured screenshot and JSON evidence,
- proved no login/profile/cookie/credential/provider/connector/Agent Bus/Gate/canonical effects.

Do not treat the public reachability proof by itself as drawing proof completion; use `06_AGENTS/Excalidraw-Public-Browser-Drawing-Proof-Run.md` and the `20260505-192722` Browser Run evidence for that.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
