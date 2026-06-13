# Runtime-Navigation-Map.md
## ChaseOS — Runtime Navigation Map

> The Runtime Navigation Map is a runtime-specific, evolving overlay map built from operational experience inside ChaseOS. It is not the shared Vault Map. It is not a behavioral profile. It is a living picture of how a specific runtime actually moves through the system — the routes it prefers, the zones it trusts, the failure points it knows, and the places it should escalate.

**Version:** 1.0
**Created:** 2026-03-25
**Updated:** 2026-05-15
**Status:** Partial - architecture defined; seeded runtime profiles exist; Studio exposes redacted Discord binding readiness

---

## 1. What the Runtime Navigation Map Is

The Vault Map (`06_AGENTS/Vault-Map.md`) is the shared, static navigation reference for all operators. It does not change based on who is using the system. It describes where files are, what they do, and how to move between them.

The Runtime Navigation Map is something different:

**A per-runtime, evolving overlay that records how a specific runtime has learned to navigate the ChaseOS vault — built from operational history, not from the system definition.**

It captures the navigational/topological dimension of a runtime's accumulated operating intelligence:
- Which routes it has actually taken through the vault
- Which routes succeeded and which led to failures or errors
- Which zones it navigates confidently and which require caution
- Which doc clusters it reaches for under which conditions
- Which writeback paths have been validated and which are untested
- Where it should escalate to the user vs. act autonomously

This map grows as the runtime operates. It is not written once and frozen — it accumulates as operational evidence builds.

---

## 2. Clear Distinctions — What the RNM Is Not

Five closely related concepts can blur together. Keeping these distinct is architecturally important.

| Concept | What it stores | Type of intelligence |
|---------|---------------|---------------------|
| **Shared Vault Map** | Static folder/file structure; canonical navigation reference for all operators | Structural |
| **Runtime-Specific Memory (Layer C)** | How this runtime tends to behave — patterns, tendencies, task performance, correction history | Behavioral |
| **Agent Identity Ledger** | Who this runtime is — cumulative behavioral identity, reputation, drift signals, across all sessions | Identity |
| **Execution Repair Memory** | How this runtime recovers — confirmed failure patterns and the fixes that worked | Repair |
| **Runtime Navigation Map** | How this runtime moves through the system — preferred routes, trusted zones, hot spots, risky paths, escalation points | Navigational / Topological |

The RNM is the **navigational dimension** of runtime intelligence. It is one component within the broader Layer C (Agent/Runtime-Specific Memory) family — alongside the Agent Identity Ledger and Execution Repair Memory, which are the **identity dimension** and **repair dimension** respectively.

**The RNM answers:** *Where does this runtime go in the vault, how does it get there, and what does it know about those routes?*

**Layer C (behavioral) answers:** *What does this runtime tend to do?*

**Agent Identity Ledger answers:** *Who is this runtime as an actor in the system?*

**Execution Repair Memory answers:** *What went wrong, and how was it fixed?*

**Vault Map answers:** *Where are things and what are they for?* (system-wide, not runtime-specific)

---

## 3. What the Runtime Navigation Map Should Eventually Contain

These are the specific navigational intelligence categories the RNM should accumulate:

### Preferred Read Routes
- Preferred doc read order for this runtime — which files does it naturally sequence through, and in what order, when given a specific task type?
- Most-used doctrine nodes — which Layer A governance docs does this runtime reference most frequently (by session evidence, not prescription)?
- Context loading shortcuts — which narrow context sets reliably orient this runtime to common task types?

### Trusted Zones
- Project operating file zones this runtime navigates confidently and correctly
- Domain knowledge areas where this runtime's outputs have been consistently accurate and well-grounded
- Workspace routes in the SIC that have produced clean, citation-grounded outputs

### Common Successful Routes
- Workspace query sequences that produced clean evidence packets
- Source package loading patterns that worked without errors
- Ingestion-to-promotion paths that completed the full five-stage flow cleanly
- Build session patterns that reliably produced accurate build logs and archive notes

### Safe Writeback Paths
- Writeback targets this runtime has written to successfully and consistently
- Gate-approved write sequences that have completed without policy violations
- Promotion paths that have passed all Gate checks without requiring rollback

### Risk Zones
- Common failure points — which routes, file combinations, or task sequences have triggered errors, wrong outputs, or Gate blocks
- Proven repair paths — the specific alternate routes or workarounds that resolved those failures
- Escalation points — decisions, file types, or ambiguous states where this runtime should halt and surface to the user rather than proceed autonomously

