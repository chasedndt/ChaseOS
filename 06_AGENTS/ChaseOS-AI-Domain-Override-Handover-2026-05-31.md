# ChaseOS.ai Domain Override + Runtime Split Handover

**Date:** 2026-05-31  
**Status:** Domain decision override / launch execution alignment  
**Primary domain now selected:** `chaseos.ai`  
**Supersedes:** prior assumption that `chaseos.systems` is the selected primary launch domain.

---

## 1. Domain decision

The launch domain is now:

```text
https://chaseos.ai
```

Treat this as the current public home for ChaseOS.

`chaseos.systems` may still be purchased later, but it is no longer the primary launch assumption. If purchased, it should be used as a redirect, standards/ecosystem alias, or secondary brand asset, not as the current source of truth.

### Current domain hierarchy

```text
Primary public domain:
chaseos.ai

Future optional secondary:
chaseos.systems

Product:
ChaseOS

App:
ChaseOS Studio

Marketplace / ecosystem:
Chaser Forge

Future managed runtime:
Managed Agents / Chaser Agent
```

---

## 2. Immediate repo truth change

Any repo document, website plan, Forge plan, roadmap, V1 cutline, README, or public launch document saying:

```text
Primary domain: chaseos.systems
Public index target: https://chaseos.systems/forge/index.json
```

must be updated to:

```text
Primary domain: chaseos.ai
Public index target: https://chaseos.ai/forge/index.json
```

Do not delete older handovers. Add a supersession note where appropriate.

Recommended note:

```text
Domain update 2026-05-31:
chaseos.ai is now the selected primary public domain. Prior chaseos.systems launch assumptions are superseded. chaseos.systems may remain a future secondary/redirect/standards domain if purchased.
```

---

## 3. Public website routes

Build the first public site around `chaseos.ai`:

```text
/
 /waitlist
 /studio
 /forge
 /forge/index.json
 /standards
 /open-core
 /pricing
 /docs
 /download
 /privacy
 /security
 /roadmap
 /support
 /terms
 /creators
 /submit-pack
```

### Minimal first launch

The first launch site does not need all pages fully finished.

Minimum live set:

```text
/
 /waitlist
 /studio
 /forge
 /standards
 /open-core
 /privacy
 /roadmap
```

`/pricing`, `/download`, `/support`, `/terms`, `/creators`, and `/submit-pack` can exist as honest preview pages if not ready.

---

## 4. Chaser Forge public index target

Chaser Forge should target:

```text
https://chaseos.ai/forge/index.json
```

Initial status:

```text
Static preview index only.
No paid marketplace.
No creator payouts.
No untrusted remote pack install without validation.
No payment/licensing mutation until payment and entitlement infrastructure are real.
```

The Forge preview should show:

```text
free example packs
manifest standard
pack install preview
creator submission waitlist
certification model
future paid pack model
9% creator-pack fee policy
```

---

## 5. Monetization truth

Keep the monetization stack:

```text
Free local core
Pro Builder around £19/month
runtime credits/top-ups
premium workflow packs
Chaser Forge 9% marketplace fee
setup sprints
managed agents later
teams/enterprise later
```

But do not implement or claim live payments unless explicitly built and approved.

Runtime credits can be specified and planned now, but not enabled unless billing/account/entitlement infrastructure is real.

---

## 6. Runtime split for this pass

Two runtimes will work in parallel:

### Hermes

Hermes is the product/strategy/orchestration/docs/review runtime.

Hermes owns:

```text
strategy alignment
Kanban / Agent Box task planning
domain override propagation
repo documentation updates
public copy and website information architecture
launch/video/GitHub readiness planning
safety boundaries
acceptance criteria
reviewing Codex outputs
documentation-history notes
```

### Codex

Codex is the implementation/build/test/runtime-integration runtime.

Codex owns:

```text
website scaffold
waitlist implementation
admin panel implementation
Cloudflare/Vercel config stubs
Forge static index
standards/docs pages
Studio V1 polish where scoped
tests/smoke scripts
scheduled tasks/cron job definitions
CI/build verification
safe public GitHub readiness implementation
```

Both must read all launch handovers, but they must not duplicate work. Hermes plans and audits. Codex builds and tests.

---

## 7. Go Mode rule

Both runtimes may be started with `/go mode`.

Go Mode means:

```text
Read the handovers.
Apply the chaseos.ai domain override first.
Create or update Kanban / Agent Box tasks.
Execute bounded changes.
Do not ask for clarification unless blocked by missing repo files, missing credentials, or conflicting canonical docs.
Mark tasks READY / PARTIAL / BLOCKED / FUTURE.
Create build logs and documentation-history notes.
Provide final handover.
```

Go Mode does not mean:

```text
deploy externally
mutate DNS
send emails
create Stripe products
make repo public
publish package registries
enable managed agents
enable arbitrary browser automation
process waitlist PII through model providers
```

---

## 8. Safety / legal checks

Surface-level public search is not legal clearance.

The repo should include a launch checklist requiring:

```text
UK trademark keyword search
USPTO trademark search
Companies House name check
GitHub organization/name check
package namespace checks where relevant
registrar ownership confirmation
DNS verification
no secret leakage
no private path leakage
no unsupported claims
```

Public docs should say:

```text
ChaseOS is Early Access.
Some automation paths are preview-only.
External actions remain approval-gated or blocked unless supported by verified executors.
```

---

## 9. Website copy update

Primary line:

```text
ChaseOS is the local-first AI operating system for builders running real projects with agents.
```

Expanded line:

```text
ChaseOS turns scattered AI chats, docs, repos, sources, agents, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.
```

Public-home line:

```text
Start at chaseos.ai.
```

Forge line:

```text
Chaser Forge is the ecosystem for ChaseOS workflow packs, operating kits, standards, and extensions.
```

---

## 10. Acceptance criteria

This pass is complete when:

```text
README and public-facing docs use chaseos.ai as primary.
ROADMAP/NEXT-STEPS/V1 cutline no longer assume chaseos.systems as primary.
Forge docs target https://chaseos.ai/forge/index.json.
Website plan targets chaseos.ai.
Waitlist/admin plan targets chaseos.ai.
Cloudflare/Vercel deploy plan targets chaseos.ai.
Video/GitHub readiness docs target chaseos.ai.
Kanban tasks are split between Hermes and Codex.
Build log exists.
Documentation-history note exists.
Remaining blockers are listed.
```

---

## 11. Important warning

Do not let the domain change reopen the whole brand strategy.

The product remains:

```text
ChaseOS
```

The app remains:

```text
ChaseOS Studio
```

The marketplace remains:

```text
Chaser Forge
```

The future hosted runtime remains:

```text
Managed Agents / Chaser Agent
```

The launch posture remains:

```text
ChaseOS Studio Early Access
```

The only primary strategy change is:

```text
chaseos.ai is now the selected public domain.
```
