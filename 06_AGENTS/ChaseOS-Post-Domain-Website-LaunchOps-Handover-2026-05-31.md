---
title: ChaseOS Post-Domain Website, Hosting, Admin, and LaunchOps Handover
created: 2026-05-31
updated: 2026-05-31
status: REPO-READY STRATEGY / IMPLEMENTATION HANDOVER
type: launch-ops-handover
scope: post-domain purchase, chaseos.systems website plan, hosting architecture, waitlist, admin panel, safety checks, repo update prompt, public docs alignment, GitHub/social launch readiness
primary_domain: chaseos.systems
premium_fallback_domain: chaseos.ai
operator_assumption: chaseos.systems purchased or in immediate purchase flow
recommended_repo_path: 06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md
must_read_with:
  - 06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
  - 06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
  - 06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
  - ChaseOS-V1-Release-Cutline.md
  - Feature-Register.md
  - PROJECT_FOUNDATION.md
  - README.md
  - ROADMAP.md
---

> **Domain override note (2026-05-31):** This document contains historical `chaseos.systems` primary-domain assumptions. It is superseded by `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md`: current primary is `https://chaseos.ai`; `chaseos.systems` is optional future secondary/alias only. Preserve non-domain strategy context, but do not use this file as current domain truth.

# ChaseOS Post-Domain Website, Hosting, Admin, and LaunchOps Handover

> This is the third repo-ready handover in the ChaseOS launch strategy sequence. It assumes the operator has selected **`chaseos.systems`** as the primary public launch domain and now needs the repository, website, waitlist, public docs, safety checks, and launch operations to align around that decision.

This document is not a fresh strategy. It is a **post-domain execution layer** for the two prior strategy handovers:

1. `ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md`
2. `ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md`

The job now is to move from strategy to launch infrastructure.

---

## 0. Executive decision

The public domain is now:

```text
https://chaseos.systems
```

The product remains:

```text
ChaseOS
```

The main app remains:

```text
ChaseOS Studio
```

The marketplace/ecosystem layer remains:

```text
Chaser Forge
```

The future hosted runtime layer should be called, conservatively:

```text
Managed Agents
```

The name **Chaser Agent** may be used later if the product family is ready, but it should not confuse V1. V1 ships ChaseOS Studio plus the local-first governed control plane. Managed Agents / Chaser Agent is post-V1 or waitlist-facing.

The premium fallback domain is:

```text
chaseos.ai
```

Operating rule:

```text
Do not buy chaseos.ai just because it is nice.
Buy it after traction or if the operator decides the price is trivial.
```

Recommended trigger:

```text
Buy chaseos.ai after any one of:
- 50 qualified waitlist signups;
- 10 serious beta applicants;
- 3 paid setup-sprint / pilot conversations;
- meaningful public traction;
- credible risk of someone else taking it.
```

---

## 1. Core launch doctrine

### 1.1 Product identity

Use this as the public identity:

```text
ChaseOS is the local-first AI operating system for builders running real projects with agents.
```

Expanded:

```text
ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.
```

Everyday version:

```text
ChaseOS is where your AI work stops being scattered.
It keeps your project memory, agents, workflows, approvals, and outputs connected in one private system.
```

Technical version:

```text
ChaseOS is a local-first AI operating system and agent control plane for source intelligence, knowledge graphs, runtime orchestration, governed writeback, approval-gated execution, workflow packs, and auditable agent operation.
```

### 1.2 Why `.systems` is now correct

`chaseos.systems` fits better than a generic app or AI-wrapper domain because ChaseOS is not only an app and not only an AI product. It is a system of systems:

```text
local-first AI operating system
source intelligence system
knowledge graph
agent control plane
runtime governance layer
workflow-pack substrate
approval and audit system
Forge marketplace
future managed-agent infrastructure
```

The domain structure should communicate that ChaseOS is an operating platform, not a small utility.

### 1.3 The central product thesis

```text
Studio drives adoption.
Forge externalizes supply.
Standards capture makes packs, approvals, agents, graph objects, and outcomes ChaseOS-native.
Data moat compounds locally first and globally only through opt-in aggregate signals.
Managed agents monetize reliability.
Credits monetize convenience.
Teams and enterprise monetize governance.
```

---

## 2. Repo alignment after domain purchase

Once `chaseos.systems` is purchased, the repository should stop treating the domain as undecided.

### 2.1 Replace old assumptions

Replace or qualify old assumptions such as:

```text
chaseos.ai is the assumed primary domain
chaseos.com is the ideal redirect
getchaseos.com is a fallback
chaseos.dev is a public product option
```

with:

