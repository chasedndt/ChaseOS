> **Domain override note (2026-05-31):** This document contains historical `chaseos.systems` primary-domain assumptions. It is superseded by `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md`: current primary is `https://chaseos.ai`; `chaseos.systems` is optional future secondary/alias only. Preserve non-domain strategy context, but do not use this file as current domain truth.

# ChaseOS V1 Execution + Kanban + Hermes/Codex Handover

**Date:** 2026-05-31  
**Primary domain:** `chaseos.systems`  
**Release posture:** ChaseOS Studio Early Access  
**Purpose:** Give Hermes, Codex, Kanban, Agent Box, and any scheduled task runner a shared execution plan for getting ChaseOS V1 and the public launch site ready without reopening strategy or overclaiming capability.

---

## 0. Read this first

This handover assumes the following documents are already in the repo or will be added before this pass:

```text
06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md
```

This file is the **execution layer** on top of those strategy handovers.

Do not restart ChaseOS.  
Do not rebuild the whole architecture.  
Do not turn ChaseOS into only a website.  
Do not overclaim live automation, payments, managed agents, arbitrary browser control, or marketplace sales.  
Do not create duplicate subsystems if the repo already has them.

The immediate goal is:

```text
ChaseOS V1 safe + demo-ready
+
chaseos.systems early-access website live
+
waitlist/admin working
+
Forge preview credible
+
public docs/GitHub safe
```

---

## 1. Locked mental model

### Product

```text
ChaseOS
```

ChaseOS is the local-first AI operating system for builders running real projects with agents.

### App/interface

```text
ChaseOS Studio
```

Studio is the app / desktop command surface / human-facing interface.

### Public domain

```text
https://chaseos.systems
```

This is the selected primary public domain.

### Marketplace / ecosystem layer

```text
Chaser Forge
```

Forge is the workflow-pack / operating-kit / extension / standards ecosystem.

### Future hosted runtime layer

```text
Managed Agents / Chaser Agent
```

Future paid managed runtime infrastructure. Do not claim it is available unless the repo and hosted infrastructure prove it.

### Core positioning

```text
ChaseOS turns scattered AI chats, docs, repos, sources, agents, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.
```

### V1 release truth

```text
Early Access.
Honest capabilities.
Local-first trust.
No fake autonomy.
No fake marketplace payments.
No fake managed agents.
```

---

## 2. V1 priorities now locked

Prioritize these before anything else:

```text
1. local-first memory
2. knowledge graph visibility
3. source/project organization
4. Studio command surface
5. agent/runtime awareness
6. approval visibility
7. workflow/mission packs
8. Forge preview
9. honest blocked/pending states
10. safe public docs
11. chaseos.systems launch site
12. waitlist + admin view
13. demo fixture: ChaseOS uses ChaseOS to launch ChaseOS
```

Everything else is secondary.

Do not prioritize these before V1:

```text
- full marketplace payments
- Stripe Connect live marketplace flow
- paid pack payout automation
- full SaaS account system
- managed agents
- arbitrary live browser automation
- CRM mutation
- payment mutation
- enterprise/private deployment
- full teams product
- generic cloud sync
```

Those are roadmap lanes, not V1 blockers.

---

## 3. Agent roles

### Hermes role

Hermes should own:

```text
- strategy/doc truth sync
- README/project foundation/roadmap language
- website copy
- launch page copy
- public docs shape
- GitHub README/public repo narrative
- video scripts and demo narrative
- Chaser Forge positioning
- standards documentation language
- issue/Kanban decomposition
- final review against strategy/claims
```

Hermes should not silently change implementation authority, Gate policy, approval semantics, browser authority, credentials, or marketplace/payment assumptions.

### Codex role

Codex should own:

```text
- repo implementation changes
- tests
- website skeleton
- Cloudflare Pages/Functions compatible code if in scope
- waitlist form implementation
- admin route implementation if in scope
- D1/Supabase schema if approved
- Forge index JSON and validators if in scope
- Studio/Graph/V1 UI hardening
- build scripts and CI checks
- secret/path scans
- release smoke suite
```

