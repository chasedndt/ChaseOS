---
title: ChaseOS Systems Domain Launch Alignment Handover
created: 2026-05-31
updated: 2026-05-31
status: OPERATOR DECISION / REPO ALIGNMENT HANDOVER
type: launch-strategy
scope: domain decision, public website structure, repo positioning updates, Chaser Forge domain linkage, waitlist, GitHub/social links, open-core wording, launch-safe claims
primary_domain: chaseos.systems
premium_fallback_domain: chaseos.ai
operator_decision: chaseos.systems selected as primary launch domain
links:
  - [[ChaseOS-Product-Positioning-and-Founder-Mode-Context]]
  - [[ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31]]
  - [[ChaseOS-Product-Strategy-Domain-Open-Core-Handover-2026-05-30]]
  - [[ChaseOS-V1-Release-Cutline]]
  - [[Feature-Register]]
  - [[Feature-Fit-Register]]
  - [[Chaser-Forge]]
  - [[Chaser-Forge-Feature-Family]]
  - [[PROJECT_FOUNDATION]]
  - [[README]]
  - [[ROADMAP]]
---

> **Domain override note (2026-05-31):** This document contains historical `chaseos.systems` primary-domain assumptions. It is superseded by `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md`: current primary is `https://chaseos.ai`; `chaseos.systems` is optional future secondary/alias only. Preserve non-domain strategy context, but do not use this file as current domain truth.

# ChaseOS Systems Domain Launch Alignment Handover

> This document updates the ChaseOS public-domain and launch strategy after the operator selected **`chaseos.systems`** as the primary domain.  
> It should be placed in the repo and used by Hermes / Codex / Claude as a repo-alignment document before any README, release-cutline, website, GitHub, social, or Chaser Forge domain updates are made.

---

## 0. Executive decision

The primary public domain for ChaseOS is now:

```text
https://chaseos.systems
```

The product name remains:

```text
ChaseOS
```

The main app remains:

```text
ChaseOS Studio
```

The marketplace / ecosystem layer remains:

```text
Chaser Forge
```

The future managed runtime / hosted agent layer remains:

```text
Managed Agents
```

or, when the product family is ready:

```text
Chaser Agent
```

The premium fallback domain is:

```text
chaseos.ai
```

But `chaseos.ai` should not be bought immediately unless the operator decides the cost is justified. The current operating rule is:

```text
Buy chaseos.ai after early waitlist proof, unless the price is trivial to the operator.
```

Suggested trigger:

```text
Buy chaseos.ai after any one of:
- 50 qualified waitlist signups,
- 10 serious beta applicants,
- 3 paid setup-sprint / pilot conversations,
- first meaningful public launch traction,
- or credible risk of someone else taking it.
```

The exact `.com` is unavailable and should not block launch.

---

## 1. Why `chaseos.systems` is the right primary domain

`chaseos.systems` is not a fallback. It is strategically coherent.

It fits ChaseOS better than a generic `.app` or tacky `get/try/use` domain because ChaseOS is not only an app. It is a system:

```text
local-first AI operating system
knowledge graph
agent control plane
runtime governance layer
workflow-pack substrate
approval and audit system
marketplace for operating kits
future managed-agent infrastructure
```

The `.systems` TLD supports the actual category:

```text
ChaseOS is a system of systems.
```

It can carry:

```text
ChaseOS Studio
Chaser Forge
ChaseOS Standards
ChaseOS Docs
ChaseOS Pricing
ChaseOS Download
ChaseOS Support
Managed Agents
Open-core pages
Marketplace terms
Creator submissions
Waitlist
```

It also avoids making ChaseOS look like a short-lived AI wrapper. `.ai` has category signal, but `.systems` has architecture signal.

Final brand interpretation:

```text
ChaseOS = product / platform / operating system
chaseos.systems = public home of the ChaseOS ecosystem
ChaseOS Studio = desktop command center
Chaser Forge = marketplace and standards layer
Managed Agents / Chaser Agent = future hosted runtime lane
```

---

## 2. Updated public product identity

### 2.1 Primary identity

Use this as the main product line:

```text
ChaseOS is the local-first AI operating system for builders running real projects with agents.
```

### 2.2 Expanded identity

```text
ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.
```

### 2.3 Technical identity

