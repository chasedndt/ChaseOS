---
type: feature-filter
system: ChaseOS
feature_name: {{Feature Name}}
date: {{YYYY-MM-DD}}
outcome: {{Proposed | Adopted - First Wave | Adopted - Second Wave | Rejected | Later Candidate}}
---

# Feature Filter: {{Feature Name}}

**Date:** {{YYYY-MM-DD}}
**Evaluator:** {{who ran this filter pass}}
**Outcome:** {{outcome}}

---

## Q1: What problem does it solve in ChaseOS specifically?

{{Specific gap or operator workflow problem this closes.
Not "it would be nice" — what is currently broken, manual, or missing?}}

---

## Q2: Which ChaseOS layer does it belong to?

**Layer:** {{Capture | SIC | AOR | Gate/Governance | Interface | Vault/Knowledge}}

{{Explain the layer mapping. If it spans layers, identify the primary layer.}}

---

## Q3: What does it depend on that doesn't exist yet?

| Dependency | Status |
|------------|--------|
| {{Module / workflow / schema}} | {{not built | in progress | complete}} |
| ... | ... |

**Blocking dependencies:** {{list any that must be built first}}

---

## Q4: What is the permission ceiling?

- **Reads protected files:** {{yes / no}}
  {{If yes: which files, and why?}}
- **Writes beyond standard scope:** {{yes / no}}
  {{If yes: where, and is this justified?}}
- **External network calls:** {{yes / no}}
  {{If yes: what data leaves the vault?}}
- **Handles Tier 4 inputs:** {{yes / no}}
  {{If yes: how is prompt injection prevented?}}

**Declared permission ceiling:** {{e.g. no_protected_file_writes | read_only | append_only | etc.}}

---

## Q5: What are the failure modes?

| Failure Mode | User Sees | Corrupts State? | Recoverable? |
|-------------|-----------|-----------------|-------------|
| {{failure mode}} | {{what happens}} | {{yes/no}} | {{yes/no — how?}} |
| ... | ... | ... | ... |

**Default failure behavior:** {{escalate | log_and_continue | abort}}

---

## Q6: What is the Phase and pass sequence?

**Phase:** {{e.g. Phase 9}}
**Pass:** {{e.g. Pass 3}}

**Definition of Done:**
- [ ] {{success criterion 1}}
- [ ] {{success criterion 2}}
- [ ] {{tests pass}}

**Tests:**
- {{test_name: what it verifies}}

---

## Outcome and Next Step

**Outcome:** {{Proposed | Adopted - First Wave | Adopted - Second Wave | Rejected | Later Candidate}}

**Next step:**
- {{Where this goes: Feature-Fit-Register, Phase spec, roadmap entry, or parked}}

---

*Feature Filter — {{YYYY-MM-DD}}*


*Graph links: [[06_AGENTS/Vault-Map|Vault-Map]]*