```text
chaseos.systems is the selected primary public domain.
chaseos.ai is a traction-triggered premium redirect/fallback.
No get/try/use-prefixed domains should be used.
chaseos.dev is not the public product domain.
```

### 2.2 Expected docs to update

Repo-aware agents should audit and update where relevant:

```text
README.md
PROJECT_FOUNDATION.md
ROADMAP.md
NEXT-STEPS.md
SYSTEM-STATUS.md
ChaseOS-V1-Release-Cutline.md
Feature-Register.md
Feature-Fit-Register.md
06_AGENTS/ChaseOS-Product-Identity-and-Wedge.md
06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
06_AGENTS/Chaser-Forge-Feature-Family.md
docs/features/chaser_forge_mvp_extension_install_contract.md
docs/website/* if present
docs/brand/* if present
docs/standards/* if present
docs/forge/* if present
```

Do not blindly rewrite all docs. Apply targeted changes only.

---

## 3. Website structure for `chaseos.systems`

Use path-based pages first. Subdomains can come later.

### 3.1 V1 public pages

Required:

```text
/                  homepage
/studio            ChaseOS Studio product page
/forge             Chaser Forge marketplace/preview page
/standards         pack/runtime/approval/graph standards page
/open-core         open-core / source-available / commercial split
/pricing           Free, Pro, Teams, Forge, Managed Agents preview
/download          download / install / early-access instructions
/docs              documentation hub
/waitlist          beta waitlist
/privacy           privacy/local-first promise
/security          security, responsible disclosure, trust boundaries
/roadmap           honest roadmap/status
/support           help/support/contact
/terms             site terms
```

Recommended soon after:

```text
/creators          creator and pack-builder page
/submit-pack       Chaser Forge pack submission waitlist
/marketplace-terms creator/premium-pack terms placeholder
/license           license posture page
/status            hosted service status placeholder
/changelog         public release notes
/admin             protected internal admin panel, not public nav
```

### 3.2 Path vs subdomain rule

V1 should use:

```text
chaseos.systems/forge
chaseos.systems/docs
chaseos.systems/standards
```

Do not use subdomains until the infrastructure is real.

Future subdomains:

```text
forge.chaseos.systems
api.chaseos.systems
account.chaseos.systems
status.chaseos.systems
docs.chaseos.systems
```

Subdomains should be introduced only when there is a distinct service boundary.

---

## 4. Hosting recommendation

### 4.1 Best immediate route

Use a simple static/mostly-static site for V1.

Recommended stack:

```text
Frontend: Astro, Next.js static export, Vite/React, or simple HTML/CSS if speed matters
Hosting: Cloudflare Pages or Vercel
Waitlist backend: Tally/Fillout first, or Supabase if building native forms
Email: Resend / Buttondown / ConvertKit / Beehiiv depending on newsletter strategy
Admin: Supabase table + protected admin page if native forms are used
Payments: Stripe later, not needed for first waitlist
```

### 4.2 Cloudflare Pages route

Recommended if the operator wants DNS, hosting, security, redirects, and future edge/serverless tooling under one roof.

Why:

```text
- Works well with a domain like chaseos.systems.
- Supports Git-based deployment or direct upload.
- Can host static marketing pages and `/forge/index.json`.
- Can later use Pages Functions / Workers for lightweight backend endpoints.
- Can add redirects and security headers early.
```

Suggested use:

```text
Cloudflare registrar/DNS if the domain is held there, or point nameservers to Cloudflare.
Create Cloudflare Pages project from GitHub.
Deploy website directory.
Add custom domain chaseos.systems.
Redirect www.chaseos.systems -> chaseos.systems.
Add security headers and cache rules.
Host /forge/index.json as static file first.
```

### 4.3 Vercel route

Recommended if the website is built in Next.js and the team wants fast frontend iteration.

Why:

```text
- Very fast frontend deployment.
- GitHub-based previews are easy.
- Good if Claude/Codex generates Next.js pages.
- Good for marketing site + simple API routes.
```

Suggested use:

```text
Vercel for frontend.
Cloudflare only for DNS/security if desired.
Supabase for database/auth/admin.
```

### 4.4 My preferred setup

For ChaseOS V1:

```text
Cloudflare DNS + Cloudflare Pages for first public site.
Supabase only if native waitlist/admin is being built.
Stripe only after pricing/licensing flow is ready.
```

Reason:

```text
The first website is mostly trust, waitlist, docs, Forge preview, and static pages.
It does not need heavy backend infrastructure.
Do not overbuild account/licensing before proving demand.
```

---

## 5. Waitlist system

### 5.1 V0 waitlist: fastest path

Use a form tool first if speed matters.

Acceptable:

```text
Tally
Fillout
Typeform
ConvertKit form
Beehiiv form
```

The V0 goal is not perfect infrastructure. It is to capture demand and learn who is interested.

### 5.2 V1 native waitlist

If building natively, use:

```text
Supabase table + form endpoint + protected admin page
```

Suggested table:

```sql
waitlist_signups (
  id uuid primary key,
  created_at timestamptz not null default now(),
  email text not null unique,
  name text,
  persona text,
  role text,
  company_or_project text,
  current_tools text,
  biggest_pain text,
  use_case text,
  os_platform text,
  wants_studio_beta boolean default false,
  wants_forge_creator_access boolean default false,
  wants_managed_agents boolean default false,
  willing_to_pay text,
  consent_marketing boolean not null default false,
  consent_research_contact boolean not null default false,
  source text,
  utm_source text,
  utm_medium text,
  utm_campaign text,
  status text default 'new',
  notes text
)
```

Status values:

```text
new
qualified
invite_ready
invited
onboarded
creator_candidate
team_candidate
enterprise_candidate
not_fit
```

### 5.3 Waitlist form questions

Keep the public form short, but capture useful market data.

Minimum:

```text
Email
Name
What best describes you? [AI builder, founder, developer, creator-builder, researcher, team lead, other]
What tools are you currently using? [ChatGPT, Claude, Codex, Cursor, Obsidian, Notion, GitHub, agents, other]
What is the biggest problem ChaseOS could solve for you?
Which are you interested in? [Studio beta, Forge creator access, managed agents, setup sprint]
Would you pay for this if it solved the problem? [No / maybe / £19-mo / £49-mo / team / services]
Can we contact you for beta/research? [yes/no]
```

### 5.4 Qualification rule

A qualified signup is someone who has:

```text
- real AI-native workflow pain;
- uses multiple AI/project tools now;
- wants Studio beta, Forge creator access, or managed-agent future;
- gives a clear use case;
- agrees to be contacted;
- optionally expresses willingness to pay or join a setup sprint.
```

The `50 signups` trigger for buying `chaseos.ai` should mean **50 qualified signups**, not 50 random emails.

---

## 6. Admin panel strategy

### 6.1 What the admin panel is

The admin panel is not ChaseOS Studio. It is the website/business admin surface for the public launch site.

It manages:

```text
waitlist signups
beta applicants
creator submissions
pack suggestions
support messages
invite status
manual notes
future licenses/entitlements
future runtime-credit balances
future account status
```

It must not manage:

```text
users' private local vaults
users' local graphs
users' local API keys
users' private project memory
users' local runtime logs
```

### 6.2 Admin panel V0

Do not overbuild it.

V0 admin can be:

```text
Supabase dashboard
Airtable/Notion table
or a simple protected `/admin` page
```

V0 actions:

```text
View signups
Filter by persona/status
Mark qualified
Mark invited
Export CSV
View creator submissions
Add private notes
```

### 6.3 Admin panel V1

A protected `/admin` page can include:

```text
Dashboard metrics
Waitlist table
Signup detail page
Creator submissions table
Pack suggestions table
Beta invite queue
Support inbox
Manual email action checklist
Export/download
Admin audit log
```

Admin roles:

```text
owner
admin
support
reviewer
read_only
```

Security boundaries:

```text
Require auth.
Require allowlisted admin emails.
Use Row Level Security if Supabase.
No raw secrets in browser.
No provider API keys exposed.
No local-vault data uploaded.
No hidden production sends without explicit admin action.
```

---

## 7. Forge public index after domain purchase

The official domain unlocks the next Chaser Forge milestone.

Current target:

```text
https://chaseos.systems/forge/index.json
```

V1 page:

```text
https://chaseos.systems/forge
```

V1 static assets:

```text
/forge/index.json
/forge/packs/<pack-id>/manifest.json
/forge/packs/<pack-id>/README.md
/forge/packs/<pack-id>/preview.png or screenshots later
```

### 7.1 What Forge can claim at V1

Allowed:

```text
Chaser Forge is the upcoming marketplace for ChaseOS workflow packs, operating kits, extensions, and agent presets.
Local/governed Forge support already exists in ChaseOS.
The public index is launching as a static preview first.
Creators can join the waitlist or submit pack ideas.
Premium marketplace, payments, licenses, and live remote install remain future.
```

Do not claim:

```text
Live paid marketplace exists.
Untrusted third-party exchange is live.
Payment/license mutation exists.
Remote fetch/install is automatically trusted.
Packs can bypass Gate/Approval.
```

### 7.2 Pack submission waitlist

Create:

```text
/creators
/submit-pack
```

