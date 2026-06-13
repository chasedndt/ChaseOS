---
type: framework-control
title: Execution Adapter Standard — ChaseOS Phase 5
version: 1.0
created: 2026-03-20
scope: framework-level
---

# Execution Adapter Standard

> Defines what an execution adapter is in ChaseOS, how it relates to provider, surface, and permission scope, and what every adapter document must contain.
> This is the conformance standard for all Phase 5 runtime binding documents.
> See `[[Agent-Control-Plane]]` for the governance architecture.
> See `[[Backends-Supported]]` for the provider/surface access matrix.
> See `[[Permission-Matrix]]` for the canonical permission rules.
> See `[[Agent-Security-Model]]` for the security architecture all adapters inherit.

---

## 1. What Is an Execution Adapter

An **execution adapter** is the binding layer between an execution surface and the ChaseOS vault + control plane.

It is not the model. It is not the provider. It is the configured, documented, and permission-scoped connection that allows a specific runtime to operate against ChaseOS in a defined way.

```
Provider / Backend    →  who makes the underlying model (Anthropic, OpenAI, Mistral, etc.)
Execution Surface     →  the class of interface (chat UI, agent harness, workflow runtime, research platform)
Execution Adapter     →  the specific configured binding of a surface to ChaseOS (the routing doc + config + permission grant)
Granted Permission    →  what the vault owner explicitly authorizes this adapter to do
```

**Example:** `CLAUDE.md` is the execution adapter for the Anthropic Agent Harness surface. It tells Claude Code how to navigate ChaseOS, what to read first, what it may and may not write, and how to behave at session close. The provider is Anthropic. The surface is the agent harness. The adapter is CLAUDE.md + associated permission settings.

**A surface without an adapter document is not authorized to operate against ChaseOS.** Trust assignment in `Agent-Registry.md` is necessary but not sufficient — the adapter document makes the binding operational.

---

## 2. Adapter Classes

Adapters inherit the trust ceiling defined in `[[Trust-Tiers]]` for their surface class:

| Surface Class | Adapter Class | Trust Ceiling | Vault Access |
|--------------|--------------|--------------|-------------|
| Agent Harness | **Harness Adapter** | Tier 2 — conditional on named contract + owner grant | Direct vault read/write |
| Workflow Runtime | **Runtime Adapter** | Tier 2 — conditional on scope definition + owner grant | Workflow-scoped only |
| Chat UI / Advisory | **Advisory Adapter** | Tier 3 | None — user-mediated import only |
| Research Platform | **Research Adapter** | Tier 3 | None — upload or external only |

Advisory and Research adapters do not write to the vault. They are documented for completeness and to define their output handling and trust assignment.

---

## 3. Required Sections for Every Adapter Document

Every execution adapter document — regardless of provider or surface class — must contain the following sections:

### 3.1 Identity
- Provider / backend
- Execution surface (class and specific name)
- Adapter document location
- Current status: `active` | `planned` | `future`
- Trust tier assigned
- Registry entry: link to the relevant entry in `[[Agent-Registry]]`

### 3.2 Access Mode
- Is this adapter advisory-only or vault-capable?
- Read path: how the adapter accesses vault content (direct filesystem, MCP, user-paste, upload)
- Write path: how the adapter writes to the vault (direct, MCP, none, user-mediated)
- User-mediated import required: yes / no / partial

### 3.3 Required Read Order
What files this adapter must read at the start of any substantive session. The minimum for any vault-capable harness adapter:
```
1. 00_HOME/Now.md               ← current sprint focus
2. 01_PROJECTS/[Relevant]-OS.md ← project in scope
3. [supporting files as needed]
```
Advisory adapters define what context the user should provide at session start.

### 3.4 Writeback Requirements
What the adapter must write before a session closes:
- Build log: `07_LOGS/Build-Logs/YYYY-MM-DD-[Project]-[descriptor].md`
- Project-OS update if state changed
- Archive note if the session was a major pass
- Index updates if new logs or archive notes were created

Advisory adapters: outputs go to `03_INPUTS/` via user import, not direct writeback.

