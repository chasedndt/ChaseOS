# Chaser Agent Adapter Spec Example

This example defines the portable ChaseOS Core framing for Chaser Agent.

## Identity

- Runtime label: Chaser Agent
- Runtime id: `chaser_agent`
- Bus name: `Chaser Agent`
- Runtime family: 24/7 ChaseOS harness/runtime lane with Hermes and OpenClaw

## Not the same as Archon

Archon is the personal instance name of the operator's Claude Code environment. It is not a public ChaseOS Core runtime, not an always-on harness, and not one of the three 24/7 runtime lanes.

## Permitted Core representation

Core may ship:

- profile examples;
- capability-manifest examples;
- workflow-node templates;
- approval packet templates;
- source-card harness contracts.

Core must not ship:

- live credentials;
- private schedules;
- personal memory;
- host-specific daemon state;
- approval-consumption authority;
- provider/model keys;
- direct canonical write authority.

## Minimum activation gates

A private deployment must prove the following before treating Chaser Agent as live:

1. Runtime adapter exists and is registered.
2. Runtime heartbeat is observable.
3. Approval packet contract is enforced.
4. Output writes are reviewable and scoped.
5. Provider/browser/shell authority is separately bounded.
6. Graph writeback routes to ChaseOS review/promotion rather than direct canonical mutation.
