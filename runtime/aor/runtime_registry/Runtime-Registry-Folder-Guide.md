# Runtime Registry — Folder Guide

Machine-readable registry for ChaseOS runtime instances.

Each runtime gets its own folder:
- `runtime/aor/runtime_registry/<runtime_id>/registry_entry.yaml`

This layer records:
- runtime identity
- provider
- surface type
- adapter binding posture
- trust ceiling
- allowed task families
- lifecycle state
- initial scope posture

This registry is descriptive/governing metadata.
It does not itself grant execution authority.
Policy binding and lifecycle progression remain separate bounded steps.
