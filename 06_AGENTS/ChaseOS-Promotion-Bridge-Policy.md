---
title: ChaseOS Promotion Bridge Policy
created: 2026-05-31
runtime: hermes-optimus
status: ACTIVE / POLICY / HUMAN REVIEW REQUIRED FOR SENSITIVE PROMOTIONS
type: promotion-bridge-policy
primary_domain: https://chaseos.ai
---

# ChaseOS Promotion Bridge Policy

## 1. Purpose

This policy prevents accidental leakage between the private ChaseOS operating vault, the private product/core repo, and the public website repo.

The core correction is:

- `chaseos_Obsidian` is private operator memory.
- `chaseos-core` is the private product/core repository.
- `chaseos-web` is the public website repository for `https://chaseos.ai`.

Artifacts move by explicit promotion, not by bulk sync.

## 2. Workspace/repository roles

### 2.1 `chaseos_Obsidian` — private operator memory

The vault may contain:

- internal strategy;
- private build logs;
- raw handovers;
- agent notes;
- personal/project context;
- local paths;
- private workflow memory;
- raw research;
- launch planning;
- non-public docs.

It must not be pushed public or bulk-copied into `chaseos-core` or `chaseos-web`.

### 2.2 `chaseos-core` — product/core repository

`chaseos-core` is the product source-of-truth after initialization. Its initial posture is GitHub-private.

It may contain:

- product code;
- product-safe architecture docs;
- tests;
- packaging/release scripts;
- public-safe examples;
- sanitized import manifests;
- release notes after review.

It must not contain:

- raw vault content;
- private build logs;
- raw transcripts;
- secrets/tokens/API keys;
- local databases;
- personal notes;
- private strategy not intended for GitHub;
- public download assets before V1 gate.

### 2.3 `chaseos-web` — public site repo

`chaseos-web` is the public website/waitlist/docs/Forge preview/standards/open-core/pricing/privacy/security/admin-stub repo.

Target domain: `https://chaseos.ai`.

It may contain:

- website pages and components;
- public-safe copy;
- waitlist UI and safe endpoint/stub;
- protected/disabled admin stub;
- static Forge preview index;
- public standards examples;
- public-safe screenshots/demo fixtures;
- privacy/security/terms pages.

It must not contain:

- core source dumps;
- raw private docs;
- private build logs;
- secrets/API keys;
- waitlist PII in public files;
- embedded `ChaseOS.exe` or installer assets before V1 approval;
- hidden private strategy.

## 3. Promotion model

Every artifact promoted out of `chaseos_Obsidian` must have a manifest and review trail.

Recommended private outbox in the vault:

```text
99_PROMOTION_OUTBOX/
└── core/
    └── <YYYY-MM-DD>_<slug>/
        ├── promotion_manifest.md
        ├── files/
        ├── review_notes.md
        └── approval.md
```

Alternative if existing ChaseOS conventions prefer logs:

```text
07_LOGS/Promotion-Outbox/Core/
```

Recommended core intake path:

```text
06_AGENTS/imports/
└── <YYYY-MM-DD>_<slug>/
    ├── promotion_manifest.md
    └── review_result.md
```

Alternative:

```text
docs/imports/
```

Recommended web intake path:

```text
docs/imports/
└── <YYYY-MM-DD>_<slug>/
    ├── promotion_manifest.md
    └── public_copy_review.md
```

## 4. Import manifest requirements

Every promoted artifact must include:

```yaml
promotion_id:
date:
source_workspace: chaseos_Obsidian
source_path:
target_repository: chaseos-core | chaseos-web
target_path:
artifact_type: code | doc | template | prompt | workflow | asset | config | test | release | copy | brand
sensitivity: public-safe | internal-safe | private | blocked
contains_personal_data: yes | no | unknown
contains_secrets: yes | no | unknown
contains_local_paths: yes | no | unknown
contains_private_strategy: yes | no | unknown
requires_human_review: yes | no
reason_for_promotion:
expected_change:
tests_required:
secret_scan_result: pass | fail | not_run
path_scan_result: pass | fail | not_run
public_claims_review: pass | fail | not_applicable
reviewer:
decision: pending | approved | rejected | needs_redaction
commit_message:
audit_note_path:
```

Minimum review notes:

- why this artifact belongs in the target repo;
- what was removed/redacted;
- what scans were run;
- what public claims changed;
- who approved sensitive promotion;
- what tests/smokes must pass after import.

## 5. Allowed promotions

