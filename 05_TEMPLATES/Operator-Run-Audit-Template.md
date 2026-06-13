---
title: Operator Run Audit Template
type: template
status: active
version: 1.0
created: 2026-04-15
knowledge_class: canonical-state
---

# Operator Run Audit Template

> Use this template for human-readable audit notes for FSOS operator runs. The machine-readable audit artifact (JSON) is written automatically by the FSOS executor to `07_LOGS/Agent-Activity/`. This template is for operator-authored post-run review notes and escalations — not a replacement for the machine audit.

**File naming:** `07_LOGS/Agent-Activity/YYYY-MM-DD_HHMMSS_operator-{surface}-audit-{run_id}.md`

---

## Run Identity

| Field | Value |
|-------|-------|
| Run ID | `{run_id}` |
| Workflow ID | `{workflow_id}` |
| Surface | `{browser | terminal | desktop | filesystem}` |
| Started | `{YYYY-MM-DD HH:MM:SS}` |
| Completed | `{YYYY-MM-DD HH:MM:SS}` |
| Duration | `{MM:SS}` |
| Outcome | `{COMPLETE | FAILED | DENIED | HALTED}` |

---

## Scope Declared

```
target_uris:
  - {uri_1}
  - {uri_2}

allowed_origins:
  - {origin_1}

allowed_paths: (if filesystem)
  - {path_1}

forbidden_zones:
  - {zone_1}

max_actions: {N}
max_duration_seconds: {N}
credential_access: {true | false}
external_network: {true | false}
```

---

## Execution Summary

**Steps planned:** {N}
**Steps completed:** {N}
**Steps failed:** {N}
**Approvals required:** {N}
**Approvals granted:** {N}
**Approvals denied:** {N}
**Recovery attempts:** {N}

---

## Step Sequence

| Step | Action | Target | Outcome | Notes |
|------|--------|--------|---------|-------|
| 1 | `{action_type}` | `{target}` | ✓ / ✗ / ⏸ | {note} |
| 2 | `{action_type}` | `{target}` | ✓ / ✗ / ⏸ | {note} |
| ... | ... | ... | ... | ... |

---

## Approval Records

| Step | Action | Decision | Timestamp | Notes |
|------|--------|----------|-----------|-------|
| {N} | `{action_type}` on `{target}` | APPROVE / DENY | `{timestamp}` | {operator note} |

---

## Failures and Recovery

### Failure {N} (if any)

**Step:** {step number}
**Action:** `{action_type}`
**Target:** `{target}`
**Error:** {error description}
**Recovery attempted:** Yes / No
**Recovery outcome:** Succeeded / Failed
**Vault state after failure:** Unchanged / {describe any partial state}

---

## Outputs

### Vault Writes (if any)

| Type | Path | Capture ID |
|------|------|-----------|
| `{quarantine capture}` | `03_INPUTS/00_QUARANTINE/{class}/{filename}` | `{uuid}` |
| `{log entry}` | `07_LOGS/Agent-Activity/{filename}` | N/A |

### Content Extracted (if any)

{Brief description of what was extracted and its current status (quarantine / promoted / pending)}

---

## Operator Notes

{Any observations, concerns, or follow-up actions from the operator's review of this run}

---

## Follow-Up Actions

- [ ] {Promote extracted content from quarantine} — if applicable
- [ ] {File failure pattern in Execution Repair Memory} — if failure occurred
- [ ] {Update workflow manifest scope} — if scope was too narrow or too broad
- [ ] {Add to Decision Ledger} — if a significant decision was made about workflow design

---

## Linked Records

- Machine audit artifact: `07_LOGS/Agent-Activity/YYYY-MM-DD_HHMMSS_operator_{surface}_{run_id}.json`
- Workflow manifest: `runtime/workflows/registry/{workflow_id}.yaml`
- Capture records (if any): `03_INPUTS/00_QUARANTINE/...`

---

*Template: Operator-Run-Audit-Template.md | v1.0 | Created: 2026-04-15 | Phase 9 FSOS sub-track | Use for human-readable operator run reviews | Machine-readable JSON audit is written automatically by executor*


*Graph links: [[06_AGENTS/Vault-Map|Vault-Map]]*
