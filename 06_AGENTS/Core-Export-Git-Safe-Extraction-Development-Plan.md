# Core Export Git-Safe Extraction Development Plan

> **For Hermes / OpenClaw / Codex / Archon:** this is a runtime-handoff-ready implementation plan. Route coordination-sensitive work through `runtime/agent_bus/`; do not use Discord/chat thread state as the machine source of truth.

**Goal:** Build a proper Git-safe ChaseOS Core extraction feature that can generate a substantial, reviewable, privacy-safe Core repository candidate before any Git initialization, commit, remote, push, or publication.

**Architecture:** Keep the private ChaseOS workspace as the source of truth. The `core_export/` lane owns allowlist manifests, curated templates, sanitizer/scanner policy, dry-run reports, manual review artifacts, and Gate-governed local export/update operations. The sibling `<WSL_WINDOWS_USER_HOME>/Documents/chaseos-core` tree is generated output only; it must never be hand-filled by dragging private files into place.

**Tech Stack:** Python stdlib, PyYAML via `uvx --with pyyaml`, ChaseOS CLI wrapper (`python3 chaseos.py ...`), canonical runtime CLI (`python3 -m runtime.cli.main ...`), Obsidian markdown docs, `runtime/agent_bus/` for cross-runtime coordination.

---

## 0. Current Live Truth

Source workspace:

```text
<WSL_CHASEOS_VAULT_ROOT>
```

Current local export target:

```text
<WSL_WINDOWS_USER_HOME>/Documents/chaseos-core
```

Current tracked export-candidate state:

```text
manifest_candidate_count: 57
rendered_preview_count: 57
scanner_blockers: 0
last_recorded_local_export_update: passed
last_recorded_verify_export: passed
2026-05-11_live_revalidation: blocked_target_absent_and_manual_review_missing
.git: absent
Git init: not performed
commit: not performed
remote/push/publication: not performed
canonical promotion: not performed
```

The earlier six-file seed proved the export/verification lane existed but was too thin for Git readiness. The current expanded candidate is no longer that six-file seed: the latest tracker/report/build-log packet records 57 manifest candidates/previews, a guarded update to the local `%USERPROFILE%\Documents\chaseos-core` (`<WSL_WINDOWS_USER_HOME>/Documents/chaseos-core`) inspection target, and a recorded verify-export pass with no scanner blockers. A 2026-05-11 live revalidation found that target absent in this environment and `core_export/reports/latest/manual-preview-review-pass2.md` missing, so current verify-export is blocked until the target and review artifact are restored through the guarded export lane.

This still does **not** approve Git initialization, license choice, public `.gitignore`, remote creation, push/publication, or canonical promotion. The next safe slice is target/review-artifact reconciliation, verify-export rerun, candidate review, and public-readiness cleanup, followed by a separate Git-init approval request only if review remains clean.

## 1. Non-Negotiable Boundaries

1. Do not initialize Git until a separate explicit operator/Gate approval is provided for Git init.
2. Do not commit, add a remote, push, publish, or canonical-promote in this feature-development lane.
3. Do not manually copy private source files into `<WSL_WINDOWS_USER_HOME>/Documents/chaseos-core`.
4. Do not weaken scanner rules to make a candidate pass.
5. Do not include private logs, raw inputs, runtime state, local bindings, credentials, channel IDs, account IDs, or machine-specific live configuration in public Core.
6. Do not treat `.gitignore` as the privacy boundary. The privacy boundary is: allowlist manifest → template/sanitizer render → scanner → dry-run report → verifier → manual review → approved export.
7. Runtime-to-runtime development coordination must use `runtime/agent_bus/`, not ambient Discord/thread state.

## 2. Definition of a Proper Git-Safe Core Candidate

A future Core candidate is Git-init-ready only when it contains enough sanitized/template material for a reviewer to understand ChaseOS as an operating system/framework:

- Root orientation: `README.md`, `PROJECT_FOUNDATION.md`, `CORE_MANIFEST.md`, `FORKING.md`, `ROADMAP.md`.
- Framework bootstrapping examples: operating-system, now, dashboard, project, knowledge, input, and log examples.
- Governance pack: Vault Map/routing guide, Permission Matrix, Trust Tiers, Gate, adapter standards, security model, AOR, runtime coordination doctrine.
- SOP pack: build log, research ingest, promotion, untrusted input, failure/ambiguity.
- Template pack: project OS, source note, synthesis note, decision log, agent activity/session, runtime profile, adapter compliance.
- Optional runtime/docs pack: sanitized runtime README/commands/schema docs only after separate review.
- Local provenance/status artifacts are either sanitized or intentionally excluded from first public commit.

## 3. Target Output Shape

Recommended generated tree shape before Git init:

```text
chaseos-core/
  README.md
  PROJECT_FOUNDATION.md
  CORE_MANIFEST.md
  FORKING.md
  ROADMAP.md
  LICENSE
  .gitignore
  docs/
    framework-home/
      Operating-System.example.md
      Now.example.md
      Dashboard.example.md
      Principles.example.md
    projects-example/
      Example-Project-OS.md
    knowledge-example/
      Knowledge-Index.example.md
      Source-Note.example.md
    inputs-example/
      README.md
    logs-example/
      Build-Logs-Index.example.md
  04_SOPS/
    Build-Log-SOP.md
    Research-Ingest-SOP.md
    Promotion-Session-SOP.md
    Untrusted-Input-Handling-SOP.md
    Agent-Failure-Ambiguity-SOP.md
  05_TEMPLATES/
    Project-OS-Template.md
    Source-Note-Template.md
    Synthesis-Note-Template.md
    Decision-Log-Template.md
    Decision-Ledger-Entry-Template.md
    Agent-Activity-Log-Template.md
    Agent-Session-Log-Template.md
    Agent-Runtime-Profile-Template.md
    Adapter-Compliance-Checklist.md
  06_AGENTS/
    Vault-Map.md
    Agent-Control-Plane.md
    Permission-Matrix.md
    Trust-Tiers.md
    ChaseOS-Gate.md
    Execution-Adapter-Standard.md
    Adapter-Manifest-Standard.md
    Agent-Security-Model.md
    Autonomous-Operator-Runtime.md
    Runtime-InterAgent-Coordination-Bus.md
    Agent-Output-Conventions.md
  runtime/                       # optional later slice; docs/schemas first
    README.md
    Runtime-Layer-Guide.md
    schemas/
      provenance_schema.md
```

## 4. Implementation Strategy

### Phase A — Inventory and Classification

**Objective:** Build a machine-readable inventory that distinguishes direct-safe, template-required, blocked, and later/deferred candidates.

**Files:**
- Create: `core_export/core_candidate_inventory.yaml`
- Create: `core_export/reports/latest/core-candidate-inventory-review-2026-04-30.md`
- Modify later: `core_export/export_manifest.yaml`

**Classification values:**

```yaml
classification: direct_sanitized | core_template | synthetic_example | blocked | deferred
review: required
risk_level: low | medium | high
reason: "short reason"
```

**Initial candidate groups:**

```yaml
root_docs:
  - README.md
  - PROJECT_FOUNDATION.md
  - CORE_MANIFEST.md
  - FORKING.md
  - ROADMAP.md
framework_examples:
  - docs/framework-home/Operating-System.example.md
  - docs/framework-home/Now.example.md
  - docs/framework-home/Dashboard.example.md
  - docs/framework-home/Principles.example.md
governance_pack:
  - 06_AGENTS/Vault-Map.md
  - 06_AGENTS/Agent-Control-Plane.md
  - 06_AGENTS/Permission-Matrix.md
  - 06_AGENTS/Trust-Tiers.md
  - 06_AGENTS/ChaseOS-Gate.md
  - 06_AGENTS/Execution-Adapter-Standard.md
  - 06_AGENTS/Adapter-Manifest-Standard.md
  - 06_AGENTS/Agent-Security-Model.md
  - 06_AGENTS/Autonomous-Operator-Runtime.md
  - 06_AGENTS/Runtime-InterAgent-Coordination-Bus.md
sop_pack:
  - 04_SOPS/Build-Log-SOP.md
  - 04_SOPS/Research-Ingest-SOP.md
  - 04_SOPS/Promotion-Session-SOP.md
  - 04_SOPS/Untrusted-Input-Handling-SOP.md
  - 04_SOPS/Agent-Failure-Ambiguity-SOP.md
template_pack:
  - 05_TEMPLATES/Project-OS-Template.md
  - 05_TEMPLATES/Source-Note-Template.md
  - 05_TEMPLATES/Synthesis-Note-Template.md
  - 05_TEMPLATES/Agent-Activity-Log-Template.md
  - 05_TEMPLATES/Agent-Session-Log-Template.md
  - 05_TEMPLATES/Agent-Runtime-Profile-Template.md
  - 05_TEMPLATES/Adapter-Compliance-Checklist.md
```

