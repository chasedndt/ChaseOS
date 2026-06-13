# Chaser OS Forge — Approved Extension Points & Safe Self-Extension Spec

**Document status:** Draft v0.1  
**Owner:** Chaser OS product/engineering  
**Intended use:** Paste into Codex, Claude Code, Abacus/AbacoX, or another repository-aware coding agent so it can inspect the Chaser OS repository and plan/build the feature safely.  
**Core idea:** Chaser OS should be able to build new Chaser OS modules from inside Chaser OS, but only through approved extension points that cannot break the core operating system.

---

## 1. Executive Summary

Chaser OS should include a new system-level feature called **Chaser Forge**.

Chaser Forge is a visual, AI-assisted builder that lets users describe a new feature, dashboard, page, workflow, agent, automation, or module in plain language. Chaser OS then turns the request into a structured feature spec, shows a live preview/demo of where it will appear in the interface, validates it, asks the user to approve permissions, and installs it into the user’s workspace.

This feature is not just an “AI coding assistant.” It is a **safe self-extension layer** for Chaser OS.

The fundamental rule:

> **Chaser Forge may extend Chaser OS, but it may not rewrite Chaser OS.**

Generated features should not edit arbitrary repo files, mutate core systems, bypass permissions, or touch secrets. Instead, they should compile into **extension manifests** and install only through approved extension points.

The intended lifecycle:

```text
User prompt
  → feature brief
  → extension manifest
  → UI/workflow/agent preview
  → validation
  → permission review
  → sandbox install, optional
  → live install
  → audit log + rollback snapshot
```

The builder should make non-technical users feel like they can create their own AI-powered modules without understanding GitHub, forks, pull requests, repo structure, routing, schemas, deployment, or code.

---

## 2. Product Framing

### Working name

**Chaser Forge**

Other names considered:

- Builder Studio
- Feature Lab
- Module Forge
- Agent Builder
- OS Builder
- Extension Lab
- Chaser Studio

### Product positioning

> **Chaser Forge lets anyone build, preview, and install custom AI-powered workflows, dashboards, agents, and workspace modules inside Chaser OS without touching code.**

Stronger positioning:

> **Describe the capability you need. Chaser OS designs it, previews it, validates it, and installs it safely into your workspace.**

This is a major differentiator. Most AI tools help developers write software. Chaser Forge helps users customize and extend their own agentic operating system.

---

## 3. The Main Problem To Solve

If the system allows AI-generated features to freely edit code, Chaser OS becomes fragile.

Bad pattern:

```text
User asks for feature
  → AI edits random files
  → global routes/layout/auth/data may change
  → core system breaks
```

Safe pattern:

```text
User asks for feature
  → AI creates structured spec
  → AI creates extension manifest
  → manifest is validated
  → extension is installed into allowed slots only
  → core remains protected
```

The hard part is not generating a dashboard page. The hard part is creating **approved extension points** so generated modules can be useful without gaining the ability to damage Chaser OS itself.

---

## 4. Non-Negotiable Safety Principle

Chaser Forge must operate like a controlled extension platform, not like an unrestricted coding agent.

### The builder can create

- New sidebar tabs
- New workspace pages
- New dashboard cards/widgets
- New forms
- New workflows
- New agent presets
- New workflow templates
- New data collections scoped to the extension
- New command palette actions
- New report templates
- New internal tools built from approved components
- New marketplace-ready templates
- New preview/demo experiences

### The builder cannot create or modify directly

- Authentication logic
- Authorization logic
- Billing/entitlement logic
- Secret storage
- Agent runtime internals
- Tool execution internals
- Extension validator internals
- Deployment configuration
- Package manager configuration
- Root app shell
- Core database schema
- Audit log system
- Security middleware
- Global CSS/theme primitives
- CI/CD config
- Any `.env` file
- Any unapproved external network behavior

---

## 5. Key Definitions

### Chaser OS Core

The protected foundation of Chaser OS.

The core includes:

- App shell
- Auth
- Permission engine
- Workspace system
- Routing foundation
- Core dashboard shell
- Data access layer
- Agent runtime
- Tool registry
- Connector framework
- Secrets management
- Billing/entitlements
- Extension registry
- Extension validator
- Installer/uninstaller
- Audit logs
- Rollback/kill switches
- Deployment/configuration

Generated features must not directly edit core systems.

### Extension

An installable module that adds functionality to Chaser OS through approved extension points.

Examples:

- “UGC Campaign Studio”
- “Shopify Growth Lab”
- “Trading Journal Lab”
- “Client Onboarding Studio”
- “AI Sales Team Dashboard”

### Extension Point

A controlled slot where extensions are allowed to attach.

Examples:

- Sidebar item slot
- Workspace page slot
- Dashboard widget slot
- Workflow template slot
- Agent preset slot
- Command palette slot
- Report template slot

### Extension Manifest

The structured source of truth for a generated feature.

It declares:

- Feature identity
- Version
- Routes
- UI components
- Agents
- Workflows
- Data schemas
- Permissions
- Preview mode
- Risk level
- Rollback strategy
- Compatibility requirements

### Preview Mode

A non-destructive demo mode using mock data and simulated agent/workflow output.

Preview mode must not:

- Write production data
- Call real external services
- Send messages
- Publish content
- Access secrets
- Install routes permanently
- Run background jobs

### Sandbox Install

An isolated installation for testing a feature with fake/test data. External side effects should remain disabled by default.

### Live Install

Installation into the user’s actual workspace after validation, permission approval, audit logging, and rollback snapshot creation.

---

## 6. Required System Architecture

Chaser Forge needs five layers:

```text
1. Builder UI
2. Feature planning/generation agents
3. Extension manifest/schema
4. Extension registry + approved extension points
5. Validator + permission + install/rollback system
```

### 6.1 Builder UI

The visible interface where users ask for new features and preview them.

Core screens:

- Forge home
- Prompt input
- Feature brief/spec screen
- Live preview/demo screen
- Permission review screen
- Sandbox/live install screen
- Extension management screen

### 6.2 Builder Agents

AI agents that help generate structured outputs.

Suggested agents:

- Product Architect Agent
- Extension Architect Agent
- UI Designer Agent
- Workflow Designer Agent
- Agent Designer Agent
- Manifest Writer Agent
- Security Reviewer Agent
- QA/Test Agent
- Demo Data Agent
- Installer Agent

Important rule:

> Builder agents can propose. The validator decides.

### 6.3 Extension Manifest

Every generated module must compile into a manifest. The manifest should be machine-validated before preview/install.

### 6.4 Extension Registry

A protected core service that knows which extensions exist, which workspace they belong to, which extension points they register, and whether they are draft/preview/sandbox/active/disabled/archived.

### 6.5 Validator + Installer

A protected core service that validates extension manifests, checks permissions, prevents core mutation, installs extensions, disables extensions, and rolls them back.

