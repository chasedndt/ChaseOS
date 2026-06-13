---
type: architecture-bridge
knowledge_class: source-derived
status: SOURCE-DERIVED ROUTING BRIDGE / REVIEW REQUIRED
source_file: 03_INPUTS/Personal-Context-Intake/2026-05-16_n-personal-context-node-reaudit-source.md
updated: 2026-05-16
---

# ChaseOS Core

> Routing bridge for the reusable, git-safe framework layer of ChaseOS.

## Source-Derived Context

- `n.md` lists `ChaseOS-Core.md` as a useful subnode under ChaseOS Architecture.
- The operator wants ChaseOS prepared for real-world personal use while also keeping the future git-safe export/template clean.
- Existing repo truth already has Core/Personal split planning and export machinery; this file is a bridge to those canonical surfaces, not a new source of truth.

## Core Role

ChaseOS Core is the reusable framework layer: folder conventions, templates, governance docs, adapter standards, runtime substrate, example notes, setup guidance, and publication-safe scaffolding.

## Core Does Not Include

- Personal identity content.
- Private project facts.
- Personal Map applied memory.
- Credentials, tokens, wallet keys, account identifiers, or private operator context.
- Unreviewed raw intake packets.

## Canonical Surfaces

- [[CORE_MANIFEST]]
- [[06_AGENTS/Core-Personal-Split-Implementation-Plan]]
- [[06_AGENTS/Core-Export-Sync-Procedure]]
- [[06_AGENTS/Core-Export-Git-Safe-Extraction-Development-Plan]]
- [[FORKING]]

## Open Loops

- Revalidate the current core export report before any public GitHub action.
- Keep personal-instance updates from leaking into Core templates.
- Use this node as a routing bridge until a dedicated Core product surface is verified.

## Graph Links

[[06_AGENTS/ChaseOS-Personal]] [[CORE_MANIFEST]] [[06_AGENTS/Core-Personal-Split-Implementation-Plan]] [[06_AGENTS/Core-Export-Sync-Procedure]] [[06_AGENTS/Vault-Map]]