Codex must respect Gate, Permission Matrix, protected-core rules, and current repo execution boundaries.

### Shared review

Both agents should cross-review:

```text
- overclaim risk
- public/private boundary
- open-core/source-available language
- Forge status
- domain assumptions
- waitlist/admin data handling
- V1 launch blockers
- demo safety
```

---

## 4. Kanban board structure

Create or update a Kanban board with these lanes:

```text
Backlog
Ready
In Progress - Hermes
In Progress - Codex
Blocked
Review
Approved
Done
Deferred / Future
```

Each card must include:

```text
ID
Title
Owner
Priority: P0 / P1 / P2 / Future
Area
Goal
Files likely touched
Acceptance criteria
Risks
External actions required: yes/no
Requires human approval: yes/no
Blocked by
Verification required
Final evidence/output
```

Recommended card ID prefixes:

```text
V1-CORE-*        ChaseOS V1 product readiness
WEB-*            chaseos.systems website
WAIT-*           waitlist/admin/data capture
FORGE-*          Chaser Forge preview/index/standards
DOCS-*           README/docs/public positioning
GH-*             GitHub/public repo readiness
DEMO-*           demo fixture/video proof
SEC-*            secrets/path/privacy/legal/safety
CRON-*           scheduled checks/jobs
PAY-*            payment/licensing future plan only
MGD-*            managed agents future plan only
```

---

## 5. Immediate P0 work packages

### P0 — V1 capability readiness sync

```text
ID: V1-CORE-001
Owner: Hermes + Codex
Priority: P0
Goal: Confirm actual V1 state and align it with public claims.
```

Tasks:

```text
- Read README.md, PROJECT_FOUNDATION.md, ROADMAP.md, NEXT-STEPS.md, SYSTEM-STATUS.md, Feature-Register.md, V1 Release Cutline.
- Confirm what is READY / PARTIAL / BLOCKED / FUTURE.
- Update docs so public claims match repo truth.
- Do not claim generic browser automation, payment mutation, marketplace sales, or managed agents if not proven.
```

Acceptance criteria:

```text
- Current/future claims separated.
- V1 pages and README do not overclaim.
- Every major V1 capability has a status.
- Every blocked/future capability has honest language.
```

---

### P0 — ChaseOS Studio V1 priorities

```text
ID: V1-CORE-002
Owner: Codex
Priority: P0
Goal: Ensure the product app demonstrates the correct V1 moat.
```

Prioritized surfaces:

```text
- Home / Command Center
- Graph / Knowledge Graph visibility
- Sources
- Projects
- Missions / Workflow Packs
- Runtimes / Agent awareness
- Approvals
- Forge Preview
- Settings / Privacy / Providers
- Logs / Audit
```

Acceptance criteria:

```text
- A user can understand ChaseOS without reading raw markdown.
- Graph/knowledge-box concept is visible.
- Runtime/agent state is visible without granting unsafe authority.
- Approvals show pending/blocked states honestly.
- Missions show workflow-pack direction.
- Forge preview shows ecosystem direction without claiming live payments.
```

---

### P0 — Website skeleton on chaseos.systems

```text
ID: WEB-001
Owner: Codex + Hermes
Priority: P0
Goal: Create the first public chaseos.systems website skeleton.
```

Recommended initial stack:

```text
Cloudflare DNS
Cloudflare Pages
Cloudflare Pages Functions for waitlist/admin endpoints if needed
Cloudflare D1 or Supabase for waitlist data
Cloudflare Turnstile for spam protection
Cloudflare Access for /admin protection
```

Do not add a full SaaS account system yet.

Minimum pages:

```text
/
/waitlist
/studio
/forge
/standards
/open-core
/pricing
/docs
/download
/privacy
/terms
/roadmap
/security
/support
```

Optional but useful:

```text
/creators
/submit-pack
/status
/changelog
```

Acceptance criteria:

```text
- Site builds locally.
- Site can deploy to Cloudflare Pages or a static hosting equivalent.
- Domain is referenced as chaseos.systems.
- Waitlist CTA exists.
- Privacy/local-first positioning is clear.
- Forge preview exists without fake payment claims.
- Standards page exists or is stubbed with truthful roadmap.
```

---

### P0 — Waitlist capture

```text
ID: WAIT-001
Owner: Codex
Priority: P0
Goal: Implement a real waitlist capture path.
```

Fields:

```text
email: required
name: optional
role: required
primary_use_case: required
current_ai_stack: optional
biggest_pain: required
interested_in_pro: boolean
interested_in_forge_creator: boolean
interested_in_setup_sprint: boolean
company_or_team_size: optional
source_channel: optional
consent_to_updates: required
created_at: auto
qualification_status: A/B/C/Creator/Team/Unreviewed
notes: admin-only
```

Spam protection:

```text
Cloudflare Turnstile or equivalent.
```

Acceptance criteria:

```text
- Email validation exists.
- Consent checkbox required.
- Turnstile or anti-spam gate exists before production.
- Data writes to approved storage only.
- No model/provider call runs on submitted PII.
- Admin can review/export entries.
```

---

### P0 — Admin panel boundary

```text
ID: WAIT-002
Owner: Codex
Priority: P0
Goal: Create minimal admin view or spec for waitlist review.
```

Admin should show:

```text
- total signups
- recent signups
- qualification status
- role/use case
- source channel
- creator interest
- team interest
- export CSV
- notes
- invite status
```

Admin must not include:

```text
- payments
- full user account management
- private ChaseOS user graph access
- production secrets
- raw provider keys
- arbitrary user data mutation
```

Recommended protection:

```text
Cloudflare Access for /admin if using Cloudflare.
```

Acceptance criteria:

```text
- /admin is not public.
- Admin auth boundary is documented.
- Admin actions are logged where possible.
- Export does not leak secrets.
```

---

### P0 — Forge preview + public index target

```text
ID: FORGE-001
Owner: Hermes + Codex
Priority: P0
Goal: Make Chaser Forge credible at V1 without pretending live payments exist.
```

Public target:

```text
https://chaseos.systems/forge/index.json
```

V1 Forge should include:

```text
- static marketplace/catalog page
- 3-5 example workflow packs
- pack manifest examples
- pack submission/waitlist CTA
- creator guidelines
- install/preview docs if safe
- public index JSON shape
- 9% future creator fee policy stated only if appropriate
```

Do not include:

```text
- fake live pack purchases
- Stripe Connect payouts
- automated paid-pack licensing
- unreviewed third-party packs
- pack code that mutates protected core
```

Acceptance criteria:

```text
- Forge preview communicates ecosystem direction.
- Public index JSON is valid if published.
- Pack manifests are documented.
- Creator submission flow exists or is stubbed.
- Payment/licensing is marked future/beta unless actually implemented.
```

---

### P0 — Safe public docs

```text
ID: DOCS-001
Owner: Hermes
Priority: P0
Goal: Make public docs trustworthy and safe.
```

Public docs should include:

```text
- What is ChaseOS?
- Local-first promise
- What data stays local
- What is optional/cloud/future
- Studio overview
- Knowledge graph overview
- Agents/runtimes overview
- Approvals and Gate overview
- Workflow packs / missions
- Forge preview
- Standards overview
- Install / download
- Open-core/source-available explanation
- Security and responsible disclosure
```

Docs must not reveal:

```text
- personal file paths
- private notes
- credentials
- internal-only build logs with sensitive data
- private project context
- internal prompt/system secrets
```

Acceptance criteria:

```text
- Docs link back to chaseos.systems.
- GitHub README can point to docs.
- Public claims are honest.
- Open-source/source-available language is precise.
```

---

### P0 — V1 demo fixture

```text
ID: DEMO-001
Owner: Hermes + Codex
Priority: P0
Goal: Prepare the demo where ChaseOS uses ChaseOS to launch ChaseOS.
```