### Runtime-Specific Navigation Traits
- Operational strengths — task types and vault regions where this runtime performs reliably
- Operational weak spots — task types and vault regions where outputs are consistently lower quality or require more user correction
- Graph affinity — which clusters of vault nodes this runtime frequently visits together, and what that says about how it conceptually organizes the system
- Workflow route preferences — when given a task, which file paths does this runtime tend to prefer?

### Policy-Sensitive Zone Map
- Files and directories this runtime should approach with extra caution given its permission ceiling and Trust Tier
- Areas where autonomous action has been blocked and escalation was required
- Boundary zones where Gate enforcement has been consistently triggered

---

## 4. How the Runtime Navigation Map Grows

The RNM is not hand-authored. It accumulates from operational evidence across sessions. The raw material already exists — it is Layer E (Execution History):

**Build logs and session records** → every session is a record of which files were read, which routes were taken, which succeeded, and which required correction.

**Execution Repair Memory** → every confirmed repair pattern is navigational intelligence: this route led to failure; this alternate path resolved it. Repair patterns directly populate the RNM's risk zone and proven repair path categories.

**Agent Activity logs** → autonomous actions produce route traces — which files were accessed, in which order, with what outcomes.

**Doctrine usage patterns** → which Layer A doctrine nodes were actually referenced most during sessions surfaces true load patterns vs. documented routing rules.

**Explicit curator marking** → in future implementations, the runtime (or the user as curator) may explicitly annotate zones as trusted, risky, or preferred based on confirmed operational evidence.

### What Does NOT Update the RNM
- A single success or failure → goes to Layer E first; not promoted to the RNM until a pattern is confirmed
- Unconfirmed patterns → not promoted until validated across multiple sessions
- Speculative routes → not added without operational evidence
- User preferences or domain knowledge → those belong in Layer B and `02_KNOWLEDGE/`, not the RNM

**The RNM is evidence-based, not prescriptive.** It records what has been learned from operation, not what someone thinks should be true.

---

## 5. Governance Rules — RNM Is Subordinate to ChaseOS

The Runtime Navigation Map is accumulated intelligence. It is **not** an authority source. It must never override:

**Layer A (Shared System Doctrine)** — if the Vault Map says a file is protected, the RNM cannot override that classification. Protected files stay protected regardless of a runtime's navigational preferences.

**Permission ceilings (Trust Tiers)** — a runtime's preferred routes cannot expand its Trust Tier or permission scope. If a runtime has navigated toward a protected zone, the RNM records that the zone is off-limits — it does not grant access to it.

**The ChaseOS Gate** — a runtime's "safe writeback paths" are only safe if they comply with Gate rules. The RNM records empirically safe paths, not Gate-exempt paths.

**The shared Vault Map** — the Vault Map is the authoritative structural reference. If the RNM and Vault Map conflict on where something is or what it does, the Vault Map wins. The RNM is an overlay on top of a fixed reference, not an alternative to it.

**The result:** The RNM makes a runtime more **efficient** within its already-defined permission scope. It does not expand what the runtime is allowed to do. It does not become a shadow control plane. It does not accumulate authority. It accumulates navigational intelligence — a different thing entirely.

Any runtime-specific navigation intelligence that would require expanding permissions, modifying protected files, or bypassing Gate rules must go through the standard governance process: user decision, architecture pass, and explicit doctrine update if warranted.

---

## 6. Current State and Canonical Home

**Current state (2026-03-25):** Not yet implemented. The raw material for the Runtime Navigation Map — build logs, session records, agent activity logs — is accumulating in Layer E without being formally organized into per-runtime navigational profiles.

**Current implementation note (2026-05-15):** Hermes, OpenClaw, and Codex runtime profiles are seeded human-readable RNM/profile nodes. Because the current runtime operator surface has mainly used Discord, each active runtime profile should reference the local Discord binding pattern and the Studio `discord_control_plane_panel` when it describes runtime chat, board, schedule, or control-plane navigation. The binding validator remains read-only and no-secret; it does not expand runtime authority.

**Near-term (Phase 9 implementation):**
- `runtime/memory/nav/[adapter-name]/nav-map.json` — structured navigation map per runtime (machine-readable)
- `06_AGENTS/[Adapter]-Runtime-Profile.md` — human-readable runtime profile including navigational preferences alongside Layer C behavioral profile
- Curation protocol: how operational evidence from Layer E is periodically reviewed and classified into the RNM

