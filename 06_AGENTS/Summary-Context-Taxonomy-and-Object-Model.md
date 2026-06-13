---
title: Summary Context Taxonomy and Object Model
type: feature-architecture
status: seeded — summary-context consolidation layer
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 substrate classification -> Phase 10 summary object layer
---

# Summary Context Taxonomy and Object Model

> This document consolidates the next step implied by `Standalone-Summary-Context-Layer.md`.
> It defines a canonical summary-class taxonomy and a draft object-model direction so ChaseOS can unify summary handling across runtime-state, workflows, coordination, and operator-facing surfaces.

**Approval Center routing:** `approval_review` and approval-center summary destinations should route to [[ChaseOS-Approval-Center]] for current approval-surface semantics.

---

## 1. Purpose

The Summary Context Layer established the core feature claim:

**ChaseOS summaries should be treated as typed operating artifacts rather than generic text blobs.**

The application passes then proved that claim across multiple live or seeded slices:
- coordination bus summaries,
- runtime-state and bindings summaries,
- workflow/role-card-linked summaries,
- operator-shell / approval / runtime-browser summaries.

What remained open was consolidation.

ChaseOS now needs one doc that answers:
- what the canonical summary classes are,
- how they group into larger summary families,
- which fields should be shared across all summary records,
- which fields are slice-specific,
- and how summaries should remain visibly subordinate to deeper governance and machine-state sources.

This document is that consolidation layer.

---

## 2. Why This Needs Its Own Canonical Doc

Without a shared taxonomy and object-model direction, each future surface risks inventing its own summary language:
- runtime-state might call something `status`,
- coordination might call something `result`,
- approval views might call something `review item`,
- chronology surfaces might flatten everything into `activity`.

That would weaken ChaseOS in three ways:
1. it would blur governance distinctions,
2. it would make future standalone surfaces inconsistent,
3. it would allow summary rendering to drift away from source/runtime truth.

A canonical taxonomy prevents that drift.

---

## 3. Governing Rule

**A summary in ChaseOS is a typed derivative operating artifact.**

That means:
- it is derived from deeper source/runtime/governance state,
- it is useful for operator visibility and routing,
- it does not become canonical truth merely by being displayed,
- it must preserve authority posture, source posture, routing posture, and review/promotion posture.

This rule applies across all families below.

---

## 4. Taxonomy Structure

The taxonomy has three layers:

### A. Summary Family
The broad operating family the summary belongs to.

### B. Summary Class
The specific semantic type the summary represents.

### C. Summary Record
A concrete instance with source references, routing posture, timestamps, and runtime/workflow linkage.

This structure lets ChaseOS keep high-level coherence while still preserving subsystem-specific meaning.

---

## 5. Canonical Summary Families

| Summary family | What it covers | Typical source families | Typical Phase 10 surfaces |
|---|---|---|---|
| `runtime_posture` | runtime identity, attachment mode, capability posture, fail-closed status | `runtime/state/`, `runtime/bindings/`, nav/profile docs | runtime cockpit, posture panel, runtime browser |
| `workflow_execution` | workflow-linked outputs, contract-aware status, execution-facing summaries | workflow manifests, role cards, AOR outputs, operator briefs | workflow registry browser, runtime shell, approval center |
| `coordination` | dual-runtime task/result/blocker/review/heartbeat visibility | `runtime/agent_bus/`, coordination bridge docs | coordination inspector, blocker/review center, liveness strip |
| `browser_evidence` | bounded browser research, watchlist, evidence, monitored-source summaries | browser registry, browser workflow outputs, quarantine-adjacent captures | browser governance workspace, evidence panel |
| `audit_timeline` | build logs, agent activity, session/build summaries, chronology entries | `07_LOGS/Build-Logs/`, `07_LOGS/Agent-Activity/` | chronology browser, audit timeline, project history |
| `approval_review` | proposals, review-required items, promotion candidates, approval-needed actions | graph hygiene, graduation, Gate/approval-linked outputs | approval center, review queue |
| `operator_session` | runtime shell session state, live operator shell feeds, execution-route visibility | OSRIL/FSOS runtime session and event state | live operator shell, command route inspector |
| `provenance_trace` | trace/lineage summaries linking outputs back to sources and decisions | provenance schema, future trace records, logs + source refs | provenance explorer, chronology browser |

These families are intentionally broad enough to survive subsystem growth without losing type discipline.

---

## 6. Canonical Summary Classes

### 6A. Runtime Posture Family
| Summary class | Meaning |
|---|---|
| `runtime_posture_summary` | current resolved runtime + attachment posture |
| `bootstrap_input_summary` | startup evidence and contract inputs used for resolution |
| `user_attachment_summary` | attached vs detached personal posture |
| `runtime_capability_posture_summary` | what the runtime can currently do under bounded posture |
| `runtime_resolution_failure_summary` | fail-closed, unresolved, or contradictory startup state |
| `resolver_provenance_summary` | how posture was derived from deeper inputs |

