---
type: framework-standard
title: Site Profile To Workflow Learning
status: PARTIAL / CANDIDATE-ONLY STANDARD IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Site Profile To Workflow Learning

Mission Mode can notice repeated website use and propose site-profile updates. It cannot activate browser skills.

## Safe Loop

1. Browser run produces screenshot/log evidence.
2. Mission review extracts site interaction observations.
3. Site profile candidate records safe read actions, proposal actions, approval-required actions, forbidden actions, friction, selector candidates, and proof requirements.
4. Browser skill candidates remain review artifacts.
5. BOSL/Gate validation and human approval are required before any future activation.

## Forbidden

- credential reads
- cookie, token, password, API key, seed phrase, or session-file capture
- unsupervised purchases or listings
- direct browser skill activation
- platform-protected automation without explicit scope

Schema: `runtime/ventureops/templates/site_profile_schema.yaml`

Validator: `runtime.ventureops.validation.validate_site_profile`

Helper: `runtime.ventureops.site_profiles.build_site_profile_candidate`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
