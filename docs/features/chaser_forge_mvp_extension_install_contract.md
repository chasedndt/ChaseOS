# Chaser Forge MVP Extension Install Contract

Date: 2026-05-25
Runtime: Codex
Status: COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, LOCAL LIVE-INDEX INPUT PREFILL BUILT, NO-DOMAIN CLOSEOUT VERIFIED, DOMAIN SELECTED / PUBLIC STATIC INDEX UPLOAD PENDING / LIVE FETCH APPROVAL-GATED

Chaser Forge may extend ChaseOS through declared extension points, but generated extensions may not rewrite ChaseOS core. The governed implementation creates a manifest validator, protected-core target-path guard, validating demo manifest, registry read model, sandbox approval request surface, approved sandbox registry writer, live-install approval request surface, approved live install executor, rollback approval request surface, approved rollback executor, source-specific approval decision handoff, read-only operator decision form, decision-bound executor consumption validation, local marketplace package export/write/import-preview foundation, ChaseOS-owned local public catalog publish, read-only Local Marketplace Library inspection, digest-bound remote distribution index artifacts, verified remote listing ingest into the local catalog, digest-gated hosted export bundles for manual static-host mirroring, digest-gated static-host publication proof directories with upload-ready files, digest-gated static-host upload handoff artifacts for operator manual upload, digest-gated static-host upload receipt artifacts for operator proof after manual upload, digest-gated published static index registration artifacts for operator-declared public index URLs, digest-gated local live `index.json` input prefill artifacts, read-only live `index.json` input readiness for the domain-selected/static-index-upload-pending hosted verification lane, marketplace import sandbox approval request surface, marketplace import sandbox request bridge, governed marketplace install executor, Studio panel controls, Approval Center routing, lifecycle visual proof, refreshed log-only proof deck, read-only Studio proof-deck clickthrough, Studio visual QA for the marketplace import sandbox request bridge, live StudioAPI control proof, operator-use Studio button proof/direct closeout smoke, local library Studio-use smoke, remote distribution direct smoke, hosted export bundle direct smoke, static-host publication direct smoke, static-host upload handoff direct smoke, static-host upload receipt direct smoke, published static index registration direct smoke, completion audit, and Feature Register / Feature Fit Register registration. Live execution is registry promotion only. Rollback execution is registry rollback only and does not delete extension files. Marketplace publish/install is local-first: catalog publish writes a vault-local catalog listing, remote distribution writes portable trust-checked index artifacts and can ingest verified listings into the local catalog, hosted export writes portable static-host bundle artifacts for operator-reviewed mirroring, static publication writes upload-ready proof files in a local fixture/proof directory only, static upload handoff writes local JSON/Markdown operator handoff artifacts only, static upload receipt writes local JSON/Markdown operator receipt artifacts only after exact digest and exact statement gates, published static index registration writes local JSON/Markdown operator registration artifacts only after exact digest and exact statement gates, live input prefill writes local packet artifacts only, live index input readiness validates the future packet locally without fetching, package install consumes approved marketplace-import plus sandbox approvals before delegating registry/file writes to the existing sandbox registry writer, and Local Marketplace Library inspection joins catalog/registry state without writes.

2026-05-21 marketplace completion: `runtime.studio.chaser_forge_live_studio_control_proof` drives the real StudioAPI controls through sandbox approval/decision/execution, live approval/decision/execution, rollback approval/decision/execution, local marketplace package write/import preview, catalog publish, marketplace-import approval/decision, approved marketplace-import bridge, sandbox approval/decision, and marketplace install execution in temporary fixture vaults. `runtime.forge.proof_deck` now includes that evidence, and `runtime.forge.completion_audit` checks proof deck, live control proof, panel completion posture, and canonical register rows before marking the governed marketplace and Studio UI implemented and registered.

2026-05-22 operator-use closeout: `runtime.studio.chaser_forge_marketplace_operator_use_visual_qa` verifies the production Studio `#/chaser-forge` button flow for `Publish Demo Package` and `Run Demo Marketplace Install`, including visible status persistence after refresh, required StudioAPI calls, accepted test confirmations, fixture registry/file writes, and exact-once marker evidence. Because the pytest wrapper repeatedly hung in this environment and left runaway Python processes, `runtime.studio.chaser_forge_marketplace_operator_use_closeout_smoke` adds a direct `python -u` smoke command with faulthandler timeout and explicit JSON output. The smoke proof is written under `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-marketplace-operator-use-closeout-smoke/`.

2026-05-22 Local Marketplace Library Studio-use closeout: `runtime.forge.marketplace.build_forge_marketplace_local_library` and Studio API `get_chaser_forge_marketplace_local_library` expose a read-only library model that joins vault-local catalog entries with the Forge registry. The production Chaser Forge panel now renders a Local Marketplace Library section with item status, registry status, target-path evidence, blocked remote exchange, and API wiring. `runtime.studio.chaser_forge_local_marketplace_library_smoke` directly drives the StudioAPI publish/import/sandbox/install chain in a temporary fixture vault, verifies listed-not-installed before install and listed-installed after install, confirms panel registry/frontend tokens, confirms real-vault registry/catalog files are unchanged, and writes JSON evidence under `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-local-marketplace-library-studio-use-smoke/`.

