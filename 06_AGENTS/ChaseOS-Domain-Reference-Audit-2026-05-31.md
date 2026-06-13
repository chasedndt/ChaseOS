---
title: ChaseOS Domain Reference Audit
created: 2026-05-31
runtime: hermes-optimus
status: COMPLETE / CURRENT DOMAIN OVERRIDE APPLIED TO TARGETED SURFACES / HISTORICAL REFS PRESERVED
type: domain-audit
links:
  - [[ChaseOS-AI-Domain-Override-Handover-2026-05-31]]
  - [[Hermes-Runtime-Profile]]
  - [[HERMES]]
  - [[Agent-Activity-Index]]
---

# ChaseOS Domain Reference Audit — 2026-05-31

## Current truth

- Primary public domain: `https://chaseos.ai`
- Public Forge index: `https://chaseos.ai/forge/index.json`
- Superseded as primary: `chaseos.systems`
- Allowed future use for `chaseos.systems`: secondary redirect, standards alias, ecosystem alias, or defensive domain if purchased later.
- Rejected active strategy: get/try/use-prefixed domains, `chaseos.dev`, `chaseos.app`.

## Classification rules

- Active public launch, website, README, Forge target, and V1 cutline references must use `chaseos.ai`.
- Historical handovers may retain old domain text only with an explicit superseded note.
- `chaseos.systems` may appear only as future secondary/alias/defensive-domain context or within guarded historical docs.
- Do not blindly replace domain history; classify first.

## Audit observations after targeted updates

