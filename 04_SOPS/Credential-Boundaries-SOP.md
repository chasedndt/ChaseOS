---
type: sop
title: Credential Boundaries SOP
version: 1.0
created: 2026-03-20
scope: framework-level
---

# Credential Boundaries SOP

> Operational policy for credential, secret, and token handling across all ChaseOS agent surfaces.
> Hard rule: credentials and secrets must never appear in vault content in plain text.
> This SOP governs where credentials live, what agents may and may not do with them, and what actions always require explicit user approval.
> See `[[06_AGENTS/Agent-Security-Model|Agent-Security-Model]]` for the broader security architecture.

---

## 1. What This SOP Covers

**Credential types in scope:**

| Credential Type | Examples |
|----------------|---------|
| Model / provider API keys | Anthropic API key, OpenAI API key, Mistral/Ollama credentials |
| MCP server credentials | MCP server tokens, workspace server access keys |
| Exchange API keys | Binance API key/secret, Bybit key/secret, Coinbase key |
| Webhook secrets | Discord webhook URLs, Telegram bot tokens, n8n webhook secrets |
| Data provider keys | TradingView, Coinglass, Glassnode, Bloomberg API credentials |
| Brokerage or account tokens | Interactive Brokers, other brokerage session tokens |
| Local environment secrets | `.env` file values, shell environment variables |
| Platform credentials | Whop API keys, Discord bot tokens, GitHub personal access tokens |
| Infrastructure credentials | Server SSH keys, database passwords, cloud provider keys |

---

## 2. The Hard Rules

### Rule 1: No credentials in vault content
Credentials, API keys, tokens, and secrets must never appear in plain text in any vault file. This includes:
- Markdown notes in `02_KNOWLEDGE/`
- Project-OS files in `01_PROJECTS/`
- Build logs in `07_LOGS/`
- SOPs or templates
- Input files in `03_INPUTS/`
- Archive notes in `99_ARCHIVE/`
- Agent registry entries
- Any file tracked by the vault

### Rule 2: Reference by name and location, never by value
Vault content may acknowledge that a credential exists and where it is stored. It may not contain the credential value.

**Permitted:**
- "API key stored in gitignored root `.env`"
- "ChaseOS setup metadata references `OPENAI_API_KEY`"
- "Exchange credentials managed via system keychain"
- "MCP server token in environment variable `MCP_TOKEN`"
- "See `.env.example` for required credential names"

**Not permitted:**
- `ANTHROPIC_API_KEY=<actual-secret-value>`
- `BINANCE_SECRET=<actual-secret-value>`
- Any actual key, token, or secret value

### Rule 3: Agents may not reveal credential values
Even if a credential exists in the agent's execution environment (e.g., environment variable available to Claude Code), the agent must not output, log, repeat, or transmit the value. The agent may acknowledge a credential is present and available.

### Rule 4: Credential-bearing operations always require approval
Any action that reads, uses, or transmits a credential requires explicit user approval in the current session. This includes:
- Making an API call that uses a stored credential
- Configuring a tool or workflow with credential access
- Writing a config file that references credentials by value

---

## 3. Where Credentials Live

### Approved storage locations

| Location | Use case | Notes |
|----------|---------|-------|
| `.env` file at ChaseOS root (gitignored) | Easy local ChaseOS install credentials | Inside local ChaseOS, outside Git-tracked truth; must be in `.gitignore`; never committed |
| `.chaseos/credentials/` (gitignored) | Local credential files such as Google service-account JSON | Store file paths in `.env`; never commit contents |
| System keychain / OS credential store | Provider API keys, high-value credentials | Recommended for all long-lived keys |
| Environment variables | Runtime-available credentials for agent harnesses | Injected at runtime; not stored in vault |
| Secrets manager (1Password, Bitwarden, etc.) | All credentials centrally managed | Preferred for keys used across multiple surfaces |
| Hardware key / 2FA device | Exchange keys, high-value accounts | Required for exchange trading keys |

### Not approved
- Plain-text vault files (any folder)
- Shared Obsidian vaults or synced vaults without encryption
- Chat histories with model providers (credentials in prompt context may be logged)
- Build logs or session notes (even as examples or test values)
- `.env.local` or similar files if not gitignored
- Agent memory systems (e.g., `~/.claude/`) — treat as potentially logged

---

## 4. What Agents May and May Not Do

### Permitted
- Acknowledge that a credential is required for an action and where it should be stored
- Confirm a credential is present in the execution environment (exists/not present) without revealing its value
- Reference credentials by variable name (`ANTHROPIC_API_KEY`) in code or config
- Instruct the user on how to set up credential storage correctly
- Execute an API call using an environment-injected credential with user approval

