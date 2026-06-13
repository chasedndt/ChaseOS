# runtime/bindings/ — Runtime Bootstrap and User Attachment Contracts

> Machine-readable bootstrap and attachment contracts for ChaseOS runtimes.
> This folder defines how a runtime discovers its platform context, runtime identity, machine-local bindings, and detachable user attachment posture.

---

## Purpose

This layer exists to bridge three already-existing ChaseOS concerns:
- constitutional governance in `06_AGENTS/` and `runtime/policy/`
- runtime-specific identity/orientation in `runtime/memory/nav/`
- core vs personal separation described in `CORE_MANIFEST.md`

It is not a new authority layer.
It is a bootstrap and attachment layer.

---

## Design Goal

Any runtime or harness launched under ChaseOS should be able to determine:
- what platform it is running on
- where the repo root is
- which runtime identity files apply to it
- whether machine-local bindings are present
- whether a personal user is attached
- whether it should run in core-only, runtime-only, or attached-personal mode

---

## Recommended Artifacts

- `runtime-bootstrap.schema.json` — schema for platform/runtime bootstrap records
- `user-attachment.schema.json` — schema for detachable user attachment records
- future runtime- or machine-local binding files that conform to those schemas

Additional GitHub-safe example:

- `discord_instance_bindings.example.yaml` - copy to `.chaseos/discord_instance_bindings.yaml` for local Discord server/user/bot/channel bindings.

Validator/status surface:

- `runtime/discord_bindings.py` validates `.chaseos/discord_instance_bindings.yaml` without returning raw IDs or secrets.
- `python -m runtime.cli.main setup discord validate --json` is the CLI entry point.
- Studio Dashboard consumes the same validator through `discord_control_plane_panel`.

---

## Separation Rule

Files in this folder should remain GitHub-safe unless explicitly declared machine-local.

Portable runtime bootstrap rules belong here.
Private user identity, secrets, and account bindings do not.

For Discord, this folder contains only the example template. The live local file belongs at `.chaseos/discord_instance_bindings.yaml` and must remain ignored by Git. Webhook URLs and bot tokens are secrets and belong in `.env` or another approved local secret source.

---

## Relationship to Other Layers

| Layer | Role |
|------|------|
| `06_AGENTS/Agent-Control-Plane.md` | constitutional governance |
| `06_AGENTS/Permission-Matrix.md` | permission ceilings |
| `runtime/policy/adapters/*.yaml` | per-adapter manifests |
| `runtime/memory/nav/*/` | per-runtime self-orientation |
| `CORE_MANIFEST.md` | public vs personal export boundary |
| `04_SOPS/Discord-Control-Plane-Setup-SOP.md` | local Discord binding setup and verification |

This folder helps a runtime move through those layers in a consistent startup order.

---

## Startup Order (Target Model)

1. Load constitutional rules.
2. Load adapter manifest and runtime identity profile.
3. Load runtime bootstrap record.
4. Discover whether machine-local bindings exist.
5. Discover whether detachable personal user attachment exists.
6. Expose current posture: core-only, runtime-only, or attached-personal.

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Portable-Runtime-Identity-and-User-Binding]] · [[Runtime-Navigation-Map]] · [[CORE_MANIFEST]]*