```text
ChaseOS is a local-first AI operating system and agent control plane for source intelligence, knowledge graphs, runtime orchestration, governed writeback, approval-gated execution, workflow packs, and auditable agent operation.
```

### 2.4 Everyday identity

```text
ChaseOS is where your AI work stops being scattered.
It keeps your project memory, agents, approvals, workflows, and outputs connected in one private system.
```

### 2.5 Website hero recommendation

```text
Human intent.
Agentic execution.
Private control.

ChaseOS is the local-first AI operating system for builders running real projects with agents.

Turn scattered chats, files, workflows, approvals, and outputs into one governed knowledge graph.
```

### 2.6 Shorter hero variant

```text
Run real projects with AI agents — without losing context or control.
```

### 2.7 Founder / builder-focused variant

```text
For AI-native builders who are tired of re-briefing agents, losing project context, and running workflows across scattered tools.
```

---

## 3. Updated domain structure

For V1, use path-based pages before subdomains.

### 3.1 Required V1 pages

```text
https://chaseos.systems/
https://chaseos.systems/studio
https://chaseos.systems/forge
https://chaseos.systems/standards
https://chaseos.systems/pricing
https://chaseos.systems/docs
https://chaseos.systems/open-core
https://chaseos.systems/download
https://chaseos.systems/privacy
https://chaseos.systems/security
https://chaseos.systems/waitlist
https://chaseos.systems/roadmap
https://chaseos.systems/support
https://chaseos.systems/terms
```

### 3.2 Important post-V1 pages

```text
https://chaseos.systems/creators
https://chaseos.systems/submit-pack
https://chaseos.systems/marketplace-terms
https://chaseos.systems/license
https://chaseos.systems/status
https://chaseos.systems/account
https://chaseos.systems/credits
https://chaseos.systems/agents
```

### 3.3 Chaser Forge public index route

The current Chaser Forge repo posture says live hosted fetch is domain-deferred. With the domain selected, the next practical target should be:

```text
https://chaseos.systems/forge/index.json
```

or:

```text
https://chaseos.systems/forge/registry/index.json
```

Recommended V1 path:

```text
https://chaseos.systems/forge/index.json
```

Use this as the public static Forge index route unless the existing Forge protocol already expects a different path.

Important boundary:

```text
Domain purchased does not automatically mean live Forge fetch is enabled.
```

The repo should move from:

```text
DOMAIN-DEFERRED
```

to:

```text
DOMAIN SELECTED / PUBLIC STATIC INDEX UPLOAD PENDING / FETCH STILL APPROVAL-GATED
```

Only after:

```text
- static index is generated,
- files are uploaded,
- URL is verified,
- digest matches local artifact,
- final approval packet is supplied,
- no external mutation occurs outside approved Forge path,
```

should the live hosted marketplace path be marked ready.

---

## 4. Subdomain roadmap

Do not rush subdomains during V1. Use paths first.

Later:

```text
studio.chaseos.systems
forge.chaseos.systems
docs.chaseos.systems
api.chaseos.systems
status.chaseos.systems
account.chaseos.systems
```

Recommended future use:

```text
studio.chaseos.systems -> hosted/account web shell if built
forge.chaseos.systems  -> public marketplace index/catalog
docs.chaseos.systems   -> developer docs and standards
api.chaseos.systems    -> licensing, accounts, credits, telemetry-opt-in, marketplace APIs
status.chaseos.systems -> hosted-service status page
```

But V1 should stay simple:

```text
chaseos.systems/studio
chaseos.systems/forge
chaseos.systems/docs
```

---

## 5. Domain safety posture

This document is not legal advice.

Current soft posture:

```text
chaseos.systems appears strategically safe enough to proceed as the selected domain,
subject to registrar confirmation and basic trademark checks.
```

Required checks before heavy public push:

```text
1. Registrar checkout confirms ownership.
2. ICANN / RDAP lookup confirms registration details after purchase.
3. GOV.UK trademark search for "ChaseOS", "Chase OS", "ChaserOS", "Chaser OS".
4. USPTO trademark search for the same terms.
5. Basic search-engine checks for exact phrase conflicts.
6. GitHub / npm / PyPI / package-name sweep if public developer packages will use the same names.
7. Company-name check if the operator intends to register a company under ChaseOS or similar.
```

Do not claim:

```text
"legally cleared"
```

until a proper mark search has been done.

Use:

