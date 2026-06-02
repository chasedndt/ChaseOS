# ChaseOS Core

ChaseOS Core is a local-first runtime and governance framework for bounded
human-AI workflows.

This production repository intentionally excludes local-only notes, generated
run evidence, credentials, workspaces, and non-product context.

## Current Scope

- Minimal production-safe CLI
- Core repository metadata
- Publication safety boundaries

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

## Status

Production baseline cleanup is in progress. Treat missing workflow packs or
workspace-specific content as intentional until they pass sanitized product
review.
