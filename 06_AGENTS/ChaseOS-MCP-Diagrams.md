---
title: ChaseOS MCP Diagrams - V1 plus Active V2 Invocation Flow
type: architecture-doc
status: frozen - v1.2 2026-04-21; V1 diagrams preserved; active V2 workflow invocation flow implemented
created: 2026-04-19
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Diagrams

> Architecture diagrams for the ChaseOS Runtime MCP V1 plus the Pass 6B active V2 `workflow.invoke_bounded` surface.
>
> All diagrams are architecture-faithful. V1 diagrams reflect the live V1 design. The invocation diagram reflects the active V2 implementation shape.
> Planned, deferred, and excluded surfaces are explicitly labeled where relevant.
>
> Diagrams are written in Mermaid syntax. They render in Obsidian with the Mermaid plugin enabled.

---

## Diagram 1 — V1 System Context

**What this shows:** Where the ChaseOS MCP V1 server sits relative to runtime adapters, the vault, and the existing control plane. Honest about what V1 calls and what it explicitly does not call.

```mermaid
flowchart TB
    subgraph Runtimes["Runtime Adapters (MCP Clients)"]
        OC[OpenClaw]
        CC[Claude Code]
        N8N[n8n]
        FUT[Future Adapters]
    end

    subgraph MCP["ChaseOS MCP Server — runtime/mcp/ — V1 BUILT"]
        MCPS[MCP Server\nstdio transport]
        PE[Permission\nEnforcer]
        RH[Resource\nHandlers]
        TH[Tool\nHandlers]
        AL[Audit\nLogger]
    end

    subgraph VaultReads["Vault — Curated Read Surfaces Only"]
        NOW["Now.md\n(sprint focus, active domains)"]
        WRG["Workflow Registry\n(IDs, statuses)"]
        RC["role-cards/\n(boundaries, write scope)"]
        OBR["Operator Briefs\n(latest summary)"]
        DL["Decision Ledger\n(index, last N entries)"]
        AA["Agent Activity\n(recent AOR events)"]
    end

    subgraph CP["Control Plane - Referenced; AOR Called Only by Active V2"]
        PM[Permission Matrix]
        TT[Trust Tiers]
        GATE[ChaseOS Gate]
        AOR[AOR Engine]
    end

    PS[("Proposal Staging Area\nNOT canonical vault")]
    APPROVALLOG["07_LOGS/Operator-Briefs/\nApproval Request Artifacts"]
    AUDITLOG["07_LOGS/Agent-Activity/\nAudit Records"]

    OC -->|"stdio MCP"| MCPS
    CC -->|"stdio MCP"| MCPS
    N8N -->|"stdio MCP"| MCPS
    FUT -->|"stdio MCP"| MCPS

    MCPS --> PE
    PE --> RH
    PE --> TH

    RH -->|"curated reads"| NOW
    RH -->|"curated reads"| WRG
    RH -->|"curated reads"| RC
    RH -->|"curated reads"| OBR
    RH -->|"curated reads"| DL
    RH -->|"curated reads"| AA

    TH -->|"staged artifacts only"| PS
    TH -->|"approval request artifacts"| APPROVALLOG

    MCPS --> AL
    AL --> AUDITLOG

    PE -. "references for enforcement" .-> PM
    PE -. "references for enforcement" .-> TT

    MCPS -. "DOES NOT CALL" .-> GATE
    MCPS -. "V1 DOES NOT CALL" .-> AOR
```

**Key reads:**
- Runtime adapters connect via stdio. The MCP transport is local-first.
- The permission enforcer references the Permission Matrix and Trust Tiers but does not call them at runtime — it applies the rules that were encoded from those documents during implementation.
- The V1 MCP server explicitly does NOT call the ChaseOS Gate or AOR Engine. These are separate surfaces with separate authorities.
- The active V2 invocation flow in Diagram 5 is the only designed exception, and it routes to AOR only through `workflow.invoke_bounded`.
- Tool handlers write only to the proposal staging area and approval request artifact path. The audit logger writes audit records. No MCP path writes canonical vault state.

---

## Diagram 2 — Authority Ladder

**What this shows:** The authority tiers of the V1 design — from lowest to highest — with clear marking of what is V1-active, deferred, and excluded.

