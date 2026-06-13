---
title: ChaseOS Layer Catalog
type: framework-architecture
version: 1.0
created: 2026-04-06
updated: 2026-04-06
status: active
---

# ChaseOS Layer Catalog

## Overview & Rationale

The ChaseOS Layer Catalog transforms the chronological development structure (Phases 1-10) into a set of normalized, distinct functional boundaries. Rather than defining architecture layers by *when* they were built, this model abstracts them by *what they do* within the context of the system’s data flow—spanning from doctrinal governance and external ingestion, through durable state persistence and grounded reasoning, and finally to bounded autonomy and operator interfaces. 

This provides long-term stability and professional reusability, ensuring components like the Source Intelligence Core (SIC) and Autonomous Operator Runtime (AOR) aren't conflated with temporal project phases.

## Layer Catalog

| Layer_ID | Layer_Name | Purpose | Example_Components | Owner | Primary_Repo_or_Module | Maturity | Notes | Source_of_Truth_Link | Last_Updated |
|---|---|---|---|---|---|---|---|---|---|
| L01 | Governance & Trust | Establishes universal system doctrine, access boundaries, authority ceilings, taxonomies, and cross-system policy enforcement. | ChaseOS Gate (hook scripts), Agent Permission Matrix, Trust Tiers, Knowledge Taxonomy | ChaseOS Core | `06_AGENTS/`, `runtime/policy/` | Stable | Acts as the foundational policy layer; all execution and storage operations must inherit its constraints. | `[[Agent-Control-Plane]]` | 2026-04-06 |
| L02 | Capture & Connectors | Manages external content intake, deduplication, and triage isolation; normalizes inbound artifacts prior to downstream logic. | Grok/Perplexity APIs, RSS Connectors, Dedup Registry, Watch-folder Automations | ChaseOS Core | `runtime/capture/`, `03_INPUTS/00_QUARANTINE/` | Active / Stable | Physical isolation enforcing 'quarantine-first' processing without autonomous advancement. | `[[Connector-Capture-Architecture]]` | 2026-04-06 |
| L03 | Durable Memory & State | Serves as the authoritative multi-hierarchy state store for canonical project data, persistent knowledge, and audit trails. | Project OS Files (01), Domain Indexes (02), Active Sprint (00_HOME/Now.md), Build Logs | Operator | `01_PROJECTS/`, `02_KNOWLEDGE/` | Stable | Contains context targeted for 'narrow routing' vs full context dumps. | `[[PROJECT_FOUNDATION]]` | 2026-04-06 |
| L04 | Source Intelligence Core | Acts as the self-hosted reasoning engine for workspace generation, chunk indexing, query retrieval, and output synthesizing. | Source Packages, Workspace Manager, Local Embedding Backends, Synthesis Engines | ChaseOS Core | `runtime/source_intelligence/` | Active / Stable | Intermediate outputs remain here pre-promotion; does not inherently replace Durable Memory artifacts. | `[[SIC-Architecture]]` | 2026-04-06 |
| L05 | Autonomous Execution | Infrastructure governing autonomous, OS-level execution including scheduled pipelines, action routing, and multi-repo workflows. | Autonomous Operator Runtime (AOR), Scheduled Briefing Pipelines (SBP), Workflow Registry | ChaseOS Core | `runtime/aor/`, `runtime/workflows/` | Emerging | Requires robust Layer 1 (Governance) to ensure bounding of all event-triggered orchestrations. | `[[Autonomous-Operator-Runtime]]` | 2026-04-06 |
| L06 | Interface & Experience | Constitutes the primary operator-facing presentation surfaces for approvals, queue management, and system visualization. | Terminal UI (TUI), Paperclip Orchestration Dashboard, Provenance Inspector | Operator | `runtime/cli/`, Phase 10 GUIs | Future | User-mediated layers allowing humans to securely endorse outputs or workflow interactions. | `ROADMAP.md` | 2026-04-06 |

---
*Graph links: [[Vault-Map]] · [[Agent-Control-Plane]] · [[Connector-Capture-Architecture]] · [[PROJECT_FOUNDATION]] · [[SIC-Architecture]] · [[Autonomous-Operator-Runtime]]*