### 3.5 Logging Behavior
- Does this adapter write build logs directly (harness adapter) or produce outputs for user import (advisory adapter)?
- Where does session activity go?
- What triggers a log entry vs what is incidental?

### 3.6 Approval Behavior
- What actions require explicit user approval in this adapter's surface context?
- How does the adapter request approval? (inline text, tool call confirmation, etc.)
- Approval scope: always the specific action + specific target + current session — does not generalize

At minimum, every adapter must enforce:
- Protected-file edits require per-file explicit approval
- Deletions require per-file explicit instruction
- External writes require session-scoped approval
- Full list: `[[Permission-Matrix]]` and `[[Agent-Security-Model]]` Section 11

### 3.7 Failure and Escalation Behavior
- What does this adapter do when scope is ambiguous?
- What does it do when a vault file contradicts the user's stated task?
- What does it do when a required context file is missing?
- Default: flag and ask — never guess and act
- Full SOP: `[[04_SOPS/Agent-Failure-Ambiguity-SOP|Agent-Failure-Ambiguity-SOP]]`

### 3.8 Memory Rules
Any state this adapter maintains outside the vault must be documented here.

**Hard rule:** The vault is the authoritative state store. Adapter memory (e.g., `~/.claude/memory/`, model-level context, workflow state) is secondary. If adapter memory conflicts with vault content, vault wins. Stale memory must be updated or discarded — it must not override vault truth.

For each out-of-vault memory location:
- Where it lives
- What it contains
- How stale it may become before it must be refreshed from vault
- What it may not contain (credentials, protected-file drafts, unverified external content)

### 3.9 Hook and Subagent Rules
If this adapter supports hooks (session-open, session-close, tool-call events) or subagent delegation:
- What hook types are configured
- What the hook is permitted to do (read, write, external call)
- Subagent trust: a subagent does not inherit its parent adapter's full permission scope by default — scope must be explicitly passed
- Subagent outputs must be treated as Tier 3 inputs unless explicitly elevated by the user

