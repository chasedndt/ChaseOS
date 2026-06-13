# ChaseOS Core

ChaseOS Core is a local-first runtime and governance framework for bounded
human-AI workflows.

This production repository intentionally excludes local-only notes, generated
run evidence, credentials, workspaces, and non-product context.

## Current Scope

- Minimal production-safe CLI
- Core repository metadata
- Publication safety boundaries
- Public-safe OpenCore/template documentation surfaces
- Chaser Forge workflow and extension-governance templates

## Safety Boundary

Do not commit credentials, local machine state, run artifacts, local-only notes,
or generated evidence bundles to this repository.

Production downloads and installers require a separate release gate with human
approval, checksums, release notes, known limitations, and a security/privacy
review.

## Development

```powershell
python -m runtime.cli.main --help
```

## OpenCore / Template Surfaces

The first tracked OpenCore transfer slice is Chaser Forge:

- `docs/forge/chaser_forge_workflows_index.md`
- `docs/forge/chaser_forge_workflow_proofs_index.md`
- `docs/forge/chaser_forge_opencore_transfer_plan.md`
- `docs/standards/chaseos-forge-workflow-node-v1.md`
- `templates/forge/`

These are governance and template surfaces only. They do not enable live
marketplace fetch, network upload, paid checkout, license enforcement,
third-party remote install, approval consumption, provider/model calls, browser
control, host mutation, or canonical promotion.

## Status

Production baseline cleanup is in progress. Treat missing workflow packs or
workspace-specific content as intentional until they pass sanitized product
review.
