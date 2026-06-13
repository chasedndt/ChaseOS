---
title: Chaser Forge Workflow Proofs Index
status: public-proof-taxonomy
created: 2026-06-13
owner: ChaseOS Core
open_core_template_status: evidence-taxonomy-only
---

# Chaser Forge Workflow Proofs Index

This is the public/Core proof taxonomy for Chaser Forge workflows. It intentionally does **not** copy private proof logs or local operator evidence. It defines what evidence classes a Core/OpenCore implementation should produce when a Forge workflow is validated, reviewed, installed, or rolled back.

## Why proof routing matters

Forge is an extension system. Extension systems are high-risk unless every transition has evidence:

1. what was requested;
2. what manifest was validated;
3. what permissions and paths were declared;
4. what operator decision was recorded;
5. what exact digest was approved;
6. whether an approval was consumed;
7. whether exact-once markers prevented repeat execution;
8. what rollback path exists.

## Evidence classes

| Evidence class | Required for | Public template? | Notes |
|---|---|---:|---|
| Manifest validation report | `forge.manifest.validate` | Yes | Should list extension points, target paths, permissions, and validation errors. |
| Preview report | `forge.extension.preview` | Yes | Should use mock/example data and perform no production writes. |
| Approval request packet | Sandbox/live/rollback/import requests | Yes | Use `templates/forge/approval-request.template.json`. |
| Operator decision handoff | Approval/rejection review | Yes | Must bind exact digest, exact decision, exact statement, reviewer, and timestamp. |
| Exact-once marker | Any approval-consuming executor | Pattern only | Implementations must prove marker reservation before writes. |
| Registry write report | Sandbox/live install | Pattern only | Should record only extension-owned paths and registry changes. |
| Rollback snapshot | Live install / rollback | Pattern only | Should preserve prior state and rollback instructions. |
| Static index checksum | Public catalog/index | Yes | Use `templates/forge/forge-index.example.json` as a starting point. |
| Remote fetch verification | Remote index fetch | No by default | Requires future network approval gate. |
| Payment/license receipt | Paid marketplace | No | Not part of Core template scope. |

## Proof artifacts that should stay private/local

Do not copy these into public Core by default:

- local operator receipts;
- generated fixture vault outputs;
- screenshots of private local state;
- machine-specific paths;
- proof logs containing private runtime names, local branches, or local host state;
- approval packets from a real operator session;
- marketplace upload/fetch receipts for a private deployment.

Convert them into synthetic examples only after sanitizer review.

## Public-safe proof packet shape

A public-safe Forge proof packet should be synthetic, local, and non-authoritative:

```json
{
  "schema": "chaseos.forge-proof.v1",
  "workflow_id": "forge.manifest.validate",
  "extension_id": "example-extension",
  "status": "example-only",
  "inputs_digest_sha256": "<example-digest>",
  "decision_digest_sha256": null,
  "writes_performed": false,
  "approval_consumed": false,
  "blocked_authority": [
    "network_fetch",
    "network_upload",
    "payment",
    "license_enforcement",
    "untrusted_remote_install"
  ]
}
```

## Required no-overclaim labels

Any Forge proof surfaced in OpenCore should explicitly say when it did **not** perform:

- network fetch or upload;
- hosted registry mutation;
- payment/licensing mutation;
- untrusted package execution;
- provider/model calls;
- browser control;
- Agent Bus task writes;
- host mutation;
- canonical promotion.

## Related Core docs

- `docs/forge/chaser_forge_workflows_index.md`
- `docs/forge/chaser_forge_opencore_transfer_plan.md`
- `docs/standards/chaseos-forge-workflow-node-v1.md`
- `templates/forge/forge-workflow-node.template.md`
- `templates/forge/approval-request.template.json`