**Verification:**

```bash
PYTHONPATH=. uvx --with pyyaml python - <<'PY'
import yaml
from pathlib import Path
p = Path('core_export/core_candidate_inventory.yaml')
data = yaml.safe_load(p.read_text())
assert data['version']
assert data['candidates']
print('inventory_ok True')
PY
```

### Phase B — Template Pack Expansion

**Objective:** Add curated Core-safe templates/synthetic examples for docs that should not be copied from the private instance.

**Files:**
- Create under `core_export/templates/`:
  - `ROADMAP.core.md`
  - `Vault-Map.core.md`
  - `Agent-Control-Plane.core.md`
  - `Permission-Matrix.core.md`
  - `Trust-Tiers.core.md`
  - `ChaseOS-Gate.core.md`
  - `Agent-Security-Model.core.md`
  - `Autonomous-Operator-Runtime.core.md`
  - `Runtime-InterAgent-Coordination-Bus.core.md`
  - `docs/framework-home/Operating-System.example.md`
  - `docs/framework-home/Now.example.md`
  - `docs/framework-home/Dashboard.example.md`
  - `docs/projects-example/Example-Project-OS.md`
  - `docs/knowledge-example/Knowledge-Index.example.md`
  - `docs/logs-example/Build-Logs-Index.example.md`

**Rule:** prefer curated templates over sanitizer rewrites for any file with private-instance shape.

**Verification:**

```bash
python3 -m py_compile runtime/core_export/sanitizers.py runtime/core_export/exporter.py
PYTHONPATH=. uvx --with pyyaml pytest runtime/tests/test_core_export_sanitizer.py -q -p no:cacheprovider
```

### Phase C — Manifest Expansion

**Objective:** Expand `core_export/export_manifest.yaml` so the dry-run export contains the real Core candidate set.

**Files:**
- Modify: `core_export/export_manifest.yaml`
- Modify/add tests: `runtime/tests/test_core_export_dry_run.py`, `runtime/tests/test_core_export_sanitizer.py`

**Manifest rules:**

```yaml
include:
  - source: ROADMAP.md
    target: ROADMAP.md
    mode: core_template
    template: core_export/templates/ROADMAP.core.md
    review: required
```

Use `core_template` for synthetic examples where no private source exists. If the current exporter requires a source path, add a safe virtual/synthetic source mode with tests rather than inventing fake private sources.

**Verification:**

```bash
PYTHONPATH=. uvx --with pyyaml python -m runtime.cli.main core-export build --dry-run \
  --source-root . \
  --target <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core \
  --manifest core_export/export_manifest.yaml \
  --write-report \
  --report-dir core_export/reports/latest \
  --json >/tmp/core_export_expanded_dry_run.json

PYTHONPATH=. uvx --with pyyaml python -m runtime.cli.main core-export verify-report \
  --source-root . \
  --target <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core \
  --manifest core_export/export_manifest.yaml \
  --report-dir core_export/reports/latest \
  --json >/tmp/core_export_expanded_verify_report.json
```

Expected:

```text
writes_performed: false
git_initialized: false
publication_performed: false
blocking_count: 0
preview_count: > 4
```

### Phase D — Manual Preview Review Packet

**Objective:** Produce a review packet that any runtime or human can inspect without mutating the export target.

**Files:**
- Create: `core_export/reports/latest/manual-preview-review-full-core-YYYY-MM-DD.md`
- Create: `core_export/reports/latest/runtime-handoff-core-export-expansion-YYYY-MM-DD.md`

**Review table columns:**

```text
target path | source/template | mode | privacy risk | framework completeness | verdict | notes
```

**Verdicts:**

```text
pass candidate
conditional pass
blocked
```

### Phase E — Request Export Update Approval