```text
domain selected
domain purchased
public launch domain
```

not:

```text
trademark cleared
brand legally protected
```

---

## 6. What changes now that `chaseos.systems` is selected

### 6.1 Previous strategy files need updating

Older strategy files may still say:

```text
chaseos.ai primary
chaseos.com brand protection
getchaseos.com fallback
chaseos.app fallback
chaseos.dev fallback
```

Update them to:

```text
Primary domain: chaseos.systems
Premium AI fallback / future redirect: chaseos.ai
Exact .com: unavailable / not required for V1
App/dev/generic fallback routes: not primary
```

### 6.2 Keep ChaseOS as product name

Do not rename to:

```text
ChaserOS
Chaser Systems
Chaser Research
Chaser Studio
```

unless a future operator decision changes this.

Correct hierarchy:

```text
ChaseOS = platform/product
ChaseOS Studio = app
Chaser Forge = marketplace
Chaser Agent / Managed Agents = future runtime layer
Chaser Research = optional research/content arm only, not the main product
```

### 6.3 Do not host HermesAgent / OpenClaw as products

Hermes and OpenClaw may appear as:

```text
compatibility examples
internal runtime lanes
proof/runtime references
developer docs
```

They should not be presented as public products hosted under ChaseOS unless the operator explicitly decides that.

Correct wording:

```text
ChaseOS is designed to coordinate multiple runtimes and agents under one governed graph.
```

Avoid:

```text
ChaseOS sells HermesAgent and OpenClaw.
```

---

## 7. GitHub and public repo changes

### 7.1 GitHub website link

Once the holding page exists, GitHub profiles/repos should link to:

```text
https://chaseos.systems
```

### 7.2 Public repo README should contain

```text
Website: https://chaseos.systems
Status: V1 / Early Access / Developer Preview
```

### 7.3 Recommended public GitHub repo structure

If using a GitHub organization later:

```text
chaseos/chaseos
chaseos/chaseos-standards
chaseos/chaser-forge-packs
chaseos/chaseos-docs
chaseos/chaser-agent
```

If using a personal/org account first, still use the same conceptual naming.

### 7.4 What should be public early

Public early:

```text
README
docs/brand
docs/standards
example packs
free starter packs
Chaser Forge manifest examples
public roadmap
open-core philosophy
security/privacy notes
issue templates
contribution guidelines
```

Keep private or gated until ready:

```text
licensing backend
payment code
premium packs
account/credits implementation
managed agent infrastructure
security-sensitive implementation details
unhardened browser automation
secrets/configs/local paths
enterprise/private deployment assets
```

---

## 8. Website page plan

### 8.1 `/` Homepage

Goal:

```text
Explain ChaseOS in under 60 seconds.
Drive waitlist / early access signup.
Show local-first trust posture.
Show Studio, Forge, standards, and managed-agent roadmap without overclaiming.
```

Sections:

```text
Hero
Problem
Product explanation
How it works
Knowledge graph / memory
Studio
Forge
Standards
Open-core / local-first promise
Pricing preview
Waitlist CTA
FAQ
```

Hero draft:

```text
Human intent.
Agentic execution.
Private control.

ChaseOS is the local-first AI operating system for builders running real projects with agents.

It connects your chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.
```

Problem draft:

```text
AI work is scattered across chats, notes, repos, browser tabs, agents, and half-finished workflows.
Every new session needs re-briefing.
Every tool has its own memory.
Every agent acts without the full project graph.

ChaseOS gives the work one operating system.
```

CTA:

```text
Join the early access waitlist
```

or:

```text
Get ChaseOS Studio Early Access
```

### 8.2 `/studio`

Goal:

```text
Explain ChaseOS Studio as the app/control panel.
```

Positioning:

```text
ChaseOS Studio is the desktop command center for your AI operating system.
Manage project memory, agents, workflow packs, approvals, graph views, and runtime status from one local-first interface.
```

Include feature cards:

```text
Command Center
Knowledge Graph
Agent Control
Approvals
Workflow Packs
Forge Browser
Settings / Privacy / Providers
Logs / Audit
```

### 8.3 `/forge`

Goal:

```text
Explain Chaser Forge as the workflow-pack marketplace and ecosystem.
```

Positioning:

```text
Chaser Forge is the marketplace for ChaseOS workflow packs, templates, extensions, agent presets, and domain-specific operating kits.
```