2026-05-22 governed remote distribution foundation: `runtime.forge.marketplace.build_forge_marketplace_remote_distribution`, `build_forge_marketplace_remote_ingest_preview`, and `build_forge_marketplace_remote_listing_ingest` create a digest-bound remote index artifact, verify publisher identity/attestation, validate listing/package/manifest digests, and ingest a trusted remote listing into the local catalog only with exact remote index digest, exact listing digest, and exact operator confirmation. Studio exposes `get_chaser_forge_marketplace_remote_distribution`, `write_chaser_forge_marketplace_remote_index`, and `ingest_chaser_forge_marketplace_remote_listing`, and the Chaser Forge panel renders a Remote Distribution section with write/ingest buttons. `runtime.studio.chaser_forge_remote_distribution_smoke` verifies the end-to-end StudioAPI flow in a fixture vault, confirms real-vault registry/catalog/remote-index paths are unchanged, and writes JSON evidence under `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-remote-distribution-foundation-smoke/`.

2026-05-22 governed hosted export bundle: `runtime.forge.marketplace.build_forge_marketplace_hosted_export_bundle` creates a digest-gated JSON bundle containing the verified remote index, publication manifest, and operator readme for manual static-host mirroring. Studio exposes `get_chaser_forge_marketplace_hosted_export_bundle` and `write_chaser_forge_marketplace_hosted_export_bundle`, and the Chaser Forge panel renders a Hosted Bundle write control in the Remote Distribution section. `runtime.studio.chaser_forge_hosted_marketplace_export_bundle_smoke` verifies preview/write, exact hosted-bundle and remote-index digest gates, no credentials, no network publish, no payment/license mutation, no package install, panel/frontend wiring, and unchanged real-vault registry/catalog/remote-index/hosted-bundle paths under `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-hosted-marketplace-export-bundle-smoke/`.

2026-05-23 governed static-host publication proof: `runtime.forge.marketplace.build_forge_marketplace_static_host_publication` creates digest-gated upload-ready files (`index.json`, `README.md`, `hosted-bundle.json`, `publication-manifest.json`, and `checksums.json`) from a verified hosted bundle. Studio exposes `get_chaser_forge_marketplace_static_host_publication` and `write_chaser_forge_marketplace_static_host_publication`, and the Chaser Forge panel renders a Write Static Publication control in the Remote Distribution section. `runtime.studio.chaser_forge_static_host_publication_smoke` verifies preview/write, exact remote-index, hosted-bundle, and static-publication digest gates, no network upload, no external registry mutation, no payment/license mutation, no package install, panel/frontend wiring, and unchanged real-vault registry/catalog/remote-index/hosted-bundle/static-publication paths under `07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-host-publication-proof-smoke/`.

2026-05-23 governed static-host upload handoff: `runtime.forge.marketplace.build_forge_marketplace_static_host_upload_handoff` creates digest-gated local JSON/Markdown operator handoff artifacts after the static-host publication files exist and match their checksums. Studio exposes `get_chaser_forge_marketplace_static_host_upload_handoff` and `write_chaser_forge_marketplace_static_host_upload_handoff`, and the Chaser Forge panel renders a Write Upload Handoff control in the Remote Distribution section. `runtime.studio.chaser_forge_static_upload_handoff_smoke` verifies preview/write, exact remote-index, hosted-bundle, static-publication, and upload-handoff digest gates, no network upload, no external registry mutation, no payment/license mutation, no package install, panel/frontend wiring, and unchanged real-vault registry/catalog/remote-index/hosted-bundle/static-publication/upload-handoff paths under `07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-upload-handoff-smoke/`.

2026-05-23 governed static-host upload receipt: `runtime.forge.marketplace.build_forge_marketplace_static_host_upload_receipt` creates digest-gated local JSON/Markdown operator receipt artifacts after the static-host upload handoff exists and matches its checksum. Studio exposes `get_chaser_forge_marketplace_static_host_upload_receipt` and `write_chaser_forge_marketplace_static_host_upload_receipt`, and the Chaser Forge panel renders a Write Upload Receipt control in the Remote Distribution section. `runtime.studio.chaser_forge_static_upload_receipt_smoke` verifies preview/write, exact remote-index, hosted-bundle, static-publication, upload-handoff, and upload-receipt digest gates, exact operator receipt statement enforcement, no network fetch/upload, no external registry mutation, no payment/license mutation, no package install, panel/frontend wiring, and unchanged real-vault registry/catalog/remote-index/hosted-bundle/static-publication/upload-handoff/upload-receipt paths under `07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-upload-receipt-smoke/`.

2026-05-24 governed published static index registration: `runtime.forge.marketplace.build_forge_marketplace_published_static_index_registration` creates digest-gated local JSON/Markdown registration artifacts after the static-host upload receipt exists and matches its digest. Studio exposes `get_chaser_forge_marketplace_published_static_index_registration` and `write_chaser_forge_marketplace_published_static_index_registration`, and the Chaser Forge panel renders a Register Published Index control in the Remote Distribution section. `runtime.studio.chaser_forge_published_static_index_registration_smoke` verifies preview/write through a builder-first bounded path, exact remote-index, hosted-bundle, static-publication, upload-handoff, upload-receipt, and registration digest gates, exact operator registration statement enforcement, no live URL fetch/upload, no external registry mutation, no payment/license mutation, no package install, panel/frontend wiring, and unchanged real-vault registry/catalog/distribution artifact paths under `07_LOGS/Studio-Visual-QA/2026-05-24-chaser-forge-published-static-index-registration-smoke/`.

