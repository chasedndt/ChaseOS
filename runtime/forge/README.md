# Chaser Forge Marketplace And Install Foundation

Chaser Forge is the governed builder lane for installable ChaseOS extension modules. It may create extension-owned manifests, UI definitions, workflow templates, data schemas, and preview artifacts, but generated extensions do not receive authority to rewrite ChaseOS core.

Current status: COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, LOCAL LIVE-INDEX INPUT PREFILL BUILT, NO-DOMAIN CLOSEOUT VERIFIED, DOMAIN SELECTED / PUBLIC STATIC INDEX UPLOAD PENDING / LIVE FETCH APPROVAL-GATED. The implementation includes approved extension points, manifest validation, protected-core guards, digest-gated sandbox/live/rollback approval requests, source-specific decision handoff/form, decision-bound executor consumption, sandbox registry write, live registry promotion, rollback registry demotion, local marketplace package export/import preview, ChaseOS-owned local public catalog publish, read-only Local Marketplace Library inspection, digest-bound remote distribution index artifacts, verified remote listing ingest into the local catalog, digest-gated hosted export bundles for manual static-host mirroring, digest-gated static-host publication proof directories with upload-ready files, digest-gated static-host upload handoff artifacts for operator manual upload, digest-gated static-host upload receipt artifacts for operator proof after manual upload, digest-gated published static index registration artifacts for operator-declared public index URLs, digest-gated local live `index.json` input prefill artifacts, read-only live `index.json` input readiness for the domain-selected/static-index-upload-pending hosted verification lane, no-domain closeout audit, marketplace-import approval, marketplace-import-to-sandbox approval bridge, approved marketplace install execution through the existing sandbox registry writer, Studio panel controls, Approval Center routing, visual QA, proof deck, live StudioAPI control proof, operator-use Studio button proof with direct closeout smoke evidence, local library Studio-use smoke evidence, remote distribution direct smoke evidence, hosted export bundle direct smoke evidence, static-host publication direct smoke evidence, static-host upload handoff direct smoke evidence, static-host upload receipt direct smoke evidence, published static index registration direct smoke evidence, completion audit, and canonical feature/family registration. Studio now marks the public hosted marketplace lane as `Coming soon` while static upload/fetch approval is pending. `runtime.studio.chaser_forge_no_domain_closeout_audit` verifies zero code-owned no-domain blockers: Studio is wired, the prefilled packet and Markdown handoff exist, the static publication files exist, the local `index.json` SHA-256 matches the packet, and live fetch authority remains blocked. Live hosted fetch verification remains deferred until `https://chaseos.ai/forge/index.json` is uploaded, digest-verified, and a final approval packet is supplied. Ambient remote marketplace calls, network upload, network fetch verification of operator-provided hosted URLs, untrusted third-party package exchange, payment/license mutation, external registry mutation, unauthorized auto-install without the existing approval chain, generic Approval Center write controls, provider/model calls, Agent Bus dispatch, protected-core mutation, Pulse memory, Personal Map, R&D truth-state, and broad canonical mutation remain blocked by design.

Implemented in this pass:

- Approved extension point registry.
- Manifest validator for schema, id, route, UI, workflow, agent, data schema, permission, preview, rollback, and target-path checks.
- Protected-core target path guard.
- Demo manifest that validates cleanly.
- Studio preview panel model and read-only UI hook.
- Registry read model at `runtime/forge/registry/extensions.json`.
- Digest-gated sandbox approval request surface that can write one pending approval artifact under `07_LOGS/Agent-Activity/_forge_sandbox_approvals/` only when the exact request digest is supplied.
- Approved sandbox registry writer that requires an approved artifact, exact digest, unconsumed approval, matching operator confirmation statement, valid target paths, no existing exact-once marker, no existing registry entry, and no existing extension-owned target files before it writes.
- Live-install approval request surface that requires sandbox proof before it can write one pending live approval artifact under `07_LOGS/Agent-Activity/_forge_live_install_approvals/`.
- Approved live install executor that requires sandbox proof, an approved live approval artifact, exact digest, unconsumed approval, matching operator confirmation statement, and no live exact-once marker before it promotes the existing sandbox registry entry to live state.
- Rollback approval request surface that requires live proof before it can write one pending rollback approval artifact under `07_LOGS/Agent-Activity/_forge_rollback_approvals/`.
- Approved rollback executor that requires live proof, an approved rollback approval artifact, exact digest, unconsumed approval, matching operator confirmation statement, and no rollback exact-once marker before it returns the existing live registry entry to sandbox state without deleting extension files.
- Native read-only Approval Center routing for Forge sandbox, live-install, and rollback approval request artifacts. The routing displays lifecycle state, request digest, touch set, source refs, and safety posture only; it does not approve, consume, execute, install, or roll back Forge items.
- Source-specific Forge approval decision handoff at `runtime.forge.approval_decision.build_forge_approval_decision_handoff`, exposed through Studio as `review_chaser_forge_approval_decision`. The handoff can record an approved/rejected operator decision for one pending Forge approval artifact, write a matching decision audit artifact under that source's `_decisions/` folder, and update the source approval artifact decision fields. It does not consume approvals, reserve exact-once markers, execute Forge lifecycle actions, mutate the registry, write/delete extension files, patch Studio, mutate protected core, call providers, dispatch Agent Bus tasks, or mutate canonical state.
- Source-specific Forge operator decision form at `runtime.forge.approval_decision_form.build_forge_approval_decision_form`, exposed through Studio as `get_chaser_forge_approval_decision_form`. The form is a read-only contract for one pending Forge approval artifact. It prepares approved/rejected decision options, exact copyable operator statements, expected request digest, and the source-specific `review_chaser_forge_approval_decision` submit payload. It does not record the decision, mutate the source artifact, write a decision sidecar, consume approvals, execute Forge lifecycle actions, mutate the registry, write/delete extension files, reserve exact-once markers, or grant generic Approval Center authority.
- Decision-bound executor consumption validation for sandbox, live-install, and rollback executors. An `approved` Forge approval artifact is no longer sufficient by itself; the executor also requires `approval_decision_recorded=true`, a matching `forge_approval_decision_handoff` sidecar under the correct source `_decisions/` folder, matching source artifact path, packet id, request digest, approval scope, record type, digest recomputation, and no decision-sidecar execution/registry/marker/write authority. Manually mutated approved JSON without the decision sidecar now fails closed.
- Static rendered Approval Center lifecycle proof for Forge approval visibility and source-specific decision handoff visibility. The proof uses a temporary fixture vault, production frontend renderer, desktop/mobile screenshots, and status-count rendering to verify pending, approved-pending-execution, consumed, rejected, invalid lifecycle states, and the source-specific `review_chaser_forge_approval_decision` handoff without persisting fixture approval artifacts in the real vault.
- Log-only Chaser Forge proof deck under `07_LOGS/Workflow-Proofs/2026-05-21_chaser-forge-marketplace-proof-deck.*`. The refreshed deck packages the existing implementation, routing, Approval Center lifecycle QA, Studio proof-deck clickthrough QA, marketplace bridge visual QA, full live StudioAPI marketplace install proof, operator-use smoke, and Local Marketplace Library smoke into Markdown/JSON without granting approval decision, approval consumption, Forge execution, provider/model, schedule, Agent Bus, protected-core, Pulse memory, Personal Map, R&D truth-state, or canonical authority to the deck itself.
- Native Studio Chaser Forge panel proof-deck section. The panel now surfaces proof deck status, Markdown/JSON artifact paths, slide statuses including `Marketplace Publish And Install`, and next-pass posture as read-only data from `build_chaser_forge_panel`; the section does not write proof artifacts, approve/consume requests, execute Forge lifecycle actions, mutate the registry, or grant new authority.
- Local Forge marketplace publish/install foundation at `runtime.forge.marketplace`. The export surface builds a validated, digest-bound local package preview for manifests that declare `marketplace.template`; the package write surface can write that same package only when the exact preview digest is supplied; the catalog publish surface writes or reuses one local public catalog listing only when the exact listing digest is supplied; the import preview recomputes package and manifest digests without installing anything; the install executor consumes approved marketplace-import and sandbox approvals through source-specific decisions before delegating registry/file writes to the existing sandbox registry writer. Remote marketplace calls, third-party package exchange, unauthorized install, provider/model calls, Agent Bus dispatch, protected-core mutation, and canonical mutation remain blocked.
- Read-only Local Marketplace Library at `runtime.forge.marketplace.build_forge_marketplace_local_library`, exposed through Studio as `get_chaser_forge_marketplace_local_library`. It joins the local catalog and Forge registry so Studio can show listed-not-installed, listed-installed, and installed-unlisted package state, including registry status and target-path evidence. It writes no package, catalog, approval, registry, extension file, exact-once marker, remote exchange, or install side effect.
- Governed remote distribution foundation at `runtime.forge.marketplace.build_forge_marketplace_remote_distribution`, `build_forge_marketplace_remote_ingest_preview`, and `build_forge_marketplace_remote_listing_ingest`, exposed through Studio as `get_chaser_forge_marketplace_remote_distribution`, `write_chaser_forge_marketplace_remote_index`, and `ingest_chaser_forge_marketplace_remote_listing`. It writes digest-gated portable remote index artifacts, verifies trusted publisher id/fingerprint and attestation, validates listing/package/manifest digests, and can ingest a verified remote listing into the local catalog with exact operator confirmation. It writes no registry entry, extension file, approval artifact, exact-once marker, network request, payment mutation, or license checkout.
- Governed hosted export bundle at `runtime.forge.marketplace.build_forge_marketplace_hosted_export_bundle`, exposed through Studio as `get_chaser_forge_marketplace_hosted_export_bundle` and `write_chaser_forge_marketplace_hosted_export_bundle`. It writes digest-gated portable bundle artifacts for manual static-host mirroring, including the verified remote index, publication manifest, and operator readme. It writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network request, credential, payment mutation, license checkout, or package install.
- Governed static-host publication proof at `runtime.forge.marketplace.build_forge_marketplace_static_host_publication`, exposed through Studio as `get_chaser_forge_marketplace_static_host_publication` and `write_chaser_forge_marketplace_static_host_publication`. It writes digest-gated upload-ready local static files (`index.json`, `README.md`, `hosted-bundle.json`, `publication-manifest.json`, and `checksums.json`) from a verified hosted bundle. It writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network upload, external registry mutation, credential, payment mutation, license checkout, or package install.
- Governed static-host upload handoff at `runtime.forge.marketplace.build_forge_marketplace_static_host_upload_handoff`, exposed through Studio as `get_chaser_forge_marketplace_static_host_upload_handoff` and `write_chaser_forge_marketplace_static_host_upload_handoff`. It writes digest-gated local JSON/Markdown handoff artifacts for an operator to manually upload the already generated static-host publication files. It writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network upload, external registry mutation, credential, payment mutation, license checkout, or package install.
- Governed static-host upload receipt at `runtime.forge.marketplace.build_forge_marketplace_static_host_upload_receipt`, exposed through Studio as `get_chaser_forge_marketplace_static_host_upload_receipt` and `write_chaser_forge_marketplace_static_host_upload_receipt`. It writes digest-gated local JSON/Markdown receipt artifacts recording an exact operator manual upload claim and operator-provided static-host base URL after the upload handoff exists. It writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network fetch, network upload, external registry mutation, credential, payment mutation, license checkout, or package install.
- Governed published static index registration at `runtime.forge.marketplace.build_forge_marketplace_published_static_index_registration`, exposed through Studio as `get_chaser_forge_marketplace_published_static_index_registration` and `write_chaser_forge_marketplace_published_static_index_registration`. It writes digest-gated local JSON/Markdown registration artifacts recording an operator-declared public index URL after the upload receipt exists. It writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, live URL fetch, network upload, external registry mutation, credential, payment mutation, license checkout, or package install.
- Governed live index input prefill at `runtime.forge.marketplace.build_forge_marketplace_live_index_input_prefill`, exposed through Studio as `get_chaser_forge_marketplace_live_index_input_prefill` and `write_chaser_forge_marketplace_live_index_input_prefill`. It writes a digest-gated local JSON packet and Markdown handoff under `07_LOGS/Operator-Briefs/Chaser-Forge-Live-Index-Input-Prefills/`, with local static-publication directory and `index.json` SHA-256 filled while domain/upload/fetch approval fields remain explicitly pending. It writes no live URL fetch, network upload, external registry mutation, credential, payment mutation, license checkout, package install, provider/model call, Agent Bus dispatch, protected-core mutation, or canonical state.
- Read-only live index input readiness at `runtime.forge.marketplace.build_forge_marketplace_live_index_input_readiness`, exposed through Studio as `get_chaser_forge_marketplace_live_index_input_readiness`. It validates the future hosted `index.json` packet locally, detects the current domain-selected/static-index-upload-pending deferral, rejects generic trusted homepages that are not Chaser Forge `/index.json` URLs, and inspects local static publication candidates/checksums when present. It writes no artifacts and performs no live URL fetch, network upload, external registry mutation, credential use, payment/license mutation, package install, provider/model call, Agent Bus dispatch, protected-core mutation, or canonical write.
- Marketplace import sandbox approval request surface at `runtime.forge.marketplace.build_forge_marketplace_import_sandbox_approval`, exposed through Studio as `request_chaser_forge_marketplace_import_sandbox_approval`. It builds a digest-gated pending operator review artifact under `07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/` for a local package import sandbox review. It can reuse an existing matching pending artifact and can feed the source-specific `marketplace-import` decision handoff. It does not install the package, request sandbox installation, mutate the Forge registry, write extension files, consume approvals, reserve exact-once markers, call providers/connectors, dispatch Agent Bus tasks, or mutate protected core/canonical state.
- Marketplace import sandbox request bridge at `runtime.forge.marketplace.build_forge_marketplace_import_sandbox_request`, exposed through Studio as `get_chaser_forge_marketplace_import_sandbox_request` and `request_chaser_forge_marketplace_import_sandbox_request`. It validates an approved, unconsumed `marketplace-import` review artifact plus its source-specific decision sidecar, then can write or reuse one normal pending Forge sandbox approval request under `_forge_sandbox_approvals/` when the exact bridge digest is supplied. It does not install the package, consume the marketplace-import approval, consume the sandbox approval, mutate the Forge registry, write extension files, reserve exact-once markers, call providers/connectors, dispatch Agent Bus tasks, or mutate protected core/canonical state.
- Static Studio visual QA for marketplace publish/install under `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-publish-install-visual-qa/`. The proof renders the production Chaser Forge panel with a temporary approved marketplace-import fixture, captures desktop/mobile screenshots, verifies the `Marketplace Publish And Install` section, bridge APIs, written pending sandbox request state, publish/install controls, and local catalog/install posture, then removes the fixture. It writes visual evidence only and does not persist real-vault marketplace-import approval artifacts, write real-vault sandbox approval requests, consume approvals, install packages, mutate registry/extension files, or grant provider/model, Agent Bus, protected-core, memory, R&D truth-state, or canonical authority.
- Live StudioAPI control proof under `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-live-studio-control-proof/`. The proof drives the real StudioAPI methods through sandbox approval/decision/execution, live approval/decision/execution, rollback approval/decision/execution, local marketplace package write/import preview, local catalog publish, marketplace-import approval/decision, marketplace-import bridge, sandbox approval/decision, and approved marketplace install execution in temporary fixture vaults. It verifies digest gates, decision-sidecar requirements, exact-once consumption for lifecycle and marketplace install executors, registry return to sandbox after rollback, retained extension-owned files, duplicate install blocking, and approved marketplace install registry/file/marker writes. It writes only the proof report in the real vault.
- Operator-use Studio button proof under `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-operator-use-studio-proof/` and direct closeout smoke evidence under `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-marketplace-operator-use-closeout-smoke/`. The production Chaser Forge panel route now preserves visible final status after publish/install refreshes, and the proof verifies the `Publish Demo Package` and `Run Demo Marketplace Install` button flow, required StudioAPI calls, operator confirmations, fixture registry write, extension-owned file write, and exact-once marker write. The direct smoke path replaces the hanging pytest route with `python -u`, faulthandler timeout, explicit JSON output, and deterministic fixture cleanup.
- Local Marketplace Library Studio-use smoke evidence under `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-local-marketplace-library-studio-use-smoke/`. The smoke drives the StudioAPI publish/import/sandbox/install chain in a fixture vault, verifies the library before and after install, confirms panel/API/frontend wiring, confirms read-only/remote-exchange/unauthorized-auto-install blocks, confirms real-vault registry/catalog files are unchanged, and removes the fixture.
- Remote Distribution, Hosted Export Bundle, Static Host Publication, Static Host Upload Handoff, Static Host Upload Receipt, and Published Static Index Registration direct smoke evidence now cover the public-catalog export lane through local/manual publication registration. The published static index registration smoke lives under `07_LOGS/Studio-Visual-QA/2026-05-24-chaser-forge-published-static-index-registration-smoke/` and verifies exact remote/hosted/static/upload-handoff/upload-receipt/registration digest gates, exact operator receipt and registration statement enforcement, local JSON/Markdown registration artifacts, panel/frontend wiring, unchanged real-vault registry/catalog/distribution artifact paths, and no live URL fetch/upload, external registry mutation, payment mutation, license checkout, or package install.
- Completion audit under `runtime.forge.completion_audit` and `07_LOGS/Workflow-Proofs/2026-05-21_chaser-forge-marketplace-completion-audit.*`. The audit checks the panel summary, proof deck, live StudioAPI proof, operator-use smoke, Local Marketplace Library smoke, Remote Distribution smoke, Hosted Export Bundle smoke, Static Host Publication smoke, Static Host Upload Handoff smoke, Static Host Upload Receipt smoke, Published Static Index Registration smoke, and canonical Feature Register / Feature Fit Register rows before marking the governed marketplace and Studio UI implemented and registered.

