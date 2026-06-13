# ChaseOS Multi-Repo Operating Model + Promotion Bridge Handover
Date: 2026-05-31  
Primary domain: https://chaseos.ai  
Release posture: ChaseOS Studio Early Access  
Status: Repo-operating-model handover for Hermes/Codex

## 0. Why this document exists

ChaseOS now has to operate across multiple workspaces/repositories without leaking private vault data, build logs, personal notes, secrets, local paths, or unfinished internal strategy into public-facing surfaces.

The key correction:

**ChaseOS Core, chaseos_Obsidian, and chaseos-web are not the same thing.**

They should be connected by a deliberate promotion workflow, not by bulk copying or uncontrolled syncing.

## 1. Repository/workspace roles

### 1.1 `chaseos_Obsidian` — private operating vault / internal command memory

This is the private internal workspace.

It may contain:

- personal and project context,
- internal strategy,
- build logs,
- raw handovers,
- Kanban history,
- agent notes,
- internal launch planning,
- private research,
- references to local files,
- private workflow memories,
- non-public docs.

It should **not** be treated as the public product repository.

It should **not** be pushed public.

It should **not** be bulk-synced into ChaseOS Core.

It can remain the “operator truth” and internal control memory.

### 1.2 `chaseos-core` — product/core repository

This is the actual product/code repository for ChaseOS Core / Studio / runtime / app logic.

It should contain:

- product code,
- product architecture docs,
- public-safe README,
- public-safe core docs,
- source intelligence implementation,
- Studio implementation,
- graph implementation,
- runtime/AOR/Gate implementation,
- mission/workflow pack implementation,
- tests,
- packaging/release scripts,
- product-safe examples,
- release notes,
- public-safe docs.

It should **not** contain:

- private vault content,
- raw personal build logs,
- raw ChatGPT/Hermes/Codex transcripts,
- secrets,
- API keys,
- local system paths,
- personal notes,
- unredacted user data,
- private business plans that are not meant for GitHub,
- monetization documents that should stay internal,
- unfinished strategy that contradicts public messaging.

Initial posture:

- private GitHub repository,
- not public,
- no public release/download until V1 hardening is complete,
- no `ChaseOS.exe` public download until scanned/tested/approved.

### 1.3 `chaseos-web` — public website / waitlist / docs shell

Local path known:

```text
%USERPROFILE%\Documents\Projects\chaseos-web
```

This is the website repository for:

```text
https://chaseos.ai
```

It should contain:

- homepage,
- waitlist,
- Studio page,
- Forge preview page,
- `/forge/index.json`,
- standards pages,
- open-core page,
- pricing placeholder,
- docs shell,
- download placeholder,
- privacy,
- security,
- roadmap,
- support,
- creators,
- submit-pack,
- admin stub/protected admin,
- brand/design assets,
- public-safe marketing copy,
- launch video/page copy.

It should **not** contain:

- ChaseOS Core source code,
- full private docs,
- private build logs,
- secrets,
- API keys,
- raw vault content,
- `ChaseOS.exe` embedded directly in repo,
- hidden/private launch strategy.

## 2. Answer to the key question: “Can we bring things from chaseos_Obsidian into chaseos-core normally?”

Yes, but not by dumping the vault into the product repo.

Use a **promotion bridge**.

The private vault can generate/promote clean product artifacts into the core repo, but every transfer needs:

1. source location,
2. target repo/path,
3. reason for promotion,
4. safety classification,
5. private-data check,
6. secret/path check,
7. human approval if sensitive,
8. commit message,
9. audit note.

## 3. Promotion bridge model

### 3.1 Recommended private outbox in `chaseos_Obsidian`

Create:

```text
99_PROMOTION_OUTBOX/
└── core/
    └── <YYYY-MM-DD>_<slug>/
        ├── promotion_manifest.md
        ├── files/
        ├── review_notes.md
        └── approval.md
```

Alternative if ChaseOS uses different naming conventions:

```text
07_LOGS/Promotion-Outbox/Core/
```

### 3.2 Recommended intake path in `chaseos-core`

Create:

```text
06_AGENTS/imports/
└── <YYYY-MM-DD>_<slug>/
    ├── promotion_manifest.md
    └── review_result.md
```

or, if `06_AGENTS` should stay architecture-focused:

```text
docs/imports/
```

### 3.3 Promotion manifest fields

Every promoted artifact should have:

```yaml
promotion_id:
date:
source_workspace: chaseos_Obsidian
source_path:
target_repository: chaseos-core
target_path:
artifact_type: code | doc | template | prompt | workflow | asset | config | test | release
sensitivity: public-safe | internal-safe | private | blocked
contains_personal_data: yes | no | unknown
contains_secrets: yes | no | unknown
contains_local_paths: yes | no | unknown
requires_human_review: yes | no
reason_for_promotion:
expected_change:
tests_required:
reviewer:
decision: pending | approved | rejected | needs_redaction
```