| File | Line | Classification | Snippet |
|---|---:|---|---|
| `README.md` | 13 | CURRENT primary | https://chaseos.ai |
| `README.md` | 17 | ALLOWED secondary/superseded | Status: ChaseOS Studio Early Access / Developer Preview. `chaseos.systems` is superseded as the primary launch domain and may remain a future secondary redirect, standards alias, e |
| `README.md` | 100 | CURRENT primary | - Primary domain selected: `https://chaseos.ai`. |
| `README.md` | 103 | CURRENT primary | - Public Forge index target: `https://chaseos.ai/forge/index.json`. |
| `PROJECT_FOUNDATION.md` | 34 | ALLOWED secondary/superseded | **Domain override alignment (2026-05-31):** The selected primary public launch domain is `https://chaseos.ai`. ChaseOS remains the product/platform, ChaseOS Studio remains the app/ |
| `ROADMAP.md` | 11 | ALLOWED secondary/superseded | **Domain override and public launch milestone (2026-05-31):** Primary domain selected: `https://chaseos.ai`. ChaseOS Studio Early Access public launch should use this domain for pr |
| `NEXT-STEPS.md` | 21 | CURRENT primary | 1. Treat `https://chaseos.ai` as the selected primary public launch domain. Do not reopen this decision. |
| `NEXT-STEPS.md` | 24 | CURRENT primary | 4. Keep Chaser Forge status at domain-selected/static-index-upload-pending/live-fetch-approval-gated until `https://chaseos.ai/forge/index.json` exists, digest-verifies, and is exp |
| `06_AGENTS/Feature-Register.md` | 499 | CURRENT primary | - The completed lane covers governed local extension lifecycle, ChaseOS-owned local public catalog publish, read-only local marketplace library inspection, governed remote index ar |
| `06_AGENTS/Feature-Register.md` | 810 | CURRENT primary | Primary public domain selected: `https://chaseos.ai`. Chaser Forge public static index target: `https://chaseos.ai/forge/index.json`. This changes the product planning status from  |
| `06_AGENTS/Feature-Fit-Register.md` | 807 | CURRENT primary | Primary public domain selected: `https://chaseos.ai`. Chaser Forge public static index target: `https://chaseos.ai/forge/index.json`. This changes the product planning status from  |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 56 | CURRENT primary | https://chaseos.ai |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 59 | ALLOWED secondary/superseded | `chaseos.systems` is not a compromise domain; it fits the ChaseOS thesis because ChaseOS is a system of systems: local-first AI operating system, knowledge graph, agent control pla |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 64 | REVIEW stale systems reference | chaseos.systems/ |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 65 | REVIEW stale systems reference | chaseos.systems/studio |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 66 | REVIEW stale systems reference | chaseos.systems/forge |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 67 | REVIEW stale systems reference | chaseos.systems/standards |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 68 | REVIEW stale systems reference | chaseos.systems/pricing |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 69 | REVIEW stale systems reference | chaseos.systems/docs |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 70 | REVIEW stale systems reference | chaseos.systems/open-core |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 71 | REVIEW stale systems reference | chaseos.systems/download |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 72 | REVIEW stale systems reference | chaseos.systems/privacy |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 73 | REVIEW stale systems reference | chaseos.systems/security |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 74 | REVIEW stale systems reference | chaseos.systems/waitlist |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 75 | REVIEW stale systems reference | chaseos.systems/roadmap |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 76 | REVIEW stale systems reference | chaseos.systems/support |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 77 | REVIEW stale systems reference | chaseos.systems/terms |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 80 | REJECTED active strategy / do not use | `chaseos.ai` is the selected primary public launch domain. `chaseos.systems` is superseded as primary and may later be a secondary redirect, standards/ecosystem alias, or defensive |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 124 | ALLOWED secondary/superseded | Operator decision context: `https://chaseos.ai` is the selected primary public launch domain. `chaseos.ai` is the selected primary public launch domain; `chaseos.systems` is option |
| `06_AGENTS/ChaseOS-V1-Release-Cutline.md` | 220 | CURRENT primary | - Chaser Forge marketplace / extension system: local proof and static-host handoff exist; `https://chaseos.ai/forge/index.json` is the selected public static-index target, but live |
| `docs/website/chaseos_hosting_deployment_checklist.md` | 6 | CURRENT primary | primary_domain: https://chaseos.ai |
| `docs/website/chaseos_hosting_deployment_checklist.md` | 25 | CURRENT primary | 4. Add apex `chaseos.ai` and `www` redirect. |
| `docs/website/chaseos_hosting_deployment_checklist.md` | 38 | ALLOWED secondary/superseded | `https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary red |
| `docs/website/chaseos_public_launch_checklist.md` | 12 | CURRENT primary | - `chaseos.ai` ownership/RDAP verified. |
| `docs/website/chaseos_public_launch_checklist.md` | 29 | ALLOWED secondary/superseded | `https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary red |
| `docs/website/chaseos_systems_page_copy.md` | 6 | CURRENT primary | primary_domain: https://chaseos.ai |
| `docs/website/chaseos_systems_page_copy.md` | 63 | ALLOWED secondary/superseded | `https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary red |
| `docs/website/chaseos_systems_site_map.md` | 6 | CURRENT primary | primary_domain: https://chaseos.ai |
| `docs/website/chaseos_systems_site_map.md` | 14 | CURRENT primary | `https://chaseos.ai` is the selected primary public launch domain. V1 uses path-based pages before subdomains. |
| `docs/website/chaseos_systems_site_map.md` | 46 | ALLOWED secondary/superseded | `https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary red |
| `docs/website/chaseos_waitlist_data_model.md` | 61 | CURRENT primary | The `chaseos.ai` purchase trigger means 50 qualified signups, 10 high-intent beta applicants, or 3 commercially serious setup/pilot conversations — not random emails. |
| `docs/launch/chaseos_systems_domain_launch_plan.md` | 6 | CURRENT primary | primary_domain: https://chaseos.ai |
| `docs/launch/chaseos_systems_domain_launch_plan.md` | 13 | REJECTED active strategy / do not use | `https://chaseos.ai` is the selected primary public launch domain. `chaseos.systems` is superseded as primary and may later be a secondary redirect, standards/ecosystem alias, or d |
| `docs/launch/chaseos_systems_domain_launch_plan.md` | 21 | CURRENT primary | 5. Demo + distribution: `ChaseOS uses ChaseOS to launch chaseos.ai`. |
| `docs/launch/chaseos_systems_domain_launch_plan.md` | 28 | ALLOWED secondary/superseded | `https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary red |
| `docs/forge/chaser_forge_public_index_domain_packet.md` | 6 | CURRENT primary | public_index_target: https://chaseos.ai/forge/index.json |
| `docs/forge/chaser_forge_public_index_domain_packet.md` | 13 | CURRENT primary | Official domain selected: `https://chaseos.ai`. |
| `docs/forge/chaser_forge_public_index_domain_packet.md` | 26 | CURRENT primary | https://chaseos.ai/forge/index.json |
| `docs/forge/chaser_forge_public_index_domain_packet.md` | 32 | CURRENT primary | https://chaseos.ai/static/forge/index.json |
| `docs/forge/chaser_forge_public_index_domain_packet.md` | 33 | CURRENT primary | https://chaseos.ai/forge/registry/index.json |
| `docs/forge/chaser_forge_public_index_domain_packet.md` | 53 | ALLOWED secondary/superseded | `https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary red |
| `docs/brand/chaseos_domain_brand_safety_checklist.md` | 6 | CURRENT primary | primary_domain: https://chaseos.ai |
| `docs/brand/chaseos_domain_brand_safety_checklist.md` | 15 | CURRENT primary | - Registrar checkout confirms `chaseos.ai` ownership. |
| `docs/brand/chaseos_domain_brand_safety_checklist.md` | 39 | CURRENT primary | Do not use `Chaser Systems` as the umbrella brand unless a future operator/legal decision clears it. Product remains ChaseOS; public domain is `chaseos.ai`. |
| `docs/brand/chaseos_domain_brand_safety_checklist.md` | 44 | ALLOWED secondary/superseded | `https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary red |
| `docs/standards/README.md` | 17 | NOT DOMAIN / schema name | - `chaseos.approval.json` — approval packet format. |
| `docs/standards/chaseos-agent-runtime-contract-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-approval-packet-v1.md` | 5 | NOT DOMAIN / schema name | schema_name: chaseos.approval.json |
| `docs/standards/chaseos-approval-packet-v1.md` | 11 | NOT DOMAIN / schema name | Schema name: `chaseos.approval.json` |
| `docs/standards/chaseos-approval-packet-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-entitlement-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-forge-index-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-graph-object-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-managed-job-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-outcome-record-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-pack-manifest-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `docs/standards/chaseos-source-provenance-v1.md` | 17 | REVIEW stale systems reference | This is a documentation-level draft created for the `chaseos.systems` launch-readiness pass. It does not create a validator, package registry, payment/license service, managed runt |
| `runtime/forge/README.md` | 5 | CURRENT primary | Current status: COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, LOCAL LIVE-INDEX INPUT PREFILL BUILT, NO-DOMAIN CLOSEOUT VERIFIED, DOMAIN SELECTED / PUBLIC STATIC INDEX UPLOAD PENDIN |
| `runtime/forge/README.md` | 426 | CURRENT primary | Primary public domain selected: `https://chaseos.ai`. Chaser Forge public static index target: `https://chaseos.ai/forge/index.json`. This confirms the product planning status as d |
| `06_AGENTS/Chaser-Forge-Feature-Family.md` | 46 | CURRENT primary | The governed local extension lifecycle, local catalog publish path, read-only Local Marketplace Library, approved marketplace install path, digest-bound remote index artifact path, |
| `06_AGENTS/Chaser-Forge-Feature-Family.md` | 107 | CURRENT primary | Primary public domain selected: `https://chaseos.ai`. Chaser Forge public static index target: `https://chaseos.ai/forge/index.json`. This confirms the product planning status as d |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 1 | CURRENT primary | # ChaseOS.ai Domain Override + Runtime Split Handover |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 5 | CURRENT primary | **Primary domain now selected:** `chaseos.ai` |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 6 | ALLOWED secondary/superseded | **Supersedes:** prior assumption that `chaseos.systems` is the selected primary launch domain. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 15 | CURRENT primary | https://chaseos.ai |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 20 | ALLOWED secondary/superseded | `chaseos.systems` may still be purchased later, but it is no longer the primary launch assumption. If purchased, it should be used as a redirect, standards/ecosystem alias, or seco |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 26 | CURRENT primary | chaseos.ai |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 29 | ALLOWED secondary/superseded | chaseos.systems |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 51 | ALLOWED secondary/superseded | Primary domain: chaseos.systems |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 52 | ALLOWED secondary/superseded | Public index target: https://chaseos.systems/forge/index.json |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 58 | CURRENT primary | Primary domain: chaseos.ai |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 59 | CURRENT primary | Public index target: https://chaseos.ai/forge/index.json |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 68 | ALLOWED secondary/superseded | chaseos.ai is now the selected primary public domain. Prior chaseos.systems launch assumptions are superseded. chaseos.systems may remain a future secondary/redirect/standards doma |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 75 | CURRENT primary | Build the first public site around `chaseos.ai`: |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 123 | CURRENT primary | https://chaseos.ai/forge/index.json |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 226 | CURRENT primary | Apply the chaseos.ai domain override first. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 297 | CURRENT primary | Start at chaseos.ai. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 313 | CURRENT primary | README and public-facing docs use chaseos.ai as primary. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 314 | ALLOWED secondary/superseded | ROADMAP/NEXT-STEPS/V1 cutline no longer assume chaseos.systems as primary. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 315 | CURRENT primary | Forge docs target https://chaseos.ai/forge/index.json. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 316 | CURRENT primary | Website plan targets chaseos.ai. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 317 | CURRENT primary | Waitlist/admin plan targets chaseos.ai. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 318 | CURRENT primary | Cloudflare/Vercel deploy plan targets chaseos.ai. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 319 | CURRENT primary | Video/GitHub readiness docs target chaseos.ai. |
| `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md` | 365 | CURRENT primary | chaseos.ai is now the selected public domain. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 8 | ALLOWED secondary/superseded | primary_domain: chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 9 | REVIEW | premium_fallback_domain: chaseos.ai |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 10 | ALLOWED secondary/superseded | operator_decision: chaseos.systems selected as primary launch domain |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 25 | ALLOWED secondary/superseded | > **Domain override note (2026-05-31):** This document contains historical `chaseos.systems` primary-domain assumptions. It is superseded by `06_AGENTS/ChaseOS-AI-Domain-Override-H |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 29 | ALLOWED secondary/superseded | > This document updates the ChaseOS public-domain and launch strategy after the operator selected **`chaseos.systems`** as the primary domain. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 39 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 75 | CURRENT primary | chaseos.ai |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 78 | CURRENT primary | But `chaseos.ai` should not be bought immediately unless the operator decides the cost is justified. The current operating rule is: |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 81 | CURRENT primary | Buy chaseos.ai after early waitlist proof, unless the price is trivial to the operator. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 87 | CURRENT primary | Buy chaseos.ai after any one of: |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 99 | ALLOWED secondary/superseded | ## 1. Why `chaseos.systems` is the right primary domain |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 101 | ALLOWED secondary/superseded | `chaseos.systems` is not a fallback. It is strategically coherent. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 145 | ALLOWED secondary/superseded | chaseos.systems = public home of the ChaseOS ecosystem |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 215 | ALLOWED secondary/superseded | https://chaseos.systems/ |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 216 | ALLOWED secondary/superseded | https://chaseos.systems/studio |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 217 | ALLOWED secondary/superseded | https://chaseos.systems/forge |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 218 | ALLOWED secondary/superseded | https://chaseos.systems/standards |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 219 | ALLOWED secondary/superseded | https://chaseos.systems/pricing |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 220 | ALLOWED secondary/superseded | https://chaseos.systems/docs |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 221 | ALLOWED secondary/superseded | https://chaseos.systems/open-core |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 222 | ALLOWED secondary/superseded | https://chaseos.systems/download |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 223 | ALLOWED secondary/superseded | https://chaseos.systems/privacy |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 224 | ALLOWED secondary/superseded | https://chaseos.systems/security |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 225 | ALLOWED secondary/superseded | https://chaseos.systems/waitlist |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 226 | ALLOWED secondary/superseded | https://chaseos.systems/roadmap |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 227 | ALLOWED secondary/superseded | https://chaseos.systems/support |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 228 | ALLOWED secondary/superseded | https://chaseos.systems/terms |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 234 | ALLOWED secondary/superseded | https://chaseos.systems/creators |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 235 | ALLOWED secondary/superseded | https://chaseos.systems/submit-pack |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 236 | ALLOWED secondary/superseded | https://chaseos.systems/marketplace-terms |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 237 | ALLOWED secondary/superseded | https://chaseos.systems/license |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 238 | ALLOWED secondary/superseded | https://chaseos.systems/status |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 239 | ALLOWED secondary/superseded | https://chaseos.systems/account |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 240 | ALLOWED secondary/superseded | https://chaseos.systems/credits |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 241 | ALLOWED secondary/superseded | https://chaseos.systems/agents |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 249 | ALLOWED secondary/superseded | https://chaseos.systems/forge/index.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 255 | ALLOWED secondary/superseded | https://chaseos.systems/forge/registry/index.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 261 | ALLOWED secondary/superseded | https://chaseos.systems/forge/index.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 306 | ALLOWED secondary/superseded | studio.chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 307 | ALLOWED secondary/superseded | forge.chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 308 | ALLOWED secondary/superseded | docs.chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 309 | ALLOWED secondary/superseded | api.chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 310 | ALLOWED secondary/superseded | status.chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 311 | ALLOWED secondary/superseded | account.chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 317 | ALLOWED secondary/superseded | studio.chaseos.systems -> hosted/account web shell if built |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 318 | ALLOWED secondary/superseded | forge.chaseos.systems  -> public marketplace index/catalog |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 319 | ALLOWED secondary/superseded | docs.chaseos.systems   -> developer docs and standards |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 320 | ALLOWED secondary/superseded | api.chaseos.systems    -> licensing, accounts, credits, telemetry-opt-in, marketplace APIs |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 321 | ALLOWED secondary/superseded | status.chaseos.systems -> hosted-service status page |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 327 | ALLOWED secondary/superseded | chaseos.systems/studio |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 328 | ALLOWED secondary/superseded | chaseos.systems/forge |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 329 | ALLOWED secondary/superseded | chaseos.systems/docs |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 341 | ALLOWED secondary/superseded | chaseos.systems appears strategically safe enough to proceed as the selected domain, |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 382 | ALLOWED secondary/superseded | ## 6. What changes now that `chaseos.systems` is selected |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 389 | CURRENT primary | chaseos.ai primary |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 391 | REJECTED active strategy / do not use | getchaseos.com fallback |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 392 | REJECTED active strategy / do not use | chaseos.app fallback |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 393 | REJECTED active strategy / do not use | chaseos.dev fallback |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 399 | ALLOWED secondary/superseded | Primary domain: chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 400 | REVIEW | Premium AI fallback / future redirect: chaseos.ai |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 462 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 468 | ALLOWED secondary/superseded | Website: https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 665 | NOT DOMAIN / schema name | chaseos.approval.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 816 | CURRENT primary | The waitlist is the proof mechanism for whether to buy `chaseos.ai`. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 834 | CURRENT primary | Trigger to buy `chaseos.ai`: |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 900 | ALLOWED secondary/superseded | hello@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 901 | ALLOWED secondary/superseded | support@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 902 | ALLOWED secondary/superseded | security@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 903 | ALLOWED secondary/superseded | privacy@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 904 | ALLOWED secondary/superseded | creators@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 905 | ALLOWED secondary/superseded | forge@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 906 | ALLOWED secondary/superseded | legal@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 925 | ALLOWED secondary/superseded | _dmarc.chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 931 | ALLOWED secondary/superseded | v=DMARC1; p=none; rua=mailto:security@chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 951 | ALLOWED secondary/superseded | official domain selected: chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 962 | ALLOWED secondary/superseded | https://chaseos.systems/forge/index.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 968 | ALLOWED secondary/superseded | https://chaseos.systems/static/forge/index.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 974 | ALLOWED secondary/superseded | https://chaseos.systems/forge/registry/index.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1293 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1333 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1335 | ALLOWED secondary/superseded | The V1 public launch should use `chaseos.systems` for: |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1345 | REVIEW | `chaseos.ai` remains a premium fallback / future redirect candidate and should be purchased after early waitlist proof or if the operator judges the price acceptable. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1355 | ALLOWED secondary/superseded | https://chaseos.systems/forge/index.json |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1373 | ALLOWED secondary/superseded | official domain selected as https://chaseos.systems; public static index upload, URL verification, final digest/approval packet, and live hosted fetch approval remain pending. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1394 | ALLOWED secondary/superseded | Buy chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1464 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1483 | ALLOWED secondary/superseded | Website: https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1495 | ALLOWED secondary/superseded | Early access: https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1507 | ALLOWED secondary/superseded | ChaseOS uses ChaseOS to launch chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1523 | ALLOWED secondary/superseded | 11. End on chaseos.systems waitlist. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1595 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1610 | REJECTED active strategy / do not use | Do not use getchaseos.com, trychaseos.com, chaseos.dev, chaseos.app, or Chaser Systems as primary. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1611 | CURRENT primary | Do not claim chaseos.ai is primary. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1632 | ALLOWED secondary/superseded | Align public-facing repo strategy with chaseos.systems as the selected domain. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1635 | ALLOWED secondary/superseded | 1. Replace previous assumed primary `chaseos.ai` with `chaseos.systems`. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1636 | REVIEW | 2. Reframe `chaseos.ai` as premium fallback / future redirect candidate after waitlist proof. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1642 | ALLOWED secondary/superseded | 8. Update README website block with https://chaseos.systems. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1646 | ALLOWED secondary/superseded | - new: official domain selected as chaseos.systems; public static index upload and live hosted fetch approval remain pending. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1647 | ALLOWED secondary/superseded | 11. Create or update website IA docs for chaseos.systems. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1698 | ALLOWED secondary/superseded | ChaseOS launches at https://chaseos.systems. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1704 | REVIEW | `chaseos.ai` is a premium fallback / future redirect candidate, not the assumed primary. Buy it after early traction or if the operator decides the cost is justified. |
| `06_AGENTS/ChaseOS-Systems-Domain-Launch-Alignment-Handover-2026-05-31.md` | 1719 | ALLOWED secondary/superseded | ChaseOS uses ChaseOS to launch chaseos.systems. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 7 | ALLOWED secondary/superseded | scope: post-domain purchase, chaseos.systems website plan, hosting architecture, waitlist, admin panel, safety checks, repo update prompt, public docs alignment, GitHub/social laun |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 8 | ALLOWED secondary/superseded | primary_domain: chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 9 | REVIEW | premium_fallback_domain: chaseos.ai |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 10 | ALLOWED secondary/superseded | operator_assumption: chaseos.systems purchased or in immediate purchase flow |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 23 | ALLOWED secondary/superseded | > **Domain override note (2026-05-31):** This document contains historical `chaseos.systems` primary-domain assumptions. It is superseded by `06_AGENTS/ChaseOS-AI-Domain-Override-H |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 27 | ALLOWED secondary/superseded | > This is the third repo-ready handover in the ChaseOS launch strategy sequence. It assumes the operator has selected **`chaseos.systems`** as the primary public launch domain and  |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 43 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 75 | CURRENT primary | chaseos.ai |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 81 | CURRENT primary | Do not buy chaseos.ai just because it is nice. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 88 | CURRENT primary | Buy chaseos.ai after any one of: |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 129 | ALLOWED secondary/superseded | `chaseos.systems` fits better than a generic app or AI-wrapper domain because ChaseOS is not only an app and not only an AI product. It is a system of systems: |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 161 | ALLOWED secondary/superseded | Once `chaseos.systems` is purchased, the repository should stop treating the domain as undecided. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 168 | CURRENT primary | chaseos.ai is the assumed primary domain |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 170 | REJECTED active strategy / do not use | getchaseos.com is a fallback |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 171 | REJECTED active strategy / do not use | chaseos.dev is a public product option |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 177 | ALLOWED secondary/superseded | chaseos.systems is the selected primary public domain. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 178 | REVIEW | chaseos.ai is a traction-triggered premium redirect/fallback. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 180 | REJECTED active strategy / do not use | chaseos.dev is not the public product domain. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 212 | ALLOWED secondary/superseded | ## 3. Website structure for `chaseos.systems` |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 254 | ALLOWED secondary/superseded | chaseos.systems/forge |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 255 | ALLOWED secondary/superseded | chaseos.systems/docs |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 256 | ALLOWED secondary/superseded | chaseos.systems/standards |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 264 | ALLOWED secondary/superseded | forge.chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 265 | ALLOWED secondary/superseded | api.chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 266 | ALLOWED secondary/superseded | account.chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 267 | ALLOWED secondary/superseded | status.chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 268 | ALLOWED secondary/superseded | docs.chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 299 | ALLOWED secondary/superseded | - Works well with a domain like chaseos.systems. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 312 | ALLOWED secondary/superseded | Add custom domain chaseos.systems. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 313 | ALLOWED secondary/superseded | Redirect www.chaseos.systems -> chaseos.systems. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 459 | CURRENT primary | The `50 signups` trigger for buying `chaseos.ai` should mean **50 qualified signups**, not 50 random emails. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 566 | ALLOWED secondary/superseded | https://chaseos.systems/forge/index.json |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 572 | ALLOWED secondary/superseded | https://chaseos.systems/forge |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 887 | ALLOWED secondary/superseded | ICANN Lookup / RDAP for chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 930 | ALLOWED secondary/superseded | "chaseos.systems" |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 935 | ALLOWED secondary/superseded | Do not use `Chaser Systems` as umbrella brand if it conflicts with an active existing company/site. The product is ChaseOS; the public domain is `chaseos.systems`. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1010 | ALLOWED secondary/superseded | Website: https://chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1011 | ALLOWED secondary/superseded | Waitlist: https://chaseos.systems/waitlist |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1012 | ALLOWED secondary/superseded | Docs: https://chaseos.systems/docs |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1013 | ALLOWED secondary/superseded | Forge preview: https://chaseos.systems/forge |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1023 | ALLOWED secondary/superseded | Buy chaseos.systems. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1039 | ALLOWED secondary/superseded | Deploy to chaseos.systems. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1120 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1171 | ALLOWED secondary/superseded | 1. Primary public domain is `https://chaseos.systems`. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1172 | REVIEW | 2. `chaseos.ai` is now a traction-triggered premium redirect/fallback, not the assumed primary. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1178 | REJECTED active strategy / do not use | 8. Do not use chaseos.dev as the public product domain. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1233 | CURRENT primary | - chaseos.ai as primary |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1235 | REJECTED active strategy / do not use | - chaseos.app as fallback primary |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1236 | REJECTED active strategy / do not use | - chaseos.dev as public product domain |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1237 | REJECTED active strategy / do not use | - getchaseos.com / trychaseos.com / usechaseos.com |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1244 | ALLOWED secondary/superseded | `chaseos.systems` is the selected primary launch domain. `chaseos.ai` is a traction-triggered premium fallback/redirect. |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1306 | ALLOWED secondary/superseded | `domain selected: chaseos.systems` |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1312 | ALLOWED secondary/superseded | https://chaseos.systems/forge/index.json |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1448 | ALLOWED secondary/superseded | 2. verify `chaseos.systems` appears in public website/docs strategy; |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1449 | REVIEW | 3. verify `chaseos.ai` appears only as fallback/redirect/traction-triggered premium domain; |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1495 | ALLOWED secondary/superseded | https://chaseos.systems |
| `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md` | 1575 | ALLOWED secondary/superseded | It is moving into a public product layer at chaseos.systems. |

## Action taken in this Hermes pass

Targeted active docs were updated to `https://chaseos.ai`; older `chaseos.systems` strategy handovers received superseded-domain notes. Historical strategy context was preserved. Schema names such as `chaseos.approval.json` are not domain references.
