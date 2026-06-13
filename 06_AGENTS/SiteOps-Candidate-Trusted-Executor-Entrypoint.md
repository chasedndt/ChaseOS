---
title: SiteOps Candidate Trusted Executor Entrypoint
type: implementation-note
status: PARTIAL / GUARDED
created: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Trusted Executor Entrypoint

`apply_trusted_candidate_artifacts` is now the canonical guarded entrypoint for
SiteOps Browser Skill candidate trusted artifact application.

It is not a live activation path. It is a stable runtime/API/CLI surface over
the existing trusted inactive artifact writer.

## Current Behavior

- Module function: `runtime.siteops.candidate_promotions.apply_trusted_candidate_artifacts`
- CLI command: `chaseos siteops candidates apply-trusted-candidate-artifacts`
- Guard marker: `siteops_guarded_executor = True`
- Delegate: `candidate_promotion_trusted_inactive_artifact_writer_implementation`
- Write flag: `--write-inactive-artifacts`
- Required before any inactive write:
  - scoped tenant/workspace/user inputs
  - approved replacement approval posture
  - immediate trusted inactive artifact writer preflight
  - clear target path posture
  - ChaseOS Gate allowance for `siteops.browser_skill_candidate.apply_trusted_artifacts`

## Boundaries

The entrypoint still does not:

- consume approvals
- mutate Gate policy
- activate promoted skills
- launch or control browsers
- enqueue Agent Bus work
- call providers
- write canonical ChaseOS memory/state

## Verification

2026-05-03 Codex pass:

- `python -m py_compile runtime/siteops/candidate_promotions.py runtime/cli/siteops_commands.py runtime/cli/main.py`
- `python -m pytest runtime/siteops/tests/test_candidate_promotions.py -q`
- `python -m pytest runtime/tests/test_cli_command_contract.py -q`
- `python -m pytest runtime/tests/test_cli_json_contract.py -q`
- `python -m runtime.cli.generate_docs --check`

Result:

- focused candidate suite: `137 passed`
- CLI command contract: `8 passed`
- CLI JSON contract: `2 passed`
- generated CLI docs: up to date

## Remaining Work

- Apply the live Gate allowlist patch only with real operator-reviewed approval IDs.
- Re-run trusted inactive writer readiness after the Gate patch.
- Run `apply-trusted-candidate-artifacts` against the approved live chain.
- Keep activation, browser execution, Agent Bus/provider calls, and canonical writeback in separate future passes.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
