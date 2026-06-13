---
title: Chaser Forge OpenCore Transfer Plan
status: active-core-packaging-plan
created: 2026-06-13
owner: ChaseOS Core
---

# Chaser Forge OpenCore Transfer Plan

## Goal

Move Chaser Forge from private implementation/proof history into a public-safe ChaseOS Core template surface that can be included in an OpenCore download.

## Product decision

Chaser Forge in OpenCore is a **governed extension and workflow-pack template system**. It is not a live paid marketplace, not a remote package installer, and not a code-writing agent with broad repository authority.

## Phase 1 — Included now

This repo now includes the first public-safe transfer slice:

- Graph hub: `docs/forge/chaser_forge_workflows_index.md`
- Proof taxonomy: `docs/forge/chaser_forge_workflow_proofs_index.md`
- Workflow node standard: `docs/standards/chaseos-forge-workflow-node-v1.md`
- Template files:
  - `templates/forge/forge-workflow-node.template.md`
  - `templates/forge/extension-manifest.example.json`
  - `templates/forge/approval-request.template.json`
  - `templates/forge/forge-index.example.json`

## Phase 2 — Next safe additions

Add validation-only tooling and tests:

1. `chaseos forge validate-workflow-node <path>`
2. `chaseos forge validate-extension-manifest <path>`
3. `chaseos forge validate-index <path>`
4. tests that verify the example templates parse and preserve blocked-authority labels

These commands should be local/read-only. They must not install extensions, call networks, consume approvals, mutate registries, dispatch runtimes, or publish indexes.

## Phase 3 — Optional runtime inclusion audit

Only after the docs/templates are stable, decide whether to include selected `runtime/forge/` source in Core. That requires a separate source inclusion audit covering:

- path guards;
- generated state exclusions;
- proof-log exclusions;
- approval packet examples vs real approvals;
- fixture and test data boundaries;
- network and payment blockers;
- public license and dependency posture.

## Phase 4 — Public package/export readiness

Before claiming an OpenCore download contains Forge workflows, verify:

- every included Forge doc has no private local paths;
- example JSON files are valid;
- proof docs are taxonomy/examples only;
- no real approval packets or operator receipts are committed;
- README and manifest accurately state that live marketplace authority is not included;
- Git history/diff contains no secrets or generated run artifacts.

## Hard blockers

Do not include the following in default OpenCore:

- live hosted fetch;
- remote upload;
- hosted registry mutation;
- payment checkout;
- license entitlement enforcement;
- seller accounts;
- creator payout logic;
- untrusted package execution;
- real operator approval packets;
- private proof logs;
- generated fixture extension files as if they were production state.

## Success criteria

The OpenCore/template transfer is ready when a fresh user can read the Forge docs, inspect the workflow-node standard, copy the example templates, and understand how to create a governed extension workflow without receiving any hidden authority to execute remote installs or mutate ChaseOS Core.
