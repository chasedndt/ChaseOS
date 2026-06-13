from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DOMAIN = "https://chaseos.ai"


PACKS = [
    {
        "id": "startup_validation_launch",
        "name": "Startup Validation Launch",
        "version": "0.1.0",
        "description": "Preview pack for turning an idea into research notes, landing-page copy, approval packets, and a launch-readiness decision.",
        "category": "founder",
    },
    {
        "id": "content_distribution_pack",
        "name": "Content Distribution Pack",
        "version": "0.1.0",
        "description": "Drafts channel-specific content plans and blocked external-action approval packets without posting automatically.",
        "category": "content",
    },
    {
        "id": "research_briefing_pack",
        "name": "Research Briefing Pack",
        "version": "0.1.0",
        "description": "Organizes source-backed research briefs with provenance and outcome records.",
        "category": "research",
    },
    {
        "id": "local_developer_ops_pack",
        "name": "Local Developer Ops Pack",
        "version": "0.1.0",
        "description": "Creates repo-inspection, patch, and test-run packets for bounded developer-agent workflows.",
        "category": "developer-ops",
    },
    {
        "id": "ecommerce_reselling_ops_pack",
        "name": "Ecommerce Reselling Ops Pack",
        "version": "0.1.0",
        "description": "Structures product research, listing drafts, content plans, and manual approval checkpoints.",
        "category": "commerce",
    },
    {
        "id": "agent_governance_pack",
        "name": "Agent Governance Pack",
        "version": "0.1.0",
        "description": "Audits runtime authority, approval posture, and blocked/future action lanes.",
        "category": "governance",
    },
]


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def sha256_json(data: dict) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def pack_manifest(pack: dict[str, str]) -> dict:
    return {
        "schema": "chaseos.pack.v1",
        "id": pack["id"],
        "name": pack["name"],
        "version": pack["version"],
        "description": pack["description"],
        "category": pack["category"],
        "status": "preview",
        "author": "ChaseOS",
        "license": "example-free-preview-no-entitlement",
        "compatibility": {"chaseos": ">=0.8.0", "studio": "early-access"},
        "permissions_required": ["read_declared_sources", "write_preview_outputs"],
        "approval_required": True,
        "docs_url": f"{DOMAIN}/forge",
        "package_scope": "example_preview_metadata",
        "authority_boundary": {
            "external_actions": "blocked_pending_operator_approval",
            "payment_required": False,
            "license_enforcement_enabled": False,
            "auto_install_enabled": False,
            "untrusted_remote_install_allowed": False,
        },
    }


def pack_index_entry(pack: dict[str, str]) -> dict:
    manifest = pack_manifest(pack)
    return {
        **pack,
        "status": "preview",
        "author": manifest["author"],
        "price_class": "free_example_preview",
        "license": manifest["license"],
        "certification_status": "uncertified_preview_example",
        "compatibility": manifest["compatibility"],
        "permissions_required": manifest["permissions_required"],
        "approval_required": True,
        "manifest_url": f"{DOMAIN}/forge/packs/{pack['id']}/manifest.json",
        "docs_url": manifest["docs_url"],
        "digest_algorithm": "sha256",
        "manifest_digest_sha256": sha256_json(manifest),
        "install_boundary": "manual_preview_only_no_auto_install",
        "submission_url": f"{DOMAIN}/submit-pack",
        "authority_boundary": manifest["authority_boundary"],
    }


def forge_index_payload() -> dict:
    return {
        "schema": "chaseos.forge-index.v1",
        "status": "preview_static_index",
        "base_url": DOMAIN,
        "index_url": f"{DOMAIN}/forge/index.json",
        "generated_at": "2026-05-31T00:00:00Z",
        "marketplace_payments": "not_enabled",
        "licensing_entitlements": "not_enabled",
        "creator_payouts": "not_enabled",
        "remote_install": "manual_preview_only_approval_gated_future",
        "external_registry_mutation": "not_enabled",
        "pack_submission_url": f"{DOMAIN}/submit-pack",
        "creator_interest_url": f"{DOMAIN}/creators",
        "packs": [pack_index_entry(pack) for pack in PACKS],
    }


def forge_standard_example() -> dict:
    index = forge_index_payload()
    return {
        key: index[key]
        for key in [
            "schema",
            "status",
            "base_url",
            "index_url",
            "marketplace_payments",
            "licensing_entitlements",
            "remote_install",
            "packs",
        ]
    }


