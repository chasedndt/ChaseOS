# Runtime Registry

ChaseOS Core names three portable 24/7 agent harness/runtime lanes:

| Runtime | Role | Status | Notes |
| --- | --- | --- | --- |
| `hermes` / Hermes | Persistent Linux/WSL + Discord operator runtime | seeded | 24/7 harness lane under ChaseOS control-plane governance |
| `openclaw` / OpenClaw | Windows-side operator harness/runtime | seeded | 24/7 harness lane for local machine operations and scheduled operator workflows |
| `chaser_agent` / Chaser Agent | First-party personal agent harness/runtime | seeded | 24/7 harness lane for governed personal-agent and source-card-harness workflows |

## Runtime boundary

Claude Code may appear as a local development helper/adapter in private deployments, but it is not one of the three always-on ChaseOS harnesses unless a private deployment explicitly registers it.

Codex may appear as a development helper/adapter in some repositories, but it is not one of the three always-on ChaseOS harnesses unless a private deployment explicitly registers it.

## Authority boundary

Runtime identity is not authority. Capability manifests and runtime profiles only make routing explicit. Shell, browser, provider calls, approval consumption, protected writes, canonical promotion, and external actions still require separate ChaseOS governance and proof.