---

## 7. Approved Extension Points

This is the most important design area. The extension points must be narrow enough to keep the system safe but flexible enough to make the builder useful.

Each extension point should define:

- ID
- Purpose
- Allowed behavior
- Forbidden behavior
- Required manifest fields
- Runtime permission checks
- Rollback behavior
- UI host/renderer

---

### 7.1 Sidebar Navigation Extension Point

**ID:** `sidebar.nav.item`

**Purpose:** Let an extension add a visible item to the sidebar or workspace navigation.

**Allowed:**

- Add a new nav item
- Define label, icon, route, category, and order hint
- Group under approved parent sections
- Hide/show based on workspace permissions
- Link only to registered extension routes

**Forbidden:**

- Removing core sidebar items
- Renaming core sidebar items
- Reordering the global sidebar unless user-level sorting exists
- Claiming core labels deceptively, such as “Billing,” “Admin,” “Security,” “Login,” or “System Settings”
- Linking outside the approved route namespace
- Running code from a nav item click beyond route navigation or approved command dispatch

**Safe route pattern:**

```text
/workspace/:workspaceId/extensions/:extensionId
/workspace/:workspaceId/extensions/:extensionId/:pageId
```

**Manifest example:**

```json
{
  "extensionPoints": {
    "sidebar.nav.item": [
      {
        "id": "ugc-campaign-studio-nav",
        "label": "UGC Campaign Studio",
        "icon": "video",
        "section": "creator",
        "route": "/workspace/{workspaceId}/extensions/ugc-campaign-studio",
        "orderHint": 40
      }
    ]
  }
}
```

---

### 7.2 Workspace Page Extension Point

**ID:** `workspace.page`

**Purpose:** Let an extension render a full page inside the Chaser OS workspace shell.

**Allowed:**

- Render an extension page inside the existing shell
- Use approved UI components
- Read/write extension-scoped data
- Launch approved workflows
- Display approved agent panels
- Display mock data in preview mode

**Forbidden:**

- Replacing root layout
- Replacing shell providers
- Accessing global auth/session internals
- Registering unnamespaced root routes
- Writing directly to core tables
- Injecting scripts
- Using unsandboxed iframes
- Running arbitrary browser code
- Disabling error boundaries

**Manifest example:**

```json
{
  "extensionPoints": {
    "workspace.page": [
      {
        "id": "ugc-campaign-studio-home",
        "title": "UGC Campaign Studio",
        "route": "/workspace/{workspaceId}/extensions/ugc-campaign-studio",
        "layout": "dashboard",
        "components": [
          "campaign-brief-card",
          "script-generator-card",
          "shot-list-table",
          "asset-tracker-card",
          "delivery-checklist-card"
        ]
      }
    ]
  }
}
```

---

### 7.3 Dashboard Widget Extension Point

**ID:** `dashboard.widget`

**Purpose:** Let extensions add cards/widgets to approved dashboard areas.

**Allowed widget types:**

- KPI card
- Table card
- Checklist card
- Chart card
- Form card
- Agent summary card
- Workflow launcher card
- Kanban card
- Timeline card
- File upload card, scoped only
- Report card

**Forbidden:**

- Replacing core dashboard widgets
- Hiding existing widgets without user action
- Rendering invisible exfiltration components
- Calling external services during render without explicit connector permission
- Global CSS injection
- Raw HTML/script injection

**Required validation:**

- Widget type must be in approved registry
- Data source must be extension-scoped or approved read-only resource
- External connector use must be permissioned
- Preview widgets must use mock data

---

### 7.4 Agent Preset Extension Point

**ID:** `agent.preset`

**Purpose:** Let users create new agents without modifying the core agent runtime.

**Allowed:**

- Define agent name
- Define role
- Define visible instructions
- Define allowed tools
- Define memory scope
- Define max runtime/tool calls
- Define approval requirements
- Attach agent to extension pages/workflows

**Forbidden:**

- Editing the core runtime
- Granting unrestricted tools
- Granting global memory
- Reading secrets
- Disabling logs
- Hiding tool calls
- Bypassing approvals
- Giving agents permissions not declared in the manifest
- Creating hidden system instructions that contradict visible behavior

**Allowed memory scopes:**

```text
none
workflow-run
extension
workspace-approved-readonly
```

**Forbidden memory scopes:**

```text
global
all-workspaces
all-users
secrets
auth
billing
admin
```

**Manifest example:**

```json
{
  "agents": [
    {
      "id": "ugc-script-agent",
      "name": "UGC Script Agent",
      "role": "Creates platform-specific UGC scripts from a campaign brief.",
      "instructions": "Generate concise scripts using the provided campaign brief. Ask for missing context before producing final deliverables.",
      "tools": ["content.generate", "content.review"],
      "memoryScope": "extension",
      "requiresApprovalFor": ["clientSend", "externalPublish"],
      "maxRunMinutes": 5,
      "maxToolCalls": 8
    }
  ]
}
```

---

### 7.5 Workflow Template Extension Point

**ID:** `workflow.template`

**Purpose:** Let users define structured repeatable workflows.

**Allowed node types:**

```text
form.input
data.read.extension
data.write.extension
agent.task
approval.gate
transform.map
transform.filter
condition.branch
report.generate
notification.draft
connector.call.approved
file.upload.extension
file.read.extension
human.task
workflow.complete
```

**Forbidden node types:**

```text
shell.execute
code.eval
core.database.rawQuery
secrets.read
auth.modify
permissions.modify
billing.modify
audit.modify
deployment.modify
network.unrestricted
package.install
```

**Workflow validation rules:**

- Every node type must be approved
- Every data write must be extension-scoped
- Every connector call must declare permission
- Every external side effect must be behind an approval gate
- Every agent task must point to a valid agent preset
- Every workflow run must create audit events
- Every workflow must include failure/stop behavior

**Manifest example:**

```json
{
  "workflows": [
    {
      "id": "generate-ugc-campaign",
      "name": "Generate UGC Campaign",
      "trigger": {
        "type": "manual",
        "label": "Generate Campaign"
      },
      "steps": [
        { "id": "collect-brief", "type": "form.input", "schemaRef": "campaignBrief" },
        { "id": "generate-script", "type": "agent.task", "agentId": "ugc-script-agent" },
        { "id": "brand-review", "type": "agent.task", "agentId": "brand-qa-agent" },
        { "id": "human-approval", "type": "approval.gate", "required": true },
        { "id": "save-campaign", "type": "data.write.extension", "collection": "campaigns" }
      ]
    }
  ]
}
```

---

### 7.6 Form + Schema Extension Point

**ID:** `form.schema`

**Purpose:** Let an extension define forms and extension-scoped data collections.

**Allowed:**

- Create forms
- Create extension-scoped collections
- Validate fields
- Store user submissions in extension namespace
- Render forms through approved components