STANDARDS = {
    "chaseos.pack.json": {
        "schema": "chaseos.pack.v1.preview",
        "status": "preview",
        "preview_notice": "Draft example for public review; not a stable API contract.",
        "id": "startup_validation_launch",
        "name": "Startup Validation Launch",
        "version": "0.1.0",
        "description": "Example workflow pack manifest for a launch-readiness mission.",
        "permissions_required": ["read_declared_sources", "write_preview_outputs"],
        "approval_required": True,
        "entrypoints": [
            {"id": "collect_sources", "type": "source.review", "writes": ["source_evidence"]},
            {"id": "draft_outputs", "type": "mission.generate", "writes": ["preview_outputs"]},
            {"id": "request_approval", "type": "approval.packet", "writes": ["approval_request"]},
        ],
        "external_actions": "blocked_until_operator_approval",
    },
    "chaseos.forge-index.json": forge_standard_example(),
    "chaseos.agent.json": {
        "schema": "chaseos.agent.v1",
        "runtime": "Codex",
        "task_types": ["repo.inspect", "code.patch", "code.review", "test.run"],
        "authority": "bounded_development_runtime",
    },
    "chaseos.approval.json": {
        "schema": "chaseos.approval.v1.preview",
        "status": "pending_operator_review",
        "preview_notice": "Approval packet example only; it does not grant execution authority.",
        "approval_id": "appr-demo-launch-publish",
        "requested_action": {
            "type": "external_publish",
            "target": "public_website_deploy",
            "summary": "Deploy the static ChaseOS public-site preview after human review.",
        },
        "risk_tier": "external_visibility",
        "required_reviewer": "operator",
        "execution_allowed": False,
        "decision": None,
    },
    "chaseos.graph.json": {
        "schema": "chaseos.graph.v1.preview",
        "status": "preview",
        "preview_notice": "Public-safe graph shape example with synthetic IDs only.",
        "nodes": [
            {"id": "project.chaseos-public-launch", "type": "project", "label": "ChaseOS public launch"},
            {"id": "pack.startup_validation_launch", "type": "workflow_pack", "label": "Startup Validation Launch"},
            {"id": "approval.appr-demo-launch-publish", "type": "approval", "label": "Deploy approval"},
            {"id": "outcome.run-demo-launch-readiness", "type": "outcome", "label": "Launch readiness output"},
        ],
        "edges": [
            {"from": "project.chaseos-public-launch", "to": "pack.startup_validation_launch", "type": "uses_pack"},
            {"from": "pack.startup_validation_launch", "to": "approval.appr-demo-launch-publish", "type": "requests_approval"},
            {"from": "approval.appr-demo-launch-publish", "to": "outcome.run-demo-launch-readiness", "type": "gates_outcome"},
        ],
        "private_graph_exported": False,
    },
    "chaseos.source.json": {
        "schema": "chaseos.source.v1",
        "source_id": "source.launch-handover",
        "trust": "repo-local",
        "provenance": "declared_demo_fixture",
    },
    "chaseos.outcome.json": {
        "schema": "chaseos.outcome.v1.preview",
        "status": "preview_generated",
        "preview_notice": "Outcome record example only; anonymous aggregate sharing is opt-in and not enabled here.",
        "run_id": "run-demo-launch-readiness",
        "pack_id": "startup_validation_launch",
        "outputs": [
            {"id": "landing-page-copy", "type": "draft", "visibility": "public_safe_preview"},
            {"id": "standards-examples", "type": "artifact", "visibility": "public_safe_preview"},
        ],
        "local_only": True,
        "telemetry_opt_in": False,
        "external_actions_executed": [],
    },
    "chaseos.entitlement.json": {
        "schema": "chaseos.entitlement.v1",
        "status": "future_not_enabled",
        "license_mutation_allowed": False,
    },
    "chaseos.managed-job.json": {
        "schema": "chaseos.managed-job.v1",
        "status": "future_not_enabled",
        "managed_runtime_available": False,
    },
}