Allowed after manifest and review:

- sanitized architecture docs;
- product-safe README/foundation excerpts;
- public-safe diagrams;
- implementation code;
- tests;
- clean templates;
- public-safe examples;
- standards schemas/examples;
- release notes after review;
- brand/docs copy intended for `chaseos-web`;
- demo fixtures proven to contain no private data.

## 6. Requires review/redaction

Requires human or Hermes review before import:

- build logs;
- strategy docs;
- marketing docs;
- agent transcripts;
- raw handovers;
- user-specific workflows;
- research docs;
- anything containing local paths;
- provider/API references;
- docs mentioning private projects;
- screenshots/video captures;
- public claims about unfinished features;
- monetization/pricing language.

## 7. Blocked artifacts

Never directly promote:

- `.env` files;
- credentials;
- API keys/tokens;
- private SSH/GitHub/auth material;
- raw personal vault content;
- raw user/client data;
- local databases;
- binary cache files;
- raw unredacted chat transcripts;
- private build logs;
- private financial details;
- waitlist PII;
- payment/customer records;
- unreviewed screenshots from the private vault;
- public downloads/installers before V1 release gate;
- private monetization details not intended for GitHub/public web.

## 8. Human review triggers

Human review is required when promotion:

- changes public product positioning;
- changes pricing, licensing, payment, marketplace, or revenue claims;
- touches privacy/security/legal pages;
- includes screenshots/video/assets from the private environment;
- includes any local path or personal-context example before redaction;
- moves strategy from private vault to public website;
- adds/updates public download/release claims;
- creates/connects GitHub repos;
- changes repo visibility;
- deploys or mutates DNS/Cloudflare.

## 9. Build logs stay private

Build logs are private operating records by default.

They may be summarized into public-safe release notes only after:

1. selecting a narrow claim;
2. removing private paths, internal agent notes, raw error dumps, and secret-adjacent text;
3. converting internal implementation details into user-facing language;
4. running secret/path/no-overclaim scans;
5. recording the source build-log path in the manifest without copying the whole log.

Do not place raw `07_LOGS/Build-Logs/`, raw `07_LOGS/Agent-Activity/`, or raw `99_ARCHIVE/Documentation-History/` entries into `chaseos-core` or `chaseos-web`.

## 10. Public-safe docs extraction

Public-safe docs must:

- use `https://chaseos.ai` as the primary domain;
- distinguish current vs preview vs planned vs blocked/future;
- avoid personal examples and local filesystem paths;
- avoid implying broad autonomous browser/shell/provider/payment authority;
- keep `ChaseOS` as product/platform, `ChaseOS Studio` as app/control panel, `Chaser Forge` as marketplace/ecosystem preview, and Managed Agents / Chaser Agent as future/post-V1 unless proven otherwise;
- label Forge as static preview until marketplace/payment/install infrastructure is real;
- label download as waitlist/early-access until V1 release gate passes.

## 11. Brand docs into web repo

Brand/copy docs can move from vault to `chaseos-web` only as public-safe excerpts or rewritten copy.

Allowed web targets:

- homepage copy components;
- `/studio` page copy;
- `/forge` copy;
- `/standards` copy;
- `/open-core` explanation;
- `/pricing` planned-pricing preview;
- `/privacy`, `/security`, `/terms` baselines;
- launch video/public screenshot copy.

Blocked web targets:

- raw founder strategy;
- private financial/marketplace assumptions not intended for public readers;
- raw internal debate/history;
- private roadmap items not safe to announce;
- screenshots with private vault, usernames, local paths, Discord channels, tokens, or customer data.

## 12. Review workflow

1. Candidate selected in `chaseos_Obsidian`.
2. Promotion outbox folder created.
3. Manifest completed.
4. Secret/path/private-data/claims scans run.
5. Redactions performed.
6. Human review triggered if required.
7. Artifact imported to `chaseos-core` or `chaseos-web`.
8. Target repo tests/smokes run.
9. Import review result recorded.
10. Commit prepared with manifest reference.

## 13. No-go rules

- No bulk sync from vault to GitHub.
- No public repo visibility changes without human approval.
- No public download until V1 gate passes.
- No DNS/Cloudflare mutation by agents.
- No live payment/marketplace/runtime-credit activation.
- No email/social campaigns.
- No model/provider calls over waitlist PII.
- No browser automation for public launch tasks in this scheduled/daemon lane.
- No canonical ChaseOS truth promotion bypassing Gate/governance.