2026-05-25 domain-selected live index input readiness: `runtime.forge.marketplace.build_forge_marketplace_live_index_input_readiness` reads the operator JSON packet template and handover, detects the explicit domain-selected/static-index-upload-pending deferral, validates future public `index.json` URL shape, rejects generic trusted homepages that do not end in `/index.json`, inspects the selected or latest local static publication directory and local `index.json` SHA-256 when present, and reports whether a future bounded live fetch pass can run. Studio exposes `get_chaser_forge_marketplace_live_index_input_readiness`, and the Chaser Forge panel/frontend renders Live Input status plus a Check Live Input control. This surface is read-only: it performs no live URL fetch, network upload, external registry mutation, credential use, payment/license mutation, package install, provider/model call, Agent Bus dispatch, protected-core mutation, or canonical write.

2026-05-25 local live input packet prefill and Studio coming-soon state: `runtime.forge.marketplace.build_forge_marketplace_live_index_input_prefill` now writes a digest-gated local JSON packet plus Markdown handoff under `07_LOGS/Operator-Briefs/Chaser-Forge-Live-Index-Input-Prefills/`. The current packet is `live-index-input-prefill-8db3a8749899.json`; it fills `local_static_publication_dir=07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Publications/local-operator-static-831f27d7c241` and `local_index_sha256=f7b2f636b4f0c5e95171deffe963889e4b7cb8f267e3e5d1f33b63639835c461`, while domain URL, upload confirmation, and future fetch approval remain explicitly pending. Studio exposes `get_chaser_forge_marketplace_live_index_input_prefill` and `write_chaser_forge_marketplace_live_index_input_prefill`; the Chaser Forge frontend labels the hosted marketplace lane as `Hosted Marketplace - Coming Soon`, adds a Prefill Live Input Packet control, and disables the live published-index registration control while the domain is deferred. No live URL fetch, network upload, external registry mutation, credential use, payment/license mutation, package install, provider/model call, Agent Bus dispatch, protected-core mutation, or canonical write was added.

2026-05-25 no-domain closeout audit: `runtime.studio.chaser_forge_no_domain_closeout_audit` and Studio API `get_chaser_forge_no_domain_closeout_audit` verify that no code-owned no-domain Chaser Forge work remains. The audit checks the `chaser-forge` Studio panel target, registry API methods, frontend source tokens for hosted marketplace coming-soon and prefill controls, the current prefilled packet and Markdown handoff, the five local static publication files, matching local `index.json` SHA-256, and domain-selected/static-index-upload-pending readiness with network fetch/upload/external registry mutation still blocked. The next step is operator-owned: purchase/configure the domain, upload the five files, fill the final packet, and approve one bounded future fetch. No live URL fetch, network upload, external registry mutation, credential use, payment/license mutation, package install, provider/model call, Agent Bus dispatch, protected-core mutation, or canonical write was added.

2026-05-20 lifecycle visual proof: the production Approval Center frontend now renders Forge source-group status counts, and the `chaser-forge-manual-ui-lifecycle-proof` harness verifies a temporary fixture containing pending, approved-pending-execution, consumed, rejected, and invalid Forge approval artifacts across desktop and mobile screenshots. This is UI proof only; it does not grant approval decisions, consume approvals, execute Forge lifecycle actions, mutate the registry, write/delete extension files, or persist fixture approval artifacts in the real vault.

2026-05-20 proof deck: `runtime.forge.proof_deck` packages the existing Forge implementation logs, current docs, Approval Center lifecycle visual QA report, Studio proof-deck clickthrough report, and marketplace import sandbox request bridge visual QA report into `07_LOGS/Workflow-Proofs/2026-05-20_chaser-forge-proof-deck.md` and `.json`. This is log-only evidence packaging; it does not grant approval decisions, consume approvals, execute sandbox/live/rollback actions, mutate the Forge registry, write/delete extension files, call providers/models, activate schedules, write Agent Bus tasks, read secrets/credentials, or mutate Pulse memory, Personal Map, R&D truth-state, protected core, or canonical state.

2026-05-21 Studio clickthrough proof: the native Chaser Forge panel now renders a read-only Proof Deck section using `build_chaser_forge_panel` and `runtime.forge.proof_deck` in `write=False` mode. `runtime.studio.chaser_forge_proof_deck_clickthrough_visual_qa` verifies the production Studio shell route `#/chaser-forge` with desktop/mobile screenshots under `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-proof-deck-clickthrough/`. This is Studio visibility only; it does not approve, consume, execute, mutate the registry, write/delete extension files, write proof deck artifacts, or grant provider/model, schedule, Agent Bus, secret, protected-core, Pulse memory, Personal Map, R&D truth-state, or canonical authority.

2026-05-20 decision handoff: `runtime.forge.approval_decision.build_forge_approval_decision_handoff` and Studio API `review_chaser_forge_approval_decision` now provide a source-specific approve/reject handoff for one pending Forge approval artifact. A write requires the exact request digest and exact operator approval/rejection statement, writes a decision audit artifact under the matching source `_decisions/` folder, and updates only the source approval artifact's decision metadata. It does not consume approvals, reserve exact-once markers, execute sandbox/live/rollback actions, mutate the registry, write/delete extension files, patch Studio, mutate protected core, call providers/connectors, write Agent Bus tasks, or mutate canonical state.

2026-05-20 decision handoff visual proof: the lifecycle visual QA harness now also verifies source-specific handoff visibility in the production Approval Center renderer, including the `review_chaser_forge_approval_decision` API token and the no-consumption/no-execution posture. Evidence for this pass is written under `07_LOGS/Studio-Visual-QA/2026-05-20-chaser-forge-approval-center-decision-handoff/`.

