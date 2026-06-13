---
title: Multi-Repo / Multi-Directory Access Policy
type: feature-family-node
status: DEFERRED / POLICY DEFINED / RUNTIME ENFORCEMENT NOT BROADLY ACTIVE
created: 2026-05-21
updated: 2026-05-21
canonical_parent: [[Autonomous-Operator-Runtime]]
---

# Multi-Repo / Multi-Directory Access Policy

This node gives the Multi-Repo / Multi-Directory Access Policy its own wiki-addressable feature-family page.

The canonical architecture remains under [[Autonomous-Operator-Runtime]], because multi-repo access is an AOR permission and manifest concern. This node exists to keep feature-family navigation, Studio mapping, and future UI work from losing the policy as a section-only feature.

## What It Is

The Multi-Repo / Multi-Directory Access Policy controls whether a ChaseOS runtime, workflow, or agent can read or write outside the primary vault/repo.

Core policy:

- primary repo access is default;
- additional directories must be explicitly declared;
- cross-repo edits require explicit enablement and operator approval;
- external network access is a separate permission dimension;
- every run must preserve repo scope in manifest/audit evidence.

## Current Status

DEFERRED / POLICY DEFINED / RUNTIME ENFORCEMENT NOT BROADLY ACTIVE.

The schema and doctrine are defined, but there is no broad multi-repo product surface or ambient cross-repo authority.

## Studio Mapping

This policy should not become a first-class default Studio page. It belongs under:

- Runtime -> Advanced, when runtime manifest scope is visible;
- Governance -> Settings, when repo scopes/configuration are inspected;
- Governance -> Logs / Audit, when a run proves cross-repo scope.

## Boundaries

This node does not authorize:

- ambient filesystem traversal;
- broad personal-file reads;
- cross-repo edits;
- network access;
- host mutation;
- Git mutation;
- canonical writeback outside declared ChaseOS paths.

## Graph Links

[[Autonomous-Operator-Runtime]] [[Permission-Matrix]] [[Agent-Control-Plane]] [[Feature-Register]] [[Feature-Fit-Register]]