### Not permitted
- Output, log, repeat, or display a credential value in any format (masked or otherwise)
- Store credentials in vault files
- Accept credentials as direct input in a prompt (user should provide via env or keychain, not paste in chat)
- Include credentials in any writeback content (build logs, OS files, knowledge notes)
- Transmit credentials to external services without explicit session approval

---

## 5. MCP Server and Tool Connector Credentials

MCP servers and tool connectors introduce additional credential risk.

### Rules
- MCP server credentials must be stored in environment variables or a secrets manager — not in the MCP server config file if that file is tracked in the vault
- The scope of MCP server access must be defined before the credential is issued — least privilege applies
- MCP server tokens must be rotated if the server's access scope changes
- Any MCP server or connector registered in `Agent-Registry.md` must document where its credentials are stored and what access they grant — without including the credential values
- Compromised MCP credentials must be rotated immediately and the incident logged

---

## 6. Exchange and Trading Credentials

Exchange API keys are high-risk due to the potential for financial loss.

### Required controls
- Exchange API keys must be stored in a hardware key manager or dedicated secrets vault
- Keys must be created with **minimum required permissions** (read-only for data, write-only for specific order types if needed — never full account control unless required)
- IP whitelisting must be enabled where the exchange supports it
- Separate keys must be created per use case (market data key ≠ trading key)
- Keys must be rotated on a regular cadence and immediately on suspected compromise
- API keys must never appear in code, config files tracked in the vault, or build logs

### Logging trading activity
Build logs and trade journal entries may reference that an exchange API was used. They must not include the key used. Example:
- Permitted: "Executed via Binance API (key: Binance-TradeSync-Prod)"
- Not permitted: "Executed via Binance API key: xyz123..."

---

## 7. Webhook and Automation Credentials

Webhook URLs, bot tokens, and automation secrets (Discord, Telegram, n8n) are high-value targets because they enable external write access.

### Rules
- Webhook URLs and bot tokens must be stored as environment variables or in a secrets manager
- Webhook URLs must be treated as secrets — anyone with the URL can trigger the webhook
- Rotate webhook secrets if they appear in any logged output or if the scope of the webhook changes
- n8n and workflow runtime credentials must be scoped to the minimum required for the workflow
- Telegram bot tokens and Discord bot tokens must be stored separately from vault content

---

## 8. When a Credential Is Compromised or Suspected Compromised

1. **Rotate immediately** — revoke the old credential; issue a new one
2. **Audit access logs** — check provider logs for unauthorized use
3. **Update storage** — issue the new credential to the correct storage location (keychain, env, secrets manager)
4. **Log the incident** — create an entry in `07_LOGS/Agent-Activity/` noting: what was compromised, when discovered, what was rotated, what was reviewed
5. **Review vault content** — confirm the compromised credential does not appear anywhere in the vault (search for partial key fragments if possible)
6. **Review connected surfaces** — check which agents, MCP servers, and workflow runtimes used the compromised credential; assess potential impact

---

## 9. Actions That Always Require Approval

The following actions are never autonomous and always require explicit user approval:

| Action | Why |
|--------|-----|
| Making an API call using a stored credential | Real-world side effect; scope must be confirmed |
| Configuring a new tool or workflow with credential access | Expands attack surface |
| Rotating a credential | Impacts all dependent systems |
| Adding a new credential reference to any config or registry | Adds new risk surface |
| Exposing a MCP server with credential-bearing access | Potential data exfiltration risk |
| Performing an exchange order or financial transaction | Irreversible financial consequence |
| Transmitting any content to an external service | Data exfiltration risk |

---

## 10. Reference

| Document | Purpose |
|----------|---------|
| `[[06_AGENTS/Agent-Security-Model|Agent-Security-Model]]` | Threat model; credential exfiltration routes |
| `[[Untrusted-Input-Handling-SOP]]` | Handling ingested content that may contain credential-like values |
| `[[06_AGENTS/Permission-Matrix|Permission-Matrix]]` | What actions require user approval |
| `[[06_AGENTS/Agent-Registry|Agent-Registry]]` | Where MCP servers and connectors are registered with their access scope |
| `[[06_AGENTS/Backends-Supported|Backends-Supported]]` | Surface-specific access model |
| `[[Credential-Setup-SOP]]` | Local `.env` and setup command workflow |

---

*Graph links: [[06_AGENTS/Vault-Map|Vault-Map]] · [[06_AGENTS/Agent-Security-Model|Agent-Security-Model]] · [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] · [[06_AGENTS/Permission-Matrix|Permission-Matrix]] · [[Untrusted-Input-Handling-SOP]] · [[06_AGENTS/Agent-Registry|Agent-Registry]] · [[06_AGENTS/Backends-Supported|Backends-Supported]] · [[ROADMAP]]*

*Credential-Boundaries-SOP.md — Version 1.0 | Created: 2026-03-20 | Phase 4 — Agent Control + Security Plane*