V1 state:

```text
Forge launches first as a static preview, free starter pack index, and creator submission waitlist.
Paid packs, licenses, and automated marketplace transactions come later.
```

Include:

```text
Browse free packs
Submit a pack
Creator waitlist
Pack standards
9% creator marketplace fee planned for paid packs
Certification coming later
```

### 8.4 `/standards`

Goal:

```text
Start standards capture early.
```

Explain:

```text
ChaseOS standards define how packs, agents, approvals, graph nodes, source evidence, runtime handoffs, and workflow outcomes are packaged.
```

Starter standards:

```text
chaseos.pack.json
chaseos.forge-index.json
chaseos.agent.json
chaseos.approval.json
chaseos.graph.json
chaseos.source.json
chaseos.outcome.json
chaseos.entitlement.json
chaseos.managed-job.json
```

V1 state:

```text
Standards are early and subject to change.
```

### 8.5 `/pricing`

Goal:

```text
Show future monetization without forcing unfinished payment logic.
```

V1 pricing posture:

```text
Local Starter — free
Pro Builder — planned £19/month
Teams — planned
Forge paid packs — planned
Managed agents — waitlist / future
Enterprise/private deployment — contact
```

Do not activate fake subscriptions until account/licensing is built.

### 8.6 `/open-core`

Goal:

```text
Explain what is open, source-available, free, paid, and commercial.
```

Core language:

```text
Open where trust matters.
Paid where reliability, convenience, distribution, and scale matter.
```

### 8.7 `/download`

Goal:

```text
Give installation path once V1 is ready.
```

Until ready:

```text
Early access not public yet.
Join waitlist.
```

### 8.8 `/privacy`

Goal:

```text
Make local-first real.
```

Key promise:

```text
Your private graph stays yours.
```

Clarify:

```text
local storage
provider keys
BYOK
optional cloud/account
optional telemetry
optional anonymized aggregate signals
export/delete
no default private-vault extraction
```

### 8.9 `/security`

Goal:

```text
Explain safety boundaries.
```

Include:

```text
approval-gated actions
no silent external sends
no secret capture
no arbitrary browser automation in V1
local-first data
Gate/permissions
audit logs
responsible disclosure contact
```

### 8.10 `/waitlist`

Waitlist fields:

```text
Email
Name
Role
Use case
Current AI tools used
Main pain
Would you use locally, cloud, or both?
Interested in Forge packs?
Interested in managed agents?
Interested in creator/pack submission?
Consent checkbox
```

Segmentation tags:

```text
ai_builder
technical_founder
solo_builder
developer
creator_builder
agency
team
enterprise
forge_creator
managed_agent_interest
setup_sprint_interest
```

---

## 9. Waitlist launch rule

The waitlist is the proof mechanism for whether to buy `chaseos.ai`.

Recommended waitlist qualification system:

```text
Unqualified signup:
Email only.

Qualified signup:
Email + role + use case + tool stack + pain statement.

High-intent signup:
Qualified signup + asks for early access / setup / demo / pricing / pack creation / team use.

Commercially serious signup:
Asks about paid setup, team, managed agent, Forge pack, enterprise, or migration.
```

Trigger to buy `chaseos.ai`:

```text
50 qualified signups
or 10 high-intent signups
or 3 commercially serious signups
```

This makes the fallback domain purchase evidence-based.

---

## 10. DNS, hosting, and launch infrastructure checklist

### 10.1 DNS

Recommended registrar/DNS stack:

```text
Domain registered wherever purchased.
DNS managed by Cloudflare if possible.
```

Minimum records:

```text
A / CNAME for apex domain
CNAME for www
TXT for domain verification
MX if email is used
SPF
DKIM
DMARC
```

### 10.2 Hosting options

Fast V1 options:

```text
Vercel
Cloudflare Pages
Netlify
GitHub Pages
```

Recommended:

```text
Cloudflare Pages or Vercel
```

Reason:

```text
fast static launch
simple deploy previews
easy custom domain
good enough for landing/waitlist/docs
```

### 10.3 Email aliases

Create forwarding aliases:

```text
hello@chaseos.systems
support@chaseos.systems
security@chaseos.systems
privacy@chaseos.systems
creators@chaseos.systems
forge@chaseos.systems
legal@chaseos.systems
```

Use only the aliases needed immediately.

