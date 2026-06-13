# Context Integrity Control Plane

Status: Canonical  
Layer: ChaseOS core control plane  
Purpose: Protect canonical documents from lossy agent compression, mojibake, and architecture memory loss.

## 1. Why This Exists

ChaseOS uses LLM agents for implementation, maintenance, research, and handover work.

LLM agents often manage long-running tasks by compressing context. That is acceptable inside the agent's temporary context, but dangerous when it leaks into source-controlled files.

This control plane exists because ChaseOS has observed a recurring bug:

> Agents make documentation "cleaner" or "more readable" while silently deleting architecture rationale, examples, governance language, and project-specific meaning.

For ChaseOS, that is not a cosmetic change. It is a system integrity issue.

## 2. Core Invariant

```text
Agent memory may be compacted.
Canonical source files must not be compacted without explicit approval.
```

## 3. Threat Model

The control plane protects against:

- mojibake,
- wrong file encoding,
- accidental UTF-8 damage,
- unapproved README shrinkage,
- deletion of design rationale,
- deletion of examples,
- over-normalized Markdown,
- generic rewrites of project-specific language,
- context summaries being written back into canonical docs,
- agent attempts to reduce token count by rewriting source-of-truth files.

## 4. Document Classes

### 4.1 Canonical documents

Canonical documents are protected. They store system meaning.

Examples:

```text
README.md
AGENTS.md
AGENT_EDITING_POLICY.md
docs/00_START_HERE.md
docs/canonical/**
docs/architecture/**
docs/harness/**
docs/evals/**
docs/changes/**
docs/governance/**
```

### 4.2 Working documents

Working documents may be rewritten more freely.

Examples:

```text
scratch/**
tmp/**
notes/drafts/**
logs/**
reports/generated/**
```

### 4.3 Generated documents

Generated documents may be regenerated, but should identify their source.

Examples:

```text
reports/generated/**
docs/generated/**
```

## 5. Agent Lifecycle Rules

### 5.1 Plan stage

Before editing, the agent must classify each target file:

```text
canonical | working | generated | code | config
```

If canonical, the agent must use minimal patches.

### 5.2 Edit stage

The agent must preserve:

- headings,
- named concepts,
- rationale,
- examples,
- diagrams,
- safety constraints,
- governance language,
- historical notes,
- human-in-the-loop decision points.

### 5.3 Verification stage

The agent must run:

```bash
python scripts/check_text_integrity.py
```

If staged changes exist:

```bash
python scripts/agent_doc_guard.py
```

### 5.4 Handover stage

The agent must report canonical doc changes separately from code changes.

## 6. Enforcement Components

### 6.1 Policy Layer

Files:

```text
AGENTS.md
AGENT_EDITING_POLICY.md
```

Function:

- communicates rules to agents,
- defines protected paths,
- defines allowed and disallowed edits.

### 6.2 Encoding Layer

Files:

```text
.editorconfig
.gitattributes
scripts/check_text_integrity.py
```

Function:

- enforce UTF-8 expectation,
- detect mojibake,
- detect replacement characters,
- prevent encoding corruption from entering the repo.

### 6.3 Diff Guard Layer

File:

```text
scripts/agent_doc_guard.py
```

Function:

- inspect staged Git changes,
- detect large canonical deletions,
- detect suspicious shrinkage,
- block unapproved structural rewrites.

### 6.4 CI Layer

File:

```text
.github/workflows/context-integrity.yml
```

Function:

- run integrity checks in pull requests,
- stop corruption before merge.

## 7. Failure Modes

### 7.1 Mojibake detected

Action:

1. Stop the change.
2. Restore from Git if needed.
3. Re-save the file as UTF-8.
4. Run the integrity check again.

### 7.2 Large canonical deletion detected

Action:

1. Inspect the diff manually.
2. Confirm whether the rewrite was requested.
3. If accidental, revert or narrow the patch.
4. If intentional, use explicit override.

### 7.3 Agent summarized a canonical file

Action:

1. Treat as architecture memory loss.
2. Restore original content from Git.
3. Reapply only the necessary targeted change.
4. Update handover with the incident.

## 8. Intentional Rewrite Protocol

A canonical doc can be rewritten only when explicitly requested.

Use:

```bash
CHASEOS_ALLOW_CANONICAL_DOC_REWRITE=1 python scripts/agent_doc_guard.py
```

The PR or handover must state:

```text
Canonical rewrite approved:
- File:
- Reason:
- What was preserved:
- What was intentionally removed:
- Human approval:
```

## 9. Practical Agent Instruction

Use this exact instruction in high-risk tasks:

```text
Do not compress, summarize, tone-normalize, or structurally rewrite ChaseOS canonical docs. Treat README.md, AGENTS.md, AGENT_EDITING_POLICY.md, and docs/canonical/** as protected architecture memory. Make only surgical edits unless I explicitly request a rewrite. Run text integrity checks before final handover.
```

## 10. Success Criteria

This control plane succeeds when:

- agents stop shrinking canonical docs without being asked,
- mojibake is caught automatically,
- canonical docs retain project-specific language,
- architecture rationale remains intact,
- handovers identify protected doc changes clearly,
- ChaseOS can safely use agentic development without silent memory erosion.