**Objective:** Once the expanded preview is clean, ask for explicit operator approval to update the local export tree. This is not Git init.

**Command preview:**

```bash
python3 chaseos.py core-export export \
  --source-root <WSL_CHASEOS_VAULT_ROOT> \
  --target <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core \
  --manifest <WSL_CHASEOS_VAULT_ROOT>/core_export/export_manifest.yaml \
  --report-dir <WSL_CHASEOS_VAULT_ROOT>/core_export/reports/latest \
  --manual-review <WSL_CHASEOS_VAULT_ROOT>/core_export/reports/latest/manual-preview-review-full-core-YYYY-MM-DD.md \
  --operator-approval-ref '<APPROVAL_REF>' \
  --confirm \
  --json
```

**Approval wording:**

```text
Approve local Core export update only. Approval ref: APPROVED-CORE-EXPORT-UPDATE-YYYY-MM-DD
```

### Phase F — Verify Expanded Export

**Objective:** Validate the generated expanded local export before any Git approval.

**Commands:**

```bash
PYTHONPATH=. uvx --with pyyaml python -m runtime.cli.main core-export verify-export \
  --source-root . \
  --target <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core \
  --manifest core_export/export_manifest.yaml \
  --report-dir core_export/reports/latest \
  --json >/tmp/core_export_expanded_verify_export.json

PYTHONPATH=. python3 -m runtime.cli.main core-export next-step \
  --source-root . \
  --target <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core \
  --manifest core_export/export_manifest.yaml \
  --report-dir core_export/reports/latest \
  --json >/tmp/core_export_expanded_next_step.json
```

Expected:

```text
verify_export_ok: true
verified_file_count: substantially greater than 4
hash_mismatches_empty: true
missing_files_empty: true
git_initialized: false
publication_performed: false
next_step_kind: approve_git_init
```

### Phase G — Git Init Gate Only After Expanded Verification

**Objective:** Keep Git init separate and explicit.

**Approval wording when ready:**

```text
Approve Git init for expanded local Core export only. Approval ref: APPROVED-CORE-GIT-INIT-YYYY-MM-DD
```

Allowed scope after that future approval:

```text
initialize Git locally inside <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core
normalize default branch to main if needed
no commit unless separately approved
no remote
no push
no publication
no canonical promotion
```

## 5. Runtime Handoff Model

### Bus-first rule

Runtime implementers should create/claim tasks through `runtime/agent_bus/`. Each task should include:

```yaml
source_platform: discord
source_channel_class: hermes-chat
conversation_key: core-export-git-safe-extraction
work_fingerprint: core-export-git-safe-extraction:<slice-id>
```

### Suggested runtime division

| Runtime | Role | First task |
|---|---|---|
| Hermes / Optimus | planning, governance, docs, status, review packets | maintain this plan, logs, and operator-facing readiness |
| Codex | implementation/tests | manifest expansion, synthetic source/template support, CLI contract/docs sync |
| OpenClaw | Windows-local/manual validation lane | inspect generated export tree in Windows IDE, confirm local path behavior, no WSL-only assumptions |
| Archon | architecture/code-review lane | review candidate pack completeness, privacy posture, and runtime handoff coherence |

## 6. Agent Bus Task Packet Templates

### Packet A — Inventory

```yaml
packet_id: core-export-inventory
sender: Operator
recipient: Codex
kind: implementation
request: >
  Build core_export/core_candidate_inventory.yaml and a report artifact classifying
  root docs, framework examples, governance docs, SOPs, templates, and runtime docs
  into direct_sanitized/core_template/synthetic_example/blocked/deferred.
constraints:
  - no Git init
  - no export target mutation
  - no commit/push/publication
  - use PYTHONPATH=. uvx --with pyyaml for YAML validation
outputs:
  - core_export/core_candidate_inventory.yaml
  - core_export/reports/latest/core-candidate-inventory-review-YYYY-MM-DD.md
verification:
  - YAML parses
  - agent_bus status OK
  - <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core/.git absent
```

### Packet B — Template Expansion