Minimum V1:

```text
hello@
support@
security@
privacy@
```

### 10.4 DMARC

Set DMARC even if using forwarding:

```text
_dmarc.chaseos.systems
```

Start with a safe monitoring policy:

```text
v=DMARC1; p=none; rua=mailto:security@chaseos.systems
```

Move to stricter policies after email is stable.

---

## 11. Chaser Forge domain update

### 11.1 New Forge domain status

Old status:

```text
domain-deferred
```

New status:

```text
official domain selected: chaseos.systems
public static index upload pending
live hosted fetch still approval-gated
payment/license mutation still blocked
```

### 11.2 Public static index target

Preferred:

```text
https://chaseos.systems/forge/index.json
```

Fallback if site routing requires:

```text
https://chaseos.systems/static/forge/index.json
```

or:

```text
https://chaseos.systems/forge/registry/index.json
```

### 11.3 V1 Forge copy

```text
Chaser Forge is the marketplace for ChaseOS operating kits.

Start with free workflow packs, examples, and a creator submission waitlist.
Paid packs, certification, licensing, and automatic installs are coming after the V1 trust layer is stable.
```

### 11.4 Creator submission CTA

```text
Build a ChaseOS pack
```

or:

```text
Submit a workflow pack
```

Fields:

```text
Name
Email
Pack idea
Target user
Problem solved
Free / paid / both
Requires external APIs?
Requires browser actions?
Requires secrets?
Expected outputs
License preference
```

Safety flags:

```text
finance/trading
health
legal
employment
payments
browser automation
external sends
credentials
children/minors
regulated data
```

---

## 12. Monetization references to install

### 12.1 Current monetization stack

```text
Free Local Starter
Pro Builder — planned £19/month
Runtime credits — future top-up / included allowance
Chaser Forge — 9% take on paid creator packs
Certified / managed packs — higher take-rate
Teams — post-V1
Managed Agents — future
Enterprise / private deployment — later
Setup sprints — early cashflow / case-study engine
```

### 12.2 Pricing page language

```text
Free to run locally.
Paid when you want maintained packs, account conveniences, managed runtime, team governance, or support.
```

### 12.3 Pro plan position

```text
Pro should not charge users to access their own local OS.
Pro should charge for convenience, premium workflow packs, updates, account/licensing, managed options, and future runtime credits.
```

### 12.4 Runtime credits

Public wording:

```text
Bring your own provider keys for maximum control, or use ChaseOS credits for convenience when managed runtime features become available.
```

Do not launch credits before:

```text
account layer
billing
usage metering
abuse limits
provider cost accounting
refund policy
terms
credit expiration rules
```

### 12.5 Forge take-rate

Public planned rule:

```text
Paid creator packs: 9% ChaseOS platform fee.
```

More complete internal structure:

```text
Free packs: 0%
Paid creator packs: 9%
Certified packs: 12–15%
Managed/runtime packs: 15–20% plus runtime usage
Enterprise/private packs: custom commercial terms
```

---

## 13. Open-core wording

Use precise language.

### 13.1 Do not say everything is open-source

Only use "open-source" where the license is genuinely open-source.

Use these categories:

```text
Open-source
Source-available
Commercial source
Free pack
Paid pack
Certified pack
Managed service
Enterprise/private deployment
```

### 13.2 Public principle

```text
Open where trust matters.
Paid where reliability, convenience, distribution, and scale matter.
```

### 13.3 Public explanation

```text
ChaseOS is local-first and inspectable where users need trust: local data, workflow manifests, approval contracts, pack standards, and example packs.

The business charges for premium workflow packs, hosted account services, managed runtimes, runtime credits, team governance, support, and enterprise/private deployment.
```

### 13.4 Suggested split

```text
Open-source:
- standards
- schemas
- validators
- example packs
- docs
- SDK examples

Source-available / open-core:
- ChaseOS Core
- Studio basic
- local graph/memory substrate
- trust-sensitive governance components

Commercial:
- hosted account/licensing
- runtime credits
- premium Studio features
- premium packs
- certification/review operations
- private Forge catalogs
- managed agents
- teams
- enterprise/private deployments
```

---

## 14. Public claims allowed now

Use these only if repo evidence supports them at the time of publication.

Allowed:

```text
local-first operating system for AI builders
source intelligence
structured memory
knowledge graph direction
governed writeback
approval-gated execution
provider-agnostic runtime architecture
ChaseOS Studio as product-facing interface
Chaser Forge as marketplace/extension path
static Forge publication/index path in progress
open-core/source-available strategy
privacy-first / local-first principles
early access / V1 / developer preview
```

Use with caution:

```text
managed agents
runtime credits
public marketplace payments
team collaboration
hosted account
cloud sync
browser automation
external posting
external sends
CRM/payment mutations
enterprise readiness
```

Blocked or future unless proven:

```text
fully autonomous company operator
arbitrary authenticated browser automation
live social posting
live email/DM sending
payment/license mutation
automatic Forge payment settlement
generic approval execution
unrestricted computer control
```

---

## 15. Repo update map

The following files should be checked and updated where appropriate.

### 15.1 Must update

```text
README.md
PROJECT_FOUNDATION.md
ROADMAP.md
NEXT-STEPS.md
06_AGENTS/ChaseOS-V1-Release-Cutline.md
06_AGENTS/ChaseOS-Product-Strategy-Domain-Open-Core-Handover-2026-05-30.md
06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
06_AGENTS/Feature-Register.md
06_AGENTS/Feature-Fit-Register.md
```

### 15.2 Create if missing

```text
docs/launch/chaseos_systems_domain_launch_plan.md
docs/website/chaseos_systems_website_information_architecture.md
docs/website/chaseos_systems_homepage_copy.md
docs/website/chaseos_systems_waitlist_spec.md
docs/website/chaseos_systems_privacy_security_terms_baseline.md
docs/forge/chaser_forge_public_index_domain_packet.md
docs/standards/README.md
```

### 15.3 Update if present

```text
docs/brand/README.md
docs/features/chaseos_v1_release_readiness_matrix.md
docs/features/chaseos_v1_public_beta_acceptance_checklist.md
runtime/forge/README.md
runtime/forge marketplace domain/index config docs
runtime/studio copy surfaces
website/app routes if present
```

### 15.4 Build logs and documentation history

Create:

```text
07_LOGS/Build-Logs/<date>_chaseos-systems-domain-alignment.md
07_LOGS/Documentation-History/<date>_chaseos-systems-domain-alignment.md
```

Update indexes:

```text
07_LOGS/Build-Logs-Index.md
07_LOGS/Documentation-History-Index.md
```

Use actual repo naming conventions if different.

---

## 16. README update block

Use this as the README domain/website block:

```md
## Website

ChaseOS public launch domain:

https://chaseos.systems

ChaseOS is the local-first AI operating system for builders running real projects with agents.

The public site will host:
- ChaseOS Studio early access
- Chaser Forge marketplace preview
- standards and pack manifests
- documentation
- open-core / commercial philosophy
- waitlist
- privacy and security notes
- support and creator submission paths
```

Use this as the public identity block:

```md
# ChaseOS

ChaseOS is the local-first AI operating system for builders running real projects with agents.

It turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

ChaseOS Studio is the desktop command center for the system.
Chaser Forge is the marketplace for workflow packs, extensions, and operating kits.
Managed Agents / Chaser Agent is the future hosted runtime layer for users and teams that do not want to self-host.
```

---

## 17. ROADMAP update block

Add a domain/launch milestone:

```md
## Domain and public launch

Primary domain selected:

https://chaseos.systems

The V1 public launch should use `chaseos.systems` for:
- product landing page,
- Studio early access,
- Forge marketplace preview,
- standards docs,
- waitlist,
- open-core/commercial explanation,
- privacy/security pages,
- support and creator submissions.

`chaseos.ai` remains a premium fallback / future redirect candidate and should be purchased after early waitlist proof or if the operator judges the price acceptable.
```

Add Forge milestone:

```md
## Chaser Forge public index

The public static index target is:

https://chaseos.systems/forge/index.json

Domain purchase changes Forge from domain-deferred to domain-selected / static-index-upload-pending. Live hosted fetch, payment/license mutation, and untrusted third-party exchange remain blocked until final approval and implementation evidence exist.
```

---

## 18. Feature Register update guidance

For Chaser Forge, update wording from:

```text
domain-deferred until official ChaseOS domain is purchased
```

to:

```text
official domain selected as https://chaseos.systems; public static index upload, URL verification, final digest/approval packet, and live hosted fetch approval remain pending.
```