Sandbox approval requests are not installs. They do not write registry entries, extension files, exact-once markers, live install state, or protected core paths.

The sandbox registry writer is not a live install. It writes only:

- `runtime/forge/registry/extensions.json`
- extension-owned target files under `extensions/<extension-id>/`
- an exact-once marker under `07_LOGS/Agent-Activity/_forge_sandbox_approvals/_sandbox_markers/`
- consumed status metadata on the approved sandbox artifact

It does not write protected core paths, Studio shell files, runtime policy, schedules, Agent Bus tasks, provider calls, secrets, credentials, or live install state.

Live-install approval requests are not live installs. The live approval request surface verifies:

- the Forge registry contains a `sandbox_installed` entry for the manifest
- the manifest digest still matches the sandbox registry entry
- the sandbox exact-once marker exists, is completed, and matches the registry entry
- extension-owned target files still exist
- no future live exact-once marker already exists

When those checks pass and the exact request digest is supplied, it writes only a pending live approval artifact. It does not execute live install, mutate the registry, write extension files, reserve a live marker, patch Studio, mutate protected core, call providers, dispatch Agent Bus tasks, or read credentials.

The approved live install executor is a registry promotion executor, not an extension-file writer. It writes only:

- live registry metadata on the existing sandbox-installed registry entry
- an exact-once live marker under `07_LOGS/Agent-Activity/_forge_live_install_approvals/_live_install_markers/`
- consumed status metadata on the approved live approval artifact

