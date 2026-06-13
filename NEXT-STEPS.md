# Next Steps

## Capture to Markdown Final Local Implementation - 2026-05-31

1. Treat Capture to Markdown as complete for local implementation, packaged proof, product-facing Studio wiring, local signed release, and add-on proof accounting.
2. Use the Studio `Capture` page at `#/capture-markdown` for the product-facing surface. Configurable Capture shortcuts and collector controls are on the Studio Settings page.
3. Local release artifacts are ready:
   - Studio executable: `dist/studio/ChaseOS-Studio.exe`
   - Installer: `dist/studio/ChaseOS-Installer.exe`
   - Release manifest: `dist/release/capture-markdown/2026-05-31/release-manifest.json`
   - Browser extension package: `dist/browser-extension/chaseos-capture-to-markdown-0.1.0.zip`
4. Verification evidence:
   - Packaged Capture proof: `07_LOGS/Visual-QA/2026-05-31-capture-markdown-final-closeout-clickthrough-r2/2026-05-31-capture-markdown-final-closeout-clickthrough-r2.json`
   - Packaged no-PowerShell open-safety proof: `07_LOGS/Visual-QA/2026-05-31-capture-markdown-final-closeout-open-safety-r2/2026-05-31-capture-markdown-final-closeout-open-safety-r2.json`
   - Add-on proof accounting: `07_LOGS/Visual-QA/2026-05-31-capture-markdown-proof-accounting/proof-accounting-summary.json`
5. Operator-only release step: public/outside-machine distribution requires an externally issued public certificate-authority code-signing certificate with private key. After the certificate is installed, follow `07_LOGS/Operator-Briefs/2026-05-31-capture-markdown-public-signing-handoff.md`.
6. Do not reopen Capture to Markdown implementation unless new product requirements are added. Public certificate-authority signing is a release/signing operation, not a local feature gap.

## Current Launch Next Action - 2026-05-31

1. Treat `https://chaseos.ai` as the selected primary public launch domain. Do not reopen this decision.
2. Build the truthful public surface first: landing page, waitlist, `/studio`, `/forge`, `/forge/index.json`, `/standards`, `/open-core`, `/pricing`, `/privacy`, `/security`, `/terms`, `/docs`, `/download`, `/roadmap`, `/support`, `/creators`, and `/submit-pack`.
3. Keep the public claim as ChaseOS Studio Early Access / Developer Preview until public-doc hygiene, Studio route smoke, legal/privacy wiring, package/license/export decision, and a recorded green release-smoke packet are complete.
4. Keep Chaser Forge status at domain-selected/static-index-upload-pending/live-fetch-approval-gated until `https://chaseos.ai/forge/index.json` exists, digest-verifies, and is explicitly approved.
5. Do not deploy, mutate DNS, send emails, create Stripe products, enable managed agents, enable payments/licensing, or claim browser automation/marketplace/managed-agent completion without separate proof and approval.


## Current MVP Next Action - 2026-05-14

1. Create or confirm the OpenAI secret outside this repo.
   - Recommended reference name: `OPENAI_API_KEY`
   - Do not paste the API key value into repo files, logs, Obsidian, or chat.
2. Validate the no-secret operator template:

```powershell
python -m runtime.cli.main mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json
```

3. After the outside-repo reference exists, preview the metadata-only setup update:

```powershell
python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --dry-run --json
```

4. Re-check the stop/continue gate:

```powershell
python -m runtime.cli.main mvp operator-action-required --json
```

Current state remains `PARTIAL / OPERATOR ACTION REQUIRED`; Codex must not call `update_goal` while `safe_to_call_update_goal_complete=false`.

## Recommended First Actions
1. Review `SOUL.md`
2. Review `00_HOME/Operating-System.md`
3. Fill in `00_HOME/Now.md`
4. Confirm runtime/provider/integration setup

## Notes
- This file should help a new operator orient quickly after scaffold creation.