```mermaid
flowchart BT
    subgraph EX["EXCLUDED — Permanent"]
        E1["writeback.commit_canonical\nVery High Authority"]
        E2["bridge.shell / bridge.git\n/ bridge.browser / bridge.network\nVery High Authority"]
    end

    subgraph DEF["ACTIVE V2 / DEFERRED — Not V1"]
        D1["draft_execution mode\nworkflow.invoke_bounded\nActive V2\nHigh Authority"]
        D2["schedule surfaces\nschedule.intent.read\nschedule.proposal.submit\nHigh Authority"]
        D3["source.workspace.lookup\nHigh Authority"]
    end

    subgraph V1["V1 ACTIVE"]
        subgraph PROP["read_plus_proposal mode"]
            P1["proposal.submit\nproposal.validate\nproposal.diff_preview\napproval_request.create\nMedium Authority"]
        end
        subgraph READ["read_only mode"]
            R1["9 curated resources\nchaseos.current_truth\nworkflows.registry\nruntime.handoff.current\n...\nMedium / Low Authority"]
        end
    end

    R1 --> P1
    P1 -. "deferred ←\nnot V1" .-> D1
    D1 -. "excluded ←\npermanent" .-> E1

    style EX fill:#ffcccc,stroke:#cc0000
    style DEF fill:#fff3cc,stroke:#cc8800
    style V1 fill:#ccffcc,stroke:#007700
```

**Key reads:**
- V1 ceiling is `read_plus_proposal`. No execution authority. No canonical write authority.
- `workflow.invoke_bounded` is active V2 only and remains unavailable in V1 modes.
- The remaining deferred tier is named and bounded — it is not "things we haven't gotten to yet," it is "things we've consciously parted from V1 with specific reasons."
- The excluded tier is permanent. Moving anything from excluded requires a Decision Ledger entry.

---

## Diagram 3 — Proposal Flow Sequence

**What this shows:** The complete lifecycle of a vault write proposal through the MCP surface. Emphasizes where human review occurs and that the MCP server has no role after approval request creation.

```mermaid
sequenceDiagram
    actor Human as Human Operator
    participant RT as Runtime Adapter
    participant MCP as ChaseOS MCP Server
    participant PS as Proposal Staging Area
    participant LOG as 07_LOGS/Operator-Briefs/

    RT->>MCP: proposal.submit(target_file, change_type, proposed_content, rationale)
    MCP->>MCP: Preliminary flagging (protected file flag, permission ceiling)
    MCP->>PS: Write staged proposal artifact
    MCP-->>RT: {proposal_id, status: "staged", preliminary_validation}

    RT->>MCP: proposal.validate(proposal_id)
    MCP->>MCP: Full governance check (permission ceiling, writeback scope, schema)
    MCP-->>RT: {is_valid, errors, warnings, governance_checks}

    RT->>MCP: proposal.diff_preview(proposal_id)
    MCP->>MCP: Read current vault file, compute unified diff
    MCP-->>RT: {diff_content, lines_added, lines_removed, sha256s}

    RT->>MCP: approval_request.create(proposal_id, urgency, human_context)
    MCP->>LOG: Write human-readable approval request artifact
    MCP-->>RT: {approval_request_id, status: "pending_human_review", delivered_to}

    Note over MCP: MCP server's role ends here.<br/>No approve/apply tool exists in V1.

    Human->>LOG: Reviews approval request artifact
    Human->>Human: Decides to approve or reject
    Note over Human: Approval is a human action.<br/>It does not go through MCP.
    Human-->>Human: Applies proposal via direct vault edit<br/>or future approved_write surface (not V1)
```

**Key reads:**
- The sequence shows 4 MCP calls. That is the full proposal surface.
- After `approval_request.create`, the MCP server has no further role. It waits for the next request.
- Human approval is not an MCP tool call. It is a human action, not an automated step.
- "Apply" does not exist in V1. The sequence shows it as a future surface, not an immediate next step.

---

## Diagram 4 — V1 Surface Map Overview

**What this shows:** All 25 named surfaces in a single view, grouped by V1 status. Intended as a quick-reference reference card and for portfolio/credibility use.