### 6B. Workflow Execution Family
| Summary class | Meaning |
|---|---|
| `operator_briefing_summary` | operator-facing workflow output like morning/close-day briefing |
| `workflow_status_summary` | bounded execution-state summary tied to one workflow |
| `workflow_contract_summary` | summary of manifest + role-card posture for operator inspection |
| `workflow_output_summary` | typed emitted output from a workflow that is not merely raw text |
| `workflow_review_summary` | workflow-produced output that remains review-required |

### 6C. Coordination Family
| Summary class | Meaning |
|---|---|
| `coordination_task_summary` | new bounded task handoff |
| `coordination_result_summary` | returned work/result visibility |
| `coordination_blocker_summary` | blocked task requiring peer/operator help |
| `coordination_review_summary` | review-needed result or coordination handoff |
| `coordination_heartbeat_summary` | liveness and runtime posture snapshot |
| `coordination_notice_summary` | lower-stakes coordination visibility item |

### 6D. Browser Evidence Family
| Summary class | Meaning |
|---|---|
| `browser_watch_summary` | bounded watchlist or monitored-source summary |
| `browser_change_summary` | meaningful change detected on a watchlisted or monitored page |
| `browser_health_summary` | bounded page-health/status verification summary |
| `browser_evidence_summary` | evidence-oriented page/task output |
| `browser_extraction_summary` | bounded extracted content summary from approved page(s) |
| `browser_policy_summary` | operator-facing summary of browser governance posture |
| `browser_quarantine_summary` | browser-derived output whose trust posture remains quarantine/evidence-first |

### 6E. Audit Timeline Family
| Summary class | Meaning |
|---|---|
| `build_session_summary` | one build/documentation/engineering pass summary |
| `runtime_activity_summary` | runtime or automation activity event summary |
| `implementation_pass_summary` | architecture/bridge/application pass summary |
| `timeline_notice_summary` | low-severity chronological entry that still matters historically |

### 6F. Approval / Review Family
| Summary class | Meaning |
|---|---|
| `approval_request_summary` | action awaiting human approval |
| `promotion_proposal_summary` | candidate promotion/proposal requiring review |
| `review_queue_summary` | item awaiting validation/review |
| `decision_outcome_summary` | immutable decision/result summary after approval/review resolution |

### 6G. Operator Session Family
| Summary class | Meaning |
|---|---|
| `operator_session_summary` | current or recent runtime session state |
| `operator_event_feed_summary` | typed live-shell/event visibility item |
| `execution_route_summary` | shell command -> workflow -> AOR -> Gate route explanation |
| `surface_status_summary` | status of browser/terminal/desktop/filesystem execution surface |

### 6H. Provenance Trace Family
| Summary class | Meaning |
|---|---|
| `provenance_trace_summary` | compact lineage summary for an output or decision |
| `source_chain_summary` | source-to-output chain summary |
| `promotion_path_summary` | how an item moved toward review/promotion |
| `chronology_trace_summary` | timeline-aware summary linking multiple artifacts/events |

---

## 7. Shared Object Model Direction

Every summary record should eventually preserve a shared core shape.

### A. Required shared fields
```json
{
  "summary_id": "stable-id",
  "summary_family": "workflow_execution",
  "summary_class": "operator_briefing_summary",
  "title": "Optional human-readable title",
  "runtime_id": "hermes",
  "workflow_id": "operator_today",
  "authority_posture": "advisory",
  "source_posture": "workflow-produced",
  "promotion_posture": "draft",
  "routing_surface": "runtime_cockpit",
  "operator_action_needed": false,
  "created_at": "ISO-8601",
  "source_refs": [],
  "governance_refs": []
}
```

### B. Strongly recommended shared fields
```json
{
  "task_id": null,
  "session_id": null,
  "approval_id": null,
  "related_summary_ids": [],
  "status": null,
  "severity": "info",
  "visibility": "operator",
  "machine_truth_ref": null
}
```

### C. Payload extension area
Each family can extend with a structured payload:
```json
{
  "payload": {
    "family_specific": "fields live here"
  }
}
```

This prevents ad hoc top-level sprawl while still allowing family-specific meaning.

---

## 8. Family-Specific Extension Rules

### Runtime Posture extensions
Use fields such as:
- `attachment_mode`
- `bootstrap_status`
- `resolved_capabilities`
- `failure_reason`

### Workflow Execution extensions
Use fields such as:
- `role_card_id`
- `permission_ceiling`
- `writeback_targets`
- `output_class`

### Coordination extensions
Use fields such as:
- `runtime_from`
- `runtime_to`
- `intent`
- `task_status`
- `owner_runtime`

### Browser Evidence extensions
Use fields such as:
- `origin`
- `origin_group`
- `watchlist_id`
- `task_class`
- `evidence_posture`
- `quarantine_state`
- `change_criteria`
- `change_detected`