Submission fields:

```text
Creator name
Email
Pack name
Pack category
Target user
Problem solved
What ChaseOS capability it uses
Expected price [free / paid / certified / managed]
Does it need browser/API/external sends?
Does it need secrets?
Does it mutate files?
Does it need managed runtime?
Demo link or description
Consent to be contacted
```

Creator categories:

```text
Founder/Startup packs
Content ops packs
Ecommerce/reselling packs
Research packs
Developer/operator packs
Education/study packs
Agent governance packs
Business ops packs
```

---

## 8. Legal, privacy, and trust pages

V1 must include at least draft-level legal/trust pages before serious public traffic.

Required:

```text
/privacy
/terms
/security
/open-core
/license
```

### 8.1 Privacy page must say

```text
ChaseOS is local-first.
Your local ChaseOS project memory and graph remain on your machine unless you explicitly choose to share/export/upload something.
The waitlist collects only the information you submit.
Optional telemetry/benchmarking must be opt-in.
Managed agents/cloud features are future or separate services.
Do not upload secrets, private keys, trading credentials, personal financial data, health records, or highly sensitive material through website forms.
```

### 8.2 Security page must say

```text
ChaseOS is designed around local-first control, approval boundaries, source provenance, and governed runtime execution.
External sends/uploads/payments/browser actions are not silently executed.
Certain features are preview/upcoming and remain disabled or approval-gated until proven.
A responsible disclosure contact will be provided.
```

### 8.3 Terms page must say

```text
Early access / beta software.
No warranty.
AI outputs may be wrong.
User remains responsible for actions taken with generated outputs.
No financial, legal, medical, or professional advice.
Marketplace and managed-agent features may be preview/future.
```

### 8.4 Open-core page must say

```text
Open where trust matters.
Commercial where reliability, hosted convenience, premium packs, marketplace distribution, managed runtime, collaboration, and support matter.
```

Avoid calling commercially restricted code “open-source.” Use accurate terms:

```text
open-source
source-available
open-core
commercial source
proprietary
creator-owned commercial pack
```

---

## 9. Hosting/DNS checklist

After domain purchase:

```text
1. Confirm registrar ownership.
2. Enable WHOIS/RDAP privacy where available.
3. Decide DNS provider: registrar DNS or Cloudflare DNS.
4. If using Cloudflare, set nameservers.
5. Add apex domain to hosting provider.
6. Add www redirect.
7. Add HTTPS/cert automation.
8. Add security headers.
9. Add robots.txt and sitemap.xml.
10. Add humans.txt and security.txt later.
11. Add favicon/social preview images.
12. Add email domain only when needed.
13. Add SPF/DKIM/DMARC before sending emails from the domain.
14. Add status page placeholder if hosted services exist.
15. Keep admin URLs protected and unlinked from public nav.
```

Recommended initial DNS pattern:

```text
@       -> website host
www     -> redirect to apex
```

Future DNS:

```text
forge   -> future marketplace service or static subdomain
api     -> future account/licensing/credits/runtime APIs
account -> future account portal
status  -> future status page
```

---

## 10. Launch page copy skeleton

### 10.1 Homepage hero

```text
Human intent.
Agentic execution.
Private control.

ChaseOS is the local-first AI operating system for builders running real projects with agents.

Turn scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

[Join the early access waitlist]
[Explore ChaseOS Studio]
```

### 10.2 Problem section

```text
AI work is scattered.

Your project context lives in ChatGPT, Claude, Codex, Cursor, Obsidian, GitHub, browser tabs, notes, logs, and half-finished workflows.
Every agent needs re-briefing. Every output gets lost. Every risky action needs manual checking. Every project starts again from zero.

ChaseOS gives the work one system.
```

### 10.3 What it connects

```text
Projects
Sources
Agents
Runtimes
Knowledge graph
Workflow packs
Approvals
Outputs
Audit trails
```

### 10.4 Core promise

```text
Run agents against real projects without losing context or control.
```

### 10.5 Trust section

```text
Local-first by default.
Provider-agnostic.
Approval-gated.
Inspectable graph.
No silent external actions.
```

### 10.6 Forge section

```text
Chaser Forge is the marketplace for ChaseOS operating kits.

Discover workflow packs, extensions, templates, and agent presets for startup work, content ops, research, ecommerce, developer workflows, and governed automation.

Forge launches as a preview first. Payments, premium licensing, and managed packs arrive later.
```

### 10.7 Managed agents section

```text
Managed Agents are the future hosted runtime layer for teams and builders who do not want to self-host long-running agent work.

For V1, ChaseOS remains local-first. Managed runtime is waitlist/upcoming.
```

