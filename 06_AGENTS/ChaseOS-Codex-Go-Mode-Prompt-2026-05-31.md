# Codex Go Mode Prompt — ChaseOS V1 Build + chaseos.ai Launch Implementation

Paste this into Codex.

---

/go mode

You are Codex working inside the ChaseOS repository.

You are the implementation/build/test runtime for the ChaseOS V1 launch preparation pass.

Do not debate the strategy. Implement the bounded launch readiness tasks.

==================================================
DOMAIN OVERRIDE — READ FIRST
==================================================

The domain truth has changed.

Primary public domain is now:

https://chaseos.ai

Any prior handover or repo doc saying chaseos.systems is the selected primary domain is superseded.

chaseos.systems may be a future secondary/redirect if purchased, but it is not the current primary launch domain.

Update all implementation plans, website targets, Forge targets, docs, and generated outputs to use chaseos.ai.

Primary public Forge index target:

https://chaseos.ai/forge/index.json

==================================================
READ THESE HANDOVERS FIRST
==================================================

Read all that exist:

- 06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
- 06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md
- 06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md
- 06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md
- 06_AGENTS/ChaseOS-V1-Execution-Kanban-Hermes-Codex-Handover-2026-05-31.md
- 06_AGENTS/ChaseOS-Launch-Video-GitHub-Public-Readiness-Handover-2026-05-31.md
- 06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md

If the final override file is missing, create it from the domain facts above before continuing.

Also read canonical repo files:
- README.md
- PROJECT_FOUNDATION.md
- ROADMAP.md
- NEXT-STEPS.md
- SYSTEM-STATUS.md
- Feature-Register.md
- Feature-Fit-Register.md
- V1 release/cutline docs if present
- Studio architecture/docs if present
- Forge docs if present
- Standards docs if present
- Website/docs directory if present
- Build log and documentation-history index files if present

==================================================
YOUR ROLE
==================================================

Codex owns implementation.

You are responsible for making the repo technically ready for:

1. ChaseOS V1 demo readiness.
2. chaseos.ai public website skeleton.
3. waitlist capture and simple admin readiness.
4. Chaser Forge static preview and /forge/index.json.
5. standards/docs skeleton.
6. Studio V1 polish where already scoped.
7. tests, smoke checks, CI/build verification, and scheduled task definitions.

Hermes is responsible for product/doc orchestration, Kanban planning, launch copy, acceptance criteria, and review. Do not duplicate Hermes strategic work unless required for implementation.

==================================================
DO NOT DO
==================================================

Do not deploy externally.
Do not mutate DNS.
Do not send emails.
Do not create Stripe products.
Do not make the repo public.
Do not process waitlist PII through model/provider calls.
Do not enable live marketplace payments.
Do not enable managed agents.
Do not add arbitrary browser automation.
Do not claim unsupported automation.
Do not create duplicate architecture if an existing module exists.
Do not delete old handovers; add supersession notes instead.
Do not expose secrets, private paths, personal data, credentials, or provider keys.

==================================================
IMPLEMENTATION PRIORITIES
==================================================

P0 — Domain and repo alignment:
- Replace selected-primary-domain assumptions from chaseos.systems to chaseos.ai.
- Keep chaseos.systems as optional future secondary only.
- Update README / ROADMAP / NEXT-STEPS / V1 cutline / Forge docs / website docs where relevant.
- Update public index target to https://chaseos.ai/forge/index.json.
- Add supersession note to old domain strategy docs if appropriate.

P0 — Website scaffold:
Create or update the website app/static site if the repo has a web surface.

Required first routes:
- /
- /waitlist
- /studio
- /forge
- /forge/index.json
- /standards
- /open-core
- /privacy
- /roadmap

Optional preview routes:
- /pricing
- /docs
- /download
- /security
- /support
- /terms
- /creators
- /submit-pack

If there is no existing website app, create a minimal scaffold according to the repo’s current stack. Prefer a simple static-first implementation. Do not overbuild.

P0 — Waitlist:
Implement or specify a waitlist capture flow.

Fields:
- email
- name
- role
- main_use_case
- current_ai_stack
- biggest_pain
- pro_interest
- forge_creator_interest
- setup_sprint_interest
- consent_to_updates
- source/referrer if available
- created_at

If backend support is not present, create:
- waitlist schema/spec
- API route stub or static form integration point
- storage plan
- admin view spec
- environment variable template
- test fixture

Do not send emails automatically unless existing approved infrastructure exists.

P0 — Admin panel:
Create a simple protected admin spec or implementation.

Admin should show:
- total signups
- qualified signups
- creator-interest signups
- team/business-interest signups
- signup source
- export-ready view

Protect admin routes. If auth is not ready, mark admin as local/protected-preview and block public access.

P0 — Forge preview:
Create or update:
- /forge page
- /forge/index.json

The index should include free/example packs only unless entitlement/payment exists.

No remote untrusted install without validation.
No payments.
No licensing mutation.

P0 — Standards skeleton:
Create or update standards docs for:
- chaseos.pack.json
- forge index format
- approval packet format
- agent runtime contract
- graph object format
- source evidence format
- outcome record format

Implementation can be docs/schema examples first.

P0 — V1 demo surfaces:
Prioritize implementation only where the repo already has substrate:
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

Do not attempt full future features.

P1 — Scheduled tasks / cron:
Define scheduled tasks or cron specs for:
- daily waitlist summary/export
- daily safety scan reminder
- weekly Forge index validation
- weekly broken-link check
- weekly launch readiness report
- daily build/smoke status if useful

If Cloudflare Workers Cron is the chosen route, create config/spec only unless runtime is set up.

P1 — Tests / smoke:
Add tests or scripts for:
- website builds
- key routes exist
- /forge/index.json validates
- waitlist schema validates
- no unsupported domain reference remains in public docs
- no secrets/private paths leak into public docs
- blocked/future features are labelled honestly
- README links point to chaseos.ai
- public docs do not claim live payments/managed agents/browser automation

==================================================
KANBAN / AGENT BOX
==================================================

Create or update Kanban/Agent Box tasks for your implementation work.

Each task must include:
- owner: Codex
- priority: P0/P1/P2/FUTURE
- status: TODO/IN_PROGRESS/READY/PARTIAL/BLOCKED/FUTURE
- acceptance criteria
- files touched
- blockers
- reviewer: Hermes or human

Do not assign Hermes implementation work unless it is documentation/review.

==================================================
BUILD LOG / HISTORY
==================================================

Create a build log.
Create a documentation-history note.
Update indexes if they exist.

Use repo conventions. If unsure, create under the existing build-log/doc-history directories.

==================================================
FINAL HANDOVER
==================================================

Final response must include:

1. Files read.
2. Files created.
3. Files modified.
4. Domain references changed from chaseos.systems to chaseos.ai.
5. Website scaffold status.
6. Waitlist implementation/spec status.
7. Admin panel implementation/spec status.
8. Forge preview and /forge/index.json status.
9. Standards docs/schema status.
10. Studio/V1 demo changes.
11. Scheduled task/cron specs created.
12. Tests/smoke checks added or run.
13. Remaining blockers.
14. What is READY / PARTIAL / BLOCKED / FUTURE.
15. Build log path.
16. Documentation-history note path.
17. What Hermes should review next.

Execute now.
