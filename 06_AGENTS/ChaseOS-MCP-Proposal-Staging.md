---
title: ChaseOS MCP Proposal Staging
type: architecture-doc
status: frozen — v1.0 2026-04-20; staging path frozen; Pass 4 stdio scaffold implemented 2026-04-20
created: 2026-04-20
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Proposal Staging

> Defines the exact staging location, artifact shape, naming convention, retention model, and permission boundaries for MCP proposal artifacts.
>
> This document is the implementation-ready contract for `staging/store.py` in Pass 4.
> No deviations from this doc without a deliberate design decision.

---

## Frozen Decision: Staging Path

**Chosen path: `.chaseos/mcp-proposals/`**

This is a hard decision. The alternative (`07_LOGS/MCP-Proposals/`) was rejected.

### Rationale

| Factor | `.chaseos/mcp-proposals/` ✅ | `07_LOGS/MCP-Proposals/` ❌ |
|---|---|---|
| Vault graph indexing | **Outside** — proposals are transient, not knowledge artifacts | Inside — adds noise to vault graph; staged drafts are not canonical |
| Operator intent | Staging area ≠ log | Logs are records of what happened; staged proposals are pending intents |
| Consistency | `.chaseos/` is the established pattern for runtime-managed ephemeral state (e.g. `dedup_registry.json`, `watch_folders.json`) | Would require a new `07_LOGS/` subdirectory with no prior pattern match |
| Auditability | Audit records in `07_LOGS/Agent-Activity/` document that proposals exist — the staging area does not need to be in the log tree | — |
| Human review path | `approval_request.create` delivers the human-facing artifact to `07_LOGS/Operator-Briefs/` — the staging area stays internal | — |

**The staging area is an internal buffer, not a log.** Its contents are pending proposals awaiting review. Once reviewed (approved or rejected), the human operator acts outside the MCP surface. The staging area does not need to be in the vault graph or log tree.

---

## Staging Location Specification

```
vault_root/
└── .chaseos/
    └── mcp-proposals/          ← staging directory root
        ├── 20260420-113042__a1b2c3d4.json
        ├── 20260420-140520__e5f6g7h8.json
        └── ...
```

- **Parent directory:** `.chaseos/` (vault-root-relative, not vault-indexed)
- **Staging subdirectory:** `mcp-proposals/`
- **Full path from vault root:** `.chaseos/mcp-proposals/`

The `.chaseos/` directory is created at vault root by the MCP server if it does not exist. It is not a vault node — it does not appear in the graph substrate and is not indexed by MarkdownExtractor or YAMLManifestExtractor.

---

## Naming Convention

```
{YYYYMMDD-HHMMSS}__{proposal_id[:8]}.json
```

**Examples:**
```
20260420-113042__a1b2c3d4.json
20260420-140520__e5f6a789.json
```

**Rules:**
- `YYYYMMDD-HHMMSS` — UTC timestamp at staging time, zero-padded
- `__` — double underscore separator (consistent with AOR audit naming pattern)
- `proposal_id[:8]` — first 8 hex characters of the UUID4 proposal ID
- `.json` — always JSON; no other extensions

**Why UTC timestamp prefix?** Consistent with the AOR audit record convention (`{timestamp}__mcp__{surface}__{request_id[:8]}.json`). Enables chronological sorting without index lookups.

**Collision handling:** If two proposals receive the same timestamp prefix (concurrent submissions), the UUID suffix guarantees uniqueness. The timestamp prefix is informational, not a primary key. The `proposal_id` (full UUID4) is the primary key.

---

## Artifact Structure (ProposalArtifact JSON Schema)

Every staged proposal is a single JSON file with this fixed schema:

```json
{
  "schema_version": "1.0",
  "proposal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "staged_at": "2026-04-20T11:30:42Z",
  "runtime_id": "openclaw",
  "safety_mode_at_staging": "read_plus_proposal",
  "change_type": "update",
  "target_file": "00_HOME/Now.md",
  "description": "Update the sprint focus line to reflect Phase 9 MCP work.",
  "proposed_content": "...",
  "current_sha256": "abc123...",
  "proposed_sha256": "def456...",
  "governance_flags": {
    "is_protected_file": false,
    "permission_ceiling_respected": true,
    "writeback_scope_declared": true
  },
  "status": "staged",
  "status_history": [
    {"status": "staged", "at": "2026-04-20T11:30:42Z"}
  ]
}
```