---

## 11. Pricing page posture

V1 pricing can be public but marked as early.

Recommended:

```text
Free / Local Starter — £0
Pro Builder — target £19/month
Teams — planned
Forge Creator Packs — free and paid packs; ChaseOS 9% platform fee on paid packs once marketplace payments exist
Managed Agents — upcoming / waitlist
Setup Sprint — early-access service offer
Enterprise / Private Deployment — contact
```

### 11.1 Do not charge for local ownership

Do not make users pay to access their own local graph or local memory. Monetize:

```text
premium workflow packs
managed convenience
hosted services
runtime credits
support
team controls
private deployment
marketplace distribution
certification
```

### 11.2 Runtime credits

Future product structure:

```text
BYOK: bring your own provider keys for control.
ChaseOS credits: top up for convenience.
Managed Agents: pay for reliability, monitoring, queues, and hosted runtime execution.
```

Do not launch credits before billing, limits, abuse controls, usage accounting, and refund policy are defined.

---

## 12. Safety / clearance checklist

This is not legal advice. It is a practical minimum launch checklist.

### 12.1 Domain ownership

Check:

```text
ICANN Lookup / RDAP for chaseos.systems
Registrar dashboard ownership
Nameservers
DNSSEC if enabled
Renewal date
Auto-renew on
Registrar account 2FA on
Recovery email secure
```

### 12.2 Trademark / naming sweep

Search at minimum:

```text
UK IPO:
- ChaseOS
- Chase OS
- ChaserOS
- Chaser OS
- Chaser Forge
- Chaser Agent

USPTO:
- ChaseOS
- Chase OS
- ChaserOS
- Chaser OS
- Chaser Forge
- Chaser Agent

EUIPO / WIPO optional if planning broader international launch.
```

Also search the open web for:

```text
"ChaseOS"
"Chase OS"
"ChaserOS"
"Chaser OS"
"Chaser Forge"
"Chaser Agent"
"chaseos.systems"
```

### 12.3 Company / brand conflict

Do not use `Chaser Systems` as umbrella brand if it conflicts with an active existing company/site. The product is ChaseOS; the public domain is `chaseos.systems`.

Check:

```text
Companies House company-name search
Google/web exact match
GitHub org/user availability
X/Twitter handle
YouTube handle
LinkedIn page
Discord community/server name
Reddit community name
npm scope
PyPI package
DockerHub org
```

### 12.4 Public-claims safety

Before publishing, verify no public page says:

```text
fully autonomous company operator today
unrestricted browser automation today
live paid marketplace today
payment/license mutation live today
managed agents live today
enterprise-ready today
external sends/uploads happen without approval
private local graph is uploaded by default
```

---

## 13. GitHub / public repo plan

### 13.1 Immediate GitHub plan

Before publicizing GitHub:

```text
Run secret scan.
Run private path scan.
Run personal-data scan.
Run README cleanup.
Make Core/Personal split clear.
Ensure public repo contains ChaseOS Core / Studio / standards / examples only.
Keep private operator instance out of public repo.
```

### 13.2 GitHub surfaces

Potential future org/repos:

```text
github.com/chaseos/chaseos            main public repo if org available
github.com/chaseos/chaseos-standards  schemas/manifests/contracts
github.com/chaseos/forge-packs        sample/free packs
github.com/chaseos/docs               docs if split
github.com/chaseos/chaser-agent       future runtime harness if public
```

If `chaseos` org/name is unavailable:

```text
Use a clean alternative under the existing personal/org account first.
Do not choose a tacky name just for GitHub.
```

### 13.3 README public link

Once the domain is live, public README should include:

```text
Website: https://chaseos.systems
Waitlist: https://chaseos.systems/waitlist
Docs: https://chaseos.systems/docs
Forge preview: https://chaseos.systems/forge
```

---

## 14. Launch sequence

### Phase 0 — Domain secured

```text
Buy chaseos.systems.
Enable registrar 2FA and auto-renew.
Run RDAP/ownership check.
Run trademark/web/company name sweep.
Create this handover in repo.
Update strategy docs from domain-deferred to domain-selected.
```

### Phase 1 — Static site + waitlist

```text
Create landing page.
Create waitlist form.
Create privacy/terms/security/open-core placeholders.
Create /forge preview page.
Create /standards page.
Deploy to chaseos.systems.
Collect waitlist signups.
```

### Phase 2 — Repo/docs alignment

```text
Update README.
Update PROJECT_FOUNDATION.
Update ROADMAP.
Update V1 Release Cutline.
Update NEXT-STEPS.
Update Feature-Register / Feature-Fit only if status actually changes.
Add docs/website, docs/brand, docs/forge, docs/standards planning docs.
```

