---
title: ChaseOS Provider and Integration Setup CLI Plan
type: architecture
status: seeded
created: 2026-04-25
updated: 2026-04-25
phase: phase-9-active
---

# ChaseOS Provider and Integration Setup CLI Plan

> This document defines how provider/runtime setup and messaging/integration setup should appear in the ChaseOS command tree.

---

## 1. Why This Exists

The current runtime inventory surface can discover provider/runtime-shaped ids such as:
- `claude`
- `openai`
- `local_oss`
- `n8n`

These are not all active lifecycle-backed runtimes on the current machine in the same sense as:
- `openclaw`
- `hermes`

But they are still real user-facing setup targets because they represent choices the operator may want to configure.

That means ChaseOS needs a command family for:
- provider setup
- API key setup
- local model/runtime setup
- integration/channel setup
- guided menu-driven onboarding

without confusing those setup/configuration surfaces with active lifecycle-backed runtime monitoring.

---

## 2. Recommended Design Principle

Separate:

### A. runtime inventory
What runtime lanes are currently known and monitorable on this machine?

### B. provider setup
What model providers or automation backends can the user configure for future use?

### C. integration setup
What messaging or delivery surfaces can the user attach?

These should not be collapsed into a single runtime-status command.

---

## 3. Recommended New Top-Level Family

```text
chaseos setup ...
```

This should become the home for guided configuration and onboarding flows.

---

## 4. Proposed Command Tree

```text
chaseos setup provider list
chaseos setup provider show <provider-id>
chaseos setup provider enable <provider-id>
chaseos setup provider disable <provider-id>
chaseos setup provider wizard
chaseos setup provider wizard <provider-id>

chaseos setup integration list
chaseos setup integration show <integration-id>
chaseos setup integration wizard
chaseos setup integration wizard <integration-id>

chaseos setup runtime wizard
chaseos setup menu
```

---

## 5. Recommended Provider Targets

### `claude`
Purpose:
- configure Anthropic-backed provider use
- attach API keys or approved local auth patterns
- define model defaults / fallback behavior

### `openai`
Purpose:
- configure OpenAI-backed provider use
- attach API keys
- select model defaults and reasoning policy

### `local_oss`
Purpose:
- configure local/self-hosted OSS model lane
- define local endpoint, model registry, or launcher assumptions
- validate model availability

### `n8n`
Purpose:
- configure workflow automation bridge / webhook / connector path
- define URL, auth secret, and workflow ownership boundaries

These should be treated as **setup/configuration targets**, not as automatically active runtime lanes unless/until explicitly activated and lifecycle-backed.

---

## 6. Recommended Integration Targets

### Messaging / operator surfaces
- Discord
- Telegram
- Slack
- future WhatsApp / email / webhook forms

These are integration surfaces, not model providers.

They belong under something like:

```text
chaseos setup integration wizard discord
chaseos setup integration wizard telegram
chaseos setup integration wizard slack
```

---

## 7. Menu / Wizard Recommendation

Yes, a menu system is the right direction.

Recommended operator flow:

```text
chaseos setup menu
```

Possible menu:

```text
ChaseOS Setup Menu
1. Configure model/provider
2. Configure runtime lane
3. Configure messaging integration
4. Validate current setup
5. Show configured providers and integrations
```

Then branching into guided wizards.

This is better than expecting the user to memorize provider-specific commands from day one.

---

## 8. Suggested Information Architecture Diagram

```text
                    chaseos
                       |
   -------------------------------------------------
   |               |             |         |        |
 runtime         gate         setup       run    schedule
   |                            |
   |                  -----------------------
   |                  |          |          |
 inventory         provider   integration  runtime
 status              |           |          |
 health              |           |          |
 health-debug        |           |          |
                     |           |          |
             claude/openai   discord/   hermes/openclaw
             local_oss/n8n   telegram/  setup-wizard
                              slack
```

---

## 9. Machine Model Diagram

```text
Monitorable runtime lanes
- openclaw
- hermes

Configurable provider targets
- claude
- openai
- local_oss
- n8n

Configurable integration targets
- discord
- telegram
- slack
```

This distinction is critical.

---

## 10. Recommended Next Steps

### Step 1
Keep `runtime inventory/status/health` focused on lifecycle-backed runtime lanes.

### Step 2
Create a new setup/configuration family for:
- providers
- integrations
- guided setup menu

### Step 3
Add machine-readable setup manifests or config records for provider/integration targets.

### Step 4
Only after setup records exist, consider promoting configured providers into richer runtime/control views where appropriate.

---

## 11. Recommendation

My recommendation is:
- do **not** treat `claude`, `openai`, `local_oss`, and `n8n` as equal to active runtime lanes in `runtime status`
- do treat them as first-class setup/configuration targets under a new `chaseos setup ...` family
- do add a menu/wizard layer because this is clearly headed toward operator onboarding and machine configuration, not just expert CLI use

That is the cleanest command model for ChaseOS as an operating system.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
