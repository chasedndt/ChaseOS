---
type: strikezone-sbp-draft
status: draft / documentation-schema-pass
created: 2026-05-26
runtime: hermes-optimus
project: StrikeZone SBP
---

# StrikeZone SBP Architecture

> StrikeZone SBP is a ChaseOS/Hermes-supported crypto market-intelligence and daily/session thesis pipeline for the StrikeZone Crypto Trading Server. It is not an autonomous trading bot, not an order-execution system, and not a Discord auto-poster without approval.

## Authority Summary

Allowed early:
- screenshot capture and provenance logging;
- scheduled digest capture;
- screenshot-to-markdown evidence cards;
- evidence packet creation;
- missing-data and contradiction detection;
- thesis draft, risk challenge, Discord draft, and ChaseOS operator brief.

Draft-only:
- bullish/bearish/neutral bias;
- suggested TradingView levels;
- entry trigger, stop, take-profit, trailing-stop logic;
- confidence score;
- alt watchlist suggestions;
- public-post recommendation.

Forbidden:
- open/close trades, move stops, move take-profits, change leverage, change account settings;
- read/store credentials or scrape private DMs without separate scope;
- mutate TradingView drawings silently;
- post live trade calls without operator approval;
- treat chatbot/social output as truth without evidence.

## System Purpose

SBP captures the user's real manual market-prep workflow and turns it into a governed ChaseOS pipeline:

```text
scheduled digests + analyst/social context + screeners + TradingView screenshots + derivatives/orderflow + macro/ETF/premium calendar
→ screenshot-to-markdown evidence cards
→ evidence packet
→ ChaseOS internal synthesis
→ thesis draft
→ risk challenge / workflow audit
→ private operator brief + optional Discord draft + private trade-plan draft
→ human approval/post/trade if appropriate
```

## Workflow Phases

### A. Scheduled Digest / Market Context

Inputs: Grok scheduled tasks, Perplexity scheduled searches, ChatGPT scheduled searches.

Purpose: first read of BTC/ETH/SOL structure, macro tone, session trap risk, rotation, and `NEEDS SNAPSHOT` gaps. Scheduled digest output is input only, never final truth.

Capture targets:
- markdown export/screenshot of each digest;
- source name, prompt title, generated timestamp, session, model/provider if visible;
- missing snapshot flags.

### B. Analyst / Social / Public-Idea Discovery

Inputs: YouTube subscription feed, X timeline, TrackFi, TradingView Crypto Ideas, ChaserCrypto/ChaseInTech account context.

Purpose: consensus/crowding, strong-trader levels, narratives, sentiment shifts. This is context/consensus, not primary evidence.

### C. Screener / Breadth / Trend Layer

Inputs: Altfins, MarketMasters.ai, CoinAnk AI market analysis generator once verified, TradingView Crypto Ideas.

Strict alt rule: include alts only when structure and flow confirmation align. If none qualify, output “No high-conviction alt setups.”

### D. TradingView Structure Layer

Core assets: `BINANCE:BTCUSDT`, `BINANCE:ETHUSDT`, `BINANCE:SOLUSDT`.

Minimum timeframes: `D`, `4H`, `1H`, `15M`. Optional expansion: `5M`, `30M`, `2H`, `8H`.

The TradingView layer has highest evidence weight. Early automation may capture; it must not silently edit drawings.

Current tested browser pattern:

```text
Persistent StrikeZone Chromium profile → user logged into TradingView → Hermes attaches via CDP → forces symbol/timeframe → collapses sidebars/toasts → reset/fit chart view → saves screenshots to 07_LOGS/Operator-Screenshots/StrikeZone/
```

### E. Derivatives / Orderflow / Liquidity Layer

Inputs: CoinAnk Pro Chart, liquidation heatmap, funding, long/short realtime, Hyperliquid data, orderbook depth, OI screener.