It does not write extension-owned files, protected core paths, Studio shell files, runtime policy, schedules, Agent Bus tasks, provider calls, secrets, credentials, or rollback state.

Rollback approval requests are not rollbacks. The rollback approval request surface verifies:

- the Forge registry contains a `live_installed` entry for the manifest
- the manifest digest still matches the live registry entry
- the live exact-once marker exists, is completed, and matches the registry entry
- extension-owned target files still exist
- no future rollback exact-once marker already exists

When those checks pass and the exact request digest is supplied, it writes only a pending rollback approval artifact. It does not execute rollback, mutate the registry, delete extension files, reserve a rollback marker, patch Studio, mutate protected core, call providers, dispatch Agent Bus tasks, or read credentials.

The approved rollback executor is a registry rollback executor, not an extension-file delete path. It writes only:

- rollback metadata on the existing live-installed registry entry, returning it to `sandbox_installed` / `sandbox`
- an exact-once rollback marker under `07_LOGS/Agent-Activity/_forge_rollback_approvals/_rollback_markers/`
- consumed status metadata on the approved rollback approval artifact

It retains extension-owned files under `extensions/<extension-id>/` and preserves the prior live execution in registry history. It does not delete extension files, write protected core paths, patch Studio shell files, mutate runtime policy, schedules, Agent Bus tasks, providers, external connectors, secrets, credentials, Pulse memory, Personal Map, R&D truth-state, or broad canonical state.