**Forbidden:**

- Writing to core user/workspace/session/auth/billing/audit tables
- Defining schemas that shadow core entities
- Storing secrets directly
- Creating unlimited file upload fields
- Creating hidden fields that capture sensitive data without disclosure

**Data naming rule:**

```text
ext_{extensionId}_{collectionName}
```

Examples:

```text
ext_ugc_campaign_studio_campaigns
ext_ugc_campaign_studio_scripts
ext_trading_journal_lab_trades
ext_shopify_growth_lab_experiments
```

---

### 7.7 Command Palette Extension Point

**ID:** `command.palette.action`

**Purpose:** Let extensions add commands to a command palette.

**Allowed:**

- Open extension page
- Start approved workflow
- Start approved agent run
- Create extension-scoped record
- Navigate to extension view

**Forbidden:**

- Impersonating core admin commands
- Bypassing permission checks
- Triggering external side effects without approval
- Running hidden automations
- Modifying core settings

---

### 7.8 Report Template Extension Point

**ID:** `report.template`

**Purpose:** Let extensions define reports, summaries, and exports.

**Allowed:**

- Generate reports from extension-scoped data
- Generate reports from approved read-only resources
- Export reports in approved formats
- Generate AI summaries from approved data

**Forbidden:**

- Exporting secrets
- Exporting data outside granted scope
- Sending reports externally without approval
- Hiding data sources used in reports

---

### 7.9 Notification Template Extension Point

**ID:** `notification.template`

**Purpose:** Let extensions create reminders and notification drafts.

**Allowed:**

- In-app reminders
- Notification drafts
- Email/Slack drafts through approved connectors
- Human approval before external send

**Forbidden:**

- Sending external notifications without approval unless explicitly configured by the user
- Sending system/security/billing/auth messages
- Modifying notification infrastructure
- Hiding recipients or message content

---

### 7.10 Connector Usage Extension Point

**ID:** `connector.usage`

**Purpose:** Let extensions request scoped access to existing connectors.

**Allowed:**

- Read-only connector access with permission
- Write connector access with stronger approval
- Use connector actions defined by the core tool registry
- Run all connector calls through audit logs

**Forbidden:**

- Reading connector credentials
- Creating raw unapproved network calls
- Creating webhooks without review
- Installing new connector infrastructure directly
- Bypassing rate limits

---

### 7.11 Marketplace Template Extension Point

**ID:** `marketplace.template`

**Purpose:** Let validated modules be shared, imported, and installed as templates.

**Allowed:**

- Package extension manifest
- Package mock data
- Package declarative UI schema
- Package workflow and agent presets
- Publish public/private templates after validation

**Forbidden:**

- Publishing secrets
- Publishing hidden permission requests
- Publishing core-mutating code
- Installing unsigned trusted-code extensions
- Hiding risk level

---

## 8. Protected Core Systems

Everything below must be considered protected core. Chaser Forge-generated extensions cannot directly modify these areas.

Actual repository paths may differ. The responsibility matters more than the path. If a file, folder, route, database table, or config participates in one of these responsibilities, it is protected.

---

### 8.1 Authentication and Identity

Protected:

- Login
- Logout
- OAuth
- Session creation
- Session refresh
- Account linking
- User identity resolution
- MFA
- Auth middleware
- Auth callbacks
- Token validation

Forbidden:

- Editing auth providers
- Changing session lifetime
- Reading auth tokens
- Adding fake login/auth routes
- Modifying auth callbacks
- Bypassing authentication checks

Example protected paths:

```text
/auth/**
/api/auth/**
/middleware/auth.*
/lib/auth/**
/server/auth/**
```

---

### 8.2 Authorization and Permissions

Protected:

- RBAC
- Permission policies
- Workspace membership
- Admin/owner rights
- Capability grants
- Approval gates
- Permission inheritance

Forbidden:

- Granting admin rights
- Bypassing role checks
- Editing permission policies from an extension
- Allowing an extension to approve itself
- Hiding permissions from the user

Example protected paths:

```text
/lib/permissions/**
/server/permissions/**
/policies/**
/rbac/**
```

---

### 8.3 Billing, Plans, Quotas, and Entitlements

Protected:

- Subscription state
- Plan limits
- Billing provider integration
- Usage caps
- Credits
- Feature entitlements
- Trial status

Forbidden:

- Disabling limits
- Granting paid features
- Changing billing records
- Accessing payment data
- Overriding plan checks

Example protected paths:

```text
/billing/**
/api/billing/**
/lib/entitlements/**
/lib/usage/**
```

---

### 8.4 Secrets and Credentials

Protected:

- `.env` files
- API keys
- OAuth refresh tokens
- Integration credentials
- Encryption keys
- Signing keys
- Webhook secrets
- Secret vault references

Forbidden:

- Reading secrets
- Displaying secrets
- Logging secrets
- Passing secrets into prompts
- Storing raw secrets in extension config
- Exposing secrets in preview mode

Example protected paths:

```text
.env
.env.*
/secrets/**
/vault/**
/lib/secrets/**
/server/secrets/**
```

---

### 8.5 Core Routing and App Shell

Protected:

- Root layout
- App shell
- Global navigation host
- Route guards
- Protected route wrappers
- Providers
- Error boundaries
- Loading boundaries

Forbidden:

- Replacing root layout
- Removing route guards
- Replacing global providers
- Editing root error boundaries
- Adding unregistered root routes
- Claiming routes like `/login`, `/admin`, `/billing`, `/settings`, `/api/auth`

Example protected paths:

```text
/app/layout.*
/app/providers.*
/app/error.*
/app/not-found.*
/app/(core)/**
/lib/router/**
```

---

### 8.6 Core Dashboard and Workspace Framework

Protected:

- Workspace shell
- Sidebar host
- Top nav host
- Dashboard layout engine
- Workspace switcher
- Core settings pages

Forbidden:

- Editing dashboard shell directly
- Removing existing tabs
- Replacing workspace switcher
- Injecting nav items without registry
- Overriding core dashboard state

Allowed:

- Register sidebar item through `sidebar.nav.item`
- Register page through `workspace.page`
- Register dashboard cards through `dashboard.widget`

---

### 8.7 Agent Runtime and Orchestration

Protected:

- Agent execution engine
- Model provider routing
- Tool invocation policy
- Memory engine
- Agent scheduling
- Run tracing
- Approval gates
- Safety filters

Forbidden:

- Editing runtime directly
- Giving generated agents unrestricted tools
- Disabling run logs
- Altering memory boundaries
- Changing global model routing
- Removing approval requirements

Allowed:

- Register agent preset with scoped tools and memory
- Register workflow that calls approved agent node

---

### 8.8 Tool Execution and External Connectors

Protected:

- Tool registry
- Connector registry
- API credential handling
- Webhook handling
- Network egress policy
- Rate limits
- Tool permission checks

Forbidden:

- Raw arbitrary tool execution
- Unapproved network requests
- Reading connector credentials
- Creating unreviewed webhooks
- Removing rate limits

Allowed:

- Request connector access in manifest
- Use approved connector actions

---

### 8.9 Core Database Schema and Migrations

Protected:

- Users
- Sessions
- Accounts
- Workspaces
- Workspace memberships
- Billing
- Permissions
- Audit logs
- Core settings
- Extension registry tables
- Agent runtime tables, if core

Forbidden:

- Dropping core tables
- Editing core migrations
- Writing directly to core records
- Changing primary keys
- Changing ownership fields
- Modifying audit records
- Modifying registry records directly

Allowed:

- Extension-scoped schemas
- Approved resource APIs for read access

---

### 8.10 Audit Logs and Observability

Protected:

- Audit event creation
- Install/update logs
- Permission grant logs
- Agent run traces
- Workflow run logs
- Error reporting
- Security alerts

Forbidden:

- Disabling logs
- Deleting logs
- Hiding extension actions
- Editing historical traces
- Suppressing security errors

---

### 8.11 Extension Registry, Validator, and Installer

Protected:

- Manifest validation
- Extension install
- Extension update
- Extension disable
- Extension rollback
- Extension compatibility checks
- Risk scoring
- Signature verification, if added

Forbidden:

- Extension edits validator
- Extension approves itself
- Invalid manifest installs
- Rollback removed
- Compatibility checks bypassed

---

### 8.12 Deployment, CI/CD, Build Config, and Package Management

Protected:

- CI/CD config
- Build scripts
- Package manager config
- Lockfiles
- Bundler config
- TypeScript config
- Environment config
- Container config

Forbidden:

- Editing deployment from Forge-generated extension
- Installing dependencies from a generated feature
- Changing build scripts
- Changing env loading
- Modifying Docker/container config

Example protected paths:

```text
package.json
pnpm-lock.yaml
yarn.lock
package-lock.json
next.config.*
vite.config.*
tsconfig.json
Dockerfile
docker-compose.*
.github/**
.vercel/**
netlify.toml
```

---

### 8.13 Security Headers, CSP, CORS, and Middleware

Protected:

- CSP
- CORS
- CSRF
- Security headers
- Request middleware
- Rate limiting

Forbidden:

- Weakening CSP
- Opening CORS broadly
- Removing CSRF protection
- Disabling rate limits
- Allowing arbitrary scripts

---

### 8.14 Core UI Component Library and Design System

Protected:

- Base components
- Design tokens
- Global theme
- Accessibility primitives
- Global styles
- Layout primitives

Forbidden:

- Editing base components directly
- Overriding global CSS
- Injecting unscoped CSS
- Breaking accessibility contracts

Allowed:

- Use approved components from Chaser UI registry
- Use scoped style variables where allowed

---

## 9. Extension Manifest Schema

Every generated feature should have a manifest.

The manifest is the contract between Chaser Forge and Chaser OS.

### 9.1 Required Top-Level Fields

```json
{
  "schemaVersion": "1.0",
  "id": "ugc-campaign-studio",
  "name": "UGC Campaign Studio",
  "description": "A module for planning, scripting, tracking, and delivering UGC campaigns.",
  "version": "0.1.0",
  "status": "draft",
  "category": "creator",
  "createdBy": {
    "type": "chaser-forge",
    "userId": "{userId}",
    "workspaceId": "{workspaceId}"
  },
  "compatibility": {
    "minChaserVersion": "0.1.0"
  },
  "risk": {
    "level": "low",
    "reasons": ["uses mock preview data", "extension-scoped storage only"]
  },
  "permissions": [],
  "extensionPoints": {},
  "schemas": [],
  "agents": [],
  "workflows": [],
  "preview": {},
  "rollback": {}
}
```

### 9.2 Full Example Manifest

```json
{
  "schemaVersion": "1.0",
  "id": "ugc-campaign-studio",
  "name": "UGC Campaign Studio",
  "description": "A workspace module for turning a brand brief into UGC scripts, shot lists, asset tracking, and delivery checklists.",
  "version": "0.1.0",
  "status": "draft",
  "category": "creator",
  "createdBy": {
    "type": "chaser-forge",
    "userId": "{userId}",
    "workspaceId": "{workspaceId}"
  },
  "compatibility": {
    "minChaserVersion": "0.1.0"
  },
  "risk": {
    "level": "low",
    "reasons": [
      "No external connector usage",
      "Only extension-scoped data writes",
      "Agents require approval before client delivery"
    ]
  },
  "permissions": [
    {
      "id": "workspace.read.basic",
      "reason": "Display workspace context inside the module."
    },
    {
      "id": "extension.data.write",
      "reason": "Save campaign briefs, scripts, assets, and delivery checklists."
    },
    {
      "id": "agent.run",
      "reason": "Run campaign, script, and brand QA agents."
    }
  ],
  "extensionPoints": {
    "sidebar.nav.item": [
      {
        "id": "ugc-campaign-studio-nav",
        "label": "UGC Campaign Studio",
        "icon": "video",
        "section": "creator",
        "route": "/workspace/{workspaceId}/extensions/ugc-campaign-studio",
        "orderHint": 40
      }
    ],
    "workspace.page": [
      {
        "id": "ugc-campaign-studio-home",
        "title": "UGC Campaign Studio",
        "route": "/workspace/{workspaceId}/extensions/ugc-campaign-studio",
        "layout": "dashboard",
        "components": [
          "campaign-brief-card",
          "script-generator-card",
          "shot-list-table",
          "asset-tracker-card",
          "delivery-checklist-card"
        ]
      }
    ],
    "dashboard.widget": [
      {
        "id": "active-campaigns-widget",
        "type": "table",
        "title": "Active Campaigns",
        "dataSource": "campaigns"
      },
      {
        "id": "delivery-checklist-widget",
        "type": "checklist",
        "title": "Delivery Checklist",
        "dataSource": "deliveryTasks"
      }
    ]
  },
  "schemas": [
    {
      "id": "campaignBrief",
      "collection": "campaigns",
      "namespace": "extension",
      "fields": [
        { "name": "brandName", "type": "string", "required": true },
        { "name": "product", "type": "string", "required": true },
        { "name": "targetAudience", "type": "string", "required": true },
        { "name": "deliverables", "type": "array", "items": "string", "required": true },
        { "name": "deadline", "type": "date", "required": false },
        { "name": "platform", "type": "enum", "values": ["TikTok", "Instagram", "YouTube Shorts", "Other"] }
      ]
    }
  ],
  "agents": [
    {
      "id": "ugc-script-agent",
      "name": "UGC Script Agent",
      "role": "Creates UGC video scripts from a campaign brief.",
      "instructions": "Generate concise, platform-specific scripts. Ask for missing campaign details before producing final deliverables.",
      "tools": ["content.generate"],
      "memoryScope": "extension",
      "requiresApprovalFor": ["clientSend", "externalPublish"],
      "maxRunMinutes": 5,
      "maxToolCalls": 8
    },
    {
      "id": "brand-qa-agent",
      "name": "Brand QA Agent",
      "role": "Reviews generated content against the brand brief and delivery checklist.",
      "instructions": "Check scripts for brand fit, missing deliverables, unclear hooks, and compliance with the brief.",
      "tools": ["content.review"],
      "memoryScope": "extension",
      "requiresApprovalFor": [],
      "maxRunMinutes": 5,
      "maxToolCalls": 8
    }
  ],
  "workflows": [
    {
      "id": "generate-ugc-campaign",
      "name": "Generate UGC Campaign",
      "trigger": {
        "type": "manual",
        "label": "Generate Campaign"
      },
      "steps": [
        { "id": "collect-brief", "type": "form.input", "schemaRef": "campaignBrief" },
        { "id": "generate-script", "type": "agent.task", "agentId": "ugc-script-agent" },
        { "id": "brand-review", "type": "agent.task", "agentId": "brand-qa-agent" },
        { "id": "human-approval", "type": "approval.gate", "required": true },
        { "id": "save-campaign", "type": "data.write.extension", "collection": "campaigns" }
      ]
    }
  ],
  "preview": {
    "mode": "mock",
    "mockDataPath": "mock-data/campaigns.json",
    "simulatedAgents": true,
    "externalSideEffects": false
  },
  "rollback": {
    "disableStrategy": "registry-disable",
    "preserveExtensionData": true,
    "removeNavigation": true,
    "removeRoutes": true,
    "revokePermissions": true
  }
}
```