### Field Definitions

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | Always `"1.0"` for V1 |
| `proposal_id` | string (UUID4) | yes | Primary key; full UUID, not truncated |
| `staged_at` | string (ISO 8601 UTC) | yes | Set by `ProposalStore.stage()` |
| `runtime_id` | string | yes | From permission envelope — identifies which runtime submitted |
| `safety_mode_at_staging` | string | yes | Active safety mode when proposal.submit was called |
| `change_type` | string enum | yes | `"create"`, `"update"`, or `"delete"` |
| `target_file` | string | yes | Vault-relative path to the file being proposed for change |
| `description` | string | yes | Human-readable explanation of the proposed change |
| `proposed_content` | string or null | yes | Full proposed file content for create/update; null for delete |
| `current_sha256` | string or null | yes | SHA-256 of current vault file, or null if file does not exist |
| `proposed_sha256` | string or null | yes | SHA-256 of proposed content, or null for delete |
| `governance_flags` | object | yes | Pre-checked governance summary at staging time |
| `status` | string enum | yes | `"staged"` on creation; may become `"validated"`, `"diff_previewed"`, `"approval_requested"` |
| `status_history` | array | yes | Append-only; each entry: `{status, at}` |

### Governance Flags at Staging Time

`governance_flags` is computed by `proposal.submit` before staging. It does not block staging — it records the validation state at submission time. A proposal with `is_protected_file: true` may still be staged, but `proposal.validate` will return a violation error, and `approval_request.create` will flag it for human review.

```json
"governance_flags": {
  "is_protected_file": false,
  "permission_ceiling_respected": true,
  "writeback_scope_declared": true
}
```

- `is_protected_file` — whether `target_file` is in the protected file list (e.g. `Permission-Matrix.md`, `Trust-Tiers.md`, `CLAUDE.md`)
- `permission_ceiling_respected` — whether the `change_type` is within the runtime's permitted write ceiling
- `writeback_scope_declared` — whether the `target_file` is within a declared writeback scope for the submitting runtime

---

## Protected File List (flagged by proposal.submit; enforced by proposal.validate)

The following files may be proposed for change via `proposal.submit`, but `governance_flags.is_protected_file` will be set to `true` and `proposal.validate` will return a violation:

- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Trust-Tiers.md`
- `CLAUDE.md`
- `04_SOPS/Credential-Boundaries-SOP.md`
- `04_SOPS/Untrusted-Input-Handling-SOP.md`
- `runtime/aor/engine.py`
- Any file matching `runtime/policy/adapters/*.yaml`

This list is hardcoded in `tools/proposal.py`. It is not loaded from a config file. Changes to this list require a code change in Pass 4+, not a config edit.

`proposal.submit` should not hard-reject solely because `target_file` appears in this list. It stages the proposal with `governance_flags.is_protected_file=true`. `proposal.validate` is the stage that returns the governance violation; `approval_request.create` may still surface the flagged proposal to a human, but no MCP apply path exists.

---

## Visibility and Auditability Model

| Audience | How They See Proposals |
|---|---|
| MCP client (runtime) | Via `proposal.validate` and `proposal.diff_preview` tool responses |
| Human operator | Via approval request artifacts in `07_LOGS/Operator-Briefs/` created by `approval_request.create` |
| Audit trail | Via audit records in `07_LOGS/Agent-Activity/` written by the server/envelope through `MCPAuditLogger` on every proposal tool call |
| Vault graph | Not indexed — `.chaseos/` is excluded from graph substrate extraction |
| Obsidian | Not indexed — `.chaseos/` is outside the vault's note graph |

**The staging area is opaque to graph queries and Obsidian.** This is intentional. Staged proposals are ephemeral; their audit trail is in `07_LOGS/Agent-Activity/`, and their human-readable delivery is in `07_LOGS/Operator-Briefs/`.

---

## Retention and Cleanup Stance

**V1 stance: no automatic cleanup.**

Staged proposals accumulate in `.chaseos/mcp-proposals/` indefinitely in V1. This is intentional:

- V1 has no apply/commit path — a proposal cannot be acted on by MCP
- Human operators decide what to do with staged proposals outside the MCP surface
- Cleanup is a future CLI command (`chaseos mcp proposals cleanup --older-than 30d`) — not in V1

**Implications for Pass 4:**
- `ProposalStore.list_staged()` returns all proposal IDs (no pagination in V1)
- No max-count enforcement in V1
- If `.chaseos/mcp-proposals/` does not exist, `ProposalStore.stage()` creates it

---

## What V1 Tools May Do in the Staging Area

| Tool | May Access | Cannot Access |
|---|---|---|
| `proposal.submit` | Write new JSON artifact | Read other proposals; modify existing |
| `proposal.validate` | Read the specified proposal by ID | List all proposals; read content of other proposals |
| `proposal.diff_preview` | Read the specified proposal by ID | List all proposals; read content of other proposals |
| `approval_request.create` | Read the specified proposal by ID | List all proposals; modify proposals |

**No V1 tool may:**
- Delete proposals from staging
- Modify an existing staged proposal's content
- Apply a staged proposal to the vault
- List all proposal IDs without a specific request (no ambient enumeration)

---

## Relationship to approval_request.create

`approval_request.create` is the bridge between the staging area and the human operator.

The flow:
1. Runtime calls `proposal.submit` → staging artifact created at `.chaseos/mcp-proposals/{name}.json`
2. Runtime calls `approval_request.create {proposal_id}` → reads staging artifact → writes human-readable markdown to `07_LOGS/Operator-Briefs/YYYYMMDD-approval-request-{id[:8]}.md`
3. Server/envelope writes an audit record to `07_LOGS/Agent-Activity/` documenting the approval request creation
4. Human operator reads the artifact in `07_LOGS/Operator-Briefs/` and decides what to do
5. **No MCP surface participates in step 4 or beyond.** There is no `proposal.approve` or `proposal.reject` tool in V1.

The staging artifact at `.chaseos/mcp-proposals/` persists after the approval request is created. It is the long-term record; the `07_LOGS/Operator-Briefs/` artifact is the human-delivery format.

---

## ProposalStore Implementation Contract (for Pass 4)

`staging/store.py` must implement `ProposalStore` with this exact interface:

```python
class ProposalStore:
    def __init__(self, staging_dir: Path) -> None:
        """staging_dir = vault_root / '.chaseos' / 'mcp-proposals'"""

    def stage(self, artifact: ProposalArtifact) -> str:
        """Write artifact JSON to staging_dir. Return proposal_id.
        Raises MCPSystemError if write fails.
        Creates staging_dir if it does not exist."""

    def read(self, proposal_id: str) -> ProposalArtifact | None:
        """Read and deserialize proposal by proposal_id.
        Returns None if not found (no error — caller decides policy)."""

    def rollback(self, proposal_id: str) -> None:
        """Delete a just-staged proposal after proposal.submit audit failure.
        Raises MCPSystemError if rollback fails."""

    def list_staged(self) -> list[str]:
        """Return list of proposal_id strings only — no content.
        Returns empty list if staging_dir does not exist."""
```

**Invariants:**
- `stage()` is atomic: JSON written fully or not at all (write-then-rename pattern)
- `read()` never raises on missing file — returns None
- `rollback()` is used only by the server/envelope after a `proposal.submit` audit failure; it is not a public cleanup tool
- `list_staged()` never raises — returns empty list on missing directory

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Module-Design]] · [[ChaseOS-MCP-Internal-Flow]] · [[ChaseOS-MCP-Audit-Policy]] · [[ChaseOS-MCP-Data-Contracts]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Server]] · [[Permission-Matrix]] · [[Autonomous-Operator-Runtime]]*

*ChaseOS-MCP-Proposal-Staging.md — v1.0 | Created: 2026-04-20 | Phase 9 Pass 3 (MCP Module Design Freeze) | Pass 4 implementation live in `runtime/mcp/staging/store.py`*
