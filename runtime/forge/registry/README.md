# Chaser Forge Extension Registry

This directory is the metadata registry for Chaser Forge extension modules.

Current status: PARTIAL / approved rollback executor foundation.

Generated extensions may not write this registry directly.

Sandbox registry mutation requires an approved Forge sandbox artifact, exact request digest, clean manifest and target-path revalidation, no existing exact-once marker, and no existing extension-owned target files.

Live-install approval packet writing is modeled and remains request-only. The live approval surface requires a sandbox-installed registry entry, matching manifest digest, completed sandbox exact-once marker, existing extension-owned target files, and no future live exact-once marker before writing a pending artifact under `07_LOGS/Agent-Activity/_forge_live_install_approvals/`.

Approved live install execution is now modeled as registry promotion only. It requires an approved live approval artifact, exact request digest, matching operator approval statement, unconsumed approval state, valid sandbox proof, and no existing live exact-once marker before it writes live registry metadata, a live marker, and consumed approval metadata. It does not write extension files, protected core paths, Studio shell files, runtime policy, schedules, Agent Bus tasks, providers, or credentials.

Rollback approval packet writing is modeled and remains request-only. The rollback approval surface requires a live-installed registry entry, matching manifest digest, completed live exact-once marker, existing extension-owned target files, and no future rollback exact-once marker before writing a pending artifact under `07_LOGS/Agent-Activity/_forge_rollback_approvals/`.

Approved rollback execution is now modeled as registry rollback only. It requires an approved rollback approval artifact, exact request digest, matching operator approval statement, unconsumed approval state, valid live proof, and no existing rollback exact-once marker before it writes rollback registry metadata, a rollback marker, and consumed approval metadata. It returns the registry entry to `sandbox_installed` / `sandbox`, preserves prior live execution history, and does not delete extension files, write protected core paths, patch Studio shell files, mutate runtime policy, schedules, Agent Bus tasks, providers, or credentials.