ROUTES = {
    "": {
        "title": "ChaseOS",
        "summary": "The local-first AI operating system for builders running real projects with agents.",
        "body": """
<section class="hero">
  <div>
    <p class="trust-line">Human intent. Agentic execution. Private control.</p>
    <h1>ChaseOS is the local-first AI operating system for builders running real projects with agents.</h1>
    <p class="lead">ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.</p>
    <div class="actions"><a class="button primary" href="waitlist/">Join the early access waitlist</a><a class="button" href="forge/">Explore Chaser Forge</a><a class="button ghost" href="docs/">Read the docs</a></div>
  </div>
  <figure class="visual-card">
    <img src="assets/chaseos-launch-map.svg" alt="ChaseOS graph connecting Studio, Forge, standards, approvals, sources, and runtimes" />
    <figcaption>Early Access preview: local graph, bounded runtimes, approval visibility, and Forge packs.</figcaption>
  </figure>
</section>
<section class="band">
  <h2>One private command layer for AI work</h2>
  <div class="grid three">
    <article><h3>ChaseOS Studio</h3><p>The desktop command surface for local memory, projects, sources, graph views, approvals, runtime awareness, and workflow packs.</p></article>
    <article><h3>Governed knowledge graph</h3><p>Sources, decisions, outputs, workflows, approvals, runtime activity, and logs stay connected instead of scattered across tools.</p></article>
    <article><h3>Bounded agent operation</h3><p>Runtimes operate through declared permissions, visible status, approval gates, and audit trails. No silent external actions.</p></article>
  </div>
</section>
<section>
  <h2>Early Access scope</h2>
  <div class="status-list">
    <p><strong>Ready/preview:</strong> local-first memory, Source Intelligence Core, bounded AOR workflows, Studio surfaces, approval visibility, workflow/mission packs, Forge static preview, and draft standards.</p>
    <p><strong>Blocked/future:</strong> marketplace checkout, hosted runtime operation, unbounded browser operation, external posting, customer-system writes, billing-system writes, and enterprise deployment readiness.</p>
  </div>
</section>
""",
    },
    "waitlist": {
        "title": "Join ChaseOS Studio Early Access",
        "summary": "Register interest without creating an account or sending data to a model provider.",
        "body": """
<section class="split">
  <div>
    <h1>Join the early access waitlist.</h1>
    <p class="lead">Tell us what kind of AI-native work you want ChaseOS to help govern. Safe static placeholder validation runs in the browser only; Production storage is not enabled in this repository.</p>
    <ul class="check-list"><li>No outbound email campaign is wired.</li><li>No provider/model calls run on waitlist data.</li><li>Backend/storage decision required before real signup capture: choose an approved database/form backend, retention policy, admin auth, and export owner.</li></ul>
  </div>
  <form id="waitlist-form" class="panel" novalidate>
    <label>Email <input name="email" type="email" autocomplete="email" required /></label>
    <label>Name <input name="name" type="text" autocomplete="name" required /></label>
    <label>Persona <select name="persona" required><option value="">Select one</option><option>AI builder</option><option>Founder</option><option>Developer</option><option>Creator-builder</option><option>Researcher</option><option>Team lead</option><option>Other</option></select></label>
    <label>Current tools <textarea name="current_tools" required placeholder="AI chats, docs, repos, Notion, Linear, browser automations, agents, etc."></textarea></label>
    <label>Biggest AI-workflow pain <textarea name="biggest_ai_workflow_pain" required></textarea></label>
    <label>Use case <textarea name="use_case" required></textarea></label>
    <label>Interest type <select name="interest_type" required><option value="">Select one</option><option>Studio Early Access</option><option>Chaser Forge creator</option><option>Team/private deployment</option><option>Standards / open-core collaboration</option><option>Other</option></select></label>
    <label>Operating system <select name="operating_system" required><option value="">Select one</option><option>Windows</option><option>macOS</option><option>Linux</option><option>WSL</option><option>Mixed / team environment</option><option>Other</option></select></label>
    <label>Willingness to pay <select name="willingness_to_pay" required><option value="">Select one</option><option>Free/local only</option><option>Would consider Pro</option><option>Would consider team plan</option><option>Would consider setup sprint</option><option>Undecided</option></select></label>
    <label>Source/UTM <input name="source_utm" type="text" required placeholder="Launch post, referral, search, event, utm_campaign" /></label>
    <input type="hidden" name="created_at" value="client_generated_on_submit" />
    <label class="consent"><input name="consent_to_contact" type="checkbox" required /> I consent to be contacted about ChaseOS early access. No outbound email campaign is wired in this static build.</label>
    <button type="submit">Validate waitlist entry locally</button>
    <p id="waitlist-result" role="status"></p>
  </form>
</section>
""",
    },
    "studio": {
        "title": "ChaseOS Studio",
        "summary": "The desktop command center for ChaseOS.",
        "body": """
<section><h1>ChaseOS Studio is the command center.</h1><p class="lead">Studio surfaces local project memory, knowledge graph visibility, source/project organization, workflow packs, runtime status, approval queues, logs, and privacy/provider state.</p></section>
<section class="grid four"><article><h3>Home</h3><p>Product status, current work, and safe next actions.</p></article><article><h3>Graph</h3><p>Source, project, decision, approval, workflow, and runtime relationships.</p></article><article><h3>Missions</h3><p>Workflow packs with local preview, approval, and result evidence lanes.</p></article><article><h3>Runtimes</h3><p>Bounded runtime awareness without granting managed-agent authority.</p></article></section>
""",
    },
    "demo": {
        "title": "Public Demo Fixture",
        "summary": "Public-safe sample data for graph, source, runtime, approval, and mission previews.",
        "body": """
<section><h1>Public-safe demo fixture for ChaseOS Studio.</h1><p class="lead">This route shows the sample surfaces V1 can preview without exposing private vault paths, secrets, customer records, or live runtime authority.</p></section>
<section class="grid three">
  <article><h3>Graph visibility</h3><p>Demo nodes connect a public launch project to sources, approvals, runtimes, mission packs, and outputs.</p><p><a href="../standards/examples/chaseos.graph.json">Graph standard example</a></p></article>
  <article><h3>Source/project organization</h3><p>Source fixtures identify public docs and synthetic example inputs, keeping project context visible but non-private.</p><p><a href="../standards/examples/chaseos.source.json">Source standard example</a></p></article>
  <article><h3>Runtime/agent awareness</h3><p>Runtime fixture cards describe bounded demo lanes only; they do not start agents, claim tasks, or grant execution.</p><p><a href="../standards/examples/chaseos.agent.json">Agent standard example</a></p></article>
  <article><h3>Approval visibility</h3><p>Approval packets stay pending or blocked, with <code>execution_allowed=false</code> for every external action.</p><p><a href="../standards/examples/chaseos.approval.json">Approval standard example</a></p></article>
  <article><h3>Mission pack preview</h3><p>The launch readiness mission previews workflow steps, evidence expectations, and blocked external action gates.</p><p><a href="../forge/packs/startup_validation_launch/manifest.json">Startup validation pack</a></p></article>
  <article><h3>Fixture files</h3><p><code>fixtures/demo/chaseos_launch/graph_nodes.json</code>, mission, approval, and output files are public-safe sample data.</p><p>No runtime authority is granted by this route.</p></article>
</section>
""",
    },
    "forge": {
        "title": "Chaser Forge",
        "summary": "Preview catalog for ChaseOS workflow packs, operating kits, templates, agent presets, and extensions.",
        "body": """
<section><h1>Chaser Forge is the marketplace path for ChaseOS packs.</h1><p class="lead">V1 is a static preview catalog with free examples, creator interest, and standards. Paid packs, creator payouts, and untrusted third-party installs are future.</p><div class="actions"><a class="button primary" href="index.json">View /forge/index.json</a><a class="button" href="../submit-pack/">Submit a pack idea</a></div></section>
<section class="grid three pack-grid" id="pack-grid"></section>
<section class="status-list"><p><strong>Now:</strong> preview catalog, example packs, creator waitlist, standards preview.</p><p><strong>Future:</strong> paid packs, 9% creator marketplace fee, certified packs, managed/runtime packs, team/private catalogs.</p></section>
""",
    },
    "standards": {
        "title": "ChaseOS Standards",
        "summary": "Portable examples for packs, Forge indexes, agents, approvals, graph objects, source evidence, and outcomes.",
        "body": """
<section><h1>Standards make AI work inspectable.</h1><p class="lead">ChaseOS standards capture portable, public-safe shapes for workflow packs, Forge catalog entries, approval packets, graph objects, and outcome records.</p></section>
<section class="status-list"><p><strong>Status:</strong> preview examples only. These files are draft scaffolds for V1 public review, not stable public APIs, live validators, managed entitlements, checkout, remote install, or hosted job authority.</p></section>
<section class="grid three">
  <article><h3>Pack manifest</h3><p><a href="examples/chaseos.pack.json">chaseos.pack.json</a> describes a workflow pack, declared permissions, approval posture, and blocked external actions.</p></article>
  <article><h3>Forge index</h3><p><a href="examples/chaseos.forge-index.json">chaseos.forge-index.json</a> sketches a static pack catalog without live paid marketplace, managed entitlements, or remote-install jobs.</p></article>
  <article><h3>Approval packet</h3><p><a href="examples/chaseos.approval.json">chaseos.approval.json</a> shows the human-review gate before any external action can execute.</p></article>
  <article><h3>Graph object</h3><p><a href="examples/chaseos.graph.json">chaseos.graph.json</a> uses synthetic nodes and edges to show how projects, packs, approvals, and outcomes connect.</p></article>
  <article><h3>Outcome record</h3><p><a href="examples/chaseos.outcome.json">chaseos.outcome.json</a> records local-only generated outputs and opt-in telemetry posture.</p></article>
  <article><h3>Additional drafts</h3><p><a href="examples/chaseos.agent.json">agent</a>, <a href="examples/chaseos.source.json">source</a>, <a href="examples/chaseos.entitlement.json">entitlement</a>, and <a href="examples/chaseos.managed-job.json">managed-job</a> examples remain secondary preview scaffolds.</p></article>
</section>
<p class="notice">Preview boundary: no full stable API is claimed; no live managed entitlements, managed jobs, checkout, runtime credits, or untrusted third-party auto-install are enabled.</p>
""",
    },
    "open-core": {
        "title": "Open-Core Posture",
        "summary": "Open where trust matters. Paid where reliability, convenience, distribution, and scale matter.",
        "body": "<section><h1>Open where trust matters.</h1><p class='lead'>ChaseOS should be inspectable around local data, standards, pack manifests, approvals, and example packs. Commercial layers can cover premium packs, hosted account services, managed runtimes, team governance, and support.</p></section>",
    },
    "pricing": {
        "title": "Pricing Preview",
        "summary": "Free local starter now; paid layers are planned, not live.",
        "body": "<section><h1>Pricing is planned, not live.</h1><div class='grid three'><article><h3>Free / Local Starter</h3><p>Run the local-first core and preview public standards.</p></article><article><h3>Pro Builder</h3><p>Planned around GBP19/month for maintained Studio conveniences, premium packs, and account services.</p></article><article><h3>Future</h3><p>Teams, Forge paid packs, managed agents, runtime credits, and enterprise/private deployment are not active in V1.</p></article></div></section>",
    },
    "docs": {
        "title": "Docs",
        "summary": "Public-safe documentation hub for Early Access.",
        "body": "<section><h1>Docs for builders and pack creators.</h1><p class='lead'>Start with Studio, Forge, standards, privacy, security, and roadmap pages. Internal ledgers, private paths, and secrets stay out of public docs.</p><div class='actions'><a class='button' href='../standards/'>Standards</a><a class='button' href='../forge/'>Forge</a><a class='button' href='../security/'>Security</a></div></section>",
    },
    "download": {
        "title": "Download",
        "summary": "ChaseOS Studio Early Access is not a public download yet.",
        "body": "<section><h1>Download is gated by Early Access.</h1><p class='lead'>The local Studio build has internal proof, but public distribution still requires public code-signing, release-smoke, and operator approval. Join the waitlist for access updates.</p><a class='button primary' href='../waitlist/'>Join Early Access</a></section>",
    },
    "privacy": {
        "title": "Privacy",
        "summary": "Local-first by default. Your private graph stays yours.",
        "body": "<section><h1>Your private graph stays yours.</h1><p class='lead'>ChaseOS stores local project memory and generated outputs in the user's system by default. Waitlist data is only what you submit. No provider/model calls are made over waitlist PII by this static site. Optional telemetry is future and must be opt-in.</p></section>",
    },
    "security": {
        "title": "Security",
        "summary": "Approval-gated execution, Gate posture, and Early Access caveats.",
        "body": "<section><h1>Security starts with boundaries.</h1><p class='lead'>ChaseOS uses local-first control, approval-gated execution, Permission Matrix posture, source provenance, and audit logs. Secrets are not stored in frontend files. External actions remain blocked or approval-gated unless verified executors exist.</p></section>",
    },
    "roadmap": {
        "title": "Roadmap",
        "summary": "Ready, preview, blocked, and future lanes.",
        "body": "<section><h1>Early Access roadmap.</h1><div class='status-list'><p><strong>Ready/preview:</strong> local-first memory, source intelligence, graph visibility, Studio, workflow packs, approvals, Forge preview, standards.</p><p><strong>Future:</strong> paid Forge marketplace, hosted runtime operation, teams, runtime credits, unbounded browser operation, external posting, customer-system writes, billing-system writes, and enterprise deployment.</p></div></section>",
    },
    "support": {
        "title": "Support",
        "summary": "Support routes are not staffed as a full public desk yet.",
        "body": "<section><h1>Support is Early Access.</h1><p class='lead'>Use the waitlist/support interest path until a formal help desk exists. Security issues should use the security contact once it is published.</p></section>",
    },
    "terms": {
        "title": "Terms",
        "summary": "Draft Early Access terms, not lawyer-reviewed.",
        "body": "<section><h1>Early Access terms are draft.</h1><p class='lead'>ChaseOS V1 is preview software. AI outputs may be wrong. Users remain responsible for external actions. Marketplace, managed-agent, account, billing, and enterprise features are future unless separately enabled and approved.</p></section>",
    },
    "creators": {
        "title": "Creators",
        "summary": "Build workflow packs, operating kits, templates, and extensions for Chaser Forge.",
        "body": "<section><h1>Build for Chaser Forge.</h1><p class='lead'>Creators can shape packs around founder workflows, content ops, research, developer ops, ecommerce, education, and governance. Paid packs, certification, and managed runtime support are planned future lanes.</p><a class='button primary' href='../submit-pack/'>Submit a pack idea</a></section>",
    },
    "submit-pack": {
        "title": "Submit a Pack",
        "summary": "Creator submission interest form. Static validation only.",
        "body": """
<section class="split"><div><h1>Submit a pack idea.</h1><p class="lead">Tell us what operating kit or workflow pack you want to build. This static preview does not store submissions.</p></div>
<form id="pack-form" class="panel" novalidate>
  <label>Creator name <input name="creator_name" required /></label>
  <label>Email <input name="email" type="email" required /></label>
  <label>Pack name <input name="pack_name" required /></label>
  <label>Problem solved <textarea name="problem_solved" required></textarea></label>
  <label>External actions needed <textarea name="external_actions"></textarea></label>
  <label class="consent"><input name="consent_to_contact" type="checkbox" required /> I consent to be contacted about Forge creator access.</label>
  <button type="submit">Validate pack submission</button><p id="pack-result" role="status"></p>
</form></section>
""",
    },
    "admin": {
        "title": "Admin",
        "summary": "Internal admin console stub. Not enabled in public builds.",
        "noindex": True,
        "body": "<section><h1>Admin console requires auth before any data exists.</h1><p class='lead'>This static route is a disabled, protected stub for a future auth allowlist. It may eventually review waitlist signups, creator interest, qualification/invite status, notes, and Safe export preview fields only after an approved backend exists.</p><p class='notice'>Status: DISABLED / AUTH REQUIRED STUB / NO PII.</p><ul class='check-list'><li>No waitlist PII is embedded in this build.</li><li>No admin API, storage adapter, provider call, or runtime-log reader is wired.</li><li>Forbidden surfaces remain excluded: local vaults, private graphs, provider keys, runtime logs, and private project memory.</li></ul></section>",
    },
}