Forge approval decision handoff is not approval consumption. For sandbox, live-install, and rollback approval artifacts, the handoff requires:

- a pending Forge approval artifact directly under the matching source approval root
- matching record type, approval scope, packet id, request digest, unconsumed state, approved material, and operator confirmation text
- an exact expected request digest supplied by the caller for writes
- an exact operator approval statement matching the generated confirmation text, or an exact generated rejection statement

When all gates pass and `write_decision=True`, it writes only:

- a decision audit artifact under the matching `_decisions/` folder
- approved/rejected decision metadata back to the source Forge approval artifact

It leaves `approval_consumed=false` and writes no registry entries, extension files, exact-once markers, protected-core paths, Studio shell files, runtime policy, schedules, Agent Bus tasks, providers/connectors, secrets, credentials, Pulse memory, Personal Map, R&D truth-state, or canonical state. Source-specific executors now revalidate the recorded decision sidecar digest and source binding in addition to the approved artifact before any later lifecycle execution.

## Operator Decision Form

The Forge operator decision form is a read-only helper over the source-specific handoff. It is built by:

```text
runtime.forge.approval_decision_form.build_forge_approval_decision_form
```

Studio exposes the form through:

```text
get_chaser_forge_approval_decision_form
```

For one pending Forge approval artifact, the form returns:

- approved and rejected decision options
- the exact operator statement required for each decision
- the expected request digest
- the future decision sidecar path preview
- a submit payload for `review_chaser_forge_approval_decision`
- blocked authority flags showing no approval consumption, Forge execution, registry write, extension file write/delete, exact-once marker reservation, provider/model call, Agent Bus dispatch, secret/credential read, Pulse memory, Personal Map, R&D truth-state, or canonical mutation

The form does not write anything. It remains source-specific and does not add generic Approval Center approve/reject controls.

## Marketplace Publish And Install Foundation

The Forge marketplace foundation is ChaseOS-owned local package publish and governed install plumbing. It is built by:

```text
runtime.forge.marketplace.build_forge_marketplace_export_package
runtime.forge.marketplace.build_forge_marketplace_catalog
runtime.forge.marketplace.build_forge_marketplace_publish
runtime.forge.marketplace.build_forge_marketplace_local_library
runtime.forge.marketplace.build_forge_marketplace_remote_distribution
runtime.forge.marketplace.build_forge_marketplace_remote_ingest_preview
runtime.forge.marketplace.build_forge_marketplace_remote_listing_ingest
runtime.forge.marketplace.build_forge_marketplace_hosted_export_bundle
runtime.forge.marketplace.build_forge_marketplace_static_host_publication
runtime.forge.marketplace.build_forge_marketplace_static_host_upload_handoff
runtime.forge.marketplace.build_forge_marketplace_static_host_upload_receipt
runtime.forge.marketplace.build_forge_marketplace_published_static_index_registration
runtime.forge.marketplace.build_forge_marketplace_live_index_input_prefill
runtime.forge.marketplace.build_forge_marketplace_live_index_input_readiness
runtime.forge.marketplace.build_forge_marketplace_import_preview
runtime.forge.marketplace.build_forge_marketplace_import_sandbox_approval
runtime.forge.marketplace.build_forge_marketplace_import_sandbox_request
runtime.forge.marketplace.build_forge_marketplace_install_execution
```

Studio exposes:

```text
get_chaser_forge_marketplace_export_package
write_chaser_forge_marketplace_export_package
get_chaser_forge_marketplace_catalog
get_chaser_forge_marketplace_publish_preview
publish_chaser_forge_marketplace_package
get_chaser_forge_marketplace_local_library
get_chaser_forge_marketplace_remote_distribution
write_chaser_forge_marketplace_remote_index
ingest_chaser_forge_marketplace_remote_listing
get_chaser_forge_marketplace_hosted_export_bundle
write_chaser_forge_marketplace_hosted_export_bundle
get_chaser_forge_marketplace_static_host_publication
write_chaser_forge_marketplace_static_host_publication
get_chaser_forge_marketplace_static_host_upload_handoff
write_chaser_forge_marketplace_static_host_upload_handoff
get_chaser_forge_marketplace_static_host_upload_receipt
write_chaser_forge_marketplace_static_host_upload_receipt
get_chaser_forge_marketplace_published_static_index_registration
write_chaser_forge_marketplace_published_static_index_registration
get_chaser_forge_marketplace_live_index_input_prefill
write_chaser_forge_marketplace_live_index_input_prefill
get_chaser_forge_marketplace_live_index_input_readiness
get_chaser_forge_marketplace_import_preview
request_chaser_forge_marketplace_import_sandbox_approval
get_chaser_forge_marketplace_import_sandbox_request
request_chaser_forge_marketplace_import_sandbox_request
execute_chaser_forge_marketplace_install
```

