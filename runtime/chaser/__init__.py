"""
runtime.chaser

ChaserAgent core package: the ChaseOS-native agent/operator layer.

Status: PARTIAL / PHASE A CORE FOUNDATION / NOT LIVE.

This package establishes ChaserAgent inside ChaseOS Core first per the
architecture decision recorded in:

- 06_AGENTS/ChaserAgent-Architecture.md
- 06_AGENTS/Session-Export-and-Artifacts-Architecture.md
- 06_AGENTS/ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2.md

Governance posture:

- ChaserAgent does not own canonical ChaseOS truth.
- ChaserAgent does not bypass ChaseOS Gate, Permission Matrix, or Trust Tiers.
- ChaserAgent does not execute unrestricted shell commands.
- ChaserAgent does not perform hidden external uploads.
- Session/tool/terminal output is untrusted until separately verified.
- Profiles, toolsets, and memory/bootstrap files are configuration surfaces,
  not authority grants.

Implemented:

- runtime.chaser.models: session/tool/terminal/artifact dataclasses
- runtime.chaser.sessions: local JSON session store and audited metadata lifecycle
- runtime.chaser.exports: governed markdown/json session export backend
- runtime.chaser.chat_session_adapter: Studio chat to SessionRecord export adapter
- runtime.chaser.agent: no-authority preview interface
- runtime.chaser.board: read-only orchestration board/card/proposal/approval-request contracts
- runtime.chaser.terminal_write_executor_readiness: N6 no-execution readiness checks
- runtime.chaser.terminal_write_executor: N6 dedicated approval-gated CLI executor
- runtime.chaser.gateway: N7 internal structured ingress facade over governed routes
- runtime.chaser.terminal_authority_audit: N8 read-only terminal authority proof packet
- runtime.chaser.runtime_readiness: read-only ChaserAgent runtime wiring readiness review
- runtime.chaser.runtime_activation_gate: read-only activation gate design before live wiring
- runtime.chaser.runtime_activation_approval: preview-only activation approval request shape
- runtime.chaser.runtime_activation_approval_request: gated activation approval request writer
- runtime.chaser.runtime_activation_approval_decision_preflight: read-only activation approval decision preflight
- runtime.chaser.runtime_activation_approval_consumption_design: no-mutation activation approval consumption design
- runtime.chaser.runtime_activation_approval_consumption_write_guard: activation approval consumption marker/audit write guard
- runtime.chaser.runtime_activation_post_consumption_readiness: read-only post-consumption readiness
- runtime.chaser.runtime_activation_executor_design: read-only activation executor design
- runtime.chaser.runtime_activation_executor_write_guard: activation marker/state/audit write guard
- runtime.chaser.runtime_activation_state_readiness: read-only activation state readiness
- runtime.chaser.runtime_profile_toolset_activation_design: read-only profile/toolset activation design
- runtime.chaser.runtime_profile_toolset_activation_write_guard: profile/toolset marker/state/audit write guard
- runtime.chaser.runtime_profile_toolset_activation_readiness: read-only profile/toolset activation readiness
- runtime.chaser.policies: fail-closed policy snapshots
- runtime.chaser.profiles: read-only profile views
- runtime.chaser.toolsets: read-only toolset views
- runtime.chaser.memory: memory-boundary previews
- runtime.chaser.artifacts: artifact manifest contracts

Still not implemented:

- live ChaserAgent execution
- Agent Bus claiming or task writes
- provider/model calls
- unrestricted tool/shell execution
- executable terminal toolset binding
- network-served gateway ingress
- companion or Chaser memory writes
- canonical writeback
"""

from __future__ import annotations

__all__ = [
    "agent",
    "artifacts",
    "chat_session_adapter",
    "board",
    "exports",
    "gateway",
    "memory",
    "models",
    "policies",
    "profiles",
    "runtime_activation_approval",
    "runtime_activation_approval_consumption_design",
    "runtime_activation_approval_consumption_write_guard",
    "runtime_activation_approval_decision_preflight",
    "runtime_activation_approval_request",
    "runtime_activation_executor_design",
    "runtime_activation_executor_write_guard",
    "runtime_activation_state_readiness",
    "runtime_profile_toolset_activation_design",
    "runtime_profile_toolset_activation_write_guard",
    "runtime_profile_toolset_activation_readiness",
    "runtime_activation_post_consumption_readiness",
    "runtime_activation_gate",
    "runtime_readiness",
    "sessions",
    "terminal_authority_audit",
    "terminal_write_executor_readiness",
    "terminal_write_executor",
    "toolsets",
]