Demo should show:

```text
1. ChaseOS Studio opens.
2. Project context is loaded.
3. Knowledge graph / Knowledge Boxes show project/source/agent/workflow links.
4. Sources and docs are organized.
5. Missions / workflow pack runs a launch or founder-mode mission.
6. Landing page copy / launch assets are generated.
7. Forge preview/index artifacts are shown.
8. Runtimes/agents are visible as bounded lanes.
9. Approval Center shows pending/blocked external actions.
10. Outputs write back locally.
11. Final handoff clarifies what is local, what is approval-only, and what is future.
```

Acceptance criteria:

```text
- Demo does not expose secrets or private paths.
- Demo proves the V1 moat: graph + memory + agents + approvals + workflows.
- Demo does not fake full browser automation or managed agents.
```

---

## 6. P1 work packages

### P1 — Settings / Providers / Privacy page in Studio

```text
ID: V1-CORE-003
Owner: Codex
Priority: P1
Goal: Make provider/privacy settings visible and honest.
```

Include:

```text
- local-first status
- provider key status without revealing secrets
- telemetry/benchmark opt-in status if applicable
- data/export/delete docs or local path references
- model/provider adapters summary
- blocked/future managed-agent status
```

Acceptance criteria:

```text
- Users can see whether they are using local/BYOK/managed routes.
- Secrets are never displayed.
- Future managed credits are not implied as active.
```

---

### P1 — Workflow/Mission Pack standards

```text
ID: FORGE-002
Owner: Hermes + Codex
Priority: P1
Goal: Define the minimum ChaseOS pack standard.
```

Minimum standards to document:

```text
chaseos.pack.json
chaseos.forge-index.json
chaseos.approval.json
chaseos.agent.json
chaseos.graph.json
chaseos.source.json
chaseos.outcome.json
```

Acceptance criteria:

```text
- Standards are public-doc ready.
- Example pack validates against manifest schema if validator exists.
- Standards are explicitly not a promise of live marketplace/payment support.
```

---

### P1 — Scheduled / cron jobs

```text
ID: CRON-001
Owner: Codex
Priority: P1
Goal: Define safe scheduled jobs for website and launch ops.
```

Safe scheduled jobs for V1:

```text
- daily waitlist summary generation
- weekly waitlist export snapshot
- daily Forge index validation
- daily public page smoke check
- weekly stale docs/domain assumption check
- weekly launch metrics summary
```

Do not schedule:

```text
- automatic user emails without explicit approval
- automatic social posts
- automatic browser actions
- automatic marketplace payouts
- automatic provider/model calls over PII
- automatic mutation of protected repo docs
```

Cloudflare Workers Cron Triggers are suitable for scheduled Worker jobs once the website stack uses Workers/Pages Functions. Use Wrangler-managed cron definitions if the Worker is Wrangler-managed.

Acceptance criteria:

```text
- Cron jobs are documented before deployment.
- Cron jobs run in UTC.
- Cron events/logging are available.
- No cron job touches secrets or sends external communications without approval.
```

---

### P1 — Website analytics without betraying local-first

```text
ID: WEB-002
Owner: Hermes + Codex
Priority: P1
Goal: Add minimal launch analytics.
```

Track:

```text
- page views
- waitlist conversion
- source_channel
- creator interest
- Pro interest
- setup sprint interest
- Forge interest
```

Avoid:

```text
- invasive tracking
- selling data
- hidden profiling
- mixing waitlist PII with product graph data
```

Acceptance criteria:

```text
- Analytics approach is disclosed in Privacy page.
- Waitlist PII is minimized.
- Product/private graph data remains local unless explicit opt-in exists.
```

---

### P1 — GitHub public safety prep

```text
ID: GH-001
Owner: Hermes + Codex
Priority: P1
Goal: Prepare public GitHub safely.
```

This is detailed in the separate video/GitHub handover, but the key requirement is:

