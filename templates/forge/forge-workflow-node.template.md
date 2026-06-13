---
workflow_id: forge.example.workflow
title: Forge Example Workflow
status: template
open_core_template_status: included
allowed_inputs:
  - templates/forge/extension-manifest.example.json
allowed_writes: []
blocked_authority:
  - network_fetch
  - network_upload
  - external_registry_mutation
  - payment_or_license_mutation
  - untrusted_remote_install
  - provider_model_call
  - browser_control
  - agent_bus_write
  - host_mutation
  - canonical_promotion
approval_required_before_execution: false
approval_packet_schema: null
proof_artifacts:
  - manifest-validation-report
runtime_paths: []
studio_surfaces:
  - Chaser Forge
obsidian_links:
  - docs/forge/chaser_forge_workflows_index.md
  - docs/standards/chaseos-forge-workflow-node-v1.md
---

# Forge Example Workflow

## Purpose

Describe what this Forge workflow does and why it belongs in a governed extension lifecycle.

## Inputs

List every file/object this workflow may read.

## Writes

List every file/object this workflow may write. If this is a validation or preview workflow, keep this empty and explicitly state that no writes occur.

## Approval boundary

State whether approval is required before execution. If any write is possible, approval must be required and the exact approval packet schema must be named.

## Blocked authority

Keep blocked authority explicit. OpenCore Forge templates must not silently imply network, payment, provider, browser, host, or canonical mutation authority.

## Proof artifacts

Name the proof/evidence this workflow should produce, for example:

- manifest validation report;
- preview report;
- approval request packet;
- decision handoff record;
- exact-once marker;
- rollback snapshot.

## Implementation notes

Add implementation paths only after they are source-safe and reviewed for public Core inclusion.
