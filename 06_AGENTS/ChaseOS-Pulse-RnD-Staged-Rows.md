# ChaseOS Pulse R&D Staged Rows

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** STAGED ONLY - do not insert until operator approval  
**Created:** 2026-04-30  
**Updated:** 2026-05-02  
**Runtime:** Codex  
**Source audit:** `06_AGENTS/ChaseOS-Pulse-Reconciliation-Truth-State-Audit.md`; `06_AGENTS/ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md`

## Boundary

This file stages recommended R&D workbook rows for ChaseOS Pulse after the
architecture, scaffold, reconciliation, and truth-state audit evidence exists.

This is not a workbook update. The workbook remains untouched until the operator
explicitly approves a sync pass.

2026-05-02 update: `06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Update-Approval.md`
is the current no-write approval packet for the future workbook sync. It extends
these staged rows with live backend proof rows for Agent Bus review handoff,
review-response ingest, candidate apply, evidence gates, and post-apply
truth-state audit status. The workbook still remains untouched.

2026-05-02 sync update: after operator approval, the workbook sync was completed
and recorded at `06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Sync.md`. Inserted rows:
`FR-028`, `F176`-`F198`, `FIT-132`-`FIT-139`, and `CH-1005`.

Latest workbook observed:

```text
99_ARCHIVE/Reporting/ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx
LastWriteTime: 28/04/2026 17:08:08
```

## Proposed Feature Register Rows

| Proposed feature | Suggested status | Phase lane | Evidence | Boundary note |
|---|---|---|---|---|
| ChaseOS Pulse Core | PARTIAL | Phase 9 backend/control-plane; Phase 10 UI later | `06_AGENTS/ChaseOS-Pulse-Architecture.md`; `runtime/pulse/` | Native ChaseOS proactive layer; not a generic digest |
| Context Memory Core | PARTIAL | Phase 9 | `06_AGENTS/Context-Memory-Core.md`; `runtime/memory/` | Candidate-first; no automatic canonical memory |
| Personal Map / User Profile Graph | PARTIAL | Phase 9 schema, Phase 10 visualization | `06_AGENTS/Personal-Map-Architecture.md`; `runtime/memory/personal_map.py` | Distinct from Vault Map; persistence/inspector not built |
| AgentHub Runtime Profiles | PARTIAL | Phase 9 | `06_AGENTS/AgentHub-Spec.md`; `runtime/agents/agent_hub.py`; `runtime/agents/runtime_profile.py` | Registration/profile layer only; no authority grant |
| Agent Runtime Brain Layer | PARTIAL | Phase 9 | `06_AGENTS/Agent-Runtime-Brain-Architecture.md`; `runtime/agents/runtime_brain.py` | Advisory brain fields; self-upgrade inactive |
| Execution Repair Memory | PARTIAL | Phase 9 | `runtime/agents/execution_repair_memory.py`; `runtime/agents/test_execution_repair_memory.py` | Schema-only runtime memory; no automatic SOP/runtime-map mutation |
| Runtime Navigation Map Integration for Pulse | PLANNED | Phase 9/10 | `06_AGENTS/AgentHub-Spec.md`; `06_AGENTS/Agent-Runtime-Brain-Architecture.md` | Referenced only; writer/inspector not built |
| Agent Identity Ledger Integration for Pulse | PLANNED | Phase 9/10 | `06_AGENTS/AgentHub-Spec.md` | Referenced only; Pulse ledger writer not built |
| Agent Pulse Decks | PARTIAL | Phase 9 | `runtime/pulse/card_schema.py`; `runtime/agents/execution_repair_memory.py` | Agent card schema exists; production deck runner not built |
| Native Pulse Schedule Manifest + Catch-Up Policy | PARTIAL | Phase 9 | `runtime/schedules/manifests/chaseos_pulse_daily.yaml`; `hermes_runtime_pulse.yaml` | Inactive intent only; live runner not built |
| Pulse Card Schema + Renderers | PARTIAL | Phase 9 | `runtime/pulse/card_schema.py`; `renderer_markdown.py`; `renderer_json.py` | Backend schema/renderers exist; full visual card UI not built |
| Pulse Feedback Rules | PARTIAL | Phase 9 | `runtime/memory/feedback_rules.py`; `runtime/pulse/feedback.py`; `runtime/memory/feedback-rules/accepted-signals.jsonl` | One approved feedback-ranking signal applied to non-canonical runtime memory; no automatic memory/project/knowledge mutation |
| Pulse Feedback Review Queue | PARTIAL | Phase 9 | `runtime/pulse/feedback_review_queue.py`; `runtime/pulse/review_decision_log.py`; `pulse-ingest-decision-0aa8eb44a239` | Review decision ingest proven for one Hermes review; approvals remain governed |
| Pulse Governed Writeback | PARTIAL | Phase 9 | `runtime/pulse/writeback.py`; `06_AGENTS/Pulse-Feedback-Policy.md`; `07_LOGS/Pulse-Decks/apply-registry/applied-decisions.json` | Non-canonical feedback apply proven; no canonical writeback |
| Pulse Local Deck Surface | PARTIAL | Phase 10A0 foothold | `runtime/pulse/local_surface.py` | Static local artifact projection; not full Studio UI |
| Pulse UI / Dashboard Surface | PLANNED | Phase 10 | `06_AGENTS/ChaseOS-Pulse-Architecture.md` | Full visual UI, approval queue, and dashboard not built |
| Pulse Truth-State Auditor | PARTIAL | Phase 9 | `06_AGENTS/ChaseOS-Pulse-Reconciliation-Truth-State-Audit.md`; `runtime/pulse/test_pulse_reconciliation_truth.py` | Audit doc and guard tests exist; broader automated auditor not built |
| Pulse Research / Source Scanner | PLANNED | Phase 10+ or gated Phase 9 continuation | `06_AGENTS/ChaseOS-Pulse-Architecture.md` | No unrestricted web scanning; connectors must be opt-in |
| Pulse Permission Envelopes | PLANNED | Phase 10+ | `06_AGENTS/Pulse-Feedback-Policy.md`; governance docs | No broad autonomous permission envelopes added |

