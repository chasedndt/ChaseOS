---
title: ChaseOS Workflow Pack Manifest v1
created: 2026-05-31
status: DRAFT / EARLY STANDARD / SUBJECT TO CHANGE
schema_name: chaseos.pack.json
type: standard-spec
---

# ChaseOS Workflow Pack Manifest v1

Schema name: `chaseos.pack.json`

Defines pack identity, creator, license class, required capabilities, requested/blocked authority, inputs, outputs, approval requirements, runtime requirements, graph nodes, and telemetry classes.

## V1 posture

This is a documentation-level draft created for the `chaseos.ai` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runtime, external fetch, external send, or live execution authority.

## Minimum fields to define next

- `schema`
- stable identifier
- version
- owner/creator/runtime where applicable
- data/authority scope
- provenance/audit fields
- safety/status labels
- digest/signature fields where needed