CSS = """
:root{--bg:#f7f7f4;--ink:#151716;--muted:#5e6661;--line:#d9ddd5;--panel:#ffffff;--green:#2f6b4f;--teal:#1f6f78;--gold:#b77a27;--red:#8e3f38;--shadow:0 18px 55px rgba(30,35,31,.12)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55}a{color:var(--green);text-decoration:none}a:hover{text-decoration:underline}.site-header{position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px clamp(20px,4vw,56px);background:rgba(247,247,244,.94);border-bottom:1px solid var(--line);backdrop-filter:blur(14px)}.brand{font-weight:800;font-size:20px;letter-spacing:0}.nav{display:flex;flex-wrap:wrap;gap:14px;font-size:14px}.nav a{color:var(--ink)}main{padding:54px clamp(20px,5vw,72px) 80px}.hero,.split{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:48px;align-items:center}.trust-line{font-weight:700;color:var(--green);margin:0 0 14px}h1{font-size:clamp(42px,5vw,76px);line-height:.98;margin:0 0 22px;letter-spacing:0}h2{font-size:clamp(28px,3vw,42px);line-height:1.1;margin:0 0 24px;letter-spacing:0}h3{font-size:20px;margin:0 0 10px}.lead{font-size:clamp(19px,2vw,24px);color:var(--muted);max-width:780px}.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}.button,button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:11px 18px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);font-weight:700;cursor:pointer}.button.primary,button{background:var(--green);border-color:var(--green);color:#fff}.button.ghost{background:transparent}.visual-card,.panel,article{background:var(--panel);border:1px solid var(--line);border-radius:8px;box-shadow:var(--shadow)}.visual-card{margin:0;padding:22px}.visual-card img{width:100%;height:auto;display:block}.visual-card figcaption{color:var(--muted);font-size:14px;margin-top:12px}.band,section{margin-top:70px}.grid{display:grid;gap:18px}.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.grid.four{grid-template-columns:repeat(4,minmax(0,1fr))}article{padding:22px}article p{color:var(--muted);margin:0}.status-list{display:grid;gap:12px}.status-list p,.notice{border-left:4px solid var(--green);background:var(--panel);padding:16px 18px;margin:0;border-radius:6px}.notice{border-left-color:var(--gold);color:var(--muted)}form.panel{padding:24px;display:grid;gap:15px}label,fieldset{display:grid;gap:7px;font-weight:700}fieldset{border:1px solid var(--line);border-radius:8px;padding:14px}fieldset label,.consent{display:flex;align-items:flex-start;gap:9px;font-weight:600}input,textarea,select{width:100%;border:1px solid var(--line);border-radius:8px;padding:11px 12px;font:inherit;background:#fff}textarea{min-height:88px}.check-list{color:var(--muted)}footer{padding:34px clamp(20px,4vw,56px);border-top:1px solid var(--line);color:var(--muted);display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}.pack-grid article{position:relative}.pack-grid small{display:block;color:var(--muted);margin-top:10px}@media(max-width:900px){.hero,.split{grid-template-columns:1fr}.grid.three,.grid.four{grid-template-columns:1fr}.site-header{align-items:flex-start;flex-direction:column}main{padding-top:34px}h1{font-size:40px}}@media(prefers-reduced-motion:no-preference){.button,button{transition:transform .16s ease}.button:hover,button:hover{transform:translateY(-1px)}}
"""