### Phase 3 — Forge public static index

```text
Generate public /forge/index.json.
Upload static index and sample packs.
Verify hash/digest if repo has existing Chaser Forge proof flow.
Update Chaser Forge status from domain-deferred to public static index pending/live depending on proof.
Do not enable paid marketplace yet.
```

### Phase 4 — Demo video + distribution

```text
Record demo: ChaseOS uses its graph, Studio, agents, approvals, and Forge preview to launch ChaseOS.
Publish launch thread/post.
Drive users to waitlist.
Track signups and qualitative use cases.
```

### Phase 5 — Admin / beta operations

```text
Build protected admin if native waitlist exists.
Tag qualified users.
Invite first beta users.
Collect feedback.
Identify first pack creators.
```

### Phase 6 — Paid tests

```text
Offer setup sprint.
Offer Pro waitlist.
Offer Forge creator beta.
Do not implement billing until offer/pain is proven.
```

---

## 15. What to ask Codex/Hermes to do

The agent should not guess. It should read all strategy handovers, then perform a bounded repo alignment pass.

The expected output is:

```text
1. domain/public website docs updated;
2. README/Foundation/Roadmap aligned;
3. Chaser Forge domain-deferred status updated carefully;
4. website plan/docs created;
5. no overclaims;
6. no live external deployment without operator action;
7. build log + documentation history created.
```

---

# 16. Master Codex / Hermes / Claude prompt

Paste this after placing all three handovers into the repo.

```text
We are continuing ChaseOS / ChaserOS development after the operator selected and purchased, or is in the process of purchasing, the primary public launch domain:

https://chaseos.systems

This is not a fresh project.
Do not restart ChaseOS.
Do not rename ChaseOS.
Do not shrink ChaseOS into Startup Validation.
Do not create a new disconnected website/app without auditing current repo structure first.
Do not overclaim live marketplace, browser automation, payment, license, managed-agent, external-send, or enterprise capability.

==================================================
PASS NAME
==================================================

ChaseOS Post-Domain Launch Alignment + Website/Waitlist/Admin Readiness Pass

==================================================
READ FIRST
==================================================

Read these strategy handovers first if present:

1. 06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
2. 06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
3. 06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
4. 06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md

Then read canonical repo docs:

- README.md
- PROJECT_FOUNDATION.md
- ROADMAP.md
- NEXT-STEPS.md
- SYSTEM-STATUS.md
- ChaseOS-V1-Release-Cutline.md
- Feature-Register.md
- Feature-Fit-Register.md if present
- 06_AGENTS/Chaser-Forge-Feature-Family.md if present
- docs/features/chaser_forge_mvp_extension_install_contract.md if present
- docs/website/* if present
- docs/brand/* if present
- docs/standards/* if present
- docs/forge/* if present
- runtime/forge/* relevant docs or implementation notes
- runtime/studio/* relevant website/Forge/admin surfaces if present

==================================================
CORE DECISIONS TO ADOPT
==================================================

Adopt these decisions unless direct repo evidence requires a narrower statement:

1. Primary public domain is `https://chaseos.systems`.
2. `chaseos.ai` is now a traction-triggered premium redirect/fallback, not the assumed primary.
3. Product name remains ChaseOS.
4. App name remains ChaseOS Studio.
5. Marketplace/ecosystem layer remains Chaser Forge.
6. Future hosted runtime layer should be called Managed Agents in V1-facing copy; Chaser Agent can remain a future/internal product-family name.
7. Do not use get/try/use-prefixed domains.
8. Do not use chaseos.dev as the public product domain.
9. Do not use Chaser Systems as umbrella brand.
10. Path-based pages come before subdomains.
11. V1 public site should launch as landing + waitlist + docs + Forge preview + standards/open-core/legal pages.
12. Do not implement payments/licensing/managed agents inside this pass unless already supported by verified repo contracts.

==================================================
PRODUCT LANGUAGE TO INSTALL
==================================================

Primary:

ChaseOS is the local-first AI operating system for builders running real projects with agents.

Expanded:

ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

Everyday:

ChaseOS is where your AI work stops being scattered. It keeps your project memory, agents, workflows, approvals, and outputs connected in one private system.

Technical:

ChaseOS is a local-first AI operating system and agent control plane for source intelligence, knowledge graphs, runtime orchestration, governed writeback, approval-gated execution, workflow packs, and auditable agent operation.

Avoid:

- AI Startup Validation OS as primary identity;
- Obsidian template as primary identity;
- generic chatbot wrapper;
- fully autonomous company operator today;
- arbitrary authenticated browser automation today;
- live paid marketplace today;
- managed agents live today unless proven.