---

## 10. Permissions Model

Permissions must be explicit. A generated module should never quietly gain access to data, tools, integrations, files, or external side effects.

### 10.1 Recommended Permission Categories

```text
workspace.read.basic
workspace.read.members
workspace.read.settings
extension.data.read
extension.data.write
core.resource.read.content
core.resource.read.files
core.resource.read.analytics
agent.run
agent.useTool
workflow.run
connector.read
connector.write
notification.draft
notification.send.requiresApproval
file.upload.extensionScoped
file.read.extensionScoped
marketplace.publish
```

### 10.2 High-Risk Permissions

These should require stronger warnings, admin approval, sandbox testing, or additional review:

```text
workspace.read.members
core.resource.read.files
core.resource.read.analytics
connector.write
notification.send
externalPublish
file.read.workspaceWide
scheduledAutomation.create
webhook.create
```

### 10.3 Always Forbidden For Generated Extensions

```text
auth.modify
permission.override
billing.modify
secrets.read
audit.modify
core.schema.modify
extension.validator.modify
deployment.modify
package.install
rawShell.execute
rawDatabase.query.core
network.unrestricted
```

### 10.4 User-Facing Permission UX

Before install, show:

```text
This feature wants to:
- Add a new sidebar tab
- Create extension-scoped records
- Run two generated agents
- Use workspace basic info
- Save campaign briefs/scripts/assets
```

For higher-risk actions:

```text
This feature wants to send external notifications.
Human approval will be required before any external message is sent.
```

---

## 11. UI Safety Architecture

### 11.1 Shell Owns The Layout

The Chaser OS shell owns:

- Root layout
- Providers
- Sidebar
- Top navigation
- Workspace context
- Route guards
- Error boundaries
- Theme
- Permission context

Extensions render inside approved host containers only.

### 11.2 Use An Approved Component Registry

Generated UIs should be declarative and rendered through approved components.

Approved component examples:

```text
Page
Section
Card
Tabs
Table
DataGrid
Chart
Form
Input
Textarea
Select
DatePicker
Button
Modal
Drawer
Checklist
Kanban
Timeline
FileUploadScoped
AgentChatPanel
WorkflowRunner
PermissionNotice
EmptyState
```

### 11.3 Forbidden UI Behaviors

Extensions must not:

- Inject raw scripts
- Use unsandboxed iframes
- Override global CSS
- Read `document.cookie`
- Read browser storage outside approved extension scope
- Replace providers
- Hide permission notices
- Render invisible exfiltration elements
- Impersonate billing/security/auth pages
- Use deceptive fake system warnings

### 11.4 Declarative UI Rendering Model

Recommended:

```text
Manifest → declarative component schema → approved renderer → extension host
```

Example:

```json
{
  "type": "Card",
  "id": "script-generator-card",
  "title": "Script Generator",
  "children": [
    {
      "type": "Form",
      "schemaRef": "campaignBrief",
      "submitWorkflow": "generate-ugc-campaign"
    }
  ]
}
```

This is safer than generating arbitrary React/JS code for MVP.

---

## 12. Agent Safety Architecture

Generated agents should be configuration objects, not unrestricted autonomous programs.

Each agent must declare:

- Name
- Role
- Instructions
- Allowed tools
- Memory scope
- Data scope
- Max runtime
- Max tool calls
- Approval requirements
- Output destination
- Audit settings

### Approval Required Before

- Sending email
- Publishing content
- Posting to social media
- Contacting clients
- Making purchases
- Charging money
- Creating webhooks
- Exporting sensitive data
- Deleting records
- Scheduling recurring automation
- Changing any important setting

### Tool Rules

Agents can only use tools declared in the manifest and approved during installation.

Example:

```json
{
  "agentId": "ugc-script-agent",
  "allowedTools": ["content.generate", "content.review"],
  "forbiddenTools": ["secrets.read", "billing.modify", "rawShell.execute"]
}
```

---

## 13. Workflow Safety Architecture

Workflows should be structured DAG-like configs.

A workflow is allowed to run only if:

- All nodes are approved node types
- Data reads/writes are scoped
- Agent tasks use valid agent presets
- External side effects have approval gates
- Connector calls are permissioned
- Run creates audit events
- Workflow has failure/stop behavior

### Safe Workflow Example

```text
manual trigger
  → collect form input
  → run agent
  → human approval
  → save to extension collection
  → generate report
```

### Unsafe Workflow Example

```text
manual trigger
  → read secrets
  → raw database query
  → external API call
  → delete core data
```

The unsafe version must be blocked.

---

## 14. Data Safety Architecture

### 14.1 Namespaced Storage

All extension data should be namespaced:

```text
ext_{extensionId}_{collectionName}
```

### 14.2 No Direct Core Table Access

Generated extensions must not query core tables directly. They should use approved APIs such as:

```text
workspace.getBasicInfo()
content.listApproved()
files.listExtensionAccessible()
analytics.getScopedMetrics()
agentRuns.listForExtension()
```

### 14.3 Extension Migrations