JS = """
const packs = __PACKS__;
function validateEmail(value){return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(value)}
function wireForm(formId,resultId,requiredNames){const form=document.getElementById(formId);if(!form)return;const result=document.getElementById(resultId);form.addEventListener('submit',event=>{event.preventDefault();const data=new FormData(form);const missing=requiredNames.filter(name=>!String(data.get(name)||'').trim());const email=String(data.get('email')||'');if(email&&!validateEmail(email))missing.push('valid email');if(missing.length){result.textContent='Missing: '+[...new Set(missing)].join(', ');result.style.color='#8e3f38';return}result.textContent='Validated locally. Safe static placeholder only: no storage, no email campaign, no provider/model calls.';result.style.color='#2f6b4f';})}
function renderPacks(){const grid=document.getElementById('pack-grid');if(!grid)return;grid.innerHTML=packs.map(pack=>`<article><h3>${pack.name}</h3><p>${pack.description}</p><small>${pack.category} / ${pack.status}</small></article>`).join('')}
wireForm('waitlist-form','waitlist-result',['email','name','persona','current_tools','biggest_ai_workflow_pain','use_case','interest_type','operating_system','willingness_to_pay','source_utm','consent_to_contact']);
wireForm('pack-form','pack-result',['creator_name','email','pack_name','problem_solved','consent_to_contact']);
renderPacks();
"""


SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 620" role="img" aria-labelledby="title desc">
  <title id="title">ChaseOS launch graph preview</title>
  <desc id="desc">A visual map of ChaseOS Studio connecting graph, sources, runtimes, approvals, missions, standards, and Forge.</desc>
  <rect width="900" height="620" rx="24" fill="#eef2ed"/>
  <rect x="52" y="52" width="796" height="516" rx="22" fill="#ffffff" stroke="#d7ddd5"/>
  <text x="92" y="112" font-family="Inter, Arial, sans-serif" font-size="34" font-weight="800" fill="#151716">ChaseOS Launch Graph</text>
  <text x="92" y="146" font-family="Inter, Arial, sans-serif" font-size="18" fill="#5e6661">local memory + bounded agents + approval visibility</text>
  <g fill="none" stroke="#9eb4a5" stroke-width="3">
    <path d="M450 300 L210 208"/><path d="M450 300 L690 208"/><path d="M450 300 L210 420"/><path d="M450 300 L690 420"/>
    <path d="M450 300 L450 500"/><path d="M450 300 L450 130"/>
  </g>
  <g font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700">
    <circle cx="450" cy="300" r="84" fill="#2f6b4f"/><text x="450" y="292" text-anchor="middle" fill="#fff">ChaseOS</text><text x="450" y="318" text-anchor="middle" fill="#dce9df">Studio</text>
    <rect x="112" y="168" width="196" height="80" rx="16" fill="#e6f0ea" stroke="#bad0c1"/><text x="210" y="214" text-anchor="middle" fill="#1d3f30">Sources</text>
    <rect x="592" y="168" width="196" height="80" rx="16" fill="#e9f0f2" stroke="#b8cdd0"/><text x="690" y="214" text-anchor="middle" fill="#1f5c63">Runtimes</text>
    <rect x="112" y="380" width="196" height="80" rx="16" fill="#f5eee4" stroke="#dfc7a3"/><text x="210" y="426" text-anchor="middle" fill="#83591d">Missions</text>
    <rect x="592" y="380" width="196" height="80" rx="16" fill="#f2e8e6" stroke="#d8b7b2"/><text x="690" y="426" text-anchor="middle" fill="#73352e">Approvals</text>
    <rect x="354" y="90" width="192" height="80" rx="16" fill="#eef4ec" stroke="#c4d9bc"/><text x="450" y="136" text-anchor="middle" fill="#2f6b4f">Standards</text>
    <rect x="354" y="460" width="192" height="80" rx="16" fill="#edf0fa" stroke="#c5cbe0"/><text x="450" y="506" text-anchor="middle" fill="#343f75">Forge</text>
  </g>