### Audit Timeline extensions
Use fields such as:
- `log_path`
- `session_date`
- `artifact_count`
- `timeline_bucket`

### Approval / Review extensions
Use fields such as:
- `approval_class`
- `requested_action`
- `decision_required_by`
- `decision_outcome`

### Operator Session extensions
Use fields such as:
- `current_step`
- `pending_approvals`
- `surface`
- `resume_state`

### Provenance Trace extensions
Use fields such as:
- `trace_depth`
- `origin_refs`
- `promotion_chain`
- `decision_refs`

---

## 9. Routing Rules by Family

| Summary family | Default routing surfaces | Never flatten into |
|---|---|---|
| `runtime_posture` | runtime cockpit, runtime browser, posture panel | generic status card with no derivation/provenance |
| `workflow_execution` | workflow registry browser, runtime shell, briefing view | anonymous output blob |
| `coordination` | coordination inspector, blocker/review center, liveness strip | generic chat transcript |
| `browser_evidence` | browser governance workspace, evidence panel | plain note with no trust/evidence posture |
| `audit_timeline` | chronology browser, audit timeline | orphaned markdown list item |
| `approval_review` | approval center, review queue | “done” card before decision resolution |
| `operator_session` | live operator shell, session panel, route inspector | canonical memory or permanent truth card |
| `provenance_trace` | provenance explorer, chronology browser | detached history note with no source chain |

---

## 10. Governance Rules for the Object Model

### A. Summary record is derivative, not sovereign
If doctrine, manifests, role cards, bus state, resolver inputs, or audit records conflict with a summary, the deeper source wins.

### B. Summary class must preserve review posture
Anything requiring review/approval must stay visibly review/approval-typed.
A display surface must not silently downgrade it to “completed.”

### C. Summary record must preserve source family truth
A coordination summary must remain visibly coordination-derived.
A runtime-state summary must remain visibly posture-derived.
A provenance summary must remain visibly trace-derived.

### D. Operator-facing convenience must not erase auditability
Friendly cards, feeds, and cockpit views are allowed.
Opaque summary objects with no source/governance link are not.

### E. Cross-surface consistency matters
The same summary record should be renderable in multiple surfaces without changing semantic class.
Only presentation changes; class meaning does not.

---

## 11. Relationship to Existing Summary-Context Application Passes

This document does not replace the existing applications.
It consolidates them.

### Coordination application contribution
Proved that task/result/blocker/review/heartbeat summaries are distinct machine-state mirrors.

### Runtime-state application contribution
Proved that posture/bootstrap/failure summaries must preserve derivation and fail-closed meaning.

### Workflow/role-card application contribution
Proved that outputs must remain tied to execution contracts and authority envelopes.

### Operator-shell application contribution
Proved that runtime shell, approvals, session feeds, and runtime-browser views need typed summary handling instead of dashboard-style flattening.

This consolidation layer is what lets those passes converge into one future summary object model.

---

## 12. Recommended Phase Placement

### Phase 9 contribution
- stabilize summary-family and summary-class language in docs
- keep source/runtime/governance distinctions intact in emitted artifacts
- ensure future machine-readable layers have enough metadata to populate summary records honestly

### Phase 10 contribution
- render summary records as typed operating artifacts
- let surfaces filter/sort by family, class, runtime, authority, and routing posture
- support provenance and chronology traversal without flattening distinctions

That makes this doc a **Phase 9 classification layer in service of a Phase 10 object/rendering layer**.

---

## 13. Recommended Near-Term Next Steps

1. Patch `Standalone-Summary-Context-Layer.md` so it points to this consolidation doc.
2. Reuse this taxonomy when refining:
   - Approval Center
   - runtime browser / cockpit
   - chronology browser
   - provenance explorer
   - `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
3. Later define the actual machine-readable summary-context schema once the first implementation surface is chosen.
4. Use this taxonomy as the classification source for any future summary-generating workflow or UI planning doc.

---

## 14. Current Verdict

The Summary Context Layer is no longer only a good idea or a set of isolated application passes.
ChaseOS now has a consolidation direction for:
- the summary families it needs,
- the summary classes it should preserve,
- and the shared object-model shape that future standalone/operator surfaces can build on.

So the rule becomes:

**A ChaseOS summary should be classifiable, routable, provenance-linked, and visibly subordinate to the deeper source/runtime/governance state from which it was derived.**

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Coordination-Bus-Summary-Context-Application]] · [[Runtime-State-and-Bindings-Summary-Context-Application]] · [[Workflow-Registry-and-Role-Cards-Standalone-Application]] · [[Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application]] · [[Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Markdown-to-Standalone-Bridge]] · [[ChaseOS-Studio-Architecture]]*

*Summary-Context-Taxonomy-and-Object-Model.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
