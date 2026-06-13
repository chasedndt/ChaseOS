---
type: architecture-bridge
knowledge_class: source-derived
status: SOURCE-DERIVED ROUTING BRIDGE / REVIEW REQUIRED
source_file: 03_INPUTS/Personal-Context-Intake/2026-05-16_n-personal-context-node-reaudit-source.md
updated: 2026-05-16
---

# Source Intelligence Core

> Routing bridge for ChaseOS source intelligence, provenance, ingestion, normalization, and promotion boundaries.

## Source-Derived Context

- `n.md` lists `Source-Intelligence-Core.md` as a useful subnode under ChaseOS Architecture.
- Existing repo truth uses `SIC-Architecture.md` as the canonical architecture note.
- This bridge exists so the source-explicit node name has a graph home without duplicating the canonical SIC architecture.

## Operating Meaning

Source Intelligence Core is the evidence layer that keeps raw inputs, generated outputs, synthesis notes, canonical knowledge, and memory surfaces separated by provenance and trust posture.

## Canonical Surfaces

- [[06_AGENTS/SIC-Architecture]]
- [[06_AGENTS/Ingestion-Architecture]]
- [[04_SOPS/Research-Ingest-SOP]]
- [[04_SOPS/Untrusted-Input-Handling-SOP]]
- [[02_KNOWLEDGE/AI-Agents/Source-Intelligence]]

## Boundaries

- Raw imported context is not automatically canonical.
- Generated summaries stay distinct from source evidence.
- Promotion into knowledge, project truth, or Personal Map memory requires review.
- Provider adapters do not own source truth.

## Open Loops

- Keep this bridge aligned with `SIC-Architecture.md`.
- Link future context-import features back to source trust labels and promotion rules.
- Avoid treating AI summaries as direct memories without evidence.

## Graph Links

[[06_AGENTS/SIC-Architecture]] [[06_AGENTS/Ingestion-Architecture]] [[04_SOPS/Research-Ingest-SOP]] [[02_KNOWLEDGE/AI-Agents/Source-Intelligence]] [[03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index]]