```yaml
packet_id: core-export-template-expansion
sender: Operator
recipient: Codex
kind: implementation
request: >
  Add curated Core templates/examples for the minimum Git candidate shape.
  Prefer synthetic docs over rewriting private state.
constraints:
  - no private source copying into export target
  - no Git init
  - no publication
outputs:
  - core_export/templates/*.core.md
  - core_export/templates/docs/**/*.md
verification:
  - scanner clean after rendered previews
  - focused sanitizer tests pass
```

### Packet C — Governance Review

```yaml
packet_id: core-export-governance-review
sender: Operator
recipient: Archon
kind: architecture-review
request: >
  Review the expanded candidate set for ChaseOS OS alignment: Core/Personal split,
  Gate, trust tiers, permission model, runtime governance, AOR, and coordination bus.
constraints:
  - review only
  - no file writes outside review report unless explicitly assigned
outputs:
  - core_export/reports/latest/archon-core-governance-review-YYYY-MM-DD.md
verification:
  - identifies pass/conditional/blocked docs
  - flags missing essentials before Git init
```

### Packet D — Windows/IDE Validation

```yaml
packet_id: core-export-windows-ide-validation
sender: Operator
recipient: OpenClaw
kind: validation
request: >
  Inspect the generated <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core tree from the
  Windows/local IDE perspective and confirm whether it is usable as a Git candidate.
constraints:
  - no Git init
  - no commit/push/publication
  - no credential/session expansion
outputs:
  - core_export/reports/latest/openclaw-core-export-windows-review-YYYY-MM-DD.md
verification:
  - confirms file count and tree shape
  - flags Windows path/tooling issues
```

## 7. Required Validation Ladder

Run this ladder after each code-affecting slice:

```bash
python3 -m py_compile runtime/core_export/exporter.py runtime/core_export/sanitizers.py runtime/cli/core_export_commands.py runtime/cli/main.py
PYTHONPATH=. uvx --with pyyaml pytest runtime/tests/test_core_export_sanitizer.py runtime/tests/test_core_export_dry_run.py -q -p no:cacheprovider
PYTHONPATH=. uvx python -m runtime.cli.generate_docs --check
PYTHONPATH=. python3 -m runtime.cli.main agent-bus status --json >/tmp/agent_bus_status_core_export_dev.json
```

Run expanded dry-run/report validation before any local export update:

```bash
PYTHONPATH=. uvx --with pyyaml python -m runtime.cli.main core-export build --dry-run \
  --source-root . \
  --target <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core \
  --manifest core_export/export_manifest.yaml \
  --write-report \
  --report-dir core_export/reports/latest \
  --json

PYTHONPATH=. uvx --with pyyaml python -m runtime.cli.main core-export verify-report \
  --source-root . \
  --target <WSL_WINDOWS_USER_HOME>/Documents/chaseos-core \
  --manifest core_export/export_manifest.yaml \
  --report-dir core_export/reports/latest \
  --json
```

## 8. Completion Criteria Before Git Init Approval

Git init can be requested only when all are true:

- [ ] Expanded manifest contains a representative Core candidate set.
- [ ] Rendered previews exist for every candidate.
- [ ] Scanner reports zero blockers on rendered previews.
- [ ] Verify-report passes with hash-stable preview metadata.
- [ ] Manual preview review marks every candidate pass or conditional pass with resolved conditions.
- [ ] Approved local export/update has generated the expanded export tree.
- [ ] Verify-export passes against the expanded export tree.
- [ ] `.git` remains absent.
- [ ] `CORE_EXPORT_STATUS.json` or successor status confirms Git/publication false.
- [ ] Operator confirms the expanded tree is substantial enough to be the local Git candidate.

## 9. First Next Step

Start with Phase A + Phase B as dry-run/report work only:

```text
Inventory + template expansion only. No export target update. No Git init.
```

This gives other runtimes enough structured state to pick up feature development without guessing from Discord history.

## 10. 2026-05-01 Continuation Status

Codex completed the first expansion slice as dry-run/report work only:

- `core_export/core_candidate_inventory.yaml` created.
- `core_export/reports/latest/core-candidate-inventory-review-2026-05-01.md` created.
- curated Core templates/examples added under `core_export/templates/`.
- `core_export/export_manifest.yaml` expanded to 39 preview candidates.
- `core_export/reports/latest/core-export-dry-run-report.json` regenerated against a scratch target path.
- rendered previews regenerated under `core_export/reports/latest/previews/`.
- `core_export/reports/latest/manual-preview-review-full-core-2026-05-01.md` created as the manual review packet.
- `core_export/reports/latest/runtime-handoff-core-export-expansion-2026-05-01.md` created.

