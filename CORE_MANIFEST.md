# CORE_MANIFEST.md
## ChaseOS Core Inventory Seed

> Explicit inventory of material that belongs in the reusable ChaseOS Core layer.
> This file is the contract between the current personal instance and the future standalone/framework repository.

**Version:** 0.3  
**Created:** 2026-04-24  
**Updated:** 2026-05-11  
**Owner label:** Optimus
**Refactor note:** Codex GPT-5 CLI consolidation and Core export hardening pass

---

## Purpose

This manifest exists to answer one question clearly:

**What can be moved or mirrored into a forkable/public `chaseos-core` layer without bringing private personal context with it?**

If a file is not clearly safe, it should not be assumed to be Core.

---

## Core-Included Categories

### 1. Structural / Framework Docs
Include when sanitized and framework-valid:
- `README.md`
- `PROJECT_FOUNDATION.md`
- `ROADMAP.md`
- `FORKING.md`
- `SOUL.template.md`

### 2. Governance / Routing Docs
Include when generic or sanitized:
- `06_AGENTS/Vault-Map.md`
- `06_AGENTS/Execution-Adapter-Standard.md`
- `06_AGENTS/Agent-Output-Conventions.md`
- `06_AGENTS/Agent-Security-Model.md`
- `06_AGENTS/Trust-Tiers.md`
- `06_AGENTS/Handoff-Protocol.md`
- `06_AGENTS/Runtime-Navigation-Map.md`
- `06_AGENTS/Browser-Autonomy-Policy.md`
- `06_AGENTS/Browser-Task-Patterns.md`
- `06_AGENTS/Core-Personal-Split-Implementation-Plan.md`

### 3. SOPs and Templates
Generally Core-safe after review:
- `04_SOPS/`
- `05_TEMPLATES/`

### 4. Runtime Framework Scaffolds
Core-safe only when generic and stripped of personal/private bindings:
- `runtime/Runtime-Layer-Guide.md`
- `runtime/memory/nav/_schema.json`
- `runtime/browser_registry/allowed_origins.yaml` (template-safe version)
- `runtime/browser_registry/task_classes.yaml`
- other generic runtime substrate files that contain no private sources, identities, or credentials

### 5. Template Folder Layer
Everything under `core_templates/` is intended specifically for future Core export.

---

## Core-Excluded Categories

These remain Personal by default unless explicitly rewritten into generic examples:
- `SOUL.md`
- `00_HOME/Now.md`
- `00_HOME/Principles.md`
- `00_HOME/Operating-System.md`
- real files in `01_PROJECTS/`
- real files in `02_KNOWLEDGE/`
- real logs in `07_LOGS/`
- personal or account-specific registry/tool files
- runtime state tied to the live instance
- any secret-bearing or identity-bearing content

---

## Export Rule

A file may enter Core only if it passes all three tests:
1. **Reusable** — another user could meaningfully adopt it
2. **Sanitized** — no private/personal/secret context remains
3. **Navigable** — it still preserves the markdown/index/routing role expected by ChaseOS

---

## Initial Core Export Shape

Planned top-level Core export structure:
- `README.md`
- `PROJECT_FOUNDATION.md`
- `ROADMAP.md`
- `FORKING.md`
- `SOUL.template.md`
- `04_SOPS/`
- `05_TEMPLATES/`
- `06_AGENTS/` (framework-safe subset)
- `runtime/` (framework-safe subset)
- `core_templates/`

---

## Current Verdict

This manifest is still a seed inventory, not a final release list. As of 2026-04-26 it is also a Phase 10 blocker: Studio/gateway work should not assume the mixed personal/core repo is export-safe until this contract becomes machine-checkable.

Its job is to stop the split from becoming ambiguous and to prevent personal runtime state, logs, inputs, identities, or credential-adjacent configuration from leaking into a future public/framework mirror.

Before any Core export or public mirror, create:
- a positive allowlist export manifest with exact file paths and required sanitization steps
- private-only ignore rules for live state, raw inputs, logs, local runtime state, caches, credentials, and generated artifacts
- sanitized templates for setup/runtime/provider/integration state instead of copying populated personal files
- a verification command that fails closed when an included file contains personal-instance signals
- a manual review queue for mixed-layer files such as root docs, agent docs, runtime bindings, and current-state records

Status basis: this is still a populated personal implementation, but Core/Personal separation is now an active structural/export lane rather than conceptual-only. Uncertain or mixed files stay out of Core unless they are allowlisted in `core_export/export_manifest.yaml`, inventoried in `core_export/core_candidate_inventory.yaml`, rendered through scanner-clean preview/template machinery, and exported through the guarded Core export command path. The 2026-05-01 local `chaseos-core` candidate evidence is for inspection; 2026-05-11 revalidation found the local target and manual review artifact missing, so current verify-export is blocked until restored through the guarded export lane. Git/publication/canonical promotion remain separate approval gates.

Refactor record: `07_LOGS/Build-Logs/2026-04-26-ChaseOS-CLI-Consolidation-Codex-GPT5.md`

---

*Graph links: [[FORKING]] · [[06_AGENTS/Vault-Map|Vault-Map]] · [[Core-Personal-Split-Implementation-Plan]]*