**Phase 10 (Interface Layer):**
- Navigation map inspector — UI surface showing the user how their active runtimes navigate the system
- Hot/cold node visualization — which vault nodes are frequently visited vs. rarely touched by each runtime
- Route audit surface — trace which routes a runtime has taken and what they produced

---

## 7. Roadmap Placement

The Runtime Navigation Map is a Phase 9 feature (Autonomous Operator Runtime) with Phase 10 UI exposure.

**Why Phase 9:** The AOR is the infrastructure that will use the RNM. When the AOR schedules autonomous workflows, it should consult the RNM before choosing routes, selecting context, and deciding whether to escalate. Without the AOR, the RNM is informational only — read by humans, not by autonomous systems. Phase 9 is when this intelligence becomes operationally useful.

**Why Phase 10 for UI:** Exposing the RNM visually (hot/cold map, route audit, node affinity graph) requires the Interface/Experience Layer that is Phase 10.

**Phase 9 RNM outputs:**
- Runtime Navigation Map schema defined
- Claude/Anthropic lane: first manual RNM population from Layer E history
- Curation protocol established for nav-map accumulation from operational evidence
- AOR reads RNM before workflow route selection (Phase 9 implementation)

**Phase 10 RNM outputs:**
- Navigation map inspector UI
- Hot/cold vault node visualization per runtime
- Route audit trail surface

---

## 8. Relationship to Other ChaseOS Components

| Component | Relationship |
|-----------|-------------|
| **Shared Vault Map** | Source of truth for static vault structure; RNM is a runtime-specific navigational overlay built on top of it — not a replacement |
| **Layer C (Runtime-Specific Memory)** | RNM is the navigational/topological dimension of Layer C; behavioral profile + Agent Identity Ledger + Execution Repair Memory + RNM together form the full Layer C picture |
| **Agent Identity Ledger** | How a runtime navigates is part of its behavioral identity; RNM contributes navigational patterns to the ledger |
| **Execution Repair Memory** | Confirmed repair patterns directly populate the RNM's risk zone and proven repair path entries |
| **Autonomous Operator Runtime** | AOR reads the RNM before autonomous workflow execution — it informs route selection, context pre-loading, risk avoidance, and escalation decisions |
| **ChaseOS Gate** | Gate rules take precedence over all RNM preferences; "safe writeback paths" in the RNM must comply with Gate; Gate blocks update the RNM's risk zone, not its permission model |
| **Handoff Protocol** | Session start/close protocol may eventually include loading the active runtime's RNM as part of context pre-loading |

---

## 9. Why This Matters

A runtime that navigates ChaseOS from scratch every session re-learns the same spatial facts each time:
- Which files to read for this task type
- Which routes work and which lead to errors
- Which zones require caution
- Which writeback paths are proven clean

Without a Runtime Navigation Map, this navigational intelligence evaporates at the end of every session and has to be re-acquired at the start of the next. This is friction that compounds over time.

A runtime with a mature Runtime Navigation Map:
- Reaches the right context faster — preferred read routes are pre-identified from operational evidence
- Avoids routes that have historically caused failures — risk zones are known before the session begins
- Knows where to escalate vs. where to act autonomously — escalation points are documented
- Has an audit trail of where it has been and what those routes produced — inspectable and improvable

This is not about constraining the runtime to only previously-traveled routes. It is about giving the runtime accumulated navigational intelligence so it operates with increasing efficiency and decreasing navigational errors over time — the same way a person who knows a city well navigates faster than one arriving for the first time.

**The long-term effect:** Runtime Navigation Maps, combined with Agent Identity Ledgers and Execution Repair Memory, allow ChaseOS runtimes to get measurably better over time — not just at a task level, but at a systems navigation level. The system accumulates operational knowledge. That knowledge is inspectable. That inspectability makes the system improvable.

---

*Graph links: [[CLAUDE]] · [[Agent-Memory-Architecture]] · [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[OpenClaw-Adapter-Spec]] · [[OpenAI-Adapter-Spec]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Hermes-Adapter-Spec]] · [[Chaser-Agent-Runtime-Profile]] · [[Codex-Runtime-Profile]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[Feature-Register]] · [[Trust-Tiers]] · [[ChaseOS-Gate]] · [[Handoff-Protocol]] · [[ROADMAP]]*

*Runtime-Navigation-Map.md — v1.0 | Created: 2026-03-25 | Architecture expansion pass — Runtime Navigation Map formally encoded as a Phase 9 ChaseOS feature; distinguished from Shared Vault Map, Layer C behavioral memory, Agent Identity Ledger, and Execution Repair Memory*
