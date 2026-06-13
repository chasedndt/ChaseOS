# runtime/ — Top-Level Command Notes

## Current Best Operator Shape

The best current operator-facing command pattern is now:

```powershell
chaseos runtime status --refresh --json
chaseos runtime resolve
chaseos runtime health --runtime openclaw
chaseos gate validate
chaseos agent-bus status
chaseos agent-bus runtimes
chaseos agent-bus route operator-briefing
```

Compatibility invocation paths still exist through the same parser:
- `python chaseos.py ...`
- `python runtime\cli.py ...`
- `python -m runtime.cli.main ...`

This is a better shape than calling subsystem-local paths directly.

## Why `runtime health` Is Better Than Top-Level `health`

Normalizing health under the `runtime` family keeps the shell tree cleaner.

Better shape:
- `chaseos runtime status`
- `chaseos runtime resolve`
- `chaseos runtime health`

Worse shape:
- `chaseos runtime ...`
- `chaseos health ...`

Health belongs to the runtime family because it is part of runtime lifecycle/inspection behavior.

## Transitional Compatibility

A temporary top-level `health` alias can still exist during transition.
But the preferred operator-facing form should now be the runtime-family shape.

## Current Reality

This is no longer only a repo-local promoted entrypoint phase.
The canonical installed/operator CLI entrypoint is now `runtime.cli.main:main`, with installed `chaseos` / `chase` pointing there directly.
`chaseos.py` and `runtime/cli.py` remain as compatibility shims only.

Current caveat:
- `runtime status` is the strongest current promoted path
- `runtime health` is now normalized correctly under the runtime family, but still needs additional promoted-path hardening before it behaves as a fully reliable bounded top-level command
- `agent-bus` promotion is now real enough for routing and task-lifecycle dogfooding, and the focused AOR review-coordination lane is now green under no-`PyYAML` fallback conditions
- schedule loading, graph-hygiene frontmatter scanning, and graph extraction have now also been hardened off hard import-time `yaml` dependency
- the next highest-impact implementation gap is the remaining maintenance-workflow and test-only surfaces that still hard-import `yaml`

*Graph links: [[06_AGENTS/Runtime-InterAgent-Coordination-Bus|Runtime-InterAgent-Coordination-Bus]] · [[Control-Plane-Ingress-and-Bus-Translation]] · [[ChaseOS-Commands-and-CLI-Surfaces]]*