```text
Never publish secrets, private paths, private user memory, internal credentials, or commercially sensitive unfinished monetization infrastructure.
```

Acceptance criteria:

```text
- README is public-safe.
- LICENSE / NOTICE / SECURITY / CONTRIBUTING exist or are intentionally deferred.
- Secret scan passes.
- Path scan passes.
- Public docs do not overclaim.
```

---

## 7. P2 / future work packages

### Future — Runtime credits

```text
ID: PAY-001
Owner: Hermes + Codex later
Priority: Future
Goal: Plan runtime credits/top-up but do not build unless approved.
```

Future model:

```text
BYOK for control.
ChaseOS credits for convenience.
Managed agents for reliability.
```

V1 action:

```text
- Pricing page may mention Pro/credits as upcoming.
- Do not collect payments unless legal/pricing/payment architecture is ready.
```

---

### Future — Stripe Connect marketplace

```text
ID: PAY-002
Owner: Codex later
Priority: Future
Goal: Marketplace payments and creator payouts.
```

Future model:

```text
Paid creator packs: 9% ChaseOS platform fee.
Certified packs: 12-15%.
Managed/runtime packs: 15-20% + runtime costs.
```

V1 action:

```text
- Keep as documented strategy.
- Maybe collect creator waitlist/submission interest.
- No live payouts.
```

---

### Future — Managed Agents

```text
ID: MGD-001
Owner: Codex later
Priority: Future
Goal: Hosted runtime workers for users who do not want to self-host.
```

Future requirements:

```text
- tenant isolation
- approved context snapshots only
- job queues
- policy/Gate enforcement
- logs/audit
- monitoring
- billing/credits
- human approval path
- no whole-vault upload by default
```

V1 action:

```text
- Mention as upcoming if desired.
- Do not imply availability.
```

---

## 8. Cloudflare launch stack guide

### Recommended first stack

```text
DNS: Cloudflare DNS
Static frontend: Cloudflare Pages
Dynamic waitlist/admin endpoints: Cloudflare Pages Functions
Database: Cloudflare D1 or Supabase
Spam protection: Cloudflare Turnstile
Admin protection: Cloudflare Access
Scheduled jobs: Cloudflare Workers Cron Triggers if/when needed
```

Cloudflare Pages supports deployment through Git providers, direct upload, or CLI, and Pages Functions can add server-side behavior without a dedicated server.

### DNS / Pages sequence

```text
1. Add chaseos.systems to Cloudflare.
2. Configure nameservers at registrar to Cloudflare nameservers.
3. Create Pages project.
4. Connect Git repo or direct upload.
5. Add apex custom domain: chaseos.systems.
6. Add www redirect if desired: www.chaseos.systems -> chaseos.systems.
7. Confirm HTTPS active.
8. Confirm /waitlist, /privacy, /terms, /forge, /docs routes.
```

### Pages routes

```text
/                      Homepage
/waitlist              Waitlist form
/studio                ChaseOS Studio product page
/forge                 Chaser Forge preview
/forge/index.json      Public Forge static index target
/standards             Standards overview
/open-core             Open-core/source-available explanation
/pricing               Free/Pro/Forge/Managed Agents roadmap pricing
/docs                  Docs landing
/download              Early access/download/install status
/privacy               Privacy/local-first promise
/terms                 Terms placeholder/legal baseline
/security              Security/responsible disclosure
/roadmap               Public roadmap
/support               Support/contact
/admin                 Protected admin view
```

### Waitlist API shape

```text
POST /api/waitlist
```

Request:

```json
{
  "email": "user@example.com",
  "name": "Optional",
  "role": "AI founder / developer / creator-builder / other",
  "primary_use_case": "string",
  "current_ai_stack": "string",
  "biggest_pain": "string",
  "interested_in_pro": true,
  "interested_in_forge_creator": false,
  "interested_in_setup_sprint": false,
  "company_or_team_size": "solo / 2-5 / 6-20 / 20+",
  "source_channel": "x / linkedin / reddit / github / direct / other",
  "consent_to_updates": true,
  "turnstile_token": "token"
}
```