```mermaid
flowchart LR
    subgraph V1R["V1 Resources (9)"]
        R1["runtime.identity"]
        R2["runtime.capabilities"]
        R3["chaseos.current_truth"]
        R4["workflows.registry"]
        R5["workflows.role_boundaries"]
        R6["runtime.permission_envelope"]
        R7["runtime.handoff.current"]
        R8["runtime.audit.recent"]
        R9["operator.briefing.latest"]
    end

    subgraph V1T["V1 Tools (4)"]
        T1["proposal.submit"]
        T2["proposal.validate"]
        T3["proposal.diff_preview"]
        T4["approval_request.create"]
    end

    subgraph V1P["V1 Prompts (1)"]
        P1["handoff.runtime_draft_frame"]
    end

    subgraph PLAN["Active V2 (1)"]
        D1["workflow.invoke_bounded"]
    end

    subgraph DEF["Deferred (5)"]
        D2["schedule.intent.read"]
        D3["schedule.proposal.submit"]
        D4["source.workspace.lookup"]
        D5["operator.briefing.synthesis_frame"]
        D6["proposal.drafting_frame"]
    end

    subgraph EXC["Excluded (5)"]
        E1["writeback.commit_canonical"]
        E2["bridge.shell"]
        E3["bridge.git"]
        E4["bridge.browser"]
        E5["bridge.network"]
    end

    style V1R fill:#e6ffe6,stroke:#339933
    style V1T fill:#e6ffe6,stroke:#339933
    style V1P fill:#e6ffe6,stroke:#339933
    style PLAN fill:#fff1cc,stroke:#cc8800
    style DEF fill:#fff9e6,stroke:#cc9900
    style EXC fill:#ffe6e6,stroke:#cc3333
```

**Surface counts:** 14 V1 active | 1 active V2 | 5 deferred | 5 excluded | 25 total named

---

## Diagram 5 - Active V2 Workflow Invocation Flow

**What this shows:** The active `workflow.invoke_bounded` flow implemented in Pass 6B. It is not active in V1 modes. The flow is AOR-routed, allowlist-bound, and draft-safe/log-safe only.

```mermaid
sequenceDiagram
    actor RT as Runtime Adapter
    participant MCP as ChaseOS MCP Server
    participant SAFE as MCP Safety/Preflight
    participant AOR as AOR Engine
    participant OBR as 07_LOGS/Operator-Briefs/
    participant AORAUD as AOR Audit
    participant MCPAUD as MCP Audit Logger

    RT->>MCP: workflow.invoke_bounded(workflow_id, inputs, dry_run)
    MCP->>SAFE: Resolve runtime + draft_execution envelope
    SAFE->>SAFE: Check exact allowlist<br/>operator_today / operator_close_day only
    SAFE->>SAFE: Verify manifest, active status,<br/>role card, permission ceiling,<br/>input keys, writeback scope

    alt Preflight denied
        SAFE-->>MCP: domain_error
        MCP->>MCPAUD: Write denied-request MCP audit
        MCP-->>RT: error response
    else Preflight passed
        MCP->>AOR: run_workflow(workflow_id, inputs, dry_run)
        AOR->>AOR: Manifest + task type + role card + ceiling checks
        AOR->>OBR: Stage 7 writeback<br/>Operator-Briefs only
        AOR->>AORAUD: Stage 8 AOR audit
        AOR-->>MCP: AORRunResult(status, audit_id, outputs)
        MCP->>MCPAUD: Write MCP invocation audit<br/>with AOR audit reference
        MCP-->>RT: Bounded status + artifact paths only
    end

    Note over MCP,AOR: MCP never calls workflow handlers directly.<br/>No shell, git, browser, network, schedule coupling, apply, or commit path exists.
```

**Key reads:**
- First release allows exactly `operator_today` and `operator_close_day`.
- The MCP preflight gate is strict, but AOR remains the execution authority.
- AOR owns workflow execution and AOR audit; MCP owns the MCP request audit through the server/envelope layer.
- A successful MCP response returns status and artifact paths only. Full generated brief text is not returned through MCP.
- If MCP completion audit fails after AOR returns, MCP must return `system_error(workflow_invocation_audit_failed)` and must not re-run the workflow.

---

## Diagram Usage Notes

**For Pass 3 (file/module design):** Diagram 1 (V1 system context) is the primary reference for understanding which vault paths each module reads and which external systems it does or does not call.

**For Pass 4 (scaffold/build):** Diagram 3 (proposal flow sequence) is the primary reference for understanding the order of operations in the tool handler pipeline.

**For governance review:** Diagram 2 (authority ladder) is the primary reference for evaluating whether a proposed addition to V1 is within the intended authority ceiling.

**For Pass 6B / invocation implementation:** Diagram 5 is the primary reference for the active V2 `workflow.invoke_bounded` flow.

**For external communication:** Diagram 4 (surface map overview) is suitable for portfolio and architecture presentation contexts. It is honest about V1 scope and makes the deferred/excluded distinction visible.

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Server]] · [[ChaseOS-MCP-Surface-Map]] · [[ChaseOS-MCP-Workflow-Invocation]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Guardrails]] · [[ChaseOS-MCP-Data-Contracts]]*

*ChaseOS-MCP-Diagrams.md - v1.2 | Created: 2026-04-19 | Updated: 2026-04-21 Pass 6B (active V2 workflow invocation flow implemented; V1 diagrams preserved)*