Validation result:

```text
expanded_dry_run_ok True
candidate_count 39
preview_count 39
preview_scanner_blocking_count 0
verify_report_ok True
missing_previews []
hash_mismatches []
seed_export_file_count 6
seed_export_git_absent True
```

No local export update, Git initialization, commit, remote, push, publication, canonical promotion, or manual private-file copy occurred.

Next safe step:

```text
Manual review the 39 rendered previews. If approved, request a separate local export update approval only. Git init remains a later separate Gate.
```

## 11. 2026-05-01 Candidate Completeness Pass

Codex completed the next candidate-completeness slice as dry-run/report work only:

- `core_export/core_candidate_inventory.yaml` updated to version 0.2.
- `core_export/export_manifest.yaml` expanded from 39 to 56 preview candidates.
- Curated Core-safe templates/examples added for:
  - credential boundaries SOP;
  - knowledge taxonomy;
  - ingestion architecture;
  - Source Intelligence Core architecture;
  - agent registry example;
  - supported backends example;
  - coordination bus folder guide;
  - coordination task packet example;
  - runtime profile example;
  - personal map node template;
  - daily note template;
  - agent audit template;
  - operator run audit template;
  - generated idea template;
  - experiment template;
  - feature filter template;
  - synthesis note example.
- `core_export/reports/latest/core-export-dry-run-report.json` regenerated.
- `core_export/reports/latest/previews/` regenerated with 56 rendered previews.
- `core_export/reports/latest/manual-preview-review-candidate-completeness-2026-05-01.md` created.
- `core_export/reports/latest/core-export-feature-completion-tracker-2026-05-01.md` created.
- `core_export/reports/latest/runtime-handoff-core-export-candidate-completeness-2026-05-01.md` created.

Validation result:

```text
manifest_include_count 56
inventory_expected 56
expanded_dry_run_ok True
candidate_count 56
preview_count 56
preview_scanner_blocking_count 0
verify_report_ok True
missing_previews []
hash_mismatches []
scratch_target_exists False
seed_export_git_absent True
```

No local export update, Git initialization, commit, remote, push, publication, canonical promotion, or manual private-file copy occurred.

Current feature status:

```text
PARTIAL / DRY-RUN VERIFIED / NOT READY FOR GIT INIT
```

The feature is not done until manual review, license decision, public ignore policy, approved local export update, verify-export, and separate Git-init approval are complete or explicitly deferred by the operator.

## 12. 2026-05-01 Runtime Registration Checklist Pass

Codex added the final runtime-onboarding convenience artifact requested after
operator inspection of the local Core export:

- `core_export/templates/New-Runtime-Registration-Checklist.core.md` added.
- `core_export/export_manifest.yaml` expanded from 56 to 57 candidates.
- `core_export/core_candidate_inventory.yaml` updated to version 0.3.
- `core_export/reports/latest/core-export-dry-run-report.json` regenerated.
- rendered previews regenerated with 57 candidates.
- `core_export/reports/latest/manual-preview-review-runtime-registration-checklist-local-export-staging-2026-05-01.md` created.
- existing `%USERPROFILE%\Documents\chaseos-core` target updated through the guarded `--update-existing` export path.

Validation result:

```text
manifest_include_count 57
inventory_expected 57
dry_run_ok True
candidate_count 57
preview_count 57
preview_scanner_blocking_count 0
export_ok True
verify_export_ok True
verified_file_count 57
missing_files []
hash_mismatches []
export_scanner_blocking_count 0
git_initialized False
publication_performed False
```

This pass did not initialize Git, commit, add a remote, push, publish,
canonical-promote, decide a license, or add a public ignore policy.

Current feature status:

```text
LOCAL EXPORT VERIFIED / GIT INIT NOT APPROVED
```

Next safe step:

```text
Operator may inspect the 57-file local Core export. License, public ignore policy,
and Git init remain separate future approval gates.
```

---

Graph links: [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Agent-Activity-Index]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Autonomous-Operator-Runtime]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[ChaseOS-Gate]] · [[Vault-Map]]