2026-05-20 decision-bound executor consumption proof: the sandbox registry writer, live-install executor, and rollback executor now require a valid recorded `forge_approval_decision_handoff` sidecar before an approved source artifact can be consumed. The executor checks the source metadata, sidecar root, source artifact path, packet id, request digest, approval scope, source record type/schema, decision digest recomputation, and no-execution/no-registry/no-marker flags on the decision sidecar. Manually edited `status=approved` artifacts without the sidecar now fail closed.

2026-05-20 operator decision form: `runtime.forge.approval_decision_form.build_forge_approval_decision_form` and Studio API `get_chaser_forge_approval_decision_form` now return a read-only source-specific form contract for one pending Forge approval artifact. The form prepares approved/rejected options, exact copyable operator statements, expected request digest, and the `review_chaser_forge_approval_decision` submit payload. It does not write decision sidecars, mutate source approval artifacts, consume approvals, execute sandbox/live/rollback actions, mutate the registry, write/delete extension files, reserve exact-once markers, or add generic Approval Center decision controls.

2026-05-20 marketplace import/export foundation: `runtime.forge.marketplace` builds a local, digest-bound Forge marketplace package preview for manifests that declare `marketplace.template`; writes the same package under `07_LOGS/Workflow-Proofs/Forge-Marketplace-Packages/` only when the exact preview digest is supplied; and previews import by recomputing package and manifest digests without installing anything.

2026-05-20 marketplace import sandbox approval request: `runtime.forge.marketplace.build_forge_marketplace_import_sandbox_approval` and Studio API `request_chaser_forge_marketplace_import_sandbox_approval` now build a digest-gated pending review artifact under `07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/` for local package-to-sandbox review. A write requires the exact `request_digest_sha256`; a matching existing pending artifact can be reused. Approval Center routes the `marketplace-import` family, and the source-specific decision handoff can record approve/reject metadata for that artifact. This still does not install packages, request sandbox execution, consume approvals, reserve exact-once markers, mutate the Forge registry, write extension files, call providers/connectors, dispatch Agent Bus tasks, or mutate protected core/canonical state.

2026-05-20 marketplace import sandbox request bridge: `runtime.forge.marketplace.build_forge_marketplace_import_sandbox_request` and Studio APIs `get_chaser_forge_marketplace_import_sandbox_request` / `request_chaser_forge_marketplace_import_sandbox_request` now validate an approved, unconsumed `marketplace-import` review artifact plus its source-specific decision sidecar and can write or reuse one normal pending sandbox approval request under `07_LOGS/Agent-Activity/_forge_sandbox_approvals/` when the exact bridge digest is supplied. This still does not install packages, consume the marketplace-import approval, consume the sandbox approval, execute the sandbox registry writer, reserve exact-once markers, mutate the Forge registry, write extension files, call providers/connectors, dispatch Agent Bus tasks, or mutate protected core/canonical state.

2026-05-21 marketplace publish/install Studio visual QA: `runtime.studio.chaser_forge_marketplace_import_bridge_visual_qa` renders the production Chaser Forge panel with a temporary approved marketplace-import fixture and verifies the `Marketplace Publish And Install` section, sandbox request preview/write APIs, `forge_marketplace_import_sandbox_request_written` state, pending `_forge_sandbox_approvals/` path, and publish/install control posture across desktop and mobile screenshots. Evidence is written under `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-publish-install-visual-qa/`. The fixture is removed; no real-vault marketplace-import approval artifact, real-vault sandbox approval request, package install, approval consumption, registry/extension mutation, provider/model call, Agent Bus dispatch, protected-core, memory, R&D truth-state, or canonical mutation is performed.

2026-05-21 marketplace proof deck refresh: the proof deck now includes marketplace build logs, visual QA report, desktop/mobile screenshots, bridge-written state, refreshed Studio proof-deck clickthrough evidence, and live StudioAPI proof for catalog publish plus governed marketplace install execution.

## Allowed Extension Points

The current approved extension points are:

- `sidebar.nav.item`
- `workspace.page`
- `dashboard.widget`
- `agent.preset`
- `workflow.template`
- `form.schema`
- `command.palette.action`
- `report.template`
- `notification.template`
- `connector.usage`
- `marketplace.template`

Each extension point is validated against its route namespace, permission set, component type, workflow node type, memory scope, data namespace, and rollback posture.

## Install Lifecycle

1. `draft`: manifest can be edited and locally validated. No writes are enabled.
2. `preview`: Studio may render a preview and inspect permissions. No production writes are enabled.
3. `sandbox`: extension-owned sandbox writes require operator approval. The current implementation can create a pending sandbox approval request artifact, then consume an approved artifact exactly once to write the sandbox registry entry and extension-owned target files.
4. `active`: live install requires clean validation, sandbox proof, explicit operator approval, and rollback snapshot metadata. The current implementation can consume an approved live-install approval artifact exactly once to promote the sandbox registry entry to live state.
5. `disabled`: rollback requires live proof, explicit operator approval, and a rollback exact-once marker. The current implementation can consume an approved rollback approval artifact exactly once to return the live registry entry to sandbox state while retaining extension-owned files and audit evidence.
6. `archived`: extension package and audit trail are retained.

## Registry And Sandbox Approval