Extension data migrations must be:

- Namespaced
- Reversible where possible
- Validated before install
- Logged
- Isolated from core schema
- Safe to disable without breaking the shell

### 14.4 Uninstall Data Behavior

Uninstall options:

1. Disable extension and preserve data
2. Disable extension and export data
3. Permanently delete extension data after confirmation

Default: **preserve data**

---

## 15. Preview, Demo, Sandbox, and Live Modes

### 15.1 Draft Preview

Fast UI mockup.

- Fake data
- No writes
- No connectors
- No background jobs
- No live agent execution unless simulated
- Clearly labeled as preview

### 15.2 Simulated Demo

Shows the workflow as if it ran.

- Mock inputs
- Simulated agent outputs
- Sample workflow result
- No production side effects

### 15.3 Sandbox Install

Functional but isolated.

- Extension is registered in sandbox status
- Test data only by default
- External actions disabled unless approved
- Useful for QA

### 15.4 Live Install

Real workspace install.

Requires:

- Valid manifest
- User/admin approval
- Permission confirmation
- Risk disclosure
- Audit log
- Rollback snapshot
- Feature flag enabled

### 15.5 Preview UI Should Show

- Feature name
- Description
- Sidebar location
- New pages
- Widgets/cards
- Agents
- Workflows
- Data collections
- Permissions
- Risk level
- Mock dashboard
- Install/sandbox/export actions

---

## 16. Install, Disable, Uninstall, and Rollback

### 16.1 Install Flow

```text
Validate manifest
  → calculate risk
  → show permission screen
  → user approves
  → create rollback snapshot
  → register extension
  → enable extension routes/nav/widgets
  → write audit event
```

### 16.2 Disable Flow

Disabling should:

- Remove nav item from UI
- Disable routes
- Stop workflows
- Stop scheduled jobs
- Revoke active runtime permissions
- Preserve data by default
- Keep audit logs
- Keep extension record as disabled

### 16.3 Rollback Flow

Rollback should:

- Restore previous extension version or disable the extension
- Remove newly registered slots
- Cancel queued jobs
- Revoke permission grants
- Preserve extension data unless deletion requested
- Write audit event

### 16.4 Emergency Kill Switch

Core admin should be able to:

```text
Disable all extensions
Disable one extension
Disable all generated extensions
Disable marketplace extensions
Disable extension workflows only
Disable extension connector calls only
```

This is protected core.

---

## 17. Extension Validation Pipeline

Validation should happen before preview and before install.

### Stages

1. Manifest schema validation
2. Extension ID validation
3. Route namespace validation
4. Permission declaration validation
5. Permission risk scoring
6. UI component registry validation
7. Workflow node validation
8. Agent tool scope validation
9. Agent memory scope validation
10. Data schema validation
11. Connector permission validation
12. Preview safety validation
13. Rollback plan validation
14. Core path protection validation
15. Test generation/execution
16. Install readiness report

### Policy-As-Code Examples

```ts
if (targetPath.matches(PROTECTED_CORE_PATHS)) {
  deny("Generated extensions cannot modify protected core files.");
}

if (!route.startsWith(`/workspace/{workspaceId}/extensions/${extensionId}`)) {
  deny("Extension routes must be namespaced.");
}

if (permission.id === "secrets.read") {
  deny("Generated extensions cannot request secret access.");
}

if (!APPROVED_WORKFLOW_NODE_TYPES.includes(step.type)) {
  deny(`Workflow node type ${step.type} is not approved.`);
}

if (!APPROVED_UI_COMPONENTS.includes(component.type)) {
  deny(`UI component ${component.type} is not approved.`);
}

if (agent.memoryScope === "global") {
  deny("Generated agents cannot use global memory.");
}

if (workflow.hasExternalSideEffect && !workflow.hasApprovalGateBeforeExternalAction) {
  deny("External side effects require a human approval gate.");
}
```

---

## 18. Protected Core Path Guard

The repository should include a protected path guard for generated extension changes.

Example:

```ts
const protectedCorePaths = [
  "app/layout.*",
  "app/providers.*",
  "app/error.*",
  "app/not-found.*",
  "middleware.*",
  "auth/**",
  "api/auth/**",
  "server/auth/**",
  "lib/auth/**",
  "lib/permissions/**",
  "server/permissions/**",
  "policies/**",
  "billing/**",
  "api/billing/**",
  "lib/entitlements/**",
  "lib/secrets/**",
  "server/secrets/**",
  "vault/**",
  "lib/agent-runtime/**",
  "server/agent-runtime/**",
  "lib/tool-registry/**",
  "server/tool-registry/**",
  "lib/audit/**",
  "server/audit/**",
  "lib/extension-validator/**",
  "server/extension-validator/**",
  "package.json",
  "pnpm-lock.yaml",
  "yarn.lock",
  "package-lock.json",
  "next.config.*",
  "vite.config.*",
  "tsconfig.json",
  "Dockerfile",
  "docker-compose.*",
  ".github/**",
  ".env",
  ".env.*"
];
```

Important nuance:

> Building Chaser Forge itself may require reviewed maintainer changes to core files. That is different from allowing generated extensions to modify core files.

Implementation distinction:

```text
Maintainer-created Forge infrastructure changes: allowed through reviewed PRs.
User-generated Forge extensions: restricted to extension areas and registry slots.
```

---

## 19. Extension Folder Structure

Recommended extension directory:

```text
/extensions/
  ugc-campaign-studio/
    manifest.json
    README.md
    ui/
      pages.json
      components.json
    workflows/
      generate-campaign.json
    agents/
      ugc-script-agent.json
      brand-qa-agent.json
    schemas/
      campaign-brief.schema.json
      campaign.schema.json
    mock-data/
      campaigns.json
      scripts.json
    tests/
      manifest.test.ts
      permissions.test.ts
      preview.test.ts
```

Alternative monorepo structure:

```text
/packages/extensions/ugc-campaign-studio/**
/apps/web/extensions/ugc-campaign-studio/**
```

Rule:

> Generated features can be added, edited, disabled, and removed inside the extension area. They cannot rewrite protected core areas.

---

## 20. Builder Agent Responsibilities

### Product Architect Agent

- Understand user request
- Convert vague idea into feature brief
- Define goal, user, pages, modules, workflows
- Identify missing information

### Extension Architect Agent

- Choose extension points
- Decide config-only vs UI vs workflow vs connector-enabled
- Define extension boundaries
- Define risk level

### UI Designer Agent

- Choose approved components
- Create page/dashboard layout
- Generate mock UI schema
- Create preview data

### Workflow Designer Agent

- Define trigger
- Define nodes
- Add approval gates
- Ensure all node types are approved

### Agent Designer Agent

- Define agent roles
- Define instructions
- Define allowed tools
- Define memory scope
- Define runtime limits

