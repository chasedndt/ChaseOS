---
type: tool-map
updated: 2026-03-18
---

# 🗺️ Tool Map — ChaseOS Stack

> Every tool, platform, and service in the operating stack.
> Know your arsenal. Know what each thing does.

---

## 🧠 AI / Intelligence Layer

ChaseOS is designed to be agent-agnostic. The framework conventions (writeback targets, output types, template usage) apply regardless of which agent backend is in use. See `06_AGENTS/Agent-Output-Conventions.md` for the full multi-backend output contract.

| Tool | Category | Use Case | Status |
|------|----------|----------|--------|
| Claude Code | AI coding agent | Primary dev partner, vault management | ✅ Active |
| Claude.ai | AI chat | Research, ideation, writing | ✅ Active |
| NotebookLM | Source synthesis | Research management, PDF analysis | ✅ Active |
| Perplexity AI | Live research | Digest generation, market intel | ✅ Active |
| Grok (xAI) | Market intel | Crypto/X-based research | ✅ Active |
| OpenRouter | Model aggregation | Multi-model workflows | ⬜ Planned |
| Ollama | Local models | Private/offline AI inference | ⬜ Planned |

---

## 🏗️ Development & Build

| Tool | Category | Use Case | Status |
|------|----------|----------|--------|
| VS Code | IDE | Primary code editor | ✅ Active |
| Git / GitHub | Version control | All project repos | ✅ Active |
| Python | Language | AI agents, data scripts, automation | ✅ Active |
| JavaScript / Node | Language | Frontend, APIs, bots | ✅ Active |
| Pine Script | Language | TradingView indicator dev | ✅ Active |
| Docker | Containerisation | Deployment, reproducible environments | ⬜ Learning |
| Raspberry Pi | Edge compute | Hardware experiments | 🟡 Partial |

---

## 📊 Trading & Markets

| Tool | Category | Use Case | Status |
|------|----------|----------|--------|
| TradingView | Charting | Chart analysis, indicator deployment | ✅ Active |
| Drift Protocol | Exchange | Primary leveraged perps (Solana) | ✅ Active |
| Hyperliquid | Exchange | Secondary perpetuals | ✅ Active |
| Unikill V2.x | Indicator | Signal generation | 🟡 In dev |
| Bias Flip | Indicator | Trend/bias detection | 🟡 In dev |
| Market Structure Analyzer | Indicator | Structure mapping | 🟡 In dev |

---

## 🌐 Community & Distribution

| Tool | Category | Use Case | Status |
|------|----------|----------|--------|
| Discord | Community | StrikeZone signals and community | ✅ Active |
| Whop | Monetisation | StrikeZone subscription management | ✅ Active |
| LinkedIn | Professional | ChaseInTech brand, career ops | ✅ Active |
| X / Twitter | Social | ChaserCrypto brand, market commentary | ✅ Active |
| YouTube | Video | Build-in-public + trading content | 🟡 Planned |
| Twitch | Streaming | Live build sessions | ⬜ Planned |
| Telegram | Messaging | Bot alerts, trading group | 🟡 Partial |

---

## ⚙️ Automation & Infrastructure

| Tool | Category | Use Case | Status |
|------|----------|----------|--------|
| n8n | Automation | Workflow automation, agent flows | ⬜ Planned |
| VPS (Linux) | Infrastructure | Hosting agents, bots, services | ⬜ Planned |
| Obsidian | PKM / Vault | Personal operating system | ✅ Active |
| Notion | _Legacy_ | _Replaced by Obsidian_ | ❌ Deprecated |

---

## 📚 Learning & Research

| Tool | Category | Use Case | Status |
|------|----------|----------|--------|
| PortSwigger Academy | Cybersecurity labs | Bug bounty / pen test training | ✅ Active |
| Kali Linux | Security OS | Attacker environment | 🟡 Setup phase |
| Nvidia Deep Learning courses | AI education | ML/AI fundamentals | 🟡 In progress |
| University Moodle | Academic | Greenwich CS (AI) degree | ✅ Active |
| Anki | Spaced repetition | Mandarin vocabulary + CS concepts | 🟡 Planned |
| Readwise | Reading management | Web clip processing | 🟡 Planned |

---

## 🔗 Key Integrations (Planned)
```
TradingView → Webhook → Discord (StrikeZone signals)
Drift Protocol → TradeSync AI Agent → Discord alerts
Perplexity/Grok digests → Vault → Content Engine
n8n → VPS → multiple agent pipelines
```

---

*Updated: 2026-03-18 | See also: [[Agent-Registry]] · [[ChaseOS/ChaseOS-OS]]*


*Graph links: [[Vault-Map]]*