Purpose: confirmation/contradiction. It must answer whether OI, CVD, funding, orderbook depth, liquidation magnets, ETF flows, Coinbase premium, and macro calendar agree with or attack the chart thesis.

### F. Synthesis Layer

Future default: ChaseOS internal synthesis engine. NotebookLM is optional/legacy/fallback.

The synthesis layer consumes evidence cards and prompt outputs; it does not invent truth.

### G. Final Action / Private Trade Plan Layer

Surfaces: Hyperliquid, Drift/BTC-PERP, Live Trade Chat, LTF Crypto Trading Assistant, Claude LTF analysis.

SBP may draft private plans but never executes. A valid private trade-plan draft must include trigger, invalidation, stop band, targets, no-trade rules, and manual execution note.

## Evidence Hierarchy

| Tier | Evidence | Weight |
|---|---|---|
| 1 | User TradingView structure, marked levels, HTF/LTF screenshots | Highest |
| 2 | CoinAnk derivatives/orderflow/liquidity screenshots/cards | Very high |
| 3 | ETF flows, Coinbase premium, economic calendar, macro cross-assets | High when relevant |
| 4 | Altfins / MarketMasters / screeners | Medium |
| 5 | YouTube / X / TrackFi / TradingView Ideas | Context / consensus |
| 6 | Chatbot outputs / scheduled search outputs / NotebookLM | Synthesis aid only |

Rule: chatbots do not create truth; they synthesize evidence.

## Confidence Model

- HTF structure clarity: 20
- LTF trigger clarity: 15
- Key levels + invalidation clarity: 15
- Derivatives/orderflow confirmation: 25
- Social/analyst/screener consensus: 10
- Macro/event risk clarity: 5
- Risk/reward and execution clarity: 10

Scores:
- 0–49: wait/no trade
- 50–64: low-confidence thesis
- 65–79: medium-confidence draft
- 80+: high-quality draft ready for operator review

Even 80+ does not authorize auto-trading or public posting.

## Agent Role Map

- Capture Agent: obtains browser/screenshots and provenance.
- Markdownizer / Evidence Extractor: creates evidence cards from captures.
- Source Evaluator: applies source weight, freshness, and contradiction checks.
- Internal Summarizer / ChaseOS Synthesis Agent: summarizes packets, replacing NotebookLM as future default.
- Thesis Synthesizer: drafts BTC/ETH/SOL session thesis and alt watchlist only if strict filter passes.
- Risk Challenger / Workflow Auditor: attacks unsupported claims and blocks unsafe drafts.
- Publisher Draft Agent: formats Discord drafts, never posts without approval.
- Logger / Auditor: writes operator brief and Agent-Activity evidence.

## Public / Private Separation

Public/member-facing Discord thesis: market read, BTC/ETH/SOL bias, key zones, confirmation gates, invalidation, screenshot references, NFA/thesis-assist framing.

Private operator brief: evidence paths, missing data, contradictions, workflow health, next actions.

Private trade-plan draft: entries/stops/TP/trailing logic. Never public by default.

## Linked Docs

- [[StrikeZone-SBP-Source-Registry]]
- [[StrikeZone-Internal-Synthesis-Engine]]
- [[StrikeZone-SBP-Workflow-Auditor]]
- [[04_SOPS/StrikeZone-Daily-Thesis-SOP|StrikeZone Daily Thesis SOP]]
- [[04_SOPS/StrikeZone-Evidence-Capture-SOP|StrikeZone Evidence Capture SOP]]
- [[04_SOPS/StrikeZone-Screenshot-To-Markdown-SOP|StrikeZone Screenshot-To-Markdown SOP]]
- [[05_TEMPLATES/StrikeZone-SBP-Evidence-Packet-Template|StrikeZone SBP Evidence Packet Template]]
- [[05_PROMPTS/Trading/StrikeZone-Prompt-Registry|StrikeZone Prompt Registry]]