The export preview validates the demo manifest, requires a `marketplace.template` extension point, packages the manifest plus permission disclosure and import contract, and returns a stable `package_digest_sha256`. The package write path writes only under:

```text
07_LOGS/Workflow-Proofs/Forge-Marketplace-Packages/
```

and only when `expected_package_digest` matches the preview digest. Import preview accepts an inline package payload or a vault-local JSON package path, recomputes the package digest and embedded manifest digest, revalidates the manifest, and reports future import requirements.

The local public catalog lives at:

```text
runtime/forge/registry/marketplace-catalog.json
```

Catalog publish writes or reuses one listing only when `expected_listing_digest` matches the preview listing digest. The listing points to the stable package digest and remains local to the vault; no remote marketplace call or third-party package exchange is performed.

The Local Marketplace Library is read-only. It joins `runtime/forge/registry/marketplace-catalog.json` with `runtime/forge/registry/extensions.json`, returning catalog counts, installed counts, listed-installed state, listed-not-installed state, installed-unlisted state, registry status, install environment, target-path evidence, and blocked authority flags. It does not publish, install, consume approvals, write registry/files, reserve markers, call a remote marketplace, or perform third-party exchange.

The Remote Distribution foundation writes digest-gated index artifacts under:

```text
07_LOGS/Workflow-Proofs/Forge-Marketplace-Remote-Indexes/
```

Only exact remote index digests can write an index. Ingest requires a matching index digest, matching listing digest, trusted publisher id/fingerprint, matching publisher attestation digest, valid package/import preview, and the exact generated operator confirmation. The ingest writes or reuses one local catalog listing only; it does not install packages, mutate the Forge registry, write extension files, consume approvals, reserve markers, perform network fetch/publish, mutate payment state, or perform license checkout.

The Hosted Export Bundle foundation writes digest-gated manual static-host bundle artifacts under:

```text
07_LOGS/Workflow-Proofs/Forge-Marketplace-Hosted-Bundles/
```

Only exact hosted bundle digests and source remote index digests can write a bundle. The bundle contains the verified remote index payload, publication manifest, and operator readme for later manual mirroring. It does not publish to a network, include credentials, mutate payment/license state, install packages, write the Forge registry, write extension files, consume approvals, or reserve markers.

The Static Host Publication proof writes upload-ready static-host files under:

```text
07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Publications/
```

Only exact remote-index, hosted-bundle, and static-publication digests can write the proof directory. The directory contains `index.json`, `README.md`, `hosted-bundle.json`, `publication-manifest.json`, and `checksums.json` for operator-reviewed manual upload. It performs no network upload, external registry mutation, credential inclusion, payment/license mutation, package install, Forge registry write, extension file write, approval consumption, or exact-once marker reservation.

The Static Host Upload Handoff writes local operator handoff artifacts under:

```text
07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Handoffs/
```

Only exact remote-index, hosted-bundle, static-publication, and upload-handoff digests can write the handoff. The handoff records the expected static files, checksums, target host label/base URL metadata, and manual operator checklist as JSON and Markdown. It performs no network upload, external registry mutation, credential inclusion, payment/license mutation, package install, Forge registry write, extension file write, approval consumption, or exact-once marker reservation.

The Static Host Upload Receipt writes local operator receipt artifacts under:

```text
07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Receipts/
```

Only exact remote-index, hosted-bundle, static-publication, upload-handoff, and upload-receipt digests plus the exact generated operator receipt statement can write the receipt. The receipt records the operator-declared static-host base URL and manual upload claim as JSON and Markdown. It performs no network fetch, network upload, external registry mutation, credential inclusion, payment/license mutation, package install, Forge registry write, extension file write, approval consumption, or exact-once marker reservation. It is local operator proof, not live hosted URL verification.

The Published Static Index Registration writes local operator registration artifacts under:

```text
07_LOGS/Workflow-Proofs/Forge-Marketplace-Published-Static-Index-Registrations/
```

Only exact remote-index, hosted-bundle, static-publication, upload-handoff, upload-receipt, and registration digests plus the exact generated operator registration statement can write the registration. The registration records the operator-declared public index URL and binds it back to the upload receipt as JSON and Markdown. It performs no live URL fetch, network upload, external registry mutation, credential inclusion, payment/license mutation, package install, Forge registry write, extension file write, approval consumption, or exact-once marker reservation. It is local operator proof, not live hosted URL verification or external registry publication.

The Live Index Input Readiness surface is read-only and does not write artifacts. It reads the operator packet template at:

```text
07_LOGS/Operator-Briefs/2026-05-24-chaser-forge-live-index-json-input-packet-template.json
```