</svg>
"""


def rel_prefix(route: str) -> str:
    return "../" if route else ""


def page_path(route: str) -> Path:
    return ROOT / "index.html" if not route else ROOT / route / "index.html"


def nav(prefix: str) -> str:
    items = [("", "Home"), ("studio", "Studio"), ("demo", "Demo"), ("forge", "Forge"), ("standards", "Standards"), ("docs", "Docs"), ("waitlist", "Waitlist")]
    return "".join(f'<a href="{prefix}{path + "/" if path else ""}">{label}</a>' for path, label in items)


def render_page(route: str, page: dict[str, str]) -> str:
    prefix = rel_prefix(route)
    canonical = f"{DOMAIN}/{route}" if route else DOMAIN
    robots = '<meta name="robots" content="noindex,nofollow" />' if page.get("noindex") else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  {robots}
  <title>{page['title']} - ChaseOS</title>
  <meta name="description" content="{page['summary']}" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:title" content="{page['title']} - ChaseOS" />
  <meta property="og:description" content="{page['summary']}" />
  <meta property="og:url" content="{canonical}" />
  <link rel="stylesheet" href="{prefix}styles.css" />
</head>
<body data-page="{route or 'home'}">
  <header class="site-header"><a class="brand" href="{prefix}">ChaseOS</a><nav class="nav" aria-label="Primary">{nav(prefix)}</nav></header>
  <main>{page['body']}</main>
  <footer><span>Start at {DOMAIN}.</span><span>ChaseOS Studio Early Access / Developer Preview. Payments, managed agents, and live external actions are not enabled.</span></footer>
  <script src="{prefix}site.js"></script>
</body>
</html>
"""