==================================================
TASKS
==================================================

JOB 1 — Strategy file placement check

Confirm these handovers exist in 06_AGENTS/ or equivalent:

- ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
- ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
- ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
- ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md

If any are missing, report which are missing and continue with available context only.

JOB 2 — Domain assumption cleanup

Search the repo for old domain assumptions:

- chaseos.ai as primary
- chaseos.com as required
- chaseos.app as fallback primary
- chaseos.dev as public product domain
- getchaseos.com / trychaseos.com / usechaseos.com
- Chaser Systems as umbrella brand

Update only where relevant.

New canonical statement:

`chaseos.systems` is the selected primary launch domain. `chaseos.ai` is a traction-triggered premium fallback/redirect.

JOB 3 — Public website docs

Create or update documentation under the nearest existing convention. If no convention exists, create:

- docs/website/chaseos_systems_site_map.md
- docs/website/chaseos_systems_page_copy.md
- docs/website/chaseos_waitlist_data_model.md
- docs/website/chaseos_admin_panel_spec.md
- docs/website/chaseos_hosting_deployment_checklist.md
- docs/website/chaseos_public_launch_checklist.md

The site map must include at minimum:

- /
- /studio
- /forge
- /standards
- /open-core
- /pricing
- /download
- /docs
- /waitlist
- /privacy
- /security
- /roadmap
- /support
- /terms
- /creators
- /submit-pack
- /status placeholder
- /admin protected internal surface, not public nav

JOB 4 — Website implementation audit

Check whether the repo already has a website/frontend app.

If it exists:
- document where it is;
- update route plan only if safe;
- do not add duplicate website infrastructure.

If it does not exist:
- create a documentation-level implementation plan only;
- recommend a follow-up pass to create the website app;
- do not create a large new app unless explicitly requested.

Recommended V1 stack:
- static/mostly-static website;
- Cloudflare Pages or Vercel;
- waitlist via form tool first or Supabase if native;
- admin V0 through Supabase dashboard or protected admin page;
- payments deferred;
- managed agents deferred.

JOB 5 — Chaser Forge public index readiness

Update Chaser Forge docs/status carefully.

Domain status should become:

`domain selected: chaseos.systems`

But do not claim live hosted fetch unless the public static index exists and has been verified.

Target public index:

https://chaseos.systems/forge/index.json

Allowed V1 claim:

Chaser Forge is launching as a public static preview / creator waitlist first.

Blocked claims:

- paid marketplace live;
- untrusted third-party exchange live;
- payment/license mutation live;
- remote install automatically trusted;
- packs bypass Gate/Approval.

JOB 6 — Admin panel spec

Create/update admin spec with these boundaries:

Admin panel manages:
- waitlist signups;
- beta applicants;
- creator submissions;
- pack suggestions;
- support messages;
- invite status;
- manual notes;
- future licenses/entitlements;
- future credit balances.

Admin panel must not manage:
- users' private local vaults;
- local graphs;
- local API keys;
- local runtime logs;
- private project memory.

JOB 7 — Waitlist spec

Create/update waitlist data model and form questions.

Required fields:
- email;
- name optional;
- persona;
- current tools;
- biggest pain;
- use case;
- interest type;
- willingness to pay;
- consent to contact;
- source/UTM.

Define qualified signup criteria.

JOB 8 — Legal/trust page drafts

Create documentation-level draft copy for:

- privacy;
- terms;
- security;
- open-core/license;
- marketplace terms placeholder.

Keep these as draft/non-lawyer reviewed unless legal counsel reviews them.

JOB 9 — README/Foundation/Roadmap alignment

Update README, PROJECT_FOUNDATION, ROADMAP, NEXT-STEPS, and V1 cutline only where needed.

Must preserve repo truth:
- local-first;
- Core/Personal split;
- Obsidian is substrate, not product identity;
- Studio is product interface direction;
- Chaser Forge current local/governed status;
- live marketplace fetch/payment blocked unless proven;
- Approval/Gate boundaries;
- no overclaiming.

JOB 10 — Safety checks file

Create:

- docs/brand/chaseos_domain_brand_safety_checklist.md

Include checks for:
- domain/RDAP ownership;
- registrar 2FA and auto-renew;
- UK IPO trademark search;
- USPTO trademark search;
- Companies House name search;
- GitHub org/name;
- X/YouTube/LinkedIn/Discord/Reddit handles;
- npm/PyPI/DockerHub namespaces;
- public exact-web search;
- no conflict with Chaser Systems as umbrella brand.

JOB 11 — Build log and documentation history