The Forge registry read model lives at `runtime/forge/registry/extensions.json`. Generated extensions may not write it directly.

The sandbox approval request surface writes only to `07_LOGS/Agent-Activity/_forge_sandbox_approvals/` and only when the caller supplies the exact `request_digest_sha256` returned by the preview. The artifact is a pending operator decision, not an approval consumption and not an install executor.

Approval Center routing: the native read-only Approval Center discovers sandbox approval request artifacts and renders their lifecycle state, request digest, affected extension-owned paths, future registry/marker refs, and safety posture. It does not grant, consume, or execute the sandbox approval.

Current sandbox approval request boundaries:

- no extension registry write
- no extension file write
- no exact-once marker reservation
- no live install
- no protected-core mutation
- no Studio shell patch
- no runtime policy or schedule mutation
- no Agent Bus task write
- no provider/model call
- no secret or credential read

## Approved Sandbox Registry Writer

The sandbox registry writer consumes an approved sandbox approval artifact. It requires:

- exact `request_digest_sha256`
- matching `approval_packet_id`
- artifact `status=approved`
- artifact `operator_decision=approved`
- unconsumed artifact state
- operator approval statement matching the generated confirmation text
- matching recorded source-specific decision sidecar digest
- matching approved material digest
- matching future registry and exact-once marker paths
- clean manifest revalidation
- no pre-existing exact-once marker
- no pre-existing extension registry entry for the same extension id
- no pre-existing extension-owned target files

When all gates pass and execution is requested, the writer reserves the exact-once marker before writes, then writes only:

- `runtime/forge/registry/extensions.json`
- `extensions/<extension-id>/**` target files declared by the manifest
- consumed status metadata back to the approval artifact
- exact-once marker completion metadata

Current sandbox writer boundaries:

- no live install
- no protected-core mutation
- no Studio shell patch
- no runtime policy or schedule mutation
- no Agent Bus task write
- no provider/model call
- no external connector call
- no secret or credential read
- no rollback execution

## Source-Specific Approval Decision Handoff

The Forge decision handoff bridges stage 2 pending request artifacts to stage 3 operator review decisions without adding generic Approval Center write authority. It supports sandbox, live-install, rollback, and marketplace-import review roots:

- `07_LOGS/Agent-Activity/_forge_sandbox_approvals/*.json`
- `07_LOGS/Agent-Activity/_forge_live_install_approvals/*.json`
- `07_LOGS/Agent-Activity/_forge_rollback_approvals/*.json`
- `07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/*.json`

For write mode, the handoff requires:

- source artifact path confined to one Forge approval root
- pending source artifact state (`status=pending_operator_decision`, `operator_decision=pending`, `approval_consumed=false`)
- matching source record type and approval scope
- exact expected `request_digest_sha256`
- exact generated approval statement for approvals, or exact generated rejection statement for rejections
- no pre-existing decision sidecar for the same artifact/digest/decision

When approved, it writes `status=approved`, `operator_decision=approved`, `operator_approval_statement`, approval timestamp/reviewer metadata, and decision sidecar references back to the source artifact. When rejected, it writes `status=rejected`, `operator_decision=rejected`, `operator_rejection_statement`, rejection timestamp/reviewer metadata, and decision sidecar references.

It always preserves:

- `approval_consumed=false`
- no registry writes
- no extension file writes or deletes
- no exact-once marker reservation
- no protected-core, Studio shell, runtime policy, schedule, Agent Bus, provider, connector, secret, credential, Pulse memory, Personal Map, R&D truth-state, or canonical mutation

Approved source artifacts are still only inputs to their separate source-specific executors. Those executors now revalidate the recorded decision sidecar digest and source binding in addition to digest, scope, material, exact-once marker absence, and lifecycle proof before any future consumption or execution.

## Source-Specific Operator Decision Form

The Forge operator decision form narrows the operator ergonomics gap between read-only Approval Center visibility and the existing source-specific decision handoff. It accepts one Forge approval artifact path and returns a preview-only form model with:

- approval family, packet id, request digest, extension id/name/version, and source artifact path
- approved and rejected decision options
- exact required operator statement per decision
- future decision sidecar path preview per decision
- prepared submit payload for `review_chaser_forge_approval_decision`
- blocked authority flags for approval consumption, Forge execution, registry mutation, extension file mutation, exact-once marker reservation, provider/model calls, Agent Bus dispatch, secrets, credentials, Pulse memory, Personal Map, R&D truth-state, and canonical mutation

The form is not the writer. The source-specific handoff remains the only Forge decision writer, and its exact digest and exact statement gates still apply.

## Marketplace Publish And Install Foundation

The current marketplace lane is `COMPLETE / CHASEOS-OWNED LOCAL PUBLIC CATALOG, GOVERNED PUBLISHED STATIC INDEX REGISTRATION, GOVERNED STATIC HOST UPLOAD RECEIPT, GOVERNED STATIC HOST UPLOAD HANDOFF, GOVERNED STATIC HOST PUBLICATION PROOF, GOVERNED HOSTED EXPORT BUNDLE, GOVERNED REMOTE DISTRIBUTION FOUNDATION, AND GOVERNED INSTALL VERIFIED`. It is not an ambient remote marketplace call surface and not an untrusted package exchange.

Implemented surfaces:

- `runtime.forge.marketplace.build_forge_marketplace_export_package`
- `runtime.forge.marketplace.build_forge_marketplace_catalog`
- `runtime.forge.marketplace.build_forge_marketplace_publish`
- `runtime.forge.marketplace.build_forge_marketplace_local_library`
- `runtime.forge.marketplace.build_forge_marketplace_remote_distribution`
- `runtime.forge.marketplace.build_forge_marketplace_remote_ingest_preview`
- `runtime.forge.marketplace.build_forge_marketplace_remote_listing_ingest`
- `runtime.forge.marketplace.build_forge_marketplace_hosted_export_bundle`
- `runtime.forge.marketplace.build_forge_marketplace_static_host_publication`
- `runtime.forge.marketplace.build_forge_marketplace_static_host_upload_handoff`
- `runtime.forge.marketplace.build_forge_marketplace_static_host_upload_receipt`
- `runtime.forge.marketplace.build_forge_marketplace_published_static_index_registration`
- `runtime.forge.marketplace.build_forge_marketplace_live_index_input_prefill`
- `runtime.forge.marketplace.build_forge_marketplace_live_index_input_readiness`
- `runtime.forge.marketplace.build_forge_marketplace_import_preview`
- `runtime.forge.marketplace.build_forge_marketplace_import_sandbox_approval`
- `runtime.forge.marketplace.build_forge_marketplace_import_sandbox_request`
- `runtime.forge.marketplace.build_forge_marketplace_install_execution`
- Studio API `get_chaser_forge_marketplace_export_package`
- Studio API `write_chaser_forge_marketplace_export_package`
- Studio API `get_chaser_forge_marketplace_catalog`
- Studio API `get_chaser_forge_marketplace_publish_preview`
- Studio API `publish_chaser_forge_marketplace_package`
- Studio API `get_chaser_forge_marketplace_local_library`
- Studio API `get_chaser_forge_marketplace_remote_distribution`
- Studio API `write_chaser_forge_marketplace_remote_index`
- Studio API `ingest_chaser_forge_marketplace_remote_listing`
- Studio API `get_chaser_forge_marketplace_hosted_export_bundle`
- Studio API `write_chaser_forge_marketplace_hosted_export_bundle`
- Studio API `get_chaser_forge_marketplace_static_host_publication`
- Studio API `write_chaser_forge_marketplace_static_host_publication`
- Studio API `get_chaser_forge_marketplace_static_host_upload_handoff`
- Studio API `write_chaser_forge_marketplace_static_host_upload_handoff`
- Studio API `get_chaser_forge_marketplace_static_host_upload_receipt`
- Studio API `write_chaser_forge_marketplace_static_host_upload_receipt`
- Studio API `get_chaser_forge_marketplace_published_static_index_registration`
- Studio API `write_chaser_forge_marketplace_published_static_index_registration`
- Studio API `get_chaser_forge_marketplace_live_index_input_prefill`
- Studio API `write_chaser_forge_marketplace_live_index_input_prefill`
- Studio API `get_chaser_forge_marketplace_live_index_input_readiness`
- Studio API `get_chaser_forge_marketplace_import_preview`
- Studio API `request_chaser_forge_marketplace_import_sandbox_approval`
- Studio API `get_chaser_forge_marketplace_import_sandbox_request`
- Studio API `request_chaser_forge_marketplace_import_sandbox_request`
- Studio API `execute_chaser_forge_marketplace_install`

Export preview packages the manifest, validation report, permission disclosure, declared `marketplace.template` extension point, artifact refs, and future import contract into a stable `package_digest_sha256`. Package writes are digest-gated and local-only under `07_LOGS/Workflow-Proofs/Forge-Marketplace-Packages/`.

Import preview can read a vault-local package JSON path or inline package payload. It recomputes the package digest, recomputes the embedded manifest digest, revalidates the manifest, and reports future import requirements. It writes no registry entry, no extension files, no approval artifact, and no exact-once marker.

Catalog publish writes or reuses one listing under `runtime/forge/registry/marketplace-catalog.json` only when the caller supplies the exact listing digest from preview. It writes no remote marketplace state.

Local Marketplace Library inspection is read-only. It joins local catalog entries with installed Forge registry entries and reports catalog counts, installed counts, listed-not-installed state, listed-installed state, installed-unlisted state, registry status, install environment, target-path evidence, and blocked authority flags. It writes no package artifact, catalog entry, approval artifact, registry entry, extension file, exact-once marker, remote marketplace state, or third-party exchange.

Remote Distribution creates portable index artifacts under `07_LOGS/Workflow-Proofs/Forge-Marketplace-Remote-Indexes/` only when the caller supplies the exact remote index digest from preview. Remote ingest verifies the remote index digest, listing digest, publisher id/fingerprint trust, publisher attestation digest, package digest, manifest digest, and normal package import preview, then writes or reuses one local catalog entry only when the exact operator confirmation is supplied. It writes no registry entry, extension file, approval artifact, exact-once marker, network request, payment mutation, or license checkout.

Hosted Export Bundle creates portable manual static-host bundle artifacts under `07_LOGS/Workflow-Proofs/Forge-Marketplace-Hosted-Bundles/` only when the caller supplies the exact hosted bundle digest and exact source remote index digest from preview. The bundle contains the verified remote index payload, publication manifest, and operator readme; it writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network request, credential, payment mutation, license checkout, or package install.

Static Host Publication creates upload-ready static-host proof files under `07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Publications/` only when the caller supplies the exact remote-index, hosted-bundle, and static-publication digests from preview. It writes `index.json`, `README.md`, `hosted-bundle.json`, `publication-manifest.json`, and `checksums.json`; it writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network upload, external registry mutation, credential, payment mutation, license checkout, or package install.