def forge_index() -> dict:
    return forge_index_payload()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> None:
    (ROOT / "assets").mkdir(parents=True, exist_ok=True)
    (ROOT / "styles.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (ROOT / "site.js").write_text(JS.replace("__PACKS__", json.dumps([{**p, "status": "preview"} for p in PACKS])).strip() + "\n", encoding="utf-8")
    (ROOT / "assets" / "chaseos-launch-map.svg").write_text(SVG.strip() + "\n", encoding="utf-8")

    for route, page in ROUTES.items():
        target = page_path(route)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(route, page), encoding="utf-8")

    index = forge_index()
    write_json(ROOT / "forge" / "index.json", index)
    for pack in PACKS:
        write_json(ROOT / "forge" / "packs" / pack["id"] / "manifest.json", pack_manifest(pack))

    for filename, data in STANDARDS.items():
        write_json(ROOT / "standards" / "examples" / filename, data)
        write_json(REPO / "docs" / "standards" / "examples" / filename, data)

    fixture_root = REPO / "fixtures" / "demo" / "chaseos_launch"
    fixture_root.mkdir(parents=True, exist_ok=True)
    (fixture_root / "README.md").write_text(
        "# ChaseOS Launch Demo Fixture\n\nPublic-safe demo fixture for the narrative: ChaseOS uses ChaseOS to launch ChaseOS. Contains no secrets, no personal paths, no real waitlist PII, and no external-action authority.\n\nFixture surfaces: graph visibility, source/project organization, runtime/agent awareness, approval visibility, and mission pack preview. These files are sample data only and do not grant runtime authority.\n",
        encoding="utf-8",
    )
    write_json(
        fixture_root / "graph_nodes.json",
        {
            "schema": "chaseos.graph.v1",
            "fixture_visibility": "public_safe_demo",
            "runtime_authority": "none_granted_fixture_only",
            "nodes": [
                {"id": "project.chaseos-public-launch", "type": "project", "label": "ChaseOS public launch demo"},
                {"id": "source.public-launch-brief", "type": "source", "label": "Public launch brief fixture"},
                {"id": "source.forge-preview-index", "type": "source", "label": "Forge preview index"},
                {"id": "runtime.hermes-demo-lane", "type": "runtime", "label": "Hermes demo lane", "execution_enabled": False},
                {"id": "runtime.openclaw-demo-lane", "type": "runtime", "label": "OpenClaw demo lane", "execution_enabled": False},
                {"id": "approval.publish-launch-copy", "type": "approval", "label": "Publish launch copy approval", "execution_allowed": False},
                {"id": "mission.launch-readiness-preview", "type": "mission", "label": "Launch readiness mission preview"},
                {"id": "pack.startup_validation_launch", "type": "pack", "label": "Startup Validation Launch"},
                {"id": "output.waitlist-plan", "type": "output", "label": "Synthetic waitlist plan"},
            ],
            "edges": [
                {"from": "project.chaseos-public-launch", "to": "source.public-launch-brief", "type": "uses_source"},
                {"from": "project.chaseos-public-launch", "to": "source.forge-preview-index", "type": "uses_source"},
                {"from": "project.chaseos-public-launch", "to": "mission.launch-readiness-preview", "type": "has_mission"},
                {"from": "mission.launch-readiness-preview", "to": "pack.startup_validation_launch", "type": "previews_pack"},
                {"from": "mission.launch-readiness-preview", "to": "runtime.hermes-demo-lane", "type": "shows_runtime_awareness"},
                {"from": "mission.launch-readiness-preview", "to": "runtime.openclaw-demo-lane", "type": "shows_runtime_awareness"},
                {"from": "mission.launch-readiness-preview", "to": "approval.publish-launch-copy", "type": "requires_approval"},
                {"from": "approval.publish-launch-copy", "to": "output.waitlist-plan", "type": "blocks_external_publish"},
            ],
        },
    )
    write_json(
        fixture_root / "launch_readiness_mission.json",
        {
            "schema": "chaseos.mission.v1",
            "fixture_visibility": "public_safe_demo",
            "runtime_authority": "none_granted_fixture_only",
            "status": "preview_fixture_no_execution",
            "name": "Launch Readiness Mission",
            "pack": "startup_validation_launch",
            "source_project": "project.chaseos-public-launch",
            "preview_steps": ["organize public sources", "render graph preview", "show runtime lane cards", "queue approval packets", "preview mission outputs"],
            "outputs": ["landing page copy", "waitlist plan", "launch posts", "Forge preview", "approval packets", "metrics targets"],
            "external_actions": "blocked_pending_operator_approval",
        },
    )
    write_json(
        fixture_root / "approval_packets.json",
        {
            "schema": "chaseos.approval.v1",
            "fixture_visibility": "public_safe_demo",
            "runtime_authority": "none_granted_fixture_only",
            "packets": [
                {"id": "deploy-site", "status": "pending_human_approval", "execution_allowed": False},
                {"id": "publish-launch-posts", "status": "blocked_no_external_send", "execution_allowed": False},
                {"id": "enable-payments", "status": "future_not_built", "execution_allowed": False},
            ],
        },
    )
    write_json(
        fixture_root / "outputs.json",
        {
            "schema": "chaseos.outcome.v1",
            "fixture_visibility": "public_safe_demo",
            "runtime_authority": "none_granted_fixture_only",
            "outputs": ["landing page copy", "waitlist plan", "Forge preview", "standards examples", "roadmap status"],
            "local_only": True,
            "contains_private_data": False,
            "external_delivery_enabled": False,
        },
    )


if __name__ == "__main__":
    build()