### Manifest Writer Agent

- Produce valid manifest
- Ensure IDs are unique
- Ensure permissions are declared
- Ensure rollback exists

### Security Reviewer Agent

- Review permissions
- Review core boundaries
- Review connector use
- Review agent memory/tools
- Assign risk level
- Flag blocked requests

### QA Agent

- Generate tests
- Test preview rendering
- Test install/disable/rollback
- Test malicious input rejection

### Demo Data Agent

- Create fake records
- Create simulated agent outputs
- Create simulated workflow runs
- Clearly label demo data as mock

### Installer Agent

- Installs only after validation
- Registers extension
- Writes audit event
- Creates rollback snapshot
- Enables feature flag

---

## 21. Chaser Forge User Flow

### Basic Flow

```text
Open Chaser Forge
  → click “Build something new”
  → describe desired feature
  → AI creates feature brief
  → user edits/approves brief
  → AI creates manifest + preview
  → user sees where the tab/page/widget will appear
  → user reviews permissions
  → user installs to sandbox or live workspace
```

### Example Request

```text
Create a tab that helps me plan, script, and track UGC videos for brand campaigns.
```

### Generated Preview

```text
Feature name: UGC Campaign Studio
Location: Sidebar → Creator → UGC Campaign Studio
Pages: Campaign Brief, Script Generator, Shot List, Asset Tracker, Delivery Checklist
Agents: UGC Script Agent, Brand QA Agent
Workflows: Generate Campaign From Brief
Data: Campaigns, Scripts, Assets, Delivery Tasks
Permissions: Workspace basic read, extension data write, agent run
Risk: Low
Preview: Mock data
```

### User Actions

```text
Edit with AI
Preview again
Install to sandbox
Install live
Export manifest
Save as template
Create GitHub PR, optional future feature
```

---

## 22. MVP Recommendation

Do not start with arbitrary code generation.

### Chaser Forge v1 should support

1. Prompt-to-feature brief
2. Feature brief editing
3. Manifest generation
4. Sidebar tab registration
5. Workspace page registration
6. Declarative dashboard cards/widgets
7. Agent preset registration
8. Workflow template registration
9. Extension-scoped schemas
10. Mock preview
11. Permission review
12. Install/disable/uninstall
13. Rollback
14. Export manifest
15. Tests for protected core rejection

### Chaser Forge v1 should not support

- Arbitrary React code generation
- Arbitrary backend code generation
- Raw shell execution
- Raw database queries
- Unrestricted external API calls
- Direct GitHub PR modification as primary path
- Dependency installation by generated feature
- Marketplace publishing before validation is strong
- Production connector writes without approval gates

---

## 23. Implementation Roadmap

### Phase 0 — Repository Inventory

The coding agent should inspect the repo and identify:

- Framework
- Routing system
- App shell
- Sidebar/nav components
- Dashboard/page layout
- Auth system
- Permission system
- Agent/workflow runtime
- Data layer
- Existing config patterns
- Test framework
- Design system

Output: architecture map.

### Phase 1 — Extension Registry

Build:

- Manifest type/schema
- Extension registry storage
- Extension statuses: draft, preview, sandbox, active, disabled, archived
- Workspace extension lookup
- Route/nav registration
- Lifecycle events

### Phase 2 — Validator and Core Guard

Build:

- Manifest validator
- Protected path list
- Route namespace validator
- Permission validator
- UI component validator
- Workflow node validator
- Agent tool/memory validator
- Data schema validator
- Tests for forbidden attempts

### Phase 3 — Host Slots

Build:

- Sidebar extension slot
- Workspace page extension slot
- Dashboard widget slot
- Agent preset registry slot
- Workflow template registry slot
- Optional command palette slot

### Phase 4 — Forge Builder UI

Build:

- Prompt input
- Feature brief/spec panel
- Preview panel
- Permission panel
- Validation report
- Install controls

### Phase 5 — Preview Renderer

Build:

- Declarative UI renderer
- Mock data loader
- Simulated agent output
- Simulated workflow output
- Preview-only labeling

### Phase 6 — Install/Disable/Rollback

Build:

- Install action
- Disable action
- Uninstall action
- Rollback snapshot
- Audit events
- Feature flags
- Permission grants/revocations

### Phase 7 — Agents and Workflows

Integrate:

- Agent preset registry
- Workflow template registry
- Workflow runner for approved nodes
- Agent run constraints
- Approval gates

### Phase 8 — Export/PR Mode

Future:

- Export manifest
- Export template pack
- Generate PR for maintainers
- Generate code only for reviewed trusted extensions

### Phase 9 — Marketplace

Future:

- Template packaging
- Publisher trust levels
- Signed manifests
- Ratings/reviews
- Install counts
- Abuse reports
- Admin approval for risky modules

---

## 24. Acceptance Criteria

### User Experience

- User can open Chaser Forge
- User can describe a new feature
- System creates feature brief
- System shows where the feature appears
- System shows mock preview
- System lists permissions
- User can install feature
- User can disable feature
- User can roll back feature

### Technical

- Every extension has valid manifest
- Routes are namespaced
- Data is namespaced
- Permissions are declared
- Invalid manifests are rejected
- Forbidden workflow nodes are rejected
- Forbidden permissions are rejected
- Agents cannot use undeclared tools
- Preview cannot write production data
- Audit logs are created
- Rollback works

### Security

The system must reject generated features that attempt to:

- Modify auth
- Modify permissions
- Modify billing
- Read secrets
- Disable audit logs
- Edit deployment config
- Add unrestricted network access
- Execute shell commands
- Run raw core database queries
- Override root routes
- Install dependencies
- Hide permission requests
- Exfiltrate data through UI

---

## 25. Test Plan

### Positive Tests

Valid extension can:

- Add sidebar tab
- Add workspace page
- Add dashboard widget
- Define extension-scoped schema
- Define agent preset
- Define workflow template
- Render mock preview
- Install after approval
- Disable cleanly
- Roll back cleanly

### Negative Tests

Validator rejects:

```text
Route: /login
Route: /admin
Route: /settings/billing
Permission: secrets.read
Permission: auth.modify
Permission: billing.modify
Workflow node: shell.execute
Workflow node: code.eval
Workflow node: rawDatabase.query.core
Agent memory scope: global
Agent tool: rawShell.execute
UI component: RawScript
UI behavior: unsandboxed iframe
Data collection: users
Data collection: sessions
Data collection: billing
Data collection: audit_logs
Path edit: package.json
Path edit: .env
Path edit: lib/auth/**
Path edit: lib/permissions/**
Path edit: server/agent-runtime/**
```

### Preview Safety Tests

Preview must not:

- Persist production records
- Send notifications
- Call external APIs
- Start scheduled jobs
- Activate extension
- Access secrets

### Rollback Tests

Rollback must:

