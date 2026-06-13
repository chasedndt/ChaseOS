# runtime/ — Lifecycle README

> Human-facing guide to the new runtime lifecycle direction in ChaseOS.

---

## What This Covers

This file explains the difference between:
- runtime inspection
- runtime lifecycle control

That distinction matters because ChaseOS now has a growing runtime inspection surface, but it does not yet fully control live runtime processes.

---

## Runtime Inspection vs Runtime Lifecycle

### Runtime inspection
Current examples:
- resolve runtime state
- show runtime status
- inspect Gate policy

These commands tell you what the runtime posture is.

### Runtime lifecycle
Future examples:
- start OpenClaw
- stop OpenClaw
- restart OpenClaw
- restart Hermes
- check runtime health

These commands affect live runtime processes or services.

---

## Important Current Truth

ChaseOS does **not yet** fully own runtime lifecycle management.

Current local CLI footholds are still mainly about:
- status
- resolve
- policy inspection
- local CLI unification seam

So if you ask whether ChaseOS can already restart OpenClaw or Hermes directly through its own true `chaseos` command family, the honest answer is:
- not yet

---

## Intended Future Command Shape

```text
chaseos runtime start <runtime>
chaseos runtime stop <runtime>
chaseos runtime restart <runtime>
chaseos runtime health <runtime>
```

Planned first runtimes in scope:
- `openclaw`
- `hermes`

---

## Why This Matters to ChaseOS

If ChaseOS is becoming the operating system and control plane for bounded runtime lanes, then it should eventually be able to:
- inspect runtimes
- understand runtimes
- manage runtime lifecycle

That is the natural next layer after runtime-state and command-surface work.

---

## Recommended Reading

- `06_AGENTS/ChaseOS-Runtime-Lifecycle-Contract.md`
- `06_AGENTS/ChaseOS-CLI-Integration-Seam.md`
- `06_AGENTS/ChaseOS-Runtime-Command-Contract.md`
- `runtime/CLI-README.md`