Create:
- build log;
- documentation-history note;
- update Build-Logs-Index.md;
- update Documentation-History-Index.md.

If those indexes do not exist, report missing and create notes in the closest existing log convention.

==================================================
DO NOT DO
==================================================

Do not:
- deploy externally;
- call registrar APIs;
- mutate DNS;
- create Stripe products;
- send emails;
- upload public files;
- execute browser automation;
- add a full account/licensing backend unless requested;
- add live marketplace payments;
- claim managed agents are live;
- claim full autonomous company operation;
- claim arbitrary authenticated browser automation;
- upload private vault data;
- expose secrets;
- rewrite broad repo docs unnecessarily.

==================================================
VERIFICATION
==================================================

After changes:

1. grep for stale domain assumptions;
2. verify `chaseos.systems` appears in public website/docs strategy;
3. verify `chaseos.ai` appears only as fallback/redirect/traction-triggered premium domain;
4. verify no get/try/use-prefixed domain remains as recommendation;
5. verify no public docs overclaim current automation/payment/managed-agent capability;
6. verify Chaser Forge status is domain-selected but not falsely live if index is not public;
7. verify waitlist/admin specs do not imply access to user local vaults;
8. verify legal pages are marked draft if not lawyer-reviewed;
9. run existing tests only if implementation files changed;
10. run docs/grep checks for secrets/private paths if public-facing files changed.

==================================================
FINAL HANDOVER MUST LIST
==================================================

1. Files read.
2. Files created.
3. Files modified.
4. Domain assumptions found and changed.
5. Final domain strategy adopted.
6. Website pages specified.
7. Hosting recommendation adopted.
8. Waitlist model adopted.
9. Admin panel boundary adopted.
10. Chaser Forge status after this pass.
11. Public index target.
12. Safety checks created.
13. README/Foundation/Roadmap changes.
14. Feature-Register/Feature-Fit changes, if any.
15. Build log path.
16. Documentation-history note path.
17. Tests/verification performed.
18. Remaining blockers before public site launch.
19. Recommended next implementation pass.
20. Exact follow-up prompt for building the website if not built in this pass.

Execute the bounded repo-alignment and documentation pass now.
```

---

## 17. Follow-up website implementation prompt

Use this only after the repo-alignment pass confirms whether a website app already exists.

```text
We are now implementing the first public ChaseOS website for:

https://chaseos.systems

Before writing code, inspect the repo for an existing website/frontend app.

If a website app exists, extend it.
If no website app exists, create the smallest viable static/mostly-static site using the repo’s preferred frontend conventions.
Do not create an oversized SaaS backend.
Do not add payments, licensing, managed agents, or live marketplace transactions.

Minimum pages:
- /
- /studio
- /forge
- /standards
- /open-core
- /pricing
- /download
- /docs
- /waitlist
- /privacy
- /security
- /roadmap
- /support
- /terms
- /creators
- /submit-pack

Optional protected page:
- /admin, only if a native waitlist backend exists; otherwise admin remains external via form tool/Supabase dashboard.

Use this product copy:

ChaseOS is the local-first AI operating system for builders running real projects with agents.

ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

Primary CTA:
Join early access.

Secondary CTA:
Explore ChaseOS Studio.

Build requirements:
- responsive layout;
- basic SEO metadata;
- OpenGraph image placeholder;
- waitlist form or external waitlist embed/link;
- Forge preview section;
- Standards page with pack/runtime/approval/graph standards summary;
- Open-core page with open-source/source-available/commercial distinction;
- Pricing page with Free, Pro £19/month target, Teams planned, Forge 9% fee future, Managed Agents upcoming;
- Legal pages as draft placeholders;
- No analytics beyond privacy-respecting basic analytics unless approved;
- No secret values;
- No external sends unless explicit operator-provided endpoint exists.

Deploy target:
Cloudflare Pages or Vercel. Do not perform deployment inside this pass unless the operator explicitly provides credentials and approval.

Final handover must list:
- exact app path;
- pages created;
- components created;
- waitlist mechanism;
- build command;
- local preview command;
- deployment instructions;
- remaining DNS steps;
- remaining legal/trust steps;
- remaining admin/backend steps.
```

---

## 18. Final doctrine

After the domain is purchased, the launch strategy becomes practical:

```text
ChaseOS is no longer only a repo and not yet a broad SaaS.
It is moving into a public product layer at chaseos.systems.

The first website should explain the system, collect serious waitlist demand, expose Forge and standards early, and preserve the local-first trust promise.

Do not overbuild.
Do not overclaim.
Do not wait for every future capability.
Ship the truthful public surface, then let the waitlist and demo pull the roadmap forward.
```