Response:

```json
{
  "ok": true,
  "message": "You are on the ChaseOS early access list."
}
```

### Minimal D1 schema option

Use this only if D1 is selected.

```sql
CREATE TABLE IF NOT EXISTS waitlist_signups (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  role TEXT NOT NULL,
  primary_use_case TEXT NOT NULL,
  current_ai_stack TEXT,
  biggest_pain TEXT NOT NULL,
  interested_in_pro INTEGER DEFAULT 0,
  interested_in_forge_creator INTEGER DEFAULT 0,
  interested_in_setup_sprint INTEGER DEFAULT 0,
  company_or_team_size TEXT,
  source_channel TEXT,
  consent_to_updates INTEGER NOT NULL DEFAULT 0,
  qualification_status TEXT NOT NULL DEFAULT 'Unreviewed',
  invite_status TEXT NOT NULL DEFAULT 'Not invited',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS waitlist_notes (
  id TEXT PRIMARY KEY,
  signup_id TEXT NOT NULL,
  note TEXT NOT NULL,
  created_by TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(signup_id) REFERENCES waitlist_signups(id)
);

CREATE TABLE IF NOT EXISTS admin_events (
  id TEXT PRIMARY KEY,
  actor TEXT,
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);
```

### Admin API shape

```text
GET /api/admin/waitlist
PATCH /api/admin/waitlist/:id
GET /api/admin/export.csv
```

All admin endpoints must be protected.

### Turnstile rule

Every public form that writes data should verify a Turnstile token server-side before writing.

### Access rule

`/admin` should be behind Cloudflare Access or equivalent. Do not ship public admin.

---

## 9. Feature gates and claims

### Allowed current V1 claims if repo supports them

```text
local-first project/source memory
knowledge graph visibility
project/source organization
Studio command surface
runtime/agent awareness
approval visibility
mission/workflow-pack direction
Forge preview
safe docs
public waitlist
```

### Approval-only / preview claims

```text
browser workflows
external posting
site deployment
email sends
creator pack submissions
premium packs
runtime credits
managed agents
```

### Blocked unless specifically implemented and approved

```text
arbitrary authenticated browser control
LinkedIn scraping
auto-DMs
payment mutation
marketplace payouts
CRM mutation
provider calls over waitlist PII
automatic user emails without approval
whole-vault cloud upload by default
```

---

## 10. Testing and verification

### Website tests

```text
- homepage renders
- all public routes render
- 404 renders
- waitlist validation rejects missing required fields
- waitlist validation rejects invalid email
- waitlist requires consent
- waitlist verifies Turnstile before write in production mode
- duplicate email handled gracefully
- admin route protected
- export route protected
- /forge/index.json valid JSON
- privacy/terms/security pages exist
```

### Repo safety tests

```text
- secret scan
- path scan
- no personal local username/path leaks
- no provider keys in public docs
- no fake claims in README
- no marketplace payment claim unless implemented
- no managed agent claim unless implemented
```

### ChaseOS V1 tests

```text
- Studio starts
- graph view renders or status explains partial state
- source/project organization accessible
- runtime/agent awareness visible
- approval visibility surface works or is clearly partial
- mission/workflow pack preview visible
- Forge preview visible
- blocked/pending states displayed honestly
```

---

## 11. Human approval checkpoints

Require human approval before:

```text
- changing public domain/DNS
- deploying public site
- making repo public
- enabling payments
- emailing waitlist
- claiming managed agents are live
- publishing marketplace/Forge index publicly
- accepting paid pack submissions
- opening source code under a license
- changing licensing/open-core policy
- adding provider/model calls over waitlist data
- adding browser automation
```

---

## 12. Development sequence

Run in this order:

