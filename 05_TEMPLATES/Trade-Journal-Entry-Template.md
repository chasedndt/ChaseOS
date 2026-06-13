---
type: template
title: Trade Journal Entry
agent-primary: true
usage: Copy this template for each trade entry. Agent creates/populates; user fills gaps as fallback.
updated: 2026-03-19
---

# Trade Journal Entry — {{DATE}}

> **Agent-first template.** This entry should be created or populated by the agent/system.
> Manual fill by the user is fallback when agent assist is not available.
> Entries live in `07_LOGS/Trade-Journal/`.

---

## Session Thesis (from Morning Prep)

**Date:** {{DATE}}
**Pre-session bias:** {{Bullish / Bearish / Neutral}}
**Bias reasoning:** {{1–2 sentences on what the derivative/macro/structural data showed}}
**Invalidation condition:** {{What price or event would make the session thesis wrong}}
**Macro context:** {{Any scheduled events today: FOMC / CPI / NFP / earnings / other}}

---

## Trade Entry

**Asset:** {{BTC / ETH / SOL / altcoin / index / equity / commodity / forex}}
**Venue:** {{Drift / Hyperliquid}}
**Direction:** {{Long / Short}}
**Entry time (ET):** {{HH:MM}}
**Entry price:** {{price}}
**Position size:** {{$ amount or % of account}}
**Leverage:** {{Xleverage}}
**Stop Loss:** {{price}}
**Take Profit 1:** {{price}} — {{% of position}}
**Take Profit 2:** {{price}} — {{% of position}} *(optional)*
**Max loss on trade ($ or %):** {{amount}}
**RR ratio at entry:** {{X:1}}

---

## Setup Context

**Why this trade:**
{{Describe the setup. What structure, level, confluence, or catalyst triggered the entry. Reference the session thesis.}}

**Key confluences at entry:**
- [ ] HTF structure alignment
- [ ] Clear level (support / resistance / order block / liquidity pool)
- [ ] Funding rate aligned
- [ ] OI signal aligned
- [ ] CVD signal aligned
- [ ] Liquidation cluster nearby
- [ ] Macro/narrative context aligned
- [ ] Within primary session window

**What would invalidate this trade mid-position:**
{{Condition or price level that signals the thesis is wrong and position should be closed}}

---

## Trade Outcome

**Exit time (ET):** {{HH:MM}}
**Exit price:** {{price}}
**Exit type:** {{TP hit / SL hit / manual close / partial close}}
**Result:** {{Win / Loss / Breakeven}}
**P&L ($ and %):** {{amount}}
**Notes on exit:** {{Did it go to plan? Was there a deviation from the TP/SL plan?}}

---

## Scoring

*Scored using `02_KNOWLEDGE/Trading-Systems/Trade-Scoring-Framework.md`. Each dimension 1–5.*

| Dimension | Score (1–5) | Notes |
|-----------|-------------|-------|
| D1 — Setup Quality | | |
| D2 — Confluence | | |
| D3 — Execution Quality | | |
| D4 — Risk Quality | | |
| D5 — Process Adherence | | |
| **Total** | **/25** | |
| **Grade** | **A / B / C / D / F** | |

---

## Review Notes

**What worked:**
{{What in the setup, entry, or management went well}}

**What didn't work:**
{{What missed, what was off, what would you do differently}}

**Pattern to watch:**
{{Is this a recurring error or success pattern? Flag for weekly review.}}

---

*Graph links: [[06_AGENTS/Vault-Map|Vault-Map]] ·  · [[Trade-Journal-Index]] · [[Weekly-Trading-Review-Workflow]]*

*Entry created: {{DATE}} | Template: Trade-Journal-Entry-Template.md*
*This entry should be filed at: `07_LOGS/Trade-Journal/{{YYYY-MM-DD}}-{{ASSET}}-{{DIRECTION}}.md`*

## Related
- [[Trade-Scoring-Framework]]
