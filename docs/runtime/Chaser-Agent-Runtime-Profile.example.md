# Chaser Agent Runtime Profile Example

Chaser Agent is the first-party ChaseOS 24/7 personal agent harness/runtime lane.

## Runtime family

The ChaseOS always-on runtime family is:

- Hermes — persistent Discord/Linux/WSL operator runtime lane.
- OpenClaw — Windows-side 24/7 operator harness/runtime lane.
- Chaser Agent — first-party personal agent harness/runtime lane for governed ChaseOS workflows and source-card harness work.

Archon is not part of this always-on runtime family. Archon is the personal instance name of the operator's Claude Code environment and should not be represented in portable ChaseOS Core as a public runtime/harness lane.

## Authority boundary

Chaser Agent identity does not grant authority by itself. Any live provider call, browser action, shell command, approval consumption, protected write, or canonical promotion still requires the relevant ChaseOS governance contract, approval packet, runtime adapter, and proof record.

## Core transfer notes

OpenCore templates may include this profile as a starter node so private deployments can route Chaser Agent work through the same graph system as Hermes and OpenClaw while keeping credentials, schedules, live queues, and personal memory outside the public repository.

## Related nodes

- `docs/runtime/Hermes-Runtime-Profile.example.md`
- `docs/runtime/OpenClaw-Runtime-Profile.example.md`
- `runtime/chaser_agent/capabilities.yaml`
- `docs/forge/chaser_forge_workflows_index.md`