```text
1. Repo strategy alignment pass using four handovers + this file.
2. Create Kanban cards from this handover.
3. Audit V1 current state and blockers.
4. Website skeleton.
5. Waitlist + admin minimal backend.
6. Forge preview + static index shape.
7. Public docs skeleton.
8. Studio V1 prioritized polish.
9. Demo fixture.
10. Video/GitHub readiness pass.
11. Release smoke suite.
12. Human review.
13. Public site deploy.
14. Controlled early-access launch.
```

---

## 13. Suggested cron/scheduled jobs

Use scheduled jobs carefully. They are not a replacement for human approval or repo governance.

### V1-safe jobs

```text
CRON-001 Daily waitlist summary
- Runs once per day UTC.
- Counts new signups, A/B/C/Creator/Team status.
- Writes internal admin summary only.
- Does not email users automatically.

CRON-002 Weekly waitlist export snapshot
- Runs weekly.
- Exports CSV to approved private storage only.
- Does not publish.

CRON-003 Daily Forge index validation
- Validates /forge/index.json shape.
- Reports errors to admin/logs.
- Does not auto-publish new packs.

CRON-004 Public page smoke check
- Checks key routes return 200.
- Reports failures.
- Does not auto-edit site.

CRON-005 Weekly stale-claim scan
- Searches public docs for stale terms: chaseos.ai primary, franchise, full autonomous operator, live payments, live managed agents.
- Reports only.
```

### Not allowed for V1

```text
- automatic external emails
- automatic social posting
- automatic marketplace payouts
- automatic paid plan activation
- automatic browser sessions
- automatic model/provider calls using waitlist PII
- automatic protected-core mutation
```

---

## 14. Build log and writeback

Every pass must create/update:

```text
Build log
Documentation-history note
Build-Logs-Index.md if present
Documentation-History-Index.md if present
Feature-Register.md only if feature state changes
Feature-Fit-Register.md only if feature placement changes
NEXT-STEPS.md with current blockers and next tasks
```

---

## 15. Final handover required from agents

Hermes/Codex final output must list:

```text
1. files read
2. files created
3. files modified
4. Kanban cards created
5. current V1 readiness by priority area
6. website pages created/spec’d
7. waitlist backend status
8. admin panel status
9. Cloudflare setup status
10. Forge preview status
11. Forge public index status
12. public docs status
13. GitHub readiness status
14. demo fixture status
15. cron/scheduled jobs created/spec’d
16. tests added/updated
17. safety checks performed
18. overclaim risks found
19. blockers
20. human approval required next
21. exact build log path
22. exact documentation-history note path
```

---

## 16. Implementation wrapper prompt

Paste this into Hermes/Codex after providing the handovers:

```text
Read these handovers first:

1. 06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
2. 06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
3. 06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
4. 06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md
5. 06_AGENTS/ChaseOS-V1-Execution-Kanban-Hermes-Codex-Handover-2026-05-31.md

Then execute a bounded V1 readiness + public site launch preparation pass.

Primary launch domain is chaseos.systems.

Priorities:
- local-first memory
- knowledge graph visibility
- source/project organization
- Studio command surface
- agent/runtime awareness
- approval visibility
- workflow/mission packs
- Forge preview
- honest blocked/pending states
- safe public docs
- chaseos.systems landing/waitlist

Create or update Kanban/Agent Box tasks using the work packages in the V1 execution handover.

Hermes should own strategy/docs/copy/video/public narrative. Codex should own implementation/tests/site/waitlist/admin/Forge index where appropriate. Both must review overclaim risk.

Do not overclaim current capabilities.
Do not deploy externally without human approval.
Do not enable payments.
Do not make the repo public without human approval.
Do not create live marketplace payouts.
Do not create managed agents.
Do not add arbitrary browser automation.
Do not mutate DNS.
Do not send emails.
Do not process waitlist PII with model/provider calls.

If a feature is missing or partial, record it honestly as READY / PARTIAL / BLOCKED / FUTURE.

Create build log and documentation-history note. Update indexes if present.

Final handover must list files read, files created, files modified, Kanban cards created, tests performed, blockers, public-site status, V1 status, and human approvals required.
```