### 3.10 Credential Handling
- Reference to `[[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]`
- Any adapter-specific credential notes (where this adapter's API key lives, what environment variables it uses)
- Hard rule: no credential values in the adapter document itself

### 3.11 Security Inheritance
All adapters inherit the Phase 4 security plane:
- Untrusted content is Tier 4 — handled per `[[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]]`
- Prompt injection defense is always active — flag before acting
- Least privilege applies — the adapter does not request broader access than its defined scope
- Fail-closed: when in doubt, escalate
- Full model: `[[Agent-Security-Model]]`

---

## 4. Adapter Status Lifecycle

```
proposed → documented → reviewed → registered → active → deprecated
```

| Stage | Meaning |
|-------|---------|
| proposed | Adapter is under consideration; no doc yet |
| documented | Adapter document exists; not yet reviewed for compliance |
| reviewed | Adapter document reviewed against this standard; conformance confirmed |
| registered | Entry in `Agent-Registry.md` with trust tier and permission scope |
| active | Adapter is operating against ChaseOS under its defined binding |
| deprecated | Adapter is no longer in use; document archived |

An adapter must reach **registered** status before it is authorized to operate against the vault.

### 4.1 Evaluation Dimensions

Before an adapter advances from **documented** to **reviewed**, the following must be assessed:

| Dimension | Assessment Question |
|-----------|---------------------|
| Adapter doc completeness | Are all 11 required sections present and non-trivial? |
| Permission scope boundedness | Is the access scope explicitly limited — no open-ended or ambient vault access? |
| Untrusted input handling | Is Section 3.11 documented and specific to this surface's injection risk profile? |
| Credential handling | Does Section 3.10 explicitly state where credentials live and confirm none appear in the doc? |
| Approval behavior | Are triggers for protected-file edits, deletions, and external writes explicitly defined? |
| Failure behavior | Is the escalation path defined — fail-closed behavior confirmed? |
| Writeback reliability | Does the adapter produce audit-traceable writeback outputs? |

These assessments do not require formal test suites. They require documented operator judgement — recorded in the adapter doc or as a note during the review.

### 4.2 Additional Evaluation for Security-Sensitive Workflows

If an adapter is designated for use in security research workflows (see `[[Security-Research-Workflow-Layer]]`), or any task class where factual accuracy and containment are critical, the following additional dimensions must be assessed before it reaches **registered** status:

| Dimension | Assessment Question |
|-----------|---------------------|
| Hallucination tendency | Does this surface tend to fabricate technical claims, CVE numbers, or vulnerability details? |
| Retrieval-groundedness | When context is provided, does the surface stay evidence-based or confabulate beyond sources? |
| Security code output behavior | Does the surface require approval before producing working exploit code for real targets? |
| Prompt injection resistance | Has this surface been tested against embedded instruction injection in input content? |
| Task class restrictions | Are high-risk task classes (auto-promotion, external writes, doctrine updates) explicitly forbidden in the manifest? |

These assessments must be recorded in the adapter doc's Section 3.11 or as a `security_notes` field in the adapter manifest.

**Rule:** No adapter used for security research workflows may remain in `documented` status during active use. It must reach at minimum `reviewed` before being used for any security research task.

---

## 5. Conformance of CLAUDE.md

`CLAUDE.md` was created before this standard was formalized. It is the adapter document for the Anthropic Agent Harness and predates Phase 5. It conforms to this standard in substance, though its section structure predates the standard's headings.

Conformance mapping:
- Identity → "What ChaseOS Is" + header metadata
- Access Mode → "Current Implementation Reality"
- Required Read Order → "Default Startup Read Order"
- Writeback Requirements → "Writeback Requirements"
- Logging Behavior → "Writeback Requirements" + audit notes
- Approval Behavior → "Protected Files" + implied by Permission-Matrix
- Failure/Escalation → "Failure and Ambiguity Behavior"
- Memory Rules → audit notes section (memory system)
- Credential Handling → not explicitly present; governed by Credential-Boundaries-SOP
- Security Inheritance → "Handling External and Untrusted Input"

CLAUDE.md does not need to be restructured to match this standard's heading format. It is the reference implementation; future adapter docs follow this standard's explicit section structure.

---

## 6. Registered Adapter Documents

| Adapter Doc | Surface | Provider | Status |
|------------|---------|----------|--------|
| `CLAUDE.md` | Anthropic Agent Harness | Anthropic | Active |
| `OPENAI.md` | OpenAI Chat Surface / Codex / OpenAI Agent Harness | OpenAI | Documented — harness planned |
| `LOCAL-OSS.md` | Local/Open-Source Harness (Claude Code+Ollama, Cline, OpenHands) | Various | Documented — planned |
| `N8N.md` | n8n Workflow Runtime | n8n | Documented — planned |

Advisory and research surfaces (NotebookLM, Perplexity, Grok) do not require adapter documents — their output handling is defined in `Agent-Registry.md` and their trust model is defined in `Trust-Tiers.md`. If a full adapter doc is created for one of these, it follows this standard's structure.

---

## 7. What an Adapter Document Is Not

- Not a trust assignment — trust is assigned in `Agent-Registry.md` by the vault owner
- Not a permission grant — permissions are defined in `Permission-Matrix.md`
- Not a security policy — security is governed by `Agent-Security-Model.md`
- Not a user interface — it is a runtime configuration and routing anchor, not what the user interacts with directly
- Not a contract — the binding contract for agent behavior is `Assistant-Contract.md`; adapter docs are routing and config, not authority grants

---

*Graph links: [[Vault-Map]] · [[Agent-Control-Plane]] · [[Agent-Registry]] · [[Backends-Supported]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Agent-Security-Model]] · [[Assistant-Contract]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]] · [[04_SOPS/Agent-Failure-Ambiguity-SOP|Agent-Failure-Ambiguity-SOP]] · [[CLAUDE]] · [[ROADMAP]]*

*Execution-Adapter-Standard.md — Version 1.1 | Created: 2026-03-20 | Updated: 2026-04-08 (Sections 4.1 Evaluation Dimensions + 4.2 Security-Sensitive Workflow Adapters added) | Phase 5 — Repo / Runtime Binding*
