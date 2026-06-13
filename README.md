# ChaseOS Core

ChaseOS Core is a public framework for building a local-first human-AI operating system. It defines governed memory, source intelligence, agent boundaries, approval workflows, runtime discipline, and evidence-first writeback.

## What This Repository Contains

- Framework documentation for the ChaseOS control plane.
- Core home/project/knowledge/log folder templates.
- Agent governance docs: Permission Matrix, Trust Tiers, Gate, adapter standards, and runtime boundaries.
- SOPs for research ingest, promotion sessions, credential boundaries, untrusted input, build logs, and agent failure ambiguity.
- Templates for notes, projects, logs, runtime profiles, audits, approval packets, and workflow packs.
- Governance patterns for approval-gated writes.
- Adapter standards for external runtimes.
- Chaser Forge workflow and extension-governance templates.
- Example folders that can be copied into a private deployment.

## What This Repository Does Not Contain

- Personal notes or private project state.
- Live runtime logs or approval queues.
- Credential values.
- Provider-specific deployment state.
- Machine-local paths.

## Intended Use

Use Core as a starter kit and reference model. Private deployments should keep local content, runtime state, and operator records outside the public Core tree.

## OpenCore / Template Surfaces

This repository now includes the compulsory public Core scaffold for a working ChaseOS starter:

- `00_HOME/`, `01_PROJECTS/`, `02_KNOWLEDGE/`, `03_INPUTS/`, `04_SOPS/`, `05_TEMPLATES/`, `06_AGENTS/`, and `07_LOGS/` starter/index surfaces.
- Public-safe agent governance and runtime boundary docs.
- Workflow/governance templates under `templates/`.
- Chaser Forge public workflow templates under `docs/forge/` and `templates/forge/`.

These are governance and template surfaces only. They do not enable live marketplace fetch, network upload, paid checkout, license enforcement, third-party remote install, approval consumption, provider/model calls, browser control, host mutation, or canonical promotion.
