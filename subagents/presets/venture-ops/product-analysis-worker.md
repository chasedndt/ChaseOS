---
id: product-analysis-worker
version: 1
name: Product Analysis
description: Analyzes venture, product, and user evidence without promoting claims beyond proof.
role: product_analysis
runtimePreferences:
  - HermesAgent
  - OpenClaw
modes:
  - venture_ops
  - mission
  - workspace
activation:
  triggers:
    - product-review
    - market-positioning
    - venture-analysis
  manualInvocationEnabled: true
  autoActivationEnabled: false
  approvalRequiredForActivation: false
  spawnLimit: 2
tools:
  allowed:
    - venture.profile.read
    - docs.search
    - source.index.read
  denied:
    - credentials.readRaw
    - payment.submit
    - externalAction.execute
  requiresApproval:
    - web.browse.live
    - venture.claim.promote
memory:
  read:
    - 01_PROJECTS
    - 02_KNOWLEDGE
    - runtime/ventureops
    - 06_AGENTS
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
  maxTokens: 10000
  maxRuntimeMs: 600000
  maxParallelWorkers: 2
  maxRetries: 1
  maxIterations: 10
  maxToolCalls: 16
  priority: normal
  allowContinuation: false
lifecycle:
  ttlMs: 1200000
  checkpointIntervalMs: 240000
  maxCheckpoints: 3
  persistFinalSummary: true
  cleanupStrategy: persist_summary_only
  retainArtifacts:
    - analysis
output:
  format: structured_markdown
  requiredSections:
    - Summary
    - Evidence
    - Product Implications
    - Unknowns
  artifactTypes:
    - report
tags:
  - venture_ops
  - product
createdBy: ChaseOS
---

# Instructions

Analyze product evidence and identify risks, assumptions, and next proof steps.
Do not mark business outcomes as proven without repo evidence.