Do not mark:

```text
payment/license mutation complete
live external marketplace complete
untrusted third-party exchange complete
generic hosted marketplace complete
```

unless implementation evidence exists.

---

## 19. Website launch phases

### Phase 0 — Domain lock

```text
Buy chaseos.systems
Configure DNS
Create holding page
Create hello/support/privacy/security aliases
Set basic DMARC/SPF/DKIM
Add waitlist provider
```

### Phase 1 — Waitlist page

```text
Homepage
Waitlist
Privacy
Terms placeholder
Open-core philosophy
Basic roadmap
```

### Phase 2 — Product site

```text
Studio page
Forge page
Standards page
Pricing preview
Download/early-access page
Support page
```

### Phase 3 — Forge public preview

```text
Static free-pack index
Creator submission form
Pack manifest docs
Free example packs
Manual install docs
```

### Phase 4 — V1 release

```text
Studio Early Access
Download/install
Local-first onboarding
Release notes
Safety/legal baseline
Smoke tests
GitHub public repo or public docs
```

### Phase 5 — Paid layers

```text
Pro £19/month
Premium packs
9% Forge fee
Runtime credits
Managed agents beta
Teams/private deployments
```

---

## 20. Social and public links

Use the same link everywhere:

```text
https://chaseos.systems
```

Social bio draft:

```text
ChaseOS — local-first AI operating system for builders running real projects with agents. Studio, Forge, knowledge graphs, approvals, and workflow packs.
```

Shorter:

```text
Local-first AI OS for builders, agents, workflows, and governed knowledge graphs.
```

GitHub profile:

```text
ChaseOS is the local-first AI operating system for builders running real projects with agents.
Website: https://chaseos.systems
```

X/Twitter launch line:

```text
We’re building ChaseOS: a local-first AI operating system for builders running real projects with agents.

Studio gives you the control panel.
Forge gives you workflow packs.
The graph keeps the work connected.

Early access: https://chaseos.systems
```

---

## 21. First launch video angle

The launch demo should prove the domain strategy.

Demo title:

```text
ChaseOS uses ChaseOS to launch chaseos.systems
```

Demo flow:

```text
1. Open ChaseOS Studio.
2. Show ChaseOS project graph.
3. Show website launch mission.
4. Show source/docs loaded.
5. Show generated homepage copy.
6. Show Forge page and standards docs.
7. Show waitlist form spec.
8. Show approval packets for external publish/upload.
9. Show static Forge index target at /forge/index.json.
10. Show what is live, preview, blocked, and upcoming.
11. End on chaseos.systems waitlist.
```

The video should emphasize:

```text
governed autonomy
knowledge graph
local-first control
workflow packs
public launch system
```

not:

```text
reckless full autonomy
magic browser control
fake payments
fake marketplace
```

---

## 22. Product-line wording after domain choice

Use this exact hierarchy:

```text
ChaseOS
The local-first AI operating system for builders running real projects with agents.

ChaseOS Studio
The desktop command center for ChaseOS.

Chaser Forge
The marketplace for ChaseOS workflow packs, extensions, templates, and operating kits.

ChaseOS Standards
The pack, graph, approval, agent, source, and outcome formats that make the ecosystem portable.

Managed Agents
Future hosted runtime workers for users and teams that do not want to self-host.
```

If using "Chaser Agent":

```text
Chaser Agent
Future first-party runtime harness for always-on agents — self-hosted locally or managed through ChaseOS services.
```

But for V1, prefer:

```text
Managed Agents — coming later.
```

This avoids confusing users before the runtime layer is ready.

---

## 23. Codex / Hermes / Claude repo-update handover prompt

Paste this into the repo-aware coding agent after adding this file.

