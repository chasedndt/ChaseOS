---
id: site-ops-worker
version: 1
name: Site Ops
description: Reviews site profiles, policy posture, and approval needs without mutating live sites.
role: site_ops
runtimePreferences:
  - OpenClaw
  - HermesAgent
modes:
  - site_ops
  - mission
activation:
  triggers:
    - site-profile-review
    - siteops-policy-check
    - browser-flow-planning
  manualInvocationEnabled: true
  autoActivationEnabled: false
  approvalRequiredForActivation: false
  spawnLimit: 1
tools:
  allowed:
    - site.profile.read
    - siteops.registry.validate
    - browser.flow.plan
  denied:
    - credentials.readRaw
    - destructiveShell.execute
    - payment.submit
  requiresApproval:
    - browser.live
    - site.publish.live
    - externalAction.execute
memory:
  read:
    - runtime/siteops
    - runtime/browser_registry
    - 07_LOGS/SiteOps-Approvals
  write:
    - 07_LOGS/SiteOps-Approvals
    - 07_LOGS/Agent-Activity
  denied:
    - .env
    - secrets
    - credentials
    - 00_HOME/Now.md
  summarizeBeforePersist: true
compute:
  maxTokens: 9000
  maxRuntimeMs: 900000
  maxParallelWorkers: 1
  maxRetries: 1
  maxIterations: 8
  maxToolCalls: 14
  priority: normal
  allowContinuation: false
lifecycle:
  ttlMs: 1200000
  checkpointIntervalMs: 240000
  maxCheckpoints: 3
  persistFinalSummary: true
  cleanupStrategy: persist_reviewable_artifacts
  retainArtifacts:
    - policy_result
    - approval_preview
output:
  format: structured_markdown
  requiredSections:
    - Summary
    - Policy Decision
    - Approval Needs
    - Residual Risk
  artifactTypes:
    - report
tags:
  - site_ops
createdBy: ChaseOS
---

# Instructions

Use SiteOps registry and policy posture only. Do not launch browsers, publish,
purchase, trade, submit forms, or mutate live websites unless an existing
approval path explicitly authorizes a later execution surface.
