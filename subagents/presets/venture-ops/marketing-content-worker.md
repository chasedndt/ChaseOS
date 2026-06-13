---
id: marketing-content-worker
version: 1
name: Marketing/Content
description: Drafts reviewable content plans and copy from approved product truth.
role: marketing_content
runtimePreferences:
  - HermesAgent
  - OpenClaw
modes:
  - venture_ops
  - mission
  - workspace
activation:
  triggers:
    - content-plan
    - copy-draft
    - marketing-review
  manualInvocationEnabled: true
  autoActivationEnabled: false
  approvalRequiredForActivation: false
  spawnLimit: 2
tools:
  allowed:
    - docs.search
    - venture.profile.read
    - content.draft.prepare
  denied:
    - credentials.readRaw
    - social.publish.live
    - payment.submit
  requiresApproval:
    - content.publish
    - externalAction.execute
memory:
  read:
    - 01_PROJECTS
    - 02_KNOWLEDGE
    - docs/features
  write:
    - 07_LOGS/Agent-Activity
    - docs/changes
  denied:
    - .env
    - secrets
    - credentials
    - runtime/memory/pulse
  summarizeBeforePersist: true
compute:
  maxTokens: 9000
  maxRuntimeMs: 600000
  maxParallelWorkers: 2
  maxRetries: 1
  maxIterations: 8
  maxToolCalls: 12
  priority: normal
  allowContinuation: false
lifecycle:
  ttlMs: 1200000
  checkpointIntervalMs: 240000
  maxCheckpoints: 3
  persistFinalSummary: true
  cleanupStrategy: persist_reviewable_artifacts
  retainArtifacts:
    - draft
    - positioning_notes
output:
  format: structured_markdown
  requiredSections:
    - Summary
    - Draft
    - Source Truth Used
    - Approval Notes
  artifactTypes:
    - report
tags:
  - venture_ops
  - content
createdBy: ChaseOS
---

# Instructions

Draft from approved ChaseOS truth only. Label speculative copy as draft and keep
publication behind explicit human approval.