It checks whether the official-domain hosted `index.json` packet is still placeholder-filled, whether the handover marks the lane as deferred pending domain purchase, whether the URL shape is valid HTTPS ending in `/index.json`, whether a local static publication candidate exists, and whether the provided local `index.json` SHA-256 matches that candidate. It rejects generic trusted homepages because they do not prove Chaser Forge publication. It performs no network fetch; the future live fetch verification pass remains deferred until the official ChaseOS domain exists and the operator supplies the completed packet plus explicit bounded fetch approval.

The import sandbox approval request accepts the same local package contract, recomputes the package/import preview material, and returns a stable `request_digest_sha256`. When the caller supplies the exact request digest and write mode is requested, it writes or reuses one pending review artifact under:

```text
07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/
```

This artifact is a package-to-sandbox review request only. The source-specific decision handoff supports the `marketplace-import` family, but approval decision recording still does not install the package or consume an approval.

The marketplace import sandbox request bridge accepts one approved, unconsumed marketplace-import review artifact and requires the matching source-specific decision sidecar to pass digest/source-binding validation. Preview mode returns a bridge `request_digest_sha256` and a nested normal sandbox approval request preview. Write mode requires that exact bridge digest and writes or reuses one pending sandbox approval request under:

```text
07_LOGS/Agent-Activity/_forge_sandbox_approvals/
```

The bridge only creates the next review artifact. It does not consume the marketplace-import approval, consume the sandbox approval, execute the sandbox registry writer, mutate the Forge registry, write extension files, or reserve exact-once markers.

The marketplace install executor requires all of the following before it can execute:

- a package already published in the local marketplace catalog
- the exact listing digest and listing id
- an approved, unconsumed marketplace-import review artifact
- a source-specific `marketplace-import` decision sidecar
- the exact bridge request digest linking that import approval to the sandbox request
- an approved, unconsumed sandbox approval artifact
- a source-specific sandbox decision sidecar
- the exact sandbox request digest

When execution is requested, the marketplace install executor delegates registry/file writes to the existing approved sandbox registry writer, consumes the sandbox approval, consumes the marketplace-import approval, writes extension-owned files, writes the Forge registry, and reserves the sandbox exact-once marker. Ambient remote marketplace calls, untrusted third-party package exchange, unauthorized install without this approval chain, payment/license mutation, provider/model calls, Agent Bus dispatch, protected-core mutation, Pulse memory, Personal Map, R&D truth-state, and canonical mutation remain blocked.

## Decision-Bound Executor Consumption

The sandbox registry writer, live-install executor, and rollback executor now require the recorded source-specific decision sidecar before they can report execution readiness or consume an approval. The sidecar must:

- live under the matching Forge source `_decisions/` folder
- use record type `forge_approval_decision_handoff`
- be source-specific and not a generic Approval Center control
- carry `operator_decision=approved`
- match the source approval artifact path, packet id, request digest, approval scope, source record type, and source schema version
- recompute to the digest stored on the source artifact
- preserve `approval_consumed=false`, `forge_execution_allowed=false`, `registry_written=false`, `extension_files_written=[]`, and `exact_once_marker_reserved=false`

This closes the manual-mutation gap between decision handoff and executor consumption while preserving the separate executor authority boundary.

Generated extension files must stay under an extension-owned root such as `extensions/<extension-id>/`. Protected ChaseOS core paths, runtime policy, schedules, adapters, Agent Bus internals, Studio shell files, secrets, credentials, and protected governance docs are rejected by the validator.

The Chaser Forge proof deck is generated by:

```powershell
python -m runtime.forge.proof_deck --vault-root . --write --json
```

The command reads existing Forge build logs, current docs, the static Approval Center lifecycle report, the Studio proof-deck clickthrough report, the marketplace import sandbox request bridge visual QA report, the live StudioAPI control proof, the operator-use smoke, and the Local Marketplace Library smoke. It writes proof artifacts only under `07_LOGS/Workflow-Proofs/` when `--write` is explicit.

The live StudioAPI control proof is generated by:

```powershell
python -m runtime.studio.chaser_forge_live_studio_control_proof --vault-root . --json
```

The operator-use Studio button proof is generated by:

```powershell
python -m runtime.studio.chaser_forge_marketplace_operator_use_visual_qa --vault-root . --json
```

The direct closeout smoke path for this proof is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_marketplace_operator_use_closeout_smoke --vault-root . --timeout-seconds 30 --json
```

The smoke command intentionally bypasses pytest/Playwright test collection hangs and emits an immediate JSON result with a faulthandler timeout.

The Local Marketplace Library Studio-use smoke is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_local_marketplace_library_smoke --vault-root . --timeout-seconds 30 --json
```

This smoke intentionally uses direct StudioAPI calls instead of the hanging visual test route. It emits explicit JSON, verifies library readiness before and after approved fixture install, and confirms real-vault registry/catalog files remain unchanged.

The governed Remote Distribution foundation smoke is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_remote_distribution_smoke --vault-root . --timeout-seconds 30 --json
```

This smoke uses direct StudioAPI calls to write a remote index in a fixture vault, verify trusted remote ingest, write the local fixture catalog listing, confirm Studio registry/frontend wiring, and confirm real-vault registry/catalog/remote-index files remain unchanged.

The governed Hosted Export Bundle smoke is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_hosted_marketplace_export_bundle_smoke --vault-root . --timeout-seconds 30 --json
```

