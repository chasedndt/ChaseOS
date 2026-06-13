---
title: ChaseOS CLI Install Notes
status: active
created: 2026-04-25
updated: 2026-04-27
---

# ChaseOS CLI Install Notes

## Current promotion path

The repo-local command surface was first developed through:

```powershell
python chaseos.py ...
```

That path is now a compatibility shim only.
The canonical installed/operator entrypoint is:
- `runtime.cli.main:main`

Installed `chaseos` and `chase` scripts point there directly.

## Editable install

From the repository root:

```powershell
pip install -e .
```

After that, the following commands should resolve through the package entrypoint when the Python user Scripts directory is on PATH:

```powershell
chaseos runtime inventory
chaseos runtime status --runtime all
chaseos runtime health --runtime all
chaseos runtime health-debug --runtime all
chaseos setup status --json
chaseos setup validate --json
chaseos setup provider wizard openai --apply --json
chaseos gate validate
```

If `chaseos` is installed but not recognized, the likely issue is PATH rather than packaging. Add the Python user Scripts directory for the current machine to PATH, or invoke the installed script by its fully qualified local path.

Example validation command after PATH is configured:

```powershell
chaseos runtime inventory --json
```

## Why this matters

This is the point where ChaseOS stops being only a Python-file invocation pattern and starts becoming a real installable operator command surface.

## Current note

The installed `chaseos` entrypoint now targets the canonical package-native parser in `runtime.cli.main:main`.
Both `chaseos.py` and `runtime/cli.py` remain available only as compatibility shims that import the same canonical parser.