```text
We are updating ChaseOS launch/domain strategy.

A new domain decision has been made:

Primary domain:
https://chaseos.systems

Product name remains:
ChaseOS

App name remains:
ChaseOS Studio

Marketplace/ecosystem remains:
Chaser Forge

Future managed runtime layer:
Managed Agents / Chaser Agent, post-V1.

Do not rename ChaseOS.
Do not use getchaseos.com, trychaseos.com, chaseos.dev, chaseos.app, or Chaser Systems as primary.
Do not claim chaseos.ai is primary.
Do not claim chaseos.com is owned.
Do not claim trademark/legal clearance.

Read first:
- 06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
- README.md
- PROJECT_FOUNDATION.md
- ROADMAP.md
- NEXT-STEPS.md
- SYSTEM-STATUS.md
- 06_AGENTS/ChaseOS-V1-Release-Cutline.md
- 06_AGENTS/ChaseOS-Product-Strategy-Domain-Open-Core-Handover-2026-05-30.md
- 06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
- 06_AGENTS/Feature-Register.md
- 06_AGENTS/Feature-Fit-Register.md
- Chaser Forge docs and runtime/forge README if present
- docs/features/chaseos_v1_release_readiness_matrix.md if present
- docs/features/chaseos_v1_public_beta_acceptance_checklist.md if present

Goal:
Align public-facing repo strategy with chaseos.systems as the selected domain.

Required updates:
1. Replace previous assumed primary `chaseos.ai` with `chaseos.systems`.
2. Reframe `chaseos.ai` as premium fallback / future redirect candidate after waitlist proof.
3. Remove or de-prioritize tacky fallback domains such as get/try/use variants.
4. Keep ChaseOS as product/platform name.
5. Keep ChaseOS Studio as app/control panel.
6. Keep Chaser Forge as marketplace/extension/workflow-pack layer.
7. Keep Managed Agents / Chaser Agent as future post-V1 runtime layer.
8. Update README website block with https://chaseos.systems.
9. Update V1 release cutline domain strategy.
10. Update Chaser Forge domain-deferred language:
    - old: official domain deferred
    - new: official domain selected as chaseos.systems; public static index upload and live hosted fetch approval remain pending.
11. Create or update website IA docs for chaseos.systems.
12. Create or update waitlist spec.
13. Create or update Forge public index domain packet.
14. Preserve all current/future/blocked capability boundaries.
15. Do not claim live marketplace payments, live hosted fetch, browser automation, or managed agents are complete unless repo evidence proves it.
16. Do not make implementation changes beyond docs/config unless explicitly safe and already supported.

Create if missing:
- docs/launch/chaseos_systems_domain_launch_plan.md
- docs/website/chaseos_systems_website_information_architecture.md
- docs/website/chaseos_systems_homepage_copy.md
- docs/website/chaseos_systems_waitlist_spec.md
- docs/forge/chaser_forge_public_index_domain_packet.md

Optional if repo conventions support:
- docs/website/chaseos_systems_privacy_security_terms_baseline.md
- docs/standards/README.md

Required writeback:
- build log
- documentation-history note
- update Build-Logs-Index.md
- update Documentation-History-Index.md
- update Feature-Register only for adopted domain/Forge status truth
- update Feature-Fit-Register only if feature placement changes

Final handover must list:
1. files read,
2. files created,
3. files modified,
4. final domain adopted,
5. old domain assumptions replaced,
6. final public product hierarchy,
7. homepage link added,
8. Forge index target adopted,
9. Chaser Forge status after domain decision,
10. what remains blocked,
11. what remains future,
12. tests/verification performed,
13. build log path,
14. documentation-history note path,
15. next recommended website implementation pass.
```

---

## 24. Final doctrine

Use this as the durable memory block:

```text
ChaseOS launches at https://chaseos.systems.

The product remains ChaseOS.

The domain is not a compromise. `.systems` fits the thesis because ChaseOS is a local-first AI operating system, knowledge graph, runtime control plane, workflow-pack substrate, and governed execution system.

`chaseos.ai` is a premium fallback / future redirect candidate, not the assumed primary. Buy it after early traction or if the operator decides the cost is justified.

The V1 site should not overclaim. It should sell ChaseOS Studio Early Access, Chaser Forge preview, standards, waitlist, privacy/local-first promise, open-core philosophy, and the public product roadmap.

Chaser Forge should move from domain-deferred to domain-selected / public-static-index-upload-pending. Live hosted fetch, payment/licensing, external marketplace mutation, and managed-agent services remain blocked/future until explicitly implemented and approved.

The public brand stack is:

ChaseOS = product/platform.
ChaseOS Studio = app/control panel.
Chaser Forge = marketplace/ecosystem.
ChaseOS Standards = pack/agent/graph/approval/source/outcome formats.
Managed Agents / Chaser Agent = future runtime service layer.

The launch proof should be:
ChaseOS uses ChaseOS to launch chaseos.systems.
```
