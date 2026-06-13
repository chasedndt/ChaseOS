---
type: template
title: Morning Thesis Output
agent-primary: true
usage: Used by the agent/system to record pre-market thesis. File in 07_LOGS/Morning-Thesis/.
updated: 2026-03-19
---

# Morning Thesis — {{DATE}}

> **Agent-first template.** Produced by the agent following `04_SOPS/Morning-Thesis-Workflow.md`.
> Manual fill is fallback only.
> File at: `07_LOGS/Morning-Thesis/YYYY-MM-DD-thesis.md`

---

## Step 1 — Overnight Price Action

**BTC:** {{direction — up / down / ranging}} | {{price}} | {{overnight high / low}}
**ETH:** {{direction}} | {{price}} | {{ETH/BTC ratio note}}
**SOL:** {{direction}} | {{price}}
**BTC.D:** {{rising / falling / stable}} — {{interpretation: risk-off / rotation / neutral}}
**Notable altcoin moves:** {{any significant sector or single-asset moves}}

**Overnight narrative summary (1–2 lines):**
{{Brief description of what happened overnight}}

---

## Step 2 — Derivatives Data

| Metric | Reading | Interpretation |
|--------|---------|----------------|
| BTC Funding rate | {{%}} | {{Positive = longs exposed / Negative = shorts exposed / Neutral}} |
| ETH Funding rate | {{%}} | |
| Key alt funding | {{asset: %}} | |
| Open Interest trend | {{Rising / Falling / Stable}} | {{Conviction direction}} |
| CVD direction | {{Positive / Negative / Diverging}} | {{Net buying / selling pressure}} |
| Nearest liq cluster above | {{price}} | |
| Nearest liq cluster below | {{price}} | |
| Long/short ratio | {{ratio}} | {{Retail lean: Long-heavy / Short-heavy / Balanced}} |

**Derivatives summary:**
{{1–2 sentences on the derivative picture}}

---

## Step 3 — Macro Context

**Scheduled events today:**
| Time (ET) | Event | Expected | Prior |
|-----------|-------|----------|-------|
| {{time}} | {{event}} | {{est}} | {{prev}} |

**Pre-market equity futures:** {{ES / NQ direction}}
**DXY:** {{direction}} — {{risk-on / risk-off lean}}
**US10Y:** {{direction}} — {{risk-on / risk-off lean}}
**VIX:** {{level}} — {{calm / elevated / fear}}

**Macro lean:** {{Risk-on / Risk-off / Neutral / Wait for event}}

---

## Step 4 — Narrative / On-Chain Context

**Active crypto narratives:** {{any sectors or catalysts in play}}
**On-chain notable:** {{any significant exchange flows, whale moves, protocol events}}
**Solana ecosystem:** {{any relevant Solana-specific context}}
**Any TradFi perp setups triggered?** {{Yes — [asset] / No}}

---

## Step 5 — Session Bias

**Primary bias:** {{Bullish / Bearish / Neutral / Wait}}
**Bias reasoning:** {{1–2 sentences: what drove this bias}}
**Invalidation condition:** {{What price or event makes this bias wrong}}

---

## Step 6 — Key Levels

**Primary asset: {{BTC/ETH/SOL/other}}**

| Level | Price | Type |
|-------|-------|------|
| Resistance 1 | {{price}} | {{Structure / Liquidity / OB}} |
| Resistance 2 | {{price}} | |
| Support 1 | {{price}} | |
| Support 2 | {{price}} | |
| Session invalidation | {{price}} | {{Above/below = thesis wrong}} |

---

## Step 7 — Session Thesis

> **{{Bullish / Bearish / Neutral}} thesis for {{DATE}}:**
> "Today I am watching for {{setup type}} on {{asset}} from {{level}}, with {{directional}} bias based on {{key confluences}}. Session thesis is invalid if {{price/condition}}."

---

## Trade Journal Connection

Any trades taken today should reference this thesis entry.
Trade journal: `07_LOGS/Trade-Journal/{{DATE}}-{{ASSET}}-{{DIRECTION}}.md`

---

*Graph links: [[06_AGENTS/Vault-Map|Vault-Map]] · [[Morning-Thesis-Workflow]] · [[Morning-Thesis-Index]] · [[TradingSystems-OS]]*

*Thesis output: {{DATE}} | Produced via `04_SOPS/Morning-Thesis-Workflow.md` | Template: Morning-Thesis-Output-Template.md*