This smoke uses direct StudioAPI calls to write a hosted bundle in a fixture vault, verify exact remote-index and hosted-bundle digest gates, confirm the manual static-host publication manifest, confirm no credentials/network/payment/license/install authority, confirm Studio registry/frontend wiring, and confirm real-vault registry/catalog/remote-index/hosted-bundle files remain unchanged.

The governed Static Host Publication proof smoke is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_static_host_publication_smoke --vault-root . --timeout-seconds 30 --json
```

This smoke uses direct StudioAPI calls to write upload-ready static files in a fixture vault, verify exact remote-index, hosted-bundle, and static-publication digest gates, confirm no network upload, external registry mutation, payment/license/install authority, confirm Studio registry/frontend wiring, and confirm real-vault registry/catalog/remote-index/hosted-bundle/static-publication files remain unchanged.

The governed Static Host Upload Handoff smoke is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_static_upload_handoff_smoke --vault-root . --timeout-seconds 30 --json
```

This smoke uses direct StudioAPI calls to write local JSON/Markdown operator upload handoff artifacts in a fixture vault, verify exact remote-index, hosted-bundle, static-publication, and upload-handoff digest gates, confirm no network upload, external registry mutation, payment/license/install authority, confirm Studio registry/frontend wiring, and confirm real-vault registry/catalog/remote-index/hosted-bundle/static-publication/upload-handoff files remain unchanged.

The governed Static Host Upload Receipt smoke is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_static_upload_receipt_smoke --vault-root . --timeout-seconds 30 --json
```

This smoke uses direct StudioAPI calls to write local JSON/Markdown operator upload receipt artifacts in a fixture vault, verify exact remote-index, hosted-bundle, static-publication, upload-handoff, and upload-receipt digest gates, verify exact operator receipt statement enforcement, confirm no network fetch/upload, external registry mutation, payment/license/install authority, confirm Studio registry/frontend wiring, and confirm real-vault registry/catalog/remote-index/hosted-bundle/static-publication/upload-handoff/upload-receipt files remain unchanged.

The governed Published Static Index Registration smoke is generated by:

```powershell
python -u -m runtime.studio.chaser_forge_published_static_index_registration_smoke --vault-root . --timeout-seconds 30 --json
```

This smoke uses a builder-first bounded path to write local JSON/Markdown registration artifacts in a fixture vault, verify exact remote-index, hosted-bundle, static-publication, upload-handoff, upload-receipt, and registration digest gates, verify exact operator registration statement enforcement, confirm no live URL fetch/upload, external registry mutation, payment/license/install authority, confirm Studio registry/frontend wiring, and confirm real-vault registry/catalog/distribution artifact files remain unchanged.

The completion audit is generated by:

```powershell
python -m runtime.forge.completion_audit --vault-root . --write --json
```

The Studio clickthrough proof is generated by:

```powershell
python -m runtime.studio.chaser_forge_proof_deck_clickthrough_visual_qa --vault-root . --json
```

The visual QA harness loads the production Studio shell frontend with a pywebview API stub, routes to `#/chaser-forge`, verifies the proof-deck section, artifact paths, `Marketplace Publish And Install` slide, and next-pass marker, and writes only visual QA evidence under `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-proof-deck-clickthrough/`.

The Approval Center decision-handoff visual proof is generated by:

```powershell
python -m runtime.studio.chaser_forge_approval_center_lifecycle_visual_qa --vault-root . --output-dir 07_LOGS\Studio-Visual-QA\2026-05-20-chaser-forge-approval-center-decision-handoff --json
```

The harness renders a temporary Forge approval fixture through the production Approval Center frontend, opens the technical details section, verifies lifecycle tokens plus `review_chaser_forge_approval_decision`, and captures desktop/mobile screenshots. It writes visual QA evidence only and does not approve, consume, execute, mutate registry/extension files, or persist fixture approval artifacts in the real vault.

The marketplace import sandbox request bridge visual proof is generated by:

```powershell
python -m runtime.studio.chaser_forge_marketplace_import_bridge_visual_qa --vault-root . --json
```

The harness renders the production Studio Chaser Forge panel route `#/chaser-forge` with a temporary approved marketplace-import fixture, verifies the Marketplace Publish And Install section, the sandbox request preview/write APIs, publish/install control labels, the `forge_marketplace_import_sandbox_request_written` handoff, and the pending `_forge_sandbox_approvals/` artifact path. It captures desktop/mobile screenshots under `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-publish-install-visual-qa/`, removes the fixture, and writes visual QA evidence only.


## 2026-05-31 domain-selected update

Primary public domain selected: `https://chaseos.ai`. Chaser Forge public static index target: `https://chaseos.ai/forge/index.json`. This confirms the product planning status as domain-selected/static-index-upload-pending; it does not enable live hosted fetch, network upload, payment/license mutation, untrusted third-party exchange, automatic remote install, or external registry mutation. Live hosted fetch remains approval-gated until the static index is uploaded, URL verified, digest matched to the local artifact, and a final approval packet exists.