## Proposed Feature Fit Rows

| Proposed fit row | Fit rationale | Required owner | Current evidence state |
|---|---|---|---|
| Pulse native scheduling fit | Aligns Pulse with ChaseOS-owned schedule intent and adapter-only execution | ChaseOS runtime/control plane | Inactive manifests verified |
| Pulse memory-governance fit | Keeps context events, atoms, Personal Map, and feedback rules candidate-first | ChaseOS memory/governance | Schema tests verified |
| Pulse agent-learning fit | Makes runtime repair and skill-gap signals inspectable without hidden self-upgrade | AgentHub/runtime memory | Runtime brain and repair schema tests verified |
| Pulse UI handoff fit | Separates backend/local artifacts from Phase 10 visual dashboard work | Studio/Pulse UI | Static surface exists; full UI not built |
| Pulse writeback fit | Preserves no-canonical-writeback default and approval gates | ChaseOS Gate/writeback layer | Log-only writeback and feedback queue verified |

## Approval Requirements Before Workbook Sync

- Operator explicitly approves an R&D workbook sync pass. COMPLETE 2026-05-02.
- Workbook row IDs and family IDs are assigned against the current workbook. COMPLETE 2026-05-02.
- Existing rows are checked for duplicates before insertion. COMPLETE 2026-05-02.
- New rows use PARTIAL/PLANNED statuses only unless backed by tests/live proof. COMPLETE 2026-05-02.
- The sync pass records workbook path, exact rows inserted, formulas checked,
  build log, archive note, daily note, and indexes. COMPLETE 2026-05-02.
- Current sync record: `06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Sync.md`.

## Non-Insert Items

Do not insert rows that claim:

- full ChaseOS Pulse complete
- full visual UI complete
- live native schedule runner complete
- unrestricted browsing or external connector scanning complete
- autonomous memory approval complete
- task creation from feedback complete
- canonical `02_KNOWLEDGE/` promotion complete
- agent self-upgrade active


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