### 3.4 Promotion rules

Allowed to promote:

- sanitized architecture docs,
- product-safe docs,
- implementation code,
- tests,
- clean templates,
- public-safe examples,
- specs that do not leak private strategy,
- release notes after review.

Requires review/redaction:

- build logs,
- strategy docs,
- marketing docs,
- agent transcripts,
- user-specific workflows,
- research docs,
- anything containing local paths,
- anything with API/provider references,
- anything mentioning private projects.

Blocked from direct promotion:

- secrets,
- `.env`,
- credentials,
- private API keys,
- tokens,
- personal vault content,
- raw user data,
- local database files,
- private build logs,
- raw unredacted chat transcripts,
- private financial details,
- private monetization details not meant for GitHub.

## 4. Recommended Git structure

### 4.1 `chaseos-core`

Branches:

```text
main        = stable private baseline / release candidate
develop     = active integration
feature/*   = implementation features
docs/*      = documentation updates
release/*   = V1 release hardening
hotfix/*    = urgent fixes
```

Initial steps:

```text
1. backup local folder
2. git init if missing
3. add .gitignore
4. run secret/path scan
5. baseline commit
6. connect private GitHub remote
7. push private
8. protect main if possible
```

Do not make public.

### 4.2 `chaseos-web`

Branches:

```text
main        = production site for chaseos.ai
develop     = active site development
feature/*   = page/feature work
preview/*   = Cloudflare preview deployments
```

Initial public posture:

- private repo while designing,
- Cloudflare Pages connected after site is safe,
- public site can go live before ChaseOS Core is downloadable,
- `/download` remains early-access/waitlist-only.

## 5. How to keep development sane

### 5.1 Do not develop product code inside the vault forever

If code is currently being edited inside `chaseos_Obsidian`, transition gradually:

1. identify product code folders,
2. copy only product code into `chaseos-core`,
3. confirm build/test paths,
4. use the product repo as code source of truth,
5. keep private notes/build logs in the vault.

The vault can still direct the work, but the code should live in the product repo.

### 5.2 Keep brand docs mostly in `chaseos-web`

Brand/design docs are mostly website/public-facing context.

Put brand assets and style docs in:

```text
chaseos-web/
├── 06_AGENTS/brand/
├── docs/brand/
└── src/content/brand/
```

Only copy brand docs into `chaseos-core` if they affect the product UI/Studio.

### 5.3 Keep internal strategy in `chaseos_Obsidian`

The full strategy memory can stay private.

Public-safe excerpts can be promoted into:

```text
chaseos-web/src/content/
chaseos-web/docs/
chaseos-core/docs/
```

## 6. GitHub use now

Use GitHub for:

- private backup/version control,
- branches,
- PR-style review even if solo,
- issue tracking / project board if useful,
- releases later,
- security scanning,
- public repo only after cleanup.

Do not use GitHub yet for:

- public downloads,
- public core repo,
- public marketplace repo,
- public agent repo,
unless the relevant repo has passed the public-readiness checklist.

When ChaseOS is ready for release, GitHub Releases can package software releases and attach binary files/release notes for download; GitHub describes releases as deployable software iterations that can include release notes and binary files. Do not use releases for public `.exe` until V1 is approved.

## 7. Public/private boundary

### Public-safe now

- chaseos.ai website,
- waitlist,
- positioning,
- high-level docs,
- standards previews,
- Forge preview,
- open-core philosophy,
- roadmap with honest status.

### Private until approved

- ChaseOS Core implementation,
- local vault,
- detailed build logs,
- internal agent transcripts,
- raw strategy docs,
- monetization implementation,
- managed agent implementation,
- secrets/config,
- release binaries.

## 8. Immediate next actions

### For Hermes

1. Create/reconcile multi-repo Kanban.
2. Define public/private boundaries.
3. Create promotion bridge policy.
4. Create product-core GitHub readiness checklist.
5. Create web-repo launch checklist.
6. Assign Codex implementation tasks separately for core and web.

### For Codex Core

1. Initialize or inspect Git.
2. Create `.gitignore`.
3. Run/prepare secret scan and path scan.
4. Create private baseline report.
5. Create promotion intake flow.
6. Do not publish or expose `.exe`.

### For Codex Web

1. Build `chaseos-web` site.
2. Implement waitlist/admin stub.
3. Implement Forge preview.
4. Implement standards preview.
5. Connect to Cloudflare only after human DNS/deployment approval.

## 9. Doctrine

ChaseOS Core is the product.  
chaseos_Obsidian is the private operating memory.  
chaseos-web is the public launch surface.  

Do not mix them by accident.