Static Host Upload Handoff creates local operator handoff artifacts under `07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Handoffs/` only when the caller supplies the exact remote-index, hosted-bundle, static-publication, and upload-handoff digests from preview. It writes JSON and Markdown checklist artifacts for manual upload of the existing static-host publication files; it writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network upload, external registry mutation, credential, payment mutation, license checkout, or package install.

Static Host Upload Receipt creates local operator receipt artifacts under `07_LOGS/Workflow-Proofs/Forge-Marketplace-Static-Host-Upload-Receipts/` only when the caller supplies the exact remote-index, hosted-bundle, static-publication, upload-handoff, and upload-receipt digests from preview plus the exact generated operator receipt statement. It writes JSON and Markdown proof artifacts recording the operator-declared static-host base URL and manual upload claim; it writes no registry entry, extension file, catalog entry, approval artifact, exact-once marker, network fetch, network upload, external registry mutation, credential, payment mutation, license checkout, or package install. This is local proof of an operator statement, not live hosted URL verification.

Marketplace import sandbox approval request can write one pending review artifact under `07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/` only when the exact request digest from the preview is supplied. It is source-specific approval review plumbing for the `marketplace-import` family, not a package installer and not a sandbox executor.

Marketplace import sandbox request bridge can write or reuse one pending sandbox approval request under `07_LOGS/Agent-Activity/_forge_sandbox_approvals/` only after an approved, unconsumed marketplace-import review artifact and matching source-specific decision sidecar validate. It is the package-review-to-sandbox-review handoff only; it does not consume either approval or execute installation.

Marketplace install execution requires a local catalog listing, the approved marketplace-import review plus decision sidecar, the bridge request digest, the approved sandbox approval plus decision sidecar, and the sandbox request digest. When `execute=True`, it delegates to the existing sandbox registry writer, consumes both approvals, writes extension-owned files, writes the Forge registry, and reserves the sandbox exact-once marker.

Still blocked by design:

- ambient/live remote marketplace calls
- network upload, network fetch verification, or external registry mutation
- untrusted third-party package exchange
- payment or license checkout mutation
- unauthorized install without source-specific marketplace-import and sandbox approvals
- generated dependency/core mutation
- provider/model calls
- Agent Bus dispatch
- protected-core, Pulse memory, Personal Map, R&D truth-state, or canonical mutation

## Decision-Bound Executor Consumption

Decision-bound executor consumption applies to the sandbox, live-install, and rollback executor families. Each executor now requires:

- source artifact `approval_decision_recorded=true`
- `approval_decision_record_type=forge_approval_decision_handoff`
- a decision artifact path under the matching source `_decisions/` folder
- sidecar `operator_decision=approved`
- matching approval packet id, request digest, approval scope, source record type, source schema version, source artifact path, and decision artifact path
- decision digest recomputation matching `approval_decision_digest_sha256` on the source artifact
- decision-sidecar flags preserving `approval_consumed=false`, `forge_execution_allowed=false`, `registry_written=false`, `extension_files_written=[]`, `extension_files_deleted=[]`, and `exact_once_marker_reserved=false`

This validation does not add generic Approval Center write authority. It only binds Forge source-specific executors to the prior recorded source-specific decision before approval consumption.

## Live Install Approval Packet

The live-install approval request surface is request-only. It can write a pending artifact under `07_LOGS/Agent-Activity/_forge_live_install_approvals/` only when the caller supplies the exact `request_digest_sha256` returned by the preview and all sandbox proof checks pass.

Approval Center routing: the native read-only Approval Center discovers live-install approval request artifacts and shows pending, approved, consumed, invalid, and source-ref state without adding live-install authority.

Live approval readiness requires:

- a Forge registry entry for the extension
- registry status `sandbox_installed`
- install environment `sandbox`
- manifest digest matching the registry entry
- completed sandbox exact-once marker matching the registry entry
- existing extension-owned target files for every normalized target path
- no future live exact-once marker
- clean manifest revalidation

The live approval request writes only:

- pending live approval artifact metadata
- future live exact-once marker path preview
- future registry path preview
- operator confirmation text
- approved material digest inputs

Current live approval boundaries:

- no registry mutation from the approval request surface
- no extension file mutation
- no live exact-once marker reservation from the approval request surface
- no protected-core mutation
- no Studio shell patch
- no runtime policy or schedule mutation
- no Agent Bus task write
- no provider/model call
- no external connector call
- no secret or credential read

## Approved Live Install Executor

The approved live install executor consumes an approved live approval artifact. It requires:

- exact `request_digest_sha256`
- matching `approval_packet_id`
- artifact `status=approved`
- artifact `operator_decision=approved`
- unconsumed artifact state
- operator approval statement matching the generated confirmation text
- matching recorded source-specific decision sidecar digest
- matching approved material digest
- matching future registry and live exact-once marker paths
- clean manifest revalidation
- a still-valid sandbox-installed registry entry
- a completed sandbox exact-once marker matching the sandbox registry entry
- existing extension-owned target files for every normalized target path
- no pre-existing live exact-once marker
- no previously recorded live execution

When all gates pass and execution is requested, the executor reserves the live exact-once marker before registry mutation, then writes only:

- live metadata on the existing entry in `runtime/forge/registry/extensions.json`
- consumed status metadata back to the live approval artifact
- exact-once live marker completion metadata

Current live executor boundaries:

- no extension file mutation
- no protected-core mutation
- no Studio shell patch
- no runtime policy or schedule mutation
- no Agent Bus task write
- no provider/model call
- no external connector call
- no secret or credential read
- no rollback execution

## Rollback Approval Packet

The rollback approval request surface is request-only. It can write a pending artifact under `07_LOGS/Agent-Activity/_forge_rollback_approvals/` only when the caller supplies the exact `request_digest_sha256` returned by the preview and all live proof checks pass.

Approval Center routing: the native read-only Approval Center discovers rollback approval request artifacts and shows pending, approved, consumed, invalid, and source-ref state without adding rollback authority.

Rollback approval readiness requires:

- a Forge registry entry for the extension
- registry status `live_installed`
- install environment `live`
- manifest digest matching the registry entry
- completed live exact-once marker matching the registry entry
- existing extension-owned target files for every normalized target path
- no future rollback exact-once marker
- clean manifest revalidation

The rollback approval request writes only:

- pending rollback approval artifact metadata
- future rollback exact-once marker path preview
- future registry path preview
- operator confirmation text
- approved material digest inputs

Current rollback approval boundaries:

- no registry mutation from the approval request surface
- no extension file mutation
- no extension file deletion
- no rollback exact-once marker reservation from the approval request surface
- no protected-core mutation
- no Studio shell patch
- no runtime policy or schedule mutation
- no Agent Bus task write
- no provider/model call
- no external connector call
- no secret or credential read

## Approved Rollback Executor

The approved rollback executor consumes an approved rollback approval artifact. It requires:

- exact `request_digest_sha256`
- matching `approval_packet_id`
- artifact `status=approved`
- artifact `operator_decision=approved`
- unconsumed artifact state
- operator approval statement matching the generated confirmation text
- matching recorded source-specific decision sidecar digest
- matching approved material digest
- matching future registry and rollback exact-once marker paths
- clean manifest revalidation
- a still-valid live-installed registry entry
- a completed live exact-once marker matching the live registry entry
- existing extension-owned target files for every normalized target path
- no pre-existing rollback exact-once marker
- no previously recorded rollback execution

When all gates pass and execution is requested, the executor reserves the rollback exact-once marker before registry mutation, then writes only:

- rollback metadata on the existing entry in `runtime/forge/registry/extensions.json`
- consumed status metadata back to the rollback approval artifact
- exact-once rollback marker completion metadata

The executor returns the registry entry to `sandbox_installed` / `sandbox`, moves the prior live execution into `live_execution_history`, and records `rollback_execution`. It does not delete extension files.

Current rollback executor boundaries:

- no extension file mutation
- no extension file deletion
- no protected-core mutation
- no Studio shell patch
- no runtime policy or schedule mutation
- no Agent Bus task write
- no provider/model call
- no external connector call
- no secret or credential read

## Protected-Core Rule

Generated extension target paths must stay under an extension-owned root such as `extensions/<extension-id>/`. The validator rejects protected core paths including:

- `.env`, `secrets/**`, and `credentials/**`
- protected governance docs and agent policy docs
- `runtime/policy/**`
- `runtime/schedules/**`
- `runtime/adapters/**`
- `runtime/agent_bus/**`
- Studio shell files such as `runtime/studio/shell/api.py`, `runtime/studio/shell/frontend/app.js`, and `runtime/studio/shell/frontend/index.html`
- package and deployment config such as `pyproject.toml`, lockfiles, and package manifests

## Current Verification

The demo manifest at `runtime/forge/examples/ugc_campaign_studio.manifest.json` validates cleanly. Focused tests cover the safe path plus rejection of forbidden permissions, unsafe routes, raw script UI components, shell workflow nodes, global memory scopes, protected core collections, protected target paths, target paths outside the extension-owned root, registry read model behavior, digest-gated sandbox approval request writes, duplicate reuse, mismatched artifact blocking, no registry/extension writes during the approval-request pass, source-specific decision preview/write, exact digest/operator statement enforcement, rejection keeping executors blocked, live-family decision root routing, approved sandbox registry writer preview, exact-digest execution, exact-once duplicate blocking, pending-artifact blocking, target-conflict blocking, registry-entry conflict blocking, approval consumption, live-install approval readiness after sandbox proof, live approval exact-digest writes, duplicate reuse, mismatched artifact blocking, invalid marker blocking, missing extension target blocking, live executor preview, approved live execution, duplicate live exact-once blocking, wrong-digest blocking, pending live artifact blocking, invalid sandbox proof blocking, pre-existing live marker blocking, no extension-file or protected-core writes during live execution, rollback approval readiness after live proof, rollback approval exact-digest writes, duplicate reuse, invalid live marker blocking, rollback executor preview, approved rollback execution, duplicate rollback exact-once blocking, wrong-digest blocking, pending rollback artifact blocking, registry rollback to sandbox state, live execution history preservation, extension file retention, and no extension-file deletion or protected-core writes during rollback execution.


## 2026-05-31 domain-selected update

Primary public domain selected: `https://chaseos.ai`. Chaser Forge public static index target: `https://chaseos.ai/forge/index.json`. This confirms the product planning status as domain-selected/static-index-upload-pending; it does not enable live hosted fetch, network upload, payment/license mutation, untrusted third-party exchange, automatic remote install, or external registry mutation. Live hosted fetch remains approval-gated until the static index is uploaded, URL verified, digest matched to the local artifact, and a final approval packet exists.