- Remove nav item
- Disable routes
- Stop workflows
- Preserve data by default
- Revoke permissions
- Log rollback
- Avoid touching unrelated extensions

---

## 26. Suggested Type Interfaces

Adapt to actual repo language/framework.

```ts
type ExtensionStatus =
  | "draft"
  | "preview"
  | "sandbox"
  | "active"
  | "disabled"
  | "archived";

type RiskLevel = "low" | "medium" | "high" | "blocked";

type ExtensionManifest = {
  schemaVersion: string;
  id: string;
  name: string;
  description: string;
  version: string;
  status: ExtensionStatus;
  category?: string;
  createdBy: {
    type: "chaser-forge" | "marketplace" | "maintainer";
    userId?: string;
    workspaceId?: string;
  };
  compatibility: {
    minChaserVersion: string;
    maxChaserVersion?: string;
  };
  risk: {
    level: RiskLevel;
    reasons: string[];
  };
  permissions: ExtensionPermission[];
  extensionPoints: Record<string, unknown[]>;
  schemas?: ExtensionSchema[];
  agents?: AgentPreset[];
  workflows?: WorkflowTemplate[];
  preview?: ExtensionPreviewConfig;
  rollback: ExtensionRollbackConfig;
};

type ExtensionPermission = {
  id: string;
  reason: string;
  required?: boolean;
};

type ExtensionValidationResult = {
  valid: boolean;
  riskLevel: RiskLevel;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  requiredApprovals: string[];
};

type ValidationIssue = {
  code: string;
  message: string;
  path?: string;
  severity: "info" | "warning" | "error" | "blocked";
};
```

---

## 27. Suggested Registry API

```ts
interface ExtensionRegistry {
  validateManifest(manifest: ExtensionManifest): ExtensionValidationResult;

  createDraft(
    workspaceId: string,
    manifest: ExtensionManifest
  ): Promise<ExtensionRecord>;

  renderPreview(
    workspaceId: string,
    extensionId: string
  ): Promise<PreviewRenderResult>;

  install(
    workspaceId: string,
    extensionId: string,
    approvedByUserId: string
  ): Promise<InstallResult>;

  disable(
    workspaceId: string,
    extensionId: string,
    disabledByUserId: string
  ): Promise<void>;

  rollback(
    workspaceId: string,
    extensionId: string,
    version: string,
    requestedByUserId: string
  ): Promise<void>;

  listWorkspaceExtensions(
    workspaceId: string
  ): Promise<ExtensionRecord[]>;
}
```

---

## 28. Example Module: Trading Journal Lab

User request:

```text
Build a tab for tracking my crypto leverage trades, including entries, exits, PnL, screenshots, mistakes, and AI review.
```

Generated feature:

```text
Name: Trading Journal Lab
Location: Sidebar → Finance → Trading Journal Lab
Pages: Trade Log, PnL Dashboard, Mistake Review, Strategy Notes
Agents: Trade Review Agent, Risk Coach Agent
Workflows: Log Trade, Review Losing Trade, Weekly Performance Summary
Data: Trades, Screenshots, Notes, Mistake Tags
Risk: Medium if external exchange connector is requested; Low if manual journal only
```

Safe MVP version:

- Manual trade logging only
- No exchange API connector
- No trade execution
- No financial advice automation
- Extension-scoped storage
- AI review framed as journal analysis, not execution advice

Blocked unsafe version:

- Agent places trades automatically
- Agent accesses exchange keys directly
- Agent bypasses approvals
- Agent modifies risk settings without confirmation

---

## 29. Example Module: Shopify Growth Lab

User request:

```text
Create a Shopify growth lab that tracks experiments, product ideas, content ideas, and weekly revenue notes.
```

Generated feature:

```text
Name: Shopify Growth Lab
Location: Sidebar → E-Commerce → Shopify Growth Lab
Pages: Experiment Tracker, Product Ideas, Content Ideas, Weekly Review
Agents: Product Analyst, Listing Copy Agent, Growth Strategist
Workflows: Create Growth Experiment, Review Results, Generate Weekly Plan
Data: Experiments, Ideas, Notes, Metrics
Risk: Low without Shopify connector; Medium with read connector; High with write connector
```

Safe MVP version:

- Manual metrics input
- Optional read-only Shopify connector later
- No product edits without explicit approval

---

## 30. Example Module: Client Onboarding Studio

User request:

```text
Build a client onboarding portal for my agency.
```

Generated feature:

```text
Name: Client Onboarding Studio
Location: Sidebar → Agency → Client Onboarding
Pages: Intake Form, Client Checklist, Asset Requests, Kickoff Notes
Agents: Onboarding Assistant, Brief Summarizer
Workflows: New Client Intake, Generate Kickoff Plan, Request Missing Assets
Data: Clients, Briefs, Tasks, Assets
Risk: Medium if external client emails are sent
```

Required approval gates:

- Before sending emails
- Before creating external shared links
- Before exporting client data

---

## 31. Marketplace Direction

Once the extension system is stable, Chaser OS can add a marketplace.

Possible categories:

- Creator Engine templates
- E-commerce templates
- Trading journal templates
- Agency ops templates
- Research templates
- Cybersecurity lab templates
- Personal productivity templates
- Startup operations templates

Marketplace safety requirements:

- Manifest validation
- Permission disclosure
- Publisher identity
- Version history
- Ratings/reviews
- Abuse reporting
- Template scanning
- Optional signed manifests
- Admin approval for high-risk modules

---

## 32. Repository Handoff Instructions

When this document is given to Codex, Claude Code, or another repository-aware coding agent, the first task should be to inspect the Chaser OS repository and produce an implementation plan for Chaser Forge v1.

The implementation plan must identify:

1. Existing navigation/sidebar structure
2. Existing routing structure
3. Existing dashboard/page layout system
4. Existing auth and permission systems
5. Existing agent/workflow systems
6. Existing data layer
7. Existing test framework
8. Where to place the extension registry
9. Where to place the manifest schema
10. Where to place the validator
11. Which files are protected core
12. The smallest safe MVP implementation path

The coding agent must not begin with arbitrary code generation.

The first implementation should focus on:

```text
- docs/chaser-forge-approved-extension-points.md
- extension manifest schema/type
- extension registry interface
- extension validator
- protected core guard
- sidebar extension slot
- workspace page extension slot
- mock preview renderer skeleton
- tests for valid/invalid manifests
```

---

## 33. Final Rule

> **Chaser Forge builds modules. It does not mutate the core.**

Generated features must live behind:

- Manifests
- Approved extension points
- Permission boundaries
- Namespaced routes
- Namespaced data
- Approved UI components
- Approved workflow nodes
- Agent tool scopes
- Preview sandboxing
- Install validation
- Audit logging
- Rollback
- Kill switches

That is how Chaser OS becomes self-extending without becoming unstable.
